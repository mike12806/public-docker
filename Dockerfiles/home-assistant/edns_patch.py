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

    Patches socket.getaddrinfo (for requests/urllib3) and
    aiohttp.TCPConnector (for aiohttp/aiodns) to only use IPv4.
    Prevents 'Network unreachable' errors on networks without IPv6.
    """
    import os  # noqa: PLC0415

    if os.environ.get("DISABLE_IPV6", "").lower() not in ("1", "true", "yes"):
        return

    import logging  # noqa: PLC0415
    import socket  # noqa: PLC0415

    _LOGGER = logging.getLogger(__name__)
    _LOGGER.info("DISABLE_IPV6 is set; forcing all connections to IPv4")

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

'''

# --- Apply patches ---

with open(RUNNER_PY, "r") as f:
    content = f.read()

# Check if already fully patched
if "_patch_aiodns_to_disable_edns" in content and "_disable_ipv6_if_requested" in content:
    print("Already patched, skipping.")
    sys.exit(0)

# Validate anchor points exist
if "def _enable_posix_spawn" not in content:
    print("ERROR: Could not find _enable_posix_spawn in runner.py", file=sys.stderr)
    sys.exit(1)

if "_enable_posix_spawn()" not in content:
    print("ERROR: Could not find _enable_posix_spawn() call in runner.py", file=sys.stderr)
    sys.exit(1)

# Remove any previous partial patch (EDNS-only from older image version)
# so we can cleanly insert the combined patch block
if "_patch_aiodns_to_disable_edns" in content and "_disable_ipv6_if_requested" not in content:
    # Strip old patch function and call, we'll re-add both
    print("Upgrading from EDNS-only patch to combined patch...")
    # Remove old call
    content = content.replace(
        "    _patch_aiodns_to_disable_edns()\n", ""
    )
    # Remove old function (everything between the markers)
    import re
    content = re.sub(
        r'\ndef _patch_aiodns_to_disable_edns\(\).*?(?=\ndef )',
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

print("Patches applied successfully!")
