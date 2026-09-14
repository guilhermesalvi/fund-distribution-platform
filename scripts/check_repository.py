"""Check solution inventory, local Markdown links and Claude Code instruction layout.

Run with Python 3.10+ from any directory. Requires Git, no Python packages.
Includes non-ignored untracked files so the check also works before staging.
"""

from collections import Counter
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOLUTION = "FundDistributionPlatform.slnx"
INSTRUCTION_LIMIT = 32 * 1024


def check_task_gates(text):
    """Check executable gate references in tasks and complete Markdown examples."""
    section = re.search(r"^## Gate Commands\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not section:
        return []
    findings = []
    commands = {}
    for line in section[1].splitlines():
        row = re.fullmatch(r"\|\s*([^|]+?)\s*\|[^|]*\|\s*(.*?)\s*\|", line)
        if not row or row[1] == "Gate" or re.fullmatch(r"[-: ]+", row[1]):
            continue
        gate, command = row[1].strip(), row[2].strip().strip("`")
        if gate not in {"quick", "full", "build", "Mutation"}:
            findings.append(f"unknown gate {gate}")
        if gate in commands:
            findings.append(f"duplicate gate {gate}")
        if not command:
            findings.append(f"empty command for {gate}")
        commands[gate] = command
    for task in re.finditer(r"^### (T(?:C)?\d+):[^\n]*\n(.*?)(?=^### |^## |\Z)", text, re.M | re.S):
        gate = re.search(r"^- \*\*Gate:\*\* (\w+)\s*$", task[2], re.M)
        if not gate:
            findings.append(f"{task[1]}: missing Gate field")
            continue
        value = gate[1]
        if value not in {"quick", "full", "build"}:
            findings.append(f"{task[1]}: invalid task gate {value}")
        if value not in commands:
            findings.append(f"{task[1]}: undeclared gate {value}")
            continue
        done = re.search(r"^- \*\*Done when:\*\*(.*?)(?=^- \*\*|\Z)", task[2], re.M | re.S)
        if not done or f"`{commands[value]}`" not in done[1]:
            findings.append(f"{task[1]}: Done when does not contain its gate command")
    return findings


def check():
    inventory = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
    ).decode("utf-8").split("\0")
    files = {path for path in inventory if path and (ROOT / path).is_file()}
    findings = []
    projects = {path for path in files if path.endswith(".csproj")}
    project_dirs = {str(Path(path).parent).replace("\\", "/") for path in projects}
    expected_files = {
        path for path in files
        if path != SOLUTION and path not in projects
        and not any(path.startswith(directory + "/") for directory in project_dirs)
    }
    solution = ET.parse(ROOT / SOLUTION).getroot()
    entries = [(kind, element.attrib["Path"], folder.attrib["Name"])
               for folder in solution.findall("Folder")
               for kind in ("File", "Project") for element in folder.findall(kind)]
    for kind, expected in (("File", expected_files), ("Project", projects)):
        actual = {path for tag, path, _ in entries if tag == kind}
        findings.extend(f"solution: missing {kind} {path}" for path in sorted(expected - actual))
        findings.extend(f"solution: unexpected {kind} {path}" for path in sorted(actual - expected))
    for path, count in Counter(path for _, path, _ in entries).items():
        if count > 1:
            findings.append(f"solution: duplicate entry {path}")
    required_folders = set()
    for kind, path, folder in entries:
        parent = Path(path).parent
        if kind == "Project":
            parent = parent.parent
        expected_folder = "/SolutionItems/" if parent == Path(".") else f"/{parent.as_posix()}/"
        if folder != expected_folder:
            findings.append(f"solution: {path} belongs in {expected_folder}, found {folder}")
        required_folders.add(expected_folder)
        while parent != Path("."):
            required_folders.add(f"/{parent.as_posix()}/")
            parent = parent.parent
    folders = [element.attrib["Name"] for element in solution.findall("Folder")]
    if folders != sorted(set(folders), key=str.casefold):
        findings.append("solution: folders must be unique and alphabetically ordered")
    for folder in sorted(required_folders - set(folders)):
        findings.append(f"solution: missing parent folder {folder}")
    for folder in solution.findall("Folder"):
        paths = [element.attrib["Path"] for element in folder]
        if paths != sorted(paths, key=str.casefold):
            findings.append(f"solution: entries out of order in {folder.attrib['Name']}")

    for path in sorted(files):
        if not path.endswith(".md"):
            continue
        text = (ROOT / path).read_text(encoding="utf-8")
        findings.extend(f"gates: {path}: {finding}" for finding in check_task_gates(text))
        # Examples intentionally reference hypothetical files; do not treat them as links.
        prose = re.sub(r"^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", text, flags=re.M | re.S)
        for href in re.findall(r"\]\(([^)\s]+)\)", prose):
            parsed = urlsplit(href.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target_path = unquote(parsed.path)
            target = (ROOT / target_path.lstrip("/")) if target_path.startswith("/") else (ROOT / path).parent / target_path
            if not target.exists():
                findings.append(f"links: {path} -> {href} does not exist")

    for path in sorted(path for path in files if path.endswith("/SKILL.md")):
        skill = ROOT / path
        text = skill.read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.S)
        if not frontmatter:
            findings.append(f"skills: missing frontmatter in {path}")
            continue
        name = re.search(r"^name: ([a-z0-9]+(?:-[a-z0-9]+)*)$", frontmatter[1], flags=re.M)
        if not name or name[1] != skill.parent.name or len(name[1]) > 64:
            findings.append(f"skills: invalid name or directory mismatch in {path}")
        if not re.search(r"^description: \S.+$", frontmatter[1], flags=re.M):
            findings.append(f"skills: missing description in {path}")

    # A rule loads at launch when it has no frontmatter, or when a file matching `paths` enters the task.
    rules = sorted(path for path in files if path.startswith(".claude/rules/") and path.endswith(".md"))
    for path in rules:
        text = (ROOT / path).read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.S)
        if frontmatter and not re.fullmatch(r"paths:\n(?:  - \"[^\"\n]+\"\n)+", frontmatter[1] + "\n"):
            findings.append(f"rules: invalid paths frontmatter in {path}")

    # Budget for the instructions one session can load: the CLAUDE.md chain from the root down to
    # each instruction-bearing or documented start directory, plus every rule, since a task may
    # touch files matching all patterns.
    rules_size = sum((ROOT / path).stat().st_size + 2 for path in rules)
    directories = {ROOT, ROOT / "src/Offering"}
    directories.update((ROOT / path).parent for path in files if Path(path).name == "CLAUDE.md")
    for directory in sorted(directories):
        chain = [ROOT] + [parent for parent in reversed(directory.parents) if ROOT in parent.parents]
        if directory != ROOT:
            chain.append(directory)
        size = rules_size + sum((parent / "CLAUDE.md").stat().st_size + 2 for parent in chain if (parent / "CLAUDE.md").is_file())
        if size > INSTRUCTION_LIMIT:
            findings.append(f"instructions: {directory.relative_to(ROOT)} uses {size} bytes, limit is {INSTRUCTION_LIMIT}")

    for finding in findings:
        print(finding)
    if not findings:
        print(f"Repository checks passed: {len(files)} files, {len(projects)} projects.")
    return bool(findings)


if __name__ == "__main__":
    try:
        sys.exit(check())
    except (OSError, subprocess.CalledProcessError, ET.ParseError) as error:
        print(f"Repository check failed: {error}", file=sys.stderr)
        sys.exit(1)
