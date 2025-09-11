import importlib
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from invenio_app.factory import create_api
from marshmallow import Schema as MMSchema

try:
    # Optional: improves path registration from view functions when available
    from apispec_webframeworks.flask import FlaskPlugin  # type: ignore
except Exception:  # pragma: no cover - plugin is optional
    FlaskPlugin = None  # type: ignore


# ------------------------- small utilities -----------------------------------


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


# ------------------------- schema registry -----------------------------------


class SchemaRegistry:
    """Collect Marshmallow Schemas from installed Invenio modules.

    Stores Schema classes and exposes simple name lookups and fuzzy matching.
    """

    DEFAULT_MODULES = [
        # RDM and common services
        "invenio_rdm_records.services.schemas.metadata",
        "invenio_rdm_records.services.schemas",
        "invenio_communities.communities.schema",
        "invenio_communities.services.schemas",
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
    ]

    def __init__(self, modules: Optional[List[str]] = None) -> None:
        self._classes: Dict[str, type[MMSchema]] = {}
        self._index: Dict[str, str] = {}
        for modname in modules or self.DEFAULT_MODULES:
            self._load_module(modname)

    def _load_module(self, modname: str) -> None:
        try:
            mod = importlib.import_module(modname)
        except Exception:
            return
        for name, obj in vars(mod).items():
            if isinstance(obj, type) and issubclass(obj, MMSchema):
                self._classes[name] = obj
                self._index[name.lower()] = name
                # Index without trailing "Schema"
                if name.lower().endswith("schema"):
                    base = name.lower()[:-6]
                    self._index[base] = name

    def names(self) -> List[str]:
        return sorted(self._classes.keys())

    def get_class(self, name: str) -> Optional[type[MMSchema]]:
        return self._classes.get(name)

    def find_by_hint(self, hint: str) -> Optional[str]:
        """Find a schema name by best-effort hint (path segment, etc.)."""
        key = hint.strip().lower()
        # naive singularization
        if key.endswith("ies"):  # communities -> community
            key = key[:-3] + "y"
        elif key.endswith("s"):
            key = key[:-1]
        # direct lookup
        if key in self._index:
            return self._index[key]
        # fuzzy contains
        for n in self.names():
            ln = n.lower()
            if key and (key in ln or ln in key):
                return n
        return None


# ------------------------- endpoint analysis ---------------------------------


@dataclass(frozen=True)
class EndpointInfo:
    rule: Any
    path: str
    methods: List[str]
    view: Any


class EndpointAnalyzer:
    """Analyze Flask app url map and guess schemas per endpoint.

    Uses a conservative heuristic: first path segment is used as a hint to
    select a schema component. This reduces hard-coded mappings and leverages
    the registry for discovery.
    """

    def __init__(self, registry: SchemaRegistry) -> None:
        self._reg = registry

    @staticmethod
    def tag_for(path: str) -> str:
        parts = [p for p in path.split("/") if p]
        if not parts:
            return "Misc"
        if parts[0] == "records":
            return "Drafts" if any("draft" in p for p in parts) else "Records"
        return parts[0].replace("_", " ").title()

    def schema_name_for(self, path: str) -> Optional[str]:
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None
        hint = parts[0]
        # prioritize well-known hints to common schema names when present
        preferred: List[Tuple[str, List[str]]] = [
            ("records", ["MetadataSchema", "Record", "RDMRecord"]),
            ("communities", ["CommunitySchema", "CommunityParentSchema", "Community"]),
            ("users", ["UserSchema", "User"]),
        ]
        for seg, candidates in preferred:
            if hint == seg:
                for c in candidates:
                    if c in self._reg.names():
                        return c
        # fallback to fuzzy
        found = self._reg.find_by_hint(hint)
        return found

    def endpoints(self, app) -> Iterable[EndpointInfo]:
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith(("/static", "/_debug_toolbar")):
                continue
            methods = sorted(list(rule.methods - {"HEAD", "OPTIONS"}))
            if not methods:
                continue
            view = app.view_functions.get(rule.endpoint)
            yield EndpointInfo(
                rule=rule, path=to_oas(rule.rule), methods=methods, view=view
            )


# ------------------------- spec builder --------------------------------------


