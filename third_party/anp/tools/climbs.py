"""Dead Men climbing, rebuilt for Dog Days.

Dog Days dropped the player climb move (DM class ZFFPlayerMovementClimb), so a climb spot becomes:
  * a ZPlayerAction "use" prompt whose use volume is the DM climb hint box (moved to the start of the climb), and
  * a grafted Dog Days MiniCutscene whose PosObjects mark each stage; the player 'act's Dead Men's own climb
    clips (/Movement/Climb/...), merged into the level's animation library, snapped to each PosObject.
The prompt is an event of the FIRST grafted PosObject, not of the DM box (in game, 11 Oct 2026: on the box it was
switched off for good - +0x7c initialised and +0x54 enabled both 0, the state kl2 0x7fdbd4 leaves after the message
with runtime id 252; the box's own DM TriggerBox fires as Kane walks in). For the same reason the DM box loses its
TriggerBox event (it only showed DM's 'climb the van' briefing, which the prompt replaces).
ZPlayerAction (kl2): ctor 0x8e92e0 sets +0x7c = 1; message handler (vt slot 26, 0x7fdbb0) ignores everything while
+0x7c == 0; 'Activate' sets +0x54 = 1, 'AITrigger' toggles it; init (slot 13) resolves +0x58 (use volume, a geom
reference; empty = the owner) into +0x88 and makes the HUD entry +0x98 visible or not from +0x54.
Orientation convention (from Dog Days MiniCut data): a stored 3x3 [r0 r1 r2] faces r2; for a yaw-only facing
f=(fx,0,fz) the stored matrix is [-fz,0,fx, 0,1,0, fx,0,fz] (identity is stored as [0,0,1,0,1,0,1,0,0])."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from graft import node_spans

DONOR_MC = '01_MiniCut_Vault_Over_Desk@5209'      # L01 group with 3 PosObject children
DONOR_POS = ['PosObject_Cover_Spot02', 'PosObject_BackOfHorseshoe', 'PosObject_Cover_Spot01']
# every DD MiniCutscene runs inside a squad; the grafted one gets its own, a copy of this L01 squad's group and its
# ZSquadScript event (eStayBack / eAllTypes / eNormalAlertness, no references - as L03's Squad_OutroCut, the squad of
# the co-op climb wall cutscene that L03's EndAlleyHACK PlayerAction starts)
SQUAD_DONOR = 'Special!CutScenes!Intro_Shanghai!IntroCollection!Introcutscene'

# world positions in cm (y up). Facing as (x,z).
CLIMBS = {
    'M01': [dict(
        name='ANP_Climb_Van',
        box='Specials!IngameBriefing!ClimbBriefTriggerON',          # DM 'press use to climb' hint box (Kane)
        text='M01/IngameBriefing/100_ClimbVan',
        box_pos=(-3185.0, 120.0, 2160.0), box_half=(140.0, 120.0, 90.0), face=(0.0, 1.0),
        # overturned getaway van (top ~2.0 m) -> bus-stop shelter roof (~3.5 m) -> drop past the fence
        steps=[('/Movement/Climb/Up/High',   (-3185.0, 30.0, 2190.0)),
               ('/Movement/Climb/Up/High',   (-3185.0, 202.0, 2590.0)),
               ('/Movement/Climb/Down/High', (-3185.0, 346.0, 2840.0))],
        # buddy=('Merc_04', 7.0),   # off until the player's climb is seen working: an actor the squad cannot bind
                                    # may stop the whole cutscene
    )],
}

def squads_for(level):
    """graft() 'squads' map for this level's climbs: each MiniCutscene inside its own squad"""
    return {c['name']: (c['name'] + '_Squad', SQUAD_DONOR) for c in CLIMBS.get(level, [])}

def stored_rot(face):
    fx, fz = face
    return [-fz, 0.0, fx, 0.0, 1.0, 0.0, fx, 0.0, fz]

