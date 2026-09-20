# Authlib migration plan

Maintainers joining the project should start with
[`AUTHLIB_MIGRATION_MAINTAINER_BRIEF.md`](AUTHLIB_MIGRATION_MAINTAINER_BRIEF.md).
It includes the AI-assistance disclosure, open PRs, local setup, validation
status, and review guidance.

## Goal and decision

Completely replace `flask-oauthlib-invenio`'s unmaintained Flask-OAuthlib/OAuthlib implementation with [Authlib](https://github.com/authlib/authlib), while preserving Invenio OAuth client and OAuth 2 server behaviour, endpoints, persisted data, supported OAuth flows, and the custom remote-provider extension surface. This is a coordinated major/breaking release, with a clear migration guide. The target is the installed Authlib 1.8.0 (pin a tested compatible range, rather than the currently unbounded latest version).

**Do not adopt Flask-Multipass for this migration.** Authlib is the OAuth/OIDC protocol client and authorization-server implementation required here. Flask-Multipass is a higher-level, pluggable *application login and identity* framework (LDAP/SAML/static/Authlib providers, identity mapping, provider selection). It neither replaces the OAuth 2 authorization server nor makes this migration smaller. Adding it would change the login architecture and public configuration. Reconsider it only in a separate project to unify multiple institutional authentication backends; it may use Authlib underneath, but is not a dependency of this work.

## Confirmed scope and compatibility baseline

The current package exposes:

- OAuth 1.0a and OAuth 2 remote clients (`OAuth`, `OAuthRemoteApp`, response/error helpers), including lazy `app_key` credentials, `tokengetter`, `authorize`, callback token exchange, signed API requests, and legacy provider factories.
- OAuth 1 and OAuth 2 authorization-server wrappers, decorators, validators, grants/tokens, cache and SQLAlchemy bindings.
- OAuth 2 authorization code, implicit, password, client-credentials, refresh-token, revocation, bearer-resource protection, and OAuth 1 flows.

In this checkout, the direct consumers are **invenio-oauthclient 9.1.1** and **invenio-oauth2server 6.1.0**. The latter is the active OAuth 2 server and uses cache-backed authorization codes; the former uses remote OAuth/OIDC providers (GitHub, ORCID, Globus, Keycloak and CERN OpenID among its tested integrations). No other local package imported this library in the searched sibling repositories.

## Architecture

1. Deliver an Authlib-based major release of the existing `flask-oauthlib-invenio` distribution and retain its `flask_oauthlib` namespace as the public compatibility shell. Reimplement that shell entirely on `Authlib`, `Flask`, and `invenio-cache`/Flask-Caching; remove direct runtime use of `oauthlib`, `requests-oauthlib`, and the legacy cache wrapper. Existing imports and configured custom provider classes must continue to load.
2. Build on Authlib's supported Flask integration points, not copied OAuthlib internals:
   - `authlib.integrations.flask_client.OAuth` for remote OAuth 1/2/OIDC clients;
   - `authlib.integrations.flask_oauth2.AuthorizationServer`, concrete grant classes, and `ResourceProtector`/bearer-token validator for the OAuth 2 server;
   - Authlib's Flask OAuth 1 authorization server integration for the public OAuth 1 server surface.
3. Keep Invenio-specific policy in Invenio packages: SQLAlchemy models, user login/identity signalling, scope policy, personal-access-token rules, UI views and REST CSRF handling belong in `invenio-oauth2server`, not a general protocol adapter.
4. Use an adapter design as a first-class public boundary. The rebuilt `flask_oauthlib.client` and `flask_oauthlib.provider` modules preserve their documented `OAuth`, `OAuthRemoteApp`, `OAuthResponse`, `OAuthException`, provider/decorator, registry, `remote_apps`, configuration and method contracts used by Invenio and instance-defined subclasses, while delegating protocol work to Authlib. Keep constructor arguments, overridable hooks and callback/request method signatures stable wherever technically possible. This shell is the supported public API for the major line, not a temporary shim; it must not retain any OAuthlib implementation.

## Delivery sequence

### 1. Discovery and contract freeze

