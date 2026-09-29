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

EXPOSE 8000

ENV PYTHONPATH=/app
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
