#!/usr/bin/env python3
"""
Kane & Lynch stream file (PC_Def.str and its language siblings, 'IOISNDSTREAM' version 9):
reader that accounts for every byte, the clips a grafted Dead Men level needs, and an
append-only merge into Dog Days' file. Both games. Spec with the evidence: re/retomoto_audio.md.

    python kl_str.py test [quick]            the selftest (quick: stock files only, 2 s; else 6 min
                                             and 3.3 GB written under <work>/build/str)
    python kl_str.py info <file.str>         header, clip counts, byte account
    python kl_str.py list <file.str> [text]  clips whose name holds text
    python kl_str.py need [level ...]        the stream clips the graft of these Dead Men levels
                                             needs (default: LEVELS), with sizes
    python kl_str.py build [level ...]       <work>/build/str/PC_Def.str (+ .map.json) = Dog Days'
                                             STOCK file + exactly those clips. --extend:
                                             <work>/build/str/extend/PC_Def.str = the current
                                             merged file <work>/build/PC_Def.str + what it lacks.
                                             Nothing is installed.
    python kl_str.py check <file.str> [level ...]   every stream record the levels need resolves

FILE (little endian; every count below is of this machine's files, 2026-10-09)
  0x00  'IOISNDSTREAM'
  0x0c  u32 9
  0x10  u64 build id          Dog Days PC_Def 4c08b8d5, Dead Men PC_Def 46e11c9f; every file of a
                              game has its OWN id (PC_Eng 4c08aec4 / 46e11909, PC_Fre 46e11f8e).
                              kl2 0x67e810 reads these 0x38 bytes and nothing else of the file
                              and compares the id with the .SND trailer (0x67e8ff / 0x67e90b).
  Dog Days                    Dead Men
  0x18  u64 index offset      0x18  u32 index offset
  0x20  u32 clip count        0x1c  u32 clip count
  0x24  u32 0x100             0x20  u32 0x100        (ASSUMPTION: the block alignment)
  0x28  u32 0                 0x24  u32 0
  0x2c  u32 1                 0x28  u32 1            (not established)
  0x30  u32 language          0x2c  u32 language     0 Def, 1 Eng, 2 Ger, 3 Fre, 4 Spa, 5 Ita (Dead
                                                     Men's five files; = the .SND stream-name order)
  0x34  u16 0x38, 2 junk      0x30  u16 0x38, 6 junk (0x38 = the header's size; the rest is stack fill)
  0x38  zero to 0x100
  0x100 DATA: one block per sound or interleaved set, each starting on a multiple of 0x100, in
        index-id order, zero padded to the next block.
        block = ['LIP ' block, 0x1000 bytes: 'LIP ', u32 length, lip-sync data] + audio
  ...   FORMAT TABLE (starts on a multiple of 0x100), one entry per clip in id order:
          u32 codec  2 = PCM 16 bit, 3 = IMA ADPCM (Dead Men only), 4 = Ogg Vorbis,
                     0x1a = the interleaved SET itself (its name is the sound project's layered
                     sound, 'LevelSetup/...'; a dialogue pair X + X_R has one named 'X_R' without
                     '.wav')
          u32 samples, u32 channels, u32 rate, u32 bits (16; ADPCM 4; Vorbis 0, or 16 in a set)
          8 bytes of junk (uninitialised: text of other names)
          PCM + u32 frame bytes (2 * channels); ADPCM + u32 0x400 block, u32 0x7f9 samples per
          block; set + u32 number of clips in it.   Sizes: Vorbis 28, PCM / set 32, ADPCM 36.
  ...   NAME TABLE: each name + NUL, id order, directly behind the format table
  ...   INDEX, directly behind the names, to the end of the file: 72 bytes per clip,
        SORTED BY NAME KEY (h = h * 5 + byte over the name as written, 32 bit):
          u64 id                (creation order: data, formats and names all ascend with it)
          u64 data offset       (of the BLOCK: the clips of a set all hold the same offset)
          u64 audio size        (a set's entry: of the whole set; without the LIP block)
          u64 format offset, u32 format size, u32 name key, u64 name length, u64 name offset
          u64 lip word          low dword 4 = this entry owns the block's LIP data, high dword a
                                small count (1..10; not decoded). = the .WHD record's 'lip' field
          u64 layer             0 = alone; n = n-th clip of a set (1-based); the set entry holds
                                the number of clips
  Stubs (PC_Eng.str of both games, 56 bytes): header only, index offset 0x100, 0 clips.

INTERLEAVED SETS (what the .WHD marks with the top format byte 0x82 / 0x01 ...)
  PCM: sample frames in turn. One period = for each clip in layer order (rate / lowest rate of
       the set) frames of its channels. Dialogue X (32 kHz mono) + X_R (16 kHz mono, the radio
       version): X X R; three stereo music layers: L1 R1 L2 R2 L3 R3; stereo 32 kHz + stereo
       16 kHz: L R L R l r. MEASURED by which de-interleaving gives smooth signals (5 sets).
       A clip's size = its own share; the shares add up to the set entry's size.
  Vorbis (Dog Days): ONE Ogg stream whose channel count is the sum (a pair of stereo layers = 4
       channels); the clips' sizes are total / n, nominal.
  Dead Men: 1,510 sets (1,486 X + X_R dialogue pairs). Dog Days: 79 (music and ambience layers,
  78 Vorbis and 1 PCM; its radio lines are separate Vorbis clips).

WHAT THE ENGINE USES. kl2.exe holds no 'IOISNDSTREAM' string and reads 0x38 bytes of the file
when a level names it; a level's .WHD record carries offset, size, rate, channels, codec and
the lip word itself. So the index is taken to be a build-tool table (ASSUMPTION: no code that
reads it at run time was looked for beyond that). merge() writes a complete, sorted one anyway.

MERGE (merge()). Append only: the base file's bytes from 0 to the end of its last data block
are copied unchanged, so no clip the base has moves (Dog Days' own, and with --extend also the
Dead Men clips of an earlier merge: levels built against the old .map.json stay valid). New
blocks follow, each on a multiple of 0x100 in Dead Men file order, copied whole (LIP block,
audio, and whatever stands before the next block); then one fresh format table, name table and
sorted index for all clips. Dead Men formats are copied as they are (nothing is re-encoded: the
level's .WHD record names the codec). Names are not used to decide anything
(12 of 6,739 Dead Men names are Dog Days names too, other recordings; 7 are members of wanted
sets and are entered a second time under their name, behind Dog Days' entry).
<out>.map.json: {Dead Men block offset: [new offset, bytes copied]} - what kl_snd.stream_map()
reads. With base = an earlier merge its tables are left behind as dead bytes (about 1 MB,
counted by account()), and the sets it entered by name only are completed in the index.

SELECTION (need()). For a Dead Men level: the roots kl_snd.graft_audio would take (sound
fields of the map-side nodes after kl_convert + the sound ids of the .LOC keys those nodes
name; for a Fragile Alliance level also every 'Multiplayer/' leaf: the voice lines), closed
over sets, sequences, definitions and waves the way kl_snd.merge closes them, then every
streamed PC_Def.str record of those waves with the other members of its set.
ASSUMPTION: 'map-side' = kl_prpjoin.sides, i.e. all a level has outside its systems. For a
story level that is MORE than kl_maps.campaign_drop leaves (the campaign's music, cut-scene
sound and squads' lines come along): wanted, because the authored Fragile Alliance layer picks
from them (kl_fa_author.CAMPAIGN_KEEP) and may pick others later.

NEVER TRIED IN THE RUNNING GAME: a file written by merge(). The earlier merge (kl_audio.merge)
is installed and levels load with it, but nobody has listened to a round yet.
"""
import collections, json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MAGIC = b'IOISNDSTREAM'
HEAD, REC, ALIGN, LIP = 0x38, 72, 0x100, 0x1000
PCM, ADPCM, VORBIS, SET = 2, 3, 4, 0x1a
CODEC = {PCM: 'pcm', ADPCM: 'adpcm', VORBIS: 'vorbis', SET: 'set'}
FMT_SIZE = {PCM: 32, ADPCM: 36, VORBIS: 28, SET: 32}
BUILD = {'dd': 0x4c08b8d5, 'dm': 0x46e11c9f}                 # PC_Def.str; = kl_snd.GAME[..]['build']
FA_LEVELS = ('M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A')
LEVELS = FA_LEVELS + ('M09_A', 'M09_B')                      # the six maps the merged file is built for
u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]


