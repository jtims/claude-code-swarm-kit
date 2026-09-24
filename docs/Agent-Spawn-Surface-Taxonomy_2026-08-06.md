---
title: Agent Spawn Surface Taxonomy — every vector, every spawnable agent
project: Fable5-Ultracode-Swarm_2026-07-27
type: spec
version: v1.1
date: 2026-08-06
run_id: n/a
status: draft
---

# Agent Spawn Surface Taxonomy

**Purpose:** the framework's answer to "account for ALL potential agents that could be spawned." The Fable5-UC blueprint v1.3.3 governed **one** of the seven ways a subagent can come into existence in this environment. This document enumerates all seven, every agent identity reachable through them, and how model/effort resolve on each path.

**Environment of record:** Claude Code **2.1.214** · driver `claude-opus-5` · `effortLevel: high` · ultracode available · no `env` block in settings.json (so all `CLAUDE_CODE_MAX_*` at defaults, agent teams OFF).

**Calibration key:** VERIFIED = re-derived this session by an independent path (execution > docs) · REPORTED = single named source · INFERRED = stated chain · ASSUMED = default, stated · UNKNOWN = exactly that.

---

## 1. The seven spawn vectors

| # | Vector | How it starts | Model resolution | Effort resolution | Gated after this session? |
|---|---|---|---|---|---|
| V1 | **Workflow `agent()`** | `Workflow` tool; script-held plan | per-call `model:` | per-call `effort:` | ✅ `workflow-model-pin-gate.py` |
| V2 | **Agent tool** (interactive + nested) | Claude calls `Agent` | per-call `model` param → frontmatter → **session model** | **frontmatter ONLY** (no tool param) | ✅ `pre-agent-pin-gate.py` + `Agent(model:*)` |
| V3 | **Fork** (`subagent_type: fork`, `/subtask`) | Claude requests type `fork`, or user runs `/subtask` | **always the driver model — unpinnable** | inherits session | ⚠️ policy only; gate blocks Claude-requested forks |
| V4 | **Skill with `context: fork`** | skill frontmatter `context: fork` + `agent:` | the named agent type's frontmatter; **defaults to `general-purpose` = inherit** | that agent's frontmatter | ⚠️ indirect — via V2 rules on the named type |
| V5 | **Agent teams** (lead + teammates) | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, lead spawns | **teammates do NOT inherit `/model`**; `/config` "Default teammate model" | **inherits the lead's effort** | ❌ disabled by choice; per-run opt-in |
| V6 | **Background sessions** | `claude --bg`, `/bg`, `/fork`, `claude agents` | directory settings → `--model` → default agent `claude` (inherit) | `--effort` → directory `effortLevel` | ❌ out of hook reach (separate process) |
| V7 | **`/batch`** bundled skill | `/batch <instruction>` | per-subagent, undocumented | undocumented | ❌ policy only — see §5 |

