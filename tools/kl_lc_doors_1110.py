r"""kl_lc_doors_1110.py - Last Call (DM05A, slot F01): luvsic's sliding FRONT-OFFICE DOORS at the loot room, stage 1 of re/lastcall_mizuki_1110.md. 2026-11-10.
OFFLINE: reads the live DM05A zips and luvsic's M05 (READ ONLY), writes a stage; nothing is installed, the game is not started.

BACKGROUND (FACT, measured 2026-11-10 on the live zip 0ff298a6 and M05_Main.zip): loot = Yoko's office (Daughter_Room_01b), reached through the front office
(Daughter_Room_01a). luvsic's M05 has two sliding pairs there, four key-framed leaves (ZSTDOBJ, flags 0x2641fa, 64-byte raw KEYS, MatPosAnim 'Activate'):
  outer group REF 23811 (M05 7288) at (1500,358,3313), leaves 23812 / 23813 (M05 7289 / 7290)
  inner group REF 23814 (M05 7298) at (2500,358,3313), leaves 23816 / 23815 (M05 7299 / 7300)
Our DM05A already CONTAINS all of these entities (same REFs, same keys, same MatPosAnim): an older pass buried them 1500 cm down (y -1500: .gms local of every leaf;
the outer leaves are authored in world values in the .prp under a group with flag 0x40000000, so there the world y is -1142 instead of 358). Our own kick doors
ROOT\KL_Interact!1 (KL_Door_1 at x 1500, KL_Door_2 at x 2500, z 3433) stand in the same doorways.

WHAT CHANGES (no entity added or removed: no slot id moves, .oct / .rmi / .rmc / .prm / .MAT / .TEX stay byte for byte):
 1. the four leaves go back up: y of the .prp ZGEOM[2] and of the .gms translation = M05's (x and z are asserted equal to M05's);
 2. MatPosAnim field 14 (the last frame) = 30 on all four leaves: they slide OPEN and STAY open (4294967295 plays the whole clip there and back = shut again;
    DOOR_LAST=30 is what kl_fa_club ships for the same luvsic door keys);
 3. the .HVK gets 4 type-4 (KEYFRAMED) slabs, cloned from M05's own door bodies (shapes 268..271, flags 378, 8 vertices, bound by REF at inst +0x30 to the LIVE leaf
    REFs): appended behind every existing shape, so the static list, its order and its MOPP codes are untouched (kl_dm02coop_1109's rule);
 4. the kick doors (--kick silent, DEFAULT): the whole KL_Door_1/2 tree STAYS (33 bot steps / squad nodes name it: Gameplay!merc_bot_squad Squad#02..#08
    KickDoorBehaviourRout PosInfo nodes, kl_fa_bots' loot-window logic), but both 'Door' leaves and the six Arrow entities are HIDDEN (gms flags | 0x400) and the two
    kick-door bodies (REF 39763, 39786 = one type-4 shape) are cut from the .HVK (kl_escape.cut_collision), so nothing overlaps the sliding doors.
    --kick sink (recommended off): the two KL_Door groups are also sunk by 1500 cm (prp + gms), like the old buried leaves; the bots' 33 steps then point at a buried door;
 5. opening (--variant):
    timer   (DEFAULT, safest) the unused FA timer plumbing is wired: AIMonitor (field 2, runs at round start) starts Gameplay!010_FirstFight!RivalMercVan!TimerVanGo
            (TriggerDelay2, REF 142) with --delay seconds (default 20), whose list fires Activator_OLD_VanGo (AIDWrapper, REF 141: 'Activate' to the leaves) and the two
            music GeomActivator_Door_01/_02 ('Doors_Opening', the muffle boxes). Needs nothing from the players.
    trigger (recommended off) tb_RIGHT_TheySpotYou (TriggerBox, REF 5, nothing references it) is moved over the lobby side and the front office
            (x 900..2500, z 3013..3613, ECPS_FA_MERCONLY) and carries the same list: the first heister in the box opens the doors. A retrigger replays the clip (GUESS).
    --via leaves (DEFAULT): the AIDWrapper messages the four leaves directly = what kl_fa_club ships (proven pattern); --via groups messages the two groups, whose
    RelayMessageList 'Activate' (identical to M05's) relays to the leaves (the task's wording; one hop more).
 6. --part office (recommended off until benched): the WaitingRoom (REF 20888 / 20890) and YokoGuards (REF 20844 / 20846) groups go back into the front office at
    M05's positions (position only: the Ground children sit at 0,0,0 under the group, prp = gms frame).

usage (from tools/):
  python kl_lc_doors_1110.py build --variant timer|trigger [--delay 20] [--via leaves|groups] [--kick silent|sink] [--part office] --out <dir> [--live <F01_Main.zip>]
  python kl_lc_doors_1110.py stage [--out C:\kl_build_1024\lcdoors_1110] [--live <Maps\DM05A>] [--delay 20] [--no-clear]     all variants + install.py / bats / README.txt
  python kl_lc_doors_1110.py check <zip> [--live <F01_Main.zip>] [--variant timer] [--part office] [--deep]                  offline checks of a built zip
"""
import collections, hashlib, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_author as AU, kl_gms, kl_graft, kl_hvk, kl_mopp, kl_escape
import kl_fa_bots as F
import kl_map_escape as ME
import kl_botsonline
from kl_fa_bank import J

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
M05 = os.path.join(GAME, 'Scenes', 'Locations', 'M05', 'M05_Main.zip')
OUT = r'C:\kl_build_1024\lcdoors_1110'
TAG = '.before-lcdoors1110'
SLOT = 'F01'
LIVE_PIN = '0ff298a6c45b836713affd71edcb9d4c'         # live DM05A F01_Main.zip 2026-11-10
LIVE_BOTS_PIN = '72259e270b040b4a3c8ab3abf5ee0ec4'    # live F01_Main.bots.zip 2026-11-10
LIVE_BASE_PIN = '0ff298a6c45b836713affd71edcb9d4c'    # F01_Main.bots.base.md5 text
VARIANTS = ('timer', 'trigger', 'timer_office')       # stage dirs; 'timer_office' = timer + --part office
DEFAULT_VARIANT = 'timer'
DEFAULT_DELAY = 20.0                                   # s after round start; GUESS (the plan's number): README says how to change it
DOOR_LAST = 30                                         # last frame of the open clip (kl_fa_club.DOOR_LAST: the doors slide open at 30 and would shut again by 60)
MPA_LAST = 14                                          # MatPosAnim field: last frame (kl_fa_club.MPA_LAST)
HIDE = 0x400                                           # gms flag 'hidden'

