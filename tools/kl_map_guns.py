#!/usr/bin/env python3
"""
Gun looks (tools/kl_guns.py) on FINISHED map builds - wardrobe builds included - and what the enemies carry.
Spec, findings and the live checks: re/map_guns.md. Offline; nothing here was run in the game.

    python kl_map_guns.py build <build folder> <out folder> [--start=1] [--set=1] [--level=M01_FA_A] [--extra]
                                        [--no-fit] [--no-sound] [--first-pairs]
                                        the folder's level with the looks; KLGuns.ini (Version 2), guns.json,
                                        map_guns.json, steps.json brought up to date, preflight and audit run again
                                        --no-fit: the looks as kl_guns puts them (10 degrees nose-up in the hands)
                                        --no-sound: every gun keeps its own sound whatever it shows
                                        --first-pairs: the P90 on the UMP as in the first builds
    python kl_map_guns.py fit           the pairings in centimetres (grip, support hand, magazine, length), and per
                                        look the Dog Days guns that fit best; from stock F01 and M01_FA_A
    python kl_map_guns.py sheet <folder> <out.png>   per look: Dog Days gun | look as kl_guns put it | as built | over
                                        each other; yellow = the right hand and the Dog Days gun's support-hand place
    python kl_map_guns.py all [--start=1] [--set=1] [--out=t_guns] [--extra] [M02 RT ...]
                                        the five builds of BUILDS -> <work>/build/t_guns/<tag>
                                        --extra: also the looks of EXTRA below (Mini-14, Taurus): an experiment, not fit to ship
    python kl_map_guns.py check <folder>    the checks of a folder built here (exit 1 on a problem)
    python kl_map_guns.py weapons <folder>  every weapon template: is its model drawn, who carries it, which
                                        look it shows (works on any build or stock level name)
    python kl_map_guns.py sizes <folder> ...  .prm / .ANM / .fxc / .WAV, chunk table entries

WHY A WRAPPER (2026-10-10; the owner on Late Night Opening: 'dead men guns dont show up')
  1 The map builds were made without kl_guns: no KLGuns.ini beside the archive, so the Guns page had nothing to
    switch (KLHook.log of the owner's session: 30 'guns: menu set ...' lines, not one 'guns: level ... has').
  2 kl_guns alone would not have shown them either, and would have made things worse. It hides a look's parts
    by giving them a variant byte (100 + n) that 'matches nothing'. kl2.exe does not work that way
    (0x67cc60, the walk over a model's mesh objects, 0x67cf77..0x67cf91; the same at 0x57ee43..0x57ee7a):
        test dword [object+0x1c], 0x800000 -> skip          a HIDE bit in the object's draw-mode word
        al = byte [node+0x158]                              the entity's variant
        if al != 0: cmp byte [object+0x0f], al -> jne skip  variant 0 on the entity takes EVERY object
    A gun entity's variant is 0 (all 61 templates' Ground of every build here), so every part of every look
    is taken whatever its variant byte: the Zastava, the MP5 and the AK-74 in one another, on every such gun,
    and klgun.c's variant-byte writes change nothing. (Static reading; the build was never run.)
  3 What decides is the HIDE bit: 0x00800000 of the mesh object's dword +0x1c. All four walkers of kl2.exe that
    take a mesh object out of the chunk table test it first (0x57ee43, 0x67cf77, 0x7581e1, 0x7af091), and stock
    Dog Days uses it on 4,432 mesh objects of five levels looked at (F01 711, F02 459, F07 856, L03 1196,
    L10 1210; 24 of them rigid parts like a gun's).
  So this step runs kl_guns.build() and then sets the hide bit on every part of the groups that are not to be
  seen. WHICH look a build shows is decided HERE, at build time (--start / --set, the same numbers as the Guns
  page: KLGunStart 0..2, KLGunSet 0..1): no hook is needed for a Dead Men gun to be in the hands.
  Switching in the menu needs klgun.c to flip that bit instead of the variant byte (re/map_guns.md 5; klhook is
  not this tool's file). KLGuns.ini is written as Version=2 for that; the hook installed today accepts
  Version 1 only and leaves a Version 2 file alone, so with it the build shows what was baked.

WHAT THE STEP CHANGES (beyond kl_guns.build)
  .prm   the stock parts of each of the six gun models become PRIVATE copies (64 bytes each, 35 in all; the
         geometry below is shared) so that a hide bit set here - or flipped by a hook later - never reaches
         another model that names the same mesh object; the object table is rewritten in place.
         Hide bit on the parts of every group but the shown one.
  .MAT   the reference counts (kl_texmat.material_refs), as kl_guns does.
  Nothing else. kl_guns.build() itself adds the Dead Men gun models (into DEAD chunk indices: kl_chars.put
  with reuse), 59 chunks at the end of the table (part copies, roots, object tables) and the guns' textures.

SECOND PASS (2026-10-10, after the owner SAW the first build: the MP5 alone in the hands = the hide bit works live;
'it holds the mp5 weird ... i dont like how it uses the ak sound too'). The numbers are at HOUSE_DEG / LOOKS below.
  THE FIT    Dog Days holds a gun 10 degrees nose-down against Dead Men's model space (measured on the three guns
         both games ship as one mesh). Each Dead Men look is turned and shifted into that hold: its parts get
         geometry of their own (sub table + descriptor + vertex chunk, 3 chunks a part, about 0.4 MB in all; the
         index chunk stays shared), positions and the packed normal / tangent / binormal turned alike.
  PAIRINGS   by `fit`: the P90 moves from the UMP to the Type 05 (the UMP has no look now).
  THE SOUND  a template's ONE sound field (type 46, an offset into the level's .SND) names a '#def' of 13 slots (dry
         fire, shot heard from others, fly-by, shot of the player, shell drop, pick up ammo, weapon change). A gun
         that SHOWS a look of another class gets the field of a stock Dog Days gun of that class (the Zastava as an
         MP5: the Type 79's). .prp only; .SND, .WHD and .WAV are byte for byte the source's. The RELOAD sound is not
         in that definition (the '.../reload/...#seq' objects of the bank are named by no .prp field): it stays the
         Dog Days gun's, as the reload animation does.
  The sound is baked for the SHOWN look. A hook that switches looks in the menu (klgun.c, Version 2) changes what is
  seen, not what is heard.
"""
import collections, json, math, os, struct, sys, zipfile, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_chars as C, kl_guns as K, kl_prmgraph as G, kl_texmat as T, kl_impact
from kl_port_check import workdir
from kl_prp import units

BS = chr(92)
HIDE_OFF, HIDE_BIT = 0x1c, 0x00800000            # kl2 0x67cf77: test dword [object+0x1c], 0x800000 -> not taken
START, SET = 1, 1                                # what a build shows unless told: the Dead Men looks (the owner asked to SEE them)
BUILDS = collections.OrderedDict([               # tag -> finished build folder under <work>/build
    ('M01', 'z_maps/M01'), ('M02', 'z_maps/M02'), ('M03', 'z_maps/M03'), ('M06', 'z_maps/M06'), ('RT', 'rt_ai2/retomoto_ai2')])
START_ITEM = 29                                  # klgun.c KLG_START_ITEM: the gun KLGunStart is about (Rifle_zastavam85)
# Looks kl_guns.LOOKS does not have (--extra). NOT FIT TO SHIP, kept as the experiment it was (re/map_guns.md 6):
# the build passes every check, but seen with kl_view (kl_guns.py sheet) the Mini-14 lies about 30 degrees nose-up
# against the Type 88 (its parts are not in the model space kl_guns assumes) and the Taurus is about 1.4 times the
# Colt's size. The pairings are this tool's GUESSES, not the owner's.
# kl_guns says the Mini-14 and the Taurus are 'in no Dead Men level's equipment tree': they are in M01_FA_A's, but
# their model object is named Ground01 (as Dog Days' three revolvers'), which kl_guns.gun_node does not look for.
EXTRA = [
    ('Rifle_Type88', 34, [('Mini-14', 'dm', 'Rifle_RugerMini14_01')]),   # GUESS: both semi-automatic rifles
    ('HG_ColtCobra',  5, [('Taurus', 'dm', 'Gun_Taurus_01')]),           # GUESS: the revolver the shop sells
]


