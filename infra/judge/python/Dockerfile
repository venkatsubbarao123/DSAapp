# Phase 5 Secure Sandbox: Python 3.12 Runner
FROM python:3.12-alpine

# Hardening: create unprivileged non-root user
RUN addgroup -g 10001 judge && \
    adduser -D -u 10001 -G judge judge

# Workspace setup
WORKDIR /workspace
RUN chown judge:judge /workspace && chmod 700 /workspace

# Switch to unprivileged user
USER judge:judge

# Default entrypoint
CMD ["python3", "solution.py"]
