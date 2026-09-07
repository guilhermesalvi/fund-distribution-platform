#!/usr/bin/env python3
"""
lint_spec.py - verificacao deterministica de um spec.md (delta ou spec viva)
gerado pela skill spec-driven.

    Uso:  python3 <skill-dir>/scripts/lint_spec.py <spec.md> [--living <spec-viva.md>]
          python3 <skill-dir>/scripts/lint_spec.py --print-prd-rev <prd.md>

Checa o esqueleto: comentario de maquina, header (campos obrigatorios, Status
valido, Data AAAA-MM-DD real, Autor sem placeholder, Prefixo igual ao dos IDs),
secoes por tier (heading casa por igualdade com os aliases PT/EN, nunca por
prefixo; secao duplicada e HARD), requisitos EARS-shaped (SHALL), IDs bem
formados e unicos, linha com aparencia de requisito nao reconhecida (HARD),
MODIFIED com `Antes:` apontando para ID existente na spec viva e igual ao texto
vigente nela (HARD se divergente: alteracao concorrente, mesma regra do
apply_delta.py), REMOVED com razao, RENAMED nao suportado (IDs sao estaveis),
assumptions sem default vazio,
tags de confianca, [PREMISSA-CRÍTICA] com "se falsa", rastreabilidade cobrindo
todo ID, cenarios herdados do PRD, Ponto de Maior Fragilidade, placeholders,
hedging e meta-narracao. Tudo que esta dentro de bloco de codigo (``` ou ~~~)
e ignorado.

Com `prd:` no comentario de maquina, le a pasta do PRD (`/docs/prd`, layout
flat ou nested) e checa: PRD nao encontrado (HARD INCOMPLETO); `prd-rev:`
ausente (WARN) ou divergente da revisao atual do arquivo (HARD); o prefixo da
spec nao coincide com prefixo de PRD (HARD); toda citacao de ID de PRD resolve
para uma definicao `- **X-nn (Must)**` / `- **X-NFR-nn**` em algum PRD da
pasta (HARD); citacao com prefixo que nenhum PRD declara (HARD ao fim de um
requisito, WARN em prosa); cada cenario herdado cita ID do PRD ou casa um caso
da tabela de Criterios de Aceitacao (HARD); spec a partir do PRD sem nenhuma
citacao de ID do PRD (WARN). Path `/docs/...` e resolvido a partir da raiz do
repositorio (ancestral da spec que contem `docs/`).

Links Markdown `[texto](destino)` para arquivo local resolvem (HARD quando nao):
destino relativo a partir da pasta da spec, `/docs/...` a partir da raiz do
repositorio; ancora `#...` e removida antes de resolver. URL com esquema
(`https:`, `mailto:`), ancora pura (`#secao`) e o que esta em bloco de codigo
ou em code span ficam fora.

`prd-rev:` e `git:<hash>` (saida de `git hash-object <prd.md>`) ou
`sha256:<12 hex>` do conteudo com quebras normalizadas para LF;
`--print-prd-rev` imprime o valor a usar.

Saida: HARD (exit 1) / WARN (nao afeta exit). HARD com prefixo INCOMPLETO
marca validacao incompleta (fonte ausente, git indisponivel), nao violacao.
Exit 2 em erro de uso: opcao desconhecida, `--living` sem valor, arquivo
ausente ou fora de UTF-8.

NAO julga semantica. Linter verde = esqueleto conforme, nao spec boa.
"""

import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    REQ_ID, REQ_LINE, TIERS, Report, check_tags, content_rev, fenced_line_mask,
    find_section_exact, find_sections_exact, git_blob_rev, iter_headings,
    norm_heading, parse_machine_comment, read_lines, scan_placeholders,
    scan_prose, strip_accents, table_rows, usage,
)

EARS_LEAD = re.compile(r"^\s*(WHEN|WHILE|WHERE|IF)\b", re.IGNORECASE)
PRD_ID = re.compile(r"\b([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})\b")
PRD_DEF = re.compile(r"^\s*[-*]\s+\*\*([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})(?:\s*\([^)]*\))?\*\*")
PRD_PREFIX_LINE = re.compile(
    r"^\s*(?:Prefixo dos requisitos|Requirement prefix|Prefixo|Prefix)\s*:\s*`?([A-Z][A-Z0-9]{1,9})`?",
    re.IGNORECASE)
