FROM ghcr.io/actions/actions-runner:2.325.0

USER root

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3-pip python3-venv pipx sshpass jq rsync openssh-client curl unzip && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    apt-get clean && \
    rm -rf awscliv2.zip aws /var/lib/apt/lists/* /root/.cache

USER runner

RUN pipx ensurepath && \
    pipx install ansible && \
    pipx install linode-cli && \
    rm -rf /home/runner/.cache