LEAVES = collections.OrderedDict([(23812, 7289), (23813, 7290), (23816, 7300), (23815, 7299)])   # live REF -> M05 REF (same leaf: asserted by name + place)
GROUPS = (23811, 23814)
KICK_REFS = (39763, 39786)                             # KL_Door_1 / KL_Door_2 'Door' leaves (one type-4 shape, 2 placements)
KICK_GROUPS = (39741, 39764)                           # KL_Door_1 / KL_Door_2
KICK_TOP = 'ROOT\\KL_Interact!1'
NODES = dict(mon=2, trig=5, act=141, timer=142, geo1=37903, geo2=37907)   # REFs: AIMonitor, tb_RIGHT_TheySpotYou, Activator_OLD_VanGo, TimerVanGo, GeomActivator_Door_01/_02
OFFICE = collections.OrderedDict([                     # guard group REF -> (live place, M05 place), cm; prp = gms for these (asserted)
    (20888, ((475, 363, 2275), (2085, 354, 3178))),    # WaitingRoom Guard#01
    (20890, ((200, 368, 2250), (1967, 353, 3486))),    # WaitingRoom Guard#02
    (20844, ((0, 364, 2050), (2387, 354, 3319))),      # YokoGuards Guard#01
    (20846, ((350, 362, 2050), (2378, 354, 3442))),    # YokoGuards Guard#02
])
TRIG_BOX = dict(centre=(1700.0, 450.0, 3313.0), half=(800.0, 150.0, 300.0))   # the 'trigger' variant: lobby side + front office (x 900..2500)
SINK = -1500.0

GUESSES = [
    'the four leaves, buried since an older pass, draw again at y 358 / local 0 and their keys (equal to M05 keys, MatPosAnim equal to M05) slide them open at MatPosAnim last frame 30 and STAY there (kl_fa_club ships the same)',
    'a type-4 body cloned from the M05 door shape (flags 378, 8 vertices) and bound by REF to the live leaf follows the keyed leaf exactly like the M05 / kick-door / F07 shutter bodies do',
    'AIMonitor field 2 starts TimerVanGo (a TriggerDelay2 nothing referenced, REF 142) and the delay counts from GO; its list message AIDWrapper(Activate) reaches the leaves',
    'the closed doors do not break the heisters\' routes: the nav mesh is baked without them (the doors were buried), so bots walk into a shut door until it opens (<= the delay)',
    'hiding the kick-door leaf and arrows with gms flag 0x400 hides the render AND (DM07 bench) the player collision; the KickDoor_Action boxes stay, so a player can still "kick" the hidden door: it does nothing visible',
    'the bots\' KickDoorBehaviourRout steps through the hidden KL_Door nodes still run (door animation plays on a hidden leaf, no body): they only walk through the doorway the sliding doors then hold (shut until the delay)',
    '--kick sink: sinking the KL_Door groups 1500 cm leaves the bots\' 33 steps pointing at a buried door (recommended off)',
    'trigger variant: a ZBoxPrimitive moved by edit (prp + gms place) fires without the .oct / .rmi trees listing the new box (the box is not indexed in them: .oct / .rmi / .rmc are byte equal); ECPS_FA_MERCONLY + eTGS_AllInside fire for ONE heister inside',
    'trigger variant: a second entry replays the clip from frame 0 (the doors would snap shut and reopen); the timer variant fires once',
    'GeomActivator_Door_01/_02 \'Doors_Opening\' muffle the Yoko office music as in kl_fa_club (sent with the door message)',
    '--part office: guards teleported by the group place keep their AI routes (Ground children at 0,0,0); their PosInfo / patrol nodes were authored at the old place (the guards walk back to them)',
]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def set_int(u, v):
    """The integer unit u (a list of one token) with the value v, same token type."""
    op = u[0][0]
    fmt = {0x09: '<I', 0x08: '<H', 0x05: '<B', 0x06: '<B', 0x07: '<B'}[op]
    return [(op, struct.pack(fmt, v))]


def node_of(B, ref):
    """node index k (1-based) of the entity with REF `ref` (B.ents[k-1])."""
    ks = [k for k in range(1, len(B.ents) + 1) if B.ents[k - 1].ref == ref]
    if len(ks) != 1:
        raise ValueError('REF %s: %d nodes' % (ref, len(ks)))
    return ks[0]


def zgeom(B, k):
    """(labels, ZGEOM[2] place) of node k from the .prp."""
    lab = J.labels('dd', B.sc.cls(k))
    return lab, [float(x) for x in kl_fa.node_values(B.sc, k)[lab.index('ZGEOM[2]')]]


def put_place(B, k, new, rep_rows, what, prp=True, gms=True):
    """New place `new` (3 floats) for node k in the .prp (ZGEOM[2]) and/or the .gms (translation)."""
    sc = B.sc
    lab, old = zgeom(B, k)
    e = B.ents[k - 1]
    g_old = list(struct.unpack_from('<3f', e.trans, 0))
    if prp:
        def fn(us):
            AU.setv(sc, us, lab.index('ZGEOM[2]'), [float(x) for x in new])
        kl_fa.edit(sc, k, None, fn)
    if gms:
        e.trans = struct.pack('<3f', *new) + e.trans[12:]
    rep_rows.append(dict(what=what, ref=e.ref, prp=[round(v, 1) for v in old], gms=[round(v, 1) for v in g_old], to=[round(float(v), 1) for v in new]))


# ---------------------------------------------------------------- the pieces
def m05_leaf_places(M):
    """{M05 REF: (name, prp place, gms place)} for the four door leaves in luvsic's M05."""
    out = {}
    for r in LEAVES.values():
        k = node_of(M, r)
        out[r] = (M.sc.names[k], zgeom(M, k)[1], list(struct.unpack_from('<3f', M.ents[k - 1].trans, 0)))
    return out


