#!/usr/bin/env python3
"""
HASTA (M11_B) layer. STEP 3a: the doors and the opening (Doors, proof). STEP 3b: the Fragile Alliance layer (author module,
below the proof: spawns, loot, bounds, van, squads, wiring, finish, check, test). OFFLINE; nothing installed, no game.

    python kl_fa_hasta_layer.py test <out> [--keep] [--plan plan.json] [--no-ai] [--no-police] [--squads-awake] [--blast [S]] [--lock-wing]
        --blast [S]: ALSO the timer-driven corner blast (kl_fa_hasta_blast.py; S s after the round start, default 1.5). Without it nothing of it runs.
        --lock-wing: the loot wing (door block, bunker wall + check block) stays SHUT until the 6 hall squads are wiped out (or the backstop); see LOCK_WING.
        F07 + M11_B --campaign with Doors armed AND this module as the authored layer -> <out>/F07+M11_B campaign; finish(),
        check(). kl_fa_hasta.py `build` runs this, then lighten, wardrobe, compact (the MEASURED order, tooling 3.5).
    python kl_fa_hasta_layer.py check <folder> | finish <folder> | plan <bare-folder> <plan.json>

    python kl_fa_hasta_layer.py proof [<scratch>]
        Builds F07 + M11_B --campaign (kl_maps.one, --keep) into <scratch> (default C:/kl_scratch/hasta) with
        Doors armed, then reads the built level back and checks: every switch entity sits SINK_DY lower than in the
        campaign level (world y), its collision placements are gone from the .HVK, the wreck group and all its
        descendants are gone from the van lane. Writes <scratch>/proof.json. Check: stop if < 3 GB free on the disk.

Doors = a GENERIC copy of kl_fa_bank.Doors (the bank is not touched: its builds stay byte-identical). Differences:
  * nodes are matched BY NAME (+ an optional ancestor-name filter), never by path or REF: the graft renumbers both
    (re/hasta_fa.md step 2 item 1);
  * a spec may be a whole GROUP: the group node is sunk (its children follow in the .prp/.gms frames) and the REF ids of
    ALL its descendants go to the collision cut (the wreck: 40 nodes);
  * the sink distance is SINK_DY (world y), not the bank's -2500.
Mechanism (unchanged from the bank's, which unchanged from the study's build_open.py): kl_graft.build calls
kl_escape.repair / place_entities / cut_collision for a Dead Men map; for one build these three are wrapped.

OPENING IS BUILD-TIME (step 3a scope). The design's RUN-TIME beat (wing door block / bunker wall opening when the hall
squads are dead, locked loot until then) is NOT built: it needs a controller that sinks a node at run time, which no
note shows working (re/hasta_fa.md section 2 and 8). The four geometry switches are simply open from the first tick, so the
loot wing is reachable at once (GUESS: acceptable for a first playable; the bunker squads are still in the way).
Not touched: SO0201_M11_CornerBroken_01 and SI0100_M11_BarricadeB_Broken01 (the 'after' models, hidden in the campaign by
a mechanism not read here; whether their collision is live while hidden is NOT known - the proof reports their boxes).
"""
import collections
import contextlib
import json
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SINK_DY = -4000.0         # GUESS: the study's figure (re/hasta_fa.md step 3); Hasta's lowest floor is the square, y -90 (craters)
# (name of the node in the campaign level, ancestor-name filter or None, what). All matched BY NAME in the joined scene.
SWITCHES = [
    ('ColiObj_Obj_Roadblock_01', 'End_Corridor', 'loot wing door block'),
    ('SI0100_M11_BarricadeB_01', None, 'bunker wall'),
    ('M11B_OYCHECK_BEFORE01', None, 'bunker check block'),
    ('SO0201_M11_Corner_01', None, 'Capitol corner (whole)'),
    ('SO0201_M11_BarricadeXX_01', None, 'stair barricade'),
]
WRECK = 'Vehicles!V_CUB_Chevy_B_Static_00#12'     # a whole group: node + descendants (kl_fa_hasta.VAN_TRY['wreck'])


def _ancestors(sc, k):
    out, k = [], sc.parent[k]
    while k > 0:
        out.append(sc.names[k]); k = sc.parent[k]
    return out


def switches():
    """SWITCHES as this build sinks them: all of them, or without the LOCKED ones under LOCK_WING (they open at run time)."""
    return [sw for sw in SWITCHES if not (LOCK_WING and sw[0] in LOCKED)]


def subtree(sc, k):
    """Node k and its descendants (node indices; scene order keeps a subtree contiguous)."""
    end = sc.end[k]
    return list(range(k, end))


