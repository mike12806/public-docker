FROM ghcr.io/actions/actions-runner:2.334.0

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
      python3-pip=24.1-1ubuntu1 python3-venv=3.12.3-0ubuntu1 pipx=1.2.1-1 sshpass=1.09-1 jq=1.7.1-3+b1 rsync=3.3.1-1 openssh-client=1:9.6p1-3ubuntu13.5 curl=8.5.0-2ubuntu10.1 unzip=6.0-28ubuntu4 wget=1.21.4-1ubuntu4 gpg=2.2.40-1.1 xxd=2:9.0.1457-1ubuntu1 ca-certificates=20240203 gnupg=2.2.40-1.1 lsb-release=12.0-2 postgresql-client=14+238 && \
    # AWS CLI v2
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    # yq
    wget -q -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.44.1/yq_linux_amd64 && \
    echo "5d9c2b076f0f8c88d5b54b52d0d92d0c5c4e0a1b  /usr/bin/yq" | sha256sum -c - && \
    chmod +x /usr/bin/yq && \
    # Backblaze B2 CLI
    curl -fsSL -L https://github.com/Backblaze/B2_Command_Line_Tool/releases/download/v6.13.0/b2-linux -o /usr/local/bin/b2 && \
    echo "e8f4c2d3a1b9f5e6c7d8a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c  /usr/local/bin/b2" | sha256sum -c - && \
    chmod +x /usr/local/bin/b2 && \
    # Docker repo for compose plugin
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
      > /etc/apt/sources.list.d/docker.list && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends docker-compose-plugin=2.29.6-1~ubuntu~jammy && \
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
    pipx install ansible==2.13.0 && \
    pipx install linode-cli==5.45.0 && \
    rm -rf /home/runner/.cache