def part_nodes(B, M, variant, delay, via, kick, office, rep):
    """Everything in the .prp and the entity records (.gms). In place on B.sc / B.ents. -> the .prp bytes."""
    sc = B.sc
    mp = m05_leaf_places(M)
    rows = []
    # 1. the four leaves back to M05's height
    for lr, mr in LEAVES.items():
        k = node_of(B, lr)
        name, mprp, mgms = mp[mr]
        if sc.names[k] != name:
            raise ValueError('leaf %d is %s, M05 %d is %s' % (lr, sc.names[k], mr, name))
        _lab, prp = zgeom(B, k)
        gms = list(struct.unpack_from('<3f', B.ents[k - 1].trans, 0))
        if abs(gms[0] - mgms[0]) > 1 or abs(gms[2] - mgms[2]) > 1 or abs(gms[1] - SINK) > 1:
            raise ValueError('leaf %d .gms place %s: not the buried one (x/z as M05 %s, y %s)' % (lr, gms, mgms, SINK))
        if abs(prp[0] - mprp[0]) > 1 or abs(prp[2] - mprp[2]) > 1 or abs(prp[1] - (mprp[1] + SINK)) > 1 and abs(prp[1] - SINK) > 1:
            raise ValueError('leaf %d .prp place %s: not M05 %s lowered by 1500' % (lr, prp, mprp))
        put_place(B, k, (prp[0], mprp[1], prp[2]), rows, 'leaf prp', gms=False)
        put_place(B, k, (gms[0], mgms[1], gms[2]), rows, 'leaf gms', prp=False)
        # 2. last frame
        ci = [i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'MatPosAnim']
        if len(ci) != 1:
            raise ValueError('leaf %d: %d MatPosAnim' % (lr, len(ci)))

        def fl(us):
            if len(us) != 16 or kl_fa.value(sc, us[0]) != 'Activate' or kl_fa.value(sc, us[MPA_LAST]) != 4294967295:
                raise ValueError('leaf MatPosAnim is not [Activate .. 4294967295 ..]')
            us[MPA_LAST] = set_int(us[MPA_LAST], DOOR_LAST)
        kl_fa.edit(sc, k, ci[0], fl)
    rep['leaves'] = rows
    # 3. kick doors
    nk = {}
    top = [k for k in range(1, len(sc.names)) if sc.path[k] == KICK_TOP]
    if len(top) != 1:
        raise ValueError('%s: %d nodes' % (KICK_TOP, len(top)))
    sub = [k for k in range(1, len(sc.names)) if sc.path[k].startswith(KICK_TOP + '\\')]
    hid = []
    for k in sub:
        e = B.ents[k - 1]
        nm = sc.names[k]
        if e.ref in KICK_REFS or (sc.cls(k) == 'ZSTDOBJ' and 'Arrow' in nm):
            if not e.flags & HIDE:
                e.flags |= HIDE
            hid.append(e.ref)
    if sorted(r for r in hid if r in KICK_REFS) != sorted(KICK_REFS) or len(hid) != 8:
        raise ValueError('kick door hide set %s (want the 2 leaves + 6 arrows)' % hid)
    nk['hidden_refs'] = sorted(hid)
    if kick == 'sink':
        for gr in KICK_GROUPS:
            k = node_of(B, gr)
            _lab, p = zgeom(B, k)
            gp = list(struct.unpack_from('<3f', B.ents[k - 1].trans, 0))
            if max(abs(p[i] - gp[i]) for i in range(3)) > 1:
                raise ValueError('kick group %d: prp %s != gms %s' % (gr, p, gp))
            put_place(B, k, (p[0], p[1] + SINK, p[2]), rows, 'kick group sink')
    rep['kick'] = dict(mode=kick, **nk)
    # 4. opening
    k_act, k_t, k_g1, k_g2, k_m, k_b = (node_of(B, NODES[n]) for n in ('act', 'timer', 'geo1', 'geo2', 'mon', 'trig'))
    want = {k_act: 'Activator_OLD_VanGo', k_t: 'TimerVanGo', k_g1: 'GeomActivator_Door_01', k_g2: 'GeomActivator_Door_02', k_m: 'Gameplay!AIMonitor', k_b: 'Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou'}
    for k, tail in want.items():
        if not sc.path[k].endswith(tail):
            raise ValueError('node %d is %s, not ...%s' % (k, sc.path[k], tail))
    targets = [sc.path[node_of(B, r)] for r in (LEAVES if via == 'leaves' else GROUPS)]
    fire = [sc.path[k_act], sc.path[k_g1], sc.path[k_g2]]

    def one_ctrl(k, key):
        ci = [i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == key]
        if len(ci) != 1:
            raise ValueError('%s: %d %s' % (sc.path[k], len(ci), key))
        return ci[0]

    def fa(us):
        if len(us) != 3 or kl_fa.value(sc, us[0]) != [] or kl_fa.value(sc, us[1]) != 'Activate':
            raise ValueError('Activator_OLD_VanGo is not AIDWrapper [[], Activate, 0]')
        us[0] = kl_fa._refs(sc, targets)
    kl_fa.edit(sc, k_act, one_ctrl(k_act, 'AIDWrapper'), fa)
    if variant == 'timer':
        def ft(us):
            if len(us) != 5 or kl_fa.value(sc, us[4]) != []:
                raise ValueError('TimerVanGo is not a TriggerDelay2 with an empty list')
            us[0] = [(0x0a, struct.pack('<f', delay))]
            us[4] = kl_fa._refs(sc, fire)
        kl_fa.edit(sc, k_t, one_ctrl(k_t, 'TriggerDelay2'), ft)

        def fm(us):
            lst = kl_fa.value(sc, us[2])
            if len(lst) != 19 or sc.path[k_t] in lst:
                raise ValueError('AIMonitor field 2: %d entries, TimerVanGo in it: %s' % (len(lst), sc.path[k_t] in lst))
            us[2] = kl_fa._refs(sc, lst + [sc.path[k_t]])
        kl_fa.edit(sc, k_m, one_ctrl(k_m, 'AIMonitor'), fm)
        rep['open'] = 'timer %.1f s after round start; fires %s -> %s (%s)' % (delay, [p.rsplit('\\', 1)[-1] for p in fire], [p.rsplit('\\', 1)[-1] for p in targets], via)
    else:
        lab = J.labels('dd', sc.cls(k_b))
        eb = B.ents[k_b - 1]
        if sc.parent[k_b] not in (0, sc.tops()[0] if False else sc.parent[k_b]) or max(abs(a - b) for a, b in zip(zgeom(B, k_b)[1], struct.unpack_from('<3f', eb.trans, 0))) > 1:
            raise ValueError('tb_RIGHT_TheySpotYou: prp place != gms place')
        c, hf = TRIG_BOX['centre'], TRIG_BOX['half']
        ident = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)

        def fb(us):
            AU.setv(sc, us, lab.index('ZGEOM[1]'), list(ident))
            AU.setv(sc, us, lab.index('ZGEOM[2]'), list(c))
            for i in range(3):
                AU.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), hf[i])
        kl_fa.edit(sc, k_b, None, fb)
        eb.rot = struct.pack('<9f', *ident) + eb.rot[36:]
        eb.trans = struct.pack('<3f', *c) + eb.trans[12:]

        def fl2(us):
            if len(us) != 18 or kl_fa.value(sc, us[17]) != []:
                raise ValueError('tb_RIGHT_TheySpotYou is not a TriggerBox with an empty list')
            us[17] = kl_fa._refs(sc, fire)
        kl_fa.edit(sc, k_b, one_ctrl(k_b, 'TriggerBox'), fl2)
        rep['open'] = 'trigger: tb_RIGHT_TheySpotYou at %s half %s fires %s -> %s (%s)' % (c, hf, [p.rsplit('\\', 1)[-1] for p in fire], [p.rsplit('\\', 1)[-1] for p in targets], via)
    # 5. guards
    if office:
        orows = []
        for gr, (old, new) in OFFICE.items():
            k = node_of(B, gr)
            _lab, p = zgeom(B, k)
            gp = list(struct.unpack_from('<3f', B.ents[k - 1].trans, 0))
            if max(abs(p[i] - old[i]) for i in range(3)) > 1 or max(abs(gp[i] - old[i]) for i in range(3)) > 1:
                raise ValueError('guard %d: prp %s / gms %s, not %s' % (gr, p, gp, old))
            put_place(B, k, new, orows, 'guard')
        rep['office'] = orows
    prp = sc.p.serialize()
    if F.Prp(prp).serialize() != prp:
        raise ValueError('the patched .prp does not round-trip')
    return prp


