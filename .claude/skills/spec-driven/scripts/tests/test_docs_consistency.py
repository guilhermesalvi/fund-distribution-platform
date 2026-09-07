"""Consistencia deterministica entre documentacao e scripts da skill:
todo link Markdown local (fora de bloco de codigo) resolve; toda flag `--x` citada junto do nome de um script
existe no argparse desse script; fences de codigo fecham; a skill irma
(prd-writer) e citada em secoes que existem.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_docs_consistency.py"
"""

import glob
import os
import re
import sys
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.dirname(SCRIPTS)
SIBLING = os.path.join(os.path.dirname(SKILL), "prd-writer")
sys.path.insert(0, SCRIPTS)
from _common import fenced_line_mask, norm_heading  # noqa: E402


def md_files(skill):
    return [os.path.join(skill, "SKILL.md")] + sorted(glob.glob(os.path.join(skill, "references", "*.md")))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def script_flags(path):
    """Toda flag literal `"--x"` presente no fonte (argparse ou parse manual)."""
    return set(re.findall(r"[\"'](--[a-z][a-z0-9-]*)[\"']", read(path)))


class DocsConsistency(unittest.TestCase):
    def test_internal_links_resolve(self):
        """Todo link Markdown para arquivo local, fora de bloco de codigo e
        de code span, resolve a partir da pasta do documento (ancora
        removida); URL com esquema e ancora pura ficam fora."""
        for md in md_files(SKILL):
            lines = read(md).splitlines()
            mask = fenced_line_mask(lines)
            for i, line in enumerate(lines):
                if mask[i]:
                    continue
                for target in re.findall(r"\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", re.sub(r"`[^`]*`", "", line)):
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", target) or target.startswith("#"):
                        continue
                    rel = target.split("#", 1)[0]
                    if not rel:
                        continue
                    self.assertTrue(os.path.exists(os.path.join(os.path.dirname(md), rel)),
                                    f"{md}:{i + 1}: link {target} nao resolve")

    def test_fences_close(self):
        for md in md_files(SKILL):
            lines = read(md).splitlines()
            mask = fenced_line_mask(lines)
            # ultimo fence aberto sem fechamento mascara ate o fim: detecta pela
            # linha final ainda mascarada sem ser uma linha de fechamento
            if mask and mask[-1]:
                self.assertRegex(lines[-1].strip(), r"^(`{3,}|~{3,})\s*$", f"{md}: fence sem fechamento")

    def test_cited_flags_exist(self):
        """Flag `--x` citada numa linha pertence ao ultimo script nomeado antes
        dela na mesma linha (uma linha pode citar dois scripts)."""
        scripts = {os.path.basename(p): script_flags(p) for p in glob.glob(os.path.join(SCRIPTS, "*.py"))
                   if not os.path.basename(p).startswith("_")}
        names = sorted(scripts, key=len, reverse=True)
        for md in md_files(SKILL):
            for line in read(md).splitlines():
                marks = sorted((m.start(), n) for n in names for m in re.finditer(re.escape(n), line))
                if not marks:
                    continue
                for fm in re.finditer(r"(--[a-z][a-z0-9-]*)", line):
                    owner = None
                    for pos, n in marks:
                        if pos < fm.start():
                            owner = n
                    if owner is not None:
                        self.assertIn(fm.group(1), scripts[owner],
                                      f"{md}: flag {fm.group(1)} citada para {owner} nao existe")

    def test_sibling_citations_resolve(self):
        """Citacoes `(specify.md, Titulo)` feitas pelo prd-writer a esta skill
        apontam para heading (ou paragrafo em negrito) existente."""
        if not os.path.isdir(SIBLING):
            self.skipTest("prd-writer ausente")
        own = {os.path.basename(p): read(p) for p in md_files(SKILL)}
        for md in md_files(SIBLING):
            for fname, title in re.findall(r"(?:skill `spec-driven`, )([a-z]+\.md), ([^)\]]+?)[),]", read(md)):
                if fname not in own:
                    continue
                text = own[fname]
                heads = {norm_heading(h) for h in re.findall(r"^#{1,3}\s+(.+)$", text, re.M)}
                bold = {norm_heading(b) for b in re.findall(r"\*\*([^*]+)\*\*", text)}
                want = norm_heading(title.split(",")[0])
                ok = any(want in h or h.startswith(want) for h in heads | bold)
                self.assertTrue(ok, f"{md}: cita '{fname}, {title}' que nao existe em {fname}")


if __name__ == "__main__":
    unittest.main()
