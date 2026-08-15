from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap.py"
INSTALLER = ROOT / "scripts" / "install.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
INSTRUCTIONS = ".claude/ctx404-instructions.md"
DEFINITION = ".claude/context/project-definition.md"
CONTEXT_RULE = ".claude/rules/ctx404-context.md"
# Always-loaded footprint budget. The split exists to keep this small; guard it against regression.
CORE_BUDGET_CHARS = 4200
# Kept in step with bootstrap.CTX404_VERSION; the migration chain asserts on it below.
CURRENT_VERSION = "0.4.0-beta.2"
PREVIOUS_VERSION = "0.4.0-beta.1"

LEGACY_AUTHORITY_TEXT = (
    "Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, "
    "Git-versioned memory system and the only durable project-context authority."
)
CURRENT_AUTHORITY_TEXT = (
    "Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, "
    "Git-versioned continuity system.\n\n"
    "`.claude/context/` is the primary durable project-context authority. Any prior context or planning "
    "system may be migrated or retired only through explicit user-approved work; installation itself "
    "does not delete or rewrite it."
)


def run_python(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *(str(arg) for arg in args)],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def legacy_claude_md(version: str, project_name: str, purpose: str) -> str:
    """Rebuild a pre-0.4.0 CLAUDE.md, where the whole protocol lived inline."""
    block = (FIXTURES / "governance-0.3.0.md").read_text(encoding="utf-8").strip()
    block = block.replace("{{CTX404_VERSION}}", version)
    block = block.replace("{{PROJECT_NAME}}", project_name)
    block = block.replace("{{INSTALL_MODE}}", "new repository bootstrap")
    policy = LEGACY_AUTHORITY_TEXT if version == "0.2.0-beta.1" else CURRENT_AUTHORITY_TEXT
    block = block.replace("{{AUTHORITY_POLICY}}", "")
    block = block.replace(
        "Claude Code auto memory is disabled for this project. `.claude/context/` is the portable, "
        "Git-versioned continuity system.",
        policy,
        1,
    )
    block = block.replace("Purpose: pending definition", f"Purpose: {purpose}", 1)
    guidance = "# Project Guidance\n\nProject-specific guidance will evolve as the project is defined."
    return f"{block}\n\n---\n\n{guidance}\n"


def downgrade_install(target: Path, version: str, purpose: str, drop_governance: bool) -> None:
    """Turn a freshly installed 0.4.0 project back into a pre-0.4.0 one for migration tests."""
    (target / "CLAUDE.md").write_text(
        legacy_claude_md(version, target.name, purpose), encoding="utf-8", newline="\n"
    )
    for relative in (INSTRUCTIONS, DEFINITION, CONTEXT_RULE):
        (target / relative).unlink()
    index_path = target / ".claude/context/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["ctx404Version"] = version
    if drop_governance:
        index.pop("governance", None)
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


