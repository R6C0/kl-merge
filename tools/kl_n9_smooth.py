#!/usr/bin/env python3
"""
SMOOTHNESS summary of a multi-seat bench run (n9_1106 and any other kl_solo_test run folder).

    python tools/kl_n9_smooth.py <run> [<run> ...] [--ref <Arcade run>] [--json] [--solo-root <folder>]
    <run> = a tag under <work>/build/klhook/solo/ (N9_DM01e) or a path to a folder holding inst1/ inst2/ ... (each with KLHook.log)

Reads ONLY the KLHook.log / KLHook.result / dump file names of each seat (no game contact) and prints, per seat:
in-round seconds, hitches (count, max ms), slow 10 s windows, netsmooth / sync corrections, pollloss episodes, asserts / faults / dumps,
then one verdict per seat and per run: SMOOTH / HITCHY / FAIL.  Last line: 'RESULT: smooth ...' (exit 1 when any run is FAIL).

WHAT THE HOOK ALREADY LOGS (formats found in klhook/*.c on 2026-11-06, all parsed here)
  core: perf: 301 frames in 10.0 s = 30.0 fps; the hook's tick 0.08 ms a frame (...), ... stutter: 153 frame(s) over 33 ms, the longest 38 ms; ...   klhook.c:1539, every 10 s
  core: hitch 345 ms                      one frame of 120 ms .. 3 s (not a load), at most 6 per 10 s window     klhook.c:1533
  stall watch: the main thread is back after 3.2 s without a frame or a loader step                              klhook.c:1553
  stall: window message 000f ... took 25.3 ms ...                       [Stall] Trace, messages >= 20 ms                klhook.c:1058
  hitch probe: 1 hitch(es), 141 sample(s); the main thread stood at: ...                                        klhook.c:1608 (where, not how long: only counted)
  fps: limiter: 40 presents in 59.5 s = 0.7 fps (target 30); frametime avg 1487.16 min 22.53 max 51545.30 ms; 22 over 33 ms; ...   klfps.c:195 (Present side, [FrameLimit] Log)
  pollloss: no keyboard poll for 5249 ms (episode 1, ...) / pollloss: back after 22266 ms (... episode 1)       klauto.c:2207/2233
  script: poll gap 22031 ms (line 3)                                    klauto.c:1574 (bench script only: counted as info)
  netsmooth: updates 14105, placed 0 (read back ok 0, differs 0), skipped (not a pure yaw) 0                    klnetsmooth.c:398, cumulative
  sync: track: 3 hooked, 12 placements (2.4/s), error before placement mean 14 max 61, refused 0, faults 0 ...; reverts this round 9 (...)  klsync.c:717, every 5 s
  sync: puppet: ... SNAP 43.2 units ... / sync: puppet: snap slot 12 d=88.1 -> ...                                klsync.c:554/591
  session: state 0x18 -> 0x19 (game mode 4)     0x19 = round running (leaving it = round over)                    klnet.c:345
  RESULT PASS (script reached pass) exit code 0, asserts 0, faults 0, loads 2, frames 19371   klauto.c (and KLHook.result)
NOT LOGGED ANYWHERE (searched klhook/*.c for rtt / ping / latency / round trip): network round-trip time. 'rtt' in this report is
therefore absent on purpose; the closest signals are pollloss, the tracker's 'error before placement' and the puppet SNAP count.

THRESHOLDS (per seat, only inside the in-round span, the first GRACE s after 0x19 skipped = the load tail)
  hitch event   = a frame >= HITCH_MS (120 ms: the hook's own 'core: hitch' threshold = 4 frames at the 30 fps cap the 9-seat benches use,
                  and about the point where a mouse turn visibly steps) or a stall watch recovery.
  FREEZE        = a stop >= FREEZE_MS (3000 ms): the netcode's own timeouts (Quazal keepalive) are of this order, a human sees a frozen game.
  slow window   = a 10 s 'core: perf' window under 90 % of the target fps (target = the limiter's cap if logged, else 60).
  FAIL   : any assert, fault, crash dump, FATAL/EXCEPTION line, never reached the round (< MIN_ROUND_S in round), or a FREEZE / pollloss >= 3 s in the round.
  HITCHY : hitch rate > HITCH_PER_MIN (1.0 a minute) or max hitch >= 1000 ms or > 10 % slow windows or p95 of the windows' longest frame > 120 ms.
  SMOOTH : none of the above.
  RUN verdict: FAIL if any seat FAILs or fewer than the expected seats reached the round; HITCHY if the HOST (inst1) is HITCHY (the host's
  hitches reach every client) or >= 2 seats are HITCHY; else SMOOTH (one hitchy joiner out of nine = bench starvation of that window).
  HONEST CAVEAT: nine kl2.exe on ONE PC are CPU/GPU starved by themselves (N9_DD01f, the best 9-seat run so far: fps 26 of 30, ~28 hitches/min on
  every seat), so an absolute 9-seat verdict is HITCHY until the hook or the bench gets cheaper; use --ref with an earlier 9-seat run
  (N9_DD01f) for a regression check and --ref ARC1_DD01 (offline Arcade, 1 seat, uncapped) for the floor.
  The numbers were checked against the real 9-seat logs of 2026-10-26 (N9_DM01e, N9_DD01f) and the Arcade reference ARC1_DD01: see kl_n9_smooth_test.py.
"""
import json, os, re, sys

