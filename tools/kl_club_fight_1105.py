"""kl_club_fight_1105.py - Last Call (DM05A) FIGHT VARIETY post-pass (2026-11-05, OFFLINE: reads a zip, writes only under the stage folder).

Owner play feedback 2026-11-05: more enemies on the 2nd floor (not only the roof); roof men need personality (flank / hold cover / push / shotgun
rusher); the front assault must run in and take cover; guards just before the loot room; kickable doors on the way out.

WHAT IT ADDS (every node is a CLONE of a node of the build itself, schemas exact; all found by NAME, so it chains over any other post-pass)
  census +14 actors / +5 squads (default; --no-new keeps the census and only edits)  NEW TOP GROUPS (all under the name prefix 'Fight!'):
    Fight!Clock               Go timers (named in the AIMonitor START list, the way OldWaves!Clock does it)
    Fight!Rush                3 men (SMG) spawn on the front lane and RUN into the foyer, then dash to cover boxes (Defend eDMS_Run -> hold -> cover Defend)
    Fight!F2_Hold             3 rifles on the 2nd floor ahead of the stairs: Defend + SquadModifier tight / UseCovers
    Fight!F2_Flank            3 SMGs spawn BEHIND the heisters' route on floor 2 (west end) and RUN back along it (RandomTrigger picks one of two lanes)
    Fight!F2_Shot             2 shotgun rushers (Hawk Police), eUnleashed, Run, loose
    Fight!Loot                3 guards, in the world from load, in the corridor between the two daughter-room doors (just before the loot room)
  EDITS of existing squads (no actor added): OldWaves!Wave_1..6 (front/foyer) and OldWaves!Roof_R1..R3 get a rout CHAIN (field 7 of the Defend):
    Wave_1 hold (tight + covers) / Wave_2 run to cover boxes / Wave_3 push (loose, deeper Pos) / Wave_4 run to cover / Wave_5 flank (RandomTrigger of two lanes)
    / Wave_6 hold + covers; Roof_R1 hold tight + covers / R2 push forward along the route after 60 s / R3 hold, then flank to the other side.
  NOTHING of the behaviours is invented: Defend (field 0 / 1 / 4 / 7), TriggerDelay2, RandomTrigger and SquadModifierBehaviour are the forms the stock FA
  bot squads (Gameplay!merc_bot_squad!Squad#03) and OldWaves already use in this map (re/dm01_ai_cover_1025.md).
  KICK DOORS: NOT staged by default (see re/club_fight_1105.md: the map has no static door leaves; the fire doors are animated and CLOSED; one mesh doorway
  on the route). `--doors` stages a SECOND zip (stage/doors/) built with kl_interact_graft on top of the result; untested, off by default.

GUESSES (labelled GUESS in the code): a Defend with field 4 eDMS_Run runs to its posts; Defend field 7 fires on arrival (proven in the bot squads); a cover
  'Pos' is a box position snapped to the walk mesh (clearance >= 60); SquadModifier field 15 eCOM_UseCovers; ZSquadScript field 0 eUnleashed for the rushers.

usage (from tools/):  python kl_club_fight_1105.py stage [--src <zip>] [--out <dir>] [--no-new] [--doors] [--force]
                      python kl_club_fight_1105.py check <zip>         (the post-pass checks of the owner-map checklist, off game)
"""
import collections, hashlib, json, math, os, shutil, struct, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_fa_bank as BK
import kl_fa_fed as FED
import kl_octree as O
import kl_prpjoin as J
import kl_old_waves as KOW
import kl_club_lastcall2 as L2
import kl_bots_kick_1025 as KK
from kl_prp import Prp

