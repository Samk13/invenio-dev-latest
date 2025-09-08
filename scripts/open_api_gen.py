# scripts/open_api_gen.py
import importlib
import re
import yaml
from typing import Any, Dict, Iterable, List, Mapping, Optional

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from invenio_app.factory import create_api
from marshmallow import Schema as MMSchema

# ------------------------- shared small utilities ----------------------------

VALID_TYPES = {"array", "boolean", "integer", "number", "object", "string"}

def to_oas(path: str) -> str:
    """Flask <param> or <type:param> → OpenAPI {param}."""
    return re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", path)

def yaml_safe(obj: Any) -> Any:
    """Make complex objects YAML-safe with minimal overhead."""
    if isinstance(obj, dict):
        return {str(k): yaml_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [yaml_safe(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    try:
        return str(obj)
    except Exception:
        return repr(obj)

def fix_types(obj: Any) -> None:
    """Normalize invalid JSON Schema 'type' values to 'string'."""
    if isinstance(obj, dict):
        t = obj.get("type")
        if isinstance(t, str) and t not in VALID_TYPES:
            obj["type"] = "string"
        for v in obj.values():
            fix_types(v)
    elif isinstance(obj, list):
        for v in obj:
            fix_types(v)

def merge_objects(objs: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Merge object schemas' properties/required minimally."""
    out = {"type": "object", "properties": {}}
    req: set[str] = set()
    for o in objs:
        if isinstance(o, dict) and o.get("type") == "object":
            out["properties"].update(o.get("properties", {}))
            req.update(o.get("required", []))
    if req:
        out["required"] = sorted(req)
    return out

def flatten_oneof(schema: Any) -> Any:
    """Replace any oneOf with a merged best-effort concrete object."""
    if isinstance(schema, dict):
        one = schema.get("oneOf")
        if isinstance(one, list):
            merged = merge_objects(flatten_oneof(x) for x in one) or {"type": "object"}
            schema.clear()
            schema.update(merged)
        for k, v in list(schema.items()):
            schema[k] = flatten_oneof(v)
        return schema
    if isinstance(schema, list):
        return [flatten_oneof(v) for v in schema]
    return schema

# ------------------------- schema conversion (SRP) ---------------------------

class MarshmallowToOpenAPI:
    """Converts Marshmallow schemas/fields → OpenAPI JSON Schema."""

    LANG_MAP_NAMES = {
        "title", "titles", "description", "descriptions",
        "title_l10n", "subtitle_l10n", "alternative_titles",
    }

    @staticmethod
    def _enum_from_field(field) -> Optional[List[Any]]:
        # 1) metadata.enum
        md = getattr(field, "metadata", {}) or {}
        if isinstance(md.get("enum"), (list, tuple)) and md["enum"]:
            return list(md["enum"])
        # 2) marshmallow.validate.OneOf
        try:
            from marshmallow import validate as V  # lazy import
            v = getattr(field, "validate", None)
            vals = v if isinstance(v, (list, tuple)) else ([v] if v else [])
            for item in vals:
                if isinstance(item, V.OneOf) and getattr(item, "choices", None):
                    return list(item.choices)
        except Exception:
            pass
        # 3) EnumField (marshmallow_enum or marshmallow_utils.fields)
        for modname, attr in (("marshmallow_enum", "EnumField"),
                              ("marshmallow_utils.fields", "EnumField")):
            try:
                mod = importlib.import_module(modname)
                EnumField = getattr(mod, attr, None)
                if EnumField and isinstance(field, EnumField):
                    enum_cls = getattr(field, "enum", None)
                    if enum_cls:
                        first = next(iter(enum_cls))
                        use_val = hasattr(first, "value")
                        return [(e.value if use_val else e.name) for e in enum_cls]
            except Exception:
                continue
        # 4) fallback: attribute "enum" on field
        try:
            enum_cls = getattr(field, "enum", None)
            if enum_cls:
                first = next(iter(enum_cls))
                use_val = hasattr(first, "value")
                return [(e.value if use_val else e.name) for e in enum_cls]
        except Exception:
            pass
        return None

    @staticmethod
    def _constraints_from_validators(field, out: Dict[str, Any]) -> None:
        try:
            from marshmallow import validate as V
            v = getattr(field, "validate", None)
            vals = v if isinstance(v, (list, tuple)) else ([v] if v else [])
            for item in vals:
                if isinstance(item, V.Range):
                    if item.min is not None: out["minimum"] = item.min
                    if item.max is not None: out["maximum"] = item.max
                elif isinstance(item, V.Length):
                    if item.min is not None: out["minLength"] = item.min
                    if item.max is not None: out["maxLength"] = item.max
                elif isinstance(item, V.Regexp):
                    pat = getattr(item, "regex", None)
                    if getattr(pat, "pattern", None): out["pattern"] = pat.pattern
        except Exception:
            pass

    @classmethod
    def field(cls, f) -> Dict[str, Any]:
        from marshmallow import fields as F
        nullable = getattr(f, "allow_none", False)

        def base(_type: str, fmt: Optional[str] = None) -> Dict[str, Any]:
            d: Dict[str, Any] = {"type": _type}
            if fmt: d["format"] = fmt
            if nullable: d["nullable"] = True
            enum_vals = cls._enum_from_field(f)
            if enum_vals: d["enum"] = enum_vals
            cls._constraints_from_validators(f, d)
            md = getattr(f, "metadata", {}) or {}
            desc = md.get("description")
            if isinstance(desc, str): d["description"] = desc
            return d

        try:
            if isinstance(f, (F.String, F.Email, F.URL, F.UUID)):
                return base("string", "uuid" if isinstance(f, F.UUID) else ("uri" if isinstance(f, F.URL) else None))
            if isinstance(f, F.Integer): return base("integer")
            if isinstance(f, (F.Float, F.Decimal)): return base("number")
            if isinstance(f, F.Boolean): return base("boolean")
            if isinstance(f, F.DateTime): return base("string", "date-time")
            if isinstance(f, F.Date): return base("string", "date")
            if isinstance(f, F.Time): return base("string", "time")
            if isinstance(f, (F.Method, F.Function, F.Raw)): return base("string")

            if isinstance(f, F.List):
                inner = getattr(f, "inner", None) or getattr(f, "container", None)
                d = {"type": "array", "items": cls.field(inner) if inner else {"type": "string"}}
                if nullable: d["nullable"] = True
                cls._constraints_from_validators(f, d)
                return d

            if isinstance(f, F.Dict):
                values = getattr(f, "values", None)
                d = {"type": "object", "additionalProperties": cls.field(values) if values else {"type": "string"}}
                if nullable: d["nullable"] = True
                return d

            if isinstance(f, F.Nested):
                many = getattr(f, "many", False)
                js = cls.schema(getattr(f, "schema", None) or getattr(f, "nested", None))
                d = {"type": "array", "items": js} if many else {
                    "type": "object", "properties": js.get("properties", {})
                }
                if not many and "required" in js: d["required"] = js["required"]
                if nullable: d["nullable"] = True
                return d

            return base("string")
        except Exception:
            return {"type": "string"}

    @classmethod
    def _maybe_lang_map_enhance(cls, field_name: str, schema: Dict[str, Any]) -> None:
        """Make language maps readable in Swagger UI."""
        if schema.get("type") != "object":
            return
        ap = schema.get("additionalProperties")
        if not (isinstance(ap, dict) and ap.get("type") == "string"):
            return
        if field_name in cls.LANG_MAP_NAMES or field_name.endswith("_l10n"):
            schema.setdefault("description", "Language map (ISO language codes as keys).")
            schema.setdefault("example", {"en": "Example text"})

    @classmethod
    def schema(cls, s: Any) -> Dict[str, Any]:
        """Marshmallow Schema → JSON Schema, keeping constraints/enums."""
        # OneOfSchema: keep structure; caller may flatten later.
        try:
            from marshmallow_oneofschema import OneOfSchema  # optional
            if isinstance(s, type) and issubclass(s, OneOfSchema):
                ts = getattr(s, "type_schemas", {}) or {}
                return {"oneOf": [cls.schema(v) or {"type": "object"} for v in ts.values()],
                        "discriminator": {"propertyName": getattr(s, "type_field", "type")}}
        except Exception:
            pass

        try:
            inst = s() if isinstance(s, type) else s
            if not isinstance(inst, MMSchema):
                return {"type": "object"}

            fields = getattr(inst, "fields", None) or getattr(inst.__class__, "_declared_fields", {}) or {}
            props: Dict[str, Any] = {}
            req: List[str] = []
            for name, fld in fields.items():
                prop = cls.field(fld)
                cls._maybe_lang_map_enhance(name, prop)
                props[name] = prop
                if getattr(fld, "required", False) and not getattr(fld, "allow_none", False):
                    req.append(name)
            out: Dict[str, Any] = {"type": "object", "properties": props}
            if req:
                out["required"] = sorted(set(req))
            return out
        except Exception:
            return {"type": "object"}

# ------------------------- schema registry (O) --------------------------------

class SchemaRegistry:
    """Scans known modules for Schema classes and exposes JSON Schema dicts."""

    DEFAULT_MODULES = [
        "invenio_rdm_records.services.schemas.metadata",
        "invenio_communities.communities.schema",
        "invenio_users_resources.services.schemas",
        "invenio_requests.services.schemas",
        "invenio_vocabularies.services.schema",
        "invenio_vocabularies.services.schemas",
        "invenio_records_resources.services.files.schema",
        "invenio_records_resources.services.records.schema",
        "invenio_jobs.services.schema",
        "invenio_jobs.schemas",
        "invenio_oaiserver.services.schemas",
        "invenio_notifications.services.schemas",
        "invenio_communities.services.schemas",
    ]

    def __init__(self, modules: Optional[List[str]] = None) -> None:
        self._schemas: Dict[str, Dict[str, Any]] = {}
        for modname in (modules or self.DEFAULT_MODULES):
            self._load_module(modname)

    def _load_module(self, modname: str) -> None:
        try:
            mod = importlib.import_module(modname)
        except Exception:
            return
        for name, obj in vars(mod).items():
            if isinstance(obj, type) and issubclass(obj, MMSchema):
                self._schemas[name] = MarshmallowToOpenAPI.schema(obj)

    def get(self, *names: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        for n in names:
            if n in self._schemas:
                return self._schemas[n]
        return default or {"type": "object"}

    @property
    def components(self) -> Dict[str, Dict[str, Any]]:
        return dict(self._schemas)

# ------------------------- endpoint typing (I) --------------------------------

class EndpointTyping:
    """Decides which schema to use for a given path (request/response)."""

    AUTH_BODIES: Dict[str, Dict[str, Any]] = {
        "change-password": {"type": "object", "properties": {
            "password": {"type": "string"}, "new_password": {"type": "string"}}, "required": ["password", "new_password"]},
        "forgot-password": {"type": "object", "properties": {
            "email": {"type": "string", "format": "email"}}, "required": ["email"]},
        "reset-password": {"type": "object", "properties": {
            "token": {"type": "string"}, "password": {"type": "string"}}, "required": ["token", "password"]},
        "send-confirmation-email": {"type": "object", "properties": {
            "email": {"type": "string", "format": "email"}}, "required": ["email"]},
        "confirm-email": {"type": "object", "properties": {
            "token": {"type": "string"}}, "required": ["token"]},
    }
    AUTH_RESP = {"type": "object", "properties": {"status": {"type": "string"}, "message": {"type": "string"}}}
    PAGES = {"type": "object", "properties": {
        "id": {"type": "string"}, "slug": {"type": "string"}, "title": {"type": "string"},
        "content": {"type": "string"}, "published": {"type": "boolean"},
        "updated": {"type": "string", "format": "date-time"}}}
    OAIPMH_FORMAT = {"type": "object", "properties": {
        "metadataPrefix": {"type": "string"},
        "schema": {"type": "string", "format": "uri"},
        "metadataNamespace": {"type": "string", "format": "uri"},
    }}

    @staticmethod
    def tag_for(path: str) -> str:
        parts = path.strip("/").split("/")
        seg = parts[0] if parts else "Misc"
        if seg == "records": return "Drafts" if "draft" in parts else "Records"
        return {
            "communities": "Communities", "users": "Users", "requests": "Requests",
            "files": "Files", "record_files": "Files", "draft_files": "Files",
            "jobs": "Jobs", "iiif": "IIIF", "vocabularies": "Vocabularies",
            "oaipmh": "OAI-PMH", "oaiserver": "OAI-PMH",
            "affiliations": "Vocabularies", "awards": "Vocabularies", "funders": "Vocabularies",
            "names": "Vocabularies", "subjects": "Vocabularies", "banners": "Banners",
            "hooks": "Hooks", "collections": "Collections", "pages": "Pages",
            "auth": "Auth", "sessions": "Sessions", "change-password": "Security",
            "forgot-password": "Security", "reset-password": "Security",
            "send-confirmation-email": "Security", "confirm-email": "Security",
        }.get(seg, seg.capitalize())

    def __init__(self, registry: SchemaRegistry) -> None:
        self._reg = registry

    def schema_for(self, path: str) -> Dict[str, Any]:
        p = path.strip("/")

        # vocabularies & controlled lists
        if p.startswith("vocabularies"):
            return self._reg.get("VocabularySchema", "BaseVocabularySchema")
        if p.startswith(("affiliations", "awards", "funders", "names", "subjects")):
            return self._reg.get("VocabularySchema")

        # core resources
        if p.startswith("records"):
            return self._reg.get("MetadataSchema")
        if p.startswith("communities"):
            return self._reg.get("CommunitySchema", "CommunityParentSchema", "Community")
        if p.startswith("users"):
            return self._reg.get("UserSchema", "User")
        if p.startswith("requests"):
            return self._reg.get("RequestSchema", "Request")
        if "files" in p:
            return self._reg.get("FileSchema")
        if p.startswith("jobs") or "/jobs" in p:
            return self._reg.get("RunSchema", "JobSchema", "JobArgumentsSchema")

        # pages & OAI-PMH
        if p.startswith("pages"):
            return self.PAGES
        if p.startswith("oaipmh/formats"):
            return {"type": "array", "items": self.OAIPMH_FORMAT}

        # auth & sessions
        for key, body in self.AUTH_BODIES.items():
            if p.startswith(key):
                return body
        if p == "sessions":
            return {"type": "array", "items": {"type": "object", "properties": {
                "sid_s": {"type": "string"}, "ip": {"type": "string"},
                "user_agent": {"type": "string"},
                "created": {"type": "string", "format": "date-time"},
            }}}
        if p.startswith("sessions/"):
            return {"type": "object", "properties": {"status": {"type": "string"}}}
        if p.startswith("collections") and p.endswith("/records"):
            return {"type": "array", "items": self._reg.get("MetadataSchema")}

        return {"type": "object"}

# ------------------------- component enrichment (D) ---------------------------

class ComponentEnricher:
    """Fix known sparse spots to avoid {} in UI, without hardcoding everything."""

    PATCHES = {
        ("RunSchema", "args"): {"type": "array", "items": {"type": "string"}},
        ("RunSchema", "custom_args"): {"type": "object", "additionalProperties": {"type": "string"}},
        ("JobLogEntrySchema", "sort"): {"type": "array", "items": {"type": "string"}},
        ("JobLogEntrySchema", "context"): {
            "type": "object", "properties": {"job_id": {"type": "string"}, "run_id": {"type": "string"}}
        },
    }

    @staticmethod
    def _user_fallback() -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"id": {"type": "string"}, "email": {"type": "string", "format": "email"}}
        }

    def apply(self, components: Dict[str, Dict[str, Any]]) -> None:
        # enrich started_by using available User schema
        user_schema = components.get("UserSchema") or components.get("User") or self._user_fallback()
        if "RunSchema" in components:
            props = components["RunSchema"].setdefault("properties", {})
            if not props.get("started_by"):
                props["started_by"] = user_schema

        # generic patches
        for (schema_name, field), patch in self.PATCHES.items():
            if schema_name in components:
                props = components[schema_name].setdefault("properties", {})
                if not props.get(field):
                    props[field] = patch

# ------------------------- spec builder (S) -----------------------------------

class SpecBuilder:
    def __init__(self, registry: SchemaRegistry, typing: EndpointTyping) -> None:
        self.registry = registry
        self.typing = typing
        self.plugin = MarshmallowPlugin()

    def build(self) -> Dict[str, Any]:
        app = create_api()
        spec = APISpec(
            title="InvenioRDM API",
            version=app.config.get("APP_VERSION", "0.0.1"),
            openapi_version="3.0.3",
            plugins=[self.plugin],
        )

        with app.app_context():
            for rule in app.url_map.iter_rules():
                if rule.rule.startswith(("/static", "/_debug_toolbar")):
                    continue
                methods = rule.methods - {"HEAD", "OPTIONS"}
                if not methods:
                    continue

                path = to_oas(rule.rule)
                tag = self.typing.tag_for(path)
                schema = self.typing.schema_for(path) or {"type": "object"}
                ops: Dict[str, Any] = {}

                for m in methods:
                    op: Dict[str, Any] = {
                        "tags": [tag],
                        "parameters": [
                            {"name": a, "in": "path", "required": True, "schema": {"type": "string"}}
                            for a in rule.arguments
                        ],
                        "responses": {"200": {"description": "Successful response",
                                              "content": {"application/json": {"schema": schema}}}},
                    }
                    if m in {"POST", "PUT", "PATCH"}:
                        # Auth endpoints get a unified (simple) response body
                        resp_schema = (EndpointTyping.AUTH_RESP
                                       if tag in {"Auth", "Security"} else schema)
                        op["requestBody"] = {"content": {"application/json": {"schema": schema}}}
                        op["responses"]["200"]["content"]["application/json"]["schema"] = resp_schema
                    ops[m.lower()] = op

                spec.path(path=path, operations=ops)

        spec_dict = spec.to_dict()
        spec_dict.setdefault("components", {}).setdefault("schemas", {}).update(self.registry.components)
        ComponentEnricher().apply(spec_dict["components"]["schemas"])
        flatten_oneof(spec_dict)          # remove oneOf noise
        fix_types(spec_dict)              # guard against invalid "type"
        return yaml_safe(spec_dict)       # ensure YAML-safe

# ------------------------- main ------------------------------------------------

def main() -> None:
    registry = SchemaRegistry()
    typing = EndpointTyping(registry)
    spec = SpecBuilder(registry, typing).build()
    with open("openapi_generated.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True)
    print("✅ OpenAPI spec generated: concise, categorized, enums/constraints kept, "
          "auth/pages/oaipmh filled, jobs fields enriched, oneOf flattened.")

if __name__ == "__main__":
    main()