HITCH_MS = 120.0
FREEZE_MS = 3000.0
HITCH_PER_MIN = 1.0
HITCH_MAX_BAD_MS = 1000.0
SLOW_FRAC = 0.10
SLOW_OF_TARGET = 0.90
P95_LONGEST_MS = 120.0
GRACE_S = 5.0
MIN_ROUND_S = 60.0
ROUND_STATE = 0x19

HERE = os.path.dirname(os.path.abspath(__file__))
TS = re.compile(r'^(\d\d):(\d\d):(\d\d)\.(\d\d\d) ')


def solo_root():
    try:
        sys.path.insert(0, HERE)
        from kl_port_check import workdir
        return os.path.join(workdir(), 'build', 'klhook', 'solo')
    except Exception:
        return 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo'


class Clock:
    """HH:MM:SS.mmm -> seconds since the first line, midnight rollover safe."""
    def __init__(s):
        s.day = 0; s.last = None; s.first = None

    def __call__(s, line):
        m = TS.match(line)
        if not m:
            return None
        t = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + int(m.group(4)) / 1000.0
        if s.last is not None and t + s.day < s.last - 3600:
            s.day += 86400
        t += s.day
        s.last = t
        if s.first is None:
            s.first = t
        return t


def pct(v, p):
    if not v:
        return 0.0
    v = sorted(v)
    return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]


R_STATE = re.compile(r'session: state (0x[0-9a-f]+) -> (0x[0-9a-f]+)')
R_PERF = re.compile(r'core: perf: (\d+) frames in ([\d.]+) s = ([\d.]+) fps;.*?stutter: (\d+) frame\(s\) over 33 ms, the longest (\d+) ms')
R_HITCH = re.compile(r'core: hitch (\d+) ms')
R_STALLW = re.compile(r'stall watch: the main thread is back after ([\d.]+) s')
R_MSG = re.compile(r'stall: window message \S+ .*? took ([\d.]+) ms')
R_LIM = re.compile(r'fps: limiter: .*?\(target (\d+)[^)]*\); frametime avg ([\d.]+) min ([\d.]+) max ([\d.]+) ms; (\d+) over 33 ms')
R_PLBACK = re.compile(r'pollloss: back after (\d+) ms')
R_PLGAP = re.compile(r'script: poll gap (\d+) ms')
R_NS = re.compile(r'netsmooth: updates (\d+), placed (\d+) \(read back ok (\d+), differs (\d+)\), skipped \(not a pure yaw\) (\d+)')
R_NSCY = re.compile(r'netsmooth camyaw: writes (\d+), restores (\d+)')
R_TRACK = re.compile(r'sync: track: (\d+) hooked, (\d+) placements \(([\d.]+)/s\), error before placement mean (\d+) max (\d+), refused (\d+), faults (\d+).*?reverts this round (\d+)')
R_SNAP = re.compile(r'sync: puppet: (?:slot \d+ c=\S+ SNAP |snap slot )')
R_PUPFAULT = re.compile(r'sync: (?:puppet|track): slot \d+ .*FAULT')
R_RESULT = re.compile(r'RESULT (PASS|FAIL)\b.*?exit code (-?\d+), asserts (\d+), faults (\d+)(?:, soft asserts (\d+))?')
R_FATAL = re.compile(r'(FATAL|EXCEPTION|ACCESS_VIOLATION|access violation|memory fault|c0000005)')


