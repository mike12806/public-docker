#!/bin/bash
set -e

cleanup() {
  echo "SIGTERM received: unregistering runner"
  cd /home/runner
  # Unregister the runner (ignore errors in case it's already removed)
  su runner -c "./config.sh remove --unattended || true"
  # Wait for any running job to finish before exiting
  while pgrep -u runner -f "Runner.Worker"; do
    echo "Job still running, waiting before shutdown..."
    sleep 2
  done
  echo "Graceful shutdown complete."
  exit 0
}
trap cleanup SIGTERM

# Launch the runner as the runner user
cd /home/runner
exec su runner -s /bin/bash -c "./run.sh"
