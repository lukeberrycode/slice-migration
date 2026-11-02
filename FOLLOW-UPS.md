# Follow-ups

Points found on 2026-11-02 during a review of this repository (at `21a18bcd`) for the `lukeberrycode-help` notes. Each one says what was found, why it matters, and what to do. Delete an entry once it's dealt with, and this file once it's empty.

## 1. Clean up test folders with `addCleanup()`, not `tearDown()`

**Found:** `tests/test_gate.py` (`GateHookTest`) and `tests/test_trace.py` (`TraceTest`) both create a temporary project in `setUp()` with `tempfile.mkdtemp()`, then keep building it (`mkdir`, `shutil.copy` of the config, `write_text` of the requirements). They delete it in `tearDown()` with `shutil.rmtree(self.project)`.

**Why it matters:** unittest only calls `tearDown()` if `setUp()` succeeded. If anything in `setUp()` fails after `mkdtemp()` (a missing template, a renamed config file), the test is reported as an error and the temporary folder is never deleted. Cleanups registered with `addCleanup()` run even when `setUp()` fails.

- `tearDown`: https://docs.python.org/3.12/library/unittest.html#unittest.TestCase.tearDown ("If `setUp()` succeeded, `tearDown()` will be run")
- `addCleanup`: https://docs.python.org/3.12/library/unittest.html#unittest.TestCase.addCleanup ("If `setUp()` fails, meaning that `tearDown()` is not called, then any cleanup functions added will still be called.")

**What to do:** in both classes, register the clean-up straight after the folder exists, and delete the `tearDown()` methods:

```python
def setUp(self):
    self.project = Path(tempfile.mkdtemp())
    self.addCleanup(shutil.rmtree, self.project)
    ...  # the rest of setUp unchanged
```

Then run `python3 -m unittest discover -v -s tests`; all 28 tests (18 + 8 + 2) should still pass.

## 2. Pin the CI runner image instead of `ubuntu-latest`

**Found:** `.github/workflows/test.yml` has `runs-on: ubuntu-latest` and runs `python3 -m unittest discover -v -s tests` with the runner image's own `python3` (there's no `setup-python` step). The checkout action is already pinned to a commit SHA (`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`), so the runner is the one unpinned part. Every branch on GitHub has the same setting as of 2026-11-02.

**Why it matters:** `ubuntu-latest` is a moving label. When GitHub points it at a newer Ubuntu image, the system Python version changes with it, and a test can start failing (or, worse, start passing for a different reason) with no change in this repository. A pinned label such as `ubuntu-24.04` changes only when you change it. daytrader-to-python's `ci.yml` already uses `ubuntu-24.04` with the same pinned checkout.

- GitHub-hosted runner labels: https://docs.github.com/en/actions/reference/runners/github-hosted-runners#supported-runners-and-hardware-resources

**What to do:**

1. Change `runs-on: ubuntu-latest` to `runs-on: ubuntu-24.04` in `.github/workflows/test.yml`.
2. Optionally also pin Python with `actions/setup-python`, pinned to a commit SHA like the checkout step, if the plugin should be tested against a particular version (Claude Code runs the hook with whatever `python3` the user has).
3. Push and check the Test workflow passes.

**Background:** the `lukeberrycode-help` notes `unittest/what-is-unittest.md` ("In slice-migration") and `github-actions/what-is-github-actions.md` ("Pinning actions and runners") explain both points.