BS = chr(92)
R = 'ROOT' + BS
TAG = '.before-1105fight'
GAME = KK.GAME
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A', 'F01_Main.zip')
PIN = 'e9fab0453a5260369c2fddd01bed5534'            # the live zip when this pass was written (2026-11-05)
OUT = 'C:/kl_build_1024/lastcall_fight_1105'
TOP = 'Fight!'
CLOCK = 'Fight!Clock'
WEAPON = R + 'AllLevels/mainsceneincludes_multiplayer.zip' + BS + 'AllLevels/equipment.zip' + BS + 'Weapon' + BS
MOD_FORM = R + 'Gameplay!merc_bot_squad!Squad#03' + BS + '012_SquadModifier_tight_defense_loot'
RND_FORM = R + 'Gameplay!merc_bot_squad!Squad#03' + BS + '010_RandomTrigger_way'
DEF_FORM = R + 'OldWaves!Wave_2' + BS + '10_Defend'
POS_FORM = R + 'OldWaves!Wave_2' + BS + '10_Defend' + BS + 'Pos#01'
SQ_FORM = 'AI_Players!Enemies!SecondRun!YokoGuards'
COVER_TOPS = ('KL_CoverSix!', 'KL_CoverMore!', 'KL_CoverAB!')
CLEAR = 60.0

# ---- anchors (x, y, z), measured in the live build (tools/kl_club_lastcall2.py ANCH and the route of the 2026-11-05 census)
FRONT_LANE = (-65.0, 19.0, -1307.0)
FOYER = (-350.0, 100.0, -450.0)
STAIRS_TOP = (300.0, 460.0, 600.0)
F2_HOLD = (-55.0, 460.0, 1545.0)
F2_WEST = (-3146.0, 460.0, -339.0)
F2_MID = (-1522.0, 460.0, 636.0)
LOOT_CORRIDOR = (2300.0, 358.0, 3330.0)             # between DaughterRoomDoorB_01 (x 1500) and DoorA_02 (x 2500); the loot room is beyond A (POI at 2700, 520, 2260)

# weapon file name -> which men carry it (clone source is an existing Enemy actor with that weapon, so its template is loaded)
RIFLE, SMG, SHOT = ('Rifle_FN_SCAR', 'Rifle_Type81', 'Rifle_AK74'), ('SMG_MPi69', 'SMG_HK_sp89', 'SMG_Type05'), ('Shotgun_Hawk_Police',)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ places
class Places:
    def __init__(self, B, nav, home):
        self.B, self.nav, self.part = B, nav, nav.part[home]
        sc = B.sc
        self.covers = []
        for t in sc.tops():
            if sc.names[t] in COVER_TOPS:
                for k in range(t + 1, sc.end[t]):
                    if sc.names[k].startswith('CoverBox'):
                        self.covers.append(tuple(B.at(k)))
        self.used = []

    def snap(self, p, need=CLEAR, radius=700.0, gap=90.0):
        """The walk-mesh place nearest p, same floor (+-150), clearance >= need (relaxed 60 -> 40 -> 25 as the roof pass did), >= gap from every place handed out."""
        nav = self.nav
        # the walk-mesh part of the nearest polygon on the same floor: the street (y 20) is a separate part from the building (home part)
        near = min((i for i in range(len(nav.pv)) if nav.ok[i] and abs(nav.mid[i][1] - p[1]) < 150.0), key=lambda i: math.dist((nav.mid[i][0], nav.mid[i][2]), (p[0], p[2])))
        cand = [c for c in nav.around(p, radius, nav.part[near], step=40.0, dy=300.0) if abs(c[1] - p[1]) < 150.0]
        if not cand:    # wide fallback: polygon middles of that part on the same floor (a spot far from the walkable roof strip)
            cand = [(nav.mid[i][0], nav.mid[i][1], nav.mid[i][2], i) for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == nav.part[near]
                    and abs(nav.mid[i][1] - p[1]) < 150.0 and math.hypot(nav.mid[i][0] - p[0], nav.mid[i][2] - p[2]) < 2500.0]
        for need_ in (need, 40.0, 25.0):
            ok = [c for c in cand if nav.clearance(c[0], c[1], c[2]) >= need_ and all(math.hypot(c[0] - q[0], c[2] - q[2]) >= gap for q in self.used)]
            if ok:
                ok.sort(key=lambda c: math.hypot(c[0] - p[0], c[2] - p[2]))
                out = (float(ok[0][0]), float(ok[0][1]), float(ok[0][2]))
                self.used.append(out)
                return out
        raise ValueError('no walk-mesh place near %s (radius %g, %d mesh cells)' % ([round(v) for v in p], radius, len(cand)))

    def cover_near(self, p, radius=700.0):
        """GUESS: a cover box's own position (snapped to the mesh) is a cover place. -> the nearest unused one, or the plain snapped place."""
        cs = [c for c in self.covers if abs(c[1] - p[1]) < 200.0 and math.hypot(c[0] - p[0], c[2] - p[2]) <= radius]
        cs.sort(key=lambda c: math.hypot(c[0] - p[0], c[2] - p[2]))
        for c in cs:
            try:
                return self.snap(c, gap=110.0)
            except ValueError:
                continue
        return self.snap(p, gap=110.0)


