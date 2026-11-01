"""kl_dmcarcover_1101_test.py - self-test of tools/kl_dmcarcover_1101.py (re/dm_car_cover_1101.md): a synthetic ZHavokCar, then the real DM01 / DM03 zips
when the game folder is there (skipped cleanly otherwise).  Exit 0 only when every check passes."""
import os, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dmcarcover_1101 as C
import kl_fa

FAIL = []


def check(name, ok, why=''):
    print('%s %s%s' % ('PASS' if ok else 'FAIL', name, (' - ' + why) if (why and not ok) else ''))
    if not ok:
        FAIL.append(name)


class P:
    def __init__(self):
        self.keys = ['', 'TRUCK', 'NORMAL_CAR', 'CHASING_CAR']

    def key_index(self, s):
        if s not in self.keys:
            self.keys.append(s)
        return self.keys.index(s)

    def key(self, tok):
        return self.keys[tok]


class FakeScene:
    def __init__(self, type_name, flag):
        self.p = P()
        tok = lambda op, pl: [(op, pl)]
        us = [tok(0x0c, struct.pack('<I', 0))] * 6 + [tok(0x09, bytes(4))] * 2 + [tok(0x09, bytes(4))] * 3     # ZGEOM, ZSTDOBJ, ZLNKOBJ stand-ins
        for i in range(13):                                    # ZHavokCar fields
            if i == C.TYPE_I:
                us.append(tok(0x0c, struct.pack('<I', self.p.key_index(type_name))))
            elif i == C.FLAG_I:
                us.append(tok(0x06, bytes([flag])))
            else:
                us.append(tok(0x09, bytes(4)))
        self.us = us
        self.nodes = [{'props': [(0x02, b'')] + [t for u in us for t in u] + [(0x7e, b'')], 'ctrls': []}]
        self.path = [r'ROOT\Cars\T\Ground_01']

    def resolve(self, s):
        return [0] if s == self.path[0] else []

    def cls(self, k):
        return 'ZHavokCar'


def synthetic():
    sc = FakeScene('TRUCK', 1)
    us = C.car_units(sc, 0)
    check('synthetic: 24 units (11 + 13)', len(us) == C.BASE + 13)
    done = C.apply_edits(sc, us, {C.TYPE_I: ('TRUCK', 'NORMAL_CAR'), C.FLAG_I: (1, 0)})
    check('synthetic: two fields changed', done == [(1, 'TRUCK', 'NORMAL_CAR'), (9, 1, 0)], str(done))
    check('synthetic: values now NORMAL_CAR / 0', kl_fa.value(sc, us[C.BASE + 1]) == 'NORMAL_CAR' and kl_fa.value(sc, us[C.BASE + 9]) == 0)
    check('synthetic: nothing else touched', all(us[i] == C.car_units(FakeScene('TRUCK', 1), 0)[i] for i in range(len(us)) if i not in (C.BASE + 1, C.BASE + 9)))
    check('synthetic: idempotent', C.apply_edits(sc, us, {C.TYPE_I: ('TRUCK', 'NORMAL_CAR'), C.FLAG_I: (1, 0)}) == [])
    try:
        C.apply_edits(FakeScene('VAN', 1), C.car_units(FakeScene('VAN', 1), 0), {C.TYPE_I: ('TRUCK', 'NORMAL_CAR')})
        check('synthetic: unexpected old value refused', False)
    except ValueError:
        check('synthetic: unexpected old value refused', True)


def real():
    base = os.path.join(C.GAME, 'KLExpansion', 'Maps')
    cases = [('DM01', 'F01_Main.zip', False), ('DM01', 'F01_Main.bots.zip', False), ('DM03', 'F03_Main.zip', True), ('DM03', 'F03_Main.bots.zip', True)]
    ran = 0
    for mp, zn, opt in cases:
        src = os.path.join(base, mp, zn)
        if not os.path.isfile(src):
            print('SKIP %s %s: not installed' % (mp, zn))
            continue
        sc, _a, _b = kl_fa.load(src)
        if not all(len(sc.resolve(p)) == 1 for p, _e in C.plan_for(mp, True)):
            print('SKIP %s %s: the planned cars are not in this build (already another stage?)' % (mp, zn))
            continue
        # a stage that was already applied (the live zip is the output) has the new values: nothing to test then
        already = all(kl_fa.value(sc, C.car_units(sc, sc.resolve(p)[0])[C.BASE + C.FLAG_I]) == 0 for p, _e in C.plan_for(mp, True))
        if already:
            print('SKIP %s %s: carcover already applied' % (mp, zn))
            continue
        with tempfile.TemporaryDirectory(prefix='carcover_t_') as td:
            for dm03 in ((False, True) if mp == 'DM03' else (False,)):
                dst = os.path.join(td, 'o%d_%s' % (dm03, zn))
                r = C.build(mp, src, dst, dm03, log=lambda *_: None)
                plan = C.plan_for(mp, dm03)
                tag = '%s %s%s' % (mp, zn, ' --dm03' if dm03 else '')
                if not plan:
                    check(tag + ': nothing planned -> same md5', r['md5_in'] == r['md5_out'])
                    continue
                mem = C.members_differing(src, dst)
                check(tag + ': only the .prp member differs', mem is not None and len(mem) == 1 and mem[0].lower().endswith('_main.prp'), str(mem))
                d = C.diff_scenes(src, dst)
                want = sorted((p, 'props') for p, _e in plan)
                check(tag + ': only the planned nodes differ (props)', d is not None and sorted(d) == want, str(d))
                sc2, _a, _b = kl_fa.load(dst)
                ok = True
                for p, edits in plan:
                    us = C.car_units(sc2, sc2.resolve(p)[0])
                    for i, (_old, new) in edits.items():
                        ok = ok and kl_fa.value(sc2, us[C.BASE + i]) == new
                check(tag + ': planned values set', ok)
                check(tag + ': same node count and paths', len(sc2.nodes) == len(sc.nodes) and sc2.path == sc.path)
                # idempotent: applying to the output changes nothing
                dst2 = os.path.join(td, 'again_%d_%s' % (dm03, zn))
                C.build(mp, dst, dst2, dm03, log=lambda *_: None)
                check(tag + ': second run is a no-op', C.diff_scenes(dst, dst2) == [])
                ran += 1
    return ran


if __name__ == '__main__':
    synthetic()
    real()
    print('RESULT: %s' % ('FAIL (%s)' % ', '.join(FAIL) if FAIL else 'PASS'))
    sys.exit(1 if FAIL else 0)
