#!/usr/bin/env python3
"""kl_rmi_cover_1108.py - are the kept OUTSIDE entities (skyline / buildings / backdrop meshes / traffic) held by an .rmi box of a room that is
drawn?  OFFLINE, READ ONLY (reads the live zips, writes nothing but the report you redirect).

  python tools/kl_rmi_cover_1108.py [MAP ...] [--zip <zip>] [--report <file>] [-v]
  (no MAP: DM03 DM06 DM03A DM06B DM01B DM07 DM09; each map's slot zip is found as <DD>\\KLExpansion\\Maps\\<MAP>\\F??_Main.zip)

WHY (research 11-06 on DM05A, kl2.exe read-only, see kl_club_rmi_1106.py): a moving entity (flag 0x4000) is drawn only while an .rmi box of a
visible room holds it.  This script measures, per map, which kept outside entities are held by no box of their parent room nor of the rooms
that hold a player eye.  The answer decides whether the box-enlarge precedent (kl_club_rmi_1106.py: one record, same count) is needed.

CLASSIFICATION of "outside" (GUESS: a heuristic, nothing in the format says it).  An entity is kept-outside when ALL of
  - it is a drawable class: 0x200002 (std object), 0x2000ff, 0x200012, 0x200006 (traffic car), has a model (model > 0), is not hidden at load
    (flag 0x400), is not under a CloneGroup* root, and its name has no glow / particle / light part;
  - AND one of: reason 'room'    its parent room's name says outside (Out, Outside, Backdrop, Rooftop, Skyline, Skydome, Street, Distance);
                reason 'traffic' it sits under a group named Traffic* or is a 0x200006;
                reason 'name'    its own name says build / facade / skyline / billboard / skydome / backdrop / distan / tower.
PARENT ROOM = nearest ancestor of tid 0x100021 / 0x10003f.  Its .rmi id is its SLOT (kl_scene.slots) + 2, not its REF label (graft_formats.md).
  MEASURED 11-08: with +2 every box id of DM05A (Roof 4085 = slot 4083), DM06B and DM07 names a room entity; without it 6 of 20 / 4 of 6 / 4 of 4 name an
  effect group.  Why +2 is not known (GUESS: the loader's room id space starts two above kl_scene's slots).
EYE ROOMS = rooms (other than backdrop rooms) with a box that holds a spawn point (tid 0x2004b0, name has SpawnPoint) raised by EYE_UP.
  GUESS: EYE_UP 170 cm (stand eye height) and that a spawn's position is at the feet.
BOUNDS = world AABB of the 8 corners of the model's mesh AABB (kl_fa_loot.Assets, drawn meshes) under the entity's world frame
  (kl_fa_loot.frames).  No mesh found -> a point at the entity origin (marked 'pt').  Conservative: a rotated mesh gets a larger box.
BOX test: flag 1 = axis aligned, flag 0 = oriented (matrix +0x04, 9 floats in the ZGEOM[1] / .gms form [col2, col1, col0] of the box
  frame: GUESS, it reads as identity for every flag-1 box).  An entity is FULL when all 8 corners are inside one box, PART when its bounds
  overlap one (compared as the AABB of the corners in the box frame, so slightly generous for oriented boxes), else NONE.
  GUESS: that the engine's box query uses the entity's bounds and overlap; if it uses the origin only, read the 'origin in box' column.
UNCOVERED = NONE against every box of the parent room and of the eye rooms (a backdrop room's own box counts for its own entities; those that
  only a backdrop box holds are listed as 'bd-only', the case 11-06 left as a contradiction).
ENLARGE: per uncovered group (parent room) the existing box of that room with the least added volume, grown in its own frame to hold the
  group's union; plus the non-backdrop boxes of OTHER rooms the grown box would overlap.  A room without any box: 'no box'.
"""
import glob
import os
import re
import struct
import sys
import zipfile
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = ('DM03', 'DM06', 'DM03A', 'DM06B', 'DM01B', 'DM07', 'DM09')
ROOM_TIDS = (0x100021, 0x10003f)
DRAW_TIDS = (0x200002, 0x2000ff, 0x200012, 0x200006)
CAR_TID = 0x200006
SPAWN_TID = 0x2004b0
HIDDEN = 0x400
DYNAMIC = 0x4000
RMI_BIAS = 2                        # .rmi room id = kl_scene slot + 2: 100 % of the ids of DM05A / DM06B / DM07 resolve to a room with it, 0 % without (11-08)
GAP_CM = 5000.0                     # uncovered entities closer than this (single linkage) are one group for the enlargement
EYE_UP = 170.0                      # GUESS: stand eye height above the spawn origin, cm
C_OFF, M_OFF, H_OFF, ROOM_OFF = 0x28, 0x04, 0x40, 0x4c
RE_ROOM = re.compile(r'(^|_)(out|outside|backdrop|rooftops?|skyline|skydome|street|distance)', re.I)
RE_NAME = re.compile(r'build|facade|skyline|billboard|skydome|backdrop|distan|tower', re.I)
RE_SKIP = re.compile(r'glow|particl|light|lamp', re.I)
RE_BACKDROP = re.compile(r'backdrop', re.I)


