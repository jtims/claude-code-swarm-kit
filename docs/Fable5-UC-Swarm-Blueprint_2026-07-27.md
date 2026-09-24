---
title: Fable 5 Ultracode Swarm Blueprint
project: Fable5-Ultracode-Swarm_2026-07-27
type: spec
version: v1.6
date: 2026-07-27
run_id: wf_4f0f9b1a-15c
status: shipped
---

# Fable 5 Ultracode Swarm Blueprint — deterministic model tiering for heavy research

**Version:** v1.6 | 2026-09-23 | Owner: jtims | Author: Claude Code (Fable 5 session; v1.4 from an Opus 5 session; v1.5 doctrine item 4 amended from an Opus 5 session — restore payload is not an evidence record; v1.6 tier pins updated from an Opus 5.5 session)
**Status:** INSTALLED — all four layers live as of 2026-07-27, extended to **all seven spawn vectors** 2026-08-06 (see §6 inventory and §11). **The end-to-end `/research-swarm` production run remains UNEXECUTED** — see §9; governance is proven, the research pipeline is not.
**Companions:** this repository's `README.md` and `docs/`
**Calibration key:** VERIFIED = re-derived this session by an independent path (execution > docs) · REPORTED = single named source · INFERRED = stated chain from labeled premises · ASSUMED = default, stated · UNKNOWN = exactly that.

---

## 0. Executive summary

**The failure was model inheritance, not context overflow — and the fix is per-call model + effort pinning, now enforced mechanically.** In Claude Code, *"every agent in a workflow uses your session's model unless the script routes a stage to a different one"* [VERIFIED — official docs + empirical pin test, §9]. Running research swarms from a Fable 5 ultracode session therefore put ~5.3M subagent tokens (a prior research program, 49 agents) effectively all on Fable, exhausting the 5-hour session bucket, the separate Fable weekly allowance, and the org's usage-credit spend cap — which killed 7 verify-agents mid-run on 2026-07-26.

The installed remedy is a four-layer, all-native-Claude-Code architecture:

1. **Agent roster** (`~/.claude/agents/`) — five tier-pinned definitions (`swarm-helper`/haiku, `swarm-worker`/sonnet, `swarm-judge`/opus, `swarm-auditor`/fable, plus a haiku-pinned `Explore` override).
2. **Saved workflow** (`~/.claude/workflows/research-swarm.js`, runs as `/research-swarm`) — the canonical five-stage swarm with every `agent()` pinned, a routing/capacity preflight that aborts before spend, budget guards with an audit reserve, disk-first data flow, and a one-repair-round fable audit.
3. **Skill** (`~/.claude/skills/research-swarm/SKILL.md`) — the hot-layer discipline that loads on research tasks.
4. **Enforcement hook** (`~/.claude/hooks/workflow-model-pin-gate.py` + settings.json PreToolUse matcher) — mechanically blocks any workflow script containing an unpinned `agent()` call. Tested 9/9 cases (§9).

**Operating default (v1.1):** Topology A′ — a single **Fable 5 ultracode session** analyzes the prompt, designs the swarm configuration, sends the command, and synthesizes, with every subagent pinned down-tier; Fable also appears once inside each run as the final auditor. Topology C (an Opus session, `claude-opus-5-5` since 2026-09-22 and `claude-opus-5` from 2026-08-01, executes a Fable-frozen saved plan) is the deliberate economy variant for overnight arcs (§3.3).

**Expected effect [INFERRED from VERIFIED premises]:** Fable consumption drops from ~100% of swarm tokens to the main loop plus one audit agent per run (in the reference run below: 84k of 1.12M subagent tokens = 7.5%; on the 2026-07-26 workload shape, order-of-magnitude ~90%+ reduction in Fable-bucket burn). Total shared-bucket burn also falls because Sonnet/Haiku are officially classed Low/Moderate token intensity vs Opus/Fable High [REPORTED — Anthropic Enterprise consumption guide; no official numeric multiplier exists].

**Confidence:** routing mechanics 95%+ (executed and journal-verified in this environment, v2.1.214). Burn-reduction magnitude ~85% (mechanism verified; exact ratios workload-dependent). Residual risks in §8.

---

## 1. Problem statement and evidence

### 1.1 Observed failure (from an owner training document, 2026-07-23 — image-only doc, transcribed here to make it greppable)

- Background-task panel: workflow `program-os-surface` 5 agents / 556.4k tokens; `byoa-feasibility` 10 agents / 980.7k tokens with 5 of 6 verify agents showing **Error**; completed `program-landscape` 13 agents / **1.4M tokens**, individual agents 92–124k tokens each. [VERIFIED against the preserved workflow journals of that program, 2026-07-26]
- claude.ai Usage panel: **"Current session … 100% used"** (resets 3h10m); weekly "All models" 15%; separate **"Fable" meter at 23%**; limits banner: temporarily boosted (Claude Code +50% through Aug 19, Cowork +100% through Aug 5).
- Two "Usage limit reached" errors mid-work.
- Community guidance screenshots recommending: orchestrator=Opus 4.8, advisor/planner=Fable 5, workers=Sonnet 5, helpers=Haiku, staged audits Sonnet→Opus→Fable; "meticulous planning in fable … hand it over to opus as the orchestrator"; "giving it too much room to explore without a spec is 10000% token burner mode." [REPORTED — community posts; sound but nowhere documented as a named/benchmarked pattern, see §5.6]

### 1.2 Corroborating worklog evidence [VERIFIED — primary artifacts in this vault]

- An internal run record, 2026-07-26/27: 3 workflows ~28 agents launched; **21/28 completed, 7 errored on the org Fable spend cap** — all 7 in the adversarial-verify layer (the highest-value stage died last); ~2.98M subagent tokens. Program total across 4 workflows: 49 agents, ~5.3M subagent tokens, 862 tool calls. Recovery required a model switch (the owner → Opus 5 session) and a resumption kit.
- A second internal run record, 2026-07-25: "the owner hit the Fable usage threshold → full handoff context written" mid-arc.
- Standing directive already born from this: *"preflight one cheap subagent before any fan-out."* This blueprint formalizes it (§4 stage 0).

### 1.3 Precision correction to the original framing

"Maxes out my session context" is, on the evidence, **usage-bucket exhaustion, not context-window overflow** [VERIFIED]: workflow agent transcripts never enter main-loop context (the earlier program's runs recorded "zero conversation context lost" alongside millions of subagent tokens), and official docs confirm workflow/subagent usage counts against the same plan limits: *"/usage … attributes recent usage to skills, subagents, plugins, and individual MCP servers."* The one true context-cutoff event (an earlier project's session-1 token-cap handoff) is already mitigated by the RESUME-HERE/WORKLOG kit pattern — retained in §7.

