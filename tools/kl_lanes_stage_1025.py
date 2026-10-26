"""kl_lanes_stage_1025.py - stage the van-lane + loot fixes of DM01 / DM02 / DM03 (2026-10-25, OFFLINE: reads zips, writes only under <root>/<MAP>/stage).

Per map: <root>/<MAP>/in/<zip> (+ the .ini / .WAV beside it, for the checkers) -> <root>/<MAP>/stage/{<zip>, install.py, build_report.json}.
Member-level patch: only the changed members of the live zip are replaced (.prp / .gms for loot, .buf for the DM01 car keys).
TOGGLE: this is map content; its on/off switch is install.py / install.py --undo (backup '<zip>.before-1025lanes').
usage (from tools/):  python kl_lanes_stage_1025.py stage <root> [DM01 DM02 DM03] [--rehearse <scratch>]
"""
import collections, json, os, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms
import kl_fa_bots as KB
import kl_loot_1025 as LO
import kl_lanes_1025 as LN
import kl_loot_scale_1026 as _LS

TAG, GAME, MAPS, md5, patch_zip = LN.TAG, LN.GAME, LN.MAPS, LN.md5, LN.patch_zip
TOTAL = 4000000                          # what this builder produces; 2026-10-26 the per-map totals (4M..8M, kl_loot_scale_1026.TARGETS) are applied AFTER it: both are accepted below

# DM02 drawer groups (ZGROUP, parent KL_Shops! at the identity) -> new place of the whole group (its 7 children sit at local 0, so the loot object 23626 etc. follows).
# Each spot is a counter / desk top of the mall, found by work/fl2*.py (HVK top of the prop - 13, like the stock tills: node 593 on a desk top 606):
#   Montre_Desk_01 (watch store, first floor), Desk_A_03 (jewellery back office, first floor), Counter_A (the diner's L-shaped counter, ground floor; x4).
# GUESS: ColiObj_weBox06 (the group's small collision box) moves with the group in the scene but its Havok body stays where the .HVK baked it (inside the shuttered shop);
#   the drawer at its new place has no collision of its own, a heister walks through a 25 cm cash drawer. Not testable offline.
DM02_MOVES = collections.OrderedDict([
    (23622, (-1767.0, 593.0, 2461.0)),     # 23626: watch store desk, 132 from the till 424 and 138 from pile 868
    (23630, (-1807.0, 77.0, -3379.0)),     # 23634: diner counter, west leg
    (23645, (2053.0, 571.0, 3141.0)),      # 23649: jewellery back office desk (Desk_A_03)
    (23653, (-1807.0, 77.0, -3639.0)),     # 23657: diner counter, west leg, 260 on
    (23668, (-1507.0, 77.0, -3799.0)),     # 23672: diner counter, south leg
    (23676, (-1307.0, 77.0, -3799.0))])    # 23680: diner counter, south leg end, 200 from the one before

# GUESS (all splits below): the owner's rule is only "total exactly 4,000,000, stacks reachable"; WHO carries the extra value is a design choice.
SPEC = collections.OrderedDict([
    # DM01: value only. The Senator / FBI agents are the guarded targets, case 1031 is the shop's stack; no prop is added or moved.
    ('DM01', dict(slot='F01', cars=True, strip=[], amounts={62: 2000000, 56: 800000, 187: 40000, 206: 200000, 208: 250000, 1031: 710000})),
    # DM02: the two reachable tills (23688, 23696) and till 1626 carry the +370,000. The six co-op drawers are NOT moved (report.txt gives why).
    # The six co-op KL_Shops drawers (150k each, shutters open only by a co-op action) are moved, group and all, onto tills / counters a player can reach
    # (spots below; Floors.stand spare 85..105 at reach 165, home-part nav 45..135; proof: re/ or the report of this run). CopCar01's route is shortened.
    ('DM02', dict(slot='F02', cars='dm02', strip=[], amounts={23688: 200000, 23696: 200000, 1626: 190000}, moves=DM02_MOVES)),
    # DM03: the ten Box_Money controllers (12445..12454: ZSTDOBJ stacked at one point (5224, 213, -11056), no model, 100,000 in all) are taken out;
    # the bank's four drawers 100k -> 250k, the eight garage piles +125k each, pile 799 +70k more.
    ('DM03', dict(slot='F03', cars=False, strip=list(range(12445, 12455)),
                  amounts={1774: 250000, 1781: 250000, 2106: 250000, 2113: 250000,
                           795: 375000, 796: 325000, 797: 375000, 798: 325000, 799: 545000, 800: 375000, 801: 325000, 802: 325000}))])


