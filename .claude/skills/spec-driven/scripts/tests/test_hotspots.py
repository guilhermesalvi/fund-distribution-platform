"""Tests for hotspots.py.

Run:  python -m unittest discover -s <skill-dir>/scripts -p "test_hotspots.py"
"""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import hotspots  # noqa: E402

UNICODE_FILE = "relatório final.md"
SPACE_FILE = "src/pasta com espaço/Über.cs"


def _git(repo, *args, author=None):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1")
    if author:
        env.update(GIT_AUTHOR_NAME=author, GIT_COMMITTER_NAME=author,
                   GIT_AUTHOR_EMAIL=f"{author.replace(' ', '.')}@example.test",
                   GIT_COMMITTER_EMAIL=f"{author.replace(' ', '.')}@example.test")
    subprocess.run(["git", "-C", repo, *args], check=True, env=env,
                   capture_output=True, text=True, encoding="utf-8")


def _commit_file(repo, rel, author):
    p = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write("x\n")
    _git(repo, "add", "-A", author=author)
    _git(repo, "commit", "-q", "-m", "change", author=author)


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = hotspots.main(argv)
    return code, out.getvalue(), err.getvalue()


@unittest.skipUnless(shutil.which("git"), "git nao encontrado")
class HotspotsRepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.repo = os.path.join(cls.tmp.name, "repo")
        os.makedirs(cls.repo)
        _git(cls.repo, "init", "-q")
        _git(cls.repo, "config", "core.autocrlf", "false")
        _git(cls.repo, "config", "core.quotepath", "true")
        # 12 commits: unicode file touched by 3 authors (8x), space file by 1 author (4x)
        for i in range(8):
            _commit_file(cls.repo, UNICODE_FILE, ["Ana Lima", "Bruno", "Carla"][i % 3])
        for _ in range(4):
            _commit_file(cls.repo, SPACE_FILE, "Ana Lima")
        os.makedirs(os.path.join(cls.repo, "quiet"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_counts_unicode_and_space_paths(self):
        code, out, err = run_main([self.repo, "--days", "30"])
        self.assertEqual(code, 0, err)
        self.assertIn("commits: 12 | arquivos tocados: 2 | mudancas (arquivo x commit): 12", out)
        self.assertIn(f"| `{UNICODE_FILE}` | 8 | 3 |", out)
        self.assertIn(f"| `{SPACE_FILE}` | 4 | 1 |", out)
        self.assertNotIn("\\303", out)
        self.assertNotIn('"', out)

    def test_hotspot_requires_min_authors(self):
        code, out, _ = run_main([self.repo, "--days", "30", "--share", "1"])
        self.assertEqual(code, 0)
        hot = out.split("## Hotspots")[1].split("## Conjunto")[0]
        self.assertIn(f"`{UNICODE_FILE}`", hot)
        self.assertNotIn(f"`{SPACE_FILE}`", hot)

    def test_report_marks_evidence_as_indicio(self):
        _, out, _ = run_main([self.repo, "--days", "30"])
        self.assertIn("## Hotspots (indicio", out)
        self.assertIn("Indicio, nao prova", out)
        self.assertIn("CODEOWNERS", out)

    def test_quiet_top_level_dirs(self):
        _, out, _ = run_main([self.repo, "--days", "30"])
        self.assertIn("`quiet`", out)

    def test_authors_table(self):
        _, out, _ = run_main([self.repo, "--days", "30"])
        self.assertIn("| Ana Lima | 7 | 2 |", out)

    def test_path_filter(self):
        code, _, err = run_main([self.repo, "--days", "30", "--path", "src"])
        self.assertEqual(code, 2)
        self.assertIn("inconclusivo", err)

    def test_path_nonexistent(self):
        code, _, err = run_main([self.repo, "--path", "nao-existe"])
        self.assertEqual(code, 2)
        self.assertIn("--path inexistente", err)


@unittest.skipUnless(shutil.which("git"), "git nao encontrado")
class InconclusiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.join(self.tmp.name, "repo")
        os.makedirs(self.repo)
        _git(self.repo, "init", "-q")

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_commits(self):
        code, out, err = run_main([self.repo])
        self.assertEqual(code, 2)
        self.assertIn("inconclusivo", err)
        self.assertEqual(out, "")

    def test_commits_without_files(self):
        for _ in range(10):
            _git(self.repo, "commit", "-q", "--allow-empty", "-m", "empty", author="A")
        code, out, err = run_main([self.repo])
        self.assertEqual(code, 2)
        self.assertIn("inconclusivo", err)
        self.assertIn("0 arquivo(s)", err)

    def test_too_few_commits(self):
        for _ in range(3):
            _commit_file(self.repo, "a.txt", "A")
        code, _, err = run_main([self.repo])
        self.assertEqual(code, 2)
        self.assertIn("inconclusivo", err)


class InvalidInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _expect_2(self, argv, fragment):
        code, _, err = run_main(argv)
        self.assertEqual(code, 2, err)
        self.assertIn(fragment, err)

    def test_invalid_params(self):
        d = self.tmp.name
        self._expect_2([d, "--days", "0"], "--days")
        self._expect_2([d, "--days", "-5"], "--days")
        self._expect_2([d, "--share", "0"], "--share")
        self._expect_2([d, "--share", "1.5"], "--share")
        self._expect_2([d, "--min-authors", "0"], "--min-authors")
        self._expect_2([d, "--top", "-1"], "--top")

    def test_repo_nonexistent(self):
        self._expect_2([os.path.join(self.tmp.name, "nada")], "repositorio inexistente")

    @unittest.skipUnless(shutil.which("git"), "git nao encontrado")
    def test_dir_without_git(self):
        self._expect_2([self.tmp.name], "nao e um repositorio git")


class NoArgsTests(unittest.TestCase):
    def test_no_args_prints_docstring_and_exits_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = hotspots.main([])
        self.assertEqual(code, 2)
        self.assertIn("hotspots.py - ", err.getvalue())


if __name__ == "__main__":
    unittest.main()