---

## 2. Root cause — three independent confirmations

| # | Path | Finding |
|---|---|---|
| 1 | Official docs [VERIFIED quote] | *"Every agent in a workflow uses your session's model unless the script routes a stage to a different one or the CLAUDE_CODE_SUBAGENT_MODEL environment variable is set, which overrides both."* — code.claude.com/docs/en/workflows |
| 2 | Subagent resolution order [VERIFIED quote] | 1. `CLAUDE_CODE_SUBAGENT_MODEL` env var → 2. per-invocation `model` param → 3. agent-definition `model` frontmatter → 4. **the main conversation's model**. Frontmatter default is `inherit`. — code.claude.com/docs/en/sub-agents |
| 3 | Empirical pin test, this environment [VERIFIED — harness journal, not self-report] | From a Fable 5 session, `agent()` opts.model routed exactly: `haiku`→`claude-haiku-4-5-20251001`, `sonnet`→`claude-sonnet-5`, `opus`→`claude-opus-5[1m]`, `fable`→`claude-fable-5`, and full ID **`claude-opus-4-8`→`claude-opus-4-8[1m]`**. Per-call `effort` accepted. Run `wf_4f0f9b1a-15c`, 2026-07-27. |

Corollaries that shaped the design:

- **Alias `opus` resolves to Opus 5, not Opus 4.8** [VERIFIED empirically]. Literal Opus 4.8 requires the full ID `claude-opus-4-8`.
- **`CLAUDE_CODE_SUBAGENT_MODEL` is a footgun for tiered swarms** [VERIFIED docs]: highest precedence, overrides per-call pins — it would flatten the fable audit tier to whatever it names. Standing rule: never set it.
- **Built-in `Explore` inherits the session model** (v2.1.198+; capped at Opus on the Claude API) [VERIFIED docs] — recon in a Fable session silently ran at top tier. A user agent literally named `Explore` overrides the built-in; installed pinned to haiku, read-only.
- **Per-subagent `effort` frontmatter exists** (`low`→`max`, overrides session effort) [VERIFIED docs quote]. Ultracode = xhigh session effort, and subagents inherit session effort by default — so effort pinning matters nearly as much as model pinning.
- **Enterprise `availableModels` allowlists cause silent fallback**: a disallowed pinned value is *skipped* and the subagent runs on the **inherited** model [VERIFIED docs] — the original failure mode, reintroduced invisibly. Hence the mandatory routing preflight.
- **Correction (v1.4, 2026-08-06): that fallback rule is now version-dependent** [REPORTED — sub-agents#choose-a-model, fetched 2026-08-06]. From **CC v2.1.222**, a blocked **family alias** (`opus`) runs on the newest version of that family the allowlist permits, following the same substitution rules as `/model`. **Any other blocked value — including a full model ID such as `claude-fable-5` — still falls back to the inherited model**, as does a family alias on providers where the substitution does not operate. Before v2.1.222 (which includes the 2.1.214 build this framework was verified on) the original all-pins-fall-back rule holds in full. Net effect: the preflight is *most* load-bearing for the full-ID **T5 audit pin**, which never benefits from alias substitution. Re-verify after any upgrade past 2.1.222.

---

## 3. Architecture

### 3.1 Definition of "orchestrator" in this harness

Dynamic-workflow orchestration is a deterministic JavaScript script — it costs zero model tokens to "run." The thing that orchestrates *at a model tier* is the **session main loop** that authors/invokes scripts and synthesizes between phases. "Opus as orchestrator" therefore means: run the driving session on the Opus tier — `claude-opus-5-5` as of 2026-09-22 (settings.json default, Skill Builder ruling R13; before that `claude-opus-5` from 2026-08-01, which superseded the original `claude-opus-4-8` after the fast-mode differentiator proved stale).

### 3.2 Tier matrix (canonical — owner-approved 2026-07-27)

| Tier | Role | Pin | Effort | Used for |
|---|---|---|---|---|
| T0 | Advisory / planning | Fable 5 **session** | xhigh (ultracode) | prompt analysis, contract shaping, decomposition, swarm-configuration design — interactive |
| T1 | Orchestration | **driving session** — Fable 5 by default (T0 and T1 are the same session in Topology A′); `claude-opus-5-5` for locked-plan economy runs | xhigh / high | workflow authoring + launch ("sends the command"), phase synthesis, human gates |
| T2 | Judge | `model: 'claude-opus-5-5'` | xhigh | contested-claim adjudication, synthesis, critique panels |
| T3 | Worker | `model: 'sonnet'` | high | gather lenses, refutation passes, drafting, extraction |
| T4 | Helper | `model: 'haiku'` | low | sweeps, enumeration, dedup, formatting, preflights |
| T5 | Final audit | `model: 'claude-fable-5-1'` | xhigh | ONE pass over the distilled dossier — never raw research |

Staged-audit ladder: worker self-checks in-stage → opus adjudication (T2) → single fable audit (T5). The community "Sonnet→Opus→Fable audit" pattern, implemented with the middle tier folded into verification where it does real work [design choice; the named ladder itself is community folklore, §5.6].

### 3.3 Session topology (owner ruling 2026-07-27, superseding the earlier C-default: **A′ default, C economy variant**)

**Owner requirement (verbatim intent):** Fable 5 must be the initial planner/advisor that analyzes the original prompt AND sends the command for the overall subagent configuration. Rationale accepted in full: the danger was never the driver's seat, it was subagent *inheritance* — now closed by the four layers. The swarm configuration (lens design, verification depth, kill-shot ordering) is the highest-leverage decision in a run and belongs on the strongest model; same-session authoring + launch eliminates spec-to-script translation loss; and mid-arc adaptive judgment (re-scoping between workflow runs) stays at Fable level.

- **Topology A′ — Fable-driven (DEFAULT):** one **Fable 5 ultracode session** end-to-end. Fable analyzes the prompt, designs the swarm configuration, authors/invokes the workflow (bespoke, or `/research-swarm` with args when the canonical shape fits), synthesizes between runs, and hosts the human gates. Every `agent()` is pinned down-tier (hook-enforced — this binds Fable's own bespoke authoring too). Fable burn = main loop + the T5 audit agent only; main-loop profile is tens of k tokens per program [VERIFIED at reference-run scale, this session], sustainable within the Teams Premium ≤50%-weekly Fable allowance [INFERRED].
- **Topology C — locked-plan economy variant (deliberate choice, never the default):** for overnight / multi-hour programs where the plan is frozen: Fable session (T0) writes spec + args, then an **Opus session** (`claude-opus-5-5`) executes the *saved* script across hours of babysitting. Lossless by construction — the script IS the configuration — and costs zero Fable main-loop tokens during execution. The only quality delta is between-phase synthesis at Opus judgment level; accept it only when phases are mechanical. (Matches the community "plan in fable … hand to opus overnight" pattern, which was always about locked-plan execution, not planning.) **Seat policy (v1.3.3, 2026-08-02):** every Topology-C output set requires a **Fable acceptance pass before its results are treated as true**, and an Opus driver never runs unsupervised state-assertion-heavy sessions (resumptions, worklogs, registers, close-outs). Evidence: 7 false-state assertions from the `claude-opus-5` driver seat across two sessions (2026-08-01/02) vs 0 across 70 pinned subagents — see owner session records, 2026-08-01/02.
- **T5 fable audit runs inside the workflow** as a pinned agent in both topologies.
- Notes: Fable 5 supports `/effort ultracode` [VERIFIED — this session runs it]; whether the Opus driver (Opus 5 or 4.8) does is UNKNOWN and irrelevant to C (saved workflows and the `ultracode` keyword run regardless of session effort [VERIFIED docs]). Human sign-off between stages = separate workflow runs (no mid-run user input, official constraint).

### 3.4 Why not n8n / plugins [VERIFIED]

- **n8n:** model routing happens inside the harness at `agent()`-call time; n8n can only trigger headless runs (`claude -p`) from outside and cannot influence per-agent routing. Additionally, the `ultracode` keyword is inert in `-p` prompts (docs), and headless runs bypass interactive permission gates. n8n stays optional as a *scheduler* for future unattended runs — never as the routing layer.
- **Superpowers plugin:** process/methodology skills (Jesse Vincent); no model-tiered orchestration in its own docs.
- **Gastown / Gascity (Steve Yegge):** role hierarchy (Mayor/Polecats/Crew) over parallel Claude Code instances; neither documents model-tier assignment per role. Heavier operational model than needed; native workflows already provide deterministic orchestration with per-call pins.

---

## 4. Canonical run shape (`/research-swarm`)

```
Stage 0  PREFLIGHT   4 micro-agents (one per tier, effort low, no tools)
                     → assert each routed to its pinned model (allowlist-fallback detector)
                     → fable pin doubles as spend-capacity check (standing directive, formalized)
                     → ANY failure = ABORT with structured reason, zero research spend
Stage 1  GATHER      1 sonnet worker per lens (default 4 lenses) — primary sources,
                     full findings → out_dir/raw/gather_<lens>_<slug>.md (disk-first),
                     returns ≤N claims each {source, load_bearing, label} + dropped_coverage
Stage 2  VERIFY      dedup across lenses (code, not agents) → load-bearing first →
                     sonnet refuter per claim (independent-path refutation) →
                     opus adjudication where load-bearing ≠ CONFIRMED or verdict = REFUTED
                     → budget guard: stops (recorded, never silent) to protect audit reserve
Stage 3  SYNTHESIZE  1 opus judge reads raw files + verified-claims table →
                     writes Dossier_<slug>.md (answer-first, labels, limitations incl. every
                     deferred/failed item) + raw/verified-claims_<slug>.json
Stage 4  AUDIT       1 fable auditor reads ONLY the two distilled files → SHIP | FIX | REJECT
                     FIX → one opus repair → one fable re-audit → then HUMAN GATE (two-attempt cap)
Return   status, dossier path, exec summary, open questions, full stats incl.
         verdict counts, budget-deferred ids, per-lens dropped coverage
```

Budget math for a representative run [ASSUMED shape, VERIFIED prices n/a — plan buckets, not dollars]: 4 lenses × ~120k + ~30 verifications × ~100k + adjudications + 1 opus synthesis + 1 fable audit ≈ 3.5–4.5M tokens, of which fable ≈ 100–300k (audit + preflight pin) ≈ **3–8%**, sonnet/haiku ≈ 80%+ at Low/Moderate intensity. Compare 2026-07-26: ~100% of ~3M on Fable.

### 4.1 Sizing ladder — decide scale before choosing a mechanism (v1.4)

Adopted from Anthropic's own multi-agent guidance [REPORTED — anthropic.com/engineering/multi-agent-research-system, fetched 2026-08-06]:

| Shape | Fan-out |
|---|---|
| Simple fact-finding / single lookup | **1 agent**, 3–10 tool calls — frequently no swarm at all |
| Direct comparison across 2–4 known angles | **2–4 subagents**, 10–15 calls each |
| Complex research over a wide unknown surface | **10+ subagents**, divided responsibilities |

Supporting numbers from the same source: multi-agent systems use **~15× the tokens of a chat interaction** (agent interactions ~4×), and **token usage alone explains ~80% of the variance** in their BrowseComp results — model choice and tool calls explain the remainder. An Opus lead with Sonnet subagents beat single-agent Opus by **90.2%** on their internal research eval, which is independent support for the shape of §3.2's tier matrix (not for any specific savings figure).

Two boundaries the same source draws, adopted here: multi-agent is a **poor fit** where all agents must share one context or where there are many interdependencies between them; and delegation prompts must carry **objective, output format, tool/source guidance, and explicit boundaries** — short instructions were their documented cause of subagents duplicating each other's work (rule 18).

### Teams Premium seat context [REPORTED — official support pages, URLs in §10]

- Per-seat allowance: rolling 5-hour window + weekly window, shared across Claude chat, Cowork, and Claude Code; size depends on seat tier (Premium > Standard).
- **Fable 5: usable up to 50% of weekly usage limits at no extra cost** (Premium-tier provision; on Pro and standard Team seats Fable is credits-only), then: usage credits, or switch models.
- The "org monthly Fable spend limit" that killed the 7 verifiers = the org's usage-credit spend cap engaging after the included Fable allowance [INFERRED — mechanism matches docs' org-level spend limits in dollar/credit terms; no per-model-family cap is documented anywhere official].
- Boosted limits (+50% Claude Code) expire ~Aug 19; the tiering must stand on its own after that [REPORTED — usage-panel banner].

---

## 5. Standing rules (the discipline layer)

1. **No `agent()` call may inherit the session model** — explicit `model:` + `effort:` on every call, even when the intended tier equals the session model (write it as a literal). Enforced by the gate.
2. **Never set `CLAUDE_CODE_SUBAGENT_MODEL`** — highest precedence; silently flattens the tier matrix including the audit tier.
3. **Preflight or abort** — never fan workers onto an unverified tier (allowlist silent-fallback + capacity check). Extends the Lovable-MCP preflight doctrine to model routing.
4. **Disk-first, and a restore payload is not an evidence record** — full findings to the run's `out_dir`; only compact summaries + paths cross agent boundaries; the fable auditor sees only the dossier + claims digest. A claims table built for restore is lossy by construction (`research-swarm.js:203`, `verdict: f || v`, drops the refuter on every adjudicated claim), so emit a separate lossless verification record with both sides and all sources; stage is unrecoverable from disk (`CLD-C035`), so carry it in each agent's return schema. Detail: `Tooling-Notes_Run-Cache-and-Evidence-Fidelity_2026-09-04.md`.
5. **No silent caps** — every truncation, sample, failed lens, or budget deferral is logged in-run and listed in the dossier's limitations (the `.slice(0,6)` lesson, mechanized).
6. **Audit reserve** — verification halts before it can starve the audit; a missing audit is an explicit `UNAUDITED` status, never a quiet omission.
7. **Two-attempt cap** on audit repair: FIX → one repair → one re-audit → human gate.
8. **Recon is read-only and cheap** — `Explore` pinned haiku with read-only tools; escalate a specific sweep to sonnet rather than editing the default (scope-authorization discipline, 2026-07-27).
9. **Worklog upkeep** — dated WORKLOG entry per run: status, stats, dossier path, open questions, spend.
10. **Alias hygiene** — `opus` resolves to the newest Opus and drifts with releases; anything version-critical uses full model IDs (`claude-opus-5-5`, `claude-fable-5-1`), as the T2 and T5 pins do since 2026-09-23.
11. **Structure is enforced, not hoped for (v1.2).** (a) Every swarm-written .md opens with the standard 7-key YAML frontmatter: `title, project, type (dossier|digest|raw-gather|worklog|resume|spec|template), version, date, run_id, status` — stamped by roster prompts and workflow prompts, audited by the fable gate (missing = FIX), and lintable by `validate-swarm-outputs.py`. (b) Projects begin with `/swarm-init` (scaffolds Prompt/WORKLOG/RESUME-HERE/Research with frontmatter; refuses existing folders; emits the launch args). (c) The ask enters through the **Optimal Research Prompt Template** (`Prompt-Template_Research-Swarm_2026-07-27.md`) — the 12-section anti-drift input contract; §§1/4/8 unfilled = no launch. (d) Agent returns are schema-typed: mandatory inside `/research-swarm`; the pin gate warns on any bespoke `agent()` lacking `schema:`.
12. **Topic routing (v1.3): one topic = one subdirectory.** Every task/topic lives in its own `<parent>/<Topic>_<YYYY-MM-DD>/` folder and inherits the framework by default — new topics via `/swarm-init`, pre-framework projects via `/swarm-init --adopt` (backfills structure, never rewrites existing content; legacy-doc policy per the owner 2026-08-01: retrofit frontmatter onto *living* docs — WORKLOG/RESUME-HERE/pending-sign-off, metadata mirroring their own headers — and grandfather closed/verified records via `.frontmatter-exempt`). Continued work routes to the topic's existing folder (`out_dir` = its `Research/`); sub-topics nest at `Research/<Sub-Topic>_<date>/`; the decision test is *same WORKLOG lineage = same folder*. This framework home is DOCS-ONLY — research output is never written here. Other topics may name a different parent in template §8 (explicit owner direction).

13. **Every spawn vector carries an explicit tier (v1.4).** The pin invariant is no longer workflow-only — it binds all seven vectors in §11. `fork` is **prohibited** without a recorded `PIN-OVERRIDE: <reason>` in the prompt, because a fork can never be pinned: it always runs at the driver model and receives the parent's entire tool pool.
14. **`Workflow` is withheld from every subagent (v1.4).** No subagent can launch a workflow, so nested fan-out is necessarily `Agent`-based and bounded by the spawn-depth limit. Design nesting accordingly; never plan a subagent that "kicks off a workflow."
15. **Teammates pin `model` explicitly (v1.4).** Agent-team teammates do **not** inherit the lead's `/model` (they *do* inherit its effort), and a teammate definition's `skills` and `mcpServers` frontmatter is **ignored**. Teams stay a per-run opt-in — never in `settings.json` `env`, because they break `/resume` with in-process teammates. **The sanctioned launch command (owner ruling 2026-08-06 — Option A, the only guaranteed per-run toggle; there is no built-in slash command to enable teams):**

    ```bash
    CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
    ```

    Teams then exist for that session only — nothing persisted, nothing to remember to switch off. When teams are used, budget ≈7× a standard session and partition files so no two teammates edit the same one.
16. **Background sessions auto-commit and push (v1.4).** A dispatched session commits without asking and pushes the branch when a worktree it entered has changes. Never dispatch one on an unfenced branch. Agent-view delete removes the worktree *including uncommitted changes*.
17. **`/batch` is outward-facing (v1.4).** It decomposes into 5–30 worktree subagents that each **open a pull request**. Treat as I=3: explicit confirmation, never autonomous.
18. **Size before choosing a vector, and bound in the prompt (v1.4).** Apply the effort ladder (§4.1) before selecting a mechanism. **`maxTurns` is deliberately unused across this roster (owner ruling 2026-08-06)** — it truncates mid-flight and is a silent cap, which rule 5 forbids. Bound each agent by stating objective, output format, tool/source guidance, and explicit boundaries in its prompt.

### 5.6 On the community pattern (honest sourcing)

The four-tier mapping (Fable plans / Opus orchestrates / Sonnet works / Haiku helps) and the staged-audit ladder come from credible-sounding community posts (transcribed in §1.1) and align with official cost guidance (*"Sonnet handles most coding tasks well… For simple subagent tasks, specify model: haiku"*), but **no official source names or benchmarks this pattern**, and claimed savings figures in circulating blog posts (30–80%, "5–10x") share no methodology [REPORTED, unverified]. This blueprint adopts the pattern because its mechanism is independently verified here — not because the community numbers are trusted.

---

## 6. Installed artifact inventory (layers 1–5 live 2026-07-27; layer 6 added 2026-08-06)

| Layer | Path | What it does |
|---|---|---|
| 1 | `~/.claude/agents/swarm-helper.md` | haiku/low helper, read-only |
| 1 | `~/.claude/agents/swarm-worker.md` | sonnet/high worker, disk-first, Write scoped to out_dir by prompt |
| 1 | `~/.claude/agents/swarm-judge.md` | claude-opus-5-5/xhigh judge — adjudication + synthesis |
| 1 | `~/.claude/agents/swarm-auditor.md` | claude-fable-5-1/xhigh final auditor, dossier-only, read-only |
| 1 | `~/.claude/agents/Explore.md` | overrides built-in Explore → haiku/low, read-only (built-in inherits session model since v2.1.198) |
| 2 | `~/.claude/workflows/research-swarm.js` | canonical 5-stage swarm; runs as `/research-swarm`; args-driven; syntax-verified; gate-clean |
| 3 | `~/.claude/skills/research-swarm/SKILL.md` | hot-layer discipline; loads on research-swarm tasks |
| 4 | `~/.claude/hooks/workflow-model-pin-gate.py` | PreToolUse gate on Workflow: blocks unpinned `agent()` (exit 2), warns on missing effort, fail-open on parse errors; 9/9 tests passed |
| 4 | `~/.claude/settings.json` | PreToolUse matcher `Workflow` → gate (timeout 10s); backup at `~/.claude/backups/settings.json.backup.<ts>`; `_last_updated` bumped |
| 5 (v1.2) | `~/.claude/commands/swarm-init.md` | `/swarm-init` — scaffolds a project folder (Prompt/WORKLOG/RESUME-HERE/Research) with frontmatter; refuses existing folders; emits pre-filled `/research-swarm` args |
| 5 (v1.2) | `_tooling/validate-swarm-outputs.py` (**canonical, this folder**; `~/.claude/hooks/validate-swarm-outputs.py` is a symlink to it as of v1.4) | Standalone structure lint: required files, 7-key frontmatter, naming convention; PASS/FAIL with itemized findings; run at init and close-out. Relocated into the framework home 2026-08-06 on the same principle as the ledger's `_tooling/` — a governance control must travel with the artifact it governs, or only one machine can enforce it. `/swarm-init` and the `research-swarm` skill keep referencing the `~/.claude` path, which resolves through the symlink |
| 5 (v1.2) | `Prompt-Template_Research-Swarm_2026-07-27.md` (this folder) | The 12-section optimal input contract — CONTRACT, scope fences, premises-to-test, kill-shot, evidence bar, budget/tiering, gates, failure protocol — each section mapped to the documented failure it prevents |

| 6 (v1.4) | `~/.claude/hooks/pre-agent-pin-gate.py` | PreToolUse gate on **Agent**: blocks any spawn resolving to inherit the session model, and any Claude-requested `fork`, unless the prompt records `PIN-OVERRIDE:`. Warns on missing `effort` and on `isolation: worktree`. Fail-open. 16/16 tests; **live-verified** (§9) |
| 6 (v1.4) | `~/.claude/settings.json` | `Agent(*)` **removed**; `Agent(model:*)` + 16 named `Agent(<name>)` allows added (129 → 145 rules); PreToolUse matcher `Agent` wired. Backup `settings.json.backup.20260806173301` |
| 6 (v1.4) | `~/.claude/commands/swarm-plan.md` | `/swarm-plan` — vector router: size → pick vector → pin tiers → bound in prompt → emit launch block. Plans only, never spawns |
| 6 (v1.4) | `~/.claude/skills/agent-swarm-doctrine/SKILL.md` | All-vector hot layer (v1.0): the invariant restated per vector, tier matrix, tool-filter and permission facts, limits, rules 13–18, teams opt-in |
| 6 (v1.4) | `~/.claude/agents/*.md` (11 files) | `effort:` pinned by tier on every previously-unpinned agent; 3 YAML-unsafe descriptions quoted. Roster now **16/16 strict-YAML valid, 16/16 effort-pinned** |
| 6 (v1.4) | `~/.claude/hooks/validate-agent-roster.py` | Deterministic frontmatter + tier-pin lint over all agents and skills. ERROR on the two **proven** silent-failure classes (`E2` de-registration via `\"` escapes in a double-quoted description; `E3` ` #` truncating a description as a YAML comment) plus missing `model`/`effort` (`E4`) and any `maxTurns` (`E5`). WARN on harness-tolerated latent forms. Wired into `/drift-audit` step 3c |
| 6 (v1.4) | `~/.claude/commands/drift-audit.md` | → **v2**: scope extended to the agent roster; +3b vault-SSOT skills · +3c roster lint · +3d registry cross-check (files on disk vs agent types actually offered) · 38-skill count reconciliation |
| 6 (v1.4) | `Agent-Swarm-Governance_2026-08-06/` | Session sub-topic: taxonomy, verification record, doc-scrub findings, WORKLOG, RESUME, `Evidence/` |

Removal/rollback: delete the artifact file(s); for the workflow hook additionally remove the `Workflow` matcher block from settings.json (or restore the backup). For the v1.4 layer, one command reverts the configuration: `cp ~/.claude/backups/settings.json.backup.20260806173301 ~/.claude/settings.json` (live, no restart — settings hot-reload is VERIFIED). Roster revert: `cp ~/.claude/backups/agents.20260806175003/*.md ~/.claude/agents/`. No other coupling.

---

## 7. Runbook — end-to-end research program (Topology A′ default)

1. **Fable 5 ultracode session (T0+T1):** route the topic first (rule 12): continued topic → its existing folder (adopt via `/swarm-init --adopt` if pre-framework); new topic → `/swarm-init <Project-Name>` — it scaffolds the folder (frontmattered Prompt/WORKLOG/RESUME-HERE/Research) and seeds `Prompt.md` from the **Optimal Research Prompt Template**. Fill the 12-section contract interactively; §§1/4/8 (`CONTRACT`, `SCOPE FENCES`, `DELIVERABLES SPEC`) must be `TBD-OWNER`-free before launch. *"Giving it too much room to explore without a spec is 10000% token burner mode"* — community, and consistent with all evidence here.
2. **Same session sends the command:** run `/research-swarm` with args pointing `out_dir` at the project's `Research/` folder (or author a bespoke pinned workflow when the canonical shape doesn't fit — the gate enforces pins either way). One run per human-gated stage. *(Topology C economy variant: for a frozen overnight plan, hand the saved script + args to an Opus session (`claude-opus-5-5`) for execution instead.)*
3. **Preflight fails → stop.** Fix routing/capacity (check `/usage`, allowlist, spend caps) and re-run. Never proceed on a failed preflight.
4. **Run returns:** read `exec_summary`, `stats` (verdict counts, deferred items, dropped coverage), and the audit verdict. `FIX_UNRESOLVED_HUMAN_GATE` / `REJECT` / `UNAUDITED` all route to the owner with the findings attached.
5. **Casualty repair:** mid-run agent deaths (spend/capacity) follow the earlier continuation pattern — the journal + `resumeFromRunId` replay completed agents from cache; author a continuation only for the gap (kit pattern: `Research/Workflow-Scripts/verify-continuation_2026-07-27.js`).
6. **Close out:** WORKLOG entry (status, spend from journal, dossier path, open questions); dossier is the deliverable of record in the vault.