def name_key(name):
    """The index's sort key: h = h * 5 + byte over the name as written (5,926 of 5,926 and
    6,739 of 6,739 stock entries)."""
    h = 0
    for c in name.encode('latin1'):
        h = (h * 5 + c) & 0xffffffff
    return h


class Clip:
    """One index entry. offset is the BLOCK's (shared by the clips of a set)."""
    __slots__ = ('id', 'offset', 'size', 'fmt_at', 'fmt', 'key', 'name', 'name_at', 'lip', 'layer',
                 'codec', 'samples', 'channels', 'rate', 'bits')

    def record(self):
        return struct.pack('<4Q2I4Q', self.id, self.offset, self.size, self.fmt_at, len(self.fmt), self.key,
                           len(self.name.encode('latin1')), self.name_at, self.lip, self.layer)

    def __repr__(self):
        return '<%s %s %d Hz %d ch layer %d @%#x+%#x %s>' % (CODEC.get(self.codec, self.codec), self.samples, self.rate,
                                                             self.channels, self.layer, self.offset, self.size, self.name)


class Stream:
    """A stream file. clips: index order; blocks: {offset: [clips]}; game: 'dd' (64-bit index
    offset) or 'dm'."""

    def __init__(self, path):
        self.path, self.size = path, os.path.getsize(path)
        self.f = f = open(path, 'rb')
        h = f.read(HEAD)
        if h[:12] != MAGIC or u32(h, 12) != 9:
            raise ValueError('%s: not an IOISNDSTREAM version 9 file' % path)
        self.head = h
        self.build = struct.unpack_from('<Q', h, 0x10)[0]
        # Dead Men's count sits where Dog Days has the high dword of the offset: a file of 4 GB
        # would be needed to mistake one for the other
        if u32(h, 0x1c) == 0 and u32(h, 0x24) == ALIGN:
            self.game = 'dd'
            self.index, self.count, self.align, self.lang = struct.unpack_from('<QI', h, 0x18) + (u32(h, 0x24), u32(h, 0x30))
            rest = struct.unpack_from('<2I', h, 0x28) + struct.unpack_from('<H', h, 0x34)
        elif u32(h, 0x20) == ALIGN:
            self.game = 'dm'
            self.index, self.count, self.align, self.lang = struct.unpack_from('<4I', h, 0x18)[:3] + (u32(h, 0x2c),)
            rest = struct.unpack_from('<2I', h, 0x24) + struct.unpack_from('<H', h, 0x30)
        else:
            raise ValueError('%s: header of neither game' % path)
        if rest != (0, 1, HEAD):
            raise ValueError('%s: header fields %r, expected (0, 1, 0x38)' % (path, rest))
        self.clips, self.blocks, self._lip = [], collections.defaultdict(list), {}
        if not self.count:
            return
        if self.index + REC * self.count != self.size:
            raise ValueError('%s: the index does not end the file' % path)
        f.seek(self.index)
        raw = f.read(REC * self.count)
        recs = [struct.unpack_from('<4Q2I4Q', raw, REC * i) for i in range(self.count)]
        lo = min(min(r[3] for r in recs), min(r[7] for r in recs))
        f.seek(lo)
        tab = f.read(self.index - lo)                       # formats and names: one read (they stand together)
        def at(o, n):
            if lo <= o and o + n <= self.index:
                return tab[o - lo:o - lo + n]
            f.seek(o)
            return f.read(n)
        for r in recs:
            c = Clip()
            c.id, c.offset, c.size, c.fmt_at, fl, c.key, nl, c.name_at, c.lip, c.layer = r
            # stock: the length is the name's, a NUL follows; kl_audio.merge counted the NUL in
            c.fmt, c.name = at(c.fmt_at, fl), at(c.name_at, nl).decode('latin1').rstrip(chr(0))
            c.codec, c.samples, c.channels, c.rate, c.bits = struct.unpack_from('<5I', c.fmt)
            self.clips.append(c)
            self.blocks[c.offset].append(c)
        for l in self.blocks.values():
            l.sort(key=lambda c: (c.codec == SET, c.layer))

    def close(self):
        self.f.close()

    # ---- blocks
    def has_lip(self, off):
        if off not in self._lip:
            self.f.seek(off)
            self._lip[off] = self.f.read(4) == b'LIP '
        return self._lip[off]

    def length(self, off):
        """Bytes of the block at off by the index: LIP block + audio."""
        return (LIP if self.has_lip(off) else 0) + self.audio(off)

    def copy_length(self, off):
        """Bytes merge() copies for the block at off: up to the next block without the zero
        padding, at least length(); all of it when more than padding stands there (the tail of
        two Dead Men blocks)."""
        n, room = self.length(off), self.extents()[off] - off
        if room - n < ALIGN:
            return n
        self.f.seek(off + n)
        return n + len(self.f.read(room - n).rstrip(bytes(1)))

    def audio(self, off):
        """Bytes of audio the index gives the block at off (without the LIP block)."""
        l = self.blocks[off]
        sets = [c for c in l if c.codec == SET]
        return sets[0].size if sets else max(c.size for c in l)

    def table_start(self):
        """Offset of the first format or name entry behind the last data block."""
        last = max(self.blocks)
        return min([c.fmt_at for c in self.clips if c.fmt_at > last] + [c.name_at for c in self.clips if c.name_at > last])

    def extents(self):
        """{block offset: offset where the next thing starts} - the next block, or the first
        format / name entry behind it. What merge() copies for a block."""
        if '_ext' not in self.__dict__:
            marks = sorted(set(self.blocks) | {c.fmt_at for c in self.clips} | {c.name_at for c in self.clips} | {self.index})
            nxt = dict(zip(marks, marks[1:]))
            self._ext = {o: nxt[o] for o in self.blocks}
        return self._ext

    def read_block(self, off):
        self.f.seek(off)
        return self.f.read(self.extents()[off] - off)

    def find(self, name):
        """Clip by name the way a sorted index is searched (bisect on the key)."""
        import bisect
        if '_keys' not in self.__dict__:
            self._keys = [c.key for c in self.clips]
        k = name_key(name)
        i = bisect.bisect_left(self._keys, k)
        while i < len(self.clips) and self.clips[i].key == k:
            if self.clips[i].name == name:
                return self.clips[i]
            i += 1
        return None

    # ---- the whole file
    def account(self):
        """Claim every byte. -> (Counter of bytes by kind, [problems]).
        kinds: header, header pad, lip, audio, pad (zero bytes up to the next block), tail (bytes
        behind a block's audio that are not zero padding: two Dead Men blocks), format, name,
        index, dead (bytes nothing in the index names: the tables of an earlier merge)."""
        by, bad, f = collections.Counter(), [], self.f
        if not self.count:
            by['header'] = HEAD
            if self.size != HEAD:
                bad.append('no clips, but %d bytes' % self.size)
            return by, bad
        spans = [(0, HEAD, 'header'), (self.index, self.index + REC * self.count, 'index')]
        keys = [c.key for c in self.clips]
        if keys != sorted(keys):
            bad.append('the index is not sorted by name key')
        if sorted(c.id for c in self.clips) != list(range(self.count)):
            bad.append('the ids are not 0..count-1')
        for c in self.clips:
            if c.key != name_key(c.name):
                bad.append('%s: name key %#x' % (c.name, c.key))
            if len(c.fmt) != FMT_SIZE.get(c.codec):
                bad.append('%s: codec %d with a %d-byte format' % (c.name, c.codec, len(c.fmt)))
            spans.append((c.fmt_at, c.fmt_at + len(c.fmt), 'format'))
            spans.append((c.name_at, c.name_at + len(c.name) + 1, 'name'))
        for off, l in self.blocks.items():
            if off % ALIGN:
                bad.append('block %#x is not on a multiple of %#x' % (off, ALIGN))
            sets, parts = [c for c in l if c.codec == SET], [c for c in l if c.codec != SET]
            if len(l) > 1:
                if len(sets) != 1 or sets[0].layer != len(parts) or sorted(c.layer for c in parts) != list(range(1, len(parts) + 1)) \
                        or u32(sets[0].fmt, 28) != len(parts):
                    bad.append('block %#x: not one set entry over layers 1..n' % off)
                elif all(c.codec == PCM for c in parts) and sum(c.size for c in parts) != sets[0].size:
                    bad.append('block %#x: the PCM shares do not add up to the set' % off)
            elif l[0].layer or sets:
                bad.append('block %#x: a single clip with a layer number' % off)
            lip = LIP if self.has_lip(off) else 0
            if bool(lip) != any(c.lip & 0xffffffff == 4 for c in l) or sum(1 for c in l if c.lip) > 1:
                bad.append('block %#x: LIP block and lip words disagree' % off)
            if lip:
                spans.append((off, off + lip, 'lip'))
            spans.append((off + lip, off + lip + self.audio(off), 'audio'))
        spans.sort()
        pos = 0
        for a, b, kind in spans:
            if a < pos:
                bad.append('%s at %#x overlaps what stands before it (%#x)' % (kind, a, pos))
            elif a > pos:
                f.seek(pos)
                gap = f.read(a - pos)
                if pos == HEAD and not any(gap):
                    by['header pad'] += len(gap)
                elif kind in ('audio', 'lip', 'format') and len(gap) < ALIGN and not any(gap) and a % ALIGN == 0:
                    by['pad'] += len(gap)
                elif not any(gap[len(gap) - len(gap) % ALIGN:]) and any(gap) and len(gap) < 0x8000 and a % ALIGN == 0 and kind != 'index':
                    by['tail'] += len(gap) - len(gap) % ALIGN; by['pad'] += len(gap) % ALIGN
                    by['blocks with a tail'] += 0           # counted below
                    self.tails = getattr(self, 'tails', []) + [(pos, len(gap))]
                else:
                    by['dead'] += len(gap)
            by[kind] += b - a
            pos = max(pos, b)
        if pos != self.size:
            bad.append('the last item ends at %#x, the file at %#x' % (pos, self.size))
        by.pop('blocks with a tail', None)
        total = sum(by.values())
        if total != self.size and not bad:
            bad.append('%d bytes accounted for, %d in the file' % (total, self.size))
        return by, bad

    def summary(self):
        cc = collections.Counter(CODEC.get(c.codec, c.codec) for c in self.clips)
        sets = sum(1 for l in self.blocks.values() if len(l) > 1)
        return '%s: %s, build %08x, language %d, %d clips in %d blocks (%d sets), %s' % (
            os.path.basename(self.path), self.game, self.build, self.lang, self.count, len(self.blocks), sets, dict(cc))


