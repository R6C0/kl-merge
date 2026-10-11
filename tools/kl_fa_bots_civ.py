#!/usr/bin/env python3
"""
AI HEISTERS THAT KILL A CIVILIAN FOR HER MONEY: a step on a FINISHED bots build (the squads of kl_fa_bots.py, with
or without the dynamic step of kl_fa_bots_dyn.py). Research and live checks: re/bots_civs.md.
OFFLINE: nothing here installs anything or starts the game. NOTHING OF IT HAS RUN IN THE GAME.

The owner, 2026-10-11: 'they need to know how to kill civs some of them otherwise they cant get money'.

    python kl_fa_bots_civ.py census <folder> ...                 the money civilians of a build, their squads, what the
                                                                 bots' chains pass near them (read only)
    python kl_fa_bots_civ.py build <build> <out> [options]       plan + write + every check of this module; exit 1 on a FAIL
    python kl_fa_bots_civ.py check <folder>                      kl_fa_bots_dyn.check (so kl_fa_bots.check too) with the
                                                                 lines this step is known to cause counted apart, + this
                                                                 module's own rules; exit 1 on a FAIL
    python kl_fa_bots_civ.py diff <build> <out>                  what the step changed; exit 1 if anything but the
                                                                 killers' new steps and the civilians' money differs
    python kl_fa_bots_civ.py owner <work>\\build [M01 ...]        the builds on the owner's tab into z_civ\\<map> (OWNER)
    options
      --donor <folder>   a build of the same map in which the civilians still HAVE their money (kl_fa_bots' option
                         'window' took the OnlineMoneyCtrl and its trigger off their groups): the two controllers
                         are put back from there, byte for byte, before anything else
      --killers a,b,..   the squads that may kill, in order of preference (default 2,4,5,8 = point man, the two
                         flankers, the runner; never a looter or the rear guard)
      --count N          killers per civilian (default 2)
      --reach D          a civilian is a squad's business when her post is within D of one of its loot places
                         (default 1500)
      --reach-height H   ... and within H in height (default 350)
      --when after|before  where the steps go into the killer's chain: after the stop's loot wait (default: the shop
                         is empty by then and the owner's 'they might go back for it'), or before the walk to the
                         stop's loot place (the form of round 1)
      --go S             seconds the killer walks to her before he is told to shoot (default 5)
      --rest S           seconds from that order until he is sent on, dead or not (default 7: the owner's 'if nothing
                         happens for like 5ish seconds they get fed up n move' + the take)
      --no-flag          the civilians' money keeps stored field 11 = 0 (default: 1, 'closed to the AI's own loot
                         test' - THE TRAP OF RUNS L8 / L10 STAYS OPEN WITHOUT IT; only for a test)
      --accept-window    (build, check) the window rule of check() becomes a NOTE: squads that are NOT sent to a
                         money civilian have places inside the loot window of her money. Field 11 narrows that
                         trap, it does not close it (re/bots_loot.md 6). FOR A TEST BUILD; such a build is no
                         candidate for the owner's tab before a run has shown nobody held at her post.

WHAT IS READ (kl2.exe; re/bots_civs.md has the addresses)
  - A civilian's money is an OnlineMoneyCtrl + a TriggerBox2 on her GROUP node. Nothing in the take looks at her:
    not the trigger (0x626ec0: every player / Ally actor inside the ball), not the money object (0x6cdb40), not the
    rules (0x56f6e0). Dead or alive is the same to the code. What a death changes is that she LIES STILL.
  - No AI of team Ally shoots a Neutral by itself. The game has a rout for it that no level of either game uses:
    KillCiviliansBehaviourRout (ZGROUP; fields: 0 s = a squad's group, 1 refs NEXT, 2 b, 3 b). Its goal
    (CPPScript::ZKillCiviliansBehaviourGoal slot 2, 0x49a5c0): for every member of THAT squad that is not dead, every
    2 s, every soldier of the rout's own squad gets the order 'cover fire for 3 s at the point 50 above her node'
    (soldier virtual +0x14c = 0x831850 -> CPPScript::ZCoverFire; when the soldier's task at +0x5ac is running and
    0x4c53b0(point) answers 1 the point goes to THAT task instead, 0x809830: not read what it is); when all of them
    are dead the rout's NEXT fires. A civilian IS a member of her squad's list +0xc0 (ZSquadScript slot 14, 0x7b39f1
    -> 0x48c480); a member taken out of the list (0x5230c0, 0x7bf950: the slot is set to 0) is passed over by the
    goal (0x49a5f6, 0x49a6a9). The rout's init (0x4af120) takes the squad object untested: check() wants the named
    squad earlier in scene order than the rout.
  - DefendNPCPosBehaviourRout (37 uses in the story levels; fields 0 refs NEXT, 1 b, 2 b, 3 f, 4 s = an object): its
    goal (0x5ed640) orders every member with [actor+0x576] == 1 to that object's place (soldier virtual +0x13c =
    0x760e50, the order the rules use for 'go to the boarding box') again every field 3 seconds, for as long as it
    is the squad's goal. It ENDS, firing its NEXT, when a pass ordered nobody (0x5ed6e3) or the object does not
    resolve (0x5ed692); NEXT is empty on both of this step's.
  - The bool at property offset 0x3e (member +0x42) of every rout = 'start once': a start message to a rout that
    has started before is skipped (rout slot 26, 0x4ebed0). 1 on the three routs here, as on the bots' Defend steps.
  - The LAST bool of every rout (property offset 0x3f) set = the squad takes no further rout (0x791090 starts a
    goal only in rout state 0 or 4 and with [squad object + 0xbc] == 0; 0x791138 sets that byte): it is 0 on
    everything made here, and check() FAILs anything else.
  - A new rout replaces the squad's running goal whatever its class (0x7f6750 takes [squad+0x154] off through
    0x4f3350 before it queues the new one; goal slots 9 and 13 are the same stub for the Defend, DefendNPCPos and
    KillCivilians goals: read whole by the review).
  - A civilian killed by a BOT costs nobody anything by the rules' death notice (slot 16, 0x485740): everything past
    the crew bookkeeping is for a killer of the PLAYER class only (0x485833); a human who kills her gets
    [tuning+0xc18] on score +0x2c (0x485892). The traitor bookkeeping (0x6706b0) runs for a victim with a crew
    record only.

WHAT A KILLER'S CHAIN GETS (per civilian in reach of one of its loot stops; '<X>' = with --when after (default) the
node the stop's loot wait names as its next link; with --when before the step that walks to the loot place of that
stop, the last DefendBehaviourRout before the stop's loot wait)
  every reference to <X> inside the squad -> civ_<name>_1_Timer_go
  civ_<name>_1_Timer_go        TriggerDelay2 0.1 s  -> civ_<name>_3_Timer_shoot, civ_<name>_2_Follow
  civ_<name>_2_Follow          DefendNPCPosBehaviourRout {NEXT none, 1, 0, 1.0 s, her ACTOR}: walk to where she IS
                               (the actor's node is what the kill goal reads her place from, 0x49a62e)
  civ_<name>_3_Timer_shoot     TriggerDelay2 --go s -> civ_<name>_6_Timer_fed_up, civ_<name>_4_Kill
  civ_<name>_4_Kill            KillCiviliansBehaviourRout {her squad, NEXT civ_<name>_5_Take, 1, 0}
  civ_<name>_5_Take            DefendNPCPosBehaviourRout {.., her money GROUP}: stand where the money's trigger is
                               (the ball and the hidden test are on the group node, 0x783e60 / 0x6cdb65: right
                               whether the group moves with her or stays at the post)
  civ_<name>_6_Timer_fed_up    TriggerDelay2 --rest s -> <X> (or the next civilian's _1_), whatever has happened
  The chain itself runs through the three TIMERS only: no order of this step can hold it up. The next Defend step
  of the build then replaces whatever goal the squad has, and the build goes on as it was.
  THE OTHERS are not touched: no node, no reference.

WHAT THE CIVILIANS GET
  - their money back where option 'window' took it out (--donor), for the human too;
  - OnlineMoneyCtrl field 11 = 1 ('behind a door' for the AI: ZLootTactic's test, 0x451a88, passes such an object
    over while no enabled KickDoor is near - these maps have none; the take, 0x6cdb40 / 0x8e8750, never reads it).
    So no bot's loot tactic goes for her money by itself - the trap of runs L8 / L10 (re/bots_loot.md) - and the
    human takes it as ever. kl_fa_bots.check knows the field: 'no candidate' - and so says NOTHING about what the
    field leaves open: the action's quirk (re/bots_loot.md 6: a bot runs to the NEAREST of its five candidates
    whatever the field says, while another one passes the test) is NARROWED, NOT CLOSED. check() here measures it
    per squad and FAILs for every squad that is not sent to her and has a place inside her window; --accept-window
    makes that a NOTE for a test build. On Late Night Opening this swaps track A's proven removal (run W1_DM02) for
    the field: no candidate for the owner's tab before a run.

WHAT IS WRITTEN: .prp, .gms + .buf (entities added inside the killers' squad groups), .oct / .rmi / .rmc (slot ids
  renumbered; nothing listed anew: the new groups have no places, like the build's SquadModifier steps). No model,
  no animation, no sound: the four large blocks keep their size; the .prm is not touched.

THE EXISTING CHECKS FAIL A BUILD OF THIS STEP AS THEY STAND, ON PURPOSE (re/bots_civs.md 7):
  - kl_fa_bots.check rule 5 ('nothing the levels do not already run'): 'controller KillCiviliansBehaviourRout /
    DefendNPCPosBehaviourRout is not used by stock F07; stock levels that run it in Arcade: NONE'. True: the first
    is in no level of either game, the second in story levels only. NEITHER HAS RUN IN A ROUND OF OURS.
  - kl_fa_bots_dyn.check does not know a step that starts something beside its next link unless that is a cover
    hold or a relay: '<timer> also starts civ_.._2_Follow (None)', two lines a civilian a killer.
  check() here runs kl_fa_bots_dyn.check, takes exactly those lines apart (named, counted, compared with the nodes
  this step made), says so in two NOTEs and FAILs on every other line. Neither file was edited.
  '--killers 0' makes a build with the money edit alone (.prp only): for telling the two apart in a live run.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, math, os, re, shutil, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene
import kl_fa_bots as F
import kl_fa_bots_dyn as D
import kl_octree as O
import kl_prpjoin as J
from kl_prp import units

R_ = F.R_
BS = '\\'
KILLERS = (2, 4, 5, 8)      # OURS: the point man, the two flankers, the runner (kl_fa_bots_dyn.PERS); the looters (3, 6)
                            # and the rear guard (7) never - 'some of them' (the owner)
COUNT = 2                   # GUESS: two a civilian, so that one may die on the way
REACH = (1500.0, 350.0)     # GUESS: her post within this of a loot place of the squad (distance, height)
GO = 5.0                    # GUESS, seconds of walking to her before the order to shoot (a bot walks ~3 m/s: run FO_J1)
REST = 7.0                  # the owner: 'like 5ish seconds they get fed up n move'; + the take (75,000 = 4 parts of 0.7 s)
START = 0.1                 # the shortest timer that has run in a bot's chain (kl_fa_bots_dyn's '--fork-gap 0.1')
FORM_FOLLOW = ('L05', R_ + 'AI!Enemies!A-Stairways!A9!SQ_Mob_4thFloor_04' + BS + 'DefendNPCPosBehaviour')
FORM_KILL = ('L02', R_ + 'AI!Friendly!Glazer04_DemolishedHouse#01' + BS + '050_FollowBehaviour')
#   ^ no level has a KillCiviliansBehaviourRout. FollowBehaviourRout is a ZGROUP's rout with the same four stored
#     fields in the same order and of the same type handlers (s 0xcfbf70, refs 0xcfc0a0, b, b 0xcfc100: props of
#     0xd04f8c against 0xd05594), so its node is taken and the controller's NAME replaced. The values are set here.
KILL, FOLLOW = 'KillCiviliansBehaviourRout', 'DefendNPCPosBehaviourRout'
OWNER = (('z_route3', 'M01', None), ('z_loot3', 'M02', ('z_route', 'M02')), ('z_cover3', 'M03', None), ('z_route', 'M06', None))
WHEN = 'after'              # where the steps go into a killer's chain: 'after' the stop's loot wait (the review's point 6:
                            # the shop is then empty, so the loot tactic - which beat Defend orders in run L10 - has no
                            # candidate to pull the bot back to the cases; and the owner: 'if they do end up getting the
                            # money they might go back for it'), or 'before' the walk to the stop's loot place (round 1)
WINDOW_NEAR = 150.0         # check(): 'at a clerk's post' in the live checks' words (re/bots_civs.md 6)
DEFAULTS = {'killers': KILLERS, 'count': COUNT, 'reach': REACH[0], 'reach_height': REACH[1], 'go': GO, 'rest': REST, 'flag': True,
            'donor': None, 'when': WHEN, 'accept_window': False}
SIDE_NEW = ('civ.json', 'civ.txt')


def short(path):
    """'Civilians!Civ_male_watch\\female_clerk' -> 'Civ_male_watch' (the squad's own name: one civilian a squad)."""
    return path.split(BS)[0].split('!')[-1]


_GROUP_RE = re.compile('^' + re.escape(F.GROUP_NAME).replace('%d', r'(\d)') + '$')


def squad_no(sc, g):
    """The number N of the bot whose actor's parent group is g ('Glazer_Bodyguard_0N', kl_fa_bots.GROUP_NAME: the
    game itself reads the digit at index 18 of that name, kl2 0x588980). Any other name is refused."""
    m = _GROUP_RE.match(sc.names[g])
    if not m:
        raise ValueError('%s is not a bot\'s group (%s)' % (sc.names[g], F.GROUP_NAME.replace('%d', 'N')))
    return int(m.group(1))


# ------------------------------------------------------------------ what is there
def civilians(B, donor=None):
    """The money civilians of build B -> [dict], scene order: path (of the GROUP that carries the money), node,
    actor (the ZFFActor with a ZCivilian below it), squad (her top-level group; it must carry a ZSquadScript), post,
    amount, flag (stored field 11), has (the money is in this build), members (civilians of that squad).
    With a donor build: also the groups that have their money THERE and not here (kl_fa_bots' strip_money)."""
    sc, out, seen = B.sc, [], set()

    def one(k, amount, flag, has):
        actor = next((j for j in range(k + 1, sc.end[k]) if sc.cls(j) == 'ZFFActor' and kl_fa.has(sc, j, 'ZCivilian')), None)
        top = sc.top[k]
        return collections.OrderedDict(
            path=sc.path[k][5:], node=k, actor=actor, squad=top, squad_ok=kl_fa.has(sc, top, 'ZSquadScript') and sc.cls(top) == 'ZGROUP',
            post=tuple(B.at(k)), amount=int(amount), flag=bool(flag), has=has,
            members=[j for j in range(top, sc.end[top]) if sc.cls(j) == 'ZFFActor'])

    for o in F.money_objects(B):
        if o['kind'] == 'civilian':
            out.append(one(o['node'], o['amount'], o['flag'], True)); seen.add(o['node'])
    if donor is not None:
        for o in F.money_objects(donor):
            if o['kind'] != 'civilian':
                continue
            hit = sc.resolve(donor.sc.path[o['node']])
            if len(hit) != 1:
                raise ValueError('donor: %s names %d nodes of the build' % (donor.sc.path[o['node']], len(hit)))
            if hit[0] not in seen:
                out.append(one(hit[0], o['amount'], o['flag'], False)); seen.add(hit[0])
    out.sort(key=lambda c: c['node'])
    return out


def loot_stops(B, g):
    """The loot stops of one squad's first chain (kl_fa_bots_dyn.graph, branch set 0) -> [dict]: wait (the node of
    the loot wait), step (the last DefendBehaviourRout before it = the walk to the loot place), after (the ONE node
    the loot wait names as its next link - a step, a modifier or a RandomTrigger; None when it names none or several),
    places [points].
    A stop whose step or wait is not in every branch set of the chain is left out (not walked every round)."""
    sc, out = B.sc, []
    chain = g['chains'][0] if g['chains'] else []
    for i, it in enumerate(chain):
        if it['ctrl'] == 'TriggerLootDepleted' or (it['ctrl'] == 'TriggerDelay2' and 'done_looting' in it['name']):
            prev = [x for x in chain[:i] if x['ctrl'] == 'DefendBehaviourRout' and x.get('places')]
            if not prev:
                continue
            L = prev[-1]
            if not all(any(x['k'] == L['k'] for x in c) and any(x['k'] == it['k'] for x in c) for c in g['sets'][0]):
                continue
            nx = [j for s in it['v'][D.NEXT[it['ctrl']]] for j in sc.resolve(s)]
            out.append({'wait': it['k'], 'step': L['k'], 'after': nx[0] if len(nx) == 1 and sc.top[nx[0]] == g['top'] else None,
                        'places': [tuple(B.at(j)) for j in L['places']]})
    return out


def squad_places(B, g):
    """Every place a squad's Defend steps name, in every branch set and behind every cover draw -> {place node: point}."""
    sc, out = B.sc, {}

    def of(v):
        return [j for s in ([v[0]] if v[0] else []) + list(v[1]) for j in sc.resolve(s)]

    for sets in g['sets']:
        for ch in sets:
            for it in ch:
                for j in it.get('places') or ():
                    out[j] = tuple(B.at(j))
                for _kind, j, alts in it['side']:
                    for x in (alts or [j]):
                        cn, v = g['ctrl'].get(x, (None, None))
                        if cn == 'DefendBehaviourRout':
                            for p in of(v):
                                out[p] = tuple(B.at(p))
    return out


def plan(B, opt=None, donor=None, log=print):
    """Who kills whom, where -> dict (JSON): civilians, killers {squad number: [{civilian, step, distance}]}, notes."""
    o = dict(DEFAULTS); o.update(opt or {})
    sc = B.sc
    G = D.graph(B)
    civs = civilians(B, donor)
    by_no = {}
    for name, g in G.items():
        by_no[squad_no(sc, sc.parent[g['actor']])] = (name, g)
    P = collections.OrderedDict(folder=B.folder, options={k: (list(v) if isinstance(v, tuple) else v) for k, v in o.items() if k != 'donor'},
                                donor=donor.folder if donor is not None else None, civilians=[], killers=collections.OrderedDict(), notes=[])
    stops = {N: loot_stops(B, g) for N, (_n, g) in by_no.items()}
    rh = float(o['reach_height'])
    if o['when'] not in ('before', 'after'):
        raise ValueError('--when is before or after, not %r' % (o['when'],))
    for c in civs:
        row = collections.OrderedDict(path=c['path'], post=[round(v) for v in c['post']], amount=c['amount'], money_here=c['has'],
                                      flag_was=c['flag'], squad=sc.names[c['squad']], killers=[], near={})
        why = None
        if c['actor'] is None:
            why = 'no civilian actor below her group'
        elif not c['squad_ok']:
            why = 'her top-level group %s has no ZSquadScript' % sc.names[c['squad']]
        elif len(c['members']) != 1:
            why = 'her squad has %d actors: the rout would have the others shot too' % len(c['members'])
        for N in sorted(by_no):
            best = None
            for s in stops[N]:
                for p in s['places']:
                    d = math.dist(p, c['post'])
                    if abs(p[1] - c['post'][1]) <= rh and (best is None or d < best[0]):
                        best = (d, s)
            if best:
                row['near'][N] = round(best[0])
        # in the order of preference, not of the squads' numbers
        if why is None:
            pref = [N for N in o['killers'] if N in row['near'] and row['near'][N] <= float(o['reach'])][:int(o['count'])]
            row['killers'] = pref
            for N in pref:
                best = min(((math.dist(p, c['post']), s) for s in stops[N] for p in s['places'] if abs(p[1] - c['post'][1]) <= rh),
                           key=lambda x: x[0])
                st = best[1]
                after = sc.names[st['after']] if st['after'] is not None else None
                when = o['when'] if after is not None else 'before'
                if when != o['when']:
                    P['notes'].append('Squad#%02d, %s: the loot wait %s names no single next link: the steps go BEFORE %s'
                                      % (N, short(c['path']), sc.names[st['wait']], sc.names[st['step']]))
                P['killers'].setdefault(N, []).append(collections.OrderedDict(
                    civilian=c['path'], step=sc.names[st['step']], wait=sc.names[st['wait']], after=after, when=when,
                    splice=after if when == 'after' else sc.names[st['step']], distance=round(best[0])))
            if not pref:
                why = 'no loot place of a squad that may kill (%s) within %d of her post (nearest: %s)' % (
                    ', '.join('#%02d' % n for n in o['killers']), o['reach'], ', '.join('#%02d %d' % kv for kv in sorted(row['near'].items(), key=lambda kv: kv[1])[:3]) or 'none')
        row['nobody'] = why
        P['civilians'].append(row)
        log('%s at (%d, %d, %d), %d%s: %s' % (c['path'], *c['post'], c['amount'], '' if c['has'] else ' (taken out of this build; back from the donor)',
                                              'killers ' + ', '.join('Squad#%02d (%s, %d from its loot place)' % (N, D.PERS[N].role, row['near'][N]) for N in row['killers'])
                                              if row['killers'] else 'NOBODY IS SENT - ' + why))
    for N, jobs in P['killers'].items():               # the nearest first where a stop has two
        jobs.sort(key=lambda j: (j['splice'], j['distance']))
    for n in P['notes']:
        log('NOTE  ' + n)
    if not civs:
        P['notes'].append('no civilian carries money on this map: nothing to do, the build is copied as it is')
    return P


# ------------------------------------------------------------------ the nodes
def _repoint(M, node, old, new):
    """Every reference token of node's controllers that names `old` (a scene path, case ignored) -> `new`."""
    n, key = 0, None
    for i, (nm, body) in enumerate(node.ctrls):
        out = []
        for op, pl in body:
            if op == 0x0c and len(pl) == 4 and M.p.keys[struct.unpack('<I', pl)[0]].lower() == old.lower():
                if key is None:
                    key = M.p.key_index(new)
                pl = struct.pack('<I', key); n += 1
            out.append((op, pl))
        node.ctrls[i] = (nm, out)
    return n


def make(B, P, log=print):
    """The plan as nodes -> (maker, {top node of the build: Node}, facts)."""
    sc = B.sc
    G = D.graph(B)
    M = D.Maker()
    out, facts = {}, collections.OrderedDict()
    civ = {c['path']: c for c in civilians(B, F.Built(P['donor']) if P.get('donor') else None)}
    go, rest = float(P['options']['go']), float(P['options']['rest'])
    for name, g in G.items():
        N = squad_no(sc, sc.parent[g['actor']])
        jobs = P['killers'].get(N) or P['killers'].get(str(N))
        if not jobs:
            continue
        top = D.from_build(M, B, g['top'])
        old = list(top.kids)
        path = lambda nm: '%s%s%s%s' % (R_, name, BS, nm)
        made = []

        def timer(nm, seconds, nxt):
            t = top.add(M.clone(D.SX, D.FORM['timer'], nm))
            t.keep = None
            M.place(t, (0.0, 0.0, 0.0))
            M.set(t, 'TriggerDelay2', {0: float(seconds), 1: 0.0, 2: -1.0, 3: 0, 4: nxt})
            made.append(nm)

        def follow(nm, actor):
            # stock L05 ...SQ_Mob_4thFloor_04\DefendNPCPosBehaviour {[], 1, 0, 1.0, 'ROOT\AI!Friendly!Kane_L05__'}: the
            # values are stock's; only the object changes (`actor` = the path of the node to walk to).
            # _2_Follow names her ACTOR node: the node the kill goal itself takes her place from (kl2 0x49a62e ->
            # 0x7b3020), right whichever of the two nodes the engine moves.
            # _5_Take names her money GROUP: the take trigger's ball and the money's hidden test are on the group node
            # (0x783e60, 0x6cdb65), so the group is where the money is paid whether it moved with her or stayed at
            # the post (the review's MUST 2; round 1 named the actor here).
            f = top.add(M.clone(FORM_FOLLOW[0], FORM_FOLLOW[1], nm))
            f.keep = None
            M.place(f, (0.0, 0.0, 0.0))
            M.set(f, FOLLOW, {0: [], 1: 1, 2: 0, 3: 1.0, 4: actor})
            made.append(nm)

        def kill(nm, squad, nxt):
            k = top.add(M.clone(FORM_KILL[0], FORM_KILL[1], nm))
            k.keep = None
            if len(k.ctrls) != 1 or M.p.key(k.ctrls[0][0]) != 'FollowBehaviourRout' or k.kids:
                raise ValueError('the form %s is not one FollowBehaviourRout on a group without children' % FORM_KILL[1])
            k.ctrls = [((k.ctrls[0][0][0], struct.pack('<I', M.p.key_index(KILL))), k.ctrls[0][1])]
            M.place(k, (0.0, 0.0, 0.0))
            # field 2 (property offset 0x3e, member +0x42) = 1 = 'start once' (rout slot 26, kl2 0x4ebed0: a start message
            # to a rout that has started before is skipped), as on every step of the bots' squads; field 3 (0x3f) = 0:
            # 1 would shut the squad to every later rout (0x791138)
            M.set(k, KILL, {0: squad, 1: nxt, 2: 1, 3: 0})
            made.append(nm)

        by_step = collections.OrderedDict()
        for j in jobs:
            by_step.setdefault(j.get('splice') or j['step'], []).append(j)
        rows = []
        for step, js in by_step.items():
            names = []
            for j in js:
                c = civ[j['civilian']]
                tag = 'civ_%s' % short(c['path'])
                names.append((tag, c))
            for i, (tag, c) in enumerate(names):
                after = path(names[i + 1][0] + '_1_Timer_go') if i + 1 < len(names) else path(step)
                timer(tag + '_1_Timer_go', START, [path(tag + '_3_Timer_shoot'), path(tag + '_2_Follow')])
                follow(tag + '_2_Follow', sc.path[c['actor']])
                timer(tag + '_3_Timer_shoot', go, [path(tag + '_6_Timer_fed_up'), path(tag + '_4_Kill')])
                kill(tag + '_4_Kill', sc.path[c['squad']], [path(tag + '_5_Take')])
                follow(tag + '_5_Take', sc.path[c['node']])
                timer(tag + '_6_Timer_fed_up', rest, [after])
            first = path(names[0][0] + '_1_Timer_go')
            if len(sc.resolve(path(step))) != 1:
                raise ValueError('%s: %s names %d nodes' % (name, step, len(sc.resolve(path(step)))))
            n = sum(_repoint(M, x, path(step), first) for kid in old for x in kid.walk())
            if not n:
                raise ValueError('%s: nothing inside the squad names the step %s' % (name, step))
            when = js[0].get('when', 'before')
            rows.append(collections.OrderedDict(step=step, when=when, wait=js[0].get('wait'), civilians=[c['path'] for _t, c in names],
                                                references_repointed=n, seconds=round(len(names) * (START + go + rest), 1)))
            log('%s (%s): %s -> %s -> %s; %d reference(s) to %s now name %s; %.1f s more in its chain'
                % (name, D.PERS[N].role, 'after the loot wait %s' % js[0].get('wait') if when == 'after' else 'before the walk to the loot place',
                   ' -> '.join('walk to %s, shoot, stand on her money' % short(c['path']) for _t, c in names), step, n, step,
                   names[0][0] + '_1_Timer_go', len(names) * (START + go + rest)))
        facts[name] = collections.OrderedDict(squad=N, role=D.PERS[N].role, splices=rows, nodes=made)
        out[g['top']] = top
    return M, out, facts


def _tokens_into(sc, toks, keys):
    """Tokens of another file's key table as tokens of scene sc's (kl_prpjoin._intern for one loaded scene)."""
    out = []
    for op, pl in toks:
        if op in J.KEYED or op == 0x0f:
            idx = struct.unpack_from('<%dI' % (len(pl) // 4), pl)
            new = [sc.p.key_index(keys[i]) for i in (idx if op in J.KEYED else idx[1:])]
            pl = struct.pack('<%dI' % len(idx), *(new if op in J.KEYED else (idx[0],) + tuple(new)))
        out.append((op, pl))
    return out


def money_edit(B, Jn, P, donor, log=print):
    """The civilians' groups in the joined scene Jn: the money back from the donor where this build has none, and
    stored field 11 of the OnlineMoneyCtrl set. Only controllers of those groups change. -> {path: dict}"""
    out = collections.OrderedDict()
    for row in P['civilians']:
        hit = Jn.resolve(R_ + row['path'])
        if len(hit) != 1:
            raise ValueError('%s names %d nodes' % (row['path'], len(hit)))
        k, n = hit[0], Jn.nodes[hit[0]]
        rec = collections.OrderedDict(amount=row['amount'], put_back=[], field_11=None)
        if not row['money_here']:
            dsc = donor.sc
            dk = dsc.resolve(R_ + row['path'])[0]
            dn = dsc.nodes[dk]
            names = [dsc.p.key(nm) for nm, _b in dn['ctrls']]
            have = [Jn.p.key(nm) for nm, _b in n['ctrls']]
            if [x for x in names if x in have] != have or J.text(dsc, dn['props']) != J.text(Jn, n['props']):
                raise ValueError('%s: the donor\'s group is not this build\'s group plus the money (controllers %s against %s)' % (row['path'], names, have))
            new = []
            for nm, body in dn['ctrls']:
                cn = dsc.p.key(nm)
                if cn in have:
                    cur = next(c for c in n['ctrls'] if Jn.p.key(c[0]) == cn)
                    if J.text(dsc, [nm] + body) != J.text(Jn, [cur[0]] + cur[1]):
                        raise ValueError('%s: controller %s differs from the donor\'s' % (row['path'], cn))
                    new.append(cur)
                else:
                    new.append((_tokens_into(Jn, [nm], dsc.p.keys)[0], _tokens_into(Jn, body, dsc.p.keys)))
                    rec['put_back'].append(cn)
            n['ctrls'] = new
            if sorted(rec['put_back']) != ['OnlineMoneyCtrl', 'TriggerBox2']:
                raise ValueError('%s: the donor would put back %s' % (row['path'], rec['put_back']))
        mi = [i for i, (nm, _b) in enumerate(n['ctrls']) if Jn.p.key(nm) == 'OnlineMoneyCtrl']
        if len(mi) != 1:
            raise ValueError('%s: %d OnlineMoneyCtrl' % (row['path'], len(mi)))
        if P['options']['flag']:
            def fn(us):
                if len(us) != 12 or len(us[11]) != 1 or len(us[11][0][1]) != 1:
                    raise ValueError('%s: OnlineMoneyCtrl field 11 is not one byte' % row['path'])
                rec['field_11'] = [us[11][0][1][0], 1]
                us[11] = [(us[11][0][0], bytes([1]))]
            kl_fa.edit(Jn, k, mi[0], fn)
        out[row['path']] = rec
        log('%s: %s%s' % (row['path'], 'OnlineMoneyCtrl + TriggerBox2 put back from the donor (%d for whoever takes it, the human too); ' % row['amount']
                          if rec['put_back'] else '',
                          'OnlineMoneyCtrl field 11 %d -> 1: no candidate of the AI\'s own loot test (kl2 0x451a88), the take is as it was' % rec['field_11'][0]
                          if rec['field_11'] else 'field 11 left as it is (--no-flag)'))
    return out


# ------------------------------------------------------------------ writing
def apply(B, P, dst, donor=None, log=print):
    """Write the plan into a copy of build B in folder dst -> report dict. (kl_fa_bots_dyn.apply's way of writing,
    without the removal: an entity that stays keeps its record, the new ones get new REF ids.)"""
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    before = F.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    rep = collections.OrderedDict(source=B.folder, out=dst)
    new = dict(B.files)
    nothing = not P['civilians']
    if not nothing:
        F._roundtrip(B)
        octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
        pre = F.room_sets_check(B.scene, octx, rmi, rmc)
        M, made, facts = make(B, P, log)
        tops_new = [made[t] for t in sc.tops() if t in made]
        if tops_new:
            q, _order = M.scene(tops_new)
            qtop = dict(zip([t for t in sc.tops() if t in made], q.tops()))
            Jn = J.join(sc, [(q, qtop[t]) if t in made else (sc, t) for t in sc.tops()], 'civ')
        else:
            Jn = same
        money = money_edit(B, Jn, P, donor, log)
        bad = J.misfits(Jn)
        if bad:
            raise ValueError('objects that do not fit their class: %s' % [(Jn.path[k], w, y) for k, w, y in bad[:3]])
        prp = Jn.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
            raise ValueError('the new .prp does not round-trip')
        new[B.ext['.prp']] = prp
        added = [n for t in tops_new for n in t.walk() if getattr(n, 'keep', None) is None]
        moved = 0
        if added:
            A = B.scene
            slot0 = A.slots()
            ref_before = A.ref_slots
            nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])

            def ent(n, parent):
                nonlocal nxt
                if getattr(n, 'keep', None) is not None:
                    e = n.keep
                else:
                    e = kl_scene.Entity()
                    e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
                    e.rot, e.trans, e.raw, e.aux, e.links, e.lkey = n.rot, n.trans, None, n.aux, n.links, 0
                    e.ref = nxt; nxt += 1
                e.parent = parent
                e.kids = [ent(k, e) for k in n.kids]
                n.ent = e
                return e

            for t in tops_new:
                ent(t, None)
            A.ref_slots = max(A.ref_slots, nxt)
            faults = A.check()
            if faults:
                raise ValueError('kl_scene.check: %s' % faults[:3])
            ents = list(A.entities())
            if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
                raise ValueError('the new .gms and .prp disagree on the entities')
            gms, buf = A.write()
            slot1 = A.slots()
            ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
            ids[1] = 1
            octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
            moved = sum(1 for a, b in ids.items() if a != b)
            if octx.record_refs() != octn.record_refs():
                raise ValueError('the .oct records moved although no tree changed its size')
            post = F.room_sets_check(A, octn, rmin, rmcn)
            if post != pre:
                raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
            new[B.ext['.gms']], new[B.ext['.buf']] = kl_gms.pack(gms), buf
            new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
            rep.update(ref_slots=[ref_before, A.ref_slots], entities_before=len(B.ents), entities=len(ents))
        rep.update(entities_added=len(added), classes_added=dict(collections.Counter(J.schema('dd').geoms.get(n.tid) for n in added)),
                   controllers_added=dict(collections.Counter(M.p.key(nm) for n in added for nm, _b in n.ctrls)),
                   slot_ids_moved=moved, squads=facts, money=money)
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    rep['members_changed'] = changed
    os.makedirs(dst, exist_ok=True)
    import kl_graft
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.',) + SIDE_NEW):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst)
    rep.update(big_before=before, big_after=after)
    if before != after:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    if changed:
        sj = os.path.join(dst, 'steps.json')
        if os.path.isfile(sj):                          # kl_maps.audit compares the folder with what was measured
            import kl_maps
            st = json.load(open(sj))
            st['bots'] = sorted(set(st.get('bots') or []) | set(changed))
            st['same'] = [e for e in st.get('same', []) if e not in changed]
            st['final'] = kl_maps.member_ids(dst)
            with open(sj, 'w') as f:
                json.dump(st, f, indent=1)
        # bots.json: kl_fa_bots.check NOTEs 'money the build took out of the level' from plan.edits.money_off - what
        # this step put back is no longer out (kept beside it as money_back, so the history stays readable)
        bj = os.path.join(dst, 'bots.json')
        back_paths = [p for p, r in rep.get('money', {}).items() if r['put_back']]
        if os.path.isfile(bj) and back_paths:
            b = json.load(open(bj), object_pairs_hook=collections.OrderedDict)
            ed = b.get('plan', {}).get('edits') or {}
            off = ed.get('money_off') or {}
            ed['money_back'] = collections.OrderedDict((p, off[p]) for p in back_paths if p in off)
            ed['money_off'] = collections.OrderedDict((p, v) for p, v in off.items() if p not in back_paths)
            with open(bj, 'w') as f:
                json.dump(b, f, indent=1)
            rep['bots_json'] = 'plan.edits.money_off: %d entr(ies) moved to money_back' % len(ed['money_back'])
        with open(os.path.join(dst, 'graft.txt'), 'a') as f:
            f.write('kl_fa_bots_civ: %d killer squad(s) get the steps for %d civilian(s) (%d entities in); the civilians\' money: %s; from %s; options %s\n'
                    % (len(rep.get('squads', {})), sum(1 for r in P['civilians'] if r['killers']), rep.get('entities_added', 0),
                       ', '.join('%s%s' % (short(p), ' (put back)' if r['put_back'] else '') for p, r in rep.get('money', {}).items()),
                       B.folder, json.dumps(P['options'], sort_keys=True)))
    log('written %s: %d entities added (%s); members changed: %s; %d slot ids renumbered'
        % (zp, rep.get('entities_added', 0), ', '.join('%s %d' % kv for kv in rep.get('controllers_added', {}).items()) or 'none',
           ' '.join(changed) or 'NONE - the archive is the source\'s byte for byte', rep.get('slot_ids_moved', 0)))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    return rep


# ------------------------------------------------------------------ the check
def my_nodes(sc):
    """The nodes of this step in a build: {node: controller name} for every KILL / FOLLOW rout and every TriggerDelay2
    named civ_* inside a bot squad."""
    out = {}
    for cn in (KILL, FOLLOW):
        for k, _i, _v in kl_fa.controllers(sc, cn):
            if sc.names[sc.top[k]].startswith(F.SQUAD):
                out[k] = cn
    for k, _i, _v in kl_fa.controllers(sc, 'TriggerDelay2'):
        if sc.names[sc.top[k]].startswith(F.SQUAD) and sc.names[k].startswith('civ_'):
            out[k] = 'TriggerDelay2'
    return out


_RE_CLASS = re.compile(r'^kl_fa_bots\.check: controller (\w+) is not used by stock \w+; stock levels that run it in Arcade: NONE$')
_RE_SIDE = re.compile(r'(?:^|\s)(civ_\S+) also starts (civ_\S+) \(None\)$')


def check(folder, log=print, base=True, accept_window=None):
    """-> ([(severity, text)], facts). kl_fa_bots_dyn.check (kl_fa_bots.check inside it) with the 'also starts'
    lines of this step's routs taken apart, and the rules of this module.
    accept_window: None = as the build's civ.json says (option --accept-window), True = waive the window rule."""
    out, facts = [], collections.OrderedDict()
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    B = F.Built(folder)
    sc = B.sc
    mine = my_nodes(sc)
    name = lambda k: sc.path[k][5:]
    res = sc.resolve
    cj = os.path.join(B.folder, 'civ.json')
    rep = json.load(open(cj)) if os.path.isfile(cj) else {}
    # ---- the two existing checks
    if base:
        o1, f1 = D.check(folder, log)
        routs = {sc.names[k] for k, cn in mine.items() if cn in (KILL, FOLLOW)}
        known, other = [], []
        new_cls = []                                    # kl_fa_bots.check rule 5: 'nothing the levels do not already run'
        timers = {sc.names[k] for k, cn in mine.items() if cn == 'TriggerDelay2'}
        for s, t in o1:
            m_side, m_cls = _RE_SIDE.search(t), _RE_CLASS.match(t)
            if s == 'FAIL' and m_side and m_side.group(1) in timers and m_side.group(2) in routs:
                known.append(t)
            elif s == 'FAIL' and m_cls and m_cls.group(1) in (KILL, FOLLOW) and mine:
                new_cls.append(m_cls.group(1))
            else:
                other.append((s, t))
        facts['classes_no_arcade_level_runs'] = new_cls
        if new_cls:
            note('kl_fa_bots.check, run as it stands, says FAIL for %s: "not used by stock F0x; stock levels that run it in Arcade: NONE". THAT IS TRUE AND IS '
                 'THIS STEP: %s is in no level of either game (its code was read: re/bots_civs.md 3), %s only in story levels (37 uses). Neither has '
                 'run in a round of ours: load a z_civ build on a TEST tree first' % (' and '.join(new_cls), KILL, FOLLOW))
        # a rout started beside a timer's next link is started by exactly one timer; _5_Take is started by its _4_Kill
        want = sum(1 for k, cn in mine.items() if cn in (KILL, FOLLOW) and not sc.names[k].endswith('_5_Take'))
        facts['kl_fa_bots_dyn'] = {'FAIL': sum(s == 'FAIL' for s, _t in o1), 'NOTE': sum(s == 'NOTE' for s, _t in o1),
                                   'lines_of_this_step': len(known), 'routs_started_beside_a_timer': want}
        out += [(s, 'kl_fa_bots_dyn.check: ' + t) for s, t in other if s == 'FAIL']
        if len(known) != want:
            fail('kl_fa_bots_dyn.check has %d \'also starts\' line(s) for the routs of this step, %d rout(s) are started beside a timer' % (len(known), want))
        if known:
            note('kl_fa_bots_dyn.check, run as it stands, says FAIL with %d line(s) of the form \'<squad>: civ_.._Timer_.. also starts civ_.._2_Follow / '
                 '_4_Kill (None)\' and with nothing else: its graph() knows a cover hold and a relay beside a step\'s next link and no other class. '
                 'They are counted against the %d rout(s) this step starts that way and left out here (re/bots_civs.md 7)' % (len(known), want))
        if f1.get('kl_fa_bots', {}).get('FAIL'):
            pass                                        # (its FAIL lines are in `other` with their prefix)
    # ---- the civilians' money
    civs = civilians(B)
    facts['civilians'] = collections.OrderedDict()
    doors = [B.at(k) for k, _i, _v in kl_fa.controllers(sc, 'KickDoor')]
    for c in civs:
        v = next(v for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if k == c['node'])
        trig = [v2 for k, _i, v2 in kl_fa.controllers(sc, 'TriggerBox2') if k == c['node'] and 'AI_TRIGGER_WITH_ACTIVATOR' in v2
                and isinstance(v2[0], list) and [j for s in v2[0] for j in res(s)] == [c['node']]]
        facts['civilians'][c['path']] = collections.OrderedDict(amount=c['amount'], field_11=int(c['flag']), take_trigger=len(trig),
                                                                 post=[round(x) for x in c['post']])
        if 'ZMONEYCTRL_TYPE_NORMAL' not in v:
            fail('%s: the money is not TYPE_NORMAL' % c['path'])
        if len(trig) != 1 or trig[0][3] != 1:
            fail('%s: not exactly one take trigger on the group that answers to people only (%d; field 3 = %s)' % (c['path'], len(trig), [t[3] for t in trig]))
        if not c['flag']:
            (note if rep.get('plan', {}).get('options', {}).get('flag') is False else fail)(
                '%s: OnlineMoneyCtrl field 11 is 0: every bot\'s own loot tactic counts her %d as loot within 800 of her GROUP node and goes there '
                '(the hold of runs L8 / L10, re/bots_loot.md)' % (c['path'], c['amount']))
        elif any(abs(d[1] - c['post'][1]) <= 250.0 and math.dist(d, c['post']) <= 500.0 for d in doors):
            fail('%s: a KickDoor within 500 / 250 of her: field 11 does not keep the loot tactic off her money (kl2 0x454c20)' % c['path'])
    stripped = (rep.get('plan') or {}).get('civilians') or []
    gone = [r['path'] for r in stripped if r['path'] not in facts['civilians']]
    if gone:
        fail('the plan names %s, which carries no money in this build' % gone)
    # ---- the nodes of this step
    G = D.graph(B)
    ctrl_all = {}
    for cn in ('TriggerDelay2', 'DefendBehaviourRout', KILL, FOLLOW):
        for k, _i, v in kl_fa.controllers(sc, cn):
            ctrl_all[k] = (cn, v)
    civ_actor = {c['actor']: c for c in civs}
    civ_squad = {c['squad']: c for c in civs}
    civ_node = {c['node']: c for c in civs}
    facts['killers'] = collections.OrderedDict()
    refs_in = list(J.references(sc))
    seen_tags = collections.defaultdict(set)
    for k, cn in sorted(mine.items()):
        top = sc.top[k]
        v = ctrl_all[k][1]
        if sc.parent[k] != top or not kl_fa.has(sc, top, 'ZSquadScript'):
            fail('%s is not a child of a squad\'s group: a rout finds its squad through its parent (kl2 0x4aff50)' % name(k))
        if cn == FOLLOW:
            tg = res(v[4]) if v[4] else []
            if v[0] or v[1] != 1 or v[2] != 0 or abs(v[3] - 1.0) > 1e-6:
                fail('%s: fields 0..3 are %s (stock L05 and this step: [], 1, 0, 1.0; field 2 = 1 would shut the squad to every later rout)' % (name(k), v[:4]))
            take = sc.names[k].endswith('_5_Take')
            if len(tg) != 1 or tg[0] not in (civ_node if take else civ_actor):
                fail('%s: field 4 %r is not %s of a civilian who carries money (the walk goes to her ACTOR, the node the kill goal reads her '
                     'place from, kl2 0x49a62e; the stand goes to her money GROUP, the node the take trigger and the money are on, 0x783e60 / '
                     '0x6cdb65)' % (name(k), v[4], 'the money group' if take else 'the actor'))
        elif cn == KILL:
            tg = res(v[0]) if v[0] else []
            nx = [j for s in v[1] for j in res(s)]
            if v[2] != 1 or v[3] != 0:
                fail('%s: fields 2, 3 are %s (this step: 1, 0; field 3 = 1 would shut the squad to every later rout, kl2 0x791138)' % (name(k), v[2:4]))
            if len(tg) != 1 or tg[0] not in civ_squad or not kl_fa.has(sc, tg[0], 'ZSquadScript'):
                fail('%s: field 0 %r is not the squad of a civilian who carries money' % (name(k), v[0]))
            else:
                acts = [j for j in range(tg[0], sc.end[tg[0]]) if sc.cls(j) == 'ZFFActor']
                if len(acts) != 1 or not kl_fa.has(sc, acts[0], 'ZCivilian'):
                    fail('%s: the squad it names has %d actors (the goal has EVERY member of that squad shot, kl2 0x49a5c0)' % (name(k), len(acts)))
                # the rout's init (slot 14, kl2 0x4af120) takes the squad object [ZSquadScript+0x3c] with no null test on
                # the node (0x4af12c) or the pointer (0x4af15c); a null squad is a read of [0+0xc0] at 0x49a5ce when the
                # rout starts. The squad object is made in ZSquadScript's slot 13 (0x6316b0). Whether every controller's
                # slot 13 runs before any slot 14 is likely, not proven: so the squad must stand EARLIER in scene order.
                if tg[0] >= k:
                    fail('%s (node %d): the squad it names, %s (node %d), does not come before it in scene order: its init (kl2 0x4af120) '
                         'takes the squad object untested' % (name(k), k, name(tg[0]), tg[0]))
            if len(nx) != 1 or len(v[1]) != 1 or mine.get(nx[0]) != FOLLOW or sc.top[nx[0]] != top:
                fail('%s: its NEXT is not one %s of the same squad' % (name(k), FOLLOW))
        else:
            if v[1:4] != [0.0, -1.0, 0]:
                fail('%s: fields 1..3 are %s (every stock bot timer: 0.0, -1.0, 0)' % (name(k), v[1:4]))
        m_tag = re.match(r'^(civ_.+)_[1-6]_[A-Za-z_]+$', sc.names[k])
        if not m_tag:
            fail('%s: not a name of this step (civ_<squad>_<1..6>_<what>)' % name(k)); continue
        seen_tags[top].add(m_tag.group(1))
    for top, tags in seen_tags.items():
        sq = sc.names[top]
        g = G.get(sq)
        N = squad_no(sc, sc.parent[g['actor']]) if g else None
        rows = []
        for tag in sorted(tags):
            n = {s: (res('%s%s%s%s%s' % (R_, sq, BS, tag, s)) or [None])[0] for s in
                 ('_1_Timer_go', '_2_Follow', '_3_Timer_shoot', '_4_Kill', '_5_Take', '_6_Timer_fed_up')}
            if None in n.values() or any(k not in mine for k in n.values()):
                fail('%s: the six nodes of %s are not all there' % (sq, tag)); continue
            nx = lambda k: [j for s in ctrl_all[k][1][4] for j in res(s)]
            a, b, e = nx(n['_1_Timer_go']), nx(n['_3_Timer_shoot']), nx(n['_6_Timer_fed_up'])
            if a != [n['_3_Timer_shoot'], n['_2_Follow']] or b != [n['_6_Timer_fed_up'], n['_4_Kill']]:
                fail('%s: %s: the timers do not name [the next timer, the rout] in that order (the chain follows the FIRST)' % (sq, tag))
            if len(e) != 1 or e[0] in (n['_2_Follow'], n['_4_Kill'], n['_5_Take']) or sc.top[e[0]] != top or \
                    not (e[0] in ctrl_all or (g and e[0] in g['ctrl'])) or (e[0] in mine and not sc.names[e[0]].endswith('_1_Timer_go')):
                fail('%s: %s: the last timer does not hand the chain on to a step of the build' % (sq, tag))
            ka = res(ctrl_all[n['_2_Follow']][1][4]); kb = res(ctrl_all[n['_5_Take']][1][4]); ks = res(ctrl_all[n['_4_Kill']][1][0])
            ca = civ_actor.get(ka[0]) if ka else None
            if not (ca and kb == [ca['node']] and ks == [ca['squad']]):
                fail('%s: %s: the three routs do not name one civilian (her actor, her money group) and her squad' % (sq, tag))
            # the chain as kl_fa_bots_dyn.graph walks it must pass the three timers in every branch set
            if g:
                for ci, sets in enumerate(g['sets']):
                    for si, ch in enumerate(sets):
                        ks_ = [x['k'] for x in ch]
                        if ci == 0:
                            want = [n['_1_Timer_go'], n['_3_Timer_shoot'], n['_6_Timer_fed_up']]
                            pos = [ks_.index(w) if w in ks_ else None for w in want]
                            if None in pos or pos != list(range(pos[0], pos[0] + 3)):
                                fail('%s: %s: branch set %d of the chain does not run through the three timers one after the other' % (sq, tag, si))
            secs = sum(ctrl_all[n[s]][1][0] for s in ('_1_Timer_go', '_3_Timer_shoot', '_6_Timer_fed_up'))
            c = civ_actor.get(ka[0]) if ka else None
            lead = [x for x, _h, _f, _s, hit in refs_in if x > 0 and n['_1_Timer_go'] in (hit or ()) and x not in mine]
            rows.append(collections.OrderedDict(civilian=c and c['path'], then=e and name(e[0]).split(BS)[-1],
                                                started_by=sorted({sc.names[x] for x in lead}), seconds=round(secs, 1)))
        facts['killers'][sq] = collections.OrderedDict(squad=N, role=D.PERS[N].role if N in D.PERS else None, civilians=rows)
        if N is not None and N not in KILLERS:
            note('%s (%s) kills: not one of the default roles %s' % (sq, D.PERS[N].role if N in D.PERS else '?', list(KILLERS)))
    # nobody else names a civilian
    for k, holder, field, s, hit in refs_in:
        if k > 0 and sc.names[sc.top[k]].startswith(F.SQUAD) and k not in mine and hit and any(h in civ_actor or h in civ_squad for h in hit):
            fail('%s (%s %s) names a civilian and is no node of this step' % (name(k), holder, field))
    served = {r['civilian'] for q in facts['killers'].values() for r in q['civilians']}
    for c in civs:
        if c['path'] not in served:
            note('%s (%d): no bot is sent to her; her money is the human\'s alone (field 11 keeps the bots\' loot TEST off it; the window '
                 'lines say what is left)' % (c['path'], c['amount']))
    # ---- the loot window of the squads that are NOT sent to her (the review's MUST 1; the task: 'the killer roles'
    # places are allowed, the others' are not'). kl_fa_bots.check says nothing here: its cannot_take answers '' for an
    # object with field 11 before it reaches the civilian rule. What the field leaves open is re/bots_loot.md 6: the
    # loot tactic's ACTION (kl2 0x7bc7d0) never reads it - while any OTHER candidate in a bot's window passes the test,
    # a bot whose nearest candidate is her money runs to her post and stands. So: every Defend place of every branch,
    # 800 / 400 (kl_fa_bots.LOOT_WINDOW) from her GROUP node, per squad; 'nearest of all' = the places at which her
    # money is the nearest money object with something left (the worst case: the action goes for the nearest).
    waived = bool(accept_window) if accept_window is not None else bool((rep.get('plan') or {}).get('options', {}).get('accept_window'))
    money = [o for o in F.money_objects(B) if o['amount'] > 0]
    sent = collections.defaultdict(set)                 # civilian path -> squad names with her steps
    for sq, q in facts['killers'].items():
        for r in q['civilians']:
            sent[r['civilian']].add(sq)
    facts['window'] = collections.OrderedDict()
    facts['window_waived'] = waived
    for c in civs:
        rows, cells_k, cells_o = collections.OrderedDict(), [], []
        for sq, g in G.items():
            pts = [p for p in squad_places(B, g).values() if F.in_window(p, c['post'])]
            if not pts:
                continue
            N = squad_no(sc, sc.parent[g['actor']])
            first = sum(1 for p in pts if min(money, key=lambda o: math.dist(o['at'], p))['node'] == c['node'])
            near = sum(1 for p in pts if math.dist(p, c['post']) <= WINDOW_NEAR)
            rows['%02d' % N] = collections.OrderedDict(killer=sq in sent[c['path']], places=len(pts), nearest=round(min(math.dist(p, c['post']) for p in pts)),
                                                        her_money_nearest_of_all_at=first, within_150=near)
            cell = '#%02d %d place(s), nearest %d%s' % (N, len(pts), rows['%02d' % N]['nearest'],
                                                        ', her money the nearest of all at %d' % first if first else '')
            (cells_k if sq in sent[c['path']] else cells_o).append(cell)
        facts['window'][c['path']] = rows
        if not c['flag'] or not cells_o:
            continue                                    # (without the field: the FAIL above already says it)
        text = ('%s (%d, field 11): squads that are NOT sent to her have Defend places inside the loot window (%d / %d) of her money: %s%s. '
                'Field 11 keeps the loot TEST off it (kl2 0x451a88); the loot ACTION does not read the field (0x7bc7d0): a bot whose nearest '
                'candidate is her post runs there and stands while anything else in its window is still to take - NARROWED, NOT CLOSED '
                '(re/bots_loot.md 6; the hold of runs L8 / L10). Whether a bot standing in her ball is PAID - which would end it - is not known'
                % (c['path'], c['amount'], F.LOOT_WINDOW[0], F.LOOT_WINDOW[1], '; '.join(cells_o),
                   ' (sent to her, allowed: %s)' % '; '.join(cells_k) if cells_k else ''))
        src_rec = (rep.get('money') or {}).get(c['path']) or {}
        if src_rec.get('put_back'):
            text += ('. THE SOURCE BUILD HAD THIS MONEY TAKEN OUT (kl_fa_bots option window: the form of the clean round W1_DM02); putting it '
                     'back re-opens what the field leaves of the trap')
        elif src_rec.get('field_11') == [0, 1]:
            text += ('. The source build carries this money WITHOUT the field (there every bot\'s own test takes it as loot): against it the '
                     'field is a gain')
        if waived:
            note('WAIVED by --accept-window - A TEST BUILD, NO CANDIDATE FOR THE OWNER\'S TAB before a run shows no bot within %d of her post for '
                 'more than 20 s with loot left: %s' % (WINDOW_NEAR, text))
        else:
            fail(text + '. (--accept-window makes this a NOTE for a test build)')
    if not civs:
        note('no civilian carries money in this build')
    bad = J.misfits(sc)
    if bad:
        fail('%d object(s) do not fit their class, e.g. %s: %s' % (len(bad), name(bad[0][0]), bad[0][2]))
    dang = [x for x in J.dangling(sc)[0] if x[0] in mine]
    if dang:
        fail('%d reference(s) of this step\'s nodes resolve to nothing, e.g. %s' % (len(dang), dang[0][3]))
    nf, nn = sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out)
    for s, t in out:
        log('%s  %s' % (s, t))
    for sq, q in facts['killers'].items():
        for r in q['civilians']:
            log('%s (%s): %s - started by %s, %.1f s of timers, then %s' % (sq, q['role'], r['civilian'], ', '.join(r['started_by']) or '?',
                                                                              r['seconds'], r['then']))
    log('RESULT (kl_fa_bots_civ): %s (%d FAIL, %d NOTE); %d civilian(s) with money, %d of them with a killer, %d killer squad(s), %d node(s) of this step'
        % ('PASS' if not nf else 'FAIL', nf, nn, len(civs), len(served), len(facts['killers']), len(mine)))
    return out, facts


