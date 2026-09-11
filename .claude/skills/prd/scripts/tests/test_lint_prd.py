"""Testes de lint_prd.py: H1, campo do header (lista fechada de rotulos, com os
contextos do `; afeta` na tabela de Dependencias e Riscos) e
secoes obrigatorias por igualdade, Requisitos Funcionais quando ha IDs,
prefixo, MoSCoW e definicoes, fence, IDs entre PRDs, PRD 0000 e a referencia a
ele, links locais, as regras de secao (conteudo, ordem, contagem de linhas,
trade-off, guardrail, Ponto de Maior Fragilidade, premissa 'se falsa' de
Perguntas em Aberto, cenario Dado/Quando/Entao, bullet regulatorio), os
rotulos de diagrama, as heuristicas WARN, a
sincronizacao com a tabela de secoes de references/writing.md e a regressao do
PRD de references/example.md.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_prd.py"
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.dirname(SCRIPTS)
EXAMPLE_MD = os.path.join(SKILL, "references", "example.md")
WRITING_MD = os.path.join(SKILL, "references", "writing.md")
sys.path.insert(0, SCRIPTS)
import lint_prd  # noqa: E402


SUMMARY = """## Resumo Executivo

Problema: o registro da oferta acontece fora da plataforma.
Solução: a oferta ganha definição estável e estado explícito.
Métrica primária: nenhuma oferta publicada com atributo inválido.
"""


def prd(prefix="ONB", frs=True, nfr=False, title="Feature X", body_extra="",
        prefix_line=True, link_0000="", header_field="Contexto Originário",
        header_value=None, summary=SUMMARY):
    value = f"Ctx{prefix}" if header_value is None else header_value
    header = f"| **{header_field}** | {value} |\n" if header_field else ""
    text = f"""# {title}

| | |
|---|---|
{header}
"""
    if prefix_line:
        text += f"Prefixo dos requisitos: `{prefix}`."
        if link_0000:
            text += f" Visão geral: [PRD 0000]({link_0000})."
        text += "\n"
    if summary:
        text += "\n" + summary
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


OV = "0000-overview.md"  # nome do PRD 0000 nos testes que criam a visao geral


def overview(prefixes=("ONB",), comment=True, header_field="Escopo"):
    rows = "\n".join(f"| Ctx{p} | resp | [x](#contextos) | `{p}` | up |" for p in prefixes)
    head = "<!-- prd: overview -->\n" if comment else ""
    field = f"| **{header_field}** | tudo |\n" if header_field else ""
    return head + f"""# Visão Geral

| | |
|---|---|
{field}

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

    def test_missing_summary_section_is_hard(self):
        self.hard_for(prd(summary=""),
                      "secao obrigatoria ausente: Resumo Executivo")

    def test_executive_summary_alias_satisfies_the_section(self):
        text = prd(summary=SUMMARY.replace("## Resumo Executivo",
                                           "## Executive Summary"))
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_overview_needs_no_summary_section(self):
        self.write("0001-onb-x.md", prd(link_0000=OV))
        self.write(OV, overview())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("Resumo Executivo", out)

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


TRADEOFF = ("\n## Trade-offs Declarados\n\n"
            "- **Decisao unica.** *Custo:* retrabalho. *Razão:* prazo.\n")
METRICS = ("\n## Métricas de Sucesso\n\n"
           "- Leading: toda combinacao invalida rejeitada.\n"
           "- Guardrails: nada do que ja funciona degrada.\n")
FRAGILITY = ("\n## Ponto de Maior Fragilidade\n\n"
             "O corte de escopo cai se a corretora fechar o livro antes.\n")
REFERENCES = "\n## Referências\n\n- CVM 160, lida em 2026-01-10.\n"


