#!/usr/bin/env python3
"""
Grenades for a STOCK Dog Days Fragile Alliance map (owner item 19, 2026-10-17). Spec and findings: re/grenades.md.
Offline: reads a built overlay folder (tools/kl_stock_mod.py build + gunsnd), writes a new one; touches no game file.

    python kl_grenade.py build <overlay folder with F0n_Main.zip> <out folder> [--n=10] [--no-route] [--squads=3]
    python kl_grenade.py check <F0n_Main.zip>                 what the level's grenade chain looks like (read only)

WHAT IT CHANGES (the .prp member only; the .gms / .buf / .oct / .prm / .SND / .ANM are byte for byte the input's)
  1 Ammo\\Grenade_Fragmentation: its projectile slot (empty in every Dog Days level; the Ammo -> Projectile reference is how
    RPG_7V reaches Rocket_RPG7) now names Projectile\\Projectiles_01\\Rocket_Flare.
  2 Rocket_Flare (the HK69 flare round, used by no actor of a Fragile Alliance level) becomes the frag grenade: its
    FFHavokProjectileBallistic [0, 10.0, 1, <snd>, 0, 0, eGRENADE_SMOKE] gets fuse 3.3 and eGRENADE_FRAG (Dead Men's Frag
    values), and it gains an Explode and a ShakeCamera controller (Dead Men's Frag values through the pairing of
    re/pairings.md, the effect / sound of Dog Days' own RPG round as stand-ins). Its red flare emitters stay as the visible
    glowing trail.
  3 N police / SWAT actors (spread over squads, a hash of the seed and the scene path: the same map gives the same build)
    get Weapon\\Grenade_Fragmentation in their first grenade field (ZFFActor[4]).
  4 (default on, --no-route skips) a THROW STEP for 2 to 3 of those squads (add_route; re/grenades.md section 12). No tactic of Dog
    Days starts a throw by itself; the only start is a ZGrenadeAttackBehaviourRout route step [actor ref, x, y, z, NEXT, b, b].
    Per chosen carrier a new ZGROUP carries one such controller (all under one new top group, so 1 + N entities are added);
    the squad's RunToCoverBehaviourRout NEXT list (the step that stock triggers start) names it, and its own NEXT list is what
    the RunToCover's NEXT held before. The new entities go through kl_scene (slot ids renumbered, .oct / .rmi / .rmc remapped),
    the same procedure as kl_fa_civs.add (which is copied in outline, not edited or imported).
  4 (default on, --no-route skips) a THROW STEP for 2 to 3 of those squads (add_route; re/grenades.md section 12). No tactic of Dog
    Days starts a throw by itself; the only start is a ZGrenadeAttackBehaviourRout route step [actor ref, x, y, z, NEXT, b, b].
    Per chosen carrier one new ZGROUP holds one such controller (all under one new top group: 1 + N entities); the squad's
    RunToCoverBehaviourRout NEXT list (the step a trigger starts) names it, and its own NEXT list is what the RunToCover's NEXT
    held before. The new entities go through kl_scene (slot ids renumbered, .oct / .rmi / .rmc remapped), the procedure of
    kl_fa_civs.add (followed in outline; that module is neither edited nor imported).
WHY NO NEW ENTITIES (steps 1 to 3 only) (for steps 1 to 3 only) (stage B of re/grenades.md as written grafts Dead Men's Projectile\\Grenade_* groups): adding an entity to a
stock level moves every slot id after it, and the .oct room trees, .rmi / .rmc and the list pool are keyed by slot id
(CLAUDE.md, TWO ID SPACES). Controllers and field values live in the .prp only, so reusing an existing projectile node needs
none of that. The cost: the grenade has no model of its own (the flare's glow) and the Frag shares the flare round's node.
"""
import collections, copy, math, os, shutil, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_arms, kl_fa, kl_gms, kl_graft, kl_scene
import kl_fa_bots as F
import kl_octree as O
import kl_prpjoin as J
from kl_prp import units, Prp

