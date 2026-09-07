#!/usr/bin/env python3
"""
check_commit.py - valida uma mensagem de commit contra Conventional Commits.

    Uso:  python3 <skill-dir>/scripts/check_commit.py --message "<msg>" [opcoes]
          python3 <skill-dir>/scripts/check_commit.py --file .git/COMMIT_EDITMSG [opcoes]

Opcoes (regra mais estrita do repositorio, por cima do default):
    --max-len N     limite da primeira linha inteira, incluindo `type: ` (default 72)
    --no-scope      rejeita `type(scope):`; so `type:` e aceito
    --no-bang       rejeita o marcador `!` de breaking change (`type!:`)
    --single-line   rejeita corpo e rodape: a mensagem e a primeira linha e nada mais
    --lowercase     exige descricao iniciada em minuscula (`feat: add`, nao `feat: Add`)

O default e o Conventional Commits generico: escopo, `!`, corpo e rodape sao
aceitos. Repositorio com politica mais estrita liga as opcoes que a
politica exige; o perfil fica onde a politica esta escrita (CLAUDE.md,
CONTRIBUTING), nunca inferido pelo script.

Como hook git (sem dependencia de agente):
    printf '#!/bin/sh\\npython3 <skill-dir>/scripts/check_commit.py --file "$1" <opcoes>\\n' > .git/hooks/commit-msg
    chmod +x .git/hooks/commit-msg

Regras: primeira linha `type(scope)!: descricao` com type em
feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert (minusculas),
scope opcional em kebab-case (proibido com --no-scope), `!` opcional (proibido
com --no-bang), primeira linha <= --max-len chars, sem ponto final, descricao
no imperativo; linha em branco antes do corpo; body/footers livres (proibidos
com --single-line). A checagem de imperativo e heuristica: rejeita a primeira
palavra da descricao quando esta numa lista fixa de formas no passado, gerundio
ou terceira pessoa (`added`, `adding`, `adds`); nao e analise linguistica.

Com --file, linhas de comentario (`#` na primeira coluna) e tudo a partir da
linha de tesoura (`# ---- >8 ----`, `git commit -v`) sao descartados antes da
validacao, como o proprio git faz depois do hook `commit-msg`.

Exit 0 ok, 1 violacao, 2 uso (argumento ausente ou invalido, arquivo ilegivel).

Estados distintos que este script NAO confunde: a mensagem *planejada* (campo
`Commit` do tasks.md), o commit *autorizado* (SKILL.md, Aprovacoes e autorizacoes; Contrato, item 3) e o
commit *executado* (hash no git). Aqui e no lint_tasks.py so a forma da
mensagem e validada; autorizacao e execucao sao decisao do usuario e fato do
repositorio, respectivamente.
"""

import argparse
import re
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
DEFAULT_MAX_LEN = 72
# Forma: type, scope opcional, `!` opcional, `: `, descricao nao vazia.
# Comprimento e checado a parte (depende de --max-len).
CC_RE = re.compile(rf"^(?:{TYPES})(\([a-z0-9][a-z0-9\-/.]*\))?!?: \S.*$")
SCOPE_RE = re.compile(rf"^(?:{TYPES})(\([^)]*\))")
BANG_RE = re.compile(rf"^(?:{TYPES})(?:\([^)]*\))?!:")
# `type(scope)!: ` ja consumido; captura a descricao inteira.
DESC_RE = re.compile(r"^\w+(?:\([^)]*\))?!?: (.*)$")
SCISSORS_RE = re.compile(r"^# -+ >8 -+$")
# Heuristica de imperativo: formas que NAO sao imperativo, para verbos comuns
# em mensagens de commit. Lista fixa; ausencia aqui nao prova imperativo.
_STEMS = {
    "add": ("added", "adds", "adding"), "align": ("aligned", "aligns", "aligning"),
    "bump": ("bumped", "bumps", "bumping"), "change": ("changed", "changes", "changing"),
    "clean": ("cleaned", "cleans", "cleaning"), "condense": ("condensed", "condenses", "condensing"),
    "correct": ("corrected", "corrects", "correcting"), "create": ("created", "creates", "creating"),
    "delete": ("deleted", "deletes", "deleting"), "document": ("documented", "documents", "documenting"),
    "drop": ("dropped", "drops", "dropping"), "extract": ("extracted", "extracts", "extracting"),
    "fix": ("fixed", "fixes", "fixing"), "handle": ("handled", "handles", "handling"),
    "implement": ("implemented", "implements", "implementing"),
    "improve": ("improved", "improves", "improving"),
    "introduce": ("introduced", "introduces", "introducing"),
    "make": ("made", "makes", "making"), "merge": ("merged", "merges", "merging"),
    "migrate": ("migrated", "migrates", "migrating"), "move": ("moved", "moves", "moving"),
    "refactor": ("refactored", "refactors", "refactoring"),
    "register": ("registered", "registers", "registering"),
    "remove": ("removed", "removes", "removing"), "rename": ("renamed", "renames", "renaming"),
    "replace": ("replaced", "replaces", "replacing"), "resolve": ("resolved", "resolves", "resolving"),
    "revert": ("reverted", "reverts", "reverting"), "rewrite": ("rewrote", "rewrites", "rewriting"),
    "update": ("updated", "updates", "updating"), "use": ("used", "uses", "using"),
}
NON_IMPERATIVE = {form: stem for stem, forms in _STEMS.items() for form in forms}


