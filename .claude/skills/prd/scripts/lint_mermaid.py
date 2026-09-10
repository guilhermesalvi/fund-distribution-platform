#!/usr/bin/env python3
"""
lint_mermaid.py - parse obrigatorio de todo bloco ```mermaid de arquivos .md.

    Uso:  python scripts/lint_mermaid.py <arquivo.md | diretorio> [...]
          python scripts/lint_mermaid.py --self-test
          python scripts/lint_mermaid.py --setup

Extrai cada bloco mermaid (sequenceDiagram, stateDiagram-v2, flowchart ou
qualquer outro tipo) e o submete a mermaid.parse() rodando em Node com jsdom -
sem Chromium. O parser e o de `mermaid-parser/` (versoes pinadas em
package.json).

Setup e validacao sao separados:

  - `--setup` instala as dependencias do parser (`npm ci` em mermaid-parser/),
    imprimindo o comando antes de executar. E o unico modo que acessa a rede.
  - A validacao (qualquer outra chamada) NUNCA instala nem acessa a rede. Sem
    `node`, sem `node_modules`, ou com o parser abortando (instalacao
    incompleta, Node incompativel), cada bloco vira HARD com prefixo
    `INCOMPLETO:` ("NAO validado - parser indisponivel") e o exit code e 3,
    para o chamador distinguir "parser indisponivel" de "diagrama invalido".
    O prefixo INCOMPLETO marca validacao que nao pode ser feita, nunca
    sucesso.

Extracao de fences (subconjunto do CommonMark, com uma excecao deliberada):

  - abertura: 3+ crases ou 3+ tils seguidos de `mermaid` (case-insensitive,
    espacos tolerados); fechamento: o MESMO caractere, comprimento >= abertura,
    nada alem de espacos na linha. Fence mermaid sem fechamento e HARD.
  - fences nao-mermaid sao rastreados apenas para que um bloco mermaid dentro
    de um fence externo demonstrativo (ex.: PRD inteiro dentro de
    ````markdown em references/example.md) seja extraido; o fence externo de
    4 crases nao e fechado por uma linha de 3 crases. Aqui o script diverge do
    CommonMark de proposito: pelo padrao, o conteudo do fence externo seria
    texto literal.
  - bloco ``` que nao e mermaid e ignorado.

O parse Mermaid NAO substitui a validacao da estrutura Markdown do documento
(secoes, IDs): isso e do lint_prd.py, que nao chama este script. Este script
so responde "o diagrama renderiza?".

Resultado por bloco: HARD com arquivo, indice do bloco (1-based), linha de
abertura e a mensagem do parser. Parser indisponivel tambem e HARD, nunca WARN
nem skip: diagrama nao validado e diagrama nao entregue.

--self-test prova (a) a extracao de fences em Python puro, sem parser, e (b) o
parser com casos fixos, entre eles um sequenceDiagram com `participant OFF as
Offering`, que precisa FALHAR (`off` e palavra reservada).

Saida: linhas `HARD  <arquivo>  L<linha>: bloco mermaid N: <mensagem>`.
Exit 0 se todos os blocos passaram, 1 se houver HARD de diagrama, 2 em erro de
uso (opcao desconhecida, path inexistente), 3 se o parser estiver
indisponivel (com HARD INCOMPLETO por bloco).

Importavel: `check_files(paths) -> (findings, blocks_checked)` onde findings e
uma lista de (path, line, msg); bloco nao parseado ou parser indisponivel e
finding (HARD para o chamador).
"""

import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PARSER_DIR = os.path.join(HERE, "mermaid-parser")
PARSER_JS = os.path.join(PARSER_DIR, "parse.mjs")
PARSER_MARKER = os.path.join(PARSER_DIR, "node_modules", "mermaid", "package.json")
SETUP_HINT = ("parser indisponivel: rode `python lint_mermaid.py --setup` "
              "(executa npm ci em scripts/mermaid-parser)")

FENCE_ANY = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
MERMAID_INFO = re.compile(r"^\s*mermaid\b", re.IGNORECASE)

