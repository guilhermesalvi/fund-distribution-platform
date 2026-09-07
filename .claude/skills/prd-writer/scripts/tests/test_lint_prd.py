"""Testes de lint_prd.py: header (Status, Autor, Data), secoes por igualdade,
Functional Requirements obrigatoria, fence, substituicao (ciclo de vida),
descoberta de PRDs (flat, nested, pasta), PRD 0000, flag omit e links locais.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_prd.py"
"""

import contextlib
import io
import itertools
import os
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import lint_prd  # noqa: E402


_FACT_SEQ = itertools.count(1)


def prd(status="Rascunho", autor="A. Souza", data="2026-09-05", prefix="ONB",
        header_extra="", tier="media", frs=True, nfr=False, title="Feature X",
        body_extra="", perguntas="Nenhuma."):
    # [FATO] unico por PRD gerado: fato identico em dois PRDs e HARD legitimo.
    fact_id = next(_FACT_SEQ)
    text = f"""<!-- prd-tier: {tier} -->
# {title}

| | |
|---|---|
| **Status** | {status} |
| **Autor** | {autor} |
| **Data** | {data} |
{header_extra}
Prefixo dos requisitos: `{prefix}`.

## Contexto e Problema

[FATO] problema do {title} (fato {fact_id}).

## Usuário-alvo / JTBD

- operador: job.

## Solução Proposta

Capability.
"""
    if frs:
        text += f"\n## Functional Requirements\n\n- **{prefix}-01 (Must)** condicao.\n"
    if nfr:
        text += f"\n## Non-functional Requirements\n\n- **{prefix}-NFR-01** atributo.\n"
    text += f"""
## Não-objetivos

- nada.

## Métricas de Sucesso

- leading
- lagging
- guardrail

## Critérios de Aceitação

| caso | entrada |
|---|---|
| a | 1 |

## Dependências e Riscos

| item | tipo |
|---|---|
| x | y |

## Resumo Executivo

resumo.

## Perguntas em Aberto

{perguntas}
{body_extra}
## Ponto de Maior Fragilidade

decisao.
"""
    return text


