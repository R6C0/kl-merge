#!/usr/bin/env python3
"""
Payday 2 audio streams (`soundbanks/streamed/<bank>/<wem id>.stream` in the crates, 74,437 entries,
6.74 GB raw, none zlib) - reader and pure-Python decoder (3.14, no numpy). Everything below was
measured on all 74,437 entries on 2026-10-10 (Steam build 25506656); re/pd2_audio.md has the tables.

    python tools/pd2_audio.py info <stream>                 RIFF chunks, format, blocks, duration
    python tools/pd2_audio.py wav  <stream> <out.wav>       decode to 16-bit PCM WAV (same rate and channels)
    python tools/pd2_audio.py rms  <stream> [<window s>]    RMS per window of the decoded signal (silence check)
    python tools/pd2_audio.py survey                        fmt header of all 74,437 streams -> <work>/pd2/audio/
                                                            stream_headers.json (15 s) and the tag / rate table
    python tools/pd2_audio.py banks                         soundbanks/music.bnk: track_NN -> stream ids
                                                            (track_streams.json) and the jukebox names from
                                                            strings/menu + hud .strings (track_names.json)
    python tools/pd2_audio.py bank <name|file.bnk> [<outdir>]
                                                            a soundbank's embedded clips (BKHD / DIDX / DATA): id, format, rate,
                                                            seconds; with <outdir> each PTADPCM clip is decoded to <id>.wav.
                                                            <name> = soundbanks/<name> read from the crates (e.g. weapon_akm)
    python tools/pd2_audio.py tracks [<name>]               the music tracks with sizes and durations (needs both)
  <stream> = a file extracted with pd2_crate.py, or a crate path such as
  soundbanks/streamed/music/121224598 (read straight from the crates).

FORMAT. Every stream is a Wwise .wem: RIFF/WAVE with chunks `fmt ` (24 bytes), `hash` (16: 'hash', 12
bytes of digest - ASSUMPTION: Wwise's source-file hash), `junk` (12, zero) and `data`; short
stingers also carry `cue ` and `LIST`; Vorbis ones have no junk. Format tags over all
74,437 entries (fmt: tag, channels, rate, bits, block align, cbSize 6, extra = u16 0, u32 channel config):
  0x8311  66,800  Wwise PTADPCM ("Platinum ADPCM", Wwise 2019.2+), 4 bits, block 0x24 per channel
                  (0x48 stereo, one 4-channel 0x90), extra 00 00 | 01 41 00 00 (mono: 1 ch, type 1,
                  mask 0x4 = FC) or 02 31 00 00 (stereo, mask 0x3 = FL FR). Rates: 32000 x 30,255,
                  44100 x 29,340, 36000 x 7,049, 28000 x 156 (mono 64,553, stereo 2,246 - of them 679
                  44.1 kHz music streams).
  0xFFFF   7,622  Wwise Vorbis (bits 0, block 0, cbSize 48): voice lines (robbers_mission_gen 2,069,
                  char_* heisters, regular_vox ...), 48000 x 4,760, 44100 x 2,525, 36000 x 262, 32000 x 75.
                  NOT decoded here (Wwise Vorbis needs the packed codebooks; vgmstream / ww2ogg do it).
  0xFFFE      15  PCM 16 bit mono 44.1 kHz (ambiences 10, hud 3, ...).
  THE FIRST READING ('tag 0x11 = IMA ADPCM') WAS WRONG: 0x8311 only ends in 0x11. The block header
  proves PTADPCM: {s16 hist2, s16 hist1, u8 index 0..12, 31 bytes = 62 nibbles} = 64 samples per
  36-byte frame (an IMA block would have {s16 sample, u8 step 0..88, u8 0}: byte 3 is NOT zero here,
  byte 4 never exceeds 12 - measured on 5,000 blocks of two files). Stereo: frame L then frame R.
  Decoder = vgmstream's decode_ptadpcm (coding/ptadpcm_decoder.c, reverse engineered from the Wwise
  plugin): sample = clamp16(step + 2*hist1 - hist2), (step, next index) = TABLE[index][nibble], low
  nibble first; the two header samples are output first. The table below is that one.
  duration = data bytes / (channels * 36) * 64 / rate.

KANE & LYNCH SIDE (tools/kl_str.py merge): Dog Days' PC_Def.str takes codec 2 = PCM 16 bit (any
rate; stock music is stereo 32 kHz, PCM sets of 2-3 stereo layers), 3 = IMA ADPCM (block 0x400 -
Dead Men only, never seen working in Dog Days) and 4 = Ogg Vorbis. So a Payday 2 track goes in as
`wav` writes it: interleaved 16-bit PCM, stereo, its own rate (44.1 kHz is 1.38 x the size of 32 kHz;
kl_str records the rate per clip, nothing in it resamples). The Wwise PTADPCM blocks themselves can NOT
be appended (no Glacier codec plays them).
"""
import os
import struct
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# vgmstream ptadpcm_table[index][nibble] = (step, next index); indices 0..12 are used (12 = all zero).
_T = [
    [(-14, 2), (-10, 2), (-7, 1), (-5, 1), (-3, 0), (-2, 0), (-1, 0), (0, 0), (0, 0), (1, 0), (2, 0), (3, 0), (5, 1), (7, 1), (10, 2), (14, 2)],
    [(-28, 3), (-20, 3), (-14, 2), (-10, 2), (-7, 1), (-5, 1), (-3, 1), (-1, 0), (1, 0), (3, 1), (5, 1), (7, 1), (10, 2), (14, 2), (20, 3), (28, 3)],
    [(-56, 4), (-40, 4), (-28, 3), (-20, 3), (-14, 2), (-10, 2), (-6, 2), (-2, 1), (2, 1), (6, 2), (10, 2), (14, 2), (20, 3), (28, 3), (40, 4), (56, 4)],
    [(-112, 5), (-80, 5), (-56, 4), (-40, 4), (-28, 3), (-20, 3), (-12, 3), (-4, 2), (4, 2), (12, 3), (20, 3), (28, 3), (40, 4), (56, 4), (80, 5), (112, 5)],
    [(-224, 6), (-160, 6), (-112, 5), (-80, 5), (-56, 4), (-40, 4), (-24, 4), (-8, 3), (8, 3), (24, 4), (40, 4), (56, 4), (80, 5), (112, 5), (160, 6), (224, 6)],
    [(-448, 7), (-320, 7), (-224, 6), (-160, 6), (-112, 5), (-80, 5), (-48, 5), (-16, 4), (16, 4), (48, 5), (80, 5), (112, 5), (160, 6), (224, 6), (320, 7), (448, 7)],
    [(-896, 8), (-640, 8), (-448, 7), (-320, 7), (-224, 6), (-160, 6), (-96, 6), (-32, 5), (32, 5), (96, 6), (160, 6), (224, 6), (320, 7), (448, 7), (640, 8), (896, 8)],
    [(-1792, 9), (-1280, 9), (-896, 8), (-640, 8), (-448, 7), (-320, 7), (-192, 7), (-64, 6), (64, 6), (192, 7), (320, 7), (448, 7), (640, 8), (896, 8), (1280, 9), (1792, 9)],
    [(-3584, 10), (-2560, 10), (-1792, 9), (-1280, 9), (-896, 8), (-640, 8), (-384, 8), (-128, 7), (128, 7), (384, 8), (640, 8), (896, 8), (1280, 9), (1792, 9), (2560, 10), (3584, 10)],
    [(-7168, 11), (-5120, 11), (-3584, 10), (-2560, 10), (-1792, 9), (-1280, 9), (-768, 9), (-256, 8), (256, 8), (768, 9), (1280, 9), (1792, 9), (2560, 10), (3584, 10), (5120, 11), (7168, 11)],
    [(-14336, 11), (-10240, 11), (-7168, 11), (-5120, 11), (-3584, 10), (-2560, 10), (-1536, 10), (-512, 9), (512, 9), (1536, 10), (2560, 10), (3584, 10), (5120, 11), (7168, 11), (10240, 11), (14336, 11)],
    [(-28672, 11), (-20480, 11), (-14336, 11), (-10240, 11), (-7168, 11), (-5120, 11), (-3072, 11), (-1024, 10), (1024, 10), (3072, 11), (5120, 11), (7168, 11), (10240, 11), (14336, 11), (20480, 11), (28672, 11)],
    [(0, 0)] * 16,
]
TAG_NAMES = {0x8311: 'Wwise PTADPCM', 0xffff: 'Wwise Vorbis', 0xfffe: 'PCM 16', 0x0002: 'Wwise IMA ADPCM', 0x0001: 'PCM'}


