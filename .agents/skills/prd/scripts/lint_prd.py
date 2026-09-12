#!/usr/bin/env python3
"""
lint_prd.py - verificacao deterministica do esqueleto de PRDs.

    Uso:  python <skill-dir>/scripts/lint_prd.py
              <caminho-do-prd.md | diretorio> [...]
              [--lang pt|en] [--source <material>] [--reverse]

Um arquivo lint a esse arquivo; um diretorio lint a todos os PRDs abaixo
dele. As checagens entre PRDs (IDs, prefixos, PRD 0000, paragrafos repetidos)
sempre usam a pasta inteira: a raiz e o diretorio `prd` mais proximo acima do
arquivo, ou o proprio diretorio do arquivo. PRD e todo `NNNN-*.md` abaixo da
raiz (`README.md`, `assets/` e `archive/` ficam fora); arquivo passado
explicitamente fora dessa forma e erro de uso (exit 2). Na documentacao da
skill, `/docs/prd` e caminho relativo a raiz do repositorio; o chamador passa
o caminho real.

`--lang pt|en` fixa o idioma do PRD e liga a checagem de heading (WARN); sem
a opcao, o par PT/EN de cada heading vale igual. O idioma do PRD e fixado pela
precedencia da skill, nao por este script.

`--source <arquivo>` liga a checagem de reformatacao (WARN): as tres frases
mais longas do PRD (prosa com 12 ou mais palavras, fora de tabela, heading e
bloco de codigo) sao buscadas no material de discovery. A opcao se repete, uma
por arquivo de material, e o material e texto (`.md`, `.txt`, extracao de PDF);
sem a opcao, a checagem nao roda. A busca e literal, com espacos colapsados,
enfase markdown removida e caixa ignorada.

`--reverse` declara que o PRD e reverso (references/modes.md, Modo reverse
PRD) e estende o WARN de mecanismo a todas as secoes; sem a opcao, esse WARN
so varre Solucao Proposta e Requisitos Funcionais. O modo do PRD e fixado pelo
pedido, nao por este script.

O linter verifica o esqueleto, nao a qualidade: linter verde e esqueleto
conforme, nao PRD bom. Tudo dentro de bloco de codigo (``` ou ~~~, 3+
caracteres; fecha com o mesmo caractere e comprimento >= abertura) e
ignorado. O PRD nunca carrega resultado de lint: a saida e feedback para quem
escreve, que corrige e roda de novo.

O linter tambem nao julga os dois motivos de manter um HARD (SKILL.md, passo
Checar): o pedido da sessao, que precisa nomear literalmente a secao, o campo
ou a forma de onde o HARD sai, e a convencao do repositorio, que precisa
aparecer em tres ou mais PRDs commitados da pasta - conte os commitados com
`git ls-files` na pasta, o linter nao distingue arquivo commitado de arquivo em
elaboracao - ou estar escrita no AGENTS.md do repositorio.

HARD (exit 1):
  - titulo H1 ('# ...') ausente;
  - header sem a tabela de duas colunas entre o titulo e a linha de prefixo
    com um dos campos `**Contexto Originario**`, `**Modulo**` ou `**Area**`
    (`**Escopo**` na visao geral); a lista e fechada, e cada rotulo tem o par
    em ingles: `**Originating Context**`, `**Module**`, `**Area**`
    (`**Scope**`);
  - secao obrigatoria ausente: Resumo Executivo, Contexto e Problema,
    Usuario-alvo, Solucao Proposta e, quando o PRD define IDs, Requisitos
    Funcionais (heading casado por igualdade com os aliases PT/EN, nunca por
    substring);
  - PRD com IDs sem a linha `Prefixo dos requisitos: `X`.` entre o titulo e
    a primeira secao (em PRD em ingles, `Requirement prefix: `X`.`; sao essas
    as duas formas escritas - SKILL.md, Header); definicao
    `- **X-nn (Must)**` / `- **X-NFR-nn**` com prefixo diferente do
    declarado; `FR-nn` / `NFR-nn` sem prefixo;
  - FR definido sem prioridade MoSCoW (`- **X-nn (Must)**`); NFR nao leva
    MoSCoW;
  - citacao de ID sem definicao em nenhum PRD da pasta; ID definido mais de
    uma vez;
  - link Markdown `[texto](destino)` para arquivo local que nao resolve
    (destino relativo a pasta do PRD, `/docs/...` a partir da raiz do
    repositorio; ancora removida; URL com esquema, ancora pura, code span e
    bloco de codigo ficam fora);
  - PRD 0000: `<!-- prd: overview -->` na primeira linha identifica a visao
    geral; arquivo `0000-*` sem o comentario; visao geral fora do numero
    0000 (o numero dela e fixo e nao passa pelo contador de `seq.py`); visao
    geral definindo requisito; dois ou mais prefixos na pasta sem visao
    geral; pasta com visao geral e PRD cuja linha de prefixo nao a
    referencia por link local;
  - secao `##` fora da tabela de secoes, que e fechada: a tabela da secao
    Secoes de `references/writing.md` nos PRDs comuns, a da secao PRD 0000
    na visao geral. A primeira coluna de cada uma nomeia a secao em portugues
    e, entre parenteses, em ingles; as duas formas passam. Subsecao (`###` ou
    mais) fica de fora.

  Fora da visao geral, sobre as secoes (a tabela e a ordem estao em
  `references/writing.md`, secao Secoes):
  - secao presente com corpo vazio ou reduzido a "Nenhuma." / "Nenhum." /
    "N/A" / "Nao se aplica.";
  - secao conhecida fora da ordem da tabela;
  - bullet de Trade-offs Declarados sem `*Custo:*` ou sem `*Razao:*`;
  - Metricas de Sucesso sem nenhuma linha de guardrail;
  - Ponto de Maior Fragilidade seguido por outra secao que nao Referencias;
  - bullet de Perguntas em Aberto com "se falsa" ("if false") fora da
    primeira posicao, ou primeiro bullet com "se falsa" sem abrir em negrito
    (`- **`); bullet com "se falsa" fora de Perguntas em Aberto: a premissa
    que derruba o PRD e declarada uma vez, e e ela que faz a secao entrar;
  - contexto citado em `; afeta <lista>` no campo do header sem linha na
    primeira coluna da tabela de Dependencias e Riscos.

WARN (nao afeta o exit; julgue):
  - hedging; meta-narracao; mecanismo nomeado em Solucao Proposta ou
    Requisitos Funcionais - com `--reverse`, em qualquer secao do PRD;
  - tag entre colchetes fora de [PREMISSA] e [LACUNA] (texto sem tag e
    fato); placeholder (TBD, TODO, `[nome]`);
  - paragrafo de prosa identico em mais de um PRD (12+ palavras);
  - citacao com prefixo que nenhum PRD da pasta declara;
  - Resumo Executivo ou Alinhamento Estrategico com menos de 3 ou mais de 5
    frases;
  - bullet de Trade-offs Declarados com mais de 2 linhas (a continuacao
    indentada conta);
  - cenario Dado/Quando/Entao (Given/When/Then) de Criterios de Aceitacao
    sem citar nenhum ID;
  - bullet de Consideracoes Regulatorias que nao aponta ID depois de `->`
    (`->` ou `→`; ID entre colchetes ou parenteses tambem vale). A linha de
    fonte e data no topo da secao, sem bullet, nao conta, e o bullet que abre
    com `[LACUNA]` fica de fora: norma nao identificada nao tem artigo a
    mapear;
  - nota de mais de 20 palavras depois do ultimo ID do mesmo bullet: o que
    nao cabe na nota e regra e vive no FR;
  - rotulo de transicao, aresta ou mensagem de `stateDiagram-v2`,
    `flowchart` ou `sequenceDiagram` sem ID: o diagrama e indice, nao
    segunda fonte;
  - `stateDiagram-v2` sem nenhuma tabela com coluna Identificador;
  - com `--lang`, heading de secao conhecida cujo alias e do outro idioma
    ('## Open Questions' com `--lang pt`). Alias sem idioma proprio (JTBD,
    persona, trade-offs, Domain Events) nunca acusa;
  - com `--source`, uma das tres frases mais longas do PRD encontrada no
    material: reformatar o material nao e sintetizar.

Saida: `HARD  Lnn  mensagem` / `WARN  Lnn  mensagem` por PRD e um resumo.
Exit 2 em erro de uso (opcao ou arquivo invalido).
"""