UBIQ = re.compile(r"^\s*(the\s+\w+|o\s+sistema|a\s+\w+|the\s+system)\s+shall\b", re.IGNORECASE)
REQ_LOOKALIKE = re.compile(r"^\s*[-*]\s+\*\*")
PREFIX_FORM = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")
DATE_LEAD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:\b|$)")
PRD_REV = re.compile(r"^(git:[0-9a-f]{40,64}|sha256:[0-9a-f]{12})$")

STATUS_DELTA = {"rascunho", "aprovado", "em andamento", "concluido", "descartado",
                "bloqueado", "draft", "approved", "in progress", "done", "discarded",
                "blocked"}
# Spike promovido: "Promovido a <mudanca>" / "Promoted to <change>" (modes.md).
STATUS_DELTA_PREFIX = ("promovido a ", "promoted to ")
STATUS_LIVING = {"vigente", "current"}
HEADER_FIELDS = {
    # chave -> (rotulos aceitos, obrigatorio em delta, obrigatorio em viva)
    "status": (("status",), True, True),
    "autor": (("autor", "author"), True, False),
    "data": (("data", "date"), True, True),
    "capability": (("capability",), True, True),
    "prefixo": (("prefixo", "prefix"), True, True),
}

DELTA_SECTIONS = {
    # alias list -> tiers em que e obrigatoria (casamento exato apos norm_heading)
    ("Contexto", "Context"): {"small", "medium", "large", "complex"},
    ("Premissas e Perguntas em Aberto", "Premissas e Perguntas", "Assumptions & Open Questions",
     "Assumptions and Open Questions", "Assumptions"): {"medium", "large", "complex"},
    ("Rastreabilidade", "Requirement Traceability", "Traceability"): {"medium", "large", "complex"},
    ("Escopo e Fora de Escopo", "Escopo", "Scope / Out of Scope", "Scope"): {"medium", "large", "complex"},
    ("Histórias", "User Stories"): {"medium", "large", "complex"},
    ("Ponto de Maior Fragilidade", "Weakest Point"): {"medium", "large", "complex"},
    ("Dimensões Implícitas", "Implicit Dimensions"): {"large", "complex"},
    ("Critérios de Sucesso", "Success Criteria"): {"large", "complex"},
}
LIVING_SECTIONS = [
    ("Propósito", "Purpose"),
    ("Requisitos", "Requirements"),
    ("Histórico de revisões", "Revision History"),
]
DELTA_REQ_SECTIONS = {
    "ADDED": ("ADDED Requirements", "ADDED"),
    "MODIFIED": ("MODIFIED Requirements", "MODIFIED"),
    "REMOVED": ("REMOVED Requirements", "REMOVED"),
    "RENAMED": ("RENAMED Requirements", "RENAMED"),
}
TRACE_ALIASES = ("Rastreabilidade", "Requirement Traceability", "Traceability")
ASSUMPTION_ALIASES = ("Premissas e Perguntas em Aberto", "Premissas e Perguntas",
                      "Assumptions & Open Questions", "Assumptions and Open Questions", "Assumptions")
DIMENSION_ALIASES = ("Dimensões Implícitas", "Implicit Dimensions")
SCENARIO_HEADER = {"cenario do prd", "prd scenario"}
ACCEPTANCE_ALIASES = ("Critérios de Aceitação", "Acceptance Criteria")


def norm_cell(s):
    return norm_heading(re.sub(r"[*`]", "", s))


def collect_reqs(rep, lines, start, end, mask, label):
    """Requisitos (idx, id, texto) da faixa; linha de lista `- **...**` que
    nao casa REQ_LINE e HARD (aparencia de requisito nao reconhecida)."""
    out = []
    for i in range(start, end):
        if mask[i]:
            continue
        m = REQ_LINE.match(lines[i])
        if m:
            out.append((i, m.group(1), m.group(2)))
        elif REQ_LOOKALIKE.match(lines[i]):
            rep.hard(f"{label}: linha com aparencia de requisito nao reconhecida "
                     f"(forma: `- **PFX-NN** — texto`): '{lines[i].strip()[:60]}'", i + 1)
    return out


