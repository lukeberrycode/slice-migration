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
    def test_the_stack_rfc_is_blocked_until_discovery_is_approved(self):
        self.assertBlocked(self.write("docs/planning/rfc-0001.md"), "stack phase", "discovery gate")
        self.approve("discovery")
        self.assertAllowed(self.write("docs/planning/rfc-0001.md"))
        self.assertAllowed(self.write("docs/planning/rfc-0001/spikes/run.sh"))
        self.assertAllowed(self.write("docs/planning/README.md"))

    def test_the_rest_of_planning_waits_for_the_stack_gate(self):
        self.approve("discovery")
        self.assertBlocked(self.write("docs/planning/cut-over.md"), "planning phase", "stack gate")
        self.approve("discovery", "stack")
        self.assertAllowed(self.write("docs/planning/cut-over.md"))

    def test_new_code_needs_every_earlier_gate(self):
        self.assertBlocked(self.write("src/app.py"), "discovery gate")
        self.approve("discovery")
        self.assertBlocked(self.write("src/app.py"), "stack gate")
        self.approve("discovery", "stack")
        self.assertBlocked(self.write("src/app.py"), "planning gate")
        self.approve("discovery", "stack", "planning")
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

    # Shell commands that write to gated paths.
    def shell(self, command):
        return self.run_hook("Bash", command=command)

    def test_shell_writes_to_gated_paths_are_blocked(self):
        for command in [
            "cat > src/app.py",
            "echo 'print(1)' >> src/app.py",
            "echo hi>src/app.py",
            "make 2>&1 | tee build.log src/out.txt",
            "cp /tmp/app.py src/app.py",
            "mv draft.md docs/planning/rfc-0001.md",
            "touch src/__init__.py",
            "sed -i 's/a/b/' src/app.py",
            "dd if=/dev/zero of=src/blob bs=1 count=1",
            "cd src && touch app.py",
            "ls; cat > src/app.py <<'EOF'\nprint('it\\'s here')\nEOF",
            "pytest &> docs/planning/results.txt",
        ]:
            with self.subTest(command=command):
                self.assertBlocked(self.shell(command), "discovery gate")

    def test_shell_writes_allowed_once_the_gates_are_approved(self):
        self.approve("discovery", "planning")
        self.assertAllowed(self.shell("cat > src/app.py <<'EOF'\nprint('ok')\nEOF"))
        self.assertAllowed(self.shell("cd src && touch app.py"))

    def test_shell_reads_and_open_phases_are_allowed(self):
        for command in [
            "cat src/app.py",
            "grep -rn TODO src docs",
            "cp src/app.py /tmp/app.py",
            "pytest tests/characterisation 2>&1 | tail -5",
            "python3 - <<'EOF'\nopen('x') # don't parse me: > src/app.py\nEOF",
            "cat > docs/discovery/one-pager.md <<'EOF'\nIt's the old slice's job.\nEOF",
            "echo done > /dev/null",
        ]:
            with self.subTest(command=command):
                self.assertAllowed(self.shell(command))

    def test_shell_writes_to_the_legacy_slice_are_blocked(self):
        self.assertBlocked(self.shell("sed -i.bak 's/x/y/' legacy/src/Main.java"), "test oracle")
        self.assertBlocked(self.shell("git checkout -- legacy/src/Main.java"), "test oracle")

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
