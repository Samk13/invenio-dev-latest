"""Customisations to expose user roles for administration."""

from __future__ import annotations

from typing import Iterable, List

from invenio_i18n import lazy_gettext as _
from invenio_records_resources.services.records.facets import TermsFacet
from marshmallow import fields, post_dump

from invenio_users_resources.config import (
    USERS_RESOURCES_SEARCH,
    USERS_RESOURCES_SEARCH_FACETS,
)
from invenio_users_resources.records.api import (
    GroupAggregate,
    GroupAggregateModel,
    UserAggregate,
    UserAggregateModel,
)
from invenio_users_resources.services.schemas import UserSchema


def _render_roles_markup(roles: Iterable[str]) -> str:
    """Return semantic-ui labels markup for the given roles."""
    cleaned = [role for role in roles if role]
    if not cleaned:
        return ""

    labels = "".join(
        f'<span class="ui tiny label role-label">{role}</span>' for role in cleaned
    )
    return f'<div class="ui tiny labels role-labels">{labels}</div>'


class UserAggregateModelWithRoles(UserAggregateModel):
    """Extend the aggregate metadata with a cached list of roles."""

    _properties = UserAggregateModel._properties + [
        "roles",
        "roles_label",
        "roles_markup",
    ]

    def from_model(self, user):
        """Populate role names in the profile section."""
        super().from_model(user)
        roles: List[str] = [role.name for role in user.roles or []]
        profile = dict(self._data.get("profile") or {})
        profile["roles"] = roles
        self._data["profile"] = profile
        self._data["roles"] = roles
        self._data["roles_label"] = ", ".join(roles)
        self._data["roles_markup"] = _render_roles_markup(roles)

    def from_kwargs(self, kwargs):
        """Ensure supplemental role fields are available from indexed data."""
        super().from_kwargs(kwargs)
        roles = kwargs.get("roles") or kwargs.get("roles_label")
        if roles and isinstance(roles, str):
            roles = [r.strip() for r in roles.split(",") if r.strip()]
        if not roles:
            roles = (kwargs.get("profile") or {}).get("roles", [])
        if roles is None:
            roles = []
        self._data["roles"] = roles
        self._data["roles_label"] = ", ".join(roles)
        self._data["roles_markup"] = _render_roles_markup(roles)


class UserWithRolesSchema(UserSchema):
    """Expose the roles field in serialized users."""

    roles = fields.List(fields.String(), dump_only=True)
    roles_label = fields.String(dump_only=True)
    roles_markup = fields.String(dump_only=True)

    @post_dump(pass_original=True)
    def populate_roles(self, data, original, **kwargs):
        """Ensure role data is exposed in flat and profile fields."""
        roles = data.get("roles")
        if roles is None:
            if isinstance(original, dict):
                roles = original.get("roles") or original.get("profile", {}).get(
                    "roles"
                )
            else:
                roles = getattr(original, "roles", None)
                if roles is None:
                    model = getattr(original, "model", None)
                    model_obj = getattr(model, "_model_obj", None) if model else None
                    if model_obj is not None:
                        roles = [role.name for role in model_obj.roles or []]
        roles = roles or []
        data["roles"] = roles
        data["roles_label"] = ", ".join(roles)
        data["roles_markup"] = _render_roles_markup(roles)

        profile = data.get("profile") or {}
        profile["roles"] = roles
        data["profile"] = profile
        return data


class GroupAggregateModelWithNameIdentifier(GroupAggregateModel):
    """Expose human-readable identifiers for groups."""

    _properties = GroupAggregateModel._properties + ["internal_id"]

    def from_model(self, role):
        """Populate data from the role model."""
        super().from_model(role)
        internal_id = self._data.get("id")
        self._data["internal_id"] = internal_id
        self._data["id"] = role.name

    def from_kwargs(self, kwargs):
        """Populate data from indexed representation."""
        super().from_kwargs(kwargs)
        internal_id = (
            kwargs.get("internal_id") or kwargs.get("uuid") or kwargs.get("pk")
        )
        if (
            internal_id is None
            and kwargs.get("id")
            and kwargs.get("id") != kwargs.get("name")
        ):
            internal_id = kwargs.get("id")
        self._data["internal_id"] = internal_id or self._data.get("internal_id")
        # Ensure the identifier falls back to the name.
        name = kwargs.get("name") or self._data.get("name")
        if name:
            self._data["id"] = name


def apply_user_roles_patch(app):
    """Register aggregate/schema overrides and role facet."""
    UserAggregate.model_cls = UserAggregateModelWithRoles
    GroupAggregate.model_cls = GroupAggregateModelWithNameIdentifier
    app.config["USERS_RESOURCES_SERVICE_SCHEMA"] = UserWithRolesSchema

    facets = app.config.setdefault(
        "USERS_RESOURCES_SEARCH_FACETS", USERS_RESOURCES_SEARCH_FACETS
    )
    if "roles" not in facets:
        facets["roles"] = {
            "facet": TermsFacet(field="profile.roles", label=_("Roles")),
            "ui": {"field": "profile.roles"},
        }

    search_conf = app.config.setdefault(
        "USERS_RESOURCES_SEARCH", USERS_RESOURCES_SEARCH
    )
    if "roles" not in search_conf["facets"]:
        search_conf["facets"].append("roles")

    app.config.setdefault(
        "GROUPS_ADMIN_SORT_OPTIONS",
        {
            "bestmatch": {
                "title": _("Best match"),
                "fields": ["_score"],
            },
            "name": {
                "title": _("Name"),
                "fields": ["name.keyword"],
            },
        },
    )

    app.config.setdefault("GROUPS_ADMIN_FACETS", {})

    app.config.setdefault(
        "GROUPS_ADMIN_SEARCH",
        {
            "sort": ["bestmatch", "name"],
            "facets": [],
        },
    )

    try:
        from invenio_app_rdm.administration.users import users as admin_users

        admin_users.USERS_ITEM_LIST.setdefault(
            "roles_markup",
            {
                "text": _("Roles"),
                "order": 4.5,
                "width": 3,
                "escape": True,
            },
        )
        admin_users.USERS_ITEM_DETAIL.setdefault(
            "roles_markup",
            {
                "text": _("Roles"),
                "order": 6.5,
                "width": 3,
                "escape": True,
            },
        )
    except Exception:  # pragma: no cover - optional dependency
        pass