class SectionContentTests(LintCase):
    def test_empty_section_is_hard(self):
        self.hard_for(prd(body_extra="\n## Não-objetivos\n\n"),
                      "secao sem conteudo: Não-objetivos")

    def test_none_line_only_section_is_hard(self):
        self.hard_for(prd(body_extra="\n## Não-objetivos\n\n- N/A\n"),
                      "secao sem conteudo: Não-objetivos")

    def test_section_with_content_is_green(self):
        self.write("0001-onb-x.md", prd(body_extra="\n## Não-objetivos\n\n- cadastro de fundo.\n"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_subsection_counts_as_content(self):
        body = "\n## Não-objetivos\n\n### Fora da v1\n\n- cadastro de fundo.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


class SectionOrderTests(LintCase):
    def test_section_out_of_order_is_hard(self):
        text = prd().replace("## Contexto e Problema",
                             METRICS.strip() + "\n\n## Contexto e Problema")
        self.hard_for(text, "'Métricas de Sucesso' aparece antes de "
                            "'Contexto e Problema'")

    def test_table_order_is_green(self):
        self.write("0001-onb-x.md",
                   prd(nfr=True, body_extra=TRADEOFF + METRICS + FRAGILITY + REFERENCES))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)

    def test_unknown_section_does_not_affect_order(self):
        self.write("0001-onb-x.md", prd(body_extra="\n## Regras Locais\n\n- uma regra.\n" + METRICS))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


def alignment(lines):
    body = "\n".join(f"linha {n} do alinhamento." for n in range(1, lines + 1))
    return f"{SUMMARY}\n## Alinhamento Estratégico\n\n{body}\n"


class SummaryLengthTests(LintCase):
    def test_summary_below_three_lines_is_warn(self):
        short = "## Resumo Executivo\n\nProblema, solução e métrica em uma linha.\n"
        self.write("0001-onb-x.md", prd(summary=short))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "secao Resumo Executivo com 1 frase(s)")

    def test_summary_above_five_lines_is_warn(self):
        long = SUMMARY + "Linha extra a.\nLinha extra b.\nLinha extra c.\n"
        self.write("0001-onb-x.md", prd(summary=long))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "secao Resumo Executivo com 6 frase(s)")

    def test_summary_between_three_and_five_lines_is_silent(self):
        self.write("0001-onb-x.md", prd())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("frase(s)", out)

    def test_alignment_below_three_lines_is_warn(self):
        self.write("0001-onb-x.md", prd(summary=alignment(2)))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "secao Alinhamento Estratégico com 2 frase(s)")

    def test_alignment_within_the_range_is_silent(self):
        self.write("0001-onb-x.md", prd(summary=alignment(5)))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("frase(s)", out)


class TradeOffTests(LintCase):
    def test_tradeoff_without_reason_is_hard(self):
        body = "\n## Trade-offs Declarados\n\n- **Decisao.** *Custo:* retrabalho.\n"
        self.hard_for(prd(body_extra=body + METRICS), "trade-off sem Razao")

    def test_tradeoff_without_cost_is_hard(self):
        body = "\n## Trade-offs Declarados\n\n- **Decisao.** *Razão:* prazo.\n"
        self.hard_for(prd(body_extra=body + METRICS), "trade-off sem Custo")

    def test_bold_and_english_markers_are_accepted(self):
        body = ("\n## Trade-offs Declarados\n\n"
                "- **Decisao A.** **Custo:** retrabalho. **Razão:** prazo.\n"
                "- **Decisao B.** *Cost:* rework. *Reason:* deadline.\n")
        self.write("0001-onb-x.md", prd(body_extra=body + METRICS))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_continuation_line_completes_the_bullet(self):
        body = ("\n## Trade-offs Declarados\n\n"
                "- **Decisao.** *Custo:* retrabalho.\n  *Razão:* prazo.\n")
        self.write("0001-onb-x.md", prd(body_extra=body + METRICS))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("trade-off com", out)

    def test_bullet_above_two_lines_is_warn(self):
        body = ("\n## Trade-offs Declarados\n\n"
                "- **Decisao.** *Custo:* retrabalho.\n  *Razão:* prazo.\n"
                "  A alternativa foi descartada.\n")
        self.write("0001-onb-x.md", prd(body_extra=body + METRICS))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "trade-off com 3 linhas")


