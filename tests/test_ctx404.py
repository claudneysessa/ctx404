from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap.py"
INSTALLER = ROOT / "scripts" / "install.py"


def run_python(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *(str(arg) for arg in args)],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


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
            self.assertIn("Project definition workspace", governance)

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

            prepared = run_python(BOOTSTRAP, "prepare", "--target", target)
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
            self.assertEqual(settings["permissions"], {"allow": ["Read"]})
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

    def test_install_requires_prepare_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_python(BOOTSTRAP, "install", "--target", directory)
            self.assertNotEqual(result.returncode, 0)


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