def strip_git_comments(message):
    """Remove linhas de comentario e tudo a partir da tesoura, como o git faz
    com cleanup=strip. Usado para --file (COMMIT_EDITMSG no hook)."""
    kept = []
    for line in message.splitlines():
        if SCISSORS_RE.match(line):
            break
        if line.startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept)


def check(message, max_len=DEFAULT_MAX_LEN, no_scope=False, no_bang=False,
          single_line=False, lowercase=False):
    """Retorna lista de violacoes (vazia = ok) da forma da mensagem."""
    lines = message.rstrip().splitlines()
    if not lines or not lines[0].strip():
        return ["mensagem vazia"]
    errs = []
    head = lines[0]
    if not CC_RE.match(head):
        errs.append(f"primeira linha fora de Conventional Commits: '{head}' "
                    f"(esperado: type(scope): descricao; type em {TYPES})")
    sm = SCOPE_RE.match(head)
    if no_scope and sm:
        errs.append(f"escopo nao permitido (--no-scope): '{sm.group(1)}' - use 'type: descricao'")
    if no_bang and BANG_RE.match(head):
        errs.append("marcador '!' de breaking change nao permitido (--no-bang); "
                    "comunique a quebra na descricao do pull request")
    if head.rstrip().endswith("."):
        errs.append("descricao nao termina com ponto")
    if len(head) > max_len:
        errs.append(f"primeira linha com {len(head)} chars (max {max_len})")
    if len(lines) > 1 and lines[1].strip():
        errs.append("linha em branco obrigatoria entre titulo e corpo")
    if single_line and any(l.strip() for l in lines[1:]):
        errs.append("corpo ou rodape nao permitido (--single-line): a mensagem e so a primeira linha")
    dm = DESC_RE.match(head)
    desc = dm.group(1) if dm else ""
    if lowercase and desc[:1].isalpha() and not desc[:1].islower():
        errs.append(f"descricao comeca com maiuscula (--lowercase): '{desc[:1]}' - "
                    f"use '{desc[:1].lower()}{desc[1:]}'")
    first = re.match(r"\w+", desc)
    if first and first.group(0).lower() in NON_IMPERATIVE:
        stem = NON_IMPERATIVE[first.group(0).lower()]
        errs.append(f"descricao no imperativo ('{stem}', nao '{first.group(0)}')")
    return errs


def build_parser():
    p = argparse.ArgumentParser(
        prog="check_commit.py", add_help=True,
        description="Valida a forma de uma mensagem de commit (Conventional Commits).")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--message", metavar="MSG", help="mensagem a validar")
    src.add_argument("--file", metavar="PATH", help="arquivo com a mensagem (ex.: .git/COMMIT_EDITMSG)")
    p.add_argument("--max-len", type=int, default=DEFAULT_MAX_LEN, metavar="N",
                   help=f"limite da primeira linha, incluindo 'type: ' (default {DEFAULT_MAX_LEN})")
    p.add_argument("--no-scope", action="store_true", help="rejeita type(scope):")
    p.add_argument("--no-bang", action="store_true", help="rejeita o marcador '!' de breaking change")
    p.add_argument("--single-line", action="store_true", help="rejeita corpo e rodape")
    p.add_argument("--lowercase", action="store_true", help="exige descricao iniciada em minuscula")
    return p


def main(argv):
    parser = build_parser()
    if len(argv) < 2:
        parser.print_usage(sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2
    try:
        args = parser.parse_args(argv[1:])
    except SystemExit as e:  # argparse ja imprimiu o diagnostico
        return 2 if e.code else 0
    if args.max_len <= 0:
        print(f"check_commit: --max-len deve ser inteiro positivo, veio {args.max_len}", file=sys.stderr)
        return 2
    if args.message is not None:
        msg = args.message
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                msg = strip_git_comments(f.read())
        except OSError as e:
            print(f"check_commit: nao foi possivel ler '{args.file}': {e.strerror or e}", file=sys.stderr)
            return 2
        except UnicodeDecodeError as e:
            print(f"check_commit: '{args.file}' nao esta em UTF-8: {e}", file=sys.stderr)
            return 2
    errs = check(msg, max_len=args.max_len, no_scope=args.no_scope, no_bang=args.no_bang,
                 single_line=args.single_line, lowercase=args.lowercase)
    for e in errs:
        print(f"HARD  {e}")
    print("check_commit: ok" if not errs else f"check_commit: {len(errs)} violacao(oes)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
