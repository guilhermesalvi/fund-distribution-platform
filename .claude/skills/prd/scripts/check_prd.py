"""Form check for a folder of PRDs (workflow.md, Checar, items 1 to 9).

Usage: python check_prd.py [<prd folder>]   (default: docs/prd)

Prints one line per finding and exits 1 when there is any. Item 10 (literal
copies from discovery material) and the visual rendering of Mermaid blocks are
not covered here and remain a manual read.

The structure it reads is fixed in English (conventions.md, Idioma): headings,
header labels, the prefix line, tags and form labels. Prose is not read, so it
can be in any language. Requirement prefixes are the ones each PRD declares in
its `Requirement prefix:` line; nothing about the repository is hard-coded.
"""
import glob
import io
import os
import re
import sys

SECTIONS = [
    "Executive Summary", "Strategic Alignment", "Context and Problem", "Target User / JTBD",
    "Opportunity / Hypothesis", "Proposed Solution", "Domain Glossary", "Functional Requirements",
    "Domain Events", "Non-functional Requirements", "Regulatory Considerations", "Non-goals",
    "Declared Trade-offs", "Success Metrics", "Acceptance Criteria", "Dependencies and Risks",
    "Open Questions", "Weakest Point", "References",
]
MANDATORY = ["Executive Summary", "Context and Problem", "Target User / JTBD", "Proposed Solution", "Functional Requirements"]
SECTIONS_0000 = ["Purpose", "Contexts", "Event Catalog", "Flows Between Contexts", "Terms per Context", "Decisions Delegated to ADR"]
HEADER_LABELS = ("Originating Context", "Module", "Area")
TAGS = ("ASSUMPTION", "GAP")
EMPTY = re.compile(r"(Nenhuma\.|Nenhum\.|None\.|N/A\.?)")
PREFIX_LINE = re.compile(r"^Requirement prefix: `([A-Z][A-Z0-9]*)`\.(.*)$", re.M)
OVERVIEW = "<!-- prd: overview -->\n"


