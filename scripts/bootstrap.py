#!/usr/bin/env python3
"""Deterministic CTX404 bootstrap or adoption for a Claude Code project."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = SKILL_ROOT / "assets" / "templates"
CTX404_VERSION = "0.4.0-beta.2"
GOVERNANCE_START = "<!-- ctx404:governance:start"
GOVERNANCE_END = "<!-- ctx404:governance:end -->"
PENDING_STATE = "ctx404-pending.json"
CLAUDE_MD = "CLAUDE.md"
RECEIPT_STATE = "ctx404-receipt.json"
VERSION_020 = "0.2.0-beta.1"
VERSION_030 = "0.3.0-beta.1"
VERSION_040 = "0.4.0-beta.1"
# Ordered reviewed migration path. Each hop is applied in sequence.
MIGRATION_CHAIN = (VERSION_020, VERSION_030, VERSION_040, CTX404_VERSION)
LEGACY_AUTHORITY_TEXT = (
    "Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, "
    "Git-versioned memory system and the only durable project-context authority."
)
INSTRUCTIONS_FILE = ".claude/ctx404-instructions.md"
DEFINITION_FILE = ".claude/context/project-definition.md"
CONTEXT_RULE_FILE = ".claude/rules/ctx404-context.md"
# Rendered from templates with placeholders instead of copied verbatim.
RENDERED_FILES = (INSTRUCTIONS_FILE, DEFINITION_FILE)
# Managed implementation. A reviewed upgrade refreshes these from the skill so the installed
# helper matches the protocol it is told to follow. Project data is never in this list.
REFRESHABLE_FILES = (
    CONTEXT_RULE_FILE,
    ".claude/scripts/context_tool.py",
    ".claude/hooks/session_context.py",
    ".claude/hooks/guard_agent_bash.py",
    ".claude/hooks/context_gate.py",
    ".claude/agents/context-scout.md",
    ".claude/agents/context-curator.md",
    ".claude/context/templates/topic.md",
    ".claude/context/schema.json",
)
DEFINITION_START = "<!-- ctx404:project-definition:start -->"
DEFINITION_END = "<!-- ctx404:project-definition:end -->"
MANAGED_FILES = (
    CONTEXT_RULE_FILE,
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
    ".claude/hooks/context_gate.py",
    ".claude/scripts/context_tool.py",
)
AUTHORITY_CANDIDATES = (
    (".planning/STATE.md", "project-state"),
    ("STATE.md", "project-state"),
    ("PROJECT_STATE.md", "project-state"),
    (".planning", "planning-system"),
    (".gsd", "planning-system"),
    (".context", "context-system"),
    (".memory", "memory-system"),
    ("memory", "memory-system"),
    (".ai/context", "context-system"),
    (".ai/memory", "memory-system"),
    ("docs/adr", "architecture-decisions"),
    ("docs/adrs", "architecture-decisions"),
    ("docs/decisions", "architecture-decisions"),
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


def git_dir(target: Path) -> Path | None:
    """Real Git directory. In a worktree or submodule `.git` is a file, not a directory."""
    git = shutil.which("git")
    if not git:
        return None
    result = run([git, "rev-parse", "--absolute-git-dir"], target)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def require_git_dir(target: Path) -> Path:
    resolved = git_dir(target)
    if not resolved:
        raise BootstrapError("Git is not initialized. Run the prepare phase first.")
    return resolved


def read_utf8(path: Path) -> str:
    """Read a project file, refusing non-UTF-8 with a usable message instead of a traceback."""
    try:
        return path.read_bytes().decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BootstrapError(
            f"{path.name} is not valid UTF-8 (byte 0x{path.read_bytes()[exc.start]:02x} at "
            f"position {exc.start}). Convert it to UTF-8 and run again; CTX404 will not guess "
            "an encoding for a file it has to rewrite."
        ) from exc


def context_ignored(target: Path) -> dict[str, object] | None:
    """Whether Git would ignore the context directory, and which rule does it."""
    git = shutil.which("git")
    if not git:
        return None
    result = run([git, "check-ignore", "-v", "--no-index", ".claude/context/index.json"], target)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    described = result.stdout.strip().splitlines()[0].split("	")[0]
    source, line, pattern = described.rsplit(":", 2)
    return {"source": source, "line": int(line), "pattern": pattern}


IGNORE_RECIPE = (
    ".claude/*",
    "!.claude/context/",
    "!.claude/agents/",
    "!.claude/hooks/",
    "!.claude/scripts/",
    "!.claude/rules/",
    "!.claude/ctx404-instructions.md",
    "!.claude/settings.json",
)


def find_claude_md(target: Path) -> str | None:
    """Return the on-disk name of the project CLAUDE.md, whatever its casing."""
    for item in sorted(target.iterdir(), key=lambda p: p.name):
        if item.is_file() and item.name.lower() == CLAUDE_MD.lower():
            return item.name
    return None


def linked_local_docs(target: Path, claude_name: str) -> list[str]:
    """Markdown files the existing CLAUDE.md points at.

    A project that already governs its own context names those files from its instructions.
    That is a structural signal, unlike guessing at filenames.
    """
    text = read_utf8(target / claude_name)
    found: list[str] = []
    for match in re.finditer(r"\]\(([^)\s]+\.md)\)|`([^`\s]+\.md)`", text):
        raw = match.group(1) or match.group(2)
        if raw.startswith(("http://", "https://", "/", "#")) or ".." in raw:
            continue
        candidate = raw.lstrip("./")
        if candidate.lower() == CLAUDE_MD.lower() or candidate in found:
            continue
        if (target / candidate).is_file():
            found.append(candidate)
    return sorted(found)


def review_claude_md(target: Path) -> dict[str, object] | None:
    name = find_claude_md(target)
    if not name:
        return None
    text = read_utf8(target / name)
    if GOVERNANCE_START in text:
        # Already governed by CTX404; there is nothing left to decide about this file.
        return None
    return {
        "path": name,
        "needsRename": name != CLAUDE_MD,
        "linkedDocs": linked_local_docs(target, name),
    }


def detect_authorities(target: Path) -> list[dict[str, str]]:
    authorities = [
        {"path": relative, "kind": kind}
        for relative, kind in AUTHORITY_CANDIDATES
        if (target / relative).exists()
    ]
    known = {item["path"] for item in authorities}
    review = review_claude_md(target)
    for relative in (review or {}).get("linkedDocs", []):
        if relative not in known:
            authorities.append({"path": relative, "kind": "claude-md-reference"})
    return authorities


def authority_policy(authority_mode: str) -> str:
    return (
        "`.claude/context/` is the primary durable project-context authority. Any prior context or planning "
        "system may be migrated or retired only through explicit user-approved work; installation itself "
        "does not delete or rewrite it."
        if authority_mode == "exclusive"
        else "`.claude/context/` is the compact routing and continuity layer, not a replacement for existing "
        "authorities. Read `.claude/context/index.json` → `governance.authorities`, update each fact in its "
        "owning source, and store only compact pointers or cross-session state here."
    )


def rename_claude_md_to(target: Path, current_name: str, new_name: str) -> None:
    """Rename through Git in two steps, since a case-only rename is a no-op on Windows."""
    git = ensure_tool("git")
    temporary = f".ctx404-claude-{uuid.uuid4().hex}.md"
    tracked = run([git, "ls-files", "--error-unmatch", current_name], target).returncode == 0
    if tracked:
        for source, destination in ((current_name, temporary), (temporary, new_name)):
            result = run([git, "mv", source, destination], target)
            if result.returncode != 0:
                raise BootstrapError(result.stderr.strip() or f"git mv failed: {source}")
        return
    (target / current_name).rename(target / temporary)
    (target / temporary).rename(target / new_name)


def rename_claude_md(target: Path, current_name: str) -> None:
    rename_claude_md_to(target, current_name, CLAUDE_MD)


def receipt_path(target: Path) -> Path:
    return require_git_dir(target) / RECEIPT_STATE


def load_receipt(target: Path) -> dict[str, object] | None:
    resolved = git_dir(target)
    if not resolved:
        return None
    path = resolved / RECEIPT_STATE
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # A half-written receipt is itself evidence of an interrupted run.
        return {"phase": "installing", "corrupt": True, "created": [], "modified": []}


def save_receipt(target: Path, receipt: dict[str, object]) -> None:
    """Persist before acting, so a killed process still leaves a usable trail."""
    path = receipt_path(target)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revert(target: Path, force: bool = False) -> dict[str, object]:
    """Undo exactly what the recorded run did, refusing on anything changed since."""
    receipt = load_receipt(target)
    if not receipt:
        raise BootstrapError("No CTX404 receipt found; there is nothing recorded to revert")

    # An interrupted run has an empty `created`; the plan is the only complete record.
    interrupted = receipt.get("phase") == "installing"
    recorded = receipt.get("planned", []) if interrupted else receipt.get("created", [])
    created = [str(item) for item in recorded]
    modified = receipt.get("modified", [])
    renamed = receipt.get("renamed")

    changed: list[str] = []
    if not force:
        for relative, digest in (receipt.get("digests") or {}).items():
            if file_digest(target / relative) != digest:
                changed.append(relative)
    if changed:
        raise BootstrapError(
            "Refusing to revert: these files changed after installation: "
            + ", ".join(sorted(changed))
            + ". Inspect them first, or rerun with --force to discard the changes."
        )

    removed: list[str] = []
    for relative in reversed(created):
        path = target / relative
        if path.is_file():
            path.unlink()
            removed.append(relative)
    for relative in sorted({str(Path(item).parent) for item in created}, reverse=True):
        directory = target / relative
        while directory != target and directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
            directory = directory.parent

    restored: list[str] = []
    for entry in modified:
        backup = Path(str(entry["backup"]))
        destination = target / str(entry["path"])
        if backup.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, destination)
            restored.append(str(entry["path"]))
        elif destination.is_file():
            destination.unlink()
            removed.append(str(entry["path"]))

    if renamed:
        current = target / str(renamed["to"])
        if current.is_file():
            rename_claude_md_to(target, str(renamed["to"]), str(renamed["from"]))

    warnings: list[str] = []
    leftovers = [
        str(path.relative_to(target).as_posix())
        for path in sorted((target / ".claude").rglob("*"))
        if path.is_file()
    ] if (target / ".claude").is_dir() else []
    if leftovers:
        warnings.append(
            ".claude/ still holds files CTX404 did not create, so it was kept: "
            + ", ".join(leftovers)
        )
    git = shutil.which("git")
    if git:
        tracked = [item for item in created if run([git, "ls-files", "--error-unmatch", item], target).returncode == 0]
        if tracked:
            warnings.append(
                "Some reverted files were already committed. They are gone from the working tree, "
                "but remain in Git history; commit the removal. Files: " + ", ".join(sorted(tracked))
            )

    resolved = require_git_dir(target)
    for leftover in resolved.glob("ctx404-*backup-*"):
        if leftover.is_dir():
            shutil.rmtree(leftover, ignore_errors=True)
    for name in (RECEIPT_STATE, PENDING_STATE):
        stale = resolved / name
        if stale.is_file():
            stale.unlink()

    return {
        "ok": True,
        "phase": "revert",
        "target": str(target),
        "revertedPhase": receipt.get("phase"),
        "removed": removed,
        "restored": restored,
        "renamedBack": {"from": renamed["to"], "to": renamed["from"]} if renamed else None,
        "warnings": warnings,
    }


def prepare(
    target: Path, authority_mode: str | None = None, claude_md: str | None = None
) -> dict[str, object]:
    git = ensure_tool("git")
    ensure_tool("python")
    mode = detect_mode(target)

    # A receipt still marked "installing" means a previous run died before finishing.
    interrupted = load_receipt(target)
    if interrupted and interrupted.get("phase") == "installing":
        return {
            "ok": False,
            "phase": "preflight",
            "target": str(target),
            "interruptedInstall": {
                # `created` is empty on a real kill; the plan is what revert will act on.
                "planned": interrupted.get("planned", []),
                "modified": [item.get("path") for item in interrupted.get("modified", [])],
                "renamed": interrupted.get("renamed"),
            },
            "error": "A previous CTX404 installation was interrupted and left partial state",
            "next": (
                "Run `bootstrap.py revert --target <project>` to undo it, then install again. "
                "Do not install over partial state."
            ),
        }

    # Never touch an existing CLAUDE.md without an explicit decision. Whoever installs without
    # reading is exactly who must not have their own instruction file edited silently.
    review = review_claude_md(target) if mode == "adopt" else None
    if review and claude_md is None:
        return {
            "ok": True,
            "phase": "preflight",
            "mode": mode,
            "target": str(target),
            "gitInitialized": False,
            "claudeMdDecisionRequired": True,
            "claudeMd": review,
            "choices": ["rename", "keep", "cancel"],
            "recommended": "rename" if review["needsRename"] else "keep",
            "next": "Show the findings and ask. Make no project changes before an explicit decision.",
        }
    if review and claude_md == "rename" and review["needsRename"]:
        if git_dir(target) is None:
            result = run([git, "init"], target)
            if result.returncode != 0:
                raise BootstrapError(result.stderr.strip() or "git init failed")
        original_name = str(review["path"])
        rename_claude_md(target, original_name)
        save_receipt(
            target,
            {
                "version": CTX404_VERSION,
                "phase": "prepared",
                "renamed": {"from": original_name, "to": CLAUDE_MD},
                "created": [],
                "modified": [],
                "digests": {},
            },
        )
        review = review_claude_md(target)

    authorities = detect_authorities(target) if mode == "adopt" else []
    if authorities and authority_mode is None:
        return {
            "ok": True,
            "phase": "preflight",
            "mode": mode,
            "target": str(target),
            "gitInitialized": False,
            "claudeMd": review,
            "authorityDecisionRequired": True,
            "detectedAuthorities": authorities,
            "choices": ["index", "exclusive", "cancel"],
            "recommended": "index",
            "next": "Ask the user to choose. Make no project changes before an explicit decision.",
        }

    selected_authority_mode = authority_mode or "exclusive"

    created_git = False
    if git_dir(target) is None:
        result = run([git, "init"], target)
        if result.returncode != 0:
            raise BootstrapError(result.stderr.strip() or "git init failed")
        created_git = True

    # Context that Git ignores never reaches another machine, which is the whole promise.
    # There is no viable "install anyway": .git/info/exclude cannot override .gitignore, and
    # forcing every future topic with `git add -f` is not a state anyone can maintain.
    ignored = context_ignored(target)
    if ignored:
        return {
            "ok": False,
            "phase": "preflight",
            "mode": mode,
            "target": str(target),
            "gitInitialized": created_git,
            "contextIgnored": ignored,
            "recipe": list(IGNORE_RECIPE),
            "error": (
                f"Git ignores the CTX404 context: {ignored['source']}:{ignored['line']} "
                f"matches {ignored['pattern']}"
            ),
            "next": (
                "Show the offending rule and the replacement recipe, then stop. Installing while "
                "the context is ignored delivers nothing. Rerun prepare after the rule is fixed."
            ),
        }

    pending_path = require_git_dir(target) / PENDING_STATE
    if pending_path.exists():
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        mode = str(pending.get("mode", mode))
    pending_path.write_text(
        json.dumps(
            {
                "version": CTX404_VERSION,
                "phase": "ready-to-install",
                "mode": mode,
                "authorityMode": selected_authority_mode,
                "detectedAuthorities": authorities,
                "claudeMd": review,
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
        "authorityMode": selected_authority_mode,
        "detectedAuthorities": authorities,
        "claudeMd": review,
        "authorityDecisionRequired": False,
        "next": "Run the install phase. Native /init and recap remain optional user guidance afterward.",
    }


def copy_template(relative_path: str, target: Path, created: list[str]) -> None:
    source = TEMPLATES_ROOT / relative_path
    destination = target / relative_path
    if destination.exists():
        raise BootstrapError(f"Refusing to overwrite existing path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    created.append(relative_path.replace("\\", "/"))


def install_mode_label(mode: str) -> str:
    return "new repository bootstrap" if mode == "new" else "existing repository adoption"


def render_instructions(authority_mode: str) -> str:
    text = (TEMPLATES_ROOT / INSTRUCTIONS_FILE).read_text(encoding="utf-8")
    text = text.replace("{{CTX404_VERSION}}", CTX404_VERSION)
    return text.replace("{{AUTHORITY_POLICY}}", authority_policy(authority_mode))


def render_definition(project_name: str, mode_label: str) -> str:
    text = (TEMPLATES_ROOT / DEFINITION_FILE).read_text(encoding="utf-8")
    text = text.replace("{{PROJECT_NAME}}", project_name)
    return text.replace("{{INSTALL_MODE}}", mode_label)


def write_rendered(target: Path, relative: str, content: str, created: list[str]) -> None:
    destination = target / relative
    if destination.exists():
        raise BootstrapError(f"Refusing to overwrite existing path: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8", newline="\n")
    created.append(relative)


def render_managed_files(target: Path, mode: str, authority_mode: str, created: list[str]) -> None:
    write_rendered(target, INSTRUCTIONS_FILE, render_instructions(authority_mode), created)
    write_rendered(
        target, DEFINITION_FILE, render_definition(target.name, install_mode_label(mode)), created
    )


def consolidate_claude_md(target: Path, created: list[str], updated: list[str]) -> None:
    """Write the two-import CTX404 stub above whatever the project already had."""
    stub = (TEMPLATES_ROOT / "CLAUDE.governance.md").read_text(encoding="utf-8").strip()
    stub = stub.replace("{{CTX404_VERSION}}", CTX404_VERSION)
    claude_path = target / "CLAUDE.md"
    existing = read_utf8(claude_path).strip() if claude_path.exists() else ""

    if GOVERNANCE_START in existing or GOVERNANCE_END in existing:
        raise BootstrapError("CLAUDE.md already contains CTX404 governance markers")

    project_guidance = existing or "# Project Guidance\n\nProject-specific guidance will evolve as the project is defined."
    content = f"{stub}\n\n---\n\n{project_guidance}\n"
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

    # Allow only the CTX404 helper, which the protocol requires on every relevant completion.
    # Anything the user already allowed is preserved; nothing is ever denied or removed.
    template_allow = template.get("permissions", {}).get("allow", [])
    if template_allow:
        permissions = merged.setdefault("permissions", {})
        if not isinstance(permissions, dict):
            raise BootstrapError("Existing .claude/settings.json permissions must be a JSON object")
        allow = permissions.setdefault("allow", [])
        if not isinstance(allow, list):
            raise BootstrapError("Existing .claude/settings.json permissions.allow must be a JSON array")
        for rule in template_allow:
            if rule not in allow:
                allow.append(rule)

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


def render_initial_json(
    target: Path, mode: str, authority_mode: str, authorities: list[dict[str, str]]
) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    context_root = target / ".claude" / "context"
    index_path = context_root / "index.json"
    index_text = index_path.read_text(encoding="utf-8").replace("{{CTX404_VERSION}}", CTX404_VERSION)
    index = json.loads(index_text)
    index["project"]["name"] = target.name
    index["governance"] = {
        "mode": authority_mode,
        "authorities": authorities if authority_mode == "index" else [],
    }
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
        "refs": [item["path"] for item in authorities] if authority_mode == "index" else [],
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
    resolved_git = require_git_dir(target)

    interrupted = load_receipt(target)
    if interrupted and interrupted.get("phase") == "installing":
        raise BootstrapError(
            "A previous CTX404 installation was interrupted. Run the revert phase before installing again."
        )

    pending_path = resolved_git / PENDING_STATE
    if not pending_path.is_file():
        raise BootstrapError("CTX404 prepare state is missing. Run the prepare phase first.")
    pending = json.loads(pending_path.read_text(encoding="utf-8"))
    mode = str(pending.get("mode", "new"))
    authority_mode = str(pending.get("authorityMode", "exclusive"))
    authorities = pending.get("detectedAuthorities", [])
    if mode not in {"new", "adopt"}:
        raise BootstrapError(f"Unsupported CTX404 installation mode: {mode}")
    if authority_mode not in {"index", "exclusive"}:
        raise BootstrapError(f"Unsupported authority mode: {authority_mode}")
    if not isinstance(authorities, list):
        raise BootstrapError("Invalid detected-authority state")

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
        installed_index = json.loads((target / ".claude/context/index.json").read_text(encoding="utf-8"))
        installed_version = str(installed_index.get("ctx404Version", "unknown"))
        upgrade_available = installed_version != CTX404_VERSION
        pending_path.unlink()
        return {
            "ok": True,
            "phase": "install",
            "mode": mode,
            "authorityMode": authority_mode,
            "detectedAuthorities": authorities,
            "target": str(target),
            "alreadyInstalled": True,
            "installedVersion": installed_version,
            "skillVersion": CTX404_VERSION,
            "upgradeAvailable": upgrade_available,
            "created": [],
            "updated": [],
            "validation": json.loads(result.stdout),
            "restartRequired": False,
            "next": (
                "CTX404 is already installed and valid. Continue working normally."
                if not upgrade_available
                else "The project remains on its installed CTX404 version. No files were overlaid; a dedicated "
                "reviewed migration is required to adopt the newer project protocol."
            ),
        }

    conflicts = [
        relative for relative in MANAGED_FILES + RENDERED_FILES if (target / relative).exists()
    ]
    if conflicts:
        raise BootstrapError("Refusing to overwrite existing managed paths: " + ", ".join(conflicts))

    # Parse and validate the existing settings before any project file is changed.
    merged_settings(target)

    created: list[str] = []
    updated: list[str] = []
    backup_root = resolved_git / f"ctx404-backup-{uuid.uuid4().hex}"
    backup_existing(target, ("CLAUDE.md", ".claude/settings.json"), backup_root)

    # Every path this run may write, recorded before the first write. A killed process cannot
    # update a receipt on its way out, so the plan has to be complete up front: revert deletes
    # whichever planned paths exist. `created` is refined afterwards for the successful case.
    planned = [
        *( ["README.md"] if mode == "new" else [] ),
        *MANAGED_FILES,
        *RENDERED_FILES,
        "CLAUDE.md",
        ".claude/settings.json",
    ]
    previous = load_receipt(target) or {}
    receipt: dict[str, object] = {
        "version": CTX404_VERSION,
        "phase": "installing",
        "mode": mode,
        "target": str(target),
        "renamed": previous.get("renamed"),
        "planned": planned,
        "created": created,
        "modified": [
            {"path": relative, "backup": str(backup_root / relative)}
            for relative in ("CLAUDE.md", ".claude/settings.json")
            if (backup_root / relative).is_file()
        ],
        "digests": {},
    }
    save_receipt(target, receipt)
    try:
        if mode == "new":
            copy_template("README.md", target, created)
        for relative in MANAGED_FILES:
            copy_template(relative, target, created)
        render_managed_files(target, mode, authority_mode, created)
        write_settings(target, created, updated)
        consolidate_claude_md(target, created, updated)
        render_initial_json(target, mode, authority_mode, authorities)

        validator = target / ".claude" / "scripts" / "context_tool.py"
        result = run([sys.executable, str(validator), "validate", "--root", str(target)], target)
        if result.returncode != 0:
            raise BootstrapError(result.stdout.strip() or result.stderr.strip() or "Context validation failed")
        save_receipt(target, receipt)
    except Exception:
        rollback(target, created, backup_root)
        receipt_file = resolved_git / RECEIPT_STATE
        if receipt_file.is_file():
            receipt_file.unlink()
        raise

    # Keep the backups: revert needs them to restore a merged CLAUDE.md or settings.json.
    receipt["phase"] = "installed"
    receipt["digests"] = {
        relative: file_digest(target / relative)
        for relative in [*created, *updated]
        if file_digest(target / relative)
    }
    save_receipt(target, receipt)
    pending_path.unlink()

    return {
        "ok": True,
        "phase": "install",
        "mode": mode,
        "authorityMode": authority_mode,
        "detectedAuthorities": authorities,
        "target": str(target),
        "created": created,
        "updated": updated,
        "validation": json.loads(result.stdout),
        "restartRequired": True,
        "restartReason": (
            "The protocol file and the SessionStart and PreToolUse hooks are read only when a session "
            "starts. This session is still running without them: no status injection, no context gate, "
            "nothing recorded. Tell the user to restart the session, last and unmissably."
        ),
        "next": (
            "CTX404 is installed in a new repository. Refine the Project definition workspace from "
            "explicit user intent and verified evidence, then synchronize README.md and the context index. "
            "Native /init or a concise recap may be requested manually and reviewed first. "
            "Then report, ending with the restart warning."
            if mode == "new"
            else "CTX404 adopted this existing repository without retrospective analysis. Durable context "
            "starts after the session restart, not before. Optionally ask Claude for a concise, "
            "evidence-based project recap or run native /init manually, then review it before saving it "
            "as context."
        ),
    }


def read_installed_version(target: Path) -> str:
    index_path = target / ".claude/context/index.json"
    if not index_path.is_file():
        raise BootstrapError("CTX404 project index is missing")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    return str(index.get("ctx404Version", "unknown"))


def pending_hops(installed_version: str) -> list[tuple[str, str]]:
    """Ordered (from, to) hops needed to reach the current version."""
    if installed_version == CTX404_VERSION:
        return []
    if installed_version not in MIGRATION_CHAIN:
        raise BootstrapError(
            f"No reviewed migration path from {installed_version} to {CTX404_VERSION}"
        )
    start = MIGRATION_CHAIN.index(installed_version)
    return [
        (MIGRATION_CHAIN[position], MIGRATION_CHAIN[position + 1])
        for position in range(start, len(MIGRATION_CHAIN) - 1)
    ]


def hop_changes(hops: list[tuple[str, str]]) -> list[str]:
    changes: list[str] = []
    for source, destination in hops:
        if (source, destination) == (VERSION_020, VERSION_030):
            changes += [
                "CLAUDE.md authority policy",
                ".claude/context/index.json governance map",
            ]
        if (source, destination) == (VERSION_030, VERSION_040):
            changes += [
                f"CLAUDE.md governance block replaced by two imports ({INSTRUCTIONS_FILE}, {DEFINITION_FILE})",
                f"{INSTRUCTIONS_FILE} created with the always-loaded core protocol",
                f"{DEFINITION_FILE} created from the existing project definition",
                f"{CONTEXT_RULE_FILE} created as a path-scoped rule",
                ".claude/settings.json gains an allow rule for the CTX404 helper",
            ]
        if (source, destination) == (VERSION_040, CTX404_VERSION):
            changes += [
                ".claude/hooks/context_gate.py added: a Stop hook that blocks a session "
                "which deliberated without recording",
                ".claude/settings.json gains the Stop hook",
                f"{INSTRUCTIONS_FILE} now counts deliberation, and rejected options, as durable context",
                f"{CONTEXT_RULE_FILE} gains the deliberation record and the review command",
            ]
    return changes + ["managed helper, hooks, agents and templates refreshed", "history checkpoint"]


def upgrade_plan(target: Path, authority_mode: str | None = None) -> dict[str, object]:
    installed_version = read_installed_version(target)
    authorities = detect_authorities(target)
    hops = pending_hops(installed_version)
    if not hops:
        return {
            "ok": True,
            "phase": "upgrade-plan",
            "target": str(target),
            "installedVersion": installed_version,
            "targetVersion": CTX404_VERSION,
            "upgradeRequired": False,
            "changes": [],
        }
    # Only the 0.2.0 hop introduces the authority decision; later hops reuse the recorded mode.
    decision_required = (
        (VERSION_020, VERSION_030) in hops and bool(authorities) and authority_mode is None
    )
    plan: dict[str, object] = {
        "ok": True,
        "phase": "upgrade-plan",
        "target": str(target),
        "installedVersion": installed_version,
        "targetVersion": CTX404_VERSION,
        "upgradeRequired": True,
        "hops": [f"{source} -> {destination}" for source, destination in hops],
        "detectedAuthorities": authorities,
        "changes": hop_changes(hops),
    }
    if decision_required:
        plan.update(
            {
                "authorityDecisionRequired": True,
                "choices": ["index", "exclusive", "cancel"],
                "recommended": "index",
            }
        )
        return plan
    plan.update(
        {
            "authorityDecisionRequired": False,
            "authorityMode": authority_mode or "exclusive",
            "preserved": [
                "current state",
                "topics",
                "project definition",
                "existing guidance",
                "project files",
            ],
        }
    )
    return plan


def hop_020_to_030(target: Path, selected_mode: str, authorities: list) -> None:
    """Rewrite the legacy authority policy; the block still lives inside CLAUDE.md."""
    claude_path = target / "CLAUDE.md"
    claude = claude_path.read_text(encoding="utf-8")
    old_marker = f'<!-- ctx404:governance:start version="{VERSION_020}" schema="1" -->'
    new_marker = f'<!-- ctx404:governance:start version="{VERSION_030}" schema="1" -->'
    if old_marker not in claude:
        raise BootstrapError("Expected legacy governance marker was not found; refusing migration")
    if LEGACY_AUTHORITY_TEXT not in claude:
        raise BootstrapError("Legacy authority policy was customized; manual migration is required")

    new_policy = (
        "Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, "
        "Git-versioned continuity system.\n\n" + authority_policy(selected_mode)
    )
    claude_path.write_text(
        claude.replace(old_marker, new_marker, 1).replace(LEGACY_AUTHORITY_TEXT, new_policy, 1),
        encoding="utf-8",
        newline="\n",
    )
    index_path = target / ".claude/context/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["ctx404Version"] = VERSION_030
    index["governance"] = {
        "mode": selected_mode,
        "authorities": authorities if selected_mode == "index" else [],
    }
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hop_030_to_040(target: Path, selected_mode: str, created: list[str], warnings: list[str]) -> None:
    """Move the inline governance block out of CLAUDE.md into managed and owned files."""
    claude_path = target / "CLAUDE.md"
    claude = claude_path.read_text(encoding="utf-8")
    block_pattern = re.compile(
        re.escape(GOVERNANCE_START) + r".*?" + re.escape(GOVERNANCE_END), re.DOTALL
    )
    match = block_pattern.search(claude)
    if not match:
        raise BootstrapError("CTX404 governance block was not found in CLAUDE.md; refusing migration")
    block = match.group(0)

    name_match = re.search(r"^- Project name: `([^`]*)`", block, re.MULTILINE)
    mode_match = re.search(r"^- Installation mode: `([^`]*)`", block, re.MULTILINE)
    project_name = name_match.group(1) if name_match else target.name
    mode_label = mode_match.group(1) if mode_match else install_mode_label("adopt")
    if not name_match or not mode_match:
        warnings.append("Project identity was incomplete in the old block; derived it from the folder")

    definition = render_definition(project_name, mode_label)
    start = block.find(DEFINITION_START)
    end = block.find(DEFINITION_END)
    if start != -1 and end != -1 and end > start:
        preserved = block[start + len(DEFINITION_START) : end].strip()
        template_start = definition.find(DEFINITION_START) + len(DEFINITION_START)
        template_end = definition.find(DEFINITION_END)
        definition = definition[:template_start] + f"\n\n{preserved}\n\n" + definition[template_end:]
    else:
        warnings.append("Project definition markers were missing; wrote the default workspace instead")

    write_rendered(target, INSTRUCTIONS_FILE, render_instructions(selected_mode), created)
    write_rendered(target, DEFINITION_FILE, definition, created)
    copy_template(CONTEXT_RULE_FILE, target, created)

    stub = (TEMPLATES_ROOT / "CLAUDE.governance.md").read_text(encoding="utf-8").strip()
    stub = stub.replace("{{CTX404_VERSION}}", CTX404_VERSION)
    claude_path.write_text(
        block_pattern.sub(lambda _: stub, claude, count=1), encoding="utf-8", newline="\n"
    )

    # 0.4.0 allows the helper the protocol depends on; merge it without touching other settings.
    settings_path = target / ".claude" / "settings.json"
    if settings_path.is_file():
        settings_path.write_text(
            json.dumps(merged_settings(target), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    index_path = target / ".claude/context/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["ctx404Version"] = CTX404_VERSION
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hop_040_to_040_beta2(target: Path, selected_mode: str) -> None:
    """Give the protocol a way to enforce itself.

    Until now reading context was a hook and writing it was a request in prose. A session
    that only deliberated - no file touched, so no diff to notice - ended with the reasoning
    left in the chat, which is exactly the loss the project exists to prevent. This hop adds
    the Stop gate and teaches the protocol that a rejected option is context worth keeping.
    """
    instructions_path = target / INSTRUCTIONS_FILE
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    instructions_path.write_text(render_instructions(selected_mode), encoding="utf-8", newline="\n")

    # The rule and the hooks arrive through REFRESHABLE_FILES; only the version marker is manual.
    claude_path = target / "CLAUDE.md"
    if claude_path.is_file():
        content = claude_path.read_text(encoding="utf-8")
        claude_path.write_text(
            re.sub(
                r'(<!-- ctx404:governance:start version=")[^"]+(")',
                lambda match: match.group(1) + CTX404_VERSION + match.group(2),
                content,
                count=1,
            ),
            encoding="utf-8",
            newline="\n",
        )

    settings_path = target / ".claude" / "settings.json"
    if settings_path.is_file():
        settings_path.write_text(
            json.dumps(merged_settings(target), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    index_path = target / ".claude/context/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["ctx404Version"] = CTX404_VERSION
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalized(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def refresh_managed_files(target: Path) -> list[str]:
    """Overwrite managed implementation files whose installed copy differs from the skill."""
    changed: list[str] = []
    for relative in REFRESHABLE_FILES:
        source = TEMPLATES_ROOT / relative
        destination = target / relative
        if not source.is_file():
            continue
        incoming = source.read_bytes()
        # Compare normalized text: a checkout differing only in line endings is not a change,
        # and rewriting it would churn the user's diff for nothing.
        if destination.is_file() and normalized(destination.read_bytes()) == normalized(incoming):
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(incoming)
        changed.append(relative)
    return changed


def upgrade_apply(target: Path, authority_mode: str | None) -> dict[str, object]:
    plan = upgrade_plan(target, authority_mode)
    if not plan.get("upgradeRequired"):
        return {**plan, "phase": "upgrade-apply", "applied": False}
    if plan.get("authorityDecisionRequired"):
        raise BootstrapError("Authority decision is required before upgrade")
    installed_version = str(plan["installedVersion"])
    authorities = plan["detectedAuthorities"]
    hops = pending_hops(installed_version)

    claude_path = target / "CLAUDE.md"
    index_path = target / ".claude/context/index.json"
    history_path = target / ".claude/context/history.jsonl"
    validator = target / ".claude/scripts/context_tool.py"
    if not all(path.is_file() for path in (claude_path, index_path, history_path, validator)):
        raise BootstrapError("Installed CTX404 project is incomplete; refusing migration")

    # Only the 0.2.0 hop asks for a decision; a project already on 0.3.0 carries its recorded mode.
    recorded = json.loads(index_path.read_text(encoding="utf-8")).get("governance", {})
    selected_mode = str(plan.get("authorityMode") or recorded.get("mode") or "exclusive")

    created: list[str] = []
    refreshed: list[str] = []
    warnings: list[str] = []
    backup_root = require_git_dir(target) / f"ctx404-upgrade-backup-{uuid.uuid4().hex}"
    backup_existing(
        target,
        ("CLAUDE.md", ".claude/context/index.json", ".claude/context/history.jsonl",
         ".claude/settings.json")
        + REFRESHABLE_FILES,
        backup_root,
    )
    try:
        for source, destination in hops:
            if (source, destination) == (VERSION_020, VERSION_030):
                hop_020_to_030(target, selected_mode, authorities)
            elif (source, destination) == (VERSION_030, VERSION_040):
                hop_030_to_040(target, selected_mode, created, warnings)
            elif (source, destination) == (VERSION_040, CTX404_VERSION):
                hop_040_to_040_beta2(target, selected_mode)
            else:
                raise BootstrapError(f"No reviewed migration step from {source} to {destination}")

        # Refresh before validating, so the doctor that runs is the one this version ships.
        refreshed = refresh_managed_files(target)

        event = {
            "at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "type": "upgrade",
            "summary": f"CTX404 project protocol upgraded from {installed_version} to {CTX404_VERSION}",
            "refs": [item["path"] for item in authorities] if selected_mode == "index" else [],
        }
        with history_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

        result = run([sys.executable, str(validator), "doctor", "--root", str(target)], target)
        if result.returncode != 0:
            raise BootstrapError(result.stdout.strip() or result.stderr.strip() or "Post-upgrade validation failed")
        validation = json.loads(result.stdout)
        if not validation.get("ok"):
            raise BootstrapError("Post-upgrade doctor reported issues")
    except Exception:
        rollback(target, created, backup_root)
        raise
    if backup_root.exists():
        shutil.rmtree(backup_root)

    return {
        "ok": True,
        "phase": "upgrade-apply",
        "target": str(target),
        "applied": True,
        "fromVersion": installed_version,
        "toVersion": CTX404_VERSION,
        "hops": [f"{source} -> {destination}" for source, destination in hops],
        "authorityMode": selected_mode,
        "detectedAuthorities": authorities,
        "created": created,
        "refreshed": refreshed,
        "warnings": warnings,
        "validation": validation,
        "preserved": plan["preserved"],
        "restartRequired": True,
        "restartReason": (
            "The refreshed protocol file and hooks are read only when a session starts. This session is "
            "still running the previous version. Tell the user to restart the session, last and "
            "unmissably."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="phase", required=True)
    for phase in ("prepare", "install", "upgrade-plan", "upgrade-apply", "revert"):
        command = subparsers.add_parser(phase)
        command.add_argument("--target", default=".", help="Project directory (default: current directory)")
        if phase in {"prepare", "upgrade-plan", "upgrade-apply"}:
            command.add_argument("--authority-mode", choices=("index", "exclusive"))
        if phase == "prepare":
            command.add_argument("--claude-md", choices=("rename", "keep"))
        if phase == "revert":
            command.add_argument("--force", action="store_true",
                                 help="Discard later changes to files CTX404 created")
    args = parser.parse_args()

    try:
        target = resolve_target(args.target)
        if args.phase == "prepare":
            result = prepare(target, args.authority_mode, args.claude_md)
        elif args.phase == "install":
            result = install(target)
        elif args.phase == "revert":
            result = revert(target, args.force)
        elif args.phase == "upgrade-plan":
            result = upgrade_plan(target, args.authority_mode)
        else:
            result = upgrade_apply(target, args.authority_mode)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except (BootstrapError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