def parse_lines(lines):
    """-> dict of one seat's numbers (see keys below). Pure function of the log text: the test feeds synthetic logs."""
    clk = Clock()
    st = dict(lines=0, first_t=None, last_t=None, spans=[], cap=None, perf=[], hitches=[], freezes=[], msgs=[], lim=[], probe_lines=0,
              pollback=[], pollgap=[], ns=None, nscy=None, track=[], snaps=0, pupfault=0, result=None, fatal=0, state_changes=0)
    cur_start = None
    rows = []                     # (t, kind, payload) in file order; filtered by span afterwards
    for ln in lines:
        st['lines'] += 1
        t = clk(ln)
        if t is None:
            continue
        if st['first_t'] is None:
            st['first_t'] = t
        st['last_t'] = t
        m = R_STATE.search(ln)
        if m:
            a, b = int(m.group(1), 16), int(m.group(2), 16)
            st['state_changes'] += 1
            if b == ROUND_STATE and cur_start is None:
                cur_start = t
            elif a == ROUND_STATE and cur_start is not None:
                st['spans'].append((cur_start, t)); cur_start = None
            continue
        if 'core: perf:' in ln:
            m = R_PERF.search(ln)
            if m:
                rows.append((t, 'perf', dict(frames=int(m.group(1)), secs=float(m.group(2)), fps=float(m.group(3)), over=int(m.group(4)), longest=float(m.group(5)))))
            continue
        if 'core: hitch' in ln:
            m = R_HITCH.search(ln)
            if m:
                rows.append((t, 'hitch', float(m.group(1))))
            continue
        if 'stall watch:' in ln:
            m = R_STALLW.search(ln)
            if m:
                rows.append((t, 'freeze', float(m.group(1)) * 1000.0))
            continue
        if ln[13:].startswith('stall: window message'):
            m = R_MSG.search(ln)
            if m:
                rows.append((t, 'msg', float(m.group(1))))
            continue
        if 'fps: limiter:' in ln:
            m = R_LIM.search(ln)
            if m:
                st['cap'] = int(m.group(1))
                rows.append((t, 'lim', dict(avg=float(m.group(2)), mn=float(m.group(3)), mx=float(m.group(4)), over=int(m.group(5)))))
            continue
        if 'hitch probe:' in ln:
            st['probe_lines'] += 1; continue
        if 'pollloss: back after' in ln:
            m = R_PLBACK.search(ln)
            if m:
                rows.append((t, 'pollback', float(m.group(1))))
            continue
        if 'script: poll gap' in ln:
            m = R_PLGAP.search(ln)
            if m:
                rows.append((t, 'pollgap', float(m.group(1))))
            continue
        if 'netsmooth: updates' in ln:
            m = R_NS.search(ln)
            if m:
                rows.append((t, 'ns', tuple(int(x) for x in m.groups())))
            continue
        if 'netsmooth camyaw: writes' in ln:
            m = R_NSCY.search(ln)
            if m:
                rows.append((t, 'nscy', tuple(int(x) for x in m.groups())))
            continue
        if 'sync: track:' in ln and 'hooked' in ln:
            m = R_TRACK.search(ln)
            if m:
                rows.append((t, 'track', tuple(float(x) for x in m.groups())))
            continue
        if 'sync: puppet:' in ln and R_SNAP.search(ln):
            rows.append((t, 'snap', 1)); continue
        if 'FAULT' in ln and R_PUPFAULT.search(ln):
            rows.append((t, 'pupfault', 1)); continue
        if ' RESULT ' in ln or ln[13:].startswith('RESULT '):
            m = R_RESULT.search(ln)
            if m:
                st['result'] = dict(state=m.group(1), exit=int(m.group(2)), asserts=int(m.group(3)), faults=int(m.group(4)), soft=int(m.group(5) or 0))
            continue
        if R_FATAL.search(ln) and 'EndOnFatal' not in ln and 'ContinueAsserts' not in ln and 'FirstChance' not in ln:
            st['fatal'] += 1
    if cur_start is not None and st['last_t'] is not None:
        st['spans'].append((cur_start, st['last_t']))
    st['rows'] = rows
    return st


