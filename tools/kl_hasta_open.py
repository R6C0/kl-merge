"""kl_hasta_open.py - OPT-IN post-pass for Hasta (DM11B, slot F04): (1) the locked loot wing opens EARLY, (2) the stray green grade box is made neutral.
Reads a BUILT F04_Main.zip, writes a copy. Rerunnable: running it on its own output gives the same bytes. Nothing imports it.
Written 2026-10-24 (hasta_1024n) after the owner: "fix the damn lighting on hasta when it makes you green" and "u still cant go to the loot room since the
thing isnt blown up just a bunch of sandbags n barricades n barb wire not letting you over". Replaces kl_hasta_wing.py (whose defaults 3 / 100 s the owner
found too slow: short rounds of 79 to 141 s never reached either).

1. THE WING (offline, kl_walk2d on the live zip md5 ef53c079, START (33950, 30250))
   Three nodes shut it (kl_fa_hasta_layer.locked_nodes): End_Corridor_01a\\ColiObj_Obj_Roadblock_01, Main_Hall_01a\\SI0100_M11_BarricadeB_01,
   M11B_OYCHECK_BEFORE01. Shut: the person reaches x <= 38100. With the three dropped: x up to 43220 and all 16 loot positions (CASES and PAINTINGS) are reached.
   The campaign's own beat (TriggerCounter 'Gameplay!020_Loot!FollowPlayers!TriggerCounter' -> Timer_SandbagsDeactive -> DeactivateGeom of the three nodes + the
   bunker-blast show) needed 3 of 6 hall squads dead or 100 s. Several of the six squads are eStayBack, so in a short round neither happened.
   NOW: counter count 2 (--count) and backstop TriggerDelay2 30 s (--backstop). The campaign show (dust emitters, Broken01 / AFTER01 remains, barrels) is kept:
   the sandbags blow at the latest 30 s into the round. GUESS (no live run): the backstop starts with the round, as its 300 s default implies.
   --fallback-sink additionally removes the three nodes at BUILD time (Doors sink + HVK cut, as the lock wing's own build does); NOT default, it needs the
   Doors machinery and is only for the case where a live run shows DeactivateGeom does not remove these three.

2. THE GREEN (offline; the colour itself is UNPROVEN because the palette curve coding was not decoded)
   Hasta carries ONE PostFilterBox: Dead Men's stray 'Locations/M11_A/M11A_Postfilter.zip\\Box' (the stock M11_B has it too), set '\\Locations\\M11_A\\Default.Pof',
   centre (12507, 2316, 10905), 32000 x 4000 x 32000 = x -3493..28507, z -5000..26905, y 316..4316. 1931 of the 9804 positioned nodes of the map lie inside:
   the whole west part (rooftop, courtyard, palms, police spawn (27500, 200, 22800), escape area). The box's set (56696 in the live .prm) is M11_A's own look
   (floats 0,1,1,..., its own R/G/B curves 58..71); every other Dead Men map the project grafted has boxes that match its play area, this one does not.
   Entering the box = the grade switches on = the owner's 'it makes you green' (the position test is by area, which matches 'when it makes you').
   NOW: the set the box names is overwritten, byte for byte, with the neutral set the Dog Days camera setup already ships (curves 1,0,0,0,1,... = identity),
   so the box stays (no structure change, nothing renumbered) but grades nothing. --keep-grade leaves it alone.
Usage (from tools/):  python kl_hasta_open.py <in F04_Main.zip> <out F04_Main.zip> [--count N] [--backstop S] [--keep-grade] [--force]
"""
import hashlib, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_light, kl_dmassets, kl_prmgraph as G, kl_prpjoin as J, kl_fa_author as A, kl_fa_hasta_layer as H
from kl_fa_bank import values

# the live DM11B zip of 2026-10-24 (hc2hasta_1024d: counter 3, backstop 100 s). OUTPUT_MD5 is filled in after the first build.
KNOWN_INPUT_MD5 = {'ef53c07927fac0599c366cd4ebc38ab5'}
KNOWN_OUTPUT_MD5 = {'323c13f3f76095941db9eecbe0f82bdb'}
NEUTRAL = (1, 0, 0, 0, 1, 0, 0, 0, 1) * 4       # 36 identity entries ... see neutral_set()
BOX_RECORD = 88                                  # kl_light: PostFilterBoxes chunk = 88-byte records, +0x30 = the set chunk


def md5(b):
    return hashlib.md5(b).hexdigest()