SEED = 2026
PROJ = 'Projectile\\Projectiles_01\\'
FLARE = PROJ + 'Rocket_Flare'
RPG = PROJ + 'Rocket_RPG7'
FRAG_AMMO = 'Ammo\\Grenade_Fragmentation'
FRAG_WEAPON = 'Grenade_Fragmentation'
# Dead Men's Grenade_Fragmentation, read from M01_FA_A (re/grenades.md section 2):
#   Explode [550.0, 200.0, 1000.0, 350.0, 0, 'EXPLODE_Explode_Impact', fx, 0.0, 0, 0, snd, 80.0, 1, 0, 0]
#   ShakeCamera [0.5, 'EXPLODE_Explode_Impact', 0, 1500.0]    FFHavokProjectileBallistic [0, 3.3, 1, snd, 0, 0, 'eGRENADE_FRAG']
# Dog Days' Explode has 18 fields: DD0<-DM0, DD1<-DM1, DD3<-DM2, DD4<-DM3, DD6..16<-DM4..14, DD2 / DD5 / DD17 new
# (re/pairings.md: Rocket_RPG7 500,150,1000,200 -> 500,150,200,1000,200,1; DD2 = 200, DD5 = 1, DD17 = 0 in every Dog Days rocket).
DM_EXPLODE = [550.0, 200.0, 1000.0, 350.0]
FUSE = 3.3
SHAKE = 1500.0


def short(sc, k):
    return sc.path[k].split('equipment.zip\\', 1)[-1]


def find(sc, rel):
    hit = [k for k in range(1, len(sc.nodes)) if short(sc, k) == rel]
    if len(hit) != 1:
        raise ValueError('%s: %d nodes' % (rel, len(hit)))
    return hit[0]


def ctrl_index(sc, k, name):
    return next((i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == name), None)


def _fl(x):
    return (0x0a, struct.pack('<f', x))


def chain(sc):
    """-> dict describing the grenade chain of a level (read only)."""
    out = {}
    a = find(sc, FRAG_AMMO)
    v = kl_fa.node_values(sc, a)
    j = v.index('LETHAL') - 2
    out['ammo_node'], out['ammo_projectile_field'], out['ammo_projectile'] = a, j, v[j]
    out['weapon'] = [short(sc, k) for k in range(1, len(sc.nodes)) if short(sc, k).startswith('Weapon\\Grenade_') and sc.cls(k) == 'ZFFItemTemplateWeapon']
    f = find(sc, FLARE)
    out['flare_ctrls'] = [(sc.p.key(n), [kl_fa.value(sc, u) for u in units(b[1:-1])]) for n, b in sc.nodes[f]['ctrls']]
    out['flare_children'] = sum(1 for k in range(f + 1, sc.end[f]) if sc.parent[k] == f) if hasattr(sc, 'end') else None
    out['flare_users'] = [short(sc, k) for k in range(1, len(sc.nodes))
                          if any(isinstance(x, str) and x.endswith('Rocket_Flare') for x in kl_fa.node_values(sc, k))]
    return out


