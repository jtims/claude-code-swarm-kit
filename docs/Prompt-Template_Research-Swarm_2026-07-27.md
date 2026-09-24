---
title: Optimal Research Prompt Template — Fable 5 Ultracode Swarm
project: Fable5-Ultracode-Swarm_2026-07-27
type: template
version: v1.2
date: 2026-07-27
run_id: n/a
status: shipped
---

# Optimal Research Prompt Template (Fable 5 Ultracode)

**Purpose:** the input contract for heavy research tasks under the swarm blueprint. Filling this template IS the Topology A′ planning phase — the Fable session refines it with you interactively, and nothing fans out until it is locked. Every section exists because a specific, documented failure happened without it (§ "Why each section exists").

**How to use:** `/swarm-init <Project-Name>` scaffolds the folder and seeds `Prompt.md` from this skeleton. Fill every field; mark unknowns `TBD-OWNER` (a `TBD-OWNER` in §§1, 4, or 8 blocks launch). Short beats vague: one precise sentence outranks a paragraph of adjectives. When locked, the Fable session launches `/research-swarm` with args derived from §§1, 4, 6, 8, 10.

---

## THE TEMPLATE (copy from here)

```markdown
# 1 · CONTRACT
CORE QUESTION (one sentence, the thing that must be answered):
<...>

VERBATIM ASK (paste your words exactly — this is the drift anchor the session
re-reads at every phase boundary; edits to it are re-confirmations, not memory):
<...>

DELIVERABLES (numbered; the run must map every item to an output or an explicit
"dropped because X"):
1. <e.g., landscape dossier in the vault>
2. <e.g., inline executive summary>
3. <...>

# 2 · REQUEST TYPE & DECISION CONTEXT
TYPE: research-question | build-feasibility | landscape | decision-support
DECISION THIS INFORMS: <what you will do differently based on the answer>
READER(S): <owner only / leadership / team — sets the dossier's altitude>
BY WHEN (goal, not a quality trade): <date or "none">

# 3 · CONTEXT & PRIOR ART (prevents re-derivation)
ALREADY KNOWN / ALREADY DECIDED (do not re-litigate):
- <decision + where it's recorded>
RELEVANT VAULT DOCS (paths):
- <...>
RELATED PRIOR RUNS: <project folders, if any>

# 4 · SCOPE FENCES
IN SCOPE (each item names WHO put it in scope — "the owner, this prompt" counts;
"the agent suggested it" does not):
- <surface/system/topic — authorized by the owner>
EXPLICITLY OUT OF SCOPE (the fence the 2026-07-27 overreach needed):
- <e.g., production app configurations; any repo not named above>
READ-ONLY BOUNDARIES: <repos/systems agents may read but never act on>
SENSITIVE MATERIAL RULE: name any 1-on-1s/comp/personnel docs surfaced by
sweeps in the same turn they are read; never quote them into outputs.

# 5 · LOAD-BEARING PREMISES TO TEST (claims, not instructions)
I believe the following — VERIFY each before building on it; refute freely:
- P1: <e.g., "no vendor does X today">
- P2: <...>

# 6 · DECOMPOSITION & LENSES
KILL-SHOT QUESTION (the check whose failure invalidates the most — run first):
<...>
LENSES (or "designer's choice — justify in the plan"; default 4:
landscape / evidence / counterevidence / practices):
- <lens: bounded question it answers + its stopping condition>

# 7 · EVIDENCE BAR
- Primary sources only for load-bearing claims (official docs > source repos >
  first-party posts); secondary sources labeled as such.
- Every statistic carries its denominator; every benchmark its version + date.
- Calibration labels mandatory: VERIFIED / REPORTED / INFERRED / ASSUMED /
  UNKNOWN. Prose confidence never exceeds the label. UNKNOWN beats a guess.
- ADVERSARIAL VERIFICATION DEPTH: <all claims | load-bearing only (default) |
  named claims: ...>

# 8 · DELIVERABLES SPEC
PARENT (rule 12 — one topic, one subdirectory): <parent>/ (default) |
<explicit other parent for other topics, owner-directed>
OUT_DIR: <THIS topic's project folder>/Research — never the framework home,
never another topic's folder. Sub-topics nest: Research/<Sub-Topic>_<date>/.
FILES: Dossier_<slug>.md (answer-first; limitations section lists every failed
lens, deferred claim, and coverage cap — no silent caps) + raw/ digests.
FRONTMATTER: standard 7-key block on every .md (blueprint rule 11).
NAMING: [Name]_YYYY-MM-DD(_vN).ext.
FORMAT NOTES: <tables? exec length? artifact mirror?>

# 9 · STOPPING CONDITIONS
PER-LENS: <e.g., "stop at 10 claims or 2 consecutive empty search angles">
OVERALL DONE = every §1 deliverable shipped or explicitly dropped, audit
verdict issued, WORKLOG entry appended.
DO-NOT-CROSS: two failed fix attempts on the same defect → halt and present
options; never a silent third.

# 10 · BUDGET & TIERING
TOPOLOGY: A′ (this Fable session drives) | C (freeze plan, Opus executes)
TOKEN BUDGET: <e.g., "+800k" | "none — judgment"> · FABLE RATION: main loop
+ one audit per run, nothing else.
TIER PINS: helpers=haiku/low · workers=sonnet/high · judges=claude-opus-5-5/xhigh ·
audit=claude-fable-5-1/xhigh (deviations require a stated reason here).
PREFLIGHT: routing + Fable-capacity assertion runs first; ABORT on failure.

# 11 · GATES & DECISION RIGHTS
HALT FOR THE OWNER AT: <e.g., "after landscape, before feasibility"; audit FIX/REJECT
always halts>. PRE-AUTHORIZED: <e.g., "writes inside this project folder">.
EVERYTHING ELSE: Change Control applies.
INCIDENTAL FINDINGS: one labeled line in the deliverable, no action, no tasks.

# 12 · FAILURE & RESUMPTION
On spend/capacity casualties: preserve journals to Research/raw/, log exact
losses in WORKLOG (what is re-runnable vs lost), stage a resumption kit
(RESUME-HERE + continuation args). Never mark REPORTED-only work as verified.
```

