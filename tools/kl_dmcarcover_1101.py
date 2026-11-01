r"""kl_dmcarcover_1101.py - DM01 / DM03 stage, 2026-11-01: PROBE for the host-only runtime cover ring around dynamic cars (re/dm_car_cover_1101.md).

PROBLEM. Online, the host's CFFCoverList has 8 cover points per ringed car that the client never builds (DM01: 347..354 around the Dynamic ram truck;
DM03: 32 = 4 cars x 8).  A soldier's cover point index travels by value, so the client indexes past its shorter list -> int3 at kl2.exe 0x6567e8 ...
(klhook AssertSoft steps over them; this stage tries to make the two lists equal at the source).

WHAT THE DATA SAYS (measured 2026-11-01, build\\carcover_1101 + the Q30 / Q33 coverdump logs, clustered here by position):
  ringed:      DM01 node 243 (ram truck, V_USA_RamTruck_A_Dynamic_00, TRUCK, [9]=1, no CoverBox child)
               DM03 nodes 6946, 7019 (PoliceCar_Reinforcement_02 / _01), 7106 (V_USA_Sedan_A_Dynamic_00), 7186 (Deliverycar_01): 4 clusters, 8 points each
  NOT ringed:  DM01 Bentley_01/02 (112, 168; NORMAL_CAR, [9]=0, on the main nav part), DM01 Cement_Truck (286; TRUCK, [9]=1, on the main nav part,
               driven by Civil\\VehicleMoveBehaviour like the ram truck), DM03 node 6874 and DM02 node 7280 (both off the nav mesh)
  No single stored field separates all of these (the cement truck matches the ram truck in type, [9], model class and nav).  So the writer's trigger
  is NOT established; this tool is a PROBE, not a proven fix.

WHAT IT CHANGES (prp only; .gms / .buf / .oct / .rmi / .rmc / every other member and every other node stay byte-identical, no entity moves):
  DM01  node ROOT\\CivilianCars!Truck\\V_USA_RamTruck_A_Dynamic_00\\Ground_01 (ZHavokCar):  [9] 1 -> 0  and  [1] TRUCK -> NORMAL_CAR
        i.e. the truck is given the two stored values the (unringed) Bentleys have.  GUESS: one of them is what makes the engine build the ring.
        Role: the truck keeps its model, position, spline drive (VehicleMoveBehaviour / TruckStartTimer), horn relays and VehicleEffects.  GUESS
        (unproven): NORMAL_CAR instead of TRUCK may change its handling / mass in the Havok sim, and [9] is an unnamed flag.  Nothing else changes.
  DM03  NOTHING by default.  The four ringed cars are the police reinforcement arrivals and the delivery car; making them static or retyping them
        would change the round, which the brief forbids.  `--dm03` opts in to [9] 1 -> 0 ONLY (type kept) on 6946, 7019, 7106, 7186: GUESS, untested,
        role risk = whatever [9] does for a driven car (if it is 'simulate'/'drive' the arrivals could stop; the bench must watch the SWAT cars arrive).

    python kl_dmcarcover_1101.py dm01 <in.zip> <out.zip>
    python kl_dmcarcover_1101.py dm03 <in.zip> <out.zip> [--dm03]
    python kl_dmcarcover_1101.py audit <in.zip>              read-only: every ZHavokCar's [1] / [9] and the plan for it
    python kl_dmcarcover_1101.py stage [<out root>] [--dm03]  the live zips -> <root>\DM01\F01_Main.zip + .bots.zip (and with --dm03 DM03_probe\F03_Main*.zip); reads the game folder only
"""
import collections, hashlib, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
from kl_prp import units, Prp

BS = chr(92)
R = 'ROOT' + BS
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
BASE = 11                      # ZHavokCar's own fields start after ZGEOM (6) + ZSTDOBJ (2) + ZLNKOBJ (3) units
TYPE_I, FLAG_I = 1, 9          # ZHavokCar[1] = enum (TRUCK / NORMAL_CAR / CHASING_CAR / VAN), [9] = an unnamed bool (1 on every ringed car)
# the plan: map -> [(path, {field index: (expected old, new)})]
PLAN = {
    'DM01': [(R + 'CivilianCars!Truck' + BS + 'V_USA_RamTruck_A_Dynamic_00' + BS + 'Ground_01', {TYPE_I: ('TRUCK', 'NORMAL_CAR'), FLAG_I: (1, 0)})],
    'DM03': [],
}
DM03_OPT = [(R + p + BS + 'Ground_01', {FLAG_I: (1, 0)}) for p in (
    'AI_Enemies!ArrivingCops_Squad_02' + BS + 'PoliceCar_Reinforcement_02',
    'AI_Enemies!ArrivingCops_Squad_01' + BS + 'PoliceCar_Reinforcement_01',
    'AI_Enemies!ParkingLotSWAT_01' + BS + 'V_USA_Sedan_A_Dynamic_00',
    'DeliveryCars!Deliverycar_01' + BS + 'Deliverycar_01')]