- Record exact public imports/configuration used by released versions of `invenio-oauthclient` and `invenio-oauth2server`, and inventory representative deployed custom `OAUTHCLIENT_REMOTE_APP` subclasses and OAuth 1 users. Treat custom providers as a supported compatibility target.
- Turn the current observable contract into black-box tests before changing code: redirect URL/query parameters, state/session lifecycle, token request form/headers, parsed response shapes, errors/statuses, token storage, authorization-code expiry/one-time use, scope checks and revocation. Add inheritance/override contract tests for custom `OAuthRemoteApp` implementations.
- Retain and migrate OAuth 1 client/server support. Authlib provides Flask OAuth 1 integrations; it must be fully tested rather than silently removed because no local Invenio consumer uses it.

### 2. Implement and test the Authlib foundation

- Implement an Authlib remote-client registry and a `flask_oauthlib.client` adapter with a configuration translator from current `params` (`consumer_key`/`consumer_secret`, `authorize_url`, `access_token_url`, `base_url`, scopes and callback settings) to Authlib registration arguments (`client_id`, `client_secret`, `authorize_url`, `access_token_url`, `api_base_url`, `client_kwargs`). Preserve `app_key` dictionary and flat-config credential loading.
- Make `OAuthRemoteApp` an adapter/facade with stable subclass seams: preserve `authorize(callback=...)`, `authorized_response()`, `get/post/put/delete/patch()`, `request()`, `make_client()`, `expand_url()`, `tokengetter`, `pre_request`, lazy properties and normalized response/error objects. Delegation must allow existing custom subclasses to override these hooks without depending on Authlib private objects. Use Authlib's state handling; never retain the old session key merely by name without validating state/CSRF semantics.
- Port exceptional provider behaviour as explicit, tested provider adapters/configuration (e.g. GitHub token content type and API calls, Globus, ORCID, Keycloak, CERN OpenID). Drop obsolete generic provider factories unless an identified consumer uses them.
- Implement the OAuth 2 server around Authlib grant classes: authorization-code (cache-backed and one-time), implicit, password, client credentials and refresh token; implement revocation and a bearer-token validator/resource protector. Preserve each currently supported grant exactly at the endpoint level. Map `Client`, `Token`, scopes, expiry, active-user checks and personal-token policy to Authlib's required model methods/interfaces, behind extensible Invenio adapter/repository interfaces so new grants or authentication methods can be added without another protocol rewrite.
- Keep the current `/oauth/authorize`, `/oauth/token`, `/oauth/errors`, `/oauth/ping`, `/oauth/info`, and `/oauth/invalid` routes and their response contracts. Update views to call Authlib server APIs rather than Flask-OAuthlib decorators. Preserve authorization consent and error redirect/state behaviour.
- Replace `bind_cache_grant`, its obsolete `OAUTH2_CACHE_TYPE` values (`redis`, `simple`, etc.), and its separate cache construction with an Invenio-owned authorization-code repository backed by `invenio_cache.current_cache` (Flask-Caching). Use the instance's current `CACHE_TYPE`/`CACHE_REDIS_URL` configuration and supported Flask-Caching backend names (e.g. `flask_caching.backends.RedisCache`/`RedisCache` and `SimpleCache` for tests), not the deprecated Cachelib configuration vocabulary.
- Namespace all grant keys (for example `oauth2::authorization-code::<client-id>::<code>`), store only the data required to reconstruct the Authlib grant, use a bounded code TTL, and delete on use. For Redis, implement atomic consume with a supported Redis primitive; for non-atomic backends either document the development-only limitation or provide a backend-appropriate lock/consume implementation. Test Redis and SimpleCache explicitly.
- Port OAuth 1 client/server support if retained, using Authlib integrations and separate test fixtures. It must not depend on OAuthlib or `requests-oauthlib`.

### Database and Alembic migration assessment

**No new database table or Alembic migration is expected for the initial Authlib migration.** `flask-oauthlib-invenio` owns no production database models. Invenio's OAuth 2 server already persists clients and bearer/refresh tokens in `oauth2server_client` and `oauth2server_token`; authorization codes/grants are ephemeral cache entries, not rows. `invenio-oauthclient`'s `oauthclient_remoteaccount` and `oauthclient_remotetoken` tables also remain unchanged.

