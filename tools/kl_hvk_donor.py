#!/usr/bin/env python3
"""
kl_hvk.join for a DONOR part: a map level of which only a few moving things are taken (Last Call's helicopter: Dead Men
M06_FA_A 'EscapeSetup!EscapeChopper', one VEHICLE placement and no static collision at all), joined under a systems level.
kl_hvk.py itself is NOT edited (owner's rule for this round); this module is a replacement with the same signature that
kl_hvk.join is pointed at for the length of a build (`patched()`).

WHAT kl_hvk.join DOES WITH SUCH A PART, MEASURED (2026-10-17, on M06_FA_A's file: 261 shapes, 1246 static placements, 3 list
codes, the chopper = 1 placement of type 3):
  * `parts` holds (hvk, refs, first_static(...)) and first_static is None when no kept placement is static. As soon as
    the systems level adds a part behind it, `pad = -h.static_count() % CHUNK` is true and `fill[0].clone(...)` is a
    TypeError (None). The pad is computed from the part's WHOLE file (h), not from what remap kept.
  * `out.lists += h.lists` takes ALL the part's list codes (one per 510 static placements of the WHOLE file). With the
    part's static placements dropped (remap without a filler drops them) those codes address placements that are not
    there: a list code of the wrong file would be read by the game's static MOPP walk.
THE FIX, here: (a) a part with no kept static placement is padded with nothing and brings none of its list codes
(zero static placements, zero lists: a multiple of CHUNK, and the next part's list codes then begin at position 0 of
its own run, which is what they address); (b) a part WITH a kept static placement is exactly kl_hvk.join's (the filler
keeps every position, the pad rounds the part's whole static count up, its list codes come along) - so a join of
ordinary maps gives the same bytes as kl_hvk.join (selftest(): byte equal on the stock pair M05_A + F07's systems).
ASSUMPTION (as in kl_hvk.join): a list code addresses the placements of its own 510 by position only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_hvk
from kl_hvk import CHUNK, Hvk, first_static, remap

_REAL = kl_hvk.join


def join(maps, systems, box=None):
    """kl_hvk.join's arguments and result; see the module docstring for the one difference."""
    out = Hvk.__new__(Hvk)
    out.shapes, out.lists, out.tail = [], [], maps[0][0].tail
    parts = [(h, refs, first_static(h.shapes, refs)) for h, refs in maps]
    extra = []
    if systems:
        fill = first_static(systems[0].shapes, systems[1])
        if fill:
            parts.append((systems[0], systems[1], fill))
        else:
            extra = remap(*systems)                 # no filler: its static placements all go
    for n, (h, refs, fill) in enumerate(parts):
        out.shapes += remap(h, refs, fill)
        if fill is None:                            # DONOR: nothing static is kept, so nothing is padded and no list code comes along
            continue
        pad = -h.static_count() % CHUNK if n < len(parts) - 1 else 0
        if pad:
            out.shapes.append(fill[0].clone([fill[1]] * pad, [fill[2]] * pad))
        out.lists += h.lists
    out.shapes += extra
    lo = [min(h.box[k] for h, _ in maps) for k in range(3)]
    hi = [max(h.box[k] for h, _ in maps) for k in range(3, 6)]
    out.box = tuple(box or lo + hi)
    return out


class patched:
    """`with kl_hvk_donor.patched():` points kl_hvk.join at join() above (kl_graft calls it as kl_hvk.join, at the moment of use)."""
    def __enter__(self):
        kl_hvk.join = join
        return self

    def __exit__(self, *exc):
        kl_hvk.join = _REAL
        return False


def counts(h):
    """(shapes, static placements, list codes, [placements by shape type]) of an Hvk, for the logs."""
    by = {}
    for s in h.shapes:
        by[s.type] = by.get(s.type, 0) + len(s.inst)
    return len(h.shapes), h.static_count(), len(h.lists), by


def selftest(log=print):
    """-> problems (list of text). 1: on a map that keeps statics the module equals kl_hvk.join byte for byte. 2: a donor with no static
    placement under a systems level with a filler: joins, round-trips, has no list code of the donor's, the systems' own lists."""
    import zipfile
    import kl_prpjoin as J, kl_scene, kl_gms
    bad = []

    def load(name, game):
        z = zipfile.ZipFile(J.level_zip(name, game))
        ext = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        sc = kl_scene.Scene(kl_gms.unpack(z.read(ext['.gms'])), z.read(ext['.buf']))
        return Hvk(z.read(ext['.HVK'])), list(sc.entities()), J.Scene.load(name, game)

    f07, f07e, f07p = load('F07', 'dd')
    m05, m05e, _m05p = load('M05_A', 'dm')
    # systems refs: the entities of F07's systems subtrees, as kl_graft keeps them (every placement of F07 here: all that has a REF)
    s_refs = {e.ref: e.ref for e in f07e}
    m_refs = {e.ref: e.ref + 100000 for e in m05e}
    s_refs = {r: r for r in s_refs if r + 0 not in m_refs}
    a = _REAL([(m05, m_refs)], (f07, s_refs))
    b = join([(m05, m_refs)], (f07, s_refs))
    if a.serialize() != b.serialize():
        bad.append('ordinary join differs from kl_hvk.join')
    log('selftest 1: ordinary join %s (%d bytes)' % ('equal' if not bad else 'DIFFERENT', len(b.serialize())))
    m06, m06e, m06p = load('M06_FA_A', 'dm')
    chop = {m06e[k - 1].ref: m06e[k - 1].ref + 200000 for k in range(1, len(m06p.nodes)) if m06p.names[m06p.top[k]] == 'EscapeSetup!EscapeChopper'}
    try:
        _REAL([(m06, chop)], (f07, s_refs))
        bad.append('kl_hvk.join no longer fails on a donor without a static placement: this module may be unnecessary')
    except TypeError:
        log('selftest 2: kl_hvk.join raises the TypeError the module avoids (as measured)')
    j = join([(m06, chop)], (f07, s_refs))
    data = j.serialize()
    again = Hvk(data)
    if again.serialize() != data:
        bad.append('donor join does not round-trip')
    n_sys = sum(1 for s in f07.shapes for i in s.inst if kl_hvk.ref(i) in s_refs)
    n_out = sum(len(s.inst) for s in again.shapes)
    veh = sum(len(s.inst) for s in again.shapes if s.type == kl_hvk.VEHICLE and any(kl_hvk.ref(i) in chop.values() for i in s.inst))
    if len(again.lists) != len(f07.lists) or veh != 1:
        bad.append('donor join: %d list codes (F07 has %d), %d chopper placements (1 wanted)' % (len(again.lists), len(f07.lists), veh))
    log('selftest 2: donor join: %s placements out (systems %d + chopper 1), lists %d, round-trip ok' % (n_out, n_sys, len(again.lists)))
    return bad


if __name__ == '__main__':
    if sys.argv[1:] == ['selftest']:
        problems = selftest()
        print('kl_hvk_donor selftest: problems: %d %s' % (len(problems), problems))
        sys.exit(1 if problems else 0)
    print(__doc__)
