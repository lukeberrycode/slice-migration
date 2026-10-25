"""Tests for hooks/gate.py, run as Claude Code runs it: JSON on stdin, exit code out."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "gate.py"
CONFIG = ROOT / "templates" / "config.json"


class GateHookTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp())
        (self.project / ".claude").mkdir()
        shutil.copy(CONFIG, self.project / ".claude" / "slice-migration.json")
        (self.project / "docs").mkdir()

    def tearDown(self):
        shutil.rmtree(self.project)

    def approve(self, *phases):
        gates = {p: {"approved_by": "A person", "date": "2026-10-25"} for p in phases}
        (self.project / "docs" / "gates.json").write_text(json.dumps(gates))

    def run_hook(self, tool, **tool_input):
        event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(self.project)}
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env={"CLAUDE_PROJECT_DIR": str(self.project), "PATH": ""},
        )

    def write(self, rel):
        return self.run_hook("Write", file_path=str(self.project / rel), content="x")

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)

    def assertBlocked(self, result, *words):
        self.assertEqual(result.returncode, 2)
        for word in words:
            self.assertIn(word, result.stderr)

    # Discovery needs no gate.
    def test_discovery_is_open_from_the_start(self):
        self.assertAllowed(self.write("docs/discovery/requirements.md"))
        self.assertAllowed(self.write("tests/characterisation/test_login.py"))

    # The gates, in order.
    def test_planning_is_blocked_until_discovery_is_approved(self):
        self.assertBlocked(self.write("docs/planning/rfc-0001.md"), "planning", "discovery gate")
        self.approve("discovery")
        self.assertAllowed(self.write("docs/planning/rfc-0001.md"))

    def test_new_code_needs_every_earlier_gate(self):
        self.assertBlocked(self.write("src/app.py"), "discovery gate")
        self.approve("discovery")
        self.assertBlocked(self.write("src/app.py"), "planning gate")
        self.approve("discovery", "planning")
        self.assertAllowed(self.write("src/app.py"))

    def test_relative_paths_are_gated_too(self):
        self.assertBlocked(self.run_hook("Edit", file_path="src/app.py"), "discovery gate")

    def test_an_approval_needs_a_name_and_a_date(self):
        (self.project / "docs" / "gates.json").write_text(json.dumps({"discovery": {"approved_by": "A person"}}))
        self.assertBlocked(self.write("docs/planning/rfc-0001.md"), "discovery gate")

    # Only a person approves a gate.
    def test_agent_cannot_write_the_gates_file(self):
        self.assertBlocked(self.write("docs/gates.json"), "only a person")

    def test_agent_cannot_write_the_gates_file_from_the_shell(self):
        result = self.run_hook("Bash", command='echo \'{"discovery":{}}\' > docs/gates.json')
        self.assertBlocked(result, "only a person")

    def test_other_shell_commands_are_allowed(self):
        self.assertAllowed(self.run_hook("Bash", command="pytest tests/characterisation"))

    # The legacy slice is the test oracle.
    def test_legacy_slice_is_read_only(self):
        self.approve("discovery", "planning", "execution")
        self.assertBlocked(self.write("legacy/src/Main.java"), "test oracle")

    # Failing closed, and staying out of the way.
    def test_unreadable_gates_file_approves_nothing(self):
        (self.project / "docs" / "gates.json").write_text("{not json")
        self.assertBlocked(self.write("docs/planning/rfc-0001.md"), "can't be read")

    def test_broken_config_blocks(self):
        (self.project / ".claude" / "slice-migration.json").write_text("{}")
        self.assertBlocked(self.write("docs/discovery/one-pager.md"), "can't be read")

    def test_projects_without_the_config_are_left_alone(self):
        (self.project / ".claude" / "slice-migration.json").unlink()
        self.assertAllowed(self.write("src/app.py"))

    def test_files_outside_the_project_are_left_alone(self):
        self.assertAllowed(self.run_hook("Write", file_path="/tmp/elsewhere/src/app.py"))


if __name__ == "__main__":
    unittest.main()
