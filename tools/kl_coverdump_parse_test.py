"""
kl_coverdump_parse_test.py - self-test of kl_coverdump_parse.py's --compare (host vs client cover POINT lists) on two
SYNTHETIC KLHook.log fragments (no game files): read_dump picks the LAST dump, built_points drops the 0 0 0 (unbuilt) points,
compare finds the common prefix, the differing indices and each side's extra points, and main() exits 3 on a divergence,
0 on identical lists. Shapes follow the real Q33_DM01 logs of 2026-11-01 (host 355 built of 1371, client 347: 8 host-only
points 347..354 = the 29 client asserts at 0x6567e8 / 0x845a8b / ...).

    python tools/kl_coverdump_parse_test.py          -> RESULT: PASS / FAIL
"""
import io, os, sys, tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_coverdump_parse as P

FAILS = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        FAILS.append(what)


def log(points, stamp='17:38:11', blank_from=None, total=None, old_dump=False):
    """A KLHook.log fragment with one coverdump (two when old_dump: an older, different one first, which must be ignored).
    points = {index: (x, y, z)}; indices from blank_from to total-1 are written as unbuilt (pos 0 0 0, the fill in +34)."""
    total = total if total is not None else (max(points) + 1 if points else 0)
    out = []
    if old_dump:
        out += ['17:30:00.000 coverdump: begin gd=1 state=16 L=2 vtable=00bbece4 expected=00bbece4 VTABLE OK',
                '17:30:00.001 coverdump: pt 0 pos 1.0 2.0 3.0 | +34 1.0 2.0 3.0 | 00000000 00000000',
                '17:30:00.002 coverdump: end records=1 (lines 1) points=1 (lines 1, cached 1) dropped=0']
    out.append('%s.300 coverdump: begin gd=28b18c20 state=19 L=36c809f0 vtable=00bbece4 expected=00bbece4 VTABLE OK' % stamp)
    out.append('%s.300 coverdump: list records base=39da4030 count=169 stride=0xa8 | points begin=37479020 end=374a2834 stride=0x7c count=%d | MaxRecords=2000 MaxPoints=6000' % (stamp, total))
    out.append("%s.317 coverdump: rec 0 36d17c20 00000000 00000100 00000000 00000000 00000000 00000001 00000001 00000000 00000000 00000000 00000000 | ent@+0x0=36d36870'CoverBoxH_K6_01'" % stamp)
    for i in range(total):
        if i in points and (blank_from is None or i < blank_from):
            x, y, z = points[i]
            out.append('%s.349 coverdump: pt %d pos %.1f %.1f %.1f | +34 %.3f %.3f %.3f | 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000001 00000000'
                       % (stamp, i, x, y, z, x + 50, y, z + 100))
        else:
            out.append('%s.361 coverdump: pt %d pos 0.0 0.0 0.0 | +34 8345069056.000 -0.000 426409608812460769280.000 | 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000001 ee1b95c9' % (stamp, i))
    out.append('%s.385 coverdump: near t+5s me (1400.0 -13.0 30238.0) of %d points: #63 d=847.5 (2229.5 -15.0 30064.4) | #64 d=898.5' % (stamp, total))
    out.append('%s.394 coverdump: end records=169 (lines 169) points=%d (lines %d, cached %d) dropped=0' % (stamp, total, total, total))
    out.append('%s.400 session: state 0x19 (game mode 4)' % stamp)
    return '\n'.join(out) + '\n'


def write(tmp, name, text):
    p = os.path.join(tmp, name)
    with open(p, 'w') as f:
        f.write(text)
    return p


