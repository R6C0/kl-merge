#!/usr/bin/env python3
"""
kl_dog_1025.py - DM02 Late Night Opening (mall, Dog Days slot F02): ONE POLICE DOG. Written 2026-10-25, OFFLINE only, nothing is run in the game.

    python kl_dog_1025.py build <in F02_Main.zip> <out F02_Main.zip> [--force]     one build (pinned on the live DM02 zip a8216b38)
    python kl_dog_1025.py check <zip>
    python kl_dog_1025.py stage <in F02_Main.zip> <out folder> [--rehearse <scratch>]
                                  build + md5-chained INSTALL/UNDO (.bat + .ps1 + dog.json) and a rehearsal on a scratch game folder

WHAT THE PLAYER SEES  A German shepherd (Dog Days F07's 'FinancialAlley_Dog', the stock chain cloned) waits out of sight in the street plaza east of
  the police-car lane. About 32 s after the round start (just after the 25 s 'Backstop' timer has sent the three police cars and their SWAT men
  to the entrance) the squad is released: the dog runs to the mall entrance, then inside to the lobby and on to the atrium, attacking any heister
  it meets (eUnleashed, soldier style eDog: no cover, no throwing; barks / growls from the level's own sound bank).
  THE TOGGLE IS THE INSTALLER UNDO: UNDO dm02 dog.bat puts the previous DM02 zip back byte for byte (md5-chained on the live zip a8216b38).

THE CHAIN (all cloned from the stock F07 dog, 'Gameplay!020_Loot!021_FinancialAlley_Dog', nodes 123..128)
  squad top (ZSquadScript, parked: field 3 = 0 and every list empty, as the stock dog and the OldWaves! chain), DefendBehaviour (+ Pos#01),
  Dog group, Ground actor (ZFFActor 0x2007f9, ZSoldier 'eDog'). The stock release is the box trigger 'tbReleaseDog' (TriggerBox field 17 lists the
  DefendBehaviour); here it is a TriggerDelay2 'T_Start' on the AIMonitor round-start list (the timer mechanism of kl_dm03a_swat_1025 / the mall's
  cars) because DM02 has no trigger volume at the street and the cars are timer-driven too. The 3 Defend routs are chained by field 7
  (entrance -> lobby -> atrium) so the dog keeps moving inward.

WHAT IS GRAFTED (the dog model is NOT in DM02): F07's model root 599 = 3 LOD meshes, 1 material (Dog_German_Shepherd_01), 3 textures, a 96-bone
  skeleton (the human bone names + tail, tail1, tail2, free_bone01).  kl_chars.put's steps on the extracted closure: reid (level-wide bone ids),
  sync_bone_ids, rebind (skel tables [8][9][10] to the level's own .ANM bone numbers by NAME), then kl_dm02_mall_1025.cars' model graft (merge_tex /
  merge_mat / G.append / O.append_records, root's .oct offset re-pointed).  The .ANM is NOT touched and NEVER copied: DM02's own .ANM already holds
  the 'Dog' animation collection (247 clips) and the tail bone names (verified here by name), so only the skeleton is bound to it.
  Sounds: the actor's ZLNKOBJ / ZLNKWHANDS integers are .SND offsets; F07 and DM02 share them (265488 foot, 267312 character_sounddefs/dog/dog_01,
  265616 engine material): proven BY NAME for every root in check().

BUDGET  actors 67 -> 68 (cap 99), squads 24 -> 25 (cap 55); +1 actor of ~350 KB model data; the .prm chunk table grows by ~40 chunks (limit 73,728).

GUESSES / UNPROVEN (each also in a code comment)  (1) the dog skinned onto DM02's .ANM 'Dog' set plays its run / attack clips correctly (the clips
  are DD's own, but never seen on this level); (2) a chained DefendBehaviourRout advances when its Pos is reached (the OldWaves! form says so);
  (3) eUnleashed chooses a heister target through the mall's walk mesh from the street (nav.path proves a route, not the AI's choice); (4) the dog
  barking is audible at the volume of F07; (5) the model's shader / material set is complete in the .fxc (checked by name, not rendered); (6) timing
  (DOG_AT) relative to the cars; (7) a dog killed in FA pays nothing / counts nothing (stock behaviour in F07, not tested here).
"""
import collections, hashlib, json, math, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_anm, kl_fa, kl_gms, kl_graft, kl_light, kl_scene
import kl_chars as CH
import kl_fa_bots as KB
import kl_fa_fed as FED
import kl_fa_author as AU
import kl_fa_climb2 as C2
import kl_interact_graft as IG
import kl_dm01b_gas_1025 as GS
import kl_dm02_assault_1025 as AS
import kl_octree as O
import kl_old_waves as KOW
import kl_prmgraph as G
import kl_texmat as T
import kl_prpjoin as J
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
SRC_MD5 = 'a8216b3887b013c96ddd587a11988299'     # the live DM02 zip (mall pass, 2026-10-25)
TAG = '.before-1025dog'
MAP, FILE = 'DM02', 'F02_Main.zip'
ENGINE_ACTORS, ENGINE_SQUADS = 99, 55            # engine-proven caps (re/actor_caps.md)

