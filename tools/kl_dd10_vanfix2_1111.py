#!/usr/bin/env python3
r"""kl_dd10_vanfix2_1111.py - Flat Raid (DD10, slot F07): v2 of kl_dd10_vanfix_1111 (stage only, nothing installed, no game launched).

WHY: v1 (KillBox sunk + 3 hit relays cut, INSTALLED as F07 0dc61bdf) did NOT fix the first-spawn death. Bench dd10vanfix1111a (2026-11-11 01:59,
TEST 91f5bd6d [DeathTrace]) MEASURED: the player walked west at -598 cm/s, stopped at x 9112 (v -102), then took ONE hit of 11000, kind 1, attacker null,
at (9099, 1, 958) - the approach box's EAST edge (x 9100, node 22144, shows the van via ActivateGeom 22000 'AITrigger' -> the van group). Stack
0x8ed094 -> 0x787250 -> 0x589318 (radius entity query) -> 0x5c7d30 -> 0x7e182e (damage apply): an AREA blast. The owner saw the van explode on screen.
The van group holds two Explode controllers: FX0900_ALL_Explosion_Gas_S_01 (node 21865, reach 600 / 400, message 'Activate', fired by Relay_VanExplotion
21972 from the four crash legs) and Template_Car_Explotion_01 (21804, reach 1000 / 200, message 'Activate_DamageFX_03').
GUESS: the show (ActivateGeom 'AITrigger' to the whole group) or the van's state-0 crash leg sets one of them off; which one is NOT proven. This stage makes BOTH
harmless and cuts the relay, so whichever it is, nobody is hurt. Visual FX/sound may still play (particles are separate).

PARTS (--parts, default reach,relay):
  reach  Explode fields 0 / 1 (reach, inner reach: kl_fa_blast E_REACH / E_INNER; precedent kl_fa_author BLAST_HARMLESS writes 1.0 / 1.0) -> 1.0 on 21865 and 21804.
  relay  Relay_VanExplotion (21972) loses its RelayMessage controller (deleted as kl_dd10_vanfix_1111 deletes the hit relays): the crash legs no longer reach the gas Explode.
Input = the LIVE DD10 with v1 installed. Changes ONLY the .prp of the plain and the bots zip.

  python tools/kl_dd10_vanfix2_1111.py stage|check [--parts reach,relay] [--in-dir <map dir>] [--out-root C:/kl_build_1024] [--no-undo]
Undo: UNDO.bat (back to v1's files byte for byte); then v1's own UNDO.bat for the pre-v1 files."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dd10_vanfix_1111 as V1

R, VAN = V1.R, V1.VAN
GAS = VAN + 'F07_Escape_Vehicle_01' + chr(92) + 'V_Van_00' + chr(92) + 'FX0900_ALL_Explosion_Gas_S_01'
TPL = VAN + 'Template_Car_Explotion_01'
RELAY = VAN + 'F07_Escape_Vehicle_01' + chr(92) + 'Relay_VanExplotion'
REACH_OLD = {GAS: (600.0, 400.0), TPL: (1000.0, 200.0)}
REACH_NEW = 1.0
PARTS_ALL = ('reach', 'relay')
LIVE_MD5 = {V1.ZIP: '0dc61bdf9fe811b3ee822499944ecdc9', V1.BOTS: '67753c7886bc4784d90617fab6deafbb', V1.BASE: '4da0052a'}   # BASE filled from the live file at import
NAME, TAG = 'dd10vanfix2_1111', '.before-dd10vanfix2_1111'


def explode_vals(sc, k):
    for kk, i, v in V1.kl_fa.controllers(sc, 'Explode'):
        if kk == k:
            return v
    raise SystemExit('REFUSED: %s has no Explode controller' % sc.path[k])


def edit_scene(B, parts=PARTS_ALL, log=print):
    sc = B.sc
    import kl_graft
    ks = {n: V1.A.node_of(sc, n) for n in (GAS, TPL, RELAY)}
    for n in (GAS, TPL):
        v = explode_vals(sc, ks[n])
        if 'reach' in parts and (round(v[0], 3), round(v[1], 3)) != REACH_OLD[n]:
            raise SystemExit('REFUSED: %s reach %r, expected %r' % (n, v[:2], REACH_OLD[n]))
    rl = [c for c in V1.kl_fa.controllers(sc, 'RelayMessage') if c[0] == ks[RELAY]]
    if 'relay' in parts and (len(rl) != 1 or rl[0][2][2] != GAS):
        raise SystemExit('REFUSED: Relay_VanExplotion does not relay to the gas Explode: %r' % rl)
    done = []
    if 'reach' in parts:
        for n in (GAS, TPL):
            k = ks[n]
            ci = V1.A.ctrl_of(sc, k, 'Explode')
            name, fields = sc.nodes[k]['ctrls'][ci]
            # same field form kl_fa_author's put() writes: (tag, 4-byte float) pairs; field 0 / 1 = reach / inner reach
            import struct
            body = list(fields)
            fl = [i for i, x in enumerate(body) if x[0] == 10]
            for j in (0, 1):
                body[fl[j]] = (10, struct.pack('<f', REACH_NEW))
            sc.nodes[k]['ctrls'][ci] = (name, body)
            log('  Explode node %d (%s): reach %s -> %.1f / %.1f' % (k, n.rsplit(chr(92), 1)[-1], REACH_OLD[n], REACH_NEW, REACH_NEW))
            done.append(k)
    if 'relay' in parts:
        k = ks[RELAY]
        del sc.nodes[k]['ctrls'][V1.A.ctrl_of(sc, k, 'RelayMessage')]
        log('  Relay_VanExplotion node %d: RelayMessage removed' % k)
        done.append(k)
    return done


def _wire():
    """Point V1's stage/check machinery at this stage (its install template, zip writer and undo rehearsal are reused unchanged)."""
    V1._mods()
    V1.LIVE_MD5 = dict(LIVE_MD5)
    V1.NAME, V1.TAG = NAME, TAG
    V1.PARTS_ALL = PARTS_ALL
    V1.edit_scene = edit_scene
    V1.README = README