---

## 8. Risk register

| Risk | Likelihood | Mitigation | Residual |
|---|---|---|---|
| Allowlist silent-fallback re-introduces inheritance | Low (no org allowlist observed) | Stage-0 preflight asserts routing every run | Near zero for workflow runs. **CLOSED for interactive Agent calls (v1.4)** — `pre-agent-pin-gate.py` + `Agent(model:*)` permission rule; live-verified |
| `fork` runs at driver tier with the parent's full tool pool | Medium (Claude may request it; user `/subtask` bypasses the Agent tool) | Gate blocks Claude-requested forks absent `PIN-OVERRIDE`; rule 13 | **Accepted** — unpinnable by construction; a user-initiated `/subtask` is outside hook reach by design |
| Background sessions auto-commit and push on an unfenced branch | Medium if used casually | Rule 16; `/swarm-plan` step 2 flags the vector | Accepted — outside hook reach (separate process, own settings scope) |
| `/batch` opens 5–30 PRs unintentionally | Low | Rule 17: explicit confirmation, never autonomous | Accepted — policy-only control |
| Ultracode suppresses the large-workflow warning and (2.1.217+) the concurrency cap | Certain while ultracode is the default | Sizing ladder §4.1 applied *before* launch; `/workflows` monitoring | Accepted deliberately — ultracode is opt-in to large runs |
| `maxTurns` omitted, so no mechanical per-agent turn bound | Certain (deliberate, owner ruling 2026-08-06) | Prompt-level boundaries (rule 18); 200/session + 1,000/run caps; manual stop via `x` in `/tasks` | **Accepted** — a silent cap was judged worse than an unbounded agent; rule 5 forbids silent truncation |
| Gate false-negative (agent call hidden in template-literal interpolation) | Low | Gate is one of four layers; script template + skill discipline + roster defaults | Accepted |
| Gate false-positive (quoted `"model":` keys) | Low | Documented style: unquoted keys in opts; gate message explains fix | Trivial to fix in-script |
| Gate fails open on its own bug | Low | By design (never brick Workflow); roster + skill still pin | Accepted — gate is backstop, not sole defense |
| Alias drift (`opus`→future Opus 6) changes T2 behavior | Medium over time | §5 rule 10: full IDs for version-critical pins; T2 uses alias deliberately (track latest) | Revisit at model releases |
| `effort` frontmatter/opts behavior changes across CC versions | Low | v2.1.214 verified now; version gates noted (ultracode ≥2.1.203, per-invocation persistence ≥2.1.211, Explore inheritance ≥2.1.198) | Re-verify after major CC upgrades |
| Fable audit agent quality < interactive Fable for planning | Medium | Topology C keeps planning interactive in a Fable session; audit is a bounded, dossier-scoped task that suits one-shot | Accepted per the owner decision |
| Boosted limits expire (~Aug 5/19) and budgets tighten | Certain | Tiering is the mitigation; §4 budget math assumes standard limits | Monitor first post-expiry run |
| Saved workflow not discovered as `/research-swarm` (filename/registration nuance) | Low | File carries `meta.name`; verify in next session's `/` autocomplete; re-save via `/workflows` `s` if needed | One-time check, noted in RESUME-HERE |

