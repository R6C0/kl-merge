#!/usr/bin/env python3
"""
HASTA (M11_B) helicopter escape: the chopper of Last Call (kl_fa_club.py heli, re/heli_call.md) instead of the van.
OFFLINE. Everything here sits behind kl_fa_hasta_layer.HELI ('--heli-escape'); with the flag off nothing of it runs and the
default build is byte-identical (re/hasta_fa.md, handover 2026-10-18).

The club's two-step chain, with Hasta's own keep / drop lists:
  STEP 1  donor(): F07 (Hasta's KEEP without the van) + the tops of M06_FA_A's chopper (kl_fa_club.HELI_WANT) -> level 'R09'
          (kl_maps.PSEUDO). Same as kl_fa_club.heli_donor, but the layer's KEEP / DROP (the blast, the lock-wing counter ...).
  STEP 2  the layer builds R09 + M11_B with HOST = 'R09' and kl_hvk_donor.patched() (the chopper has no static placement).
          prepare_host calls place(): the club's heli_place with the pad and approach of this file (the club's module globals are
          set for the length of the build by club_frame()), wire() names the chopper group in the exit trigger, no van_wire.
Not run in the game. Everything marked GUESS below is one.
"""
import contextlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# ------------------------------------------------------------------ where it lands
# MEASURED on the finished level (kl_map_escape.Ground over build/hasta_owner_1018/M11B_cornerfloor): the square is open floor from z 21,550
# to 27,800 over x 22,000..31,000 (nothing above 400 but the props at z 25,050..25,800); the north facade is 1,000..2,000 high from z
# 21,300 northwards, so the van's stop (25,600, 0, 21,800) is 500 from it - too near for a rotor of 8 .. 10 m. The bomb craters of the
# square lie at x 22,700..23,500 / z 22,600..23,500 and x 25,700..26,300 / z 23,200..23,800 (y down to -160).
PAD = (27500.0, 0.0, 22800.0)           # GUESS: centre of the landing; 1,200 off the facade, 1,400 east of the second crater, floor y 0 (measured at the point)
APPROACH = (-0.961262, -0.275637)       # GUESS: 196 deg turn of the old (+x) heading: the chopper flies in from the east (heading -x, a little -z); chosen by a clearance scan (opt.py) as the only turn with the rotor disc >300 above every roof on both splines
BOT_PARK = (27500.0, 0.0, 23250.0)      # GUESS: where the AI heisters wait: 450 south of the landing, the side the crew arrives from (the stair foot is at z 27,758)
EXIT_HALF = (700.0, 250.0, 500.0)       # the exit box over the whole pad, as the club's (HELI_EXIT). GUESS
GROUP = 'EscapeSetup!EscapeChopper\\Escape_Chopper'
CH = 'EscapeSetup!EscapeChopper\\'


def exit_box():
    return (PAD[0], PAD[1] + 200.0, PAD[2]), EXIT_HALF


def place_table():
    """The layer's place_now() entries that hang on the pad (name -> (pos, face, half, why)). SOUTH is the layer's."""
    import kl_fa_club as C
    c, h = exit_box()
    box = (c, None, h, 'HELI: GUESS: the pad (the chopper lands in its middle)')
    t = {'Gameplay!EscapeSetup!otrExitLevel': box,
         'FASpecials!POI!POI_TheEscapeArea': ((PAD[0], PAD[1] + C.ESC_POI_UP, PAD[2]), None, None, 'HELI: over the pad')}
    for k in ('FASpecials!POI!Trigger_POI_TheEscapeArea', 'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn',
              'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly'):
        t[k] = box
    return t


@contextlib.contextmanager
def club_frame(hvk_origin=False):
    """The club's heli_frame / heli_place / heli_hvk read module globals: set them to this map's pad for the length of the build."""
    import kl_fa_club as C
    names = ('HELI_PAD', 'HELI_APPROACH', 'HELI_GROUND_OLD', 'HELI_HVK_ORIGIN')
    saved = {n: getattr(C, n) for n in names}
    C.HELI_PAD, C.HELI_APPROACH, C.HELI_GROUND_OLD, C.HELI_HVK_ORIGIN = PAD, APPROACH, 0.0, bool(hvk_origin)
    try:
        yield
    finally:
        for n, v in saved.items():
            setattr(C, n, v)


def place(S, log=print):
    """prepare_host, heli mode: lay the chopper's nodes on the pad (the club's heli_place, set to this pad by club_frame)."""
    import kl_fa_club as C
    if C.HELI_PAD != PAD:
        raise ValueError('kl_fa_hasta_heli.place outside club_frame()')
    return C.heli_place(S, log)


@contextlib.contextmanager
def hvk_layer(log=print):
    import kl_fa_club as C
    with C.heli_hvk_layer(log):
        yield