def check_ears(rep, reqs, label):
    for i, rid, text in reqs:
        if not re.search(r"\bSHALL\b", text):
            rep.hard(f"{label} {rid}: requisito sem SHALL (nao testavel / nao EARS)", i + 1)
        elif not (EARS_LEAD.match(text) or UBIQ.match(text)):
            rep.warn(f"{label} {rid}: SHALL presente mas sem padrao EARS reconhecido "
                     f"(WHEN/WHILE/WHERE/IF ou 'The <system> SHALL')", i + 1)
        if re.search(r"\bSHALL\b.*\bSHALL\b", text):
            rep.warn(f"{label} {rid}: dois SHALL na mesma linha - um requisito por linha?", i + 1)
        low = text.lower()
        for v in ("rapidamente", "graciosamente", "apropriad", "adequadament", "quickly",
                  "gracefully", "appropriately", "efficiently"):
            if v in low:
                rep.warn(f"{label} {rid}: termo vago '{v}' - use valor concreto", i + 1)
                break


def living_texts(path):
    """{id: texto} dos requisitos da spec viva (fora de bloco de codigo)."""
    out = {}
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        m = REQ_LINE.match(l)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def living_ids(path):
    ids = set()
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    for i, l in enumerate(lines):
        m = REQ_LINE.match(l)
        if m and not mask[i]:
            ids.add(m.group(1))
    return ids


def resolve_local_path(doc_path, target):
    """Path absoluto de um destino local citado por um documento: como esta,
    relativo ao documento, ou `/docs/...` a partir da raiz do repositorio
    (primeiro ancestral do documento que contem `docs/`). None se nada existe."""
    cands = []
    if os.path.isabs(target) and os.path.exists(target):
        return target
    base = os.path.dirname(os.path.abspath(doc_path))
    cands.append(os.path.normpath(os.path.join(base, target)))
    rel = target.lstrip("/\\")
    cur = base
    while True:
        if os.path.isdir(os.path.join(cur, "docs")):
            cands.append(os.path.normpath(os.path.join(cur, rel)))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def prd_index(prd_path):
    """(definicoes, prefixos) de todos os .md da pasta de PRDs (ancestral `prd`)."""
    d = os.path.dirname(os.path.abspath(prd_path)) if os.path.isfile(prd_path) else prd_path
    root = d
    cur = d
    while True:
        if os.path.basename(cur).lower() in ("prd", "prds"):
            root = cur
            break
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    defs, prefixes = set(), set()
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [x for x in dirnames if not x.startswith(".") and x not in ("assets", "node_modules")]
        for f in files:
            if not f.endswith(".md") or f.lower() == "readme.md":
                continue
            plines = read_lines(os.path.join(dirpath, f))
            pmask = fenced_line_mask(plines)
            for i, l in enumerate(plines):
                if pmask[i]:
                    continue
                m = PRD_DEF.match(l)
                if m:
                    defs.add(f"{m.group(1)}-{m.group(2) or ''}{m.group(3)}")
                pm = PRD_PREFIX_LINE.match(l)
                if pm:
                    prefixes.add(pm.group(1))
    return defs, prefixes


def prd_acceptance_cases(prd_path):
    """Primeira coluna da primeira tabela da secao Criterios de Aceitacao do
    PRD, normalizada. None se a secao nao existe."""
    plines = read_lines(prd_path)
    pmask = fenced_line_mask(plines)
    sec = find_section_exact(plines, ACCEPTANCE_ALIASES, mask=pmask)
    if sec is None:
        return None
    return {norm_cell(cells[0]) for _, cells in table_rows(plines, *sec) if cells and cells[0]}


def check_prd_rev(rep, fields, prd_path):
    declared = fields.get("prd-rev")
    if not declared:
        rep.warn("proveniencia sem revisao; adicione prd-rev "
                 "(lint_spec.py --print-prd-rev <prd.md>)", 1)
        return
    if not PRD_REV.match(declared):
        rep.hard(f"prd-rev '{declared}' invalido: use git:<hash de `git hash-object`> ou sha256:<12 hex>", 1)
        return
    if declared.startswith("git:"):
        actual = git_blob_rev(prd_path)
        if actual is None:
            rep.incomplete("prd-rev declarado como git: mas git indisponivel para calcular a revisao do PRD", 1)
            return
    else:
        actual = content_rev(prd_path)
    if actual != declared:
        rep.hard(f"PRD mudou desde a spec; re-derive (prd-rev declarado {declared}, atual {actual})", 1)


