#!/bin/bash
set -e

# If command is passed, exec it directly (for "docker run ... <cmd>")
if [[ "$#" -gt 0 && "$1" != "./run.sh" ]]; then
  exec "$@"
fi

cleanup() {
  cd /home/runner
  su runner -c "./config.sh remove --unattended || true"
  while pgrep -u runner -f "Runner.Worker"; do
    sleep 2
  done
  exit 0
}
trap cleanup SIGTERM

cd /home/runner
exec su runner -s /bin/bash -c "./run.sh"
