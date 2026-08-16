#!/usr/bin/env python3
"""Install CTX404 into a user-level Claude Code skills directory."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parent.parent
INSTALL_ITEMS = ("SKILL.md", "scripts", "assets", "references")


class InstallError(RuntimeError):
    pass


def copy_item(name: str, destination: Path) -> None:
    source = SOURCE_ROOT / name
    target = destination / name
    if not source.exists():
        raise InstallError(f"Missing source item: {source}")
    if source.is_dir():
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-root",
        default=str(Path.home() / ".claude" / "skills"),
        help="Claude Code skills directory (default: ~/.claude/skills)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing CTX404 installation transactionally.",
    )
    args = parser.parse_args()

    try:
        skills_root = Path(args.skills_root).expanduser().resolve()
        destination = skills_root / "ctx404"
        if destination.exists() and not args.force:
            raise InstallError(
                f"Destination already exists: {destination}. "
                "Re-run with --force to replace it safely."
            )
        skills_root.mkdir(parents=True, exist_ok=True)
        nonce = uuid.uuid4().hex
        staging = skills_root / f".ctx404-install-{nonce}"
        backup = skills_root / f".ctx404-backup-{nonce}"
        staging.mkdir()
        try:
            for name in INSTALL_ITEMS:
                copy_item(name, staging)

            replaced = destination.exists()
            if replaced:
                destination.rename(backup)
            try:
                staging.rename(destination)
            except Exception:
                if backup.exists() and not destination.exists():
                    backup.rename(destination)
                raise
            if backup.exists():
                shutil.rmtree(backup)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise

        result = {
            "ok": True,
            "installedAt": str(destination),
            "replacedExisting": replaced,
            "command": "/ctx404",
            "restartHint": (
                "Restart Claude Code if the skill is not immediately discovered. "
                "Restart again after /ctx404 finishes in a project: the installed protocol and hooks "
                "are read only when a session starts, so the session that installed them is not "
                "governed by them and records nothing."
            ),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (InstallError, OSError, shutil.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
