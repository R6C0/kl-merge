#!/usr/bin/env python3
"""kl_club_rmi_1106.py - Last Call (DM05A) pass rmi1106 (candidate 2f): enlarge Roof .rmi box 7 upward and eastward so the escape heli stays in a
room that is drawn. OFFLINE, level data only. Used by `kl_lastcall_chain_1106.py chain --cam 2f` (pass 'rmi', after helicam).

  python tools/kl_club_rmi_1106.py stage [--in-dir <dir>] [--out <dir>] [--allow-md5 <8+ hex>]    (writes F01_Main.zip + bots zip + base.md5, no install.py)
  python tools/kl_club_rmi_1106.py check <zip> [<base zip>]

WHY (research 11-06, kl2.exe read-only): a dynamic entity (flag 0x4000) gets its rooms from the .rmi box query (ZCollisionWintel [0x138c868]); a frame is
collected only from rooms stamped by the visibility walk, which starts from the rooms whose .rmi box holds the EYE. Roof (slot 4085) has 17 boxes, all topping
out near y 2610, so a heli above that is held by the whole-map Backdrop box 59 only. In benches 2c/2d/2e the heli is drawn on the pad (inside Roof box 7) and
NOT after lift-off. GUESS (not proven): being outside every Roof box is why it vanishes; the .rmi data alone leaves a contradiction (Backdrop holds everything
and the eye stamps Backdrop). If the 2f bench still shows no heli, log the heli's room set (0x8df280) before blaming anything else.

EDIT (one record of 60; box count and slot ids stay, so no REF / SLOT renumbering; .oct and .rmc untouched):
  box 7 (room Roof, slot 4085): centre (7378.3,2035.2,3510.2) half (702.2,575.2,916.4)  ->  centre (7971,4030,3510) half (1295,2570,916)
  = x 6676..9266, y 1460..6600, z 2594..4426. Covers ROUTE_2E (7058..8800, 2271..6200, 3100..3467) and the 2e eye (7400,2500,2800). Roof box 2 starts at
  x 9266 (touching), Street box 1 is z -7074..-2490, CarShop box 58 z 4466..5694 y <= 1460: no overlap. ROUTE_2C (z up to 5600) is NOT covered.
  GUESS: the exact top y 6600 (the route peaks at 6200). The +0x34 'second point' is left as it was (GUESS: not part of the containment test).
  The tree item of box 7 gets the matching quantised bounds (kl_octree.quantise_box, rounded outwards); if the item then lies outside its node's loose cell
  the tree is rebuilt (build_tree) from the same items. Read back: parse, Tree.check, every other 0x58-byte record byte-identical, point queries.
"""
import hashlib
import json
import os
import shutil
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
OUT = r'C:\kl_build_1024\lcrmi_1106'
BOX_INDEX = 7
ROOF_SLOT = 4085
OLD_CENTRE = (7378.3193359375, 2035.199951171875, 3510.2099609375)
OLD_HALF = (702.243896484375, 575.1982421875, 916.430419921875)
NEW_CENTRE = (7971.0, 4030.0, 3510.0)
NEW_HALF = (1295.0, 2570.0, 916.0)
# points that must resolve to Roof (+ Backdrop 59) after the edit; the first two are the 2e eye and the route start (Roof before too)
ROOF_POINTS = ((7400.0, 2500.0, 2800.0), (7058.0, 2271.0, 3467.0), (8268.0, 5005.0, 3207.0), (8305.0, 5161.0, 3200.0), (8800.0, 6200.0, 3100.0))
BACKDROP = 59
C_OFF, H_OFF, ROOM_OFF = 0x28, 0x40, 0x4c


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def contains(raw, p):
    """Axis-aligned box record (flag 1) holds the world point p."""
    c = struct.unpack_from('<3f', raw, C_OFF)
    h = struct.unpack_from('<3f', raw, H_OFF)
    return all(abs(p[a] - c[a]) <= h[a] for a in range(3))


