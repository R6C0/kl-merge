#!/usr/bin/env python3
"""
kl_launcher_music.py - a short Dead Men music clip for the KL Merge launcher, decoded from the TESTER'S OWN
Dead Men install (PC_Def.str) at install / first-run time. Nothing of it ships: the package and the repo
hold no game audio; when the file cannot be read or no candidate clip decodes, the launcher plays silence.

    python kl_launcher_music.py extract --dm "<Dead Men folder>" --out <file.wav> [--clip NAME] [--seconds 90]
    python kl_launcher_music.py list    --dm "<Dead Men folder>" [TEXT]          clips whose name holds TEXT
    python kl_launcher_music.py extract --dm ... --out ... --list                 the same listing (Music/ only)

Exit codes: 0 = the .wav was written; 2 = no usable clip (PC_Def.str missing / unreadable, the clip is Vorbis and no decoder
(bin/kl_oggdec.exe, ffmpeg, kl_pyvorbis.py) is here, or an unknown codec, nothing of the candidate list is in the file) - the launcher then stays silent; 1 = usage.
Writes ONLY the one output file (a partial file is removed on failure).

Output: standard RIFF/WAVE, 16-bit PCM, the clip's own rate and channels, at most --seconds (default 90) with a
1 s fade-in and a 3 s fade-out (so the launcher's loop seam is quiet).

STREAM FILE ('IOISNDSTREAM' version 9; the spec with the evidence is tools/kl_str.py's docstring, MEASURED
on both games' files; this module re-implements the read so the shipped launcher needs no other repo file)
  0x00 'IOISNDSTREAM', 0x0c u32 9, 0x10 u64 build id
  Dead Men: 0x18 u32 index offset, 0x1c u32 clip count, 0x20 u32 0x100 (block alignment)
  Dog Days: 0x18 u64 index offset, 0x20 u32 clip count, 0x24 u32 0x100       (read too, not needed here)
  data blocks from 0x100, each on a 0x100 multiple; a block that starts with 'LIP ' carries 0x1000 bytes of
  lip-sync data first, the audio follows (kl_str.LIP; kl_audio.LIP_BLOCK)
  index record, 72 bytes: u64 id, u64 block offset, u64 audio size, u64 format offset, u32 format size,
  u32 name key, u64 name length, u64 name offset, u64 lip word, u64 layer (0 alone; 1..n = n-th clip of an
  interleaved set; the set's own entry holds n)
  format: u32 codec (2 PCM 16 bit, 3 IMA ADPCM, 4 Ogg Vorbis, 0x1a = the interleaved set itself), u32 samples,
  u32 channels, u32 rate, u32 bits, 8 junk bytes; PCM + u32 frame bytes; ADPCM + u32 block align (0x400),
  u32 samples per block (0x7f9); set + u32 number of clips
  INTERLEAVED PCM SET: sample frames in turn, one period = for each clip in layer order (rate / lowest rate)
  frames of its channels; two stereo 32 kHz music layers = L1 R1 L2 R2 (kl_str.py 'INTERLEAVED SETS', MEASURED
  on 5 sets). A clip's size is its own share of the block.

WHAT IS PROVEN / GUESSED
  - PCM and the 2-layer PCM sets of the Retomoto music: PROVEN layout (re/retomoto_audio.md 4.1: TokyoAction1 =
    TakyoAction_V3_44_Layer1_Loop + TakyoAction_Layer2_TAmbient_Loop, 2 x stereo 32 kHz, 105.6 s (index 'samples' / channels); the merged
    stream file carries those blocks and the game plays them).
  - IMA ADPCM: mono blocks decoded as kl_audio.ima_to_pcm does (the same tables); a STEREO ADPCM clip is refused
    (GUESS: its block layout was never looked at; no music clip is ADPCM in the notes).
  - Vorbis (codec 4): the record's bytes are a PLAIN Ogg Vorbis stream (found by 06 on MenuLoop_01: starts 'OggS', 259 pages,
    'vorbis' id header at 29). GUESS (from that one clip): every codec-4 record is a complete Ogg stream at block offset
    (behind a LIP block if any), length = the index 'audio size'. It is accepted only when every page has the 'OggS'
    capture pattern and a good Ogg page CRC and the pages end exactly at the record's end; anything else is refused.
    Decoded by tools/launcher/bin/kl_oggdec.exe (stb_vorbis, public domain, built by tools/launcher/oggdec/build.bat),
    else ffmpeg on the PATH, else kl_pyvorbis.py beside this file (pure Python, by 6b: MenuLoop_01 = ffmpeg's frames,
    max diff 1 LSB, ~7 s); with none of them the clip is skipped (exit 2 if it was the only one).
    Mono/stereo only. Trim + fade as for PCM. (Retomoto rappel clip and Retomoto_Ambient_V2_Loop are Vorbis too.)
  - The default candidate order (CANDIDATES) and the codec of the FA theme are GUESSES; the file decides at run time.
"""
import array, os, shutil, struct, subprocess, sys

