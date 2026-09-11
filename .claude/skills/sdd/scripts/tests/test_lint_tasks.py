"""Testes do lint_tasks.py: comentario de maquina, paragrafo "Como este
repositorio testa", Comandos de Gate (nomes de linha fechados, com a linha
de mutacao opcional, mas obrigatoria quando a tabela Riscos e tecnicas do
design lista um dos tres riscos que a exigem), plano e fases (a ultima task de cada
fase com `Gate: build`), campos por task e sua sincronia com
references/tasks.md, `O quê` com 'e' (dois entregaveis sao duas tasks),
`Pronto quando` (o comando do gate da task e criterio de comportamento), Tests/Gate
(a regra do campo `Gate`, com `Tests: none` silencioso na camada de config e
schema), dependencias,
Rastreabilidade (obrigatoria e coerente com os campos `Requisito`), cobertura
contra a spec viva (com e sem `scope:`) e prosa (placeholder, hedging,
meta-narracao e tag fora da convencao).

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

GATES = """\
| Quick | `Gate: quick` | `dotnet test tests/Domain.Tests` |
| Full | `Gate: full` | `dotnet test` |
| Build | `Gate: build` | `dotnet build && dotnet test` |"""
# Comando que cada gate declara em GATES: `Pronto quando` leva o do gate da task.
GATE_CMD = {"quick": "dotnet test tests/Domain.Tests", "full": "dotnet test",
            "build": "dotnet build && dotnet test"}
PLAN = "### Fase 1: Dominio\nT1 → T2\n\n### Fase 2: Adapters\nT3"
INTRO = ("Como este repositorio testa: xUnit em `tests/`, `dotnet test` na raiz. "
         "O gate Build executa 212 testes antes desta mudanca.")

SPEC = """\
<!-- sdd: spec | capability: reservation-book/reservation-lifecycle -->
# Spec

Prefixo dos requisitos: `RSV`.

## Contexto

c

## Requisitos

- **RSV-07** — WHEN amount < lot THEN the system SHALL reject with MIN_LOT_NOT_MET
"""


def task(tid, deps="nenhuma", req="RSV-07", tests="unit", gate="quick", done=None, extra="",
         gate_cmd=None):
    done = done or ["`Create` rejeita valor abaixo do lote com `MinLotNotMet`",
                    f"Gate passa: `{gate_cmd or GATE_CMD.get(gate, GATE_CMD['quick'])}`"]
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
{extra}
"""


TASK_HEADING = re.compile(r"^### (TC?\d+):", re.MULTILINE)
REQUIREMENT_FIELD = re.compile(r"^- \*\*Requisito:\*\* (.*)$", re.MULTILINE)


def auto_trace(bodies):
    """Rastreabilidade coerente com os campos `Requisito` das tasks dadas: a
    secao e obrigatoria, e cada doc() de teste precisa da sua."""
    rows = {}
    for body in re.split(r"(?=^### TC?\d+:)", bodies, flags=re.MULTILINE):
        head = TASK_HEADING.search(body)
        field = REQUIREMENT_FIELD.search(body)
        if not head or not field:
            continue
        for rid in re.findall(r"\b[A-Z][A-Z0-9]{1,9}-\d{2,}\b", field.group(1)):
            rows.setdefault(rid, []).append(head.group(1))
    body = "".join(f"| {rid} | {', '.join(tids)} |\n" for rid, tids in rows.items())
    return f"\n## Rastreabilidade\n\n| Requisito | Tasks |\n|---|---|\n{body}"


