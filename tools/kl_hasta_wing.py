"""kl_hasta_wing.py - OPT-IN post-pass for Hasta (DM11B): the locked loot wing opens sooner. Reads a BUILT F04_Main.zip, writes a copy. Nothing imports it.
Written 2026-10-24 (hc2hasta_1024b) after the owner: "lighting issues on hasta and the loot area isnt blown up so you cant walk in".

FOUND (offline, live DM11B F04_Main.zip of 2026-10-24):
  * The wing is shut by three nodes (kl_fa_hasta_layer.locked_nodes: End_Corridor_01a\\ColiObj_Obj_Roadblock_01, Main_Hall_01a\\SI0100_M11_BarricadeB_01,
    M11B_OYCHECK_BEFORE01). kl_walk2d from START (33950, 30250): shut = the person reaches only x <= 38100; with those three dropped = x up to 43220 (the
    wing). So the geometry is right: the wing opens IF the opener (campaign DeactivateGeom 'GeomDeactivatorSandbags') fires. lock_check(sc) reports no fault.
  * The opener is fired by Timer_SandbagsDeactive, which is named by (a) F07's spare TriggerCounter 'Gameplay!020_Loot!FollowPlayers!TriggerCounter', count 6,
    one count per hall squad wiped out, and (b) the backstop timer, 300 s. The six squads are RebelMainBarricadeEntrance_01 (Hunt), RebelGotoHole (Defend,
    eUnleashed), RebelSideBarricadeSideEntrance_01/_02 and RebelSideBarricadeTopFloor_01/_02 (Defend, eStayBack = they hold their posts, upper floor and the
    side barricades). The owner's round ended after ~145 s (his log) and the wing was shut: a 'stay back' squad that nobody reaches keeps the count below 6,
    and the backstop (300 s) is later than the round. So the beat is too strict for the way a round is played; the walls are not the fault.
WHAT IT CHANGES (the .prp only; no slot or REF number moves)
  1. the counter's count 6 -> --count N (default 3). GUESS: any three of the six squads dead is 'the hall is broken'; TriggerCounter field 0 is the count
     (kl_fa_hasta_layer sets it with f0=len(squads)).
  2. the backstop TriggerDelay2's delay 300 s -> --backstop S (default 100). GUESS: ~100 s is inside an owner round (145 s) and after the first fight.
Usage (from tools/):  python kl_hasta_wing.py <in F04_Main.zip> <out F04_Main.zip> [--count N] [--backstop S]
"""
import os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_fa_author as A, kl_fa_hasta_layer as H
from kl_fa_bank import values


def wire(sc, count=3, backstop=100.0, log=print):
    """-> number of fields changed. Refuses when the lock-wing chain is not in the scene (lock_check)."""
    if not H.lock_present(sc):
        raise ValueError('kl_hasta_wing: the lock-wing chain is not in this level (not DM11B with --lock-wing)')
    bad = H.lock_check(sc)
    if bad:
        raise ValueError('kl_hasta_wing: lock_check reports %s; nothing changed' % (bad,))
    n = 0
    kc = A.node_of(sc, H.COUNTER)
    ic = A.ctrl_of(sc, kc, 'TriggerCounter')
    old = values(sc, kc, 'TriggerCounter')[0]
    if old != count:
        kl_fa.edit(sc, kc, ic, lambda us: A.setv(sc, us, 0, count))
        log('  TriggerCounter count %s -> %d (of %d hall squads)' % (old, count, old))
        n += 1
    kb = A.node_of(sc, H.ROLE['backstop'])
    ib = A.ctrl_of(sc, kb, 'TriggerDelay2')
    old = values(sc, kb, 'TriggerDelay2')[0]
    if abs(old - backstop) > 1e-3:
        kl_fa.edit(sc, kb, ib, lambda us: A.setv(sc, us, 0, float(backstop)))
        log('  backstop delay %.1f s -> %.1f s' % (old, backstop))
        n += 1
    return n


def run(src, dst, count=3, backstop=100.0, log=print):
    sc, _, _ = kl_fa.load(src)
    zf = zipfile.ZipFile(src)
    names = zf.namelist()
    pn = [n for n in names if n.lower().endswith('_main.prp')][0]
    if not wire(sc, count, backstop, log):
        log('kl_hasta_wing: nothing to change')
        return {}
    back = sc.p.serialize()
    members = [(n, back if n == pn else zf.read(n)) for n in names]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    log('kl_hasta_wing: wrote %s (changed: %s)' % (dst, pn))
    return {pn: back}


def main():
    argv = sys.argv[1:]
    opt = {}
    a = []
    i = 0
    while i < len(argv):
        if argv[i] in ('--count', '--backstop'):
            opt[argv[i]] = argv[i + 1]
            i += 2
        else:
            a.append(argv[i])
            i += 1
    if len(a) != 2:
        print(__doc__)
        return 2
    run(a[0], a[1], int(opt.get('--count', 3)), float(opt.get('--backstop', 100.0)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
