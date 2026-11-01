FROM ghcr.io/sparfenyuk/mcp-proxy:v0.13.2

# Install Node.js and npm so mcp-proxy can spawn npx-based MCP servers.
# Upgrade first: apk add leaves packages already in the base image at their
# old versions, so a fixed library (e.g. brotli-libs for CVE-2026-111497)
# would otherwise wait for an upstream mcp-proxy release.
RUN apk upgrade --no-cache && apk add --no-cache nodejs npm
