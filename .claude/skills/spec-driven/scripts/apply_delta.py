#!/usr/bin/env python3
"""
apply_delta.py - funde deterministicamente um delta de mudanca na spec viva
da capability (passo 1 do arquivamento em references/memory.md).

    Uso:
      python3 <skill-dir>/scripts/apply_delta.py apply <delta-spec.md> [--living <spec.md>]
                                                 [--create] [--date YYYY-MM-DD] [--dry-run]
      python3 <skill-dir>/scripts/apply_delta.py check <delta-spec.md> [--living <spec.md>]

Identidade da mudanca = nome do diretorio pai do delta (`NNNN-<slug>`,
ex. `0001-partial-reservation`). E a chave exata da linha de historico.

`apply` aplica ADDED / MODIFIED / REMOVED na lista da secao Requisitos da
spec viva, em ordem por ID, e acrescenta uma linha em Historico de revisoes
com TODOS os IDs afetados, explicitos e sem intervalo:
`+RSV-07, +RSV-08, ~RSV-03, -RSV-05`. RENAMED nao existe: IDs sao estaveis;
mude com REMOVED + ADDED.

Validacao integral antes de qualquer escrita (tudo-ou-nada): tipo dos
artefatos (`sdd: spec-delta` no delta, `sdd: spec` na viva), mesma
`capability` nos dois, IDs unicos no delta, linha com aparencia de requisito
nao reconhecida, MODIFIED/REMOVED com ID existente, MODIFIED com `Antes:`
igual ao texto vigente (divergencia = alteracao concorrente), ADDED com ID
inedito (nem existente nem aposentado no historico). Qualquer falha e HARD
e nada e escrito.

Replay: se o historico ja tem a linha da mudanca, `apply` nao reaplica.
Ultima linha e estado batendo -> "ja aplicado" (exit 0); ha linhas
posteriores -> "delta historico, superseded" (exit 0, nada tocado); ultima
linha e estado divergente -> HARD. Estado final presente sem linha de
historico e HARD (historico ausente/inconsistente), nunca "ja aplicado".

`check` nao escreve. Mudanca na ultima linha do historico: exige ADDED
presentes com texto identico, MODIFIED com o texto novo, REMOVED ausentes.
Mudanca com linhas posteriores (delta historico): exige so a linha do
historico e que os REMOVED continuem ausentes. Nunca recomenda reaplicar.

Regioes do script na spec viva (as unicas que ele escreve): a lista da
secao `## Requisitos`, o campo `**Data**` do header e a tabela de
`## Historico de revisoes`. Regioes do autor, nunca tocadas: Proposito,
Glossario, Domain Events e qualquer outra secao. A promessa "unica escrita
na spec viva" vale para as regioes do script. O documento novo e gerado em
memoria, revalidado, escrito em arquivo temporario no mesmo diretorio e
trocado com os.replace; em qualquer erro o original fica intacto. Encoding
(UTF-8 com ou sem BOM) e quebra de linha (CRLF ou LF) sao detectados no
original e preservados.

`--create` cria a spec viva a partir do delta (capability nova, so ADDED):
comentario de maquina com `capability`, `prd` e `prd-rev` quando existirem
no delta; header com Status, Data, Capability e Prefixo; Proposito copiado
do Contexto do delta e marcado para reescrita pelo autor; Domain Events
vazio; Glossario; Historico. Falha se a viva ja existe.

Exit codes: 0 ok / ja aplicado / superseded; 1 HARD; 2 uso.
"""

import argparse
import datetime
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    REQ_LINE, Report, find_section, parse_machine_comment,
)

