"""Checks on the plugin's commands, from their text: they're instructions, not code."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./*-]+)")


class CommandTest(unittest.TestCase):
    def test_every_plugin_path_a_command_names_exists(self):
        for command in (ROOT / "commands").glob("*.md"):
            for path in PLUGIN_PATH.findall(command.read_text(encoding="utf-8")):
                with self.subTest(command=command.name, path=path):
                    self.assertTrue(list(ROOT.glob(path.rstrip("/"))), "nothing there")

    def test_migrate_init_handles_both_sources(self):
        text = (ROOT / "commands" / "migrate-init.md").read_text(encoding="utf-8")
        for needed in ("--design", "templates/config.json", "templates/config-design.json", "templates/discovery/legacy/*.md", "templates/discovery/design/*.md"):
            self.assertIn(needed, text)


if __name__ == "__main__":
    unittest.main()
