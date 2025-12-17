#!/usr/bin/env bash
# Show inverted dependency tree for a given Python package using `uv pip tree`.
# Usage: ./dep-tree.sh <package> [--depth N]
# Example: ./dep-tree.sh flask-mail --depth 3

set -euo pipefail

# --- Defaults ---
DEPTH=2

# --- Argument parsing ---
if [ $# -lt 1 ]; then
  echo "Usage: $0 <package> [--depth N]" >&2
  exit 1
fi

PACKAGE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --depth)
      DEPTH="${2:-2}"
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      PACKAGE="$1"
      shift
      ;;
  esac
done

if [ -z "$PACKAGE" ]; then
  echo "Error: Package name is required." >&2
  exit 1
fi

# --- Command execution ---
CMD=(uv pip tree --package="$PACKAGE" --invert --show-version-specifiers --depth "$DEPTH")

echo "🔍 Running: ${CMD[*]}"
echo
if ! command -v uv >/dev/null 2>&1; then
  echo "❌ Error: 'uv' command not found. Please install uv: https://github.com/astral-sh/uv" >&2
  exit 1
fi

"${CMD[@]}"
