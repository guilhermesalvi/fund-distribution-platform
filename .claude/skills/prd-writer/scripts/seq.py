#!/usr/bin/env python3
"""
seq.py - verificacao e alocacao deterministica do contador sequencial de
PRDs.

    Uso:
      python scripts/seq.py check <root> [--kind prd]
      python scripts/seq.py next  <root> [--kind prd] [--slug <feature-slug>]
                                  [--domain <domain-slug>] [--layout flat|nested]
      python scripts/seq.py next  <root> --overview [--domain <domain-slug>]
                                  [--layout flat|nested]

`<root>` e o diretorio real dos PRDs. Na documentacao da skill, `/docs/prd`
significa caminho relativo a raiz do repositorio; o chamador passa o caminho
real (`docs/prd`, `C:/repo/docs/prd`, ...). Qualquer diretorio serve: o
projeto define onde os PRDs vivem.

Convencao: `NNNN-<slug>` (4 digitos, zero a esquerda, slug kebab-case em
ingles), como arquivo `NNNN-<slug>.md` (plano) ou diretorio `NNNN-<slug>/`
com `prd.md` (pasta). O contador e global na raiz: o mesmo numero nao se
repete entre dominios, subpastas ou layouts. Dois layouts, um por
repositorio, inferidos do filesystem:
  flat    `<root>/NNNN-<domain>-<feature-slug>[.md]`
  nested  `<root>/<domain>/NNNN-<feature-slug>[.md]`
`check` acusa WARN quando os dois coexistem. `next --domain D --slug S`
imprime o path relativo a raiz no layout detectado; raiz sem artefato exige
`--layout`, e `--layout` que conflita com o layout detectado e erro.

PRD 0000 (visao geral, writing.md, PRD 0000) fica sempre na raiz:
`0000-<domain>-overview.md` em flat, `0000-overview.md` em nested.
`next --overview` imprime esse path e falha se 0000 ja existe. O 0000 na
raiz nao conta para a deteccao de layout.

O que nao e PRD: `README.md`, `assets/`, `archive/` e o conteudo de uma pasta
de PRD (`decisions.md`, `assets/`). `.md` sem numero fora dessas excecoes e
WARN (legado).

`check` (exit 1 em HARD):
  HARD  numero duplicado (global na raiz); prefixo numerico fora do formato;
        slug fora do kebab-case; arquivo e diretorio com o mesmo nome;
        substituicao: `| **Substitui** | NNNN |` (ou Supersedes/Replaces)
        apontando para numero inexistente ou nao anterior ao proprio; Status
        `Substituido por NNNN`/`Superseded by NNNN` apontando para numero
        inexistente; relacao nao reciproca (um lado declara e o outro nao);
        ciclo.
  WARN  lacuna na sequencia; candidato sem numero (legado); mesmo slug em
        dois numeros sem marcacao de substituicao; layouts flat e nested
        coexistindo. A sequencia pode comecar em 0000 ou 0001.
Os marcadores de substituicao sao lidos nas primeiras 40 linhas do
`.md` (plano) ou do `prd.md` (pasta), so na forma de linha da tabela do
header; "substitui" em prosa nao conta. A extensao `.md` e aceita em
qualquer caixa (`.MD`), como no lint_prd.py.

`next` roda todas as checagens de `check` e se recusa a alocar sobre HARD.
Imprime o proximo numero (`NNNN-<slug>` com --slug; path completo relativo
a raiz com --domain) sem tocar no disco. O numero e derivado do maior
existente, nunca de um contador armazenado - o estado e o proprio
filesystem. Colisao e reportada, nunca corrigida: o script nao renumera.

O que o script NAO faz: dizer qual regra prevalece. Precedencia vive no
conteudo (`Substitui` no header). O numero e indice e ordem de chegada, nao
semantica.
"""

import argparse
import os
import re
import sys

NUMBERED = re.compile(r"^(\d+)-(.*?)(\.md)?$", re.IGNORECASE)
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
WIDTH = 4
NOT_PRD = ("README.md", "assets", "archive")

# Marcadores de precedencia, lidos nas primeiras linhas do artefato e so na
# forma do header (output.md, Header): a linha de tabela `| **Substitui** |
# NNNN |` e o Status `Substituido por NNNN`. Prosa com o verbo "substitui"
# seguido de um numero nao e marcador (mesma leitura do lint_prd.py).
# Os numeros sao todos os tokens de 4 digitos da celula (`0001`, `PRD 0001`,
# `[0001](0001-x.md)`, `0001, 0002`), a mesma leitura do lint_prd.py.
SUPERSEDES = re.compile(
    r"^\|\s*\*{0,2}\s*(supersedes|substitui|replaces)\s*\*{0,2}\s*\|([^|\n]*)",
    re.IGNORECASE | re.MULTILINE)
