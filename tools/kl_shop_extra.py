#!/usr/bin/env python3
r"""
kl_shop_extra.py - which extra guns can klhook\klshop.c hand over in place of a shop row (re\shop_more_guns.md). OFFLINE, read only.
The swaps it suggests ran live 2026-10-20 (S7-S11, re\shop_more_guns.md).

    python kl_shop_extra.py rows [kl2.exe]            the 36 shop rows read from the exe: row, item, ammo, price, rank, tier, DLC
    python kl_shop_extra.py check <build folder>      per NON-shop item 1..63: has the build a weapon template (the pool maker needs one),
                                                      and which handling clips does the police set carry (GUESS: the criminal sets
                                                      must carry them too). Prints candidate "Swap=row:item" lines.
The shop rows themselves cannot grow (hashed table); a swap REPLACES what one row hands over. Rename that row's text yourself
(LOC / menu text) so the shop does not show the old gun; this tool only prints the facts.
"""
import os, sys, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
EXE = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'
TABLE, ROWS = 0xbd1f68, 36


def rows(path=EXE):
    import kl_exe
    x = kl_exe.Exe(path)
    return [struct.unpack('<6i', x.read(TABLE + 24 * i, 24)) for i in range(ROWS)]


def main():
    a = sys.argv[1:]
    if a and a[0] == 'rows':
        for i, r in enumerate(rows(*a[1:2])):
            print('row %2d item %2d ammo %4d price %7d rank %2d tier %d dlc %d' % ((i,) + r))
        return 0
    if len(a) == 2 and a[0] == 'check':
        import kl_fa_fedbody as F
        L = F.Level(a[1])
        guns = L.guns()
        shop = {r[0] for r in rows()}
        try:
            _m, aset, _p = L.police()
            clips = L.handling(aset)
        except ValueError as e:
            print('police set unreadable: %s' % e); clips = {}
        print('shop items: %s' % sorted(shop))
        cand = []
        for it in range(1, 64):
            if it in shop:
                continue
            g = guns.get(it)
            print('item %2d  %-28s  %s' % (it, g[0] if g else '-- no template: unusable --', ('handling ' + str(g[1])) if g else ''))
            if g:
                cand.append(it)
        print('usable (template present, NOT yet proven to have handling clips): %s' % cand)
        print('example line for KLHook.ini [Shop]: Swap=<row>:<item>  e.g. a row whose gun you will not miss')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
