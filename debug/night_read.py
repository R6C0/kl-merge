"""night_read.py [KLHook.log] [--all] [--selftest]   short verdicts for the 2026-10-17 night tests, read-only.
Default log: <Dog Days>/KLHook.log (kl.DD). Reads the LAST session ('==== KLHook ... loaded'); --all = every session.
 (a) Loads  : each 'LOAD start/end scene=' (klauto.c), 'level loaded:' lines, and the faults / asserts / watchdogs of
              the session (the KINDS of log.py), each placed in or after the load it belongs to.
 (b) Bots   : the 'otrace:' lines (klescort.c kltr_line): per bot the sequence of order givers, flip-flops (two givers
              alternating on one bot within 30 s), SKIP lines (WalkExclusive), and whether x rises along the hop-walk
              orders (re/bots_active.md 'Order trace and the DM09 walk conflict').
 (c) Heli   : the 'heli:' lines (klheliprobe.c) read by the rules of re/heli_call.md 'Handover: HELI4 grep recipe':
              goal=0, goal8 not 0/4, sq=0, a_bc!=0, a154!=goal after the start, pos unchanged; plus the bots' van lines
              ('bots: ... van S t' states, 'bots: VAN/van:', 'botvan:') and the 'hud: van card' lines.
 (d) Camera : tools/kl_camlog.py is called (parse + report); its '6. VERDICT' block is printed.
Plain text; exit code 0. Nothing is written, installed or started."""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
HEAD = re.compile(r'(\d\d:\d\d:\d\d\.\d+) (.*)')
KEEP = ('otrace:', 'heli:', 'LOAD ', 'script ', 'bots: ', 'botvan:', 'hud: van card', 'cam', '====',
        'steam: level ')                # the SHIP hook has no klauto LOAD lines: klsteam's archive / level lines stand in
FLIP_S = 30.0

try:                                   # the crash markers live in log.py; a short copy is the fallback
    import log as _log
    KINDS = _log.KINDS
except Exception:
    KINDS = [('ASSERT', re.compile(r'ASSERT at kl2\.exe\+\w+ \((\w+)\)')),
             ('CRASH', re.compile(r'CRASH (\w+) at kl2\.exe\+\w+ \((\w+)\)')),
             ('FAULT', re.compile(r'(?:FAULT \(first chance[^)]*\)|FATAL unhandled exception|FATAL stack overflow) (\w+) at (.+?)\+0x(\w+) \((\w+)\)')),
             ('FATAL', re.compile(r'FATAL (C runtime: .*)')),
             ('WATCHDOG', re.compile(r'WATCHDOG: (.*)')),
             ('RESULT', re.compile(r'RESULT (\w+) \((.*)\) exit code (-?\d+)'))]
MARK = {'ASSERT', 'CRASH', 'FAULT', 'FATAL', 'WATCHDOG', 'RESULT', 'END'}


def sessions(lines):
    """-> [[(time, text, idx)]]: only the lines this tool reads, per session (a log without header = one session)."""
    ses = [[]]; hdr = False
    for i, ln in enumerate(lines):
        m = HEAD.match(ln.rstrip('\r\n'))
        if not m:
            continue
        t, r = m.groups()
        if r.startswith('==== KLHook') and 'loaded' in r:
            if hdr or ses[-1]:
                ses.append([])
            hdr = True
        if r.startswith(KEEP) or any(p.match(r) for k, p in KINDS if k in MARK):
            ses[-1].append((t, r, i))
    return [s for s in ses if s] or [[]]


def secs(t):
    h, m, s = t.split(':'); return int(h) * 3600 + int(m) * 60 + float(s)


