FROM ghcr.io/actions/actions-runner:2.330.0

# ---- Versions / paths ----
ARG CODEQL_VERSION=2.23.3
ENV CODEQL_VERSION=${CODEQL_VERSION}

# Toolcache root used by @actions/tool-cache on self-hosted runners
ENV RUNNER_TOOL_CACHE=/opt/hostedtoolcache

# Predeclare where we'll unpack CodeQL (standard layout)
ENV CODEQL_TOOLCACHE_DIR=${RUNNER_TOOL_CACHE}/CodeQL/${CODEQL_VERSION}/x64
ENV CODEQL_DIST=${CODEQL_TOOLCACHE_DIR}/codeql
ENV PATH=${CODEQL_DIST}:${PATH}

# Some Copilot/agents flows demand a GitHub host string. Keep the job step that writes
# to $GITHUB_ENV, but this ENV helps in most paths.
ENV GITHUB_HOST=github.com

USER root

# Base tooling
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      python3-pip python3-venv pipx sshpass jq rsync openssh-client curl unzip wget gpg xxd ca-certificates gnupg lsb-release && \
    # AWS CLI v2
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    # yq
    wget -q -O /usr/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && \
    chmod +x /usr/bin/yq && \
    # Backblaze B2 CLI
    curl -fsSL -L https://github.com/Backblaze/B2_Command_Line_Tool/releases/latest/download/b2-linux -o /usr/local/bin/b2 && \
    chmod +x /usr/local/bin/b2 && \
    # Docker repo for compose plugin
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
      > /etc/apt/sources.list.d/docker.list && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends docker-compose-plugin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache /tmp/awscliv2.zip /tmp/aws

# ---------- Preinstall CodeQL (toolcache layout) ----------
# This matches the layout used on GitHub-hosted runners:
#   /opt/hostedtoolcache/CodeQL/<version>/x64/{codeql/*}
# Plus marker files: pinned-version and x64.complete
RUN set -eux; \
    mkdir -p "${CODEQL_TOOLCACHE_DIR}"; \
    tmp_tgz="$(mktemp -u)/codeql-bundle-linux64.tar.gz"; \
    mkdir -p "$(dirname "$tmp_tgz")"; \
    echo "Downloading CodeQL bundle v${CODEQL_VERSION} ..."; \
    curl -fsSL "https://github.com/github/codeql-action/releases/download/codeql-bundle-v${CODEQL_VERSION}/codeql-bundle-linux64.tar.gz" -o "${tmp_tgz}"; \
    echo "Unpacking CodeQL to ${CODEQL_TOOLCACHE_DIR} ..."; \
    tar -xzf "${tmp_tgz}" -C "${CODEQL_TOOLCACHE_DIR}"; \
    # Marker files recognized by setup actions
    touch "${CODEQL_TOOLCACHE_DIR}/pinned-version"; \
    touch "${RUNNER_TOOL_CACHE}/CodeQL/${CODEQL_VERSION}/x64.complete"; \
    # Make sure runner user can read the cache and write temp bits alongside it
    chown -R runner:runner "${RUNNER_TOOL_CACHE}"; \
    chmod -R a+rX "${RUNNER_TOOL_CACHE}"; \
    # Convenience shim (optional, PATH is already set)
    ln -sf "${CODEQL_DIST}/codeql" /usr/local/bin/codeql; \
    rm -f "${tmp_tgz}"; \
    # Quick sanity check (as root)
    codeql --version

# Switch to runner and validate again to ensure PATH/permissions are good for non-root
USER runner
RUN codeql --version && \
    pipx ensurepath && \
    pipx install ansible && \
    pipx install linode-cli && \
    rm -rf /home/runner/.cache
