# The runner and Docker client come from the official image; everything else
# sits on Ubuntu 26.04, so jobs that asked GitHub for ubuntu-26.04 get the same
# OS here. Renovate bumps both FROM lines.
#
# Each tool is fetched or installed in its own stage, so BuildKit builds them
# in parallel and a version bump rebuilds only that stage. Every stage leaves
# its files under /out, laid out as they go in the image (parent directories
# included, with their owners and modes), and the final stage stacks them on
# the base with COPY --link, which doesn't depend on the layers beneath it.
FROM ghcr.io/actions/actions-runner:2.338.2 AS runner

# ---------- Base: OS packages and the runner user ----------
FROM ubuntu:26.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
# Same runner settings as the official image (ARC relies on them).
ENV RUNNER_MANUALLY_TRAP_SIG=1
ENV ACTIONS_RUNNER_PRINT_LOG_TO_STDOUT=1
ENV ImageOS=ubuntu26

# Toolcache root used by @actions/tool-cache on self-hosted runners
ENV RUNNER_TOOL_CACHE=/opt/hostedtoolcache

# Some Copilot/agents flows demand a GitHub host string. Keep the job step that writes
# to $GITHUB_ENV, but this ENV helps in most paths.
ENV GITHUB_HOST=github.com

# Base tooling, plus the libraries the runner's bundled .NET needs (the
# official image gets those from dotnet/runtime-deps).
RUN set -eux; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends \
      sudo lsb-release gpg-agent software-properties-common git \
      ca-certificates libc6 libgcc-s1 libstdc++6 libssl3t64 libkrb5-3 zlib1g tzdata \
      "$(apt-cache search --names-only '^libicu[0-9]+$' | sort -V | tail -1 | cut -d' ' -f1)" \
      python3 python3-pip python3-venv python3-yaml pipx sshpass jq rsync openssh-client curl unzip zip wget gpg xxd gnupg \
      postgresql-client restic dnsutils iputils-ping file make; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /root/.cache

# The runner user, sudo and docker group exactly as in the official image.
RUN adduser --disabled-password --gecos "" --uid 1001 runner \
    && groupadd docker --gid 123 \
    && usermod -aG sudo runner \
    && usermod -aG docker runner \
    && echo "%sudo   ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers \
    && echo "Defaults env_keep += \"DEBIAN_FRONTEND\"" >> /etc/sudoers \
    && chmod 777 /home/runner

WORKDIR /home/runner

# The runner itself, over the runner user's home (which keeps its owner and
# mode). It is checked as the runner user in tests/runner-smoke.sh: running it
# here as root would leave a root-owned ~/_diag it can't write to.
FROM base AS runner-home
COPY --chown=runner:docker --from=runner /home/runner /home/runner