def wire(sc, count=2, backstop=30.0, log=print):
    """The opener. -> number of fields changed. Refuses when the chain is not DM11B's lock wing."""
    if not H.lock_present(sc):
        raise ValueError('kl_hasta_open: the lock-wing chain is not in this level (not DM11B with --lock-wing)')
    # lock_check wants count 6 (the build's own value); the only fault allowed here is the count itself
    bad = [b for b in H.lock_check(sc) if not str(b).startswith('the counter holds')]
    kc = A.node_of(sc, H.COUNTER)
    ic = A.ctrl_of(sc, kc, 'TriggerCounter')
    cv = values(sc, kc, 'TriggerCounter')
    if sorted(cv[4]) != sorted(['ROOT\\' + H.SAND_TIMER, 'ROOT\\' + H.DUST_TIMER]):
        bad.append('the counter does not drive exactly the two campaign timers: %s' % (cv[4],))
    if bad:
        raise ValueError('kl_hasta_open: lock_check reports %s; nothing changed' % (bad,))
    n = 0
    if cv[0] != count:
        kl_fa.edit(sc, kc, ic, lambda us: A.setv(sc, us, 0, count))
        log('  TriggerCounter count %s -> %d' % (cv[0], count))
        n += 1
    kb = A.node_of(sc, H.ROLE['backstop'])
    ib = A.ctrl_of(sc, kb, 'TriggerDelay2')
    old = values(sc, kb, 'TriggerDelay2')[0]
    if abs(old - backstop) > 1e-3:
        kl_fa.edit(sc, kb, ib, lambda us: A.setv(sc, us, 0, float(backstop)))
        log('  backstop delay %.1f s -> %.1f s' % (old, backstop))
        n += 1
    return n


def neutral_set(p, kinds):
    """-> (chunk index, bytes) of the stock identity filter set of the camera setup: the ONE 176-byte set whose 37 entries are 1,0,0,0,1,0,0,0,1 x4 then 0
    (what Dog Days' 'Default' filter of every stock level looks like)."""
    want = NEUTRAL + (0,)
    hits = [i for i, k in kinds.items() if k == 'pf' and tuple(kl_light.set_curves(p.chunks[i])) == want]
    if not hits or len({p.chunks[h] for h in hits}) != 1:                 # after a first run the box's set is a second, identical copy
        raise ValueError('kl_hasta_open: %d identity filter sets in the .prm (expected 1): %s' % (len(hits), hits))
    return hits[0], p.chunks[hits[0]]


def box_sets(sc, p):
    """-> the set chunk indices named by the scene's PostFilterBoxes chunk (record +0x30)."""
    blk = dict(J.block(sc))
    if 'PostFilterBoxes' not in blk:
        return []
    ch = struct.unpack('<I', blk['PostFilterBoxes'][4][1])[0]
    c = p.chunks[ch]
    return [struct.unpack_from('<I', c, o + 0x30)[0] for o in range(0, len(c) - len(c) % BOX_RECORD, BOX_RECORD)]


def neutralise(sc, prm_bytes, gms, prp_bytes, log=print):
    """-> new .prm bytes with every box set made neutral (same bytes back when already so)."""
    p = G.read(prm_bytes, 'dd')
    kinds, _a = G.walk(p, kl_dmassets.prm_roots(gms, prp_bytes, 'dd'))
    sets = box_sets(sc, p)
    if not sets:
        log('  no PostFilterBoxes: nothing to grade')
        return prm_bytes
    ni, nb = neutral_set(p, kinds)
    changed = 0
    for s in sorted(set(sets)):
        if kinds.get(s) != 'pf' or len(p.chunks[s]) != kl_light.PF_SET:
            raise ValueError('kl_hasta_open: box set %d is not a filter set (%s)' % (s, kinds.get(s)))
        if p.chunks[s] != nb:
            p.chunks[s] = nb
            changed += 1
            log('  box set chunk %d made neutral (copy of %d)' % (s, ni))
    out = G.write(p)
    if not changed:
        return prm_bytes
    if len(out) != len(prm_bytes):
        raise ValueError('kl_hasta_open: .prm size changed (%d -> %d)' % (len(prm_bytes), len(out)))
    return out


def run(src, dst, count=2, backstop=30.0, grade=True, force=False, log=print):
    raw = open(src, 'rb').read()
    if md5(raw) not in KNOWN_INPUT_MD5 | KNOWN_OUTPUT_MD5 and not force:
        raise ValueError('kl_hasta_open: %s md5 %s is not a known Hasta input (use --force)' % (src, md5(raw)))
    sc, _, _ = kl_fa.load(src)
    zf = zipfile.ZipFile(src)
    names = zf.namelist()
    pn = [n for n in names if n.lower().endswith('_main.prp')][0]
    mn = pn[:-4] + '.prm'
    gn = pn[:-4] + '.gms'
    prp_in = zf.read(pn)
    wire(sc, count, backstop, log)
    prp = sc.p.serialize()
    prm_in = zf.read(mn)
    prm = neutralise(sc, prm_in, zf.read(gn), prp_in, log) if grade else prm_in
    new = {pn: prp, mn: prm}
    members = [(n, new.get(n, None) if n in new else zf.read(n)) for n in names]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    log('kl_hasta_open: wrote %s md5 %s (prp %s, prm %s)' % (dst, md5(open(dst, 'rb').read()),
        'changed' if prp != prp_in else 'same', 'changed' if prm != prm_in else 'same'))
    return dst


def main():
    argv = sys.argv[1:]
    opt, a, i = {}, [], 0
    while i < len(argv):
        if argv[i] in ('--count', '--backstop'):
            opt[argv[i]] = argv[i + 1]
            i += 2
        else:
            (opt.__setitem__(argv[i], True) if argv[i].startswith('--') else a.append(argv[i]))
            i += 1
    if len(a) != 2:
        print(__doc__)
        return 2
    run(a[0], a[1], int(opt.get('--count', 2)), float(opt.get('--backstop', 30.0)), '--keep-grade' not in opt, '--force' in opt)
    return 0


if __name__ == '__main__':
    sys.exit(main())