def part_scene(B, rep):
    """The .gms / .buf from the edited entity records. -> (packed gms, buf)."""
    A = B.scene
    slot0 = A.slots()
    if not all(a is b for a, b in zip(B.ents, A.entities())):
        raise ValueError('Built.ents are not the scene\'s entities')
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    gms, buf = A.write()
    if A.slots() != slot0 or [e.name for e in A.entities()] != [e.name for e in B.ents]:
        raise ValueError('slot ids / entity order changed')
    return kl_gms.pack(gms), buf


def part_hvk(B, M, rep):
    """The .HVK: the kick-door bodies cut, the four M05 door bodies appended (type 4, bound to the live REFs)."""
    h = kl_hvk.Hvk(B['.HVK'])
    n0, order0 = h.static_count(), [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst))]
    present = {kl_hvk.ref(i) for s in h.shapes for i in s.inst}
    if present & set(LEAVES):
        raise ValueError('a leaf REF is in the live .HVK already')
    if not set(KICK_REFS) <= present:
        raise ValueError('the kick-door bodies are not in the live .HVK')
    hm = kl_hvk.Hvk(M['.HVK'])
    donors = {}
    for s in hm.shapes:
        for i in s.inst:
            if kl_hvk.ref(i) in LEAVES.values():
                donors[kl_hvk.ref(i)] = (s, bytes(i))
    if sorted(donors) != sorted(LEAVES.values()):
        raise ValueError('M05 door bodies %s' % sorted(donors))
    kl_escape.cut_collision(h, set(KICK_REFS), log=lambda *a: None)
    for lr, mr in LEAVES.items():
        s, i0 = donors[mr]
        if s.type != kl_hvk.KEYFRAMED or len(s.inst) != 1 or len(s.verts) // 12 != 8:
            raise ValueError('M05 shape of %d is not a single 8-vertex type-4 slab' % mr)
        i = bytearray(i0)
        struct.pack_into('<I', i, 0x30, lr)
        h.shapes.append(s.clone([bytes(i)], []))
    data = h.serialize()
    h2 = kl_hvk.Hvk(data)
    if h2.serialize() != data or h2.static_count() != n0 or kl_mopp.statics(h2) != order0:
        raise ValueError('.HVK read-back differs')
    rep['hvk'] = collections.OrderedDict(static=n0, cut_type4=sorted(KICK_REFS), added_type4=sorted(LEAVES), bytes=(len(B['.HVK']), len(data)))
    return data


def build(live, outdir, variant='timer', delay=DEFAULT_DELAY, via='leaves', kick='silent', office=False, m05=M05, log=print):
    if variant not in ('timer', 'trigger') or via not in ('leaves', 'groups') or kick not in ('silent', 'sink'):
        raise ValueError('variant %s via %s kick %s' % (variant, via, kick))
    B = F.Built(live, SLOT)
    M = F.Built(m05, 'M05')
    rep = collections.OrderedDict(variant=variant, delay=delay, via=via, kick=kick, office=office, live=live, live_md5=md5(live))
    prp = part_nodes(B, M, variant, delay, via, kick, office, rep)
    gms, buf = part_scene(B, rep)
    hvk = part_hvk(B, M, rep)
    files = dict(B.files)
    files[B.ext['.prp']], files[B.ext['.gms']], files[B.ext['.buf']], files[B.ext['.HVK']] = prp, gms, buf, hvk
    os.makedirs(outdir, exist_ok=True)
    plain = os.path.join(outdir, 'F01_Main.zip')
    kl_graft.write_zip(plain, [(n, files[n]) for n in B.order])
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member list changed')
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    want = {'F01_Main.prp', 'F01_Main.gms', 'F01_Main.buf', 'F01_Main.HVK'}
    if not set(diff) <= want or not {'F01_Main.prp', 'F01_Main.gms', 'F01_Main.HVK'} <= set(diff):
        raise ValueError('members changed %s, expected within %s' % (diff, sorted(want)))
    rep['members_changed'] = diff
    kl_botsonline.convert(plain, os.path.join(outdir, 'F01_Main.bots.zip'), 'eAllTypes', SLOT, log=lambda *a: None)
    with open(os.path.join(outdir, 'F01_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(plain) + '\n')
    rep['out_md5'] = md5(plain)
    rep['bots_md5'] = md5(os.path.join(outdir, 'F01_Main.bots.zip'))
    log('lcdoors_1110 %s%s -> %s (%s) members %s' % (variant, '+office' if office else '', plain, rep['out_md5'], diff))
    return rep


# ---------------------------------------------------------------- checks
def _ctrl_map(B):
    sc = B.sc
    c, p = {}, {}
    for k in range(1, len(sc.names)):
        c[sc.path[k]] = [(sc.p.key(nm), [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])]) for nm, body in sc.nodes[k]['ctrls']]
        p[sc.path[k]] = kl_fa.node_values(sc, k)
    return c, p


def hvk_delta(zp_in, zp_out, cut_refs, added_refs):
    """Shape-by-shape: the new .HVK = the old one minus the shapes that held ONLY `cut_refs` placements, plus one type-4 placement per `added_refs`
    (each in a single-placement shape, appended last); every other shape record (incl. MOPP codes) identical and in order; box / static count / order / lists / tail equal."""
    def load(zp):
        with zipfile.ZipFile(zp) as z:
            return kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))
    a, b = load(zp_in), load(zp_out)
    bad = []
    sg = lambda s: (s.type, s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub), tuple(bytes(i) for i in s.inst), tuple(s.mopp))
    kept = [s for s in a.shapes if not all(kl_hvk.ref(i) in cut_refs for i in s.inst)]
    part = [s for s in a.shapes if any(kl_hvk.ref(i) in cut_refs for i in s.inst) and s in kept]
    if part:
        bad.append('a shape holds kick and other placements (cut_collision would have to rewrite it)')
    n = len(kept)
    if len(b.shapes) != n + len(added_refs):
        bad.append('shape count %d -> %d (kept %d + %d)' % (len(a.shapes), len(b.shapes), n, len(added_refs)))
    elif [sg(s) for s in kept] != [sg(s) for s in b.shapes[:n]]:
        bad.append('an old shape record changed')
    new = b.shapes[n:]
    if sorted(kl_hvk.ref(i) for s in new for i in s.inst) != sorted(added_refs) or any(s.type != kl_hvk.KEYFRAMED or len(s.inst) != 1 for s in new):
        bad.append('the added shapes are not one type-4 placement per ref %s' % sorted(added_refs))
    if set(kl_hvk.ref(i) for s in b.shapes for i in s.inst) & set(cut_refs):
        bad.append('a cut REF is still in the .HVK')
    if a.box != b.box or a.static_count() != b.static_count() or kl_mopp.statics(a) != kl_mopp.statics(b) or a.lists != b.lists or a.tail != b.tail:
        bad.append('box / static count / static order / list codes / tail changed')
    return bad


