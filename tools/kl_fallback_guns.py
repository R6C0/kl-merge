#!/usr/bin/env python3
"""
kl_fallback_guns.py (2026-11-08, offline, nothing installed): the Page II shop set WITHOUT any Payday 2 data, made of Dead Men (DM) guns.

    python tools/kl_fallback_guns.py bake-set <map> [<map> ...] [--out=<dir>] [--src=<map folder>] [--base-ok]
                                              every pair of SPECS_FALLBACK on each map (DM gun where one is proven, else the STOCK gun, with the reason);
                                              <out>/<map>/ (zip, .ini files, report.json) + <out>/KLShopPage.ini ([Pairs] / [Desc] of the live structure, [Set] Name=dm)
    python tools/kl_fallback_guns.py bake <map> <out dir> [--item=33] [--host=..] [--dm=..] [--level=M01_FA_A] [--src=..] [--base-ok]   one pair
    python tools/kl_fallback_guns.py verify <out dir>        pd2_guns_multi.verify on every staged map + this file's own checks
    python tools/kl_fallback_guns.py restore <staged map dir> <dest dir>    the baked templates back on their previous root (report.json previous_root)

SAME ITEM IDS AND ROWS as the live Page II ([Pairs] P0..P12 of KLShopPage.ini): only the model, name and description differ, each gun on a template of its OWN
weapon class (never a heli / hind / player template: items 42-46, 48, 51 are not in the table). B&W cards are not touched here (kl_shop_pics keeps them).

ROUTE (a DM gun is already ROOT + parts + bones + materials + textures in Dog Days form, so pd2_guns_multi.fit_one / build_level, which want a PD2 plate, are not used):
  1 kl_chars.put (what kl_guns.build uses) converts the DM gun roots of the level into the map's .prm / .MAT / .TEX, once per template for the whole set.
  2 kl_guns._part makes a 64-byte copy of every rigid part for the HOST template's skeleton (bone by NAME, a missing one folds to its ancestor), variant 0.
  3 where the DM mesh is NOT in the host's space the parts get private geometry turned into the Dog Days hold (kl_map_guns.house); where it is (HK69, RPG-7: same vertex
    counts and box as the host's) the hold is the identity.
  4 a NEW root = copy of the host's root, object table = the DM parts + the host's hidden detail-16 box; .oct record appended; ONLY the host template's Ground node is
    retargeted (same as pd2_guns_multi.build_level). Stats, price, sound, animation stay the host's.

BASE: a no-PD2 build must start from stock gun roots. The source zip is classified (classify_base): 'stock' = no Weapons/W_PD2_* material; 'pd2-restored' = it was PD2 layered
and every PD2 template was first sent back to its stock root with pd2_guns_multi.restore_level (roots from the earlier layers' report.json via stock_roots; one with no report
is the skeleton+2 sibling, GUESS, checked); anything else is refused unless --base-ok ('unchecked'). report.json pins the source zip md5 and records base.

CLASS GUARD (CLASS_RULES): every class has an explicit rule; a launcher (grenade / rocket) is built only when the DM mesh is in the host's space (no fitted hold exists for
a launcher); a class without a rule, a pair whose DM class differs from the host's, or a hold whose measured grip / hand numbers are off, is REFUSED: the pair stays 'stock'.
GUESS marks are in the code (hold shift = AK-74's, detail 255 parts, the union box, LOD widening, the fit thresholds).

FIT (per gun): fit_hold solves a translation + small turn (FIT_SHIFT_MAX 6 cm, FIT_Z_MAX 3, FIT_DEG_MAX 2) from the AK-74 house hold that minimises grip gap + support hand + magazine
offset (same definitions as kl_map_guns.measure); strict guards GRIP_MAX 3 / HAND_MAX 4 / MAG_MAX 4 cm; a failed measurement or a missing hand on a two-handed class refuses the pair.
report.json records the fitted shift, turn, residuals, house baseline and the folded-bone count per gun.
SAME MODEL: a DM gun whose vertex buffers, bones and detail equal the host's (all four launchers) is mode 'stock-same-model': nothing baked, stock root kept, counted apart.
SEVERAL MAPS: every map must agree per pair, else the pair is stock on ALL maps. bake-set runs verify and prints SET RESULT PASS only if it passes.
WRITE GUARDS: bake / bake-set / restore refuse game folders (DD, DM), KL_PortBackup, dest == staged and a staged zip whose md5 differs from the report pin. bake also writes KLShopPage.ini.
pd2_guns_multi.py is NOT edited.
"""
import hashlib, json, math, os, re, shutil, struct, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_chars as C, kl_guns as K, kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_gms, kl_map_guns as MG, kl_pd2mask as PM
import pd2_guns_multi as M

DD = M.DD
MAPROOT = M.MAPROOT
LIVE_INI = os.path.join(DD, 'KLShopPage.ini')
OUT_DEFAULT = r'C:\kl_build_1024\nopd2_spike\out_set'
LEVEL = 'M01_FA_A'                      # every DM gun below is a template of this map (checked on the spike)
DEFAULT = dict(item=33, host='Rifle_Type81', dm='Rifle_SG552_01', level=LEVEL)
HIDDEN_DETAIL = 16                      # the host's hidden 'box' part (pd2_guns_multi: p.chunks[o][0x0e] == 16)
# STRICT guards, applied to the FITTED hold (fit_hold), never loosened to let one gun through:
GRIP_MAX = 3.0                          # GUESS (cm): refuse a hold whose mean grip gap after the fit is above this (the spike's SG 552 on the Type 81 measured 0.92)
HAND_MAX = 4.0                          # GUESS (cm): refuse a support-hand place further than this from the host's 'l hand attacher' (the spike measured 2.1)
MAG_MAX = 4.0                           # GUESS (cm): refuse a magazine centre further than this from the host's w_bone_clip parts (classes with a clip bone on both sides)
FIT_SHIFT_MAX = 6.0                     # GUESS (cm): the fitted x / y shift may leave HOUSE_SHIFT by this much at most (a fit further away is a different gun, not a hold)
FIT_Z_MAX = 3.0                         # GUESS (cm): the same for z
FIT_DEG_MAX = 2.0                       # GUESS (degrees): the fitted turn may leave HOUSE_DEG (-10, the same in every Dog Days gun frame, kl_map_guns) by this much at most: more would aim the barrel off the bullet line
FIT_WEIGHTS = (1.0, 1.0, 1.0)           # GUESS: cost = 1 * grip gap + 1 * |support hand| + 1 * |magazine| (cm)
EXT_REAR_MAX = 3.0                      # GUESS (cm): the fitted DM gun may reach this far behind the host's rear (kl_map_guns.cost penalises rear overhang: a stock in the arm)
EXT_FRONT_MAX = 5.0                     # GUESS (cm): the DM muzzle must be within this of the host's muzzle (either way: |front|)
EXT_BELOW_MAX = 6.0                     # GUESS (cm): no geometry further below the host's lowest point (y, 'up' is +y in the gun frame) than this
EXT_BOX_MAX = 8.0                       # GUESS (cm): root-box overhang on any side (the full-detail parts' box stands in for the host's root box)
TURN_PENALTY = 0.1                      # GUESS (cm of cost per degree): light tie-break toward the house turn, so a flat valley (the USP) settles near HOUSE_DEG
PIN_TOL = 1e-3                          # a fitted shift / turn this close to its clamp bound wanted to leave the bound: refused
SAME_BOX = 0.05                         # cm: DM and host geometry boxes closer than this = the same space (identity hold)


class Refuse(Exception):
    """A pair that must stay on its stock gun; str() is the reason written to report.json / the summary."""


# ------------------------------------------------------------------ the table
# DM template -> weapon class (the class names of pd2_guns_multi.CLASS_WT); every template is a template of LEVEL
DM_CLASS = {'HG_HK_USP_01': 'pistol', 'Rifle_SG552_01': 'rifle', 'Rifle_M4A1_01': 'rifle', 'Rifle_AK74_01': 'rifle', 'Mg_Minimi_SPW_01': 'mg', 'MG_PKMSN2_01': 'mg',
            'Sn_Rem700_01': 'sniper', 'Launcher_HK69A1_01': 'grenade', 'Launcher_HK69A1_01Flare': 'grenade', 'Launcher_HK69A1_01TearGas': 'grenade', 'RPG_7V': 'rocket'}

# one rule per class. hold: 'house' = the DM mesh is turned into the Dog Days hold (measured, guarded), 'same' = only when it already is in the host's space.
CLASS_RULES = {'pistol': dict(hold='house'), 'rifle': dict(hold='house'), 'mg': dict(hold='house'), 'sniper': dict(hold='house'),
               'grenade': dict(hold='same'), 'rocket': dict(hold='same')}


def host_of(item):
    """The Dog Days host template of a shop item as pd2_guns_multi.SPECS pins it (the last non-heli spec of the item)."""
    hs = [s for s in M.SPECS if s['item'] == item and not M.HELI_RE.search(s['template'])]
    if not hs:
        raise ValueError('item %d: no non-heli spec in pd2_guns_multi.SPECS' % item)
    return hs[-1]['template']


