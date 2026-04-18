#!/bin/sh
# Per-service start dispatch. Railway sets RAILWAY_SERVICE_NAME at runtime.
# One image, two entry points — so both rescue-web and rescue-agent can share
# the same railway.json startCommand without needing per-service dashboard config.
set -e
case "$RAILWAY_SERVICE_NAME" in
  rescue-agent)
    exec uv run python app/voice/agent.py start
    ;;
  *)
    exec uv run uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
    ;;
esac
