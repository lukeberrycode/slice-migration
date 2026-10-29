"""Tests for scripts/handoff.py, run as a person or CI would run it."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HANDOFF = Path(__file__).resolve().parent.parent / "scripts" / "handoff.py"

USERS = """# Users, states and journeys

| User | How they use it | Priority |
|---|---|---|
| Trader | Buys and sells | 1 |

| ID | State | Entered by | Risk |
|---|---|---|---|
| S1 | Logged in | Logging in | High |
| S2 | Logged out | Logging out | Low |

| Journey | States, in order | Requirements on the transitions |
|---|---|---|
| Log in and out | S2, S1, S2 | AUTH-1 |
"""

REQUIREMENTS = """# Requirements

| # | Question | Suggestion | Decision | Decided by |
|---|---|---|---|---|
| 1 | Is admin in scope? | No | No | Luke |

| ID | State or transition | Requirement | Test | Source | Status |
|---|---|---|---|---|---|
| AUTH-1 | S2 to S1 | Registering logs the user in | `test_register` | Old slice | Confirmed |
| AUTH-2N | S1 | Quantities are whole numbers | `test_quantity` | Fixed | Confirmed, see KF-1 |
| ADMIN-4 | S1 | Rebuilding the database destroys all data | checked | Old slice | By hand: it destroys the data other tests use |

| ID | Requirement | Measure | Baseline or target | Source | Status |
|---|---|---|---|---|---|
| PERF-1 | Quotes are fast | p95 latency | 40 ms | Old slice | Confirmed |

| ID | Requirement | Reason | Decided by |
|---|---|---|---|
| ADMIN-9 | Admin can reset the market | Out of scope | Luke |
"""

DECISIONS = """# Keep or fix