def _row(pair, item, cls, dm, name, why=None):
    return dict(pair=pair, item=item, cls=cls, host=host_of(item), dm=dm, level=LEVEL, name=name, why=why)


# pair -> item (the order of the live KLShopPage.ini [Pairs]); dm=None = a pair with no DM gun of its class: it stays STOCK (why = the reason)
SPECS_FALLBACK = [
    _row(0, 62, 'pistol', 'HG_HK_USP_01', 'USP'),
    _row(1, 63, 'pistol', None, 'M9', 'DM has one pistol model (the USP, used on item 62): a second look would be the same gun'),
    _row(2, 54, 'grenade', 'Launcher_HK69A1_01Flare', 'HK69 FLARE'),
    _row(3, 53, 'grenade', 'Launcher_HK69A1_01TearGas', 'HK69 GAS'),
    _row(4, 52, 'grenade', 'Launcher_HK69A1_01', 'HK69'),
    _row(5, 50, 'rocket', 'RPG_7V', 'RPG-7'),
    _row(6, 40, 'mg', 'MG_PKMSN2_01', 'PKM'),
    _row(7, 47, 'mg', 'Mg_Minimi_SPW_01', 'MINIMI'),
    _row(8, 41, 'mg', None, 'MG', 'DM has two light machine guns (PKM, Minimi), both used on items 40 and 47'),
    _row(9, 33, 'rifle', 'Rifle_SG552_01', 'SG 552'),
    _row(10, 35, 'rifle', 'Rifle_M4A1_01', 'M4A1'),
    _row(11, 38, 'rifle', 'Rifle_AK74_01', 'AK-74'),
    _row(12, 49, 'sniper', 'Sn_Rem700_01', 'REM 700'),
]


def table_problems():
    """Pure. [] when the table holds its invariants: item in the pool, not a heli item / template, class(host) == class(DM), one pair per item."""
    bad, seen = [], set()
    for s in SPECS_FALLBACK:
        it = s['item']
        if it not in M.POOL_ITEMS:
            bad.append('pair %d item %d is not in POOL_ITEMS' % (s['pair'], it))
        if it in (42, 43, 44, 45, 46, 48, 51) or M.HELI_RE.search(s['host']):
            bad.append('pair %d item %d host %s is a heli / hind / player template' % (s['pair'], it, s['host']))
        if it in seen:
            bad.append('item %d twice' % it)
        seen.add(it)
        hostc = {M.spec_class(x) for x in M.SPECS if x['item'] == it and x['template'] == s['host']}
        if len(hostc) != 1:
            bad.append('pair %d: host %s of item %d has no single class (%s)' % (s['pair'], s['host'], it, sorted(hostc)))
        if s['cls'] not in CLASS_RULES:
            bad.append('pair %d: class %s has no rule' % (s['pair'], s['cls']))
        if hostc and s['cls'] not in hostc:
            bad.append('pair %d: class %s != host class %s' % (s['pair'], s['cls'], sorted(hostc)))
        if s['dm'] is not None:
            if DM_CLASS.get(s['dm']) != s['cls']:
                bad.append('pair %d: DM %s is class %s, the pair %s' % (s['pair'], s['dm'], DM_CLASS.get(s['dm']), s['cls']))
        elif not s['why']:
            bad.append('pair %d: a stock pair without a reason' % s['pair'])
    return bad


_bad = table_problems()
if _bad:
    raise AssertionError('SPECS_FALLBACK: ' + '; '.join(_bad))


# ------------------------------------------------------------------ the per-gun hold fit
def _np():
    import numpy
    return numpy


def _nearest(a, b):
    """numpy: distance of every row of a (n,3) to the nearest row of b (m,3), chunked."""
    np = _np()
    out = []
    for i in range(0, len(a), 256):
        d2 = ((a[i:i + 256, None, :] - b[None, :, :]) ** 2).sum(2)
        out.append(np.sqrt(d2.min(1)))
    return np.concatenate(out)


class HoldCtx:
    """Arrays the fit needs of one (DM look, host) pairing; shape() dicts of kl_map_guns."""

    def __init__(self, look, host):
        np = _np()
        self.host_b = np.array([v for v in MG._points(host) if MG._in_zone(v, 2.0)], dtype=float).reshape(-1, 3)
        a = np.array(MG._points(look), dtype=float).reshape(-1, 3)
        pt, _v = MG.house((0.0, 0.0, 0.0))
        # prune: a point that can never reach the zone under any allowed shift / turn is dropped (grow = FIT_SHIFT_MAX + the turn's lever, 70 cm * 2 degrees = 2.5 cm, + HOUSE_SHIFT)
        grow = FIT_SHIFT_MAX + 6.0 + abs(MG.HOUSE_SHIFT[0]) + abs(MG.HOUSE_SHIFT[1])
        keep = [q for q in a if MG._in_zone(pt(tuple(q)), grow)]
        self.look_a = np.array(keep, dtype=float).reshape(-1, 3)
        self.lh, self.ll = host['bones'].get('l hand attacher'), look['bones'].get('l hand attacher')
        self.cl = np.array([v for b, vs in look['parts'] if b == 'w_bone_clip' for v in vs], dtype=float).reshape(-1, 3)
        self.ch = np.array([v for b, vs in host['parts'] if b == 'w_bone_clip' for v in vs], dtype=float).reshape(-1, 3)
        self.evals = 0


def hold_eval(ctx, shift, deg):
    """The three residuals of the DM look turned by `deg` and shifted by `shift` (kl_map_guns.house) against the host's bones, in cm, the same definitions as
    kl_map_guns.measure: grip = mean gap (worst 30 % left out) of the look's points in GRIP_ZONE to the host's surface; hand = the look's 'l hand attacher' (+ LHAND_CONV)
    minus the host's (x, y) or None; mag = the look's w_bone_clip box centre minus the host's (x, y) or None. -> dict(grip, hand, mag, cost)."""
    np = _np()
    ctx.evals += 1
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    A = ctx.look_a
    X, Y, Z = c * A[:, 0] - s * A[:, 1] + shift[0], s * A[:, 0] + c * A[:, 1] + shift[1], A[:, 2] + shift[2]
    z = MG.GRIP_ZONE
    m = (X >= z[0]) & (X <= z[1]) & (Y >= z[2]) & (Y <= z[3])
    grip = None
    if m.sum() >= 10 and len(ctx.host_b) >= 10:
        d = np.sort(_nearest(np.stack([X[m], Y[m], Z[m]], 1), ctx.host_b))
        d = d[:max(8, int(len(d) * 0.7))]
        grip = float(d.mean())
    pt, _vec = MG.house(shift, deg)
    hand = None
    if ctx.lh and ctx.ll:
        q = pt(ctx.ll[9:12])
        hand = (q[0] + MG.LHAND_CONV[0] - ctx.lh[9], q[1] + MG.LHAND_CONV[1] - ctx.lh[10])
    mag = None
    if len(ctx.cl) and len(ctx.ch):
        X2, Y2 = c * ctx.cl[:, 0] - s * ctx.cl[:, 1] + shift[0], s * ctx.cl[:, 0] + c * ctx.cl[:, 1] + shift[1]
        mag = (float((X2.min() + X2.max()) / 2 - (ctx.ch[:, 0].min() + ctx.ch[:, 0].max()) / 2),
               float((Y2.min() + Y2.max()) / 2 - (ctx.ch[:, 1].min() + ctx.ch[:, 1].max()) / 2))
    w = FIT_WEIGHTS
    cost = w[0] * (grip if grip is not None else 10.0) + w[1] * (math.hypot(*hand) if hand else 0.0) + w[2] * (math.hypot(*mag) if mag else 0.0)
    return dict(grip=grip, hand=hand, mag=mag, cost=cost)


def _res(e):
    """A hold_eval dict as plain rounded numbers for report.json."""
    r = lambda x: None if x is None else round(x, 3)
    return dict(grip=r(e['grip']), hand=None if e['hand'] is None else [r(e['hand'][0]), r(e['hand'][1])],
                hand_len=None if e['hand'] is None else r(math.hypot(*e['hand'])), mag=None if e['mag'] is None else [r(e['mag'][0]), r(e['mag'][1])],
                mag_len=None if e['mag'] is None else r(math.hypot(*e['mag'])), cost=r(e['cost']))


def extent_of(look, host, shift, deg):
    """Overhang of the fitted DM look against the host, in cm (kl_map_guns.measure's rear / front, plus the box on every side): points of all full-detail parts (clip
    included; the hidden box part is not in shape()) through house(shift, deg). rear = host min x - look min x, front = look max x - host max x (x = along the barrel),
    below = host min y - look min y; box = the largest overhang of the look's box beyond the host's on any of the 6 sides. GUESS: the shape() points stand in for the root box."""
    pt, _v = MG.house(tuple(shift), deg)
    a = [pt(v) for v in MG._points(look, True)]
    h = MG._points(host, True)
    lo = lambda pts, i: min(q[i] for q in pts)
    hi = lambda pts, i: max(q[i] for q in pts)
    sides = [lo(h, i) - lo(a, i) for i in range(3)] + [hi(a, i) - hi(h, i) for i in range(3)]
    return dict(rear=round(sides[0], 3), front=round(sides[3], 3), below=round(sides[1], 3), box=round(max(sides), 3))


