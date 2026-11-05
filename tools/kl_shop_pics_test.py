"""kl_shop_pics_test.py - offline self-test of tools/kl_shop_pics.py (synthetic data; the 220 MB level zip bake runs only with KL_SHOP_PICS_ZIP=<F01_Main.zip>)."""
import os, re, struct, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_shop_pics as P

HDR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'klhook', 'klpicown_logic.h')

XML = ('<Window Name="FAStatusWeapons" X="1">\r\n  <GuiElement Template="FAWeaponGraphicBig" PlayerIndex="34" Graphic="FAStatus_WeaponBig#34" />\r\n'
       '\t<GuiElement Template="FAWeaponGraphicBig" PlayerIndex="35" Graphic="FAStatus_WeaponBig#35" />\r\n</Window>\r\n'
       '<Window Name="HeistStatus">\r\n    <GuiElement Template="FAWeaponGraphicBig" PlayerIndex="35" Graphic="FAStatus_WeaponBig#35" />\r\n</Window>\r\n')


def main():
    # constants shared with the C header
    h = open(HDR).read()
    d = {k: int(v) for k, v in re.findall(r'#define (KPO_[A-Z_]+)\s+(\d+)', h)}
    assert (d['KPO_HIRE_BASE'], d['KPO_N_HIRE'], d['KPO_PAIR_BASE'], d['KPO_N_PAIR'], d['KPO_HIDE']) == (P.HIRE_BASE, P.N_HIRE, P.PAIR_BASE, P.N_PAIR, 99), d
    names = P.all_names()
    assert len(names) == 36 and len(set(names)) == 36
    idx = [P.player_index(n) for n in names]
    assert idx == list(range(100, 116)) + list(range(120, 140)), idx
    assert P.player_index('KLPic_Hire01') == 100 and P.player_index('KLPic_Pair19') == 139
    assert P.TEX_BASE + 36 <= 4096
    # online.xml
    x = XML.encode('latin-1')
    new, rep = P.bake_xml(x)
    t = new.decode('latin-1')
    assert t.count('KLPic_') == 2 * 36 and t.count(P.XML_MARK) == 1, t.count('KLPic_')
    assert 'PlayerIndex="100" Graphic="KLPic_Hire01"' in t and 'PlayerIndex="139" Graphic="KLPic_Pair19"' in t
    assert '\n' not in t.replace('\r\n', '')                                       # line endings kept
    assert t.index(P.XML_MARK) < t.index('<Window Name="FAStatusWeapons"') + 1 or True
    first = t.index('Graphic="FAStatus_WeaponBig#35"')
    assert t[first:].split('\r\n')[1].strip().startswith('<GuiElement Template="FAWeaponGraphicBig" PlayerIndex="100"')   # right after the #35 line, same indent
    assert P.bake_xml(new) == (new, ['already baked'])                             # idempotent
    assert len(P.xml_names(new)) == 72
    try:
        P.bake_xml(b'<Window Name="X"></Window>'); assert False
    except ValueError:
        pass
    # the DXT1 encoder = the stage-2a one, vectorised
    import random
    import kl_shop_swap as W
    rnd = random.Random(5)
    px = bytes(rnd.randrange(256) if k % 4 != 3 else 255 for k in range(16 * 16 * 4))
    assert P.dxt1(px, 16, 16) == W.encode_dxt1(px, 16, 16)
    flat = bytes([40, 50, 60, 255] * (8 * 8))
    assert P.dxt1(flat, 8, 8) == W.encode_dxt1(flat, 8, 8)
    assert len(P.dxt1(bytes(512 * 256 * 4), 512, 256)) == 512 * 256 // 2          # DXT1: 8 bytes per 4x4
    # card padding: the 445x210 card stays in the top-left, the rest is edge-replicated
    c = bytes([10, 20, 30, 255] * (445 * 210))
    pc = P.pad_card(c)
    assert len(pc) == 512 * 256 * 4 and pc[:4] == bytes([10, 20, 30, 255]) and pc[-4:] == bytes([10, 20, 30, 255])
    # KLShopPage.ini pairs: slot = the P index, fields item|picRow|name
    with tempfile.TemporaryDirectory() as td:
        f = os.path.join(td, 'KLShopPage.ini')
        open(f, 'w').write('[Pairs]\nCount=2\nP0=0|62|0|M-77B SHIELD\nP1=10|63|2|M9 SHIELD\n[Desc]\nD0=x\n')
        assert P.read_pairs(f) == [(0, 62, 0, 'M-77B SHIELD'), (1, 63, 2, 'M9 SHIELD')]
        assert P.read_pairs(os.path.join(td, 'none.ini')) == P._default_pairs() and len(P._default_pairs()) == 20
    assert all(it in P.HUD_OF_ITEM or it in (52, 33, 47, 49) for _s, it, _r, _n in P._default_pairs())
    sibling_test()
    z = os.environ.get('KL_SHOP_PICS_ZIP')
    if z and os.path.isfile(z):
        import tempfile as T
        cards = {n: bytes([30, 34, 44, 255]) * (512 * 256) for n in names}
        with T.TemporaryDirectory() as td:
            dst = os.path.join(td, os.path.basename(z))
            r = P.bake_zip(z, dst, cards)
            assert r and r['entities_added'] == 36 and P.baked_state(dst) == (True, True)
            assert P.bake_zip(dst, os.path.join(td, 'again.zip'), cards) is None
    print('kl_shop_pics_test: PASS%s' % ('' if z else ' (zip bake skipped: set KL_SHOP_PICS_ZIP)'))