def is_citation_at_end(line, rid):
    """ID entre colchetes ao fim de uma linha de requisito (comentario HTML
    opcional depois)."""
    if not REQ_LINE.match(line):
        return False
    tail = re.sub(r"<!--.*?-->\s*$", "", line).rstrip()
    m = re.search(r"\[([^\[\]]*)\]\s*$", tail)
    return bool(m and re.search(rf"\b{re.escape(rid)}\b", m.group(1)))


def lint_inherited_scenarios(rep, lines, mask, defs, prefixes, spec_ids, spec_prefix, prd_path):
    sec = find_section_exact(lines, TRACE_ALIASES, mask=mask)
    if sec is None:
        return
    start, end = sec
    header = None
    for i in range(start, end):
        l = lines[i].strip()
        if mask[i] or not l.startswith("|"):
            continue
        cells = [c.strip() for c in l.strip("|").split("|")]
        if cells and norm_cell(cells[0]) in SCENARIO_HEADER:
            header = i
            break
    if header is None:
        return
    cases = prd_acceptance_cases(prd_path)
    if cases is None:
        rep.warn(f"PRD {os.path.basename(prd_path)} sem secao Criterios de Aceitacao; "
                 "cenarios herdados so validam por ID", header + 1)
        cases = set()
    for i, cells in table_rows(lines, header, end):
        if mask[i] or not cells:
            continue
        name = cells[0]
        row = " | ".join(cells)
        resolved = any(f"{m.group(1)}-{m.group(2) or ''}{m.group(3)}" in defs
                       for m in PRD_ID.finditer(row) if m.group(1) in prefixes)
        if not resolved and norm_cell(name) not in cases:
            rep.hard(f"cenario herdado '{name[:50]}' nao cita ID do PRD que resolve nem casa um caso "
                     "da tabela de Criterios de Aceitacao do PRD", i + 1)
        if len(cells) >= 2:
            for rid in REQ_ID.findall(cells[1]):
                if rid.rsplit("-", 1)[0] == spec_prefix and rid not in spec_ids:
                    rep.hard(f"cenario herdado '{name[:40]}': requisito EARS {rid} nao existe no delta", i + 1)


MD_LINK = re.compile(r"\[[^\]]*\]\(\s*(?:<([^>]*)>|([^)\s]+))(?:\s+\"[^\"]*\")?\s*\)")  # destino em <...> (com espacos) ou sem espacos
URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
CODE_SPAN = re.compile(r"`[^`]*`")


def link_target(m):
    """Destino de um match de MD_LINK: forma <...> ou forma simples."""
    return m.group(1) if m.group(1) is not None else m.group(2)


