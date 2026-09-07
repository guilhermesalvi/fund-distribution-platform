#!/usr/bin/env python3
"""
lint_tasks.py - verificacao deterministica de um tasks.md gerado pela skill
spec-driven.

    Uso:  python3 <skill-dir>/scripts/lint_tasks.py <tasks.md> --spec <spec.md>
              [--commit-max-len N] [--commit-no-scope] [--commit-no-bang]
              [--commit-single-line] [--commit-lowercase]

`--spec` e obrigatorio: sem ele a cobertura requisito -> task nao e verificada
e o linter reporta HARD "validacao incompleta". So spec-delta com secao
`## ADDED Requirements` / `## MODIFIED Requirements` e aceita como fonte.

Checa:
- comentario de maquina; secoes Matriz de Cobertura, Comandos de Gate e Plano
  de execucao presentes e com linhas de dados; celula de comando vazia (HARD);
  todo valor de `Gate` usado nas tasks tem linha na tabela Comandos de Gate
  (HARD);
- tasks `### Tn:` e tasks de correcao `### TCn:` (verify.md, 2.8), em
  `## Tasks` ou `## Tasks de correcao`; ID duplicado (HARD);
- campos obrigatorios por task, distinguindo ausente, vazio e invalido; campo
  duplicado na mesma task (HARD); Onde sem path reconhecivel (WARN; varios
  arquivos por task sao esperados - implementacao, teste, registro);
- dependencias: task inexistente, ciclo (DFS sobre `Depende de`, ciclo
  reportado com os IDs), dependencia para fase posterior, numero maior sem
  fase anterior/igual que justifique (HARD);
- plano de execucao nos dois sentidos: task no plano que nao existe e task
  fora do plano (HARD); `## Mapa de execucao`, quando presente, cita o mesmo
  conjunto de tasks T do plano (HARD). Tasks de correcao (TC) ficam fora das
  duas exigencias, no plano e no mapa, porque nascem no Verify, depois do
  plano aprovado;
- todo ID de requisito ADDED/MODIFIED da spec mapeado a >=1 task (HARD).
  Delta de refactor (`no-behavior-change` no comentario de maquina, sem
  ADDED/MODIFIED): a fonte de cobertura sao os IDs citados no delta com o
  prefixo do header (`| **Prefixo** | RSV |`; sem header, todo ID X-nn),
  fora de bloco de codigo - os invariantes da spec viva (modes.md, Refactor).
  IDs de PRD ou de ADR citados no Contexto nao entram. Task que cita ID fora
  dessa lista e HARD, invariante sem task e WARN;
- `Tests`: lista separada por virgula de unit|integration|e2e, ou `none`
  sozinho; `none` (WARN); `Tests: none` exige `Gate: build`; Tests com
  integration/e2e com `Gate: quick` (HARD, incoerente);
- `Pronto quando` com criterios `- [ ]` (HARD sem); WARN sem criterio citando
  o gate; WARN quando todo criterio e estrutural (gate/build/contagem) -
  exit 0 nao prova regra de negocio;
- `Commit`: mensagem planejada validada com check_commit.check(); vazia
  (WARN: planejamento pode nao ter commit autorizado); presente e invalida
  (HARD). `--commit-max-len`, `--commit-no-scope`, `--commit-no-bang`,
  `--commit-single-line` e `--commit-lowercase` repassam a regra mais estrita
  do repositorio, uma a uma, as opcoes homonimas do check_commit.py (mesma
  politica nos dois lugares). Mensagem planejada, commit autorizado e commit
  executado sao estados distintos: aqui so a forma da mensagem e validada;
- placeholders proibidos (HARD).

Saida: HARD (exit 1) / WARN (nao afeta exit).
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    REQ_ID, REQ_LINE, TIERS, Report, fenced_line_mask, find_section,
    parse_machine_comment, read_lines, scan_placeholders, table_rows, usage,
)
import check_commit  # noqa: E402

FIELDS = {
    "what": (("o quê", "o que", "what"), "hard"),
    "where": (("onde", "where"), "hard"),
    "depends": (("depende de", "depends on"), "hard"),
    "requirement": (("requisito", "requirement"), "hard"),
    "interfaces": (("interfaces",), "warn"),
    "done": (("pronto quando", "done when"), "hard"),
    "tests": (("tests", "testes"), "hard"),
    "gate": (("gate",), "hard"),
    "commit": (("commit",), "warn"),
}
# Campos cujo valor vem na mesma linha; vazio e defeito. Os demais (Interfaces,
# Pronto quando) sao blocos: o valor esta nas linhas seguintes.
SCALAR_FIELDS = ("what", "where", "depends", "requirement", "tests", "gate")
TESTS_OK = {"unit", "integration", "e2e", "none"}
GATE_OK = {"quick", "full", "build"}
PATH_RE = re.compile(r"`?[\w./\\\-]+/[\w.\-]+\.[A-Za-z0-9]+`?")
# IDs de task normais (T1) e de correcao (TC1). Nao usa _common.TASK_ID porque
# ele nao reconhece TC.
TASK_REF = re.compile(r"\b(TC?)(\d+)\b")
TASK_HEADING = re.compile(r"^###\s+(TC?)(\d+)\s*:\s*(.+)$")
NO_DEPS = re.compile(r"^\s*(?:nenhuma|nenhum|none|n/?a|-)\s*$", re.IGNORECASE)
STRUCTURAL_RE = re.compile(
    r"gate|test|build|dotnet|npm|pytest|make|lint|contagem|count|compil|exit",
    re.IGNORECASE)

SECTION_MATRIX = ("Matriz de Cobertura", "Test Coverage Matrix")
SECTION_GATES = ("Comandos de Gate", "Gate Check Commands", "Gate Commands")
SECTION_PLAN = ("Plano de execução", "Plano de execucao", "Execution Plan")
SECTION_MAP = ("Mapa de execução", "Mapa de execucao", "Execution Map")


def task_refs(text):
    """IDs de task citados no texto, normalizados ('T1', 'TC2'), na ordem."""
    return [f"{fam}{num}" for fam, num in TASK_REF.findall(text)]


def task_key(tid):
    """Ordena T antes de TC, depois por numero."""
    fam, num = TASK_REF.match(tid).groups()
    return (fam, int(num))


def parse_tasks(lines):
    """Retorna (tasks, duplicates).
    tasks: tid -> {'line': idx, 'family': 'T'|'TC', 'num': int, 'title': str,
                   'fields': {key: (idx, value)}, 'dup_fields': [(idx, label)]}
    duplicates: [(idx, tid)] para cada heading repetido (a primeira vale)."""
    tasks = {}
    dups = []
    cur = None
    for i, l in enumerate(lines):
        m = TASK_HEADING.match(l)
        if m:
            tid = f"{m.group(1)}{m.group(2)}"
            if tid in tasks:
                dups.append((i, tid))
                cur = None  # corpo da duplicata nao sobrescreve a primeira
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
            for key, (aliases, _) in FIELDS.items():
                if any(label.startswith(a) for a in aliases):
                    if key in tasks[cur]["fields"]:
                        tasks[cur]["dup_fields"].append((i, aliases[0]))
                    else:
                        tasks[cur]["fields"][key] = (i, fm.group(2).strip())
                    break
    return tasks, dups


def parse_plan(lines):
    """Retorna (plan_ids, phase_of, sec).
    plan_ids: IDs citados na secao Plano de execucao, na ordem;
    phase_of: tid -> numero da fase ('### Fase N' / '### Phase N');
    sec: (start, end) ou None se a secao nao existe."""
    sec = find_section(lines, SECTION_PLAN)
    plan_ids, phase_of = [], {}
    if not sec:
        return plan_ids, phase_of, None
    cur = None
    for i in range(*sec):
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


def parse_map(lines):
    """IDs citados em ## Mapa de execucao, ou None se a secao nao existe."""
    sec = find_section(lines, SECTION_MAP)
    if not sec:
        return None
    ids = []
    for i in range(*sec):
        for t in task_refs(lines[i]):
            if t not in ids:
                ids.append(t)
    return ids


