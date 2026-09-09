"""Testes de lint_prd.py: H1 e secoes obrigatorias por igualdade, Requisitos
Funcionais quando ha IDs, prefixo e definicoes, fence, IDs entre PRDs, PRD
0000, links locais e as heuristicas WARN.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_prd.py"
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import lint_prd  # noqa: E402


def prd(prefix="ONB", frs=True, nfr=False, title="Feature X", body_extra="",
        prefix_line=True):
    text = f"""# {title}

| | |
|---|---|
| **Contexto Originário** | Ctx{prefix} |

"""
    if prefix_line:
        text += f"Prefixo dos requisitos: `{prefix}`.\n"
    text += f"""
## Contexto e Problema

problema do {title}.

## Usuário-alvo / JTBD

- operador: job.

## Solução Proposta

Capability.
"""
    if frs:
        text += f"\n## Requisitos Funcionais\n\n- **{prefix}-01 (Must)** condicao.\n"
    if nfr:
        text += f"\n## Requisitos Não Funcionais\n\n- **{prefix}-NFR-01** atributo.\n"
    return text + body_extra


def overview(prefixes=("ONB",), comment=True):
    rows = "\n".join(f"| Ctx{p} | resp | [x](#contextos) | `{p}` | up |" for p in prefixes)
    head = "<!-- prd: overview -->\n" if comment else ""
    return head + f"""# Visão Geral

| | |
|---|---|
| **Escopo** | tudo |

## Propósito

proposito.

## Contextos

