"""Testes de seq.py (spec-driven): mudancas em changes/ em qualquer
profundidade, ADRs planos, unicidade global, next recusa sobre HARD,
--kind prd rejeitado.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_seq.py"
"""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEQ = os.path.join(SCRIPTS, "seq.py")


def adr(status="Ativa", extra=""):
    return f"""# ADR X

| | |
|---|---|
| **Status** | {status} |
| **Data** | 2026-09-05 |
{extra}
## Contexto

texto.
"""


class SeqCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def mk(self, rel, content=""):
        p = os.path.join(self.tmp.name, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def run_seq(self, *args):
        r = subprocess.run([sys.executable, SEQ, *args], capture_output=True,
                           text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr


class ChangeTests(SeqCase):
    def test_next_walks_nested_changes(self):
        self.mk("docs/specs/a/b/changes/0001-x/spec.md", "<!-- sdd: spec-delta -->\n# x\n")
        self.mk("docs/specs/c/d/changes/0002-y/spec.md", "<!-- sdd: spec-delta -->\n# y\n")
        rc, out = self.run_seq("next", os.path.join(self.tmp.name, "docs", "specs"), "--slug", "z")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0003-z")

    def test_duplicate_across_capabilities_blocks_next(self):
        self.mk("docs/specs/a/b/changes/0001-x/spec.md")
        self.mk("docs/specs/c/d/changes/0001-y/spec.md")
        root = os.path.join(self.tmp.name, "docs", "specs")
        rc, out = self.run_seq("check", root)
        self.assertEqual(rc, 1, out)
        self.assertIn("duplicado", out)
        rc, out = self.run_seq("next", root, "--slug", "z")
        self.assertNotEqual(rc, 0, out)

    def test_empty_root_starts_at_0001(self):
        root = os.path.join(self.tmp.name, "docs", "specs")
        os.makedirs(root)
        rc, out = self.run_seq("next", root, "--slug", "z")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0001-z")

    def test_bad_slug_rejected(self):
        root = os.path.join(self.tmp.name, "docs", "specs")
        os.makedirs(root)
        rc, out = self.run_seq("next", root, "--slug", "Bad_Slug")
        self.assertNotEqual(rc, 0, out)


class AdrTests(SeqCase):
    def test_next_adr(self):
        self.mk("docs/adr/0001-outbox.md", adr())
        rc, out = self.run_seq("next", os.path.join(self.tmp.name, "docs", "adr"), "--slug", "retry")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0002-retry")

    def test_supersedes_reciprocal_and_orphan(self):
        root = os.path.join(self.tmp.name, "docs", "adr")
        self.mk("docs/adr/0001-a.md", adr(status="Substituída por 0002"))
        self.mk("docs/adr/0002-a.md", adr(extra="| **Substitui** | 0001 |\n"))
        rc, out = self.run_seq("check", root)
        self.assertEqual(rc, 0, out)
        self.mk("docs/adr/0003-b.md", adr(status="Substituída por 0009"))
        rc, out = self.run_seq("check", root)
        self.assertEqual(rc, 1, out)


class ContractTests(SeqCase):
    def test_kind_prd_rejected(self):
        root = os.path.join(self.tmp.name, "docs", "prd")
        os.makedirs(root)
        rc, out = self.run_seq("check", root, "--kind", "prd")
        self.assertEqual(rc, 2, out)
        self.assertIn("prd-writer", out)

    def test_unknown_root_name_requires_kind(self):
        root = os.path.join(self.tmp.name, "stuff")
        os.makedirs(root)
        rc, out = self.run_seq("check", root)
        self.assertEqual(rc, 2, out)


class NoArgsTests(unittest.TestCase):
    def test_no_args_prints_docstring_and_exits_2(self):
        r = subprocess.run([sys.executable, SEQ], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 2)
        self.assertIn("seq.py - ", r.stderr)


if __name__ == "__main__":
    unittest.main()
