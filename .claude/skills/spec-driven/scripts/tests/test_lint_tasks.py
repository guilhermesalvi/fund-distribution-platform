"""Testes do lint_tasks.py.

Roda com:
    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_tasks.py"
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
import lint_tasks  # noqa: E402

TASKS_MD = os.path.join(os.path.dirname(SCRIPTS), "references", "tasks.md")

MATRIX = "| Dominio | unit | todas as ramificacoes | tests/Domain.Tests | `dotnet test tests/Domain.Tests` |"
GATES = """\
| Quick | task com unit test | `dotnet test tests/Domain.Tests` |
| Full | task com integration/e2e | `dotnet test` |
| Build | ultima da fase; task sem teste | `dotnet build && dotnet test` |"""
PLAN = "### Fase 1: Dominio\nT1 → T2\n\n### Fase 2: Adapters\nT3"

SPEC = """\
<!-- sdd: spec | tier: large | capability: reservation -->
# Spec

## ADDED Requirements
- **RSV-07** — WHEN amount < lot THEN the system SHALL reject with MIN_LOT_NOT_MET
"""


def task(tid, deps="nenhuma", req="RSV-07", tests="unit", gate="quick",
         commit="feat: add thing", done=None, extra=""):
    done = done or ["`Create` rejeita valor abaixo do lote com `MinLotNotMet`",
                    "Gate passa: `dotnet test tests/Domain.Tests`"]
    d = "\n".join(f"  - [ ] {c}" for c in done)
    return f"""### {tid}: Criar coisa {tid}
- **O quê:** value object com validacao de lote
- **Onde:** `src/Domain/Thing{tid}.cs`; `tests/Domain.Tests/Thing{tid}Tests.cs`
- **Depende de:** {deps}
- **Requisito:** {req}
- **Interfaces:**
  - Consome: `Money`
  - Produz: `Thing.Create(Money m): Result<Thing>`
- **Pronto quando:**
{d}
- **Tests:** {tests}
- **Gate:** {gate}
- **Commit:** `{commit}`
{extra}
"""


def doc(tasks=None, plan=PLAN, matrix=MATRIX, gates=GATES, extra=""):
    if tasks is None:
        tasks = [task("T1"), task("T2", deps="T1"), task("T3", deps="T2")]
    return f"""<!-- sdd: tasks | tier: large | design: ./design.md -->
# Coisa — Tasks

## Matriz de Cobertura de Testes
> Gerada do repositorio.

| Camada | Tipo de teste | Expectativa de cobertura | Padrão de localização | Comando |
|---|---|---|---|---|
{matrix}

## Comandos de Gate

| Gate | Quando | Comando |
|---|---|---|
{gates}

## Plano de execução

{plan}

## Tasks

