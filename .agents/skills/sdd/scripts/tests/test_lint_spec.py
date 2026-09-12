"""Testes de lint_spec.py: comentario de maquina, linha de prefixo, secoes
obrigatorias (igualdade, duplicata, fence) e sua sincronia com
references/specify.md, requisitos e IDs (SHALL, prefixo, duplicata,
aposentados, citacao orfa, subtitulos por tema), PRD (prd, prd-rev, prefixos,
citacoes), Rastreabilidade, tags, links locais e erros de uso.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_spec.py"
"""

import contextlib
import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import _common  # noqa: E402
import lint_spec  # noqa: E402

SPECIFY_MD = os.path.join(os.path.dirname(SCRIPTS), "references", "specify.md")

PRD = """# PRD do Livro

Prefixo dos requisitos: `BOOK`.

## Functional Requirements

- **BOOK-01 (Must)** — Registrar reserva.
- **BOOK-02 (Should)** — Alterar reserva.
- **BOOK-NFR-01** — Prazo.
"""

CONTEXT = """\
Origem no PRD 0002.
Fronteira: o livro registra reservas; a alocacao e do Allocation.
Base lida: `src/ReservationBook` tem so a composicao do servico."""

SPEC = """<!-- sdd: spec | capability: reservation-book/reservation-lifecycle{prd} -->
# Livro

{prefix_line}
## Contexto (Context)

""" + CONTEXT + """

## Requisitos (Requirements)

{reqs}
{extra}"""

REQS = """- **RSV-01** — WHEN o operador registra THEN the system SHALL aceitar [BOOK-01]
- **RSV-02** — WHEN o operador altera THEN the system SHALL aceitar [BOOK-02]
"""

PRD_FIELD = " | prd: /docs/prd/0002-reservation-book.md"

REQ_WITH_CITATION = re.compile(r"^\s*[-*]\s+\*\*([A-Z][A-Z0-9]{1,9}-\d{2,})\*\*.*\[([^\[\]]+)\]\s*$")
ANY_ID = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-(?:NFR-)?\d{2,}\b")


def trace_section(reqs):
    """Secao Rastreabilidade derivada das citacoes ao fim dos requisitos: com
    `prd:` no comentario de maquina o linter exige que todo FR em escopo
    apareca na primeira coluna."""
    rows = {}
    for l in reqs.splitlines():
        m = REQ_WITH_CITATION.match(l)
        if not m:
            continue
        for prd_id in ANY_ID.findall(m.group(2)):
            rows.setdefault(prd_id, []).append(m.group(1))
    body = "".join(f"| {k} | {', '.join(v)} |\n" for k, v in rows.items())
    return "\n## Rastreabilidade\n\n| ID do PRD | IDs EARS |\n|---|---|\n" + body


