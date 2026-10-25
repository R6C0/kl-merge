"""kl_botsonline.py - give a finished Dead Men FA build's seven bot squads an EGameType that includes online Fragile Alliance.

    python kl_botsonline.py <in F01_Main.zip> <out F01_Main.zip> [eAllTypes|eFragileAllianceOnly]

Why: the clone from F07 has ZSquadScript field 1 = eHeistOnly (mask 8). Online, ZSquadScript slot 14 (kl2 0x7b3790) drops a member whose squad
mask lacks FA (bit 1) when the session is networked and the game type is FA, so the 7 Glazer_Bodyguard_0N never run (re/bots_online_fill.md).
eAllTypes keeps Arcade (mask has 8) and adds online; only the .prp changes, every other member is copied byte for byte.
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


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) not in (2, 3):
        raise SystemExit(__doc__)
    convert(a[0], a[1], a[2] if len(a) == 3 else 'eAllTypes')
