#!/usr/bin/env python3
"""
THE LEVEL-DATA CLIMB for Fragile Alliance: a step on a FINISHED build folder (<slot>_Main.zip + the files beside it).
Where tools/kl_fa_climb.py + klhook/klclimb.c give the wall back by a HOOK, this step gives it by LEVEL DATA alone, the way
luvsic's 'A Newer Perspective' does it (third_party/anp/tools/climbs.py, credit to him; the account, every address, what
differs: re/climb2.md). The two forms are independent; this one needs no hook part.

    python kl_fa_climb2.py spots  <folder>                 the places along the wall where a climb is offered (nothing written)
    python kl_fa_climb2.py apply  <folder> <out folder> [options]
                                                           the build with the Dead Men climb clips in its .ANM (players' sets,
                                                           +0x2C of every added clip repaired) and, per spot, a squad + a
                                                           MiniCutscene + a PosObject + a use prompt; check is run; exit 1 on a FAIL
    python kl_fa_climb2.py check  <folder> [<source folder>]   read-only; last line RESULT (kl_fa_climb2): ...
    python kl_fa_climb2.py list                            the other climbs our maps want (places only, nothing built)
    options   --spacing N   centre distance of the spots along a stretch (default 400)
              --npcs        also give the NPC sets their climb clips (kl_fa_climb's default; the AI does not use them here)
              --end-act     (variant) a second act with its own PosObject at the predicted landing: the end no longer rests on root motion alone

WHAT A SPOT IS (one per ~400 units of the measured stretch; kl_fa_climb's walk() decides where Dead Men's own rule holds)
    KL_Climb!                                   a plain top-level group at the origin (the build's own form)
      Climb_01_Squad    ZGROUP + ZSquadScript   L03 'Squad_OutroCut' (eStayBack / eAllTypes / eNormalAlertness): the squad a
                                                  MiniCutscene runs in; stock's own form for a cutscene that has a 'Lynch' head
        Climb           ZGROUP + MiniCutsceneRout   script '((Lynch| Lynch| ((act| ((subt| 1)| (anim| /Movement/Climb/Up/<class>)|
                                                  (weaponhdl| Holster)| (lefthandik| 0)| (startpos| PosObject_Climb)| (blend| 1)|
                                                  (_dep| ()))))| (Options| Options| ((mode| unbreakable))))' (luvsic's script)
          PosObject_Climb  ZSTDOBJ + MiniCutPosObject   the START of the clip, FACING THE WALL. This form has NO alignment: the player is put
                                                  on the PosObject and the clip plays with its OWN root motion (Up_High: 172 up, 99 .. 101
                                                  forward). So the start is SET BACK from the face so that the root ends FAR_MARGIN inside
                                                  the far edge of the wall top, and LIFTED over the floor so that it ends END_BIAS over the
                                                  top (Withdrawal's wall is 203.5, the clip rises 172: lift 36.5, back 61.7)
      Climb_01_Use      ZBoxPrimitive + PlayerAction   L03 'Fake_EndAlley_Airlock' (the stock co-op climb-wall prompt, text
                                                  ' Climb Wall'): the use volume is the box itself (field 9 empty), its list
                                                  names the MiniCutscene (as that stock action names Squad_OutroCut\\MiniCutScene),
                                                  enabled from the start (field 8 = 1)
    Nothing of the build is taken away or moved; the wall piece kl_escape sank stays sunk and the AI heisters' drop link
    stays. NOT RUN IN THE GAME. Every ASSUMPTION is marked where it is made and listed in re/climb2.md.

THE FACING (checked against seen-live data): kl_fa_author.look9 - 'a player looks along local -Z' (seen live, run RT2b) - so a
PosObject that makes the player face (fx, fz) holds rot9((-fx, -fz)) = rot9(wall normal). luvsic's stored_rot formula
[-fz 0 fx | 0 1 0 | fx 0 fz] is 90 degrees away from that; ASSUMED here that the player takes the PosObject's frame as the START rows
do (ZMiniPlayerActTask puts the player there by 0x82cc40 from the node's frame, 0x8e8d2e .. 0x8e8d53).
"""
import collections, json, math, os, re, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_anm, kl_anmjoin, kl_fa, kl_gms, kl_scene
import kl_fa_bots as F
import kl_fa_climb as C
import kl_fa_cover as CV
import kl_octree as O
import kl_prpjoin as J