# ---------------------------------------------------------------- (a) loads
def loads(S):
    out = ['(a) LOADS']
    cur = None; done = []; ev = []; arch = {}; ship = []
    for t, r, i in S:
        m = re.match(r'steam: level archive (\S+) opened from (.*?): ', r)
        if m:
            arch[m.group(1).lower()] = os.path.basename(os.path.dirname(m.group(2))); continue
        m = re.match(r"steam: level '([^']*)'(?:: its archive (\S+))?", r)
        if m:                          # SHIP hook: the level started (it got past the load)
            ship.append(dict(scene=m.group(1), t0=t, end=t, info='', name=arch.get((m.group(2) or '').lower(), ''))); continue
        m = re.match(r"LOAD start scene='([^']*)'", r)
        if m:
            cur = dict(scene=m.group(1), t0=t, end=None, info='', name=''); done.append(cur); continue
        m = re.match(r"LOAD end scene='([^']*)'(.*)", r)
        if m:
            c = cur if cur and cur['scene'] == m.group(1) and not cur['end'] else None
            if c is None:
                c = dict(scene=m.group(1), t0=t, end=None, info='', name=''); done.append(c)
            c['end'] = t; c['info'] = m.group(2).strip(); cur = c; continue
        m = re.match(r'script \d+: level loaded: (.*)', r)
        if m and done:
            done[-1]['name'] = m.group(1).strip(); continue
        for k, p in KINDS:
            if k in MARK and p.match(r):
                state = 'in %s' % os.path.basename(cur['scene'] or '?') if cur and not cur['end'] else \
                        ('after %s' % os.path.basename(cur['scene']) if cur else 'before any load')
                ev.append((t, k, r, state, cur)); break
    if not done and ship:
        out.append('  no LOAD start/end lines (SHIP hook): levels that started, from klsteam lines (a crash during a load shows only as a missing entry)')
        done = ship
    if not done:
        out.append('  no LOAD start/end lines (is this the hook log of a run? or an old log)')
    for c in done:
        nodes = re.search(r'(\d+) ms, (\d+) nodes, (\d+) rooms, asserts during load (-?\d+)', c['info'])
        extra = '%s ms, %s nodes, asserts during load %s' % (nodes.group(1), nodes.group(2), nodes.group(4)) if nodes else c['info'][:70]
        out.append('  %-34s %s%s %s' % (os.path.basename(c['scene'].replace('\\', '/')),
                   'LOADED' if c['end'] else 'NO LOAD END (crashed, hung or still loading)',
                   ' "%s"' % c['name'] if c['name'] else '', ('(%s)' % extra.strip('()')) if extra else ''))
    fatal = [e for e in ev if e[1] in ('CRASH', 'FATAL', 'WATCHDOG') or (e[1] == 'FAULT' and e[2].startswith('FATAL')) or e[1] == 'ASSERT']
    first = [e for e in ev if e[1] == 'FAULT' and not e[2].startswith('FATAL')]
    for t, k, r, st, c in fatal:
        out.append('  %s %s %s: %s' % (t, k, st, r[:130]))
    if first:
        out.append('  %d first-chance fault line(s) (may have been handled)' % len(first))
    for t, k, r, st, c in ev:
        if k == 'RESULT':
            out.append('  %s RESULT: %s' % (t, r[:120]))
    bad = bool(fatal) or any(not c['end'] for c in done)
    out.append('  VERDICT: %s' % ('PROBLEM - ' + ('%d fatal/assert line(s)' % len(fatal) if fatal else '') +
               (' a load without end' if any(not c['end'] for c in done) else '') + '; run python debug/triage.py --keep'
               if bad else ('all %d load(s) ended, no assert/crash/watchdog line' % len(done) if done else 'nothing to judge')))
    return out


# ---------------------------------------------------------------- (b) bots
OT = re.compile(r'otrace: t=(\d+) r=(-?[\d.]+) rec=(-?\d+) by=(\S+) (\S+) \((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)(.*?) why=(.*)')
XYZ = re.compile(r'\((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)')


