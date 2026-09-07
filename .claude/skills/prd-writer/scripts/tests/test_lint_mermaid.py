"""Tests for lint_mermaid.py.

Run:  python -m unittest discover -s <skill-dir>/scripts -p "test_lint_mermaid.py"
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import lint_mermaid  # noqa: E402


def extract(text):
    blocks, problems = lint_mermaid.extract_blocks_from_text(text)
    return [(line, body) for _, line, body in blocks], [line for line, _ in problems]


class ExtractionTests(unittest.TestCase):
    def test_simple_block_with_line_number(self):
        blocks, problems = extract("# T\n\ntexto\n\n```mermaid\nflowchart TD\n A-->B\n```\n")
        self.assertEqual(blocks, [(5, "flowchart TD\n A-->B")])
        self.assertEqual(problems, [])

    def test_nested_in_four_backtick_outer_fence(self):
        text = "````markdown\n# PRD\n\n```mermaid\nflowchart TD\n A-->B\n```\n\ntexto\n````\n"
        blocks, problems = extract(text)
        self.assertEqual(blocks, [(4, "flowchart TD\n A-->B")])
        self.assertEqual(problems, [])

    def test_four_backtick_mermaid_not_closed_by_three(self):
        blocks, problems = extract("````mermaid\nflowchart TD\n A-->B\n```\n````\n")
        self.assertEqual(blocks, [(1, "flowchart TD\n A-->B\n```")])
        self.assertEqual(problems, [])

    def test_unclosed_fence_is_problem(self):
        blocks, problems = extract("```mermaid\nflowchart TD\n A-->B\n")
        self.assertEqual(problems, [1])
        self.assertEqual(len(blocks), 1)

    def test_closer_with_trailing_text_does_not_close(self):
        blocks, problems = extract("```mermaid\nflowchart TD\n``` x\n")
        self.assertEqual(problems, [1])
        self.assertEqual(blocks[0][1], "flowchart TD\n``` x")

    def test_multiple_blocks_different_fence_sizes(self):
        text = ("```mermaid\nA\n```\n\n~~~~mermaid\nB\n~~~~\n\n`````mermaid\nC\n`````\n"
                "\n```mermaid\nD\n````\n")
        blocks, problems = extract(text)
        self.assertEqual(blocks, [(1, "A"), (5, "B"), (9, "C"), (13, "D")])
        self.assertEqual(problems, [])

    def test_tildes_case_insensitive_and_spaces(self):
        blocks, problems = extract("~~~  MERMAID\nflowchart TD\n~~~\n")
        self.assertEqual(blocks, [(1, "flowchart TD")])
        self.assertEqual(problems, [])

    def test_tildes_do_not_close_backticks(self):
        blocks, problems = extract("```mermaid\nflowchart TD\n~~~\n```\n")
        self.assertEqual(blocks, [(1, "flowchart TD\n~~~")])
        self.assertEqual(problems, [])

    def test_non_mermaid_fence_ignored(self):
        text = "```python\nprint(1)\n```\n\n```\nplain\n```\n\n```mermaid\nA\n```\n"
        blocks, problems = extract(text)
        self.assertEqual(blocks, [(9, "A")])
        self.assertEqual(problems, [])

    def test_no_blocks(self):
        self.assertEqual(extract("# so texto\n\n```sh\nls\n```\n"), ([], []))


class ParserUnavailableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "doc.md")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("```mermaid\nflowchart TD\n A-->B\n```\n\n```mermaid\nflowchart TD\n C-->D\n```\n")
        self.marker = os.path.join(self.tmp.name, "nope", "package.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_check_files_returns_hard_per_block(self):
        with mock.patch.object(lint_mermaid, "PARSER_MARKER", self.marker), \
                mock.patch.object(lint_mermaid.subprocess, "run") as run:
            findings, n = lint_mermaid.check_files([self.path])
            run.assert_not_called()
        self.assertEqual(n, 2)
        self.assertEqual([(p, line) for p, line, _ in findings], [(self.path, 1), (self.path, 6)])
        for _, _, msg in findings:
            self.assertIn("parser indisponivel", msg)
            self.assertIn("--setup", msg)

    def test_main_exit_3_and_never_installs(self):
        out = io.StringIO()
        with mock.patch.object(lint_mermaid, "PARSER_MARKER", self.marker), \
                mock.patch.object(lint_mermaid.subprocess, "run") as run, \
                contextlib.redirect_stdout(out):
            code = lint_mermaid.main(["lint_mermaid.py", self.path])
            run.assert_not_called()
        self.assertEqual(code, 3)
        self.assertEqual(out.getvalue().count("HARD  "), 2)

    def test_main_exit_0_without_blocks_even_if_parser_missing(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("# sem diagrama\n")
        out = io.StringIO()
        with mock.patch.object(lint_mermaid, "PARSER_MARKER", self.marker), \
                contextlib.redirect_stdout(out):
            self.assertEqual(lint_mermaid.main(["lint_mermaid.py", self.path]), 0)

    def test_unavailable_findings_carry_incompleto_prefix(self):
        with mock.patch.object(lint_mermaid, "PARSER_MARKER", self.marker):
            findings, _ = lint_mermaid.check_files([self.path])
        for _, _, msg in findings:
            self.assertTrue(msg.startswith("INCOMPLETO: "), msg)

    def test_parser_abort_is_exit_3_not_diagram_hard(self):
        """node e node_modules existem, mas o processo do parser aborta:
        validacao incompleta (exit 3), nao diagrama invalido (exit 1)."""
        aborted = mock.Mock(returncode=1, stdout="", stderr="Error: Cannot find module 'jsdom'")
        out = io.StringIO()
        with mock.patch.object(lint_mermaid, "ensure_parser", return_value=None), \
                mock.patch.object(lint_mermaid.subprocess, "run", return_value=aborted), \
                contextlib.redirect_stdout(out):
            code = lint_mermaid.main(["lint_mermaid.py", self.path])
        self.assertEqual(code, 3, out.getvalue())
        self.assertIn("INCOMPLETO: bloco mermaid 1 NAO validado", out.getvalue())
        self.assertIn("--setup", out.getvalue())

    def test_missing_path_is_usage(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = lint_mermaid.main(["lint_mermaid.py", os.path.join(self.tmp.name, "nope.md")])
        self.assertEqual(code, 2)
        self.assertIn("path inexistente", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_unknown_flag_is_usage(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = lint_mermaid.main(["lint_mermaid.py", "--bogus"])
        self.assertEqual(code, 2)
        self.assertIn("opcao desconhecida", err.getvalue())

    def test_unclosed_fence_is_hard_without_parser(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("```mermaid\nflowchart TD\n A-->B\n")
        with mock.patch.object(lint_mermaid, "PARSER_MARKER", self.marker):
            findings, n = lint_mermaid.check_files([self.path])
        self.assertEqual(n, 1)
        self.assertEqual(findings, [(self.path, 1, "fence mermaid sem fechamento")])


@unittest.skipUnless(lint_mermaid.parser_available(), "parser mermaid nao instalado")
class RealParserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, text):
        p = os.path.join(self.tmp.name, "doc.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def test_valid_block_passes(self):
        p = self._write("````markdown\n```mermaid\nflowchart TD\n A-->B\n```\n````\n")
        findings, n = lint_mermaid.check_files([p])
        self.assertEqual((findings, n), ([], 1))

    def test_invalid_block_fails_with_line(self):
        p = self._write("# T\n\n```mermaid\nsequenceDiagram\n  participant OFF as Offering\n"
                        "  participant Book\n  OFF->>Book: x\n```\n")
        findings, n = lint_mermaid.check_files([p])
        self.assertEqual(n, 1)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][:2], (p, 3))
        self.assertIn("bloco mermaid 1:", findings[0][2])

    def test_main_exit_1_on_invalid(self):
        p = self._write("```mermaid\nflowchart TD\n  A --> B{\"x\" --> C\n```\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lint_mermaid.main(["lint_mermaid.py", p]), 1)

    def test_self_test_passes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lint_mermaid.self_test(), 0)


if __name__ == "__main__":
    unittest.main()
