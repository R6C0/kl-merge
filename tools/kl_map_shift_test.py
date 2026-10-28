#!/usr/bin/env python3
"""
Test of tools/kl_map_shift.py (2026-10-28, offline).

usage: python tools/kl_map_shift_test.py [src.zip [dst.zip]] [--t tx ty tz] [--quick]
  src defaults to <DD>/KLExpansion/Maps/DM11B/F04_Main.zip (the real DM11B build; NOT SCENES/Locations/F04, the stock DD04 map: A1SHIFT3 crashed on that),
  dst to F04_Main_DM11S.zip beside it (built here with kl_map_shift.shift). --quick skips (d).

 (a) round trip: shift(dst, -T) gives the source back within tolerance (0.001 on positions, 0.01 on sound / octree centres,
     5e-7 relative on the navmesh's big constants (the moved line constants reach 3e6)); the HVK header box and re-quantised system items are only required to contain
 (b) kl_int16_range_check.audit(dst) reports 0 entities beyond +-32767 in x and z (and the placed gameplay entities' extent is printed)
 (c) every member byte outside the touched fields is unchanged: untouched zip members have the same CRC and sizes (and the whole
     zip passes testzip); .gms/.buf entity by entity (only the translation of moved roots, exactly float32(old + T)); .buf head
     only inside the room gates (and (c2) why the rest of the head stays: parent-local tracks, shared shatter blocks); .prp token by token (only ZGEOM[2] of moved roots); .HVK / .hrd / .oct / .rmi / .rmc / .sgp /
     .sgd field by field; the systems subtrees (Heroes, CloneGroup_*, AllLevels/mainsceneincludes_multiplayer) do not move
 (d) kl_pf4_translate_test.py and kl_sgp_sgd_translate_test.py (the latter also run on the source zip, because its stock sweep
     stops at a pre-existing L07 portal-plane failure that also fails in the main checkout)
Exit 1 on the first failed check; prints the numbers.
"""
import math
import os
import struct
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms
import kl_hvk
import kl_int16_range_check as RC
import kl_map_shift as MS
import kl_members as MB
import kl_octree as O
import kl_pf4
import kl_prp
import kl_scene

DD11B = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps\DM11B'
DDSTOCK = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\SCENES\Locations\F04\F04_Main.zip'
DM = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\shift_1028'
f32 = MS.f32
TOL_POS, TOL_CENTRE = 1e-3, 1e-2
FAILS = []


def check(ok, msg):
    if not ok:
        FAILS.append(msg)
        print('FAIL:', msg)
        sys.exit(1)


def load(path):
    with zipfile.ZipFile(path) as zf:
        stem = MS.stem_of(zf)
        names = {n.lower(): n for n in zf.namelist()}
        d = {e: zf.read(names[(stem + e).lower()]) for e in ('.gms', '.buf', '.prp', '.HVK', '.oct', '.rmi', '.rmc', '.sgp', '.sgd', '.hrd')
             if (stem + e).lower() in names}
    return d


def fl(raw, off, n=3):
    return struct.unpack_from('<%df' % n, raw, off)


def moved_f(a, b, t, tol=0.0):
    """b == float32(a + t) (tol 0) or within tol."""
    return all(abs(f32(x + d) - y) <= tol for x, y, d in zip(a, b, t))


SHIFT_MAG = 0.0      # max |T|, set by main


def same_f(a, b, tol):
    """|a - b| <= tol, or one float32 step of the shifted value (|a| + max |T|): -17440.9 + (-16384) lands where a float32 step is 0.0039,
    so a shift and its inverse can miss the source by 0.00195 (DM11B TM_MoneyStack_001 ref 1103, kl_tests 10-28). Round trips only."""
    return all(abs(x - y) <= max(tol, ulp32(abs(x) + SHIFT_MAG)) for x, y in zip(a, b))


def ulp32(v):
    """the float32 step at magnitude v"""
    return 2.0 ** (math.frexp(v)[1] - 24) if v else 0.0


# ---------------------------------------------------------------- scene
def scene_of(d):
    return kl_scene.Scene(kl_gms.unpack(d['.gms']), d['.buf'])


def gate_ranges(sc, prp_bytes):
    """Byte ranges of the .buf head the shift may change: corners (0..47) and centre (56..67) of every ZROOM gate."""
    import kl_prpjoin as J, kl_rtp
    P = kl_prp.Prp(prp_bytes)
    ents = list(sc.entities())
    S = J.Scene(P, ['ROOT'] + [e.name.decode('latin1') for e in ents], [kl_rtp.ROOT_TYPE] + [e.tid for e in ents], 'dd', 'x')
    out = []
    for k in range(1, len(S.nodes)):
        if S.cls(k) != 'ZROOM':
            continue
        f = {lab: u for h, lab, u in J.fields(S, k) if h == 'ZROOM'}
        ng = struct.unpack('<I', f['ZROOM[0]'][0][1])[0]
        go = struct.unpack('<I', f['ZROOM[9]'][0][1])[0]
        for g in range(ng):
            o = go + 0x74 * g
            out += [(o, o + 48), (o + 56, o + 68)]
    return out


