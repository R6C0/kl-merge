"""kl_menu_count.py - how many entries a set of menu XML files puts into kl2.exe's element table.

    python tools/kl_menu_count.py frontend  <frontend.xml> <online.xml>  [--gamepad] [--locale English] [--region Europe]
    python tools/kl_menu_count.py level     <ingame.xml>   <online.xml>  [--arcade | --fa] [--difficulty N] ...
    python tools/kl_menu_count.py selftest  <dir with patch01_frontend.xml patch01_ingame.xml frontend_online.xml>
    python tools/kl_menu_count.py count     <any.xml> ...                (one file, no load-set context: --frontend / --level flags)

The table (ZMercsMenuElements, [[0xdd265c]+0x824], count at +0x9f48) holds 0x13e8 = 5096 {object, kind} pairs
and overflows into a bare int3 (0x7fad8d GuiElement, 0x667e6e Window); re/hud_menu.md 1.1 explains why the
usable budget is 5000. The live count was never read (that needs KLHook, hud_menu.md K0); this is the STATIC
model, written from kl2.exe on 2026-10-24 (ZGUIXMLReader2: start element 0x8ce850, end element 0x5dcf30,
read file 0x87e930, reader set-up 0x87e9e0; factories 0x4ecea0 / 0x579650 / 0x7fad10 / 0x667e00 / 0x47d5e0 /
0x53c720 / 0x686270; template instancing 0x403060). Every rule below was read in that code; the two things
it cannot know are marked GUESS.

What makes an entry (kind): <GuiElement Type=T> whose T a factory knows (0), <Window> (1, type "Standard"
when none is given), <ColorSet> (2), <ButtonGraphic> (3). Text / Graphic / GraphicElement children and
unknown tags go through 0x7b0fa0 and make no entry. <Template> makes NO entry: it takes one of the reader's
512 definition slots (0x686270: 0x5ac bytes each, counter reader+0x1e8, zeroed only in the reader's
constructor 0x51aa76 and the reader lives for one load set = both files; a 513th template returns NULL,
silently). Its child tags ARE created when the definition is parsed (they are ordinary tags under the
definition) - once. An element that names a Template WITH children (<GuiElement Template="X"> where X has
child tags) creates nothing itself: 0x403060 attaches X's already-made children to the enclosing object
(the same objects, no clones), and the reader pushes a null (0x8cee91..0x8ceed0). An element that names a
template without children is created from the merged attributes (0x5532b0; the element's own win).

Conditional blocks (a stack of include flags, reader+0x1d0 / +0x1d1.., depth +0x1e4):
- <Platform> and <BuildTag> share one rule (0x8cef26): included when attribute "PC" (exact case) is True, or
  - when no "PC" attribute is there - the attribute named after the ini BuildTag ("Default" when unset,
  case-insensitive) is True, or the attribute named PC_KEYBOARD (PC_GC when [manager+0xaf68], the gamepad
  flag) is True. XENON / PS3 are never looked at. So <Platform PC_GC="True" PS3="True"> is OUT on a keyboard.
- <ExcludeIn K="True" ...> is excluded when any named key's condition holds (the key's value must be the
  word True; False or anything else = not set). Keys and their tests, in the exe's order:
  FA: 0x863a60(session) && [session+0x5c] == 4; Arcade: 0x7f6850(session); Campaign: 0x7aca80(session);
  Demo: [[0xdd265c]+0x8ad]; HiddenDemo: that && +0x8ae; Normal: NOT +0x8ad (so Normal="True" blocks are
  out of the retail game); GameRelease: ALWAYS (a release exe); GermanSKU / NotGermanSKU and JapaneseSKU /
  NotJapaneseSKU: ini 0x793550 on [0xdd2640]; Extreme: [0x156b5f0] == 3; Hard: == 2; PreviewBuild: +0x8af;
  LifePreviewBuild: +0x8b0. Unknown keys (the XML writes "Preview") are ignored.
- <Locale> / <GameRegion>: included only when the attribute named after the current language (table
  0xcd8dcc: English German French Spanish Italian Dutch Russian Polish Japanese, index [0xdda79c]) /
  region (0xcd8df0: NorthAmerica Europe Asia Rest, index [0xcd8e00]) is True (case-insensitive).
- <MainIniOption Name=K Value=V>: included when atoi(ini K) == V (V default 1, a missing key reads 0).
Tags inside an excluded block are not created at all (0x8cee45 returns before any factory), and a block
nested in an excluded block stays excluded (every rule ANDs with the enclosing flag).

GUESS 1: 0x7a1ff0 (template lookup by name) is taken as exact-name, falling back to case-insensitive.
GUESS 2: the menu scene's own elements (the ZWIN* entities of the frontend .gms) are NOT in this table;
only XML-made objects are counted here. The K0 line settles both.
"""
import os, re, sys