---

## 9. Verification record (what was actually done — 2026-07-27, extended 2026-08-06)

| Check | Method | Result |
|---|---|---|
| Per-call model pinning (5 values incl. full ID `claude-opus-4-8`) | Live workflow `wf_4f0f9b1a-15c` from this Fable session; harness journal `model` field per agent (not self-report) | 5/5 exact matches [VERIFIED] |
| Per-call `effort` accepted | Same run, `effort:'low'|'medium'` on all 9 agents | Accepted, ran [VERIFIED] |
| Official docs: workflow default model, resolution order, frontmatter values, env-var precedence, allowlist fallback, effort field, Explore inheritance, ultracode mechanics, saved-workflow format, usage-limit structure, Fable 50% provision | 4 sonnet researchers with verbatim-quote extraction; key quotes re-checked against fetched pages | Quotes in §2/§4/§10 [VERIFIED at doc level] |
| Enforcement gate | 9 payload tests: unpinned block (exit 2), pinned allow, effort-warning, scriptPath, named-workflow pass, non-Workflow pass, fail-open on garbage, string-literal immunity, `subagent(`/`obj.agent(` non-match | 9/9 pass [VERIFIED] |
| Gate wired into settings.json | Python edit + re-parse; matchers now `Edit|Write|NotebookEdit`, `Bash`, `Workflow`; timestamped backup | [VERIFIED] |
| `research-swarm.js` syntax | `node --check` under harness-equivalent async wrapping (top-level `return` is the documented workflow idiom) | SYNTAX OK [VERIFIED] |
| `research-swarm.js` gate-clean | Gate run against the saved file via scriptPath payload | exit 0, silent [VERIFIED] |
| Claude Code version gates | `claude --version` → 2.1.214 (≥ 2.1.203 ultracode, ≥ 2.1.211 pin persistence, ≥ 2.1.198 Explore inheritance) | Compatible [VERIFIED] |
| End-to-end `/research-swarm` production run | NOT yet executed — first real run is the acceptance test | **UNKNOWN — still unexecuted as of 2026-08-06.** owner ruling: kept deliberately separate from the v1.4 governance work so the framework is proven before a full run is spent on it. The v1.4 additions below prove *governance*; they prove nothing about the research pipeline |
| **v1.4 — `PreToolUse` fires on the `Agent` tool** | Live probe: unpinned `general-purpose` spawn returned `PreToolUse:Agent hook error: … BLOCKED by pre-agent-pin-gate`. Docs are **silent** on whether `Agent` is a valid PreToolUse matcher (only `Bash`, `Edit\|Write`, `mcp__.*` are shown); headless verification was impossible (`claude -p` → `Not logged in`) | [VERIFIED by execution] — also proves **exit 2 blocks the spawn** and **settings.json hot-reloads mid-session** |
| **v1.4 — pin gate unit suite** | 16 synthetic payloads, failure condition declared per case before running | 16/16 PASS, zero regressions after the §9.1 defect fixes [VERIFIED] |
| **v1.4 — roster hardening** | Applied to isolated copies first, then live; strict-YAML parse + gate sweep | 16/16 strict-YAML valid (from 14/16); 16/16 effort-pinned; `maxTurns` absent by ruling [VERIFIED] |
| **v1.4 — roster baseline corroboration** | Two independent paths: direct Python parse vs a pinned haiku agent reading the files itself | Agreement on all three counts (11 lacking effort, 16 lacking maxTurns, 16 total) [VERIFIED] |