def in_span(t, spans, grace=GRACE_S):
    return any(a + grace <= t <= b for a, b in spans)


def summarize(st, dumps=()):
    """-> flat dict of numbers + verdict + reasons for one seat."""
    spans = st['spans']
    inround = sum(max(0.0, b - a) for a, b in spans)
    measured = sum(max(0.0, b - a - GRACE_S) for a, b in spans)
    rows = [r for r in st['rows'] if in_span(r[0], spans)]
    perf = [p for t, k, p in rows if k == 'perf']
    hitch = [p for t, k, p in rows if k == 'hitch']
    freeze = [p for t, k, p in rows if k == 'freeze']
    msgs = [p for t, k, p in rows if k == 'msg']
    lim = [p for t, k, p in rows if k == 'lim']
    pback = [p for t, k, p in rows if k == 'pollback']
    pgap = [p for t, k, p in rows if k == 'pollgap']
    cap = st['cap']
    target = float(min(cap, 60)) if cap else 60.0
    slow = [p for p in perf if p['fps'] < SLOW_OF_TARGET * target]
    longest = [p['longest'] for p in perf]
    maxes = hitch + freeze + longest + [l['mx'] for l in lim]
    ev = len(hitch) + len(freeze)
    out = dict(in_round_s=round(inround, 1), measured_s=round(measured, 1), windows=len(perf),
               fps_mean=round(sum(p['fps'] for p in perf) / len(perf), 1) if perf else 0.0, fps_min=min([p['fps'] for p in perf]) if perf else 0.0,
               target=target, capped=bool(cap), slow_windows=len(slow), longest_p95=pct(longest, 0.95), longest_max=max(longest) if longest else 0.0,
               stall_count=ev, stall_max_ms=round(max(maxes), 1) if maxes else 0.0, hitch_lines=len(hitch), freeze_lines=len(freeze),
               stall_per_min=round(ev / (measured / 60.0), 2) if measured > 0 else 0.0, msg_over_20ms=len(msgs), msg_max_ms=max(msgs) if msgs else 0.0,
               probe_lines=st['probe_lines'], pollloss_in_round=len(pback), pollloss_max_ms=max(pback) if pback else 0.0,
               pollloss_total=len([1 for t, k, p in st['rows'] if k == 'pollback']), script_gaps_in_round=len(pgap))
    ns = [p for t, k, p in st['rows'] if k == 'ns']
    if ns:
        out.update(ns_updates=ns[-1][0], ns_placed=ns[-1][1], ns_readback_differs=ns[-1][3], ns_skipped=ns[-1][4])
    cy = [p for t, k, p in st['rows'] if k == 'nscy']
    if cy:
        out.update(ns_camyaw_writes=cy[-1][0])
    tr = [p for t, k, p in st['rows'] if k == 'track']
    if tr:
        pl = sum(p[1] for p in tr)
        out.update(track_windows=len(tr), track_placements=int(pl), track_err_mean=round(sum(p[3] * p[1] for p in tr) / pl, 1) if pl else 0.0,
                   track_err_max=max(p[4] for p in tr), track_refused=int(sum(p[5] for p in tr)), track_faults=int(sum(p[6] for p in tr)),
                   track_reverts_max=int(max(p[7] for p in tr)))
    out['puppet_snaps'] = sum(1 for t, k, p in st['rows'] if k == 'snap')
    out['puppet_faults'] = sum(1 for t, k, p in st['rows'] if k == 'pupfault')
    res = st['result'] or {}
    out.update(asserts=res.get('asserts', 0), faults=res.get('faults', 0), soft_asserts=res.get('soft', 0), fatal_lines=st['fatal'],
               result=(res.get('state') or ('NO RESULT LINE')), crash_dumps=[d for d in dumps if 'freeze' not in d.lower()],
               freeze_dumps=[d for d in dumps if 'freeze' in d.lower()])
    why_fail, why_hitchy = [], []
    if out['asserts']:
        why_fail.append('%d assert(s)' % out['asserts'])
    if out['faults']:
        why_fail.append('%d fault(s)' % out['faults'])
    if out['crash_dumps']:
        why_fail.append('dump file(s) %s' % ','.join(out['crash_dumps'][:3]))
    if out['fatal_lines']:
        why_fail.append('%d FATAL/EXCEPTION line(s)' % out['fatal_lines'])
    if out['result'] == 'FAIL':
        why_fail.append('RESULT FAIL')
    if inround < MIN_ROUND_S:
        why_fail.append('in round only %.0f s (< %.0f)' % (inround, MIN_ROUND_S))
    if out['stall_max_ms'] >= FREEZE_MS and measured > 0:
        why_fail.append('freeze of %.0f ms in the round' % out['stall_max_ms'])
    if out['pollloss_max_ms'] >= FREEZE_MS:
        why_fail.append('pollloss %.0f ms in the round' % out['pollloss_max_ms'])
    if measured > 0:
        if out['stall_per_min'] > HITCH_PER_MIN:
            why_hitchy.append('%.1f hitches/min (> %.1f)' % (out['stall_per_min'], HITCH_PER_MIN))
        if out['stall_max_ms'] >= HITCH_MAX_BAD_MS:
            why_hitchy.append('max stop %.0f ms' % out['stall_max_ms'])
        if perf and len(slow) > SLOW_FRAC * len(perf):
            why_hitchy.append('%d/%d windows under %.0f %% of %.0f fps' % (len(slow), len(perf), SLOW_OF_TARGET * 100, target))
        if out['longest_p95'] > P95_LONGEST_MS:
            why_hitchy.append('p95 of window-longest frame %.0f ms (> %.0f)' % (out['longest_p95'], P95_LONGEST_MS))
    out['verdict'] = 'FAIL' if why_fail else ('HITCHY' if why_hitchy else 'SMOOTH')
    out['why'] = why_fail + why_hitchy
    return out


