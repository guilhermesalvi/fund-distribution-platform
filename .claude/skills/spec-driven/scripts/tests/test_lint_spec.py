"""Testes de lint_spec.py: gramatica de secoes (igualdade, duplicata, fence),
requisito malformado, header, proveniencia do PRD (prd, prd-rev, prefixos),
cenarios herdados, RENAMED e MODIFIED sem Antes.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_spec.py"
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import _common  # noqa: E402
import lint_spec  # noqa: E402

PRD = """# PRD do Livro

Prefixo dos requisitos: `BOOK`.

## Functional Requirements

- **BOOK-01 (Must)** — Registrar reserva.
- **BOOK-02 (Should)** — Alterar reserva.
- **BOOK-NFR-01** — Prazo.

## Critérios de Aceitação

Contexto da tabela.

| Caso | Resultado |
|---|---|
| Reserva aceita | Ativa |
| Reserva rejeitada | rejeitada |

- **Dado** x, **quando** y, **então** z.
"""

HEADER = """| | |
|---|---|
| **Status** | {status} |
| **Autor** | {autor} |
| **Data** | {data} |
| **Capability** | reservation-book/reservation-lifecycle |
| **Prefixo** | {prefixo} |
"""

DELTA = """<!-- sdd: spec-delta | tier: medium | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book.md{rev} -->
# Livro

{header}
## Contexto (Context)

Origem no PRD 0002.

## Escopo e Fora de Escopo (Scope / Out of Scope)

**Em escopo:** registrar.

## Premissas e Perguntas em Aberto (Assumptions & Open Questions)

| Premissa | Default | Racional | Confirmada? |
|---|---|---|---|
| [PREMISSA] formato | JSON | padrao | nao |

**Perguntas em aberto:** nenhuma.

## Histórias (User Stories)

### P1: Registrar

## ADDED Requirements

{added}
{extra}
## Rastreabilidade (Requirement Traceability)

| ID do PRD | IDs EARS |
|---|---|
| BOOK-01 | RSV-01 |
| BOOK-02 | RSV-02 |

{scenarios}
## Ponto de Maior Fragilidade (Weakest Point)

O corte.
"""

ADDED = """- **RSV-01** — WHEN o operador registra THEN the system SHALL aceitar [BOOK-01]
- **RSV-02** — WHEN o operador altera THEN the system SHALL aceitar [BOOK-02]
"""

SCENARIOS = """| Cenário do PRD | IDs EARS |
|---|---|
| Reserva aceita | RSV-01 |
| Alteracao (BOOK-02) | RSV-02 |
"""


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
        self.change = os.path.join(self.root, "docs", "specs", "reservation-book",
                                   "reservation-lifecycle", "changes", "0001-reservation-lifecycle")
        os.makedirs(self.change)
        self.spec = os.path.join(self.change, "spec.md")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def write(path, text):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def delta(self, status="Rascunho", autor="Fulano", data="2026-09-06", prefixo="RSV",
              added=ADDED, extra="", scenarios=SCENARIOS, rev=""):
        header = HEADER.format(status=status, autor=autor, data=data, prefixo=prefixo)
        text = DELTA.format(header=header, added=added, extra=extra, scenarios=scenarios, rev=rev)
        self.write(self.spec, text)
        return run(self.spec)

    def assertHard(self, out, fragment):
        self.assertIn(fragment, out)
        self.assertTrue(any(l.startswith("HARD") and fragment in l for l in out.splitlines()),
                        f"'{fragment}' nao e HARD em:\n{out}")

    def assertWarn(self, out, fragment):
        self.assertTrue(any(l.startswith("WARN") and fragment in l for l in out.splitlines()),
                        f"'{fragment}' nao e WARN em:\n{out}")


class ValidSpec(Base):
    def test_valid_delta_passes_with_only_prd_rev_warn(self):
        code, out = self.delta()
        self.assertEqual(code, 0, out)
        self.assertIn("0 HARD, 1 WARN", out)
        self.assertWarn(out, "proveniencia sem revisao")


class SectionGrammar(Base):
    def test_non_functional_requirements_does_not_satisfy_requirements(self):
        living = os.path.join(self.root, "living.md")
        self.write(living, """<!-- sdd: spec | capability: x/y -->
# L

| | |
|---|---|
| **Status** | Vigente |
| **Data** | 2026-09-05 (última mudança: init) |
| **Capability** | x/y |
| **Prefixo** | RSV |

