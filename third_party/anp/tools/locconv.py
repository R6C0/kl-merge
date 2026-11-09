"""Dead Men .LOC string tables -> Dog Days text conventions (ANP_LOC_FIX).

Format (same in both games; checked by an exact parse/rebuild round trip over every stock .LOC of both games):
  root      = u8 count, u32 offsets[count-1], children
  child     = name\\0, u8 type, payload
  directory = type 0x10: u8 count, u32 offsets[count-1], children. offsets[k-1] = start of child k relative to the
              first child, which follows the table directly.
  leaf      = any other type. Bit 0x01: payload starts with the text (UTF-8, \\0-terminated); what follows (sound ids)
              is kept byte for byte. A leaf runs up to the next sibling (or the end of its parent).

Text fixes (Dead Men's strings, read by Dog Days' exe):
  * Icon tags. Both exes turn {name} into a private-use glyph through a _stricmp chain (kl2 0x926350, Dead Men
    0x45d550..0x45d988), but the names differ. Dog Days does not know Dead Men's {a}/{b}/{x}/{y} or its squad icons
    {attack} {defend} {follow} {objective} {rappel} {heal} {ammo} (+ _kb), so it would treat them as input-action
    tags (kl2 0x68e4b0, U+E100 path) and draw no icon. They are renamed to the Dog Days tag that yields the SAME code
    point: {a} -> {gc_a} (0xe000) ... {attack} -> {yellowcard} (0xe012) ... {ammo} -> {skull} (0xe018). The glyph
    for that code point comes from the level's font (Dead Men's art with ANP_DM_FONTS).
  * C1 controls. Dead Men's LOC has cp1252 punctuation stored as U+0080..U+009F (U+0092 for an apostrophe, U+0085
    ellipsis, U+0096 en dash, U+009C oe...). No font has glyphs for them: Dead Men's lookup falls back to a space
    (0x56caa1), Dog Days' to '_' (kl2 0x4fb6f1), so they would show as underscores. They are replaced by the
    character cp1252 means.

Additions (port_level.py, each behind its own switch; add_leaves / map_texts below):
  * ANP_CHAPTER_TITLES: /AllLevels/Menu/Play/L01..L11_ChapterTitle = this level's Dead Men title (kl2 finds no L<n> in a
    Dead Men scene path and uses chapter index 0, so its title lookups ask for L01_ChapterTitle).
  * ANP_LOC_EXTREME: /AllLevels/Menu/Play/Difficulty_Extreme (Dog Days' 4th difficulty; Dead Men has three).
  * ANP_BRIEF_COMMANDS: the crew-command hints name Dead Men input actions ({HoldFollow} ...) that kl2 does not know;
    they are rewritten to the keys the loader's crew orders use (loader/squad.inc).
  * ANP_LOADER=silent: the Dog Days loading screen's subtitle lines (/Load/<L>_Load/...) blanked."""
import re, struct

# Dead Men tag -> Dog Days tag with the same code point (kaneandlynch.exe 0x45d550.. / kl2.exe 0x926350..)
TAG_MAP = {
    'a': 'gc_a', 'b': 'gc_b', 'x': 'gc_x', 'y': 'gc_y',                                   # 0xe000..0xe003
    'attack': 'yellowcard', 'defend': 'yellowcardtarget', 'follow': 'escapevehicle_green',  # 0xe012..0xe014
    'objective': 'escapevehicle_yellow', 'rappel': 'escapevehicle_red',                    # 0xe015, 0xe016
    'heal': 'heist1up', 'ammo': 'skull',                                                   # 0xe017, 0xe018
}
TAG_MAP.update({k + '_kb': v + '_kb' for k, v in list(TAG_MAP.items()) if len(k) > 1})
TAG_CP = {'gc_a': 0xe000, 'gc_b': 0xe001, 'gc_x': 0xe002, 'gc_y': 0xe003, 'yellowcard': 0xe012,
          'yellowcardtarget': 0xe013, 'escapevehicle_green': 0xe014, 'escapevehicle_yellow': 0xe015,
          'escapevehicle_red': 0xe016, 'heist1up': 0xe017, 'skull': 0xe018}

# U+0080..U+009F -> what the byte means in cp1252 (bytes cp1252 leaves undefined are kept)
C1_MAP = {}
for _b in range(0x80, 0xa0):
    try: C1_MAP[chr(_b)] = bytes([_b]).decode('cp1252')
    except UnicodeDecodeError: pass

