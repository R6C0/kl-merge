"""kl_arcade_fix2_1026.py - DD10 (Flat Raid, F07), DM07 (The Dig, F06), DM01B (F03), DM06B (F02) closer to the stock Arcade standard. 2026-10-26, OFFLINE:
reads the live zips, writes only under <root>/<MAP>/stage.   Reference: C:/kl_build_1024/arcade_ref_1026 (audit.md, profile.md, measure_all.py).

One member-level patch of a COPY of the live zip (md5 pinned): only .prp / .gms (and .buf when its bytes differ) are replaced; .oct .rmi .rmc .prm .HVK ... stay
byte-identical (asserted). No entity is created or deleted (no slot renumbering, no .prm Entries change): edits are values of existing nodes.
TOGGLE (owner's rule): map CONTENT; the switch is install.py / install.py --undo (original -> '<zip>.before-1026arcade').

Pieces
  thin_start   squads with soldiers closer than LIMIT_M to START: their MEN groups (not the step groups) are moved to the nearest mesh place >= KEEP_M from every START
               row, same floor; the squad's Pos# / RunToPosInfo / Defend boxes keep their world places, so the squad still comes to the fight when it is started.
  gather       loot stacks to reachable places beside other stacks (<= GATHER_M from an anchor stack = one audit cluster), checked with kl_fa_loot.Floors.stand.
  cover        an all-AUTO PlayerCoverModifier (cloned from stock F01) on the existing *CoverBox* nodes near the loot stacks.
  approach     DD10: the POI trigger box (9 m round the pad) widened to a street zone, so the escape POI + text appear on the way, as stock F07's box 94 m before the pad.
Totals are REPORTED, not asserted (owner 2026-10-26: loot totals up to 8,000,000 will be rescaled by tools/kl_loot_scale_1026.py after install).

Usage (from tools/):  python kl_arcade_fix2_1026.py stage <root> [MAP ...] [--rehearse <scratch>]       <root>/<MAP>/in/<zip> (+ files beside it)
"""
import collections, json, math, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_loot_1025 as LT
import kl_bots_kick_1025 as KK
import kl_prpjoin as J

BS = chr(92)
TAG = '.before-1026arcade'
GAME = LT.GAME
md5 = LT.md5
LIMIT_M = 5            # thin_start: keep at most this many soldiers within 30 m of START (stock max 7)
NEAR_M = 30.0
KEEP_M = 33.0          # a moved squad stands at least this far from every START row (stock nearest soldier 19.2 m, within-30 m max 7)
GATHER_M = 7.0         # gathered stacks stand within this of their anchor stack (the audit clusters stacks closer than 10 m)
MIN_WALK_M = 41.0     # DM07: gathered stacks stay at least this far (walking) from START (owner: none within 40 m)
COVER_R = 1200.0       # cover boxes within 12 m of a stack
COVER_MAX = 4

# name -> (slot, zip name, pinned live md5)
MAPS = collections.OrderedDict([
    ('DD10', ('F07', 'F07_Main.zip', '03db243ba43cf2aa257843a944e2d235')),
    ('DM07', ('F06', 'F06_Main.zip', 'd59d69a5ec5f975a8f22d838cca83933')),
    ('DM01B', ('F03', 'F03_Main.zip', 'fbbb721638e265a8963882ecd10daf30')),
    ('DM06B', ('F02', 'F02_Main.zip', '835457e1c12a20ed0bb64ed6848e6909'))])


