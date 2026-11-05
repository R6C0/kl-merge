"""kl_shop_buttons_test.py - offline self-test of tools/kl_shop_buttons.py on a synthetic online.xml (no game files needed)."""
import hashlib, os, sys, tempfile, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_shop_buttons as k

XML = ('<Window Name="HeistStatus" X="1">\r\n  <Platform PC_GC="True">\r\n\t<GuiElement Type="GUIGroup" Template="BottomFrameButtons">\r\n'
       '\t  <GuiElement Type="GUIGroup" W="151" H="40" X="873" Y="0">\r\n\t  </GuiElement>\r\n\t  <GuiElement Type="GUIGroup" W="151" H="40" X="655" Y="0">\r\n'
       '\t\t<GuiElement Template="BuyWeaponsButton_PC" Type="SendMessage" />\r\n\t  </GuiElement>\r\n\t</GuiElement>\r\n  </Platform>\r\n'
       '  <Platform PC_KEYBOARD="True">\r\n    <GuiElement Template="BuyWeaponsButton_PC" AlignH="Right" Message="ZW_SELECT3" TakeFocus="False" />\r\n    <GuiElement Type="SendMessage" />\r\n  </Platform>\r\n</Window>\r\n'
       '<Window Name="Other">\r\n <GuiElement Template="BuyWeaponsButton_PC" AlignH="Right" TakeFocus="False" />\r\n</Window>\r\n')


def _zip(path, xml, extra=b'x' * 5000):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('Menu/online.xml', xml)
        z.writestr('A.prm', extra)


def _md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def _tree(root):
    return {os.path.relpath(os.path.join(d, f), root): _md5(os.path.join(d, f)) for d, _s, fs in os.walk(root) for f in fs}


def sibling_test():
    """a fake Dog Days folder: one stock map (no sibling), DM11B-like (sibling + base.md5 + Int16Ok), one more with a sibling whose md5 had drifted"""
    x = XML.encode('latin-1')
    with tempfile.TemporaryDirectory() as dd:
        sc = os.path.join(dd, 'Scenes', 'Locations', 'F01'); os.makedirs(sc)
        _zip(os.path.join(sc, 'F01_Main.zip'), x)
        for nm, drift in (('DM11B', False), ('DM01', True)):
            d = os.path.join(dd, 'KLExpansion', 'Maps', nm); os.makedirs(d)
            plain, bots = os.path.join(d, 'F04_Main.zip'), os.path.join(d, 'F04_Main.bots.zip')
            _zip(plain, x); _zip(bots, x, b'y' * 4000)
            open(os.path.join(d, 'F04_Main.bots.base.md5'), 'w').write(('0' * 32 if drift else _md5(plain)) + '\n')
            if nm == 'DM11B':
                open(os.path.join(d, 'Int16Ok.txt'), 'w').write('zip=%d\nbots=%d\nshift=-12288,0,-16384 md5=e831\n' % (os.path.getsize(plain), os.path.getsize(bots)))
        orig = _tree(dd)
        args = ['--root', dd, '--skip-run-check']
        assert k.main(['install'] + args) == 0
        t1 = _tree(dd)
        for nm in ('DM11B', 'DM01'):
            d = os.path.join(dd, 'KLExpansion', 'Maps', nm)
            for f in ('F04_Main.zip', 'F04_Main.bots.zip'):
                with zipfile.ZipFile(os.path.join(d, f)) as z:
                    assert b'[F2] More guns' in z.read('Menu/online.xml'), (nm, f)
                assert os.path.exists(os.path.join(d, f + k.BAK))
        d = os.path.join(dd, 'KLExpansion', 'Maps', 'DM11B')
        assert open(os.path.join(d, 'F04_Main.bots.base.md5')).read().strip() == _md5(os.path.join(d, 'F04_Main.zip'))
        assert os.path.exists(os.path.join(d, 'F04_Main.bots.base.md5' + k.BAK)) and os.path.exists(os.path.join(d, 'Int16Ok.txt' + k.BAK))
        i16 = open(os.path.join(d, 'Int16Ok.txt')).read()
        assert i16.startswith('zip=%d\nbots=%d\nshift=-12288' % (os.path.getsize(os.path.join(d, 'F04_Main.zip')), os.path.getsize(os.path.join(d, 'F04_Main.bots.zip')))), i16
        assert open(os.path.join(dd, 'KLExpansion', 'Maps', 'DM01', 'F04_Main.bots.base.md5')).read().strip() == '0' * 32      # drifted before: stays flagged
        assert not os.path.exists(os.path.join(sc, 'F01_Main.bots.zip'))
        assert k.main(['install'] + args) == 0 and _tree(dd) == t1                                  # idempotent: nothing changes
        assert k.main(['undo'] + args) == 0
        assert not [f for f in _tree(dd) if f.endswith(k.BAK)], 'a backup was left behind'
        assert _tree(dd) == orig
        # a failure mid-map (the sibling has no online.xml) restores the whole map
        with zipfile.ZipFile(os.path.join(d, 'F04_Main.bots.zip'), 'w') as z:
            z.writestr('A.prm', b'z')
        orig2 = _tree(dd)
        assert k.main(['install', '--maps', 'DM11B'] + args) == 1 and _tree(dd) == orig2, 'a failed map was not restored'
        assert k.main(['install', '--maps', 'F01'] + args) == 0                                      # the stock map is untouched by the other's failure


def main():
    x = XML.encode('latin-1')
    new, rep = k.bake(x, 'F2', 'F3')
    t = new.decode('latin-1')
    assert t.count('[F2] More guns') == 2 and t.count('[F3] Heisters') == 2, t           # one keyboard + one PC_GC pair, 'Other' untouched
    assert 'X="437"' in t and 'X="219"' in t
    assert t.split('<Window Name="Other">')[1] == XML.split('<Window Name="Other">')[1]
    assert '\n' not in t.replace('\r\n', '')                                              # line endings kept
    assert k.bake(new)[0] == new and k.bake(new)[1] == ['already baked']                  # idempotent
    new2, _ = k.bake(x, 'F5', 'F6'); assert b'[F5] More guns' in new2 and b'[F6] Heisters' in new2
    try:
        k.bake(b'<Window Name="X"></Window>'); assert False
    except ValueError:
        pass
    sibling_test()
    print('kl_shop_buttons_test: PASS')


if __name__ == '__main__':
    main()
