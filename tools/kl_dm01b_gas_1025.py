#!/usr/bin/env python3
"""
kl_dm01b_gas_1025.py - DM01B Hot Coffee II: Dog Days F03 FUEL CANS (gas explosion) in the garage + 2 more wall extinguishers (agent, 2026-10-25).

    python kl_dm01b_gas_1025.py spots <in.zip>                      the chosen places (nothing written)
    python kl_dm01b_gas_1025.py build <in.zip> <out.zip> [--force]  one build (md5 pin of the live DM01B zip unless --force)
    python kl_dm01b_gas_1025.py stage <in.zip> <out folder> [--rehearse <scratch folder>]
                                    build + md5-chained INSTALL/UNDO (.bat + .ps1 + gas.json); the rehearsal runs on a scratch game
                                    folder under <scratch> only (install, idempotent, undo byte-identical, wrong md5 refused)

WHAT THE PLAYER GETS (map DM01B = Dog Days slot F03, KLExpansion\\Maps\\DM01B\\F03_Main.zip)
  3 fuel cans (Dog Days F03 FX0900_ALL_FuelCan_D_01: a small jerry can, Havok rigid body, throwable, with the stock
  Explosion_Gas_S group: fire / smoke / dust emitters, flash + fireball meshes, omni light, CheapCamFx + DocuCamControl (camera shake),
  Sound_bam) on the floor of the garage hall, each at the foot of a police cover line where the Dead Men police stand in the fight,
  on the side the heisters come from. The garage hall is the first fight of the round (heisters spawn at the south end).
  2 fire extinguishers (clones of the live KL_Ext_n, the F04 template, re-appended like kl_interact_graft does) on the east wall of
  the hall: one at the spawn end, one half way along the fight.
Everything is a NEW top group KL_Gas!1 (own fresh REF labels); the installed KL_Interact! / KL_CoverMore! groups, the kick doors,
the cover passes and the garage-door pass are not touched. Idempotent: an input that holds KL_Gas!1 is written out unchanged.
This module imports kl_interact_graft (Donor, make_extinguisher, helpers) without editing it; IG.TOP_PATH is set for the run.
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_interact_graft as IG
import kl_prmgraph as G, kl_texmat as T, kl_hvk
import kl_prpjoin as J
import kl_octree as O

TOP = 'KL_Gas!1'
SRC_MD5 = 'f0aaba9272736ebf2dd6bb9582e47990'          # the live DM01B zip this was built and checked on (2026-10-25)
TAG = '.before-1025dm01bgas'
MAP, FILE = 'DM01B', 'F03_Main.zip'

FUEL_DONOR = 'F03'
FUEL_PARENT = 'ROOT\\Locations/F03/F03_Locations.zip\\Locations/F03/F03_LOC_Outside.zip\\F03_Garage'
FUEL_CAN = 1442                                         # F03 .prp node numbers: the can (ZHavokRigidBody), its explosion group 1279 with kids 1280..1296
FUEL_KEEP = list(range(1279, 1297)) + [1440, 1441, 1442]

# Places, floor level x z (cm, the map's world). Fuel cans: an anchor at the foot of a police cover line, snapped to the nearest nav
# point that has 60 cm of walk mesh on every side (so the can lies on open floor, no wall or prop within reach).
#   1  east aisle: foot of the cover line CoverBoxH_07/_05 (x ~ -400, z 6045..6206) under the police defend place (-404,6657)
#   2  west lane : police assault place Pos#03 (-1766,5762) / ToolStorage_A_07 + CoverBoxH_04 (-1700,5650)
#   3  north door: the police entry (Pos# at z ~7475, x -450..-225), the way the heisters leave the hall to the north
FUEL_ANCHORS = [(-520.0, 6560.0), (-1650.0, 5850.0), (-330.0, 7230.0)]
# Extinguishers: on the east wall of the hall (walk mesh wall edge x = -31 / -23, 45 cm off it), z along the wall.
EXT_WALL = [(-31.0, 6140.0), (-23.0, 4400.0)]
START_Z = (4150.0, 4690.0)                              # the heisters' start spawn points (z range); fuel cans stay >= FUEL_MIN_START away
FUEL_MIN_START = 900.0


def md5(b):
    return hashlib.md5(b).hexdigest()


# ------------------------------------------------------------------ places
def _margin_ok(nav, x, y, z, r=60.0):
    a = nav.at(x, y, z, dy=80.0)
    if not a:
        return False
    for k in range(8):
        t = k * math.pi / 4
        b = nav.at(x + r * math.cos(t), y, z + r * math.sin(t), dy=80.0)
        if not b or abs(nav.height(b[0], x + r * math.cos(t), z + r * math.sin(t)) - nav.height(a[0], x, z)) > 40.0:
            return False
    return True


def snap(nav, x, z, y=0.0, reach=300.0, step=20.0):
    """The nearest (x, floor y, z) with a 60 cm margin of walk mesh, within `reach` of (x, z)."""
    best = None
    n = int(reach // step)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            px, pz = x + i * step, z + j * step
            d = math.hypot(px - x, pz - z)
            if d > reach or (best and d >= best[0]):
                continue
            if _margin_ok(nav, px, y, pz):
                a = nav.at(px, y, pz, dy=80.0)
                best = (d, px, nav.height(a[0], px, pz), pz)
    if not best:
        raise ValueError('no walk mesh with a margin near (%s, %s)' % (x, z))
    return (best[1], best[2], best[3])


def fuel_spots(B, nav):
    import kl_fa_bots as F
    starts = [B.at(k) for k in range(1, len(B.sc.nodes)) if B.sc.cls(k) == 'ZSpawnPoint' and 'Start' in B.sc.names[k]]
    out = []
    for anc in FUEL_ANCHORS:
        ax, az = anc[0], anc[1]
        s = snap(nav, ax, az, y=anc[2] if len(anc) > 2 else 0.0)      # optional 3rd value = floor level (DM02 has three floors)
        near = min(math.hypot(s[0] - p[0], s[2] - p[2]) for p in starts)
        if near < FUEL_MIN_START:
            raise ValueError('fuel can at %s is only %.0f cm from a start spawn' % (s, near))
        out.append(s)
    return out


def ext_spots_wall(B, nav):
    out = []
    for wx, wz in EXT_WALL:
        x = wx - 45.0                                    # the wall edge is the east end of the walk mesh: the can stands 45 cm west of it
        a = nav.at(x, 0.0, wz, dy=80.0)
        if not a or not nav.inside(a[0], x, wz):
            raise ValueError('extinguisher place (%s, %s) is not on the walk mesh' % (x, wz))
        out.append((x, nav.height(a[0], x, wz), wz, 0.0))
    return out


# ------------------------------------------------------------------ the fuel can (copy of kl_interact_graft.make_extinguisher, F03 nodes)
def make_fuelcan(M, B, don, n, at, tmpl_ok):
    import kl_fa_cover as CV
    gk = CV.group_form(B)
    grp = CV._node(M, B, gk, 'KL_Fuel_%d' % n)
    M.place(grp, (0.0, 0.0, 0.0))
    newp = IG.TOP_PATH + '\\' + grp.name + '\\'
    old = FUEL_PARENT + '\\'
    rn = lambda s: (newp + s[len(old):]) if s.lower().startswith(old.lower()) else s
    can0 = struct.unpack_from('<3f', don.ent(FUEL_CAN).trans)
    d = tuple(at[i] - can0[i] for i in range(3))
    byk = {}
    for k in FUEL_KEEP:
        nd = IG.clone(M, don, k, don.sc.names[k], rn)
        byk[k] = nd
        par = don.sc.parent[k]
        (byk[par] if par in byk else grp).add(nd)
        if par not in byk:                                # a top-level node of the template: its place is a world place
            IG.shift(M, nd, d)
    gone = []
    for k in list(byk):
        nd = byk[k]
        if nd.tid == 0x2000ff:
            nm = IG._emitter_template(M, nd)
            if nm and nm.lower() not in tmpl_ok:
                gone.append(nd)
    for nd in gone:
        for k, v in list(byk.items()):
            if v is nd:
                del byk[k]
        for v in grp.walk():
            if nd in v.kids:
                v.kids.remove(nd)
    return grp, byk[FUEL_CAN], byk, [g.name for g in gone]


# ------------------------------------------------------------------ build
def build(src_zip, dst_zip, pin=SRC_MD5, log=print):
    import kl_fa_bots as F, kl_fa_cover as CV, kl_fa_climb2 as C2, kl_graft, kl_light, kl_scene, kl_gms
    data = open(src_zip, 'rb').read()
    if pin and md5(data) != pin:
        raise ValueError('%s: md5 %s is not the pinned %s (use --force)' % (src_zip, md5(data), pin))
    B = F.Built(src_zip)
    sc = B.sc
    if sc.resolve(F.R_ + TOP):
        log('already grafted (%s present): written unchanged' % TOP)
        open(dst_zip, 'wb').write(data)
        return dict(unchanged=True)
    IG.TOP_PATH = 'ROOT\\' + TOP
    lines = []

    def say(s=''):
        log(s); lines.append(s)
    say('kl_dm01b_gas_1025: %s (%s) -> %s' % (src_zip, md5(data), dst_zip))
    nav = F.Nav(B.scene.nav)
    fspots = fuel_spots(B, nav)
    espots = ext_spots_wall(B, nav)
    say('  fuel cans at %s' % [tuple(round(v) for v in s) for s in fspots])
    say('  extinguishers at %s' % [tuple(round(v) for v in s[:3]) for s in espots])
    fdon, edon = IG.Donor.get(FUEL_DONOR), IG.Donor.get(IG.EXT_DONOR)
    tmpl_ok = {sc.names[k].lower() for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZParticleTemplate'}
    M = F.Maker()
    topg = CV._node(M, B, CV.group_form(B), TOP)
    M.place(topg, (0.0, 0.0, 0.0))
    fcan0, ecan0 = fdon.ent(FUEL_CAN), edon.ent(IG.EXT_CAN)
    fbox = struct.unpack_from('<6f', fdon.prm.chunks[fcan0.model], 0x20)
    ebox = struct.unpack_from('<6f', edon.prm.chunks[ecan0.model], 0x20)
    finsts, einsts = [], []
    for n, (x, y, z) in enumerate(fspots, 1):
        at = (x, y - fbox[1] + 1.0, z)                    # ASSUMPTION (as kl_interact_graft): the model's own y axis is up, box bottom on the floor
        grp, can, byk, gone = make_fuelcan(M, B, fdon, n, at, tmpl_ok)
        topg.add(grp)
        finsts.append(dict(group=grp, can=can, byk=byk, at=at))
        say('  KL_Fuel_%d at %s: %d nodes, emitters without template dropped: %s' % (n, tuple(round(v) for v in at), len(list(grp.walk())) - 1, gone))
    for n, (x, y, z, _L) in enumerate(espots, 11):
        at = (x, y - ebox[1] + 1.0, z)
        grp, can, byk, gone, cuts = IG.make_extinguisher(M, B, edon, n, at, tmpl_ok)
        topg.add(grp)
        einsts.append(dict(group=grp, can=can, byk=byk, at=at))
        say('  KL_Ext_%d at %s: %d nodes, %d list entries dropped, emitters without template dropped: %s' % (n, tuple(round(v) for v in at), len(list(grp.walk())) - 1, cuts, gone))
    # ---- models, one leg per donor level (as kl_interact_graft)
    pS, matS, texS = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    legs = []
    for dn, its in ((fdon, finsts), (edon, einsts)):
        if not its:                                       # no extinguishers asked (EXT_WALL = []): nothing of that donor is appended
            continue
        dprm = dn.prm
        roots = sorted({nd.model for it in its for nd in it['group'].walk() if nd.model and getattr(nd, 'donor', None)})
        kinds, args = G.walk(dprm, roots)
        slots = {dprm.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
        want = set(T.used_textures(dn.mat, slots))
        for i, k in kinds.items():
            for off, typ, _k in G.fields(dprm, i, k, args.get(i, 0)):
                if typ in 'tT' and dprm.u32(i, off):
                    want.add(dprm.u32(i, off) % G.SLOTS['dd'])
        tex, tmap = T.merge_tex(texS, dn.tex, want)
        mat, mmap = T.merge_mat(matS, dn.mat, slots, tmap)
        pS, cmap = G.append(pS, dprm, roots, mmap, None, tmap)
        lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
        say('  .prm: %d chunks of %s appended; materials %s; shaders missing in the map .fxc: %s' % (len(kinds), dn.level, sorted(mmap[s] for s in slots), lack or 'none'))
        if lack:
            raise ValueError('%s: shaders missing in the map .fxc: %s' % (dn.level, lack))
        legs.append(dict(don=dn, prm=dprm, roots=roots, kinds=kinds, mmap=mmap, tmap=tmap, cmap=cmap))
        texS, matS = tex, mat
        for it in its:
            for nd in it['group'].walk():
                if getattr(nd, 'donor', None) and nd.model:
                    nd.model = cmap[nd.model]
                    M.set(nd, None, {'ZGEOM[4]': nd.model})
    mat, tex = matS, texS
    # ---- light lists: a donor ZSTDOBJ with a list gets the nearest map object's
    lit = [e for e in B.ents if e.tid == 0x200002 and e.links]
    allit = finsts + einsts
    for it in allit:
        for nd in it['group'].walk():
            if nd.links and nd.tid == 0x200002 and getattr(nd, 'donor', None):      # a light node (IOLight01, links []) keeps its own empty list
                P = it['at']
                best = min(lit, key=lambda e: sum((B.fr[e][1][i] - P[i]) ** 2 for i in range(3)))
                nd.links = list(best.links)
    # ---- the scene
    q, order = M.scene([topg])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'gas')
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
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
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
    lo = tuple(min(it['at'][i] for it in allit) - 400.0 for i in range(3))
    hi = tuple(max(it['at'][i] for it in allit) + 400.0 for i in range(3))
    root3 = octn.rooms[0][3]
    if root3 is None:
        raise ValueError('the root room has no tree 3')
    octn.rooms[0][3] = O.join_trees(root3, O.build_tree([(slot1[made[id(topg)]] + 2, lo, hi)], root3.origin, root3.scale))
    octn.rooms[0][3].check()
    t0 = octn.rooms[0][0]
    if t0 is not None and einsts:
        # GUESS (cosmetic, as kl_interact_graft): the extinguisher explosion's two group-0 meshes are listed in tree 0 with a 3 m box.
        # The F03 donor lists NO fuel-can mesh in any tree 0 (only the group 1279 in room 19 tree 3), so none is added for them.
        items = []
        for it in einsts:
            for k in IG.EXT_TREE0:
                nd = it['byk'].get(k)
                if nd is not None:
                    items.append((slot1[made[id(nd)]] + 2, tuple(it['at'][i] - 300.0 for i in range(3)), tuple(it['at'][i] + 300.0 for i in range(3))))
        octn.rooms[0][0] = O.join_trees(t0, O.build_tree(items, t0.origin, t0.scale))
        octn.rooms[0][0].check()
        say('  %d extinguisher explosion meshes listed in tree 0 of the root room (%d -> %d items)' % (len(items), len(t0.items), len(octn.rooms[0][0].items)))
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    # ---- .oct records of the donor models, then the .prm for real, one leg per donor
    unref = lambda v: (v & ~1) - 4
    octj, held, pcur, moved = octn, octx.record_refs(), G.read(B['.prm'], 'dd'), 0
    for lg in legs:
        dn = lg['don']
        rec_d = {v: n for n, v in enumerate(dn.oct.record_refs())}
        keep = sorted({rec_d[lg['prm'].u32(i, 0x1c)] for i, k in lg['kinds'].items() if k == 'root' and lg['prm'].u32(i, 0x1c)})
        octk, _same, refs_b = O.append_records(octj, dn.oct, lg['cmap'], keep)
        refs_a = dict(zip(held, octk.record_refs()))
        pnew, cmap2 = G.append(pcur, lg['prm'], lg['roots'], lg['mmap'], {unref(a): unref(b) for a, b in refs_b.items()}, lg['tmap'])
        if cmap2 != lg['cmap']:
            raise ValueError('kl_prmgraph.append numbers chunks differently on the second run (%s)' % dn.level)
        for i in range(1, len(pcur.chunks)):
            c = pnew.chunks[i]
            if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
                v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
                if v != struct.unpack_from('<I', c, 0x1c)[0]:
                    pnew.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]; moved += 1
        held, octj, pcur = octk.record_refs(), octk, pnew
    prm = pcur
    prm_bytes = G.write(prm)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    # ---- Havok: one type-2 shape record per donor can (clone of the stock instance, new place + REF label), one .hrd record each, in
    # shape / instance order (the new shapes go behind every existing one; the .hrd gets its records in the same order)
    hvk = kl_hvk.Hvk(B['.HVK'])
    n_rigid = sum(len(s.inst) for s in hvk.shapes if s.type == kl_hvk.RIGID)
    has_hrd = '.hrd' in B.ext
    # 1025 park2: DM06B (M06_A graft) has 6 rigid instances and NO .hrd member (live-run map); kl_interact_graft.build leaves such a map without one
    # too, so a map without .hrd stays without (no member is invented).
    hrd_old = B.files[B.ext['.hrd']] if has_hrd else b''
    if has_hrd and len(hrd_old) != 28 * n_rigid:
        raise ValueError('.hrd has %d bytes, %d rigid instances need %d' % (len(hrd_old), n_rigid, 28 * n_rigid))
    hrd_new = []
    for dn, can_id, insts in ((fdon, FUEL_CAN, finsts), (edon, IG.EXT_CAN, einsts)):
        if not insts:
            continue
        dh = dn.hvk
        dc = dn.ent(can_id)
        dshape = next(s for s in dh.shapes if any(kl_hvk.ref(i) == dc.ref for i in s.inst))
        dinst = next(i for i in dshape.inst if kl_hvk.ref(i) == dc.ref)
        t2 = [i for s in dh.shapes if s.type == kl_hvk.RIGID for i in s.inst]
        drec = dn.files['.hrd'][28 * t2.index(dinst):28 * t2.index(dinst) + 28]
        news = []
        for it in insts:
            i = bytearray(dinst)
            struct.pack_into('<3f', i, 0, *(v / 100.0 for v in it['at']))
            struct.pack_into('<I', i, 0x30, made[id(it['can'])].ref)
            news.append(bytes(i))
            rec = bytearray(drec)
            struct.pack_into('<3f', rec, 0, *(v / 100.0 for v in it['at']))
            hrd_new.append(bytes(rec))
        hvk.shapes.append(dshape.clone(news, []))
    hvk_bytes = hvk.serialize()
    if kl_hvk.Hvk(hvk_bytes).serialize() != hvk_bytes:
        raise ValueError('.HVK does not round-trip')
    h2 = kl_hvk.Hvk(hvk_bytes)
    if has_hrd and 28 * sum(len(s.inst) for s in h2.shapes if s.type == kl_hvk.RIGID) != len(hrd_old) + 28 * len(hrd_new):
        raise ValueError('.hrd record count does not match the rigid instances')
    hrd = hrd_old + b''.join(hrd_new)
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octj.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    new[B.ext['.HVK']] = hvk_bytes
    if has_hrd:
        new[B.ext['.hrd']] = hrd
    p2 = G.read(prm_bytes, 'dd')
    if G.write(p2) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    out = kl_graft.write_zip(dst_zip, [(nm, new[nm]) for nm in B.order])
    say('written %s md5 %s; members changed: %s; %d map .prm roots re-pointed' % (out, md5(open(out, 'rb').read()), ' '.join(changed), moved))
    return dict(out=out, changed=changed, fuel=fspots, ext=[s[:3] for s in espots], lines=lines)


# ------------------------------------------------------------------ INSTALL / UNDO
PS1 = r'''# gas.ps1 - DM01B Hot Coffee II: 3 fuel cans (gas explosion) in the garage + 2 wall extinguishers (tools/kl_dm01b_gas_1025.py, 2026-10-25).
#   powershell -ExecutionPolicy Bypass -File gas.ps1 [-Undo] [-DryRun] [-Game <folder>]   (-Rehearsal: scratch folders only, skips the kl2 check)
# WHAT: the WHOLE KLExpansion\Maps\DM01B\F03_Main.zip is replaced by the build file next to this script (entities were added, so .prp .gms
#   .buf .oct .rmi .rmc .prm .MAT .TEX .HVK .hrd change). The live zip is renamed F03_Main.zip.before-1025dm01bgas (never overwritten).
# SAFETY: refuses while kl2.exe runs; the live zip md5 must be exactly the one in gas.json "old" (or already the new one); read-back md5
#   after the copy; on failure the original is put back; UNDO only when live == the new build, and renames the backup back (byte identical).
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025dm01bgas'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'gas.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
$real = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
if ($Rehearsal -and $Game.TrimEnd('') -ieq $real) { '-Rehearsal is only for a scratch copy, not the real game folder.'; exit 1 }
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$dst = Join-Path $Game ('KLExpansion\Maps\' + $man.m + '\' + $man.f)
$bak = "$dst$tag"; $tmp = "$dst.tmp1025"
$src = Join-Path $PSScriptRoot $man.f
"target: $dst"
if (-not (Test-Path -LiteralPath $dst)) { "SKIP, $dst not installed"; exit 4 }
$cur = md5 $dst
if ($Undo) {
  if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $man.old) { 'already undone'; exit 0 } else { "SKIP, no backup and live is $cur"; exit 4 } }
  if ($cur -ne $man.new) { "SKIP, live is $cur, not this build (changed since?). Backup left in place."; exit 4 }
  if ((md5 $bak) -ne $man.old) { 'SKIP, backup is not the expected original'; exit 4 }
  if ($DryRun) { 'would restore the original (dry run)'; exit 0 }
  Remove-Item -LiteralPath $dst -Force
  Rename-Item -LiteralPath $bak -NewName $man.f
  if ((md5 $dst) -ne $man.old) { 'FAILED, restored file does not read back right!'; exit 4 }
  'original restored, read back ok'; exit 0
}
if ($cur -eq $man.new) { 'already installed'; exit 0 }
if ($cur -ne $man.old) { "SKIP, live md5 is $cur, expected $($man.old). Another install in between? Not changed."; exit 4 }
if (Test-Path -LiteralPath $bak) { "SKIP, $bak already exists. Not changed."; exit 4 }
if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $man.new) { "SKIP, build file $src missing or changed"; exit 4 }
if ($DryRun) { 'would install (dry run)'; exit 0 }
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
Copy-Item -LiteralPath $src -Destination $tmp
if ((md5 $tmp) -ne $man.new) { 'FAILED copying, live untouched'; Remove-Item -LiteralPath $tmp -Force; exit 4 }
Rename-Item -LiteralPath $dst -NewName ($man.f + $tag)
$ok = $false
try { Rename-Item -LiteralPath $tmp -NewName $man.f; $ok = (Test-Path -LiteralPath $dst) } catch { $ok = $false }
if (-not $ok) {
  if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
  Rename-Item -LiteralPath $bak -NewName $man.f
  'FAILED swap, original put back'; exit 4
}
if ((md5 $dst) -ne $man.new) { 'FAILED read-back, run UNDO'; exit 4 }
"installed (md5 $((md5 $dst).Substring(0,8))), original kept as $($man.f)$tag"
'''
BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0gas.ps1" {arg}\r\npause\r\n'


def _ps(d, game, undo=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'gas.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(src, out, scratch=None, log=print):
    old = md5(open(src, 'rb').read())
    if old != SRC_MD5:
        raise SystemExit('input md5 %s is not the pinned %s' % (old, SRC_MD5))
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, FILE)
    rep = build(src, z)
    if rep.get('unchanged'):
        raise SystemExit('input already holds ' + TOP)
    new = md5(open(z, 'rb').read())
    man = dict(m=MAP, f=FILE, old=old, new=new, tag=TAG)
    with open(os.path.join(out, 'gas.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'gas.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL gas.bat', ''), ('UNDO gas.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %s -> %s' % (out, old, new))
    if scratch:
        rehearse(src, out, man, scratch, log)
    return 0


def rehearse(src, d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', MAP, FILE)
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    log('rehearsal target: ' + live)
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    fm = lambda p: md5(open(p, 'rb').read())
    t = _ps(d, g); log(t); assert 'installed' in t and fm(live) == man['new'], t
    assert os.path.isfile(live + TAG) and fm(live + TAG) == man['old']
    t = _ps(d, g); assert 'already installed' in t, t
    t = _ps(d, g, True); log(t)
    assert fm(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    t = _ps(d, g, True); assert 'already undone' in t, t
    t = _ps(d, g); assert fm(live) == man['new']
    t = _ps(d, g, True); assert fm(live) == man['old'] and not os.path.exists(live + TAG)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = _ps(d, g); log(t); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
    shutil.copy2(src, live)
    shutil.rmtree(g, ignore_errors=True)
    log('rehearsal ok (install, idempotent, undo byte-identical, undo twice, reinstall same md5, wrong md5 refused)')


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('spots', 'build', 'stage'):
        print(__doc__); return 2
    import kl_fa_bots as F
    if a[0] == 'spots':
        B = F.Built(a[1]); nav = F.Nav(B.scene.nav)
        print('fuel', [tuple(round(v) for v in s) for s in fuel_spots(B, nav)])
        print('ext ', [tuple(round(v) for v in s[:3]) for s in ext_spots_wall(B, nav)])
        return 0
    force = '--force' in a
    if force:
        a.remove('--force')
    if a[0] == 'build':
        build(a[1], a[2], pin=None if force else SRC_MD5)
        return 0
    scratch = None
    if '--rehearse' in a:
        i = a.index('--rehearse'); scratch = a[i + 1]; del a[i:i + 2]
    return stage(a[1], a[2], scratch)


if __name__ == '__main__':
    sys.exit(main())