# ------------------------------------------------------------------ the pairings, the fit and the sound (2026-10-10, second pass)
# The owner on the first build that showed a look (rt_guns/retomoto_ai2_guns): 'it holds the mp5 weird ... i dont like how
# it uses the ak sound too'. Both are answered here; the measurements and the reasons are in re/map_guns.md 8.
# Dog Days template, item, [(label, game, template whose parts the look gets, the look's weapon class, sound donor or None)]
#   class: WT_ enum name of what the look IS. When it differs from the Dog Days gun's own class the template's sound
#   definition is re-pointed to a stock Dog Days gun of the look's class (SOUND_OF), unless a donor is named here.
#   donor: a Dog Days template whose sound definition the gun takes while it shows this look (the AK-74 look is Dog
#   Days' own AK-74: it sounds like it).
LOOKS = [
    ('Rifle_zastavam85', 29, [('MP5', 'dm', 'Smg_MP5-A3_01', 'WT_SUBMACHINEGUN', None), ('AK-74', 'dd', 'Rifle_AK74', 'WT_RIFLE', 'Rifle_AK74')]),
    ('Rifle_FN_SCAR',    30, [('SG 552', 'dm', 'Rifle_SG552_01', 'WT_RIFLE', None)]),
    ('Rifle_AK47',       31, [('M4A1', 'dm', 'Rifle_M4A1_01', 'WT_RIFLE', None)]),
    ('SMG_Type05',       27, [('P90', 'dm', 'Smg_FN_P90_01', 'WT_SUBMACHINEGUN', None)]),      # RE-PAIRED, was on SMG_UMP (item 20): see below
    ('SMG_MAC_10',       23, [('Steyr TMP', 'dm', 'Smg_SteyrTMP_01', 'WT_SUBMACHINEGUN', None)]),
    ('HG_M9Beretta',      8, [('USP', 'dm', 'HG_HK_USP_01', 'WT_PISTOL', None)]),
]
# THE PAIRINGS, by `python kl_map_guns.py fit` (the table is in re/map_guns.md 8). Five of the six first pairings stay:
# after the fit the support hand of each is within 2 cm of its place along the barrel. The P90 is MOVED from the UMP to
# the Type 05: on the UMP the left hand is 15 cm in front of the P90's fore grip (past its muzzle); the Type 05 is a
# short bullpup of the P90's length (x0.99) whose support hand is 1.5 cm from the P90's along the barrel. Still the
# worst of the six (the P90's fore grip is 8 cm lower than the Type 05's hand place, its magazine lies on top).
# The MP5 stays on the Zastava (the starting rifle: the owner equips it): its support hand lands 0.8 cm from the
# Zastava's; the 18 cm it has behind the grip is its stock, which the Zastava folds - it ends where the UMP's stock
# ends, and the UMP has the Zastava's skeleton to the last digit (ASSUMPTION that the two are then shouldered alike).
# --first-pairs builds the table of 2026-10-09 (P90 on the UMP) instead.
FIRST_PAIRS = {'Smg_FN_P90_01': ('SMG_UMP', 20)}
# class of a look -> stock Dog Days templates to borrow the sound definition from, in order of preference (the first
# the level has, that is not the gun itself, not silenced and of that class in the level). GUESSES by calibre and kind:
# the Type 79 is the two-handed SMG that has a definition of its own (the UMP and the MAC-10 share one, so the P90 and
# the Steyr TMP already sound alike); the MPi69 is a 9 mm like the MP5 but one-handed.
SOUND_OF = {
    'WT_SUBMACHINEGUN': ['SMG_Type79', 'SMG_MPi69', 'SMG_MAC_10'],
    'WT_RIFLE':         ['Rifle_AK74', 'Rifle_AK47', 'Rifle_FN_SCAR'],
    'WT_PISTOL':        ['HG_M9Beretta', 'HG_M-77B', 'HG_DesertEagle'],
}
SOUND_TYPE = 46                                  # kl_rtp type handler of ZFFItemTemplateWeapon's sound-definition field (kl_snd.SOUND_TYPES)
SOUND_SLOTS = ('dry fire', 'shot (others)', 'fly-by', '', 'shot (player)', 'shell drop', '', 'pick up ammo', 'weapon change', '', '', '', '')

# THE FIT. Dog Days holds every gun 10 degrees nose-down against Dead Men's model space, and a little higher in the hand.
# MEASURED on the three guns both games ship as the same mesh (trimmed nearest-point fit of the full-detail vertices,
# scratch icp.py): Dead Men -> Dog Days = a turn about the model's z axis by
#     AK-74   -10.00 degrees, then a shift of ( 1.04, 1.41, -0.14)     residual 0.06
#     Minimi  -10.00 degrees,                 ( 0.68, 1.59, -2.50)              0.05
#     SPAS-12 -10.01 degrees,                 ( 0.02, 4.20,  0.19)              0.10
# (units are centimetres: the AK-74 is 94.2 long in both). Every Dog Days gun's w_bone_frame rests turned by the same
# angle (rows (0.985, -0.170), (0.170, 0.985); Dead Men's: the identity), the launcher HK69 alone was left as it was.
# So a Dead Men look put on a Dog Days gun as it is (kl_guns: 'the same axes, scale and grip place') points 10 degrees
# UP out of the hands and sits 1.5 to 4 low: the owner's 'holds the mp5 weird'.
# The turn is ESTABLISHED (three guns, the same number). The shift is per gun in Dog Days (each was re-seated in the
# hand); every Dead Men look gets the AK-74's: ASSUMPTION that a Dead Men grip sits in a Dead Men hand as the AK-74's
# does. Tried and DROPPED: finding the shift per pairing by laying the look's grip on the Dog Days gun's (seat() below):
# between two different guns the answer moves by +-1.5 with the choice of the zone (scratch seat2.py), more than the
# shifts differ from the AK-74's; seat() stays as the table's 'off' column, a rough number.
HOUSE_DEG = -10.0
HOUSE_SHIFT = (1.04, 1.41, -0.14)                # the AK-74's
SEAT_MAX = 4.0                                   # seat(): a fitted x / y further than this from HOUSE_SHIFT is no fit at all
GRIP_ZONE = (-4.0, 18.0, -12.0, 8.0)             # x0, x1, y0, y1 around the right hand (the model's origin); magazines left out
# 'l hand attacher' of a gun: Dog Days rests it on the gun's axis, Dead Men beside it (the wrist). The AK-74 of both
# games: Dead Men (39.9, 7.9, 9.4) -> after the turn and shift (41.71, 2.26, 9.26); Dog Days (41.7, 0.3, 0.4). Along the
# barrel they agree to 0.01, so x is comparable; y / z differ by this constant (ASSUMPTION that it is one constant
# for every Dead Men gun: it is one pair of numbers).
LHAND_CONV = (0.0, -1.96, -8.86)
V_STRIDE = 40                                    # a rigid part's vertex: +0 position, +12 normal, +16 colour, +20 uv, +28 tangent, +32 binormal, +36 pad
V_VECTORS = (12, 28, 32)                         # packed B, G, R, 0 = ((b2 - 128) / 127, (b1 - 128) / 127, (b0 - 128) / 127) (re/pd2_klside.md 1)


def gun_node(sc, template):
    """kl_guns.gun_node that also takes a model object named Ground01."""
    for name in ('Ground', 'Ground01'):
        tail = BS + 'Weapon' + BS + template + BS + name
        hits = [k for k in range(1, len(sc.nodes)) if sc.path[k].endswith(tail)]
        if len(hits) == 1:
            return hits[0]
    raise ValueError('%s: no single weapon template named %s with a Ground / Ground01' % (sc.label, template))


def wanted(guns, start=START, sets=SET):
    """{template: group shown} by the Guns page's two numbers (klgun.c klg_tick)."""
    out = {}
    for g in guns:
        w = start if g['item'] == START_ITEM else (1 if sets else 0)
        out[g['template']] = w if 0 <= w <= len(g['looks']) else 0
    return out


def sizes(src):
    """The four members the game reads into one block each, and the chunk table. src: an Lv or a folder."""
    lv = src if isinstance(src, C.Lv) else C.Lv(src)
    wav = lv.beside.get('.WAV')
    return collections.OrderedDict([
        ('.prm', len(lv['.prm'])), ('.ANM', len(lv['.ANM'])), ('.fxc', len(lv['.fxc'])),
        ('.WAV', os.path.getsize(wav) if wav else 0), ('.TEX', len(lv['.TEX'])),
        ('entries', struct.unpack_from('<I', lv['.prm'], 4)[0])])


def groups_of(p, g):
    """[[object, ...] stock, look 1, look 2 ...] of a gun of the report, from the model's object table."""
    objs, out, i = C.objects(p, g['root']), [], 0
    for n in [g['stock_parts']] + [l['parts'] for l in g['looks']]:
        out.append(objs[i:i + n]); i += n
    if i != len(objs):
        raise ValueError('%s: %d objects, the groups say %d' % (g['template'], len(objs), i))
    return out