{"".join(tasks)}
{extra}
"""


class LintTasksBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.spec = self.write("spec.md", SPEC)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def run_lint(self, content, *args, spec="default", name="tasks.md"):
        path = self.write(name, content)
        argv = ["lint_tasks.py", path]
        if spec == "default":
            argv += ["--spec", self.spec]
        elif spec is not None:
            argv += ["--spec", spec]
        argv += list(args)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lint_tasks.main(argv)
        return code, out.getvalue()

    def findings(self, out, level):
        return [l for l in out.splitlines() if l.startswith(level)]

    def assertHard(self, out, fragment):
        self.assertTrue(any(fragment in l for l in self.findings(out, "HARD")),
                        f"esperava HARD com '{fragment}'; saida:\n{out}")

    def assertNoHard(self, out):
        self.assertEqual(self.findings(out, "HARD"), [], f"nao esperava HARD; saida:\n{out}")

    def assertNoHardWith(self, out, fragment):
        self.assertFalse(any(fragment in l for l in self.findings(out, "HARD")),
                         f"nao esperava HARD com '{fragment}'; saida:\n{out}")

    def assertWarn(self, out, fragment):
        self.assertTrue(any(fragment in l for l in self.findings(out, "WARN")),
                        f"esperava WARN com '{fragment}'; saida:\n{out}")


class ValidDocumentTest(LintTasksBase):
    def test_valid_tasks_pass(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_higher_number_in_same_phase_is_accepted(self):
        # T2 depende de T3, ambas na fase 1, sem ciclo: ordem topologica existe.
        tasks = [task("T1"), task("T2", deps="T3"), task("T3", deps="T1")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T3 → T2"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)


class DuplicateIdTest(LintTasksBase):
    def test_duplicate_task_id_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T1", commit="feat: first"),
                 task("T2", deps="T1", commit="feat: second")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2"))
        self.assertHard(out, "ID de task duplicado: T2")
        self.assertEqual(code, 1)


class DependencyTest(LintTasksBase):
    def test_missing_dependency_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T9"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: depende de T9, que nao existe")
        self.assertEqual(code, 1)

    def test_cycle_is_hard_with_ids(self):
        tasks = [task("T1", deps="T2"), task("T2", deps="T1"), task("T3")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2 → T3"))
        self.assertHard(out, "ciclo de dependencia: T1 -> T2 -> T1")
        self.assertEqual(code, 1)

    def test_dependency_on_later_phase_is_hard(self):
        tasks = [task("T1", deps="T3"), task("T2", deps="T1"), task("T3")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1 (fase 1) depende de T3 (fase 2) - dependencia para fase posterior")
        self.assertEqual(code, 1)

    def test_higher_number_without_phase_is_hard(self):
        tasks = [task("T1", deps="T2"), task("T2"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks, plan="T1, T2, T3"))
        self.assertHard(out, "T1: depende de T2 (numero maior ou igual")
        self.assertEqual(code, 1)


class ExecutionPlanTest(LintTasksBase):
    def test_plan_citing_missing_task_is_hard(self):
        code, out = self.run_lint(doc(plan="### Fase 1: X\nT1 → T2 → T9\n\n### Fase 2: Y\nT3"))
        self.assertHard(out, "Plano de execucao cita T9, que nao existe")
        self.assertEqual(code, 1)

    def test_task_outside_plan_is_hard(self):
        code, out = self.run_lint(doc(plan="### Fase 1: X\nT1 → T2"))
        self.assertHard(out, "T3: nao aparece no Plano de execucao")
        self.assertEqual(code, 1)

    def test_map_diverging_from_plan_is_hard(self):
        code, out = self.run_lint(doc(extra="## Mapa de execução\n\n```\nFase 1: T1 → T2\n```\n"))
        self.assertHard(out, "Mapa de execucao diverge do Plano de execucao: so no plano: T3")
        self.assertEqual(code, 1)

    def test_map_matching_plan_passes(self):
        code, out = self.run_lint(doc(extra="## Mapa de execução\n\n```\nFase 1: T1 → T2\nFase 2: T3\n```\n"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)


class TablesTest(LintTasksBase):
    def test_empty_matrix_is_hard(self):
        code, out = self.run_lint(doc(matrix=""))
        self.assertHard(out, "secao Matriz de Cobertura sem linhas de dados")
        self.assertEqual(code, 1)

    def test_empty_gate_table_is_hard(self):
        code, out = self.run_lint(doc(gates=""))
        self.assertHard(out, "secao Comandos de Gate sem linhas de dados")
        self.assertEqual(code, 1)

    def test_empty_command_cell_is_hard(self):
        code, out = self.run_lint(doc(gates="| Quick | unit |  |\n| Build | fase | `dotnet build` |"))
        self.assertHard(out, "Comandos de Gate: celula de comando vazia")
        self.assertEqual(code, 1)

    def test_gate_used_without_command_row_is_hard(self):
        code, out = self.run_lint(doc(gates="| Build | fase | `dotnet build` |"))
        self.assertHard(out, "Gate 'quick' usado em T1, T2, T3 sem linha na tabela Comandos de Gate")
        self.assertEqual(code, 1)

    def test_gate_row_match_is_case_insensitive(self):
        code, out = self.run_lint(doc(gates="| QUICK | unit | `dotnet test` |\n| build | fase | `dotnet build` |"))
        self.assertNoHard(out)


class SpecArgumentTest(LintTasksBase):
    def test_missing_spec_flag_is_hard_incomplete(self):
        code, out = self.run_lint(doc(), spec=None)
        self.assertHard(out, "validacao incompleta: --spec obrigatorio")
        self.assertEqual(code, 1)

    def test_nonexistent_spec_is_hard_incomplete(self):
        code, out = self.run_lint(doc(), spec=os.path.join(self.dir, "nope.md"))
        self.assertHard(out, "validacao incompleta: spec nao encontrada")
        self.assertEqual(code, 1)

    def test_spec_without_delta_sections_is_hard_incomplete(self):
        living = self.write("living.md", "<!-- sdd: spec | tier: large -->\n# Spec\n\n## Requisitos\n- **RSV-07** — x\n")
        code, out = self.run_lint(doc(), spec=living)
        self.assertHard(out, "validacao incompleta")
        self.assertHard(out, "sem secao ADDED/MODIFIED Requirements")
        self.assertEqual(code, 1)

    def test_requirement_without_task_is_hard(self):
        spec = self.write("spec2.md", SPEC + "- **RSV-08** — WHEN y THEN the system SHALL z\n")
        code, out = self.run_lint(doc(), spec=spec)
        self.assertHard(out, "requisito RSV-08 da spec sem task")
        self.assertEqual(code, 1)


class CorrectionTaskTest(LintTasksBase):
    def test_tc1_is_recognized_and_validated(self):
        code, out = self.run_lint(doc(extra="## Tasks de correção\n\n" + task("TC1", deps="T3")))
        self.assertNoHard(out)
        self.assertEqual(code, 0)
        # mesma validacao de campos: TC com Gate invalido dispara HARD com o ID TC1
        code, out = self.run_lint(doc(extra="## Tasks de correção\n\n" + task("TC1", deps="T3", gate="nope")))
        self.assertHard(out, "TC1: Gate invalido")

    def test_tc_inside_tasks_section_is_accepted(self):
        tasks = [task("T1"), task("T2", deps="T1"), task("T3", deps="T2"), task("TC1", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_tc_depending_on_tc_and_own_numbering(self):
        extra = "## Tasks de correção\n\n" + task("TC1", deps="T1") + task("TC2", deps="TC1")
        code, out = self.run_lint(doc(extra=extra))
        self.assertNoHard(out)

    def test_t_depending_on_tc_is_hard(self):
        tasks = [task("T1"), task("T2", deps="TC1"), task("T3", deps="T2"), task("TC1", deps="T1")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: depende de TC1 - task de correcao nasce no Verify")


class FieldsTest(LintTasksBase):
    def test_duplicate_field_is_hard(self):
        tasks = [task("T1", extra="- **Tests:** unit"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: campo duplicado: tests")
        self.assertEqual(code, 1)

    def test_missing_empty_and_invalid_are_distinct(self):
        tasks = [task("T1", tests=""), task("T2", deps="T1", tests="fuzz"), task("T3", deps="T2")]
        content = doc(tasks).replace("- **Tests:** unit\n- **Gate:** quick\n- **Commit:** `feat: add thing`\n\n",
                                     "- **Gate:** quick\n- **Commit:** `feat: add thing`\n\n", 1)
        code, out = self.run_lint(content)
        self.assertHard(out, "T1: campo vazio: tests")
        self.assertHard(out, "T2: Tests invalido: tipo(s) invalido(s): 'fuzz'")
        self.assertHard(out, "T3: campo obrigatorio ausente: tests")

    def test_tests_list_of_valid_types_is_accepted(self):
        tasks = [task("T1", tests="unit, integration", gate="full"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_none_in_list_is_rejected(self):
        tasks = [task("T1", tests="none, unit"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests invalido: 'none' so sozinho")
        self.assertEqual(code, 1)

    def test_tests_none_with_gate_quick_is_hard(self):
        tasks = [task("T1", tests="none", gate="quick"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests: none com Gate: quick - incoerente")
        self.assertWarn(out, "T1: Tests: none - confirme contra a Matriz")

    def test_integration_with_gate_quick_is_hard(self):
        tasks = [task("T1", tests="unit, e2e", gate="quick"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests com integration/e2e exige Gate: full, veio quick")

    def test_tests_none_with_gate_build_is_accepted(self):
        tasks = [task("T1", tests="none", gate="build"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)


class DoneCriteriaTest(LintTasksBase):
    def test_no_checkbox_is_hard(self):
        tasks = [task("T1", done=["x"]).replace("  - [ ] x", "  - x"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Pronto quando sem criterios '- [ ]'")

    def test_only_structural_criteria_is_warn(self):
        tasks = [task("T1", done=["Gate passa: `dotnet test`", "Build verde", "Contagem de testes: +2"]),
                 task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)
        self.assertWarn(out, "T1: criterios so estruturais; exit 0 nao prova regra de negocio")
        self.assertEqual(code, 0)


class CoverageAndPlanTest(LintTasksBase):
    def test_correction_task_in_map_does_not_diverge_from_plan(self):
        tasks = [task("T1"), task("T2", deps="T1"), task("T3", deps="T2")]
        tc = task("TC1", deps="T3").replace("### TC1: Criar coisa TC1", "### TC1: Corrigir coisa")
        body = doc(tasks, extra="## Mapa de execução\n\n```\nFase 1: T1 → T2\nFase 2: T3\nCorreção: TC1\n```\n\n## Tasks de correção\n\n" + tc)
        code, out = self.run_lint(body)
        self.assertNotIn("Mapa de execucao diverge", out)
        self.assertNoHard(out)

    def test_refactor_delta_serves_as_coverage_source(self):
        refactor = self.write("refactor.md", """\
