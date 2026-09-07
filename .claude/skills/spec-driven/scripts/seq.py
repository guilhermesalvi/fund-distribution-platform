#!/usr/bin/env python3
"""
seq.py - verificacao e alocacao deterministica do contador sequencial de
mudancas de spec e ADRs (skill spec-driven). PRDs sao do seq.py da skill
prd-writer: `--kind prd` e recusado aqui.

    Uso:
      python3 <skill-dir>/scripts/seq.py check <root> [--kind change|adr]
      python3 <skill-dir>/scripts/seq.py next  <root> [--kind change|adr] [--slug <slug>]

`<root>` e o diretorio real dos artefatos. Na documentacao da skill,
`/docs/specs` e `/docs/adr` significam caminho relativo a raiz do
repositorio; o chamador passa o caminho real (`docs/specs`,
`C:/repo/docs/adr`, ...). Qualquer diretorio serve: o projeto define onde
os artefatos vivem. `--kind` e inferido do nome da raiz (`specs`, `spec`,
`changes` -> change; `adr`, `adrs`, `decisions` -> adr); raiz com outro
nome exige `--kind`.

Convencao: `NNNN-<slug>` (4 digitos, zero a esquerda, slug kebab-case em
ingles). O contador e global por raiz:
  change  `<root>/**/changes/NNNN-<feature-slug>/` (diretorio com `spec.md`),
          em qualquer profundidade abaixo da raiz
  adr     `<root>/NNNN-<slug>.md` (arquivos planos na raiz)
O mesmo numero nao se repete entre capabilities ou dominios.

`check` (exit 1 em HARD):
  HARD  numero duplicado (global na raiz); prefixo numerico fora do formato;
        slug fora do kebab-case; arquivo e diretorio com o mesmo nome;
        substituicao: `Substitui NNNN`/`Supersedes NNNN` apontando para
        numero inexistente ou nao anterior ao proprio; `Substituido por
        NNNN`/`Superseded by NNNN` apontando para numero inexistente;
        relacao nao reciproca (um lado declara e o outro nao); ciclo.
  WARN  lacuna na sequencia; candidato sem numero (legado); mesmo slug em
        dois numeros sem marcacao de substituicao.
Os marcadores de substituicao sao lidos nas primeiras 40 linhas do `.md`
(adr) ou do `spec.md` (change).

`next` roda todas as checagens de `check` e se recusa a alocar sobre HARD.
Imprime o proximo numero (ou `NNNN-<slug>` com --slug) sem tocar no disco.
O numero e derivado do maior existente, nunca de um contador armazenado - o
estado e o proprio filesystem. Colisao e reportada, nunca corrigida: o
script nao renumera.

O que o script NAO faz: dizer qual regra prevalece. Precedencia vive no
conteudo (MODIFIED/REMOVED apontando para ID; `supersedes:` no header). O
numero e indice e ordem de chegada, nao semantica.
"""

import argparse
import os
import re
import sys

NUMBERED = re.compile(r"^(\d+)-(.*?)(\.md)?$")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WIDTH = 4
KINDS = ("change", "adr")
PRD_MSG = ("seq: --kind prd nao e deste script; PRDs sao do seq.py da skill "
           "prd-writer (<prd-writer>/scripts/seq.py)")

# marcadores de precedencia lidos nas primeiras linhas do artefato
SUPERSEDES = re.compile(
    r"\b(supersedes|substitui|replaces)\b[^0-9\n]{0,40}(\d{4})", re.IGNORECASE)
SUPERSEDED_BY = re.compile(
    r"\b(superseded[- ]by|substitu[ií]d[oa] por|replaced by)\b[^0-9\n]{0,40}(\d{4})",
    re.IGNORECASE)
HEADER_SCAN_LINES = 40


class Report:
    def __init__(self):
        self.hard_findings = []
        self.warn_findings = []

    def hard(self, msg, where=None):
        self.hard_findings.append((where, msg))

    def warn(self, msg, where=None):
        self.warn_findings.append((where, msg))

    def emit(self, root):
        for where, msg in self.hard_findings:
            print(f"HARD  {where or '-'}  {msg}")
        for where, msg in self.warn_findings:
            print(f"WARN  {where or '-'}  {msg}")
        h, w = len(self.hard_findings), len(self.warn_findings)
        tail = ("Corrija os HARD antes de criar ou apresentar o artefato."
                if h else "Apenas WARN - julgue cada um.")
        print(f"\nseq: {h} HARD, {w} WARN em {root}. {tail}")
        return 1 if h else 0


class Entry:
    def __init__(self, path, number, slug, is_dir):
        self.path = path
        self.number = number      # int ou None (sem numero)
        self.slug = slug
        self.is_dir = is_dir

    @property
    def doc(self):
        """Arquivo markdown principal do artefato, se existir."""
        if not self.is_dir:
            return self.path
        p = os.path.join(self.path, "spec.md")
        return p if os.path.isfile(p) else None


