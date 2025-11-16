#!/usr/bin/env python3

"""
PyPI Package Freshness Checker
===============================

Check the "freshness" of your Python packages - like checking if fruit is too old!
This script compares your installed package versions against PyPI to show both their
ages and highlight packages with recent updates available.

Features:
---------
- Color-coded output based on package age (like a freshness indicator)
- Shows both current and latest version ages
- Configurable sorting (by current or latest version age)
- Parallel API requests for fast execution
- Works with uv-managed and pip-managed virtual environments

Usage:
------
# Basic usage (uses active venv from $VIRTUAL_ENV):
uv run ./pypi_freshness_check.py

# Specify a different virtual environment:
./pypi_freshness_check.py --venv /path/to/.venv

# Sort by latest version age to see recent PyPI releases:
uv run ./pypi_freshness_check.py --sort-by latest

# Adjust number of parallel workers:
uv run ./pypi_freshness_check.py --workers 16

Color Coding:
-------------
The output is color-coded based on the age matching your sort option:
- When sorting by current (default): Colors show current version age
- When sorting by latest: Colors show latest version age

Color meanings:
- RED:    Released today (0 days ago)
- ORANGE: Released yesterday (1 day ago)
- YELLOW: Released 2-3 days ago
- BLUE:   Released 4-7 days ago
- NORMAL: Released 8+ days ago

Columns:
--------
- Package:      Package name
- Current:      Your currently installed version
- Current Age:  How long ago your installed version was released
- Latest:       Latest available version on PyPI
- Latest Age:   How long ago the latest version was released

Sorting Options:
----------------
--sort-by current (default): Sorts by current version age (shows your newest installed packages first)
--sort-by latest:           Sorts by latest version age (shows packages with newest releases first)

Examples:
---------
# Find packages with recent updates available:
uv run ./check_pypi_release_date.py

# Find which of your installed packages are oldest:
uv run ./check_pypi_release_date.py --sort-by current

# Check another environment:
./check_pypi_release_date.py --venv ~/.virtualenvs/myproject/.venv
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# ANSI colors
RED = "\033[31m"
ORANGE = "\033[38;5;208m" 
YELLOW = "\033[33m"
BLUE = "\033[94m"
GRAY = "\033[90m"
RESET = "\033[0m"

def run(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def freeze_cmd(venv: str | None) -> str:
    """Prefer uv pip; fall back to pip from chosen environment."""
    # If uv is available, use it directly (works with uv-managed venvs)
    if shutil.which("uv"):
        return "uv pip freeze"
    # Fall back to regular pip
    if venv:
        py = os.path.join(venv, "bin", "python")
        return f'"{py}" -m pip freeze'
    return f'"{sys.executable}" -m pip freeze'

def parse_freeze(text: str):
    pkgs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("-e ") or "@" in line:
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            if name and version:
                pkgs.append((name, version))
    return pkgs

def iso_to_epoch(s: str | None) -> float | None:
    if not s:
        return None
    try:
        # prefer the part before '.' to avoid subsecond parsing quirks
        s = s.replace("Z", "+00:00")
        if "." in s and "+" in s:
            # keep timezone, strip subseconds
            left, right = s.split("+", 1)
            s = left.split(".", 1)[0] + "+" + right
        elif "." in s:
            s = s.split(".", 1)[0]
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None

def fetch_latest(name: str, current_version: str):
    """Return (latest_version, latest_upload_iso, latest_days, current_upload_iso, current_days) or (None, None, None, None, None) on failure."""
    # Try exact name first, then PEP 503 normalized
    candidates = [name, name.replace("_", "-").lower()]
    for n in candidates:
        # Strip control chars to avoid jq-like failures
        proc = run(f'curl -sSfL https://pypi.org/pypi/{n}/json | tr -d "\\000-\\037"')
        if proc.returncode != 0 or not proc.stdout:
            continue
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            continue
        latest = (data.get("info") or {}).get("version")
        if not latest:
            continue
        
        releases = data.get("releases") or {}
        
        # Get latest version info
        latest_files = releases.get(latest, [])
        latest_ts = None
        latest_picked = None
        for f in latest_files:
            u = f.get("upload_time_iso_8601") or f.get("upload_time")
            e = iso_to_epoch(u)
            if e is not None and (latest_ts is None or e > latest_ts):
                latest_ts = e
                latest_picked = u
        
        latest_days = None
        if latest_picked and latest_ts:
            now = datetime.now(timezone.utc).timestamp()
            latest_days = int((now - latest_ts) // 86400)
        
        # Get current version info
        current_files = releases.get(current_version, [])
        current_ts = None
        current_picked = None
        for f in current_files:
            u = f.get("upload_time_iso_8601") or f.get("upload_time")
            e = iso_to_epoch(u)
            if e is not None and (current_ts is None or e > current_ts):
                current_ts = e
                current_picked = u
        
        current_days = None
        if current_picked and current_ts:
            now = datetime.now(timezone.utc).timestamp()
            current_days = int((now - current_ts) // 86400)
        
        return latest, latest_picked, latest_days, current_picked, current_days
    
    return None, None, None, None, None

def color_for_days(days: int | None) -> str:
    if days is None:
        return RESET
    if days == 0:
        return RED
    if days == 1:
        return ORANGE
    if 2 <= days <= 3:
        return YELLOW
    if 4 <= days <= 7:
        return BLUE
    return RESET

def group_rank(days: int | None) -> int:
    if days is None:
        return 5
    if days == 0:
        return 0
    if days == 1:
        return 1
    if 2 <= days <= 3:
        return 2
    if 4 <= days <= 7:
        return 3
    return 4  # 8+ days

def main():
    parser = argparse.ArgumentParser(description="Show latest PyPI releases by recency (color-coded).")
    parser.add_argument("--venv", help="Path to a virtualenv to inspect (defaults to the active venv).")
    parser.add_argument("--workers", type=int, default=min(32, (os.cpu_count() or 8) * 4),
                        help="Parallel requests (default: CPU*4, max 32).")
    parser.add_argument("--sort-by", choices=["current", "latest"], default="current",
                        help="Sort by 'current' version age or 'latest' version age (default: current).")
    args = parser.parse_args()

    active_venv = args.venv or os.environ.get("VIRTUAL_ENV")
    env_label = active_venv or os.path.dirname(sys.executable)

    print(f"{GRAY}Using Python {'.'.join(map(str, sys.version_info[:3]))}  environment at: {env_label}")
    print()
    print("this is unsorted output - see final summary below")
    print(f"{RESET}")

    # Get freeze list
    proc = run(freeze_cmd(active_venv))
    if proc.returncode != 0:
        print(proc.stderr or "Failed to run pip freeze", file=sys.stderr)
        sys.exit(1)
    pkgs = parse_freeze(proc.stdout)
    if not pkgs:
        print("No packages found.")
        sys.exit(0)

    # Column widths (fixed once so live output aligns)
    name_w = max( len("Package"), max(len(n) for n,_ in pkgs) ) + 2
    cur_w  = max( len("Current"), max(len(v) for _,v in pkgs) ) + 2
    latest_w = max( len("Latest"), cur_w ) + 2
    cur_age_w = 18  # "released XXX days"
    latest_age_w = 18  # "released XXX days"

    header = f"{'Package':<{name_w}} {'Current':<{cur_w}} {'Current Age':<{cur_age_w}} {'Latest':<{latest_w}} {'Latest Age':<{latest_age_w}}"
    rule = "-" * (name_w + cur_w + cur_age_w + latest_w + latest_age_w + 4)
    print(f"{GRAY}{header}")
    print(rule)
    print(f"{RESET}")

    results = []

    def work(item):
        name, cur = item
        latest, latest_upload, latest_days, current_upload, current_days = fetch_latest(name, cur)
        return (name, cur, latest, latest_upload, latest_days, current_upload, current_days)

    # Parallel fetch & live print
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(work, it): it for it in pkgs}
        for fut in as_completed(futures):
            name, cur, latest, latest_upload, latest_days, current_upload, current_days = fut.result()
            results.append((name, cur, latest, latest_upload, latest_days, current_upload, current_days))
            # Gray output for unsorted live results
            cur_when = f"{current_days} days ago" if current_days is not None else "N/A"
            latest_when = f"{latest_days} days ago" if latest_days is not None else "N/A"
            latest_disp = latest or "N/A"
            print(f"{GRAY}{name:<{name_w}} {cur:<{cur_w}} {cur_when:<{cur_age_w}} {latest_disp:<{latest_w}} {latest_when:<{latest_age_w}}{RESET}")
            sys.stdout.flush()

    # Final sorted summary
    print("\n" + "=" * (len(rule)))
    if args.sort_by == "current":
        print("Sorted by CURRENT version age (newest first):")
        print("use --sort-by latest to see packages with newest releases first")
        print("Color indicates CURRENT version age - Red: today | Orange: 1 day | Yellow: 2-3 days | Blue: 4-7 days | Normal: 8+ days\n")
        sort_index = 6  # current_days
    else:
        print("Sorted by LATEST version age (newest first):")
        print("use --sort-by current or remove the --sort-by option to see packages with newest installed versions first")
        print("Color indicates LATEST version age - Red: today | Orange: 1 day | Yellow: 2-3 days | Blue: 4-7 days | Normal: 8+ days\n")
        sort_index = 4  # latest_days
    
    print(header)
    print(rule)

    for name, cur, latest, latest_upload, latest_days, current_upload, current_days in sorted(
        results,
        key=lambda r: (group_rank(r[sort_index]), r[sort_index] if r[sort_index] is not None else 10**9, r[0].lower())
    ):
        color_days = current_days if args.sort_by == "current" else latest_days
        color = color_for_days(color_days)
        cur_when = f"{current_days} days ago" if current_days is not None else "N/A"
        latest_when = f"{latest_days} days ago" if latest_days is not None else "N/A"
        latest_disp = latest or "N/A"
        print(f"{color}{name:<{name_w}} {cur:<{cur_w}} {cur_when:<{cur_age_w}} {latest_disp:<{latest_w}} {latest_when:<{latest_age_w}}{RESET}")

if __name__ == "__main__":
    main()
