# Phase 5 Secure Sandbox: TypeScript / Node.js Runner
FROM node:current-alpine

# Install TypeScript compiler globally and strip package managers/cache to eliminate CVE attack surface
RUN npm config set strict-ssl false && \
    npm install -g typescript@5.7.3 && \
    rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack /opt/yarn* /root/.npm /root/.cache

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
