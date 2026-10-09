#!/usr/bin/env python3
"""
Kane & Lynch .SND (the sound project of a level, a pointer image): walker, bank merge, and the
sound side of a graft. Spec with the evidence: re/audio.md. Both games.

    python kl_snd.py test [quick]        the selftest below (quick: no walk of all 41 banks)
    python kl_snd.py walk <level>        item and pointer counts of one stock bank
    python kl_snd.py merge <S> <M>       trial merge with M's map roots -> <work>/build/audio/<S>+<M>/
                                         (files to look at; nothing is installed)

WHAT A GRAFTED LEVEL NEEDS (S = Dog Days systems level, M = map level of either game)
  Every sound reference of a level is a byte offset into that level's .SND: the .prp fields with
  type handler 70 / 46 (Dog Days; 65 / 45 in Dead Men) and the sound ids of the .LOC. So
  - S's bank is the base and keeps every byte below its first type table: S's nodes, S's .LOC
    and S's _LS bank stay valid untouched;
  - what M's map nodes name is appended behind (merge()), and those fields are rewritten through
    the offset map merge() returns (rewrite()).
  graft_audio() does all of it for kl_graft; see its docstring for the call.

FILE (pointers are file offsets, 0 = none; no relocation table)
  0x00  u32 T (trailer), u32 size, 3, 4;  0x10 stream file names, 16 bytes each (10 DD / 6 DM)
  ...   objects, strings, lists | material matrix | type tables | parameter tables | T trailer
  Trailer, H = T + 4 + 4 * streams rounded up to 8:
    T+0 matrix*, T+4 stream name*..., H+0 u64 build id of the stream file (kl2 0x67e8f8 refuses
    PC_Def.str when it differs: Dog Days 4c08b8d5, Dead Men 46e11c9f), H+8 group*, H+0x10 25 x
    object count (index = type - 1), H+0x74 25 x type table*, H+0xd8 0, H+0xdc {count, table*}
    per parameter type 1..33 (DD) / 1..32 (DM).
  Object head: +0 type, +8 name* ('audio:<path>#<kind>'), +0xc u16 parameter count, +0x10
  parameter list*. Types: 1 sound (0x34 DD / 0x30 DM; +0x14 wave*, 0xfffffffe = in the _LS bank),
  2 set (+0x14 list*, +0x18 n), 3 seq (+0x14 events*: {kind, time, target}; target is an object
  for kinds 2 4 5 6), 4 wave, 5 def (list), 7 roomeffect (0x50 DD / 0x70 DM, other content),
  0x12 objectproperty, 0x13 surfaceproperty, 0x17 group (+0x14 children*, +0x1c slots*, +0x3c
  display name*, +0x40 parent*). Parameter record {u32 type, ...} 0x10 bytes (types 5 0x1b 0x1d:
  0x20, 0x13: 0x30); type 0x12 +4 = group*, type 0x13 +0x1c = object*.
  Wave: first dword 4 = one .WHD record (0x20 bytes: +8 file name*, +0x14 .WHD offset); first
  dword 0 = streamed, +0xc u16 flags, bit 1 = localized: one 0x1c-byte record per language
  ({name*, flags, 0, .WHD offset, f32 seconds, 0, 0}; 9 in Dog Days, 5 in Dead Men, first five
  in the same order Eng Ger Fre Spa Ita). A .WHD offset is the record's offset - 4.
  _LS.SND (loading sounds, beside the archive): 16-byte header whose first dword = T of the
  level's .SND (40 of 40 stock pairs), then sound objects whose name and parameter list are
  offsets into the level's .SND.

MEASURED by `test` on this machine (2026-10-09)
  - 21 + 20 stock banks walk clean (0 unclaimed non-zero bytes, 0 overlap, 0 stray pointers) and
    round-trip (moved by 0x1230, re-walked, moved back: same bytes, items, pointers): Dog Days
    475,903 items / 1,251,457 pointers, Dead Men 392,937 / 882,228. Every Dog Days bank has
    nothing but tables and trailer behind its first type table (what merge() relies on).
  - F07 + F09 map (same game): 71 distinct references on 7,054 map nodes; 105 objects reused
    from F07, added 72 sounds 69 waves 16 sets 1 seq 2 defs 7 room effects, 64 in-memory records
    (8.4 MB) and 5 stream records; 457 fields rewritten, 1 kept (loading sound); sounds 4,569 ->
    4,641, waves 4,434 -> 4,503.
  - F07 + M01_FA_A map (Dead Men): 70 references on 7,720 map nodes + 134 voice-line sounds of
    141 .LOC keys the map's nodes name; added 270 sounds 268 waves 22 sets 3 seqs 1 def, 124
    in-memory records (2.5 MB), 144 stream records; 10 room effects -> 0; 98 parameters dropped;
    351 fields rewritten; sounds 4,569 -> 4,839, waves 4,434 -> 4,702 (ABOVE the stock maxima
    4,806 / 4,568: with loc=False it is 4,705 / 4,568).
  - Both: merged .SND walks clean under the Dog Days walker, stock bytes below the first type
    table unchanged, every wave reference (28,428 / 29,699) hits a .WHD record, every in-memory
    record (865 / 925) has its data, every added stream record is a clip of the merged
    PC_Def.str (build id 4c08b8d5 = the banks'), 0 clips missing.
  - The same for all 72 pairs S in F04..F09, M in the other eight Dog Days FA levels and the four
    Dead Men FA levels: 0 problems; never the same name with other content; largest tables
    5,128 sounds (F05 + F06), 4,858 waves (F04 + M03_FA_A).
  - kl_convert carries Dead Men's sound references into the Dog Days fields unchanged: every
    non-zero value on the converted map nodes of the four FA maps is an object of the Dead Men
    bank (or 0xffffffff); 14 / 12 / 50 / 45 references are lost with fields Dog Days lacks.

GUESSES (each is marked ASSUMPTION where the code makes it)
  - Dead Men sound -> Dog Days: the float Dog Days added at +0x1c is written 0.6 (most common
    stock value); the two bytes added at the end are 0.
  - Dead Men parameter types 3, 6, 7 are dropped (no stock Dog Days bank uses them; meaning
    unknown). No parameter type is understood except 0x12 (group).
  - GROUP: Dead Men mixer group -> Dog Days group, by name and meaning only.
  - A Dead Men room effect has no Dog Days form: references become 0 (no reverb).
  - A Dead Men localized wave has audio in the merged stream file only in English: all nine
    Dog Days language records name the English clip.
  - Object / surface properties are matched by name, a surface Dog Days lacks becomes 'default'.
  - New objects are appended to the type and parameter tables; what the engine does with the
    order of either table is not established.
  - Same game (M from Dog Days): an object S's bank holds under the same name with the same
    content is reused (F07 / F09: 5062 of 5161 names are common). Same name, other content =
    a second object under that name (0 in the test; whether the engine minds is not known).
  - The first dword of _LS.SND is set to the new T; whether the engine reads it is not known.

NEVER TRIED IN THE RUNNING GAME: all of it. No merged .SND / .WHD / .WAV, no grafted .LOC and no
patched _LS.SND has been loaded by kl2.exe. The first things to expect are listed in re/audio.md
section 10 (fixed pools: the largest stock bank has 4,806 sounds and 4,568 waves).
0xffffffff in a sound field = 'the sound of the _LS bank' (the map's Loading_Sound ZSNDOBJ in F09
and M01_FA_A). The slot keeps S's _LS bank, so the value stays; S's loading sound plays for M's map.
Weak evidence that the engine does not check the _LS header: the milestone A build in the F01 slot
ran F07's bank (T 0x2469d0) with stock F01's _LS.SND (first dword 0x24ec40) and left cleanly.
"""
import collections, glob, json, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_whd as W, kl_loc
from kl_port_check import find, workdir, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