def bots(S):
    out = ['(b) BOT ORDER TRACE']
    rows = []
    for t, r, i in S:
        if not r.startswith('otrace:'):
            continue
        m = OT.match(r)
        if not m:
            continue
        tick, rr, rec, by, kind, x, y, z, rest, why = m.groups()
        sets = XYZ.findall(rest)
        rows.append(dict(tick=int(tick), r=float(rr), rec=int(rec), by=by, kind=kind, a=(float(x), float(y), float(z)),
                         b=tuple(map(float, sets[0])) if sets else None, why=why))
    on = [r for t, r, i in S if r.startswith('otrace: ON')]
    if not rows:
        out.append('  no otrace: lines%s' % (' (the ON line is there: no order was given)' if on else ' (OrderTrace=0 or the test dll is not the one running)'))
        out.append('  VERDICT: nothing to judge')
        return out
    out.append('  %d otrace lines, %d bot record(s)%s' % (len(rows), len({r['rec'] for r in rows}), ' ' if on else ' (no ON line)'))
    flips_total = 0
    for rec in sorted({r['rec'] for r in rows}):
        rs = [r for r in rows if r['rec'] == rec]
        orders = [r for r in rs if r['kind'] in ('ORDER', 'ORDER-DRY', 'BLOCK-CHANGED')]
        seq = []                                    # run-length of givers
        for r in orders:
            if seq and seq[-1][0] == r['by']: seq[-1][1] += 1
            else: seq.append([r['by'], 1])
        flips = []
        for a, b, c in zip(orders, orders[1:], orders[2:]):          # A B A inside 30 s, A != B
            if a['by'] != b['by'] and c['by'] == a['by'] and ((c['tick'] - a['tick']) & 0xffffffff) / 1000.0 <= FLIP_S:
                flips.append((a, b, c))
        flips_total += len(flips)
        sk = [r for r in rs if r['kind'] == 'SKIP']
        tp = [r for r in rs if r['kind'] == 'TELEPORT']
        pairs = {}
        for a, b, c in flips:
            k = tuple(sorted((a['by'], b['by']))); pairs[k] = pairs.get(k, 0) + 1
        sq = ' > '.join('%s%s' % (b, ' x%d' % n if n > 1 else '') for b, n in seq[:14]) + (' ...(%d runs)' % len(seq) if len(seq) > 14 else '')
        out.append('  rec %d: %d orders%s%s | %s' % (rec, len(orders), ', %d SKIP' % len(sk) if sk else '', ', %d teleport' % len(tp) if tp else '', sq or '-'))
        if flips:
            a, b, c = flips[0]
            out.append('      FLIP-FLOP x%d (%s) first at r=%.1f: %s -> %s -> %s' % (len(flips), ', '.join('%s/%s %d' % (k[0], k[1], n) for k, n in pairs.items()), a['r'], a['by'], b['by'], c['by']))
    walk = [r for r in rows if r['by'] == 'hop-walk' and r['kind'].startswith('ORDER')]
    skips = [r for r in rows if r['kind'] == 'SKIP']
    game = [r for r in rows if r['by'] == 'GAME?']
    out.append('  WalkExclusive SKIP lines: %s' % ('%d (by %s)' % (len(skips), ', '.join(sorted({r['by'] for r in skips}))) if skips else 'none'))
    out.append('  by=GAME? lines (the game\'s own chain or an untraced module): %d' % len(game))
    prog = []
    for rec in sorted({r['rec'] for r in walk}):
        w = [r for r in walk if r['rec'] == rec]
        xs = [(r['b'] or r['a'])[0] for r in w]                       # the position the game set; asked when absent
        tgt = max(set(r['a'][0] for r in w), key=[r['a'][0] for r in w].count)
        up = sum(1 for p, q in zip(xs, xs[1:]) if q > p); n = max(len(xs) - 1, 1)
        prog.append((rec, len(w), xs[0], xs[-1], up, n, tgt))
        out.append('  hop-walk rec %d: %d orders, x %.0f -> %.0f (rises %d of %d steps), walk target x %.0f (the most common asked x)' % (rec, len(w), xs[0], xs[-1], up, n, tgt))
    if not walk:
        out.append('  no hop-walk orders: the DM09 walk was not exercised (no [CrewHop] walk in this round)')
    giveups = [r for r in rows if 'giveup' in r['by'] or 'GIVE UP' in r['why'].upper()]
    if giveups:
        out.append('  hop-walk GIVE UP lines: %d' % len(giveups))
    rising = bool(prog) and all(p[3] > p[2] and p[4] >= 0.7 * p[5] for p in prog)
    out.append('  VERDICT: %s; walk x %s; WalkExclusive %s' % (
        'FLIP-FLOP on %d occasion(s)' % flips_total if flips_total else 'no flip-flop within %d s' % FLIP_S,
        ('rises toward the target' if rising else 'does NOT rise steadily') if prog else 'not tested',
        'active (SKIPs seen)' if skips else 'not seen (off, or nothing to skip)'))
    return out


# ---------------------------------------------------------------- (c) heli + van
KV = re.compile(r'\b([A-Za-z_]\w*)=([0-9A-Fa-f]+)\b')
POS = re.compile(r'pos=(unreadable )?\((-?[\d.]+), (-?[\d.]+), (-?[\d.]+)\)')


