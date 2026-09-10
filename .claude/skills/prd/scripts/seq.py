#!/usr/bin/env python3
"""
seq.py - contador sequencial dos PRDs: proximo numero e numero duplicado.

    Uso:
      python scripts/seq.py check <root>
      python scripts/seq.py next  <root> [--slug <slug>]

`<root>` e o diretorio real dos PRDs; na documentacao da skill, `/docs/prd`
e caminho relativo a raiz do repositorio. PRD e todo `NNNN-<slug>.md` abaixo
da raiz, em qualquer subpasta (`assets/`, `archive/`, `node_modules/` e
diretorios ocultos ficam fora): 4 digitos, zero a esquerda, slug kebab-case
ascii minusculo. O numero e global na raiz e o estado e o proprio
filesystem, nunca um contador armazenado.

`check` (exit 1 em HARD): numero usado por mais de um PRD. O script reporta,
nunca renumera.

`next` roda o `check`, recusa alocar sobre HARD e imprime max+1 sem tocar no
disco: `NNNN` sem `--slug`, `NNNN-<slug>` com `--slug`. O slug precisa ser
kebab-case ascii minusculo (exit 1 se nao for). Raiz sem PRD comeca em 0001.

Exit 2 em erro de uso: raiz inexistente, subcomando ou opcao desconhecida.
"""

import argparse
import os
import re
import sys

NUMBERED = re.compile(r"^(\d{4})-([^/\\]+)\.md$", re.IGNORECASE)
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WIDTH = 4
SKIP_DIRS = {"assets", "archive", "node_modules"}


def prd_files(root):
    """(numero, slug, path) de todo `NNNN-<slug>.md` abaixo de root."""
    out = []
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS)
        for f in sorted(files):
            m = NUMBERED.match(f)
            if m:
                out.append((int(m.group(1)), m.group(2), os.path.join(dirpath, f)))
    return out


def duplicates(entries):
    by_num = {}
    for n, _, p in entries:
        by_num.setdefault(n, []).append(p)
    return {n: ps for n, ps in sorted(by_num.items()) if len(ps) > 1}


def report(dups):
    for n, paths in dups.items():
        print(f"HARD  numero {n:0{WIDTH}d} usado por mais de um PRD: {', '.join(paths)}")


def cmd_check(args):
    entries = prd_files(args.root)
    dups = duplicates(entries)
    report(dups)
    tail = " Renumere o PRD que chegou depois; o script nao renumera." if dups else ""
    print(f"seq: {len(dups)} HARD em {args.root} ({len(entries)} PRD(s)).{tail}")
    return 1 if dups else 0


def cmd_next(args):
    if args.slug is not None and not SLUG.match(args.slug):
        print(f"seq: slug fora do kebab-case ascii minusculo: '{args.slug}'", file=sys.stderr)
        return 1
    entries = prd_files(args.root)
    dups = duplicates(entries)
    if dups:
        report(dups)
        print("seq: sequencia invalida; nao aloco numero sobre HARD pendente.", file=sys.stderr)
        return 1
    nxt = max((n for n, _, _ in entries), default=0) + 1
    if nxt > 10 ** WIDTH - 1:
        print(f"seq: contador estourou {WIDTH} digitos", file=sys.stderr)
        return 1
    print(f"{nxt:0{WIDTH}d}" + (f"-{args.slug}" if args.slug else ""))
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("check", cmd_check), ("next", cmd_next)):
        sp = sub.add_parser(name)
        sp.add_argument("root", help="diretorio real dos PRDs (o '/docs/prd' da "
                        "documentacao e relativo a raiz do repositorio)")
        if name == "next":
            sp.add_argument("--slug", help="slug kebab-case para compor NNNN-<slug>")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    if not os.path.isdir(args.root):
        print(f"seq: raiz inexistente: {args.root}", file=sys.stderr)
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
