#!/usr/bin/env python3
"""PreToolUse hook: no work on a phase until every earlier phase's gate is approved.

Reads the hook input (JSON) on stdin. Exits 2 with a reason on stderr to block
the tool call; Claude Code shows the reason to the model. Exits 0 to allow.

Also blocks:
- any write to the legacy slice (it is the test oracle and must not change);
- any write by the agent to the gates file (only a person approves a gate).

Writes are checked for the file tools, and for shell commands that write in the
usual ways: redirections, tee, cp, mv, touch, sed -i and the like. A shell
command can always write in a way no parser sees (a script, python -c), so the
shell check is a guard against mistakes, not a sandbox.

Projects opt in with `.claude/slice-migration.json` (see templates/config.json).
Without it the hook allows everything.
"""

import json
import os
import re
import shlex
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

CONFIG = ".claude/slice-migration.json"
FILE_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}

REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")", "\n"}
# Commands whose arguments (after options) are all files they write.
WRITES_ALL_ARGS = {"touch", "truncate", "rm", "rmdir", "mkdir", "tee", "chmod", "chown"}
# Commands that write to their last argument.
WRITES_LAST_ARG = {"cp", "mv", "install", "ln", "rsync"}
# Commands that write their file arguments when given -i.
WRITES_IN_PLACE = {"sed", "perl"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")


class Gate:
    def __init__(self, project: Path, config: dict):
        self.project = project
        self.gates_file = config["gates_file"].strip("/")
        self.phases = config["phases"]
        self.legacy = (config.get("legacy_path") or "").strip("/")

    def relative(self, raw: str, cwd: Path):
        """The path relative to the project, or None if it's outside it."""
        path = Path(os.path.expanduser(raw))
        if not path.is_absolute():
            path = cwd / path
        try:
            return PurePosixPath(path.resolve().relative_to(self.project)).as_posix()
        except ValueError:
            return None

    def check(self, rel: str):
        """Why writing `rel` is blocked, or None if it's allowed."""
        if rel == self.gates_file:
            return f"only a person may approve a gate. Ask them to update {self.gates_file} themselves."
        if self.legacy and (rel == self.legacy or rel.startswith(self.legacy + "/")):
            return f"{self.legacy} is the legacy slice, the test oracle. It must not be modified."

        index = next(
            (i for i, phase in enumerate(self.phases) if any(fnmatch(rel, p) for p in phase.get("paths", []))),
            None,
        )
        if index is None:
            return None

        try:
            with (self.project / self.gates_file).open(encoding="utf-8") as f:
                gates = json.load(f)
        except FileNotFoundError:
            gates = {}
        except (OSError, ValueError) as e:
            return f"{self.gates_file} can't be read ({e!r}), so no gate counts as approved."

        for earlier in self.phases[:index]:
            if not approved(gates, earlier["name"]):
                return (
                    f"{rel} belongs to the {self.phases[index]['name']} phase, "
                    f"but the {earlier['name']} gate hasn't been approved. "
                    f"Finish {earlier['name']} and ask a person to review it. "
                    f"They approve it by adding approved_by and date for "
                    f'"{earlier["name"]}" in {self.gates_file}.'
                )
        return None


def block(reason: str) -> None:
    print(f"slice-migration: {reason}", file=sys.stderr)
    sys.exit(2)


def approved(gates: dict, phase: str) -> bool:
    entry = gates.get(phase)
    return isinstance(entry, dict) and bool(entry.get("approved_by")) and bool(entry.get("date"))


def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies: they're data, and their quotes would confuse the parser."""
    lines = command.split("\n")
    kept, end = [], None
    for line in lines:
        if end is not None:
            if line.strip() == end:
                end = None
            continue
        kept.append(line)
        match = HEREDOC.search(line)
        if match:
            end = match.group(2)
    return "\n".join(kept)


def split_commands(command: str):
    """Yield (words, redirect targets) for each simple command in a shell line."""
    lexer = shlex.shlex(strip_heredocs(command), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.whitespace = " \t\r"  # Keep newlines: they separate commands.
    words, targets, tokens = [], [], list(lexer)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in SEPARATORS:
            if words or targets:
                yield words, targets
            words, targets = [], []
        elif token in REDIRECTS and i + 1 < len(tokens):
            targets.append(tokens[i + 1])
            i += 1
        elif token in {"<", "<<", "<<<", ">&", "<&"} and i + 1 < len(tokens):
            i += 1  # Input, or a file descriptor: nothing written.
        elif not (token.isdigit() and i + 1 < len(tokens) and tokens[i + 1] in REDIRECTS | {">&"}):
            words.append(token)
        i += 1
    if words or targets:
        yield words, targets


def written_paths(words: list) -> list:
    """The files a simple command writes, as far as its name and options show."""
    if not words:
        return []
    name = os.path.basename(words[0])
    args = words[1:]
    files = [a for a in args if not a.startswith("-")]
    if name == "dd":
        return [a[3:] for a in args if a.startswith("of=")]
    if name in WRITES_ALL_ARGS:
        return files
    if name in WRITES_LAST_ARG:
        target = next((a.split("=", 1)[1] for a in args if a.startswith("--target-directory=")), None)
        if "-t" in args and args.index("-t") + 1 < len(args):
            target = args[args.index("-t") + 1]
        return [target] if target else files[-1:]
    if name in WRITES_IN_PLACE and any(re.fullmatch(r"-[a-zA-Z]*i\S*|--in-place\S*", a) for a in args):
        return files[1:] if name == "sed" and not any(a in {"-e", "-f"} for a in args) else files
    if name == "git" and args[:1] in (["checkout"], ["restore"]) and "--" in args:
        return args[args.index("--") + 1 :]
    return []


def check_shell(gate: Gate, command: str, cwd: Path) -> None:
    if gate.gates_file in command:
        block(f"only a person may approve a gate. Ask them to update {gate.gates_file} themselves.")
    try:
        commands = list(split_commands(command))
    except ValueError:
        return  # Unbalanced quotes: the shell will refuse it too.
    for words, targets in commands:
        if words[:1] == ["cd"] and len(words) == 2:
            cwd = Path(os.path.expanduser(words[1])) if os.path.isabs(os.path.expanduser(words[1])) else cwd / words[1]
            continue
        for raw in targets + written_paths(words):
            rel = gate.relative(raw, cwd)
            reason = rel and gate.check(rel)
            if reason:
                block(reason)


def main() -> None:
    event = json.load(sys.stdin)
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    cwd = Path(event.get("cwd") or project)

    config_path = project / CONFIG
    if not config_path.is_file():
        return
    try:
        with config_path.open(encoding="utf-8") as f:
            gate = Gate(project, json.load(f))
    except (OSError, ValueError, KeyError, AttributeError) as e:
        # Fail closed: a broken config must not switch the gates off.
        block(f"{CONFIG} can't be read ({e!r}). Fix it before going on.")

    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool == "Bash":
        check_shell(gate, tool_input.get("command", ""), cwd)
    elif tool in FILE_TOOLS and tool_input.get(FILE_TOOLS[tool]):
        rel = gate.relative(tool_input[FILE_TOOLS[tool]], cwd)
        reason = rel and gate.check(rel)
        if reason:
            block(reason)


if __name__ == "__main__":
    main()
