# The runner and Docker client come from the official image; everything else
# sits on Ubuntu 26.04, so jobs that asked GitHub for ubuntu-26.04 get the same
# OS here. Renovate bumps both FROM lines.
FROM ghcr.io/actions/actions-runner:2.338.1 AS runner

FROM ubuntu:26.04

# ---- Versions / paths ----
ARG CODEQL_VERSION=2.25.2
ENV CODEQL_VERSION=${CODEQL_VERSION}

ENV DEBIAN_FRONTEND=noninteractive
# Same runner settings as the official image (ARC relies on them).
ENV RUNNER_MANUALLY_TRAP_SIG=1
ENV ACTIONS_RUNNER_PRINT_LOG_TO_STDOUT=1
ENV ImageOS=ubuntu26

# Toolcache root used by @actions/tool-cache on self-hosted runners
ENV RUNNER_TOOL_CACHE=/opt/hostedtoolcache

# Predeclare where we'll unpack CodeQL (standard layout)
ENV CODEQL_TOOLCACHE_DIR=${RUNNER_TOOL_CACHE}/CodeQL/${CODEQL_VERSION}/x64
ENV CODEQL_DIST=${CODEQL_TOOLCACHE_DIR}/codeql
ENV PATH=${CODEQL_DIST}:${PATH}

# Some Copilot/agents flows demand a GitHub host string. Keep the job step that writes
# to $GITHUB_ENV, but this ENV helps in most paths.
ENV GITHUB_HOST=github.com

# renovate: datasource=github-releases depName=docker/compose extractVersion=^v(?<version>.+)$
ARG COMPOSE_VERSION=5.6.1
# renovate: datasource=github-releases depName=cli/cli extractVersion=^v(?<version>.+)$
ARG GH_VERSION=2.103.2

# Base tooling, plus the libraries the runner's bundled .NET needs (the
# official image gets those from dotnet/runtime-deps).
RUN set -eux; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends \
      sudo lsb-release gpg-agent software-properties-common git \
      ca-certificates libc6 libgcc-s1 libstdc++6 libssl3t64 libkrb5-3 zlib1g tzdata \
      "$(apt-cache search --names-only '^libicu[0-9]+$' | sort -V | tail -1 | cut -d' ' -f1)" \
      python3 python3-pip python3-venv pipx sshpass jq rsync openssh-client curl unzip zip wget gpg xxd gnupg \
      postgresql-client restic dnsutils iputils-ping file make; \
    # AWS CLI v2
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip; \
    unzip -q /tmp/awscliv2.zip -d /tmp; \
    /tmp/aws/install; \
    # yq v4.53.2
    wget -q -O /usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.53.2/yq_linux_amd64; \
    echo "d56bf5c6819e8e696340c312bd70f849dc1678a7cda9c2ad63eebd906371d56b  /usr/bin/yq" | sha256sum -c -; \
    chmod +x /usr/bin/yq; \
    # Backblaze B2 CLI v4.6.0
    curl -fsSL -L https://github.com/Backblaze/B2_Command_Line_Tool/releases/download/v4.6.0/b2-linux -o /usr/local/bin/b2; \
    echo "4ac55ebe37a50eba9d19f24809da584539e1395992b8aa43f906cc83180bffa1  /usr/local/bin/b2" | sha256sum -c -; \
    chmod +x /usr/local/bin/b2; \
    # Docker Compose plugin (Docker's apt repo has no 26.04 suite yet)
    mkdir -p /usr/local/lib/docker/cli-plugins; \
    curl -fsSLo /usr/local/lib/docker/cli-plugins/docker-compose "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-x86_64"; \
    echo "$(curl -fsSL "https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-x86_64.sha256" | cut -d' ' -f1)  /usr/local/lib/docker/cli-plugins/docker-compose" | sha256sum -c -; \
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose; \
    # GitHub CLI
    curl -fsSLo /tmp/gh.tgz "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_amd64.tar.gz"; \
    curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_checksums.txt" | grep " gh_${GH_VERSION}_linux_amd64.tar.gz\$" | sed "s#gh_${GH_VERSION}_linux_amd64.tar.gz#/tmp/gh.tgz#" | sha256sum -c -; \
    tar -xzf /tmp/gh.tgz -C /tmp; \
    install -m 755 "/tmp/gh_${GH_VERSION}_linux_amd64/bin/gh" /usr/local/bin/gh; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /root/.cache /tmp/awscliv2.zip /tmp/aws /tmp/gh.tgz /tmp/gh_*

# The runner user, sudo and docker group exactly as in the official image.
RUN adduser --disabled-password --gecos "" --uid 1001 runner \
    && groupadd docker --gid 123 \
    && usermod -aG sudo runner \
    && usermod -aG docker runner \
    && echo "%sudo   ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers \
    && echo "Defaults env_keep += \"DEBIAN_FRONTEND\"" >> /etc/sudoers \
    && chmod 777 /home/runner

WORKDIR /home/runner
COPY --chown=runner:docker --from=runner /home/runner /home/runner
COPY --from=runner /usr/local/lib/docker/cli-plugins/docker-buildx /usr/local/lib/docker/cli-plugins/docker-buildx
COPY --from=runner /usr/bin/docker /usr/bin/docker
RUN ./bin/Runner.Listener --version && docker --version && docker compose version && docker buildx version

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

# TrueNAS api_client (not on PyPI; pinned to a commit on main) and the
# websocket-client it needs, for public-jobs' NFS updater. websocket-client
# 1.9.1 raced on close; see that workflow's history before moving the pin.
# renovate: datasource=git-refs depName=https://github.com/truenas/api_client currentValue=main
ARG TRUENAS_API_CLIENT_REF=8d7e37383717aea15ce46167cfcd92325acbcd8a
# renovate: datasource=pypi depName=websocket-client
ARG WEBSOCKET_CLIENT_VERSION=1.9.2
RUN pip3 install --no-cache-dir --break-system-packages \
      "git+https://github.com/truenas/api_client.git@${TRUENAS_API_CLIENT_REF}" \
      "websocket-client==${WEBSOCKET_CLIENT_VERSION}" \
    && python3 -c "import truenas_api_client, websocket"

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
