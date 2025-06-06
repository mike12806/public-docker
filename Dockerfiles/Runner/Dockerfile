FROM ghcr.io/actions/actions-runner:latest

USER root

# Update and install system packages
RUN apt-get update -y && \
    apt-get install -y \
    python3-pip \
    python3-venv \
    pipx \
    sshpass && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER runner

RUN pipx ensurepath && \
    pipx install ansible && \
    pipx install linode-cli

# Do NOT switch back to root!
USER runner
