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

    def test_prepare_rejects_non_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "existing.txt").write_text("keep", encoding="utf-8")
            result = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((target / "existing.txt").read_text(encoding="utf-8"), "keep")

    def test_install_consolidates_governance_and_validates_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            prepared = run_python(BOOTSTRAP, "prepare", "--target", target)
            self.assertEqual(prepared.returncode, 0, prepared.stdout)
            native = "# Native project guidance\n\nKeep this line.\n"
            (target / "CLAUDE.md").write_text(native, encoding="utf-8")

            installed = run_python(BOOTSTRAP, "install", "--target", target)
            self.assertEqual(installed.returncode, 0, installed.stderr + installed.stdout)
            payload = json.loads(installed.stdout)
            self.assertTrue(payload["validation"]["ok"])

            governance = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("ctx404:governance:start", governance)
            self.assertIn(native.strip(), governance)
            self.assertEqual(governance.count("ctx404:governance:start"), 1)

            helper = target / ".claude" / "scripts" / "context_tool.py"
            doctor = run_python(helper, "doctor", cwd=target)
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertTrue(json.loads(doctor.stdout)["ok"])

            index = json.loads((target / ".claude" / "context" / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["project"]["name"], target.name)

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
