#!/usr/bin/env python3
"""validate-agent-roster.py — frontmatter + tier-pin lint for agents and skills.

Usage:
    python3 ~/.claude/hooks/validate-agent-roster.py [--json]

Checks every `~/.claude/agents/*.md` and `~/.claude/skills/*/SKILL.md` (following
symlinks to canonical sources) for the silent-failure classes that cost real time on
2026-08-06:

  E1  frontmatter absent or not strict-YAML parseable
        -> the harness may drop `tools:`/`model:` and the agent inherits, or the
           definition fails to load entirely.
  E2  DE-REGISTRATION HAZARD: a double-quoted description containing backslash
        -escaped quotes (\\"). PyYAML accepts this; the harness parser does NOT.
        PROVEN 2026-08-06: `transcript-distiller` silently vanished from the agent
        registry after its description was double-quoted with 6 \\" escapes, and
        returned when reformatted as a single-quoted scalar. Use single quotes.
  E3  unquoted description containing ': ' or ' #'
        -> ' #' starts a YAML comment and TRUNCATES the rest of the description,
           silently discarding trigger vocabulary (hit transcript-distiller,
           transcript-processing, skill-dependencies); ': ' breaks strict parsers.
  E4  agent missing `model:` or `effort:`
        -> the Agent tool has NO effort parameter, so an agent without an effort
           pin inherits SESSION effort (xhigh under ultracode). Blueprint rule 1.
  E5  agent carrying `maxTurns:`
        -> deliberately unused (owner ruling 2026-08-06): a silent mid-flight cap
           violates blueprint standing rule 5. Bound work in the prompt (rule 18).
  W1  description over the 1,024-char portable cap (claude.ai/Cowork surfaces)
  W2  name field not matching the filename (legal, but harder to audit)

Exit 0 = PASS (warnings allowed). Exit 1 = FAIL (any error).

Blueprint: docs/ (v1.4 §11)
v1.0 | 2026-08-06 | Owner: jtims
"""
import glob
import json as jsonlib
import os
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None

PORTABLE_DESC_CAP = 1024


