# Phase 5 Secure Sandbox: C++20 (GCC 13) Runner
FROM alpine:3.19

# Install C++ toolchain
RUN apk add --no-cache g++ make

# Hardening: create unprivileged non-root user
RUN addgroup -g 10001 judge && \
    adduser -D -u 10001 -G judge judge

# Workspace setup
WORKDIR /workspace
RUN chown judge:judge /workspace && chmod 700 /workspace

# Switch to unprivileged user
USER judge:judge

# Default entrypoint
CMD ["./solution"]