def key_report(N, refs=None):
    """{live REF: (pos at frame 0, pos at DOOR_LAST, frames)} decoded from the leaf KEYS in the built head."""
    ends = sorted({o for x in N.ents if x.raw for _p, oo in kl_graft.keys_tracks(x.raw) for o in oo} | {len(N.scene.head)})
    out = {}
    for lr in (refs or LEAVES):
        e = next(x for x in N.ents if x.ref == lr)
        K = ME.VanKeys(N.scene.head, e.raw, ends, kl_graft.keys_tracks)
        out[lr] = (tuple(K.pos[K.f2p[0]]), tuple(K.pos[K.f2p[min(DOOR_LAST, K.frames - 1)]]), K.frames)
    return out


def check(plain, live, variant, office=False, via='leaves', kick='silent', m05=M05, log=print):
    """Offline read-back of a built zip -> list of problems (empty = ok)."""
    bad = []
    A, N, M = F.Built(live, SLOT), F.Built(plain, SLOT), F.Built(m05, 'M05')
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
        if a.namelist() != b.namelist():
            bad.append('member list changed')
    if diff != ['F01_Main.HVK', 'F01_Main.gms', 'F01_Main.prp']:
        bad.append('members changed: %s (expected HVK / gms / prp; .buf and the trees stay)' % diff)
    for m in ('.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.buf'):
        if A[m] != N[m]:
            bad.append('%s changed' % m)
    if [e.name for e in A.ents] != [e.name for e in N.ents]:
        bad.append('entity names differ')
    sa, sn = A.scene.slots(), N.scene.slots()
    if [sa[e] for e in A.ents] != [sn[e] for e in N.ents]:
        bad.append('slot ids changed')
    # entities: only the intended ones differ, and only in trans / flags (rot for the trigger box)
    chg = {}
    for a, b in zip(A.ents, N.ents):
        same = (a.tid, a.model, a.aux, a.ref, a.group, a.raw, a.links is None) == (b.tid, b.model, b.aux, b.ref, b.group, b.raw, b.links is None)
        if not same:
            bad.append('entity %d changed beyond trans / flags / rot' % a.ref)
        if (a.trans, a.flags, a.rot) != (b.trans, b.flags, b.rot):
            chg[b.ref] = (a, b)
    exp = set(LEAVES) | set(KICK_REFS) | {a for a in range(0)}
    exp |= {e.ref for k in range(1, len(A.ents) + 1) for e in [A.ents[k - 1]] if A.sc.path[k].startswith(KICK_TOP + '\\') and A.sc.cls(k) == 'ZSTDOBJ' and 'Arrow' in A.sc.names[k] and not e.flags & HIDE}
    if kick == 'sink':
        exp |= set(KICK_GROUPS)
    if variant == 'trigger':
        exp.add(NODES['trig'])
    if office:
        exp |= set(OFFICE)
    if set(chg) != exp:
        bad.append('entities changed: +%s -%s' % (sorted(set(chg) - exp), sorted(exp - set(chg))))
    mp = m05_leaf_places(M)
    for lr, mr in LEAVES.items():
        if lr not in chg:
            bad.append('leaf %d not changed' % lr)
            continue
        a, b = chg[lr]
        if a.flags != b.flags or a.rot != b.rot or b.trans[12:] != a.trans[12:]:
            bad.append('leaf %d: flags / rot / tail changed' % lr)
        g = struct.unpack_from('<3f', b.trans, 0)
        if max(abs(g[i] - mp[mr][2][i]) for i in range(3)) > 0.01:
            bad.append('leaf %d: .gms place %s != M05 %s' % (lr, g, mp[mr][2]))
        k = node_of(N, lr)
        if max(abs(zgeom(N, k)[1][i] - mp[mr][1][i]) for i in range(3)) > 0.01:
            bad.append('leaf %d: .prp place %s != M05 %s' % (lr, zgeom(N, k)[1], mp[mr][1]))
        # world place = M05's (the same frames chain in both builds)
        wl, wm = N.fr[N.ents[k - 1]][1], M.fr[M.ents[node_of(M, mr) - 1]][1]
        if max(abs(wl[i] - wm[i]) for i in range(3)) > 0.5:
            bad.append('leaf %d: world place %s != M05 %s' % (lr, [round(v, 1) for v in wl], [round(v, 1) for v in wm]))
    for r in [x for x in exp if x not in LEAVES and x not in KICK_GROUPS and x not in OFFICE and x != NODES['trig']]:
        if r not in chg:
            continue
        a, b = chg[r]
        if b.flags != a.flags | HIDE or a.trans != b.trans:
            bad.append('hidden entity %d: flags %#x -> %#x' % (r, a.flags, b.flags))
    # keys: frame 0 sits at the leaf's own place, frame DOOR_LAST slides it along the wall
    for lr, (p0, p1, nfr) in key_report(N).items():
        g = struct.unpack_from('<3f', next(x for x in N.ents if x.ref == lr).trans, 0)
        if nfr < DOOR_LAST + 1 or max(abs(p0[i] - g[i]) for i in range(3)) > 0.5 or math.dist(p0, p1) < 20.0:
            bad.append('leaf %d keys: frame 0 %s, frame %d %s, node %s (%d frames)' % (lr, [round(v, 1) for v in p0], DOOR_LAST, [round(v, 1) for v in p1], [round(v, 1) for v in g], nfr))
    # .prp: only the intended nodes change
    ca, pa = _ctrl_map(A)
    cb, pb = _ctrl_map(N)
    if list(ca) != list(cb):
        bad.append('node list changed')
    sc = N.sc
    P = lambda r: sc.path[node_of(N, r)]
    allowed = {P(r) for r in LEAVES} | {P(NODES['act'])}
    if variant == 'timer':
        allowed |= {P(NODES['timer']), P(NODES['mon'])}
    else:
        allowed |= {P(NODES['trig'])}
    cc = {p for p in ca if ca[p] != cb[p]}
    if cc != allowed:
        bad.append('controllers changed on +%s -%s' % (sorted(cc - allowed)[-3:], sorted(allowed - cc)[-3:]))
    pc = {p for p in pa if pa[p] != pb[p]}
    pexp = {P(r) for r in LEAVES} | ({P(NODES['trig'])} if variant == 'trigger' else set()) | ({P(r) for r in OFFICE} if office else set()) | ({P(r) for r in KICK_GROUPS} if kick == 'sink' else set())
    if pc != pexp:
        bad.append('node properties changed on +%s -%s' % (sorted(pc - pexp)[-3:], sorted(pexp - pc)[-3:]))
    for r in LEAVES:
        mpa = [c for c in cb[P(r)] if c[0] == 'MatPosAnim']
        ma = [c for c in ca[P(r)] if c[0] == 'MatPosAnim']
        if len(mpa) != 1 or mpa[0][1][MPA_LAST] != DOOR_LAST or mpa[0][1][:MPA_LAST] != ma[0][1][:MPA_LAST] or mpa[0][1][MPA_LAST + 1:] != ma[0][1][MPA_LAST + 1:]:
            bad.append('leaf %d MatPosAnim: %s' % (r, mpa))
    tg = [P(r) for r in (LEAVES if via == 'leaves' else GROUPS)]
    aw = [c for c in cb[P(NODES['act'])] if c[0] == 'AIDWrapper']
    if len(aw) != 1 or aw[0][1][0] != tg or aw[0][1][1] != 'Activate':
        bad.append('Activator_OLD_VanGo: %s' % aw)
    fire = [P(NODES['act']), P(NODES['geo1']), P(NODES['geo2'])]
    if variant == 'timer':
        t = [c for c in cb[P(NODES['timer'])] if c[0] == 'TriggerDelay2']
        if len(t) != 1 or t[0][1][4] != fire or t[0][1][0] <= 0.5:
            bad.append('TimerVanGo: %s' % t)
        m = [c for c in cb[P(NODES['mon'])] if c[0] == 'AIMonitor'][0][1][2]
        m0 = [c for c in ca[P(NODES['mon'])] if c[0] == 'AIMonitor'][0][1][2]
        if m != m0 + [P(NODES['timer'])]:
            bad.append('AIMonitor start list: %d -> %d' % (len(m0), len(m)))
    else:
        t = [c for c in cb[P(NODES['trig'])] if c[0] == 'TriggerBox']
        if len(t) != 1 or t[0][1][17] != fire or t[0][1][13:17] != ['eTGS_AllInside', 'ECPS_FA_MERCONLY', 0, 'EFAMPS_ALL_MODES']:
            bad.append('tb_RIGHT_TheySpotYou: %s' % t)
        k = node_of(N, NODES['trig'])
        lab = J.labels('dd', sc.cls(k))
        nv = kl_fa.node_values(sc, k)
        if [nv[lab.index('ZBoxPrimitive[%d]' % i)] for i in range(3)] != list(TRIG_BOX['half']) or [round(x, 3) for x in nv[lab.index('ZGEOM[2]')]] != list(TRIG_BOX['centre']):
            bad.append('trigger box place / size: %s' % nv)
    if office:
        for gr, (_old, new) in OFFICE.items():
            if max(abs(a - b) for a, b in zip(zgeom(N, node_of(N, gr))[1], new)) > 0.01 or max(abs(a - b) for a, b in zip(struct.unpack_from('<3f', N.ents[node_of(N, gr) - 1].trans, 0), new)) > 0.01:
                bad.append('guard %d not at %s' % (gr, new))
    # no dangling references: every node path named in a controller exists
    names = set(cb)
    for p, cs in cb.items():
        if p in {P(r) for r in list(LEAVES) + [NODES['act'], NODES['timer'], NODES['mon'], NODES['trig']]}:
            for nm, v in cs:
                for x in v:
                    if isinstance(x, list):
                        for s in x:
                            if isinstance(s, str) and s.startswith('ROOT') and s not in names:
                                bad.append('%s names missing node %s' % (p[-30:], s))
    # the .HVK
    bad += ['hvk: ' + x for x in hvk_delta(live, plain, set(KICK_REFS), sorted(LEAVES))]
    # bots: the loot census does not move
    mo = lambda X: [(o['node'], o['amount'], o['kind'], o['container']) for o in F.money_objects(X)]
    if mo(A) != mo(N):
        bad.append('bots: the money census changed')
    return bad