FOUR_DIGITS = re.compile(r"\b(\d{4})\b")
SUPERSEDED_BY = re.compile(
    r"^\|\s*\*{0,2}\s*status\s*\*{0,2}\s*\|[^|]*?"
    r"(superseded[- ]by|substitu[ií]d[oa] por|replaced by)\s+(\d{4})\b",
    re.IGNORECASE | re.MULTILINE)
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
        """Arquivo markdown principal do PRD, se existir."""
        if not self.is_dir:
            return self.path
        p = os.path.join(self.path, "prd.md")
        return p if os.path.isfile(p) else None


def infer_kind(root):
    name = os.path.basename(os.path.normpath(root)).lower()
    if name in ("specs", "spec", "changes", "adr", "adrs", "decisions"):
        return None
    return "prd"


def candidate_dirs(root):
    """Diretorios cujos filhos diretos sao os PRDs numerados: a propria raiz
    (layout flat e PRD 0000) mais cada subdiretorio nao numerado (pasta de
    dominio, layout nested). Subdiretorio numerado na raiz e PRD em pasta,
    nao pasta de dominio."""
    root = os.path.normpath(root)
    domains = [os.path.join(root, d) for d in sorted(os.listdir(root))
               if os.path.isdir(os.path.join(root, d))
               and not d.startswith(".") and not NUMBERED.match(d)
               and d not in NOT_PRD]
    return [root] + domains


def collect(root, rep):
    entries = []
    root = os.path.normpath(root)
    for parent in candidate_dirs(root):
        for name in sorted(os.listdir(parent)):
            if name.startswith(".") or name in NOT_PRD:
                continue
            path = os.path.join(parent, name)
            is_dir = os.path.isdir(path)
            is_md = name.lower().endswith(".md")
            if not is_dir and not is_md:
                continue
            if parent == root and is_dir and not NUMBERED.match(name):
                continue  # pasta de dominio: ja e um parent em candidate_dirs
            m = NUMBERED.match(name)
            if not m:
                stem = name[:-3] if is_md else name
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
            rep.hard("arquivo e diretorio com o mesmo nome - PRD plano nao "
                     "convive com PRD em pasta", e.path)
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
                     f"raiz, entre dominios e subpastas): {paths}. Renumere o "
                     "artefato que chegou depois; o script nao renumera")

    if numbered:
        present = sorted(by_num)
        missing = [n for n in range(present[0], present[-1] + 1) if n not in by_num]
        if present[0] > 1:
            rep.warn(f"sequencia nao comeca em {0:0{WIDTH}d} (visao geral) nem em "
                     f"{1:0{WIDTH}d} (primeiro: {present[0]:0{WIDTH}d})")
        for n in missing:
            rep.warn(f"lacuna na sequencia: {n:0{WIDTH}d} ausente")
    return by_num


def detect_layout(entries, root):
    """'flat', 'nested', 'mixed' ou None (sem artefato numerado). O PRD 0000
    fica na raiz nos dois layouts e nao conta."""
    root = os.path.normpath(root)
    numbered = [e for e in entries if e.number is not None and e.number != 0]
    flat = any(os.path.dirname(e.path) == root for e in numbered)
    nested = any(os.path.dirname(e.path) != root for e in numbered)
    if flat and nested:
        return "mixed"
    if flat:
        return "flat"
    if nested:
        return "nested"
    return None


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
        head = "\n".join(l.rstrip("\n") for l in read_head(doc))
        supersedes.setdefault(e.number, set())
        superseded_by.setdefault(e.number, set())
        for _, cell in SUPERSEDES.findall(head):
            for target in FOUR_DIGITS.findall(cell):
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
                rep.hard(f"superseded-by {target}: um PRD nao substitui a si mesmo", doc)

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
            # cada par consecutivo da cadeia esta ligado em alguma direcao
            marked = all((a, b) in linked or (b, a) in linked for a, b in zip(nums, nums[1:]))
            if not marked:
                rep.warn(f"slug '{slug}' em mais de um numero "
                         f"({', '.join(f'{n:0{WIDTH}d}' for n in nums)}) - "
                         "se e substituicao, declare supersedes/superseded-by")