NAMES = {1: 'sound', 2: 'set', 3: 'seq', 4: 'wave', 5: 'def', 7: 'roomeffect', 0x12: 'objectproperty',
         0x13: 'surfaceproperty', 0x17: 'group'}
GAME = {'dd': dict(streams=10, nparam=33, build=0x4c08b8d5,
                   sizes={1: 0x34, 2: 0x30, 3: 0x20, 4: 0x20, 5: 0x20, 7: 0x50, 0x12: 0x20, 0x13: 0x30, 0x17: 0x50}),
        'dm': dict(streams=6, nparam=32, build=0x46e11c9f,
                   sizes={1: 0x30, 2: 0x30, 3: 0x20, 4: 0x20, 5: 0x20, 7: 0x70, 0x12: 0x20, 0x13: 0x30, 0x17: 0x50})}
PARAM_SIZE = {5: 0x20, 0x1b: 0x20, 0x1d: 0x20, 0x13: 0x30}      # the others 0x10
NTYPES = 25
LS_WAVE, LS_SOUND = 0xfffffffe, 0xffffffff        # in a sound's wave pointer / in a type table: lives in the _LS bank
# re/<exe>.json type handler index of the two sound reference fields: any object / a definition
SOUND_TYPES = {'dd': (70, 46), 'dm': (65, 45)}
DROP_PARAMS = (3, 6, 7)                           # ASSUMPTION: Dead Men only, meaning unknown
NEW_FLOAT = 0.6                                   # ASSUMPTION: Dog Days sound +0x1c
# Dead Men mixer group -> Dog Days group (display names). ASSUMPTION: by meaning, read from neither exe
GROUP = {'Master': 'Master', 'Dialog': 'Dialog', 'DialogUser': 'Dialog_user', 'Music': 'Music', 'MusicUser': 'Music_User',
         'Ambient': 'Ambient', 'AmbientRAM': 'Ambient', 'AmbientUser': 'Ambient_User', 'Sfx': 'SFX', 'SfxUser': 'SFX_User',
         'SfxSuper': 'SFX_Special', 'Explosions': 'SFX_Explosions', 'Footsteps': 'SFX_Footstep', 'SfxImpacts': 'SFX_ImpactHit',
         'SfxShatter': 'SFX_Shatter', 'SfxShatterShellDrop': 'SFX_Weapons_ShellDrop', 'Weapon': 'SFX_weapons',
         'Vehicles': 'SFX_Vehicles', 'Chopper': 'SFX_Vehicles', 'Plane': 'SFX_Vehicles', 'Environment': 'SFX',
         'FlashBacks': 'SFX_CutScene'}
DEFAULT_SURFACE = b'audio:materials/surface/default#surfaceproperty'
NUL = bytes(1)
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]
u16 = lambda b, o: struct.unpack_from('<H', b, o)[0]
cs = lambda b, o: b[o:b.index(NUL, o)]


# ------------------------------------------------------------------ stock files
def game_dir(game):
    return find(*((DM_GUESSES, DM_EXE) if game == 'dm' else (DD_GUESSES, DD_EXE)))


def game_of(level):
    return 'dm' if level.startswith('M') else 'dd'


def level_zip(level, game=None):
    """Stock archive of a level folder ('F02', 'M01_FA_A'); a file moved to KL_PortBackup wins
    over what stands in its place (kl_prpjoin.level_zip)."""
    base = game_dir(game or game_of(level))
    for root in (os.path.join(base, 'KL_PortBackup'), base):
        hit = glob.glob(os.path.join(root, 'Scenes', 'Locations', level, '*_Main.zip'))
        if hit:
            return hit[0]
    raise FileNotFoundError(level)


def stock_levels(game):
    """Level folders of a game that hold a level archive."""
    root = os.path.join(game_dir(game), 'Scenes', 'Locations')
    return sorted(d for d in os.listdir(root) if glob.glob(os.path.join(root, d, '*_Main.zip')))


def beside(level, suffix, game=None):
    """Path of the stock file <archive name minus .zip><suffix> ('.WHD', '_LS.SND',
    '_LS_Default.WAV'), or None. A file moved to KL_PortBackup wins."""
    game = game or game_of(level)
    base = game_dir(game)
    stem = os.path.basename(level_zip(level, game))[:-4]
    for root in (os.path.join(base, 'KL_PortBackup'), base):
        p = os.path.join(root, 'Scenes', 'Locations', level, stem + suffix)
        if os.path.isfile(p):
            return p
    return None


def read(path):
    with open(path, 'rb') as f:
        return f.read()


def member(level, ext, game=None):
    """First archive member of a stock level whose name ends in ext."""
    with zipfile.ZipFile(level_zip(level, game)) as zf:
        for n in zf.namelist():
            if n.lower().endswith(ext.lower()):
                return zf.read(n)
    raise KeyError('%s has no %s' % (level, ext))


def ls_files(level, game=None):
    """-> {suffix: path} of a level's loading-sound files ('_LS.SND', '_LS_Default.WHD', ...)"""
    game = game or game_of(level)
    stem = os.path.basename(level_zip(level, game))[:-4]
    out = {}
    for root in (game_dir(game), os.path.join(game_dir(game), 'KL_PortBackup')):   # the backup wins
        for p in glob.glob(os.path.join(root, 'Scenes', 'Locations', level, stem + '_LS*')):
            out[os.path.basename(p)[len(stem):]] = p
    return out


def bank(level, game=None):
    """Walked Snd of a stock level, with its _LS bank."""
    game = game or game_of(level)
    ls = beside(level, '_LS.SND', game)
    return Snd(game, member(level, '_Main.SND', game), read(ls) if ls else b'').walk()


def stream_file(which='merged'):
    """Path of PC_Def.str: 'merged' = <work>/build (Dog Days' + Dead Men's FA clips, kl_audio.merge),
    'dd' = the one the game folder holds now, 'stock' = Dog Days' own (KL_PortBackup if moved)."""
    dd = game_dir('dd')
    if which == 'merged':
        return os.path.join(workdir(), 'build', 'PC_Def.str')
    bak = os.path.join(dd, 'KL_PortBackup', 'PC_Def.str')
    return bak if which == 'stock' and os.path.isfile(bak) else os.path.join(dd, 'PC_Def.str')


def stream_index(path):
    """-> (build id, set of clip offsets) of an IOISNDSTREAM file (kl_audio.StreamFile layout)."""
    with open(path, 'rb') as f:
        h = f.read(0x40)
        if h[:12] != b'IOISNDSTREAM':
            raise ValueError('not an IOISNDSTREAM file')
        if u32(h, 0x1c) == 0:
            index, count = struct.unpack_from('<Q', h, 0x18)[0], u32(h, 0x20)     # Dog Days
        else:
            index, count = u32(h, 0x18), u32(h, 0x1c)                             # Dead Men
        f.seek(index)
        raw = f.read(72 * count)
    return struct.unpack_from('<Q', h, 0x10)[0], {struct.unpack_from('<Q', raw, 72 * i + 8)[0] for i in range(count)}


def stream_map():
    """PC_Def.str.map.json of the merged stream file: {Dead Men clip offset: new offset}."""
    with open(stream_file('merged') + '.map.json') as f:
        return {int(k): v[0] for k, v in json.load(f).items()}


