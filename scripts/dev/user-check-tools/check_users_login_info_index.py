"""Count DB and indexed user login-info fields for retention testing.

Usage:
    uv run invenio shell scripts/dev/user-check-tools/check_users_login_info_index.py
"""

from datetime import datetime, timezone

from click import secho
from flask import current_app
from invenio_accounts.models import LoginInformation, User
from invenio_db import db
from invenio_search.proxies import current_search_client
from invenio_users_resources.proxies import current_users_service
from opensearch_dsl import Search
from sqlalchemy import func, or_


IP_FIELDS = (
    ("last_login_ip", "last_login_at"),
    ("current_login_ip", "current_login_at"),
)


def retention_cutoff():
    """Return the same cutoff used by ``invenio_accounts.tasks.delete_ips``."""
    return datetime.now(timezone.utc) - current_app.config["ACCOUNTS_RETENTION_PERIOD"]


def count(query):
    """Return a scalar SQL count."""
    return query.scalar() or 0


def db_count(ip_field=None, date_field=None, expired=False):
    """Count DB login-info rows matching an IP-field condition."""
    if ip_field is None:
        return count(db.session.query(func.count(User.id)))

    ip_column = getattr(LoginInformation, ip_field)
    query = db.session.query(func.count(LoginInformation.user_id)).filter(
        ip_column.isnot(None)
    )

    if expired:
        query = query.filter(getattr(LoginInformation, date_field) < retention_cutoff())

    return count(query)


def indexed_name():
    """Return the concrete latest-build users index, if it exists."""
    index_name = current_users_service.record_cls.index._name
    pattern = f"latest-build-{index_name}-*"
    if not current_search_client.indices.exists(index=pattern):
        return None

    return next(iter(current_search_client.indices.get_alias(index=pattern).keys()))


def search_count(index_name, query=None):
    """Count indexed users matching an optional OpenSearch query."""
    search = Search(using=current_search_client, index=index_name)
    if query:
        search = search.query(query)
    return search.count()


def exists_query(field):
    """Build an exists query."""
    return {"exists": {"field": field}}


def expired_query(ip_field, date_field):
    """Build an indexed expired-IP query."""
    return {
        "bool": {
            "filter": [
                exists_query(ip_field),
                {"range": {date_field: {"lt": retention_cutoff().isoformat()}}},
            ]
        }
    }


def any_ip_query():
    """Build an indexed any-IP-present query."""
    return {
        "bool": {
            "should": [exists_query("last_login_ip"), exists_query("current_login_ip")],
            "minimum_should_match": 1,
        }
    }


def print_row(label, db_value, indexed_value=None, warn_nonzero=False):
    """Print one report row."""
    fg = "green"
    if warn_nonzero and (db_value or indexed_value):
        fg = "yellow"
    if indexed_value is None:
        secho(f"  {label}: db={db_value}", fg=fg)
    else:
        secho(f"  {label}: db={db_value} indexed={indexed_value}", fg=fg)


def main():
    """Print a compact before/after retention report."""
    cutoff = retention_cutoff()
    index_name = indexed_name()

    secho("User login-info retention counts", fg="bright_blue", bold=True)
    secho(f"  retention_cutoff: {cutoff.isoformat()}", fg="blue")
    secho(f"  concrete_index: {index_name or 'missing'}", fg="blue")
    secho("")

    total_db = count(db.session.query(func.count(User.id)))
    any_ip_db = count(
        db.session.query(func.count(LoginInformation.user_id)).filter(
            or_(
                LoginInformation.last_login_ip.isnot(None),
                LoginInformation.current_login_ip.isnot(None),
            )
        )
    )

    if index_name is None:
        secho(
            "OpenSearch users index is missing. Run the migration reindex script.",
            fg="red",
        )
        print_row("users total", total_db)
        print_row("users with any IP", any_ip_db)
        return

    current_search_client.indices.refresh(index=index_name)
    print_row("users total", total_db, search_count(index_name))
    print_row("users with any IP", any_ip_db, search_count(index_name, any_ip_query()))

    db_ip_values = 0
    indexed_ip_values = 0
    db_expired_ip_values = 0
    indexed_expired_ip_values = 0

    for ip_field, date_field in IP_FIELDS:
        db_present = db_count(ip_field)
        indexed_present = search_count(index_name, exists_query(ip_field))
        db_expired = db_count(ip_field, date_field, expired=True)
        indexed_expired = search_count(index_name, expired_query(ip_field, date_field))

        db_ip_values += db_present
        indexed_ip_values += indexed_present
        db_expired_ip_values += db_expired
        indexed_expired_ip_values += indexed_expired

        print_row(
            f"{ip_field} present",
            db_present,
            indexed_present,
        )
        print_row(
            f"{ip_field} expired and present",
            db_expired,
            indexed_expired,
            warn_nonzero=True,
        )

    secho("")
    print_row("IP values present total", db_ip_values, indexed_ip_values)
    print_row(
        "expired IP values present total",
        db_expired_ip_values,
        indexed_expired_ip_values,
        warn_nonzero=True,
    )

    secho("")
    secho(
        "After delete_ips + reindex, expired-and-present rows should be 0.", fg="blue"
    )


main()