MAGIC = b'IOISNDSTREAM'
HEAD, REC, ALIGN, LIP = 0x38, 72, 0x100, 0x1000
PCM, ADPCM, VORBIS, SET = 2, 3, 4, 0x1a
CODEC = {PCM: 'pcm', ADPCM: 'adpcm', VORBIS: 'vorbis', SET: 'set'}
STREAM_NAME = 'PC_Def.str'
DEFAULT_SECONDS = 90.0
FADE_IN, FADE_OUT = 1.0, 3.0
MAX_SECONDS = 600.0

# Tried in this order when --clip is not given; the first that is in the file AND decodes wins.
# Names as the Dead Men index spells them (re/campaign_fa_prison.md, re/retomoto_audio.md 4.1, re/bank_campaign.md).
CANDIDATES = (
    ('SFX/UserInterface/MenuLoop_01.wav',
     'Dead Men main menu loop, SFX/UserInterface, Vorbis; the index says 154 s but it decodes to 77.0 s (found by 06: codec 4, 32000 Hz stereo, a plain Ogg stream; the only long clip under SFX/UserInterface)'),
    ('Music/InHouse/FA_Slash/FA_SlashMixPrison.wav',
     "Dead Men's own Fragile Alliance theme (125.8 s, settings field 150 of every FA level). GUESS: its codec is not in the notes; a Vorbis clip is skipped"),
    ('Music/InHouse/Japan/M09_A/TakyoAction_Layer2_TAmbient_Loop.wav',
     'Retomoto Tower tension bed: layer 2 of the PCM set TokyoAction1 (PROVEN 2 x stereo 32 kHz PCM, 105.6 s)'),
    ('Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav',
     'bank break-in suspense bed: layer 1 of the 4-layer PCM set BO_Sus_LOOP (interleaved PCM, 72 s)'),
    ('Music/InHouse/Japan/M09_A/Rooftop_Layer2_TAmbient_Loop.wav',
     'Retomoto roof bed: layer 2 of the PCM set M09A_Rooftop (PCM set, 110.4 s)'),
)

u32 = lambda b, o: struct.unpack_from('<I', b, o)[0]


class NoClip(Exception):
    """Nothing usable: exit 2 (the launcher falls back to silence)."""


class Clip(object):
    __slots__ = ('id', 'offset', 'size', 'fmt_at', 'fmt', 'key', 'name', 'name_at', 'lip', 'layer',
                 'codec', 'samples', 'channels', 'rate', 'bits', 'block', 'spb', 'nclips')

    def __repr__(self):
        return '<%s %d Hz %d ch %.1f s layer %d @%#x+%#x %s>' % (CODEC.get(self.codec, self.codec), self.rate, self.channels,
                                                                 self.seconds(), self.layer, self.offset, self.size, self.name)

    def seconds(self):
        # The index 'samples' counts samples of ALL channels: MEASURED on Vorbis MenuLoop_01 (4928626 for a clip that ffmpeg
        # and kl_oggdec both decode to 2464313 frames = 77.0 s at 32 kHz stereo) and on stereo PCM (size = 2 * samples bytes
        # on Kane_Family_Theme, FA_SlashMixPrison, M13B_Kane_Drive_Loop, TakyoAction_V3: 102.3 / 125.8 / 96.0 / 105.6 s,
        # half the lengths re/ notes quoted before 11-09). So divide by channels for every codec.
        n = float(self.samples) / (self.channels or 1)
        return n / self.rate if self.rate else 0.0


