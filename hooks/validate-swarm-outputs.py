#!/usr/bin/env python3
"""validate-swarm-outputs.py — deterministic structure lint for research-swarm projects.

Usage:
    python3 ~/.claude/hooks/validate-swarm-outputs.py <project_dir | out_dir>

Accepts either a project folder (contains Research/) or a Research out_dir.
Checks:
  1. Required project files: Prompt.md, a worklog (either WORKLOG_*.md or the
     Working-Projects-vault convention WORKLOG.md), RESUME-HERE_*.md, Research/
     (project mode only).
  2. Research/raw/ exists (once any research has run; warning if absent).
  3. Frontmatter: every swarm-written .md opens with a YAML block containing the
     7 required keys: title, project, type, version, date, run_id, status.
     Exempt: Prompt.md (the owner's verbatim ask may predate the standard) and any file
     listed in .frontmatter-exempt (one relative path per line, project root).
  4. Naming: top-level deliverables match [Name]_YYYY-MM-DD(_vN).(md|html|json);
     Research/raw/** and Research/Workflow-Scripts/** are exempt from date-naming
     (run artifacts are slug-named) but .md files there still need frontmatter.

Exit 0 = PASS (warnings allowed). Exit 1 = FAIL (any error). Output is a
structured report, one finding per line: LEVEL | path | detail.

Blueprint rule 11: docs/
v1.1 | 2026-08-27 | Owner: jtims

Changelog
  v1.1 (2026-08-27): check 1 now accepts `WORKLOG.md` as well as `WORKLOG_*.md`. The
    framework's own home and every vault project use `WORKLOG.md`,
    which `close-session.sh:112` hard-requires by literal path, so the previous
    `WORKLOG_*.md`-only rule ERRORed on every real project including this framework's
    own folder (control test 2026-08-27). Owner-approved. Backup: .bak-2026-08-27.
  v1.0 (2026-07-27): initial.
"""
import re
import sys
from pathlib import Path

REQUIRED_KEYS = {"title", "project", "type", "version", "date", "run_id", "status"}
DATED = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]*(_[A-Za-z0-9-]+)*_\d{4}-\d{2}-\d{2}(_v\d+)?\.(md|html|json)$")
EXEMPT_DEFAULT = {"Prompt.md"}


def frontmatter_keys(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    keys = set()
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:", line)
        if m:
            keys.add(m.group(1))
    return keys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate-swarm-outputs.py <project_dir | out_dir>")
        return 1
    root = Path(sys.argv[1]).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR | {root} | not a directory")
        return 1

    findings = []  # (level, path, detail)
    project_mode = (root / "Research").is_dir() or not root.name == "Research"
    project_root = root if (root / "Research").is_dir() else (root.parent if root.name == "Research" else root)
    research = project_root / "Research"

    # 1. required project files
    if project_root == root or research.exists():
        if not (project_root / "Prompt.md").exists():
            findings.append(("ERROR", "Prompt.md", "missing — the verbatim contract file is required"))
        if not list(project_root.glob("WORKLOG_*.md")) and not (project_root / "WORKLOG.md").exists():
            findings.append(("ERROR", "WORKLOG_*.md | WORKLOG.md", "missing — living cross-session record is required"))
        if not list(project_root.glob("RESUME-HERE_*.md")):
            findings.append(("WARN", "RESUME-HERE_*.md", "missing — required before first session handoff"))
        if not research.is_dir():
            findings.append(("ERROR", "Research/", "missing"))

    # 2. raw dir
    if research.is_dir() and not (research / "raw").is_dir():
        findings.append(("WARN", "Research/raw/", "absent — expected once a run has executed"))

    # exemptions
    exempt = set(EXEMPT_DEFAULT)
    exfile = project_root / ".frontmatter-exempt"
    if exfile.exists():
        exempt |= {l.strip() for l in exfile.read_text().splitlines() if l.strip()}

    # 3 + 4. per-file checks
    for p in sorted(project_root.rglob("*")):
        if not p.is_file() or p.name.startswith("."):
            continue
        rel = p.relative_to(project_root).as_posix()
        in_exempt_tree = rel.startswith("Research/raw/") or rel.startswith("Research/Workflow-Scripts/") or "/Attachments/" in ("/" + rel) or rel.startswith("Attachments/") or rel.startswith("_archive/")
        # naming (top-level + Research/ deliverables only)
        if p.suffix in (".md", ".html", ".json") and not in_exempt_tree and rel not in exempt:
            if not DATED.match(p.name) and not p.name.startswith("WORKLOG_"):
                findings.append(("WARN", rel, "name does not match [Name]_YYYY-MM-DD(_vN).ext"))
        # frontmatter (all swarm-written .md, including raw/)
        if p.suffix == ".md" and rel not in exempt and not rel.startswith("_archive/") and not rel.startswith("Attachments/"):
            keys = frontmatter_keys(p)
            if keys is None:
                findings.append(("ERROR", rel, "no YAML frontmatter block"))
            else:
                missing = REQUIRED_KEYS - keys
                if missing:
                    findings.append(("ERROR", rel, f"frontmatter missing keys: {sorted(missing)}"))

    errors = [f for f in findings if f[0] == "ERROR"]
    warns = [f for f in findings if f[0] == "WARN"]
    for lvl, path, detail in findings:
        print(f"{lvl} | {path} | {detail}")
    print(f"{'FAIL' if errors else 'PASS'} | {project_root} | {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
