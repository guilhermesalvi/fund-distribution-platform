#!/usr/bin/env python3
"""
skills_gate.py - gate deterministico das skills de agente (.claude/skills).

    Uso:  python3 .github/scripts/skills_gate.py            # roda todos os checks
          python3 .github/scripts/skills_gate.py --list     # imprime a lista de checks e limites
          python3 .github/scripts/skills_gate.py --only ID  # roda so o check ID (repetivel)

Roda a partir da raiz do repositorio, em qualquer sistema. E a mesma lista que a
CI (.github/workflows/skills.yml) executa; o que o gate nao cobre - a revisao
cetica por LLM com nota minima - esta escrito em .claude/skills/GATE.md, que
aponta para este script como fonte da parte deterministica.

Cada check tem um identificador, uma descricao e um limite (threshold)
explicito. O gate imprime uma linha por check, `PASS` ou `FAIL`, com o valor
medido ao lado do limite, e termina com exit 1 se qualquer check falhou.
Nenhum check e pulado em silencio: ambiente sem o parser Mermaid instalado
(exit 3 dos lint_mermaid.py) e FAIL, porque o gate existe para nao deixar
validacao por fazer.

Checks (a mesma lista sai com --list):

  mermaid-selftest   parser Mermaid de cada skill passa no --self-test        exit 0 nos 2
  suite-prd          suite da prd: falhas, erros e skips                      0 / 0 / 0
  suite-sdd          suite da sdd: falhas, erros e skips                      0 / 0 / 0
  suite-github       suite de .github/scripts: falhas, erros e skips          0 / 0 / 0
  lint-prd           seq check + lint_prd + lint_mermaid em docs/prd          0 HARD
  lint-specs         seq check + lint_spec em cada docs/specs/*/*/spec.md     0 HARD
  lint-changes       lint_design e lint_tasks (--spec) em docs/specs/*/*/*    0 HARD
  lint-adr           seq check + lint_adr em docs/adr, quando existe          0 HARD
  mermaid-specs      lint_mermaid em docs/specs                               0 HARD
  independence       skill citando a outra, a si mesma por path ou "commit"   0 ocorrencias
  entities           entidades HTML (&lt; &gt; &amp;) nos .md e .py das skills 0 arquivos
  eol                fim de linha CRLF ou misto no indice das skills          0 arquivos
  slnx               arquivo versionado fora do FundDistributionPlatform.slnx 0 arquivos
  readme-scripts     script de skill sem comando no README.md                 0 scripts

WARN dos linters nao entra em limite: e heuristica para julgamento humano e o
gate so o reporta. Os limites sao fixos no codigo (CHECKS); mudar um limite e
mudanca de regra e passa pela revisao de GATE.md.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ("prd", "sdd")
SKIP_DIRS = {"__pycache__", "node_modules", ".git"}

UNITTEST_RAN = re.compile(r"^Ran (\d+) tests? in", re.MULTILINE)
UNITTEST_TAIL = re.compile(r"^(OK|FAILED)(?: \(([^)]*)\))?\s*$", re.MULTILINE)
LINT_SUMMARY = re.compile(r"(\d+) HARD, (\d+) WARN")
ENTITY = re.compile(r"&lt;|&gt;|&amp;")
SLNX_ENTRY = re.compile(r'<(File|Project) Path="([^"]+)"')

# Independencia entre skills: a mesma lista do teste de cada skill e da CI. "prd" sozinho e o
# artefato (PRD), nao a skill; o acoplamento permitido e so pelo artefato.
INDEPENDENCE = (
    ("sdd cita a outra skill ou arquivo que nao existe mais",
     "sdd", r"skills/prd\b|intake\.md|writing\.md|output\.md|review\.md|modes\.md|memory\.md",
     {"test_docs_consistency.py"}, set()),
    ("sdd cita a si mesma por path",
     "sdd", r"skills/sdd\b", {"test_docs_consistency.py"}, set()),
    ("prd cita a sdd ou os artefatos dela",
     "prd", r"skills/sdd\b|specify\.md|design\.md|memory\.md|/docs/specs|prd-rev", set(), set()),
    ("prd cita a si mesma por path",
     "prd", r"skills/prd\b", set(), {"mermaid-parser"}),
)
# Politica de commit e do repositorio: os scripts da sdd nao a conhecem.
COMMIT_WORD_DIR = Path(".claude/skills/sdd/scripts")


@dataclass(frozen=True)
class Result:
    ok: bool
    measured: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class Check:
    id: str
    description: str
    threshold: str
    run: Callable[[], Result]


def run_cmd(args: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def python(*args: str) -> subprocess.CompletedProcess:
    return run_cmd([sys.executable, *args])


def parse_unittest(output: str) -> dict[str, int]:
    """Le a cauda do unittest: total, failures, errors, skipped. Sem cauda reconhecivel,
    conta como 1 erro (a suite nem chegou a rodar)."""
    counts = {"ran": 0, "failures": 0, "errors": 0, "skipped": 0}
    ran = UNITTEST_RAN.findall(output)
    tail = UNITTEST_TAIL.findall(output)
    if not ran or not tail:
        counts["errors"] = 1
        return counts
    counts["ran"] = int(ran[-1])
    status, extra = tail[-1]
    for part in (extra or "").split(","):
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            if key in counts:
                counts[key] = int(value)
    if status == "FAILED" and counts["failures"] == 0 and counts["errors"] == 0:
        counts["errors"] = 1
    return counts


def parse_lint(output: str) -> tuple[int, int]:
    """Soma HARD e WARN de todas as linhas-resumo `N HARD, M WARN` da saida."""
    hard = warn = 0
    for h, w in LINT_SUMMARY.findall(output):
        hard += int(h)
        warn += int(w)
    return hard, warn


def check_suite(tests_dir: str) -> Result:
    proc = python("-m", "unittest", "discover", "-s", tests_dir)
    counts = parse_unittest(proc.stdout + proc.stderr)
    ok = counts["failures"] == 0 and counts["errors"] == 0 and counts["skipped"] == 0
    measured = (f"{counts['ran']} testes, falhas {counts['failures']}, erros {counts['errors']}, "
                f"skips {counts['skipped']}")
    details = () if ok else tuple((proc.stdout + proc.stderr).strip().splitlines()[-25:])
    return Result(ok, measured, details)


def check_mermaid_selftest() -> Result:
    details = []
    for skill in SKILLS:
        proc = python(f".claude/skills/{skill}/scripts/lint_mermaid.py", "--self-test")
        if proc.returncode != 0:
            details.append(f"{skill}: exit {proc.returncode}")
            details.extend((proc.stdout + proc.stderr).strip().splitlines()[-5:])
    return Result(not details, f"{len(SKILLS) - sum(1 for d in details if ': exit' in d)} de {len(SKILLS)} com exit 0",
                  tuple(details))


def lint_group(commands: list[list[str]]) -> Result:
    """Roda cada comando; HARD e a soma dos resumos, e exit 2 ou 3 (uso, parser ausente) tambem
    e falha, porque significa validacao nao feita."""
    hard = warn = 0
    details: list[str] = []
    for cmd in commands:
        proc = python(*cmd)
        out = proc.stdout + proc.stderr
        h, w = parse_lint(out)
        hard += h
        warn += w
        if proc.returncode in (2, 3) or (proc.returncode != 0 and h == 0):
            hard += 1
            details.append(f"exit {proc.returncode}: {' '.join(cmd)}")
            details.extend(out.strip().splitlines()[-5:])
        elif h:
            details.extend(line for line in out.splitlines() if line.startswith("HARD"))
    return Result(hard == 0, f"{hard} HARD, {warn} WARN", tuple(details))


def specs() -> list[Path]:
    return sorted((ROOT / "docs/specs").glob("*/*/spec.md")) if (ROOT / "docs/specs").is_dir() else []


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_lint_prd() -> Result:
    if not (ROOT / "docs/prd").is_dir():
        return Result(True, "sem docs/prd")
    return lint_group([
        [".claude/skills/prd/scripts/seq.py", "check", "docs/prd"],
        [".claude/skills/prd/scripts/lint_prd.py", "docs/prd"],
        [".claude/skills/prd/scripts/lint_mermaid.py", "docs/prd"],
    ])


def check_lint_specs() -> Result:
    found = specs()
    if not found:
        return Result(True, "sem docs/specs")
    commands: list[list[str]] = []
    for spec in found:
        commands.append([".claude/skills/sdd/scripts/seq.py", "check", rel(spec.parent)])
        commands.append([".claude/skills/sdd/scripts/lint_spec.py", rel(spec)])
    return lint_group(commands)


def check_lint_changes() -> Result:
    commands: list[list[str]] = []
    for spec in specs():
        for design in sorted(spec.parent.glob("*/design.md")):
            commands.append([".claude/skills/sdd/scripts/lint_design.py", rel(design), "--spec", rel(spec)])
        for tasks in sorted(spec.parent.glob("*/tasks.md")):
            commands.append([".claude/skills/sdd/scripts/lint_tasks.py", rel(tasks), "--spec", rel(spec)])
    if not commands:
        return Result(True, "sem design.md ou tasks.md em docs/specs")
    return lint_group(commands)


def check_lint_adr() -> Result:
    if not (ROOT / "docs/adr").is_dir():
        return Result(True, "sem docs/adr")
    return lint_group([
        [".claude/skills/sdd/scripts/seq.py", "check", "docs/adr"],
        [".claude/skills/sdd/scripts/lint_adr.py", "docs/adr"],
    ])


def check_mermaid_specs() -> Result:
    if not (ROOT / "docs/specs").is_dir():
        return Result(True, "sem docs/specs")
    return lint_group([[".claude/skills/sdd/scripts/lint_mermaid.py", "docs/specs"]])


def iter_files(base: Path, skip_dirs: set[str] = frozenset(), skip_files: set[str] = frozenset()):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and d not in skip_dirs)
        for name in sorted(filenames):
            if name not in skip_files:
                yield Path(dirpath) / name


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""  # binario: fora do escopo, como o grep -I


def grep(base: Path, pattern: str, skip_files: set[str] = frozenset(),
         skip_dirs: set[str] = frozenset()) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    hits = []
    for path in iter_files(ROOT / base, skip_dirs, skip_files):
        for number, line in enumerate(read_text(path).splitlines(), 1):
            if regex.search(line):
                hits.append(f"{rel(path)}:{number}: {line.strip()[:120]}")
    return hits


def check_independence() -> Result:
    details = []
    for label, skill, pattern, skip_files, skip_dirs in INDEPENDENCE:
        hits = grep(Path(".claude/skills") / skill, pattern, skip_files, skip_dirs)
        if hits:
            details.append(f"{label}:")
            details.extend(hits)
    hits = grep(COMMIT_WORD_DIR, r"commit", skip_dirs={"tests"})
    if hits:
        details.append("politica de commit dentro dos scripts da sdd:")
        details.extend(hits)
    count = sum(1 for d in details if not d.endswith(":"))
    return Result(count == 0, f"{count} ocorrencia(s)", tuple(details))


def check_entities() -> Result:
    offenders = []
    for skill in SKILLS:
        for path in iter_files(ROOT / ".claude/skills" / skill):
            if path.suffix in (".md", ".py") and ENTITY.search(read_text(path)):
                offenders.append(rel(path))
    return Result(not offenders, f"{len(offenders)} arquivo(s)", tuple(offenders))


def check_eol() -> Result:
    proc = run_cmd(["git", "ls-files", "--eol", "--", ".claude/skills"])
    offenders = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] in ("i/crlf", "i/mixed"):
            offenders.append(f"{parts[0]} {parts[-1]}")
    return Result(not offenders, f"{len(offenders)} arquivo(s)", tuple(offenders))


def slnx_missing(slnx_text: str, tracked: list[str], slnx_name: str) -> list[str]:
    """Arquivo versionado que nem esta como <File> nem vive sob a pasta de um <Project>."""
    files = set()
    project_dirs = set()
    for kind, path in SLNX_ENTRY.findall(slnx_text):
        if kind == "Project":
            project_dirs.add(path.rsplit("/", 1)[0] + "/")
        else:
            files.add(path)
    missing = []
    for path in tracked:
        if path == slnx_name or path in files:
            continue
        if any(path.startswith(d) for d in project_dirs):
            continue
        missing.append(path)
    return missing


def check_slnx() -> Result:
    slnx = ROOT / "FundDistributionPlatform.slnx"
    tracked = run_cmd(["git", "ls-files"]).stdout.split()
    missing = slnx_missing(slnx.read_text(encoding="utf-8"), tracked, slnx.name)
    return Result(not missing, f"{len(missing)} arquivo(s) fora do .slnx", tuple(missing))


def scripts_without_readme_command(readme: str, scripts: list[str]) -> list[str]:
    return [s for s in scripts if s not in readme]


def check_readme_scripts() -> Result:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    scripts = []
    for skill in SKILLS:
        for path in sorted((ROOT / ".claude/skills" / skill / "scripts").glob("*.py")):
            if not path.name.startswith("_"):
                scripts.append(rel(path))
    missing = scripts_without_readme_command(readme, scripts)
    return Result(not missing, f"{len(missing)} de {len(scripts)} script(s) sem comando", tuple(missing))


CHECKS: tuple[Check, ...] = (
    Check("mermaid-selftest", "parser Mermaid de cada skill passa no --self-test", "exit 0 nos 2",
          check_mermaid_selftest),
    Check("suite-prd", "suite da prd: falhas, erros e skips", "0 / 0 / 0",
          lambda: check_suite(".claude/skills/prd/scripts/tests")),
    Check("suite-sdd", "suite da sdd: falhas, erros e skips", "0 / 0 / 0",
          lambda: check_suite(".claude/skills/sdd/scripts/tests")),
    Check("suite-github", "suite de .github/scripts: falhas, erros e skips", "0 / 0 / 0",
          lambda: check_suite(".github/scripts/tests")),
    Check("lint-prd", "seq check + lint_prd + lint_mermaid em docs/prd", "0 HARD", check_lint_prd),
    Check("lint-specs", "seq check + lint_spec em cada docs/specs/*/*/spec.md", "0 HARD", check_lint_specs),
    Check("lint-changes", "lint_design e lint_tasks (--spec) em docs/specs/*/*/*", "0 HARD", check_lint_changes),
    Check("lint-adr", "seq check + lint_adr em docs/adr, quando existe", "0 HARD", check_lint_adr),
    Check("mermaid-specs", "lint_mermaid em docs/specs", "0 HARD", check_mermaid_specs),
    Check("independence", 'skill citando a outra, a si mesma por path ou "commit"', "0 ocorrencias",
          check_independence),
    Check("entities", "entidades HTML (&lt; &gt; &amp;) nos .md e .py das skills", "0 arquivos", check_entities),
    Check("eol", "fim de linha CRLF ou misto no indice das skills", "0 arquivos", check_eol),
    Check("slnx", "arquivo versionado fora do FundDistributionPlatform.slnx", "0 arquivos", check_slnx),
    Check("readme-scripts", "script de skill sem comando no README.md", "0 scripts", check_readme_scripts),
)


def list_checks() -> str:
    width = max(len(c.id) for c in CHECKS)
    return "\n".join(f"{c.id:<{width}}  {c.description:<58} {c.threshold}" for c in CHECKS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate deterministico das skills (.claude/skills).")
    parser.add_argument("--list", action="store_true", help="imprime os checks e limites, sem rodar")
    parser.add_argument("--only", action="append", default=[], metavar="ID",
                        help="roda so o check ID (repetivel)")
    args = parser.parse_args(argv)

    if args.list:
        print(list_checks())
        return 0

    known = {c.id for c in CHECKS}
    unknown = [i for i in args.only if i not in known]
    if unknown:
        print(f"skills_gate: check desconhecido: {', '.join(unknown)}", file=sys.stderr)
        return 2

    selected = [c for c in CHECKS if not args.only or c.id in args.only]
    width = max(len(c.id) for c in selected)
    failed = 0
    for check in selected:
        result = check.run()
        status = "PASS" if result.ok else "FAIL"
        print(f"{status}  {check.id:<{width}}  {result.measured}  (limite: {check.threshold})")
        if not result.ok:
            failed += 1
            for line in result.details:
                print(f"      {line}")
    print(f"skills_gate: {len(selected) - failed} PASS, {failed} FAIL de {len(selected)} check(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