class Stream(object):
    """The index of one stream file. clips: index order; blocks: {block offset: [clips]} (set entry last)."""

    def __init__(self, path):
        self.path = path
        self.f = f = open(path, 'rb')
        self.size = os.path.getsize(path)
        h = f.read(HEAD)
        if len(h) < HEAD or h[:12] != MAGIC or u32(h, 12) != 9:
            raise NoClip('%s: not an IOISNDSTREAM version 9 file' % path)
        self.build = struct.unpack_from('<Q', h, 0x10)[0]
        if u32(h, 0x1c) == 0 and u32(h, 0x24) == ALIGN:            # Dog Days layout (u64 index offset)
            self.game = 'dd'
            self.index, self.count = struct.unpack_from('<QI', h, 0x18)
        elif u32(h, 0x20) == ALIGN:                                 # Dead Men layout
            self.game = 'dm'
            self.index, self.count = struct.unpack_from('<2I', h, 0x18)
        else:
            raise NoClip('%s: header of neither game' % path)
        if self.index + REC * self.count != self.size:
            raise NoClip('%s: the index does not end the file (truncated or not a stream file)' % path)
        f.seek(self.index)
        raw = f.read(REC * self.count)
        recs = [struct.unpack_from('<4Q2I4Q', raw, REC * i) for i in range(self.count)]
        self.clips, self.blocks = [], {}
        if not recs:
            return
        lo = min(min(r[3] for r in recs), min(r[7] for r in recs))
        f.seek(lo)
        tab = f.read(self.index - lo)                              # formats and names stand together before the index

        def at(o, n):
            if lo <= o and o + n <= self.index:
                return tab[o - lo:o - lo + n]
            f.seek(o)
            return f.read(n)
        for r in recs:
            c = Clip()
            c.id, c.offset, c.size, c.fmt_at, fl, c.key, nl, c.name_at, c.lip, c.layer = r
            c.fmt = at(c.fmt_at, fl)
            c.name = at(c.name_at, nl).decode('latin1').rstrip('\0')
            if len(c.fmt) < 20:
                raise NoClip('%s: format record of %d bytes' % (c.name, len(c.fmt)))
            c.codec, c.samples, c.channels, c.rate, c.bits = struct.unpack_from('<5I', c.fmt)
            c.block = c.spb = c.nclips = 0
            if c.codec == ADPCM and len(c.fmt) >= 36:
                c.block, c.spb = struct.unpack_from('<2I', c.fmt, 28)
            if c.codec == SET and len(c.fmt) >= 32:
                c.nclips = u32(c.fmt, 28)
            self.clips.append(c)
            self.blocks.setdefault(c.offset, []).append(c)
        for l in self.blocks.values():
            l.sort(key=lambda c: (c.codec == SET, c.layer))

    def close(self):
        self.f.close()

    def find(self, name):
        """Clip by name: exact (case-insensitive, '.wav' optional), else the one clip whose name ends with it."""
        want = name.replace('\\', '/').lower()
        bare = want[:-4] if want.endswith('.wav') else want
        for c in self.clips:
            n = c.name.lower()
            if n == want or n == bare or n == bare + '.wav':
                return c
        hits = [c for c in self.clips if c.name.lower().endswith(bare) or c.name.lower().endswith(bare + '.wav')]
        return hits[0] if len(hits) == 1 else None

    def has_lip(self, off):
        self.f.seek(off)
        return self.f.read(4) == b'LIP '

    def block_audio(self, off, nbytes):
        """The first nbytes of audio of the block at off (behind its LIP block when it has one)."""
        start = off + (LIP if self.has_lip(off) else 0)
        self.f.seek(start)
        return self.f.read(nbytes)

    def layers(self, c):
        """The parts of c's block in layer order (c alone when it is not part of a set)."""
        parts = [x for x in self.blocks.get(c.offset, [c]) if x.codec != SET]
        return parts if len(parts) > 1 else [c]


# ------------------------------------------------------------------ decoding
_STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97,
         107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
         876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428,
         4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350,
         22385, 24623, 27086, 29794, 32767]
_IDX = [-1, -1, -1, -1, 2, 4, 6, 8]


