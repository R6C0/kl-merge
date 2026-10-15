#!/usr/bin/env python3
"""
The AI heisters rappel WITH you on Retomoto (2026-10-14, the owner: 'making the ai heisters or anyone who starts there getting to rappel at
the same time'). An addition to a build that already has kl_fa_rappel.py's cut for the human (ROOT\\KL_Rappel!).

    python kl_fa_rappel_bots.py add <build folder or _Main.zip> <out folder> [--slot F06] [--x 6090] [--mode unbreakable-vulnerable]
                                    [--start-bots 18]   (Timer_start_bots, s after the round start; 0 = leave it)
    python kl_fa_rappel_bots.py check <build folder> [--slot F06]

WHAT add DOES (L07's own form for NPCs, re/rappel.md 2 and 3A): INSIDE each AI heister's own squad Gameplay!merc_bot_squad!Squad#0N
(N = 2 .. 8; L07 keeps its rappel rout in the squad of the soldier it moves) ONE MiniCutsceneRout KL_Rappel whose head is `Actor| Glazer_Bodyguard_0N` (the bot's actor
group, as L07's `Actor| Soldier_SnowWolf_01`) and ONE act: the same clip as the human's (Repelling_01, 17.6 m, 4.2 s) from a PosObject 17.6 m
over the bot's landing. The landings are on the balcony beside the human's (x = --x, the bot's own START z, the two bots that share a z moved
apart), so the clip's early 1.6 m push away from the wall does not start a bot inside the glass (the START rows stand 58 .. 218 from it).
The existing Rappel_Timer (2.0 s after the round-start event) gets the seven routs on its list, so everybody drops at once.
Nothing else changes: the .ANM already has the clips in the crew's sets (kl_fa_rappel.py apply), the bots' own chains start later
(Timer_start_bots), KLJoin.ini and KLTalk.ini are copied unchanged.
LIVE 2026-10-14 (v62_RPB, then the owner's own round): the first form - the routs in squads of their own (KL_RappelBots! / Rappel_Bot_0N) -
did NOTHING: the bots stood on the balcony and only the human dropped (a squad without the actor cannot drive it). Hence the rout now
goes into the bot's own squad. Still NOT KNOWN until a live run: whether a crew bot plays the act in the pre-round.
"""
import collections, json, os, shutil, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_rappel as R

ROUT = 'KL_Rappel'
POS_FMT = 'PosObject_Bot_%02d'
BOTS = 'Gameplay!merc_bot_squad!Squad#%02d'
ACTOR = 'Glazer_Bodyguard_%02d'
MODE = 'unbreakable-vulnerable'
LAND_X = 6090.0                       # the human lands at 6100 (floor to 6150, re/rappel.md 8.3); the START rows stand at x 5918 .. 6078
FACE = (-1.0, 0.0)
START_BOTS = 'Gameplay!merc_bot_squad!Timer_start_bots'
# THE STREET WITHOUT YOU (2026-10-14, the owner: 'the ai heisters still sit there at the bottom of the tower ... they should be able to do it').
# The crew's street route (each squad's 050_DefendBehaviour_street) is started ONLY by the lobby car's jump point, i.e. when the HUMAN
# takes the car (Specials!JumpPoints!06_Exit's list). klhop.c ([CrewHop] in KLJoin.ini) now brings a bot down by itself to the car
# door downstairs, where it stood. This adds a ZTriggerBox2 there (F08's loot box form, radius mode): any player or AI heister inside it
# sends 'AITrigger' to the seven street routs - the same message the jump point sends (re/club_campaign.md W: TriggerBox2 sends to its
# field-0 list; a DefendBehaviourRout started once ignores the copies, field 8 = 1). Fires every tick a visitor is inside: harmless.
# THE HAND-OVER (2026-10-14, live: the bots landed and then STOOD on the balcony / inside the glass, their order the landing place, long
# after Timer_start_bots): the rout had an empty out-link list, so the squad's goal stayed the cutscene and the AITrigger of the squad's first
# step (Counter_room_clear -> 010_DefendBehaviour_to_loot) found the goal busy. L07's own rappel routs name the next step in that list
# (re/rappel.md 2: 'the rout's reference list (out-link) hands the squad on ... when the clip ends'). Now each bot's rout names its squad's
# first step, so the squad walks on the moment the bot is down.
FIRST_STEP = '010_DefendBehaviour_to_loot'
STREET_GO = 'KL_StreetGo'
STREET_DONOR = ('F08', 'ROOT\\Locations/F08/F08_Locations.zip\\Locations/F08/F08_LOC_Inside.zip\\F08_ServerRoom_Main_1stFloor\\PC0001_F08_LootUnit_75\\Triggerbox_OpenLoot')
STREET_AT = (5900.0, 600.0, -6365.0)  # the middle of the [CrewJoin] / [CrewHop] landing places in front of the lobby car's door
STREET_R = 450.0
STREET_ROUT = '050_DefendBehaviour_street'
START_AFTER = 18.0                    # s after the round-start event: the blast is at 16.5, the drop ends at 6.2 (was 91.5: the crew stood a minute
                                      # and a half on the balcony unless the boardroom's squads died first)