**Two structural constraints that shape every design [REPORTED — sub-agents#available-tools]:**

1. **`Workflow` is withheld from every subagent.** A subagent can never launch a workflow, so nested fan-out is necessarily `Agent`-based and bounded by the depth limit. Filter 1 also removes `AskUserQuestion`, `EnterPlanMode`, `ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers`, `EndConversation`, and `ExitPlanMode` (unless `permissionMode: plan`).
2. **Background subagents get a reduced built-in tool set** — and background is the **default** since v2.1.198. A background subagent keeps every MCP tool but only these built-ins: `Read`, `Grep`, `Glob`, `Bash`, `PowerShell`, `Edit`, `Write`, `NotebookEdit`, `WebFetch`, `WebSearch`, `TodoWrite`, `Skill`, `ToolSearch`, `EnterWorktree`, `ExitWorktree`, `Monitor`, `TaskStop`, `SendMessage`, `Artifact`. **Everything else is removed with no error reported** unless the `tools` list resolves to nothing. Forks skip both filters.

---

## 2. Every spawnable agent identity (25)

### 2.1 Built-in (6) [REPORTED — sub-agents#built-in-subagents]

| Agent | Model | Tools | Loads CLAUDE.md? | Note |
|---|---|---|---|---|
| `Explore` | inherits, **capped at Opus** on Claude API | read-only | **No** | the owner overrides it → `haiku`/`low`. A user/project agent named `Explore` beats the built-in and keeps its own `model`. |
| `Plan` | inherits | read-only | **No** | plan-mode research; one-shot, no agent ID, cannot be resumed |
| `general-purpose` | inherits | **every** subagent tool | Yes | the default when Claude names no type |
| `claude` | inherits | **every** subagent tool | Yes | catch-all; **also the default agent for dispatched background sessions** |
| `statusline-setup` | **Sonnet** (fixed) | Read, Edit | Yes | `/statusline` only |
| `claude-code-guide` | **Haiku** (fixed) | Bash, Read, WebFetch, WebSearch | Yes | Claude Code questions |

`Explore` and `Plan` are the **only** agents that skip CLAUDE.md and git status, and there is no frontmatter field or per-agent setting to change which agents skip them.

### 2.2 Custom user roster (16) — state as of this session

Tier-pinned swarm four + `Explore` override carry both `model` and `effort`. The other eleven carry `model` only, so **effort inherits the session** (`high` today, `xhigh` under ultracode). None carried `maxTurns`. [VERIFIED twice — direct parse + independent haiku sweep]

| Agent | Model | Effort | Tier |
|---|---|---|---|
| `swarm-helper` | haiku | low | T4 |
| `Explore` | haiku | low | T4 (recon) |
| `gtm-research-retriever` | haiku | *absent* | T4 |
| `kb-drift-auditor` | haiku | *absent* | T4 |
| `transcript-distiller` | haiku | *absent* | T4 |
| `swarm-worker` | sonnet | high | T3 |
| `branded-deliverable-builder` | sonnet | *absent* | T3 |
| `docx-engineer` | sonnet | high | T3 |
| `external-content-tos-gatekeeper` | sonnet | *absent* | T3 |
| `kb-content-processor` | sonnet | *absent* | T3 |
| `project-bootstrap` | sonnet | *absent* | T3 |
| `swarm-judge` | claude-opus-5-5 | xhigh | T2 |
| `database-architect` | claude-opus-5-5 | xhigh | T2 |
| `gtm-workflow-architect` | claude-opus-5-5 | xhigh | T2 |
| `skill-ecosystem-auditor` | claude-opus-5-5 | xhigh | T2 |
| `swarm-auditor` | claude-fable-5-1 | xhigh | T5 |

> **Amended 2026-09-23 (v1.1):** the model and effort cells of the eight rows above (the swarm-worker, swarm-judge and swarm-auditor rows, the three T2 specialists and docx-engineer) follow the owner ruling of 2026-09-23: T2 `claude-opus-5-5`/xhigh, T3 `sonnet`/high, T5 `claude-fable-5-1`/xhigh. Every other part of this document remains the 2026-08-06 snapshot on CC 2.1.214.

### 2.3 Plugin (2) + fork (1)

`architects:backend-architect` and `architects:frontend-architect` — **all tools**, and per the docs a plugin subagent **ignores `permissionMode`, `hooks`, and `mcpServers`** entirely. Plugin names are namespaced with `:`; a custom agent name may not contain `:`.

`fork` — not a definition but a spawn type. Inherits the parent's model, system prompt, tools, and full message history; shares the parent's prompt cache (so it is *cheaper* per token than a fresh subagent for the same context). Cannot spawn further forks.

---

## 3. Frontmatter: 16 fields, 5 previously used

The blueprint used `name`, `description`, `tools`, `model`, `effort`. The full set [REPORTED — sub-agents#supported-frontmatter-fields]:

| Field | Why it matters here |
|---|---|
| `disallowedTools` | denylist applied **before** `tools`; accepts `mcp__<server>` and `mcp__*` patterns |
| `permissionMode` | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan`/`manual`. **Parent `bypassPermissions`/`acceptEdits` wins and cannot be overridden**; under parent `auto` the field is ignored entirely |
| `maxTurns` | the only runaway-turn cap — **but it is a silent cap**, colliding with standing rule 5 |
| `skills` | preloads **full skill content** at startup (not just the description) |
| `mcpServers` | per-agent MCP scope; inline definitions connect on start and disconnect on finish. Keeps a server out of the parent conversation entirely |
| `hooks` | agent-scoped lifecycle hooks; project-scope agent hooks require workspace trust (v2.1.218+) |
| `memory` | `user`/`project`/`local` persistent dir; auto-enables Read/Write/Edit; inert if auto-memory is off |
| `background` | force background; ignored under `CLAUDE_CODE_FORK_SUBAGENT=1` |
| `isolation` | `worktree` — branches from the **default branch**, not the parent's HEAD; auto-cleaned if unchanged |
| `color`, `initialPrompt`, `prompt` | display; main-session-agent first turn; inline system prompt |

**Two fields are silently dropped for agent-team teammates:** `skills` and `mcpServers` are **not applied** when a definition runs as a teammate — teammates load skills and MCP from project/user settings like a normal session. A teammate honours `tools` and `model`, and the body is **appended** to its system prompt rather than replacing it.

---

## 4. Limits — and how CC 2.1.214 differs from current docs

| Limit | Default | Env var | On 2.1.214 |
|---|---|---|---|
| Session subagents | 200 | `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` | **active** (2.1.212+) |
| Concurrent subagents | 20 | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | **NOT present** (2.1.217+); once present, **ultracode sessions are exempt** |
| Nesting depth | 3 | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | **5 and uncappable** (env var 2.1.217+; default 3 at 2.1.219) |
| Workflow concurrency | min(16, cores−2) | — | active |
| Workflow agents/run | 1,000 | — | active |
| Items per `parallel`/`pipeline` | 4,096 | — | active |
| Workflow size guideline | `medium` (<15) | `workflowSizeGuideline` | setting is 2.1.219+; harness reports `medium` for this session |

Counting rules: workflow `agent()` calls do **not** count against the session subagent limit (workflows have their own per-run cap), but subagents that a workflow's agents spawn **with the Agent tool** do. `/subtask` forks count; a `/fork` background session does not.

**Allowlist behaviour changed at 2.1.222** [REPORTED]: a blocked **family alias** (`opus`) now runs on the newest permitted version of that family. Any *other* blocked value — including a full model ID such as `claude-fable-5` — still falls back to the **inherited** model. On 2.1.214 the blueprint's original claim holds in full for every pin. **The stage-0 routing preflight remains mandatory**, and is most load-bearing for the full-ID T5 pin.

---

## 5. Vector-specific hazards

- **V3 fork** — unpinnable by construction. In a Fable session every fork is a Fable-tier agent with the parent's entire tool pool.
- **V5 teams** — teammates start with the **lead's permission mode** (including `--dangerously-skip-permissions`) and cannot be given per-teammate modes at spawn. No nested teams, one team per session, lead is fixed, and `/resume` does not restore in-process teammates. Cost: **~7× a standard session** when teammates run in plan mode [REPORTED — costs#agent-team-token-costs].
- **V6 background sessions** — each consumes quota independently ("ten agents in parallel uses quota roughly ten times as fast"). Claude **commits without asking and pushes the branch** when a worktree it entered has changes; it never force-pushes or merges to main. Agent-view delete removes the worktree **including uncommitted changes**.
- **V7 `/batch`** — decomposes into **5–30 units**, one background subagent each in its own worktree, and **each opens a pull request**. That is an outward-facing, many-PR action: treat as I=3 and require explicit confirmation. Never autonomous.

---

## 6. Sizing rule (adopted from Anthropic's own guidance)

Multi-agent systems use **~15× the tokens of chat**; agent interactions ~4×. **Token usage alone explains ~80% of performance variance** on their BrowseComp evaluation. Their stated effort ladder [REPORTED — anthropic.com/engineering/multi-agent-research-system]:

> simple fact-finding → **1 agent, 3–10 tool calls** · direct comparison → **2–4 subagents, 10–15 calls each** · complex research → **10+ subagents** with divided responsibilities

Also load-bearing for our design: delegation prompts must carry *objective, output format, tool/source guidance, and explicit boundaries* — short instructions caused their subagents to duplicate work; and multi-agent is a **poor fit** where agents must share one context or have many interdependencies.

---

## 7. Standing rules this taxonomy adds (blueprint 13–18, proposed)

13. Every spawn vector carries an explicit tier. `fork` is prohibited without a recorded override.
14. `Workflow` is withheld from all subagents — nested fan-out is `Agent`-based and depth-capped.
15. Teammates pin `model` explicitly (they do not inherit `/model`); their `skills`/`mcpServers` frontmatter is ignored.
16. Background sessions auto-commit and push — never dispatch one on a branch that is not fenced.
17. `/batch` opens 5–30 PRs: explicit confirmation, never autonomous.
18. Size the fan-out by the §6 ladder **before** choosing a vector.

Plus, from the live calibration finding: **any `maxTurns` stop must be surfaced in the run's limitations** — it is a silent cap and rule 5 forbids silent caps.

---

## 8. Sources

All fetched 2026-08-06: `code.claude.com/docs/en/` — `sub-agents` · `workflows` · `agents` · `agent-teams` · `agent-view` · `hooks` · `skills` · `commands` · `costs` · `permissions`; plus `anthropic.com/engineering/multi-agent-research-system`. Extraction detail and verbatim quotes in [`Doc-Scrub-Findings_2026-08-06.md`](Doc-Scrub-Findings_2026-08-06.md).
