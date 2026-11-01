"""
kl_coverring_parse_test.py - self-test of kl_coverring_parse.py (the CR1 / CR2 grader of the [CoverRing] lines) on SYNTHETIC
KLHook.log fragments shaped exactly like klcoverring.c's format strings (no game files). Checks: the parser reads load / poll /
car / clientbuild lines, rings() orders the ringed cars by their first index (the 0x558350 assignment order, not the entity-table
or the poll order), gaps() counts the single ZCreateActorCover points between rings, surplus() balances the count, compare()
exits 3 on host-only / client-only rings, differing order, indices or gaps and 0 on identical seats, --load picks a load,
and a ClientBuild-only log (no 'load' line) still grades. Shapes follow the Q33_DM01 evidence of 2026-11-01 (host 347 + 8 ring
points for the ram truck, the client 347).

    python tools/kl_coverring_parse_test.py          -> RESULT: PASS / FAIL
"""
import io, os, sys, tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_coverring_parse as P

FAILS = []
CHECKS = [0]


def check(cond, what):
    CHECKS[0] += 1
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        FAILS.append(what)


def car_line(i, t, slot, name, n, done, rsv, idx, car='3c2ed5f0', script='3c2f0000'):
    ix = ','.join(str(v) for v in idx[:min(n, 8)])
    return ("17:38:%02d.%03d coverring: car #%d t+%dms slot %d '%s' car=%s vt=00bcb00c script=%s n[+1c4]=%d done[+1e8]=%d rsv[+1e9]=%d idx[+1c8]=[%s] car+8c0=00000000 car+a28=00000003"
            % (t // 1000 % 60, t % 1000, i, t, slot, name, car, script, n, done, rsv, ix))


def poll_line(t, cnt, cars, ran, kind='(first sample of this load)'):
    return '17:38:%02d.%03d coverring: poll t+%dms state=19 L=36c809f0 real-count[+68]=%d %s points(vec 1371) cars=%d ring-ran=%d (cars with done or reserved set)' % (
        t // 1000 % 60, t % 1000, t, cnt, kind, cars, ran)


def load_line(gd='28b18c20'):
    return '17:38:10.000 coverring: load gd=%s state=16 (poll every tick for 90 s, then every 5 s)' % gd


# --- host log: base 347; the ram truck (slot 243, entity-table AFTER the cement truck slot 120) rings first (347..354), one actor cover
#     takes 355, then the cement truck rings 356..363. The cement truck is listed first in every car block (entity-table order).
HOST = [load_line(),
        poll_line(1500, 347, 2, 0),
        car_line(0, 1500, 120, 'V_USA_CementTruck_A_Dynamic_00', 0, 0, 0, []),
        car_line(1, 1500, 243, 'V_USA_RamTruck_A_Dynamic_00', 0, 0, 0, []),
        '17:38:12.000 coverring: poll count 347 -> 355 (delta 8)',
        poll_line(2200, 355, 2, 1, 'CHANGED'),
        car_line(0, 2200, 120, 'V_USA_CementTruck_A_Dynamic_00', 0, 0, 0, []),
        car_line(1, 2200, 243, 'V_USA_RamTruck_A_Dynamic_00', 8, 1, 1, list(range(347, 355))),
        poll_line(40000, 364, 2, 2, 'CHANGED'),
        car_line(0, 40000, 120, 'V_USA_CementTruck_A_Dynamic_00', 8, 1, 1, list(range(356, 364))),
        car_line(1, 40000, 243, 'V_USA_RamTruck_A_Dynamic_00', 8, 1, 1, list(range(347, 355)))]

# --- client log (CR1 shape): nothing rings, count stays 347
CLIENT_NONE = [load_line(),
               poll_line(1600, 347, 2, 0),
               car_line(0, 1600, 120, 'V_USA_CementTruck_A_Dynamic_00', 0, 0, 0, []),
               car_line(1, 1600, 243, 'V_USA_RamTruck_A_Dynamic_00', 0, 0, 0, []),
               poll_line(40000, 347, 2, 0, '(cars changed)'),
               car_line(0, 40000, 120, 'V_USA_CementTruck_A_Dynamic_00', 0, 0, 0, []),
               car_line(1, 40000, 243, 'V_USA_RamTruck_A_Dynamic_00', 0, 0, 0, [])]

# --- client log (CR2 shape, ClientBuild only, no 'load' line): the client rings BOTH cars in entity-table order right after the load:
#     cement truck 347..354, ram truck 355..362 (the host's order is the other way round and the host has an actor cover at 355)
CLIENT_CB = ["17:38:11.000 coverring: clientbuild t+900ms state=19: waiting for a stable count",
             "17:38:12.000 coverring: clientbuild GO t+2000ms slot 'f01\\f01_main' state=19 L=36c809f0 real-count[+68]=347 cars=2 (entity-table order; GUESS: equals the host's order - compare with the host's 'coverring: car #' lines)",
             "17:38:12.001 coverring: clientbuild car #0 slot 120 'V_USA_CementTruck_A_Dynamic_00' car=3c2ed5f0 script=3c2f0000 called 0x81b6f0: count 347 -> 355 (delta 8) n[+1c4]=8 done[+1e8]=1 rsv[+1e9]=1 idx[+1c8]=[347,348,349,350,351,352,353,354]",
             "17:38:12.002 coverring: clientbuild car #1 slot 243 'V_USA_RamTruck_A_Dynamic_00' car=3c2ed600 script=3c2f0100 called 0x81b6f0: count 355 -> 363 (delta 8) n[+1c4]=8 done[+1e8]=1 rsv[+1e9]=1 idx[+1c8]=[355,356,357,358,359,360,361,362]",
             "17:38:12.003 coverring: clientbuild car #2 slot 300 'V_Bentley_00' car=3c2ed700 script=00000000 UNREADABLE done=0 rsv=0 - SKIPPED",
             "17:38:12.004 coverring: clientbuild END cars=3 eligible=2 called=2 real-count 347 -> 363"]


def write(lines, prefix):
    f = tempfile.NamedTemporaryFile('w', suffix='.log', prefix=prefix, delete=False)
    f.write('\n'.join(lines) + '\n')
    f.close()
    return f.name


def run_main(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = P.main(['kl_coverring_parse.py'] + args)
    return code, buf.getvalue()


def test_host():
    h = write(HOST, 'host_')
    loads = P.read_log(h)
    check(len(loads) == 1, 'host: one load')
    L = loads[0]
    check(len(L['polls']) == 3 and P.base_count(L) == 347 and P.final_count(L) == 364, 'host: 3 polls, base 347, final 364')
    check(set(L['cars']) == {(120, 'V_USA_CementTruck_A_Dynamic_00'), (243, 'V_USA_RamTruck_A_Dynamic_00')}, 'host: two cars keyed by slot + name')
    rl = P.rings(L)
    check([r['slot'] for r in rl] == [243, 120], 'host: rings sorted by FIRST INDEX (ram truck 347 before cement truck 356), not entity-table order')
    check(rl[0]['idx'] == list(range(347, 355)) and rl[1]['idx'] == list(range(356, 364)), 'host: ring indices read')
    check(all(P.contiguous(r) for r in rl), 'host: both rings contiguous')
    g = P.gaps(rl, 347)
    check(g == [((243, 'V_USA_RamTruck_A_Dynamic_00'), 355, 1)], 'host: one actor-cover index (355) between the rings: %r' % (g,))
    check(P.surplus(L, rl) == 1, 'host: surplus 1 = the actor cover')
    code, out = run_main([h])
    check(code == 0 and 'rings (sorted by first index = assignment order): 2' in out and 'between rings: 1 index(es) from 355' in out, 'host: single-seat report (exit 0)')
    os.unlink(h)


def test_compare_none():
    h, c = write(HOST, 'host_'), write(CLIENT_NONE, 'client_')
    code, lines = P.compare(P.read_log(h)[-1], P.read_log(c)[-1])
    txt = '\n'.join(lines)
    check(code == 3, 'CR1 shape: host rings, client none -> exit 3')
    check(txt.count('HOST-ONLY ring') == 2 and 'CLIENT-ONLY' not in txt, 'CR1 shape: two host-only rings named')
    check('FINAL COUNT differs: host 364, client 347' in txt, 'CR1 shape: final counts compared')
    check("host order (for a per-map car list, entity-table slots in the host's assignment order): 243,120" in txt, 'CR1 shape: the host order line lists 243,120')
    code2, out = run_main([h, '--compare', c])
    check(code2 == 3 and 'RESULT: DIVERGENT (exit 3)' in out, 'CR1 shape: main exits 3')
    os.unlink(h); os.unlink(c)


def test_compare_clientbuild():
    h, c = write(HOST, 'host_'), write(CLIENT_CB, 'clientcb_')
    cl = P.read_log(c)
    check(len(cl) == 1 and cl[0]['gd'] == '?', 'CR2 shape: a ClientBuild-only log (no load line) opens one anonymous load')
    L = cl[0]
    check(L['cb']['go'] and L['cb']['go']['cnt'] == 347 and len(L['cb']['called']) == 2 and len(L['cb']['skipped']) == 1 and L['cb']['end']['c1'] == 363, 'CR2 shape: GO / 2 called / 1 skipped / END read')
    check(P.base_count(L) is None and P.final_count(L) == 363, 'CR2 shape: no poll = base unknown, final from END')
    rl = P.rings(L)
    check([r['slot'] for r in rl] == [120, 243] and all(r['how'] == 'clientbuild' for r in rl), 'CR2 shape: rings from the called lines, cement truck first (347)')
    code, lines = P.compare(P.read_log(h)[-1], L)
    txt = '\n'.join(lines)
    check(code == 3, 'CR2 shape: divergent')
    check('ORDER differs on the common cars' in txt, 'CR2 shape: order difference named (host 243,120 vs client 120,243)')
    check("INDICES differ for slot 120" in txt and "INDICES differ for slot 243" in txt, 'CR2 shape: both cars have different indices')
    check('ACTOR-COVER GAPS differ' in txt, 'CR2 shape: the host actor cover at 355 has no client twin')
    os.unlink(h); os.unlink(c)


def test_identical_and_loads():
    # two loads in one log; the FIRST load is the ring-less one, the second equals HOST: default grades the last, --load 0 the first
    both = [load_line('11111111')] + CLIENT_NONE[1:] + HOST
    h, c = write(both, 'two_'), write(HOST, 'host_')
    loads = P.read_log(h)
    check(len(loads) == 2 and loads[0]['gd'] == '11111111' and loads[1]['gd'] == '28b18c20', 'two loads split on the load line')
    code, lines = P.compare(P.pick_load(loads), P.read_log(c)[-1])
    check(code == 0 and lines[0].startswith('IDENTICAL: 2 ring(s)'), 'identical seats -> exit 0, IDENTICAL')
    code0, out0 = run_main([h, '--load', '0', '--compare', c])
    check(code0 == 3 and 'grading load 0' in out0, '--load 0 grades the ring-less first load against the host -> 3')
    codeL, outL = run_main([h, '--compare', c])
    check(codeL == 0 and 'RESULT: IDENTICAL' in outL, 'default grades the last load -> 0')
    os.unlink(h); os.unlink(c)


def test_overlap_and_missing():
    # a client whose second ring reuses the first ring's indices (a misread / re-run), and a car flagged done with no index read
    odd = [load_line(), poll_line(1000, 347, 3, 0),
           car_line(0, 1000, 243, 'A', 8, 1, 1, list(range(347, 355))),
           car_line(1, 1000, 120, 'B', 8, 1, 1, list(range(351, 359))),
           car_line(2, 1000, 400, 'C', 0, 1, 0, [])]
    o = write(odd, 'odd_')
    L = P.read_log(o)[-1]
    rl = P.rings(L)
    check([r['slot'] for r in rl] == [243, 120, 400] and rl[2]['first'] is None, 'overlap log: order 243,120 then the index-less car last')
    g = P.gaps(rl, 347)
    check(g == [((243, 'A'), 351, -4)], 'overlap log: a 4-index overlap is reported as negative: %r' % (g,))
    code, out = run_main([o])
    check(code == 0 and 'OVERLAP: ring at 351 reuses 4 index(es)' in out and '(none read)' in out, 'overlap log: report lines')
    empty = write(['17:38:10.000 core: perf: nothing here'], 'empty_')
    code, out = run_main([empty])
    check(code == 2 and 'no coverring lines' in out, 'a log without coverring lines -> exit 2')
    os.unlink(o); os.unlink(empty)


def main():
    test_host()
    test_compare_none()
    test_compare_clientbuild()
    test_identical_and_loads()
    test_overlap_and_missing()
    print('RESULT: %s (%d checks, %d failed)' % ('PASS' if not FAILS else 'FAIL', CHECKS[0], len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
