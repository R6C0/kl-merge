#!/usr/bin/env python3
"""
CIVILIANS FOR A FINISHED FRAGILE ALLIANCE BUILD: a post-step that adds N frightened civilians (Dog Days' own form) to a
build folder made by kl_fa_club / kl_fa_bank / ... Research and decisions: re/civilians.md.
OFFLINE: nothing here installs anything or starts the game. NOTHING OF IT HAS RUN IN THE GAME.

The owner (re/owner_feedback_1017.md): 'LOTS of civilians' on Last Call (club), Withdrawal (bank), Hot Coffee, later
others; 'more gritty and brutal'.

    python kl_fa_civs.py census <folder> [slot]            actors / squads / civilians / models of a build (read only)
    python kl_fa_civs.py plan <folder> <slot> <N> [--centre x y z --radius R --seed S]
                                                          N places on the build's own navigation mesh (read only)
    python kl_fa_civs.py build <folder> <slot> <out> <N> [--centre x y z --radius R --model auto|F07|<chunk>
                                                          --alert R --no-tree --seed S]
                                                          plan + write + every check of this module; exit 1 on a FAIL
    python kl_fa_civs.py check <folder> [slot] [--play]    this module's rules on a folder made by build; exit 1 on a FAIL
    NEW FLAGS (2026-10-18; without them every output is byte-identical to before; GUESS = a value not measured):
      --play-part [--play-radius R=2000 --play-band H=400]   plan/build: the mesh part of the START spawns (else the part with most
                                          guards/bots) instead of the largest; centre = the start; places only within R of the centre AND of a
                                          spawn/guard/bot, within H of the start floor; written to civs.json 'play'. R 1500..2500 is a GUESS.
                                          Why: the largest part of Last Call is the street network at y~220, not the club (2026-10-18).
      --cap [--max-actors 99 --max-squads 55]   build: N is cut so actors/squads of the result stay under the caps (each civilian is 1 actor
                                          and 1 squad); 0 left = nothing written, exit 3. 99/55 is a GUESS (the largest build that ran live).
      --avoid-bounds [--bounds-margin M=150]   plan/build: no civilian, flee point or straight run line within M of a LevelBound kill box (2026-10-18:
                                          Last Call's StreetLeft/StreetRight bounds killed the scripted player next to civilians 002/009/004;
                                          M is a GUESS). check --play FAILs a civilian or flee point inside a box, or a straight run through one (margin 0).
      --start-clear [M=150]               plan/build: no post whose run box (the --alert half extents + M, in x, z and y) would hold a START spawn
                                          (2026-10-18, run N1018_L7: the 1200 boxes held 8-10 of 10 START spawns, so 20_RunToStreet fired at second 0 and
                                          nobody was seen; M is a GUESS). check (ALWAYS, no flag; check-only, build outputs unchanged): FAIL when a START
                                          spawn lies inside any civilian's tbCivRunToGate box (real place and half extents read from the built files).
      --play                              check: also apply the play-area rules (automatic when civs.json has 'play') and print a per-part census.
    python kl_fa_civs.py diff <folder> <out> [slot]        what the step changed; exit 1 if anything but the new nodes
    python kl_fa_civs.py selftest                          builds on a temp copy of a finished build (skips if none)

API (all of it importable; nothing happens at import)
    add(src, dst, civs, slot='F01', model='auto', alert=1200.0, tree=True, max_prm_growth=0, log=print) -> report dict
        src   a finished build folder (holds <slot>_Main.zip), dst a new EMPTY folder (src is never touched)
        civs  [dict(pos=(x, y, z)[, face=(dx, dz)][, flee=[(x, y, z), ...]][, model=<chunk>])]
              pos = where she stands; flee = the places she runs to when a player comes near, in order (default: two
              places picked on the mesh by flee_points(); a civilian with no mesh and no flee list is refused)
        model 'auto'  the model most guards of the build wear (no .prm growth; GUESS that it fits the Civilian
                      animation database - the skeleton is shared, but no run has shown a guard model walking the
                      civilian clips)
              <int>   a live model root chunk of the build's .prm (census() lists them)
              'F07'   Dog Days' own civilian (stock F07, chunk 1794) appended with its materials and textures by
                      kl_prmgraph.append (the kl_fa_ropevis recipe): +~0.57 MB of .prm, so max_prm_growth must allow it
        alert half extent (x and z) of the box that makes her run: she runs when a player is inside it (GUESS that
              the three values are HALF extents: stock F07's box has centre y 299 and y value 314, i.e. 0..613, a person)
        seal  call kl_fa_bank.seal(dst) at the end (default; the club's and the bank's check() FAIL without it: the new entities
              take the REF ids that the 'parked' room-list entries name)
        tree  list her groups in the root's group tree 3 of the .oct as the bots' groups are (stock lists groups, not boxes)
    census(B) -> dict, flee_points(nav, post, ...), plan_places(B, n, ...) -> civs, check(folder, slot), diff(src, dst, slot),
    selftest().

WHAT ONE CIVILIAN IS (stock F07 'Gameplay!000_Civilians!001_Civilian_01', read whole; re/civilians.md)
    top ZGROUP + ZSquadScript (12 members at most, soldiers and civilians cannot mix: one civilian a squad as in stock)
      30_SquadModifier_Deactivate  ZGROUP + SquadModifierBehaviour (eAM_Deactivate: the squad AI is off once she ran)
      20_RunToStreet               ZGROUP + MiniCutsceneRout; field 0 is the script text '((Actor| NAME| ((move| ((subt| 1)|
                                   (mode| run)| (dst| POSOBJECT)| (_dep| ())))| ...)))| (Options| ...)', field 1 the
                                   rout's NEXT = the Deactivate modifier
        Flee_NN                    ZSTDOBJ + MiniCutPosObject: the flee points (the script names them)
      Civ_NNN                      ZGROUP at her post; its child 'Ground' = the ZFFActor (team Neutral) with ZCivilian
      tbCivRunToGate               ZBoxPrimitive + TriggerBox (eTGS_AllInside) -> 20_RunToStreet
    Stock also has a RandomTrigger -> Timer pair and a second 10_RunToGaate rout; neither is read by anything that
    matters here and they are left out (GUESS: the pair is dead; it has no target past the Timer).
    The actor's ints that point into level files (ZLNKOBJ / ZLNKWHANDS = .SND offsets 241120, 340736, 349360, 265616)
    are stock F07's: the finished builds keep F07's .SND records at the same offsets (proven by comparing the records).

FLEEING IS DOG DAYS' OWN MECHANISM, not Dead Men's: Dead Men had a ZLIST 'FLEEPOINTS' + Pos# nodes (the string exists
only in kaneandlynch.exe); Dog Days' civilians run a MiniCutsceneRout script when a trigger fires (stock F07/F08/L**).
What the ZCivilian controller does on its own (panic at shots, ragdoll, 'attacked' squad list 0x7b4918) is NOT read.

LIMITS (stock Dog Days, census of the 21 levels: re/civilians.md)
    most civilians in one level 60 (L01); most actors 148 (L07); most squads 90 (L07); most nodes 42,915 (L10);
    stock Fragile Alliance levels: <= 13 civilians (F01), <= 57 actors, <= 36 squads.
    Each civilian here adds 8 entities (top, modifier, rout, 2 flee points, group, actor, trigger).
    The .prm pool limit is 73,728 chunks (the bank build has 65,852): an appended model is ~55 chunks, once.
    Actors are networked by 16-bit scene references (re/netcode.md); how many AI actors a match tolerates: not measured.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, math, os, random, re, shutil, struct, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene
import kl_octree as O
import kl_prpjoin as J
import kl_fa_bots as F
from kl_prp import Prp

HOST = 'F07'
FORM = 'ROOT\\Gameplay!000_Civilians!001_Civilian_01'
FORM_CIV = 'Civ_In_The_Streets_M_06'
TOPS = 'Gameplay!FA_Crowd!Civ_%03d'          # GUESS: any name; stock's own are 'Gameplay!000_Civilians!00N_Civilian_NN'
MODEL_F07 = 1794                             # the stock F07 civilian's ZGEOM[4] (.prm chunk of the model root)
OLD_RE = re.compile(r'\(Actor\| ' + re.escape(FORM_CIV) + r'\|')
MOVE = '(move| ((subt| 1)| (mode| run)| (dst| %s)| (_dep| ())))'
SCRIPT = '((Actor| %s| (%s))| (Options| Options| ((mode| unbreakable-vulnerable))))'
FLEE_MIN, FLEE_MAX = 1800.0, 4500.0          # GUESS: stock's two flee points are 1.4 m..96 m away (F07 civilian 001: 9.7 km!)
SEP = 150.0                                  # GUESS: civilians at least this far apart (the bots' SEP is 110)
CIV_PER_SQUAD = 1                            # stock: one civilian a squad


# ------------------------------------------------------------------ what is there
def census(B):
    """-> dict: actors, civilians, squads, nodes, models {chunk: n} of non-civilian actors by squad group name."""
    sc = B.sc
    out = collections.OrderedDict(actors=0, civilians=0, squads=0, nodes=len(sc.nodes) - 1, models=collections.Counter(),
                                  guard_models=collections.Counter())
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZFFActor':
            out['actors'] += 1
            m = B.values(k)['ZGEOM[4]']
            if kl_fa.has(sc, k, 'ZCivilian'):
                out['civilians'] += 1
            else:
                out['models'][m] += 1
                if sc.names[sc.parent[k]].lower().startswith('guard'):
                    out['guard_models'][m] += 1
        out['squads'] += sum(1 for nm, _b in sc.nodes[k]['ctrls'] if sc.p.key(nm) == 'ZSquadScript')
    return out


def live_model(prm, m):
    """True when chunk m of the parsed .prm is a model root that the graph walk accepts."""
    import kl_prmgraph as G
    try:
        G.walk(prm, [m])
        return True
    except Exception:
        return False


def auto_model(B):
    """The most common live model among the guards of the build (GUESS: it looks like a person in a suit)."""
    import kl_prmgraph as G
    prm = G.read(B['.prm'], 'dd')
    c = census(B)
    for m, _n in (c['guard_models'] or c['models']).most_common():
        if live_model(prm, m):
            return m
    raise ValueError('no live actor model in the build')


# ------------------------------------------------------------------ placing
def flee_points(nav, post, k=2, lo=FLEE_MIN, hi=FLEE_MAX, away=None, rng=None, keep=None):
    """Up to k places on the mesh part of `post` (x, y, z, polygon) that a civilian can run to: reached by a path of
    lo..hi, each in another direction than the ones before. `away` = a point to run from (preferred direction).
    keep (new, --avoid-bounds): a test (start, place) -> bool every place must pass."""
    rng = rng or random.Random(0)
    hit = nav.at(*post[:3])
    if not hit:
        return []
    part = nav.part[hit[0]]
    a = (post[0], hit[1], post[2], hit[0])
    cands = nav.around(a, hi, part, step=250.0, dy=400.0)
    dist, _prev, _at = nav.dist_map(a[3], a[:3])
    good = [c for c in cands if lo <= dist.get(c[3], 1e30) <= hi * 1.3 and lo <= math.hypot(c[0] - a[0], c[2] - a[2])
            and abs(c[1] - a[1]) <= 200.0 and nav.clearance(c[0], c[1], c[2]) >= F.CLEAR]   # same floor (+-2 m)
    if keep is not None:
        good = [c for c in good if keep(a, c)]
    out = []
    rng.shuffle(good)
    for _ in range(k):
        best = None
        for c in good:
            ang = math.atan2(c[2] - a[2], c[0] - a[0])
            sep = min([abs((ang - o[1] + math.pi) % (2 * math.pi) - math.pi) for o in out] or [math.pi])
            score = sep + (0.0 if away is None else math.hypot(c[0] - away[0], c[2] - away[2]) / 20000.0)
            if best is None or score > best[0]:
                best = (score, c, ang)
        if best is None:
            break
        out.append((best[1], best[2]))
        good.remove(best[1])
    return [(c[0], c[1], c[2]) for c, _a in out]


# ------------------------------------------------------------------ the play area (flags --play-part / --cap; default builds do not use it)
PLAY_RADIUS = 2000.0                         # GUESS (1500..2500): how far from the spawn / a guard / a bot a civilian may stand
PLAY_BAND = 400.0                            # GUESS: half height of the y-band around the start floor (one floor, not the one above)
CAP_ACTORS, CAP_SQUADS = 99, 55              # GUESS: the largest build that ran live (kl_fa_bank.ACTORS_LIVE); not a measured engine limit


BOUND_MARGIN = 150.0                         # GUESS: how far outside a LevelBound kill box a civilian or her flee point must stay


def bound_boxes(B):
    """[(node, half (x, y, z))]: every ZBoxPrimitive with a LevelBound controller (the 'KILLED BY: AN ACCIDENT' volume: two
    one-step deaths at Last Call's StreetLeft / StreetRight bounds, run N1018_L2c, 2026-10-18)."""
    sc, out = B.sc, []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZBoxPrimitive' and any(sc.p.key(nm) == 'LevelBound' for nm, _b in sc.nodes[k]['ctrls']):
            v = B.values(k)
            out.append((k, tuple(abs(float(v['ZBoxPrimitive[%d]' % i])) for i in range(3))))
    return out


def in_bound(B, boxes, p, margin=BOUND_MARGIN):
    """The LevelBound node whose box (half extents + margin, in its own frame) holds the world point p, else None."""
    for k, h in boxes:
        q = B.local(k, p)
        if all(abs(q[i]) <= h[i] + margin for i in range(3)):
            return k
    return None


def crosses_bound(B, boxes, a, b, margin=BOUND_MARGIN, step=50.0):
    """The LevelBound node met on the straight line a -> b (sampled every `step`; the run follows the mesh, so this is a
    proxy, GUESS), else None. Height is taken at the ends' mean (the run stays on one floor)."""
    n = int(math.hypot(b[0] - a[0], b[2] - a[2]) / step) + 1
    for i in range(n + 1):
        t = i / n
        k = in_bound(B, boxes, (a[0] + (b[0] - a[0]) * t, (a[1] + b[1]) / 2, a[2] + (b[2] - a[2]) * t), margin)
        if k is not None:
            return k
    return None


def start_points(B):
    """World places of the ZSpawnPoint nodes of the round's START row (kl_fa.START)."""
    sc, out = B.sc, []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint' and any(isinstance(x, str) and x == kl_fa.START for x in kl_fa.node_values(sc, k)):
            out.append(tuple(B.at(k)))
    return out


def anchors(B):
    """Places a civilian should be near to be seen: the START spawns and every actor that is not a civilian (guards, bots)."""
    sc = B.sc
    out = list(start_points(B))
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZFFActor' and not kl_fa.has(sc, k, 'ZCivilian'):
            out.append(tuple(B.at(k)))
    return out


def play_area(B, nav, band=PLAY_BAND):
    """-> dict(part, centre, y0, source): the mesh part of the round's start (the START spawns float ~100 above the floor, as
    kl_fa_bots.stations looks for it), else the part holding most non-civilian actors. centre = the mean START place (or the
    mean of those actors), y0 = the floor under it."""
    starts = start_points(B)
    parts, floors = collections.Counter(), {}
    for p in starts:
        hit = nav.at(p[0], p[1], p[2], lo=p[1] - 260.0, hi=p[1] + 40.0)
        if hit:
            parts[nav.part[hit[0]]] += 1
            floors.setdefault(nav.part[hit[0]], []).append((p, hit[1]))
    if parts:
        part = parts.most_common(1)[0][0]
        pts = [p for p, _h in floors[part]]
        centre = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
        y0 = sum(h for _p, h in floors[part]) / len(floors[part])
        return dict(part=part, centre=centre, y0=y0, band=band, source='START spawn')
    sc, acts = B.sc, []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZFFActor' and not kl_fa.has(sc, k, 'ZCivilian'):
            p = tuple(B.at(k))
            hit = nav.at(p[0], p[1], p[2], dy=300.0)
            if hit:
                acts.append((nav.part[hit[0]], p, hit[1]))
    if not acts:
        raise ValueError('no START spawn and no actor stands on the navigation mesh: no play area')
    part = collections.Counter(a[0] for a in acts).most_common(1)[0][0]
    pts = [a for a in acts if a[0] == part]
    centre = tuple(sum(a[1][i] for a in pts) / len(pts) for i in range(3))
    return dict(part=part, centre=centre, y0=sum(a[2] for a in pts) / len(pts), band=band, source='most actors')


def part_census(B, nav, play=None):
    """-> {part: dict(polygons, actors, civilians, starts)} and, for every civilian, her part and distance to the start."""
    sc = B.sc
    rows = collections.defaultdict(lambda: dict(polygons=0, actors=0, civilians=0, starts=0))
    for i in range(len(nav.pv)):
        if nav.ok[i]:
            rows[nav.part[i]]['polygons'] += 1
    civ = []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor':
            continue
        p = tuple(B.at(k))
        hit = nav.at(p[0], p[1], p[2], dy=300.0)
        part = nav.part[hit[0]] if hit else None
        if kl_fa.has(sc, k, 'ZCivilian'):
            rows[part]['civilians'] += 1
            civ.append(dict(node=sc.names[sc.parent[k]], part=part, pos=p,
                            d_start=(math.hypot(p[0] - play['centre'][0], p[2] - play['centre'][2]) if play else None)))
        else:
            rows[part]['actors'] += 1
    for p in start_points(B):
        hit = nav.at(p[0], p[1], p[2], lo=p[1] - 260.0, hi=p[1] + 40.0)
        rows[nav.part[hit[0]] if hit else None]['starts'] += 1
    return dict(rows), civ


def cap_count(c, n, max_actors=CAP_ACTORS, max_squads=CAP_SQUADS):
    """How many of n civilians fit under the caps given census c (each adds one actor and one squad); never negative."""
    return max(0, min(n, max_actors - c['actors'], max_squads - c['squads']))


def plan_places(B, n, centre=None, radius=None, seed=1, away=None, sep=SEP, flee=2, play=None, bounds=None, start_clear=None, alert=1200.0):
    """n civilians placed on the build's own navigation mesh -> [civ dict] for add(). centre (x, y, z) and radius select
    the area (default radius None: the whole mesh part that holds most polygons, from the polygons' middles); places keep F.CLEAR from walls and `sep` from
    each other and from every actor already in the build (guards, bots).
    play (play_area() dict, new): the play part instead of the largest one, centre default = the start, radius default
    PLAY_RADIUS, places only within play['band'] of the start floor and within the radius of an anchor() (START spawn / guard / bot).
    bounds (new, --avoid-bounds): a margin; no place and no flee point within it of a LevelBound box (bound_boxes).
    start_clear (new, --start-clear): a margin M; no place whose run box (half extents `alert`, + M; y 314 + M about post y + 300)
    would hold a START spawn (start_points)."""
    rng = random.Random(seed)
    nav = F.Nav(B.scene.nav)
    parts = collections.Counter(nav.part[i] for i in range(len(nav.pv)) if nav.ok[i])
    if play is not None:
        part = play['part']
        if centre is None:
            centre = play['centre']
        if radius is None:
            radius = PLAY_RADIUS
    elif centre is None:
        part = parts.most_common(1)[0][0]
        i = nav.nearest((0, 0, 0), part)
        centre = tuple(nav.mid[i])
    else:
        hit = nav.at(*centre, dy=600.0)
        if not hit:
            raise ValueError('the centre %s is off the mesh' % (centre,))
        part = nav.part[hit[0]]
    if play is not None:
        hit = nav.at(centre[0], play['y0'], centre[2], dy=play['band'], part=part)
        if not hit:
            raise ValueError('the centre %s is off the play part %s' % (centre, part))
        centre = (centre[0], hit[1], centre[2])
    if radius is None:                              # the whole part: the polygons' middles and points half way to their corners
        cands = []
        for i in range(len(nav.pv)):
            if nav.ok[i] and nav.part[i] == part:
                m = nav.mid[i]
                cands.append((m[0], m[1], m[2], i))
                for v in nav.pv[i]:
                    x, z = (m[0] + v[0]) / 2, (m[2] + v[2]) / 2
                    h = nav.at(x, m[1], z, 300.0, part)
                    if h and h[0] == i:
                        cands.append((x, h[1], z, i))
    else:
        cands = nav.around(centre, radius, part, step=100.0, dy=600.0)
    rng.shuffle(cands)
    taken = [tuple(B.at(k)) for k in range(1, len(B.sc.nodes)) if B.sc.cls(k) == 'ZFFActor']
    near = anchors(B) if play is not None else None
    kill = bound_boxes(B) if bounds is not None else None
    starts = start_points(B) if start_clear is not None else None
    out = []
    for c in cands:
        if len(out) >= n:
            break
        if play is not None and (abs(c[1] - play['y0']) > play['band']
                                 or not any(math.hypot(c[0] - a[0], c[2] - a[2]) <= radius for a in near)):
            continue
        if nav.clearance(c[0], c[1], c[2]) < F.CLEAR:
            continue
        if any(math.hypot(c[0] - o[0], c[2] - o[2]) < sep for o in taken + [x['pos'] for x in out]):
            continue
        pos = (c[0], c[1], c[2])
        if bounds is not None and in_bound(B, kill, pos, bounds) is not None:
            continue
        if starts is not None and any(abs(s_[0] - pos[0]) <= alert + start_clear and abs(s_[2] - pos[2]) <= alert + start_clear
                                      and abs(s_[1] - (pos[1] + 300.0)) <= 314.0 + start_clear for s_ in starts):
            continue
        if bounds is None:
            fl = flee_points(nav, pos, flee, away=away, rng=rng)
        else:
            fl = flee_points(nav, pos, flee, away=away, rng=rng, keep=lambda s, f: crosses_bound(B, kill, s, f, bounds) is None)
        if not fl:                                 # a pocket of the mesh with nowhere to run to: she is not placed
            continue
        out.append(dict(pos=pos, face=(rng.uniform(-1, 1), rng.uniform(-1, 1)), flee=fl))
    return out


# ------------------------------------------------------------------ making the nodes
def _retarget(M, node, old, new):
    """Every reference token of node's controllers that starts with `old` (case ignored) now starts with `new`."""
    n = 0
    for i, (nm, body) in enumerate(node.ctrls):
        out = []
        for op, pl in body:
            if op == 0x0c and len(pl) == 4:
                s = M.p.keys[struct.unpack('<I', pl)[0]]
                if s.lower().startswith(old.lower()):
                    pl = struct.pack('<I', M.p.key_index(new + s[len(old):])); n += 1
            out.append((op, pl))
        node.ctrls[i] = (nm, out)
    return n


def make(B, civs, model, alert, log=print):
    """-> (maker, [top nodes], facts). Every form is a clone of stock F07's civilian; the fields set are named in the
    module docstring."""
    M = F.Maker()
    tops, facts = [], []
    n0 = 0                                   # one above the highest number in use (a build that lost some, as lastcall2's, has gaps)
    for t in B.sc.tops():
        m_ = re.fullmatch(re.escape(TOPS).replace('%03d', r'(\d+)'), B.sc.names[t])
        if m_:
            n0 = max(n0, int(m_.group(1)) + 1)
    for i, c in enumerate(civs):
        name = TOPS % (n0 + i)
        path = F.R_ + name
        if B.sc.resolve(path):
            raise ValueError('%s is already in the build' % path)
        if not c.get('flee'):
            raise ValueError('civilian %d: no flee points' % i)
        top = M.clone(HOST, FORM, name)
        M.place(top, (0.0, 0.0, 0.0))
        # ---- the squad modifier (stays as stock: nothing refers to a path in it)
        mod = top.add(M.clone(HOST, FORM + '\\30_SquadModifier_Deactivate'))
        M.place(mod, (0.0, 0.0, 0.0))
        # ---- the run: script text + flee points
        cname = 'Civ_FA_%03d' % (n0 + i)
        rout = top.add(M.clone(HOST, FORM + '\\20_RunToStreet'))
        M.place(rout, (0.0, 0.0, 0.0))
        flee = []
        for j, p in enumerate(c['flee']):
            f = rout.add(M.clone(HOST, FORM + '\\20_RunToStreet\\MoveToPosObject', 'Flee_%02d' % j))
            M.place(f, p)
            flee.append(f.name)
        script = SCRIPT % (cname, '| '.join(MOVE % f for f in flee))
        M.set(rout, 'MiniCutsceneRout', {0: script})
        _retarget(M, rout, F.R_ + FORM[5:], path)
        # ---- the civilian
        grp = top.add(M.clone(HOST, FORM + '\\' + FORM_CIV, cname))
        face = c.get('face') or (0.0, 1.0)
        M.place(grp, c['pos'], F.rot9(*face))
        act = grp.add(M.clone(HOST, FORM + '\\' + FORM_CIV + '\\Ground'))
        M.place(act, (0.0, 0.0, 0.0))
        m = c.get('model') or model
        act.model = m
        M.set(act, None, {'ZGEOM[4]': m})
        # ---- the trigger
        tb = top.add(M.clone(HOST, FORM + '\\tbCivRunToGate'))
        M.place(tb, (c['pos'][0], c['pos'][1] + 300.0, c['pos'][2]))
        M.set(tb, None, {'ZBoxPrimitive[0]': float(alert), 'ZBoxPrimitive[1]': 314.0, 'ZBoxPrimitive[2]': float(alert)})
        _retarget(M, tb, F.R_ + FORM[5:], path)
        tops.append(top)
        facts.append(collections.OrderedDict(path=path, post=[round(v, 1) for v in c['pos']], flee=[[round(v, 1) for v in p] for p in c['flee']],
                                             model=m, actor=cname))
    return M, tops, facts


# ------------------------------------------------------------------ the model of Dog Days' own civilian
def append_model(B, prm_bytes, log=print):
    """Stock F07's civilian closure appended to the build's .prm/.MAT/.TEX (the kl_fa_ropevis recipe) ->
    (new root chunk, .prm bytes, .MAT bytes, .TEX bytes, report). No .oct is involved (a model without collision)."""
    import kl_prmgraph as G, kl_texmat as T, kl_light
    with zipfile.ZipFile(J.level_zip(HOST, 'dd')) as z:
        m7 = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        p7, mat7, tex7 = G.read(z.read(m7['.prm']), 'dd'), T.read_mat(z.read(m7['.MAT'])), T.read_tex(z.read(m7['.TEX']))
    pD, matD, texD = G.read(prm_bytes, 'dd'), T.read_mat(B['.MAT']), T.read_tex(B['.TEX'])
    kinds, _args = G.walk(p7, [MODEL_F07])
    slots = {p7.u16(i, 0x12) for i, k in kinds.items() if k in ('mesh', 'scatter', 'water')}
    want = set(T.used_textures(mat7, slots))
    tex, tmap = T.merge_tex(texD, tex7, want)
    mat, mmap = T.merge_mat(matD, mat7, slots, tmap)
    prm, cmap = G.append(pD, p7, [MODEL_F07], mmap, None, tmap)
    root = cmap[MODEL_F07]
    zeroed = 0
    for i in kinds:                                  # F07's .oct collision records are not in this build: no record (kl_fa_ropevis does the same)
        c = prm.chunks[cmap[i]]
        if len(c) == 64 and c[:4] == bytes([0, 1, 7, 0]) and struct.unpack_from('<I', c, 0x1c)[0]:
            b = bytearray(c); struct.pack_into('<I', b, 0x1c, 0); prm.chunks[cmap[i]] = bytes(b); zeroed += 1
    lack = kl_light.missing_shaders(mat, B['.fxc'], [mmap[s] for s in slots])
    out = G.write(prm)
    mat.refs = T.material_refs(out, mat.ninst)
    rep = dict(chunks_appended=len(kinds), root=root, oct_records_zeroed=zeroed, materials=[mmap[s] for s in sorted(slots)], shaders_missing=str(lack or 'none'))
    log('  F07 civilian model: %d chunks appended (root %d), materials %s, shaders the .fxc lacks: %s'
        % (len(kinds), root, rep['materials'], lack or 'none'))
    return root, out, T.write_mat(mat), T.write_tex(tex), rep


# ------------------------------------------------------------------ writing
def add(src, dst, civs, slot='F01', model='auto', alert=1200.0, tree=True, max_prm_growth=0, seal=True, log=print, play=None):
    """Write the civilians into a copy of the finished build `src` in the new folder `dst` -> report dict."""
    import kl_graft, kl_prmgraph as G, kl_texmat as T
    B = F.Built(src, slot)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    if not civs:
        raise ValueError('no civilians')
    before = F.sizes(B.folder, slot)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    new = dict(B.files)
    prm_report = None
    if model == 'auto':
        model = auto_model(B)
    elif model == HOST:
        model, new[B.ext['.prm']], new[B.ext['.MAT']], new[B.ext['.TEX']], prm_report = append_model(B, B['.prm'], log)
        B.files[B.ext['.MAT']] = B.files[B.ext['.MAT']]          # (B is read only from here on)
    elif not isinstance(model, int) or not live_model(G.read(B['.prm'], 'dd'), model):
        raise ValueError('model %r is not a live model root of the build\'s .prm' % (model,))
    M, tops, facts = make(B, civs, model, alert, log)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'civs')
    bad = J.misfits(Jn)
    if bad:
        raise ValueError('objects that do not fit their class: %s' % [(Jn.path[k], w, y) for k, w, y in bad[:3]])
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made[id(n)] = e
        for k in n.kids:
            ent(k, e)
    for t in tops:
        ent(t, None)
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
    items = []
    if tree:
        for n in order:
            if not n.tid & kl_scene.GROUP or n.name.startswith('Civ_FA_'):      # the actor group is dynamic: not listed (as the bots')
                continue
            ps = [k.pos for k in n.walk() if k.name.startswith('Flee_')]
            if n.name.startswith('Gameplay!FA_Crowd!'):
                ps = ps + [k.pos for k in n.kids if k.name.startswith('Civ_FA_')]
            if ps:
                lo = tuple(min(p[a] for p in ps) - 10.0 for a in range(3))
                hi = tuple(max(p[a] for p in ps) + (10.0 if a != 1 else 190.0) for a in range(3))
                items.append((slot1[made[id(n)]] + 2, lo, hi))
    root3 = octn.rooms[0][3]
    listed, repointed = 0, 0
    prm_bytes = new[B.ext['.prm']]
    if root3 is not None and items:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        listed = len(items)
        octn.rooms[0][3].check()
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            prm = bytearray(prm_bytes)
            t, n = struct.unpack_from('<II', prm, 0)
            old = set(octx.record_refs())
            for i in range(1, n):
                o, size = struct.unpack_from('<II', prm, t + 16 * i)
                if size == 64 and prm[o:o + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', prm, o + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', prm, o + 0x1c, move[v]); repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            prm_bytes = bytes(prm)
            if B.ext['.MAT'] in new:
                pass
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.prm']] = prm_bytes
    if prm_report:
        mat = T.read_mat(new[B.ext['.MAT']])
        mat.refs = T.material_refs(prm_bytes, mat.ninst)
        new[B.ext['.MAT']] = T.write_mat(mat)
        if G.write(G.read(prm_bytes, 'dd')) != prm_bytes:
            raise ValueError('.prm does not round-trip')
        lost = T.used_textures(T.read_mat(new[B.ext['.MAT']])) - set(T.read_tex(new[B.ext['.TEX']]).tex)
        if lost:
            raise ValueError('materials name textures the .TEX lacks: %s' % sorted(lost)[:5])
    growth = len(prm_bytes) - len(B['.prm'])
    if growth > max_prm_growth:
        raise ValueError('the .prm would grow by %d bytes (max_prm_growth %d)' % (growth, max_prm_growth))
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'civs.')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst, slot)
    sealed = None
    if seal:                                    # the map tools' rule: after the last tool that adds entities, room-list entries that name
        import kl_fa_bank                       # nothing are moved to the free REF id (the new entities took the ids those entries named)
        sealed = kl_fa_bank.seal(dst, log=lambda *_: None)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):                                   # kl_maps.audit compares the folder with what was measured
        import kl_maps
        st = json.load(open(sj))
        st['civs'] = changed
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_civs: %d civilians (%d entities) from %s; model %s; alert %s\n' % (len(civs), len(order), B.folder, model, alert))
    rep = collections.OrderedDict(source=B.folder, out=dst, civilians=facts, model=model, entities_added=len(order), entities=len(ents),
                                  slot_ids_moved=moved, groups_listed_in_root_tree_3=listed, prm_roots_repointed=repointed,
                                  members_changed=changed, prm_growth=growth, big_before=before, big_after=after, model_append=prm_report, sealed=sealed)
    if play is not None:                                    # only with --play-part: the rules check() then applies
        rep['play'] = play
    with open(os.path.join(dst, 'civs.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    log('written %s: %d civilians, %d entities added; members changed: %s; %d slot ids renumbered, %d groups listed, '
        '%d model roots re-pointed; .prm %+d bytes' % (zp, len(civs), len(order), ' '.join(changed), moved, listed, repointed, growth))
    return rep


# ------------------------------------------------------------------ the check
def check(folder, slot='F01', log=print, play=False):
    """This module's rules on a folder made by add() -> (fails, notes). Reads civs.json for the civilians' names."""
    fails, notes = [], []
    B = F.Built(folder, slot)
    sc = B.sc
    cj = os.path.join(folder, 'civs.json')
    if not os.path.isfile(cj):
        return ['no civs.json: not a folder made by kl_fa_civs.add'], notes
    rep = json.load(open(cj))
    import kl_prmgraph as G
    prm = G.read(B['.prm'], 'dd')
    bad = J.misfits(sc)
    if bad:
        fails.append('%d objects do not fit their class' % len(bad))
    if F.Prp(B['.prp']).serialize() != B['.prp']:
        fails.append('.prp does not round-trip')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    nrs = F.room_sets_check(B.scene, octx, rmi, rmc)
    notes.append('room sets: %s' % (nrs,))
    for c in rep['civilians']:
        path = c['path']
        hit = sc.resolve(path)
        if len(hit) != 1:
            fails.append('%s: %d nodes' % (path, len(hit))); continue
        t = hit[0]
        if not kl_fa.has(sc, t, 'ZSquadScript') or sc.cls(t) != 'ZGROUP':
            fails.append('%s: not a ZGROUP with a ZSquadScript' % path)
        kids = {sc.names[j]: j for j in range(t + 1, sc.end[t]) if sc.parent[j] == t}
        grp = kids.get(c['actor'])
        rout = kids.get('20_RunToStreet')
        tb = kids.get('tbCivRunToGate')
        if None in (grp, rout, tb) or '30_SquadModifier_Deactivate' not in kids:
            fails.append('%s: a part is missing (%s)' % (path, sorted(kids))); continue
        actor = next((j for j in range(grp + 1, sc.end[grp]) if sc.cls(j) == 'ZFFActor' and kl_fa.has(sc, j, 'ZCivilian')), None)
        if actor is None:
            fails.append('%s: no ZFFActor with ZCivilian under %s' % (path, c['actor'])); continue
        v = B.values(actor)
        if v['ZGEOM[4]'] != c['model'] or not G.walk(prm, [c['model']]):
            fails.append('%s: model %s is not a live root' % (path, c['model']))
        script = kl_fa.controllers(sc, 'MiniCutsceneRout')
        s = next((x for k, _i, x in script if k == rout), None)
        flee = [sc.names[j] for j in range(rout + 1, sc.end[rout]) if sc.cls(j) == 'ZSTDOBJ']
        if not s or '(Actor| %s|' % c['actor'] not in s[0]:
            fails.append('%s: the script does not name her group %s' % (path, c['actor']))
        for f in flee:
            if '(dst| %s)' % f not in s[0]:
                fails.append('%s: the script does not walk to %s' % (path, f))
        if re.findall(r'\(dst\| ([^)]*)\)', s[0]) != flee:
            fails.append('%s: script destinations %s differ from flee nodes %s' % (path, re.findall(r'\(dst\| ([^)]*)\)', s[0]), flee))
        if not flee:
            fails.append('%s: no flee points' % path)
        tv = next((x for k, _i, x in kl_fa.controllers(sc, 'TriggerBox') if k == tb), None)
        if not tv or sc.resolve(tv[-1][0] if isinstance(tv[-1], list) and tv[-1] else '') != [rout]:
            fails.append('%s: the trigger does not start the run (%s)' % (path, tv and tv[-1]))
        nxt = s[1] if s else []
        if sc.resolve(nxt[0] if nxt else '') != [kids['30_SquadModifier_Deactivate']]:
            fails.append('%s: the run\'s NEXT is not the Deactivate modifier (%s)' % (path, nxt))
        if sum(1 for j in range(t, sc.end[t]) if sc.cls(j) == 'ZFFActor') != CIV_PER_SQUAD:
            fails.append('%s: more than %d actor in the squad' % (path, CIV_PER_SQUAD))
    least = start_clearance(B, fails, notes)
    if play or rep.get('play'):
        play_check(B, rep, fails, notes)
        kill = bound_boxes(B)                       # LevelBound kill boxes: nobody may stand or flee into one (margin 0 here)
        for c in rep['civilians']:
            hit = sc.resolve(c['path'])
            if len(hit) != 1:
                continue
            t = hit[0]
            me = next((tuple(B.at(j)) for j in range(t + 1, sc.end[t]) if sc.cls(j) == 'ZFFActor' and kl_fa.has(sc, j, 'ZCivilian')), None)
            for j in range(t + 1, sc.end[t]):
                if (sc.cls(j) == 'ZFFActor' and kl_fa.has(sc, j, 'ZCivilian')) or (sc.cls(j) == 'ZSTDOBJ' and sc.names[sc.parent[j]] == '20_RunToStreet'):
                    p = tuple(B.at(j))
                    b = in_bound(B, kill, p, 0.0)
                    if b is None and me is not None and sc.cls(j) == 'ZSTDOBJ':
                        b = crosses_bound(B, kill, me, p, 0.0)
                    if b is not None:
                        fails.append('%s: %s %s stands in or runs through the LevelBound kill box %s' % (
                            c['path'], sc.names[j], tuple(round(v) for v in p), sc.path[b].split('!', 1)[-1]))
        notes.append('LevelBound kill boxes: %d' % len(kill))
    log('%d civilians checked: %d FAIL, %d NOTE' % (len(rep['civilians']), len(fails), len(notes)))
    for x in fails:
        log('FAIL ' + x)
    for x in notes:
        log('NOTE ' + x)
    return fails, notes


def start_clearance(B, fails, notes):
    """New rule (2026-10-18): no START spawn may lie inside a civilian's tbCivRunToGate box, else 20_RunToStreet fires at second 0.
    Reads each box's real place and half extents from the built files (every ZBoxPrimitive named tbCivRunToGate). -> least clearance
    (horizontal distance a START spawn is outside a box, x and z; negative = inside), None without spawns or boxes."""
    sc = B.sc
    starts = start_points(B)
    boxes = []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k] == 'tbCivRunToGate':
            v = B.values(k)
            boxes.append((k, tuple(abs(float(v['ZBoxPrimitive[%d]' % i])) for i in range(3))))
    least = None
    for k, h in boxes:
        held = []
        for s_ in starts:
            q = B.local(k, s_)
            d = max(abs(q[i]) - h[i] for i in range(3))
            dh = max(abs(q[0]) - h[0], abs(q[2]) - h[2])          # the clearance reported is horizontal (y is always inside: 30 vs 0..628)
            least = dh if least is None or dh < least else least
            if d <= 0:
                held.append(s_)
        if held:
            fails.append('%s: its run box (half %s, at %s) holds %d of %d START spawns, e.g. %s: the run would fire at second 0' % (
                sc.path[sc.parent[k]].split('!', 1)[-1], tuple(round(x) for x in h), tuple(round(x) for x in B.at(k)), len(held), len(starts),
                tuple(round(x) for x in held[0])))
    if least is not None:
        notes.append('START clearance: %d spawns, %d run boxes, least horizontal distance outside a box %.0f (negative = inside)' % (len(starts), len(boxes), least))
    return least