# ------------------------------------------------------------------ paths
def paths():
    """-> dict: 'stock' Dog Days' own PC_Def.str (KL_PortBackup when it was moved there),
    'installed' the one in the game folder now, 'merged' <work>/build/PC_Def.str (kl_audio.merge,
    the one kl_snd.stream_map() describes), 'dm' Dead Men's, 'out' where build writes."""
    import kl_snd
    from kl_port_check import workdir
    dd, dm, w = kl_snd.game_dir('dd'), kl_snd.game_dir('dm'), workdir()
    bak = os.path.join(dd, 'KL_PortBackup', 'PC_Def.str')
    return {'stock': bak if os.path.isfile(bak) else os.path.join(dd, 'PC_Def.str'),
            'installed': os.path.join(dd, 'PC_Def.str'), 'merged': os.path.join(w, 'build', 'PC_Def.str'),
            'dm': os.path.join(dm, 'PC_Def.str'), 'out': os.path.join(w, 'build', 'str', 'PC_Def.str')}


def load_map(path):
    """<merged file>.map.json -> {Dead Men block offset: (new offset, bytes)}"""
    with open(path) as f:
        return {int(k): tuple(v) for k, v in json.load(f).items()}


# ------------------------------------------------------------------ selection
def closure(src, roots):
    """Objects of walked bank src that `roots` reach: over parameter targets, a sound's wave, the
    members of a set / definition and a sequence's targets - the rule of kl_snd.merge (its
    'kids'), without its reuse of base objects: for a Dead Men source only groups, materials and
    room effects are replaced there, and none of those leads to a wave. -> set of offsets"""
    import kl_snd
    d, kind, u16 = src.b, src.kind, kl_snd.u16
    seen, stack = set(), [r for r in roots if r]
    while stack:
        o = stack.pop()
        if o in seen or o not in kind:
            continue
        seen.add(o)
        t = kind[o]
        if t in (4, 7, 0x12, 0x13, 0x17):
            continue
        n, c = u16(d, o + 0x18), u32(d, o + 0x14)
        if u32(d, o + 0x10):
            for q in struct.unpack_from('<%dI' % u16(d, o + 0xc), d, u32(d, o + 0x10)):
                if u32(d, q) == 0x13 and u32(d, q + 0x1c): stack.append(u32(d, q + 0x1c))
        if t == 1 and c and c < src.T: stack.append(c)
        elif t in (2, 5) and c: stack += [x for x in struct.unpack_from('<%dI' % n, d, c) if x]
        elif t == 3 and c: stack += [u32(d, c + 12 * i + 8) for i in range(n) if u32(d, c + 12 * i) in (2, 4, 5, 6)]
    return seen


