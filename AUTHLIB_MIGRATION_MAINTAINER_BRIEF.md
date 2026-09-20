# Maintainer brief: Flask-OAuthlib to Authlib migration

## Why this document exists

This is a coordinated migration of Invenio's OAuth client and authorization
server stack from the unmaintained Flask-OAuthlib/OAuthlib implementation to
Authlib 1.8.

The work is **AI-assisted**. Multiple coding-agent sessions have been used to
inventory the old behavior, implement the compatibility layer, add security
regressions, investigate failures, and maintain the handoff documents. A human
is curating the work, running tests, reviewing findings, and coordinating the
pull requests. The use of agents does not replace normal maintainer review,
security review, or release validation. Reviewers should treat the changes like
any other substantial authentication and authorization rewrite.

This document is the entry point for maintainers joining the effort. Detailed
planning, security decisions, and current validation notes are in:

- [`AUTHLIB_MIGRATION_PLAN.md`](AUTHLIB_MIGRATION_PLAN.md)
- [`AUTHLIB_MIGRATION_SECURITY_HANDOFF.md`](AUTHLIB_MIGRATION_SECURITY_HANDOFF.md)

## Open pull requests

Review the compatibility package first because both downstream PRs depend on
it.

| Order | Repository | Pull request | Local checkout |
| --- | --- | --- | --- |
| 1 | `flask-oauthlib-invenio` | [PR #7](https://github.com/inveniosoftware/flask-oauthlib-invenio/pull/7) | `../flask-oauthlib-invenio` |
| 2 | `invenio-oauth2server` | [PR #317](https://github.com/inveniosoftware/invenio-oauth2server/pull/317) | `../invenio-oauth2server` |
| 3 | `invenio-oauthclient` | [PR #394](https://github.com/inveniosoftware/invenio-oauthclient/pull/394) | `../invenio-oauthclient` |

Current local branch names are:

- `flask-oauthlib-invenio`: `test-oauthlib-migration-test-01`
- `invenio-oauth2server`: `test-oauthlib-migration-01`
- `invenio-oauthclient`: `test-oauthlib-migration-01`

## What changed

### Compatibility package

The `flask-oauthlib-invenio` distribution remains installed and keeps the
public `flask_oauthlib` namespace, but its protocol implementation is now
backed by Authlib. This minimizes changes for Invenio packages and existing
custom providers while removing runtime use of `oauthlib` and
`requests-oauthlib` this is debatable if we should also change this as well.

The compatibility layer retains the important public surfaces:

- `OAuth`, `OAuthRemoteApp`, response helpers, and the remote-app registry;
- lazy application credentials and existing configuration shapes;
- `authorize()`, `authorized_response()`, token getters, request helpers, and
  custom remote-app override hooks;
- `OAuth2Provider`, provider decorators, grant/token callbacks, and resource
  protection;
- OAuth 1 client/server compatibility using Authlib;
- authorization code, implicit, password, client credentials, refresh token,
  revocation, and bearer-token flows.

Direct imports of the separately installed OAuthlib package and its private
validators/server internals are intentionally no longer supported.

### OAuth client

`invenio-oauthclient` continues using the `flask_oauthlib` compatibility API.
The main migration changes are:

- Authlib owns OAuth protocol state and token exchange;
- Invenio's signed application state (`app`, `next`, and `sid`) is stored
  separately and keyed by Authlib's random protocol state;
- missing, mismatched, tampered, and replayed callback state fails before token
  exchange;
- EOSC AAI PKCE uses Authlib's standard `client_kwargs` support instead of a
  custom stateful `OAuthRemoteApp` subclass;
- existing provider-specific token and identity handlers remain in Invenio.

### OAuth 2 server

`invenio-oauth2server` retains its routes, models, scopes, token formats, and
public integration points while delegating protocol work to Authlib.

Notable changes include:

- Authlib authorization grants and bearer resource protection;
- one-time cache-backed authorization codes through Invenio-Cache;
- PKCE support that fails closed when a custom repository cannot persist PKCE
  fields;
- token revocation through `Token.delete()` and the Invenio database session;
- optional strict settings for token endpoint methods and bearer transport;
- removal of the obsolete OAuthlib URL-encoded parser monkeypatch.

No database or Alembic schema migration is expected. Existing client, token,
remote-account, and remote-token rows remain in their current tables and
formats.

## Security-sensitive decisions

The following behavior has dedicated regression coverage and deserves focused
review:

- OAuth callback state is mandatory, separated from application state, and
  consumed once.
- Authorization consent POSTs are bound to a validated consent request.
- Redirect URIs are checked before success and error redirects.
- PKCE supports `plain` and `S256`; missing or incorrect verifiers fail.
- Redis authorization codes use an atomic, bounded-lifetime consumption marker.
- OAuth 1 HMAC-SHA1 and RSA-SHA1 requests use real signatures in tests.
- Legacy GET token requests and query/form bearer tokens remain enabled by
  default for compatibility, but can be disabled with:

  ```python
  OAUTH2_ALLOW_LEGACY_TOKEN_ENDPOINT_GET = False
  OAUTH2_ALLOW_LEGACY_BEARER_TOKEN_TRANSPORT = False
  ```

The compatibility defaults above are deprecated because credentials in URLs or
form bodies can leak through logs, browser history, and referrers.

## Python support

The migrated packages require Python 3.10 or newer. The old packages supported
Python 3.9, but Authlib 1.8 itself requires Python 3.10 or newer. Keeping Python
3.9 in package metadata would therefore advertise an unsatisfiable dependency
combination.

The downstream CI matrices cover Python 3.10, 3.12, and 3.14. The
`flask-oauthlib-invenio` matrix currently covers 3.12 and 3.14 and should also
exercise Python 3.10, its declared minimum.

## Temporary cross-PR dependency

The released `flask-oauthlib-invenio==2.0.0` is the legacy implementation and
does not contain the new APIs. Installing it caused downstream failures such as
an unsupported `client_kwargs` argument and a missing provider revocation hook.

Until PR #7 is released, both downstream projects temporarily depend on:

```text
flask-oauthlib-invenio @ git+https://github.com/inveniosoftware/flask-oauthlib-invenio.git@refs/pull/7/head
```

Hatch direct references are enabled solely to support coordinated PR testing.
This reference is mutable and is not suitable for a final release. After PR #7
is published:

1. replace the Git references with bounded release requirements;
2. remove `allow-direct-references` if no other direct references remain;
3. regenerate dependency resolution and rerun all CI jobs.

## Broader package impact

An audit of the development instance found no additional package importing
`flask_oauthlib` directly. However, several packages depend on or import the two
downstream Invenio packages and must be included in integration testing and
release coordination:

| Package | Relationship | Expected action |
| --- | --- | --- |
| `invenio-app-rdm` | Requires both `invenio-oauthclient` and `invenio-oauth2server` | Run full instance tests and update upper bounds if either downstream package receives a major version. |
| `invenio-rdm-records` | Requires `invenio-oauth2server`; imports `Token` and `Scope`; contributes an OAuth scope entry point | Test resource-access tokens and update the dependency bound for a server major release. |
| `invenio-users-resources` | Requires `invenio-oauthclient` | Run integration tests and update the dependency bound for an OAuth client major release. |
| `invenio-vcs` | Optional integration importing OAuth client models/helpers and OAuth server tokens | It is not part of the required migration path. Test GitHub/GitLab linking separately if optional VCS compatibility is retained. |
| `invenio-github` | Deprecated package importing OAuth client models/helpers and OAuth server tokens | No migration work is planned. Do not use it as a release blocker; direct users should move to a supported integration. |
| `invenio-stats` | Uses OAuth server tokens in tests | Run its test suite against the migrated server if it remains in the supported matrix. |
| Instance/meta package | Selects all three migration packages | Regenerate its lock and constraints after final versions are chosen. |

`Flask-Multipass` is installed and has an optional Authlib extra, but it does
not consume this compatibility package or replace the OAuth authorization
server. No migration change is currently required there.

The audited virtual environment still contains stale `oauthlib` and
`requests-oauthlib` installations plus old editable `egg-info` metadata, even
though the current root lock no longer selects those libraries. Use a clean
environment or run a synchronized install before final dependency verification;
do not treat the presence of those stale packages as a current runtime
requirement.

If `flask-oauthlib-invenio`, `invenio-oauthclient`, or
`invenio-oauth2server` is released with a new major version—as intended by the
migration plan—the upper bounds in the packages above must be updated in
coordinated PRs. If maintainers choose to preserve the current major versions,
the bounds already accept them, but that choice must be reconciled with the
migration's documented breaking changes.

## Local setup

Clone the repositories as siblings so the commands and handoffs use the same
layout:

```bash
mkdir authlib-migration
cd authlib-migration

gh repo clone inveniosoftware/flask-oauthlib-invenio
gh repo clone inveniosoftware/invenio-oauth2server
gh repo clone inveniosoftware/invenio-oauthclient

(cd flask-oauthlib-invenio && gh pr checkout 7)
(cd invenio-oauth2server && gh pr checkout 317)
(cd invenio-oauthclient && gh pr checkout 394)
```

Create isolated environments with Python 3.10 or newer. Python 3.12 is the
currently exercised local version:

```bash
cd flask-oauthlib-invenio
uv venv --python 3.12
uv pip install --python .venv/bin/python -e ".[tests]"
cd ..

cd invenio-oauth2server
uv venv --python 3.12
uv pip install --python .venv/bin/python -e ".[tests,admin]"
cd ..

cd invenio-oauthclient
uv venv --python 3.12
uv pip install --python .venv/bin/python -e ".[tests,admin]"
cd ..
```

The downstream metadata currently installs PR #7. For local development of
uncommitted compatibility-package changes, override it with the sibling
checkout:

```bash
uv pip install --python invenio-oauth2server/.venv/bin/python \
  -e ./flask-oauthlib-invenio
uv pip install --python invenio-oauthclient/.venv/bin/python \
  -e ./flask-oauthlib-invenio
```

Confirm that the expected checkout is loaded before debugging downstream
failures:

```bash
invenio-oauth2server/.venv/bin/python -c \
  'import flask_oauthlib; print(flask_oauthlib.__file__)'

invenio-oauthclient/.venv/bin/python -c \
  'import flask_oauthlib; print(flask_oauthlib.__file__)'
```

The path should point to the sibling migration checkout or the PR-based
installation, not an older released copy in `site-packages`.

## Running tests

The test scripts use `docker-services-cli`; Docker must be running. Activate
each repository's environment so its command-line tools are on `PATH`.

```bash
cd flask-oauthlib-invenio
source .venv/bin/activate
./run-tests.sh tests -q

deactivate
cd ../invenio-oauth2server
source .venv/bin/activate
./run-tests.sh

deactivate
cd ../invenio-oauthclient
source .venv/bin/activate
./run-tests.sh
```

PostgreSQL Alembic checks remain required:

```bash
cd invenio-oauth2server
source .venv/bin/activate
DB=postgresql ./run-tests.sh tests/test_alembic.py -q

cd ../invenio-oauthclient
source .venv/bin/activate
DB=postgresql ./run-tests.sh tests/test_alembic.py -q
```

## Validation status

A previously validated baseline, using the migrated compatibility checkout,
was:

```text
flask-oauthlib-invenio: 156 passed
invenio-oauthclient:    164 passed, 8 skipped
invenio-oauth2server:    59 passed, 1 skipped
```

The Flask compatibility suite was rerun after its concurrent Redis test was
fixed and still passed all 156 tests. The latest downstream dependency and
token-revocation commits require fresh full-suite and GitHub CI confirmation;
do not interpret the older baseline as final release sign-off.

Manual live-instance checks previously covered local login/logout and GitHub
and ORCID login. The remaining live and operational checks are listed in the
security handoff.

## Remaining work

Before release or merge completion:

1. Confirm all three GitHub PR workflows pass against PR #7.
2. Rerun complete downstream suites and PostgreSQL Alembic checks.
3. Add Python 3.10 to the `flask-oauthlib-invenio` CI matrix.
4. Reinstall all three packages in a live instance and restart web and worker
   processes.
5. Recheck GitHub/ORCID state, bearer-token negative cases, authorization-code
   replay, PKCE failures, redirect validation, refresh rotation, and strict
   legacy transport.
6. Investigate the previously observed themed 404 from live
   `POST /oauth/token`.
7. Test representative third-party custom `OAuthRemoteApp` subclasses and any
   deployed OAuth 1 integrations.
8. Decide final package versions and the support window for the retained
   `flask_oauthlib` compatibility namespace.
9. Replace temporary Git dependencies with released, bounded versions.

## How maintainers can help

The most useful review is behavior-focused rather than line-by-line style-only
review. In particular:

- compare endpoint responses and redirects with deployed clients;
- inspect state, nonce, PKCE, redirect URI, scope, revocation, and replay logic;
- provide representative custom provider subclasses or OAuth 1 integrations;
- run the PRs against real Redis and PostgreSQL services;
- test an upgrade with existing clients, bearer/refresh tokens, remote accounts,
  and remote tokens;
- flag any direct imports of OAuthlib internals that need an explicit migration
  path.

Please record new findings in `AUTHLIB_FOUND_ISSUES.md` and update the security
handoff when an issue is resolved or validation is completed.



 I’ve spent the last three days on an AI-assisted Flask-OAuthlib → Authlib migration; it works locally and the test suites pass.
 PRs: Flask #7, OAuth2 server #317, and OAuth client #394.
 It remains backward compatible with existing data, so no Alembic migration is expected; Python 3.9 must be upgraded because Authlib 1.8 requires 3.10+.
 This is not intended to replace your work, but hopefully it provides a useful tested starting point—please review and reuse anything helpful.