EXIT_OK, EXIT_HARD, EXIT_USAGE, EXIT_PARSER_UNAVAILABLE = 0, 1, 2, 3
# Prefixo de finding que marca validacao incompleta (parser indisponivel),
# distinta de diagrama invalido. Quem consome findings o exibe.
INCOMPLETE_PREFIX = "INCOMPLETO: "


class ParserUnavailable(Exception):
    pass


# --- extracao ---------------------------------------------------------------

def _is_closer(line, fence):
    s = line.strip()
    return s.startswith(fence) and set(s) == {fence[0]}


def extract_blocks_from_text(text):
    """Retorna (blocks, problems).

    blocks   = [(index_1based, open_line_1based, body)]
    problems = [(open_line_1based, msg)] - fences mermaid sem fechamento.
    """
    lines = text.splitlines()
    blocks, problems = [], []
    stack = []  # fences nao-mermaid abertos: apenas o marcador (``` / ~~~~)
    i = 0
    while i < len(lines):
        m = FENCE_ANY.match(lines[i])
        if not m:
            i += 1
            continue
        fence, info = m.group(1), m.group(2)
        if stack and _is_closer(lines[i], stack[-1]):
            stack.pop()
            i += 1
            continue
        if not MERMAID_INFO.match(info):
            stack.append(fence)
            i += 1
            continue
        start = i
        body = []
        i += 1
        while i < len(lines) and not _is_closer(lines[i], fence):
            body.append(lines[i])
            i += 1
        if i >= len(lines):
            problems.append((start + 1, "fence mermaid sem fechamento"))
        blocks.append((len(blocks) + 1, start + 1, "\n".join(body)))
        i += 1
    return blocks, problems


def extract_blocks(path):
    with open(path, encoding="utf-8") as f:
        return extract_blocks_from_text(f.read())


# --- parser -----------------------------------------------------------------

def ensure_parser():
    """Verifica sem instalar. Levanta ParserUnavailable com a instrucao de setup."""
    if not os.path.isfile(PARSER_JS):
        raise ParserUnavailable(f"{SETUP_HINT}; parse.mjs ausente em {PARSER_DIR}")
    if not shutil.which("node"):
        raise ParserUnavailable(f"{SETUP_HINT}; node nao encontrado no PATH")
    if not os.path.isfile(PARSER_MARKER):
        raise ParserUnavailable(f"{SETUP_HINT}; node_modules ausente")


def parser_available():
    try:
        ensure_parser()
    except ParserUnavailable:
        return False
    return True


def setup_parser():
    """Unico caminho que instala. Imprime o comando antes de rodar."""
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not shutil.which("node"):
        print("lint_mermaid --setup: node nao encontrado no PATH", file=sys.stderr)
        return EXIT_PARSER_UNAVAILABLE
    if not npm:
        print("lint_mermaid --setup: npm nao encontrado no PATH", file=sys.stderr)
        return EXIT_PARSER_UNAVAILABLE
    cmd = [npm, "ci", "--no-audit", "--no-fund", "--loglevel=error"]
    print(f"lint_mermaid --setup: executando `{' '.join(cmd)}` em {PARSER_DIR}")
    try:
        r = subprocess.run(cmd, cwd=PARSER_DIR, shell=(os.name == "nt"), timeout=600)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"lint_mermaid --setup: npm ci falhou: {e}", file=sys.stderr)
        return EXIT_PARSER_UNAVAILABLE
    if r.returncode != 0 or not os.path.isfile(PARSER_MARKER):
        print(f"lint_mermaid --setup: npm ci falhou (exit {r.returncode})", file=sys.stderr)
        return EXIT_PARSER_UNAVAILABLE
    print("lint_mermaid --setup: parser instalado")
    return EXIT_OK


