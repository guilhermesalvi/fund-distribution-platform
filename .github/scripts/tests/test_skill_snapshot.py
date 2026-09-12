"""Exercise HEAD-based convention discovery, separately from index inventory."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Snapshot Test")
        self.git("config", "user.email", "snapshot@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args, check=True):
        env = os.environ.copy()
        # A caller's repository/index must never redirect fixture operations.
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            env.pop(key, None)
        return subprocess.run(
            ["git", *args], cwd=self.repo, env=env, check=check,
            capture_output=True, text=True, encoding="utf-8",
        )

    def write(self, name, content="# Approved heading\n"):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit_examples(self, count):
        for i in range(count):
            self.write(f"docs/prd/{i:04d}-example.md")
        self.git("add", "--", "docs/prd")
        self.git("commit", "--quiet", "-m", "test: add fixture examples")

    def candidates(self, directory="docs/prd", filename=None):
        paths = self.git("ls-tree", "-r", "--name-only", "HEAD", "--", directory).stdout.splitlines()
        return [p for p in paths if Path(p).suffix == ".md"
                and (filename is None or Path(p).name == filename)]

    def test_two_in_head_and_third_staged(self):
        self.commit_examples(2)
        self.write("docs/prd/0002-example.md")
        self.git("add", "--", "docs/prd/0002-example.md")
        self.assertEqual(len(self.git("ls-files", "--", "docs/prd").stdout.splitlines()), 3)
        self.assertEqual(len(self.candidates()), 2)

    def test_three_committed_examples(self):
        self.commit_examples(3)
        self.assertEqual(len(self.candidates()), 3)

    def test_local_heading_does_not_change_head_content(self):
        self.commit_examples(3)
        name = self.candidates()[0]
        self.write(name, "# Local heading\n")
        self.assertEqual(self.git("show", f"HEAD:{name}").stdout, "# Approved heading\n")
        self.assertEqual((self.repo / name).read_text(encoding="utf-8"), "# Local heading\n")

    def test_untracked_example_is_excluded(self):
        self.commit_examples(2)
        self.write("docs/prd/0002-example.md")
        self.assertEqual(len(self.candidates()), 2)

    def test_missing_head_is_an_explicit_failure(self):
        result = self.git("ls-tree", "-r", "--name-only", "HEAD", "--", "docs/prd", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr)

    def test_only_markdown_of_selected_type_counts(self):
        self.commit_examples(2)
        for name in ("docs/prd/notes.txt", "docs/specs/demo/spec.md",
                     "docs/specs/demo/0001-demo/design.md", "docs/specs/demo/0001-demo/tasks.md"):
            self.write(name)
        self.git("add", "--", "docs")
        self.git("commit", "--quiet", "-m", "test: add mixed fixture types")
        self.assertEqual(len(self.candidates()), 2)
        self.assertEqual(self.candidates("docs/specs", "design.md"),
                         ["docs/specs/demo/0001-demo/design.md"])
        self.assertEqual(self.candidates("docs/specs", "tasks.md"),
                         ["docs/specs/demo/0001-demo/tasks.md"])


class SnapshotInstructionsTest(unittest.TestCase):
    def test_linter_docstring_delegates_convention_discovery(self):
        source = (ROOT / ".agents/skills/prd/scripts/lint_prd.py").read_text(encoding="utf-8")
        docstring = source.split('"""', 2)[1]
        self.assertNotIn("git ls-files", docstring)
        self.assertIn("workflow.md", docstring)

    def test_convention_sources_use_head(self):
        for name in ("prd/references/workflow.md", "sdd/references/validation.md",
                     "sdd/references/adr.md"):
            with self.subTest(source=name):
                text = (ROOT / ".agents/skills" / name).read_text(encoding="utf-8")
                self.assertIn("git ls-tree", text)
                self.assertIn("git show", text)
                self.assertRegex(text, r"(?i)(sem HEAD|HEAD não exist|HEAD inexist|não h[aá] HEAD)")
                self.assertNotIn("git ls-files", text)

    def test_tracked_layer_inventory_is_preserved(self):
        for name in ("sdd/references/design.md", "sdd/references/workflow.md"):
            text = (ROOT / ".agents/skills" / name).read_text(encoding="utf-8")
            self.assertIn("git ls-files", text)
            self.assertRegex(text, r"rastread[oa]s")


if __name__ == "__main__":
    unittest.main()
