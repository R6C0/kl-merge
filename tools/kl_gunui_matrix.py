#!/usr/bin/env python3
r"""
kl_gunui_matrix.py - which of the 21 Fragile Alliance maps show OUR gun shelf names / cards / HUD dial (2026-11-01, job T5; no crash involved).
READ ONLY: it opens each map's installed F0x_Main.zip and F0x_Main.bots.zip and the bench logs, and writes nothing into any game folder.

Per map folder under <Dog Days>\KLExpansion\Maps (DD01-DD10, the DM maps) and per archive (plain = Arcade, .bots = online) it reports
  * ROW TEXT  rows 13/16/32/35 of the English .LOC (AllLevels/Menu/Online/WeaponShop/Weapon<row>): 'baked' = it names the gun the map's swap
    line hands over (tools/kl_shop_swap.py: HK69 / TYPE 81 / REM 700 / MINIMI), 'stock' = the carrier's own name (TOQ Model 18 ...), else 'other'.
  * CARD      the two textures of the row's shop picture (FAStatus_WeaponBig#NN, FAStatus_WeaponNN) found like kl_shop_swap.find_ids:
    'stock' = both equal the stock pixels (md5 of mip 0, measured on the untouched Scenes\Locations\F02..F09 archives, the same in all eight),
    'baked' = both differ, 'mixed' = one of two. A fingerprint (first 6 hex of the md5 of the four big cards) tells bake generations apart.
  * DIAL      the level carries the HUD pictures 113 / 114 the weapon dial needs (tex:UserInterface/KLMerge_HUD_01#dab / #disc, kl_hud.py EXTRAS).
  * LOGS      bench logs <work>\build\klhook\solo\<TAG>\inst1|inst2\KLHook.log: the map (Maps\<MAP>\Loader_Sequence), 'shoptext: row N seen ... stock
    text 0|1', 'oswlog: ... OURS|STOCK|OURS (flipped ...)', 'shoppic: ... unbaked 1' (OnlineSwapPic fired). The dial is an ARCHIVE check only: no log
    line proves it drew ('now renders through the private vtable' is only the element's vtable wrap), so logs are not read for it.
    Logs older than BAKE_TIME on a rebaked map are listed as stale.
Then it says per map what is still needed ([Shop] OnlineSwapText=2, OnlineSwapPic, or a bake).

    python tools/kl_gunui_matrix.py                     print the table (markdown) and the needs
    python tools/kl_gunui_matrix.py --md out.md         also write the table to a file
    python tools/kl_gunui_matrix.py --maps DM07,DD10    only these maps
    python tools/kl_gunui_matrix.py --tags GUN*         bench tags to read (glob; default GUN*; --tags none = no logs)
    python tools/kl_gunui_matrix.py --game DIR --solo DIR --stock-zip F06_Main.zip   other places / one more stock reference
"""
import argparse, fnmatch, glob, hashlib, os, re, struct, sys, time, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
SOLO = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook\solo'
ROWS = (13, 16, 32, 35)
DEFAULT_SWAP = '13:52,16:33,32:49,35:47'          # tools/kl_shop_swap.py DEFAULT_SWAP = the hook's [Shop] Swap default
KEY = b'AllLevels/Menu/Online/WeaponShop/Weapon'
# measured 2026-11-01 (read only) on the untouched stock archives Scenes\Locations\F02..F09_Main.zip (identical in all eight): row -> (full md5 of
# the big card's mip 0 data, full md5 of the small card's mip 0 data); stock_hashes() measures the same from any untouched archive.
STOCK_CARD = {13: ('c8314f24952e934c5e3456cbbcd4709c', '8309e0b8b58481810ee2036c7363dd46'),
              16: ('00175f20cb726568f7ff948ff0b87439', '5d1cf7b288388c20ae864639da0a0077'),
              32: ('a0662e0131ee11f3a262dc7edbfab53e', 'b45f6032d17c2b5e44e86b5663a49a1c'),
              35: ('8c3fd35fa75d2ddbe97bfcc0cdfee49b', '129162b0a61d0e7e30e11f162307b432')}
# the gunui_1029 bake was installed on DM07 (F06) and DD10 (F07) at 2026-11-01 ~02:10 (re/open_work_log.md); a bench log older than that
# on these maps shows the UNBAKED state and is listed as stale, never mixed with the current status.
BAKE_TIME = {'DM07': time.mktime((2026, 11, 1, 2, 10, 0, 0, 0, -1)), 'DD10': time.mktime((2026, 11, 1, 2, 10, 0, 0, 0, -1))}
DIAL_NAMES = ('KLMerge_HUD_01#dab', 'KLMerge_HUD_01#disc')     # extras slot 113 / 114 (kl_hud.py EXTRAS_NEW)


def _loc():
    import kl_loc
    return kl_loc


