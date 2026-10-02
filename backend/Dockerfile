# Production Multi-Stage Dockerfile for FastAPI Backend
FROM python:3.13-slim AS builder

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.13-slim AS runner

WORKDIR /app
# Run as non-root unprivileged service account
RUN useradd -m -u 10001 dsaapp

COPY --from=builder /install /usr/local
COPY . /app/backend

USER dsaapp

# Render/PaaS platforms inject the port to listen on via $PORT and route traffic
# to it. Hardcoding 8000 means the platform probes a port nothing is bound to,
# which shows up as a health-check timeout.
EXPOSE 8000

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Container health probe against the root health endpoint. /health verifies the
# database connection and returns 503 when degraded, so an unhealthy container
# is one that must not receive traffic. It probes $PORT, never a fixed port.
# The timeout is generous because /health performs a real database round-trip
# (a cold connection to a managed Postgres can take several seconds), and a
# probe that flaps on latency would be worse than no probe at all.
HEALTHCHECK --interval=30s --timeout=15s --start-period=45s --retries=3 \
  CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{p}/health', timeout=10).status==200 else 1)"

# Production startup:
#   --host 0.0.0.0            required so the platform can reach the container
#   --port ${PORT:-8000}      honours the platform-injected port
#   --workers ${WEB_CONCURRENCY:-1}
#         A single worker by default. Every worker runs the FastAPI lifespan,
#         so extra workers would each start their own judge worker loop and
#         duplicate startup work against the database.
# Shell form is required so ${PORT} is expanded at runtime; the previous JSON
# exec form could not expand it and therefore always bound port 8000.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1}"]
