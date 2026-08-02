#!/usr/bin/env python3
"""Deterministic CTX404 bootstrap for an empty Claude Code project."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = SKILL_ROOT / "assets" / "templates"
CTX404_VERSION = "0.1.0-beta.1"
GOVERNANCE_START = "<!-- ctx404:governance:start"
GOVERNANCE_END = "<!-- ctx404:governance:end -->"
PENDING_STATE = "ctx404-pending.json"


class BootstrapError(RuntimeError):
    pass


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def ensure_tool(command: str) -> str:
    executable = shutil.which(command)
    if not executable:
        raise BootstrapError(f"Required command not found: {command}")
    return executable


def resolve_target(raw_target: str) -> Path:
    target = Path(raw_target).expanduser().resolve()
    if not target.exists():
        target.mkdir(parents=True)
    if not target.is_dir():
        raise BootstrapError(f"Target is not a directory: {target}")
    return target


def visible_entries(target: Path) -> list[Path]:
    return sorted((item for item in target.iterdir() if item.name != ".git"), key=lambda p: p.name)


def assert_bootstrappable(target: Path) -> None:
    entries = visible_entries(target)
    if entries:
        names = ", ".join(item.name for item in entries[:10])
        raise BootstrapError(
            "CTX404 v1 only initializes an empty directory or one containing only .git. "
            f"Found: {names}"
        )


def prepare(target: Path) -> dict[str, object]:
    git = ensure_tool("git")
    ensure_tool("python")
    assert_bootstrappable(target)

    created_git = False
    if not (target / ".git").exists():
        result = run([git, "init"], target)
        if result.returncode != 0:
            raise BootstrapError(result.stderr.strip() or "git init failed")
        created_git = True

    pending_path = target / ".git" / PENDING_STATE
    pending_path.write_text(
        json.dumps({"version": CTX404_VERSION, "phase": "awaiting-init"}) + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "phase": "prepare",
        "target": str(target),
        "gitInitialized": created_git,
        "next": "Invoke Claude Code /init, then run the install phase.",
    }


def copy_template(relative_path: str, target: Path, created: list[str]) -> None:
    source = TEMPLATES_ROOT / relative_path
    destination = target / relative_path
    if destination.exists():
        raise BootstrapError(f"Refusing to overwrite existing path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    created.append(relative_path.replace("\\", "/"))


def consolidate_claude_md(target: Path, created: list[str], updated: list[str]) -> None:
    governance = (TEMPLATES_ROOT / "CLAUDE.governance.md").read_text(encoding="utf-8").strip()
    governance = governance.replace("{{PROJECT_NAME}}", target.name)
    governance = governance.replace("{{CTX404_VERSION}}", CTX404_VERSION)
    claude_path = target / "CLAUDE.md"
    existing = claude_path.read_text(encoding="utf-8").strip() if claude_path.exists() else ""

    if GOVERNANCE_START in existing or GOVERNANCE_END in existing:
        raise BootstrapError("CLAUDE.md already contains CTX404 governance markers")

    project_guidance = existing or "# Project Guidance\n\nProject-specific guidance will evolve as the project is defined."
    content = f"{governance}\n\n---\n\n{project_guidance}\n"
    claude_path.write_text(content, encoding="utf-8", newline="\n")
    if existing:
        updated.append("CLAUDE.md")
    else:
        created.append("CLAUDE.md")


def render_initial_json(target: Path) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    context_root = target / ".claude" / "context"
    index_path = context_root / "index.json"
    index_text = index_path.read_text(encoding="utf-8").replace("{{CTX404_VERSION}}", CTX404_VERSION)
    index = json.loads(index_text)
    index["project"]["name"] = target.name
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    current_path = context_root / "current.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    current["updatedAt"] = now
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    history_path = context_root / "history.jsonl"
    history_event = {
        "at": now,
        "type": "bootstrap",
        "summary": "CTX404 context foundation installed",
        "refs": [],
    }
    history_path.write_text(json.dumps(history_event, ensure_ascii=False) + "\n", encoding="utf-8")

    readme_path = target / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = readme.replace("{{PROJECT_NAME}}", target.name)
    readme_path.write_text(readme, encoding="utf-8", newline="\n")


def install(target: Path) -> dict[str, object]:
    ensure_tool("git")
    ensure_tool("python")
    if not (target / ".git").is_dir():
        raise BootstrapError("Git is not initialized. Run the prepare phase first.")

    allowed = {"CLAUDE.md"}
    unexpected = [item.name for item in visible_entries(target) if item.name not in allowed]
    if unexpected:
        raise BootstrapError(
            "After /init, only CLAUDE.md may exist before CTX404 installation. "
            f"Found: {', '.join(unexpected)}"
        )

    created: list[str] = []
    updated: list[str] = []
    for relative in (
        "README.md",
        ".claude/context/index.json",
        ".claude/context/current.json",
        ".claude/context/schema.json",
        ".claude/context/history.jsonl",
        ".claude/context/topics/.gitkeep",
        ".claude/context/templates/topic.md",
        ".claude/agents/context-scout.md",
        ".claude/agents/context-curator.md",
        ".claude/settings.json",
        ".claude/hooks/session_context.py",
        ".claude/hooks/guard_agent_bash.py",
        ".claude/scripts/context_tool.py",
    ):
        copy_template(relative, target, created)

    consolidate_claude_md(target, created, updated)
    render_initial_json(target)

    validator = target / ".claude" / "scripts" / "context_tool.py"
    result = run([sys.executable, str(validator), "validate", "--root", str(target)], target)
    if result.returncode != 0:
        raise BootstrapError(result.stdout.strip() or result.stderr.strip() or "Context validation failed")

    pending_path = target / ".git" / PENDING_STATE
    if pending_path.exists():
        pending_path.unlink()

    return {
        "ok": True,
        "phase": "install",
        "target": str(target),
        "created": created,
        "updated": updated,
        "validation": json.loads(result.stdout),
        "next": (
            "CTX404 is installed. Take ownership of the repository: refine the Project definition "
            "workspace in CLAUDE.md from explicit user intent and verified evidence, then synchronize "
            "README.md and .claude/context/index.json. Restart Claude Code before relying on the "
            "new project subagents, because file-defined agents load at session start."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="phase", required=True)
    for phase in ("prepare", "install"):
        command = subparsers.add_parser(phase)
        command.add_argument("--target", default=".", help="Project directory (default: current directory)")
    args = parser.parse_args()

    try:
        target = resolve_target(args.target)
        result = prepare(target) if args.phase == "prepare" else install(target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (BootstrapError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
