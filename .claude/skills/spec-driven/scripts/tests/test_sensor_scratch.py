"""Testes de sensor_scratch.py: o scratch contem exatamente a versao
verificada (commits em HEAD + staged + unstaged + untracked, com e sem escopo),
`reset` volta ao snapshot depois de mutacoes consecutivas, e a arvore real,
o index e os branches nao mudam.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_sensor_scratch.py"
"""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import sensor_scratch  # noqa: E402

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def git(args, cwd):
    return subprocess.run(GIT + args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return f.read()


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = sensor_scratch.main(["sensor_scratch.py"] + argv)
    return code, out.getvalue(), err.getvalue()


class SensorScratchBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sdd-sensor-")
        self.repo = os.path.join(self.tmp, "repo")
        self.scratch = os.path.join(self.tmp, "scratch")
        os.makedirs(self.repo)
        git(["init", "-q", "-b", "main"], self.repo)
        write(self.repo, ".gitignore", "bin/\n")
        write(self.repo, "src/Calc.cs", "int Add(int a, int b) => a + b;\n")
        write(self.repo, "tests/CalcTests.cs", "Assert(Add(1, 2) == 3);\n")
        write(self.repo, "README.md", "base\n")
        git(["add", "-A"], self.repo)
        git(["commit", "-q", "-m", "chore: base"], self.repo)
        self.base = git(["rev-parse", "HEAD"], self.repo).strip()

    def tearDown(self):
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo, capture_output=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def real_state(self):
        """Tudo que o script promete nao tocar: HEAD, branch, index, arvore."""
        return (git(["rev-parse", "HEAD"], self.repo),
                git(["branch", "--show-current"], self.repo),
                git(["diff", "--cached"], self.repo),
                git(["diff"], self.repo),
                git(["status", "--porcelain", "--untracked-files=all"], self.repo),
                git(["stash", "list"], self.repo))

    def assert_scratch_clean(self):
        self.assertEqual(git(["status", "--porcelain"], self.scratch), "")

    def snapshot_sha(self):
        return sensor_scratch.read_snapshot(self.scratch)


class CreateTests(SensorScratchBase):
    def test_all_committed(self):
        write(self.repo, "src/Calc.cs", "int Add(int a, int b) => a + b + 0;\n")
        git(["commit", "-qam", "feat: change"], self.repo)
        before = self.real_state()
        code, out, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        self.assertEqual(read(self.scratch, "src/Calc.cs"), read(self.repo, "src/Calc.cs"))
        self.assertIn("tracked changes applied: 0", out)
        self.assert_scratch_clean()
        self.assertEqual(self.real_state(), before)
        # o snapshot e um commit em cima de HEAD, so no scratch
        self.assertEqual(git(["rev-parse", "HEAD~1"], self.scratch).strip(),
                         git(["rev-parse", "HEAD"], self.repo).strip())

    def test_all_uncommitted_staged_unstaged_untracked(self):
        write(self.repo, "src/Calc.cs", "staged\n")
        git(["add", "src/Calc.cs"], self.repo)
        write(self.repo, "tests/CalcTests.cs", "unstaged\n")
        write(self.repo, "src/New.cs", "untracked\n")
        write(self.repo, "bin/out.dll", "ignored\n")
        before = self.real_state()
        code, out, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        self.assertEqual(read(self.scratch, "src/Calc.cs"), "staged\n")
        self.assertEqual(read(self.scratch, "tests/CalcTests.cs"), "unstaged\n")
        self.assertEqual(read(self.scratch, "src/New.cs"), "untracked\n")
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "bin", "out.dll")))
        self.assert_scratch_clean()
        self.assertEqual(self.real_state(), before)

    def test_mixed_commits_after_base_plus_pending(self):
        """O caso que `git diff <base>` aplicado sobre HEAD nao resolve."""
        write(self.repo, "src/Calc.cs", "committed after base\n")
        git(["commit", "-qam", "feat: step one"], self.repo)
        write(self.repo, "src/Calc.cs", "committed after base\npending\n")
        write(self.repo, "tests/NewTests.cs", "pending untracked\n")
        # controle: o procedimento antigo falha
        patch = subprocess.run(["git", "diff", self.base], cwd=self.repo, capture_output=True, text=True).stdout
        other = os.path.join(self.tmp, "old-procedure")
        git(["worktree", "add", "--detach", "-q", other, "HEAD"], self.repo)
        old = subprocess.run(["git", "apply", "-"], cwd=other, input=patch, capture_output=True, text=True)
        self.assertNotEqual(old.returncode, 0, "diff contra a base deveria falhar sobre HEAD")
        git(["worktree", "remove", "--force", other], self.repo)
        before = self.real_state()
        code, out, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        self.assertEqual(read(self.scratch, "src/Calc.cs"), "committed after base\npending\n")
        self.assertEqual(read(self.scratch, "tests/NewTests.cs"), "pending untracked\n")
        self.assert_scratch_clean()
        self.assertEqual(self.real_state(), before)

    def test_pending_deletion_and_rename(self):
        git(["mv", "README.md", "NOTES.md"], self.repo)
        os.remove(os.path.join(self.repo, "tests/CalcTests.cs"))
        code, out, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.exists(os.path.join(self.scratch, "NOTES.md")))
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "README.md")))
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "tests", "CalcTests.cs")))
        self.assert_scratch_clean()

    def test_path_scope_excludes_preexisting_changes(self):
        write(self.repo, "src/Calc.cs", "in scope\n")
        write(self.repo, "README.md", "preexisting edit outside the change\n")
        write(self.repo, "docs/notes.md", "untracked outside\n")
        write(self.repo, "tests/NewTests.cs", "untracked in scope\n")
        code, out, err = run(["create", self.scratch, "--repo", self.repo, "--path", "src", "--path", "tests"])
        self.assertEqual(code, 0, err)
        self.assertEqual(read(self.scratch, "src/Calc.cs"), "in scope\n")
        self.assertEqual(read(self.scratch, "tests/NewTests.cs"), "untracked in scope\n")
        self.assertEqual(read(self.scratch, "README.md"), "base\n")
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "docs", "notes.md")))
        self.assert_scratch_clean()

    def test_binary_pending_change(self):
        with open(os.path.join(self.repo, "logo.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x01")
        git(["add", "logo.png"], self.repo)
        git(["commit", "-qm", "chore: add logo"], self.repo)
        with open(os.path.join(self.repo, "logo.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x02\x03")
        code, out, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        with open(os.path.join(self.scratch, "logo.png"), "rb") as f:
            self.assertEqual(f.read(), b"\x89PNG\r\n\x1a\n\x00\x02\x03")

    def test_create_from_subdirectory_keeps_root_relative_paths(self):
        write(self.repo, "src/Calc.cs", "modified\n")
        write(self.repo, "src/New.cs", "untracked\n")
        write(self.repo, "tests/Deep/NewTests.cs", "untracked deep\n")
        cwd = os.getcwd()
        os.chdir(os.path.join(self.repo, "src"))
        try:
            code, out, err = run(["create", self.scratch, "--path", "src", "--path", "tests"])
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0, err)
        self.assertEqual(read(self.scratch, "src/Calc.cs"), "modified\n")
        self.assertEqual(read(self.scratch, "src/New.cs"), "untracked\n")
        self.assertEqual(read(self.scratch, "tests/Deep/NewTests.cs"), "untracked deep\n")
        self.assertFalse(os.path.exists(os.path.join(self.scratch, "src", "src")))
        self.assert_scratch_clean()

    def test_refuses_scratch_inside_repo(self):
        before = self.real_state()
        code, _, err = run(["create", os.path.join(self.repo, "scratch"), "--repo", self.repo])
        self.assertEqual(code, 1)
        self.assertIn("dentro do repositorio", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(self.real_state(), before)
        self.assertNotIn("scratch", git(["worktree", "list"], self.repo))

    def test_refuses_symlink_into_repo(self):
        os.makedirs(os.path.join(self.repo, "sub"))
        link = os.path.join(self.tmp, "sublink")
        os.symlink(os.path.join(self.repo, "sub"), link)
        before = self.real_state()
        code, _, err = run(["create", link, "--repo", self.repo])
        self.assertEqual(code, 1)
        self.assertIn("link simbolico", err)
        self.assertEqual(self.real_state(), before)
        self.assertNotIn("sub", git(["worktree", "list"], self.repo))

    def test_refuses_existing_file_as_dir(self):
        write(self.tmp, "afile", "x\n")
        code, _, err = run(["create", os.path.join(self.tmp, "afile"), "--repo", self.repo])
        self.assertEqual(code, 1)
        self.assertIn("nao e diretorio", err)
        self.assertNotIn("Traceback", err)

    def test_missing_repo_is_error_not_traceback(self):
        code, _, err = run(["create", self.scratch, "--repo", os.path.join(self.tmp, "nope")])
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", err)

    def test_populate_failure_removes_worktree(self):
        write(self.repo, "src/Calc.cs", "modified\n")
        with unittest.mock.patch.object(sensor_scratch, "populate", side_effect=OSError("disk full")):
            code, _, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 1)
        self.assertIn("worktree removido", err)
        self.assertNotIn("scratch", git(["worktree", "list"], self.repo))
        self.assertFalse(os.path.exists(self.scratch))

    def test_refuses_non_empty_dir(self):
        os.makedirs(self.scratch)
        write(self.scratch, "x.txt", "x\n")
        code, out, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 1)
        self.assertIn("nao esta vazio", err)

    def test_no_branch_created_and_worktree_listed(self):
        branches = git(["branch", "--list"], self.repo)
        code, _, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        self.assertEqual(git(["branch", "--list"], self.repo), branches)
        self.assertIn(os.path.realpath(self.scratch), git(["worktree", "list"], self.repo).replace("\\", "/"))


