# Phase 5 Secure Sandbox: Java 17 Runner
FROM eclipse-temurin:17-alpine

# Hardening: create unprivileged non-root user
RUN addgroup -g 10001 judge && \
    adduser -D -u 10001 -G judge judge

# Workspace setup
WORKDIR /workspace
RUN chown judge:judge /workspace && chmod 700 /workspace

# Switch to unprivileged user
USER judge:judge

# Default entrypoint
CMD ["java", "-Xmx256m", "-XX:+UseSerialGC", "Solution"]
