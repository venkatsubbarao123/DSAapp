# Phase 5 Secure Sandbox: JavaScript / Node.js Runner
FROM node:current-alpine

# Hardening: remove unnecessary package managers (npm, yarn, corepack) to eliminate CVE attack surface
RUN rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /opt/yarn*

# Hardening: create unprivileged non-root user
RUN addgroup -g 10001 judge && \
    adduser -D -u 10001 -G judge judge

# Workspace setup
WORKDIR /workspace
RUN chown judge:judge /workspace && chmod 700 /workspace

# Switch to unprivileged user
USER judge:judge

# Default entrypoint
CMD ["node", "solution.js"]