class ResetTests(SensorScratchBase):
    def setUp(self):
        super().setUp()
        write(self.repo, "src/Calc.cs", "int Add(int a, int b) => a + b; // verified\n")
        write(self.repo, "src/Untracked.cs", "untracked verified\n")
        code, _, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        self.sha = self.snapshot_sha()

    def test_two_consecutive_mutations_restore_snapshot(self):
        for n in (1, 2):
            write(self.scratch, "src/Calc.cs", f"int Add(int a, int b) => a - b; // mutation {n}\n")
            write(self.scratch, "src/Untracked.cs", f"mutated {n}\n")
            write(self.scratch, f"src/Extra{n}.cs", "created by mutation\n")
            os.remove(os.path.join(self.scratch, "tests", "CalcTests.cs"))
            code, out, err = run(["reset", self.scratch])
            self.assertEqual(code, 0, err)
            self.assertEqual(read(self.scratch, "src/Calc.cs"), "int Add(int a, int b) => a + b; // verified\n")
            self.assertEqual(read(self.scratch, "src/Untracked.cs"), "untracked verified\n")
            self.assertTrue(os.path.exists(os.path.join(self.scratch, "tests", "CalcTests.cs")))
            self.assertFalse(os.path.exists(os.path.join(self.scratch, "src", f"Extra{n}.cs")))
            self.assertEqual(git(["rev-parse", "HEAD"], self.scratch).strip(), self.sha)
            self.assert_scratch_clean()
            self.assertIn(self.sha, out)

    def test_reset_after_commit_in_scratch(self):
        write(self.scratch, "src/Calc.cs", "mutated and committed\n")
        git(["commit", "-qam", "mutation"], self.scratch)
        code, _, err = run(["reset", self.scratch])
        self.assertEqual(code, 0, err)
        self.assertEqual(git(["rev-parse", "HEAD"], self.scratch).strip(), self.sha)
        self.assertEqual(read(self.scratch, "src/Calc.cs"), "int Add(int a, int b) => a + b; // verified\n")

    def test_checkout_dot_would_not_restore_verified_version(self):
        """Documenta por que `git checkout -- .` nao serve: sem o commit de
        snapshot, o index e HEAD e a versao verificada se perde."""
        other = os.path.join(self.tmp, "no-snapshot")
        git(["worktree", "add", "--detach", "-q", other, "HEAD"], self.repo)
        write(other, "src/Calc.cs", "int Add(int a, int b) => a + b; // verified\n")
        write(other, "src/Calc.cs", "mutated\n")
        git(["checkout", "--", "."], other)
        self.assertEqual(read(other, "src/Calc.cs"), "int Add(int a, int b) => a + b;\n")  # HEAD, nao a verificada
        git(["worktree", "remove", "--force", other], self.repo)

    def test_reset_keeps_ignored_files(self):
        write(self.scratch, "bin/build.dll", "expensive build output\n")
        code, _, err = run(["reset", self.scratch])
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.exists(os.path.join(self.scratch, "bin", "build.dll")))

    def test_reset_without_snapshot_fails(self):
        os.remove(sensor_scratch.snapshot_path(self.scratch))
        code, _, err = run(["reset", self.scratch])
        self.assertEqual(code, 1)
        self.assertIn("snapshot ausente", err)

    def test_reset_missing_dir_fails(self):
        code, _, err = run(["reset", os.path.join(self.tmp, "nope")])
        self.assertEqual(code, 1)
        self.assertIn("nao existe", err)

    def test_real_tree_untouched_across_cycle(self):
        before = self.real_state()
        write(self.scratch, "src/Calc.cs", "mutated\n")
        run(["reset", self.scratch])
        run(["remove", self.scratch])
        self.assertEqual(self.real_state(), before)


class RemoveTests(SensorScratchBase):
    def test_remove_unregisters_worktree(self):
        code, _, err = run(["create", self.scratch, "--repo", self.repo])
        self.assertEqual(code, 0, err)
        write(self.scratch, "src/Calc.cs", "dirty\n")
        code, _, err = run(["remove", self.scratch])
        self.assertEqual(code, 0, err)
        self.assertFalse(os.path.exists(self.scratch))
        self.assertNotIn("scratch", git(["worktree", "list"], self.repo))

    def test_remove_missing_dir_fails(self):
        code, _, err = run(["remove", os.path.join(self.tmp, "nope")])
        self.assertEqual(code, 1)


class UsageTests(unittest.TestCase):
    def test_no_args_is_usage(self):
        code, _, err = run([])
        self.assertEqual(code, 2)
        self.assertIn("create", err)

    def test_unknown_command_is_usage(self):
        code, _, err = run(["frobnicate", "x"])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