class MetricGuardrailTests(LintCase):
    def test_metrics_without_guardrail_is_hard(self):
        body = "\n## Métricas de Sucesso\n\n- Leading: toda regra invalida rejeitada.\n"
        self.hard_for(prd(body_extra=body), "sem nenhuma linha de guardrail")

    def test_metrics_with_guardrail_is_green(self):
        self.write("0001-onb-x.md", prd(body_extra=METRICS))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


class FragilityPositionTests(LintCase):
    def test_section_after_fragility_is_hard(self):
        body = FRAGILITY + "\n## Dependências e Riscos\n\n- integracao externa.\n"
        self.hard_for(prd(body_extra=body),
                      "Ponto de Maior Fragilidade fora de posicao: "
                      "'Dependências e Riscos' vem depois")

    def test_references_after_fragility_is_green(self):
        self.write("0001-onb-x.md", prd(body_extra=FRAGILITY + REFERENCES))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


PREMISE = ("- **[PREMISSA] O lead time vem da troca manual, nao da analise; "
           "se falsa, a digitalizacao nao paga a iniciativa.** Dono: operacoes. "
           "Resolve-se medindo 20 casos antes de aprovar.\n")
PREMISE_EN = ("- **[PREMISSA] Lead time comes from the manual exchange, not from "
              "the analysis; if false, digitalization does not pay for the "
              "initiative.** Dono: operacoes. Resolve-se medindo 20 casos.\n")
QUESTION = ("- Ha regulacao setorial alem de KYC para o segmento PJ (ONB-01)? "
            "Dono: compliance. Resolve-se com parecer por escrito.\n")
QUESTIONS = "\n## Perguntas em Aberto\n\n"


class FalsePremiseTests(LintCase):
    def test_false_premise_after_another_bullet_is_hard(self):
        self.hard_for(prd(body_extra=QUESTIONS + QUESTION + PREMISE),
                      "premissa 'se falsa' fora da primeira posicao")

    def test_first_bullet_without_bold_is_hard(self):
        self.hard_for(prd(body_extra=QUESTIONS + PREMISE.replace("**", "")),
                      "premissa 'se falsa' sem negrito")

    def test_bold_first_bullet_is_green(self):
        self.write("0001-onb-x.md", prd(body_extra=QUESTIONS + PREMISE + QUESTION))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("premissa 'se falsa'", out)

    def test_section_without_false_premise_is_silent(self):
        self.write("0001-onb-x.md", prd(body_extra=QUESTIONS + QUESTION))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("premissa 'se falsa'", out)

    def test_english_if_false_without_bold_is_hard(self):
        self.hard_for(prd(body_extra=QUESTIONS + PREMISE_EN.replace("**", "")),
                      "premissa 'se falsa' sem negrito")

    def test_english_if_false_in_bold_is_green(self):
        self.write("0001-onb-x.md", prd(body_extra=QUESTIONS + PREMISE_EN))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("premissa 'se falsa'", out)


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

    def test_added_hedging_words_are_warn(self):
        body = "\nO operador poderia esperar muito pela publicacao da oferta.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "hedging lexical: 'poderia'")
        self.assert_warn(out, "hedging lexical: 'muito'")

    def test_added_english_hedging_words_are_warn(self):
        body = "\nThe operator could wait very long for the offer to be published.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "hedging lexical: 'could'")
        self.assert_warn(out, "hedging lexical: 'very'")

    def test_mechanism_in_solution_is_warn(self):
        text = prd().replace("Capability.", "Publicar no Kafka a cada mudanca.")
        self.write("0001-onb-x.md", text)
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "mecanismo nomeado em secao de problem space: 'kafka'")

    def test_identical_paragraph_in_two_prds_is_warn(self):
        long = "\nO mercado exige liquidacao em D+2 para toda oferta publica de cotas de fundo fechado.\n"
        self.write("0001-onb-x.md", prd(body_extra=long, link_0000=OV))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y",
                                        body_extra=long, link_0000=OV))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "paragrafo identico em mais de um PRD")

    def test_short_identical_lines_are_not_paragraphs(self):
        short = "\nCada requisito e uma condicao verificavel.\n"
        self.write("0001-onb-x.md", prd(body_extra=short, link_0000=OV))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y",
                                        body_extra=short, link_0000=OV))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("WARN", out)


