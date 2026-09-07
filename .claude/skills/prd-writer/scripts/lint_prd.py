#!/usr/bin/env python3
"""
lint_prd.py - verificacao deterministica de conformidade mecanica de PRDs
gerados pela skill prd-writer.

    Uso:  python scripts/lint_prd.py <caminho-do-prd.md | diretorio> [...]

Um arquivo lint a esse arquivo; um diretorio lint a todos os PRDs abaixo
dele. As checagens entre PRDs (resolucao de IDs, prefixos, fatos duplicados,
substituicao) sempre usam a pasta inteira: a raiz e o diretorio `prd` mais
proximo acima do arquivo, ou o proprio diretorio do arquivo.

O que e PRD (mesma politica no lint local e no indice cruzado): apenas
`NNNN-*.md` (plano) e `NNNN-*/prd.md` (pasta), na raiz (layout flat) ou em
`<domain>/` (layout nested). `README.md`, `decisions.md`, `assets/` e qualquer
outro `.md` dentro de pasta de PRD nao sao PRDs: nao entram no indice nem sao
lintados. Arquivo passado explicitamente que nao segue essa forma e erro de
uso (exit 2). Na documentacao da skill, `/docs/prd` e caminho relativo a raiz
do repositorio; o chamador passa o caminho real.

NAO e um gate de qualidade. O linter verifica o esqueleto: conformidade
mecanica e estavel - exatamente o que a auto-revisao da LLM faz mal por drift
de geracao. Linter verde significa esqueleto conforme, nao PRD bom. A
semantica (capability test, guardrails reais, fato vs premissa, ponto de
fragilidade nao-cosmetico, regra dita duas vezes com outras palavras)
permanece com as passadas de julgamento da skill.

Checagens por arquivo:
  comentario de tier (simples|media|complexa|overview); H1; header em tabela
  com Status/Autor/Data; Status na enumeracao (Rascunho, Em Revisao, Aprovado,
  Substituido por NNNN / Draft, In Review, Approved, Superseded by NNNN);
  Autor sem placeholder; Data AAAA-MM-DD de calendario; valor de Confianca;
  grafia das tags de confianca; [PREMISSA-CRITICA] com "se falsa" (max 3);
  placeholders; secoes bloqueantes e esperadas para o tier (heading casado por
  igualdade com aliases PT/EN, nunca por substring); Functional Requirements
  obrigatoria quando o PRD define IDs ou tem Non-functional Requirements;
  Ponto de Maior Fragilidade; prefixo declarado (linha "Prefixo dos
  requisitos: `X`" apos a tabela ou campo Prefixo no header); definicoes
  `- **X-nn (Must)**` / `- **X-NFR-nn**` com o prefixo declarado;
  `FR-nn`/`NFR-nn` sem prefixo; "decisoes tomadas" em Perguntas em Aberto;
  link Markdown `[texto](destino)` para arquivo local que nao resolve (destino
  relativo a pasta do PRD, ancora removida; URL com esquema e ancora pura
  ficam fora); parse de todo bloco ```mermaid (lint_mermaid.py).
  Linhas dentro de bloco de codigo (``` ou ~~~, 3+ caracteres; fecha com o
  mesmo caractere e comprimento >= abertura) sao ignoradas para headings,
  definicoes, citacoes, tags e placeholders. Blocos ```mermaid continuam
  sendo entregues ao lint_mermaid.
Checagens entre PRDs da pasta:
  toda citacao de ID resolve para uma definicao; ID definido duas vezes;
  paragrafo [FATO] identico em mais de um PRD; PRD 0000 (overview) sem
  requisito proprio, listando todo prefixo da pasta; >= 2 prefixos sem 0000;
  substituicao reciproca: sucessor declara `| **Substitui** | NNNN |` e o
  antigo `Substituido por NNNN`; falta de um dos lados, ciclo, dois sucessores
  ativos para o mesmo antigo ou alvo inexistente sao HARD.
  PRD com Status `Substituido por NNNN` e HISTORICO: suas definicoes nao
  contam como duplicata das do sucessor, seus [FATO] nao geram duplicidade,
  e citacao de outro PRD a ID que so existe nele e WARN.
Heuristicas (WARN): hedging, meta-narracao, mecanismo nomeado em secao de
  problem space, prefixo de ID nao declarado por nenhum PRD.

Convencao do projeto substituindo default da skill: o comentario de tier
aceita `omit:` com as chaves internas das secoes cujo WARN de "secao esperada
para o tier" deve ser silenciado:
  <!-- prd-tier: complexa | omit: aceitacao,dependencias -->
Chaves validas: as de SECTION_PATTERNS (contexto, usuario, solucao,
nao_objetivos, metricas, perguntas, resumo, frs, aceitacao, dependencias,
estrategico, nfrs, regulatorio, proposito, contextos, catalogo, fluxos).
Chave desconhecida e WARN. HARD nunca e silenciado por flag.

Saida:
  HARD  -> violacao mecanica; corrija antes de apresentar o PRD. Exit code 1.
  WARN  -> heuristica com risco de falso-positivo; julgue, nao obedeca cego.
           Nao afeta o exit code.
"""

import datetime
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lint_mermaid  # noqa: E402

ALLOWED_TAGS = {"FATO", "PREMISSA", "PREMISSA-CRÍTICA", "LACUNA"}
TIER_VALUES = {"simples", "media", "complexa", "overview"}

