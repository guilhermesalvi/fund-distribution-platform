"""Testes do lint_adr.py: titulo `# ADR NNNN: titulo`, linha `Participantes:`,
secoes obrigatorias na ordem do template e com conteudo, `Regras derivadas`
por ultimo, consequencia negativa, reciprocidade de `Substitui:` e
`Substituída por:`, placeholder e prosa, pasta e erros de uso.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_lint_adr.py"
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
import lint_adr  # noqa: E402

ADR_MD = os.path.join(os.path.dirname(SCRIPTS), "references", "adr.md")

TITLE = "# ADR 0007: Eventos de dominio saem por outbox transacional"
PARTICIPANTS = "Participantes: Ana (decisao); Bruno (consulta)."

CONTEXTO = "O servico publica no broker dentro da mesma transacao da escrita no banco."
DECISAO = "Toda publicacao passa por uma tabela de outbox lida por um worker."
ALTERNATIVAS = """\
| Alternativa | Por que rejeitada |
|---|---|
| Publicar direto no broker | Perde o evento quando a transacao falha |"""
CONSEQUENCIAS = """\
- Positivas: entrega ao menos uma vez sem transacao distribuida.
- Negativas: a latencia de publicacao sobe ate o intervalo do worker."""
REGRAS = "Outbox obrigatorio para evento de dominio (CLAUDE.md, Contextos)."

SECTIONS = [("Contexto", CONTEXTO), ("Decisão", DECISAO),
            ("Alternativas consideradas", ALTERNATIVAS), ("Consequências", CONSEQUENCIAS)]


def doc(sections=None, title=TITLE, header=PARTICIPANTS):
    if sections is None:
        sections = SECTIONS
    body = "".join(f"\n## {t}\n\n{text}\n" for t, text in sections)
    head = f"\n{header}\n" if header else "\n"
    return f"{title}\n{head}{body}"


class LintAdrBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = os.path.join(self.tmp.name, "docs", "adr")
        os.makedirs(self.folder)
        self.adr = os.path.join(self.folder, "0007-outbox.md")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def write(path, content):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        return path

    def run_lint(self, content, target=None):
        if content is not None:
            self.write(self.adr, content)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = lint_adr.main(["lint_adr.py", target or self.adr])
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


class ValidDocumentTest(LintAdrBase):
    def test_valid_adr_passes(self):
        code, out = self.run_lint(doc())
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_derived_rules_as_last_section_passes(self):
        code, out = self.run_lint(doc(SECTIONS + [("Regras derivadas", REGRAS)]))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_english_section_names_are_accepted(self):
        english = [("Context", CONTEXTO), ("Decision", DECISAO),
                   ("Alternatives considered", ALTERNATIVAS),
                   ("Consequences", CONSEQUENCIAS.replace("Negativas", "Negatives"))]
        code, out = self.run_lint(doc(english, header="Participants: Ana; Bruno."))
        self.assertNoHard(out)


class TitleTest(LintAdrBase):
    def test_title_without_adr_number_is_hard(self):
        code, out = self.run_lint(doc(title="# Eventos saem por outbox"))
        self.assertEqual(code, 1)
        self.assertHard(out, "titulo fora da forma `# ADR NNNN: titulo`")

    def test_title_without_text_is_hard(self):
        code, out = self.run_lint(doc(title="# ADR 0007:"))
        self.assertHard(out, "titulo fora da forma `# ADR NNNN: titulo`")

    def test_missing_h1_is_hard(self):
        code, out = self.run_lint(doc().replace(TITLE + "\n", ""))
        self.assertHard(out, "sem titulo H1")


class ParticipantsTest(LintAdrBase):
    def test_missing_participants_is_hard(self):
        code, out = self.run_lint(doc(header=""))
        self.assertEqual(code, 1)
        self.assertHard(out, "linha `Participantes:` ausente")

    def test_participants_without_name_is_hard(self):
        code, out = self.run_lint(doc(header="Participantes:"))
        self.assertHard(out, "linha `Participantes:` sem nome")

    def test_participants_after_the_first_section_is_hard(self):
        content = doc(header="").replace("\n## Contexto\n", f"\n## Contexto\n\n{PARTICIPANTS}\n")
        code, out = self.run_lint(content)
        self.assertHard(out, "linha `Participantes:` ausente")


class SectionsTest(LintAdrBase):
    def test_missing_section_is_hard(self):
        code, out = self.run_lint(doc([s for s in SECTIONS if s[0] != "Alternativas consideradas"]))
        self.assertEqual(code, 1)
        self.assertHard(out, "secao obrigatoria ausente: ## Alternativas consideradas")

    def test_section_out_of_order_is_hard(self):
        swapped = [SECTIONS[1], SECTIONS[0], SECTIONS[2], SECTIONS[3]]
        code, out = self.run_lint(doc(swapped))
        self.assertHard(out, "secao fora de ordem: 'Decisão' aparece antes de 'Contexto'")

    def test_empty_section_is_hard(self):
        code, out = self.run_lint(doc([("Contexto", "")] + SECTIONS[1:]))
        self.assertHard(out, "secao sem conteudo: Contexto")

    def test_section_reduced_to_a_negation_is_hard(self):
        code, out = self.run_lint(doc(SECTIONS + [("Regras derivadas", "Nenhuma.")]))
        self.assertHard(out, "secao sem conteudo: Regras derivadas")

    def test_derived_rules_before_the_end_is_hard(self):
        code, out = self.run_lint(doc(SECTIONS[:3] + [("Regras derivadas", REGRAS), SECTIONS[3]]))
        self.assertHard(out, "## Regras derivadas nao e a ultima secao")

    def test_heading_inside_fence_is_ignored(self):
        code, out = self.run_lint(doc() + "\n```markdown\n## Secao Inventada\n```\n")
        self.assertNoHard(out)


class NegativeConsequenceTest(LintAdrBase):
    def test_consequences_without_negative_line_is_hard(self):
        only_positive = "- Positivas: entrega ao menos uma vez sem transacao distribuida."
        code, out = self.run_lint(doc(SECTIONS[:3] + [("Consequências", only_positive)]))
        self.assertEqual(code, 1)
        self.assertHard(out, "sem linha `- Negativas: <texto>`")

    def test_negative_label_without_text_is_hard(self):
        empty_label = CONSEQUENCIAS.replace(
            "- Negativas: a latencia de publicacao sobe ate o intervalo do worker.", "- Negativas:")
        code, out = self.run_lint(doc(SECTIONS[:3] + [("Consequências", empty_label)]))
        self.assertHard(out, "sem linha `- Negativas: <texto>`")

    def test_bold_negative_label_is_accepted(self):
        bold = CONSEQUENCIAS.replace("- Negativas:", "- **Negativas:**")
        code, out = self.run_lint(doc(SECTIONS[:3] + [("Consequências", bold)]))
        self.assertNoHard(out)


class SupersedeTest(LintAdrBase):
    def setUp(self):
        super().setUp()
        self.old = os.path.join(self.folder, "0003-broker-direto.md")

    def old_adr(self, header):
        return doc(title="# ADR 0003: Eventos vao direto ao broker", header=header)

    def test_reciprocal_pair_passes(self):
        self.write(self.old, self.old_adr(f"{PARTICIPANTS}\nSubstituída por: 0007"))
        code, out = self.run_lint(doc(header=f"{PARTICIPANTS}\nSubstitui: 0003"))
        self.assertNoHard(out)
        self.assertEqual(code, 0)

    def test_supersedes_without_target_file_is_hard(self):
        code, out = self.run_lint(doc(header=f"{PARTICIPANTS}\nSubstitui: 0003"))
        self.assertEqual(code, 1)
        self.assertHard(out, "`Substitui: 0003` sem ADR 0003-*.md na mesma pasta")

    def test_supersedes_without_back_reference_is_hard(self):
        self.write(self.old, self.old_adr(PARTICIPANTS))
        code, out = self.run_lint(doc(header=f"{PARTICIPANTS}\nSubstitui: 0003"))
        self.assertHard(out, "sem reciproco: 0003-broker-direto.md nao tem `Substituída por: 0007`")

    def test_superseded_by_without_back_reference_is_hard(self):
        self.write(self.old, self.old_adr(PARTICIPANTS))
        content = doc(header=f"{PARTICIPANTS}\nSubstituída por: 0003")
        code, out = self.run_lint(content)
        self.assertHard(out, "sem reciproco: 0003-broker-direto.md nao tem `Substitui: 0007`")

    def test_superseded_by_with_back_reference_passes(self):
        self.write(self.old, self.old_adr(f"{PARTICIPANTS}\nSubstitui: 0007"))
        code, out = self.run_lint(doc(header=f"{PARTICIPANTS}\nSubstituída por: 0003"))
        self.assertNoHard(out)


class ProseTest(LintAdrBase):
    def test_placeholder_is_warn_not_hard(self):
        code, out = self.run_lint(doc([("Contexto", CONTEXTO + " TBD: o volume diario.")] + SECTIONS[1:]))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "placeholder")

    def test_hedging_is_warn_not_hard(self):
        code, out = self.run_lint(doc([("Contexto", "Talvez o broker perca eventos na falha.")] + SECTIONS[1:]))
        self.assertEqual(code, 0, out)
        self.assertWarn(out, "hedging lexical")

    def test_placeholder_inside_fence_is_ignored(self):
        contexto = CONTEXTO + "\n\n```text\nTODO no exemplo\n```"
        code, out = self.run_lint(doc([("Contexto", contexto)] + SECTIONS[1:]))
        self.assertEqual(self.findings(out, "WARN"), [], out)


class TemplateRegressionTest(LintAdrBase):
    """O template de references/adr.md, gravado como uma ADR da pasta, linta
    sem HARD."""

    def template(self):
        with open(ADR_MD, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r"### Template\b[^\n]*\n+`{3,4}markdown\n(.*?)\n`{3,4}\n", text, re.DOTALL)
        self.assertIsNotNone(m, "bloco de template nao encontrado em references/adr.md")
        return m.group(1)

    def test_template_is_clean(self):
        code, out = self.run_lint(self.template() + "\n")
        self.assertNoHard(out)
        self.assertEqual(code, 0)


class FolderTest(LintAdrBase):
    def test_folder_lints_every_numbered_file(self):
        self.write(self.adr, doc())
        self.write(os.path.join(self.folder, "0003-broker-direto.md"),
                   doc(SECTIONS[:3], title="# ADR 0003: Eventos vao direto ao broker"))
        code, out = self.run_lint(None, target=self.folder)
        self.assertEqual(code, 1)
        self.assertHard(out, "secao obrigatoria ausente: ## Consequências")
        self.assertIn("0007-outbox.md", out)

    def test_unnumbered_file_in_the_folder_is_ignored(self):
        self.write(self.adr, doc())
        self.write(os.path.join(self.folder, "README.md"), "# Nao e ADR\n")
        code, out = self.run_lint(None, target=self.folder)
        self.assertEqual(code, 0)
        self.assertNotIn("README.md", out)

    def test_empty_folder_is_not_a_failure(self):
        code, out = self.run_lint(None, target=self.folder)
        self.assertEqual(code, 0)
        self.assertIn("nenhuma ADR", out)


class UsageTest(LintAdrBase):
    def exit_code(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = lint_adr.main(["lint_adr.py", *argv])
            except SystemExit as e:
                code = e.code
        return code, err.getvalue()

    def test_unknown_option_is_usage(self):
        self.write(self.adr, doc())
        code, err = self.exit_code(self.adr, "--bogus")
        self.assertEqual(code, 2)
        self.assertIn("opcao desconhecida", err)

    def test_missing_file_is_usage_not_traceback(self):
        code, err = self.exit_code(os.path.join(self.folder, "nope.md"))
        self.assertEqual(code, 2)
        self.assertIn("arquivo ilegivel", err)
        self.assertNotIn("Traceback", err)

    def test_non_utf8_file_is_usage(self):
        with open(self.adr, "wb") as f:
            f.write(b"# ADR 0007: T\x97\n")
        code, err = self.exit_code(self.adr)
        self.assertEqual(code, 2)
        self.assertIn("UTF-8", err)


if __name__ == "__main__":
    unittest.main()
