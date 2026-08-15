#!/usr/bin/env python3
"""Restrict CTX404 auxiliary agents to deterministic Bash helpers."""

from __future__ import annotations

import json
import re
import sys


AUXILIARY_AGENTS = {"context-scout", "context-curator"}
SAFE_COMMAND = re.compile(
    r'^\s*python(?:\.exe)?\s+"?\.claude[\\/]scripts[\\/]context_tool\.py"?\s+'
    r'(?:validate|doctor|sync|status|find|review|list-topics|history|snapshot)'
    r'(?:\s+[^;&|><`\r\n]*)?\s*$',
    re.IGNORECASE,
)


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        emit({})
        return 0

    if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
        emit({})
        return 0

    if event.get("agent_type") not in AUXILIARY_AGENTS:
        emit({})
        return 0

    command = str((event.get("tool_input") or {}).get("command", ""))
    if SAFE_COMMAND.fullmatch(command):
        emit({})
        return 0

    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "CTX404 auxiliary agents may use Bash only for "
                    "python .claude/scripts/context_tool.py commands. "
                    "Return other shell work to the main model."
                ),
            }
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
