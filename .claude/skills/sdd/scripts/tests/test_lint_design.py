"""Testes do lint_design.py: comentario de maquina (`sdd: design` e `spec:`
que resolve), secoes conhecidas na ordem de references/design.md e sem secao
vazia, fecho 'Sem alternativa real:' em Criterios de avaliacao contra a
presenca de Abordagens, cobertura dos requisitos `IF ... THEN` da spec em
Tratamento de erros (com e sem `scope:`), proposito de componente em uma so
frase, placeholder e erros de uso.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_design.py"
"""

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import lint_design  # noqa: E402

DESIGN_MD = os.path.join(os.path.dirname(SCRIPTS), "references", "design.md")

SPEC = """\
<!-- sdd: spec | capability: reservation-book/reservation-lifecycle -->
# Reserva Parcial — Spec

Prefixo dos requisitos: `RSV`.

## Contexto

Origem no PRD 0002.

## Requisitos

- **RSV-07** — WHEN o operador registra a reserva THEN the system SHALL aceitar
- **RSV-11** — IF a posicao fica acima do maximo THEN the system SHALL rejeitar com `POSITION_ABOVE_MAXIMUM`
"""

CONTEXT = ("Spec: RSV-07 a RSV-11. ADR 0001 (outbox) restringe a publicacao de eventos. "
           "Base lida: `src/ReservationBook/Reservations/*`.")
COMPONENTS = """\
### ReservationService
- **Proposito:** aceitar reservas contra a oferta publicada.
- **Localizacao:** `src/ReservationBook/Reservations/ReservationService.cs`"""
ERRORS = """\
| Cenario (ID) | Tratamento | Impacto |
|---|---|---|
| Posicao acima do maximo (RSV-11) | `Result.Failure(POSITION_ABOVE_MAXIMUM)`; 422 no endpoint | Operador ve a posicao |"""

COMMENT = "<!-- sdd: design | spec: ../spec.md -->"


def doc(sections=None, comment=COMMENT):
    if sections is None:
        sections = [("Contexto de design", CONTEXT),
                    ("Componentes", COMPONENTS),
                    ("Tratamento de erros", ERRORS)]
    body = "".join(f"\n## {title}\n\n{text}\n" for title, text in sections)
    return f"{comment}\n# Reserva Parcial — Design\n{body}"


class LintDesignBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.cap = os.path.join(self.root, "docs", "specs", "reservation-book", "reservation-lifecycle")
        self.change = os.path.join(self.cap, "0001-reserva-parcial")
        os.makedirs(self.change)
        self.spec = self.write(os.path.join(self.cap, "spec.md"), SPEC)
        self.design = os.path.join(self.change, "design.md")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def write(path, content):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        return path

    def run_lint(self, content, spec="default", *args):
        self.write(self.design, content)
        argv = ["lint_design.py", self.design]
        if spec == "default":
            argv += ["--spec", self.spec]
        elif spec is not None:
            argv += ["--spec", spec]
        argv += list(args)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lint_design.main(argv)
        return code, out.getvalue()

    def findings(self, out, level):
        return [l for l in out.splitlines() if l.startswith(level)]

    def assertHard(self, out, fragment):
        self.assertTrue(any(fragment in l for l in self.findings(out, "HARD")),
                        f"esperava HARD com '{fragment}'; saida:\n{out}")

    def assertNoHard(self, out):
        self.assertEqual(self.findings(out, "HARD"), [], f"nao esperava HARD; saida:\n{out}")

    def assertWarn(self, out, fragment):
        self.assertTrue(any(fragment in l for l in self.findings(out, "WARN")),
                        f"esperava WARN com '{fragment}'; saida:\n{out}")

    def assertNoWarn(self, out, fragment):
        self.assertFalse(any(fragment in l for l in self.findings(out, "WARN")),
                         f"nao esperava WARN com '{fragment}'; saida:\n{out}")


