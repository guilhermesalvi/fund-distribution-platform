"""Testes do check_commit.py (politica de commit do repositorio).

    python -m unittest discover -s .github/scripts/tests
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import check_commit  # noqa: E402


class CheckCommitTest(unittest.TestCase):
    def test_default_accepts_scope_and_72(self):
        self.assertEqual(check_commit.check("feat(api): " + "x" * 61), [])

    def test_no_scope_rejects_scope(self):
        errs = check_commit.check("feat(api): add thing", no_scope=True)
        self.assertTrue(any("escopo nao permitido" in e for e in errs), errs)
        self.assertEqual(check_commit.check("feat: add thing", no_scope=True), [])

    def test_max_len_60(self):
        msg = "feat: " + "x" * 60
        self.assertEqual(check_commit.check(msg), [])
        errs = check_commit.check(msg, max_len=60)
        self.assertTrue(any("66 chars (max 60)" in e for e in errs), errs)

    def test_past_tense_and_period(self):
        errs = check_commit.check("fix(api): Fixed thing.")
        self.assertTrue(any("imperativo" in e for e in errs), errs)
        self.assertTrue(any("ponto" in e for e in errs), errs)

    def test_cli_flags(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_commit.main(["check_commit.py", "--message", "feat(api): add thing", "--no-scope"])
        self.assertEqual(code, 1)
        self.assertIn("escopo nao permitido", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_commit.main(["check_commit.py", "--message", "feat: " + "x" * 60, "--max-len", "60"])
        self.assertEqual(code, 1)
        self.assertIn("max 60", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_commit.main(["check_commit.py", "--message", "feat: add thing", "--max-len", "60", "--no-scope"])
        self.assertEqual(code, 0)

    # --- perfil estrito (AGENTS.md deste repositorio): 60 chars, sem escopo,
    # sem `!`, uma linha, minuscula inicial ---------------------------------
    STRICT = dict(max_len=60, no_scope=True, no_bang=True, single_line=True, lowercase=True)

    def test_default_accepts_bang_body_and_capital(self):
        self.assertEqual(check_commit.check("feat!: add endpoint"), [])
        self.assertEqual(check_commit.check("feat: Add endpoint"), [])
        self.assertEqual(check_commit.check("feat: add endpoint\n\nBody.\n\nRefs: #1"), [])

    def test_strict_accepts_control(self):
        self.assertEqual(check_commit.check("feat: add endpoint", **self.STRICT), [])
        self.assertEqual(check_commit.check("chore: .editorconfig for tabs", **self.STRICT), [])

    def test_no_bang_rejects_breaking_marker(self):
        errs = check_commit.check("feat!: add endpoint", no_bang=True)
        self.assertTrue(any("--no-bang" in e for e in errs), errs)
        errs = check_commit.check("feat(api)!: add endpoint", no_bang=True)
        self.assertTrue(any("--no-bang" in e for e in errs), errs)

    def test_lowercase_rejects_capital_description(self):
        errs = check_commit.check("feat: Add endpoint", lowercase=True)
        self.assertTrue(any("--lowercase" in e for e in errs), errs)
        self.assertEqual(check_commit.check("feat: add Endpoint", lowercase=True), [])

    def test_single_line_rejects_body_and_footer(self):
        errs = check_commit.check("feat: add endpoint\n\nBody.", single_line=True)
        self.assertTrue(any("--single-line" in e for e in errs), errs)
        errs = check_commit.check("feat: add endpoint\n\nCo-Authored-By: X <x@y>", single_line=True)
        self.assertTrue(any("--single-line" in e for e in errs), errs)
        self.assertEqual(check_commit.check("feat: add endpoint\n\n  \n", single_line=True), [])

    def test_non_imperative_forms(self):
        for msg in ("feat: implemented endpoint", "feat: adds endpoint", "fix: fixing bug",
                    "refactor: Rewrote module"):
            errs = check_commit.check(msg)
            self.assertTrue(any("imperativo" in e for e in errs), (msg, errs))
        self.assertEqual(check_commit.check("feat: add endpoint"), [])

    def test_file_strips_git_comments_and_scissors(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "COMMIT_EDITMSG")
            with open(path, "w", encoding="utf-8") as f:
                f.write("feat: add endpoint\n\n# Please enter the commit message\n"
                        "# ------------------------ >8 ------------------------\n"
                        "diff --git a/x b/x\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = check_commit.main(["check_commit.py", "--file", path, "--single-line"])
            self.assertEqual(code, 0, out.getvalue())

    def test_usage_errors_exit_2_without_traceback(self):
        cases = (["check_commit.py", "--message"],
                 ["check_commit.py", "--message", "feat: x", "--max-len"],
                 ["check_commit.py", "--message", "feat: x", "--max-len", "abc"],
                 ["check_commit.py", "--message", "feat: x", "--max-len", "0"],
                 ["check_commit.py", "--file", os.path.join(tempfile.gettempdir(), "nope-" + "x" * 8)],
                 ["check_commit.py"],
                 ["check_commit.py", "--message", "feat: x", "--file", "y"])
        for argv in cases:
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = check_commit.main(argv)
            self.assertEqual(code, 2, (argv, err.getvalue()))
            self.assertNotIn("Traceback", err.getvalue())

    def test_file_not_utf8_is_usage(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "COMMIT_EDITMSG")
            with open(path, "wb") as f:
                f.write(b"fix: corrigir acentua\xe7\xe3o\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                code = check_commit.main(["check_commit.py", "--file", path])
            self.assertEqual(code, 2)
            self.assertIn("UTF-8", err.getvalue())
            self.assertNotIn("Traceback", err.getvalue())

    def test_violation_exit_1_distinct_from_usage(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_commit.main(["check_commit.py", "--message", "feat!: Add thing.",
                                      "--no-bang", "--lowercase"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue().count("HARD"), 3)


if __name__ == "__main__":
    unittest.main()
