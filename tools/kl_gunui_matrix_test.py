#!/usr/bin/env python3
"""kl_gunui_matrix_test.py - off-game self-test of kl_gunui_matrix.py (fixtures built here: tiny archives with a .LOC, a .prm and a Dog Days .TEX
written by kl_texmat.write_tex; fake logs made of lines copied from real KLHook.log files). Exit 0 = all pass."""
import hashlib, os, struct, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loc as L
import kl_texmat as T
import kl_gunui_matrix as M

FAILS = []


def check(name, cond, extra=''):
    if not cond:
        FAILS.append(name)
    print('%s %s %s' % ('ok  ' if cond else 'FAIL', name, extra))


def loc_bytes(names):
    leaves = [L.leaf(('Weapon%d' % r).encode(), t.encode(), 0) for r, t in sorted(names.items())]
    tree = L.Node(b'AllLevels', L.TABLE, [L.Node(b'Menu', L.TABLE, [L.Node(b'Online', L.TABLE, [L.Node(b'WeaponShop', L.TABLE, leaves)])])])
    return L.build([tree])


def tex_entry(idx, name, data):
    """a .TEX record as kl_gunpics.tex_info reads it: +0 size, +4 fourcc, +12 id, +16 w,h, +20 mips, +24 flags, +36 name, then mip 0 (u32 size + data)"""
    e = bytearray(36) + name.encode() + b'\0' + struct.pack('<I', len(data)) + data
    struct.pack_into('<I', e, 0, len(e)); e[4:8] = b'DXT5'[::-1]; struct.pack_into('<I', e, 12, idx)
    struct.pack_into('<HH', e, 16, 4, 4); struct.pack_into('<II', e, 20, 1, 0)
    return bytes(e)


IDS = {13: (1, 2), 16: (3, 4), 32: (5, 6), 35: (7, 8)}          # row -> (big id, small id) of the fixtures


def make_zip(path, datas, dial, loc):
    t = T.Tex('dd')
    for r, (b, s) in IDS.items():
        t.tex[b] = T.Texture(tex_entry(b, 'FAStatus_WeaponBig#%02d' % r, datas[r][0]))
        t.tex[s] = T.Texture(tex_entry(s, 'FAStatus_Weapon%02d#1' % r, datas[r][1]))
    if dial:
        t.tex[20] = T.Texture(tex_entry(20, 'UserInterface/KLMerge_HUD_01#dab', b'd1'))
        t.tex[21] = T.Texture(tex_entry(21, 'UserInterface/KLMerge_HUD_01#disc', b'd2'))
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('English.LOC', loc)
        z.writestr('F02_Main.prm', b'x')
        z.writestr('F02_Main.TEX', T.write_tex(t))
    return path


def fake_ids(z, stem, rows):
    return IDS