# ------------------------------------------------------------------ squad maker
class Fight:
    """Builds new squads / chains out of clones of the build's own nodes."""

    def __init__(self, B, places, log):
        self.B, self.sc, self.pl, self.log = B, B.sc, places, log
        self.M = KB.Maker()
        node = lambda path: self.sc.resolve(path)[0]
        self.n = dict(mod=node(MOD_FORM), rnd=node(RND_FORM), dfd=node(DEF_FORM), pos=node(POS_FORM), tim=node(KOW.TIMER_FORM), squad=node(R + SQ_FORM))
        self.clock = FED.clone_built(self.M, B, node(R + KB.SQUAD + 'Squad#02'), CLOCK)
        self.clock.ctrls = []
        self.M.place(self.clock, (0.0, 0.0, 0.0))
        self.tops = [self.clock]
        self.go = []
        self.pools = collections.defaultdict(list)
        for k in range(1, len(self.sc.nodes)):
            if self.sc.cls(k) != 'ZFFActor' or B.values(k).get('ZFFActor[0]') != 'Enemy':
                continue
            if not any(self.sc.p.key(nm) == 'ZSoldier' for nm, _b in self.sc.nodes[k]['ctrls']) or 'Bouncer' in str(B.values(k).get('ZLNKOBJ[2]')):
                continue
            self.pools[str(B.values(k).get('ZFFActor[1]')).split(BS)[-1]].append(k)

    # ---- rout pieces: each returns the path of the node it made
    def _z(self, parent, node, name, fields=None, cname=None):
        g = parent.add(FED.clone_built(self.M, self.B, node, name))
        self.M.place(g, (0.0, 0.0, 0.0))
        if fields is not None:
            self.M.set(g, cname, fields)
        return g

    def defend(self, top, me, name, posts, run=False, nxt=(), cover=False):
        """A Defend rout with one Pos per man (field 1), or ONE cover Pos in field 0 (cover=True, the stock 'pos_cover' form).  run: field 4 eDMS_Run (GUESS)."""
        d = self._z(top, self.n['dfd'], name)
        refs = []
        for j, c in enumerate(posts):
            pp = d.add(FED.clone_built(self.M, self.B, self.n['pos'], 'Pos#%02d' % (j + 1)))
            self.M.place(pp, c[:3])
            refs.append(me + BS + name + BS + 'Pos#%02d' % (j + 1))
        f = {0: refs[0] if cover else '', 1: [] if cover else refs, 2: 1, 3: 0, 4: 'eDMS_Run' if run else 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: list(nxt), 8: 1, 9: 0}
        self.M.set(d, 'DefendBehaviourRout', f)
        return me + BS + name

    def timer(self, top, me, name, secs, targets):
        t = self._z(top, self.n['tim'], name)
        self.M.set(t, 'TriggerDelay2', {0: float(secs), 4: list(targets)})
        return me + BS + name

    def modifier(self, top, me, name, tight=True, covers=True, nxt=()):
        m = self._z(top, self.n['mod'], name)
        # GUESS: field 9 defend distance, 15 cover use (eCOM_UseCovers); 14 vision stays NotSet (only eVIM_Factor_2_0 is proven, re/dm01_ai_cover_1025.md 11)
        self.M.set(m, 'SquadModifierBehaviour', {9: 'eDM_Tight' if tight else 'eDM_Loose', 14: 'eVIM_NotSet', 15: 'eCOM_UseCovers' if covers else 'eCOM_NotSet', 26: list(nxt)})
        return me + BS + name

    def random(self, top, me, name, lanes):
        r = self._z(top, self.n['rnd'], name)
        f = {5: [], 6: [], 7: [], 8: []}
        for i, p in enumerate(lanes[:4]):
            f[5 + i] = [p]
        self.M.set(r, 'RandomTrigger', f)
        return me + BS + name

    # ---- a whole new squad
    def squad(self, name, spec, f3, wake):
        """spec: dict(men=[(spawn, weapon_group)], face=(x,z), chain=callable(top, me, ctx) -> path of the first rout, leash)."""
        top = FED.clone_built(self.M, self.B, self.n['squad'], TOP + name)
        top.ctrls = [c for c in top.ctrls if self.M.p.key(c[0]) == 'ZSquadScript']
        self.M.place(top, (0.0, 0.0, 0.0))
        me = R + TOP + name
        self.M.set(top, 'ZSquadScript', {0: spec.get('leash', 'eStayBack'), 1: 'eAllTypes', 3: f3, **{j: [] for j in range(4, 19)}})
        first = spec['chain'](top, me)
        for j, (sp, wg) in enumerate(spec['men']):
            pool = [a for w in wg for a in self.pools.get(w, [])]
            if not pool:
                raise ValueError('no Enemy actor carries %s' % (wg,))
            a = pool[(len(self.go) * 3 + j) % len(pool)]
            grp = top.add(FED.clone_built(self.M, self.B, self.sc.parent[a], '%s_%02d' % (name, j + 1)))
            dx, dz = spec['face'][0] - sp[0], spec['face'][1] - sp[2]
            L = math.hypot(dx, dz) or 1.0
            self.M.place(grp, sp[:3], KB.rot9(dx / L, dz / L))
            grp.add(FED.clone_built(self.M, self.B, a))
        go = self._z(self.clock, self.n['tim'], 'Go_' + name)
        self.M.set(go, 'TriggerDelay2', {0: float(wake), 4: [first]})
        self.go.append(R + CLOCK + BS + 'Go_' + name)
        self.tops.append(top)
        return top


