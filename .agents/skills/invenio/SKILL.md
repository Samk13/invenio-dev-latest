---
name: invenio
description: Guidance for developing and reviewing InvenioRDM code while preserving its architecture.
---

# InvenioRDM development

## Tooling
- Use `uv` for Python dependencies and commands; use `pnpm` for JavaScript dependencies and scripts.
- Start the instance with `uv run invenio-cli run`.
- Run code in application context with `uv run invenio shell` or `uv run invenio shell python_file.py`.
- Format Python with `uv run ruff format`; follow each package's lint and test configuration.
- If startup fails, inspect `docker ps`; do not stop containers without confirming they belong to this instance.

## Architecture
- Consult `/Users/samaa2kth.se/Documents/CODE/INVENIO/docs-invenio-rdm/docs/maintenance/architecture/`, especially `software.md` and `runtime.md`; read domain-specific guides when relevant.
- Respect the strict flow: presentation → services → data access. Identify where each change belongs before implementing it.
- Presentation (REST resources, UI views, CLI, Celery tasks) parses/validates input, calls services, and serializes results; no business logic or permission checks here.
- Services own authorization, business validation, and control flow; keep them independent of HTTP/request context.
- Presentation exchanges identity-specific record projections with services; services use record entities to access data.
- Data access (`records/`) owns persistence, structural integrity, relations, and record lifecycle through record APIs, models, system fields, and dumpers.
- Service schemas handle business validation and field permissions; JSONSchemas define stored structure, not user-input requirements.
- Prefer declarative system fields and existing record APIs over inheritance, dictionary wrangling, and repeated type conversions.
- Keep one entity representation across database and search storage; dump/load round trips must preserve the record.
- The database is authoritative; search indexes are secondary and eventually consistent. Prefer search for queries and database primary-key lookups.
- Preserve optimistic concurrency checks and account for stale indexed data.
- Use Unit of Work for state-changing services; never directly commit/rollback sessions or index records inside service methods.
- Coordinate indexing and background tasks through UoW so they happen only after a successful database commit.
- Extend through service/resource configuration, components, Flask extensions, and entry points; reuse established extension mechanisms.
- Respect separate UI/API applications and application/request contexts; never assume module loading order within an assembly phase.

## Instance customization and frontend overrides
- Do not edit installed sources (`.venv/`, `site-packages/`, `node_modules/`) or generated output; such changes disappear on reinstall or rebuild. Generated links and outputs are fine.
- Keep customizations and test translations in this repository, using `assets/`, override registries, translations, and supported extension points. For upstream fixes, edit and link the package checkout through the supported workflow.
- Inspect the consumer and extension points first. Prefer props, wrappers, or component slots over copying upstream components and their logic.
- Translation resources do not inject React props. Verify the consumer forwards labels; if no injection point exists, explain the limitation and propose the smallest upstream forwarding change. Do not monkey-patch, call components as functions, or silently copy them.
- Verify assets compile from repository-owned sources and the intended linked package. Report browser verification separately; a successful build does not prove labels appear.
- Keep temporary overrides identifiable and reversible; preserve unrelated local changes.

## Tests
- Avoid `monkeypatch` whenever possible; prefer real fixtures, public service APIs, and configuration/dependency injection.
- Mock only unavoidable external boundaries; do not bypass authorization, validation, or transaction behavior to make tests pass.
- Add focused regression tests for changed behavior, including relevant permissions, invalid input, and failure paths.
- Run the affected package's tests and checks with `uv`/`pnpm`; report what ran and any blockers.

## Mandatory self-review
- Is the code we added really needed? Can we remove it while keeping the functionality working?
- What can we remove from the added code: duplicate logic, unnecessary abstractions, branches, fallbacks, or dependencies?
- Are we following Invenio architecture, or poking holes in its boundaries and invariants?
- Are we taking shortcuts or using hacks to achieve our goal? If so, replace them with the correct architectural solution.
- Prefer the smallest correct change that reuses existing capabilities; do not add speculative functionality.
- If the correct approach is unclear, inspect existing implementations and documentation, then ask rather than inventing a workaround.
- is the code readable, maintainable, and testable? Would a new developer understand it without asking questions?
