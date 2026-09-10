"""Testes do lint_design.py: comentario de maquina (`sdd: design` e `spec:`
que resolve), secoes conhecidas na ordem de references/design.md e sem secao
vazia, cobertura dos requisitos `IF ... THEN` da spec em Tratamento de erros
(com e sem `scope:`), placeholder e erros de uso.

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
- **Proposito:** aceitar e alterar reservas contra a oferta publicada.
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


class ValidDocumentTest(LintDesignBase):
    def test_valid_design_passes(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_all_known_sections_in_order_pass(self):
        sections = [("Contexto de design", CONTEXT),
                    ("Critérios de avaliação", "| # | Criterio | Origem |\n|---|---|---|\n| C1 | x | BOOK-NFR-02 |"),
                    ("Riscos e técnicas", "| Risco | Tecnica |\n|---|---|\n| Duplicata | Idempotency key |"),
                    ("Abordagens", "Sem alternativa real."),
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

    def test_template_is_clean(self):
        tpl = self.template()
        handled = sorted(set(re.findall(r"\bRSV-\d{2}\b", self.section(tpl, "Tratamento de erros"))))
        self.assertEqual(len(handled), 1, f"template trata {handled}; o teste assume um so")
        ids = sorted(set(re.findall(r"\bRSV-\d{2}\b", tpl)))
        reqs = "".join(
            f"- **{r}** — IF x THEN the system SHALL y\n" if r in handled
            else f"- **{r}** — WHEN x THEN the system SHALL y\n" for r in ids)
        spec = self.write(os.path.join(self.cap, "spec-template.md"),
                          SPEC[:SPEC.index("- **RSV-07**")] + reqs)
        code, out = self.run_lint(tpl + "\n", spec=spec)
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    @staticmethod
    def section(text, title):
        lines = text.splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == f"## {title}")
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        return "\n".join(lines[start:end])


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