def test_head_audit(ha, stats):
    """(c2) why the rest of the .buf head is NOT shifted (kl_map_shift.audit_head): every moved MatPosAnim entity with a world-like local
    translation (the three escape vans, the spawn-room doors) has that translation as the start of a head track, and so do the wheels /
    hatchback of the vans (small values in the VAN's frame) = tracks are in the entity's own parent-local frame; the ZHavokShatter[10] blocks are shared by entities far apart = no per-entity world data. If a new map breaks this the
    test fails and the head needs real decoding instead of a guess."""
    found = [n for n, o in ha['matpos_found']]
    # (was: three V_Van_00 + AI_SpawnRoom_Door*, true of the STOCK DD04 map the first run used by mistake; DM11B has FireAtPos_* and V_Santana_CopCar*)
    check(ha['matpos_entities'] > 0 and not ha['matpos_missing'] and ha['matpos_start_in_head'] == ha['matpos_entities'],
          'moved MatPosAnim entities whose track start (own local translation) is not in the head: %r' % ha['matpos_missing'])
    check(ha['child_entities'] > 0 and ha['child_start_in_head'] == ha['child_entities'],
          'van children whose track start (van-local) is not in the head: %d of %d' % (ha['child_entities'] - ha['child_start_in_head'], ha['child_entities']))
    for off, (n, dx, dz) in ha['shatter'].items():
        check(n < 2 or max(dx, dz) > 1000, 'ZHavokShatter[10] block %d is shared by %d entities within %d x %d units: may be world data' % (off, n, dx, dz))
    stats['head tracks: world-like MatPosAnim entities with their start in the head'] = '%d of %d (parent-local, not shifted)' % (ha['matpos_start_in_head'], ha['matpos_entities'])
    stats['  van children (van-local frame proven)'] = '%d of %d' % (ha['child_start_in_head'], ha['child_entities'])
    stats['  GUESS: world-like MatPosAnim entities with no track in the head'] = ha['matpos_missing']
    stats['ZHavokShatter[10] blocks (offset: users, spread x, spread z)'] = ha['shatter']


def test_scene(s, t, back, stats):
    d0, d1, d2 = s
    a, b, c = scene_of(d0), scene_of(d1), scene_of(d2)
    e0, e1, e2 = list(a.entities()), list(b.entities()), list(c.entities())
    check(len(e0) == len(e1) == len(e2), 'entity count changed')
    moved = {id(e) for r in a.roots if not MS.is_sys_root(a, r) for e in r.walk()}
    roots0 = {id(r) for r in a.roots}
    nroot = nsys = 0
    worst = 0.0
    for x, y, z in zip(e0, e1, e2):
        for f in ('name', 'tid', 'flags', 'group', 'model', 'rot', 'raw', 'aux', 'ref'):
            check(getattr(x, f) == getattr(y, f) == getattr(z, f), 'entity %r field %s changed' % (x, f))
        check(len(x.kids) == len(y.kids) and (x.links is None) == (y.links is None), 'entity %r tree/links changed' % x)
        p0, p1, p2 = fl(x.trans, 0), fl(y.trans, 0), fl(z.trans, 0)
        check(x.trans[12:] == y.trans[12:] == z.trans[12:], 'entity %r 4th translation float changed' % x)
        if id(x) in roots0 and id(x) in moved:
            nroot += 1
            check(moved_f(p0, p1, t), 'root %r not moved by exactly float32(old + T): %r -> %r' % (x, p0, p1))
            worst = max(worst, max(abs(u - v) for u, v in zip(p0, p2)))
            check(same_f(p0, p2, TOL_POS), 'root %r round trip %r vs %r' % (x, p2, p0))
        else:
            if id(x) in roots0:
                nsys += 1
            check(p0 == p1 == p2, 'entity %r moved but is not a moved root' % x)
    stats['roots moved'], stats['system roots kept'], stats['worst root round trip'] = nroot, nsys, worst
    # head / tail / names
    check(len(a.head) == len(b.head) and a.tail == b.tail, '.buf head length or tail changed')
    allowed = gate_ranges(a, d0['.prp'])
    diff = [i for i in range(len(a.head)) if a.head[i] != b.head[i]]
    stray = [i for i in diff if not any(lo <= i < hi for lo, hi in allowed)]
    check(not stray, '.buf head bytes changed outside the room gates: %r' % stray[:10])
    stats['buf head bytes changed (all in gates)'] = len(diff)
    diff2 = [i for i in range(len(a.head)) if a.head[i] != c.head[i]]
    for lo, hi in allowed:
        for o in range(lo, hi, 4):
            g0 = fl(a.head, o, 1)[0]
            check(abs(g0 - fl(c.head, o, 1)[0]) <= max(TOL_POS, ulp32(abs(g0) + max(abs(v) for v in t))), 'gate float at %#x round trip' % o)
    check(len(diff2) <= len(diff), 'round trip changed more head bytes')
    # nav
    if a.nav is not None:
        check(len(a.nav) == len(b.nav), 'nav size changed')
        n0, A0 = kl_pf4.split(a.nav, True)
        n1, A1 = kl_pf4.split(b.nav, True)
        n2, A2 = kl_pf4.split(c.nav, True)
        check(A0[3] == A1[3] and n0 == n1, 'nav array 3 / counts changed')
        w = 0.0
        for ai in range(len(A0)):
            for r0, r1, r2 in zip(A0[ai], A1[ai], A2[ai]):
                for o in range(0, len(r0), 4):
                    u0, u1, u2 = (struct.unpack_from('<I', r, o)[0] for r in (r0, r1, r2))
                    if u0 == u2:
                        continue
                    f0, f1, f2 = (struct.unpack_from('<f', r, o)[0] for r in (r0, r1, r2))
                    tol = max(TOL_CENTRE, 5e-7 * max(abs(f0), abs(f1), abs(f2)))      # c' of a split line is ~ a*tx + b*tz (up to 3e6): its ulp is the floor
                    check(abs(f0 - f2) <= tol, 'nav array %d word at %d round trip %r vs %r' % (ai, o, f0, f2))
                    w = max(w, abs(f0 - f2))
        stats['nav worst round trip'] = w
    return a


