#!/usr/bin/env python3
"""
A dead AI heister comes back as a fed: one PARKED police soldier per AI heister on a FINISHED bots build
(kl_fa_bots), released by that heister's own squad when it has no living man left. Owner, 2026-10-10: 'i want to
make it so you can come back as a fed or the ai heisters can come back as feds too'.
Research: re/fed_respawn.md 5 (read in kl2.exe); spec, the hook's part and the live checks: re/fed.md.
OFFLINE: nothing here installs anything. NOTHING OF THIS HAS RUN IN THE GAME.

    python kl_fa_fed.py build <bots build folder> <out folder> [options]   the feds into a COPY of the build
    python kl_fa_fed.py check <folder>                                     every check on a finished folder; exit 1 on a FAIL
    python kl_fa_fed.py plan  <bots build folder> [options]                only the plan: places, the body, the hunt box
    python kl_fa_fed.py diff  <bots build folder> <out folder>             what the step changed; exit 1 if anything
                                                                           but the feds and seven list entries differs
    options
      --template PATH     the actor GROUP to copy the fed from (scene path without ROOT\\, e.g.
                          'AIEnemies!PoliceSwats\\PoliceSwats_01'); default: the build's own police (see BODY)
      --hunt-box auto|map|mesh   the hunt rout's search box: 'map' = the place and size of the largest search box a
                          hunt rout of this map already has, 'mesh' = the bounds of the START row's mesh part (GUESS:
                          what the box means to the rout was not read - 'where to look' by its name), 'auto' (default)
                          = the map's own when the feds' places, the START row and the boarding place are inside it,
                          else the mesh's
      --body auto|map|player   'map' = a copy of one of the map's own police actors (BODY below); 'player' = the
                          police PLAYER's model (the body the human comes back in) on the heisters' own actor form
                          (player_body(): the way stock dresses its AI heisters in the heroes' models; an ASSUMPTION
                          for this model); 'auto' (default) = 'map' when the map has an actor named police / swat /
                          fbi ..., else 'player' (M06 has gangs and no police)
      --no-tree           do not list the new groups in the scene root's group tree (then .oct keeps its layout and
                          the .prm is not touched at all) - for an A / B run if a load fault points there

WHAT IS BUILT (per AI heister squad `Gameplay!merc_bot_squad!Squad#0N`, N = 2..8; five entities each)
  Gameplay!Feds!Fed#0N              ZGROUP + ZSquadScript: a copy of the heister's own squad group with
                                    field 0 = eUnleashed, field 1 = eHeistOnly (Arcade only), field 3 = 0 (the squad
                                    is NOT in the world at the load; stock: 5..18 squads a level are parked so and come
                                    in when one of their routs is named - seen live on Retomoto), lists 4..18 empty
    10_Hunt                         ZGROUP + HuntBehaviourRout {0: its SearchBox, 1: 1, 2: [], 3: 1, 4: 0}: the form
      SearchBox                     of stock F03 `Gameplay!40_SWAT_Reinforcement_0n\\HuntBehaviour`, which stock names
                                    from a squad's field 8 exactly as here (all 5 stock hunt routs have these values)
    Fed_0N \\ Ground                 the BODY: a whole copy of one of the build's own police actors (group + ZFFActor +
                                    ZSoldier): its model, animation set, weapon, soldier row, voice sets and .SND
                                    offsets as they are - a model, a skeleton and a weapon this level already runs.
                                    Only the place and the facing are new. Team Enemy: he shoots the crew and the
                                    criminal player as every police soldier does, and leaves a police PLAYER alone
                                    (kl2 0x8824e7).
  Squad#0N  @ZSquadScript  field 8 += ROOT\\Gameplay!Feds!Fed#0N\\10_Hunt
                                    field 8 is the list ZSquadScript's update (0x47e440) sends through 0x87ebf0 when
                                    the squad's count of living men reaches 0, once. The heister squads' lists 4..18
                                    are empty in stock and in the bots builds.
  BODY (auto): among the build's Enemy actors with a ZSoldier the ones whose squad or group is named police / swat /
  fbi / cop / agent / fed score highest, then soldier style eArmy, then a rifle; the feds take that squad's men in
  turn (so their weapons vary as the squad's do). No model, texture, animation or sound is added: the four large
  members (.prm .ANM .fxc and the .WAV beside the archive) keep their size (checked).
  PLACE: the map's FRAGILE_ALLIANCE_AFTER_DEATH points are where a police PLAYER appears. An AI soldier needs the
  navigation mesh, and on the part the crew is on. So: where such points stand over the START row's mesh part
  (M03) the feds stand round them, 110..600 away and 110 apart (never ON a point: a police player may appear
  there in the same second); where they do not (M01: a roof of its own mesh part; M02: 20 m outside the mesh;
  M06: 13 m above it - places a player drops or walks in from) the feds stand on the START row's part at the
  place nearest to the points in the plan, and the plan says how far that is. GUESS: the distances.

THE CATCH, AND THE HOOK (re/fed_respawn.md 5.3 / 5.4, klhook/klfed.c section 3)
  'Living' for a squad (0x71adc0) also ends when a heister BOARDS the escape vehicle (actor+0x8f0 = 1, 0x684253):
  with this level data alone a heister who gets away releases his fed too. klfed.c with [Fed] Bots=1 makes it
  deaths only by two data writes per heister; Bots=2 mutes the list (no AI fed on this very build).
  Between two rounds on the same loaded level: not known (the list's latch has no writer that clears it).

WHAT IS WRITTEN: .prp (the subtrees appended, seven list entries), .gms + .buf (kl_scene), .oct / .rmi / .rmc
  (every SLOT id renumbered; the squad and hunt groups listed in the root's group tree as stock F03 lists its
  reinforcement squads: the box of a hunt group is its search box, measured on stock and on this build), and
  the .prm's 4-byte .oct record offsets in place (same size) - all exactly as kl_fa_bots.apply does it.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, math, os, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene
import kl_fa_bots as KB
import kl_octree as O
import kl_prpjoin as J
from kl_prp import Prp, units

R_ = 'ROOT\\'
FEDS = 'Gameplay!Feds!'
FED = FEDS + 'Fed#0%d'
HUNT = '10_Hunt'
MAN = 'Fed_0%d'
HUNT_FORM = ('F03', R_ + 'Gameplay!40_SWAT_Reinforcement_01\\HuntBehaviour')      # the stock form (docstring)
NEAR, FAR = 110.0, 600.0        # GUESS: a fed stands this far from an AFTER_DEATH point (stock bots: 80..440 from a START point)
ENTRY = 800.0                   # GUESS: radius round the mesh place nearest to the AFTER_DEATH points, when they are off the mesh
CREW_FAR = 1500.0               # NOTE below this from the START row: the fed would appear among the starting crew
POLICE_WORDS = ('police', 'swat', 'fbi', 'cop', 'agent', 'fed', 'sheriff', 'army')
DEFAULTS = {'template': None, 'body': 'auto', 'hunt_box': 'auto', 'tree': True}


# ------------------------------------------------------------------ the plan
def bot_squads(sc):
    """{N: (squad node, index of its ZSquadScript, field values, actor node)} of the AI heister squads."""
    out = {}
    for N in KB.BOTS:
        hit = sc.resolve(R_ + KB.SQUAD + 'Squad#0%d' % N)
        if len(hit) != 1:
            continue
        k = hit[0]
        ci = [i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'ZSquadScript']
        acts = [j for j in range(k, sc.end[k]) if sc.cls(j) == 'ZFFActor']
        if len(ci) != 1 or not acts:
            continue
        i = ci[0]
        v = [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][i][1][1:-1])]
        out[N] = (k, i, v, acts)
    return out


def fed_nodes(sc):
    return {k for t in sc.tops() if sc.names[t].startswith(FEDS) for k in range(t, sc.end[t])}


def dead_points(B):
    sc = B.sc
    return [(k, B.at(k)) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and
            any(isinstance(x, str) and x == kl_fa.DEAD for x in kl_fa.node_values(sc, k))]


def soldier_row(sc, k):
    for nm, body in sc.nodes[k]['ctrls']:
        if sc.p.key(nm) == 'ZSoldier':
            return [kl_fa.value(sc, u) for u in units(body[1:-1])]
    return None


def bodies(B, want=None):
    """The actor groups a fed can be a copy of -> [(score, group node, actor node)], best first. want: a scene path."""
    sc, out = B.sc, []
    mine = fed_nodes(sc)
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor' or k in mine:
            continue
        g, v, row = sc.parent[k], B.values(k), soldier_row(sc, k)
        if v['ZFFActor[0]'] != 'Enemy' or row is None or sc.cls(g) != 'ZGROUP' or sc.end[g] - g != 2 or not sc.resolve(v['ZFFActor[1]']):
            continue                                    # a group with one actor and nothing else, armed, a soldier
        if want is not None:
            if sc.path[g][5:].lower() == want.lower():
                out.append((100, g, k))
            continue
        words = (sc.names[sc.top[k]] + ' ' + sc.names[g]).lower()
        score = 4 * any(w in words for w in POLICE_WORDS) + 2 * (row[0] == 'eArmy') + ('rifle' in v['ZFFActor[1]'].lower())
        out.append((score, g, k))
    out.sort(key=lambda x: (-x[0], x[1]))
    return out


SWAT_FORM = ('F07', R_ + 'Gameplay!020_Loot!020_FinancialAlley_RightGround\\Police_SWAT_01__\\Ground')    # stock's commonest police row
SWAT_ROW = (0, 4, 5, 6, 7, 8, 13, 14, 15, 16, 17)      # the ZSoldier fields that make a soldier a policeman (re/map_ai.md 1)


def player_body(B, squads):
    """For a map without police of its own: the police PLAYER's model on the build's AI-heister actor form.
    Stock dresses its AI heisters exactly so in the heroes' models: actor model = the player object's model, the
    actor group's aux = the player group's (measured on M02 M06 F07: the group's aux follows the model), animation
    set = the player's + '_NPC'. Here the player is the police one (type MULTIPLAYER_POLICEMAN; all eight share one
    model). The soldier row and the weapon are those of stock F07's SWAT; team Enemy. -> dict for plan()."""
    sc = B.sc
    cops = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFPlayer' and 'eZFFP_TYPE_MULTIPLAYER_POLICEMAN' in [x for x in kl_fa.node_values(sc, k) if isinstance(x, str)]]
    if not cops:
        raise ValueError('no police player object (ZFFPlayer of type MULTIPLAYER_POLICEMAN)')
    c = cops[0]
    cv = B.values(c)
    anim = cv['ZLNKOBJ[2]'] + '_NPC'
    forms = [acts[0] for _k, _i, _v, acts in squads.values() if B.values(acts[0])['ZLNKOBJ[2]'].lower() == anim.lower()]
    if not forms:
        raise ValueError('no AI heister uses the animation set %s' % anim)
    stock, _e = KB.Maker.level(SWAT_FORM[0])
    s = stock.resolve(SWAT_FORM[1])
    if len(s) != 1:
        raise ValueError('stock %s has no %s' % SWAT_FORM)
    sv = dict(zip(J.labels('dd', stock.cls(s[0])), kl_fa.node_values(stock, s[0])))
    row = soldier_row(stock, s[0])
    weapon = sv['ZFFActor[1]'] if sc.resolve(sv['ZFFActor[1]']) else B.values(forms[0])['ZFFActor[1]']
    return collections.OrderedDict(model=B.ents[c - 1].model, aux=B.ents[sc.parent[c] - 1].aux, anim=anim, player=sc.path[c], form=sc.parent[forms[0]],
                                   weapon=weapon, kill=sv['ZFFActor[16]'], row=collections.OrderedDict((i, row[i]) for i in SWAT_ROW))