# ---- the stock donor chain (F07 nodes; asserted by name in make_nodes)
DONOR = 'F07'
OLD_TOP = R + 'Gameplay!020_Loot!021_FinancialAlley_Dog'
K_TOP, K_DEF, K_POS, K_DOGG, K_GROUND = 123, 124, 125, 126, 127          # 128 = tbReleaseDog (not cloned: replaced by the timer)
DOG_ROOT = 599                                   # ZGEOM[4] of F07's dog actor = model root chunk in F07's .prm
# ---- the new nodes
SQUAD_TOP = 'KL_Dog!Squad'
CLOCK = 'KL_Dog!Clock'
ROUTS = ['10_Defend', '20_Defend', '30_Defend']
DOG_AT = 32.0            # s after the round start. GUESS: the cars' 'Backstop' fires at 25 s, the lane takes ~10 s, the dog needs ~6 s from the park to the entrance
# ---- places (walk-mesh cells of the main part, snapped by plan())
PARK_AT = (2600.0, 0.0, -9000.0)                 # street plaza east of the car lane: open (clearance 400), 930 cm from the lane, 4100 cm from the entrance
POST_AT = [(600.0, 0.0, -5400.0),                # in front of the entrance (the cars' posts stand at z -5600..-6050)
           (0.0, 0.0, -2500.0),                  # lobby
           (-300.0, 0.0, -700.0)]                # atrium (the dog stops here, the FA crew comes down to it)
# the mall's car lane (build_report of kl_dm02_mall_1025: starts -> stops of the three cars); the park stays 500+ cm from it
LANE = [((1705.0, -10333.0), (1050.0, -6300.0)), ((1965.0, -10471.0), (1039.0, -6771.0)), ((1917.0, -10318.0), (1221.0, -6917.0))]
CLEAR_PARK, CLEAR_POST, FAR_FROM_CREW, LANE_GAP = 150.0, 60.0, 3000.0, 500.0


def md5(b):
    return hashlib.md5(b).hexdigest()


def md5f(p):
    return md5(open(p, 'rb').read())


# ------------------------------------------------------------------ plan: cells
def _dseg(p, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz)


def plan(B, nav, log):
    """-> dict(home, park, posts, walk): park cell (x, y, z, polygon) and the 3 Defend cells, all on the crew's (main) mesh part."""
    st = KB.stations(B, nav)
    home = st['home']
    snap = lambda target, clear, extra=lambda c: True: min(
        (c for c in nav.around(target, 600.0, home, step=40.0, dy=60.0) if nav.clearance(c[0], c[1], c[2]) >= clear and extra(c)),
        key=lambda c: math.hypot(c[0] - target[0], c[2] - target[2]), default=None)
    far = lambda c: all(math.hypot(c[0] - s[0][0], c[2] - s[0][2]) >= FAR_FROM_CREW for s in st['starts']) and \
        all(min(_dseg((c[0], c[2]), a, b) for a, b in LANE) >= LANE_GAP for _ in (0,))
    park = snap(PARK_AT, CLEAR_PARK, far)
    posts = [snap(t, CLEAR_POST) for t in POST_AT]
    if park is None or any(p is None for p in posts):
        raise ValueError('no cell found: park %s posts %s' % (park, posts))
    walk, a = [], park
    for p in posts:
        r = nav.path(a[:4], p[:4])
        if r is None:
            raise ValueError('no walk-mesh route from %s to %s' % ([round(v) for v in a[:3]], [round(v) for v in p[:3]]))
        walk.append(round(r[1]))
        a = p
    log('  dog: park %s; posts %s; mesh walk park->entrance->lobby->atrium %s cm' % (
        [round(v) for v in park[:3]], [[round(v) for v in p[:3]] for p in posts], walk))
    return dict(home=home, park=park, posts=posts, walk=walk)