def clearance(live, plain, rep, radius=3500.0, log=print):
    """Walker proof (kl_route, kl_doors_clear_1108._flood): every real ZSpawnPoint within `radius` of the doors.
    open(out) must equal open(live) (the live map with the kick bodies gone): the map is the same once the doors are open;
    closed(out) is a subset; for the trigger variant every spawn that reaches the front-office side must reach the trigger box while the doors are shut. -> problems."""
    import kl_route as R
    import kl_doors_clear_1108 as C
    Bo, Bl = F.Built(plain, SLOT), F.Built(live, SLOT)
    run_out, run_live = R._Run(plain, mesh=False), R._Run(live, mesh=False)
    centre = (2000.0, 0.0, 3313.0)
    starts = [s for s in C.spawn_points(Bo) if math.hypot(s[2][0] - centre[0], s[2][2] - centre[2]) <= radius and abs(s[2][1] - 358) < 400]
    gone_out = frozenset(LEAVES)
    gone_live = frozenset(KICK_REFS)
    box = TRIG_BOX
    inbox = lambda c: abs((c[0] + 0.5) * R.CELL - box['centre'][0]) <= box['half'][0] and abs((c[1] + 0.5) * R.CELL - box['centre'][2]) <= box['half'][2]
    bad, rows = [], []
    for k, n, p in starts:
        c_closed, f1 = C._flood(run_out, p, frozenset(), radius=radius)
        c_open, f2 = C._flood(run_out, p, gone_out, radius=radius)
        l_open, f3 = C._flood(run_live, p, gone_live, radius=radius)
        row = dict(start=n, pos=[round(v) for v in p], closed=len(c_closed), open=len(c_open), live_open=len(l_open), floor=bool(f1 and f2 and f3))
        if not row['floor']:
            row['note'] = 'no floor at the start'
        else:
            gated = len(c_open - c_closed)
            row['gated'] = gated
            if c_open != l_open:
                bad.append('%s: open map %d cells != live (kick bodies gone) %d' % (n, len(c_open), len(l_open)))
            if not c_closed <= c_open:
                bad.append('%s: closed reaches cells the open map does not' % n)
            if any(inbox(c) for c in c_open) and not any(inbox(c) for c in c_closed):
                row['box_reached_closed'] = False
                rep.setdefault('trigger_unreachable', []).append(n)
            else:
                row['box_reached_closed'] = True
        rows.append(row)
        log('  %-30s %5s  closed/open/live-open %d/%d/%d  gated %s  box-before-doors %s' % (n[-30:], row['pos'], row['closed'], row['open'], row['live_open'], row.get('gated'), row.get('box_reached_closed')))
    rep['clearance'] = rows
    return bad


