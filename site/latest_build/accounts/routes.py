"""Endpoints for role management actions."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from invenio_access import Permission
from invenio_accounts.proxies import current_datastore
from invenio_db import db
from werkzeug.exceptions import BadRequest, Conflict, Forbidden, NotFound

from invenio_users_resources.permissions import user_management_action
from invenio_users_resources.proxies import current_groups_service
from invenio_users_resources.records.api import GroupAggregate


def _ensure_can_manage():
    """Verify current identity can manage roles/users."""
    if not Permission(user_management_action).can():
        raise Forbidden()


def _resolve_role(identifier):
    """Fetch role by name or ID."""
    role = current_datastore.find_role(identifier)
    if role:
        return role

    role = current_datastore.find_role_by_id(identifier)
    if role:
        return role

    raise NotFound(f"Role '{identifier}' was not found.")


def _user_roles_payload(user):
    """Return ordered list of role names for the user."""
    return sorted(role.name for role in (user.roles or []))


def _serialize_role(role):
    """Serialize role data for API responses."""
    return {
        "id": role.name,
        "internal_id": role.id,
        "name": role.name,
        "description": role.description or "",
        "is_managed": role.is_managed,
    }


def _create_role_from_payload(payload):
    name = (payload.get("name") or "").strip()
    description = (payload.get("description") or "").strip()

    if not name:
        raise BadRequest("Role name is required.")

    if current_datastore.find_role(name):
        raise Conflict(f"Role '{name}' already exists.")

    role = current_datastore.create_role(
        name=name,
        description=description or None,
        is_managed=True,
    )
    db.session.commit()
    return role


def _aggregate_role(role):
    """Return aggregate representation used by the groups index."""
    return GroupAggregate.from_model(role)


def _index_role(role, previous_identifier: str | None = None):
    """Push role changes to the groups search index."""
    try:
        aggregate = _aggregate_role(role)
        current_groups_service.indexer.index(aggregate)
        if previous_identifier and previous_identifier != aggregate.id:
            current_groups_service.indexer.client.delete(
                index=aggregate.index._name,
                id=previous_identifier,
                ignore=[404],
            )
    except Exception as exc:  # pragma: no cover - best effort
        current_app.logger.warning(
            "Failed to index role '%s': %s", getattr(role, "name", role), exc
        )


def _delete_role_from_index(aggregate):
    """Remove a role aggregate from the groups index."""
    try:
        current_groups_service.indexer.delete(aggregate)
    except Exception as exc:  # pragma: no cover - best effort
        current_app.logger.warning(
            "Failed to remove role '%s' from index: %s",
            getattr(aggregate, "name", getattr(aggregate, "id", "unknown")),
            exc,
        )


def create_roles_blueprint(name: str = "latest_build_roles_api", url_prefix: str = ""):
    """Return the blueprint registering role management routes."""
    blueprint = Blueprint(name, __name__, url_prefix=url_prefix)

    @blueprint.post("/groups")
    def create_group():
        _ensure_can_manage()
        payload = request.get_json() or {}
        role = _create_role_from_payload(payload)
        _index_role(role)
        return jsonify(_serialize_role(role)), 201

    @blueprint.post("/user-roles")
    def create_role():
        _ensure_can_manage()
        payload = request.get_json() or {}
        role = _create_role_from_payload(payload)
        _index_role(role)
        return jsonify(_serialize_role(role)), 201

    @blueprint.put("/groups/<role_identifier>")
    @blueprint.patch("/groups/<role_identifier>")
    def update_role(role_identifier):
        _ensure_can_manage()
        role = _resolve_role(role_identifier)
        previous_identifier = role.name

        payload = request.get_json() or {}
        new_name = (payload.get("name") or role.name).strip()
        description = (payload.get("description") or "").strip()

        if new_name != role.name and current_datastore.find_role(new_name):
            raise Conflict(f"Role '{new_name}' already exists.")

        role.name = new_name
        role.description = description or None
        db.session.commit()
        _index_role(
            role,
            previous_identifier=previous_identifier
            if previous_identifier != new_name
            else None,
        )

        return jsonify(_serialize_role(role))

    @blueprint.delete("/groups/<role_identifier>")
    def delete_group(role_identifier):
        _ensure_can_manage()
        role = _resolve_role(role_identifier)
        aggregate = _aggregate_role(role)
        if not role.is_managed:
            raise Conflict("Externally managed roles cannot be deleted.")
        current_datastore.delete(role)
        db.session.commit()
        _delete_role_from_index(aggregate)
        return "", 204

    @blueprint.delete("/user-roles/<role_identifier>")
    def delete_role_legacy(role_identifier):
        return delete_group(role_identifier)

    @blueprint.post("/users/<int:user_id>/roles")
    def assign_role(user_id):
        _ensure_can_manage()
        payload = request.get_json() or {}
        role_identifier = payload.get("role")
        if not role_identifier:
            raise BadRequest("Missing 'role' parameter.")

        user = current_datastore.get_user_by_id(user_id)
        if user is None:
            raise NotFound(f"User '{user_id}' was not found.")

        role = _resolve_role(role_identifier)
        current_datastore.add_role_to_user(user, role)
        db.session.commit()

        return jsonify({"roles": _user_roles_payload(user)})

    @blueprint.delete("/users/<int:user_id>/roles/<role_identifier>")
    def remove_role(user_id, role_identifier):
        _ensure_can_manage()
        user = current_datastore.get_user_by_id(user_id)
        if user is None:
            raise NotFound(f"User '{user_id}' was not found.")

        role = _resolve_role(role_identifier)
        removed = current_datastore.remove_role_from_user(user, role)
        if not removed:
            raise NotFound(
                f"User '{user_id}' does not have the role '{role_identifier}'."
            )

        db.session.commit()
        return jsonify({"roles": _user_roles_payload(user)})

    @blueprint.get("/user-roles")
    def list_roles_legacy():
        _ensure_can_manage()
        roles = current_datastore.role_model.query.order_by(
            current_datastore.role_model.name
        ).all()
        return jsonify({"hits": {"hits": [_serialize_role(r) for r in roles]}})

    return blueprint