class Doors:
    """See the module docstring. arm(specs=SWITCHES, groups=(WRECK,), dy=SINK_DY) puts the wrappers in; they take
    themselves out after cut() (or when place() finds nothing to cut)."""
    real, state = None, None
    specs, groups, dy = SWITCHES, (WRECK,), SINK_DY

    @classmethod
    def sunk(cls, sc):
        """-> [(node, what)] the nodes this build takes out, matched by name in the joined scene `sc`. Each spec must
        match exactly ONE node (a name seen twice is an error, not a guess)."""
        out = []
        for nm, anc, what in cls.specs:
            hit = [k for k in range(1, len(sc.names)) if sc.names[k] == nm
                   and (anc is None or any(anc in a for a in _ancestors(sc, k)))]
            if len(hit) != 1:
                raise KeyError('%s: %d nodes named %s (filter %s)' % (sc.label, len(hit), nm, anc))
            out.append((hit[0], what))
        for nm in cls.groups:
            hit = [k for k in range(1, len(sc.names)) if sc.names[k] == nm]
            if len(hit) != 1:
                raise KeyError('%s: %d nodes named %s' % (sc.label, len(hit), nm))
            out.append((hit[0], 'wreck group'))
        return out

    @classmethod
    def arm(cls, log=print, specs=None, groups=None, dy=None):
        import kl_escape
        if specs is not None:
            cls.specs = specs
        if groups is not None:
            cls.groups = tuple(groups)
        if dy is not None:
            cls.dy = dy
        if cls.real is None:
            cls.real = (kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision)
            kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision = cls.repair, cls.place, cls.cut
        cls.state = {'sink': {}, 'old': {}, 'prp_w': {}, 'tree': {}, 'what': {}}

    @classmethod
    def disarm(cls):
        import kl_escape
        if cls.real is not None:
            kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision = cls.real
            cls.real = None

    @staticmethod
    def prp_frame(sc, k):
        """World rotation (rows) of node k's PARENT frame from the .prp chain, and that parent's world place."""
        import kl_fa
        import kl_prpjoin as J
        chain, j = [], sc.parent[k]
        while j > 0:
            chain.append(j); j = sc.parent[j]
        Rm, T = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], [0.0, 0.0, 0.0]
        for j in reversed(chain):
            lab = J.labels('dd', sc.cls(j))
            v = kl_fa.node_values(sc, j)
            t, r = v[lab.index('ZGEOM[2]')], v[lab.index('ZGEOM[1]')]
            T = [T[a] + sum(Rm[a][b] * t[b] for b in range(3)) for a in range(3)]
            m = [r[6:9], r[3:6], r[0:3]]
            m = [[m[b][a] for b in range(3)] for a in range(3)]
            Rm = [[sum(Rm[a][c] * m[c][b] for c in range(3)) for b in range(3)] for a in range(3)]
        return Rm, T

    @classmethod
    def prp_world(cls, sc, k):
        import kl_fa
        import kl_prpjoin as J
        Rm, T = cls.prp_frame(sc, k)
        t = kl_fa.node_values(sc, k)[J.labels('dd', sc.cls(k)).index('ZGEOM[2]')]
        return tuple(T[a] + sum(Rm[a][b] * t[b] for b in range(3)) for a in range(3))

    @classmethod
    def repair(cls, sc, log=print):
        import kl_fa
        import kl_prpjoin as J
        import kl_fa_author as A
        done = cls.real[0](sc, log)
        st, tilted = cls.state, 0
        for k, what in cls.sunk(sc):
            lab = J.labels('dd', sc.cls(k))
            Rm, _T = cls.prp_frame(sc, k)
            d = [Rm[1][a] * cls.dy for a in range(3)]    # R^T (0, dy, 0): the world's y move in the parent's frame
            tilted += abs(d[1] - cls.dy) > 0.01
            old = list(kl_fa.node_values(sc, k)[lab.index('ZGEOM[2]')])
            new = [old[a] + d[a] for a in range(3)]
            before = cls.prp_world(sc, k)
            kl_fa.edit(sc, k, None, lambda us, lab=lab, new=new: A.setv(sc, us, lab.index('ZGEOM[2]'), new))
            st['sink'][k], st['old'][k], st['prp_w'][k] = cls.dy, old, (before, cls.prp_world(sc, k))
            st['tree'][k] = subtree(sc, k)
            st['what'][k] = what
        log('  kl_fa_hasta_layer: doors: %d nodes sunk by %g (world y) in the joined .prp (matched by name); %d in a parent frame '
            'with another y axis than the world\'s' % (len(st['sink']), -cls.dy, tilted))
        return done

    @classmethod
    def place(cls, sc, ents, done, log=print):
        import kl_fa_bank as B
        st = cls.state
        world_of = B.world_of
        before = {k: world_of(ents[k - 1])[0] for k in st['sink']}
        for k in st['sink']:
            e = ents[k - 1]
            t = struct.unpack('<3f', e.trans[:12])
            if max(abs(before[k][a] - st['prp_w'][k][0][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: world place by the .gms %s, by the .prp %s' % (sc.names[k], before[k], st['prp_w'][k][0]))
            Rm = world_of(e.parent)[1] if e.parent is not None else [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
            done['move'][k] = tuple(t[a] + Rm[1][a] * cls.dy for a in range(3))      # place_entities writes it into the record
        refs = set(cls.real[1](sc, ents, done, log))
        for k in st['sink']:                            # the node and every descendant: their placements leave the .HVK
            refs |= {ents[j - 1].ref for j in st['tree'][k]}
        st['refs'] = sorted(refs)
        for k in sorted(st['sink']):
            after = world_of(ents[k - 1])[0]
            if abs(after[0] - before[k][0]) > 0.5 or abs(after[2] - before[k][2]) > 0.5 or abs(after[1] - before[k][1] - cls.dy) > 0.5:
                raise ValueError('%s moved %s -> %s, not straight down by %g' % (sc.names[k], before[k], after, -cls.dy))
            if max(abs(after[a] - st['prp_w'][k][1][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: after the move the .gms says %s, the .prp %s' % (sc.names[k], after, st['prp_w'][k][1]))
        st['names'] = {k: sc.names[k] for k in st['sink']}
        log('  kl_fa_hasta_layer: doors: %d entities moved in the .gms, %d REF ids (with descendants) go to cut_collision' % (
            len(st['sink']), len(refs)))
        if not refs:
            cls.disarm()
        return refs

    @classmethod
    def cut(cls, hvk, refs, log=print):
        import kl_hvk
        try:
            mine = collections.Counter(s.type for s in hvk.shapes for i in s.inst if kl_hvk.ref(i) in refs)
            h = cls.real[2](hvk, refs, log)
            left = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) in refs)
            if left:
                raise ValueError('%d placements are left in the .HVK under the %d REF ids taken out' % (left, len(refs)))
            cls.state['cut'] = dict(mine)
            log('  kl_fa_hasta_layer: doors: %d placements (by shape type %s) were under the %d REF ids; none is left' % (
                sum(mine.values()), dict(mine), len(refs)))
            return h
        finally:
            cls.disarm()


@contextlib.contextmanager
def doors(log=print, **kw):
    """For a script that builds: the wrappers of Doors for the length of the block, taken out whatever happens."""
    Doors.arm(log, **kw)
    try:
        yield Doors
    finally:
        Doors.disarm()


# ------------------------------------------------------------------ the proof on a scratch graft
def proof(scratch='C:/kl_scratch/hasta', keep=False):
    import kl_hvk
    import kl_maps
    import kl_map_escape as E
    import kl_fa_hasta as H
    scratch = os.path.abspath(scratch)
    os.makedirs(scratch, exist_ok=True)
    free = shutil.disk_usage(scratch).free / 1e9
    if free < 3.0:
        raise SystemExit('only %.1f GB free under %s: stop' % (free, scratch))
    folder = os.path.join(scratch, 'F07+M11_B')
    with doors() as D:
        res = kl_maps.one(scratch, H.HOST, H.LEVEL, keep=True, campaign=True)
        state = dict(D.state)
    out = dict(built=bool(res.get('ok')), free_gb_before=round(free, 1))
    if not state.get('sink'):
        out['error'] = 'Doors found nothing (state empty): the build did not call kl_escape.repair'
        json.dump(out, open(os.path.join(scratch, 'proof.json'), 'w'), indent=1)
        print(json.dumps(out)); return 1
    # --- read back: the built level vs the campaign level, matched BY NAME
    F = E.Level(folder)
    C = E.Level(H.DM_ZIP)
    fsc, csc = F.sc, C.sc
    refs = set(state['refs'])
    here = {r: i for i, r in enumerate(state['refs'])}
    rows, ok = [], True
    for k, nm in sorted(state['names'].items()):
        hits = [i + 1 for i, e in enumerate(F.ents) if e.name.decode('latin1') == nm]
        # the built level may hold the name more than once (a clone): take the one whose REF is in the cut set
        mine = [j for j in hits if F.ents[j - 1].ref in refs]
        camp = [i + 1 for i, e in enumerate(C.ents) if e.name.decode('latin1') == nm]
        row = dict(name=nm, what=state['what'][k], built_hits=len(hits), cut_hits=len(mine), campaign_hits=len(camp))
        if len(mine) == 1 and camp:
            pb = F.place(mine[0])
            pc = C.place(camp[0])
            row.update(world_built=[round(v) for v in pb], world_campaign=[round(v) for v in pc])
            row['dy'] = round(pb[1] - pc[1])
            row['ok_dy'] = abs(row['dy'] - SINK_DY) < 2
        else:
            row['ok_dy'] = False
        ok &= row['ok_dy']
        rows.append(row)
    out['switches'] = rows
    # collision: no placement of the cut set in the built .HVK, and the count kept stays sane
    left = sum(1 for s in F.hvk.shapes for i in s.inst if kl_hvk.ref(i) in refs)
    out['hvk_placements_left_under_cut_refs'] = left
    out['hvk_cut'] = state.get('cut')
    ok &= (left == 0)
    # the van road: the lane test of VAN_TRY with no `clear` list must now plan without faults
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        P = E.van_plan_points(folder, arrive=H.VAN_TRY['arrive'], stop=H.VAN_TRY['stop'], leave=H.VAN_TRY['leave'],
                              heading=None, at='origin', clear=[])
    out['van_plan_without_clear'] = dict(faults=P['faults'], lin=P.get('lin'), lout=P.get('lout'), stop=P.get('stop'))
    ok &= not P['faults']
    # the 'broken' siblings: report only
    out['broken_siblings_report'] = [dict(name=n, hits=sum(1 for e in F.ents if e.name.decode('latin1') == n))
                                     for n in ('SO0201_M11_CornerBroken_01', 'SI0100_M11_BarricadeB_Broken01')]
    out['ok'] = bool(ok)
    json.dump(out, open(os.path.join(scratch, 'proof.json'), 'w'), indent=1)
    print(json.dumps(out)[:1500])
    if not keep:                                        # delete the intermediate (the big archive); proof.json stays
        shutil.rmtree(folder, ignore_errors=True)
    return 0 if ok else 1




# =====================================================================================================================
# STEP 3b: THE FRAGILE ALLIANCE LAYER (an authoring module: kl_graft.AUTHOR_NAMES). Copy of the structure of kl_fa_v2_park.py
# (not imported: another session owns it), HOST F07, LEVEL M11_B, Hasta's own tables. MEASURED = read from the real files
# (re/hasta_fa.md steps 1-3a); every other number is a GUESS and says so.
# =====================================================================================================================
import math
import kl_graft
import kl_fa
import kl_maps
import kl_prpjoin as J
import kl_fa_author as A
import kl_fa_bank as BK
import kl_map_escape as ESC
import kl_fa_hasta_blast as HB

HOST, LEVEL = 'F07', 'M11_B'
TITLE = 'Hasta (campaign)'
R = 'ROOT\\'
put, values, facing, world_of = BK.put, BK.values, BK.facing, BK.world_of
KNOWN = (('stream clips are not in the merged stream file', 'the campaign level\'s music and ambience beds have no record in the installed PC_Def.str '
          '(a later stream-file step): those sounds are silent, nothing else'),
         ("the game's table has 73728", "the chunk table (74,763) is above the game's 73,728 only BEFORE compaction: kl_chars.py compact (the chain's last stage) brings it under; "
          "kl_fa_hasta.py build checks the compacted result"),)
NO_AI = False                           # True ('--no-ai'): no squad of the campaign stays
SQUADS_AWAKE = False                    # True ('--squads-awake'): ZSquadScript field 3 = 1 on all (fall-back if naming the start child does not wake a squad)
POLICE_ARRIVE = True                    # False ('--no-police')
BLAST_AT = None                         # seconds ('--blast [S]'): the timer-driven corner blast of kl_fa_hasta_blast.py, S s after the round start (default 1.5). None = off (the build is then unchanged)
VOICE = True
M_DROP = ()                             # what the campaign pre-pass drops on top of its own rule (GUESS: nothing; the first build's verify says)
LOCK_WING = False                       # True ('--lock-wing'): the loot wing is LOCKED until the hall squads are dead (or the backstop). False = build unchanged
# LOCK_WING (re/hasta_fa.md, handover 'locked loot'). The run-time beat the design asked for, made the Retomoto main-room way (kl_fa_author: squads' 'dead' list -> TriggerCounter
# -> a geometry switch) with the CAMPAIGN's own switch for the bunker: M11_B's top-level `GeomDeactivatorSandbags` (a DeactivateGeom, 'AITrigger') already names the bunker wall
# and its check block; the loot wing door block's own deactivator (`GeomDeactivator_Coli`) sits inside the LastSeven squad that is not kept, so its target is added to the
# list of the kept one. No new geometry (the .prm does not grow), no new controller kind. The three nodes are NOT sunk at build time; their HVK placements stay.
LOCKED = ('ColiObj_Obj_Roadblock_01', 'SI0100_M11_BarricadeB_01', 'M11B_OYCHECK_BEFORE01')       # names of SWITCHES that stay shut until the beat
LOCK_OPEN = (r'End_Corridor_01a\ColiObj_Obj_Roadblock_01', 'SI0100_M11_BarricadeB_01', 'M11B_OYCHECK_BEFORE01')   # kl_route.stations(opened=): path pieces of the LOCKED nodes (the rooftop's Roadblock is another)
OPENER = '070_CapitolioInside!Enemies!GeomDeactivatorSandbags'      # the campaign's DeactivateGeom (top level), kept by campaign_names under the flag
COUNTER = 'Gameplay!020_Loot!FollowPlayers!TriggerCounter'          # F07's spare TriggerCounter (Retomoto's loot counter; single top-level ZBoxPrimitive), kept under the flag

EAST, WEST, SOUTH = (1.0, 0.0), (-1.0, 0.0), (0.0, -1.0)
HALL_Y, SQUARE_Y = 800.0, 20.0
# ------------------------------------------------------------------ places (MEASURED in design_read.json unless GUESS)
# START: the design's row x 33,900..34,000, z 29,900..30,900, floor y 800 (3 probes), facing +x. 2 columns x 4 rows. GUESS: the grid
START = [(float(x), HALL_Y, float(z)) for z in (29950, 30250, 30550, 30850) for x in (33900, 34000)]
TRAITOR = [(33700.0, HALL_Y, float(z)) for z in (30000, 30300, 30600, 30900)]                        # GUESS: 3 m behind the row
TEAM_MERC = [(float(x), HALL_Y, float(z)) for z in (30050, 30350, 30650, 30950) for x in (33780, 33840)]   # GUESS
WING_DOOR = (39350.0, HALL_Y, 31335.0)      # MEASURED: door block x 39,458..39,754, z 31,295..31,374; corridor starts x 39,300
HOLE = (32095.0, 888.0, 29022.0)            # MEASURED: the Capitol corner marker
GALLERY = (28380.0, 840.0, 29370.0)         # MEASURED
STAIR_TOP = (27540.0, 470.0, 30193.0)       # MEASURED
STAIR_FOOT = (26667.0, 20.0, 27758.0)       # MEASURED
# MEASURED (kl_route stations on the built level, 2026-10-17): the door point itself and its first 80 m stand in Collapsed_Walls_001/002; these 4 are on the mesh, in nothing, reached from START
STAGE_B = [(float(x), HALL_Y, float(z)) for x, z in ((39430, 31415), (39510, 31415), (39430, 31495), (39510, 31335))]
STAGE_C = [(STAIR_TOP[0] + dx, STAIR_TOP[1], STAIR_TOP[2] + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]
STAGE_D = [(STAIR_FOOT[0] + dx, STAIR_FOOT[1], STAIR_FOOT[2] + dz) for dx, dz in ((0, 0), (80, 0), (0, 80), (80, 80))]
# the dead's police come back on the square, east of the stair foot's line, well off the van's lane (z 21,800). GUESS
AFTER_DEATH = [(27800.0 + 150.0 * i, SQUARE_Y, 25600.0) for i in range(7)]
BODIES = [(27700.0 + 120.0 * i, SQUARE_Y, 26300.0) for i in range(8)]


def snap_mesh(mesh, p):
    """p with the navigation mesh's height under it (p itself when the mesh has nothing there)."""
    hit = mesh.on(*[float(v) for v in p]) if mesh is not None else None
    return (float(p[0]), float(hit[1]), float(p[2])) if hit else (float(p[0]), float(p[1]), float(p[2]))


# ------------------------------------------------------------------ loot: 16 places (MEASURED: the 11 case + 5 painting places of the wing, y 800)
# F07's drop pool holds 108 (ALL) + 25 (TM_ONLY) top-level stacks (MEASURED, stock F07): 16 places fit with 117 to spare.
CASES = [(39360, 31015), (39550, 31915), (39724, 31537), (40200, 31365), (40200, 32465), (40800, 31675), (40800, 32155),
         (42020, 31430), (42020, 32390), (42620, 31260), (42620, 32560)]
PAINTINGS = [(39900, 31015), (40500, 32365), (40500, 31465), (41400, 31615), (41400, 32215)]
WING_AXIS_Z = 31900.0                   # GUESS: the wing's middle line (corridor z 31,000..32,500, end room 30,700..33,300)
LOOT_BESIDE = 110.0                     # GUESS: a case lies this far from its display case towards the wing's middle line (inside the glass it would clip the pedestal)
# MEASURED (kl_route stations --near 125 from START, grid probe): the three paintings that the fixed 110 shift left 71..98 off the mesh and
# unreachable (the corridor floor there starts at z ~31,380; the wall is at x >= 39,900) -> nearest reached mesh point, absolute (x, z)
LOOT_FIX = {(39900, 31015): (39800, 31125), (40500, 32365): (40400, 32255), (40500, 31465): (40400, 31575)}
LOOT = []
for _i, (_x, _z) in enumerate(CASES + PAINTINGS):
    _dz = LOOT_BESIDE if _z < WING_AXIS_Z else -LOOT_BESIDE
    _case = _i < len(CASES)
    _x, _z = LOOT_FIX.get((_x, _z), (_x, _z + _dz))
    LOOT.append(((float(_x), HALL_Y, float(_z)), float((37 * _i) % 180 - 90), 150000 if _case else 300000,
                 'display case' if _case else 'painting'))      # GUESS: values 11 x 150,000 + 5 x 300,000 = 3.15 million; turns
LOOT_REACH = 125.0                      # TriggerBox2 radius (kl_escape.REACH)
CASE = 'dm'                             # the prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, as the club's and the park's
POOL_ALL = 8                            # of the 16: this many from the ALL pool (the park's 8 / 7 split), the rest TM_ONLY

# ------------------------------------------------------------------ level bounds: x/z rectangles OUTSIDE the playable area (GUESS: just beyond the measured extents)
# playable: hall x 28,200..40,260, wing to x 43,600, gallery + side stair x 26,470..29,600, square x 21,100..31,500 z 21,350..28,000 (design_read.json)
BOUND_Y = (1200.0, 1800.0)              # centre, half extent: y -600 .. 3000 (the craters go to -90, the hall roof is about 2100)
BOUNDS = {      # group: (bound rect xmin, xmax, zmin, zmax), (warn rect), why
    '040_LevelBound_AlleyTop': ((43900, 44900, 28500, 34500), (43700, 44900, 28500, 34500), 'behind the end room (x 43,600)'),
    '030_LevelBound_StreetLeft': ((20000, 20900, 21000, 28500), (20000, 21100, 21000, 28500), 'west of the square, behind the rubble (the campaign\'s own bound stands at x 21,200)'),
    '030_LevelBound_StreetRight': ((20800, 31600, 19800, 20800), (20800, 31600, 19800, 21000), 'south of the square (road edge z 21,100)'),
    '040_LevelBound_AlleyRight': ((32000, 33000, 20800, 28200), (31900, 33000, 20800, 28200), 'east of the square beyond the roadblock line (x 31,900); the hole to the hall is at z 28,500+'),
}
PARK = (0.0, -60000.0, 0.0)
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyLeft') for b in ('Bound', 'Warn01', 'Warn02')]


def _box(rect):
    x0, x1, z0, z1 = rect
    return ((x0 + x1) / 2.0, BOUND_Y[0], (z0 + z1) / 2.0), (abs(x1 - x0) / 2.0, BOUND_Y[1], abs(z1 - z0) / 2.0)


def in_rect(p, rect):
    return rect[0] <= p[0] <= rect[1] and rect[2] <= p[2] <= rect[3]


def _bounds_place():
    out = collections.OrderedDict()
    for g, (b, w, why) in BOUNDS.items():
        c, h = _box(b)
        out['Specials!LevelBound!%s!Bound' % g] = (c, None, h, 'GUESS: ' + why)
        c, h = _box(w)
        for n in ('Warn01', 'Warn02'):
            out['Specials!LevelBound!%s!%s' % (g, n)] = (c, None, h, 'GUESS: warn from the playable side')
    return out


# ------------------------------------------------------------------ the host's layer (F07): the same role objects the park uses (HOST is the same level)
FF = 'Gameplay!010_FirstFight!'
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'start timer': FF + 'RivalMercs!Timer',
        'backstop': FF + 'RivalMercVan!Timer',
        'walk box': FF + 'tb_LEFT_TheySpotYou',                          # the wing's door -> the wing guards
        'floor box': FF + 'tb_RIGHT_TheySpotYou',                        # the stair's top -> the street squads, the alarm, the gate
        'gate': 'Gameplay!RunToEscape!RunToEscapeGate',
        'van on': FF + 'Shutters!GeomActivator_TearGas_LEFT',
        'van timer': FF + 'RivalMercs!DisableVisionBlocker!Timer',
        'reset hide': FF + 'RivalMercs!DisableVisionBlocker!GeomDeactivator',
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel'}
GATE_WAYS = ('Way#01', 'Way#02')
START_AT = 2.0                          # s from the round-start event to the hall squads. GUESS (as the park's)
BACKSTOP_AT = 300.0                     # s: the police come whatever the crew did. GUESS (a longer route than the park's)
VAN_DELAY = 8.0                         # s from the alarm to the van's show and the police. GUESS
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'
LINES = {17: 'Multiplayer/F06/ReachlootArea_01_R', 18: 'Multiplayer/F09/MissionReminder_02_R', 19: 'Multiplayer/F06/MissionReminder_01_R',
         20: 'Multiplayer/F06/ReachlootArea_01_R', 127: 'Multiplayer/F06/ReachlootArea_01_R', 130: 'Multiplayer/F04/ExitLootArea_01_R',
         136: 'Multiplayer/F06/MissionReminder_01_R', 137: 'Multiplayer/F09/MissionReminder_02_R'}
START_KEY = 'AllLevels/Interface/Online/GameStart/M11B_%s_Start'
TEXTS = {START_KEY % 'FA': 'The tank shell has opened the Capitol. Take the paintings and cases in the east wing, fight back through the hall and down the side stair, then run the square to the van.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'The tank shell has opened the Capitol. Take the paintings and cases in the east wing, fight back through the hall and down the side stair, then run the square to the van.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}

# ------------------------------------------------------------------ the van on the square (MEASURED trial: 0 faults, lin 2,200, lout 4,400, stop (25600, 2, 21800))
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'
ROAD = dict(arrive=[(23400.0, 0.0, 21800.0), (24500.0, 0.0, 21800.0)], stop=(25600.0, 0.0, 21800.0),
            leave=[(29100.0, 0.0, 21800.0), (30600.0, 0.0, 21800.0)], at='origin', heading=None, cam=None)
# heading None on purpose: with 270 the planner said 'heads 90' (re/hasta_fa.md step 2 item 4; the reason is still unexplained)
PLAN = None
NO_PLAN = 'kl_fa_hasta_layer: the van has no plan: build with \'kl_fa_hasta_layer.py test <out>\' or kl_fa_hasta_layer.build()'
BOARD_FALLBACK = (25000.0, 20.0, 21800.0)     # about the standing van's rear doors; prepare_host takes PLAN['board'] once there is a plan
LANE_CLEAR = 250.0                      # no spawn point, man or the marker nearer than this to the van's drive. GUESS (as the park's)
FED_CLEAR = 1000.0                      # no AFTER_DEATH point or police body nearer than this to the boarding place
BOARD_NEAR = 30.0
MAN_OFF, MAN_IN = 60.0, 15.0


def board():
    return PLAN['board'] if PLAN else BOARD_FALLBACK


def _spawn():
    """ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing)."""
    b = board()
    return {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (AFTER_DEATH, (0, 0, 0), b),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (30, 0, 20), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (30, 0, 20), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, 40), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (AFTER_DEATH, (0, 0, 0), b),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (TEAM_MERC, (0, 0, 0), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), EAST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), WEST),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (40, 0, 40), SOUTH),
            'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (AFTER_DEATH, (0, 0, 0), b)}


def _fixed():
    wing = (41500.0, 900.0, 31800.0)
    t = collections.OrderedDict([
        ('FASpecials!POI!Trigger_POI_TheLootArea', (wing, None, (2300, 150, 1500), 'GUESS: the whole wing (it starts the loot marker\'s timer)')),
        ('FASpecials!POI!POI_TheLootArea', ((41000.0, 1000.0, 31800.0), None, None, 'over the wing')),
        ('FASpecials!PIP!EnterLootArea', (wing, None, (2300, 150, 1500), 'the wing: AI heisters\' first stage is inside this box')),
        ('FASpecials!PIP!ExitLootArea', ((WING_DOOR[0] - 150, 900.0, WING_DOOR[2]), None, (60, 150, 450), 'GUESS: a plane at the wing\'s mouth, after the last loot')),
        ('Specials!LevelSpeak!TriggerBox', ((HOLE[0], 950.0, HOLE[2]), None, (300, 150, 300), 'GUESS: the corner hole (the crew comes out of the hall)')),
        ('Specials!LevelSpeak!OnlineSpeakTrigger_01', ((HOLE[0], 950.0, HOLE[2]), None, None, 'with its trigger box')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A', ((36500.0, 1700.0, 31800.0), None, None, 'GUESS: the hall, high')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A', ((34000.0, 900.0, 30400.0), None, None, 'the START rows')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B', ((38200.0, 1500.0, 31300.0), None, None, 'GUESS: the hall before the wing')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B', (WING_DOOR, None, None, 'GUESS')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C', ((28900.0, 1300.0, 29900.0), None, None, 'GUESS: the gallery')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C', (STAIR_TOP, None, None, 'GUESS')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D', ((26700.0, 700.0, 29200.0), None, None, 'GUESS: over the stair')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D', (STAIR_FOOT, None, None, 'GUESS')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police', ((27200.0, 900.0, 27300.0), None, None, 'GUESS: the stair foot')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police', ((28000.0, 100.0, 25500.0), None, None, 'GUESS')),
        ('FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA', ((27200.0, 900.0, 27300.0), None, None, 'GUESS')),
        ('FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA', ((28000.0, 100.0, 25500.0), None, None, 'GUESS')),
        # team mode: the respawn stage moves when a criminal passes these (GUESS: the wing's mouth, the stair's top, the stair's foot)
        ('FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B', (WING_DOOR, None, (250, 150, 450), 'GUESS: the wing\'s mouth')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C', (STAIR_TOP, None, (300, 150, 300), 'GUESS: the stair\'s top')),
        ('FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D', (STAIR_FOOT, None, (300, 150, 300), 'GUESS: the stair\'s foot')),
        ('Specials!JumpPoints!01_Start', (START[2], EAST, None, 'the hall')),
        ('Specials!JumpPoints!02_MarketMain', (WING_DOOR, EAST, None, 'the wing\'s mouth')),
        ('Specials!JumpPoints!03_MarketOrange', ((42000.0, HALL_Y, 31900.0), EAST, None, 'the end room')),
        ('Specials!JumpPoints!04_LootWarehouse', (HOLE, WEST, None, 'the corner hole')),
        ('Specials!JumpPoints!05_MarketGreen', (STAIR_FOOT, SOUTH, None, 'the stair\'s foot')),
    ])
    t.update(_bounds_place())
    return t


WALK_BOX = ((WING_DOOR[0] + 150.0, 900.0, WING_DOOR[2]), (350.0, 150.0, 450.0))        # GUESS: across the wing's mouth
FLOOR_BOX = ((STAIR_TOP[0], STAIR_TOP[1] + 100.0, STAIR_TOP[2]), (350.0, 150.0, 350.0))   # GUESS: the stair's top


def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT bare F07 + M11_B folder WITH THE DOORS (the wreck gone). A fault is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_fa_hasta_layer: no van on ROAD: %s' % '; '.join(P['faults']))
    return P


def plan_of(path):
    P = json.load(open(path, encoding='utf-8'), object_pairs_hook=collections.OrderedDict)
    P = P.get('plan', P)
    lack = [k for k in ('path', 'lin', 'lout', 'wait', 'stop', 'end', 'board', 'cam', 'points') if k not in P]
    if lack or P.get('faults'):
        raise ValueError('%s is no plan of the van without a fault (lacks %s; faults %s)' % (path, lack, P.get('faults')))
    road = {k: [list(map(float, p)) for p in v] if k in ('arrive', 'leave') else list(map(float, v)) if k == 'stop' else v for k, v in ROAD.items()}
    if any(P['points'].get(k) != v for k, v in road.items()):
        raise ValueError('%s is a plan of other way points than ROAD: %s' % (path, {k: P['points'].get(k) for k in road if P['points'].get(k) != road[k]}))
    return P


def lay_van(P):
    global PLAN
    PLAN = P
    return P


def van_path():
    return R + VAN + '\\' + VAN_GROUP


def place_now():
    """_fixed() + the objects that hang on the van's boarding place (the exit box, the escape-area triggers, the marker)."""
    t = collections.OrderedDict(_fixed())
    b = board()
    mark = (b[0], b[1] + 188.0, b[2] + 350.0)       # GUESS: 350 north of the boarding place, off the drive (z 21,800); check() measures the distance
    box = ((b[0], b[1] + 200.0, b[2]), None, (450.0, 300.0, 450.0), 'GUESS: round the van\'s boarding place on the square')
    t['Gameplay!EscapeSetup!otrExitLevel'] = box
    for k in ('FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly'):
        t[k] = box
    t['FASpecials!POI!POI_TheEscapeArea'] = (mark, None, None, 'beside the boarding place')
    t['Specials!JumpPoints!06_Exit'] = ((b[0], b[1], b[2]), SOUTH, None, 'the boarding place')
    t[ROLE['walk box']] = (WALK_BOX[0], None, WALK_BOX[1], 'GUESS: the wing\'s mouth')
    t[ROLE['floor box']] = (FLOOR_BOX[0], None, FLOOR_BOX[1], 'GUESS: the stair\'s top')
    return t


# F07's four police squads that arrive on the square (laid by coordinates). squad -> (anchor, men, cover, defend); GUESS: every place. They stand between the stair
# foot (z 27,758) and the van's lane (z 21,800), 1,800+ off the lane: the Heat-style stretch of the round.
G30 = 'Gameplay!030_AfterLoot!'
ARRIVE_XZ = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((26000, 24900), [(25900, 25200), (26100, 25000), (26300, 25200)], [(25800, 24700), (26200, 24600), (26600, 24700)], (26000, 24400))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((25200, 25400), [(25000, 25600), (25300, 25700)], [(25100, 25000), (25500, 25000)], (25300, 25200))),
    (G30 + '030_FinancialAlleyExit_Right', ((28600, 24900), [(28300, 25200), (28500, 25000), (28700, 25200)], [(28200, 24700), (28600, 24600), (29000, 24700)], (28600, 24400))),
    (G30 + '030_FinancialAlleyExitStreet_Right', ((29200, 25400), [(29000, 25600), (29300, 25700)], [(29100, 25000), (29500, 25000)], (29300, 25200)))])