# ---------- Downloads ----------
FROM ubuntu:26.04 AS fetch
# The self-hosted runners occasionally drop a TLS handshake (curl exit 35), so
# every download retries transient failures. Only the download stages see this
# rc file; the image doesn't.
ENV CURL_HOME=/etc/curl-build
RUN set -eux; \
    apt-get update -y; \
    apt-get install -y --no-install-recommends ca-certificates curl unzip; \
    rm -rf /var/lib/apt/lists/*; \
    mkdir -p "$CURL_HOME"; \
    printf '%s\n' 'retry = 5' 'retry-all-errors' 'retry-delay = 3' 'connect-timeout = 30' > "$CURL_HOME/.curlrc"
WORKDIR /tmp

# AWS CLI v2. Its installer writes absolute symlinks, so it installs in place
# and is copied to /out from there.
FROM fetch AS awscli
RUN set -eux; \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip; \
    unzip -q awscliv2.zip; \
    ./aws/install; \
    mkdir /out; \
    cp -a --parents /usr/local/aws-cli /usr/local/bin/aws /usr/local/bin/aws_completer /out; \
    /usr/local/bin/aws --version

# yq v4.53.2 and Backblaze B2 CLI v4.6.0
FROM fetch AS yq-b2
RUN set -eux; \
    mkdir -p /out/usr/bin /out/usr/local/bin; \
    curl -fsSLo /out/usr/bin/yq https://github.com/mikefarah/yq/releases/download/v4.53.2/yq_linux_amd64; \
    echo "d56bf5c6819e8e696340c312bd70f849dc1678a7cda9c2ad63eebd906371d56b  /out/usr/bin/yq" | sha256sum -c -; \
    curl -fsSLo /out/usr/local/bin/b2 https://github.com/Backblaze/B2_Command_Line_Tool/releases/download/v4.6.0/b2-linux; \
    echo "4ac55ebe37a50eba9d19f24809da584539e1395992b8aa43f906cc83180bffa1  /out/usr/local/bin/b2" | sha256sum -c -; \
    chmod +x /out/usr/bin/yq /out/usr/local/bin/b2

# Docker Compose plugin (Docker's apt repo has no 26.04 suite yet)
FROM fetch AS compose
# renovate: datasource=github-releases depName=docker/compose extractVersion=^v(?<version>.+)$
ARG COMPOSE_VERSION=5.6.1
RUN set -eux; \
    url="https://github.com/docker/compose/releases/download/v${COMPOSE_VERSION}/docker-compose-linux-x86_64"; \
    bin=/out/usr/local/lib/docker/cli-plugins/docker-compose; \
    mkdir -p "$(dirname "$bin")"; \
    curl -fsSLo "$bin" "$url"; \
    echo "$(curl -fsSL "$url.sha256" | cut -d' ' -f1)  $bin" | sha256sum -c -; \
    chmod +x "$bin"; \
    "$bin" version

# GitHub CLI
FROM fetch AS gh
# renovate: datasource=github-releases depName=cli/cli extractVersion=^v(?<version>.+)$
ARG GH_VERSION=2.103.2
RUN set -eux; \
    tgz="gh_${GH_VERSION}_linux_amd64.tar.gz"; \
    curl -fsSLO "https://github.com/cli/cli/releases/download/v${GH_VERSION}/${tgz}"; \
    curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_checksums.txt" | grep " ${tgz}\$" | sha256sum -c -; \
    tar -xzf "$tgz"; \
    install -D -m 755 "gh_${GH_VERSION}_linux_amd64/bin/gh" /out/usr/local/bin/gh; \
    /out/usr/local/bin/gh --version

# ---------- Pinned tools jobs would otherwise download every run ----------
# Renovate bumps these through the `# renovate:` comments (custom regex manager
# in renovate.json). Workflows that run on this image use the tools as-is
# instead of installing their own.

# Node in the toolcache layout ($RUNNER_TOOL_CACHE), so actions/setup-node
# finds it without downloading (node-version: 24), and on PATH for jobs that
# skip setup-node. 1001:1001 is runner:runner.
FROM fetch AS node
# renovate: datasource=node-version depName=node
ARG NODE_VERSION=24.22.1
RUN set -eux; \
    tgz="node-v${NODE_VERSION}-linux-x64.tar.gz"; \
    dir="/opt/hostedtoolcache/node/${NODE_VERSION}/x64"; \
    curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/${tgz}"; \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/SHASUMS256.txt" | grep " ${tgz}\$" | sha256sum -c -; \
    mkdir -p "/out$dir" /out/usr/local/bin; \
    tar -xzf "$tgz" -C "/out$dir" --strip-components=1; \
    touch "/out$dir.complete"; \
    ln -sf "$dir/bin/node" "$dir/bin/npm" "$dir/bin/npx" /out/usr/local/bin/; \
    chown -R 1001:1001 /out/opt/hostedtoolcache; \
    "/out$dir/bin/node" --version

# Terraform and Vault (zips checked against HashiCorp's SHA256SUMS)
FROM fetch AS terraform
# renovate: datasource=github-releases depName=hashicorp/terraform extractVersion=^v(?<version>.+)$
ARG TERRAFORM_VERSION=1.17.0
RUN set -eux; \
    zip="terraform_${TERRAFORM_VERSION}_linux_amd64.zip"; \
    curl -fsSLO "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/${zip}"; \
    curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_SHA256SUMS" | grep " ${zip}\$" | sha256sum -c -; \
    mkdir -p /out/usr/local/bin; \
    unzip -q "$zip" terraform -d /out/usr/local/bin; \
    /out/usr/local/bin/terraform version

FROM fetch AS vault
# renovate: datasource=github-releases depName=hashicorp/vault extractVersion=^v(?<version>.+)$
ARG VAULT_VERSION=2.2.1
RUN set -eux; \
    zip="vault_${VAULT_VERSION}_linux_amd64.zip"; \
    curl -fsSLO "https://releases.hashicorp.com/vault/${VAULT_VERSION}/${zip}"; \
    curl -fsSL "https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_SHA256SUMS" | grep " ${zip}\$" | sha256sum -c -; \
    mkdir -p /out/usr/local/bin; \
    unzip -q "$zip" vault -d /out/usr/local/bin; \
    /out/usr/local/bin/vault version

FROM fetch AS kubectl
# renovate: datasource=github-releases depName=kubernetes/kubernetes extractVersion=^v(?<version>.+)$
ARG KUBECTL_VERSION=1.37.1
RUN set -eux; \
    url="https://dl.k8s.io/release/v${KUBECTL_VERSION}/bin/linux/amd64/kubectl"; \
    mkdir -p /out/usr/local/bin; \
    curl -fsSLo /out/usr/local/bin/kubectl "$url"; \
    echo "$(curl -fsSL "$url.sha256")  /out/usr/local/bin/kubectl" | sha256sum -c -; \
    chmod +x /out/usr/local/bin/kubectl; \
    /out/usr/local/bin/kubectl version --client

FROM fetch AS helm
# renovate: datasource=github-releases depName=helm/helm extractVersion=^v(?<version>.+)$
ARG HELM_VERSION=4.3.1
RUN set -eux; \
    tgz="helm-v${HELM_VERSION}-linux-amd64.tar.gz"; \
    curl -fsSLO "https://get.helm.sh/${tgz}"; \
    echo "$(curl -fsSL "https://get.helm.sh/${tgz}.sha256sum" | cut -d' ' -f1)  ${tgz}" | sha256sum -c -; \
    tar -xzf "$tgz" linux-amd64/helm; \
    install -D -m 755 linux-amd64/helm /out/usr/local/bin/helm; \
    /out/usr/local/bin/helm version

# ---------- Python and npm installs (need the base OS) ----------
# TrueNAS api_client (not on PyPI; pinned to a commit on main) and the
# websocket-client it needs, for public-jobs' NFS updater. websocket-client
# 1.9.1 raced on close; see that workflow's history before moving the pin.
FROM base AS truenas
# renovate: datasource=git-refs depName=https://github.com/truenas/api_client currentValue=main
ARG TRUENAS_API_CLIENT_REF=8d7e37383717aea15ce46167cfcd92325acbcd8a
# renovate: datasource=pypi depName=websocket-client
ARG WEBSOCKET_CLIENT_VERSION=1.9.2
RUN set -eux; \
    pip3 install --no-cache-dir --break-system-packages --root /out \
      "git+https://github.com/truenas/api_client.git@${TRUENAS_API_CLIENT_REF}" \
      "websocket-client==${WEBSOCKET_CLIENT_VERSION}"; \
    PYTHONPATH="$(echo /out/usr/local/lib/python3*/dist-packages)" python3 -c "import truenas_api_client, websocket"

