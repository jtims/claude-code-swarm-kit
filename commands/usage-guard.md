---
description: 'Guard a running swarm against the claude.ai session usage limit. Reads the usage page in the owner''s Chrome on a fixed tick, screenshots every Nth tick, logs to the project, and at the threshold (default 95 percent) runs the capture-then-stop pause. Args: [threshold] [interval_s]'
argument-hint: '[threshold=95] [interval_s=150]'
---

# /usage-guard $ARGUMENTS

Owner rulings this encodes (2026-09-04, verbatim): "when I say 'pause', you immediately capture all context via scripts, then ONLY then do you shut down the workflow eloquently" and "tie the pause command to when the usage gets to 95%" and "capture screenshot every 5 minutes". Deterministic half: `~/.claude/scripts/usage-guard.py`. Never stop anything before the capture verifies.

## 0. Resolve config
- Project = the mounted swarm project (its `Research/raw/usage-monitor/guard-config.json`). Run `python3 ~/.claude/scripts/usage-guard.py show --project <P>`. If the config lacks `workflow_task`, `run_id`, `pause_script`, ask the owner for them in one question, then write them with `config`.
- Apply `$ARGUMENTS`: first token threshold, second interval seconds; write them with `config --threshold --interval`. Default 95 and 150. Screenshot every `screenshot_every` ticks (default 2, so every 5 minutes at 150 s).

## 1. Open the usage page in the owner's real Chrome (logged-in session)
- `ToolSearch select:mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__tabs_close_mcp` in ONE call.
- `navigate` to `usage_url` (default `https://claude.ai/new#settings/usage`); record the tabId with `config --tab-id`.
- Do not click anything on claude.ai other than the usage refresh icon. Never type into the page.

## 2. Read (every tick), by this exact JavaScript (result keys must not contain the word session; the tool redacts those)

> **v1.2, 2026-09-15.** The usage page relabelled its weekly blocks between 2026-09-05 and 2026-09-15: `All models` became `This week`, and `Fable` became `Fable this week` with a `Separate weekly limit for Fable ·` line before its reset. The v1.1 reader then matched only the session block (Fable Audit, misalignments/M03). The reader below accepts both label sets, each block still matched independently; tested offline against both page texts and against a banner between the blocks.
> **v1.1, 2026-09-05.** The old single-regex reader matched all three blocks in one pass and broke the moment a weekly-boost banner appeared between them, degrading silently to screenshot-reading. It now matches each labelled block independently, so an interstitial banner cannot break it.
```
(() => { const t = document.body.innerText.replace(/\s+/g, ' '); const g = (rx) => { const m = t.match(rx); return m ? { resets: m[1], pct: Number(m[2]) } : null; }; const cur = g(/Current session Resets (?:in |at )?(.*?) (\d+)% used/), all = g(/(?:This week|All models) Resets (?:in )?(.*?) (\d+)% used/), fab = g(/Fable(?: this week)?(?: Separate weekly limit for Fable ·)? Resets (?:in )?(.*?) (\d+)% used/); const upd = (t.match(/Last updated: (.*?)(?: Type| Learn|$)/) || [])[1]; return (cur && all && fab) ? { clock: new Date().toTimeString().slice(0,8), cur_resets_in: cur.resets, cur_pct: cur.pct, weekly_all_pct: all.pct, fable_pct: fab.pct, page_updated: (upd || '').trim() } : { error: 'pattern not found', snippet: (t.match(/Your usage limits.{0,300}/) || [''])[0] }; })()
```
- **Before each read, PRESS the modal's own Refresh control. A reload does NOT refresh the figures.** Measured 2026-09-05: an un-refreshed page reported 10% while the true value was 17%. The control sits below the fold (y=721 in a 694px frame) so it cannot be clicked by coordinate. Press it by label instead, as its own call:
```
(() => { const b = [...document.querySelectorAll('button,[role="button"]')].find(x => (x.getAttribute('aria-label') || '') === 'Refresh'); if (!b) return { clicked: false }; b.click(); return { clicked: true }; })()
```
  then `computer wait 5`, THEN the read above. **Do not combine click, wait and read into one async IIFE: the Chrome JavaScript tool does not await a returned promise and the call resolves to `{}`** (measured 2026-09-05).
- If `error`, take a screenshot and read the number from it; log it with `--note "read from screenshot"`.
- Run counts for the row: `grep -c '"type":"started"'`, `'"type":"result"'`, `'"result":null'` on the run's `journal.jsonl`.
- Log: `python3 ~/.claude/scripts/usage-guard.py log --project <P> --pct <cur_pct> --resets "<cur_resets_in>" --weekly <n> --fable <n> --updated "<page_updated>" --run-started <n> --run-results <n> --run-nulls <n> [--screenshot <id>]`.

## 3. Arm the tick (one Monitor, persistent)
```
i=0; while true; do sleep <interval>; i=$((i+1)); if [ $((i % <screenshot_every>)) -eq 0 ]; then echo "USAGE-TICK $i $(date '+%H:%M') READ + SCREENSHOT"; else echo "USAGE-TICK $i $(date '+%H:%M') READ only"; fi; done
```
Record its task id with `config --tick-monitor`. On every tick: step 2; on a screenshot tick also `computer screenshot` (save_to_disk true) and pass its id to `--screenshot`.

## 4. Act on the decision printed by `log`
- **HOLD**: nothing.
- **WARN** (projected to cross the threshold before the next tick): re-arm the tick at 60 s. Do not pause early; the owner set the threshold.
- **PAUSE** (pct at or above threshold), in this order and no other:
  1. `zsh <pause_script>`; proceed only if it prints `CAPTURE COMPLETE` (it exports the run cache, snapshots the driver session, writes PAUSE-STATE, self-verifies). If it prints CAPTURE INCOMPLETE, fix and re-run; never stop first.
  2. `TaskStop <workflow_task>`.
  3. `TaskStop` the `stage_monitor`, `reexport_loop` and `tick_monitor` from the config.
  4. Append the WORKLOG pause entry: time, usage reading, journal counts, in-flight agents from PAUSE-STATE, the exact same-session resume call (`Workflow({scriptPath, resumeFromRunId})`, CLD-C033), and the fresh-session limitation.
  5. Report to the owner: what was captured, what stopped, when the window resets, and the resume command.

## 5. Stand down
When the workflow completion notification arrives: `TaskStop` the tick monitor, log a final row with `--note "run complete"`, close the Chrome tab with `tabs_close_mcp` unless the owner wants it open.