### 9.1 Three gate defects caught by verifying before writing (v1.4)

The roster-candidate check first *read* as a gate failure (11 effort warnings against files that had just been hardened). Chasing the **declared failure condition** rather than the headline showed the test harness was resolving the wrong files — and then that the gate itself was wrong three ways:

| Defect | Consequence had it shipped | Fix |
|---|---|---|
| Scope precedence inverted — user scope read before project scope | wrong definition resolved in any project overriding an agent name (docs: project wins; managed wins over both) | ordered roots: project scopes nearest-first walking up from cwd, then user |
| No recursive scan | subfolder definitions invisible, though both scopes are scanned recursively | `os.walk` per root; `name:` field authoritative, filename only a fast path |
| Managed scope unhandled | an org-deployed pin could be misread as unpinned | documented limitation; fails toward **block** (visible, one retry) rather than silent allow |

A gate that resolved the wrong agent definition would have been silently wrong in precisely the way this framework exists to prevent. Full record: `Agent-Swarm-Governance_2026-08-06/Verification-Record_2026-08-06.md`.

Reference run economics (the validation workflow itself, run under the new rules): 9 agents, 1.12M subagent tokens, 0 errors, fable share = one 84k pin test (7.5%) — vs 100% fable on the 2026-07-26 runs.

