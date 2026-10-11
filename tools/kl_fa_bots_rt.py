#!/usr/bin/env python3
"""
AI heisters on RETOMOTO TOWER: the squad of tools/kl_fa_bots.py on a map made of TWO navigation parts (the tower,
M09_A, and lobby + street, M09_B) that only the hook joins. Spec, the reading of kl2.exe it rests on, the hook part
(klhook/klcrew_rt.c), live checks: re/bots_retomoto.md. OFFLINE: nothing here installs anything or starts the game.

    python kl_fa_bots_rt.py build <build folder> <out folder> [options]   plan + write + every check; exit 1 on a FAIL
    python kl_fa_bots_rt.py plan  <build folder> [options]                the plan only (stations, places, notes)
    python kl_fa_bots_rt.py check <folder>                                kl_fa_bots.check + the checks of this module
    python kl_fa_bots_rt.py diff  <build folder> <out folder>             kl_fa_bots.diff, the JumpPoint allowed
    options
      --tower-only         no second leg: the bots end beside the tower car in an AllyEscapeBox and are taken from
                           there when a van waits in the street (re/bots.md 6.3). No JumpPoint list, no [CrewJoin] section.
                           The form that needs NO hook part - for an A / B run.
      --loot-seconds N     the wait at the boardroom table: until its six briefcases are gone or N s (default 30, GUESS:
                           the table's loot only appears when the room's guards are dead, kl_fa_author GATE_MAIN_ROOM)
      --enter-after-blast  the bots walk in AFTER_BLAST s after the blast (as before 2026-10-11); default: they wait
                           at the window until the boardroom's three squads are dead (the room counter), or
                           --room-wait S (75) after the blast at the latest
      --after-blast S      Timer_start_bots = the level's own blast timer + S (default 1.0, GUESS): the bots stand on
                           the balcony until the window has gone
      --street-hold S      seconds the squad waits at the last place BEFORE the level exit box (default 10, GUESS;
                           0 = no wait). A bot inside that box calls the van (kl2 0x6cd8e0, re/bots.md 11), and
                           Retomoto has ONE van (kl_fa_street.ONE_VAN).
      --no-tree            as kl_fa_bots

THE DESIGN (the three ways weighed: re/bots_retomoto.md 2)
  ONE squad of seven, the same seven actors and crew records from the balcony to the van - so loot, money, heist
  stage and the traitor flag carry over. The route is two chains:
    tower   Timer_start_bots (after the blast) -> in through the window (ENTERS_BANK, stage 1) -> the boardroom table
            (TriggerLootDepleted) -> down the stairs -> a place BESIDE the tower car's jump box, inside an
            AllyEscapeBox (kl_fa_bots' --park form; the fall-back when the hook part is off: re/bots.md 6.3)
    street  started by the JUMP: `Specials!JumpPoints!06_Exit`'s reference list names the first street step of each
            squad. kl2 0x57e110, after it has placed the local player at a jump entry, calls 0x72e0f0(the entry's
            ZJumpPoint), which sends 'AITrigger' (word [0x1689020], registered by jumppoint.cpp) to every object of
            that list ([jp+0x34]); a DefendBehaviourRout takes 'AITrigger' in its slot 26 (0x4ebed0, word
            [0x168d804]) and starts. Stock form: campaign L05 `Jumppoints!Jump05` names `AI!Friendly!B6!Kane_B6\\
            FollowLynch` (a friendly AI's step), L02 has six such lists.
            lobby (EXITS_BANK on the stairs, stage 2) -> entrance -> forecourt -> east pavement of the road -> a
            place before the level exit box (TriggerDelay2 --street-hold) -> into the box (stage 3; the van is
            called) -> beside the van's stop, on the pavement side of its lane; boarding by ZBoardEscapeVehicleTactic
            (stock F07's form: these ARE F07's vans).
  What moves the ACTORS from the tower part to the street part is the hook (klhook/klcrew_rt.c, [CrewJoin] Enable=1):
  in the tick in which kljoin.c's jump request for that entry is pending - before the game moves the player and
  sends the 'AITrigger' - it calls the game's own actor teleport 0x62a900 (the routine 0x8f3fa0 itself uses on the
  story crew at 0x8f4128, and ZFFActor's own slot 18 on itself at 0x6ccdc1) for every AI crew record in play, with
  the places this module writes into the [CrewJoin] section of the build's KLJoin.ini. WITHOUT that hook part the street steps are
  started for bots that stand in the tower: what a DefendBehaviourRout does with a place on another navigation
  part is NOT established - use a --tower-only build then.

WHAT IS WRITTEN beyond kl_fa_bots.apply: the street steps (cloned F07 forms, as every other step), ONE edit of an
  existing node (field 0 of the JumpPoint controller of 06_Exit), the [CrewJoin] section appended to <out>/KLJoin.ini.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_bots as F
import kl_fa_author as au
from kl_prp import units
import kl_fa_van as van
import kl_fa_street as street

R_ = F.R_
JOIN_NAME = au.ROLE['join']             # 'Specials!JumpPoints!06_Exit': the entry KLJoin.ini jumps the player to
BLAST_TIMER = au.ROLE['blast timer']    # the level's TriggerDelay2 that swaps the glass (kl_fa_author.wire)
AFTER_BLAST = 1.0       # GUESS: the bots' start timer runs this long after the blast timer
# THE ROOM FIRST (2026-10-11, after runs HP / T1 / T2_DM09: the seven walked in and looted while the boardroom's guards
# lived, and died to their bullets in 95-150 s; the owner's design: the main room is looted 'once everyone in it is
# dead'). The bots' chain is now started by kl_fa_author's room counter (ROLE['counter'], the TriggerCounter the three
# room squads' field 8 feeds; it switched the table loot on and nothing else) through a one-shot gate counter, and by
# Timer_start_bots as the FALL-BACK ROOM_WAIT s after the blast (stock pairs 'those enemies are dead' with a timer,
# re/bots_dynamic.md 3) - so an idle player or a hiding guard does not leave the seven on the balcony for the round.
# Until then they stand at the blown window and shoot at what shows. GUESS: ROOM_WAIT; ASSUMPTION: a TriggerCounter
# with field 0 = 1 fires its list once when first named (stock F07 tcRunToEscape's form, fields 2 / 3 = 0).
ROOM_GATE = True        # False ('--enter-after-blast'): Timer_start_bots alone, AFTER_BLAST after the blast, as before
ROOM_WAIT = 75.0        # GUESS: the fall-back, seconds after the blast timer
ROOM_COUNTER = au.ROLE['counter']
GATE_NAME = F.SQUAD + 'Counter_room_clear'
LOOT_SECONDS = 30       # GUESS (docstring)
STREET_HOLD = 10.0      # GUESS (docstring)
WARP = 15.0             # a polygon whose corners lie farther than this from the plane kl_fa_bots.Nav fits through its
                        # first three is not used for a place: the fitted height is wrong there (measured: the pentagon
                        # through the main window, corners y 20996 / 21025, fitted heights up to 21118)
BOMB_KEEP = 170.0       # GUESS: no bot within this of the charge on the glass (its radii are 1.0 on this build:
                        # kl_fa_author.BLAST_HARMLESS; this is for the look, not for damage)
INVISI_KEEP = 330.0     # the InvisiBomb's first radius is 300 (kl_fa_author.INVISIBOMB): no bot inside it
PARK_GAP = 150.0        # the gather square beside the tower car begins at least this far from the jump box (GUESS: the
                        # human has to walk INTO that box; seven bots standing in it would be in his way)
PARK_SQUARE = 160.0     # half side of the gather square (kl_fa_bots puts the seven within ALLY_SIZE * INSIDE = 157)
ARRIVE = (300.0, 900.0)  # the bots arrive this far in front of the jump entry (the entry is INSIDE the lobby car:
                        # kl_fa_author.CAR_B; car A's box is 433 deep, so its door is ~216 from the middle)
ARRIVE_SEP = 120.0      # between two arrival places (the game's own crew jump puts them 100 apart: kl2 0x8f4100)
STOP_RING = (150.0, 650.0)   # the last places: this far from the boarding box at the van's stop (kl_fa_bots.PARK is
                        # 150..400; here the lane itself is kept clear, which costs 350 of it)
LANE_SOUTH = 800.0      # the van's lane is kept clear from this far south of its waiting place (GUESS) to the end of the map
EXIT_SHARE = 0.9        # a 'level exit' place lies within this share of the box's half extents (0.45 would leave no
                        # place on the pavement side of the lane: the box is x -5700..-300, the lane x -1850)
DEFAULTS = {'tower_only': False, 'loot_seconds': LOOT_SECONDS, 'after_blast': AFTER_BLAST, 'street_hold': STREET_HOLD, 'tree': True,
            'room_gate': ROOM_GATE, 'room_wait': ROOM_WAIT}


# ------------------------------------------------------------------ small things
def warp(nav, i):
    return max(abs(nav.height(i, v[0], v[2]) - v[1]) for v in nav.pv[i])


def flat(nav, c):
    return warp(nav, c[3]) <= WARP


def hdist(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def rect_dist(p, box):
    """Distance in the plan from point p to the rectangle of a ((x0, x1), (y0, y1), (z0, z1)) box."""
    dx = max(box[0][0] - p[0], 0.0, p[0] - box[0][1])
    dz = max(box[2][0] - p[2], 0.0, p[2] - box[2][1])
    return math.hypot(dx, dz)


def blast_seconds(B):
    """Field 0 of the level's blast timer (seconds after the round-start event), or None."""
    hit = B.sc.resolve(R_ + BLAST_TIMER)
    for k, _i, v in kl_fa.controllers(B.sc, 'TriggerDelay2'):
        if hit and k == hit[0]:
            return float(v[0])
    return None


