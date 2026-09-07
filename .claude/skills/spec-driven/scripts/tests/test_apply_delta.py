"""Testes de apply_delta.py: validacao integral, replay, historico explicito,
persistencia atomica com preservacao de BOM/CRLF e regioes do autor.

    python -m unittest discover -s <skill-dir>/scripts/tests -p "test_apply_delta.py"
"""

import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
import apply_delta  # noqa: E402

LIVING = """<!-- sdd: spec | capability: x/cap -->
# Cap — Spec

| | |
|---|---|
| **Status** | Vigente |
| **Data** | 2026-01-01 (última mudança: 0000-init) |
| **Capability** | x/cap |
| **Prefixo** | AB |

## Propósito (Purpose)

Texto do autor, com acento e `código`.

## Requisitos (Requirements)

- **AB-01** — The system SHALL um
- **AB-02** — The system SHALL dois
- **AB-04** — The system SHALL quatro

## Domain Events

| Evento | Produtor | Consumidores | Payload semântico | Gatilho |
|---|---|---|---|---|
| Coisa | cap | outro | payload | gatilho |

## Glossário

- termo: definicao do autor

## Histórico de revisões

| Data | Mudança | IDs afetados |
|---|---|---|
| 2026-01-01 | 0000-init | +AB-01, +AB-02, +AB-04 |
"""

DELTA_HEAD = "<!-- sdd: spec-delta | tier: small | capability: x/cap -->\n# Delta\n\n## Contexto\n\nctx\n\n"


def delta(added=(), modified=(), removed=(), head=DELTA_HEAD, extra=""):
    """modified: (id, novo, antes | None)."""
    out = head
    if added:
        out += "## ADDED Requirements\n\n" + "".join(f"- **{i}** — {t}\n" for i, t in added) + "\n"
    if modified:
        out += "## MODIFIED Requirements\n\n"
        for i, t, before in modified:
            out += f"- **{i}** — {t}\n"
            if before is not None:
                out += f"  Antes: {before}\n"
        out += "\n"
    if removed:
        out += "## REMOVED Requirements\n\n" + "".join(f"- **{i}** — Razão: {t}\n" for i, t in removed) + "\n"
    return out + extra


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cap = os.path.join(self.tmp.name, "cap")
        os.makedirs(self.cap)
        self.living = os.path.join(self.cap, "spec.md")
        self.write_living(LIVING)

    def tearDown(self):
        self.tmp.cleanup()

    def write_living(self, text, newline="\n", bom=False):
        data = text.replace("\n", newline).encode("utf-8")
        with open(self.living, "wb") as f:
            f.write((b"\xef\xbb\xbf" if bom else b"") + data)

    def read_bytes(self, path=None):
        with open(path or self.living, "rb") as f:
            return f.read()

    def read_text(self):
        return self.read_bytes().decode("utf-8-sig").replace("\r\n", "\n")

    def write_delta(self, name, text):
        d = os.path.join(self.cap, "changes", name)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "spec.md")
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return p

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = apply_delta.main(list(argv))
        return code, out.getvalue()

    def apply(self, path, *extra):
        return self.run_cli("apply", path, "--date", "2026-02-01", *extra)

    def check(self, path):
        return self.run_cli("check", path)

    def assert_hard(self, result, *fragments):
        code, out = result
        self.assertEqual(code, 1, out)
        for frag in fragments:
            self.assertIn(frag, out)


