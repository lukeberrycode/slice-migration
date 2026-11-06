#!/usr/bin/env python3
"""Handoff check: does Discovery's output meet the Discovery handoff in method.md?

Delivery starts from the handoff and from nothing else, so this checks only what
the handoff names, whatever source the requirements came from:

1. Users, states, transitions and journeys, with a risk for every state.
2. Requirements, each with an ID, a state or transition, the requirement, a test
   method and a source (old slice, fixed or design). None still a hypothesis.
   A fixed requirement names its keep-or-fix entry. Dropped requirements have a
   reason and who decided.
3. A boundary test for every old-slice requirement, by the trace check's tags,
   or "By hand". A fixed or design requirement has a test method instead, and
   is listed as having its test due in Execution: nothing can pass it yet.
   Unlike the trace check, `trace.exempt` doesn't apply: whether a test is due
   now depends on the requirement's source, not on its ID.
4. A baseline or target for every non-functional requirement with a measure.
5. A decision for every row of the decision log, and who made it.
6. The Discovery gate, approved by a person in the gates file.

It also checks "IDs and links" in method.md, on which review of the above relies:
every user, state, transition and requirement has a well-formed, unique ID and an
anchor, and links back to the definitions it depends on, and every link in these
files leads to an anchor or a heading. Older IDs such as AUTH-1 don't pass here, though the trace
check still reads them.

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
from collections import Counter
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

USER_ID = re.compile(trace.USER)
STATE_ID = re.compile(rf"({trace.USER})_({trace.NAME}{trace.INDEX})")
TO_STATE = re.compile(rf"{trace.NAME}{trace.INDEX}{trace.INDEX}")
REQUIREMENT_ID = re.compile(rf"(.+)_REQ{trace.INDEX}")
RESERVED = {"TO", "REQ"}  # Mark the parts of an ID, so they can't be a whole state name.
INLINE_CODE = re.compile(r"`[^`]*`")
LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]*)#([^)\s]+)\)")
ANCHOR_ID = re.compile(r'<a\s+id="([^"]+)"\s*>\s*</a>')
HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$", re.M)
# Inline code, an HTML tag, a link or image, or underscore emphasis: what a heading renders as.
HEADING_MARKUP = re.compile(r"`([^`]*)`|<[^>]+>|!?\[([^\]]*)\]\([^)]*\)|(?<!\w)_+(.+?)_+(?!\w)")


def valid_state(text: str) -> bool:
    return bool(STATE_ID.fullmatch(text)) and not RESERVED & set(text.split("_"))


def valid_transition(text: str) -> bool:
    parts = text.split("_TO_")
    return (
        len(parts) == 2
        and valid_state(parts[0])
        and bool(TO_STATE.fullmatch(parts[1]))
        and not RESERVED & set(parts[1].split("_"))
    )


def valid_requirement(text: str) -> bool:
    match = REQUIREMENT_ID.fullmatch(text)
    return bool(match) and (valid_state(match[1]) or valid_transition(match[1]))


def unfenced(path: Path) -> str:
    """The file's text, without code blocks."""
    lines, fenced = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced:
            lines.append(line)
    return "\n".join(lines)


def visible(path: Path) -> str:
    """The file's text, without code: an example of a link or anchor isn't one."""
    return INLINE_CODE.sub("", unfenced(path))


def heading_anchors(path: Path) -> set:
    """The anchors GitHub generates for the file's headings: `## Quote latency` is #quote-latency.

    Lower case, punctuation removed, each space a hyphen, and a repeated heading
    numbered from its second use (#limit, #limit-1).
    """
    found, seen = set(), Counter()
    for heading in HEADING.findall(unfenced(path)):
        text = HEADING_MARKUP.sub(lambda m: next((g for g in m.groups() if g), ""), heading)
        anchor = re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")
        found.add(f"{anchor}-{seen[anchor]}" if seen[anchor] else anchor)
        seen[anchor] += 1
    return found