# ------------------------------------------------------------------ the image
class Snd:
    """walk() claims every byte by a typed item (items: {offset: (size, tag)}) and lists every
    dword that holds a pointer (ptrs), so the image can be moved or grown. ls = the level's
    _LS.SND (its objects' strings and parameters live in this image)."""

    def __init__(self, game, data, ls=b''):
        self.game, self.b, self.ls = game, data, ls
        G, b = GAME[game], data
        self.T, self.size, v3, v4 = struct.unpack_from('<4I', b, 0)
        if self.size != len(b) or (v3, v4) != (3, 4):
            raise ValueError('not a .SND')
        self.matrix = u32(b, self.T)
        self.H = self.T + 4 + 4 * G['streams']
        self.H += -self.H % 8
        self.build = struct.unpack_from('<Q', b, self.H)[0]
        self.counts = struct.unpack_from('<%dI' % NTYPES, b, self.H + 16)
        self.tabs = struct.unpack_from('<%dI' % NTYPES, b, self.H + 16 + 4 * NTYPES)
        self.P = self.H + 16 + 8 * NTYPES + 4               # {count, pointer} per parameter type, 1-based
        self.nparam = G['nparam']
        self.tables = {t + 1: list(struct.unpack_from('<%dI' % self.counts[t], b, self.tabs[t]))
                       for t in range(NTYPES) if self.counts[t]}
        self.nmat = len(self.tables[0x12]) + len(self.tables[0x13])
        self.cut = min(p for p in self.tabs if p)           # the first type table
        self.kind = {o: t for t, offs in self.tables.items() for o in offs if o < self.T}

    def name(self, o):
        return cs(self.b, u32(self.b, o + 8))

    def langs(self, o):
        """Number of .WHD records of the wave at o."""
        if u32(self.b, o) == 4:
            return 1
        return GAME[self.game]['streams'] - 1 if u16(self.b, o + 0xc) & 2 else 1

    def walk(self):
        b, G = self.b, GAME[self.game]
        self.items, self.ptrs, self.err, self.lsptrs = {}, set(), collections.Counter(), set()
        items, ptrs, T = self.items, self.ptrs, self.T

        def claim(o, n, tag):
            if o in items:
                m, was = items[o]
                if {was, tag} == {'paramtable', 'paramlist'}:            # a list that is also a table
                    items[o] = (max(m, n), 'paramtable'); return False
                if (m, was) != (n, tag):
                    self.err['clash %s/%s' % (was, tag)] += 1
                return False
            items[o] = (n, tag); return True

        def cstr(o, tag):
            claim(o, b.index(NUL, o) - o + 1, tag)

        def plist(o, n, tag):
            claim(o, 4 * n, tag)
            v = struct.unpack_from('<%dI' % n, b, o)
            ptrs.update(o + 4 * i for i, x in enumerate(v) if x and x < T)
            return v

        def wavename(q):
            a = b.rfind(b'audio:', 0, q)
            if a < 0:
                return
            text = b[a:q].rstrip(NUL)
            if text.endswith(b'#wave') and NUL not in text:
                claim(a, len(text) + 1, 'wavename')

        def wavename_after(o):
            """A sound's own '#wave' alias string follows its name even when the wave is shared."""
            e = b.index(NUL, u32(b, o + 8))
            a = e + 16 - e % 16
            if b[a:a + 6] == b'audio:':
                t = b[a:b.index(NUL, a)]
                if t.endswith(b'#wave'):
                    claim(a, len(t) + 1, 'wavename')

        def wave(o):
            if u32(b, o) == 4:
                if claim(o, 0x20, 'wave'):
                    cstr(u32(b, o + 8), 'wavfile'); wavename(u32(b, o + 8))
                ptrs.add(o + 8); return
            n = self.langs(o)
            if not claim(o, 0x20 + 0x1c * (n - 1), 'streamwave'):
                return
            for i in range(n):
                q = o + 8 + 0x1c * i
                if u32(b, q):                                # a language without a clip is all zero
                    cstr(u32(b, q), 'wavfile'); ptrs.add(q)
            wavename(u32(b, o + 8))

        def param(q):
            t = u32(b, q)
            claim(q, PARAM_SIZE.get(t, 0x10), 'param')
            if t == 0x12 and u32(b, q + 4):
                ptrs.add(q + 4)
            if t == 0x13 and u32(b, q + 0x1c):
                ptrs.add(q + 0x1c)

        def params(o, n):
            for q in plist(o, n, 'paramlist'):
                param(q); seen.add(q)

        seen = set()
        claim(0, 16, 'header'); ptrs.add(0)
        for i in range(G['streams']):
            cstr(u32(b, T + 4 + 4 * i), 'streamname'); ptrs.add(T + 4 + 4 * i)
        claim(T, len(b) - T, 'trailer'); ptrs.update((T, self.H + 8))
        plist(self.matrix, (self.nmat + 1) * self.nmat, 'matrix')
        for t in range(NTYPES):
            if self.counts[t]:
                plist(self.tabs[t], self.counts[t], 'typetable'); ptrs.add(self.H + 16 + 4 * NTYPES + 4 * t)
        tabparams = set()
        for k in range(self.nparam):
            n, p = struct.unpack_from('<2I', b, self.P + 8 * k)
            if n:
                tabparams.update(plist(p, n, 'paramtable')); ptrs.add(self.P + 8 * k + 4)
        for q in tabparams:
            param(q)
        for t, offs in self.tables.items():
            for o in offs:
                if o >= T:
                    continue                                 # -1 / -2: lives in the _LS bank
                if t == 4:
                    wave(o); continue
                if u32(b, o) != t:
                    self.err['type %d' % t] += 1
                claim(o, G['sizes'][t], NAMES[t]); cstr(u32(b, o + 8), 'name'); ptrs.add(o + 8)
                if u32(b, o + 0x10):
                    params(u32(b, o + 0x10), u16(b, o + 0xc)); ptrs.add(o + 0x10)
                n, c = u16(b, o + 0x18), u32(b, o + 0x14)
                if t == 1:
                    if c and c < T:
                        ptrs.add(o + 0x14); wave(c)
                    wavename_after(o)
                elif t in (2, 5, 0x17) and c:
                    plist(c, n, 'list'); ptrs.add(o + 0x14)
                elif t == 3 and c:
                    claim(c, 12 * n, 'events'); ptrs.add(o + 0x14)
                    ptrs.update(c + 12 * i + 8 for i in range(n) if u32(b, c + 12 * i) in (2, 4, 5, 6) and u32(b, c + 12 * i + 8))
                if t == 0x17:
                    cstr(u32(b, o + 0x3c), 'groupname'); ptrs.add(o + 0x3c)
                    if u32(b, o + 0x40):
                        ptrs.add(o + 0x40)
                    if u32(b, o + 0x1c):
                        claim(u32(b, o + 0x1c), 4 * u16(b, o + 0x22), 'slots'); ptrs.add(o + 0x1c)
        # the loading-sound bank: sound records whose name and parameter list live in this file
        z = self.ls
        step = G['sizes'][1] + (-G['sizes'][1] % 16)
        for o in range(0x10, len(z), step):
            if u32(z, o) != 1:
                self.err['ls type'] += 1
            q = u32(z, o + 8); cstr(q, 'name')
            a = b.index(NUL, q); a += 16 - a % 16
            if b[a:a + 6] == b'audio:' and b[a:b.index(NUL, a)].endswith(b'#wave'):
                cstr(a, 'wavename')
            if u32(z, o + 0x10):
                params(u32(z, o + 0x10), u16(z, o + 0xc))
            self.lsptrs.update((o + 8, o + 0x10))
        self.orphans = 0                                    # waves nothing refers to (streamed)
        for o in range(0x10, T, 16):
            if o not in items and u32(b, o) == 0 and u32(b, o + 4) == 0 and u16(b, o + 0xc) in (1, 0xb) and u16(b, o + 0xe) == 0 \
                    and 0 < u32(b, o + 8) < o and cs(b, u32(b, o + 8)).lower().endswith(b'.wav') and u32(b, o + 8) not in items:
                wave(o); self.orphans += 1
        self.unlisted = len(tabparams - seen)
        self.err['param on a list but in no table'] += len(seen - tabparams)
        for o, (n, tag) in items.items():                   # waves reached only through a sound
            if tag in ('wave', 'streamwave'):
                self.kind.setdefault(o, 4)
        return self

    def check(self):
        """-> (unclaimed non-zero bytes, overlapping bytes, pointers that miss an item start)"""
        cover, over = bytearray(len(self.b)), 0
        for o, (n, tag) in self.items.items():
            over += sum(cover[o:o + n]); cover[o:o + n] = b'\1' * n
        self.cover = cover
        nz = int.from_bytes(self.b.translate(bytes([0]) + bytes([1]) * 255), 'little')
        un = (nz ^ (nz & int.from_bytes(cover, 'little'))).bit_count()
        stray = sum(1 for a in self.ptrs if u32(self.b, a) not in self.items and a != 0)
        return un, over, stray

    def clean(self):
        """-> [] or what is wrong with the image (the checks every stock bank passes)"""
        un, over, stray = self.check()
        bad = ['%d %s' % (v, k) for k, v in self.err.items() if v]
        bad += ['%d %s' % (v, k) for k, v in (('non-zero bytes no item claims', un), ('overlapping bytes', over),
                                             ('pointers that miss an item', stray)) if v]
        high = sum(1 for o, (n, tag) in self.items.items() if o >= self.cut and tag not in ('typetable', 'paramtable', 'trailer'))
        if self.game == 'dd' and high:                      # merge() cuts here
            bad.append('%d items behind the first type table' % high)
        return bad

    def shifted(self, delta):
        """The same image with everything behind the header moved by delta (a multiple of 16),
        and its _LS bank. The round trip of the walker's pointer map."""
        out = bytearray(self.b[:16] + bytes(delta) + self.b[16:])
        for a in self.ptrs:
            struct.pack_into('<I', out, a + (delta if a >= 16 else 0), u32(self.b, a) + delta)
        struct.pack_into('<I', out, 4, len(out))
        ls = bytearray(self.ls)
        for a in self.lsptrs:
            if u32(ls, a):
                struct.pack_into('<I', ls, a, u32(ls, a) + delta)
        return bytes(out), bytes(ls)

    def waves(self):
        """-> (wave offset, record index, .WHD offset) of every .WHD reference with a clip"""
        b = self.b
        for o, t in self.kind.items():
            if t != 4:
                continue
            if u32(b, o) == 4:
                yield o, 0, u32(b, o + 0x14); continue
            for i in range(self.langs(o)):
                if u32(b, o + 8 + 0x1c * i):
                    yield o, i, u32(b, o + 0x14 + 0x1c * i)


