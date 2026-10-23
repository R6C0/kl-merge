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

LOOKS (2026-10-15, worker 'shop', the owner: 'shop revamp would be good'): a gun whose Dead Men LOOK the build shows (tools/kl_map_guns.py;
KLGuns.ini beside the archive, [Gun.n] Item / Shown / Look<k>) is sold under the look's name - the owner's eight maps all show MP5 on the
Zastava, SG 552 on the FN SCAR, M4A1 on the AK-47, P90 on the Type 05, Steyr TMP on the MAC-10, USP on the M9 Beretta (KLGuns.ini Shown=1
on every one, read 2026-10-15), yet the shop said ZASTAVA M85 ... . The English description of such a row is a new one in the shop's own
'Police reg.' manner that ends 'Handles as the <Dog Days gun>.' (price, rank, stats, sound and animations stay the Dog Days gun's: the shop
table 0xbd1f68 and the templates are not touched); other languages keep their description (the name is the gun's in every language).
The SILENCED rows (M9 BERETTA SIL, MAC-10 SIL, TYPE 05 SIL) are other items with their own models: no look, their names stay.
The name is BAKED: a look switched later on the Guns page ([Guns] Start / Set) is not followed here - the HUD dial follows it
(klhook klhud_weapon.c, [HUD] LookNames=1). No KLGuns.ini, or one without Shown > 0: the names are as before.
    python kl_hud_shop.py names <build folder | KLGuns.ini>      prints the rows this build's looks rename (reads only)

SWAPS (2026-10-20, re/shop_swap_names.md): klhook/klshop.c can make a bought shop row hand over ANOTHER gun ([Shop] Swap=row:item, per map
in KLGuns.ini). The row's name and description are then baked from the handed-over gun (SWAP_ITEMS) so the shop says what you get; its
price, rank, stars, lock and DLC gate stay the carrier row's (hashed table 0xbd1f68). The picture is baked by tools/kl_shop_swap.py.
    python kl_hud_shop.py swaps "13:52,16:33"                    prints the rows a swap line renames
NOT LOADED IN THE GAME YET.
"""
import configparser, os, re, sys
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


# a look's label in KLGuns.ini (tools/kl_map_guns.py LOOKS) -> (the name shown, the English description). The names are klhud_weapon.c's
# klwd_looks word for word. '%s' = the Dog Days gun's own shop name (ROWS), so the player knows what it handles like.
LOOKS = {
    'MP5':       ('MP5', 'Police reg.: 6453-A753\nSubmachine gun. Origin: German. Left behind by The7 after a botched bank job. Handles as the %s.'),
    'AK-74':     ('AK-74', 'Police reg.: 6453-A754\nAssault rifle. Origin: Russian. Bought off a Serbian fence, no questions asked. Handles as the %s.'),
    'SG 552':    ('SG 552', 'Police reg.: 9791-A243\nSwiss carbine. Taken from a dead mercenary on a jungle road. Handles as the %s.'),
    'M4A1':      ('M4A1', 'Police reg.: 1574-A088\nUS carbine. Origin: a Los Angeles police armoury, never reported missing. Handles as the %s.'),
    'P90':       ('P90', 'Police reg.: 4534-A975\nPersonal defence weapon. Origin: Belgian. Recovered after a prison break. Handles as the %s.'),
    'Steyr TMP': ('STEYR TMP', 'Police reg.: 1612-D621\nMachine pistol. Origin: Austrian. Found in a Tokyo nightclub after the shooting. Handles as the %s.'),
    'USP':       ('USP', 'Police reg.: 4962-B092\nHand gun. Origin: German. Confiscated from a Mr. Kane. Handles as the %s.'),
}


# eFF2Item value -> (the name shown, the English description). The first five names are klhud_weapon.c's klwd_names word for word (CERTAIN:
# they are the HUD's wording); 'TYPE 88 MG' is a GUESS (the HUD has no picture / name for item 40). The 'Police reg.' numbers and the
# origin lines are INVENTED flavour in the shop's own manner (GUESS, not game data). '%s' = the carrier row's own name (ROWS), because
# the swapped row keeps that row's price, rank and lock.
SWAP_ITEMS = {
    33: ('TYPE 81', 'Police reg.: 2381-T081\nAssault rifle. Origin: Chinese. Plain, rugged and everywhere. Sold in the %s row: same price, same rank.'),
    40: ('TYPE 88 MG', 'Police reg.: 2388-T088\nLight machine gun. Origin: Chinese. Belt-fed and heavy. Sold in the %s row: same price, same rank.'),
    47: ('MINIMI', 'Police reg.: 5547-M249\nLight machine gun. Origin: Belgian. Lifted from an army depot. Sold in the %s row: same price, same rank.'),
    49: ('REM 700', 'Police reg.: 7700-R700\nSniper rifle. Origin: American. A hunting rifle with a long reach. Sold in the %s row: same price, same rank.'),
    50: ('RPG-7', 'Police reg.: 7007-R007\nRocket launcher. Origin: Russian. Not for the faint-hearted. Sold in the %s row: same price, same rank.'),
    52: ('HK69', 'Police reg.: 6969-H069\nGrenade launcher. Origin: German. One 40 mm grenade at a time. Sold in the %s row: same price, same rank.'),
}


def parse_swap(text, log=print):
    """'13:52,16:33' -> {row: item}; the same rules as klshop.c (row 0..35, item 1..63, one per row, at most 8)."""
    out = {}
    for part in (text or '').split(','):
        part = part.strip()
        if not part:
            continue
        try:
            r, it = (int(x) for x in part.split(':'))
        except ValueError:
            log('shop swap: %r is not row:item - ignored' % part); continue
        if not (0 <= r < 36 and 1 <= it < 64) or r in out or len(out) >= 8:
            log('shop swap: %r is out of range / a repeat of a row / past 8 pairs - ignored (the hook ignores it too)' % part); continue
        if it not in SWAP_ITEMS:
            log('shop swap: item %d has no name in SWAP_ITEMS - the hook would still hand it over, the shop would keep the carrier name' % it)
        out[r] = it
    return out


def read_swaps(path, default=None, log=print):
    """KLGuns.ini (or its folder) -> ({row: item}, source). The [Shop] Swap line of the file if it has one (empty = no swap on this map),
    else `default` (the text of KLHook.ini's [Shop] Swap): the order klshop.c uses."""
    if path and os.path.isdir(path):
        path = os.path.join(path, 'KLGuns.ini')
    if path and os.path.isfile(path):
        cp = configparser.RawConfigParser(strict=False)
        cp.optionxform = str
        try:
            cp.read(path, encoding='latin1')
            if cp.has_option('Shop', 'Swap'):
                return parse_swap(cp.get('Shop', 'Swap'), log), 'KLGuns.ini'
        except configparser.Error as e:
            log('shop swap: %s not read (%s)' % (path, e))
    return parse_swap(default, log), 'default'


# the Dog Days gun in a sentence ('Handles as the Zastava M85.'); a row not here uses its ROWS name
PLAIN = {8: 'M9 Beretta', 23: 'MAC-10', 27: 'Type 05', 29: 'Zastava M85', 30: 'FN SCAR', 31: 'AK-47'}


def read_looks(path, log=print):
    """KLGuns.ini (or the build folder holding it) -> {shop item: look label} for every gun built to show a look (Shown > 0).
    {} when there is no file or no such gun; a look label not in LOOKS is left out (logged)."""
    if path and os.path.isdir(path):
        path = os.path.join(path, 'KLGuns.ini')
    if not path or not os.path.isfile(path):
        return {}
    cp = configparser.RawConfigParser(strict=False)
    cp.optionxform = str
    try:
        cp.read(path, encoding='latin1')
        n = cp.getint('Guns', 'Count', fallback=0)
    except (configparser.Error, ValueError) as e:
        log('shop names: %s not read (%s) - no look names' % (path, e)); return {}
    out = {}
    for i in range(1, n + 1):
        sec = 'Gun.%d' % i
        if not cp.has_section(sec):
            continue
        try:
            item, shown = cp.getint(sec, 'Item'), cp.getint(sec, 'Shown', fallback=0)
        except ValueError:
            continue
        if shown <= 0:
            continue
        lab = cp.get(sec, 'Look%d' % shown, fallback='').strip()
        if lab in LOOKS:
            out[item] = lab
        else:
            log('shop names: %s [%s] shows look %d %r, which has no shop name here - left as the Dog Days gun' % (path, sec, shown, lab))
    return out


def _set_text(node, text):
    t, _x, _sid, _rest = L.fields(node)
    e = node.raw.index(b'\0')
    node.raw = text + node.raw[e:]


def _tidy(b):
    b = b.replace(b'\xe2\x80\x99', b"'").replace(b'\xe2\x80\x98', b"'")
    b = b'\n'.join(re.sub(rb'[ \t]+', b' ', line).strip(b' \t') for line in b.split(b'\n'))
    return b


def apply_loc(data, english=False, log=print, tag='', looks=None, swaps=None):
    """one .LOC member -> (new bytes, number of leaves changed). english: check the stock names first (a level whose shop rows read
    otherwise is left alone, logged), and the description of a row in `looks` ({item: look label}, read_looks) is the look's."""
    looks = looks or {}
    swaps = {r: i for r, i in (swaps or {}).items() if i in SWAP_ITEMS}
    kids = L.parse(data)
    if kids is None:
        return data, 0
    leaves = dict(L.leaves(kids))
    if english:
        have = [L.fields(leaves[KEY + str(r)])[0] if KEY + str(r) in leaves else None for r in range(36)]
        ok = lambda r, t: t in (STOCK_EN[r], ROWS[r][1]) or t in [v[0] for v in LOOKS.values()] or t in [v[0] for v in SWAP_ITEMS.values()]      # stock, or baked here before
        bad = [r for r in range(36) if have[r] is None or not ok(r, b' '.join(have[r].split()).decode('latin1'))]
        if bad:
            log('shop names %s: rows %s do not read as the stock shop (first: %r) - names left stock' % (tag, bad[:5], have[bad[0]]))
            return data, 0
    n = 0
    for r, (item, name) in enumerate(ROWS):
        lab = looks.get(item)
        k = leaves.get(KEY + str(r))
        if k is not None and k.flags & L.TEXT:
            shown = SWAP_ITEMS[swaps[r]][0] if r in swaps else LOOKS[lab][0] if lab else name      # a swap beats a look: the carrier's gun is not what is handed over
            if L.fields(k)[0] != shown.encode('latin1'):
                _set_text(k, shown.encode('latin1')); n += 1
        d = leaves.get(KEY + str(r) + 'Desc')
        if d is not None and d.flags & L.TEXT:
            t = L.fields(d)[0] or b''
            if r in swaps and english:
                t2 = (SWAP_ITEMS[swaps[r]][1] % name.title()).encode('latin1')
            else:
                t2 = (LOOKS[lab][1] % PLAIN.get(item, name)).encode('latin1') if lab and english else _tidy(t)
            if t2 != t:
                _set_text(d, t2); n += 1
    if not n:
        return data, 0
    out = L.build(kids)
    if len(out) > L.LOC_CAP and len(out) > len(data):          # names never grow a stock file past the game's buffer: keep it stock
        log('shop names %s: the .LOC would be %d bytes, over %d: names left stock' % (tag, len(out), L.LOC_CAP))
        return data, 0
    assert L.build(L.parse(out)) == out
    return out, n


def apply_level(files, log=print, guns=None, swaps=None):
    """every .LOC member of an open level (kl_hud.open_level's files) in place -> the names of the members changed.
    guns: the build's KLGuns.ini (or its folder): rows of a gun built to show a Dead Men look take the look's name (LOOKS)."""
    looks = read_looks(guns, log)
    locs = [m for m in files if m.lower().endswith('.loc')]
    en = [m for m in locs if m.lower().endswith('english.loc')]
    if not en:
        log('shop names: the level has no English .LOC - left stock'); return []
    _o, n_en = apply_loc(files[en[0]], True, log, en[0], looks, swaps)
    if not n_en:
        return []
    changed = []
    for m in locs:
        new, n = apply_loc(files[m], m == en[0], log, m, looks, swaps)
        if n:
            files[m] = new; changed.append(m)
    log('shop names: %d weapon names in the HUD\'s wording, descriptions tidied; %d .LOC member(s): %s' % (len(ROWS), len(changed), ', '.join(x.rsplit('/', 1)[-1] for x in changed)))
    if swaps:
        log('shop names: swapped rows named for the gun they hand over: %s' % ', '.join('row %d -> %s' % (r, SWAP_ITEMS[i][0]) for r, i in sorted(swaps.items()) if i in SWAP_ITEMS))
    if looks:
        log('shop names: Dead Men looks sold under their own names: %s' % ', '.join('%s as %s' % (dict(ROWS)[i] if i in dict(ROWS) else i, LOOKS[l][0]) for i, l in sorted(looks.items())))
    return changed


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'swaps':
        for r, i in sorted(parse_swap(sys.argv[2]).items()):
            print('row %2d %-16s -> item %2d %-10s  %s' % (r, ROWS[r][1], i, SWAP_ITEMS[i][0] if i in SWAP_ITEMS else '?', (SWAP_ITEMS[i][1].replace('\n', ' | ') % ROWS[r][1].title()) if i in SWAP_ITEMS else ''))
        raise SystemExit(0)
    if len(sys.argv) != 3 or sys.argv[1] != 'names':
        raise SystemExit(__doc__)
    lk = read_looks(sys.argv[2])
    if not lk:
        print('no gun of %s is built to show a look: the shop keeps the names of ROWS' % sys.argv[2])
    for r, (item, name) in enumerate(ROWS):
        if item in lk:
            print('row %2d item %2d  %-14s -> %-10s  %s' % (r, item, name, LOOKS[lk[item]][0], LOOKS[lk[item]][1].replace('\n', ' | ') % PLAIN.get(item, name)))
