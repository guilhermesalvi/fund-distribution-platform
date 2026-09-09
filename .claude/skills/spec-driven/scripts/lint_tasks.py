#!/usr/bin/env python3
"""
lint_tasks.py - verificacao deterministica do esqueleto de um tasks.md.

    Uso:  python3 <skill-dir>/scripts/lint_tasks.py <tasks.md> --spec <spec.md>

`--spec` e obrigatorio: e a spec viva da capability, fonte dos IDs de
requisito. Sem ela a cobertura nao e verificada e o linter reporta HARD.

Escopo da mudanca: por default, todos os requisitos da spec. Mudanca que toca
so parte deles declara `scope: RSV-07, RSV-10` no comentario de maquina
(`<!-- sdd: tasks | spec: ../spec.md | design: ./design.md | scope: RSV-07, RSV-10 -->`);
so esses entram em "requisito sem task".

HARD (exit 1):
- comentario de maquina ausente ou sem `sdd: tasks`; `spec:` ausente;
- secoes `## Comandos de Gate` e `## Plano de execucao` ausentes;
- tabela Comandos de Gate sem linhas de dados; celula de Comando vazia; valor
  de `Gate` usado numa task sem linha na tabela;
- task `### Tn:` ou `### TCn:` com ID duplicado; campo obrigatorio ausente
  (O que, Onde, Depende de, Requisito, Pronto quando, Tests, Gate) ou vazio;
  campo duplicado na mesma task;
- task sem Requisito (sem nenhum ID); ID de requisito que nao existe na spec;
  requisito da spec (no escopo) sem task;
- dependencia: task inexistente; ciclo (reportado com os IDs); dependencia
  para fase posterior; `T` dependendo de `TC` (task de correcao nasce no
  Verify, depois do plano);
- plano de execucao nos dois sentidos: task citada no plano sem corpo; task
  `T` com corpo fora do plano (tasks `TC` ficam fora dessa exigencia);
- `Tests` fora de unit|integration|e2e (lista) ou `none` sozinho; `Gate` fora
  de quick|full|build; Tests com integration/e2e e Gate quick; Tests none e
  Gate diferente de build.

WARN (nao afeta exit):
- Onde sem path de arquivo reconhecivel; Tests none; placeholder (TBD, TODO,
  "similar a T3").

Exit 2 em erro de uso: opcao desconhecida, arquivo ausente ou fora de UTF-8.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    REQ_ID, REQ_LINE, Report, fenced_line_mask, find_section_exact, parse_machine_comment,
    read_lines, scan_placeholders, table_rows, usage,
)

FIELDS = {
    "what": ("o quê", "o que", "what"),
    "where": ("onde", "where"),
    "depends": ("depende de", "depends on"),
    "requirement": ("requisito", "requirement"),
    "interfaces": ("interfaces",),
    "done": ("pronto quando", "done when"),
    "tests": ("tests", "testes"),
    "gate": ("gate",),
}
REQUIRED_FIELDS = ("what", "where", "depends", "requirement", "done", "tests", "gate")
# Campos cujo valor vem na mesma linha; vazio e defeito. Interfaces e Pronto
# quando sao blocos: o valor esta nas linhas seguintes.
SCALAR_FIELDS = ("what", "where", "depends", "requirement", "tests", "gate")
TESTS_OK = {"unit", "integration", "e2e", "none"}
GATE_OK = {"quick", "full", "build"}
PATH_RE = re.compile(r"`?[\w./\\\-]+/[\w.\-]+\.[A-Za-z0-9]+`?")
TASK_REF = re.compile(r"\b(TC?)(\d+)\b")
TASK_HEADING = re.compile(r"^###\s+(TC?)(\d+)\s*:\s*(.+)$")
NO_DEPS = re.compile(r"^\s*(?:nenhuma|nenhum|none|n/?a|-)\s*$", re.IGNORECASE)

SECTION_GATES = ("Comandos de Gate", "Gate Commands")
SECTION_PLAN = ("Plano de execução", "Plano de execucao", "Execution Plan")


def task_refs(text):
    return [f"{fam}{num}" for fam, num in TASK_REF.findall(text)]


def task_key(tid):
    fam, num = TASK_REF.match(tid).groups()
    return (fam, int(num))


def parse_tasks(lines, mask):
    """Retorna (tasks, duplicates).
    tasks: tid -> {'line', 'family', 'num', 'title', 'fields': {key: (idx, value)}, 'dup_fields'}
    duplicates: [(idx, tid)] para cada heading repetido (a primeira vale)."""
    tasks, dups, cur = {}, [], None
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        m = TASK_HEADING.match(l)
        if m:
            tid = f"{m.group(1)}{m.group(2)}"
            if tid in tasks:
                dups.append((i, tid))
                cur = None
                continue
            cur = tid
            tasks[tid] = {"line": i, "family": m.group(1), "num": int(m.group(2)),
                          "title": m.group(3).strip(), "fields": {}, "dup_fields": []}
            continue
        if l.startswith("## ") or l.startswith("### "):
            cur = None
            continue
        if cur is None:
            continue
        fm = re.match(r"^\s*[-*]\s+\*\*([^*]+?)\s*:?\*\*\s*:?\s*(.*)$", l)
        if fm:
            label = fm.group(1).strip().lower()
            for key, aliases in FIELDS.items():
                if any(label.startswith(a) for a in aliases):
                    if key in tasks[cur]["fields"]:
                        tasks[cur]["dup_fields"].append((i, aliases[0]))
                    else:
                        tasks[cur]["fields"][key] = (i, fm.group(2).strip())
                    break
    return tasks, dups


def parse_plan(lines, mask):
    """(plan_ids, phase_of, sec): IDs citados no Plano de execucao, fase de
    cada um ('### Fase N' / '### Phase N'), faixa da secao ou None."""
    sec = find_section_exact(lines, SECTION_PLAN, mask=mask)
    plan_ids, phase_of = [], {}
    if not sec:
        return plan_ids, phase_of, None
    cur = None
    for i in range(*sec):
        if mask[i]:
            continue
        pm = re.match(r"^###\s+(?:Fase|Phase)\s+(\d+)", lines[i], re.IGNORECASE)
        if pm:
            cur = int(pm.group(1))
            continue
        for t in task_refs(lines[i]):
            if t not in plan_ids:
                plan_ids.append(t)
            if cur is not None:
                phase_of.setdefault(t, cur)
    return plan_ids, phase_of, sec


def table_header(lines, start, end):
    for i in range(start, end):
        l = lines[i].strip()
        if l.startswith("|"):
            return [c.strip().lower() for c in l.strip("|").split("|")]
    return []


def column_index(header, names, default):
    for n, cell in enumerate(header):
        if any(cell.startswith(x) for x in names):
            return n
    return default


def clean_cell(v):
    return v.strip().strip("`*").strip().lower()


def check_gate_table(rep, lines, mask, gates_used):
    sec = find_section_exact(lines, SECTION_GATES, mask=mask)
    if sec is None:
        rep.hard("secao ausente: ## Comandos de Gate")
        return
    rows = table_rows(lines, *sec)
    if not rows:
        rep.hard("secao Comandos de Gate sem linhas de dados na tabela", sec[0])
        return
    header = table_header(lines, *sec)
    cmd_col = column_index(header, ("comando", "command"), len(header) - 1)
    gate_col = column_index(header, ("gate",), 0)
    declared = set()
    for i, cells in rows:
        cmd = cells[cmd_col] if cmd_col < len(cells) else ""
        if not clean_cell(cmd):
            rep.hard("Comandos de Gate: celula de comando vazia", i + 1)
        if gate_col < len(cells):
            declared.add(clean_cell(cells[gate_col]))
    for gate in sorted(gates_used):
        if gate not in declared:
            tids = ", ".join(sorted(gates_used[gate], key=task_key))
            rep.hard(f"Gate '{gate}' usado em {tids} sem linha na tabela Comandos de Gate")


def spec_requirements(path):
    """IDs dos requisitos da secao Requisitos da spec viva (fora de fence)."""
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    sec = find_section_exact(lines, ("Requisitos", "Requirements"), mask=mask)
    ids = set()
    if sec:
        for i in range(*sec):
            m = REQ_LINE.match(lines[i])
            if m and not mask[i]:
                ids.add(m.group(1))
    return ids


def find_cycles(deps):
    """DFS sobre tid -> [deps]. Lista de ciclos, cada um fechado
    (['T1', 'T2', 'T1']); cada ciclo reportado uma vez."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {t: WHITE for t in deps}
    stack, cycles, seen = [], [], set()

    def visit(t):
        color[t] = GRAY
        stack.append(t)
        for d in deps.get(t, ()):
            if d not in color:
                continue
            if color[d] == GRAY:
                cyc = stack[stack.index(d):] + [d]
                key = frozenset(cyc)
                if key not in seen:
                    seen.add(key)
                    cycles.append(cyc)
            elif color[d] == WHITE:
                visit(d)
        stack.pop()
        color[t] = BLACK

    for t in sorted(deps, key=task_key):
        if color[t] == WHITE:
            visit(t)
    return cycles


