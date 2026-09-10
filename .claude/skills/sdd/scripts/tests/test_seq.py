"""Testes de seq.py: proximo numero (max+1), forma do slug, numero duplicado
na pasta, o que conta como item numerado (subpasta de mudanca ou arquivo de
ADR, so filhos diretos) e erros de uso.

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
        self.root = os.path.join(self.tmp.name, "docs", "specs", "offering", "offer-lifecycle")
        os.makedirs(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content="# X\n"):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def mkdir(self, rel):
        p = os.path.join(self.root, rel)
        os.makedirs(p, exist_ok=True)
        return p

    def run_seq(self, *args):
        r = subprocess.run([sys.executable, SEQ, *args], capture_output=True,
                           text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr


class NextTests(SeqCase):
    def test_next_is_max_plus_one_over_change_folders(self):
        self.mkdir("0001-partial-reservation")
        self.mkdir("0003-book-freeze")
        rc, out = self.run_seq("next", self.root, "--slug", "book-reopen")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0004-book-reopen")
        rc, out = self.run_seq("next", self.root)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0004")

    def test_adr_files_count(self):
        self.write("0001-outbox.md")
        self.write("0002-versioning.MD")
        rc, out = self.run_seq("next", self.root, "--slug", "retention")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0003-retention")

    def test_empty_folder_starts_at_0001(self):
        rc, out = self.run_seq("next", self.root, "--slug", "first")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0001-first")

    def test_invalid_slug_is_rejected(self):
        for slug in ("Book-Z", "book_z", "book--z", "book-", "book z"):
            rc, out = self.run_seq("next", self.root, "--slug", slug)
            self.assertEqual(rc, 1, out)
            self.assertIn("kebab-case", out)

    def test_only_direct_children_and_numbered_names_count(self):
        self.mkdir("0001-partial-reservation")
        self.write("spec.md")
        self.write("README.md")
        self.mkdir("notes")
        self.mkdir(".hidden/0009-not")
        self.mkdir("0001-partial-reservation/0007-nested")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)
        self.assertIn("1 item(ns)", out)
        rc, out = self.run_seq("next", self.root)
        self.assertEqual(out.strip(), "0002")


class DuplicateTests(SeqCase):
    def test_duplicate_number_is_hard(self):
        self.mkdir("0001-partial-reservation")
        self.mkdir("0001-book-freeze")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)
        self.assertIn("HARD  numero 0001 usado por mais de um item", out)
        rc, out = self.run_seq("next", self.root, "--slug", "z")
        self.assertEqual(rc, 1, out)
        self.assertNotIn("0002", out)

    def test_folder_and_file_with_same_number_is_hard(self):
        self.mkdir("0002-book-freeze")
        self.write("0002-book-freeze.md")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)

    def test_check_green_without_duplicates(self):
        self.mkdir("0001-partial-reservation")
        self.mkdir("0005-book-freeze")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)
        self.assertFalse(any(l.startswith("HARD") for l in out.splitlines()), out)


class ContractTests(SeqCase):
    def test_no_args_prints_docstring_and_exits_2(self):
        rc, out = self.run_seq()
        self.assertEqual(rc, 2)
        self.assertIn("seq.py - ", out)

    def test_missing_dir(self):
        rc, out = self.run_seq("check", os.path.join(self.tmp.name, "nope"))
        self.assertEqual(rc, 2, out)

    def test_unknown_option(self):
        rc, out = self.run_seq("next", self.root, "--domain", "offering")
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
