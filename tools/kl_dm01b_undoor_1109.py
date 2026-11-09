"""kl_dm01b_undoor_1109 - DM01B: put plain stock doors back where a kick door is dead or leads nowhere (owner 2026-11-09: DM03 had a kick door on one side with no room behind it;
the DM01B audit found the same on KL_Interact!1 KL_Door_4 (dead_one_side) and KL_Interact!2 KL_Door_2 (sealed closet)).

A kick door (kl_interact_graft) REPLACED a static door leaf of the map: the leaf entity left the scene, its collision was cut out of the .HVK (a filler copy took its static position), its
model chunks went unreferenced (stubs later reused), and a KL_Door_n group (23 nodes: leaf with the Dog Days model, two KickDoor_Arrow stands, a type-4 collision slab) took its place.
This tool undoes ONE or more of those, in place on the LIVE zip (many later layers sit on it: street2 van, PD2 guns, glass ...; a chain re-run is not possible):

  .gms/.buf/.prp  the KL_Door_n group goes (kl_scene.remove, kl_prpjoin.join skip); the ORIGINAL leaf entity (copy of the pre-door build's, REF label restored, own light lists restored) is
                  inserted into its old parent group behind the sibling it followed (kl_prpjoin.join insert); the same prp edit goes into the .bots zip
  .oct            the slot ids are renumbered, the group's items drop, the leaf is listed again in the room/tree boxes it had
  .HVK            the filler copy at the leaf's static position is replaced by the leaf's own shape, placement and MOPP code (static count and every list position unchanged);
                  the type-4 slab of the group goes
  .prm/.MAT/.TEX  the leaf's model closure is appended from the pre-door build (stub chunks first, kl_prmgraph.append), materials/textures merged (deduped), .oct records appended

  python tools/kl_dm01b_undoor_1109.py --out <dir> [--hosts D4,2D2] [--live <dir>]    writes F03_Main.zip, F03_Main.bots.zip, F03_Main.bots.base.md5 + report.json
  python tools/kl_dm01b_undoor_1109.py --check <dir> [--live <dir>]                   re-reads <dir> against the live files and proves the diff (exit 1 on a problem)

GUESS (no game run): the engine draws and collides the restored leaf like the stock one (it is the pre-door entity, byte for byte); the appended model closure behaves like the original
(same bytes, new chunk numbers); the freed room/tree boxes are the ones the pre-door .oct had. Hosts: D4 and 2D2 are the owner-requested reverts; D3 only with a proof (--hosts D4,2D2,D3).
"""
import collections, hashlib, json, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BS = chr(92)
WORK = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools'
REF_ZIP = WORK + r'\build\shopwhite_1024\stage\DM01B\F03_Main.zip'
LIVE_DIR = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps\DM01B'
PINS = dict(live='778b075c7e0d1e92185ea250bca0d248', bots='dccc9250c6e05b3f874630eb76aed8c1', base='6616525ad3caab8ce2029096cdb2f02b',
            ref='fd3e805dc8300d956d3428fb08fc4076')
LIVE_CHUNKS = 69089
# k = node of the pre-door build (= entity index + 1); ref = its REF label; hinge = world position of the group's Door leaf in the live map (the audit's key)
HOSTS = collections.OrderedDict([
    ('D4', dict(k=7166, ref=27190, top='KL_Interact!1', grp='KL_Door_4', hinge=(1888.0, 462.0, 17210.0), why='dead_one_side')),
    ('2D2', dict(k=7168, ref=27192, top='KL_Interact!2', grp='KL_Door_2', hinge=(1640.0, 462.0, 17290.0), why='sealed closet')),
    ('D3', dict(k=8844, ref=28868, top='KL_Interact!1', grp='KL_Door_3', hinge=(4560.0, 0.0, 22286.0), why='gates nothing (needs the proof)')),
])
DEFAULT = ['D4', '2D2']
GROUP_NODES = 23
ENT_ATTRS = ('name', 'tid', 'flags', 'group', 'rot', 'trans', 'raw', 'aux', 'ref')


def md5b(b):
    return hashlib.md5(b).hexdigest()


def md5(p):
    return md5b(open(p, 'rb').read())


def set_prop(sc, k, name, value):
    """Set one 32-bit field of node k's property tokens (kl_dm02door_1108.set_prop). -> old value."""
    import kl_prpjoin as J
    from kl_prp import units
    lab = J.labels('dd', sc.cls(k))
    node = sc.nodes[k]
    us = [list(u) for u in units(node['props'][1:-1])]
    i = lab.index(name)
    old = struct.unpack('<I', us[i][0][1])[0]
    us[i] = [(us[i][0][0], struct.pack('<I', value))]
    node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]
    return old


def get_prop(sc, k, name):
    import kl_prpjoin as J
    from kl_prp import units
    lab = J.labels('dd', sc.cls(k))
    us = units(sc.nodes[k]['props'][1:-1])
    return struct.unpack('<I', us[lab.index(name)][0][1])[0]


