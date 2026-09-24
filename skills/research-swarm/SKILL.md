---
name: research-swarm
description: Model-tiered research swarm discipline for heavy research in Claude Code. Load when running deep/heavy research, multi-agent research, a research workflow, an ultracode research task, or any fan-out that could burn the Fable budget. Triggers on - research swarm, deep research, heavy research, landscape scan, multi-lens research, adversarial verification run, ultracode research, subagent swarm, model tiering. Enforces the Fable5-UC tier matrix (helpers=haiku, workers=sonnet, judges=opus, final audit=fable), routing preflight, budget discipline, and the two-session topology.
---

# Research Swarm — model-tiered orchestration discipline

**Canonical reference:** `docs/Fable5-UC-Swarm-Blueprint_2026-07-27.md` (evidence, rationale, runbook, risk register). This skill is the hot layer; the blueprint is the source of truth.

**Scope (v1.4):** this skill governs the **research shape** only. The all-vector layer is the `agent-swarm-doctrine` skill — it covers every way a subagent can be spawned (Workflow, Agent tool, fork, skill `context: fork`, agent teams, background sessions, `/batch`), the tool-filter and permission facts that differ per vector, and standing rules 13–18. Co-load it for any fan-out that is not research-shaped, and route unclassified fan-out through `/swarm-plan` first. Full taxonomy: `Agent-Spawn-Surface-Taxonomy_2026-08-06.md` in the framework home.