def hunt_boxes(B):
    """[(volume, world centre, size, path)] of the search boxes the map's own hunt routs name (not the feds')."""
    sc, out, mine = B.sc, [], fed_nodes(B.sc)
    for k, _i, v in kl_fa.controllers(sc, 'HuntBehaviourRout'):
        if k in mine or not isinstance(v[0], str):
            continue
        for j in sc.resolve(v[0]):
            if sc.cls(j) == 'ZBoxPrimitive':
                s = B.box(j)
                out.append((s[0] * s[1] * s[2], tuple(B.at(j)), tuple(s), sc.path[j][5:]))
    return sorted(out, reverse=True)


def plan(B, opt=None, log=print):
    opt = dict(DEFAULTS, **(opt or {}))
    sc, nav = B.sc, KB.Nav(B.scene.nav)
    if fed_nodes(sc):
        raise ValueError('the build already has %s squads' % FEDS)
    squads = bot_squads(sc)
    if not squads:
        raise ValueError('no AI heister squad (%sSquad#0N with a ZFFActor): run kl_fa_bots first' % KB.SQUAD)
    S = KB.stations(B, nav)
    home, mid = S['home'], S['start_mid']
    dead = dead_points(B)
    if not dead:
        raise ValueError('no %s spawn point' % kl_fa.DEAD)
    on = []
    for k, p in dead:
        hit = nav.at(p[0], p[1], p[2], lo=p[1] - 260.0, hi=p[1] + 40.0, part=home)
        if hit:
            on.append((p[0], hit[1], p[2]))
    centre = tuple(sum(p[i] for _k, p in dead) / len(dead) for i in range(3))
    log('AFTER_DEATH points: %d, centre (%d, %d, %d); %d stand over the START row\'s mesh part (%d of %d polygons)'
        % (len(dead), *centre, len(on), nav.part_size[home], len(nav.pv)))
    # ---- the places
    need = len(squads)
    if on:
        how = 'round the AFTER_DEATH points that stand over the mesh'
        anchor = tuple(sum(p[i] for p in on) / len(on) for i in range(3))
        cands = {}
        for p in on:
            for c in nav.around(p, FAR, home):
                cands[(round(c[0]), round(c[2]), c[3])] = c
        cands = [c for c in cands.values() if all(math.hypot(c[0] - p[0], c[2] - p[2]) >= NEAR for _k, p in dead)]
        off = 0.0
    else:
        # the place of the START row's part nearest to the points in the plan (then in height)
        i = min((i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == home),
                key=lambda i: (math.hypot(nav.mid[i][0] - centre[0], nav.mid[i][2] - centre[2]), abs(nav.mid[i][1] - centre[1])))
        anchor = tuple(nav.mid[i])
        off = math.hypot(anchor[0] - centre[0], anchor[2] - centre[2])
        how = 'on the START row\'s mesh part at the place nearest to the AFTER_DEATH points: %d away in the plan, %d below' % (off, centre[1] - anchor[1])
        cands = nav.around(anchor, ENTRY, home)
    spots = nav.spots(cands, need, KB.SEP, ref=anchor + (0,))
    if len(spots) < need:
        raise ValueError('only %d places with %d between them %s (need %d)' % (len(spots), KB.SEP, how, need))
    log('places: %s' % how)
    # ---- the body
    tm = bodies(B, opt['template'])
    pb = None
    if opt['body'] == 'player' or (opt['body'] == 'auto' and not opt['template'] and (not tm or tm[0][0] < 4)):
        pb = player_body(B, squads)
        log('body: %s - the POLICE PLAYER\'s model %d on the heisters\' own actor form (%s, animation set %s, weapon %s, '
            'soldier row %s): the way stock dresses the AI heisters in the heroes\' models. ASSUMPTION: it holds for this model too; never seen in the game'
            % ('--body player' if opt['body'] == 'player' else 'the map has no actor named police (best: %s)' % ('%s, score %d' % (sc.names[tm[0][1]], tm[0][0]) if tm else 'none'),
               pb['model'], sc.names[pb['form']], pb['anim'], pb['weapon'].rsplit('\\', 1)[-1], dict(pb['row'])))
        best = [(0, pb['form'], pb['form'] + 1)]
    else:
        if not tm:
            raise ValueError('no Enemy actor group to copy' + (' at %s' % opt['template'] if opt['template'] else ' (a ZGROUP holding one armed ZFFActor with a ZSoldier)'))
        best = [t for t in tm if t[0] == tm[0][0] and sc.top[t[1]] == sc.top[tm[0][1]]]
        log('body: %d actor group(s) of %s (score %d of 7: named police 4, soldier style eArmy 2, a rifle 1)' % (len(best), sc.names[sc.top[best[0][1]]], best[0][0]))
    # ---- the hunt box
    hb = hunt_boxes(B)
    xs = [v for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == home for v in nav.pv[i]]
    lo, hi = [min(v[a] for v in xs) for a in range(3)], [max(v[a] for v in xs) for a in range(3)]
    must = [(s[0], s[1], s[2]) for s in spots] + [tuple(mid)] + ([tuple(B.at(S['action']))] if S['action'] else [])
    holds = lambda h: all(abs(p[a] - h[1][a]) <= h[2][a] / 2 for p in must for a in range(3))
    if hb and (opt['hunt_box'] == 'map' or (opt['hunt_box'] == 'auto' and holds(hb[0]))):
        box = {'centre': list(hb[0][1]), 'size': list(hb[0][2]), 'from': hb[0][3]}
    else:
        if hb and opt['hunt_box'] == 'auto':
            log("hunt box: the map's own largest (%s, centre (%d, %d, %d), size (%d, %d, %d)) does not hold the feds' places, the START row and the "
                "boarding place: not taken" % (hb[0][3], *hb[0][1], *hb[0][2]))
        # GUESS: the whole part the crew walks on, 200 more each way and 300 up (a box's three values are its full size:
        # measured, the root's group tree lists a hunt group with exactly its search box, on stock F03 and on M02)
        box = {'centre': [(lo[a] + hi[a]) / 2 for a in range(3)], 'size': [hi[a] - lo[a] + (600.0 if a == 1 else 400.0) for a in range(3)],
               'from': 'the bounds of the START row\'s mesh part'}
        box['centre'][1] += 150.0
    log('hunt box: %s, centre (%d, %d, %d), size (%d, %d, %d)' % (box['from'], *box['centre'], *box['size']))
    feds = collections.OrderedDict()
    for n, N in enumerate(sorted(squads)):
        k, _i, v, acts = squads[N]
        x, y, z, poly = spots[n]
        g, a = best[n % len(best)][1:]
        av = B.values(a)
        d = math.hypot(mid[0] - x, mid[2] - z) or 1.0
        way = nav.path((x, y, z, poly), (mid[0], nav.mid[nav.nearest(mid, home)][1], mid[2], nav.nearest(mid, home)))
        feds[N] = collections.OrderedDict(
            squad=sc.path[k], heister=sc.path[acts[0]], field8=list(v[8]), place=[x, y, z], face=[(mid[0] - x) / d, (mid[2] - z) / d],
            clearance=round(nav.clearance(x, y, z)), to_START_row=round(d), path_to_START_row=round(way[1]) if way else None,
            to_nearest_AFTER_DEATH=round(min(math.hypot(x - p[0], z - p[2]) for _k, p in dead)),
            template=sc.path[g], model=B.ents[a - 1].model, weapon=av['ZFFActor[1]'].rsplit('\\', 1)[-1], anim=av['ZLNKOBJ[2]'], row=soldier_row(sc, a)[:8])
        if pb:
            feds[N].update(player=pb, model=pb['model'], weapon=pb['weapon'].rsplit('\\', 1)[-1], anim=pb['anim'], row=[pb['row'].get(i, r) for i, r in enumerate(soldier_row(sc, a)[:8])])
        log('  Fed#0%d for %s: at (%d, %d, %d), clearance %d, %d from an AFTER_DEATH point, %s of path to the START row; body %s (model %d, %s, %s, health %d)'
            % (N, sc.names[k], x, y, z, feds[N]['clearance'], feds[N]['to_nearest_AFTER_DEATH'], feds[N]['path_to_START_row'], sc.names[g], feds[N]['model'],
               feds[N]['weapon'], feds[N]['row'][0], feds[N]['row'][7]))
    return collections.OrderedDict(options=opt, how=how, off_mesh_distance=round(off), dead_points=len(dead), dead_on_mesh=len(on), home=home,
                                   box=box, feds=feds, systems=B.result.get('S'))