def parse_tests(value):
    raw = value.strip("` ").lower()
    if not raw:
        return [], ["vazio"]
    items = [x.strip().strip("`") for x in raw.split(",")]
    errs = []
    bad = [x for x in items if x not in TESTS_OK]
    if bad:
        errs.append(f"tipo(s) invalido(s): {', '.join(repr(b) for b in bad)}; aceitos: unit|integration|e2e|none")
    if "none" in items and len(items) > 1:
        errs.append("'none' so sozinho, nao em lista")
    if len(set(items)) != len(items):
        errs.append("tipo repetido na lista")
    return items, errs


def check_dependencies(rep, tasks, phase_of):
    graph = {}
    for tid in sorted(tasks, key=task_key):
        t = tasks[tid]
        f = t["fields"]
        graph[tid] = []
        if "depends" not in f or not f["depends"][1]:
            continue
        idx, value = f["depends"]
        ln = idx + 1
        deps = task_refs(value)
        if not deps and not NO_DEPS.match(value):
            rep.hard(f"{tid}: Depende de invalido: '{value[:40]}' (esperado IDs de task ou 'nenhuma')", ln)
            continue
        for d in deps:
            if d not in tasks:
                rep.hard(f"{tid}: depende de {d}, que nao existe", ln)
                continue
            graph[tid].append(d)
            if d == tid:
                continue
            dt = tasks[d]
            if t["family"] == "T" and dt["family"] == "TC":
                rep.hard(f"{tid}: depende de {d} - task de correcao nasce no Verify, depois de toda task T", ln)
                continue
            if tid in phase_of and d in phase_of and phase_of[d] > phase_of[tid]:
                rep.hard(f"{tid} (fase {phase_of[tid]}) depende de {d} (fase {phase_of[d]}) - dependencia para fase posterior", ln)
                continue
            if dt["family"] == t["family"] and dt["num"] >= t["num"]:
                same_or_earlier = tid in phase_of and d in phase_of and phase_of[d] <= phase_of[tid]
                if not same_or_earlier:
                    rep.hard(f"{tid}: depende de {d} (numero maior ou igual, sem fase anterior/igual no plano que justifique) - ordem errada", ln)
    for cyc in find_cycles(graph):
        rep.hard(f"ciclo de dependencia: {' -> '.join(cyc)}", tasks[cyc[0]]["fields"]["depends"][0] + 1)