# ------------------------------------------------------------------ the diff
def diff(src, dst, donor=None, log=print):
    """What the step changed -> list of UNEXPECTED differences. Expected and nothing else:
      members .prp .gms .buf .oct .rmi .rmc (none at all on a map without a money civilian);
      entities = the source's, in order, + nodes named civ_* directly below a bot squad's group;
      of the source's nodes only (a) nodes of a killer's squad in which reference strings that named ONE step now name
      a civ_.._1_Timer_go of the same squad, (b) a money civilian's group: OnlineMoneyCtrl field 11, and with a donor
      the two controllers put back, equal to the donor's;
      the files beside the archive byte for byte but the ones this step writes (civ.*, steps.json, graft.txt,
      bots.json when money was put back, audit.*)."""
    A, Bn = F.Built(src), F.Built(dst)
    sa, sb = A.sc, Bn.sc
    bad = []
    ext_of = {n: e for e, n in A.ext.items()}
    differ = sorted(ext_of.get(n, n) for n in A.order if A.files[n] != Bn.files.get(n))
    if A.order != Bn.order:
        bad.append('the archives do not hold the same members in the same order')
    extra = [e for e in differ if e not in ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc')]
    if extra:
        bad.append('members that may not differ do: %s' % extra)
    new = [k for k in range(1, len(sb.nodes)) if not sa.resolve(sb.path[k])]
    for k in new:
        if not (sb.names[k].startswith('civ_') and sb.names[sb.parent[k]].startswith(F.SQUAD + 'Squad#') and sb.parent[sb.parent[k]] == 0):
            bad.append('a new node that is no civ_ step of a squad: %s' % sb.path[k][5:])
    if [sb.path[k] for k in range(len(sb.nodes)) if k not in set(new)] != sa.path:
        bad.append('the source\'s entities are not all there in their order')
    civ_b = {c['node'] for c in civilians(Bn)}
    dsc = F.Built(donor).sc if donor else None
    changed, repointed, money = [], 0, []
    for k in range(1, len(sa.nodes)):
        hit = sb.resolve(sa.path[k])
        if len(hit) != 1:
            continue
        j, na, nb = hit[0], sa.nodes[k], sb.nodes[hit[0]]
        if sa.tids[k] != sb.tids[j] or J.text(sa, na['props']) != J.text(sb, nb['props']):
            bad.append('%s: class or properties differ' % sa.path[k][5:]); continue
        ta = [J.text(sa, [nm] + body) for nm, body in na['ctrls']]
        tb = [J.text(sb, [nm] + body) for nm, body in nb['ctrls']]
        if ta == tb:
            continue
        changed.append(k)
        if j in civ_b:
            ca = [sa.p.key(nm) for nm, _b in na['ctrls']]
            cb = [sb.p.key(nm) for nm, _b in nb['ctrls']]
            ok = True
            for i, (nm, body) in enumerate(nb['ctrls']):
                cn = sb.p.key(nm)
                if cn in ca and ta[ca.index(cn)] == tb[i]:
                    continue
                if cn == 'OnlineMoneyCtrl':
                    ref = na['ctrls'][ca.index(cn)] if cn in ca else None
                    rsc = sa
                    if ref is None and dsc is not None:
                        dk = dsc.resolve(sa.path[k])
                        ref = next((c for c in dsc.nodes[dk[0]]['ctrls'] if dsc.p.key(c[0]) == cn), None) if dk else None
                        rsc = dsc
                    if ref is None:
                        ok = False; continue
                    ua = [J.text(rsc, list(u)) for u in units(ref[1][1:-1])]
                    ub = [J.text(sb, list(u)) for u in units(body[1:-1])]
                    if len(ua) != len(ub) or [i2 for i2 in range(len(ua)) if ua[i2] != ub[i2]] not in ([11], []):
                        ok = False
                elif cn == 'TriggerBox2' and cn not in ca and dsc is not None:
                    dk = dsc.resolve(sa.path[k])
                    ref = [c for c in dsc.nodes[dk[0]]['ctrls'] if dsc.p.key(c[0]) == cn] if dk else []
                    if not any(J.text(dsc, [c[0]] + c[1]) == tb[i] for c in ref):
                        ok = False
                else:
                    ok = False
            if not ok or [c for c in cb if c in ca] != ca:
                bad.append('%s: a civilian\'s group differs by more than its money (controllers %s -> %s)' % (sa.path[k][5:], ca, cb))
            else:
                money.append(sa.path[k][5:])
            continue
        top = sb.top[j]
        if not sb.names[top].startswith(F.SQUAD + 'Squad#') or len(ta) != len(tb):
            bad.append('%s: controllers differ' % sa.path[k][5:]); continue
        # only whole path strings may differ, old = one step of this squad, new = a civ_.._1_Timer_go of it
        okn = True
        for (nm, ba), (nm2, bb) in zip(na['ctrls'], nb['ctrls']):
            if sa.p.key(nm) != sb.p.key(nm2) or len(ba) != len(bb):
                okn = False; break
            for (opa, pa), (opb, pb) in zip(ba, bb):
                if opa != opb:
                    okn = False; break
                if opa in J.KEYED:
                    s1, s2 = sa.p.key((opa, pa)), sb.p.key((opb, pb))
                    if s1 != s2:
                        t1, t2 = sa.resolve(s1), sb.resolve(s2)
                        if opa == 0x0c and t1 and t2 and sb.names[t2[0]].startswith('civ_') and sb.names[t2[0]].endswith('_1_Timer_go') \
                                and sb.top[t2[0]] == top and sa.top[t1[0]] == sa.top[k]:
                            repointed += 1
                        else:
                            okn = False
                elif pa != pb:
                    okn = False
        if not okn:
            bad.append('%s: its controllers differ by more than a step\'s name' % sa.path[k][5:])
    if J.text(sa, sa.p.settings) != J.text(sb, sb.p.settings):
        bad.append('.prp: the scene property block differs')
    skip = ('audit.', 'steps.json', 'graft.txt', os.path.basename(A.zp)) + SIDE_NEW
    side = [f for f in os.listdir(A.folder) if os.path.isfile(os.path.join(A.folder, f)) and not f.startswith(skip)]
    sdiff = [f for f in side if not os.path.isfile(os.path.join(Bn.folder, f)) or
             open(os.path.join(A.folder, f), 'rb').read() != open(os.path.join(Bn.folder, f), 'rb').read()]
    if 'bots.json' in sdiff and any(True for _ in money) and dsc is not None:
        sdiff.remove('bots.json')
    if sdiff:
        bad.append('files beside the archive differ: %s' % sdiff)
    log('members that differ: %s; %d new node(s), all civ_ steps below a squad\'s group; %d node(s) of the source differ: %d reference(s) in the '
        'killers\' squads re-pointed at a civ_.._1_Timer_go, the money of %d civilian(s) (%s); %d files beside the archive byte for byte'
        % (' '.join(differ) or 'NONE', len(new), len(changed), repointed, len(money), ', '.join(short(m) for m in money) or '-', len(side) - len(sdiff)))
    for x in bad:
        log('UNEXPECTED: ' + x)
    log('RESULT (diff): %s' % ('only the killers\' steps were added and the civilians\' money edited' if not bad else '%d UNEXPECTED difference(s)' % len(bad)))
    return bad


# ------------------------------------------------------------------ commands
def census(folder, log=print):
    B = F.Built(folder)
    sc = B.sc
    G = D.graph(B)
    log('==== %s' % folder)
    civs = civilians(B)
    bj = os.path.join(B.folder, 'bots.json')
    off = (json.load(open(bj)).get('plan', {}).get('edits') or {}).get('money_off') or {} if os.path.isfile(bj) else {}
    for p, d in off.items():
        log('  TAKEN OUT of this build by kl_fa_bots (option window): %s, %s at %s' % (p, d.get('amount'), d.get('at')))
    stops = {}
    for name, g in G.items():
        stops[squad_no(sc, sc.parent[g['actor']])] = loot_stops(B, g)
    for c in civs:
        v = next(v for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if k == c['node'])
        log('  %s  %d at (%d, %d, %d); field 11 %d; parts of %s every %.1f s; squad %s (%s, %d actor(s)); group flags %#x'
            % (c['path'], c['amount'], *c['post'], c['flag'], v[4], v[5], sc.names[c['squad']],
               'ZSquadScript' if c['squad_ok'] else 'NO ZSquadScript', len(c['members']), B.ents[c['node'] - 1].flags))
        near = []
        for N, ss in sorted(stops.items()):
            ds = [(math.dist(p, c['post']), sc.names[s['step']]) for s in ss for p in s['places'] if abs(p[1] - c['post'][1]) <= REACH[1]]
            if ds:
                near.append('#%02d %d (%s)' % (N, min(ds)[0], min(ds)[1]))
        log('      nearest loot place of each squad: %s' % (', '.join(near) or 'none within %d in height' % REACH[1]))
    log('  %d civilian(s) with money, %d; %d node(s) of this step in the build' % (len(civs), sum(c['amount'] for c in civs), len(my_nodes(sc))))


def build(src, dst, opt=None, log=print):
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    o = dict(DEFAULTS); o.update(opt or {})
    say('kl_fa_bots_civ build %s -> %s%s' % (src, dst, ' (donor %s)' % o['donor'] if o['donor'] else ''))
    B = F.Built(src)
    donor = F.Built(o['donor']) if o['donor'] else None
    if my_nodes(B.sc):
        raise ValueError('%s already has the steps of this module' % src)
    P = plan(B, o, donor, say)
    rep = apply(B, P, dst, donor, say)
    rep['plan'] = P
    with open(os.path.join(dst, 'civ.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    out, facts = check(dst, say)
    bad = diff(src, dst, o['donor'], say)
    out = out + [('FAIL', 'diff: ' + x) for x in bad]
    rep.update(check=[list(x) for x in out], facts=facts, diff=bad)
    with open(os.path.join(dst, 'civ.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    nf = sum(s == 'FAIL' for s, _t in out)
    say('RESULT (build): %s' % ('PASS' if not nf else 'FAIL (%d)' % nf))
    with open(os.path.join(dst, 'civ.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out, rep


def options(a):
    opt, i = {}, 0
    while i < len(a):
        x = a[i]
        if x in ('--donor', '--killers', '--count', '--reach', '--reach-height', '--go', '--rest', '--when'):
            v = a[i + 1]
            opt[x[2:].replace('-', '_')] = (v if x in ('--donor', '--when') else tuple(int(n) for n in v.split(',')) if x == '--killers'
                                            else int(v) if x == '--count' else float(v))
            del a[i:i + 2]
        elif x == '--no-flag':
            opt['flag'] = False
            del a[i]
        elif x == '--accept-window':
            opt['accept_window'] = True
            del a[i]
        else:
            i += 1
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) >= 2 and a[0] == 'census':
        for f in a[1:]:
            census(f)
    elif len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'check':
        out, _f = check(a[1], accept_window=True if opt.get('accept_window') else None)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if diff(a[1], a[2], opt.get('donor')) else 0)
    elif len(a) >= 2 and a[0] == 'owner':
        res = {}
        for sub, d, don in OWNER:
            if a[2:] and d not in a[2:]:
                continue
            print('==== %s' % d)
            o = dict(opt)
            if don:
                o['donor'] = os.path.join(a[1], *don)
            out, _rep = build(os.path.join(a[1], sub, d), os.path.join(a[1], 'z_civ', d), o)
            res[d] = not any(s == 'FAIL' for s, _t in out)
        for k, v in res.items():
            print('%s: %s' % (k, 'PASS' if v else 'FAIL'))
        sys.exit(0 if res and all(res.values()) else 1)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
