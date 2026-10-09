#!/usr/bin/env python3
"""
Character speech on a grafted level: who speaks in Dog Days, what a graft does to it, and the
repairs. Spec with the evidence: re/voice.md. OFFLINE: nothing here has been heard in the game.

    python kl_voice.py test                  the exe / stock-file facts below, re-measured (1 min)
    python kl_voice.py census <level|zip>    characters, voice sets, clip formats, line keys
    python kl_voice.py build [<out>]         the bank (F07 + M03_FA_A) and Retomoto (F07 + M09_B +
                                             M09_A) WITHOUT and WITH the repairs into <out>
                                             (default <work>/build/voice), census of each, the
                                             before / after table. Nothing is installed.
    python kl_voice.py defs <level>          the character definitions of a stock bank, slot by slot

HOW A CHARACTER SPEAKS IN DOG DAYS (EXE = read in kl2.exe, MEASURED = counted on the stock files)
  1 Barks. A character (class ZLNKWHANDS and below: ZFFActor, ZFFPlayer) holds six sound
    DEFINITIONS (ZLNKWHANDS[0..5], type handler 46, object +0x1e8 .. +0x238, 16 bytes each).
    [0..2] are voice sets, [3] [4] are 0 in every stock level, [5] is the material sound table.
    A definition is a list of slots, one per speech event; the code asks for an event by slot
    number and every reader checks the number against the definition's own length (EXE: all 17
    uses of the list accessor 0x65c140, e.g. 0x7a1040, 0x474770, 0x900ff0). So a short or a
    long definition is safe, and an empty slot is silence.
    Slot order (MEASURED, all 21 + 20 stock banks): an NPC definition has 35 slots in Dog Days
    and 31 in Dead Men; 0..25 mean the same in both (0 pain, 1 die, 3 first contact, 4 enemy
    close, 5 enemy spotted, 7 / 8 suppress, 13 heavy fire, 16 panic, 18 advance, 25 man down).
    Dog Days' code also asks for 27 (battle cries), 28 / 29 (advance) and 34 (alert): nothing
    there in a Dead Men definition, and Dead Men's 27 (a wounded man begging, 'graceshot') sits
    where Dog Days expects the battle cry. def_slots() moves them.
  2 Heisters. The 16 ZFFPlayer of ALL nine stock Fragile Alliance levels have NO voice set
    (MEASURED). Kane and Lynch in the story have one (kane_default 63 slots, lynch_default 42:
    pain, death, reload, ammo low / out, cover, enemy spotted, panic, adrenalin). So in stock
    Fragile Alliance the heisters never bark; all they say are the settings' lines (3).
    hero_voices() gives the eight heisters the story sets - an EXPERIMENT, see re/voice.md.
  3 Lines. ZOnlineFragileAllianceSettings holds 302 line keys (fields 17..323). Its Init (EXE
    0x88d780) hands each to 0x6b8710 with a flag. Flag 0: the key K itself is looked up
    (0x828fa0). Flag 1: ONLY K_C1 .. K_C9 and K_R_C9 are looked up, never K (0x6b879d ..
    0x6b8978) - one recording per heister (C1..C8) and for Glazer (C9). LINES below is that
    flag for every field, read off the 302 call sites; `test` proves it on the nine stock
    levels (a flag-1 field's key exists only with _C<n>, a flag-0 field's only plain).
    A Dead Men key (one voice per line, no _C<n>) in a flag-1 field is therefore SILENT: that
    is 105 of the bank's 228 line fields. loc_aliases() adds K_C1..K_C9 leaves that name K's clip.
  4 Idle talk. There is no idle-banter system in the stock Fragile Alliance levels: the exe has
    a ZSmallTalkCtrl class (controller SmallTalkCtrl), no stock level uses it (MEASURED on
    F01 F06 F07 L01 L04). What a waiting crew hears are the reminder lines of the settings
    (fields 136..138 'MissionReminder', the time warnings 161..166) - they need a real round.
  5 Streamed clips. The wave header (.WHD record) names the codec; the buffer fill routine
    (EXE 0x79ff50, ZSoundBufferWintel slot 12) branches on it: 0x11 = IMA ADPCM, with a path
    for buffers in memory (0x7a004d) AND one for streamed buffers (0x7a00c1: block = channels
    * 0x400, decoder 0x6d2020, the three interleave modes); 0x1000 = Vorbis (0x7a0254); else
    PCM (0x7a04e0). So the stream player does have an ADPCM decoder path, although Dog Days
    ships no streamed ADPCM clip. Nothing is re-encoded. Whether it SOUNDS right is for ears.

WHAT IS A GUESS (each marked ASSUMPTION where the code makes it)
  - def_slots(): which Dead Men slot feeds Dog Days' 27, 28, 29, 34 (by the names of the sets
    the stock definitions hold in those slots, not read in code).
  - give_voices(): a mute soldier gets the voice set most of its kind have on the same map.
  - hero_voices(): that ZFFPlayer barks in a Fragile Alliance round when it has a voice set
    (stock never tries it), and that four heisters sharing Kane's voice is acceptable.
  - fill_lines(): a field Dead Men left empty takes Dog Days' line of the same field.
"""
import collections, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd, kl_loc, kl_whd as W, kl_fa, kl_prpjoin as J
from kl_prp import units
from kl_snd import u32, u16