# ------------------------------------------------------------------ nodes
def make_nodes(B, d, P):
    """The dog chain cloned from F07 + the clock. -> (Maker, tops, dog actor Node)."""
    sc = B.sc
    dsc = d.sc
    for k, nm in ((K_TOP, 'Gameplay!020_Loot!021_FinancialAlley_Dog'), (K_DEF, 'DefendBehaviour'), (K_POS, 'Pos#01'), (K_DOGG, 'Dog'), (K_GROUND, 'Ground')):
        if dsc.names[k] != nm:
            raise ValueError('F07 node %d is %r, expected %r (the donor changed?)' % (k, dsc.names[k], nm))
    if d.ent(K_GROUND).model != DOG_ROOT or d.ent(K_GROUND).raw:
        raise ValueError('F07 dog actor: model %s, KEYS %s' % (d.ent(K_GROUND).model, bool(d.ent(K_GROUND).raw)))
    M = KB.Maker()
    me = R + SQUAD_TOP
    rn = lambda s: (me + s[len(OLD_TOP):]) if s.lower().startswith(OLD_TOP.lower()) else s
    top = IG.clone(M, d, K_TOP, SQUAD_TOP, rn)
    M.place(top, (0.0, 0.0, 0.0))
    # the parked squad: stock fields 3 = 0 and every list empty; asserted, not set (the stock dog is already so)
    sq = [kl_fa.value(dsc, u) for u in KB.units(dsc.nodes[K_TOP]['ctrls'][0][1][1:-1])]
    if sq[3] != 0 or any(sq[j] != [] for j in range(4, 19)):
        raise ValueError('F07 dog squad is not parked: %s' % sq[:8])
    posts = P['posts']
    for j, name in enumerate(ROUTS):
        dn = top.add(IG.clone(M, d, K_DEF, name, rn))
        M.place(dn, (0.0, 0.0, 0.0))
        pp = dn.add(IG.clone(M, d, K_POS, 'Pos#01', rn))
        M.place(pp, posts[j][:3])                                    # world place (every group of the chain stands at the origin)
        nxt = [me + BS + ROUTS[j + 1]] if j + 1 < len(ROUTS) else []
        # field 7 = the next rout (GUESS 2: a Defend rout hands over when its Pos is reached, as the OldWaves! form's chain)
        M.set(dn, 'DefendBehaviourRout', {1: [me + BS + name + BS + 'Pos#01'], 7: nxt})
    a, b = P['park'], posts[0]
    dx, dz = b[0] - a[0], b[2] - a[2]
    L = math.hypot(dx, dz) or 1.0
    grp = top.add(IG.clone(M, d, K_DOGG, 'Dog', rn))
    M.place(grp, a[:3], KB.rot9(dx / L, dz / L))
    act = grp.add(IG.clone(M, d, K_GROUND, 'Ground', rn))
    M.place(act, (0.0, 0.0, 0.0))
    # ---- the clock: the round-start timer
    node = lambda path: sc.resolve(path)[0]
    clock = FED.clone_built(M, B, node(R + KB.SQUAD + 'Squad#02'), CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    t = clock.add(FED.clone_built(M, B, node(KOW.TIMER_FORM), 'T_Start'))
    M.place(t, (0.0, 0.0, 0.0))
    M.set(t, 'TriggerDelay2', {0: float(DOG_AT), 4: [me + BS + ROUTS[0]]})
    return M, [top, clock], act


# ------------------------------------------------------------------ the model graft
def graft_model(B, d, log):
    """The dog closure of F07's .prm made fit for DM02: bone ids, .ANM binding. -> (ex, root in ex, prm_s, anm names, report)"""
    prm_s = G.read(B['.prm'], 'dd')
    anm = kl_anm.Anm(B['.ANM'], 'dd')
    ex, cm = G.extract(d.prm, [DOG_ROOT])
    root = cm[DOG_ROOT]
    sk = CH.skeleton(ex, root)
    if not sk:
        raise ValueError('F07 model %d has no skeleton' % DOG_ROOT)
    names = CH.bone_names(ex, sk)
    if CH.FREE_NAME not in names:
        raise ValueError('the dog skeleton has no %s' % CH.FREE_NAME)
    number = CH.anm_number(anm.bones)
    lack = [s for s in names if s.lower() not in number]
    if lack:
        # we never edit the .ANM (header sizes differ between games): a bone the level's table lacks stops the build
        raise ValueError('bones missing in DM02\'s .ANM bone table: %s' % lack)
    ids = CH.level_ids(prm_s)
    renamed = CH.reid(ex, sk, ids)
    import kl_impact
    kl_impact.sync_bone_ids(ex, [sk])
    moved = CH.rebind(ex, sk, number)
    cols = [c.name for c in anm.cols]
    if not any(str(c).lower().endswith('dog') for c in cols):
        raise ValueError('DM02 .ANM has no Dog collection: %s' % cols)
    ex2, cm2 = G.extract(ex, [root])                 # drops what the edits orphaned
    rep = dict(bones=len(names), bone_ids_changed=renamed, anm_numbers_changed=moved[0] if isinstance(moved, tuple) else moved,
               chunks=len(ex2.chunks) - 1, anm_collections=len(cols))
    log('  dog model: %d bones, %d bone ids renumbered, %s animation numbers rebound to the level .ANM, %d chunks' % (
        len(names), renamed, rep['anm_numbers_changed'], rep['chunks']))
    return ex2, cm2[root], prm_s, anm, rep


# ------------------------------------------------------------------ build
def build(src, dst, force=False, log=print):
    data = open(src, 'rb').read()
    h = md5(data)
    if h != SRC_MD5 and not force:
        raise SystemExit('refusing: %s md5 %s is not the pinned %s (use --force)' % (src, h, SRC_MD5))
    if os.path.abspath(src) == os.path.abspath(dst):
        raise SystemExit('the output is the input')
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + SQUAD_TOP):
        shutil.copyfile(src, dst)
        log('%s already holds %s: copied unchanged' % (src, SQUAD_TOP))
        return None
    d = IG.Donor.get(DONOR)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    a0, s0 = AS.census(sc)
    if a0 + 1 > ENGINE_ACTORS or s0 + 1 > ENGINE_SQUADS:
        raise ValueError('budget: %d / %d would pass the cap %d / %d' % (a0 + 1, s0 + 1, ENGINE_ACTORS, ENGINE_SQUADS))
    nav = KB.Nav(A.nav, links=True)
    P = plan(B, nav, log)
    big0 = {e: len(B[e]) for e in KB.BIG}
    # ---- nodes
    M, tops, act = make_nodes(B, d, P)
    # ---- the model: skeleton bound to this level, then the graft of kl_dm02_mall_1025.cars
    ex, root, pS, anm, mrep = graft_model(B, d, log)
    matS, texS = T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    kinds, args = G.walk(ex, [root])
    slots = {ex.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(d.mat, slots))
    for i, k in kinds.items():
        for off_, typ, _k in G.fields(ex, i, k, args.get(i, 0)):
            if typ in 'tT' and ex.u32(i, off_):
                want.add(ex.u32(i, off_) % G.SLOTS['dd'])
    tex, tmap = T.merge_tex(texS, d.tex, want)
    mat, mmap = T.merge_mat(matS, d.mat, slots, tmap)
    pS, cmap = G.append(pS, ex, [root], mmap, None, tmap)
    lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
    if lack:
        raise ValueError('shaders missing in the map .fxc: %s' % lack)
    log('  .prm: %d chunks in the closure, %d materials, %d textures; shaders missing: none' % (len(kinds), len(slots), len(want)))
    act.model = cmap[root]
    M.set(act, None, {'ZGEOM[4]': act.model})
    # ---- the join
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'dog')
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    start = R + CLOCK + BS + 'T_Start'
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [start]))
    # ---- sounds: the actor's integers are F07 .SND offsets; keep a root only when DM02's bank holds an object of the SAME NAME at the same offset, else re-point by name (else 0)
    import kl_snd
    mine = kl_snd.Snd('dd', B.files[B.ext['.SND']])
    byname = {}
    for o in mine.kind:
        try:
            byname.setdefault(mine.name(o), o)
        except Exception:
            pass
    dsnd = kl_snd.bank(DONOR)
    ks = [k for k in range(1, len(Jn.nodes)) if (R + SQUAD_TOP).lower() in Jn.path[k].lower()]
    roots = kl_snd.roots(Jn, ks)
    omap, table = {}, []
    for r in sorted(roots):
        nm = dsnd.name(r) if r in dsnd.kind else None
        tgt = byname.get(nm, 0)
        if tgt != r:
            omap[r] = tgt
        table.append((r, (nm or b'?').decode('latin1'), tgt))
    if omap:
        kl_snd.rewrite(Jn, ks, omap)
    log('  sound roots %s; re-pointed %d' % (table, len(omap)))
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5], sorted(set(dang1[1]) - set(dang0[1]))[:5]))
    for p in [start] + [R + SQUAD_TOP + BS + x for x in ROUTS]:
        if len(Jn.resolve(p)) != 1:
            raise ValueError('%s does not resolve' % p)
    prp = Jn.p.serialize()
    back_prp = Prp(prp)
    if back_prp.serialize() != prp or len(back_prp.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    fa, fs = AS.census(Jn)
    if fa != a0 + 1 or fs != s0 + 1 or fa > ENGINE_ACTORS or fs > ENGINE_SQUADS:
        raise ValueError('census %d / %d -> %d / %d' % (a0, s0, fa, fs))
    log('  census %d / %d -> %d / %d (cap %d / %d)' % (a0, s0, fa, fs, ENGINE_ACTORS, ENGINE_SQUADS))
    # ---- entities (.gms / .buf)
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    for t in tops:
        nxt = C2._write_ent(A, t, None, nxt, made)
    A.ref_slots = max(A.ref_slots, nxt)
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    allents = list(A.entities())
    if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, set()), O.remap_ids(rmi, ids, set()), O.remap_ids(rmc, ids, set())
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for t in tops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    if r3 is None:
        raise ValueError('the root has no tree 3')
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
    octn.rooms[0][3].check()
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    # ---- .oct record of the dog's root, .prm re-point (the cars' sequence)
    unref = lambda v: (v & ~1) - 4
    rec_d = {v: n for n, v in enumerate(d.oct.record_refs())}
    keep = sorted({rec_d[ex.u32(i, 0x1c)] for i, k in kinds.items() if k == 'root' and ex.u32(i, 0x1c)})
    for n in keep:
        if d.oct.records[n].tree.items:
            raise ValueError('the dog root\'s .oct record lists %d triangle batches (not handled)' % len(d.oct.records[n].tree.items))
    octk, _same, refs_b = O.append_records(octn, d.oct, cmap, keep)
    refs_a = dict(zip(octx.record_refs(), octk.record_refs()))
    pcur = G.read(B['.prm'], 'dd')
    pnew, cmap2 = G.append(pcur, ex, [root], mmap, {unref(a): unref(b) for a, b in refs_b.items()}, tmap)
    if cmap2 != cmap:
        raise ValueError('kl_prmgraph.append numbers chunks differently on the second run')
    repointed = 0
    for i in range(1, len(pcur.chunks)):
        c = pnew.chunks[i]
        if len(c) == 64 and c[:4] == b'\0\1\7\0' and struct.unpack_from('<I', c, 0x1c)[0] in refs_a:
            v = refs_a[struct.unpack_from('<I', c, 0x1c)[0]]
            if v != struct.unpack_from('<I', c, 0x1c)[0]:
                pnew.chunks[i] = c[:0x1c] + struct.pack('<I', v) + c[0x20:]
                repointed += 1
    prm_bytes = G.write(pnew)
    import kl_impact
    lim = kl_impact.chunk_limit(pnew)
    if lim:
        raise ValueError(lim)
    mat.refs = T.material_refs(prm_bytes, mat.ninst)
    if G.write(G.read(prm_bytes, 'dd')) != prm_bytes:
        raise ValueError('.prm does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octk.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']] = prm_bytes, T.write_mat(mat), T.write_tex(tex)
    if T.material_refs(prm_bytes, mat.ninst) != T.read_mat(new[B.ext['.MAT']]).refs:
        raise ValueError('.MAT ref counts')
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    if '.ANM' in changed:
        raise ValueError('the .ANM changed (it must not)')
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    kl_graft.write_zip(dst, [(nm, new[nm]) for nm in B.order])
    out = md5f(dst)
    log('written %s md5 %s: %d entities added, %d slot ids renumbered, %d .prm roots re-pointed, members changed: %s' % (
        dst, out, len(order), moved, repointed, ' '.join(changed)))
    return collections.OrderedDict(
        source_md5=h, out_md5=out, census=[a0, s0, fa, fs], entities_added=len(order), slot_ids_moved=moved, prm_roots_repointed=repointed,
        members_changed=changed, prm_chunks=(len(pcur.chunks) - 1, len(pnew.chunks) - 1), prm_bytes=(len(B['.prm']), len(prm_bytes)),
        tex_bytes=(len(B['.TEX']), len(new[B.ext['.TEX']])), model=mrep, sound=[[hex(r), n, hex(t)] for r, n, t in table],
        park=[round(v) for v in P['park'][:3]], posts=[[round(v) for v in p[:3]] for p in P['posts']], mesh_walk_cm=P['walk'],
        release_s=DOG_AT, start=start, large_blocks_unchanged=big0 == {e: len(new[B.ext[e]]) for e in KB.BIG})