def level_roots(level, voice=None, log=None):
    """Roots in the .SND of Dead Men level `level` that its graft takes: sound fields of the
    map-side nodes (kl_snd.map_scene: after kl_convert, as kl_graft sees them), sound ids of the
    .LOC keys those nodes name, and with voice (default: for a Fragile Alliance level) of every
    'Multiplayer/' leaf. -> (set of offsets, Counter)"""
    import zipfile, kl_snd, kl_loc
    st = collections.Counter()
    sc, ks = kl_snd.map_scene(level)
    rs = kl_snd.roots(sc, ks)
    st['sound references on map-side nodes'] = len(rs)
    with zipfile.ZipFile(kl_snd.level_zip(level, 'dm')) as zf:
        loc = zf.read(kl_loc.members(zf)['English'])
    named = {s.lower().replace('\\', '/') for s in kl_snd.strings_of(sc, ks)}
    voice = level in FA_LEVELS if voice is None else voice
    for p, k in kl_loc.leaves(kl_loc.parse(loc)):
        sid = kl_loc.fields(k)[2]
        if not sid:
            continue
        if p.lower() in named:
            rs.add(sid); st['.LOC keys the map names'] += 1
        elif voice and p.lower().startswith('multiplayer/'):
            rs.add(sid); st['Multiplayer/ voice leaves'] += 1
    return rs, st