# Full Ansible (ansible-core plus collections), for playbooks that would
# otherwise `pipx run --spec ansible` (which fetches it on every run).
FROM base AS pipx
USER runner
# renovate: datasource=pypi depName=ansible
ARG ANSIBLE_VERSION=14.5.0
# renovate: datasource=pypi depName=linode-cli
ARG LINODE_CLI_VERSION=5.69.0
RUN pipx install --include-deps "ansible==${ANSIBLE_VERSION}" && \
    pipx install "linode-cli==${LINODE_CLI_VERSION}" && \
    ~/.local/bin/ansible-playbook --version && \
    rm -rf ~/.cache
USER root
RUN mkdir /out && cp -a --parents /home/runner/.local /out

# Renovate and wrangler in npx's cache, under the same package specs the
# workflows pass to npx (`npx --yes -p renovate@X ...`), so they run without
# downloading and unpacking Renovate (it took ~6 min on a throttled runner).
# Keep in step with the workflows' RENOVATE_VERSION / WRANGLER_VERSION pins;
# Renovate bumps both.
FROM base AS npx
COPY --from=node /out/ /
USER runner
# renovate: datasource=npm depName=renovate
ARG RENOVATE_VERSION=44.186.1
# renovate: datasource=npm depName=wrangler
ARG WRANGLER_VERSION=4.153.0
RUN set -eux; \
    npx --yes -p "renovate@${RENOVATE_VERSION}" -c 'renovate --version'; \
    npx --yes "wrangler@${WRANGLER_VERSION}" --version; \
    rm -rf ~/.npm/_logs
USER root
RUN mkdir /out && cp -a --parents /home/runner/.npm /out

# ---------- The image ----------
FROM base
COPY --link --from=runner-home /home/ /home/
COPY --link --from=runner /usr/local/lib/docker/cli-plugins/docker-buildx /usr/local/lib/docker/cli-plugins/docker-buildx
COPY --link --from=runner /usr/bin/docker /usr/bin/docker
COPY --link --from=awscli /out/ /
COPY --link --from=yq-b2 /out/ /
COPY --link --from=compose /out/ /
COPY --link --from=gh /out/ /
COPY --link --from=node /out/ /
COPY --link --from=terraform /out/ /
COPY --link --from=vault /out/ /
COPY --link --from=kubectl /out/ /
COPY --link --from=helm /out/ /
COPY --link --from=truenas /out/ /
COPY --link --from=pipx /out/ /
COPY --link --from=npx /out/ /

USER runner
# pipx puts its apps here. Job steps don't read ~/.bashrc, so it goes on PATH
# directly instead of through `pipx ensurepath`.
ENV PATH=/home/runner/.local/bin:${PATH}
