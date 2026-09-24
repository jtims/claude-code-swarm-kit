#!/usr/bin/env python3
"""workflow-model-pin-gate.py — PreToolUse gate on the Workflow tool.

Blocks (exit 2) any dynamic-workflow script containing agent() calls that lack
an explicit `model:` pin in their options object. Rationale: in a Fable 5
session every unpinned agent inherits Fable and burns the scarce Fable budget
(root cause of the 2026-07-26 spend-cap event; see blueprint).

Blueprint: docs/
Tier matrix: helpers=haiku/low . workers=sonnet/high . judges=claude-opus-5-5/xhigh .
final audit=claude-fable-5-1/xhigh . orchestration=driving session.

Design: FAIL-OPEN. Any internal error, unreadable scriptPath, or named-workflow
invocation (no inline script) allows the call. The gate lints only what it can
read. Missing `effort:` or `schema:` is a warning, not a block.

v1.2 | 2026-09-23 | Owner: jtims
Changelog: v1.2 - tier-matrix text in this docstring and in the block message updated
per owner ruling 2026-09-23; no logic change. v1.1 — added schema: warning (structured-outputs nudge, P4 of the
owner-approved additions); topology wording updated to A'. v1.0 — initial.
"""
import json
import re
import sys


def sanitize(src: str) -> str:
    """Blank out comments and string/template literals, preserving offsets and
    newlines, so parens/keywords inside them don't confuse the scanner."""
    res = list(src)
    i, n = 0, len(src)

    def blank(a: int, b: int) -> None:
        for k in range(a, min(b, n)):
            if res[k] != "\n":
                res[k] = " "

    while i < n:
        c = src[i]
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            j = n if j == -1 else j
            blank(i, j)
            i = j
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            blank(i, j)
            i = j
        elif c in "\"'`":
            q, j = c, i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == q:
                    break
                j += 1
            blank(i + 1, min(j, n))
            i = j + 1
        else:
            i += 1
    return "".join(res)


def check(script: str):
    """Return (missing_model, missing_effort, missing_schema) line lists."""
    s = sanitize(script)
    missing_model, missing_effort, missing_schema = [], [], []
    for m in re.finditer(r"(?<![\w$.])agent\s*\(", s):
        start = m.end() - 1  # index of '('
        depth, j = 0, start
        while j < len(s):
            if s[j] == "(":
                depth += 1
            elif s[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        call = s[start : j + 1]
        line = s.count("\n", 0, m.start()) + 1
        if not re.search(r"\bmodel\s*:", call):
            missing_model.append(line)
        if not re.search(r"\beffort\s*:", call):
            missing_effort.append(line)
        if not re.search(r"\bschema\s*:", call):
            missing_schema.append(line)
    return missing_model, missing_effort, missing_schema


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open
    if payload.get("tool_name") != "Workflow":
        return 0
    ti = payload.get("tool_input") or {}
    script = ti.get("script")
    if not script and ti.get("scriptPath"):
        try:
            with open(ti["scriptPath"], "r", encoding="utf-8") as f:
                script = f.read()
        except Exception:
            return 0  # fail-open
    if not script:
        return 0  # named/bundled workflow invocation — pre-vetted, allow
    try:
        mm, me, ms = check(script)
    except Exception:
        return 0  # fail-open
    if mm:
        sys.stderr.write(
            "BLOCKED by workflow-model-pin-gate: agent() call(s) without an explicit "
            f"model: pin at line(s) {mm}. Every agent() must carry opts.model "
            "('haiku' | 'sonnet' | 'claude-opus-5-5' | 'claude-fable-5-1' | full model ID) — unpinned "
            "agents inherit the session model, and in a Fable 5 session that burns the "
            "Fable budget (tier matrix: helpers=haiku/low, workers=sonnet/high, "
            "judges=claude-opus-5-5/xhigh, final audit=claude-fable-5-1/xhigh). "
            + (f"Also missing effort: at line(s) {me} (pin it for determinism). " if me else "")
            + (f"Also missing schema: at line(s) {ms} (prefer typed structured returns). " if ms else "")
            + "Add explicit pins — inheriting deliberately still requires writing the "
            "session tier out as a literal — then retry. "
            "Gate: ~/.claude/hooks/workflow-model-pin-gate.py"
        )
        return 2
    warnings = []
    if me:
        warnings.append(
            f"agent() at line(s) {me} missing effort: — will inherit session effort (ultracode = xhigh); pin per tier."
        )
    if ms:
        warnings.append(
            f"agent() at line(s) {ms} missing schema: — untyped free-text return; prefer a JSON schema for structured, validated output."
        )
    if warnings:
        sys.stderr.write("workflow-model-pin-gate notes (allowed): " + " ".join(warnings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