def check_local_links(rep, lines, mask, doc_path):
    """Todo link Markdown para arquivo local resolve: destino relativo so a
    partir da pasta do documento (como o GitHub renderiza), `/docs/...` a
    partir da raiz do repositorio. URL e ancora pura ficam fora. HARD com a
    linha e o path onde o destino foi procurado."""
    base = os.path.dirname(os.path.abspath(doc_path))
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        for m in MD_LINK.finditer(CODE_SPAN.sub("", l)):
            raw = link_target(m).strip()
            if not raw or URL_SCHEME.match(raw) or raw.startswith("#"):
                continue
            target = raw.split("#", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                ok = resolve_local_path(doc_path, target) is not None
                expected = f"<raiz do repositorio>{target}"
            else:
                expected = os.path.normpath(os.path.join(base, target))
                ok = os.path.exists(expected)
            if not ok:
                rep.hard(f"link '{raw}' nao resolve (procurado em {expected}); "
                         "conte os `../` a partir da pasta deste arquivo", i + 1)


def lint_prd_links(rep, lines, mask, fields, spec_path, spec_ids, spec_prefix, is_delta):
    prd_field = fields.get("prd")
    if not prd_field:
        if fields.get("prd-rev"):
            rep.warn("prd-rev sem prd: no comentario de maquina; revisao nao verificada", 1)
        return
    prd_path = resolve_local_path(spec_path, prd_field)
    if not prd_path:
        rep.incomplete(f"validacao incompleta: PRD nao encontrado ('{prd_field}'); "
                       "prefixo, citacoes e cenarios herdados nao verificados", 1)
        return
    check_prd_rev(rep, fields, prd_path)
    defs, prefixes = prd_index(prd_path)
    spec_prefixes = {rid.rsplit("-", 1)[0] for rid in spec_ids}
    if spec_prefix:
        spec_prefixes.add(spec_prefix)
    for pfx in sorted(spec_prefixes & prefixes):
        rep.hard(f"prefixo da spec '{pfx}' coincide com prefixo de PRD em {os.path.dirname(prd_path)}; "
                 "IDs de spec e de PRD tem a mesma forma X-nn - use outro prefixo (specify.md, Origem e modo)")
    cited = 0
    seen = set()
    for i, l in enumerate(lines):
        if mask[i] or l.strip().startswith("<!--"):
            continue
        for m in PRD_ID.finditer(l):
            pfx = m.group(1)
            if pfx in spec_prefixes:
                continue
            rid = f"{pfx}-{m.group(2) or ''}{m.group(3)}"
            if (rid, i) in seen:
                continue
            seen.add((rid, i))
            if pfx not in prefixes:
                msg = f"citacao de {rid}: prefixo '{pfx}' nao e declarado por nenhum PRD da pasta"
                if is_citation_at_end(l, rid):
                    rep.hard(msg, i + 1)
                else:
                    rep.warn(msg + " (em prosa; confirme que nao e citacao)", i + 1)
                continue
            cited += 1
            if rid not in defs:
                rep.hard(f"citacao de {rid} nao resolve para definicao em nenhum PRD da pasta", i + 1)
    if cited == 0:
        rep.warn("spec a partir do PRD sem nenhuma citacao de ID do PRD; requisitos EARS citam "
                 "o ID com prefixo e a Rastreabilidade lista PRD -> EARS (specify.md)")
    if is_delta:
        lint_inherited_scenarios(rep, lines, mask, defs, prefixes, spec_ids, spec_prefix, prd_path)


def parse_header(lines, h1):
    """dict chave -> (valor, idx) dos campos da tabela de header; None se a
    tabela nao existe logo abaixo do H1."""
    i = h1 + 1
    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith("<!--")):
        i += 1
    if i >= len(lines) or not lines[i].lstrip().startswith("|"):
        return None, i
    out = {}
    for idx, cells in table_rows(lines, i, min(i + 14, len(lines))):
        if not cells:
            continue
        label = norm_cell(cells[0])
        value = cells[1].strip() if len(cells) > 1 else ""
        for key, (labels, _, _) in HEADER_FIELDS.items():
            if label in labels and key not in out:
                out[key] = (value, idx)
    return out, i


def lint_header(rep, lines, mc_idx, is_delta):
    """Valida o header e devolve o dict de campos (vazio se ausente)."""
    h1 = next((i for i, l in enumerate(lines) if l.startswith("# ")), None)
    if h1 is None:
        rep.hard("sem titulo H1")
        return {}
    if mc_idx is not None and mc_idx > h1:
        rep.hard("comentario de maquina <!-- sdd: ... --> deve vir antes do H1", mc_idx + 1)
    fields, tbl = parse_header(lines, h1)
    if fields is None:
        rep.hard("header deve ser tabela de duas colunas logo abaixo do H1", h1 + 1)
        return {}
    for key, (labels, req_delta, req_living) in HEADER_FIELDS.items():
        required = req_delta if is_delta else req_living
        if key not in fields:
            if required:
                rep.hard(f"header sem campo obrigatorio {key.title()}", tbl + 1)
            continue
        value, idx = fields[key]
        if not value:
            rep.hard(f"header com campo {key.title()} vazio", idx + 1)
            continue
        if key == "status":
            allowed = STATUS_DELTA if is_delta else STATUS_LIVING
            sv = strip_accents(value.lower())
            if sv not in allowed and not (is_delta and sv.startswith(STATUS_DELTA_PREFIX)):
                rep.hard(f"header: Status '{value}' invalido; use um de {sorted(allowed)}"
                         + (" ou 'Promovido a <mudanca>'" if is_delta else ""), idx + 1)
        elif key == "data":
            m = DATE_LEAD.match(value)
            if not m:
                rep.hard(f"header: Data '{value}' invalida; formato AAAA-MM-DD", idx + 1)
            else:
                try:
                    datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                except ValueError:
                    rep.hard(f"header: Data '{value}' nao e data de calendario", idx + 1)
        elif key == "autor":
            if re.fullmatch(r"\[.*\]", value) or strip_accents(value.lower()) in ("nome", "name"):
                rep.hard(f"header: Autor '{value}' e placeholder", idx + 1)
        elif key == "prefixo":
            if not PREFIX_FORM.match(value.strip("`")):
                rep.hard(f"header: Prefixo '{value}' invalido; forma [A-Z][A-Z0-9]{{1,9}}", idx + 1)
    return {k: v for k, (v, _) in fields.items()}


