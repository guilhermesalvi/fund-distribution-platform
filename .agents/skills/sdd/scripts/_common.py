"""Helpers compartilhados por lint_spec.py, lint_design.py, lint_tasks.py e
lint_adr.py.

Saida padrao dos linters:
  HARD  -> violacao mecanica do esqueleto; corrija e rode de novo. Exit code 1.
  WARN  -> heuristica com risco de falso-positivo; julgue. Nao afeta exit.

A ultima linha resume: com HARD manda corrigir; sem HARD e com WARN manda
julgar cada um; com 0 HARD e 0 WARN diz que o esqueleto esta conforme, para
o chamador nao procurar WARN inexistente.
"""

import os
import re
import subprocess
import sys
import unicodedata

# Console Windows em cp1252 quebra ao imprimir emoji/acentos do artefato.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

REQ_ID = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d{2,})\b")
REQ_LINE = re.compile(r"^\s*[-*]\s+\*\*([A-Z][A-Z0-9]{1,9}-\d{2,})\*\*\s*[—\-–:]\s*(.+)$")

ALLOWED_TAGS = {"PREMISSA", "LACUNA"}
# Tags de convencoes anteriores ou mal grafadas: a convencao e so [PREMISSA] e [LACUNA].
REJECTED_TAGS = {"FATO", "FATOS", "PREMISSAS", "LACUNAS", "PREMISSA-CRITICA", "PREMISSA-CRÍTICA",
                 "ASSUMPTION", "GAP", "FACT"}

# Marcadores em caixa alta casam case-sensitive: "todo" em prosa PT-BR colide com TODO.
PLACEHOLDER_HARD_CS = [r"\bTBD\b", r"\bTODO\b", r"\bTBC\b", r"\bFIXME\b", r"\bXXX\b"]
PLACEHOLDER_HARD = [
    r"implementar depois", r"implement later", r"fill in later",
    r"adicionar valida[cç][aã]o apropriada", r"add appropriate validation",
    r"add validation\b", r"tratar edge cases", r"handle edge cases",
    r"similar (?:à|a|to) T\d+",
]
HEDGING = ["provavelmente", "talvez", "na verdade", "probably", "perhaps", "maybe"]
# Placeholder de template: colchetes com texto livre comecando por letra, ate
# 200 caracteres - `[nome]`, `[Uma frase: o que faremos.]`, `[Regra em
# AGENTS.md ... com o path.]`. Link Markdown fica fora pelo `(` seguinte; tag
# ([PREMISSA], [BOOK-04]) fica fora por TAG_LIKE.
TEMPLATE_PLACEHOLDER = re.compile(r"\[([A-Za-zÀ-Úà-ú][^\[\]]{2,199})\](?!\()")
# Valor reduzido a reticencias - `- Positivas: …`, `| Racional | ... |`:
# rotulo escrito, conteudo por escrever.
ELLIPSIS_VALUE = re.compile(r"(?::|\|)\s*(?:…|\.{3})\s*(?:\||$)")
TAG_LIKE = re.compile(r"^[A-ZÀ-Ú0-9\s\-]+$")
# Trecho entre crases: `[Fact]` e codigo citado, nao texto por escrever.
CODE_SPAN = re.compile(r"`[^`]*`")
META_OPENERS = [
    "esta spec", "este documento", "neste documento", "este design",
    "vamos discutir", "é importante notar", "e importante notar", "vale notar",
    "this spec", "this document", "this design", "it's important to note",
    "we will discuss", "in this document",
]


class Report:
    def __init__(self, label):
        self.label = label
        self.hard_findings = []
        self.warn_findings = []

    def hard(self, msg, line=None):
        self.hard_findings.append((line, msg))

    def warn(self, msg, line=None):
        self.warn_findings.append((line, msg))

    def emit(self, path):
        def fmt(line):
            return f"L{line}" if line else "-"

        for line, msg in self.hard_findings:
            print(f"HARD  {fmt(line):>6}  {msg}")
        for line, msg in self.warn_findings:
            print(f"WARN  {fmt(line):>6}  {msg}")
        h, w = len(self.hard_findings), len(self.warn_findings)
        if h:
            tail = f"Corrija os HARD e rode de novo ({self.label})."
        elif w:
            tail = "Apenas WARN - julgue cada um."
        else:
            tail = "OK esqueleto conforme; a semantica nao foi verificada."
        print(f"\n{self.label}: {h} HARD, {w} WARN em {path}. {tail}")
        return 1 if h else 0