import os
import re
import sys
import unicodedata

# Secoes cujo heading precisa ser IGUAL a um alias (norm_heading). Substring
# nao serve: "non-functional requirements" contem "functional requirements".
SECTIONS = {
    "resumo": ("resumo executivo", "sumario executivo", "executive summary"),
    "alinhamento": ("alinhamento estrategico", "strategic alignment"),
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
    "oportunidade": (
        "oportunidade / hipotese", "oportunidade/hipotese", "oportunidade",
        "hipotese", "opportunity / hypothesis", "opportunity/hypothesis",
        "opportunity", "hypothesis",
    ),
    "solucao": ("solucao proposta", "proposed solution"),
    "glossario": (
        "glossario de dominio", "glossario", "domain glossary", "glossary",
    ),
    "frs": ("requisitos funcionais", "functional requirements"),
    "eventos": ("domain events", "eventos de dominio", "eventos"),
    "nfrs": (
        "requisitos nao funcionais", "requisitos nao-funcionais",
        "non-functional requirements", "non functional requirements",
        "nonfunctional requirements",
    ),
    "regulatorio": (
        "consideracoes regulatorias", "regulatory considerations",
    ),
    "nao_objetivos": (
        "nao-objetivos", "nao objetivos", "non-goals", "non goals",
    ),
    "tradeoffs": (
        "trade-offs declarados", "tradeoffs declarados", "trade-offs",
        "tradeoffs", "declared trade-offs", "declared tradeoffs",
    ),
    "metricas": ("metricas de sucesso", "metricas", "success metrics"),
    "aceitacao": ("criterios de aceitacao", "acceptance criteria"),
    "dependencias": (
        "dependencias e riscos", "dependencies and risks",
        "dependencies & risks",
    ),
    "perguntas": ("perguntas em aberto", "open questions"),
    "fragilidade": (
        "ponto de maior fragilidade", "weakest point", "biggest weakness",
    ),
    "referencias": ("referencias", "references"),
}
# Secoes da tabela de `references/writing.md`, secao PRD 0000: a visao geral
# tem lista propria, fechada do mesmo jeito. O teste de sincronizacao cobra a
# correspondencia com a tabela.
OVERVIEW_SECTIONS = {
    "proposito": ("proposito", "purpose"),
    "contextos": ("contextos", "contexts"),
    "eventos": ("catalogo de eventos", "event catalog", "event catalogue"),
    "fluxos": ("fluxos entre contextos", "flows between contexts"),
    "termos": ("termos por contexto", "terms per context"),
    "adr": ("decisoes delegadas a adr", "decisions delegated to adr"),
}
# Ordem da tabela de `references/writing.md`, secao Secoes.
SECTION_ORDER = [
    "resumo", "alinhamento", "contexto", "usuario", "oportunidade", "solucao",
    "glossario", "frs", "eventos", "nfrs", "regulatorio", "nao_objetivos",
    "tradeoffs", "metricas", "aceitacao", "dependencias", "perguntas",
    "fragilidade", "referencias",
]
# Idioma de cada alias de SECTIONS, para `--lang`. Alias neutro e o termo que a
# skill nao traduz (Domain Events) ou que e o mesmo nos dois idiomas (JTBD,
# persona, trade-offs): nunca acusa. Todo alias de SECTIONS esta em exatamente
# um dos tres conjuntos - o teste de sincronizacao cobra isso.
ALIAS_NEUTRAL = frozenset((
    "jtbd", "persona", "personas", "trade-offs", "tradeoffs", "domain events",
))
ALIAS_EN = frozenset((
    "executive summary", "strategic alignment", "context and problem",
    "context & problem", "context", "problem", "problem statement",
    "background", "target user / jtbd", "target user", "target users",
    "users", "opportunity / hypothesis", "opportunity/hypothesis",
    "opportunity", "hypothesis", "proposed solution", "domain glossary",
    "glossary", "functional requirements", "non-functional requirements",
    "non functional requirements", "nonfunctional requirements",
    "regulatory considerations", "non-goals", "non goals",
    "declared trade-offs", "declared tradeoffs", "success metrics",
    "acceptance criteria", "dependencies and risks", "dependencies & risks",
    "open questions", "weakest point", "biggest weakness", "references",
))
ALIAS_PT = frozenset((
    "resumo executivo", "sumario executivo", "alinhamento estrategico",
    "contexto e problema", "contexto", "problema", "contexto e problem",
    "usuario-alvo / jtbd", "usuario-alvo", "usuario alvo", "usuarios-alvo",
    "usuarios-alvo / jtbd", "usuario-alvo e jtbd", "usuarios",
    "oportunidade / hipotese", "oportunidade/hipotese", "oportunidade",
    "hipotese", "solucao proposta", "glossario de dominio", "glossario",
    "requisitos funcionais", "eventos de dominio", "eventos",
    "requisitos nao funcionais", "requisitos nao-funcionais",
    "consideracoes regulatorias", "nao-objetivos", "nao objetivos",
    "trade-offs declarados", "tradeoffs declarados", "metricas de sucesso",
    "metricas", "criterios de aceitacao", "dependencias e riscos",
    "perguntas em aberto", "ponto de maior fragilidade", "referencias",
))
LANGS = {"pt": ALIAS_PT, "en": ALIAS_EN}

LABELS = {
    "resumo": "Resumo Executivo",
    "contexto": "Contexto e Problema",
    "usuario": "Usuario-alvo / JTBD",
    "solucao": "Solucao Proposta",
    "frs": "Requisitos Funcionais",
}
REQUIRED = ["resumo", "contexto", "usuario", "solucao"]
# Contagens da tabela de secoes de `references/writing.md`.
SUMMARY_SECTIONS = ("resumo", "alinhamento")
SUMMARY_MIN_SENTENCES = 3
SUMMARY_MAX_SENTENCES = 5
SENTENCE_END = re.compile(r"[.!?](?:\s|$)")
TRADEOFF_MAX_LINES = 2

ALLOWED_TAGS = {"PREMISSA", "LACUNA"}

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
HEDGING = ["provavelmente", "talvez", "na verdade", "poderia", "muito",
           "probably", "perhaps", "could", "very"]
META_OPENERS = [
    "este prd", "este documento", "neste prd", "neste documento",
    "vamos discutir", "é importante notar", "e importante notar",
    "vale notar", "this prd", "this document", "it's important to note",
    "we will discuss", "in this document",
]
PLACEHOLDER_WORDS = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b")  # caixa alta: "todo" em PT-BR
PLACEHOLDER_LOREM = re.compile(r"\blorem ipsum\b", re.IGNORECASE)
PLACEHOLDER_SLOTS = re.compile(
    r"\[(nome|name|contexto|context|autor|author|data|date)\]", re.IGNORECASE)
