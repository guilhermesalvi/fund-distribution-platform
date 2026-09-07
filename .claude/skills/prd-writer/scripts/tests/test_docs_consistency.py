"""Consistencia deterministica entre documentacao e scripts da skill:
links internos resolvem; toda flag `--x` citada junto do nome de um script
existe no argparse desse script; fences de codigo fecham; citacoes a
secoes da skill irma (spec-driven) apontam para heading existente.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_docs_consistency.py"
"""

import glob
import os
import re
import unicodedata
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.dirname(SCRIPTS)
SIBLING = os.path.join(os.path.dirname(SKILL), "spec-driven")


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


class DocsConsistency(unittest.TestCase):
    def test_internal_links_resolve(self):
        for md in md_files(SKILL):
            base = os.path.dirname(md)
            for target in re.findall(r"\]\((references/[a-z_]+\.md|[a-z_]+\.md)\)", read(md)):
                cand = [os.path.join(base, target), os.path.join(SKILL, target)]
                self.assertTrue(any(os.path.exists(c) for c in cand), f"{md}: link {target} nao resolve")

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

    def test_sibling_citations_resolve(self):
        if not os.path.isdir(SIBLING):
            self.skipTest("spec-driven ausente")
        own = {os.path.basename(p): read(p) for p in md_files(SIBLING)}
        for md in md_files(SKILL):
            for fname, title in re.findall(r"skill `spec-driven`, ([a-z]+\.md), ([^)\]]+?)[),]", read(md)):
                self.assertIn(fname, own, f"{md}: cita {fname} inexistente na spec-driven")
                text = own[fname]
                heads = {norm(h) for h in re.findall(r"^#{1,3}\s+(.+)$", text, re.M)}
                want = norm(title.split(",")[0])
                self.assertTrue(any(want in h for h in heads), f"{md}: cita '{fname}, {title}' sem heading em {fname}")


if __name__ == "__main__":
    unittest.main()