def round_trip(s, delta=0x1230):
    """Move the image by delta, walk it again, move it back: -> True if the items, the pointer
    set and the bytes come back. (A pointer in a field taken for a number would pass this.)"""
    b2, ls2 = s.shifted(delta)
    s2 = Snd(s.game, b2, ls2).walk()
    mv = lambda a: a + (delta if a >= 16 else 0)
    if s2.clean() or {mv(a) for a in s.ptrs} != s2.ptrs:
        return False
    if collections.Counter(t for n, t in s.items.values()) != collections.Counter(t for n, t in s2.items.values()):
        return False
    b3 = bytearray(b2[:16] + b2[16 + delta:])
    for a in s.ptrs:
        struct.pack_into('<I', b3, a, u32(b2, mv(a)) - delta)
    struct.pack_into('<I', b3, 4, len(b3))
    return bytes(b3) == s.b


# ------------------------------------------------------------------ the merge
def _signatures(s):
    """Content of an object without its addresses, for 'the same object in another bank of the
    same game': type, name, the record's bytes outside its pointers, parameters, children."""
    b, memo, sizes = s.b, {}, GAME[s.game]['sizes']

    def par(q):
        t = u32(b, q)
        r = bytearray(b[q:q + PARAM_SIZE.get(t, 0x10)])
        x = None
        if t == 0x12 and u32(b, q + 4):
            x = sig(u32(b, q + 4)); r[4:8] = bytes(4)
        if t == 0x13 and u32(b, q + 0x1c):
            x = sig(u32(b, q + 0x1c)); r[0x1c:0x20] = bytes(4)
        return bytes(r), x

    def sig(o):
        if o in memo:
            return memo[o]
        memo[o] = 'loop'                                   # a sequence that names itself: none seen
        t = s.kind.get(o)
        if t is None:
            r = ('?', o)
        elif t == 4:
            n = s.langs(o)
            r = ('wave', u32(b, o), u16(b, o + 0xc), tuple(cs(b, u32(b, o + 8 + 0x1c * i)) if u32(b, o + 8 + 0x1c * i) else None
                                                           for i in range(n)))
        elif t in (0x12, 0x13):
            r = (t, s.name(o))                               # matched by name; ids are the base's
        elif t == 0x17:
            r = (t, cs(b, u32(b, o + 0x3c)))
        else:
            rec = bytearray(b[o:o + sizes[t]])
            rec[8:12] = bytes(4); rec[0x10:0x14] = bytes(4)
            n, c = u16(b, o + 0x18), u32(b, o + 0x14)
            ps = tuple(par(q) for q in struct.unpack_from('<%dI' % u16(b, o + 0xc), b, u32(b, o + 0x10))) if u32(b, o + 0x10) else ()
            kids = ()
            if t in (1, 2, 3, 5):
                rec[0x14:0x18] = bytes(4)
            if t == 1:
                kids = ('ls',) if c >= s.T else (sig(c),) if c else ()
            elif t in (2, 5) and c:
                kids = tuple(sig(x) if x else 0 for x in struct.unpack_from('<%dI' % n, b, c))
            elif t == 3 and c:
                ev = [struct.unpack_from('<3I', b, c + 12 * i) for i in range(n)]
                kids = tuple((k, tm, sig(x) if k in (2, 4, 5, 6) and x else x) for k, tm, x in ev)
            r = (t, s.name(o), bytes(rec), ps, kids)
        memo[o] = hash(r)
        return memo[o]
    return sig