def run_checks(root, rep):
    entries = collect(root, rep)
    by_num = check_shape(entries, rep)
    if detect_layout(entries, root) == "mixed":
        rep.warn("layouts flat e nested coexistem - escolha um por repositorio "
                 "e mova os artefatos do outro")
    check_supersedes(entries, by_num, rep)
    return entries


def cmd_check(args):
    rep = Report()
    run_checks(args.root, rep)
    return rep.emit(args.root)


def resolve_layout(entries, root, requested):
    detected = detect_layout(entries, root)
    layout = requested or detected
    if layout in (None, "mixed"):
        why = ("raiz sem artefato numerado" if detected is None
               else "layouts flat e nested coexistem")
        print(f"seq: {why}; passe --layout flat|nested", file=sys.stderr)
        return None
    if detected not in (None, "mixed") and layout != detected:
        print(f"seq: layout detectado e '{detected}'; --layout {layout} "
              f"conflita - nao misture layouts", file=sys.stderr)
        return None
    return layout


def cmd_next(args):
    rep = Report()
    entries = run_checks(args.root, rep)
    if rep.hard_findings:
        rep.emit(args.root)
        print("seq: sequencia invalida; nao aloco numero sobre HARD pendente.",
              file=sys.stderr)
        return 1
    for label, value in (("slug", args.slug), ("domain", args.domain)):
        if value is not None and not SLUG.match(value):
            print(f"seq: {label} fora do kebab-case ascii minusculo: '{value}'",
                  file=sys.stderr)
            return 1
    if args.overview:
        if args.slug is not None:
            print("seq: --overview nao aceita --slug (o slug e 'overview')",
                  file=sys.stderr)
            return 1
        existing = [e for e in entries if e.number == 0]
        if existing:
            print(f"seq: PRD 0000 ja existe: {existing[0].path}", file=sys.stderr)
            return 1
        layout = resolve_layout(entries, args.root, args.layout)
        if layout is None:
            return 1
        if layout == "flat":
            if args.domain is None:
                print("seq: layout flat exige --domain para 0000-<domain>-overview.md",
                      file=sys.stderr)
                return 1
            rel = f"{0:0{WIDTH}d}-{args.domain}-overview.md"
        else:
            rel = f"{0:0{WIDTH}d}-overview.md"
        print(rel)
        return 0
    nums = [e.number for e in entries if e.number is not None]
    nxt = (max(nums) + 1) if nums else 1
    if nxt > 10 ** WIDTH - 1:
        print(f"seq: contador estourou {WIDTH} digitos", file=sys.stderr)
        return 1
    if args.domain is None:
        if args.slug is None:
            print(f"{nxt:0{WIDTH}d}")
            return 0
        full_slug, rel = args.slug, f"{nxt:0{WIDTH}d}-{args.slug}"
    else:
        if args.slug is None:
            print("seq: --domain exige --slug", file=sys.stderr)
            return 1
        layout = resolve_layout(entries, args.root, args.layout)
        if layout is None:
            return 1
        if layout == "flat":
            full_slug = f"{args.domain}-{args.slug}"
            rel = f"{nxt:0{WIDTH}d}-{full_slug}"
        else:
            full_slug = args.slug
            rel = f"{args.domain}/{nxt:0{WIDTH}d}-{args.slug}"
    if any(e.slug == full_slug for e in entries):
        print(f"seq: aviso - slug '{full_slug}' ja existe; se e substituicao, "
              f"declare supersedes no header", file=sys.stderr)
    print(rel)
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
        sp.add_argument("--kind", choices=("prd",), default="prd",
                        help="so 'prd'")
        if name == "next":
            sp.add_argument("--slug", help="feature-slug para compor NNNN-<slug>")
            sp.add_argument("--domain", help="domain-slug; imprime o path "
                            "relativo a raiz no layout do repositorio")
            sp.add_argument("--layout", choices=("flat", "nested"),
                            help="obrigatorio com --domain/--overview quando a raiz "
                                 "nao tem artefato numerado; deve coincidir com o "
                                 "detectado")
            sp.add_argument("--overview", action="store_true",
                            help="aloca o PRD 0000 (0000-<domain>-overview.md em "
                                 "flat, 0000-overview.md em nested); falha se ja existe")
        sp.set_defaults(fn=fn)
    args = p.parse_args(argv)
    if not os.path.isdir(args.root):
        print(f"seq: raiz inexistente: {args.root}", file=sys.stderr)
        return 2
    if infer_kind(args.root) is None:
        print(f"seq: '{os.path.basename(os.path.normpath(args.root))}' parece raiz de "
              "specs ou ADRs; este seq.py cuida so de PRDs", file=sys.stderr)
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