def d2(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


class Work:
    """A built map (KB.Built) with the navigation mesh, the START rows and the helpers the pieces need."""

    def __init__(self, src, slot):
        self.src, self.slot = src, slot
        self.B = KB.Built(src, slot)
        self.sc = self.B.sc
        self.nav = KB.Nav(self.B.scene.nav, links=True)
        self.st = KB.stations(self.B, self.nav)
        self.home = self.st['home']
        self.starts = [tuple(p) for p, _f in self.st['starts']]
        self.centre = tuple(sum(p[i] for p in self.starts) / len(self.starts) for i in range(3))
        self.log = []

    def say(self, s):
        self.log.append(s)
        print(s)

    def on_home(self, x, y, z, dy=60.0):
        h = self.nav.at(x, y, z, dy=dy)
        return (x, h[1], z) if h and self.nav.part[h[0]] == self.home else None

    def actors(self):
        return [self.B.at(k) for k in range(1, len(self.sc.nodes)) if self.sc.cls(k) == 'ZFFActor']

    def set_zgeom(self, k, pos, local=False):
        """Top-level or child node k to world place pos (the .prp ZGEOM[2] is local to the parent; the .gms record is local too)."""
        sc, e = self.sc, self.B.ents[k - 1]
        lab = J.labels('dd', sc.cls(k))
        p = self.B.local(sc.parent[k], pos) if sc.parent[k] else pos
        p = [float(v) for v in p]
        kl_graft.edit(sc.nodes[k], 'props', lambda us: AU.setv(sc, us, lab.index('ZGEOM[2]'), p))
        e.trans = struct.pack('<3f', *p) + e.trans[12:]


# ------------------------------------------------------------------ thin_start
def squads_near(w, centre):
    """-> {squad top: [(man group node, its ZFFActor node, world place)]} for the Enemy squads (not the heister bots, not the hero rows)."""
    sc, out = w.sc, collections.OrderedDict()
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor' or sc.names[k] != 'Ground':
            continue
        g = sc.parent[k]
        if g == 0 or sc.cls(g) != 'ZGROUP':
            continue
        top = sc.top[k]
        if top == g or 'merc_bot_squad' in sc.path[top] or sc.names[top].startswith('Heroes'):
            continue
        out.setdefault(top, []).append((g, k, w.B.at(k)))
    return out


def thin_start(w, only=None, limit=LIMIT_M):
    """Move the nearest squads' men away from START until at most `limit` soldiers stand within 30 m. -> [report rows]."""
    sc = w.sc
    sq = squads_near(w, w.centre)
    dist = lambda p: d2(p, w.centre) / 100.0
    near = sum(1 for s in sq.values() for _g, _k, p in s if dist(p) < NEAR_M)
    order = sorted(sq, key=lambda t: min(dist(p) for _g, _k, p in sq[t]))
    rows, taken = [], [p for s in sq.values() for _g, _k, p in s]
    stuck = LT.listed_in_oct(w.B, [g for s in sq.values() for g, _k, _p in s])
    for top in order:
        if near <= limit:
            break
        men = sq[top]
        inside = [m for m in men if dist(m[2]) < NEAR_M]
        if not inside or (only and sc.names[top] not in only):
            continue
        if any(g in stuck for g, _k, _p in men):
            w.say('  thin: %s skipped: a man group is listed in an .oct tree' % sc.names[top])
            continue
        # one site for the squad: the nearest mesh place to the first man that is KEEP_M from every START row, then the others at their offsets
        a = men[0][2]
        site = None
        for rad in range(300, 14001, 150):
            cand = []
            for k in range(0, 24):
                ang = k * math.pi / 12
                x, z = a[0] + rad * math.cos(ang), a[2] + rad * math.sin(ang)
                p = w.on_home(x, a[1], z)
                if not p or min(d2(p, s) for s in w.starts) < KEEP_M * 100.0:
                    continue
                spots = []
                for g, _k, q in men:
                    t = w.on_home(p[0] + q[0] - a[0], q[1], p[2] + q[2] - a[2])
                    if t is None:
                        t = next((w.on_home(p[0] + dx, q[1], p[2] + dz) for dx, dz in ((130, 0), (-130, 0), (0, 130), (0, -130), (200, 200), (-200, -200)) if w.on_home(p[0] + dx, q[1], p[2] + dz)), None)
                    if t is None or any(d2(t, o) < 110.0 and abs(t[1] - o[1]) < 150 for o in taken + [s for s in spots]):
                        spots = None
                        break
                    spots.append(t)
                if spots:
                    cand.append((abs(math.hypot(w.centre[0] - p[0], w.centre[2] - p[2]) - KEEP_M * 100.0), spots))
            if cand:
                site = min(cand, key=lambda c: c[0])[1]
                break
        if site is None:
            w.say('  thin: %s: no mesh site found' % sc.names[top])
            continue
        for (g, _k, q), t in zip(men, site):
            w.set_zgeom(g, (t[0], t[1] + 1.0, t[2]))   # a man's group stands 1 above the floor (MEASURED: ZFFActor y - mesh y = 1.0 on every actor of DM07)
            taken.append(t)
        near -= len(inside)
        rows.append(dict(squad=sc.path[top].replace('ROOT' + BS, ''), men=len(men), near_before=len(inside), old=[[round(v) for v in m[2]] for m in men],
                         new=[[round(v) for v in t] for t in site], dist_new_m=[round(dist(t), 1) for t in site]))
        w.say('  thin: %s: %d men %s -> %s' % (sc.names[top], len(men), [round(dist(m[2]), 1) for m in men], rows[-1]['dist_new_m']))
    w.say('  thin: soldiers within 30 m of START now %d (limit %d)' % (near, limit))
    return rows


# ------------------------------------------------------------------ gather (loot)
class Reach:
    def __init__(self, w, zp, margin=1500.0):
        import kl_fa_loot as L
        self.L = L
        self.lv = L.Built(zp)
        xs = [p[0] for pl in w.nav.pv for p in pl]
        zs = [p[2] for pl in w.nav.pv for p in pl]
        box = (min(xs) - margin, max(xs) + margin, min(zs) - margin, max(zs) + margin)
        self.f = L.Floors(self.lv.hvk, box, skip=(self.lv.soft() | self.lv.hidden))
        self.seen, _ = self.f.flood([tuple(p) for p in w.starts], snap=200.0)
        self.rad = L.loot(self.lv)[0]['radius']

        # walking distance from the START spawn nearest the centre, over the plain mesh (no links), as the audit (arcade_ref_1026/measure_all.py) counts it
        self.nav0 = KB.Nav(w.B.scene.nav)
        order = sorted(w.starts, key=lambda q: math.hypot(q[0] - w.centre[0], q[2] - w.centre[2]))
        self.dm = None
        for sp in order:
            i0 = self._nat(sp)
            if i0 is not None:
                self.dm = self.nav0.dist_map(i0, sp)[0]
                break

    def _nat(self, p):
        for dy in (260.0, 600.0, 1500.0):
            h = self.nav0.at(p[0], p[1], p[2], dy=dy)
            if h:
                return h[0]

    def walk(self, p):
        i = self._nat(p)
        extra = 0.0
        if i is None or i not in self.dm:
            best = min(((math.hypot(self.nav0.mid[j][0] - p[0], self.nav0.mid[j][2] - p[2]), j) for j in self.dm), default=None)
            if best is None or best[0] > 800:
                return None
            i, extra = best[1], best[0] / 100
        return self.dm[i] / 100 + extra

    def spare(self, p):
        pl, hd, n = self.f.stand(self.seen, p, self.rad)
        return None if hd is None else self.rad + 40.0 - hd


def gather(w, reach, moves, min_walk=0.0, radius_m=None):
    """moves: {stack node: anchor stack node} -> {node: new place}. The new place: on the main mesh part, Floors.stand spare >= 60, 3 m..GATHER_M from the anchor,
    3 m from every other stack, 450 from every START row, same floor as the anchor."""
    B = w.B
    pos = {k: tuple(B.at(k)) for k in range(1, len(w.sc.nodes)) if k in {o['node'] for o in KB.money_objects(B)}}
    out = {}
    R = (radius_m or GATHER_M) * 100
    for k, anchor in moves.items():
        a = out.get(anchor, pos[anchor])
        fl = w.nav.at(a[0], a[1], a[2], dy=120.0)
        off = a[1] - fl[1] if fl else 0.0          # the anchor stack's height above its floor
        best = []
        for dx in range(-int(R), int(R) + 1, 30):
            for dz in range(-int(R), int(R) + 1, 30):
                dd = math.hypot(dx, dz)
                if dd < 300 or dd > R:
                    continue
                x, z = a[0] + dx, a[2] + dz
                p = w.on_home(x, a[1] - off, z, dy=80.0)
                if not p:
                    continue
                q = (x, p[1] + off, z)
                if any(d2(q, o) < 300 and abs(q[1] - o[1]) < 150 for kk, o in list(pos.items()) + list(out.items()) if kk != k):
                    continue
                if min(d2(q, s) for s in w.starts) < 450:
                    continue
                if min_walk and (reach.walk(q) or 0) < min_walk:
                    continue
                sp = reach.spare(q)
                if sp is None or sp < 60:
                    continue
                best.append((abs(dd - 500), q, round(sp)))
        if not best:
            raise ValueError('stack %d: no place within %.0f m of stack %d' % (k, GATHER_M, anchor))
        best.sort()
        out[k] = tuple(round(v, 1) for v in best[0][1])
        w.say('  gather: stack %d %s -> %s (beside %d, spare %d)' % (k, [round(v) for v in pos[k]], [round(v) for v in out[k]], anchor, best[0][2]))
    for k, p in out.items():
        LT.move(B, k, p)
    return out


# ------------------------------------------------------------------ cover
def donor_pcm():
    sc = J.Scene.load('F01')
    for k, i, v in kl_fa.controllers(sc, 'PlayerCoverModifier'):
        if sc.cls(k) == 'ZSTDOBJ' and all(x == 'AUTO' for x in v if isinstance(x, str)) and len(sc.nodes[k]['ctrls']) == 1:
            nm, body = sc.nodes[k]['ctrls'][i]
            return nm, body, sc
    raise ValueError('no all-AUTO PlayerCoverModifier in F01')


def remap(tok, src, dst):
    op, pl = tok
    if op in (0x0c, 0x0e):
        return (op, struct.pack('<I', dst.p.key_index(src.p.keys[struct.unpack('<I', pl)[0]])))
    if op == 0x0f:
        raise ValueError('donor holds a 0x0f token')   # GUESS: same layout as 0x0c / 0x0e; the donor has none
    return tok


def cover(w, stacks, where=None):
    """-> [(box node, stack node, metres)]"""
    sc = w.sc
    nm, body, src = donor_pcm()
    name = remap(nm, src, sc)
    toks = [remap(t, src, sc) for t in body]
    boxes = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSTDOBJ' and 'coverbox' in sc.names[k].lower()]
    have = {k for k, i, v in kl_fa.controllers(sc, 'PlayerCoverModifier')}
    done, taken = [], set()
    for s in stacks:
        p = (where or {}).get(s) or w.B.at(s)      # where: the stacks' new places (B.at still has the frames of the input)
        near = sorted((math.dist(p, w.B.at(k)), k) for k in boxes if k not in have)
        for d, k in [x for x in near if x[0] <= COVER_R][:COVER_MAX]:
            if k not in taken:
                sc.nodes[k]['ctrls'].append((name, list(toks)))
                taken.add(k)
            done.append((k, s, round(d / 100.0, 1)))
    w.say('  cover: %d PlayerCoverModifier added on %d *CoverBox* nodes (%d box-stack pairs, %d boxes in the map)' % (len(taken), len(taken), len(done), len(boxes)))
    return done


# ------------------------------------------------------------------ write
def write(w, dst, expect_members=('.prp', '.gms', '.buf')):
    B = w.B
    prp = w.sc.p.serialize()
    gms, buf = B.scene.write()
    gms = kl_gms.pack(gms)
    new = {B.ext['.prp']: prp, B.ext['.gms']: gms, B.ext['.buf']: buf}
    repl = {n: b for n, b in new.items() if b != B.files[n]}
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    LT.patch_zip(w.src, dst, repl)
    A = KB.Built(dst, w.slot)
    bad = []
    for n in A.files:
        if n not in repl and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    for ext in ('.prm', '.oct', '.rmi', '.rmc'):
        if A.files[B.ext[ext]] != B.files[B.ext[ext]]:
            bad.append('%s changed' % ext)
    if len(A.ents) != len(B.ents):
        bad.append('entity count changed')
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    return A, sorted(repl)


# ------------------------------------------------------------------ the plans
# DD10: widen the POI trigger box. Stock F07's Trigger_POI_TheEscapeArea sits ~94 m before the pad; DD10's is the same 9 m box as the exit trigger.
APPROACH_NODE = 'FASpecials!POI!Trigger_POI_TheEscapeArea'
APPROACH_BOX = ((9300.0, 200.0, 1100.0), (1500.0, 300.0, 900.0))   # centre, half size: x 7800..10800, z 200..2000. GUESS: on the way from the tower to the pad; START (12736) is 19 m east of it


def approach(w):
    ks = w.sc.resolve('ROOT' + BS + APPROACH_NODE)
    if len(ks) != 1:
        raise ValueError('%d nodes %s' % (len(ks), APPROACH_NODE))
    k = ks[0]
    if LT.listed_in_oct(w.B, [k]):
        raise ValueError('approach trigger listed in an .oct tree')
    was = (tuple(w.B.at(k)), w.B.box(k))
    lab = J.labels('dd', w.sc.cls(k))
    pos, half = APPROACH_BOX

    def fn(us):
        AU.setv(w.sc, us, lab.index('ZGEOM[2]'), [float(v) for v in pos])
        for i, v in enumerate(half):
            AU.setv(w.sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
    kl_graft.edit(w.sc.nodes[k], 'props', fn)
    w.B.ents[k - 1].trans = struct.pack('<3f', *pos) + w.B.ents[k - 1].trans[12:]
    w.say('  approach: %s %s -> %s' % (APPROACH_NODE, was, APPROACH_BOX))
    return dict(node=k, was=was, now=APPROACH_BOX)


def plan_DD10(w, zp):
    rep = collections.OrderedDict()
    rep['approach'] = approach(w)
    return rep


def plan_DM07(w, zp):
    rep = collections.OrderedDict()
    rep['thin'] = thin_start(w)
    # GUESS: gather the 11 stacks into 2..3 clusters far from the exit (stock FA: 2..4 clusters); stock stacks sit in the open, 3..7 m apart
    reach = Reach(w, zp)
    # owner 2026-10-26: no stack within 40 m walk of START (stock profile min 30.3 m; here MIN_WALK_M): anchors 14224 / 14227 already stand 43 / 41 m away
    moves = {14228: 14229, 14223: 14229, 14226: 14227, 14225: 14227, 14224: 14227, 14140: 14127, 14129: 14128}   # -> 3 clusters: {227,224,225,226} {229,228,223} {127,140} {128,129}; stacks 14127/14128/14229/14227 stay
    rep['gather'] = gather(w, reach, moves, min_walk=MIN_WALK_M, radius_m=9.0)
    rep['cover'] = cover(w, [14223, 14224, 14225, 14226, 14227, 14228, 14229, 14127, 14128, 14129, 14140], where=rep['gather'])
    return rep


def plan_DM01B(w, zp):
    return collections.OrderedDict()


def plan_DM06B(w, zp):
    rep = collections.OrderedDict()
    reach = Reach(w, zp)
    # GUESS: 98/99 beside 101 and 100 beside 103 (3 clusters instead of 7); the six far upper stacks (335 m walk, stock max 300.8 m) beside 115 / 204 (287 / 293 m)
    moves = {19098: 19101, 19099: 19102, 19100: 19103,
             19198: 19115, 19199: 19115, 19200: 19115, 19201: 19204, 19202: 19204, 19203: 19204}
    rep['gather'] = gather(w, reach, moves)
    rep['cover'] = cover(w, sorted(set(moves) | set(moves.values())), where=rep['gather'])
    return rep


PLANS = dict(DD10=plan_DD10, DM07=plan_DM07, DM01B=plan_DM01B, DM06B=plan_DM06B)


def build(name, src, dst, log=print):
    slot, zn, pin = MAPS[name]
    h = md5(src)
    if h != pin:
        raise SystemExit('%s md5 %s is not the pinned %s' % (src, h, pin))
    w = Work(src, slot)
    money0 = LT.money(w.B)
    rep = PLANS[name](w, src)
    A, members = write(w, dst)
    money1 = LT.money(A)
    rep = collections.OrderedDict(md5_in=h, md5_out=md5(dst), members_changed=members, loot_total_before=sum(money0.values()), loot_total_after=sum(money1.values()),
                                  loot_stacks=len(money1), **rep)
    rep['log'] = w.log
    return rep


def stage(root, names=None, scratch=None, log=print):
    out = {}
    for name in names or MAPS:
        slot, zn, pin = MAPS[name]
        d = os.path.join(root, name)
        src = os.path.join(d, 'in', zn)
        st = os.path.join(d, 'stage')
        KK.rmtree(st)
        os.makedirs(st)
        log('== %s' % name)
        rep = build(name, src, os.path.join(st, zn), log)
        with open(os.path.join(st, 'install.py'), 'w', newline='\n') as fh:
            fh.write((KK.INSTALL_PY % dict(map=name, zip=zn, tag=TAG, game=GAME, old=pin, new=rep['md5_out'])).replace(
                'door-kick zip (tools/kl_bots_kick_1025.py', 'arcade-standard zip (tools/kl_arcade_fix2_1026.py'))
        with open(os.path.join(st, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        if scratch:
            KK.MAPS[name] = (slot, zn, pin)
            KK.TAG = TAG
            KK.rehearse(st, name, src, rep['md5_out'], pin, scratch, log)
        out[name] = rep
    return out


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) >= 2 and a[0] == 'stage':
        names = [x for x in a[2:] if x in MAPS]
        stage(a[1], names or None, opt('--rehearse'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