SETTINGS = 'OnlineFragileAllianceSettings'
# (first field, last field, flag, who) of ZOnlineFragileAllianceSettings' line keys, from the 302
# calls of its Init (kl2 0x88d780; field = (member offset - 0x2c) / 4). flag 1 = looked up as
# K_C1..K_C9 (+ K_R_C9) only. who = the third argument, stored at line +0x24: -1 1 2 3 4, not
# decoded (ASSUMPTION by the keys: who hears / says it).
LINES = ((17, 20, 1, 2), (21, 26, 0, 2), (27, 29, 1, 2), (30, 35, 1, 4), (36, 38, 1, 2), (39, 41, 0, 2), (42, 50, 1, 2),
         (51, 53, 0, 2), (54, 59, 1, 2), (60, 62, 0, 2), (63, 71, 1, 2), (72, 77, 0, -1), (78, 83, 1, 2), (84, 89, 0, 2),
         (90, 92, 1, 3), (93, 95, 0, 3), (96, 98, 1, 3), (99, 101, 0, 3), (102, 104, 1, 2), (105, 109, 0, 2),
         (110, 111, 0, -1), (112, 114, 0, 1), (115, 117, 0, -1), (118, 120, 1, 3), (121, 123, 0, 3), (124, 132, 1, 3),
         (133, 135, 0, 2), (136, 138, 1, 2), (139, 142, 0, 3), (143, 148, 1, 2), (149, 151, 1, 3), (152, 154, 0, 3),
         (160, 160, 0, -1), (161, 161, 0, 2), (162, 163, 0, 3), (164, 164, 0, 2), (165, 166, 0, 3), (167, 167, 1, 1),
         (168, 168, 0, 1), (169, 169, 1, 1), (170, 171, 0, 1), (172, 172, 0, 2), (173, 175, 0, 1), (176, 178, 1, 3),
         (179, 184, 0, 3), (185, 187, 0, 2), (188, 190, 0, 1), (191, 193, 1, 1), (194, 196, 0, 1), (197, 199, 1, 2),
         (200, 208, 0, -1), (209, 214, 0, 1), (215, 220, 1, 1), (221, 223, 0, 1), (224, 229, 0, 2), (230, 232, 0, 3),
         (233, 235, 1, 3), (236, 238, 0, 3), (239, 241, 1, 3), (242, 244, 0, 3), (245, 274, 0, 1), (275, 286, 0, 2),
         (287, 289, 0, 1), (290, 292, 1, 2), (293, 298, 0, 2), (299, 301, 1, 2), (302, 304, 0, 2), (305, 307, 0, 1),
         (308, 312, 0, 2), (313, 323, 0, -1))