def ima_mono_to_pcm(data, block, max_samples):
    """Mono IMA ADPCM in MS block layout (4-byte block head: i16 predictor, u8 step index, 0; then nibbles,
    low nibble first) -> array('h'). The same tables and arithmetic as tools/kl_audio.ima_to_pcm."""
    block = block or 1024
    out = array.array('h')
    step_t, idx_t = _STEP, _IDX
    for b in range(0, len(data) - 3, block):
        blk = data[b:b + block]
        pred, idx = struct.unpack_from('<hB', blk, 0)
        idx = min(idx, 88)
        out.append(pred)
        for byte in blk[4:]:
            for nib in (byte & 15, byte >> 4):
                step = step_t[idx]
                diff = step >> 3
                if nib & 4:
                    diff += step
                if nib & 2:
                    diff += step >> 1
                if nib & 1:
                    diff += step >> 2
                pred = pred - diff if nib & 8 else pred + diff
                pred = -32768 if pred < -32768 else 32767 if pred > 32767 else pred
                out.append(pred)
                idx += idx_t[nib & 7]
                idx = 0 if idx < 0 else 88 if idx > 88 else idx
        if len(out) >= max_samples:
            break
    del out[max_samples:]
    return out


def pcm_samples(data):
    """16-bit little-endian PCM bytes -> array('h') (host order)."""
    a = array.array('h')
    a.frombytes(data[:len(data) - len(data) % 2])
    if sys.byteorder != 'little':
        a.byteswap()
    return a