def heli(S):
    out = ['(c) HELI (HELI4) AND VAN']
    hs = []; scan = []
    for t, r, i in S:
        if r.startswith('heli: probe scan'):
            scan.append((t, r))
        elif r.startswith('heli: t='):
            d = {k: v for k, v in KV.findall(r.split(' pos=')[0])}
            p = POS.search(r)
            if not p:
                continue
            d['_t'] = t; d['_chg'] = ' CHANGE ' in r; d['_unread'] = bool(p.group(1)); d['_pos'] = tuple(float(p.group(n)) for n in (2, 3, 4))
            hs.append(d)
    on = [r for t, r, i in S if r.startswith('heli: probe ON')]
    for t, r in scan[-2:]:
        out.append('  %s' % r[:150])
    if not hs:
        out.append('  no "heli: t=" lines%s' % (' (the probe is on and found nothing; N=0: rerun with Probe=2)' if on or scan else ' (Probe=0 or the test dll is not the one running)'))
    else:
        for rout in dict.fromkeys(d['rout'] for d in hs):
            L = [d for d in hs if d['rout'] == rout]
            N = lambda d, k: int(d[k], 16 if k in ('goal', 'sq', 'a8c', 'a90', 'a154') else 10)
            st = [d for d in L if N(d, 'started') == 1]
            first = st[0] if st else None
            ch = [d for d in L if d['_chg']]
            out.append('  rout %s: %d lines (%d CHANGE), %s .. %s' % (rout, len(L), len(ch), L[0]['_t'], L[-1]['_t']))
            v = []                                                    # the rules, one by one
            if not st:
                v.append(('started', 'no started=1 ever: the call never reached the rout (AITrigger / RESET wiring)', False))
            else:
                after = L[L.index(first):]; last = after[-1]
                g = N(last, 'goal'); v.append(('goal', 'goal=%08x %s' % (g, 'after the start: NOT BUILT (init 0x815aa0 failed at load)' if g == 0 else 'built'), g != 0))
                g8s = sorted({N(d, 'goal8') for d in L}); v.append(('goal8', 'goal8 %s %s' % (g8s, 'ok (0 or 4)' if set(g8s) <= {0, 4} else 'NOT 0/4: early-out 1 (0x80dcd0 returns)'), set(g8s) <= {0, 4}))
                sq0 = N(last, 'sq') == 0; v.append(('sq', 'sq=%08x %s' % (N(last, 'sq'), 'ZERO: early-out 2 (0x791090 exits at 0x7910af)' if sq0 else 'set'), not sq0))
                abc_pre = [d for d in L[:L.index(first)] if N(d, 'a_bc') != 0]; abc_all = [d for d in L if N(d, 'a_bc') != 0]
                v.append(('a_bc', 'a_bc!=0 %s' % ('before the start: early-out 3' if abc_pre else ('only after the start (%d lines; a one-shot flag the start sets: fine)' % len(abc_all) if abc_all else 'never: ok')), not abc_pre))
                a154 = N(last, 'a154'); gl = N(last, 'goal'); store = a154 == gl and gl != 0
                if store:
                    m = 'a154==goal: the add-goal store ran'
                elif N(last, 'a8c') == 0 and N(last, 'a90') == 0:
                    m = 'a154=%08x != goal=%08x with a8c=a90=0: the add-goal store (0x7f680e) is SKIPPED' % (a154, gl)
                else:
                    m = 'a154=%08x != goal=%08x (a8c=%08x a90=%08x)' % (a154, gl, N(last, 'a8c'), N(last, 'a90'))
                v.append(('a154', m, store))
                ps = [d['_pos'] for d in after if not d['_unread']]
                if not ps: v.append(('pos', 'pos unreadable after the start', False))
                else:
                    mx = max(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5 for a in ps for b in ps)
                    v.append(('pos', 'pos %s (spread %.0f over %d lines; first %s, last %s)' % ('UNCHANGED' if mx < 1 else 'MOVES', mx, len(ps), tuple(map(int, ps[0])), tuple(map(int, ps[-1]))), mx >= 1))
                vs = []
                for d in L:
                    if not vs or vs[-1] != N(d, 'veh1dc'): vs.append(N(d, 'veh1dc'))
                v.append(('veh1dc', 'veh1dc %s' % '>'.join(map(str, vs[:10])), True))
            for k, m, ok in v:
                out.append('      %-8s %s %s' % (k, 'ok ' if ok else '-- ', m))
            kinds = sorted({N(d, 'kind') for d in L}); out.append('      kind=%s (2 = ZHeli)' % kinds)
            if not st: verdict = 'call never reached the rout'
            elif not all(ok for k, m, ok in v if k in ('goal', 'goal8', 'sq', 'a_bc', 'a154')):
                verdict = 'a guard fails: ' + ', '.join(k for k, m, ok in v if not ok and k in ('goal', 'goal8', 'sq', 'a_bc', 'a154'))
            elif [ok for k, m, ok in v if k == 'pos'] == [False]: verdict = 'all guards fine, pos CONSTANT: goal exists, nothing feeds the body (next: ZHeliFlyBehaviour -> ZHeliFlyGoal at ZHeli+0x8c)'
            else: verdict = 'all guards fine and the heli MOVES: it flies (compare to the spline)'
            out.append('      HELI VERDICT: ' + verdict)
    # the bots' van lines
    states = []; vl = []; hud = []
    for t, r, i in S:
        m = re.match(r'bots: L(\d+) s(\w+) van (\d+) (-?[\d.]+)s', r)
        if m:
            if not states or states[-1][1] != int(m.group(3)): states.append((t, int(m.group(3)), float(m.group(4))))
        elif re.match(r'bots: (VAN|van:)', r) or (r.startswith('botvan:') and not r.startswith('botvan: on')):
            vl.append((t, r))
        elif r.startswith('hud: van card'):
            hud.append((t, r))
    out.append('  van state (bots: L.. van S): %s' % (' > '.join('%d@%s' % (s, t[:8]) for t, s, _ in states[:12]) if states else 'no "bots: L.. van" lines'))
    out.append('  bots van lines (bots: VAN / van: , botvan:): %d' % len(vl))
    for t, r in vl[:6]: out.append('      %s %s' % (t, r[:150]))
    on = [x for x in hud if ' ON ' in x[1]]; off = [x for x in hud if 'card off' in x[1]]
    out.append('  hud: van card lines: %d (%d ON, %d off, %d other)%s' % (len(hud), len(on), len(off), len(hud) - len(on) - len(off), '; first %s, last %s' % (hud[0][0], hud[-1][0]) if hud else ''))
    for t, r in hud[:2]: out.append('      %s %s' % (t, r[:150]))
    return out


