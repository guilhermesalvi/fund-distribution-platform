"""Regression checks for task gate contracts and the runnable PRD example."""

from pathlib import Path
import importlib.util
import re
import unittest
import uuid

from check_repository import ROOT, check_task_gates


TASKS = """## Gate Commands

| Gate | When | Command |
|---|---|---|
| quick | T1 | `python verify.py` |

## Tasks

### T1: Verify a rule
- **Done when:**
  - [ ] Result matches the rule.
  - [ ] `python verify.py`
- **Tests:** unit
- **Gate:** quick
"""


class GateContracts(unittest.TestCase):
    def test_valid_task_and_fenced_example(self):
        for text in (TASKS, f"```markdown\n{TASKS}\n```"):
            self.assertEqual([], check_task_gates(text))

    def test_case_sensitive_gate_name(self):
        findings = check_task_gates(TASKS.replace("| quick |", "| Quick |"))
        self.assertIn("unknown gate Quick", findings)
        self.assertIn("T1: undeclared gate quick", findings)

    def test_command_from_another_gate_is_rejected(self):
        text = TASKS.replace("  - [ ] `python verify.py`", "  - [ ] `python other.py`")
        self.assertIn("T1: Done when does not contain its gate command", check_task_gates(text))

    def test_duplicate_and_empty_commands(self):
        text = TASKS.replace("| quick | T1 | `python verify.py` |", "| quick | T1 | `python verify.py` |\n| quick | T2 | |")
        findings = check_task_gates(text)
        self.assertIn("duplicate gate quick", findings)
        self.assertIn("empty command for quick", findings)

    def test_mutation_is_not_a_task_gate(self):
        text = TASKS.replace("quick", "Mutation")
        self.assertIn("T1: invalid task gate Mutation", check_task_gates(text))


class PrdExample(unittest.TestCase):
    def test_complete_example_and_broken_reference(self):
        path = ROOT / ".claude/skills/prd/scripts/check_prd.py"
        spec = importlib.util.spec_from_file_location("check_prd", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = (ROOT / ".claude/skills/prd/references/example.md").read_text(encoding="utf-8")
        block = re.search(r"^````markdown\n(.*?)^````$", source, re.M | re.S)
        self.assertIsNotNone(block)
        artifacts = (ROOT / "artifacts").resolve()
        if not artifacts.is_relative_to(ROOT):
            raise RuntimeError("Test artifacts must remain inside the repository")
        artifacts.mkdir(exist_ok=True)
        folder = artifacts / f"prd-contract-{uuid.uuid4().hex}"
        folder.mkdir()
        example = folder / "0001-customer-onboarding-document-verification.md"
        try:
            example.write_text(block[1], encoding="utf-8")
            self.assertEqual([], module.check(folder))
            example.write_text(block[1] + "\nReferência ausente: ONB-99.\n", encoding="utf-8")
            self.assertTrue(any("ONB-99 has no definition" in item for item in module.check(folder)))
        finally:
            example.unlink(missing_ok=True)
            folder.rmdir()


if __name__ == "__main__":
    unittest.main()
