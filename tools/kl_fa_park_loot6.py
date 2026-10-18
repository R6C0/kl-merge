#!/usr/bin/env python3
"""
kl_fa_park_loot6.py - Park II (DM06B), the tea house's money case (loot 6 of kl_fa_v2_park.LOOT): move it so the bots can take it. OFFLINE post-pass, opt-in.

    python kl_fa_park_loot6.py <finished map folder> <out folder>
    python kl_fa_park_loot6.py check <folder>            # where the case is, which polygon, how far a bot at the door is from it

WHY (kl-merge-e5's analysis of the Park II runs): the crew's walk to the tea house ends about 170 units from the case, and the pick-up reach is 165
(TriggerBox2 radius 125 + 40). The tea house is ONE mesh polygon (DM06B nav polygon 447, x 737..869, z -2536..-2334, flat y 220); its only way in is the
north edge (z -2334) from polygon 666. The old case stood at (802, -2456), 122 in from that edge, so a bot that stops in front of the door is out of reach.
The new place is 46 in from the edge and 3 from the west wall: a bot standing at the door is 78 away on the floor plan (87 from the door's far corner).

HOW REACH IS MEASURED (kl_fa_loot.in_reach, read at kl2 0x783e60; klhook has no copy of it): FLAT distance h = hypot(dx, dz) between the actor's node and the
trigger's node must be <= radius + 40; then the HEIGHT must satisfy |actor y - node y| <= 100 + sqrt(R*R - h*h). It is not a 3D distance. The mesh floor
of this map is a flat y 220 (the garden's collision floors are 172..199), so a bot's node is 44 above the case's origin: inside the height window at every h
(100 + chord), so the case's y is NOT what stops a pick-up and is not raised to the mesh. It only follows the COLLISION floor under the new spot.

What changes: the .prp ZGEOM[2] (position) of the one node FASpecials!DropMoney!MoneyStack_099 (a ZSTDOBJ with the OnlineMoneyCtrl and TriggerBox2 controllers in
the same node; no children), by the offset old -> new. Controllers carry no position of their own, so nothing else moves. Only the .prp member of
<slot>_Main.zip is rewritten; every other member and every side file is copied as it was.

NOT moved (looked at): Specials!JumpPoints!03_MarketOrange (802, 180, -2456) is a jump point of the crew's hop, at the old x/z; Gameplay!merc_bot_squad!Squad#03's
defend place Pos#01 (802.6, 220, -2470.7). Neither belongs to the case.

GUESS / ASSUMPTION (NOT RUN IN THE GAME):
  * the .gms entity record keeps the old position: kl_fa_author.place writes both 'as in stock', this pass only the .prp, as asked. The Dog Days loader reads
    the .prp's position (kl_fa_author.place docstring); whether anything reads the .gms copy (lists, culling) was not checked.
  * the collision floor under the new spot is 176.5 (kl_fa_loot.Floors at (740, -2380): 176.47; the old spot 175.5, written 175.0), so the origin rises 1.5;
    the case is not turned or scaled. The spot is clear of the tea house's walls by the walk test's grid only (cell 20 x 20), not by the model's footprint.
  * a bot stops at the door, not inside: the 170 is the earlier analysis's number, not re-measured here.
"""
import math, os, shutil, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_fa_author as au, kl_prpjoin as J

OLD = (802.0, -2456.0)                  # x, z of the case in kl_fa_v2_park.LOOT (the tea house)
OLD_FLOOR = 175.0                       # LOOT's underside y
NEW = (740.0, -2380.0)                  # on mesh polygon 447; fallback (760, -2400) (floor 180)
NEW_FLOOR = 176.5                       # MEASURED: collision floor at NEW (kl_fa_loot.Floors cell, 176.47)
POLY = 447                              # the tea house's mesh polygon (DM06B)
DOOR = (803.0, 220.0, -2334.0)          # middle of the edge polygon 447 shares with 666 (the way in); MEASURED from the mesh
BOT_STOP = (802.0, 220.0, -2290.0)      # where the earlier analysis had bots stop: ~170 from the old case (e5's number, here as a point on the door's axis)
PAD = 40.0                              # kl2 0x783e60 (kl_fa_loot.REACH_PAD)


def reach_ok(node, feet, radius):
    """kl2 0x783e60 as in kl_fa_loot.in_reach: flat h <= radius + 40 and |dy| <= 100 + sqrt(R*R - h*h)."""
    r = radius + PAD
    h = math.hypot(feet[0] - node[0], feet[2] - node[2])
    return h <= r and abs(feet[1] - node[1]) <= 100.0 + math.sqrt(r * r - h * h)


def zgeom(sc, k):
    lab = J.labels('dd', sc.cls(k))
    return lab.index('ZGEOM[2]'), kl_fa.node_values(sc, k)[lab.index('ZGEOM[2]')]


def loot_nodes(sc):
    """Every top-level money object that is loot -> [(node, position)]."""
    out = []
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if 'DROP' not in v[2] and sc.parent[k] == 0:
            out.append((k, tuple(zgeom(sc, k)[1])))
    return out


