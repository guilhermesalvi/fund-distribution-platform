#!/usr/bin/env python3
"""
lint_validation.py - gate de conclusao: o validation.md do Verifier e real?

    Uso:  python3 <skill-dir>/scripts/lint_validation.py <validation.md>
              [--spec <delta-spec.md>] [--uat] [--evidence-of-run <log>]

Chamado pelo orquestrador (nao pelo Verifier): o Verifier e read-only e
devolve o relatorio; o orquestrador persiste validation.md, roda este linter
e so entao atualiza spec/tasks (SKILL.md, Gates; verify.md, 2.8).

O que o linter faz e o que nao faz: confere a CONSISTENCIA do relatorio
(veredito coerente com tabelas, gate, sensor, gaps) e a forma. NAO prova que
os comandos rodaram. `--evidence-of-run <log>` aproxima isso: o arquivo deve
existir e conter a string do comando do Gate Build.

Comentario de maquina (primeira linha nao vazia):
    <!-- sdd: validation | change: <NNNN-slug> | tier: <small|medium|large|complex> [| uat] -->
`change` ou `tier` ausente -> HARD (as regras proporcionais dependem do tier).

Veredito: uma palavra apos `**Veredito:**` / `**Verdict:**`, enumeracao exata
PASS | FAIL | BLOCKED; emojis opcionais depois. Qualquer outra coisa
(`NOT PASS`, `PASS | FAIL`, vazio) -> HARD. BLOCKED = verificacao incompleta
(dependencia indisponivel, gate nao executavel, sensor impossivel) e exige a
linha `**Motivo do bloqueio:** <texto>`.

Consistencia veredito x conteudo (cada violacao e HARD):
  PASS  -> toda linha de `## Conformidade a spec` com PASS/OK (sem X, GAP, FAIL,
           lacuna); `## Gate Build` com Falhou 0 (e exit 0, se houver) e
           Total > 0; `## Gaps` sem item numerado; `## Aderencia ao design`
           sem X; sensor sem mutante sobrevivente; `## UAT` sem X/Bloqueante/Maior.
  FAIL  -> ao menos um dos sinais negativos acima.
  BLOCKED -> motivo declarado.

Conteudo obrigatorio: tabela de conformidade com >=1 linha, 4 colunas por
linha, IDs de requisito unicos, linha PASS com file:line; Gate Build com
Comando, Total, Passou, Falhou, Pulou; Pulou > 0 exige justificativa na secao
(texto apos os numeros ou linha `Pulados:`). Com `--spec`, todo ID
ADDED/MODIFIED do delta aparece na tabela; sem `--spec`, WARN.

Proporcional ao tier: sensor de discriminacao obrigatorio em large/complex
(HARD), WARN em medium, nao exigido em small. Aderencia ao design: >=4 itens
quando existe design.md ao lado do validation.md; sem design.md, a secao pode
dizer "N/A porque ..." (plano inline). UAT obrigatorio com `--uat` ou flag
`uat` no comentario de maquina.

Exit: PASS valido -> 0; FAIL -> 1 ("mudanca NAO esta pronta"); BLOCKED -> 1
("verificacao incompleta/bloqueada: <motivo>"); qualquer HARD -> 1.
Saida: HARD (exit 1) / WARN (nao afeta exit).
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import (  # noqa: E402
    FILE_LINE, REQ_ID, Report, find_section, parse_machine_comment, read_lines,
    scan_placeholders, table_rows, usage,
)

VERDICTS = ("PASS", "FAIL", "BLOCKED")
TIERS = ("small", "medium", "large", "complex")

VERDICT_RE = re.compile(r"^\*\*(Veredito|Verdict)\s*:\*\*\s*(.*)$", re.IGNORECASE)
BLOCK_REASON_RE = re.compile(
    r"^\*\*(Motivo do bloqueio|Block(?:ing)? reason)\s*:\*\*\s*(.*)$", re.IGNORECASE)
NUMBERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+\S")
GATE_NUM_RE = {
    "total": re.compile(r"\bTotal\b\s*:?\s*(\d+)", re.IGNORECASE),
    "passed": re.compile(r"\b(?:Passou|Passed)\b\s*:?\s*(\d+)", re.IGNORECASE),
    "failed": re.compile(r"\b(?:Falhou|Failed)\b\s*:?\s*(\d+)", re.IGNORECASE),
    "skipped": re.compile(r"\b(?:Pulou|Skipped)\b\s*:?\s*(\d+)", re.IGNORECASE),
}
GATE_EXIT_RE = re.compile(r"\bexit\b\s*[:=]?\s*(\d+)", re.IGNORECASE)
GATE_CMD_RE = re.compile(r"\b(?:Comando|Command)\s*:\s*(.+?)(?:\s+·|\s+\||$)", re.IGNORECASE)
SKIP_JUSTIFICATION_RE = re.compile(r"^\s*(?:Pulados|Skipped)\s*:\s*\S", re.IGNORECASE)

NEG_RESULT_RE = re.compile(r"❌|\bGAP\b|\bFAIL\b|⚠️|lacuna", re.IGNORECASE)
POS_RESULT_RE = re.compile(r"✅|\bPASS\b")
SURVIVED_RE = re.compile(r"sobreviveu|survived|❌", re.IGNORECASE)
UAT_NEG_RE = re.compile(r"❌|\bBloqueante\b|\bMaior\b|\bBlocker\b|\bMajor\b", re.IGNORECASE)
NA_BECAUSE_RE = re.compile(r"\bN/?A\b.*\b(?:porque|because)\b", re.IGNORECASE)


def parse_args(argv):
    opts = {"path": None, "spec": None, "uat": False, "evidence": None}
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--spec" and i + 1 < len(argv):
            opts["spec"] = argv[i + 1]
            i += 2
        elif a == "--evidence-of-run" and i + 1 < len(argv):
            opts["evidence"] = argv[i + 1]
            i += 2
        elif a == "--uat":
            opts["uat"] = True
            i += 1
        elif opts["path"] is None and not a.startswith("--"):
            opts["path"] = a
            i += 1
        else:
            usage(__doc__)
    if opts["path"] is None:
        usage(__doc__)
    return opts


def spec_delta_ids(path):
    """IDs de requisito em ## ADDED / ## MODIFIED do delta (itens de lista)."""
    lines = read_lines(path)
    ids = set()
    for kind in ("ADDED", "MODIFIED"):
        sec = find_section(lines, (f"{kind} Requirements", kind))
        if not sec:
            continue
        for i in range(*sec):
            if re.match(r"^\s*[-*]\s+\*\*", lines[i]):
                m = REQ_ID.search(lines[i])
                if m:
                    ids.add(m.group(1))
    return ids