README = """DD10 VAN FIX v2 1111 (Flat Raid, slot F07) - staged, NOT installed. (recommended on)
On top of v1 (kl_dd10_vanfix_1111, live F07 0dc61bdf). Parts: %(parts)s. Both van Explode controllers get reach 1 cm; Relay_VanExplotion is cut.
Staged md5: zip %(zip)s bots %(bots)s base %(base)s. INSTALL.bat installs (refuses unless the live files are v1's), UNDO.bat puts v1's files back.
"""


def check(in_dir, out_root, parts, log=print, undo_rehearsal=True):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(c, msg):
        log('  %s %s' % ('ok  ' if c else 'FAIL', msg))
        if not c:
            bad.append(msg)
    import zipfile
    for n in (V1.ZIP, V1.BOTS):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order' % n)
            changed = sorted(m.rsplit('_Main', 1)[1] for m in zb.namelist() if zb.read(m) != zs.read(m))
            need(changed == ['.prp'], '%s: only .prp differs (%s)' % (n, changed))
        Bb, Bs = V1.F.Built(base), V1.F.Built(stg)
        need(V1.F.Prp(Bs['.prp']).serialize() == Bs['.prp'], '%s: .prp round trip' % n)
        ks = {x: V1.A.node_of(Bs.sc, x) for x in (GAS, TPL, RELAY)}
        want = set()
        if 'reach' in parts:
            for x in (GAS, TPL):
                v = explode_vals(Bs.sc, ks[x])
                vb = explode_vals(Bb.sc, ks[x])
                need(v[0] == REACH_NEW and v[1] == REACH_NEW and v[2:] == vb[2:], '%s: %s reach %s, other fields equal' % (n, x.rsplit(chr(92), 1)[-1], v[:2]))
                want.add(ks[x])
        if 'relay' in parts:
            need(not [c for c in V1.kl_fa.controllers(Bs.sc, 'RelayMessage') if c[0] == ks[RELAY]], '%s: Relay_VanExplotion has no RelayMessage' % n)
            want.add(ks[RELAY])
        diffn = [j for j in range(1, len(Bb.sc.nodes)) if Bb.sc.nodes[j]['props'] != Bs.sc.nodes[j]['props'] or Bb.sc.nodes[j]['ctrls'] != Bs.sc.nodes[j]['ctrls']]
        need(set(diffn) == want, '%s: exactly nodes %s differ (got %s)' % (n, sorted(want), diffn))
        need(len(Bb.sc.nodes) == len(Bs.sc.nodes), '%s: node count unchanged' % n)
    ok = V1.check.__wrapped__ if hasattr(V1.check, '__wrapped__') else None
    log('CHECK %s (%d failures)' % ('PASS' if not bad else 'FAIL', len(bad)))
    return not bad


def main(a):
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] not in ('stage', 'check'):
        print(__doc__)
        return 2
    in_dir, out_root = opt('--in-dir', V1.LIVE), opt('--out-root', V1.OUT_ROOT)
    LIVE_MD5[V1.BASE] = V1.fmd5(os.path.join(in_dir, V1.BASE))
    _wire()
    parts = tuple(opt('--parts', ','.join(PARTS_ALL)).split(','))
    if not set(parts) <= set(PARTS_ALL):
        print('REFUSED: unknown part in %s' % (parts,))
        return 2
    if a[0] == 'stage':
        V1.stage(in_dir, out_root, parts)
    return 0 if check(in_dir, out_root, parts) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