def plan_new(Fx, P, log):
    """The six new squads (positions all on the walk mesh, clearance >= CLEAR)."""
    sn = P.snap
    out = []
    # --- front rush: from the front lane into the foyer, then cover
    sp = [sn((FRONT_LANE[0] + dx, FRONT_LANE[1], FRONT_LANE[2] - dz), gap=110.0) for dx, dz in ((0, 0), (160, 80), (-160, 80))]
    land = [sn((FOYER[0] + dx, FOYER[1], FOYER[2] + dz), gap=110.0) for dx, dz in ((0, 0), (220, 60), (-200, 120))]
    cov = [P.cover_near(c) for c in land]

    def ch_rush(top, me):
        c = Fx.defend(top, me, '30_Cover', cov, run=True)
        t = Fx.timer(top, me, '20_Hold', 5.0, [c])
        return Fx.defend(top, me, '10_Rush', land, run=True, nxt=[t])
    out.append(('Rush', dict(men=[(s, SMG) for s in sp], face=(FOYER[0], FOYER[2]), leash='eUnleashed', chain=ch_rush), 0, 20.0))
    # --- floor 2 hold
    hp = [sn((F2_HOLD[0] + dx, F2_HOLD[1], F2_HOLD[2] + dz), gap=130.0) for dx, dz in ((0, 0), (260, -140), (-260, -120))]

    def ch_hold(top, me):
        m = Fx.modifier(top, me, '20_Mod_tight', True, True)
        return Fx.defend(top, me, '10_Hold', hp, nxt=[m])
    out.append(('F2_Hold', dict(men=[(s, RIFLE) for s in hp], face=(STAIRS_TOP[0], STAIRS_TOP[2]), chain=ch_hold), 0, 45.0))
    # --- floor 2 flank: spawn on the west end, run back along the route; RandomTrigger picks lane a or b
    fp = [sn((F2_WEST[0] + dx, F2_WEST[1], F2_WEST[2] + dz), gap=130.0) for dx, dz in ((0, 0), (200, 140), (-200, 120))]
    la = [sn((F2_MID[0] + dx, F2_MID[1], F2_MID[2] + dz), gap=130.0) for dx, dz in ((-250, 0), (0, 160), (250, 0))]
    lb = [sn((F2_MID[0] + dx, F2_MID[1], F2_MID[2] + dz), gap=130.0) for dx, dz in ((-250, 420), (0, 520), (250, 420))]

    def ch_flank(top, me):
        a = Fx.defend(top, me, '20_Lane_a', la, run=True, nxt=[Fx.modifier(top, me, '30_Mod', False, True)])
        b = Fx.defend(top, me, '20_Lane_b', lb, run=True, nxt=[Fx.modifier(top, me, '30_Mod_b', False, True)])
        r = Fx.random(top, me, '10_Pick', [a, b])
        return r
    out.append(('F2_Flank', dict(men=[(s, SMG) for s in fp], face=(F2_MID[0], F2_MID[2]), leash='eUnleashed', chain=ch_flank), 0, 70.0))
    # --- shotgun rushers
    sp2 = [sn((F2_HOLD[0] + dx, F2_HOLD[1], F2_HOLD[2] + dz), gap=130.0) for dx, dz in ((520, 200), (480, -200))]
    tg = [sn((STAIRS_TOP[0] + dx, STAIRS_TOP[1], STAIRS_TOP[2] + dz), gap=130.0) for dx, dz in ((-150, 180), (150, 280))]

    def ch_shot(top, me):
        m = Fx.modifier(top, me, '20_Mod_loose', False, False)
        return Fx.defend(top, me, '10_Rush', tg, run=True, nxt=[m])
    out.append(('F2_Shot', dict(men=[(s, SHOT) for s in sp2], face=(STAIRS_TOP[0], STAIRS_TOP[2]), leash='eUnleashed', chain=ch_shot), 0, 90.0))
    # --- loot room guards (in the world from load)
    lp = [sn((LOOT_CORRIDOR[0] + dx, LOOT_CORRIDOR[1], LOOT_CORRIDOR[2] + dz), gap=130.0) for dx, dz in ((0, 0), (-200, 140), (-200, -140))]

    def ch_loot(top, me):
        m = Fx.modifier(top, me, '20_Mod_tight', True, True)
        return Fx.defend(top, me, '10_Guard', lp, nxt=[m])
    out.append(('Loot', dict(men=[(lp[0], SHOT), (lp[1], RIFLE), (lp[2], RIFLE)], face=(1500.0, LOOT_CORRIDOR[2]), chain=ch_loot), 1, 0.1))
    return out


