# Phase 5 Secure Sandbox: TypeScript / Node.js 20 Runner
FROM node:20-alpine

# Install TypeScript compiler globally (bypass corporate/local SSL intercept during image build)
RUN npm config set strict-ssl false && npm install -g typescript

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