# ------------------------------------------------------------------ check
def check(zp, log=print):
    B = KB.Built(zp)
    sc = B.sc
    bad = 0

    def say(ok, msg):
        nonlocal bad
        bad += (not ok)
        log('%s %s' % ('ok  ' if ok else 'FAIL', msg))
    a, s = AS.census(sc)
    say(a <= ENGINE_ACTORS and s <= ENGINE_SQUADS, 'budget %d actors / %d squads (cap %d / %d)' % (a, s, ENGINE_ACTORS, ENGINE_SQUADS))
    top = sc.resolve(R + SQUAD_TOP)
    say(len(top) == 1, 'squad %s present' % SQUAD_TOP)
    nav = KB.Nav(B.scene.nav, links=True)
    st = KB.stations(B, nav)
    home = st['home']
    if top:
        t = top[0]
        men = [j for j in range(t, sc.end[t]) if sc.cls(j) == 'ZFFActor']
        say(len(men) == 1, '1 dog actor (%d)' % len(men))
        if men:
            m = men[0]
            pos = B.at(m)
            h = nav.at(pos[0], pos[1], pos[2], dy=60)
            say(h is not None and nav.part[h[0]] == home, 'the dog stands on the crew\'s mesh part at (%d,%d,%d)' % tuple(pos))
            say(all(math.hypot(pos[0] - x[0][0], pos[2] - x[0][2]) >= FAR_FROM_CREW for x in st['starts']), 'the dog is %d+ cm from every heister start (out of view)' % FAR_FROM_CREW)
            model = CH.person(sc, m)
            say(model[2].lower() == 'dog', 'animation set %r' % model[2])
            prm = G.read(B['.prm'], 'dd')
            anm = kl_anm.Anm(B['.ANM'], 'dd')
            probs = CH.check_bones(prm, anm.bones, roots=[model[0]])
            say(not probs, 'dog skeleton bound to the level .ANM, level-wide bone ids consistent (%s)' % probs[:2])
            try:
                CH.level_ids(prm)
                ok = True
            except ValueError as e:
                ok = False
                log(str(e))
            say(ok, 'level_ids over every skeleton of the level agree')
            import kl_snd
            mine = kl_snd.Snd('dd', B.files[B.ext['.SND']])
            roots = kl_snd.roots(sc, list(range(t, sc.end[t])))
            say(all(r in mine.kind for r in roots) and bool(roots), 'every sound reference of the dog chain (%s) names an object of this level .SND' % sorted(roots))
        say(sc.tids[sc.parent[men[0]]] == 0x100001 if men else False, 'the actor stands in a group under the squad top')
        routs = [j for j in range(t, sc.end[t]) if sc.names[j] in ROUTS]
        say(len(routs) == len(ROUTS), '%d Defend routs' % len(routs))
        posn = [j for j in range(t, sc.end[t]) if sc.names[j] == 'Pos#01']
        say(len(posn) == len(ROUTS) and all(nav.at(*B.at(j), dy=60) and nav.part[nav.at(*B.at(j), dy=60)[0]] == home for j in posn), 'the Defend posts are mesh cells of the main part')
        dead = []
        for j in range(t, sc.end[t]):
            for nm, body in sc.nodes[j]['ctrls']:
                for u in KB.units(body[1:-1]):
                    v = kl_fa.value(sc, u)
                    for x in (v if isinstance(v, list) else [v]):
                        if isinstance(x, str) and x.startswith(R) and not sc.resolve(x):
                            dead.append((sc.path[j][-40:], x[-50:]))
        say(not dead, 'every reference of the dog chain resolves (%s)' % dead[:3])
        sqv = [kl_fa.value(sc, u) for u in KB.units(sc.nodes[t]['ctrls'][0][1][1:-1])]
        say(sqv[3] == 0 and all(sqv[j] == [] for j in range(4, 19)), 'the squad is parked until a rout is named')
    mon = sc.resolve(KOW.MONITOR)[0]
    say(R + CLOCK + BS + 'T_Start' in KOW.values(sc, mon, 'AIMonitor')[KOW.START_LIST], 'AIMonitor round-start list names T_Start')
    tm = sc.resolve(R + CLOCK + BS + 'T_Start')
    say(len(tm) == 1, 'timer present')
    say(bool(sc.resolve(R + 'KL_Cars!')) or bool(sc.resolve(R + 'KL_Cars!Clock')), 'the mall pass (police cars) is still in the zip')
    return bad