class CrossPrdTests(LintCase):
    def test_citation_without_definition(self):
        self.hard_for(prd(body_extra="\nDepende de ONB-77.\n"),
                      "citacao de ONB-77 nao resolve para nenhuma definicao")

    def test_citation_resolves_across_prds(self):
        self.write("0001-onb-x.md", prd(body_extra="\nVer OTH-01.\n", link_0000=OV))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y", link_0000=OV))
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
        p = self.write("0001-onb-x.md", prd(body_extra="\nVer OTH-01.\n", link_0000=OV))
        self.write("0002-oth-y.md", prd(prefix="OTH", title="Feature Y", link_0000=OV))
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
        zero = "0000-platform-overview.md"
        self.write("0001-onb-x.md", prd(link_0000=zero))
        self.write("0002-oth-y.md", prd(prefix="OTH", link_0000=zero))
        self.write(zero, overview(("ONB", "OTH")))
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
        self.write("0001-onb-x.md", prd(link_0000="0000-platform-overview.md"))
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
        self.write("0001-onb-x.md",
                   prd(body_extra="\nVeja [PRD 0002](0002-oth-y.md#contexto) e [pasta](../prd).\n",
                       link_0000=OV))
        self.write("0002-oth-y.md", prd(prefix="OTH", link_0000=OV))
        self.write("0000-overview.md", overview(("ONB", "OTH")))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_link_is_relative_to_prd_folder(self):
        self.write("onb/0001-x.md", prd(body_extra="\nVeja [nota](notes.md).\n",
                                        link_0000="../0000-overview.md"))
        self.write("onb/notes.md", "# N\n")
        self.write("0000-overview.md", overview())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_root_relative_link_resolves_from_repo_root(self):
        self.write("0001-onb-x.md",
                   prd(body_extra="\nVeja [spec](/docs/prd/0002-oth-y.md) e [x](/docs/nope.md).\n",
                       link_0000=OV))
        self.write("0002-oth-y.md", prd(prefix="OTH", link_0000=OV))
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


