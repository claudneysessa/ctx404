#!/usr/bin/env python3
"""Stop the session from ending while deliberation is still unrecorded.

CTX404 could always write context; nothing ever asked it to. Reading was a hook and
writing was a paragraph, so a session made of decisions - no file touched, no diff to
notice - ended with the reasoning still only in the chat. This gate closes that gap.

It blocks the stop once, never twice: Claude Code sets stop_hook_active on the retry,
and the guard below lets that one through. Worst case the user loses one extra turn.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


DEFAULT_PENDING_TURNS = 3
# Auxiliary agents answer questions; they do not own the project record.
SKIP_AGENTS = {"context-scout", "context-curator"}
REASON = (
    "CTX404: this session has {pending} exchanges with no context written. "
    "Deliberation is durable context even when no file changed - the model or structure "
    "discussed, the approach chosen, the constraint discovered, and above all what the user "
    "considered and rejected, with the reason. Record it now, then stop.\n"
    "Write or update the affected topic with "
    "`python .claude/scripts/context_tool.py topic-write`, then run "
    "`python .claude/scripts/context_tool.py complete --event-type decision`. "
    "Read .claude/rules/ctx404-context.md for the exact arguments.\n"
    "If this session genuinely decided nothing - a greeting, a lookup, a repeated answer - "
    "say so in one line and stop; this gate does not block twice."
)


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def pending_turns(transcript: Path) -> int:
    """User turns since the last `complete`. The transcript is the only honest witness."""
    turns = 0
    with transcript.open(encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("isMeta") or entry.get("agent_type"):
                continue
            message = entry.get("message") or {}
            content = message.get("content")
            if entry.get("type") == "user":
                if isinstance(content, str):
                    blocks = [content]
                elif isinstance(content, list):
                    # A tool result is the session answering itself, not the user speaking.
                    blocks = [
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                else:
                    blocks = []
                for text in blocks:
                    stripped = text.strip()
                    if stripped and not stripped.startswith("<"):
                        turns += 1
                        break
            elif entry.get("type") == "assistant" and isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    payload = json.dumps(block.get("input") or {}, ensure_ascii=False)
                    if "context_tool.py" in payload and "complete" in payload:
                        turns = 0
                        break
    return turns


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        emit({})
        return 0

    # Claude Code sets this on the stop it already blocked once. Never trap a session.
    if event.get("stop_hook_active") or event.get("agent_type") in SKIP_AGENTS:
        emit({})
        return 0

    raw_root = event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = Path(str(raw_root)).resolve()
    if not (root / ".claude" / "context" / "current.json").is_file():
        emit({})
        return 0

    transcript = event.get("transcript_path")
    if not transcript:
        emit({})
        return 0
    path = Path(str(transcript))
    if not path.is_file():
        emit({})
        return 0

    try:
        threshold = max(1, int(os.environ.get("CTX404_GATE_TURNS", DEFAULT_PENDING_TURNS)))
    except ValueError:
        threshold = DEFAULT_PENDING_TURNS

    try:
        pending = pending_turns(path)
    except OSError:
        # A gate that breaks the session is worse than a gate that misses one. Fail open.
        emit({})
        return 0

    if pending < threshold:
        emit({})
        return 0

    emit({"decision": "block", "reason": REASON.format(pending=pending)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
