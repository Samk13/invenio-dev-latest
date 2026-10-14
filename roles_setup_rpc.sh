#!/usr/bin/env bash
#
# SPDX-FileCopyrightText: 2026 KTH Royal Institute of Technology.
# SPDX-License-Identifier: MIT

export DYLD_LIBRARY_PATH="/opt/homebrew/lib${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
# Quit on errors
set -uo errexit

# Quit on unbound symbols
set -o nounset

# Start the server in the instance directory before running this script:
# invenio rpc-server start --socket socket.file
RPC_SOCKET="${RPC_SOCKET:-socket.file}"
if [[ ! -S "$RPC_SOCKET" ]]; then
    echo "RPC socket not found: $RPC_SOCKET" >&2
    echo "Start the server in another terminal, then rerun this script:" >&2
    echo "invenio rpc-server start --socket $RPC_SOCKET" >&2
    exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
RPC_SERVER="$(command -v rpc-server || true)"
if [[ -z "$RPC_SERVER" ]]; then
    RPC_SERVER="$SCRIPT_DIR/.venv/bin/rpc-server"
fi
if [[ ! -x "$RPC_SERVER" ]]; then
    echo "rpc-server not found on PATH or in $SCRIPT_DIR/.venv/bin" >&2
    exit 1
fi

echo "Creating Community administration-moderation role ..."
"$RPC_SERVER" send --socket "$RPC_SOCKET" roles create administration-moderation

echo "Creating Community administration role ..."
"$RPC_SERVER" send --socket "$RPC_SOCKET" roles create administration

echo "Allow Access ..."

echo "Allow administration-moderation to role administration-moderation ..."
"$RPC_SERVER" send --socket "$RPC_SOCKET" access allow administration-moderation role administration-moderation

echo "Allow administration-access to role administration ..."
"$RPC_SERVER" send --socket "$RPC_SOCKET" access allow administration-access role administration

# echo "Allow superuser-access to role administration ..."
# "$RPC_SERVER" send --socket "$RPC_SOCKET" access allow superuser-access role administration

echo "add test@test.com as administrator"

"$RPC_SERVER" send --socket "$RPC_SOCKET" roles add test@test.com administration
"$RPC_SERVER" send --socket "$RPC_SOCKET" roles add test@test.com administration-moderation

echo "done!"