- Implement Authlib client, token and authorization-code interfaces as adapters over the existing models and cache repository. Add Python methods/properties where Authlib requires them; do not rename tables, columns, indexes, foreign keys, encryptors, token formats or stored scope format.
- Preserve existing access and refresh tokens across upgrade. Add an upgrade test that inserts records using the current schema, upgrades the package, validates them through Authlib and exercises refresh/revocation. No data copy, token rotation or Alembic revision should be necessary.
- PKCE and the retained implicit/password grants add only ephemeral authorization-request/code fields in the namespaced cache payload. They do not justify a table.
- Generate and run Alembic autogeneration/checks in `invenio-oauth2server` and `invenio-oauthclient` as a guard: the expected result is **no schema diff**. If implementation reveals an unavoidable persistent Authlib requirement, stop before adding a table and propose a separate, reversible Alembic revision with upgrade/downgrade, backfill, retention and token-compatibility plans.
- This assessment does not cover third-party applications that used the legacy package's optional `bind_sqlalchemy` helper: their models are application-owned. The migration guide must provide an Authlib repository/adapter example that maps their existing client/token/grant tables before recommending any schema change.

### 3. Migrate dependent Invenio libraries

- **invenio-oauthclient:** no production import or provider-base-class change should be required: retain `flask_oauthlib.client` imports, `app.extensions["oauthlib.client"]`, `OAuthRemoteApp` subclass hooks and existing configuration through the rebuilt shell. Update dependency bounds, examples/docs and tests only where Authlib behaviour exposes a deliberate compatibility correction.
- **invenio-oauth2server:** retain `flask_oauthlib.provider.OAuth2Provider` and `flask_oauthlib.contrib.oauth2.bind_cache_grant` imports through the rebuilt shell where their compatible adapters suffice. Remove its *direct* `oauthlib.*` imports, request parsing monkey patches and legacy cache configuration because OAuthlib will no longer be installed; replace them with public shell/Authlib-compatible error/request APIs and Invenio-Cache configuration. Keep models, routes, schemas and stored token formats unchanged.
- Update package dependency bounds, constraints/lock files, editable-instance setup, documentation and examples across all three repositories. Release coordinated compatible versions: consumers must require the new package before the old package is removed.

### 4. Validation, release and removal

- Run unit, integration and style/type checks for the replacement package, `invenio-oauthclient`, `invenio-oauth2server`, and the full Invenio instance dependency set in clean environments. Add CI jobs for the supported Python/Flask/Authlib matrix.
- Add end-to-end browser/test-client flows for each configured remote provider and all server grants, including negative cases: missing/tampered/replayed state, redirect URI mismatch, invalid client credentials, inactive users, expired/replayed/revoked tokens, insufficient scopes, malformed authorization headers, and Redis/cache failure.
- Test upgrade with pre-existing `Client`, `Token`, and remote-account records and with active bearer tokens. Verify intentional token compatibility; if token validation semantics change, publish a rotation/revocation procedure.
- Ship the Authlib replacement as the coordinated major release with a migration guide, configuration translator, provider-subclass migration cookbook, compatibility matrix and exact list of intentionally removed low-level APIs. Retain the import/provider adapter in this release to minimize operational breakage. Remove `oauthlib` and `requests-oauthlib` runtime dependencies and verify no implementation path uses them; defer removal of the compatibility namespace to a separately announced future major release.

## Expected breaking changes

- Direct imports of the separately installed `oauthlib` package and its request validators/server internals are intentionally removed; use the rebuilt `flask_oauthlib` public adapters or Authlib APIs instead. This is the principal major-version API break and the migration guide must map each supported use case.
- Preserve `flask_oauthlib` client/provider imports, `app.extensions["oauthlib.client"]`, configuration names/shapes, `bind_cache_grant`, and `OAuthRemoteApp` subclass hooks through adapters. The old configuration shape remains supported in this major line.
- Session key names, response wrapper types, exception classes, HTTP-client behaviour, default state generation, token parsing and error text may differ internally. Treat endpoint status/redirect/error parameters, custom-provider behaviour and persisted token data as compatibility contracts; do not promise Authlib/private-object identity.
- Retain implicit and resource-owner-password grants exactly as currently supported, despite their security-deprecated status. Do not alter existing clients by enabling PKCE as mandatory; add it as a compatible, configurable capability for future clients.

