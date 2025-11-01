# Upstreaming the Latest-Build Role Administration Customisations

This document explains how to contribute the role-management tweaks from the `latest_build` instance back to the upstream projects so that we can drop the local overrides. The work spans three areas:

1. **Expose user roles in the administration UI with proper styling.**
2. **Use human-readable role identifiers (role names) across the groups service and admin views.**
3. **Keep the groups search index in sync after create/update/delete operations.**

Below you will find the recommended target packages, implementation notes, testing hints, and cleanup steps for each part.

---

## 1. Rich Role Metadata in the Administration UI

- **Target package:** `invenio-users-resources`
- **Source files in this repo:** `site/latest_build/accounts/patches.py`
- **Goal:** Ensure the `UsersService` search/list endpoints expose both a list of roles and an HTML fragment with Semantic UI labels, so the admin UI can render role chips without local overrides.

### Proposed upstream changes

1. Extend `UserAggregateModel` (or provide a dedicated mixin) to cache role names, a comma-joined label, and optional pre-rendered markup.
2. Update `UserSchema` in `invenio_users_resources.services.schemas` to:
   - Expose a `roles` list field.
   - Expose an optional `roles_label` string.
   - Optionally expose a `roles_markup` string (ensure it is clearly documented and sanitised/marked safe for UI usage).
   - Guarantee that `profile.roles` stays in sync.
3. Adjust admin UI configuration in `invenio_app_rdm.administration.users.users` (or the relevant module) to consume the new fields directly, removing the need for runtime patching.

### Tests / validation

- Add a unit test covering the aggregate and schema changes to confirm role data is serialised correctly.
- Add an integration test hitting the `/api/users/all` endpoint to check that the payload contains the new fields.
- Document the new schema fields in `invenio-users-resources` release notes.

### Cleanup in this repo

- Once upstream is released and pinned, remove:
  - `UserAggregateModelWithRoles`, `UserWithRolesSchema`, and related helpers from `site/latest_build/accounts/patches.py`.
  - The admin column overrides (`roles_markup`) in the same file.

---

## 2. Name-Based Role Identifiers

- **Target package:** `invenio-users-resources`
- **Source files in this repo:** `site/latest_build/accounts/patches.py`, `site/latest_build/accounts/routes.py`, `site/latest_build/administration/roles.py`
- **Goal:** Make the groups resource (which represents roles) expose and accept role names as identifiers, matching the behaviour expected by the administration frontend.

### Proposed upstream changes

1. Modify `GroupAggregateModel` so its `id` property resolves to `role.name`, while preserving the database primary key in a separate attribute (e.g. `internal_id`). Make sure ES documents are written with `id = name`.
2. Update `GroupSchema` to expose the internal UUID only if truly needed; otherwise rely on the name.
3. Ensure the search and CRUD APIs in `GroupsResource` and `GroupsService` accept and return role names consistently.
4. Update the admin configuration shipped in `invenio-app-rdm` so it no longer assumes UUID identifiers. This includes setting `pid_path = "name"` and removing redundant identifier columns.

### Tests / validation

- Add/adjust service tests to cover `read`, `update`, `delete`, and search operations using role names.
- Add an API test verifying that role creation returns `id == name`.
- Confirm that existing indices migrate cleanly (provide a note or migration helper for operators to reindex groups).

### Cleanup in this repo

- Remove `GroupAggregateModelWithNameIdentifier` once the upstream aggregate honours the name.
- Delete `_serialize_role`’s manual identifier swapping and the admin list/detail overrides after upgrading.

---

## 3. Immediate Search Index Updates

- **Target package:** `invenio-users-resources`
- **Source files in this repo:** `site/latest_build/accounts/routes.py`
- **Goal:** Ensure the groups/roles search index is updated immediately when roles are created, edited, or deleted through the REST API.

### Proposed upstream changes

1. Inside the upstream `GroupsResource` or its service layer, call the indexer after successful create/update/delete operations. This may already happen via the UoW in other resources; align the groups service with that pattern if possible.
2. On rename, delete the old ES document keyed by the previous identifier to prevent dangling hits. This logic should live close to the service layer so every client benefits.
3. If the default REST blueprints already orchestrate service calls, consider adding the logic to service components rather than duplicating it in blueprints.

### Tests / validation

- Create a service test that renames a role and confirms the search results reflect the new name without duplicates.
- Add/extend API tests to ensure the index is updated immediately after delete (i.e. the role no longer appears in search hits).

### Cleanup in this repo

- Drop `_aggregate_role`, `_index_role`, `_delete_role_from_index`, and the related calls in `site/latest_build/accounts/routes.py` once the upstream service handles indexing.

---

## General Contribution Checklist

1. **Open issues/PRs upstream** describing the desired behaviour, referencing the local overrides for context.
2. **Port the changes** to the appropriate packages:
   - `invenio-users-resources`: aggregates, schemas, service/indexing logic.
   - `invenio-app-rdm`: admin view configuration updates.
3. **Write tests** that cover the new behaviour end-to-end.
4. **Document release notes** for each package highlighting the behavioural change (new fields, identifier semantics, indexing behaviour).
5. **Wait for upstream releases** and update `uv.lock`/`pyproject.toml` to pin the new versions.
6. **Remove local shims** (`patches.py`, `routes.py` helpers, etc.) and verify the instance still behaves as expected.

Following this plan will reduce maintenance on `latest_build` and ensure the wider community benefits from the improvements. Feel free to add PR references and tracking links to this document as work progresses.