def _hud_shop():
    import kl_hud_shop
    return kl_hud_shop


# ------------------------------------------------------------------ one archive
def row_texts(loc_bytes):
    """English .LOC bytes -> {row: name bytes or None} for ROWS"""
    L = _loc()
    kids = L.parse(loc_bytes)
    if kids is None:
        return {r: None for r in ROWS}
    lv = dict(L.leaves(kids))
    out = {}
    for r in ROWS:
        k = lv.get(KEY.decode() + str(r))
        out[r] = L.fields(k)[0] if k is not None else None
    return out


def text_state(raw, row, want_item):
    """-> ('baked'|'stock'|'other'|'missing', shown text). baked = the name of the gun swap_items hands over on this row."""
    HS = _hud_shop()
    if raw is None:
        return 'missing', ''
    t = ' '.join(raw.decode('latin1').split())
    if want_item in HS.SWAP_ITEMS and t == HS.SWAP_ITEMS[want_item][0]:
        return 'baked', t
    if t in HS.STOCK_EN or t == HS.ROWS[row][1]:
        return 'stock', t
    return 'other', t


def mip0_md5(tex_entry):
    import kl_gunpics as P
    inf = P.tex_info(tex_entry)
    n = struct.unpack_from('<I', tex_entry, inf['mip0'])[0]
    return hashlib.md5(bytes(tex_entry[inf['mip0'] + 4:inf['mip0'] + 4 + n])).hexdigest()


def card_state(big, small, row, stock=None):
    """big / small = md5 hex of mip 0 -> 'stock' | 'baked' | 'mixed' (stock = {row: (big prefix, small prefix)} + extra full md5 sets)"""
    ref = STOCK_CARD if stock is None else stock
    sb, ss = ref[row]
    ib = big.startswith(sb) if isinstance(sb, str) else big in sb
    is_ = small.startswith(ss) if isinstance(ss, str) else small in ss
    return 'stock' if ib and is_ else 'baked' if not ib and not is_ else 'mixed'


def dial_state(tex_names):
    """texture names of the level -> True when both dial pictures (113 / 114) are in it"""
    return all(any(n.endswith(d) for n in tex_names) for d in DIAL_NAMES)


def find_ids_default(z, stem, rows):
    import kl_shop_swap
    return kl_shop_swap.find_ids(z, stem, rows)


def analyse_zip(path, want, stock=None, ids_fn=None):
    """one level archive -> dict(text={row: (state, shown)}, card={row: (state, bigmd5[:6])}, dial=bool, family=str, err=str|None)
    want = {row: item} the swap line of the map. ids_fn(z, stem, rows) -> {row: (big id, small id)} (default: the scene method of kl_shop_swap)."""
    import kl_texmat as T
    res = dict(text={}, card={}, dial=None, family='', err=None)
    try:
        z = zipfile.ZipFile(path)
        names = z.namelist()
        en = [n for n in names if n.lower().endswith('english.loc')]
        raws = row_texts(z.read(en[0])) if en else {r: None for r in ROWS}
        for r in ROWS:
            res['text'][r] = text_state(raws[r], r, want.get(r)) if r in want else ('noswap', raws[r].decode('latin1') if raws[r] else '')
        prm = [n for n in names if n.endswith('.prm')]
        if not prm:
            res['err'] = 'no .prm member'
            return res
        stem = prm[0][:-4]
        tex = T.read_tex(z.read(stem + '.TEX'))
        res['dial'] = dial_state([x.name for x in tex.tex.values()])
        ids = (ids_fn or find_ids_default)(z, stem, list(ROWS))
        fam = hashlib.md5()
        for r in ROWS:
            b, s = ids[r]
            hb, hs = mip0_md5(tex.tex[b].entry), mip0_md5(tex.tex[s].entry)
            res['card'][r] = (card_state(hb, hs, r, stock), hb[:6])
            fam.update(hb.encode())
        res['family'] = fam.hexdigest()[:6]
    except (SystemExit, Exception) as e:                 # find_ids raises SystemExit on a picture it cannot find
        res['err'] = '%s: %s' % (type(e).__name__, e)
    return res


def stock_hashes(zip_paths, ids_fn=None):
    """stock reference from untouched archives: {row: (set of big md5, set of small md5)} (full digests)"""
    import kl_texmat as T
    out = {r: (set(), set()) for r in ROWS}
    for p in zip_paths:
        z = zipfile.ZipFile(p)
        stem = [n for n in z.namelist() if n.endswith('.prm')][0][:-4]
        tex = T.read_tex(z.read(stem + '.TEX'))
        ids = (ids_fn or find_ids_default)(z, stem, list(ROWS))
        for r in ROWS:
            out[r][0].add(mip0_md5(tex.tex[ids[r][0]].entry)); out[r][1].add(mip0_md5(tex.tex[ids[r][1]].entry))
    return out


