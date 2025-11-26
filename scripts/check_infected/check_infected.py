"""Check for infected packages by shelling out to ``pnpm list``."""
# make sure you setup the virtual environment first in .venv at the root of the repo
# uv run ./scripts/check_infected/check_infected.py

import json
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
LOCKFILE = REPO_ROOT / ".venv" / "var" / "instance" / "assets" / "pnpm-lock.yaml"
PNPM_WORKSPACE = LOCKFILE.parent
# INFECTED_FILE = SCRIPT_DIR / "npm_infected_versions.json"
INFECTED_FILE = SCRIPT_DIR / "shai-hulud-2-packages.json"


def load_infected() -> set[str]:
    """Load infected packages from JSON file into a set of `pkg@version` strings."""
    with INFECTED_FILE.open(encoding="utf-8") as f:
        raw = json.load(f)

    infected = set()
    for pkg, versions in raw.items():
        for version in versions.split(","):
            version = version.strip()
            if version:
                infected.add(f"{pkg}@{version}")
    return infected


def collect_installed() -> set[str]:
    """Return installed `pkg@version` pairs using ``pnpm list``."""

    if not PNPM_WORKSPACE.exists():
        raise RuntimeError(f"pnpm workspace not found: {PNPM_WORKSPACE}")

    cmd = [
        "pnpm",
        "list",
        "--recursive",
        "--depth",
        "Infinity",
        "--parseable",
        "--long",
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=PNPM_WORKSPACE,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("pnpm executable not found on PATH.") from exc
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip()
        message = f"pnpm list failed with exit code {exc.returncode}."
        if details:
            message = f"{message} {details}"
        raise RuntimeError(message) from exc

    installed: set[str] = set()
    for line in proc.stdout.splitlines():
        parts = line.strip().split(":", 2)
        if len(parts) < 2:
            continue

        spec = parts[1].strip()
        if not spec or spec.upper() == "PRIVATE":
            continue

        name_part, version_part = spec.rsplit("@", 1)
        version_part = version_part.strip()
        if not name_part or not version_part:
            continue

        skip_prefixes = ("workspace:", "link:", "file:")
        if version_part.startswith(skip_prefixes):
            continue

        installed.add(f"{name_part}@{version_part}")

    return installed


def main() -> None:
    if not LOCKFILE.exists():
        print(f"❌ Lockfile not found: {LOCKFILE}")
        return
    if not INFECTED_FILE.exists():
        print(f"❌ Infected list not found: {INFECTED_FILE}")
        return

    infected = load_infected()
    try:
        installed = collect_installed()
    except RuntimeError as err:
        print(f"❌ {err}")
        return
    found = sorted(installed & infected)

    if found:
        print("⚠️ Infected packages found:")
        for package in found:
            print(f"  - {package}")
    else:
        print("✅ No infected packages found in your lockfile.")


if __name__ == "__main__":
    main()