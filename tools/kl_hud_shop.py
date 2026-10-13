"""
kl_hud_shop.py - THE BUY-WEAPONS NAMES (2026-10-13; the owner, with a picture of the weapon shop: 'gun purchase ui ... names a lil revamp too').

The shop lists Dog Days' made-up names ('Kaliningrad 47', 'TOQ Model Four S', 'Nianshi  40XR' with a double space), while the HUD's gun
dial names the same gun 'AK-47' / 'UMP SIL' (klhook/klhud_weapon.c klwd_names). Here the shop takes the HUD's names, so a gun is called
the same thing where you buy it and where you carry it, in the capitals of the owner's look.

WHERE THE NAMES ARE: the level's .LOC, AllLevels/Menu/Online/WeaponShop/Weapon<row> (and Weapon<row>Desc), one per row of the shop table
of kl2.exe (0xbd1f68, 36 rows of 24 bytes {item, ammunition, price, rank, tier, DLC}; read from the owner's kl2.exe 2026-10-13). The row's
item (eFF2Item*, tools/dd_enums.json) names the gun; the LOC's old name and description agree with every row (row 29 = item 31 = AK-47 =
'Kaliningrad 47', the row tools/kl_fa_fedbody.py RECORD already uses).
The descriptions keep their words; only the UTF-8 right quote the game's font shows as an accented 'a' ('Mr. Glazer<a>s') becomes an apostrophe, and
spaces are tidied. All languages: the names are the guns' own (not translated); a language whose leaf is missing is left alone.

NOT DONE: a gun whose LOOK the hook switches ([Guns], tools/kl_guns.py: Zastava as MP5 ...) keeps its Dog Days name, as on the HUD.
NOT LOADED IN THE GAME YET.
"""
import re
import kl_loc as L

KEY = 'AllLevels/Menu/Online/WeaponShop/Weapon'

# shop row -> (item, the name shown). The names are klhud_weapon.c's klwd_names, word for word.
ROWS = (
    (6, 'M-77B'), (7, 'M-77B SIL'), (8, 'M9 BERETTA'), (9, 'M9 BERETTA SIL'), (3, 'POLICE REVOLVER'), (11, 'TT-33'),
    (4, 'SIG 226'), (1, 'SW MP45'), (10, 'DESERT EAGLE'), (5, 'COLT COBRA'), (2, 'TAURUS JUDGE'), (14, 'HAWK SAWN-OFF'),
    (16, 'REMINGTON 870'), (13, 'HAWK POLICE'), (17, 'SPAS-12'), (15, 'TPS'), (12, 'HAWK BULLPUP'), (22, 'SP89 SIL'),
    (23, 'MAC-10'), (24, 'MAC-10 SIL'), (25, 'MPI 69'), (18, 'SA61'), (27, 'TYPE 05'), (28, 'TYPE 05 SIL'),
    (26, 'TYPE 79'), (20, 'UMP'), (21, 'UMP SIL'), (19, 'UMP SBR'), (29, 'ZASTAVA M85'), (31, 'AK-47'),
    (32, 'AK-74'), (34, 'TYPE 88'), (36, 'TYPE 88 SCOPE'), (30, 'FN SCAR'), (37, 'TYPE 95'), (39, 'TYPE 95 SCOPE'),
)
# the stock English names, to refuse a level whose rows are not the ones this table was made from
STOCK_EN = ('N 77P', 'N 77P Silenced', 'Doretta', 'Doretta Silenced', 'Copper', 'DD 33', 'Nianshi 226', 'SM45', 'Wasteland Hawk',
            'KL Viper', 'TOQ Model 66X', 'Nianshi 40XR', 'Steele 870', 'TOQ Model 18', 'Gras 12', 'RTS', 'Buqiang 300BP', 'DK ST80',
            'PAC 10', 'PAC 10 Silenced', 'SMi 69', 'Desert Spider', 'Nianshi 500', 'Nianshi 500 Silenced', 'Nianshi 700',
            'TOQ Model Four', 'TOQ Model Four S', 'TOQ SBR', 'Vamazast', 'Kaliningrad 47', 'Kaliningrad 74', 'Buqiang 800',
            'Buqiang 800 Scoped', 'TOQ Elite', 'Buqiang 900', 'Buqiang 900 Scoped')


def _set_text(node, text):
    t, _x, _sid, _rest = L.fields(node)
    e = node.raw.index(b'\0')
    node.raw = text + node.raw[e:]


def _tidy(b):
    b = b.replace(b'\xe2\x80\x99', b"'").replace(b'\xe2\x80\x98', b"'")
    b = b'\n'.join(re.sub(rb'[ \t]+', b' ', line).strip(b' \t') for line in b.split(b'\n'))
    return b


def apply_loc(data, english=False, log=print, tag=''):
    """one .LOC member -> (new bytes, number of leaves changed). english: check the stock names first (a level whose shop rows read
    otherwise is left alone, logged)."""
    kids = L.parse(data)
    if kids is None:
        return data, 0
    leaves = dict(L.leaves(kids))
    if english:
        have = [L.fields(leaves[KEY + str(r)])[0] if KEY + str(r) in leaves else None for r in range(36)]
        bad = [r for r in range(36) if have[r] is None or b' '.join(have[r].split()).decode('latin1') != STOCK_EN[r]]
        if bad:
            log('shop names %s: rows %s do not read as the stock shop (first: %r) - names left stock' % (tag, bad[:5], have[bad[0]]))
            return data, 0
    n = 0
    for r, (_item, name) in enumerate(ROWS):
        k = leaves.get(KEY + str(r))
        if k is not None and k.flags & L.TEXT:
            if L.fields(k)[0] != name.encode('latin1'):
                _set_text(k, name.encode('latin1')); n += 1
        d = leaves.get(KEY + str(r) + 'Desc')
        if d is not None and d.flags & L.TEXT:
            t = L.fields(d)[0] or b''
            t2 = _tidy(t)
            if t2 != t:
                _set_text(d, t2); n += 1
    if not n:
        return data, 0
    out = L.build(kids)
    assert L.build(L.parse(out)) == out
    return out, n


def apply_level(files, log=print):
    """every .LOC member of an open level (kl_hud.open_level's files) in place -> the names of the members changed"""
    locs = [m for m in files if m.lower().endswith('.loc')]
    en = [m for m in locs if m.lower().endswith('english.loc')]
    if not en:
        log('shop names: the level has no English .LOC - left stock'); return []
    _o, n_en = apply_loc(files[en[0]], True, log, en[0])
    if not n_en:
        return []
    changed = []
    for m in locs:
        new, n = apply_loc(files[m], False, log, m)
        if n:
            files[m] = new; changed.append(m)
    log('shop names: %d weapon names in the HUD\'s wording, descriptions tidied; %d .LOC member(s): %s' % (len(ROWS), len(changed), ', '.join(x.rsplit('/', 1)[-1] for x in changed)))
    return changed
