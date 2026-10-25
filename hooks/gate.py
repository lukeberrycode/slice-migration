#!/usr/bin/env python3
"""PreToolUse hook: no work on a phase until every earlier phase's gate is approved.

Reads the hook input (JSON) on stdin. Exits 2 with a reason on stderr to block
the tool call; Claude Code shows the reason to the model. Exits 0 to allow.

Also blocks:
- any write to the legacy slice (it is the test oracle and must not change);
- any write by the agent to the gates file (only a person approves a gate).

Projects opt in with `.claude/slice-migration.json` (see templates/config.json).
Without it the hook allows everything.
"""

import json
import os
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

CONFIG = ".claude/slice-migration.json"
FILE_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}


def block(reason: str) -> None:
    print(f"slice-migration: {reason}", file=sys.stderr)
    sys.exit(2)


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def approved(gates: dict, phase: str) -> bool:
    entry = gates.get(phase)
    return isinstance(entry, dict) and bool(entry.get("approved_by")) and bool(entry.get("date"))


def under(rel: str, folder: str) -> bool:
    folder = folder.strip("/")
    return rel == folder or rel.startswith(folder + "/")


def main() -> None:
    event = json.load(sys.stdin)
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()

    config_path = project / CONFIG
    if not config_path.is_file():
        return
    try:
        config = load_json(config_path)
        gates_file = config["gates_file"]
        phases = config["phases"]
        legacy = config.get("legacy_path")
    except (OSError, ValueError, KeyError) as e:
        # Fail closed: a broken config must not switch the gates off.
        block(f"{CONFIG} can't be read ({e!r}). Fix it before going on.")

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool == "Bash":
        command = tool_input.get("command", "")
        if gates_file in command:
            block(f"only a person may approve a gate. Ask them to update {gates_file} themselves.")
        return

    if tool not in FILE_TOOLS:
        return
    raw = tool_input.get(FILE_TOOLS[tool])
    if not raw:
        return
    path = Path(raw)
    if not path.is_absolute():
        path = Path(event.get("cwd") or project) / path
    try:
        rel = PurePosixPath(path.resolve().relative_to(project)).as_posix()
    except ValueError:
        return  # Outside the project: not ours to police.

    if rel == gates_file.strip("/"):
        block(f"only a person may approve a gate. Ask them to update {gates_file} themselves.")
    if legacy and under(rel, legacy):
        block(f"{legacy} is the legacy slice, the test oracle. It must not be modified.")

    index = next(
        (i for i, phase in enumerate(phases) if any(fnmatch(rel, p) for p in phase.get("paths", []))),
        None,
    )
    if index is None:
        return

    try:
        gates = load_json(project / gates_file)
    except FileNotFoundError:
        gates = {}
    except (OSError, ValueError) as e:
        block(f"{gates_file} can't be read ({e!r}), so no gate counts as approved.")

    for earlier in phases[:index]:
        if not approved(gates, earlier["name"]):
            block(
                f"{rel} belongs to the {phases[index]['name']} phase, "
                f"but the {earlier['name']} gate hasn't been approved. "
                f"Finish {earlier['name']} and ask a person to review it. "
                f"They approve it by adding approved_by and date for "
                f'"{earlier["name"]}" in {gates_file}.'
            )


if __name__ == "__main__":
    main()
