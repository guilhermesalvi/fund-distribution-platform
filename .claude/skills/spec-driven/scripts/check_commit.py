#!/usr/bin/env python3
"""
check_commit.py - valida uma mensagem de commit contra Conventional Commits.

    Uso:  python3 <skill-dir>/scripts/check_commit.py --message "<msg>" [opcoes]
          python3 <skill-dir>/scripts/check_commit.py --file .git/COMMIT_EDITMSG [opcoes]

Opcoes (regra mais estrita do repositorio, por cima do default):
    --max-len N   limite da primeira linha inteira, incluindo `type: ` (default 72)
    --no-scope    rejeita `type(scope):`; so `type:` e aceito

Como hook git (sem dependencia de agente):
    printf '#!/bin/sh\\npython3 <skill-dir>/scripts/check_commit.py --file "$1"\\n' > .git/hooks/commit-msg
    chmod +x .git/hooks/commit-msg

Regras: primeira linha `type(scope)!: descricao` com type em
feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert, scope opcional
em kebab-case (proibido com --no-scope), primeira linha <= --max-len chars
sem ponto final, descricao no imperativo; linha em branco antes do corpo;
body/footers livres. Exit 0 ok, 1 violacao, 2 uso.

Estados distintos que este script NAO confunde: a mensagem *planejada* (campo
`Commit` do tasks.md), o commit *autorizado* (SKILL.md, Aprovacoes e autorizacoes; Contrato, item 3) e o
commit *executado* (hash no git). Aqui e no lint_tasks.py so a forma da
mensagem e validada; autorizacao e execucao sao decisao do usuario e fato do
repositorio, respectivamente.
"""

import re
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
DEFAULT_MAX_LEN = 72
# Forma: type, scope opcional, `!` opcional, `: `, descricao nao vazia.
# Comprimento e checado a parte (depende de --max-len).
CC_RE = re.compile(rf"^(?:{TYPES})(\([a-z0-9][a-z0-9\-/.]*\))?!?: \S.*$")
SCOPE_RE = re.compile(rf"^(?:{TYPES})(\([^)]*\))")
PAST_TENSE = ("added", "fixed", "updated", "changed", "removed")


def check(message, max_len=DEFAULT_MAX_LEN, no_scope=False):
    """Retorna lista de violacoes (vazia = ok) da forma da mensagem."""
    lines = message.rstrip("\n").splitlines()
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
    if head.rstrip().endswith("."):
        errs.append("descricao nao termina com ponto")
    if len(head) > max_len:
        errs.append(f"primeira linha com {len(head)} chars (max {max_len})")
    if len(lines) > 1 and lines[1].strip():
        errs.append("linha em branco obrigatoria entre titulo e corpo")
    m = re.match(r"^\w+(?:\([^)]*\))?!?: (\w+)", head)
    if m and m.group(1).lower() in PAST_TENSE:
        errs.append("descricao no imperativo ('add', nao 'added')")
    return errs


def parse_options(argv):
    """Le --max-len e --no-scope de argv. Retorna (max_len, no_scope)."""
    max_len = DEFAULT_MAX_LEN
    if "--max-len" in argv:
        raw = argv[argv.index("--max-len") + 1]
        if not raw.isdigit() or int(raw) <= 0:
            print(f"--max-len deve ser inteiro positivo, veio '{raw}'", file=sys.stderr)
            sys.exit(2)
        max_len = int(raw)
    return max_len, "--no-scope" in argv


def main(argv):
    msg = None
    if "--message" in argv:
        msg = argv[argv.index("--message") + 1]
    elif "--file" in argv:
        with open(argv[argv.index("--file") + 1], encoding="utf-8") as f:
            msg = f.read()
    else:
        print(__doc__, file=sys.stderr)
        return 2
    max_len, no_scope = parse_options(argv)
    errs = check(msg, max_len=max_len, no_scope=no_scope)
    for e in errs:
        print(f"HARD  {e}")
    print("check_commit: ok" if not errs else f"check_commit: {len(errs)} violacao(oes)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