---

## Filled example (illustrative)

```markdown
# 1 · CONTRACT
CORE QUESTION: Does a production-grade "signal-based outbound orchestration"
platform exist that the organization could adopt instead of building on n8n?
VERBATIM ASK: "Find out if we should buy or build signal-based outbound —
what exists, what it costs, what breaks — before the Q4 planning cycle."
DELIVERABLES: 1. Landscape dossier (vault) · 2. Buy-vs-build verdict with
labeled evidence · 3. Inline exec summary for CRO readout.

# 2 · TYPE & DECISION: landscape + decision-support; informs Q4 build-vs-buy;
readers the owner + VP RevOps; goal 2026-08-15 (goal, not a quality trade).

# 3 · PRIOR ART: 6sense + HubSpot already licensed (do not re-evaluate as
new vendors); gtm-workflows skill catalogs current n8n patterns.

# 4 · SCOPE FENCES
IN (the owner, this prompt): vendor landscape; pricing pages; integration surface
vs Salesforce/HubSpot/6sense; n8n build-cost comparison.
OUT: reading any the organization production instance/config; contract negotiations;
any vendor demo signups. READ-ONLY: existing n8n workflow exports.

# 5 · PREMISES TO TEST
P1: "No vendor covers intent-signal → sequenced outbound end-to-end without
an SDR seat model." P2: "n8n build would need ~3 integrations we own."

# 6 · KILL-SHOT: if P1 is false (a vendor DOES cover it end-to-end), the
build case collapses — verify P1 first.
LENSES: vendor-landscape / pricing-and-packaging / integration-fit /
build-cost-counterfactual.

# 7 · EVIDENCE BAR: defaults + adversarial depth = load-bearing only.
# 8 · DELIVERABLES SPEC: out_dir .../Signal-Outbound_2026-08-01/Research;
defaults apply.
# 9 · STOPPING: 10 claims/lens or 2 empty angles; DONE per §1.
# 10 · BUDGET: Topology A′; +600k; standard pins; preflight-or-abort.
# 11 · GATES: halt after landscape verdict, before build-cost deep dive.
Pre-authorized: writes in this project folder only.
# 12 · FAILURE: standard resumption kit.
```

---

## Why each section exists (failure-mode map — all documented events)

| § | Prevents | The receipt |
|---|---|---|
| 1 CONTRACT | Answering a nearby easier question; deliverables silently dropped | Frontier rule 1; contract-diff pre-send |
| 2 TYPE | Misreading a question as a build order (or vice versa) | Frontier rule 1 request-type classification |
| 3 PRIOR ART | Re-deriving settled decisions; contradicting locked specs | the "do not re-litigate" list pattern |
| 4 SCOPE FENCES | Scope overreach — the 2026-07-27 production-repo audit that was never authorized | `feedback_scope_authorization_discipline`; an earlier project's process-failure entry |
| 5 PREMISES | Premise-following: building on an untested assertion | Frontier rule 2; two recon claims in an earlier project were REFUTED by critics |
| 6 KILL-SHOT / LENSES | Token burn on downstream work a first check would invalidate; unbounded grep-sweep remits | "10000% token burner without a spec"; bounded-questions rule |
| 7 EVIDENCE BAR | Fluent guesses; unlabeled confidence; the OSWorld "7× improvement" arc that failed verification | earlier re-verification corrections |
| 8 DELIVERABLES SPEC | Unstructured outputs, missing frontmatter, wrong locations | This turn's the owner gap-call; blueprint rule 11 |
| 9 STOPPING | Runs that never converge; third fix attempts | Hard stops; two-attempt cap |
| 10 BUDGET & TIERING | The 2026-07-26 spend death (7 verifiers killed); Fable inheritance | Blueprint §§1–2; pin gate |
| 11 GATES | Acting on incidental findings; unauthorized work items (`task_e098b984`) | Scope-authorization discipline |
| 12 FAILURE | Losing overnight work; REPORTED-only data read as verified | an earlier loss-ledger + resumption-kit pattern |

**Changelog** — v1.2 (2026-09-23): TIER PINS line updated per owner ruling 2026-09-23 (workers sonnet/high, judges claude-opus-5-5/xhigh, audit claude-fable-5-1/xhigh). v1.1 (2026-07-27): §8 gains PARENT field + rule-12 routing (one topic = one subdirectory; sub-topics nest under the parent's Research/). v1.0 (2026-07-27): initial, per the owner directive for a holistic anti-drift input contract.