class ApplyValid(Base):
    def test_added_modified_removed(self):
        p = self.write_delta("0001-a", delta(
            added=[("AB-03", "The system SHALL tres"), ("AB-05", "The system SHALL cinco")],
            modified=[("AB-01", "The system SHALL um-novo", "The system SHALL um")],
            removed=[("AB-02", "morreu")]))
        code, out = self.apply(p)
        self.assertEqual(code, 0, out)
        text = self.read_text()
        reqs = [l for l in text.splitlines() if l.startswith("- **AB-")]
        self.assertEqual(reqs, [
            "- **AB-01** — The system SHALL um-novo",
            "- **AB-03** — The system SHALL tres",
            "- **AB-04** — The system SHALL quatro",
            "- **AB-05** — The system SHALL cinco",
        ])
        self.assertIn("| 2026-02-01 | 0001-a | +AB-03, +AB-05, ~AB-01, -AB-02 |", text)
        self.assertNotIn("..", text.split("## Histórico")[1])
        self.assertIn("| **Data** | 2026-02-01 (última mudança: 0001-a) |", text)
        self.assertEqual(self.check(p)[0], 0)

    def test_dry_run_does_not_write(self):
        before = self.read_bytes()
        p = self.write_delta("0001-a", delta(added=[("AB-03", "The system SHALL tres")]))
        code, out = self.apply(p, "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("- **AB-03** — The system SHALL tres", out)
        self.assertEqual(self.read_bytes(), before)

    def test_author_regions_crlf_and_bom_preserved(self):
        self.write_living(LIVING, newline="\r\n", bom=True)
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(added=[("AB-03", "The system SHALL tres")]))
        code, out = self.apply(p)
        self.assertEqual(code, 0, out)
        data = self.read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"\r\n", data)
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        # regioes do autor byte a byte: tudo antes de "## Requisitos" exceto a
        # linha Data, e tudo entre "## Domain Events" e "## Histórico".
        def author_parts(b):
            t = b.decode("utf-8-sig")
            head = t.split("## Requisitos")[0]
            head = "\r\n".join(l for l in head.split("\r\n") if not l.startswith("| **Data**"))
            middle = t.split("## Domain Events")[1].split("## Histórico")[0]
            return head, middle
        self.assertEqual(author_parts(data), author_parts(original))

    def test_no_behavior_change_twice(self):
        p = self.write_delta("0001-nbc", "<!-- sdd: spec-delta | tier: small | capability: x/cap "
                                         "| no-behavior-change -->\n# N\n\n## Contexto\n\nctx\n")
        self.assertEqual(self.apply(p)[0], 0)
        after_first = self.read_bytes()
        code, out = self.apply(p)
        self.assertEqual(code, 0)
        self.assertIn("ja aplicado", out)
        self.assertEqual(self.read_bytes(), after_first)
        self.assertEqual(self.read_text().count("| 0001-nbc |"), 1)
        self.assertEqual(self.check(p)[0], 0)


class ApplyRefused(Base):
    def assert_untouched(self, original):
        self.assertEqual(self.read_bytes(), original)

    def test_before_mismatch_refused(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(
            added=[("AB-03", "The system SHALL tres")],
            modified=[("AB-01", "The system SHALL um-novo", "The system SHALL outro")]))
        self.assert_hard(self.apply(p), "MODIFIED AB-01: 'Antes:' difere")
        self.assert_untouched(original)  # tudo-ou-nada: ADDED valido nao entra

    def test_modified_without_before_refused(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(modified=[("AB-01", "The system SHALL x", None)]))
        self.assert_hard(self.apply(p), "sem linha 'Antes:'")
        self.assert_untouched(original)

    def test_missing_ids_refused(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(
            modified=[("AB-09", "The system SHALL x", "y")], removed=[("AB-08", "r")]))
        self.assert_hard(self.apply(p), "MODIFIED AB-09: ID inexistente", "REMOVED AB-08: ID inexistente")
        self.assert_untouched(original)

    def test_duplicate_and_conflicting_ids(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(
            added=[("AB-03", "The system SHALL a"), ("AB-03", "The system SHALL b")],
            modified=[("AB-03", "The system SHALL c", "The system SHALL um")]))
        self.assert_hard(self.apply(p), "ADDED AB-03: ID duplicado no delta", "MODIFIED AB-03: ID duplicado")
        self.assert_untouched(original)
        p = self.write_delta("0002-b", delta(added=[("AB-01", "The system SHALL x")]))
        self.assert_hard(self.apply(p), "ADDED AB-01: ID ja existe")
        self.assert_untouched(original)

    def test_malformed_requirement_lines(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(added=[("AB-03", "The system SHALL tres")],
                                             extra="- **CHK-2** — sem dois digitos\n- **chk-01** — minusculo\n"))
        code, out = self.apply(p)
        self.assertEqual(code, 1)
        self.assertEqual(out.count("linha com aparencia de requisito nao reconhecida"), 2)
        self.assert_untouched(original)

    def test_retired_id_list_and_legacy_range(self):
        self.write_living(LIVING.replace(
            "| 2026-01-01 | 0000-init | +AB-01, +AB-02, +AB-04 |",
            "| 2026-01-01 | 0000-init | +AB-01, +AB-02, +AB-04, +AB-05..07, +AB-09 |\n"
            "| 2026-01-02 | 0000-cut | -AB-05..07, −AB-09 |"))
        original = self.read_bytes()
        for rid in ("AB-05", "AB-06", "AB-07", "AB-09"):
            p = self.write_delta("0001-a", delta(added=[(rid, "The system SHALL x")]))
            self.assert_hard(self.apply(p), f"ADDED {rid}: ID aposentado")
            self.assert_untouched(original)
        p = self.write_delta("0001-a", delta(added=[("AB-08", "The system SHALL x")]))
        self.assertEqual(self.apply(p)[0], 0)

    def test_renamed_rejected(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(added=[("AB-03", "The system SHALL tres")],
                                             extra="## RENAMED Requirements\n\n- **AB-01**: um → uno\n"))
        self.assert_hard(self.apply(p), "RENAMED nao suportado: IDs sao estaveis; use REMOVED + ADDED")
        self.assert_untouched(original)

    def test_wrong_capability_and_kind(self):
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(
            added=[("AB-03", "The system SHALL tres")],
            head="<!-- sdd: spec-delta | tier: small | capability: x/other -->\n# D\n\n"))
        self.assert_hard(self.apply(p), "capability divergente: delta 'x/other', spec viva 'x/cap'")
        self.assert_untouched(original)
        p = self.write_delta("0002-b", delta(
            added=[("AB-03", "The system SHALL tres")],
            head="<!-- sdd: spec | capability: x/cap -->\n# D\n\n"))
        self.assert_hard(self.apply(p), "delta deve declarar `sdd: spec-delta`")
        self.assert_untouched(original)
        self.write_living(LIVING.replace("sdd: spec |", "sdd: spec-delta |"))
        p = self.write_delta("0003-c", delta(added=[("AB-03", "The system SHALL tres")]))
        self.assert_hard(self.apply(p), "spec viva deve declarar `sdd: spec`")

    def test_state_present_without_history_is_hard(self):
        p = self.write_delta("0001-a", delta(
            modified=[("AB-01", "The system SHALL um", "The system SHALL zero")]))
        # texto novo ja vigente, sem linha de historico: nao e "ja aplicado"
        code, out = self.apply(p)
        self.assertEqual(code, 1)
        self.assertNotIn("ja aplicado", out)
        self.assertIn("historico ausente/inconsistente", out)
        self.assertNotIn("| 0001-a |", self.read_text())
        p = self.write_delta("0002-b", delta(removed=[("AB-03", "nunca existiu")]))
        self.assert_hard(self.apply(p), "historico ausente/inconsistente")

    def test_write_failure_preserves_original(self):
        self.write_living(LIVING, newline="\r\n", bom=True)
        original = self.read_bytes()
        p = self.write_delta("0001-a", delta(added=[("AB-03", "The system SHALL tres")]))
        with mock.patch("os.replace", side_effect=OSError("disco cheio")):
            code, out = self.apply(p)
        self.assertEqual(code, 1)
        self.assertIn("falha ao escrever", out)
        self.assertIn("original intacto", out)
        self.assertEqual(self.read_bytes(), original)
        self.assertEqual([f for f in os.listdir(self.cap) if f.endswith(".tmp")], [])