# ------------------------------------------------------------------ the maps
def map_order(name):
    m = re.match(r'(DD|DM)(\d+)([A-Z]?)$', name)
    return (m.group(1) != 'DD', int(m.group(2)), m.group(3)) if m else (2, 0, name)


def find_maps(game, only=None):
    """-> [(map, folder, plain zip or None, bots zip or None)] in table order (DD01.. then DM01..)"""
    root = os.path.join(game, 'KLExpansion', 'Maps')
    out = []
    for m in sorted(os.listdir(root), key=map_order) if os.path.isdir(root) else []:
        d = os.path.join(root, m)
        if not os.path.isdir(d) or (only and m not in only):
            continue
        zs = sorted(f for f in os.listdir(d) if re.match(r'F\d+_Main(\.bots)?\.zip$', f))
        plain = next((os.path.join(d, f) for f in zs if '.bots' not in f), None)
        bots = next((os.path.join(d, f) for f in zs if '.bots' in f), None)
        if plain or bots:
            out.append((m, d, plain, bots))
    return out


def map_swap(folder):
    """the swap line of a map: KLGuns.ini [Shop] Swap beside the archive, else the hook's default -> {row: item}"""
    HS = _hud_shop()
    sw, _src = HS.read_swaps(os.path.join(folder, 'KLGuns.ini'), DEFAULT_SWAP, lambda s: None)
    return {r: i for r, i in sw.items() if r in ROWS}


# ------------------------------------------------------------------ the bench logs
RE_MAP = re.compile(r'Maps[\\/](\w+)[\\/]Loader_Sequ', re.I)
RE_TXT = re.compile(r'shoptext: row (\d+) seen: .*?stock text (\d)')
RE_OSW = re.compile(r'oswlog: map \S+ row (\d+) .*?: (OURS|STOCK)\b( \(flipped)?')   # 'OURS handed over' | 'STOCK handed over' | 'OURS (flipped after the first report, state 0x16)'
RE_PIC = re.compile(r'shoppic: element \S+ role \d+ row (\d+) -> pic row')


def scan_log(path):
    """one KLHook.log -> dict(map, text={row: set of 0/1}, osw={row: set of 'OURS'|'STOCK'|'FLIPPED'}, pic=set of rows, mtime)"""
    ev = dict(map=None, text={}, osw={}, pic=set(), mtime=os.path.getmtime(path))
    with open(path, 'rb') as f:
        for ln in f.read().decode('latin1').splitlines():
            if ev['map'] is None:
                m = RE_MAP.search(ln)
                if m:
                    ev['map'] = m.group(1).upper()
            m = RE_TXT.search(ln)
            if m:
                ev['text'].setdefault(int(m.group(1)), set()).add(int(m.group(2)))
                continue
            m = RE_OSW.search(ln)
            if m:
                ev['osw'].setdefault(int(m.group(1)), set()).add('FLIPPED' if m.group(3) else m.group(2))
                continue
            m = RE_PIC.search(ln)
            if m:
                ev['pic'].add(int(m.group(1)))
    return ev


def scan_tags(solo, pattern='GUN*'):
    """-> {MAP: [(tag, inst, evidence)]} for every tag folder matching the glob (inst1 = host seat, inst2 = join seat)"""
    out = {}
    if not solo or not os.path.isdir(solo) or pattern == 'none':
        return out
    for tag in sorted(os.listdir(solo), key=lambda t: (len(t), t)):
        if not fnmatch.fnmatch(tag, pattern):
            continue
        for inst in ('inst1', 'inst2'):
            p = os.path.join(solo, tag, inst, 'KLHook.log')
            if os.path.isfile(p):
                ev = scan_log(p)
                if ev['map']:
                    out.setdefault(ev['map'], []).append((tag, inst, ev))
    return out


def evidence_text(items, cutoff=None):
    """[(tag, inst, ev)] of one map -> short strings: one per current tag (the seats merged), then one line naming the stale tags.
    cutoff = time of the map's last bake: a log older than it (file mtime) is stale (pre-bake), not current status."""
    by = {}
    for tag, inst, ev in items:
        b = by.setdefault(tag, dict(text=set(), osw=set(), pic=set(), stale=bool(cutoff and ev['mtime'] < cutoff)))
        for r, s in ev['text'].items():
            b['text'].add('stock' if 1 in s else 'baked')
        for r, s in ev['osw'].items():
            b['osw'] |= s
        b['pic'] |= set(ev['pic'])
    out, stale = [], []
    for tag, b in by.items():
        if b['stale']:
            stale.append(tag)
            continue
        bits = []
        if b['text']:
            bits.append('shop text ' + ('stock (answered by OnlineSwapText=2)' if 'stock' in b['text'] else 'baked'))
        if b['osw']:
            bits.append('pool ' + ('STOCK at the first report, flipped to OURS' if 'FLIPPED' in b['osw'] else '/'.join(sorted(b['osw']))))
        if b['pic']:
            bits.append('OnlineSwapPic fired rows ' + ','.join(str(r) for r in sorted(b['pic'])))
        if bits:
            out.append('%s: %s' % (tag, ', '.join(bits)))
    if stale:
        out.append('STALE (before the bake, unbaked state, not current): ' + ', '.join(stale))
    return out


