# Celery spawn investigation handoff

## Current decision

First try pinning `billiard==4.2.4` on macOS. That version was in the earlier lockfile when the instance worked with these shell settings:

```sh
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY="YES"
export INVENIO_CELERY_WORKER_POOL="solo"
```

The trial package edits have been saved here as patches and removed from `.venv`. No instance configuration or dependency file was changed for this handoff. `uv.lock` was left untouched; the user will handle dependency installation. No dependency pin was applied.

## Cause and package versions

The current lockfile selects Billiard 4.3.0, Celery 5.4.0, Flask-CeleryExt 0.5.1, and Invenio-Celery 2.2.1. Billiard 4.3.0 defaults to `spawn` on macOS. Spawn serializes the embedded beat process and worker state; this exposed unpicklable Flask config values and later Celery beat and worker initialization failures. Linux keeps Billiard's `fork` default. Billiard 4.2.4 avoids the spawn path, but it may bring back the older macOS fork crash.

## Saved patches

- [flask-celeryext-0.5.1.patch](flask-celeryext-0.5.1.patch): On macOS, send only Celery settings from Flask config and use an importable task base. Linux behavior remains as shipped.
- [invenio-celery-2.2.1.patch](invenio-celery-2.2.1.patch): On macOS, correct embedded beat's pickle reconstruction, initialize spawned workers and Flask context, and preserve existing `CELERY_IMPORTS` entries. Linux behavior remains as shipped.

Each patch is a standard unified diff relative to its package root. To apply later, run `git apply --check /absolute/path/to/patch` and then `git apply /absolute/path/to/patch` from the matching package source checkout. Both patches were checked against the original release files from the local uv cache and reproduced the trial files exactly. The patch files are a trial, not a reviewed upstream submission.

## Observations from the trial

- With Billiard 4.3.0 and the package edits, embedded beat started and shut down without the pickle or scheduler error.
- A task ran in a macOS spawned prefork child with `app_context=True` using an in-memory broker. For that probe only, `INVENIO_CELERY_WORKER_POOL` was overridden to `prefork`.
- Full startup against RabbitMQ could not be confirmed in the sandbox because the broker connection was blocked.
- Celery and both edited integration package files were restored and matched the original release files in the local uv cache.

## Next steps

1. Try Billiard 4.2.4 on macOS and start the instance with the existing zsh settings. The user will handle the lockfile and installation.
2. If the earlier macOS crash returns, restore Billiard 4.3.0 and apply the saved patches to maintained package source checkouts for review.