def check_verdict(rep, lines):
    """Retorna (verdict, block_reason). Registra HARD quando fora do enum."""
    verdict = None
    for i, l in enumerate(lines[:30]):
        m = VERDICT_RE.match(l)
        if not m:
            continue
        rest = m.group(2).strip()
        tokens = rest.split()
        head = tokens[0] if tokens else ""
        tail = " ".join(tokens[1:])
        # depois da palavra so emoji/pontuacao; letra, digito, '|' ou '/' e outra opcao
        if head not in VERDICTS or re.search(r"[A-Za-z0-9|/]", tail):
            rep.hard(f"Veredito fora do enum PASS|FAIL|BLOCKED: '{rest[:40]}'", i + 1)
            return None, None
        verdict = head
        break
    if verdict is None:
        rep.hard("linha '**Veredito:** PASS|FAIL|BLOCKED' ausente nas primeiras 30 linhas")
        return None, None
    reason = None
    for i, l in enumerate(lines):
        m = BLOCK_REASON_RE.match(l)
        if m:
            reason = m.group(2).strip()
            if verdict == "BLOCKED" and not reason:
                rep.hard("**Motivo do bloqueio:** vazio", i + 1)
            break
    if verdict == "BLOCKED" and reason is None:
        rep.hard("veredito BLOCKED exige linha '**Motivo do bloqueio:** <motivo>'")
    return verdict, reason


def check_conformance(rep, lines, spec_ids):
    """Retorna (negatives, rows_ok). negatives = lista de mensagens de sinal negativo."""
    negatives = []
    sec = find_section(lines, ("Conformidade à spec", "Conformidade a spec", "Spec conformance"))
    if not sec:
        rep.hard("secao ## Conformidade à spec ausente")
        return negatives
    rows = table_rows(lines, *sec)
    if not rows:
        rep.hard("tabela de conformidade vazia")
        return negatives
    seen = {}
    for i, c in rows:
        ln = i + 1
        if len(c) != 4:
            rep.hard(f"linha de conformidade com {len(c)} colunas; esperado 4 "
                     f"(Requisito | Resultado da spec | file:line | Resultado)", ln)
            continue
        m = REQ_ID.search(c[0])
        rid = m.group(1) if m else c[0].strip()
        if rid in seen:
            rep.hard(f"ID de requisito duplicado na tabela de conformidade: {rid} (ja em L{seen[rid]})", ln)
        else:
            seen[rid] = ln
        result = c[3]
        has_evidence = any(FILE_LINE.search(x) for x in c)
        if NEG_RESULT_RE.search(result):
            negatives.append(f"conformidade L{ln}: {rid} -> '{result.strip()[:30]}'")
        elif POS_RESULT_RE.search(result):
            if not has_evidence:
                rep.hard(f"requisito marcado PASS sem file:line: '{rid}'", ln)
        else:
            rep.hard(f"resultado de conformidade nao reconhecido (PASS/GAP/lacuna): '{result[:30]}'", ln)
    if spec_ids is not None:
        for rid in sorted(spec_ids - set(seen)):
            rep.hard(f"requisito {rid} do delta (ADDED/MODIFIED) ausente na tabela de conformidade")
    return negatives


