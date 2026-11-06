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

| ID | User | How they use it | Priority |
|---|---|---|---|
| <a id="TRAD"></a>TRAD | Trader | Buys and sells | 1 |

| ID | State | User | Entered by | Risk |
|---|---|---|---|---|
| <a id="TRAD_IN"></a>TRAD_IN | Logged in | [TRAD](#TRAD) | Logging in | High |
| <a id="TRAD_OUT"></a>TRAD_OUT | Logged out | [TRAD](#TRAD) | Logging out | Low |

| ID | Transition | From | To |
|---|---|---|---|
| <a id="TRAD_OUT_TO_IN"></a>TRAD_OUT_TO_IN | Log in | [TRAD_OUT](#TRAD_OUT) | [TRAD_IN](#TRAD_IN) |
| <a id="TRAD_IN_TO_OUT"></a>TRAD_IN_TO_OUT | Log out | [TRAD_IN](#TRAD_IN) | [TRAD_OUT](#TRAD_OUT) |

| Journey | User | Transitions, in order |
|---|---|---|
| Log in and out | [TRAD](#TRAD) | [TRAD_OUT_TO_IN](#TRAD_OUT_TO_IN), [TRAD_IN_TO_OUT](#TRAD_IN_TO_OUT) |
"""

REQUIREMENTS = """# Requirements

| # | Question | Suggestion | Decision | Decided by |
|---|---|---|---|---|
| 1 | Is admin in scope? | No | No | Luke |

| ID | State or transition | Requirement | Test | Source | Status |
|---|---|---|---|---|---|
| <a id="TRAD_OUT_TO_IN_REQ_1"></a>TRAD_OUT_TO_IN_REQ_1 | [TRAD_OUT_TO_IN](users-states-journeys.md#TRAD_OUT_TO_IN) | Registering logs the user in | `test_register` | Old slice | Confirmed |
| <a id="TRAD_IN_REQ_1"></a>TRAD_IN_REQ_1 | [TRAD_IN](users-states-journeys.md#TRAD_IN) | Quantities are whole numbers | `test_quantity` | Fixed | Confirmed, see [KF-1](keep-or-fix.md#KF-1) |
| <a id="TRAD_IN_REQ_2"></a>TRAD_IN_REQ_2 | [TRAD_IN](users-states-journeys.md#TRAD_IN) | Rebuilding the database destroys all data | checked | Old slice | By hand: it destroys the data other tests use |

| ID | State or transition | Requirement | Measure | Baseline or target | Source | Status |
|---|---|---|---|---|---|---|
| <a id="TRAD_IN_REQ_3"></a>TRAD_IN_REQ_3 | [TRAD_IN](users-states-journeys.md#TRAD_IN) | Quotes are fast | p95 latency | 40 ms | Old slice | Confirmed |

| ID | State or transition | Requirement | Reason | Decided by |
|---|---|---|---|---|
| <a id="TRAD_IN_REQ_4"></a>TRAD_IN_REQ_4 | [TRAD_IN](users-states-journeys.md#TRAD_IN) | Admin can reset the market | Out of scope | Luke |
"""

DECISIONS = """# Keep or fix

| ID | Behaviour | Evidence | Who depends on it | Suggestion | Decision | Decided by |
|---|---|---|---|---|---|---|
| <a id="KF-1"></a>KF-1 | Fractional quantities accepted | test_quantity | Nobody | Fix | Fix | Luke |
"""

TESTS = 'req("TRAD_OUT_TO_IN_REQ_1")\nreq("TRAD_IN_REQ_1")\nreq("TRAD_IN_REQ_3")\nreq("TRAD_IN_REQ_4")\n'

USERS_FILE = "docs/discovery/users-states-journeys.md"
REQUIREMENTS_FILE = "docs/discovery/requirements.md"


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
        self.assertProblem("states with no risk: TRAD_OUT.")

    def test_no_journeys_fails(self):
        self.replace(USERS_FILE, "| Log in and out | [TRAD](#TRAD) | [TRAD_OUT_TO_IN](#TRAD_OUT_TO_IN), [TRAD_IN_TO_OUT](#TRAD_IN_TO_OUT) |\n", "")
        self.assertProblem("no journeys.")

    def test_a_missing_users_file_fails(self):
        (self.project / "docs/discovery/users-states-journeys.md").unlink()
        self.assertProblem("users-states-journeys.md is missing.")

    # 2. Requirements.
    def test_a_requirement_with_no_source_fails(self):
        self.replace("docs/discovery/requirements.md", "`test_register` | Old slice |", "`test_register` | |")
        self.assertProblem("TRAD_OUT_TO_IN_REQ_1: source is none, not old slice, fixed or design.")

    def test_a_table_with_no_source_column_fails(self):
        self.replace("docs/discovery/requirements.md", "| Test | Source | Status |", "| Test | Origin | Status |")
        self.assertProblem("a requirements table has no source column.")

    def test_a_hypothesis_fails(self):
        self.replace("docs/discovery/requirements.md", "`test_register` | Old slice | Confirmed |", "`test_register` | Old slice | Hypothesis |")
        self.assertProblem("TRAD_OUT_TO_IN_REQ_1: still a hypothesis.")

    def test_a_fixed_requirement_must_name_its_decision(self):
        self.replace("docs/discovery/requirements.md", "Confirmed, see [KF-1](keep-or-fix.md#KF-1)", "Confirmed")
        self.assertProblem("TRAD_IN_REQ_1: fixed, but names no entry in the decision log.")

    def test_a_dropped_requirement_needs_who_decided(self):
        self.replace("docs/discovery/requirements.md", "| Out of scope | Luke |", "| Out of scope | |")
        self.assertProblem("TRAD_IN_REQ_4: dropped, but doesn't say who decided.")

    # 3. Boundary tests.
    def test_an_old_slice_requirement_needs_its_test_now(self):
        self.write("tests/test_boundary.py", 'req("TRAD_IN_REQ_1")\nreq("TRAD_IN_REQ_3")\n')
        self.assertProblem("No boundary test (1): TRAD_OUT_TO_IN_REQ_1.")

    def test_trace_exempt_does_not_apply_at_the_handoff(self):
        self.write(".claude/slice-migration.json", json.dumps({"trace": {"exempt": ["_REQ_1$"]}}))
        self.write("tests/test_boundary.py", 'req("TRAD_IN_REQ_1")\nreq("TRAD_IN_REQ_3")\n')
        self.assertProblem("No boundary test (1): TRAD_OUT_TO_IN_REQ_1.")

    def test_a_fixed_requirement_test_is_due_in_execution(self):
        self.write("tests/test_boundary.py", 'req("TRAD_OUT_TO_IN_REQ_1")\nreq("TRAD_IN_REQ_3")\n')
        result = self.run_handoff()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Tests due in Execution (1, fixed or design): TRAD_IN_REQ_1.", result.stdout)

    def test_a_design_requirement_test_is_due_in_execution(self):
        self.replace("docs/discovery/requirements.md", "`test_register` | Old slice |", "`test_register` | Design |")
        self.write("tests/test_boundary.py", 'req("TRAD_IN_REQ_3")\n')
        result = self.run_handoff()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Tests due in Execution (2, fixed or design): TRAD_IN_REQ_1, TRAD_OUT_TO_IN_REQ_1.", result.stdout)

    def test_a_test_due_in_execution_still_needs_a_test_method(self):
        self.replace("docs/discovery/requirements.md", "| `test_quantity` | Fixed |", "| | Fixed |")
        self.write("tests/test_boundary.py", 'req("TRAD_OUT_TO_IN_REQ_1")\nreq("TRAD_IN_REQ_3")\n')
        self.assertProblem("TRAD_IN_REQ_1: no test method.")

    def test_a_tag_for_an_unknown_requirement_fails(self):
        self.write("tests/test_boundary.py", TESTS + 'req("TRAD_IN_REQ_7")\n')
        self.assertProblem("Unknown requirement TRAD_IN_REQ_7, tagged in: tests/test_boundary.py.")

    # 4. Numbers for non-functional requirements.
    def test_a_measure_with_no_baseline_or_target_fails(self):
        self.replace("docs/discovery/requirements.md", "| p95 latency | 40 ms |", "| p95 latency | TBD |")
        self.assertProblem("TRAD_IN_REQ_3: a measure, but no baseline or target.")

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
        self.replace(REQUIREMENTS_FILE, "keep-or-fix.md#KF-1", "assumptions.md#KF-1")
        self.write(".claude/slice-migration.json", json.dumps({"handoff": {"decisions": ["docs/discovery/assumptions.md"]}}))
        self.assertEqual(self.run_handoff().returncode, 0)

    def test_no_decision_log_fails(self):
        (self.project / "docs/discovery/keep-or-fix.md").unlink()
        self.assertProblem("No decision log")

    # IDs and links.
    def test_a_state_name_of_several_words_uses_hyphens(self):
        for rel in (USERS_FILE, REQUIREMENTS_FILE):
            path = self.project / rel
            path.write_text(path.read_text().replace("TRAD_IN", "TRAD_READY-TO-SHIP").replace("_TO_IN", "_TO_READY-TO-SHIP"))
        self.write("tests/test_boundary.py", TESTS.replace("TRAD_IN", "TRAD_READY-TO-SHIP").replace("_TO_IN", "_TO_READY-TO-SHIP"))
        result = self.run_handoff()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_indexes_are_allowed_on_every_kind_of_id(self):
        def indexed(text):
            text = text.replace("TRAD_IN_TO_OUT", "@1").replace("TRAD_OUT_TO_IN", "@2")
            text = text.replace("TRAD_IN", "TRAD_IN_1").replace("TRAD_OUT", "TRAD_OUT_2")
            return text.replace("@1", "TRAD_IN_1_TO_OUT_2_3").replace("@2", "TRAD_OUT_2_TO_IN_1")

        self.write(USERS_FILE, indexed(USERS))
        self.write(REQUIREMENTS_FILE, indexed(REQUIREMENTS))
        self.write("tests/test_boundary.py", indexed(TESTS))
        result = self.run_handoff()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_an_old_style_requirement_id_fails(self):
        self.replace(REQUIREMENTS_FILE, 'id="TRAD_OUT_TO_IN_REQ_1"></a>TRAD_OUT_TO_IN_REQ_1', 'id="AUTH-1"></a>AUTH-1')
        self.assertProblem("AUTH-1: not a valid requirement ID.")

    def test_a_badly_formed_state_id_fails(self):
        self.replace(USERS_FILE, "</a>TRAD_OUT |", "</a>TRAD_LOGGED_OUT |")
        self.assertProblem("TRAD_LOGGED_OUT: not a valid state ID.")

    def test_a_reserved_word_cannot_be_a_state_name(self):
        self.replace(USERS_FILE, "</a>TRAD_OUT |", "</a>TRAD_TO |")
        self.assertProblem("TRAD_TO: not a valid state ID.")

    def test_a_user_id_of_the_wrong_length_fails(self):
        self.replace(USERS_FILE, "</a>TRAD |", "</a>TRADERS |")
        self.assertProblem("TRADERS: not a valid user ID.")

    def test_a_definition_with_no_anchor_fails(self):
        self.replace(USERS_FILE, '<a id="TRAD_OUT"></a>TRAD_OUT |', "TRAD_OUT |")
        self.assertProblem("TRAD_OUT: no anchor for links to reach it.")

    def test_a_duplicate_id_fails(self):
        self.replace(REQUIREMENTS_FILE, '<a id="TRAD_IN_REQ_2"></a>TRAD_IN_REQ_2', '<a id="TRAD_IN_REQ_1"></a>TRAD_IN_REQ_1')
        self.assertProblem("TRAD_IN_REQ_1: used as an ID 2 times.")

    def test_a_state_must_link_back_to_its_user(self):
        self.replace(USERS_FILE, "| Logged out | [TRAD](#TRAD) |", "| Logged out | TRAD |")
        self.assertProblem("TRAD_OUT: needs one link back to its user, and has 0.")

    def test_a_transition_must_link_back_to_both_states(self):
        self.replace(USERS_FILE, "| Log in | [TRAD_OUT](#TRAD_OUT) | [TRAD_IN](#TRAD_IN) |", "| Log in | [TRAD_OUT](#TRAD_OUT) | TRAD_IN |")
        self.assertProblem("TRAD_OUT_TO_IN: needs one link back to the state it enters, and has 0.")

    def test_a_transition_linking_to_the_wrong_state_fails(self):
        self.replace(USERS_FILE, "| Log in | [TRAD_OUT](#TRAD_OUT) | [TRAD_IN](#TRAD_IN) |", "| Log in | [TRAD_IN](#TRAD_IN) | [TRAD_OUT](#TRAD_OUT) |")
        result = self.run_handoff()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("TRAD_OUT_TO_IN: links back to TRAD_IN as the state it leaves", result.stdout)
        self.assertIn("TRAD_OUT_TO_IN: links back to TRAD_OUT as the state it enters", result.stdout)

    def test_a_requirement_must_link_back(self):
        self.replace(REQUIREMENTS_FILE, "| [TRAD_OUT_TO_IN](users-states-journeys.md#TRAD_OUT_TO_IN) |", "| TRAD_OUT_TO_IN |")
        self.assertProblem("TRAD_OUT_TO_IN_REQ_1: needs one link back to its state or transition, and has 0.")

    def test_a_requirement_linking_to_the_wrong_parent_fails(self):
        self.replace(REQUIREMENTS_FILE, "| [TRAD_OUT_TO_IN](users-states-journeys.md#TRAD_OUT_TO_IN) |", "| [TRAD_IN](users-states-journeys.md#TRAD_IN) |")
        self.assertProblem("TRAD_OUT_TO_IN_REQ_1: links back to TRAD_IN, but its ID says TRAD_OUT_TO_IN.")

    def test_a_requirement_with_no_such_parent_fails(self):
        self.replace(REQUIREMENTS_FILE, '<a id="TRAD_IN_REQ_2"></a>TRAD_IN_REQ_2 | [TRAD_IN](users-states-journeys.md#TRAD_IN)', '<a id="TRAD_GONE_REQ_2"></a>TRAD_GONE_REQ_2 | [TRAD_GONE](users-states-journeys.md#TRAD_GONE)')
        result = self.run_handoff()
        self.assertIn("TRAD_GONE_REQ_2: TRAD_GONE isn't in the states or transitions tables.", result.stdout)
        self.assertIn("the link to users-states-journeys.md#TRAD_GONE goes nowhere.", result.stdout)

    def test_a_non_functional_requirement_needs_a_state_or_transition(self):
        self.replace(REQUIREMENTS_FILE, "| ID | State or transition | Requirement | Measure |", "| ID | Parent | Requirement | Measure |")
        self.assertProblem("a requirements table has no state or transition column.")

    def test_a_dropped_requirement_links_back_too(self):
        self.replace(REQUIREMENTS_FILE, "| [TRAD_IN](users-states-journeys.md#TRAD_IN) | Admin can", "| TRAD_IN | Admin can")
        self.assertProblem("TRAD_IN_REQ_4: needs one link back to its state or transition, and has 0.")

    def test_a_dangling_link_fails(self):
        self.replace(REQUIREMENTS_FILE, "[KF-1](keep-or-fix.md#KF-1)", "[KF-1](keep-or-fix.md#KF-2), KF-1")
        self.assertProblem("the link to keep-or-fix.md#KF-2 goes nowhere.")

    def test_a_link_shown_as_code_is_not_checked(self):
        self.replace(REQUIREMENTS_FILE, "# Requirements\n", "# Requirements\n\nFor example `[X](#Y)`.\n\n```\n[X](#Y)\n```\n")
        self.assertEqual(self.run_handoff().returncode, 0)

    def test_no_transitions_fails(self):
        self.write(USERS_FILE, USERS.split("| ID | Transition |")[0] + USERS[USERS.index("| Journey |"):])
        self.assertProblem("no transitions.")

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