# ------------------------------------------------------------------ the fit: measuring
def shape(p, root):
    """What the fit looks at of a gun model: {'bones': {name: 12 floats (three rows = the bone's axes in model space,
    then its place)}, 'parts': [(bone name, [positions])]} - the rigid parts drawn at full detail."""
    sk = C.skeleton(p, root)
    names = C.bone_names(p, sk)
    parts = []
    for o in C.objects(p, root):
        c = p.chunks[o]
        if len(c) == 64 and c[0x0c] == 2 and p.u32(o, 0x38) == 1 and c[0x0e] & 1:
            for d in _descriptors(p, o):
                nv, v = p.u32(d, 0), p.chunks[p.u32(d, 4)]
                parts.append((names[p.u32(o, 0x3c)], [struct.unpack_from('<3f', v, V_STRIDE * i) for i in range(nv)]))
    return dict(bones=dict(zip(names, C._rest(p, sk))), parts=parts)


def _descriptors(p, o):
    """The geometry descriptors of a mesh object: its sub table at +0x28 is a 0-terminated list of chunk indices."""
    out = []
    for d in struct.unpack_from('<%dI' % (len(p.chunks[p.u32(o, 0x28)]) // 4), p.chunks[p.u32(o, 0x28)]):
        if not d:
            break
        out.append(d)
    return out


def house(shift=HOUSE_SHIFT, deg=HOUSE_DEG):
    """Dead Men gun space -> Dog Days gun space: (point function, vector function)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (lambda v: (c * v[0] - s * v[1] + shift[0], s * v[0] + c * v[1] + shift[1], v[2] + shift[2]),
            lambda v: (c * v[0] - s * v[1], s * v[0] + c * v[1], v[2]))


def _points(sh, clip=False):
    return sorted({v for bone, vs in sh['parts'] if clip or bone != 'w_bone_clip' for v in vs})


def _in_zone(v, grow=0.0):
    return GRIP_ZONE[0] - grow <= v[0] <= GRIP_ZONE[1] + grow and GRIP_ZONE[2] - grow <= v[1] <= GRIP_ZONE[3] + grow


def _near(a, pts):
    return min((a[0] - q[0]) ** 2 + (a[1] - q[1]) ** 2 + (a[2] - q[2]) ** 2 for q in pts) ** 0.5


def grip_gap(look, host, xf):
    """How far the look's grip is from the host's: mean distance of the look's points around the hand (after xf) to
    the nearest host point there, the worst 30 % left out (what one gun has and the other lacks). None = no points."""
    b = [v for v in _points(host) if _in_zone(v, 2.0)]
    a = [q for q in (xf(v) for v in _points(look)) if _in_zone(q)]
    if len(a) < 10 or len(b) < 10:
        return None
    d = sorted(_near(q, b) for q in a)
    d = d[:max(8, int(len(d) * 0.7))]
    return sum(d) / len(d)


def seat(look, host, keep=0.7):
    """The shift (after the house turn) that would lay the look's grip on the host's: translation-only nearest-point
    fit in GRIP_ZONE, x and y; z stays the AK-74's (a folded stock on one side would pull a gun sideways).
    -> (shift, note); HOUSE_SHIFT with a note when there is too little to fit or the answer is out of SEAT_MAX.
    NOT used to build (see HOUSE_SHIFT): good to 0.01 on the same mesh, to about 1.5 between different guns."""
    b = [v for v in _points(host) if _in_zone(v, 2.0)]
    _pt, vec = house()
    a0 = [vec(v) for v in _points(look)]
    t = list(HOUSE_SHIFT[:2])
    for _it in range(40):
        a = [(v[0] + t[0], v[1] + t[1], v[2] + HOUSE_SHIFT[2]) for v in a0]
        a = [q for q in a if _in_zone(q)]
        if len(a) < 10 or len(b) < 10:
            return HOUSE_SHIFT, 'too few points around the hand: the AK-74\'s shift'
        pr = sorted(((_near(q, b), q) for q in a), key=lambda x: x[0])[:max(8, int(len(a) * keep))]
        d = [0.0, 0.0]
        for _dist, q in pr:
            n = min(b, key=lambda r: (q[0] - r[0]) ** 2 + (q[1] - r[1]) ** 2 + (q[2] - r[2]) ** 2)
            d[0] += n[0] - q[0]; d[1] += n[1] - q[1]
        d = [x / len(pr) for x in d]
        t = [t[0] + d[0], t[1] + d[1]]
        if max(abs(x) for x in d) < 0.004:
            break
    if max(abs(t[0] - HOUSE_SHIFT[0]), abs(t[1] - HOUSE_SHIFT[1])) > SEAT_MAX:
        return HOUSE_SHIFT, 'no grip fit (%.2f, %.2f)' % (t[0], t[1])
    return (round(t[0], 2), round(t[1], 2), HOUSE_SHIFT[2]), ''


def _box(pts):
    return [(min(v[i] for v in pts), max(v[i] for v in pts)) for i in range(3)]


def measure(look, host, game='dm', shift=None):
    """One pairing in numbers (centimetres, the Dog Days gun's space). 'before' = the look as kl_guns puts it (its own
    space taken for the Dog Days gun's), 'after' = through house(). A Dog Days look (game 'dd') is in place already.
        grip        grip_gap() before / after (mean distance between the two guns' surfaces around the right hand: it
                    cannot reach 0 between different guns)
        grip_off    how much further seat() would move the look to lay grip on grip (along the barrel, up); rough
        hand        look's support-hand place minus the Dog Days gun's 'l hand attacher', (along the barrel, up),
                    before / after; None when one of them has no such bone (one-handed guns)
        mag         the look's magazine centre minus the Dog Days gun's (its w_bone_clip parts; the look's magazine
                    turns about the Dog Days gun's magazine bone at a reload), after
        length      look / Dog Days gun; rear, front = how far the look reaches past the gun's ends, after
    """
    ident = lambda v: v
    if game == 'dm':
        shift = HOUSE_SHIFT if shift is None else shift
        pt, _vec = house(shift)
        st, note = seat(look, host)
        off = (st[0] - shift[0], st[1] - shift[1]) if not note else None
    else:
        shift, note, pt, off = (0.0, 0.0, 0.0), 'a Dog Days model: in place', ident, None
    out = dict(shift=tuple(shift), deg=HOUSE_DEG if game == 'dm' else 0.0, note=note, grip_off=off,
               grip=(grip_gap(look, host, ident), grip_gap(look, host, pt)))
    lh, ll = host['bones'].get('l hand attacher'), look['bones'].get('l hand attacher')
    if lh and ll:
        conv = LHAND_CONV if game == 'dm' else (0.0, 0.0, 0.0)
        place = lambda f: tuple(f(ll[9:12])[i] + conv[i] - lh[9 + i] for i in (0, 1))
        out['hand'] = (place(ident), place(pt))
    else:
        out['hand'] = None
    cl = [pt(v) for b, vs in look['parts'] if b == 'w_bone_clip' for v in vs]
    ch = [v for b, vs in host['parts'] if b == 'w_bone_clip' for v in vs]
    if cl and ch:
        bl, bh = _box(cl), _box(ch)
        out['mag'] = tuple((bl[i][0] + bl[i][1]) / 2 - (bh[i][0] + bh[i][1]) / 2 for i in (0, 1))
    else:
        out['mag'] = None
    bl, bh = _box([pt(v) for v in _points(look, True)]), _box(_points(host, True))
    out.update(length=(bl[0][1] - bl[0][0]) / (bh[0][1] - bh[0][0]), rear=bh[0][0] - bl[0][0], front=bl[0][1] - bh[0][1])
    return out


def cost(m):
    """One number to rank pairings by: grip gap + support hand off its place along the barrel + magazine off its
    pivot + what sticks out behind where the Dog Days gun has nothing (a stock in the arm), all in centimetres.
    A ranking aid only - the weights are 1, 1, 0.5, 0.25 by judgement."""
    c = (m['grip'][1] if m['grip'][1] is not None else 5.0)
    c += abs(m['hand'][1][0]) if m['hand'] else 0.0
    c += 0.5 * math.hypot(*m['mag']) if m['mag'] else 0.0
    c += 0.25 * max(m['rear'], 0.0)
    return c


def _f(x, w=5):
    return ('%*.1f' % (w, x)) if x is not None else ' ' * (w - 1) + '-'


def row(label, host, m):
    h = m['hand']
    g = m.get('grip_off')
    return '%-10s on %-18s grip gap %s ->%s off (%s,%s)  support hand along barrel %s ->%s up %s ->%s  mag (%s,%s)  length x%.2f rear %s front %s  cost %4.1f' % (
        label, host, _f(m['grip'][0], 4), _f(m['grip'][1], 4), _f(g[0] if g else None, 4), _f(g[1] if g else None, 4),
        _f(h[0][0] if h else None), _f(h[1][0] if h else None), _f(h[0][1] if h else None), _f(h[1][1] if h else None),
        _f(m['mag'][0] if m['mag'] else None), _f(m['mag'][1] if m['mag'] else None), m['length'], _f(m['rear']), _f(m['front']), cost(m))


def fit_table(level='F01', dm_level='M01_FA_A', log=print):
    """Every look of LOOKS (and Dead Men's own AK-74) against every Dog Days gun the shop sells that is held the same
    way: the six pairings, then per look the three best hosts. -> (rows of the pairings, {label: best hosts})."""
    import kl_arms
    lv = C.Lv(level); sc, _raw = lv.scene(); p = G.read(lv['.prm'], 'dd')
    src = C.Source.get(dm_level, lambda *_a: None)
    eq = kl_arms.equipment(sc)
    hosts = {}
    for name, e in eq.items():
        if e['wt'] in ('WT_RIFLE', 'WT_SUBMACHINEGUN', 'WT_PISTOL') and 'silenced' not in e['item'].lower() and 'Human_Shield' not in e['item'] and e['item'] != 'eFF2ItemSMG_HK_SP89_Silenced':
            hosts[e['name']] = dict(shape(p, C.person(sc, gun_node(sc, e['name']))[0]), wt=e['wt'], hands=e['hands'])
    looks = [(label, game, tpl, kind, host) for host, _item, ls in LOOKS for label, game, tpl, kind, _donor in ls]
    looks.append(('AK-74 (DM)', 'dm', 'Rifle_AK74_01', 'WT_RIFLE', None))
    shapes = {}
    for label, game, tpl, kind, host in looks:
        shapes[label] = shape(src.prm, C.person(src.sc, gun_node(src.sc, tpl))[0]) if game == 'dm' else shape(p, C.person(sc, gun_node(sc, tpl))[0])
    log('centimetres, in the Dog Days gun\'s space; before -> after the fit (turn %.0f degrees, shift (%.2f, %.2f, %.2f)).' % ((HOUSE_DEG,) + HOUSE_SHIFT))
    log('grip gap = mean distance of the two guns\' surfaces around the right hand; off = how much further a grip-on-grip fit would move the look (rough, +-1.5);')
    log('support hand = the look\'s place for it minus the Dog Days gun\'s; mag = magazine centre minus the Dog Days gun\'s (after); rear / front = past its ends (after)')
    log('THE PAIRINGS')
    pairs, best = [], {}
    for label, game, tpl, kind, host in looks:
        if host:
            m = measure(shapes[label], hosts[host], game)
            pairs.append((label, host, m)); log('  ' + row(label, host, m))
    log('PER LOOK, the three Dog Days guns of its hold that fit best (the shop\'s guns; silenced variants left out)')
    for label, game, tpl, kind, host in looks:
        two = 'l hand attacher' in shapes[label]['bones']
        cands = []
        for hn, h in hosts.items():
            if hn == tpl or ('l hand attacher' in h['bones']) != two or (kind == 'WT_PISTOL') != (h['wt'] == 'WT_PISTOL'):
                continue
            m = measure(shapes[label], h, game)
            cands.append((cost(m), hn, m))
        cands.sort(key=lambda x: x[0])
        best[label] = [(hn, c) for c, hn, _m in cands]
        for c, hn, m in cands[:3]:
            log('  ' + row(label, hn, m) + ('   <- the pairing' if hn == host else '') + ('   [%s]' % hosts[hn]['wt'][3:].lower()))
    return pairs, best


# ------------------------------------------------------------------ the fit: building
def _turn_vertices(v, nv, pt, vec):
    """A rigid part's vertex chunk with every position through pt and the packed normal / tangent / binormal through vec."""
    if not nv * V_STRIDE <= len(v) < nv * V_STRIDE + 16:
        raise ValueError('a look part\'s vertex chunk is %d bytes for %d vertices: not the %d-byte rigid vertex' % (len(v), nv, V_STRIDE))
    out = bytearray(v)
    for i in range(nv):
        o = V_STRIDE * i
        struct.pack_into('<3f', out, o, *pt(struct.unpack_from('<3f', v, o)))
        for k in V_VECTORS:
            b0, b1, b2 = v[o + k], v[o + k + 1], v[o + k + 2]
            n = vec(((b2 - 128) / 127.0, (b1 - 128) / 127.0, (b0 - 128) / 127.0))
            out[o + k:o + k + 3] = bytes(max(0, min(255, int(round(x * 127.0 + 128)))) for x in (n[2], n[1], n[0]))
    return bytes(out)


def refit(p, rep, log=print):
    """Every Dead Men look turned into the Dog Days gun's hold (house()): the look's parts get
    PRIVATE geometry - sub table, descriptor and vertex chunk copied, the index chunk stays shared - so the Dead Men
    model the parts were copied from is not touched. p: the open .prm; rep['guns'] gets the numbers."""
    made = 0
    for g in rep['guns']:
        gr = groups_of(p, g)
        host = shape_of_objects(p, g['root'], gr[0])
        for n, l in enumerate(g['looks'], 1):
            look = shape(p, l['source_root'])
            l['fit'] = m = measure(look, host, l['game'])
            if l['game'] != 'dm':
                continue
            pt, vec = house(m['shift'])
            done = {}
            for o in gr[n]:
                subs = []
                for d in _descriptors(p, o):
                    if d not in done:
                        dv = list(struct.unpack('<12I', p.chunks[d]))
                        dv[1] = G.new_chunk(p, _turn_vertices(p.chunks[dv[1]], dv[0], pt, vec), p.refs[dv[1]])
                        done[d] = G.new_chunk(p, struct.pack('<12I', *dv), p.refs[d]); made += 2
                    subs.append(done[d])
                old = p.chunks[p.u32(o, 0x28)]
                sub = G.new_chunk(p, struct.pack('<%dI' % len(subs), *subs) + old[4 * len(subs):], p.refs[p.u32(o, 0x28)]); made += 1
                p.chunks[o] = C._put(p.chunks[o], 0x28, '<I', sub)
            l['geometry'] = sorted(done.values())
            h = m['hand']
            log('  %-18s %-9s turned %.0f degrees, shift (%.2f, %.2f, %.2f): support hand off its place by (%s, %s) -> (%s, %s) cm (along the barrel, up), grip gap %s -> %s' % (
                g['template'], l['label'], HOUSE_DEG, m['shift'][0], m['shift'][1], m['shift'][2], _f(h[0][0] if h else None, 0), _f(h[0][1] if h else None, 0),
                _f(h[1][0] if h else None, 0), _f(h[1][1] if h else None, 0), _f(m['grip'][0], 0), _f(m['grip'][1], 0)))
    rep['fit_chunks'] = made
    return made


def shape_of_objects(p, root, objs):
    """shape() of some of a model's objects (the stock group of a gun that has looks already)."""
    sk = C.skeleton(p, root)
    names = C.bone_names(p, sk)
    parts = []
    for o in objs:
        c = p.chunks[o]
        if c[0x0e] & 1:
            for d in _descriptors(p, o):
                nv, v = p.u32(d, 0), p.chunks[p.u32(d, 4)]
                parts.append((names[p.u32(o, 0x3c)], [struct.unpack_from('<3f', v, V_STRIDE * i) for i in range(nv)]))
    return dict(bones=dict(zip(names, C._rest(p, sk))), parts=parts)


# ------------------------------------------------------------------ the sound of a look
def sound_field():
    """Index of ZFFItemTemplateWeapon's sound-definition field among its stored properties: the one of type 46.
    (Its other sound field, type 70, is 0 on all 61 templates.) The value is an offset into the level's .SND and names
    a '#def' object: 13 slots, SOUND_SLOTS. Stock Dog Days shares definitions between guns the same way (the UMP plays
    the MAC-10's, the UMP SBR the Zastava's, the Type 05 the MPi69's), so re-pointing the field is what the game's own
    data does; nothing is added to the bank and the .WAV does not change."""
    import kl_snd as S
    hot = [i for i, f in enumerate(S._schema().fields('ZFFItemTemplateWeapon')) if f.type == SOUND_TYPE and f.kind == 'I']
    if len(hot) != 1:
        raise ValueError('ZFFItemTemplateWeapon has %d fields of type %d, expected one' % (len(hot), SOUND_TYPE))
    return hot[0]


def template_node(sc, template):
    return sc.parent[gun_node(sc, template)]


def sound_of(sc, k, fld=None):
    """The sound-definition offset of weapon template node k."""
    us = units(sc.nodes[k]['props'][1:-1])
    return struct.unpack('<I', us[sound_field() if fld is None else fld][0][1])[0]


def sound_name(snd, off):
    """'smg_type79' of 'audio:levelsetup/all/weapons_kl2_final/smg_type79/smg_type79#def'; raises when off is no definition."""
    if snd.kind.get(off) != 5:
        raise ValueError('sound offset %#x is not a definition (type 5) of the bank' % off)
    return snd.name(off).decode('latin1').rsplit('/', 1)[-1].split('#')[0]


def sound_slots(snd, off):
    """The 13 slots of a definition as short names ('' = empty)."""
    b = snd.b
    lst, n = struct.unpack_from('<IH', b, off + 0x14)
    out = []
    for i in range(n):
        t = struct.unpack_from('<I', b, lst + 4 * i)[0]
        out.append(snd.name(t).decode('latin1').split('weapons_kl2_final/')[-1] if t else '')
    return out


def resound(lv, rep, log=print):
    """A gun whose SHOWN look is of another weapon class than the gun - or names a donor - takes the sound definition
    of a stock Dog Days gun of the look's class: one .prp field of the template. Edits lv's .prp; -> changes made.
    Everyone who fires that template is heard with it, as everyone is seen with the look."""
    import kl_snd as S, kl_arms
    sc, _raw = lv.scene()
    snd = S.Snd('dd', lv['.SND'])
    eq = kl_arms.equipment(sc)
    fld, n = sound_field(), 0
    for g in rep['guns']:
        k = template_node(sc, g['template'])
        own = sound_of(sc, k, fld)
        g['sound'] = dict(before=sound_name(snd, own), after=sound_name(snd, own), donor=None, why='')
        if not g.get('shown'):
            continue
        l = g['looks'][g['shown'] - 1]
        wt = eq[g['template'].lower()]['wt']
        donors = [l['donor']] if l.get('donor') else (SOUND_OF.get(l['kind'], []) if l['kind'] != wt else [])
        if not donors:
            continue
        for d in donors:
            e = eq.get(d.lower())
            if not e or d == g['template'] or (not l.get('donor') and e['wt'] != l['kind']):
                continue
            off = sound_of(sc, template_node(sc, d), fld)
            name = sound_name(snd, off)
            if 'silenced' in name or off == own:
                continue
            node = sc.nodes[k]
            us = [list(u) for u in units(node['props'][1:-1])]
            us[fld] = [(us[fld][0][0], struct.pack('<I', off))]
            node['props'] = [node['props'][0]] + [t for u in us for t in u] + [node['props'][-1]]
            g['sound'].update(after=name, donor=d, offset=off, was=own,
                              why='the look is Dog Days\' own %s' % d if l.get('donor') else 'the look is a %s, the gun a %s' % (l['kind'][3:].lower(), wt[3:].lower()))
            a, b = sound_slots(snd, own), sound_slots(snd, off)
            g['sound']['slots'] = [(SOUND_SLOTS[i], a[i], b[i]) for i in range(min(len(a), len(b), len(SOUND_SLOTS))) if a[i] != b[i]]
            n += 1
            log('  %-18s sounds like %s now (was %s): %s' % (g['template'], name, g['sound']['before'], g['sound']['why']))
            break
        else:
            log('  %-18s keeps %s: no stock gun of class %s to borrow from in this level' % (g['template'], g['sound']['before'], l['kind']))
    if n:
        lv['.prp'] = sc.p.serialize()
    rep['sounds_changed'] = n
    return n


def bake(lv, rep, want, fit=True, log=print):
    """Private stock parts, the fit of the Dead Men looks (refit) and the hide bit on every group but want[template].
    lv: kl_chars.Lv, edited in place."""
    p, made = G.read(lv['.prm'], 'dd'), 0
    if fit:
        refit(p, rep, log)
    rep['fitted'] = bool(fit)
    for g in rep['guns']:
        gr = groups_of(p, g)
        for j, o in enumerate(gr[0]):                 # the stock parts are the OLD root's objects too: copies for this root
            i = C._new(p, p.chunks[o]); p.refs[i] = p.refs[o]
            gr[0][j] = i; made += 1
        flat = [o for part in gr for o in part]
        tab = p.u32(g['root'], 0x18)
        if len(p.chunks[tab]) < 4 * len(flat):
            raise ValueError('%s: the object table chunk is smaller than its count' % g['template'])
        p.chunks[tab] = struct.pack('<%dI' % len(flat), *flat) + p.chunks[tab][4 * len(flat):]
        for n, part in enumerate(gr):
            for o in part:
                w = p.u32(o, HIDE_OFF)
                if w & HIDE_BIT:
                    raise ValueError('%s: part %d has the hide bit already' % (g['template'], o))
                if n != want[g['template']]:
                    p.chunks[o] = C._put(p.chunks[o], HIDE_OFF, '<I', w | HIDE_BIT)
        g['shown'] = want[g['template']]
        log('  %-18s shows %s' % (g['template'], g['looks'][g['shown'] - 1]['label'] + ' (look %d)' % g['shown'] if g['shown'] else 'its own model'))
    prm = G.write(p)
    mat = T.read_mat(lv['.MAT']); mat.refs = T.material_refs(prm)
    lv['.prm'], lv['.MAT'] = prm, T.write_mat(mat)
    rep['private_stock_parts'] = made
    rep['chunks'] = (rep['chunks'][0], len(p.chunks) - 1)
    rep['prm_bytes'] = (rep['prm_bytes'][0], len(prm))
    return rep


def drawn(p, root, variant):
    """The objects of a model the game's walk takes for an entity of that variant (kl2 0x67cf77..0x67cf91)."""
    return [o for o in C.objects(p, root) if not p.u32(o, HIDE_OFF) & HIDE_BIT and (variant == 0 or p.chunks[o][0x0f] == variant)]


def check(lv, rep):
    """What must hold for the gun models of a folder built here. -> problems."""
    bad = []
    p = G.read(lv['.prm'], 'dd'); sc, raw = lv.scene()
    used = collections.Counter()
    for i, c in enumerate(p.chunks):
        if c and len(c) >= 0x20 and c[2] == 7 and c[3] == 0:
            try:
                used.update(set(C.objects(p, i)))
            except Exception:                         # not a model root after all
                pass
    for g in rep['guns']:
        k = gun_node(sc, g['template'])
        root, var, _a = C.person(sc, k)
        if root != g['root']:
            bad.append('%s: the template does not name the new model' % g['template']); continue
        if var != 0:
            bad.append('%s: the gun entity\'s variant is %d, not 0' % (g['template'], var))
        n = p.u32(C.skeleton(p, root), 0)
        gr = groups_of(p, g)
        for j, part in enumerate(gr):
            for o in part:
                c = p.chunks[o]
                if len(c) != 64 or c[2] != 8 or c[0x0c] != 2 or p.u32(o, 0x38) != 1 or p.u32(o, 0x3c) >= n:
                    bad.append('%s: object %d of group %d is not a rigid part on a bone of the gun' % (g['template'], o, j))
                if bool(p.u32(o, HIDE_OFF) & HIDE_BIT) != (j != g['shown']):
                    bad.append('%s: object %d of group %d: hide bit %s' % (g['template'], o, j, 'missing' if j != g['shown'] else 'set on the shown group'))
                if used[o] != 1:
                    bad.append('%s: object %d is in %d models\' object tables: a hide bit would reach the others' % (g['template'], o, used[o]))
        d = drawn(p, root, var)
        if d != gr[g['shown']]:
            bad.append('%s: the game\'s walk takes %d objects, the shown group has %d' % (g['template'], len(d), len(gr[g['shown']])))
        if not any(p.chunks[o][0x0e] & 1 for o in d):
            bad.append('%s: nothing of the shown group is at full detail' % g['template'])
        low = [b for b in range(8) if not any(p.chunks[o][0x0e] >> b & 1 for o in d)]
        g['detail_levels_empty'] = low               # a note: Dead Men's guns use other masks than Dog Days' (re/map_guns.md 3)
        if rep.get('fitted'):
            bad += ['%s: %s' % (g['template'], x) for x in check_fit(p, g, gr)]
    if 'sounds_changed' in rep:
        bad += check_sound(lv, sc, rep)
    return bad


def check_fit(p, g, gr):
    """A fitted Dead Men look: every part has geometry of its own (no vertex chunk shared with the model it was copied
    from), and its vertices ARE that model's through house() with the recorded shift; the grip gap is as recorded."""
    bad = []
    for n, l in enumerate(g['looks'], 1):
        if l.get('game') != 'dm':
            continue
        if not l.get('fit') or not l.get('geometry'):
            bad.append('look %s was not fitted' % l['label']); continue
        pt, vec = house(l['fit']['shift'])
        unpack = lambda c, o: ((c[o + 2] - 128) / 127.0, (c[o + 1] - 128) / 127.0, (c[o] - 128) / 127.0)
        src = {}                                      # index chunk -> descriptor of the Dead Men model (the look shares the index chunk)
        for o in C.objects(p, l['source_root']):
            for d in _descriptors(p, o):
                src[p.u32(d, 0x18)] = d
        worst = 0.0
        for o in gr[n]:
            for d in _descriptors(p, o):
                s = src.get(p.u32(d, 0x18))
                if s is None:
                    bad.append('look %s: object %d has geometry that is not the Dead Men model\'s' % (l['label'], o)); continue
                if d == s or p.u32(d, 4) == p.u32(s, 4):
                    bad.append('look %s: object %d shares its vertices with the Dead Men model: not fitted' % (l['label'], o)); continue
                nv, a, b = p.u32(d, 0), p.chunks[p.u32(d, 4)], p.chunks[p.u32(s, 4)]
                if nv != p.u32(s, 0) or len(a) != len(b):
                    bad.append('look %s: object %d: vertex count differs from the Dead Men model' % (l['label'], o)); continue
                for i in range(0, nv, max(1, nv // 24)):
                    q, w = struct.unpack_from('<3f', a, V_STRIDE * i), pt(struct.unpack_from('<3f', b, V_STRIDE * i))
                    worst = max(worst, max(abs(q[j] - w[j]) for j in range(3)))
                    for k in V_VECTORS:               # normal, tangent, binormal: turned with the part, to a byte's step
                        q, w = unpack(a, V_STRIDE * i + k), [max(-128 / 127.0, min(1.0, x)) for x in vec(unpack(b, V_STRIDE * i + k))]   # a byte saturates
                        if max(abs(q[j] - w[j]) for j in range(3)) > 1.5 / 127:
                            bad.append('look %s: object %d: the packed vector at +%d was not turned with the part' % (l['label'], o, k)); break
                    if a[V_STRIDE * i + 16:V_STRIDE * i + 28] != b[V_STRIDE * i + 16:V_STRIDE * i + 28]:
                        bad.append('look %s: object %d: colour / texture coordinate changed' % (l['label'], o)); break
        if worst > 0.01:
            bad.append('look %s: a vertex is %.3f from where the fit puts it' % (l['label'], worst))
        host, look = shape_of_objects(p, g['root'], gr[0]), shape_of_objects(p, g['root'], gr[n])
        gap = grip_gap(look, host, lambda v: v)
        if gap is None or l['fit']['grip'][1] is None or abs(gap - l['fit']['grip'][1]) > 0.05:
            bad.append('look %s: grip gap measured on the written parts %s, recorded %s' % (l['label'], gap, l['fit']['grip'][1]))
    return bad


def check_sound(lv, sc, rep):
    """Each gun's sound field names a definition of the bank, and it is the one the report says."""
    import kl_snd as S
    bad, snd = [], S.Snd('dd', lv['.SND'])
    for g in rep['guns']:
        try:
            now = sound_name(snd, sound_of(sc, template_node(sc, g['template'])))
        except ValueError as x:
            bad.append('%s: %s' % (g['template'], x)); continue
        if now != g['sound']['after']:
            bad.append('%s: sounds like %s, the report says %s' % (g['template'], now, g['sound']['after']))
    return bad


def write_ini(rep, path, entries):
    """KLGuns.ini, Version 2: Version 1's keys (kl_guns.write_ini) + how a group is hidden and which one the file shows.
    entries: the chunk count of the .prm the Root indices belong to (its dword +4 = what the game puts at 0xeac7a4).
    klgun.c refuses a Version 2 file without Entries= and leaves one alone whose Entries is not the loaded .prm's
    count: a file left over beside a newer archive must not be taken for this build's (re/hook_review_1010.md G1)."""
    if not 0 < entries <= 0x12000:
        raise ValueError('KLGuns.ini: %r is not a chunk count the game\'s table holds' % (entries,))
    with open(path, 'w', newline='\r\n') as f:
        f.write('; written by tools/kl_map_guns.py - belongs to the level archive beside it (klhook\\klgun.c)\n')
        f.write('; Version 2: a part is hidden by bit HideBit of the dword at +HideWord of its mesh object (kl2 0x67cf77), NOT by its variant byte:\n')
        f.write('; a gun entity\'s variant is 0 and variant 0 takes every object. Shown = the group the file was built to show (0 = the stock gun, n = look n).\n')
        f.write('; A hook that accepts Version 1 only leaves this file alone: the level then shows what was built in.\n')
        if rep.get('fitted'):
            f.write('; The Dead Men looks are turned %.0f degrees and shifted (%.2f, %.2f, %.2f) into the Dog Days hold (geometry of their own).\n' % ((HOUSE_DEG,) + HOUSE_SHIFT))
        for g in rep['guns']:
            s = g.get('sound')
            if s and s.get('donor'):
                f.write('; %s shows %s and is built to sound like %s (was %s): the sound is in the level, a switch in the menu does not change it.\n' % (
                    g['template'], g['looks'][g['shown'] - 1]['label'], s['after'], s['before']))
        f.write('; Entries = the chunk count of the .prm in the archive beside this file: the hook takes the file for that .prm only.\n')
        f.write('[Guns]\nVersion=2\nCount=%d\nHidden=%d\nHideWord=%d\nHideBit=%d\nEntries=%d\n' % (len(rep['guns']), K.HIDDEN, HIDE_OFF, HIDE_BIT, entries))
        for i, g in enumerate(rep['guns'], 1):
            f.write('[Gun.%d]\nTemplate=%s\nItem=%d\nRoot=%d\nStock=%d\nLooks=%d\nShown=%d\n' % (
                i, g['template'], g['item'], g['root'], g['stock_parts'], len(g['looks']), g['shown']))
            for n, l in enumerate(g['looks'], 1):
                f.write('Look%d=%s\nLook%dParts=%d\n' % (n, l['label'], n, l['parts']))


def weapons(src, log=print):
    """Every weapon template of a level: is its model drawn (the game's walk, a compiled shader for each material of
    the taken parts), who carries it, which look it shows. -> (rows, problems). src: an Lv, a folder or a level name."""
    import kl_arms, kl_light
    lv = src if isinstance(src, C.Lv) else C.Lv(src)
    sc, raw = lv.scene()
    p, mat = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT'])
    lack = kl_light.missing_shaders(mat, lv['.fxc'])
    carried, second = collections.Counter(), collections.Counter()
    for _k, _squad, w, w2, _g1, _g2, _s in kl_arms.carriers(sc):
        carried[w.lower()] += 1; second[w2.lower()] += 1
    looks = {}
    gj = lv.side.get('guns.json')
    if gj:
        for g in json.load(open(gj))['guns']:
            looks[g['template'].lower()] = g
    rows, bad = [], []
    for name, e in sorted(kl_arms.equipment(sc).items()):
        # the gun's model object: the child 'Ground' ('Ground01' on the three revolvers), a ZLNKOBJ
        k = next((c for c in range(1, len(sc.nodes)) if sc.path[c].startswith(e['path'] + BS + 'Ground') and sc.cls(c) == 'ZLNKOBJ'
                  and sc.path[c].count(BS) == e['path'].count(BS) + 1), None)
        row = dict(template=e['name'], item=e['item'], carried=carried[name], secondary=second[name], faults=[])
        rows.append(row)
        root, var = C.person(sc, k)[:2] if k is not None else (0, 0)
        row.update(model=root, variant=var)
        if not root:
            row['faults'].append('no model object (Ground) or no model')
            bad.append('%s: %s' % (e['name'], row['faults'][-1])); continue
        d = drawn(p, root, var)
        row.update(objects=len(C.objects(p, root)), drawn=len(d), full_detail=sum(p.chunks[o][0x0e] & 1 for o in d),
                   materials=sorted({mat.insts[p.u16(o, 0x12)].name.split('/')[-1] for o in d}))
        if not any(p.chunks[o][0x0e] & 1 for o in d):
            row['faults'].append('NOT DRAWN: the walk takes no object at full detail (%d taken of %d)' % (len(d), row['objects']))
        for s in sorted({p.u16(o, 0x12) for o in d} & set(lack)):
            row['faults'].append('material %s (slot %d) asks for an effect the .fxc lacks: %s' % (mat.insts[s].name, s, [str(x) for x in lack[s]][:1]))
        g = looks.get(name)
        row['shows'] = (g['looks'][g['shown'] - 1]['label'] if g.get('shown') else 'own model') if g else 'own model'
        row['look_of'] = bool(g)
        bad += ['%s: %s' % (e['name'], x) for x in row['faults']]
    for w, n in sorted(carried.items()):
        if w and w not in {r['template'].lower() for r in rows}:
            bad.append('%d actor(s) carry %s, which the equipment tree does not have' % (n, w))
    return rows, bad


def show_weapons(src, log=print):
    rows, bad = weapons(src)
    log('%-28s %-34s %5s %5s  %s' % ('template', 'item', 'model', 'drawn', 'carried by / shows'))
    for r in rows:
        if r['carried'] or r['secondary'] or r['faults'] or r.get('look_of'):
            log('%-28s %-34s %5s %2s/%-2s  %s%s%s' % (r['template'], r['item'], r.get('model', '-'), r.get('drawn', '-'), r.get('objects', '-'),
                '%d actor(s)' % r['carried'] if r['carried'] else 'nobody placed', ' (+%d as second gun)' % r['secondary'] if r['secondary'] else '',
                '; shows ' + r['shows'] if r.get('look_of') else ''))
        for x in r['faults']:
            log('    FAULT: ' + x)
    quiet = sum(1 for r in rows if not (r['carried'] or r['secondary'] or r['faults'] or r.get('look_of')))
    log('%d weapon templates (%d more: nobody placed carries them, no look, drawn); problems: %d' % (len(rows), quiet, len(bad)))
    return rows, bad


def _mark(x, y, r=1.2, col=(255, 230, 60)):
    """A small square in the picture at (x, y): a hand place."""
    return ([(x - r, y - r, 30.0), (x + r, y - r, 30.0), (x + r, y + r, 30.0), (x - r, y + r, 30.0)], [(0, 1, 2), (0, 2, 3), (0, 2, 1), (0, 3, 2)], col)


def sheet(folder, out):
    """One row per look of a folder built here: the Dog Days gun | the look as kl_guns put it (the Dead Men model's own
    space) | the look as built | the look as built over the Dog Days gun. Yellow squares: the right hand (the model's
    origin) and the Dog Days gun's 'l hand attacher'. Side view, software renderer (kl_view): shapes, not materials."""
    import kl_view as V
    lv = C.Lv(folder); p = G.read(lv['.prm'], 'dd')
    rep = json.load(open(os.path.join(folder, 'guns.json')))
    panels = []
    for g in rep['guns']:
        gr = groups_of(p, g)
        stock = K._items(p, gr[0], (200, 170, 150))
        box = (-32, 108, -30, 30) if g['template'][:2] != 'HG' else (-10, 50, -14, 14)
        sk = C.skeleton(p, g['root'])
        rest = dict(zip(C.bone_names(p, sk), C._rest(p, sk)))
        marks = [_mark(0.0, 0.0, 1.2 if box[1] > 60 else 0.5)]
        if 'l hand attacher' in rest:
            marks.append(_mark(rest['l hand attacher'][9], rest['l hand attacher'][10]))
        for n, l in enumerate(g['looks'], 1):
            was = K._items(p, C.objects(p, l['source_root']), (220, 120, 110))
            now = K._items(p, gr[n], (150, 150, 220))
            panels += [('front', box, stock + marks), ('front', box, was + marks), ('front', box, now + marks), ('front', box, stock + now + marks)]
    V.sheet(out, panels, 330, 150, cols=4)
    return len(panels) // 4


def _steps(out, slot, log):
    """steps.json of kl_maps.ready_one records which members each step after kl_graft.verify changed, and the ids of the
    folder it measured; kl_maps.audit refuses a folder that differs. This step is one more: recorded the same way."""
    import kl_maps as M
    sj = os.path.join(out, 'steps.json')
    if not os.path.isfile(sj):
        return None
    st = json.load(open(sj)); now = M.member_ids(out, slot)
    was = {m[0]: m[1:] for m in st['final'][0]}
    changed = sorted(m[0] for m in now[0] if was.get(m[0]) != m[1:])
    st['guns'] = changed
    st['same'] = [e for e in st['same'] if e not in changed]
    st['beside_same'] = st['beside_same'] if now[1] == st['final'][1] else sum(a == b for a, b in zip(now[1], st['final'][1]))
    st['final'] = now
    with open(sj, 'w') as f:
        json.dump(st, f, indent=1)
    log('  steps.json: the gun looks changed %s' % ' '.join(changed))
    return changed


def findings(folder):
    """The checkers of kl_maps.audit that need no stock systems level, as text: for 'nothing new' against the source."""
    import kl_fa, kl_arms
    lv = C.Lv(folder)
    sc, snd, loc = kl_fa.load(lv.src)
    out = ['fa: ' + str(x) for x in kl_fa.check(sc, snd, loc, lv['.ANM']) if x.sev <= kl_fa.BROKEN]
    out += ['arms: %s %s' % (c, t) for s, c, t in kl_arms.check(sc, lv['.ANM']) if s == 1]
    out += ['people: %s %s: %s' % (sev, r['path'], text) for r in C.people(lv) for sev, text in r['faults'] if sev != 'NOTE']
    out += ['chars: ' + str(x) for x in C.check(lv, extra=C.wardrobe_roots(lv), log=lambda *_a: None)]
    return out


def _annotate(rep, table):
    """kl_guns' report knows a look by label, parts and source model: add game, class and sound donor from the table."""
    info = {tpl: looks for tpl, _item, looks in table}
    for g in rep['guns']:
        for l, t in zip(g['looks'], info[g['template']]):
            l.update(game=t[1], source=t[2], kind=t[3] if len(t) > 3 else '', donor=t[4] if len(t) > 4 else None)


def pairs(first=False):
    """LOOKS, or with first: the pairings of the first builds (FIRST_PAIRS)."""
    if not first:
        return list(LOOKS)
    return [(FIRST_PAIRS[ls[0][2]] if ls[0][2] in FIRST_PAIRS else (t, i)) + (ls,) for t, i, ls in LOOKS]


def build(src, out, start=START, sets=SET, level='M01_FA_A', audit=True, extra=False, fit=True, sound=True, first=False, log=print):
    """<src> (a finished build folder; not changed) with the gun looks -> <out>. -> report; ['bad'] must be empty.
    fit: the Dead Men looks turned and seated into the Dog Days hold; sound: a look of another class sounds like its class."""
    if os.path.abspath(src) == os.path.abspath(out):
        raise ValueError('the out folder is the build itself')
    lv = C.Lv(src)
    if 'KLGuns.ini' in lv.side:
        raise ValueError('%s has gun looks already (KLGuns.ini): start from the build without them' % src)
    before = sizes(lv)
    keep = K.LOOKS, K.gun_node
    try:                                              # kl_guns reads its table and its node finder as module globals
        table = pairs(first) + (EXTRA if extra else [])
        K.LOOKS, K.gun_node = [(t, i, [l[:3] for l in looks]) for t, i, looks in table], gun_node
        rep = K.build(lv, level, log)
    finally:
        K.LOOKS, K.gun_node = keep
    rep['extra_looks'] = bool(extra)
    _annotate(rep, table)
    side = {e: (len(lv[e]), zlib.crc32(lv[e])) for e in ('.SND', '.ANM', '.fxc')}
    for g in rep['guns']:
        log('  %-18s item %2d  model %5d -> %5d (%d users)  %d stock parts, looks: %s' % (
            g['template'], g['item'], g['stock_root'], g['root'], g['users'], g['stock_parts'],
            ', '.join('%s (%d parts)' % (l['label'], l['parts']) for l in g['looks'])))
    bake(lv, rep, wanted(rep['guns'], start, sets), fit and not extra, log)
    if sound:
        resound(lv, rep, log)
    bad = ['guns: ' + x for x in check(lv, rep)]
    bad += ['%s changed: the gun step must not touch it' % e for e in side if side[e] != (len(lv[e]), zlib.crc32(lv[e]))]
    bad += ['chars: ' + str(x) for x in C.check(lv, None, rep['roots'] + rep['extra_roots'], extra=rep['extra_roots'], log=lambda *_a: None)]
    after = sizes(lv)
    for f in ('guns.json', 'map_guns.json', 'KLGuns.ini'):           # of an earlier run into the same folder
        if os.path.isfile(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    path = lv.write(out, lv.name)
    write_ini(rep, os.path.join(out, 'KLGuns.ini'), struct.unpack_from('<I', lv['.prm'], 4)[0])
    with open(os.path.join(out, 'guns.json'), 'w') as fh:
        json.dump(dict(base=src, problems=bad, **rep), fh, indent=1, default=str)
    lv2 = C.Lv(out)                                                  # everything below reads the WRITTEN folder
    again = check(lv2, json.load(open(os.path.join(out, 'guns.json'))))
    bad += ['guns (written folder): ' + x for x in again]
    bad += ['guns (written folder): ' + x for x in ini_entries(out, lv2)]
    imp = kl_impact.check(path)
    bad += ['impact: ' + x for x in imp]
    rows, wbad = weapons(lv2)
    bad += ['weapons: ' + x for x in wbad]
    out_rep = collections.OrderedDict(
        src=src, out=out, start=start, set=sets, level=level, extra_looks=bool(extra), fit=bool(fit), sound=bool(sound), first_pairs=bool(first), before=before, after=after,
        fits={'%s / %s' % (g['template'], l['label']): l.get('fit') for g in rep['guns'] for l in g['looks']},
        sounds={g['template']: g.get('sound') for g in rep['guns']},
        growth={k: after[k] - before[k] for k in before}, chunk_limit=kl_impact.CHUNK_SAFE,
        dead_indices=rep.get('free_indices'), shows={g['template']: (g['looks'][g['shown'] - 1]['label'] if g['shown'] else 'stock') for g in rep['guns']},
        carried={r['template']: r['carried'] for r in rows if r['carried']},
        carried_with_look={r['template']: (r['carried'], r['shows']) for r in rows if r['carried'] and r.get('look_of')},
        impact=imp, bad=bad)
    log('  .prm %.1f -> %.1f MB, %d -> %d table entries (limit %d); .ANM %d, .fxc %d, .WAV %d: %s; .TEX %.1f -> %.1f MB' % (
        before['.prm'] / 1e6, after['.prm'] / 1e6, before['entries'], after['entries'], kl_impact.CHUNK_SAFE, after['.ANM'], after['.fxc'], after['.WAV'],
        'unchanged' if all(before[k] == after[k] for k in ('.ANM', '.fxc', '.WAV')) else 'CHANGED', before['.TEX'] / 1e6, after['.TEX'] / 1e6))
    out_rep['steps'] = _steps(out, lv.name, log)
    if audit:
        import kl_maps as M
        rj = os.path.join(out, 'result.json')
        if os.path.isfile(os.path.join(out, 'preflight.json')) and os.path.isfile(rj):
            try:                                                     # the carried preflight.* are the source folder's: again
                with open(os.path.join(out, 'preflight.txt'), 'w', encoding='utf-8') as fh:
                    M.preflight(out, lv.name, log=lambda t: fh.write(str(t) + '\n'))
            except Exception as x:
                log('  kl_maps.preflight did not run on the new folder (%s: %s): the carried preflight.* are the source build\'s' % (type(x).__name__, x))
                out_rep['preflight_error'] = '%s: %s' % (type(x).__name__, x)
        try:
            a = M.audit(out, lv.name, log=lambda *_a: None)
            out_rep['audit'] = dict(bad=a['bad'], known=len(a['known']), prm_entries=a['prm_entries'], content_id=a['content_id'])
            bad += ['audit: ' + x for x in a['bad']]
            log('  kl_maps.audit: %s (%d that must be 0, %d known and accepted)' % ('PASS' if not a['bad'] else 'FAIL', len(a['bad']), len(a['known'])))
        except Exception as x:                                       # Retomoto: its systems level 'R09' is no stock level
            out_rep['audit'] = dict(error='%s: %s' % (type(x).__name__, x))
            log('  kl_maps.audit did not run (%s: %s): the same checkers on the source and on the new folder instead' % (type(x).__name__, x))
            new = findings(out)
            old = set(findings(src))
            out_rep['findings'] = dict(source=len(old), now=len(new), new=[x for x in new if x not in old])
            bad += ['new finding: ' + x for x in out_rep['findings']['new']]
            log('  kl_fa.check / kl_arms.check / kl_chars.undrawn / kl_chars.check: %d findings on the source, %d now, %d new' % (
                len(old), len(new), len(out_rep['findings']['new'])))
    with open(os.path.join(out, 'map_guns.json'), 'w') as fh:
        json.dump(out_rep, fh, indent=1, default=str)
    log('built %s (%.0f MB) + KLGuns.ini (Version 2), problems: %d' % (path, os.path.getsize(path) / 1e6, len(bad)))
    for b in bad[:20]:
        log('  PROBLEM: ' + b)
    return out_rep


def ini_entries(folder, lv=None):
    """Does the folder's KLGuns.ini carry Entries= with the chunk count of the folder's own .prm? -> problems.
    (klgun.c refuses the file without the key; the problem text holds the line to add to a build of before 2026-10-10.)"""
    lv = lv or C.Lv(folder)
    n = struct.unpack_from('<I', lv['.prm'], 4)[0]
    got, sec = None, ''
    for line in open(os.path.join(folder, 'KLGuns.ini')).read().splitlines():
        line = line.strip()
        if line.startswith('['):
            sec = line
        elif sec == '[Guns]' and line.split('=')[0].strip() == 'Entries':
            got = line.split('=', 1)[1].strip()
    if got is None:
        return ['KLGuns.ini has no Entries= : the hook refuses it and the level shows what was built in - add the line "Entries=%d" under [Guns], or build again' % n]
    if got != str(n):
        return ['KLGuns.ini says Entries=%s, the .prm beside it has %d chunks: the hook leaves the file alone' % (got, n)]
    return []


def recheck(folder, log=print):
    lv = C.Lv(folder)
    rep = json.load(open(os.path.join(folder, 'guns.json')))
    bad = check(lv, rep) + ['impact: ' + x for x in kl_impact.check(lv.src)] + ini_entries(folder, lv)
    ini = open(os.path.join(folder, 'KLGuns.ini')).read()
    for g in rep['guns']:
        if 'Root=%d\n' % g['root'] not in ini.replace('\r', ''):
            bad.append('%s: KLGuns.ini does not name model %d' % (g['template'], g['root']))
    rows, wbad = weapons(lv)
    bad += wbad
    log('%s: %d guns with looks, shows %s; problems: %d' % (folder, len(rep['guns']), ', '.join(
        '%s=%s' % (g['template'], g['looks'][g['shown'] - 1]['label'] if g['shown'] else 'stock') for g in rep['guns']), len(bad)))
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = dict(x[2:].split('=', 1) for x in sys.argv[1:] if x.startswith('--') and '=' in x)
    kw = dict(start=int(opt.get('start', START)), sets=int(opt.get('set', SET)), level=opt.get('level', 'M01_FA_A'), extra='--extra' in sys.argv,
              fit='--no-fit' not in sys.argv, sound='--no-sound' not in sys.argv, first='--first-pairs' in sys.argv)
    if a[:1] == ['build'] and len(a) == 3:
        sys.exit(1 if build(a[1], a[2], audit='--no-audit' not in sys.argv, **kw)['bad'] else 0)
    elif a[:1] == ['all']:
        n = 0
        for tag in a[1:] or list(BUILDS):
            print('== %s' % tag)
            r = build(os.path.join(workdir(), 'build', *BUILDS[tag].split('/')), os.path.join(workdir(), 'build', opt.get('out', 't_guns'), tag), **kw)
            n += len(r['bad'])
        sys.exit(1 if n else 0)
    elif a[:1] == ['check'] and len(a) == 2:
        sys.exit(1 if recheck(a[1]) else 0)
    elif a[:1] == ['weapons'] and len(a) == 2:
        sys.exit(1 if show_weapons(a[1])[1] else 0)
    elif a[:1] == ['fit']:
        fit_table(opt.get('base', 'F01'), opt.get('level', 'M01_FA_A'))
    elif a[:1] == ['sheet'] and len(a) == 3:
        print('%s: %d rows (stock | the look as kl_guns put it | fitted | fitted over stock)' % (a[2], sheet(a[1], a[2])))
    elif a[:1] == ['sizes'] and len(a) >= 2:
        for f in a[1:]:
            print(f, dict(sizes(f)))
    else:
        print(__doc__); sys.exit(1)