# ------------------------------------------------------------------ pure helpers (kl_rmi_cover_1108_test.py)
def corners(lo, hi):
    return [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]


def world_bounds(lo, hi, R, T):
    """Local AABB (lo, hi) under rows-matrix R and translation T -> (world lo, world hi, the 8 world corners)."""
    pts = [tuple(T[i] + sum(R[i][j] * c[j] for j in range(3)) for i in range(3)) for c in corners(lo, hi)]
    return tuple(min(p[i] for p in pts) for i in range(3)), tuple(max(p[i] for p in pts) for i in range(3)), pts


class Box:
    """One .rmi record: flag (1 axis aligned, 0 oriented), centre, half extents, frame columns, room SLOT."""

    def __init__(self, raw, index=0):
        self.index = index
        self.flag = struct.unpack_from('<I', raw, 0)[0]
        self.c = struct.unpack_from('<3f', raw, C_OFF)
        self.h = struct.unpack_from('<3f', raw, H_OFF)
        f = struct.unpack_from('<9f', raw, M_OFF)
        self.cols = (f[6:9], f[3:6], f[0:3])           # GUESS: [col2, col1, col0] order, as kl_fa_loot.m9_of
        self.room = struct.unpack_from('<I', raw, ROOM_OFF)[0]

    def local(self, p):
        d = [p[i] - self.c[i] for i in range(3)]
        return tuple(sum(col[i] * d[i] for i in range(3)) for col in self.cols)

    def world(self, q):
        return tuple(self.c[i] + sum(q[a] * self.cols[a][i] for a in range(3)) for i in range(3))

    def holds(self, p):
        q = self.local(p)
        return all(abs(q[a]) <= self.h[a] for a in range(3))

    def relation(self, pts):
        """'FULL' all points inside, 'PART' the points' bounds in the box frame overlap it, else 'NONE'."""
        qs = [self.local(p) for p in pts]
        if all(all(abs(q[a]) <= self.h[a] for a in range(3)) for q in qs):
            return 'FULL'
        if all(min(q[a] for q in qs) <= self.h[a] and max(q[a] for q in qs) >= -self.h[a] for a in range(3)):
            return 'PART'
        return 'NONE'

    def volume(self):
        return 8.0 * self.h[0] * self.h[1] * self.h[2]


def best_relation(rels):
    return 'FULL' if 'FULL' in rels else ('PART' if 'PART' in rels else 'NONE')


def grown(box, pts):
    """The box grown (in its own frame) to hold pts as well -> (centre, half) of the result."""
    qs = [box.local(p) for p in pts]
    lo = [min(-box.h[a], min(q[a] for q in qs)) for a in range(3)]
    hi = [max(box.h[a], max(q[a] for q in qs)) for a in range(3)]
    mid = tuple((lo[a] + hi[a]) / 2.0 for a in range(3))
    return box.world(mid), tuple((hi[a] - lo[a]) / 2.0 for a in range(3))


def box_extent(c, h, box):
    """World AABB of a (centre, half) in box's frame -> (lo, hi)."""
    class _B:
        pass
    b = _B()
    b.c, b.cols, b.h = c, box.cols, h
    pts = [Box.world(b, s) for s in corners([-h[0], -h[1], -h[2]], h)]
    return tuple(min(p[i] for p in pts) for i in range(3)), tuple(max(p[i] for p in pts) for i in range(3))


