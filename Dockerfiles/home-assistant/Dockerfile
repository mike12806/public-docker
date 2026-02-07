# Custom Home Assistant image with EDNS cookie fix
# Based on https://github.com/home-assistant/core/commit/8a5e031339fae48f3fb84a78dd4ec53026cda8e0
# Fixes DNS timeouts with forwarding resolvers that don't handle EDNS cookies properly
# Related issue: https://github.com/home-assistant/core/issues/145708

ARG HA_VERSION=latest
FROM ghcr.io/home-assistant/home-assistant:${HA_VERSION}

# Apply the EDNS cookie patch to homeassistant/runner.py
# This patches aiodns to disable EDNS cookies by default, preventing timeouts
# with DNS servers (dnsmasq, pihole, unbound) that don't properly forward EDNS cookies
COPY edns_patch.py /tmp/edns_patch.py
RUN python3 /tmp/edns_patch.py && rm /tmp/edns_patch.py