_TAG_RX = re.compile(r'\{([A-Za-z0-9_]+)\}')


def _children(d, p, cnt, end, out):
    offs = struct.unpack_from('<%dI' % max(cnt - 1, 0), d, p); p += 4 * max(cnt - 1, 0); base = p
    starts = [base] + [base + o for o in offs] if cnt else []
    for k, s in enumerate(starts):
        e = starts[k + 1] if k + 1 < cnt else end
        assert base <= s < e <= end, ('bad child extent', hex(s), hex(e))
        ne = d.index(b'\0', s); name = d[s:ne]; t = d[ne + 1]
        if t == 0x10:
            sub = []; _children(d, ne + 3, d[ne + 2], e, sub); out.append([name, t, sub])
        elif t & 1:
            te = d.index(b'\0', ne + 2); assert te < e
            out.append([name, t, d[ne + 2:te], d[te + 1:e]])
        else:
            out.append([name, t, None, d[ne + 2:e]])
    return out


def parse(d):
    """-> list of [name, 0x10, children] / [name, type, text bytes or None, trailing bytes]"""
    return _children(d, 1, d[0], len(d), [])


def _build(nodes):
    assert len(nodes) < 256, 'directory with %d children' % len(nodes)
    blobs = []
    for n in nodes:
        if n[1] == 0x10: blobs.append(n[0] + b'\0\x10' + _build(n[2]))
        elif n[2] is not None: blobs.append(n[0] + b'\0' + bytes([n[1]]) + n[2] + b'\0' + n[3])
        else: blobs.append(n[0] + b'\0' + bytes([n[1]]) + n[3])
    offs = []; acc = 0
    for b in blobs[:-1]: acc += len(b); offs.append(acc)
    if not nodes: return b'\0'
    return bytes([len(nodes)]) + struct.pack('<%dI' % len(offs), *offs) + b''.join(blobs)


def build(nodes): return _build(nodes)


def fix_text(s, stats, squad_icons=True):
    def tag(m):
        nm = m.group(1); new = TAG_MAP.get(nm.lower())
        if new is None or (not squad_icons and not new.startswith('gc_')): return m.group(0)
        stats['tag {%s} -> {%s}' % (nm, new)] = stats.get('tag {%s} -> {%s}' % (nm, new), 0) + 1
        return '{%s}' % new
    s2 = _TAG_RX.sub(tag, s)
    if any(c in C1_MAP for c in s2):
        for c in set(s2) & set(C1_MAP):
            k = 'U+%04X -> U+%04X' % (ord(c), ord(C1_MAP[c])); stats[k] = stats.get(k, 0) + s2.count(c)
        s2 = ''.join(C1_MAP.get(c, c) for c in s2)
    return s2


def find(nodes, path):
    """node at path (list of names, case-insensitive) or None"""
    for n in nodes:
        if n[0].decode('latin1').lower() == path[0].lower():
            if len(path) == 1: return n
            return find(n[2], path[1:]) if n[1] == 0x10 else None
    return None


def _insert_sorted(children, node):
    """Dead Men keeps every directory sorted case-insensitively (all 1620 directories of M02A's LOC); Dog Days nearly
    so. New entries go where that order puts them."""
    k = node[0].lower()
    i = next((j for j, c in enumerate(children) if c[0].lower() > k), len(children))
    children.insert(i, node)


def add_leaves(d, adds, stats=None):
    """Add text leaves to a .LOC. adds = [(path, text bytes, template leaf)]: path = list of names; the template (a
    parsed leaf, e.g. a sibling) gives the type byte and the trailing bytes. Missing directories are created; an
    existing key is left alone. Returns (bytes, stats); the input bytes come back unchanged when nothing was added."""
    stats = {} if stats is None else stats
    nodes = parse(d); n_add = 0
    for path, text, tpl in adds:
        if find(nodes, path) is not None:
            stats['key already present (kept) %s' % '/'.join(path)] = 1; continue
        cur = nodes
        for k, nm in enumerate(path[:-1]):
            dn = find(cur, [nm])
            if dn is None:
                dn = [nm.encode('latin1'), 0x10, []]; _insert_sorted(cur, dn)
            elif dn[1] != 0x10: raise ValueError('LOC: %s is a leaf, not a directory' % '/'.join(path[:k + 1]))
            cur = dn[2]
        typ, tail = (tpl[1], tpl[3]) if tpl is not None else (0x09, b'\0\0\0\0')
        _insert_sorted(cur, [path[-1].encode('latin1'), typ | 1, text, tail]); n_add += 1
    stats['keys added'] = stats.get('keys added', 0) + n_add
    if not n_add: return d, stats
    out = build(nodes)
    assert parse(out) == nodes
    return out, stats