# ------------------------------------------------------------------ the nodes
def clone_built(M, B, k, name=None):
    """A node of the build itself as a kl_fa_bots.Node (Maker.clone does the same from a stock level)."""
    sc, n = B.sc, B.sc.nodes[k]
    node = KB.Node(name or sc.names[k], sc.tids[k], M.adopt(n['props'], sc.p.keys),
                   [(M.adopt([nm], sc.p.keys)[0], M.adopt(body, sc.p.keys)) for nm, body in n['ctrls']], B.ents[k - 1])
    node.model = B.ents[k - 1].model
    return node


def make(B, P):
    sc, M, tops = B.sc, KB.Maker(), []
    for N, f in P['feds'].items():
        N = int(N)
        fed = lambda tail='': R_ + FED % N + tail
        top = clone_built(M, B, sc.resolve(f['squad'])[0], FED % N)
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        fields = {i: [] for i in range(4, 19)}
        fields.update({0: 'eUnleashed', 1: 'eHeistOnly', 3: 0})
        M.set(top, 'ZSquadScript', fields)
        hunt = top.add(M.clone(HUNT_FORM[0], HUNT_FORM[1], HUNT))
        M.place(hunt, (0.0, 0.0, 0.0))
        box = hunt.add(M.clone(HUNT_FORM[0], HUNT_FORM[1] + '\\SearchBox', 'SearchBox'))
        M.place(box, P['box']['centre'])
        M.set(box, None, {'ZBoxPrimitive[%d]' % a: float(P['box']['size'][a]) for a in range(3)})
        M.set(hunt, 'HuntBehaviourRout', {0: fed('\\%s\\SearchBox' % HUNT), 2: []})
        g = sc.resolve(f['template'])[0]
        grp = top.add(clone_built(M, B, g, MAN % N))
        M.place(grp, f['place'], KB.rot9(*f['face']))
        act = grp.add(clone_built(M, B, g + 1))            # the actor as it is: at its group's origin
        pb = f.get('player')
        if pb:                                             # the heisters' actor form in the police player's model (plan: player_body)
            grp.aux = pb['aux']
            act.model = pb['model']
            M.set(act, None, {'ZGEOM[4]': pb['model'], 'ZLNKOBJ[2]': pb['anim'], 'ZFFActor[0]': 'Enemy', 'ZFFActor[1]': pb['weapon'], 'ZFFActor[16]': pb['kill']})
            M.set(act, 'ZSoldier', {int(i): v for i, v in pb['row'].items()})
        tops.append(top)
    return M, tops


