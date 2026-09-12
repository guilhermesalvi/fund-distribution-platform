"""Verify discoverable editorial policy and examples, not writing quality."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3] / ".agents/skills"
HEADINGS = {"Convenções de escrita", "Texto de instruções", "Texto do artefato", "Checklist editorial"}
PROFILES = {
    "prd/references/writing.md": "Formas por seção",
    "sdd/references/specify.md": "Forma de escrita",
    "sdd/references/design.md": "Forma de escrita",
    "sdd/references/tasks.md": "Forma de escrita",
    "sdd/references/adr.md": "Forma de escrita",
    "sdd/references/execute.md": "Forma da comunicação",
    "sdd/references/verify.md": "Forma da comunicação",
}
EXAMPLES = ("prd/references/example.md", "sdd/references/specify.md",
            "sdd/references/design.md", "sdd/references/tasks.md",
            "sdd/references/adr.md", "sdd/references/verify.md")


def headings(text):
    return set(re.findall(r"^#{1,4} (.+)$", text, re.MULTILINE))


def fenced_blocks(text):
    """Respect fence length so nested examples remain inside their template."""
    opened = None
    body = []
    prefix = []
    for line in text.splitlines():
        marker = re.match(r"^(`{3,}|~{3,})(.*)$", line)
        if opened is None:
            if marker:
                opened = (marker[1][0], len(marker[1]), marker[2].strip())
                body = []
            else:
                prefix.append(line)
        elif (marker and marker[1][0] == opened[0]
              and len(marker[1]) >= opened[1] and not marker[2].strip()):
            yield opened[2], "\n".join(body), "\n".join(prefix)
            opened = None
            prefix = []
        else:
            body.append(line)


def editorial_link_resolves(text, documents):
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    for target in targets:
        name, _, anchor = target.partition("#")
        if name == "prose.md" and anchor == "convenções-de-escrita":
            return name in documents and "Convenções de escrita" in headings(documents[name])
    if "(prose.md, Convenções de escrita)" in text:
        return "prose.md" in documents and "Convenções de escrita" in headings(documents["prose.md"])
    return False


def partial_examples_valid(text):
    """A before/after fragment needs a text fence and a nearby partial label."""
    found = False
    for language, body, preceding in fenced_blocks(text):
        if not ("Antes:" in body and "Depois:" in body):
            continue
        found = True
        prefix = preceding.strip().split("\n\n")[-2:]
        context = "\n".join(prefix) + "\n" + body
        if language != "text":
            return False
        if not re.search(r"(?i)did[aá]tic|parcial|fragmento|ilustrativ", context):
            return False
        if re.search(r"(?im)^(?:#{1,4}\s+)?(?:exemplo|artefato) completo", "\n".join(prefix)):
            return False
    return found


class EditorialTest(unittest.TestCase):
    def test_local_prose_files_exist(self):
        paths = [ROOT / skill / "references/prose.md" for skill in ("prd", "sdd")]
        for path in paths:
            self.assertTrue(path.is_file(), str(path))
            self.assertFalse(path.is_symlink(), str(path))
        self.assertNotEqual(paths[0].resolve(), paths[1].resolve())

    def test_editorial_headings_exist(self):
        for skill in ("prd", "sdd"):
            text = (ROOT / skill / "references/prose.md").read_text(encoding="utf-8")
            self.assertTrue(HEADINGS <= headings(text))
            for heading in HEADINGS:
                damaged = text.replace("## " + heading, "## Missing section")
                self.assertFalse(HEADINGS <= headings(damaged))

    def test_local_editorial_references_resolve(self):
        for skill, source in (("prd", "writing.md"), ("sdd", "workflow.md")):
            folder = ROOT / skill / "references"
            text = (folder / source).read_text(encoding="utf-8")
            documents = {"prose.md": (folder / "prose.md").read_text(encoding="utf-8")}
            self.assertTrue(editorial_link_resolves(text, documents))
            self.assertFalse(editorial_link_resolves(text, {}))
            self.assertFalse(editorial_link_resolves(text.replace("prose.md", "absent.md"), documents))
            self.assertFalse(editorial_link_resolves(text, {"prose.md": "# No target heading\n"}))

    def test_artifact_profiles_present(self):
        for name, heading in PROFILES.items():
            with self.subTest(source=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn(heading, headings(text))
                self.assertNotIn(heading, headings(text.replace("### " + heading, "### Missing profile")))

    def test_partial_examples_are_labeled(self):
        for name in EXAMPLES:
            with self.subTest(source=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                self.assertTrue(partial_examples_valid(text))
        fixture = "Exemplo parcial didático.\n\n```text\nAntes: A\nDepois: B\n```\n"
        self.assertTrue(partial_examples_valid(fixture))
        self.assertFalse(partial_examples_valid(fixture.replace("text", "markdown")))
        self.assertFalse(partial_examples_valid(fixture.replace("Exemplo parcial didático", "Artefato completo")))
        self.assertFalse(partial_examples_valid(fixture.replace("Exemplo parcial didático.", "")))
        self.assertTrue(partial_examples_valid(fixture.replace(
            "Exemplo parcial didático.", "Fragmento didático; não é um artefato completo.")))

    def test_nested_fences_keep_the_complete_template(self):
        fixture = "````markdown\n# Template\n```mermaid\ngraph LR\n```\n````\n"
        blocks = list(fenced_blocks(fixture))
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0][0], "markdown")
        self.assertIn("```mermaid", blocks[0][1])

    def test_complete_examples_keep_contracts(self):
        # Existing lint suites remain the authority for complete template validity.
        for name in EXAMPLES:
            if name.endswith("verify.md"):
                continue  # Verify provides a chat fragment, not a document template.
            with self.subTest(source=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                complete = [body for language, body, _ in fenced_blocks(text) if language == "markdown"]
                self.assertTrue(complete, "Complete template must remain in its markdown fence")
                self.assertTrue(any(re.search(r"^# ", block, re.MULTILINE) for block in complete))
                self.assertTrue(partial_examples_valid(text))


if __name__ == "__main__":
    unittest.main()