# ---------------------------------------------------------------- (d) camera
def camera(path):
    out = ['(d) CAMERA']
    try:
        import kl_camlog
    except Exception as x:
        return out + ['  tools/kl_camlog.py not importable (%s): skipped' % x]
    with open(path, encoding='cp1252', errors='replace') as fh:
        recs = kl_camlog.parse(x for x in fh if re.match(r'\s*\d\d:\d\d:\d\d[.,]\d+\s+cam(ev|dump)?:', x))
    rep = kl_camlog.report(recs)
    if not recs:
        return out + ['  ' + rep[-1].strip()]
    i = next((n for n, l in enumerate(rep) if l.startswith('6. VERDICT')), None)
    run = next((l for l in rep if 'cam: samples' in l), '')
    out.append(run)
    out += rep[i:] if i is not None else rep[-3:]
    return out


def read_all(path):
    with open(path, encoding='cp1252', errors='replace') as fh:
        return list(fh)


def run(path, every=False, pr=print):
    lines = read_all(path)
    ss = sessions(lines)
    pr('log: %s (%d session(s), %d line(s))' % (path, len(ss), len(lines)))
    for n, S in enumerate(ss if every else ss[-1:]):
        if every: pr('\n== session %d%s' % (n + 1, '' if not S else ' from ' + S[0][0]))
        for part in (loads(S), bots(S), heli(S)):
            for l in part: pr(l)
        if not every or n == len(ss) - 1:
            for l in camera(path): pr(l)
    return ss