# Conjunto de secoes esperado por tier (writing.md, Secoes).
# REQUIRED -> HARD: ausencia deixa o PRD estruturalmente incompleto em
# qualquer contexto. EXPECTED -> WARN: esperado para o tier, mas ha omissao
# legitima; julgue (ou declare `omit:` no comentario de tier).
# Cada chave lista os titulos aceitos, ja normalizados (norm_heading): o
# heading do PRD precisa ser IGUAL a um alias. Substring nao serve:
# "non-functional requirements" contem "functional requirements".
SECTION_PATTERNS = {
    "contexto": (
        "contexto e problema", "contexto", "problema", "contexto e problem",
        "context and problem", "context & problem", "context", "problem",
        "problem statement", "background",
    ),
    "usuario": (
        "usuario-alvo / jtbd", "usuario-alvo", "usuario alvo", "usuarios-alvo",
        "usuarios-alvo / jtbd", "usuario-alvo e jtbd", "jtbd",
        "target user / jtbd", "target user", "target users", "persona",
        "personas", "users", "usuarios",
    ),
    "solucao": ("solucao proposta", "proposed solution"),
    "nao_objetivos": (
        "nao-objetivos", "nao objetivos", "non-goals", "non goals",
        "out of scope", "fora de escopo",
    ),
    "metricas": (
        "metricas de sucesso", "metricas", "success metrics", "metrics",
    ),
    "perguntas": ("perguntas em aberto", "open questions"),
    "resumo": ("resumo executivo", "executive summary"),
    "frs": ("functional requirements", "requisitos funcionais"),
    "aceitacao": ("criterios de aceitacao", "acceptance criteria"),
    "dependencias": (
        "dependencias e riscos", "dependencias", "dependencies and risks",
        "dependencies & risks", "dependencies", "riscos e dependencias",
    ),
    "estrategico": ("alinhamento estrategico", "strategic alignment"),
    "nfrs": (
        "non-functional requirements", "nonfunctional requirements",
        "non functional requirements", "requisitos nao-funcionais",
        "requisitos nao funcionais",
    ),
    "regulatorio": ("consideracoes regulatorias", "regulatory considerations"),
    "proposito": ("proposito", "purpose"),
    "contextos": (
        "contextos", "contexts", "mapa de contextos", "context map",
        "bounded contexts",
    ),
    "catalogo": ("catalogo de eventos", "event catalog", "event catalogue"),
    "fluxos": (
        "fluxos entre contextos", "fluxos", "flows", "flows between contexts",
        "cross-context flows", "sequencias", "sequences",
    ),
}
SECTION_LABELS = {
    "contexto":      "Contexto e Problema",
    "usuario":       "Usuario-alvo / JTBD",
    "solucao":       "Solucao Proposta",
    "nao_objetivos": "Nao-objetivos",
    "metricas":      "Metricas de Sucesso",
    "perguntas":     "Perguntas em Aberto",
    "resumo":        "Resumo Executivo",
    "frs":           "Functional Requirements",
    "aceitacao":     "Criterios de Aceitacao",
    "dependencias":  "Dependencias e Riscos",
    "estrategico":   "Alinhamento Estrategico",
    "nfrs":          "Non-functional Requirements",
    "regulatorio":   "Consideracoes Regulatorias",
    "proposito":     "Proposito",
    "contextos":     "Contextos (mapa)",
    "catalogo":      "Catalogo de eventos",
    "fluxos":        "Fluxos entre contextos",
}
_BASE_REQUIRED = ["contexto", "usuario", "solucao"]
TIER_REQUIRED = {
    "simples":  _BASE_REQUIRED,
    "media":    _BASE_REQUIRED,
    "complexa": _BASE_REQUIRED,
    "overview": [],
}
_SIMPLES_EXPECTED = ["nao_objetivos", "metricas", "perguntas"]
_MEDIA_EXPECTED = _SIMPLES_EXPECTED + [
    "resumo", "frs", "aceitacao", "dependencias",
]
TIER_EXPECTED = {
    "simples":  _SIMPLES_EXPECTED,
    "media":    _MEDIA_EXPECTED,
    "complexa": _MEDIA_EXPECTED + ["estrategico", "nfrs", "regulatorio"],
    "overview": ["proposito", "contextos", "catalogo", "fluxos"],
}

# Status (output.md, Header): enumeracao exata PT/EN, comparada sem acento.
STATUS_VALUES = {"rascunho", "em revisao", "aprovado",
                 "draft", "in review", "approved"}
STATUS_SUPERSEDED = re.compile(r"^(?:substituido por|superseded by)\s+(\d{4})$")
SUPERSEDES_FIELDS = {"substitui", "supersedes", "replaces"}
AUTHOR_PLACEHOLDERS = {"", "tbd", "todo", "nome", "name", "autor", "author",
                       "n/a", "-", "—"}

# tokens de tecnologia/mecanismo de alto sinal: quase nunca pertencem ao
# problem space de uma Solucao Proposta, nem mesmo nomeados como exclusao.
MECHANISM_TERMS = [
    "kafka", "rabbitmq", "lambda", "sqs", "sns", "dynamodb", "redis",
    "step functions", "microservi", "webhook", "event bus", "graphql",
]
EXCLUSION_MARKERS = [
    "fora de escopo", "out of scope", "não nomear", "nao nomear",
    "sem nomear", "não-objetivo", "nao-objetivo",
]
HEDGING = ["provavelmente", "talvez", "na verdade", "probably", "perhaps"]
META_OPENERS = [
    "este prd", "este documento", "neste prd", "neste documento",
    "vamos discutir", "é importante notar", "e importante notar",
    "vale notar", "this prd", "this document", "it's important to note",
    "we will discuss", "in this document",
]

# IDs (writing.md, IDs): <PREFIXO>-nn e <PREFIXO>-NFR-nn
ID_DEF = re.compile(
    r"^\s*[-*]\s+\*\*([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})"
    r"(?:\s*\((?:Must|Should|Could|Won'?t|Won’t)[^)]*\))?\*\*")