<!-- sdd: spec-delta | tier: medium | capability: reservation-book/reservation-lifecycle | no-behavior-change -->
# Refactor

## Contexto (Context)

Invariantes preservados: RSV-07 e RSV-09. Objetivo: extrair a policy de lote.
""")
        tasks = [task("T1", req="RSV-07"), task("T2", deps="T1", req="RSV-09"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=refactor)
        self.assertNotIn("INCOMPLETO", out)
        self.assertNoHard(out)
        tasks = [task("T1", req="RSV-07"), task("T2", deps="T1", req="RSV-99"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=refactor)
        self.assertHard(out, "task referencia RSV-99, que o delta de refactor nao lista como invariante")
        self.assertIn("invariante RSV-09 do refactor sem task", out)

    def test_refactor_invariants_use_the_delta_prefix_only(self):
        refactor = self.write("refactor.md", """\
<!-- sdd: spec-delta | tier: medium | capability: reservation-book/reservation-lifecycle | no-behavior-change -->
# Refactor

| | |
|---|---|
| **Status** | Rascunho |
| **Prefixo** | RSV |

## Contexto (Context)

Invariantes preservados: RSV-07 [BOOK-03] e RSV-09 [BOOK-04], hash SHA-256 conforme ADR-0001.
""")
        tasks = [task("T1", req="RSV-07"), task("T2", deps="T1", req="RSV-09"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=refactor)
        self.assertNoHard(out)
        self.assertNotIn("invariante BOOK-03", out)
        self.assertNotIn("invariante ADR-0001", out)
        tasks = [task("T1", req="BOOK-03"), task("T2", deps="T1", req="RSV-09"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=refactor)
        self.assertHard(out, "task referencia BOOK-03, que o delta de refactor nao lista como invariante")

    def test_refactor_invariants_come_only_from_contexto(self):
        refactor = self.write("refactor.md", """\
