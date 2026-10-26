FROM ghcr.io/actions/actions-runner:2.338.1

# ---- Versions / paths ----
ARG CODEQL_VERSION=2.25.2
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
      python3-pip python3-venv pipx sshpass jq rsync openssh-client curl unzip wget gpg xxd ca-certificates gnupg lsb-release postgresql-client \
      restic dnsutils iputils-ping && \
    # AWS CLI v2
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip" && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    # yq v4.53.2
    wget -q -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.53.2/yq_linux_amd64 && \
    echo "d56bf5c6819e8e696340c312bd70f849dc1678a7cda9c2ad63eebd906371d56b  /usr/bin/yq" | sha256sum -c - && \
    chmod +x /usr/bin/yq && \
    # Backblaze B2 CLI v4.6.0
    curl -fsSL -L https://github.com/Backblaze/B2_Command_Line_Tool/releases/download/v4.6.0/b2-linux -o /usr/local/bin/b2 && \
    echo "4ac55ebe37a50eba9d19f24809da584539e1395992b8aa43f906cc83180bffa1  /usr/local/bin/b2" | sha256sum -c - && \
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

# ---------- Pinned tools jobs would otherwise download every run ----------
# Renovate bumps these through the `# renovate:` comments (custom regex manager
# in renovate.json). Workflows that run on this image use the tools as-is
# instead of installing their own.
# renovate: datasource=node-version depName=node
ARG NODE_VERSION=24.22.1
# renovate: datasource=github-releases depName=hashicorp/terraform extractVersion=^v(?<version>.+)$
ARG TERRAFORM_VERSION=1.17.0
# renovate: datasource=github-releases depName=hashicorp/vault extractVersion=^v(?<version>.+)$
ARG VAULT_VERSION=2.1.0
# renovate: datasource=github-releases depName=kubernetes/kubernetes extractVersion=^v(?<version>.+)$
ARG KUBECTL_VERSION=1.37.1

# Node in the toolcache layout, so actions/setup-node finds it without
# downloading (node-version: 24), and on PATH for jobs that skip setup-node.
RUN set -eux; \
    dir="${RUNNER_TOOL_CACHE}/node/${NODE_VERSION}/x64"; \
    mkdir -p "$dir"; \
    cd /tmp; \
    curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.gz"; \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" | grep " node-v${NODE_VERSION}-linux-x64.tar.gz\$" | sha256sum -c -; \
    tar -xzf "node-v${NODE_VERSION}-linux-x64.tar.gz" -C "$dir" --strip-components=1; \
    touch "${RUNNER_TOOL_CACHE}/node/${NODE_VERSION}/x64.complete"; \
    ln -sf "$dir/bin/node" "$dir/bin/npm" "$dir/bin/npx" /usr/local/bin/; \
    chown -R runner:runner "${RUNNER_TOOL_CACHE}"; \
    rm -f /tmp/node-v*.tar.gz; \
    node --version

# Terraform, Vault (zips checked against HashiCorp's SHA256SUMS) and kubectl.
RUN set -eux; \
    cd /tmp; \
    for tool in "terraform:${TERRAFORM_VERSION}" "vault:${VAULT_VERSION}"; do \
      name="${tool%%:*}"; ver="${tool#*:}"; zip="${name}_${ver}_linux_amd64.zip"; \
      curl -fsSLO "https://releases.hashicorp.com/${name}/${ver}/${zip}"; \
      curl -fsSL "https://releases.hashicorp.com/${name}/${ver}/${name}_${ver}_SHA256SUMS" | grep " ${zip}\$" | sha256sum -c -; \
      unzip -q -o "$zip" "$name" -d /usr/local/bin; \
      rm -f "$zip"; \
    done; \
    curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl"; \
    echo "$(curl -fsSL "https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256")  /usr/local/bin/kubectl" | sha256sum -c -; \
    chmod +x /usr/local/bin/kubectl; \
    terraform version; vault version; kubectl version --client

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
# pipx puts its apps here. Job steps don't read ~/.bashrc, so it goes on PATH
# directly instead of through `pipx ensurepath`.
ENV PATH=/home/runner/.local/bin:${PATH}
# Full Ansible (ansible-core plus collections), for playbooks that would
# otherwise `pipx run --spec ansible` (which fetches it on every run).
# renovate: datasource=pypi depName=ansible
ARG ANSIBLE_VERSION=14.5.0
# renovate: datasource=pypi depName=linode-cli
ARG LINODE_CLI_VERSION=5.66.0
RUN codeql --version && \
    pipx install --include-deps "ansible==${ANSIBLE_VERSION}" && \
    pipx install "linode-cli==${LINODE_CLI_VERSION}" && \
    ansible-playbook --version && \
    rm -rf /home/runner/.cache

# Renovate and wrangler in npx's cache, under the same package specs the
# workflows pass to npx (`npx --yes -p renovate@X ...`), so they run without
# downloading and unpacking Renovate (it took ~6 min on a throttled runner).
# Keep in step with the workflows' RENOVATE_VERSION / WRANGLER_VERSION pins;
# Renovate bumps both.
# renovate: datasource=npm depName=renovate
ARG RENOVATE_VERSION=44.181.7
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.152.0
RUN set -eux; \
    npx --yes -p "renovate@${RENOVATE_VERSION}" -c 'renovate --version'; \
    npx --yes "wrangler@${WRANGLER_VERSION}" --version; \
    rm -rf /home/runner/.npm/_logs
