import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import skills_gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


class ParseUnittestTest(unittest.TestCase):
    def test_ok_tail(self):
        out = "....\n----\nRan 4 tests in 0.010s\n\nOK\n"
        self.assertEqual(skills_gate.parse_unittest(out),
                         {"ran": 4, "failures": 0, "errors": 0, "skipped": 0})

    def test_failed_with_counts(self):
        out = "Ran 10 tests in 1.000s\n\nFAILED (failures=2, errors=1)\n"
        counts = skills_gate.parse_unittest(out)
        self.assertEqual((counts["ran"], counts["failures"], counts["errors"]), (10, 2, 1))

    def test_ok_with_skips_is_counted(self):
        out = "Ran 3 tests in 0.1s\n\nOK (skipped=1)\n"
        self.assertEqual(skills_gate.parse_unittest(out)["skipped"], 1)

    def test_no_tail_counts_as_error(self):
        counts = skills_gate.parse_unittest("Traceback (most recent call last)\nImportError: x\n")
        self.assertEqual(counts["errors"], 1)


class ParseLintTest(unittest.TestCase):
    def test_sums_every_summary_line(self):
        out = "lint_spec: 0 HARD, 5 WARN em a.md.\nlint_spec: 1 HARD, 2 WARN em b.md.\n"
        self.assertEqual(skills_gate.parse_lint(out), (1, 7))

    def test_no_summary_is_zero(self):
        self.assertEqual(skills_gate.parse_lint("OK  5 bloco(s) mermaid"), (0, 0))


class SlnxMissingTest(unittest.TestCase):
    SLNX = ('<Folder Name="/src/"><Project Path="src/App/App.csproj" /></Folder>'
            '<Folder Name="/docs/"><File Path="docs/a.md" /></Folder>')

    def test_listed_file_and_project_sources_are_covered(self):
        tracked = ["docs/a.md", "src/App/App.csproj", "src/App/Program.cs", "X.slnx"]
        self.assertEqual(skills_gate.slnx_missing(self.SLNX, tracked, "X.slnx"), [])

    def test_unlisted_file_is_reported(self):
        tracked = ["docs/a.md", "docs/b.md"]
        self.assertEqual(skills_gate.slnx_missing(self.SLNX, tracked, "X.slnx"), ["docs/b.md"])


class ReadmeScriptsTest(unittest.TestCase):
    def test_missing_script_is_reported(self):
        readme = "python3 .claude/skills/prd/scripts/seq.py check docs/prd\n"
        scripts = [".claude/skills/prd/scripts/seq.py", ".claude/skills/prd/scripts/lint_prd.py"]
        self.assertEqual(skills_gate.scripts_without_readme_command(readme, scripts),
                         [".claude/skills/prd/scripts/lint_prd.py"])


class ChecksDocumentationTest(unittest.TestCase):
    """A tabela de GATE.md, a docstring e a lista CHECKS descrevem os mesmos checks com os mesmos limites."""

    def test_gate_md_table_matches_checks(self):
        text = (ROOT / ".claude/skills/GATE.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| `([a-z-]+)` \| .+? \| (.+?) \|$", text, re.MULTILINE)
        self.assertEqual([(c.id, c.threshold) for c in skills_gate.CHECKS], rows)

    def test_docstring_lists_every_check_with_its_threshold(self):
        doc = skills_gate.__doc__
        for check in skills_gate.CHECKS:
            line = next((ln for ln in doc.splitlines() if ln.strip().startswith(check.id + " ")), None)
            self.assertIsNotNone(line, check.id)
            self.assertTrue(line.rstrip().endswith(check.threshold), (check.id, line))

    def test_list_output_has_every_check(self):
        listing = skills_gate.list_checks()
        for check in skills_gate.CHECKS:
            self.assertIn(check.id, listing)
            self.assertIn(check.threshold, listing)

    def test_ids_are_unique(self):
        ids = [c.id for c in skills_gate.CHECKS]
        self.assertEqual(len(ids), len(set(ids)))


class MainTest(unittest.TestCase):
    @staticmethod
    def run_main(argv):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return skills_gate.main(argv)

    def test_list_exits_zero(self):
        self.assertEqual(self.run_main(["--list"]), 0)

    def test_unknown_check_is_usage_error(self):
        self.assertEqual(self.run_main(["--only", "nope"]), 2)

    def test_only_runs_a_cheap_check(self):
        self.assertEqual(self.run_main(["--only", "entities"]), 0)


if __name__ == "__main__":
    unittest.main()