def free_stubs(B, p):
    """Unreached all-zero 16-byte chunks, lowest first (kl_dm02door_1108.free_stubs)."""
    import kl_gms, kl_prmgraph as G
    raw = kl_gms.unpack(B['.gms'])
    reached = G.closure(p, G.level_roots(B.sc.p, B.sc.tids, raw))
    return [i for i in range(1, len(p.chunks)) if p.chunks[i] == bytes(16) and i not in reached]


def read_members(path):
    with zipfile.ZipFile(path) as z:
        return [(n, z.read(n)) for n in z.namelist()]


# ---------------------------------------------------------------- the pieces
def find_group(B, h):
    """The live KL_Door_n group node of host h: scene path, 23 nodes, Door leaf at the audit's hinge. -> (group node, door leaf entity)."""
    sc = B.sc
    g = sc.resolve('ROOT' + BS + h['top'] + BS + h['grp'])
    if len(g) != 1:
        raise ValueError('%s: %d nodes named %s\\%s' % (h['grp'], len(g), h['top'], h['grp']))
    g = g[0]
    if sc.end[g] - g != GROUP_NODES:
        raise ValueError('%s: group has %d nodes, not %d' % (h['grp'], sc.end[g] - g, GROUP_NODES))
    d = sc.resolve(sc.path[g] + BS + 'Door')
    if len(d) != 1:
        raise ValueError('%s: no single Door leaf' % h['grp'])
    leaf = B.ents[d[0] - 1]
    p = B.fr[leaf][1]
    if max(abs(p[i] - h['hinge'][i]) for i in range(3)) > 1.0:
        raise ValueError('%s: Door leaf at %s, not the audited hinge %s' % (h['grp'], [round(v, 1) for v in p], h['hinge']))
    return g, leaf


def restore_entities(B, R, hosts, rep):
    """Mutate B.scene: drop the groups, insert the pre-door leaves. -> (removed entities, {host: new entity}, prp insert spec, group node list, leaf refs of the doors)."""
    import kl_scene
    A = B.scene
    nodeof = {e: i + 1 for i, e in enumerate(B.ents)}
    groups = {n: find_group(B, HOSTS[n]) for n in hosts}
    gnodes = sorted(g for g, _l in groups.values())
    gent = {n: B.ents[g - 1] for n, (g, _l) in groups.items()}
    # nothing outside a group may name a node inside one (squads, scripts)
    import kl_prpjoin as J
    inside = {k for g in gnodes for k in range(g, B.sc.end[g])}
    named = sorted({(B.sc.names[k], B.sc.names[x]) for k, _h, _f, _s, hit in J.references(B.sc) for x in (hit or []) if x in inside and k not in inside})
    if named:
        raise ValueError('nodes outside the groups name their nodes: %s' % named[:5])
    removed, door_refs, group_refs = [], {}, set()
    for n in hosts:
        walk = list(gent[n].walk())
        removed += walk
        group_refs |= {e.ref for e in walk}
        door_refs[n] = groups[n][1].ref
    rm = A.remove  # noqa
    for n in hosts:
        r = rm(gent[n])
        rep.setdefault('removed', {})[n] = r
    made, spec = {}, collections.defaultdict(list)
    for n in sorted(hosts, key=lambda x: HOSTS[x]['k']):
        h = HOSTS[n]
        re_ = R.ents[h['k'] - 1]
        if re_.ref != h['ref'] or re_.kids or re_.raw is not None or not re_.model:
            raise ValueError('%s: pre-door node %d is not the plain static leaf %d' % (n, h['k'], h['ref']))
        if any(re_ in p for p in R.scene.pairs):
            raise ValueError('%s: the leaf is in a room pair' % n)
        pn = B.sc.resolve(R.sc.path[R.sc.parent[h['k']]])
        if len(pn) != 1:
            raise ValueError('%s: parent %s is %d live nodes' % (n, R.sc.path[R.sc.parent[h['k']]][-60:], len(pn)))
        pent = B.ents[pn[0] - 1]
        if re_.parent is None or re_.parent.ref != pent.ref:
            raise ValueError('%s: live parent REF %d is not the pre-door parent REF %d' % (n, pent.ref, re_.parent.ref if re_.parent else -1))
        sibs = re_.parent.kids
        bykids = {e.ref: e for e in pent.kids}
        anchor = next((bykids[s.ref] for s in reversed(sibs[:sibs.index(re_)]) if s.ref in bykids), None)
        at = pent.kids.index(anchor) + 1 if anchor is not None else 0
        c = kl_scene.Entity()
        for a in ENT_ATTRS:
            setattr(c, a, getattr(re_, a))
        c.model, c.lkey, c.kids, c.links, c.parent = 0, 0, [], None, pent
        pent.kids.insert(at, c)
        made[n] = c
        pred = c
        while True:                                     # the base node this one follows in preorder: skip back over restored siblings
            i = pent.kids.index(pred)
            pred = pent.kids[i - 1] if i else None
            if pred is None or pred not in made.values():
                break
        before = B.sc.end[nodeof[pred]] if pred is not None else pn[0] + 1
        spec[before].append((pn[0], R.sc, h['k']))
        rep.setdefault('placed', {})[n] = dict(parent=pent.name.decode('latin1'), after=pred.name.decode('latin1') if pred is not None else None, at=at)
    # lists: the leaf's own light list, and the reverse entries lights held for it (by REF label)
    live_by = {e.ref: e for e in A.entities()}
    for n, c in made.items():
        re_ = R.ents[HOSTS[n]['k'] - 1]
        if re_.links is not None:
            c.links = [(None, b) if t is None else (live_by[t.ref], b) for t, b in re_.links if t is None or t.ref in live_by]
            rep.setdefault('lists', {})[n] = dict(own=len(c.links), own_ref=len(re_.links))
        back = 0
        for lt in R.ents:
            if lt.links and any(t is re_ for t, _b in lt.links):
                lv = live_by.get(lt.ref)
                if lv is None:
                    continue
                at = next(i for i, (t, _b) in enumerate(lt.links) if t is re_)
                before = sum(1 for t, _b in lt.links[:at] if t is None or t.ref in live_by)
                bits = lt.links[at][1]
                lv.links = list(lv.links or [])
                lv.links.insert(min(before, len(lv.links)), (c, bits))
                back += 1
        rep.setdefault('lists', {}).setdefault(n, {})['lights'] = back
    return removed, made, dict(spec), gnodes, door_refs, group_refs