def table_header(lines, start, end):
    """Celulas do header da primeira tabela markdown da secao, em minusculas.
    Lista vazia se nao ha tabela."""
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


def check_tables(rep, lines, gates_used):
    """Matriz e Comandos de Gate: linhas de dados, celula de comando, cobertura
    dos valores de Gate usados nas tasks."""
    for aliases, label in ((SECTION_MATRIX, "Matriz de Cobertura"),
                           (SECTION_GATES, "Comandos de Gate")):
        sec = find_section(lines, aliases)
        if sec is None:
            continue  # ausencia ja reportada
        rows = table_rows(lines, *sec)
        if not rows:
            rep.hard(f"secao {label} sem linhas de dados na tabela", sec[0])
            continue
        header = table_header(lines, *sec)
        cmd_col = column_index(header, ("comando", "command"), len(header) - 1)
        for i, cells in rows:
            cmd = cells[cmd_col] if cmd_col < len(cells) else ""
            if not clean_cell(cmd):
                rep.hard(f"{label}: celula de comando vazia", i + 1)
        if aliases is SECTION_GATES:
            gate_col = column_index(header, ("gate",), 0)
            declared = {clean_cell(cells[gate_col]) for _, cells in rows if gate_col < len(cells)}
            for gate in sorted(gates_used):
                if gate not in declared:
                    tids = ", ".join(sorted(gates_used[gate], key=task_key))
                    rep.hard(f"Gate '{gate}' usado em {tids} sem linha na tabela Comandos de Gate")