## Principal risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Authlib is not a drop-in Flask-OAuthlib API replacement | Use the native architecture and contract tests; limit and time-box the compatibility facade. |
| OAuth 2 flow/security regression, especially state, redirect URI, scopes or code replay | Security review plus negative and replay tests; strict redirect matching; state validation; atomic code consumption. |
| Existing external OAuth clients/providers reject changed request details | Capture legacy request/response fixtures and run provider sandbox/contract tests before rollout. |
| Cached grants, cache backend configuration, existing tokens or timezone handling change | Move grants to `invenio_cache.current_cache` with namespaced keys and migration warnings for `OAUTH2_CACHE_*`; test Redis and SimpleCache upgrades, model/token compatibility and UTC expiry; explicitly rotate only if required. |
| OAuth 1 or custom remote apps are silently lost | Inventory users first; retain and test Authlib OAuth 1 support or announce a major removal. |
| Broad dependency upgrade destabilizes unrelated Invenio packages | Coordinate bounds/releases, use a clean lockfile and test the full dependency graph before removal. |

## Confirmed decisions and remaining input

- This is a complete Authlib replacement and coordinated breaking major release, not a partial migration. `flask-oauthlib-invenio` remains installed only as a rewritten Authlib-backed public compatibility shell; no legacy OAuthlib code or dependencies remain. It requires migration documentation for every intentional break.
- Existing custom client providers are a supported target. The rebuilt `flask_oauthlib` public surface preserves provider/client imports and must be validated against representative real custom subclasses.
- Keep implicit and password grants behaviourally compatible. Make the new server architecture extensible for future grants/authentication mechanisms.
- Cache decision: authorization codes move from the deprecated per-OAuth Cachelib configuration to the instance-wide Invenio-Cache/Flask-Caching backend. `OAUTH2_CACHE_TYPE` and `OAUTH2_CACHE_REDIS_*` are deprecated; `CACHE_TYPE` and `CACHE_REDIS_URL` are authoritative.
- Remaining operational input: provide representative custom provider subclasses and any deployed OAuth 1 integrations for the compatibility test suite, and choose the package/version naming and support window for the retained `flask_oauthlib` adapter.


## Current implementation status

The Authlib-backed compatibility implementation and security hardening are in place across the three migration branches. The latest `flask-oauthlib-invenio` run passes all 156 tests, including Redis-backed concurrent authorization-code consumption. The concurrent test workers create their own Flask application contexts when using `invenio_cache.current_cache`.

The two previous review questions are resolved. Revoked persisted tokens are deleted through `Token.delete()`, so loaded token rows correctly report `is_revoked() == False`. Python 3.10 is the supported minimum because Authlib 1.8 requires Python 3.10 or newer; this intentional compatibility break is documented in the Flask package's migration guide.

For coordinated PR testing, `invenio-oauthclient` and `invenio-oauth2server` temporarily depend directly on `flask-oauthlib-invenio` PR 7. Their full local suites and GitHub CI still need to be rerun against that dependency. Replace the Git references with bounded release requirements once the compatibility package is published. The remaining implementation work is otherwise limited to the operational validation in `AUTHLIB_MIGRATION_SECURITY_HANDOFF.md`.

## Open PRs 

### invenio-oauth2server
https://github.com/inveniosoftware/invenio-oauth2server/pull/317
`../invenio-oauth2server`

### flask-oauthlib-invenio
https://github.com/inveniosoftware/flask-oauthlib-invenio/pull/7
`../flask-oauthlib-invenio`

### invenio-oauthclient
https://github.com/inveniosoftware/invenio-oauthclient/pull/394
`../invenio-oauthclient`
