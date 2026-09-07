"""Testes do lint_validation.py: veredito, consistencia e regras por tier.

Roda com:
    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_validation.py"
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
import lint_validation  # noqa: E402

VERIFY_MD = os.path.join(os.path.dirname(SCRIPTS), "references", "verify.md")

MC = "<!-- sdd: validation | change: 0001-partial-reservation | tier: {tier}{extra} -->"

CONFORMANCE_PASS = """\
| RSV-07 | rejeita com MIN_LOT_NOT_MET | `tests/PartialReservationTests.cs:41` — `result.Error.Should().Be(MinLotNotMet)` | ✅ PASS |
| RSV-08 | aceita lote | `tests/PartialReservationTests.cs:60` — `result.IsSuccess.Should().BeTrue()` | ✅ PASS |"""

CONFORMANCE_GAP = """\
| RSV-07 | rejeita com MIN_LOT_NOT_MET | `tests/PartialReservationTests.cs:41` — assertion nao mira o erro | ❌ GAP |
| RSV-08 | aceita lote | `tests/PartialReservationTests.cs:60` — `result.IsSuccess.Should().BeTrue()` | ✅ PASS |"""

SENSOR = """\
## Sensor de discriminação

| Mutação | Arquivo:linha | Testes rodados | Resultado |
|---|---|---|---|
| `>` → `>=` no lote mínimo | `src/Book.cs:57` | Quick | morto ✅ |
"""

SENSOR_SURVIVED = SENSOR.replace("morto ✅", "sobreviveu ❌")

DESIGN = """\
| Estrutura segue o design | ✅ | |
| Responsabilidades respeitadas | ✅ | |
| Interfaces batem com as assinaturas | ✅ | |
| Sem dependência fora do planejado | ✅ | |"""


def doc(verdict="PASS ✅", tier="large", conformance=CONFORMANCE_PASS,
        gate="Comando: `dotnet test` · Total 12 · Passou 12 · Falhou 0 · Pulou 0 · Contagem antes/depois: 10 → 12",
        sensor=SENSOR, design=DESIGN, gaps="Nenhum", extra_head="", mc_extra="", uat=""):
    parts = [
        MC.format(tier=tier, extra=mc_extra),
        "# Reserva Parcial — Validação",
        "",
        f"**Veredito:** {verdict}",
        extra_head,
        "**Verificador:** sub-agente fresco (independente)",
        "**Diff:** `abc..def` — 3 arquivos",
        "**Data:** 2026-09-06",
        "",
        "## Conformidade à spec",
        "",
        "| Requisito | Resultado da spec | `file:line` + assertion | Resultado |",
        "|---|---|---|---|",
        conformance,
        "",
        "## Gate Build",
        gate,
        "",
        sensor,
        "## Aderência ao design",
        "",
        "| Item | Status | Observação |",
        "|---|---|---|",
        design,
        "",
        "## Qualidade de código",
        "Nada a notar.",
        "",
        uat,
        "## Gaps (ordenados por severidade)",
        "",
        gaps,
        "",
        "## Iteração",
        "1 de 3",
    ]
    return "\n".join(p for p in parts if p is not None) + "\n"


class LintValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, content):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def run_lint(self, content, *args, name="validation.md"):
        path = self.write(name, content)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lint_validation.main(["lint_validation.py", path, *args])
        return code, out.getvalue()

    def assertHard(self, out, fragment):
        hard = [l for l in out.splitlines() if l.startswith("HARD")]
        self.assertTrue(any(fragment in l for l in hard),
                        f"esperava HARD com '{fragment}'; saida:\n{out}")

    def assertNoHard(self, out):
        hard = [l for l in out.splitlines() if l.startswith("HARD")]
        self.assertEqual(hard, [], f"nao esperava HARD; saida:\n{out}")

    # --- veredito ---------------------------------------------------------

    def test_pass_valid_exits_0(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_pass_with_gap_row_is_hard(self):
        code, out = self.run_lint(doc(conformance=CONFORMANCE_GAP))
        self.assertHard(out, "veredito PASS com sinal negativo: conformidade")
        self.assertEqual(code, 1)

    def test_pass_with_failed_2_is_hard(self):
        code, out = self.run_lint(doc(
            gate="Comando: `dotnet test` · Total 12 · Passou 10 · Falhou 2 · Pulou 0"))
        self.assertHard(out, "Falhou 2")
        self.assertEqual(code, 1)

    def test_not_pass_is_hard(self):
        code, out = self.run_lint(doc(verdict="NOT PASS"))
        self.assertHard(out, "Veredito fora do enum")
        self.assertEqual(code, 1)

    def test_pass_pipe_fail_is_hard(self):
        code, out = self.run_lint(doc(verdict="PASS ✅ | FAIL ❌"))
        self.assertHard(out, "Veredito fora do enum")
        self.assertEqual(code, 1)

    def test_fail_consistent_exits_1_with_message(self):
        code, out = self.run_lint(doc(
            verdict="FAIL ❌", conformance=CONFORMANCE_GAP,
            gate="Comando: `dotnet test` · Total 12 · Passou 11 · Falhou 1 · Pulou 0",
            gaps="1. Maior — RSV-07 sem assertion exata → task de correção TC1"))
        self.assertNoHard(out)
        self.assertEqual(code, 1)
        self.assertIn("mudanca NAO esta pronta", out)

    def test_fail_without_negative_signal_is_hard(self):
        code, out = self.run_lint(doc(verdict="FAIL ❌"))
        self.assertHard(out, "FAIL sem evidencia de falha")
        self.assertEqual(code, 1)

    def test_blocked_with_reason_exits_1_distinct_message(self):
        code, out = self.run_lint(doc(
            verdict="BLOCKED ⛔",
            extra_head="**Motivo do bloqueio:** gate nao executavel: SDK .NET ausente no ambiente"))
        self.assertNoHard(out)
        self.assertEqual(code, 1)
        self.assertIn("verificacao incompleta/bloqueada: gate nao executavel", out)
        self.assertNotIn("mudanca NAO esta pronta", out)

    def test_blocked_without_reason_is_hard(self):
        code, out = self.run_lint(doc(verdict="BLOCKED"))
        self.assertHard(out, "Motivo do bloqueio")
        self.assertEqual(code, 1)

    # --- comentario de maquina --------------------------------------------

    def test_missing_tier_is_hard(self):
        content = doc().replace(" | tier: large", "")
        code, out = self.run_lint(content)
        self.assertHard(out, "sem 'tier:")
        self.assertEqual(code, 1)

    def test_missing_change_is_hard(self):
        content = doc().replace(" | change: 0001-partial-reservation", "")
        code, out = self.run_lint(content)
        self.assertHard(out, "sem 'change:")
        self.assertEqual(code, 1)

    # --- sensor por tier ----------------------------------------------------

    def test_large_without_sensor_is_hard(self):
        code, out = self.run_lint(doc(tier="large", sensor=""))
        self.assertHard(out, "tier large: sensor de discriminacao ausente")
        self.assertEqual(code, 1)

    def test_medium_without_sensor_is_warn_only(self):
        code, out = self.run_lint(doc(tier="medium", sensor=""))
        self.assertNoHard(out)
        self.assertIn("WARN", out)
        self.assertIn("tier medium: sem sensor", out)
        self.assertEqual(code, 0)

    def test_small_without_sensor_is_clean(self):
        code, out = self.run_lint(doc(tier="small", sensor=""))
        self.assertNoHard(out)
        self.assertNotIn("sensor", out.lower().replace("sem --spec", ""))
        self.assertEqual(code, 0)

    def test_sensor_survivor_with_pass_is_hard(self):
        code, out = self.run_lint(doc(sensor=SENSOR_SURVIVED))
        self.assertHard(out, "mutante sobreviveu")
        self.assertEqual(code, 1)

    # --- conformidade -------------------------------------------------------

    def test_duplicate_requirement_ids_is_hard(self):
        dup = CONFORMANCE_PASS.replace("RSV-08", "RSV-07")
        code, out = self.run_lint(doc(conformance=dup))
        self.assertHard(out, "ID de requisito duplicado")
        self.assertEqual(code, 1)

    def test_row_with_wrong_column_count_is_hard(self):
        bad = CONFORMANCE_PASS + "\n| RSV-09 | aceita | ✅ PASS |"
        code, out = self.run_lint(doc(conformance=bad))
        self.assertHard(out, "3 colunas; esperado 4")

    def test_spec_with_omitted_id_is_hard(self):
        spec = self.write("spec.md", "\n".join([
            "<!-- sdd: spec-delta | tier: large | capability: reservation-book/x -->",
            "# Delta",
            "",
            "## ADDED Requirements",
            "",
            "- **RSV-07** — WHEN x THEN the system SHALL y",
            "- **RSV-08** — WHEN x THEN the system SHALL y",
            "- **RSV-09** — WHEN x THEN the system SHALL z",
            "",
            "## MODIFIED Requirements",
            "",
            "- **RSV-03** — WHEN a THEN the system SHALL b",
            "  Antes: WHEN a THEN the system SHALL c",
            "",
        ]))
        code, out = self.run_lint(doc(), "--spec", spec)
        self.assertHard(out, "requisito RSV-09 do delta")
        self.assertHard(out, "requisito RSV-03 do delta")
        self.assertEqual(code, 1)

    def test_spec_fully_covered_is_clean(self):
        spec = self.write("spec.md", "\n".join([
            "<!-- sdd: spec-delta | tier: large | capability: reservation-book/x -->",
            "## ADDED Requirements",
            "- **RSV-07** — WHEN x THEN the system SHALL y",
            "- **RSV-08** — WHEN x THEN the system SHALL y",
            "",
        ]))
        code, out = self.run_lint(doc(), "--spec", spec)
        self.assertNoHard(out)
        self.assertNotIn("nao verificada contra a spec", out)
        self.assertEqual(code, 0)

    def test_without_spec_warns(self):
        code, out = self.run_lint(doc())
        self.assertIn("WARN", out)
        self.assertIn("cobertura de requisitos nao verificada contra a spec", out)
        self.assertEqual(code, 0)

    # --- gate ---------------------------------------------------------------

    def test_skipped_2_without_justification_is_hard(self):
        code, out = self.run_lint(doc(
            gate="Comando: `dotnet test` · Total 12 · Passou 10 · Falhou 0 · Pulou 2 · Contagem antes/depois: 10 → 12"))
        self.assertHard(out, "Pulou 2 sem justificativa")
        self.assertEqual(code, 1)

    def test_skipped_2_with_justification_line_is_clean(self):
        code, out = self.run_lint(doc(
            gate="Comando: `dotnet test` · Total 12 · Passou 10 · Falhou 0 · Pulou 2\n"
                 "Pulados: 2 testes de integracao exigem Docker, ausente no ambiente de verificacao"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_total_0_with_pass_is_hard(self):
        code, out = self.run_lint(doc(
            gate="Comando: `dotnet test` · Total 0 · Passou 0 · Falhou 0 · Pulou 0"))
        self.assertHard(out, "Total 0")
        self.assertEqual(code, 1)

    def test_gate_without_numbers_is_hard(self):
        code, out = self.run_lint(doc(gate="Comando: `dotnet test` · tudo verde"))
        self.assertHard(out, "Gate Build sem numeros")

    def test_evidence_of_run_missing_command_is_hard(self):
        log = self.write("gate.log", "dotnet build\nBuild succeeded.\n")
        code, out = self.run_lint(doc(), "--evidence-of-run", log)
        self.assertHard(out, "--evidence-of-run nao contem o comando")
        self.assertEqual(code, 1)

    def test_evidence_of_run_with_command_is_clean(self):
        log = self.write("gate.log", "$ dotnet test\nPassed! - Failed: 0, Passed: 12\n")
        code, out = self.run_lint(doc(), "--evidence-of-run", log)
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    # --- aderencia ao design -----------------------------------------------

    def test_design_missing_with_na_because_is_ok(self):
        code, out = self.run_lint(doc(design="N/A porque design pulado (plano inline)"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_design_missing_without_na_because_is_hard(self):
        code, out = self.run_lint(doc(design=""))
        self.assertHard(out, "precisa de tabela ou 'N/A porque")

    def test_design_present_requires_4_items(self):
        self.write("design.md", "<!-- sdd: design | tier: large | spec: ./spec.md -->\n# Design\n")
        three = "\n".join(DESIGN.splitlines()[:3])
        code, out = self.run_lint(doc(design=three))
        self.assertHard(out, "tabela de aderencia com 3 itens; minimo 4")

    def test_design_present_with_4_items_is_clean(self):
        self.write("design.md", "<!-- sdd: design | tier: large | spec: ./spec.md -->\n# Design\n")
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_design_x_with_pass_is_hard(self):
        bad = DESIGN.replace("| Interfaces batem com as assinaturas | ✅ | |",
                             "| Interfaces batem com as assinaturas | ❌ | assinatura divergente |")
        code, out = self.run_lint(doc(design=bad))
        self.assertHard(out, "aderencia")
        self.assertEqual(code, 1)

    # --- UAT ----------------------------------------------------------------

    def test_uat_flag_without_section_is_hard(self):
        code, out = self.run_lint(doc(), "--uat")
        self.assertHard(out, "UAT obrigatorio")
        code, out = self.run_lint(doc(mc_extra=" | uat"))
        self.assertHard(out, "UAT obrigatorio")

    def test_uat_with_blocker_and_pass_is_hard(self):
        uat = "## UAT\n\n1. Teste 1: fluxo de reserva — ❌ Bloqueante: tela trava ao confirmar\n"
        code, out = self.run_lint(doc(uat=uat), "--uat")
        self.assertHard(out, "UAT L")
        self.assertEqual(code, 1)

    # --- regressao: template de verify.md ----------------------------------

    def test_template_from_verify_md_completed_as_pass_is_clean(self):
        with open(VERIFY_MD, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"```markdown\n(<!-- sdd: validation.*?)```", text, re.DOTALL)
        self.assertIsNotNone(m, "template de validation.md nao encontrado em verify.md")
        t = m.group(1)
        # completa o template como PASS valido, preservando a estrutura
        t = re.sub(r"^<!-- sdd: validation \| change: [^|>]+?\s*(\|[^>]*)?-->",
                   "<!-- sdd: validation | change: 0001-partial-reservation | tier: large -->",
                   t, count=1, flags=re.MULTILINE)
        t = re.sub(r"^\*\*Veredito:\*\*.*$", "**Veredito:** PASS ✅", t, flags=re.MULTILINE)
        t = re.sub(r"^\*\*Motivo do bloqueio:\*\*.*\n", "", t, flags=re.MULTILINE)
        t = t.replace("**Verificador:** sub-agente fresco (independente) | passada fresh-eyes do autor (independência parcial)",
                      "**Verificador:** sub-agente fresco (independente)")
        t = t.replace("**Diff:** `<base>..<head>` — N arquivos", "**Diff:** `abc..def` — 3 arquivos")
        t = t.replace("**Data:** AAAA-MM-DD", "**Data:** 2026-09-06")
        t = t.replace("| Requisito | Resultado da spec | `file:line` + assertion | Resultado |\n|---|---|---|---|\n",
                      "| Requisito | Resultado da spec | `file:line` + assertion | Resultado |\n|---|---|---|---|\n"
                      + CONFORMANCE_PASS + "\n")
        t = t.replace("N/N requisitos com evidência · M lacunas de precisão · K gaps",
                      "2/2 requisitos com evidência · 0 lacunas de precisão · 0 gaps")
        t = re.sub(r"^Comando: .*$",
                   "Comando: `dotnet test` · Total 12 · Passou 12 · Falhou 0 · Pulou 0 · Contagem antes/depois: 10 → 12",
                   t, flags=re.MULTILINE)
        t = t.replace("morto ✅ / sobreviveu ❌", "morto ✅")
        t = t.replace("| Item | Status | Observação |\n|---|---|---|\n",
                      "| Item | Status | Observação |\n|---|---|---|\n" + DESIGN + "\n")
        t = t.replace("[por arquivo, só o que falhou ou merece nota]", "Nada a notar.")
        t = t.replace("<!-- quando aplicável -->", "N/A: backend, sem comportamento user-facing.")
        t = re.sub(r"^1\. \[severidade\].*$", "Nenhum", t, flags=re.MULTILINE)
        code, out = self.run_lint(t)
        self.assertNoHard(out)
        self.assertEqual(code, 0, out)


class SourceAndReasonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def lint(self, content, *args):
        path = os.path.join(self.tmp.name, "validation.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lint_validation.main(["lint_validation.py", path, *args])
        return code, out.getvalue()

    def test_missing_spec_file_is_incomplete(self):
        code, out = self.lint(doc(), "--spec", os.path.join(self.tmp.name, "nope.md"))
        self.assertEqual(code, 1)
        self.assertTrue(any(l.startswith("HARD") and "INCOMPLETO" in l and "nao encontrado" in l
                            for l in out.splitlines()), out)

    def test_template_comment_is_not_a_blocking_reason(self):
        code, out = self.lint(doc(verdict="BLOCKED", extra_head="**Motivo do bloqueio:** <!-- só quando BLOCKED -->"))
        self.assertEqual(code, 1)
        self.assertTrue(any(l.startswith("HARD") and "Motivo do bloqueio" in l and "vazio" in l
                            for l in out.splitlines()), out)


class UsageTests(unittest.TestCase):
    def test_missing_file_is_usage_not_traceback(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_validation.main(["lint_validation.py", os.path.join(tempfile.gettempdir(), "nope-validation.md")])
            except SystemExit as e:
                code = e.code
        self.assertEqual(code, 2)
        self.assertIn("arquivo ilegivel", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())


if __name__ == "__main__":
    unittest.main()