<!-- sdd: spec-delta | tier: medium | capability: reservation-book/reservation-lifecycle | no-behavior-change -->
# Refactor

| | |
|---|---|
| **Prefixo** | RSV |

## Contexto (Context)

Invariantes preservados: RSV-07.

## Perguntas em aberto

RSV-11 pode ser afetado? Dono: produto.
""")
        tasks = [task("T1", req="RSV-07"), task("T2", deps="T1", req="RSV-07"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=refactor)
        self.assertNoHard(out)
        self.assertNotIn("invariante RSV-11", out)
        tasks = [task("T1", req="RSV-07"), task("T2", deps="T1", req="RSV-11"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=refactor)
        self.assertHard(out, "task referencia RSV-11, que o delta de refactor nao lista como invariante")

    def test_flag_with_added_requirements_keeps_normal_coverage(self):
        flagged = self.write("flagged.md", SPEC.replace("<!-- sdd: spec | tier: large | capability: reservation -->",
                                                        "<!-- sdd: spec-delta | tier: large | capability: reservation | no-behavior-change -->")
                             + "- **RSV-08** — WHEN x THEN the system SHALL y\n")
        tasks = [task("T1", req="RSV-07"), task("T2", deps="T1", req="RSV-07"), task("T3", deps="T2", req="RSV-07")]
        code, out = self.run_lint(doc(tasks), spec=flagged)
        self.assertHard(out, "requisito RSV-08 da spec sem task")

    def test_missing_tasks_file_is_usage_not_traceback(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_tasks.main(["lint_tasks.py", os.path.join(self.dir, "nope.md"), "--spec", self.spec])
            except SystemExit as e:
                code = e.code
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


class TemplateRegressionTest(LintTasksBase):
    """O template de references/tasks.md, com T2 minima e tabelas preenchidas,
    linta sem HARD. O plano e o mapa do template citam T3-T5 sem corpo; o
    harness reduz ambos a T1 -> T2 para lintar o que existe."""

    def template(self):
        with open(TASKS_MD, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"## Template: `changes/NNNN-<feature-slug>/tasks\.md`\s*\n`{3,4}markdown\n(.*?)\n`{3,4}\n\n---",
                      text, re.DOTALL)
        self.assertIsNotNone(m, "bloco de template nao encontrado em references/tasks.md")
        return m.group(1)

    def test_template_with_minimal_t2_is_clean(self):
        tpl = self.template()
        t2 = task("T2", deps="T1", req="RSV-07", commit="feat(bookbuilding): add reservation policy")
        tpl = tpl.replace("### T2: …\n", t2)
        tpl = tpl.replace("[gerada na seção 2]",
                          "| Camada | Tipo de teste | Expectativa de cobertura | Padrão de localização | Comando |\n"
                          "|---|---|---|---|---|\n" + MATRIX)
        tpl = tpl.replace("[gerados na seção 2]",
                          "| Gate | Quando | Comando |\n|---|---|---|\n" + GATES)
        tpl = re.sub(r"## Plano de execução\n.*?(?=\n## Tasks)",
                     "## Plano de execução\n\n### Fase 1: Domínio\nT1 → T2\n", tpl, flags=re.DOTALL)
        tpl = re.sub(r"## Mapa de execução\n\n```\n.*?```", "## Mapa de execução\n\n```\nFase 1: T1 → T2\n```",
                     tpl, flags=re.DOTALL)
        spec = self.write("spec.md", SPEC + "- **RSV-08** — WHEN amount is not a lot multiple THEN the system SHALL reject\n")
        code, out = self.run_lint(tpl, spec=spec)
        self.assertNoHard(out)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