def map_texts(d, fn, stats=None):
    """fn(path string, text str) -> new text str for every text leaf (path like '/M02/IngameBriefing/Key').
    Returns (bytes, stats); unchanged input bytes when no text changed."""
    stats = {} if stats is None else stats
    nodes = parse(d); changed = [0]
    def walk(ns, path):
        for n in ns:
            p = path + '/' + n[0].decode('latin1')
            if n[1] == 0x10: walk(n[2], p); continue
            if n[2] is None: continue
            try: s = n[2].decode('utf-8')
            except UnicodeDecodeError: continue
            s2 = fn(p, s)
            if s2 != s: n[2] = s2.encode('utf-8'); changed[0] += 1
    walk(nodes, '')
    stats['texts rewritten'] = stats.get('texts rewritten', 0) + changed[0]
    if not changed[0]: return d, stats
    out = build(nodes)
    assert parse(out) == nodes
    return out, stats


# Crew-command hints (ANP_BRIEF_COMMANDS). Dead Men names its squad input actions in the text; kl2 has none of these
# action names (no string in kl2.exe), so they would draw nothing. Only the hint keys are rewritten: {HoldDefend} is
# also Dead Men's cutscene-skip prompt (/AllLevels/Menu/Misc/Skip), which keeps it.
SQUAD_TAGS = {'HoldFollow': 'follow', 'HoldAttack': 'attack', 'HoldDefend': 'defend',
              'NextCommandReceiver': 'next', 'PrevCommandReceiver': 'prev'}
# loader/squad.inc defaults (ANP_squad.txt follow=0x02 attack=0x03 defend=0x04 next=0x0f prev=0 = Shift+next)
SQUAD_KEYS = {'follow': '1', 'attack': '2', 'defend': '3', 'next': 'Tab', 'prev': 'Shift+Tab'}
COMMAND_HINT_RX = re.compile(r'/IngameBriefing/[^/]*_Commands', re.I)


def squad_keys(spec=''):
    """'follow=1,attack=2,...' (ANP_SQUAD_KEYS) over the squad.inc defaults"""
    k = dict(SQUAD_KEYS)
    for kv in [x for x in spec.split(',') if '=' in x]:
        a, b = (t.strip() for t in kv.split('=', 1))
        if a.lower() in k and b: k[a.lower()] = b
    return k


def command_hint_fix(keys, stats):
    """map_texts function: in crew-command hints, {HoldFollow} ... -> '[1]' ... (keys from squad_keys)"""
    def fn(path, s):
        if not COMMAND_HINT_RX.search(path): return s
        def tag(m):
            a = SQUAD_TAGS.get(m.group(1))
            if a is None: return m.group(0)
            stats['command hint {%s} -> [%s]' % (m.group(1), keys[a])] = stats.get('command hint {%s} -> [%s]' % (m.group(1), keys[a]), 0) + 1
            return '[%s]' % keys[a]
        return _TAG_RX.sub(tag, s)
    return fn


