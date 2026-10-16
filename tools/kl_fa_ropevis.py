#!/usr/bin/env python3
"""
kl_fa_ropevis.py - A VISIBLE ROPE for Retomoto's rappel (agent rope, 2026-10-16). A step on a FINISHED DM09 build folder; writes a NEW folder.

    python kl_fa_ropevis.py build <DM09 build folder> <new folder> [--top X Y Z] [--bottom X Y Z] [--donor ROPE01_Final] [--thick N] [--room N|none]
      --room N: list the rope in tree 0 of room N (room order of kl_octree; 14 = DM09's outside room at the balcony) as a
               static object (pool group 0, flags 0x201f2: NOT DRAWN in run T29); default none = L07's own form (pool group 2, in no
               tree): DRAWN (run T30, a debug bar across the balcony)
      --thick N: the cross-section N times as wide (default 2.5; 8 = a 20 cm debug bar)

WHAT IT DOES
  Dog Days L07 hangs its soldiers' ropes as plain ZSTDOBJ models in the animation package
  Animation/L07/Situations/L07_Construction_Midship_Repelling.zip (ROPE, ROPE01, ROPE02 with a VertAnim controller; ROPE*_Final
  without one, 16.4 .. 16.9 m, a 437-vertex tube). This step copies ONE of them (default ROPE01_Final) into the build:
  - .prm: the model's closure (8 chunks) appended by kl_prmgraph.append; materials / textures by kl_texmat.merge_mat / merge_tex.
    The copy's VERTICES are rewritten: the tube is straightened along its own axis (L07's top -> bottom vertex) and laid on
    the segment TOP -> BOTTOM given here (default: Dead Men's roof rappel point over the balcony, 25483 -> the balcony floor
    21011, i.e. 44.7 m, Dead Men's M09_A rope); the cross-section is kept, the length stretched. The model root's box
    (+0x20) is the new box; its .oct record reference (+0x1c) is 0 (the rope has no collision).
  - one top group KL_RopeVis! (the build's plain group form, listed in the root's group tree as kl_fa_rappel does) with the
    ZSTDOBJ 'KL_RappelRope' under it: the donor's properties, place = TOP, rotation identity, pool group 2 and the flags of
    the VISIBLE L07 ropes (0x264182: the _Final ones carry 0x400 more, they are switched on by ActivateGeom after the drop);
    pool-group-2 ZSTDOBJ are in no room tree in L07 (1079 of 1079), so neither is this one. Its light list = the list of the
    nearest build ZSTDOBJ that has one.
  Nothing else of the build changes (members: .prm .MAT .TEX .gms .buf .prp .oct .rmi .rmc; .fxc kept, shader needs reported).
"""
import collections, json, math, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G, kl_texmat as T, kl_gms, kl_scene
import kl_prpjoin as J

GROUP, NAME = 'KL_RopeVis!', 'KL_RappelRope'
PKG = 'ROOT\\Animation/L07/Situations/L07_Construction_Midship_Repelling.zip\\L07_Construction_Midship_Repelling\\'
TOP = (5975.0, 25483.0, -70.0)       # x between the cut's start 5940 and its landing 6100, Dead Men's RappelBox height
BOTTOM = (5975.0, 21013.0, -70.0)    # on the balcony floor (21011)
VIS_FLAGS = 0x264182
ROOM_DM09_OUTSIDE = 14                         # DM09's 'M09_A_Out_CityScapeFront' room: its tree 0 lists the balcony's own objects outside the facade
ROOM = None                          # default: L07's own form (T30: DRAWN)
ROOM_FLAGS = 0x201f2                 # the flags of those objects (pool group 0, a light list)
VERTEX = 40
THICK = 2.5                          # L07's tube is ~2 cm: 2.5 x reads as a rope at 640 x 480 from the third-person camera