def model_leg(B, R, made, mat_octj, rep):
    """Append the closure of the restored leaves' models from the pre-door build into B's .prm. -> (prm bytes, Mat, Tex, Oct with records)"""
    import kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_light
    pr, matR, texR, octR = G.read(R['.prm'], 'dd'), T.read_mat(R['.MAT']), T.read_tex(R['.TEX']), O.Oct.parse(R['.oct'])
    pS, matS, texS = G.read(B['.prm'], 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    if G.write(pS) != B['.prm']:
        raise ValueError('the live .prm does not round-trip')
    n0 = len(pS.chunks)
    roots = sorted({R.ents[HOSTS[n]['k'] - 1].model for n in made})
    kinds, args = G.walk(pr, roots)
    slots = {pr.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(matR, slots))
    for i, k in kinds.items():
        for off, typ, _k in G.fields(pr, i, k, args.get(i, 0)):
            if typ in 'tT' and pr.u32(i, off):
                want.add(pr.u32(i, off) % G.SLOTS['dd'])
    tex, tmap = T.merge_tex(texS, texR, want)
    mat, mmap = T.merge_mat(matS, matR, slots, tmap)
    lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
    if lack:
        raise ValueError('shaders missing in the map .fxc: %s' % lack)
    stubs = free_stubs(B, pS)
    pS.free = stubs[::-1]
    dry, cmap = G.append(pS, pr, roots, mmap, None, tmap)
    pS.free = stubs[::-1]
    unref = lambda v: (v & ~1) - 4
    held = mat_octj.record_refs()
    rec_d = {v: n for n, v in enumerate(octR.record_refs())}
    keep = sorted({rec_d[pr.u32(i, 0x1c)] for i, k in kinds.items() if k == 'root' and pr.u32(i, 0x1c)})
    octk, _same, refs_b = O.append_records(mat_octj, octR, cmap, keep)
    refs_a = dict(zip(held, octk.record_refs()))
    pnew, cmap2 = G.append(pS, pr, roots, mmap, {unref(a): unref(b) for a, b in refs_b.items()}, tmap)
    if cmap2 != cmap:
        raise ValueError('kl_prmgraph.append numbers chunks differently on the second run')
    moved = 0
    for i in range(1, n0):
        c = pnew.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
            v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
            if v != struct.unpack_from('<I', c, 0x1c)[0]:
                pnew.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]; moved += 1
    pb = G.write(pnew)
    mat.refs = T.material_refs(pb, mat.ninst)
    rep['model'] = dict(roots=roots, closure=len(kinds), stubs_free=len(stubs), chunks_before=n0, chunks_after=len(pnew.chunks), oct_records=len(keep),
                        materials=sorted(mmap[s] for s in slots), textures=len(want), oct_rerefs=moved, cmap={r: cmap[r] for r in roots})
    return pb, mat, tex, octk, {r: cmap[r] for r in roots}


