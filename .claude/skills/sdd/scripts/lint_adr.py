#!/usr/bin/env python3
"""
lint_adr.py - verificacao deterministica do esqueleto de uma ADR.

    Uso:  python3 <skill-dir>/scripts/lint_adr.py <adr.md | dir>

Com uma pasta, verifica todo `NNNN-<slug>.md` filho direto dela (`docs/adr`).
A ADR guarda o porquê de uma decisao de projeto; o linter confere a forma,
nunca o conteudo. Tudo que esta dentro de bloco de codigo (``` ou ~~~) e
ignorado.

HARD (exit 1):
- titulo fora da forma `# ADR NNNN: titulo` (quatro digitos, titulo nao vazio);
- linha `Participantes:` ausente ou sem nome, entre o titulo e a primeira `##`:
  decisao de arquitetura raramente e de uma pessoa, e o nome responde depois
  do turnover;
- secao obrigatoria ausente: `## Contexto`, `## Decisão`, `## Alternativas
  consideradas` e `## Consequências` (heading casa por igualdade com os
  aliases PT/EN, nunca por prefixo);
- secao obrigatoria fora da ordem dessa lista;
- secao `##` fora da lista de secoes da ADR: as quatro obrigatorias mais
  `## Regras derivadas`, com os aliases em ingles (references/adr.md,
  Template);
- secao presente sem conteudo: corpo vazio ou reduzido a uma linha entre
  'Nenhuma.', 'Nenhum.', 'N/A' e 'Nao se aplica.';
- `## Regras derivadas`, quando presente, nao e a ultima secao;
- `## Regras derivadas` sem bullet algum, ou com bullet sem o path do arquivo
  onde a regra vive entre crases (`CLAUDE.md`, `.claude/rules/x.md`,
  `docs/adr`): regra sem path e seguida cegamente ou ignorada
  (references/adr.md, Conformar e superseder). O path pode estar em qualquer
  linha do bullet;
- Alternativas consideradas com tabela sem linha de dados, ou com linha cuja
  alternativa ou razao esta vazia: a secao promete o que nao entrega;
- Consequências sem uma linha `- Negativas: <texto>`: ADR sem consequencia
  negativa e decisao nao examinada; rotulo seguido so de reticencias ou de
  pontuacao conta como ausente;
- tag fora de [PREMISSA] e [LACUNA] ([FATO], [PREMISSA-CRÍTICA] e grafias
  erradas);
- `Substitui: NNNN` abaixo do titulo cujo `NNNN-*.md` nao existe na mesma
  pasta, ou existe e nao tem `Substituída por: <este NNNN>`; o mesmo, ao
  contrario, para `Substituída por: NNNN`.

WARN (nao afeta exit):
- placeholder (TBD, TODO, `[nome]`, `[Uma frase: ...]`, valor reduzido a
  reticencias), hedging, meta-narracao fora de bloco de codigo.

Exit 2 em erro de uso: opcao desconhecida, arquivo ausente ou fora de UTF-8.
Linter verde e esqueleto conforme, nao decisao bem tomada.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    Report, check_tags, check_unknown_sections, fenced_line_mask, find_section_exact,
    iter_headings, norm_heading, read_lines, scan_placeholders, scan_prose, strip_accents,
    table_rows, usage,
)

# Ordem das secoes obrigatorias, como no template de references/adr.md.
SECTIONS_ORDER = [
    ("Contexto", "Context"),
    ("Decisão", "Decision"),
    ("Alternativas consideradas", "Alternatives considered"),
    ("Consequências", "Consequences"),
]
SECTION_RULES = ("Regras derivadas", "Derived rules")
# Lista fechada das secoes `##` da ADR: as obrigatorias mais Regras derivadas
# (references/adr.md, Template); secao fora dela e HARD.
SECTIONS_KNOWN = SECTIONS_ORDER + [SECTION_RULES]
# Corpo de secao reduzido a uma dessas linhas conta como secao sem conteudo.
NO_CONTENT_LINES = frozenset(("nenhuma", "nenhum", "n/a", "nao se aplica", "not applicable"))

ADR_FILE = re.compile(r"^(\d{4})-[^/\\]+\.md$", re.IGNORECASE)
H1 = re.compile(r"^#\s+ADR\s+(\d{4})\s*:\s*(\S.*?)\s*$")
PARTICIPANTS = re.compile(r"^\s*\**\s*(?:Participantes|Participants)\s*\**\s*:\s*(.*)$", re.IGNORECASE)
SUPERSEDES = re.compile(r"^\s*\**\s*(?:Substitui|Supersedes)\s*\**\s*:\s*(.*)$", re.IGNORECASE)
SUPERSEDED_BY = re.compile(r"^\s*\**\s*(?:Substitu[ií]da por|Superseded by)\s*\**\s*:\s*(.*)$",
                           re.IGNORECASE)
NEGATIVE = re.compile(r"^\s*[-*]\s*\**\s*(?:Negativas?|Negatives?)\s*\**\s*:\s*(\S.*)$", re.IGNORECASE)
NUMBER = re.compile(r"\b(\d{4})\b")
BULLET = re.compile(r"^\s*[-*]\s+(\S.*)$")
# Conteudo de code span que e path: tem separador de diretorio, ou nome com
# extensao (`CLAUDE.md`), ou dotfile (`.editorconfig`).
PATH_SPAN = re.compile(r"^(?:[^\s`]*[/\\][^\s`]*|[\w.\-]+\.[A-Za-z0-9]{1,10}|\.[\w\-]+)$")
# Valor so com pontuacao ou reticencias: o rotulo esta escrito, o conteudo nao.
NO_TEXT = re.compile(r"^[\s.…\-–—*_]*$")


def has_text(value):
    """Valor com conteudo, e nao so pontuacao ou reticencias."""
    return not NO_TEXT.match(value)


def section_index(title):
    """Posicao do heading na lista de secoes obrigatorias, ou None."""
    key = norm_heading(title)
    for n, aliases in enumerate(SECTIONS_ORDER):
        if key in {norm_heading(a) for a in aliases}:
            return n
    return None


def is_no_content(body):
    """Corpo vazio, ou reduzido a uma linha de negacao ('Nenhuma.', 'N/A')."""
    kept = [l.strip() for l in body if l.strip()]
    if not kept:
        return True
    if len(kept) > 1:
        return False
    return strip_accents(kept[0].lower()).strip(" .") in NO_CONTENT_LINES


def find_h1(rep, lines, mask):
    """(idx, numero) do titulo `# ADR NNNN: titulo`. (None, None) quando
    ausente ou fora da forma."""
    idx = next((i for i, l in enumerate(lines) if l.startswith("# ") and not mask[i]), None)
    if idx is None:
        rep.hard("sem titulo H1; a forma e `# ADR NNNN: titulo`")
        return None, None
    m = H1.match(lines[idx])
    if not m:
        rep.hard("titulo fora da forma `# ADR NNNN: titulo` "
                 f"(veio '{lines[idx].strip()[:60]}')", idx + 1)
        return idx, None
    return idx, m.group(1)


def header_range(lines, mask, h1_idx):
    """Faixa entre o titulo e a primeira `##`: onde vivem `Participantes:`,
    `Substitui:` e `Substituída por:`."""
    start = 0 if h1_idx is None else h1_idx + 1
    end = next((i for i, _ in iter_headings(lines, 2, mask) if i >= start), len(lines))
    return start, end


def check_participants(rep, lines, mask, head):
    """`Participantes:` com pelo menos um nome, antes da primeira `##`."""
    for i in range(*head):
        if mask[i]:
            continue
        m = PARTICIPANTS.match(lines[i])
        if m:
            if not m.group(1).strip(" .;:"):
                rep.hard("linha `Participantes:` sem nome; quem decidiu e quem foi "
                         "consultado e conteudo da decisao", i + 1)
            return
    rep.hard("linha `Participantes:` ausente entre o titulo e a primeira `##`", head[0])


def check_sections(rep, lines, mask):
    """Secoes obrigatorias presentes, na ordem, com conteudo; `Regras
    derivadas`, quando presente, por ultimo."""
    hs = iter_headings(lines, 2, mask)
    seen, latest = {}, None
    rules_idx = None
    for n, (i, text) in enumerate(hs):
        end = hs[n + 1][0] if n + 1 < len(hs) else len(lines)
        if is_no_content(lines[i + 1:end]):
            rep.hard(f"secao sem conteudo: {text}; secao existe quando ha o que dizer - "
                     "preencha ou remova", i + 1)
        if norm_heading(text) in {norm_heading(a) for a in SECTION_RULES}:
            rules_idx = n
        idx = section_index(text)
        if idx is None:
            continue
        seen.setdefault(idx, i)
        if latest and idx < latest[0]:
            rep.hard(f"secao fora de ordem: '{latest[1]}' aparece antes de '{text}', que "
                     "deveria precede-la; a ordem e a do template de references/adr.md", i + 1)
        else:
            latest = (idx, text)
    for n, aliases in enumerate(SECTIONS_ORDER):
        if n not in seen:
            rep.hard(f"secao obrigatoria ausente: ## {aliases[0]}")
    if rules_idx is not None and rules_idx != len(hs) - 1:
        rep.hard(f"## {SECTION_RULES[0]} nao e a ultima secao; a regra derivada fecha a ADR",
                 hs[rules_idx][0] + 1)


def check_negative_consequence(rep, lines, mask):
    """Consequências com uma linha `- Negativas: <texto>` alem do rotulo;
    reticencias no lugar do texto nao sao o custo aceito."""
    sec = find_section_exact(lines, SECTIONS_ORDER[3], mask=mask)
    if sec is None:
        return
    for i in range(*sec):
        if mask[i]:
            continue
        m = NEGATIVE.match(lines[i])
        if m and has_text(m.group(1)):
            return
    rep.hard(f"## {SECTIONS_ORDER[3][0]} sem linha `- Negativas: <texto>`; ADR sem "
             "consequencia negativa e decisao nao examinada (reticencias nao sao "
             "o custo aceito)", sec[0])


def bullet_items(lines, start, end, mask):
    """Bullets da faixa, como (idx da primeira linha, texto do item inteiro).
    Linha seguinte que nao abre bullet nem esta vazia continua o item."""
    items = []
    for i in range(start, end):
        if mask[i]:
            continue
        m = BULLET.match(lines[i])
        if m:
            items.append([i, m.group(1)])
        elif items and lines[i].strip():
            items[-1][1] += " " + lines[i].strip()
        elif not lines[i].strip():
            continue
    return [(i, text) for i, text in items]


def has_path_span(text):
    """Trecho entre crases que e um path: `CLAUDE.md`, `docs/adr`,
    `.claude/rules/tracing.md`."""
    return any(PATH_SPAN.match(m.group(1).strip()) for m in re.finditer(r"`([^`]+)`", text))


def check_derived_rules(rep, lines, mask):
    """Cada regra derivada e um bullet com o path do arquivo onde ela vive:
    regra sem path e seguida cegamente ou ignorada (references/adr.md,
    Conformar e superseder)."""
    sec = find_section_exact(lines, SECTION_RULES, mask=mask)
    if sec is None:
        return
    items = bullet_items(lines, sec[0], sec[1], mask)
    if not items:
        rep.hard(f"## {SECTION_RULES[0]} sem bullet; cada regra derivada e um bullet com o "
                 "path do arquivo onde ela vive, entre crases", sec[0])
        return
    for i, text in items:
        if not has_path_span(text):
            rep.hard(f"## {SECTION_RULES[0]}: regra sem o path do arquivo onde ela vive, "
                     f"entre crases (veio '{text[:60]}')", i + 1)


def check_alternatives(rep, lines, mask):
    """Alternativas consideradas com ao menos uma alternativa preenchida: sem
    elas a IA re-propoe caminhos ja descartados e o time re-litiga o que ja foi
    pago (references/adr.md, O que a ADR guarda)."""
    sec = find_section_exact(lines, SECTIONS_ORDER[2], mask=mask)
    if sec is None:
        return
    if not any(lines[i].strip().startswith("|") for i in range(*sec) if not mask[i]):
        return
    rows = [(i, cells) for i, cells in table_rows(lines, *sec) if not mask[i]]
    if not rows:
        rep.hard(f"## {SECTIONS_ORDER[2][0]} com tabela sem linha de dados; alternativa "
                 "descartada e o que impede re-litigar a decisao", sec[0])
        return
    for i, cells in rows:
        if len(cells) < 2 or not has_text(cells[0]) or not has_text(cells[1]):
            rep.hard(f"## {SECTIONS_ORDER[2][0]}: linha sem a alternativa ou sem a razao "
                     "da rejeicao", i + 1)


# --- superseder -------------------------------------------------------------

def sibling_adr(path, number):
    """Path do `NNNN-*.md` irmao, ou None."""
    folder = os.path.dirname(os.path.abspath(path))
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return None
    for name in names:
        m = ADR_FILE.match(name)
        if m and m.group(1) == number and os.path.join(folder, name) != os.path.abspath(path):
            return os.path.join(folder, name)
    return None


def cites(path, pattern, number):
    """A ADR em `path` tem uma linha `pattern:` citando `number`."""
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    for i, l in enumerate(lines):
        if mask[i]:
            continue
        m = pattern.match(l)
        if m and number in NUMBER.findall(m.group(1)):
            return True
    return False


def check_supersede(rep, lines, mask, head, path, number):
    """`Substitui:` e `Substituída por:` sao reciprocos: cada lado aponta para
    uma ADR que existe na pasta e que aponta de volta."""
    pairs = ((SUPERSEDES, SUPERSEDED_BY, "Substitui", "Substituída por"),
             (SUPERSEDED_BY, SUPERSEDES, "Substituída por", "Substitui"))
    for i in range(*head):
        if mask[i]:
            continue
        for pattern, back, label, back_label in pairs:
            m = pattern.match(lines[i])
            if not m:
                continue
            for other in NUMBER.findall(m.group(1)):
                target = sibling_adr(path, other)
                if target is None:
                    rep.hard(f"`{label}: {other}` sem ADR {other}-*.md na mesma pasta", i + 1)
                elif number and not cites(target, back, number):
                    rep.hard(f"`{label}: {other}` sem reciproco: {os.path.basename(target)} "
                             f"nao tem `{back_label}: {number}` abaixo do titulo", i + 1)
            break


# --- main -------------------------------------------------------------------

def lint_file(path):
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    rep = Report("lint_adr")

    h1_idx, number = find_h1(rep, lines, mask)
    head = header_range(lines, mask, h1_idx)
    check_participants(rep, lines, mask, head)
    check_unknown_sections(rep, lines, SECTIONS_KNOWN, "references/adr.md, Template", mask)
    check_sections(rep, lines, mask)
    check_alternatives(rep, lines, mask)
    check_negative_consequence(rep, lines, mask)
    check_derived_rules(rep, lines, mask)
    check_supersede(rep, lines, mask, head, path, number)
    check_tags(rep, lines, mask=mask)
    scan_placeholders(rep, lines, mask=mask)
    scan_prose(rep, lines, mask=mask)
    return rep.emit(path)


def adr_files(folder):
    """`NNNN-<slug>.md` filhos diretos da pasta, em ordem."""
    return [os.path.join(folder, n) for n in sorted(os.listdir(folder)) if ADR_FILE.match(n)]


def parse_args(argv):
    args = list(argv[1:])
    if not args:
        usage(__doc__)
    if args[0].startswith("--"):
        usage(f"primeiro argumento deve ser o path da ADR ou da pasta, veio '{args[0]}'\n\n{__doc__}")
    if len(args) > 1:
        usage(f"opcao desconhecida: {args[1]}\n\n{__doc__}")
    return args[0]


def main(argv):
    target = parse_args(argv)
    if os.path.isdir(target):
        paths = adr_files(target)
        if not paths:
            print(f"nenhuma ADR (NNNN-<slug>.md) em {target}")
            return 0
    else:
        paths = [target]
    status = 0
    for n, path in enumerate(paths):
        if n:
            print()
        status |= lint_file(path)
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