SLOT = {'DM01': 'F01', 'DM03': 'F03'}
LIVE_PIN = {                   # live md5s the research ran on (2026-11-01)
    'DM01': {'F01_Main.zip': 'fe9d5751dc0204fa8eb79541fb434e8a', 'F01_Main.bots.zip': '2fb07d3b60d59190d33c5268cf91a15d'},
    'DM03': {'F03_Main.zip': 'c0fb50f7e2ab3d8066966f0ae898769c', 'F03_Main.bots.zip': '30d7f1797e38c115e9870eaf8755933c'}}


def md5(b):
    return hashlib.md5(b).hexdigest()


def prp_name(names):
    return [n for n in names if n.lower().endswith('_main.prp')][0]


def car_units(sc, k):
    return [list(u) for u in units(sc.nodes[k]['props'][1:-1])]


def apply_edits(sc, us, edits, where=''):
    """Edit the field units `us` of a ZHavokCar in place.  edits = {index: (expected old value, new value)}; the old value is checked, a value that
    already equals the new one is left alone (idempotent).  -> the list of (index, old, new) really changed."""
    import kl_fa_author as AU
    done = []
    for i, (old, new) in sorted(edits.items()):
        cur = kl_fa.value(sc, us[BASE + i])
        if cur == new:
            continue
        if cur != old:
            raise ValueError('%s: ZHavokCar[%d] is %r, expected %r' % (where, i, cur, old))
        AU.setv(sc, us, BASE + i, new)
        done.append((i, cur, new))
    return done


def edit_scene(sc, plan, log=print):
    out = []
    for path, edits in plan:
        hit = sc.resolve(path)
        if len(hit) != 1:
            raise ValueError('%s: %d nodes' % (path, len(hit)))
        k = hit[0]
        if sc.cls(k) != 'ZHavokCar':
            raise ValueError('%s is a %s, not a ZHavokCar' % (path, sc.cls(k)))
        us = car_units(sc, k)
        done = apply_edits(sc, us, edits, path)
        n = sc.nodes[k]
        n['props'] = [n['props'][0]] + [t for u in us for t in u] + [n['props'][-1]]
        out.append((path, done))
        log('  %s: %s' % (path, '; '.join('[%d] %r -> %r' % d for d in done) or 'already as wanted'))
    return sc.p.serialize(), out


def patch_zip(src, dst, repl):
    """src with the members in `repl` {name: bytes} replaced and every other member copied unchanged (bytes, compression, stamp, order)."""
    n = 0
    with zipfile.ZipFile(src) as zi, zipfile.ZipFile(dst, 'w', allowZip64=True) as zo:
        for info in zi.infolist():
            i2 = zipfile.ZipInfo(info.filename, info.date_time)
            i2.compress_type, i2.external_attr, i2.create_system = info.compress_type, info.external_attr, info.create_system
            i2.comment = info.comment
            if info.filename in repl:
                zo.writestr(i2, repl[info.filename], compress_type=info.compress_type)
                n += 1
            else:
                with zi.open(info) as fi, zo.open(i2, 'w', force_zip64=info.file_size > 0x7fffffff) as fo:
                    while True:
                        c = fi.read(1 << 20)
                        if not c:
                            break
                        fo.write(c)
    if n != len(repl):
        raise ValueError('%s: %d of %d members to replace were found' % (src, n, len(repl)))


def plan_for(mp, dm03=False):
    if mp not in PLAN:
        raise ValueError('map %s: dm01 or dm03' % mp)
    return PLAN[mp] + (DM03_OPT if (mp == 'DM03' and dm03) else [])