def hvk_restore(B, R, made, door_refs, group_refs, rep):
    """Replace the filler at each leaf's static position by its own shape; drop the type-4 slabs. -> bytes"""
    import kl_hvk
    hvk, hr = kl_hvk.Hvk(B['.HVK']), kl_hvk.Hvk(R['.HVK'])
    n_static = hvk.static_count()
    refs_r = [kl_hvk.ref(i) for s in hr.shapes if s.type == kl_hvk.STATIC for i in s.inst]
    refs_l = [kl_hvk.ref(i) for s in hvk.shapes if s.type == kl_hvk.STATIC for i in s.inst]
    if len(refs_r) != len(refs_l):
        raise ValueError('static counts differ: pre-door %d, live %d' % (len(refs_r), len(refs_l)))
    cnt = collections.Counter(refs_l)
    for n in made:
        ref = HOSTS[n]['ref']
        idx = refs_r.index(ref)
        if refs_r.count(ref) != 1 or ref in cnt:
            raise ValueError('%s: REF %d is not one static placement of the pre-door map only' % (n, ref))
        fill = refs_l[idx]
        if cnt[fill] < 8:
            raise ValueError('%s: live static %d (REF %d) is not a filler copy (x%d)' % (n, idx, fill, cnt[fill]))
        rs, rk = next((s, k) for s in hr.shapes if s.type == kl_hvk.STATIC for k, i in enumerate(s.inst) if kl_hvk.ref(i) == ref)
        new, flat = [], 0
        done = False
        for s in hvk.shapes:
            if s.type == kl_hvk.STATIC and not done and flat <= idx < flat + len(s.inst):
                j = idx - flat
                if j:
                    new.append(s.clone(s.inst[:j], s.mopp[:j]))
                new.append(rs.clone([rs.inst[rk]], [rs.mopp[rk]]))
                if j + 1 < len(s.inst):
                    new.append(s.clone(s.inst[j + 1:], s.mopp[j + 1:]))
                done = True
            else:
                new.append(s)
            if s.type == kl_hvk.STATIC:
                flat += len(s.inst)
        if not done:
            raise ValueError('%s: static position %d not found' % (n, idx))
        hvk.shapes = new
        refs_l[idx] = ref
        rep.setdefault('hvk', {})[n] = dict(static_index=idx, filler_ref=fill)
    # slabs
    drop = set(door_refs.values())
    out, slabs = [], 0
    for s in hvk.shapes:
        if s.type == kl_hvk.STATIC or not any(kl_hvk.ref(i) in group_refs for i in s.inst):
            out.append(s); continue
        keep = [k for k, i in enumerate(s.inst) if kl_hvk.ref(i) not in group_refs]
        if s.type != 4 or any(kl_hvk.ref(i) in group_refs and kl_hvk.ref(i) not in drop for i in s.inst):
            raise ValueError('a group REF has a placement that is not a type-4 door slab (type %d)' % s.type)
        slabs += len(s.inst) - len(keep)
        if keep:
            out.append(s.clone([s.inst[k] for k in keep], []))
    if slabs != len(drop):
        raise ValueError('%d slab placements for %d doors' % (slabs, len(drop)))
    if any(kl_hvk.ref(i) in group_refs for s in hvk.shapes if s.type == kl_hvk.STATIC for i in s.inst):
        raise ValueError('a group REF is a static placement')
    hvk.shapes = out
    if hvk.static_count() != n_static:
        raise ValueError('static count %d -> %d' % (n_static, hvk.static_count()))
    b = hvk.serialize()
    if kl_hvk.Hvk(b).serialize() != b:
        raise ValueError('.HVK does not round-trip')
    rep['hvk_slabs'] = slabs
    return b


def prp_join(sc, gnodes, spec):
    import kl_prpjoin as J
    return J.join(sc, [(sc, t) for t in sc.tops()], 'undoor', skip=set(gnodes), insert=spec)