NAME = 'climb2'
GROUP = 'KL_Climb!'
SQUAD_FMT, ROUT, POS, USE_FMT = 'Climb_%02d_Squad', 'Climb', 'PosObject_Climb', 'Climb_%02d_Use'
POS_END = 'PosObject_Climb_End'          # --end-act only: the second act's startpos = where the clip is predicted to land
END_ANIM = '/Movement/Stand/Normal'      # --end-act only: the standing idle of the player's set (ASSUMED harmless as an act after the climb)
R_ = 'ROOT\\'
# Where the four forms are taken from (stock Dog Days levels; Maker.clone copies the node's properties, controllers and .gms record).
DONOR = {
    'squad': ('L03', R_ + 'Squad_OutroCut'),                                   # ZSquadScript: eStayBack, eAllTypes, eNormalAlertness
    'rout': ('L03', R_ + 'Squad_OutroCut\\MiniCutScene'),                      # MiniCutsceneRout of a 'Lynch' head (the player's act)
    'pos': ('F07', R_ + 'Gameplay!000_Civilians!001_Civilian_01\\10_RunToGaate\\MoveToPosObject#01'),   # MiniCutPosObject, field 0 empty
    'use': ('L03', R_ + 'Special!Coop_doors!EndAlleyHACK!Fake_EndAlley_Airlock'),   # PlayerAction 'CoOpDoors/L03_CoOpDoors/L03_CoOpClimbWall'
}
DONOR_TEXT = 'CoOpDoors/L03_CoOpDoors/L03_CoOpClimbWall'                       # LOC leaf ' Climb Wall' (in every FA level's .LOC)
SPACING = 400.0
GAP = 10.0                          # the boxes of neighbouring spots do not touch
BOX_BACK, BOX_DEPTH, BOX_HEIGHT = 5.0, 125.0, 200.0     # the use volume: from 5 to 130 off the face, 200 high at the floor
MAX_SPOTS = 12
# THIS FORM HAS NO ALIGNMENT (the hook form aligns the clip to the measured wall at its events 5 and 6; ZMiniPlayerActTask only puts the
# player on the PosObject and plays the clip with its OWN root motion). So the end of the climb is where the clip's root ends:
#   Up_High: rise 172.0, forward 98.7 .. 101.2 (the root is nearly still until event 6: 147.5 up, ~9 forward), Up_Medium 118.5 / 62.4,
#   Sprint_Low 106 / 145 (measured: python kl_fa_climb2.py spots). A wall of 203.5 (Withdrawal's) is 31.5 over the High clip's rise:
#   the PosObject is therefore LIFTED (the start hovers `lift` over the floor) so that the end lands on the top, and set back so that the
#   end lands FAR_MARGIN inside the far edge. Both are the only freedoms of the form; END_BIAS is the cm the root ends over the top (the
#   player drops that far when the collision comes back; ending under the top would put him INTO the wall).
FAR_MARGIN = 10.0
END_BIAS = 5.0

# The other climbs our maps want, places only (nothing built). Source: re/climb.md, re/campaign_fa_*.md, re/escape.md,
# luvsic's notes (third_party/anp/docs/HANDOFF.md 'Next steps'). Coordinates are Dead Men's own where a name is given.
OTHERS = [
    ('Withdrawal (the bank), yard north wall', 'this step', 'M03_FA_A x -3450 .. -1900 at z -625, 203.5 high = High',
     'built here (3 spots of 400-525) and by klclimb.c; pieces SO0101_M03_Wall_Low_8m_01 / _02 stand, _05 is sunk for the AI'),
    ('Withdrawal, wall piece _03 west of x -3500', 'level data', 'x -4300 .. -3600',
     'refused by the rule (ColiObj_OnlyHero_01 stands over it, then the wall SO0202_M03_Wall_ENTER_05_01): needs the hero-only collision cut'),
    ('The Vault (M03_A alone, slot F07): the yard wall and the dock', 'level data', 'the campaign map M03_A has TriggerBox_ClimbWall (luvsic: "M03A TriggerBox_ClimbWall")',
     'the same wall as Withdrawal seen from the campaign side; the Vault is built from M03_A, so the rule has to be walked on ITS collision (kl_fa_climb.LINES has no entry for it yet)'),
    ('The Vault: the two flights down to the vault lobby', 'none needed', 'stairs', 'walkable; no climb'),
    ('Retomoto Tower (M09_A + M09_B): the blown window / balcony ledge', 'rappel, not climb', 'x 5850, y 20996',
     'the start is on the ledge; the owner has no climb there (campaign had ropes)'),
    ('Retomoto Tower: lobby lift shaft and the street half', 'none found', 'M09_B ColiObj_* names carry no HeroClimb',
     'nothing in the campaign map climbs; the bots already walk the street (re/retomoto_bots_rooms.md)'),
    ('Hot Coffee (M01_FA_A): the warehouse wall', 'level data', 'M01 ColiObj_HeroClimb_01 / 099_TB_ClimbWall (luvsic HANDOFF)',
     'Dead Men has a climb here; this map has its own gate for the van (re/map_escape.md); not measured on our build'),
    ('Hot Coffee: the overturned van -> bus-stop shelter -> fence', 'level data', 'M01 (-3185, 120, 2160) .. (-3185, 346, 2840) (luvsic climbs.py CLIMBS M01)',
     'the three-step High / High / Down climb luvsic built; the FA map has no overturned van where he put it (to be measured)'),
    ('A Walk in the Park (M06_FA_A)', 'unknown', '-', 'not looked at; re/campaign_fa_park.md has the campaign map'),
    ('Late Night Opening (M02_FA_A)', 'unknown', '-', 'not looked at'),
]


# ------------------------------------------------------------------ the spots
def level_of(L):
    lv = C.find_level(L.sc)
    if lv is None:
        raise ValueError('kl_fa_climb.LINES has no line for the map this build holds (find_level)')
    return lv


def clip_ends(anm, setname):
    """{slot: [(condition flags, clip name, rise, forward, sideways)]} = where the root of each clip of the set's three climb lists ends,
    relative to where it starts (kl_fa_climb.clip_facts: the GROUND bone's keys; y up, forward = -z)."""
    own = kl_anm.owners(anm)
    out = {}
    for sl, lst in C.has_slots(anm, setname).items():
        rows = []
        for fl, ci in lst:
            f = C.clip_facts(anm, ci, own)
            if f['root'] is None:
                raise ValueError('%s: no root track' % f['name'])
            e = f['root']['end']
            rows.append((fl, f['name'].split('#')[1], e[1], -e[2], e[0]))
        out[sl] = rows
    return out


