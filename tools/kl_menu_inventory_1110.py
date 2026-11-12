"""kl_menu_inventory_1110.py - READ-ONLY inventory of the menu XML (track T9, 2026-11-10, local partner).

Dumps every <Window> and <GuiElement> of a menu XML file with the attributes the cloud's layout tool needs:
window, nesting, name, Type, X Y W H, AlignH / AlignV, Priority, Font, ColorSet, Text key / literal, picture refs.
Values are EFFECTIVE: an attribute the element does not carry itself is taken from its Template chain (marked with
a trailing '~'). GUESS (not read from the exe): the game resolves Template="" exactly as 'template attributes first,
the element's own on top'; duplicate template names (Platform-specific copies) resolve to the LAST definition in file order.

    python tools\\kl_menu_inventory_1110.py dump <zip-or-xml> <member> <out.md> [--title T]
    python tools\\kl_menu_inventory_1110.py diff <zip-or-xml> <member> <zip-or-xml> <member>
    python tools\\kl_menu_inventory_1110.py summary <zip-or-xml> <member>

Never opens a game file for writing. Uses kl_hud_menu.tags (the game-style lenient tag reader).
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_hud_menu as H  # noqa: E402

CONTAINERS = ('Platform', 'ExcludeIn', 'Locale', 'GameRegion', 'BuildTag', 'MainIniOption')
COLS = ('X', 'Y', 'W', 'H', 'AlignH', 'AlignV', 'Priority', 'Font', 'ColorSet')


def load(path, member=None):
    if member and path.lower().endswith('.zip'):
        z = zipfile.ZipFile(path)
        names = {n.lower(): n for n in z.namelist()}
        data = z.read(names[member.lower()])
    else:
        data = open(path, 'rb').read()
    return data.decode('latin-1')


def parse(xml):
    """-> (windows, templates, stats). windows: list of dict(name, attrs, elements[]); element dict has own/eff/inh."""
    ts = H.tags(xml)
    templates, dupes = {}, 0
    for t in ts:
        if t.name == 'Template' and not t.close and not t.window:
            a = dict(t.attrs)
            n = a.get('Name')
            if n in templates:
                dupes += 1
            templates[n] = a
            # a tag with a DUPLICATE Name attribute (online.xml: Name="ScreenBaseSize" Name="ScreenBaseSize(SafeFrame)") is
            # registered under every value; which one the exe keeps is a GUESS (dict() alone kept only the last).
            for k, v in t.attrs:
                if k == 'Name' and v != n:
                    templates.setdefault(v, a)

    def effective(own):
        chain, seen, cur = [], set(), own.get('Template')
        while cur and cur in templates and cur not in seen:
            seen.add(cur)
            chain.append(templates[cur])
            cur = templates[cur].get('Template')
        eff, inh = {}, set()
        for tpl in reversed(chain):
            for k, v in tpl.items():
                if k not in ('Name', 'Template'):
                    eff[k] = v
                    inh.add(k)
        for k, v in own.items():
            eff[k] = v
            inh.discard(k)
        return eff, inh

    windows, win, stack, cond, outer = [], None, [], [], []
    for t in ts:
        a = dict(t.attrs)
        if t.name == 'Window':
            if t.close:
                win = None
                stack = []
                cond = []
            else:
                win = {'name': a.get('Name', '?'), 'attrs': a, 'elements': []}
                windows.append(win)
                stack, cond = [], list(outer)
            continue
        if win is None:
            if t.name in CONTAINERS:
                if t.close:
                    if outer:
                        outer.pop()
                elif not t.selfclose:
                    outer.append('%s[%s]' % (t.name, ','.join('%s=%s' % kv for kv in t.attrs)))
            elif t.name == 'Template' and not t.close and not t.selfclose and not t.window:
                # a template WITH a body (child GuiElements, instanced where it is used): listed as a pseudo-window
                win = {'name': 'Template:' + a.get('Name', '?'), 'attrs': a, 'elements': [], 'template': True}
                windows.append(win)
                stack, cond = [], list(outer)
            continue
        if t.name == 'Template' and t.close and win.get('template'):
            win = None
            continue
        if t.name == 'GuiElement':
            if t.close:
                if stack and stack[-1][0] == 'G':
                    stack.pop()
                continue
            depth = sum(1 for s in stack if s[0] == 'G')
            eff, inh = effective(a)
            parent = next((s[1] for s in reversed(stack) if s[0] == 'G'), None)
            el = {'idx': len(win['elements']), 'depth': depth, 'own': a, 'eff': eff, 'inh': inh,
                  'cond': ' '.join(cond), 'texts': [], 'gfx': [], 'parent': parent['idx'] if parent else None}
            win['elements'].append(el)
            if not t.selfclose:
                stack.append(('G', el))
            continue
        if t.name in CONTAINERS:
            if t.close:
                if stack and stack[-1][0] == 'C':
                    stack.pop()
                    cond.pop()
            elif not t.selfclose:
                stack.append(('C', 0))
                cond.append('%s[%s]' % (t.name, ','.join('%s=%s' % kv for kv in t.attrs)))
            continue
        if t.name in ('Text', 'Graphic') and not t.close:
            el = next((s[1] for s in reversed(stack) if s[0] == 'G'), None)
            if el is not None:
                (el['texts'] if t.name == 'Text' else el['gfx']).append(a.get('Text' if t.name == 'Text' else 'Graphic', ''))
            continue
    return windows, templates, {'template_defs': len(templates), 'template_dupes': dupes}


def cell(el, k):
    if k in el['own']:
        return el['own'][k]
    if k in el['eff']:
        return el['eff'][k] + '~'
    return ''


def esc(s):
    return s.replace('|', '\\|').replace('\n', ' ')


def render(windows, templates, stats, title):
    out = ['# %s' % title, '',
           'Generated by tools/kl_menu_inventory_1110.py (read-only). `~` after a value = inherited from the Template chain. '
           '`d` = GuiElement nesting depth; `par` = index of the parent element in the same window. `cond` = enclosing Platform/ExcludeIn/Locale/GameRegion tags. '
           '`pic` = Graphic= of the element plus child <Graphic> lists and FocusGraphic.', '',
           'windows %d, template bodies %d, elements %d (all sections), template definitions %d (duplicate names %d)' % (
               sum(1 for w in windows if not w.get('template')), sum(1 for w in windows if w.get('template')), sum(len(w['elements']) for w in windows), stats['template_defs'], stats['template_dupes']), '']
    for w in windows:
        wa = w['attrs']
        out.append('## %s `%s` (%d elements)' % ('Template body' if w.get('template') else 'Window', w['name'], len(w['elements'])))
        out.append('Window attrs: ' + ' '.join('%s=%s' % kv for kv in wa.items() if kv[0] != 'Name'))
        out.append('')
        out.append('| i | par | d | name | Type | Template | ' + ' | '.join(COLS) + ' | text | pic | cond |')
        out.append('|' + '---|' * (6 + len(COLS) + 3))
        for el in w['elements']:
            e = el['eff']
            text = e.get('Text', '') + ('~' if 'Text' in el['inh'] else '')
            if el['texts']:
                text += ' [' + ';'.join(el['texts'][:6]) + (';..%d' % len(el['texts']) if len(el['texts']) > 6 else '') + ']'
            pic = cell(el, 'Graphic')
            if el['gfx']:
                pic += ' [' + ';'.join(el['gfx'][:6]) + (';..%d' % len(el['gfx']) if len(el['gfx']) > 6 else '') + ']'
            if 'FocusGraphic' in e:
                pic += ' focus:' + e['FocusGraphic']
            out.append('| %d | %s | %d | %s | %s | %s | %s | %s | %s | %s |' % (
                el['idx'], '' if el['parent'] is None else el['parent'], el['depth'], esc(el['own'].get('Name', '')),
                esc(cell(el, 'Type')), esc(el['own'].get('Template', '')), ' | '.join(esc(cell(el, k)) for k in COLS),
                esc(text), esc(pic), esc(el['cond'])))
        out.append('')
    return '\n'.join(out) + '\n'


def summary(windows, templates, stats):
    types = {}
    for w in windows:
        for el in w['elements']:
            t = el['eff'].get('Type', '?')
            types[t] = types.get(t, 0) + 1
    return {'windows': sum(1 for w in windows if not w.get('template')), 'template_bodies': sum(1 for w in windows if w.get('template')), 'elements': sum(len(w['elements']) for w in windows), 'types': types, **stats}


def signature_of(windows):
    out = {}
    for w in windows:
        for el in w['elements']:
            out[(w['name'], el['idx'])] = (el['own'].get('Name', ''),) + tuple(el['eff'].get(k, '') for k in COLS + ('Type', 'Text', 'Graphic'))
    return out


def diff(wa, wb):
    a, b = signature_of(wa), signature_of(wb)
    return [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == 'dump':
        w, t, s = parse(load(argv[1], argv[2]))
        title = argv[argv.index('--title') + 1] if '--title' in argv else '%s %s' % (argv[1], argv[2])
        open(argv[3], 'w', encoding='utf-8', newline='\n').write(render(w, t, s, title))
        print(summary(w, t, s))
        return 0
    if cmd == 'summary':
        w, t, s = parse(load(argv[1], argv[2]))
        print(summary(w, t, s))
        return 0
    if cmd == 'diff':
        wa, _, _ = parse(load(argv[1], argv[2]))
        wb, _, _ = parse(load(argv[3], argv[4]))
        d = diff(wa, wb)
        for k, x, y in d[:200]:
            print(k, x, '->', y)
        print('%d differing elements' % len(d))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