def read_lines(path):
    """Linhas do arquivo em UTF-8 (BOM aceito e removido). Arquivo ausente,
    ilegivel ou fora de UTF-8 e erro de uso (exit 2), nunca traceback."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            return f.read().splitlines()
    except OSError as e:
        usage(f"arquivo ilegivel: {path}: {e.strerror or e}")
    except UnicodeDecodeError as e:
        usage(f"arquivo nao esta em UTF-8: {path}: {e}")


def parse_machine_comment(lines):
    """Primeira linha nao vazia deve ser <!-- sdd: kind | k: v -->.
    Retorna (fields, line_idx) ou (None, line_idx)."""
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            continue
        m = re.match(r"^<!--\s*sdd:\s*(.*?)\s*-->$", s)
        if not m:
            return None, i
        parts = [p.strip() for p in m.group(1).split("|")]
        fields = {"sdd": parts[0].strip()}
        for p in parts[1:]:
            if ":" in p:
                k, v = p.split(":", 1)
                fields[k.strip().lower()] = v.strip()
        return fields, i
    return None, None


def headings(lines, level=2):
    """Lista de (idx, texto) para headings do nivel dado."""
    prefix = "#" * level + " "
    out = []
    for i, l in enumerate(lines):
        if l.startswith(prefix) and not l.startswith("#" * (level + 1)):
            out.append((i, l[len(prefix):].strip()))
    return out


FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")


def fenced_line_mask(lines):
    """list[bool] paralela a `lines`: True nas linhas de abertura/fechamento e
    no interior de blocos de codigo (``` ou ~~~, 3+ caracteres; o fechamento
    usa o mesmo caractere com comprimento >= abertura e nada mais na linha).
    Fence nao fechado mascara ate o fim (CommonMark)."""
    mask = [False] * len(lines)
    open_ch, open_len = None, 0
    for i, l in enumerate(lines):
        m = FENCE.match(l)
        if open_ch is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                open_ch, open_len = m.group(1)[0], len(m.group(1))
                mask[i] = True
        else:
            mask[i] = True
            if (m and m.group(1)[0] == open_ch and len(m.group(1)) >= open_len
                    and not m.group(2).strip()):
                open_ch = None
    return mask


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def norm_heading(s):
    """Forma canonica de um heading para casamento exato: minusculo, sem
    acento, sem o alias entre parenteses, so [a-z0-9&] e espacos simples."""
    s = strip_accents(s.lower())
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9&\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def iter_headings(lines, level=2, mask=None):
    """Como `headings`, ignorando linhas marcadas em `mask` (fenced_line_mask)."""
    if mask is None:
        mask = fenced_line_mask(lines)
    return [(i, t) for i, t in headings(lines, level) if not mask[i]]


def check_unknown_sections(rep, lines, known, source, mask=None, hard=True):
    """Secao `##` fora da lista fechada do artefato. `known` e a lista de
    tuplas de alias PT/EN; `source` diz onde a lista vive, no formato
    `references/<arquivo>.md, <Titulo>`. A mensagem e a mesma nos quatro
    linters; `hard=False` a rebaixa para WARN."""
    if mask is None:
        mask = fenced_line_mask(lines)
    wanted = {norm_heading(a) for aliases in known for a in aliases}
    for i, text in iter_headings(lines, 2, mask):
        if norm_heading(text) not in wanted:
            msg = f"secao desconhecida: ## {text}; a lista de secoes e a de {source}"
            (rep.hard if hard else rep.warn)(msg, i + 1)


def find_sections_exact(lines, aliases, level=2, mask=None):
    """Todas as secoes cujo heading normalizado (norm_heading) e IGUAL a algum
    alias normalizado - nunca prefixo/substring. Lista de (start, end, hidx);
    headings dentro de fence sao ignorados. Vazia se ausente."""
    if mask is None:
        mask = fenced_line_mask(lines)
    hs = iter_headings(lines, level, mask)
    wanted = {norm_heading(a) for a in aliases}
    out = []
    for n, (i, text) in enumerate(hs):
        if norm_heading(text) in wanted:
            end = hs[n + 1][0] if n + 1 < len(hs) else len(lines)
            out.append((i + 1, end, i))
    return out


def find_section_exact(lines, aliases, level=2, mask=None):
    """(start, end) da primeira secao que casa por igualdade (ver
    find_sections_exact). None se ausente."""
    found = find_sections_exact(lines, aliases, level, mask)
    return (found[0][0], found[0][1]) if found else None


def repo_root_for(doc_path):
    """Primeiro ancestral do documento que contem `docs/`, ou None."""
    cur = os.path.dirname(os.path.abspath(doc_path))
    while True:
        if os.path.isdir(os.path.join(cur, "docs")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def resolve_local_path(doc_path, target):
    """Path absoluto de um destino local: relativo ao documento, ou
    `/docs/...` a partir da raiz do repositorio. None se nada existe."""
    base = os.path.dirname(os.path.abspath(doc_path))
    if target.startswith("/"):
        root = repo_root_for(doc_path)
        cand = os.path.normpath(os.path.join(root, target.lstrip("/"))) if root else None
    else:
        cand = os.path.normpath(os.path.join(base, target))
    return cand if cand and os.path.exists(cand) else None


def git_blob_rev(path):
    """`git:<hash>` de `git hash-object <path>` (rodado no diretorio do
    arquivo, para os filtros do repositorio valerem). None se git ausente ou
    falhar."""
    path = os.path.abspath(path)
    try:
        r = subprocess.run(["git", "hash-object", os.path.basename(path)],
                           cwd=os.path.dirname(path), capture_output=True,
                           text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    out = r.stdout.strip()
    if r.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", out):
        return None
    return "git:" + out


def table_rows(lines, start, end):
    """Linhas de dados da primeira tabela markdown da faixa (exclui header e
    separador). Retorna lista de (idx, [celulas])."""
    rows = []
    seen_header = False
    for i in range(start, end):
        l = lines[i].strip()
        if not l.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip() for c in l.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            seen_header = True
            continue
        if not seen_header:
            continue  # linha de header
        rows.append((i, cells))
    return rows


def is_template_placeholder(line):
    """Linha com colchetes de template - `[nome]`, `[Situação e restrições
    ...]`. Fora: item de checklist, link Markdown, URL, code span (`[Fact]`),
    tag ([PREMISSA], [LACUNA]) e linha com ID de requisito ([BOOK-04])."""
    if "http" in line or REQ_ID.search(line) or re.match(r"^\s*- \[[ xX]\]", line):
        return False
    return any(not TAG_LIKE.match(m.group(1))
               for m in TEMPLATE_PLACEHOLDER.finditer(CODE_SPAN.sub(" ", line)))


def scan_placeholders(rep, lines, skip_first=0, mask=None):
    """Placeholder e WARN: a decisao de que aquilo e conteudo faltando e do
    agente. Vale para marcador (TBD, TODO), colchete de template e valor
    reduzido a reticencias. `mask` (fenced_line_mask) e opcional: linhas
    marcadas sao ignoradas."""
    for i, l in enumerate(lines):
        if i < skip_first or (mask and mask[i]):
            continue
        if any(re.search(p, l) for p in PLACEHOLDER_HARD_CS) or any(
                re.search(p, l, re.IGNORECASE) for p in PLACEHOLDER_HARD):
            rep.warn(f"placeholder: '{l.strip()[:70]}'", i + 1)
        elif is_template_placeholder(l):
            rep.warn(f"possivel placeholder de template: '{l.strip()[:70]}'", i + 1)
        elif ELLIPSIS_VALUE.search(CODE_SPAN.sub(" ", l)):
            rep.warn(f"valor reduzido a reticencias: '{l.strip()[:70]}'", i + 1)


def scan_prose(rep, lines, mask=None):
    """Hedging e meta-narracao (WARN). `mask` (fenced_line_mask) e opcional."""
    for i, l in enumerate(lines):
        if mask and mask[i]:
            continue
        low = l.lower()
        if low.strip().startswith("<!--") or low.strip().startswith("|"):
            continue
        for h in HEDGING:
            if re.search(rf"\b{h}\b", low):
                rep.warn(f"hedging lexical ('{h}')", i + 1)
                break
        for m in META_OPENERS:
            if low.lstrip("#>*- ").startswith(m):
                rep.warn(f"meta-narracao ('{m}')", i + 1)
                break


def check_tags(rep, lines, mask=None):
    """So [PREMISSA] e [LACUNA] sao tags; [FATO], [PREMISSA-CRÍTICA] e
    grafias erradas sao HARD. `mask` (fenced_line_mask) e opcional."""
    for i, l in enumerate(lines):
        if mask and mask[i]:
            continue
        for m in re.finditer(r"\[([A-ZÀ-Ú][A-ZÀ-Ú\-\s]{2,})\]", l):
            tag = m.group(1).strip()
            if tag in ALLOWED_TAGS:
                continue
            key = strip_accents(tag.replace(" ", "-"))
            if key in {strip_accents(t) for t in REJECTED_TAGS}:
                rep.hard(f"tag fora da convencao: [{tag}] (sem tag e fato; use [PREMISSA] ou [LACUNA])", i + 1)


def usage(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)
