FROM ghcr.io/actions/actions-runner:latest

USER root

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
    python3-pip python3-venv pipx sshpass jq && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /root/.cache

USER runner

RUN pipx ensurepath && \
    pipx install ansible && \
    pipx install linode-cli && \
    rm -rf /home/runner/.cache

USER runner