# ---------------------------------------------------------------- self test
SELF = """\
12:00:00.000 ==== KLHook loaded (ContinueAsserts=1 MaxDumps=4) kl2.exe 00400000-0174e000
12:00:01.000 LOAD start scene='SCENES\\Locations\\F07\\F07_Main.gms' (argument 0012)
12:00:09.000 LOAD end scene='SCENES\\Locations\\F07\\F07_Main.gms' 8000 ms, 41000 nodes, 12 rooms, asserts during load 0
12:00:09.100 script 20: level loaded: Vault
12:00:20.000 LOAD start scene='SCENES\\Locations\\F06\\F06_Main.gms' (argument 0012)
12:00:21.500 CRASH c0000005 at kl2.exe+6ad1c3 (006ad1c3)
12:00:30.000 bots: L1 s16 van 0 0.0s | 0 you in-play g0 $0
12:00:40.000 bots: L1 s16 van 3 6.2s | 0 you in-play g0 $0
12:00:41.000 bots: VAN: bot 3 (traitor, actor 0123) blows the vehicle up
12:00:42.000 botvan: record 2 (AI heister, stage 3) has waited 4.0 s with no vehicle
12:00:43.000 hud: van card ON at (1036, 234) 211 wide, icon slot 170 (picture loaded), health share 1.00
12:00:44.000 hud: van card off (the stock panel stopped drawing for 2.5 s)
12:01:00.000 otrace: ON ([Bots] OrderTrace=1): one 'otrace:' line per order
12:01:01.000 otrace: t=100000 r=10.0 rec=1 by=hop-walk ORDER (2560, 19601, 740) set=(-952, 19601, 740) why=walk
12:01:05.000 otrace: t=104000 r=14.0 rec=1 by=fedkit-hunted ORDER (-895, 4, 740) set=(-895, 4, 740) why=towards you
12:01:09.000 otrace: t=108000 r=18.0 rec=1 by=hop-walk ORDER (2560, 19601, 740) set=(-21, 19601, 740) why=walk
12:01:13.000 otrace: t=112000 r=22.0 rec=1 by=fedkit-hunted ORDER (767, -658, 740) set=(767, -658, 740) why=step aside
12:01:20.000 otrace: t=119000 r=29.0 rec=1 by=GAME? BLOCK-CHANGED (130, 238, 740) was=(767, -658, 740) why=-
12:01:21.000 otrace: t=120000 r=30.0 rec=2 by=hop-walk ORDER (2560, 19601, 740) set=(100, 19601, 740) why=walk
12:01:29.000 otrace: t=128000 r=38.0 rec=2 by=hop-walk ORDER (2560, 19601, 740) set=(600, 19601, 740) why=walk
12:01:37.000 otrace: t=136000 r=46.0 rec=2 by=hop-walk ORDER (2560, 19601, 740) set=(1100, 19601, 740) why=walk
12:01:38.000 otrace: t=137000 r=47.0 rec=2 by=move-restless SKIP (0, 0, 0) why=walking
12:02:00.000 heli: probe scan: 1 ZHeliFlyBehaviourRout, 1 ZHeli in the entity table (table 01234567)
12:02:01.000 heli: t=200000 tick rout=0a000010 goal=00000000 goal8=0 started=0 blocked=0 sq=00000000 a8c=00000000 a90=00000000 a_bc=0 a154=00000000 | rules=0b000000 veh1dc=0 kind=2 ref1e4=00000000 | zheli=0c000000 pos=(0, 0, 0) ctl7d8=00000000 ctl7dc=00000000
12:02:02.000 heli: t=201000 CHANGE rout=0a000010 goal=00000000 goal8=0 started=1 blocked=0 sq=00000000 a8c=00000000 a90=00000000 a_bc=0 a154=00000000 | rules=0b000000 veh1dc=0 kind=2 ref1e4=00000000 | zheli=0c000000 pos=(0, 0, 0) ctl7d8=00000000 ctl7dc=00000000
12:02:03.000 heli: t=202000 tick rout=0a000010 goal=00000000 goal8=0 started=1 blocked=0 sq=00000000 a8c=00000000 a90=00000000 a_bc=0 a154=00000000 | rules=0b000000 veh1dc=0 kind=2 ref1e4=00000000 | zheli=0c000000 pos=(0, 0, 0) ctl7d8=00000000 ctl7dc=00000000
12:03:00.000 cam: on: Log=1
12:03:01.000 cam: f 1 T 1.00 dt 0.016
"""

