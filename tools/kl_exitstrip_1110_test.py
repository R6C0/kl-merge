"""Off-game self-test for tools/kl_exitstrip_1110.py (no game, no zips): table geometry, the swept-footprint maths on a synthetic lane, install.py generation and a scratch
install / refuse / undo round trip for every map of the table."""
import hashlib, math, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy
import kl_exitstrip_1110 as D

D.np = numpy

TPL = '''"""Installs / undoes DD10 DOOR FIX 1109 on the live DD10 files (<name>.before-dd10doorfix1109).
"""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days'
MAP, TAG = 'DD10', '.before-dd10doorfix1109'
FILES = [('F07_Main.zip', 'aa', 'bb')]


def main(a):
    return 0
'''


def check(c, msg):
    print('%s %s' % ('ok  ' if c else 'FAIL', msg))
    return 0 if c else 1


def main():
    bad = 0
    # synthetic lane: van drives east along z = 0 (heading +x = atan2(1, 0)), then reverses west with the same heading
    lane = [(x, 0.0, math.pi / 2) for x in range(-2000, 2001, 100)] + [(x, 0.0, math.pi / 2) for x in range(2000, -2001, -100)]
    rect_in = (-300, 300, -200, 200)
    bad += check(not D.clear_of_lane(lane, rect_in)[0], 'a box across the lane is hit (forward and reverse legs)')
    bad += check(D.clear_of_lane(lane, (-300, 300, D.HW + 10, D.HW + 400))[0], 'a strip %g cm off the lane centre is clear' % (D.HW + 10))
    bad += check(not D.clear_of_lane(lane, (-300, 300, D.HW - 10, D.HW + 400))[0], 'a strip %g cm off the lane centre is hit' % (D.HW - 10))
    bad += check(not D.clear_of_lane(lane, (-300, 300, -D.HW - 400, -D.HW + 10))[0] and D.clear_of_lane(lane, (-300, 300, -D.HW - 400, -D.HW - 10))[0], 'same on the other side')
    top = D.choose(lane, (-450, 450, -450, 450), (-450, 450, 200, 450))
    bad += check(bool(top) and top[0][4] >= D.HW and top[0][0] > 0, 'choose() prefers the free rectangle that overlaps the ally box (z %g..%g)' % (top[0][4], top[0][5]))
    for m, c in D.MAPS.items():
        o, n = D.rect_of(c['old_at'], c['old_half']), D.rect_of(c['new_at'], c['new_half'])
        bad += check(o[0] <= n[0] and n[1] <= o[1] and o[2] <= n[2] and n[3] <= o[3], '%s: new box inside the old one' % m)
        bad += check(all(v % 10 == 0 or v == w for v, w in zip(n, o)) and c['new_at'][1] == c['old_at'][1] and c['new_half'][1] == c['old_half'][1], '%s: changed edges on 10 cm, y kept' % m)
        bad += check(min(n[1] - n[0], n[3] - n[2]) >= 200, '%s: strip at least 2 m on both sides' % m)
        bad += check(all(len(v) == 32 for v in c['live'].values()) and c['zip'] == c['slot'] + '_Main.zip', '%s: live pins are full md5s' % m)
    sm = {}
    for m, c in D.MAPS.items():
        sm = {c['zip']: 'a' * 32, c['bots']: 'b' * 32, c['base']: 'c' * 32}
        t = D.make_install(m, c, sm, TPL)
        bad += check(("MAP, TAG = '%s', '.before-exitstrip1110'" % m) in t and ("'%s', '%s', '%s')" % (c['zip'], c['live'][c['zip']], 'a' * 32)) in t and 'before-dd10doorfix' not in t and 'KLJoin.ini' not in t,
                     '%s: install.py: map, tag, three pinned rows' % m)
    try:
        D.template_text()
        have_tpl = True
    except SystemExit:
        have_tpl = False
    if have_tpl:
        for m, c in D.MAPS.items():
            with tempfile.TemporaryDirectory() as tmp:
                kit, game = os.path.join(tmp, 'kit'), os.path.join(tmp, 'game')
                d = os.path.join(game, 'KLExpansion', 'Maps', m)
                os.makedirs(kit)
                os.makedirs(d)
                md = lambda b: hashlib.md5(b).hexdigest()
                names = list(c['live'])
                data = {n: n.encode() + b' live' for n in names}
                stg = {n: n.encode() + b' staged' for n in names}
                live = {n: md(data[n]) for n in names}
                for n in names:
                    open(os.path.join(d, n), 'wb').write(data[n])
                    open(os.path.join(kit, n), 'wb').write(stg[n])
                cfg = dict(c, live=live)
                open(os.path.join(kit, 'install.py'), 'w', newline='\n').write(D.make_install(m, cfg, {n: md(stg[n]) for n in names}))
                run = lambda *a: subprocess.run([sys.executable, os.path.join(kit, 'install.py'), '--game', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
                bad += check(run('--dry').returncode == 0, '%s: scratch --dry' % m)
                bad += check(run().returncode == 0 and all(open(os.path.join(d, n), 'rb').read() == stg[n] for n in names), '%s: scratch install' % m)
                bad += check(run().returncode != 0, '%s: second install refused' % m)
                bad += check(run('--undo').returncode == 0 and all(open(os.path.join(d, n), 'rb').read() == data[n] for n in names), '%s: scratch undo byte exact' % m)
    print('RESULT: %s' % ('FAIL %d' % bad if bad else 'PASS'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