ID_REF = re.compile(r"\b([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})\b")
PREFIX_LINE = re.compile(
    r"^\s*(?:Prefixo dos requisitos|Requirement prefix|Prefixo|Prefix)\s*:\s*"
    r"`?([A-Z][A-Z0-9]{1,9})`?", re.IGNORECASE)
PREFIX_FIELDS = {"prefixo", "prefix", "prefixo dos requisitos", "requirement prefix",
                 "prefixo de id", "id prefix"}
BARE_PREFIXES = {"FR", "NFR"}
DECISIONS_TAKEN = re.compile(r"decis(?:ões|oes|ions)\s+(?:tomadas|taken|made)", re.IGNORECASE)
BACKTICK_PREFIX = re.compile(r"`([A-Z][A-Z0-9]{1,9})`")
TIER_COMMENT = re.compile(
    r"<!--\s*prd-tier:\s*([^\s|>]+)\s*(?:\|\s*omit:\s*([^>|]*?))?\s*-->")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
NUMBERED = re.compile(r"^(\d{4})-[^/\\]+$")
NUMBERED_MD = re.compile(r"^(\d{4})-[^/\\]+\.md$", re.IGNORECASE)
SKIP_DIRS = {"node_modules", "assets", "archive"}


def norm(s):
    """Minusculas sem acento, para casar titulo de secao PT/EN."""
    d = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in d if unicodedata.category(c) != "Mn")


def norm_heading(s):
    """Titulo de secao normalizado para comparar com os aliases."""
    s = re.sub(r"^#+\s*", "", s.strip())
    s = re.sub(r"[*_`]", "", s)
    s = norm(s)
    s = re.sub(r"\s+", " ", s).strip(" :.")
    return s


def heading_variants(s):
    """O titulo inteiro e, se houver parentese final, cada metade:
    'Contexto e Problema (Context and Problem)' casa PT ou EN."""
    h = norm_heading(s)
    out = [h]
    pm = re.match(r"^(.*?)\s*\(([^()]*)\)$", h)
    if pm:
        out += [pm.group(1).strip(), pm.group(2).strip()]
    return out


def heading_is(key, heading):
    """True se o heading e (por igualdade) um dos aliases da secao `key`."""
    aliases = SECTION_PATTERNS[key]
    return any(v in aliases for v in heading_variants(heading))


def fence_mask(lines):
    """Lista de bool por linha: True dentro de bloco de codigo (inclusive as
    linhas de abertura e fechamento). Abre com >=3 crases ou tils; fecha com o
    mesmo caractere, comprimento >= abertura e nada mais na linha."""
    mask = [False] * len(lines)
    open_fence = None
    for i, raw in enumerate(lines):
        if open_fence is None:
            m = FENCE.match(raw)
            if m:
                open_fence = m.group(1)
                mask[i] = True
            continue
        mask[i] = True
        s = raw.strip()
        if (s and set(s) == {open_fence[0]} and len(s) >= len(open_fence)):
            open_fence = None
    return mask


def strip_md_prefix(s):
    """Remove marcadores markdown de inicio de linha (lista, heading, citacao)."""
    return re.sub(r"^[\s>#*\-]+", "", s)


def is_tag_like(token):
    """True se o token parece uma tag de confianca (maiusculas, len>=2)."""
    if len(token) < 2:
        return False
    return bool(re.fullmatch(r"[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ\-]*", token))


def parse_header_table(lines, h1_idx):
    """Retorna (rows, end_idx). rows = lista de (first_cell, value_cell)."""
    i = h1_idx + 1
    while i < len(lines) and (
        lines[i].strip() == "" or lines[i].strip().startswith("<!--")
    ):
        i += 1
    if i >= len(lines) or not lines[i].lstrip().startswith("|"):
        return None, i
    rows = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if not all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            if len(cells) >= 2:
                first = re.sub(r"[*`]", "", cells[0]).strip().lower()
                rows.append((first, cells[1]))
        i += 1
    return rows, i


def prd_number(path):
    """Numero NNNN do PRD pelo nome do arquivo (plano) ou da pasta (prd.md)."""
    base = os.path.basename(path)
    if base.lower() == "prd.md":
        m = NUMBERED.match(os.path.basename(os.path.dirname(path)))
    else:
        m = NUMBERED_MD.match(base)
    return int(m.group(1)) if m else None


def is_prd_path(path):
    base = os.path.basename(path)
    if base.lower() == "prd.md":
        return bool(NUMBERED.match(os.path.basename(os.path.dirname(path))))
    return bool(NUMBERED_MD.match(base))


MD_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
CODE_SPAN = re.compile(r"`[^`]*`")


def local_link_findings(doc):
    """(linha_1based, destino, path_procurado) para cada link Markdown local
    que nao resolve a partir da pasta do documento. URL e ancora pura ficam
    fora; bloco de codigo e code span tambem."""
    base = os.path.dirname(os.path.abspath(doc.path))
    out = []
    for i, raw in enumerate(doc.lines):
        if not doc.visible(i):
            continue
        for m in MD_LINK.finditer(CODE_SPAN.sub("", raw)):
            target = m.group(1)
            if URL_SCHEME.match(target) or target.startswith("#"):
                continue
            rel = target.split("#", 1)[0]
            if not rel:
                continue
            expected = os.path.normpath(os.path.join(base, rel))
            if not os.path.exists(expected):
                out.append((i + 1, target, expected))
    return out


