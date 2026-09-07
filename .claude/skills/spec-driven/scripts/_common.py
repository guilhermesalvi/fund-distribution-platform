"""Helpers compartilhados pelos linters da skill spec-driven.

Saida padrao (igual ao lint_prd.py do prd-writer):
  HARD  -> violacao mecanica; corrija antes de apresentar. Exit code 1.
  WARN  -> heuristica com risco de falso-positivo; julgue. Nao afeta exit.
"""

import hashlib
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
TASK_ID = re.compile(r"\bT(\d+)\b")
# Linha `Antes:` de um MODIFIED (specify.md, Delta): indentada ou nao, PT ou
# EN, mesma leitura no lint_spec.py e no apply_delta.py.
BEFORE_LINE = re.compile(r"^\s*(Antes|Before)\s*:\s*(.+?)\s*$", re.IGNORECASE)
FILE_LINE = re.compile(r"[\w./\\\-]+\.[A-Za-z0-9]+:\d+")

TIERS = {"small", "medium", "large", "complex"}
ALLOWED_TAGS = {"FATO", "PREMISSA", "PREMISSA-CRÍTICA", "LACUNA"}

# Marcadores em caixa alta casam case-sensitive: "todo" em prosa PT-BR
# colidia com TODO (mesma decisao do lint_prd.py do prd-writer).
PLACEHOLDER_HARD_CS = [r"\bTBD\b", r"\bTODO\b", r"\bTBC\b", r"\bFIXME\b", r"\bXXX\b"]
PLACEHOLDER_HARD = [
    r"implementar depois", r"implement later", r"fill in later",
    r"adicionar valida[cç][aã]o apropriada", r"add appropriate validation",
    r"add validation\b", r"tratar edge cases", r"handle edge cases",
    r"similar (?:à|a|to) T\d+",
]
HEDGING = ["provavelmente", "talvez", "na verdade", "probably", "perhaps", "maybe"]
META_OPENERS = [
    "esta spec", "este documento", "neste documento", "este design",
    "vamos discutir", "é importante notar", "e importante notar", "vale notar",
    "this spec", "this document", "this design", "it's important to note",
    "we will discuss", "in this document",
]
VAGUE = [
    "rapidamente", "graciosamente", "apropriad", "adequad", "eficiente",
    "quickly", "gracefully", "appropriate", "efficient", "robust", "robust",
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

    def incomplete(self, msg, line=None):
        """Validacao incompleta (fonte ausente, git indisponivel): HARD com
        prefixo INCOMPLETO, para o relatorio nao fingir sucesso."""
        self.hard(f"INCOMPLETO: {msg}", line)

    def emit(self, path):
        def fmt(line):
            return f"L{line}" if line else "-"

        for line, msg in self.hard_findings:
            print(f"HARD  {fmt(line):>6}  {msg}")
        for line, msg in self.warn_findings:
            print(f"WARN  {fmt(line):>6}  {msg}")
        h, w = len(self.hard_findings), len(self.warn_findings)
        tail = (f"Corrija os HARD antes de apresentar ({self.label})."
                if h else "Apenas WARN - julgue cada um.")
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
    """Primeira linha nao vazia deve ser <!-- sdd: kind | k: v | flag -->.
    Retorna (fields, flags, line_idx) ou (None, None, None)."""
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            continue
        m = re.match(r"^<!--\s*sdd:\s*(.*?)\s*-->$", s)
        if not m:
            return None, None, i
        parts = [p.strip() for p in m.group(1).split("|")]
        fields = {"sdd": parts[0].strip()}
        flags = set()
        for p in parts[1:]:
            if ":" in p:
                k, v = p.split(":", 1)
                fields[k.strip().lower()] = v.strip()
            elif p:
                flags.add(p.lower())
        return fields, flags, i
    return None, None, None


def headings(lines, level=2):
    """Lista de (idx, texto) para headings do nivel dado."""
    prefix = "#" * level + " "
    out = []
    for i, l in enumerate(lines):
        if l.startswith(prefix) and not l.startswith("#" * (level + 1)):
            out.append((i, l[len(prefix):].strip()))
    return out


def norm(s):
    s = s.lower()
    s = re.sub(r"\(.*?\)", " ", s)  # remove aliases entre parenteses
    s = re.sub(r"[^a-z0-9àáâãéêíóôõúç&\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def find_section(lines, aliases, level=2):
    """Retorna (start, end) do corpo da secao cujo heading casa com algum alias
    (prefixo, case-insensitive, PT ou EN). None se ausente."""
    hs = headings(lines, level)
    wanted = [norm(a) for a in aliases]
    for n, (i, text) in enumerate(hs):
        t = norm(text)
        raw = text.lower()
        if any(t.startswith(w) or w in raw for w in wanted):
            end = hs[n + 1][0] if n + 1 < len(hs) else len(lines)
            return i + 1, end
    return None


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
    """Como `headings`, ignorando linhas marcadas em `mask` (fenced_line_mask).
    `mask=None` calcula a mascara."""
    if mask is None:
        mask = fenced_line_mask(lines)
    return [(i, t) for i, t in headings(lines, level) if not mask[i]]


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


def content_rev(path):
    """`sha256:<12 hex>` do conteudo com quebras de linha normalizadas para LF."""
    with open(path, "rb") as f:
        data = f.read().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return "sha256:" + hashlib.sha256(data).hexdigest()[:12]


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
    """Linhas de tabela markdown (exclui header e separador). Retorna
    lista de (idx, [celulas])."""
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


def scan_placeholders(rep, lines, skip_first=0, mask=None):
    """`mask` (fenced_line_mask) e opcional: linhas marcadas sao ignoradas."""
    for i, l in enumerate(lines):
        if i < skip_first or (mask and mask[i]):
            continue
        if any(re.search(p, l) for p in PLACEHOLDER_HARD_CS) or any(
                re.search(p, l, re.IGNORECASE) for p in PLACEHOLDER_HARD):
            rep.hard(f"placeholder proibido: '{l.strip()[:70]}'", i + 1)
        if re.search(r"\[[a-zà-ú][^\]]{2,40}\]", l) and "http" not in l and not REQ_ID.search(l):
            # [nome], [razão], [what we'll do] ... colchetes com texto minusculo
            if not re.search(r"^\s*- \[[ x]\]", l):
                rep.warn(f"possivel placeholder de template: '{l.strip()[:70]}'", i + 1)


def scan_prose(rep, lines, mask=None):
    """`mask` (fenced_line_mask) e opcional: linhas marcadas sao ignoradas."""
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
    """`mask` (fenced_line_mask) e opcional: linhas marcadas sao ignoradas."""
    crit_count = 0
    for i, l in enumerate(lines):
        if mask and mask[i]:
            continue
        for m in re.finditer(r"\[([A-ZÀ-Ú][A-ZÀ-Ú\-\s]{2,})\]", l):
            tag = m.group(1).strip()
            if tag in ALLOWED_TAGS:
                if tag == "PREMISSA-CRÍTICA":
                    crit_count += 1
                    if not re.search(r"se falsa|if false|se for falsa", l, re.IGNORECASE):
                        rep.hard("[PREMISSA-CRÍTICA] sem clausula 'se falsa...' na mesma linha", i + 1)
                continue
            if re.fullmatch(r"[A-ZÀ-Ú][A-ZÀ-Ú\-\s]+", tag) and tag.replace(" ", "-") in {
                "PREMISSA-CRITICA", "PREMISSA-CRÍTICA", "FATOS", "PREMISSAS", "LACUNAS",
            }:
                rep.hard(f"tag de confianca mal grafada: [{tag}] (use {sorted(ALLOWED_TAGS)})", i + 1)
    if crit_count > 3:
        rep.hard(f"{crit_count} [PREMISSA-CRÍTICA]; maximo 3 - se tudo e critico, nada e")
    return crit_count


def usage(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)