def patch_level(sc, n_actors=10, seed=SEED, log=print):
    """Edit the scene in place. -> report dict."""
    rep = {}
    eq = kl_arms.equipment(sc)
    root = next(i['path'].rsplit('\\', 1)[0] + '\\' for i in eq.values())
    # 1 ammo -> projectile
    a = find(sc, FRAG_AMMO)
    v = kl_fa.node_values(sc, a)
    j = v.index('LETHAL') - 2
    if v[j] != '':
        raise ValueError('the Frag ammo already names a projectile: %r' % v[j])
    equip = sc.path[a].rsplit('Ammo\\', 1)[0]
    flare_path = equip + FLARE

    def ammo(us):
        us[j] = [kl_fa._str(sc, flare_path)]
    kl_fa.edit(sc, a, None, ammo)
    rep['ammo_field'] = j
    # 2 the flare round becomes the grenade
    f = find(sc, FLARE)
    bi = ctrl_index(sc, f, 'FFHavokProjectileBallistic')
    if bi is None or ctrl_index(sc, f, 'Explode') is not None:
        raise ValueError('Rocket_Flare is not the stock flare round')

    def ball(us):
        if len(us) != 7 or us[1][0][0] != 0x0a:
            raise ValueError('FFHavokProjectileBallistic is not in the Dog Days layout')
        us[1] = [_fl(FUSE)]
        us[6] = [(us[6][0][0], struct.pack('<I', sc.p.key_index('eGRENADE_FRAG')))]
    kl_fa.edit(sc, f, bi, ball)
    r = find(sc, RPG)
    for name, make in (('Explode', None), ('ShakeCamera', None)):
        ri = ctrl_index(sc, r, name)
        sc.nodes[f]['ctrls'].append(copy.deepcopy(sc.nodes[r]['ctrls'][ri]))
    ei, si = len(sc.nodes[f]['ctrls']) - 2, len(sc.nodes[f]['ctrls']) - 1

    def explode(us):
        if len(us) != 18:
            raise ValueError('Explode is not the 18-field Dog Days layout (%d)' % len(us))
        for i, x in ((0, DM_EXPLODE[0]), (1, DM_EXPLODE[1]), (3, DM_EXPLODE[2]), (4, DM_EXPLODE[3]), (13, 80.0)):
            if us[i][0][0] != 0x0a:
                raise ValueError('Explode field %d is not a float' % i)
            us[i] = [_fl(x)]
        # DM12 = 1, DM13 = 0, DM14 = 0 -> DD14, DD15, DD16 (the rocket has 0, 0, 1: 'explode on impact' is GUESSED to be DD16)
        if us[14][0][0] != us[16][0][0]:
            raise ValueError('Explode fields 14 / 16 differ in kind')
        us[14], us[16] = us[16], us[14]
    kl_fa.edit(sc, f, ei, explode)

    def shake(us):
        if us[3][0][0] != 0x0a:
            raise ValueError('ShakeCamera field 3 is not a float')
        us[3] = [_fl(SHAKE)]
    kl_fa.edit(sc, f, si, shake)
    rep['flare'] = [(sc.p.key(n), [kl_fa.value(sc, u) for u in units(b[1:-1])]) for n, b in sc.nodes[f]['ctrls']]
    # 3 carriers
    fl = kl_arms.fields()
    pool = []
    for k, squad, w, w2, g1, g2, aset in kl_arms.carriers(sc):
        if aset in ('Police', 'Swat_02') and w and not g1 and not g2 and 'Heister' not in squad:
            pool.append((k, squad))
    by = {}
    for k, squad in sorted(pool, key=lambda t: kl_arms._rank(seed, sc.path[t[0]])):
        by.setdefault(squad, []).append(k)
    chosen, squads = [], sorted(by)
    i = 0
    while len(chosen) < n_actors and any(by.values()):             # round robin over the squads: spread, not one squad
        s = squads[i % len(squads)]
        i += 1
        if by[s]:
            chosen.append((s, by[s].pop(0)))
    gpath = root + FRAG_WEAPON
    if FRAG_WEAPON.lower() not in eq:
        raise ValueError('the level has no Weapon\\' + FRAG_WEAPON)
    for s, k in chosen:
        def fn(us, p=gpath):
            us[fl[2]] = [kl_fa._str(sc, p)]
        kl_fa.edit(sc, k, None, fn)
    rep['actors'] = [(s, sc.path[k]) for s, k in chosen]
    return rep


# ------------------------------------------------------------------ step 4: the throw steps (route nodes)
STEP = 'GrenadeAttackBehaviourRout'
STEPS_TOP = 'AI_Players!GrenadeSteps'
MIN_DIST = 1500.0          # a carrier nearer than this to the target would be asked to throw at his own feet
# GUESS: the two booleans. Every other behaviour rout in Dog Days ends [... 1, 0] (RunToCover [NEXT, 1, 0], Defend 2 / 3 = 1, 0), and
# no stock object of this class exists (0 of 21 levels, 0 of Dead Men's 20), so there is no real value to copy.
BOOLS = (1, 0)


def loot_centre(B):
    """-> (x, y, z): the mean place of the level's NORMAL loot stacks (kl_fa_bots.money_objects), the point the heisters pass."""
    pts = [o['at'] for o in F.money_objects(B) if o['type'] == 'NORMAL']
    if not pts:
        raise ValueError('the level has no loot object: pass the throw target with --target=x,y,z')
    return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))


