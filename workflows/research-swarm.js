// research-swarm — canonical model-tiered research workflow
//
// ── VERSION SERIES (D109 / F73). READ THIS BEFORE COMPARING ANY TWO VERSION NUMBERS. ──
// FOUR independent series describe this framework. They are NOT comparable to each other,
// and F27 was filed on exactly that mistake: it read the script as "trailing" the skill by
// two minor versions, when the two numbers count different things entirely.
//
//   1. THIS FILE  ............ v1.3 (2026-09-23)  — revisions of the executable workflow
//   2. research-swarm SKILL ... v1.6 (2026-09-23)  — revisions of the skill document
//   3. Fable5-UC Blueprint ... v1.6 (2026-09-23)  — revisions of the design SSOT
//   4. hook citations ........ "research-swarm v1.3.2" in opus-driver-protocol.sh — a
//                              PROVENANCE citation naming the version that introduced the
//                              seat policy, deliberately NOT a current-version claim.
//
// Rules: never infer staleness from one series against another. A lower number here does not
// mean this file trails anything. Ask instead whether the BEHAVIOUR is present — for the seat
// policy it is (Fable acceptance pass via agentType 'swarm-auditor' at model claude-fable-5-1 /
// effort xhigh, the CLD-C012 frozen-plan owner gate, and explicit model+effort pins on every
// agent() call per CLD-C015).
//
// CAUTION: this file's header may read ahead of git. As of 2026-08-24 the v1.1 feature below
// was written but NEVER COMMITTED — git HEAD still holds v1.0. A version claim taken from git
// therefore disagrees with the file on disk. That gap is part of what F73 was chasing.
// Blueprint + runbook: docs/ (blueprint v1.4; moved here
//   from an earlier location)
// Tier matrix: helpers=haiku/low · workers=sonnet/high · judges=claude-opus-5-5/xhigh · final audit=claude-fable-5-1/xhigh (owner ruling 2026-09-23).
// INVARIANT: every agent() call pins model + effort explicitly. Nothing inherits the session
// model (enforced by ~/.claude/hooks/workflow-model-pin-gate.py).
// v1.3 | 2026-09-23: TIER PINS per owner ruling 2026-09-23: worker sonnet/high, judge claude-opus-5-5/xhigh,
//   auditor claude-fable-5-1/xhigh; the preflight now expects the judge and auditor VERSIONS (opus-5-5,
//   fable-5-1), so a silent fallback to an older version aborts the run instead of passing on the family name.
// v1.2 | 2026-09-04: LOSSLESS VERIFY RECORD. Both verify stages now survive into the claims table: the adjudicate
//   thunk carries `refuter: v` alongside `verdict: f || v`, the non-contested path carries it too, and claimTable
//   gains refuter_verdict / refuter_evidence / refuter_sources. Before this, `verdict: f || v` discarded the refuter
//   on EVERY adjudicated claim, so the framework's own verified-claims JSON retained only the surviving side of every
//   contested claim — and adjudication is where the value concentrates (run wf_08645a1a-139: 26 of 45 refuted claims
//   contested, adjudicator evidence median 8,084 chars vs refuters' 1,899). Fixes at source what
//   build-verification-record_2026-09-04.py had to reconstruct. Skill rule 2 + blueprint doctrine item 4 amended to
//   match (both v1.5). Related: CLD-C035 (label/phase never reach disk, so stage cannot be recovered either).
// v1.1 | 2026-08-18: +args.pause_before_audit — arg-controlled owner gate AFTER synthesize, BEFORE the
//   fable audit (CLD-C012: gates belong IN the script before launch; a retrofit pause = kill + full tail
//   re-run). Repair stage gets its own REPAIR_SCHEMA (stage:'repair') so journal forensics can distinguish
//   repair from synthesize (schema collision found 2026-08-18, run wf_2559383a-a9c). Deferred: moving
//   fragile schema-heavy calls later in the flow.
// v1.0 | 2026-07-27

export const meta = {
  name: 'research-swarm',
  description: 'Model-tiered research swarm: routing preflight, sonnet gather lenses, sonnet refute + opus adjudicate, opus dossier, single fable final audit',
  whenToUse: 'Heavy research questions needing multi-lens evidence with adversarial verification, without burning the Fable budget on workers. Pass args: {question, out_dir, slug, scope?, lenses?, max_claims_per_lens?, pause_before_audit?}.',
  phases: [
    { title: 'Preflight', detail: 'routing assertion + Fable spend-capacity check; aborts run on failure' },
    { title: 'Gather', detail: 'one sonnet worker per lens, disk-first', model: 'sonnet' },
    { title: 'Verify', detail: 'sonnet refuters; opus adjudication on contested load-bearing claims' },
    { title: 'Synthesize', detail: 'opus writes the dossier + verified-claims digest', model: 'claude-opus-5-5' },
    { title: 'Audit', detail: 'one fable pass over the distilled dossier only', model: 'claude-fable-5-1' },
  ],
}

