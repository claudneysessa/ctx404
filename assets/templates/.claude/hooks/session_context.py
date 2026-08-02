#!/usr/bin/env python3
"""Inject compact project state into the main Claude session."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        event = {}

    if event.get("agent_type"):
        emit({})
        return 0

    raw_root = event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = Path(str(raw_root)).resolve()
    helper = root / ".claude" / "scripts" / "context_tool.py"
    command = [sys.executable, str(helper), "status", "--root", str(root)]

    try:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=8, check=False)
        if result.returncode == 0:
            status = json.loads(result.stdout)
            context = "CTX404 project context: " + json.dumps(
                status, ensure_ascii=False, separators=(",", ":")
            )
        else:
            detail = (result.stderr or result.stdout or "unknown error").strip()[:300]
            context = f"CTX404 context status unavailable: {detail}"
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        context = f"CTX404 context status unavailable: {str(exc)[:300]}"

    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