class Doc:
    """Dados estruturais de um PRD; findings ficam em hard/warn."""

    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8") as f:
            self.text = f.read()
        self.lines = self.text.splitlines()
        self.fenced = fence_mask(self.lines)
        self.hard = []
        self.warn = []
        self.tier = None
        self.tier_declared = False
        self.omit = set()
        self.omit_unknown = []
        self.number = prd_number(path)
        self.is_overview = self.number == 0
        self.prefix = None
        self.prefix_line = None
        self.defs = []       # (id, line_1based)
        self.refs = []       # (id, prefix, line_1based)
        self.fatos = []      # (normalized_text, line_1based)
        self.h1_idx = None
        self.header_end = 0
        self.rows = []
        self.status = None          # valor bruto do campo Status
        self.superseded_by = None   # int quando Status = Substituido por NNNN
        self.supersedes = []        # ints do campo Substitui/Supersedes
        self.scan()

    @property
    def historical(self):
        return self.superseded_by is not None

    @property
    def label(self):
        base = os.path.basename(self.path)
        if base.lower() == "prd.md":
            return os.path.basename(os.path.dirname(self.path)) + "/prd.md"
        return base

    def add_hard(self, msg, line=None):
        self.hard.append((line, msg))

    def add_warn(self, msg, line=None):
        self.warn.append((line, msg))

    def visible(self, i):
        return not self.fenced[i]

    def scan(self):
        m = TIER_COMMENT.search(self.text)
        if m:
            self.tier_declared = True
            v = m.group(1).lower()
            if v in TIER_VALUES:
                self.tier = v
                if v == "overview":
                    self.is_overview = True
            if m.group(2):
                for k in re.split(r"[,\s]+", m.group(2).strip()):
                    if not k:
                        continue
                    if k in SECTION_PATTERNS:
                        self.omit.add(k)
                    else:
                        self.omit_unknown.append(k)
        self.h1_idx = next((i for i, ln in enumerate(self.lines)
                            if self.visible(i) and re.match(r"#\s+\S", ln)), None)
        if self.h1_idx is not None:
            rows, end = parse_header_table(self.lines, self.h1_idx)
            self.rows = rows or []
            self.header_end = end
            for first, val in self.rows:
                if first in PREFIX_FIELDS:
                    pm = re.search(r"([A-Z][A-Z0-9]{1,9})", val)
                    if pm:
                        self.prefix = pm.group(1)
                        self.prefix_line = self.h1_idx + 1
                if first == "status":
                    self.status = val.strip()
                    sm = STATUS_SUPERSEDED.match(norm(re.sub(r"[*`]", "", val)).strip())
                    if sm:
                        self.superseded_by = int(sm.group(1))
                if first in SUPERSEDES_FIELDS:
                    self.supersedes = [int(n) for n in re.findall(r"\b(\d{4})\b", val)]
            # linha de prefixo entre a tabela e a primeira secao
            for i in range(self.header_end, len(self.lines)):
                if self.lines[i].startswith("## "):
                    break
                pm = PREFIX_LINE.match(self.lines[i])
                if pm:
                    self.prefix = pm.group(1)
                    self.prefix_line = i + 1
                    break
        for i, raw in enumerate(self.lines):
            if not self.visible(i) or TIER_COMMENT.search(raw):
                continue
            dm = ID_DEF.match(raw)
            if dm:
                self.defs.append((f"{dm.group(1)}-{dm.group(2) or ''}{dm.group(3)}", i + 1))
            for rm in ID_REF.finditer(raw):
                self.refs.append((f"{rm.group(1)}-{rm.group(2) or ''}{rm.group(3)}",
                                  rm.group(1), i + 1))
            stripped = strip_md_prefix(raw)
            if stripped.startswith("[FATO]"):
                body = re.sub(r"\s+", " ", stripped[len("[FATO]"):]).strip().lower()
                if body:
                    self.fatos.append((body, i + 1))

    @property
    def fr_defs(self):
        return [(rid, ln) for rid, ln in self.defs if "-NFR-" not in rid]

    def headings(self):
        return [self.lines[i].strip() for i in range(self.header_end, len(self.lines))
                if self.visible(i) and re.match(r"^##\s+", self.lines[i].strip())]

    def has_section(self, key):
        return any(heading_is(key, h) for h in self.headings())

    def section_body(self, key):
        """Linhas (idx, texto) da secao ## cujo titulo e alias de `key`."""
        out, inside = [], False
        for i, raw in enumerate(self.lines):
            if not self.visible(i):
                continue
            s = raw.strip()
            if re.match(r"^##\s+", s):
                inside = heading_is(key, s)
                continue
            if inside:
                out.append((i, raw))
        return out