// ---------- tier matrix (single source of truth inside this script) ----------
const T = {
  helper:  { model: 'haiku',            effort: 'low'   },
  worker:  { model: 'sonnet',           effort: 'high'  },
  judge:   { model: 'claude-opus-5-5',  effort: 'xhigh' },
  auditor: { model: 'claude-fable-5-1', effort: 'xhigh' },
}
const AUDIT_RESERVE_TOKENS = 250000 // never spend the audit's headroom on extra verification

// ---------- args contract ----------
const A = args || {}
if (!A.question || !A.out_dir) {
  return { status: 'ABORTED_ARGS', error: 'research-swarm requires args.question and args.out_dir (absolute, run-unique). Optional: slug, scope, lenses[], max_claims_per_lens, load JSON args rather than prose.' }
}
const SLUG = A.slug || 'run'
const OUT = A.out_dir.replace(/\/+$/, '')
const MAX_CLAIMS = A.max_claims_per_lens || 10
const hasBudget = (typeof budget !== 'undefined') && budget && budget.total
const remaining = () => (hasBudget ? budget.remaining() : Infinity)

const DEFAULT_LENSES = [
  { key: 'landscape',       hint: 'What exists today: products, frameworks, standards, primary documentation.' },
  { key: 'evidence',        hint: 'Quantitative evidence: benchmarks, measured reliability, adoption data — denominators, versions, dates mandatory.' },
  { key: 'counterevidence', hint: 'The strongest case AGAINST the emerging answer: failures, retirements, contradicting sources, absent demand.' },
  { key: 'practices',       hint: 'How practitioners do this today: official guidance vs credible community patterns, clearly separated.' },
]
const lenses = (Array.isArray(A.lenses) && A.lenses.length ? A.lenses : DEFAULT_LENSES)
  .map(l => (typeof l === 'string' ? { key: l, hint: '' } : l))

// ---------- Phase 0: preflight (routing assertion + fable capacity) ----------
// Detects two failure modes before any real spend: (1) enterprise availableModels
// allowlist silently falling a pinned tier back to the inherited (session) model;
// (2) Fable capacity exhausted (the 2026-07-26 event) — the audit tier must be
// confirmed reachable BEFORE workers spend, or the run ends unauditable.
const PIN_SCHEMA = {
  type: 'object',
  properties: { stated_model: { type: 'string' }, self_id: { type: 'string' } },
  required: ['stated_model', 'self_id'],
}
const PIN_PROMPT = 'Use NO tools. Report verbatim the model line from your own system prompt/environment context (e.g. "You are powered by the model named X. The exact model ID is Y") in stated_model, and your best self-identification in self_id. Be literal.'
const pinSpecs = [
  { tier: 'helper',  expect: 'haiku'  },
  { tier: 'worker',  expect: 'sonnet' },
  { tier: 'judge',   expect: 'opus-5-5'  },
  { tier: 'auditor', expect: 'fable-5-1' },
]
const pinRes = await parallel(pinSpecs.map(p => () =>
  agent(PIN_PROMPT, { label: 'preflight:' + T[p.tier].model, phase: 'Preflight', schema: PIN_SCHEMA, model: T[p.tier].model, effort: 'low' })))
const pinFailures = pinSpecs
  .map((p, i) => {
    const r = pinRes[i]
    const id = r ? ((r.stated_model || '') + ' ' + (r.self_id || '')).toLowerCase() : ''
    return { tier: p.tier, requested: T[p.tier].model, ok: !!r && id.includes(p.expect), reported: r ? r.stated_model : 'NO RESPONSE (capacity/limit or error)' }
  })
  .filter(f => !f.ok)
if (pinFailures.length) {
  log('PREFLIGHT FAILED — aborting before any research spend: ' + JSON.stringify(pinFailures))
  return {
    status: 'ABORTED_PREFLIGHT',
    failures: pinFailures,
    note: 'A tier did not route to its pinned model (allowlist silent-fallback or spend limit). Fix routing/capacity, then re-run. Never fan workers onto an unverified tier.',
  }
}
log('Preflight OK: all 4 tiers routed to their pinned models; Fable capacity confirmed.')

