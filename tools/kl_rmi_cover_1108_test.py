"""Off-game self-test of kl_rmi_cover_1108: pure helpers on synthetic .rmi records, no game files."""
import math, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_rmi_cover_1108 as C

fails = []


def t(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok:
        fails.append(name)


IDENT = (0, 0, 1, 0, 1, 0, 1, 0, 0)          # the [col2, col1, col0] form of the identity, as every flag-1 box stores it


def rec(flag, c, h, room, m9=IDENT):
    b = bytearray(0x58)
    struct.pack_into('<I', b, 0, flag)
    struct.pack_into('<9f', b, 4, *m9)
    struct.pack_into('<3f', b, 0x28, *c)
    struct.pack_into('<3f', b, 0x34, *c)
    struct.pack_into('<3f', b, 0x40, *h)
    struct.pack_into('<I', b, 0x4c, room)
    return bytes(b)


def box(c, h, room=7, flag=1, m9=IDENT, i=0):
    return C.Box(rec(flag, c, h, room, m9), i)


# record read-back
b = box((10.0, 20.0, 30.0), (1.0, 2.0, 3.0), room=4085)
t('record fields', b.c == (10.0, 20.0, 30.0) and b.h == (1.0, 2.0, 3.0) and b.room == 4085 and b.flag == 1)
t('identity local', b.local((11.0, 18.0, 33.0)) == (1.0, -2.0, 3.0))
t('holds on the edge', b.holds((11.0, 22.0, 27.0)) and not b.holds((11.01, 20.0, 30.0)))

# relations
inside = C.corners((9.5, 19.5, 29.5), (10.5, 20.5, 30.5))
over = C.corners((10.5, 20.0, 30.0), (14.0, 24.0, 34.0))
away = C.corners((50.0, 50.0, 50.0), (60.0, 60.0, 60.0))
t('FULL', b.relation(inside) == 'FULL')
t('PART', b.relation(over) == 'PART')
t('NONE', b.relation(away) == 'NONE')
t('touching counts as overlap', b.relation(C.corners((11.0, 20.0, 30.0), (12.0, 21.0, 31.0))) == 'PART')
t('best_relation', C.best_relation(['NONE', 'PART', 'FULL']) == 'FULL' and C.best_relation(['NONE', 'PART']) == 'PART' and C.best_relation([]) == 'NONE')

# oriented box: a quarter turn about Y.  Frame columns: col0 -> (0,0,-1), col1 -> (0,1,0), col2 -> (1,0,0); m9 = [col2, col1, col0]
q = (1, 0, 0, 0, 1, 0, 0, 0, -1)
o = box((0.0, 0.0, 0.0), (10.0, 1.0, 1.0), flag=0, m9=q)         # long along its local x = world -z
t('oriented holds along world z', o.holds((0.0, 0.0, -9.0)) and o.holds((0.0, 0.0, 9.0)))
t('oriented rejects along world x', not o.holds((9.0, 0.0, 0.0)))
t('oriented FULL / NONE', o.relation(C.corners((-0.5, -0.5, -8.0), (0.5, 0.5, 8.0))) == 'FULL' and o.relation(C.corners((5.0, -0.5, -0.5), (8.0, 0.5, 0.5))) == 'NONE')

# grown: result holds the old box and the points, and a no-op when already inside
c2, h2 = C.grown(b, away)
g = box(c2, h2)
t('grown holds the points', all(g.holds(p) for p in away))
t('grown keeps the old box', all(g.holds(p) for p in C.corners((9.0, 18.0, 27.0), (11.0, 22.0, 33.0))))
t('grown no-op', C.grown(b, inside) == (b.c, b.h))
og = box((0.0, 0.0, 0.0), (10.0, 1.0, 1.0), flag=0, m9=q)
c3, h3 = C.grown(og, [(0.0, 5.0, -20.0)])
g3 = box(c3, h3, flag=0, m9=q)
t('grown oriented holds point, keeps own frame', g3.holds((0.0, 5.0, -20.0)) and g3.holds((0.0, 0.0, 9.0)) and g3.cols == og.cols)
lo, hi = C.box_extent(c3, h3, og)
t('box_extent covers the point', lo[2] <= -20.0 and hi[1] >= 5.0)

# world_bounds: turn about Y by 90 degrees, rows matrix [[0,0,1],[0,1,0],[-1,0,0]]
R = [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]
wlo, whi, pts = C.world_bounds((0.0, 0.0, 0.0), (2.0, 1.0, 4.0), R, (100.0, 0.0, 0.0))
t('world_bounds turn+shift', wlo == (100.0, 0.0, -2.0) and whi == (104.0, 1.0, 0.0) and len(pts) == 8)

# best_enlarge picks the box that needs the least added volume
near = box((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), i=0)
far = box((100.0, 0.0, 0.0), (1.0, 1.0, 1.0), i=1)
be = C.best_enlarge([near, far], C.corners((3.0, 0.0, 0.0), (4.0, 1.0, 1.0)))
t('best_enlarge nearest box', be['box'] == 0 and be['grow'][0] > 0 and be['added'] > 0)
t('best_enlarge none', C.best_enlarge([], away) is None)

# clusters: single linkage on bounds
def ent(lo, hi):
    return {'lo': lo, 'hi': hi}


a1, a2, a3 = ent((0, 0, 0), (10, 10, 10)), ent((12, 0, 0), (20, 10, 10)), ent((1000, 0, 0), (1010, 10, 10))
cl = C.clusters([a1, a3, a2], 5.0)
t('clusters split', sorted(len(x) for x in cl) == [1, 2] and len(C.clusters([a1, a3, a2], 5000.0)) == 1)

# classification
t('classify room', C.classify('M09_A_Out_CityScapeFront', 'SO0301_Foo', 0x200002, []) == 'room')
t('classify backdrop room', C.classify('M09_Backdrop_A_00', 'x', 0x200002, []) == 'room')
t('classify skyscraper room', C.classify('M09_B_Skyscrabers_01a', 'Foo', 0x200002, []) == 'room')
t('classify name', C.classify('M05_A_Inside_Lounge', 'SO0501_Building_09_01', 0x200002, []) == 'name')
# (fix 1) traffic by NAME, not by tid
t('traffic by group', C.classify('M05_A_Inside', 'Wheel', 0x200002, ['Traffic!Cars!A']) == 'traffic')
t('traffic by spline group', C.classify(None, 'Car_01', 0x200002, ['TrafficSplines!Vehicles!']) == 'traffic')
t('traffic by KL_ group', C.classify(None, 'KL_Bus', 0x200006, ['KL_Traffic!']) == 'traffic')
t('traffic by template name', C.classify(None, 'Ground_JPN_Civilian_A_00', 0x200006, []) == 'traffic')
t('tid 0x200006 Ground tile is NOT traffic', C.classify('M03_FAA_Outside_04_Buildings', 'Ground_12', 0x200006, []) == 'room')
t('tid 0x200006 elsewhere is placeholder', C.classify(None, 'Car', 0x200006, []) == 'placeholder'
  and C.classify(None, 'WindowBlowup!BombWindow03', 0x200006, []) == 'placeholder')
t('tid 0x200002 unknown is not placeholder', C.classify(None, 'Car', 0x200002, []) is None)
t('classify skips glow / non-draw / interior', C.classify('Out_X', 'Glow01', 0x200002, []) is None and C.classify('Out_X', 'Building', 0x2000e1, []) is None
  and C.classify('M05_A_Inside_Lounge', 'Table', 0x200002, []) is None)
# (fix 2) play rooms: only the entity's own sky / building name counts
for nm in ('Debris_03', 'Object_12', 'Railing_A', 'Tree_edge_04', 'SO0100_M06_Ground_Border_A_38', 'PC0100_M06_GrassTall_A_11'):
    t('play room drops ' + nm, C.classify('M06_FAA_Out_Part_02a', nm, 0x200002, []) is None)
t('play room keeps Skyscraper', C.classify('M06_FAA_Out_Part_02a', 'Skyscraper_Small_D02', 0x200002, []) == 'name')
t('play room keeps far Building', C.classify('M06_A_Out_Part_01a', 'SO0501_Building_13_02', 0x200002, []) == 'name')
t('play room keeps Antenna', C.classify('M06_A_Out_Part_01a', 'SO0501_Antenna_01_02', 0x200002, []) == 'name')
t('non-play Out room keeps debris', C.classify('M09_A_Out_CityScapeFront', 'Debris_03', 0x200002, []) == 'room')
t('RE_PLAY rooms', all(C.RE_PLAY.search(r) for r in ('M06_A_Out_Part_01a', 'M09_B_Bus_Terminal_01a', 'M09_B_Overpass_01a', 'M09_B_Retomoto_Square_01a', 'M09_B_Street_01a',
                                                     'M09_B_Hotel_Street_01a', 'M03_FAA_Outside_01A', 'M09_A_Out_Roof_401')))
t('RE_PLAY not backdrop rooms', not any(C.RE_PLAY.search(r) for r in ('M09_A_Out_CityScapeFront', 'M03_FAA_Outside_04_Buildings', 'M06_A_Out_Visible_01a', 'M09_Backdrop_A_00')))
# (d) DM09 street rooms: facades, billboards, collapse groups are street props, not skyline; a skyline name still counts
for nm in ('SO0200_JPN_Facade_O_Front_A', 'PC0100_JPN_Glass_Ad_Billboard_03', 'CollapseGroup_Buildings_01', 'Collapse_FacadeA_01', 'SO0500_JPN_Office_Building_01', 'SO1200_JPN_CornerBuilding_02'):
    t('DM09 street drops ' + nm, C.classify('M09_B_Street_01a', nm, 0x200002, []) is None and C.classify('M09_B_Bus_Terminal_01a', nm, 0x200002, []) is None)
t('DM09 street keeps SkyL', C.classify('M09_B_Retomoto_Square_01a', 'SO0301_SkyL1_14', 0x200002, []) == 'name')
# (fix c) 'light' skip must not drop skylight / highlight
t('skip light', all(C.RE_SKIP.search(x) for x in ('Streetlight_01', 'Light_A', 'SpotLight', 'Flashlight', 'Lamp_3', 'glow', 'Particles')))
t('skylight / highlight survive skip', not C.RE_SKIP.search('Skylight_Big') and not C.RE_SKIP.search('SO0301_SkyLight_02') and not C.RE_SKIP.search('Highlight_Wall'))
t('skylight classified (not dropped)', C.classify('M09_A_Out_CityScapeFront', 'Skylight_Big', 0x200002, []) == 'room')

# (fix a) origin test vs overlap test differ: a box that touches the bounds but does not hold the origin
bb = box((0.0, 0.0, 0.0), (10.0, 10.0, 10.0))
tb = C.corners((8.0, -1.0, -1.0), (30.0, 1.0, 1.0))            # bounds reach into the box, origin (20,0,0) is outside it
t('overlap yes, origin no', bb.relation(tb) == 'PART' and not bb.holds((20.0, 0.0, 0.0)))
t('visibility nearer / bigger scores higher', C.visibility({'lo': (0, 0, 0), 'hi': (5000, 5000, 5000)}, [(10000, 0, 0)]) > C.visibility({'lo': (0, 0, 0), 'hi': (500, 500, 500)}, [(10000, 0, 0)])
  and C.visibility({'lo': (0, 0, 0), 'hi': (500, 500, 500)}, [(2000, 0, 0)]) > C.visibility({'lo': (0, 0, 0), 'hi': (500, 500, 500)}, [(20000, 0, 0)]))
fake = {'ents': [{'why': 'room', 'dyn': False, 'status': 'NONE', 'ostatus': 'OUT', 'bd_only': False, 'car': False},
                 {'why': 'room', 'dyn': False, 'status': 'PART', 'ostatus': 'OUT', 'bd_only': False, 'car': False},
                 {'why': 'traffic', 'dyn': True, 'status': 'FULL', 'ostatus': 'IN', 'bd_only': False, 'car': True},
                 {'why': 'placeholder', 'dyn': False, 'status': 'NONE', 'ostatus': 'OUT', 'bd_only': False, 'car': False}]}
cn = C.counts(fake)
t('counts: placeholder apart, both tests', cn['sky'] == 2 and cn['sky_ov'] == 1 and cn['sky_or'] == 2 and cn['sky_any'] == 2 and cn['trf'] == 1 and cn['trf_ov'] == 0
  and cn['ph'] == 1 and cn['ph_ov'] == 1)

print('%s: %d failed' % ('FAIL' if fails else 'ALL PASS', len(fails)))
sys.exit(1 if fails else 0)