def lint_doc(doc):
    lines = doc.lines
    hard, warn = doc.add_hard, doc.add_warn

    # --- 1. comentario de tier ---------------------------------------------
    m = TIER_COMMENT.search(doc.text)
    if not m:
        hard("comentario de tier ausente. Primeira linha deve ser "
             "'<!-- prd-tier: simples|media|complexa|overview -->'"
             + (" (arquivo 0000-*: use 'overview')." if doc.is_overview else "."))
    elif m.group(1).lower() not in TIER_VALUES:
        hard(f"tier '{m.group(1)}' invalido. Use simples, media, complexa ou "
             "overview (ASCII minusculo, sem acento).")
    for k in doc.omit_unknown:
        warn(f"omit: chave desconhecida '{k}'. Chaves validas: "
             f"{', '.join(SECTION_PATTERNS)}.")
    tier = doc.tier or ("overview" if doc.is_overview else None)

    # --- 2. titulo H1 -------------------------------------------------------
    if doc.h1_idx is None:
        hard("titulo H1 ('# ...') ausente.")
        return

    # --- 3. header em tabela ------------------------------------------------
    rows, _ = parse_header_table(lines, doc.h1_idx)
    if rows is None:
        hard("header nao esta em tabela markdown. Hard break por espacos e "
             "lista nao servem: use tabela de 2 colunas logo apos o H1.",
             doc.h1_idx + 2)
        rows = []

    # --- 4. campos obrigatorios do header ----------------------------------
    field_names = {r[0] for r in rows}
    for req, label in [
        ({"status"}, "Status"),
        ({"autor", "author"}, "Autor/Author"),
        ({"data", "date"}, "Data/Date"),
    ]:
        if not (req & field_names):
            hard(f"campo de header obrigatorio ausente: {label}.")

    # --- 4a. Status na enumeracao; Autor sem placeholder --------------------
    for first, val in rows:
        clean = re.sub(r"[*`]", "", val).strip()
        if first == "status":
            n = re.sub(r"\s+", " ", norm(clean)).strip()
            if n not in STATUS_VALUES and not STATUS_SUPERSEDED.match(n):
                hard(f"Status '{clean}' fora da enumeracao. Use Rascunho, Em "
                     "Revisao, Aprovado ou 'Substituido por NNNN' (EN: Draft, "
                     "In Review, Approved, 'Superseded by NNNN').")
        elif first in {"autor", "author"}:
            if clean.lower() in AUTHOR_PLACEHOLDERS or re.fullmatch(r"\[.*\]", clean):
                hard(f"campo Autor nao preenchido: '{clean or '(vazio)'}'.")

    # --- 4b. valor de Confianca --------------------------------------------
    for first, val in rows:
        if first in {"confiança", "confianca", "confidence"}:
            head = val.split()[0].strip().lower().strip("—-") if val.split() else ""
            if head in {"alta", "high"}:
                hard("Confianca 'Alta/High' explicita e ruido - omita a "
                     "linha quando a confianca for alta.")
            elif head not in {"média", "media", "baixa", "medium", "low"}:
                warn(f"valor de Confianca nao reconhecido: '{val}'.")

    # --- 4c. formato e validade de Data -------------------------------------
    for first, val in rows:
        if first in {"data", "date"}:
            v = val.strip()
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                try:
                    datetime.date.fromisoformat(v)
                except ValueError:
                    hard(f"Data '{v}' nao e data de calendario valida.")
            elif v in {"AAAA-MM-DD", "YYYY-MM-DD"} or re.fullmatch(r"\[.*\]", v):
                warn("campo Data nao preenchido (placeholder).")
            else:
                hard(f"formato de Data invalido: '{v}'. Use AAAA-MM-DD.")

    header_end = doc.header_end
    # corpo com as linhas em bloco de codigo apagadas (numeracao preservada)
    body_lines = [raw if doc.visible(header_end + k) else ""
                  for k, raw in enumerate(lines[header_end:])]
    body_text = "\n".join(body_lines)

    # --- 5. grafia das tags de confianca (apenas line-initial) -------------
    for offset, raw in enumerate(body_lines):
        stripped = strip_md_prefix(raw)
        tm = re.match(r"\[([^\]]+)\]", stripped)
        if tm:
            token = tm.group(1)
            if is_tag_like(token) and token not in ALLOWED_TAGS:
                hard(f"token entre colchetes nao reconhecido: '[{token}]'. "
                     f"Se for tag de confianca, corrija a grafia "
                     f"(esperado: {', '.join(sorted(ALLOWED_TAGS))}).",
                     header_end + offset + 1)

    # --- 6. [PREMISSA-CRÍTICA]: contagem e clausula 'se falsa' -------------
    pc_decls = []
    for offset, raw in enumerate(body_lines):
        if strip_md_prefix(raw).startswith("[PREMISSA-CRÍTICA]"):
            pc_decls.append(header_end + offset)
    if len(pc_decls) > 3:
        warn(f"{len(pc_decls)} declaracoes de [PREMISSA-CRÍTICA] em linha. "
             "Max 1-3 por documento - confirme que sao distintas e nao ecos.")
    falsa_re = re.compile(
        r"se\s+(for\s+)?falsa|caso\s+seja\s+falsa|if\s+(this\s+is\s+)?"
        r"(false|untrue|wrong)", re.IGNORECASE)
    for idx in pc_decls:
        window = "\n".join(lines[idx: idx + 3])
        if not falsa_re.search(window):
            hard("uma [PREMISSA-CRÍTICA] nao preserva a clausula 'se falsa, "
                 "...' (o que invalida se a premissa cair).", idx + 1)

    # --- 7. vazamento de placeholder (apenas no corpo) ---------------------
    # marcadores em caixa alta casam case-sensitive: "todo" em prosa PT-BR
    # colidia com TODO. Custo aceito: "todo:" minusculo escapa.
    ph_words_upper = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b")
    ph_words_lorem = re.compile(r"\blorem ipsum\b", re.IGNORECASE)
    for offset, raw in enumerate(body_lines):
        pm = ph_words_upper.search(raw) or ph_words_lorem.search(raw)
        if pm:
            hard(f"placeholder nao preenchido no corpo: '{pm.group(0)}'.",
                 header_end + offset + 1)
    ph_slots = re.compile(
        r"\[(nome|name|contexto|context|autor|author|data|date)\]", re.IGNORECASE)
    for offset, raw in enumerate(body_lines):
        sm = ph_slots.search(raw)
        if sm:
            hard(f"slot de template nao preenchido no corpo: '{sm.group(0)}'.",
                 header_end + offset + 1)

    # --- 8. (WARN) hedging lexical -----------------------------------------
    for w in HEDGING:
        n = len(re.findall(r"\b" + re.escape(w) + r"\b", body_text, re.IGNORECASE))
        if n:
            warn(f"hedging lexical: '{w}' ({n}x). Redacao token-eficiente "
                 "evita hedge - ver writing.md, Redacao.")

    # --- 9. (WARN) meta-narracao -------------------------------------------
    for offset, raw in enumerate(body_lines):
        low = strip_md_prefix(raw).lower()
        for opener in META_OPENERS:
            if low.startswith(opener):
                warn(f"abertura de meta-narracao: '{raw.strip()[:50]}...'. "
                     "O titulo ja diz o que e o documento.",
                     header_end + offset + 1)
                break

    # --- 10. (WARN) mecanismo nomeado na Solucao Proposta / FRs ------------
    section_re = re.compile(r"^##\s+(.*)$")
    in_target = False
    for offset, raw in enumerate(body_lines):
        sm = section_re.match(raw.strip())
        if sm:
            in_target = heading_is("solucao", raw) or heading_is("frs", raw)
            continue
        if in_target:
            low = raw.lower()
            if any(x in low for x in EXCLUSION_MARKERS):
                continue
            for term in MECHANISM_TERMS:
                if term in low:
                    warn(f"possivel mecanismo nomeado em secao de problem "
                         f"space: '{term}'. Capability test - reescreva como "
                         f"comportamento, ou ignore se for exclusao legitima.",
                         header_end + offset + 1)
                    break

    # --- 11. secao Ponto de Maior Fragilidade (nao se aplica ao overview) --
    headings = doc.headings()
    normed = [norm(h) for h in headings]
    if tier != "overview":
        has_fragility = any(
            re.search(r"fragilidad|fragility|contestavel|contestable", h)
            for h in normed)
        if not has_fragility:
            hard("secao 'Ponto de Maior Fragilidade' ausente. Todo PRD termina "
                 "nomeando a decisao de julgamento mais contestavel - em "
                 "qualquer tier. Ausencia sinaliza analise rasa, nao PRD "
                 "perfeito.")

    # --- 12. conjunto de secoes esperado para o tier declarado -------------
    present = doc.has_section

    if tier:
        for key in TIER_REQUIRED[tier]:
            if not present(key):
                hard(f"secao obrigatoria ausente para tier '{tier}': "
                     f"{SECTION_LABELS[key]}.")
        for key in TIER_EXPECTED[tier]:
            if not present(key) and key not in doc.omit:
                warn(f"secao esperada para tier '{tier}' nao encontrada: "
                     f"{SECTION_LABELS[key]}. Se a omissao e deliberada, "
                     f"declare 'omit: {key}' no comentario de tier; se o PRD "
                     f"encolheu, reveja o tier declarado.")

    # --- 12b. Functional Requirements obrigatoria quando ha FR ou NFR -------
    if tier != "overview" and not present("frs"):
        if doc.fr_defs:
            hard(f"PRD define {len(doc.fr_defs)} requisito(s) ('{doc.fr_defs[0][0]}'"
                 "...) sem secao Functional Requirements. O heading precisa ser "
                 "exatamente 'Functional Requirements' ou 'Requisitos Funcionais'.",
                 doc.fr_defs[0][1])
        if present("nfrs"):
            hard("secao Non-functional Requirements sem secao Functional "
                 "Requirements. NFR qualifica FR; 'Non-functional Requirements' "
                 "nao satisfaz 'Functional Requirements'.")

    # --- 13. prefixo declarado / definicoes com o prefixo ------------------
    if tier == "overview":
        if doc.defs:
            for rid, ln in doc.defs:
                hard(f"PRD 0000 define o requisito {rid}; a visao geral nao "
                     "contem regra de negocio - mova para o PRD dono.", ln)
        if present("frs"):
            hard("PRD 0000 com secao Functional Requirements; a visao geral so cita IDs.")
    else:
        if doc.defs and not doc.prefix:
            hard("PRD com requisitos sem prefixo declarado. Acrescente a linha "
                 "'Prefixo dos requisitos: `X`' logo apos a tabela do header "
                 "(output.md, Header).", header_end + 1)
        if doc.prefix and not doc.defs and present("frs"):
            warn(f"prefixo `{doc.prefix}` declarado mas nenhuma definicao "
                 "'- **PREFIXO-nn (Must)**' encontrada; confira a forma dos FRs.")
        for rid, ln in doc.defs:
            p = rid.split("-", 1)[0]
            if doc.prefix and p != doc.prefix:
                hard(f"requisito {rid} definido com prefixo '{p}', mas o PRD "
                     f"declara '{doc.prefix}'.", ln)

    # --- 14. FR-nn / NFR-nn sem prefixo de contexto ------------------------
    seen_bare = set()
    for rid, p, ln in doc.refs:
        if p in BARE_PREFIXES and (rid, ln) not in seen_bare:
            seen_bare.add((rid, ln))
            hard(f"ID sem prefixo de contexto: '{rid}'. Use <PREFIXO>-nn ou "
                 "<PREFIXO>-NFR-nn (writing.md, IDs).", ln)

    # --- 15. 'decisoes tomadas' em Perguntas em Aberto ---------------------
    for i, raw in doc.section_body("perguntas"):
        if DECISIONS_TAKEN.search(raw):
            hard("Perguntas em Aberto com lista de 'decisoes tomadas'. "
                 "Perguntas em Aberto lista pendencias reais (pergunta, "
                 "impacto, dono, criterio); 'Nenhuma.' so sem pendencia; "
                 "decisao tomada vive em Trade-offs ou no FR.", i + 1)
            break

    # --- 16. links Markdown para arquivo local resolvem --------------------
    for line, target, expected in local_link_findings(doc):
        hard(f"link '{target}' nao resolve (procurado em {expected}); "
             "o destino e relativo a pasta deste arquivo.", line)