def check_duplicate_sections(rep, lines, mask, groups):
    """Dois headings H2 casando o mesmo grupo de aliases, ou com o mesmo texto
    normalizado, e HARD."""
    reported = set()
    for aliases in groups:
        found = find_sections_exact(lines, aliases, mask=mask)
        if len(found) > 1:
            first = found[0][2]
            for _, _, hidx in found[1:]:
                rep.hard(f"secao duplicada ## {aliases[0]} (tambem em L{first + 1})", hidx + 1)
                reported.add(hidx)
    seen = {}
    for i, text in iter_headings(lines, 2, mask):
        key = norm_heading(text)
        if key in seen and i not in reported:
            rep.hard(f"secao duplicada ## {text} (tambem em L{seen[key] + 1})", i + 1)
        seen.setdefault(key, i)


def check_prefix(rep, header, ids, label):
    declared = (header.get("prefixo") or "").strip("`")
    if not PREFIX_FORM.match(declared):
        return declared or None
    for rid, i in sorted(ids.items(), key=lambda kv: kv[1]):
        pfx = rid.rsplit("-", 1)[0]
        if pfx != declared:
            rep.hard(f"{label} {rid}: prefixo '{pfx}' difere do Prefixo declarado no header ('{declared}')", i + 1)
    return declared


