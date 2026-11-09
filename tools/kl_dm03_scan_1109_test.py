"""Off-game self-test of kl_dm03_scan_1109's pure helpers (classify, pair_leaves, within, world_box, hvk_by_ref) on synthetic data. No game files."""
import math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_dm03_scan_1109 as S

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


BS = chr(92)
t('classify: a steel door leaf', S.classify('ROOT' + BS + 'SecurityHall_01a' + BS + 'SI0201_M03_DoorSteel_B_01') == 'leaf')
t('classify: a garage wall piece with a door opening is a frame', S.classify('X' + BS + 'SI0200_M03_Garage_Wall_3xM_Door_03') == 'frame')
t('classify: Wall_Door_4m is a frame, not a leaf', S.classify('SI0200_M03_Wall_Door_4m_A_13') == 'frame')
t('classify: vault / gate / shutter are leaves', all(S.classify(n) == 'leaf' for n in ('BankVault_DDorSlide_01', 'Gate_A', 'RollerShutterA_04')))
t('classify: a money box is nothing', S.classify('PC0500_M03_MoneyBox_01') is None)
t('classify: only the last path element counts', S.classify('Doors!Group' + BS + 'Pillar_01') is None)

leaves = [dict(k=10, pos=(-150.0, 240.0, -6480.0)), dict(k=12, pos=(150.0, 240.0, -6480.0)), dict(k=30, pos=(2000.0, 240.0, -6480.0)),
          dict(k=40, pos=(-150.0, 800.0, -6480.0))]
pairs = S.pair_leaves(leaves)
t('pair_leaves: the two leaves 300 apart on one floor pair up', pairs == [(10, 12, 300)])
t('pair_leaves: a leaf one floor up does not pair', not any(40 in p[:2] for p in pairs))
t('pair_leaves: wider dist takes the far one too', (12, 30, 1850) in S.pair_leaves(leaves, dist=2000.0))
t('within: plan distance, None centre = always', S.within((0, 0, 0), None, 1) and S.within((3, 99, 4), (0, 0, 0), 5) and not S.within((3, 0, 4), (0, 0, 0), 4.9))


class Shape:
    pass


sh = Shape()
sh.vstride = 12
sh.verts = struct.pack('<9f', -1.2, 0.0, -0.02, 0.0, 2.2, 0.02, -0.6, 1.1, 0.0)        # the stock leaf slab's extremes in metres
ident = struct.pack('<12f', 1.0, 2.0, 3.0, 1, 0, 0, 0, 1, 0, 0, 0, 1) + struct.pack('<II', 777, 0)
lo, hi = S.world_box(ident, sh)
t('world_box: identity placement at (1,2,3) m -> cm box', lo == [-20, 200, 298] and hi == [100, 420, 302])
turned = struct.pack('<12f', 0.0, 0.0, 0.0, 0, 0, 1, 0, 1, 0, -1, 0, 0) + struct.pack('<II', 777, 0)   # x -> -z, z -> x
lo2, hi2 = S.world_box(turned, sh)
t('world_box: a turned placement swaps the horizontal extents', lo2 == [-2, 0, 0] and hi2 == [2, 220, 120])


class H:
    pass


h = H()
s1, s2 = Shape(), Shape()
s1.type, s1.inst = 1, [ident, turned]
s2.type, s2.inst = 4, [struct.pack('<12f', *([0.0] * 12)) + struct.pack('<II', 777, 0)]
h.shapes = [s1, s2]
d = S.hvk_by_ref(h)
t('hvk_by_ref: REF 777 has one static and one key-framed placement', sorted(x[0] for x in d[777]) == [1, 1, 4] and d[777][2] == (4, 1, 0))
t('PAIR_DIST covers a double door with a pillar between (300 cm)', S.PAIR_DIST >= 300.0)
print('RESULT: %s' % ('FAIL %d' % len(fails) if fails else 'PASS'))
sys.exit(1 if fails else 0)