def need(levels=LEVELS, voice=None, log=None, roots=None):
    """The stream clips the grafts of Dead Men `levels` need.
    -> ({Dead Men block offset in its PC_Def.str: sorted [.WHD record names]}, {level: Counter}).
    roots: {level: extra .SND offsets} to carry beyond level_roots()."""
    import kl_snd, kl_whd as W
    want, stats = collections.defaultdict(set), {}
    for level in levels:
        rs, st = level_roots(level, voice)
        rs |= set((roots or {}).get(level, ()))
        src = kl_snd.bank(level, 'dm')
        whd = kl_snd.read(kl_snd.beside(level, '.WHD', 'dm'))
        recs = W.records('dm', whd)
        objs = closure(src, rs)
        st['roots'], st['objects reached'] = len(rs), len(objs)
        for o, _i, at in src.waves():
            if o not in objs:
                continue
            f = recs.get(at)
            if f is None or not f['fmt'] & W.STREAMED:
                st['waves in memory' if f else 'waves that name no .WHD record'] += 1
                continue
            if f['fmt'] & W.LANGFILE:
                st['records of a language file (not merged)'] += 1
                continue
            members = W.group_of('dm', recs, at) if f['fmt'] >> 24 else [at]
            if members is None:
                st['records of a torn set (left out, as kl_snd.merge does)'] += 1
                continue
            for m in members:
                want[recs[m]['off']].add(kl_snd.cs(whd, recs[m]['name']).decode('latin1'))
            st['stream records'] += 1
        st['blocks'] = len({recs[at]['off'] for o, _i, at in src.waves() if o in objs and at in recs
                            and recs[at]['fmt'] & W.STREAMED and not recs[at]['fmt'] & W.LANGFILE} & set(want))
        stats[level] = st
        if log:
            log('  %-9s %s' % (level, dict(st)))
    return {o: sorted(n) for o, n in want.items()}, stats


