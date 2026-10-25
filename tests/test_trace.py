"""Tests for scripts/trace.py, run as a person or CI would run it."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TRACE = Path(__file__).resolve().parent.parent / "scripts" / "trace.py"

REQUIREMENTS = """# Requirements

| ID | Requirement | Test | Status |
|---|---|---|---|
| AUTH-1 | Registering logs the user in | `test_register` | Confirmed |
| **AUTH-2** | A wrong password doesn't log in | `test_wrong_password` | Corrected |
| ADMIN-4 | Rebuilding the database destroys all data | checked | By hand: it destroys the data other tests use |
| MONEY-1N | Money is exact decimal | Planned | Planned |

| Feature | Requirements |
|---|---|
| Register | AUTH-1 |
"""


class TraceTest(unittest.TestCase):
    def setUp(self):
        self.project = Path(tempfile.mkdtemp())
        (self.project / "docs" / "discovery").mkdir(parents=True)
        (self.project / "docs" / "discovery" / "requirements.md").write_text(REQUIREMENTS)
        (self.project / "tests").mkdir()

    def tearDown(self):
        shutil.rmtree(self.project)

    def write_test(self, name, text):
        (self.project / "tests" / name).write_text(text)

    def config(self, trace):
        (self.project / ".claude").mkdir(exist_ok=True)
        (self.project / ".claude" / "slice-migration.json").write_text(json.dumps({"trace": trace}))

    def run_trace(self):
        return subprocess.run([sys.executable, str(TRACE), str(self.project)], capture_output=True, text=True)

    def test_untested_requirements_fail(self):
        self.write_test("test_auth.py", '@pytest.mark.req("AUTH-1")\ndef test_register(): ...\n')
        result = self.run_trace()
        self.assertEqual(result.returncode, 1)
        self.assertIn("No test (2): AUTH-2, MONEY-1N", result.stdout)
        self.assertIn("4 requirements", result.stdout)

    def test_every_requirement_traced_passes(self):
        self.write_test("test_auth.py", '@pytest.mark.req("AUTH-1", "AUTH-2")\ndef test_both(): ...\n')
        self.write_test("money.test.ts", "it('rounds half up', () => { req('MONEY-1N') })\n")
        result = self.run_trace()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Checked by hand (1): ADMIN-4", result.stdout)

    def test_tags_for_unknown_requirements_fail(self):
        self.write_test("test_auth.py", 'req("AUTH-1")\nreq("AUTH-2")\nreq("MONEY-1N")\nreq("AUTH-9")\n')
        result = self.run_trace()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Unknown requirement AUTH-9, tagged in: tests/test_auth.py", result.stdout)

    def test_exempt_patterns_are_listed_not_failed(self):
        self.config({"exempt": ["N$"]})
        self.write_test("test_auth.py", 'req("AUTH-1")\nreq("AUTH-2")\n')
        result = self.run_trace()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Exempt (1, by trace.exempt): MONEY-1N", result.stdout)

    def test_paths_and_tag_come_from_the_config(self):
        self.config({"tests": ["spec"], "tag": r"@req:([\w-]+)"})
        (self.project / "spec").mkdir()
        (self.project / "spec" / "auth.feature").write_text("@req:AUTH-1 @req:AUTH-2 @req:MONEY-1N\nScenario: x\n")
        self.write_test("test_ignored.py", 'req("AUTH-9")\n')
        result = self.run_trace()
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_a_missing_requirements_file_is_an_error(self):
        (self.project / "docs" / "discovery" / "requirements.md").unlink()
        self.assertEqual(self.run_trace().returncode, 2)


if __name__ == "__main__":
    unittest.main()