def main():
    static = {i: (-10608.2 + 7 * i, -15.0, 26299.5 + 3 * i) for i in range(347)}            # built on both sides, same places
    ring = {347 + k: (15884.0 + dx, -15.0, 27165.0 + dz) for k, (dx, dz) in enumerate(
        [(-410, 269), (-560, 119), (-560, -119), (-410, -269), (411, -269), (561, -119), (561, 119), (411, 269)])}
    host_pts = dict(static); host_pts.update(ring)
    with tempfile.TemporaryDirectory() as tmp:
        host = write(tmp, 'host.log', log(host_pts, total=1371, old_dump=True))
        client = write(tmp, 'client.log', log(static, total=1371))
        same = write(tmp, 'same.log', log(host_pts, stamp='17:40:00', total=1371))
        moved = dict(host_pts); moved[5] = (0.0, 1.0, 2.0)
        moved_log = write(tmp, 'moved.log', log(moved, total=1371))

        dh, dc = P.read_dump(host), P.read_dump(client)
        check(dh is not None and len(dh['points']) == 1371, 'read_dump reads the LAST dump (1371 points, the old 1-point dump ignored): %s' % (dh and len(dh['points'])))
        check(dh['points'][0][1:4] == (-10608.2, -15.0, 26299.5), 'point 0 parsed with its place')
        check(len(P.built_points(dh)) == 355 and len(P.built_points(dc)) == 347, 'built points host 355 / client 347 (0 0 0 = unbuilt): %d / %d'
              % (len(P.built_points(dh)), len(P.built_points(dc))))

        r = P.compare(dh, dc)
        check(r['diverge'] and r['prefix'] == 347, 'divergence found at index 347: prefix %d' % r['prefix'])
        check(r['differ'] == list(range(347, 355)), 'the 8 differing indices are 347..354: %s' % r['differ'])
        check(r['host_extra'] == list(range(347, 355)) and r['client_extra'] == [], 'host-only 347..354, client-only none')
        check(r['h'][347] == (15474.0, -15.0, 27434.0), 'an extra point keeps its place: %s' % (r['h'][347],))

        r2 = P.compare(dh, P.read_dump(same))
        check(not r2['diverge'] and r2['prefix'] == 1371 and r2['differ'] == [], 'identical lists: no divergence, prefix = every index')

        r3 = P.compare(dh, P.read_dump(moved_log))
        check(r3['differ'] == [5] and r3['host_extra'] == [] and r3['client_extra'] == [], 'a point built on both but moved is a differ, not an extra: %s' % r3['differ'])

        jit = dict(host_pts); jit[350] = (jit[350][0] + 0.1, jit[350][1], jit[350][2] - 0.1)    # CR5 DM01: the seats differ by 0.1 unit
        r4 = P.compare(dh, P.read_dump(write(tmp, 'jit.log', log(jit, total=1371))))
        check(not r4['diverge'] and r4['jitter'] == [350], 'a 0.1-unit jitter is not a divergence, it is listed as jitter: %s / %s' % (r4['differ'], r4['jitter']))

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = P.main([host, '--compare', client])
        out = buf.getvalue()
        check(rc == 3, '--compare exits 3 on a divergence (got %d)' % rc)
        check('DIVERGE at index 347' in out and 'built on host only (8)' in out and '#347 (15474 -15 27434)' in out,
              '--compare names the index, the host-only count and the first extra point')
        check('0x6567e8' in out and 'MaxAsserts=200' in out, '--compare names the assert sites and the 200 limit')

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = P.main([host, '--compare', same])
        check(rc == 0 and 'IDENTICAL' in buf.getvalue(), '--compare exits 0 and says IDENTICAL on equal lists (got %d)' % rc)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = P.main([host])
        check(rc == 0 and 'points dumped: 1371' in buf.getvalue(), 'the plain summary still works (got %d)' % rc)

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = P.main([host, '--compare', write(tmp, 'empty.log', 'nothing here\n')])
        check(rc == 1, 'a compare log without a dump is exit 1 (got %d)' % rc)

    print('RESULT: %s (%d checks, %d failed)' % ('PASS' if not FAILS else 'FAIL', 14, len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == '__main__':
    sys.exit(main())