MIN_PARAGRAPH_WORDS = 12

ID_DEF = re.compile(
    r"^\s*[-*]\s+\*\*([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})"
    r"(\s*\((?:Must|Should|Could|Won'?t|Won’t)[^)]*\))?\*\*")
ID_REF = re.compile(r"\b([A-Z][A-Z0-9]{1,9})-(NFR-)?(\d{2,})\b")
PREFIX_LINE = re.compile(
    r"^\s*(?:Prefixo dos requisitos|Requirement prefix|Prefixo|Prefix)\s*:\s*"
    r"`?([A-Z][A-Z0-9]{1,9})`?", re.IGNORECASE)
BARE_PREFIXES = {"FR", "NFR"}
BACKTICK_PREFIX = re.compile(r"`([A-Z][A-Z0-9]{1,9})`")
OVERVIEW_COMMENT = re.compile(r"<!--\s*prd:\s*overview\s*-->")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
NUMBERED_MD = re.compile(r"^(\d{4})-[^/\\]+\.md$", re.IGNORECASE)
SKIP_DIRS = {"node_modules", "assets", "archive"}
MD_LINK = re.compile(r"\[[^\]]*\]\(\s*(?:<([^>]*)>|([^)\s]+))(?:\s+\"[^\"]*\")?\s*\)")
URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:")
CODE_SPAN = re.compile(r"`[^`]*`")
HEADING = re.compile(r"^(#{2,6})\s+(\S.*)$")
BULLET = re.compile(r"^\s{0,3}[-*+]\s+")
# Corpo de secao reduzido a uma dessas linhas conta como secao sem conteudo.
NO_CONTENT_LINES = frozenset(("nenhuma", "nenhum", "n/a", "nao se aplica"))

# Campo de contexto da tabela do header (SKILL.md, Gravar): lista fechada de
# rotulos aceitos, cada um mapeado ao nome usado na mensagem. A visao geral usa
# outro campo.
HEADER_FIELD = {
    "contexto originario": "Contexto Originario",
    "originating context": "Contexto Originario",
    "modulo": "Modulo",
    "module": "Modulo",
    "area": "Area",
}
HEADER_FIELD_OVERVIEW = {"escopo": "Escopo", "scope": "Escopo"}
TABLE_ROW = re.compile(r"^\s{0,3}\|(.*)\|\s*$")
SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")
IDENTIFIER_COLUMN = ("identificador", "identifier")
# Contexto afetado declarado no campo do header: `<contexto>; afeta A, B e C`.
AFFECTS = re.compile(r";\s*afeta\s+(\S.*)$", re.IGNORECASE)
AFFECTS_SEPARATOR = re.compile(r",|\s+e\s+")

# Perguntas em Aberto: a premissa que, se falsa, derruba a abordagem do PRD.
FALSE_PREMISE = re.compile(r"\bse\s+falsa\b|\bif\s+false\b")
BOLD_OPEN = re.compile(r"^\*\*\S")

# Cenario de Criterios de Aceitacao: os tres marcadores na mesma entrada.
GWT_MARKERS = (("dado", "quando", "entao"), ("given", "when", "then"))

# Consideracoes Regulatorias: `o que a norma diz -> ID`. Norma nao
# identificada abre o bullet com `[LACUNA]` e nao aponta ID. Depois do ID cabe
# uma nota curta (tabela de secoes de `references/writing.md`); o que nao cabe
# nela e regra e vive no FR.
ARROW = re.compile(r"->|→")
GAP_BULLET = re.compile(r"^[*`\s]*\[LACUNA\]")
REGULATORY_NOTE_MAX_WORDS = 20
NOTE_LEAD = re.compile(r"^[\s.,;:)\]}*`_\-–—]+")

# `--source`: as tres frases mais longas do PRD nao aparecem no material de
# discovery (`references/intake.md`, Material de discovery). O piso de palavras
# tira da disputa a frase curta, que casa com qualquer material por acaso.
SOURCE_SENTENCES = 3
SOURCE_MIN_WORDS = 12
EMPHASIS = re.compile(r"[*_`]")

# Rotulos de diagrama Mermaid.
MERMAID_OPEN = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*mermaid\s*$", re.IGNORECASE)
STATE_TRANSITION = re.compile(r"-{2,}>\s*[^:]+:\s*(\S.*)$")
FLOW_EDGE_PIPE = re.compile(r"-{2,}>\s*\|([^|]*)\|")
FLOW_EDGE_MID = re.compile(r"(?:^|[^-<>])-{2,}\s*(\"[^\"]*\"|[^\"\-|>]+?)\s*-{2,}>")
SEQ_MESSAGE = re.compile(
    r"^\s*[A-Za-z0-9_]+\s*(?:-{1,2}>>?|-{1,2}\)|-{1,2}x)\s*[A-Za-z0-9_]+\s*:\s*(\S.*)$")


def _mark(alternatives):
    """`*Custo:*`, `**Custo:**` e `*Custo*:`, sobre o texto ja normalizado."""
    return re.compile(r"\*{1,2}\s*(?:" + alternatives + r")\s*:\s*\*{1,2}"
                      r"|\*{1,2}\s*(?:" + alternatives + r")\s*\*{1,2}\s*:")


COST_MARK = _mark("custo|cost")
REASON_MARK = _mark("razao|reason")


def norm(s):
    """Minusculas sem acento, para casar titulo de secao PT/EN."""
    d = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in d if unicodedata.category(c) != "Mn")


def norm_heading(s):
    s = re.sub(r"^#+\s*", "", s.strip())
    s = re.sub(r"[*_`]", "", s)
    s = norm(s)
    return re.sub(r"\s+", " ", s).strip(" :.")


def heading_variants(s):
    """O titulo inteiro e, se houver parentese final, cada metade:
    'Contexto e Problema (Context and Problem)' casa PT ou EN."""
    h = norm_heading(s)
    out = [h]
    pm = re.match(r"^(.*?)\s*\(([^()]*)\)$", h)
    if pm:
        out += [pm.group(1).strip(), pm.group(2).strip()]
    return out


def heading_in(table, key, heading):
    """O titulo casa um alias de `table[key]` (SECTIONS ou OVERVIEW_SECTIONS)."""
    return any(v in table[key] for v in heading_variants(heading))


def heading_is(key, heading):
    return heading_in(SECTIONS, key, heading)


def fence_mask(lines):
    """True por linha dentro de bloco de codigo, fences inclusos. Abre com
    >=3 crases ou tils; fecha com o mesmo caractere, comprimento >= abertura
    e nada mais na linha."""
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
        if s and set(s) == {open_fence[0]} and len(s) >= len(open_fence):
            open_fence = None
    return mask


def strip_md_prefix(s):
    """Remove marcadores markdown de inicio de linha (lista, heading, citacao)."""
    return re.sub(r"^[\s>#*\-]+", "", s)


def is_tag_like(token):
    """True se o token parece uma tag (maiusculas, len>=2)."""
    return len(token) >= 2 and bool(re.fullmatch(r"[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ\-]*", token))


def prd_number(path):
    m = NUMBERED_MD.match(os.path.basename(path))
    return int(m.group(1)) if m else None


def is_prd_path(path):
    return bool(NUMBERED_MD.match(os.path.basename(path)))


