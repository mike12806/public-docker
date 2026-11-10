# Gitea with the Alpine base packages kept current.
#
# Upstream rebuilds gitea/gitea only when Gitea itself releases, so an Alpine
# security fix can sit unshipped for weeks: OpenSSH's CVE-2026-123158
# ("SSHole", musl builds without PAM) was fixed in Alpine 3.24 as
# openssh-server 10.3_p1-r2 on 2026-11-05, while gitea/gitea:28.3.0 (built
# 2026-11-01) still ships 10.3_p1-r1. The publish workflow rebuilds this image
# weekly (and on any change here), so it picks up whatever Alpine has patched
# since the upstream build. Run the workflow by hand to ship a fix sooner.
#
# Renovate bumps GITEA_VERSION; the base image's own entrypoint, user and
# volumes are inherited unchanged.

ARG GITEA_VERSION=28.3.0
FROM gitea/gitea:${GITEA_VERSION}

RUN apk upgrade --no-cache
