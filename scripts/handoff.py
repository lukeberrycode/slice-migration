#!/usr/bin/env python3
"""Handoff check: does Discovery's output meet the Discovery handoff in method.md?

Delivery starts from the handoff and from nothing else, so this checks only what
the handoff names, whatever source the requirements came from:

1. Users, states and journeys, with a risk for every state.
2. Requirements, each with an ID, a state or transition, the requirement, a test
   method and a source (old slice, fixed or design). None still a hypothesis.
   A fixed requirement names its keep-or-fix entry. Dropped requirements have a
   reason and who decided.
3. A boundary test for every requirement, by the trace check's tags, or "By
   hand". Unlike the trace check, `trace.exempt` doesn't apply: at the handoff
   every requirement has its test, even one that fails until Execution.
4. A baseline or target for every non-functional requirement with a measure.
5. A decision for every row of the decision log, and who made it.
6. The Discovery gate, approved by a person in the gates file.

When there's an old slice to replace (`legacy_path` exists), it also checks the
replacement inputs: the architecture, the data inventory and the
characterisation tests.

Usage: handoff.py [--before-sign-off] [project dir]. --before-sign-off skips
item 6, for checking the handoff before a person decides the gate. Exit 0 if the
handoff is complete, 1 if not, 2 if the config or requirements can't be read.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

# Load the trace check by path: a plain `import trace` would find the standard library's.
_spec = importlib.util.spec_from_file_location("slice_trace", Path(__file__).resolve().parent / "trace.py")
trace = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trace)
CONFIG, ID = trace.CONFIG, trace.ID

DEFAULTS = {
    "users": "docs/discovery/users-states-journeys.md",
    "decisions": ["docs/discovery/keep-or-fix.md"],
    "architecture": "docs/discovery/architecture.md",
    "data_inventory": "docs/discovery/data-inventory.md",
    "characterisation": "tests/characterisation",
}
SOURCES = {"old slice", "fixed", "design"}
EMPTY = {"", "-", "–", "—", "tbd", "todo", "?"}


def tables(path: Path) -> list:
    """Every Markdown table in the file, as {"header": [...], "rows": [{column: cell}]}.

    Column names are lower case. The header is kept so that a missing column can
    be told apart from an empty table.
    """
    found, block = [], []
    for line in path.read_text(encoding="utf-8").splitlines() + [""]:
        if line.lstrip().startswith("|"):
            block.append([c.strip() for c in line.strip().strip("|").split("|")])
            continue
        if len(block) >= 2:
            header = [h.strip("*` ").lower() for h in block[0]]
            rows = [dict(zip(header, cells)) for cells in block[2:]]
            found.append({"header": header, "rows": rows})
        block = []
    return found


def cell(row: dict, *names) -> str:
    """The first of the named columns the row has, stripped of Markdown emphasis."""
    for name in names:
        if name in row:
            return row[name].strip("*_` ")
    return ""


def filled(text: str) -> bool:
    return text.strip().lower() not in EMPTY


def has(table: dict, *columns) -> bool:
    return all(c in table["header"] for c in columns)


class Handoff:
    def __init__(self, project: Path):
        self.project = project
        self.problems = []
        config = {}
        if (project / CONFIG).is_file():
            config = json.loads((project / CONFIG).read_text(encoding="utf-8"))
        self.config = config
        self.trace = trace.settings(project)
        self.dropped = set()
        self.paths = {**DEFAULTS, **config.get("handoff", {})}

    def problem(self, text: str):
        self.problems.append(text)

    def read(self, rel: str):
        """The file's tables, or None (and a problem) if it isn't there."""
        path = self.project / rel
        if not path.is_file():
            self.problem(f"{rel} is missing.")
            return None
        return tables(path)

    def users(self):
        found = self.read(self.paths["users"])
        if found is None:
            return
        rel = self.paths["users"]
        users = [t for t in found if has(t, "user")]
        states = [t for t in found if has(t, "state") and not has(t, "user")]
        journeys = [t for t in found if has(t, "journey")]
        if not any(t["rows"] for t in users):
            self.problem(f"{rel}: no users.")
        if not any(t["rows"] for t in journeys):
            self.problem(f"{rel}: no journeys.")
        rows = [r for t in states for r in t["rows"]]
        if not rows:
            self.problem(f"{rel}: no states.")
        if states and not all(has(t, "risk") for t in states):
            self.problem(f"{rel}: the states table has no Risk column.")
        unranked = [cell(r, "id") or cell(r, "state") for r in rows if not filled(cell(r, "risk"))]
        if unranked and all(has(t, "risk") for t in states):
            self.problem(f"{rel}: states with no risk: {', '.join(unranked)}.")

    def decisions(self) -> set:
        """Check the decision log, and return its entry IDs."""
        ids = set()
        logs = [rel for rel in self.paths["decisions"] if (self.project / rel).is_file()]
        if not logs:
            self.problem(f"No decision log: none of {', '.join(self.paths['decisions'])} exists.")
        # Scope decisions in the requirements file are decisions too.
        if (self.project / self.trace["requirements"]).is_file():
            logs.append(self.trace["requirements"])
        for rel in logs:
            for table in tables(self.project / rel):
                if not has(table, "decision"):
                    continue
                if not has(table, "decided by"):
                    self.problem(f"{rel}: a table of decisions has no Decided by column.")
                for row in table["rows"]:
                    name = cell(row, "id", "#", "question", "behaviour") or "a row"
                    if ID.fullmatch(cell(row, "id")):
                        ids.add(cell(row, "id"))
                    if not filled(cell(row, "decision")):
                        self.problem(f"{rel}: {name} has no decision.")
                    elif has(table, "decided by") and not filled(cell(row, "decided by")):
                        self.problem(f"{rel}: {name} doesn't say who decided.")
        return ids

    def requirements(self, decision_ids: set) -> dict:
        """Check the requirements, and return ID -> row text for those not dropped."""
        rel = self.trace["requirements"]
        path = self.project / rel
        found = tables(path)  # Raises if it can't be read: main() reports it.
        functional = [t for t in found if has(t, "id", "requirement", "test")]
        nonfunctional = [t for t in found if has(t, "id", "requirement", "measure")]
        dropped = [t for t in found if has(t, "id", "reason")]
        if not any(t["rows"] for t in functional):
            self.problem(f"{rel}: no requirements.")

        for table, needed in [(t, ["state or transition", "source"]) for t in functional] + [
            (t, ["source"]) for t in nonfunctional
        ]:
            missing = [c for c in needed if c not in table["header"]]
            if missing:
                self.problem(f"{rel}: a requirements table has no {' or '.join(missing)} column.")
        for table in nonfunctional:
            if not any(c in table["header"] for c in ("baseline or target", "baseline", "target")):
                self.problem(f"{rel}: the non-functional requirements table has no Baseline or target column.")

        reqs = {}
        for table in functional + nonfunctional:
            for row in table["rows"]:
                req = cell(row, "id")
                if not ID.fullmatch(req):
                    continue
                text = " | ".join(row.values())
                reqs[req] = text
                if not filled(cell(row, "requirement")):
                    self.problem(f"{req}: no requirement.")
                if "state or transition" in table["header"] and not filled(cell(row, "state or transition")):
                    self.problem(f"{req}: no state or transition.")
                if "test" in table["header"] and not filled(cell(row, "test")):
                    self.problem(f"{req}: no test method.")
                if cell(row, "status").lower().startswith("hypothesis"):
                    self.problem(f"{req}: still a hypothesis.")
                source = cell(row, "source").lower()
                if "source" in table["header"] and source not in SOURCES:
                    shown = f'"{cell(row, "source")}"' if source else "none"
                    self.problem(f"{req}: source is {shown}, not old slice, fixed or design.")
                if source == "fixed" and not decision_ids & set(ID.findall(text)):
                    self.problem(f"{req}: fixed, but names no entry in the decision log.")
                if table in nonfunctional and filled(cell(row, "measure")):
                    if not filled(cell(row, "baseline or target", "baseline", "target")):
                        self.problem(f"{req}: a measure, but no baseline or target.")

        for table in dropped:
            for row in table["rows"]:
                req = cell(row, "id")
                if not ID.fullmatch(req):
                    continue
                reqs.pop(req, None)
                self.dropped.add(req)
                if not filled(cell(row, "reason")):
                    self.problem(f"{req}: dropped with no reason.")
                if not filled(cell(row, "decided by")):
                    self.problem(f"{req}: dropped, but doesn't say who decided.")
        return reqs

    def tests(self, reqs: dict):
        tagged = trace.tags(self.project, self.trace["tests"], self.trace["tag"])
        untested = sorted(r for r in reqs if r not in tagged and not re.search(r"by hand", reqs[r], re.I))
        if untested:
            self.problem(f"No boundary test ({len(untested)}): {', '.join(untested)}.")
        for req in sorted(r for r in tagged if r not in reqs and r not in self.dropped):
            self.problem(f"Unknown requirement {req}, tagged in: {', '.join(sorted(tagged[req]))}.")
        return tagged

    def replacing(self) -> bool:
        legacy = (self.config.get("legacy_path") or "").strip("/")
        return bool(legacy) and (self.project / legacy).exists()

    def replacement(self):
        for key in ("architecture", "data_inventory"):
            found = self.read(self.paths[key])
            if found is not None and not any(t["rows"] for t in found):
                self.problem(f"{self.paths[key]}: no table has a row yet.")
        folder = self.project / self.paths["characterisation"]
        if not folder.is_dir() or not any(f.is_file() for f in folder.rglob("*")):
            self.problem(f"{self.paths['characterisation']}: no characterisation tests.")

    def signed_off(self) -> bool:
        gates_file = self.config.get("gates_file", "docs/gates.json")
        try:
            gates = json.loads((self.project / gates_file).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            gates = {}
        entry = gates.get("discovery")
        return isinstance(entry, dict) and bool(entry.get("approved_by")) and bool(entry.get("date"))


def main() -> int:
    args = sys.argv[1:]
    before_sign_off = "--before-sign-off" in args
    args = [a for a in args if a != "--before-sign-off"]
    project = Path(args[0] if args else ".").resolve()
    try:
        check = Handoff(project)
        reqs = check.requirements(check.decisions())
    except (OSError, ValueError) as e:
        print(f"Can't read the config or the requirements: {e}", file=sys.stderr)
        return 2
    check.users()
    tagged = check.tests(reqs)
    replacing = check.replacing()
    if replacing:
        check.replacement()
    signed = check.signed_off()
    if not signed and not before_sign_off:
        check.problem("The Discovery gate isn't approved. Only a person approves it, in the gates file.")

    traced = sum(1 for r in reqs if r in tagged)
    print(f"{len(reqs)} requirements; {traced} traced to tests.")
    print(f"Replacing an old slice: {'yes' if replacing else 'no'}.")
    print(f"Sign-off: {'approved' if signed else 'waiting on a person'}.")
    if check.problems:
        print(f"The handoff isn't complete ({len(check.problems)}):")
        for problem in check.problems:
            print(f"- {problem}")
        return 1
    print("The handoff is complete." if not before_sign_off or signed else "The handoff is ready for sign-off.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
