# Celery spawn patch for macOS

This patch captures the current `.venv` edits from this workspace.

Files:
- `artifacts/celery-spawn-macos-all-changes.patch`

## What it contains

This is the clean current patch set only:
- `flask_celeryext/app.py`
- `invenio_celery/ext.py`
- `celery/beat.py`
- `celery/concurrency/prefork.py`
- `celery/app/base.py`
- `celery/app/utils.py`

It does not include the earlier config-callable edits that were later reverted.

## Where to run it

Run the commands from the repository root, the directory that contains:
- `.venv/`
- `artifacts/`
- `pyproject.toml`

In this workspace that directory is:

```bash
/change/me/invenio-dev-latest
```

## Apply

```bash
cd /change/me/invenio-dev-latest
git apply --reject --whitespace=nowarn artifacts/celery-spawn-macos-all-changes.patch
```

If `git apply` is unavailable or refuses the patch, use:

```bash
cd /change/me/invenio-dev-latest
patch -p1 < artifacts/celery-spawn-macos-all-changes.patch
```

## Verify

```bash
cd /change/me/invenio-dev-latest
rg -n "flask_app_factory|setup_worker_optimizations|task_cls = 'flask_celeryext.app:AppContextTask'|def __reduce__" .venv/lib/python3.14/site-packages
```

## Notes

- This patch targets a Python 3.14 venv layout under `.venv/lib/python3.14/site-packages`.
- The patch is intended for a local virtualenv, not for the project source tree itself.
- If another machine uses a different Python minor version or venv path, the target paths may need adjustment.
