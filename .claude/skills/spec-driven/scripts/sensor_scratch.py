#!/usr/bin/env python3
"""
sensor_scratch.py - scratch isolado para o sensor de discriminacao (verify.md,
2.4): a versao verificada da mudanca, num worktree separado, com snapshot
imutavel para voltar entre mutacoes. A arvore real, o index e os branches do
repositorio nunca mudam.

    Uso:  python3 <skill-dir>/scripts/sensor_scratch.py create <dir> [--repo <path>] [--path <p> ...]
          python3 <skill-dir>/scripts/sensor_scratch.py reset <dir>
          python3 <skill-dir>/scripts/sensor_scratch.py remove <dir>

create
    `git worktree add --detach <dir> HEAD` e, sobre ele, o que ainda nao esta
    commitado: `git diff HEAD --binary` (staged e unstaged, inclusive remocoes
    e renames) aplicado com `git apply`, mais os arquivos untracked nao
    ignorados, copiados. O patch e relativo a HEAD, nao a base da mudanca:
    diff contra a base inclui commits que HEAD ja tem e nao aplica. Com
    `--path`, so o que esta sob esses paths entra (alteracao preexistente fora
    da mudanca fica de fora); sem `--path`, tudo. O resultado e commitado no
    scratch (HEAD destacado, `--no-verify`, autor fixo) como snapshot; o hash
    do snapshot fica em `<git-dir-do-worktree>/sdd-snapshot` e e impresso.
    Arquivo ignorado (bin/, obj/, node_modules/) nao e copiado: o gate no
    scratch precisa se bastar (restore, build). Recusa <dir> existente e nao
    vazio.

reset
    `git reset --hard <snapshot>` + `git clean -fd` no scratch: volta a versao
    verificada e remove arquivo que a mutacao criou (ignorados ficam). Falha
    (exit 1) se, depois disso, `git status --porcelain` nao estiver vazio ou
    HEAD nao for o snapshot. `git checkout -- .` nao serve para isso: restaura
    o index, que no worktree recem-criado e HEAD, nao a versao verificada.

remove
    `git worktree remove --force <dir>` + `git worktree prune`. O commit de
    snapshot fica dangling e o gc do git o recolhe.

Sem Git (modes.md, Sem repositorio Git): copia integral do diretorio do
projeto, com uma segunda copia intocada como snapshot; este script nao cobre
esse caso.

Exit 0 ok, 1 falha (git falhou, scratch fora do snapshot), 2 uso.
"""

import argparse
import os
import shutil
import subprocess
import sys

SNAPSHOT_FILE = "sdd-snapshot"
SNAPSHOT_MSG = "sdd: verified snapshot for discrimination sensor"
GIT_IDENTITY = ["-c", "user.name=sdd-sensor", "-c", "user.email=sdd-sensor@localhost",
                "-c", "commit.gpgsign=false"]


class GitError(RuntimeError):
    pass


def git(args, cwd, check=True, binary=False, input_bytes=None):
    """Roda git em cwd. Retorna stdout (str, ou bytes com binary=True)."""
    cmd = ["git"] + GIT_IDENTITY + list(args)
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, input=input_bytes)
    except OSError as e:
        raise GitError(f"git indisponivel: {e}")
    if check and r.returncode != 0:
        err = r.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"`git {' '.join(args)}` falhou (exit {r.returncode}): {err}")
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


def worktree_git_dir(scratch):
    """Diretorio git privado do worktree (.git/worktrees/<nome>), absoluto."""
    out = git(["rev-parse", "--git-dir"], cwd=scratch).strip()
    return os.path.normpath(os.path.join(scratch, out)) if not os.path.isabs(out) else out


def snapshot_path(scratch):
    return os.path.join(worktree_git_dir(scratch), SNAPSHOT_FILE)


def read_snapshot(scratch):
    if not os.path.isdir(scratch):
        raise GitError(f"{scratch} nao existe")
    p = snapshot_path(scratch)
    try:
        with open(p, encoding="utf-8") as f:
            sha = f.read().strip()
    except OSError:
        raise GitError(f"snapshot ausente em {p}: o scratch nao foi criado por `create`")
    if not sha:
        raise GitError(f"snapshot vazio em {p}")
    return sha