class SpecBuilder:
    def __init__(self, registry: SchemaRegistry, analyzer: EndpointAnalyzer) -> None:
        self.registry = registry
        self.analyzer = analyzer
        self.ma_plugin = MarshmallowPlugin()
        self.flask_plugin = FlaskPlugin() if FlaskPlugin else None

    def _create_spec(self, app) -> APISpec:
        plugins = [self.ma_plugin]
        if self.flask_plugin is not None:
            plugins.insert(0, self.flask_plugin)
        return APISpec(
            title="InvenioRDM API",
            version=str(app.config.get("APP_VERSION", "0.0.1")),
            openapi_version="3.0.3",
            plugins=plugins,
        )

    def _register_components(self, spec: APISpec) -> None:
        # Register all discovered marshmallow schemas as components
        for name in self.registry.names():
            cls = self.registry.get_class(name)
            if not cls:
                continue
            try:
                # Let MarshmallowPlugin generate component definitions
                spec.components.schema(name, schema=cls, lazy=True)
            except Exception:
                # Be resilient to broken schemas; continue
                continue

    def _build_paths(self, app) -> Dict[str, Any]:
        paths: Dict[str, Any] = {}
        for ep in self.analyzer.endpoints(app):
            operations: Dict[str, Any] = {}
            tag = self.analyzer.tag_for(ep.path)
            schema_name = self.analyzer.schema_name_for(ep.path)

            # NOTE: We intentionally skip FlaskPlugin path registration; we
            # build a minimal but valid operation map ourselves.

            # Build minimal operation definitions
            for m in ep.methods:
                op: Dict[str, Any] = {"tags": [tag], "responses": {}}
                # path parameters
                params = [
                    {
                        "name": a,
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                    for a in ep.rule.arguments
                ]
                if params:
                    op["parameters"] = params

                # heuristics
                is_get = m.upper() == "GET"
                is_write = m.upper() in {"POST", "PUT", "PATCH"}

                # Prefer component refs by name using explicit $ref
                if schema_name:
                    ref_obj: Any = {"$ref": f"#/components/schemas/{schema_name}"}
                    resp_schema: Any = ref_obj
                    # Simple heuristic for collection endpoints
                    tail = ep.path.rstrip("/").split("/")[-1]
                    if is_get and "{" not in tail:
                        resp_schema = {"type": "array", "items": ref_obj}
                else:
                    resp_schema = {"type": "object"}

                if is_write:
                    op["requestBody"] = {
                        "content": {"application/json": {"schema": resp_schema}}
                    }

                op["responses"]["200"] = {
                    "description": "Successful response",
                    "content": {"application/json": {"schema": resp_schema}},
                }

                operations[m.lower()] = op

            # Attach path-level params (deduplicated across operations)
            paths.setdefault(ep.path, {}).update(operations)
        return paths

    @staticmethod
    def _sanitize_schema_types(spec_dict: Dict[str, Any]) -> None:
        """Remove or fix invalid JSON Schema 'type' values in components.

        Some Marshmallow fields carry a custom 'type' metadata (e.g. 'communitytypes',
        'dynamic') which apispec can leak into the OpenAPI output. These are not
        valid JSON Schema types and cause validation errors. We remove those when
        a $ref/allOf is present, or coerce to 'object' as a safe fallback.
        """
        allowed = {"array", "boolean", "integer", "number", "object", "string"}

        def fix(node: Any) -> None:
            if isinstance(node, dict):
                # If this node declares an invalid 'type', fix or drop it
                if "type" in node:
                    t = node.get("type")
                    if isinstance(t, str) and t not in allowed:
                        if (
                            "$ref" in node
                            or "allOf" in node
                            or "anyOf" in node
                            or "oneOf" in node
                        ):
                            node.pop("type", None)
                        else:
                            node["type"] = "object"
                # Recurse
                for v in node.values():
                    fix(v)
            elif isinstance(node, list):
                for v in node:
                    fix(v)

        comps = spec_dict.get("components", {}).get("schemas", {})
        fix(comps)

    def build(self) -> Dict[str, Any]:
        app = create_api()
        with app.app_context():
            spec = self._create_spec(app)
            self._register_components(spec)
            # Build the spec dict and then inject our paths
            spec_dict = yaml_safe(spec.to_dict())
            spec_dict["paths"] = self._build_paths(app)
            # Post-process to remove invalid 'type' values produced by 3rd-party schemas
            self._sanitize_schema_types(spec_dict)
            return spec_dict


# ------------------------- main ----------------------------------------------


def main(argv: Optional[List[str]] = None) -> None:
    out = "openapi_generated.yaml"
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) >= 1 and argv[0]:
        out = argv[0]

    registry = SchemaRegistry()
    analyzer = EndpointAnalyzer(registry)
    spec_dict = SpecBuilder(registry, analyzer).build()
    with open(out, "w", encoding="utf-8") as f:
        yaml.safe_dump(spec_dict, f, sort_keys=False, allow_unicode=True)
    print(f"✅ OpenAPI spec generated → {out}")


if __name__ == "__main__":
    main()