class MoscowTests(LintCase):
    def test_fr_without_moscow_is_hard(self):
        self.hard_for(prd(body_extra="\n- **ONB-02** condicao sem prioridade.\n"),
                      "requisito ONB-02 definido sem prioridade MoSCoW")

    def test_every_priority_is_accepted(self):
        body = ("\n- **ONB-02 (Should)** a.\n- **ONB-03 (Could)** b.\n"
                "- **ONB-04 (Won't)** c.\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_nfr_without_moscow_is_green(self):
        self.write("0001-onb-x.md", prd(nfr=True))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("MoSCoW", out)


class HeaderFieldTests(LintCase):
    def test_missing_field_is_hard(self):
        self.hard_for(prd(header_field=""),
                      "header sem o campo 'Contexto Originario', 'Modulo' ou 'Area'")

    def test_english_alias_is_accepted(self):
        self.write("0001-onb-x.md", prd(header_field="Originating Context"))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_module_and_area_labels_are_accepted(self):
        for label in ("Módulo", "Module", "Área", "Area"):
            with self.subTest(label=label):
                self.write("0001-onb-x.md", prd(header_field=label))
                rc, out = self.run_lint()
                self.assert_no_hard(rc, out)

    def test_label_outside_the_closed_list_is_hard(self):
        self.hard_for(prd(header_field="Contexto"),
                      "header sem o campo 'Contexto Originario', 'Modulo' ou 'Area'")

    def test_field_without_value_is_hard(self):
        text = prd().replace("| **Contexto Originário** | CtxONB |",
                             "| **Contexto Originário** |  |")
        self.hard_for(text, "campo 'Contexto Originario' do header sem valor")

    def test_field_below_the_prefix_line_is_hard(self):
        text = prd(header_field="").replace(
            "Prefixo dos requisitos: `ONB`.",
            "Prefixo dos requisitos: `ONB`.\n\n| | |\n|---|---|\n"
            "| **Contexto Originário** | CtxONB |")
        self.hard_for(text, "header sem o campo 'Contexto Originario'")

    def test_overview_uses_escopo(self):
        self.write("0001-onb-x.md", prd(link_0000=OV))
        self.write(OV, overview(header_field=""))
        rc, out = self.run_lint()
        self.assertEqual(rc, 1, out)
        self.assert_hard(out, "header sem o campo 'Escopo'")


DEPENDENCIES = ("\n## Dependências e Riscos\n\n"
                "| Item | Tipo | Impacto |\n|---|---|---|\n"
                "| Account Activation lê a elegibilidade | Acoplamento entre contextos "
                "| ONB-01 é o contrato |\n"
                "| Compliance Review recebe o caso | Acoplamento entre contextos "
                "| a fila parte deste estado |\n")


class AffectsDependenciesTests(LintCase):
    """`; afeta <lista>` no campo do header exige linha na tabela de
    Dependencias e Riscos, uma por contexto afetado."""

    def test_affected_context_without_table_is_hard(self):
        self.hard_for(prd(header_value="CtxONB; afeta Account Activation"),
                      "contexto afetado sem linha em Dependencias e Riscos: "
                      "'Account Activation'")

    def test_affected_context_missing_from_the_table_is_hard(self):
        text = prd(header_value="CtxONB; afeta Account Activation, Billing e "
                                "Compliance Review",
                   body_extra=DEPENDENCIES)
        self.hard_for(text, "contexto afetado sem linha em Dependencias e "
                            "Riscos: 'Billing'")

    def test_every_affected_context_in_the_table_is_green(self):
        self.write("0001-onb-x.md",
                   prd(header_value="CtxONB; afeta Account Activation e Compliance Review",
                       body_extra=DEPENDENCIES))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("contexto afetado", out)

    def test_header_without_afeta_is_silent(self):
        self.write("0001-onb-x.md", prd())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("contexto afetado", out)


class OverviewReferenceTests(LintCase):
    def test_prefix_line_without_link_is_hard(self):
        self.write("0001-onb-x.md", prd())
        self.write(OV, overview())
        rc, out = self.run_lint()
        self.assertEqual(rc, 1, out)
        self.assert_hard(out, "linha de prefixo sem link para o PRD 0000")

    def test_prefix_line_with_link_is_green(self):
        self.write("0001-onb-x.md", prd(link_0000=OV))
        self.write(OV, overview())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)

    def test_link_outside_the_prefix_line_does_not_count(self):
        self.write("0001-onb-x.md", prd(body_extra=f"\nVeja [0000]({OV}).\n"))
        self.write(OV, overview())
        rc, out = self.run_lint()
        self.assertEqual(rc, 1, out)
        self.assert_hard(out, "linha de prefixo sem link para o PRD 0000")

    def test_folder_without_overview_needs_no_link(self):
        self.write("0001-onb-x.md", prd())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


CRITERIA = "\n## Critérios de Aceitação\n\n"
REGULATORY = "\n## Considerações Regulatórias\n\nCVM 160 lida em 2026-01-10.\n\n"
STATE_DIAGRAM = ("\n```mermaid\nstateDiagram-v2\n"
                 "    [*] --> Draft: criar (ONB-01)\n"
                 "    Draft --> Open: publicar\n"
                 "```\n\n"
                 "| Estado | Identificador | Significado |\n|---|---|---|\n"
                 "| Rascunho | `Draft` | minuta em elaboracao |\n")
