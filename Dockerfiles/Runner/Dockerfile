FROM ghcr.io/actions/actions-runner:2.329.0

# CodeQL version to install
ARG CODEQL_VERSION=2.23.3

USER root

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3-pip python3-venv pipx sshpass jq rsync openssh-client curl unzip wget docker-compose gpg xxd && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    wget -O /usr/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 && \
    chmod +x /usr/bin/yq && \
    # Install Backblaze B2 CLI
    curl -L https://github.com/Backblaze/B2_Command_Line_Tool/releases/latest/download/b2-linux -o b2 && \
    chmod +x b2 && \
    mv b2 /usr/local/bin/ && \
    apt-get clean && \
    rm -rf awscliv2.zip aws /var/lib/apt/lists/* /root/.cache

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
    docker-compose-plugin

# Install CodeQL
# Pinning to a specific version for reproducibility and to avoid SSL/network issues during build
RUN set -e && \
    bundle_tag_name="codeql-bundle-v${CODEQL_VERSION}" && \
    echo "Downloading CodeQL bundle ${CODEQL_VERSION}..." && \
    # Download the CodeQL bundle \
    curl -fsSL "https://github.com/github/codeql-action/releases/download/${bundle_tag_name}/codeql-bundle-linux64.tar.gz" -o /tmp/codeql-bundle.tar.gz && \
    # Create toolcache directory structure \
    mkdir -p "/opt/hostedtoolcache/CodeQL/${CODEQL_VERSION}/x64" && \
    echo "Unpacking the downloaded CodeQL bundle archive..." && \
    tar -xzf /tmp/codeql-bundle.tar.gz -C "/opt/hostedtoolcache/CodeQL/${CODEQL_VERSION}/x64" && \
    # Touch marker files \
    touch "/opt/hostedtoolcache/CodeQL/${CODEQL_VERSION}/x64/pinned-version" && \
    touch "/opt/hostedtoolcache/CodeQL/${CODEQL_VERSION}/x64.complete" && \
    # Add CodeQL to PATH \
    ln -s "/opt/hostedtoolcache/CodeQL/${CODEQL_VERSION}/x64/codeql/codeql" /usr/local/bin/codeql && \
    # Cleanup \
    rm -f /tmp/codeql-bundle.tar.gz && \
    # Verify installation \
    codeql --version

USER runner

RUN pipx ensurepath && \
    pipx install ansible && \
    pipx install linode-cli && \
    rm -rf /home/runner/.cache