class Replay(Base):
    def setUp(self):
        super().setUp()
        self.a = self.write_delta("0001-a", delta(
            added=[("AB-03", "The system SHALL tres")],
            modified=[("AB-01", "The system SHALL um-A", "The system SHALL um")],
            removed=[("AB-04", "sai")]))
        self.b = self.write_delta("0002-b", delta(
            modified=[("AB-01", "The system SHALL um-B", "The system SHALL um-A"),
                      ("AB-03", "The system SHALL tres-B", "The system SHALL tres")]))

    def test_reapply_same_change(self):
        self.assertEqual(self.apply(self.a)[0], 0)
        snapshot = self.read_bytes()
        code, out = self.apply(self.a)
        self.assertEqual(code, 0)
        self.assertIn("ja aplicado", out)
        self.assertEqual(self.read_bytes(), snapshot)

    def test_last_change_with_divergent_state(self):
        self.assertEqual(self.apply(self.a)[0], 0)
        self.write_living(self.read_text().replace("The system SHALL um-A", "The system SHALL editado"))
        snapshot = self.read_bytes()
        code, out = self.apply(self.a)
        self.assertEqual(code, 1)
        self.assertIn("estado inconsistente com o historico", out)
        self.assertEqual(self.read_bytes(), snapshot)

    def test_a_then_b_then_a_does_not_revert_b(self):
        self.assertEqual(self.apply(self.a)[0], 0)
        self.assertEqual(self.apply(self.b)[0], 0)
        snapshot = self.read_bytes()
        code, out = self.apply(self.a)
        self.assertEqual(code, 0)
        self.assertIn("delta historico, superseded por 0002-b; nao reaplique", out)
        self.assertEqual(self.read_bytes(), snapshot)
        text = self.read_text()
        self.assertIn("- **AB-01** — The system SHALL um-B", text)
        self.assertEqual(text.count("| 0001-a |"), 1)
        # check(A) audita: linha do historico e REMOVED ausente, sem exigir texto
        code, out = self.check(self.a)
        self.assertEqual(code, 0, out)
        self.assertIn("delta historico, superseded por 0002-b", out)
        self.assertNotIn("reaplique", out.replace("nao reaplique", ""))
        # check(B) e o estado recem-aplicado: exige texto
        self.assertEqual(self.check(self.b)[0], 0)
        self.write_living(self.read_text().replace("The system SHALL um-B", "The system SHALL um-C"))
        self.assert_hard(self.check(self.b), "MODIFIED AB-01 nao reflete o texto novo")
        # check(A) falha so se um REMOVED voltar
        self.write_living(self.read_text().replace(
            "- **AB-02** — The system SHALL dois", "- **AB-02** — The system SHALL dois\n- **AB-04** — voltou"))
        self.assert_hard(self.check(self.a), "REMOVED AB-04 ainda presente")

    def test_check_without_history_line(self):
        self.assert_hard(self.check(self.a), "historico de revisoes sem linha para a mudanca '0001-a'")