# ---------------------------------------------------------------- build
def build(live_dir=LIVE_DIR, out=None, hosts=DEFAULT, ref_zip=REF_ZIP, pins=True, log=print):
    import kl_fa_bots as F, kl_prpjoin as J, kl_octree as O, kl_gms, kl_graft, kl_texmat as T, kl_prmgraph as G
    zl, zb, zbase = (os.path.join(live_dir, n) for n in ('F03_Main.zip', 'F03_Main.bots.zip', 'F03_Main.bots.base.md5'))
    if pins:
        for p, k in ((zl, 'live'), (zb, 'bots'), (zbase, 'base'), (ref_zip, 'ref')):
            if md5(p) != PINS[k]:
                raise ValueError('%s md5 %s is not the pinned %s' % (p, md5(p), PINS[k]))
    for h in hosts:
        if h not in HOSTS:
            raise ValueError('unknown host %s (have %s)' % (h, list(HOSTS)))
    rep = dict(hosts=list(hosts), pins={k: PINS[k] for k in PINS})
    B, R = F.Built(zl), F.Built(ref_zip)
    A = B.scene
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(A, octx, rmi, rmc)
    slot0 = A.slots()
    removed, made, spec, gnodes, door_refs, group_refs = restore_entities(B, R, list(hosts), rep)
    # the model first (the entities need their new model numbers before the .gms is written)
    slotR = R.scene.slots()
    octR = O.Oct.parse(R['.oct'])
    # ---- slot ids: renumber, drop the groups, list the leaves
    # (the .gms write follows the model leg, so the new leaf slots are taken from a trial numbering of the final tree)
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    drop = {slot0[e] + 2 for e in removed}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, drop), O.remap_ids(rmi, ids, drop), O.remap_ids(rmc, ids, drop)
    boxes = {}
    for n, c in made.items():
        sid = slotR[R.ents[HOSTS[n]['k'] - 1]] + 2
        found = []
        for ri, room in enumerate(octR.rooms):
            for ti, t in enumerate(room):
                for it in (t.items if t else ()):
                    if it[0] == sid:
                        found.append((ri, ti, t.world(it[1:4]), t.world([v + 1 for v in it[4:7]]), tuple(it[1:7]), t.origin, t.scale))
        if not found:
            raise ValueError('%s: the leaf is in no room tree of the pre-door .oct' % n)
        for ri, ti, lo, hi, q, org, sc_ in found:
            t = octn.rooms[ri][ti]
            if t is None:
                raise ValueError('%s: live room %d has no tree %d' % (n, ri, ti))
            octn.rooms[ri][ti] = O.join_trees(t, O.build_tree([(slot1[c] + 2, lo, hi)], t.origin, t.scale))
            octn.rooms[ri][ti].check()
        boxes[n] = [(f[0], f[1], f[2], f[3]) for f in found]
    rep['oct_boxes'] = {n: [(a, b) for a, b, _l, _h in v] for n, v in boxes.items()}
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('room set check after the renumbering: %s (before: %s)' % (post, pre))
    # ---- model
    prm_bytes, mat, tex, octj, cmap = model_leg(B, R, made, octn, rep)
    for n, c in made.items():
        c.model = cmap[R.ents[HOSTS[n]['k'] - 1].model]
        set_prop(R.sc, HOSTS[n]['k'], 'ZGEOM[4]', c.model)
    # ---- scene
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    spec_ = dict(spec)
    Jn = prp_join(B.sc, gnodes, spec_)
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot2 = A.slots()
    if slot2 != slot1:
        raise ValueError('slot numbers moved between the oct edit and the write')
    # ---- hvk
    hvk_bytes = hvk_restore(B, R, made, door_refs, group_refs, rep)
    # ---- the zips
    new = dict(B.files)
    E = B.ext
    new[E['.prp']], new[E['.gms']], new[E['.buf']] = prp, kl_gms.pack(gms), buf
    new[E['.oct']], new[E['.rmi']], new[E['.rmc']] = octj.pack(), rmin.pack(), rmcn.pack()
    new[E['.prm']], new[E['.MAT']], new[E['.TEX']], new[E['.HVK']] = prm_bytes, T.write_mat(mat), T.write_tex(tex), hvk_bytes
    p2 = G.read(prm_bytes, 'dd')
    if G.write(p2) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[E['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    # bots: same edit on the bots .prp (same node numbers: only props differ)
    SB = J.Scene.from_zip(zb)
    if SB.names != B.sc.names or SB.tids != B.sc.tids:
        raise ValueError('the bots scene has other nodes than the plain one')
    JB = prp_join(SB, gnodes, spec_)
    if JB.names != Jn.names or JB.tids != Jn.tids:
        raise ValueError('bots and plain scene differ after the edit')
    bots_prp = JB.p.serialize()
    rep['dangling'] = dict(live=len(J.dangling(B.sc)), plain=len(J.dangling(Jn)), bots_in=len(J.dangling(SB)), bots=len(J.dangling(JB)))
    if rep['dangling']['plain'] != rep['dangling']['live'] or rep['dangling']['bots'] != rep['dangling']['bots_in']:
        raise ValueError('dangling references changed: %s' % rep['dangling'])
    rep['entries_changed'] = len(G.read(prm_bytes, 'dd').chunks) != LIVE_CHUNKS
    rep['chunks'] = len(p2.chunks)
    if out:
        os.makedirs(out, exist_ok=True)
        pz = kl_graft.write_zip(os.path.join(out, 'F03_Main.zip'), [(nm, new[nm]) for nm in B.order])
        bm = dict(read_members(zb))
        bnew = dict(new)
        bnew[E['.prp']] = bots_prp
        if [n for n in bm if n != E['.prp'] and bm[n] != B.files[n]]:
            raise ValueError('the bots zip differs from the plain zip in more than the .prp')
        bz = kl_graft.write_zip(os.path.join(out, 'F03_Main.bots.zip'), [(nm, bnew[nm]) for nm in bm])
        with open(os.path.join(out, 'F03_Main.bots.base.md5'), 'wb') as f:
            f.write((md5(pz) + '\n').encode('ascii'))
        rep['md5'] = dict(plain=md5(pz), bots=md5(bz), base=md5(os.path.join(out, 'F03_Main.bots.base.md5')))
        json.dump(rep, open(os.path.join(out, 'report.json'), 'w'), indent=1, default=str)
    log(json.dumps(rep, indent=1, default=str)[:4000])
    return rep


# ---------------------------------------------------------------- the proof
def check(out, live_dir=LIVE_DIR, ref_zip=REF_ZIP, hosts=DEFAULT, log=print):
    """Re-read the staged files against the live ones. -> list of problems ([] = the diff is exactly the undo)."""
    import kl_fa_bots as F, kl_prpjoin as J, kl_octree as O, kl_hvk, kl_prmgraph as G, kl_scene
    bad = []
    zl, zo, zbo, zbl = (os.path.join(live_dir, 'F03_Main.zip'), os.path.join(out, 'F03_Main.zip'), os.path.join(out, 'F03_Main.bots.zip'), os.path.join(live_dir, 'F03_Main.bots.zip'))
    L, N, R = F.Built(zl), F.Built(zo), F.Built(ref_zip)
    # 0. members
    ml, mn = dict(read_members(zl)), dict(read_members(zo))
    if list(ml) != list(mn):
        bad.append('member list differs')
    changed = sorted(n.rsplit('_Main', 1)[1] for n in ml if ml[n] != mn.get(n))
    log('members changed: %s' % changed)
    if set(changed) - {'.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.HVK'}:
        bad.append('unexpected members changed: %s' % changed)
    # 1. entities
    lref = {e.ref: e for e in L.ents}
    nref = {e.ref: e for e in N.ents}
    groups = {}
    for n in hosts:
        h = HOSTS[n]
        g, leaf = find_group(L, h)
        groups[n] = {e.ref for e in L.ents[g - 1].walk()}
    gone = set().union(*groups.values())
    add = {HOSTS[n]['ref'] for n in hosts}
    if set(lref) - set(nref) != gone:
        bad.append('entities that left: %s, expected %d group entities' % (sorted(set(lref) - set(nref))[:5], len(gone)))
    if set(nref) - set(lref) != add:
        bad.append('entities that came: %s, expected %s' % (sorted(set(nref) - set(lref)), sorted(add)))
    nmodel = {}
    for r, e in nref.items():
        if r in add:
            continue
        o = lref[r]
        if any(getattr(e, a) != getattr(o, a) for a in ENT_ATTRS + ('model',)):
            bad.append('entity REF %d changed' % r); break
        if (o.parent.ref if o.parent else None) != (e.parent.ref if e.parent else None):
            bad.append('entity REF %d moved' % r); break
        ol = None if o.links is None else [(t.ref if t else None, b) for t, b in o.links if t is None or t.ref not in gone]
        nl = None if e.links is None else [(t.ref if t else None, b) for t, b in e.links if t is None or t.ref not in add]
        if ol != nl:
            bad.append('list of REF %d changed (%s vs %s)' % (r, ol and len(ol), nl and len(nl))); break
    for n in hosts:
        re_, ne = R.ents[HOSTS[n]['k'] - 1], nref[HOSTS[n]['ref']]
        if any(getattr(re_, a) != getattr(ne, a) for a in ENT_ATTRS):
            bad.append('%s: restored entity differs from the pre-door one' % n)
        if re_.parent.ref != ne.parent.ref or ne.kids or (ne.links is None) != (re_.links is None):
            bad.append('%s: parent / kids / list presence differ' % n)
        if ne.links and [t.ref for t, _b in ne.links if t] != [t.ref for t, _b in re_.links if t and t.ref in lref]:
            bad.append('%s: own light list differs' % n)
        for lt in R.ents:
            if lt.links and any(t is re_ for t, _b in lt.links) and lt.ref in nref:
                if not any(t is not None and t.ref == ne.ref for t, _b in nref[lt.ref].links or ()):
                    bad.append('%s: light REF %d lost the leaf' % (n, lt.ref))
        nmodel[n] = ne.model
    if N.scene.check():
        bad.append('kl_scene.check: %s' % N.scene.check()[:3])
    if [(a is not None and a.ref, b.ref) for a, b in N.scene.pairs] != [(a is not None and a.ref, b.ref) for a, b in L.scene.pairs if (a is None or a.ref not in gone) and b.ref not in gone]:
        bad.append('room pairs changed')
    # 2. prp: path list of old minus the groups plus the leaves; props equal node by node
    def rows(S):
        return [(S.path[k], J.text(S, S.nodes[k]['props']), [(c[0], J.text(S, c[1])) if False else c[0] for c in S.nodes[k]['ctrls']]) for k in range(len(S.nodes))]
    lr, nr = rows(L.sc), rows(N.sc)
    lset = collections.Counter((r[0], r[1]) for r in lr)
    nset = collections.Counter((r[0], r[1]) for r in nr)
    lost, came = lset - nset, nset - lset
    exp_lost = sum(L.sc.end[find_group(L, HOSTS[n])[0]] - find_group(L, HOSTS[n])[0] for n in hosts)
    if sum(lost.values()) != exp_lost:
        bad.append('%d prp nodes left, expected %d' % (sum(lost.values()), exp_lost))
    if sum(came.values()) != len(hosts):
        bad.append('%d prp nodes came, expected %d' % (sum(came.values()), len(hosts)))
    for n in hosts:
        k = N.sc.resolve(R.sc.path[HOSTS[n]['k']])
        k = [x for x in k if N.ents[x - 1].ref == HOSTS[n]['ref']]
        if len(k) != 1:
            bad.append('%s: leaf node not found in the new .prp' % n); continue
        kk = k[0]
        tx = lambda S, i: J.text(S, S.nodes[i]['props'])
        if get_prop(N.sc, kk, 'ZGEOM[4]') != nmodel[n]:
            bad.append('%s: .prp model %d != .gms model %d' % (n, get_prop(N.sc, kk, 'ZGEOM[4]'), nmodel[n]))
        a, b = R.sc.nodes[HOSTS[n]['k']]['props'], N.sc.nodes[kk]['props']
        ra = [J.text(R.sc, [t]) for t in a]; rb = [J.text(N.sc, [t]) for t in b]
        diff = [i for i, (x, y) in enumerate(zip(ra, rb)) if x != y]
        if len(ra) != len(rb) or len(diff) > 1:
            bad.append('%s: restored .prp node differs from the pre-door one in %d tokens' % (n, len(diff)))
        if N.sc.nodes[kk]['ctrls'] != [] and len(N.sc.nodes[kk]['ctrls']) != len(R.sc.nodes[HOSTS[n]['k']]['ctrls']):
            bad.append('%s: controllers differ' % n)
    # bots zip: its .prp is the plain one edited the same way
    SBo, SBl = J.Scene.from_zip(zbo), J.Scene.from_zip(zbl)
    if SBo.names != N.sc.names or SBo.tids != N.sc.tids:
        bad.append('bots scene nodes differ from the new plain scene')
    mbo, mbl = dict(read_members(zbo)), dict(read_members(zbl))
    pn = [n for n in mbo if n.lower().endswith('.prp')][0]
    if [n for n in mbo if mbo[n] != mn[n]] != [pn]:
        bad.append('bots zip differs from the new plain zip in more than the .prp: %s' % [n for n in mbo if mbo[n] != mn[n]])
    lb = collections.Counter((SBl.path[k], J.text(SBl, SBl.nodes[k]['props'])) for k in range(len(SBl.nodes)))
    nb = collections.Counter((SBo.path[k], J.text(SBo, SBo.nodes[k]['props'])) for k in range(len(SBo.nodes)))
    if sum((lb - nb).values()) != exp_lost or sum((nb - lb).values()) != len(hosts):
        bad.append('bots prp diff: %d left / %d came' % (sum((lb - nb).values()), sum((nb - lb).values())))
    # 3. oct: items by entity REF
    def items(S, oct_):
        by = {s + 2: e for e, s in S.scene.slots().items()}
        out = collections.Counter()
        for ri, room in enumerate(oct_.rooms):
            for ti, t in enumerate(room):
                for it in (t.items if t else ()):
                    out[(ri, ti, by[it[0]].ref)] += 1
        return out
    il, i_n = items(L, O.Oct.parse(L['.oct'])), items(N, O.Oct.parse(N['.oct']))
    lostc, camec = il - i_n, i_n - il
    if {k[2] for k in lostc} - gone or {k[2] for k in camec} != add:
        bad.append('oct items: left %s, came %s' % (sorted({k[2] for k in lostc} - gone)[:4], sorted({k[2] for k in camec})))
    # every item of a surviving entity is still in the same room trees
    keep = collections.Counter({k: v for k, v in il.items() if k[2] not in gone})
    if keep - i_n:
        bad.append('oct: items of surviving entities lost')
    # restored leaf boxes: the same room/tree as the pre-door .oct
    ir = items(R, O.Oct.parse(R['.oct']))
    for n in hosts:
        want = {(a, b) for (a, b, r) in ir if r == HOSTS[n]['ref']}
        got = {(a, b) for (a, b, r) in i_n if r == HOSTS[n]['ref']}
        if want != got:
            bad.append('%s: oct rooms/trees %s, pre-door %s' % (n, sorted(got), sorted(want)))
    # .rmi/.rmc: same boxes (room ids go through the entity refs)
    for ext in ('.rmi', '.rmc'):
        a, b = O.RoomIndex.parse(L[ext]), O.RoomIndex.parse(N[ext])
        if len(a.boxes) != len(b.boxes):
            bad.append('%s box count %d -> %d' % (ext, len(a.boxes), len(b.boxes)))
    # 4. hvk
    hl, hn, hr = kl_hvk.Hvk(L['.HVK']), kl_hvk.Hvk(N['.HVK']), kl_hvk.Hvk(R['.HVK'])
    sig = lambda s: (s.type, s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub))
    flat = lambda h: [(sig(s), bytes(i), s.mopp[j][0] + s.mopp[j][1] if s.mopp else None) for s in h.shapes if s.type == 1 for j, i in enumerate(s.inst)]
    fl, fn, fr = flat(hl), flat(hn), flat(hr)
    ridx = {kl_hvk.ref(x[1]): k for k, x in enumerate(fr)}
    pos = {ridx[HOSTS[n]['ref']] for n in hosts}
    if len(fl) != len(fn) or hl.static_count() != hn.static_count():
        bad.append('static count changed')
    d = {k for k in range(min(len(fl), len(fn))) if fl[k] != fn[k]}
    if d != pos:
        bad.append('static positions that changed: %s, expected %s' % (sorted(d)[:6], sorted(pos)))
    for k in pos:
        if fn[k] != fr[k]:
            bad.append('static %d is not the pre-door placement byte for byte' % k)
    if hl.lists != hn.lists or hl.box != hn.box or hl.tail != hn.tail:
        bad.append('.HVK list codes / box / tail changed')
    nonl = collections.Counter((sig(s), bytes(i)) for s in hl.shapes if s.type != 1 for i in s.inst)
    nonn = collections.Counter((sig(s), bytes(i)) for s in hn.shapes if s.type != 1 for i in s.inst)
    lostp, camep = nonl - nonn, nonn - nonl
    if camep or sum(lostp.values()) != len(hosts) or {kl_hvk.ref(x[1]) for x in lostp} != {g for g in gone if any(kl_hvk.ref(i) == g for s in hl.shapes if s.type != 1 for i in s.inst)}:
        bad.append('non-static placements: %d left (expected %d slabs), %d new' % (sum(lostp.values()), len(hosts), sum(camep.values())))
    if [s.type for s in hn.shapes if s.type != 1 and s.type != 4] != [s.type for s in hl.shapes if s.type != 1 and s.type != 4]:
        bad.append('shapes other than the slabs changed')
    if any(kl_hvk.ref(i) in gone for s in hn.shapes for i in s.inst):
        bad.append('a placement of a removed group REF is left in the .HVK')
    # 5. prm: the restored closure equals the pre-door one byte for byte (chunk numbers aside), nothing else changed
    pl, pn_, pr = G.read(L['.prm'], 'dd'), G.read(N['.prm'], 'dd'), G.read(R['.prm'], 'dd')
    ch = [i for i in range(min(len(pl.chunks), len(pn_.chunks))) if pl.chunks[i] != pn_.chunks[i]]
    stub = [i for i in ch if pl.chunks[i] == bytes(16)]
    if len(ch) != len(stub):
        bad.append('%d chunks of the live .prm changed that were not stubs' % (len(ch) - len(stub)))
    for n in hosts:
        rm_, nm_ = R.ents[HOSTS[n]['k'] - 1].model, nmodel[n]
        kr, _a = G.walk(pr, [rm_])
        kn, _b = G.walk(pn_, [nm_])
        sr = sorted((k, len(pr.chunks[i])) for i, k in kr.items())
        sn = sorted((k, len(pn_.chunks[i])) for i, k in kn.items())
        if sr != sn:
            bad.append('%s: model closure %d chunks vs %d / kinds differ' % (n, len(kr), len(kn)))
        vr = sorted(bytes(pr.chunks[i]) for i, k in kr.items() if k in ('vtx', 'idx'))
        vn = sorted(bytes(pn_.chunks[i]) for i, k in kn.items() if k in ('vtx', 'idx'))
        if vr != vn:
            bad.append('%s: vertex / index data differ from the pre-door model' % n)
    if len(pn_.chunks) != len(pl.chunks):
        log('NOTE: .prm chunk count %d -> %d (Entries= in KLJoin.ini / KLGuns.ini needs the new count)' % (len(pl.chunks), len(pn_.chunks)))
    return bad


def main(a):
    if '--check' in a:
        out = a[a.index('--check') + 1]
        live = a[a.index('--live') + 1] if '--live' in a else LIVE_DIR
        hs = a[a.index('--hosts') + 1].split(',') if '--hosts' in a else DEFAULT
        bad = check(out, live, hosts=hs)
        for b in bad:
            print('PROBLEM', b)
        print('RESULT: %s' % ('FAIL %d' % len(bad) if bad else 'PASS'))
        return 1 if bad else 0
    if '--out' not in a:
        print(__doc__); return 2
    out = a[a.index('--out') + 1]
    live = a[a.index('--live') + 1] if '--live' in a else LIVE_DIR
    hs = a[a.index('--hosts') + 1].split(',') if '--hosts' in a else DEFAULT
    build(live, out, hs, pins='--no-pins' not in a)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