## 10. References (all fetched 2026-07-27)

- code.claude.com/docs/en/workflows — workflow model default, saved-workflow format (`~/.claude/workflows/`, `meta` + script, runs as `/<name>`, `args` global), no-mid-run-input constraint, agent caps, ultracode keyword/effort mechanics
- code.claude.com/docs/en/sub-agents — resolution order, frontmatter `model`/`effort`, `CLAUDE_CODE_SUBAGENT_MODEL` precedence + v2.1.196 `inherit` semantics, allowlist skip behavior, Explore inheritance (v2.1.198), per-invocation persistence (v2.1.211)
- code.claude.com/docs/en/model-config — alias resolution (opus/sonnet → Opus 5/Sonnet 5 on Anthropic API), full-ID pinning, effort levels
- code.claude.com/docs/en/costs — subagent/workflow usage attribution to plan limits; per-seat 5h + weekly windows; "specify model: haiku" guidance
- support.claude.com/en/articles/14552983 (models & limits in Claude Code) · 15424964 (Fable 5 on your plan — 50% weekly provision, Pro/standard-seat exclusion) · 9797557 (usage-limit best practices, 5-hour session) · 14782391 (Enterprise consumption guide — Low/Moderate/High token intensity, org spend limits) · 11145838 (Pro/Max shared pool)
- Community (REPORTED only): tiering posts transcribed in §1.1; claude.com/plugins/superpowers; github.com/gastownhall/gascity; github.com/steveyegge/gastown
- **v1.4 additions (all fetched 2026-08-06):** `code.claude.com/docs/en/` — `agents` (the four parallel-agent surfaces) · `agent-teams` · `agent-view` · `hooks` (SubagentStart cannot block) · `skills` (`context: fork`) · `commands` (`/batch`) · `permissions` (`Agent(model:*)` matchers, deny→ask→allow precedence) · `costs` (agent teams ≈7×; MCP definitions deferred) · plus `anthropic.com/engineering/multi-agent-research-system`. Extraction detail: `Agent-Swarm-Governance_2026-08-06/Doc-Scrub-Findings_2026-08-06.md`

