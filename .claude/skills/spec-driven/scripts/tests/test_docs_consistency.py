"""Consistencia deterministica entre documentacao e scripts da skill:
todo link Markdown local (fora de bloco de codigo) resolve; toda flag `--x` citada junto do nome de um script
existe no argparse desse script; fences de codigo fecham; toda citacao
`arquivo.md, Titulo` (a esta skill ou a irma prd-writer, nos dois sentidos)
aponta para heading ou trecho em negrito existente.

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


OWN_FILES = "specify|design|tasks|execute|verify|memory|modes"
SIBLING_FILES = "intake|writing|output|review|example"
CITATION_RE = r"\b(%s)\.md, ([^)\];|]+?)(?=[)\];]|, [A-Z]|\. |$)"


def cited_sections(text, files_alt):
    """(arquivo, titulo) para toda citacao `arquivo.md, Titulo` fora de bloco de
    codigo; o titulo termina no fecha-parenteses/colchete, ponto-e-virgula ou
    fim de linha."""
    out = []
    lines = text.splitlines()
    mask = fenced_line_mask(lines)
    for i, line in enumerate(lines):
        if mask[i]:
            continue
        for fname, title in re.findall(CITATION_RE % files_alt, line):
            out.append((fname + ".md", title.strip(), i + 1))
    return out


def section_exists(doc_text, title):
    """Titulo casa com heading (qualquer nivel) ou paragrafo/trecho em negrito,
    por igualdade normalizada ou prefixo; a vírgula separa subtitulo opcional."""
    first = re.sub(r"\s*\(.*$", "", title.split(",")[0]).strip()
    raw_heads = re.findall(r"^#{1,4}\s+(.+)$", doc_text, re.M)
    num = re.match(r"^(?:se[cç][aã]o|section)?\s*(\d+(?:\.\d+)*)$", first, re.IGNORECASE)
    if num:  # citacao por numero de secao: "seção 1", "2.4"
        return any(re.match(r"^" + re.escape(num.group(1)) + r"(?:[.\s]|$)", h.strip()) for h in raw_heads)
    want = norm_heading(first)
    heads = {norm_heading(h) for h in raw_heads}
    bold = {norm_heading(b) for b in re.findall(r"\*\*([^*\n]+)\*\*", doc_text)}
    return any(want == h or h.startswith(want) or want in h for h in heads | bold)


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
                for angled, plain in re.findall(r"\[[^\]]*\]\(\s*(?:<([^>]*)>|([^)\s]+))(?:\s+\"[^\"]*\")?\s*\)", re.sub(r"`[^`]*`", "", line)):
                    target = (angled or plain).strip()
                    if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", target) or target.startswith("#"):
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

    def test_own_citations_resolve(self):
        """Citacoes `arquivo.md, Titulo` a arquivos desta skill apontam para
        heading ou trecho em negrito existente."""
        own = {os.path.basename(p): read(p) for p in md_files(SKILL)}
        total = sum(len(cited_sections(read(md), OWN_FILES)) for md in md_files(SKILL))
        self.assertGreater(total, 0, "nenhuma citacao encontrada: regex de citacao morta")
        for md in md_files(SKILL):
            for fname, title, line in cited_sections(read(md), OWN_FILES):
                self.assertIn(fname, own, f"{md}:{line}: cita {fname} inexistente")
                self.assertTrue(section_exists(own[fname], title),
                                f"{md}:{line}: cita '{fname}, {title}' que nao existe em {fname}")

    def test_sibling_citations_resolve(self):
        """Citacoes desta skill a arquivos da skill irma (prd-writer) e da
        irma a esta skill apontam para heading ou trecho em negrito existente."""
        if not os.path.isdir(SIBLING):
            self.skipTest("prd-writer ausente")
        own = {os.path.basename(p): read(p) for p in md_files(SKILL)}
        sib = {os.path.basename(p): read(p) for p in md_files(SIBLING)}
        for md in md_files(SKILL):
            for fname, title, line in cited_sections(read(md), SIBLING_FILES):
                self.assertIn(fname, sib, f"{md}:{line}: cita {fname} inexistente na prd-writer")
                self.assertTrue(section_exists(sib[fname], title),
                                f"{md}:{line}: cita '{fname}, {title}' que nao existe em {fname} (prd-writer)")
        for md in md_files(SIBLING):
            for fname, title, line in cited_sections(read(md), OWN_FILES):
                self.assertIn(fname, own, f"{md}:{line}: cita {fname} inexistente nesta skill")
                self.assertTrue(section_exists(own[fname], title),
                                f"{md}:{line}: cita '{fname}, {title}' que nao existe em {fname}")


if __name__ == "__main__":
    unittest.main()