| ID | Behaviour | Evidence | Who depends on it | Suggestion | Decision | Decided by |
|---|---|---|---|---|---|---|
| KF-1 | Fractional quantities accepted | test_quantity | Nobody | Fix | Fix | Luke |
"""

TESTS = 'req("AUTH-1")\nreq("AUTH-2N")\nreq("PERF-1")\nreq("ADMIN-9")\n'


class HandoffTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp())
        self.write("docs/discovery/users-states-journeys.md", USERS)
        self.write("docs/discovery/requirements.md", REQUIREMENTS)
        self.write("docs/discovery/keep-or-fix.md", DECISIONS)
        self.write("tests/test_boundary.py", TESTS)
        self.write("docs/gates.json", json.dumps({"discovery": {"approved_by": "Luke", "date": "2026-10-29"}}))

    def tearDown(self):
        shutil.rmtree(self.project)

    def write(self, rel, text):
        path = self.project / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def replace(self, rel, old, new):
        path = self.project / rel
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new))

    def run_handoff(self, *flags):
        return subprocess.run(
            [sys.executable, str(HANDOFF), *flags, str(self.project)], capture_output=True, text=True
        )

    def assertProblem(self, text, *flags):
        result = self.run_handoff(*flags)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(text, result.stdout)

    def test_a_complete_handoff_passes(self):
        result = self.run_handoff()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("4 requirements; 3 traced to tests.", result.stdout)
        self.assertIn("Replacing an old slice: no.", result.stdout)
        self.assertIn("The handoff is complete.", result.stdout)

    def test_a_design_source_passes_the_same_way(self):
        self.replace("docs/discovery/requirements.md", "| Old slice |", "| Design |")
        self.assertEqual(self.run_handoff().returncode, 0)

    # 1. Users, states and journeys.
    def test_a_state_with_no_risk_fails(self):
        self.replace("docs/discovery/users-states-journeys.md", "| Logging out | Low |", "| Logging out | |")
        self.assertProblem("states with no risk: S2.")

    def test_no_journeys_fails(self):
        self.replace("docs/discovery/users-states-journeys.md", "| Log in and out | S2, S1, S2 | AUTH-1 |\n", "")
        self.assertProblem("no journeys.")

    def test_a_missing_users_file_fails(self):
        (self.project / "docs/discovery/users-states-journeys.md").unlink()
        self.assertProblem("users-states-journeys.md is missing.")

    # 2. Requirements.
    def test_a_requirement_with_no_source_fails(self):
        self.replace("docs/discovery/requirements.md", "`test_register` | Old slice |", "`test_register` | |")
        self.assertProblem("AUTH-1: source is none, not old slice, fixed or design.")

    def test_a_table_with_no_source_column_fails(self):
        self.replace("docs/discovery/requirements.md", "| Test | Source | Status |", "| Test | Origin | Status |")
        self.assertProblem("a requirements table has no source column.")

    def test_a_hypothesis_fails(self):
        self.replace("docs/discovery/requirements.md", "| Old slice | Confirmed |\n| AUTH-2N", "| Old slice | Hypothesis |\n| AUTH-2N")
        self.assertProblem("AUTH-1: still a hypothesis.")

    def test_a_fixed_requirement_must_name_its_decision(self):
        self.replace("docs/discovery/requirements.md", "Confirmed, see KF-1", "Confirmed")
        self.assertProblem("AUTH-2N: fixed, but names no entry in the decision log.")

    def test_a_dropped_requirement_needs_who_decided(self):
        self.replace("docs/discovery/requirements.md", "| Out of scope | Luke |", "| Out of scope | |")
        self.assertProblem("ADMIN-9: dropped, but doesn't say who decided.")

    # 3. Boundary tests.
    def test_trace_exempt_does_not_apply_at_the_handoff(self):
        self.write(".claude/slice-migration.json", json.dumps({"trace": {"exempt": ["N$"]}}))
        self.write("tests/test_boundary.py", 'req("AUTH-1")\nreq("PERF-1")\n')
        self.assertProblem("No boundary test (1): AUTH-2N.")

    def test_a_tag_for_an_unknown_requirement_fails(self):
        self.write("tests/test_boundary.py", TESTS + 'req("AUTH-7")\n')
        self.assertProblem("Unknown requirement AUTH-7, tagged in: tests/test_boundary.py.")

    # 4. Numbers for non-functional requirements.
    def test_a_measure_with_no_baseline_or_target_fails(self):
        self.replace("docs/discovery/requirements.md", "| p95 latency | 40 ms |", "| p95 latency | TBD |")
        self.assertProblem("PERF-1: a measure, but no baseline or target.")

    # 5. The decision log.
    def test_an_undecided_entry_fails(self):
        self.replace("docs/discovery/keep-or-fix.md", "| Fix | Fix | Luke |", "| Fix | | |")
        self.assertProblem("keep-or-fix.md: KF-1 has no decision.")

    def test_a_decision_must_say_who_made_it(self):
        self.replace("docs/discovery/keep-or-fix.md", "| Fix | Fix | Luke |", "| Fix | Fix | |")
        self.assertProblem("keep-or-fix.md: KF-1 doesn't say who decided.")

    def test_scope_decisions_count_too(self):
        self.replace("docs/discovery/requirements.md", "| No | No | Luke |", "| No | | |")
        self.assertProblem("requirements.md: 1 has no decision.")

    def test_a_decision_log_from_the_config(self):
        (self.project / "docs/discovery/keep-or-fix.md").unlink()
        self.write("docs/discovery/assumptions.md", DECISIONS.replace("Keep or fix", "Assumptions"))
        self.write(".claude/slice-migration.json", json.dumps({"handoff": {"decisions": ["docs/discovery/assumptions.md"]}}))
        self.assertEqual(self.run_handoff().returncode, 0)

    def test_no_decision_log_fails(self):
        (self.project / "docs/discovery/keep-or-fix.md").unlink()
        self.assertProblem("No decision log")

    # 6. Sign-off.
    def test_no_sign_off_fails(self):
        (self.project / "docs/gates.json").unlink()
        self.assertProblem("The Discovery gate isn't approved.")

    def test_before_sign_off_skips_it(self):
        (self.project / "docs/gates.json").unlink()
        result = self.run_handoff("--before-sign-off")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Sign-off: waiting on a person.", result.stdout)
        self.assertIn("The handoff is ready for sign-off.", result.stdout)

    # Replacement inputs.
    def test_replacing_needs_the_replacement_inputs(self):
        self.write(".claude/slice-migration.json", json.dumps({"legacy_path": "legacy"}))
        self.write("legacy/Main.java", "public class Main {}\n")
        result = self.run_handoff()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Replacing an old slice: yes.", result.stdout)
        self.assertIn("architecture.md is missing.", result.stdout)
        self.assertIn("tests/characterisation: no characterisation tests.", result.stdout)

        self.write("docs/discovery/architecture.md", "| Project | Runtime |\n|---|---|\n| web | Java |\n")
        self.write("docs/discovery/data-inventory.md", "| Store | Holds |\n|---|---|\n| orders | Orders |\n")
        self.write("tests/characterisation/test_old.py", "")
        self.assertEqual(self.run_handoff().returncode, 0, self.run_handoff().stdout)

    def test_a_missing_requirements_file_is_an_error(self):
        (self.project / "docs/discovery/requirements.md").unlink()
        self.assertEqual(self.run_handoff().returncode, 2)

    def test_the_templates_have_the_columns_the_handoff_needs(self):
        templates = Path(__file__).resolve().parent.parent / "templates" / "discovery"
        result = self.run_handoff()  # Sanity: the fixture passes before the templates replace it.
        self.assertEqual(result.returncode, 0)
        for name in ("requirements.md", "keep-or-fix.md", "users-states-journeys.md"):
            shutil.copy(templates / name, self.project / "docs" / "discovery" / name)
        out = self.run_handoff().stdout
        self.assertNotIn("column", out)


if __name__ == "__main__":
    unittest.main()
