#!/usr/bin/env python3
"""
hotspots.py - evidencia deterministica do repositorio para a analise da base
(design.md, Analise da base): onde o codigo muda e quantas maos o tocam.

    Uso:  python3 <skill-dir>/scripts/hotspots.py <repo> [--days 90] [--share 0.9]
                                                   [--min-authors 3] [--top 30] [--path <subdir>]

Le `git log` da janela (default: ultimos 90 dias) e calcula, por arquivo,
quantidade de commits que o tocaram e autores distintos. Reporta:

  1. Hotspots: o menor conjunto de arquivos que concentra `--share` (default
     90%) das mudancas, cruzado com autores distintos >= `--min-authors`.
     Muitas mudancas com muitas maos e INDICIO de ownership difuso e de
     remendo acumulado (Don't Touch My Code, Microsoft Research), nao prova:
     um arquivo de composicao (Program.cs, csproj, CLAUDE.md) muda muito por
     construcao, e um time inteiro pode ser dono legitimo. E por ali que a
     leitura do design comeca, nao onde ela termina.
  2. Concentracao: quantos arquivos (e que fracao do total tocado) formam o
     conjunto de `--share`.
  3. Diretorios de primeiro nivel sem nenhuma mudanca na janela: ou nao dao
     bug e ninguem usa, ou a branch analisada esta errada.
  4. Autores mais ativos na janela, com commits e arquivos tocados: quem tem
     fluencia no repositorio para responder perguntas (nao quem e mais
     importante).

O que o script NAO faz: julgar. Churn e numero de autores sao indicio; a
conclusao (decisao registrada, divida, ownership difuso ou legitimo) exige
confirmar com CODEOWNERS, ADRs e o historico dos commits, e e isso que o
design vai procurar.

Resultado inconclusivo (menos de 10 commits na janela, ou nenhum arquivo
alterado) avisa e sai com exit 2, sem relatorio. Parametro invalido (`--days`,
`--min-authors`, `--top` < 1; `--share` fora de (0, 1]), repositorio
inexistente ou sem git, `--path` inexistente: exit 2 com mensagem. Exit 0 caso
contrario; nao ha HARD/WARN, e relatorio.
"""

import argparse
import collections
import os
import subprocess
import sys

MIN_COMMITS = 10


class GitError(Exception):
    pass


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, "-c", "core.quotepath=false", *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        raise GitError(f"git nao pode ser executado: {e}")
    if r.returncode != 0:
        raise GitError(f"git falhou: {r.stderr.strip()}")
    return r.stdout