def check_gate(rep, lines, evidence_path):
    """Retorna (negatives, total, command)."""
    negatives = []
    sec = find_section(lines, ("Gate Build", "Build gate", "Gate"))
    if not sec:
        rep.hard("secao ## Gate Build ausente")
        return negatives, None, None
    start, end = sec
    nums = {}
    exit_code = None
    command = None
    num_line = None
    for i in range(start, end):
        l = lines[i]
        for k, rx in GATE_NUM_RE.items():
            m = rx.search(l)
            if m and k not in nums:
                nums[k] = int(m.group(1))
                num_line = i
        m = GATE_EXIT_RE.search(l)
        if m and exit_code is None:
            exit_code = int(m.group(1))
        m = GATE_CMD_RE.search(l)
        if m and command is None:
            command = m.group(1).strip().strip("`").strip()
    if command is None:
        rep.hard("Gate Build sem 'Comando:'", start)
    missing = [k for k in ("total", "passed", "failed", "skipped") if k not in nums]
    if missing:
        rep.hard("Gate Build sem numeros: " + ", ".join(
            {"total": "Total", "passed": "Passou", "failed": "Falhou", "skipped": "Pulou"}[k]
            for k in missing), start)
        return negatives, None, command
    ln = num_line + 1
    if nums["failed"] > 0:
        negatives.append(f"gate L{ln}: Falhou {nums['failed']}")
    if exit_code is not None and exit_code != 0:
        negatives.append(f"gate L{ln}: exit {exit_code}")
    if nums["skipped"] > 0:
        justified = False
        for i in range(start, end):
            if SKIP_JUSTIFICATION_RE.match(lines[i]):
                justified = True
                break
        if not justified:
            m = GATE_NUM_RE["skipped"].search(lines[num_line])
            tail = lines[num_line][m.end():]
            parts = [p.strip() for p in re.split(r"[·|]", tail)]
            parts = [p for p in parts
                     if p and not re.match(r"(?:Contagem|Count|exit)\b", p, re.IGNORECASE)]
            justified = bool(parts)
        if not justified:
            rep.hard(f"Pulou {nums['skipped']} sem justificativa (texto apos os numeros ou linha 'Pulados:')", ln)
    if evidence_path is not None:
        if not os.path.exists(evidence_path):
            rep.hard(f"--evidence-of-run {evidence_path} nao encontrado")
        elif command:
            with open(evidence_path, encoding="utf-8", errors="replace") as f:
                log = f.read()
            if command not in log:
                rep.hard(f"--evidence-of-run nao contem o comando do Gate Build: '{command[:50]}'")
    return negatives, nums["total"], command


def check_sensor(rep, lines, tier):
    negatives = []
    sec = find_section(lines, ("Sensor de discriminação", "Sensor de discriminacao", "Discrimination sensor"))
    rows = table_rows(lines, *sec) if sec else []
    if not rows:
        if tier in ("large", "complex"):
            rep.hard(f"tier {tier}: sensor de discriminacao ausente ou sem mutacoes registradas")
        elif tier == "medium":
            rep.warn("tier medium: sem sensor de discriminacao - obrigatorio se ha risco nomeado")
        return negatives
    for i, c in rows:
        if c and SURVIVED_RE.search(c[-1]):
            negatives.append(f"sensor L{i + 1}: mutante sobreviveu ('{c[0][:30]}')")
    return negatives