def run(path, *extra):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = lint_spec.main(["lint_spec.py", path, *extra])
    return code, buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.prd_dir = os.path.join(self.root, "docs", "prd")
        os.makedirs(self.prd_dir)
        self.prd = os.path.join(self.prd_dir, "0002-reservation-book.md")
        self.write(self.prd, PRD)
        self.cap = os.path.join(self.root, "docs", "specs", "reservation-book", "reservation-lifecycle")
        os.makedirs(self.cap)
        self.spec = os.path.join(self.cap, "spec.md")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def write(path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def lint(self, reqs=REQS, extra="", prd=PRD_FIELD, prefix_line="Prefixo dos requisitos: `RSV`.\n",
             trace=None):
        if trace is None:
            trace = trace_section(reqs) if prd else ""
        self.write(self.spec, SPEC.format(prd=prd, prefix_line=prefix_line, reqs=reqs, extra=extra) + trace)
        return run(self.spec)

    def assertHard(self, out, fragment):
        self.assertTrue(any(l.startswith("HARD") and fragment in l for l in out.splitlines()),
                        f"'{fragment}' nao e HARD em:\n{out}")

    def assertNoHard(self, out, fragment=None):
        hards = [l for l in out.splitlines() if l.startswith("HARD")]
        if fragment is None:
            self.assertEqual(hards, [], out)
        else:
            self.assertFalse(any(fragment in l for l in hards), out)

    def assertWarn(self, out, fragment):
        self.assertTrue(any(l.startswith("WARN") and fragment in l for l in out.splitlines()),
                        f"'{fragment}' nao e WARN em:\n{out}")


class ValidSpec(Base):
    def test_minimal_spec_passes(self):
        code, out = self.lint(prd="")
        self.assertEqual(code, 0, out)
        self.assertIn("0 HARD, 0 WARN", out)

    def test_spec_with_prd_passes_with_only_prd_rev_warn(self):
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertIn("0 HARD, 1 WARN", out)
        self.assertWarn(out, "prd-rev ausente")

    def test_optional_sections_are_not_required(self):
        code, out = self.lint(prd="")
        for name in ("Escopo", "Premissas", "Perguntas em Aberto", "Rastreabilidade", "Historias",
                     "Dimensoes", "Criterios de Sucesso", "Ponto de Maior Fragilidade", "Status"):
            self.assertNotIn(name, out)


class MachineComment(Base):
    def test_missing_comment_is_hard(self):
        self.write(self.spec, "# Livro\n\nPrefixo dos requisitos: `RSV`.\n\n## Contexto\n\nx\n\n## Requisitos\n\n" + REQS)
        code, out = run(self.spec)
        self.assertEqual(code, 1)
        self.assertHard(out, "primeira linha deve ser <!-- sdd: spec")

    def test_other_kind_is_hard(self):
        self.write(self.spec, SPEC.format(prd="", prefix_line="Prefixo dos requisitos: `RSV`.\n", reqs=REQS, extra="")
                   .replace("<!-- sdd: spec |", "<!-- sdd: spec-delta | tier: large |"))
        code, out = run(self.spec)
        self.assertHard(out, "sdd: 'spec-delta'")

    def test_missing_capability_is_hard(self):
        self.write(self.spec, SPEC.format(prd="", prefix_line="Prefixo dos requisitos: `RSV`.\n", reqs=REQS, extra="")
                   .replace(" | capability: reservation-book/reservation-lifecycle", ""))
        code, out = run(self.spec)
        self.assertHard(out, "sem 'capability:'")

    def test_no_tier_status_author_or_date_required(self):
        code, out = self.lint(prd="")
        self.assertEqual(code, 0, out)
        findings = [l for l in out.splitlines() if l.startswith(("HARD", "WARN"))]
        self.assertEqual(findings, [])


class PrefixLine(Base):
    def test_missing_prefix_line_is_hard(self):
        code, out = self.lint(prd="", prefix_line="")
        self.assertEqual(code, 1)
        self.assertHard(out, "linha logo abaixo do titulo deve ser")

    def test_english_prefix_line_accepted(self):
        code, out = self.lint(prd="", prefix_line="Requirement prefix: `RSV`.\n")
        self.assertEqual(code, 0, out)

    def test_id_with_other_prefix_is_hard(self):
        code, out = self.lint(prd="", prefix_line="Prefixo dos requisitos: `RES`.\n")
        self.assertHard(out, "RSV-01: prefixo difere do declarado ('RES')")

    def test_header_table_is_rejected(self):
        table = "| | |\n|---|---|\n| **Status** | Rascunho |\n| **Prefixo** | RSV |\n"
        code, out = self.lint(prd="", prefix_line=table)
        self.assertEqual(code, 1)
        self.assertHard(out, "linha logo abaixo do titulo deve ser")


class SectionGrammar(Base):
    def test_missing_contexto_is_hard(self):
        self.write(self.spec, "<!-- sdd: spec | capability: x/y -->\n# L\n\nPrefixo dos requisitos: `RSV`.\n\n## Requisitos\n\n" + REQS)
        code, out = run(self.spec)
        self.assertHard(out, "secao obrigatoria ausente: ## Contexto")

    def test_non_functional_requirements_does_not_satisfy_requirements(self):
        self.write(self.spec, "<!-- sdd: spec | capability: x/y -->\n# L\n\nPrefixo dos requisitos: `RSV`.\n\n## Contexto\n\nc\n\n## Non-functional Requirements\n\n" + REQS)
        code, out = run(self.spec)
        self.assertHard(out, "secao obrigatoria ausente: ## Requisitos")

    def test_non_requirements_is_not_requirements(self):
        self.assertIsNone(_common.find_section_exact(
            ["## Non-Requirements", "x"], ("Requisitos", "Requirements")))
        self.assertEqual(_common.find_section_exact(
            ["## Requisitos (Requirements)", "x"], ("Requisitos", "Requirements")), (1, 2))

    def test_duplicate_heading_is_hard(self):
        code, out = self.lint(prd="", extra="## Contexto (Context)\n\ndup\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "secao duplicada ## Contexto")

    def test_requirement_inside_fence_is_ignored(self):
        fenced = "````md\n## Requisitos\n- **RSV-01** — The system SHALL x [ZZZ-01]\n```\nainda dentro\n````\n"
        code, out = self.lint(prd="", extra=fenced)
        self.assertEqual(code, 0, out)
        self.assertNotIn("ID duplicado", out)
        self.assertNotIn("ZZZ", out)

    def test_fenced_line_mask_matches_closing_length(self):
        mask = _common.fenced_line_mask(["a", "~~~~", "x", "~~~", "y", "~~~~", "z"])
        self.assertEqual(mask, [False, True, True, True, True, True, False])

    def test_subheadings_inside_requisitos_are_allowed(self):
        reqs = "### Registro\n\n" + REQS + "\n### Consulta\n\n- **RSV-03** — WHEN x THEN the system SHALL y\n"
        code, out = self.lint(prd="", reqs=reqs)
        self.assertEqual(code, 0, out)


class ContextSize(Base):
    def lint_context(self, body):
        self.write(self.spec, SPEC.format(prd="", prefix_line="Prefixo dos requisitos: `RSV`.\n",
                                          reqs=REQS, extra="").replace(CONTEXT, body))
        return run(self.spec)

    def test_three_to_five_lines_are_silent(self):
        code, out = self.lint_context(CONTEXT)
        self.assertEqual(code, 0, out)
        self.assertNotIn("secao Contexto com", out)
        code, out = self.lint_context(CONTEXT + "\nBase ignorada: `src/ReservationBook/Reports`.\n\nADR 0001 restringe a publicacao.")
        self.assertNotIn("secao Contexto com", out)

    def test_fewer_than_three_lines_is_warn(self):
        code, out = self.lint_context("Origem no PRD 0002.")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "secao Contexto com 1 linha(s) nao vazia(s)")

    def test_more_than_five_lines_is_warn(self):
        code, out = self.lint_context("\n".join(f"Linha {n} do contexto." for n in range(1, 7)))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "secao Contexto com 6 linha(s) nao vazia(s)")