# ------------------------------------------------------------------ step 1: the donor
def donor(out, layer, log=print):
    """STEP 1: F07 (the layer's KEEP / DROP, HELI on: no van) + the chopper tops of M06_FA_A -> <out>/chain/F07+M06_FA_A as level R09 (kept),
    kl_maps.PSEUDO['R09'] set. -> kl_maps.one's result. `layer` = the kl_fa_hasta_layer module (HELI already True)."""
    import kl_graft, kl_maps, kl_hvk_donor
    import kl_fa_club as C
    want = {n.lower() for n in C.HELI_WANT}
    real_sel = kl_graft.Select
    keep, drop = tuple(layer.KEEP), tuple(layer.DROP)
    class Donor(real_sel):
        def __init__(self, geometry=False, m_add=(), m_drop=(), s_keep=(), s_drop=()):
            super().__init__(geometry, m_add, m_drop, tuple(s_keep) + tuple(x for x in keep if x not in s_keep), tuple(s_drop) + drop)
        def m(self, name):              # M06: the wanted tops only (exact names)
            return name.lower() in want
    kl_graft.Select = Donor
    mid = os.path.join(out, 'chain')
    try:
        with kl_hvk_donor.patched():
            r = kl_maps.one(mid, 'F07', C.HELI_DONOR, keep=True, campaign=False, slot='R09')
    finally:
        kl_graft.Select = real_sel
    if r.get('ok'):
        left = [x for x in r.get('problems', []) if not any(k in x for k in C.HELI_DONOR_EXPECTED)]
        r = dict(r, problems_expected=len(r.get('problems', [])) - len(left), problems=left)
        kl_maps.PSEUDO['R09'] = os.path.join(mid, 'F07+%s' % C.HELI_DONOR)
        log('heli donor: R09 = F07+%s, %s entities, %s MB, problems %s' % (C.HELI_DONOR, r.get('entities'), r.get('archive_mb'), r.get('problems')))
    else:
        log('heli donor FAILED: %s %s' % (r.get('error'), r.get('where')))
    return r


# ------------------------------------------------------------------ the check (a built, finished folder)
def check(folder, sc, ents, pos, hvk, fail, log=print):
    """The chopper form read back from the written level: ONE chopper group with ONE OnlineEscVehicleController and ONE monitor, no van, no
    FakeTarget, the exit trigger naming the group, the boarding box / PIP point / on-map marker / exit box on the pad, the chopper's key-framed
    placement present, and its approach and departure splines clear of the collision (kl_map_escape.Ground, 300 above the floor at least)."""
    import kl_fa
    import kl_fa_author as A
    import kl_hvk
    import kl_fa_club as C
    R = 'ROOT\\'
    vans, fakes = kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle'), kl_fa.controllers(sc, 'FakeTarget')
    ex = [k for k, _i, _v in kl_fa.controllers(sc, kl_fa.EXIT)]
    mons = kl_fa.controllers(sc, kl_fa.MONITOR)
    hv = [k for k, _i, _v in kl_fa.controllers(sc, 'OnlineEscVehicleController')]
    if vans or len(mons) != 1 or len(ex) != 1 or len(hv) != 1 or fakes:
        fail('HELI: %d OnlineEscAnimatedVehicle, %d OnlineEscVehicleMonitor, %d exit triggers, %d OnlineEscVehicleController, %d FakeTarget (0, 1, 1, 1, 0 wanted)' % (
            len(vans), len(mons), len(ex), len(hv), len(fakes)))
        return
    named = [v for k, i, v in kl_fa.controllers(sc, kl_fa.EXIT) if k == ex[0]][0]
    if [s for s in named[2:6] if s] != [R + GROUP]:
        fail('HELI: the exit trigger names %s, not the chopper group' % [s for s in named[2:6] if s])
    log('  heli: 1 chopper (%s), 1 OnlineEscVehicleMonitor, 1 exit trigger naming it; no van' % sc.names[hv[0]])
    on_pad = lambda p_: abs(p_[0] - PAD[0]) <= EXIT_HALF[0] + 400.0 and abs(p_[2] - PAD[2]) <= EXIT_HALF[2] + 400.0 and -100.0 < p_[1] - PAD[1] < 1200.0
    for n_ in ('Triggers!BoardingTrigger_Heli', 'Triggers!BoardingGameplayTrigger', 'PIP_Points!Boarding', CH + 'EscapeChopper_OnMap', 'Gameplay!EscapeSetup!otrExitLevel'):
        e_ = ents[A.node_of(sc, n_) - 1]
        if not on_pad(pos[e_]):
            fail('HELI: %s stands at (%d, %d, %d), not on the pad (%s)' % (n_, *pos[e_], PAD))
    gh = A.node_of(sc, GROUP)
    mine_ = {ents[j - 1].ref for j in range(gh, sc.end[gh])}
    n_pl = sum(1 for s_ in hvk.shapes if s_.type != kl_hvk.STATIC for i in s_.inst if kl_hvk.ref(i) in mine_)
    log('  heli: the boarding box, the PIP point, the on-map marker and the exit box are on the pad; the chopper has %d key-framed placement(s)' % n_pl)
    if not n_pl:
        fail('HELI: the chopper has no key-framed .HVK placement')
    approach_clearance(folder, sc, fail, log)