FLOWCHART = ("\n```mermaid\nflowchart TD\n"
             '    n0["Livro fechado (ONB-01)"] --> n1{"D > B ?"}\n'
             '    n1 -- "nao" --> n2["Nao formada (ONB-01)"]\n'
             '    n1 -- "sim (ONB-01)" --> n3["Formada (ONB-01)"]\n'
             "```\n")
SEQUENCE = ("\n```mermaid\nsequenceDiagram\n"
            "    participant Operador\n"
            "    participant Offering\n"
            "    Operador->>Offering: publicar\n"
            "    Offering-->>Operador: publicada (ONB-01)\n"
            "```\n")


class ScenarioIdTests(LintCase):
    def test_scenario_without_id_is_warn(self):
        body = CRITERIA + "- **Dado** um Draft, **quando** publica, **então** Aberta.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "cenario Dado/Quando/Entao sem ID de requisito")

    def test_scenario_with_id_is_silent(self):
        body = CRITERIA + "- **Dado** um Draft, **quando** publica, **então** Aberta (ONB-01).\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("cenario Dado/Quando/Entao", out)

    def test_given_when_then_is_checked(self):
        body = ("\n## Acceptance Criteria\n\n"
                "- **Given** a draft, **when** published, **then** open.\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_warn(out, "cenario Dado/Quando/Entao sem ID de requisito")

    def test_bullet_that_is_not_a_scenario_is_ignored(self):
        body = CRITERIA + "- A primeira coluna da tabela nomeia o caso.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assertNotIn("cenario Dado/Quando/Entao", out)


class RegulatoryLineTests(LintCase):
    def test_bullet_without_arrow_and_id_is_warn(self):
        body = REGULATORY + "- Art. 73: restituicao integral abaixo do minimo.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "bullet regulatorio sem '-> ID'")

    def test_bullet_citing_id_without_arrow_is_warn(self):
        body = REGULATORY + "- Art. 73: restituicao integral abaixo do minimo. ONB-01.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_warn(out, "bullet regulatorio sem '-> ID'")

    def test_both_arrows_and_bracketed_id_are_accepted(self):
        body = (REGULATORY
                + "- Art. 73: restituicao abaixo do minimo → ONB-01.\n"
                + "- Art. 74, parágrafo único: efetivamente distribuidos -> [ONB-01].\n"
                + "- LGPD, art. 15, I: o tratamento termina -> (ONB-01).\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("bullet regulatorio", out)

    def test_bullet_not_starting_with_art_is_checked(self):
        body = REGULATORY + "- CVM 160, art. 65: a reserva e irrevogavel.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_warn(out, "bullet regulatorio sem '-> ID'")

    def test_source_line_without_bullet_is_ignored(self):
        body = REGULATORY + "- Art. 73: restituicao abaixo do minimo → ONB-01.\n"
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assertNotIn("bullet regulatorio", out)

    def test_gap_bullet_needs_no_id(self):
        body = (REGULATORY
                + "- [LACUNA] Regulacao setorial do segmento PJ nao levantada.\n"
                + "- **[LACUNA]** Norma de retencao de documento nao identificada.\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("bullet regulatorio", out)

    def test_gap_tag_in_the_middle_does_not_exempt(self):
        body = (REGULATORY
                + "- Art. 73: restituicao abaixo do minimo, ainda `[LACUNA]`.\n")
        self.write("0001-onb-x.md", prd(body_extra=body))
        rc, out = self.run_lint()
        self.assert_warn(out, "bullet regulatorio sem '-> ID'")


class DiagramLabelTests(LintCase):
    def test_state_transition_without_id_is_warn(self):
        self.write("0001-onb-x.md", prd(body_extra=STATE_DIAGRAM))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "rotulo sem ID no diagrama: 'publicar'")
        self.assertNotIn("'criar (ONB-01)'", out)

    def test_flowchart_edge_without_id_is_warn(self):
        self.write("0001-onb-x.md", prd(body_extra=FLOWCHART))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "rotulo sem ID no diagrama: 'nao'")
        self.assertNotIn("'sim (ONB-01)'", out)

    def test_sequence_message_without_id_is_warn(self):
        self.write("0001-onb-x.md", prd(body_extra=SEQUENCE))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "rotulo sem ID no diagrama: 'publicar'")
        self.assertNotIn("'publicada (ONB-01)'", out)

    def test_prd_without_diagram_is_silent(self):
        self.write("0001-onb-x.md", prd())
        rc, out = self.run_lint()
        self.assertNotIn("rotulo sem ID", out)