def spec_ids(path):
    """(ids, has_delta, refactor): ids por tipo; has_delta e False quando a
    spec nao tem secao ADDED/MODIFIED Requirements (nao e spec-delta). Com o
    flag `no-behavior-change` (refactor=True), ids["INVARIANT"] traz os IDs
    citados no delta fora de bloco de codigo e do comentario de maquina, e
    has_delta e True."""
    lines = read_lines(path)
    ids = {"ADDED": set(), "MODIFIED": set(), "REMOVED": set(), "INVARIANT": set()}
    has_delta = False
    _, flags, mc_idx = parse_machine_comment(lines)
    refactor = bool(flags) and "no-behavior-change" in flags
    if refactor:
        mask = fenced_line_mask(lines)
        prefix = None
        for l in lines[:40]:
            pm = re.match(r"^\|\s*\*{0,2}\s*(?:prefixo|prefix)\s*\*{0,2}\s*\|\s*`?([A-Z][A-Z0-9]{1,9})`?", l, re.IGNORECASE)
            if pm:
                prefix = pm.group(1).upper()
                break
        for i, l in enumerate(lines):
            if i == mc_idx or mask[i]:
                continue
            for rid in REQ_ID.findall(l):
                if prefix is None or rid.startswith(prefix + "-"):
                    ids["INVARIANT"].add(rid)
        has_delta = True
    for kind in ids:
        sec = find_section(lines, (f"{kind} Requirements",))
        if sec:
            if kind in ("ADDED", "MODIFIED"):
                has_delta = True
            for i in range(*sec):
                m = REQ_LINE.match(lines[i])
                if m:
                    ids[kind].add(m.group(1))
    return ids, has_delta, refactor