def infer_kind(root):
    name = os.path.basename(os.path.normpath(root)).lower()
    if name in ("specs", "spec", "changes"):
        return "change"
    if name in ("adr", "adrs", "decisions"):
        return "adr"
    return None


def candidate_dirs(root, kind):
    """Diretorios cujos filhos diretos sao os artefatos numerados."""
    root = os.path.normpath(root)
    if kind == "adr":
        return [root]
    out = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        if os.path.basename(dirpath) == "changes":
            out.append(dirpath)
            dirnames[:] = []  # o conteudo de uma mudanca nao e artefato numerado
    return out


def collect(root, kind, rep):
    entries = []
    for parent in candidate_dirs(root, kind):
        for name in sorted(os.listdir(parent)):
            if name.startswith(".") or name in ("README.md", "assets", "archive"):
                continue
            path = os.path.join(parent, name)
            is_dir = os.path.isdir(path)
            if not is_dir and not name.endswith(".md"):
                continue
            m = NUMBERED.match(name)
            if not m:
                stem = name[:-3] if name.endswith(".md") else name
                entries.append(Entry(path, None, stem, is_dir))
                continue
            digits, slug, _ = m.groups()
            if len(digits) != WIDTH:
                rep.hard(f"prefixo numerico deve ter exatamente {WIDTH} digitos "
                         f"(veio '{digits}')", path)
            if not SLUG.match(slug):
                rep.hard(f"slug fora do kebab-case ascii minusculo: '{slug}'", path)
            entries.append(Entry(path, int(digits), slug, is_dir))
    return entries


def check_shape(entries, rep):
    # arquivo e diretorio com o mesmo nome (0004-x.md e 0004-x/)
    seen = {}
    for e in entries:
        key = (os.path.dirname(e.path), e.number, e.slug)
        if key in seen and seen[key].is_dir != e.is_dir:
            rep.hard("arquivo e diretorio com o mesmo nome - artefato plano nao "
                     "convive com artefato em pasta", e.path)
        seen[key] = e

    for e in entries:
        if e.number is None:
            rep.warn("candidato sem prefixo numerico (legado?) - renumere ou "
                     "mova para fora do diretorio de artefatos", e.path)

    numbered = [e for e in entries if e.number is not None]
    by_num = {}
    for e in numbered:
        by_num.setdefault(e.number, []).append(e)
    for n, group in sorted(by_num.items()):
        distinct = {(os.path.dirname(g.path), g.slug) for g in group}
        if len(distinct) > 1:
            paths = ", ".join(g.path for g in group)
            rep.hard(f"numero {n:0{WIDTH}d} duplicado (o contador e global na "
                     f"raiz, entre capabilities e dominios): {paths}. Renumere o "
                     "artefato que chegou depois; o script nao renumera")

    if numbered:
        present = sorted(by_num)
        missing = [n for n in range(present[0], present[-1] + 1) if n not in by_num]
        if present[0] != 1:
            rep.warn(f"sequencia nao comeca em {1:0{WIDTH}d} "
                     f"(primeiro: {present[0]:0{WIDTH}d})")
        for n in missing:
            rep.warn(f"lacuna na sequencia: {n:0{WIDTH}d} ausente")
    return by_num


def read_head(path):
    try:
        with open(path, encoding="utf-8") as f:
            return [next(f) for _ in range(HEADER_SCAN_LINES)]
    except StopIteration:
        with open(path, encoding="utf-8") as f:
            return f.read().splitlines()
    except OSError:
        return []