def _fmt_num(n):
    return f"{n:04d}"


def supersession_checks(docs, is_target):
    """Reciprocidade Substitui <-> Substituido por, ciclo, sucessores ativos
    duplicados, alvo inexistente. Findings vao para os docs que sao target."""
    by_num = {}
    for d in docs:
        if d.number is not None:
            by_num.setdefault(d.number, []).append(d)

    def report(d, msg):
        if is_target[d.path]:
            d.add_hard(msg)

    successors = {}  # numero antigo -> [docs que declaram Substitui]
    for d in docs:
        for t in d.supersedes:
            successors.setdefault(t, []).append(d)
            if t not in by_num:
                report(d, f"Substitui {_fmt_num(t)}: nenhum PRD com esse numero na pasta.")
                continue
            if d.number is not None and t == d.number:
                report(d, f"Substitui {_fmt_num(t)}: o PRD nao pode substituir a si mesmo.")
                continue
            for old in by_num[t]:
                if old.superseded_by != d.number:
                    report(d, f"Substitui {_fmt_num(t)}, mas {old.label} nao declara "
                              f"Status 'Substituido por {_fmt_num(d.number or 0)}' "
                              "- a relacao precisa ser reciproca.")
                    report(old, f"{d.label} declara Substitui {_fmt_num(t)}, mas o "
                                f"Status aqui e '{old.status}' - mude para "
                                f"'Substituido por {_fmt_num(d.number or 0)}'.")
    for d in docs:
        if d.superseded_by is None:
            continue
        s = d.superseded_by
        if s not in by_num:
            report(d, f"Status 'Substituido por {_fmt_num(s)}', mas nenhum PRD com "
                      "esse numero existe na pasta.")
            continue
        for new in by_num[s]:
            if d.number is not None and d.number not in new.supersedes:
                report(d, f"Status 'Substituido por {_fmt_num(s)}', mas {new.label} "
                          f"nao declara '| **Substitui** | {_fmt_num(d.number)} |' "
                          "- a relacao precisa ser reciproca.")
                report(new, f"{d.label} declara 'Substituido por {_fmt_num(s)}', mas "
                            f"este PRD nao declara Substitui {_fmt_num(d.number)}.")
    # dois sucessores ativos para o mesmo antigo
    for old_n, succ in successors.items():
        active = [s for s in succ if not s.historical]
        if len(active) > 1:
            names = ", ".join(s.label for s in active)
            for s in active:
                report(s, f"{_fmt_num(old_n)} tem mais de um sucessor ativo ({names}); "
                          "so um PRD ativo pode substitui-lo.")
            for old in by_num.get(old_n, []):
                report(old, f"mais de um sucessor ativo declara Substitui "
                            f"{_fmt_num(old_n)} ({names}).")
    # ciclo no grafo antigo -> novo (arestas de Substitui e de Substituido por)
    edges = {}
    for d in docs:
        if d.number is None:
            continue
        for t in d.supersedes:
            edges.setdefault(t, set()).add(d.number)
        if d.superseded_by is not None:
            edges.setdefault(d.number, set()).add(d.superseded_by)
    in_cycle = set()
    for start in edges:
        stack, seen = [(start, [start])], set()
        while stack:
            node, path = stack.pop()
            for nxt in edges.get(node, ()):
                if nxt == start:
                    in_cycle.update(path)
                elif nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, path + [nxt]))
    if in_cycle:
        chain = " -> ".join(_fmt_num(n) for n in sorted(in_cycle))
        for n in in_cycle:
            for d in by_num.get(n, []):
                report(d, f"ciclo de substituicao ({chain}): um PRD nao pode "
                          "substituir, direta ou indiretamente, o seu substituto.")