// ---------- Phase 1: gather (sonnet workers, disk-first) ----------
const GATHER_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    file_path: { type: 'string' },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string' },
          claim: { type: 'string' },
          source_url: { type: 'string' },
          source_type: { type: 'string', enum: ['primary', 'secondary'] },
          load_bearing: { type: 'boolean' },
          label: { type: 'string', enum: ['VERIFIED', 'REPORTED', 'INFERRED', 'ASSUMED', 'UNKNOWN'] },
        },
        required: ['id', 'claim', 'source_url', 'source_type', 'load_bearing', 'label'],
      },
    },
    dropped_coverage: { type: 'string' },
  },
  required: ['lens', 'file_path', 'claims', 'dropped_coverage'],
}
const gatherRaw = await parallel(lenses.map(l => () =>
  agent(
    'RESEARCH LENS "' + l.key + '" — ' + l.hint + '\n\nQuestion: ' + A.question +
    (A.scope ? '\nScope/constraints: ' + A.scope : '') +
    '\n\nGather evidence for this lens from primary sources (official docs, source repos, first-party announcements; label anything secondary). ' +
    'Write your FULL findings as markdown to ' + OUT + '/raw/gather_' + l.key + '_' + SLUG + '.md (create parent dirs; write nowhere else). ' +
    'The file MUST open with the standard swarm YAML frontmatter block — all 7 keys: title, project: "' + SLUG + '", type: raw-gather, version: v1.0, date: <today>, run_id: n/a, status: draft. ' +
    'Then return structured output: your top claims (max ' + MAX_CLAIMS + ', ids "' + l.key + '-1"…), each with source_url, source_type, load_bearing (would the final answer change if this is wrong?), and a calibration label. ' +
    'dropped_coverage must state exactly what you did not cover and why — "none" only if truly complete. No silent caps.',
    { label: 'gather:' + l.key, phase: 'Gather', schema: GATHER_SCHEMA, agentType: 'swarm-worker', model: T.worker.model, effort: T.worker.effort }
  )))
const gathered = gatherRaw.filter(Boolean)
const gatherFailed = lenses.filter((l, i) => !gatherRaw[i]).map(l => l.key)
if (gatherFailed.length) log('Gather lenses FAILED (will be recorded in dossier limitations): ' + gatherFailed.join(', '))
if (!gathered.length) return { status: 'ABORTED_GATHER', error: 'All gather lenses failed', failed: gatherFailed }

// dedup across lenses before paying for verification (barrier justified: needs all claims)
const seen = new Set()
const claims = []
for (const g of gathered) {
  for (const c of (g.claims || []).slice(0, MAX_CLAIMS)) {
    const key = (c.claim || '').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 80)
    if (!key || seen.has(key)) continue
    seen.add(key)
    claims.push(c)
  }
}
claims.sort((a, b) => (b.load_bearing ? 1 : 0) - (a.load_bearing ? 1 : 0)) // load-bearing verified first
log('Gather complete: ' + gathered.length + '/' + lenses.length + ' lenses, ' + claims.length + ' deduped claims (' + claims.filter(c => c.load_bearing).length + ' load-bearing).')

// ---------- Phase 2: verify (sonnet refute -> opus adjudicate) ----------
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    claim_id: { type: 'string' },
    verdict: { type: 'string', enum: ['CONFIRMED', 'PARTIALLY', 'REFUTED', 'UNVERIFIABLE'] },
    evidence: { type: 'string' },
    sources: { type: 'array', items: { type: 'string' } },
  },
  required: ['claim_id', 'verdict', 'evidence', 'sources'],
}
const verified = []
const unverifiedBudget = []
const BATCH = 8
for (let i = 0; i < claims.length; i += BATCH) {
  if (remaining() < AUDIT_RESERVE_TOKENS) {
    claims.slice(i).forEach(c => unverifiedBudget.push(c.id))
    log('BUDGET GUARD: stopping verification at ' + i + '/' + claims.length + ' to preserve the audit reserve. Unverified (recorded, not silent): ' + unverifiedBudget.join(', '))
    break
  }
  const batch = claims.slice(i, i + BATCH)
  const results = await pipeline(
    batch,
    c => agent(
      'ADVERSARIALLY REFUTE this claim via an INDEPENDENT path (do not just re-read its cited source; find a second primary source, execute a check, or recompute with stated denominators). Do not write any files. Before checking, state what refutation would look like.\n\nClaim [' + c.id + ']' + (c.load_bearing ? ' (LOAD-BEARING)' : '') + ': ' + c.claim + '\nClaimed source: ' + c.source_url,
      { label: 'refute:' + c.id, phase: 'Verify', schema: VERDICT_SCHEMA, model: T.worker.model, effort: T.worker.effort }
    ),
    (v, c) => {
      if (!v) return { claim: c, verdict: null }
      const contested = (c.load_bearing && v.verdict !== 'CONFIRMED') || v.verdict === 'REFUTED'
      if (!contested) return { claim: c, refuter: v, verdict: v }
      return agent(
        'ADJUDICATE a contested claim. Weigh the original evidence against the refuter, verify decisive points yourself via primary sources, and issue the FINAL verdict. Quote both sides where they contradict; never silently choose.\n\nClaim [' + c.id + ']' + (c.load_bearing ? ' (LOAD-BEARING)' : '') + ': ' + c.claim + '\nOriginal source: ' + c.source_url + '\nRefuter verdict: ' + v.verdict + '\nRefuter evidence: ' + v.evidence + '\nRefuter sources: ' + (v.sources || []).join(' | '),
        { label: 'adjudicate:' + c.id, phase: 'Verify', schema: VERDICT_SCHEMA, agentType: 'swarm-judge', model: T.judge.model, effort: T.judge.effort }
      ).then(f => ({ claim: c, refuter: v, verdict: f || v, adjudicated: true }))
    }
  )
  verified.push(...results.filter(Boolean))
}
const verdictCounts = {}
verified.forEach(r => { const v = r.verdict ? r.verdict.verdict : 'NO-VERDICT'; verdictCounts[v] = (verdictCounts[v] || 0) + 1 })
log('Verification: ' + JSON.stringify(verdictCounts) + (unverifiedBudget.length ? ' · ' + unverifiedBudget.length + ' deferred on budget' : ''))