def untracked_files(repo, paths):
    out = git(["ls-files", "--others", "--exclude-standard", "-z", "--"] + paths, cwd=repo, binary=True)
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def create(scratch, repo, paths):
    repo = os.path.abspath(repo)
    scratch = os.path.abspath(scratch)
    git(["rev-parse", "--verify", "HEAD"], cwd=repo)
    if os.path.exists(scratch) and os.listdir(scratch):
        raise GitError(f"{scratch} existe e nao esta vazio; escolha outro diretorio ou rode `remove`")
    git(["worktree", "add", "--detach", "--quiet", scratch, "HEAD"], cwd=repo)
    patch = git(["diff", "HEAD", "--binary", "--"] + paths, cwd=repo, binary=True)
    applied = []
    if patch.strip():
        git(["apply", "--whitespace=nowarn", "-"], cwd=scratch, input_bytes=patch)
        applied = [l for l in git(["diff", "HEAD", "--name-status", "--"] + paths, cwd=repo).splitlines() if l]
    copied = []
    for rel in untracked_files(repo, paths):
        src = os.path.join(repo, rel)
        dst = os.path.join(scratch, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel)
    git(["add", "-A"], cwd=scratch)
    git(["commit", "--quiet", "--no-verify", "--allow-empty", "-m", SNAPSHOT_MSG], cwd=scratch)
    sha = git(["rev-parse", "HEAD"], cwd=scratch).strip()
    with open(snapshot_path(scratch), "w", encoding="utf-8") as f:
        f.write(sha + "\n")
    status = git(["status", "--porcelain"], cwd=scratch)
    if status.strip():
        raise GitError(f"scratch sujo logo apos o snapshot:\n{status}")
    print(f"scratch: {scratch}")
    print(f"snapshot: {sha}")
    print(f"tracked changes applied: {len(applied)}")
    for l in applied:
        print(f"  {l}")
    print(f"untracked files copied: {len(copied)}")
    for rel in copied:
        print(f"  A\t{rel}")
    return 0


def reset(scratch):
    scratch = os.path.abspath(scratch)
    sha = read_snapshot(scratch)
    git(["reset", "--quiet", "--hard", sha], cwd=scratch)
    git(["clean", "--quiet", "-fd"], cwd=scratch)
    head = git(["rev-parse", "HEAD"], cwd=scratch).strip()
    status = git(["status", "--porcelain"], cwd=scratch)
    if head != sha or status.strip():
        raise GitError(f"scratch nao voltou ao snapshot {sha} (HEAD {head}):\n{status}")
    print(f"snapshot: {sha}")
    print("scratch restored: git status clean")
    return 0


def remove(scratch):
    scratch = os.path.abspath(scratch)
    if not os.path.isdir(scratch):
        raise GitError(f"{scratch} nao existe")
    common = git(["rev-parse", "--git-common-dir"], cwd=scratch).strip()
    repo_git = os.path.normpath(os.path.join(scratch, common)) if not os.path.isabs(common) else common
    git(["worktree", "remove", "--force", scratch], cwd=os.path.dirname(repo_git) or scratch)
    git(["worktree", "prune"], cwd=os.path.dirname(repo_git) or os.getcwd())
    print(f"scratch removed: {scratch}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="sensor_scratch.py",
                                description="Scratch com snapshot para o sensor de discriminacao.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="worktree em HEAD + alteracoes pendentes, commitadas como snapshot")
    c.add_argument("dir", help="diretorio novo (ou vazio) para o scratch")
    c.add_argument("--repo", default=".", metavar="PATH", help="repositorio de origem (default: cwd)")
    c.add_argument("--path", action="append", default=[], metavar="P",
                   help="restringe as alteracoes pendentes a este path (repetivel)")
    r = sub.add_parser("reset", help="volta o scratch ao snapshot")
    r.add_argument("dir")
    d = sub.add_parser("remove", help="remove o worktree do scratch")
    d.add_argument("dir")
    return p


def main(argv):
    parser = build_parser()
    if len(argv) < 2:
        parser.print_usage(sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2
    try:
        args = parser.parse_args(argv[1:])
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        if args.cmd == "create":
            return create(args.dir, args.repo, args.path)
        if args.cmd == "reset":
            return reset(args.dir)
        return remove(args.dir)
    except GitError as e:
        print(f"sensor_scratch {args.cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
