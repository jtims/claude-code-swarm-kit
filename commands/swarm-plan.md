---
description: Route ANY subagent-spawning task to the right vector, tier, and pins before spawning anything — the general pre-flight beneath /research-swarm and /swarm-init
---

# /swarm-plan — spawn-vector router

Plan any fan-out **before** it spawns. `/research-swarm` handles the research shape; this command handles everything else — audits, migrations, reviews, sweeps, implementation fan-outs — and routes research back to `/research-swarm`.

Input: `$ARGUMENTS` = the task in plain words. Output: a filled routing decision plus a ready-to-run launch block. **This command plans; it does not spawn.**

Canonical references — read before improvising: `agent-swarm-doctrine` skill (hot layer) · `Agent-Spawn-Surface-Taxonomy_2026-08-06.md` and `Fable5-UC-Swarm-Blueprint_2026-07-27.md` in `docs/`.

## Step 1 — Size it before choosing anything

Anthropic's ladder. Answer this first; it decides whether a swarm is warranted at all.

| Shape | Fan-out |
|---|---|
| Simple fact-finding / single lookup | **1 agent**, 3–10 tool calls — often no swarm at all |
| Direct comparison, 2–4 known angles | **2–4 subagents**, 10–15 calls each |
| Complex research / wide unknown surface | **10+ subagents**, divided responsibilities |

Multi-agent costs ~15× a chat interaction, and token usage alone explains ~80% of outcome variance. **If a single agent can hold it, use a single agent.** Multi-agent is a poor fit when workers must share one context or have many interdependencies.

## Step 2 — Pick the vector

| If the work… | Vector | Why |
|---|---|---|
| is research with lenses + verification | **`/research-swarm`** | canonical 5-stage shape already exists — stop here and use it |
| needs a script to hold the loop, or >15 agents, or cross-checking | **Workflow** (`agent()`) | plan lives in code; resumable; per-call pins |
| is a handful of independent side tasks in this session | **Agent tool** | cheapest; results summarise back |
| needs workers to argue with each other | **Agent teams** | shared task list + direct messaging (see Step 5) |
| is many independent long jobs you'll check on later | **Background sessions** | own quota each; auto-worktree |
| is one large change across many files, each wanting its own PR | **`/batch`** | 5–30 worktree subagents, **each opens a PR** — confirm explicitly, never autonomous |
| needs the full current conversation | **fork** — last resort | unpinnable; runs at driver tier with the parent's whole tool pool |

Two hard constraints: **subagents never receive the `Workflow` tool**, so nested fan-out is `Agent`-based and depth-bounded; and **background subagents lose most built-in tools silently** (the default since v2.1.198).

## Step 3 — Pin every tier

| Tier | Pin | Effort | For |
|---|---|---|---|
| T4 helper | `haiku` | `low` | sweeps, enumeration, dedup, formatting, preflights |
| T3 worker | `sonnet` | `high` | gathering, drafting, extraction, refutation |
| T2 judge | `claude-opus-5-5` | `xhigh` | adjudication, synthesis, critique panels |
| T5 audit | `claude-fable-5-1` | `xhigh` | ONE pass over a distilled dossier, never raw material |

Rules that bite:

- **Workflow `agent()`**: pass `model:` **and** `effort:` on every call. The gate blocks a missing `model:`.
- **Agent tool**: there is **no `effort` parameter** — effort comes only from the agent definition. Spawn a roster agent (all 16 carry `model` + `effort`) or pass an explicit `model` and accept session effort.
- Unpinned `general-purpose` / `claude` / `Plan` / `fork` / plugin `architects:*` spawns are **blocked** by `pre-agent-pin-gate.py`. That is the design, not a bug.
- Never set `CLAUDE_CODE_SUBAGENT_MODEL` — highest precedence, flattens every tier including the audit.

## Step 4 — Bound the work in the prompt, not with a cap

`maxTurns` is deliberately **not** used anywhere in this roster (owner ruling 2026-08-06): it truncates mid-flight and is a silent cap, which standing rule 5 forbids. Bound scope in the delegation prompt instead. Every spawn prompt states:

1. **Objective** — the one question or change this agent owns
2. **Output format** — schema, file path, or exact shape expected
3. **Tools and sources** — which to use, which to avoid
4. **Boundaries** — what is out of scope, and what to do on a dead end rather than widen

Short prompts are the documented cause of subagents duplicating each other's work.

## Step 5 — Agent teams: per-run opt-in only

Teams are **not** enabled in settings, deliberately: they break `/resume` with in-process teammates. Enable per session at launch, never estate-wide:

```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
```

If teams are chosen, also account for: teammates **do not inherit `/model`** (set it in the spawn prompt or `/config` → Default teammate model) · they **do** inherit the lead's effort · a teammate definition's `skills` and `mcpServers` frontmatter is **ignored** · all teammates start with the lead's permission mode and cannot be given per-teammate modes at spawn · partition files so no two teammates edit the same one · cost ≈ 7× a standard session.

## Step 6 — Emit the block, then stop

Report: sizing verdict · chosen vector + why · per-agent tier table · the bounded prompt skeleton · the launch block · and anything deliberately **not** covered. Then hand off — the human launches.

For a research run:

```
/research-swarm {"question": "...", "out_dir": "<topic folder>/Research", "slug": "...", "scope": "...", "max_claims_per_lens": 10}
```

For a bespoke workflow, copy the tier constants and the stage-0 routing preflight from `~/.claude/workflows/research-swarm.js`. The pin gate enforces either way.

## Standing checks before any fan-out

1. **Preflight or abort** — assert each tier routes to its pinned model; an org `availableModels` allowlist causes silent fallback to the inherited model. Never fan out on a failed preflight.
2. **Disk-first** — full findings to `out_dir`; only compact summaries cross agent boundaries.
3. **No silent caps** — every truncation, sample, failed lens, or deferral is logged and lands in the deliverable's limitations.
4. **Topic routing (rule 12)** — one topic = one subdirectory. New topic → `/swarm-init`; pre-framework folder → `/swarm-init --adopt`.
5. **Outward-facing spawns need explicit confirmation** — `/batch` PRs, background sessions that auto-commit and push, anything publishing.