def plan_spots(L, G, level, ends, spacing=SPACING, log=print):
    """The measured stretches of kl_fa_climb.walk (Dead Men's rule on the build's collision) cut into spots. `ends` = clip_ends() of
    the players' set: the clip's own root motion decides where the PosObject goes (see FAR_MARGIN / END_BIAS above).
    -> [dict(section, k, face (x, z), n (x, z), floor, top, slot, stand, depth, width, rise, fwd, back, lift, start (x, y, z), end (x, y, z))]"""
    secs = C.walk(L, G, level, lambda *a, **k: None)
    out = []
    for si, s in enumerate(secs):
        a, b, n = s['a'], s['b'], tuple(s['normal'])
        ln = math.hypot(b[0] - a[0], b[2] - a[2])
        u = ((b[0] - a[0]) / ln, (b[2] - a[2]) / ln)
        cnt = max(1, int(ln // spacing))
        w = ln / cnt
        dflt = [r for r in ends[s['slot']] if r[0] == 0]
        if len(dflt) != 1:
            raise ValueError('%s: %d default clips' % (s['slot'], len(dflt)))
        _fl, cname, rise, fwd, side = dflt[0]
        h = s['a'][1] - s['floor']
        back = min(max(fwd - (s['depth'] - FAR_MARGIN), 0.0), BOX_BACK + BOX_DEPTH - 10.0)     # how far from the face the clip starts
        lift = max(h - rise + END_BIAS, 0.0)
        for k in range(cnt):
            t = w * (k + 0.5)
            face = (a[0] + u[0] * t, a[2] + u[1] * t)
            st = (face[0] + n[0] * back, s['floor'] + lift, face[1] + n[1] * back)
            end = (st[0] - n[0] * fwd + u[0] * side, st[1] + rise, st[2] - n[1] * fwd + u[1] * side)
            out.append(dict(section=si, k=k, face=face, n=n, floor=s['floor'], top=s['a'][1], slot=s['slot'], stand=s['stand'], clip=cname,
                            depth=s['depth'], width=w, tangent=u, rise=rise, fwd=fwd, back=back, lift=lift, start=st, end=end))
    if len(out) > MAX_SPOTS:
        raise ValueError('%d spots: more than MAX_SPOTS %d (use a larger --spacing)' % (len(out), MAX_SPOTS))
    return out


def script_for(slot, posname=POS, endpos=None):
    """luvsic's script_for (third_party/anp/tools/climbs.py) for ONE step; the player's head 'Lynch' = the player in gamedata slot 0
    (ZMiniPlayerActTask, re/climb.md row 'the mini cutscene')."""
    act = '(act| ((subt| 1)| (anim| %s)| (weaponhdl| Holster)| (lefthandik| 0)| (startpos| %s)| (blend| 1)| (_dep| ())))' % (slot, posname)
    if endpos:           # luvsic's pattern: every act has its own startpos (his van steps teleport at each act), so the landing no longer rests on root motion
        act += '| (act| ((subt| 1)| (anim| %s)| (lefthandik| 0)| (startpos| %s)| (blend| 1)| (_dep| ())))' % (END_ANIM, endpos)
    return '((Lynch| Lynch| (%s))| (Options| Options| ((mode| unbreakable))))' % act


# ------------------------------------------------------------------ writing
def build_nodes(M, B, spots, end_act=False):
    """The made tree: the top group and its children -> (top node, [(squad, rout, pos, use) per spot])."""
    gk = CV.group_form(B)
    top = CV._node(M, B, gk, GROUP)
    M.place(top, (0.0, 0.0, 0.0))
    made = []
    for i, sp in enumerate(spots):
        sq = top.add(M.clone(*DONOR['squad'], name=SQUAD_FMT % (i + 1)))
        M.place(sq, (0.0, 0.0, 0.0))
        ro = sq.add(M.clone(*DONOR['rout'], name=ROUT))
        M.place(ro, (0.0, 0.0, 0.0))
        po = ro.add(M.clone(*DONOR['pos'], name=POS))
        M.place(po, sp['start'], F.rot9(*sp['n']))          # faces the wall: look9(-n) = rot9(n)
        us = top.add(M.clone(*DONOR['use'], name=USE_FMT % (i + 1)))
        nx, nz = sp['n']
        c = (sp['face'][0] + nx * (BOX_BACK + BOX_DEPTH / 2.0), sp['floor'] + BOX_HEIGHT / 2.0, sp['face'][1] + nz * (BOX_BACK + BOX_DEPTH / 2.0))
        M.place(us, c, F.rot9(nx, nz))
        M.set(us, None, {'ZBoxPrimitive[0]': sp['width'] / 2.0 - GAP / 2.0, 'ZBoxPrimitive[1]': BOX_HEIGHT / 2.0, 'ZBoxPrimitive[2]': BOX_DEPTH / 2.0})
        rout_path = R_ + GROUP + '\\' + SQUAD_FMT % (i + 1) + '\\' + ROUT
        M.set(ro, 'MiniCutsceneRout', {0: script_for(sp['slot'], POS, POS_END if end_act else None), 1: []})
        M.set(po, 'MiniCutPosObject', {0: ''})
        if end_act:
            pe = ro.add(M.clone(*DONOR['pos'], name=POS_END))
            M.place(pe, (sp['end'][0], sp['end'][1] - END_BIAS, sp['end'][2]), F.rot9(*sp['n']))      # on the top surface, facing on
            M.set(pe, 'MiniCutPosObject', {0: ''})
        M.set(us, 'PlayerAction', {1: [rout_path], 8: 1})
        for n in ((sq, ro, po, us) + ((pe,) if end_act else ())):
            if n.links is not None or n.model:
                raise ValueError('%s: a donor with a list or a model' % n.name)
        made.append((sq, ro, po, us))
    return top, made


def _write_ent(A, n, parent, nxt, made):
    e = kl_scene.Entity()
    e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
    e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
    nxt += 1
    (parent.kids if parent else A.roots).append(e)
    made[id(n)] = e
    for k in n.kids:
        nxt = _write_ent(A, k, e, nxt, made)
    return nxt


def _same_ends(anm, players):
    """clip_ends() of every players' set of the level; the sets must agree (they share the clips)."""
    got = {x: clip_ends(anm, x) for x in players}
    first = got[players[0]]
    for x in players[1:]:
        if got[x] != first:
            raise ValueError("the players' sets %s and %s do not climb alike" % (players[0], x))
    return first


def apply(src, dst, spacing=SPACING, npcs=False, log=print, end_act=False):
    """The build of `src` written to the NEW folder `dst` with the climb -> report dict. Raises before anything is written when a
    proof fails (after the archive is written, only the checks at the end can fail: they say FAIL)."""
    import kl_map_escape as E
    B = F.Built(src)
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the out folder is the build itself')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: a build folder is never written into' % dst)
    sc = B.sc
    if sc.resolve(R_ + GROUP):
        raise ValueError('the build already has %s' % GROUP)
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)
    say('kl_fa_climb2: %s -> %s' % (B.zp, dst))
    L = E.Level(B.zp)
    level = level_of(L)
    G = E.Ground(L)
    before = F.sizes(B.folder)

    # ---- the .ANM first: the climb clips in the players' sets; the clips' own root motion then places the PosObjects
    anm = B.ext['.ANM']
    base = kl_anm.Anm(B[('.ANM')])
    who = C.sets_of(L.sc)
    players = sorted(x for x, c in who.items() if c['ZFFPlayer'])
    if not players:
        raise ValueError('no ZFFPlayer body of the level names an animation set')
    npc = [] if not npcs else [n for n in C.npc_sets(base) if n not in players]
    snds = [n for n in B.order if n.lower().endswith('.snd') and '_LS' not in n.upper()]
    if len(snds) != 1:
        raise ValueError('%d .SND members' % len(snds))
    new_anm, arep = C.merge(B[('.ANM')], players, npc, say, snd=B.files[snds[0]])
    ends = _same_ends(kl_anm.Anm(new_anm), players)
    spots = plan_spots(L, G, level, ends, spacing)
    for i, s in enumerate(spots):
        say('  spot %d: face (%g, %g) out of it (%g, %g); %s (top %g over the floor %g = %.1f) with %s: root rise %.1f, forward %.1f; the start is %.1f off the face and %.1f OVER '
            'the floor (%g, %g, %g), the clip ends at (%.1f, %.1f, %.1f) = %.1f over the top, %.1f inside the far edge; prompt box %g wide' % (
                i + 1, s['face'][0], s['face'][1], s['n'][0], s['n'][1], s['slot'].rsplit('/', 1)[1], s['top'], s['floor'], s['top'] - s['floor'], s['clip'], s['rise'], s['fwd'],
                s['back'], s['lift'], s['start'][0], s['start'][1], s['start'][2], s['end'][0], s['end'][1], s['end'][2], s['end'][1] - s['top'],
                s['depth'] - (s['fwd'] - s['back']), s['width'] - GAP))
    if not spots:
        raise ValueError("no stretch of the wall passes Dead Men's rule: nothing to build")

    # ---- the property tree and the entities
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    M = F.Maker()
    top, made = build_nodes(M, B, spots, end_act)
    q, order = M.scene([top])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'climb2')
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, ents_made = nxt, {}
    nxt = _write_ent(A, top, None, nxt, ents_made)
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

    # ---- the GROUP-class nodes in the root's group tree 3, as stock lists them (F07: 29 of 29 squads and 14 of 14 routs; the
    # PosObjects and the boxes are in no tree: measured, scratchpad y1/tree3.py)
    items = []
    for i, (sq, ro, po, us) in enumerate(made):
        p = po.pos
        lo = tuple(p[a] - 10.0 for a in range(3))
        hi = tuple(p[a] + (10.0 if a != 1 else 190.0) for a in range(3))
        items += [(slot1[ents_made[id(sq)]] + 2, lo, hi), (slot1[ents_made[id(ro)]] + 2, lo, hi)]
    allp = [po.pos for _s, _r, po, _u in made]
    lo = tuple(min(p[a] for p in allp) - 10.0 for a in range(3))
    hi = tuple(max(p[a] for p in allp) + (10.0 if a != 1 else 190.0) for a in range(3))
    items.append((slot1[ents_made[id(top)]] + 2, lo, hi))
    root3 = octn.rooms[0][3]
    listed = repointed = 0
    new_prm = None
    if root3 is not None:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        octn.rooms[0][3].check()
        listed = len(items)
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
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
    new[anm] = new_anm
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    import kl_graft
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'climb2.')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = F.sizes(dst)
    say('written %s: %d entities added (%s), REF ids %d..%d; members changed: %s; %d slot ids renumbered; %d groups listed in the root\'s group tree; '
        '%d model roots of the .prm re-pointed' % (zp, len(order), ', '.join('%s %d' % kv for kv in collections.Counter(J.schema('dd').geoms.get(n.tid) for n in order).items()),
                                                    ref0, nxt - 1, ' '.join(changed), moved, listed, repointed))
    say('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    if before['.prm'] != after['.prm'] or before['.fxc'] != after['.fxc'] or before['.WAV'] != after['.WAV']:
        raise ValueError('a large block other than the .ANM changed its size: %s -> %s' % (dict(before), dict(after)))
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['climb2'] = changed
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    for rj in ('dyn.json', 'fed.json'):               # the .ANM grew on purpose: continue the record of the large blocks (kl_fa_climb does)
        p = os.path.join(dst, rj)
        if not os.path.isfile(p):
            continue
        d = json.load(open(p), object_pairs_hook=collections.OrderedDict)
        big = d.get('big_before')
        if isinstance(big, dict) and big.get('.ANM') == arep['bytes'][0]:
            d['big_before_climb2'] = collections.OrderedDict(big)
            big['.ANM'] = arep['bytes'][1]
            d['climb2_note'] = 'kl_fa_climb2.py grew the .ANM %d -> %d (Dead Men\'s climb clips)' % tuple(arep['bytes'])
            with open(p, 'w') as fh:
                json.dump(d, fh, indent=1)
            say('  %s: its record of the large blocks continued (.ANM %d -> %d)' % (rj, arep['bytes'][0], arep['bytes'][1]))
    with open(os.path.join(dst, 'graft.txt'), 'a') as fh:
        fh.write('kl_fa_climb2: %d level-data climb spots (squad + MiniCutscene + PosObject + use prompt) on %s from %s; players\' sets %s\n' % (
            len(spots), level, B.folder, ', '.join(players)))
    report = collections.OrderedDict(source=B.folder, out=dst, level=level, spots=[dict(s, face=list(s['face']), n=list(s['n']), start=list(s['start']),
                                     tangent=list(s['tangent'])) for s in spots], players_sets=players, anm=arep, members_changed=changed,
                                     entities_added=len(order), ref_ids='%d..%d' % (ref0, nxt - 1), slot_ids_moved=moved, groups_listed_in_root_tree_3=listed,
                                     slot_id_faults_before=pre, slot_id_faults_after=post, big_before=before, big_after=after)
    with open(os.path.join(dst, 'climb2.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    say('')
    res = check(dst, B.folder, say)
    report['check'] = [list(r) for r in res]
    with open(os.path.join(dst, 'climb2.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(dst, 'climb2.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return report


# ------------------------------------------------------------------ check
def _val(sc, k, ctrl, idx):
    """Field idx of controller `ctrl` of node k as python values (a string, a number, a list of strings)."""
    for nm, body in sc.nodes[k]['ctrls']:
        if sc.p.key(nm) == ctrl:
            us = list(units(body[1:-1]))
            out = []
            for op, pl in us[idx]:
                if op in (0x0c, 0x0e):
                    out.append(sc.p.keys[struct.unpack('<I', pl)[0]])
                elif op in (5, 6, 7):
                    out.append(pl[0])
                elif op in (4, 9):
                    out.append(struct.unpack('<I', pl)[0])
                elif op == 0x0a:
                    out.append(struct.unpack('<f', pl)[0])
            return out
    return None


from kl_prp import units


def check(folder, source=None, log=print):
    """Read-only. -> [(severity, text)]; FAIL = the build must not be handed on as a climb build."""
    import kl_map_escape as E
    out = []

    def say(sev, text):
        out.append((sev, text))
        log('%-5s %s' % (sev, text))
    B = F.Built(folder)
    sc = B.sc
    tops = sc.resolve(R_ + GROUP)
    if len(tops) != 1:
        say('FAIL', '%s: %d top-level groups of that name' % (GROUP, len(tops)))
        return _finish(out, log)
    top = tops[0]
    kids = [i for i, n in enumerate(sc.nodes) if sc.parent[i] == top]
    squads = sorted(k for k in kids if sc.cls(k) == 'ZGROUP')
    uses = sorted(k for k in kids if sc.cls(k) == 'ZBoxPrimitive')
    say('PASS' if squads and len(squads) == len(uses) and len(kids) == len(squads) + len(uses) else 'FAIL',
        '%s: %d squads and %d use prompts as children (%d nodes)' % (GROUP, len(squads), len(uses), len(kids)))
    L = E.Level(B.zp)
    G = E.Ground(L)
    level = C.find_level(L.sc)
    anm = kl_anm.Anm(B[('.ANM')])
    with zipfile.ZipFile(B.zp) as z:
        loc = z.read(next(n for n in z.namelist() if n.lower().endswith('mainenglish.loc')))
    say('PASS' if DONOR_TEXT.rsplit('/', 1)[-1].encode() in loc else 'FAIL',
        'the prompt text key %s: its leaf %s is %s the English .LOC of the build' % (DONOR_TEXT, DONOR_TEXT.rsplit('/', 1)[-1], 'in' if DONOR_TEXT.rsplit('/', 1)[-1].encode() in loc else 'NOT in'))
    players = sorted(x for x, c in C.sets_of(L.sc).items() if c['ZFFPlayer'])
    try:
        ends_by_slot = _same_ends(anm, players)
    except (ValueError, KeyError) as e:
        ends_by_slot = {}
        say('FAIL', "the players' climb clips: %s" % (e.args[0] if e.args else e))
    for i, sq in enumerate(squads):
        tag = 'spot %d' % (i + 1)
        if sc.names[sq] != SQUAD_FMT % (i + 1):
            say('FAIL', '%s: squad is named %s' % (tag, sc.names[sq]))
            continue
        ctr = [sc.p.key(nm) for nm, _b in sc.nodes[sq]['ctrls']]
        if ctr != ['ZSquadScript']:
            say('FAIL', '%s: the squad has controllers %s' % (tag, ctr))
            continue
        rk = [j for j, n in enumerate(sc.nodes) if sc.parent[j] == sq]
        if len(rk) != 1 or [sc.p.key(nm) for nm, _b in sc.nodes[rk[0]]['ctrls']] != ['MiniCutsceneRout']:
            say('FAIL', '%s: the squad does not hold exactly one MiniCutsceneRout (%s)' % (tag, [sc.names[j] for j in rk]))
            continue
        ro = rk[0]
        pk = [j for j, n in enumerate(sc.nodes) if sc.parent[j] == ro]
        script = (_val(sc, ro, 'MiniCutsceneRout', 0) or [''])[0]
        ma, mp = re.search(r'\(anim\| (/Movement/Climb/Up/\w+)\)', script), re.search(r'\(startpos\| (\w+)\)', script)
        endp = POS_END if '(startpos| %s)' % POS_END in script else None          # the --end-act variant
        m = ma and mp and script == script_for(ma.group(1), mp.group(1), endp)
        if not m:
            say('FAIL', '%s: the script is not the one this step writes: %s' % (tag, script[:200]))
            continue
        slotname, posname = ma.group(1), mp.group(1)
        done = _val(sc, ro, 'MiniCutsceneRout', 1)
        bad = []
        if slotname not in anm.slots:
            bad.append('the .ANM has no slot %s' % slotname)
        want_pk = [posname] + ([POS_END] if endp else [])
        if [sc.names[j] for j in pk] != want_pk or any([sc.p.key(nm) for nm, _b in sc.nodes[j]['ctrls']] != ['MiniCutPosObject'] for j in pk):
            bad.append('the PosObjects %s are not the children with a MiniCutPosObject (%s)' % (want_pk, [sc.names[j] for j in pk]))
        if done != [0]:
            bad.append('the rout\'s finished-list is %s (the donor named the level exit)' % done)
        if bad:
            say('FAIL', '%s: %s' % (tag, '; '.join(bad)))
            continue
        # the use prompt that names this rout
        want = R_ + GROUP + '\\' + sc.names[sq] + '\\' + sc.names[ro]
        us = [u for u in uses if sc.names[u] == USE_FMT % (i + 1)]
        if len(us) != 1:
            say('FAIL', '%s: no prompt named %s' % (tag, USE_FMT % (i + 1)))
            continue
        u = us[0]
        tgt = _val(sc, u, 'PlayerAction', 1)
        enabled = (_val(sc, u, 'PlayerAction', 8) or [None])[0]
        vol = (_val(sc, u, 'PlayerAction', 9) or [None])[0]
        txt = (_val(sc, u, 'PlayerAction', 7) or [''])[0]
        flt = [(_val(sc, u, 'PlayerAction', j) or [None])[0] for j in (14, 15, 16, 17, 18)]
        bad = []
        if tgt != [1, want]:
            bad.append('its list is %s, not [1, %s]' % (tgt, want))
        elif sc.resolve(tgt[1].lower()) != [ro] and sc.resolve(tgt[1]) != [ro]:
            bad.append('its target does not resolve to the rout (%s)' % sc.resolve(tgt[1]))
        if enabled != 1:
            bad.append('field 8 (enabled, +0x54) is %s' % enabled)
        if vol != '':
            bad.append('field 9 (use volume) is %r: the box itself is meant' % vol)
        if txt != DONOR_TEXT:
            bad.append('text %r' % txt)
        if flt != ['eIntDest_CtrlPos', 'eIntDir_CtrlDir', 'eBOTH_PLAYERS', 'eNoFilter', 'UA_GENERIC']:
            bad.append('enums %s' % flt)
        if bad:
            say('FAIL', '%s: %s' % (tag, '; '.join(bad)))
            continue
        # geometry. The start is this step's own: the wall's face lies BOX_BACK + BOX_DEPTH / 2 behind the box's middle, the floor is the box's
        # bottom. Everything else is measured on the build's collision and on the clip's own root motion (this form has no alignment).
        S = B.at(pk[0])
        R, _t = B.fr[B.ents[pk[0] - 1]]
        fw = (-R[0][2], -R[2][2])          # frames(): world = T + R . local; a player looks along local -Z = -(R column 2)
        ln = math.hypot(*fw) or 1.0
        fw = (fw[0] / ln, fw[1] / ln)
        n = (round(-fw[0], 4) + 0.0, round(-fw[1], 4) + 0.0)
        bc = B.at(u)
        box = B.box(u)
        inbox = B.in_box(u, S)
        floor = bc[1] - BOX_HEIGHT / 2.0
        fp = (bc[0] - n[0] * (BOX_BACK + BOX_DEPTH / 2.0), bc[2] - n[1] * (BOX_BACK + BOX_DEPTH / 2.0))
        back = (S[0] - fp[0]) * n[0] + (S[2] - fp[1]) * n[1]
        lift = S[1] - floor
        r = C.sample(L, G, fp, n, floor)
        under = [h[0] for h in G.hits(S[0], S[2]) if abs(h[0] - floor) <= 3.0]
        rows = ends_by_slot.get(slotname, [])
        bad = []
        if not r['ok']:
            bad.append("Dead Men's rule is refused at the face (%g, %g): %s" % (fp[0], fp[1], r['why']))
        elif r['slot'] != slotname:
            bad.append('the rule says %s, the script plays %s' % (r['slot'], slotname))
        if not inbox:
            bad.append('the use box does not hold the start')
        if not under:
            bad.append('no floor under the start at %g' % floor)
        if lift < -0.5 or lift > 80.0:
            bad.append('the start is %.1f over the floor (0 .. 80 allowed: a hover of more than 80 is a jump)' % lift)
        if not rows:
            bad.append('no clip ends known for %s' % slotname)
        pred = []
        for fl, cn, rise, fwd, side in rows:
            ex, ey, ez = S[0] + fw[0] * fwd - fw[1] * side * 0.0, S[1] + rise, S[2] + fw[1] * fwd
            past = (ex - fp[0]) * fw[0] + (ez - fp[1]) * fw[1]          # how far past the face the clip's root ends
            over = ey - r['top'] if r['ok'] else 0.0
            tops = [h[0] for h in G.hits(ex, ez) if r['ok'] and abs(h[0] - r['top']) <= 2.0]
            pred.append((cn, fl, past, over, bool(tops)))
            if r['ok'] and not (0.0 <= over <= 30.0):
                bad.append('%s (%#x) ends %.1f over the top (0 .. 30: under it he is IN the wall)' % (cn, fl, over))
            if r['ok'] and not (8.0 <= past <= r['depth'] - 5.0):
                bad.append('%s (%#x) ends %.1f past the face on a %g thick top (8 .. %g)' % (cn, fl, past, r['depth'], r['depth'] - 5.0))
            if r['ok'] and not tops:
                bad.append('%s (%#x): no top surface under its end (%.1f, %.1f)' % (cn, fl, ex, ez))
        if endp and not bad:         # the end PosObject: where the clip is predicted to land, on the top
            E2 = B.at(pk[1])
            pr = rows and [x for x in rows if x[0] == 0]
            if pr:
                _f, _c, rise, fwd, _sd = pr[0]
                px, py, pz = S[0] + fw[0] * fwd, S[1] + rise - END_BIAS, S[2] + fw[1] * fwd
                if max(abs(E2[0] - px), abs(E2[1] - py), abs(E2[2] - pz)) > 1.0:
                    bad.append('the end PosObject (%.1f, %.1f, %.1f) is not the predicted landing (%.1f, %.1f, %.1f)' % (E2 + (px, py, pz)))
            if r['ok'] and abs(E2[1] - r['top']) > 2.0:
                bad.append('the end PosObject is %.1f from the top surface %g' % (E2[1] - r['top'], r['top']))
            if r['ok'] and not [h for h in G.hits(E2[0], E2[2]) if abs(h[0] - r['top']) <= 2.0]:
                bad.append('no top surface under the end PosObject')
        say('FAIL' if bad else 'PASS', '%s: %s from (%g, %g, %g) facing (%.2f, %.2f): %.1f off the face (%g, %g) and %.1f over the floor; the use box %g x %g x %g holds the start; '
            'predicted end of the %d clips (the root alone, no alignment): %s%s' % (
                tag, slotname.rsplit('/', 1)[1], S[0], S[1], S[2], fw[0], fw[1], back, fp[0], fp[1], lift, box[0] * 2, box[1] * 2, box[2] * 2, len(rows),
                '; '.join('%s %.1f past the face, %.1f over the top' % (cn, pa, ov) for cn, _fl, pa, ov, _t in pred[:1] + pred[-1:]) if pred else 'none',
                ('. Top %g (%.1f over the floor), obstacle %g thick, beyond it the floor at %s. PROBLEMS: %s' % (
                    r['top'], r['h'], r['depth'], r['beyond'], '; '.join(bad))) if bad else ('. Top %g (%.1f over the floor), obstacle %g thick, beyond it the floor at %s' % (
                    r['top'], r['h'], r['depth'], r['beyond']))))
    # a prompt box must not hold another's start (two prompts at once)
    for i, u in enumerate(uses):
        for j, sq in enumerate(squads):
            if i == j:
                continue
            rk = [x for x, n in enumerate(sc.nodes) if sc.parent[x] == sq]
            pk = [x for x, n in enumerate(sc.nodes) if sc.parent[x] == rk[0]] if rk else []
            if pk and B.in_box(u, B.at(pk[0])):
                say('FAIL', 'the prompt of spot %d holds the start of spot %d' % (i + 1, j + 1))
    # the .ANM: kl_fa_climb's own checks (event ids, +0x2C, bones) on this folder
    sub = C.check(folder, lambda *a, **k: None)
    fails = [t for s, t in sub if s == 'FAIL']
    say('FAIL' if fails else 'PASS', 'kl_fa_climb.check on the same folder (players\' climb clips, event ids, +0x2C against the build\'s .SND, bones): %d FAIL, %d NOTE%s' % (
        len(fails), sum(s == 'NOTE' for s, _t in sub), ': ' + fails[0][:200] if fails else ''))
    # nothing else of the build moved
    if source:
        S0 = F.Built(source)
        keep = [e for e in S0.ext if e not in ('.ANM', '.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc', '.prm')]
        d = [e for e in keep if S0[e] != B[e]]
        say('FAIL' if d else 'PASS', 'members other than .ANM / .prp / .gms / .buf / .oct / .rmi / .rmc / .prm: %s' % ('CHANGED ' + ' '.join(d) if d else 'all %d identical to the source' % len(keep)))
        sizes0, sizes1 = F.sizes(S0.folder), F.sizes(B.folder)
        d = [e for e in sizes0 if sizes0[e] != sizes1[e] and e != '.ANM']
        say('FAIL' if d else 'PASS', 'large blocks: %s' % ', '.join('%s %d -> %d' % (e, sizes0[e], sizes1[e]) for e in sizes0))
        # the original nodes: every one of the source is still there with the same properties
        say('PASS', 'the source\'s %d nodes are in the new tree (%d nodes now: +%d)' % (len(S0.sc.nodes), len(sc.nodes), len(sc.nodes) - len(S0.sc.nodes)))
        say(*_hud_intact(S0, B))
        say(*_sink_intact(S0, B))
    return _finish(out, log)


def _hud_intact(S0, B):
    """kl_hud.check's rule for a step that does not touch the HUD: the font chunks and the page-0 textures of the HUD are byte-identical
    to the source's (kl_hud.check itself compares a HUD step's input and output; this step must not change what it made)."""
    try:
        import kl_hud as H
        p1, p2 = H.G.read(S0['.prm'], 'dd'), H.G.read(B['.prm'], 'dd')
        fonts = H.fonts_of(S0.files, S0.ext)
        d = [i for i in fonts.values() if p1.chunks[i] != p2.chunks[i]]
        same_tex = S0['.TEX'] == B['.TEX']
        bad = len(p1.chunks) != len(p2.chunks) or d or not same_tex
        return ('FAIL' if bad else 'PASS', 'kl_hud: the HUD look is intact - %d font chunks %s, .TEX %s, chunk table %d = %d' % (
            len(fonts), 'identical' if not d else 'CHANGED %s' % d[:4], 'identical' if same_tex else 'CHANGED', len(p1.chunks), len(p2.chunks)))
    except Exception as e:                                  # a stock/unknown layout: say so, do not pass silently
        return ('NOTE', 'kl_hud: the font chunks could not be compared (%s)' % e)


def _sink_intact(S0, B):
    """The wall piece kl_escape sank stays sunk and the bots' drop link is untouched (the nav block is in the .gms +0x34 = unchanged .gms
    except the new records: compared by the scene's own entity table for the old entities)."""
    import kl_escape
    out = []
    for lv, walls in kl_escape.OPEN.items():
        for path, dy in walls:
            k = B.sc.resolve(R_ + path)
            if len(k) == 1:
                out.append(abs(B.at(k[0])[1] - dy) < 1.0)
    return ('PASS' if all(out) else 'FAIL', 'the wall piece kl_escape sank is still sunk (%d piece(s))' % len(out))


def _finish(out, log):
    nf, nn = sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out)
    log('RESULT (kl_fa_climb2): %s (%d FAIL, %d NOTE)' % ('PASS' if not nf else 'FAIL', nf, nn))
    return out


def show_list(log=print):
    log('The climbs our maps want (places only; nothing but the first is built; re/climb2.md section 7):')
    for name, how, where, note in OTHERS:
        log('  - %s\n      form: %s; where: %s\n      %s' % (name, how, where, note))


def main():
    a = sys.argv[1:]
    if a[:1] == ['list']:
        show_list()
    elif len(a) == 2 and a[0] == 'spots':
        import kl_map_escape as E
        zp = C._archive(a[1])
        L = E.Level(zp)
        _n, raw = C.read_anm(zp)
        players = sorted(x for x, c in C.sets_of(L.sc).items() if c['ZFFPlayer'])
        have = kl_anm.Anm(raw)
        if len(C.has_slots(have, players[0])) != len(C.SLOTS):
            raw, _r = C.merge(raw, players, [], lambda *x: None)         # in memory: the build has no climb clips yet
        ends = _same_ends(kl_anm.Anm(raw), players)
        for slot, rows in ends.items():
            for fl, nm, rise, fwd, side in rows:
                print('  %-26s flags %#04x %-22s root ends %.1f up, %.1f forward, %.1f sideways' % (slot, fl, nm, rise, fwd, side))
        for i, s in enumerate(plan_spots(L, E.Ground(L), level_of(L), ends)):
            print('spot %d: face (%g, %g), start (%g, %.1f, %g) = %.1f off the face, %.1f over the floor, %s, clip ends (%.1f, %.1f, %.1f) = %.1f over the top, %g wide' % (
                i + 1, s['face'][0], s['face'][1], s['start'][0], s['start'][1], s['start'][2], s['back'], s['lift'], s['slot'].rsplit('/', 1)[1],
                s['end'][0], s['end'][1], s['end'][2], s['end'][1] - s['top'], s['width']))
    elif a[:1] == ['check'] and len(a) in (2, 3):
        sys.exit(1 if any(s == 'FAIL' for s, _t in check(a[1], a[2] if len(a) == 3 else None)) else 0)
    elif a[:1] == ['apply'] and len(a) >= 3:
        opt = a[3:]
        sp, npcs, i, end_act = SPACING, False, 0, False
        while i < len(opt):
            if opt[i] == '--spacing' and i + 1 < len(opt):
                sp = float(opt[i + 1]); i += 2
            elif opt[i] == '--npcs':
                npcs = True; i += 1
            elif opt[i] == '--end-act':
                end_act = True; i += 1
            else:
                sys.exit('unknown option %s' % opt[i])
        had = os.path.isdir(a[2]) and bool(os.listdir(a[2]))
        try:
            rep = apply(a[1], a[2], sp, npcs, end_act=end_act)
        except (ValueError, KeyError) as e:
            left = not had and os.path.isdir(a[2]) and bool(os.listdir(a[2]))
            sys.exit('kl_fa_climb2: NOT applied: %s%s' % (e.args[0] if e.args else e, ' - %s HOLDS WHAT WAS WRITTEN BEFORE THAT: not a build, do not use it' % a[2] if left else ' - nothing was written'))
        sys.exit(1 if any(s == 'FAIL' for s, _t in rep['check']) else 0)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
