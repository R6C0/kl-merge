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
    python kl_voice.py variety <level|zip>   per voice set and slot: distinct clips, silent members, mode
    python kl_voice.py build2 [<out>]        the bank and Retomoto without / with the repairs into
                                             <out> (default <work>/build/voice2), per-slot clip counts
                                             before / after, file sizes. Nothing is installed.
    python kl_voice.py said <level|zip> <key> ...   plain line keys as one lookup finds them: clip form, seconds
    python kl_voice.py talk <folder> [<file.str>]   the check of tools/kl_fa_talk.py on a build folder
    python kl_voice.py heisters <level|zip> [merged|dd]
                                             CHECK: the heisters' lines as kl2.exe looks them up, per
                                             heister, clip formats, stream file, AI heisters' character
                                             index (re/bots_voice.md). Exit code = CRASH findings.

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

  6 Repetition (the owner's first round on Retomoto: 'the soldiers replay the same thing too
    many times'). EXE: a set picks its member in 0x4ddb10 by set +0x20: 0 = in order, 1 = at
    random, 2 = a bag - a 32-bit mask at set +0x1c of the members that had their turn, a random
    one of the others is taken, the mask is cleared when one is left (a set of 1 is played as
    mode 0, above 32 members as mode 1). Dead Men has the same routine (0x5d3d30) and the merge
    copies the set record whole, so NOTHING IS LOST IN THE MERGE: the played bank holds the 73
    / 63 clips Dead Men's own bank holds, in mode 2. The state lives in the set, so it is shared
    by every character with that voice. The cause is the content: Dead Men's Japanese voice
    has 1 clip for 'enemy close' and 'heavy fire', 2 for 'suppress response' and 'man down',
    none for 'enemy spotted' (Dog Days' police_01: 4, 2, 10, 12, 12), the same 6 police
    warnings serve 'first contact' (3) AND slot 28, which Dog Days fires as 'advance' - and
    every soldier of a Dead Men level has the one set (Dog Days gives each three: fields 0..2).
    The only gate on a bark is per character (0x763200: not before its own last clip ended, by
    the wave's seconds at wave +0x18). No field of a set or sound is a cooldown. planner()
    therefore widens the thin slots from the neighbouring Dead Men sets and the second Japanese
    voice (guard_japanese_male_01, in both M09 banks), without a clip in two of those slots,
    and pads every speech set to `cycle` members with a silent sound: no line comes again
    before `cycle` calls of its event.
  7 Streamed ADPCM (all the Japanese shouted lines). The buffer fill has the path (5), but no
    stock Dog Days clip is one, so it has never been proven to play. stream_clip() takes the
    clip's blocks out of Dead Men's PC_Def.str and merge() stores them in the level's .WAV as
    an in-memory ADPCM record - same codec, same 0x400 blocks, the form of 643 of F07's 729
    in-memory records. Nothing is decoded or re-encoded.

WHAT IS A GUESS (each marked ASSUMPTION where the code makes it)
  - planner(): which Dead Men sets may fill which Dog Days event (NPC_POOL, by set names), and
    that a silent turn is better than the same line again (`cycle`).
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
# Dog Days slot <- where its clips come from, in order: ('own', Dead Men slot of the same definition)
# or ('alt', part of a set name in the second voice of that language, ALT). The first source is the
# slot's own; a clip that another slot of this table already has is left out of the later ones, so
# no line serves two events - unless the slot would stay empty (then its first source that holds
# anything is taken whole).
# ASSUMPTION, by set names only: Dog Days 3 first contact, 4 enemy close, 5 enemy spotted, 7 suppress
# response, 8 suppress, 13 heavy fire, 18 / 28 / 29 advance, 25 man down, 27 battle cries, 34 alert;
# Dead Men 9 / 11 cover responses, 10 / 12 cover talk, 15 team disruption + retreat, 16 panic, 17
# advance response + police orders, 28 police warning, 30 'no access' (a guard sending you away);
# second Japanese voice: attacks, 'fight breakout', 'break down door' (the shouted ones; its hurt /
# panic / begging sets are not used).
NPC_POOL = {3: (('own', 3),), 4: (('own', 4), ('alt', 'attack')), 5: (('own', 5), ('own', 10), ('own', 12)),
            7: (('own', 7), ('own', 9), ('own', 11)), 8: (('own', 8),), 13: (('own', 13), ('own', 15)), 18: (('own', 18),),
            25: (('own', 25), ('own', 16)), 27: (('alt', 'fightbreakout'), ('own', 28), ('own', 18)),
            28: (('own', 17), ('own', 18)), 29: (('alt', 'breakdowndoor'), ('own', 17), ('own', 18)),
            34: (('own', 30), ('own', 3), ('own', 5), ('own', 4))}
ALT = {'/jpn_': 'guard_japanese_male_01#def'}                # part of a definition's name -> the second voice in its bank
SPEECH_FROM = 2                             # slots 0 pain and 1 die are left as they are
INMEM_MAX = 1 << 20                         # a streamed ADPCM clip above this stays streamed (none on the six maps)
OPTIONS = dict(defs=True,                   # Dead Men character definitions in Dog Days' slot order
               variety=True,                # ... with the thin slots widened (NPC_POOL) instead of the plain def_slots
               cycle=8,                     # every speech set padded with silence to this many members (0 = no padding)
               inmem=True,                  # streamed ADPCM clips into the level's .WAV
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


def clip_key(S, o):
    """What tells two sounds with the same recording apart from two recordings: the wave's file name."""
    w = u32(S.b, o + 0x14)
    return kl_snd.cs(S.b, u32(S.b, w + 8)).lower() if w and w < S.T and u32(S.b, w + 8) else S.name(o).lower()


def planner(src, opt=None):
    """-> kl_snd.merge's `defs` hook for source bank src (walked), or None when the options ask
    for nothing. A 31-slot Dead Men voice definition comes out with Dog Days' 35 slots:
    variety off = def_slots() (whole Dead Men sets moved); on = the slots of NPC_POOL are sets
    made here (kl_snd.Pool) from the clips of several Dead Men sets, no clip in two of them.
    cycle = n: every speech set of the definition with fewer than n clips is padded with a
    silent sound to n members, so the bag (mode 2, kl2 0x4ddb10) gives each line once in n
    calls. A slot whose set needs neither keeps Dead Men's own set object."""
    o_ = options(opt if opt is not None else True)
    if not o_['defs']:
        return None
    cycle = min(int(o_['cycle'] or 0), kl_snd.BAG_MAX)
    if not o_['variety'] and not cycle:
        return def_slots
    by_tail = {name.rsplit('/', 1)[-1]: slots for name, slots in definitions(src).values()}
    made = {}                               # (clips, pad) -> Pool: the same pool is one set (jpn_guard_01 and jpn_bouncer_01)

    def clips(x):
        """The sounds below set x, a recording once; None if a sequence is among them (left alone)."""
        if not x or src.kind.get(x) != 2:
            return None if x else []
        out, seen = [], set()
        for s in sounds_below(src, x):
            if clip_key(src, s) not in seen:
                seen.add(clip_key(src, s)); out.append(s)
        return out

    def alt_sets(name):
        tail = next((v for k, v in ALT.items() if k in name), None)
        found = {}
        for x in by_tail.get(tail, ()) if tail else ():
            stack = [x]
            while stack:
                y = stack.pop()
                if y and src.kind.get(y) == 2 and y not in found:
                    found[y] = src.name(y).decode('latin1').rsplit('/', 1)[-1]
                    n, c = u16(src.b, y + 0x18), u32(src.b, y + 0x14)
                    stack += [k for k in (struct.unpack_from('<%dI' % n, src.b, c) if c else ()) if src.kind.get(k) == 2]
        return found

    def pool(name, i, mem, own):
        """own: the Dead Men set this slot had (0 = none). -> what the slot gets."""
        pad = max(0, cycle - len(mem)) if mem else 0
        if not mem:
            return 0
        if not pad and own and clips(own) == mem:
            return own
        key = (tuple(mem), pad)
        if key not in made:
            made[key] = kl_snd.Pool(b'audio:dialog/kl_merge/' + name.rsplit('/', 1)[-1].split('#')[0].encode('latin1') + b'_slot%02d#set' % i, mem, pad)
        return made[key]

    def plan(name, slots):
        if len(slots) != NPC_DM:
            return None
        name = name.decode('latin1') if isinstance(name, bytes) else name
        base = def_slots(name, slots)
        if any(clips(x) is None for x in slots):            # ASSUMPTION: a voice set built on sequences is not to be re-cut (none on the six maps)
            return base
        out = list(base)
        if o_['variety']:
            alts = alt_sets(name)
            def source(kind, what):
                if kind == 'own':
                    return clips(slots[what]) or []
                got, seen = [], set()
                for y, nm in sorted(alts.items(), key=lambda kv: kv[1]):
                    if what in nm:
                        for s in clips(y) or []:
                            if clip_key(src, s) not in seen:
                                seen.add(clip_key(src, s)); got.append(s)
                return got
            used, mem, lent = set(), {}, {}
            for i, srcs in NPC_POOL.items():                # first every slot's own source ...
                mem[i] = [s for s in source(*srcs[0]) if clip_key(src, s) not in used]
                used.update(clip_key(src, s) for s in mem[i])
            for i, srcs in NPC_POOL.items():                # ... then what the others left
                for kw in srcs[1:]:
                    add = [s for s in source(*kw) if clip_key(src, s) not in used]
                    mem[i] += add; used.update(clip_key(src, s) for s in add)
                    if add and kw[0] == 'own' and kw[1] not in NPC_POOL:
                        lent[kw[1]] = i                     # that Dead Men slot's event now draws from the same bag
            for i, srcs in NPC_POOL.items():
                if mem[i]:
                    out[i] = pool(name, i, mem[i][:kl_snd.BAG_MAX], slots[i] if srcs[0] == ('own', i) else 0)
            for j, i in lent.items():
                out[j] = out[i]
            for i in range(SPEECH_FROM, len(out)):          # the slots the table does not name: Dead Men's set, padded
                if out[i] and not isinstance(out[i], kl_snd.Pool) and i not in NPC_POOL:
                    out[i] = pool(name, i, clips(out[i]), out[i])
            for i, srcs in NPC_POOL.items():                # nothing left for it: the set of the first source that has one, shared
                if not mem[i]:
                    kw = next((kw for kw in srcs if source(*kw)), None)
                    out[i] = 0 if kw is None else out[kw[1]] if kw[0] == 'own' else pool(name, i, source(*kw)[:kl_snd.BAG_MAX], 0)
        for i in range(SPEECH_FROM, len(out)):              # variety off: every speech set as it is, padded
            if out[i] and not isinstance(out[i], kl_snd.Pool):
                out[i] = pool(name, i, clips(out[i]), out[i])
        return out
    return plan


_dm_str = {}

def stream_clip(f, name=None):
    """kl_snd.merge's `inmem` hook: the bytes of the streamed mono IMA ADPCM clip with Dead Men
    .WHD record f, read from Dead Men's PC_Def.str (the block at the record's offset, behind its
    0x1000-byte LIP block if it has one), or None when they do not look like 0x400-byte ADPCM
    blocks (predictor, step index <= 88, a zero byte). The same bytes an in-memory ADPCM record
    holds (block 0x400, 0x7f9 samples a block), so nothing is re-encoded."""
    import kl_str
    if f['ch'] != 1 or f['block'] != 0x400 or f['size'] % 0x400 or not 0 < f['size'] <= INMEM_MAX:
        return None
    if 'f' not in _dm_str:
        _dm_str['f'] = open(kl_str.paths()['dm'], 'rb')
    fh = _dm_str['f']
    fh.seek(f['off'])
    if fh.read(4) != b'LIP ':
        fh.seek(f['off'])
    else:
        fh.seek(f['off'] + kl_str.LIP)
    data = fh.read(f['size'])
    if len(data) != f['size'] or any(data[b + 2] > 88 or data[b + 3] for b in range(0, len(data), 0x400)):
        return None
    return data


def variety(src, log=None):
    """Per voice definition the characters of a level use (a built archive or a stock Dog Days
    level): {name: {slot: (distinct clips, silent members, mode, by format)}}."""
    sc, S, recs, _leaves = load(src)
    defs, used = definitions(S), collections.Counter()
    for _k, _kind, slots, _a in characters(sc):
        used.update(v for v in slots if v in defs)
    out = collections.OrderedDict()
    for o, n in used.most_common():
        name, slots = defs[o]
        if len(slots) not in (NPC_DM, NPC_DD):
            continue
        row, every = {}, set()
        for i, x in enumerate(slots):
            if not x:
                continue
            ss = sounds_below(S, x)
            real = [s for s in ss if S.name(s) != kl_snd.SILENCE]
            every.update(clip_key(S, s) for s in real)
            row[i] = (len({clip_key(S, s) for s in real}), sum(1 for s in _members(S, x) if S.kind.get(s) == 1 and S.name(s) == kl_snd.SILENCE),
                      u32(S.b, x + 0x20) if S.kind.get(x) == 2 else -1, dict(collections.Counter(codec(S, recs, s) for s in set(real))))
        out['%s (%d characters, %d distinct clips)' % (name.split('/')[-1], n, len(every))] = row
    if log:
        for name, row in out.items():
            log('  %s; slot:clips+silent members' % name)
            log('      ' + '  '.join('%d:%d%s' % (i, v[0], '+%ds' % v[1] if v[1] else '') for i, v in sorted(row.items())))
    return out


def _members(S, x):
    n, c = u16(S.b, x + 0x18), u32(S.b, x + 0x14)
    return struct.unpack_from('<%dI' % n, S.b, c) if c and S.kind.get(x) == 2 else ()


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


# ------------------------------------------------------------------ the heisters' lines (re/bots_voice.md)
# How a line gets its voice (EXE, kl2 0x421c70, the Arcade branch): a per-character line (flag 1) holds ten entries
# K_C1..K_C9, K_R_C9 (0x6b8710); the one spoken is entry [rules + 0x33e + speaker's player slot] (0x6ae750), and
# entry 0 (K_C1) when that one is empty. An AI heister's table byte is name[0x12] - '1' of its group
# ('Glazer_Bodyguard_0N', 0x588980); speaker -6 takes entry 8 (K_C9, Glazer); the list accessor 0x51ab20 asserts
# (int3) on an index outside 0..9. OnlineSpeakPlayer looks its key up PLAIN, once (0x8cb6e0).
BOT_DIGIT = 0x12                            # index of the character digit in an AI heister's group name
HEISTERS = 8                                # K_C1 .. K_C8; K_C9 is Glazer's


def _clip(S, recs, leaves, name, clips):
    """-> (state, recording) of .LOC leaf `name`: state = the clip's format (codec()), or why the
    exe finds nothing; recording = clip_key (tells one voice aliased eight times from eight)."""
    if name not in leaves:
        return 'no leaf', None
    sid = leaves[name]
    if not sid or S.kind.get(sid) != 1:
        return 'leaf without a sound in the bank', None
    c, w = codec(S, recs, sid), u32(S.b, sid + 0x14)
    f = recs.get(u32(S.b, w + 0x14)) if w and w < S.T else None
    if f is None:
        return c, None
    off = f['off'] | (f['offhi'] << 32)
    if f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE and clips is not None and off not in clips:
        return c + ', NOT IN THE STREAM FILE', None
    return c, clip_key(S, sid)


def heisters(src, log=None, stream='merged'):
    """CHECK (re/bots_voice.md): what the heisters - the player's character and the AI heisters -
    can say on a built level archive or a stock level. Counts every line key of the settings the
    way kl2.exe looks it up, per heister, with the clip's format and whether a streamed clip is a
    clip of the stream file (`stream`: 'merged' = the work folder's PC_Def.str, 'dd' = the game's,
    None = not checked). -> dict; ['findings'] = [(severity, text)], severity CRASH / SILENT / NOTE.
    Proven on stock F07 (0 CRASH, the one SILENT stock has itself) and the five builds of 2026-10-10."""
    sc, S, recs, leaves = load(src)
    try:
        clips = kl_snd.stream_index(kl_snd.stream_file(stream))[1] if stream else None
    except (OSError, ValueError):
        clips = None
    out, find = collections.OrderedDict(), []
    st = settings(sc)
    out['settings objects'] = len(st)
    per, c9, plain, recn, own = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    host_keys = collections.Counter()
    for _k, _i, v in st:
        for f, (flag, _prio) in sorted(line_fields().items()):
            if not v[f]:
                continue
            k = v[f].strip('/').lower()
            part = k.split('/')
            if len(part) > 2 and part[0] == 'multiplayer' and len(part[1]) == 3 and part[1][0] == 'f' and part[1][1:].isdigit():
                host_keys[part[1].upper()] += 1
            if not flag:
                s, _c = _clip(S, recs, leaves, k, clips)
                plain[s] += 1
                if not s.startswith(('stream', 'memory')) or 'NOT IN' in s:
                    find.append(('SILENT', 'field %d %s: %s' % (f, v[f], s)))
                continue
            ss = [_clip(S, recs, leaves, '%s_c%d' % (k, i), clips) for i in range(1, VARIANTS + 1)]
            for s, _c in ss[:HEISTERS]:
                per[s] += 1
            c9[ss[HEISTERS][0]] += 1
            n = len({c for _s, c in ss[:HEISTERS] if c})
            recn[n] += 1
            own['eight voices (Dog Days)' if n == HEISTERS else 'one voice for all eight (a Dead Men line)' if n == 1 else
                'none' if n == 0 else '%d voices' % n] += 1
            bad = [i + 1 for i, (s, _c) in enumerate(ss[:HEISTERS]) if not s.startswith(('stream', 'memory')) or 'NOT IN' in s]
            if bad and ss[0][1] is None:
                find.append(('SILENT', 'field %d %s: no clip for heister 1, the fallback of all (K_C1): %s' % (f, v[f], ss[0][0])))
            elif bad:
                find.append(('NOTE', 'field %d %s: heisters %s have no clip of their own and speak with heister 1\'s' % (f, v[f], bad)))
    out['per-character keys (flag 1)'] = sum(recn.values())
    out['  key x heister pairs by clip'] = dict(per)
    out['  keys by who recorded them'] = dict(own)
    out['  Glazer (K_C9) by clip'] = dict(c9)
    out['plain keys (flag 0) by clip'] = dict(plain)
    if host_keys:
        out['keys of a stock level\'s own folder'] = dict(host_keys)
    # speech controllers: OnlineSpeakPlayer = one plain lookup per key (0x8cb6e0)
    for _k, _i, v in kl_fa.controllers(sc, 'OnlineSpeakPlayer'):
        for key in [x for x in v[1:3] if isinstance(x, str) and x]:
            s, _c = _clip(S, recs, leaves, key.strip('/').lower(), clips)
            out.setdefault('OnlineSpeakPlayer keys', collections.Counter())[s] += 1
            if not s.startswith(('stream', 'memory')):
                find.append(('SILENT', 'OnlineSpeakPlayer %s: %s (looked up plain; %s)' % (
                    key, s, 'it exists as _C1.. only, as in stock' if key.strip('/').lower() + '_c1' in leaves else 'no such key')))
    if 'OnlineSpeakPlayer keys' in out:
        out['OnlineSpeakPlayer keys'] = dict(out['OnlineSpeakPlayer keys'])
    # the people: voice sets of heisters / AI heisters, and the AI heisters' character digit
    who, digits = collections.defaultdict(collections.Counter), collections.Counter()
    defs = definitions(S)
    for k, kind, slots, _anim in characters(sc):
        if kind in ('heister', 'bot', 'police player'):
            who[kind]['with a voice set' if any(v in defs for v in slots) else 'no voice set (as stock)'] += 1
        if kind == 'bot':
            name = sc.names[sc.parent[k]] if sc.parent[k] > 0 else ''
            d = ord(name[BOT_DIGIT]) - ord('1') if len(name) > BOT_DIGIT else None
            digits[d] += 1
            if d is None or not 0 <= d < VARIANTS + 1:
                find.append(('CRASH', 'AI heister %s (group \'%s\'): character index %s from name[0x12] - \'1\'%s: outside the ten '
                                      'entries of a line, int3 at kl2 0x51ab2d when it first speaks' % (
                                          sc.path[k], name, d, '' if d is not None else ' (the name is shorter: the byte read lies behind it)')))
            elif d >= HEISTERS:
                find.append(('NOTE', 'AI heister %s speaks entry %d (Glazer\'s or the radio one), empty for most keys: heister 1\'s voice instead' % (sc.path[k], d)))
    for d, n in digits.items():
        if d is not None and n > 1:
            find.append(('NOTE', '%d AI heisters share character index %s: the same voice' % (n, d)))
    out['people'] = {kind: dict(c) for kind, c in sorted(who.items())}
    out['AI heisters by character index'] = {('none' if d is None else d): n for d, n in sorted(digits.items(), key=lambda x: (x[0] is None, x[0] or 0))}
    # Dead Men soldier definitions left in Dead Men's slot order = the voice repairs were off at the build
    old = sorted({defs[v][0].split('/')[-1] for _k, kind, slots, _a in characters(sc) if kind == 'soldier' for v in slots
                  if v in defs and len(defs[v][1]) == NPC_DM})
    if old:
        find.append(('NOTE', 'soldier voice sets still in Dead Men\'s 31-slot order (built with kl_snd.VOICE off: no battle cry / '
                             'advance / alert, thin slots repeat - re/voice.md 7): %s' % ', '.join(old)))
    out['findings'] = find
    if log:
        log('heisters\' lines of %s' % src)
        for k, v in out.items():
            if k != 'findings':
                log('  %s: %s' % (k, v))
        sev = collections.Counter(s for s, _t in find)
        log('  findings: %s' % (dict(sev) or 'none'))
        for s, t in find:
            log('    %-6s %s' % (s, t))
    return out


# ------------------------------------------------------------------ tests
def said(src, keys, stream='merged', log=None):
    """CHECK (re/talk.md): PLAIN line keys the way a single lookup finds them (kl2 0x828fa0: OnlineSpeakPlayer's
    key, a key the hook part kltalk says) on a built level archive or a stock Dog Days level. stream: 'merged' /
    'dd' (kl_snd.stream_file), a path to a stream file, or None = streamed clips not looked up.
    -> {key: (state, seconds)}; state as _clip() gives it ('stream vorbis', 'memory adpcm', 'no leaf', ...,
    with ', NOT IN THE STREAM FILE'), seconds None when the exe would find no clip."""
    sc, S, recs, leaves = load(src)
    try:
        clips = kl_snd.stream_index(stream if stream and os.path.isfile(stream) else kl_snd.stream_file(stream))[1] if stream else None
    except (OSError, ValueError):
        clips = None
    out = collections.OrderedDict()
    for key in keys:
        k = key.strip('/').lower()
        st, rec = _clip(S, recs, leaves, k, clips)
        secs = None
        if rec is not None:
            f = recs[u32(S.b, u32(S.b, leaves[k] + 0x14) + 0x14)]
            secs = f['samples'] / float(f['rate'] or 1)
        out[key] = (st, secs)
        if log:
            log('  %-34s %s  %s' % (st, '%6.2f s' % secs if secs is not None else '   -    ', key))
    return out


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


def build2(out=None, log=print, maps=('bank', 'retomoto')):
    """The bank and Retomoto without and with the repairs into <out>/<before|after>/ (default
    <work>/build/voice2), then per voice set and slot the distinct clips before / after and the
    sizes of the files a level loads. Nothing is installed. -> {name: (result, archive)}"""
    import kl_maps
    from kl_port_check import workdir
    out = out or os.path.join(workdir(), 'build', 'voice2')
    res = {}
    for tag, voice in (('before', None), ('after', True)):
        kl_snd.VOICE = voice
        try:
            folder = os.path.join(out, tag)
            if 'bank' in maps:
                r = kl_maps.one(folder, 'F07', 'M03_FA_A', keep=True)
                res['bank ' + tag] = (r, os.path.join(folder, 'F07+M03_FA_A', kl_maps.SLOT + '_Main.zip'))
            if 'retomoto' in maps:
                kl_maps.PSEUDO.pop('R09', None)
                r = kl_maps.chain(folder, 'F07', 'M09_B', 'M09_A', keep=True, author=True)
                res['retomoto ' + tag] = (r, os.path.join(folder, 'R09+M09_A (R09 = F07+M09_B)', kl_maps.SLOT + '_Main.zip'))
        finally:
            kl_snd.VOICE = None
            kl_maps.PSEUDO.pop('R09', None)
    for name, (r, path) in res.items():
        log('\n===== %s: %s, %s s, problems %s' % (name, 'built' if r.get('ok') else 'FAILED ' + str(r.get('error')), r.get('seconds'), r.get('problems')))
        if r.get('ok') and os.path.isfile(path):
            log('  ' + path)
            c = census(path)
            log('  characters: %s' % c['characters'])
            log('  bank: %s' % c['bank'])
            log('  clips by format: %s' % c['clips by format'])
            variety(path, log)
            log('  sizes: %s' % ', '.join('%s %d' % (e, os.path.getsize(path[:-4] + e)) for e in ('.zip', '.WHD', '.WAV')))
    return res


def main(a):
    if a[:1] == ['test']:
        return test()
    if a[:1] == ['variety'] and len(a) > 1:
        variety(a[1], print); return 0
    if a[:1] == ['build2']:
        build2(a[1] if len(a) > 1 else None); return 0
    if a[:1] == ['census'] and len(a) > 1:
        census(a[1], print); return 0
    if a[:1] == ['heisters'] and len(a) > 1:
        r = heisters(a[1], print, stream=a[2] if len(a) > 2 else 'merged')
        return sum(1 for s, _t in r['findings'] if s == 'CRASH')
    if a[:1] == ['said'] and len(a) > 2:
        r = said(a[1], a[2:], log=print)
        return sum(1 for st, secs in r.values() if secs is None)
    if a[:1] == ['talk'] and len(a) > 1:                 # the lines of tools/kl_fa_talk.py (KLTalk.ini beside the archive)
        import kl_fa_talk
        return sum(1 for s, _t in kl_fa_talk.check(a[1], a[2] if len(a) > 2 else None)[0] if s == 'FAIL')
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