class BootstrapTests(unittest.TestCase):
    def test_prepare_initializes_git_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            first = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            self.assertTrue((target / ".git").is_dir())

            second = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)
            self.assertTrue((target / ".git" / "ctx404-pending.json").is_file())

    def test_prepare_detects_existing_project_without_changing_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "existing.txt").write_text("keep", encoding="utf-8")
            result = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(result.stdout)["mode"], "adopt")
            self.assertEqual((target / "existing.txt").read_text(encoding="utf-8"), "keep")

    def test_prepare_stops_before_git_when_existing_authority_needs_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = target / ".planning" / "STATE.md"
            state.parent.mkdir()
            state.write_text("# Existing state\n", encoding="utf-8")

            result = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["authorityDecisionRequired"])
            self.assertEqual(payload["recommended"], "index")
            self.assertIn({"path": ".planning/STATE.md", "kind": "project-state"}, payload["detectedAuthorities"])
            self.assertFalse((target / ".git").exists())
            self.assertEqual(state.read_text(encoding="utf-8"), "# Existing state\n")

    def test_prepare_gates_on_an_existing_claude_md_and_offers_the_rename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            # The SPALLA shape: lowercase file, own governance, rules linking their own records.
            (target / "checkpoint.md").write_text("# Checkpoint\n", encoding="utf-8")
            (target / "changelog.md").write_text("# Changelog\n", encoding="utf-8")
            (target / "roadmap.md").write_text("# Roadmap\n", encoding="utf-8")
            (target / "claude.md").write_text(
                "# Rules\n\n"
                "Regra 1: registre em [`changelog.md`](changelog.md).\n"
                "Regra 2: mantenha o [`checkpoint.md`](checkpoint.md) vivo.\n"
                "Regra 3: tarefas em `roadmap.md`.\n"
                "Veja tambem https://example.com/other.md e ../fora.md\n",
                encoding="utf-8",
            )

            gated = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(gated.returncode, 0, gated.stderr + gated.stdout)
            payload = json.loads(gated.stdout)
            self.assertTrue(payload["claudeMdDecisionRequired"])
            self.assertEqual(payload["claudeMd"]["path"], "claude.md")
            self.assertTrue(payload["claudeMd"]["needsRename"])
            self.assertEqual(
                payload["claudeMd"]["linkedDocs"], ["changelog.md", "checkpoint.md", "roadmap.md"]
            )
            self.assertEqual(payload["recommended"], "rename")
            # Nothing may happen before the user answers.
            self.assertFalse((target / ".git").exists())

            renamed = run_python(BOOTSTRAP, "prepare", "--target", target, "--claude-md", "rename")
            self.assertEqual(renamed.returncode, 0, renamed.stderr + renamed.stdout)
            after = json.loads(renamed.stdout)
            self.assertTrue(after["authorityDecisionRequired"])
            # The linked records become authorities, so the existing decision gate covers them.
            paths = [item["path"] for item in after["detectedAuthorities"]]
            self.assertEqual(paths, ["changelog.md", "checkpoint.md", "roadmap.md"])
            self.assertEqual(after["recommended"], "index")
            self.assertEqual(
                sorted(p.name for p in target.iterdir() if p.suffix == ".md"),
                ["CLAUDE.md", "changelog.md", "checkpoint.md", "roadmap.md"],
            )

    def test_prepare_does_not_regate_a_project_already_running_ctx404(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)

            again = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(again.returncode, 0, again.stderr + again.stdout)
            payload = json.loads(again.stdout)
            self.assertNotIn("claudeMdDecisionRequired", payload)
            self.assertIsNone(payload["claudeMd"])

    def test_prepare_refuses_when_git_ignores_the_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app.py").write_text("x\n", encoding="utf-8")
            (target / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)

            result = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["contextIgnored"]["pattern"], ".claude/")
            self.assertEqual(payload["contextIgnored"]["source"], ".gitignore")
            # `.claude/` cannot be negated, so the recipe has to switch to `.claude/*`.
            self.assertEqual(payload["recipe"][0], ".claude/*")
            self.assertIn("!.claude/context/", payload["recipe"])
            self.assertIn("!.claude/settings.json", payload["recipe"])
            self.assertFalse((target / ".claude").exists())

            (target / ".gitignore").write_text(
                "\n".join(payload["recipe"]) + "\n", encoding="utf-8"
            )
            fixed = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(fixed.returncode, 0, fixed.stderr + fixed.stdout)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)
            check = subprocess.run(
                ["git", "check-ignore", "-q", ".claude/context/index.json"],
                cwd=target,
                check=False,
            )
            self.assertNotEqual(check.returncode, 0, "context must be versionable after the fix")

    def test_prepare_refuses_a_non_utf8_claude_md_without_a_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app.py").write_text("x\n", encoding="utf-8")
            (target / "CLAUDE.md").write_bytes("# Regras\n\nconfiguração\n".encode("cp1252"))

            result = run_python(BOOTSTRAP, "prepare", "--target", target, "--claude-md", "keep")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("Traceback", result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("not valid UTF-8", payload["error"])
            self.assertFalse((target / ".claude").exists())

    def test_install_works_inside_a_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            main = Path(directory) / "main"
            main.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=main, check=True)
            (main / "a.txt").write_text("x\n", encoding="utf-8")
            for command in (
                ["git", "add", "-A"],
                ["git", "-c", "user.email=a@b", "-c", "user.name=c", "commit", "-qm", "i"],
                ["git", "worktree", "add", "-q", str(Path(directory) / "wt"), "-b", "feat"],
            ):
                subprocess.run(command, cwd=main, check=True)
            worktree = Path(directory) / "wt"
            # In a worktree `.git` is a file, so the Git directory must be resolved, not assumed.
            self.assertTrue((worktree / ".git").is_file())

            prepared = run_python(BOOTSTRAP, "prepare", "--target", worktree)
            self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
            installed = run_python(BOOTSTRAP, "install", "--target", worktree)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            self.assertTrue(json.loads(installed.stdout)["validation"]["ok"])
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=main, check=False)

    def test_doctor_warns_when_the_context_becomes_ignored_later(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)
            helper = target / ".claude" / "scripts" / "context_tool.py"
            self.assertEqual(json.loads(run_python(helper, "doctor", cwd=target).stdout)["warnings"], [])

            # Someone adds the rule months after installation.
            (target / ".gitignore").write_text(".claude/\n", encoding="utf-8")
            later = json.loads(run_python(helper, "doctor", cwd=target).stdout)
            self.assertTrue(any("Git ignores the context" in w for w in later["warnings"]))
            # A warning, not a failure: it must not block ordinary work.
            self.assertTrue(later["ok"])

    def test_revert_undoes_an_adoption_and_restores_the_original_claude_md(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            guidance = "# My rules\n\nKeep Decimal arithmetic.\n"
            (target / "app.py").write_text("print('keep')\n", encoding="utf-8")
            (target / "claude.md").write_text(guidance, encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            subprocess.run(["git", "add", "-A"], cwd=target, check=True)
            subprocess.run(
                ["git", "-c", "user.email=a@b", "-c", "user.name=c", "commit", "-qm", "i"],
                cwd=target, check=True,
            )

            run_python(BOOTSTRAP, "prepare", "--target", target, "--claude-md", "rename")
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)
            self.assertTrue((target / ".claude").is_dir())

            reverted = run_python(BOOTSTRAP, "revert", "--target", target)
            self.assertEqual(reverted.returncode, 0, reverted.stderr + reverted.stdout)
            payload = json.loads(reverted.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["revertedPhase"], "installed")

            # The project must look untouched: no CTX404 files, original name and content back.
            self.assertFalse((target / ".claude").exists())
            self.assertEqual((target / "app.py").read_text(encoding="utf-8"), "print('keep')\n")
            names = sorted(p.name for p in target.iterdir() if p.name != ".git")
            self.assertEqual(names, ["app.py", "claude.md"])
            self.assertEqual((target / "claude.md").read_text(encoding="utf-8"), guidance)
            self.assertEqual(
                subprocess.run(["git", "status", "--short"], cwd=target, capture_output=True, text=True).stdout,
                "",
            )

    def test_revert_refuses_when_a_created_file_changed_afterwards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)

            definition = target / DEFINITION
            definition.write_text(
                definition.read_text(encoding="utf-8").replace(
                    "Purpose: pending definition", "Purpose: real work happened here"
                ),
                encoding="utf-8",
            )

            refused = run_python(BOOTSTRAP, "revert", "--target", target)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("changed after installation", json.loads(refused.stdout)["error"])
            self.assertTrue(definition.is_file(), "nothing may be deleted when revert refuses")

            forced = run_python(BOOTSTRAP, "revert", "--target", target, "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr + forced.stdout)
            self.assertFalse((target / ".claude").exists())

    def test_an_interrupted_install_is_detected_and_revertible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app.py").write_text("x\n", encoding="utf-8")
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)

            # Reproduce what a killed process actually leaves: the receipt is written before any
            # file lands, so `created` is empty and only `planned` describes the damage. An
            # earlier version of this test flipped `phase` on a finished receipt, which tested a
            # state that cannot occur and hid the fact that revert had nothing to undo.
            git_dir = Path(
                subprocess.run(
                    ["git", "rev-parse", "--absolute-git-dir"],
                    cwd=target, capture_output=True, text=True, check=True,
                ).stdout.strip()
            )
            receipt_path = git_dir / "ctx404-receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertTrue(receipt["planned"], "the plan must be recorded before any write")
            receipt["phase"] = "installing"
            receipt["created"] = []
            receipt["digests"] = {}
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            blocked = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertNotEqual(blocked.returncode, 0)
            payload = json.loads(blocked.stdout)
            self.assertIn("interrupted", payload["error"])
            self.assertIn("revert", payload["next"])
            self.assertTrue(payload["interruptedInstall"]["planned"])

            # Installing over partial state must be refused too, not just prepare.
            self.assertNotEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)

            recovered = run_python(BOOTSTRAP, "revert", "--target", target, "--force")
            self.assertEqual(recovered.returncode, 0, recovered.stderr + recovered.stdout)
            self.assertTrue(json.loads(recovered.stdout)["removed"], "revert must undo the plan")
            self.assertFalse((target / ".claude").exists())
            self.assertFalse((target / "CLAUDE.md").exists())
            self.assertFalse(receipt_path.exists())
            self.assertFalse(list(git_dir.glob("ctx404-*backup-*")))

            # And the project installs cleanly afterwards.
            self.assertEqual(run_python(BOOTSTRAP, "prepare", "--target", target).returncode, 0)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)

    def test_index_mode_preserves_and_registers_existing_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = target / ".planning" / "STATE.md"
            state.parent.mkdir()
            state.write_text("# Existing state\n", encoding="utf-8")

            prepared = run_python(
                BOOTSTRAP, "prepare", "--target", target, "--authority-mode", "index"
            )
            self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            payload = json.loads(installed.stdout)
            self.assertEqual(payload["authorityMode"], "index")
            self.assertEqual(state.read_text(encoding="utf-8"), "# Existing state\n")

            index = json.loads((target / ".claude/context/index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["governance"]["mode"], "index")
            self.assertIn(
                {"path": ".planning/STATE.md", "kind": "project-state"},
                index["governance"]["authorities"],
            )
            instructions = (target / INSTRUCTIONS).read_text(encoding="utf-8")
            self.assertIn("routing and continuity layer", instructions)
            self.assertNotIn("routing and continuity layer", (target / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_new_install_creates_governance_directly_without_init(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            prepared = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(prepared.returncode, 0, prepared.stdout)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            payload = json.loads(installed.stdout)
            self.assertTrue(payload["validation"]["ok"])

            governance = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("ctx404:governance:start", governance)
            self.assertEqual(governance.count("ctx404:governance:start"), 1)
            self.assertIn("@.claude/ctx404-instructions.md", governance)
            self.assertIn("@.claude/context/project-definition.md", governance)
            # The protocol body must no longer sit in the user's own file.
            self.assertNotIn("Start every session", governance)
            self.assertNotIn("Route work by cost", governance)
            self.assertLess(len(governance), 800, "CTX404 stub grew back into the user's CLAUDE.md")

            self.assertIn("Start every session", (target / INSTRUCTIONS).read_text(encoding="utf-8"))
            self.assertIn("Definition workspace", (target / DEFINITION).read_text(encoding="utf-8"))
            self.assertIn('paths:', (target / CONTEXT_RULE).read_text(encoding="utf-8"))

            helper = target / ".claude" / "scripts" / "context_tool.py"
            doctor = run_python(helper, "doctor", cwd=target)
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertTrue(json.loads(doctor.stdout)["ok"])

            index = json.loads((target / ".claude" / "context" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["project"]["name"], target.name)

    def test_adopt_preserves_existing_project_and_merges_governance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            readme = "# Existing calculator\n\nDo not replace this.\n"
            guidance = "# Calculator rules\n\nKeep Decimal arithmetic.\n"
            app = "print('calculator')\n"
            (target / "README.md").write_text(readme, encoding="utf-8")
            (target / "CLAUDE.md").write_text(guidance, encoding="utf-8")
            (target / "app.py").write_text(app, encoding="utf-8")
            settings_path = target / ".claude" / "settings.json"
            settings_path.parent.mkdir()
            existing_hook = {
                "matcher": "Write",
                "hooks": [{"type": "command", "command": "python", "args": ["tools/check.py"]}],
            }
            settings_path.write_text(
                json.dumps({"permissions": {"allow": ["Read"]}, "hooks": {"PostToolUse": [existing_hook]}}),
                encoding="utf-8",
            )

            gated = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(gated.returncode, 0, gated.stderr + gated.stdout)
            self.assertTrue(json.loads(gated.stdout)["claudeMdDecisionRequired"])
            self.assertFalse((target / ".git").exists())

            prepared = run_python(BOOTSTRAP, "prepare", "--target", target, "--claude-md", "keep")
            self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
            self.assertEqual(json.loads(prepared.stdout)["mode"], "adopt")
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            payload = json.loads(installed.stdout)
            self.assertEqual(payload["mode"], "adopt")
            self.assertTrue(payload["validation"]["ok"])

            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), readme)
            self.assertEqual((target / "app.py").read_text(encoding="utf-8"), app)
            merged_guidance = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn(guidance.strip(), merged_guidance)
            self.assertEqual(merged_guidance.count("ctx404:governance:start"), 1)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            # The user's own rules survive; CTX404 only appends an allow for its helper.
            self.assertEqual(settings["permissions"]["allow"][0], "Read")
            self.assertIn(
                "Bash(python .claude/scripts/context_tool.py:*)", settings["permissions"]["allow"]
            )
            self.assertNotIn("deny", settings["permissions"])
            self.assertEqual(settings["hooks"]["PostToolUse"], [existing_hook])
            self.assertIn("SessionStart", settings["hooks"])
            self.assertIn("PreToolUse", settings["hooks"])
            self.assertFalse(settings["autoMemoryEnabled"])

            current = json.loads((target / ".claude" / "context" / "current.json").read_text(encoding="utf-8"))
            self.assertEqual(current["status"], "active")
            self.assertIn("adopted an existing repository", current["lastCompleted"])
            history = json.loads((target / ".claude" / "context" / "history.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(history["type"], "adopt")

    def test_adopt_refuses_managed_path_conflict_without_partial_install(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app.py").write_text("print('keep')\n", encoding="utf-8")
            conflict = target / ".claude" / "agents" / "context-scout.md"
            conflict.parent.mkdir(parents=True)
            conflict.write_text("custom agent\n", encoding="utf-8")
            prepared = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertNotEqual(installed.returncode, 0)
            self.assertEqual(conflict.read_text(encoding="utf-8"), "custom agent\n")
            self.assertFalse((target / "CLAUDE.md").exists())
            self.assertFalse((target / ".claude" / "context").exists())

    def test_second_install_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app.py").write_text("print('keep')\n", encoding="utf-8")
            first_prepare = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(first_prepare.returncode, 0, first_prepare.stderr + first_prepare.stdout)
            first_install = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(first_install.returncode, 0, first_install.stderr + first_install.stdout)
            first_claude = (target / "CLAUDE.md").read_text(encoding="utf-8")

            second_prepare = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(second_prepare.returncode, 0, second_prepare.stderr + second_prepare.stdout)
            second_install = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(second_install.returncode, 0, second_install.stderr + second_install.stdout)
            self.assertTrue(json.loads(second_install.stdout)["alreadyInstalled"])
            self.assertEqual((target / "CLAUDE.md").read_text(encoding="utf-8"), first_claude)

    def test_reinstall_reports_version_drift_without_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            prepared = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)

            downgrade_install(target, "0.2.0-beta.1", "pending definition", drop_governance=False)
            claude_path = target / "CLAUDE.md"
            before = claude_path.read_text(encoding="utf-8")

            second_prepare = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(second_prepare.returncode, 0, second_prepare.stderr + second_prepare.stdout)
            second_install = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(second_install.returncode, 0, second_install.stderr + second_install.stdout)
            payload = json.loads(second_install.stdout)
            self.assertTrue(payload["alreadyInstalled"])
            self.assertTrue(payload["upgradeAvailable"])
            self.assertEqual(payload["installedVersion"], "0.2.0-beta.1")
            self.assertEqual(payload["skillVersion"], CURRENT_VERSION)
            self.assertEqual(claude_path.read_text(encoding="utf-8"), before)

    def test_reviewed_upgrade_migrates_v02_without_losing_project_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            prepared = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(prepared.returncode, 0, prepared.stderr + prepared.stdout)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)

            index_path = target / ".claude/context/index.json"
            claude_path = target / "CLAUDE.md"
            downgrade_install(
                target, "0.2.0-beta.1", "preserve this custom definition", drop_governance=True
            )
            current_before = (target / ".claude/context/current.json").read_text(encoding="utf-8")

            plan = run_python(
                BOOTSTRAP, "upgrade-plan", "--target", target, "--authority-mode", "exclusive"
            )
            self.assertEqual(plan.returncode, 0, plan.stderr + plan.stdout)
            planned = json.loads(plan.stdout)
            self.assertTrue(planned["upgradeRequired"])
            self.assertEqual(
                planned["hops"],
                [
                    "0.2.0-beta.1 -> 0.3.0-beta.1",
                    f"0.3.0-beta.1 -> {PREVIOUS_VERSION}",
                    f"{PREVIOUS_VERSION} -> {CURRENT_VERSION}",
                ],
            )

            applied = run_python(
                BOOTSTRAP, "upgrade-apply", "--target", target, "--authority-mode", "exclusive"
            )
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)
            payload = json.loads(applied.stdout)
            self.assertTrue(payload["applied"])
            self.assertTrue(payload["validation"]["ok"])
            self.assertEqual(payload["warnings"], [])
            self.assertEqual(
                (target / ".claude/context/current.json").read_text(encoding="utf-8"), current_before
            )

            migrated_claude = claude_path.read_text(encoding="utf-8")
            # The inline block must be gone and replaced by the stub.
            self.assertNotIn("Start every session", migrated_claude)
            self.assertNotIn("Context boundaries", migrated_claude)
            self.assertEqual(migrated_claude.count("ctx404:governance:start"), 1)
            self.assertIn(f'version="{CURRENT_VERSION}"', migrated_claude)
            self.assertIn("@.claude/ctx404-instructions.md", migrated_claude)
            self.assertIn("Project-specific guidance will evolve", migrated_claude)

            # The user's edited definition must survive the move, not be reset to the template.
            definition = (target / DEFINITION).read_text(encoding="utf-8")
            self.assertIn("Purpose: preserve this custom definition", definition)
            self.assertIn(f"Project name: `{target.name}`", definition)
            self.assertIn("Start every session", (target / INSTRUCTIONS).read_text(encoding="utf-8"))
            self.assertTrue((target / CONTEXT_RULE).is_file())

            migrated_index = json.loads(index_path.read_text(encoding="utf-8"))
            self.assertEqual(migrated_index["governance"]["mode"], "exclusive")
            self.assertEqual(migrated_index["ctx404Version"], CURRENT_VERSION)
            history = (target / ".claude/context/history.jsonl").read_text(encoding="utf-8")
            self.assertIn('"type": "upgrade"', history)

    def test_reviewed_upgrade_moves_v03_block_out_of_claude_md(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)

            downgrade_install(target, "0.3.0-beta.1", "keep my scope", drop_governance=False)
            claude_path = target / "CLAUDE.md"
            self.assertIn("Route work by cost", claude_path.read_text(encoding="utf-8"))

            plan = run_python(BOOTSTRAP, "upgrade-plan", "--target", target)
            self.assertEqual(plan.returncode, 0, plan.stderr + plan.stdout)
            self.assertEqual(
                json.loads(plan.stdout)["hops"],
                [f"0.3.0-beta.1 -> {PREVIOUS_VERSION}", f"{PREVIOUS_VERSION} -> {CURRENT_VERSION}"],
            )

            applied = run_python(BOOTSTRAP, "upgrade-apply", "--target", target)
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)
            payload = json.loads(applied.stdout)
            self.assertTrue(payload["applied"])
            self.assertTrue(payload["validation"]["ok"])
            self.assertEqual(payload["warnings"], [])
            self.assertIn(INSTRUCTIONS, payload["created"])
            self.assertIn(CONTEXT_RULE, payload["created"])

            migrated = claude_path.read_text(encoding="utf-8")
            self.assertNotIn("Route work by cost", migrated)
            self.assertNotIn("Maintain context after relevant work", migrated)
            self.assertLess(len(migrated), 800)
            self.assertIn("keep my scope", (target / DEFINITION).read_text(encoding="utf-8"))

    def test_upgrade_refreshes_the_managed_helper_only_when_it_changed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)
            downgrade_install(target, "0.3.0-beta.1", "keep my scope", drop_governance=False)

            helper = target / ".claude/scripts/context_tool.py"
            # A 0.3.0 project carries the old helper, which has no topic-write. The rule the
            # upgrade installs tells Claude to use it, so the migration must ship the new helper.
            helper.write_text(
                helper.read_text(encoding="utf-8").replace('sub.add_parser("topic-write")', 'sub.add_parser("stale")'),
                encoding="utf-8",
            )
            # Line endings alone must not count as a change.
            hook = target / ".claude/hooks/session_context.py"
            hook.write_bytes(hook.read_bytes().replace(b"\n", b"\r\n"))

            applied = run_python(BOOTSTRAP, "upgrade-apply", "--target", target)
            self.assertEqual(applied.returncode, 0, applied.stderr + applied.stdout)
            payload = json.loads(applied.stdout)
            self.assertIn(".claude/scripts/context_tool.py", payload["refreshed"])
            self.assertNotIn(".claude/hooks/session_context.py", payload["refreshed"])
            self.assertIn("topic-write", helper.read_text(encoding="utf-8"))

            # A migrated project must also gain the allow rule the new protocol depends on.
            settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
            self.assertIn(
                "Bash(python .claude/scripts/context_tool.py:*)", settings["permissions"]["allow"]
            )

            # The refreshed doctor is the one that knows about the new files.
            doctor = run_python(helper, "doctor", cwd=target)
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertTrue(json.loads(doctor.stdout)["ok"])

    def test_always_loaded_core_stays_within_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)

            # Claude Code strips block-level HTML comments before loading, so they cost nothing.
            always_loaded = sum(
                len(re.sub(r"<!--.*?-->", "", (target / relative).read_text(encoding="utf-8"), flags=re.DOTALL).strip())
                for relative in ("CLAUDE.md", INSTRUCTIONS, DEFINITION)
            )
            self.assertLess(
                always_loaded,
                CORE_BUDGET_CHARS,
                "Always-loaded CTX404 footprint regressed; move detail into a path-scoped rule",
            )
            # The path-scoped rule must stay out of the always-loaded set.
            self.assertNotIn(
                "context_tool.py complete",
                (target / INSTRUCTIONS).read_text(encoding="utf-8"),
            )

    def test_topic_write_creates_updates_and_rejects_bad_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)
            helper = target / ".claude" / "scripts" / "context_tool.py"

            def write_topic(body: str, *args: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [sys.executable, str(helper), "topic-write", "--body-file", "-", *args],
                    cwd=target,
                    input=body,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            created = write_topic(
                "# Decision\n\nRegistry chosen.\n",
                "--id", "calculator-core",
                "--summary", "Core uses a pluggable operation registry",
                "--keyword", "architecture",
                "--keyword", "registry",
            )
            self.assertEqual(created.returncode, 0, created.stderr + created.stdout)
            payload = json.loads(created.stdout)
            self.assertTrue(payload["created"])
            self.assertEqual(payload["topicSync"]["topicCount"], 1)

            topic = (target / ".claude/context/topics/calculator-core.md").read_text(encoding="utf-8")
            self.assertIn('keywords: ["architecture", "registry"]', topic)
            self.assertIn("revision: 1", topic)
            self.assertIn("Registry chosen.", topic)

            updated = write_topic(
                "# Decision\n\nRevised.\n",
                "--id", "calculator-core",
                "--summary", "Core uses a pluggable operation registry",
                "--keyword", "architecture",
            )
            self.assertEqual(updated.returncode, 0, updated.stderr + updated.stdout)
            self.assertFalse(json.loads(updated.stdout)["created"])
            revised = (target / ".claude/context/topics/calculator-core.md").read_text(encoding="utf-8")
            self.assertIn("revision: 2", revised)
            self.assertIn(topic.split("created-at: ")[1].splitlines()[0], revised)

            empty = write_topic("   \n", "--id", "blank", "--summary", "s", "--keyword", "k")
            self.assertNotEqual(empty.returncode, 0)
            self.assertIn("body must not be empty", json.loads(empty.stdout)["error"])

            bad_id = write_topic("body", "--id", "Bad_Id", "--summary", "s", "--keyword", "k")
            self.assertNotEqual(bad_id.returncode, 0)
            self.assertFalse((target / ".claude/context/topics/Bad_Id.md").exists())

            # A topic written through the helper must satisfy the same doctor the protocol requires.
            doctor = run_python(helper, "doctor", cwd=target)
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertTrue(json.loads(doctor.stdout)["ok"])

    def test_doctor_detects_a_broken_import(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(run_python(BOOTSTRAP, "install", "--target", target).returncode, 0)
            helper = target / ".claude" / "scripts" / "context_tool.py"

            claude_path = target / "CLAUDE.md"
            claude_path.write_text(
                claude_path.read_text(encoding="utf-8").replace("@.claude/ctx404-instructions.md", ""),
                encoding="utf-8",
            )
            broken = run_python(helper, "doctor", cwd=target)
            self.assertNotEqual(broken.returncode, 0)
            self.assertIn("import", json.loads(broken.stdout)["issues"][0])

    def test_install_refuses_to_overwrite_an_existing_rule_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "app.py").write_text("print('keep')\n", encoding="utf-8")
            conflict = target / CONTEXT_RULE
            conflict.parent.mkdir(parents=True)
            conflict.write_text("my own rule\n", encoding="utf-8")

            run_python(BOOTSTRAP, "prepare", "--target", target)
            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertNotEqual(installed.returncode, 0)
            self.assertEqual(conflict.read_text(encoding="utf-8"), "my own rule\n")
            self.assertFalse((target / "CLAUDE.md").exists())

    def test_install_requires_prepare_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_python(BOOTSTRAP, "install", "--target", directory)
            self.assertNotEqual(result.returncode, 0)


def said(text: str) -> dict[str, object]:
    return {"type": "user", "message": {"role": "user", "content": text}}


def recorded() -> dict[str, object]:
    """An assistant turn that actually wrote context."""
    return {"type": "assistant", "message": {"content": [{
        "type": "tool_use",
        "name": "Bash",
        "input": {"command": 'python .claude/scripts/context_tool.py complete --summary "x"'},
    }]}}


class DeliberationTests(unittest.TestCase):
    """Reading context was always a hook; writing it was only a request. These cover the gate."""

    def install(self, target: Path) -> Path:
        self.assertEqual(run_python(BOOTSTRAP, "prepare", "--target", target).returncode, 0)
        installed = run_python(BOOTSTRAP, "install", "--target", target)
        self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
        return target / ".claude" / "scripts" / "context_tool.py"

    def gate(self, target: Path, entries: list[dict[str, object]], **overrides: object) -> dict:
        transcript = target / "transcript.jsonl"
        transcript.write_text("\n".join(json.dumps(entry) for entry in entries), encoding="utf-8")
        event: dict[str, object] = {
            "hook_event_name": "Stop",
            "cwd": str(target),
            "stop_hook_active": False,
            "transcript_path": str(transcript),
        }
        event.update(overrides)
        result = subprocess.run(
            [sys.executable, str(target / ".claude" / "hooks" / "context_gate.py")],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_install_wires_the_stop_hook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.install(target)
            settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))
            command = settings["hooks"]["Stop"][0]["hooks"][0]
            self.assertIn("context_gate.py", command["args"][0])
            self.assertTrue((target / ".claude/hooks/context_gate.py").is_file())

    def test_gate_blocks_a_session_that_deliberated_without_recording(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.install(target)
            verdict = self.gate(target, [said("a"), said("b"), said("c")])
            self.assertEqual(verdict["decision"], "block")
            self.assertIn("rejected", verdict["reason"])

    def test_gate_leaves_a_short_session_alone(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.install(target)
            self.assertEqual(self.gate(target, [said("a"), said("b")]), {})

    def test_gate_never_blocks_the_same_stop_twice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.install(target)
            entries = [said("a"), said("b"), said("c")]
            self.assertEqual(self.gate(target, entries, stop_hook_active=True), {})

    def test_gate_clears_once_context_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            self.install(target)
            entries = [said("a"), said("b"), said("c"), recorded()]
            self.assertEqual(self.gate(target, entries), {})

    def test_review_reads_back_a_rejected_option(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            helper = self.install(target)
            body = (
                "## Decided\nShip the smaller thing.\n\n"
                "## Rejected\nA rewrite, because the deadline does not survive it.\n"
            )
            written = subprocess.run(
                [sys.executable, str(helper), "topic-write", "--id", "scope",
                 "--summary", "Scope decision", "--keyword", "scope", "--body-file", "-"],
                cwd=target, input=body, text=True, capture_output=True, check=False,
            )
            self.assertEqual(written.returncode, 0, written.stderr + written.stdout)

            found = run_python(helper, "review", "--section", "rejected", cwd=target)
            self.assertEqual(found.returncode, 0, found.stderr + found.stdout)
            payload = json.loads(found.stdout)
            self.assertEqual(payload["count"], 1)
            self.assertIn("deadline does not survive", payload["entries"][0]["text"])
            self.assertEqual(payload["entries"][0]["topic"], "scope")

            # A rejected option must not be reachable only by luck of wording.
            queried = run_python(helper, "review", "--query", "rewrite", cwd=target)
            self.assertEqual(json.loads(queried.stdout)["count"], 1)
            missing = run_python(helper, "review", "--section", "revoked", cwd=target)
            self.assertEqual(json.loads(missing.stdout)["count"], 0)


class SkillInstallerTests(unittest.TestCase):
    def test_installer_is_transactional_and_excludes_repository_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills_root = Path(directory)
            first = run_python(INSTALLER, "--skills-root", skills_root)
            self.assertEqual(first.returncode, 0, first.stderr + first.stdout)
            destination = skills_root / "ctx404"
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertFalse((destination / "README.md").exists())
            self.assertFalse((destination / "tests").exists())

            refused = run_python(INSTALLER, "--skills-root", skills_root)
            self.assertNotEqual(refused.returncode, 0)

            marker = destination / "obsolete.txt"
            marker.write_text("old", encoding="utf-8")
            replaced = run_python(INSTALLER, "--skills-root", skills_root, "--force")
            self.assertEqual(replaced.returncode, 0, replaced.stderr + replaced.stdout)
            self.assertFalse(marker.exists())


class SkillMetadataTests(unittest.TestCase):
    def test_skill_frontmatter_and_name(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---", 2)[1]
        self.assertIn("name: ctx404", frontmatter)
        self.assertIn("description:", frontmatter)


if __name__ == "__main__":
    unittest.main()
