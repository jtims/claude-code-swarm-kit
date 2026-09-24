#!/usr/bin/env python3
"""usage-guard.py: the deterministic half of the /usage-guard command (the browser reads are MCP tool calls the
driver makes; this script owns config, logging, rate/ETA arithmetic and the PAUSE/WARN/HOLD decision).

Subcommands
  config --project P [--workflow-task ID] [--run-id R] [--label L] [--stage-monitor ID] [--reexport-loop ID]
         [--tick-monitor ID] [--pause-script PATH] [--threshold 95] [--interval 150] [--screenshot-every 2]
         [--usage-url URL] [--tab-id N]
      writes/updates <P>/Research/raw/usage-monitor/guard-config.json (only the keys given) and prints it.
  log --project P --pct N --resets TEXT --weekly N --fable N --updated TEXT
      [--run-started N --run-results N --run-nulls N] [--screenshot ID] [--note TEXT]
      appends a CSV row to <P>/Research/raw/usage-monitor/usage-log_<date>.csv, computes the burn rate (percent per
      minute over up to the last 3 readings) and the ETA to the threshold, and prints JSON with
      decision = PAUSE (pct >= threshold) | WARN (projected to cross before the next tick; tighten the interval) | HOLD.
  show --project P
      prints the config and the last 5 log rows.
Never stops anything. The driver acts on the decision: PAUSE -> run the pause script, verify CAPTURE COMPLETE, then
TaskStop the workflow task, then the monitors and loops listed in the config, then the WORKLOG pause entry.
v1.0 | 2026-09-04 | owner instruction (verbatim): "build a script to carry this out automatically when I invoke it"
"""
import argparse, csv, json, os, sys, time

def cfg_path(p): return os.path.join(p, 'Research', 'raw', 'usage-monitor', 'guard-config.json')
def log_path(p): return os.path.join(p, 'Research', 'raw', 'usage-monitor', f"usage-log_{time.strftime('%Y-%m-%d')}.csv")
COLS = ['time', 'session_pct', 'session_resets_in', 'weekly_all_pct', 'fable_pct', 'page_last_updated',
        'run_agents_started', 'run_results', 'action']

def load_cfg(p):
    f = cfg_path(p)
    return json.load(open(f)) if os.path.exists(f) else {}

def cmd_config(a):
    os.makedirs(os.path.dirname(cfg_path(a.project)), exist_ok=True)
    c = load_cfg(a.project)
    for k in ('workflow_task', 'run_id', 'label', 'stage_monitor', 'reexport_loop', 'tick_monitor', 'pause_script',
              'threshold', 'interval', 'screenshot_every', 'usage_url', 'tab_id'):
        v = getattr(a, k, None)
        if v is not None: c[k] = v
    c.setdefault('threshold', 95); c.setdefault('interval', 150); c.setdefault('screenshot_every', 2)
    c.setdefault('usage_url', 'https://claude.ai/new#settings/usage')
    c['updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
    json.dump(c, open(cfg_path(a.project), 'w'), indent=1)
    print(json.dumps(c, indent=1))

def read_rows(p):
    f = log_path(p)
    if not os.path.exists(f): return []
    return [r for r in csv.DictReader(open(f)) if r.get('session_pct', '').strip().isdigit()]

def cmd_log(a):
    c = load_cfg(a.project); thr = int(c.get('threshold', 95)); interval = int(c.get('interval', 150))
    f = log_path(a.project); new = not os.path.exists(f)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    now = time.strftime('%H:%M')
    prev = read_rows(a.project)
    decision = 'PAUSE' if a.pct >= thr else 'HOLD'
    # burn rate over up to the last 3 prior readings (percent per minute)
    rate = None
    pts = [(r['time'], int(r['session_pct'])) for r in prev[-3:]] + [(now, a.pct)]
    if len(pts) >= 2:
        def mins(t): h, m = t.split(':'); return int(h) * 60 + int(m)
        dt = mins(pts[-1][0]) - mins(pts[0][0]); dp = pts[-1][1] - pts[0][1]
        if dt > 0: rate = round(dp / dt, 2)
    eta_min = None
    if rate and rate > 0 and a.pct < thr: eta_min = round((thr - a.pct) / rate, 1)
    if decision == 'HOLD' and eta_min is not None and eta_min * 60 <= interval: decision = 'WARN'
    action = a.note or (f"{decision}" + (f"; rate {rate}%/min; ETA to {thr}% {eta_min} min" if rate is not None else '') +
                        (f"; screenshot {a.screenshot}" if a.screenshot else ''))
    row = dict(zip(COLS, [now, a.pct, a.resets, a.weekly, a.fable, a.updated, a.run_started, a.run_results, action]))
    with open(f, 'a', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        if new: w.writeheader()
        w.writerow(row)
    out = {'time': now, 'pct': a.pct, 'threshold': thr, 'decision': decision, 'rate_pct_per_min': rate,
           'eta_to_threshold_min': eta_min, 'interval_s': interval, 'run_nulls': a.run_nulls, 'log': f,
           'next': ({'PAUSE': 'run pause_script; on CAPTURE COMPLETE TaskStop workflow_task, then stage_monitor, reexport_loop, tick_monitor; then WORKLOG pause entry',
                     'WARN': 'threshold likely crossed before the next tick: re-arm the tick monitor at 60s (or read again now); PAUSE only at >= threshold',
                     'HOLD': 'nothing; next tick'}[decision]),
           'config': {k: c.get(k) for k in ('workflow_task', 'stage_monitor', 'reexport_loop', 'tick_monitor', 'pause_script', 'run_id')}}
    print(json.dumps(out))
    sys.exit(0)

def cmd_show(a):
    print(json.dumps(load_cfg(a.project), indent=1))
    for r in read_rows(a.project)[-5:]: print(r)

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('config'); c.add_argument('--project', required=True)
    for k in ('workflow_task', 'run_id', 'label', 'stage_monitor', 'reexport_loop', 'tick_monitor', 'pause_script', 'usage_url'):
        c.add_argument('--' + k.replace('_', '-'), dest=k)
    for k in ('threshold', 'interval', 'screenshot_every', 'tab_id'):
        c.add_argument('--' + k.replace('_', '-'), dest=k, type=int)
    c.set_defaults(fn=cmd_config)
    l = sub.add_parser('log'); l.add_argument('--project', required=True); l.add_argument('--pct', type=int, required=True)
    l.add_argument('--resets', default=''); l.add_argument('--weekly', type=int, default=None); l.add_argument('--fable', type=int, default=None)
    l.add_argument('--updated', default=''); l.add_argument('--run-started', dest='run_started', type=int, default=None)
    l.add_argument('--run-results', dest='run_results', type=int, default=None); l.add_argument('--run-nulls', dest='run_nulls', type=int, default=None)
    l.add_argument('--screenshot', default=None); l.add_argument('--note', default=None); l.set_defaults(fn=cmd_log)
    s = sub.add_parser('show'); s.add_argument('--project', required=True); s.set_defaults(fn=cmd_show)
    a = ap.parse_args(); a.fn(a)

if __name__ == '__main__': main()