def merge(base, src, base_whd, base_wav, src_whd, src_wav, roots, strmap=None, log=print, stats=None):
    """Append what `roots` need of bank `src` to the Dog Days bank `base`.
    base, src: walked Snd (src of either game); *_whd, *_wav: their .WHD / .WAV bytes;
    roots: offsets in src's .SND (the map nodes' sound fields, .LOC sound ids);
    strmap: {Dead Men clip offset in its PC_Def.str: offset in the merged stream file}
    (stream_map()), needed when src is a Dead Men bank.
    -> (new .SND, new .WHD, new .WAV, {src offset: new offset}). Every byte of base below its
    first type table keeps its place. A map value of 0 = no Dog Days form (a Dead Men room
    effect, a wave whose clip is not in the stream file). A root that is no object of src gets
    no entry. stats (a Counter) receives the counts that are logged."""
    if base.game != 'dd':
        raise ValueError('the base bank must be Dog Days\'')
    bad = base.clean()
    if bad:
        raise ValueError('base bank: ' + '; '.join(bad))
    same = src.game == base.game
    if not same and strmap is None:
        strmap = stream_map()
    st = collections.Counter() if stats is None else stats
    b, d, kind, sizes = base.b, src.b, src.kind, GAME[src.game]['sizes']
    by_name = {(t, base.name(o)): o for o, t in base.kind.items() if t != 4}
    groups = {cs(b, u32(b, o + 0x3c)).decode('latin1'): o for o in base.tables[0x17]}
    sig_b, sig_s = (_signatures(base), _signatures(src)) if same else (None, None)

    def group(x):
        """The base's mixer group for src's group x: by name, else the nearest parent the base has."""
        seen = set()
        while x and x not in seen:
            seen.add(x)
            n = cs(d, u32(d, x + 0x3c)).decode('latin1')
            n = n if same else GROUP.get(n)
            if n in groups:
                st['group named differently or absent: a parent used'] += len(seen) > 1
                return groups[n]
            x = u32(d, x + 0x40)
        st['group not found: Master'] += 1
        return groups['Master']

    def shared(o):
        """The base's own object that stands for src's o, None if o has to be copied."""
        t = kind[o]
        if t == 0x17:
            return group(o)
        if t in (0x12, 0x13):                               # materials: the base's matrix is kept, so the base's ids
            hit = by_name.get((t, src.name(o).lower())) or by_name.get((t, src.name(o)))
            if hit is None:
                st['%s the base lacks' % NAMES[t]] += 1
                return by_name[0x13, DEFAULT_SURFACE] if t == 0x13 else 0
            return hit
        if t == 7 and not same:
            return 0                                        # ASSUMPTION: Dead Men's reverb block has no Dog Days form
        if same and t != 4:
            hit = by_name.get((t, src.name(o)))
            if hit is not None:
                if sig_b(hit) == sig_s(o):
                    return hit
                st['same name as an object of the base, other content: copied'] += 1
        return None

    # ---- 1. what is needed
    order, target, stack = [], {}, list(roots)
    def kids(o):
        t, out = kind[o], []
        if t == 4:
            return out
        n, c = u16(d, o + 0x18), u32(d, o + 0x14)
        if u32(d, o + 0x10):
            for q in struct.unpack_from('<%dI' % u16(d, o + 0xc), d, u32(d, o + 0x10)):
                if u32(d, q) == 0x12 and u32(d, q + 4): out.append(u32(d, q + 4))
                if u32(d, q) == 0x13 and u32(d, q + 0x1c): out.append(u32(d, q + 0x1c))
        if t == 1 and c and c < src.T: out.append(c)
        elif t in (2, 5) and c: out += [x for x in struct.unpack_from('<%dI' % n, d, c) if x]
        elif t == 3 and c: out += [u32(d, c + 12 * i + 8) for i in range(n) if u32(d, c + 12 * i) in (2, 4, 5, 6) and u32(d, c + 12 * i + 8)]
        return out
    while stack:
        o = stack.pop()
        if o in target or not o:
            continue
        if o not in kind:
            st['roots that are no object of the source bank'] += o in roots
            st['pointers to no object inside the source bank'] += o not in roots
            continue
        hit = shared(o)
        target[o] = ('o', o) if hit is None else ('abs', hit)
        if hit is None:
            order.append(o); stack += kids(o)
        else:
            st['reused from the base' if hit else 'no Dog Days form: 0'] += 1

    # ---- 2. wave headers and wave data
    recs = W.records(src.game, src_whd)
    writer, whdmap = W.Writer(base_whd, base_wav), {}
    def whd_rec(old):
        if old not in whdmap:
            f = recs.get(old)
            if f is None:
                st['waves that name no .WHD record'] += 1
                whdmap[old] = None; return None
            name, g, data = cs(src_whd, f['name']), W.to_dd(f, src.game), None
            if f['fmt'] & W.STREAMED:
                if not same:
                    if f['fmt'] & W.LANGFILE or f['off'] not in strmap:   # only PC_Def.str was merged
                        st['stream clips not in the merged stream file'] += 1
                        whdmap[old] = None; return None
                    off = strmap[f['off']]
                    g['fmt'], g['off'], g['offhi'] = f['fmt'], off & 0xffffffff, off >> 32
                st['stream records added'] += 1
            else:
                off = f['off'] | (f.get('offhi', 0) << 32)
                data = src_wav[off:off + f['size']]
                if len(data) != f['size']:
                    raise ValueError('wave data of %r is outside the source .WAV' % name)
                st['in-memory records added'] += 1; st['in-memory bytes added'] += len(data)
            whdmap[old] = writer.add(name, g, data)
        return whdmap[old]

    # ---- 3. the new items, behind the base's objects and matrix
    cut = base.cut
    if base.matrix + 4 * (base.nmat + 1) * base.nmat > cut:
        raise ValueError('base bank: the material matrix is not below the type tables')
    out, new, fix = bytearray(b[:cut]), {}, []              # fix: (position, key of the target)
    def put(key, data, refs=()):
        out.extend(bytes(-len(out) % 16)); new[key] = len(out)
        fix.extend((len(out) + r, k) for r, k in refs); out.extend(data)
    def string(p):
        if ('s', p) not in new:
            put(('s', p), cs(d, p) + NUL)
        return ('s', p)
    tg = lambda x: target.get(x, ('abs', 0))               # a pointer to no object of the source: 0
    newtab, newpar = collections.defaultdict(list), collections.defaultdict(list)
    nl_src, nl_dst = GAME[src.game]['streams'] - 1, GAME['dd']['streams'] - 1
    for o in order:
        t = kind[o]
        if t == 4:
            if u32(d, o) == 4:                              # one record
                r = whd_rec(u32(d, o + 0x14))
                if r is None:
                    target[o] = ('abs', 0); continue
                put(('o', o), d[o:o + 4] + b'\xcd' * 4 + d[o + 8:o + 0x14] + struct.pack('<I', r) + d[o + 0x18:o + 0x20],
                    [(8, string(u32(d, o + 8)))])
            else:
                n = src.langs(o)
                rs = [list(struct.unpack_from('<6I', d, o + 8 + 0x1c * i)) for i in range(n)]    # name flags 0 whd seconds 0
                for r in (rs if same else rs[:1]):           # Dead Men: only the English clip is carried
                    if r[0]:
                        r[3] = whd_rec(r[3])
                if rs[0][3] is None or not rs[0][0]:
                    target[o] = ('abs', 0); continue
                if not same and n == nl_src:
                    # ASSUMPTION: only English audio of Dead Men is in the merged stream file, so all
                    # nine Dog Days language records name the English clip (flags 3 = stock, 310,072 of 310,120)
                    rs = [rs[0]] + [[rs[0][0], 3, 0, rs[0][3], rs[0][4], 0]] * (nl_dst - 1)
                blob, refs = bytearray(d[o:o + 8]), []
                for i, r in enumerate(rs):
                    if not r[0] or r[3] is None:            # no clip in this language
                        st['language records without a clip'] += r[3] is None
                        blob += bytes(0x1c); continue
                    refs.append((8 + 0x1c * i, string(r[0])))
                    blob += struct.pack('<7I', *r, 0)
                put(('o', o), bytes(blob[:0x20 + 0x1c * (len(rs) - 1)]), refs)
            newtab[4].append(('o', o)); continue
        body = bytearray(d[o:o + sizes[t]])
        if t == 1 and not same:
            # 0x30 -> 0x34. ASSUMPTION: the float Dog Days added at +0x1c = NEW_FLOAT; the cone, the
            # zero dword and the five flag bytes move 4 up (same-named sounds of both games agree
            # there, re/audio.md 2.2); the two bytes Dog Days added after them = 0
            body = body[:0x1c] + struct.pack('<f', NEW_FLOAT) + body[0x1c:0x2d] + b'\0\0\xcd'
        refs = [(8, string(u32(d, o + 8)))]
        np_, pl, n, c = u16(d, o + 0xc), u32(d, o + 0x10), u16(d, o + 0x18), u32(d, o + 0x14)
        if pl:
            keep = []
            for q in struct.unpack_from('<%dI' % np_, d, pl):
                pt = u32(d, q)
                if not same and pt in DROP_PARAMS:
                    st['parameters dropped (types 3, 6, 7)'] += 1; continue
                if ('p', q) not in new:
                    pr = []
                    if pt == 0x12 and u32(d, q + 4): pr.append((4, tg(u32(d, q + 4))))
                    if pt == 0x13 and u32(d, q + 0x1c): pr.append((0x1c, tg(u32(d, q + 0x1c))))
                    put(('p', q), d[q:q + PARAM_SIZE.get(pt, 0x10)], pr)
                keep.append(('p', q)); newpar[pt].append(('p', q))
            struct.pack_into('<H', body, 0xc, len(keep))
            if keep:
                put(('pl', o), bytes(4 * len(keep)), [(4 * i, k) for i, k in enumerate(keep)]); refs.append((0x10, ('pl', o)))
            else:
                struct.pack_into('<I', body, 0x10, 0)
        if t == 1 and c:
            if c < src.T:
                refs.append((0x14, tg(c)))
            else:                                           # its wave is in the source's _LS bank: not carried
                struct.pack_into('<I', body, 0x14, 0); st['sounds of the source\'s _LS bank: no wave'] += 1
        elif t in (2, 5) and c:
            put(('cl', o), bytes(4 * n), [(4 * i, tg(x)) for i, x in enumerate(struct.unpack_from('<%dI' % n, d, c)) if x])
            refs.append((0x14, ('cl', o)))
        elif t == 3 and c:
            put(('ev', o), d[c:c + 12 * n], [(12 * i + 8, tg(u32(d, c + 12 * i + 8))) for i in range(n)
                                             if u32(d, c + 12 * i) in (2, 4, 5, 6) and u32(d, c + 12 * i + 8)])
            refs.append((0x14, ('ev', o)))
        put(('o', o), bytes(body), refs); newtab[t].append(('o', o))
    value = lambda key: key[1] if key[0] == 'abs' else new.get(key, 0)
    for pos, key in fix:
        key = target.get(key[1], key) if key[0] == 'o' else key       # a wave that was dropped after it was named
        struct.pack_into('<I', out, pos, value(key))

    # ---- 4. tables and trailer
    counts, tabs = list(base.counts), list(base.tabs)
    for t in range(NTYPES):
        add = [new[k] for k in newtab.get(t + 1, [])]
        if base.counts[t] or add:
            out.extend(bytes(-len(out) % 16)); tabs[t] = len(out); counts[t] = base.counts[t] + len(add)
            out.extend(b[base.tabs[t]:base.tabs[t] + 4 * base.counts[t]] + struct.pack('<%dI' % len(add), *add))
    pairs = []
    for k in range(base.nparam):
        n, p = struct.unpack_from('<2I', b, base.P + 8 * k)
        add = [new[x] for x in newpar.get(k + 1, [])]       # one entry per use, as stock
        if n or add:
            out.extend(bytes(-len(out) % 16)); pairs += [n + len(add), len(out)]
            out.extend(b[p:p + 4 * n] + struct.pack('<%dI' % len(add), *add))
        else:
            pairs += [0, 0]
    if any(k > base.nparam for k in newpar):
        raise ValueError('parameter type beyond Dog Days\' %d' % base.nparam)
    out.extend(bytes(-len(out) % 16))
    T, tr = len(out), bytearray(b[base.T:])
    struct.pack_into('<%dI' % NTYPES, tr, base.H - base.T + 16, *counts)
    struct.pack_into('<%dI' % NTYPES, tr, base.H - base.T + 16 + 4 * NTYPES, *tabs)
    struct.pack_into('<%dI' % len(pairs), tr, base.P - base.T, *pairs)
    out.extend(tr); struct.pack_into('<2I', out, 0, T, len(out))
    whd, wav = writer.finish()
    omap = {o: value(target[o]) for o in target}
    for t in sorted(newtab):
        st['added: ' + NAMES[t]] = len(newtab[t])
    log('  sound bank: %s' % ', '.join('%s %d' % kv for kv in sorted(st.items())))
    return bytes(out), whd, wav, omap