# ------------------------------------------------------------------ writing (as kl_fa_bots.apply)
def apply(B, P, dst, log=print):
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    sc = B.sc
    before = KB.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    g0, b0 = B.scene.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(B.scene, octx, rmi, rmc)

    M, tops = make(B, P)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'feds')
    # ---- each heister squad's 'no living man left' list names its fed's hunt rout
    for N, f in P['feds'].items():
        k = Jn.resolve(f['squad'])[0]
        ci = next(i for i, (nm, _b) in enumerate(Jn.nodes[k]['ctrls']) if Jn.p.key(nm) == 'ZSquadScript')
        want = R_ + FED % int(N) + '\\' + HUNT
        def fn(us, want=want):
            have = [Jn.p.key(t) for t in us[8][1:]]
            us[8] = kl_fa._refs(Jn, have + [want])
        kl_fa.edit(Jn, k, ci, fn)
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    # ---- .gms / .buf
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
        for c in n.kids:
            ent(c, e)
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
    # ---- .oct / .rmi / .rmc: every slot id moved
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    # the squad and hunt groups in the root's group tree, as stock lists a parked police squad (F03's reinforcements):
    # the hunt group with the box of its search box, the squad with that and its man
    c, s = P['box']['centre'], P['box']['size']
    blo, bhi = tuple(c[a] - s[a] / 2 for a in range(3)), tuple(c[a] + s[a] / 2 for a in range(3))
    items = []
    for t in tops:
        man = next(k.pos for k in t.kids if k.name.startswith('Fed_'))
        items.append((slot1[made[id(t)]] + 2, tuple(min(blo[a], man[a] - 10.0) for a in range(3)), tuple(max(bhi[a], man[a] + (190.0 if a == 1 else 10.0)) for a in range(3))))
        items.append((slot1[made[id(t.kids[0])]] + 2, blo, bhi))
    root3 = octn.rooms[0][3]
    listed, repointed, new_prm = 0, 0, None
    if root3 is not None and items and P['options']['tree']:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        listed = len(items)
        octn.rooms[0][3].check()
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            prm = bytearray(B['.prm'])
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
            new_prm = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))

    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    import kl_graft
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'fed.')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = KB.sizes(dst)
    if after != before:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    rep = collections.OrderedDict(
        source=B.folder, out=dst, members_changed=changed, entities_added=len(order), entities=len(ents),
        classes_added=dict(collections.Counter(J.schema('dd').geoms.get(n.tid) for n in order)),
        controllers_added=dict(collections.Counter(M.p.key(nm) for n in order for nm, _b in n.ctrls)),
        ref_ids='%d..%d' % (nxt - len(order), nxt - 1), slot_ids_moved=moved, groups_listed_in_root_tree_3=listed,
        prm_model_roots_repointed=repointed, slot_id_faults_before=pre, slot_id_faults_after=post, big_before=before, big_after=after)
    sj = os.path.join(dst, 'steps.json')                # kl_maps.audit compares the folder with what was measured
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['fed'] = changed
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_fed: %d parked police squads (%d entities) from %s; options %s\n' % (len(tops), len(order), B.folder, json.dumps(P['options'], sort_keys=True)))
    log('written %s: %d entities added (%s); members changed: %s; %d slot ids renumbered, %d groups listed in the root\'s group tree, '
        '%d model roots of the .prm re-pointed at their moved .oct records'
        % (zp, len(order), ', '.join('%s %d' % kv for kv in rep['classes_added'].items()), ' '.join(changed), moved, listed, repointed))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    return rep