def _archive(folder):
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def _norm(v):
    l = math.sqrt(sum(x * x for x in v))
    return tuple(x / l for x in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def relay(p, root, top, bottom, thick=1.0):
    """In place on Prm p: every mesh of root's closure straightened and laid from local (0,0,0) to bottom - top. -> report."""
    kinds, _a = G.walk(p, [root])
    meshes = [i for i, k in kinds.items() if k == 'mesh']
    pts_all = []
    for m in meshes:
        sub = p.u32(m, 0x28); d = p.u32(sub, 0); nv, vtx = p.u32(d, 0), p.u32(d, 4)
        v = p.chunks[vtx]
        pts_all += [struct.unpack_from('<3f', v, VERTEX * j) for j in range(nv)]
    t0 = max(pts_all, key=lambda q: q[1]); b0 = min(pts_all, key=lambda q: q[1])
    u = _norm(tuple(b0[i] - t0[i] for i in range(3))); L0 = math.sqrt(sum((b0[i] - t0[i]) ** 2 for i in range(3)))
    a = _norm(_cross(u, (0.0, 0.0, 1.0))); b = _cross(u, a)
    D = tuple(bottom[i] - top[i] for i in range(3)); L1 = math.sqrt(sum(x * x for x in D)); w = _norm(D)
    a1 = _norm(_cross(w, (0.0, 0.0, 1.0))) if abs(w[2]) < 0.99 else (1.0, 0.0, 0.0); b1 = _cross(w, a1)
    # the tube's centre line: the mean of the vertices in 8-unit slices along the axis (the L07 rope bends up to ~50 off the
    # straight top -> bottom line; that bend is removed, only the cross-section is kept)
    bins = collections.defaultdict(list)
    for q in pts_all:
        r = tuple(q[i] - t0[i] for i in range(3))
        bins[int(round(sum(r[i] * u[i] for i in range(3)) / 8.0))].append(q)
    centre = {k: tuple(sum(q[i] for q in v) / len(v) for i in range(3)) for k, v in bins.items()}
    lo, hi, rmax = [1e30] * 3, [-1e30] * 3, 0.0
    for m in meshes:
        sub = p.u32(m, 0x28); d = p.u32(sub, 0); nv, vtx = p.u32(d, 0), p.u32(d, 4)
        v = bytearray(p.chunks[vtx])
        for j in range(nv):
            q = struct.unpack_from('<3f', v, VERTEX * j)
            r = tuple(q[i] - t0[i] for i in range(3))
            t = sum(r[i] * u[i] for i in range(3))
            c = centre[int(round(t / 8.0))]
            r = tuple(q[i] - c[i] for i in range(3))
            ra, rb = sum(r[i] * a[i] for i in range(3)), sum(r[i] * b[i] for i in range(3))
            rmax = max(rmax, math.hypot(ra, rb))
            s = t / L0 * L1
            n = tuple(w[i] * s + a1[i] * ra * thick + b1[i] * rb * thick for i in range(3))
            struct.pack_into('<3f', v, VERTEX * j, *n)
            for i in range(3):
                lo[i] = min(lo[i], n[i]); hi[i] = max(hi[i], n[i])
        p.chunks[vtx] = bytes(v)
    rc = bytearray(p.chunks[root])
    struct.pack_into('<6f', rc, 0x20, *(lo + hi))
    struct.pack_into('<I', rc, 0x1c, 0)
    p.chunks[root] = bytes(rc)
    return dict(meshes=meshes, vertices=len(pts_all), length_before=round(L0, 1), length_after=round(L1, 1), radius=round(rmax, 1),
                box=[round(x, 1) for x in lo + hi])


def build(src, dst, top=TOP, bottom=BOTTOM, donor='ROPE01_Final', thick=THICK, room=ROOM, log=print):
    import kl_fa_bots as F, kl_fa_cover as CV, kl_fa_climb2 as C2, kl_graft, kl_light
    import kl_octree as O
    zp = _archive(src)
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty' % dst)
    B = F.Built(zp)
    sc = B.sc
    if sc.resolve(F.R_ + GROUP):
        raise ValueError('the build already has %s' % GROUP)
    lines = []

    def say(s=''):
        log(s); lines.append(s)
    say('kl_fa_ropevis build: %s -> %s' % (zp, dst))
    # ---- the donor
    M = F.Maker()
    rope = M.clone('L07', PKG + donor, NAME)
    sc7, ents7 = M.level('L07')
    k7 = sc7.resolve(PKG + donor)[0]
    e7 = ents7[k7 - 1]
    with zipfile.ZipFile(J.level_zip('L07', 'dd')) as z:
        m7 = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        p7, mat7, tex7 = G.read(z.read(m7['.prm']), 'dd'), T.read_mat(z.read(m7['.MAT'])), T.read_tex(z.read(m7['.TEX']))
    root7 = e7.model
    rep = relay(p7, root7, top, bottom, thick)
    say('  donor L07 %s: model root %d, %s' % (donor, root7, rep))
    # ---- .prm / .MAT / .TEX
    pD, matD, texD = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    kinds, args = G.walk(p7, [root7])
    slots = {p7.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(mat7, slots))
    tex, tmap = T.merge_tex(texD, tex7, want)
    mat, mmap = T.merge_mat(matD, mat7, slots, tmap)
    prm, cmap = G.append(pD, p7, [root7], mmap, None, tmap)
    newroot = cmap[root7]
    say('  .prm: %d chunks appended (root %d -> %d); materials %s -> %s; textures %s -> %s' % (
        len(kinds), root7, newroot, sorted(slots), [mmap[s] for s in sorted(slots)], sorted(want), [tmap[t] for t in sorted(want)]))
    lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
    say('  shaders the rope material needs that the build\'s .fxc lacks: %s' % (lack or 'none'))
    # ---- the nodes
    gk = CV.group_form(B)
    topg = CV._node(M, B, gk, GROUP)
    M.place(topg, (0.0, 0.0, 0.0))
    topg.add(rope)
    M.place(rope, top, F.rot9(0.0, 1.0))
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    slotx = B.scene.slots()
    in_room = set(it[0] for it in octx.rooms[room][0].items) if room is not None and octx.rooms[room][0] is not None else set()
    # the .prp names the model too (ZGEOM[4] = the .prm chunk of the root; the clone still held L07's 15451 - found by T28)
    if room is None:
        rope.model, rope.flags, rope.group = newroot, VIS_FLAGS, 2
        M.set(rope, None, {'ZGEOM[4]': newroot})
    else:
        rope.model, rope.flags, rope.group = newroot, ROOM_FLAGS, 0
        M.set(rope, None, {'ZGEOM[4]': newroot, 'ZGEOM[0]': 'BOUNDING_Static', 'ZGEOM[3]': 0})
    best = None
    for e in B.ents:
        if e.tid == 0x200002 and e.links and (room is None or slotx[e] + 2 in in_room):
            P = B.fr[e][1]
            dd = (P[0] - top[0]) ** 2 + (P[2] - top[2]) ** 2 + (P[1] - (top[1] + bottom[1]) / 2) ** 2
            if best is None or dd < best[0]:
                best = (dd, e)
    rope.links = list(best[1].links) if best else []
    say('  light list: that of %s (%d entries, %.0f away)' % (best[1].name.decode('latin1') if best else '-', len(rope.links), math.sqrt(best[0]) if best else 0))
    q, order = M.scene([topg])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'ropevis')
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    pre = F.room_sets_check(A, octx, rmi, rmc)
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    nxt = C2._write_ent(A, topg, None, nxt, made)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    lo = tuple(min(top[i], bottom[i]) - 30.0 for i in range(3)); hi = tuple(max(top[i], bottom[i]) + 30.0 for i in range(3))
    root3 = octn.rooms[0][3]
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree([(slot1[made[id(topg)]] + 2, lo, hi)], root3.origin, root3.scale))
        octn.rooms[0][3].check()
    if room is not None:                                     # the rope itself in the room's tree 0 with its world box
        t0 = octn.rooms[room][0]
        rlo = tuple(min(top[i], bottom[i]) - 30.0 for i in range(3)); rhi = tuple(max(top[i], bottom[i]) + 30.0 for i in range(3))
        octn.rooms[room][0] = O.join_trees(t0, O.build_tree([(slot1[made[id(rope)]] + 2, rlo, rhi)], t0.origin, t0.scale))
        octn.rooms[room][0].check()
        say('  listed in tree 0 of room %d (%d -> %d items)' % (room, len(t0.items), len(octn.rooms[room][0].items)))
    move = {x: y for x, y in zip(octx.record_refs(), octn.record_refs()) if x != y}
    pm = bytearray(G.write(prm))
    repointed = 0
    if move:
        t, n = struct.unpack_from('<II', pm, 0)
        for i in range(1, n):
            o, size = struct.unpack_from('<II', pm, t + 16 * i)
            if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    prm_bytes = bytes(pm)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    # proofs on what is written
    p2 = G.read(prm_bytes, 'dd')
    if G.write(p2) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    lost = T.used_textures(T.read_mat(new[B.ext['.MAT']])) - set(T.read_tex(new[B.ext['.TEX']]).tex)
    if lost:
        raise ValueError('materials name textures the .TEX lacks: %s' % sorted(lost)[:5])
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(nm, new[nm]) for nm in B.order])
    for x in os.listdir(B.folder):
        pth = os.path.join(B.folder, x)
        if os.path.isfile(pth) and pth != zp:
            shutil.copyfile(pth, os.path.join(dst, x))
    say('written %s: %d entities added (REF %d..), members changed: %s; %d .prm roots re-pointed (.oct records moved); root group tree + %s' % (
        out, len(order), nxt - len(order), ' '.join(changed), repointed, GROUP))
    report = dict(source=zp, out=out, top=list(top), bottom=list(bottom), donor=donor, relay=rep, root=newroot, members_changed=changed,
                  shaders_missing={str(k): [str(x) for x in v] for k, v in lack.items()})
    json.dump(report, open(os.path.join(dst, 'ropevis.json'), 'w'), indent=1)
    open(os.path.join(dst, 'ropevis.txt'), 'w').write('\n'.join(lines) + '\n')
    return report


def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] != 'build':
        print(__doc__); return 2
    kw = {}
    for flag, key in (('--top', 'top'), ('--bottom', 'bottom')):
        if flag in a:
            i = a.index(flag); kw[key] = tuple(float(x) for x in a[i + 1:i + 4]); del a[i:i + 4]
    if '--thick' in a:
        i = a.index('--thick'); kw['thick'] = float(a[i + 1]); del a[i:i + 2]
    if '--room' in a:
        i = a.index('--room'); kw['room'] = None if a[i + 1] == 'none' else int(a[i + 1]); del a[i:i + 2]
    if '--donor' in a:
        i = a.index('--donor'); kw['donor'] = a[i + 1]; del a[i:i + 2]
    build(a[1], a[2], **kw)
    return 0


if __name__ == '__main__':
    sys.exit(main())
