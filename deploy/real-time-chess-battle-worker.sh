
#!/usr/bin/env bash
# Worker entrypoint for Real-time-chess-battle.
# Derives the port from RTCB_SERVER_ID (preferred) or KFCHESS_SERVER_ID (legacy).
set -euo pipefail

SERVER_ID="${RTCB_SERVER_ID:-${KFCHESS_SERVER_ID:-}}"
if [[ -z "${SERVER_ID}" ]]; then
    echo "ERROR: RTCB_SERVER_ID/KFCHESS_SERVER_ID is not set" >&2
    exit 1
fi

NUM="${SERVER_ID//[!0-9]/}"
if [[ -z "$NUM" ]]; then
    echo "ERROR: Cannot extract worker number from SERVER_ID=$SERVER_ID" >&2
    exit 1
fi

PORT=$((8000 + NUM))
exec uv run uvicorn kfchess.main:app --host 127.0.0.1 --port "$PORT" --workers 1 --log-level info