VARIANTS = 9                                # K_C1 .. K_C9
NPC_DM, NPC_DD = 31, 35                     # slots of an NPC voice definition
# Dog Days slot <- the first Dead Men slot of the list that holds something.
# ASSUMPTION, by the sets the stock definitions hold there: Dog Days 27 = battlecries_*, 28 / 29 =
# advance_*, 34 = alert_*; Dead Men 28 = policewarning_* / japaneseguard_attack, 18 = advance_*,
# 17 = advanceresponse_*, 3 = enemyspotted1stcontact_*.
NPC_FROM = {27: (28, 18), 28: (18, 17), 29: (17, 18), 34: (3, 5, 4)}
NPC_CLEAR = (26, 27, 28, 30)                # Dead Men's own use of slots Dog Days gives another meaning (or none)
HERO_DEFS = {'Kane': b'/kane_default#def', 'Lynch': b'/lynch_default#def'}     # animation set -> story voice set
OPTIONS = dict(defs=True,                   # Dead Men character definitions in Dog Days' slot order
               npc=True, prefer='map',      # a voice set for mute soldiers / civilians: the map's own first, or 'host'
               lines=True,                  # empty / unknown line keys of the map's settings from S
               aliases=True,                # K_C1..K_C9 leaves for Dead Men keys in per-character fields
               heroes=False, hero_source='L01')   # EXPERIMENT: Kane's / Lynch's story voice sets on the heisters


def options(voice):
    o = dict(OPTIONS)
    if isinstance(voice, dict):
        bad = set(voice) - set(o)
        if bad:
            raise ValueError('kl_voice: unknown options %s' % sorted(bad))
        o.update(voice)
    return o


def line_fields():
    """-> {settings field: (flag, who)} for the 302 line keys"""
    return {f: (flag, who) for a, b, flag, who in LINES for f in range(a, b + 1)}


# ------------------------------------------------------------------ definitions
def def_slots(name, slots):
    """kl_snd.merge's `defs` hook: a Dead Men NPC voice definition (31 slots) in Dog Days' slot
    order (35). Other definitions (weapons 13, civilians 5, players 20 / 49 / 55) stay."""
    if len(slots) != NPC_DM:
        return None
    out = list(slots) + [0] * (NPC_DD - NPC_DM)
    for i in NPC_CLEAR:
        out[i] = 0
    for dst, srcs in NPC_FROM.items():
        out[dst] = next((slots[s] for s in srcs if slots[s]), 0)
    return out


def definitions(S):
    """-> {offset: (name, [slot objects])} of a walked bank"""
    out = {}
    for o in S.tables.get(5, []):
        n, c = u16(S.b, o + 0x18), u32(S.b, o + 0x14)
        out[o] = (S.name(o).decode('latin1'), list(struct.unpack_from('<%dI' % n, S.b, c)) if c else [])
    return out


def sounds_below(S, o, seen=None):
    """The sound objects a set / definition / sequence leads to."""
    seen = set() if seen is None else seen
    if not o or o in seen or o not in S.kind:
        return []
    seen.add(o)
    t, b, out = S.kind[o], S.b, []
    if t == 1:
        return [o]
    n, c = u16(b, o + 0x18), u32(b, o + 0x14)
    if t in (2, 5) and c:
        for x in struct.unpack_from('<%dI' % n, b, c):
            out += sounds_below(S, x, seen)
    elif t == 3 and c:
        for i in range(n):
            k, _t, x = struct.unpack_from('<3I', b, c + 12 * i)
            if k in (2, 4, 5, 6):
                out += sounds_below(S, x, seen)
    return out


