#!/usr/bin/env python3
"""Trace check: every requirement has a test, and every test tag names a requirement.

A requirement is a table row in the requirements file whose first cell is an ID
such as AUTH-1 or MONEY-1N. A test is traced to it by a tag naming the ID, by
default `req("AUTH-1")` (a pytest marker, or the same text in any language).

Rows that say "By hand" count as traced (checked by a person, with the reason in
the row) and are listed separately. IDs matching a pattern in `trace.exempt` in
the config are listed, not failed: for example requirements whose tests are
planned for a later phase.

Usage: trace.py [project dir]. Exit 0 if everything is traced, 1 if not, 2 if
the requirements file can't be read.
"""

import json
import re
import sys
from pathlib import Path

CONFIG = ".claude/slice-migration.json"
DEFAULTS = {
    "requirements": "docs/discovery/requirements.md",
    "tests": ["tests"],
    "tag": r"""req\(([^)]*)\)""",
    "exempt": [],
}
ID = re.compile(r"[A-Z][A-Z0-9]*-\d+[A-Z]*")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "build", "dist"}


def settings(project: Path) -> dict:
    config = {}
    if (project / CONFIG).is_file():
        config = json.loads((project / CONFIG).read_text(encoding="utf-8")).get("trace", {})
    return {**DEFAULTS, **config}


def requirements(path: Path) -> dict:
    """ID -> the row's text, from every Markdown table in the file."""
    found = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        first = cells[0].strip("*` ")
        if ID.fullmatch(first) and first not in found:
            found[first] = line
    return found


def tags(project: Path, folders: list, pattern: str) -> dict:
    """ID -> the test files that tag it."""
    tag = re.compile(pattern)
    found = {}
    for folder in folders:
        root = project / folder
        files = [root] if root.is_file() else root.rglob("*") if root.is_dir() else []
        for file in files:
            if not file.is_file() or SKIP_DIRS & set(file.relative_to(project).parts):
                continue
            try:
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for match in tag.finditer(text):
                for req in ID.findall(match.group(1) if tag.groups else match.group(0)):
                    found.setdefault(req, set()).add(file.relative_to(project).as_posix())
    return found


def main() -> int:
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        config = settings(project)
        reqs = requirements(project / config["requirements"])
    except (OSError, ValueError) as e:
        print(f"Can't read the requirements: {e}", file=sys.stderr)
        return 2
    tagged = tags(project, config["tests"], config["tag"])
    exempt = [re.compile(p) for p in config["exempt"]]

    traced = sorted(r for r in reqs if r in tagged)
    by_hand = sorted(r for r in reqs if r not in tagged and re.search(r"by hand", reqs[r], re.I))
    exempted = sorted(r for r in reqs if r not in tagged and r not in by_hand and any(p.search(r) for p in exempt))
    untested = sorted(r for r in reqs if r not in tagged and r not in by_hand and r not in exempted)
    unknown = sorted(r for r in tagged if r not in reqs)

    print(f"{len(reqs)} requirements in {config['requirements']}; {len(traced)} traced to tests.")
    if by_hand:
        print(f"Checked by hand ({len(by_hand)}): {', '.join(by_hand)}")
    if exempted:
        print(f"Exempt ({len(exempted)}, by trace.exempt): {', '.join(exempted)}")
    if untested:
        print(f"No test ({len(untested)}): {', '.join(untested)}")
    for req in unknown:
        print(f"Unknown requirement {req}, tagged in: {', '.join(sorted(tagged[req]))}")
    return 1 if untested or unknown else 0


if __name__ == "__main__":
    sys.exit(main())