class Create(Base):
    def setUp(self):
        super().setUp()
        os.remove(self.living)

    def test_create_then_check_then_reapply(self):
        head = ("<!-- sdd: spec-delta | tier: large | capability: x/cap | prd: /docs/prd/0001-x.md "
                "| prd-rev: sha256:abc -->\n# Delta\n\n| | |\n|---|---|\n| **Status** | Rascunho |\n"
                "| **Prefixo** | AB |\n\n## Contexto\n\nContexto do delta.\n\n")
        p = self.write_delta("0001-a", delta(
            added=[("AB-02", "The system SHALL publicar `Coisa`"), ("AB-01", "The system SHALL um")],
            head=head))
        code, out = self.apply(p, "--create")
        self.assertEqual(code, 0, out)
        self.assertIn("AB-02 publica evento", out)
        text = self.read_text()
        self.assertTrue(text.startswith(
            "<!-- sdd: spec | capability: x/cap | prd: /docs/prd/0001-x.md | prd-rev: sha256:abc -->\n"))
        for frag in ("| **Status** | Vigente |", "| **Data** | 2026-02-01 (última mudança: 0001-a) |",
                     "| **Capability** | x/cap |", "| **Prefixo** | AB |", "## Propósito", "Contexto do delta.",
                     "reescrever no escopo da capability", "## Requisitos", "## Domain Events",
                     "## Glossário", "## Histórico de revisões", "| 2026-02-01 | 0001-a | +AB-01, +AB-02 |"):
            self.assertIn(frag, text)
        reqs = [l for l in text.splitlines() if l.startswith("- **AB-")]
        self.assertEqual(reqs, ["- **AB-01** — The system SHALL um",
                                "- **AB-02** — The system SHALL publicar `Coisa`"])
        self.assertEqual(self.check(p)[0], 0)
        code, out = self.apply(p)
        self.assertEqual(code, 0)
        self.assertIn("ja aplicado", out)
        self.assert_hard(self.apply(p, "--create"), "--create com spec viva ja existente")

    def test_create_refuses_modified(self):
        p = self.write_delta("0001-a", delta(modified=[("AB-01", "x", "y")]))
        self.assert_hard(self.apply(p, "--create"), "capability nova so admite ADDED")
        self.assertFalse(os.path.exists(self.living))

    def test_missing_living_without_create(self):
        p = self.write_delta("0001-a", delta(added=[("AB-01", "x")]))
        self.assert_hard(self.apply(p), "spec viva inexistente")


class ExitCodes(Base):
    def test_usage(self):
        self.assertEqual(self.run_cli("apply", os.path.join(self.cap, "nope.md"))[0], 2)
        p = os.path.join(self.cap, "loose.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(delta(added=[("AB-03", "x")]))
        self.assertEqual(self.run_cli("apply", p)[0], 2)  # spec viva nao inferivel

    def test_bad_change_name(self):
        d = os.path.join(self.cap, "changes", "feature-x")
        os.makedirs(d)
        p = os.path.join(d, "spec.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(delta(added=[("AB-03", "x")]))
        self.assert_hard(self.apply(p), "identidade da mudanca invalida")


class NoArgsTests(unittest.TestCase):
    def test_invalid_date_is_usage(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = apply_delta.main(["apply", "x.md", "--date", "2026-13-45", "--dry-run"])
            except SystemExit as e:
                code = e.code
        self.assertEqual(code, 2)
        self.assertIn("data invalida", err.getvalue())

    def test_check_with_missing_living_is_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            change = os.path.join(d, "cap", "changes", "0001-x")
            os.makedirs(change)
            delta = os.path.join(change, "spec.md")
            with open(delta, "w", encoding="utf-8") as f:
                f.write("<!-- sdd: spec-delta | tier: small | capability: x/cap -->\n# X\n\n## ADDED Requirements\n\n- **AB-01** — The system SHALL x\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = apply_delta.main(["check", delta])
            self.assertEqual(code, 1)
            self.assertIn("INCOMPLETO: spec viva nao encontrada", out.getvalue())

    def test_no_args_prints_docstring_and_exits_2(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = apply_delta.main([])
        self.assertEqual(code, 2)
        self.assertIn("apply_delta.py - ", err.getvalue())


if __name__ == "__main__":
    unittest.main()
