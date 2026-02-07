"""Patch homeassistant/runner.py to:
1. Disable EDNS cookies in aiodns (fixes DNS timeouts with forwarding resolvers)
2. Optionally disable IPv6 via DISABLE_IPV6 env var (fixes Network unreachable)

Based on: https://github.com/home-assistant/core/commit/8a5e031
Fixes: https://github.com/home-assistant/core/issues/145708

c-ares 1.33.0+ enables EDNS cookies by default which can cause timeouts
with forwarding DNS servers (dnsmasq, pihole, unbound chains).
"""

import sys

RUNNER_PY = "/usr/src/homeassistant/homeassistant/runner.py"

PATCH_FUNCTIONS = '''

def _patch_aiodns_to_disable_edns() -> None:
    """Disable EDNS cookies in aiodns by setting default flags to 0.

    c-ares 1.33.0+ enables EDNS cookies by default which can cause timeouts
    with some DNS servers. We disable EDNS (and thus cookies) by default
    unless flags are explicitly set.
    """
    try:
        import aiodns  # noqa: PLC0415
    except ImportError:
        return

    original_query = aiodns.DNSResolver.query

    def patched_query(self, host, qtype, flags=0):  # noqa: ANN001, ANN202
        """Wrapper to set flags=0 by default instead of None."""
        return original_query(self, host, qtype, flags)

    aiodns.DNSResolver.query = patched_query


def _disable_ipv6_if_requested() -> None:
    """Disable IPv6 connections when DISABLE_IPV6 env var is set.

    Patches three layers to ensure IPv4-only operation:
    1. socket.getaddrinfo - forces AF_INET (covers requests/urllib3/stdlib)
    2. aiodns.DNSResolver - forces c-ares to only use IPv4 DNS transport
    3. aiohttp.TCPConnector - forces AF_INET for HTTP connections

    This prevents both 'Network unreachable' errors (from attempting IPv6
    connections) and 'Could not contact DNS servers' errors (from c-ares
    trying to reach DNS servers over IPv6).
    """
    import os  # noqa: PLC0415

    if os.environ.get("DISABLE_IPV6", "").lower() not in ("1", "true", "yes"):
        return

    import logging  # noqa: PLC0415
    import socket  # noqa: PLC0415

    _LOGGER = logging.getLogger(__name__)
    _LOGGER.warning("DISABLE_IPV6 is set; forcing all connections to IPv4")

    # Layer 1: Patch socket.getaddrinfo to never return IPv6 results.
    # This covers requests, urllib3, and any stdlib-based DNS resolution.
    _orig_getaddrinfo = socket.getaddrinfo

    def _ipv4_only_getaddrinfo(
        host, port, family=0, type=0, proto=0, flags=0,
    ):
        """Wrapper that forces AF_INET for all unspecified lookups."""
        if family in (0, socket.AF_UNSPEC):
            family = socket.AF_INET
        elif family == socket.AF_INET6:
            return []
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = _ipv4_only_getaddrinfo

    # Layer 2: Patch aiodns.DNSResolver to constrain c-ares to IPv4 DNS transport.
    # Without this, c-ares may try to contact DNS servers over IPv6, causing
    # "Could not contact DNS servers" errors even though IPv4 DNS works fine.
    try:
        import aiodns  # noqa: PLC0415

        _orig_resolver_init = aiodns.DNSResolver.__init__

        def _ipv4_resolver_init(self, *args, **kwargs):
            """Wrapper that adds ARES_FLAG_USEVC is not needed; just set servers to IPv4."""
            _orig_resolver_init(self, *args, **kwargs)
            # After c-ares channel is created, force IPv4-only DNS lookups.
            # The nameservers are already set; we just need to ensure the
            # channel doesn't try to reach them over IPv6.
            try:
                self._channel.set_local_ip("0.0.0.0")  # noqa: SLF001
            except (AttributeError, Exception):
                pass

        aiodns.DNSResolver.__init__ = _ipv4_resolver_init
    except ImportError:
        pass

    # Layer 3: Patch aiohttp.TCPConnector to default to AF_INET.
    # This ensures all outbound HTTP connections use IPv4.
    try:
        import aiohttp  # noqa: PLC0415

        _orig_tcp_init = aiohttp.TCPConnector.__init__

        def _ipv4_tcp_init(self, *args, **kwargs):
            """Wrapper that defaults TCPConnector family to AF_INET."""
            kwargs.setdefault("family", socket.AF_INET)
            _orig_tcp_init(self, *args, **kwargs)

        aiohttp.TCPConnector.__init__ = _ipv4_tcp_init
    except ImportError:
        pass

    # Layer 4: Patch aiohttp resolver to use IPv4-only.
    # aiohttp's AsyncResolver wraps aiodns and may pass family=0 (UNSPEC).
    try:
        from aiohttp.resolver import AsyncResolver  # noqa: PLC0415

        _orig_async_resolve = AsyncResolver.resolve

        async def _ipv4_async_resolve(self, host, port=0, family=socket.AF_INET):
            """Wrapper that forces family to AF_INET."""
            return await _orig_async_resolve(self, host, port, family=socket.AF_INET)

        AsyncResolver.resolve = _ipv4_async_resolve
    except (ImportError, AttributeError):
        pass

'''

# --- Apply patches ---

with open(RUNNER_PY, "r") as f:
    content = f.read()

# Check if already fully patched (v2 with Layer 2 aiodns patch)
if "_ipv4_resolver_init" in content:
    print("Already patched (v2), skipping.")
    sys.exit(0)

# Validate anchor points exist
if "def _enable_posix_spawn" not in content:
    print("ERROR: Could not find _enable_posix_spawn in runner.py", file=sys.stderr)
    sys.exit(1)

if "_enable_posix_spawn()" not in content:
    print("ERROR: Could not find _enable_posix_spawn() call in runner.py", file=sys.stderr)
    sys.exit(1)

# Remove any previous patch (v1 EDNS-only or v1 combined) so we can cleanly insert v2
import re  # noqa: E402

if "_patch_aiodns_to_disable_edns" in content:
    print("Removing previous patch version...")
    # Remove old calls
    content = content.replace("    _patch_aiodns_to_disable_edns()\n", "")
    content = content.replace("    _disable_ipv6_if_requested()\n", "")
    # Remove old functions
    content = re.sub(
        r'\ndef _patch_aiodns_to_disable_edns\(\).*?(?=\ndef _enable_posix_spawn)',
        '\n',
        content,
        flags=re.DOTALL,
    )

# Insert patch functions before _enable_posix_spawn
content = content.replace(
    "def _enable_posix_spawn",
    PATCH_FUNCTIONS + "def _enable_posix_spawn",
)

# Insert calls right after _enable_posix_spawn()
content = content.replace(
    "    _enable_posix_spawn()\n",
    "    _enable_posix_spawn()\n"
    "    _patch_aiodns_to_disable_edns()\n"
    "    _disable_ipv6_if_requested()\n",
)

with open(RUNNER_PY, "w") as f:
    f.write(content)

print("Patches applied successfully (v2)!")