def parse_blocks(blocks):
    """blocks: lista de (id, text). Retorna dict id -> (ok, info)."""
    ensure_parser()
    payload = json.dumps([{"id": i, "text": t} for i, t in blocks])
    try:
        r = subprocess.run(["node", PARSER_JS], input=payload, capture_output=True,
                           text=True, encoding="utf-8", cwd=PARSER_DIR, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ParserUnavailable(f"node falhou: {e}")
    if r.returncode != 0:
        raise ParserUnavailable("parser abortou: " + (r.stderr or r.stdout).strip()[-400:])
    out = {}
    for line in r.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        d = json.loads(line)
        out[d["id"]] = (d["ok"], d.get("type") if d["ok"] else d.get("error", ""))
    missing = [i for i, _ in blocks if i not in out]
    if missing:
        raise ParserUnavailable(f"parser nao respondeu para {len(missing)} bloco(s)")
    return out


def _one_line(msg):
    return " | ".join(s.strip() for s in msg.splitlines() if s.strip())[:400]


def check_files(paths):
    """Retorna (findings, n_blocks). findings = [(path, line, msg)]."""
    per_file, findings = {}, []
    unclosed = set()
    for p in paths:
        blocks, problems = extract_blocks(p)
        per_file[p] = blocks
        for line, msg in problems:
            findings.append((p, line, msg))
            unclosed.add((p, line))
    n_blocks = sum(len(b) for b in per_file.values())
    flat = [(f"{p}::{idx}", text) for p, blocks in per_file.items()
            for idx, line, text in blocks if (p, line) not in unclosed]
    if not flat:
        return findings, n_blocks
    try:
        results = parse_blocks(flat)
    except ParserUnavailable as e:
        findings.extend((p, line, f"{INCOMPLETE_PREFIX}bloco mermaid {idx} NAO validado - {e}")
                        for p, blocks in per_file.items() for idx, line, _ in blocks
                        if (p, line) not in unclosed)
        return findings, n_blocks
    for p, blocks in per_file.items():
        for idx, line, _ in blocks:
            key = f"{p}::{idx}"
            if key not in results:
                continue
            ok, info = results[key]
            if not ok:
                findings.append((p, line, f"bloco mermaid {idx}: {_one_line(info)}"))
    findings.sort(key=lambda t: (paths.index(t[0]) if t[0] in paths else 0, t[1]))
    return findings, n_blocks


def collect_md(args):
    out = []
    for a in args:
        if os.path.isdir(a):
            for root, dirs, files in os.walk(a):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d != "node_modules")
                out.extend(os.path.join(root, f) for f in sorted(files) if f.endswith(".md"))
        else:
            out.append(a)
    return out


# --- self-test --------------------------------------------------------------

SELF_TEST_PARSER = [
    ("valid sequenceDiagram", True,
     "sequenceDiagram\n  participant Operador\n  participant Offering\n"
     "  Operador->>Offering: publicar (OFF-03)"),
    ("participant OFF as Offering (reserved word 'off')", False,
     "sequenceDiagram\n  participant OFF as Offering\n  participant Book\n  OFF->>Book: x"),
    ("participant end (reserved word)", False,
     "sequenceDiagram\n  participant end as Ending\n  participant Book\n  end->>Book: x"),
    ("valid stateDiagram-v2", True,
     "stateDiagram-v2\n  [*] --> Draft: criar (OFF-01)\n  Draft --> Open: publicar (OFF-03)"),
    ("valid flowchart", True,
     "flowchart TD\n  n0[\"Livro: D (ALLOC-05)\"] --> n1{\"D > 4B/3 ?\"}\n  n1 -- \"nao\" --> n2[fim]"),
    ("broken flowchart", False, "flowchart TD\n  A --> B{\"x\" --> C"),
]