def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def pick_steps(B, carriers, target, n):
    """The carriers (ZFFActor node paths) whose squad has ONE RunToCoverBehaviourRout that something starts (a trigger or a
    cut-scene names it), one per squad, not nearer than MIN_DIST to the target, nearest first. -> [dict]."""
    sc, hit, started = B.sc, [], set()
    for k in range(1, len(sc.nodes)):
        for nm, body in sc.nodes[k]['ctrls']:
            for u in units(body[1:-1]):
                for s in _strings(kl_fa.value(sc, u)):
                    if '\\' in s:
                        started.update(sc.resolve(s))
    seen = set()
    for cpath in carriers:
        k = next(j for j in range(1, len(sc.nodes)) if sc.path[j] == cpath)
        group = sc.parent[k]
        squad = sc.parent[group]
        if squad in seen or not kl_fa.has(sc, squad, 'ZSquadScript'):
            continue
        rtc = [j for j in range(squad + 1, sc.end[squad]) if sc.parent[j] == squad and kl_fa.has(sc, j, 'RunToCoverBehaviourRout')]
        if len(rtc) != 1 or rtc[0] not in started:
            continue
        p = B.at(k)
        d = math.hypot(p[0] - target[0], p[2] - target[2])
        if d < MIN_DIST:
            continue
        i = next(i for i, (nm, _b) in enumerate(sc.nodes[rtc[0]]['ctrls']) if sc.p.key(nm) == 'RunToCoverBehaviourRout')
        old = kl_fa.value(sc, list(units(sc.nodes[rtc[0]]['ctrls'][i][1][1:-1]))[0])
        seen.add(squad)
        hit.append(dict(squad=sc.path[squad], rtc=rtc[0], rtc_ctrl=i, old_next=list(old or []), actor=sc.path[group], carrier=cpath, dist=d))
    hit.sort(key=lambda h: h['dist'])
    return hit[:n]


def _step_tokens(M, actor, target, nxt):
    keys = M.p
    return ([(0x02, b''), (0x0c, struct.pack('<I', keys.key_index(actor)))]
            + [(0x0a, struct.pack('<f', float(v))) for v in target]
            + [(0x04, struct.pack('<I', len(nxt)))] + [(0x0c, struct.pack('<I', keys.key_index(s))) for s in nxt]
            + [(0x06, bytes([BOOLS[0]])), (0x06, bytes([BOOLS[1]])), (0x7e, b'')])


def add_route(src, dst, carriers, slot, squads=3, target=None, log=print):
    """Write the throw steps into a copy of the finished level folder `src` in the new, empty folder `dst` -> report dict.
    carriers: ZFFActor node paths that hold the grenade. target: (x, y, z) or None = loot_centre()."""
    import kl_fa_bank
    B = F.Built(src, slot)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder) or (os.path.isdir(dst) and os.listdir(dst)):
        raise ValueError('%s is the source or not empty' % dst)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the level\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    target = tuple(target) if target else loot_centre(B)
    plan = pick_steps(B, carriers, target, squads)
    if not plan:
        raise ValueError('no squad with a started RunToCover step among the carriers')
    if sc.resolve(F.R_ + STEPS_TOP):
        raise ValueError('%s is already in the level' % STEPS_TOP)
    # ---- the new nodes (clones of the squad's own RunToCover group: a bare ZGROUP)
    M = F.Maker()
    tmpl = plan[0]['squad'] + '\\RunToCover'
    top = M.clone(slot, tmpl, STEPS_TOP)
    nm_op = top.ctrls[0][0][0]
    top.ctrls = []
    M.place(top, (0.0, 0.0, 0.0))
    for h in plan:
        name = 'Throw_' + h['squad'].split('Enemys!')[-1]
        n = top.add(M.clone(slot, tmpl, name))
        M.place(n, (0.0, 0.0, 0.0))
        h['name'] = name
        h['path'] = F.R_ + STEPS_TOP + '\\' + name
        n.ctrls = [((nm_op, struct.pack('<I', M.p.key_index(STEP))), _step_tokens(M, h['actor'], target, h['old_next']))]
    q, order = M.scene([top])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'grenade steps')
    # ---- the earlier step names the new one
    for h in plan:
        def fn(us, h=h):
            us[0] = kl_fa._refs(Jn, [h['path']])
        kl_fa.edit(Jn, h['rtc'], h['rtc_ctrl'], fn)
    bad = J.misfits(Jn)
    if bad:
        raise ValueError('objects that do not fit their class: %s' % [(Jn.path[k], w, y) for k, w, y in bad[:3]])
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    # ---- the .gms / .buf side
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        for k in n.kids:
            ent(k, e)
    ent(top, None)
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
    moved = sum(1 for a, b in ids.items() if a != b)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    # the .oct collision records are named by .prm chunks: they must not have moved (no room tree gained an entry)
    if octn.record_refs() != octx.record_refs():
        raise ValueError('the .oct records moved: the .prm would have to be re-pointed (not done here)')
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not os.path.exists(os.path.join(dst, f)):
            try:
                os.link(p, os.path.join(dst, f))
            except OSError:
                shutil.copyfile(p, os.path.join(dst, f))
    sealed = kl_fa_bank.seal(dst, log=lambda *_: None)
    rep = collections.OrderedDict(target=[round(v, 1) for v in target], steps=[{k: v for k, v in h.items() if k != 'rtc_ctrl'} for h in plan],
                                  entities_added=len(order), slot_ids_moved=moved, members_changed=changed, sealed=sealed, out=zp)
    log('route: %d throw steps at %s, %d entities added, %d slot ids renumbered; members changed: %s' % (len(plan), rep['target'], len(order), moved, changed))
    return rep