# ------------------------------------------------------------------ merge
def merge(base_path, dm_path, want, out_path, prior=None, log=print):
    """Write out_path = the base file (Dog Days' PC_Def.str, or an earlier merge of it) + the
    Dead Men blocks `want` (block offsets in dm_path; need()'s keys).
    prior: {Dead Men block offset: (offset in the base, bytes)} when the base is an earlier merge
    (its .map.json): those blocks are not copied again and stay in the new map.
    Every byte of the base below the end of its last data block keeps its place.
    -> dict(map={Dead Men block offset: (new offset, bytes)}, added=[Clip], bytes_added=..,
    size=.., base_size=..). Also writes out_path + '.map.json'."""
    base, dm = Stream(base_path), Stream(dm_path)
    if base.game != 'dd' or dm.game != 'dm':
        raise ValueError('merge: the base must be a Dog Days file, the source a Dead Men one')
    if os.path.abspath(out_path).lower() in (os.path.abspath(base_path).lower(), os.path.abspath(dm_path).lower()):
        raise ValueError('merge: the output may not be one of the inputs')
    prior = dict(prior or {})
    missing = [o for o in want if o not in dm.blocks]
    if missing:
        raise ValueError('merge: %d wanted offsets are no block of %s (first %#x)' % (len(missing), dm_path, missing[0]))
    for o, (at, _n) in prior.items():
        if at not in base.blocks:
            raise ValueError('merge: the prior map names %#x, no block of the base' % at)
    back = {at: o for o, (at, _n) in prior.items()}
    end = data_end(base, dm, back)
    ext_b = base.extents()                                  # before the base's clips get their new table offsets
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    placed, added, clips = dict(prior), [], []
    with open(out_path, 'wb') as out:
        base.f.seek(0)
        left = end
        while left:
            chunk = base.f.read(min(left, 32 << 20))
            if not chunk:
                out.write(bytes(left)); break               # the last block ended the data without padding
            out.write(chunk); left -= len(chunk)
        for o in sorted(set(want) - set(prior)):
            n = dm.copy_length(o)
            out.write(bytes(-out.tell() % ALIGN))
            placed[o] = (out.tell(), n)
            dm.f.seek(o)
            out.write(dm.f.read(n))
        out.write(bytes(-out.tell() % ALIGN))
        # one table for all: the base's clips keep their ids, the new ones follow in Dead Men id order
        for c in sorted(base.clips, key=lambda c: c.id):
            clips.append(c)
        have = {(c.name, c.offset) for c in base.clips}
        names = {c.name for c in base.clips}
        nid, twice = len(clips), 0
        # blocks of an earlier merge first: kl_audio.merge entered only the names its filter
        # matched, so most of its sets lack members and the set entry; they are completed here
        for o in sorted(prior, key=lambda o: prior[o][0]) + sorted(set(want) - set(prior)):
            for c in sorted(dm.blocks[o], key=lambda c: c.id):
                if (c.name, placed[o][0]) in have:
                    continue                                # entered by the earlier merge
                # 12 Dead Men names are Dog Days names too (other recordings: Sniper_0n0_Lynch,
                # Die_Helper_00n_Lynch, AirlockLynch_0n0_Lynch); 7 are members of wanted sets. The
                # clip is entered under its own name all the same: the base's entry has the lower
                # id and stays the first of that key, a level names a clip by offset
                twice += c.name in names
                n = Clip()
                for a in Clip.__slots__:
                    setattr(n, a, getattr(c, a))
                n.id, n.offset = nid, placed[o][0]
                nid += 1
                clips.append(n); added.append(n); names.add(n.name)
        fmt_at = out.tell()
        for c in clips:
            c.fmt_at = out.tell(); out.write(c.fmt)
        for c in clips:
            c.name_at = out.tell(); out.write(c.name.encode('latin1') + b'\0')
        index = out.tell()
        for c in sorted(clips, key=lambda c: (c.key, c.id)):
            out.write(c.record())
        size = out.tell()
        out.seek(0)
        h = bytearray(base.head)
        struct.pack_into('<QI', h, 0x18, index, len(clips))
        out.write(h)
    # kl_audio's map held one clip's size: write the bytes of the block the base really holds
    # (it cut the tail of Dead Men block 0x5f27300; the index size of that clip is all there)
    short = 0
    for o, (at, n) in prior.items():
        n = min(dm.copy_length(o), ext_b[at] - at)
        short += n < dm.copy_length(o)
        placed[o] = (at, n)
    res = dict(map=placed, added=added, size=size, base_size=base.size, data_end=end, tables=fmt_at,
               bytes_added=size - base.size, blocks_added=len(set(want) - set(prior)), names_twice=twice, prior_short=short)
    with open(out_path + '.map.json', 'w') as f:
        json.dump({str(k): list(v) for k, v in sorted(placed.items())}, f)
    log('  %s: %d Dead Men blocks (%d clips) added behind %#x; %d bytes (base %d, +%.1f MB); %d clips' % (
        out_path, res['blocks_added'], len(added), end, size, base.size, (size - base.size) / 2 ** 20, len(clips)))
    base.close(); dm.close()
    return res


def data_end(base, dm=None, back=None):
    """Where the base's data ends (a multiple of 0x100): behind its last block. back: {offset in
    the base: Dead Men block offset} for the blocks of an earlier merge, whose length is taken
    from Dead Men's file (the earlier merge's index does not give it for a set)."""
    last = max(base.blocks)
    end = last + (dm.copy_length(back[last]) if back and last in back else base.length(last))
    return end + -end % ALIGN


def verify(out_path, base_path, dm_path, placed, log=print, prior=None):
    """Re-read a merged file: every byte accounted for, the base's clips where they were and
    byte-identical data below the base's data end, every placed Dead Men block equal to its
    source, every Dead Men clip of a placed block in the index with its format. -> [problems]"""
    import hashlib
    m, base, dm = Stream(out_path), Stream(base_path), Stream(dm_path)
    by, bad = m.account()
    if m.build != base.build or m.head[:0x18] != base.head[:0x18] or m.head[0x24:] != base.head[0x24:]:
        bad.append('header differs from the base beyond index offset and count')
    for c in base.clips:
        n = m.find(c.name)
        if n is None or (n.offset, n.size, n.fmt, n.lip, n.layer) != (c.offset, c.size, c.fmt, c.lip, c.layer):
            bad.append('base clip %s moved or changed' % c.name)
            if len(bad) > 20: break
    end = data_end(base, dm, {at: o for o, (at, _n) in (prior or {}).items()})
    ha, hb = hashlib.sha1(), hashlib.sha1()
    for f, h in ((m.f, ha), (base.f, hb)):
        f.seek(0x38); left = end - 0x38
        while left:
            chunk = f.read(min(left, 32 << 20)); h.update(chunk); left -= len(chunk)
    if ha.digest() != hb.digest():
        bad.append('bytes 0x38..%#x differ from the base' % end)
    n_clip = 0
    for o, (at, n) in placed.items():
        if at not in m.blocks:
            bad.append('placed block %#x is no block of the merged file' % at); continue
        dm.f.seek(o); m.f.seek(at)
        if dm.f.read(n) != m.f.read(n):
            bad.append('block %#x differs from Dead Men %#x' % (at, o))
        got = {c.name: c for c in m.blocks[at]}
        for c in dm.blocks[o]:
            g = got.get(c.name)
            n_clip += 1
            if g is None or (g.size, g.fmt, g.lip, g.layer, g.key) != (c.size, c.fmt, c.lip, c.layer, c.key):
                bad.append('clip %s of block %#x is not in the index as Dead Men has it' % (c.name, at))
    log('  verify %s: %s; %d base clips, %d placed blocks (%d clips); %d problems' % (
        os.path.basename(out_path), dict(by), len(base.clips), len(placed), n_clip, len(bad)))
    for x in (m, base, dm):
        x.close()
    return bad