# ------------------------------------------------------------------ the check
def check(folder, log=print, slot=KB.SLOT):
    """Every check on a finished folder -> (list of (severity, text), facts). FAIL must be none before an install."""
    B = KB.Built(folder, slot)
    sc, nav, out = B.sc, KB.Nav(B.scene.nav), []
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    name = lambda k: sc.path[k][5:]
    S = KB.stations(B, nav)
    home, mid = S['home'], S['start_mid']
    mine = fed_nodes(sc)
    squads = bot_squads(sc)
    dead = dead_points(B)
    facts = collections.OrderedDict(feds=0, fed_nodes=len(mine), heister_squads=len(squads))
    tops = [t for t in sc.tops() if sc.names[t].startswith(FEDS)]
    if not tops:
        fail('no %s squad' % FEDS)
    cols = None
    try:
        import kl_anm
        cols = {c.name.lower() for c in kl_anm.Anm(B['.ANM'], 'dd').cols}
    except Exception as x:
        note('the .ANM could not be read for the animation-set test: %s' % x)
    others = {}                                         # model -> an actor of the map (not a fed) that wears it, else a player
    for cls in ('ZFFActor', 'ZFFPlayer'):
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == cls and k not in mine:
                others.setdefault(B.ents[k - 1].model, k)
    facts['bodies'] = collections.Counter()
    scripts = {k: v for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript')}
    hunts = {k: v for k, _i, v in kl_fa.controllers(sc, 'HuntBehaviourRout')}
    feet, routs = [], {}
    for t in tops:
        nm = sc.names[t]
        N = int(nm[len(FEDS) + 5:len(FEDS) + 6]) if nm[len(FEDS):len(FEDS) + 5] == 'Fed#0' and nm[len(FEDS) + 5:len(FEDS) + 6].isdigit() else None
        v = scripts.get(t)
        if N is None or v is None:
            fail('%s: not a Fed#0N group with a ZSquadScript' % nm); continue
        if v[0] != 'eUnleashed' or v[1] != 'eHeistOnly' or v[3] != 0:
            fail('%s: ZSquadScript fields 0 / 1 / 3 = %s / %s / %s (want eUnleashed / eHeistOnly / 0 = not in the world at the load)' % (nm, v[0], v[1], v[3]))
        if any(v[i] for i in range(4, 19)):
            fail('%s: its own event lists are not empty' % nm)
        acts = [k for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        hs = [k for k in range(t, sc.end[t]) if k in hunts]
        if len(acts) != 1 or len(hs) != 1:
            fail('%s: %d actors, %d hunt routs (want 1 and 1)' % (nm, len(acts), len(hs))); continue
        a, h = acts[0], hs[0]
        routs[N] = sc.path[h]
        facts['feds'] += 1
        # the rout
        hv = hunts[h]
        box = sc.resolve(hv[0]) if isinstance(hv[0], str) else []
        if len(box) != 1 or sc.cls(box[0]) != 'ZBoxPrimitive' or sc.parent[box[0]] != h:
            fail('%s: field 0 of its HuntBehaviourRout does not name its own child box' % name(h))
        elif not B.in_box(box[0], mid, 0.5):
            note('%s: the START row is not inside the search box' % name(h))
        if hv[1:] != [1, [], 1, 0]:
            note('%s: HuntBehaviourRout fields 1..4 = %s (all five stock hunt routs: 1, [], 1, 0)' % (name(h), hv[1:]))
        # the body
        av, e = B.values(a), B.ents[a - 1]
        if av['ZFFActor[0]'] != 'Enemy':
            fail('%s: team %s (want Enemy; an Ally would be registered as a crew member, kl2 0x8e5650)' % (name(a), av['ZFFActor[0]']))
        if soldier_row(sc, a) is None:
            fail('%s: no ZSoldier controller' % name(a))
        if e.model != av['ZGEOM[4]'] or e.model not in others:
            fail('%s: model %d (.gms) / %d (.prp) is worn by no other actor of this level' % (name(a), e.model, av['ZGEOM[4]']))
        else:
            w = others[e.model]
            o, npc = B.values(w), sc.cls(w) == 'ZFFPlayer'
            facts['bodies']['model %d as %s' % (e.model, name(sc.parent[w]))] += 1
            for f in ('ZLNKOBJ[1]', 'ZLNKOBJ[2]', 'ZLNKWHANDS[5]'):
                # an actor in a PLAYER's model has that player's animation set + '_NPC' (stock: every AI heister)
                if av[f] != (o[f] + '_NPC' if npc and f == 'ZLNKOBJ[2]' else o[f]):
                    (fail if f == 'ZLNKOBJ[2]' else note)('%s: %s = %s, %s (same model) has %s' % (name(a), f, av[f], name(w), o[f]))
            if B.ents[sc.parent[a] - 1].aux != B.ents[sc.parent[w] - 1].aux:
                note('%s: its group\'s aux is %d, the group of %s (same model) has %d' % (name(a), B.ents[sc.parent[a] - 1].aux, name(w), B.ents[sc.parent[w] - 1].aux))
            if npc:
                note('%s wears the police PLAYER\'s model %d on an actor (ASSUMPTION: as stock\'s AI heisters wear the heroes\'; not in a played build)' % (name(a), e.model))
        if cols is not None and av['ZLNKOBJ[2]'].lower() not in cols:
            fail('%s: animation set %s is not in the .ANM' % (name(a), av['ZLNKOBJ[2]']))
        if not sc.resolve(av['ZFFActor[1]']):
            fail('%s: weapon %s does not resolve' % (name(a), av['ZFFActor[1]']))
        # the place
        p = B.at(a)
        hit = nav.at(p[0], p[1], p[2], dy=15.0)
        if not hit:
            fail('%s at (%d, %d, %d) is not on a walkable polygon (within 15 of the mesh\'s height)' % (name(a), *p)); continue
        if nav.part[hit[0]] != home:
            fail('%s at (%d, %d, %d) is on a mesh part of %d polygons, not the START row\'s: it could not reach the crew' % (name(a), *p, nav.part_size[nav.part[hit[0]]]))
        cl = nav.clearance(p[0], hit[1], p[2])
        if cl < KB.CLEAR_MIN:
            fail('%s at (%d, %d, %d): %d from a mesh edge without a neighbour (least %d)' % (name(a), *p, cl, KB.CLEAR_MIN))
        dd = min(math.hypot(p[0] - q[0], p[2] - q[2]) for _k, q in dead) if dead else -1
        on = [q for _k, q in dead if math.hypot(p[0] - q[0], p[2] - q[2]) < 60 and abs(q[1] - p[1]) < 300]
        if on:
            fail('%s stands ON an AFTER_DEATH point (%d away): a police player appears there' % (name(a), dd))
        if math.hypot(p[0] - mid[0], p[2] - mid[2]) < CREW_FAR:
            note('%s is %d from the START row (under %d): he would appear among the starting crew' % (name(a), math.hypot(p[0] - mid[0], p[2] - mid[2]), CREW_FAR))
        feet.append((N, p, round(cl), round(dd)))
    if feet:
        apart = min([math.hypot(a[1][0] - b[1][0], a[1][2] - b[1][2]) for i, a in enumerate(feet) for b in feet[i + 1:]] or [9e9])
        if apart < 80:
            fail('two feds stand %d apart' % apart)
        facts['places'] = {'apart_at_least': round(apart) if apart < 9e9 else None, 'clearance': [min(f[2] for f in feet), max(f[2] for f in feet)],
                           'to_nearest_AFTER_DEATH_point': [min(f[3] for f in feet), max(f[3] for f in feet)],
                           'to_START_row': [round(min(math.hypot(f[1][0] - mid[0], f[1][2] - mid[2]) for f in feet)), round(max(math.hypot(f[1][0] - mid[0], f[1][2] - mid[2]) for f in feet))]}
    # the links: each heister squad's field 8 names its own fed's hunt rout, and nothing else names a fed
    linked = 0
    for N, (k, _i, v, acts) in sorted(squads.items()):
        want = routs.get(N)
        if len(acts) != 1:
            fail('%s has %d actors: the hook\'s deaths-only switch needs a one-man squad' % (sc.names[k], len(acts)))
        if want is None:
            note('%s has no fed' % sc.names[k]); continue
        if [s.lower() for s in v[8]].count(want.lower()) != 1:
            fail('%s: field 8 (%s) does not name %s once' % (sc.names[k], v[8], want)); continue
        if any(v[i] for i in range(4, 19) if i != 8) or len(v[8]) != 1:
            note('%s: other event list entries besides its fed: %s' % (sc.names[k], {i: v[i] for i in range(4, 19) if v[i]}))
        linked += 1
    for N in routs:
        if N not in squads:
            fail('Fed#0%d has no heister squad Squad#0%d: nothing would ever release it' % (N, N))
    facts['linked'] = linked
    tops_of = {k: v[0] for v in squads.values() for k in [v[0]]}
    for k, holder, field, s, hit in J.references(sc):
        if k in mine and not hit:
            fail('%s %s -> %s does not resolve' % (sc.path[k], field, s))
        elif k not in mine and any(h in mine for h in hit) and k not in tops_of:
            fail('%s %s names %s: a fed must be released by its heister\'s squad only' % (sc.path[k] if k >= 0 else holder, field, s))
    # classes and controllers: nothing the level and stock do not already run
    sys_level = B.result.get('S') or 'F07'
    stock, _e = KB.Maker.level(sys_level if sys_level in KB.SYSTEM_LEVELS else 'F07')
    s_tids = set(stock.tids)
    here_c = {sc.p.key(nm) for k in range(1, len(sc.nodes)) if k not in mine for nm, _b in sc.nodes[k]['ctrls']}
    for t in sorted({sc.tids[k] for k in mine}):
        if t not in s_tids:
            fail('class %s (%#x) of the feds is in no object of stock %s' % (J.schema('dd').geoms.get(t), t, sys_level))
    for cn in sorted({sc.p.key(nm) for k in mine for nm, _b in sc.nodes[k]['ctrls']}):
        if not any(J.schema('dd').controller(cn, sc.cls(k)) for k in mine if any(sc.p.key(nm) == cn for nm, _b in sc.nodes[k]['ctrls'])):
            fail('controller %s is not registered in kl2.exe' % cn)
        elif cn not in here_c:
            users = [L for L in KB.SYSTEM_LEVELS if any(KB.Maker.level(L)[0].p.key(nm) == cn for n in KB.Maker.level(L)[0].nodes for nm, _b in n['ctrls'])]
            (note if users else fail)('controller %s is used by the feds only in this level; stock levels with it: %s' % (cn, ' '.join(users) or 'NONE'))
    for k, what_, why in [m for m in J.misfits(sc) if m[0] in mine or m[0] in tops_of][:5]:
        fail('%s: %s does not fit its class: %s' % (name(k), what_, why))
    # the files
    for x in B.scene.check()[:5]:
        fail('kl_scene.check: ' + x)
    for k in mine:
        e, v = B.ents[k - 1], kl_fa.node_values(sc, k)
        if tuple(struct.unpack('<3f', e.trans[:12])) != tuple(struct.unpack('<3f', struct.pack('<3f', *v[2]))) or e.model != v[4]:
            fail('%s: .gms record and .prp disagree on place or model' % name(k)); break
    facts['bodies'] = dict(facts.get('bodies') or {})
    facts['big'] = KB.sizes(folder, slot)
    fj = os.path.join(B.folder, 'fed.json')
    if os.path.isfile(fj):
        was = json.load(open(fj)).get('big_before')
        if was and dict(was) != dict(facts['big']):
            fail('a large block changed its size since the build the feds were added to: %s -> %s' % (was, dict(facts['big'])))
    out.sort(key=lambda x: x[0] != 'FAIL')
    for sev, text in out:
        log('%-4s %s' % (sev, text))
    for N, p, cl, dd in sorted(feet):
        log('  Fed#0%d at (%d, %d, %d): clearance %d, %d from an AFTER_DEATH point, %d from the START row; released by %s' % (N, *p, cl, dd, math.hypot(p[0] - mid[0], p[2] - mid[2]),
            sc.names[squads[N][0]] if N in squads else 'NOTHING'))
    log('RESULT: %s (%d FAIL, %d NOTE); %d feds, %d linked to their heister squad, %d fed nodes; large blocks %s' % (
        'PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL', sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out),
        facts['feds'], linked, len(mine), ', '.join('%s %d' % kv for kv in facts['big'].items())))
    return out, facts


def diff(src, dst, log=print):
    """What differs between the bots build and the result -> list of UNEXPECTED differences (must be empty).
    kl_fa_bots.diff proves the files (entities, slot ids by entity, room trees, .prm cells, every other member and
    the files beside the archive byte for byte); here: the heister squads differ in ONE list entry each."""
    A, B = KB.Built(src), KB.Built(dst)
    sa, sb = bot_squads(A.sc), bot_squads(B.sc)
    bad = list(KB.diff(src, dst, log, also={A.sc.names[v[0]] for v in sa.values()}))
    n = 0
    for N, (k, i, v, _a) in sa.items():
        if N not in sb:
            bad.append('Squad#0%d is gone' % N); continue
        k2, i2, v2, _a2 = sb[N]
        add = [s for s in v2[8] if s not in v[8]]
        if v2[:8] != v[:8] or v2[9:] != v[9:] or v2[8][:len(v[8])] != v[8] or len(add) > 1 or (add and add[0] != R_ + FED % N + '\\' + HUNT):
            bad.append('Squad#0%d: its ZSquadScript differs in more than one new entry of field 8' % N)
        fa, fb = J.fingerprints(A.sc), J.fingerprints(B.sc)
        ka = [c for c in range(k + 1, A.sc.end[k]) if A.sc.parent[c] == k]
        kb = [c for c in range(k2 + 1, B.sc.end[k2]) if B.sc.parent[c] == k2]
        if [fa[c] for c in ka] != [fb[c] for c in kb] or J.text(A.sc, A.sc.nodes[k]['props']) != J.text(B.sc, B.sc.nodes[k2]['props']):
            bad.append('Squad#0%d: its own properties or its children differ' % N)
        n += len(add)
    new = [B.sc.names[t] for t in B.sc.tops()[len(A.sc.tops()):]]
    if any(not x.startswith(FEDS) for x in new):
        bad.append('new top-level subtrees that are no feds: %s' % [x for x in new if not x.startswith(FEDS)][:4])
    log('.prp: %d heister squads, each differs in one new entry of ZSquadScript field 8 (%d entries); %d new subtrees, all %s...' % (len(sa), n, len(new), FEDS))
    log('FED RESULT: %s' % ('only the feds and their list entries were added' if not bad else '%d unexpected differences' % len(bad)))
    return bad


def build(src, dst, opt=None, log=print):
    """plan + apply + check + diff on the written folder; fed.txt / fed.json in it -> (findings, report)."""
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    B = KB.Built(src)
    say('kl_fa_fed build %s -> %s' % (src, dst))
    P = plan(B, opt, say)
    rep = apply(B, P, dst, say)
    out, facts = check(dst, say)
    bad = diff(src, dst, say)
    out += [('FAIL', 'diff: ' + x) for x in bad]
    rep.update(plan=P, check=[list(x) for x in out], facts=facts, diff=bad)
    with open(os.path.join(dst, 'fed.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'fed.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, rep


def options(a):
    opt = {}
    def take(name):
        if name in a:
            i = a.index(name); v = a[i + 1]; del a[i:i + 2]
            return v
        return None
    v = take('--template')
    if v is not None:
        opt['template'] = v[5:] if v.upper().startswith('ROOT\\') else v
    v = take('--body')
    if v is not None:
        if v not in ('auto', 'map', 'player'):
            sys.exit('--body auto|map|player')
        opt['body'] = v
    v = take('--hunt-box')
    if v is not None:
        if v not in ('auto', 'map', 'mesh'):
            sys.exit('--hunt-box auto|map|mesh')
        opt['hunt_box'] = v
    if '--no-tree' in a:
        a.remove('--no-tree'); opt['tree'] = False
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'check':
        out, _f = check(a[1])
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'plan':
        plan(KB.Built(a[1]), opt)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if diff(a[1], a[2]) else 0)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