# (nome, texto, blocos esperados [(linha, body)], problemas esperados [linha])
SELF_TEST_EXTRACT = [
    ("bloco simples",
     "# T\n\n```mermaid\nflowchart TD\n A-->B\n```\n",
     [(3, "flowchart TD\n A-->B")], []),
    ("aninhado em fence externo de 4 crases",
     "````markdown\n# PRD\n```mermaid\nflowchart TD\n A-->B\n```\ntexto\n````\n",
     [(3, "flowchart TD\n A-->B")], []),
    ("fence mermaid de 4 crases nao fecha com 3",
     "````mermaid\nflowchart TD\n A-->B\n```\n````\n",
     [(1, "flowchart TD\n A-->B\n```")], []),
    ("sem fechamento",
     "```mermaid\nflowchart TD\n A-->B\n",
     [(1, "flowchart TD\n A-->B")], [1]),
    ("fechamento com texto depois nao fecha",
     "```mermaid\nflowchart TD\n``` x\n",
     [(1, "flowchart TD\n``` x")], [1]),
    ("tils e caixa alta, espacos tolerados",
     "~~~  MERMAID\nflowchart TD\n~~~~\n",
     [(1, "flowchart TD")], []),
    ("tils nao fecham crases",
     "```mermaid\nflowchart TD\n~~~\n```\n",
     [(1, "flowchart TD\n~~~")], []),
    ("varios blocos, tamanhos diferentes, nao-mermaid ignorado",
     "```python\nprint(1)\n```\n\n```mermaid\nA\n```\n\n~~~~mermaid\nB\n~~~~\n\n`````mermaid\nC\n`````\n",
     [(5, "A"), (9, "B"), (13, "C")], []),
]


def self_test_extract():
    failed = 0
    for name, text, exp_blocks, exp_problems in SELF_TEST_EXTRACT:
        blocks, problems = extract_blocks_from_text(text)
        got_blocks = [(line, body) for _, line, body in blocks]
        got_problems = [line for line, _ in problems]
        ok = got_blocks == exp_blocks and got_problems == exp_problems
        failed += 0 if ok else 1
        print(f"{'ok' if ok else 'MISMATCH':8}  extracao: {name}")
        if not ok:
            print(f"          esperado blocos={exp_blocks} problemas={exp_problems}")
            print(f"          obtido   blocos={got_blocks} problemas={got_problems}")
    return failed


def self_test():
    failed = self_test_extract()
    try:
        results = parse_blocks([(name, text) for name, _, text in SELF_TEST_PARSER])
    except ParserUnavailable as e:
        print(f"HARD  self-test  {e}")
        print("-" * 60)
        print("self-test: extracao " + ("OK" if not failed else f"com {failed} caso(s) fora do esperado")
              + "; parser indisponivel")
        return EXIT_PARSER_UNAVAILABLE
    for name, expect_ok, _ in SELF_TEST_PARSER:
        ok, info = results[name]
        status = "ok" if ok == expect_ok else "MISMATCH"
        if ok != expect_ok:
            failed += 1
        detail = info if ok else _one_line(info)
        print(f"{status:8}  parser: {name}: parser={'pass' if ok else 'fail'} "
              f"expected={'pass' if expect_ok else 'fail'}  {detail}")
    print("-" * 60)
    print("self-test OK" if not failed else f"self-test: {failed} caso(s) fora do esperado")
    return EXIT_HARD if failed else EXIT_OK


def main(argv):
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return EXIT_USAGE
    if argv[1] == "--self-test":
        return self_test()
    if argv[1] == "--setup":
        return setup_parser()
    for a in argv[1:]:
        if a.startswith("-"):
            print(f"lint_mermaid: opcao desconhecida '{a}' (aceitas: --self-test, --setup)", file=sys.stderr)
            return EXIT_USAGE
        if not os.path.exists(a):
            print(f"lint_mermaid: path inexistente '{a}'", file=sys.stderr)
            return EXIT_USAGE
    paths = collect_md(argv[1:])
    if not paths:
        print("lint_mermaid: nenhum .md encontrado", file=sys.stderr)
        return EXIT_USAGE
    findings, n = check_files(paths)
    for p, line, msg in findings:
        print(f"HARD  {p}  L{line}: {msg}")
    print("-" * 60)
    if any(msg.startswith(INCOMPLETE_PREFIX) for _, _, msg in findings):
        print(f"{len(findings)} HARD em {n} bloco(s) mermaid. {SETUP_HINT}. "
              "Diagrama nao validado e diagrama nao entregue.")
        return EXIT_PARSER_UNAVAILABLE
    if findings:
        print(f"{len(findings)} HARD em {n} bloco(s) mermaid. Diagrama nao validado "
              "e diagrama nao entregue.")
        return EXIT_HARD
    print(f"OK  {n} bloco(s) mermaid em {len(paths)} arquivo(s) passaram no parse.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv))