# ------------------------------------------------------------------ verdict and table
def verdict(plain, bots):
    """-> (list of needs, short status). The online seat reads the .bots archive, Arcade the plain one."""
    needs = []
    for label, a in (('Arcade (plain zip)', plain), ('online (.bots zip)', bots)):
        if a is None:
            needs.append('%s: archive missing' % label); continue
        if a['err']:
            needs.append('%s: not readable (%s)' % (label, a['err'])); continue
        tx = [r for r, (s, _t) in a['text'].items() if s in ('stock', 'other', 'missing')]
        cd = [r for r, (s, _f) in a['card'].items() if s != 'baked']
        if tx:
            needs.append('%s: rows %s text not baked -> bake, or [Shop] OnlineSwapText=2 (online only)' % (label, ','.join(map(str, tx))))
        if cd:
            needs.append('%s: rows %s card not baked -> bake, or [Shop] OnlineSwapPic=1 (look-alike card)' % (label, ','.join(map(str, cd))))
        if a['dial'] is False:
            needs.append('%s: no dial pictures 113/114 -> kl_hud.py --look deadmen' % label)
    return needs, ('OK' if not needs else 'NEEDS')


def fmt_text(a):
    if a is None:
        return '-'
    if a['err']:
        return 'ERR'
    sts = sorted({s for s, _t in a['text'].values()})
    return sts[0] if len(sts) == 1 else '/'.join(sts)


def fmt_card(a):
    if a is None:
        return '-'
    if a['err']:
        return 'ERR'
    sts = sorted({s for s, _f in a['card'].values()})
    return (sts[0] if len(sts) == 1 else '/'.join(sts)) + ' ' + a['family']


def fmt_dial(a):
    return '-' if a is None else 'ERR' if a['dial'] is None else 'dial' if a['dial'] else 'no dial'


def table(rows, logs):
    """rows = [(map, slot, plain analysis, bots analysis, swapline, needs)] -> markdown lines"""
    out = ['| # | map | slot | swap rows | text plain | text bots | card plain | card bots | hud plain | hud bots | bench evidence | status |',
           '|---|-----|------|-----------|------------|-----------|------------|-----------|-----------|----------|----------------|--------|']
    for i, (m, slot, p, b, sw, needs) in enumerate(rows, 1):
        ev = evidence_text(logs.get(m, []), BAKE_TIME.get(m))
        out.append('| %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (
            i, m, slot, ','.join('%d:%d' % x for x in sorted(sw.items())), fmt_text(p), fmt_text(b), fmt_card(p), fmt_card(b),
            fmt_dial(p), fmt_dial(b), '; '.join(ev) if ev else 'none', 'OK' if not needs else 'NEEDS'))
    return out


def run(game, solo, tags, only, stock_zips, log=print):
    maps = find_maps(game, only)
    stock = None
    if stock_zips:
        ref = stock_hashes(stock_zips)
        stock = {r: (ref[r][0], ref[r][1]) for r in ROWS}
    logs = scan_tags(solo, tags)
    rows = []
    for m, d, plain, bots in maps:
        sw = map_swap(d)
        slot = re.match(r'(F\d+)_Main', os.path.basename(plain or bots)).group(1)
        a = analyse_zip(plain, sw, stock) if plain else None
        b = analyse_zip(bots, sw, stock) if bots else None
        needs, _st = verdict(a, b)
        rows.append((m, slot, a, b, sw, needs))
        log('  %s %s %s' % (m, slot, 'ok' if not needs else 'needs: ' + ' | '.join(needs)))
    return rows, logs


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--game', default=GAME)
    ap.add_argument('--solo', default=SOLO)
    ap.add_argument('--tags', default='GUN*')
    ap.add_argument('--maps', default='')
    ap.add_argument('--md', default='')
    ap.add_argument('--stock-zip', action='append', default=[], help='extra untouched archive whose cards count as stock')
    a = ap.parse_args(argv)
    only = set(x.strip() for x in a.maps.split(',') if x.strip()) or None
    rows, logs = run(a.game, a.solo, a.tags, only, a.stock_zip)
    lines = table(rows, logs)
    print('\n'.join(lines))
    print()
    for m, slot, p, b, sw, needs in rows:
        if needs:
            print('%s (%s): %s' % (m, slot, ' | '.join(needs)))
    if a.md:
        with open(a.md, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