def check_levels(str_path, levels=LEVELS, s_name='F07', log=print, strmap=None):
    """Every stream record the grafted levels' merged banks hold resolves into str_path.
    For each level: kl_snd.merge of stock s_name + the level with need()'s roots and the file's
    .map.json, then every streamed PC_Def.str record of the merged .WHD must be the offset of a
    block of str_path, the bank's build id must be the file's, and no clip may be reported
    missing. -> [problems]"""
    import kl_snd, kl_whd as W
    m = Stream(str_path)
    strmap = strmap or {k: v[0] for k, v in load_map(str_path + '.map.json').items()}
    bad = []
    base = kl_snd.bank(s_name)
    b_whd, b_wav = kl_snd.read(kl_snd.beside(s_name, '.WHD')), kl_snd.read(kl_snd.beside(s_name, '.WAV'))
    for level in levels:
        rs, _st = level_roots(level)
        src = kl_snd.bank(level, 'dm')
        st = collections.Counter()
        snd, whd, wav, omap = kl_snd.merge(base, src, b_whd, b_wav, kl_snd.read(kl_snd.beside(level, '.WHD', 'dm')),
                                           kl_snd.read(kl_snd.beside(level, '.WAV', 'dm')), rs, strmap=strmap, log=lambda *a: None, stats=st)
        new = kl_snd.Snd('dd', snd)
        T = u32(b_whd, 0)
        recs = W.records('dd', whd)
        streams = [(r, f) for r, f in recs.items() if f['fmt'] & W.STREAMED and not f['fmt'] & W.LANGFILE]
        miss = [r for r, f in streams if (f['off'] | f['offhi'] << 32) not in m.blocks]
        added = sum(1 for r, f in streams if r >= T)
        over = 0
        for r, f in streams:                                # the record's data has to lie inside its block
            o = f['off'] | f['offhi'] << 32
            if o in m.blocks and r >= T and f['size'] > m.audio(o):
                over += 1
        lost = st['stream clips not in the merged stream file'] + st['stream clips of a group that is torn in the source or not in the merged stream file']
        log('  %s + %-9s roots %d: %d stream records (%d added), %d resolve to no block, %d larger than their block, %d clips missing, build %08x' % (
            s_name, level, len(rs), len(streams), added, len(miss), over, lost, new.build))
        if miss: bad.append('%s: %d stream records name no block of %s' % (level, len(miss), os.path.basename(str_path)))
        if over: bad.append('%s: %d added stream records are larger than their block' % (level, over))
        if lost: bad.append('%s: %d stream clips not in the file' % (level, lost))
        if new.build != m.build: bad.append('%s: bank build id %08x, stream file %08x' % (level, new.build, m.build))
    m.close()
    return bad


# ------------------------------------------------------------------ level music
# Sound objects ('audio:<name>#sound') of a Dead Men story level's bank that are its music, the
# level's main theme first. Each pair is the two layers of ONE interleaved stream set (they
# share a block and play in step); re/retomoto_audio.md section 4 has what the campaign does
# with them.
MUSIC = {
    'M09_A': ('levelsetup/level/m09_a/music/tokyoaction_v3_44_layer1_loop',         # action theme, from the window blast on
              'levelsetup/level/m09_a/music/tokyoaction_layer2_tambient_loop',      # its tension layer
              'levelsetup/level/m09_a/music/rooftop_v2_new_44_layer1_loop',         # roof
              'levelsetup/level/m09_a/music/rooftop_layer2_tambient_loop',
              'levelsetup/level/m09_a/music/tokyorappel_v2_wind'),                  # rappel (wind, one layer)
    'M09_B': ('levelsetup/level/m09_a/music/tokyoaction2a_mainguitar_layer1',       # street theme
              'levelsetup/level/m09_a/music/tokyoaction2b_mainguitaretnic_layer2',
              'levelsetup/level/m09_a/music/tokyoaction_v3_44_layer1_loop'),        # the end of the level
}


def sound_offset(level, name, kind='sound'):
    """Offset of object 'audio:<name>#<kind>' in the .SND of stock level `level` (what a sound
    field of that level holds, and the key of kl_snd.graft_audio's map)."""
    import kl_snd
    src = kl_snd.bank(level)
    want = ('audio:%s#%s' % (name.lower(), kind)).encode('latin1')
    for o, t in src.kind.items():
        if t != 4 and src.name(o) == want:
            return o
    raise KeyError('%s: no %s' % (level, want.decode()))


def music_roots(level):
    """Offsets of MUSIC[level] in the level's .SND, for graft_audio(more_roots=...)."""
    return [sound_offset(level, n) for n in MUSIC.get(level, ())]


def set_fa_music(sc, offset, field=157, log=print):
    """Write a sound of the MERGED bank into field 157 of the Fragile Alliance settings of the
    joined property tree sc (kl_prpjoin.Scene, Dog Days form). kl2 0x88edba: the settings' Init
    hands that field to the game mode (0x8736d0: [0x168e958]+0x944), which starts it at once as
    a 2-D sound it keeps (0x8ce720) - from the level load on, not from the round start - and
    replaces it by field 158 when the local player turns traitor (0x67f0a9). All nine stock
    levels hold 0. -> number of settings objects written."""
    import kl_fa
    n = 0
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            continue
        def fn(us):
            us[field] = [(us[field][0][0], struct.pack('<I', offset))]
        kl_fa.edit(sc, k, i, fn)
        n += 1
    log('  kl_str: settings field %d = %#x on %d settings object(s)' % (field, offset, n))
    return n


