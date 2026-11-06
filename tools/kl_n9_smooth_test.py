#!/usr/bin/env python3
"""kl_n9_smooth_test.py - synthetic KLHook.log texts through kl_n9_smooth (no game files; real 2026-10-26 logs are an optional extra check)."""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_n9_smooth as S

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


def ts(sec, base=9 * 3600):
    t = base + sec
    t %= 86400
    return '%02d:%02d:%02d.%03d' % (t // 3600, t % 3600 // 60, t % 60, int((sec % 1) * 1000))


def perf(t, fps=30.0, longest=38, over=150):
    return '%s core: perf: %d frames in 10.0 s = %.1f fps; the hook\'s tick 0.08 ms a frame (0.2 %% of the frame time, slowest 0.9 ms), 1332 memory reads a frame; stutter: %d frame(s) over 33 ms, the longest %d ms; UI Automation requests refused: 0' % (
        ts(t), int(fps * 10), fps, over, longest)


def seat(round_s=120, fps=30.0, longest=38, hitches=(), freezes=(), cap=30, extra=(), asserts=0, faults=0, start=100, base=9 * 3600, in_round=True):
    """a log: menus (with a 22 s pollloss like every real first load), round from `start` for `round_s` s."""
    L = ['%s KLHook loaded (ContinueAsserts=1 MaxDumps=4) kl2.exe' % ts(0, base),
         '%s pollloss: back after 22266 ms (gap between the last poll before and the first after; episode 1)' % ts(10, base),
         '%s stall watch: the main thread is back after 21.8 s without a frame or a loader step' % ts(11, base),
         '%s session: state 0x18 -> 0x19 (game mode 4)' % ts(start, base) if in_round else '%s session: state 0x7 -> 0xb (game mode 4)' % ts(start, base)]
    if cap:
        L.append('%s fps: limiter: 300 presents in 10.0 s = 30.0 fps (target %d); frametime avg 33.33 min 30.1 max 41.00 ms; 12 over 33 ms; waiting 5.0 %% of the time; adaptive off pace 0.00 ms; watchdog 0 resets 0' % (ts(start + 6, base), cap))
    t = start + 10
    while t <= start + round_s:
        L.append(perf(t, fps, longest).replace(ts(t), ts(t, base)))
        t += 10
    for h in hitches:
        L.append('%s core: hitch %d ms' % (ts(start + 30, base), h))
    for f in freezes:
        L.append('%s stall watch: the main thread is back after %.1f s without a frame or a loader step' % (ts(start + 40, base), f))
    L += list(extra)
    if in_round:
        L.append('%s session: state 0x19 -> 0x1f (game mode 4)' % ts(start + round_s, base))
    L.append('%s RESULT PASS (script reached pass) exit code 0, asserts %d, faults %d, loads 2, frames 19371' % (ts(start + round_s + 5, base), asserts, faults))
    return L


def one(lines, dumps=()):
    return S.summarize(S.parse_lines(lines), dumps)


# 1 a clean seat
a = one(seat())
check(a['verdict'] == 'SMOOTH', 'clean seat SMOOTH: %r' % a['why'])
check(abs(a['in_round_s'] - 120) < 0.5, 'in round 120 s: %r' % a['in_round_s'])
check(a['stall_count'] == 0 and a['windows'] == 12, 'no stalls, 12 windows: %r %r' % (a['stall_count'], a['windows']))
check(a['pollloss_total'] == 1 and a['pollloss_in_round'] == 0, 'the menu-time pollloss / stall watch is NOT counted in the round: %r' % a)
check(a['capped'] and a['target'] == 30.0, 'cap 30 read from the limiter line')
# 2 hitchy: 5 hitches of 150..300 ms in 115 s
b = one(seat(hitches=[150, 200, 250, 180, 300]))
check(b['verdict'] == 'HITCHY' and b['stall_count'] == 5 and b['stall_max_ms'] == 300.0, 'hitchy seat: %r %r' % (b['verdict'], b['why']))
# 3 a single hitch in two minutes stays SMOOTH
c = one(seat(hitches=[200]))
check(c['verdict'] == 'SMOOTH', 'one hitch in 2 min is SMOOTH: %r' % c['why'])
# 4 a freeze in the round is FAIL
d = one(seat(freezes=[11.2]))
check(d['verdict'] == 'FAIL' and d['stall_max_ms'] == 11200.0, 'freeze FAIL: %r' % d['why'])
# 5 slow windows (fps 20 of 30) = HITCHY
e = one(seat(fps=20.0))
check(e['verdict'] == 'HITCHY' and e['slow_windows'] == 12, 'slow windows HITCHY: %r' % e['why'])
# 6 asserts / faults
check(one(seat(asserts=2))['verdict'] == 'FAIL', 'assert FAIL')
check(one(seat(faults=1))['verdict'] == 'FAIL', 'fault FAIL')
# 7 never in the round
f = one(seat(in_round=False))
check(f['verdict'] == 'FAIL' and f['in_round_s'] == 0, 'never in round FAIL: %r' % f['why'])
# 8 a crash dump fails, a freeze dump does not by itself
check(one(seat(), ['KLHook_1.dmp'])['verdict'] == 'FAIL', 'crash dump FAIL')
check(one(seat(), ['KLHook_freeze.dmp'])['verdict'] == 'SMOOTH', 'freeze dump alone is only listed')
check(one(seat(), ['KLHook_freeze.dmp'])['freeze_dumps'] == ['KLHook_freeze.dmp'], 'freeze dump listed')
# 9 midnight rollover
g = one(seat(base=86400 - 150))
check(abs(g['in_round_s'] - 120) < 0.5 and g['verdict'] == 'SMOOTH', 'midnight rollover: in round %r' % g['in_round_s'])
# 10 netsmooth / sync parse
ex = ['%s netsmooth: updates 1825, placed 40 (read back ok 40, differs 2), skipped (not a pure yaw) 7' % ts(150),
      '%s netsmooth: updates 3305, placed 90 (read back ok 88, differs 2), skipped (not a pure yaw) 9' % ts(160),
      '%s sync: track: 3 hooked, 10 placements (2.0/s), error before placement mean 20 max 80, refused 1, faults 0 (total 0); skipped: in tolerance 603, reverts this round 9 (netsnap 29, y-only 0), bound stalls placed 1, BindFix writes 0' % ts(170),
      '%s sync: track: 3 hooked, 30 placements (6.0/s), error before placement mean 40 max 500, refused 0, faults 0 (total 0); skipped: in tolerance 603, reverts this round 12 (netsnap 29, y-only 0), bound stalls placed 1, BindFix writes 0' % ts(175),
      '%s sync: puppet: slot 12 c=ZFFActor SNAP 88.1 units to (1.0,2.0,3.0) from (4.0,5.0,6.0)' % ts(180),
      '%s sync: puppet: snap slot 13 d=120.0 -> (1,2,3) (was (1,2,3), now (1,2,3))' % ts(181),
      '%s sync: puppet: slot 14 c=ZFFActor FAULT in the teleport: slot blacklisted for this round' % ts(182),
      '%s hitch probe: 1 hitch(es), 141 sample(s); the main thread stood at: ntdll.dll+0x7320c x50' % ts(183)]
h = one(seat(extra=ex))
check(h['ns_updates'] == 3305 and h['ns_placed'] == 90 and h['ns_readback_differs'] == 2 and h['ns_skipped'] == 9, 'netsmooth cumulative = last line: %r' % {k: v for k, v in h.items() if k.startswith('ns_')})
check(h['track_placements'] == 40 and abs(h['track_err_mean'] - 35.0) < 0.01 and h['track_err_max'] == 500 and h['track_reverts_max'] == 12 and h['track_refused'] == 1,
      'sync track sums: %r' % {k: v for k, v in h.items() if k.startswith('track_')})
check(h['puppet_snaps'] == 2 and h['puppet_faults'] == 1 and h['probe_lines'] == 1, 'snaps 2, fault 1, probe 1: %r' % ((h['puppet_snaps'], h['puppet_faults'], h['probe_lines']),))
# 11 pollloss in the round of 5 s is only HITCHY-free but a 3 s+ one is FAIL
i = one(seat(extra=['%s pollloss: back after 4200 ms (gap between the last poll before and the first after; episode 2)' % ts(200)]))
check(i['verdict'] == 'FAIL' and i['pollloss_in_round'] == 1, 'pollloss 4.2 s in round FAIL: %r' % i['why'])
# 12 uncapped Arcade reference (offline): 387 fps, longest 14 ms
r = one(seat(fps=387.9, longest=14, cap=0, extra=['%s netsmooth: PROBE on' % ts(150)]))
check(r['verdict'] == 'SMOOTH' and not r['capped'] and r['target'] == 60.0, 'Arcade reference SMOOTH, uncapped target 60: %r' % r['why'])
# 13 run verdicts
sm = lambda **k: one(seat(**k))
nine = [sm() for _ in range(9)]
check(S.run_verdict(nine)[0] == 'SMOOTH', 'nine clean = SMOOTH')
one_h = list(nine); one_h[4] = sm(fps=20.0)
check(S.run_verdict(one_h)[0] == 'SMOOTH', 'one hitchy joiner tolerated')
host_h = list(nine); host_h[0] = sm(fps=20.0)
check(S.run_verdict(host_h)[0] == 'HITCHY', 'hitchy host = HITCHY')
two_h = list(nine); two_h[3] = sm(fps=20.0); two_h[6] = sm(fps=20.0)
check(S.run_verdict(two_h)[0] == 'HITCHY', 'two hitchy joiners = HITCHY')
fl = list(nine); fl[2] = sm(freezes=[20.0])
check(S.run_verdict(fl)[0] == 'FAIL', 'one frozen seat = FAIL')
eight = nine[:8]
check(S.run_verdict(eight, expect=9)[0] == 'FAIL', 'only 8 of 9 expected seats = FAIL')
# 14 folder reading: result file fallback, dump names
with tempfile.TemporaryDirectory() as td:
    for n in (1, 2):
        d = os.path.join(td, 'inst%d' % n)
        os.makedirs(d)
        lines = [l for l in seat(round_s=90) if ' RESULT ' not in l]            # log cut before the RESULT line
        open(os.path.join(d, 'KLHook.log'), 'w', encoding='latin-1').write('\n'.join(lines) + '\n')
        open(os.path.join(d, 'KLHook.result'), 'w').write('state=PASS\nreason=x\nexit=0\nasserts=%d\nfaults=0\nsoft_asserts=3\n' % (1 if n == 2 else 0))
    open(os.path.join(td, 'inst1', 'KLHook_freeze.dmp'), 'w').write('x')
    open(os.path.join(td, 'inst2', 'kl2_490_crash_1.mdmp'), 'w').write('x')
    rr = S.analyse(td, expect=2)
    check(len(rr['seats']) == 2 and rr['seats'][0]['asserts'] == 0 and rr['seats'][1]['asserts'] == 1, 'result file fallback: %r' % [s['asserts'] for s in rr['seats']])
    check(rr['seats'][0]['soft_asserts'] == 3, 'soft asserts read from the result file')
    check(rr['verdict'] == 'FAIL' and rr['seats'][1]['crash_dumps'] == ['kl2_490_crash_1.mdmp'], 'run FAIL on seat 2 crash: %r' % rr['why'])
    check('inst1' in S.fmt_run(rr) and 'RESULT' not in S.fmt_run(rr), 'format prints a table')
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        rc = S.main([td, '--json'])
    check(rc == 1, 'main exits 1 on a FAIL run')
# 15 optional: real logs of 2026-10-26 (skipped when absent)
real = os.path.join(S.solo_root(), 'N9_DD01f')
if os.path.isdir(real):
    rv = S.analyse('N9_DD01f')
    check(len(rv['seats']) == 9 and rv['verdict'] == 'HITCHY' and all(s['in_round_s'] > 200 for s in rv['seats']),
          'real N9_DD01f: 9 seats, HITCHY (9 clients on one PC), %r' % rv['why'])
real = os.path.join(S.solo_root(), 'N9_DM01e')
if os.path.isdir(real):
    rv = S.analyse('N9_DM01e')
    check(rv['verdict'] == 'FAIL' and rv['seats'][1]['verdict'] == 'FAIL', 'real N9_DM01e: inst2 froze 55 s in the round (the run was a script PASS): FAIL')

print('kl_n9_smooth_test: %d checks, %d FAIL' % (checks, fails))
sys.exit(1 if fails else 0)