def doc(tasks=None, plan=PLAN, gates=GATES, extra="", comment="<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->", intro=INTRO, trace=None):
    if tasks is None:
        tasks = [task("T1"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
    if trace is None:
        trace = "" if "Rastreabilidade" in extra else auto_trace("".join(tasks) + extra)
    return f"""{comment}
# Coisa — Tasks

{intro}

## Comandos de Gate

| Gate | Quando | Comando |
|---|---|---|
{gates}

## Plano de execução

{plan}

## Tasks

{"".join(tasks)}
{extra}
{trace}"""


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

    def assertWarn(self, out, fragment):
        self.assertTrue(any(fragment in l for l in self.findings(out, "WARN")),
                        f"esperava WARN com '{fragment}'; saida:\n{out}")


class ValidDocumentTest(LintTasksBase):
    def test_valid_tasks_pass(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_higher_number_in_same_phase_is_accepted(self):
        tasks = [task("T1"), task("T2", deps="T3", gate="build"), task("T3", deps="T1")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T3 → T2"))
        self.assertNoHard(out)

    def test_no_matrix_map_commit_or_tier_required(self):
        code, out = self.run_lint(doc())
        for word in ("Matriz", "Mapa", "Commit", "tier", "Validação"):
            self.assertNotIn(word, out)


class MachineCommentTest(LintTasksBase):
    def test_missing_or_wrong_kind_is_hard(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: design | spec: ../spec.md -->"))
        self.assertHard(out, "primeira linha deve ser <!-- sdd: tasks")

    def test_missing_spec_field_is_hard(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: tasks | design: ./design.md -->"))
        self.assertHard(out, "sem 'spec:'")

    def test_design_field_is_optional(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: tasks | spec: ../spec.md -->"))
        self.assertNoHard(out)


class DuplicateIdTest(LintTasksBase):
    def test_duplicate_task_id_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T1", gate="build"), task("T2", deps="T1", gate="build")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2"))
        self.assertHard(out, "ID de task duplicado: T2")


class DependencyTest(LintTasksBase):
    def test_missing_dependency_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T9"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: depende de T9, que nao existe")

    def test_cycle_is_hard_with_ids(self):
        tasks = [task("T1", deps="T2"), task("T2", deps="T1", gate="build"), task("T3")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2 → T3"))
        self.assertHard(out, "ciclo de dependencia: T1 -> T2 -> T1")

    def test_dependency_on_later_phase_is_hard(self):
        tasks = [task("T1", deps="T3"), task("T2", deps="T1", gate="build"), task("T3")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1 (fase 1) depende de T3 (fase 2) - dependencia para fase posterior")

    def test_dependency_on_later_task_of_the_same_phase_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T3"), task("T3", deps="T1")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2 → T3"))
        self.assertEqual(code, 1)
        self.assertHard(out, "T2 depende de T3, que vem depois dele na fase 1 do Plano de execucao")

    def test_higher_number_without_phase_is_hard(self):
        tasks = [task("T1", deps="T2"), task("T2"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks, plan="T1, T2, T3"))
        self.assertHard(out, "T1: depende de T2 (numero maior ou igual")

    def test_t_depending_on_tc_is_hard(self):
        tasks = [task("T1"), task("T2", deps="TC1"), task("T3", deps="T2", gate="build"), task("TC1", deps="T1")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: depende de TC1 - task de correcao nasce no Verify")


class ExecutionPlanTest(LintTasksBase):
    def test_missing_plan_is_hard(self):
        code, out = self.run_lint(doc().replace("## Plano de execução", "## Ordem"))
        self.assertHard(out, "secao ausente: ## Plano de execução")

    def test_plan_citing_missing_task_is_hard(self):
        code, out = self.run_lint(doc(plan="### Fase 1: X\nT1 → T2 → T9\n\n### Fase 2: Y\nT3"))
        self.assertHard(out, "Plano de execucao cita T9, que nao existe")

    def test_task_outside_plan_is_hard(self):
        code, out = self.run_lint(doc(plan="### Fase 1: X\nT1 → T2"))
        self.assertHard(out, "T3: nao aparece no Plano de execucao")

    def test_correction_tasks_stay_outside_plan(self):
        code, out = self.run_lint(doc(extra="## Tasks de correção\n\n" + task("TC1", deps="T3")))
        self.assertNoHard(out)
        code, out = self.run_lint(doc(extra="## Tasks de correção\n\n" + task("TC1", deps="T3", gate="nope")))
        self.assertHard(out, "TC1: Gate invalido")


class PhaseGateTest(LintTasksBase):
    """A ultima task de cada fase do Plano de execucao leva `Gate: build`."""

    def test_last_task_of_every_phase_with_build_passes(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_last_task_of_a_phase_without_build_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T1"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertEqual(code, 1)
        self.assertHard(out, "T2: ultima task da fase 1 com Gate: quick - a ultima task de cada "
                             "fase leva Gate: build")
        self.assertNotIn("T3: ultima task", out)

    def test_task_that_does_not_close_a_phase_keeps_its_own_gate(self):
        tasks = [task("T1", tests="unit, integration", gate="full"),
                 task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_last_task_of_the_phase_follows_the_plan_order(self):
        """Fecha a fase quem vem por ultimo no plano, nao quem tem o maior numero."""
        tasks = [task("T1"), task("T2", deps="T3"), task("T3", deps="T1", gate="build")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T3 → T2"))
        self.assertHard(out, "T2: ultima task da fase 1 com Gate: quick")
        self.assertNotIn("T3: ultima task", out)


class TestsGateRuleTest(LintTasksBase):
    """Regra do campo `Gate` (references/tasks.md, Campos): `unit` sozinho
    exige `quick`, `integration`/`e2e` exigem `full`, `none` exige `build`; a
    ultima task de cada fase exige `build` em qualquer caso."""

    def three(self, first):
        return [first, task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]

    def test_unit_with_gate_quick_passes(self):
        code, out = self.run_lint(doc(self.three(task("T1", tests="unit", gate="quick"))))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_unit_with_gate_full_is_hard(self):
        code, out = self.run_lint(doc(self.three(task("T1", tests="unit", gate="full"))))
        self.assertEqual(code, 1)
        self.assertHard(out, "T1: Tests: unit exige Gate: quick, veio full")

    def test_unit_with_gate_build_outside_the_end_of_a_phase_is_hard(self):
        code, out = self.run_lint(doc(self.three(task("T1", tests="unit", gate="build"))))
        self.assertHard(out, "T1: Tests: unit exige Gate: quick, veio build - so a ultima task "
                             "da fase leva build")

    def test_integration_with_gate_build_outside_the_end_of_a_phase_is_hard(self):
        code, out = self.run_lint(doc(self.three(task("T1", tests="integration", gate="build"))))
        self.assertHard(out, "T1: Tests com integration/e2e exige Gate: full, veio build")

    def test_integration_with_gate_full_passes(self):
        code, out = self.run_lint(doc(self.three(task("T1", tests="integration", gate="full"))))
        self.assertNoHard(out)

    def test_tests_none_with_gate_full_is_hard(self):
        code, out = self.run_lint(doc(self.three(task("T1", tests="none", gate="full"))))
        self.assertHard(out, "T1: Tests: none com Gate: full - incoerente")

    def test_last_task_of_a_phase_keeps_build_with_any_tests(self):
        """A ultima task da fase leva build mesmo com `Tests: unit` ou
        `integration`: e a unica excecao a regra."""
        tasks = [task("T1"), task("T2", deps="T1", gate="build"),
                 task("T3", deps="T2", tests="integration", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_correction_task_follows_the_rule(self):
        """`TCn` fica fora do plano e, por isso, nunca fecha fase: vale a regra
        do `Tests`."""
        extra = "## Tasks de correção\n\n" + task("TC1", deps="T3", tests="unit", gate="build")
        code, out = self.run_lint(doc(extra=extra))
        self.assertHard(out, "TC1: Tests: unit exige Gate: quick, veio build")


class GateTableTest(LintTasksBase):
    def test_missing_gate_table_is_hard(self):
        code, out = self.run_lint(doc().replace("## Comandos de Gate", "## Gates"))
        self.assertHard(out, "secao ausente: ## Comandos de Gate")

    def test_empty_gate_table_is_hard(self):
        code, out = self.run_lint(doc(gates=""))
        self.assertHard(out, "secao Comandos de Gate sem linhas de dados")

    def test_empty_command_cell_is_hard(self):
        code, out = self.run_lint(doc(gates="| Quick | unit |  |\n| Build | fase | `dotnet build` |"))
        self.assertHard(out, "Comandos de Gate: celula de comando vazia")

    def test_gate_used_without_command_row_is_hard(self):
        code, out = self.run_lint(doc(gates="| Build | fase | `dotnet build` |"))
        self.assertHard(out, "Gate 'quick' usado em T1 sem linha na tabela Comandos de Gate")

    def test_gate_row_match_is_case_insensitive(self):
        tasks = [task("T1", gate_cmd="dotnet test"),
                 task("T2", deps="T1", gate="build", gate_cmd="dotnet build"),
                 task("T3", deps="T2", gate="build", gate_cmd="dotnet build")]
        code, out = self.run_lint(doc(tasks, gates="| QUICK | `Gate: quick` | `dotnet test` |\n"
                                                   "| build | `Gate: build` | `dotnet build` |"))
        self.assertNoHard(out)

    def test_row_name_outside_the_closed_list_is_hard(self):
        gates = (GATES + "\n| Smoke | quando der | `dotnet test --filter Smoke` |")
        code, out = self.run_lint(doc(gates=gates))
        self.assertEqual(code, 1)
        self.assertHard(out, "Comandos de Gate: linha 'smoke' fora dos nomes aceitos")

    def test_mutation_row_is_accepted(self):
        """A linha `Mutação` e opcional e e onde o comando de mutacao da
        mudanca fica declarado (references/tasks.md, Registro no tasks.md)."""
        gates = GATES + "\n| Mutação | a mudança declara mutação | `dotnet stryker` |"
        code, out = self.run_lint(doc(gates=gates))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_mutation_row_without_command_is_hard(self):
        gates = GATES + "\n| Mutação | a mudança declara mutação |  |"
        code, out = self.run_lint(doc(gates=gates))
        self.assertHard(out, "Comandos de Gate: celula de comando vazia")

    def test_mutation_is_not_a_task_gate(self):
        tasks = [task("T1", tests="none", gate="mutação"),
                 task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        gates = GATES + "\n| Mutação | a mudança declara mutação | `dotnet stryker` |"
        code, out = self.run_lint(doc(tasks, gates=gates))
        self.assertHard(out, "T1: Gate invalido: deve ser quick|full|build")


class TestingIntroTest(LintTasksBase):
    def test_missing_paragraph_is_hard(self):
        code, out = self.run_lint(doc(intro="Mudanca sem design; a estrutura esta nas tasks."))
        self.assertEqual(code, 1)
        self.assertHard(out, "paragrafo 'Como este repositorio testa' ausente antes de ## Comandos de Gate")

    def test_paragraph_after_the_gate_table_does_not_count(self):
        code, out = self.run_lint(doc(intro="", extra=INTRO))
        self.assertHard(out, "paragrafo 'Como este repositorio testa' ausente antes de ## Comandos de Gate")

    def test_paragraph_without_test_count_is_hard(self):
        code, out = self.run_lint(doc(intro="Como este repositorio testa: xUnit em `tests/`, `dotnet test` na raiz."))
        self.assertHard(out, "paragrafo 'Como este repositorio testa' sem a contagem-base do gate Build")

    def test_count_in_another_line_of_the_paragraph_counts(self):
        intro = ("Como este repositório testa: xUnit em `tests/`.\n"
                 "O gate Build executa 212 testes antes desta mudança.")
        code, out = self.run_lint(doc(intro=intro))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_english_paragraph_and_count_are_accepted(self):
        intro = "How this repository tests: xUnit under `tests/`. The Build gate runs 212 tests before this change."
        code, out = self.run_lint(doc(intro=intro))
        self.assertNoHard(out)
        self.assertEqual(code, 0)


class TraceabilityTest(LintTasksBase):
    @staticmethod
    def trace(rows):
        body = "".join(f"| {rid} | {tids} |\n" for rid, tids in rows)
        return f"\n## Rastreabilidade\n\n| Requisito | Tasks |\n|---|---|\n{body}"

    def test_absent_section_is_hard(self):
        code, out = self.run_lint(doc(trace=""))
        self.assertEqual(code, 1)
        self.assertHard(out, "secao ausente: ## Rastreabilidade")

    def test_coherent_table_passes(self):
        code, out = self.run_lint(doc(extra=self.trace([("RSV-07", "T1, T2, T3")])))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_task_citing_requirement_outside_the_table_is_hard(self):
        code, out = self.run_lint(doc(extra=self.trace([("RSV-07", "T1, T2")])))
        self.assertEqual(code, 1)
        self.assertHard(out, "Rastreabilidade: T3 cita RSV-07 sem linha na tabela que ligue os dois")

    def test_row_listing_a_task_that_does_not_cite_it_is_hard(self):
        code, out = self.run_lint(doc(extra=self.trace([("RSV-07", "T1, T2, T3"), ("RSV-08", "T2")])))
        self.assertHard(out, "Rastreabilidade: RSV-08 lista T2, que nao cita esse requisito no campo Requisito")

    def test_row_listing_a_task_that_does_not_exist_is_hard(self):
        code, out = self.run_lint(doc(extra=self.trace([("RSV-07", "T1, T2, T3, T9")])))
        self.assertHard(out, "Rastreabilidade: RSV-07 lista T9, que nao existe na lista de tasks")


class FieldsTest(LintTasksBase):
    def test_duplicate_field_is_hard(self):
        tasks = [task("T1", extra="- **Tests:** unit"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: campo duplicado: tests")

    def test_missing_empty_and_invalid_are_distinct(self):
        tasks = [task("T1", tests=""), task("T2", deps="T1", tests="fuzz"), task("T3", deps="T2", gate="build")]
        content = doc(tasks).replace("- **Tests:** unit\n- **Gate:** build\n\n", "- **Gate:** build\n\n", 1)
        code, out = self.run_lint(content)
        self.assertHard(out, "T1: campo vazio: tests")
        self.assertHard(out, "T2: Tests invalido: tipo(s) invalido(s): 'fuzz'")
        self.assertHard(out, "T3: campo obrigatorio ausente: tests")

    def test_missing_interfaces_is_hard(self):
        block = "- **Interfaces:**\n  - Consome: `Money`\n  - Produz: `Thing.Create(Money m): Result<Thing>`\n"
        code, out = self.run_lint(doc().replace(block, "", 1))
        self.assertEqual(code, 1)
        self.assertHard(out, "T1: campo obrigatorio ausente: interfaces")
        code, out = self.run_lint(doc())
        self.assertNoHard(out)

    def test_where_without_path_is_warn(self):
        content = doc().replace("- **Onde:** `src/Domain/ThingT1.cs`; `tests/Domain.Tests/ThingT1Tests.cs`", "- **Onde:** no dominio", 1)
        code, out = self.run_lint(content)
        self.assertWarn(out, "T1: Onde sem path de arquivo reconhecivel")

    def test_tests_list_of_valid_types_is_accepted(self):
        tasks = [task("T1", tests="unit, integration", gate="full"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_none_in_list_is_rejected(self):
        tasks = [task("T1", tests="none, unit"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests invalido: 'none' so sozinho")

    def test_tests_none_with_gate_quick_is_hard(self):
        tasks = [task("T1", tests="none", gate="quick"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests: none com Gate: quick - incoerente")
        self.assertWarn(out, "T1: Tests: none")

    def test_integration_with_gate_quick_is_hard(self):
        tasks = [task("T1", tests="unit, e2e", gate="quick"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests com integration/e2e exige Gate: full, veio quick")

    def test_tests_none_with_gate_build_is_accepted(self):
        tasks = [task("T1", tests="none", gate="build"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_placeholder_is_warn(self):
        tasks = [task("T1", done=["similar à T3", "Gate passa: `dotnet test tests/Domain.Tests`"]),
                 task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "placeholder")


class ProseAndTagsTest(LintTasksBase):
    """O executor le a task como instrucao: hedging e meta-narracao sao WARN e
    tag fora da convencao e HARD, como na spec e no design."""

    def with_prose(self, text):
        return doc(extra=f"\n{text}\n")

    def test_hedging_is_warn_not_hard(self):
        code, out = self.run_lint(self.with_prose("O registro talvez precise de migration."))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "hedging lexical")

    def test_meta_narration_is_warn_not_hard(self):
        code, out = self.run_lint(self.with_prose("Este documento lista as tasks."))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "meta-narracao")

    def test_declarative_prose_is_silent(self):
        code, out = self.run_lint(self.with_prose("O registro no modulo entra na T2."))
        warns = [l for l in out.splitlines() if l.startswith("WARN")]
        self.assertFalse([l for l in warns if "hedging" in l or "meta-narracao" in l], out)

    def test_rejected_tag_is_hard(self):
        code, out = self.run_lint(self.with_prose("[FATO] a migration ja existe."))
        self.assertEqual(code, 1)
        self.assertHard(out, "tag fora da convencao: [FATO]")

    def test_allowed_tags_pass(self):
        code, out = self.run_lint(self.with_prose("[PREMISSA] a migration roda no deploy."))
        self.assertNoHard(out)

    def test_value_reduced_to_an_ellipsis_is_warn(self):
        code, out = self.run_lint(self.with_prose("- Estrutura: …"))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "valor reduzido a reticencias")


class DoneWhenTest(LintTasksBase):
    def rest(self):
        return [task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]

    def test_behaviour_and_gate_pass(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_without_gate_command_is_hard(self):
        tasks = [task("T1", done=["`Create` rejeita valor abaixo do lote com `MinLotNotMet`",
                                  "Testes verdes"])] + self.rest()
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Pronto quando sem o comando do gate entre crases")

    def test_only_gate_command_is_hard(self):
        tasks = [task("T1", done=["Gate passa: `dotnet test tests/Domain.Tests`",
                                  "Build passa: `dotnet build FundDistributionPlatform.slnx`"])] + self.rest()
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Pronto quando so com comando de gate")

    def test_empty_done_block_is_hard(self):
        items = ("  - [ ] `Create` rejeita valor abaixo do lote com `MinLotNotMet`\n"
                 "  - [ ] Gate passa: `dotnet test tests/Domain.Tests`\n")
        code, out = self.run_lint(doc().replace(items, "", 1))
        self.assertHard(out, "T1: Pronto quando sem item")

    def test_identifier_code_span_is_not_a_command(self):
        """`Result<Thing>` e `Create` sao identificadores: sem o comando do
        gate a task nao passa, mesmo com crase em todo item."""
        tasks = [task("T1", done=["`Create` devolve `Result<Thing>` com o valor preservado",
                                  "`PartialReservation.Create` rejeita abaixo do minimo"])] + self.rest()
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Pronto quando sem o comando do gate entre crases")

    def test_single_word_command_declared_in_gate_table_counts(self):
        tasks = [task("T1", done=["`Create` rejeita valor abaixo do lote", "Gate passa: `pytest`"],
                      tests="unit", gate="quick"),
                 task("T2", deps="T1", gate="build", gate_cmd="pytest && ruff check"),
                 task("T3", deps="T2", gate="build", gate_cmd="pytest && ruff check")]
        gates = "| Quick | `Gate: quick` | `pytest` |\n| Build | `Gate: build` | `pytest && ruff check` |"
        code, out = self.run_lint(doc(tasks, gates=gates))
        self.assertNoHard(out)

    def test_command_of_another_gate_is_hard(self):
        """O comando tem de ser o do gate da task: o do Build numa task `quick`
        prova o gate errado."""
        tasks = [task("T1", gate="quick", gate_cmd="dotnet build && dotnet test")] + self.rest()
        code, out = self.run_lint(doc(tasks))
        self.assertEqual(code, 1)
        self.assertHard(out, "T1: Pronto quando com comando que nao e o do gate quick - escreva "
                             "`dotnet test tests/Domain.Tests`, a linha quick da tabela Comandos de Gate")

    def test_same_command_with_other_spacing_and_case_counts(self):
        tasks = [task("T1", gate="quick", gate_cmd="DOTNET  test   tests/Domain.Tests")] + self.rest()
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_prose_code_span_without_a_declared_executable_is_not_a_command(self):
        """`reserva ativa` e prosa entre crases: duas palavras minusculas nao
        fazem um comando."""
        tasks = [task("T1", done=["grava a `reserva ativa` no livro (RSV-07)",
                                  "`Create` devolve `Result<Thing>`"])] + self.rest()
        code, out = self.run_lint(doc(tasks))
        self.assertEqual(code, 1)
        self.assertHard(out, "T1: Pronto quando sem o comando do gate entre crases "
                             "(ex.: Gate passa: `dotnet test tests/Domain.Tests`)")

    def test_checked_items_are_accepted_like_unchecked(self):
        done = ["`Create` rejeita valor abaixo do lote com `MinLotNotMet`",
                "Gate passa: `dotnet test tests/Domain.Tests`"]
        content = doc([task("T1", done=done), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")])
        code, out = self.run_lint(content.replace("- [ ]", "- [x]"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)


class WhatConjunctionTest(LintTasksBase):
    """`O quê` com 'e' fora de crases soma dois entregaveis, e dois
    entregaveis sao duas tasks; teste e registro do mesmo entregavel nao
    contam."""

    WHAT = "- **O quê:** value object com validacao de lote"

    def what(self, text):
        tasks = [task("T1"), task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        return self.run_lint(doc(tasks).replace(self.WHAT, f"- **O quê:** {text}", 1))

    def test_two_deliverables_is_warn(self):
        code, out = self.what("value object com validacao de lote e endpoint de registro")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "T1: O que com 'e': dois entregaveis sao duas tasks")

    def test_tests_and_registration_of_the_same_deliverable_are_silent(self):
        for text in ("value object com validacao de lote e seus testes unitarios",
                     "value object com validacao de lote e seu teste de contrato",
                     "endpoint de registro e seu registro no modulo"):
            code, out = self.what(text)
            self.assertEqual(code, 0, out)
            self.assertNotIn("O que com 'e'", out)

    def test_other_possessive_is_not_exempt(self):
        code, out = self.what("value object com validacao de lote e sua migration")
        self.assertWarn(out, "T1: O que com 'e'")

    def test_conjunction_inside_backticks_is_ignored(self):
        code, out = self.what("value object `Quantity e Limits` do dominio")
        self.assertEqual(code, 0, out)
        self.assertNotIn("O que com 'e'", out)


class ConfigLayerTest(LintTasksBase):
    """`Tests: none` na camada de config, schema ou migration nao pede
    confirmacao: o default forte manda so o gate Build nela."""

    WHERE = "- **Onde:** `src/Domain/ThingT1.cs`; `tests/Domain.Tests/ThingT1Tests.cs`"

    def where(self, paths):
        tasks = [task("T1", tests="none", gate="build").replace(self.WHERE, f"- **Onde:** {paths}", 1),
                 task("T2", deps="T1", gate="build"), task("T3", deps="T2", gate="build")]
        return self.run_lint(doc(tasks))

    def test_config_schema_and_migration_paths_are_silent(self):
        for paths in ("`src/AppHost/appsettings.json`",
                      "`.github/workflows/ci.yml`; `src/Directory.Packages.props`",
                      "`src/Offering/Offering.csproj`; `db/schema/offer.sql`",
                      "`src/DataMigration/migrations/0004_add_offer.cs`"):
            code, out = self.where(paths)
            self.assertEqual(code, 0, out)
            self.assertNotIn("Tests: none", out)

    def test_code_path_still_warns(self):
        code, out = self.where("`src/Domain/Thing.cs`; `src/AppHost/appsettings.json`")
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "T1: Tests: none - confirme que a camada nao exige teste")


class CoverageTest(LintTasksBase):
    def test_missing_spec_flag_is_hard(self):
        code, out = self.run_lint(doc(), spec=None)
        self.assertHard(out, "--spec obrigatorio")

    def test_nonexistent_spec_is_hard(self):
        code, out = self.run_lint(doc(), spec=os.path.join(self.dir, "nope.md"))
        self.assertHard(out, "spec nao encontrada")

    def test_requirement_without_task_is_hard(self):
        spec = self.write("spec2.md", SPEC + "- **RSV-08** — WHEN y THEN the system SHALL z\n")
        code, out = self.run_lint(doc(), spec=spec)
        self.assertHard(out, "requisito RSV-08 da spec sem task")

    def test_task_citing_unknown_requirement_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T1", req="RSV-99"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: requisito RSV-99 nao existe na spec")

    def test_task_without_requirement_id_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T1", req="refactor interno"), task("T3", deps="T2", gate="build")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: Requisito sem ID")

    def test_scope_narrows_coverage(self):
        spec = self.write("spec2.md", SPEC + "- **RSV-08** — WHEN y THEN the system SHALL z\n"
                                             "- **RSV-09** — WHEN w THEN the system SHALL v\n")
        scoped = doc(comment="<!-- sdd: tasks | spec: ../spec.md | scope: RSV-07 -->")
        code, out = self.run_lint(scoped, spec=spec)
        self.assertNoHard(out)
        code, out = self.run_lint(doc(comment="<!-- sdd: tasks | spec: ../spec.md | scope: RSV-07, RSV-08 -->"), spec=spec)
        self.assertHard(out, "requisito RSV-08 da spec sem task")
        self.assertNotIn("RSV-09", out)

    def test_scope_with_unknown_id_is_hard(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: tasks | spec: ../spec.md | scope: RSV-07, RSV-42 -->"))
        self.assertHard(out, "scope: RSV-42 nao existe na spec")

    def test_spec_without_requirements_is_hard(self):
        empty = self.write("empty.md", "<!-- sdd: spec | capability: x/y -->\n# S\n\nPrefixo dos requisitos: `RSV`.\n\n## Contexto\n\nc\n\n## Requisitos\n\n")
        code, out = self.run_lint(doc(), spec=empty)
        self.assertHard(out, "sem requisitos em ## Requisitos")

    def test_missing_tasks_file_is_usage_not_traceback(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_tasks.main(["lint_tasks.py", os.path.join(self.dir, "nope.md"), "--spec", self.spec])
            except SystemExit as e:
                code = e.code
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err.getvalue())

    def test_commit_options_are_gone(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_tasks.main(["lint_tasks.py", self.write("t.md", doc()), "--spec", self.spec, "--commit-no-scope"])
            except SystemExit as e:
                code = e.code
        self.assertEqual(code, 2)
        self.assertIn("opcao desconhecida", err.getvalue())


class MutationRowTest(LintTasksBase):
    """Risco de dinheiro, seguranca ou concorrencia na tabela Riscos e tecnicas
    do design obriga a linha `Mutação` na tabela Comandos de Gate
    (references/verify.md, Mutação)."""

    MUTATION_ROW = "\n| Mutação | a mudança declara mutação | `dotnet stryker` |"

    def design(self, risk, name="design.md"):
        return self.write(name, "<!-- sdd: design | spec: ../spec.md -->\n# Coisa — Design\n\n"
                                "## Riscos e técnicas\n\n"
                                "| Risco | Fonte | Técnica | Onde |\n|---|---|---|---|\n"
                                f"| {risk} | RSV-07 | Idempotency key persistida | `Service` |\n")

    def test_risk_without_mutation_row_is_hard(self):
        self.design("Concorrência, duplicata, retry")
        code, out = self.run_lint(doc())
        self.assertEqual(code, 1)
        self.assertHard(out, "Comandos de Gate sem a linha Mutação")
        self.assertHard(out, "Concorrência, duplicata, retry")

    def test_risk_with_mutation_row_passes(self):
        self.design("Concorrência, duplicata, retry")
        code, out = self.run_lint(doc(gates=GATES + self.MUTATION_ROW))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_each_closed_name_is_hard_with_its_connectors(self):
        for risk in ("Dinheiro, cálculo financeiro", "Dinheiro e cálculo financeiro",
                     "Segurança, dado regulado", "Concorrência, duplicata e retry"):
            with self.subTest(risk=risk):
                self.design(risk)
                code, out = self.run_lint(doc())
                self.assertHard(out, "Comandos de Gate sem a linha Mutação")

    def test_risk_outside_the_closed_list_does_not_require_the_row(self):
        self.design("Duplicata por retry do canal")
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_design_option_overrides_the_machine_comment(self):
        self.design("Performance")
        other = self.design("Segurança, dado regulado", name="outro.md")
        code, out = self.run_lint(doc(), "--design", other)
        self.assertHard(out, "Comandos de Gate sem a linha Mutação")

    def test_nonexistent_design_option_is_hard(self):
        code, out = self.run_lint(doc(), "--design", os.path.join(self.dir, "nope.md"))
        self.assertHard(out, "design nao encontrado")

    def test_change_without_design_is_not_checked(self):
        code, out = self.run_lint(doc(comment="<!-- sdd: tasks | spec: ../spec.md -->"))
        self.assertNoHard(out)
        self.assertNotIn("Mutação", out)

    def test_declared_design_that_does_not_resolve_is_warn(self):
        code, out = self.run_lint(doc())
        self.assertWarn(out, "design do comentario de maquina nao encontrado")
        self.assertNoHard(out)


class MutationRisksInSyncWithReferencesTest(unittest.TestCase):
    """Os tres riscos de MUTATION_RISKS sao os nomes de linha da tabela de
    references/design.md, Do risco à técnica, e os mesmos que
    references/verify.md, Mutação lista. Doc e script divergentes fariam o
    linter exigir mutacao por risco que a referencia nao nomeia."""

    @staticmethod
    def read(name):
        with open(os.path.join(os.path.dirname(SCRIPTS), "references", name), encoding="utf-8") as f:
            return f.read()

    def test_names_are_rows_of_the_design_table(self):
        rows = set()
        for l in self.read("design.md").splitlines():
            if l.strip().startswith("|"):
                rows.add(tuple(lint_tasks.risk_tokens(l.strip().strip("|").split("|")[0])))
        for name in lint_tasks.MUTATION_RISKS:
            self.assertIn(name, rows, f"risco {name} sem linha na tabela de references/design.md")

    def test_names_appear_in_the_mutation_section_of_verify(self):
        text = self.read("verify.md")
        start = text.index("## Mutação")
        stream = " ".join(lint_tasks.risk_tokens(text[start:]))
        for name in lint_tasks.MUTATION_RISKS:
            self.assertIn(" ".join(name), stream,
                          f"risco {name} ausente de references/verify.md, Mutação")


class TemplateRegressionTest(LintTasksBase):
    """O template de references/tasks.md, com a T2 elidida preenchida, linta
    sem HARD contra uma spec com os IDs que ele cita."""

    def template(self):
        with open(TASKS_MD, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"## Template\b[^\n]*\n+`{3,4}markdown\n(.*?)\n`{3,4}\n", text, re.DOTALL)
        self.assertIsNotNone(m, "bloco de template nao encontrado em references/tasks.md")
        return m.group(1)

    @staticmethod
    def row_command(tpl, gate):
        """Comando que a tabela Comandos de Gate do template declara para um
        gate: e ele que `Pronto quando` tem de repetir."""
        for l in tpl.splitlines():
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if l.strip().startswith("|") and len(cells) == 3 and cells[0].lower() == gate.lower():
                m = re.search(r"`([^`]+)`", cells[2])
                return m.group(1) if m else cells[2]
        return ""

    @staticmethod
    def traced(tpl, tid):
        """Requisitos que a Rastreabilidade do template atribui a `tid`: a T2
        elidida cita o que a tabela ja diz que ela atende."""
        out = []
        for l in tpl.splitlines():
            if not l.strip().startswith("|"):
                continue
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cells) == 2 and re.fullmatch(r"RSV-\d{2}", cells[0]) and tid in re.findall(r"\bTC?\d+\b", cells[1]):
                out.append(cells[0])
        return out

    def test_template_is_clean(self):
        tpl = self.template()
        ids = sorted(set(re.findall(r"\bRSV-\d{2}\b", tpl)))
        self.assertTrue(ids, "template sem IDs RSV")
        spec = self.write("spec.md", SPEC.replace("- **RSV-07** — WHEN amount < lot THEN the system SHALL reject with MIN_LOT_NOT_MET\n",
                                                  "".join(f"- **{r}** — WHEN x THEN the system SHALL y\n" for r in ids)))
        t2 = self.traced(tpl, "T2")
        self.assertTrue(t2, "Rastreabilidade do template nao atribui requisito a T2")
        build = self.row_command(tpl, "Build")
        self.assertTrue(build, "template sem comando na linha Build de Comandos de Gate")
        # T2 fecha a Fase 1 do plano do template: Gate build, com o comando que
        # a linha Build da tabela do proprio template declara.
        tpl = re.sub(r"### T2: …\n(?:<!--.*?-->\n)?",
                     task("T2", deps="T1", req=", ".join(t2), tests="unit", gate="build",
                          gate_cmd=build), tpl)
        code, out = self.run_lint(tpl, spec=spec)
        self.assertNoHard(out)
        self.assertEqual(code, 0)


class FieldsInSyncWithReferenceTest(unittest.TestCase):
    """Os campos da tabela de references/tasks.md, Campos, sao os que o parser
    conhece, na mesma ordem. Doc e script divergentes fazem o linter cobrar um
    campo que a referencia nao manda escrever, ou ignorar um que ela manda."""

    @staticmethod
    def documented():
        with open(TASKS_MD, encoding="utf-8") as f:
            lines = f.read().splitlines()
        start = next(i for i, l in enumerate(lines) if l.strip() == "### Campos")
        end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
        out = []
        for l in lines[start:end]:
            if not l.strip().startswith("|"):
                continue
            cell = l.strip().strip("|").split("|")[0].strip().strip("*").strip()
            if cell and cell != "Campo" and not re.fullmatch(r":?-{2,}:?", cell):
                out.append(cell.lower())
        return out

    def test_names_and_order_match(self):
        names = self.documented()
        self.assertTrue(names, "tabela de campos nao encontrada em references/tasks.md")
        self.assertEqual(names, [lint_tasks.FIELDS[key][0] for key in lint_tasks.REQUIRED_FIELDS])


if __name__ == "__main__":
    unittest.main()