def ls_bank(ls, T):
    """A level's _LS.SND for a bank whose trailer moved to T. Its name / parameter pointers
    point below the first type table, which merge() keeps in place.
    ASSUMPTION: the first dword is the level bank's T (equal in 40 of 40 stock pairs; whether the
    engine reads it is not established)."""
    return struct.pack('<I', T) + ls[4:] if ls else ls


def verify(base, snd, whd, wav, ls=None, omap=None):
    """The checks a merged bank must pass, by the rules every stock bank obeys (the stream clips:
    verify_streams). -> (problems, counts)"""
    bad, n = [], collections.Counter()
    m = Snd('dd', snd, base.ls if ls is None else ls).walk()
    bad += ['merged .SND: ' + x for x in m.clean()]
    if snd[16:base.cut] != base.b[16:base.cut]:
        bad.append('stock bytes below the first type table changed')
    if m.build != base.build or m.build != GAME['dd']['build']:
        bad.append('build id %x is not Dog Days\' stream file\'s' % m.build)
    if ls is not None and ls and u32(ls, 0) != m.T:
        bad.append('_LS.SND does not name the new trailer')
    for t in base.tables:
        if m.tables[t][:len(base.tables[t])] != base.tables[t]:
            bad.append('type table %d does not start with the base\'s entries' % t)
        n['table: ' + NAMES[t]] = len(m.tables[t])
    try:
        recs = W.records('dd', whd)
    except ValueError as e:
        return bad + ['merged .WHD: %s' % e], n
    n['.WHD records'] = len(recs)
    for o, i, r in m.waves():
        n['wave -> .WHD references'] += 1
        if r not in recs:
            n['wave -> .WHD references that hit no record'] += 1
    if n['wave -> .WHD references that hit no record']:
        bad.append('%d wave references hit no .WHD record' % n['wave -> .WHD references that hit no record'])
    if u32(wav, 4) != len(wav):
        bad.append('.WAV size field')
    for r, f in recs.items():
        if f['fmt'] & W.STREAMED:
            n['streamed records'] += 1
        else:
            off = f['off'] | (f['offhi'] << 32)
            n['in-memory records'] += 1
            n['in-memory records with their data in the .WAV'] += 16 <= off and off + f['size'] <= len(wav)
    if n['in-memory records'] != n['in-memory records with their data in the .WAV']:
        bad.append('in-memory records without data')
    if omap is not None:
        for o, v in omap.items():
            n['offset map entries'] += 1
            n['offset map entries -> 0'] += not v
            if v and v not in m.kind:
                bad.append('offset map: %#x -> %#x is no object' % (o, v))
    return bad, n


def verify_streams(base_whd, whd, clips):
    """-> (streamed PC_Def.str records the merge added, how many are no clip of the stream file)"""
    T = u32(base_whd, 0)
    add = [f for r, f in W.records('dd', whd).items() if r >= T and f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE]
    return len(add), sum(1 for f in add if (f['off'] | (f['offhi'] << 32)) not in clips)


# ------------------------------------------------------------------ the level's objects
def _schema():
    import kl_rtp
    if 'dd' not in _schema.__dict__:
        _schema.dd = kl_rtp.Schema.load('dd')
    return _schema.dd


