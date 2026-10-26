#!/usr/bin/env bash
# Smoke test for the Runner image: every preinstalled tool works, and the
# tools jobs reach through npx and actions/setup-node are already cached, so
# a job using them doesn't download anything.
#
# Usage: tests/runner-smoke.sh <image> [Dockerfile]
set -euo pipefail

image=$1
dockerfile=${2:-Dockerfiles/Runner/Dockerfile}
arg() { sed -n "s/^ARG $1=//p" "$dockerfile"; }

node_version=$(arg NODE_VERSION)
renovate_version=$(arg RENOVATE_VERSION)
wrangler_version=$(arg WRANGLER_VERSION)
ansible_version=$(arg ANSIBLE_VERSION)
for v in node_version renovate_version wrangler_version ansible_version; do
  [ -n "${!v}" ] || { echo "::error::$v not found in $dockerfile"; exit 1; }
done

docker image inspect -f 'Image size: {{.Size}} bytes' "$image"

echo "::group::OS, runner and sudo"
docker run --rm "$image" bash -euc '
  . /etc/os-release; echo "$PRETTY_NAME"
  [ "$VERSION_ID" = "26.04" ] || { echo "want Ubuntu 26.04, got $VERSION_ID"; exit 1; }
  [ "$(id -un)" = runner ] && [ "$(id -u)" = 1001 ]
  ~/bin/Runner.Listener --version
  test -x ~/run.sh
  sudo -n true && echo "runner has passwordless sudo"
'
echo "::endgroup::"

echo "::group::Tools on PATH"
docker run --rm "$image" bash -euc '
  python3 --version; codeql --version; psql --version
  node --version; npm --version
  terraform version; vault version; kubectl version --client
  ansible-playbook --version; command -v linode-cli
  restic version; dig -v; ping -V; yq --version; jq --version; b2 version
  docker --version; docker compose version; docker buildx version
  gh --version; git --version; make --version | head -1; file --version | head -1; aws --version
  python3 -c "import truenas_api_client, websocket; print(\"truenas_api_client + websocket-client\", websocket.__version__)"
'
echo "::endgroup::"

echo "::group::Pinned versions"
docker run --rm -e NODE_VERSION="$node_version" -e ANSIBLE_VERSION="$ansible_version" "$image" bash -euc '
  [ "$(node --version)" = "v${NODE_VERSION}" ] || { echo "node is $(node --version), want v${NODE_VERSION}"; exit 1; }
  pipx list --short | grep -qx "ansible ${ANSIBLE_VERSION}" || { pipx list --short; echo "want ansible ${ANSIBLE_VERSION}"; exit 1; }
  echo "node and ansible match the Dockerfile"
'
echo "::endgroup::"

# actions/setup-node looks in $RUNNER_TOOL_CACHE/node/<version>/x64 and only
# trusts a version with the x64.complete marker beside it.
echo "::group::Node in the toolcache"
docker run --rm -e NODE_VERSION="$node_version" "$image" bash -euc '
  dir="$RUNNER_TOOL_CACHE/node/$NODE_VERSION"
  test -f "$dir/x64.complete"
  test -x "$dir/x64/bin/node"
  [ "$(stat -c %U "$dir/x64")" = runner ] || { echo "toolcache not owned by runner"; exit 1; }
  echo "setup-node will find $dir"
'
echo "::endgroup::"

# No network: these pass only if npx finds them in its cache.
echo "::group::npx cache (no network)"
docker run --rm --network none \
  -e RENOVATE_VERSION="$renovate_version" -e WRANGLER_VERSION="$wrangler_version" \
  "$image" bash -euc '
  cd "$(mktemp -d)"
  echo "{}" > renovate.json
  npx --yes -p "renovate@${RENOVATE_VERSION}" renovate-config-validator renovate.json
  npx --yes --package="renovate@${RENOVATE_VERSION}" -- renovate-config-validator --strict renovate.json
  npx --yes "wrangler@${WRANGLER_VERSION}" --version
'
echo "::endgroup::"

echo "Runner image smoke test passed."
