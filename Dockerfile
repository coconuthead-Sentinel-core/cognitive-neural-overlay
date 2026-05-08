# syntax=docker/dockerfile:1.6

# ---------- Stage 1: build the frontend bundle ----------
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend

# Cache npm install: copy lockfile + manifest first
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
# Vite outputs to ../cno/static via vite.config.ts
RUN mkdir -p /app/cno/static && npm run build


# ---------- Stage 2: python runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CNO_DB_PATH=/data/cno_audit.db \
    CNO_AMC_JSONL_PATH=/data/cno_anchors.jsonl \
    PORT=8000 \
    UVICORN_WORKERS=1

WORKDIR /app

# System deps: curl for HEALTHCHECK; build-essential is NOT needed for our wheels.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps first (better cache layer)
COPY requirements.txt ./
RUN pip install -r requirements.txt

# App code
COPY cno/ ./cno/
COPY pyproject.toml ./

# Built frontend bundle from stage 1
COPY --from=frontend-build /app/cno/static/ ./cno/static/

# Runtime data dir (audit DB + jsonl sink) — mount a volume here in prod
RUN mkdir -p /data && \
    addgroup --system cno && adduser --system --ingroup cno cno && \
    chown -R cno:cno /app /data
USER cno

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/healthz" || exit 1

# Production: gunicorn-style worker pool with uvicorn workers.
# Override UVICORN_WORKERS via env. Single-worker also fine for low traffic.
CMD ["sh", "-c", "exec uvicorn cno.app:app --host 0.0.0.0 --port ${PORT} --workers ${UVICORN_WORKERS}"]