def sound_fields(sc, k, sch=None):
    """Sound reference fields of node k of a Dog Days property tree (kl_prpjoin.Scene: stock,
    joined, or Dead Men's after kl_convert) and of its registered controllers.
    -> [(holder, key, [field index])]: the object's tokens are holder[key] ('props') or
    holder[key][1] (a controller), as kl_graft.objects / get_obj have it."""
    sch = sch or _schema()
    n, cls = sc.nodes[k], sc.cls(k)
    objs = [(cls, n, 'props')]
    for i, (nm, _body) in enumerate(n['ctrls']):
        impl = sch.controller(sc.p.key(nm), cls)
        if impl:
            objs.append((impl, n['ctrls'], i))
    out = []
    for c, holder, key in objs:
        hot = [i for i, f in enumerate(sch.fields(c) or ()) if f.type in SOUND_TYPES['dd'] and f.kind == 'I']
        if hot:
            out.append((holder, key, hot))
    return out


def _units(holder, key):
    from kl_prp import units
    obj = holder[key] if key == 'props' else holder[key][1]
    return obj, [list(u) for u in units(obj[1:-1])]


def roots(sc, ks, sch=None):
    """Every non-zero sound reference on nodes ks (the nodes that came from the map level):
    offsets into the MAP level's .SND. -> set"""
    out = set()
    for k in ks:
        for holder, key, hot in sound_fields(sc, k, sch):
            _obj, us = _units(holder, key)
            out.update(struct.unpack('<I', us[i][0][1])[0] for i in hot)
    return out - {0, LS_SOUND}


def rewrite(sc, ks, omap, sch=None):
    """Replace every sound reference on nodes ks through omap (merge()'s result). A value the
    map does not hold becomes 0 and is counted: it named no object of the map level's bank.
    -> Counter"""
    count = collections.Counter()
    for k in ks:
        for holder, key, hot in sound_fields(sc, k, sch):
            obj, us = _units(holder, key)
            for i in hot:
                v = struct.unpack('<I', us[i][0][1])[0]
                if not v:
                    continue
                if v == LS_SOUND:                           # the sound of the _LS bank: the slot keeps S's
                    count['references to the loading sound (kept: the _LS bank of the slot)'] += 1
                    continue
                if v not in omap:
                    count['sound references that name no object of the map\'s bank: 0'] += 1
                new = omap.get(v, 0)
                count['sound references rewritten' if new else 'sound references without a Dog Days form: 0'] += v in omap
                us[i][0] = (us[i][0][0], struct.pack('<I', new))
            toks = [obj[0]] + [t for u in us for t in u] + [obj[-1]]
            if key == 'props':
                holder[key] = toks
            else:
                holder[key] = (holder[key][0], toks)
    return count