def strip_orphans(B, ks):
    """Take OnlineMoneyCtrl and the node's own take triggers (TriggerBox2 whose only target is the node) out of the ZSTDOBJ nodes ks. Refuses anything else."""
    sc, got = B.sc, []
    refs = KB.J.references(sc) if ks else []
    for k in ks:
        n = sc.nodes[k]
        if sc.cls(k) != 'ZSTDOBJ' or sc.end[k] != k + 1 or sc.parent[k] != 0:
            raise ValueError('%s: not a childless top-level ZSTDOBJ' % sc.path[k])
        if [1 for kk, _h, _f, _s, g in refs if g and k in g and kk != k]:
            raise ValueError('%s is named by another node' % sc.path[k])
        cv = [(sc.p.key(nm), [kl_fa.value(sc, u) for u in KB.units(body[1:-1])]) for nm, body in n['ctrls']]
        drop = set()
        for i, (cn, v) in enumerate(cv):
            if cn == 'OnlineMoneyCtrl':
                drop.add(i)
            elif cn == 'TriggerBox2' and v and isinstance(v[0], list) and [j for s in v[0] for j in sc.resolve(s)] == [k]:
                drop.add(i)
            else:
                raise ValueError('%s: unexpected controller %s' % (sc.path[k], cn))
        n['ctrls'] = [c for i, c in enumerate(n['ctrls']) if i not in drop]
        got.append((k, sc.names[k], [cv[i][0] for i in sorted(drop)]))
    return got


def move_group(B, g, pos):
    """Group node g (ZGROUP directly under a top-level group at the identity) to the world place pos: .prp ZGEOM[2] + the .gms record (kl_loot_1025.move without its top-level check)."""
    sc, e = B.sc, B.ents[g - 1]
    par = sc.parent[g]
    if sc.cls(g) != 'ZGROUP' or sc.parent[par] != 0 or any(abs(v) > 1e-6 for v in LO.zgeom(B, par)):
        raise ValueError('%s: not a group under a top-level group at the origin' % sc.path[g])
    kids = [j for j in range(g + 1, sc.end[g]) if sc.parent[j] == g]
    lab = LO.J.labels('dd', sc.cls(g))
    i = lab.index('ZGEOM[2]')
    LO.kl_graft.edit(sc.nodes[g], 'props', lambda us: LO.AU.setv(sc, us, i, [float(x) for x in pos]))
    e.trans = LO.struct.pack('<3f', *[float(x) for x in pos]) + e.trans[12:]
    return kids


