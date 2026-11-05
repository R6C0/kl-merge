"""kl_shop_buttons_test.py - offline self-test of tools/kl_shop_buttons.py on a synthetic online.xml (no game files needed)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_shop_buttons as k

XML = ('<Window Name="HeistStatus" X="1">\r\n  <Platform PC_GC="True">\r\n\t<GuiElement Type="GUIGroup" Template="BottomFrameButtons">\r\n'
       '\t  <GuiElement Type="GUIGroup" W="151" H="40" X="873" Y="0">\r\n\t  </GuiElement>\r\n\t  <GuiElement Type="GUIGroup" W="151" H="40" X="655" Y="0">\r\n'
       '\t\t<GuiElement Template="BuyWeaponsButton_PC" Type="SendMessage" />\r\n\t  </GuiElement>\r\n\t</GuiElement>\r\n  </Platform>\r\n'
       '  <Platform PC_KEYBOARD="True">\r\n    <GuiElement Template="BuyWeaponsButton_PC" AlignH="Right" Message="ZW_SELECT3" TakeFocus="False" />\r\n    <GuiElement Type="SendMessage" />\r\n  </Platform>\r\n</Window>\r\n'
       '<Window Name="Other">\r\n <GuiElement Template="BuyWeaponsButton_PC" AlignH="Right" TakeFocus="False" />\r\n</Window>\r\n')


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
    print('kl_shop_buttons_test: PASS')


if __name__ == '__main__':
    main()
