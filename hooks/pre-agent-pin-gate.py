#!/usr/bin/env python3
"""pre-agent-pin-gate.py — PreToolUse gate on the Agent tool.

Companion to workflow-model-pin-gate.py, which covers ONLY the Workflow tool.
That gate returns 0 for every other tool, so before this file existed every
interactive / nested / skill-forked subagent spawn was ungated: an agent whose
definition omits `model:` (or sets `inherit`) silently runs on the SESSION model.
In a Fable 5 ultracode session that is the exact inheritance failure the
Fable5-UC blueprint was built to close, arriving through the other door.

WHAT IT BLOCKS (exit 2)
  1. A spawn whose effective model resolves to "inherit the session model":
     no per-invocation `model`, and the named agent's definition has no usable
     `model:` pin (missing, empty, or literally `inherit`).
  2. A `fork` spawn requested by Claude. A fork ALWAYS inherits the driver model
     and receives the parent's full tool pool (docs: sub-agents#fork), so it
     cannot be pinned at all. the owner's own `/subtask` does NOT route through the
     Agent tool and is therefore unaffected.

WHAT IT WARNS ON (exit 0 + stderr)
  - Resolved definition has no `effort:` pin. The Agent tool exposes no effort
    parameter, so effort can ONLY come from frontmatter; without it the subagent
    inherits session effort (xhigh under ultracode).
  - `isolation: worktree` on a spawn (writes land in a temp worktree).

DESIGN: FAIL-OPEN, matching the Workflow gate. Any unreadable payload, unknown
agent type, or internal error allows the call. This is the fourth layer of
defense, never the only one.

Tier matrix: helpers=haiku/low . workers=sonnet/high . judges=claude-opus-5-5/xhigh .
final audit=claude-fable-5-1/xhigh . orchestration=driving session.
Blueprint: docs/

v1.2 | 2026-09-23 | tier-matrix text in this docstring and in the block message updated per
       owner ruling 2026-09-23; no logic change
v1.1 | 2026-08-22 | plugin agent resolution: namespaced types (plugin:agent)
       resolved via installed_plugins.json installPath/agents (CLD-C009 —
       harness honours plugin frontmatter pins; live block probe 2026-08-22)
v1.0 | 2026-08-06 | Owner: jtims
"""
import json
import os
import re
import sys

# Built-in subagent types and whether their model is FIXED by the harness.
# Source: code.claude.com/docs/en/sub-agents "Built-in subagents" (2026-08-06).
BUILTIN_FIXED = {
    "statusline-setup": "sonnet",
    "claude-code-guide": "haiku",
}
BUILTIN_INHERITS = {"explore", "plan", "general-purpose", "claude"}

# Escape hatch: a prompt containing this marker documents a deliberate
# inherit-tier spawn and is allowed through with a warning.
OVERRIDE_MARKER = "PIN-OVERRIDE:"

def agent_roots():
    """Ordered agent-definition roots, highest precedence first.

    Docs (sub-agents#choose-the-subagent-scope): when several definitions share a
    name, the higher-priority location wins, and "across nested project
    directories, the definition closest to the working directory wins". So:
    project scopes nearest-first, then user scope. Both are scanned RECURSIVELY.

    LIMITATION: managed-settings agents (priority 1, org-deployed) are NOT
    resolved here because the managed directory is platform-specific and this
    gate must never guess a path. If managed subagents are ever deployed, a
    managed definition could pin a model this gate reports as unpinned; the gate
    fails toward BLOCK there, which is the safe direction (a false block is
    visible and one retry fixes it; a false allow is silent inheritance).
    """
    roots, seen = [], set()
    d = os.getcwd()
    while True:
        cand = os.path.join(d, ".claude", "agents")
        if os.path.isdir(cand) and cand not in seen:
            roots.append(cand)
            seen.add(cand)
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    user = os.path.join(os.path.expanduser("~"), ".claude", "agents")
    if os.path.isdir(user) and user not in seen:
        roots.append(user)
    return roots


