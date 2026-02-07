"""Patch homeassistant/runner.py to disable EDNS cookies in aiodns.

Based on: https://github.com/home-assistant/core/commit/8a5e031
Fixes: https://github.com/home-assistant/core/issues/145708

c-ares 1.33.0+ enables EDNS cookies by default which can cause timeouts
with forwarding DNS servers (dnsmasq, pihole, unbound chains).
"""

import sys

RUNNER_PY = "/usr/src/homeassistant/homeassistant/runner.py"

PATCH_FUNCTION = '''

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

'''

with open(RUNNER_PY, "r") as f:
    content = f.read()

# Check if already patched
if "_patch_aiodns_to_disable_edns" in content:
    print("Already patched, skipping.")
    sys.exit(0)

# Insert the function before _enable_posix_spawn
if "def _enable_posix_spawn" not in content:
    print("ERROR: Could not find _enable_posix_spawn in runner.py", file=sys.stderr)
    sys.exit(1)

content = content.replace(
    "def _enable_posix_spawn",
    PATCH_FUNCTION + "def _enable_posix_spawn",
)

# Add the call inside run(), right after _enable_posix_spawn()
if "_enable_posix_spawn()" not in content:
    print("ERROR: Could not find _enable_posix_spawn() call in runner.py", file=sys.stderr)
    sys.exit(1)

content = content.replace(
    "    _enable_posix_spawn()\n",
    "    _enable_posix_spawn()\n    _patch_aiodns_to_disable_edns()\n",
)

with open(RUNNER_PY, "w") as f:
    f.write(content)

print("Patch applied successfully!")