def find(sc, at):
    """The loot nodes whose flat position is within 1 of at=(x, z) -> [node]."""
    return [k for k, p in loot_nodes(sc) if math.hypot(p[0] - at[0], p[2] - at[1]) < 1.0]


def reach_radius(sc, k):
    from kl_prp import units
    obj = sc.nodes[k]['ctrls'][au.ctrl_of(sc, k, 'TriggerBox2')][1]
    return kl_fa.value(sc, list(units(obj[1:-1]))[2])


def check(sc, log=print):
    bad = []
    old, new = find(sc, OLD), find(sc, NEW)
    log('  loot objects: %d; at the old place (%g, %g): %s; at the new (%g, %g): %s' % (
        len(loot_nodes(sc)), *OLD, [sc.names[k] for k in old], *NEW, [sc.names[k] for k in new]))
    if len(old) + len(new) != 1:
        bad.append('the tea house case is not exactly one object at the old or the new place')
        return bad
    k = (old or new)[0]
    p = zgeom(sc, k)[1]
    r = reach_radius(sc, k)
    log('  %s at (%.1f, %.1f, %.1f), pick-up radius %g -> reach %g flat' % (sc.names[k], *p, r, r + PAD))
    if r + PAD != 165.0:
        bad.append('pick-up reach is %g, expected 165' % (r + PAD))
    log('  from the door middle %s: flat %.0f, from the old stopping point %s: flat %.0f, in reach: %s / %s' % (
        DOOR, math.hypot(DOOR[0] - p[0], DOOR[2] - p[2]), BOT_STOP, math.hypot(BOT_STOP[0] - p[0], BOT_STOP[2] - p[2]),
        reach_ok(p, DOOR, r), reach_ok(p, BOT_STOP, r)))
    if new:
        for name, feet in (('door middle', DOOR), ('old stopping point', BOT_STOP)):
            if not reach_ok(p, feet, r):
                bad.append('a bot at the %s %s is out of reach' % (name, feet))
        if not (737.0 <= p[0] <= 869.0 and -2536.0 <= p[2] <= -2334.0):
            bad.append('the new place is outside polygon %d' % POLY)
    return bad


def run(folder, out, log=print):
    folder, out = os.path.abspath(folder), os.path.abspath(out)
    zn = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
    zp = os.path.join(folder, zn)
    sc, _snd, _loc = kl_fa.load(zp)
    hit = find(sc, OLD)
    if len(hit) != 1:
        raise SystemExit('%d loot objects at the old place (%g, %g) (already moved?): %s' % (len(hit), *OLD, [sc.names[k] for k in hit]))
    if find(sc, NEW):
        raise SystemExit('a loot object already stands at the new place (%g, %g)' % NEW)
    k = hit[0]
    i, p = zgeom(sc, k)
    d = (NEW[0] - OLD[0], NEW_FLOOR - OLD_FLOOR, NEW[1] - OLD[1])
    q = [p[0] + d[0], p[1] + d[1], p[2] + d[2]]
    kids = sc.end[k] - k - 1
    kl_graft.edit(sc.nodes[k], 'props', lambda us: au.setv(sc, us, i, [float(x) for x in q]))
    data, bad, _paths, _n = J.check(sc, log=lambda *_a: None)
    if bad:
        raise SystemExit('%d objects do not fit after the edit' % len(bad))
    problems = check(sc, log=lambda *_a: None)     # the edited scene itself
    if problems:
        raise SystemExit('check: ' + '; '.join(problems))
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(folder):
        if f != zn and os.path.isfile(os.path.join(folder, f)):
            shutil.copyfile(os.path.join(folder, f), os.path.join(out, f))
    with zipfile.ZipFile(zp) as zin, zipfile.ZipFile(os.path.join(out, zn), 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as zo:
        for zi in zin.infolist():
            blob = data if zi.filename.lower().endswith('_main.prp') else zin.read(zi.filename)
            ni = zipfile.ZipInfo(zi.filename, zi.date_time)
            ni.compress_type, ni.external_attr = zi.compress_type, zi.external_attr
            zo.writestr(ni, blob)
    log('park loot 6: %s (%d children, controllers %s) (%.1f, %.1f, %.1f) -> (%.1f, %.1f, %.1f); flat to the door %.0f -> %.0f of reach 165' % (
        sc.names[k], kids, [sc.p.key(n) for n, _b in sc.nodes[k]['ctrls']], *p, *q,
        math.hypot(DOOR[0] - OLD[0], DOOR[2] - OLD[1]), math.hypot(DOOR[0] - NEW[0], DOOR[2] - NEW[1])))
    return k


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == 'check':
        zp = a[1] if a[1].lower().endswith('.zip') else os.path.join(a[1], [f for f in os.listdir(a[1]) if f.lower().endswith('_main.zip')][0])
        sc, _s, _l = kl_fa.load(zp)
        b = check(sc)
        print('PASS' if not b else 'FAIL: ' + '; '.join(b))
        sys.exit(1 if b else 0)
    if len(a) != 2 or a[0].startswith('--'):
        print(__doc__); sys.exit(2)
    run(a[0], a[1])