class Stream:
    """A parsed .wem: fmt fields and the data chunk."""

    def __init__(self, data, name='?'):
        self.name = name
        if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
            raise ValueError('%s: not a RIFF WAVE' % name)
        self.chunks = []
        p = 12
        self.fmt = self.data = None
        while p + 8 <= len(data):
            cid, sz = data[p:p + 4], struct.unpack_from('<I', data, p + 4)[0]
            self.chunks.append((cid.decode('latin-1'), sz))
            if cid == b'fmt ':
                self.fmt = data[p + 8:p + 8 + sz]
            elif cid == b'data':
                self.data = data[p + 8:p + 8 + sz]
            p += 8 + sz + (sz & 1)
        if self.fmt is None or self.data is None:
            raise ValueError('%s: no fmt / data chunk' % name)
        self.tag, self.channels, self.rate, self.byte_rate, self.block, self.bits = struct.unpack_from('<HHIIHH', self.fmt)
        self.cb = struct.unpack_from('<H', self.fmt, 16)[0] if len(self.fmt) >= 18 else 0
        self.extra = self.fmt[18:18 + self.cb]

    @property
    def frame(self):
        return self.block // self.channels          # 0x24 per channel

    @property
    def samples(self):
        """Sample frames (per channel)."""
        if self.tag == 0x8311:
            return (len(self.data) // self.block) * (2 + (self.frame - 5) * 2)
        if self.tag == 0xfffe:
            return len(self.data) // (2 * self.channels)
        return 0

    @property
    def seconds(self):
        return self.samples / self.rate if self.rate else 0.0

    def decode(self):
        """-> list of channel lists of int16 (PTADPCM and PCM 16)."""
        if self.tag == 0xfffe:
            n = len(self.data) // 2
            flat = struct.unpack('<%dh' % n, self.data[:2 * n])
            return [list(flat[c::self.channels]) for c in range(self.channels)]
        if self.tag != 0x8311:
            raise ValueError('%s: tag 0x%x (%s) is not decoded here' % (self.name, self.tag, TAG_NAMES.get(self.tag, '?')))
        return [self._decode_channel(c) for c in range(self.channels)]

    def _decode_channel(self, c):
        d, fs, ch, T = self.data, self.frame, self.channels, _T
        nblk = len(d) // self.block
        out = [0] * (nblk * (2 + (fs - 5) * 2))
        w = 0
        unpack = struct.unpack_from
        for b in range(nblk):
            o = b * self.block + c * fs
            hist2, hist1 = unpack('<hh', d, o)
            index = d[o + 4]
            if index > 12:
                index = 12
            out[w] = hist2
            out[w + 1] = hist1
            w += 2
            row = T[index]
            for byte in d[o + 5:o + fs]:
                for nib in (byte & 15, byte >> 4):
                    step, index = row[nib]
                    s = step + 2 * hist1 - hist2
                    if s > 32767:
                        s = 32767
                    elif s < -32768:
                        s = -32768
                    out[w] = s
                    w += 1
                    hist2, hist1 = hist1, s
                    row = T[index]
        return out


def load(arg):
    """A Stream from a file on disk or a crate path (soundbanks/streamed/...)."""
    if os.path.isfile(arg):
        with open(arg, 'rb') as f:
            return Stream(f.read(), os.path.basename(arg))
    import pd2_crate
    ix = pd2_crate.Index(quiet=True)
    e = ix.get(arg.replace('\\', '/'), 'stream')
    return Stream(ix.read(e), arg)


def write_wav(path, channels, rate):
    """channels = list of int16 lists -> 16-bit PCM WAVE, interleaved."""
    n = len(channels[0])
    nch = len(channels)
    frames = bytearray()
    pack = struct.Struct('<%dh' % nch).pack
    if nch == 1:
        frames = struct.pack('<%dh' % n, *channels[0])
    else:
        for i in range(n):
            frames += pack(*(ch[i] for ch in channels))
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(frames)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 1, nch, rate, rate * 2 * nch, 2 * nch, 16))
        f.write(b'data' + struct.pack('<I', len(frames)))
        f.write(frames)


