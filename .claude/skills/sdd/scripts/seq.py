#!/usr/bin/env python3
"""
seq.py - contador sequencial de uma pasta: proximo numero e numero duplicado.

    Uso:
      python3 scripts/seq.py check <dir>
      python3 scripts/seq.py next  <dir> [--slug <slug>]

`<dir>` e a pasta real onde os itens numerados vivem: a pasta de uma
capability (`/docs/specs/<domain>/<capability>`, onde cada mudanca e a
subpasta `NNNN-<change-slug>/`) ou a pasta das ADRs (`/docs/adr`, onde cada
ADR e o arquivo `NNNN-<slug>.md`). So os filhos diretos contam: 4 digitos,
zero a esquerda, slug kebab-case ascii minusculo; diretorios ocultos ficam
fora. O numero e local a pasta e o estado e o proprio filesystem, nunca um
contador armazenado.

`check` (exit 1 em HARD): numero usado por mais de um item. O script
reporta, nunca renumera.

`next` roda o `check`, recusa alocar sobre HARD e imprime max+1 sem tocar no
disco: `NNNN` sem `--slug`, `NNNN-<slug>` com `--slug`. O slug precisa ser
kebab-case ascii minusculo (exit 1 se nao for). Pasta sem item comeca em 0001.

Exit 2 em erro de uso: pasta inexistente, subcomando ou opcao desconhecida.
"""

import argparse
import os
import re
import sys

NUMBERED_DIR = re.compile(r"^(\d{4})-([^/\\]+)$")
NUMBERED_FILE = re.compile(r"^(\d{4})-([^/\\]+)\.md$", re.IGNORECASE)
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WIDTH = 4


def numbered_items(folder):
    """(numero, slug, path) de todo `NNNN-<slug>/` e `NNNN-<slug>.md` filho direto de folder."""
    out = []
    for name in sorted(os.listdir(folder)):
        if name.startswith("."):
            continue
        path = os.path.join(folder, name)
        m = NUMBERED_DIR.match(name) if os.path.isdir(path) else NUMBERED_FILE.match(name)
        if m:
            out.append((int(m.group(1)), m.group(2), path))
    return out


def duplicates(entries):
    by_num = {}
    for n, _, p in entries:
        by_num.setdefault(n, []).append(p)
    return {n: ps for n, ps in sorted(by_num.items()) if len(ps) > 1}


def report(dups):
    for n, paths in dups.items():
        print(f"HARD  numero {n:0{WIDTH}d} usado por mais de um item: {', '.join(paths)}")


def cmd_check(args):
    entries = numbered_items(args.dir)
    dups = duplicates(entries)
    report(dups)
    tail = " Renumere o item que chegou depois; o script nao renumera." if dups else ""
    print(f"seq: {len(dups)} HARD em {args.dir} ({len(entries)} item(ns)).{tail}")
    return 1 if dups else 0


def cmd_next(args):
    if args.slug is not None and not SLUG.match(args.slug):
        print(f"seq: slug fora do kebab-case ascii minusculo: '{args.slug}'", file=sys.stderr)
        return 1
    entries = numbered_items(args.dir)
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
        sp.add_argument("dir", help="pasta real da capability ou das ADRs")
        if name == "next":
            sp.add_argument("--slug", help="slug kebab-case para compor NNNN-<slug>")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    if not os.path.isdir(args.dir):
        print(f"seq: pasta inexistente: {args.dir}", file=sys.stderr)
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