def cross_checks(docs, targets):
    """Checagens que dependem da pasta inteira. Findings vao para os targets."""
    by_path = {d.path: d for d in docs}
    is_target = {d.path: (d.path in targets) for d in docs}
    active = [d for d in docs if not d.historical]
    historical = [d for d in docs if d.historical]

    # definicoes e prefixos dos PRDs ativos; historicos ficam a parte
    defs = {}
    for d in active:
        for rid, ln in d.defs:
            defs.setdefault(rid, []).append((d.path, ln))
    hist_defs = {}
    for d in historical:
        for rid, _ in d.defs:
            hist_defs.setdefault(rid, []).append(d)
    prefixes = {}
    for d in active:
        if d.prefix:
            prefixes.setdefault(d.prefix, d.path)
    overviews = [d for d in docs if d.is_overview]

    # ID definido mais de uma vez (entre PRDs ativos)
    for rid, places in defs.items():
        if len(places) > 1:
            where = ", ".join(f"{by_path[p].label}:L{ln}" for p, ln in places)
            for p, ln in places:
                if is_target[p]:
                    by_path[p].add_hard(f"ID {rid} definido mais de uma vez ({where}); "
                                        "ID e unico na pasta e nunca reciclado.", ln)

    # citacoes resolvem
    for d in docs:
        if not is_target[d.path]:
            continue
        own = {rid for rid, _ in d.defs} if d.historical else set()
        reported = set()
        for rid, p, ln in d.refs:
            if p in BARE_PREFIXES:
                continue  # ja e HARD por arquivo
            if rid in defs or rid in own:
                continue
            key = (rid, ln)
            if key in reported:
                continue
            reported.add(key)
            if rid in hist_defs:
                olds = ", ".join(h.label for h in hist_defs[rid])
                d.add_warn(f"cita ID de PRD substituido: {rid} so existe em {olds}. "
                           "Aponte para o ID do sucessor ou mantenha por razao "
                           "historica.", ln)
            elif p in prefixes:
                d.add_hard(f"citacao de {rid} nao resolve para nenhuma definicao "
                           f"na pasta (prefixo '{p}' e de "
                           f"{by_path[prefixes[p]].label}).", ln)
            else:
                d.add_warn(f"possivel ID '{rid}' com prefixo '{p}' que nenhum PRD "
                           "da pasta declara; se for ID, declare o prefixo; se "
                           "nao for, ignore.", ln)

    # [FATO] identico em mais de um PRD (ativos)
    fato_index = {}
    for d in active:
        for body, ln in d.fatos:
            fato_index.setdefault(body, []).append((d.path, ln))
    for body, places in fato_index.items():
        paths = {p for p, _ in places}
        if len(paths) > 1:
            where = ", ".join(f"{by_path[p].label}:L{ln}" for p, ln in places)
            for p, ln in places:
                if is_target[p]:
                    by_path[p].add_hard(
                        f"paragrafo [FATO] identico em mais de um PRD ({where}). "
                        "Fato compartilhado vive no PRD 0000; os demais citam.", ln)

    # PRD 0000: existencia e cobertura de prefixos
    if len(prefixes) >= 2 and not overviews:
        for d in docs:
            if is_target[d.path]:
                d.add_hard(f"{len(prefixes)} prefixos na pasta "
                           f"({', '.join(sorted(prefixes))}) sem PRD 0000 de visao "
                           "geral (writing.md, PRD 0000).")
    for ov in overviews:
        listed = set(BACKTICK_PREFIX.findall(ov.text))
        for p, path in sorted(prefixes.items()):
            if p not in listed:
                msg = (f"prefixo `{p}` ({by_path[path].label}) nao aparece na "
                       f"tabela de contextos de {ov.label}.")
                if is_target[ov.path]:
                    ov.add_hard(msg)
                elif is_target[path]:
                    by_path[path].add_hard(msg)

    supersession_checks(docs, is_target)


