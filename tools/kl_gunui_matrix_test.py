#!/usr/bin/env python3
"""kl_gunui_matrix_test.py - off-game self-test of kl_gunui_matrix.py (fixtures built here: a tiny archive with only a .LOC, fake logs). Exit 0 = all pass."""
import os, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_loc as L
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
    check('card stock', M.card_state(s[0] + 'aa', s[1] + 'bb', 13) == 'stock')
    check('card baked', M.card_state('111111', '222222', 13) == 'baked')
    check('card mixed', M.card_state(s[0] + 'aa', '222222', 13) == 'mixed')
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

        # scan_log / scan_tags
        solo = os.path.join(td, 'solo')
        for tag, lines in (
            ('GUN1', ['12:00:00.000 FindFirstFileA Maps\\DM02\\Loader_Sequence.x',
                      'shoptext: row 13 seen: HK69 stock text 0',
                      'oswlog: map f04\\f04_main.zip row 13 carrier 13 item 52: OURS handed over',
                      'hud: weapon: A now renders through the private vtable']),
            ('GUN2', ['Maps/DM07/Loader_Sequence',
                      'shoptext: row 16 seen: TOQ Model 18 stock text 1',
                      'oswlog: map f04\\f04_main.zip row 16 carrier 12 item 33: STOCK handed over',
                      'shoppic: element 5 role 2 row 16 -> pic row 7',
                      'hud: weapon: no dial pictures']),
            ('OTHER', ['Maps\\DM09\\Loader_Sequence'])):
            d = os.path.join(solo, tag, 'inst1')
            os.makedirs(d)
            with open(os.path.join(d, 'KLHook.log'), 'wb') as f:
                f.write('\n'.join(lines).encode())
        ev = M.scan_log(os.path.join(solo, 'GUN1', 'inst1', 'KLHook.log'))
        check('scan_log GUN1', ev['map'] == 'DM02' and ev['text'] == {13: {0}} and ev['osw'] == {13: {'OURS'}} and ev['dial'] == 'dial')
        ev2 = M.scan_log(os.path.join(solo, 'GUN2', 'inst1', 'KLHook.log'))
        check('scan_log GUN2', ev2['map'] == 'DM07' and ev2['pic'] == {16} and ev2['dial'] == 'no dial' and ev2['osw'] == {16: {'STOCK'}})
        tags = M.scan_tags(solo, 'GUN*')
        check('scan_tags glob', sorted(tags) == ['DM02', 'DM07'])
        check('scan_tags none', M.scan_tags(solo, 'none') == {})
        et = M.evidence_text(tags['DM07'])
        check('evidence_text', len(et) == 1 and 'OnlineSwapPic fired rows 16' in et[0] and 'stock' in et[0] and 'no dial' in et[0], et[0])

    # verdict
    good = dict(text={r: ('baked', 'x') for r in M.ROWS}, card={r: ('baked', 'ab') for r in M.ROWS}, dial=True, family='abc123', err=None)
    needs, st = M.verdict(good, good)
    check('verdict OK', st == 'OK' and not needs)
    bad = dict(good, text=dict(good['text'], **{'16': None}) if False else dict(good['text']), card=dict(good['card']), dial=False)
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