ARRIVE_START = '10_RunToCover'

ESCAPE = ('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith(('Gameplay!0', 'Gameplay!RunToEscape!')))


def police():
    return ARRIVE_XZ if POLICE_ARRIVE and not NO_AI else {}


def __getattr__(name):
    if name == 'KEEP':
        return _KEEP + tuple(x for x in police() if x not in _KEEP) + (HB.KEEP if BLAST_AT is not None else ()) + ((COUNTER,) if LOCK_WING else ())
    raise AttributeError(name)


DROP = ('Specials!CoverPoints!*',)      # M11_B brings its own cover list when it has one: a second FFCoverList is an assert (the park's rule; check() counts)

# ------------------------------------------------------------------ the campaign's squads (M11_B), MEASURED with probe: plain kinds only (no MountedWeapon, ActivateGeom, vehicle)
# Left out: the Allies (FollowBehaviourRout), the Loyalists, the Seven's mounted guns (SevenDudes), LastSeven (ActivateGeom), Fuentes / Carlos (cutscene men),
# the RPG squads whose only starter is a mini-cutscene (RPG_01, RPGBeforeTank, GainAccess), the machine guns, BTR, T72, the helicopter, rooftop and courtyard squads.
# stage -> when: 'start' the round-start timer (+ START_AT); 'walk' the box at the wing's mouth; 'floor' the box at the stair's top (with the alarm and the gate)
GE = '060_CapitolioSquare!Enemies!CapitolioSquare_'
GI = '070_CapitolioInside!Enemies!CapitolioInsideSoldiers_'
SQUADS = collections.OrderedDict([
    (GE + 'RebelMainBarricadeEntrance_01', ('start', 'HuntBehaviour')),            # 2: at the start's elbow (15 m): the opening fight. GUESS (the design said 'held')
    (GE + 'RebelGotoHole', ('start', 'DefendBehaviour')),                          # 1
    (GE + 'RebelSideBarricadeSideEntrance_01', ('start', 'DefendBehaviour')),      # 1: the gallery's defenders (they hold their posts)
    (GE + 'RebelSideBarricadeSideEntrance_02', ('start', 'DefendBehaviour')),      # 1
    (GE + 'RebelSideBarricadeTopFloor_01', ('start', 'DefendBehaviour')),          # 1
    (GE + 'RebelSideBarricadeTopFloor_02', ('start', 'DefendBehaviour')),          # 1
    (GI + 'LastRoomFight_01', ('walk', 'DefendBehaviour')),                        # 2: the wing's guards
    (GI + 'LastRoomFight_02', ('walk', 'DefendBehaviour')),                        # 1
    (GE + 'RebelSideBarricade_01', ('floor', 'FlankingBehaviour')),                # 6: the stair
    (GE + 'RebelSideEngage_01', ('floor', 'DefendBehaviour')),                     # 4
    (GE + 'RebelSideEngage_02', ('floor', 'DefendBehaviour')),                     # 4
    (GE + 'RebelSideBarricade_Guard', ('floor', 'DefendBehaviour'))])              # 2
STRIP = A.STRIP | {'AttachGeomToBone', 'WarnBehaviourRout', 'GateGroup', 'GatePath', 'DeactivateGeom', 'Filter'}
MESSAGE_KINDS = ('ZSquadScript', 'SquadModifierBehaviour', 'TriggerBox', 'TriggerDelay', 'TriggerCounter')
SQUAD_ACTIVE = A.SQUAD_ACTIVE
MEN = collections.OrderedDict()         # {path of a man's group: (x, y, z) hint}: none yet (strip() puts men beside the mesh onto it; the first check says which)

_plan = {}


def squad_plan():
    """The campaign's squads that stay -> ({squad: (path of the child that starts it, actors, kinds stripped, the kind that starts it)}, {left: why})."""
    if NO_AI:
        return {}, {'*': 'a build without enemies (NO_AI)'}
    if 'plan' not in _plan:
        sc = J.Scene.load(LEVEL, 'dm')
        keep, left = {}, {}
        for t in sc.tops():
            name = sc.names[t]
            ctrl = collections.Counter(sc.p.key(nm) for k in range(t, sc.end[t]) for nm, _b in sc.nodes[k]['ctrls'])
            if not ctrl['ZSquadScript']:
                continue
            if name not in SQUADS:
                left[name] = 'not a squad of this round'
                continue
            _stage, child = SQUADS[name]
            actors = sum(sc.cls(k) == 'ZFFActor' for k in range(t, sc.end[t]))
            odd = sorted(set(ctrl) - A.PLAIN - STRIP)
            if odd or not actors or ctrl['ZSoldier'] != actors:
                raise ValueError('kl_fa_hasta_layer: %s cannot stay: it holds %s, %d actors, %d ZSoldier' % (name, odd or 'plain kinds', actors, ctrl['ZSoldier']))
            ks = sc.resolve(R + name + '\\' + child)
            kinds = {sc.p.key(nm) for k in ks for nm, _b in sc.nodes[k]['ctrls']}
            kind = next(iter(sorted(kinds & A.BEHAVE)), 'SquadModifierBehaviour' if 'SquadModifierBehaviour' in kinds else None)
            if len(ks) != 1 or kind is None:
                raise ValueError('kl_fa_hasta_layer: %s\\%s: %d nodes holding %s - neither a behaviour rout nor a squad modifier' % (name, child, len(ks), sorted(kinds)))
            keep[name] = (R + name + '\\' + child, actors, sorted(set(ctrl) & STRIP), kind)
        if set(keep) != set(SQUADS):
            raise ValueError('kl_fa_hasta_layer: squads of SQUADS that are not in %s: %s' % (LEVEL, sorted(set(SQUADS) - set(keep))))
        _plan['plan'] = keep, left
    return _plan['plan']


def place_police(S, mesh, log=print):
    """F07's police squads of ARRIVE_XZ onto the square (kl_fa_v2_park.place_police's way, this file's table). -> [(squad, men)]"""
    sc, out = S.prp, []
    tr = lambda k: struct.unpack('<3f', S.ents[k - 1].trans[:12])
    up = lambda p: (p[0], p[1] + 1.0, p[2])
    sn = lambda xz: snap_mesh(mesh, (float(xz[0]), SQUARE_Y, float(xz[1])))
    for name, (anchor, men, cover, defend) in police().items():
        top = A.node_of(sc, name)
        turned = max(abs(a - b) for a, b in zip(struct.unpack('<9f', S.ents[top - 1].rot[:36]), A.rot9((0.0, 1.0))))
        if not kl_fa.has(sc, top, 'ZSquadScript') or turned > 1e-3 or not sc.resolve(R + name + '\\' + ARRIVE_START):
            raise ValueError('%s: not a squad group without a turn that has a %s' % (name, ARRIVE_START))
        own = []
        def go(k):
            for c in range(k + 1, sc.end[k]):
                if sc.parent[c] == k:
                    own.append(c) if any(abs(v) > 0.5 for v in tr(c)) else go(c)
        go(top)
        by = collections.defaultdict(list)
        for k in own:
            by['men' if any(sc.cls(c) == 'ZFFActor' for c in range(k, sc.end[k])) else sc.names[sc.parent[k]]].append(k)
        at = up(sn(anchor))
        want = {'men': [up(sn(p)) for p in men], ARRIVE_START: [up(sn(p)) for p in cover], '10_Defend': [up(sn(defend))], '40_RunToEscape': [at]}
        if {k: len(v) for k, v in by.items()} != {k: len(v) for k, v in want.items()}:
            raise ValueError('%s: placed children %s, the table has %s' % (name, {k: len(v) for k, v in by.items()}, {k: len(v) for k, v in want.items()}))
        A.place(S, top, at)
        for kind, ks in by.items():
            for k, p in zip(ks, want[kind]):
                A.place(S, k, tuple(p[a] - at[a] for a in range(3)))
        out.append((name, len(by['men'])))
    if out:
        log('  kl_fa_hasta_layer: the police that arrive: %d of F07\'s squads re-placed (%d men) on the square' % (len(out), sum(n for _s, n in out)))
    return out


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for Hasta. S: kl_graft.Level('F07'), unedited."""
    import kl_route
    sc = S.prp
    if PLAN is None:
        raise ValueError(NO_PLAN)
    mesh = kl_route.load(LEVEL).mesh()
    for tbl in (START, TRAITOR, TEAM_MERC, STAGE_B, STAGE_C, STAGE_D, AFTER_DEATH, BODIES):      # heights from the navigation mesh (the tables hold guesses)
        tbl[:] = [snap_mesh(mesh, p) for p in tbl]
    spawn = _spawn()
    for name, (pos, face, half, _why) in place_now().items():
        put(S, name, pos, face, half)
    for name in PARKED:
        put(S, name, PARK)
    seen = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) == 'ZSpawnPoint':
            kind = kl_fa.node_values(sc, t)[8]
            if kind not in spawn:
                raise KeyError('%s: no place for spawn points of kind %s' % (sc.names[t], kind))
            pts, d, face = spawn[kind]
            p = pts[seen[kind] % len(pts)]
            p = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            A.place(S, t, p, turn=facing(p, face))
            seen[kind] += 1
        elif sc.names[t].startswith('Heroes!'):
            crook = sc.names[t].startswith('Heroes!Hero_0')
            pts, face = (START, EAST) if crook else (BODIES, board())
            p = pts[seen[crook, 'hero'] % len(pts)]
            A.place(S, t, p, facing(p, face))
            seen[crook, 'hero'] += 1
    log('  kl_fa_hasta_layer: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
    # loot: stacks of F07's drop pools become loot that lies in the map (the club's way); finish() gives them the briefcase
    pool = collections.defaultdict(list)
    for k, i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if v[2] == 'ZMONEYCTRL_TYPE_DROP' and sc.parent[k] == 0:
            pool[v[0]].append((sc.names[k], k, i))
    take = (sorted(pool['ZMONEYCTRL_GAMEMODE_ALL'])[-POOL_ALL:] + sorted(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])[POOL_ALL - len(LOOT):])[:len(LOOT)]
    if len(take) != len(LOOT):
        raise ValueError('%d pool stacks for %d loot places' % (len(take), len(LOOT)))
    loot = []
    for (name, k, i), (p, _yaw, value, _what) in zip(take, LOOT):
        def fn(us, value=value):
            for j, v in enumerate(('ZMONEYCTRL_GAMEMODE_ALL', value, 'ZMONEYCTRL_TYPE_NORMAL', 'ZMONEYCTRL_VARIANT_NORMAL', 15000, 0.2, 1, 30.0, 800.0, 1000.0, 0, 0)):
                A.setv(sc, us, j, v)
        kl_fa.edit(sc, k, i, fn)
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'TriggerBox2'), lambda us: A.setv(sc, us, 2, LOOT_REACH))
        A.place(S, k, p, hidden=False)
        loot.append(name)
    log('  kl_fa_hasta_layer: loot: %d objects, %d in all (pool: %d ALL + %d TM_ONLY stacks)' % (
        len(LOOT), sum(v for _p, _y, v, _w in LOOT), len(pool['ZMONEYCTRL_GAMEMODE_ALL']), len(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])))
    place_police(S, mesh, log)
    S.van = ESC.van_prepare(S, PLAN, log)
    # the van is NOT in the world until the alarm (the club's VAN_LATE: no FakeTarget, hidden from the load)
    vg = A.node_of(sc, van_path()[len(R):])
    gone = [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
    for k in gone:
        sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
    A.place(S, vg, hidden=True)
    log('  kl_fa_hasta_layer: the van\'s FakeTarget (%d) is taken off and its group is hidden from the load; the alarm shows it' % len(gone))
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(place_now()['FASpecials!POI!POI_TheEscapeArea'][0])[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_fa_hasta_layer: the escape marker is %d from the van\'s drive (%d wanted)' % (off, LANE_CLEAR))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    if BLAST_AT is not None:
        HB.BLAST_AT = BLAST_AT
        HB.prepare_host(S, log)
    S.authored = {'loot': loot, 'van': van}
    return S.authored


# ------------------------------------------------------------------ the campaign's own objects
def campaign_names(level):
    """Top-level names of M11_B the campaign pre-pass must leave in: the kept squads. (No shatter wrapper: the corner blast is NOT built, see BLAST.)"""
    if level != LEVEL:
        return ()
    return tuple(squad_plan()[0]) + ((OPENER,) if LOCK_WING else ())


_tpl_key = J.tpl_key


def orphan_clones(level, sc=None, log=print):
    """Top-level clone groups ('CloneGroup_*') holding ZAllocMany copies for which the scene has no template (a ZAllocMany OUTSIDE the clone groups whose
    path, '!' read as '/', ends in the group's path). kl_prpjoin.templates() only reads '/', and kl_maps.campaign_drop drops the '!' templates of
    Effects! / scripting but leaves their clone groups as 'map': the copies' template pointer (ZAllocMany +0x58) stays 0 and the first copy's
    ZParticleEmitter crashes at kl2 0x4c63f2 (M11B, 2026-10-17: Artillery_Impact_Group). -> [glob-escaped top names], on the Dead Men level LEVEL
    (before the join; names then match the m_drop rule) or, given sc, on any joined scene."""
    import glob
    if sc is None:
        if level != LEVEL:
            return ()
        sc = J.Scene.load(level, 'dm')
    dropped = set()
    if sc.label == level:                       # the source level: what the campaign pre-pass drops (squads it must keep excepted) holds no template either
        import fnmatch
        drop = [n for n in kl_maps.campaign_drop(level)[0] if n not in {glob.escape(x) for x in campaign_names(level)}]
        for t in sc.tops():
            if any(fnmatch.fnmatchcase(sc.names[t], d) for d in drop):
                dropped.update(range(t, sc.end[t]))
    out = [glob.escape(sc.names[t]) for t in J.orphan_clone_groups(sc, dropped)]
    if out:
        log('  kl_fa_hasta_layer: %d clone group(s) without a template: %s' % (len(out), ', '.join(o.split('/')[-1] for o in out)))
    return tuple(out)


def strip(M, log=print):
    """On the converted Dead Men level, before the join: the kept squads lose STRIP's kinds; every man who stands beside the mesh goes onto it."""
    import kl_route
    if M.name != LEVEL:
        return 0
    keep = squad_plan()[0]
    if not keep:
        log('  kl_fa_hasta_layer: %s: no squad stays (NO_AI)' % M.name)
        return 0
    sc, n, props = M.prp, collections.Counter(), 0
    for t in sc.tops():
        if sc.names[t] not in keep:
            continue
        for k in range(t, sc.end[t]):
            nd = sc.nodes[k]
            gone = [sc.p.key(c[0]) for c in nd['ctrls'] if sc.p.key(c[0]) in STRIP]
            if gone:
                nd['ctrls'] = [c for c in nd['ctrls'] if sc.p.key(c[0]) not in STRIP]
                n.update(gone)
                if 'AttachGeomToBone' in gone:
                    A.place(M, k, hidden=True)
                    A.place(M, sc.parent[k], hidden=True)
                    props += 1
    mesh = kl_route.load(LEVEL).mesh()
    placed = []
    for path, hint in MEN.items():
        g = A.node_of(sc, path)
        hit = mesh.on(*[float(v) for v in hint])
        if hit is None:
            raise ValueError('kl_fa_hasta_layer: MEN: %s: (%d, %d, %d) is not on the navigation mesh' % (path, *hint))
        was = world_of(M.ents[g - 1])[0]
        BK.man_to(M, g, (float(hint[0]), hit[1], float(hint[2])), mesh)
        placed.append((path, was))
    moved, off = [], []
    for t in sc.tops():
        if sc.names[t] not in keep:
            continue
        for k in range(t, sc.end[t]):
            if sc.cls(k) != 'ZFFActor':
                continue
            g = sc.parent[k]
            w = world_of(M.ents[g - 1])[0]
            if mesh.on(*w) is not None:
                continue
            d, i = mesh.nearest(*w)
            if i is None or d > MAN_OFF:
                off.append('%s at (%d, %d, %d), %s off' % (sc.path[k], *w, d))
                continue
            mid = mesh.mid[i]
            for step in range(1, 201):
                x, z = w[0] + (mid[0] - w[0]) * step / 200.0, w[2] + (mid[2] - w[2]) * step / 200.0
                if mesh.inside(i, x, z) and math.hypot(x - w[0], z - w[2]) >= d + MAN_IN:
                    break
            new = (x, mesh.height(i, x, z), z)
            BK.man_to(M, g, new, mesh)
            moved.append((sc.path[g][5:], round(d), math.dist(w, new)))
    log('  kl_fa_hasta_layer: %s: %d squads stay (%d men); taken off them: %s; %d props hidden' % (
        M.name, len(keep), sum(a for _s, a, _k, _w in keep.values()), dict(n) or 'nothing', props))
    log('  kl_fa_hasta_layer: %d men re-placed (MEN); %d stood beside the navigation mesh and were put on it: %s' % (
        len(placed), len(moved), ', '.join('%s %d off, moved %d' % (p.split('!')[-1], d, m) for p, d, m in moved) or '-'))
    for o in off:
        log('  kl_fa_hasta_layer: MAN OFF THE MESH (give him a place in MEN): ' + o)
    if off:
        raise ValueError('kl_fa_hasta_layer: %d men stand more than %d off the navigation mesh: %s' % (len(off), MAN_OFF, off))
    return sum(n.values())


# ------------------------------------------------------------------ the joined scene
BLAST = ('NOT BUILT: the design\'s opening blast at the Capitol corner has no object to reuse. M11_B\'s BoomBoxDust (070_CapitolioInside!Enemies) is an Explode with an '
         'EMPTY effect name (the bunker\'s dust, mask 737088), the rooftop BoomBox names FX_Grenade_T72_02 inside the campaign\'s dropped mainsceneincludes.zip, and the '
         'tank shell is a T72 group. A blast needs kl_fa_blast-style objects (ShakeCamera + a Dog Days particle template) hung on the start timer: a later step.')


def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_fa_hasta_layer: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    plan = squad_plan()[0]
    stage, quiet = collections.defaultdict(list), 0
    for n, (first, _actors, _strip, kind) in plan.items():
        k = node(n)
        st = SQUADS[n][0]
        if values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE] not in (0, 1):
            raise ValueError('%s: ZSquadScript field %d is %r' % (n, SQUAD_ACTIVE, values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE]))
        put_(k, 'ZSquadScript', **{'f%d' % SQUAD_ACTIVE: 1 if SQUADS_AWAKE else 0})
        j = sc.resolve(must([first])[0])[0]
        stage[st].append(first)
        if kind == 'SquadModifierBehaviour':
            put_(j, kind, **{'f4': 'eAM_Activate'})
        for j in range(k, sc.end[k]):               # a message list inside the squad names only what still holds a controller
            for kind_ in [sc.p.key(nm) for nm, _b in sc.nodes[j]['ctrls'] if sc.p.key(nm) in MESSAGE_KINDS]:
                for f, x in enumerate(values(sc, j, kind_)):
                    if isinstance(x, list) and x and isinstance(x[0], str):
                        live = [s for s in x if not any(sc.top[h] == k and not sc.nodes[h]['ctrls'] for h in sc.resolve(s))]
                        if len(live) != len(x):
                            put_(j, kind_, **{'f%d' % f: live})
                            quiet += len(x) - len(live)
    arrive = must([R + n + '\\' + ARRIVE_START for n in police()])
    armed = BK.soldier_rows(sc, plan, log) if plan else {}
    ways = must([R + ROLE['gate'] + '\\' + w for w in GATE_WAYS])
    if not kl_fa.has(sc, node(ROLE['gate']), 'GateGroup') or any(not kl_fa.has(sc, sc.resolve(w)[0], 'GatePath') for w in ways):
        raise ValueError('%s is not a GateGroup with the two GatePath %s' % (ROLE['gate'], GATE_WAYS))
    for w in ways:
        put_(sc.resolve(w)[0], 'GatePath', f0=arrive)
    lists('start timer', 'TriggerDelay2', f0=START_AT, f4=stage['start'])
    lists('walk box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['walk'])
    # the stair's top: the street squads, the alarm (the van's timer) and the gate (the police on the square)
    lists('floor box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BK.BOX_PER_MAN: 0}, f17=stage['floor'] + [R + ROLE['van timer'], ways[0]])
    lists('backstop', 'TriggerDelay2', f0=BACKSTOP_AT, f4=[ways[1], R + ROLE['van timer']] + ([R + OPENER] if LOCK_WING else []))
    lists('van on', 'ActivateGeom', f0='AITrigger', f1=[van_path()])
    lists('van timer', 'TriggerDelay2', f0=VAN_DELAY, f4=[R + ROLE['van on'], R + ROLE['speak']])
    lists('reset hide', 'DeactivateGeom', f0='AITrigger', f1=[van_path()])
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    lists('monitor', 'AIMonitor', f2=[R + ROLE['reset hide']] + have + [R + ROLE['start timer'], R + ROLE['backstop']])
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']])
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    if PLAN is None:
        raise ValueError('kl_fa_hasta_layer: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    men = sum(a for _f, a, _s, _k in plan.values())
    log('  kl_fa_hasta_layer: wired: %d campaign squads (%d men): round start + %.0f s -> %d hall/gallery squads; the box at the wing -> %d; the box at the '
        'stair\'s top -> %d + the alarm (+%.0f s: the van, the exit line) + the gate (%d police squads); backstop %.0f s; %d dead entries cut; soldier rows: %s' % (
            len(plan), men, START_AT, len(stage['start']), len(stage['walk']), len(stage['floor']), VAN_DELAY, len(arrive), BACKSTOP_AT, quiet,
            dict(armed) or 'Dead Men\'s rows stay'))
    if LOCK_WING:
        lock_wire(sc, stage['start'], log)
    if BLAST_AT is not None:
        HB.BLAST_AT = BLAST_AT
        HB.wire(sc, log)
    else:
        log('  kl_fa_hasta_layer: ' + BLAST)
    return {'stage': dict(stage), 'arrive': arrive, 'ways': ways}


def locked_nodes(sc):
    """-> [(node, name)] of LOCKED in the joined scene `sc`, matched by name exactly as Doors does (one hit each; SWITCHES' ancestor filter)."""
    out = []
    for nm, anc, _what in SWITCHES:
        if nm not in LOCKED:
            continue
        hit = [k for k in range(1, len(sc.names)) if sc.names[k] == nm and (anc is None or any(anc in a for a in _ancestors(sc, k)))]
        if len(hit) != 1:
            raise KeyError('%s: %d nodes named %s (filter %s)' % (sc.label, len(hit), nm, anc))
        out.append((hit[0], nm))
    return out


def lock_wire(sc, first, log=print):
    """LOCK_WING, on the joined scene: the 'start' squads' dead lists -> COUNTER (count = those squads) -> OPENER (DeactivateGeom on the three LOCKED nodes).
    first: the paths of the children that start the 'start' squads (wire()'s stage['start']). The backstop names OPENER too (wire())."""
    node = lambda n: A.node_of(sc, n)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    ko, kc = node(OPENER), node(COUNTER)
    if sc.parent[kc] != 0 or sc.end[kc] - kc != 1 or not kl_fa.has(sc, kc, 'TriggerCounter'):
        raise ValueError('%s is not a single top-level TriggerCounter' % COUNTER)
    if not kl_fa.has(sc, ko, 'DeactivateGeom'):
        raise ValueError('%s holds no DeactivateGeom' % OPENER)
    targets = [sc.path[k] for k, _nm in locked_nodes(sc)]
    put_(ko, 'DeactivateGeom', f0='AITrigger', f1=targets)      # GUESS: f0 'AITrigger' is the message it answers (it is the campaign's own value, kept)
    squads = [sc.top[sc.resolve(p)[0]] for p in first]
    for k in squads:
        dead = [s for s in values(sc, k, 'ZSquadScript')[A.SQUAD_DEAD] if sc.resolve(s)]
        put_(k, 'ZSquadScript', **{'f%d' % A.SQUAD_DEAD: dead + [R + COUNTER]})
    put_(kc, 'TriggerCounter', f0=len(squads), f4=[R + OPENER])
    log('  kl_fa_hasta_layer: LOCK_WING: %d nodes stay shut (%s); %d hall squads wiped out -> counter -> %s opens them; the %.0f s backstop opens them too' % (
        len(targets), ', '.join(n for _k, n in locked_nodes(sc)), len(squads), OPENER.split('!')[-1], BACKSTOP_AT))
    return {'squads': [sc.names[k] for k in squads], 'targets': targets}


def lock_check(sc):
    """-> [faults] of a built level's locked-wing chain: squads -> counter -> opener -> the three nodes, nobody else names them, the backstop opens too."""
    bad = []
    node = lambda n: A.node_of(sc, n)
    ko, kc = node(OPENER), node(COUNTER)
    cv, ov = values(sc, kc, 'TriggerCounter'), values(sc, ko, 'DeactivateGeom')
    want = [(R + COUNTER).lower()]
    firing = [k for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript') if any(s.lower() in want for s in v[A.SQUAD_DEAD])]
    stage = {R + n for n, (st, _k) in SQUADS.items() if st == 'start'}
    got = {sc.path[k] for k in firing}
    if got != stage:
        bad.append('the squads that report to the counter are %s, wanted the %d start squads %s' % (sorted(x[-30:] for x in got), len(stage), sorted(x[-30:] for x in stage)))
    if cv[0] != len(stage) or [s.lower() for s in cv[4]] != [(R + OPENER).lower()]:
        bad.append('the counter holds %r / %r (wanted %d and only the opener)' % (cv[0], cv[4], len(stage)))
    tg = {sc.path[k].lower() for k, _nm in locked_nodes(sc)}
    if ov[0] != 'AITrigger' or {s.lower() for s in ov[1]} != tg or len(ov[1]) != len(tg):
        bad.append('the opener holds %r, wanted AITrigger on the three locked nodes' % (ov,))
    bs = node(ROLE['backstop'])
    if (R + OPENER).lower() not in [s.lower() for s in values(sc, bs, 'TriggerDelay2')[4]]:
        bad.append('the backstop timer does not open the wing')
    mine = {(R + OPENER).lower(), (R + COUNTER).lower()}
    for k in range(1, len(sc.nodes)):
        for _h, _f, u in J.fields(sc, k):
            for s_ in J.strings(sc, u):
                if s_.lower() in mine and k not in firing and k not in (kc, bs):
                    bad.append('%s names %s' % (sc.path[k][-60:], s_[-40:]))
    return bad


def lock_present(sc):
    return bool(sc.resolve(R + OPENER)) and bool(sc.resolve(R + COUNTER))


def layer_names(sc):
    camp = set(campaign_names(LEVEL))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    return True


# ------------------------------------------------------------------ on the written level
def finish(folder, log=print):
    """The written level, in place: the lightened level, the briefcases on the loot, the texts. -> [problems]"""
    import kl_fa_loot as L, kl_chars as C, kl_light, kl_loc, kl_texmat as T
    from kl_port_check import workdir
    E = L.Edit(folder)
    sc, bad = E.sc, []
    loot = [k for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    pool = {E.ents[k - 1].model for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2]}
    dressed = not {E.ents[k - 1].model for k in loot} <= pool
    if len(loot) != len(LOOT):
        bad.append('%d loot objects in the level, LOOT has %d' % (len(loot), len(LOOT)))
    n0 = len(E.p.chunks)
    L.lighten_first(E, log)
    if CASE and loot and not dressed:
        C.dead_indices(E.p, sc, E.raw, E.oct, E.extra, log)
        root, _box, slots = L.case_model(E, CASE, CASE_SCALE, log)
        lo, _hi = L._assets(E).bounds(root)
        for k in loot:
            at = E.at(k)
            p, yaw, _value, _what = min(LOOT, key=lambda r: math.dist(r[0], at))
            if math.dist(p, at) > 1.0:
                bad.append('%s lies at (%d, %d, %d), which is no place of LOOT' % (sc.names[k], *at))
                continue
            E.put(k, (p[0], p[1] - lo[1], p[2]), L.yaw9(yaw), root)
        if len(E.p.chunks) != n0:
            raise ValueError('the chunk table grew from %d to %d: not enough dead indices' % (n0, len(E.p.chunks)))
        if slots:
            fxc = E.lv['.fxc']
            upath = os.path.join(workdir(), 'build', 'shared', 'union.fxc')
            if os.path.isfile(upath):
                fxc = T.merge_fxc(fxc, open(upath, 'rb').read())
            fit = kl_light.fit_shaders(E.mat, fxc, slots=slots, log=log)
            E.lv['.fxc'] = fxc
            bad += ['no compiled shader for %s' % v[0] for v in fit['unresolved'].values()]
        log('  kl_fa_hasta_layer: %d briefcases (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(loot), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_fa_hasta_layer: %s: the loot already shows models of its own: left as it is' % folder)
    langs = 0
    for ext in sorted(E.lv.ext):
        if not ext.lower().endswith('.loc'):
            continue
        kids = kl_loc.parse(E.lv[ext])
        if kids is None:
            continue
        for key, text in TEXTS.items():
            BK.set_text(kids, key, text)
        E.lv[ext] = kl_loc.build(kids)
        langs += 1
    for k, i, _v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, START_KEY % w)]) for f, w in START_FIELDS.items()])
    log('  kl_fa_hasta_layer: %d text keys in %d languages; settings fields %s name the start windows' % (len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ build and check
def build(out, log=print, plan=None):
    """F07 + M11_B with the doors AND the layer into <out>/F07+M11_B campaign -> (kl_maps.one's result, that folder, the van's plan, kl_map_escape's report).
    plan None = made here on a BARE graft (doors armed, no layer; <out>/_bare, deleted again)."""
    import kl_snd
    name = '%s+%s campaign' % (HOST, LEVEL)
    free = shutil.disk_usage(out if os.path.isdir(out) else os.path.dirname(os.path.abspath(out))).free / 1e9
    if free < 3.0:
        raise SystemExit('only %.1f GB free: stop' % free)
    if plan is None:
        bare = os.path.join(out, '_bare')
        try:
            with doors(log, specs=switches()):
                r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', m_drop=M_DROP + orphan_clones(LEVEL))
            if not r.get('ok'):
                raise ValueError('kl_fa_hasta_layer: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    kl_snd.VOICE = True if VOICE else None
    try:
        with ESC.van_layer(plan, log) as st, doors(log, specs=switches()):
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_hasta_layer', m_drop=M_DROP + orphan_clones(LEVEL))
    except ValueError:
        if r.get('ok') or not r:
            raise
    finally:
        kl_snd.VOICE = None
    return r, os.path.join(out, name), plan, {k: st.get(k) for k in ('van', 'wired', 'hvk')}


def van_check(folder, log=print, plan=None):
    L = ESC.Level(folder)
    rep = ESC.van_check(L, log, plan)
    return rep, L, rep['faults']


def check(folder, log=print, problems=None):
    """Every check of this layer on a built (and finished) folder -> [what is wrong]."""
    import kl_route, kl_arms
    arch = BK.archive_of(folder)
    sc, scene, ents, pos, hvk, snd, loc, size = BK.read_built(folder)
    bad = []
    def fail(s):
        bad.append(s); log('  FAIL: ' + s)
    res = json.load(open(os.path.join(folder, 'result.json'))) if os.path.isfile(os.path.join(folder, 'result.json')) else {}
    if problems is None:
        problems = res.get('problems')
    if res.get('dangling'):
        fail('the build left %d dangling scene paths: %s' % (len(res['dangling']), res['dangling'][:3]))
    for p in problems or ():
        why = next((w for t, w in KNOWN if t in p), None)
        log('  verify: %s %s%s' % ('known' if why else 'OPEN ', p[:200], '\n          = %s' % why if why else ''))
        if not why:
            fail('kl_graft.verify: ' + p[:200])
    listed, lost, have = BK.lost_clips(folder, res)
    if listed:
        log('  sound: of the %d clip names result.json lists, %d have a streamed record in the built .WHD; %d have NO record (music / ambience: silent)' % (
            len(listed), len(listed) - len(lost), len(lost)))
    for f in kl_fa.check(sc, snd, loc, kl_arms.read_anm(arch)):
        why = next((w for t, w in KNOWN if t in f.text), None) if f.sev <= kl_fa.BROKEN else None
        log('  kl_fa: %s%s' % (str(f)[:230], '\n          = known: %s' % why if why else ''))
        if f.sev <= kl_fa.BROKEN and not why:
            fail('kl_fa.check: ' + str(f)[:200])
    ncov = len(kl_fa.controllers(sc, 'FFCoverList'))
    log('  cover lists (FFCoverList): %d' % ncov)
    if ncov != 1:
        fail('%d cover lists (a level needs exactly one)' % ncov)
    # ---- clone groups: every group of ZAllocMany copies needs its template (else the first copy's emitter crashes at kl2 0x4c63f2)
    for g in orphan_clones(LEVEL, sc, lambda *a: None):
        fail('clone group %s holds ZAllocMany copies and no template exists (copy +0x58 stays 0: crash at kl2 0x4c63f2 at load)' % g)
    # ---- the doors: the sunk switches sit 4,000 lower (read back by name against the campaign level), nothing of the wreck is left in the lane
    names = [e.name.decode('latin1') for e in ents]
    locked = lock_present(sc)               # a level built with --lock-wing (read from the folder, not from the flag)
    for nm, _anc, what in SWITCHES:
        hit = [i for i, n in enumerate(names) if n == nm]
        low = [i for i in hit if pos[ents[i]][1] < -2000]
        if locked and nm in LOCKED:
            if not hit or low:       # (the rooftop's Roadblock has the same name: only 'none sunk' is asked; lock_check pins the right one by path)
                fail('locked door %s (%s): %d entities named so, %d of them sunk (it must stay in place until the beat)' % (nm, what, len(hit), len(low)))
        elif len(low) != 1:
            fail('door %s (%s): %d entities named so, %d of them sunk' % (nm, what, len(hit), len(low)))
    if locked:
        for f in lock_check(sc):
            fail('lock-wing: ' + f)
        log('  lock-wing: %d hall squads -> counter -> opener -> %d locked nodes (+ backstop %.0f s); reach / stage checks asked with them OPENED' % (
            sum(1 for _n, (st, _k) in SQUADS.items() if st == 'start'), len(LOCKED), BACKSTOP_AT))
    wreck = [i for i, n in enumerate(names) if n == WRECK]
    if len(wreck) != 1 or pos[ents[wreck[0]]][1] > -2000:
        fail('the wreck group %s: %d entities, not one sunk' % (WRECK, len(wreck)))
    # ---- the loot: the values, each on the navigation mesh
    mesh = kl_route.load(LEVEL).mesh()
    loot = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    if len(loot) != len(LOOT) or sorted(v[1] for _k, v in loot) != sorted(w for _p, _y, w, _x in LOOT):
        fail('loot: %d objects with values %s, expected %d with %s' % (len(loot), sorted(v[1] for _k, v in loot)[:3], len(LOOT), sorted(w for _p, _y, w, _x in LOOT)[:3]))
    log('  loot: %d objects, %d in all' % (len(loot), sum(v[1] for _k, v in loot)))
    for k, v in loot:
        p = pos[ents[k - 1]]
        near = mesh.nearest(*p)
        if near[0] is None or near[0] > 120.0:
            fail('loot %s at (%d, %d, %d) is %s from the navigation mesh' % (sc.names[k], *p, near[0]))
    # reach: every loot place (125 = pickup reach) and every spawn of the stage tables must be walked to from the first START place
    try:
        _start = (START[0][0], START[0][1] + 30.0, START[0][2])
        _open = LOCK_OPEN if locked else ()         # the reach is asked with the locked nodes OPENED (the beat has happened); closed they are meant to stop the walk
        _pts = [_start] + [tuple(pos[ents[k - 1]]) for k, _v in loot]
        for r in kl_route.stations(os.path.join(folder, 'F01_Main.zip') if os.path.isdir(folder) else folder, _pts, opened=_open, near=LOOT_REACH)[1:]:
            if not r['reached']:
                fail('loot at (%d, %d, %d) is NOT reached from START (off the mesh by %s; walk comes within %s)' % (*r['at'], r['off'], r['gap']))
        _pts = [_start] + [tuple(p) for p in STAGE_B + STAGE_C + STAGE_D]
        for r in kl_route.stations(os.path.join(folder, 'F01_Main.zip') if os.path.isdir(folder) else folder, _pts, opened=_open, near=60.0)[1:]:
            if r['in'] or not r['reached']:
                fail('stage spawn (%d, %d, %d) is %s' % (*r['at'], 'inside ' + str(r['in'][:1]) if r['in'] else 'not reached'))
    except Exception as ex:      # GUESS: a route-tool failure must not hide the other checks
        log('  (reach check not run: %s: %s)' % (type(ex).__name__, ex))
    # ---- spawn points and men on the mesh; no spawn / station inside a level bound
    drive = ESC.Poly([tuple(p) for p in PLAN['path']]) if PLAN else None
    kinds = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) != 'ZSpawnPoint':
            continue
        kind = kl_fa.node_values(sc, t)[8]
        p = pos[ents[t - 1]]
        kinds[kind] += 1
        if 'START' in kind or 'TRAITOR' in kind or 'AFTER_DEATH' in kind:
            if mesh.on(*p) is None and (mesh.nearest(*p)[0] or 1e9) > 60.0:
                fail('spawn point %s (%s) at (%d, %d, %d) is %s off the navigation mesh' % (sc.names[t], kind[-12:], *p, mesh.nearest(*p)[0]))
        if any(in_rect(p, b[0]) for b in BOUNDS.values()):
            fail('spawn point %s at (%d, %d, %d) is inside a level bound' % (sc.names[t], *p))
        if 'AFTER_DEATH' in kind and PLAN and math.dist(p, PLAN['board']) < FED_CLEAR:
            fail('spawn point %s (AFTER_DEATH) is %d from the boarding place (%d wanted)' % (sc.names[t], math.dist(p, PLAN['board']), FED_CLEAR))
        if drive is not None and 'AFTER_DEATH' not in kind and abs(drive.project(p)[1]) < LANE_CLEAR and 'START' in kind:
            fail('spawn point %s is %d from the van\'s drive' % (sc.names[t], abs(drive.project(p)[1])))
    log('  spawn points by kind: %s' % {k.replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in kinds.items()})
    for k, _v in loot:
        if any(in_rect(pos[ents[k - 1]], b[0]) for b in BOUNDS.values()):
            fail('loot %s is inside a level bound' % sc.names[k])
    men = [k for k in range(1, len(sc.names)) if sc.cls(k) == 'ZFFActor']
    squads = [k for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript')]
    off = 0
    for k in men:
        g = sc.parent[k]
        p = pos[ents[g - 1]]
        if mesh.on(*p) is None and (mesh.nearest(*p)[0] or 1e9) > MAN_OFF:
            off += 1
            fail('man %s at (%d, %d, %d) is %s off the navigation mesh' % (sc.path[k], *p, mesh.nearest(*p)[0]))
        if drive is not None and sc.path[k][len(R):].startswith(G30) and abs(drive.project(p)[1]) < LANE_CLEAR:
            fail('policeman %s is %d from the van\'s drive' % (sc.path[k], abs(drive.project(p)[1])))
    log('  actors: %d, squads: %d (campaign squads %d, F07\'s police squads %d); men off the mesh: %d' % (
        len(men), len(squads), len(SQUADS) if not NO_AI else 0, len(police()), off))
    if not NO_AI:
        for n in SQUADS:
            kk = sc.resolve(R + n)
            if not kk:
                fail('squad %s is not in the level' % n)
                continue
            if values(sc, kk[0], 'ZSquadScript')[SQUAD_ACTIVE] != (1 if SQUADS_AWAKE else 0):
                fail('squad %s: field %d is %r' % (n, SQUAD_ACTIVE, values(sc, kk[0], 'ZSquadScript')[SQUAD_ACTIVE]))
    # ---- the exit and the van
    ex = [(k, v) for k, _i, v in kl_fa.controllers(sc, kl_fa.EXIT)]
    if len(ex) != 1 or ex[0][1][2] != van_path():
        fail('the exit trigger: %s, wanted one naming %s' % ([v[2:5] for _k, v in ex], van_path()))
    if PLAN:
        b = PLAN['board']
        log('  van: boarding place (%d, %d, %d); stop %s; exit box %d from it' % (*b, [round(x) for x in PLAN['stop']], math.dist(pos[ents[ex[0][0] - 1]], b) if ex else -1))
        for t in sc.tops():
            if sc.cls(t) == 'ZSpawnPoint' and 'START' in kl_fa.node_values(sc, t)[8] and math.dist(pos[ents[t - 1]], b) < 1500:
                fail('a START spawn point is %d from the boarding place' % math.dist(pos[ents[t - 1]], b))
    if HB.present(sc):                      # a level built with --blast: its objects, values and particle groups (read from the folder, not from the flag)
        bad += ['blast: ' + b for b in HB.check(os.path.join(folder, 'F01_Main.zip') if os.path.isdir(folder) else folder, log)]
    return bad


def flags_of():
    f = collections.OrderedDict(SQUADS_AWAKE=SQUADS_AWAKE, NO_AI=NO_AI, POLICE_ARRIVE=POLICE_ARRIVE, START_AT=START_AT, BACKSTOP_AT=BACKSTOP_AT, VAN_DELAY=VAN_DELAY,
                                SINK_DY=SINK_DY)
    if BLAST_AT is not None:
        f['BLAST_AT'] = BLAST_AT
    if LOCK_WING:
        f['LOCK_WING'] = True
    return f


def test(out, keep=False, log=print, plan=None):
    """Build the level with the doors and the layer into <out>, finish it, check it. -> 0 or 1. Beside the archive: van.json."""
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    vrep = van_check(folder, lambda *a: None, plan)[0]
    with open(os.path.join(folder, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'], flags=flags_of(), check=vrep), f, indent=1, default=str)
    bad = check(folder, log, r['problems']) + late
    log('level: %d entities, %d rooms, %.0f MB' % (r['entities'], r['rooms'], r['archive_mb']))
    if not keep:
        for f in os.listdir(folder):
            if '_Main' in f:
                os.remove(os.path.join(folder, f))
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


def load_plan(folder):
    lay_van(plan_of(os.path.join(folder, 'van.json')))


def main():
    global NO_AI, SQUADS_AWAKE, POLICE_ARRIVE, BLAST_AT, LOCK_WING
    a = sys.argv[1:]
    if a[:1] == ['proof']:
        sys.exit(proof(a[1] if len(a) > 1 and not a[1].startswith('--') else 'C:/kl_scratch/hasta', '--keep' in a))
    if len(a) >= 2 and a[0] == 'test':
        NO_AI = '--no-ai' in a
        SQUADS_AWAKE = '--squads-awake' in a
        POLICE_ARRIVE = '--no-police' not in a
        LOCK_WING = '--lock-wing' in a
        if '--blast' in a:
            i = a.index('--blast') + 1
            BLAST_AT = float(a[i]) if i < len(a) and not a[i].startswith('--') else HB.BLAST_AT
        plan = plan_of(a[a.index('--plan') + 1]) if '--plan' in a else None
        sys.exit(test(a[1], '--keep' in a, plan=plan))
    elif len(a) == 3 and a[0] == 'plan':
        P = van_plan(a[1])
        with open(a[2], 'w', encoding='utf-8') as f:
            json.dump(P, f, indent=1, default=str)
        print('kl_fa_hasta_layer.plan: %s (stop %s, board %s)' % (a[2], P['stop'], P['board']))
    elif len(a) == 2 and a[0] == 'finish':
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        load_plan(a[1])
        bad = check(a[1])
        print('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_hasta_layer
    kl_fa_hasta_layer.main()