def _set_arrays(ops, s, e, rot=None, pos=None):
    """set the first [9] (rotation) and [3] (position) float arrays inside ops[s:e]"""
    j = s; done9 = rot is None; done3 = pos is None
    while j < e and not (done9 and done3):
        op = ops[j]
        if op[1] & 0x7f == 1 and op[2] == 9 and not done9:
            for k in range(9): ops[j + 1 + k] = [ops[j + 1 + k][0], ops[j + 1 + k][1], float(rot[k])]
            done9 = True; j += 10; continue
        if op[1] & 0x7f == 1 and op[2] == 3 and not done3 and done9:
            for k in range(3): ops[j + 1 + k] = [ops[j + 1 + k][0], ops[j + 1 + k][1], float(pos[k])]
            done3 = True; j += 4; continue
        j += 1
    assert done9 and done3, 'arrays not found'

def _obj_end(ops, j):
    d = 0
    while True:
        b = ops[j][1] & 0x7f
        if b == 2: d += 1
        elif b == 0x7e:
            d -= 1
            if d == 0: return j + 1
        j += 1

def script_for(c):
    P = DONOR_POS
    acts = []
    for k, (anim, pos) in enumerate(c['steps']):
        hdl = '| (weaponhdl| Holster)' if k == 0 else ''        # as Lynch's act in L03's co-op climb wall cutscene
        acts.append('(act| ((subt| 1)| (anim| %s)%s| (lefthandik| 0)| (startpos| %s)| (blend| 1)| (_dep| ())))' % (anim, hdl, P[k]))
    s = '((Lynch| Lynch| (%s))' % '| '.join(acts)
    if c.get('buddy'):
        who, delay = c['buddy']
        last_anim = c['steps'][-1][0]
        s += ('| (Actor| %s| ((delay| ((delay| %.1f)| (delayforever| 0)| (randdelay| 0.0)| (_dep| ())))| '
              '(act| ((subt| 1)| (anim| %s)| (lefthandik| 0)| (startpos| %s)| (blend| 1)| (_dep| ())))))'
              % (who, delay, last_anim, P[len(c['steps']) - 1]))
    s += '| (Options| Options| ((mode| unbreakable))))'
    return s

def make_patch(level, rep):
    """returns (graft subtree specs, patch callback) for this level's climbs"""
    cl = CLIMBS.get(level, [])
    specs = [DONOR_MC + '=' + c['name'] for c in cl]
    byname = {c['name']: c for c in cl}
    def patch(k, newname, ops):
        c = byname.get(newname)
        if not c: return
        spans, _ = node_spans(ops, 0)
        # root group: identity at origin, so PosObjects are in world space
        r0, r1 = spans[0]
        pe = _obj_end(ops, r0)
        _set_arrays(ops, r0, pe, [0, 0, 1, 0, 1, 0, 1, 0, 0], [0.0, 0.0, 0.0])
        # MiniCutsceneRout event: our script, no on-finish activations
        j = pe; assert ops[j][1] & 0x7f == 4; nev = ops[j][2]; j += 1
        for e_ in range(nev):
            name = ops[j][2]; ev0 = j + 1; ev1 = _obj_end(ops, ev0)
            if name == 'MiniCutsceneRout':
                assert ops[ev0 + 1][1] & 0x7f == 12
                ops[ev0 + 1] = [ops[ev0 + 1][0], ops[ev0 + 1][1], script_for(c)]
                q = ev0 + 2; assert ops[q][1] & 0x7f == 4
                n = ops[q][2]
                del ops[q + 1:q + 1 + n]; ops[q] = [ops[q][0], ops[q][1], 0]
                ev1 = _obj_end(ops, ev0)
                # the last bool before the two trailing strings: 1 on L03's player climb-wall cutscene (and on most
                # stock MiniCutscenes), 0 on the NPC vault this one is copied from
                bl = [i for i in range(q + 1, ev1) if ops[i][1] & 0x7f == 6]
                ops[bl[-1]] = [ops[bl[-1]][0], ops[bl[-1]][1], 1]
            j = ev1
        spans, _ = node_spans(ops, 0)
        assert len(spans) == 1 + len(DONOR_POS), len(spans)
        rot = stored_rot(c['face'])
        for idx, (anim, pos) in enumerate(c['steps']):
            s0, s1 = spans[1 + idx]
            _set_arrays(ops, s0, _obj_end(ops, s0), rot, pos)
        # the use prompt: an event of the first PosObject (at the start of the climb), its volume the DM box
        s0, _ = spans[1]; j = _obj_end(ops, s0); assert ops[j][1] & 0x7f == 4
        ops[j] = [ops[j][0], ops[j][1], ops[j][2] + 1]
        ops[j + 1:j + 1] = action_event(c)
        rep['climb %s: %d stages, use prompt on %s (volume %s)' % (newname, len(c['steps']), DONOR_POS[0], c['box'])] += 1
    return specs, patch