def build(mp, src, dst, dm03=False, log=print):
    """One zip.  -> dict(md5_in, md5_out, changes, members_changed)."""
    plan = plan_for(mp, dm03)
    data = open(src, 'rb').read()
    sc, _s, _l = kl_fa.load(src)
    with zipfile.ZipFile(src) as z:
        pn = prp_name(z.namelist())
    if not plan:
        log('  %s: nothing planned (see the docstring): copied unchanged' % mp)
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        open(dst, 'wb').write(data)
        return collections.OrderedDict(md5_in=md5(data), md5_out=md5(data), changes=[], members_changed=[])
    prp, changes = edit_scene(sc, plan, log)
    if Prp(prp).serialize() != prp:
        raise ValueError('the new .prp does not round-trip')
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    patch_zip(src, dst, {pn: prp})
    return collections.OrderedDict(md5_in=md5(data), md5_out=md5(open(dst, 'rb').read()), changes=changes, members_changed=[pn])


def audit(src, log=print):
    sc, _s, _l = kl_fa.load(src)
    want = {p for p, _e in PLAN['DM01'] + DM03_OPT}
    for k in range(len(sc.names)):
        if sc.cls(k) == 'ZHavokCar':
            us = car_units(sc, k)
            log('%6d %-90s [1]=%-12s [9]=%s%s' % (k, sc.path[k], kl_fa.value(sc, us[BASE + TYPE_I]), kl_fa.value(sc, us[BASE + FLAG_I]),
                                                  '  <- planned (dm03 opt-in)' if sc.path[k] in {p for p, _e in DM03_OPT} else ('  <- planned' if sc.path[k] in want else '')))


def diff_scenes(a, b):
    """Node paths whose props / controllers differ between two zips' .prp, as [(path, 'props'|'ctrls')]; None when the node lists differ."""
    sa, _x, _y = kl_fa.load(a)
    sb, _x, _y = kl_fa.load(b)
    if len(sa.nodes) != len(sb.nodes) or sa.path != sb.path or sa.p.keys[:len(sa.p.keys)] != sb.p.keys[:len(sa.p.keys)]:
        return None
    d = []
    for k in range(len(sa.nodes)):
        na, nb = sa.nodes[k], sb.nodes[k]
        if na['props'] != nb['props']:
            d.append((sa.path[k], 'props'))
        if list(na['ctrls']) != list(nb['ctrls']):
            d.append((sa.path[k], 'ctrls'))
    return d


def members_differing(a, b):
    with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
        if za.namelist() != zb.namelist():
            return None
        return [n for n in za.namelist() if za.read(n) != zb.read(n)]


def work_root():
    import kl_port_check
    return os.path.join(kl_port_check.workdir(), 'build', 'carcover_1101')


def stage(root=None, dm03=False, log=print):
    root = root or work_root()
    rep = collections.OrderedDict()
    for mp, pins in LIVE_PIN.items():
        for zn, pin in pins.items():
            src = os.path.join(GAME, 'KLExpansion', 'Maps', mp, zn)
            if not os.path.isfile(src):
                log('%s %s: absent, skipped' % (mp, zn))
                continue
            got = md5(open(src, 'rb').read())
            if got != pin:
                log('%s %s: live md5 %s is not the researched %s (the edit checks node values itself, so it goes on)' % (mp, zn, got, pin))
            if mp == 'DM03' and not dm03:
                log('%s %s: nothing planned without --dm03: not staged' % (mp, zn))
                continue
            dst = os.path.join(root, 'DM03_probe' if mp == 'DM03' else mp, zn)
            log('%s %s' % (mp, zn))
            rep['%s/%s' % (mp, zn)] = build(mp, src, dst, dm03, log)
    return rep


def main(argv):
    flags = [a for a in argv if a.startswith('--')]
    a = [x for x in argv if not x.startswith('--')]
    if len(a) == 2 and a[0] == 'audit':
        audit(a[1])
        return 0
    if len(a) >= 1 and a[0] == 'stage':
        rep = stage(a[1] if len(a) > 1 else None, '--dm03' in flags)
        for k, v in rep.items():
            print('%s  in %s  out %s  %s' % (k, v['md5_in'], v['md5_out'], 'changed' if v['changes'] else 'unchanged'))
        return 0
    if len(a) == 3 and a[0] in ('dm01', 'dm03'):
        r = build(a[0].upper(), a[1], a[2], '--dm03' in flags)
        print('md5 in %s out %s members %s' % (r['md5_in'], r['md5_out'], r['members_changed']))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
