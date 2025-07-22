FROM ghcr.io/actions/actions-runner:2.327.0

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

USER runner

RUN pipx ensurepath && \
    pipx install ansible && \
    pipx install linode-cli && \
    rm -rf /home/runner/.cache