def clusters(ents, gap):
    """Single-linkage groups of entities whose world bounds are closer than gap (cm) on every axis -> list of lists."""
    n, par = len(ents), list(range(len(ents)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(n):
        for j in range(i + 1, n):
            a, b = ents[i], ents[j]
            if all(a['lo'][k] - gap <= b['hi'][k] and b['lo'][k] - gap <= a['hi'][k] for k in range(3)):
                par[find(i)] = find(j)
    out = {}
    for i in range(n):
        out.setdefault(find(i), []).append(ents[i])
    return sorted(out.values(), key=lambda g: -len(g))


def best_enlarge(boxes, pts):
    """Among boxes (one room's) the one that needs the least added volume to hold pts -> dict or None (no boxes)."""
    best = None
    for b in boxes:
        c, h = grown(b, pts)
        add = 8.0 * h[0] * h[1] * h[2] - b.volume()
        if best is None or add < best['added']:
            best = {'box': b.index, 'flag': b.flag, 'old_c': b.c, 'old_h': b.h, 'new_c': c, 'new_h': h, 'added': add,
                    'grow': tuple(h[a] - b.h[a] for a in range(3))}
    return best


def classify(room_name, name, tid, path_names):
    """-> 'room' | 'traffic' | 'name' | None (not outside).  path_names: names of the ancestors."""
    if tid not in DRAW_TIDS or RE_SKIP.search(name):
        return None
    if tid == CAR_TID or any(n.startswith('Traffic') for n in path_names):
        return 'traffic'
    if room_name and RE_ROOM.search(room_name):
        return 'room'
    if RE_NAME.search(name):
        return 'name'
    return None


# ------------------------------------------------------------------ the level
def slot_zip(m):
    d = os.path.join(GAME, 'KLExpansion', 'Maps', m)
    z = sorted(glob.glob(os.path.join(d, 'F*_Main.zip')))
    z = [p for p in z if not p.lower().endswith('.bots.zip')]
    if len(z) != 1:
        raise ValueError('%s: want one F??_Main.zip in %s, found %r' % (m, d, z))
    return z[0]


def model_bounds(As, model, cache):
    """Local AABB of a model's drawn meshes -> (lo, hi) or None."""
    if model not in cache:
        r = None
        try:
            lo, hi = [1e30] * 3, [-1e30] * 3
            for o in As.meshes(model):
                pos = As.geometry(o)[0]
                for p in pos:
                    for a in range(3):
                        lo[a], hi[a] = min(lo[a], p[a]), max(hi[a], p[a])
            if lo[0] <= hi[0]:
                r = (tuple(lo), tuple(hi))
        except (ValueError, IndexError, KeyError, struct.error, TypeError):
            r = None
        cache[model] = r
    return cache[model]


def analyse(zp, log=lambda *a: None):
    """-> dict: boxes, rooms, ents (list of dicts), eye_rooms, spawns"""
    import kl_fa_loot as L
    import kl_octree as O
    import kl_scene
    z = zipfile.ZipFile(zp)
    sc = kl_scene.read(z)
    names = {n.lower(): n for n in z.namelist()}
    rmi = [n for n in z.namelist() if n.lower().endswith('.rmi')]
    if len(rmi) != 1:
        raise ValueError('want one .rmi, found %r' % rmi)
    idx = O.RoomIndex.parse(z.read(rmi[0]))
    boxes = [Box(b.raw, i) for i, b in enumerate(idx.boxes)]
    fr = L.frames(sc)
    slots = sc.slots()
    As = L.Assets(zp)
    cache, ents, rooms, spawns, nomesh = {}, [], {}, [], [0]

    def walk(e, room, path):
        n = e.name.decode('latin1')
        if n.startswith('CloneGroup'):
            return
        if e.tid in ROOM_TIDS:
            room = e
            rooms[slots[e] + RMI_BIAS] = n
        if e.tid == SPAWN_TID and 'SpawnPoint' in n:
            spawns.append(fr[e][1])
        hid = bool(e.flags & HIDDEN)
        why = None if e.model <= 0 else classify(room.name.decode('latin1') if room else None, n, e.tid, path)
        if hid and e.tid != CAR_TID:
            why = None                              # hidden at load: not drawn (a hidden traffic CAR is kept: a spawner shows it later)
        if why:
            R, T = fr[e]
            mb = model_bounds(As, e.model, cache)
            if mb is None and e.tid != CAR_TID:
                nomesh[0] += 1                      # no drawn mesh (cover boxes, hulls): nothing for a box to cull
                why = None
        if why:
            if mb:
                lo, hi, pts = world_bounds(mb[0], mb[1], R, T)
            else:
                lo = hi = tuple(T)
                pts = [tuple(T)]
            ents.append({'name': n, 'why': why, 'dyn': bool(e.flags & DYNAMIC), 'car': e.tid == CAR_TID, 'hid': hid,
                         'room': slots[room] + RMI_BIAS if room else None,
                         'room_name': room.name.decode('latin1') if room else '-', 'lo': lo, 'hi': hi, 'pts': pts, 'T': tuple(T),
                         'pt': mb is None, 'tid': e.tid, 'slot': slots[e]})
        for k in e.kids:
            walk(k, room, path + [n])
    for r in sc.roots:
        walk(r, None, [])
    inv = {v: e for e, v in slots.items()}
    roomtid = {b.room: ((inv[b.room - RMI_BIAS].tid, inv[b.room - RMI_BIAS].name.decode('latin1')) if b.room - RMI_BIAS in inv else None) for b in boxes}
    bd = {s for s, n in rooms.items() if RE_BACKDROP.search(n)}
    eye = set()
    for p in spawns:
        q = (p[0], p[1] + EYE_UP, p[2])
        eye |= {b.room for b in boxes if b.holds(q) and b.room not in bd}
    by_room = {}
    for b in boxes:
        by_room.setdefault(b.room, []).append(b)
    for e in ents:
        own = by_room.get(e['room'], [])
        eyeb = [b for r in eye for b in by_room.get(r, [])]
        e['own'] = best_relation([b.relation(e['pts']) for b in own])
        e['eye'] = best_relation([b.relation(e['pts']) for b in eyeb])
        every = [b for b in boxes if b.relation(e['pts']) != 'NONE']
        e['held_by'] = sorted({b.room for b in every})
        e['origin_in'] = sorted({b.room for b in boxes if b.holds(e['T'])})
        got = [b for b in own + eyeb]
        e['status'] = best_relation([b.relation(e['pts']) for b in got])
        e['bd_only'] = e['status'] != 'NONE' and all(b.room in bd for b in got if b.relation(e['pts']) != 'NONE')
    return {'zip': zp, 'boxes': boxes, 'rooms': rooms, 'ents': ents, 'eye_rooms': sorted(eye), 'spawns': spawns, 'backdrops': sorted(bd), 'nomesh': nomesh[0], 'roomtid': roomtid,
            'by_room': by_room}


# ------------------------------------------------------------------ report
def f3(p):
    return '(%.0f,%.0f,%.0f)' % tuple(p)


def report(m, d, verbose=False):
    out = []
    ents = d['ents']
    rn = d['rooms']
    unc = [e for e in ents if e['status'] == 'NONE']
    out.append('=== %s  %s' % (m, d['zip']))
    out.append('boxes %d (flag1 %d, flag0 %d), rooms %d, spawns %d, eye rooms %s, backdrop rooms %s' % (
        len(d['boxes']), sum(b.flag == 1 for b in d['boxes']), sum(b.flag == 0 for b in d['boxes']), len(rn), len(d['spawns']),
        [(r, rn.get(r, '?')) for r in d['eye_rooms']], [(r, rn[r]) for r in d['backdrops']]))
    c = Counter((e['why'], 'car' if e['car'] else ('dyn' if e['dyn'] else 'static')) for e in ents)
    bad = sorted((r, v) for r, v in d['roomtid'].items() if v is None or v[0] not in ROOM_TIDS)
    out.append('boxes whose room SLOT is not a room entity in this scene: %s' % (bad or 'none'))
    out.append('KEPT %d  UNCOVERED %d (of which dynamic flag 0x4000 or car: %d; the rest are static, which the .oct room trees hold, not the .rmi: GUESS)   by kind %s' % (
        len(ents), len(unc), sum(e['dyn'] or e['car'] for e in unc), dict(c)))
    out.append('  status FULL %d PART %d NONE %d | bd-only (held only by a backdrop box) %d | origin outside every box %d | no mesh bounds (pt, cars only) %d | excluded: no drawn mesh %d' % (
        sum(e['status'] == 'FULL' for e in ents), sum(e['status'] == 'PART' for e in ents), len(unc), sum(e['bd_only'] for e in ents),
        sum(not e['origin_in'] for e in ents), sum(e['pt'] for e in ents), d['nomesh']))
    out.append('  by parent room (kept / uncovered / dynamic):')
    rr = OrderedDict()
    for e in ents:
        a = rr.setdefault(e['room'], [0, 0, 0])
        a[0] += 1
        a[1] += e['status'] == 'NONE'
        a[2] += e['dyn'] or e['car']
    for r, (k, u, dy) in rr.items():
        out.append('    room %-6s %-34s kept %5d  uncovered %5d  dynamic/car %5d  boxes %d' % (r, rn.get(r, '-'), k, u, dy, len(d['by_room'].get(r, []))))
    if not unc:
        out.append('  uncovered list: none')
        return out
    out.append('  UNCOVERED list (room, name, kind, dyn/static, world bounds, held by rooms):')
    shown = unc if verbose else unc[:60]
    for e in shown:
        out.append('    [%s] %-44s %-7s %-6s %s..%s  held_by %s' % (e['room_name'][:24], e['name'][:44], e['why'], 'dyn' if e['dyn'] else 'static',
                                                                    f3(e['lo']), f3(e['hi']), e['held_by'][:6]))
    if len(unc) > len(shown):
        out.append('    ... %d more (-v lists all)' % (len(unc) - len(shown)))
    out.append('  SMALLEST ENLARGEMENT per uncovered cluster (parent room, then single linkage gap %.0f cm); options: a box of the parent room / a box of an eye room:' % GAP_CM)
    grp = OrderedDict()
    for e in unc:
        grp.setdefault(e['room'], []).append(e)
    eyeboxes = [b for r in d['eye_rooms'] for b in d['by_room'].get(r, [])]
    for r, es in grp.items():
        for cl in clusters(es, GAP_CM):
            pts = [p for e in cl for p in e['pts']]
            lo = tuple(min(p[i] for p in pts) for i in range(3))
            hi = tuple(max(p[i] for p in pts) for i in range(3))
            out.append('    room %s %s: %d entities (%d dynamic or car), union %s..%s  e.g. %s' % (
                r, rn.get(r, '-'), len(cl), sum(e['dyn'] or e['car'] for e in cl), f3(lo), f3(hi), cl[0]['name'][:40]))
            for label, bs in (('parent room box', d['by_room'].get(r, [])), ('eye room box', [x for x in eyeboxes if x.room != r])):
                be = best_enlarge(bs, pts)
                if not be:
                    if bs or label.startswith('parent'):
                        out.append('      %s: none (a box record would have to be appended)' % label)
                    continue
                b = bs[[x.index for x in bs].index(be['box'])]
                nlo, nhi = box_extent(be['new_c'], be['new_h'], b)
                olo, ohi = box_extent(b.c, b.h, b)
                hit = sorted({(x.index, x.room, rn.get(x.room, '?')) for x in d['boxes']
                              if x.room not in (b.room, *d['backdrops']) and x.relation(corners(nlo, nhi)) != 'NONE' and x.relation(corners(olo, ohi)) == 'NONE'})
                out.append('      %s %d (room %s, flag %d): centre %s half %s -> centre %s half %s (half +%.0f/+%.0f/+%.0f, +%.3g cm3); world %s..%s -> %s..%s; newly overlaps other rooms: %s' % (
                    label, be['box'], b.room, be['flag'], f3(be['old_c']), f3(be['old_h']), f3(be['new_c']), f3(be['new_h']), *be['grow'], be['added'],
                    f3(olo), f3(ohi), f3(nlo), f3(nhi), sorted({h[1] for h in hit}) or 'none'))
    return out


def main(a):
    verbose = '-v' in a
    rep = a[a.index('--report') + 1] if '--report' in a else None
    one = a[a.index('--zip') + 1] if '--zip' in a else None
    skip = {a[i + 1] for i, x in enumerate(a) if x in ('--zip', '--report')}
    maps = [x for x in a if not x.startswith('-') and x not in skip] or list(MAPS)
    lines = ['kl_rmi_cover_1108 - read-only; see the module docstring for the classification and what is GUESS']
    for m in maps:
        zp = one or slot_zip(m)
        lines += report(m, analyse(zp), verbose)
        lines.append('')
    text = '\n'.join(lines)
    print(text)
    if rep:
        with open(rep, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(text + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
