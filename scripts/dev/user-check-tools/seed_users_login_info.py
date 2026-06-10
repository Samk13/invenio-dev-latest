"""Seed login-info rows for IP retention cleanup testing.

Usage:
    uv run invenio shell scripts/dev/seed_users_login_info.py

The script updates every existing accounts_user row with repeating retention
test cases. It does not create users.
"""

from datetime import datetime, timedelta, timezone
from itertools import cycle
from random import Random

from flask import current_app
from invenio_accounts.models import User
from invenio_accounts.proxies import current_datastore
from invenio_db import db


RANDOM_SEED = 20260610


def _retention_dates():
    """Return timestamps just outside and inside the configured retention window."""
    retention_period = current_app.config["ACCOUNTS_RETENTION_PERIOD"]
    expires_before = datetime.now(timezone.utc) - retention_period
    return {
        "expired": expires_before - timedelta(days=1),
        "recent": datetime.now(timezone.utc),
    }


def _seed_specs():
    """Build seed users for each retention cleanup case."""
    dates = _retention_dates()
    return [
        {
            "last_login_at": dates["expired"],
            "current_login_at": dates["expired"],
            "last_login_ip": "198.51.100.10",
            "current_login_ip": "198.51.100.11",
        },
        {
            "last_login_at": dates["recent"],
            "current_login_at": dates["recent"],
            "last_login_ip": "198.51.100.20",
            "current_login_ip": "198.51.100.21",
        },
        {
            "last_login_at": dates["expired"],
            "current_login_at": dates["recent"],
            "last_login_ip": "198.51.100.30",
            "current_login_ip": "198.51.100.31",
        },
        {
            "last_login_at": dates["recent"],
            "current_login_at": dates["expired"],
            "last_login_ip": "198.51.100.40",
            "current_login_ip": "198.51.100.41",
        },
        {
            "last_login_at": dates["expired"],
            "current_login_at": dates["expired"],
            "last_login_ip": None,
            "current_login_ip": None,
        },
    ]


def _existing_users():
    """Return every existing user account."""
    return db.session.query(User).order_by(User.id).all()


def _update_login_info(user, spec, login_count):
    """Apply the login tracking fields to a user."""
    user.last_login_at = spec["last_login_at"]
    user.current_login_at = spec["current_login_at"]
    user.last_login_ip = spec["last_login_ip"]
    user.current_login_ip = spec["current_login_ip"]
    user.login_count = login_count

    # LoginInformation changes are not User model changes, so mark the aggregate
    # user as changed for the normal datastore post-commit indexing hooks.
    current_datastore.mark_changed(id(db.session), model=user)


def main():
    """Seed all login-info retention cases."""
    users = _existing_users()
    spec_cycle = cycle(_seed_specs())
    random = Random(RANDOM_SEED)
    seeded = []

    for user in users:
        spec = next(spec_cycle)
        login_count = random.randint(1, 500)
        _update_login_info(user, spec, login_count)
        seeded.append((user, spec, login_count))

    current_datastore.commit()

    print(f"Seeded IP retention login-info for {len(seeded)} existing users:")
    for user, spec, login_count in seeded:
        print(
            "  "
            f"updated: id={user.id} email={user.email} "
            f"login_count={login_count} "
            f"last=({spec['last_login_at'].isoformat()}, {spec['last_login_ip']}) "
            f"current=({spec['current_login_at'].isoformat()}, "
            f"{spec['current_login_ip']})"
        )

    print()
    print("Rebuild the user/group indices with the known-good migration script:")
    print(
        "  uv run invenio shell scripts/indices-migration-v13-14/user-groups-indices-migration.py"
    )
    print()
    print("Then check indexed counts with:")
    print("  uv run invenio shell scripts/dev/check_users_login_info_index.py")
    print()
    print("Run the retention task manually with:")
    print("  uv run invenio shell")
    print("  >>> from invenio_accounts.tasks import delete_ips")
    print("  >>> delete_ips()")


main()