def main():
    # row_texts / text_state
    raw = loc_bytes({13: 'HK69', 16: 'TOQ Model 18', 32: 'Weird', 35: 'MINIMI'})
    rt = M.row_texts(raw)
    check('row_texts reads four rows', rt[13] == b'HK69' and rt[16] == b'TOQ Model 18' and rt[32] == b'Weird')
    check('text baked', M.text_state(rt[13], 13, 52)[0] == 'baked')
    check('text stock', M.text_state(rt[16], 16, 33)[0] == 'stock')
    check('text other', M.text_state(rt[32], 32, 49)[0] == 'other')
    check('text missing', M.text_state(None, 13, 52)[0] == 'missing')
    check('row_texts on a stub', M.row_texts(b'\0') is not None)

    # card_state: prefix strings and full-digest sets
    s = M.STOCK_CARD[13]
    check('STOCK_CARD holds full 32-hex digests', all(len(x) == 32 for v in M.STOCK_CARD.values() for x in v))
    check('card stock', M.card_state(s[0], s[1], 13) == 'stock')
    check('card baked', M.card_state('1' * 32, '2' * 32, 13) == 'baked')
    check('card mixed', M.card_state(s[0], '2' * 32, 13) == 'mixed')
    ref = {13: ({'x1'}, {'y1'})}
    check('card stock via sets', M.card_state('x1', 'y1', 13, ref) == 'stock' and M.card_state('x2', 'y1', 13, ref) == 'mixed')

    # dial_state
    check('dial both', M.dial_state(['UserInterface/KLMerge_HUD_01#dab', 'UserInterface/KLMerge_HUD_01#disc', 'z']))
    check('dial one missing', not M.dial_state(['UserInterface/KLMerge_HUD_01#dab']))

    # map_order
    check('map order', sorted(['DM01B', 'DM01', 'DD10', 'DD02', 'DM11B'], key=M.map_order) == ['DD02', 'DD10', 'DM01', 'DM01B', 'DM11B'])

    with tempfile.TemporaryDirectory() as td:
        # archive with a LOC but no .prm: text analysed, then err
        zp = os.path.join(td, 'F04_Main.zip')
        with zipfile.ZipFile(zp, 'w') as z:
            z.writestr('English.LOC', raw)
        a = M.analyse_zip(zp, {13: 52, 16: 33}, None)
        check('analyse: text states', a['text'][13][0] == 'baked' and a['text'][16][0] == 'stock' and a['text'][32][0] == 'noswap')
        check('analyse: no prm is an error', a['err'] == 'no .prm member')
        a2 = M.analyse_zip(os.path.join(td, 'absent.zip'), {}, None)
        check('analyse: unreadable archive reports err', bool(a2['err']))

        # archives with a .prm and a .TEX: stock pixels, baked pixels, a half-baked card, with and without the dial pictures
        stock = {r: (hashlib.md5(b'big%d' % r).hexdigest(), hashlib.md5(b'small%d' % r).hexdigest()) for r in M.ROWS}
        sdat = {r: (b'big%d' % r, b'small%d' % r) for r in M.ROWS}
        bdat = {r: (b'BAKEDbig%d' % r, b'BAKEDsmall%d' % r) for r in M.ROWS}
        hdat = dict(sdat); hdat[32] = (b'BAKEDbig32', sdat[32][1])
        wl = {13: 52, 16: 33, 32: 49, 35: 47}
        loc_ok = loc_bytes({13: 'HK69', 16: 'TYPE 81', 32: 'REM 700', 35: 'MINIMI'})
        zs = make_zip(os.path.join(td, 'stock_F02.zip'), sdat, False, raw)
        zb = make_zip(os.path.join(td, 'baked_F02.zip'), bdat, True, loc_ok)
        zh = make_zip(os.path.join(td, 'half_F02.zip'), hdat, True, loc_ok)
        e0 = T.read_tex(T.write_tex(T.Tex('dd', {1: T.Texture(tex_entry(1, 'n', b'abc'))}))).tex[1].entry
        check('mip0_md5 hashes the mip 0 data only', M.mip0_md5(e0) == hashlib.md5(b'abc').hexdigest())
        sh = M.stock_hashes([zs], fake_ids)
        check('stock_hashes from an archive', sh[13] == ({stock[13][0]}, {stock[13][1]}) and sh[35] == ({stock[35][0]}, {stock[35][1]}))
        a = M.analyse_zip(zs, wl, stock, fake_ids)
        check('analyse stock archive: text stock, cards stock, no dial',
              a['err'] is None and all(c[0] == 'stock' for c in a['card'].values()) and a['dial'] is False and a['text'][16][0] == 'stock' and a['text'][32][0] == 'other', str(a))
        a = M.analyse_zip(zb, wl, stock, fake_ids)
        check('analyse baked archive: text, cards baked, dial, 6-hex family',
              a['err'] is None and all(c[0] == 'baked' for c in a['card'].values()) and all(t[0] == 'baked' for t in a['text'].values())
              and a['dial'] is True and len(a['family']) == 6, str(a))
        check('analyse: bake generations differ in the family', a['family'] != M.analyse_zip(zs, wl, stock, fake_ids)['family'])
        check('analyse half-baked card is mixed', M.analyse_zip(zh, wl, stock, fake_ids)['card'][32][0] == 'mixed')
        a = M.analyse_zip(zb, wl, None, fake_ids)
        check('analyse with the built-in STOCK_CARD: other pixels count as baked', all(c[0] == 'baked' for c in a['card'].values()))
        nd, st = M.verdict(M.analyse_zip(zb, wl, stock, fake_ids), M.analyse_zip(zs, wl, stock, fake_ids))
        check('verdict from analysed archives names text, card, dial',
              st == 'NEEDS' and any('OnlineSwapText=2' in n for n in nd) and any('OnlineSwapPic=1' in n for n in nd) and any('113/114' in n for n in nd), str(nd))
        nd, st = M.verdict(M.analyse_zip(zb, wl, stock, fake_ids), M.analyse_zip(zb, wl, stock, fake_ids))
        check('verdict OK from analysed archives', st == 'OK' and not nd)

        # find_maps
        root = os.path.join(td, 'KLExpansion', 'Maps')
        for m in ('DM01', 'DD10', 'DD02'):
            os.makedirs(os.path.join(root, m))
        for m, f in (('DM01', 'F04_Main.zip'), ('DM01', 'F04_Main.bots.zip'), ('DD10', 'F10_Main.zip'), ('DD02', 'F02_Main.bots.zip')):
            open(os.path.join(root, m, f), 'wb').close()
        fm = M.find_maps(td)
        check('find_maps order', [x[0] for x in fm] == ['DD02', 'DD10', 'DM01'])
        check('find_maps plain/bots', fm[2][2].endswith('F04_Main.zip') and fm[2][3].endswith('.bots.zip') and fm[0][2] is None)
        check('find_maps filter', [x[0] for x in M.find_maps(td, {'DD10'})] == ['DD10'])
        check('map_swap default', M.map_swap(os.path.join(root, 'DM01')) == {13: 52, 16: 33, 32: 49, 35: 47})

        # scan_log / scan_tags; every line is copied from a real KLHook.log (solo GUN5 inst2, GUN12b inst1)
        solo = os.path.join(td, 'solo')
        pre = 'C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\'
        for tag, lines in (
            ('GUN1', ['22:43:55.662 expansion: FindFirstFileA NOT in the map folder, stock file used: ' + pre + 'SCENES\\Locations\\F02\\Loader_Sequence.zip -> '
                      + pre + 'KLExpansion\\Maps\\DM02\\Loader_Sequence.zip',
                      '04:04:28.173 shoptext: row 13 seen: pool state 2 (item 52), stock text 1, text now \'TOQ Model 18\' (mode 2, online 1)',
                      '22:44:04.826 oswlog: map f02\\f02_main.zip row 13 carrier 13 item 52: STOCK handed over',
                      '22:44:05.609 oswlog: map f02\\f02_main.zip row 13 carrier 13 item 52: OURS (flipped after the first report, state 0x16)',
                      '22:44:04.988 oswlog: map f02\\f02_main.zip row 16 carrier 12 item 33: OURS handed over']),
            ('GUN2', ['04:01:20.390 expansion: FindFirstFileA NOT in the map folder, stock file used: ' + pre + 'SCENES\\Locations\\F06\\Loader_Sequence.zip -> '
                      + pre + 'KLExpansion\\Maps\\DM07\\Loader_Sequence.zip',
                      '04:04:28.173 shoptext: row 13 seen: pool state 2 (item 52), stock text 0, text now \'HK69\' (mode 2, online 1)',
                      '04:04:29.093 shoppic: element 30feda90 role 11 row 13 -> pic row 14 (item 52, mode 2, unbaked 1, online 1, index 0)',
                      '22:44:04.826 oswlog: map f02\\f02_main.zip row 16 carrier 12 item 33: STOCK handed over']),
            ('OTHER', ['expansion: x Maps\\DM09\\Loader_Sequence.zip'])):
            d = os.path.join(solo, tag, 'inst1')
            os.makedirs(d)
            with open(os.path.join(d, 'KLHook.log'), 'wb') as f:
                f.write('\n'.join(lines).encode())
        ev = M.scan_log(os.path.join(solo, 'GUN1', 'inst1', 'KLHook.log'))
        check('scan_log GUN1: the flipped OURS line is read (not dropped)',
              ev['map'] == 'DM02' and ev['text'] == {13: {1}} and ev['osw'] == {13: {'STOCK', 'FLIPPED'}, 16: {'OURS'}}, str(ev['osw']))
        ev2 = M.scan_log(os.path.join(solo, 'GUN2', 'inst1', 'KLHook.log'))
        check('scan_log GUN2', ev2['map'] == 'DM07' and ev2['text'] == {13: {0}} and ev2['pic'] == {13} and ev2['osw'] == {16: {'STOCK'}}, str(ev2['pic']))
        check('scan_log has no dial field (archive check only)', 'dial' not in ev2)
        check('RE_OSW on the real flipped line', M.RE_OSW.search(
            'oswlog: map f02\\f02_main.zip row 32 carrier 36 item 49: OURS (flipped after the first report, state 0x16)').groups() == ('32', 'OURS', ' (flipped'))
        check('RE_OSW on the real handed-over lines', M.RE_OSW.search('oswlog: map f02\\f02_main.zip row 35 carrier 39 item 47: STOCK handed over').groups() == ('35', 'STOCK', None)
              and M.RE_OSW.search('oswlog: map f02\\f02_main.zip row 35 carrier 39 item 47: OURS handed over').group(2) == 'OURS')
        check('RE_TXT on a real line', M.RE_TXT.search(
            'shoptext: row 13 seen: pool state 2 (item 52), stock text 1, text now \'TOQ Model 18\' (mode 2, online 1)').groups() == ('13', '1'))
        check('RE_PIC on a real line', M.RE_PIC.search(
            'shoppic: element 30feda90 role 11 row 13 -> pic row 14 (item 52, mode 2, unbaked 1, online 1, index 0)').group(1) == '13')
        tags = M.scan_tags(solo, 'GUN*')
        check('scan_tags glob', sorted(tags) == ['DM02', 'DM07'])
        check('scan_tags none', M.scan_tags(solo, 'none') == {})
        et = M.evidence_text(tags['DM07'])
        check('evidence_text', len(et) == 1 and 'OnlineSwapPic fired rows 13' in et[0] and 'shop text baked' in et[0] and 'pool STOCK' in et[0] and 'dial' not in et[0], et[0])
        et2 = M.evidence_text(tags['DM02'])
        check('evidence_text: a flipped OURS is not shown as STOCK', len(et2) == 1 and 'STOCK at the first report, flipped to OURS' in et2[0], et2[0])
        mt = tags['DM07'][0][2]['mtime']
        etc = M.evidence_text(tags['DM07'], mt + 100)
        check('evidence_text: a pre-bake log is stale, its numbers not mixed in',
              len(etc) == 1 and etc[0].startswith('STALE') and 'GUN2' in etc[0] and 'OnlineSwapPic' not in etc[0], str(etc))
        etn = M.evidence_text(tags['DM07'], mt - 100)
        check('evidence_text: a post-bake log is current', len(etn) == 1 and not etn[0].startswith('STALE'))
        check('BAKE_TIME names the two maps rebaked 1029', set(M.BAKE_TIME) == {'DM07', 'DD10'})

    # verdict
    good = dict(text={r: ('baked', 'x') for r in M.ROWS}, card={r: ('baked', 'ab') for r in M.ROWS}, dial=True, family='abc123', err=None)
    needs, st = M.verdict(good, good)
    check('verdict OK', st == 'OK' and not needs)
    bad = dict(good, text=dict(good['text']), card=dict(good['card']), dial=False)
    bad['text'][16] = ('stock', 'TOQ Model 18')
    bad['card'][32] = ('mixed', 'ab')
    needs, st = M.verdict(good, bad)
    check('verdict NEEDS names text, card, dial',
          st == 'NEEDS' and any('OnlineSwapText=2' in n for n in needs) and any('OnlineSwapPic=1' in n for n in needs) and any('113/114' in n for n in needs), str(needs))
    needs, st = M.verdict(None, dict(good, err='boom'))
    check('verdict missing / unreadable archive', st == 'NEEDS' and len(needs) == 2)

    # table
    rows = [('DD02', 'F02', good, good, {13: 52}, []), ('DM07', 'F04', good, bad, {13: 52, 16: 33}, ['x'])]
    lines = M.table(rows, {})
    check('table shape', len(lines) == 4 and lines[2].count('|') == lines[0].count('|') and lines[2].endswith('| OK |') and lines[3].endswith('| NEEDS |'), lines[3])

    print('RESULT: %s' % ('all pass' if not FAILS else 'FAIL ' + ', '.join(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