def boxes_at(idx, p):
    """Indices of the boxes holding p by brute force over the records (the ground truth the tree walk must agree with)."""
    return [k for k, b in enumerate(idx.boxes) if struct.unpack_from('<I', b.raw, 0)[0] == 1 and contains(b.raw, p)]


def tree_at(idx, p):
    return sorted(idx.tree.point(idx.tree.quantise(p)))


def edit(data):
    """.rmi bytes -> (new .rmi bytes, info). Raises ValueError unless box 7 is exactly the stock Roof box (or already the new one: idempotent, returns data)."""
    import kl_octree as O
    idx = O.RoomIndex.parse(data)
    if len(idx.boxes) <= BOX_INDEX:
        raise ValueError('the .rmi has %d boxes, no box %d' % (len(idx.boxes), BOX_INDEX))
    b = idx.boxes[BOX_INDEX]
    if b.room != ROOF_SLOT or struct.unpack_from('<I', b.raw, 0)[0] != 1:
        raise ValueError('box %d is not the axis aligned Roof box (room slot %d, flag %d)' % (BOX_INDEX, b.room, struct.unpack_from('<I', b.raw, 0)[0]))
    c, h = struct.unpack_from('<3f', b.raw, C_OFF), struct.unpack_from('<3f', b.raw, H_OFF)
    if c == NEW_CENTRE and h == NEW_HALF:
        return data, {'already': True}
    if c != OLD_CENTRE or h != OLD_HALF:
        raise ValueError('box %d is neither the stock Roof box nor the 2f box: centre %r half %r' % (BOX_INDEX, c, h))
    before = [bytes(x.raw) for x in idx.boxes]
    struct.pack_into('<3f', b.raw, C_OFF, *NEW_CENTRE)
    struct.pack_into('<3f', b.raw, H_OFF, *NEW_HALF)
    lo = tuple(NEW_CENTRE[a] - NEW_HALF[a] for a in range(3))
    hi = tuple(NEW_CENTRE[a] + NEW_HALF[a] for a in range(3))
    q = O.quantise_box(idx.tree.origin, idx.tree.scale, lo, hi)
    pos = [i for i, it in enumerate(idx.tree.items) if it[0] == BOX_INDEX]
    if len(pos) != 1:
        raise ValueError('box %d has %d tree items' % (BOX_INDEX, len(pos)))
    old_item = list(idx.tree.items[pos[0]])
    idx.tree.items[pos[0]] = [BOX_INDEX] + q
    rebuilt = False
    try:
        idx.tree.check()                    # the item must stay inside the loose cell of the node that holds it
    except ValueError:
        t = O.build_tree([list(it) for it in idx.tree.items], idx.tree.origin, idx.tree.scale, True)
        idx.tree = t.check()
        rebuilt = True
    out = idx.pack()
    problems = check_edit(data, out)
    if problems:
        raise ValueError('rmi read-back failed: ' + '; '.join(problems))
    return out, {'already': False, 'old_item': old_item, 'new_item': [BOX_INDEX] + q, 'tree_rebuilt': rebuilt, 'unchanged_records': len(before) - 1}