def check_plan(rep, tasks, plan_ids, plan_sec):
    if plan_sec is None:
        rep.hard("secao ausente: ## Plano de execução")
        return
    for t in plan_ids:
        if t not in tasks:
            rep.hard(f"Plano de execucao cita {t}, que nao existe na lista de tasks", plan_sec[0])
    for tid in sorted(tasks, key=task_key):
        if tasks[tid]["family"] == "T" and tid not in plan_ids:
            rep.hard(f"{tid}: nao aparece no Plano de execucao", tasks[tid]["line"] + 1)


def check_task(rep, tid, t, gates_used, req_refs):
    f = t["fields"]
    ln = t["line"] + 1
    for idx, label in t["dup_fields"]:
        rep.hard(f"{tid}: campo duplicado: {label}", idx + 1)
    for key in REQUIRED_FIELDS:
        if key not in f:
            rep.hard(f"{tid}: campo obrigatorio ausente: {FIELDS[key][0]}", ln)
        elif key in SCALAR_FIELDS and not f[key][1]:
            rep.hard(f"{tid}: campo vazio: {FIELDS[key][0]}", f[key][0] + 1)
    if "where" in f and f["where"][1] and not PATH_RE.findall(f["where"][1]):
        rep.warn(f"{tid}: Onde sem path de arquivo reconhecivel", f["where"][0] + 1)
    if "requirement" in f and f["requirement"][1]:
        refs = set(REQ_ID.findall(f["requirement"][1]))
        if not refs:
            rep.hard(f"{tid}: Requisito sem ID - task sem requisito e escopo escondido", f["requirement"][0] + 1)
        req_refs[tid] = refs

    test_types = []
    if "tests" in f and f["tests"][1]:
        test_types, errs = parse_tests(f["tests"][1])
        for e in errs:
            rep.hard(f"{tid}: Tests invalido: {e} (veio '{f['tests'][1][:40]}')", f["tests"][0] + 1)
        if errs:
            test_types = []
        elif test_types == ["none"]:
            rep.warn(f"{tid}: Tests: none - confirme que a camada nao exige teste", f["tests"][0] + 1)

    gate = None
    if "gate" in f and f["gate"][1]:
        gate = f["gate"][1].strip("` ").lower()
        if gate not in GATE_OK:
            rep.hard(f"{tid}: Gate invalido: deve ser quick|full|build, veio '{gate}'", f["gate"][0] + 1)
            gate = None
        else:
            gates_used.setdefault(gate, set()).add(tid)
    if test_types == ["none"] and gate in ("quick", "full"):
        rep.hard(f"{tid}: Tests: none com Gate: {gate} - incoerente (sem teste o gate e build)", f["gate"][0] + 1)
    if gate == "quick" and {"integration", "e2e"} & set(test_types):
        rep.hard(f"{tid}: Tests com integration/e2e exige Gate: full, veio quick", f["gate"][0] + 1)


