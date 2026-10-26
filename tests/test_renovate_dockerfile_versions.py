"""Renovate can update every pinned tool version in the Dockerfiles.

Uses the matchStrings from renovate.json's custom regex manager, so a version
ARG that Renovate wouldn't see (missing or malformed `# renovate:` comment)
fails here instead of silently going stale.

Run: python3 -m unittest discover -s tests -p 'test_*.py'
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Version ARGs Renovate doesn't track, and why.
UNTRACKED = {
    # CodeQL bundle: tracked by hand (not yet a Renovate dependency).
    "CODEQL_VERSION",
}


def manager_regexes():
    config = json.loads((ROOT / "renovate.json").read_text())
    for manager in config.get("customManagers", []):
        if manager.get("customType") != "regex":
            continue
        files = [p.strip("/") for p in manager["managerFilePatterns"]]
        # Renovate's (?<name>) groups are Python's (?P<name>).
        patterns = [re.compile(s.replace("(?<", "(?P<")) for s in manager["matchStrings"]]
        yield files, patterns


def dockerfiles():
    return sorted(ROOT.glob("Dockerfiles/*/Dockerfile"))


class RenovateDockerfileVersions(unittest.TestCase):
    def test_regex_manager_enabled(self):
        config = json.loads((ROOT / "renovate.json").read_text())
        self.assertIn("custom.regex", config["enabledManagers"])

    def test_every_version_arg_is_tracked(self):
        managers = list(manager_regexes())
        self.assertTrue(managers, "no custom regex manager in renovate.json")
        for dockerfile in dockerfiles():
            text = dockerfile.read_text()
            rel = str(dockerfile.relative_to(ROOT))
            covering = [p for files, pats in managers for p in pats
                        if any(re.search(f, rel) for f in files)]
            tracked = {}
            for pattern in covering:
                for m in pattern.finditer(text):
                    arg = re.search(r"ARG ([A-Z0-9_]+)=", m.group(0)).group(1)
                    tracked[arg] = m.groupdict()
            version_args = set(re.findall(r"^ARG ([A-Z0-9_]+_(?:VERSION|REF))=", text, re.M))
            # The built-in dockerfile manager updates ARGs a FROM line uses.
            from_args = set(re.findall(r"^FROM \S*\$\{?([A-Z0-9_]+)\}?", text, re.M))
            version_args -= from_args
            for arg in sorted(version_args - UNTRACKED):
                with self.subTest(dockerfile=rel, arg=arg):
                    self.assertIn(arg, tracked, f"{arg} has no `# renovate:` comment Renovate can read")
                    dep = tracked[arg]
                    self.assertTrue(dep["datasource"] and dep["depName"] and dep["currentValue"])
                    if dep.get("currentDigest") is not None:
                        self.assertRegex(dep["currentDigest"], r"^[0-9a-f]{40}$")

    def test_extract_version_patterns_compile(self):
        for files, patterns in manager_regexes():
            for dockerfile in dockerfiles():
                for pattern in patterns:
                    for m in pattern.finditer(dockerfile.read_text()):
                        ev = m.groupdict().get("extractVersion")
                        if ev:
                            with self.subTest(extractVersion=ev):
                                rx = re.compile(ev.replace("(?<", "(?P<"))
                                self.assertIn("version", rx.groupindex)
                                self.assertEqual(rx.match("v" + m.group("currentValue")).group("version"),
                                                 m.group("currentValue"))


if __name__ == "__main__":
    unittest.main()
