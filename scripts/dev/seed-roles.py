#
# Usage: uv run invenio shell seed-roles.py
#
# This script seeds roles for development/testing
# All roles created as unmanaged groups

from invenio_access.models import ActionRoles
from invenio_access.permissions import superuser_access
from invenio_accounts.proxies import current_datastore
from invenio_users_resources.permissions import user_management_action


def create_role(id, name, description, is_managed=False):
    """Create a role if it does not exist."""
    existing = current_datastore.find_role(id)
    if existing:
        print(f"Role already exists: {id}, skipping...")
        return existing

    print(f"Creating role: {id} (managed={is_managed})")

    role = current_datastore.create_role(
        id=id,
        name=name,
        description=description,
        is_managed=is_managed,
    )
    current_datastore.commit()
    return role


def main():
    roles_to_create = [
        (user_management_action.value, user_management_action.value,
         "User management action group"),
        ("it-dep", "it-dep", "IT Department"),
        ("hr-dep", "hr-dep", "HR Department"),
        ("not-managed-dep", "not-managed-dep", "Unmanaged testing group"),
        ("asd1234", "employee", "Employee role"),
        ("student", "student", "Student role"),
        ("moderator", "moderator", "Moderator role"),
        ("community-creator", "community-creator", "Community Creator role"),
        ("teacher", "teacher", "Teacher role"),
    ]

    created = {}

    for rid, rname, rdesc in roles_to_create:
        role = create_role(rid, rname, rdesc)
        created[rid] = role

    admin_role = created.get("admin")
    if admin_role:
        print("Assigning superuser access to admin role...")
        ActionRoles.create(action=superuser_access, role=admin_role)
        current_datastore.commit()

    print("✅ All roles seeded.")


main()
