"""Renovate automerges Ansible updates only behind the Runner image checks.

The Runner image's ANSIBLE_VERSION moves only through Renovate. Every update
(majors included) automerges, but only once the PR's checks pass: the image
build and tests/runner-smoke.sh, which runs a play with the new version. That
needs ignoreTests off for ansible, and Renovate merging by itself, because
GitHub's auto-merge would wait only for the branch's required checks.

Run: python3 -m unittest discover -s tests -p 'test_*.py'
"""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class RenovateAnsibleGate(unittest.TestCase):
    def test_ansible_updates_wait_for_the_checks(self):
        config = json.loads((ROOT / "renovate.json").read_text())
        rules = [r for r in config.get("packageRules", []) if "ansible" in r.get("matchDepNames", [])]
        self.assertTrue(rules, "renovate.json has no packageRule for ansible")
        # Renovate applies every matching rule in order; the last one wins.
        merged = {}
        for rule in rules:
            merged.update(rule)
        self.assertIs(merged.get("automerge"), True)
        self.assertIs(merged.get("ignoreTests"), False, "ansible updates must wait for the checks")
        self.assertIs(merged.get("platformAutomerge"), False,
                      "GitHub's auto-merge waits only for required checks, not the Runner image's")

    def test_the_pin_is_exact(self):
        dockerfile = (ROOT / "Dockerfiles" / "Runner" / "Dockerfile").read_text()
        lines = dockerfile.splitlines()
        index = next(i for i, line in enumerate(lines) if line.startswith("ARG ANSIBLE_VERSION="))
        self.assertEqual(lines[index - 1].strip(), "# renovate: datasource=pypi depName=ansible")
        version = lines[index].split("=", 1)[1]
        self.assertRegex(version, r"^\d+\.\d+\.\d+$", "pin an exact Ansible version")


if __name__ == "__main__":
    unittest.main()