def extent_problem(ext, lim=None):
    """Pure. None = pass, else the reason for an extent record of extent_of()."""
    lim = lim or dict(EXT_REAR_MAX=EXT_REAR_MAX, EXT_FRONT_MAX=EXT_FRONT_MAX, EXT_BELOW_MAX=EXT_BELOW_MAX, EXT_BOX_MAX=EXT_BOX_MAX)
    if ext['rear'] > lim['EXT_REAR_MAX']:
        return 'rear overhang %.1f cm behind the host (limit %.1f)' % (ext['rear'], lim['EXT_REAR_MAX'])
    if abs(ext['front']) > lim['EXT_FRONT_MAX']:
        return 'muzzle %.1f cm off the host muzzle (limit %.1f)' % (ext['front'], lim['EXT_FRONT_MAX'])
    if ext['below'] > lim['EXT_BELOW_MAX']:
        return 'geometry %.1f cm below the host lowest point (limit %.1f)' % (ext['below'], lim['EXT_BELOW_MAX'])
    if ext['box'] > lim['EXT_BOX_MAX']:
        return 'root box overhangs the host box by %.1f cm (limit %.1f)' % (ext['box'], lim['EXT_BOX_MAX'])
    return None


def pinned_axis(fit):
    """Pure. The first axis of a fit record whose shift / turn sits on its clamp bound (within PIN_TOL), else None."""
    sh = fit.get('shift')
    if sh is None or fit.get('deg') is None:
        return None
    x0 = [MG.HOUSE_SHIFT[0], MG.HOUSE_SHIFT[1], MG.HOUSE_SHIFT[2], MG.HOUSE_DEG]
    lim = [FIT_SHIFT_MAX, FIT_SHIFT_MAX, FIT_Z_MAX, FIT_DEG_MAX]
    x = list(sh) + [fit['deg']]
    for i, nm in enumerate(('shift x', 'shift y', 'shift z', 'turn')):
        if abs(abs(x[i] - x0[i]) - lim[i]) <= PIN_TOL:
            return nm
    return None


def fit_hold(look, host):
    """PER-GUN hold fit. Pattern search over (x, y, z shift in cm, turn in degrees) starting from kl_map_guns' house() (HOUSE_SHIFT, HOUSE_DEG = the AK-74's), minimising
    grip gap + |support hand| + |magazine| (FIT_WEIGHTS), inside FIT_SHIFT_MAX / FIT_Z_MAX / FIT_DEG_MAX of the start. The turn is about the model origin, which is the
    right hand's grip place (GRIP_ZONE is centred there): GUESS that this makes it 'a small rotation about the grip'. -> dict(shift, deg, **residuals, base=residuals at house())."""
    ctx = HoldCtx(look, host)
    x0 = [MG.HOUSE_SHIFT[0], MG.HOUSE_SHIFT[1], MG.HOUSE_SHIFT[2], MG.HOUSE_DEG]
    lim = [FIT_SHIFT_MAX, FIT_SHIFT_MAX, FIT_Z_MAX, FIT_DEG_MAX]
    ev = lambda x: hold_eval(ctx, (x[0], x[1], x[2]), x[3])
    pen = lambda x: TURN_PENALTY * abs(x[3] - MG.HOUSE_DEG)       # tie-break only; the recorded cost stays the raw one
    base = ev(x0)
    x, best = list(x0), base
    bobj = base['cost'] + pen(x0)
    step = [1.0, 1.0, 0.5, 1.0]
    floor = [0.01, 0.01, 0.01, 0.02]
    while any(step[i] >= floor[i] for i in range(4)):
        moved = False
        for i in range(4):
            if step[i] < floor[i]:
                continue
            for sg in (1, -1):
                y = list(x)
                y[i] = min(x0[i] + lim[i], max(x0[i] - lim[i], x[i] + sg * step[i]))
                if y[i] == x[i]:
                    continue
                e = ev(y)
                if e['cost'] + pen(y) < bobj - 1e-9:
                    x, best, moved, bobj = y, e, True, e['cost'] + pen(y)
        if not moved:
            step = [t / 2 for t in step]
    out = dict(shift=[round(v, 3) for v in x[:3]], deg=round(x[3], 3), evals=ctx.evals, **_res(best))
    out['base'] = _res(base)
    out['turn_penalty'] = TURN_PENALTY
    out['extent'] = extent_of(look, host, x[:3], x[3])
    return out


# ------------------------------------------------------------------ geometry helpers
def _turn_parts(p, parts, shift=None, deg=None):
    """kl_map_guns.refit's body for a list of part objects: private sub table + descriptor + vertex chunk, positions and packed normals through house(shift, deg)."""
    pt, vec = MG.house(MG.HOUSE_SHIFT if shift is None else shift, MG.HOUSE_DEG if deg is None else deg)
    done = {}
    for o in parts:
        subs = []
        for d in MG._descriptors(p, o):
            if d not in done:
                dv = list(struct.unpack('<12I', p.chunks[d]))
                dv[1] = G.new_chunk(p, MG._turn_vertices(p.chunks[dv[1]], dv[0], pt, vec), p.refs[dv[1]])
                done[d] = G.new_chunk(p, struct.pack('<12I', *dv), p.refs[d])
            subs.append(done[d])
        old = p.chunks[p.u32(o, 0x28)]
        sub = G.new_chunk(p, struct.pack('<%dI' % len(subs), *subs) + old[4 * len(subs):], p.refs[p.u32(o, 0x28)])
        p.chunks[o] = C._put(p.chunks[o], 0x28, '<I', sub)
    return done


def _box(p, parts):
    pts = []
    for o in parts:
        for d in MG._descriptors(p, o):
            nv, v = p.u32(d, 0), p.chunks[p.u32(d, 4)]
            pts += [struct.unpack_from('<3f', v, MG.V_STRIDE * i) for i in range(nv)]
    return tuple(tuple(f(q[k] for q in pts) for k in range(3)) for f in (min, max))


def _vcount(p, o):
    return sum(p.u32(d, 0) for d in MG._descriptors(p, o))


def same_space(p, host_parts, dm_parts):
    """True when the DM gun's geometry IS the host's (HK69, RPG-7 of both games: the same vertex counts per part and the same box): the hold is the identity."""
    if sorted(_vcount(p, o) for o in host_parts) != sorted(_vcount(p, o) for o in dm_parts):
        return False
    a, b = _box(p, host_parts), _box(p, dm_parts)
    return all(abs(a[i][k] - b[i][k]) <= SAME_BOX for i in (0, 1) for k in range(3))


def mesh_signature(p, root, objs):
    """On an open .prm: what makes a gun's drawn mesh the same mesh. Per part (lower-case bone name, detail without the hidden-box bit 16 [GUESS: that bit is only
    the host's hidden box part and does not change what is drawn], md5 of its vertex buffers + their counts) and, for every bone a part sits on, the bone's rest matrix
    (3 decimals). -> (sorted part list, sorted bone list)."""
    sk = C.skeleton(p, root)
    names = C.bone_names(p, sk)
    rest = C._rest(p, sk)
    parts, bones = [], set()
    for o in objs:
        h = hashlib.md5()
        for d in MG._descriptors(p, o):
            nv = p.u32(d, 0)
            h.update(struct.pack('<I', nv)); h.update(p.chunks[p.u32(d, 4)][:nv * MG.V_STRIDE])
        b = p.u32(o, 0x3c)
        parts.append((names[b].lower(), p.chunks[o][0x0e] & 0xEF, h.hexdigest()))
        bones.add((names[b].lower(), tuple(round(x, 3) for x in rest[b])))
    return sorted(parts), sorted(bones)


def same_mesh(p, host_root, host_parts, dm_root, dm_parts):
    """True when the DM gun is, mesh for mesh, the host's own model (Dog Days already ships Dead Men's HK69 and RPG-7): vertex buffers, bones and detail all equal."""
    return mesh_signature(p, host_root, host_parts) == mesh_signature(p, dm_root, dm_parts)


def lod_detail(p, parts, host_mask, drop_box_bit):
    """The detail (LOD mask, +0x0e) of the new parts. GUESS: (a) a DM part with the box bit 16 set (SG 552 parts are 255) loses it when the host keeps its own hidden detail-16
    box part, so the box stays the host's; (b) an LOD bit the host's parts cover and the DM parts together do not (the DM gun would vanish at that distance) is added to the parts
    that show at full detail (bit 1; else the first part). -> {object: new detail}."""
    det = {o: p.chunks[o][0x0e] & (0xEF if drop_box_bit else 0xFF) for o in parts}
    cover = 0
    for v in det.values():
        cover |= v
    miss = host_mask & ~cover & (0xEF if drop_box_bit else 0xFF)
    if miss:
        near = [o for o in parts if det[o] & 1] or parts[:1]
        for o in near:
            det[o] |= miss
    return det