// ---------- Phase 3: synthesize (opus, disk-first) ----------
const SYNTH_SCHEMA = {
  type: 'object',
  properties: {
    dossier_path: { type: 'string' },
    claims_path: { type: 'string' },
    exec_summary: { type: 'string' },
    open_questions: { type: 'array', items: { type: 'string' } },
  },
  required: ['dossier_path', 'claims_path', 'exec_summary', 'open_questions'],
}
const claimTable = verified.map(r => ({
  id: r.claim.id, claim: r.claim.claim, load_bearing: r.claim.load_bearing,
  source: r.claim.source_url, gather_label: r.claim.label,
  final_verdict: r.verdict ? r.verdict.verdict : 'NO-VERDICT',
  verify_evidence: r.verdict ? r.verdict.evidence : 'verifier failed',
  refuter_verdict: r.refuter ? r.refuter.verdict : null,
  refuter_evidence: r.refuter ? r.refuter.evidence : null,
  refuter_sources: (r.refuter && r.refuter.sources) || [],
  adjudicated: !!r.adjudicated,
}))
const synth = await agent(
  'SYNTHESIZE the research dossier.\n\nQuestion: ' + A.question + (A.scope ? '\nScope: ' + A.scope : '') +
  '\n\nInputs: (1) full lens findings at ' + gathered.map(g => g.file_path).join(' , ') + ' — read them; (2) the verified-claims table below (final verdicts are authoritative; a claim REFUTED in verification must not survive into the answer).\n\n' +
  'Write TWO files: (a) the dossier to ' + OUT + '/Dossier_' + SLUG + '.md — opening with the standard swarm YAML frontmatter block (all 7 keys: title, project: "' + SLUG + '", type: dossier, version: v1.0, date: <today>, run_id: n/a, status: verified), then answer-first (verdict/answer in the first paragraph), calibration labels on every load-bearing claim, statistics with denominators, a methodology section (lenses run: ' + gathered.map(g => g.lens).join(', ') + (gatherFailed.length ? '; FAILED lenses: ' + gatherFailed.join(', ') : '') + '), and a limitations section that explicitly lists ' + (unverifiedBudget.length ? 'these budget-deferred unverified claim ids: ' + unverifiedBudget.join(', ') : 'any unverified/failed items') + '; (b) the claims table verbatim as JSON to ' + OUT + '/raw/verified-claims_' + SLUG + '.json.\n\n' +
  'CLAIMS TABLE:\n' + JSON.stringify(claimTable, null, 1),
  { label: 'synthesize', phase: 'Synthesize', schema: SYNTH_SCHEMA, agentType: 'swarm-judge', model: T.judge.model, effort: T.judge.effort }
)
if (!synth) return { status: 'ABORTED_SYNTHESIS', error: 'Synthesizer failed', stats: { lenses: gathered.length, claims: claims.length, verdicts: verdictCounts } }

