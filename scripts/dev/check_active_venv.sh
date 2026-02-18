#!/usr/bin/env bash

# Shows: VIRTUAL_ENV (claimed) vs python sys.prefix/executable (actual)

ve="${VIRTUAL_ENV:- ✅ <none> }"
py=""
py="$(command -v python 2>/dev/null || command -v python3 2>/dev/null || true)"

echo "claimed VIRTUAL_ENV: $ve"

if [[ -z "$py" ]]; then
echo "actual python: <not found>"
exit 1
fi

echo "python in PATH:      $py"

"$py" - <<'PY'
import os, sys
print("sys.executable:     ", sys.executable)
print("sys.prefix:         ", sys.prefix)
print("sys.base_prefix:    ", getattr(sys, "base_prefix", "<n/a>"))
ve = os.environ.get("VIRTUAL_ENV")
if ve:
    ok = (os.path.realpath(sys.prefix) == os.path.realpath(ve))
    print("matches VIRTUAL_ENV:", ok)
else:
    print("matches VIRTUAL_ENV: <no VIRTUAL_ENV set>")
PY
