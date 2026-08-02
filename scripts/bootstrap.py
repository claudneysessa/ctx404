#!/usr/bin/env python3
"""Deterministic CTX404 bootstrap or adoption for a Claude Code project."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = SKILL_ROOT / "assets" / "templates"
CTX404_VERSION = "0.2.0-beta.1"
GOVERNANCE_START = "<!-- ctx404:governance:start"
GOVERNANCE_END = "<!-- ctx404:governance:end -->"
PENDING_STATE = "ctx404-pending.json"
MANAGED_FILES = (
    ".claude/context/index.json",
    ".claude/context/current.json",
    ".claude/context/schema.json",
    ".claude/context/history.jsonl",
    ".claude/context/topics/.gitkeep",
    ".claude/context/templates/topic.md",
    ".claude/agents/context-scout.md",
    ".claude/agents/context-curator.md",
    ".claude/hooks/session_context.py",
    ".claude/hooks/guard_agent_bash.py",
    ".claude/scripts/context_tool.py",
)


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


def detect_mode(target: Path) -> str:
    return "new" if not visible_entries(target) else "adopt"


def prepare(target: Path) -> dict[str, object]:
    git = ensure_tool("git")
    ensure_tool("python")
    mode = detect_mode(target)

    created_git = False
    if not (target / ".git").exists():
        result = run([git, "init"], target)
        if result.returncode != 0:
            raise BootstrapError(result.stderr.strip() or "git init failed")
        created_git = True

    pending_path = target / ".git" / PENDING_STATE
    if pending_path.exists():
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        mode = str(pending.get("mode", mode))
    pending_path.write_text(
        json.dumps(
            {
                "version": CTX404_VERSION,
                "phase": "awaiting-init" if mode == "new" else "ready-to-adopt",
                "mode": mode,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "phase": "prepare",
        "mode": mode,
        "target": str(target),
        "gitInitialized": created_git,
        "next": (
            "Invoke Claude Code /init, then run the install phase."
            if mode == "new"
            else "Skip /init and run the install phase. Existing project files will be preserved."
        ),
    }


def copy_template(relative_path: str, target: Path, created: list[str]) -> None:
    source = TEMPLATES_ROOT / relative_path
    destination = target / relative_path
    if destination.exists():
        raise BootstrapError(f"Refusing to overwrite existing path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    created.append(relative_path.replace("\\", "/"))


def consolidate_claude_md(target: Path, mode: str, created: list[str], updated: list[str]) -> None:
    governance = (TEMPLATES_ROOT / "CLAUDE.governance.md").read_text(encoding="utf-8").strip()
    governance = governance.replace("{{PROJECT_NAME}}", target.name)
    governance = governance.replace("{{CTX404_VERSION}}", CTX404_VERSION)
    governance = governance.replace(
        "{{INSTALL_MODE}}", "new repository bootstrap" if mode == "new" else "existing repository adoption"
    )
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


def merged_settings(target: Path) -> dict[str, object]:
    template_path = TEMPLATES_ROOT / ".claude" / "settings.json"
    template = json.loads(template_path.read_text(encoding="utf-8"))
    destination = target / ".claude" / "settings.json"
    existing: dict[str, object] = {}
    if destination.exists():
        loaded = json.loads(destination.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise BootstrapError("Existing .claude/settings.json must contain a JSON object")
        existing = loaded

    merged = dict(existing)
    merged["autoMemoryEnabled"] = False
    hooks = merged.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise BootstrapError("Existing .claude/settings.json hooks must be a JSON object")

    for event, entries in template["hooks"].items():
        current = hooks.setdefault(event, [])
        if not isinstance(current, list):
            raise BootstrapError(f"Existing hook event must be a JSON array: {event}")
        for entry in entries:
            if entry not in current:
                current.append(entry)
    return merged


def write_settings(target: Path, created: list[str], updated: list[str]) -> None:
    destination = target / ".claude" / "settings.json"
    existed = destination.exists()
    content = merged_settings(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (updated if existed else created).append(".claude/settings.json")


def render_initial_json(target: Path, mode: str) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    context_root = target / ".claude" / "context"
    index_path = context_root / "index.json"
    index_text = index_path.read_text(encoding="utf-8").replace("{{CTX404_VERSION}}", CTX404_VERSION)
    index = json.loads(index_text)
    index["project"]["name"] = target.name
    if mode == "adopt" and not (target / "README.md").is_file():
        index["entrypoints"].pop("readme", None)
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    current_path = context_root / "current.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    current["updatedAt"] = now
    if mode == "adopt":
        current["status"] = "active"
        current["lastCompleted"] = "CTX404 adopted an existing repository"
        current["nextStep"] = "Continue working normally and capture durable context as each area is touched"
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    history_path = context_root / "history.jsonl"
    history_event = {
        "at": now,
        "type": "bootstrap" if mode == "new" else "adopt",
        "summary": (
            "CTX404 context foundation installed"
            if mode == "new"
            else "CTX404 adopted an existing repository; durable context starts from this point"
        ),
        "refs": [],
    }
    history_path.write_text(json.dumps(history_event, ensure_ascii=False) + "\n", encoding="utf-8")

    readme_path = target / "README.md"
    if mode == "new":
        readme = readme_path.read_text(encoding="utf-8")
        readme = readme.replace("{{PROJECT_NAME}}", target.name)
        readme_path.write_text(readme, encoding="utf-8", newline="\n")


def rollback(target: Path, created: list[str], backup_root: Path) -> None:
    for relative in reversed(created):
        path = target / relative
        if path.is_file():
            path.unlink()
    if backup_root.exists():
        for backup in backup_root.rglob("*"):
            if backup.is_file():
                destination = target / backup.relative_to(backup_root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, destination)
        shutil.rmtree(backup_root)


def backup_existing(target: Path, relative_paths: tuple[str, ...], backup_root: Path) -> None:
    for relative in relative_paths:
        source = target / relative
        if source.is_file():
            destination = backup_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def install(target: Path) -> dict[str, object]:
    ensure_tool("git")
    ensure_tool("python")
    if not (target / ".git").is_dir():
        raise BootstrapError("Git is not initialized. Run the prepare phase first.")

    pending_path = target / ".git" / PENDING_STATE
    if not pending_path.is_file():
        raise BootstrapError("CTX404 prepare state is missing. Run the prepare phase first.")
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    mode = str(pending.get("mode", "new"))
    if mode not in {"new", "adopt"}:
        raise BootstrapError(f"Unsupported CTX404 installation mode: {mode}")

    existing_claude = (target / "CLAUDE.md").read_text(encoding="utf-8") if (target / "CLAUDE.md").exists() else ""
    has_start = GOVERNANCE_START in existing_claude
    has_end = GOVERNANCE_END in existing_claude
    if has_start != has_end:
        raise BootstrapError("CLAUDE.md contains incomplete CTX404 governance markers")
    if has_start and has_end:
        validator = target / ".claude" / "scripts" / "context_tool.py"
        if not validator.is_file():
            raise BootstrapError("CTX404 governance exists but the context helper is missing")
        result = run([sys.executable, str(validator), "validate", "--root", str(target)], target)
        if result.returncode != 0:
            raise BootstrapError(result.stdout.strip() or result.stderr.strip() or "Existing context validation failed")
        pending_path.unlink()
        return {
            "ok": True,
            "phase": "install",
            "mode": mode,
            "target": str(target),
            "alreadyInstalled": True,
            "created": [],
            "updated": [],
            "validation": json.loads(result.stdout),
            "next": "CTX404 is already installed and valid. Continue working normally.",
        }

    if mode == "new":
        allowed = {"CLAUDE.md"}
        unexpected = [item.name for item in visible_entries(target) if item.name not in allowed]
        if unexpected:
            raise BootstrapError(
                "After /init, only CLAUDE.md may exist before CTX404 installation. "
                f"Found: {', '.join(unexpected)}"
            )

    conflicts = [relative for relative in MANAGED_FILES if (target / relative).exists()]
    if conflicts:
        raise BootstrapError("Refusing to overwrite existing managed paths: " + ", ".join(conflicts))

    # Parse and validate the existing settings before any project file is changed.
    merged_settings(target)

    created: list[str] = []
    updated: list[str] = []
    backup_root = target / ".git" / f"ctx404-backup-{uuid.uuid4().hex}"
    backup_existing(target, ("CLAUDE.md", ".claude/settings.json"), backup_root)
    try:
        if mode == "new":
            copy_template("README.md", target, created)
        for relative in MANAGED_FILES:
            copy_template(relative, target, created)
        write_settings(target, created, updated)
        consolidate_claude_md(target, mode, created, updated)
        render_initial_json(target, mode)

        validator = target / ".claude" / "scripts" / "context_tool.py"
        result = run([sys.executable, str(validator), "validate", "--root", str(target)], target)
        if result.returncode != 0:
            raise BootstrapError(result.stdout.strip() or result.stderr.strip() or "Context validation failed")
    except Exception:
        rollback(target, created, backup_root)
        raise
    if backup_root.exists():
        shutil.rmtree(backup_root)
    pending_path.unlink()

    return {
        "ok": True,
        "phase": "install",
        "mode": mode,
        "target": str(target),
        "created": created,
        "updated": updated,
        "validation": json.loads(result.stdout),
        "next": (
            "CTX404 is installed in a new repository. Refine the Project definition workspace from "
            "explicit user intent and verified evidence, then synchronize README.md and the context index."
            if mode == "new"
            else "CTX404 adopted this existing repository without retrospective analysis. Durable context "
            "starts now. Continue working normally. Optionally ask Claude for a concise, evidence-based "
            "project baseline and approve it before saving it as context. Native /init may also be run "
            "manually and reviewed before incorporation."
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
