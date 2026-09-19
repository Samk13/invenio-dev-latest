# Authlib migration security-review handoff

## Resolution status

Resolved in the working trees on 2026-03-12. The implementation now rejects OAuth 2 callbacks before token exchange when state is missing/mismatched/replayed, binds authorization POSTs to validated consent GETs, validates all redirect targets, forwards OAuth 1 RSA keys and binds OAuth 1 callbacks to request tokens, supports optional PKCE, and exercises Redis through Invenio-Cache's test extra. Cache backend selection uses ``CACHE_TYPE`` (for example ``RedisCache`` or ``SimpleCache``); legacy ``OAUTH2_CACHE_TYPE`` was removed rather than renamed because it is no longer read.

Validation completed:

- `flask-oauthlib-invenio`: 146 passed, including live Redis cache consumption.
- `invenio-oauth2server`: 61 passed, 1 skipped.
- `invenio-oauthclient`: 162 passed, 8 skipped.

PostgreSQL-specific Alembic runs and live-instance browser/API checks remain operational follow-up tasks.

## Scope reviewed

Reviewed `master..HEAD` and current source in:

- `../flask-oauthlib-invenio`
- `../invenio-oauthclient`
- `../invenio-oauth2server`

against `AUTHLIB_MIGRATION_PLAN.md`, with emphasis on state, consent/redirect URI binding, grant replay, token/resource protection, CSRF, and OAuth 1 signatures. This is a code review, not a completed penetration test.

Current migration commits include `52c605a fix(provider): restore resource verification`. `invenio-oauth2server` has an unrelated untracked `invenio_oauth2server/errors-to-fix.md`.

## Block release: fix before deploying

### 1. OAuth 2 client accepts a callback after state validation fails

**Location:** `../flask-oauthlib-invenio/flask_oauthlib/client.py`, `OAuthRemoteApp.authorized_response()`.

`MismatchingStateError` falls back to `handle_oauth2_response()` whenever `code` is present. The generic `OAuthError` path repeats the fallback. This explicitly defeats Authlib's state validation and permits login CSRF/account-linking attacks for any caller using the compatibility shell directly. It conflicts with the plan's requirement to use Authlib state handling and preserve state/CSRF semantics.

**Required fix:** Never exchange a code after a missing, mismatched, tampered, or replayed state. Return the legacy callback error shape only if that can be done without token exchange; otherwise raise `OAuthException`. If an identified legacy flow truly has no state, make it an explicit, opt-in, loudly documented insecure compatibility switch—not the default.

**Tests required:** start an authorization request, then callback with missing/tampered/replayed state plus a valid code; assert no token HTTP request occurs and no login/token persistence occurs. Preserve a normal state-validated callback test.

### 2. Direct POST to `/oauth/authorize` can bypass validated consent-request data; empty scope is an open redirect

**Location:** `../flask-oauthlib-invenio/flask_oauthlib/provider/oauth2.py`, `OAuth2Provider.authorize_handler()` and `confirm_authorization_request()`.

Only GET calls `server.get_consent_grant()`, which validates the authorization request and obtains the validated client/redirect URI. A POST directly invokes the application handler and then `confirm_authorization_request()` with attacker-controlled form values. Worse, the special empty-scope branch directly executes:

```python
redirect_uri = request.values.get("redirect_uri") or self.error_uri
return redirect(redirect_uri + "?error=Scopes+must+be+set")
```

Thus an authenticated victim can POST `confirm=yes`, `scope=` and `redirect_uri=https://attacker.example` to obtain an open redirect. More broadly, consent approval/denial must be bound to the previously validated authorization request, not values posted by the browser.

**Required fix:** Remove the direct empty-scope redirect. On both approval and denial, have Authlib construct the response only from a newly validated request or a server-side, integrity-protected authorization-request/consent transaction. Do not redirect to a URI until the client and exact redirect URI have been validated. Ensure POST cannot approve an authorization request that was never displayed/validated.

**Tests required:** authenticated direct POST with malicious redirect URI, empty scope, mismatched client/redirect URI, and altered state must not redirect off-site or issue a code/token. Normal approval and denial must redirect only to the registered URI and preserve state.

## Important gaps to resolve

### 3. OAuth 1 RSA signatures are no longer wired through

**Location:** `../flask-oauthlib-invenio/flask_oauthlib/client.py`, `_oauth1_auth()`.