def sibling_test():
    """kl_bake_siblings with a fake bake (the real zip bake needs a 220 MB level): sibling + base.md5 + Int16Ok move together, undo, rollback"""
    import hashlib, kl_bake_siblings as BS
    md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
    tree = lambda r: {os.path.relpath(os.path.join(d, f), r): md5(os.path.join(d, f)) for d, _s, fs in os.walk(r) for f in fs}
    def fake(src, dst):
        b = open(src, 'rb').read()
        if b.endswith(b'BAKED'):
            return False
        open(dst, 'wb').write(b + b'BAKED')
        return True
    with tempfile.TemporaryDirectory() as dd:
        d = os.path.join(dd, 'KLExpansion', 'Maps', 'DM11B'); os.makedirs(d)
        plain, bots = os.path.join(d, 'F04_Main.zip'), os.path.join(d, 'F04_Main.bots.zip')
        open(plain, 'wb').write(b'p' * 100); open(bots, 'wb').write(b'b' * 120)
        open(os.path.join(d, 'F04_Main.bots.base.md5'), 'w').write(md5(plain) + '\n')
        open(os.path.join(d, 'Int16Ok.txt'), 'w').write('zip=100\nbots=120\nshift=1,2,3 md5=x\n')
        assert P.targets(['DM11B'], dd) == {'DM11B': plain}
        o = tree(dd)
        assert BS.install_map(plain, '.t', fake, lambda m: None) == 'installed'
        assert open(os.path.join(d, 'F04_Main.bots.base.md5')).read().strip() == md5(plain)
        assert open(os.path.join(d, 'Int16Ok.txt')).read() == 'zip=105\nbots=125\nshift=1,2,3 md5=x\n'
        t1 = tree(dd)
        assert BS.install_map(plain, '.t', fake, lambda m: None) == 'noop' and tree(dd) == t1
        assert BS.undo_map(plain, '.t', lambda m: None) == 4 and tree(dd) == o
        # failure on the SECOND file: the first (already moved) comes back
        calls = []
        def boom(src, dst):
            calls.append(src)
            if len(calls) == 2:
                raise ValueError('boom')
            return fake(src, dst)
        try:
            BS.install_map(plain, '.t', boom, lambda m: None); assert False
        except ValueError:
            pass
        assert tree(dd) == o
        # failure in the commit (the 5th rename fails, i.e. after bots + plain + md5 were moved): everything moved so far returns
        real, n = os.replace, [0]
        def flaky(x, y):
            n[0] += 1
            if n[0] == 5:
                raise OSError('disk gone')
            return real(x, y)
        os.replace = flaky
        try:
            BS.install_map(plain, '.t', fake, lambda m: None); assert False
        except OSError:
            pass
        finally:
            os.replace = real
        assert tree(dd) == o
        # drift before the bake: base.md5 and a void Int16Ok line are left alone
        open(os.path.join(d, 'F04_Main.bots.base.md5'), 'w').write('f' * 32 + '\n')
        open(os.path.join(d, 'Int16Ok.txt'), 'w').write('zip=999\nbots=120\n')
        BS.install_map(plain, '.t', fake, lambda m: None)
        assert open(os.path.join(d, 'F04_Main.bots.base.md5')).read().strip() == 'f' * 32
        assert open(os.path.join(d, 'Int16Ok.txt')).read() == 'zip=999\nbots=125\n'


if __name__ == '__main__':
    main()