def strings_of(sc, ks):
    """Every string the nodes ks and their controllers hold (candidates for .LOC keys)."""
    out, keys = set(), sc.p.keys
    for k in ks:
        n = sc.nodes[k]
        for toks in [n['props']] + [body for _nm, body in n['ctrls']]:
            for op, pl in toks:
                if op == 0x0c:
                    out.add(keys[struct.unpack('<I', pl)[0]])
                elif op == 0x0f:
                    out.update(keys[i] for i in struct.unpack_from('<%dI' % (len(pl) // 4 - 1), pl, 4))
    return out


class Audio:
    """Result of graft_audio(): members {'.SND': bytes, 'English.LOC': bytes, ...} to put into
    the archive in place of S's (keys as kl_graft.Level.ext), beside {'.WHD': bytes, '.WAV':
    bytes, '_LS.SND': bytes, '_LS_Default.WHD': path, ...} to write next to it as
    <slot>_Main<suffix> (bytes are written, a path is copied), map, counts, problems."""

    def __init__(self):
        self.members, self.beside, self.map = {}, {}, {}
        self.counts, self.problems = collections.Counter(), []

    def write_beside(self, folder, slot):
        import shutil
        for suffix, v in self.beside.items():
            p = os.path.join(folder, slot + '_Main' + suffix)
            if isinstance(v, bytes):
                with open(p, 'wb') as f:
                    f.write(v)
            else:
                shutil.copyfile(v, p)


def graft_audio(s_name, m_name, sc, ks, log=print, more_roots=(), loc=True):
    """The sound side of a graft of map level m_name (either game) under the Dog Days systems
    level s_name. sc: the JOINED property tree (kl_prpjoin.Scene, Dog Days form); ks: the indices
    in sc of the nodes that came from the map level. sc is edited in place: every sound
    reference on ks is moved into the merged bank (0xffffffff = 'the sound of the _LS bank', on
    the map's Loading_Sound ZSNDOBJ in F09 and M01_FA_A, stays: the slot keeps S's _LS bank). more_roots: further offsets of the map
    level's .SND to carry (they appear in .map). -> Audio.

    kl_graft.build(): call it where the loop 'for k in sorted(m_nodes)' sets these fields to 0
    today, with ks = [mj[k] for k in sorted(m_nodes)], BEFORE Jn.p.serialize(); see the patch
    description in the module's report. Everything here reads stock files of both levels itself.

    .LOC: a key that a string of the map's nodes names, that the map level's .LOC has and S's
    does not, is grafted into S's files with its sound (Dead Men's voice lines on the map's
    OnlineSpeakTrigger / settings fields). Between two Dog Days FA levels nothing is added (all
    nine share their 2,328 Multiplayer/ keys)."""
    a, st = Audio(), collections.Counter()
    mg = game_of(m_name)
    base, src = bank(s_name), bank(m_name, mg)
    want, sids = set(), {}
    with zipfile.ZipFile(level_zip(s_name)) as zf:
        s_loc = {lang: zf.read(n) for lang, n in kl_loc.members(zf).items()}
    if loc:
        with zipfile.ZipFile(level_zip(m_name, mg)) as zf:
            m_loc = {lang: zf.read(n) for lang, n in kl_loc.members(zf).items()}
        have = {p.lower() for p, _k in kl_loc.leaves(kl_loc.parse(s_loc['English']))}
        named = {s.lower().replace('\\', '/') for s in strings_of(sc, ks)}
        for p, k in kl_loc.leaves(kl_loc.parse(m_loc['English'])):
            if p.lower() in named and p.lower() not in have:
                want.add(p); sids[p] = kl_loc.fields(k)[2] or 0
        st['.LOC keys the map names that %s lacks' % s_name] = len(want)
    rs = roots(sc, ks) | set(more_roots) | {v for v in sids.values() if v}
    st['roots'] = len(rs)
    snd, whd, wav, omap = merge(base, src, read(beside(s_name, '.WHD')), read(beside(s_name, '.WAV')),
                                read(beside(m_name, '.WHD', mg)), read(beside(m_name, '.WAV', mg)), rs, log=log, stats=st)
    st.update(rewrite(sc, ks, omap))
    a.map, a.members['.SND'] = omap, snd
    a.beside['.WHD'], a.beside['.WAV'] = whd, wav
    ls = None
    for suffix, p in ls_files(s_name).items():
        if suffix == '_LS.SND':
            ls = ls_bank(read(p), u32(snd, 0)); a.beside[suffix] = ls
        else:
            a.beside[suffix] = p
    if want:
        files, n = kl_loc.graft_level(s_loc, m_loc, lambda p: p in want, omap, log)
        st['.LOC leaves added per language'] = n
        st['.LOC leaves added without a sound'] = sum(1 for p in want if not omap.get(sids[p]))
        a.members.update({lang + '.LOC': d for lang, d in files.items()})
    a.problems, n = verify(base, snd, whd, wav, ls, omap)
    left = roots(sc, ks) - set(Snd('dd', snd).kind)
    if left:
        a.problems.append('%d sound references of the map name no object of the merged bank' % len(left))
    if st['roots that are no object of the source bank']:
        a.problems.append('%d sound references of the map named no object of %s\'s bank (set to 0)' % (
            st['roots that are no object of the source bank'], m_name))
    if st['stream clips not in the merged stream file']:
        a.problems.append('%d stream clips are not in the merged stream file (kl_audio.merge)' % st['stream clips not in the merged stream file'])
    a.counts = st + n
    log('  sound: %s' % dict(a.counts))
    return a


# ------------------------------------------------------------------ tests
def map_scene(level):
    """(property tree in Dog Days form, indices of its map-side nodes) of a stock level, the way
    kl_graft sees a map level: a Dead Men level goes through kl_convert first."""
    import kl_prpjoin as J
    if game_of(level) == 'dd':
        sc = J.Scene.load(level)
        side = J.sides(sc)
    else:
        import kl_convert as K
        from kl_prp import Prp
        src = J.Scene.load(level, 'dm')
        side = J.sides(src)
        data, _st = K.convert_level(member(level, '_Main.prp', 'dm'), K.converter(game_dir('dd'), workdir()), src.tids)
        sc = J.Scene(Prp(data), src.names, [src.tids[0]] + [K.RETYPE.get(t, t) for t in src.tids[1:]], 'dd', level)
    return sc, [k for k in range(1, len(sc.nodes)) if side[k] == 'map']


def test_merge(s_name, m_name, log=print, out=None):
    """One trial graft_audio on the map side of stock m_name. -> number of problems"""
    sc, ks = map_scene(m_name)
    before = roots(sc, ks)
    a = graft_audio(s_name, m_name, sc, ks, log=lambda *_a: None)
    base = bank(s_name)
    m = Snd('dd', a.members['.SND'], a.beside.get('_LS.SND', b'')).walk()
    c = a.counts
    bad = list(a.problems)
    build, clips = stream_index(stream_file('merged'))
    if build != m.build:
        bad.append('the merged stream file has build id %x, the bank %x (kl2 0x67e8f8)' % (build, m.build))
    nstream, lost = verify_streams(read(beside(s_name, '.WHD')), a.beside['.WHD'], clips)
    if lost:
        bad.append('%d added stream records are no clip of the merged stream file' % lost)
    after = roots(sc, ks)
    if not after <= set(m.kind):
        bad.append('rewritten references that are no object')
    log('%s systems + %s map: %d map nodes, %d distinct references' % (s_name, m_name, len(ks), len(before)))
    log('  counts:  %s' % ', '.join('%s %d' % kv for kv in sorted(c.items())))
    log('  merged .SND %d bytes (stock %d): %s; stock bytes below %#x unchanged: %s' % (
        len(a.members['.SND']), len(base.b), m.clean() or 'walks clean (0 unclaimed, 0 overlap, 0 stray)', base.cut,
        a.members['.SND'][16:base.cut] == base.b[16:base.cut]))
    log('  objects stock -> merged: %s' % ', '.join('%s %d -> %d' % (NAMES[t], len(base.tables[t]), len(m.tables[t])) for t in sorted(m.tables)))
    log('  .WHD %d bytes (stock %d), %d records; wave references %d, hit no record: %d; in memory %d, with data %d; stream records added %d, not a clip of the merged PC_Def.str: %d' % (
        len(a.beside['.WHD']), os.path.getsize(beside(s_name, '.WHD')), c['.WHD records'], c['wave -> .WHD references'],
        c['wave -> .WHD references that hit no record'], c['in-memory records'], c['in-memory records with their data in the .WAV'], nstream, lost))
    log('  .WAV %d bytes (stock %d); offset map %d entries, %d to 0; _LS.SND first dword %s' % (
        len(a.beside['.WAV']), os.path.getsize(beside(s_name, '.WAV')), c['offset map entries'], c['offset map entries -> 0'],
        '= new T' if a.beside.get('_LS.SND') and u32(a.beside['_LS.SND'], 0) == m.T else 'NOT SET'))
    sounds = set(m.tables[1])
    for lang, d in sorted(a.members.items()):
        if lang == '.SND':
            continue
        t = kl_loc.parse(d)
        stock = kl_loc.parse(member(s_name, '_Main' + lang))
        if t is None:
            if d != member(s_name, '_Main' + lang):
                bad.append('%s: stub changed' % lang)
            continue
        old = {p: (k.flags, k.raw) for p, k in kl_loc.leaves(stock)}
        now = {p: k for p, k in kl_loc.leaves(t)}
        ids = [kl_loc.fields(k)[2] for p, k in now.items() if p not in old]
        ok = all(p in now and (now[p].flags, now[p].raw) == v for p, v in old.items()) and kl_loc.build(t) == d \
            and [p for p, _k in kl_loc.leaves(t) if p in old] == [p for p, _k in kl_loc.leaves(stock)]
        if not ok or any(i and i not in sounds for i in ids):
            bad.append('%s: stock leaves changed or a new id is no sound' % lang)
        if lang == 'English.LOC':
            log('  .LOC: %d leaves -> %d (%d added, %d with a sound of the merged bank); stock leaves and their order unchanged: %s' % (
                len(old), len(now), len(ids), sum(1 for i in ids if i in sounds), ok))
    for p in bad:
        log('  PROBLEM: ' + p)
    if out:
        os.makedirs(out, exist_ok=True)
        for ext, d in a.members.items():
            with open(os.path.join(out, 'F01_Main' + ext), 'wb') as f:
                f.write(d)
        a.write_beside(out, 'F01')
        with open(os.path.join(out, 'snd_map.json'), 'w') as f:
            json.dump({str(k): v for k, v in sorted(a.map.items())}, f)
        log('  written to %s' % out)
    return len(bad)


def test_banks(log=print):
    """Every stock bank of both games: walks clean, round-trips, base of a merge. -> failures"""
    fails = 0
    for g in ('dd', 'dm'):
        tot = collections.Counter()
        for lv in stock_levels(g):
            s = bank(lv, g)
            bad = s.clean()
            ok = round_trip(s)
            tot['banks'] += 1; tot['walk clean'] += not bad; tot['round trip'] += ok
            tot['items'] += len(s.items); tot['pointers'] += len(s.ptrs)
            tot['_LS first dword = T'] += bool(s.ls) and u32(s.ls, 0) == s.T
            tot['_LS banks'] += bool(s.ls)
            tot['build id is the game\'s'] += s.build == GAME[g]['build']
            if bad or not ok:
                fails += 1; log('  %s %s: %s; round trip %s' % (g, lv, bad, ok))
        log('%s .SND: %s' % (g, dict(tot)))
    for which in ('dd', 'merged'):
        p = stream_file(which)
        if os.path.isfile(p):
            build, clips = stream_index(p)
            log('stream file %s: build id %x (%s Dog Days banks\'), %d clip offsets' % (
                p, build, 'the' if build == GAME['dd']['build'] else 'NOT the', len(clips)))
            fails += build != GAME['dd']['build']
    return fails


def selftest(quick=False, log=print):
    fails = 0
    if not quick:
        fails += test_banks(log)
        fails += W.selftest(log)
        fails += kl_loc.selftest(log)
    fails += test_merge('F07', 'F09', log)
    fails += test_merge('F07', 'M01_FA_A', log)
    log('failures: %d' % fails)
    return fails


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['test']:
        sys.exit(1 if selftest('quick' in a) else 0)
    elif a[:1] == ['walk'] and len(a) == 2:
        s = bank(a[1])
        print(a[1], s.clean() or 'clean', dict(collections.Counter(t for n, t in s.items.values())), len(s.ptrs), 'pointers')
    elif a[:1] == ['merge'] and len(a) == 3:
        sys.exit(1 if test_merge(a[1], a[2], out=os.path.join(workdir(), 'build', 'audio', '%s+%s' % (a[1], a[2]))) else 0)
    else:
        print(__doc__)