def read_seat(d):
    log = os.path.join(d, 'KLHook.log')
    lines = open(log, encoding='latin-1', errors='replace').read().splitlines() if os.path.isfile(log) else []
    st = parse_lines(lines)
    if st['result'] is None:                       # KLHook.result is the fallback when the log was cut
        p = os.path.join(d, 'KLHook.result')
        if os.path.isfile(p):
            kv = dict(l.split('=', 1) for l in open(p, errors='replace').read().splitlines() if '=' in l)
            try:
                st['result'] = dict(state=kv.get('state', '?'), exit=int(kv.get('exit', 0)), asserts=int(kv.get('asserts', 0)), faults=int(kv.get('faults', 0)),
                                    soft=int(kv.get('soft_asserts', 0)))
            except ValueError:
                pass
    dumps = [f for f in os.listdir(d) if f.lower().endswith(('.dmp', '.mdmp'))] if os.path.isdir(d) else []
    s = summarize(st, dumps)
    s['log_lines'] = len(lines)
    return s


def seat_dirs(run):
    base = run if os.path.isdir(run) else os.path.join(solo_root(), run)
    if not os.path.isdir(base):
        return base, []
    ds = sorted((d for d in os.listdir(base) if re.fullmatch(r'inst\d+', d)), key=lambda x: int(x[4:]))
    return base, [os.path.join(base, d) for d in ds]