def lint_delta(rep, lines, mask, fields, flags, living, header):
    tier = fields.get("tier", "").lower()
    if tier not in TIERS:
        rep.hard(f"tier ausente ou invalido no comentario de maquina: '{tier}' (small|medium|large|complex)", 1)
        tier = "large"
    if not fields.get("capability"):
        rep.hard("comentario de maquina sem 'capability:'", 1)

    check_duplicate_sections(rep, lines, mask, list(DELTA_SECTIONS) + list(DELTA_REQ_SECTIONS.values()))
    for aliases, tiers in DELTA_SECTIONS.items():
        if tier in tiers and find_section_exact(lines, aliases, mask=mask) is None:
            rep.hard(f"secao obrigatoria para tier {tier} ausente: ## {aliases[0]}")

    # requisitos por secao de delta
    all_ids = {}
    delta = {}
    for kind, aliases in DELTA_REQ_SECTIONS.items():
        sec = find_section_exact(lines, aliases, mask=mask)
        if kind == "RENAMED":
            if sec:
                rep.hard("RENAMED nao suportado: IDs sao estaveis; use REMOVED + ADDED", sec[0])
            delta[kind] = []
            continue
        delta[kind] = collect_reqs(rep, lines, *sec, mask, kind) if sec else []
        for i, rid, _ in delta[kind]:
            if rid in all_ids:
                rep.hard(f"ID duplicado {rid} (tambem em L{all_ids[rid] + 1})", i + 1)
            all_ids[rid] = i

    if not any(delta.values()):
        if "no-behavior-change" in flags:
            rep.warn("delta vazio declarado como no-behavior-change - confirme que e refactor puro")
        else:
            rep.hard("nenhum requisito em ADDED/MODIFIED/REMOVED "
                     "(declare 'no-behavior-change' no comentario se for refactor puro)")

    check_ears(rep, delta["ADDED"], "ADDED")
    check_ears(rep, delta["MODIFIED"], "MODIFIED")
    for i, rid, text in delta["REMOVED"]:
        if not re.search(r"raz[aã]o|reason", text, re.IGNORECASE):
            rep.hard(f"REMOVED {rid}: sem razao registrada", i + 1)
    before_of = {}
    for i, rid, _ in delta["MODIFIED"]:
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        bm = re.match(r"^\s*(?:antes|before)\s*:\s*(.*?)\s*$", nxt, re.IGNORECASE)
        if not bm:
            rep.hard(f"MODIFIED {rid}: sem linha 'Antes:' com o texto anterior", i + 1)
        else:
            before_of[rid] = (i, bm.group(1))

    changed = {rid: i for kind in ("ADDED", "MODIFIED") for i, rid, _ in delta[kind]}
    spec_prefix = check_prefix(rep, header, changed, "delta")

    # IDs contra a spec viva
    if living and os.path.exists(living):
        ltexts = living_texts(living)
        lids = living_ids(living)
        for kind in ("MODIFIED", "REMOVED"):
            for i, rid, _ in delta[kind]:
                if rid not in lids:
                    rep.hard(f"{kind} {rid}: ID nao existe na spec viva {living}", i + 1)
        for rid, (i, before) in before_of.items():
            if rid in ltexts and ltexts[rid] != before:
                rep.hard(f"MODIFIED {rid}: 'Antes:' difere do texto vigente na spec viva "
                         f"(alteracao concorrente; revise o delta). Vigente: {ltexts[rid][:60]}", i + 2)
        for i, rid, _ in delta["ADDED"]:
            if rid in lids:
                rep.hard(f"ADDED {rid}: ID ja existe na spec viva - use MODIFIED ou ID novo", i + 1)
    elif delta["MODIFIED"] or delta["REMOVED"]:
        rep.warn("MODIFIED/REMOVED presentes mas spec viva nao encontrada - "
                 "passe --living para validar IDs")

    # rastreabilidade cobre todo ID de ADDED/MODIFIED
    sec = find_section_exact(lines, TRACE_ALIASES, mask=mask)
    if sec and tier != "small":
        body = "\n".join(l for i, l in enumerate(lines[sec[0]:sec[1]], sec[0]) if not mask[i])
        traced = set(REQ_ID.findall(body))
        for kind in ("ADDED", "MODIFIED"):
            for i, rid, _ in delta[kind]:
                if rid not in traced:
                    rep.hard(f"{rid} nao aparece na Rastreabilidade", i + 1)

    # assumptions
    sec = find_section_exact(lines, ASSUMPTION_ALIASES, mask=mask)
    if sec:
        for i, cells in table_rows(lines, *sec):
            if mask[i]:
                continue
            if len(cells) >= 3:
                if not cells[1].strip():
                    rep.hard(f"assumption '{cells[0][:40]}' com default vazio", i + 1)
                if not cells[2].strip():
                    rep.hard(f"assumption '{cells[0][:40]}' sem racional", i + 1)
        body = "\n".join(lines[sec[0]:sec[1]]).lower()
        if "perguntas em aberto" not in body and "open questions" not in body:
            rep.warn("secao de premissas sem linha 'Perguntas em aberto:' / 'Open questions:'")

    # dimensoes implicitas: celula vazia
    sec = find_section_exact(lines, DIMENSION_ALIASES, mask=mask)
    if sec:
        for i, cells in table_rows(lines, *sec):
            if mask[i]:
                continue
            if len(cells) >= 2 and not cells[1].strip():
                rep.hard(f"dimensao '{cells[0]}' sem requisito nem 'N/A porque'", i + 1)
            elif len(cells) >= 2 and re.fullmatch(r"n/?a\.?", cells[1].strip(), re.IGNORECASE):
                rep.hard(f"dimensao '{cells[0]}': 'N/A' sem 'porque' - a razao e obrigatoria", i + 1)

    # PMF: deve ser a ultima secao (tier >= medium)
    if tier != "small":
        hs = iter_headings(lines, 2, mask)
        if hs:
            last = hs[-1][1].lower()
            if "fragilidade" not in last and "weakest" not in last:
                rep.warn("Ponto de Maior Fragilidade nao e a ultima secao")
    return set(all_ids), spec_prefix


