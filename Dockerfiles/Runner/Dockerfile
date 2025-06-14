FROM ghcr.io/actions/actions-runner:2.325.0

USER root

# Tool versions from GitHub releases and similar sources
ARG YQ_VERSION=4.40.5
ARG AWS_CLI_VERSION=2.13.35
ARG B2_CLI_VERSION=3.14.0
ARG ANSIBLE_VERSION=9.1.0
ARG LINODE_CLI_VERSION=5.41.1

# Install base system packages
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3-pip \
    python3-venv \
    pipx \
    sshpass \
    jq \
    rsync \
    openssh-client \
    curl \
    unzip \
    wget && \
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
    # Record package versions for future reference
    echo "Installed package versions:" > /tmp/package_versions.txt && \
    dpkg-query -W python3-pip python3-venv pipx sshpass jq rsync openssh-client curl unzip wget >> /tmp/package_versions.txt && \
    cat /tmp/package_versions.txt && \
    # Cleanup
    apt-get clean && \
    rm -rf awscliv2.zip aws /var/lib/apt/lists/* /root/.cache

USER runner

RUN pipx ensurepath && \
    pipx install "ansible==${ANSIBLE_VERSION}" && \
    pipx install "linode-cli==${LINODE_CLI_VERSION}" && \
    rm -rf /home/runner/.cache
