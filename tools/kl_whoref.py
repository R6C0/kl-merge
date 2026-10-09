#!/usr/bin/env python3
"""
Who names it? Every node / controller whose fields name a path matching a pattern (a reference
list entry or a ROOT\\ path string), the top-level subtree it sits in, and whether
kl_graft.build would KEEP or DROP that subtree. Also prints the matching nodes' own controllers
and every string in them (the message a MatPosAnim waits for, e.g. 'Activate').
Read-only: nothing is written.

Made for the bank's escape (re/fa_round.md 6.4): what starts the yard fences
SO0301_USA_animFence_02_FA_* in Dead Men's M03_FA_A, and does the graft keep it?

    python kl_whoref.py M03_FA_A "*animFence*"               the converted level, as the graft sees it
    python kl_whoref.py M03_FA_A "*animFence*" --raw <DM>\\...\\M03_FA_A_Main.zip
                                                              also the unconverted Dead Men level:
                                                              a referrer only there = the converter
                                                              dropped it
    python kl_whoref.py M03_FA_A "*MetalGate*" --s F07       another pattern / systems level

LEAD (read of the code, 2026-10-09, not tried): kl_graft.picks_of drops a Dead Men top-level
subtree without a word in these cases:
  1. its NAME equals one of S's systems subtrees -> S's copy is taken instead. Systems names are
     kl_prpjoin.SYSTEMS + Heroes!*, so this hits Dead Men's own TrackLinkObjects,
     ZParticleController, AllLevels/OnlineWeaponPacks.zip and Heroes!*. PRIME SUSPECT:
     TrackLinkObjects - by its name the animation-track links (what it holds is NOT checked);
     if the fences' MatPosAnim tracks are linked from there, F07's copy has nothing for them;
  2. it is on the systems side (gamemenu.zip, AllLevels/mainsceneincludes.zip, CoverList);
  3. M has two top-level subtrees of the same name -> only the first is taken (written for M03's
     duplicate car-explosion clone group, but it applies to every name).
The build log line 'left out of M03_FA_A: ...' counts dropped subtrees by family only; this
tool names them per referrer.

UNTESTED: written from the cloud while the game PC was out of reach (2026-10-09). It reads only
the structures kl_fa.prune / kl_fa.census / kl_graft.picks_of use; if one has moved, fix it here.
"""
import argparse, fnmatch, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_graft as K
import kl_fa
import kl_prpjoin as J
from kl_prp import units


def strings(sc, obj):
    """-> every 0x0c string in one property / controller body."""
    out = []
    for u in units(obj[1:-1]):
        for t in u:
            if t[0] == 0x0c:
                try:
                    out.append(sc.p.key(t))
                except Exception:
                    pass
    return out


def bodies(sc, k):
    """-> [(controller name or '(node)', body)] of node k."""
    n = sc.nodes[k]
    return [('(node)', n['props'])] + [(sc.p.key(nm), body) for nm, body in n['ctrls']]


def tops_index(sc):
    return sorted((t, sc.end[t]) for t in sc.tops())


def top_of(index, k):
    for t, end in index:
        if t <= k < end:
            return t
    return None


def scan(sc, pattern, label, status=None, log=print):
    """Referrers of paths matching pattern, and the matching nodes' own controller strings."""
    pat = pattern.lower()
    index = tops_index(sc)
    log('== %s: referrers of %s' % (label, pattern))
    found = 0
    try:
        # the codebase's own walker: every field of every node AND the scene property block
        # (holder -1), path strings resolved through the scene's index
        hits = list(J.references(sc))
    except Exception as e:
        log('  (kl_prpjoin.references failed: %s: %s - falling back to ROOT\\ strings on nodes)' % (type(e).__name__, e))
        hits = [(k, who, '?', s, sc.resolve(s)) for k in range(1, len(sc.nodes)) for who, body in bodies(sc, k)
                for s in strings(sc, body) if isinstance(s, str) and s[:5].upper() == 'ROOT\\']
    for k, holder, field, s, hit in hits:
        tg = list(hit) if isinstance(hit, (list, tuple, set)) else ([hit] if hit else [])
        if not (fnmatch.fnmatch(s.lower(), pat) or any(fnmatch.fnmatch(sc.names[x].lower(), pat) for x in tg
                                                        if isinstance(x, int) and 0 <= x < len(sc.names))):
            continue
        t = top_of(index, k) if k >= 0 else None
        found += 1
        log('  %-48s %-28s field %-5s -> %s%s   [top: %s%s]' % (
            sc.names[k] if k >= 0 else '(scene property block)', holder, field, s, '' if tg else '  (UNRESOLVED)',
            sc.names[t] if t is not None else '-', (' ' + status(t)) if status and t is not None else ''))
    log('  %d references' % found)
    log('== %s: nodes named like %s, their controllers and strings' % (label, pattern))
    for k in range(1, len(sc.nodes)):
        if fnmatch.fnmatch(sc.names[k].lower(), pat):
            t = top_of(index, k)
            log('  %s [%s] (top: %s%s)' % (sc.names[k], sc.cls(k), sc.names[t] if t is not None else '?',
                                           (' ' + status(t)) if status else ''))
            for who, body in bodies(sc, k):
                ss = [s for s in strings(sc, body) if isinstance(s, str) and s]
                log('      %-28s %s' % (who, ss[:12]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('m', help='Dead Men level, e.g. M03_FA_A')
    ap.add_argument('pattern', help='fnmatch pattern on paths / names, e.g. "*animFence*"')
    ap.add_argument('--s', default='F07', help='systems level of the graft (default F07)')
    ap.add_argument('--raw', help='the unconverted Dead Men archive (..._Main.zip) to scan as well')
    a = ap.parse_args()

    S, M = K.Level(a.s), K.DeadMen(a.m, print, 0.5)
    picks, _dropped = K.picks_of(S, M, K.Select())
    kept = {t for sc, t in picks if sc is M.prp}
    s_sys = {S.prp.names[t] for t in S.prp.tops() if S.side[t] == 'systems'}
    first = {}
    for t in M.prp.tops():
        first.setdefault(M.prp.names[t], t)

    def status(t):
        if t in kept:
            return 'KEPT'
        name = M.prp.names[t]
        why = ('S has a systems subtree of this name' if name in s_sys else
               'second subtree of a duplicate name' if first.get(name) != t else
               'systems side' if M.side[t] != 'map' else 'not selected')
        return 'DROPPED (%s)' % why

    scan(M.prp, a.pattern, '%s converted (graft view)' % a.m, status)
    if a.raw:
        # kl_fa.load reads with the Dog Days schema ('dd'); on an unconverted Dead Men archive
        # that may not parse - the converted scan above has already printed by then
        try:
            sc, _snd, _loc = kl_fa.load(a.raw)
            scan(sc, a.pattern, '%s raw' % a.m)
        except Exception as e:
            print('== raw scan failed (%s: %s): kl_fa.load may need the Dead Men schema' % (type(e).__name__, e))


if __name__ == '__main__':
    main()
