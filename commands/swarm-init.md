---
description: Scaffold a research-swarm project subdirectory (Prompt/WORKLOG/RESUME-HERE/Research, standard frontmatter) or adopt an existing project folder into the framework (--adopt), then emit pre-filled /research-swarm args
---

# /swarm-init — research project scaffold / adopt

Scaffold or adopt a research-swarm project per the Fable5-UC Swarm Blueprint (v1.4, `docs/` — that folder is the framework's DOCS-ONLY home; research output is never written there). Input: `$ARGUMENTS` = project name (optional one-line question after `--`), or `--adopt <existing folder path>`. Examples: `/swarm-init Vendor-Consolidation -- which workflow vendors overlap?` · `/swarm-init --adopt "<vault>/<Existing-Project>"`

**Topic routing rule (standing rule 12):** one topic = one subdirectory under `<vault>/` (template §8 may name a different parent). Same WORKLOG lineage → same folder; a new question with its own deliverable → a new folder. Never mix topics.

## Procedure

1. **Derive names.** `PROJECT = <Kebab-Name>_<YYYY-MM-DD>` (today's date; naming per file conventions — hyphens in words, underscores between segments, no spaces). `SLUG = <kebab-name lowercase>`.
2. **Target folder:** `<vault>/<PROJECT>/`. **If it already exists, STOP and report — never touch an existing folder.**
3. **Create** (Change Control: state the plan, then create on approval unless the owner pre-authorized this init):
   - `<PROJECT>/Research/raw/` and `<PROJECT>/Research/Workflow-Scripts/`
   - `Prompt.md` — from the **Optimal Research Prompt Template** (`docs/Prompt-Template_Research-Swarm_2026-07-27.md`): copy the skeleton, fill what the owner has provided, mark every unfilled field `TBD-OWNER`. the owner's ask goes in VERBATIM once given.
   - `WORKLOG_<Kebab-Name>.md` — header: living cross-session record note, newest-entry-at-top rule, companion-file list, `**Version:** v1.0 | Created <date>`.
   - `RESUME-HERE_<PROJECT>.md` — status STUB, pointer to Prompt.md + WORKLOG, quick-verify checklist.
   - Every created .md opens with the standard swarm frontmatter block (all 7 keys required):

   ```yaml
   ---
   title: <human title>
   project: <PROJECT>
   type: worklog | resume | spec | dossier | digest | raw-gather | template
   version: v1.0
   date: <YYYY-MM-DD>
   run_id: n/a
   status: draft
   ---
   ```

4. **Validate:** run `python3 ~/.claude/hooks/validate-swarm-outputs.py "<full path to PROJECT>"` — must PASS before reporting done.
5. **Emit the launch block** (do not run it — the owner launches when the Prompt.md contract is locked):

   ```
   /research-swarm {"question": "<from Prompt.md CONTRACT>", "out_dir": "<PROJECT abs path>/Research", "slug": "<SLUG>", "scope": "<from SCOPE FENCES>", "max_claims_per_lens": 10}
   ```

6. **Report:** folder tree created, validator result, the launch block, and what remains `TBD-OWNER` in Prompt.md.

## Adopt mode (`--adopt <existing folder>`)

Attaches the framework to a pre-existing project folder WITHOUT touching its content:

1. **Never overwrite or edit any existing file.** Backfill only what is missing: `Research/raw/`, `Research/Workflow-Scripts/`, `RESUME-HERE_<name>.md` (stub, frontmattered) if absent, `Prompt.md` (template skeleton) if absent.
2. **Split legacy docs (the owner policy, 2026-08-01):** RETROFIT the *living* docs — WORKLOG, RESUME-HERE, and any deliverable still awaiting sign-off — by prepending the 7-key frontmatter (values mirror the doc's own header: its version, its creation/snapshot date; status per its real state; run_id n/a). GRANDFATHER everything closed/verified via `.frontmatter-exempt` at the project root (relative paths, one per line) — never churn frozen evidentiary records. New files created after adoption are NOT exempt — the framework applies by default from adoption forward.
3. Run `python3 ~/.claude/hooks/validate-swarm-outputs.py "<folder>"` — must PASS (warnings on legacy naming are acceptable; record them).
4. Append a dated adoption entry to the project's WORKLOG.
5. Emit the launch block with `out_dir` = `<folder>/Research` — all future runs for this topic land HERE, never in the framework home or another topic's folder.
6. Sub-topics: a heavy sub-question inside an adopted/scaffolded project nests at `<folder>/Research/<Sub-Topic>_<YYYY-MM-DD>/` — same lineage, same WORKLOG.

## Rules

- Topology A′ default: this same Fable session refines Prompt.md interactively before any launch. No fan-out before the contract is locked.
- Default parent is `<vault>/`; template §8 PARENT field may direct a topic elsewhere (explicit owner direction required).
- WORKLOG upkeep applies from creation/adoption (first entry: "Project initialized/adopted via /swarm-init").
