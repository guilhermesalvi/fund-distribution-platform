"""Check router structure and destinations; this does not evaluate an LLM."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3] / ".agents/skills"
ROUTES = {
    "prd": {
        "Criar PRD": ("intake.md", "writing.md", "conventions.md", "workflow.md"),
        "Atualizar PRD": ("writing.md", "conventions.md", "workflow.md"),
        "Documentar o produto existente": ("modes.md",),
        "Plataforma": ("modes.md",),
    },
    "sdd": {entry: (reference,) for entry, reference in (
        ("Specify", "specify.md"), ("Design", "design.md"), ("Tasks", "tasks.md"),
        ("Execute", "execute.md"), ("Verify", "verify.md"), ("Retomar", "execute.md"),
    )},
}
NEW_REFERENCES = {"prd": ("workflow", "conventions", "prose"),
                  "sdd": ("workflow", "validation", "prose")}


def route_errors(text, routes):
    errors = []
    rows = [line for line in text.splitlines() if line.startswith("|")]
    for label, references in routes.items():
        matching = [row for row in rows if label in row]
        if not matching:
            errors.append(label)
        elif not any(all(ref in row for ref in references) for row in matching):
            errors.append(label + ": destination")
    return errors


class RoutingTest(unittest.TestCase):
    def test_skill_names_are_preserved(self):
        for skill in ROUTES:
            text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertRegex(text, rf"(?m)^name: {skill}$")

    def test_entry_tables_point_to_expected_references(self):
        for skill, routes in ROUTES.items():
            with self.subTest(skill=skill):
                text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertEqual(route_errors(text, routes), [])

    def test_missing_route_and_wrong_destination_fail(self):
        routes = {"Specify": ("specify.md",)}
        self.assertEqual(route_errors("| Specify | specify.md |", routes), [])
        self.assertTrue(route_errors("| Design | design.md |", routes))
        self.assertTrue(route_errors("| Specify | tasks.md |", routes))

    def test_new_references_are_discoverable(self):
        for skill, names in NEW_REFERENCES.items():
            text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            for name in names:
                self.assertTrue((ROOT / skill / "references" / f"{name}.md").is_file())
                self.assertIn(f"references/{name}.md", text)

    def test_routers_do_not_reference_the_other_package(self):
        for skill, other in (("prd", "sdd"), ("sdd", "prd")):
            text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertNotRegex(text, rf"skills/{other}\b|\.\./{other}/")


if __name__ == "__main__":
    unittest.main()