def check_supersedes(entries, by_num, rep):
    """Reciprocidade Substitui <-> Substituido por, alvo inexistente, ordem,
    ciclo; e o WARN de slug repetido sem marcacao."""
    numbered = [e for e in entries if e.number is not None]
    supersedes = {}     # numero -> set de numeros que ele substitui
    superseded_by = {}  # numero -> set de numeros declarados como substituto
    for e in numbered:
        doc = e.doc
        if not doc:
            continue
        head = "".join(read_head(doc))
        supersedes.setdefault(e.number, set())
        superseded_by.setdefault(e.number, set())
        for _, target in SUPERSEDES.findall(head):
            t = int(target)
            supersedes[e.number].add(t)
            if t not in by_num:
                rep.hard(f"supersedes {target}: numero inexistente", doc)
            elif t >= e.number:
                rep.hard(f"supersedes {target}: alvo deve ser anterior a "
                         f"{e.number:0{WIDTH}d} - a sequencia e a ordem de precedencia", doc)
        for _, target in SUPERSEDED_BY.findall(head):
            t = int(target)
            superseded_by[e.number].add(t)
            if t not in by_num:
                rep.hard(f"superseded-by {target}: numero inexistente", doc)
            elif t == e.number:
                rep.hard(f"superseded-by {target}: um artefato nao substitui a si mesmo", doc)

    def docs_of(n):
        return [e.doc for e in by_num.get(n, []) if e.doc]

    # reciprocidade
    for new, olds in supersedes.items():
        for old in olds:
            if old in by_num and old != new and new not in superseded_by.get(old, set()):
                for doc in docs_of(old):
                    rep.hard(f"{new:0{WIDTH}d} declara supersedes {old:0{WIDTH}d}, mas "
                             f"este artefato nao declara 'superseded-by {new:0{WIDTH}d}' "
                             "- a relacao precisa ser reciproca", doc)
    for old, news in superseded_by.items():
        for new in news:
            if new in by_num and new != old and old not in supersedes.get(new, set()):
                for doc in docs_of(old):
                    rep.hard(f"declara superseded-by {new:0{WIDTH}d}, mas "
                             f"{new:0{WIDTH}d} nao declara 'supersedes {old:0{WIDTH}d}' "
                             "- a relacao precisa ser reciproca", doc)

    # ciclo no grafo antigo -> novo
    edges = {}
    for new, olds in supersedes.items():
        for old in olds:
            edges.setdefault(old, set()).add(new)
    for old, news in superseded_by.items():
        for new in news:
            edges.setdefault(old, set()).add(new)
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
        chain = " -> ".join(f"{n:0{WIDTH}d}" for n in sorted(in_cycle))
        for n in sorted(in_cycle):
            for doc in docs_of(n) or [None]:
                rep.hard(f"ciclo de substituicao ({chain})", doc)

    # slug repetido sem marcacao
    linked = set()
    for new, olds in supersedes.items():
        linked.update((old, new) for old in olds)
    for old, news in superseded_by.items():
        linked.update((old, new) for new in news)
    by_slug = {}
    for e in numbered:
        by_slug.setdefault(e.slug, []).append(e)
    for slug, group in by_slug.items():
        if len(group) > 1:
            nums = sorted(g.number for g in group)
            marked = all(any((a, b) in linked for b in nums if b != a) for a in nums)
            if not marked:
                rep.warn(f"slug '{slug}' em mais de um numero "
                         f"({', '.join(f'{n:0{WIDTH}d}' for n in nums)}) - "
                         "se e substituicao, declare supersedes/superseded-by")


def run_checks(root, kind, rep):
    entries = collect(root, kind, rep)
    by_num = check_shape(entries, rep)
    check_supersedes(entries, by_num, rep)
    return entries


def cmd_check(args):
    rep = Report()
    run_checks(args.root, args.kind, rep)
    return rep.emit(args.root)


def cmd_next(args):
    rep = Report()
    entries = run_checks(args.root, args.kind, rep)
    if rep.hard_findings:
        rep.emit(args.root)
        print("seq: sequencia invalida; nao aloco numero sobre HARD pendente.",
              file=sys.stderr)
        return 1
    nums = [e.number for e in entries if e.number is not None]
    nxt = (max(nums) + 1) if nums else 1
    if nxt > 10 ** WIDTH - 1:
        print(f"seq: contador estourou {WIDTH} digitos", file=sys.stderr)
        return 1
    if args.slug is not None:
        if not SLUG.match(args.slug):
            print(f"seq: slug fora do kebab-case ascii minusculo: '{args.slug}'",
                  file=sys.stderr)
            return 1
        if any(e.slug == args.slug for e in entries):
            print(f"seq: aviso - slug '{args.slug}' ja existe; se e substituicao, "
                  f"declare supersedes no header", file=sys.stderr)
        print(f"{nxt:0{WIDTH}d}-{args.slug}")
    else:
        print(f"{nxt:0{WIDTH}d}")
    return 0


def kind_arg(value):
    if value == "prd":
        raise argparse.ArgumentTypeError(PRD_MSG)
    if value not in KINDS:
        raise argparse.ArgumentTypeError(f"kind invalido '{value}'; use change|adr")
    return value


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("check", cmd_check), ("next", cmd_next)):
        sp = sub.add_parser(name)
        sp.add_argument("root", help="diretorio real dos artefatos (o '/docs/specs' "
                        "ou '/docs/adr' da documentacao e relativo a raiz do "
                        "repositorio)")
        sp.add_argument("--kind", type=kind_arg, metavar="{change,adr}",
                        help="tipo de artefato; inferido do nome da raiz se omitido. "
                             "PRDs sao do seq.py da skill prd-writer")
        if name == "next":
            sp.add_argument("--slug", help="slug para compor NNNN-<slug>")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    if not os.path.isdir(args.root):
        print(f"seq: raiz inexistente: {args.root}", file=sys.stderr)
        return 2
    if args.kind is None:
        name = os.path.basename(os.path.normpath(args.root)).lower()
        if name in ("prd", "prds"):
            print(PRD_MSG, file=sys.stderr)
            return 2
        args.kind = infer_kind(args.root)
        if args.kind is None:
            print("seq: nao consegui inferir --kind da raiz; passe --kind change|adr",
                  file=sys.stderr)
            return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