def parse_args(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo", help="raiz do repositorio git")
    ap.add_argument("--days", type=int, default=90, help="janela em dias (default 90)")
    ap.add_argument("--share", type=float, default=0.9,
                    help="fracao das mudancas que define o conjunto concentrado (default 0.9)")
    ap.add_argument("--min-authors", type=int, default=3,
                    help="autores distintos para um arquivo do conjunto virar hotspot (default 3)")
    ap.add_argument("--top", type=int, default=30, help="linhas por tabela (default 30)")
    ap.add_argument("--path", default=None, help="restringe a um subdiretorio")
    args = ap.parse_args(argv)

    problems = []
    if args.days < 1:
        problems.append(f"--days deve ser >= 1 (recebido {args.days})")
    if not 0 < args.share <= 1:
        problems.append(f"--share deve estar em (0, 1] (recebido {args.share})")
    if args.min_authors < 1:
        problems.append(f"--min-authors deve ser >= 1 (recebido {args.min_authors})")
    if args.top < 1:
        problems.append(f"--top deve ser >= 1 (recebido {args.top})")
    if not os.path.isdir(args.repo):
        problems.append(f"repositorio inexistente: {args.repo}")
    elif args.path is not None and not os.path.exists(os.path.join(args.repo, args.path)):
        problems.append(f"--path inexistente no repositorio: {args.path}")
    return args, problems


def collect(repo, days, path):
    """Le o git log da janela. Retorna (n_commits, changes, authors_by_file,
    commits_by_author, files_by_author)."""
    log_args = ["log", f"--since={days} days ago", "--name-only",
                "--format=%x01%H%x02%an", "--no-merges"]
    if path:
        log_args += ["--", path]
    out = git(repo, *log_args)

    changes = collections.Counter()
    authors_by_file = collections.defaultdict(set)
    commits_by_author = collections.Counter()
    files_by_author = collections.defaultdict(set)
    n_commits = 0
    author = None
    for line in out.splitlines():
        if line.startswith("\x01"):
            _, author = line[1:].split("\x02", 1)
            n_commits += 1
            commits_by_author[author] += 1
            continue
        f = line.strip()
        if not f:
            continue
        changes[f] += 1
        authors_by_file[f].add(author)
        files_by_author[author].add(f)
    return n_commits, changes, authors_by_file, commits_by_author, files_by_author


def main(argv=None):
    args, problems = parse_args(argv)
    if problems:
        for p in problems:
            print(f"hotspots: {p}", file=sys.stderr)
        return 2

    try:
        git(args.repo, "rev-parse", "--git-dir")
    except GitError as e:
        print(f"hotspots: nao e um repositorio git ({args.repo}): {e}", file=sys.stderr)
        return 2

    try:
        git(args.repo, "rev-parse", "--verify", "--quiet", "HEAD")
    except GitError:
        print("hotspots: inconclusivo - repositorio sem nenhum commit", file=sys.stderr)
        return 2

    try:
        n_commits, changes, authors_by_file, commits_by_author, files_by_author = \
            collect(args.repo, args.days, args.path)
        branch = git(args.repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
    except GitError as e:
        print(f"hotspots: {e}", file=sys.stderr)
        return 2

    total = sum(changes.values())
    if n_commits < MIN_COMMITS or total == 0:
        print(f"hotspots: inconclusivo - {n_commits} commit(s) e {len(changes)} arquivo(s) "
              f"alterado(s) nos ultimos {args.days} dias"
              + (f" em {args.path}" if args.path else "")
              + f"; minimo {MIN_COMMITS} commits com arquivos. Janela curta demais, "
              "branch errada ou --path fora do que muda. Aumente --days.", file=sys.stderr)
        return 2

    ranked = changes.most_common()
    acc, concentrated = 0, []
    for f, n in ranked:
        concentrated.append((f, n))
        acc += n
        if acc / total >= args.share:
            break
    hotspots = [(f, n, len(authors_by_file[f])) for f, n in concentrated
                if len(authors_by_file[f]) >= args.min_authors]
    hotspots.sort(key=lambda x: (-x[1], -x[2], x[0]))

    print(f"# Hotspots de {os.path.abspath(args.repo)} (branch {branch}, ultimos {args.days} dias"
          + (f", path {args.path}" if args.path else "") + ")")
    print(f"commits: {n_commits} | arquivos tocados: {len(changes)} | "
          f"mudancas (arquivo x commit): {total}")
    print(f"concentracao: {len(concentrated)} arquivo(s) = "
          f"{len(concentrated) / len(changes):.0%} dos tocados somam {args.share:.0%} das mudancas")
    print()
    print(f"## Hotspots (indicio: no conjunto concentrado, >= {args.min_authors} autores)")
    print("| Arquivo | Mudancas | Autores |")
    print("|---|---|---|")
    for f, n, a in hotspots[:args.top]:
        print(f"| `{f}` | {n} | {a} |")
    if not hotspots:
        print("| (nenhum) | | |")
    print()
    print(f"## Conjunto concentrado ({args.share:.0%} das mudancas)")
    print("| Arquivo | Mudancas | Autores |")
    print("|---|---|---|")
    for f, n in concentrated[:args.top]:
        print(f"| `{f}` | {n} | {len(authors_by_file[f])} |")
    print()

    top_dirs = sorted(d for d in os.listdir(args.repo)
                      if os.path.isdir(os.path.join(args.repo, d)) and not d.startswith("."))
    touched_dirs = {f.split("/", 1)[0] for f in changes}
    quiet = [d for d in top_dirs if d not in touched_dirs]
    print(f"## Diretorios de primeiro nivel sem mudanca na janela ({len(quiet)}/{len(top_dirs)})")
    print(", ".join(f"`{d}`" for d in quiet) if quiet else "(nenhum)")
    print()
    print("## Autores na janela")
    print("| Autor | Commits | Arquivos tocados |")
    print("|---|---|---|")
    for a, n in commits_by_author.most_common(args.top):
        print(f"| {a} | {n} | {len(files_by_author[a])} |")
    print()
    print("Indicio, nao prova: churn e numero de autores nao demonstram ausencia de "
          "ownership nem divida. Confirme com CODEOWNERS, ADRs e o historico dos commits "
          "antes de registrar como [FATO].")
    return 0


if __name__ == "__main__":
    sys.exit(main())