def parse_args(argv):
    args = list(argv[1:])
    if not args or args[0].startswith("--"):
        usage(__doc__)
    path, spec, i = args[0], None, 1
    while i < len(args):
        if args[i] == "--spec":
            spec = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        else:
            usage(f"opcao desconhecida: {args[i]}\n\n{__doc__}")
    return path, spec


def main(argv):
    path, spec = parse_args(argv)
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    rep = Report("lint_tasks")

    fields, mc_idx = parse_machine_comment(lines)
    if fields is None or fields["sdd"].lower() != "tasks":
        rep.hard("primeira linha deve ser <!-- sdd: tasks | spec: <path> [| design: <path>] [| scope: IDs] -->", 1)
        return rep.emit(path)
    if not fields.get("spec"):
        rep.hard("comentario de maquina sem 'spec:'", 1)

    tasks, dups = parse_tasks(lines, mask)
    for i, tid in dups:
        rep.hard(f"ID de task duplicado: {tid} (a primeira definicao vale; esta e ignorada)", i + 1)
    if not tasks:
        rep.hard("nenhuma task '### Tn: ...' ou '### TCn: ...' encontrada")
        return rep.emit(path)

    plan_ids, phase_of, plan_sec = parse_plan(lines, mask)
    gates_used, req_refs = {}, {}
    for tid in sorted(tasks, key=task_key):
        check_task(rep, tid, tasks[tid], gates_used, req_refs)
    check_dependencies(rep, tasks, phase_of)
    check_plan(rep, tasks, plan_ids, plan_sec)
    check_gate_table(rep, lines, mask, gates_used)

    if spec is None:
        rep.hard("--spec obrigatorio: cobertura requisito -> task nao verificada")
    elif not spec or not os.path.exists(spec):
        rep.hard(f"spec nao encontrada: '{spec}'")
    else:
        known = spec_requirements(spec)
        if not known:
            rep.hard(f"{spec} sem requisitos em ## Requisitos - nao serve de fonte de cobertura")
        cited = set().union(*req_refs.values()) if req_refs else set()
        for tid in sorted(req_refs, key=task_key):
            for rid in sorted(req_refs[tid] - known):
                rep.hard(f"{tid}: requisito {rid} nao existe na spec", tasks[tid]["fields"]["requirement"][0] + 1)
        scope = known
        if fields.get("scope"):
            scope = set(REQ_ID.findall(fields["scope"]))
            for rid in sorted(scope - known):
                rep.hard(f"scope: {rid} nao existe na spec", 1)
        for rid in sorted(scope & known - cited):
            rep.hard(f"requisito {rid} da spec sem task - codigo que nao vai existir")

    scan_placeholders(rep, lines, skip_first=(mc_idx or 0) + 1, mask=mask)
    return rep.emit(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