def play_check(B, rep, fails, notes):
    """The play-area rules (only with check(play=True) or a civs.json made with --play-part): every civilian stands on the
    play part (the part of the START spawns), within the band of the start floor, within the radius of the centre (the start by
    default) and of an anchor (START spawn / guard / bot). Adds a per-part census to the notes."""
    pl = rep.get('play') or {}
    radius, band = float(pl.get('radius', PLAY_RADIUS)), float(pl.get('band', PLAY_BAND))
    nav = F.Nav(B.scene.nav)
    area = play_area(B, nav, band)
    centre = tuple(pl.get('centre') or area['centre'])
    rows, civ = part_census(B, nav, dict(area, centre=centre))
    notes.append('play part %s (from %s), start %s, floor y %.0f, radius %.0f, band %.0f' % (
        area['part'], area['source'], tuple(round(v) for v in centre), area['y0'], radius, band))
    for part in sorted(rows, key=lambda q: (q is None, q)):
        r = rows[part]
        notes.append('part %s%s: %d polygons, %d actors, %d civilians, %d START spawns' % (
            part, ' (PLAY)' if part == area['part'] else '', r['polygons'], r['actors'], r['civilians'], r['starts']))
    near = anchors(B)
    ds = []
    for c in civ:
        p, d = c['pos'], c['d_start']
        ds.append(d)
        if c['part'] != area['part']:
            fails.append('%s: on mesh part %s, the play part is %s' % (c['node'], c['part'], area['part']))
        if d > radius + 1e-3:
            fails.append('%s: %.0f from the centre (radius %.0f)' % (c['node'], d, radius))
        if abs(p[1] - area['y0']) > band + 1e-3:
            fails.append('%s: y %.0f is %.0f from the start floor (band %.0f)' % (c['node'], p[1], abs(p[1] - area['y0']), band))
        if not any(math.hypot(p[0] - a[0], p[2] - a[2]) <= radius + 1e-3 for a in near):
            fails.append('%s: no spawn, guard or bot within %.0f' % (c['node'], radius))
    if ds:
        ds.sort()
        notes.append('civilians: %d, distance to the start min %.0f median %.0f max %.0f' % (len(ds), ds[0], ds[len(ds) // 2], ds[-1]))


def diff(src, dst, slot='F01', log=print):
    """What the step changed -> list of problems (empty = only the new nodes, and tree/id bookkeeping)."""
    A, B = F.Built(src, slot), F.Built(dst, slot)
    out = []
    ka = J.fingerprints(A.sc)[0]
    kb = J.fingerprints(B.sc)[0]
    # every old node unchanged: the fingerprint lists (path -> hash) of A are a subset of B's
    if isinstance(ka, dict) and isinstance(kb, dict):
        miss = [p for p, h in ka.items() if kb.get(p) != h]
        if miss:
            out.append('%d old nodes changed or lost, e.g. %s' % (len(miss), miss[:2]))
    new_names = [n for n in B.sc.names[1:] if n not in set(A.sc.names[1:])]
    log('%d nodes in %s, %d in %s (%d new names)' % (len(A.sc.names) - 1, src, len(B.sc.names) - 1, dst, len(new_names)))
    for e in ('.ANM', '.fxc', '.SND', '.LOC', '.TEX', '.MAT'):
        if e in A.ext and A[e] != B[e] and e not in ('.TEX', '.MAT'):
            out.append('%s differs' % e)
    return out


# ------------------------------------------------------------------ selftest / cli
def _find_build():
    try:
        import kl_port_check as K
        w = K.workdir()
    except Exception:
        return None
    for rel, slot in (('build/club_1017/DM05A/club', 'F01'), ('build/vault_door3z_1017/DM03A', 'F07')):
        p = os.path.join(w, *rel.split('/'))
        if os.path.isfile(os.path.join(p, slot + '_Main.zip')):
            return p, slot
    return None


def selftest(log=print):
    """Build 3 civilians on a temp copy of a finished build, check them, and break one thing to see check() fail."""
    hit = _find_build()
    if not hit:
        log('selftest: no finished build found: SKIPPED')
        return True
    src, slot = hit
    tmp = tempfile.mkdtemp(prefix='civs_')
    try:
        B = F.Built(src, slot)
        civs = plan_places(B, 3, seed=7)
        assert len(civs) == 3 and all(c['flee'] for c in civs), civs
        out = os.path.join(tmp, 'out')
        rep = add(src, out, civs, slot=slot, log=lambda *_: None)
        fails, _n = check(out, slot, log=lambda *_: None)
        assert not fails, fails
        assert not diff(src, out, slot, log=lambda *_: None), 'diff'
        assert rep['entities_added'] == 8 * 3, rep['entities_added']
        # a civs.json that names another group than the script does must FAIL
        bad = os.path.join(tmp, 'bad')
        shutil.copytree(out, bad)
        cj = os.path.join(bad, 'civs.json')
        j = json.load(open(cj))
        j['civilians'][0]['actor'] = 'Nobody'
        json.dump(j, open(cj, 'w'))
        fails, _n = check(bad, slot, log=lambda *_: None)
        assert fails, 'check() passed a folder whose script names another group'
        log('selftest: PASS (3 civilians, %d entities, members changed %s)' % (rep['entities_added'], rep['members_changed']))
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _opt(a, flag, n=1, conv=float, default=None):
    if flag not in a:
        return default
    i = a.index(flag)
    v = [conv(x) for x in a[i + 1:i + 1 + n]]
    del a[i:i + 1 + n]
    return v[0] if n == 1 else tuple(v)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 2
    cmd = a.pop(0)
    if cmd == 'selftest':
        return 0 if selftest() else 1
    centre = _opt(a, '--centre', 3)
    radius = _opt(a, '--radius', default=None)
    seed = _opt(a, '--seed', conv=int, default=1)
    alert = _opt(a, '--alert', default=1200.0)
    model = _opt(a, '--model', conv=str, default='auto')
    tree = '--no-tree' not in a
    a = [x for x in a if x != '--no-tree']
    play_part = '--play-part' in a                       # new flags; none given = the old behaviour, byte for byte
    play_radius = _opt(a, '--play-radius', default=PLAY_RADIUS)
    play_band = _opt(a, '--play-band', default=PLAY_BAND)
    cap = '--cap' in a
    max_actors = _opt(a, '--max-actors', conv=int, default=CAP_ACTORS)
    max_squads = _opt(a, '--max-squads', conv=int, default=CAP_SQUADS)
    play_chk = '--play' in a
    bounds = _opt(a, '--bounds-margin', default=BOUND_MARGIN) if '--avoid-bounds' in a else None
    start_clear = None
    if '--start-clear' in a:                            # optional margin: a number right after the flag
        i = a.index('--start-clear')
        start_clear = 150.0
        if i + 1 < len(a) and re.fullmatch(r'-?\d+(\.\d+)?', a[i + 1]):
            start_clear = float(a[i + 1]); del a[i + 1]
        del a[i]
    a = [x for x in a if x not in ('--play-part', '--cap', '--play', '--avoid-bounds')]
    if model.isdigit():
        model = int(model)
    if cmd == 'census':
        B = F.Built(a[0], a[1] if len(a) > 1 else 'F01')
        c = census(B)
        print(json.dumps({k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in c.items()}, indent=1))
        return 0
    if cmd == 'plan':
        B = F.Built(a[0], a[1])
        area = play_area(B, F.Nav(B.scene.nav), play_band) if play_part else None
        for c in plan_places(B, int(a[2]), centre, play_radius if play_part and radius is None else radius, seed, play=area, bounds=bounds, start_clear=start_clear, alert=alert):
            print(c)
        return 0
    if cmd == 'build':
        src, slot, out, n = a[0], a[1], a[2], int(a[3])
        B = F.Built(src, slot)
        if cap:
            c = census(B)
            m = cap_count(c, n, max_actors, max_squads)
            print('cap (GUESS: %d actors, %d squads): the build has %d actors / %d squads; %d of %d civilians fit' % (
                max_actors, max_squads, c['actors'], c['squads'], m, n))
            if m == 0:
                print('NOTHING WRITTEN: the build is at or over the cap without any civilian')
                return 3
            n = m
        play = None
        if play_part:
            nav = F.Nav(B.scene.nav)
            area = play_area(B, nav, play_band)
            play = dict(part=area['part'], centre=[round(v, 1) for v in (centre or area['centre'])], radius=play_radius if radius is None else radius,
                        band=play_band, y0=round(area['y0'], 1), source=area['source'])
            print('play area: part %s from %s, centre %s, radius %s, band %s' % (play['part'], play['source'], play['centre'], play['radius'], play_band))
            civs = plan_places(B, n, centre, play['radius'], seed, play=area, bounds=bounds, start_clear=start_clear, alert=alert)
        else:
            civs = plan_places(B, n, centre, radius, seed, bounds=bounds, start_clear=start_clear, alert=alert)
        if len(civs) < n:
            print('NOTE: %d of %d places found' % (len(civs), n))
        add(src, out, civs, slot, model, alert, tree, max_prm_growth=(1 << 21) if model == HOST else 0, play=play)
        fails, _ = check(out, slot, play=play_chk)
        return 1 if fails else 0
    if cmd == 'check':
        fails, _ = check(a[0], a[1] if len(a) > 1 else 'F01', play=play_chk)
        return 1 if fails else 0
    if cmd == 'diff':
        bad = diff(a[0], a[1], a[2] if len(a) > 2 else 'F01')
        for x in bad:
            print('FAIL', x)
        return 1 if bad else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
