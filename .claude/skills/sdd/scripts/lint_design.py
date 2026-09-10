#!/usr/bin/env python3
"""
lint_design.py - verificacao deterministica do esqueleto de um design.md.

    Uso:  python3 <skill-dir>/scripts/lint_design.py <design.md> --spec <spec.md>

`--spec` e obrigatorio: e a spec viva da capability, fonte dos requisitos de
comportamento indesejado (`IF ... THEN`) que o design tem de tratar. Sem ela a
cobertura nao e verificada e o linter reporta HARD.

Escopo da mudanca: por default, todos os requisitos `IF ... THEN` da spec.
Mudanca que toca so parte deles declara `scope: RSV-07, RSV-10` no comentario
de maquina (`<!-- sdd: design | spec: ../spec.md | scope: RSV-07, RSV-10 -->`);
so os requisitos listados entram na cobertura.

O design nao decide comportamento; o linter confere a forma, nunca o conteudo.
Tudo que esta dentro de bloco de codigo (``` ou ~~~) e ignorado.

HARD (exit 1):
- comentario de maquina ausente ou sem `sdd: design`: a primeira linha nao
  vazia e `<!-- sdd: design | spec: ../spec.md -->`;
- `spec:` ausente no comentario de maquina, ou destino que nao resolve para
  arquivo (relativo a pasta do design, ou `/docs/...` a partir da raiz do
  repositorio);
- secao `##` fora da lista de secoes conhecidas (references/design.md, Secoes);
- secoes conhecidas fora da ordem dessa lista;
- secao presente sem conteudo: corpo vazio ou reduzido a uma linha entre
  'Nenhuma.', 'Nenhum.', 'N/A' e 'Nao se aplica.';
- requisito `IF ... THEN` da spec (no escopo) cujo ID nao e citado na secao
  `## Tratamento de erros`: cenario de erro sem mecanismo escolhido;
- ID em `scope:` que nao existe na spec.

WARN (nao afeta exit):
- placeholder (TBD, TODO, `[nome]`) fora de bloco de codigo.

Exit 2 em erro de uso: opcao desconhecida, arquivo ausente ou fora de UTF-8.
Linter verde e esqueleto conforme, nao design bom.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    REQ_ID, REQ_LINE, Report, fenced_line_mask, find_section_exact, iter_headings,
    norm_heading, parse_machine_comment, read_lines, resolve_local_path, scan_placeholders,
    strip_accents, usage,
)

# Ordem das secoes do design, como em references/design.md, secao "Secoes".
SECTIONS_ORDER = [
    ("Contexto de design", "Design Context"),
    ("Critérios de avaliação", "Evaluation Criteria"),
    ("Riscos e técnicas", "Risks and Techniques"),
    ("Abordagens", "Approaches"),
    ("Visão da arquitetura", "Architecture Overview"),
    ("Unidade de deploy", "Deployment Unit"),
    ("Componentes", "Components"),
    ("Domain Events",),
    ("Modelo de dados", "Data Model"),
    ("Tratamento de erros", "Error handling"),
    ("Decisões técnicas", "Technical Decisions"),
    ("Arquivos a criar ou modificar", "Files to Create or Modify"),
]
SECTION_ERRORS = ("Tratamento de erros", "Error handling")
# Corpo de secao reduzido a uma dessas linhas conta como secao sem conteudo.
NO_CONTENT_LINES = frozenset(("nenhuma", "nenhum", "n/a", "nao se aplica", "not applicable"))
# EARS de comportamento indesejado: `IF <gatilho> THEN the system SHALL <resposta>`.
UNWANTED = re.compile(r"^\s*IF\b.*\bTHEN\b")


def section_index(title):
    """Posicao do heading na lista de secoes conhecidas, ou None."""
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


def check_sections(rep, lines, mask):
    """Secao conhecida, na ordem da lista, e com conteudo."""
    hs = iter_headings(lines, 2, mask)
    latest = None
    for n, (i, text) in enumerate(hs):
        end = hs[n + 1][0] if n + 1 < len(hs) else len(lines)
        if is_no_content(lines[i + 1:end]):
            rep.hard(f"secao sem conteudo: {text}; secao existe quando ha o que dizer - "
                     "preencha ou remova", i + 1)
        idx = section_index(text)
        if idx is None:
            rep.hard(f"secao desconhecida: ## {text}; a lista de secoes e a de "
                     "references/design.md, Secoes", i + 1)
            continue
        if latest and idx < latest[0]:
            rep.hard(f"secao fora de ordem: '{latest[1]}' aparece antes de '{text}', que "
                     "deveria precede-la; a ordem e a da lista de references/design.md, Secoes", i + 1)
        else:
            latest = (idx, text)


def spec_requirements(path):
    """(known, unwanted): IDs dos requisitos da secao Requisitos da spec viva e,
    entre eles, os de comportamento indesejado (`IF ... THEN`)."""
    lines = read_lines(path)
    mask = fenced_line_mask(lines)
    sec = find_section_exact(lines, ("Requisitos", "Requirements"), mask=mask)
    known, unwanted = set(), []
    if sec is None:
        return known, unwanted
    for i in range(*sec):
        if mask[i]:
            continue
        m = REQ_LINE.match(lines[i])
        if not m:
            continue
        known.add(m.group(1))
        if UNWANTED.match(m.group(2)) and m.group(1) not in unwanted:
            unwanted.append(m.group(1))
    return known, unwanted


def scoped_unwanted(rep, fields, known, unwanted):
    """`scope:` no comentario de maquina restringe a cobertura aos requisitos
    listados; ID que nao existe na spec e escopo escrito no vazio."""
    declared = fields.get("scope")
    if not declared:
        return unwanted
    ids = set(REQ_ID.findall(declared))
    for rid in sorted(ids - known):
        rep.hard(f"scope: {rid} nao existe na spec", 1)
    return [rid for rid in unwanted if rid in ids]


def check_error_handling(rep, lines, mask, unwanted):
    """Todo `IF ... THEN` da spec aparece em Tratamento de erros, com o
    mecanismo escolhido para trata-lo."""
    if not unwanted:
        return
    sec = find_section_exact(lines, SECTION_ERRORS, mask=mask)
    if sec is None:
        rep.hard(f"secao ausente: ## {SECTION_ERRORS[0]}; a spec tem requisito(s) "
                 f"IF ... THEN sem cenario aqui: {', '.join(unwanted)}")
        return
    cited = set()
    for i in range(*sec):
        if mask[i]:
            continue
        cited.update(REQ_ID.findall(lines[i]))
    for rid in unwanted:
        if rid not in cited:
            rep.hard(f"{rid}: requisito IF ... THEN da spec sem cenario em "
                     f"## {SECTION_ERRORS[0]}", sec[0])


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
    rep = Report("lint_design")

    fields, mc_idx = parse_machine_comment(lines)
    if fields is None or fields["sdd"].lower() != "design":
        rep.hard("primeira linha deve ser <!-- sdd: design | spec: <path> [| scope: IDs] -->", 1)
        return rep.emit(path)
    declared = fields.get("spec")
    if not declared:
        rep.hard("comentario de maquina sem 'spec:'", 1)
    elif not resolve_local_path(path, declared):
        rep.hard(f"spec do comentario de maquina nao encontrada: '{declared}' "
                 "(relativo a pasta do design ou `/docs/...` da raiz)", 1)

    check_sections(rep, lines, mask)

    if spec is None:
        rep.hard("--spec obrigatorio: cobertura IF ... THEN -> Tratamento de erros nao verificada")
    elif not spec or not os.path.exists(spec):
        rep.hard(f"spec nao encontrada: '{spec}'")
    else:
        known, unwanted = spec_requirements(spec)
        check_error_handling(rep, lines, mask, scoped_unwanted(rep, fields, known, unwanted))

    scan_placeholders(rep, lines, skip_first=(mc_idx or 0) + 1, mask=mask)
    return rep.emit(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
