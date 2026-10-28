#!/usr/bin/env python3
"""
Translate a whole Dog Days map build by a world vector T (2026-10-28, offline; design and numbers: re/map_shift_int16_1027.md).

WHY: online positions are int16 with no scale; DM11B (slot F04) lies at x -2644..44400, z -1057..47816, so with
T = (-12288, 0, -16384) (powers of two: the integer part of every float32 stays exact) it fits +-32767.

    shift(src_zip, dst_zip, T=DEFAULT_T)        -> report dict

WHAT IS TRANSLATED (everything below is a pure translation; scale / rotation / indices / ids are copied):
  .gms   translation of every top-level entity that is not a SYSTEMS subtree (children are parent-local, so the whole subtree moves);
         zero-translation baked roots get trans = T (their vertices are world coordinates, the entity transform composes)
  .prp   ZGEOM[2] of the same roots (the node's own copy of its place)
  .gms   PF4 navmesh (kl_pf4.translate)
  .buf   head: ZROOM gates (4 corners + centre, 0x74-byte records, ZROOM[9] / ZROOM[0])
  .HVK   placement position (+0, in metres = units / 100) of every placement whose entity moved, the MOPP offset (x, y, z, scale) of its
         static code and of every 510-chunk list code whose placements all moved, the header box (grown to hold old and new)
  .hrd   position of every rigid-body record whose instance moved (metres)
  .oct   the five room trees of every room: origin += T (quantised bounds stay for moved items; items of systems entities, which do NOT
         move, are re-quantised outwards into the new frame and the tree is rebuilt only when that breaks Tree.check)
         ZOctreeCompiled RECORDS are per-model (origin ~ 0, local frame): untouched
  .rmi .rmc   tree origin += T, every room box: centre (+0x28) += T, second point (+0x34) += T when it is not zero
  .sgp   Sgp.translate     .sgd   sgd_translate (point octree centres)
Systems subtrees stay where they are: AllLevels/mainsceneincludes_multiplayer, CloneGroup_*, Heroes (and their HVK placements).

NOT TRANSLATED, on purpose (2026-10-28 review; the claims below are measured by audit_head() and checked by the test, not decoded):
  .buf head 0..55,120: three long (x, 0, z) polylines at 7,936 / 23,600 / 36,476 (~600 points each). Each starts within 0.05 of the entity-local
    translation of V_Van_00 under F04_Escape_Vehicle_01 / _02 / _03 (ZGROUP + MatPosAnim). So they are the ZMatPosAnim tracks of the escape
    vans, written in the same frame as the entity's own .gms translation = PARENT-LOCAL. The Escape_Vehicle roots (zero translation) get T, the
    vans ride along; shifting the tracks too would move them twice. (The prp holds no pointer to them; the start-equals-translation match
    is the evidence. GUESS: MatPosAnim writes the local matrix. Only a live run shows the van drive-in.) The rest of the floats over 3000 in
    magnitude in 0..55,120 are misaligned bytes of packed data (garbage values 1e20+ beside them).
  .buf head 186,352..241,120 (the ZHavokShatter[10] offsets point to its start, 186,352 and 212,768, from 31 entities spread over 10,000 x
    10,000 units): the same kind of data. The first record (186,368) is (-4750, 0, 22010) = the local translation of AI_SpawnRoom_Door_02, the
    one at 187,872 is AI_SpawnRoom_Door_01's (-5095, 0, 18240), and the van parts (Shadow_Plane, Door_Hatchback, wheels) start there too. So
    it is MatPosAnim track data, entity-local, shared as one pool; ZHavokShatter[10] merely names an offset in it (GUESS: a default / unused
    pointer for entities without a track). One block serving extinguishers in 10 different rooms cannot be per-entity world data. NOT moved.
    The .sgd shatter octrees ARE moved (their centre follows the entity, kl_members).
  Other .buf head data (packed KEYS tracks 55,120..186,352, ZLNKOBJ / ZLNKWHANDS, ZParticleEmitter blocks, FDX bone dynamics, light / SND emitter
  data) is not decoded and is not moved; no prp pointer of those classes was found to hold an absolute position (GUESS).
  The .ANM files (assumed parent-local, as the van tracks are), .prm bounds of ordinary models (local) and .SND stay.
Unchanged zip members are copied compressed (no recompression), so every untouched byte is identical.
"""
import os
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms
import kl_hvk
import kl_members
import kl_octree as O
import kl_pf4
import kl_prp
import kl_prpjoin as J
import kl_rtp
import kl_scene