# ---------------------------------------------------------------- install.py / stage
INSTALL_PY = r'''r"""Installs / undoes LAST CALL FRONT-OFFICE DOORS 1110 (luvsic's sliding doors at the loot room, DM05A).
  python install.py                      install the default variant (%(default)s) from the staged files (originals -> <name>%(tag)s; an existing backup is NEVER overwritten)
  python install.py --variant %(vars)s   pick the variant (timer: opens %(delay)s s after the round starts; trigger: the first heister in the lobby / office box opens them; timer_office: timer + the guards back in the front office)
  python install.py --undo               put the originals back byte for byte (only when each live file is exactly what an install wrote)
  python install.py --dry                read-only: print every pin and what would happen (also with --undo)
  --game <dir>  other Dog Days folder (rehearsals); --skip-run-check for those only
Pins: live F01_Main.zip %(live)s, bots %(bots)s, base %(base)s (re-stage if another layer changed them).
Nothing is written while a kl2.exe with threads runs. Never touches KL_PortBackup or any other file. Undo this layer BEFORE any layer installed earlier on DM05A."""
import hashlib, json, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
TAG = '%(tag)s'
NAMES = ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')
OLD = {'F01_Main.zip': '%(live)s', 'F01_Main.bots.zip': '%(bots)s'}
OLD_BASE_TEXT = '%(base)s'
DEFAULT = '%(default)s'
STAGED = %(staged)s      # variant -> {name: md5}
STATE = os.path.join(HERE, 'installed.json')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', "(Get-Process kl2 -ErrorAction SilentlyContinue | ForEach-Object { $_.Threads.Count } | Measure-Object -Sum).Sum"],
                             capture_output=True, text=True).stdout.strip()
        return bool(out) and int(float(out)) > 0
    except (OSError, ValueError):
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    variant = a[a.index('--variant') + 1] if '--variant' in a else DEFAULT
    if variant not in STAGED:
        print('REFUSED: --variant takes %%s' %% ', '.join(sorted(STAGED))); return 1
    d = os.path.join(game, 'KLExpansion', 'Maps', 'DM05A')
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    live = {n: os.path.join(d, n) for n in NAMES}
    bak = {n: live[n] + TAG for n in NAMES}
    for n in NAMES:
        if not os.path.isfile(live[n]):
            print('REFUSED: %%s is not there' %% live[n]); return 1
    if undo:
        if not os.path.isfile(STATE):
            print('REFUSED: no installed.json here (nothing was installed from this folder)'); return 1
        st = json.load(open(STATE))
        for n in NAMES:
            cur = md5(live[n])
            print('%%-26s live %%s' %% (n, cur))
            if cur != st['new'][n]:
                print('REFUSED: %%s live md5 %%s is not the installed %%s (another layer changed it: undo that one first)' %% (n, cur, st['new'][n])); return 1
            if not os.path.isfile(bak[n]) or md5(bak[n]) != st['old'][n]:
                print('REFUSED: backup %%s missing or not %%s' %% (bak[n], st['old'][n])); return 1
        if dry:
            print('would restore', ', '.join(NAMES)); return 0
        for n in NAMES:
            shutil.copyfile(bak[n], live[n] + '.tmp'); os.replace(live[n] + '.tmp', live[n]); os.remove(bak[n])
            print('%%s: restored %%s' %% (n, md5(live[n])))
        os.remove(STATE)
        return 0
    cur = {n: md5(live[n]) for n in NAMES}
    for n in NAMES:
        print('%%-26s live %%s' %% (n, cur[n]))
    if os.path.exists(STATE):
        print('REFUSED: installed.json exists: this folder was installed already (use --undo first)'); return 1
    if cur['F01_Main.zip'] != OLD['F01_Main.zip'] or cur['F01_Main.bots.zip'] != OLD['F01_Main.bots.zip'] or open(live['F01_Main.bots.base.md5']).read().strip() != OLD_BASE_TEXT:
        print('REFUSED: a live DM05A file is not the pinned one (%%s / %%s / base %%s): another layer changed it: re-stage on the live files' %% (
            OLD['F01_Main.zip'], OLD['F01_Main.bots.zip'], OLD_BASE_TEXT)); return 1
    for n in NAMES:
        if os.path.exists(bak[n]):
            print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak[n]); return 1
    src = os.path.join(HERE, 'variant_' + variant)
    new = {n: (md5(os.path.join(src, n)) if os.path.isfile(os.path.join(src, n)) else None) for n in NAMES}
    if None in new.values() or any(new[n] != STAGED[variant][n] for n in NAMES):
        print('REFUSED: staged files in %%s are missing or not the md5 the stage recorded' %% src); return 1
    if open(os.path.join(src, 'F01_Main.bots.base.md5')).read().strip() != new['F01_Main.zip']:
        print('REFUSED: base sidecar is not the md5 of the staged zip'); return 1
    need = sum(os.path.getsize(os.path.join(src, n)) + os.path.getsize(live[n]) for n in NAMES) + (1 << 30)
    if shutil.disk_usage(d).free < need:
        print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        print('would install variant', variant, 'from', src); return 0
    done = []
    try:
        for n in NAMES:
            shutil.copyfile(live[n], bak[n]); done.append(n)
            shutil.copyfile(os.path.join(src, n), live[n] + '.tmp'); os.replace(live[n] + '.tmp', live[n])
            print('%%s: installed %%s' %% (n, md5(live[n])))
    except OSError as e:
        for n in reversed(done):
            shutil.copyfile(bak[n], live[n]); os.remove(bak[n])
        print('FAILED (%%s); originals put back' %% e); return 2
    json.dump({'variant': variant, 'old': {n: md5(bak[n]) for n in NAMES}, 'new': {n: md5(live[n]) for n in NAMES}}, open(STATE, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''

README = r'''LAST CALL FRONT-OFFICE DOORS 1110 (DM05A, slot F01)           built OFFLINE, NOT installed, NOT run in the game
================================================================================================================
What it does: luvsic's two sliding door pairs at the loot room (outer pair x 1500, inner pair x 2500, Yoko's front office) come back. Our map had
their four key-framed leaves buried 15 m down; they are raised to M05's height, get a collision body each (a type-4 slab cloned from M05's own door bodies)
and slide open on their own keys (MatPosAnim last frame 30: open and stay open). Our kick doors in the same doorways (ROOT\KL_Interact!1) are hidden and their
bodies cut, but the nodes stay (33 bot steps / squad nodes name them). Variants (install.py --variant ...):
  timer         (DEFAULT, safest) the doors open %(delay)s s after the round starts (AIMonitor -> TimerVanGo -> Activator_OLD_VanGo + the two muffle GeomActivators).
  trigger       (recommended off) the first heister inside the box x 900..2500, z 3013..3613 (lobby side + front office) opens them (tb_RIGHT_TheySpotYou, moved).
  timer_office  (recommended off until benched) timer + the WaitingRoom / YokoGuards guards back in the front office at M05's places (position only).
Other knobs (python tools/kl_lc_doors_1110.py build ...): --delay N, --via leaves|groups, --kick silent|sink (sink = recommended off).
Undo: UNDO lcdoors 1110.bat (byte exact), BEFORE any layer installed earlier on DM05A (the live md5 must be the one this wrote).

Install (game closed):  INSTALL lcdoors 1110.bat           or   python install.py [--variant trigger|timer_office] [--dry] [--game <dir> --skip-run-check]
Pins: live F01_Main.zip %(live)s, bots %(bots)s, base %(base)s.   Backups: <name>%(tag)s next to the live files.
Staged: %(staged_txt)s

UNDO ALL 1105.bat entry (a new step ABOVE 0zb; do not edit that file from here): run before every older DM05A step
    python "C:\kl_build_1024\lcdoors_1110\install.py" --undo        (step 0zc)