class ValidDocumentTest(LintDesignBase):
    def test_valid_design_passes(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_all_known_sections_in_order_pass(self):
        sections = [("Contexto de design", CONTEXT),
                    ("Critérios de avaliação", "| # | Criterio | Origem |\n|---|---|---|\n| C1 | x | BOOK-NFR-02 |"),
                    ("Riscos e técnicas", "| Risco | Tecnica |\n|---|---|\n| Duplicata | Idempotency key |"),
                    ("Abordagens", "| Abordagem | C1 | C2 |\n|---|---|---|\n| Outbox (recomendada) | atende | 3s |\n| Fila dedicada | atende | 1s |"),
                    ("Visão da arquitetura", "Um servico, um modulo."),
                    ("Unidade de deploy", "Fica em `src/ReservationBook`."),
                    ("Componentes", COMPONENTS),
                    ("Domain Events", "Nenhum evento novo nesta mudanca."),
                    ("Modelo de dados", "Tabela `reservations` ganha a coluna `position`."),
                    ("Tratamento de erros", ERRORS),
                    ("Decisões técnicas", "| Decisao | Escolha | Racional | Tipo |\n|---|---|---|---|\n| Ordem | Contador | x | interna |"),
                    ("Arquivos a criar ou modificar", "- `src/ReservationBook/Reservations/ReservationService.cs` — novo")]
        code, out = self.run_lint(doc(sections))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_english_section_names_are_accepted(self):
        sections = [("Design Context", CONTEXT), ("Components", COMPONENTS), ("Error handling", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertNoHard(out)


class MachineCommentTest(LintDesignBase):
    def test_missing_or_wrong_kind_is_hard(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: tasks | spec: ../spec.md -->"))
        self.assertHard(out, "primeira linha deve ser <!-- sdd: design")
        code, out = self.run_lint(doc().replace(COMMENT + "\n", ""))
        self.assertHard(out, "primeira linha deve ser <!-- sdd: design")

    def test_missing_spec_field_is_hard(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: design -->"))
        self.assertHard(out, "sem 'spec:'")

    def test_spec_field_that_does_not_resolve_is_hard(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: design | spec: ./spec.md -->"))
        self.assertHard(out, "spec do comentario de maquina nao encontrada: './spec.md'")

    def test_root_relative_spec_field_resolves(self):
        target = "/docs/specs/reservation-book/reservation-lifecycle/spec.md"
        code, out = self.run_lint(doc(comment=f"<!-- sdd: design | spec: {target} -->"))
        self.assertNoHard(out)


class SectionsTest(LintDesignBase):
    def test_unknown_section_is_hard(self):
        sections = [("Contexto de design", CONTEXT), ("Estratégia de rollout", "Canario."),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertEqual(code, 1)
        self.assertHard(out, "secao desconhecida: ## Estratégia de rollout")

    def test_section_out_of_order_is_hard(self):
        sections = [("Componentes", COMPONENTS), ("Contexto de design", CONTEXT),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertEqual(code, 1)
        self.assertHard(out, "secao fora de ordem: 'Componentes' aparece antes de 'Contexto de design'")

    def test_empty_section_is_hard(self):
        sections = [("Contexto de design", CONTEXT), ("Componentes", ""),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertEqual(code, 1)
        self.assertHard(out, "secao sem conteudo: Componentes")

    def test_section_reduced_to_a_negation_is_hard(self):
        sections = [("Contexto de design", CONTEXT), ("Domain Events", "Nenhum."),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertHard(out, "secao sem conteudo: Domain Events")

    def test_last_section_with_content_is_not_reported_as_empty(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)

    def test_heading_inside_fence_is_ignored(self):
        fenced = "```markdown\n## Secao Inventada\n\n```\n"
        code, out = self.run_lint(doc() + "\n" + fenced)
        self.assertNoHard(out)


CRITERIA = ("| # | Criterio | Origem |\n|---|---|---|\n"
            "| C1 | O livro lido pelo Allocation e identico ao congelado | BOOK-NFR-02 |")
NO_ALT = "Sem alternativa real: a ADR 0001 ja fixa o transporte e a spec fixa o comportamento."
APPROACHES = ("| Abordagem | C1 |\n|---|---|\n| Outbox (recomendada) | atende |\n"
              "| Fila dedicada | atende |")


class NoRealAlternativeTest(LintDesignBase):
    """Sem a secao Abordagens, Criterios de avaliacao fecha com 'Sem
    alternativa real: <motivo>'; com ela, a linha nega a tabela abaixo."""

    def sections(self, criteria, approaches=None, criteria_title="Critérios de avaliação"):
        out = [("Contexto de design", CONTEXT), (criteria_title, criteria)]
        if approaches is not None:
            out.append(("Abordagens", approaches))
        out.append(("Tratamento de erros", ERRORS))
        return out

    def test_criteria_closing_with_the_line_passes(self):
        code, out = self.run_lint(doc(self.sections(CRITERIA + "\n\n" + NO_ALT)))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_criteria_without_the_line_is_hard(self):
        code, out = self.run_lint(doc(self.sections(CRITERIA)))
        self.assertEqual(code, 1)
        self.assertHard(out, "sem a secao ## Abordagens, a ultima linha de Critérios de avaliação")

    def test_line_out_of_the_last_position_is_hard(self):
        code, out = self.run_lint(doc(self.sections(NO_ALT + "\n\n" + CRITERIA)))
        self.assertHard(out, "sem a secao ## Abordagens, a ultima linha de Critérios de avaliação")

    def test_line_with_approaches_section_is_hard(self):
        code, out = self.run_lint(doc(self.sections(CRITERIA + "\n\n" + NO_ALT, APPROACHES)))
        self.assertEqual(code, 1)
        self.assertHard(out, "com a secao ## Abordagens presente")

    def test_approaches_without_the_line_passes(self):
        code, out = self.run_lint(doc(self.sections(CRITERIA, APPROACHES)))
        self.assertNoHard(out)

    def test_english_line_is_accepted(self):
        sections = self.sections(CRITERIA + "\n\nNo real alternative: ADR 0001 fixes the transport.",
                                 criteria_title="Evaluation Criteria")
        code, out = self.run_lint(doc(sections))
        self.assertNoHard(out)

    def test_line_inside_fence_does_not_count(self):
        fenced = CRITERIA + "\n\n```markdown\n" + NO_ALT + "\n```"
        code, out = self.run_lint(doc(self.sections(fenced)))
        self.assertHard(out, "sem a secao ## Abordagens, a ultima linha de Critérios de avaliação")

    def test_design_without_the_section_is_silent(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)


class ErrorHandlingCoverageTest(LintDesignBase):
    def test_unwanted_requirement_without_scenario_is_hard(self):
        errors = ERRORS.replace("(RSV-11)", "(RSV-07)")
        sections = [("Contexto de design", CONTEXT), ("Tratamento de erros", errors)]
        code, out = self.run_lint(doc(sections))
        self.assertEqual(code, 1)
        self.assertHard(out, "RSV-11: requisito IF ... THEN da spec sem cenario em ## Tratamento de erros")

    def test_missing_section_with_unwanted_requirement_is_hard(self):
        sections = [("Contexto de design", CONTEXT), ("Componentes", COMPONENTS)]
        code, out = self.run_lint(doc(sections))
        self.assertHard(out, "secao ausente: ## Tratamento de erros")
        self.assertIn("RSV-11", out)

    def test_spec_without_unwanted_requirement_does_not_require_the_section(self):
        without = "".join(l + "\n" for l in SPEC.splitlines() if not l.startswith("- **RSV-11**"))
        spec = self.write(os.path.join(self.cap, "spec2.md"), without)
        sections = [("Contexto de design", CONTEXT), ("Componentes", COMPONENTS)]
        code, out = self.run_lint(doc(sections), spec=spec)
        self.assertNoHard(out)

    def test_requirement_inside_fence_of_the_spec_is_ignored(self):
        spec = self.write(os.path.join(self.cap, "spec3.md"), SPEC + "\n```md\n- **RSV-12** — IF x THEN the system SHALL y\n```\n")
        sections = [("Contexto de design", CONTEXT), ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections), spec=spec)
        self.assertNoHard(out)

    def test_id_cited_anywhere_in_the_section_counts(self):
        errors = "Posicao acima do maximo (RSV-11): `Result.Failure`; 422 no endpoint."
        sections = [("Contexto de design", CONTEXT), ("Tratamento de erros", errors)]
        code, out = self.run_lint(doc(sections))
        self.assertNoHard(out)

    def test_missing_spec_flag_is_hard(self):
        code, out = self.run_lint(doc(), spec=None)
        self.assertHard(out, "--spec obrigatorio")

    def test_nonexistent_spec_is_hard(self):
        code, out = self.run_lint(doc(), spec=os.path.join(self.root, "nope.md"))
        self.assertHard(out, "spec nao encontrada")


class ScopeTest(LintDesignBase):
    """`scope:` restringe a cobertura `IF ... THEN` aos requisitos listados."""

    def setUp(self):
        super().setUp()
        self.spec2 = self.write(
            os.path.join(self.cap, "spec2.md"),
            SPEC + "- **RSV-12** — IF o livro esta fechado THEN the system SHALL rejeitar com `BOOK_CLOSED`\n")

    def scoped(self, scope):
        return doc(comment=f"<!-- sdd: design | spec: ../spec.md | scope: {scope} -->")

    def test_requirement_outside_scope_is_not_required(self):
        code, out = self.run_lint(self.scoped("RSV-11"), spec=self.spec2)
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_without_scope_every_unwanted_requirement_is_required(self):
        code, out = self.run_lint(doc(), spec=self.spec2)
        self.assertHard(out, "RSV-12: requisito IF ... THEN da spec sem cenario")

    def test_requirement_inside_scope_without_scenario_is_hard(self):
        code, out = self.run_lint(self.scoped("RSV-11, RSV-12"), spec=self.spec2)
        self.assertHard(out, "RSV-12: requisito IF ... THEN da spec sem cenario")

    def test_scope_with_unknown_id_is_hard(self):
        code, out = self.run_lint(self.scoped("RSV-11, RSV-42"), spec=self.spec2)
        self.assertHard(out, "scope: RSV-42 nao existe na spec")


PURPOSE_WARN = "proposito com mais de uma frase ou com 'e'"


class ComponentPurposeTest(LintDesignBase):
    """Um componente, um proposito: WARN quando o proposito soma
    responsabilidades com 'e' ou se estende por mais de uma frase."""

    def lint_purpose(self, purpose):
        components = (f"### ReservationService\n- **Propósito:** {purpose}\n"
                      "- **Localizacao:** `src/ReservationBook/Reservations/ReservationService.cs`")
        sections = [("Contexto de design", CONTEXT), ("Componentes", components),
                    ("Tratamento de erros", ERRORS)]
        return self.run_lint(doc(sections))

    def test_single_purpose_is_silent(self):
        code, out = self.lint_purpose("manter o livro de reservas de uma oferta publicada.")
        self.assertNoWarn(out, PURPOSE_WARN)
        self.assertEqual(code, 0)

    def test_purpose_with_conjunction_is_warn(self):
        code, out = self.lint_purpose("aceitar e alterar reservas da oferta publicada.")
        self.assertWarn(out, PURPOSE_WARN)
        self.assertEqual(code, 0)

    def test_purpose_with_two_sentences_is_warn(self):
        code, out = self.lint_purpose("manter o livro de reservas. Publicar o resultado.")
        self.assertWarn(out, PURPOSE_WARN)

    def test_conjunction_and_dots_inside_backticks_do_not_count(self):
        code, out = self.lint_purpose(
            "manter o `livro e o lastro` de `src/ReservationBook/Reservations/Book.cs`.")
        self.assertNoWarn(out, PURPOSE_WARN)

    def test_purpose_without_accent_is_read(self):
        components = "### ReservationService\n- **Proposito:** aceitar e alterar reservas."
        sections = [("Contexto de design", CONTEXT), ("Componentes", components),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertWarn(out, PURPOSE_WARN)

    def test_purpose_outside_the_components_section_is_ignored(self):
        sections = [("Contexto de design", "- **Propósito:** aceitar e alterar reservas."),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertNoWarn(out, PURPOSE_WARN)

    def test_purpose_inside_fence_is_ignored(self):
        components = ("### ReservationService\n- **Propósito:** manter o livro.\n\n"
                      "```markdown\n- **Propósito:** aceitar e alterar reservas.\n```")
        sections = [("Contexto de design", CONTEXT), ("Componentes", components),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertNoWarn(out, PURPOSE_WARN)


class PlaceholderTest(LintDesignBase):
    def test_placeholder_is_warn_not_hard(self):
        sections = [("Contexto de design", CONTEXT + " TBD: base ignorada."),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "placeholder")

    def test_placeholder_inside_fence_is_ignored(self):
        sections = [("Contexto de design", CONTEXT + "\n\n```text\nTODO no exemplo\n```"),
                    ("Tratamento de erros", ERRORS)]
        code, out = self.run_lint(doc(sections))
        self.assertEqual(self.findings(out, "WARN"), [], out)


class TemplateRegressionTest(LintDesignBase):
    """O template de references/design.md, gravado como design.md da mudanca,
    linta sem HARD contra uma spec cujo unico requisito `IF ... THEN` e o que
    o template trata."""

    def template(self):
        with open(DESIGN_MD, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"## Template\b[^\n]*\n+`{3,4}markdown\n(.*?)\n`{3,4}\n", text, re.DOTALL)
        self.assertIsNotNone(m, "bloco de template nao encontrado em references/design.md")
        return m.group(1)

    def lint_template(self):
        """A spec do teste define todo ID que o template cita, inclusive os do
        `scope:`, e so o requisito tratado em Tratamento de erros e
        `IF ... THEN`."""
        tpl = self.template()
        handled = sorted(set(re.findall(r"\bRSV-\d{2}\b", self.section(tpl, "Tratamento de erros"))))
        self.assertEqual(len(handled), 1, f"template trata {handled}; o teste assume um so")
        scope = self.scope(tpl)
        self.assertIn(handled[0], scope, "o requisito tratado esta fora do scope do template")
        ids = sorted(set(scope) | set(re.findall(r"\bRSV-\d{2}\b", tpl)))
        reqs = "".join(
            f"- **{r}** — IF x THEN the system SHALL y\n" if r in handled
            else f"- **{r}** — WHEN x THEN the system SHALL y\n" for r in ids)
        spec = self.write(os.path.join(self.cap, "spec-template.md"),
                          SPEC[:SPEC.index("- **RSV-07**")] + reqs)
        return self.run_lint(tpl + "\n", spec=spec)

    def test_template_is_clean(self):
        code, out = self.lint_template()
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_every_scope_id_is_a_requirement_of_the_spec(self):
        """`scope:` do template so existe contra uma spec que define os IDs;
        ID de escopo sem requisito e HARD."""
        scope = self.scope(self.template())
        self.assertTrue(scope, "template sem scope: no comentario de maquina")
        code, out = self.lint_template()
        self.assertNotIn("nao existe na spec", out)

    @staticmethod
    def scope(text):
        """IDs do `scope:` do comentario de maquina do template."""
        comment = next(l for l in text.splitlines() if l.strip().startswith("<!--"))
        return sorted(set(re.findall(r"\bRSV-\d{2}\b", comment)))

    def test_template_purpose_is_silent(self):
        code, out = self.lint_template()
        self.assertNoWarn(out, PURPOSE_WARN)

    @staticmethod
    def section(text, title):
        lines = text.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == f"## {title}")
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        return "\n".join(lines[start:end])


class SectionsInSyncWithReferenceTest(unittest.TestCase):
    """A lista de secoes do script e a de references/design.md, secao Secoes:
    mesmos nomes, mesma ordem. Doc e script divergentes fazem o linter recusar
    a secao que a referencia manda escrever."""

    @staticmethod
    def documented():
        with open(DESIGN_MD, encoding="utf-8") as f:
            lines = f.read().splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "## Seções")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
        out = []
        for l in lines[start:end]:
            m = re.match(r"^\d+\.\s+(.+)$", l.strip())
            if m:
                out.append(re.split(r"\s+—\s+", m.group(1))[0].strip().rstrip("."))
        return out

    def test_names_and_order_match(self):
        names = self.documented()
        self.assertTrue(names, "lista numerada de secoes nao encontrada em references/design.md")
        self.assertEqual(names, [aliases[0] for aliases in lint_design.SECTIONS_ORDER])


class UsageTest(LintDesignBase):
    def exit_code(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_design.main(["lint_design.py", *argv])
            except SystemExit as e:
                code = e.code
        return code, err.getvalue()

    def test_unknown_option_is_usage(self):
        self.write(self.design, doc())
        code, err = self.exit_code(self.design, "--spec", self.spec, "--bogus")
        self.assertEqual(code, 2)
        self.assertIn("opcao desconhecida", err)

    def test_missing_file_is_usage_not_traceback(self):
        code, err = self.exit_code(os.path.join(self.root, "nope.md"), "--spec", self.spec)
        self.assertEqual(code, 2)
        self.assertIn("arquivo ilegivel", err)
        self.assertNotIn("Traceback", err)

    def test_non_utf8_file_is_usage(self):
        with open(self.design, "wb") as f:
            f.write(b"<!-- sdd: design | spec: ../spec.md -->\n# T\x97\n")
        code, err = self.exit_code(self.design, "--spec", self.spec)
        self.assertEqual(code, 2)
        self.assertIn("UTF-8", err)


if __name__ == "__main__":
    unittest.main()