# ------------------------------------------------------------------ one pair
def import_dms(lv, level, dms, log=print):
    """One kl_chars.put for every distinct DM template (one extract: what the guns share stays shared). -> {dm template: root in the map's .prm}."""
    src = C.Source.get(level, log)
    dms = sorted(set(dms))
    picks = [C.Pick((), level, src.sc.path[K.gun_node(src.sc, t)][5:], {0: 0}) for t in dms]
    # reuse=False: the dead chunks of a layered map hold the STOCK roots that restore_level (earlier report.json stock_root ids) needs back: never overwrite them
    rep = C.put(lv, picks, free='none', log=log, reuse=False)
    return {t: pk['new_model'] for t, pk in zip(dms, rep['picks'])}


def guard_fit(fit, cls):
    """Pure. The STRICT guards on a fit_hold() result; None = pass, else the reason text."""
    pin = pinned_axis(fit)
    if pin:
        return 'fit pinned to bound %s (the fit wanted to leave its clamp)' % pin
    if fit.get('grip') is None:
        return 'too few points around the hand to measure the grip'
    if fit['grip'] > GRIP_MAX:
        return 'grip gap %.2f cm after the fitted hold (limit %.1f; at the house hold %s)' % (fit['grip'], GRIP_MAX, (fit.get('base') or {}).get('grip'))
    if cls != 'pistol' and fit.get('hand') is None:
        return 'no support-hand bone (l hand attacher) on one side: a two-handed class cannot be checked'
    if fit.get('hand') is not None and fit['hand_len'] > HAND_MAX:
        return 'support hand %.1f cm off after the fitted hold (limit %.1f; at the house hold %s)' % (fit['hand_len'], HAND_MAX, (fit.get('base') or {}).get('hand_len'))
    if fit.get('mag') is not None and fit['mag_len'] > MAG_MAX:
        return 'magazine %.1f cm off the host clip bone after the fitted hold (limit %.1f)' % (fit['mag_len'], MAG_MAX)
    if fit.get('extent') is not None:
        why = extent_problem(fit['extent'])
        if why:
            return why
    return None


def plan(lv, item, host, dm, dm_root, cls, expect_root=None):
    """READ ONLY decision of one pair. Raises Refuse (the pair stays stock, str() = the reason). -> dict(mode, ...):
      mode 'stock-same-model': the DM gun is mesh for mesh the host's stock model (same_mesh): nothing is baked, the stock root stays;
      mode 'dm': bake it; same = identity hold (launcher in the host's space), else fit = fit_hold() residuals that passed the STRICT guards."""
    rule = CLASS_RULES.get(cls)
    if rule is None:
        raise Refuse('class %s has no rule' % cls)
    sc, _raw = lv.scene()
    p = G.read(lv['.prm'], 'dd')
    try:
        k = K.gun_node(sc, host)
    except ValueError as e:
        raise Refuse('%s: %s' % (host, e))
    old, var, _aset = C.person(sc, k)
    if var != 0:
        raise Refuse('%s: the gun entity has variant %d' % (host, var))
    if expect_root is not None and old != expect_root:
        raise Refuse('%s: the template is on root %d, not the stock root %d' % (host, old, expect_root))
    hidden = [o for o in C.objects(p, old) if p.chunks[o][0x0e] == HIDDEN_DETAIL]
    shown = [o for o in C.objects(p, old) if o not in hidden]
    dm_objs = C.objects(p, dm_root)
    base = dict(old=old, hidden=len(hidden), shown=len(shown), dm_parts=len(dm_objs))
    if same_mesh(p, old, shown, dm_root, dm_objs):
        return dict(base, mode='stock-same-model', same=True, fit=None,
                    reason='%s is mesh for mesh the stock model of %s (same vertex buffers, bones, detail): Dog Days already ships this gun, stock root kept, nothing baked' % (dm, host))
    same = same_space(p, shown, dm_objs)
    if rule['hold'] == 'same' and not same:
        raise Refuse('%s: a %s launcher whose mesh is not in the host\'s space: no fitted hold exists for launchers' % (dm, cls))
    if same:
        return dict(base, mode='dm', same=True, fit=dict(identity=True), reason=None)
    try:
        fit = fit_hold(MG.shape(p, dm_root), MG.shape_of_objects(p, old, shown))
    except Exception as e:
        raise Refuse('%s on %s: the hold measurement failed (%s: %s)' % (dm, host, type(e).__name__, str(e)[:100]))
    why = guard_fit(fit, cls)
    if why:
        raise Refuse('%s on %s: %s' % (dm, host, why))
    return dict(base, mode='dm', same=False, fit=fit, reason=None)


