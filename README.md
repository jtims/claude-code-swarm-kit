# claude-code-swarm-kit

A model-tiered multi-agent research kit for Claude Code: a pinned agent roster, a five-stage research workflow, two skills that govern every way a subagent can be spawned, four deterministic gates and linters, three commands, and the design document that explains why each piece exists.

## Why it exists

In Claude Code, every agent in a workflow inherits the session's model unless the script routes a stage elsewhere. A research program launched from a frontier-model session therefore spends frontier tokens on sweeps and enumeration, and the most valuable stage, adversarial verification, is the one that dies last when a spend cap engages. The root cause was model inheritance, not context overflow, confirmed three independent ways and recorded in the blueprint. The remedy is per-call model and effort pinning, enforced mechanically rather than by convention.

## The tier matrix

| Tier | Role | Model | Effort | Does |
|---|---|---|---|---|
| T1 | orchestration | the driving session | xhigh or high | authoring, launching, phase synthesis, human gates |
| T2 | judge | `claude-opus-5-5` | xhigh | adjudication, cross-lens synthesis, critique panels |
| T3 | worker | `sonnet` | high | gathering, drafting, extraction, refutation |
| T4 | helper | `haiku` | low | sweeps, enumeration, dedup, formatting, preflights |
| T5 | final audit | `claude-fable-5-1` | xhigh | one pass over a distilled dossier, never raw material |

## What is in it

| Path | Holds |
|---|---|
| `agents/` | `swarm-helper`, `swarm-worker`, `swarm-judge`, `swarm-auditor`, each pinned to its tier's model, effort and tool set, plus an `Explore` override that pins the built-in explorer to haiku and read-only |
| `workflows/research-swarm.js` | The canonical five-stage swarm: preflight (routing assertion and spend-capacity check, aborts before spend), gather (one Sonnet worker per lens), verify (Sonnet refuters, Opus adjudication on contested claims), synthesize (Opus dossier and verified-claims digest), audit (one Fable pass over the distilled dossier) |
| `skills/agent-swarm-doctrine/` | The doctrine for all seven spawn vectors: subagents, dynamic workflows, agent teams, background sessions, forks, batch and nested spawns, with the tool-filter, permission and cost facts that differ per vector |
| `skills/research-swarm/` | The research-run discipline: routing preflight, budget rules, the two-session topology, worklog and evidence conventions |
| `hooks/pre-agent-pin-gate.py`, `hooks/workflow-model-pin-gate.py` | PreToolUse gates that block an unpinned agent or workflow spawn before it runs |
| `hooks/validate-agent-roster.py` | Frontmatter and tier-pin lint for agents and skills, including the harness parsing traps that silently drop a definition's pins |
| `hooks/validate-swarm-outputs.py` | Deterministic structure lint for a research-swarm project folder |
| `commands/` | `/swarm-plan` routes any spawning task to its vector, tier and pins; `/swarm-init` scaffolds or adopts a research project; `/usage-guard` watches the plan's usage meter and runs a capture-then-stop pause at a threshold |
| `scripts/usage-guard.py` | The logger behind `/usage-guard` |
| `docs/` | The blueprint (problem, root cause, architecture, runbook, risk register, verification record, the seven spawn vectors), the spawn-surface taxonomy, and the research prompt template |

## Install

Copy each folder into the matching folder under `~/.claude/`: `agents/`, `workflows/`, `skills/`, `hooks/`, `commands/`, `scripts/`. Register the two PreToolUse hooks in `~/.claude/settings.json` against the Agent and Workflow tools. Never set a global subagent-model override; the pins in the definitions are the mechanism. Run `python3 hooks/validate-agent-roster.py` and require PASS.

## Status, stated plainly

The layers are installed and verified piecewise: the pins resolve, the gates block, the linters catch the documented failure classes, and the workflow's preflight aborts before spend on a routing failure. The full end-to-end production run of `/research-swarm` had not been executed when the blueprint was last revised; the blueprint's verification record says exactly what was and was not run.

## What this demonstrates

- Cost governance as code: model and effort pinned per call, gated before spend, linted after edit.
- Root-cause work: three independent confirmations of a failure mechanism before any fix, and the evidence kept.
- A written doctrine for the whole spawn surface, so the rules apply beyond the one workflow they were learned on.
- Honest verification records: what was executed is separated from what is installed.

## License

MIT. See `LICENSE`.