def linked(text: str) -> list:
    """The IDs that a table cell links to."""
    return [fragment for _, fragment in LINK.findall(text)]


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
            return trace.plain(row[name]).strip("*_` ")
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
        self.sources = {}
        self.due = []
        self.paths = {**DEFAULTS, **config.get("handoff", {})}
        self.user_rows, self.state_rows, self.transition_rows = [], [], []
        self.requirement_rows, self.dropped_rows = [], []

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
        users = [t for t in found if has(t, "user") and not any(c in t["header"] for c in ("state", "transition", "journey"))]
        states = [t for t in found if has(t, "state")]
        transitions = [t for t in found if has(t, "transition")]
        journeys = [t for t in found if has(t, "journey")]
        self.user_rows = [r for t in users for r in t["rows"]]
        self.transition_rows = [r for t in transitions for r in t["rows"]]
        if not any(t["rows"] for t in users):
            self.problem(f"{rel}: no users.")
        if not self.transition_rows:
            self.problem(f"{rel}: no transitions.")
        if not any(t["rows"] for t in journeys):
            self.problem(f"{rel}: no journeys.")
        rows = [r for t in states for r in t["rows"]]
        self.state_rows = rows
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

        for table, needed in [(t, ["state or transition", "source"]) for t in functional + nonfunctional] + [
            (t, ["state or transition"]) for t in dropped
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
                self.requirement_rows.append(row)
                if not req:
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
                self.sources[req] = source
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
                self.dropped_rows.append(row)
                if not req:
                    continue
                reqs.pop(req, None)
                self.dropped.add(req)
                if not filled(cell(row, "reason")):
                    self.problem(f"{req}: dropped with no reason.")
                if not filled(cell(row, "decided by")):
                    self.problem(f"{req}: dropped, but doesn't say who decided.")
        return reqs

    def identified(self, row: dict, kind: str, valid, form: str) -> str:
        """The row's ID, or "" (and a problem) if it can't be checked any further."""
        found = cell(row, "id")
        if not found:
            self.problem(f"A {kind} has no ID: {cell(row, kind, 'requirement') or 'an empty row'}.")
            return ""
        if not valid(found):
            self.problem(f"{found}: not a valid {kind} ID. The form is {form}, with an optional index.")
            return ""
        if found not in ANCHOR_ID.findall(row["id"]):
            self.problem(f"{found}: no anchor for links to reach it.")
        return found

    def parent(self, row: dict, found: str, column: str, what: str) -> str:
        """The one ID this row's column links back to, or "" (and a problem)."""
        targets = linked(row.get(column, ""))
        if len(targets) != 1:
            self.problem(f"{found}: needs one link back to {what}, and has {len(targets)}.")
            return ""
        return targets[0]

    def definitions(self):
        """Every definition has a good ID and an anchor, and links back to what it depends on."""
        users, states, transitions = set(), set(), set()
        for rows, kind, valid, form, seen in (
            (self.user_rows, "user", USER_ID.fullmatch, "USER", users),
            (self.state_rows, "state", valid_state, "USER_STATE", states),
            (self.transition_rows, "transition", valid_transition, "USER_STATE1_TO_STATE2", transitions),
        ):
            for row in rows:
                found = self.identified(row, kind, valid, form)
                if found:
                    seen.add(found)
        for row in self.state_rows:
            found = cell(row, "id")
            if found in states:
                user = STATE_ID.fullmatch(found)[1]
                target = self.parent(row, found, "user", "its user")
                if target and target != user:
                    self.problem(f"{found}: links back to {target}, but its ID says {user}.")
                elif target and target not in users:
                    self.problem(f"{found}: its user {target} isn't in the users table.")
        for row in self.transition_rows:
            found = cell(row, "id")
            if found in transitions:
                self.transition_parents(row, found, states)
        for row in self.requirement_rows + self.dropped_rows:
            found = self.identified(row, "requirement", valid_requirement, "USER_STATE_REQ or USER_STATE1_TO_STATE2_REQ")
            if not found:
                continue
            expected = REQUIREMENT_ID.fullmatch(found)[1]
            target = self.parent(row, found, "state or transition", "its state or transition")
            if target and target != expected:
                self.problem(f"{found}: links back to {target}, but its ID says {expected}.")
            elif target and target not in states | transitions:
                self.problem(f"{found}: {target} isn't in the states or transitions tables.")

        defined = [cell(r, "id") for r in self.user_rows + self.state_rows + self.transition_rows + self.requirement_rows]
        for rows in (defined, [cell(r, "id") for r in self.dropped_rows]):
            for found, count in Counter(rows).items():
                if found and count > 1:
                    self.problem(f"{found}: used as an ID {count} times.")

    def transition_parents(self, row: dict, found: str, states: set):
        left, right = found.split("_TO_")
        user = STATE_ID.fullmatch(left)[1]
        source = self.parent(row, found, "from", "the state it leaves")
        target = self.parent(row, found, "to", "the state it enters")
        if source and source != left:
            self.problem(f"{found}: links back to {source} as the state it leaves, but its ID says {left}.")
        # The ID's second state may be followed by the transition's own index.
        entered = {f"{user}_{right}", f"{user}_{re.sub(r'_[0-9]+$', '', right)}"}
        if target and target not in entered:
            self.problem(f"{found}: links back to {target} as the state it enters, which doesn't match its ID.")
        for state in (source, target):
            if state and state not in states:
                self.problem(f"{found}: {state} isn't in the states table.")

    def links(self):
        """Every link to an anchor or heading, in the files that hold the definitions, leads somewhere."""
        files = [self.paths["users"], self.trace["requirements"], *self.paths["decisions"]]
        for rel in files:
            path = self.project / rel
            if not path.is_file():
                continue
            for file, fragment in LINK.findall(visible(path)):
                if "://" in file:
                    continue
                target = (path.parent / file) if file else path
                if not target.is_file() or fragment not in {*ANCHOR_ID.findall(visible(target)), *heading_anchors(target)}:
                    self.problem(f"{rel}: the link to {file}#{fragment} goes nowhere.")

    def tests(self, reqs: dict):
        tagged = trace.tags(self.project, self.trace["tests"], self.trace["tag"])
        missing = [r for r in sorted(reqs) if r not in tagged and not re.search(r"by hand", reqs[r], re.I)]
        self.due = [r for r in missing if self.sources.get(r) in ("fixed", "design")]
        untested = [r for r in missing if r not in self.due]
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
    check.definitions()
    check.links()
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
    if check.due:
        print(f"Tests due in Execution ({len(check.due)}, fixed or design): {', '.join(check.due)}.")
    if check.problems:
        print(f"The handoff isn't complete ({len(check.problems)}):")
        for problem in check.problems:
            print(f"- {problem}")
        return 1
    print("The handoff is complete." if not before_sign_off or signed else "The handoff is ready for sign-off.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