def script_for(actor, slot, posname, mode=MODE):
    act = '(act| ((subt| 1)| (anim| %s)| (lefthandik| 0)| (startpos| %s)| (blend| 1)| (_dep| ())))' % (slot, posname)
    return '((Actor| %s| (%s))| (Options| Options| ((mode| %s))))' % (actor, act, mode)


def bot_landings(B, sc, x=LAND_X, human_z=-100.0):
    """[(n, actor name, landing)] for the crew squads the build has; the landing z = the actor's place z, moved off the human's
    and off each other (at least 110 apart)."""
    out = []
    for n in range(1, 20):
        a = sc.resolve(R_ + (BOTS % n) + '\\' + (ACTOR % n))
        if len(a) != 1:
            continue
        g = sc.resolve(R_ + (BOTS % n) + '\\' + (ACTOR % n) + '\\ground')
        at = B.at(g[0] if len(g) == 1 else a[0])
        out.append([n, sc.names[a[0]], [x, at[1], at[2]]])
    used = [human_z]
    for b in sorted(out, key=lambda b: b[2][2]):
        z = b[2][2]
        while any(abs(z - u) < 110.0 for u in used):
            z += 120.0 if z >= -100.0 else -120.0
        b[2][2] = z
        used.append(z)
    return out


R_ = 'ROOT\\'


def join_under(J, base, under, label='join'):
    """kl_prpjoin.join(base, its own tops) with extra subtrees put INSIDE existing nodes: under = {base node index: [(scene, top), ...]},
    each added as the LAST children of that node (after its own subtree), in preorder like everything else; origin as join's."""
    out = J.join(base, [(base, t) for t in base.tops()], label)
    p = out.p
    kids = {}
    for k in range(1, len(base.nodes)):
        kids.setdefault(base.parent[k], []).append(k)
    table = {s: i for i, s in enumerate(p.keys)}
    order = list(p.keys)
    names, tids, origin = ['ROOT'], [base.tids[0]], [(base, 0)]

    def copy(sc, k):
        n, keys = sc.nodes[k], sc.p.keys
        props = J._intern(n['props'], keys, table, order)
        ctrls = [(J._intern([nm], keys, table, order)[0], J._intern(body, keys, table, order)) for nm, body in n['ctrls']]
        return {'props': props, 'ctrls': ctrls, 'children': []}

    def emit(sc, k, into, sub):
        d = copy(sc, k)
        into['children'].append(d)
        names.append(sc.names[k]); tids.append(sc.tids[k]); origin.append((sc, k))
        for c in sub.get(k, []):
            emit(sc, c, d, sub)
        if sc is base:
            for xs, xt in under.get(k, []):
                xk = {}
                for j in range(xt + 1, xs.end[xt]):
                    xk.setdefault(xs.parent[j], []).append(j)
                emit(xs, xt, d, xk)
    root = copy(base, 0)
    for t in kids.get(0, []):
        emit(base, t, root, kids)
    if order[:len(p.keys)] != list(p.keys):
        raise ValueError('the key table changed order')
    p.root = root
    p.keys, p.nkeys = order, len(order) - 1
    p.keyblob = b''.join(s.encode('latin1') + b'\0' for s in order)
    new = J.Scene(p, names, tids, base.game, label)
    new.origin = origin
    return new