SELF2 = """\
09:00:00.000 ==== KLHook loaded (x) kl2.exe 00400000-0174e000
09:00:01.000 LOAD start scene='SCENES\\Locations\\F01\\F01_Main.gms' (argument 0012)
09:00:05.000 LOAD end scene='SCENES\\Locations\\F01\\F01_Main.gms' 4000 ms, 9000 nodes, 3 rooms, asserts during load 0
09:00:06.000 heli: t=1 CHANGE rout=0a000010 goal=0d000000 goal8=4 started=1 blocked=0 sq=0e000000 a8c=00000000 a90=00000000 a_bc=0 a154=0d000000 | rules=0b000000 veh1dc=0 kind=2 ref1e4=00000000 | zheli=0c000000 pos=(10, 20, 30) ctl7d8=00000001 ctl7dc=00000000
09:00:07.000 heli: t=2 tick rout=0a000010 goal=0d000000 goal8=4 started=1 blocked=0 sq=0e000000 a8c=00000000 a90=00000000 a_bc=0 a154=0d000000 | rules=0b000000 veh1dc=1 kind=2 ref1e4=00000000 | zheli=0c000000 pos=(310, 20, 30) ctl7d8=00000001 ctl7dc=00000000
09:00:10.000 otrace: t=4294967000 r=1.0 rec=0 by=hop-walk ORDER (2560, 0, 0) set=(0, 0, 0) why=w
09:00:18.000 otrace: t=7000 r=9.0 rec=0 by=hop-walk ORDER (2560, 0, 0) set=(800, 0, 0) why=w
09:00:26.000 otrace: t=15000 r=17.0 rec=0 by=hop-walk ORDER (2560, 0, 0) set=(1600, 0, 0) why=w
09:00:27.000 otrace: t=16000 r=18.0 rec=0 by=fedkit-hunted SKIP (0, 0, 0) why=walking
"""


def selftest():
    import io, tempfile
    def check(c, m):
        if not c: raise AssertionError(m)
    def go(txt):
        with tempfile.NamedTemporaryFile('w', suffix='.log', delete=False, encoding='cp1252') as f: f.write(txt); p = f.name
        buf = []
        try: run(p, pr=buf.append)
        finally: os.unlink(p)
        return '\n'.join(buf)
    o = go(SELF); print(o); print()
    check('F07_Main.gms' in o and 'LOADED "Vault"' in o and 'asserts during load 0' in o, 'load ok')
    check('F06_Main.gms' in o and 'NO LOAD END' in o and 'CRASH in F06_Main.gms' in o and 'PROBLEM' in o, 'load crash')
    check('FLIP-FLOP x' in o and 'fedkit-hunted' in o and 'fedkit-hunted/hop-walk' in o, 'flip-flop on rec 1')
    check('rec 2:' in o and o.split('rec 2:')[1].split('\n')[1].find('FLIP') < 0, 'no flip-flop on rec 2')
    check('1 SKIP' in o or 'SKIP lines: 1 (by move-restless)' in o, 'skip')
    check('hop-walk rec 2: 3 orders, x 100 -> 1100 (rises 2 of 2 steps)' in o, 'rising x')
    check('by=GAME? lines' in o and ': 1\n' in o, 'game line')
    check('goal=00000000 after the start: NOT BUILT' in o and 'sq=00000000 ZERO' in o and 'pos UNCHANGED' in o, 'heli guards')
    check('HELI VERDICT: a guard fails: goal, sq, a154' in o, 'heli verdict ' + o.split('HELI VERDICT')[1][:80])
    check('0@12:00:30 > 3@12:00:40' in o and 'bots van lines (bots: VAN / van: , botvan:): 2' in o, 'van lines')
    check('hud: van card lines: 2 (1 ON, 1 off' in o, 'hud lines')
    check('(d) CAMERA' in o, 'camera section')
    o2 = go(SELF2); print(o2); print()
    check('no flip-flop within' in o2 and 'rises toward the target' in o2 and 'SKIP lines: 1' in o2 and 'x 0 -> 1600' in o2, 'clean walk + 32 bit tick wrap')
    check('all guards fine and the heli MOVES' in o2 and 'veh1dc 0>1' in o2, 'heli flies')
    check('all 1 load(s) ended' in o2, 'clean load')
    # an old log without any of these lines must not fail
    o3 = go('10:00:00.000 ==== KLHook loaded\n10:00:01.000 something else\n')
    check('no LOAD start/end' in o3 and 'no otrace: lines' in o3 and 'no "heli: t=" lines' in o3, 'empty')
    print('selftest ok')


def main(argv):
    if '--selftest' in argv:
        selftest(); return 0
    args = [a for a in argv if not a.startswith('--')]
    if args: path = args[0]
    else:
        try:
            import kl; path = os.path.join(kl.DD, 'KLHook.log')
        except Exception:
            path = os.path.join(r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', 'KLHook.log')
    if not os.path.isfile(path):
        print('no log at %s' % path); return 0
    run(path, '--all' in argv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
