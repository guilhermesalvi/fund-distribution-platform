"""Testes de seq.py (prd-writer): layouts flat/nested, PRD plano e em pasta,
PRD 0000 via --overview, unicidade global do numero, consistencia check/next
e substituicao (reciproca, orfa, ciclo, nao anterior).

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_seq.py"
"""

import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEQ = os.path.join(SCRIPTS, "seq.py")


def header(status="Rascunho", extra=""):
    return f"""<!-- prd-tier: media -->
# X

| | |
|---|---|
| **Status** | {status} |
| **Autor** | A. Souza |
| **Data** | 2026-09-05 |
{extra}
## Contexto e Problema

texto.
"""


class SeqCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "docs", "prd")
        os.makedirs(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content=None):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content if content is not None else header())
        return p

    def run_seq(self, *args):
        r = subprocess.run([sys.executable, SEQ, *args], capture_output=True,
                           text=True, encoding="utf-8")
        return r.returncode, r.stdout + r.stderr


class FlatLayoutTests(SeqCase):
    def test_next_flat_plain_and_folder(self):
        self.write("0001-onb-x.md")
        self.write("0002-onb-y/prd.md")
        rc, out = self.run_seq("next", self.root, "--domain", "onb", "--slug", "z")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0003-onb-z")

    def test_check_flat_green(self):
        self.write("0001-onb-x.md")
        self.write("0002-onb-y/prd.md")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)
        self.assertNotIn("HARD", out.split("\n")[0])

    def test_folder_contents_are_not_prds(self):
        self.write("0001-onb-x/prd.md")
        self.write("0001-onb-x/decisions.md", "# decisoes\n")
        self.write("0001-onb-x/assets/note.md", "# nota\n")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)
        self.assertNotIn("legado", out)

    def test_overview_flat(self):
        self.write("0001-onb-x.md")
        rc, out = self.run_seq("next", self.root, "--overview", "--domain", "platform")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0000-platform-overview.md")

    def test_overview_refuses_when_exists(self):
        self.write("0000-platform-overview.md")
        self.write("0001-onb-x.md")
        rc, out = self.run_seq("next", self.root, "--overview", "--domain", "platform")
        self.assertNotEqual(rc, 0, out)
        self.assertIn("0000", out)

    def test_empty_root_requires_layout(self):
        rc, out = self.run_seq("next", self.root, "--domain", "onb", "--slug", "x")
        self.assertNotEqual(rc, 0, out)
        self.assertIn("--layout", out)
        rc, out = self.run_seq("next", self.root, "--domain", "onb", "--slug", "x",
                               "--layout", "flat")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0001-onb-x")


class NestedLayoutTests(SeqCase):
    def test_next_nested(self):
        self.write("onb/0001-x.md")
        self.write("oth/0002-y/prd.md")
        rc, out = self.run_seq("next", self.root, "--domain", "onb", "--slug", "z")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip().replace("\\", "/"), "onb/0003-z")

    def test_number_unique_across_domains(self):
        self.write("onb/0001-x.md")
        self.write("oth/0001-y.md")
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)
        self.assertIn("duplicado", out)
        rc, out = self.run_seq("next", self.root, "--domain", "onb", "--slug", "z")
        self.assertNotEqual(rc, 0, out)
        self.assertTrue(os.path.exists(os.path.join(self.root, "onb", "0001-x.md")))

    def test_overview_nested(self):
        self.write("onb/0001-x.md")
        rc, out = self.run_seq("next", self.root, "--overview")
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.strip(), "0000-overview.md")

    def test_mixed_layouts_warn(self):
        self.write("0001-onb-x.md")
        self.write("oth/0002-y.md")
        rc, out = self.run_seq("check", self.root)
        self.assertIn("WARN", out)
        self.assertIn("flat", out.lower())


class SupersedesTests(SeqCase):
    def test_reciprocal_ok(self):
        self.write("0001-onb-x.md", header(status="Substituído por 0002"))
        self.write("0002-onb-x.md", header(extra="| **Substitui** | 0001 |\n"))
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 0, out)

    def test_orphan_backlink(self):
        self.write("0001-onb-x.md", header(status="Substituído por 0009"))
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)
        rc2, out2 = self.run_seq("next", self.root, "--domain", "onb", "--slug", "z")
        self.assertNotEqual(rc2, 0, out2)

    def test_not_reciprocal(self):
        self.write("0001-onb-x.md")
        self.write("0002-onb-x.md", header(extra="| **Substitui** | 0001 |\n"))
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)

    def test_cycle(self):
        self.write("0001-onb-x.md", header(status="Substituído por 0002",
                                           extra="| **Substitui** | 0002 |\n"))
        self.write("0002-onb-x.md", header(status="Substituído por 0001",
                                           extra="| **Substitui** | 0001 |\n"))
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)

    def test_supersedes_not_earlier(self):
        self.write("0001-onb-x.md", header(extra="| **Substitui** | 0002 |\n"))
        self.write("0002-onb-x.md", header(status="Substituído por 0001"))
        rc, out = self.run_seq("check", self.root)
        self.assertEqual(rc, 1, out)


class ContractTests(SeqCase):
    def test_kind_change_rejected(self):
        rc, out = self.run_seq("check", self.root, "--kind", "change")
        self.assertEqual(rc, 2, out)

    def test_missing_root(self):
        rc, out = self.run_seq("check", os.path.join(self.tmp.name, "nope"))
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