def build_loot(src, slot, dst, amounts, strip, moves=None, log=print):
    B = KB.Built(src, slot)
    sc = B.sc
    before = LO.money(B)
    moves = moves or {}
    pos0 = {g: [round(float(v), 3) for v in B.at(g)] for g in moves}
    kids = {}
    if moves:
        every = [j for g in moves for j in range(g, sc.end[g])]
        stuck = LO.listed_in_oct(B, every)
        if stuck:
            raise ValueError('nodes %s are listed in an .oct room tree' % stuck)
        for g, pos in moves.items():
            kids[g] = move_group(B, g, pos)
    for k in list(amounts) + list(strip):
        if k not in before:
            raise ValueError('node %d is not a loot object' % k)
    gone = strip_orphans(B, strip)
    for k, v in amounts.items():
        LO.amount(B, k, v)
    prp = sc.p.serialize()
    gms, buf = B.scene.write()
    new = {B.ext['.prp']: prp, B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf}
    repl = {n: b for n, b in new.items() if b != B.files[n]}
    LO.patch_zip(src, dst, repl)
    A = KB.Built(dst, slot)
    after = LO.money(A)
    bad = []
    for k in before:
        if k in strip:
            if k in after:
                bad.append('node %d still a loot object' % k)
        elif after.get(k) != amounts.get(k, before[k]):
            bad.append('node %d amount %s != %s' % (k, after.get(k), amounts.get(k, before[k])))
    if set(after) != set(before) - set(strip):
        bad.append('loot set differs')
    if sum(after.values()) not in (TOTAL,) + tuple(t for t, _w in _LS.TARGETS.values()):     # 2026-10-26: 4M (this builder) or a map's 4M..8M target
        bad.append('total %d != %d' % (sum(after.values()), TOTAL))
    for n in A.files:
        if n not in repl and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if A.files[B.ext['.prm']] != B.files[B.ext['.prm']]:
        bad.append('.prm changed')
    if len(A.sc.names) != len(sc.names):
        bad.append('node count changed')
    for g, pos in moves.items():
        for j in range(g, sc.end[g]):         # the group lands on pos and every child keeps its offset from the group (the group's own turn is untouched)
            w, w0, a0, b0 = A.at(j), B.at(j), A.at(g), B.at(g)
            if j == g and any(abs(w[i] - pos[i]) > 0.01 for i in range(3)):
                bad.append('%s world %s != %s' % (sc.path[j], [round(v, 2) for v in w], pos))
            if any(abs((w[i] - a0[i]) - (w0[i] - b0[i])) > 0.01 for i in range(3)):
                bad.append('%s moved against its group' % sc.path[j])
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep = collections.OrderedDict(
        members_changed=sorted(repl), total_before=sum(before.values()), total_after=sum(after.values()), objects_before=len(before), objects_after=len(after),
        amounts=[collections.OrderedDict(node=k, name=sc.names[k], old=before[k], new=v) for k, v in amounts.items()],
        stripped=[collections.OrderedDict(node=k, name=n, removed=c) for k, n, c in gone],
        moved_groups=[collections.OrderedDict(group=g, name=sc.names[g], old=pos0[g], new=list(p), children=len(kids[g])) for g, p in moves.items()])
    log('  loot: members %s; total %d -> %d; %d amounts, %d stripped' % (' '.join(rep['members_changed']), rep['total_before'], rep['total_after'], len(amounts), len(strip)))
    return rep


INSTALL_PY = LO.INSTALL_PY.replace('loot-placement', 'van-lane + loot').replace('tools/kl_loot_1025.py', 'tools/kl_lanes_stage_1025.py')


def stage_map(root, name, scratch=None, log=print):
    sp = SPEC[name]
    slot, zn, pin = MAPS[name]
    d = os.path.join(root, name)
    src = os.path.join(d, 'in', zn)
    h = md5(src)
    if h != pin:
        raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, pin))
    out = os.path.join(d, 'stage')
    LO.rmtree(out)
    os.makedirs(out)
    log('== %s (%s) ==' % (name, zn))
    mid = os.path.join(out, 'mid_' + zn)
    final = os.path.join(out, zn)
    rep = build_loot(src, slot, mid, sp['amounts'], sp['strip'], sp.get('moves'), log)
    cars = []
    if sp['cars']:
        if sp['cars'] == 'dm02':
            s0, plen, _prof = LN.dm02_start_s(src)
            log('  CopCar01 route %.0f long: re-spread from s0 = %.0f (every pose >= %.0f from the swept footprint of the van)' % (plen, s0, LN.DM02_CLEAR))
            repl, cars = LN.relay_cars(mid, log, [LN.DM02_CAR], LN.lanes_dm02(s0))
        else:
            repl, cars = LN.relay_cars(mid, log)
        patch_zip(mid, final, repl)
        os.remove(mid)
        rep['members_changed'] = sorted(set(rep['members_changed']) | set(repl))
        for c in cars:
            log('  ' + c)
    else:
        os.replace(mid, final)
    rep.update(md5_in=h, md5_out=md5(final), cars=cars)
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(final) as b:
        assert a.namelist() == b.namelist()
        diff = sorted(n for n in a.namelist() if a.read(n) != b.read(n))
        assert diff == rep['members_changed'], (diff, rep['members_changed'])
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=name, zip=zn, tag=TAG, game=GAME, old=h, new=rep['md5_out']))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    if scratch:
        LO.MAPS[name] = dict(slot=slot, zip=zn)
        LO.TAG = TAG
        LO.rehearse(out, name, src, rep['md5_out'], h, scratch, log)
    return rep


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] != 'stage':
        print(__doc__)
        return 2
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    names = [x for x in a[2:] if x in SPEC] or list(SPEC)
    for n in names:
        stage_map(a[1], n, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
