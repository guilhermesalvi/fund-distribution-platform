"""Consistencia deterministica entre documentacao e scripts da skill:
todo link Markdown local (fora de bloco de codigo) resolve; toda flag `--x` citada junto do nome de um script
existe no argparse desse script; fences de codigo fecham; toda citacao
`arquivo.md, Titulo` a arquivos desta skill aponta para heading ou trecho em
negrito existente.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_docs_consistency.py"
"""

import glob
import os
import re
import unicodedata
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.dirname(SCRIPTS)


def md_files(skill):
    return [os.path.join(skill, "SKILL.md")] + sorted(glob.glob(os.path.join(skill, "references", "*.md")))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9&\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fenced_line_mask(lines):
    """True para linhas dentro de bloco de codigo (``` ou ~~~), fences inclusos."""
    mask, open_ch, open_len = [], None, 0
    for l in lines:
        m = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", l)
        if open_ch is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                open_ch, open_len = m.group(1)[0], len(m.group(1))
                mask.append(True)
                continue
            mask.append(False)
        else:
            mask.append(True)
            if m and m.group(1)[0] == open_ch and len(m.group(1)) >= open_len and not m.group(2).strip():
                open_ch = None
    return mask


def fence_unclosed(lines):
    open_ch, open_len = None, 0
    for l in lines:
        m = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", l)
        if open_ch is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                open_ch, open_len = m.group(1)[0], len(m.group(1))
        elif m and m.group(1)[0] == open_ch and len(m.group(1)) >= open_len and not m.group(2).strip():
            open_ch = None
    return open_ch is not None


def script_flags(path):
    """Toda flag literal `"--x"` presente no fonte (argparse ou parse manual)."""
    return set(re.findall(r"[\"'](--[a-z][a-z0-9-]*)[\"']", read(path)))


OWN_FILES = "intake|writing|output|review|example"
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
    want = norm(first)
    heads = {norm(h) for h in raw_heads}
    bold = {norm(b) for b in re.findall(r"\*\*([^*\n]+)\*\*", doc_text)}
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
            self.assertFalse(fence_unclosed(read(md).splitlines()), f"{md}: fence sem fechamento")

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


if __name__ == "__main__":
    unittest.main()
