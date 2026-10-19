"""kl_escape_noblow.py - OPT-IN post-pass: the ESCAPE vehicle of a built map can no longer blow up. Reads a BUILT Fxx_Main.zip,
writes a copy. Does nothing unless run; no builder imports it. Written 2026-10-19 after the owner's run of 13:25 (Hasta, F04).

WHY: on Hasta (DM11B) the escape vehicle is Dead Men M06's 'EscapeSetup!EscapeChopper\\Escape_Chopper' with VehicleEffects
field 23 = BlowupChanceDefinite and health 2200. KLHook's FollowOutHold kept it waiting ~45 s for the crew but could not shield it
(the 'Invulnerable' byte exists only on a ZAnimatedVehicle health object, the chopper has none), the police shot it down
(state 6 = DESTROYED) and the five bots aboard died with it (KLHook.log 13:29:27). DM05A carries the same chopper.
WHAT IT CHANGES: VehicleEffects field 23 (enum BlowupChance*, CERTAIN) BlowupChanceDefinite -> BlowupChanceNone on every node
under an 'EscapeSetup!' path. Only the .prp member differs: no entity added or removed, slot order unchanged (kl_netcheck).
GUESS: that None alone keeps the vehicle out of state 6 (in Dog Days' own maps 'None' cars - armoured transports - do not blow up;
whether a helicopter's death path also reads it is not proven).
Usage (from tools/):  python kl_escape_noblow.py <in Fxx_Main.zip> <out Fxx_Main.zip> [--prefix 'EscapeSetup!']
"""
import os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_map_ai as MA
from kl_prp import units

BLOW_FIELD = 23                       # VehicleEffects: enum BlowupChance* (same field kl_hc2_strip.py sets)


def noblow(src, dst, prefix='EscapeSetup!', log=print):
    zf = zipfile.ZipFile(src)
    sc, _, _ = kl_fa.load(src)
    changed = []
    for k in range(1, len(sc.nodes)):
        if prefix.lower() not in sc.path[k].lower():
            continue
        for ci, (nm, b) in enumerate(sc.nodes[k]['ctrls']):
            if sc.p.key(nm) != 'VehicleEffects':
                continue
            us = [list(u) for u in units(b[1:-1])]
            if kl_fa.value(sc, us[BLOW_FIELD]) != 'BlowupChanceDefinite':
                continue
            kl_fa.edit(sc, k, ci, lambda f: MA.setv(sc, f, BLOW_FIELD, 'BlowupChanceNone'))
            changed.append(sc.path[k])
    if not changed:
        log('kl_escape_noblow: nothing to change in %s (no Definite escape vehicle under %r)' % (src, prefix))
        return changed
    pn = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
    members = [(n, sc.p.serialize() if n == pn else zf.read(n)) for n in zf.namelist()]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    for p in changed:
        log('  None: %s' % p)
    log('kl_escape_noblow: %d escape vehicle(s) -> BlowupChanceNone -> %s' % (len(changed), dst))
    return changed


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    prefix = a[a.index('--prefix') + 1] if '--prefix' in a else 'EscapeSetup!'
    noblow(a[0], a[1], prefix)
    return 0


if __name__ == '__main__':
    sys.exit(main())