def check_hide(sc, ents, fail, log=print):
    """--heli-hide read back: the chopper group hidden both ways (.prp ZGEOM[3] = 1, .gms flag 0x400), the monitor's list 4 naming an ActivateGeom
    that answers AITrigger and lists the group, no other ActivateGeom / timer showing the group."""
    import kl_fa
    import kl_fa_author as A
    import kl_fa_club as C
    import kl_prpjoin as J
    R = 'ROOT\\'
    gh = A.node_of(sc, GROUP)
    lab = J.labels('dd', sc.cls(gh))
    z3 = kl_fa.node_values(sc, gh)[lab.index('ZGEOM[3]')]
    flag = bool(ents[gh - 1].flags & C.HIDDEN) if hasattr(ents[gh - 1], 'flags') else None
    if z3 != 1 or flag is False:
        fail('HELI_HIDE: the chopper group is not hidden at start (ZGEOM[3] %r, .gms 0x400 %r)' % (z3, flag))
    mon = [v for _k, _i, v in kl_fa.controllers(sc, kl_fa.MONITOR)][0]
    targets = mon[4]
    shows = []
    for k, _i, v in kl_fa.controllers(sc, 'ActivateGeom'):
        if R + GROUP in (v[1] or []):
            shows.append(sc.path[k])
            if v[0] != 'AITrigger':
                fail('HELI_HIDE: %s answers %r, not AITrigger' % (sc.path[k], v[0]))
    if len(shows) != 1 or [t for t in targets] != shows:
        fail('HELI_HIDE: monitor list 4 %r, ActivateGeom(s) showing the chopper %r (one, equal, wanted)' % (targets, shows))
    log('  heli: HELI_HIDE: chopper hidden at start; monitor list 4 -> %s' % shows)


def spline_points(sc, name):
    """World points of a chopper spline node (the club's heli_frame reading) -> [(x, y, z)]."""
    import struct
    import kl_fa
    import kl_fa_author as A
    import kl_prpjoin as J
    k = A.node_of(sc, CH + name + '\\Spline')
    lab = J.labels('dd', sc.cls(k))
    v = kl_fa.node_values(sc, k)
    m, p = [float(x) for x in v[lab.index('ZGEOM[1]')]], [float(x) for x in v[lab.index('ZGEOM[2]')]]
    blob = next(x for x in v if isinstance(x, (bytes, bytearray)) and bytes(x[:4]) == b'1TPW')
    n = struct.unpack_from('<I', blob, 4)[0]
    pts = [struct.unpack_from('<3f', blob, 12 + 24 * j) for j in range(n)]
    return [tuple(p[a] + q[0] * m[6 + a] + q[1] * m[3 + a] + q[2] * m[a] for a in range(3)) for q in pts]


def approach_clearance(folder, sc, fail, log=print, rotor=1000.0, lift=300.0):
    """The Incomming and Escaping splines read back from the written level against the map's collision: every point (and, on each segment, the
    points 200 apart) must be at least `lift` above the highest floor within `rotor` of it. A point under a roof is a fault."""
    import kl_map_escape as E
    L = E.Level(folder)
    G = E.Ground(L)
    worst = None
    for name in ('Incomming', 'Escaping'):
        pts = spline_points(sc, name)
        dense = []
        for a, b in zip(pts, pts[1:]):
            n = max(1, int(math.dist(a, b) // 200))
            dense += [tuple(a[i] + (b[i] - a[i]) * j / n for i in range(3)) for j in range(n)]
        dense.append(pts[-1])
        for p in dense:
            top = -1e9
            for dx in (-rotor, -rotor / 2, 0.0, rotor / 2, rotor):
                for dz in (-rotor, -rotor / 2, 0.0, rotor / 2, rotor):
                    if math.hypot(dx, dz) > rotor + 1:
                        continue
                    for h in G.hits(p[0] + dx, p[2] + dz):
                        top = max(top, h[0])
            gap = p[1] - top
            if worst is None or gap < worst[0]:
                worst = (gap, name, p)
            if gap < lift:
                fail('HELI: the %s spline passes (%d, %d, %d), %d above the collision within %d (%d wanted)' % (name, *p, gap, rotor, lift))
                break
    if worst:
        log('  heli: the approach / departure splines clear the collision by %d at worst (%s at (%d, %d, %d)); rotor radius assumed %d (GUESS)' % (worst[0], worst[1], *worst[2], rotor))
