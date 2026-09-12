"""Consistencia deterministica entre documentacao e scripts da skill:
todo link Markdown local (fora de bloco de codigo) resolve; toda flag `--x`
citada junto do nome de um script existe nesse script; fences de codigo
fecham; toda citacao `arquivo.md, Titulo` aponta para heading ou trecho em
negrito existente; a skill nao cita outra skill nem a si mesma pelo caminho;
nenhum artefato, template ou linter carrega campo de status, autor, data,
confianca ou aprovacao.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_docs_consistency.py"
"""

import glob
import os
import re
import sys
import unittest
from unittest.mock import patch

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)
from _common import fenced_line_mask, norm_heading  # noqa: E402


def md_files(skill):
    return [os.path.join(skill, "SKILL.md")] + sorted(glob.glob(os.path.join(skill, "references", "*.md")))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def fence_unclosed(lines):
    """Track fence character and minimum closing length independently."""
    open_char, open_length = None, 0
    for line in lines:
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if open_char is None:
            if match and not (match.group(1)[0] == "`" and "`" in match.group(2)):
                open_char, open_length = match.group(1)[0], len(match.group(1))
        elif (match and match.group(1)[0] == open_char
              and len(match.group(1)) >= open_length and not match.group(2).strip()):
            open_char = None
    return open_char is not None


def script_flags(path):
    """Toda flag literal `"--x"` presente no fonte (argparse ou parse manual)."""
    return set(re.findall(r"[\"'](--[a-z][a-z0-9-]*)[\"']", read(path)))


OWN_FILES = "specify|design|tasks|execute|verify|adr|workflow|validation|prose|SKILL"
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

    def test_independence_from_other_skills(self):
        """Nenhuma mencao a outra skill (pelo caminho `skills/prd`: "prd"
        sozinho e o artefato, nao a skill), a arquivos dela ou a arquivos que
        esta skill nao tem mais; a propria skill nunca e citada pelo caminho
        em referencia, template ou script. O acoplamento e so pelo artefato
        (PRD em /docs/prd)."""
        others = re.compile(r"skills/prd\b|intake\.md|writing\.md|output\.md|review\.md|modes\.md|memory\.md",
                            re.IGNORECASE)
        own_name = re.compile(r"skills/sdd\b", re.IGNORECASE)
        for path in md_files(SKILL) + sorted(glob.glob(os.path.join(SCRIPTS, "*.py"))):
            for i, line in enumerate(read(path).splitlines(), 1):
                self.assertIsNone(others.search(line), f"{path}:{i}: cita outra skill: {line.strip()[:80]}")
                allowed = path.endswith("SKILL.md") and (line.startswith("name: ") or line.startswith("# "))
                if not allowed:
                    self.assertIsNone(own_name.search(line), f"{path}:{i}: cita a propria skill pelo nome: {line.strip()[:80]}")

    def test_no_status_author_date_or_confidence_fields(self):
        """Aprovacao e o commit: nenhum campo de Status, Autor, Data, Confianca
        ou aprovacao em template ou linter."""
        field = re.compile(r"^\|\s*\*\*(Status|Autor|Author|Data|Date|Confian[cç]a|Confidence|Aprovad[oa]|Approved)\*\*\s*\|",
                           re.IGNORECASE)
        for md in md_files(SKILL):
            for i, line in enumerate(read(md).splitlines(), 1):
                self.assertIsNone(field.search(line), f"{md}:{i}: campo de status/autor/data/confianca: {line.strip()}")
        for py in glob.glob(os.path.join(SCRIPTS, "*.py")):
            self.assertNotRegex(read(py), r"(?i)\b(STATUS_DELTA|STATUS_LIVING|HEADER_FIELDS|TIERS)\b",
                                f"{py}: linter ainda conhece status/tier")

    def test_no_commit_policy_in_scripts(self):
        """Politica de commit e do repositorio: os scripts nao validam
        mensagem nem recebem opcao de commit."""
        for py in glob.glob(os.path.join(SCRIPTS, "*.py")):
            self.assertNotRegex(read(py), r"--commit-|check_commit|Conventional Commits", f"{py}: politica de commit no linter")


class DocumentationRegressionFixtures(unittest.TestCase):
    """Positive and negative text fixtures exercise the existing checks."""

    def test_new_reference_citations_resolve(self):
        cases = (("workflow", "Aprovação e autorizações"),
                 ("validation", "Scripts"),
                 ("prose", "Convenções de escrita"))
        for name, heading in cases:
            with self.subTest(reference=name):
                text = read(os.path.join(SKILL, "references", name + ".md"))
                citations = cited_sections(f"({name}.md, {heading})", OWN_FILES)
                self.assertEqual(citations, [(name + ".md", heading, 1)])
                self.assertTrue(section_exists(text, heading))
                self.assertFalse(section_exists(text, "Heading inexistente de fixture"))

    def test_removed_root_headings_fail(self):
        root = read(os.path.join(SKILL, "SKILL.md"))
        for heading in ("Abrir uma mudança", "Scripts", "Revisão por entrada", "Idioma"):
            with self.subTest(heading=heading):
                self.assertFalse(section_exists(root, heading))

    def run_document_check(self, method, text):
        fixture = os.path.join(SKILL, "fixture.md")
        with patch(__name__ + ".md_files", return_value=[fixture]), \
                patch(__name__ + ".read", return_value=text):
            getattr(DocsConsistency(method), method)()

    def test_existing_markdown_link_passes(self):
        self.run_document_check("test_internal_links_resolve",
                                "[Escrita](references/prose.md)")

    def test_missing_markdown_link_fails(self):
        with self.assertRaises(AssertionError):
            self.run_document_check("test_internal_links_resolve",
                                    "[Escrita](references/absent-fixture.md)")

    def test_closed_fence_passes(self):
        for opening, closing in (("```text", "```"), ("````text", "`````"),
                                 ("~~~text", "~~~"), ("~~~~text", "~~~~~")):
            with self.subTest(opening=opening, closing=closing):
                self.run_document_check("test_fences_close", f"{opening}\nexample\n{closing}\n")

    def test_open_fence_fails(self):
        for text in ("```text\nexample\n", "````text\nexample\n```\n",
                     "```text\nexample\n~~~\n", "~~~text\nexample\n```\n",
                     "```\n", "~~~~\n"):
            with self.subTest(text=text), self.assertRaisesRegex(AssertionError, "fence sem fechamento"):
                self.run_document_check("test_fences_close", text)


if __name__ == "__main__":
    unittest.main()