def rms_windows(channels, rate, window=5.0):
    """[(start s, rms)] over all channels."""
    n = len(channels[0])
    step = max(1, int(rate * window))
    out = []
    for i in range(0, n, step):
        acc = cnt = 0
        for ch in channels:
            seg = ch[i:i + step]
            acc += sum(x * x for x in seg)
            cnt += len(seg)
        out.append((i / rate, (acc / cnt) ** 0.5 if cnt else 0.0))
    return out


def info(s):
    print('%s: chunks %s' % (s.name, s.chunks))
    print('  tag 0x%04x %s, %d ch, %d Hz, %d bits, block %d, cbSize %d, extra %s' % (
        s.tag, TAG_NAMES.get(s.tag, '?'), s.channels, s.rate, s.bits, s.block, s.cb, s.extra.hex()))
    print('  data %d bytes, %d blocks (rem %d), %d samples, %.2f s' % (
        len(s.data), len(s.data) // s.block if s.block else 0, len(s.data) % s.block if s.block else 0, s.samples, s.seconds))


def _work():
    import kl_port_check
    w = os.path.join(kl_port_check.workdir(), 'pd2', 'audio')
    os.makedirs(w, exist_ok=True)
    return w


def survey():
    """fmt header of every stream entry (first 512 bytes of each blob, read in crate offset order).
    Row = [path, raw size, tag, channels, rate, bits, block align, cbSize, extra hex, data bytes, crate]."""
    import zlib
    import collections
    import pd2_crate
    ix = pd2_crate.Index(quiet=True)
    sh = pd2_crate.hash64('stream')
    byfile = collections.defaultdict(list)
    for e in ix.entries:
        if e.ext == sh:
            byfile[e.crate].append(e)
    rows, tab, bad = [], collections.Counter(), collections.Counter()
    for crate, lst in byfile.items():
        lst.sort(key=lambda e: e.offset)
        with open(os.path.join(ix.assets, crate), 'rb') as f:
            for e in lst:
                if e.raw == 0:
                    bad['empty'] += 1
                    continue
                f.seek(e.offset)
                d = f.read(min(e.stored or e.raw, 512))
                if e.stored:
                    d = zlib.decompressobj().decompress(d, 128)
                if d[:4] != b'RIFF' or d[8:12] != b'WAVE':
                    bad['not RIFF'] += 1
                    continue
                p, fmt, datasz = 12, None, None
                while p + 8 <= len(d):
                    cid, csz = d[p:p + 4], struct.unpack_from('<I', d, p + 4)[0]
                    if cid == b'fmt ':
                        fmt = d[p + 8:p + 8 + min(csz, 72)]
                    if cid == b'data':
                        datasz = csz
                        break
                    p += 8 + csz + (csz & 1)
                if fmt is None:
                    bad['no fmt'] += 1
                    continue
                tag, ch, rate, _, ba, bits = struct.unpack_from('<HHIIHH', fmt)
                cb = struct.unpack_from('<H', fmt, 16)[0] if len(fmt) >= 18 else 0
                extra = fmt[18:18 + cb].hex()
                tab[(tag, ch, rate, bits, ba, cb)] += 1
                rows.append([ix.path_name(e.path), e.raw, tag, ch, rate, bits, ba, cb, extra, datasz, crate])
    w = _work()
    with open(os.path.join(w, 'stream_headers.json'), 'w') as f:
        json.dump(rows, f)
    print('%d streams, %.2f GB raw, faults %s -> %s' % (len(rows), sum(r[1] for r in rows) / 1e9, dict(bad), os.path.join(w, 'stream_headers.json')))
    print('   tag  ch   rate bits block cb : count')
    for k, v in tab.most_common():
        print('0x%04x %3d %6d %4d %5d %2d : %d' % (k + (v,)))
    return rows


def _fnv32(s):
    """Wwise's name hash (FNV-1 32 bit of the lower-case name): switch / state values, event ids."""
    h = 2166136261
    for b in s.lower().encode():
        h = (h * 16777619) & 0xffffffff
        h ^= b
    return h


def _strings_table(data):
    """A Diesel .strings file: u64 0, u64 n, u64 n, u64 0x38, 16 bytes, then n x 32 {u64 key idstring,
    u64 0, u64 value offset, u32 ?, u32 0}; UTF-8 NUL-terminated values from 0x38 + 32 n to the end
    (strings/menu.strings: n = 13,214, first value at 422,904 = exactly the table's end)."""
    n = struct.unpack_from('<Q', data, 8)[0]
    out = {}
    for i in range(n):
        k, _, off = struct.unpack_from('<QQQ', data, 0x38 + 32 * i)
        out[k] = off
    return out


def banks():
    """soundbanks/music.bnk (Wwise 145 = 2021.1): HIRC 2,345 objects {3: 193, 4: 97, 10 segment: 790,
    11 track: 790, 12 switch: 9, 13 playlist: 464, 14: 2}. Four of the nine music switch containers hold
    a decision tree keyed by the FNV-1 hash of the track names of tweakdata.lua's track_list ('track_01'
    .. 'track_81', *_lcv, track_47_gen, track_pth_01..09); the u32 four dwords after the key is the
    playlist node. From there: every u32 of a node that is the id of a playlist / segment / track object
    is a child (a brute-force reference scan, so the HIRC record layouts need not be known), a track's
    u32s that are stream ids of the index are its sources. 90 tracks resolve to 6-10 streams each (652 of
    the 781 soundbanks/streamed/music/ streams; the four switch containers are the heist / stealth /
    stress / hit sets of tweakdata's music events, ASSUMPTION). Which stream of a track is the setup /
    control / anticipation / assault layer is NOT read (it sits in the segments' structure)."""
    import re as _re
    import pd2_crate
    ix = pd2_crate.Index(quiet=True)
    w = _work()
    hp = os.path.join(w, 'stream_headers.json')
    rows = json.load(open(hp)) if os.path.exists(hp) else survey()
    streams = {int(r[0].rsplit('/', 1)[1]): r for r in rows if r[0].rsplit('/', 1)[1].isdigit()}
    d = ix.read(ix.get('soundbanks/music', 'bnk'))
    o, hirc = 0, None
    while o + 8 <= len(d):
        cid, sz = d[o:o + 4], struct.unpack_from('<I', d, o + 4)[0]
        if cid == b'HIRC':
            hirc = o + 8
        o += 8 + sz
    objs = {}
    n = struct.unpack_from('<I', d, hirc)[0]
    q = hirc + 4
    for i in range(n):
        t, s, oid = d[q], struct.unpack_from('<I', d, q + 1)[0], struct.unpack_from('<I', d, q + 5)[0]
        objs[oid] = (t, d[q + 9:q + 5 + s])
        q += 5 + s
    music_ids = {k for k, (t, b) in objs.items() if t in (10, 11, 13)}

    def u32s(b):
        return [struct.unpack_from('<I', b, i)[0] for i in range(0, len(b) - 3)]
    refs, srcs = {}, {}
    for oid, (t, b) in objs.items():
        vals = set(u32s(b))
        refs[oid] = (vals & music_ids) - {oid}
        srcs[oid] = vals & set(streams)
    lua = ix.read(ix.get('lib/tweak_data/tweakdata', 'lua'))
    names = sorted({m.decode() for m in _re.findall(rb'track_(?:\d\d|pth_\d\d)(?:_lcv|_gen)?', lua)})
    keys = {_fnv32(t): t for t in names}
    roots = {}
    for oid, (t, b) in objs.items():
        if t != 12:
            continue
        vals = u32s(b)
        for i, v in enumerate(vals):
            if v in keys and i + 4 < len(vals) and vals[i + 4] in music_ids:
                roots.setdefault(keys[v], set()).add(vals[i + 4])

    def walk(oid, seen, depth=0):
        if oid in seen or depth > 6:
            return
        seen.add(oid)
        for r in refs.get(oid, ()):
            walk(r, seen, depth + 1)
    result = {}
    for t, rs in roots.items():
        seen = set()
        for r in rs:
            walk(r, seen)
        result[t] = sorted(set().union(*(srcs[x] for x in seen)))
    json.dump(result, open(os.path.join(w, 'track_streams.json'), 'w'), indent=0)
    # names: menu_jukebox_<track> in strings/menu.strings (english = props 0); two are in strings/hud
    tabs = []
    for nm in ('strings/menu', 'strings/hud'):
        sd = ix.read(ix.get(nm, 'strings', 0))
        tabs.append((sd, _strings_table(sd)))
    tn = {}
    for t in result:
        tn[t] = None
        for sd, tab in tabs:
            off = tab.get(pd2_crate.hash64('menu_jukebox_' + t))
            if off is not None:
                tn[t] = sd[off:sd.index(b'\0', off)].decode('utf-8', 'replace')
                break
    json.dump(tn, open(os.path.join(w, 'track_names.json'), 'w'), indent=1)
    allref = set().union(*(set(v) for v in result.values()))
    print('%d track names in tweakdata.lua, %d resolved in music.bnk, %d named; %d distinct streams (%d in soundbanks/streamed/music/, %.1f MB)' % (
        len(names), len(result), sum(1 for v in tn.values() if v), len(allref),
        sum(1 for x in allref if '/music/' in streams[x][0]), sum(streams[x][1] for x in allref) / 1e6))
    for t in names:
        if t not in result:
            print('  not in music.bnk:', t)


def tracks_table(name=None):
    w = _work()
    tr = json.load(open(os.path.join(w, 'track_streams.json')))
    rows = {r[0].rsplit('/', 1)[1]: r for r in json.load(open(os.path.join(w, 'stream_headers.json')))}
    names = json.load(open(os.path.join(w, 'track_names.json')))
    for t in sorted(tr):
        nm = names.get(t) or '?'
        if name and name.lower() not in t and name.lower() not in nm.lower():
            continue
        ids = tr[t]
        sz = sum(rows[str(i)][1] for i in ids)
        secs = sum(rows[str(i)][9] / rows[str(i)][6] * 64 / rows[str(i)][4] for i in ids if rows[str(i)][2] == 0x8311)
        print('%-14s %-40s %3d streams %7.1f MB %7.1f s' % (t, nm, len(ids), sz / 1e6, secs))
        if name:
            for i in ids:
                r = rows[str(i)]
                dur = r[9] / r[6] * 64 / r[4] if r[2] == 0x8311 else 0
                print('     %10d  %2d ch %5d Hz %6.1f s %8.2f MB' % (i, r[3], r[4], dur, r[1] / 1e6))


def bank_clips(data):
    """{wem id: wem bytes} of the DIDX / DATA chunks of a Wwise .bnk (BKHD, DIDX = 12-byte {id, offset, size}
    entries, DATA = the wem files at those offsets; the other chunk, HIRC, is NOT parsed here)."""
    p, didx, blob = 0, b'', b''
    while p + 8 <= len(data):
        cid, sz = data[p:p + 4], struct.unpack_from('<I', data, p + 4)[0]
        body = data[p + 8:p + 8 + sz]
        if cid == b'DIDX':
            didx = body
        elif cid == b'DATA':
            blob = body
        p += 8 + sz
    out = {}
    for i in range(0, len(didx), 12):
        wid, off, size = struct.unpack_from('<III', didx, i)
        out[wid] = blob[off:off + size]
    return out


def bank(arg, outdir=None):
    """Print (and with outdir decode) the clips of a soundbank; -> {id: Stream}."""
    if os.path.isfile(arg):
        data = open(arg, 'rb').read()
    else:
        import pd2_crate
        ix = pd2_crate.Index(quiet=True)
        data = ix.read(ix.get('soundbanks/' + arg.replace('\\', '/').replace('soundbanks/', ''), 'bnk'))
    streams = {wid: Stream(w, str(wid)) for wid, w in bank_clips(data).items()}
    print('%d clips' % len(streams))
    for wid, s in sorted(streams.items()):
        print('  %10d  %-14s %d ch %5d Hz %6.3f s %7d bytes' % (wid, TAG_NAMES.get(s.tag, hex(s.tag)), s.channels, s.rate, s.seconds, len(s.data)))
        if outdir and s.tag == 0x8311:
            os.makedirs(outdir, exist_ok=True)
            write_wav(os.path.join(outdir, '%d.wav' % wid), s.decode(), s.rate)
    return streams


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    if cmd == 'info':
        info(load(argv[2]))
    elif cmd == 'wav':
        s = load(argv[2])
        info(s)
        ch = s.decode()
        write_wav(argv[3], ch, s.rate)
        rw = rms_windows(ch, s.rate, 10.0)
        print('  wrote %s: %d frames; RMS per 10 s: %s' % (argv[3], len(ch[0]), ' '.join('%.0f' % r for _, r in rw)))
    elif cmd == 'rms':
        s = load(argv[2])
        ch = s.decode()
        for t, r in rms_windows(ch, s.rate, float(argv[3]) if len(argv) > 3 else 5.0):
            print('%7.1f s  rms %6.0f' % (t, r))
    elif cmd == 'survey':
        survey()
    elif cmd == 'bank':
        bank(argv[2], argv[3] if len(argv) > 3 else None)
    elif cmd == 'banks':
        banks()
    elif cmd == 'tracks':
        tracks_table(argv[2] if len(argv) > 2 else None)
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