TABLE = 0x13e8          # 5096
BUDGET = 5000           # re/hud_menu.md 1.1: entry 5000 is read by the DefaultFocus hover
TEMPLATE_SLOTS = 0x200  # reader+0x1e8 cap (0x686270)

LOCALES = ['English', 'German', 'French', 'Spanish', 'Italian', 'Dutch', 'Russian', 'Polish', 'Japanese']
REGIONS = ['NorthAmerica', 'Europe', 'Asia', 'Rest']

# Type names the two factories accept (ZMercsMenuFactory 0x859460: 146, ZStandardMenuFactory 0x5fa2d0: 18).
# Read from kl2.exe build 0490 (strings referenced by the strcmp chains). Window types: 0x667e00 asks the same
# factories through slot 1; the only type the stock XML gives a Window is none -> "Standard".
GUI_TYPES = set('''
ZGuiEdit ZGUIVirtualKeyboard ToggleText ToggleImages Slider SliderText CloseWindow OpenWindow OpenWindowTimer
QuitGame TextBlock Graphic Frame GUIList Animation GUIGroup Toggle SendMessage
MercsGraphic Credits MercsLeaderboard MercsShowInfo MercsShowAchievement MercsObjectivesInfo
MercsObjectivePlayerName MercsLevelSelector MercsLevelSelectorHeist MercsLevelIndicator
MercsLevelCompletedIndicator MercsElementToggler MercsServerBrowser MercsOptions MercsPushIndex
MercsMiscController MercsHeader MercsIndexPush SaveOptions OptionTimer ApplyOption MercsReloadCheckpointTimer
MercsFAToggleImages MercsFAPIP MercsFARules MercsFABuyWeapons MercsFAQuitLobby MercsFAStatusReady
MercsHeistHighscoreReady MercsFASelector MercsFASelectorLobby MercsFASelectorStatus MercsShowInfoFA
MercsShowInfoFAFocus MercsShowInfoFAGamestats MercsShowInfoFALobby MercsShowInfoFALobbyFocus
MercsShowInfoFAWeapons MercsSendMessageWeapons MercsShowInfoGameTips
'''.split())
_FACTORY_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 're', 'menu_factory_names.json')


def load_types():
    """The full 164-name list lives in re/menu_factory_names.json (written by the 2026-10-24 extraction);
    the inline set above is the subset quoted in re/menus.md and is enough for a smoke test."""
    try:
        import json
        d = json.load(open(_FACTORY_JSON))
        s = set()
        for v in d.values():
            s.update(v)
        return s
    except (OSError, ValueError):
        return GUI_TYPES