# ANP_HINTS2 (port_level.py; PLAN item 4): three more Dead Men hint kinds come back with Dog Days / loader keys.
#  * ObjectiveLocator (M01/M02/M03): Dead Men's map key {IngameMapActive} -> Dog Days' own input tag {HoldObjective}
#    (bound to O / D-pad down, kl2 0xb510dc; stock L01 /L01/IngameBriefing/L01_IngameBriefing_120_Weapon_pc writes
#    'Press {HoldObjective} to locate weapons.', so kl2 draws that tag as the bound key).
#  * LynchTargetSniper (M06): {HoldAttack} -> the squad.inc attack key, like the crew-command hints.
#  * GiveLynchShotgun / GiveLynchSidearm (M02): Dead Men describes its inventory wheel; the text is replaced by the
#    loader's give key (loader/give.inc: the held gun goes to the selected / nearest merc within 300 cm). Dead Men has
#    no Dutch/Russian/Polish/Japanese LOC (those are English copies), so these get the English text.
OBJ_LOCATOR_RX = re.compile(r'/IngameBriefing/[^/]*ObjectiveLocator', re.I)
SNIPER_HINT_RX = re.compile(r'/IngameBriefing/LynchTargetSniper', re.I)
GIVE_HINT_RX = re.compile(r'/IngameBriefing/[^/]*_B_GiveLynch(Shotgun|Sidearm)(_[a-z0-9]+)?$', re.I)
GIVE_TEXT = {
    'English': ('Hold a primary weapon and press [{k}] near Lynch\nto give it to him',
                'Hold a secondary weapon and press [{k}] near Lynch\nto give it to him'),
    'German': ('Halte eine Primärwaffe und drücke [{k}] in Lynchs Nähe,\num sie ihm zu geben.',
               'Halte eine Sekundärwaffe und drücke [{k}] in Lynchs Nähe,\num sie ihm zu geben.'),
    'French': ('Prenez une arme principale en main et pressez [{k}] près de Lynch\npour la lui donner',
               'Prenez une arme secondaire en main et pressez [{k}] près de Lynch\npour la lui donner'),
    'Spanish': ('Empuña un arma principal y pulsa [{k}] cerca de Lynch\npara dársela.',
                'Empuña un arma secundaria y pulsa [{k}] cerca de Lynch\npara dársela.'),
    'Italian': ("Impugna un'arma primaria e premi [{k}] vicino a Lynch\nper dargliela.",
                "Impugna un'arma secondaria e premi [{k}] vicino a Lynch\nper dargliela."),
}


def hints2_fix(lang, keys, give_key, stats):
    """map_texts function (ANP_HINTS2): lang = the language of the Dead Men text in this LOC, keys = squad_keys(),
    give_key = the label of give.inc's key"""
    def bump(k): stats[k] = stats.get(k, 0) + 1
    def fn(path, s):
        if OBJ_LOCATOR_RX.search(path) and '{IngameMapActive}' in s:
            bump('objective locator hint {IngameMapActive} -> {HoldObjective}')
            return s.replace('{IngameMapActive}', '{HoldObjective}')
        if SNIPER_HINT_RX.search(path):
            def tag(m):
                if m.group(1) != 'HoldAttack': return m.group(0)
                bump('sniper hint {HoldAttack} -> [%s]' % keys['attack']); return '[%s]' % keys['attack']
            return _TAG_RX.sub(tag, s)
        m = GIVE_HINT_RX.search(path)
        if m:
            t = GIVE_TEXT.get(lang, GIVE_TEXT['English'])[0 if m.group(1).lower() == 'shotgun' else 1]
            bump('give hint %s -> key [%s] (%s)' % (m.group(1), give_key, lang if lang in GIVE_TEXT else 'English'))
            return t.format(k=give_key)
        return s
    return fn


LOADER_SUB_RX = re.compile(r'^/Load/[^/]+_Load/', re.I)


def loader_subtitles_blank(stats):
    """map_texts function: Dog Days' loading-screen subtitle lines (/Load/L01_Load/L01_Load_Lynch ... and FA_Load) -> ''.
    /Load/Buffering and /Load/PressToSkip_* stay."""
    def fn(path, s):
        if not LOADER_SUB_RX.search(path) or not s: return s
        stats['loader subtitle blanked'] = stats.get('loader subtitle blanked', 0) + 1
        return ''
    return fn


def convert(d, stats=None, squad_icons=True):
    """Dead Men .LOC bytes -> fixed .LOC bytes (identical when nothing needs fixing). squad_icons=False keeps Dead Men's
    squad tags ({attack}...) as they are: only right when the level's fonts carry Dead Men's art at 0xe012..0xe018
    (ANP_DM_FONTS without ANP_DM_FONT_DD), else they would draw Dog Days' yellow card, escape vehicle, skull..."""
    stats = {} if stats is None else stats
    nodes = parse(d)
    assert build(nodes) == d, 'LOC round trip failed'
    changed = [0]
    def walk(ns):
        for n in ns:
            if n[1] == 0x10: walk(n[2]); continue
            if n[2] is None: continue
            try: s = n[2].decode('utf-8')
            except UnicodeDecodeError:
                stats['non-UTF-8 strings kept'] = stats.get('non-UTF-8 strings kept', 0) + 1; continue
            s2 = fix_text(s, stats, squad_icons)
            if s2 != s: n[2] = s2.encode('utf-8'); changed[0] += 1
    walk(nodes)
    stats['strings changed'] = stats.get('strings changed', 0) + changed[0]
    if not changed[0]: return d, stats
    out = build(nodes)
    assert parse(out) == nodes
    return out, stats