def add(src, dst, slot='F06', x=LAND_X, mode=MODE, log=print, start_bots=START_AFTER, street=True):
    import kl_fa, kl_gms, kl_graft
    import kl_prpjoin as J
    import kl_octree as O
    import kl_fa_bots as F
    import kl_fa_cover as CV
    import kl_fa_climb2 as C2
    import kl_anm
    B = F.Built(src, slot)
    zp = B.zp
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty' % dst)
    sc = B.sc
    if not sc.resolve(R_ + R.GROUP + '\\' + R.TIMER):
        raise ValueError('the build has no %s\\%s: run kl_fa_rappel.py build first' % (R.GROUP, R.TIMER))
    if any(sc.resolve(R_ + (BOTS % n) + '\\' + ROUT) for n in range(1, 20)):
        raise ValueError('the build already has bot rappel routs')
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)
    say('kl_fa_rappel_bots add: %s -> %s' % (zp, dst))
    an, _sn = R._anm_snd(B.order)
    a = kl_anm.Anm(B.files[an])
    frames, net, _prof = R.profile(a)
    wnet = R.world_net(net, FACE)
    bots = bot_landings(B, sc, x)
    if not bots:
        raise ValueError('no crew squad %s with an actor %s' % (BOTS, ACTOR))
    for b in bots:
        b.append(tuple(b[2][i] - wnet[i] for i in range(3)))
        say('  bot %d %s: lands (%.0f, %.0f, %.0f), PosObject (%.0f, %.0f, %.0f)' % (b[0], b[1], b[2][0], b[2][1], b[2][2], b[3][0], b[3][1], b[3][2]))
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0]:
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    M = F.Maker()
    made, routs, tops = [], [], []
    for n, actor, land, start in bots:
        ro = M.clone(*C2.DONOR['rout'], name=ROUT)
        M.place(ro, (0.0, 0.0, 0.0))
        po = ro.add(M.clone(*C2.DONOR['pos'], name=POS_FMT % n))
        M.place(po, start, F.rot9(-FACE[0], -FACE[1]))
        nxt_step = R_ + (BOTS % n) + '\\' + FIRST_STEP
        if len(sc.resolve(nxt_step)) != 1:
            raise ValueError('no first step %s' % nxt_step)
        M.set(ro, 'MiniCutsceneRout', {0: script_for(actor, R.SLOT, POS_FMT % n, mode), 1: [nxt_step]})
        M.set(po, 'MiniCutPosObject', {0: ''})
        made += [ro, po]
        tops.append((n, ro))
        routs.append(R_ + (BOTS % n) + '\\' + ROUT)
    for nd in made:
        if nd.links is not None or nd.model:
            raise ValueError('%s: a donor with a list or a model' % nd.name)
    tb = None
    if street:
        st = [R_ + (BOTS % n) + '\\' + STREET_ROUT for n, _ro in tops]
        miss = [p_ for p_ in st if len(sc.resolve(p_)) != 1]
        if miss:
            raise ValueError('no street rout %s' % miss[:2])
        tb = M.clone(*STREET_DONOR, name=STREET_GO)
        M.place(tb, STREET_AT)
        M.set(tb, 'TriggerBox2', {0: st, 1: 1, 2: STREET_R, 5: 'AITrigger'})
        made.append(tb)
    q, order = M.scene([ro for _n, ro in tops] + ([tb] if tb else []))
    qt = q.tops()
    if len(qt) != len(tops) + (1 if tb else 0):
        raise ValueError('the made scene has %d tops for %d routs' % (len(qt), len(tops)))
    under = {}
    for (n, _ro), t in zip(tops, qt):
        k = sc.resolve(R_ + (BOTS % n))
        if len(k) != 1:
            raise ValueError('%s is not one node' % (BOTS % n))
        under[k[0]] = [(q, t)]
    if tb:
        under[sc.resolve(R_ + (BOTS % tops[0][0]))[0]].append((q, qt[-1]))
    Jn = join_under(J, sc, under, 'rappel_bots')
    tm = Jn.resolve(R_ + R.GROUP + '\\' + R.TIMER)
    if len(tm) != 1:
        raise ValueError('the timer is not one node')
    ti = next(i for i, (nm, _b) in enumerate(Jn.nodes[tm[0]]['ctrls']) if Jn.p.key(nm) == 'TriggerDelay2')
    seen = {}

    def fn(us):
        have = [Jn.p.key(t) for t in us[4][1:]]
        seen['before'] = list(have)
        us[4] = kl_fa._refs(Jn, have + [r for r in routs if r.lower() not in [h.lower() for h in have]])
    kl_fa.edit(Jn, tm[0], ti, fn)
    say('  %s: its list had %s; the %d bot routs added' % (R.TIMER, seen.get('before'), len(routs)))
    if start_bots:
        sb = Jn.resolve(R_ + START_BOTS)
        if len(sb) != 1:
            raise ValueError('%s is not one node' % START_BOTS)
        si = next(i for i, (nm, _b) in enumerate(Jn.nodes[sb[0]]['ctrls']) if Jn.p.key(nm) == 'TriggerDelay2')
        was = {}

        def fs(us):
            was['s'] = struct.unpack('<f', us[0][0][1])[0]
            us[0] = [(0x0a, struct.pack('<f', float(start_bots)))]
        kl_fa.edit(Jn, sb[0], si, fs)
        say('  %s: %.1f s -> %.1f s after the round start (the crew moves off the balcony once it has landed and the blast is over;'
            ' owner: the bots \'afk at the bottom\')' % (START_BOTS, was['s'], start_bots))
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, ents_made = nxt, {}
    ents0 = list(A.entities())
    for n, ro in tops:
        k = sc.resolve(R_ + (BOTS % n))[0]
        if ents0[k - 1].name.decode('latin1') != sc.names[k]:
            raise ValueError('the .gms entity of %s is not where the .prp has it' % sc.names[k])
        nxt = C2._write_ent(A, ro, ents0[k - 1], nxt, ents_made)
        if tb and n == tops[0][0]:
            nxt = C2._write_ent(A, tb, ents0[k - 1], nxt, ents_made)
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
    moved = sum(1 for k, v in ids.items() if k != v)
    items = []
    for (n, nd), b in zip(tops, bots):
        p = b[3]
        lo = (p[0] - 10.0, p[1] - 10.0, -700.0)
        hi = (p[0] + 10.0, p[1] + 190.0, 700.0)
        items.append((slot1[ents_made[id(nd)]] + 2, lo, hi))
    # the trigger box is no octree item: a ZBoxPrimitive is of the category room set check refuses in that tree, and the level's own
    # timer boxes (Timer_start_bots, F07's form) are in none either
    root3 = octn.rooms[0][3]
    repointed = 0
    new_prm = None
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        octn.rooms[0][3].check()
        move = {k: v for k, v in zip(octx.record_refs(), octn.record_refs()) if k != v}
        if move:
            pm = bytearray(B['.prm'])
            t, n = struct.unpack_from('<II', pm, 0)
            old = set(octx.record_refs())
            for i in range(1, n):
                o, size = struct.unpack_from('<II', pm, t + 16 * i)
                if size == 64 and pm[o:o + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', pm, o + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', pm, o + 0x1c, move[v]); repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(pm)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, nm in B.ext.items() if new[nm] != B.files[nm])
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(nm, new[nm]) for nm in B.order])
    for fx in os.listdir(B.folder):
        pth = os.path.join(B.folder, fx)
        if os.path.isfile(pth) and pth != zp:
            shutil.copyfile(pth, os.path.join(dst, fx))
    say('written %s: %d entities added, REF ids %d..%d; members changed: %s; %d slot ids renumbered; %d model roots of the .prm re-pointed' % (
        out, len(order), ref0, nxt - 1, ' '.join(changed), moved, repointed))
    for e in ('.ANM', '.fxc', '.WAV'):
        if e in B.ext and new[B.ext[e]] != B.files[B.ext[e]]:
            raise ValueError('%s changed' % e)
    res = check(dst, slot, log=say)
    rep = collections.OrderedDict(source=B.folder, out=dst, bots=[[b[0], b[1], list(b[2]), list(b[3])] for b in bots], routs=routs,
                                  members_changed=changed, check=[list(r) for r in res])
    with open(os.path.join(dst, 'rappel_bots.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    with open(os.path.join(dst, 'rappel_bots.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return rep


def check(folder, slot='F06', log=print):
    import kl_fa
    import kl_fa_bots as F
    out = []

    def say(s, t):
        out.append((s, t))
        log('  %-4s %s' % (s, t))
    B = F.Built(folder, slot)
    sc = B.sc
    tm = sc.resolve(R_ + R.GROUP + '\\' + R.TIMER)
    tv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if tm and k == tm[0]]
    lst = [str(x).lower() for x in (tv[0][4] if tv else [])]
    n = 0
    for k in range(1, 20):
        ro = sc.resolve(R_ + (BOTS % k) + '\\' + ROUT)
        if not ro:
            continue
        n += 1
        po = sc.resolve(R_ + (BOTS % k) + '\\' + ROUT + '\\' + (POS_FMT % k))
        ctl = {sc.p.key(nm): [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])] for nm, body in sc.nodes[ro[0]]['ctrls']}
        script = ctl.get('MiniCutsceneRout', [''])[0]
        actor = sc.resolve(R_ + (BOTS % k) + '\\' + (ACTOR % k))
        okp = len(po) == 1
        say('PASS' if okp and actor and ('Actor| %s|' % (ACTOR % k)).lower() in script.lower() else 'FAIL',
            'bot %d: rout + PosObject %s, the head names %s (%s in the build)' % (k, 'there' if okp else 'MISSING', ACTOR % k, 'there' if actor else 'NOT'))
        if okp:
            p = B.at(po[0])
            say('PASS' if p[0] > 5880.0 else 'FAIL', 'bot %d: the drop starts at (%.0f, %.0f, %.0f), outside the glass (x 5860)' % (k, p[0], p[1], p[2]))
        path = (R_ + (BOTS % k) + '\\' + ROUT).lower()
        say('PASS' if path in lst else 'FAIL', 'bot %d: the timer names its rout' % k)
        outl = [str(x).lower() for x in (ctl.get('MiniCutsceneRout', ['', []])[1] or [])]
        say('PASS' if any(FIRST_STEP.lower() in x for x in outl) else 'FAIL', 'bot %d: the rout hands the squad on to %s (%s)' % (k, FIRST_STEP, outl))
    sg = [k for k in range(len(sc.nodes)) if sc.names[k] == STREET_GO]
    if sg:
        tv2 = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerBox2') if k == sg[0]]
        ok = bool(tv2) and str(tv2[0][5]) == 'AITrigger' and len(tv2[0][0]) == n and all(STREET_ROUT.lower() in str(t).lower() for t in tv2[0][0])
        say('PASS' if ok else 'FAIL', 'the street trigger %s at %s sends %s to %d street rout(s)' % (STREET_GO, tuple(round(c) for c in B.at(sg[0])), tv2[0][5] if tv2 else '?', len(tv2[0][0]) if tv2 else 0))
    else:
        say('NOTE', 'no street trigger (built with --no-street)')
    human = (R_ + R.GROUP + '\\' + R.SQUAD + '\\' + R.ROUT).lower()
    say('PASS' if human in lst else 'FAIL', 'the timer still names the human\'s rout (%d entries)' % len(lst))
    say('PASS' if n else 'FAIL', '%d bot routs' % n)
    nf = sum(s == 'FAIL' for s, _t in out)
    log('RESULT (kl_fa_rappel_bots): %s (%d FAIL)' % ('PASS' if not nf else 'FAIL', nf))
    return out


def main():
    a = sys.argv[1:]
    slot, x, mode, start = 'F06', LAND_X, MODE, START_AFTER
    opts = a[3:] if a[:1] == ['add'] else a[2:]
    i = 0
    while i < len(opts):
        if opts[i] == '--slot':
            slot = opts[i + 1]; i += 2
        elif opts[i] == '--x':
            x = float(opts[i + 1]); i += 2
        elif opts[i] == '--mode':
            mode = opts[i + 1]; i += 2
        elif opts[i] == '--start-bots':
            start = float(opts[i + 1]); i += 2
        else:
            sys.exit(__doc__)
    if len(a) >= 3 and a[0] == 'add':
        try:
            rep = add(a[1], a[2], slot, x, mode, start_bots=start)
        except (ValueError, KeyError) as e:
            sys.exit('kl_fa_rappel_bots: NOT built: %s' % (e.args[0] if e.args else e))
        sys.exit(1 if any(s == 'FAIL' for s, _t in rep['check']) else 0)
    elif len(a) >= 2 and a[0] == 'check':
        sys.exit(1 if any(s == 'FAIL' for s, _t in check(a[1], slot)) else 0)
    sys.exit(__doc__)


if __name__ == '__main__':
    main()