**Version:** v1.6 | 2026-09-23 (v1.6: tier pins updated per owner ruling 2026-09-23; the matrix itself lives in `agent-swarm-doctrine` v1.1 (T2 `claude-opus-5-5`/xhigh, T3 `sonnet`/high, T5 `claude-fable-5-1`/xhigh); here the Topology C driver moves to `claude-opus-5-5`, matching settings.json since 2026-09-22, and the rule 1 full-ID example to `claude-fable-5-1`) | v1.5 | 2026-09-04 (v1.5: standing rule 2 amended — a restore payload is not an evidence record. Canonical `research-swarm.js:203` `verdict: f || v` discards the refuter on every adjudicated claim, so the framework's own claims artifact retained only the surviving side of every contested claim; measured on run wf_08645a1a-139, 26 of 45 refuted claims were contested and their refuter evidence was being dropped. Rule now requires a separate lossless verification record and points at `CLD-C035` for the unrecoverable-stage problem. Cascade: blueprint doctrine item 4 → v1.5, `research-swarm.js` → v1.2 (fixed at source), skill-dependencies → 2.17; `agent-swarm-doctrine` assessed and NOT reached, rule 2 being a research-shape rule not a cross-vector one. Detail: `Tooling-Notes_Run-Cache-and-Evidence-Fidelity_2026-09-04.md`) | v1.4 | 2026-08-06 (v1.4: re-scoped as a specialization of `agent-swarm-doctrine` — the all-vector layer now owns cross-vector rules 13–18, the seven spawn vectors, and the tool-filter/permission facts; allowlist-fallback semantics corrected for the v2.1.222 family-alias substitution; `maxTurns` deliberately unused per owner ruling — bound agents in the prompt, not with a silent cap. v1.3.2: seat policy — Opus drives only frozen plans, and every Topology-C output requires a Fable acceptance pass; from the 2026-08-01/02 driver-seat state-assertion incidents. v1.3.1: Topology-C driver rerouted claude-opus-4-8 → claude-opus-5, matching settings.json. v1.3: rule 12 topic routing — one topic = one subdirectory, adopt mode for pre-framework projects, framework home is docs-only. v1.2: structure enforcement — /swarm-init scaffold, 7-key frontmatter standard, output validator, prompt-template input contract. v1.1: topology inverted per owner ruling: A′ Fable-driven default; C = locked-plan economy variant)

## The one invariant

**No `agent()` call may inherit the session model.** Every agent in every workflow script carries an explicit `model:` AND `effort:` pin. In a Fable 5 session, an unpinned agent burns the scarcest budget (root cause of the 2026-07-26 spend-cap event). The PreToolUse gate `~/.claude/hooks/workflow-model-pin-gate.py` blocks violations mechanically; write compliant scripts rather than fighting it.

## Tier matrix — POINTER, plus the research-shaped delta (F54 / D111)

**T1 through T5 are owned by `agent-swarm-doctrine`** ("Tier matrix (pin verbatim)"). That skill is
the all-vector layer and its own scope statement claims the cross-vector rules, so it owns the
generic matrix. **Read the pins there; they are not restated here.** One owner, everyone points.

Only what is specific to the *research* shape lives here, because `agent-swarm-doctrine`'s matrix
does not carry it:

| Tier | Pin | Effort | Use for |
|---|---|---|---|
| **T0 Advisory/plan** (research-only; absent from the doctrine matrix) | Fable 5 session (ultracode) | xhigh | prompt analysis, contract shaping, swarm-configuration design — interactive |
| **T1 refinement for research runs** | the driving session — Fable 5 default (same session as T0); `claude-opus-5-5` for locked-plan **Topology C** economy runs | xhigh / high | workflow authoring + launch, phase synthesis, human gates |

Everything else — T2 judge, T3 worker, T4 helper, T5 final audit, and the `swarm-helper` /
`swarm-worker` / `swarm-judge` / `swarm-auditor` roster with `Explore` pinned to haiku — is defined
once in `agent-swarm-doctrine`. This section was a full duplicate until 2026-08-24; the two copies
had already diverged (the doctrine matrix has five rows, this one had six), which is precisely the
drift F54 exists to stop.

## Topology (owner ruling 2026-07-27: A′ default, C economy)

- **Default — Topology A′ (Fable-driven):** one **Fable 5 ultracode session** end-to-end — it analyzes the original prompt, designs the swarm configuration, authors/invokes the workflow (`/research-swarm` with args when the canonical shape fits; bespoke pinned script otherwise), and synthesizes between runs. Every subagent pinned down-tier (hook-enforced, including Fable's own bespoke authoring); the fable audit runs INSIDE the workflow as the pinned T5 agent. Fable burn = main loop + audit only.
- **Economy variant — Topology C (locked plans only, deliberate choice):** for overnight/multi-hour programs with a frozen plan: the Fable session writes spec + args, an **Opus session** (`claude-opus-5-5`) executes the saved script and babysits. Lossless by construction (the script IS the configuration); the only delta is between-phase synthesis at Opus level.
- **Seat policy (v1.3.2 — evidence-based):** an Opus model holds the driver seat ONLY for locked-plan (Topology C) execution, and every Topology-C output set requires a **Fable acceptance pass before its results are treated as true**. Opus never drives unsupervised state-assertion-heavy sessions (resumptions, worklogs, registers, close-outs). Evidence: 7 false-state assertions from the `claude-opus-5` driver seat (2026-08-01/02) vs 0 across 70 pinned subagents — blueprint v1.3.3 §3.3 / cascade brief §3.
- Human sign-off between stages = separate workflow runs (per official docs: no mid-run user input).
- **Never set `CLAUDE_CODE_SUBAGENT_MODEL`** — it has highest precedence and silently flattens the tier matrix (including the fable audit tier).

## Running it

**Topic routing first (rule 12): one topic = one subdirectory.** New topic → `/swarm-init <Project-Name>` scaffolds its own folder under `<parent>/` (frontmattered Prompt/WORKLOG/RESUME-HERE/Research). Continued work on an existing topic → that topic's existing folder; if it predates the framework, `/swarm-init --adopt <folder>` attaches the structure without touching existing files. Sub-topics nest at `<project>/Research/<Sub-Topic>_<date>/`. The framework home (`Fable5-Ultracode-Swarm_2026-07-27/`) is docs-only — research output is NEVER written there. `Prompt.md` is seeded from the **Optimal Research Prompt Template** (that folder, `Prompt-Template_Research-Swarm_2026-07-27.md`); §§1/4/8 (CONTRACT, SCOPE FENCES, DELIVERABLES SPEC) must be `TBD-OWNER`-free before any fan-out.

Then the saved workflow — `/research-swarm` (source: `~/.claude/workflows/research-swarm.js`), args:

```
{ "question": "<the research question>",
  "out_dir": "<THAT TOPIC's project folder>/Research",   // never the framework home; never another topic's folder
  "slug": "<short-run-slug>",
  "scope": "<optional constraints>",
  "lenses": [{"key":"...","hint":"..."}],   // optional; default 4 generic lenses
  "max_claims_per_lens": 10 }
```

For bespoke workflows (ultracode keyword or `/effort ultracode`): copy the tier constants and the preflight stage from `research-swarm.js`; the gate enforces the pins either way.

## Standing rules (apply to every run)

1. **Preflight or abort.** Stage 0 asserts each tier routes to its pinned model and confirms Fable capacity before any worker spend. Never fan out on a failed preflight. An enterprise `availableModels` allowlist causes SILENT fallback: before CC v2.1.222 **any** blocked pin falls back to the inherited model; from v2.1.222 a blocked **family alias** (`opus`) instead runs on the newest permitted version of that family, while any other blocked value — including a full model ID such as `claude-fable-5-1` — still falls back to inherited. The preflight is therefore most load-bearing for the full-ID T5 audit pin. Verify against the running version.
2. **Disk-first; and a restore payload is not an evidence record.** Workers write full findings under the run's `out_dir`; only compact structured summaries + paths return to the script. The fable auditor reads only the dossier + claims digest. Claims tables built for restore are **lossy by construction** — canonical `research-swarm.js:203` (`verdict: f || v`) keeps only the surviving side of a contested claim, so the refuter's evidence is dropped on every adjudicated one. Emit a **separate lossless verification record** carrying both sides plus all sources, and never hand a successor session the restore payload as evidence. Stage is likewise unrecoverable from disk (`CLD-C035`): carry it in each agent's return schema, never by parsing prompts.
3. **No silent caps.** Every truncation, sample, failed lens, or budget deferral is logged and lands in the dossier's limitations section.
4. **Budget guard.** Verification stops (recorded, not silent) when remaining budget threatens the audit reserve; the audit is never sacrificed silently — a skipped audit returns status UNAUDITED explicitly.
5. **Two-attempt cap on audit repair.** FIX → one repair → one re-audit → human gate. Never a third automatic round.
6. **Worklog upkeep.** After every run, append a dated entry to the project's WORKLOG (per feedback_ias_worklog_upkeep pattern) with: run status, stats block, dossier path, open questions.
7. **Spend telemetry.** Surface per-run token totals (from the workflow result/journal) to the owner in the close-out.
8. **Structure is enforced (blueprint rule 11).** Every swarm-written .md opens with the 7-key frontmatter (title, project, type, version, date, run_id, status); the fable audit FIXes a dossier without it. Agent returns are schema-typed (the gate warns on bespoke `agent()` calls missing `schema:`). Close-out runs `python3 ~/.claude/hooks/validate-swarm-outputs.py <project_dir>` — must PASS before reporting done.

## What this replaces

Unpinned ultracode fan-outs (every agent inheriting Fable). It does NOT replace: `/deep-research` for quick questions (fine as-is on an Opus session), or single-agent work for tasks below fan-out scale.
