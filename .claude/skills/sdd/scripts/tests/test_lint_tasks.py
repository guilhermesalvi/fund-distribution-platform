"""Testes do lint_tasks.py: comentario de maquina, paragrafo "Como este
repositorio testa", Comandos de Gate, plano e fases, campos por task, `Pronto
quando` (comando do gate e criterio de comportamento), Tests/Gate,
dependencias, Rastreabilidade e cobertura contra a spec viva (com e sem
`scope:`).

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
| Quick | task com unit test | `dotnet test tests/Domain.Tests` |
| Full | task com integration/e2e | `dotnet test` |
| Build | ultima da fase; task sem teste | `dotnet build && dotnet test` |"""
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


def task(tid, deps="nenhuma", req="RSV-07", tests="unit", gate="quick", done=None, extra=""):
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
{extra}
"""


def doc(tasks=None, plan=PLAN, gates=GATES, extra="", comment="<!-- sdd: tasks | spec: ../spec.md | design: ./design.md -->", intro=INTRO):
    if tasks is None:
        tasks = [task("T1"), task("T2", deps="T1"), task("T3", deps="T2")]
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

    def assertWarn(self, out, fragment):
        self.assertTrue(any(fragment in l for l in self.findings(out, "WARN")),
                        f"esperava WARN com '{fragment}'; saida:\n{out}")


class ValidDocumentTest(LintTasksBase):
    def test_valid_tasks_pass(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_higher_number_in_same_phase_is_accepted(self):
        tasks = [task("T1"), task("T2", deps="T3"), task("T3", deps="T1")]
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
        tasks = [task("T1"), task("T2", deps="T1"), task("T2", deps="T1")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2"))
        self.assertHard(out, "ID de task duplicado: T2")


class DependencyTest(LintTasksBase):
    def test_missing_dependency_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T9"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: depende de T9, que nao existe")

    def test_cycle_is_hard_with_ids(self):
        tasks = [task("T1", deps="T2"), task("T2", deps="T1"), task("T3")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2 → T3"))
        self.assertHard(out, "ciclo de dependencia: T1 -> T2 -> T1")

    def test_dependency_on_later_phase_is_hard(self):
        tasks = [task("T1", deps="T3"), task("T2", deps="T1"), task("T3")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1 (fase 1) depende de T3 (fase 2) - dependencia para fase posterior")

    def test_dependency_on_later_task_of_the_same_phase_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T3"), task("T3", deps="T1")]
        code, out = self.run_lint(doc(tasks, plan="### Fase 1: X\nT1 → T2 → T3"))
        self.assertEqual(code, 1)
        self.assertHard(out, "T2 depende de T3, que vem depois dele na fase 1 do Plano de execucao")

    def test_higher_number_without_phase_is_hard(self):
        tasks = [task("T1", deps="T2"), task("T2"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks, plan="T1, T2, T3"))
        self.assertHard(out, "T1: depende de T2 (numero maior ou igual")

    def test_t_depending_on_tc_is_hard(self):
        tasks = [task("T1"), task("T2", deps="TC1"), task("T3", deps="T2"), task("TC1", deps="T1")]
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
        self.assertHard(out, "Gate 'quick' usado em T1, T2, T3 sem linha na tabela Comandos de Gate")

    def test_gate_row_match_is_case_insensitive(self):
        code, out = self.run_lint(doc(gates="| QUICK | unit | `dotnet test` |\n| build | fase | `dotnet build` |"))
        self.assertNoHard(out)


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

    def test_absent_section_is_not_checked(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)

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
        tasks = [task("T1", extra="- **Tests:** unit"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: campo duplicado: tests")

    def test_missing_empty_and_invalid_are_distinct(self):
        tasks = [task("T1", tests=""), task("T2", deps="T1", tests="fuzz"), task("T3", deps="T2")]
        content = doc(tasks).replace("- **Tests:** unit\n- **Gate:** quick\n\n", "- **Gate:** quick\n\n", 1)
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
        tasks = [task("T1", tests="unit, integration", gate="full"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_none_in_list_is_rejected(self):
        tasks = [task("T1", tests="none, unit"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests invalido: 'none' so sozinho")

    def test_tests_none_with_gate_quick_is_hard(self):
        tasks = [task("T1", tests="none", gate="quick"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests: none com Gate: quick - incoerente")
        self.assertWarn(out, "T1: Tests: none")

    def test_integration_with_gate_quick_is_hard(self):
        tasks = [task("T1", tests="unit, e2e", gate="quick"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T1: Tests com integration/e2e exige Gate: full, veio quick")

    def test_tests_none_with_gate_build_is_accepted(self):
        tasks = [task("T1", tests="none", gate="build"), task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertNoHard(out)

    def test_placeholder_is_warn(self):
        tasks = [task("T1", done=["similar à T3", "Gate passa: `dotnet test tests/Domain.Tests`"]),
                 task("T2", deps="T1"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "placeholder")


class DoneWhenTest(LintTasksBase):
    def rest(self):
        return [task("T2", deps="T1"), task("T3", deps="T2")]

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
                      tests="unit", gate="quick")] + self.rest()
        gates = "| Quick | task com unit test | `pytest` |\n| Build | fase | `pytest && ruff check` |"
        code, out = self.run_lint(doc(tasks, gates=gates))
        self.assertNoHard(out)

    def test_checked_items_are_accepted_like_unchecked(self):
        done = ["`Create` rejeita valor abaixo do lote com `MinLotNotMet`",
                "Gate passa: `dotnet test tests/Domain.Tests`"]
        content = doc([task("T1", done=done), task("T2", deps="T1"), task("T3", deps="T2")])
        code, out = self.run_lint(content.replace("- [ ]", "- [x]"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)


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
        tasks = [task("T1"), task("T2", deps="T1", req="RSV-99"), task("T3", deps="T2")]
        code, out = self.run_lint(doc(tasks))
        self.assertHard(out, "T2: requisito RSV-99 nao existe na spec")

    def test_task_without_requirement_id_is_hard(self):
        tasks = [task("T1"), task("T2", deps="T1", req="refactor interno"), task("T3", deps="T2")]
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
        tpl = re.sub(r"### T2: …\n(?:<!--.*?-->\n)?", task("T2", deps="T1", req=", ".join(t2)), tpl)
        code, out = self.run_lint(tpl, spec=spec)
        self.assertNoHard(out)
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