def place(lv, item, host, dm, dm_root, cls, expect_root=None, log=print, pl=None):
    """lv (kl_chars.Lv, edited in place ONLY when this returns): the DM gun at `dm_root` on the Ground node of host template `host` (shop item `item`).
    Raises Refuse (lv untouched) when plan() says no or says 'stock-same-model'. -> report dict (the shape pd2_guns_multi.verify reads)."""
    pl = pl or plan(lv, item, host, dm, dm_root, cls, expect_root)
    if pl['mode'] != 'dm':
        raise Refuse(pl['reason'])
    same, fit = pl['same'], pl['fit']
    sc, raw = lv.scene(); raw = bytearray(raw)
    models = C.gms_models(raw)
    p, mat = G.read(lv['.prm'], 'dd'), T.read_mat(lv['.MAT'])
    k = K.gun_node(sc, host)
    old = C.person(sc, k)[0]
    hidden = [o for o in C.objects(p, old) if p.chunks[o][0x0e] == HIDDEN_DETAIL]
    shown = [o for o in C.objects(p, old) if o not in hidden]
    dm_objs = C.objects(p, dm_root)
    sk = C.skeleton(p, old)
    dst = {s.lower(): i for i, s in enumerate(C.bone_names(p, sk))}
    ssk = C.skeleton(p, dm_root)
    names, par = C.bone_names(p, ssk), C.bone_parents(p, ssk)
    note = dict(folded=0)
    parts = [K._part(p, o, names, par, dst, 0, note) for o in dm_objs]
    if not any(p.chunks[o][0x0e] & 1 for o in parts):
        raise Refuse('%s: no part at full detail' % dm)
    host_mask = 0
    for o in shown:
        host_mask |= p.chunks[o][0x0e]
    det = lod_detail(p, parts, host_mask, bool(hidden))
    for o in parts:
        if det[o] != p.chunks[o][0x0e]:
            c = bytearray(p.chunks[o]); c[0x0e] = det[o]; p.chunks[o] = bytes(c)
    if not same:
        _turn_parts(p, parts, fit['shift'], fit['deg'])
    root = C._new(p, p.chunks[old]); p.refs[root] = 1
    C._set_objects(p, root, parts + hidden)
    box = _box(p, parts)
    PM.widen_root(p, root, box)       # GUESS: the root's union box (+0x20) grows to the DM geometry, as build_level does with the PD2 box
    ref = p.u32(old, 0x1c)
    oct_s = O.Oct.parse(lv['.oct'])
    if ref:
        refs0 = oct_s.record_refs(); rec_of = {x: n for n, x in enumerate(refs0)}
        r = oct_s.records[rec_of[ref]]
        if r.tree.items:
            raise Refuse('%s: the .oct record of the root is not an empty tree' % host)
        oct_s.records.append(O.Record(r.vtable, r.pointer, O.Tree(r.tree.origin, r.tree.scale, [list(x) for x in r.tree.nodes], [], r.tree.fill)))
        refs1 = oct_s.record_refs()
        if refs1[:len(refs0)] != refs0:
            raise Refuse('appending an .oct record moved the base level records')
        p.chunks[root] = C._put(p.chunks[root], 0x1c, '<I', refs1[len(refs0)])
    K._retarget(sc, raw, models, k, root)             # ONLY this template's Ground node
    prm = G.write(p)
    mat.refs = T.material_refs(prm)
    lv['.prm'], lv['.MAT'], lv['.oct'] = prm, T.write_mat(mat), oct_s.pack()
    lv['.gms'], lv['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    shift = [0.0, 0.0, 0.0] if same else list(fit['shift'])
    log('  item %d %s <- %s: root %d -> %d, %d parts (%d folded bones), %s' % (item, host, dm, old, root, len(parts), note['folded'],
        'identity hold' if same else 'fitted hold shift %s turn %.2f (grip %.2f hand %s mag %s)' % (fit['shift'], fit['deg'], fit['grip'], fit['hand_len'], fit['mag_len'])))
    return dict(item=item, template=host, stock_root=old, previous_root=old, root=root, body_object=parts[0], parts=len(parts), dm_template=dm, dm_level=LEVEL, dm_root=dm_root,
                cls=cls, same_space=same, details=[det[o] for o in parts], body_vertices=0, body_triangles=0, magazine=True, outward_share=1.0,
                material_slot=[p.u16(o, 0x12) for o in parts], textures=[], shift=shift, deg=(0.0 if same else fit['deg']), fit=fit,
                folded_bones=note['folded'],
                box=[[round(x, 2) for x in box[0]], [round(x, 2) for x in box[1]]])


# ------------------------------------------------------------------ where this tool may write
class Unsafe(ValueError):
    """A path this tool must never write to (a game folder, KL_PortBackup) or a staged map that does not match its report pin."""


DM_DIR = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men'
GAME_DIRS = [DD, DM_DIR]
SCRATCH_OK = [os.path.join(DM_DIR, 'KL_PortTools', 'build')]       # the one place inside a game folder that is build scratch


def _under(path, root):
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:                                              # another drive
        return False


def _norm(path):
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def out_problem(path):
    """Pure. None when `path` may be written, else the reason: it names KL_PortBackup, or lies inside the Dog Days / Dead Men game folder (the build scratch
    <DM>\\KL_PortTools\\build excepted)."""
    ap = _norm(path)
    if 'kl_portbackup' in ap.split(os.sep):
        return '%s is inside KL_PortBackup' % path
    if any(_under(ap, _norm(s)) for s in SCRATCH_OK):
        return None
    for g in GAME_DIRS:
        if _under(ap, _norm(g)):
            return '%s is inside the game folder %s' % (path, g)
    return None


def require_out(path):
    why = out_problem(path)
    if why:
        raise Unsafe('refusing to write: ' + why)


# ------------------------------------------------------------------ base: stock or PD2 layered
def pd2_markers(lv):
    """Names of the PD2 gun materials in the map ('Weapons/W_PD2_*'): non-empty = the zip is PD2 layered."""
    mat = T.read_mat(lv['.MAT'])
    return sorted(e.name for e in mat.insts.values() if e.name and 'W_PD2_' in e.name)


def guess_stock_root(p, cur):
    """A template's stock root when no earlier report names it (pd2_gun's AKM on Rifle_Type81). GUESS: in every stock gun of this game the root chunk is its skeleton chunk + 2
    (2418/2416, 4878/4876, 4836/4834, 2700/2698 ...); accepted only when that chunk is below `cur`, has objects and names the same skeleton. classify_base then checks it
    against a pre-PD2 copy of the zip (stock_root_evidence) when one exists."""
    sk = C.skeleton(p, cur)
    cand = sk + 2
    if cand < cur and C.objects(p, cand) and C.skeleton(p, cand) == sk:
        return cand
    return None


def _lv_of_zip(path):
    """A read-only kl_chars.Lv of a lone zip (a '.before-*' copy: C.Lv wants a folder holding exactly one *_Main.zip)."""
    import zipfile
    lv = C.Lv.__new__(C.Lv)
    with zipfile.ZipFile(path) as z:
        lv.order = z.namelist()
        lv.files = {n: z.read(n) for n in lv.order}
    lv.ext = {n.rsplit('_Main', 1)[1]: n for n in lv.order if '_Main' in n}
    lv.name = next(n for n in lv.order if '_Main' in n).split('/')[-1].split('_Main')[0]
    lv.src, lv.beside, lv.side = path, {}, {}
    return lv


def stock_root_evidence(src_dir, cur_prm, templates, log=print):
    """READ ONLY evidence for stock roots that are not pinned by an earlier PD2 layer report: the smallest '<slot>_Main.zip.before-*' copy beside the live zip that has no
    W_PD2 material (made before any PD2 layer: the shop-button / shop-picture backups) names, for each template, the root of its Ground node. The root chunk and its
    object chunks must also be byte-equal in the layered .prm (layers only append). -> {template: dict(root, zip, zip_bytes, chunks, root_chunk_equal, objects_equal)} ({} = no usable copy)."""
    import glob
    cands = sorted((f for f in glob.glob(os.path.join(src_dir, '*_Main.zip.before-*')) if not f.lower().endswith('.bots.zip') and '.bots.zip' not in f.lower()),
                   key=os.path.getsize)
    for f in cands:
        try:
            lv = _lv_of_zip(f)
            if pd2_markers(lv):
                continue
            sc, _raw = lv.scene()
            p0 = G.read(lv['.prm'], 'dd')
        except Exception as e:
            log('  evidence copy %s unusable (%s)' % (os.path.basename(f), str(e)[:80]))
            continue
        out = {}
        for t in templates:
            try:
                r = C.person(sc, K.gun_node(sc, t))[0]
            except Exception:
                continue
            objs = C.objects(p0, r)
            out[t] = dict(root=r, zip=os.path.basename(f), zip_bytes=os.path.getsize(f), chunks=len(p0.chunks), no_pd2_materials=True,
                          root_chunk_equal=r < len(cur_prm.chunks) and p0.chunks[r] == cur_prm.chunks[r],
                          objects_equal=bool(objs) and all(o < len(cur_prm.chunks) and p0.chunks[o] == cur_prm.chunks[o] for o in objs))
        return out
    return {}


def classify_base(lv, name, hosts, log=print, base_ok=False, src_dir=None):
    """-> (base, restores, roots, notes, evidence). base 'stock' | 'pd2-restored' | 'unchecked'; restores = [(key, item, template)] for restore_level; roots = {template: (stock root,
    chunks, source)}; evidence = {template: stock_root_evidence entry + 'verdict'}.
    PD2 layered: every PD2 template (the hosts plus every pd2_guns_multi.SPECS template) with a stock root goes back; an unresolvable host raises Refuse unless base_ok. A host root
    that comes from the skeleton+2 GUESS is checked against the pre-PD2 copy (the evidence wins on a mismatch); one pinned by an earlier report that the copy contradicts raises Refuse."""
    marks = pd2_markers(lv)
    if not marks:
        return 'stock', [], {}, [], {}
    sc, _raw = lv.scene()
    p = G.read(lv['.prm'], 'dd')
    n = len(p.chunks)
    want = sorted(set(hosts) | {s['template'] for s in M.SPECS})
    notes = []
    try:
        found = M.stock_roots(name, set(want))
    except Exception as e:
        if not base_ok:
            raise Refuse('PD2 layered base and the stock roots cannot be resolved: %s (--base-ok to build anyway)' % e)
        return 'unchecked', [], {}, ['stock_roots: %s' % e], {}
    roots = {t: (sr, n, f) for t, (sr, _b, f) in found.items()}
    guessed = set()
    for t in want:
        if t in roots:
            continue
        try:
            cur = C.person(sc, K.gun_node(sc, t))[0]
        except Exception:
            continue                                         # the map has no such template
        g = guess_stock_root(p, cur) if t in hosts else None
        if g is not None:
            roots[t] = (g, n, 'skeleton+2 sibling (GUESS)'); guessed.add(t)
        elif t in hosts:
            if not base_ok:
                raise Refuse('PD2 layered base: no stock root for %s (--base-ok to build anyway)' % t)
            notes.append('%s: no stock root, left as it is' % t)
    evid = stock_root_evidence(src_dir, p, sorted(roots), log) if src_dir else {}
    for t in sorted(roots):
        e = evid.get(t)
        if e is None:
            if t in guessed:
                notes.append('%s: stock root %d is the skeleton+2 sibling (GUESS), NO pre-PD2 copy to check it against' % (t, roots[t][0]))
            continue
        agree = e['root'] == roots[t][0] and e['root_chunk_equal'] and e['objects_equal']
        e['verdict'] = 'confirmed by %s (no W_PD2 material, %d chunks): same root, same chunks' % (e['zip'], e['chunks']) if agree else 'CONTRADICTED'
        if agree:
            if t in guessed:
                notes.append('%s: stock root %d (skeleton+2 GUESS) CONFIRMED by pre-PD2 copy %s' % (t, e['root'], e['zip']))
            continue
        if t in guessed and e['root_chunk_equal'] and e['objects_equal']:
            e['verdict'] = 'GUESS %d was wrong: the pre-PD2 copy names root %d (chunks equal), used' % (roots[t][0], e['root'])
            roots[t] = (e['root'], n, 'pre-PD2 copy ' + e['zip'])
            notes.append('%s: %s' % (t, e['verdict']))
        else:
            raise Refuse('%s: stock root %s contradicts the pre-PD2 copy %s (root %s, root chunk equal %s, objects equal %s)' % (
                t, roots[t][0], e['zip'], e['root'], e['root_chunk_equal'], e['objects_equal']))
    restores = [('R%d' % i, _item_of(t), t) for i, t in enumerate(sorted(roots))]
    log('  base PD2 layered (%d W_PD2 materials): restoring %d templates to their stock roots (%d checked against a pre-PD2 copy)' % (len(marks), len(roots), len(evid)))
    return 'pd2-restored', restores, roots, notes, evid


def _item_of(t):
    for s in M.SPECS:
        if s['template'] == t:
            return s['item']
    return 0


# ------------------------------------------------------------------ one map
def md5(f):
    h = hashlib.md5()
    with open(f, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


STOCK_MODES = ('stock', 'stock-same-model')


def measure_set(name, specs=None, src=None, base_ok=False, log=print):
    """READ ONLY pass of one map: base, restore, every DM gun imported into a scratch Lv (never written), plan() of every pair. -> {item: dict(mode, reason, plan)}."""
    specs = specs or SPECS_FALLBACK
    src = src or os.path.join(MAPROOT, name)
    lv = C.Lv(src); lv.beside, lv.side = {}, {}
    hosts = {s['host'] for s in specs}
    base, restores, roots, _notes, _ev = classify_base(lv, name, hosts, log, base_ok, src)
    if restores:
        M.restore_level(lv, restores, name, log=log, roots=roots)
    stock_of = {t: r[0] for t, r in roots.items()}
    todo = [s for s in specs if s['dm']]
    dm_roots = import_dms(lv, LEVEL, [s['dm'] for s in todo], log) if todo else {}
    dec = {}
    for s in specs:
        if not s['dm']:
            dec[s['item']] = dict(mode='stock', reason=s['why'])
            continue
        try:
            pl = plan(lv, s['item'], s['host'], s['dm'], dm_roots[s['dm']], s['cls'], stock_of.get(s['host']))
        except Refuse as e:
            dec[s['item']] = dict(mode='stock', reason=str(e))
            log('  [measure %s] item %d %s: STOCK (%s)' % (name, s['item'], s['host'], e))
            continue
        dec[s['item']] = dict(mode=pl['mode'], reason=pl['reason'], plan=pl)
        log('  [measure %s] item %d %s: %s%s' % (name, s['item'], s['host'], pl['mode'], '' if pl['fit'] is None or pl['same'] else
            ' shift %s turn %s grip %s hand %s mag %s' % (pl['fit']['shift'], pl['fit']['deg'], pl['fit']['grip'], pl['fit']['hand_len'], pl['fit']['mag_len'])))
    return dec


def combine_decisions(per_map, force=None):
    """Pure. {map: {item: decision}} -> {item: decision} the SAME on every map: where the maps agree on the mode that mode; where they do not, 'stock' on all of them
    with the reason naming each map; `force` {item: reason} makes an item stock. The shop ini is one file for every map, so a pair may not be baked on one map only."""
    force = force or {}
    maps = sorted(per_map)
    out = {}
    for item in sorted(per_map[maps[0]]):
        ds = {m: per_map[m][item] for m in maps}
        modes = {d['mode'] for d in ds.values()}
        if item in force:
            out[item] = dict(mode='stock', reason=force[item])
        elif len(modes) == 1:
            out[item] = dict(ds[maps[0]])
        else:
            out[item] = dict(mode='stock', reason='maps disagree, stock on all: ' + '; '.join('%s %s%s' % (m, d['mode'], (' (%s)' % d['reason']) if d['reason'] else '') for m, d in ds.items()))
    return out


def bake_set(name, out, specs=None, src=None, base_ok=False, log=print, decisions=None):
    """Every pair of `specs` (default SPECS_FALLBACK) on one map: DM gun where the guard passes, 'stock-same-model' where the DM gun is the host's own mesh (nothing baked),
    else the stock gun. `decisions` {item: dict(mode, reason)} (combine_decisions: the same on every map); None = measure_set of this map. Same layout as
    pd2_guns_multi.stage_map: <out>/<name>/<slot>_Main.zip (+ the .ini files with Entries= moved) + report.json. -> report dict ('mismatch' = items that did not end in the decided mode)."""
    require_out(out)
    specs = specs or SPECS_FALLBACK
    src = src or os.path.join(MAPROOT, name)
    if decisions is None:
        decisions = measure_set(name, specs, src, base_ok, log)
    lv = C.Lv(src); lv.beside, lv.side = {}, {}
    slot = lv.name
    src_zip = os.path.join(src, slot + '_Main.zip')
    src_md5 = md5(src_zip)
    old_n = len(G.read(lv['.prm'], 'dd').chunks)
    t0 = time.time()
    hosts = {s['host'] for s in specs}
    base, restores, roots, notes, evid = classify_base(lv, name, hosts, log, base_ok, src)
    restored = M.restore_level(lv, restores, name, log=log, roots=roots) if restores else {}
    stock_of = {t: r[0] for t, r in roots.items()}
    todo = [s for s in specs if s['dm'] and decisions[s['item']]['mode'] == 'dm']
    dm_roots = import_dms(lv, LEVEL, [s['dm'] for s in todo], log) if todo else {}
    guns, pairs, mismatch = {}, [], []
    for s in specs:
        d = decisions[s['item']]
        row = dict(pair=s['pair'], item=s['item'], template=s['host'], dm_template=s['dm'])
        if d['mode'] != 'dm':
            pairs.append(dict(row, mode=d['mode'], reason=d['reason']))
            continue
        try:
            g = place(lv, s['item'], s['host'], s['dm'], dm_roots[s['dm']], s['cls'], expect_root=stock_of.get(s['host']), log=log)
        except Refuse as e:
            log('  item %d %s: STOCK at bake (%s)' % (s['item'], s['host'], e))
            pairs.append(dict(row, mode='stock', reason=str(e), refused_at_bake=True))
            mismatch.append(s['item'])
            continue
        guns['DM%d' % s['item']] = g
        pairs.append(dict(row, mode='dm', reason=None, fit=dict((k, g['fit'].get(k)) for k in ('shift', 'deg', 'grip', 'hand_len', 'mag_len', 'extent')) if not g['same_space'] else 'identity',
                          folded_bones=g['folded_bones']))
    p = G.read(lv['.prm'], 'dd')
    new_n = len(p.chunks)
    d = os.path.join(out, name)
    os.makedirs(d, exist_ok=True)
    lv.write(d, slot)
    ini = {}
    for f in sorted(os.listdir(src)):
        if f.lower().endswith('.ini'):
            txt = open(os.path.join(src, f), encoding='latin-1', newline='').read()
            new, n = re.subn(r'(?m)^(Entries\s*=\s*)%d(\s*)$' % old_n, lambda m: m.group(1) + str(new_n) + m.group(2), txt)
            if n:
                open(os.path.join(d, f), 'w', encoding='latin-1', newline='').write(new)
                ini[f] = n
    zp = os.path.join(d, slot + '_Main.zip')
    rep = dict(map=name, slot=slot, set='dm', base=base, base_notes=notes, stock_root_evidence=evid, source=src_zip, source_md5=src_md5,
               chunks_before=old_n, chunks_after=new_n, ini_entries=ini, guns=guns, restored=restored, pairs=pairs, mismatch=mismatch,
               limits=dict(GRIP_MAX=GRIP_MAX, HAND_MAX=HAND_MAX, MAG_MAX=MAG_MAX, FIT_SHIFT_MAX=FIT_SHIFT_MAX, FIT_Z_MAX=FIT_Z_MAX, FIT_DEG_MAX=FIT_DEG_MAX,
                           EXT_REAR_MAX=EXT_REAR_MAX, EXT_FRONT_MAX=EXT_FRONT_MAX, EXT_BELOW_MAX=EXT_BELOW_MAX, EXT_BOX_MAX=EXT_BOX_MAX, TURN_PENALTY=TURN_PENALTY, PIN_TOL=PIN_TOL),
               md5={os.path.basename(zp): md5(zp), **{f: md5(os.path.join(d, f)) for f in ini}},
               live_md5={f: md5(os.path.join(src, f)) for f in [slot + '_Main.zip'] + list(ini)}, seconds=round(time.time() - t0, 1))
    json.dump(rep, open(os.path.join(d, 'report.json'), 'w'), indent=1, default=str)
    log('%s: %s base %s, chunks %d -> %d, ini %s, %.0f s' % (name, slot, base, old_n, new_n, ini, rep['seconds']))
    return rep


def out_conflicts(out, maps, modes):
    """Raises Unsafe when `out` already holds a staged map (report.json) that is not in `maps` and whose pair modes differ from `modes` (this run's decisions): the shop ini is
    one file for every map, so the maps of one out must agree. Bake all maps together or use a fresh out."""
    if not os.path.isdir(out):
        return
    for n in sorted(os.listdir(out)):
        rp = os.path.join(out, n, 'report.json')
        if n in maps or not os.path.isfile(rp):
            continue
        old = {pr['item']: pr['mode'] for pr in json.load(open(rp)).get('pairs', [])}
        diff = sorted(i for i in modes if i in old and old[i] != modes[i])
        if diff:
            raise Unsafe('out %s holds map %s whose report modes differ from this run on items %s: bake all maps together or use a fresh out' % (out, n, diff))


def bake_maps(maps, out, specs=None, srcs=None, base_ok=False, log=print, rounds=3):
    """bake_set on several maps with ONE mode per pair on every map: measure every map first (read only), combine_decisions, bake, and when a map still ended in another mode
    than decided (a refusal at bake time) force that pair to stock on ALL maps and bake again; after `rounds` the residual mismatch raises RuntimeError. -> ({map: report}, {item: mode})."""
    require_out(out)
    if rounds < 1:
        raise ValueError('bake_maps: rounds must be at least 1')
    specs = specs or SPECS_FALLBACK
    srcs = srcs or {}
    per_map = {m: measure_set(m, specs, srcs.get(m), base_ok, log) for m in maps}
    force = {}
    for _r in range(rounds):
        merged = combine_decisions(per_map, force)
        out_conflicts(out, maps, {i: d['mode'] for i, d in merged.items()})
        reps = {m: bake_set(m, out, specs, srcs.get(m), base_ok, log, decisions=merged) for m in maps}
        bad = {pr['item']: pr['reason'] for r in reps.values() for pr in r['pairs'] if pr.get('refused_at_bake')}
        if not bad:
            break
        for it, why in bad.items():
            force[it] = 'refused at bake time on one map, stock on all: ' + str(why)
        log('  residual mismatch on items %s: forcing stock on every map and baking again' % sorted(bad))
    else:
        raise RuntimeError('pairs %s still differ between maps after %d rounds' % (sorted(bad), rounds))
    modes = {pr['item']: pr['mode'] for pr in reps[maps[0]]['pairs']}
    for m in maps:
        mm = {pr['item']: pr['mode'] for pr in reps[m]['pairs']}
        if mm != modes or reps[m]['mismatch']:
            raise RuntimeError('map %s ended with other modes than %s: %s vs %s' % (m, maps[0], mm, modes))
    return reps, modes


def bake(name, out, item, host, dm, level, src=None, base_ok=False, log=print):
    """One pair (the spike's entry point). Writes <out>/<name>/ and ALSO <out>/KLShopPage.ini (this pair on its DM name / text, every other pair stock)."""
    require_out(out)
    cls = DM_CLASS.get(dm)
    spec = dict(pair=0, item=item, cls=cls, host=host, dm=dm, level=level, name=dm, why=None)
    rep = bake_set(name, out, [spec], src, base_ok, log)
    modes = {pr['item']: pr['mode'] for pr in rep['pairs']}
    fp = write_shop_ini(out, [spec], modes)
    log('wrote ' + fp)
    return rep


# ------------------------------------------------------------------ restore: the baked templates back on their previous root
def restore_plan(rep):
    """Pure. report.json -> [(template, root to go back to, baked root)] for every baked gun."""
    plan_ = []
    for key, g in sorted(rep.get('guns', {}).items()):
        if 'skipped' in g:
            continue
        if g.get('previous_root') is None:
            raise ValueError('%s: the report has no previous_root' % key)
        plan_.append((g['template'], g['previous_root'], g['root']))
    return plan_


def restore_guard(staged, dest, rep):
    """Raises Unsafe: dest is the staged folder, or inside a game folder / KL_PortBackup (out_problem), or a staged file does not match the md5 pinned in report.json."""
    if _norm(dest) == _norm(staged):
        raise Unsafe('restore: dest is the staged folder itself')
    if _under(_norm(dest), _norm(staged)):
        raise Unsafe('restore: dest is inside the staged folder')
    require_out(dest)
    pins = rep.get('md5') or {}
    if not pins:
        raise Unsafe('restore: the report pins no md5')
    for f, want in pins.items():
        fp = os.path.join(staged, f)
        if not os.path.isfile(fp) or md5(fp) != want:
            raise Unsafe('restore: staged %s does not match the md5 pinned in report.json (%s)' % (f, want))


def restore(staged, dest, log=print):
    """staged = <out>/<map> (zip + report.json): writes <dest>/<slot>_Main.zip (+ the .ini files) with every baked template on its previous root. No chunk is removed
    (Entries= stays), so the .ini files are copied as they are. Refused (Unsafe) before anything is read or written when dest == staged, dest is in a game folder /
    KL_PortBackup, or the staged files differ from the report's pinned md5."""
    rep = json.load(open(os.path.join(staged, 'report.json')))
    restore_guard(staged, dest, rep)
    lv = C.Lv(staged); lv.beside, lv.side = {}, {}
    sc, raw = lv.scene(); raw = bytearray(raw)
    models = C.gms_models(raw)
    for t, prev, now in restore_plan(rep):
        k = K.gun_node(sc, t)
        if C.person(sc, k)[0] != now:
            raise ValueError('%s: the template is not on the baked root %d' % (t, now))
        K._retarget(sc, raw, models, k, prev)
        log('  restore %s: root %d -> %d' % (t, now, prev))
    lv['.gms'], lv['.prp'] = kl_gms.pack(bytes(raw)), sc.p.serialize()
    os.makedirs(dest, exist_ok=True)
    lv.write(dest, rep['slot'])
    for f in rep['ini_entries']:
        shutil.copyfile(os.path.join(staged, f), os.path.join(dest, f))
    return rep


# ------------------------------------------------------------------ KLShopPage.ini
def _ini_name(s, mode):
    import kl_shop_sets as S
    return s['name'] if mode in ('dm', 'same') else S.ITEMS[s['item']][0]


def shop_ini_text(live_text, specs, modes):
    """Pure. The live KLShopPage.ini structure (comment lines, [Pairs] row|item|picture row|NAME, [Desc]) with the names / descriptions of this set, plus a [Set] block.
    modes = {item: 'dm' | 'stock-same-model' | 'stock'}; an item missing from `modes` / `specs` is stock (a one-pair bake). 'dm' and 'stock-same-model' show the DM name (the
    same-model gun IS the Dead Men gun); stock pairs get the stock name and text of kl_shop_sets.ITEMS."""
    import kl_shop_sets as S
    by_item = {s['item']: s for s in SPECS_FALLBACK}
    by_item.update({s['item']: s for s in specs})
    mode_of = lambda item: {'stock-same-model': 'same'}.get(modes.get(item, 'stock'), modes.get(item, 'stock'))
    lines = live_text.replace('\r\n', '\n').split('\n')
    out, sec, rows = [], '', {}
    for ln in lines:
        m = re.match(r'\[(\w+)\]', ln)
        if m:
            sec = m.group(1)
        pm = re.match(r'P(\d+)=(\d+)\|(\d+)\|(\d+)\|(.*)$', ln) if sec == 'Pairs' else None
        dmx = re.match(r'D(\d+)=(.*)$', ln) if sec == 'Desc' else None
        if pm:
            n, row, item, pic = int(pm.group(1)), pm.group(2), int(pm.group(3)), pm.group(4)
            s = by_item[item]
            rows[n] = (item, row)
            out.append('P%d=%s|%d|%s|%s' % (n, row, item, pic, _ini_name(s, mode_of(item))))
        elif dmx:
            n = int(dmx.group(1)); item = rows[n][0]; s = by_item[item]
            sold = re.search(r'Page II: sold in the (.+?) row, same price, same rank\.', dmx.group(2))
            tail = ' Page II: sold in the %s row, same price, same rank.' % (sold.group(1) if sold else '?')
            kind, text = S.ITEMS[item][1].split('.', 1)[0], S.ITEMS[item][1]
            md = mode_of(item)
            if md == 'dm':
                body = '%s. Dead Men gun: the %s, on a Dog Days %s.%s' % (kind, s['name'], S.ITEMS[item][0], tail)
            elif md == 'same':
                body = '%s. Dead Men gun: the %s (Dog Days already ships this very model).%s' % (kind, s['name'], tail)
            else:
                body = text + tail
            out.append('D%d=Police reg.: 20%d-II%d\\n%s' % (n, item, item, body))
        else:
            out.append(ln)
    while out and out[-1] == '':
        out.pop()
    def _look(it):
        md = mode_of(it)
        return '%d:%s' % (it, md + ':' + by_item[it]['dm'] if md in ('dm', 'same') else 'stock')
    looks = ','.join(_look(it) for it in sorted(by_item, key=lambda i: by_item[i]['pair']) if it in modes)
    out += ['[Set]', '; written by tools/kl_fallback_guns.py bake-set. The hook ignores [Set] for now (nothing reads it): a later set check can.',
            'Name=dm', 'Looks=' + looks, '']
    return '\r\n'.join(out)


def write_shop_ini(out, specs, modes, live=LIVE_INI):
    require_out(out)
    txt = open(live, encoding='latin-1', newline='').read()
    new = shop_ini_text(txt, specs, modes)
    fp = os.path.join(out, 'KLShopPage.ini')
    os.makedirs(out, exist_ok=True)
    open(fp, 'w', encoding='latin-1', newline='').write(new)
    return fp


# ------------------------------------------------------------------ verify
def report_problems(rep):
    """Pure. What a report.json must say: base classified, source zip md5 pinned, a previous root per baked gun, a reason per stock / same-model pair, every dm pair baked,
    every baked gun's fit inside the strict guards (grip, hand, magazine, folded-bone count recorded)."""
    bad = []
    if rep.get('base') not in ('stock', 'pd2-restored', 'unchecked'):
        bad.append('base %r is not classified' % rep.get('base'))
    if not re.fullmatch(r'[0-9a-f]{32}', str(rep.get('source_md5'))):
        bad.append('no source zip md5 pinned')
    baked = {g['template'] for g in rep.get('guns', {}).values()}
    for key, g in rep.get('guns', {}).items():
        if g.get('previous_root') is None:
            bad.append('%s: no previous_root' % key)
        if 'folded_bones' in g or 'fit' in g:
            if g.get('folded_bones') is None:
                bad.append('%s: no folded-bone count' % key)
            f = g.get('fit') or {}
            if not g.get('same_space') and f:
                lim = rep.get('limits') or dict(GRIP_MAX=GRIP_MAX, HAND_MAX=HAND_MAX, MAG_MAX=MAG_MAX)
                if f.get('grip') is None or f['grip'] > lim['GRIP_MAX']:
                    bad.append('%s: grip %s over %s' % (key, f.get('grip'), lim['GRIP_MAX']))
                if f.get('hand_len') is not None and f['hand_len'] > lim['HAND_MAX']:
                    bad.append('%s: support hand %s over %s' % (key, f['hand_len'], lim['HAND_MAX']))
                if f.get('mag_len') is not None and f['mag_len'] > lim['MAG_MAX']:
                    bad.append('%s: magazine %s over %s' % (key, f['mag_len'], lim['MAG_MAX']))
                if f.get('extent') is not None and all(k in lim for k in ('EXT_REAR_MAX', 'EXT_FRONT_MAX', 'EXT_BELOW_MAX', 'EXT_BOX_MAX')):
                    why = extent_problem(f['extent'], lim)
                    if why:
                        bad.append('%s: %s' % (key, why))
                if pinned_axis(f):
                    bad.append('%s: fit pinned to bound %s' % (key, pinned_axis(f)))
    for pr in rep.get('pairs', []):
        if pr['mode'] == 'dm' and pr['template'] not in baked:
            bad.append('pair %d: dm but no baked gun for %s' % (pr['pair'], pr['template']))
        if pr['mode'] in STOCK_MODES:
            if not pr.get('reason'):
                bad.append('pair %d: %s without a reason' % (pr['pair'], pr['mode']))
            if pr['template'] in baked:
                bad.append('pair %d: %s but %s is baked' % (pr['pair'], pr['mode'], pr['template']))
        if pr['mode'] not in ('dm',) + STOCK_MODES:
            bad.append('pair %d: mode %r' % (pr['pair'], pr['mode']))
    if rep.get('mismatch'):
        bad.append('items %s ended in another mode than decided' % rep['mismatch'])
    return bad


def check(out, name, log=print):
    """What must hold beside pd2_guns_multi.verify: report_problems, every baked template names its new root and every stock pair its stock root, no hide bit / variant
    surprises, Entries= equals the chunk count."""
    d = os.path.join(out, name)
    rep = json.load(open(os.path.join(d, 'report.json')))
    lv = C.Lv(d); lv.beside, lv.side = {}, {}
    p = G.read(lv['.prm'], 'dd'); sc, _raw = lv.scene()
    bad = report_problems(rep)
    n = len(p.chunks)
    if n != rep['chunks_after']:
        bad.append('chunks %d != report %d' % (n, rep['chunks_after']))
    if rep.get('base') == 'stock' and pd2_markers(lv):
        bad.append('base stock but the zip holds W_PD2 materials')
    for f in rep['ini_entries']:
        m = re.search(r'(?m)^Entries\s*=\s*(\d+)', open(os.path.join(d, f), encoding='latin-1').read())
        if not m or int(m.group(1)) != n:
            bad.append('%s Entries= %s != %d' % (f, m and m.group(1), n))
    for key, g in rep['guns'].items():
        r = C.person(sc, K.gun_node(sc, g['template']))[0]
        if r != g['root']:
            bad.append('%s: template names root %d, report %d' % (key, r, g['root']))
        objs = C.objects(p, r)
        nb = p.u32(C.skeleton(p, r), 0)
        for o in objs:
            c = p.chunks[o]
            if c[0x0f] != 0 or p.u32(o, MG.HIDE_OFF) & MG.HIDE_BIT or (c[0x0e] != HIDDEN_DETAIL and p.u32(o, 0x3c) >= nb):
                bad.append('%s: object %d variant %d bone %d of %d' % (key, o, c[0x0f], p.u32(o, 0x3c), nb))
        log('  %s: root %d (was %d), %d objects %s, item %d, %s' % (key, r, g.get('previous_root', -1), len(objs), [(p.chunks[o][0x0e], p.u32(o, 0x3c)) for o in objs], g['item'],
                                                              'identity' if g.get('same_space') else 'shift %s turn %s' % (g['shift'], g.get('deg'))))
    for pr in rep.get('pairs', []):
        if pr['mode'] in STOCK_MODES and pr['template'] not in {g['template'] for g in rep['guns'].values()}:
            st = [g['stock_root'] for g in (rep.get('restored') or {}).values() if g['template'] == pr['template']]
            if st and C.person(sc, K.gun_node(sc, pr['template']))[0] != st[0]:
                bad.append('pair %d: stock pair %s is not on its stock root %d' % (pr['pair'], pr['template'], st[0]))
    return bad


def ini_problems(out, maps):
    """<out>/KLShopPage.ini [Pairs] names against the reports: 'dm' and 'stock-same-model' items (the same-model gun IS the DM gun, shop_ini_text shows its DM name) carry exactly
    the SPECS_FALLBACK DM name, every other item the stock name of kl_shop_sets.ITEMS; the maps must agree on every pair's mode."""
    import kl_shop_sets as S
    fp = os.path.join(out, 'KLShopPage.ini')
    if not os.path.isfile(fp):
        return ['%s is missing' % fp]
    modes, bad = {}, []
    for m in maps:
        mm = {pr['item']: pr['mode'] for pr in json.load(open(os.path.join(out, m, 'report.json')))['pairs']}
        for i, md in mm.items():
            if modes.setdefault(i, md) != md:
                bad.append('item %d: maps disagree (%s vs %s)' % (i, modes[i], md))
    by_item = {s['item']: s for s in SPECS_FALLBACK}
    txt = open(fp, encoding='latin-1').read().replace('\r\n', '\n')
    sec, seen = '', set()
    for ln in txt.split('\n'):
        mm = re.match(r'\[(\w+)\]', ln)
        if mm:
            sec = mm.group(1)
        pm = re.match(r'P(\d+)=(\d+)\|(\d+)\|(\d+)\|(.*)$', ln) if sec == 'Pairs' else None
        if not pm:
            continue
        item, name = int(pm.group(3)), pm.group(5)
        seen.add(item)
        want = by_item[item]['name'] if modes.get(item, 'stock') in ('dm', 'stock-same-model') else S.ITEMS[item][0]
        if name != want:
            bad.append('KLShopPage.ini item %d is named %r, mode %s wants %r' % (item, name, modes.get(item, 'stock'), want))
    if not seen:
        bad.append('KLShopPage.ini has no [Pairs] rows')
    return bad


def verify(out, log=print, only=None):
    maps = sorted(n for n in os.listdir(out) if os.path.isfile(os.path.join(out, n, 'report.json')) and (only is None or n in only))
    if not maps:
        raise SystemExit('no staged map (report.json) under %s' % out)
    bad = []
    for n in maps:
        bad += ['%s: %s' % (n, b) for b in check(out, n, log)]
    ok = M.verify(out, only=maps, log=log)
    bad += ini_problems(out, maps)
    for m in maps:
        rep = json.load(open(os.path.join(out, m, 'report.json')))
        src = rep.get('source')
        if src and os.path.isfile(src):
            if md5(src) != rep.get('source_md5'):
                log('  WARNING: %s: the LIVE map zip %s changed since the bake (md5 now %s, report pins %s): this stage was built on an older live zip, re-bake before using it' % (m, src, md5(src), rep.get('source_md5')))
        else:
            log('  note: %s: live zip %s not found, source md5 not re-checked' % (m, src))
    for b in bad:
        log('  PROBLEM: ' + b)
    log('RESULT: %s (report-consistent + structural checks only; geometry quality is fit-time, not re-measured here) (maps %s, own checks %d problems, pd2_guns_multi.verify %s)' % (
        'PASS' if ok and not bad else 'FAIL', ','.join(maps), len(bad), ok))
    return ok and not bad


def main(argv):
    a = [x for x in argv if not x.startswith('--')]
    opt = dict(x[2:].split('=', 1) for x in argv if x.startswith('--') and '=' in x)
    base_ok = '--base-ok' in argv
    if a[:1] == ['bake-set'] and len(a) >= 2:
        out = opt.get('out', OUT_DEFAULT)
        require_out(out)
        maps = a[1:]
        reps, modes = bake_maps(maps, out, srcs={maps[0]: opt['src']} if opt.get('src') and len(maps) == 1 else None, base_ok=base_ok)
        for pr in reps[maps[0]]['pairs']:
            print('  pair %2d item %2d %-16s %s' % (pr['pair'], pr['item'], pr['mode'], pr.get('dm_template') if pr['mode'] == 'dm' else pr['reason']))
        fp = write_shop_ini(out, SPECS_FALLBACK, modes)
        print('wrote ' + fp)
        ok = verify(out)            # EVERY staged map under out, not only this run's
        cnt = lambda m: sum(v == m for v in modes.values())
        print('SET RESULT %s (set=dm, %d dm / %d stock-same-model / %d stock)' % ('PASS' if ok else 'FAIL', cnt('dm'), cnt('stock-same-model'), cnt('stock')))
        sys.exit(0 if ok else 1)
    elif a[:1] == ['bake'] and len(a) == 3:
        bake(a[1], a[2], int(opt.get('item', DEFAULT['item'])), opt.get('host', DEFAULT['host']), opt.get('dm', DEFAULT['dm']), opt.get('level', DEFAULT['level']),
             opt.get('src'), base_ok)
    elif a[:1] == ['verify'] and len(a) == 2:
        sys.exit(0 if verify(a[1]) else 1)
    elif a[:1] == ['restore'] and len(a) == 3:
        restore(a[1], a[2])
    else:
        print(__doc__); sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