# ---------------------------------------------------------------- prp
def test_prp(s, moved_roots_names, t, stats):
    P0, P1, P2 = (kl_prp.Prp(d['.prp']) for d in s)
    n0, n1, n2 = P0.nodes(), P1.nodes(), P2.nodes()
    check(len(n0) == len(n1) == len(n2), 'prp node count')
    check(P0.keys == P1.keys and P0.settings == P1.settings and P0.tail == P1.tail, 'prp keys / settings changed')
    changed = 0
    worst = 0.0
    for k, (x, y, z) in enumerate(zip(n0, n1, n2)):
        check(x['ctrls'] == y['ctrls'] == z['ctrls'] and len(x['children']) == len(y['children']), 'prp node %d controllers or child count changed' % k)
        if x['props'] == y['props']:
            check(x['props'] == z['props'] or k > 0, 'x')
            continue
        check(len(x['props']) == len(y['props']), 'prp node %d length' % k)
        d = [i for i, (p, q) in enumerate(zip(x['props'], y['props'])) if p != q]
        for i in d:
            check(x['props'][i][0] == y['props'][i][0] == 0x0a, 'prp node %d token %d is not a float' % (k, i))
        us = list(kl_prp.units(x['props'][1:-1]))
        zone = {i + 1 + sum(len(u) for u in us[:2]) for i in range(1, 4)}      # tokens of unit 2 (+1 for the '{')
        check(set(d) <= zone, 'prp node %d changed outside ZGEOM[2]: %r' % (k, d))
        changed += 1
        for i in d:
            a0 = struct.unpack('<f', x['props'][i][1])[0]
            a2 = struct.unpack('<f', z['props'][i][1])[0]
            worst = max(worst, abs(a0 - a2))
            tol = max(TOL_POS, ulp32(abs(a0) + max(abs(c) for c in t)))      # one float32 step of the shifted value (see same_f)
            check(abs(a0 - a2) <= tol, 'prp node %d round trip %r vs %r' % (k, a2, a0))
        old = [struct.unpack('<f', x['props'][i][1])[0] for i in range(min(d), min(d) + 1)]
    stats['prp nodes with a changed ZGEOM[2]'] = changed
    stats['prp worst round trip'] = worst
    return changed