def check_edit(old, new):
    """Read the written .rmi back against the stock one. -> list of problems (empty = fine)."""
    import kl_octree as O
    bad = []
    a, b = O.RoomIndex.parse(old), O.RoomIndex.parse(new)
    if len(a.boxes) != len(b.boxes) or a.size != b.size:
        return ['box count/size changed: %d/%d -> %d/%d' % (len(a.boxes), a.size, len(b.boxes), b.size)]
    try:
        b.tree.check()
    except ValueError as e:
        bad.append('tree: %s' % e)
    if (a.tree.origin, a.tree.scale) != (b.tree.origin, b.tree.scale):
        bad.append('tree frame changed')
    diff = [k for k in range(len(a.boxes)) if bytes(a.boxes[k].raw) != bytes(b.boxes[k].raw)]
    if diff != [BOX_INDEX]:
        bad.append('records that differ: %r (want only [%d])' % (diff, BOX_INDEX))
    else:
        r = bytes(b.boxes[BOX_INDEX].raw)
        o = bytes(a.boxes[BOX_INDEX].raw)
        if struct.unpack_from('<3f', r, C_OFF) != NEW_CENTRE or struct.unpack_from('<3f', r, H_OFF) != NEW_HALF:
            bad.append('box %d does not read back as the 2f box' % BOX_INDEX)
        keep = [i for i in range(len(r)) if not (C_OFF <= i < C_OFF + 12 or H_OFF <= i < H_OFF + 12)]
        if any(r[i] != o[i] for i in keep):
            bad.append('box %d changed outside its centre / half extents' % BOX_INDEX)
    ia = {it[0]: it for it in a.tree.items}
    ib = {it[0]: it for it in b.tree.items}
    if sorted(ia) != sorted(ib):
        bad.append('tree items changed')
    else:
        for k in ia:
            if k != BOX_INDEX and ia[k] != ib[k]:
                bad.append('tree item of box %d changed' % k)
    for k, it in ib.items():                # every record's item must still cover its box (rounded outwards)
        raw = b.boxes[k].raw
        if struct.unpack_from('<I', raw, 0)[0] == 1 and k == BOX_INDEX:
            c, h = struct.unpack_from('<3f', raw, C_OFF), struct.unpack_from('<3f', raw, H_OFF)
            for corner in ((c[0] - h[0], c[1] - h[1], c[2] - h[2]), (c[0] + h[0], c[1] + h[1], c[2] + h[2])):
                qq = b.tree.quantise(corner)
                if not all(it[1 + x] <= qq[x] <= it[4 + x] for x in range(3)):
                    bad.append('item of box %d does not cover its corner %r' % (k, corner))
    lo = [NEW_CENTRE[x] - NEW_HALF[x] for x in range(3)]
    hi = [NEW_CENTRE[x] + NEW_HALF[x] for x in range(3)]
    for k, bx in enumerate(b.boxes):        # no OTHER room's box may overlap the enlarged volume (Roof's own boxes and Backdrop may)
        c, h = struct.unpack_from('<3f', bx.raw, C_OFF), struct.unpack_from('<3f', bx.raw, H_OFF)
        if k != BOX_INDEX and bx.room not in (ROOF_SLOT, b.boxes[BACKDROP].room) and all(c[x] - h[x] < hi[x] and c[x] + h[x] > lo[x] for x in range(3)):
            bad.append('box %d (room slot %d) overlaps the enlarged Roof box' % (k, bx.room))
    for p in ROOF_POINTS:
        got, want = tree_at(b, p), boxes_at(b, p)
        if got != want:
            bad.append('point %r: tree walk %r != brute force %r' % (p, got, want))
        if BOX_INDEX not in got or BACKDROP not in got:
            bad.append('point %r resolves to %r, want Roof box %d + Backdrop %d' % (p, got, BOX_INDEX, BACKDROP))
        if any(b.boxes[k].room not in (ROOF_SLOT, b.boxes[BACKDROP].room) for k in got):
            bad.append('point %r also in a non-Roof room: %r' % (p, [(k, b.boxes[k].room) for k in got]))
    return bad


def members(path):
    z = zipfile.ZipFile(path)
    return [(i.filename, z.read(i.filename)) for i in z.infolist()]


def rmi_name(names):
    r = [n for n in names if n.lower().endswith('.rmi')]
    if len(r) != 1:
        raise ValueError('want one .rmi member, found %r' % r)
    return r[0]