DEFAULT_T = (-12288.0, 0.0, -16384.0)
SYSTEM_PREFIXES = ('CloneGroup_', 'AllLevels/mainsceneincludes_multiplayer')
SYSTEM_FIRST = ('Heroes',)


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def is_system(name):
    n = name.decode('latin1') if isinstance(name, (bytes, bytearray)) else name
    return n.startswith(SYSTEM_PREFIXES) or n.split('!')[0] in SYSTEM_FIRST


HEROES_MAP_FRAME = 8192.0       # stock Dog Days: Heroes! at ~(843, 6070) = engine placeholders, kept. DM11B graft: at (33900, 29950) = the map's own spawn, must move


def heroes_move(sc):
    """2026-10-28: the real DM11B build authors its Heroes!/Henchmen spawn roots in the MAP frame (x 27700..34000, z 26300..30850; the
    stock map keeps them near 843, 6070). Left unmoved they sit beyond int16 and 12288 / 16384 units from the shifted spawn area, so
    Heroes move iff any of them is farther than HEROES_MAP_FRAME from the origin (decided per scene, so shift(-T) undoes it)."""
    return any(max(abs(v) for v in struct.unpack_from('<3f', r.trans, 0)[::2]) > HEROES_MAP_FRAME
               for r in sc.roots if r.name.decode('latin1').split('!')[0] in SYSTEM_FIRST)


def is_sys_root(sc, root):
    """is_system(root.name), except Heroes of a map that authors them in the map frame (heroes_move)."""
    if root.name.decode('latin1').split('!')[0] in SYSTEM_FIRST:
        return not heroes_move(sc)
    return is_system(root.name)


def add3(raw, off, d, fmt='<3f'):
    """3 floats of a bytearray at off, plus d (computed in double, rounded once to float32)."""
    v = struct.unpack_from(fmt, raw, off)
    struct.pack_into(fmt, raw, off, *[v[i] + d[i] for i in range(3)])


def stem_of(zf):
    g = [n for n in zf.namelist() if n.lower().endswith('.gms')]
    if len(g) != 1:
        raise ValueError('expected one .gms, found %d' % len(g))
    return g[0][:-4]


# ------------------------------------------------------------------ scene (.gms .prp .buf head)
def shift_scene(sc, prp_bytes, T, log):
    """sc is modified in place (roots, nav, head). -> (prp bytes, set of moved entity ids, info)."""
    ents = list(sc.entities())
    top = {}
    for r in sc.roots:
        for e in r.walk():
            top[id(e)] = r
    moved_roots = [r for r in sc.roots if not is_sys_root(sc, r)]
    moved = {id(e) for r in moved_roots for e in r.walk()}
    info = {'roots': len(sc.roots), 'moved_roots': len(moved_roots), 'zero_trans': 0, 'entities': len(ents), 'moved_entities': len(moved)}
    # .prp: ZGEOM[2] (unit 2 of the node's own property object) of the moved roots
    P = kl_prp.Prp(prp_bytes)
    if P.serialize() != prp_bytes:
        raise ValueError('.prp does not round-trip through kl_prp.Prp')
    nodes = P.nodes()
    if len(nodes) != len(ents) + 1:
        raise ValueError('%d prp nodes for %d entities' % (len(nodes), len(ents)))
    names = ['ROOT'] + [e.name.decode('latin1') for e in ents]
    tids = [kl_rtp.ROOT_TYPE] + [e.tid for e in ents]
    S = J.Scene(P, names, tids, 'dd', 'src')
    root_ix = {id(r) for r in moved_roots}
    bad = 0
    for k, e in enumerate(ents, 1):
        if id(e) not in root_ix:
            continue
        pos = struct.unpack_from('<3f', e.trans)
        if all(v == 0.0 for v in pos):
            info['zero_trans'] += 1
        n = nodes[k]
        us = [list(u) for u in kl_prp.units(n['props'][1:-1])]
        u = us[2]
        if not (u[0][0] == 0x01 and len(u) == 5 and all(t[0] == 0x0a for t in u[1:4])):
            raise ValueError('%s: ZGEOM[2] is not a 3-float array' % names[k])
        pv = [struct.unpack('<f', t[1])[0] for t in u[1:4]]
        if max(abs(a - b) for a, b in zip(pv, pos)) > 1e-3:
            bad += 1
        u[1:4] = [(0x0a, struct.pack('<f', pv[i] + T[i])) for i in range(3)]
        n['props'] = [n['props'][0]] + [t for uu in us for t in uu] + [n['props'][-1]]
        t = bytearray(e.trans)
        add3(t, 0, T)
        e.trans = bytes(t)
    info['prp_gms_place_mismatch'] = bad
    # PF4 navmesh
    if sc.nav is not None:
        sc.nav = kl_pf4.translate(sc.nav, T)
    # room gates
    head = bytearray(sc.head)
    seen, ngates = set(), 0
    for k in range(1, len(S.nodes)):
        if S.cls(k) != 'ZROOM' or id(ents[k - 1]) not in moved:
            continue
        f = {lab: u for h, lab, u in J.fields(S, k) if h == 'ZROOM'}
        ng = struct.unpack('<I', f['ZROOM[0]'][0][1])[0]
        go = struct.unpack('<I', f['ZROOM[9]'][0][1])[0]
        for g in range(ng):
            o = go + 0x74 * g
            if o in seen:
                raise ValueError('room gate at %#x claimed twice' % o)
            seen.add(o)
            for c in range(4):                       # corners: floats 0..11
                add3(head, o + 12 * c, T)
            add3(head, o + 14 * 4, T)                # centre: floats 14..16 (GUESS for the 12/13 floats: left, they are 0 in the stock gates)
            ngates += 1
    info['head_audit'] = audit_head(sc, S, ents, moved)       # before sc.head is replaced (the audit only reads the untouched regions)
    sc.head = bytes(head)
    info['gates'] = ngates
    return P.serialize(), moved, top, info