class RequirementThemes(Base):
    """Subtitulos `###` por tema em Requisitos: a partir de 8 requisitos a
    lista precisa deles, abaixo disso sao cerimonia."""

    @staticmethod
    def reqs(lo, hi):
        return "".join(f"- **RSV-{n:02d}** — WHEN x{n} THEN the system SHALL y\n"
                       for n in range(lo, hi + 1))

    def test_eight_requirements_without_subheading_is_warn(self):
        code, out = self.lint(prd="", reqs=self.reqs(1, 8))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "secao Requisitos com 8 requisitos sem subtitulo ### por tema")

    def test_eight_requirements_with_subheadings_are_silent(self):
        reqs = "### Registro\n\n" + self.reqs(1, 4) + "\n### Consulta\n\n" + self.reqs(5, 8)
        code, out = self.lint(prd="", reqs=reqs)
        self.assertEqual(code, 0, out)
        self.assertNotIn("subtitulo ###", out)

    def test_fewer_than_eight_with_subheading_is_warn(self):
        code, out = self.lint(prd="", reqs="### Registro\n\n" + self.reqs(1, 2))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "secao Requisitos com 2 requisito(s) e subtitulo ### por tema")

    def test_fewer_than_eight_without_subheading_is_silent(self):
        code, out = self.lint(prd="")
        self.assertEqual(code, 0, out)
        self.assertNotIn("subtitulo ###", out)


class RequirementLines(Base):
    def test_requirement_without_shall_is_hard(self):
        code, out = self.lint(prd="", reqs=REQS + "- **RSV-03** — o sistema aceita\n")
        self.assertHard(out, "RSV-03: requisito sem SHALL")

    def test_unrecognized_ears_pattern_is_warn(self):
        code, out = self.lint(prd="", reqs=REQS + "- **RSV-03** — Sempre que possivel the system SHALL y\n")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "RSV-03: SHALL presente mas sem padrao EARS")

    def test_malformed_requirement_line_is_hard(self):
        code, out = self.lint(prd="", reqs=REQS + "- **RSV-3** — The system SHALL c\n")
        self.assertHard(out, "linha com aparencia de requisito nao reconhecida")

    def test_duplicate_id_is_hard(self):
        code, out = self.lint(prd="", reqs=REQS + "- **RSV-02** — The system SHALL c\n")
        self.assertHard(out, "ID duplicado RSV-02")

    def test_empty_requisitos_is_hard(self):
        code, out = self.lint(prd="", reqs="")
        self.assertHard(out, "secao Requisitos sem requisito com ID")