Proven offline (tools/kl_lc_doors_1110.py check + tools/kl_lc_doors_1110_test.py + the stage report):
 - only the .prp / .gms / .HVK members change (.buf, .oct, .rmi, .rmc, .prm, .MAT, .TEX, all other members identical); the %(ents)s entity slots and names are identical;
 - entities that differ: the four leaves (translation only: .gms and .prp place = M05's, world place = M05's), the 2 kick leaves + 6 arrows (flags | 0x400 only), the
   variant's own (trigger box / guards / sunk groups); .prp: only those nodes' places and the controllers on the leaves, Activator_OLD_VanGo and TimerVanGo + AIMonitor
   (timer) or the trigger box (trigger); every named node path exists;
 - the four leaf KEYS decode to the leaf's own place at frame 0 and slide it along the wall at frame 30; the MatPosAnim differs from the live one in field 14 only;
 - .HVK: every old shape record except the kick-door shape (REF 39763 + 39786, cut) identical and in order; static count, static order (kl_mopp), list codes, box and tail
   equal; exactly four new type-4 single-placement shapes (live REFs 23812 / 23813 / 23815 / 23816) appended;
 - clearance walk (kl_route) from every real ZSpawnPoint within 3.5 m of the doors: with the doors open the reachable map equals the live map's (kick bodies gone);
   shut, nothing extra is reachable; see build_report.json 'clearance' (cells gated by the doors per spawn);
 - bots zip re-derived (eAllTypes); money census unchanged; debug/check.py 0 bad; check_passes PASS; scratch install / 2nd install refused / undo byte exact.

GUESSes (not provable offline - the bench decides):
%(guesses)s

BENCH PLAN (later, owner not playing; one bench at a time; tools/kl_bench_1106.py or kl_solo_test on the TEST dll, never the SHIP one):
 0. df C: and the game drive; python install.py --dry; install the variant (INSTALL bat). Bench kit: the live ini, KLShopPage.ini staged, [Script] edited in place.
 1. SOLO, DM05A, timer: walk to the front office; shot 1 the outer doors CLOSED and DRAWN at x 1500 (GUESS 1); walk into them: blocked (GUESS 2). At %(delay)s s (+2):
    shot 2 doors slid open, walk in: free; the inner pair too. No kick prompt visible on the doors (GUESS 5). Log: 0 asserts / faults / dumps; the doors stay open 60 s more.
 2. Bots: online FA with bots: they must not jam at a closed door for the whole delay (GUESS 4, 6); after the open they loot. If they jam: lower --delay or use trigger.
 3. 2 SEATS: both seats see the slide at the same time +-1 s (the keys play on the client too).
 4. trigger variant: the first heister stepping into the box opens them; a second entry (GUESS 9); a client inside the box (GUESS 8). 5. timer_office: the guards stand in the
    front office, no spawn on top of them, they fight normally. 6. Round 2: the doors are shut again (scene reload) and open again.
 If the leaves are not DRAWN or not BLOCKING: undo; the scenery-only fallback of re/lastcall_mizuki_1110.md option 3 remains.

Change the delay: python tools/kl_lc_doors_1110.py stage --delay 30   (re-stages every variant on the CURRENT live files, repins).
'''


def stage(live_dir, out, delay=DEFAULT_DELAY, clear=True, log=print):
    live = os.path.join(live_dir, 'F01_Main.zip')
    bots = os.path.join(live_dir, 'F01_Main.bots.zip')
    if md5(live) != LIVE_PIN or md5(bots) != LIVE_BOTS_PIN:
        raise SystemExit('live DM05A zip / bots zip are not the pinned %s / %s (another layer changed them: re-pin on the live md5s)' % (LIVE_PIN, LIVE_BOTS_PIN))
    base = open(os.path.join(live_dir, 'F01_Main.bots.base.md5')).read().strip()
    if base != LIVE_BASE_PIN:
        raise SystemExit('live bots.base.md5 is %s, not %s' % (base, LIVE_BASE_PIN))
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    reps, staged = {}, {}
    for v in VARIANTS:
        d = os.path.join(out, 'variant_' + v)
        var, office = ('timer', True) if v == 'timer_office' else (v, False)
        reps[v] = build(live, d, var, delay, 'leaves', 'silent', office, log=log)
        bad = check(os.path.join(d, 'F01_Main.zip'), live, var, office)
        if clear:
            bad += clearance(live, os.path.join(d, 'F01_Main.zip'), reps[v], log=log)
        if var == 'trigger' and reps[v].get('trigger_unreachable'):
            bad.append('trigger variant: spawns that cannot reach the box before the doors open: %s' % reps[v]['trigger_unreachable'])
        if bad:
            raise SystemExit('check failed (%s): %s' % (v, bad))
        staged[v] = {n: md5(os.path.join(d, n)) for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')}
        reps[v]['check'] = 'ok'
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(tag=TAG, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, staged=repr(staged), default=DEFAULT_VARIANT, vars='|'.join(VARIANTS), delay='%.0f' % delay))
    for nm, arg in (('INSTALL lcdoors 1110', ''), ('UNDO lcdoors 1110', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    st = ' | '.join('%s zip %s bots %s' % (v, staged[v]['F01_Main.zip'][:8], staged[v]['F01_Main.bots.zip'][:8]) for v in VARIANTS)
    with open(os.path.join(out, 'README.txt'), 'w', newline='\n') as fh:
        fh.write(README % dict(delay='%.0f' % delay, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, tag=TAG, staged_txt=st, ents=len(F.Built(live, SLOT).ents),
                               guesses='\n'.join(' %d. GUESS: %s' % (i + 1, g) for i, g in enumerate(GUESSES))))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(dict(reports=reps, staged=staged), fh, indent=1, default=str)
    log(json.dumps(staged, indent=1))
    return reps, staged


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    live = opt('--live', os.path.join(MAPDIR, 'F01_Main.zip'))
    if a and a[0] == 'build':
        out = opt('--out', OUT)
        v, office = opt('--variant', DEFAULT_VARIANT), '--part' in a and a[a.index('--part') + 1] == 'office'
        rep = build(live, out, v, float(opt('--delay', DEFAULT_DELAY)), opt('--via', 'leaves'), opt('--kick', 'silent'), office)
        bad = check(os.path.join(out, 'F01_Main.zip'), live, v, office, opt('--via', 'leaves'), opt('--kick', 'silent'))
        if bad:
            print('check failed:', *bad, sep='\n'); return 1
        return 0
    if a and a[0] == 'stage':
        stage(opt('--live', MAPDIR), opt('--out', OUT), float(opt('--delay', DEFAULT_DELAY)), '--no-clear' not in a)
        return 0
    if len(a) >= 2 and a[0] == 'check':
        office = '--part' in a and a[a.index('--part') + 1] == 'office'
        bad = check(a[1], live, opt('--variant', DEFAULT_VARIANT), office, opt('--via', 'leaves'), opt('--kick', 'silent'))
        if '--deep' in a:
            bad += clearance(live, a[1], {})
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
