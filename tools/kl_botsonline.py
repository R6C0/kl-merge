"""kl_botsonline.py - give a finished Dead Men FA build's seven bot squads an EGameType that includes online Fragile Alliance.

    python kl_botsonline.py <in F01_Main.zip> <out F01_Main.zip> [eAllTypes|eFragileAllianceOnly]

Why: the clone from F07 has ZSquadScript field 1 = eHeistOnly (mask 8). Online, ZSquadScript slot 14 (kl2 0x7b3790) drops a member whose squad
mask lacks FA (bit 1) when the session is networked and the game type is FA, so the 7 Glazer_Bodyguard_0N never run (re/bots_online_fill.md).
eAllTypes keeps Arcade (mask has 8) and adds online; only the .prp changes, every other member is copied byte for byte.
STOCK MODE: python kl_botsonline.py --stock <in Fxx_Main.zip> <out Fxx_Main.bots.zip> [game] [--only <name part>]: every eHeistOnly ZSquadScript
(or only those whose node name contains <name part>, e.g. merc_bot_squad: DD01 also has 4 SwatExit#0N_HEIST squads that are not heisters), full verify.
The same change for a fresh build: kl_fa_bots.py build ... --squad-game eAllTypes (field written at clone time)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa, kl_gms
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_loot_1025 as LO


def convert(src, dst, game='eAllTypes', slot='F01', log=print):
    B = KB.Built(src, slot)
    sc = B.sc
    sq = [(k, i, v) for k, i, v in kl_fa.controllers(sc, 'ZSquadScript') if k in sc.tops() and KB.SQUAD + 'Squad#' in sc.names[k]]
    if len(sq) != 7:
        raise ValueError('%d bot squads (want 7)' % len(sq))
    for k, i, v in sq:
        if v[1] not in ('eHeistOnly', game):
            raise ValueError('%s: field 1 = %s' % (sc.names[k], v[1]))
        kl_fa.edit(sc, k, i, lambda us: AU.setv(sc, us, 1, game))
    LO.patch_zip(src, dst, {B.ext['.prp']: sc.p.serialize()})
    A = KB.Built(dst, slot)
    got = [(sc.names[k], v[1], v[0]) for k, i, v in kl_fa.controllers(A.sc, 'ZSquadScript') if k in A.sc.tops() and KB.SQUAD + 'Squad#' in A.sc.names[k]]
    bad = [g for g in got if g[1] != game]
    if len(got) != 7 or bad or len(A.sc.names) != len(sc.names):
        raise ValueError('verify: %s' % got)
    for n in A.files:
        if n != B.ext['.prp'] and A.files[n] != B.files[n]:
            raise ValueError('member %s changed' % n)
    for g in got:
        log('  %s: field 1 eHeistOnly -> %s (field 0 %s)' % g)
    return got


def convert_stock(src, dst, game='eAllTypes', slot='F01', log=print, only=None):
    """STOCK-MAP MODE (2026-10-26): EVERY ZSquadScript (any node, any name) whose field 1 is eHeistOnly -> game. Nothing else may change:
    every other archive member byte for byte, every other node/controller/field equal after re-reading. -> [(node name, field 0)]."""
    B = KB.Built(src, slot)
    sc = B.sc
    hit = [(k, i, v) for k, i, v in kl_fa.controllers(sc, 'ZSquadScript') if v[1] == 'eHeistOnly' and (not only or only in sc.names[k])]
    if not hit:
        raise ValueError('no ZSquadScript with field 1 eHeistOnly')
    for k, i, v in hit:
        kl_fa.edit(sc, k, i, lambda us: AU.setv(sc, us, 1, game))
    LO.patch_zip(src, dst, {B.ext['.prp']: sc.p.serialize()})
    O = KB.Built(src, slot)      # the untouched original, re-read
    A = KB.Built(dst, slot)
    want = {(k, i) for k, i, v in hit}
    if len(A.sc.nodes) != len(O.sc.nodes) or A.sc.names != O.sc.names:
        raise ValueError('verify: node list changed')
    for n in A.files:
        if n != B.ext['.prp'] and A.files[n] != O.files[n]:
            raise ValueError('member %s changed' % n)
    if A.order != O.order:
        raise ValueError('verify: member order changed')
    nfield = 0
    for k in range(1, len(O.sc.nodes)):
        no, na = O.sc.nodes[k], A.sc.nodes[k]
        if kl_fa.node_values(O.sc, k) != kl_fa.node_values(A.sc, k) or len(no['ctrls']) != len(na['ctrls']):
            raise ValueError('verify: node %d (%s) changed' % (k, O.sc.names[k]))
        for i, ((n1, b1), (n2, b2)) in enumerate(zip(no['ctrls'], na['ctrls'])):
            u1 = [kl_fa.value(O.sc, u) for u in kl_fa.units(b1[1:-1])]
            u2 = [kl_fa.value(A.sc, u) for u in kl_fa.units(b2[1:-1])]
            if O.sc.p.key(n1) != A.sc.p.key(n2):
                raise ValueError('verify: controller name changed at node %d' % k)
            if (k, i) in want:
                if u1[1] != 'eHeistOnly' or u2[1] != game or u1[:1] + u1[2:] != u2[:1] + u2[2:]:
                    raise ValueError('verify: %s squad fields %s -> %s' % (O.sc.names[k], u1, u2))
                nfield += 1
            elif u1 != u2:
                raise ValueError('verify: node %d (%s) controller %d changed' % (k, O.sc.names[k], i))
    if nfield != len(hit) or (not only and any(v[1] == 'eHeistOnly' for k, i, v in kl_fa.controllers(A.sc, 'ZSquadScript'))):
        raise ValueError('verify: %d of %d squads changed / eHeistOnly left' % (nfield, len(hit)))
    out = [(sc.names[k], v[0]) for k, i, v in hit]
    for nm, f0 in out:
        log('  %s: field 1 eHeistOnly -> %s (field 0 %s)' % (nm, game, f0))
    log('%d ZSquadScript changed; other squads (not eHeistOnly): %s' % (len(out), sorted({v[1] for k, i, v in kl_fa.controllers(A.sc, 'ZSquadScript')})))
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--stock':
        only = None
        if '--only' in a:
            j = a.index('--only'); only = a[j + 1]; a = a[:j] + a[j + 2:]
        if len(a) not in (3, 4):
            raise SystemExit(__doc__)
        convert_stock(a[1], a[2], a[3] if len(a) == 4 else 'eAllTypes', only=only)
        raise SystemExit(0)
    if len(a) not in (2, 3):
        raise SystemExit(__doc__)
    convert(a[0], a[1], a[2] if len(a) == 3 else 'eAllTypes')