def section(text, name):
    """Return the body of a `## name` section, or "" when absent."""
    m = re.search(r"^## " + re.escape(name) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def without_mermaid(text):
    return re.sub(r"```mermaid\n.*?```", "", text, flags=re.S)


def check(folder):
    files = sorted(glob.glob(os.path.join(folder, "*.md")))
    texts = {os.path.basename(f): io.open(f, encoding="utf-8").read() for f in files}
    everything = "\n".join(texts.values())
    findings = []

    # Prefixes come from the prefix lines; the id patterns derive from them.
    prefixes = sorted(set(m.group(1) for m in PREFIX_LINE.finditer(everything)))
    prefix_rx = "(?:" + "|".join(prefixes) + ")" if prefixes else "(?!x)x"
    id_rx = prefix_rx + r"-(?:NFR-)?\d\d"

    # 1. Numbering: unique NNNN per folder.
    numbers = [n[:4] for n in texts]
    for n in set(numbers):
        if numbers.count(n) > 1:
            findings.append(f"numbering: {n} used by more than one file")

    # 4. IDs: defined once, FR with MoSCoW, NFR without, citations resolve.
    defined = {}
    for m in re.finditer(r"\*\*(" + id_rx + r")(?: \((Must|Should|Could|Won't)\))?\*\*", everything):
        defined.setdefault(m.group(1), 0)
        defined[m.group(1)] += 1
    for name, count in defined.items():
        if count > 1:
            findings.append(f"ids: {name} defined {count} times")
    for m in re.finditer(r"\*\*(" + prefix_rx + r"-\d\d)\*\*", everything):
        findings.append(f"ids: {m.group(1)} without MoSCoW priority")
    for m in re.finditer(r"\*\*(" + prefix_rx + r"-NFR-\d\d) \(", everything):
        findings.append(f"ids: {m.group(1)} carries a MoSCoW priority")

    for name, text in texts.items():
        is_overview = text.startswith(OVERVIEW)
        cited = set(re.findall(r"\b(" + id_rx + r")\b", text))
        for c in sorted(cited - set(defined)):
            findings.append(f"{name}: citation {c} has no definition in the folder")
        for m in re.finditer(r"(?<![A-Z0-9-])\b(FR|NFR)-\d\d\b", text):
            findings.append(f"{name}: unprefixed id {m.group(0)}")
        for m in re.finditer(r"(?<![A-Za-z0-9-])([A-Z][A-Z0-9]+)-(?:NFR-)?\d\d\b", text):
            if m.group(1) not in prefixes and m.group(1) not in ("FR", "NFR"):
                findings.append(f"{name}: id with an undeclared prefix: {m.group(0)}")

        # 6. Local links resolve.
        for m in re.finditer(r"\]\(([^)]+)\)", text):
            href = m.group(1).split("#")[0]
            if href.startswith("http"):
                continue
            if not os.path.exists(os.path.join(folder, href)):
                findings.append(f"{name}: local link does not resolve: {href}")

        # 3. Sections: closed table, order, mandatory, nothing empty.
        headings = re.findall(r"^## (.+)$", text, re.M)
        table = SECTIONS_0000 if is_overview else SECTIONS
        positions = []
        for h in headings:
            if h not in table:
                findings.append(f"{name}: section outside the table: {h}")
            else:
                positions.append(table.index(h))
            body = section(text, h).strip()
            if not body or EMPTY.fullmatch(body):
                findings.append(f"{name}: empty section: {h}")
        if positions != sorted(positions):
            findings.append(f"{name}: sections out of table order")

        # 9. Tags and placeholders (Mermaid node labels are not brackets of prose).
        prose = without_mermaid(text)
        for m in re.finditer(r"\[([^\]]+)\]", prose):
            inner = m.group(1)
            if inner in TAGS or prose[m.end():m.end() + 1] == "(":
                continue  # tag, or markdown link text
            findings.append(f"{name}: unexpected bracket [{inner}]")
        if re.search(r"\bTBD\b|\bTODO\b", text):
            findings.append(f"{name}: TBD/TODO placeholder")

        # 8. Diagrams: closed fences, declared type, reserved words as aliases.
        if text.count("```") % 2:
            findings.append(f"{name}: unclosed code fence")
        for m in re.finditer(r"```mermaid\n(.*?)```", text, re.S):
            block = m.group(1).strip()
            kind = block.splitlines()[0].split()[0] if block else ""
            if kind not in ("stateDiagram-v2", "flowchart", "sequenceDiagram"):
                findings.append(f"{name}: mermaid block without a known diagram type ({kind})")
            if re.search(r"^\s*participant (end|off)\b|^\s*(end|off)\s*(-->|\[)", block, re.M | re.I):
                findings.append(f"{name}: reserved word used as mermaid alias")
            for line in block.splitlines()[1:]:
                if ("-->" in line or "->>" in line) and (":" in line or "|" in line) and not re.search(prefix_rx + r"-\d\d", line):
                    findings.append(f"{name}: mermaid label without id: {line.strip()[:60]}")
            if kind == "stateDiagram-v2" and "| Identifier |" not in text[m.end():m.end() + 400]:
                findings.append(f"{name}: stateDiagram-v2 without the identifier table beside it")

        if is_overview:
            # 7. PRD 0000: marker, number, no requirement definition.
            if not name.startswith("0000-"):
                findings.append(f"{name}: overview marker on a file that is not 0000")
            if re.search(r"\*\*" + id_rx + r"\b", text):
                findings.append(f"{name}: PRD 0000 defines a requirement")
            if not re.search(r"^\| \*\*Scope\*\* \| .+ \|$", text, re.M):
                findings.append(f"{name}: PRD 0000 header table missing or without the Scope label")
            continue

        # 2. Header: title, one-field table, prefix line pointing to 0000.
        if not text.startswith("# "):
            findings.append(f"{name}: first line is not the title")
        if not re.search(r"^\| \*\*(" + "|".join(HEADER_LABELS) + r")\*\* \| .+ \|$", text, re.M):
            findings.append(f"{name}: header table missing or with an unexpected label")
        has_0000 = any(n.startswith("0000-") for n in texts)
        prefix_line = PREFIX_LINE.search(text)
        if not prefix_line:
            findings.append(f"{name}: prefix line missing")
        elif has_0000 and "0000-" not in prefix_line.group(2):
            findings.append(f"{name}: prefix line does not point to PRD 0000")
        if prefix_line:
            own = prefix_line.group(1)
            for m in re.finditer(r"\*\*(" + prefix_rx + r")-(?:NFR-)?\d\d", text):
                if m.group(1) != own:
                    findings.append(f"{name}: defines an id with a foreign prefix: {m.group(0)[2:]}")
                    break
        for h in MANDATORY:
            if h not in headings:
                findings.append(f"{name}: mandatory section missing: {h}")
        if "Weakest Point" in headings and headings[-2:] != ["Weakest Point", "References"]:
            findings.append(f"{name}: Weakest Point must be followed only by References")

        # 5. Forms per section.
        for line in section(text, "Declared Trade-offs").splitlines():
            if line.startswith("- ") and not ("*Cost:*" in line and "*Reason:*" in line):
                findings.append(f"{name}: trade-off without Cost/Reason: {line[2:50]}")
        metrics = section(text, "Success Metrics")
        if metrics and "Guardrail" not in metrics:
            findings.append(f"{name}: Success Metrics without a guardrail line")
        for line in section(text, "Regulatory Considerations").splitlines():
            if not line.startswith("- ") or line.startswith("- [GAP]"):
                continue  # a norm not identified is a [GAP] bullet without id
            if "→" not in line:
                findings.append(f"{name}: regulatory line without → id: {line[2:50]}")
                continue
            after = line.split("→", 1)[1].strip()
            note = re.sub(r"^[^.]*\.\s*", "", after, count=1)
            if note and len(note.split()) > 20:
                findings.append(f"{name}: regulatory note over 20 words: {note[:50]}")
        open_questions = section(text, "Open Questions")
        for m in re.finditer(r"^- (.*)$", open_questions, re.M):
            if "if false" in m.group(1) and not m.group(1).startswith("**"):
                findings.append(f"{name}: 'if false' premise not in bold")
        for h in headings:
            if h != "Open Questions" and "if false" in section(text, h):
                findings.append(f"{name}: 'if false' premise outside Open Questions ({h})")
        for m in re.finditer(r"^- \*\*Given\*\*.*$", text, re.M):
            if not re.search(r"\(" + prefix_rx + r"-", m.group(0)):
                findings.append(f"{name}: Given/When/Then without an id: {m.group(0)[:50]}")
        header = re.search(r"\| \*\*Originating Context\*\* \| [^;|]+; affects ([^|]+) \|", text)
        if header:
            deps = section(text, "Dependencies and Risks")
            for ctx in re.split(r",| and ", header.group(1)):
                ctx = ctx.strip()
                if ctx and not re.search(r"^\| " + re.escape(ctx) + r" \|", deps, re.M):
                    findings.append(f"{name}: affected context without a row in Dependencies and Risks: {ctx}")

    # 7. PRD 0000 exists when there are two or more prefixes; each PRD links it (checked above).
    if len(prefixes) >= 2 and not any(n.startswith("0000-") for n in texts):
        findings.append("folder: two or more prefixes without a PRD 0000")

    # 9. Prose paragraph repeated across PRDs.
    seen = {}
    for name, text in texts.items():
        for p in text.split("\n\n"):
            p = p.strip()
            if len(p) > 120 and not p.startswith(("|", "-", "```", "#")):
                seen.setdefault(p, []).append(name)
    for p, names in seen.items():
        if len(names) > 1:
            findings.append(f"paragraph repeated in {', '.join(names)}: {p[:50]}")
    return findings


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.join("docs", "prd")
    if not os.path.isdir(target):
        print(f"not a folder: {target}")
        sys.exit(2)
    result = check(target)
    print("\n".join(result) if result else f"no findings in {target}")
    sys.exit(1 if result else 0)
