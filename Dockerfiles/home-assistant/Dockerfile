# Custom Home Assistant image with EDNS cookie fix
# Based on https://github.com/home-assistant/core/commit/8a5e031339fae48f3fb84a78dd4ec53026cda8e0
# Fixes DNS timeouts with forwarding resolvers that don't handle EDNS cookies properly

ARG HA_VERSION=latest
FROM ghcr.io/home-assistant/home-assistant:${HA_VERSION}

# Apply the EDNS cookie patch to homeassistant/runner.py
# This patches aiodns to disable EDNS cookies by default, preventing timeouts
# with DNS servers (dnsmasq, pihole, unbound) that don't properly forward EDNS cookies
USER root
RUN sed -i '/def _enable_posix_spawn/i \
def _patch_aiodns_to_disable_edns() -> None:\
    """Disable EDNS cookies in aiodns by setting default flags to 0.\
\
    c-ares 1.33.0+ enables EDNS cookies by default which can cause timeouts\
    with some DNS servers. We disable EDNS (and thus cookies) by default\
    unless flags are explicitly set.\
    """\
    try:\
        import aiodns\
    except ImportError:\
        return\
\
    original_query = aiodns.DNSResolver.query\
\
    def patched_query(self, host, qtype, flags=0):\  # noqa: ANN001, ANN202\
        """Wrapper to set flags=0 by default instead of None."""\
        return original_query(self, host, qtype, flags)\
\
    aiodns.DNSResolver.query = patched_query\
\
' /usr/src/homeassistant/homeassistant/runner.py && \
    sed -i 's/def setup(/def setup(/' /usr/src/homeassistant/homeassistant/runner.py && \
    sed -i '/def setup(/a \    _patch_aiodns_to_disable_edns()' /usr/src/homeassistant/homeassistant/runner.py && \
    grep -A 5 "_patch_aiodns_to_disable_edns" /usr/src/homeassistant/homeassistant/runner.py

# Switch back to default user from base image (inherits from upstream)
USER root