def codec(S, recs, o):
    """How the English clip of sound o is stored: 'memory adpcm', 'stream vorbis', 'stream adpcm',
    'stream pcm', 'stream pcm set' ..., or why there is none."""
    w = u32(S.b, o + 0x14)
    if not w:
        return 'no wave'
    if w >= S.T:
        return 'loading-sound bank'
    f = recs.get(u32(S.b, w + 0x14))
    if f is None:
        return 'no .WHD record'
    name = {1: 'pcm', 0x11: 'adpcm', 0x1000: 'vorbis'}.get(f['fmt'] & 0xffff, '%#x' % (f['fmt'] & 0xffff))
    if not f['fmt'] & W.STREAMED:
        return 'memory ' + name
    return 'stream ' + name + (' set' if f['fmt'] >> 24 else '')


# ------------------------------------------------------------------ characters
def _kind(sc, k, d):
    ctrls = {sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']}
    anim = (d.get('ZLNKOBJ[2]') or '').rsplit('#', 1)[-1]
    if sc.cls(k) == 'ZFFPlayer':
        t = str(d.get('ZFFPlayer[1]'))                     # eZFFP_TYPE_MULTIPLAYER_NORMAL, ..._POLICEMAN, ..._SINGLEPLAYER(_COOP)
        return 'heister' if t.endswith('MULTIPLAYER_NORMAL') else 'police player' if t.endswith('POLICEMAN') else 'player'
    if 'ZCivilian' in ctrls:
        return 'woman' if 'female' in anim.lower() else 'civilian'
    if 'ZSoldier' in ctrls:
        return 'dog' if anim == 'Dog' else 'bot' if d.get('ZFFActor[0]') == 'Ally' else 'soldier'
    return None


def characters(sc, ks=None):
    """-> [(node, kind, (voice slots 0..2), animation set)] of the players and actors among nodes
    ks (default: all). kind: heister, police player, player, soldier, bot, dog, civilian, woman."""
    sch, out = J.schema('dd'), []
    for k in (range(1, len(sc.nodes)) if ks is None else ks):
        cls = sc.cls(k)
        if cls not in ('ZFFActor', 'ZFFPlayer'):
            continue
        d = dict(zip(J.labels('dd', cls), kl_fa.node_values(sc, k)))
        kind = _kind(sc, k, d)
        if kind:
            out.append((k, kind, tuple(d['ZLNKWHANDS[%d]' % i] for i in range(3)), (d.get('ZLNKOBJ[2]') or '').rsplit('#', 1)[-1]))
    return out


def set_voice(sc, k, slots):
    """Write voice slots 0..2 of node k (.SND offsets of definitions)."""
    lab = J.labels('dd', sc.cls(k))
    def fn(us):
        for i, v in enumerate(slots):
            j = lab.index('ZLNKWHANDS[%d]' % i)
            us[j][0] = (us[j][0][0], struct.pack('<I', v))
    kl_fa.edit(sc, k, None, fn)


_stock = {}

def stock_scene(level):
    if level not in _stock:
        _stock[level] = J.Scene.load(level)
    return _stock[level]


def host_sets(s_name):
    """{kind: voice slots} the systems level's own characters use most (offsets into ITS bank,
    which a merged bank keeps in place)."""
    by = collections.defaultdict(collections.Counter)
    for _k, kind, slots, _a in characters(stock_scene(s_name)):
        if any(slots):
            by[kind][slots] += 1
    return {kind: c.most_common(1)[0][0] for kind, c in by.items()}


def give_voices(sc, ks, s_name, snd, log=print, prefer='map'):
    """A voice set for every soldier and civilian among ks that has none. prefer 'map': the set
    most of its kind have on the map itself (already in the merged bank: the Japanese guards'
    for a mute Japanese guard), else the systems level's; 'host': the other way round.
    ASSUMPTION: a soldier without a voice is meant to sound like the others of its level.
    A woman gets a woman's set or none (F07 has only male civilians). -> Counter"""
    st, kinds = collections.Counter(), ('soldier', 'civilian', 'woman')
    cs_ = [c for c in characters(sc, ks) if c[1] in kinds]
    defs = {o for o, t in kl_snd.Snd('dd', snd).kind.items() if t == 5}
    mine = collections.defaultdict(collections.Counter)
    for _k, kind, slots, _a in cs_:
        if any(slots) and all(v in defs for v in slots if v):
            mine[kind][slots] += 1
    mine = {kind: c.most_common(1)[0][0] for kind, c in mine.items()}
    host = host_sets(s_name)
    for k, kind, slots, _a in cs_:
        if any(slots):
            st['map characters with their own voice set'] += 1
            continue
        pick = (mine.get(kind) or host.get(kind)) if prefer == 'map' else (host.get(kind) or mine.get(kind))
        if not pick:
            st['map characters left without a voice (%s: no set of that kind in either level)' % kind] += 1
            continue
        set_voice(sc, k, pick)
        st['map characters given a voice set (%s)' % ('the map\'s' if pick == mine.get(kind) else s_name + '\'s')] += 1
    if st:
        log('  kl_voice: %s' % dict(st))
    return st


def hero_voices(sc, snd, whd, wav, ls, log=print, source='L01'):
    """EXPERIMENT (never heard): Kane's / Lynch's story voice sets on the eight heisters, by the
    animation set each already uses (Hero_01/03/05/07 Kane, 02/04/06/08 Lynch). The two
    definitions are appended from the story level `source` unless the bank has them (the second
    step of a chained build). Police players and bots stay as they are.
    ASSUMPTION: ZFFPlayer's bark code runs in a Fragile Alliance round too; stock never gives it
    a definition there. -> (.SND, .WHD, .WAV, Counter)"""
    st = collections.Counter()
    base = kl_snd.Snd('dd', snd, ls).walk()
    find = lambda S: {a: o for o in S.tables.get(5, []) for a, tail in HERO_DEFS.items() if S.name(o).lower().endswith(tail)}
    have = find(base)
    if len(have) < len(HERO_DEFS):
        src = kl_snd.bank(source)
        theirs = find(src)
        if len(theirs) < len(HERO_DEFS):
            raise ValueError('%s has no kane_default / lynch_default' % source)
        snd, whd, wav, omap = kl_snd.merge(base, src, whd, wav, kl_snd.read(kl_snd.beside(source, '.WHD')),
                                           kl_snd.read(kl_snd.beside(source, '.WAV')), set(theirs.values()),
                                           log=lambda *_a: None, stats=st)
        have = {a: omap[o] for a, o in theirs.items()}
        st = collections.Counter({'story voice sets: ' + k: v for k, v in st.items() if k.startswith(('added', 'reused', 'stream', 'in-memory'))})
    for k, kind, slots, anim in characters(sc):
        if kind == 'heister' and not any(slots) and anim in have:
            set_voice(sc, k, (have[anim], 0, 0)); st['heisters given the story voice set of %s' % anim] += 1
    log('  kl_voice: %s' % dict(st))
    return snd, whd, wav, st


# ------------------------------------------------------------------ the settings' lines
def settings(sc, ks=None):
    """[(node, controller index, values)] of the Fragile Alliance settings (on nodes ks only)."""
    return [c for c in kl_fa.controllers(sc, SETTINGS) if (ks is None or c[0] in set(ks)) and len(c[2]) == 340]


def heard(key, flag, leaves):
    """What kl2.exe finds for line key `key` in a field with `flag`: [sound ids] of the leaves it
    looks up (0x6b8710): flag 1 -> K_C1..K_C9, flag 0 -> K. leaves: {lower key: sound id or 0}."""
    k = key.strip('/').lower()
    names = ['%s_c%d' % (k, i) for i in range(1, VARIANTS + 1)] if flag else [k]
    return [leaves[n] for n in names if leaves.get(n)]


def fill_lines(sc, ks, s_name, known, log=print):
    """The map's settings (a Dead Men Fragile Alliance level's, after kl_convert's field table):
    a line field that is empty, or names a key neither level's .LOC has, takes the systems
    level's key of that field. ASSUMPTION: Dog Days' line is better than none for an event Dead
    Men had no line for (three minutes left, second boarding call ...). known: lower-case keys
    of both .LOC files. -> Counter"""
    st, mine = collections.Counter(), settings(sc, ks)
    if not mine:
        return st
    host = settings(stock_scene(s_name))
    if len(host) != 1:
        return st
    theirs, fields = host[0][2], line_fields()
    for k, i, v in mine:
        new = {}
        for f in fields:
            ok = v[f] and (v[f].strip('/').lower() in known or v[f].strip('/').lower() + '_c1' in known)
            if not ok and theirs[f]:
                new[f] = theirs[f]
                st['line fields that were %s: %s\'s key' % ('empty' if not v[f] else 'no .LOC key', s_name)] += 1
        def fn(us):
            for f, s in new.items():
                us[f] = [kl_fa._str(sc, s)]
        if new:
            kl_fa.edit(sc, k, i, fn)
    if st:
        log('  kl_voice: %s' % dict(st))
    return st


def variant_keys(sc, ks, known=None):
    """Lower-case keys in the per-character fields (flag 1) of the settings on nodes ks."""
    fields = line_fields()
    return {v[f].strip('/').lower() for _k, _i, v in settings(sc, ks) for f, (flag, _w) in fields.items() if flag and v[f]}


def loc_aliases(files, sc, ks, want):
    """files: {language: .LOC bytes} after kl_loc.graft_level; want: the grafted keys. Every
    grafted key that stands in a per-character field gets leaves K_C1..K_C9 with K's text and
    sound, so the line is found whichever heister says it (Dead Men recorded one voice).
    -> (files, leaves added per language)"""
    keys = {p for p in want if p.lower() in variant_keys(sc, ks)}
    out, n = {}, 0
    for lang, d in files.items():
        t = kl_loc.parse(d)
        if t is None or not keys:
            out[lang] = d; continue
        n = kl_loc.aliases(t, keys, VARIANTS)
        out[lang] = kl_loc.build(t)
    return out, n


# ------------------------------------------------------------------ census
def load(src):
    """-> (scene, walked bank, {.WHD offset: record}, {lower .LOC key: sound id}) of a built level
    archive (the .WHD beside it) or a stock Dog Days level name."""
    sc, snd, loc = kl_fa.load(src)
    if os.path.isfile(src):
        whd = kl_snd.read(src[:-4] + '.WHD')
    else:
        whd = kl_snd.read(kl_snd.beside(src, '.WHD'))
    leaves = {p.lower(): kl_loc.fields(n)[2] or 0 for p, n in kl_loc.leaves(kl_loc.parse(loc))}
    return sc, kl_snd.Snd('dd', snd).walk(), W.records('dd', whd), leaves


def census(src, log=None):
    """Counts of everything speech needs on a level. -> dict (flat: number or small dict)"""
    sc, S, recs, leaves = load(src)
    defs, out = definitions(S), collections.OrderedDict()
    who = collections.defaultdict(collections.Counter)
    used = collections.Counter()
    for k, kind, slots, _anim in characters(sc):
        ok = [v for v in slots if v in defs]
        who[kind]['stray voice reference' if any(v and v not in defs for v in slots) else 'with a voice set' if ok else 'without'] += 1
        used.update(ok)
    out['characters'] = {kind: dict(c) for kind, c in sorted(who.items())}
    table = {}
    for o, n in used.most_common():
        name, slots = defs[o]
        clips = collections.Counter(codec(S, recs, x) for x in set(sounds_below(S, o)))
        table[name.split('/')[-1]] = {'characters': n, 'slots': len(slots), 'filled': sum(1 for x in slots if x),
                                      'dog days events 27 28 29 34': sum(1 for i in (27, 28, 29, 34) if i < len(slots) and slots[i]),
                                      'clips': dict(clips)}
    out['voice sets in use'] = table
    st, silent = collections.Counter(), []
    for _k, _i, v in settings(sc):
        for f, (flag, _w) in sorted(line_fields().items()):
            if not v[f]:
                st['empty'] += 1
            elif any(x in S.kind for x in heard(v[f], flag, leaves)):
                st['heard (per character)' if flag else 'heard'] += 1
            else:
                st['SILENT'] += 1; silent.append((f, v[f]))
    out['line fields'] = dict(st)
    out['silent lines'] = silent
    # OnlineSpeakTrigger finds its line by sound name (kl_graft.mute_speech); OnlineSpeakPlayer's lookup was not read:
    # stock F07's names a key that exists only as _C1.._C8, so either form counts here
    key = lambda name, v: v[6] if name == 'OnlineSpeakTrigger' else v[1]
    out['speak triggers'] = dict(collections.Counter(
        'with its line' if any(x in S.kind for flag in (0, 1) for x in heard(key(name, v), flag, leaves)) else 'WITHOUT its line'
        for name in ('OnlineSpeakTrigger', 'OnlineSpeakPlayer') for _k, _i, v in kl_fa.controllers(sc, name)))
    out['speakers'] = sorted(sc.cls(k) for k in range(1, len(sc.nodes)) if (sc.cls(k) or '').startswith('ZSpeaker'))
    out['bank'] = {'sounds': len(S.tables.get(1, [])), 'waves': len(S.tables.get(4, [])), 'definitions': len(defs), '.LOC keys': len(leaves),
                   'spoken .LOC keys': sum(1 for v in leaves.values() if v in S.kind)}
    out['clips by format'] = dict(collections.Counter(codec(S, recs, o) for o, t in S.kind.items() if t == 1))
    if log:
        show(out, log)
    return out


def show(c, log=print):
    for k, v in c.items():
        if k == 'silent lines':
            log('  silent lines: %d%s' % (len(v), ''.join('\n      field %d  %s' % x for x in v[:6]) + ('\n      ...' if len(v) > 6 else '')))
        elif k == 'voice sets in use':
            log('  voice sets in use:')
            for name, d in v.items():
                log('      %-28s %2d characters, %d slots (%d filled, %d of Dog Days\' events 27 28 29 34), clips %s' % (
                    name, d['characters'], d['slots'], d['filled'], d['dog days events 27 28 29 34'], d['clips']))
        else:
            log('  %s: %s' % (k, v))


# ------------------------------------------------------------------ tests
def test(log=print):
    """The facts the module rests on, re-measured on the stock files. -> number of failures"""
    bad = 0
    # 1. LINES against the nine stock levels: a per-character field's key has _C<n> leaves and no plain one
    fields = line_fields()
    agree = collections.Counter()
    for lv in ['F0%d' % i for i in range(1, 10)]:
        sc, snd, loc = kl_fa.load(lv)
        keys = {p.lower() for p, _n in kl_loc.leaves(kl_loc.parse(loc))}
        for _k, _i, v in settings(sc):
            for f, (flag, _w) in fields.items():
                if not v[f]:
                    continue
                k = v[f].strip('/').lower()
                plain, var = k in keys, k + '_c1' in keys
                agree['flag %d: %s' % (flag, 'only _C<n>' if var and not plain else 'only plain' if plain and not var else
                                       'both' if plain else 'neither')] += 1
    log('settings line fields of F01..F09 by flag and what the .LOC holds: %s' % dict(sorted(agree.items())))
    wrong = agree['flag 1: only plain'] + agree['flag 0: only _C<n>']
    bad += bool(wrong)
    log('  %s' % ('LINES agrees with every stock level' if not wrong else 'LINES DISAGREES in %d fields' % wrong))
    # 2. slot counts and slot meaning of the NPC definitions of both games
    for game, n in (('dd', NPC_DD), ('dm', NPC_DM)):
        fam, levels = collections.defaultdict(collections.Counter), 0
        for lv in kl_snd.stock_levels(game):
            S = kl_snd.bank(lv, game); levels += 1
            for name, slots in definitions(S).values():
                if len(slots) != n:
                    continue
                for i, x in enumerate(slots):
                    if x:
                        fam[i][S.name(x).decode('latin1').split('/')[-2]] += 1
        log('%s: definitions of %d slots in %d banks: slot -> most common set folder' % (game, n, levels))
        log('  ' + ', '.join('%d %s' % (i, fam[i].most_common(1)[0][0]) for i in sorted(fam)))
    # 3. no Fragile Alliance heister has a voice set; the story players have
    for lv in ['F0%d' % i for i in range(1, 10)] + ['L01', 'L03']:
        c = collections.Counter((kind, bool(any(s))) for _k, kind, s, _a in characters(stock_scene(lv)) if 'player' in kind or kind == 'heister')
        log('%s players (kind, has a voice set): %s' % (lv, dict(c)))
    # 4. def_slots on the Dead Men definitions the six maps use
    for lv in ('M03_FA_A', 'M09_A', 'M09_B'):
        S = kl_snd.bank(lv, 'dm')
        for name, slots in definitions(S).values():
            new = def_slots(name, slots)
            if new:
                nm = lambda x: S.name(x).decode('latin1').split('/')[-1] if x else '-'
                log('%s %s: 27 <- %s, 28 <- %s, 29 <- %s, 34 <- %s' % (lv, name.split('/')[-1], nm(new[27]), nm(new[28]), nm(new[29]), nm(new[34])))
                bad += len(new) != NPC_DD
    log('problems: %d' % bad)
    return bad


def build(out=None, log=print):
    """The bank and Retomoto, each without and with the repairs (and with the heisters'
    experiment), into <out>/<name>/. Uses kl_maps (its folders, the campaign pre-pass, --author
    for Retomoto as the played build had). Nothing is installed. -> {name: census}"""
    import kl_maps
    from kl_port_check import workdir
    out = out or os.path.join(workdir(), 'build', 'voice')
    res, quiet = {}, lambda *_a: None
    jobs = (('before', None), ('after', True), ('after+heroes', {'heroes': True}))
    for tag, voice in jobs:
        kl_snd.VOICE = voice
        try:
            folder = os.path.join(out, tag)
            r = kl_maps.one(folder, 'F07', 'M03_FA_A', keep=True)
            res['bank ' + tag] = (r, os.path.join(folder, 'F07+M03_FA_A', kl_maps.SLOT + '_Main.zip'))
            kl_maps.PSEUDO.pop('R09', None)
            r = kl_maps.chain(folder, 'F07', 'M09_B', 'M09_A', keep=True, author=True)
            res['retomoto ' + tag] = (r, os.path.join(folder, 'R09+M09_A (R09 = F07+M09_B)', kl_maps.SLOT + '_Main.zip'))
        finally:
            kl_snd.VOICE = None
            kl_maps.PSEUDO.pop('R09', None)
    cens = {}
    for name, (r, path) in res.items():
        log('\n===== %s: %s, %s s, problems %s' % (name, 'built' if r.get('ok') else 'FAILED ' + str(r.get('error')), r.get('seconds'), r.get('problems')))
        if r.get('ok') and os.path.isfile(path):
            log('  ' + path)
            cens[name] = census(path, log)
    return cens


def main(a):
    if a[:1] == ['test']:
        return test()
    if a[:1] == ['census'] and len(a) > 1:
        census(a[1], print); return 0
    if a[:1] == ['build']:
        build(a[1] if len(a) > 1 else None); return 0
    if a[:1] == ['defs'] and len(a) > 1:
        S = kl_snd.bank(a[1])
        for o, (name, slots) in sorted(definitions(S).items(), key=lambda x: x[1][0]):
            print('%s  %d slots' % (name, len(slots)))
            for i, x in enumerate(slots):
                if x:
                    print('   %2d %s (%d sounds)' % (i, S.name(x).decode('latin1'), len(set(sounds_below(S, x)))))
        return 0
    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