---

## 11. The seven spawn vectors (v1.4)

§§0–10 were written as though dynamic workflows were *the* fan-out mechanism. They are one of **seven** vectors, and official docs enumerate four parallel-agent surfaces as peers (subagents · agent view · agent teams · dynamic workflows). Until 2026-08-06 the framework's enforcement covered exactly one, because `workflow-model-pin-gate.py` is matched on `Workflow` and returns 0 for every other tool while `permissions.allow` carried a blanket `Agent(*)`.

| # | Vector | Model resolution | Effort resolution | Governed |
|---|---|---|---|---|
| V1 | Workflow `agent()` | per-call `model:` | per-call `effort:` | `workflow-model-pin-gate.py` |
| V2 | Agent tool (interactive + nested) | per-call `model` → frontmatter → **session** | **frontmatter only** (no tool param) | `pre-agent-pin-gate.py` + `Agent(model:*)` |
| V3 | Fork (`subagent_type: fork`, `/subtask`) | **always driver — unpinnable** | inherits session | rule 13 + gate (Claude-requested only) |
| V4 | Skill `context: fork` + `agent:` | named agent's frontmatter; **defaults `general-purpose` = inherit** | that agent's frontmatter | via V2 on the named type |
| V5 | Agent teams | **no `/model` inheritance**; `/config` default teammate model | **inherits the lead's effort** | rule 15; per-run opt-in only |
| V6 | Background sessions | directory settings → `--model`; default agent `claude` = inherit | `--effort` → directory `effortLevel` | rule 16; outside hook reach |
| V7 | `/batch` | per-subagent, undocumented | undocumented | rule 17; confirmation only |

