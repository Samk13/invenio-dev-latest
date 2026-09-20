# Authlib migration security handoff

## Scope and baseline

This handoff covers the Authlib migration branches in:

- `flask-oauthlib-invenio`
- `invenio-oauthclient`
- `invenio-oauth2server`

The compatibility namespace remains `flask_oauthlib`, but protocol handling is backed by Authlib. Existing persisted OAuth client, token, remote-account, and remote-token rows remain compatible; no schema migration is expected.

## Security findings resolved

### PKCE fails closed for unsupported repositories

Cache-backed authorization codes retain `code_challenge` and `code_challenge_method`, and S256 exchanges require the correct verifier. A custom or SQLAlchemy grant repository that does not explicitly advertise PKCE field support rejects PKCE authorization requests instead of silently downgrading them.

Regression coverage includes successful S256 exchange, missing/wrong verifiers, and fail-closed SQLAlchemy behavior.

### Atomic Redis authorization-code consumption

Authorization-code grants now use only Invenio-Cache's public API. A bounded-lifetime `cache.add()` consumption marker is atomic on distributed backends such as Redis and remains in place after consumption so an interrupted consumer fails closed. The implementation no longer creates a separate Redis client or accesses Flask-Caching private clients, prefixes, or serializers.

The Redis URL is supplied through the test environment, and coverage includes concurrent consumption where exactly one consumer succeeds. Each concurrent test worker now establishes its own Flask application context before accessing `invenio_cache.current_cache`, matching production request handling.

### Invenio-Cache dependency and initialization

`invenio-oauth2server` directly declares bounded `invenio-cache>=3.0.0,<4.0.0`. Normal Invenio extension loading remains the supported initialization path. Direct extension use requires Invenio-Cache to be initialized first; tests cover this contract.

### OAuth client callback state

`OAuthRemoteApp.authorized_response()` now delegates callback processing to Authlib's supported `authorize_access_token()` API. It no longer calls private Authlib framework state methods.

Authlib protocol state and Invenio application state no longer conflict:

- a random protocol state is generated for each login and persisted by Authlib;
- signed Invenio state (`app`, `next`, `sid`) is stored separately in the Flask session under a key derived from protocol state;
- callback handling consumes that application-state entry before invoking the provider handler;
- missing, mismatched, tampered, and replayed state is rejected before token exchange.

OIDC can opt into Authlib ID-token/nonce validation with `parse_id_token=True` and `server_metadata_url`. Existing providers that validate ID tokens themselves retain the raw `id_token`. PKCE verifier data remains managed by Authlib state handling.

### Legacy callback bypass closed

`handle_oauth2_response(args)` no longer performs a stateless exchange. Arguments must match the active callback request and processing delegates to the state-validating callback path.

### Obsolete OAuthlib parser configuration removed

`OAUTH2SERVER_ALLOWED_URLENCODE_CHARACTERS`, its warning-only monkeypatch, and obsolete tests were removed from `invenio-oauth2server`. Authlib uses Flask/Werkzeug request parsing and has no equivalent global OAuthlib parser patch.

### Legacy token transport controls

Applications can disable legacy transport with:

```python
OAUTH2_ALLOW_LEGACY_TOKEN_ENDPOINT_GET = False
OAUTH2_ALLOW_LEGACY_BEARER_TOKEN_TRANSPORT = False
```

The first setting enforces POST token requests. The second rejects query-string and form-body bearer credentials, requiring the Authorization header. Compatibility defaults remain enabled and are documented as deprecated because URL/form credentials can leak through logs, history, and referrers.

### OAuth 1 signature coverage

HMAC-SHA1 and RSA-SHA1 requests are signed with real fixtures and verified using Authlib's signature verifiers. OAuth1 request-token callback binding and configured RSA key forwarding are also covered.

### Token revocation compatibility

`invenio-oauth2server.models.Token.delete()` now owns persisted-token deletion and commits through the Invenio database session. Both the released provider's legacy revocation validator and the migrated Authlib provider can therefore revoke tokens without an import-time dependency on a new provider decorator. `is_revoked()` intentionally returns `False` because revoked rows are deleted and cannot subsequently be loaded as active tokens.

### Python support decision

The three migration branches require Python 3.10 or newer. This is intentional: the migration targets Authlib 1.8, whose package metadata requires Python 3.10 or newer. Retaining Python 3.9 support would advertise an unsatisfiable dependency combination. The reason is documented in `flask-oauthlib-invenio/docs/authlib-migration.rst`, and the downstream CI matrices include Python 3.10, 3.12, and 3.14.

### Coordinated PR dependencies

Until the migrated compatibility package is released, `invenio-oauthclient` and `invenio-oauth2server` install `flask-oauthlib-invenio` directly from PR 7. Hatch direct references are enabled for these temporary dependencies. This prevents CI from resolving the incompatible released `flask-oauthlib-invenio==2.0.0`. Replace the PR references with final version bounds after the compatibility package is released.

## Validation completed

The following suites passed before the temporary PR dependency references and latest revocation compatibility change:

```text
flask-oauthlib-invenio: 156 passed
invenio-oauthclient:    164 passed, 8 skipped
invenio-oauth2server:    59 passed, 1 skipped
```

The Redis-backed tests ran with the standard `docker-services-cli --cache redis` configuration and include concurrent one-time authorization-code consumption through Invenio-Cache. The complete `flask-oauthlib-invenio` suite was rerun after correcting the worker application contexts and passes with 156 tests. The downstream suites must be rerun to validate their latest dependency and revocation commits.

A live callback initially continued to fail because the instance loaded the
released `invenio-oauthclient` copy from `site-packages` while loading the
migrated `flask-oauthlib-invenio` checkout. The development environment now
installs `invenio-oauthclient` from its editable migration checkout as well.
Regression tests assert that protocol and application state remain separate and
that missing Authlib state returns 403 without making a token request.

Previously completed manual checks on the live InvenioRDM instance covered local login/logout and GitHub/ORCID login. The original GitHub `MismatchingStateError` was caused by using Invenio's signed application token as Authlib protocol state; the separated state design above fixes that conflict.

## Operational validation still required

These are environment/release checks, not unresolved implementation findings:

1. Rerun the complete `invenio-oauthclient` and `invenio-oauth2server` suites and confirm GitHub CI uses `flask-oauthlib-invenio` PR 7 rather than the released package.
2. Run PostgreSQL-specific Alembic tests for `invenio-oauthclient` and `invenio-oauth2server`.
3. Rebuild/reinstall the three changed packages in the live instance and restart all web/worker processes before retesting.
4. Re-run live HTTPS flows for:
   - GitHub and ORCID callback state;
   - valid, expired, revoked, malformed, and insufficient-scope bearer tokens;
   - authorization-code replay;
   - PKCE success and wrong/missing verifier;
   - invalid redirect URI and invalid/replayed state;
   - refresh-token rotation;
   - strict legacy transport settings.
5. Recheck the live `POST /oauth/token` route. It previously returned a themed 404 despite `OPTIONS` advertising POST, which may be an instance routing/deployment issue.
6. After PR 7 is released, replace both temporary Git references with bounded release requirements and disable Hatch direct references if they are no longer needed.

## Commands

```bash
cd ../flask-oauthlib-invenio
./run-tests.sh tests -q

cd ../invenio-oauth2server
DB=postgresql ./run-tests.sh tests/test_alembic.py -q
.venv/bin/python -m pytest tests -q -o addopts=''

cd ../invenio-oauthclient
DB=postgresql ./run-tests.sh tests/test_alembic.py -q
.venv/bin/python -m pytest tests -q -o addopts=''
```