def _build_prp(src, dst, n_actors=10, log=print):
    zp = src if src.lower().endswith('.zip') else next(os.path.join(src, x) for x in sorted(os.listdir(src)) if x.lower().endswith('_main.zip'))
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the output folder is the input\'s own')
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    if data != files[ext['.prp']] or bad:
        raise ValueError('the input .prp does not re-serialise byte for byte (%d misfits)' % len(bad))
    rep = patch_level(sc, n_actors, log=log)
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    if bad:
        raise ValueError('%d objects do not fit after the patch: %s' % (len(bad), bad[:3]))
    files[ext['.prp']] = data
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(m, files[m]) for m in order])
    # everything beside the archive is linked (same bytes), the archive is the only new big file
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        d = os.path.join(dst, x)
        if os.path.isfile(q) and q != zp and not os.path.exists(d):
            try:
                os.link(q, d)
            except OSError:
                import shutil
                shutil.copyfile(q, d)
    with zipfile.ZipFile(zp) as a, zipfile.ZipFile(out) as b:
        diff = [n for n in a.namelist() if a.read(n) != b.read(n)]
        assert [n for n in a.namelist()] == b.namelist()
    rep['members_changed'] = diff
    log('wrote %s; members that differ from the input: %s' % (out, diff))
    return out, rep


def build(src, dst, n_actors=10, route=True, squads=3, target=None, log=print):
    """Steps 1 to 3 (the .prp edits), then step 4 (the throw steps) unless route is False. -> (zip path, report)."""
    if not route:
        return _build_prp(src, dst, n_actors, log)
    import tempfile
    stage = tempfile.mkdtemp(prefix='kl_grenade_stage_', dir=os.path.dirname(os.path.abspath(dst)) or None)
    try:
        zp1, rep = _build_prp(src, stage, n_actors, log)
        slot = os.path.basename(zp1).split('_Main')[0]
        carriers = [p for _s, p in rep['actors']]
        rr = add_route(stage, dst, carriers, slot, squads, target, log)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    rep['route'] = rr
    rep['members_changed'] = sorted(set(rep['members_changed']) | {os.path.basename(zp1).replace('_Main.zip', '_Main') + e for e in rr['members_changed']})
    return rr['out'], rep


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = {x.split('=')[0]: (x.split('=') + [''])[1] for x in sys.argv[1:] if x.startswith('--')}
    if a[:1] == ['build'] and len(a) == 3:
        tg = tuple(float(v) for v in opt['--target'].split(',')) if opt.get('--target') else None
        out, rep = build(a[1], a[2], int(opt.get('--n', 10) or 10), '--no-route' not in opt, int(opt.get('--squads', 3) or 3), tg)
        print('flare controllers now:')
        for n, v in rep['flare']:
            print('  ', n, v)
        print('actors with a frag grenade (%d):' % len(rep['actors']))
        for s, p in rep['actors']:
            print('  ', s, p.rsplit('\\', 2)[-2])
        for h in rep.get('route', {}).get('steps', []):
            print('throw step', h['path'], 'actor', h['actor'].rsplit('\\', 1)[-1], 'from', round(h['dist']), 'away; RunToCover NEXT was', h['old_next'])
        print('RESULT: PASS')
    elif a[:1] == ['check'] and len(a) == 2:
        sc = kl_fa.load(a[1])[0]
        for k, v in chain(sc).items():
            print(k, v)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