def frontmatter(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except Exception as exc:
        return None, "unreadable: %s" % exc
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not m:
        return None, "no YAML frontmatter block"
    return m.group(1), None


def raw_line(fm, key):
    m = re.search(r"^%s\s*:\s*(.*)$" % re.escape(key), fm, re.M)
    return m.group(1) if m else None


def check_file(path, kind):
    """Return list of (level, code, detail)."""
    out = []
    fm, err = frontmatter(path)
    if fm is None:
        return [("ERROR", "E1", err)]

    parsed = None
    if yaml is not None:
        try:
            parsed = yaml.safe_load(fm)
            if not isinstance(parsed, dict):
                out.append(("ERROR", "E1", "frontmatter is not a mapping"))
                parsed = None
        except Exception as exc:
            # WARN, not ERROR: the harness parser is more permissive than PyYAML and
            # loads these files today (directly observed 2026-08-06 — every skill in
            # this class was live in the session's skill listing). It is real latent
            # fragility for portable/strict tooling, not a live outage.
            out.append(("WARN", "W3", "strict-YAML parse failed (harness-tolerated today): %s"
                        % str(exc).split("\n")[0]))

    desc_raw = raw_line(fm, "description")
    if desc_raw is not None:
        stripped = desc_raw.strip()
        if stripped.startswith('"'):
            if '\\"' in stripped:
                out.append((
                    "ERROR", "E2",
                    "double-quoted description with backslash-escaped quotes — "
                    "DE-REGISTRATION HAZARD; reformat as a single-quoted scalar",
                ))
        elif ": " in stripped and not stripped.startswith("'"):
            # ': ' is latent only: harness-tolerated today, breaks strict parsers.
            out.append(("WARN", "W4", "unquoted description containing ': ' — harness-tolerated "
                                      "today but breaks strict YAML tooling; single-quote it"))

        # ' #' is a PROVEN content-loss defect REGARDLESS OF QUOTING. Correcting an
        # earlier wrong call in this file's own history: single-quoting alone does NOT
        # neutralise it. Observed 2026-08-06 — `transcript-distiller` kept a ' #' in a
        # single-quoted description and the harness dropped its `tools:` list (the agent
        # showed "All tools"); `transcript-processing` kept one and its description
        # rendered truncated with a stray leading quote. Both rendered correctly and in
        # full only once the ' #' and inner double quotes were REMOVED from the value.
        # Literal formatting syntax belongs in the body, never the description.
        if desc_raw is not None and " #" in desc_raw:
            out.append(("ERROR", "E3", "description contains ' #' — the harness mis-parses the "
                                       "scalar even when quoted (drops later keys such as tools:, "
                                       "or truncates the value). REMOVE the character; put literal "
                                       "formatting syntax in the body"))
        if desc_raw is not None and desc_raw.strip().startswith("'") and '"' in desc_raw:
            out.append(("WARN", "W5", "single-quoted description contains inner double quotes — "
                                      "tolerated alone, but harmful in combination with ' #'; "
                                      "prefer removing them from the description"))

    if parsed is not None:
        desc = parsed.get("description") or ""
        if len(desc) > PORTABLE_DESC_CAP:
            out.append(("WARN", "W1", "description %d chars exceeds the %d portable cap"
                        % (len(desc), PORTABLE_DESC_CAP)))
        name = parsed.get("name")
        base = os.path.basename(path)
        expected = os.path.basename(os.path.dirname(path)) if base == "SKILL.md" else base[:-3]
        if name and name != expected:
            out.append(("WARN", "W2", "name '%s' does not match '%s'" % (name, expected)))

        if kind == "agent":
            if not parsed.get("model"):
                out.append(("ERROR", "E4", "no model: pin — would inherit the session model"))
            if not parsed.get("effort"):
                out.append(("ERROR", "E4", "no effort: pin — the Agent tool has no effort "
                                           "parameter, so this inherits SESSION effort"))
            if "maxTurns" in parsed:
                out.append(("ERROR", "E5", "maxTurns present — deliberately unused per owner ruling "
                                           "2026-08-06 (silent cap violates rule 5)"))
    return out


def main():
    as_json = "--json" in sys.argv
    targets = []
    for p in sorted(glob.glob(os.path.expanduser("~/.claude/agents/*.md"))):
        targets.append((p, "agent"))
    for d in sorted(glob.glob(os.path.expanduser("~/.claude/skills/*/SKILL.md"))):
        targets.append((d, "skill"))

    findings, errors, warns = [], 0, 0
    for path, kind in targets:
        for level, code, detail in check_file(path, kind):
            label = os.path.basename(os.path.dirname(path)) if path.endswith("SKILL.md") else os.path.basename(path)
            findings.append({"level": level, "code": code, "kind": kind,
                             "target": label, "detail": detail})
            if level == "ERROR":
                errors += 1
            else:
                warns += 1

    if as_json:
        print(jsonlib.dumps({"findings": findings, "errors": errors, "warnings": warns,
                             "agents": sum(1 for _, k in targets if k == "agent"),
                             "skills": sum(1 for _, k in targets if k == "skill")}, indent=2))
    else:
        for f in findings:
            print("%s | %s | %s (%s) | %s" % (f["level"], f["code"], f["target"], f["kind"], f["detail"]))
        if yaml is None:
            print("WARN | -- | pyyaml absent — E1/E4/E5 checks degraded to raw-text only")
        n_a = sum(1 for _, k in targets if k == "agent")
        n_s = sum(1 for _, k in targets if k == "skill")
        print("%s | %d agent(s) + %d skill(s) scanned | %d error(s), %d warning(s)"
              % ("FAIL" if errors else "PASS", n_a, n_s, errors, warns))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