The compatibility constructor retains `rsa_key`, but `_oauth1_auth()` constructs Authlib `ClientAuth` without it. Authlib therefore cannot make RSA-SHA1 OAuth 1 client signatures through this path. This violates the plan's retained OAuth 1/custom-user compatibility target if any deployment uses RSA signatures.

**Fix/test:** pass and validate `rsa_key` using Authlib's supported API, or explicitly announce/remove the compatibility argument in the major migration guide after inventory proves it unused. Add a signed request fixture for every retained signature method (at least HMAC-SHA1 and RSA-SHA1 if supported).

### 4. PKCE capability is absent

The plan requires a compatible, configurable PKCE capability for future clients, with verifier/challenge data in the ephemeral grant payload. The reviewed Authlib grant registration/cache payload has no `code_challenge`, `code_challenge_method`, or `code_verifier` handling.

**Fix/test:** add Authlib PKCE support to authorization-code grants without making it mandatory for existing clients. Test S256 success, missing/wrong verifier rejection, and that legacy non-PKCE clients remain compatible.

### 5. Required negative end-to-end coverage remains incomplete

The plan calls for missing/tampered/replayed state, redirect mismatch, invalid credentials, inactive users, expired/replayed/revoked tokens, insufficient scope, malformed Authorization headers, and Redis/cache failure. Existing tests cover substantial model/cache and provider registration work, but do not prove all of those flows end-to-end. The two block-release cases above are not covered and would have caught the regressions.

Add endpoint-level tests using real Authlib request parsing and the `invenio-oauth2server` views, not only adapter mocks. Include authorization-code one-time consumption under Redis and failure behavior when the cache is unavailable.

### 6. Redis validation is still environment-dependent and may be skipped

`c12282a` skips the Redis cache test when Redis support is absent. That makes developer tests robust but does not meet the plan's explicit Redis validation requirement. `OAUTH2_CACHE_TYPE = "redis"` also remains in `invenio_oauth2server/config.py` even though the plan calls this obsolete; authoritative configuration must be `CACHE_TYPE`/`CACHE_REDIS_URL` through Invenio-Cache.

**Fix:** make CI/service-backed `./run-tests.sh tests/test_contrib/test_oauth2_cache.py -q` provision/configure Redis and fail if the Redis-specific test is skipped there. Deprecate/remove the unused `OAUTH2_CACHE_TYPE` default and document the replacement configuration.

OAUTH2_CACHE_TYPE = "redis" is legacy and should be upgraded to the new OAUTH2_CACHE_TYPE = "RedisCache" that also apply to all other cache types; double check that and fix it as well

## Things that look correct but should be regression-tested in the integrated app

- `52c605a` restored `_CompatAuthorizationServer.verify_request()`; `invenio-oauth2server.ext.verify_request()` delegates through `oauth2.verify_request(scopes)`, and resource protection uses Authlib's `ResourceProtector`.
- The REST CSRF bypass is set only after a bearer token validates (`request.oauth` exists). Confirm valid token behavior still goes through endpoint permission/scope checks and invalid/malformed tokens never set `skip_csrf_check`.
- Cache grants use namespaced keys and attempt atomic Redis `GETDEL`; retain the SimpleCache one-time-use test and add the real Redis concurrency/replay test.
- Existing Alembic no-diff and persisted client/token/remote-token tests are a good start; run them against PostgreSQL as planned.

## Suggested execution order

1. Fix state fallback and add the no-token-exchange regression tests.
2. Fix authorization POST/redirect binding and add direct-POST/empty-scope tests.
3. Run focused suites in all three repos, then full suites.
4. Implement or explicitly defer/document RSA OAuth1 and PKCE only after a compatibility decision; PKCE is stated as required by the plan.
5. Make Redis CI mandatory, run PostgreSQL Alembic checks, then do live valid/expired/revoked/insufficient-scope token tests.
6. Add the missing migration guide: removed OAuthlib APIs/dependencies, cache configuration, OAuth1 status/signature support, provider subclass hooks, PKCE, and no-schema-migration guarantee.

## Commands

```bash
cd ../flask-oauthlib-invenio
./run-tests.sh tests -q
./run-tests.sh tests/test_contrib/test_oauth2_cache.py -q

cd ../invenio-oauthclient
DB=postgresql ./run-tests.sh tests/test_alembic.py -q

cd ../invenio-oauth2server
DB=postgresql ./run-tests.sh tests/test_alembic.py -q
```