def run_verdict(seats, expect=None):
    expect = expect or len(seats)
    inr = [s for s in seats if s['in_round_s'] >= MIN_ROUND_S]
    why = []
    if any(s['verdict'] == 'FAIL' for s in seats):
        why.append('seat(s) FAIL: %s' % ','.join('inst%d' % (i + 1) for i, s in enumerate(seats) if s['verdict'] == 'FAIL'))
    if len(inr) < expect:
        why.append('only %d of %d seats reached the round' % (len(inr), expect))
    if why:
        return 'FAIL', why
    hitchy = [i for i, s in enumerate(seats) if s['verdict'] == 'HITCHY']
    if seats and seats[0]['verdict'] == 'HITCHY':
        return 'HITCHY', ['the host (inst1) is HITCHY: %s' % '; '.join(seats[0]['why'])]
    if len(hitchy) >= 2:
        return 'HITCHY', ['%d seats HITCHY: %s' % (len(hitchy), ','.join('inst%d' % (i + 1) for i in hitchy))]
    return 'SMOOTH', (['one seat HITCHY (inst%d: %s), tolerated' % (hitchy[0] + 1, '; '.join(seats[hitchy[0]]['why']))] if hitchy else [])


def analyse(run, expect=None):
    base, ds = seat_dirs(run)
    seats = [read_seat(d) for d in ds]
    v, why = run_verdict(seats, expect) if seats else ('FAIL', ['no inst folders under %s' % base])
    return dict(run=run, base=base, seats=seats, verdict=v, why=why)


def fmt_run(r, refs=()):
    out = ['== %s  [%s]  (%s)' % (r['run'], r['verdict'], '; '.join(r['why']) or 'all seats within thresholds')]
    out.append('  seat  verdict  inround  fps(mean/min) slow  hitch/min  stalls max_ms  p95long  pollloss  snaps  trk_err(mean/max)  ns(upd/placed)  asserts/faults/dumps')
    for i, s in enumerate(r['seats'], 1):
        out.append('  inst%-2d %-7s %6.0fs  %5.1f/%-5.1f  %3d/%-3d %6.2f  %5d %7.0f  %7.0f  %3d/%-6.0f %5d   %s/%s  %s/%s  %d/%d/%d' % (
            i, s['verdict'], s['in_round_s'], s['fps_mean'], s['fps_min'], s['slow_windows'], s['windows'], s['stall_per_min'], s['stall_count'], s['stall_max_ms'],
            s['longest_p95'], s['pollloss_in_round'], s['pollloss_max_ms'], s['puppet_snaps'], s.get('track_err_mean', '-'), s.get('track_err_max', '-'),
            s.get('ns_updates', '-'), s.get('ns_placed', '-'), s['asserts'], s['faults'], len(s['crash_dumps'])))
        if s['why']:
            out.append('         why: ' + '; '.join(s['why']))
    mean = lambda x, k: sum(s[k] for s in x['seats']) / max(1, len(x['seats']))
    for ref in refs:
        if ref['seats']:
            out.append('  vs %s [%s] (seat mean there / here): fps %.1f / %.1f, hitches/min %.2f / %.2f, longest p95 %.0f / %.0f ms' % (
                ref['run'], ref['verdict'], mean(ref, 'fps_mean'), mean(r, 'fps_mean'), mean(ref, 'stall_per_min'), mean(r, 'stall_per_min'),
                mean(ref, 'longest_p95'), mean(r, 'longest_p95')))
    return '\n'.join(out)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    refs = []
    while '--ref' in a:                               # several allowed: an Arcade run and an earlier 9-seat run (the baseline)
        i = a.index('--ref'); refs.append(a[i + 1]); del a[i:i + 2]
    if '--solo-root' in a:
        i = a.index('--solo-root'); globals()['solo_root'] = lambda p=a[i + 1]: p; del a[i:i + 2]
    js = '--json' in a
    if js:
        a.remove('--json')
    if not a:
        print(__doc__); return 2
    rrs = [analyse(x) for x in refs]
    runs = [analyse(x) for x in a]
    if js:
        print(json.dumps(dict(runs=runs, refs=rrs), indent=1, default=str))
    else:
        for r in runs:
            print(fmt_run(r, rrs))
    bad = [r['run'] for r in runs if r['verdict'] == 'FAIL']
    print('RESULT: smooth %s' % ', '.join('%s %s' % (r['run'], r['verdict']) for r in runs) + (' (FAIL: %s)' % ','.join(bad) if bad else ''))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