def overview(prefixes=("ONB",)):
    rows = "\n".join(f"| Ctx{p} | resp | [x](#contextos) | `{p}` | up |" for p in prefixes)
    return f"""<!-- prd-tier: overview -->
# Visão Geral

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | A. Souza |
| **Data** | 2026-09-05 |
| **Escopo** | tudo |

## Propósito

[FATO] proposito.

## Contextos

| Contexto | Responsabilidade | PRD | Prefixo de ID | Posição |
|---|---|---|---|---|
{rows}

## Catálogo de eventos

| Evento | Produtor |
|---|---|

## Fluxos entre contextos

texto.
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
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(lint_prd.lint_mermaid, "check_files",
                                  side_effect=lambda paths: ([], 0)):
            rc = lint_prd.main(["lint_prd"] + list(targets or [self.root]))
        return rc, out.getvalue() + err.getvalue()

    def assert_hard(self, out, needle):
        hard = [ln for ln in out.splitlines() if ln.startswith("HARD")]
        self.assertTrue(any(needle in ln for ln in hard),
                        f"HARD com '{needle}' nao encontrado em:\n{out}")

    def assert_no_hard(self, rc, out):
        self.assertEqual(rc, 0, out)
        hard = [ln for ln in out.splitlines() if ln.startswith("HARD")]
        self.assertEqual(hard, [], out)

    def assert_warn(self, out, needle):
        warn = [ln for ln in out.splitlines() if ln.startswith("WARN")]
        self.assertTrue(any(needle in ln for ln in warn),
                        f"WARN com '{needle}' nao encontrado em:\n{out}")


class HeaderTests(LintCase):
    def test_valid_prd_is_green(self):
        self.write("0001-onb-x.md", prd())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_status_outside_enumeration_is_hard(self):
        self.write("0001-onb-x.md", prd(status="Banana"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "Status 'Banana' fora da enumeracao")

    def test_status_enumeration_pt_en(self):
        for i, st in enumerate(["Rascunho", "Em Revisão", "Aprovado", "Draft",
                                "In Review", "Approved"], start=1):
            self.write(f"{i:04d}-onb-x{i}.md", prd(status=st, prefix=f"P{i}"))
        self.write("0000-platform-overview.md",
                   overview(tuple(f"P{i}" for i in range(1, 7))))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_author_placeholder_is_hard(self):
        for i, autor in enumerate(["[nome]", "[name]", "", "TBD"], start=1):
            self.write(f"{i:04d}-onb-x{i}.md", prd(autor=autor, prefix=f"P{i}"))
        self.write("0000-platform-overview.md", overview(("P1", "P2", "P3", "P4")))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assertEqual(out.count("campo Autor nao preenchido"), 4, out)

    def test_invalid_calendar_date_is_hard(self):
        self.write("0001-onb-x.md", prd(data="2026-99-99"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "nao e data de calendario valida")

    def test_invalid_date_format_is_hard(self):
        self.write("0001-onb-x.md", prd(data="05/09/2026"))
        rc, out = self.run_lint()
        self.assert_hard(out, "formato de Data invalido")


class SectionTests(LintCase):
    def test_nfr_without_fr_is_hard(self):
        self.write("0001-onb-x.md", prd(frs=False, nfr=True, tier="complexa"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "Non-functional Requirements sem secao Functional Requirements")

    def test_non_functional_heading_does_not_satisfy_fr(self):
        text = prd(frs=False, nfr=True, tier="complexa")
        doc = lint_prd.Doc(self.write("0001-onb-x.md", text))
        self.assertTrue(doc.has_section("nfrs"))
        self.assertFalse(doc.has_section("frs"))

    def test_ids_defined_without_fr_section_is_hard(self):
        text = prd(frs=False, body_extra="\n## Regras\n\n- **ONB-01 (Must)** regra.\n")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "sem secao Functional Requirements")

    def test_heading_with_parenthetical_alias(self):
        text = prd().replace("## Contexto e Problema", "## Contexto e Problema (Context)")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_decisions_taken_in_open_questions(self):
        self.write("0001-onb-x.md", prd(perguntas="Decisões tomadas:\n- a."))
        rc, out = self.run_lint()
        self.assert_hard(out, "decisao tomada vive em Trade-offs ou no FR")

    def test_omit_silences_expected_section_warn(self):
        text = prd().replace("<!-- prd-tier: media -->",
                             "<!-- prd-tier: media | omit: aceitacao,dependencias -->")
        text = text.replace("## Critérios de Aceitação\n\n| caso | entrada |\n|---|---|\n| a | 1 |\n", "")
        text = text.replace("## Dependências e Riscos\n\n| item | tipo |\n|---|---|\n| x | y |\n", "")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_omit_does_not_silence_hard(self):
        text = prd().replace("<!-- prd-tier: media -->",
                             "<!-- prd-tier: media | omit: contexto -->")
        start = text.index("## Contexto e Problema")
        end = text.index("## Usuário-alvo")
        text = text[:start] + text[end:]
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assertEqual(rc, 1, out)
        self.assert_hard(out, "Contexto e Problema")

    def test_omit_unknown_key_is_warn(self):
        text = prd().replace("<!-- prd-tier: media -->",
                             "<!-- prd-tier: media | omit: banana -->")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "omit: chave desconhecida 'banana'")

    def test_omit_missing_section_without_flag_is_warn(self):
        text = prd().replace("## Critérios de Aceitação\n\n| caso | entrada |\n|---|---|\n| a | 1 |\n", "")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "declare 'omit: aceitacao'")


class FenceTests(LintCase):
    def test_definitions_headings_and_tags_inside_fence_are_ignored(self):
        fenced = ("\n```\n- **ONB-01 (Must)** duplicata.\n## Non-functional Requirements\n"
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

    def test_mermaid_blocks_still_reach_lint_mermaid(self):
        text = prd(body_extra="\n```mermaid\nflowchart TD\n A-->B\n```\n")
        p = self.write("0001-onb-x.md", text)
        seen = []
        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(lint_prd.lint_mermaid, "check_files",
                                  side_effect=lambda paths: (seen.extend(paths), ([], 1))[1]):
            lint_prd.main(["lint_prd", self.root])
        self.assertEqual(seen, [p])


class SupersessionTests(LintCase):
    def old(self, by="0002", **kw):
        return prd(status=f"Substituído por {by}", **kw)

    def new(self, old="0001", **kw):
        return prd(header_extra=f"| **Substitui** | {old} |", **kw)

    def test_valid_supersession_keeps_ids_and_facts(self):
        self.write("0001-onb-x.md", self.old())
        self.write("0002-onb-x.md", self.new())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_citation_to_id_only_in_historical_prd_is_warn(self):
        self.write("0001-onb-x.md", self.old(body_extra="\n- **ONB-07 (Must)** antiga.\n"))
        self.write("0002-onb-x.md", self.new())
        self.write("0003-onb-y.md", prd(prefix="OTH", body_extra="\nVer ONB-07.\n"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "cita ID de PRD substituido: ONB-07")

    def test_orphan_superseded_by_is_hard(self):
        self.write("0001-onb-x.md", self.old(by="0009"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "Substituido por 0009', mas nenhum PRD")

    def test_supersedes_nonexistent_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-onb-y.md", self.new(old="0007", prefix="OTH"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "Substitui 0007: nenhum PRD")

    def test_non_reciprocal_old_side_missing_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-onb-x.md", self.new())
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "nao declara Status 'Substituido por 0002'")

    def test_non_reciprocal_new_side_missing_is_hard(self):
        self.write("0001-onb-x.md", self.old())
        self.write("0002-onb-x.md", prd())
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "nao declara '| **Substitui** | 0001 |'")

    def test_cycle_is_hard(self):
        self.write("0001-onb-x.md", prd(status="Substituído por 0002",
                                        header_extra="| **Substitui** | 0002 |"))
        self.write("0002-onb-x.md", prd(status="Substituído por 0001",
                                        header_extra="| **Substitui** | 0001 |"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "ciclo de substituicao (0001 -> 0002)")

    def test_two_active_successors_is_hard(self):
        self.write("0001-onb-x.md", self.old())
        self.write("0002-onb-x.md", self.new())
        self.write("0003-onb-x.md", self.new())
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "mais de um sucessor ativo")

    def test_status_superseded_in_english(self):
        self.write("0001-onb-x.md", prd(status="Superseded by 0002"))
        self.write("0002-onb-x.md", prd(header_extra="| **Supersedes** | 0001 |"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


class DiscoveryTests(LintCase):
    def test_folder_prd_only_prd_md_is_linted(self):
        self.write("0001-onb-x/prd.md", prd())
        self.write("0001-onb-x/decisions.md", "# Decisoes\n\ntexto sem header.\n")
        self.write("0001-onb-x/assets/notes.md", "# Nota\n")
        self.write("README.md", "# Indice\n")
        self.write("0002-onb-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertIn("3 PRD(s)", out)
        self.assertNotIn("decisions.md", out)

    def test_prd_files_discovery(self):
        self.write("0001-onb-x/prd.md", prd())
        self.write("0001-onb-x/decisions.md", "# D\n")
        self.write("README.md", "# I\n")
        self.write("0002-onb-y.md", prd())
        self.write("notes.md", "# N\n")
        found = [os.path.relpath(p, self.root).replace("\\", "/")
                 for p in lint_prd.prd_files(self.root)]
        self.assertEqual(found, ["0001-onb-x/prd.md", "0002-onb-y.md"])

    def test_explicit_non_prd_file_is_usage_error(self):
        p = self.write("0001-onb-x/decisions.md", "# D\n")
        self.write("0001-onb-x/prd.md", prd())
        rc, out = self.run_lint(p)
        self.assertEqual(rc, 2)
        self.assertIn("nao e PRD", out)

    def test_single_folder_prd_target_uses_parent_root(self):
        p = self.write("0001-onb-x/prd.md", prd())
        self.write("0002-onb-y.md", prd(prefix="OTH", body_extra="\nVer ONB-01.\n"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint(p)
        self.assert_no_hard(rc, out)
        self.assertIn("1 PRD(s)", out)

    def test_nested_layout(self):
        self.write("onb/0001-x.md", prd())
        self.write("oth/0002-y/prd.md", prd(prefix="OTH", body_extra="\nCita ONB-01.\n"))
        self.write("oth/0002-y/decisions.md", "# D\n")
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertIn("3 PRD(s)", out)

    def test_nested_duplicate_id_across_domains_is_hard(self):
        self.write("onb/0001-x.md", prd())
        self.write("oth/0002-y.md", prd())
        self.write("0000-overview.md", overview(("ONB",)))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "ID ONB-01 definido mais de uma vez")


class OverviewTests(LintCase):
    def test_overview_with_all_prefixes_is_green(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_two_prefixes_without_overview_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "sem PRD 0000")

    def test_overview_missing_prefix_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview.md", overview(("ONB",)))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1)
        self.assert_hard(out, "prefixo `OTH`")

    def test_overview_defining_requirement_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview.md",
                   overview(("ONB", "OTH")) + "\n- **ONB-09 (Must)** regra.\n")
        rc, out = self.run_lint()
        self.assert_hard(out, "PRD 0000 define o requisito ONB-09")

    def test_folder_overview_is_overview(self):
        self.write("0001-onb-x.md", prd())
        self.write("0002-oth-y.md", prd(prefix="OTH"))
        self.write("0000-platform-overview/prd.md", overview(("ONB", "OTH")))
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

    def test_nested_layout_link_is_relative_to_prd_folder(self):
        self.write("onb/0001-x/prd.md", prd(body_extra="\nVeja [0000](../../0000-overview.md) e [dec](decisions.md).\n"))
        self.write("onb/0001-x/decisions.md", "# D\n")
        self.write("0000-overview.md", overview(("ONB",)))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_url_anchor_code_span_and_fence_are_ignored(self):
        body = ("\nFontes: [CVM](https://example.org/a.pdf), [sec](#contexto), `[x](nao/existe.md)`\n\n"
                "```markdown\n[y](nao/existe/tambem.md)\n```\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


if __name__ == "__main__":
    unittest.main()
