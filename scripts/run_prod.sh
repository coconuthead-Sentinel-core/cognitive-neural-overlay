#!/usr/bin/env bash
# Production runner for non-Docker hosts (VM / bare metal).
# Assumes Python 3.10+ is on PATH and dependencies are installed:
#   pip install -r requirements.txt
#
# Reads .env if present.

set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . .env
    set +a
fi

PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-1}"

# If the frontend bundle isn't built yet, build it (requires Node 18+).
if [ ! -f cno/static/index.html ] && [ -d frontend ] && command -v npm >/dev/null 2>&1; then
    echo "[run_prod] frontend bundle missing — building"
    (cd frontend && npm ci --no-audit --no-fund && npm run build)
fi

exec uvicorn cno.app:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips '*'