**Two structural constraints that shape every design** [REPORTED — sub-agents#available-tools]: every subagent loses the **`Workflow`** tool (so a subagent can never launch a workflow — nested fan-out is `Agent`-based and depth-bounded), along with `AskUserQuestion`, `EnterPlanMode`, `ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers`, `EndConversation`, and `ExitPlanMode` unless `permissionMode: plan`. And **background subagents — the default since v2.1.198 — keep only** `Read, Grep, Glob, Bash, PowerShell, Edit, Write, NotebookEdit, WebFetch, WebSearch, TodoWrite, Skill, ToolSearch, EnterWorktree, ExitWorktree, Monitor, TaskStop, SendMessage, Artifact` plus all MCP tools; every other built-in is removed **with no error**. Forks skip both filters.

**Three facts that change how governance must be written:**

1. **`SubagentStart` cannot block** — the hooks table reads "No — shows stderr to user only." It supports `additionalContext` injection and nothing else, so pre-spawn enforcement must be `PreToolUse` on the `Agent` tool (now VERIFIED to fire, §9).
2. **Workflow subagents always run `acceptEdits`** and inherit the tool allowlist regardless of session mode. Settings-file hooks still fire inside subagents, so the Change Control write-gate holds — but the *permission* layer does not.
3. **Every built-in and custom subagent loads the full CLAUDE.md hierarchy plus a git-status snapshot.** `Explore` and `Plan` are the only exemptions and **there is no frontmatter field or per-agent setting to change that.** Measured locally: **486 lines / 32,564 B / ~8.1k tokens per agent** — roughly 244k tokens of preamble across a 30-agent fan-out, before any work.

**Agent identities reachable: 25** — 6 built-in (`Explore`, `Plan`, `general-purpose`, `claude`, `statusline-setup`, `claude-code-guide`), 16 custom (all now `model` + `effort` pinned), 2 plugin (`architects:*`, which **ignore `permissionMode`, `hooks`, and `mcpServers`**), plus `fork`. Frontmatter offers **16 fields**; this framework previously used 5.

**Version-gated limits on the verified 2.1.214 build:** session subagents 200 (active) · concurrent 20 (**absent until 2.1.217, and ultracode-exempt thereafter**) · nesting depth **5 and uncappable** (env var 2.1.217+, default 3 at 2.1.219) · workflow concurrency min(16, cores−2) · 1,000 agents/run · 4,096 items per `parallel`/`pipeline`. Workflow `agent()` calls do not count against the session limit; Agent-tool spawns *inside* a workflow do.

Full matrix, per-vector hazards, and the complete field reference: **`Agent-Swarm-Governance_2026-08-06/Agent-Spawn-Surface-Taxonomy_2026-08-06.md`**. Operational entry point: **`/swarm-plan`**. Hot layer: the **`agent-swarm-doctrine`** skill.

---

**Changelog**
- v1.6 (2026-09-23): Tier pins updated per owner ruling 2026-09-23 (permissions-review session d873b659): T2 judge `claude-opus-5-5`/xhigh (was `opus`/high), T3 worker `sonnet`/high (was medium), T5 final audit `claude-fable-5-1`/xhigh (was `claude-fable-5`); the specialist agents the taxonomy files under T2 (database-architect, gtm-workflow-architect, skill-ecosystem-auditor) and T3 (docx-engineer) take the same pins; the Topology C driver references move to `claude-opus-5-5`, matching settings.json since 2026-09-22. Cascade: agent-swarm-doctrine v1.1, research-swarm skill v1.6, research-swarm.js v1.3, /swarm-plan, both pin-gate hooks (text only), seven agent definitions, prompt template v1.2, taxonomy v1.1, diagram, RESUME-HERE v1.5, project memory, skill-dependencies v3.7 and the swarm-pin memory note. Historical and evidence references (WORKLOG entries, pin-test records, incident attributions, ledger provenance, older changelog lines) stay as written. The v1.5 header change of 2026-09-04 has no line in this changelog.
- v1.4 (2026-08-06): **All-vector expansion.** The pin invariant extended from workflow `agent()` calls to all seven spawn vectors (new §11), after a scrub of 10 official Anthropic sources established that the framework governed 1 of 7 and that four parallel-agent surfaces exist as peers. Added: §4.1 sizing ladder (Anthropic's own effort ladder + the ~15× / 80%-variance figures) · standing rules 13–18 · §2 corollary corrected for the v2.1.222 family-alias allowlist substitution · §6 inventory +6 artifacts · §8 six new/updated risk rows (interactive-Agent residual **CLOSED**) · §9 four new verification rows + §9.1 the three gate defects that pre-write verification caught. Shipped: `pre-agent-pin-gate.py` (PreToolUse on `Agent`, 16/16, live-verified) · `settings.json` (`Agent(*)` removed, `Agent(model:*)` + 16 named allows, 129→145 rules) · `/swarm-plan` · `agent-swarm-doctrine` skill · roster hardened to 16/16 effort-pinned and strict-YAML valid · `research-swarm` skill → v1.4 (re-scoped as a specialization). **owner rulings:** `maxTurns` omitted entirely — a silent cap was judged worse than an unbounded agent (rule 5 forbids silent truncation), so agents are bounded in the prompt instead; agent teams remain a **per-run** launch-flag opt-in, never in `settings.json` `env`, because they break `/resume`; the end-to-end `/research-swarm` acceptance run stays **deliberately separate** so governance is proven before a full run is spent — §9 still reads UNKNOWN and the status line says so.
- v1.3.3 (2026-08-02): Seat policy adopted (mirrored in research-swarm skill v1.3.2): Topology-C outputs require a Fable acceptance pass before being treated as true; Opus never drives unsupervised state-assertion-heavy sessions. Basis: the 2026-08-01/02 driver-seat state-assertion incidents (7 instances vs 0/70 pinned subagents).
- v1.3.2 (2026-08-01, later): Driver rerouted `claude-opus-4-8` → `claude-opus-5` (the owner decision; settings.json + all 12 normative doc sites; historical/verbatim references deliberately untouched — WORKLOG entries, Prompt.md, pin-test records, changelog history stay as written). Rationale: fast-mode differentiator stale (available on Opus 5), newer cutoff, judges already on Opus 5 via alias; closing grep proves only historical/factual hits remain.
- v1.3.1 (2026-08-01): Rule-12 adoption policy locked (the owner decision after lift/risk advisory): living docs get retrofitted frontmatter, closed/verified records stay grandfathered. Executed on both legacy projects — the first (WORKLOG v1.2, RESUME v2, Design-Spec v1.1 → enforced, exempt list narrowed 14→11, validator PASS 0/0) and the second (WORKLOG v1.0, RESUME v5). Pre-retrofit rescan found no new materials; one image-embed scratch note flagged to the owner.
- v1.3 (2026-07-27): Topic-routing rule 12 per the owner directive — one topic = one subdirectory inheriting the framework by default; framework home declared docs-only; `/swarm-init --adopt` mode added for pre-framework projects (backfill-only, legacy docs grandfathered pending the owner's retrofit decision); skill v1.3 `out_dir` wording fixed (was ambiguously "vault folder"); template v1.1 §8 PARENT field + sub-topic nesting; an earlier project adopted as the first inheritance.
- v1.2 (2026-07-27, later): Structure enforcement layer added per the owner gap-call ("no commands for structured outputs, frontmatter, or directory setup" — confirmed): standing rule 11; `/swarm-init` scaffold command; 7-key frontmatter standard wired into roster + workflow prompts + fable audit; `validate-swarm-outputs.py` lint (live-tested PASS on this folder); pin-gate v1.1 adds a `schema:` warning; **Optimal Research Prompt Template** added (12-section anti-drift input contract + filled example + failure-mode map). This project's own docs retrofitted with frontmatter (dogfood).
- v1.1 (2026-07-27, later): Topology inverted per owner ruling — **A′ (Fable-driven) is the default**: Fable 5 analyzes the prompt, designs the swarm configuration, and sends the command, with all subagents pinned down-tier; Topology C demoted to locked-plan overnight economy variant. §0/§3.2 T0–T1 rows/§3.3/§7 updated. Rationale: the remedy was never "don't drive from Fable," it was "don't let subagents inherit Fable" — now hook-enforced.
- v1.0 (2026-07-27): Initial. Evidence transcribed from the image-only source docx; root cause triple-confirmed; four layers designed, installed, and verified per §9; Topology C + Opus 4.8 driver + Opus 5 judges + enforcement hook locked by the owner decision (session of 2026-07-27). First production `/research-swarm` run pending (acceptance test).