def build(src, dst, log=print):
    """plain zip -> plain zip; only the .rmi member changes. Reads both back and checks. -> info"""
    import kl_graft
    if os.path.abspath(src) == os.path.abspath(dst):
        raise ValueError('the output is the input')
    mem = members(src)
    nm = rmi_name([m[0] for m in mem])
    new, info = edit(dict(mem)[nm])
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    if info.get('already'):
        shutil.copyfile(src, dst)
        log('rmi already done: copied unchanged')
        return info
    kl_graft.write_zip(dst, [(n, new if n == nm else d) for n, d in mem])
    bad = check(dst, src)
    if bad:
        raise ValueError('zip read-back failed: ' + '; '.join(bad))
    log('rmi box %d enlarged to centre %r half %r (tree rebuilt: %s); only %s differs' % (BOX_INDEX, NEW_CENTRE, NEW_HALF, info['tree_rebuilt'], nm))
    return info


def check(zp, base=None):
    """Read the written zip back. With a base zip: only the .rmi member differs (.oct and .rmc byte-identical) and the .rmi differs in box 7 only.
    Without: the .rmi is the 2f box and parses, .oct parses. -> list of problems"""
    import kl_octree as O
    bad = []
    mem = members(zp)
    names = [m[0] for m in mem]
    d = dict(mem)
    nm = rmi_name(names)
    for ext in ('.oct', '.rmc'):
        n = [x for x in names if x.lower().endswith(ext)]
        if len(n) != 1:
            return ['want one %s member' % ext]
    O.Oct.parse(d[[x for x in names if x.lower().endswith('.oct')][0]])
    O.RoomIndex.parse(d[[x for x in names if x.lower().endswith('.rmc')][0]])
    if base:
        bm = members(base)
        if [m[0] for m in bm] != names:
            return ['member list differs from the base']
        bd = dict(bm)
        diff = [n for n in names if bd[n] != d[n]]
        if diff != [nm]:
            bad.append('members that differ: %r (want only %s)' % (diff, nm))
        bad += check_edit(bd[nm], d[nm])
    else:
        idx = O.RoomIndex.parse(d[nm])
        b = idx.boxes[BOX_INDEX]
        if struct.unpack_from('<3f', b.raw, C_OFF) != NEW_CENTRE or struct.unpack_from('<3f', b.raw, H_OFF) != NEW_HALF:
            bad.append('box %d is not the 2f box' % BOX_INDEX)
        idx.tree.check()
        for p in ROOF_POINTS:
            got = tree_at(idx, p)
            if BOX_INDEX not in got or BACKDROP not in got:
                bad.append('point %r resolves to %r' % (p, got))
    return bad


def stage(out=OUT, in_dir=MAPDIR, log=print, allow=()):
    import kl_botsonline
    names = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')
    src = os.path.join(in_dir, 'F01_Main.zip')
    h = md5(src)
    if not any(h.startswith(a.lower()) for a in allow if len(a) >= 8):
        raise ValueError('refusing: %s md5 %s is not in the allowed list %r (pass allow=)' % (src, h, list(allow)))
    os.makedirs(out, exist_ok=True)
    cp = os.path.join(out, '_in.zip')
    shutil.copyfile(src, cp)                       # the input is only ever READ, through this copy
    if md5(cp) != h:
        raise ValueError('the input changed while it was copied')
    final = os.path.join(out, 'F01_Main.zip')
    info = build(cp, final, log)
    os.remove(cp)
    plain = md5(final)
    kl_botsonline.convert(final, os.path.join(out, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    rep = {'in_dir': in_dir, 'in_md5': h, 'info': info, 'files': {n: md5(os.path.join(out, n)) for n in names}}
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    log('staged %s plain md5 %s' % (out, plain))
    return rep


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    if a and a[0] == 'check' and len(a) in (2, 3):
        bad = check(a[1], a[2] if len(a) == 3 else None)
        print('\n'.join(bad) or 'PASS')
        return 1 if bad else 0
    if a and a[0] == 'stage':
        stage(opt('--out', OUT), opt('--in-dir', MAPDIR), allow=[opt('--allow-md5', '')])
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