// v1.1: owner gate — pause AFTER synthesize, BEFORE the fable audit (CLD-C012:
// gates belong IN the script before launch; a retrofit pause = kill + tail re-run).
// The flag never enters an agent prompt, so removing it on the approval resume
// keeps every cache key intact — the gate costs nothing by construction.
if (A.pause_before_audit) {
  return {
    status: 'PAUSED_PRE_AUDIT_HUMAN_GATE',
    dossier: synth.dossier_path,
    claims_digest: synth.claims_path,
    exec_summary: synth.exec_summary,
    open_questions: synth.open_questions,
    stats: {
      lenses_ok: gathered.length, lenses_failed: gatherFailed,
      claims_deduped: claims.length, verdicts: verdictCounts,
      budget_deferred_unverified: unverifiedBudget,
      dropped_coverage_by_lens: gathered.map(g => ({ lens: g.lens, dropped: g.dropped_coverage })),
    },
    next: 'On owner approval: resume with resumeFromRunId and pause_before_audit removed — the prefix replays from cache, only the audit runs live.',
  }
}

// ---------- Phase 4: final audit (fable, dossier only, one repair round max) ----------
const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['SHIP', 'FIX', 'REJECT'] },
    findings: { type: 'array', items: { type: 'string' } },
    required_fixes: { type: 'array', items: { type: 'string' } },
  },
  required: ['verdict', 'findings', 'required_fixes'],
}
// v1.1: repair returns the synth fields + a literal stage marker so journal
// forensics can tell a repair from a synthesize (identical field sets otherwise).
const REPAIR_SCHEMA = {
  type: 'object',
  properties: {
    dossier_path: { type: 'string' },
    claims_path: { type: 'string' },
    exec_summary: { type: 'string' },
    open_questions: { type: 'array', items: { type: 'string' } },
    stage: { type: 'string', enum: ['repair'] },
  },
  required: ['dossier_path', 'claims_path', 'exec_summary', 'open_questions', 'stage'],
}
const auditPrompt = (round) =>
  'FINAL AUDIT (round ' + round + '). Read ONLY these two files: ' + synth.dossier_path + ' and ' + synth.claims_path +
  '. Run the full five-question audit protocol from your role definition and the mimic scan. Also verify the dossier opens with the standard swarm YAML frontmatter (title, project, type, version, date, run_id, status) — missing or incomplete frontmatter = FIX. Original question for CONTRACT check: ' + A.question +
  '. Return SHIP, FIX (itemized minimal fixes), or REJECT (failed premise named).'
let audit = await agent(auditPrompt(1), { label: 'audit:fable-r1', phase: 'Audit', schema: AUDIT_SCHEMA, agentType: 'swarm-auditor', model: T.auditor.model, effort: T.auditor.effort })
let repairApplied = false
if (audit && audit.verdict === 'FIX') {
  log('Audit verdict FIX — one repair round (two-attempt cap): ' + audit.required_fixes.join(' | '))
  const repair = await agent(
    'REPAIR the dossier at ' + synth.dossier_path + ' by applying EXACTLY these audit fixes (append a changelog line "v1.1 — post-audit repairs" at the top; change nothing else): \n- ' + audit.required_fixes.join('\n- ') + '\nReturn {dossier_path, claims_path, exec_summary, open_questions, stage:"repair"} with the same paths.',
    { label: 'repair', phase: 'Audit', schema: REPAIR_SCHEMA, agentType: 'swarm-judge', model: T.judge.model, effort: T.judge.effort }
  )
  repairApplied = !!repair
  if (repair) {
    audit = await agent(auditPrompt(2), { label: 'audit:fable-r2', phase: 'Audit', schema: AUDIT_SCHEMA, agentType: 'swarm-auditor', model: T.auditor.model, effort: T.auditor.effort })
  }
}

// ---------- result ----------
return {
  status: audit ? (audit.verdict === 'SHIP' ? 'SHIPPED' : (audit.verdict === 'FIX' ? 'FIX_UNRESOLVED_HUMAN_GATE' : audit.verdict)) : 'UNAUDITED_HUMAN_GATE',
  dossier: synth.dossier_path,
  claims_digest: synth.claims_path,
  exec_summary: synth.exec_summary,
  open_questions: synth.open_questions,
  audit: audit || 'fable auditor failed — treat dossier as UNAUDITED',
  repair_applied: repairApplied,
  stats: {
    lenses_ok: gathered.length, lenses_failed: gatherFailed,
    claims_deduped: claims.length, verdicts: verdictCounts,
    budget_deferred_unverified: unverifiedBudget,
    dropped_coverage_by_lens: gathered.map(g => ({ lens: g.lens, dropped: g.dropped_coverage })),
  },
  next: 'Main session: append WORKLOG entry; surface exec_summary + open_questions + any FIX/REJECT findings to the owner.',
}