def frontmatter(path):
    """Return the raw frontmatter block of a .md file, or '' on any failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(8192)
    except Exception:
        return ""
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", head, re.S)
    return m.group(1) if m else ""


def scalar(block, key):
    """Extract a top-level scalar from a frontmatter block.

    Deliberately regex-based, not a YAML parse: several definitions in this
    roster contain unquoted ': ' or ' #' inside `description`, which makes a
    strict YAML load raise. The gate must not fail on files the harness accepts.
    """
    m = re.search(r"^%s\s*:\s*(.*)$" % re.escape(key), block, re.M)
    if not m:
        return None
    val = m.group(1).strip().strip("'\"")
    val = re.sub(r"\s+#.*$", "", val).strip()  # trailing YAML comment
    return val or None


def find_definition(agent_type):
    """Locate the definition block for an agent type, honouring scope precedence.

    Identity comes only from the `name` frontmatter field, not the filename
    (docs), so `name:` is authoritative and a filename match is only a fast path.
    Each root is walked recursively because both scopes are scanned recursively.
    """
    if not agent_type:
        return None
    for root in agent_roots():
        fallback = None
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                path = os.path.join(dirpath, fn)
                block = frontmatter(path)
                if not block:
                    continue
                if scalar(block, "name") == agent_type:
                    return block  # authoritative: name field match
                if fallback is None and fn[:-3] == agent_type:
                    fallback = block  # filename match, kept only if no name match
        if fallback is not None:
            return fallback
    return plugin_definition(agent_type)


PLUGIN_REGISTRY = os.path.join(
    os.path.expanduser("~"), ".claude", "plugins", "installed_plugins.json"
)


def plugin_definition(agent_type):
    """Resolve a namespace-qualified plugin agent type ('plugin-name:agent-name').

    Installed plugins are registered in ~/.claude/plugins/installed_plugins.json
    (v2: {"plugins": {"<plugin>@<marketplace>": [{"installPath": ...}, ...]}});
    each install ships agents at <installPath>/agents/*.md with the BARE agent
    name in `name:` frontmatter (verified 2026-08-22 against reasoning-bundle
    0.2.0 + architects 1.0.0). Per CLD-C009 the harness honours these pins, so
    the gate must read them. Any read/parse failure returns None, flowing to
    the existing BLOCK path — a false block is visible and retryable; a false
    allow is silent inheritance.
    """
    if ":" not in agent_type:
        return None
    plugin_name, _, agent_name = agent_type.partition(":")
    if not plugin_name or not agent_name:
        return None
    try:
        with open(PLUGIN_REGISTRY, "r", encoding="utf-8") as f:
            registry = json.load(f)
    except Exception:
        return None
    roots, seen = [], set()
    for key, installs in (registry.get("plugins") or {}).items():
        if key.split("@", 1)[0] != plugin_name or not isinstance(installs, list):
            continue
        for entry in installs:
            ip = (entry or {}).get("installPath")
            if not ip:
                continue
            root = os.path.join(ip, "agents")
            if root not in seen and os.path.isdir(root):
                roots.append(root)
                seen.add(root)
    for root in roots:
        fallback = None
        for dirpath, _dirnames, filenames in os.walk(root):
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                block = frontmatter(os.path.join(dirpath, fn))
                if not block:
                    continue
                if scalar(block, "name") == agent_name:
                    return block
                if fallback is None and fn[:-3] == agent_name:
                    fallback = block
        if fallback is not None:
            return fallback
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open
    if payload.get("tool_name") not in ("Agent", "Task"):  # Task = pre-2.1.63 alias
        return 0

    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        return 0
    agent_type = (ti.get("subagent_type") or "").strip()
    per_call_model = (ti.get("model") or "").strip()
    prompt = ti.get("prompt") or ""
    override = OVERRIDE_MARKER in prompt

    warnings = []
    if ti.get("isolation") == "worktree":
        warnings.append("isolation:worktree — edits land in a temp git worktree, not the checkout.")

    # --- Rule 2: forks can never be pinned ---------------------------------
    if agent_type.lower() == "fork":
        if override:
            warnings.append("fork spawn allowed by PIN-OVERRIDE — runs at DRIVER tier with the parent's full tool pool.")
        else:
            sys.stderr.write(
                "BLOCKED by pre-agent-pin-gate: subagent_type 'fork' cannot be model-pinned. "
                "A fork always inherits the driver model and receives the parent's entire tool "
                "pool (it skips both subagent tool filters), so in a Fable/Opus session every "
                "fork is a top-tier agent with full write reach. Use a pinned named agent "
                "(swarm-helper | swarm-worker | swarm-judge | swarm-auditor) and pass the "
                "context it needs in the prompt. If a fork is genuinely required, include "
                "'PIN-OVERRIDE: <reason>' in the prompt to record the deliberate choice. "
                "Gate: ~/.claude/hooks/pre-agent-pin-gate.py"
            )
            return 2

    # --- Rule 1: effective model must not resolve to inherit ---------------
    if per_call_model:
        effective, source = per_call_model, "per-invocation model param"
        block = find_definition(agent_type) if agent_type else None
    else:
        key = agent_type.lower()
        if key in BUILTIN_FIXED:
            effective, source, block = BUILTIN_FIXED[key], "built-in fixed model", None
        else:
            block = find_definition(agent_type) if agent_type else None
            fm_model = scalar(block, "model") if block else None
            if fm_model and fm_model.lower() != "inherit":
                effective, source = fm_model, "definition frontmatter"
            else:
                effective, source = None, None

    if effective is None:
        if override:
            warnings.append(
                "inherit-tier spawn of '%s' allowed by PIN-OVERRIDE." % (agent_type or "<unnamed>")
            )
        else:
            why = (
                "it is a built-in catch-all that inherits the session model"
                if agent_type.lower() in BUILTIN_INHERITS
                else "its definition has no usable model: pin (missing, empty, or 'inherit')"
                if block is not None
                else "no definition was found for it in ~/.claude/agents, ./.claude/agents, "
                     "or installed plugins (~/.claude/plugins/installed_plugins.json)"
            )
            sys.stderr.write(
                "BLOCKED by pre-agent-pin-gate: spawn of agent '%s' would INHERIT the session "
                "model because %s. Pass an explicit model on the Agent call "
                "('haiku' | 'sonnet' | 'opus' | 'fable'), or spawn a tier-pinned agent instead "
                "(swarm-helper=haiku | swarm-worker=sonnet | swarm-judge=claude-opus-5-5 | "
                "swarm-auditor=claude-fable-5-1). Inheriting deliberately still requires writing "
                "the tier out as a literal, or recording 'PIN-OVERRIDE: <reason>' in the prompt. "
                "Gate: ~/.claude/hooks/pre-agent-pin-gate.py"
                % (agent_type or "<unnamed>", why)
            )
            return 2

    # --- Effort warning: only frontmatter can set it -----------------------
    fm_effort = scalar(block, "effort") if block else None
    if not fm_effort and agent_type.lower() not in BUILTIN_FIXED:
        warnings.append(
            "agent '%s' has no effort: pin — the Agent tool has no effort parameter, so it "
            "inherits SESSION effort (xhigh under ultracode). Add effort: to its definition."
            % (agent_type or "<unnamed>")
        )

    if warnings:
        sys.stderr.write(
            "pre-agent-pin-gate notes (allowed; model=%s via %s): %s"
            % (effective, source, " ".join(warnings))
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
