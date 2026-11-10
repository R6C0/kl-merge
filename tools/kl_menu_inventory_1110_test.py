"""Self-test of kl_menu_inventory_1110 on synthetic XML (no game files)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_menu_inventory_1110 as I  # noqa: E402

XML = '''<Windows>
<Template Name="Row" Type="TextBlock" Font="Text" ColorSet="Default" X="5" />
<Template Name="Row2" Template="Row" Y="9" />
<Template Name="ScreenBaseSize" AlignH="Center" W="768" H="576" />
<Window Name="A" Template="WindowDefault">
  <GuiElement Type="GUIGroup" Template="ScreenBaseSize" X="2">
    <Platform PC="True">
      <GuiElement Name="r1" Template="Row2" Text="/Menu/x" X="7"><Text Text="k1"/><Text Text="k2"/></GuiElement>
    </Platform>
    <GuiElement Type="Graphic" Graphic="Pic1" />
  </GuiElement>
</Window>
<Window Name="B"><GuiElement Name="z" Type="Graphic" Graphic="P2"/></Window>
</Windows>'''


def main():
    w, t, s = I.parse(XML)
    assert len(w) == 2 and [len(x['elements']) for x in w] == [3, 1], w
    g, r1, p = w[0]['elements']
    assert g['eff']['W'] == '768' and 'W' in g['inh']
    assert r1['eff']['Font'] == 'Text' and r1['eff']['Y'] == '9' and r1['eff']['X'] == '7' and 'X' not in r1['inh']
    assert r1['parent'] == 0 and r1['depth'] == 1 and r1['texts'] == ['k1', 'k2'] and 'Platform[PC=True]' in r1['cond']
    assert p['cond'] == '' and p['parent'] == 0
    assert I.cell(r1, 'Y') == '9~' and I.cell(r1, 'X') == '7'
    md = I.render(w, t, s, 'T')
    assert '## Window `A`' in md and 'windows 2, template bodies 0, elements 4' in md
    assert not I.diff(w, w)
    print('kl_menu_inventory_1110_test PASS')


if __name__ == '__main__':
    main()