## Propósito (Purpose)

p

## Non-functional Requirements

- **RSV-01** — The system SHALL a

## Histórico de revisões

| Data | Mudança | IDs |
|---|---|---|
""")
        code, out = run(living)
        self.assertEqual(code, 1)
        self.assertHard(out, "spec viva sem secao ## Requisitos")

    def test_non_requirements_is_not_requirements(self):
        self.assertIsNone(_common.find_section_exact(
            ["## Non-Requirements", "x"], ("Requisitos", "Requirements")))
        self.assertEqual(_common.find_section_exact(
            ["## Requisitos (Requirements)", "x"], ("Requisitos", "Requirements")), (1, 2))

    def test_duplicate_heading_is_hard(self):
        code, out = self.delta(extra="## Contexto (Context)\n\ndup\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "secao duplicada ## Contexto")

    def test_requirement_inside_fence_is_ignored(self):
        fenced = "````md\n## MODIFIED Requirements\n- **RSV-01** — The system SHALL x [ZZZ-01]\n```\nainda dentro\n````\n"
        code, out = self.delta(extra=fenced)
        self.assertEqual(code, 0, out)
        self.assertNotIn("ID duplicado", out)
        self.assertNotIn("ZZZ", out)
        self.assertNotIn("MODIFIED", out)

    def test_fenced_line_mask_matches_closing_length(self):
        mask = _common.fenced_line_mask(["a", "~~~~", "x", "~~~", "y", "~~~~", "z"])
        self.assertEqual(mask, [False, True, True, True, True, True, False])


class RequirementLines(Base):
    def test_malformed_requirement_line_is_hard(self):
        code, out = self.delta(added=ADDED + "- **RSV-3** — The system SHALL c [BOOK-01]\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "linha com aparencia de requisito nao reconhecida")

    def test_missing_separator_is_hard(self):
        code, out = self.delta(added=ADDED + "- **RSV-03** The system SHALL c\n")
        self.assertHard(out, "linha com aparencia de requisito nao reconhecida")


class Header(Base):
    def test_invalid_status(self):
        code, out = self.delta(status="Qualquer")
        self.assertHard(out, "Status 'Qualquer' invalido")

    def test_placeholder_author(self):
        code, out = self.delta(autor="[nome]")
        self.assertHard(out, "Autor '[nome]' e placeholder")

    def test_invalid_calendar_date(self):
        code, out = self.delta(data="2026-99-99")
        self.assertHard(out, "nao e data de calendario")

    def test_invalid_date_format(self):
        code, out = self.delta(data="06/09/2026")
        self.assertHard(out, "formato AAAA-MM-DD")

    def test_empty_and_missing_fields_have_distinct_messages(self):
        code, out = self.delta(autor="")
        self.assertHard(out, "header com campo Autor vazio")
        with open(self.spec, encoding="utf-8") as f:
            text = f.read().replace("| **Autor** |  |\n", "")
        self.write(self.spec, text)
        code, out = run(self.spec)
        self.assertHard(out, "header sem campo obrigatorio Autor")

    def test_english_status_accepted(self):
        code, out = self.delta(status="In progress")
        self.assertEqual(code, 0, out)


class PrdProvenance(Base):
    def test_missing_prd_is_incomplete_hard(self):
        os.remove(self.prd)
        code, out = self.delta()
        self.assertEqual(code, 1)
        self.assertHard(out, "INCOMPLETO: validacao incompleta: PRD nao encontrado")

    def test_unknown_prefix_citation_is_hard_in_requirement_and_warn_in_prose(self):
        code, out = self.delta(added=ADDED + "- **RSV-03** — The system SHALL c [ZZZ-01]\n",
                               extra="Em prosa ZZZ-02 aparece.\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "citacao de ZZZ-01: prefixo 'ZZZ' nao e declarado")
        self.assertWarn(out, "citacao de ZZZ-02: prefixo 'ZZZ' nao e declarado")

    def test_unresolved_known_prefix_citation_is_hard(self):
        code, out = self.delta(added=ADDED + "- **RSV-03** — The system SHALL c [BOOK-99]\n")
        self.assertHard(out, "citacao de BOOK-99 nao resolve")

    def test_header_prefix_must_match_ids(self):
        code, out = self.delta(prefixo="RES")
        self.assertHard(out, "prefixo 'RSV' difere do Prefixo declarado no header ('RES')")

    def test_prefix_colliding_with_prd_is_hard(self):
        added = ADDED.replace("RSV-", "BOOK-")
        code, out = self.delta(prefixo="BOOK", added=added,
                               scenarios=SCENARIOS.replace("RSV-", "BOOK-"))
        self.assertHard(out, "prefixo da spec 'BOOK' coincide com prefixo de PRD")

    def test_prd_rev_sha256_matches(self):
        rev = _common.content_rev(self.prd)
        self.assertRegex(rev, r"^sha256:[0-9a-f]{12}$")
        code, out = self.delta(rev=f" | prd-rev: {rev}")
        self.assertEqual(code, 0, out)
        self.assertNotIn("proveniencia sem revisao", out)

    def test_prd_rev_sha256_ignores_line_endings(self):
        rev = _common.content_rev(self.prd)
        with open(self.prd, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(PRD)
        self.assertEqual(rev, _common.content_rev(self.prd))

    def test_prd_rev_divergent_is_hard(self):
        code, out = self.delta(rev=" | prd-rev: sha256:000000000000")
        self.assertEqual(code, 1)
        self.assertHard(out, "PRD mudou desde a spec; re-derive")

    def test_prd_rev_git_matches_when_git_available(self):
        rev = _common.git_blob_rev(self.prd)
        if rev is None:
            self.skipTest("git indisponivel")
        self.assertRegex(rev, r"^git:[0-9a-f]{40,64}$")
        code, out = self.delta(rev=f" | prd-rev: {rev}")
        self.assertEqual(code, 0, out)

    def test_prd_rev_git_without_git_is_incomplete(self):
        with mock.patch.object(lint_spec, "git_blob_rev", return_value=None):
            code, out = self.delta(rev=" | prd-rev: git:" + "a" * 40)
        self.assertHard(out, "INCOMPLETO: prd-rev declarado como git:")

    def test_prd_rev_missing_is_warn(self):
        code, out = self.delta()
        self.assertWarn(out, "proveniencia sem revisao; adicione prd-rev")

    def test_print_prd_rev_flag(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = lint_spec.main(["lint_spec.py", "--print-prd-rev", self.prd])
        self.assertEqual(code, 0)
        expected = _common.git_blob_rev(self.prd) or _common.content_rev(self.prd)
        self.assertEqual(buf.getvalue().strip(), expected)


class InheritedScenarios(Base):
    def test_scenario_without_id_or_case_name_is_hard(self):
        scen = SCENARIOS + "| Cenario inventado | RSV-01 |\n"
        code, out = self.delta(scenarios=scen)
        self.assertEqual(code, 1)
        self.assertHard(out, "cenario herdado 'Cenario inventado' nao cita ID do PRD")

    def test_scenario_by_case_name_and_by_id_pass(self):
        code, out = self.delta()
        self.assertNotIn("cenario herdado", out)

    def test_scenario_citing_unknown_ears_id_is_hard(self):
        scen = SCENARIOS + "| Reserva rejeitada | RSV-77 |\n"
        code, out = self.delta(scenarios=scen)
        self.assertHard(out, "requisito EARS RSV-77 nao existe no delta")


class DeltaModel(Base):
    def test_renamed_is_hard(self):
        code, out = self.delta(extra="## RENAMED Requirements\n\n- **RSV-01** — a → b\n")
        self.assertEqual(code, 1)
        self.assertHard(out, "RENAMED nao suportado")

    def test_modified_without_before_is_hard(self):
        living = os.path.join(self.root, "docs", "specs", "reservation-book",
                              "reservation-lifecycle", "spec.md")
        self.write(living, "<!-- sdd: spec | capability: x -->\n# L\n\n## Requisitos\n\n"
                           "- **RSV-05** — The system SHALL old\n")
        code, out = self.delta(extra="## MODIFIED Requirements\n\n"
                                     "- **RSV-05** — The system SHALL new [BOOK-01]\n")
        self.assertHard(out, "MODIFIED RSV-05: sem linha 'Antes:'")
        code, out = self.delta(extra="## MODIFIED Requirements\n\n"
                                     "- **RSV-05** — The system SHALL new [BOOK-01]\n"
                                     "  Antes: The system SHALL old\n")
        self.assertNotIn("sem linha 'Antes:'", out)
        self.assertNotIn("MODIFIED RSV-05: ID nao existe", out)


if __name__ == "__main__":
    unittest.main()