class RetiredIds(Base):
    def test_reused_retired_id_is_hard(self):
        code, out = self.lint(prd="", extra="\nAposentados: RSV-02\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "RSV-02: ID reutilizado")

    def test_gap_without_retirement_is_warn_and_with_retirement_is_silent(self):
        reqs = REQS + "- **RSV-04** — The system SHALL d\n"
        code, out = self.lint(prd="", reqs=reqs)
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "numero(s) pulado(s)")
        self.assertIn("RSV-03", out)
        code, out = self.lint(prd="", reqs=reqs, extra="\nAposentados: RSV-03\n")
        self.assertEqual(code, 0, out)
        self.assertNotIn("pulado", out)

    def test_citation_of_retired_id_in_prose_is_allowed(self):
        reqs = REQS + "- **RSV-04** — The system SHALL d\n"
        code, out = self.lint(prd="", reqs=reqs, extra="\nRSV-03 saiu com a mudanca 0002.\n\nAposentados: RSV-03\n")
        self.assertNoHard(out)

    def test_citation_of_unknown_own_id_is_hard(self):
        code, out = self.lint(prd="", extra="\n## Rastreabilidade\n\n| ID do PRD | IDs EARS |\n|---|---|\n| BOOK-01 | RSV-01, RSV-77 |\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "citacao de RSV-77, que nao e requisito desta spec nem esta aposentado")


class PrdProvenance(Base):
    def test_missing_prd_is_hard(self):
        os.remove(self.prd)
        code, out = self.lint()
        self.assertEqual(code, 1)
        self.assertHard(out, "PRD nao encontrado")

    def test_unknown_prefix_citation_is_hard_in_requirement_and_warn_in_prose(self):
        code, out = self.lint(reqs=REQS + "- **RSV-03** — The system SHALL c [ZZZ-01]\n",
                              extra="Em prosa ZZZ-02 aparece.\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "citacao de ZZZ-01: prefixo 'ZZZ' nao e declarado")
        self.assertWarn(out, "citacao de ZZZ-02: prefixo 'ZZZ' nao e declarado")

    def test_unresolved_known_prefix_citation_is_hard(self):
        code, out = self.lint(reqs=REQS + "- **RSV-03** — The system SHALL c [BOOK-99]\n")
        self.assertHard(out, "citacao de BOOK-99 nao resolve")

    def test_nfr_citation_resolves(self):
        code, out = self.lint(reqs=REQS + "- **RSV-03** — The system SHALL c [BOOK-NFR-01]\n")
        self.assertNoHard(out)

    def test_prefix_colliding_with_prd_is_hard(self):
        code, out = self.lint(reqs=REQS.replace("RSV-", "BOOK-"), prefix_line="Prefixo dos requisitos: `BOOK`.\n")
        self.assertHard(out, "prefixo da spec 'BOOK' coincide com prefixo de PRD")

    def test_prefix_colliding_with_prd_is_hard_without_prd_field(self):
        """Sem `prd:` a colisao e conferida em `docs/prd` da raiz do
        repositorio; sem essa pasta nada e conferido."""
        reqs = REQS.replace("RSV-", "BOOK-")
        code, out = self.lint(prd="", reqs=reqs, prefix_line="Prefixo dos requisitos: `BOOK`.\n")
        self.assertEqual(code, 1, out)
        self.assertHard(out, "prefixo da spec 'BOOK' coincide com prefixo de PRD")
        shutil.rmtree(self.prd_dir)
        code, out = self.lint(prd="", reqs=reqs, prefix_line="Prefixo dos requisitos: `BOOK`.\n")
        self.assertEqual(code, 0, out)
        self.assertNoHard(out)

    def test_prefix_sharing_two_first_letters_with_prd_is_hard(self):
        code, out = self.lint(reqs=REQS.replace("RSV-", "BOO-"),
                              prefix_line="Prefixo dos requisitos: `BOO`.\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "prefixo da spec 'BOO' comeca com as mesmas duas letras do prefixo 'BOOK'")
        self.assertHard(out, "0002-reservation-book.md")

    def test_prefix_differing_in_the_first_two_letters_passes(self):
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertNotIn("duas primeiras letras", out)

    def test_prd_rev_git_matches_when_git_available(self):
        rev = _common.git_blob_rev(self.prd)
        if rev is None:
            self.skipTest("git indisponivel")
        self.assertRegex(rev, r"^git:[0-9a-f]{40,64}$")
        code, out = self.lint(prd=PRD_FIELD + f" | prd-rev: {rev}")
        self.assertEqual(code, 0, out)
        self.assertIn("0 HARD, 0 WARN", out)

    def test_prd_rev_divergent_is_warn_not_hard(self):
        with mock.patch.object(lint_spec, "git_blob_rev", return_value="git:" + "b" * 40):
            code, out = self.lint(prd=PRD_FIELD + " | prd-rev: git:" + "a" * 40)
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "PRD mudou desde a spec")

    def test_prd_rev_without_git_is_warn(self):
        with mock.patch.object(lint_spec, "git_blob_rev", return_value=None):
            code, out = self.lint(prd=PRD_FIELD + " | prd-rev: git:" + "a" * 40)
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "git indisponivel")

    def test_prd_rev_sha256_form_is_hard(self):
        code, out = self.lint(prd=PRD_FIELD + " | prd-rev: sha256:000000000000")
        self.assertHard(out, "prd-rev 'sha256:000000000000' invalido")

    def test_prd_without_any_citation_is_warn(self):
        code, out = self.lint(reqs="- **RSV-01** — WHEN x THEN the system SHALL y\n")
        self.assertWarn(out, "sem nenhuma citacao de ID do PRD")

    def test_prd_prefix_line_with_trailing_text_is_indexed(self):
        self.write(self.prd, PRD.replace("Prefixo dos requisitos: `BOOK`.\n",
                                         "Prefixo dos requisitos: `BOOK`. Mapa de contextos: [PRD 0000](0000-overview.md).\n"))
        defs, prefixes = lint_spec.prd_index(self.prd_dir)
        self.assertIn("BOOK", prefixes)
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertNotIn("nao e declarado", out)

    def test_prefix_declared_in_prd_header_table_is_indexed(self):
        self.write(self.prd, PRD.replace("Prefixo dos requisitos: `BOOK`.\n", "| | |\n|---|---|\n| **Prefixo** | `BOOK` |\n"))
        defs, prefixes = lint_spec.prd_index(self.prd_dir)
        self.assertIn("BOOK", prefixes)
        code, out = self.lint()
        self.assertEqual(code, 0, out)

    def test_decisions_md_inside_folder_prd_is_not_indexed(self):
        folder = os.path.join(self.prd_dir, "0003-onboarding")
        os.makedirs(folder)
        self.write(os.path.join(folder, "prd.md"), PRD.replace("`BOOK`", "`ONB`").replace("BOOK-", "ONB-"))
        self.write(os.path.join(folder, "decisions.md"), "# Decisoes\n\nPrefixo dos requisitos: `RSV`.\n\n- **RSV-01 (Must)** — nao e PRD.\n")
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        defs, prefixes = lint_spec.prd_index(self.prd_dir)
        self.assertNotIn("RSV", prefixes)
        self.assertIn("ONB-01", defs)


class Traceability(Base):
    HEAD = "\n## Rastreabilidade\n\n| ID do PRD | IDs EARS |\n|---|---|\n"

    def test_missing_section_with_prd_is_hard(self):
        code, out = self.lint(trace="")
        self.assertEqual(code, 1)
        self.assertHard(out, "sem secao ## Rastreabilidade")

    def test_missing_section_without_prd_is_silent(self):
        code, out = self.lint(prd="", trace="")
        self.assertEqual(code, 0, out)
        self.assertNotIn("Rastreabilidade", out)

    def test_cited_prd_id_outside_first_column_is_hard(self):
        code, out = self.lint(trace=self.HEAD + "| BOOK-01 | RSV-01, RSV-02 |\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "BOOK-02 e citado por requisito mas nao aparece na primeira coluna")

    def test_first_column_of_any_table_of_the_section_counts(self):
        trace = (self.HEAD + "| BOOK-01 | RSV-01 |\n"
                 + "\n| Cenario do PRD | IDs EARS |\n|---|---|\n| Alteracao aceita (BOOK-02) | RSV-02 |\n")
        code, out = self.lint(trace=trace)
        self.assertEqual(code, 0, out)

    def test_unknown_ears_id_in_table_is_reported_once(self):
        code, out = self.lint(trace=self.HEAD + "| BOOK-01 | RSV-01 |\n| BOOK-02 | RSV-02, RSV-77 |\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "citacao de RSV-77, que nao e requisito desta spec")
        self.assertEqual(len([l for l in out.splitlines() if "RSV-77" in l]), 1, out)

    def test_retired_ears_id_in_table_is_hard(self):
        code, out = self.lint(extra="\nAposentados: RSV-09\n",
                              trace=self.HEAD + "| BOOK-01 | RSV-01, RSV-09 |\n| BOOK-02 | RSV-02 |\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "Rastreabilidade: RSV-09 nao e requisito definido nesta spec "
                             "(consta da lista de aposentados)")

    def test_row_without_requirement_that_cites_it_is_warn(self):
        code, out = self.lint(trace=self.HEAD + "| BOOK-01 | RSV-01 |\n| BOOK-02 | RSV-02 |\n"
                                              + "| BOOK-NFR-01 | RSV-02 |\n")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "Rastreabilidade: BOOK-NFR-01 mapeado sem requisito que o cite")

    def test_design_criterion_row_is_exempt_from_the_warn(self):
        """NFR sem teste direto vira criterio de design: a linha existe sem
        requisito que a cite, e a segunda coluna diz isso."""
        for second in ("Critério de design: ADR de transporte (PRD 0000)",
                       "Design criterion: transport ADR"):
            code, out = self.lint(trace=self.HEAD + "| BOOK-01 | RSV-01 |\n| BOOK-02 | RSV-02 |\n"
                                                  + f"| BOOK-NFR-01 | {second} |\n")
            self.assertEqual(code, 0, out)
            self.assertNoHard(out)
            self.assertNotIn("BOOK-NFR-01 mapeado sem requisito", out)

    def test_other_prose_in_the_second_column_is_not_exempt(self):
        code, out = self.lint(trace=self.HEAD + "| BOOK-01 | RSV-01 |\n| BOOK-02 | RSV-02 |\n"
                                              + "| BOOK-NFR-01 | Coberto pelo design |\n")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "Rastreabilidade: BOOK-NFR-01 mapeado sem requisito que o cite")


class InheritedScenarios(Base):
    """Cenario da tabela de Criterios de Aceitacao do PRD aparece na primeira
    coluna de alguma tabela da Rastreabilidade."""

    HEAD = Traceability.HEAD
    CASES = ("\n## Critérios de Aceitação\n\n| Caso | Livro | Resultado |\n|---|---|---|\n"
             "| Reserva aceita | A 50 | posicao 50 (BOOK-01) |\n"
             "| Alteração de vínculo | A 50, A 400 | as duas vinculadas (BOOK-02) |\n"
             "| Rateio calculado | A 50 | rateio 10 (ALLOC-03) |\n"
             "| Caso sem requisito | A 50 | aceita |\n")

    def setUp(self):
        super().setUp()
        self.write(self.prd, PRD + self.CASES)

    def mapped(self, *names):
        rows = "".join(f"| {n} | RSV-01 |\n" for n in names)
        return (self.HEAD + "| BOOK-01 | RSV-01 |\n| BOOK-02 | RSV-02 |\n"
                + "\n| Cenário do PRD | IDs EARS |\n|---|---|\n" + rows)

    def test_every_scenario_mapped_passes(self):
        code, out = self.lint(trace=self.mapped("Reserva aceita", "Alteração de vínculo"))
        self.assertEqual(code, 0, out)

    def test_scenario_without_row_is_hard(self):
        code, out = self.lint(trace=self.mapped("Reserva aceita"))
        self.assertEqual(code, 1)
        self.assertHard(out, "cenario 'Alteração de vínculo' dos Criterios de Aceitacao do PRD "
                             "sem linha na Rastreabilidade")

    def test_header_row_of_the_prd_table_is_not_a_scenario(self):
        code, out = self.lint(trace=self.mapped("Reserva aceita", "Alteração de vínculo"))
        self.assertNotIn("'Caso'", out)

    def test_prd_without_acceptance_table_is_silent(self):
        self.write(self.prd, PRD + "\n## Critérios de Aceitação\n\n- **Dado** uma reserva, **então** aceita.\n")
        code, out = self.lint()
        self.assertEqual(code, 0, out)
        self.assertNotIn("Criterios de Aceitacao", out)

    def test_spec_without_prd_field_is_silent(self):
        code, out = self.lint(prd="", trace="")
        self.assertEqual(code, 0, out)
        self.assertNotIn("Criterios de Aceitacao", out)

    def test_scenario_of_another_capability_is_silent(self):
        code, out = self.lint(trace=self.mapped("Reserva aceita", "Alteração de vínculo"))
        self.assertNotIn("'Rateio calculado'", out)

    def test_scenario_without_requirement_id_is_warn(self):
        code, out = self.lint(trace=self.mapped("Reserva aceita", "Alteração de vínculo"))
        self.assertEqual(code, 0, out)
        self.assertIn("cenario 'Caso sem requisito' do PRD nao cita requisito", out)

    def test_out_of_capability_row_is_mapped_and_exempt(self):
        rows = self.mapped("Reserva aceita", "Alteração de vínculo")
        rows += "| Caso sem requisito | Fora desta capability: `allocation/book-processing` |\n"
        code, out = self.lint(trace=rows)
        self.assertEqual(code, 0, out)
        self.assertNotIn("Caso sem requisito", out)


class Tags(Base):
    def test_premissa_and_lacuna_are_accepted(self):
        code, out = self.lint(prd="", extra="\n## Premissas\n\n| Premissa | Default | Racional |\n|---|---|---|\n| [PREMISSA] formato | JSON | padrao |\n\n[LACUNA] limite de reservas por investidor.\n")
        self.assertEqual(code, 0, out)

    def test_fato_and_premissa_critica_are_hard(self):
        code, out = self.lint(prd="", extra="\n[FATO] x.\n\n[PREMISSA-CRÍTICA] y. Se falsa, z.\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "tag fora da convencao: [FATO]")
        self.assertHard(out, "tag fora da convencao: [PREMISSA-CRÍTICA]")


class LocalLinks(Base):
    def test_relative_link_with_wrong_depth_is_hard(self):
        code, out = self.lint(extra="\nOrigem: [PRD 0002](../../prd/0002-reservation-book.md).\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "link '../../prd/0002-reservation-book.md' nao resolve")

    def test_relative_link_with_right_depth_passes(self):
        code, out = self.lint(extra="\nOrigem: [PRD 0002](../../../prd/0002-reservation-book.md#contexto).\n")
        self.assertEqual(code, 0, out)

    def test_root_relative_link_resolves_from_repo_root(self):
        code, out = self.lint(extra="\nOrigem: [PRD 0002](/docs/prd/0002-reservation-book.md).\n")
        self.assertEqual(code, 0, out)
        code, out = self.lint(extra="\nOrigem: [PRD](/docs/prd/0009-missing.md).\n")
        self.assertHard(out, "link '/docs/prd/0009-missing.md' nao resolve")

    def test_absolute_filesystem_path_is_not_a_valid_link(self):
        code, out = self.lint(extra="\nVeja [host](/etc/hostname).\n")
        self.assertHard(out, "link '/etc/hostname' nao resolve")

    def test_url_anchor_code_span_and_fence_are_ignored(self):
        extra = ("\nFontes: [CVM 160](https://example.org/x.pdf), [seção](#contexto), "
                 "`[literal](nao/existe.md)`, <mailto:x@y.z>.\n\n"
                 "```markdown\n[exemplo](nao/existe/tambem.md)\n```\n")
        code, out = self.lint(extra=extra)
        self.assertEqual(code, 0, out)


class Placeholders(Base):
    def test_placeholder_is_warn_not_hard(self):
        code, out = self.lint(prd="", extra="\nTBD: limite.\n")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "placeholder")

    def test_bracket_starting_with_uppercase_is_warn(self):
        """Placeholder de template comeca por maiuscula tanto quanto por
        minuscula: `[Uma frase: o que faremos.]` e o texto que ficou por
        escrever."""
        for text in ("[Uma frase: o que faremos.]",
                     "[Situação e restrições que forçaram a decisão; o que estava em jogo.]",
                     "Participantes: [quem decidiu]; [quem foi consultado]."):
            code, out = self.lint(prd="", extra=f"\n{text}\n")
            self.assertEqual(code, 0, out)
            self.assertWarn(out, "possivel placeholder de template")

    def test_tag_id_and_markdown_link_are_not_placeholders(self):
        extra = ("\n[PREMISSA] Forma da rejeicao.\n\n[LACUNA] limite por investidor.\n"
                 "\nOrigem: [PRD 0002](../../../prd/0002-reservation-book.md).\n"
                 "\n- [ ] Item de checklist com texto suficiente.\n")
        code, out = self.lint(prd="", extra=extra)
        self.assertEqual(code, 0, out)
        self.assertNotIn("possivel placeholder", out)

    def test_two_hundred_characters_is_the_ceiling(self):
        """O teto de 200 caracteres separa o texto por escrever - inclusive o
        placeholder longo de uma secao inteira - da prosa que so por acaso esta
        entre colchetes."""
        code, out = self.lint(prd="", extra="\n[P" + "a" * 199 + "]\n")
        self.assertWarn(out, "possivel placeholder de template")
        code, out = self.lint(prd="", extra="\n[P" + "a" * 200 + "]\n")
        self.assertEqual(code, 0, out)
        self.assertNotIn("possivel placeholder", out)

    def test_value_reduced_to_an_ellipsis_is_warn(self):
        """Rotulo escrito e valor por escrever ('- Positivas: …') passava sem
        sinal: o placeholder nao precisa de colchete."""
        for text in ("- Positivas: …", "- Positivas: ...", "| Racional | ... |"):
            code, out = self.lint(prd="", extra=f"\n{text}\n")
            self.assertEqual(code, 0, out)
            self.assertWarn(out, "valor reduzido a reticencias")

    def test_ellipsis_inside_a_sentence_is_not_a_placeholder(self):
        code, out = self.lint(prd="", extra="\nA fila aceita: pedido, retry e descarte.\n")
        self.assertEqual(code, 0, out)
        self.assertNotIn("reticencias", out)


class TemplateRegressionTest(Base):
    """O template de references/specify.md, gravado como spec viva da
    capability que declara, linta sem HARD contra um PRD com os IDs que ele
    cita."""

    def template(self):
        with open(SPECIFY_MD, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"## Template\b[^\n]*\n+`{3,4}markdown\n(.*?)\n`{3,4}\n", text, re.DOTALL)
        self.assertIsNotNone(m, "bloco de template nao encontrado em references/specify.md")
        return m.group(1)

    def test_template_is_clean(self):
        tpl = self.template()
        lines = tpl.splitlines()
        fields, _ = _common.parse_machine_comment(lines)
        self.assertIn("prd", fields, "template sem prd: no comentario de maquina")
        spec_prefix = next(m.group(1) for m in map(lint_spec.PREFIX_LINE.match, lines) if m)
        cited = {(p, nfr, n) for p, nfr, n in lint_spec.PRD_ID.findall(tpl) if p != spec_prefix}
        prd_prefixes = {p for p, _, _ in cited}
        self.assertEqual(len(prd_prefixes), 1, f"template cita mais de um prefixo de PRD: {prd_prefixes}")
        prd_prefix = prd_prefixes.pop()
        prd_path = os.path.join(self.root, *fields["prd"].strip("/").split("/"))
        defs = "".join(f"- **{p}-{nfr}{n}{'' if nfr else ' (Must)'}** — x.\n" for p, nfr, n in sorted(cited))
        self.write(prd_path, f"# PRD\n\nPrefixo dos requisitos: `{prd_prefix}`.\n\n## Requisitos Funcionais\n\n{defs}")
        self.write(self.spec, tpl + "\n")
        code, out = run(self.spec)
        self.assertNoHard(out)
        self.assertEqual(code, 0, out)


class UnknownSectionTest(Base):
    """Secao `##` fora da tabela de references/specify.md, Secoes, e WARN - e
    nao HARD, porque spec real carrega secao herdada do PRD."""

    def test_section_outside_the_table_is_warn(self):
        code, out = self.lint(prd="", extra="\n## Notas adicionais\n\nx\n")
        self.assertEqual(code, 0)
        self.assertWarn(out, "secao desconhecida: ## Notas adicionais; a lista de secoes "
                             "e a de references/specify.md, Secoes")

    def test_section_in_the_table_is_silent(self):
        code, out = self.lint(prd="", extra="\n## Premissas\n\n[PREMISSA] x\n")
        self.assertEqual(code, 0)
        self.assertNotIn("secao desconhecida", out)

    def test_english_alias_is_silent(self):
        code, out = self.lint(prd="", extra="\n## Assumptions\n\n[PREMISSA] x\n")
        self.assertNotIn("secao desconhecida", out)


class SectionsInSyncWithReferenceTest(unittest.TestCase):
    """A lista de secoes do script e a tabela de references/specify.md, secao
    Secoes: os mesmos nomes, PT na primeira coluna e EN na segunda, virgula
    separando formas alternativas. Doc e script divergentes deixam sem fonte
    escrita o nome que o linter aceita."""

    @staticmethod
    def documented():
        with open(SPECIFY_MD, encoding="utf-8") as f:
            lines = f.read().splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "## Seções")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
        out = []
        for l in lines[start:end]:
            if not l.strip().startswith("|"):
                continue
            cells = [c.strip().strip("*").strip() for c in l.strip().strip("|").split("|")]
            if len(cells) < 2 or not cells[0] or cells[0] == "Seção":
                continue
            if re.fullmatch(r":?-{2,}:?", cells[0]):
                continue
            names = [n.strip() for n in (cells[0] + "," + cells[1]).split(",") if n.strip()]
            out.append(tuple(dict.fromkeys(names)))
        return out

    def test_names_match(self):
        rows = self.documented()
        self.assertTrue(rows, "tabela de secoes nao encontrada em references/specify.md")
        self.assertEqual(sorted(rows),
                         sorted(tuple(aliases) for aliases in lint_spec.SECTIONS_KNOWN))


class Usage(Base):
    def exit_code(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_spec.main(["lint_spec.py", *argv])
            except SystemExit as e:
                code = e.code
        return code, err.getvalue()

    def test_unknown_option_is_usage(self):
        self.lint(prd="")
        for opt in ("--living", "--print-prd-rev", "--bogus"):
            code, err = self.exit_code(self.spec, opt)
            self.assertEqual(code, 2, opt)
            self.assertIn("opcao desconhecida", err)

    def test_missing_file_is_usage_not_traceback(self):
        code, err = self.exit_code(os.path.join(self.root, "nope.md"))
        self.assertEqual(code, 2)
        self.assertIn("arquivo ilegivel", err)
        self.assertNotIn("Traceback", err)

    def test_non_utf8_file_is_usage(self):
        with open(self.spec, "wb") as f:
            f.write(b"<!-- sdd: spec | capability: x/y -->\n# T\x97\n")
        code, err = self.exit_code(self.spec)
        self.assertEqual(code, 2)
        self.assertIn("UTF-8", err)

    def test_bom_is_accepted(self):
        self.lint(prd="")
        with open(self.spec, "rb") as f:
            raw = f.read()
        with open(self.spec, "wb") as f:
            f.write(b"\xef\xbb\xbf" + raw)
        code, out = run(self.spec)
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
