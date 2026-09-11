#!/usr/bin/env python3
"""
lint_spec.py - verificacao deterministica do esqueleto de uma spec.md.

    Uso:  python3 <skill-dir>/scripts/lint_spec.py <spec.md>

A spec e viva e editada no lugar; o linter confere a forma, nunca o conteudo.
Tudo que esta dentro de bloco de codigo (``` ou ~~~) e ignorado.

HARD (exit 1):
- comentario de maquina ausente ou malformado: a primeira linha nao vazia e
  `<!-- sdd: spec | capability: <dominio>/<capability> [| prd: <path> | prd-rev: git:<hash>] -->`;
- secao obrigatoria ausente: `## Contexto` e `## Requisitos` (heading casa por
  igualdade com os aliases PT/EN, nunca por prefixo; secao duplicada e HARD);
- linha de prefixo ausente ou malformada: logo abaixo do `#`, a linha
  `Prefixo dos requisitos: \\`RSV\\`.` (ou `Requirement prefix:`);
- requisito sem `SHALL`; linha `- **...**` em Requisitos que nao tem a forma
  `- **PFX-NN** — texto`;
- ID com prefixo diferente do declarado; ID duplicado; ID citado com o prefixo
  da spec que nao e requisito nem consta da lista de aposentados;
- ID reutilizado: requisito cujo ID esta na lista `Aposentados: RSV-05, RSV-09`
  (ou `Retired:`), em qualquer ponto da spec;
- prefixo da spec igual a um prefixo declarado por PRD, ou compartilhando com
  ele as duas primeiras letras (`OFR` vs `OFF`): com `prd:` no comentario de
  maquina, lido na pasta do PRD citado; sem `prd:`, lido em `docs/prd` da raiz
  do repositorio (ancestral que contem `docs/`), quando a pasta existe;
- com `prd:` no comentario de maquina: PRD nao encontrado; citacao `X-nn` ou
  `X-NFR-nn` com prefixo de PRD que nao resolve para uma definicao
  `- **X-nn (Must)**` / `- **X-NFR-nn**` em nenhum PRD da pasta; citacao com
  prefixo que nenhum PRD declara ao fim de um requisito;
- com `prd:` no comentario de maquina, secao `## Rastreabilidade` ausente; ID
  de PRD citado ao fim de um requisito (FR em escopo) que nao aparece na
  primeira coluna de nenhuma tabela dessa secao; ID EARS listado nas tabelas
  dessa secao que nao e requisito definido na spec; nome de caso da primeira
  coluna de uma tabela dos Criterios de Aceitacao do PRD (cenario herdado)
  que cita FR em escopo e nao aparece na primeira coluna de nenhuma tabela
  dessa secao (cenario sem ID nenhum e WARN; linha `Fora desta capability:`
  na segunda coluna conta como mapeada);
- tag fora da convencao (`[FATO]`, `[PREMISSA-CRÍTICA]`, grafia errada): sem
  tag e fato; as tags sao `[PREMISSA]` e `[LACUNA]`;
- link Markdown `[texto](destino)` para arquivo local que nao resolve: destino
  relativo a partir da pasta da spec, `/docs/...` a partir da raiz do
  repositorio (ancestral que contem `docs/`); ancora e removida antes; URL com
  esquema, ancora pura, code span e bloco de codigo ficam fora.

WARN (nao afeta exit):
- `SHALL` presente mas sem padrao EARS reconhecido (WHEN/WHILE/WHERE/IF ou
  `The <system> SHALL`); dois `SHALL` na mesma linha; termo vago;
- `prd-rev` divergente de `git hash-object <prd>` (o PRD mudou desde a spec:
  re-derive); `prd-rev` ausente ou git indisponivel para conferir;
- numero pulado na sequencia de IDs sem estar na lista de aposentados;
- secao `## Contexto` com menos de 3 ou mais de 5 linhas nao vazias; secao
  `## Requisitos` com 8 ou mais requisitos sem nenhum subtitulo `###` por tema,
  ou com menos de 8 e algum subtitulo;
- citacao com prefixo desconhecido em prosa; spec com `prd:` sem nenhuma
  citacao de ID do PRD; linha de Rastreabilidade so com IDs de PRD que nenhum
  requisito cita, exceto quando a segunda coluna comeca com `Critério de
  design:` (ou `Design criterion:`), a forma do NFR que vira criterio de
  design em vez de requisito EARS;
- placeholder (TBD, TODO, `[nome]`, `[Uma frase: ...]`), hedging,
  meta-narracao.

Exit 2 em erro de uso: opcao desconhecida, spec ausente ou fora de UTF-8.
Linter verde e esqueleto conforme, nao spec boa.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    REQ_ID, REQ_LINE, Report, check_tags, fenced_line_mask, find_section_exact,
    find_sections_exact, git_blob_rev, iter_headings, norm_heading, parse_machine_comment,
    read_lines, repo_root_for, resolve_local_path, scan_placeholders, scan_prose, strip_accents,
    table_rows, usage,
)

EARS_LEAD = re.compile(r"^\s*(WHEN|WHILE|WHERE|IF)\b", re.IGNORECASE)
UBIQ = re.compile(r"^\s*(the\s+\w+|o\s+sistema|a\s+\w+|the\s+system)\s+shall\b", re.IGNORECASE)
REQ_LOOKALIKE = re.compile(r"^\s*[-*]\s+\*\*")
PREFIX_FORM = re.compile(r"^[A-Z][A-Z0-9]{1,9}$")
PREFIX_LINE = re.compile(
    r"^\s*(?:Prefixo dos requisitos|Requirement prefix|Prefixo|Prefix)\s*:\s*`?([A-Za-z][A-Za-z0-9]{1,9})`?(?![\w-])",
    re.IGNORECASE)
RETIRED_LINE = re.compile(r"^\s*\**\s*(?:Aposentados|Retired)\s*\**\s*:\s*(.*)$", re.IGNORECASE)
PRD_REV = re.compile(r"^git:[0-9a-f]{40,64}$")
PRD_ID = re.compile(r"\b([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})\b")
PRD_DEF = re.compile(r"^\s*[-*]\s+\*\*([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})(?:\s*\([^)]*\))?\*\*")
# `| **Prefixo** | X |` ou `Prefixo dos requisitos: \`X\`.` no PRD: mesma leitura do linter de PRD.
PRD_PREFIX_ROW = re.compile(
    r"^\|\s*\*{0,2}\s*(?:prefixo dos requisitos|requirement prefix|prefixo de id|id prefix|prefixo|prefix)"
    r"\s*\*{0,2}\s*\|\s*`?([A-Z][A-Z0-9]{1,9})`?", re.IGNORECASE)

SECTIONS_REQUIRED = [
    ("Contexto", "Context"),
    ("Requisitos", "Requirements"),
]
# Contexto e enquadramento, nao capitulo: abaixo do minimo nao situa quem le,
# acima do maximo vira prosa que ninguem mantem.
CONTEXT_MIN, CONTEXT_MAX = 3, 5
# Subtitulos `###` por tema em Requisitos (references/specify.md, Secoes).
THEME_MIN = 8
SECTIONS_KNOWN = SECTIONS_REQUIRED + [
    ("Escopo e Fora de Escopo", "Escopo", "Scope / Out of Scope", "Scope"),
    ("Premissas", "Assumptions"),
    ("Perguntas em Aberto", "Open Questions"),
    ("Domain Events",),
    ("Glossário", "Glossary"),
    ("Rastreabilidade", "Traceability"),
    ("Divergências", "Divergences"),
]


def norm_cell(s):
    return norm_heading(re.sub(r"[*`]", "", s))


def collect_reqs(rep, lines, start, end, mask):
    """Requisitos (idx, id, texto) da faixa; linha de lista `- **...**` que
    nao casa REQ_LINE e HARD."""
    out = []
    for i in range(start, end):
        if mask[i]:
            continue
        m = REQ_LINE.match(lines[i])
        if m:
            out.append((i, m.group(1), m.group(2)))
        elif REQ_LOOKALIKE.match(lines[i]):
            rep.hard("linha com aparencia de requisito nao reconhecida "
                     f"(forma: `- **PFX-NN** — texto`): '{lines[i].strip()[:60]}'", i + 1)
    return out


def check_ears(rep, reqs):
    for i, rid, text in reqs:
        if not re.search(r"\bSHALL\b", text):
            rep.hard(f"{rid}: requisito sem SHALL (nao testavel / nao EARS)", i + 1)
        elif not (EARS_LEAD.match(text) or UBIQ.match(text)):
            rep.warn(f"{rid}: SHALL presente mas sem padrao EARS reconhecido "
                     "(WHEN/WHILE/WHERE/IF ou 'The <system> SHALL')", i + 1)
        if re.search(r"\bSHALL\b.*\bSHALL\b", text):
            rep.warn(f"{rid}: dois SHALL na mesma linha - um requisito por linha?", i + 1)
        low = text.lower()
        for v in ("rapidamente", "graciosamente", "apropriad", "adequadament", "quickly",
                  "gracefully", "appropriately", "efficiently"):
            if v in low:
                rep.warn(f"{rid}: termo vago '{v}' - use valor concreto", i + 1)
                break


def find_prefix(rep, lines, mask, h1):
    """Prefixo declarado na linha logo abaixo do H1 (linhas em branco e
    comentarios HTML sao pulados). None quando ausente ou malformado."""
    i = h1 + 1
    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith("<!--")):
        i += 1
    if i >= len(lines) or mask[i]:
        rep.hard("linha de prefixo ausente logo abaixo do titulo: `Prefixo dos requisitos: `RSV`.`", h1 + 1)
        return None
    m = PREFIX_LINE.match(lines[i])
    if not m:
        rep.hard("linha logo abaixo do titulo deve ser `Prefixo dos requisitos: `RSV`.` "
                 f"(veio '{lines[i].strip()[:60]}')", i + 1)
        return None
    prefix = m.group(1)
    if not PREFIX_FORM.match(prefix):
        rep.hard(f"prefixo '{prefix}' invalido; forma [A-Z][A-Z0-9]{{1,9}}", i + 1)
        return None
    return prefix


def retired_ids(lines, mask):
    """IDs listados em linhas `Aposentados: RSV-05, RSV-09` / `Retired:`."""
    out = {}
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        m = RETIRED_LINE.match(l)
        if m:
            for rid in REQ_ID.findall(m.group(1)):
                out.setdefault(rid, i)
    return out


def check_duplicate_sections(rep, lines, mask):
    reported = set()
    for aliases in SECTIONS_KNOWN:
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


def check_context_size(rep, lines, mask):
    """Tamanho da secao Contexto, em linhas nao vazias."""
    found = find_sections_exact(lines, ("Contexto", "Context"), mask=mask)
    if not found:
        return
    start, end, hidx = found[0]
    n = sum(1 for i in range(start, end) if lines[i].strip())
    if n < CONTEXT_MIN or n > CONTEXT_MAX:
        rep.warn(f"secao Contexto com {n} linha(s) nao vazia(s); o esperado e de "
                 f"{CONTEXT_MIN} a {CONTEXT_MAX} - origem, fronteira e base lida, sem virar capitulo",
                 hidx + 1)


def check_requirement_themes(rep, lines, mask, reqs, sec):
    """Subtitulos `###` por tema em Requisitos a partir de THEME_MIN requisitos
    (references/specify.md, Secoes): lista longa sem tema nao se navega, lista
    curta com tema e cerimonia."""
    themes = [i for i, _ in iter_headings(lines, 3, mask) if sec[0] <= i < sec[1]]
    n = len(reqs)
    if n >= THEME_MIN and not themes:
        rep.warn(f"secao Requisitos com {n} requisitos sem subtitulo ### por tema; "
                 f"a partir de {THEME_MIN} a lista se navega por tema", sec[0])
    elif n < THEME_MIN and themes:
        rep.warn(f"secao Requisitos com {n} requisito(s) e subtitulo ### por tema; "
                 f"o tema entra a partir de {THEME_MIN} requisitos", themes[0] + 1)


def check_ids(rep, lines, mask, reqs, prefix, retired):
    """Prefixo, duplicata, reutilizacao de aposentado, citacao orfa e
    numero pulado. Retorna (IDs definidos, IDs de citacao orfa ja reportados)."""
    ids = {}
    orphans = set()
    for i, rid, _ in reqs:
        if rid in ids:
            rep.hard(f"ID duplicado {rid} (tambem em L{ids[rid] + 1})", i + 1)
            continue
        ids[rid] = i
        if prefix and rid.rsplit("-", 1)[0] != prefix:
            rep.hard(f"{rid}: prefixo difere do declarado ('{prefix}')", i + 1)
        if rid in retired:
            rep.hard(f"{rid}: ID reutilizado - consta da lista de aposentados (L{retired[rid] + 1}); "
                     "ID removido morre, use um numero novo", i + 1)
    if not prefix:
        return set(ids), orphans
    # citacao orfa: ID com o prefixo da spec que nao e requisito nem aposentado
    for i, l in enumerate(lines):
        if mask[i] or l.strip().startswith("<!--") or RETIRED_LINE.match(l):
            continue
        for rid in REQ_ID.findall(l):
            if rid.rsplit("-", 1)[0] == prefix and rid not in ids and rid not in retired:
                rep.hard(f"citacao de {rid}, que nao e requisito desta spec nem esta aposentado", i + 1)
                orphans.add(rid)
    # numero pulado sem aposentadoria
    nums = sorted(int(r.rsplit("-", 1)[1]) for r in ids)
    if nums:
        width = len(next(iter(ids)).rsplit("-", 1)[1])
        known = set(nums) | {int(r.rsplit("-", 1)[1]) for r in retired if r.rsplit("-", 1)[0] == prefix}
        missing = [n for n in range(1, nums[-1]) if n not in known]
        if missing:
            shown = ", ".join(f"{prefix}-{n:0{width}d}" for n in missing[:8])
            rep.warn(f"numero(s) pulado(s) na sequencia sem constar de 'Aposentados:': {shown}")
    return set(ids), orphans


# --- PRD -------------------------------------------------------------------

PRD_FILE = re.compile(r"^\d{4}-[^/\\]+\.md$", re.IGNORECASE)
PRD_FOLDER = re.compile(r"^\d{4}-[^/\\]+$")


def prd_files(root):
    """PRDs abaixo de root: `NNNN-*.md` (plano) e `NNNN-*/prd.md` (pasta), na
    raiz ou em subpasta de dominio; anexos de pasta de PRD ficam fora."""
    out = []
    for dirpath, dirnames, files in os.walk(root):
        keep = []
        for d in sorted(dirnames):
            if d.startswith(".") or d in ("assets", "archive", "node_modules"):
                continue
            if PRD_FOLDER.match(d):
                cand = os.path.join(dirpath, d, "prd.md")
                if os.path.isfile(cand):
                    out.append(cand)
                continue
            keep.append(d)
        dirnames[:] = keep
        out.extend(os.path.join(dirpath, f) for f in sorted(files) if PRD_FILE.match(f))
    return out


def prd_dir_for(prd_path):
    """Pasta de PRDs do PRD citado: ancestral `prd`/`prds`, ou a propria pasta
    do arquivo quando nenhum ancestral tem esse nome."""
    d = os.path.dirname(os.path.abspath(prd_path))
    cur = d
    while True:
        if os.path.basename(cur).lower() in ("prd", "prds"):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return d
        cur = parent


def default_prd_dir(spec_path):
    """`docs/prd` da raiz do repositorio (ancestral da spec que contem
    `docs/`), ou None quando a pasta nao existe."""
    root = repo_root_for(spec_path)
    cand = os.path.join(root, "docs", "prd") if root else None
    return cand if cand and os.path.isdir(cand) else None


def prd_index(prd_dir):
    """(definicoes, prefixos) de todos os PRDs abaixo da pasta de PRDs; os
    prefixos vem como {prefixo: path do PRD que o declara}."""
    defs, prefixes = set(), {}
    for path in prd_files(prd_dir):
        plines = read_lines(path)
        pmask = fenced_line_mask(plines)
        for i, l in enumerate(plines):
            if pmask[i]:
                continue
            m = PRD_DEF.match(l)
            if m:
                defs.add(f"{m.group(1)}-{m.group(2) or ''}{m.group(3)}")
            pm = PREFIX_LINE.match(l) or PRD_PREFIX_ROW.match(l)
            if pm:
                prefixes.setdefault(pm.group(1).upper(), path)
    return defs, prefixes


def is_citation_at_end(line, rid):
    """ID entre colchetes ao fim de uma linha de requisito (comentario HTML
    opcional depois)."""
    if not REQ_LINE.match(line):
        return False
    tail = re.sub(r"<!--.*?-->\s*$", "", line).rstrip()
    m = re.search(r"\[([^\[\]]*)\]\s*$", tail)
    return bool(m and re.search(rf"\b{re.escape(rid)}\b", m.group(1)))


def check_prd_rev(rep, fields, prd_path):
    declared = fields.get("prd-rev")
    if not declared:
        rep.warn("prd-rev ausente no comentario de maquina; use git:<hash de `git hash-object <prd>`>", 1)
        return
    if not PRD_REV.match(declared):
        rep.hard(f"prd-rev '{declared}' invalido: forma git:<hash de `git hash-object`>", 1)
        return
    actual = git_blob_rev(prd_path)
    if actual is None:
        rep.warn("git indisponivel: prd-rev nao conferido", 1)
    elif actual != declared:
        rep.warn(f"PRD mudou desde a spec (prd-rev {declared}, atual {actual}); re-derive "
                 "os requisitos que citam os IDs tocados e atualize prd-rev", 1)


def prd_label(path, prd_dir):
    """Nome do PRD relativo a pasta de PRDs, para citar na mensagem."""
    try:
        return os.path.relpath(path, prd_dir)
    except ValueError:
        return path


def check_prefix_collision(rep, prefix, prefixes, prd_dir):
    """HARD quando o prefixo da spec e declarado por um PRD da pasta, ou
    compartilha com ele as duas primeiras letras (`OFR` vs `OFF`): a leitura
    rapida de um ID confunde os dois."""
    if not prefix:
        return
    up = prefix.upper()
    if up in prefixes:
        rep.hard(f"prefixo da spec '{prefix}' coincide com prefixo de PRD em {prd_dir} "
                 f"({prd_label(prefixes[up], prd_dir)}); "
                 "IDs de spec e de PRD tem a mesma forma X-nn - use outro prefixo")
        return
    near = sorted(p for p in prefixes if p[:2] == up[:2])
    if near:
        rep.hard(f"prefixo da spec '{prefix}' comeca com as mesmas duas letras do prefixo "
                 f"'{near[0]}', declarado por {prd_label(prefixes[near[0]], prd_dir)} em {prd_dir}; "
                 "IDs quase iguais se confundem na leitura - use outro prefixo")


def lint_prd(rep, lines, mask, fields, spec_path, prefix):
    prd_field = fields.get("prd")
    if not prd_field:
        if fields.get("prd-rev"):
            rep.warn("prd-rev sem prd: no comentario de maquina; revisao nao verificada", 1)
        prd_dir = default_prd_dir(spec_path)
        if prd_dir:
            check_prefix_collision(rep, prefix, prd_index(prd_dir)[1], prd_dir)
        return
    prd_path = resolve_local_path(spec_path, prd_field)
    if not prd_path:
        rep.hard(f"PRD nao encontrado: '{prd_field}' (relativo a pasta da spec ou `/docs/...` da raiz)", 1)
        return
    check_prd_rev(rep, fields, prd_path)
    prd_dir = prd_dir_for(prd_path)
    defs, prefixes = prd_index(prd_dir)
    check_prefix_collision(rep, prefix, prefixes, prd_dir)
    cited = 0
    seen = set()
    for i, l in enumerate(lines):
        if mask[i] or l.strip().startswith("<!--"):
            continue
        for m in PRD_ID.finditer(l):
            pfx = m.group(1)
            if pfx == prefix:
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
        rep.warn("spec com prd: sem nenhuma citacao de ID do PRD; requisito derivado do PRD "
                 "cita o ID ao fim da linha")


# --- rastreabilidade --------------------------------------------------------

SECTION_TRACE = ("Rastreabilidade", "Traceability")
SECTION_ACCEPTANCE = ("Critérios de Aceitação", "Acceptance Criteria")
SEPARATOR_CELL = re.compile(r":?-{2,}:?")
# Segunda coluna de `Critério de design:`: NFR que e atributo de qualidade sem
# teste direto vira criterio de design, nao requisito EARS (specify.md, A
# partir do PRD), entao a linha existe sem requisito que a cite.
DESIGN_CRITERION = re.compile(r"^[*_`\s]*(?:criterio de design|design criterion|fora desta capability|out of this capability)\s*:", re.IGNORECASE)


def all_table_rows(lines, start, end, mask):
    """Linhas de dados de TODAS as tabelas markdown da faixa (header e
    separador ficam fora). Lista de (idx, [celulas])."""
    rows, after_sep = [], False
    for i in range(start, end):
        if mask[i]:
            continue
        l = lines[i].strip()
        if not l.startswith("|"):
            after_sep = False
            continue
        cells = [c.strip() for c in l.strip("|").split("|")]
        if all(SEPARATOR_CELL.fullmatch(c) for c in cells if c):
            after_sep = True
            continue
        if after_sep:
            rows.append((i, cells))
    return rows


def cited_prd_ids(lines, mask, prefix):
    """FR em escopo: {ID de PRD citado ao fim de um requisito: linha}."""
    out = {}
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        for m in PRD_ID.finditer(l):
            if m.group(1) == prefix:
                continue
            rid = f"{m.group(1)}-{m.group(2) or ''}{m.group(3)}"
            if is_citation_at_end(l, rid):
                out.setdefault(rid, i)
    return out


def id_only_cell(cell):
    """Celula que so tem IDs e pontuacao - linha de mapeamento, nao prosa."""
    return not re.sub(r"[,;/\s]", "", PRD_ID.sub("", cell))


def is_design_criterion(cells):
    """Linha cuja segunda coluna comeca com `Critério de design:` ou
    `Fora desta capability:`: formas prescritas para o NFR que vira criterio
    de design e para o FR ou cenario de outra capability; nenhuma tem
    requisito que a cite."""
    return len(cells) > 1 and bool(DESIGN_CRITERION.match(strip_accents(cells[1])))


def check_traceability(rep, lines, mask, prefix, defined, orphans, retired):
    """Com `prd:` no comentario de maquina: secao obrigatoria, todo FR em
    escopo mapeado e todo ID EARS das tabelas definido na spec."""
    sec = find_section_exact(lines, SECTION_TRACE, mask=mask)
    if sec is None:
        rep.hard("spec com prd: no comentario de maquina sem secao ## Rastreabilidade; "
                 "cada FR do PRD em escopo mapeia para os IDs EARS que o atendem")
        return
    first_col, mapped_only, ears = {}, {}, {}
    for i, cells in all_table_rows(lines, sec[0], sec[1], mask):
        if not cells:
            continue
        criterion = is_design_criterion(cells)
        for m in PRD_ID.finditer(cells[0]):
            if m.group(1) == prefix:
                continue
            rid = f"{m.group(1)}-{m.group(2) or ''}{m.group(3)}"
            first_col.setdefault(rid, i)
            if id_only_cell(cells[0]) and not criterion:
                mapped_only.setdefault(rid, i)
        for c in cells:
            for rid in REQ_ID.findall(c):
                if prefix and rid.rsplit("-", 1)[0] == prefix:
                    ears.setdefault(rid, i)
    cited = cited_prd_ids(lines, mask, prefix)
    for rid, idx in cited.items():
        if rid not in first_col:
            rep.hard(f"{rid} e citado por requisito mas nao aparece na primeira coluna da "
                     "Rastreabilidade; FR em escopo sem mapeamento", idx + 1)
    for rid, idx in mapped_only.items():
        if rid not in cited:
            rep.warn(f"Rastreabilidade: {rid} mapeado sem requisito que o cite ao fim da linha", idx + 1)
    for rid, idx in ears.items():
        if rid in defined or rid in orphans:
            continue
        extra = " (consta da lista de aposentados)" if rid in retired else ""
        rep.hard(f"Rastreabilidade: {rid} nao e requisito definido nesta spec{extra}", idx + 1)


def prd_scenarios(prd_path):
    """Cenarios herdados: {nome normalizado: (nome, IDs de PRD citados na
    linha)} da primeira coluna de toda tabela sob os Criterios de Aceitacao do
    PRD (header e separador fora)."""
    lines = read_lines(prd_path)
    mask = fenced_line_mask(lines)
    out = {}
    for start, end, _ in find_sections_exact(lines, SECTION_ACCEPTANCE, mask=mask):
        for _, cells in all_table_rows(lines, start, end, mask):
            key = norm_cell(cells[0]) if cells else ""
            if key:
                ids = {f"{p}-{nfr or ''}{n}" for p, nfr, n in PRD_ID.findall(" ".join(cells))}
                out.setdefault(key, (cells[0].strip(), ids))
    return out


def check_inherited_scenarios(rep, lines, mask, prd_path, cited):
    """Cenario dos Criterios de Aceitacao do PRD que cita um FR em escopo
    aparece na primeira coluna de alguma tabela da Rastreabilidade (HARD): e o
    caso de teste que a spec tem de cobrir. Cenario que so cita FRs fora do
    escopo e de outra capability e fica em silencio; cenario sem ID nenhum nao
    e escopavel e vira WARN ate ser mapeado ou marcado `Fora desta capability:`."""
    scenarios = prd_scenarios(prd_path)
    if not scenarios:
        return
    sec = find_section_exact(lines, SECTION_TRACE, mask=mask)
    if sec is None:
        return
    mapped = {norm_cell(cells[0]) for _, cells in all_table_rows(lines, sec[0], sec[1], mask) if cells}
    for key, (name, ids) in scenarios.items():
        if key in mapped:
            continue
        if ids & set(cited):
            rep.hard(f"cenario '{name}' dos Criterios de Aceitacao do PRD sem linha na "
                     "Rastreabilidade; cenario herdado mapeia para os IDs EARS que o cobrem",
                     sec[0])
        elif not ids:
            rep.warn(f"cenario '{name}' do PRD nao cita requisito: mapeie-o na Rastreabilidade "
                     "ou marque-o 'Fora desta capability:'", sec[0])


# --- links ------------------------------------------------------------------

MD_LINK = re.compile(r"\[[^\]]*\]\(\s*(?:<([^>]*)>|([^)\s]+))(?:\s+\"[^\"]*\")?\s*\)")
URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
CODE_SPAN = re.compile(r"`[^`]*`")


def check_local_links(rep, lines, mask, doc_path):
    base = os.path.dirname(os.path.abspath(doc_path))
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        for m in MD_LINK.finditer(CODE_SPAN.sub("", l)):
            raw = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
            if not raw or URL_SCHEME.match(raw) or raw.startswith("#"):
                continue
            target = raw.split("#", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                root = repo_root_for(doc_path)
                expected = os.path.normpath(os.path.join(root, target.lstrip("/"))) if root else f"<raiz>{target}"
                ok = root is not None and os.path.exists(expected)
            else:
                expected = os.path.normpath(os.path.join(base, target))
                ok = os.path.exists(expected)
            if not ok:
                rep.hard(f"link '{raw}' nao resolve (procurado em {expected}); "
                         "conte os `../` a partir da pasta deste arquivo", i + 1)


# --- main -------------------------------------------------------------------

def parse_args(argv):
    args = list(argv[1:])
    if not args:
        usage(__doc__)
    if args[0].startswith("--"):
        usage(f"primeiro argumento deve ser o path da spec, veio '{args[0]}'\n\n{__doc__}")
    if len(args) > 1:
        usage(f"opcao desconhecida: {args[1]}\n\n{__doc__}")
    return args[0]


def main(argv):
    path = parse_args(argv)
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    rep = Report("lint_spec")

    fields, mc_idx = parse_machine_comment(lines)
    if fields is None:
        rep.hard("primeira linha deve ser <!-- sdd: spec | capability: <dominio>/<capability> "
                 "[| prd: <path> | prd-rev: git:<hash>] -->", (mc_idx or 0) + 1)
        return rep.emit(path)
    if fields["sdd"].lower() != "spec":
        rep.hard(f"sdd: '{fields['sdd']}' - este linter le `sdd: spec`", 1)
    if not fields.get("capability"):
        rep.hard("comentario de maquina sem 'capability:'", 1)

    h1 = next((i for i, l in enumerate(lines) if l.startswith("# ") and not mask[i]), None)
    if h1 is None:
        rep.hard("sem titulo H1")
        prefix = None
    else:
        if mc_idx is not None and mc_idx > h1:
            rep.hard("comentario de maquina <!-- sdd: ... --> deve vir antes do H1", mc_idx + 1)
        prefix = find_prefix(rep, lines, mask, h1)

    check_duplicate_sections(rep, lines, mask)
    for aliases in SECTIONS_REQUIRED:
        if find_section_exact(lines, aliases, mask=mask) is None:
            rep.hard(f"secao obrigatoria ausente: ## {aliases[0]}")
    check_context_size(rep, lines, mask)

    reqs = []
    sec = find_section_exact(lines, ("Requisitos", "Requirements"), mask=mask)
    if sec:
        reqs = collect_reqs(rep, lines, *sec, mask)
        if not reqs:
            rep.hard("secao Requisitos sem requisito com ID")
        check_ears(rep, reqs)
        check_requirement_themes(rep, lines, mask, reqs, sec)
    retired = retired_ids(lines, mask)
    defined, orphans = check_ids(rep, lines, mask, reqs, prefix, retired)

    if prefix is None and reqs:
        # sem linha de prefixo (ja HARD), o prefixo mais comum dos IDs evita
        # que toda citacao da propria spec vire "prefixo desconhecido"
        counts = {}
        for _, rid, _ in reqs:
            counts[rid.rsplit("-", 1)[0]] = counts.get(rid.rsplit("-", 1)[0], 0) + 1
        prefix = max(counts, key=counts.get)
    lint_prd(rep, lines, mask, fields, path, prefix)
    if fields.get("prd"):
        check_traceability(rep, lines, mask, prefix, defined, orphans, retired)
        prd_path = resolve_local_path(path, fields["prd"])
        if prd_path:
            check_inherited_scenarios(rep, lines, mask, prd_path, cited_prd_ids(lines, mask, prefix))
    check_local_links(rep, lines, mask, path)
    check_tags(rep, lines, mask=mask)
    scan_placeholders(rep, lines, skip_first=(mc_idx or 0) + 1, mask=mask)
    scan_prose(rep, lines, mask=mask)
    return rep.emit(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