def check_design(rep, lines, design_exists):
    negatives = []
    sec = find_section(lines, ("Aderência ao design", "Aderencia ao design", "Design adherence"))
    if not sec:
        rep.hard("secao ## Aderência ao design ausente (eixo 2)")
        return negatives
    rows = table_rows(lines, *sec)
    if not rows:
        body = " ".join(lines[sec[0]:sec[1]])
        if design_exists:
            rep.hard("design.md existe e a tabela de aderencia ao design esta vazia")
        elif not NA_BECAUSE_RE.search(body):
            rep.hard("sem design.md: aderencia ao design precisa de tabela ou 'N/A porque ...'")
        return negatives
    if design_exists and len(rows) < 4:
        rep.hard(f"design.md existe: tabela de aderencia com {len(rows)} itens; minimo 4")
    for i, c in rows:
        if len(c) < 2:
            continue
        status = c[1]
        obs = c[2].strip() if len(c) >= 3 else ""
        if ("⚠️" in status or "❌" in status) and not obs:
            rep.hard(f"item de aderencia com ⚠️/❌ sem observacao: '{c[0][:40]}'", i + 1)
        if "❌" in status:
            negatives.append(f"aderencia L{i + 1}: ❌ '{c[0][:30]}'")
    return negatives


def check_gaps(lines):
    negatives = []
    sec = find_section(lines, ("Gaps",))
    if not sec:
        return negatives
    for i in range(*sec):
        if NUMBERED_ITEM_RE.match(lines[i]):
            negatives.append(f"gaps L{i + 1}: '{lines[i].strip()[:40]}'")
    return negatives


def check_uat(rep, lines, required):
    negatives = []
    sec = find_section(lines, ("UAT",))
    items = []
    if sec:
        for i in range(*sec):
            s = lines[i].strip()
            if s and not s.startswith("<!--"):
                items.append((i, s))
    if required and not items:
        rep.hard("UAT obrigatorio (--uat ou flag uat) e secao ## UAT ausente ou vazia")
        return negatives
    for i, s in items:
        if UAT_NEG_RE.search(s):
            negatives.append(f"UAT L{i + 1}: '{s[:40]}'")
    return negatives


def main(argv):
    opts = parse_args(argv)
    path = opts["path"]
    lines = read_lines(path)
    rep = Report("lint_validation")

    fields, flags, mc_idx = parse_machine_comment(lines)
    if fields is None or fields["sdd"].lower() != "validation":
        rep.hard("primeira linha deve ser <!-- sdd: validation | change: <NNNN-slug> | tier: <tier> -->", 1)
        return rep.emit(path)
    if not fields.get("change"):
        rep.hard("comentario de maquina sem 'change: <NNNN-slug>'", mc_idx + 1)
    tier = fields.get("tier", "").lower()
    if tier not in TIERS:
        rep.hard("comentario de maquina sem 'tier: small|medium|large|complex' "
                 "(as regras proporcionais dependem dele)", mc_idx + 1)
        tier = None

    verdict, reason = check_verdict(rep, lines)

    spec_ids = None
    if opts["spec"]:
        if not os.path.exists(opts["spec"]):
            rep.warn(f"--spec {opts['spec']} nao encontrado; cobertura de requisitos nao verificada contra a spec")
        else:
            spec_ids = spec_delta_ids(opts["spec"])
    else:
        rep.warn("sem --spec: cobertura de requisitos nao verificada contra a spec")

    design_exists = os.path.exists(os.path.join(os.path.dirname(os.path.abspath(path)), "design.md"))
    uat_required = opts["uat"] or "uat" in (flags or set())

    negatives = []
    negatives += check_conformance(rep, lines, spec_ids)
    gate_neg, total, _ = check_gate(rep, lines, opts["evidence"])
    negatives += gate_neg
    negatives += check_sensor(rep, lines, tier)
    negatives += check_design(rep, lines, design_exists)
    negatives += check_gaps(lines)
    negatives += check_uat(rep, lines, uat_required)

    if verdict == "PASS":
        for n in negatives:
            rep.hard(f"veredito PASS com sinal negativo: {n}")
        if total == 0:
            rep.hard("veredito PASS com Gate Build Total 0: teste nao executado nao e evidencia")
    elif verdict == "FAIL" and not negatives:
        rep.hard("FAIL sem evidencia de falha: nenhum GAP, ❌, Falhou > 0, mutante sobrevivente ou gap listado")

    scan_placeholders(rep, lines, skip_first=mc_idx + 1)
    code = rep.emit(path)
    if verdict == "FAIL":
        print("lint_validation: veredito FAIL - a mudanca NAO esta pronta; roteie os gaps para tasks de correcao.")
        return 1
    if verdict == "BLOCKED":
        print(f"lint_validation: verificacao incompleta/bloqueada: {reason or '(motivo ausente)'} "
              "- o relatorio e entregavel, mas a mudanca nao fecha.")
        return 1
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