def action_event(c):
    """ZPlayerAction 'PlayerAction' event ops; field values as on L03 PlayerAction_HsingCutGo (active from start)"""
    S = lambda v: [0, 12, v]; B = lambda v: [0, 6, v]; E = lambda v: [0, 14, v]; Cn = lambda n: [0, 4, n]
    return [S('PlayerAction'), [0, 2, None],
            S(''), Cn(1), S(PLACEHOLDER + c['name'] + '_Squad\\' + c['name']), Cn(0), Cn(0), Cn(0), Cn(0),   # +0x34, +0x38..+0x48 targets
            S(''), S(c['text']), B(1), S('ROOT\\' + c['box']), B(0), B(0), B(0), B(0),  # +0x4c, +0x50 text, +0x54 enabled, +0x58 volume
            E('eIntDest_CtrlPos'), E('eIntDir_CtrlDir'), E('eBOTH_PLAYERS'), E('eNoFilter'), E('UA_GENERIC'),
            B(1), B(1), [0, 0x7e, None]]

PLACEHOLDER = '@ANP_GRAFT_PREFIX@'

def add_player_actions(level, out, k, ent_names, rep):
    """make each climb's DM hint box the use volume of its prompt (the prompt itself is grafted with the
    MiniCutscene, see make_patch): move/reshape it and drop its DM TriggerBox events.
    Returns the change in the number of PRP objects (each dropped event is one)."""
    delta = 0
    for c in CLIMBS.get(level, []):
        try: ei = ent_names.index(c['box'])
        except ValueError:
            rep['climb %s: box %s missing' % (c['name'], c['box'])] += 1; continue
        spans, _ = node_spans(out, k)
        s0, s1 = spans[ei + 1]
        pe = _obj_end(out, s0)
        hx, hy, hz = c['box_half']
        # move/reshape the box (props end with its three half sizes)
        o = [list(x) for x in out[s0:pe]]
        _set_arrays(o, 0, len(o), stored_rot(c['face']), list(c['box_pos']))
        fl = [i for i, x in enumerate(o) if x[1] & 0x7f == 10]
        for i, v in zip(fl[-3:], (hx, hy, hz)): o[i][2] = float(v)
        # the volume's last bool before its sizes is 1 on Dog Days' always-available use prompts
        # (L03 PlayerAction_HsingCutGo) and 0 on ones a script switches on later
        bl = [i for i, x in enumerate(o) if x[1] & 0x7f == 6]
        if bl: o[bl[-1]][2] = 1
        out[s0:pe] = [tuple(x) for x in o]
        # drop the box's DM TriggerBox events: one fires as Kane walks in (DM's briefing) and must not
        # disarm the volume the prompt uses
        j = pe; assert out[j][1] & 0x7f == 4
        nev = out[j][2]; e = j + 1; kept = 0
        for _ in range(nev):
            name = out[e][2]; ee = _obj_end(out, e + 1)
            if name == 'TriggerBox':
                del out[e:ee]; delta -= 1; rep['climb %s: DM TriggerBox dropped from %s' % (c['name'], c['box'])] += 1
            else:
                e = ee; kept += 1
        out[j] = (out[j][0], out[j][1], kept)
        rep['climb %s: use volume %s' % (c['name'], c['box'])] += 1
    return delta

def fix_targets(out, prefix):
    n = 0
    for i, (p, op, v) in enumerate(out):
        if isinstance(v, str) and v.startswith(PLACEHOLDER):
            out[i] = (p, op, prefix + v[len(PLACEHOLDER):]); n += 1
    return n