def audit_head(sc, S, ents, moved):
    """Evidence for what the shift does NOT touch in the .buf head (see the module docstring). -> info dict.
    matpos: moved ZMatPosAnim entities at |x| or |z| >= 1000 and how many have their own local (x, y, z) as a float triple in the head
    (= the track starts in the entity's own frame); child_*: the same for children of such a vehicle (wheels, hatchback: small local values,
    parent far from the origin) - their tracks are in the VAN's frame, which proves the frame rule for the van itself.
    shatter: ZHavokShatter[10] head offset -> (entities using it, widest spread of their summed-translation x / z); a block shared by entities
    far apart cannot hold per-entity world positions. World position here = sum of the translations up the parents (rotation ignored: the
    parents of these entities are zero-translation groups)."""
    head = sc.head
    info = {'matpos_entities': 0, 'matpos_start_in_head': 0, 'matpos_found': [], 'matpos_missing': [],
            'child_entities': 0, 'child_start_in_head': 0, 'shatter': {}}
    fl = [v for (v,) in struct.iter_unpack('<f', head[:len(head) // 4 * 4])]
    byint = {}
    for i, v in enumerate(fl):
        if v == v and abs(v) < 1e6:
            byint.setdefault(int(v // 2), []).append(i)          # 2-unit buckets: a lookup for "float within 1.0"

    def start_in_head(e, tol):
        x, y, z = struct.unpack_from('<3f', e.trans)
        return [i * 4 for b in (int(x // 2) - 1, int(x // 2), int(x // 2) + 1) for i in byint.get(b, ())
                if abs(fl[i] - x) < tol and i + 2 < len(fl) and abs(fl[i + 1] - y) < max(tol, 5.0) and abs(fl[i + 2] - z) < tol]

    pos, mp = {}, {}
    for k in range(1, len(S.nodes)):
        e = ents[k - 1]
        labs = {lab: u for h, lab, u in J.fields(S, k) if lab in ('ZMatPosAnim[0]', 'ZHavokShatter[10]')}
        if 'ZMatPosAnim[0]' in labs:
            mp[id(e)] = e
        if 'ZMatPosAnim[0]' in labs and id(e) in moved:
            x, _, z = struct.unpack_from('<3f', e.trans)
            if max(abs(x), abs(z)) >= 1000:                      # world-like local value (escape vans, doors, ...)
                info['matpos_entities'] += 1
                hit = start_in_head(e, 1.0)
                if hit:                                          # (x, y, z) of the entity's own local translation inside the head
                    info['matpos_start_in_head'] += 1
                    info['matpos_found'].append((e.name.decode('latin1'), min(hit)))
                else:
                    info['matpos_missing'].append(e.name.decode('latin1'))     # tracks elsewhere (.ANM?), or relative: not established
            elif max(abs(x), abs(z)) >= 50 and e.parent is not None and id(e.parent) in mp and max(abs(v) for v in struct.unpack_from('<2f', e.parent.trans)) >= 1000:
                info['child_entities'] += 1                      # a van's wheel / hatchback: its parent has a world-like position, its own value is small
                info['child_start_in_head'] += bool(start_in_head(e, 0.5))
        if 'ZHavokShatter[10]' in labs:
            w, p = [0.0, 0.0], e
            while p is not None:
                v = struct.unpack_from('<3f', p.trans)
                w[0] += v[0]; w[1] += v[2]
                p = p.parent
            pos.setdefault(struct.unpack('<I', labs['ZHavokShatter[10]'][0][1])[0], []).append(w)
    for off, ws in pos.items():
        info['shatter'][off] = (len(ws), round(max(w[0] for w in ws) - min(w[0] for w in ws)), round(max(w[1] for w in ws) - min(w[1] for w in ws)))
    return info


# ------------------------------------------------------------------ .HVK / .hrd
def shift_hvk(data, hrd, ents, moved, T, log):
    byref = {}
    for e in ents:
        byref.setdefault(e.ref, []).append(e)
    t = [T[0] / 100.0, T[1] / 100.0, T[2] / 100.0]          # placements are in metres

    def moves(inst):
        es = byref.get(kl_hvk.ref(inst), [])
        m = {id(e) in moved for e in es}
        if len(m) == 2:
            raise ValueError('REF %d belongs to a moved and a systems entity' % kl_hvk.ref(inst))
        return m == {True}

    h = kl_hvk.Hvk(data)
    info = {'placements_moved': 0, 'placements_kept': 0, 'codes_moved': 0, 'lists_moved': 0}

    def mv_inst(i):
        b = bytearray(i)
        add3(b, 0, t)
        return bytes(b)

    def mv_off(off):
        b = bytearray(off)
        add3(b, 0, t)                                          # x y z; the 4th float is the scale
        return bytes(b)

    rigid_moved = []
    static_moved = []
    for s in h.shapes:
        new, flags = [], []
        for i in s.inst:
            mv = moves(i)
            flags.append(mv)
            new.append(mv_inst(i) if mv else i)
            info['placements_moved' if mv else 'placements_kept'] += 1
        if s.type == kl_hvk.STATIC:
            s.mopp = [(mv_off(o) if mv else o, c) for (o, c), mv in zip(s.mopp, flags)]
            info['codes_moved'] += sum(flags)
            static_moved += flags
        if s.type == kl_hvk.RIGID:
            rigid_moved += flags
        s.inst = new
    # ASSUMPTION (holds on DM11B, verified there): one list code per 510 static placements in shape order; a chunk must not mix moved and kept
    if len(h.lists) != -(-len(static_moved) // kl_hvk.CHUNK):
        raise ValueError('%d list codes for %d static placements: the 510-chunk rule does not hold' % (len(h.lists), len(static_moved)))
    for c in range(len(h.lists)):                              # one list code per 510 static placements
        ch = static_moved[c * kl_hvk.CHUNK:(c + 1) * kl_hvk.CHUNK]
        if len(set(ch)) > 1:
            raise ValueError('static chunk %d mixes moved and systems placements' % c)
        if ch and ch[0]:
            h.lists[c] = (mv_off(h.lists[c][0]), h.lists[c][1])
            info['lists_moved'] += 1
    lo, hi = h.box[:3], h.box[3:]
    # header box: GUESS it is the Havok world bound in metres (min xyz, max xyz); grown to hold the old and the moved map
    h.box = tuple(f32(min(lo[a], lo[a] + t[a])) for a in range(3)) + tuple(f32(max(hi[a], hi[a] + t[a])) for a in range(3))
    out = h.serialize()
    # .hrd: 28-byte records in rigid-instance order, position first (metres)
    new_hrd = None
    if hrd is not None:
        if len(hrd) != 28 * len(rigid_moved):
            raise ValueError('.hrd has %d bytes for %d rigid instances' % (len(hrd), len(rigid_moved)))
        b = bytearray(hrd)
        for k, mv in enumerate(rigid_moved):
            if mv:
                add3(b, 28 * k, t)
        new_hrd = bytes(b)
        info['hrd_moved'] = sum(rigid_moved)
    return out, new_hrd, info


# ------------------------------------------------------------------ .oct .rmi .rmc
def _requant(tree, origin, it):
    lo, hi = tree.world(it[1:4]), tree.world([v + 1 for v in it[4:7]])
    sc = tree.scale
    a = [O.math.floor((lo[k] - origin[k]) * sc + 32768.0 + 1e-6) for k in range(3)]
    b = [O.math.ceil((hi[k] - origin[k]) * sc + 32768.0 - 1e-6) - 1 for k in range(3)]
    return [it[0]] + [min(max(v, 0), 0xffff) for v in a + b]


def shift_tree(tree, T, stay_ids, info):
    """Origin += T. Items whose id is in stay_ids (systems entities, not moved) are re-quantised into the new frame."""
    o2 = tuple(f32(tree.origin[a] + T[a]) for a in range(3))
    if not any(it[0] in stay_ids for it in tree.items):
        return O.Tree(o2, tree.scale, tree.nodes, tree.items, tree.fill)
    items = [_requant(tree, o2, it) if it[0] in stay_ids else list(it) for it in tree.items]
    t2 = O.Tree(o2, tree.scale, [list(n) for n in tree.nodes], items, tree.fill)
    info['trees_with_systems'] += 1
    try:
        t2.check()
    except ValueError:
        t2 = O.build_tree([list(i) for i in items], o2, tree.scale, quantised=True)
        t2.check()
        info['trees_rebuilt'] += 1
    return t2


def shift_oct(data, stay_slots, T):
    info = {'trees': 0, 'trees_with_systems': 0, 'trees_rebuilt': 0}
    o = O.Oct.parse(data)
    for room in o.rooms:
        for i, t in enumerate(room):
            if t is not None:
                room[i] = shift_tree(t, T, stay_slots, info)
                info['trees'] += 1
    old_refs = O.Oct.parse(data).record_refs()
    packed = o.pack()
    return packed, info, old_refs, O.Oct.parse(packed).record_refs()


def repoint_prm(prm, old_refs, new_refs):
    """The .prm type-7 chunks (64 bytes, 00 01 07 00) hold their ZOctreeCompiled record's .oct offset, (offset+4)|1, at +0x1c. Rebuilding room
    trees changes the .oct size, so every record moves and these must follow (A1SHIFT2 crashed at kl2+0x1c6901 reading a vtable out of tree node
    data, 2026-10-28). -> (prm, number repointed)."""
    move = {a: b for a, b in zip(old_refs, new_refs) if a != b}
    if not move:
        return prm, 0
    prm = bytearray(prm)
    old = set(old_refs)
    tt, nn = struct.unpack_from('<II', prm, 0)
    n = 0
    for i in range(1, nn):
        off, size = struct.unpack_from('<II', prm, tt + 16 * i)
        if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
            v = struct.unpack_from('<I', prm, off + 0x1c)[0]
            if v in move:
                struct.pack_into('<I', prm, off + 0x1c, move[v])
                n += 1
            elif v and v not in old:
                raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
    return bytes(prm), n


def shift_room_index(data, T):
    ri = O.RoomIndex.parse(data)
    ri.tree = O.Tree(tuple(f32(ri.tree.origin[a] + T[a]) for a in range(3)), ri.tree.scale, ri.tree.nodes, ri.tree.items, ri.tree.fill)
    for b in ri.boxes:
        p2 = struct.unpack_from('<3f', b.raw, 0x34)
        add3(b.raw, 0x28, T)
        if any(p2):                                   # GUESS: the second point is a position when set (.rmi: equals the centre), 0 in the .rmc
            add3(b.raw, 0x34, T)
    return ri.pack()


# ------------------------------------------------------------------ zip writer
def _copy_raw(out, src, info):
    """Copy a member compressed, byte for byte (no recompression)."""
    zi = zipfile.ZipInfo(info.filename, info.date_time)
    zi.compress_type, zi.CRC = info.compress_type, info.CRC
    zi.compress_size, zi.file_size = info.compress_size, info.file_size
    zi.external_attr, zi.create_system, zi.flag_bits = info.external_attr, info.create_system, 0
    zi.extra = b''
    f = src.fp
    f.seek(info.header_offset)
    hdr = f.read(30)
    n, m = struct.unpack_from('<HH', hdr, 26)
    f.seek(info.header_offset + 30 + n + m)
    zi.header_offset = out.fp.tell()
    out.fp.write(zi.FromHeader() if hasattr(zi, 'FromHeader') else zi.FileHeader())
    left = info.compress_size
    while left:
        b = f.read(min(left, 1 << 22))
        if not b:
            raise ValueError('short read in %s' % info.filename)
        out.fp.write(b)
        left -= len(b)
    out.filelist.append(zi)
    out.NameToInfo[zi.filename] = zi
    out._didModify = True
    out.start_dir = out.fp.tell()


def write_zip(src_path, dst_path, new):
    """new: {member name: bytes}. Members keep the source order; the others are copied compressed."""
    with zipfile.ZipFile(src_path) as src, zipfile.ZipFile(dst_path, 'w') as out:
        for info in src.infolist():
            if info.filename in new:
                out.writestr(zipfile.ZipInfo(info.filename, info.date_time), new[info.filename], zipfile.ZIP_DEFLATED, 6)
            else:
                _copy_raw(out, src, info)


# ------------------------------------------------------------------ source guard
DM11B_PRP_SIZE = 4021760        # the .prp of the real DM11B build (KLExpansion\Maps\DM11B\F04_Main.zip); stock Dog Days F04 has 3,711,080


class WrongSource(ValueError):
    pass


def check_sound(zf, stem, whd=None):
    """2026-10-28 (A1SHIFT3: both seats died, divide by zero at kl2+0x4668b). The first clip played read a junk .WHD record because the shift
    had been run on the STOCK Dog Days F04 zip (copied from the F04 slot; the DM11B redirect only happens at run time) and installed beside
    DM11B's .WHD. Every .SND wave must point at a record of the .WHD that goes with the map. whd = path or bytes; default: the sidecar
    <src dir>/<stem>.WHD (zf.filename). Raises WrongSource. -> (waves, misses)."""
    import kl_snd
    import kl_whd
    snd = next((n for n in zf.namelist() if n.lower() == (stem + '.snd').lower()), None)
    if snd is None:
        return 0, 0
    if whd is None:
        base = os.path.splitext(zf.filename)[0]
        for cand in (base + '.WHD', os.path.join(os.path.dirname(zf.filename), stem + '.WHD')):
            if os.path.isfile(cand):
                whd = cand
                break
        else:
            raise WrongSource('no %s.WHD beside %s: cannot prove the .SND matches this map (pass whd=, or whd=False to skip)' % (stem, zf.filename))
    if isinstance(whd, str):
        with open(whd, 'rb') as f:
            whd = f.read()
    recs = kl_whd.records('dd', whd)
    waves = [r for _o, _i, r in kl_snd.Snd('dd', zf.read(snd)).walk().waves()]
    miss = sum(1 for r in waves if r not in recs)
    if miss:
        raise WrongSource('%s: %d of %d .SND waves reference no record of the .WHD: wrong source zip for this .WHD (stock Dog Days F04 instead of the '
                          'DM11B build?)' % (zf.filename, miss, len(waves)))
    return len(waves), miss


# ------------------------------------------------------------------ main
def shift(src_zip, dst_zip, T=DEFAULT_T, log=print, whd=None, expect_prp_size=None):
    """whd: the map's .WHD (path / bytes; default the sidecar beside src_zip; False = skip the .SND/.WHD guard).
    expect_prp_size: refuse a source whose .prp has another size (the CLI passes DM11B_PRP_SIZE)."""
    T = tuple(float(v) for v in T)
    with zipfile.ZipFile(src_zip) as zf:
        stem = stem_of(zf)
        if expect_prp_size is not None:
            n = next((i for i in zf.infolist() if i.filename.lower() == (stem + '.prp').lower()), None)
            if n is None or n.file_size != expect_prp_size:
                raise WrongSource('%s: .prp is %s bytes, expected %d (not the DM11B build)' % (src_zip, n and n.file_size, expect_prp_size))
        if whd is not False:
            log('sound guard: %d waves, %d misses' % check_sound(zf, stem, whd))
        names = {n.lower(): n for n in zf.namelist()}
        mem = lambda ext: names.get((stem + ext).lower())
        data = {e: zf.read(mem(e)) for e in ('.gms', '.buf', '.prp', '.HVK', '.oct', '.rmi', '.rmc', '.sgp', '.sgd', '.hrd') if mem(e)}
    sc = kl_scene.Scene(kl_gms.unpack(data['.gms']), data['.buf'])
    ents = list(sc.entities())
    slots = sc.slots()
    prp, moved, top, rep = shift_scene(sc, data['.prp'], T, log)
    log('scene: %(moved_roots)d of %(roots)d roots move (%(zero_trans)d with zero translation), %(moved_entities)d of %(entities)d entities, '
        '%(gates)d room gates, prp/gms place mismatches %(prp_gms_place_mismatch)d' % rep)
    log('head not moved: %s' % rep['head_audit'])
    gms_u, buf = sc.write()
    new = {mem('.gms'): kl_gms.pack(gms_u), mem('.buf'): buf, mem('.prp'): prp}
    if '.HVK' in data:
        hvk, hrd, hi = shift_hvk(data['.HVK'], data.get('.hrd'), ents, moved, T, log)
        new[mem('.HVK')] = hvk
        if hrd is not None:
            new[mem('.hrd')] = hrd
        rep['hvk'] = hi
        log('hvk: %s' % hi)
    stay = {slots[e] for e in ents if id(e) not in moved}
    if '.oct' in data:
        new[mem('.oct')], oi, old_refs, new_refs = shift_oct(data['.oct'], stay, T)
        if old_refs != new_refs and mem('.prm'):
            with zipfile.ZipFile(src_zip) as zf:
                prm, oi['prm_chunks_repointed'] = repoint_prm(zf.read(mem('.prm')), old_refs, new_refs)
            if oi['prm_chunks_repointed']:
                new[mem('.prm')] = prm
        rep['oct'] = oi
        log('oct: %s' % oi)
    for ext in ('.rmi', '.rmc'):
        if ext in data:
            new[mem(ext)] = shift_room_index(data[ext], T)
    if '.sgp' in data:
        new[mem('.sgp')] = kl_members.Sgp(data['.sgp']).translate(T).serialize()
    if '.sgd' in data:
        new[mem('.sgd')] = kl_members.sgd_translate(data['.sgd'], T)
    write_zip(src_zip, dst_zip, new)
    rep['changed'] = sorted(new)
    log('wrote %s (%d members changed)' % (dst_zip, len(new)))
    return rep


def bots_companion(shifted_zip, dst=None, slot='F04', log=print):
    """The [BotGate] companion (<name>.bots.zip) of a SHIFTED map zip. 2026-10-28.
    The companion is the plain zip with ONE change, the .prp: every eHeistOnly ZSquadScript becomes eAllTypes (kl_botsonline.convert; every other
    member byte for byte). The bots' places (squad members, spawn points, waypoints, the PF4 navmesh they walk) are ordinary entities / nav data of
    the level, so shift() has already moved them with everything else; no separate coordinate pass exists or is needed. Hence the companion MUST be built
    from the shifted zip (the DM11B one built from the unshifted level puts the bots 12288 / 16384 units away from the shifted map).
    Writes <dst> (default <shifted stem>.bots.zip) and <dst stem>.base.md5 = md5 of the shifted zip, the file the hook's drift check compares
    with the plain zip it sits beside (kl_botgate_stage_1026.drift). -> (dst, base md5)."""
    import hashlib
    import kl_botsonline
    dst = dst or shifted_zip[:-4] + '.bots.zip'
    kl_botsonline.convert(shifted_zip, dst, 'eAllTypes', slot, log)
    h = hashlib.md5()
    with open(shifted_zip, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    with open(dst[:-4] + '.base.md5', 'w', newline='\n') as fh:
        fh.write(h.hexdigest() + '\n')
    return dst, h.hexdigest()


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == '--bots':
        # kl_map_shift.py --bots <shifted.zip> [<out.bots.zip>] [slot]
        print(bots_companion(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None, sys.argv[4] if len(sys.argv) > 4 else 'F04'))
        sys.exit(0)
    if len(sys.argv) < 3:
        sys.exit('usage: kl_map_shift.py <src.zip> <dst.zip> [tx ty tz]  |  kl_map_shift.py --bots <shifted.zip> [<out.bots.zip>] [slot]')
    shift(sys.argv[1], sys.argv[2], tuple(float(v) for v in sys.argv[3:6]) if len(sys.argv) >= 6 else DEFAULT_T, expect_prp_size=DM11B_PRP_SIZE)
