# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

from click import secho
from opensearchpy.helpers import bulk

from invenio_accounts.models import User
from invenio_accounts.proxies import current_datastore
from invenio_search.proxies import current_search, current_search_client
from invenio_users_resources.records.api import UserAggregate, GroupAggregate

secho("Deleting old users/groups indices...", fg="yellow", bold=True)

deleted = list(current_search.delete(index_list=[
    "users-user-v1.0.0",
    "users-user-v2.0.0",
    "users-user-v3.0.0",
    "groups-group-v1.0.0",
    "groups-group-v2.0.0",
]))

secho("Deleted:", fg="red", bold=True)
for name, result in deleted:
    secho(f"  ✓ {name}: {result}", fg="red")

secho("Creating latest users/groups indices...", fg="yellow", bold=True)

created = list(current_search.create(index_list=[
    "users-user-v3.0.0",
    "groups-group-v2.0.0",
]))

secho("Created:", fg="green", bold=True)
for name, result in created:
    secho(f"  ✓ {name}: {result}", fg="green")

USERS_INDEX = next(
    name for name, _ in created
    if name.startswith("latest-build-users-user-v3.0.0-")
)

GROUPS_INDEX = next(
    name for name, _ in created
    if name.startswith("latest-build-groups-group-v2.0.0-")
)

secho(f"Users index: {USERS_INDEX}", fg="cyan", bold=True)
secho(f"Groups index: {GROUPS_INDEX}", fg="cyan", bold=True)

Role = current_datastore.role_model


def user_actions():
    for user_model in User.query.yield_per(1000):
        record = UserAggregate.from_model(user_model)
        source = record.dumps()
        yield {
            "_op_type": "index",
            "_index": USERS_INDEX,
            "_id": str(record.id),
            "_source": source,
            "_version": source["version_id"],
            "_version_type": "external_gte",
        }


def group_actions():
    for role_model in Role.query.yield_per(1000):
        record = GroupAggregate.from_model(role_model)
        source = record.dumps()
        yield {
            "_op_type": "index",
            "_index": GROUPS_INDEX,
            "_id": str(record.id),
            "_source": source,
            "_version": source["version_id"],
            "_version_type": "external_gte",
        }


secho("Reindexing users...", fg="yellow", bold=True)

users_result = bulk(
    current_search_client,
    user_actions(),
    stats_only=True,
)

secho("Reindexing groups...", fg="yellow", bold=True)

groups_result = bulk(
    current_search_client,
    group_actions(),
    stats_only=True,
)

current_search_client.indices.refresh(index=USERS_INDEX)
current_search_client.indices.refresh(index=GROUPS_INDEX)

secho(
    f"Users indexed: {users_result[0]}, failures: {users_result[1]}",
    fg="green" if users_result[1] == 0 else "red",
    bold=True,
)

secho(
    f"Groups indexed: {groups_result[0]}, failures: {groups_result[1]}",
    fg="green" if groups_result[1] == 0 else "red",
    bold=True,
)

user_count = current_search_client.count(index=USERS_INDEX)["count"]
group_count = current_search_client.count(index=GROUPS_INDEX)["count"]

secho(f"User count: {user_count}", fg="blue", bold=True)
secho(f"Group count: {group_count}", fg="blue", bold=True)

secho("Migration completed successfully.", fg="green", bold=True)