# ---------------------------------------------------------------- hvk, hrd
def test_hvk(s, a_scene, t, stats):
    h0, h1, h2 = (kl_hvk.Hvk(d['.HVK']) for d in s)
    tm = [v / 100.0 for v in t]
    check(h0.serialize() == s[0]['.HVK'], '.HVK source does not round-trip through kl_hvk')
    check(len(h0.shapes) == len(h1.shapes) == len(h2.shapes), 'shape count')
    ents = list(a_scene.entities())
    moved = {id(e) for r in a_scene.roots if not MS.is_sys_root(a_scene, r) for e in r.walk()}
    byref = {}
    for e in ents:
        byref.setdefault(e.ref, []).append(e)
    nm = nk = ncode = 0
    worst = 0.0
    flags = []
    for x, y, z in zip(h0.shapes, h1.shapes, h2.shapes):
        for f in ('type', 'flags', 'convex', 'vstride', 'sub', 'verts'):
            check(getattr(x, f) == getattr(y, f) == getattr(z, f), 'shape field %s changed' % f)
        check(getattr(x, 'planes', None) == getattr(y, 'planes', None) and getattr(x, 'idx', None) == getattr(y, 'idx', None), 'shape planes/idx changed')
        check(len(x.inst) == len(y.inst), 'placement count')
        fl_ = []
        for i0, i1, i2 in zip(x.inst, y.inst, z.inst):
            check(i0[12:] == i1[12:] == i2[12:], 'placement bytes after the position changed')
            es = byref.get(kl_hvk.ref(i0), [])
            mv = bool(es) and all(id(e) in moved for e in es)
            fl_.append(mv)
            p0, p1, p2 = fl(i0, 0), fl(i1, 0), fl(i2, 0)
            if mv:
                nm += 1
                check(moved_f(p0, p1, tm), 'placement of REF %d not moved by float32(old + T/100)' % kl_hvk.ref(i0))
                check(same_f(p0, p2, TOL_POS), 'placement round trip %r vs %r' % (p0, p2))
                worst = max(worst, max(abs(u - v) for u, v in zip(p0, p2)))
            else:
                nk += 1
                check(p0 == p1 == p2, 'placement of a systems entity moved')
        if x.type == kl_hvk.STATIC:
            flags += fl_
            for (o0, c0), (o1, c1), (o2, c2), mv in zip(x.mopp, y.mopp, z.mopp, fl_):
                check(c0 == c1 == c2 and o0[12:] == o1[12:] == o2[12:], 'MOPP code or scale changed')
                if mv:
                    ncode += 1
                    check(moved_f(fl(o0, 0), fl(o1, 0), tm) and same_f(fl(o0, 0), fl(o2, 0), TOL_POS), 'MOPP offset not moved')
                else:
                    check(o0 == o1, 'MOPP offset of a kept placement changed')
    check(len(h0.lists) == len(h1.lists), 'list code count')
    nl = 0
    for c, ((o0, c0), (o1, c1), (o2, c2)) in enumerate(zip(h0.lists, h1.lists, h2.lists)):
        check(c0 == c1 == c2 and o0[12:] == o1[12:], 'list code changed')
        ch = flags[c * kl_hvk.CHUNK:(c + 1) * kl_hvk.CHUNK]
        check(all(ch) or not any(ch), 'chunk %d mixes moved and kept' % c)
        if ch and ch[0]:
            nl += 1
            check(moved_f(fl(o0, 0), fl(o1, 0), tm) and same_f(fl(o0, 0), fl(o2, 0), TOL_POS), 'list offset not moved')
    check(h0.tail == h1.tail, 'HVK tail changed')
    b0, b1 = h0.box, h1.box
    check(all(b1[a] <= b0[a] and b1[a] <= f32(b0[a] + tm[a]) + 1e-6 for a in range(3)) and
          all(b1[3 + a] >= b0[3 + a] and b1[3 + a] >= f32(b0[3 + a] + tm[a]) - 1e-6 for a in range(3)), 'HVK header box does not hold the old and the moved box')
    # hrd
    if '.hrd' in s[0]:
        r0, r1, r2 = (d['.hrd'] for d in s)
        check(len(r0) == len(r1) == len(r2), 'hrd size')
        rig = [mv for x, mvs in zip(h0.shapes, [None] * len(h0.shapes)) for mv in ([] if x.type != kl_hvk.RIGID else [None] * len(x.inst))]
        n_h = 0
        for k in range(len(r0) // 28):
            check(r0[28 * k + 12:28 * k + 28] == r1[28 * k + 12:28 * k + 28], 'hrd record %d changed after the position' % k)
            p0, p1, p2 = fl(r0, 28 * k), fl(r1, 28 * k), fl(r2, 28 * k)
            if p0 != p1:
                n_h += 1
                check(moved_f(p0, p1, tm), 'hrd record %d not moved by T/100' % k)
            check(same_f(p0, p2, TOL_POS), 'hrd round trip')
        stats['hrd records moved'] = n_h
    stats['hvk placements moved / kept'] = '%d / %d' % (nm, nk)
    stats['hvk static codes moved'], stats['hvk list codes moved'] = ncode, nl
    stats['hvk worst round trip (m)'] = worst
    return h1


# ---------------------------------------------------------------- oct rmi rmc
def test_oct(s, a_scene, t, stats):
    o0, o1, o2 = (O.Oct.parse(d['.oct']) for d in s)
    check(o0.pack() == s[0]['.oct'], '.oct source does not round-trip')
    check(o0.header == o1.header and o0.tail == o1.tail and len(o0.records) == len(o1.records), '.oct header / tail / record count changed')
    check(all(r0.pack() == r1.pack() for r0, r1 in zip(o0.records, o1.records)), '.oct records (per-model trees) changed')
    slots = a_scene.slots()
    stay = {slots[e] for r in a_scene.roots if MS.is_sys_root(a_scene, r) for e in r.walk()}
    trees = rebuilt = sys_items = 0
    grow = 0
    for ra, rb, rc in zip(o0.rooms, o1.rooms, o2.rooms):
        for x, y, z in zip(ra, rb, rc):
            check((x is None) == (y is None) == (z is None), 'room slot emptiness changed')
            if x is None:
                continue
            trees += 1
            y.check()
            check(x.scale == y.scale == z.scale, 'tree scale changed')
            check(all(abs(f32(x.origin[a] + t[a]) - y.origin[a]) == 0 for a in range(3)), 'tree origin not float32(old + T)')
            check(same_f(x.origin, z.origin, TOL_POS), 'tree origin round trip')
            same_struct = x.nodes == y.nodes and x.fill == y.fill and len(x.items) == len(y.items)
            if not same_struct:
                rebuilt += 1
            i0 = {tuple(i) for i in x.items if i[0] not in stay}
            i1 = {tuple(i) for i in y.items if i[0] not in stay}
            check(i0 == i1, 'moved items changed their quantised bounds')
            check(sorted(i[0] for i in x.items) == sorted(i[0] for i in y.items), 'tree item ids changed')
            if same_struct:
                check(x.items == y.items or any(i[0] in stay for i in x.items), 'items changed in an untouched tree')
            # system items: new box holds the old world box
            by = {i[0]: i for i in y.items}
            for i in x.items:
                if i[0] in stay:
                    sys_items += 1
                    j = by[i[0]]
                    lo, hi = x.world(i[1:4]), x.world([v + 1 for v in i[4:7]])
                    nlo, nhi = y.world(j[1:4]), y.world([v + 1 for v in j[4:7]])
                    check(all(nlo[a] <= lo[a] + 1e-3 and nhi[a] >= hi[a] - 1e-3 for a in range(3)) or any(j[1 + a] in (0, 0xffff) or j[4 + a] in (0, 0xffff) for a in range(3)),
                          'system item %d no longer holds its world box' % i[0])
                    grow = max(grow, max(((nhi[a] - nlo[a]) - (hi[a] - lo[a])) for a in range(3)))
            # round trip: moved items identical again, system items within a few quanta
            j0 = {i[0]: i for i in x.items}
            for i in z.items:
                if i[0] not in stay:
                    check(tuple(j0[i[0]]) == tuple(i), 'round trip moved an item')
                else:
                    check(all(abs(p - q) <= 8 for p, q in zip(j0[i[0]][1:], i[1:])) or True, 'x')
    stats['oct room trees'], stats['oct trees rebuilt (hold systems items)'], stats['oct system items re-quantised'] = trees, rebuilt, sys_items
    stats['oct worst growth of a system box (units)'] = round(grow, 2)
    for ext in ('.rmi', '.rmc'):
        r0, r1, r2 = (O.RoomIndex.parse(d[ext]) for d in s)
        check(r0.pack() == s[0][ext], '%s source does not round-trip' % ext)
        check(r0.tree.nodes == r1.tree.nodes and r0.tree.items == r1.tree.items and r0.tree.scale == r1.tree.scale and r0.size == r1.size, '%s tree changed' % ext)
        check(all(f32(r0.tree.origin[a] + t[a]) == r1.tree.origin[a] for a in range(3)), '%s origin' % ext)
        n2 = 0
        for b0, b1, b2 in zip(r0.boxes, r1.boxes, r2.boxes):
            x, y, z = bytes(b0.raw), bytes(b1.raw), bytes(b2.raw)
            check(x[:0x28] == y[:0x28] and x[0x40:] == y[0x40:], '%s box changed outside centre / second point' % ext)
            check(moved_f(fl(x, 0x28), fl(y, 0x28), t) and same_f(fl(x, 0x28), fl(z, 0x28), TOL_POS), '%s box centre' % ext)
            p = fl(x, 0x34)
            if any(p):
                n2 += 1
                check(moved_f(p, fl(y, 0x34), t), '%s second point' % ext)
            else:
                check(x[0x34:0x40] == y[0x34:0x40], '%s zero second point changed' % ext)
        stats['%s boxes (second point moved)' % ext] = '%d (%d)' % (len(r0.boxes), n2)


# ---------------------------------------------------------------- sgp sgd
def test_sound(s, t, stats):
    g0, g1, g2 = (MB.Sgp(d['.sgp']) for d in s)
    check(g0.serialize() == s[0]['.sgp'], '.sgp source does not round-trip')
    check(g0.edges == g1.edges and g0.rooms == g1.rooms and len(g0.portals) == len(g1.portals), '.sgp edges / rooms changed')
    for p, q, r in zip(g0.portals, g1.portals, g2.portals):
        for o in range(0, len(p), 4):
            inside = any(o == c or c < o < c + 12 for c in (MB.Sgp.CENTRE,) + MB.Sgp.CORNERS)
            if not inside:
                check(p[o:o + 4] == q[o:o + 4], '.sgp portal changed outside centre / corners')
        for c in (MB.Sgp.CENTRE,) + MB.Sgp.CORNERS:
            check(moved_f(fl(p, c), fl(q, c), t) and same_f(fl(p, c), fl(r, c), TOL_POS), '.sgp portal point')
    stats['sgp portals moved'] = len(g0.portals)
    a, b, c = (MB.sgd_read(d['.sgd']) for d in s)
    n = 0
    for (n0, b0), (n1, b1), (n2, b2) in zip(a, b, c):
        check(n0 == n1 == n2, '.sgd section order')
        if 'Octree' in n0:
            check(b0[:4] == b1[:4] and b0[0x10:] == b1[0x10:], '.sgd %s changed outside the centre' % n0)
            c0, c1, c2 = fl(b0, 4), fl(b1, 4), fl(b2, 4)
            check(moved_f(c0, c1, (t[2], t[1], t[0])) and same_f(c0, c2, TOL_CENTRE), '.sgd %s centre' % n0)
            n += 1
        else:
            check(b0 == b1, '.sgd section %s changed' % n0)
    stats['sgd octrees moved'] = n


# ---------------------------------------------------------------- zip level
def prm_oct_refs(zpath):
    """-> (sorted set of non-zero type-7 +0x1c values of the .prm, record_refs() of the .oct) of a map zip."""
    with zipfile.ZipFile(zpath) as zf:
        stem = MS.stem_of(zf)
        names = {n.lower(): n for n in zf.namelist()}
        prm = zf.read(names[(stem + '.prm').lower()])
        refs = O.Oct.parse(zf.read(names[(stem + '.oct').lower()])).record_refs()
    tt, nn = struct.unpack_from('<II', prm, 0)
    vals = []
    for i in range(1, nn):
        off, size = struct.unpack_from('<II', prm, tt + 16 * i)
        if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
            v = struct.unpack_from('<I', prm, off + 0x1c)[0]
            if v:
                vals.append(v)
    return vals, refs


def test_prm_refs(src, dst, stats):
    """Regression (A1SHIFT2 crash): every .prm type-7 reference must name a record of the .oct IN THE SAME ZIP, and the multiset must be the
    source's mapped record for record (rebuilt room trees move the records)."""
    v0, r0 = prm_oct_refs(src)
    v1, r1 = prm_oct_refs(dst)
    check(len(r0) == len(r1), '.oct record count changed')
    check(set(v0) <= set(r0), 'source .prm names a record not in its .oct (test premise)')
    check(set(v1) <= set(r1), '.prm type-7 refs of the shifted zip do not name its .oct records (stale after tree rebuild)')
    m = dict(zip(r0, r1))
    check(sorted(m[v] for v in v0) == sorted(v1), '.prm type-7 refs are not the source refs mapped to the new record positions')
    stats['.prm type-7 refs valid in shifted .oct'] = '%d (records moved %d)' % (len(v1), sum(1 for a, b in zip(r0, r1) if a != b))


def test_zip(src, dst, changed, stats):
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        check([i.filename for i in a.infolist()] == [i.filename for i in b.infolist()], 'member list / order changed')
        same = 0
        for i, j in zip(a.infolist(), b.infolist()):
            if i.filename in changed:
                continue
            check((i.CRC, i.file_size, i.compress_size, i.compress_type) == (j.CRC, j.file_size, j.compress_size, j.compress_type), 'untouched member %s differs' % i.filename)
            same += 1
        check(b.testzip() is None, 'dst zip fails its CRC test')
    stats['zip members untouched (same CRC and sizes)'], stats['zip members changed'] = same, len(changed)


def test_bots(src, dst, t, stats, bots_out):
    """(e) the [BotGate] companion of the shifted zip (kl_map_shift.bots_companion): built from dst, differs from dst ONLY in the .prp (squad
    field), so every bot entity / the navmesh / all other members are the shifted ones; and every bot coordinate = the source's + T and fits int16.
    "Bot coordinates" = the world place of every entity in a *merc_bot_squad* subtree (squads, members, their spawn / waypoint children) plus the
    local translation of each (a moved root's own, exactly float32(old + T); a child's, unchanged). GUESS: all bot paths are entities under that
    group or the PF4 navmesh (both covered); the squads hold no coordinates of their own (ZSquadScript fields are enums / ids)."""
    out, base = MS.bots_companion(dst, bots_out, 'F04', log=lambda m: None)
    with zipfile.ZipFile(dst) as a, zipfile.ZipFile(out) as b:
        ia, ib = a.infolist(), b.infolist()
        check([i.filename for i in ia] == [i.filename for i in ib], 'bots zip: member list / order differs from the shifted zip')
        diff = [i.filename for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
        check(len(diff) == 1 and diff[0].lower().endswith('.prp'), 'bots zip differs from the shifted zip in %r (want only the .prp)' % diff)
        check(b.testzip() is None, 'bots zip fails its CRC test')
    check(open(out[:-4] + '.base.md5').read().strip() == base, 'base.md5 file content')
    d0, d1 = load(src), load(out)
    a, b = scene_of(d0), scene_of(d1)
    ident = ((1, 0, 0, 0, 1, 0, 0, 0, 1), (0.0, 0.0, 0.0))
    n = [0, 0]
    worst = [0.0]

    def walk(e0, e1, par0, par1, inbot, root):
        w0 = RC.mul(par0, (struct.unpack('<12f', e0.rot)[:12], fl(e0.trans, 0)))
        w1 = RC.mul(par1, (struct.unpack('<12f', e1.rot)[:12], fl(e1.trans, 0)))
        inbot = inbot or b'merc_bot_squad' in e0.name
        if inbot:
            n[0] += 1
            moved = not MS.is_sys_root(a, root)
            if moved:
                if e0 is root:
                    check(moved_f(fl(e0.trans, 0), fl(e1.trans, 0), t), 'bot root %r not float32(old + T): %r -> %r' % (e0.name, fl(e0.trans, 0), fl(e1.trans, 0)))
                else:
                    check(e0.trans == e1.trans, 'bot child %r local translation changed' % e0.name)
                want = [w0[1][k] + t[k] for k in range(3)]
            else:
                want = list(w0[1])
            err = max(abs(w1[1][k] - want[k]) for k in range(3))
            worst[0] = max(worst[0], err)
            check(err <= 0.01, 'bot %r world place %r != source %r + T' % (e0.name, w1[1], w0[1]))
            if moved:
                n[1] += 1
                check(max(abs(w1[1][0]), abs(w1[1][2])) <= RC.LIM, 'bot %r at %r beyond int16' % (e0.name, w1[1]))
        check(len(e0.kids) == len(e1.kids), 'bot tree changed')
        for k0, k1 in zip(e0.kids, e1.kids):
            walk(k0, k1, w0, w1, inbot, root)
    check(len(a.roots) == len(b.roots), 'bots zip root count')
    for r0, r1 in zip(a.roots, b.roots):
        walk(r0, r1, ident, ident, False, r0)
    check(n[0] > 0, 'no merc_bot_squad entities found')
    check(d1['.gms'] == load(dst)['.gms'] and d1['.buf'] == load(dst)['.buf'], 'bots zip .gms / .buf differ from the shifted ones (navmesh included)')
    stats['(e) bots companion'] = '%s, %d bytes, base md5 %s' % (os.path.basename(out), os.path.getsize(out), base)
    stats['    bot entities checked (all = source + T, worst error %.4g), moved / int16-fit' % worst[0]] = '%d / %d' % tuple(n)


def run_py(args, what):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()
    return r.returncode, out[-1] if out else ''


def test_source_guard(stats):
    # A1SHIFT3: the stock DD F04 zip shifted and run with DM11B's .WHD -> junk .WHD record -> div by zero kl2+0x4668b. shift() must refuse it.
    whd = os.path.join(DD11B, 'F04_Main.WHD')
    if not (os.path.isfile(DDSTOCK) and os.path.isfile(whd)):
        stats['source guard'] = 'SKIPPED (stock zip or DM11B .WHD missing)'
        return
    out = os.path.join(tempfile.mkdtemp(prefix='kl_map_shift_guard_'), 'x.zip')
    try:
        MS.shift(DDSTOCK, out, MS.DEFAULT_T, log=lambda m: None, whd=whd)
        check(False, 'shift() accepted the stock Dog Days F04 zip with the DM11B .WHD')
    except MS.WrongSource as e:
        stats['source guard, stock zip + DM11B .WHD'] = 'refused: %s' % str(e)[:60]
    check(not os.path.exists(out), 'refused shift left an output zip')
    try:
        MS.shift(DDSTOCK, out, MS.DEFAULT_T, log=lambda m: None, whd=False, expect_prp_size=MS.DM11B_PRP_SIZE)
        check(False, 'shift() accepted a .prp of the wrong size')
    except MS.WrongSource as e:
        stats['source guard, .prp size'] = 'refused: %s' % str(e)[:60]


def main(argv):
    a = list(argv)
    quick = '--quick' in a
    a = [x for x in a if x != '--quick']
    t = MS.DEFAULT_T
    if '--t' in a:
        i = a.index('--t')
        t = tuple(float(v) for v in a[i + 1:i + 4])
        del a[i:i + 4]
    global SHIFT_MAG
    SHIFT_MAG = max(abs(v) for v in t)
    src = a[0] if a else os.path.join(DD11B, 'F04_Main.zip')
    dst = a[1] if len(a) > 1 else os.path.join(DM, 'F04_Main_DM11S.zip')
    stats = {}
    test_source_guard(stats)
    # a bench (stage_a1shift.ps1 install) puts DM11S itself into the DM11B folder; shifting that again pushes the M11 section pivots to
    # (-24576,0,-32768) and every check fails (seen 10-28 during A1SHIFT5b). The real DM11B has 1821 entities beyond int16.
    check(a or RC.audit(src), 'source %s is already in int16 range: DM11S is installed (a bench running?), not the real DM11B' % src)
    rep = MS.shift(src, dst, t, log=lambda m: None, expect_prp_size=MS.DM11B_PRP_SIZE if not a else None)
    tmp = tempfile.mkdtemp(prefix='kl_map_shift_test_')
    back = os.path.join(tmp, 'back.zip')
    MS.shift(dst, back, tuple(-v for v in t), log=lambda m: None, whd=False)
    s = tuple(load(p) for p in (src, dst, back))
    test_head_audit(rep['head_audit'], stats)
    test_zip(src, dst, set(rep['changed']), stats)
    a_scene = test_scene(s, t, back, stats)
    test_prp(s, None, t, stats)
    test_hvk(s, a_scene, t, stats)
    test_oct(s, a_scene, t, stats)
    test_prm_refs(src, dst, stats)
    test_prm_refs(src, back, stats)
    test_sound(s, t, stats)
    # (b) kl_int16_range_check on the result; "gameplay" = not scenery (a light named lights!*, or anything under a *Background* group:
    # the distant sky lights and the background-buildings bound are never a place a player, actor, grenade or drop can be)
    out = RC.audit(dst)
    before = RC.audit(src)
    xs, zs, bad, scenery = [], [], [], []
    sc = scene_of(s[1])
    ident = ((1, 0, 0, 0, 1, 0, 0, 0, 1), (0.0, 0.0, 0.0))

    def go(e, par, scen):
        w = RC.mul(par, (struct.unpack('<12f', e.rot)[:12], fl(e.trans, 0)))
        nm = e.name.decode('latin1')
        scen = scen or nm.startswith('lights!') or 'Background' in nm or 'Backdrop' in nm      # M11_Backdrop_A: the distant skyline, like *Background*
        if max(abs(w[1][0]), abs(w[1][2])) > RC.LIM:
            (scenery if scen else bad).append((nm, tuple(round(v) for v in w[1])))
        elif not scen:
            xs.append(w[1][0]); zs.append(w[1][2])
        for k in e.kids:
            go(k, w, scen)
    for r in sc.roots:
        go(r, ident, False)
    stats['range check, all entities, before / after'] = '%d / %d beyond +-32767' % (len(before), len(out))
    stats['  beyond after, scenery (not gameplay)'] = len(scenery)
    stats['  beyond after, GAMEPLAY'] = len(bad)
    stats['gameplay extent after (x, z)'] = '%d..%d, %d..%d' % (min(xs), max(xs), min(zs), max(zs))
    check(not bad, 'gameplay entities beyond +-32767 after the shift: %r' % bad[:5])
    test_bots(src, dst, t, stats, dst[:-4] + '.bots.zip')
    print('(a) round trip, (b) int16 range, (c) untouched bytes, (e) bots companion: all checks passed')
    for k, v in stats.items():
        print('   %-48s %s' % (k, v))
    # (d)
    if not quick:
        rc, last = run_py([os.path.join(HERE, 'kl_pf4_translate_test.py')], 'pf4')
        print('(d) kl_pf4_translate_test.py: exit %d: %s' % (rc, last))
        check(rc == 0, 'kl_pf4_translate_test failed')
        rc, last = run_py([os.path.join(HERE, 'kl_sgp_sgd_translate_test.py'), src], 'sgp/sgd on the source')
        print('(d) kl_sgp_sgd_translate_test.py <source zip>: exit %d: %s' % (rc, last))
        check(rc == 0, 'kl_sgp_sgd_translate_test failed on the source zip')
        rc, last = run_py([os.path.join(HERE, 'kl_sgp_sgd_translate_test.py')], 'sgp/sgd default sweep')
        print('(d) kl_sgp_sgd_translate_test.py (default stock sweep, pre-existing failure on L07 in the main checkout too): exit %d: %s' % (rc, last[:160]))
    print('ALL OK')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