# ------------------------------------------------------------------ tests / command line
def test_stock(log=print):
    """Every stream file of both games: read, account for every byte."""
    import glob, kl_snd
    bad, P = [], paths()
    files = [P['stock']] + sorted(glob.glob(os.path.join(kl_snd.game_dir('dd'), 'PC_*.str'))) + \
            sorted(glob.glob(os.path.join(kl_snd.game_dir('dm'), 'PC_*.str'))) + [P['merged']]
    seen = set()
    for p in files:
        if p.lower() in seen or not os.path.isfile(p):
            continue
        seen.add(p.lower())
        s = Stream(p)
        by, b = s.account()
        log('  ' + s.summary())
        log('      %s -> %d of %d bytes%s' % (dict(by), sum(by.values()), s.size, ''.join('; ' + x for x in b[:2])))
        if getattr(s, 'tails', None):
            log('      tails: ' + ', '.join('%#x (%#x bytes)' % t for t in s.tails))
        stock = p != P['merged'] and (p == P['stock'] or os.path.getsize(p) != os.path.getsize(P['merged']))
        if stock and (b or by['dead']):
            bad.append('%s: %s' % (p, b[:3] or 'dead bytes in a stock file'))
        elif b:                                             # the earlier merge (kl_audio.merge): reported, not a failure of this reader
            log('      NOTE not a stock file: %d sets without their set entry or a member; %d bytes no index entry names' % (
                sum(1 for x in b if 'set entry' in x), by['dead']))
        s.close()
    return bad


def build(levels=LEVELS, extend=False, out=None, log=print):
    """need() + merge() + verify(). extend: base = the current merged file with its map (nothing
    that is built against it goes stale); else Dog Days' stock file. -> (out path, problems)"""
    P = paths()
    out = out or (os.path.join(os.path.dirname(P['out']), 'extend', 'PC_Def.str') if extend else P['out'])
    log('selection for %s:' % ', '.join(levels))
    want, _st = need(levels, log=log)
    dm = Stream(P['dm'])
    cost = sum(dm.extents()[o] - o for o in want)
    log('  %d blocks, %d clips, %.1f MB in Dead Men\'s file' % (len(want), sum(len(dm.blocks[o]) for o in want), cost / 2 ** 20))
    dm.close()
    base, prior = (P['merged'], load_map(P['merged'] + '.map.json')) if extend else (P['stock'], None)
    if extend:
        log('  base = %s: %d of the %d blocks are in it already' % (base, len(set(want) & set(prior)), len(want)))
    res = merge(base, P['dm'], want, out, prior, log)
    bad = verify(out, base, P['dm'], res['map'], log, prior)
    return out, bad


def selftest(quick=False, log=print):
    bad = []
    log('1. stock files')
    bad += test_stock(log)
    if not quick:
        import tempfile
        log('2. merge for %s (stock base)' % ', '.join(LEVELS))
        out, b = build(log=log)
        bad += b
        log('3. every stream record of the six grafted banks against it')
        bad += check_levels(out, log=log)
        log('4. the same, base = the current merged file (--extend)')
        out2, b = build(extend=True, log=log)
        bad += b
        bad += check_levels(out2, log=log)
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    for x in bad:
        log('  ' + x)
    return not bad


def main(a):
    cmd = a[0] if a else 'test'
    flags = {x for x in a[1:] if x.startswith('--')}
    rest = [x for x in a[1:] if not x.startswith('--')]
    if cmd == 'test':
        return 0 if selftest('quick' in rest) else 1
    if cmd == 'info':
        s = Stream(rest[0])
        by, bad = s.account()
        print(s.summary()); print(dict(by)); print('problems:', bad or 'none')
    elif cmd == 'list':
        s = Stream(rest[0])
        for c in sorted(s.clips, key=lambda c: (c.offset, c.codec == SET, c.layer)):
            if len(rest) < 2 or rest[1].lower() in c.name.lower():
                print('%-6s %8.1f s %5d Hz %d ch layer %d  %#11x +%#9x  %s' % (
                    CODEC.get(c.codec, c.codec), c.samples / max(1, c.rate), c.rate, c.channels, c.layer, c.offset, c.size, c.name))
    elif cmd == 'need':
        want, _st = need(rest or LEVELS, log=print)
        dm = Stream(paths()['dm'])
        print('%d blocks, %.1f MB' % (len(want), sum(dm.extents()[o] - o for o in want) / 2 ** 20))
        if '--names' in flags:
            for o in sorted(want):
                print('  %#11x %9d  %s' % (o, dm.extents()[o] - o, ' | '.join(want[o])))
    elif cmd == 'build':
        out, bad = build(rest or LEVELS, '--extend' in flags)
        bad += check_levels(out, rest or LEVELS)
        print('RESULT: %s  %s' % ('PASS' if not bad else 'FAIL', out))
        for x in bad:
            print('  ' + x)
        return 1 if bad else 0
    elif cmd == 'check':
        bad = check_levels(rest[0], rest[1:] or LEVELS)
        print('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
        for x in bad:
            print('  ' + x)
        return 1 if bad else 0
    else:
        print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