def find_root(path):
    d = os.path.dirname(os.path.abspath(path))
    if os.path.basename(path).lower() == "prd.md":
        d = os.path.dirname(d)  # pasta do PRD -> diretorio que a contem
    cur = d
    while True:
        if os.path.basename(cur).lower() in ("prd", "prds"):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return d
        cur = parent


def prd_files(root):
    """PRDs abaixo de root: NNNN-*.md e NNNN-*/prd.md, na raiz ou em
    subpastas de dominio. Outros .md e o conteudo de pasta de PRD ficam fora."""
    out = []
    for dirpath, dirnames, files in os.walk(root):
        keep = []
        for d in sorted(dirnames, key=str.lower):
            if d.startswith(".") or d in SKIP_DIRS:
                continue
            if NUMBERED.match(d):
                p = os.path.join(dirpath, d, "prd.md")
                if os.path.isfile(p):
                    out.append(p)
                continue  # nao desce: decisions.md, assets/ nao sao PRD
            keep.append(d)
        dirnames[:] = keep
        for f in sorted(files, key=str.lower):
            if NUMBERED_MD.match(f):
                out.append(os.path.join(dirpath, f))
    return out


def _fmt(line):
    return f"L{line}" if line else "  -"


def report(doc, multi):
    if multi:
        print(f"== {doc.path}")
    for line, msg in sorted(doc.hard, key=lambda x: (x[0] or 0)):
        print(f"HARD  {_fmt(line):>6}  {msg}")
    for line, msg in sorted(doc.warn, key=lambda x: (x[0] or 0)):
        print(f"WARN  {_fmt(line):>6}  {msg}")


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    targets, roots = [], []
    for a in argv[1:]:
        a = os.path.abspath(a)
        if os.path.isdir(a):
            targets.extend(prd_files(a))
            roots.append(a)
        elif os.path.isfile(a):
            if not is_prd_path(a):
                print(f"erro: {a} nao e PRD (esperado NNNN-<slug>.md ou "
                      "NNNN-<slug>/prd.md); decisions.md, README.md e outros "
                      ".md nao sao lintados como PRD", file=sys.stderr)
                return 2
            targets.append(a)
            roots.append(find_root(a))
        else:
            print(f"erro: {a} nao existe", file=sys.stderr)
            return 2
    if not targets:
        print("erro: nenhum PRD (NNNN-*.md ou NNNN-*/prd.md) a verificar",
              file=sys.stderr)
        return 2
    index_paths = []
    for r in dict.fromkeys(roots):
        index_paths.extend(prd_files(r))
    for t in targets:
        if t not in index_paths:
            index_paths.append(t)
    docs = {}
    for p in dict.fromkeys(index_paths):
        try:
            docs[p] = Doc(p)
        except OSError as e:
            print(f"erro ao abrir {p}: {e}", file=sys.stderr)
            return 2
    target_set = set(targets)
    for p in targets:
        lint_doc(docs[p])
    cross_checks(list(docs.values()), target_set)

    # --- mermaid: parse obrigatorio ---------------------------------------
    findings, n_blocks = lint_mermaid.check_files(targets)
    for p, line, msg in findings:
        docs[p].add_hard(msg, line)

    multi = len(targets) > 1
    h = w = 0
    for p in targets:
        report(docs[p], multi)
        h += len(docs[p].hard)
        w += len(docs[p].warn)
    print("-" * 60)
    scope = f"{len(targets)} PRD(s), {n_blocks} bloco(s) mermaid"
    if h == 0 and w == 0:
        print(f"OK  conformidade mecanica verde ({scope}). Lembrete: o esqueleto "
              "esta conforme, a semantica nao foi verificada.")
    else:
        print(f"{h} HARD, {w} WARN ({scope}). "
              + ("Corrija os HARD antes de apresentar o PRD."
                 if h else "Apenas WARN - julgue cada um."))
    return 1 if h else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