def lint_living(rep, lines, mask, fields, header):
    if not fields.get("capability"):
        rep.hard("comentario de maquina sem 'capability:'", 1)
    check_duplicate_sections(rep, lines, mask, LIVING_SECTIONS + list(DELTA_REQ_SECTIONS.values()))
    for aliases in LIVING_SECTIONS:
        if find_section_exact(lines, aliases, mask=mask) is None:
            rep.hard(f"spec viva sem secao ## {aliases[0]}")
    ids = {}
    sec = find_section_exact(lines, ("Requisitos", "Requirements"), mask=mask)
    if sec:
        reqs = collect_reqs(rep, lines, *sec, mask, "REQ")
        if not reqs:
            rep.hard("spec viva sem requisitos com ID")
        check_ears(rep, reqs, "REQ")
        for i, rid, _ in reqs:
            if rid in ids:
                rep.hard(f"ID duplicado {rid}", i + 1)
            ids.setdefault(rid, i)
    for kind in DELTA_REQ_SECTIONS:
        if find_section_exact(lines, DELTA_REQ_SECTIONS[kind], mask=mask):
            rep.hard(f"spec viva nao deve ter secao {kind} - deltas vivem em changes/NNNN-<feature>/spec.md")
    spec_prefix = check_prefix(rep, header, ids, "REQ")
    return set(ids), spec_prefix


def print_prd_rev(path):
    if not os.path.isfile(path):
        usage(f"arquivo nao encontrado: {path}")
    rev = git_blob_rev(path) or content_rev(path)
    print(rev)
    return 0


def parse_args(argv):
    """Retorna ('print', prd_path) ou ('lint', spec_path, living). Opcao
    desconhecida, valor ausente ou arquivo faltando e erro de uso (exit 2)."""
    args = list(argv[1:])
    if not args:
        usage(__doc__)
    if "--print-prd-rev" in args:
        pos = args.index("--print-prd-rev")
        if pos + 1 >= len(args) or args[pos + 1].startswith("--"):
            usage("--print-prd-rev exige o path do PRD")
        if len(args) != 2:
            usage("--print-prd-rev nao se combina com outras opcoes")
        return "print", args[pos + 1], None
    if args[0].startswith("--"):
        usage(f"primeiro argumento deve ser o path da spec, veio '{args[0]}'\n\n{__doc__}")
    path, living, i = args[0], None, 1
    while i < len(args):
        a = args[i]
        if a == "--living":
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                usage("--living exige o path da spec viva")
            living = args[i + 1]
            i += 2
        else:
            usage(f"opcao desconhecida: {a}\n\n{__doc__}")
    return "lint", path, living


def main(argv):
    mode, path, living = parse_args(argv)
    if mode == "print":
        if not os.path.isfile(path):
            usage(f"PRD nao encontrado: {path}")
        return print_prd_rev(path)
    if living is not None and not os.path.isfile(living):
        usage(f"spec viva nao encontrada: {living}")
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    rep = Report("lint_spec")

    fields, flags, mc_idx = parse_machine_comment(lines)
    if fields is None:
        rep.hard("primeira linha deve ser <!-- sdd: spec-delta | tier: ... | capability: ... --> "
                 "ou <!-- sdd: spec | capability: ... -->", (mc_idx or 0) + 1)
        return rep.emit(path)
    kind = fields["sdd"].lower()
    is_delta = kind == "spec-delta"
    header = lint_header(rep, lines, mc_idx, is_delta)

    spec_ids, spec_prefix = set(), None
    if is_delta:
        if living is None:
            cand = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(path)), "..", "..", "spec.md"))
            if os.path.exists(cand):
                living = cand
        spec_ids, spec_prefix = lint_delta(rep, lines, mask, fields, flags, living, header)
    elif kind == "spec":
        spec_ids, spec_prefix = lint_living(rep, lines, mask, fields, header)
    else:
        rep.hard(f"sdd: '{kind}' nao e spec-delta nem spec", 1)
    lint_prd_links(rep, lines, mask, fields, path, spec_ids, spec_prefix, is_delta)
    check_local_links(rep, lines, mask, path)

    check_tags(rep, lines, mask=mask)
    scan_placeholders(rep, lines, skip_first=mc_idx + 1, mask=mask)
    scan_prose(rep, lines, mask=mask)
    return rep.emit(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
