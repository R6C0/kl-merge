#!/usr/bin/env python3
"""
Cut every scene-path field that names a node that is not there (re/l05_flat_raid_1025.md section 6).

WHY: a graft with --m-drop leaves the kept subtrees holding paths into the dropped ones (L05 stripped of
Checkpoints / AI!Friendly / ...: 214 to 284 dangling paths, every one held by an enemy squad, a trigger or a
gate). kl_fa.prune does this only with the FA layer on and only for M's own tops; this works on the whole
joined scene, with or without --no-fa, and loops until kl_prpjoin.dangling finds nothing.

Rules (what "cut" means, per field form as kl_prp.units splits it):
  - a reference LIST (0x04 count + n strings): the entries that do not resolve are removed and the count
    rewritten. GUESS (same as kl_fa.prune): parallel lists (a position list next to a name list) are not
    kept in step; no list of the L05 squads was found to be paired, but that was not read per class.
  - a single path string: set to the empty string. GUESS: the engine treats an empty path as "no target";
    stock Dog Days levels hold empty strings in these same fields (kl_fa.repair writes them too).
  - the scene property block (holder -1): left alone and counted (camera paths; kl_graft re-points them).
  - 0x0f key lists: left alone and counted (not seen to hold a dangling path).
The nodes are NOT deleted: only the pointers. -> {'lists': entries removed, 'strings': blanked, 'left': n}

    python kl_prune_dangling.py <F01_Main.zip>        report only (what would be cut, by holder class and target)
"""
import collections, os, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prpjoin as J
import kl_fa
from kl_prp import units


def _gone(sc, tok):
    s = sc.p.key(tok)
    return s[:5].upper() == 'ROOT\\' and not sc.resolve(s)


def prune(sc, log=print, limit=8):
    """Cut dangling paths of every node (and controller) of sc until none is left. -> counts."""
    tot = {'lists': 0, 'strings': 0, 'left': 0, 'rounds': 0}
    for rnd in range(limit):
        paths, _names = J.dangling(sc)
        holders = {k for k, _h, _f, _s in paths if k >= 0}
        tot['left'] = sum(1 for k, _h, _f, _s in paths if k < 0)
        if not holders:
            break
        tot['rounds'] += 1
        for k in sorted(holders):
            for i in [None] + list(range(len(sc.nodes[k]['ctrls']))):
                def fn(us):
                    for j, u in enumerate(us):
                        if u[0][0] == 0x04 and len(u) > 1 and u[1][0] == 0x0c:
                            live = [x for x in u[1:] if not _gone(sc, x)]
                            tot['lists'] += len(u) - 1 - len(live)
                            us[j] = [(0x04, struct.pack('<I', len(live)))] + live
                        elif u[0][0] == 0x0c and _gone(sc, u[0]):
                            us[j] = [kl_fa._str(sc, '')]; tot['strings'] += 1
                kl_fa.edit(sc, k, i, fn)
    paths, names = J.dangling(sc)
    tot['left'] = len(paths)
    log('  prune_dangling: %d list entries removed, %d path strings blanked in %d round(s); %d dangling paths left '
        '(%d scene-block), %d bare names without node (not touched)' % (
            tot['lists'], tot['strings'], tot['rounds'], len(paths), sum(1 for p in paths if p[0] < 0), len(names)))
    return tot


def report(path):
    sc = J.Scene.from_zip(path, 'dd', path)
    paths, names = J.dangling(sc)
    by = collections.Counter()
    for k, h, f, s in paths:
        by[(sc.names[sc.top[k]] if k > 0 else '(block)').split('!')[0] + ' -> ' + s.split('\\')[1].split('!')[0] if s.count('\\') else s] += 1
    print('%s: %d dangling paths, %d names' % (path, len(paths), len(names)))
    for kv, n in by.most_common(25):
        print('  %5d  %s' % (n, kv))


if __name__ == '__main__':
    if len(sys.argv) == 2:
        report(sys.argv[1])
    else:
        print(__doc__)