def join_point(B):
    """(node, place, facing in the plan) of the jump entry. A JumpPoint's entry direction is its local -Z
    (kl_fa_author, read in run RT5): for 06_Exit (-1, 0), out of the car's door."""
    hit = B.sc.resolve(R_ + JOIN_NAME)
    if len(hit) != 1 or not kl_fa.has(B.sc, hit[0], 'JumpPoint'):
        raise ValueError('no JumpPoint %s in the build' % JOIN_NAME)
    Rm = B.fr[B.ents[hit[0] - 1]][0]
    return hit[0], B.at(hit[0]), (-Rm[0][2], -Rm[2][2])


def lane(p):
    """Is p in the strip the van drives through (waiting place .. the end of its drive)?"""
    return abs(p[0] - van.LANE_X) < street.VAN_CLEAR and p[2] >= van.WAIT_Z - LANE_SOUTH


def walk(nav, pts):
    """The mesh path through `pts` [(x, y, z, polygon)] in order, as points; None when a leg has no path."""
    out = [pts[0][:3]]
    for a, b in zip(pts, pts[1:]):
        got = nav.path(a, b)
        if got is None:
            return None
        out += got[0][1:]
    return out


def samples(poly, step=20.0):
    for p, q in zip(poly, poly[1:]):
        n = max(1, int(math.dist(p, q) // step))
        for t in range(n + 1):
            yield tuple(p[i] + (q[i] - p[i]) * t / n for i in range(3))


def straight(nav, part, a, b):
    """Does the straight line from a to b stay on the mesh of `part` (a sample every 20, each within 120 of the
    line's height) and out of the van's lane?"""
    return all(not lane(m) and nav.at(m[0], m[1], m[2], dy=120.0, part=part) is not None for m in samples([a[:3], b[:3]]))


def rides_with_van(B, act):
    """Is the boarding action a child of the van standing at kl_fa_van's waiting place? (kl_fa_street lays the box
    BOARD_BACK behind the van's origin; the van's keys take it to STOP_Z.)"""
    ap = B.at(act)
    return '\\V_Van_' in B.sc.path[act] and abs(ap[2] - (van.WAIT_Z - street.BOARD_BACK)) < 5.0 and abs(ap[0] - van.LANE_X) < 5.0


# ------------------------------------------------------------------ the tower half
def tower_park(B, nav, home, log=print):
    """Where the seven gather: a square of mesh beside the jump box of KLJoin.ini, not in it. -> (x, y, z)."""
    jb = au.JOIN_BOX
    mid = tuple((a + b) / 2 for a, b in jb)
    c = nav.around(mid, 900.0, home, dy=200.0)
    if not c:
        raise ValueError('no mesh of the START row\'s part within 900 of the jump box')
    best = None
    for q in c:
        if rect_dist(q, jb) - PARK_SQUARE < PARK_GAP:
            continue
        n = sum(1 for o in c if abs(o[0] - q[0]) <= PARK_SQUARE and abs(o[2] - q[2]) <= PARK_SQUARE and abs(o[1] - q[1]) < 30.0)
        key = (n, -rect_dist(q, jb))                    # the fullest square, then the nearest to the box
        if best is None or key > best[0]:
            best = (key, q)
    if best is None:
        raise ValueError('no place for a gather square beside the jump box')
    (n, d), q = best
    log('tower: the seven gather round (%d, %d, %d): %d of %d grid places of the square are mesh; its edge is %d from the jump box x %d..%d z %d..%d'
        % (*q[:3], n, (2 * int(PARK_SQUARE // 40) + 1) ** 2, -d - PARK_SQUARE, *jb[0], *jb[2]))
    return q[:3]


def ledge_starts(B, nav, S, log=print):
    """Seven places on the balcony outside the main window (kl_fa_author.LEDGE), beside the START stacks, clear of
    the charge and of the InvisiBomb -> [(x, y, z, polygon)]."""
    (x0, x1), (z0, z1) = au.LEDGE
    home = S['home']
    c = [q for q in nav.around((sum(au.LEDGE[0]) / 2, au.LEDGE_Y, sum(au.LEDGE[1]) / 2), 1300.0, home)
         if x0 <= q[0] <= x1 and z0 <= q[2] <= z1 and flat(nav, q)
         and F.START_NEAR <= min(hdist(q, p) for p, _f in S['starts']) <= F.START_FAR
         and hdist(q, au.BOMB) >= BOMB_KEEP and hdist(q, au.INVISIBOMB) >= INVISI_KEEP]
    # The balcony's mesh is 170 wide: 'nearest to the middle first' (Nav.spots) finds six. So: a greedy pick along
    # the balcony, in several orders, the widest spacing that gives seven, of those the pick with the most clearance.
    c = [q for q in c if nav.clearance(*q[:3]) >= F.CLEAR_MIN + 10.0]
    got = []
    for sep in (F.SEP + 20.0, F.SEP, 90.0):             # stock: at least ~100 apart; kl_fa_bots.check wants 80
        tries = []
        for key in (lambda q: (q[2], q[0]), lambda q: (q[2], -q[0]), lambda q: (-q[2], q[0]), lambda q: (-q[2], -q[0]),
                    lambda q: (-nav.clearance(*q[:3]), q[2])):
            pick = []
            for q in sorted(c, key=key):
                if len(pick) < 7 and all(hdist(q, o) >= sep for o in pick):
                    pick.append(q)
            if len(pick) == 7:
                tries.append(pick)
        if tries:
            got = max(tries, key=lambda pk: (min(nav.clearance(*q[:3]) for q in pk), -max(hdist(q, au.BOMB) for q in pk)))
            got.sort(key=lambda q: q[2])
            break
    if len(got) < 7:
        raise ValueError('only %d places for the seven bots on the balcony (%d candidates)' % (len(got), len(c)))
    log('tower: the seven start on the balcony (x %d..%d, glass at x 5860): x %d..%d, z %d..%d, y %d; %d..%d from the charge, %d..%d from the InvisiBomb, clearance %d..%d'
        % (x0, x1, min(g[0] for g in got), max(g[0] for g in got), min(g[2] for g in got), max(g[2] for g in got), got[0][1],
           min(hdist(g, au.BOMB) for g in got), max(hdist(g, au.BOMB) for g in got),
           min(hdist(g, au.INVISIBOMB) for g in got), max(hdist(g, au.INVISIBOMB) for g in got),
           min(nav.clearance(*g[:3]) for g in got), max(nav.clearance(*g[:3]) for g in got)))
    return got


def flatten(B, nav, S, P, log=print):
    """kl_fa_bots.plan put places on polygons whose fitted height is wrong (WARP): each is moved to the nearest
    place on a flat polygon of the same part - inside the same trigger box when the station is one."""
    home, moved = S['home'], 0
    for si, st in enumerate(P['stations']):
        node = B.sc.resolve(R_ + st['node'])[0] if st['node'] else None
        for b, N in enumerate(F.BOTS):
            p = st['places'][b]
            hit = nav.at(p[0], p[1], p[2], dy=15.0)
            if hit and warp(nav, hit[0]) <= WARP:
                continue
            others = [st['places'][o] for o in range(7) if o != b]
            c = [q for q in nav.around(p, 400.0, home, dy=260.0) if flat(nav, q) and (node is None or B.in_box(node, q[:3]))]
            c.sort(key=lambda q: (min([hdist(q, o) for o in others] or [1e9]) < F.SEP * 0.5, nav.clearance(*q[:3]) < F.CLEAR_MIN + 10, hdist(q, p)))
            if not c:
                raise ValueError('station %d (%s): no flat polygon for the place (%d, %d, %d)' % (si + 1, st['what'], *p))
            q = [round(v, 1) for v in c[0][:3]]
            st['places'][b] = q
            P['bots'][N]['places'][si] = q
            moved += 1
    if moved:
        log('tower: %d places moved off polygons whose fitted height is off by more than %d (the window\'s pentagon)' % (moved, WARP))
    return moved


def tower_plan(B, opt, log=print):
    nav = F.Nav(B.scene.nav)
    S = F.stations(B, nav)
    blast = blast_seconds(B)
    if blast is None:
        raise ValueError('no blast timer %s in the build: is it a Retomoto build of kl_fa_author?' % BLAST_TIMER)
    delay = blast + float(opt['after_blast'])
    log('tower: the level\'s blast timer runs %.1f s after the round-start event; Timer_start_bots = %.1f s' % (blast, delay))
    park = tower_park(B, nav, S['home'], log)
    P = F.plan(B, {'park': list(park), 'ally_box': 'on', 'start_delay': delay, 'loot_seconds': int(opt['loot_seconds']), 'tree': opt['tree']}, log)
    stand = ledge_starts(B, nav, S, log)
    for b, N in enumerate(F.BOTS):
        P['bots'][N]['start'] = [round(v, 1) for v in stand[b][:3]]
        P['bots'][N]['face'] = [-1.0, 0.0]              # into the room (kl_fa_author.IN), as the START points face
    flatten(B, nav, S, P, log)
    P['rt'] = collections.OrderedDict(blast_timer=blast, tower_park=[round(v, 1) for v in park], options=dict(opt))
    return nav, S, P


# ------------------------------------------------------------------ the street half
def street_plan(B, nav, S, opt, log=print):
    """-> dict: part, arrive (7 places for the hook), stations [{kind, what, node, places (7)}], steps, notes."""
    sc, notes = B.sc, []
    name = lambda k: sc.path[k][5:]
    jp, jpos, face = join_point(B)
    hit = nav.at(jpos[0], jpos[1], jpos[2], lo=jpos[1] - 300.0, hi=jpos[1] + 100.0)
    if hit is None:
        raise ValueError('the jump entry %s at (%d, %d, %d) is not over the navigation mesh' % (JOIN_NAME, *jpos))
    part = nav.part[hit[0]]
    if part == S['home']:
        raise ValueError('the jump entry is on the START row\'s own mesh part: this map needs no second leg (use kl_fa_bots)')
    j0 = (jpos[0], hit[1], jpos[2], hit[0])
    log('street: jump entry %s at (%d, %d, %d), floor %d, facing (%g, %g); its mesh part has %d polygons (the START row\'s %d)'
        % (JOIN_NAME, *jpos, hit[1], *face, nav.part_size[part], nav.part_size[S['home']]))
    lane_z0 = van.WAIT_Z - LANE_SOUTH
    # ---- where the hook puts the seven: in front of the car's door
    c = [q for q in nav.around(j0, ARRIVE[1], part, dy=60.0)
         if flat(nav, q) and (q[0] - jpos[0]) * face[0] + (q[2] - jpos[2]) * face[1] >= ARRIVE[0] and hdist(q, jpos) <= ARRIVE[1]]
    arrive = nav.spots(c, 7, ARRIVE_SEP, ref=(jpos[0] + face[0] * ARRIVE[0], hit[1], jpos[2] + face[1] * ARRIVE[0]))
    if len(arrive) < 7:
        raise ValueError('only %d arrival places in front of the jump entry (%d candidates)' % (len(arrive), len(c)))
    a1 = arrive[0]
    # ---- the van's stop
    act = S['action']
    ap = B.at(act)
    veh = S['vehicle'] and S['vehicle'][2]
    if rides_with_van(B, act):
        stop = (ap[0], ap[1], ap[2] + van.STOP_Z - van.WAIT_Z)
        log('street: the boarding box %s stands at (%d, %d, %d) = the van\'s waiting place (kl_fa_van WAIT_Z %d - %d behind its origin); it rides '
            'with the van to the stop: (%d, %d, %d)' % (name(act), *ap, van.WAIT_Z, street.BOARD_BACK, *stop))
    else:
        stop = ap
        notes.append('the boarding box %s at (%d, %d, %d) is not at kl_fa_van\'s waiting place: its own place is taken as the stop' % (name(act), *ap))
    sh = nav.at(stop[0], stop[1], stop[2], part=part, lo=stop[1] - 400.0, hi=stop[1] + 200.0)
    if sh is None:
        raise ValueError('the van\'s stop (%d, %d, %d) is not over the mesh part of the jump entry' % stop)
    s0 = (stop[0], sh[1], stop[2], sh[0])
    # ---- THE LANE. The van stands at its waiting place and drives north through the stop to the end of the map
    # (kl_fa_van: one straight line x = LANE_X); its nose carries a KillBox (kl_fa_street.VAN_CLEAR). The road's
    # polygons are 20 m wide, so the lane cannot be cut out of the mesh: instead every place from LANE_SOUTH before
    # the waiting place on lies on ONE side of the lane - the side the way from the lobby comes up on - and the
    # last legs are laid as straight lines that are tested to stay on the mesh and out of the lane.
    got = nav.path(a1, s0)
    if got is None:
        raise ValueError('no path on the mesh from the lobby to the van\'s stop')
    side = 1.0
    for p in got[0]:
        if p[2] >= lane_z0:
            break
        side = 1.0 if p[0] > van.LANE_X else -1.0
    good = lambda q: flat(nav, q) and (q[2] < lane_z0 or (q[0] - van.LANE_X) * side >= street.VAN_CLEAR)
    d_from = nav.dist_map(a1[3], a1[:3])[0]
    d_to = nav.dist_map(s0[3], s0[:3])[0]
    ring = [q for q in nav.around(s0, STOP_RING[1], part, dy=120.0) if good(q) and STOP_RING[0] <= hdist(q, s0) <= STOP_RING[1] and q[3] in d_from]
    if not ring:
        raise ValueError('no place %d..%d from the van\'s stop on the %s side of its lane' % (*STOP_RING, 'east' if side > 0 else 'west'))
    park0 = min(ring, key=lambda q: (hdist(q, s0), abs(q[2] - s0[2])))
    ring = [q for q in ring if hdist(q, park0) <= 420.0]

    def best(k, share, what, cost):
        c = [q for q in F.box_places(B, nav, k, part, share=share) if good(q) and q[3] in d_from and q[3] in d_to]
        if not c:
            notes.append('%s %s at (%d, %d, %d): no place inside it on the way' % (what, name(k), *B.at(k)))
            return None
        least = min(cost(q) for q in c)
        return max((q for q in c if cost(q) <= least + 120.0), key=lambda q: nav.clearance(*q[:3])), [q for q in c if cost(q) <= least + 400.0]

    seq = [('arrive', 'the lobby, in front of the car', a1, None, None)]
    for k in S['triggers'].get('EXITS', [])[:1]:
        got = best(k, F.INSIDE, 'EXITS_BANK', lambda q: d_from[q[3]] + d_to[q[3]])
        if got:
            seq.append(('exit', 'EXITS_BANK %s (stage 2)' % name(k), got[0], k, got[1]))
    lev = None
    for k in S['exits']:
        got = best(k, EXIT_SHARE, 'level exit', lambda q: d_from[q[3]] + math.dist(q[:3], nav.mid[q[3]]) + hdist(q, park0))
        if got and (lev is None or d_from[got[0][3]] < d_from[lev[2][3]]):
            lev = ('level', 'level exit %s (stage 3; a bot inside it calls the van: kl2 0x6cd8e0)' % name(k), got[0], k, got[1])
    if lev is None:
        raise ValueError('no level exit box with a place on the street part: the bots would never board')
    seq.append(lev)
    seq.append(('park', 'beside the van\'s stop, %d..%d from the boarding box, on the %s side of its lane' % (*STOP_RING, 'east' if side > 0 else 'west'), park0, None, ring))
    exits = S['exits']
    inbox = lambda q: bool(F.in_exit(B, exits, q))
    route, total = [], 0.0
    for (ka, _wa, a, _na, _ca), (kb, wb, b, nb_, cb) in zip(seq, seq[1:]):
        if straight(nav, part, a, b):
            pts = [a[:3], b[:3]]
        else:
            got = nav.path(a, b)
            if got is None:
                raise ValueError('no path on the street part from %s to %s' % (ka, kb))
            pts = got[0]
        length = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
        total += length
        run, nxt = 0.0, F.SPACING
        for p, q in zip(pts, pts[1:]):
            d = math.dist(p, q)
            while d > 0 and run + d >= nxt and length - nxt > F.SPACING * 0.5:
                t = (nxt - run) / d
                m = tuple(p[i] + (q[i] - p[i]) * t for i in range(3))
                c = [x for x in nav.around(m, 260.0, part, dy=260.0) if good(x) and (kb != 'level' or not inbox(x))]
                s = (nav.spots(c, 1, 0.0, ref=m) or [None])[0]
                if s:
                    route.append(('way', 'on the way to %s' % kb, s, None, None))
                nxt += F.SPACING
            run += d
        route.append((kb, wb, b, nb_, cb))
    # the hold: the last station before the level exit box must lie outside it
    i_lev = next(i for i, r in enumerate(route) if r[0] == 'level')
    hold = float(opt['street_hold'])
    if hold > 0 and i_lev == 0:
        notes.append('no station before the level exit box: no hold')
        hold = 0.0
    places = []
    for i, (kind, what, anchor, node, cands) in enumerate(route):
        if cands:
            got = nav.spots(cands, 7, F.SEP, ref=anchor)
            if len(got) < 7:
                got = nav.spots(cands, 7, 50.0, ref=anchor) or got
        else:
            c = [x for x in nav.around(anchor, 260.0, part) if good(x) and (i > i_lev or not inbox(x))]
            got = nav.spots(c, 7, F.SEP, ref=anchor) or [anchor]
        if hold > 0 and i == i_lev - 1:
            kind, what = 'rally', 'the rally place before the level exit box (hold %g s)' % hold
        places.append({'kind': kind, 'what': what, 'node': name(node) if node else None, 'distinct_places': len(got),
                       'places': [[round(v, 1) for v in got[b % len(got)][:3]] for b in range(7)]})
        log('  %-6s %-84s round (%6d %5d %6d): %d distinct places, clearance %d..%d' % (
            kind, what[:84], *anchor[:3], len(got), min(nav.clearance(*g[:3]) for g in got), max(nav.clearance(*g[:3]) for g in got)))
    # steps: up to STEP_MAX places each; the hold splits them; a step does not END on a place all seven share
    # (kl_fa_bots: they would hold on the stairs)
    steps = []
    def cut(idx, base, word):
        chunk, n = [], 0
        for i in idx:
            chunk.append(i)
            keep = []
            if len(chunk) == F.STEP_MAX and places[i]['distinct_places'] < 7 and i != idx[-1]:
                keep = [chunk.pop()]
            if i == idx[-1] or len(chunk) >= F.STEP_MAX or keep:
                steps.append({'name': '%03d_DefendBehaviour_%s' % (base + n, word), 'stations': chunk})
                chunk, n = keep, n + 1
    first = list(range(i_lev)) if hold > 0 else list(range(len(places)))
    cut(first, 50, 'street')
    if hold > 0:
        steps.append({'name': '070_Timer_rally', 'hold': hold})
        cut(list(range(i_lev, len(places))), 80, 'to_van')
    if any(int(s['name'][:3]) >= 70 for s in steps if 'stations' in s and 'street' in s['name']):
        raise ValueError('too many street steps for the names')
    log('street: %d of path from the lobby to the stop, %d stations in %d steps%s; arrival places x %d..%d z %d..%d, %d..%d from the jump entry'
        % (total, len(places), len([s for s in steps if 'stations' in s]), ', a hold of %g s before the level exit box' % hold if hold > 0 else '',
           min(a[0] for a in arrive), max(a[0] for a in arrive), min(a[2] for a in arrive), max(a[2] for a in arrive),
           min(hdist(a, jpos) for a in arrive), max(hdist(a, jpos) for a in arrive)))
    for n in notes:
        log('  NOTE ' + n)
    return collections.OrderedDict(
        join={'node': JOIN_NAME, 'at': [round(v, 1) for v in jpos], 'facing': list(face), 'floor': round(hit[1], 1)},
        mesh_part_polygons=nav.part_size[part], arrive=[[round(v, 1) for v in a[:3]] for a in arrive],
        stop=[round(v, 1) for v in s0[:3]], boarding_box=name(act), vehicle=veh, lane_side='east' if side > 0 else 'west',
        lane_from_z=lane_z0, path_length=round(total), hold=hold, stations=places, steps=steps, notes=notes)


SQ = lambda N, tail='': '%s%sSquad#0%d%s' % (R_, F.SQUAD, N, tail)
LAST = '090_SquadModifier_tight_defense_van'


class Street:
    """The second leg, for kl_fa_bots.apply(more=...): nodes(M, tops) adds the street steps to the seven squads,
    edit(Jn) writes the JumpPoint's list. Every node is a clone of the F07 form kl_fa_bots.make uses."""

    def __init__(self, st, room=None):
        self.st = st
        self.firsts = []
        self.room = room          # {'fallback': seconds after the round-start event} or None

    def nodes(self, M, tops):
        st, Sx = self.st, 'F07'
        if self.room:
            t = next(n for n in tops if n.name == F.SQUAD + 'Timer_start_bots')
            body = next(b for nm, b in t.ctrls if M.p.key(nm) == 'TriggerDelay2')
            first = [M.p.key(tok) for tok in [list(u) for u in units(body[1:-1])][4][1:]]      # the seven first steps
            gate = M.clone(Sx, R_ + 'Gameplay!RunToEscape!tcRunToEscape', GATE_NAME)
            M.place(gate, (0.0, 0.0, 0.0))
            M.set(gate, 'TriggerCounter', {0: 1, 1: 4294967295, 2: 0, 3: 0, 4: first})
            tops.append(gate)
            M.set(t, 'TriggerDelay2', {0: float(self.room['fallback']), 4: [R_ + GATE_NAME]})
        if st is None:
            return
        for b, N in enumerate(F.BOTS):
            top = tops[b]
            if top.name != F.SQUAD + 'Squad#0%d' % N:
                raise ValueError('kl_fa_bots.make: squad %d is %s' % (N, top.name))
            chain = [s['name'] for s in st['steps']] + [LAST]
            nxt = {a: [SQ(N, '\\' + c)] for a, c in zip(chain, chain[1:])}
            for s in st['steps']:
                if 'hold' in s:
                    w = top.add(M.clone(Sx, R_ + F.SQUAD + 'Timer_start_bots', s['name']))
                    M.place(w, (0.0, 0.0, 0.0))
                    M.set(w, 'TriggerDelay2', {0: float(s['hold']), 1: 0.0, 2: -1.0, 3: 0, 4: nxt[s['name']]})
                    continue
                g = top.add(M.clone(Sx, SQ(2, '\\020_DefendBehaviour_rout_merc_fight_left'), s['name']))
                M.place(g, (0.0, 0.0, 0.0))
                refs = []
                for j, si in enumerate(s['stations']):
                    box = g.add(M.clone(Sx, SQ(2, '\\020_DefendBehaviour_rout_merc_fight_left\\Pos#01'), 'Pos#%02d' % (j + 1)))
                    M.place(box, st['stations'][si]['places'][b])
                    refs.append(SQ(N, '\\%s\\Pos#%02d' % (s['name'], j + 1)))
                # eDMS_Sprint as on kl_fa_bots' way out (re/bots.md 8: ASSUMPTION that it suits)
                M.set(g, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_Sprint', 5: 'eDF_NotSet', 6: '', 7: nxt[s['name']], 8: 1, 9: 0})
            g = top.add(M.clone(Sx, SQ(2, '\\100_SquadModifier_tight_defense_van'), LAST))
            M.place(g, (0.0, 0.0, 0.0))
            M.set(g, 'SquadModifierBehaviour', {0: 'eLM_Leash', 9: 'eDM_Tight', 26: []})
            self.firsts.append(SQ(N, '\\' + chain[0]))

    def edit(self, Jn):
        if self.room:
            c = Jn.resolve(R_ + ROOM_COUNTER)[0]
            ci = next(i for i, (nm, _b) in enumerate(Jn.nodes[c]['ctrls']) if Jn.p.key(nm) == 'TriggerCounter')
            def fc(us):
                have = [Jn.p.key(t) for t in us[4][1:]]
                us[4] = kl_fa._refs(Jn, have + [R_ + GATE_NAME])
            kl_fa.edit(Jn, c, ci, fc)
        if self.st is None:
            return
        k = Jn.resolve(R_ + JOIN_NAME)[0]
        i = next(i for i, (nm, _b) in enumerate(Jn.nodes[k]['ctrls']) if Jn.p.key(nm) == 'JumpPoint')
        firsts = self.firsts
        def fn(us):
            have = [Jn.p.key(t) for t in us[0][1:]]
            us[0] = kl_fa._refs(Jn, have + [f for f in firsts if f.lower() not in [h.lower() for h in have]])
        kl_fa.edit(Jn, k, i, fn)


CREW_HEAD = """
; ---- [CrewJoin]: written by tools\\kl_fa_bots_rt.py. Read by KLHook's klcrew_rt.c, and only when KLHook.ini has
; [CrewJoin] Enable=1. The tower's navigation mesh does not reach the lobby, so the AI heisters cannot walk there.
; When kljoin.c's jump request for the entry named here is pending (the tick BEFORE the game moves the player), every
; AI heister still in play is put on one of the places below by the game's own actor teleport (kl2 0x62a900). The
; game then moves the player and sends 'AITrigger' to the entry's own list, which starts the bots' street route.
; Late form (the request was not seen pending): the same when a local player stands within Radius of Target after
; he was farther than From from it.
; Places = feet on the lobby's navigation mesh in front of the car's door, record order (the n-th AI crew record
; in play gets Place.n). Lift = added to the height of every place (0: the mesh height, as the level places a bot).
"""


def write_ini(dst, st, log=print):
    """Append the [CrewJoin] section to <dst>/KLJoin.ini (the file kl_fa_bots.apply copied from the source build)."""
    p = os.path.join(dst, 'KLJoin.ini')
    if not os.path.isfile(p):
        raise ValueError('%s: no KLJoin.ini (the build has no join)' % dst)
    text = open(p, encoding='latin1').read()
    if '[CrewJoin]' in text:
        text = text[:text.index('[CrewJoin]')].rstrip('\n')
        text = text[:text.rindex('; ---- [CrewJoin]')].rstrip('\n') + '\n' if '; ---- [CrewJoin]' in text else text + '\n'
    j = st['join']
    lines = [CREW_HEAD.rstrip('\n'), '[CrewJoin]', 'Name=%s' % JOIN_NAME.split('!')[-1], 'Target=%g %g %g' % tuple(j['at']), 'Tolerance=8',
             'Radius=300', 'From=2000', 'Lift=0', 'Places=%d' % len(st['arrive'])]
    lines += ['Place.%d=%g %g %g' % (i + 1, *a) for i, a in enumerate(st['arrive'])]
    with open(p, 'w', encoding='latin1', newline='\r\n') as f:
        f.write(text.rstrip('\n') + '\n' + '\n'.join(lines) + '\n')
    log('written %s: [CrewJoin] with %d places' % (p, len(st['arrive'])))


def read_ini(folder):
    """{'join': {...}, 'crew': {...}} of <folder>/KLJoin.ini (plain reading, as GetPrivateProfileString would)."""
    out, sec = collections.defaultdict(dict), None
    p = os.path.join(folder, 'KLJoin.ini')
    if not os.path.isfile(p):
        return out
    for ln in open(p, encoding='latin1'):
        ln = ln.strip()
        if ln.startswith('[') and ln.endswith(']'):
            sec = ln[1:-1].lower()
        elif sec and '=' in ln and not ln.startswith(';'):
            k, v = ln.split('=', 1)
            out[sec][k.strip().lower()] = v.strip()
    return out


def vec(s):
    return tuple(float(x) for x in s.replace(',', ' ').split())


# ------------------------------------------------------------------ the check of this module
def check(folder, log=print):
    """What kl_fa_bots.check does not look at: the balcony start, the gather place, the JumpPoint's list, the street
    chain on ITS mesh part, the van's lane, the [CrewJoin] places. -> ([(severity, text)], facts)."""
    B = F.Built(folder)
    sc, nav, out = B.sc, F.Nav(B.scene.nav), []
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    name = lambda k: sc.path[k][5:]
    res = sc.resolve
    S = F.stations(B, nav)
    home = S['home']
    facts = collections.OrderedDict()
    allies = sorted((k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and B.values(k)['ZFFActor[0]'] == 'Ally'), key=lambda k: sc.names[sc.top[k]])
    # 1. the start: on the balcony, outside the glass, after the blast
    (x0, x1), (z0, z1) = au.LEDGE
    feet = [B.at(k) for k in allies]
    off = [f for f in feet if not (x0 <= f[0] <= x1 and z0 <= f[2] <= z1)]
    if off:
        fail('%d bots do not start on the balcony (x %d..%d, z %d..%d), e.g. (%d, %d, %d): the glass at x 5860 keeps the players out until the blast'
             % (len(off), x0, x1, z0, z1, *off[0]))
    near = [f for f in feet if hdist(f, au.INVISIBOMB) < 300.0]
    if near:
        fail('%d bots start inside the InvisiBomb\'s first radius (300)' % len(near))
    blast = blast_seconds(B)
    tv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if res(R_ + F.SQUAD + 'Timer_start_bots') and k == res(R_ + F.SQUAD + 'Timer_start_bots')[0]]
    delay = tv[0][0] if tv else None
    facts['start'] = {'blast_timer': blast, 'Timer_start_bots': delay, 'bots': [[round(v) for v in f] for f in feet]}
    if blast is None or delay is None:
        fail('no blast timer or no Timer_start_bots')
    elif delay <= blast:
        fail('Timer_start_bots (%.1f s) does not wait for the blast timer (%.1f s): the bots would walk at the intact glass' % (delay, blast))
    gate = res(R_ + GATE_NAME)
    if gate:
        gv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if k == gate[0]][0]
        cv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if res(R_ + ROOM_COUNTER) and k == res(R_ + ROOM_COUNTER)[0]]
        fed = cv and any(s.lower() == (R_ + GATE_NAME).lower() for s in cv[0][4])
        facts['room_gate'] = {'counter_names_gate': bool(fed), 'gate_count': gv[0], 'gate_names': len(gv[4]), 'fallback': delay}
        if not fed:
            fail('the room counter %s does not name %s' % (ROOM_COUNTER, GATE_NAME))
        if gv[0] != 1 or len(gv[4]) != len(F.BOTS) or any(not res(s) for s in gv[4]):
            fail('%s: count %d, names %d of %d first steps' % (GATE_NAME, gv[0], len(gv[4]), len(F.BOTS)))
        if tv and [s.lower() for s in tv[0][4]] != [(R_ + GATE_NAME).lower()]:
            fail('Timer_start_bots does not name the gate alone: %s' % tv[0][4])
    # 2. the chains
    NEXT = {'DefendBehaviourRout': 7, 'SquadModifierBehaviour': 26, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerActorsDead': 2}
    mine = {k for t in sc.tops() if sc.names[t].startswith(F.SQUAD) for k in range(t, sc.end[t])}
    ctrl_of = {}
    for cn in NEXT:
        for k, _i, v in kl_fa.controllers(sc, cn):
            if k in mine:
                ctrl_of[k] = (cn, v)

    # A RandomTrigger between two steps (kl_fa_bots_dyn's random routes; this module makes none): the chain forks.
    # As in kl_fa_bots.check, a chain is then walked once per BRANCH SET v: branch v mod (number of branches) at
    # every fork - so every branch of every fork is walked and checked. forks[0] = the widest fork met.
    rand_of = F.fork_branches(sc, mine)
    forks = [1]

    def chain(k, variant=0):
        """-> (places [node], index of the first place after a wait or None, ends tight, the wait's seconds, faults)"""
        places, seen, tight, n_wait, secs, bad = [], set(), False, None, None, []
        while k is not None and k not in seen:
            seen.add(k)
            if k in rand_of and k not in ctrl_of:
                br = rand_of[k]
                forks[0] = max(forks[0], len(br))
                k = br[variant % len(br)] if br else None
                continue
            cn, v = ctrl_of.get(k, (None, None))
            if cn is None:
                bad.append('the chain reaches %s, which has no behaviour or wait controller' % name(k)); break
            if cn == 'DefendBehaviourRout':
                places += [j for s in ([v[0]] if v[0] else []) + list(v[1]) for j in res(s)]
            elif cn == 'SquadModifierBehaviour':
                tight = v[9] == 'eDM_Tight'
            elif n_wait is None:
                n_wait, secs = len(places), v[0] if cn == 'TriggerDelay2' else v[1]
            nx = [j for s in v[NEXT[cn]] for j in res(s)]
            k = nx[0] if nx else None
        return places, n_wait, tight, secs, bad

    timer = res(R_ + F.SQUAD + 'Timer_start_bots')
    firsts = tv[0][4] if tv else []
    jb = au.JOIN_BOX
    ally_boxes = [k for k, _i, _v in kl_fa.controllers(sc, 'AllyEscapeBox')]
    tower_end = {}
    for k in allies:
        top = sc.top[k]
        f = [j for s in firsts for j in res(s) if sc.top[j] == top]
        # (the tower's LAST place is behind every fork: a fork's branches rejoin before it. The places of the
        # tower's branches are kl_fa_bots.check's business, which walks every branch set)
        places, _nw, _t, _secs, _bad = chain(f[0]) if f else ([], None, False, None, [])
        if not places:
            continue
        last = B.at(places[-1])
        tower_end[sc.names[top]] = [round(v) for v in last]
        if rect_dist(last, jb) < 60.0:
            fail('%s: its last tower place (%d, %d, %d) is in or at the jump box of KLJoin.ini (x %d..%d, z %d..%d): the bots would stand where the '
                 'human has to walk' % (sc.names[top], *last, *jb[0], *jb[2]))
        if rect_dist(last, jb) > 1200.0:
            note('%s: its last tower place is %d from the jump box' % (sc.names[top], rect_dist(last, jb)))
        if not any(B.in_box(a, last) for a in ally_boxes):
            fail('%s: its last tower place is in no AllyEscapeBox (the fall-back when the hook part is off)' % sc.names[top])
    facts['tower_end'] = tower_end
    # 3. the JumpPoint and the street chain
    ini = read_ini(B.folder)
    jp = res(R_ + JOIN_NAME)
    jv = [v for k, _i, v in kl_fa.controllers(sc, 'JumpPoint') if jp and k == jp[0]]
    lst = jv[0][0] if jv else []
    facts['jump_list'] = len(lst)
    if not lst:
        note('TOWER ONLY: %s names nothing; the bots end beside the tower car and board through the AllyEscapeBox' % JOIN_NAME)
        if 'crewjoin' in ini:
            fail('KLJoin.ini has a [CrewJoin] section but the JumpPoint starts no street route: the hook would move bots that have no way on')
    else:
        jpos = B.at(jp[0])
        j = ini.get('join', {})
        if j.get('name', '') not in JOIN_NAME or 'target' not in j or max(abs(a - b) for a, b in zip(vec(j['target']), jpos)) > float(j.get('tolerance', 8)):
            fail('KLJoin.ini [Join] (Name %s, Target %s) does not name %s at (%d, %d, %d)' % (j.get('name'), j.get('target'), JOIN_NAME, *jpos))
        hit = nav.at(jpos[0], jpos[1], jpos[2], lo=jpos[1] - 300.0, hi=jpos[1] + 100.0)
        part = hit and nav.part[hit[0]]
        if hit is None or part == home:
            fail('the jump entry is not on a mesh part of its own')
        tgt = [x for s in lst for x in res(s)]
        if len(tgt) != len(lst):
            fail('%s: %d of its %d list entries do not resolve' % (JOIN_NAME, len(lst) - len(tgt), len(lst)))
        tops = collections.Counter(sc.top[x] for x in tgt)
        if set(tops) != {sc.top[k] for k in allies} or any(n != 1 for n in tops.values()):
            fail('%s names %d steps in %d squads (wanted: one first street step in each of the %d)' % (JOIN_NAME, len(tgt), len(tops), len(allies)))
        if any(ctrl_of.get(x, (None,))[0] != 'DefendBehaviourRout' for x in tgt):
            fail('%s names something that is no DefendBehaviourRout step (kl2 0x72e0f0 sends it \'AITrigger\')' % JOIN_NAME)
        act = S['action']
        ap = B.at(act)
        stop = (ap[0], ap[1], ap[2] + van.STOP_Z - van.WAIT_Z) if rides_with_van(B, act) else ap
        if hit and nav.at(stop[0], stop[1], stop[2], part=part, lo=stop[1] - 400.0, hi=stop[1] + 200.0) is None:
            fail('the van\'s stop (%d, %d, %d) is not over the street\'s mesh part: ZBoardEscapeVehicleTactic\'s path test would fail' % stop)
        crew = ini.get('crewjoin', {})
        arr = [vec(crew['place.%d' % (i + 1)]) for i in range(int(crew.get('places', 0))) if 'place.%d' % (i + 1) in crew]
        facts['crew_places'] = [[round(v) for v in a] for a in arr]
        if len(arr) < len(allies):
            fail('KLJoin.ini [CrewJoin] has %d places for %d bots' % (len(arr), len(allies)))
        if crew and (crew.get('name', '') not in JOIN_NAME or max(abs(a - b) for a, b in zip(vec(crew.get('target', '0 0 0')), jpos)) > 8):
            fail('KLJoin.ini [CrewJoin] Name / Target do not name the jump entry')
        ah = []
        for a in arr:
            h = nav.at(a[0], a[1], a[2], dy=15.0, part=part)
            if h is None or warp(nav, h[0]) > WARP:
                fail('[CrewJoin] place (%d, %d, %d) is not on a flat polygon of the street part at its height' % a); continue
            ah.append(tuple(a) + (h[0],))
            if nav.clearance(*a) < F.CLEAR_MIN:
                fail('[CrewJoin] place (%d, %d, %d) is %d from a mesh edge without a neighbour' % (*a, nav.clearance(*a)))
            if hdist(a, jpos) < 150.0:
                fail('[CrewJoin] place (%d, %d, %d) is %d from the jump entry: a bot would be put into the player' % (*a, hdist(a, jpos)))
        apart = min([hdist(a, b) for i, a in enumerate(arr) for b in arr[i + 1:]] or [0])
        if arr and apart < 80.0:
            fail('two [CrewJoin] places are %d apart' % apart)
        routes = collections.OrderedDict()
        enters_exit = S['triggers'].get('EXITS', [])
        jobs = [(x, 0) for x in sorted(tgt, key=lambda x: sc.names[sc.top[x]])]
        said, variant = set(), 0
        fail = lambda s: None if (variant and ('FAIL', s) in said) else (said.add(('FAIL', s)), out.append(('FAIL', s)))[0]
        note = lambda s: None if (variant and ('NOTE', s) in said) else (said.add(('NOTE', s)), out.append(('NOTE', s)))[0]
        branch_sets = collections.OrderedDict()
        for x, variant in jobs:                         # (a further branch set of a forking chain: findings said once)
            sq = sc.names[sc.top[x]]
            forks[0] = 1
            places, n_wait, tight, secs, bad = chain(x, variant)
            if variant == 0 and forks[0] > 1:
                jobs += [(x, n_v) for n_v in range(1, forks[0])]
                branch_sets[sq] = forks[0]
            for t in bad:
                fail('%s (street): %s' % (sq, t))
            pts, low, ok = [], 1e9, True
            for jn in places:
                p = B.at(jn)
                h = nav.at(p[0], p[1], p[2], dy=15.0)
                if h is None:
                    fail('%s (street): %s at (%d, %d, %d) is not on a walkable polygon within 15 of the mesh\'s height' % (sq, name(jn), *p)); ok = False; continue
                if nav.part[h[0]] != part:
                    fail('%s (street): %s at (%d, %d, %d) is not on the jump entry\'s mesh part' % (sq, name(jn), *p)); ok = False; continue
                if warp(nav, h[0]) > WARP:
                    fail('%s (street): %s stands on a polygon whose fitted height is off by %d' % (sq, name(jn), warp(nav, h[0])))
                c = nav.clearance(*p)
                low = min(low, c)
                if c < F.CLEAR_MIN:
                    fail('%s (street): %s at (%d, %d, %d): %d from a mesh edge without a neighbour' % (sq, name(jn), *p, c))
                if lane(p):
                    fail('%s (street): %s at (%d, %d, %d) is in the van\'s lane (x %d +- %d from z %d): its nose carries a KillBox' % (sq, name(jn), *p, van.LANE_X, street.VAN_CLEAR, van.WAIT_Z - LANE_SOUTH))
                pts.append(tuple(p) + (h[0],))
            if not ok or not pts:
                continue
            # a way from EVERY [CrewJoin] place (the hook gives places by record order, not by squad) through the places
            length, cross = 0.0, 0
            for a in ah:
                poly = walk(nav, [a] + pts)
                if poly is None:
                    fail('%s (street): no path on the mesh from [CrewJoin] place (%d, %d, %d) along its places' % (sq, *a[:3])); break
                length = max(length, sum(math.dist(p, q) for p, q in zip(poly, poly[1:])))
            # the van's lane: from LANE_SOUTH before its waiting place on, every place on ONE side of it, and the
            # straight line from each place to the next on the mesh and out of the lane (the road's polygons are too
            # large for this module's portal path to say where a walker goes; a straight line that is all mesh is
            # the way any pathfinder takes)
            zone = [i for i, p in enumerate(pts) if p[2] >= van.WAIT_Z - LANE_SOUTH]
            sides = {p[0] > van.LANE_X for i, p in enumerate(pts) if i in zone}
            if len(sides) > 1:
                fail('%s (street): its places lie on BOTH sides of the van\'s lane: it would cross it' % sq)
            for i in zone:
                if i and not straight(nav, part, pts[i - 1], pts[i]):
                    cross += 1
            if cross:
                note('%s (street): %d legs near the van are not a straight line on the mesh clear of its lane (the pathfinder\'s way there is not known)' % (sq, cross))
            st2 = any(B.in_box(t, p[:3]) for t in enters_exit for p in pts)
            st3 = [i for i, p in enumerate(pts) if F.in_exit(B, S['exits'], p[:3])]
            if not st2:
                note('%s (street): no place inside an EXITS_BANK box (stage 2 is skipped; stage 3 does not need it)' % sq)
            if not st3:
                fail('%s (street): no place inside the level exit box: no stage 3, the bot never boards (kl2 0x4faf60)' % sq)
            elif n_wait is not None and st3[0] < n_wait:
                fail('%s (street): place %d is inside the level exit box BEFORE the hold: the van is called before the squad has gathered' % (sq, st3[0] + 1))
            call = F.first_exit_entry(B, nav, S['exits'], [ah[0]] + pts) if S['exits'] and ah else None
            if call and n_wait is not None and call[1] <= n_wait:
                fail('%s (street): the path enters the level exit box on the way to place %d of the %d before the hold' % (sq, call[1], n_wait))
            d = hdist(pts[-1], stop)
            if not STOP_RING[0] - 1 <= d <= STOP_RING[1] + 1:
                fail('%s (street): its last place is %d from the boarding box at the stop (wanted %d..%d)' % (sq, d, *STOP_RING))
            if not tight:
                note('%s (street): the chain does not end in a tight-defense SquadModifierBehaviour' % sq)
            route = {'places': [[round(v) for v in p[:3]] for p in pts], 'path_length_longest': round(length), 'least_clearance': round(low),
                     'stage_2': st2, 'stage_3_from_place': st3[0] + 1 if st3 else None, 'places_before_the_hold': n_wait, 'hold_seconds': secs,
                     'first_inside_the_exit_box': call and {'path': round(call[0]), 'place': call[1]}, 'last_place_from_the_stop': round(d),
                     'legs_near_the_van_not_straight': cross, 'side_of_the_lane': 'east' if sides == {True} else 'west' if sides == {False} else None}
            if variant == 0:
                routes[sq] = route
            else:
                facts.setdefault('street_branches', collections.OrderedDict()).setdefault(sq, []).append(route)
        variant = 0
        if branch_sets:
            log('street forks (a RandomTrigger between two steps): every branch walked and checked, in up to %d branch sets a squad' % max(branch_sets.values()))
        facts['street'] = routes
        facts['stop'] = [round(v) for v in stop]
    facts['big'] = F.sizes(folder)
    out.sort(key=lambda x: x[0] != 'FAIL')
    for sev, text in out:
        log('%-4s %s' % (sev, text))
    for nm, r in facts.get('street', {}).items():
        log('  %s street: %d places, longest path %d, least clearance %d, stage 2 %s, stage 3 from place %s, hold after place %s (%s s), last place %d from the stop'
            % (nm, len(r['places']), r['path_length_longest'], r['least_clearance'], r['stage_2'], r['stage_3_from_place'], r['places_before_the_hold'], r['hold_seconds'], r['last_place_from_the_stop']))
    log('RESULT (kl_fa_bots_rt): %s (%d FAIL, %d NOTE); start delay %s s after a blast at %s s; jump list %d; [CrewJoin] places %d'
        % ('PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL', sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out),
           delay, blast, len(lst), len(facts.get('crew_places', []))))
    return out, facts


# ------------------------------------------------------------------ build
def plan(B, opt=None, log=print):
    opt = dict(DEFAULTS, **(opt or {}))
    nav, S, P = tower_plan(B, opt, log)
    st = None
    if not opt['tower_only']:
        st = street_plan(B, nav, S, opt, log)
        P['rt']['street'] = st
    return P, st


def build(src, dst, opt=None, log=print):
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    opt = dict(DEFAULTS, **(opt or {}))
    B = F.Built(src)
    say('kl_fa_bots_rt build %s -> %s (%s)' % (src, dst, 'tower only' if opt['tower_only'] else 'tower + street'))
    P, st = plan(B, opt, say)
    room = {'fallback': blast_seconds(B) + float(opt['room_wait'])} if opt['room_gate'] else None
    if room:
        say('tower: the room first - the bots\' chain starts from %s through %s; fall-back Timer_start_bots at %.1f s after the round-start event (blast + %.0f s)' % (
            ROOM_COUNTER, GATE_NAME, room['fallback'], float(opt['room_wait'])))
    more = Street(st, room) if (st or room) else None
    rep = F.apply(B, P, dst, say, more=more)
    if st:
        write_ini(dst, st, say)
    out, facts = F.check(dst, say)
    out2, facts2 = check(dst, say)
    rep.update(plan=P, check=[list(x) for x in out], facts=facts, check_rt=[list(x) for x in out2], facts_rt=facts2)
    with open(os.path.join(dst, 'bots.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'bots.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out + out2, rep


def options(a):
    opt = {}
    if '--tower-only' in a:
        a.remove('--tower-only'); opt['tower_only'] = True
    if '--no-tree' in a:
        a.remove('--no-tree'); opt['tree'] = False
    if '--enter-after-blast' in a:
        a.remove('--enter-after-blast'); opt['room_gate'] = False
    for flag, key, conv in (('--loot-seconds', 'loot_seconds', int), ('--after-blast', 'after_blast', float), ('--street-hold', 'street_hold', float),
                            ('--room-wait', 'room_wait', float)):
        if flag in a:
            i = a.index(flag)
            opt[key] = conv(a[i + 1]); del a[i:i + 2]
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'plan':
        P, st = plan(F.Built(a[1]), opt)
        for N, b in P['bots'].items():
            print('Squad#0%d: starts at %s; tower places %s' % (N, tuple(b['start']), b['places']))
            if st:
                print('          street places %s' % [s['places'][N - 2] for s in st['stations']])
        if st:
            print('[CrewJoin] places: %s' % st['arrive'])
            print('street steps: %s' % [(s['name'], s.get('stations', s.get('hold'))) for s in st['steps']])
    elif len(a) == 2 and a[0] == 'check':
        out, _f = F.check(a[1])
        out2, _f2 = check(a[1])
        sys.exit(1 if any(s == 'FAIL' for s, _t in out + out2) else 0)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if F.diff(a[1], a[2], also=(JOIN_NAME,)) else 0)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