def find_cycles(deps):
    """DFS sobre tid -> [deps]. Retorna lista de ciclos, cada um como lista de
    IDs fechada (['T1', 'T2', 'T1']); cada ciclo reportado uma vez."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {t: WHITE for t in deps}
    stack, cycles, seen = [], [], set()

    def visit(t):
        color[t] = GRAY
        stack.append(t)
        for d in deps.get(t, ()):
            if d not in color:
                continue  # inexistente: reportado a parte
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
    """Retorna (types, errors). types e lista normalizada; errors lista de
    mensagens (vazio = valido)."""
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
    """Existencia, ordem (numeracao/fase) e ciclos."""
    graph = {}
    for tid in sorted(tasks, key=task_key):
        t = tasks[tid]
        f = t["fields"]
        graph[tid] = []
        if "depends" not in f:
            continue
        idx, value = f["depends"]
        ln = idx + 1
        if not value:
            continue  # vazio ja reportado
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
                continue  # ciclo trivial: reportado pelo DFS
            dt = tasks[d]
            if t["family"] == "T" and dt["family"] == "TC":
                rep.hard(f"{tid}: depende de {d} - task de correcao nasce no Verify, depois de toda task T", ln)
                continue
            if tid in phase_of and d in phase_of and phase_of[d] > phase_of[tid]:
                rep.hard(f"{tid} (fase {phase_of[tid]}) depende de {d} (fase {phase_of[d]}) - dependencia para fase posterior", ln)
                continue
            if dt["family"] == t["family"] and dt["num"] >= t["num"]:
                same_or_earlier_phase = tid in phase_of and d in phase_of and phase_of[d] <= phase_of[tid]
                if not same_or_earlier_phase:
                    rep.hard(f"{tid}: depende de {d} (numero maior ou igual, sem fase anterior/igual no plano que justifique) - ordem errada", ln)
    for cyc in find_cycles(graph):
        first = tasks[cyc[0]]
        rep.hard(f"ciclo de dependencia: {' -> '.join(cyc)}", first["fields"]["depends"][0] + 1)


def check_plan(rep, tasks, plan_ids, plan_sec, map_ids):
    """Plano nos dois sentidos e Mapa de execucao == Plano."""
    if plan_sec is None:
        return  # ausencia ja reportada
    plan_line = plan_sec[0]
    for t in plan_ids:
        if t not in tasks:
            rep.hard(f"Plano de execucao cita {t}, que nao existe na lista de tasks", plan_line)
    for tid in sorted(tasks, key=task_key):
        if tasks[tid]["family"] == "TC":
            continue
        if tid not in plan_ids:
            rep.hard(f"{tid}: nao aparece no Plano de execucao", tasks[tid]["line"] + 1)
    if map_ids is not None:
        p = {t for t in plan_ids if not t.startswith("TC")}
        m = {t for t in map_ids if not t.startswith("TC")}
        if p != m:
            only_plan = ", ".join(sorted(p - m, key=task_key)) or "-"
            only_map = ", ".join(sorted(m - p, key=task_key)) or "-"
            rep.hard(f"Mapa de execucao diverge do Plano de execucao: so no plano: {only_plan}; so no mapa: {only_map}")


def check_done(rep, lines, tid, f):
    idx = f["done"][0]
    j = idx + 1
    crit, has_gate, has_behavior = 0, False, False
    while j < len(lines) and not re.match(r"^\s*[-*]\s+\*\*", lines[j]) and not lines[j].startswith("#"):
        cm = re.match(r"^\s*[-*]\s+\[[ x]\]\s*(.*)$", lines[j])
        if cm:
            crit += 1
            if STRUCTURAL_RE.search(cm.group(1)):
                has_gate = True
            else:
                has_behavior = True
        j += 1
    if crit == 0:
        rep.hard(f"{tid}: Pronto quando sem criterios '- [ ]'", idx + 1)
        return
    if not has_gate:
        rep.warn(f"{tid}: Pronto quando sem criterio referenciando o comando de gate", idx + 1)
    if not has_behavior:
        rep.warn(f"{tid}: criterios so estruturais; exit 0 nao prova regra de negocio", idx + 1)


def check_task(rep, lines, tid, t, gates_used, all_req_refs, commit_opts):
    f = t["fields"]
    ln = t["line"] + 1
    for idx, label in t["dup_fields"]:
        rep.hard(f"{tid}: campo duplicado: {label}", idx + 1)
    for key, (aliases, sev) in FIELDS.items():
        if key not in f:
            (rep.hard if sev == "hard" else rep.warn)(f"{tid}: campo obrigatorio ausente: {aliases[0]}", ln)
        elif key in SCALAR_FIELDS and not f[key][1]:
            rep.hard(f"{tid}: campo vazio: {aliases[0]}", f[key][0] + 1)
    if "where" in f and f["where"][1]:
        if not PATH_RE.findall(f["where"][1]):
            rep.warn(f"{tid}: Onde sem path de arquivo reconhecivel", f["where"][0] + 1)
    if "requirement" in f and f["requirement"][1]:
        refs = set(REQ_ID.findall(f["requirement"][1]))
        if not refs and not re.search(r"^\s*n/?a\s+(porque|because)\b", f["requirement"][1], re.IGNORECASE):
            rep.hard(f"{tid}: Requisito sem ID (task sem requisito e escopo escondido; refactor cita os IDs "
                     f"que preserva; excecao so 'N/A porque ...')", f["requirement"][0] + 1)
        all_req_refs |= refs

    test_types = []
    if "tests" in f and f["tests"][1]:
        test_types, errs = parse_tests(f["tests"][1])
        for e in errs:
            rep.hard(f"{tid}: Tests invalido: {e} (veio '{f['tests'][1][:40]}')", f["tests"][0] + 1)
        if not errs and test_types == ["none"]:
            rep.warn(f"{tid}: Tests: none - confirme contra a Matriz de Cobertura", f["tests"][0] + 1)
        if errs:
            test_types = []

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
    if gate == "quick" and test_types:
        if {"integration", "e2e"} & set(test_types):
            rep.hard(f"{tid}: Tests com integration/e2e exige Gate: full, veio quick", f["gate"][0] + 1)

    if "done" in f:
        check_done(rep, lines, tid, f)

    if "commit" in f:
        msg = f["commit"][1].strip("` ")
        if not msg:
            rep.warn(f"{tid}: Commit vazio - sem mensagem planejada (aceitavel quando commits nao estao autorizados)", f["commit"][0] + 1)
        else:
            for e in check_commit.check(msg, **commit_opts):
                rep.hard(f"{tid}: Commit invalido: {e}", f["commit"][0] + 1)


def parse_args(argv):
    """Retorna (path, spec, commit_opts). spec e None quando --spec ausente."""
    args = list(argv[1:])
    if not args or args[0].startswith("--"):
        usage(__doc__)
    path = args[0]
    spec = None
    commit_opts = {}
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--spec":
            spec = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif a == "--commit-max-len":
            raw = args[i + 1] if i + 1 < len(args) else ""
            if not raw.isdigit() or int(raw) <= 0:
                usage(f"--commit-max-len deve ser inteiro positivo, veio '{raw}'")
            commit_opts["max_len"] = int(raw)
            i += 2
        elif a == "--commit-no-scope":
            commit_opts["no_scope"] = True
            i += 1
        elif a == "--commit-no-bang":
            commit_opts["no_bang"] = True
            i += 1
        elif a == "--commit-single-line":
            commit_opts["single_line"] = True
            i += 1
        elif a == "--commit-lowercase":
            commit_opts["lowercase"] = True
            i += 1
        else:
            usage(f"opcao desconhecida: {a}\n\n{__doc__}")
    return path, spec, commit_opts


def main(argv):
    path, spec, commit_opts = parse_args(argv)
    lines = read_lines(path)
    rep = Report("lint_tasks")

    fields, flags, mc_idx = parse_machine_comment(lines)
    if fields is None or fields["sdd"].lower() != "tasks":
        rep.hard("primeira linha deve ser <!-- sdd: tasks | tier: ... | design: ... -->", 1)
        return rep.emit(path)
    if fields.get("tier", "").lower() not in TIERS:
        rep.hard("tier ausente ou invalido no comentario de maquina", 1)

    for aliases in (SECTION_MATRIX, SECTION_GATES, SECTION_PLAN):
        if find_section(lines, aliases) is None:
            rep.hard(f"secao ausente: ## {aliases[0]}")

    tasks, dups = parse_tasks(lines)
    for i, tid in dups:
        rep.hard(f"ID de task duplicado: {tid} (a primeira definicao vale; esta e ignorada)", i + 1)
    if not tasks:
        rep.hard("nenhuma task '### Tn: ...' ou '### TCn: ...' encontrada")
        return rep.emit(path)

    plan_ids, phase_of, plan_sec = parse_plan(lines)
    map_ids = parse_map(lines)
    gates_used = {}
    all_req_refs = set()

    for tid in sorted(tasks, key=task_key):
        check_task(rep, lines, tid, tasks[tid], gates_used, all_req_refs, commit_opts)
    check_dependencies(rep, tasks, phase_of)
    check_plan(rep, tasks, plan_ids, plan_sec, map_ids)
    check_tables(rep, lines, gates_used)

    if spec is None:
        rep.incomplete("validacao incompleta: --spec obrigatorio (cobertura requisito -> task nao verificada)")
    elif not spec or not os.path.exists(spec):
        rep.incomplete(f"validacao incompleta: spec nao encontrada: '{spec}'")
    else:
        ids, has_delta, refactor = spec_ids(spec)
        if not has_delta:
            rep.incomplete(f"validacao incompleta: {spec} sem secao ADDED/MODIFIED Requirements - so spec-delta serve de fonte de cobertura")
        elif refactor:
            for rid in sorted(all_req_refs - ids["INVARIANT"]):
                rep.hard(f"task referencia {rid}, que o delta de refactor nao lista como invariante (modes.md, Refactor)")
            for rid in sorted(ids["INVARIANT"] - all_req_refs):
                rep.warn(f"invariante {rid} do refactor sem task que o preserve (teste de characterization)")
        else:
            for rid in sorted(ids["ADDED"] | ids["MODIFIED"]):
                if rid not in all_req_refs:
                    rep.hard(f"requisito {rid} da spec sem task - codigo que nao vai existir")
            for rid in sorted(ids["REMOVED"]):
                if rid not in all_req_refs:
                    rep.warn(f"requisito REMOVED {rid} sem task que remova o comportamento/teste")
            known = ids["ADDED"] | ids["MODIFIED"] | ids["REMOVED"]
            for rid in sorted(all_req_refs - known):
                rep.warn(f"task referencia {rid}, que nao esta no delta (spec viva? verifique)")

    scan_placeholders(rep, lines, skip_first=mc_idx + 1)
    return rep.emit(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