# ------------------------------------------------------------------ INSTALL / UNDO (the gas installer, renamed)
def ps_text():
    s = GS.PS1
    s = s.replace('gas.json', 'dog.json').replace('.before-1025dm01bgas', TAG).replace('gas.ps1', 'dog.ps1')
    s = s.replace('Maps' + chr(92) + 'DM01B' + chr(92) + 'F03_Main.zip', 'Maps' + chr(92) + 'DM02' + chr(92) + 'F02_Main.zip').replace('renamed F03_Main.zip', 'renamed F02_Main.zip')
    first = s.index('\n')
    return ('# dog.ps1 - DM02 Late Night Opening, 2026-10-25 (tools/kl_dog_1025.py): ONE police dog released with the arriving SWAT (~32 s).\n'
            '#   Chained on the live DM02 zip a8216b38 (mall pass): `old` in dog.json is that md5; the install refuses any other.\n'
            '#   THE TOGGLE IS UNDO: dog.ps1 -Undo (UNDO dm02 dog.bat) puts the previous zip back byte for byte (backup ' + TAG + ').\n') + s[first + 1:]


BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dog.ps1" {arg}\r\npause\r\n'


def run_ps(d, game, undo=False, dry=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'dog.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    if dry:
        a.append('-DryRun')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(src, out, scratch=None, log=print):
    old = md5f(src)
    if old != SRC_MD5:
        raise SystemExit('input md5 %s is not the pinned %s' % (old, SRC_MD5))
    os.makedirs(out, exist_ok=True)
    z = os.path.join(out, FILE)
    rep = build(src, z, log=log)
    if rep is None:
        raise SystemExit('input already holds the pass')
    new = md5f(z)
    man = dict(m=MAP, f=FILE, old=old, new=new, tag=TAG, chain='live DM02 zip a8216b38 (mall pass)')
    with open(os.path.join(out, 'dog.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(out, 'dog.ps1'), 'w', newline='\r\n') as fh:
        fh.write(ps_text())
    for nm, arg in (('INSTALL dm02 dog.bat', ''), ('UNDO dm02 dog.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %s -> %s' % (out, old, new))
    if scratch:
        rehearse(src, out, man, scratch, log)
    return man


def rehearse(src, d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', MAP, FILE)
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(os.path.dirname(live))
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    shutil.copy2(src, live)
    t = run_ps(d, g, dry=True); log(t.strip()); assert 'would install' in t and md5f(live) == man['old'], t
    t = run_ps(d, g); log(t.strip()); assert 'installed' in t and md5f(live) == man['new'], t
    assert md5f(live + TAG) == man['old']
    assert 'already installed' in run_ps(d, g)
    t = run_ps(d, g, undo=True); log(t.strip())
    assert md5f(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
    assert 'already undone' in run_ps(d, g, undo=True)
    run_ps(d, g); assert md5f(live) == man['new']
    run_ps(d, g, undo=True); assert md5f(live) == man['old'] and not os.path.exists(live + TAG)
    with open(live, 'ab') as fh:
        fh.write(b'x')
    t = run_ps(d, g); log(t.strip()); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
    shutil.rmtree(g, ignore_errors=True)
    log('rehearsal ok (dry run, install, idempotent, undo byte-identical, undo twice, reinstall, wrong md5 refused)')


def main():
    a = sys.argv[1:]
    force = '--force' in a
    if force:
        a.remove('--force')
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) < 2 or a[0] not in ('build', 'check', 'stage'):
        print(__doc__)
        return 2
    if a[0] == 'check':
        return 1 if check(a[1]) else 0
    if a[0] == 'build':
        print(json.dumps(build(a[1], a[2], force), indent=1, default=str))
        return 0
    stage(a[1], a[2], opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