ID_RE = r"[A-Z][A-Z0-9]{1,9}-\d{2,}"
BEFORE = re.compile(r"^\s+(Antes|Before):\s*(.+?)\s*$")
REASON = re.compile(r"^\s*(Raz[ãa]o|Reason)\s*:\s*(.+)$", re.IGNORECASE)
# Bullet que comeca com algo parecido com ID (bold opcional) mas nao casa
# REQ_LINE: `- **CHK-2** —`, `- **chk-01** —`, `- CHK-01 — ...`.
REQ_LIKE = re.compile(r"^\s*[-*]\s+\*{0,2}[A-Za-z][A-Za-z0-9]{0,9}-\d+\b")
EVENT_HINT = re.compile(r"\bpublic(?:ar|a|ate|ish)\b|\bemit(?:ir|e)\b", re.IGNORECASE)
CHANGE_NAME = re.compile(r"^\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
HIST_TOKEN = re.compile(rf"^([+~−-])({ID_RE})(?:\.\.(\d+))?$")
NO_CHANGE = ("sem mudança de requisito", "sem mudanca de requisito", "no requirement change")
SECTIONS = {
    "ADDED": ("ADDED Requirements", "ADDED"),
    "MODIFIED": ("MODIFIED Requirements", "MODIFIED"),
    "REMOVED": ("REMOVED Requirements", "REMOVED"),
}
RENAMED_ALIASES = ("RENAMED Requirements", "RENAMED")
LIVING_REQS = ("Requisitos", "Requirements")
LIVING_HIST = ("Histórico de revisões", "Historico de revisoes", "Revision History")
HEADER_FIELD = re.compile(r"^\|\s*\*\*([^*|]+)\*\*\s*\|\s*(.*?)\s*\|\s*$")


class Usage(Exception):
    """Erro de uso: exit 2."""


# --------------------------------------------------------------------------
# Leitura e escrita preservando BOM e quebra de linha
# --------------------------------------------------------------------------

class Document:
    def __init__(self, lines, bom=False, eol="\n", trailing=True):
        self.lines = lines
        self.bom = bom
        self.eol = eol
        self.trailing = trailing

    @classmethod
    def read(cls, path):
        with open(path, "rb") as f:
            raw = f.read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw[3:].decode("utf-8") if bom else raw.decode("utf-8")
        eol = "\r\n" if "\r\n" in text else "\n"
        text = text.replace("\r\n", "\n")
        trailing = text.endswith("\n")
        if trailing:
            text = text[:-1]
        return cls(text.split("\n") if text else [], bom, eol, trailing)

    def render(self, lines=None):
        lines = self.lines if lines is None else lines
        body = self.eol.join(lines) + (self.eol if self.trailing else "")
        return (b"\xef\xbb\xbf" if self.bom else b"") + body.encode("utf-8")


def write_atomic(path, data):
    """Escreve em temporario no mesmo diretorio e troca com os.replace."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".apply_delta-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def sort_key(rid):
    prefix, num = rid.rsplit("-", 1)
    return (prefix, int(num))


def collect(rep, lines, start, end, where):
    """[(idx, id, texto, antes)] das linhas de requisito em [start, end).
    Linha com aparencia de requisito que nao casa REQ_LINE e HARD."""
    out = []
    for i in range(start, end):
        m = REQ_LINE.match(lines[i])
        if not m:
            if REQ_LIKE.match(lines[i]):
                rep.hard(f"{where}: linha com aparencia de requisito nao reconhecida "
                         f"(forma exigida: `- **ID-nn** — texto`): {lines[i].strip()[:60]}", i + 1)
            continue
        before = None
        if i + 1 < end:
            b = BEFORE.match(lines[i + 1])
            if b:
                before = b.group(2)
        out.append((i, m.group(1), m.group(2).strip(), before))
    return out


def header_field(lines, name):
    for l in lines[:40]:
        m = HEADER_FIELD.match(l)
        if m and m.group(1).strip().lower() == name.lower():
            return m.group(2)
    return None


def change_name(delta_path):
    return os.path.basename(os.path.dirname(os.path.abspath(delta_path)))


def default_living(delta_path):
    """<...>/changes/<NNNN-slug>/spec.md -> <...>/spec.md"""
    d = os.path.dirname(os.path.abspath(delta_path))
    changes = os.path.dirname(d)
    if os.path.basename(changes) == "changes":
        return os.path.join(os.path.dirname(changes), "spec.md")
    return None


def parse_delta(rep, path):
    doc = Document.read(path)
    lines = doc.lines
    fields, flags, _ = parse_machine_comment(lines)
    fields = fields or {}
    flags = flags or set()
    if fields.get("sdd", "").lower() != "spec-delta":
        rep.hard(f"delta deve declarar `sdd: spec-delta` (encontrado: '{fields.get('sdd', '')}')", 1)
    if not fields.get("capability"):
        rep.hard("delta sem `capability:` no comentario de maquina", 1)
    change = change_name(path)
    if not CHANGE_NAME.match(change):
        rep.hard(f"identidade da mudanca invalida: diretorio pai do delta deve ser "
                 f"NNNN-<slug> (encontrado: '{change}')")
    if find_section(lines, RENAMED_ALIASES):
        rep.hard("RENAMED nao suportado: IDs sao estaveis; use REMOVED + ADDED")
    delta = {}
    for kind, aliases in SECTIONS.items():
        sec = find_section(lines, aliases)
        delta[kind] = collect(rep, lines, *sec, kind) if sec else []
    seen = {}
    for kind in SECTIONS:
        for i, rid, _, _ in delta[kind]:
            if rid in seen:
                rep.hard(f"{kind} {rid}: ID duplicado no delta (ja em {seen[rid]})", i + 1)
            else:
                seen[rid] = kind
    for i, rid, _, before in delta["MODIFIED"]:
        if before is None:
            rep.hard(f"MODIFIED {rid}: sem linha 'Antes:' com o texto anterior", i + 1)
    for i, rid, text, _ in delta["REMOVED"]:
        if not REASON.match(text):
            rep.warn(f"REMOVED {rid}: sem 'Razão:' explicita", i + 1)
    if not any(delta.values()) and "no-behavior-change" not in flags:
        rep.hard("delta sem requisitos em ADDED/MODIFIED/REMOVED "
                 "(refactor puro declara `no-behavior-change`)")
    return doc, fields, flags, delta, change


def parse_living(rep, doc, delta_fields):
    """Retorna (sec, reqs, hist) da spec viva. hist: (sec, rows) com rows =
    [(idx, change, {'+': ids, '~': ids, '-': ids})]."""
    lines = doc.lines
    fields, _, _ = parse_machine_comment(lines)
    fields = fields or {}
    if fields.get("sdd", "").lower() != "spec":
        rep.hard(f"spec viva deve declarar `sdd: spec` (encontrado: '{fields.get('sdd', '')}')", 1)
    cap_delta, cap_living = delta_fields.get("capability", ""), fields.get("capability", "")
    if cap_delta and cap_living != cap_delta:
        rep.hard(f"capability divergente: delta '{cap_delta}', spec viva '{cap_living}'", 1)
    sec = find_section(lines, LIVING_REQS)
    reqs = []
    if sec is None:
        rep.hard("spec viva sem secao '## Requisitos'")
    else:
        reqs = collect(rep, lines, *sec, "spec viva")
        seen = {}
        for i, rid, _, _ in reqs:
            if rid in seen:
                rep.hard(f"spec viva com ID duplicado {rid} (ja em L{seen[rid] + 1})", i + 1)
            seen[rid] = i
    hist = parse_history(rep, lines)
    return sec, reqs, hist


def parse_history(rep, lines):
    sec = find_section(lines, LIVING_HIST)
    if sec is None:
        rep.hard("spec viva sem '## Histórico de revisões'")
        return None, []
    rows = []
    seen_sep = False
    for i in range(*sec):
        s = lines[i].strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and cells:
            seen_sep = True
            continue
        if not seen_sep:
            continue
        if len(cells) < 3:
            rep.hard(f"historico: linha com menos de 3 colunas: {s[:60]}", i + 1)
            continue
        rows.append((i, cells[1], parse_history_ids(rep, cells[2], i)))
    return sec, rows


def parse_history_ids(rep, cell, idx):
    """'+AB-01, ~AB-02, -AB-03' -> {'+': [...], '~': [...], '-': [...]}.
    Intervalo legado '-AB-01..03' expande para AB-01, AB-02, AB-03."""
    out = {"+": [], "~": [], "-": []}
    cell = cell.strip()
    if not cell or cell.lower() in NO_CHANGE:
        return out
    for tok in (t.strip() for t in cell.split(",")):
        if not tok:
            continue
        m = HIST_TOKEN.match(tok)
        if not m:
            rep.hard(f"historico: token de ID nao reconhecido '{tok}'", idx + 1)
            continue
        sign = "-" if m.group(1) == "−" else m.group(1)
        rid, hi = m.group(2), m.group(3)
        if hi is None:
            out[sign].append(rid)
            continue
        prefix, lo = rid.rsplit("-", 1)
        if int(hi) < int(lo):
            rep.hard(f"historico: intervalo invalido '{tok}'", idx + 1)
            continue
        for n in range(int(lo), int(hi) + 1):
            out[sign].append(f"{prefix}-{str(n).zfill(len(lo))}")
    return out


def retired_ids(rows):
    return {rid for _, _, ids in rows for rid in ids["-"]}


def locate_change(rows, change):
    """(posicao da linha da mudanca, mudancas posteriores) ou (None, [])."""
    pos = [n for n, (_, name, _) in enumerate(rows) if name == change]
    if not pos:
        return None, []
    return pos[-1], [rows[n][1] for n in range(pos[-1] + 1, len(rows))]


# --------------------------------------------------------------------------
# Estado e validacao
# --------------------------------------------------------------------------

def state_findings(delta, reqs, full=True):
    """Divergencias entre o estado esperado apos o delta e a spec viva.
    full=False confere so os REMOVED (auditoria de delta historico)."""
    by_id = {rid: text for _, rid, text, _ in reqs}
    out = []
    if full:
        for _, rid, text, _ in delta["ADDED"]:
            if rid not in by_id:
                out.append(f"ADDED {rid} ausente na spec viva")
            elif by_id[rid] != text:
                out.append(f"ADDED {rid} com texto divergente da spec viva")
        for _, rid, text, _ in delta["MODIFIED"]:
            if rid not in by_id:
                out.append(f"MODIFIED {rid} ausente na spec viva")
            elif by_id[rid] != text:
                out.append(f"MODIFIED {rid} nao reflete o texto novo do delta")
    for _, rid, _, _ in delta["REMOVED"]:
        if rid in by_id:
            out.append(f"REMOVED {rid} ainda presente na spec viva")
    return out


def validate(rep, delta, reqs, retired):
    by_id = {rid: text for _, rid, text, _ in reqs}
    for kind in ("MODIFIED", "REMOVED"):
        for i, rid, _, _ in delta[kind]:
            if rid not in by_id:
                rep.hard(f"{kind} {rid}: ID inexistente na spec viva", i + 1)
    for i, rid, _, before in delta["MODIFIED"]:
        if rid in by_id and before is not None and by_id[rid] != before:
            rep.hard(f"MODIFIED {rid}: 'Antes:' difere do texto vigente na spec viva "
                     f"(alteracao concorrente; revise o delta). Vigente: {by_id[rid][:60]}", i + 1)
    for i, rid, _, _ in delta["ADDED"]:
        if rid in by_id:
            rep.hard(f"ADDED {rid}: ID ja existe na spec viva - IDs nao sao reusados", i + 1)
        elif rid in retired:
            rep.hard(f"ADDED {rid}: ID aposentado no historico - "
                     f"ID de requisito removido morre, nao e reciclado", i + 1)


# --------------------------------------------------------------------------
# Merge
# --------------------------------------------------------------------------

def render_req(rid, text):
    return f"- **{rid}** — {text}"


def is_ordered(reqs):
    return all(sort_key(a[1]) < sort_key(b[1]) for a, b in zip(reqs, reqs[1:]))


def merge(living_lines, delta, sec, reqs):
    """Novas linhas da spec viva; toca so a lista de requisitos."""
    by_id = {rid: (i, text) for i, rid, text, _ in reqs}
    out = list(living_lines)

    for _, rid, text, _ in delta["MODIFIED"]:
        out[by_id[rid][0]] = render_req(rid, text)

    drop = {by_id[rid][0] for _, rid, _, _ in delta["REMOVED"]}

    survivors = [(i, rid) for i, rid, _, _ in reqs if i not in drop]
    ordered = all(sort_key(a[1]) < sort_key(b[1]) for a, b in zip(survivors, survivors[1:]))
    cursor = survivors[-1][0] + 1 if survivors else sec[1]
    insertions = []
    for _, rid, text, _ in sorted(delta["ADDED"], key=lambda r: sort_key(r[1])):
        pos = cursor
        if ordered and survivors:
            for i, existing in survivors:
                if sort_key(rid) < sort_key(existing):
                    pos = i
                    break
        insertions.append((pos, render_req(rid, text)))
        survivors = sorted(survivors + [(pos, rid)], key=lambda t: t[0])

    ins_by_pos = {}
    for pos, line in insertions:
        ins_by_pos.setdefault(pos, []).append(line)
    result = []
    for i, line in enumerate(out):
        result.extend(ins_by_pos.pop(i, []))
        if i in drop:
            continue
        result.append(line)
    for pos in sorted(ins_by_pos):
        result.extend(ins_by_pos[pos])
    spaced = []
    for i, line in enumerate(result):
        spaced.append(line)
        if REQ_LINE.match(line) and i + 1 < len(result) and result[i + 1].startswith("#"):
            spaced.append("")
    return spaced, ordered


def history_ids(delta):
    parts = []
    for sign, kind in (("+", "ADDED"), ("~", "MODIFIED"), ("-", "REMOVED")):
        parts.extend(f"{sign}{rid}" for rid in sorted((r[1] for r in delta[kind]), key=sort_key))
    return ", ".join(parts) or NO_CHANGE[0]


def history_line(date, change, delta):
    return f"| {date} | {change} | {history_ids(delta)} |"


def insert_history(lines, line):
    start, end = find_section(lines, LIVING_HIST)
    last = start
    for i in range(start, end):
        if lines[i].strip().startswith("|"):
            last = i
    return lines[:last + 1] + [line] + lines[last + 1:]


def touch_date(lines, date, change):
    for i, l in enumerate(lines[:40]):
        m = HEADER_FIELD.match(l)
        if m and m.group(1).strip().lower() in ("data", "date"):
            lines[i] = f"| **{m.group(1).strip()}** | {date} (última mudança: {change}) |"
            break
    return lines


def revalidate(rep, merged, delta, change, was_ordered):
    """Confere o documento gerado em memoria antes de escrever."""
    sec = find_section(merged, LIVING_REQS)
    if sec is None:
        rep.hard("revalidacao: secao '## Requisitos' ausente no documento gerado")
        return
    tmp = Report("revalidacao")
    reqs = collect(tmp, merged, *sec, "revalidacao")
    ids = [rid for _, rid, _, _ in reqs]
    if len(ids) != len(set(ids)):
        rep.hard("revalidacao: ID duplicado no documento gerado")
    if was_ordered and not is_ordered(reqs):
        rep.hard("revalidacao: lista de requisitos perdeu a ordem por ID")
    if state_findings(delta, reqs):
        rep.hard("revalidacao: documento gerado nao reflete o delta")
    hsec = find_section(merged, LIVING_HIST)
    hits = 0
    if hsec:
        for i in range(*hsec):
            cells = [c.strip() for c in merged[i].strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[1] == change:
                hits += 1
    if hits != 1:
        rep.hard(f"revalidacao: historico com {hits} linha(s) para '{change}'; esperado 1")


# --------------------------------------------------------------------------
# --create
# --------------------------------------------------------------------------

def new_living(delta_doc, fields, delta, date, change):
    lines = delta_doc.lines
    capability = fields.get("capability", "")
    title = capability.rsplit("/", 1)[-1].replace("-", " ").title()
    comment = [f"capability: {capability}"]
    for k in ("prd", "prd-rev"):
        if fields.get(k):
            comment.append(f"{k}: {fields[k]}")
    prefix = header_field(lines, "Prefixo") or header_field(lines, "Prefix")
    if not prefix:
        prefixes = {rid.rsplit("-", 1)[0] for _, rid, _, _ in delta["ADDED"]}
        prefix = prefixes.pop() if len(prefixes) == 1 else None
    ctx = find_section(lines, ("Contexto", "Context"))
    purpose = "\n".join(lines[ctx[0]:ctx[1]]).strip() if ctx else ""
    header = [
        "| | |",
        "|---|---|",
        "| **Status** | Vigente |",
        f"| **Data** | {date} (última mudança: {change}) |",
        f"| **Capability** | {capability} |",
    ]
    if prefix:
        header.append(f"| **Prefixo** | {prefix} |")
    out = [
        f"<!-- sdd: spec | {' | '.join(comment)} -->",
        f"# {title} — Spec",
        "",
        *header,
        "",
        "## Propósito (Purpose)",
        "",
        "> Herdado do Contexto do delta pelo `--create`; reescrever no escopo da capability.",
        "",
    ]
    out.extend(purpose.split("\n") if purpose else [])
    out.extend([
        "",
        "## Requisitos (Requirements)",
        "",
        "## Domain Events",
        "",
        "| Evento | Produtor | Consumidores | Payload semântico | Gatilho |",
        "|---|---|---|---|---|",
        "",
        "## Glossário",
        "",
        "## Histórico de revisões",
        "",
        "| Data | Mudança | IDs afetados |",
        "|---|---|---|",
    ])
    return Document(out, bom=False, eol=delta_doc.eol, trailing=True)


# --------------------------------------------------------------------------
# Comandos
# --------------------------------------------------------------------------

def resolve_living(args):
    living = args.living or default_living(args.delta)
    if not living:
        raise Usage("apply_delta: nao consegui inferir a spec viva "
                    "(delta fora de changes/<NNNN-slug>/); passe --living")
    return living


def cmd_apply(args):
    rep = Report("apply_delta")
    ddoc, fields, flags, delta, change = parse_delta(rep, args.delta)
    living = resolve_living(args)
    date = args.date or datetime.date.today().isoformat()

    created = False
    if args.create:
        if os.path.isfile(living):
            rep.hard(f"--create com spec viva ja existente: {living}")
            return rep.emit(args.delta)
        if delta["MODIFIED"] or delta["REMOVED"]:
            rep.hard("capability nova so admite ADDED; ha MODIFIED/REMOVED no delta")
        if rep.hard_findings:
            return rep.emit(args.delta)
        ldoc = new_living(ddoc, fields, delta, date, change)
        created = True
    elif not os.path.isfile(living):
        rep.hard(f"spec viva inexistente: {living} (use --create para capability nova)")
        return rep.emit(args.delta)
    else:
        ldoc = Document.read(living)
    if rep.hard_findings:
        return rep.emit(args.delta)

    sec, reqs, (hsec, rows) = parse_living(rep, ldoc, fields)
    if rep.hard_findings:
        return rep.emit(args.delta)

    pos, later = locate_change(rows, change)
    if pos is not None:
        if later:
            print(f"apply_delta: delta historico, superseded por {', '.join(later)}; "
                  f"nao reaplique. Nada tocado em {living}.")
            return rep.emit(args.delta)
        diffs = state_findings(delta, reqs)
        if diffs:
            for d in diffs:
                rep.hard(f"estado inconsistente com o historico ('{change}' e a ultima "
                         f"mudanca): {d}")
            return rep.emit(args.delta)
        print(f"apply_delta: '{change}' ja aplicado em {living}; nada a fazer.")
        return rep.emit(args.delta)

    if any(delta.values()) and not state_findings(delta, reqs):
        rep.hard(f"estado final do delta ja presente na spec viva sem linha de historico "
                 f"para '{change}': historico ausente/inconsistente; nao escrevo")
        return rep.emit(args.delta)

    validate(rep, delta, reqs, retired_ids(rows))
    if rep.hard_findings:
        return rep.emit(args.delta)

    was_ordered = is_ordered(reqs)
    merged, ordered = merge(ldoc.lines, delta, sec, reqs)
    if not ordered and delta["ADDED"]:
        rep.warn("lista de requisitos da spec viva fora de ordem por ID - "
                 "ADDED inseridos ao fim da secao")
    merged = touch_date(merged, date, change)
    merged = insert_history(merged, history_line(date, change, delta))
    revalidate(rep, merged, delta, change, was_ordered)
    if rep.hard_findings:
        return rep.emit(args.delta)

    for _, rid, text, _ in delta["ADDED"]:
        if EVENT_HINT.search(text):
            rep.warn(f"{rid} publica evento - atualize a tabela Domain Events da spec viva "
                     f"(o script nao infere payload nem consumidores)")

    data = ldoc.render(merged)
    if args.dry_run:
        sys.stdout.write(data.decode("utf-8").lstrip("﻿"))
        print(f"apply_delta: dry-run, nada escrito em {living}.")
        return rep.emit(args.delta)
    try:
        write_atomic(living, data)
    except OSError as e:
        rep.hard(f"falha ao escrever {living}: {e}; original intacto")
        return rep.emit(args.delta)
    verb = "criada" if created else "atualizada"
    n = len(delta["ADDED"]), len(delta["MODIFIED"]), len(delta["REMOVED"])
    print(f"apply_delta: spec viva {verb} - {living} "
          f"(+{n[0]} ~{n[1]} -{n[2]}). Rode lint_spec.py nela.")
    return rep.emit(args.delta)


def cmd_check(args):
    rep = Report("apply_delta --check")
    _, fields, _, delta, change = parse_delta(rep, args.delta)
    living = resolve_living(args)
    if not os.path.isfile(living):
        rep.hard(f"spec viva nao encontrada: {living}")
        return rep.emit(args.delta)
    ldoc = Document.read(living)
    _, reqs, (_, rows) = parse_living(rep, ldoc, fields)
    if rep.hard_findings:
        return rep.emit(args.delta)

    pos, later = locate_change(rows, change)
    if pos is None:
        rep.hard(f"historico de revisoes sem linha para a mudanca '{change}'")
        return rep.emit(args.delta)
    if later:
        print(f"apply_delta --check: '{change}' e delta historico, superseded por "
              f"{', '.join(later)}; auditoria restrita a linha do historico e REMOVED ausentes.")
        for d in state_findings(delta, reqs, full=False):
            rep.hard(d)
        return rep.emit(args.delta)
    for d in state_findings(delta, reqs):
        rep.hard(d)
    return rep.emit(args.delta)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("apply", cmd_apply), ("check", cmd_check)):
        sp = sub.add_parser(name)
        sp.add_argument("delta", help="changes/<NNNN-slug>/spec.md")
        sp.add_argument("--living", help="spec viva da capability; inferida do path se omitida")
        if name == "apply":
            sp.add_argument("--create", action="store_true",
                            help="capability nova: cria a spec viva a partir do delta")
            sp.add_argument("--date", help="data do historico (default: hoje)")
            sp.add_argument("--dry-run", action="store_true",
                            help="imprime o resultado sem escrever")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    if not os.path.isfile(args.delta):
        print(f"apply_delta: delta inexistente: {args.delta}", file=sys.stderr)
        return 2
    try:
        return args.fn(args)
    except Usage as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
