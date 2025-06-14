FROM ghcr.io/actions/actions-runner:2.325.0

USER root

# Tool versions from GitHub releases and similar sources
ARG YQ_VERSION=4.40.5
ARG AWS_CLI_VERSION=2.13.35
ARG B2_CLI_VERSION=3.14.0
ARG ANSIBLE_VERSION=9.1.0
ARG LINODE_CLI_VERSION=5.59.0

# APT package versions
ARG PYTHON3_PIP_VERSION=22.0.2+dfsg-1ubuntu0.5
ARG PYTHON3_VENV_VERSION=3.10.6-1~22.04.1
ARG PIPX_VERSION=1.0.0-1
ARG SSHPASS_VERSION=1.09-1
ARG JQ_VERSION=1.6-2.1ubuntu3
ARG RSYNC_VERSION=3.2.7-0ubuntu0.22.04.4
ARG OPENSSH_CLIENT_VERSION=1:8.9p1-3ubuntu0.13
ARG CURL_VERSION=7.81.0-1ubuntu1.20
ARG UNZIP_VERSION=6.0-26ubuntu3.2
ARG WGET_VERSION=1.21.2-2ubuntu1.1

# Install base system packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3-pip=${PYTHON3_PIP_VERSION} \
    python3-venv=${PYTHON3_VENV_VERSION} \
    pipx=${PIPX_VERSION} \
    sshpass=${SSHPASS_VERSION} \
    jq=${JQ_VERSION} \
    rsync=${RSYNC_VERSION} \
    openssh-client=${OPENSSH_CLIENT_VERSION} \
    curl=${CURL_VERSION} \
    unzip=${UNZIP_VERSION} \
    wget=${WGET_VERSION} && \
    # Install AWS CLI
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWS_CLI_VERSION}.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    # Install YQ
    wget -O /usr/bin/yq "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_amd64" && \
    chmod +x /usr/bin/yq && \
    # Install Backblaze B2 CLI
    curl -L "https://github.com/Backblaze/B2_Command_Line_Tool/releases/download/v${B2_CLI_VERSION}/b2-linux" -o b2 && \
    chmod +x b2 && \
    mv b2 /usr/local/bin/ && \
    apt-get clean && \
    rm -rf awscliv2.zip aws /var/lib/apt/lists/* /root/.cache

USER runner

RUN pipx ensurepath && \
    pipx install "ansible==${ANSIBLE_VERSION}" && \
    pipx install "linode-cli==${LINODE_CLI_VERSION}" && \
    rm -rf /home/runner/.cache