def repo_root_for(path):
    """Primeiro ancestral do arquivo que contem `docs/`, ou None."""
    cur = os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.isdir(os.path.join(cur, "docs")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def link_targets(raw):
    """Destino de cada link Markdown da linha, fora de code span."""
    for m in MD_LINK.finditer(CODE_SPAN.sub("", raw)):
        target = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if target:
            yield target


def resolve_link(doc, target):
    """Path procurado por um link local: relativo a pasta do PRD, ou a raiz do
    repositorio quando comeca por `/`. None quando o link nao e local (URL com
    esquema, ancora pura)."""
    if URL_SCHEME.match(target) or target.startswith("#"):
        return None
    rel = target.split("#", 1)[0]
    if not rel:
        return None
    if rel.startswith("/"):
        root = repo_root_for(doc.path)
        if root is None:
            return f"<raiz>{rel}"
        return os.path.normpath(os.path.join(root, rel.lstrip("/")))
    base = os.path.dirname(os.path.abspath(doc.path))
    return os.path.normpath(os.path.join(base, rel))


def local_link_findings(doc):
    """(linha_1based, destino, path_procurado) por link Markdown local que
    nao resolve."""
    out = []
    for i, raw in enumerate(doc.lines):
        if not doc.visible(i):
            continue
        for target in link_targets(raw):
            expected = resolve_link(doc, target)
            if expected is not None and not os.path.exists(expected):
                out.append((i + 1, target, expected))
    return out


class Section:
    """Heading de nivel >= 2 e o corpo ate a proxima heading de nivel <= o seu.

    `key` e a chave de SECTIONS quando o titulo casa um alias, senao None.
    `line` e a linha 1-based do heading; `body` sao as linhas cruas do corpo.
    """

    def __init__(self, level, title, index, key, body):
        self.level = level
        self.title = title
        self.index = index      # 0-based, linha do heading
        self.key = key
        self.body = body

    @property
    def line(self):
        return self.index + 1

    def body_lines(self):
        """(linha_1based, texto) de cada linha do corpo."""
        return [(self.index + 2 + k, raw) for k, raw in enumerate(self.body)]


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
        self.number = prd_number(path)
        self.is_overview = False
        self.prefix = None
        self.prefix_line = None
        self.defs = []        # (id, line_1based)
        self.defs_no_moscow = []  # (id, line_1based) de FR sem MoSCoW
        self.refs = []        # (id, prefix, line_1based)
        self.paragraphs = []  # (normalized_text, line_1based)
        self.h1_idx = None
        self.scan()

    @property
    def label(self):
        return os.path.basename(self.path)

    def add_hard(self, msg, line=None):
        self.hard.append((line, msg))

    def add_warn(self, msg, line=None):
        self.warn.append((line, msg))

    def visible(self, i):
        return not self.fenced[i]

    def scan(self):
        self.is_overview = any(self.visible(i) and OVERVIEW_COMMENT.search(l)
                               for i, l in enumerate(self.lines))
        self.h1_idx = next((i for i, ln in enumerate(self.lines)
                            if self.visible(i) and re.match(r"#\s+\S", ln)), None)
        if self.h1_idx is not None:
            for i in range(self.h1_idx + 1, len(self.lines)):
                if self.lines[i].startswith("## "):
                    break
                pm = PREFIX_LINE.match(self.lines[i])
                if pm and self.visible(i):
                    self.prefix = pm.group(1)
                    self.prefix_line = i + 1
                    break
        for i, raw in enumerate(self.lines):
            if not self.visible(i):
                continue
            dm = ID_DEF.match(raw)
            if dm:
                rid = f"{dm.group(1)}-{dm.group(2) or ''}{dm.group(3)}"
                self.defs.append((rid, i + 1))
                if not dm.group(2) and not dm.group(4):
                    self.defs_no_moscow.append((rid, i + 1))
            for rm in ID_REF.finditer(raw):
                self.refs.append((f"{rm.group(1)}-{rm.group(2) or ''}{rm.group(3)}",
                                  rm.group(1), i + 1))
            s = raw.strip()
            if s and s[0] not in "#|-*>" and not s.startswith("<!--") \
                    and not PREFIX_LINE.match(s):
                body = re.sub(r"\s+", " ", s).lower()
                if len(body.split()) >= MIN_PARAGRAPH_WORDS:
                    self.paragraphs.append((body, i + 1))

    def body_start(self):
        return (self.h1_idx + 1) if self.h1_idx is not None else 0

    def headings(self):
        return [self.lines[i].strip() for i in range(self.body_start(), len(self.lines))
                if self.visible(i) and re.match(r"^##\s+", self.lines[i].strip())]

    def has_section(self, key):
        return any(heading_is(key, h) for h in self.headings())

    def sections(self):
        heads = []
        for i in range(self.body_start(), len(self.lines)):
            if not self.visible(i):
                continue
            m = HEADING.match(self.lines[i].strip())
            if m:
                heads.append((i, len(m.group(1)), m.group(2).strip()))
        out = []
        for n, (i, level, title) in enumerate(heads):
            end = len(self.lines)
            for j, lvl, _ in heads[n + 1:]:
                if lvl <= level:
                    end = j
                    break
            key = next((k for k in SECTION_ORDER if heading_is(k, title)), None)
            out.append(Section(level, title, i, key, self.lines[i + 1:end]))
        return out


def is_no_content(body):
    """Corpo vazio, ou uma unica linha de nao-conteudo ('Nenhuma.', 'N/A')."""
    filled = [l for l in body if l.strip()]
    if not filled:
        return True
    if len(filled) > 1:
        return False
    s = re.sub(r"[*_`]", "", strip_md_prefix(filled[0]))
    return norm(s).strip().rstrip(".").strip() in NO_CONTENT_LINES


def section_bullets(section):
    """(linha_1based, texto, linhas) por bullet de primeiro nivel; linha
    seguinte nao vazia que nao abre bullet continua o bullet anterior e conta
    como mais uma linha dele."""
    out = []
    open_bullet = False
    for line, raw in section.body_lines():
        if BULLET.match(raw):
            out.append([line, raw.strip(), 1])
            open_bullet = True
        elif not raw.strip():
            open_bullet = False
        elif open_bullet:
            out[-1][1] += " " + raw.strip()
            out[-1][2] += 1
    return [tuple(b) for b in out]


def table_cells(raw):
    """Celulas de uma linha de tabela Markdown, ou None se nao for uma."""
    m = TABLE_ROW.match(raw)
    return [c.strip() for c in m.group(1).split("|")] if m else None


def table_headers(doc):
    """Celulas de cada linha de tabela seguida da linha separadora."""
    out = []
    for i, raw in enumerate(doc.lines[:-1]):
        if not doc.visible(i):
            continue
        cells = table_cells(raw)
        sep = table_cells(doc.lines[i + 1])
        if cells and sep and all(SEPARATOR_CELL.match(c) for c in sep):
            out.append(cells)
    return out


def cites_id(text):
    """True se o texto cita ao menos um `<PREFIXO>-nn` com prefixo de contexto."""
    return any(m.group(1) not in BARE_PREFIXES for m in ID_REF.finditer(text))


def header_rows(doc):
    """(linha_1based, celulas) por linha de tabela do header: entre o titulo e
    a linha de prefixo, ou a primeira secao quando nao ha prefixo."""
    if doc.h1_idx is None:
        return []
    end = doc.prefix_line - 1 if doc.prefix_line else next(
        (i for i in range(doc.h1_idx + 1, len(doc.lines))
         if doc.visible(i) and doc.lines[i].strip().startswith("## ")), len(doc.lines))
    out = []
    for i in range(doc.h1_idx + 1, end):
        cells = table_cells(doc.lines[i]) if doc.visible(i) else None
        if cells:
            out.append((i + 1, cells))
    return out


def affected_contexts(doc):
    """(linha_1based, contextos) do `; afeta A, B e C` do campo de contexto do
    header; sem o campo ou sem o `afeta`, a lista e vazia."""
    fields = HEADER_FIELD_OVERVIEW if doc.is_overview else HEADER_FIELD
    for line, cells in header_rows(doc):
        if len(cells) < 2 or norm_heading(cells[0]) not in fields:
            continue
        m = AFFECTS.search(cells[1])
        if not m:
            return line, []
        names = [n.strip().strip(".") for n in AFFECTS_SEPARATOR.split(m.group(1))]
        return line, [n for n in names if n]
    return None, []


def section_table_keys(doc, key):
    """Primeira celula de cada linha de tabela da secao, sem a separadora."""
    out = []
    for sec in doc.sections():
        if sec.key != key:
            continue
        for _, raw in sec.body_lines():
            cells = table_cells(raw)
            if cells and not all(SEPARATOR_CELL.match(c) for c in cells):
                out.append(cells[0])
    return out


def mermaid_blocks(doc):
    """(linha_1based_da_abertura, tipo, [(linha_1based, texto)]) por bloco
    ```mermaid; o tipo e a primeira linha nao vazia do bloco."""
    out, i, lines = [], 0, doc.lines
    while i < len(lines):
        m = MERMAID_OPEN.match(lines[i])
        if not m:
            i += 1
            continue
        fence, body, j = m.group(1), [], i + 1
        while j < len(lines):
            s = lines[j].strip()
            if s and set(s) == {fence[0]} and len(s) >= len(fence):
                break
            body.append((j + 1, lines[j]))
            j += 1
        kind = next((raw.strip() for _, raw in body if raw.strip()), "")
        out.append((i + 1, kind, body))
        i = j + 1
    return out


def diagram_labels(kind, raw):
    """Rotulos de transicao, aresta ou mensagem na linha, pelo tipo do bloco."""
    k = norm(kind)
    if k.startswith("statediagram"):
        m = STATE_TRANSITION.search(raw)
        return [m.group(1).strip()] if m else []
    if k.startswith("flowchart") or k.startswith("graph"):
        return [g.strip().strip('"') for g in
                FLOW_EDGE_PIPE.findall(raw) + FLOW_EDGE_MID.findall(raw)]
    if k.startswith("sequencediagram"):
        m = SEQ_MESSAGE.match(raw)
        return [m.group(1).strip()] if m else []
    return []


def check_fr_moscow(doc):
    """FR definido sem MoSCoW; NFR nao leva prioridade."""
    for rid, ln in doc.defs_no_moscow:
        doc.add_hard(f"requisito {rid} definido sem prioridade MoSCoW; a forma e "
                     f"'- **{rid} (Must)** condicao.' (Must, Should, Could ou "
                     "Won't; NFR nao leva MoSCoW).", ln)


def check_header_field(doc):
    """Tabela do header com um dos campos de contexto do tipo de PRD."""
    fields = HEADER_FIELD_OVERVIEW if doc.is_overview else HEADER_FIELD
    for line, cells in header_rows(doc):
        label = fields.get(norm_heading(cells[0])) if len(cells) >= 2 else None
        if label:
            if not cells[1]:
                doc.add_hard(f"campo '{label}' do header sem valor.", line)
            return
    accepted = [f"'{n}'" for n in dict.fromkeys(fields.values())]
    names = " ou ".join([", ".join(accepted[:-1]), accepted[-1]] if len(accepted) > 1
                        else accepted)
    doc.add_hard(f"header sem o campo {names}: entre o titulo e a linha de "
                 "prefixo vai uma tabela de duas colunas com um desses campos.",
                 doc.h1_idx + 1)


def check_affects_dependencies(doc):
    """Cada contexto do `; afeta` do header abre uma linha de Dependencias e
    Riscos: acoplamento declarado no header sem linha na tabela e acoplamento
    sem tipo nem impacto."""
    line, affected = affected_contexts(doc)
    if not affected:
        return
    keys = [norm(c) for c in section_table_keys(doc, "dependencias")]
    for name in affected:
        if not any(norm(name) in k for k in keys):
            doc.add_hard(f"contexto afetado sem linha em Dependencias e Riscos: "
                         f"'{name}'. O header declara que o PRD o afeta; a "
                         "tabela diz qual e o acoplamento e o impacto.", line)


def check_scenario_cites_id(doc):
    """Cenario Dado/Quando/Entao de Criterios de Aceitacao cita o FR que exercita."""
    for sec in doc.sections():
        if sec.key != "aceitacao":
            continue
        for line, text, _ in section_bullets(sec):
            words = set(re.findall(r"[a-z]+", norm(text)))
            if not any(all(w in words for w in group) for group in GWT_MARKERS):
                continue
            if not cites_id(text):
                doc.add_warn("cenario Dado/Quando/Entao sem ID de requisito: "
                             f"'{strip_md_prefix(text)[:50]}'. Cada cenario cita "
                             "o FR que exercita.", line)


def regulatory_note(tail):
    """Nota do bullet regulatorio: o texto depois do ultimo ID citado no trecho
    que vem apos a seta."""
    last = None
    for m in ID_REF.finditer(tail):
        if m.group(1) not in BARE_PREFIXES:
            last = m
    return NOTE_LEAD.sub("", tail[last.end():]).strip() if last else ""


def check_regulatory_lines(doc):
    """Bullet de Consideracoes Regulatorias termina apontando o ID que modela a
    norma: `o que a norma diz -> ID`, e depois do ID cabe uma nota de ate 20
    palavras. A linha de fonte e data, sem bullet, fica de fora, e o bullet que
    abre com `[LACUNA]` tambem: norma nao identificada nao tem artigo a
    mapear."""
    for sec in doc.sections():
        if sec.key != "regulatorio":
            continue
        for line, text, _ in section_bullets(sec):
            body = strip_md_prefix(text).strip()
            if GAP_BULLET.match(body):
                continue
            tail = ARROW.split(body)[-1] if ARROW.search(body) else None
            if tail is None or not cites_id(tail):
                doc.add_warn(f"bullet regulatorio sem '-> ID': '{body[:50]}'. O "
                             "bullet termina no ID que modela a norma; norma sem "
                             "ID nao entra.", line)
                continue
            note = regulatory_note(tail)
            words = len(note.split())
            if words > REGULATORY_NOTE_MAX_WORDS:
                doc.add_warn(f"nota de {words} palavras depois do ID: "
                             f"'{note[:50]}'. A nota vai ate "
                             f"{REGULATORY_NOTE_MAX_WORDS} palavras; o que nao "
                             "couber e regra e vive no FR.", line)


def search_key(s):
    """Texto comparavel na busca de `--source`: sem enfase markdown, espacos
    colapsados e caixa ignorada."""
    return re.sub(r"\s+", " ", EMPHASIS.sub("", s)).casefold().strip()


def split_sentences(text):
    """Frases de uma linha de prosa, cortadas em `.`, `!` ou `?` seguidos de
    espaco ou fim de linha."""
    out, start = [], 0
    for m in SENTENCE_END.finditer(text):
        out.append(text[start:m.end()])
        start = m.end()
    out.append(text[start:])
    return [s.strip() for s in out if s.strip()]


def prose_sentences(doc):
    """(linha_1based, frase) de cada frase de prosa do PRD, na ordem do
    arquivo. Bloco de codigo, heading, linha de tabela, comentario e a linha de
    prefixo ficam de fora; marcador de lista e enfase saem do texto."""
    out = []
    for i, raw in enumerate(doc.lines):
        if not doc.visible(i):
            continue
        s = raw.strip()
        if not s or s[0] in "#|" or s.startswith("<!--") or PREFIX_LINE.match(s):
            continue
        text = re.sub(r"\s+", " ", EMPHASIS.sub("", strip_md_prefix(s))).strip()
        for sentence in split_sentences(text):
            out.append((i + 1, sentence))
    return out


def longest_sentences(doc, count=SOURCE_SENTENCES):
    """As `count` frases mais longas do PRD, da maior para a menor; empate se
    decide pela ordem no arquivo. Frase com menos de SOURCE_MIN_WORDS palavras
    nao disputa."""
    candidates = [(line, s) for line, s in prose_sentences(doc)
                  if len(s.split()) >= SOURCE_MIN_WORDS]
    return sorted(candidates, key=lambda x: (-len(x[1]), x[0]))[:count]


def check_source_reformat(doc, sources):
    """Nenhuma das tres frases mais longas do PRD aparece no material de
    discovery: sintetizar nao e reformatar, e a frase que sobreviveu literal
    veio do material sem passar por sintese."""
    for line, sentence in longest_sentences(doc):
        key = search_key(sentence)
        if not key:
            continue
        for label, text in sources:
            if key in text:
                doc.add_warn(f"frase do PRD encontrada em {label}: "
                             f"'{sentence[:50]}'. Uma das tres frases mais "
                             "longas do PRD esta literal no material; sintetize "
                             "em vez de reformatar.", line)
                break


def check_diagram_labels(doc):
    """Rotulo de diagrama cita o ID: o diagrama e indice, nao segunda fonte."""
    for _, kind, body in mermaid_blocks(doc):
        for line, raw in body:
            for label in diagram_labels(kind, raw):
                if label and not cites_id(label):
                    doc.add_warn(f"rotulo sem ID no diagrama: '{label[:50]}'. O "
                                 "rotulo cita o requisito que governa a "
                                 "transicao; o diagrama e indice, nao segunda "
                                 "fonte.", line)


def check_state_identifier_column(doc):
    """Ao lado do stateDiagram-v2 vai a tabela com coluna Identificador."""
    blocks = [(line, kind) for line, kind, _ in mermaid_blocks(doc)
              if norm(kind).startswith("statediagram")]
    if not blocks:
        return
    for cells in table_headers(doc):
        if any(norm_heading(c) in IDENTIFIER_COLUMN for c in cells):
            return
    doc.add_warn("stateDiagram-v2 sem tabela com coluna Identificador; o codigo "
                 "carrega o nome de cada estado, e nome inventado fora do PRD e "
                 "decisao de linguagem tomada fora dele.", blocks[0][0])


def check_overview_reference(doc, overview):
    """A linha de prefixo referencia o PRD 0000 por link local."""
    if not doc.prefix_line:
        return
    want = os.path.normcase(os.path.abspath(overview.path))
    for target in link_targets(doc.lines[doc.prefix_line - 1]):
        got = resolve_link(doc, target)
        if got and os.path.normcase(os.path.abspath(got)) == want:
            return
    doc.add_hard(f"linha de prefixo sem link para o PRD 0000 ({overview.label}); "
                 "a pasta tem visao geral, e cada PRD a referencia ali em vez de "
                 "repetir proposito, mapa de contextos e catalogo de eventos.",
                 doc.prefix_line)


def check_empty_sections(doc):
    for sec in doc.sections():
        if is_no_content(sec.body):
            doc.add_hard(f"secao sem conteudo: {sec.title}. Secao vazia ou "
                         "reduzida a 'Nenhuma.' e defeito: preencha ou remova "
                         "a secao.", sec.line)


def check_unknown_sections(doc):
    """Toda secao `##` esta na tabela de writing.md. A tabela e fechada: secao
    fora dela nao tem criterio de entrada nem posicao, e entraria por forma. A
    visao geral responde a tabela da secao PRD 0000; os demais PRDs, a de
    Secoes. Subsecao (`###` ou mais) nao e cobrada: a tabela nomeia secoes."""
    if doc.is_overview:
        table, source = OVERVIEW_SECTIONS, "PRD 0000"
    else:
        table, source = SECTIONS, "Secoes"
    for sec in doc.sections():
        if sec.level != 2 or any(heading_in(table, k, sec.title) for k in table):
            continue
        doc.add_hard(f"secao fora da tabela: '{sec.title}'. A tabela da secao "
                     f"{source} de references/writing.md e fechada; use a secao "
                     "da tabela que cobre esse conteudo, com o nome da primeira "
                     "coluna no idioma do PRD (o de fora dos parenteses em pt, "
                     "o de dentro em en; ver --lang), ou mova o conteudo para "
                     "ela.", sec.line)


def check_section_order(doc):
    """As secoes conhecidas seguem a ordem da tabela de writing.md."""
    known = [(SECTION_ORDER.index(s.key), s.title, s.line)
             for s in doc.sections() if s.level == 2 and s.key]
    latest = None
    for idx, title, line in known:
        if latest and idx < latest[0]:
            doc.add_hard(f"secao fora de ordem: '{latest[1]}' aparece antes de "
                         f"'{title}', que deveria precede-la; a ordem e a da "
                         "tabela de secoes em references/writing.md.", line)
        else:
            latest = (idx, title)


def check_heading_language(doc, lang):
    """Heading de secao conhecida esta no idioma fixado. O heading passa quando
    algum de seus aliases e do idioma ou e neutro; alias do outro idioma e WARN,
    porque o PRD fala um idioma so."""
    other = "en" if lang == "pt" else "pt"
    for sec in doc.sections():
        if not sec.key:
            continue
        matched = [v for v in heading_variants(sec.title) if v in SECTIONS[sec.key]]
        if not matched or any(v in ALIAS_NEUTRAL or v in LANGS[lang] for v in matched):
            continue
        doc.add_warn(f"heading em {other} num PRD em {lang}: '{sec.title}'. Use o "
                     f"alias {lang} da tabela de secoes (references/writing.md); "
                     "o PRD fala um idioma so.", sec.line)


def check_tradeoff_cost_and_reason(doc):
    for sec in doc.sections():
        if sec.key != "tradeoffs":
            continue
        for line, text, count in section_bullets(sec):
            body = norm(text)
            missing = [name for name, rx in (("Custo", COST_MARK),
                                             ("Razao", REASON_MARK))
                       if not rx.search(body)]
            if missing:
                doc.add_hard(f"trade-off sem {' e sem '.join(missing)}: "
                             f"'{strip_md_prefix(text)[:50]}'. A forma e "
                             "'**Decisao.** *Custo:* ... *Razao:* ...'.", line)
            if count > TRADEOFF_MAX_LINES:
                doc.add_warn(f"trade-off com {count} linhas: "
                             f"'{strip_md_prefix(text)[:50]}'. O bullet vai ate "
                             f"{TRADEOFF_MAX_LINES} linhas; o que nao couber e "
                             "regra e vive no FR.", line)


def check_summary_length(doc):
    """Resumo Executivo e Alinhamento Estrategico cabem em 3 a 5 frases: menos
    e resumo que nao resume, mais e a secao virando o PRD de novo."""
    for sec in doc.sections():
        if sec.key not in SUMMARY_SECTIONS:
            continue
        count = sum(len(SENTENCE_END.findall(l)) for l in sec.body if l.strip())
        if SUMMARY_MIN_SENTENCES <= count <= SUMMARY_MAX_SENTENCES:
            continue
        doc.add_warn(f"secao {sec.title} com {count} frase(s); a forma e um paragrafo de "
                     f"{SUMMARY_MIN_SENTENCES}-{SUMMARY_MAX_SENTENCES} frases "
                     "(references/writing.md, tabela de secoes).", sec.line)


def check_metric_guardrail(doc):
    for sec in doc.sections():
        if sec.key == "metricas" and not any("guardrail" in norm(l) for l in sec.body):
            doc.add_hard(f"secao {sec.title} sem nenhuma linha de guardrail; "
                         "sem guardrail a metrica vira alvo.", sec.line)


def check_fragility_is_last(doc):
    secs = [s for s in doc.sections() if s.level == 2]
    for n, sec in enumerate(secs):
        if sec.key != "fragilidade":
            continue
        after = [s for s in secs[n + 1:] if s.key != "referencias"]
        if after:
            doc.add_hard(f"Ponto de Maior Fragilidade fora de posicao: "
                         f"'{after[0].title}' vem depois dele; e a ultima secao "
                         "de conteudo, so Referencias pode segui-la.",
                         after[0].line)


def bullet_content(text):
    """Texto do bullet sem o marcador de lista, com o negrito preservado."""
    return BULLET.sub("", text, count=1).strip()


def check_false_premise_bullet(doc):
    """A premissa que, se falsa, derruba o PRD abre Perguntas em Aberto e vem
    em negrito. Secao sem 'se falsa' e silenciosa: a checagem so cobra posicao
    e forma de quem ja declarou a premissa."""
    for sec in doc.sections():
        if sec.key != "perguntas":
            continue
        for n, (line, text, _) in enumerate(section_bullets(sec)):
            if not FALSE_PREMISE.search(norm(text)):
                continue
            body = bullet_content(text)
            if n:
                doc.add_hard(f"premissa 'se falsa' fora da primeira posicao: "
                             f"'{strip_md_prefix(text)[:50]}'. A premissa que "
                             "derruba a abordagem do PRD e o primeiro bullet de "
                             f"{sec.title}.", line)
            elif not BOLD_OPEN.match(body):
                doc.add_hard(f"premissa 'se falsa' sem negrito: "
                             f"'{strip_md_prefix(text)[:50]}'. A forma e "
                             "'- **[PREMISSA] ...; se falsa, ...** Dono: ... "
                             "Resolve-se ...'.", line)


def open_questions_body_ranges(doc):
    """Intervalos (primeira, ultima) de linha 1-based do corpo de cada secao
    Perguntas em Aberto, subsecoes incluidas."""
    return [(sec.line + 1, sec.line + len(sec.body))
            for sec in doc.sections() if sec.key == "perguntas"]


def check_false_premise_section(doc):
    """Bullet com 'se falsa' ('if false') fora de Perguntas em Aberto: a
    premissa que derruba o PRD e declarada uma vez, na secao que ela mesma faz
    entrar (`references/writing.md`, Secoes). Sem a checagem, a premissa fica
    em outra secao e a secao obrigatoria some sem achado."""
    ranges = open_questions_body_ranges(doc)
    for i, raw in enumerate(doc.lines):
        line = i + 1
        if not doc.visible(i) or not BULLET.match(raw):
            continue
        if any(first <= line <= last for first, last in ranges):
            continue
        if not FALSE_PREMISE.search(norm(raw)):
            continue
        doc.add_hard(f"premissa 'se falsa' fora de Perguntas em Aberto: "
                     f"'{strip_md_prefix(raw.strip())[:50]}'. A premissa que "
                     "derruba a abordagem do PRD e declarada uma vez, no "
                     "primeiro bullet de Perguntas em Aberto, e e ela que faz "
                     "a secao entrar; onde importa, cite-a.", line)


def lint_doc(doc, lang=None, sources=(), reverse=False):
    lines = doc.lines
    hard, warn = doc.add_hard, doc.add_warn

    if doc.h1_idx is None:
        hard("titulo H1 ('# ...') ausente.")
        return
    if doc.number == 0 and not doc.is_overview:
        hard("arquivo 0000-* sem '<!-- prd: overview -->' na primeira linha; "
             "a visao geral e o unico PRD que o linter trata diferente.", 1)
    if doc.is_overview and doc.number != 0:
        hard(f"visao geral numerada {doc.number:04d}; o numero da visao geral e "
             "fixo em 0000 e nao passa pelo contador de `seq.py` (SKILL.md, "
             "Caminho e numeracao). Renomeie para '0000-<slug>-overview.md'.", 1)

    start = doc.body_start()
    body_lines = [raw if doc.visible(start + k) else "" for k, raw in enumerate(lines[start:])]
    body_text = "\n".join(body_lines)

    # --- header, diagramas -----------------------------------------------
    check_header_field(doc)
    check_diagram_labels(doc)
    check_state_identifier_column(doc)
    if lang:
        check_heading_language(doc, lang)
    if sources:
        check_source_reformat(doc, sources)

    # --- secoes obrigatorias ---------------------------------------------
    check_unknown_sections(doc)
    if not doc.is_overview:
        for key in REQUIRED:
            if not doc.has_section(key):
                hard(f"secao obrigatoria ausente: {LABELS[key]}.")
        if doc.defs and not doc.has_section("frs"):
            hard(f"PRD define {len(doc.defs)} requisito(s) ('{doc.defs[0][0]}'...) sem "
                 "secao Requisitos Funcionais. O heading precisa ser exatamente "
                 "'Requisitos Funcionais' ou 'Functional Requirements'.", doc.defs[0][1])
        check_empty_sections(doc)
        check_section_order(doc)
        check_summary_length(doc)
        check_tradeoff_cost_and_reason(doc)
        check_metric_guardrail(doc)
        check_fragility_is_last(doc)
        check_false_premise_bullet(doc)
        check_false_premise_section(doc)
        check_scenario_cites_id(doc)
        check_regulatory_lines(doc)
        check_affects_dependencies(doc)

    # --- prefixo e definicoes --------------------------------------------
    if doc.is_overview:
        for rid, ln in doc.defs:
            hard(f"PRD 0000 define o requisito {rid}; a visao geral nao contem "
                 "regra de negocio - mova para o PRD dono.", ln)
    else:
        if doc.defs and not doc.prefix:
            hard("PRD com requisitos sem prefixo declarado. Acrescente a linha "
                 "'Prefixo dos requisitos: `X`.' ('Requirement prefix: `X`.' em "
                 "PRD em ingles) entre o titulo e a primeira secao.",
                 doc.h1_idx + 1)
        for rid, ln in doc.defs:
            p = rid.split("-", 1)[0]
            if doc.prefix and p != doc.prefix:
                hard(f"requisito {rid} definido com prefixo '{p}', mas o PRD "
                     f"declara '{doc.prefix}'.", ln)
        check_fr_moscow(doc)
    seen_bare = set()
    for rid, p, ln in doc.refs:
        if p in BARE_PREFIXES and (rid, ln) not in seen_bare:
            seen_bare.add((rid, ln))
            hard(f"ID sem prefixo de contexto: '{rid}'. Use <PREFIXO>-nn ou "
                 "<PREFIXO>-NFR-nn.", ln)

    # --- links locais ----------------------------------------------------
    for line, target, expected in local_link_findings(doc):
        hard(f"link '{target}' nao resolve (procurado em {expected}); "
             "o destino e relativo a pasta deste arquivo.", line)

    # --- WARN: tags, placeholders, hedging, meta-narracao, mecanismo -----
    for offset, raw in enumerate(body_lines):
        stripped = strip_md_prefix(raw)
        tm = re.match(r"\[([^\]]+)\]", stripped)
        if tm and is_tag_like(tm.group(1)) and tm.group(1) not in ALLOWED_TAGS:
            warn(f"tag nao reconhecida: '[{tm.group(1)}]'. As tags sao "
                 f"{', '.join(sorted(ALLOWED_TAGS))}; texto sem tag e fato.",
                 start + offset + 1)
        pm = PLACEHOLDER_WORDS.search(raw) or PLACEHOLDER_LOREM.search(raw) \
            or PLACEHOLDER_SLOTS.search(raw)
        if pm:
            warn(f"placeholder nao preenchido: '{pm.group(0)}'.", start + offset + 1)
        low = stripped.lower()
        for opener in META_OPENERS:
            if low.startswith(opener):
                warn(f"abertura de meta-narracao: '{raw.strip()[:50]}...'. "
                     "O titulo ja diz o que e o documento.", start + offset + 1)
                break
    for w in HEDGING:
        n = len(re.findall(r"\b" + re.escape(w) + r"\b", body_text, re.IGNORECASE))
        if n:
            warn(f"hedging lexical: '{w}' ({n}x).")
    in_target = False
    for offset, raw in enumerate(body_lines):
        if re.match(r"^##\s+", raw.strip()):
            in_target = reverse or heading_is("solucao", raw) or heading_is("frs", raw)
            continue
        if in_target:
            low = raw.lower()
            if any(x in low for x in EXCLUSION_MARKERS):
                continue
            for term in MECHANISM_TERMS:
                if term in low:
                    warn(f"possivel mecanismo nomeado em secao de problem space: "
                         f"'{term}'. Capability test - reescreva como comportamento, "
                         "ou ignore se for exclusao legitima.", start + offset + 1)
                    break


def cross_checks(docs, targets):
    """Checagens que dependem da pasta inteira. Findings vao para os targets."""
    by_path = {d.path: d for d in docs}
    is_target = {d.path: (d.path in targets) for d in docs}

    defs = {}
    for d in docs:
        for rid, ln in d.defs:
            defs.setdefault(rid, []).append((d.path, ln))
    prefixes = {}
    for d in docs:
        if d.prefix:
            prefixes.setdefault(d.prefix, d.path)
    overviews = [d for d in docs if d.is_overview]

    for rid, places in defs.items():
        if len(places) > 1:
            where = ", ".join(f"{by_path[p].label}:L{ln}" for p, ln in places)
            for p, ln in places:
                if is_target[p]:
                    by_path[p].add_hard(f"ID {rid} definido mais de uma vez ({where}); "
                                        "ID e unico na pasta e nunca reciclado.", ln)

    for d in docs:
        if not is_target[d.path]:
            continue
        reported = set()
        for rid, p, ln in d.refs:
            if p in BARE_PREFIXES or rid in defs or (rid, ln) in reported:
                continue
            reported.add((rid, ln))
            if p in prefixes:
                d.add_hard(f"citacao de {rid} nao resolve para nenhuma definicao na "
                           f"pasta (prefixo '{p}' e de {by_path[prefixes[p]].label}).", ln)
            else:
                d.add_warn(f"possivel ID '{rid}' com prefixo '{p}' que nenhum PRD da "
                           "pasta declara; se for ID, declare o prefixo; se nao for, "
                           "ignore.", ln)

    para_index = {}
    for d in docs:
        for body, ln in d.paragraphs:
            para_index.setdefault(body, []).append((d.path, ln))
    for body, places in para_index.items():
        if len({p for p, _ in places}) > 1:
            where = ", ".join(f"{by_path[p].label}:L{ln}" for p, ln in places)
            for p, ln in places:
                if is_target[p]:
                    by_path[p].add_warn(f"paragrafo identico em mais de um PRD ({where}). "
                                        "Fato compartilhado vive no PRD 0000; os demais "
                                        "citam.", ln)

    for d in docs:
        if is_target[d.path] and not d.is_overview and overviews:
            check_overview_reference(d, overviews[0])

    if len(prefixes) >= 2 and not overviews:
        for d in docs:
            if is_target[d.path]:
                d.add_hard(f"{len(prefixes)} prefixos na pasta ({', '.join(sorted(prefixes))}) "
                           "sem PRD 0000 de visao geral.")


def find_root(path):
    d = os.path.dirname(os.path.abspath(path))
    cur = d
    while True:
        if os.path.basename(cur).lower() in ("prd", "prds"):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return d
        cur = parent


def prd_files(root):
    """PRDs abaixo de root: todo `NNNN-*.md`, na raiz ou em subpastas."""
    out = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = sorted((d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS),
                             key=str.lower)
        out.extend(os.path.join(dirpath, f) for f in sorted(files, key=str.lower)
                   if NUMBERED_MD.match(f))
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


def parse_args(args):
    """(caminhos, idioma, materiais, reverse) da linha de comando, ou (None,
    mensagem, None, None) no erro de uso. `--lang` e `--source` aceitam as duas
    formas (`--lang pt` e `--lang=pt`); `--source` se repete, uma vez por
    material; `--reverse` nao leva valor."""
    paths, lang, sources, reverse, rest = [], None, [], False, list(args)
    while rest:
        a = rest.pop(0)
        if a == "--lang" or a.startswith("--lang="):
            value = a.split("=", 1)[1] if "=" in a else (rest.pop(0) if rest else "")
            if value not in LANGS:
                return None, (f"erro: --lang aceita {' ou '.join(sorted(LANGS))}"
                              + (f", nao '{value}'" if value else " e veio sem valor")), None, None
            lang = value
        elif a == "--source" or a.startswith("--source="):
            value = a.split("=", 1)[1] if "=" in a else (rest.pop(0) if rest else "")
            if not value:
                return None, "erro: --source veio sem o arquivo de material", None, None
            sources.append(value)
        elif a == "--reverse":
            reverse = True
        elif a.startswith("-") and a != "-":
            return None, f"erro: opcao desconhecida: {a}", None, None
        else:
            paths.append(a)
    return paths, lang, sources, reverse


def load_sources(paths):
    """[(rotulo, texto comparavel)] por material de `--source`, ou (None,
    mensagem) quando um deles nao se le."""
    out = []
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                out.append((os.path.basename(p), search_key(f.read())))
        except OSError as e:
            return None, f"erro ao abrir o material {p}: {e}"
    return out, None


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    args, lang, source_paths, reverse = parse_args(argv[1:])
    if args is None:
        print(lang, file=sys.stderr)
        return 2
    sources, err = load_sources(source_paths)
    if sources is None:
        print(err, file=sys.stderr)
        return 2
    targets, roots = [], []
    for a in args:
        a = os.path.abspath(a)
        if os.path.isdir(a):
            targets.extend(prd_files(a))
            roots.append(a)
        elif os.path.isfile(a):
            if not is_prd_path(a):
                print(f"erro: {a} nao e PRD (esperado NNNN-<slug>.md)", file=sys.stderr)
                return 2
            targets.append(a)
            roots.append(find_root(a))
        else:
            print(f"erro: {a} nao existe", file=sys.stderr)
            return 2
    if not targets:
        print("erro: nenhum PRD (NNNN-*.md) a verificar", file=sys.stderr)
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
        lint_doc(docs[p], lang, sources, reverse)
    cross_checks(list(docs.values()), target_set)

    multi = len(targets) > 1
    h = w = 0
    for p in targets:
        report(docs[p], multi)
        h += len(docs[p].hard)
        w += len(docs[p].warn)
    print("-" * 60)
    scope = f"{len(targets)} PRD(s)"
    if h == 0 and w == 0:
        print(f"OK  esqueleto conforme ({scope}); a semantica nao foi verificada.")
    else:
        print(f"{h} HARD, {w} WARN ({scope}). "
              + ("Corrija os HARD e rode de novo." if h else "Apenas WARN - julgue cada um."))
    return 1 if h else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