class Context:
    """Which conditional blocks are in. Defaults = retail PC, keyboard, English, Europe, frontend (no session)."""
    def __init__(self, **kw):
        self.gamepad = False          # [manager+0xaf68]
        self.buildtag = 'Default'     # ini BuildTag
        self.locale = 'English'
        self.region = 'Europe'
        self.fa = False               # 0x863a60 && session+0x5c == 4
        self.arcade = False           # 0x7f6850
        self.campaign = False         # 0x7aca80
        self.demo = False             # [0xdd265c]+0x8ad
        self.hidden_demo = False      # +0x8ae (with demo)
        self.german = False           # ini GermanSKU
        self.japanese = False         # ini JapaneseSKU
        self.difficulty = 0           # [0x156b5f0]: 2 = Hard, 3 = Extreme
        self.preview = False          # +0x8af
        self.life_preview = False     # +0x8b0
        self.ini = {}                 # MainIniOption store (the -o Key=Value store, ASSUMPTION in re/menus.md)
        for k, v in kw.items():
            if not hasattr(self, k):
                raise TypeError(k)
            setattr(self, k, v)

    def input_name(self):
        return 'PC_GC' if self.gamepad else 'PC_KEYBOARD'

    def exclude_in(self, key):
        """True when the ExcludeIn key's condition holds (so the block is excluded)."""
        return {
            'FA': self.fa, 'Arcade': self.arcade, 'Campaign': self.campaign, 'Demo': self.demo,
            'HiddenDemo': self.demo and self.hidden_demo, 'Normal': not self.demo, 'GameRelease': True,
            'GermanSKU': self.german, 'NotGermanSKU': not self.german, 'JapaneseSKU': self.japanese,
            'NotJapaneseSKU': not self.japanese, 'Extreme': self.difficulty == 3, 'Hard': self.difficulty == 2,
            'PreviewBuild': self.preview, 'LifePreviewBuild': self.life_preview,
        }.get(key, False)


def read_bool(attrs, name, ci=False):
    """0x86f6e0 / 0x612380: the attribute's value as True/False, or None when absent or another word."""
    for k, v in attrs:
        if (k.lower() == name.lower()) if ci else (k == name):
            if v.lower() == 'true':
                return True
            if v.lower() == 'false':
                return False
            return None
    return None


def attr(attrs, name):
    for k, v in attrs:
        if k == name:
            return v
    return None


