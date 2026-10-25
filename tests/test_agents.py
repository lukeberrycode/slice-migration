"""Guardrails on the plugin's agents, checked from their definitions."""

import unittest
from pathlib import Path

AGENTS = Path(__file__).resolve().parent.parent / "agents"
READ_ONLY = {"Read", "Glob", "Grep"}


def frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "---", f"{path.name} has no frontmatter"
    fields = {}
    for line in lines[1 : lines.index("---", 1)]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"')
    return fields


class AgentTest(unittest.TestCase):
    def test_the_gate_reviewer_is_read_only(self):
        tools = frontmatter(AGENTS / "gate-reviewer.md").get("tools", "")
        # No tools field would mean every tool; an empty set would mean none.
        granted = {t.strip() for t in tools.split(",") if t.strip()}
        self.assertTrue(granted, "gate-reviewer must list its tools explicitly")
        self.assertLessEqual(granted, READ_ONLY, f"gate-reviewer can do more than read: {granted - READ_ONLY}")

    def test_every_agent_lists_its_tools(self):
        for path in AGENTS.glob("*.md"):
            with self.subTest(agent=path.name):
                self.assertIn("tools", frontmatter(path))


if __name__ == "__main__":
    unittest.main()
