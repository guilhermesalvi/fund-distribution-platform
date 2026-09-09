"""Testes de seq.py: proximo numero (max+1), forma do slug, numero duplicado
global na raiz, o que conta como PRD e erros de uso.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_seq.py"
"""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEQ = os.path.join(SCRIPTS, "seq.py")


class SeqCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "docs", "prd")
        os.makedirs(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content="# X\n"):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def run_seq(self, *args):
        r = subprocess.run([sys.executable, SEQ, *args], capture_output=True,
                           text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr


class NextTests(SeqCase):
    def test_next_is_max_plus_one(self):
        self.write("0001-onb-x.md")
        self.write("0003-onb-y.md")
        rc, out = self.run_seq("next", self.root, "--slug", "onb-z")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0004-onb-z")
        rc, out = self.run_seq("next", self.root)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0004")

    def test_empty_root_starts_at_0001(self):
        rc, out = self.run_seq("next", self.root, "--slug", "onb-x")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0001-onb-x")

    def test_overview_counts_as_prd(self):
        self.write("0000-platform-overview.md")
        rc, out = self.run_seq("next", self.root)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0001")

    def test_invalid_slug_is_rejected(self):
        for slug in ("Onb-Z", "onb_z", "onb--z", "onb-", "onb z"):
            rc, out = self.run_seq("next", self.root, "--slug", slug)
            self.assertEqual(rc, 1, out)
            self.assertIn("kebab-case", out)

    def test_upper_case_md_counts_as_prd(self):
        self.write("0001-onb-x.MD")
        rc, out = self.run_seq("next", self.root)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0002")

    def test_non_prd_files_are_ignored(self):
        self.write("0001-onb-x.md")
        self.write("README.md")
        self.write("notes.md")
        self.write("assets/0009-not.md")
        self.write("0008-onb-y/prd.md")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)
        self.assertIn("1 PRD(s)", out)
        rc, out = self.run_seq("next", self.root)
        self.assertEqual(out.strip(), "0002")


class DuplicateTests(SeqCase):
    def test_number_unique_across_subfolders(self):
        self.write("onb/0001-x.md")
        self.write("oth/0001-y.md")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)
        self.assertIn("HARD  numero 0001 usado por mais de um PRD", out)
        rc, out = self.run_seq("next", self.root, "--slug", "z")
        self.assertEqual(rc, 1, out)
        self.assertNotIn("0002", out)

    def test_check_green_without_duplicates(self):
        self.write("0000-overview.md")
        self.write("0001-onb-x.md")
        self.write("0005-onb-y.md")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)
        self.assertFalse(any(l.startswith("HARD") for l in out.splitlines()), out)


class ContractTests(SeqCase):
    def test_no_args_prints_docstring_and_exits_2(self):
        rc, out = self.run_seq()
        self.assertEqual(rc, 2)
        self.assertIn("seq.py - ", out)

    def test_missing_root(self):
        rc, out = self.run_seq("check", os.path.join(self.tmp.name, "nope"))
        self.assertEqual(rc, 2, out)

    def test_unknown_option(self):
        rc, out = self.run_seq("next", self.root, "--domain", "onb")
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