class IdentifierColumnTests(LintCase):
    def test_state_diagram_without_identifier_column_is_warn(self):
        block = ("\n```mermaid\nstateDiagram-v2\n"
                 "    [*] --> Draft: criar (ONB-01)\n```\n")
        self.write("0001-onb-x.md", prd(body_extra=block))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assert_warn(out, "stateDiagram-v2 sem tabela com coluna Identificador")

    def test_identifier_column_is_silent(self):
        self.write("0001-onb-x.md", prd(body_extra=STATE_DIAGRAM))
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)
        self.assertNotIn("coluna Identificador", out)

    def test_flowchart_needs_no_identifier_column(self):
        self.write("0001-onb-x.md", prd(body_extra=FLOWCHART))
        rc, out = self.run_lint()
        self.assertNotIn("coluna Identificador", out)


class SectionTableSyncTest(unittest.TestCase):
    """A tabela da secao Secoes de references/writing.md e a fonte dos nomes e
    da ordem; SECTIONS e SECTION_ORDER a espelham."""

    def table_sections(self):
        """Primeira coluna da tabela de secoes, na ordem do documento."""
        with open(WRITING_MD, encoding="utf-8") as f:
            lines = f.read().splitlines()
        start = next((i for i, l in enumerate(lines)
                      if lint_prd.norm_heading(l) == "secoes"
                      and l.startswith("## ")), None)
        self.assertIsNotNone(start, "secao '## Seções' nao encontrada em writing.md")
        rows = []
        for raw in lines[start + 1:]:
            if raw.startswith("## "):
                break
            cells = lint_prd.table_cells(raw)
            if cells and not all(lint_prd.SEPARATOR_CELL.match(c) for c in cells):
                rows.append(cells[0])
        self.assertTrue(rows, "tabela de secoes vazia em writing.md")
        self.assertEqual(lint_prd.norm_heading(rows[0]), "secao",
                         "a primeira linha da tabela deveria ser o header")
        return rows[1:]

    def test_names_match_sections(self):
        for name in self.table_sections():
            with self.subTest(section=name):
                keys = [k for k in lint_prd.SECTION_ORDER
                        if lint_prd.heading_is(k, name)]
                self.assertEqual(len(keys), 1,
                                 f"'{name}' nao casa exatamente um alias de SECTIONS")

    def test_order_matches_section_order(self):
        keys = [next(k for k in lint_prd.SECTION_ORDER if lint_prd.heading_is(k, name))
                for name in self.table_sections()]
        self.assertEqual(keys, lint_prd.SECTION_ORDER)


class ExampleRegressionTest(LintCase):
    """O PRD de references/example.md, gravado como PRD real, linta sem HARD."""

    def example(self):
        with open(EXAMPLE_MD, encoding="utf-8") as f:
            text = f.read()
        # A cerca do bloco e mais longa que as cercas de dentro dele.
        m = re.search(r"^(`{3,})markdown\s*\n(.*?)\n\1\s*$", text,
                      re.DOTALL | re.MULTILINE)
        self.assertIsNotNone(m, "bloco markdown nao encontrado em references/example.md")
        return m.group(2)

    def test_example_has_no_hard(self):
        self.write("0001-onb-document-verification.md", self.example())
        rc, out = self.run_lint()
        self.assert_no_hard(rc, out)


if __name__ == "__main__":
    unittest.main()