def deinterleave(data, layers, want, frames):
    """PCM bytes of an interleaved set block -> (array('h') of the wanted layer, frames taken).
    layers = [(channels, rate)] in layer order, want = index into it. One period = for each layer
    (rate / lowest rate) frames of its channels (kl_str.py, MEASURED)."""
    low = min(r for _, r in layers)
    counts = [ch * (r // low) for ch, r in layers]              # samples per layer per period
    period = sum(counts)
    start = sum(counts[:want])
    ch, rate = layers[want]
    per_period = counts[want]                                   # = ch * (rate // low) samples
    periods = min(len(data) // (2 * period), -(-frames // (rate // low)))
    all_s = pcm_samples(data[:2 * period * periods])
    if per_period == 1:
        return all_s[start::period], periods
    cols = [all_s[start + k::period] for k in range(per_period)]
    out = array.array('h', bytes(2 * per_period * periods))
    for k, col in enumerate(cols):
        out[k::per_period] = col
    return out, periods * (rate // low)


# ------------------------------------------------------------------ Ogg Vorbis (codec 4)
def _crc_table():
    t = []
    for i in range(256):
        r = i << 24
        for _ in range(8):
            r = ((r << 1) ^ 0x04c11db7) if r & 0x80000000 else (r << 1)
        t.append(r & 0xffffffff)
    return t


_CRC = _crc_table()


def ogg_crc(page):
    """Ogg page checksum (CRC-32, poly 0x04c11db7, not reflected, init 0) of `page` with its CRC field (bytes 22..25) zeroed."""
    r = 0
    for b in page[:22] + b'\0\0\0\0' + page[26:]:
        r = ((r << 8) & 0xffffffff) ^ _CRC[(r >> 24) ^ b]
    return r


def ogg_check(data):
    """-> number of pages when `data` is exactly a sequence of valid Ogg pages whose first packet is a Vorbis id header;
    raises NoClip otherwise (capture pattern, version, size, CRC of every page, no trailing bytes)."""
    pos, pages = 0, 0
    n = len(data)
    while pos < n:
        if n - pos < 27 or data[pos:pos + 4] != b'OggS' or data[pos + 4] != 0:
            raise NoClip('not an Ogg stream (no OggS page at byte %d)' % pos)
        nseg = data[pos + 26]
        hlen = 27 + nseg
        if pos + hlen > n:
            raise NoClip('Ogg page %d is cut off' % pages)
        plen = hlen + sum(bytearray(data[pos + 27:pos + hlen]))
        if pos + plen > n:
            raise NoClip('Ogg page %d is cut off' % pages)
        page = data[pos:pos + plen]
        if ogg_crc(page) != u32(page, 22):
            raise NoClip('Ogg page %d has a bad CRC' % pages)
        if pages == 0 and page[hlen:hlen + 7] != b'\x01vorbis':
            raise NoClip('Ogg stream is not Vorbis (no id header in the first page)')
        pos += plen
        pages += 1
    if pages == 0:
        raise NoClip('empty Ogg stream')
    return pages


def vorbis_decoders():
    """-> [(label, argv, via_stdin)] to try in order: the bundled kl_oggdec.exe, then ffmpeg on the PATH."""
    here = os.path.dirname(os.path.abspath(__file__))
    out = []
    names = [os.environ.get('KL_OGGDEC', '')] + [os.path.join(here, *p) for p in
             (('bin', 'kl_oggdec.exe'), ('launcher', 'bin', 'kl_oggdec.exe'), ('kl_oggdec.exe',))]
    if sys.platform == 'win32':                                   # the bundled one is a Windows exe
        for p in names:
            if p and os.path.isfile(p):
                out.append(('kl_oggdec', [p, '-'], 'wav'))
                break
    ff = shutil.which('ffmpeg')
    if ff:
        out.append(('ffmpeg', [ff, '-v', 'error', '-nostdin', '-i', 'pipe:0', '-f', 'wav', '-acodec', 'pcm_s16le', 'pipe:1'], 'wav'))
    return out


def parse_wav16(blob):
    """RIFF/WAVE 16-bit PCM bytes (data size may be 0 / 0xffffffff when streamed) -> (array('h'), channels, rate)."""
    if blob[:4] != b'RIFF' or blob[8:12] != b'WAVE':
        raise NoClip('decoder output is not a WAV')
    pos, ch, rate, bits = 12, 0, 0, 0
    while pos + 8 <= len(blob):
        tag, size = blob[pos:pos + 4], u32(blob, pos + 4)
        if tag == b'fmt ':
            fmt, ch, rate = struct.unpack_from('<HHI', blob, pos + 8)
            bits = struct.unpack_from('<H', blob, pos + 22)[0]
            if fmt != 1 or bits != 16:
                raise NoClip('decoder output is not 16-bit PCM')
        elif tag == b'data':
            body = blob[pos + 8:] if size in (0, 0xffffffff) or pos + 8 + size > len(blob) else blob[pos + 8:pos + 8 + size]
            if not ch or not rate:
                raise NoClip('decoder output has no fmt chunk')
            return pcm_samples(body[:len(body) - len(body) % (2 * ch)]), ch, rate
        pos += 8 + size + (size & 1)
    raise NoClip('decoder output has no data chunk')


def decode_vorbis(c, data, seconds):
    """Ogg Vorbis record -> (array('h'), channels, rate), at most `seconds`. Raises NoClip."""
    ogg_check(data)
    decs = vorbis_decoders()
    pyv = py_vorbis()
    if not decs and not pyv:
        raise NoClip('%s: Ogg Vorbis, but neither tools/launcher/bin/kl_oggdec.exe nor ffmpeg nor kl_pyvorbis.py is here to decode it' % c.name)
    errs = []
    for label, argv, _ in decs:
        try:
            r = subprocess.run(argv, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
            if r.returncode != 0 or not r.stdout:
                errs.append('%s exit %s %s' % (label, r.returncode, r.stderr[:120].decode('latin1').strip()))
                continue
            s, ch, rate = parse_wav16(r.stdout)
        except (OSError, subprocess.SubprocessError, NoClip) as e:
            errs.append('%s: %s' % (label, e))
            continue
        if ch not in (1, 2):
            errs.append('%s: %d channels' % (label, ch))
            continue
        del s[ch * int(min(seconds, MAX_SECONDS) * rate):]
        return s, ch, rate
    if pyv:                                                        # last: slow (~7 s for 77 s) but needs no exe
        try:
            s, ch, rate = pyv.vorbis_decode(bytes(data), int(min(seconds, MAX_SECONDS) * c.rate))
        except Exception as e:                                     # VorbisError, or a bug on a stream it never saw
            errs.append('kl_pyvorbis: %s' % e)
        else:
            if ch in (1, 2) and len(s):
                del s[ch * int(min(seconds, MAX_SECONDS) * rate):]
                return s, ch, rate
            errs.append('kl_pyvorbis: %d channels, %d samples' % (ch, len(s)))
    raise NoClip('%s: no decoder could decode the Ogg Vorbis stream (%s)' % (c.name, '; '.join(errs)))


def py_vorbis():
    """-> the kl_pyvorbis module beside this file, or None (not shipped / KL_NO_PYVORBIS=1 in the self-test)."""
    if os.environ.get('KL_NO_PYVORBIS') == '1':
        return None
    here = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isfile(os.path.join(here, 'kl_pyvorbis.py')):
        return None
    if here not in sys.path:
        sys.path.insert(0, here)
    try:
        import kl_pyvorbis
    except ImportError:
        return None
    return kl_pyvorbis


def decode(st, c, seconds):
    """-> (array('h') interleaved samples, channels, rate) of at most `seconds` of clip c."""
    frames = int(min(seconds, MAX_SECONDS) * c.rate)
    if c.codec == SET:
        parts = st.layers(c)
        if len(parts) < 2:
            raise NoClip('%s: a set entry without layers' % c.name)
        c = parts[0]                                            # the driving layer (layer 1) of the set
        frames = int(min(seconds, MAX_SECONDS) * c.rate)
    if c.codec == PCM:
        if c.bits != 16:
            raise NoClip('%s: PCM with %d bits' % (c.name, c.bits))
        parts = st.layers(c)
        if len(parts) == 1:
            nbytes = min(c.size, 2 * c.channels * frames)
            s = pcm_samples(st.block_audio(c.offset, nbytes))
            del s[c.channels * frames:]
            return s, c.channels, c.rate
        layers = [(p.channels, p.rate) for p in parts]
        if any(p.codec != PCM or p.bits != 16 for p in parts):
            raise NoClip('%s: a set whose layers are not all 16-bit PCM' % c.name)
        if any(r % min(x[1] for x in layers) for _, r in layers):
            raise NoClip('%s: set rates are not multiples of the lowest' % c.name)
        want = parts.index(c)
        low = min(r for _, r in layers)
        period_bytes = 2 * sum(ch * (r // low) for ch, r in layers)
        total = sum(p.size for p in parts)
        nbytes = min(total, period_bytes * (-(-frames // (c.rate // low))))
        s, _ = deinterleave(st.block_audio(c.offset, nbytes), layers, want, frames)
        del s[c.channels * frames:]
        return s, c.channels, c.rate
    if c.codec == ADPCM:
        if c.channels != 1:
            raise NoClip('%s: %d-channel IMA ADPCM (GUESS: block layout unknown, only mono is decoded)' % (c.name, c.channels))
        if st.layers(c) != [c]:
            raise NoClip('%s: ADPCM inside an interleaved set' % c.name)
        block = c.block or 1024
        spb = c.spb or ((block - 4) * 2 + 1)
        nblocks = -(-frames // spb)
        data = st.block_audio(c.offset, min(c.size, block * nblocks))
        s = ima_mono_to_pcm(data, block, min(frames, c.samples))
        return s, 1, c.rate
    if c.codec == VORBIS:
        if st.layers(c) != [c]:
            raise NoClip('%s: Vorbis inside an interleaved set' % c.name)
        return decode_vorbis(c, st.block_audio(c.offset, c.size), seconds)
    raise NoClip('%s: codec %d not understood' % (c.name, c.codec))


def fade(s, channels, rate, fade_in=FADE_IN, fade_out=FADE_OUT):
    """Linear fade-in / fade-out in place on interleaved int16 samples."""
    frames = len(s) // channels
    n_in = min(int(fade_in * rate), frames // 2)
    n_out = min(int(fade_out * rate), frames - n_in)
    for i in range(n_in):
        g = float(i) / n_in
        for k in range(channels):
            j = i * channels + k
            s[j] = int(s[j] * g)
    for i in range(n_out):
        g = float(n_out - 1 - i) / n_out
        base = (frames - n_out + i) * channels
        for k in range(channels):
            s[base + k] = int(s[base + k] * g)
    return s


def wav_bytes(s, channels, rate):
    """array('h') interleaved -> RIFF/WAVE 16-bit PCM bytes."""
    if sys.byteorder != 'little':
        s = array.array('h', s)
        s.byteswap()
    data = s.tobytes()
    hdr = struct.pack('<4sI4s4sIHHIIHH4sI', b'RIFF', 36 + len(data), b'WAVE', b'fmt ', 16, 1, channels, rate,
                      rate * channels * 2, channels * 2, 16, b'data', len(data))
    return hdr + data


# ------------------------------------------------------------------ the commands
def stream_path(dm):
    if dm.lower().endswith('.str') and os.path.isfile(dm):
        return dm
    return os.path.join(dm, STREAM_NAME)


def open_stream(dm, log):
    p = stream_path(dm)
    if not os.path.isfile(p):
        raise NoClip('no %s in %s' % (STREAM_NAME, dm))
    st = Stream(p)
    log('%s: %s layout, %d clips, build %08x' % (p, st.game, st.count, st.build))
    return st


def candidates(st, clip, log):
    """-> [(Clip, reason)] to try in order: the one named with --clip, or every built-in candidate the file has."""
    if clip:
        c = st.find(clip)
        if c is None:
            raise NoClip('clip %r is not in the file (list with: list --dm ... %s)' % (clip, clip.split('/')[-1][:12]))
        return [(c, 'named with --clip')]
    cands = []
    for name, why in CANDIDATES:
        c = st.find(name)
        if c is not None:
            cands.append((c, why))
        else:
            log('  candidate not in the file: %s' % name)
    if not cands:
        raise NoClip('none of the %d candidate clips is in the file' % len(CANDIDATES))
    return cands


def extract(dm, out, clip=None, seconds=DEFAULT_SECONDS, log=print):
    """Decode the clip (or the first decodable candidate) to `out`. -> the Clip; raises NoClip."""
    st = open_stream(dm, log)
    try:
        cands = candidates(st, clip, log)
        last = None
        for c, why in cands:
            try:
                log('  trying %r (%s)' % (c, why))
                s, ch, rate = decode(st, c, seconds)
            except NoClip as e:
                last = e
                log('  skipped: %s' % e)
                continue
            if len(s) < ch * rate:                                 # under a second of audio: not worth playing
                last = NoClip('%s: only %d samples decoded' % (c.name, len(s)))
                log('  skipped: %s' % last)
                continue
            fade(s, ch, rate)
            blob = wav_bytes(s, ch, rate)
            d = os.path.dirname(os.path.abspath(out))
            if d and not os.path.isdir(d):
                os.makedirs(d)
            try:
                with open(out, 'wb') as f:
                    f.write(blob)
            except Exception:
                try:
                    os.remove(out)
                except OSError:
                    pass
                raise
            log('wrote %s: %s, %d Hz, %d ch, %.1f s, %d bytes' % (out, c.name, rate, ch, float(len(s)) / (ch * rate), len(blob)))
            return c
        raise last or NoClip('nothing decoded')
    finally:
        st.close()


def listing(st, text='', log=print):
    text = (text or '').lower()
    n = 0
    for c in st.clips:
        if text and text not in c.name.lower():
            continue
        log('%-6s %6.1fs %5d Hz %d ch layer %d  %s' % (CODEC.get(c.codec, c.codec), c.seconds(), c.rate, c.channels, c.layer, c.name))
        n += 1
    log('%d clips' % n)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    e = sub.add_parser('extract', help='decode one clip to a 16-bit PCM .wav')
    e.add_argument('--dm', required=True, help="the Dead Men folder (holds PC_Def.str), or the .str file itself")
    e.add_argument('--out', required=True, help='the .wav to write')
    e.add_argument('--clip', default='', help='clip name (default: the first of the built-in candidates that decodes)')
    e.add_argument('--seconds', type=float, default=DEFAULT_SECONDS, help='trim to at most this many seconds (default %g)' % DEFAULT_SECONDS)
    e.add_argument('--list', action='store_true', help='list the Music/ clips of the file instead of extracting')
    l = sub.add_parser('list', help='list the clips of the file')
    l.add_argument('--dm', required=True)
    l.add_argument('text', nargs='?', default='')
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 1
    try:
        if a.cmd == 'list' or a.list:
            st = open_stream(a.dm, print)
            try:
                listing(st, a.text if a.cmd == 'list' else 'music/')
            finally:
                st.close()
            return 0
        if a.seconds <= 0 or a.seconds > MAX_SECONDS:
            print('--seconds must be in 0 < s <= %g' % MAX_SECONDS)
            return 1
        extract(a.dm, a.out, a.clip or None, a.seconds, print)
        return 0
    except NoClip as e:
        print('NO MUSIC: %s' % e)
        return 2
    except (IOError, OSError) as e:
        print('NO MUSIC: %s' % e)
        return 2


if __name__ == '__main__':
    sys.exit(main())