| Contexto | Responsabilidade | PRD | Prefixo de ID | Posição |
|---|---|---|---|---|
{rows}
"""


class LintCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "docs", "prd")
        os.makedirs(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, rel, content):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def run_lint(self, *targets):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = lint_prd.main(["lint_prd"] + list(targets or [self.root]))
        return rc, out.getvalue() + err.getvalue()

    def assert_hard(self, out, needle):
        hard = [ln for ln in out.splitlines() if ln.startswith("HARD")]
        self.assertTrue(any(needle in ln for ln in hard),
                        f"HARD com '{needle}' nao encontrado em:\n{out}")

    def assert_no_hard(self, rc, out):
        self.assertEqual(rc, 0, out)
        self.assertEqual([ln for ln in out.splitlines() if ln.startswith("HARD")], [], out)

    def assert_warn(self, out, needle):
        warn = [ln for ln in out.splitlines() if ln.startswith("WARN")]
        self.assertTrue(any(needle in ln for ln in warn),
                        f"WARN com '{needle}' nao encontrado em:\n{out}")

    def hard_for(self, text, needle, extra_files=()):
        self.write("0001-onb-x.md", text)
        for rel, content in extra_files:
            self.write(rel, content)
        rc, out = self.run_lint()
        self.assertEqual(rc, 1, out)
        self.assert_hard(out, needle)


class SkeletonTests(LintCase):
    def test_valid_prd_is_green(self):
        self.write("0001-onb-x.md", prd(nfr=True))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_missing_h1(self):
        self.hard_for(prd().replace("# Feature X\n", ""), "titulo H1")

    def test_required_section_missing(self):
        self.hard_for(prd().replace("## Contexto e Problema\n", "## Cenario\n"),
                      "secao obrigatoria ausente: Contexto e Problema")

    def test_heading_with_parenthetical_alias(self):
        text = prd().replace("## Contexto e Problema", "## Contexto e Problema (Context)")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_english_headings_are_aliases(self):
        text = prd(nfr=True).replace("## Requisitos Funcionais", "## Functional Requirements")
        text = text.replace("## Requisitos Não Funcionais", "## Non-functional Requirements")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_ids_without_fr_section_is_hard(self):
        self.hard_for(prd(frs=False, body_extra="\n## Regras\n\n- **ONB-01 (Must)** regra.\n"),
                      "sem secao Requisitos Funcionais")

    def test_nfr_only_ids_without_fr_section_is_hard(self):
        self.hard_for(prd(frs=False, nfr=True), "sem secao Requisitos Funcionais")

    def test_non_functional_heading_does_not_satisfy_fr(self):
        doc = lint_prd.Doc(self.write("0001-onb-x.md", prd(frs=False, nfr=True)))
        self.assertFalse(doc.has_section("frs"))

    def test_prd_without_ids_needs_no_prefix_or_fr_section(self):
        self.write("0001-onb-x.md", prd(frs=False, prefix_line=False))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_ids_without_prefix_line_is_hard(self):
        self.hard_for(prd(prefix_line=False), "sem prefixo declarado")

    def test_definition_with_other_prefix_is_hard(self):
        self.hard_for(prd(body_extra="\n- **OTH-02 (Must)** regra.\n"),
                      "definido com prefixo 'OTH', mas o PRD declara 'ONB'")

    def test_bare_fr_id_without_context_prefix(self):
        self.hard_for(prd(body_extra="\nVeja FR-03.\n"), "ID sem prefixo de contexto: 'FR-03'")

    def test_overview_comment_is_ignored_outside_first_lines(self):
        """O comentario identifica a visao geral onde estiver fora de fence;
        dentro de fence nao conta."""
        text = prd() + "\n```markdown\n<!-- prd: overview -->\n```\n"
        doc = lint_prd.Doc(self.write("0001-onb-x.md", text))
        self.assertFalse(doc.is_overview)


class FenceTests(LintCase):
    def test_definitions_headings_and_tags_inside_fence_are_ignored(self):
        fenced = ("\n```\n- **ONB-01 (Must)** duplicata.\n## Requisitos Não Funcionais\n"
                  "[TIPO] tag invalida\nTODO placeholder\nONB-99 citacao\n```\n")
        self.write("0001-onb-x.md", prd(body_extra=fenced))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_tilde_fence_and_longer_close(self):
        fenced = "\n~~~\n- **ONB-01 (Must)** dup.\n```\n- **ONB-01 (Must)** dup.\n~~~~\n"
        self.write("0001-onb-x.md", prd(body_extra=fenced))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_shorter_close_does_not_end_fence(self):
        lines = ["a", "````", "b", "```", "c", "````", "d"]
        self.assertEqual(lint_prd.fence_mask(lines),
                         [False, True, True, True, True, True, False])


class WarnTests(LintCase):
    def test_unknown_tag_is_warn(self):
        self.write("0001-onb-x.md", prd(body_extra="\n[PREMISA] algo.\n\n[FATO] outro.\n"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "tag nao reconhecida: '[PREMISA]'")
        self.assert_warn(out, "tag nao reconhecida: '[FATO]'")

    def test_allowed_tags_are_silent(self):
        body = "\n[PREMISSA] algo.\n\n- [LACUNA] falta.\n\n**[PREMISSA] em negrito; se falsa, cai.**\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_placeholder_is_warn(self):
        self.write("0001-onb-x.md", prd(body_extra="\nLimite: TBD.\n\nDono: [nome].\n"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "placeholder nao preenchido: 'TBD'")
        self.assert_warn(out, "placeholder nao preenchido: '[nome]'")

    def test_hedging_and_meta_narration_are_warn(self):
        self.write("0001-onb-x.md", prd(body_extra="\nEste PRD descreve algo que talvez mude.\n"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "hedging lexical: 'talvez'")
        self.assert_warn(out, "meta-narracao")

    def test_mechanism_in_solution_is_warn(self):
        text = prd().replace("Capability.", "Publicar no Kafka a cada mudanca.")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "mecanismo nomeado em secao de problem space: 'kafka'")

    def test_identical_paragraph_in_two_prds_is_warn(self):
        long = "\nO mercado exige liquidacao em D+2 para toda oferta publica de cotas de fundo fechado.\n"
        self.write("0001-onb-x.md", prd(body_extra=long))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y", body_extra=long))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "paragrafo identico em mais de um PRD")

    def test_short_identical_lines_are_not_paragraphs(self):
        short = "\nCada requisito e uma condicao verificavel.\n"
        self.write("0001-onb-x.md", prd(body_extra=short))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y", body_extra=short))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)


class CrossPrdTests(LintCase):
    def test_citation_without_definition(self):
        self.hard_for(prd(body_extra="\nDepende de ONB-77.\n"),
                      "citacao de ONB-77 nao resolve para nenhuma definicao")

    def test_citation_resolves_across_prds(self):
        self.write("0001-onb-x.md", prd(body_extra="\nVer OTH-01.\n"))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y"))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_duplicated_id_across_prds(self):
        self.hard_for(prd(), "ID ONB-01 definido mais de uma vez",
                      extra_files=(("0002-onb-y.md", prd(title="Feature Y")),))

    def test_unknown_prefix_citation_is_warn(self):
        self.write("0001-onb-x.md", prd(body_extra="\nVer ISO-27001.\n"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "prefixo 'ISO' que nenhum PRD da pasta declara")

    def test_single_file_target_uses_folder_index(self):
        p = self.write("0001-onb-x.md", prd(body_extra="\nVer OTH-01.\n"))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y"))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint(p)
        self.assert_no_hard(rc, out)
        self.assertIn("1 PRD(s)", out)


class DiscoveryTests(LintCase):
    def test_prd_files_discovery(self):
        self.write("0001-onb-x.md", prd())
        self.write("README.md", "# I\n")
        self.write("notes.md", "# N\n")
        self.write("assets/0009-not.md", "# A\n")
        self.write("onb/0002-y.md", prd())
        found = [os.path.relpath(p, self.root).replace("\\", "/")
                 for p in lint_prd.prd_files(self.root)]
        self.assertEqual(found, ["0001-onb-x.md", "onb/0002-y.md"])

    def test_explicit_non_prd_file_is_usage_error(self):
        p = self.write("notes.md", "# D\n")
        rc, out = self.run_lint(p)
        self.assertEqual(rc, 2)
        self.assertIn("nao e PRD", out)

    def test_nested_duplicate_id_across_folders_is_hard(self):
        self.write("onb/0001-x.md", prd())
        self.write("oth/0002-y.md", prd())
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "ID ONB-01 definido mais de uma vez")


class OverviewTests(LintCase):
    def test_overview_with_two_prefixes_is_green(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_two_prefixes_without_overview_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "sem PRD 0000")

    def test_overview_defining_requirement_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0000-platform-overview.md",
                   overview() + "\n- **ONB-09 (Must)** regra.\n")
        rc, out = self.run_lint()
        self.assert_hard(out, "PRD 0000 define o requisito ONB-09")

    def test_zero_file_without_comment_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH"), comment=False))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "sem '<!-- prd: overview -->'")

    def test_overview_needs_no_required_sections(self):
        self.write("0001-onb-x.md", prd())
        self.write("0000-platform-overview.md", overview())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


class LocalLinkTests(LintCase):
    """Link Markdown para arquivo local resolve a partir da pasta do PRD;
    URL, ancora pura, code span e bloco de codigo ficam fora."""

    def test_broken_relative_link_is_hard(self):
        self.write("0001-onb-x.md", prd(body_extra="\nVeja [PRD 0000](0000-overview.md).\n"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "link '0000-overview.md' nao resolve")

    def test_resolving_links_pass(self):
        self.write("0001-onb-x.md", prd(body_extra="\nVeja [PRD 0002](0002-oth-y.md#contexto) e [pasta](../prd).\n"))
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_link_is_relative_to_prd_folder(self):
        self.write("onb/0001-x.md", prd(body_extra="\nVeja [0000](../0000-overview.md) e [nota](notes.md).\n"))
        self.write("onb/notes.md", "# N\n")
        self.write("0000-overview.md", overview())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_root_relative_link_resolves_from_repo_root(self):
        self.write("0001-onb-x.md", prd(body_extra="\nVeja [spec](/docs/prd/0002-oth-y.md) e [x](/docs/nope.md).\n"))
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "link '/docs/nope.md' nao resolve")
        self.assertNotIn("0002-oth-y.md' nao resolve", out)

    def test_angle_bracket_link_with_space_is_checked(self):
        self.write("notas/ata reuniao.md", "# Ata\n")
        self.write("0001-onb-x.md", prd(body_extra="\nVeja [ata](<notas/ata reuniao.md>) e [x](<notas/nao existe.md>).\n"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "link 'notas/nao existe.md' nao resolve")
        self.assertNotIn("ata reuniao.md' nao resolve", out)

    def test_url_anchor_code_span_and_fence_are_ignored(self):
        body = ("\nFontes: [CVM](https://example.org/a.pdf), [sec](#contexto), `[x](nao/existe.md)`\n\n"
                "```markdown\n[y](nao/existe/tambem.md)\n```\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


if __name__ == "__main__":
    unittest.main()
