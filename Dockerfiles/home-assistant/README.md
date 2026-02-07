# Home Assistant with EDNS Cookie Fix

Custom Home Assistant Docker image with a patch to disable EDNS cookies, fixing DNS timeout issues with forwarding resolvers.

## Problem

Home Assistant 2025.5+ uses aiodns with c-ares 1.33.0+, which enables EDNS cookies by default. Many DNS forwarding setups (dnsmasq, pihole, unbound chains) don't properly handle EDNS cookies, causing intermittent DNS resolution failures with errors like:

```
Could not contact DNS servers
Cannot connect to host <hostname>:443 ssl:default [Timeout while contacting DNS servers]
```

## Solution

This image applies the patch from [home-assistant/core#8a5e031](https://github.com/home-assistant/core/commit/8a5e031339fae48f3fb84a78dd4ec53026cda8e0) which disables EDNS cookies in aiodns by default.

## Usage

Replace the official Home Assistant image in your Kubernetes deployment:

```yaml
# Before
image: ghcr.io/home-assistant/home-assistant:2026.2.1

# After
image: ghcr.io/mike12806/public-docker/home-assistant:latest
# or pin to specific version:
image: ghcr.io/mike12806/public-docker/home-assistant:2026.2.1
```

## Build Arguments

- `HA_VERSION`: Home Assistant version to base the image on (default: latest)

## License

This Dockerfile is licensed under Apache 2.0. Home Assistant Core is also licensed under Apache 2.0.

## Related Issues

- [home-assistant/core#145708](https://github.com/home-assistant/core/issues/145708) - Timeout while contacting DNS servers when forwarding resolver has broken EDNS cookie handling
- [home-assistant/core#8a5e031](https://github.com/home-assistant/core/commit/8a5e031339fae48f3fb84a78dd4ec53026cda8e0) - Upstream patch