# ------------------------------------------------------------------ edits of existing squads
def men_of(sc, B, top):
    return [k for k in range(top, sc.end[top]) if sc.cls(k) == 'ZFFActor']


def edits(Fx, B, Jn_holder, P, log):
    """-> [(squad top path, defend path, {field: value-as-paths}) ...] and the new chain nodes (made into the Fx maker as extra tops)."""
    sc, M = B.sc, Fx.M
    plan = []
    node = lambda p: sc.resolve(R + p)[0]
    for i in range(1, 7):
        top = node('OldWaves!Wave_%d' % i)
        me = R + 'OldWaves!Wave_%d' % i
        posts = [tuple(B.at(k)) for k in range(top, sc.end[top]) if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#')]
        if not posts:
            raise ValueError('Wave_%d has no posts' % i)
        # new chain nodes live under a clone of the wave's own top, named Fight!W<i> (a separate top: the wave itself is edited only in the Defend's field 7)
        ctop = FED.clone_built(M, B, Fx.n['squad'], TOP + 'W%d' % i)
        ctop.ctrls = []
        M.place(ctop, (0.0, 0.0, 0.0))
        cme = R + TOP + 'W%d' % i
        if i in (1, 6):                      # hold: tight + covers after a short breath
            first = Fx.timer(ctop, cme, '10_Breath', 4.0, [Fx.modifier(ctop, cme, '20_Mod', True, True)])
        elif i in (2, 4):                    # run to cover boxes
            cov = [P.cover_near(c) for c in posts]
            first = Fx.timer(ctop, cme, '10_Breath', 6.0, [Fx.defend(ctop, cme, '20_Cover', cov, run=True, nxt=[Fx.modifier(ctop, cme, '30_Mod', True, True)])])
        elif i == 3:                         # push: deeper, loose
            deep = [P.snap((p[0] * 0.5 + STAIRS_TOP[0] * 0.5, p[1], p[2] * 0.5 + STAIRS_TOP[2] * 0.5), gap=110.0) for p in posts[:3]]
            first = Fx.timer(ctop, cme, '10_Breath', 20.0, [Fx.defend(ctop, cme, '20_Push', deep, run=True, nxt=[Fx.modifier(ctop, cme, '30_Mod', False, False)])])
        else:                                # 5: flank, two lanes
            la = [P.snap((p[0] - 450.0, p[1], p[2] + 150.0), gap=110.0) for p in posts[:3]]
            lb = [P.snap((p[0] + 450.0, p[1], p[2] + 150.0), gap=110.0) for p in posts[:3]]
            a = Fx.defend(ctop, cme, '30_Lane_a', la, run=True, nxt=[Fx.modifier(ctop, cme, '40_Mod_a', False, True)])
            b = Fx.defend(ctop, cme, '30_Lane_b', lb, run=True, nxt=[Fx.modifier(ctop, cme, '40_Mod_b', False, True)])
            first = Fx.timer(ctop, cme, '10_Breath', 12.0, [Fx.random(ctop, cme, '20_Pick', [a, b])])
        Fx.tops.append(ctop)
        plan.append((me + BS + '10_Defend', first, 'Wave_%d' % i))
    for i, kind in ((1, 'hold'), (2, 'push'), (3, 'flank')):
        top = node('OldWaves!Roof_R%d' % i)
        me = R + 'OldWaves!Roof_R%d' % i
        posts = [tuple(B.at(k)) for k in range(top, sc.end[top]) if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#')]
        ctop = FED.clone_built(M, B, Fx.n['squad'], TOP + 'Roof%d' % i)
        ctop.ctrls = []
        M.place(ctop, (0.0, 0.0, 0.0))
        cme = R + TOP + 'Roof%d' % i
        if kind == 'hold':
            first = Fx.timer(ctop, cme, '10_Breath', 5.0, [Fx.modifier(ctop, cme, '20_Mod', True, True)])
        elif kind == 'push':                 # 60 s later forward along the route (west), loose
            fwd = [P.snap((p[0] - 900.0, p[1], p[2] - 250.0), gap=110.0) for p in posts[:4]]
            first = Fx.timer(ctop, cme, '10_Wait', 60.0, [Fx.defend(ctop, cme, '20_Push', fwd, run=True, nxt=[Fx.modifier(ctop, cme, '30_Mod', False, False)])])
        else:                                # hold first, then slip to the other side
            side = [P.snap((p[0] - 350.0, p[1], p[2] - 600.0), gap=110.0) for p in posts[:4]]
            first = Fx.timer(ctop, cme, '10_Wait', 75.0, [Fx.defend(ctop, cme, '20_Side', side, run=True, nxt=[Fx.modifier(ctop, cme, '30_Mod', True, True)])])
        Fx.tops.append(ctop)
        plan.append((me + BS + '10_Defend', first, 'Roof_R%d' % i))
    for d, first, nm in plan:
        log('    edit %s: Defend field 7 -> %s' % (nm, first[len(R):]))
    return plan


# ------------------------------------------------------------------ the build
def build(src, dst, log=print, new=True, force=False):
    h_in = md5(src)
    if h_in != PIN and not force:
        raise ValueError('%s md5 %s is not the pinned %s (use --force to chain over another post-pass)' % (src, h_in, PIN))
    B = KB.Built(src)
    sc = B.sc
    if sc.resolve(R + CLOCK):
        shutil.copyfile(src, dst)
        log('already holds %s: copied unchanged' % CLOCK)
        return dict(unchanged=True, md5_out=md5(dst), md5_in=h_in)
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
    a0, s0 = L2.census(sc)
    nav = KB.Nav(A.nav, links=True)
    st = KB.stations(B, nav)
    P = Places(B, nav, st['home'])
    log('census before: %d actors / %d squads; %d cover boxes found' % (a0, s0, len(P.covers)))
    Fx = Fight(B, P, log)
    made = []
    if new:
        for name, spec, f3, wake in plan_new(Fx, P, log):
            Fx.squad(name, spec, f3, wake)
            made.append(dict(name=name, f3=f3, wake=wake, men=[[round(v) for v in sp[:3]] for sp, _w in spec['men']]))
            log('  new squad %s: %d men, f3 %d, wake %.1f s at %s' % (name, len(spec['men']), f3, wake, made[-1]['men'][0]))
    plan = edits(Fx, B, None, P, log)
    q, order = Fx.M.scene(Fx.tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'fight1105')
    # ---- edits of the existing squads: the Defend's field 7 gets the chain's first node (appended, never replaced)
    for dpath, first, nm in plan:
        k = Jn.resolve(dpath)
        if len(k) != 1:
            raise ValueError('%d nodes at %s' % (len(k), dpath))
        k = k[0]

        def fn(us, first=first):
            have = [Jn.p.key(t) for t in us[7][1:]]
            if first not in have:
                have.append(first)
            us[7] = kl_fa._refs(Jn, have)
        kl_fa.edit(Jn, k, AU.ctrl_of(Jn, k, 'DefendBehaviourRout'), fn)
    # ---- AIMonitor START list: the new Go timers
    km = Jn.resolve(KOW.MONITOR)[0]
    ci = AU.ctrl_of(Jn, km, 'AIMonitor')
    have = list(KOW.values(Jn, km, 'AIMonitor')[KOW.START_LIST])
    kl_fa.edit(Jn, km, ci, lambda us: AU.setv(Jn, us, KOW.START_LIST, have + [g for g in Fx.go if g not in have]))
    # the chain tops that only hold timers / routs of the existing squads need no START entry: the existing Defend's field 7 starts them
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    a1, s1 = L2.census(Jn)
    # ---- .gms / .buf
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ents_of = {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
        e.ref = nxt
        nxt += 1
        e.parent = parent
        e.kids = []
        (parent.kids if parent else A.roots).append(e)
        ents_of[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t in Fx.tops:
        ent(t, None)
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
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    items = []
    for t in Fx.tops:
        pts = [k.pos for k in t.kids if k.pos and k.pos != (0.0, 0.0, 0.0)] + [p.pos for k in t.kids for p in k.kids if p.pos and p.pos != (0.0, 0.0, 0.0)]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[ents_of[id(t)]] + 2, lo, hi))
    r3 = octn.rooms[0][3]
    octn.rooms[0][3] = O.join_trees(r3, O.build_tree(items, r3.origin, r3.scale))
    octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move:
        prm = bytearray(B['.prm'])
        tt, nn = struct.unpack_from('<II', prm, 0)
        old = set(octx.record_refs())
        for i in range(1, nn):
            off, size = struct.unpack_from('<II', prm, tt + 16 * i)
            if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', prm, off + 0x1c, move[v])
                    repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    newf = dict(B.files)
    newf[B.ext['.prp']], newf[B.ext['.gms']], newf[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    newf[B.ext['.oct']], newf[B.ext['.rmi']], newf[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        newf[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if newf[n] != B.files[n])
    repl = {B.ext[e]: newf[B.ext[e]] for e in changed}
    work = tempfile.mkdtemp(prefix='fight_')
    try:
        wz = os.path.join(work, os.path.basename(dst))
        KK.patch_zip(src, wz, repl)
        counts = []
        for zsrc in (src, wz):
            tmpd = tempfile.mkdtemp(prefix='fight_seal_')
            try:
                shutil.copyfile(zsrc, os.path.join(tmpd, os.path.basename(dst)))
                counts.append(BK.seal(tmpd, log=lambda *_: None))
            finally:
                KK.rmtree(tmpd)
        if counts[0] != counts[1]:
            raise ValueError('seal would move %d room list entries in the output, %d in the input' % (counts[1], counts[0]))
        problems = BK.reverify(work, log=lambda *_: None)
        wi = tempfile.mkdtemp(prefix='fight_in_')
        try:
            shutil.copyfile(src, os.path.join(wi, os.path.basename(dst)))
            base_problems = BK.reverify(wi, log=lambda *_: None)
        finally:
            KK.rmtree(wi)
        problems = [x for x in problems if x not in base_problems]
        if problems:
            raise ValueError('reverify: %s' % problems[:5])
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(wz, dst)
    finally:
        KK.rmtree(work)
    # ---- read back
    B2 = KB.Built(dst)
    s2 = B2.sc
    bad = []
    for n in B2.files:
        if n not in repl and B2.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if len(s2.resolve(R + CLOCK)) != 1:
        bad.append('no %s' % CLOCK)
    for dpath, first, nm in plan:
        d = s2.resolve(dpath)
        vals = [v for k, i, v in kl_fa.controllers(s2, 'DefendBehaviourRout') if k == d[0]]
        if not vals or first.lower() not in [str(x).lower() for x in vals[0][7]]:
            bad.append('%s: Defend field 7 does not name %s' % (nm, first))
    fa, fs = L2.census(s2)
    if (fa, fs) != (a1, s1):
        bad.append('census readback %s != %s' % ((fa, fs), (a1, s1)))
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep = collections.OrderedDict(md5_in=h_in, md5_out=md5(dst), members_changed=changed, census_before=[a0, s0], census_after=[a1, s1], entities_before=len(B.ents),
                                  entities=len(allents), added=len(order), slot_ids_moved=moved, prm_roots_repointed=repointed, new_squads=made,
                                  edited=[nm for _d, _f, nm in plan], room_sets=[str(pre), str(post)])
    log('  members %s; %d entities added (%d -> %d), %d slot ids renumbered, %d .prm roots re-pointed; census %d/%d -> %d/%d' % (
        ' '.join(changed), len(order), len(B.ents), len(allents), moved, repointed, a0, s0, a1, s1))
    return rep


def stage(src, out, new=True, force=False, doors=False, log=print):
    st = os.path.join(out, 'stage')
    KK.rmtree(st)
    os.makedirs(st)
    dst = os.path.join(st, 'F01_Main.zip')
    rep = build(src, dst, log, new, force)
    if rep.get('unchanged'):
        return rep
    if doors:
        rep['doors'] = stage_doors(dst, st, log)
    with open(os.path.join(st, 'install.py'), 'w', newline='\n') as fh:
        fh.write(KK.INSTALL_PY % dict(map='DM05A', zip='F01_Main.zip', tag=TAG, game=GAME, old=rep['md5_in'], new=rep['md5_out']))
    with open(os.path.join(st, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    log('staged %s  md5 %s (in %s)' % (st, rep['md5_out'], rep['md5_in']))
    return rep


def stage_doors(zp, st, log):
    """OPTIONAL, untested: a kick door in the one mesh doorway on the route (kl_interact_graft virtual host). Staged as stage/doors/F01_Main.zip."""
    import kl_interact_graft as IG
    B = KB.Built(zp)
    nav = KB.Nav(B.scene.nav, links=True)
    sc = KB.stations(B, nav)
    route = L2.Route(B, nav, sc['home'], sc['start_mid'])
    necks = IG.neck_targets(B, nav, 200, apart=300.0, detail=True)
    pick = []
    for x, z, y, gap, (ux, uz) in necks:
        near = [p for p in route.pts if abs(p[1] - y) < 120.0]
        if near and min(math.hypot(x - p[0], z - p[2]) for p in near) < 350.0:
            pick.append(('at', (x + ux * gap / 2.0, y - 0.0, z + uz * gap / 2.0), (-ux, 0.0, -uz)))
    if not pick:
        log('  doors: no mesh doorway on the route, nothing staged')
        return dict(doors=[])
    d = os.path.join(st, 'doors')
    os.makedirs(d, exist_ok=True)
    IG.build(zp, os.path.join(d, 'F01_Main.zip'), ext=0, doors=pick, log=lambda *_: None)
    return dict(doors=[[round(v) for v in p[1]] for p in pick], md5=md5(os.path.join(d, 'F01_Main.zip')))


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] != 'stage':
        print(__doc__)
        return 2
    src = opt('--src', LIVE)
    stage(src, opt('--out', OUT), new='--no-new' not in a, force='--force' in a, doors='--doors' in a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