def tokenize(data):
    """The game's own tokenizer, 0x7b9700 (ZGUIXMLReader2 read file 0x87e930 -> 0x79edf0 loop), as read in
    kl2.exe. Yields ('start', name, attrs, offset), ('end', name), and finally ('eof', ok, offset). The rules that
    differ from a real XML parser, and so from expat:
    - between tokens, bytes <= 0x20 and . - _ : are skipped (0x4b4be0); anything else that is not '<' ENDS
      the file (token 4 = error): stray text truncates the file silently, the elements made so far stay.
    - a comment '<!--' ends at the FIRST '-->' (a '<!--' inside is text; Patch01 frontend.xml:2656 nests one).
    - names and bare values are runs of isalnum . - _ (0x674120); a quoted value runs to the next '"', no
      escapes; attributes are kept in file order, a repeated name is found FIRST (0x612380); more than 50
      attribute pairs or a malformed one (no '=', no value) = token 4, the file ends there.
    - '<name .../>' is start + end (token 2); '</name>' is end (1); no entities, no CDATA, no '<?xml'
      (a '?' is no name character: such a first line would end the file at once)."""
    n = len(data); i = 0
    skip = set(range(0, 0x21)) | set(b'.-_:')
    namech = set(b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_')

    def token(i):
        """0x674120: a quoted string or a name run; returns (value or None, new i)."""
        if i < n and data[i:i + 1] == b'"':
            j = data.find(b'"', i + 1)
            if j < 0:
                return None, n
            return data[i + 1:j].decode('latin-1'), j + 1
        j = i
        while j < n and data[j] in namech:
            j += 1
        return (data[i:j].decode('latin-1') if j > i else None), j

    while True:
        while i < n and data[i] in skip:
            i += 1
        if i >= n:
            yield ('eof', True, i); return
        if data[i:i + 1] != b'<':
            yield ('eof', False, i); return
        if data[i:i + 4] == b'<!--':
            k = data.find(b'-->', i + 1)
            if k < 0:
                yield ('eof', False, i); return      # "Non-terminated": token 4
            i = k + 3; continue
        tag_at = i
        i += 1
        if data[i:i + 1] == b'/':
            name, i = token(i + 1)
            if data[i:i + 1] != b'>':
                yield ('eof', False, i); return
            yield ('end', name); i += 1; continue
        name, i = token(i)
        if not name:
            yield ('eof', False, i); return
        attrs = []
        empty = False
        while True:
            while i < n and data[i] in skip:
                i += 1
            if i >= n:
                yield ('eof', False, i); return
            c = data[i:i + 1]
            if c == b'>':
                i += 1; break
            if c == b'/':
                if data[i + 1:i + 2] != b'>':
                    yield ('eof', False, i); return
                empty = True; i += 2; break
            if not c.isalpha():
                yield ('eof', False, i); return
            k, i = token(i)
            while i < n and data[i] in skip:
                i += 1
            if data[i:i + 1] != b'=':
                yield ('eof', False, i); return
            v, i = token(i + 1)
            if v is None:
                yield ('eof', False, i); return
            if len(attrs) > 49:                      # 0x7b9877: cmp ecx, 0x62 on the pointer count
                yield ('eof', False, i); return
            attrs.append((k, v))
        yield ('start', name, attrs, tag_at)
        if empty:
            yield ('end', name)


COND_TAGS = ('Platform', 'ExcludeIn', 'BuildTag', 'MainIniOption', 'Locale', 'GameRegion')


class Counter:
    """One load set = one reader: templates persist across the files, the table is shared."""
    def __init__(self, ctx, types=None):
        self.ctx = ctx
        self.types = types or load_types()
        self.templates = {}           # name -> {'attrs': [...], 'children': int}
        self.template_slots = 0
        self.template_overflow = 0
        self.entries = []             # (kind, file, line, name/type) in table order
        self.kinds = {0: 0, 1: 0, 2: 0, 3: 0}
        self.unknown_types = {}
        self.skipped_template_refs = 0
        self.per_file = {}
        self.truncated = {}           # file -> None (read to the end) or (offset, line) where token 4 ended it

    # -- template attribute merge (0x5532b0): the element's own attributes win, then the template chain
    def merged(self, attrs):
        out = list(attrs)
        seen = {k for k, _ in attrs}
        tname = attr(attrs, 'Template')
        depth = 0
        while tname and depth < 16:
            t = self.find_template(tname)
            if not t:
                break
            for k, v in t['attrs']:
                if k not in seen:
                    out.append((k, v)); seen.add(k)
            tname = attr(t['attrs'], 'Template')
            depth += 1
        return out

    def find_template(self, name):
        t = self.templates.get(name)
        if t is None:                 # GUESS 1
            for k, v in self.templates.items():
                if k.lower() == name.lower():
                    return v
        return t

    def count_file(self, path, text=None):
        ctx = self.ctx
        data = text if text is not None else open(path, 'rb').read()
        include = [True]              # reader+0x1d0 with its stack
        objstack = []                 # reader+0xb59ec: the object under construction, None = nothing
        fname = os.path.basename(path)
        self.per_file[fname] = before = len(self.entries)

        import bisect
        nl = [m.start() for m in re.finditer(b'\n', data)]
        line = [1]

        def start(tag, attrs):
            cur = include[-1]
            if tag == 'ExcludeIn':
                flag = cur
                for k, v in attrs:
                    if v.lower() == 'true' and ctx.exclude_in(k):
                        flag = False
                include.append(flag); return
            if tag in ('Platform', 'BuildTag'):
                b16 = read_bool(attrs, 'PC')
                if b16 is None and ctx.buildtag:
                    b16 = read_bool(attrs, ctx.buildtag, ci=True)
                b15 = read_bool(attrs, ctx.input_name())
                include.append(bool(b16 or b15) and cur); return
            if tag == 'Locale':
                include.append(bool(read_bool(attrs, ctx.locale, ci=True)) and cur); return
            if tag == 'GameRegion':
                include.append(bool(read_bool(attrs, ctx.region, ci=True)) and cur); return
            if tag == 'MainIniOption':
                want = attr(attrs, 'Value'); want = int(want) if want and want.strip().lstrip('-').isdigit() else 1
                key = attr(attrs, 'Name') or ''
                have = ctx.ini.get(key)
                try:
                    have = int(str(have).strip()) if have not in (None, '') else 0
                except ValueError:
                    have = 0
                include.append(have == want and cur); return
            if not cur:
                objstack.append(None); return
            # 0x8cee45: an included element
            tname = attr(attrs, 'Template')
            t = self.find_template(tname) if tname else None
            if t and t['children']:
                self.skipped_template_refs += 1
                if objstack and isinstance(objstack[-1], dict) and objstack[-1].get('template'):
                    objstack[-1]['children'] += t['children']   # 0x403060 under a definition: its children become this one's
                objstack.append(None); return
            eff = self.merged(attrs)
            obj = None
            if tag == 'Template':
                if self.template_slots < TEMPLATE_SLOTS:
                    self.template_slots += 1
                    obj = {'attrs': attrs, 'children': 0, 'template': True}
                    name = attr(attrs, 'Name')
                    if name:
                        self.templates[name] = obj
                else:
                    self.template_overflow += 1
            elif tag == 'GuiElement':
                typ = attr(eff, 'Type')
                if typ in self.types:
                    obj = self.add(0, fname, line[0], typ)
                else:                     # no Type at all (0x579650 falls through to 0x7b0fa0) or a name no factory knows
                    typ = typ or '(no Type: template missing, empty, or in an excluded block)'
                    self.unknown_types[typ] = self.unknown_types.get(typ, 0) + 1
            elif tag == 'Window':
                typ = attr(eff, 'Type') or 'Standard'
                obj = self.add(1, fname, line[0], attr(eff, 'Name') or typ)
            elif tag == 'ColorSet':
                obj = self.add(2, fname, line[0], attr(attrs, 'Name'))
            elif tag == 'ButtonGraphic':
                obj = self.add(3, fname, line[0], attr(attrs, 'Name'))
            else:
                obj = {'other': tag}   # Text, Graphic, GraphicElement, Windows: 0x7b0fa0, no table entry
            objstack.append(obj)

        def end(tag):
            if tag in COND_TAGS:
                include.pop(); return
            if not include[-1]:
                return
            child = objstack.pop()
            if child is not None and objstack and objstack[-1] is not None:
                parent = objstack[-1]
                if isinstance(parent, dict) and parent.get('template'):
                    parent['children'] += 1       # AddChild on the definition (0x5dd0b4 -> slot 2)

        pos = 0
        for tok in tokenize(data):
            if tok[0] == 'start':
                line[0] = bisect.bisect_left(nl, tok[3]) + 1
                start(tok[1], tok[2])
            elif tok[0] == 'end':
                end(tok[1])
            else:
                self.truncated[fname] = None if tok[1] else (tok[2], data.count(b'\n', 0, tok[2]) + 1)
        self.per_file[fname] = len(self.entries) - before
        return len(self.entries) - before

    def add(self, kind, fname, line, name):
        self.entries.append((kind, fname, line, name))
        self.kinds[kind] += 1
        return {'kind': kind}

    def report(self):
        n = len(self.entries)
        lines = ['table %d of %d entries (%d elements, %d windows, %d colour sets, %d button graphics); '
                 '%d free below entry %d%s' % (n, TABLE, self.kinds[0], self.kinds[1], self.kinds[2], self.kinds[3],
                                              BUDGET - n, BUDGET, '' if n <= BUDGET else
                                              ' - OVER: entry %d is a %s' % (BUDGET, ['element', 'WINDOW', 'COLOUR SET', 'BUTTON GRAPHIC'][self.entries[BUDGET][0]]))]
        lines.append('per file: ' + ', '.join('%s %d' % kv for kv in self.per_file.items()))
        for f, t in self.truncated.items():
            if t:
                lines.append('WARNING %s: the game stops reading at offset %d (line %d): stray text or a malformed tag; nothing after it is loaded' % (f, t[0], t[1]))
        lines.append('templates: %d of %d definition slots used%s; %d element(s) that name a template with children (made nothing)'
                     % (self.template_slots, TEMPLATE_SLOTS, '' if not self.template_overflow else ' - %d OVERFLOWED (silently null)' % self.template_overflow,
                        self.skipped_template_refs))
        if self.unknown_types:
            lines.append('made no entry: ' + ', '.join('%s x%d' % kv for kv in sorted(self.unknown_types.items(), key=lambda x: -x[1])))
        return '\n'.join(lines)


def parse_flags(args):
    kw = {}
    rest = []
    it = iter(args)
    for a in it:
        if a == '--gamepad': kw['gamepad'] = True
        elif a == '--arcade': kw['arcade'] = True
        elif a == '--fa': kw['fa'] = True
        elif a == '--campaign': kw['campaign'] = True
        elif a == '--german': kw['german'] = True
        elif a == '--japanese': kw['japanese'] = True
        elif a == '--locale': kw['locale'] = next(it)
        elif a == '--region': kw['region'] = next(it)
        elif a == '--difficulty': kw['difficulty'] = int(next(it))
        elif a == '--ini':
            k, _, v = next(it).partition('='); kw.setdefault('ini', {})[k] = v
        else: rest.append(a)
    return Context(**kw), rest


def selftest(d):
    """The stock sets, as the retail PC game loads them. The frontend set must fit the table (the stock game
    runs), which the 2026-10-09 model (count.py, 5992) failed."""
    ok = True
    fe = Counter(Context())
    fe.count_file(os.path.join(d, 'patch01_frontend.xml')); fe.count_file(os.path.join(d, 'frontend_online.xml'))
    print('FRONTEND (Patch01 frontend.xml + kaneandlynch.zip online.xml, keyboard):'); print(fe.report())
    ok &= len(fe.entries) <= TABLE
    fg = Counter(Context(gamepad=True))
    fg.count_file(os.path.join(d, 'patch01_frontend.xml')); fg.count_file(os.path.join(d, 'frontend_online.xml'))
    print('FRONTEND, gamepad: %d entries' % len(fg.entries))
    ok &= len(fg.entries) <= TABLE
    for label, ctx in (('Arcade', Context(arcade=True)), ('FA online', Context(fa=True)), ('campaign Normal', Context(campaign=True)),
                       ('campaign Hard', Context(campaign=True, difficulty=2))):
        lv = Counter(ctx)
        lv.count_file(os.path.join(d, 'patch01_ingame.xml'))
        if not label.startswith('campaign'):
            lv.count_file(os.path.join(d, 'frontend_online.xml'))
        print('LEVEL %s (Patch01 ingame.xml%s):' % (label, '' if label.startswith('campaign') else ' + level online.xml')); print(lv.report())
        ok &= len(lv.entries) <= TABLE
    print('selftest', 'OK' if ok else 'FAIL: a stock set is over the table, the model is wrong')
    return ok


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    mode = argv[1]
    if mode == 'selftest':
        return 0 if selftest(argv[2]) else 1
    ctx, files = parse_flags(argv[2:])
    c = Counter(ctx)
    for f in files:
        c.count_file(f)
    print(c.report())
    return 0 if len(c.entries) <= BUDGET else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
