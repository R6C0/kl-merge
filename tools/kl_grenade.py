#!/usr/bin/env python3
"""
Grenades for a STOCK Dog Days Fragile Alliance map (owner item 19, 2026-10-17). Spec and findings: re/grenades.md.
Offline: reads a built overlay folder (tools/kl_stock_mod.py build + gunsnd), writes a new one; touches no game file.

    python kl_grenade.py build <overlay folder with F0n_Main.zip> <out folder> [--n=10]
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
WHY NO NEW ENTITIES (stage B of re/grenades.md as written grafts Dead Men's Projectile\\Grenade_* groups): adding an entity to a
stock level moves every slot id after it, and the .oct room trees, .rmi / .rmc and the list pool are keyed by slot id
(CLAUDE.md, TWO ID SPACES). Controllers and field values live in the .prp only, so reusing an existing projectile node needs
none of that. The cost: the grenade has no model of its own (the flare's glow) and the Frag shares the flare round's node.
"""
import copy, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_arms, kl_fa, kl_graft
import kl_prpjoin as J
from kl_prp import units

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


def build(src, dst, n_actors=10, log=print):
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


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = {x.split('=')[0]: (x.split('=') + [''])[1] for x in sys.argv[1:] if x.startswith('--')}
    if a[:1] == ['build'] and len(a) == 3:
        out, rep = build(a[1], a[2], int(opt.get('--n', 10) or 10))
        print('flare controllers now:')
        for n, v in rep['flare']:
            print('  ', n, v)
        print('actors with a frag grenade (%d):' % len(rep['actors']))
        for s, p in rep['actors']:
            print('  ', s, p.rsplit('\\', 2)[-2])
        print('RESULT: PASS')
    elif a[:1] == ['check'] and len(a) == 2:
        sc = kl_fa.load(a[1])[0]
        for k, v in chain(sc).items():
            print(k, v)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
