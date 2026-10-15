#!/usr/bin/env python3
"""
kl_gunsnd.py - list, extract, process and replace the in-memory gun sounds of a Kane & Lynch 2: Dog Days level bank.

A level's sound = <L>_Main.SND (in the zip) + <L>_Main.WHD (wave headers) + <L>_Main.WAV (wave data), both beside
the zip (re/audio.md sections 1-3). Gun shots are NOT in PC_Def.str: they are in-memory clips of every level bank,
named 'SFX/Weapons_KL2_Final/<gun>/<gun>_Shot_NN.wav', 16-bit-equivalent Microsoft IMA ADPCM (format 0x11, 4 bits,
block align 0x400, 0x7f9 samples per block), mono, mostly 44.1 kHz. Each of our KLExpansion/Maps/<id> maps carries
its own copy of the slot's .WHD/.WAV, so a change has to be written into every bank the guns should change in.

    python kl_gunsnd.py list    <bank.WHD> [regex]           # default regex: weapons (shots, distant shots, tails)
    python kl_gunsnd.py extract <bank.WHD> <outdir> [regex]  # decoded 16-bit PCM .wav per record
    python kl_gunsnd.py refs    <bank.SND> <bank.WHD> [regex] # which .SND wave/sound objects use each record
    python kl_gunsnd.py replace <bank.WHD> <outdir> <map.txt> [--snd <bank.SND>]
          map.txt lines: <wave name as in the .WHD> = <path to a .wav (PCM 16 or float, any rate; resampled to the
          record's rate, mixed to the record's channels)>
          Writes <outdir>/<bank>.WHD + .WAV (+ .SND if given). Never touches the input files.
    python kl_gunsnd.py heat    <bank.WHD> <outdir> <regex> [--style street|indoor] [--snd <bank.SND>]
          Prototype: process the bank's OWN clips (low shelf, saturation, synthetic echo tail) and replace them.
          --tail <s>: length of the synthetic echo (default street 2.6 s, indoor 1.0 s)
          --fit: cut each processed clip back to its stock length (no .WAV growth, every record stays in place)
    python kl_gunsnd.py groups   <bank.SND>                   # sound groups and their volume floats
    python kl_gunsnd.py groupvol <bank.SND> <out.SND> sfx_weapons_shot_npc=0.6 [...]   # in-place group volume
    python kl_gunsnd.py selftest <bank.WHD>                   # codec round trip + bank rebuild checks

How a replacement is stored (keeps every offset that anything points at):
  * The .WHD keeps its size and layout. Only the replaced record's fields change: pcm bytes (+0x10), data bytes
    (+0x14), data offset (+0x1c), samples (+0x24). The .SND points at the record (offset - 4, re/audio.md 2.3),
    not at the data, so the .SND's pointers stay valid.
  * New data that fits in the old data's bytes is written in place (rest of the old span zeroed); longer data is
    APPENDED to the .WAV (16-aligned) and the record's offset moved there; the .WAV header's size dword (+4) is
    updated. Nothing else in the .WAV moves.
  * The .SND wave object carries the clip length in seconds (+0x18, f32). With --snd it is rewritten for every wave
    object that points at a changed record (same size file, in place). Whether the engine uses that value (voice
    stealing, loop end?) is NOT established; keep it consistent anyway. The .SND then has to go back into the zip
    (the repo's zip tools; this script does not repack the 200 MB archive).

Parsing of the .WHD follows re/audio.md 9.3 (whd.py, track-voice) and luvsic's third_party/anp/tools/whdconv.py
(record layout); the IMA ADPCM decoder follows third_party/anp/loader/adpcm.h (luvsic). The encoder is the
standard IMA step quantiser, written here.
"""
import os, re, struct, sys, math
import numpy as np

DEFAULT_RX = r'weapons'
NUL = b'\0'
DD_F = 'name fmt rate bits pcm size ch off offhi samples block spb lip x34 x38 x3c x40'.split()
REC = 0x44
F = {k: i for i, k in enumerate(DD_F)}

# ------------------------------------------------------------------------------------------------------------- .WHD
def parse_whd(b):
    """-> list of ('name', off, bytes) / ('rec', off, list of 17 dwords), as re/audio.md 9.3 (whd.py)"""
    T, size, v3, v4 = struct.unpack_from('<4I', b, 0)
    assert size == len(b) and (v3, v4) == (3, 4), 'not a WHD'
    out = []; names = {0}; p = 0x10; end = T if T else len(b)
    while p < end:
        v = struct.unpack_from('<I', b, p)[0]
        if v in names and (v or len(names) == 1) and p + REC <= end and 0 < (struct.unpack_from('<I', b, p + 4)[0] & 0xffff) <= 0x1000:
            out.append(('rec', p, list(struct.unpack_from('<17I', b, p)))); p += REC
        elif v == 0:
            p += 4
        elif p % 16 == 0 and 32 <= b[p] < 127:
            e = b.index(NUL, p); out.append(('name', p, b[p:e])); names.add(p); p = e + 1; p += -p % 4
        else:
            raise ValueError('%#x: neither a name nor a record (%08x)' % (p, v))
    return out


class Wave:
    __slots__ = ('rec_off', 'name', 'f')
    def __init__(self, rec_off, name, f): self.rec_off, self.name, self.f = rec_off, name, f
    def get(self, k): return self.f[F[k]]
    @property
    def codec(self): return self.f[1] & 0xffff
    @property
    def streamed(self): return bool(self.f[1] & 0x00800000)
    @property
    def seconds(self): return self.get('samples') / max(1, self.get('ch')) / max(1, self.get('rate')) if self.codec == 1 else \
        self.get('samples') / max(1, self.get('rate'))


def waves(whd):
    names = {}; out = []
    for kind, off, v in parse_whd(whd):
        if kind == 'name': names[off] = v.decode('latin1')
        else: out.append(Wave(off, names.get(v[0], '?'), v))
    return out


# --------------------------------------------------------------------------------------------- IMA ADPCM (MS 0x11)
STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
        130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963, 1060,
        1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
        7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]
IDX = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]


def _nib(st, n):
    pred, idx = st
    step = STEP[idx]; diff = step >> 3
    if n & 1: diff += step >> 2
    if n & 2: diff += step >> 1
    if n & 4: diff += step
    pred = pred - diff if n & 8 else pred + diff
    pred = 32767 if pred > 32767 else (-32768 if pred < -32768 else pred)
    idx += IDX[n]; idx = 0 if idx < 0 else (88 if idx > 88 else idx)
    st[0], st[1] = pred, idx
    return pred


def ima_decode(data, ch, block, spb, nsamples):
    """MS IMA ADPCM -> int16 array [frames, ch] (third_party/anp/loader/adpcm.h, luvsic)"""
    out = []
    for bo in range(0, len(data), block):
        blk = data[bo:bo + block]
        if len(blk) < 4 * ch: break
        st = []; fr = np.zeros((spb, ch), np.int16)
        for c in range(ch):
            p = struct.unpack_from('<h', blk, 4 * c)[0]; i = min(blk[4 * c + 2], 88)
            st.append([p, i]); fr[0, c] = p
        s = 1; p = 4 * ch
        while p + 4 * ch <= len(blk) and s < spb:
            for c in range(ch):
                for k in range(4):
                    b = blk[p + 4 * c + k]; s0 = s + 2 * k
                    v0 = _nib(st[c], b & 15); v1 = _nib(st[c], b >> 4)
                    if s0 < spb: fr[s0, c] = v0
                    if s0 + 1 < spb: fr[s0 + 1, c] = v1
            p += 4 * ch; s += 8
        out.append(fr[:s])
    pcm = np.concatenate(out) if out else np.zeros((0, ch), np.int16)
    return pcm[:nsamples]


def _enc_sample(st, x):
    """quantise one sample, update state like the decoder, return nibble"""
    pred, idx = st
    step = STEP[idx]; d = x - pred; n = 0
    if d < 0: n = 8; d = -d
    if d >= step: n |= 4; d -= step
    if d >= step >> 1: n |= 2; d -= step >> 1
    if d >= step >> 2: n |= 1
    _nib(st, n)
    return n


def ima_encode(pcm, block=0x400):
    """int16 [frames, ch] -> MS IMA ADPCM bytes, samples per block = (block - 4ch) * 2 / ch + 1"""
    frames, ch = pcm.shape
    spb = (block - 4 * ch) * 2 // ch + 1
    out = bytearray(); st = [[0, 0] for _ in range(ch)]
    x = pcm.astype(np.int32).tolist()
    for f0 in range(0, frames, spb):
        seg = x[f0:f0 + spb]
        blk = bytearray()
        for c in range(ch):
            p = seg[0][c]
            # keep the step index from the previous block (better than restarting at 0)
            st[c][0] = p
            blk += struct.pack('<hBB', p, st[c][1], 0)
        # last block: the stock banks store whole blocks (data bytes = n x block align, e.g. 25,347 samples = 13 x
        # 0x400 = 13,312 bytes), so pad with the last sample to a full block; the record's sample count stops playback
        n = len(seg) - 1; groups = (spb - 1) // 8
        body = seg[1:] + [seg[-1]] * (groups * 8 - n)
        for g in range(groups):
            for c in range(ch):
                nib = [_enc_sample(st[c], body[g * 8 + k][c]) for k in range(8)]
                blk += bytes(nib[2 * k] | (nib[2 * k + 1] << 4) for k in range(4))
        out += blk
    return bytes(out), spb


# ------------------------------------------------------------------------------------------------------------- WAV io
def read_wav(path):
    """-> float64 [frames, ch] in -1..1, rate. PCM 8/16/24/32 or IEEE float."""
    b = open(path, 'rb').read()
    assert b[:4] == b'RIFF' and b[8:12] == b'WAVE', path
    p = 12; fmt = None; data = None
    while p + 8 <= len(b):
        cid, sz = b[p:p + 4], struct.unpack_from('<I', b, p + 4)[0]
        if cid == b'fmt ': fmt = struct.unpack_from('<HHIIHH', b, p + 8)
        elif cid == b'data': data = b[p + 8:p + 8 + sz]
        p += 8 + sz + (sz & 1)
    tag, ch, rate, _, _, bits = fmt
    if tag == 0xfffe: tag = 3 if bits == 32 and False else 1
    if tag == 3: a = np.frombuffer(data, '<f4' if bits == 32 else '<f8').astype(np.float64)
    elif bits == 16: a = np.frombuffer(data, '<i2') / 32768.0
    elif bits == 8: a = (np.frombuffer(data, 'u1').astype(np.float64) - 128) / 128.0
    elif bits == 24:
        u = np.frombuffer(data, 'u1').reshape(-1, 3).astype(np.int32)
        a = ((u[:, 0] | (u[:, 1] << 8) | (u[:, 2] << 16)) << 8 >> 8) / 8388608.0
    elif bits == 32: a = np.frombuffer(data, '<i4') / 2147483648.0
    else: raise ValueError('wav bits %d' % bits)
    return a.reshape(-1, ch), rate


def write_wav(path, pcm16, rate):
    ch = pcm16.shape[1]; d = pcm16.astype('<i2').tobytes()
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(d)) + b'WAVEfmt ' + struct.pack('<IHHIIHH', 16, 1, ch, rate, rate * ch * 2, ch * 2, 16))
        f.write(b'data' + struct.pack('<I', len(d)) + d)


def resample(x, src, dst):
    if src == dst: return x
    n = int(round(len(x) * dst / src)); t = np.arange(n) * (src / dst)
    return np.stack([np.interp(t, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], 1)


def to_i16(x):
    return np.clip(np.round(x * 32767.0), -32768, 32767).astype(np.int16)


# ------------------------------------------------------------------------------------------------------- bank access
def decode_wave(wav, w):
    """-> float [frames, ch] of an in-memory record"""
    off, size, ch = w.get('off'), w.get('size'), w.get('ch')
    data = wav[off:off + size]
    if w.codec == 0x11:
        return ima_decode(data, ch, w.get('block'), w.get('spb'), w.get('samples')) / 32768.0
    if w.codec == 1 and w.get('bits') == 16:
        return (np.frombuffer(data, '<i2').reshape(-1, ch)) / 32768.0
    raise ValueError('%s: codec %#x bits %d not handled' % (w.name, w.codec, w.get('bits')))


def encode_for(w, x, rate):
    """float [frames, ch] at rate -> (data bytes, samples field, pcm bytes field) in the record's own format"""
    x = resample(x, rate, w.get('rate'))
    ch = w.get('ch')
    if x.shape[1] != ch: x = np.repeat(x.mean(1, keepdims=True), ch, 1)
    pcm = to_i16(x)
    if w.codec == 0x11:
        data, spb = ima_encode(pcm, w.get('block'))
        assert spb == w.get('spb'), (spb, w.get('spb'))
        return data, len(pcm), len(pcm) * ch * 2
    if w.codec == 1:
        return pcm.tobytes(), len(pcm) * ch, len(pcm) * ch * 2   # PCM records count samples x channels (whdconv)
    raise ValueError('codec %#x' % w.codec)


def snd_wave_objects(snd):
    """-> {whd record offset: [ (wave object offset, file name) ]} from the .SND type-4 table (re/audio.md 2.1-2.3)"""
    T = struct.unpack_from('<I', snd, 0)[0]
    H = T + 0x30                                       # Dog Days: 10 stream names
    cnt = struct.unpack_from('<I', snd, H + 0x10 + 4 * 3)[0]
    tab = struct.unpack_from('<I', snd, H + 0x74 + 4 * 3)[0]
    out = {}
    for i in range(cnt):
        o = struct.unpack_from('<I', snd, tab + 4 * i)[0]
        if o + 0x20 > len(snd): continue               # 0xfffffffe = the _LS bank's wave (re/audio.md 2.4)
        t, _, nm, fl, _, whdo, sec = struct.unpack_from('<IIIIIIf', snd, o)
        if t not in (0, 4): continue
        if fl & 0xffff in (0xa, 0xb): continue         # localized: dialogue, never a gun
        out.setdefault(whdo + 4, []).append((o, sec))
    return out


def snd_sounds(snd):
    """-> {wave object offset: [sound object name]} (type 1 table, +0x14 wave pointer)"""
    T = struct.unpack_from('<I', snd, 0)[0]; H = T + 0x30
    cnt = struct.unpack_from('<I', snd, H + 0x10)[0]; tab = struct.unpack_from('<I', snd, H + 0x74)[0]
    out = {}
    for i in range(cnt):
        o = struct.unpack_from('<I', snd, tab + 4 * i)[0]
        if o + 0x18 > len(snd): continue
        nm, = struct.unpack_from('<I', snd, o + 8); wv, = struct.unpack_from('<I', snd, o + 0x14)
        e = snd.index(NUL, nm); out.setdefault(wv, []).append(snd[nm:e].decode('latin1'))
    return out


def rebuild(whd, wav, repl, snd=None, log=print):
    """repl: {record offset: (data bytes, samples, pcm bytes, seconds)} -> new (whd, wav, snd)"""
    whd = bytearray(whd); wav = bytearray(wav); snd = bytearray(snd) if snd is not None else None
    ws = {w.rec_off: w for w in waves(bytes(whd))}
    so = snd_wave_objects(bytes(snd)) if snd is not None else {}
    for ro, (data, samples, pcmb, sec) in sorted(repl.items()):
        w = ws[ro]; old_off, old_size = w.get('off'), w.get('size')
        assert not w.streamed, w.name
        if len(data) <= old_size:
            wav[old_off:old_off + old_size] = data + bytes(old_size - len(data)); new_off = old_off; how = 'in place'
        else:
            wav += bytes(-len(wav) % 16); new_off = len(wav); wav += data; how = 'appended'
        f = list(w.f); f[F['off']] = new_off; f[F['offhi']] = 0; f[F['size']] = len(data)
        f[F['samples']] = samples; f[F['pcm']] = pcmb
        struct.pack_into('<17I', whd, ro, *f)
        n = 0
        for wo, _ in so.get(ro, []):
            struct.pack_into('<f', snd, wo + 0x18, sec); n += 1
        log('  %-70s %6d -> %6d bytes, %.3f s, %s%s' % (w.name[-70:], old_size, len(data), sec, how,
                                                         ', %d .SND wave object(s) +0x18' % n if snd is not None else ''))
    struct.pack_into('<I', wav, 4, len(wav))
    return bytes(whd), bytes(wav), (bytes(snd) if snd is not None else None)


# --------------------------------------------------------------------------------------- 'Heat' processing (numpy)
def _fft_filter(x, rate, gain_db_fn):
    """zero-phase EQ by a gain curve in the frequency domain (fine for one-shot clips)"""
    n = 1 << int(math.ceil(math.log2(len(x) * 2 + 1)))
    X = np.fft.rfft(x, n, axis=0); fr = np.fft.rfftfreq(n, 1 / rate)
    g = 10 ** (gain_db_fn(fr) / 20.0)
    return np.fft.irfft(X * g[:, None], n, axis=0)[:len(x)]


def _shelf(fr, f0, db, low=True):
    s = 1 / (1 + (fr / f0) ** 2) if low else 1 - 1 / (1 + (fr / f0) ** 2)
    return db * s


def _peak(fr, f0, db, q=1.0):
    return db * np.exp(-0.5 * (np.log2(np.maximum(fr, 1) / f0) * 2 * q) ** 2)


def synth_ir(rate, style, seed=7, tail=None):
    """Self-generated impulse response (no third-party audio): street = discrete slap echoes off building faces
    (40-400 ms, alternating L/R distance) + a long diffuse decaying noise tail low-passed (outdoor air absorbs highs);
    indoor = short dense early reflections + 0.9 s tail."""
    rng = np.random.default_rng(seed)
    if style == 'street':
        tail = tail or 2.6; L = int(rate * tail); ir = np.zeros(L)
        for t, a in ((0.045, .55), (0.11, .42), (0.19, .33), (0.28, .26), (0.41, .20), (0.62, .14), (0.9, .09)):
            i = int(t * rate)
            if i + 64 < L: ir[i:i + 64] += a * np.hanning(64) * rng.choice([-1, 1])
        t = np.arange(L) / rate
        ir += rng.standard_normal(L) * np.exp(-t / (0.21 * tail)) * np.clip((t - 0.03) / 0.08, 0, 1) * 0.22
        # darker with distance: progressive low-pass by blending a smoothed copy
        k = np.hanning(int(rate * 0.0012)); k /= k.sum(); ir = 0.35 * ir + 0.65 * np.convolve(ir, k, 'same')
    else:
        tail = tail or 1.0; L = int(rate * tail); t = np.arange(L) / rate; ir = np.zeros(L)
        for i in range(24):
            d = int(rng.uniform(0.004, 0.06) * rate); ir[d] += rng.uniform(-.4, .4)
        ir += rng.standard_normal(L) * np.exp(-t / (0.22 * tail)) * 0.18
    ir[0] = 0
    return ir


def heat(x, rate, style='street', tail_gain=0.55, low_db=5.0, drive=2.2, tail=None):
    """the game's own shot -> heavier, louder, with an echo tail. x float [frames, ch]."""
    # 1. EQ: +5 dB low shelf at 120 Hz (body), +3 dB at 2.5 kHz (crack), -2 dB at 450 Hz (box), cut <30 Hz
    y = _fft_filter(x, rate, lambda fr: _shelf(fr, 120, low_db) + _peak(fr, 2500, 3, 1) + _peak(fr, 450, -2, 1.2)
                    - 24 * (1 / (1 + (fr / 30) ** 4)))
    # 2. saturation: tanh drive, normalised so the peak lands near full scale (loud, 'raw')
    y = np.tanh(drive * y / max(1e-9, np.abs(y).max())) / math.tanh(drive)
    # 3. echo tail: convolve with a synthetic IR, high-cut the wet signal (distance), mix under the dry
    ir = synth_ir(rate, style, tail=tail)
    n = 1 << int(math.ceil(math.log2(len(y) + len(ir))))
    wet = np.fft.irfft(np.fft.rfft(y, n, axis=0) * np.fft.rfft(ir, n)[:, None], n, axis=0)[:len(y) + len(ir)]
    wet = _fft_filter(wet, rate, lambda fr: -18 * (1 - 1 / (1 + (fr / 3500) ** 2)))
    out = np.zeros_like(wet); out[:len(y)] = y
    out += tail_gain * wet / max(1e-9, np.abs(wet).max())
    # 4. trim the tail where it falls below -60 dB, fade the last 50 ms, peak at -0.5 dBFS
    env = np.abs(out).max(1); thr = env.max() * 1e-3
    last = int(np.nonzero(env > thr)[0][-1]) + 1; out = out[:last]
    fade = min(len(out), int(0.05 * rate)); out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    # soft limiter instead of a plain peak normalise: the dry + wet sum peaks above full scale at the onset, and a
    # linear rescale cost the attack ~4 dB (measured on HG_M9Beretta_Shot_01); tanh keeps the crack loud and dense
    out = np.tanh(1.6 * out) / math.tanh(1.6)
    return out * (0.944 / max(1e-9, np.abs(out).max()))


# -------------------------------------------------------------------------------------------------------------- CLI
def sel(ws, rx):
    r = re.compile(rx, re.I)
    return [w for w in ws if r.search(w.name)]


def cmd_list(whd_path, rx=DEFAULT_RX):
    ws = waves(open(whd_path, 'rb').read())
    s = sel(ws, rx); tot = 0
    print('%-8s %-6s %-5s %-3s %-6s %-8s %-8s %-8s %s' % ('record', 'codec', 'rate', 'ch', 'secs', 'bytes', 'offset', 'where', 'name'))
    for w in s:
        tot += 0 if w.streamed else w.get('size')
        print('%08x %-6s %-5d %-3d %6.3f %8d %08x %-8s %s' % (w.rec_off, hex(w.codec), w.get('rate'), w.get('ch'), w.seconds,
              w.get('size'), w.get('off'), 'stream' if w.streamed else 'memory', w.name))
    print('%d of %d records match /%s/, %.1f KB in memory' % (len(s), len(ws), rx, tot / 1024))


def cmd_extract(whd_path, outdir, rx=DEFAULT_RX):
    whd = open(whd_path, 'rb').read(); wav = open(whd_path[:-4] + '.WAV', 'rb').read()
    os.makedirs(outdir, exist_ok=True); n = 0
    for w in sel(waves(whd), rx):
        if w.streamed: continue
        x = decode_wave(wav, w); fn = '%08x_%s' % (w.rec_off, w.name.replace('/', '__'))
        write_wav(os.path.join(outdir, fn), to_i16(x), w.get('rate')); n += 1
    print('%d clips -> %s' % (n, outdir))


def cmd_refs(snd_path, whd_path, rx=DEFAULT_RX):
    snd = open(snd_path, 'rb').read(); ws = waves(open(whd_path, 'rb').read())
    so = snd_wave_objects(snd); ss = snd_sounds(snd)
    for w in sel(ws, rx):
        objs = so.get(w.rec_off, [])
        print('%08x %-62s' % (w.rec_off, w.name[-62:]))
        for o, sec in objs:
            print('     wave obj %08x %.3f s  <- %s' % (o, sec, ', '.join(ss.get(o, ['(no #sound)']))))


def _write_out(outdir, whd_path, nwhd, nwav, nsnd, snd_path):
    os.makedirs(outdir, exist_ok=True); base = os.path.basename(whd_path)[:-4]
    for ext, d in (('.WHD', nwhd), ('.WAV', nwav)): open(os.path.join(outdir, base + ext), 'wb').write(d)
    if nsnd is not None: open(os.path.join(outdir, os.path.basename(snd_path)), 'wb').write(nsnd)
    print('written to', outdir)


def _verify(nwhd, nwav, repl):
    """re-parse the rebuilt bank, decode each replaced clip again"""
    ws = {w.rec_off: w for w in waves(nwhd)}
    for ro in repl:
        x = decode_wave(nwav, ws[ro]); assert len(x) == ws[ro].get('samples'), ws[ro].name
    assert struct.unpack_from('<I', nwav, 4)[0] == len(nwav)
    print('verify: %d replaced records parse and decode, .WAV size field ok' % len(repl))


def cmd_replace(whd_path, outdir, mapfile, snd_path=None):
    whd = open(whd_path, 'rb').read(); wav = open(whd_path[:-4] + '.WAV', 'rb').read()
    snd = open(snd_path, 'rb').read() if snd_path else None
    by = {w.name.lower(): w for w in waves(whd)}; repl = {}
    for ln in open(mapfile, encoding='utf-8'):
        ln = ln.strip()
        if not ln or ln.startswith('#'): continue
        k, v = [s.strip() for s in ln.split('=', 1)]
        w = by[k.lower()]; x, r = read_wav(v)
        data, ns, pcmb = encode_for(w, x, r)
        repl[w.rec_off] = (data, ns, pcmb, (ns / w.get('ch') if w.codec == 1 else ns) / w.get('rate'))
    nwhd, nwav, nsnd = rebuild(whd, wav, repl, snd)
    _verify(nwhd, nwav, repl); _write_out(outdir, whd_path, nwhd, nwav, nsnd, snd_path)


def cmd_heat(whd_path, outdir, rx, style='street', snd_path=None, tail=None, fit=False):
    whd = open(whd_path, 'rb').read(); wav = open(whd_path[:-4] + '.WAV', 'rb').read()
    snd = open(snd_path, 'rb').read() if snd_path else None
    repl = {}; pre = os.path.join(outdir, 'preview'); os.makedirs(pre, exist_ok=True)
    for w in sel(waves(whd), rx):
        if w.streamed: continue
        x = decode_wave(wav, w); r = w.get('rate'); y = heat(x, r, style, tail=tail)
        if fit:     # --fit: keep the stock data size (no .WAV growth, nothing moves): cut to the stock length, 80 ms fade
            n = min(len(y), w.get('samples')); y = y[:n].copy(); fd = min(n, int(0.08 * r)); y[-fd:] *= np.linspace(1, 0, fd)[:, None]
        tag = w.name.split('/')[-1][:-4]
        write_wav(os.path.join(pre, tag + '_orig.wav'), to_i16(x), r)
        write_wav(os.path.join(pre, tag + '_heat_%s.wav' % style), to_i16(y), r)
        data, ns, pcmb = encode_for(w, y, r)
        repl[w.rec_off] = (data, ns, pcmb, (ns / w.get('ch') if w.codec == 1 else ns) / r)
    print('%d clip(s) processed (%s)' % (len(repl), style))
    nwhd, nwav, nsnd = rebuild(whd, wav, repl, snd)
    _verify(nwhd, nwav, repl); _write_out(outdir, whd_path, nwhd, nwav, nsnd, snd_path)


def cmd_selftest(whd_path):
    whd = open(whd_path, 'rb').read(); wav = open(whd_path[:-4] + '.WAV', 'rb').read()
    ws = [w for w in sel(waves(whd), r'_shot_0?1\.wav') if not w.streamed and w.codec == 0x11][:3]
    for w in ws:
        x = decode_wave(wav, w)
        data, ns, _ = encode_for(w, x, w.get('rate'))
        # re-encoding the decoded stock clip: same sample count, same byte count, near-identical audio
        y = ima_decode(data, w.get('ch'), w.get('block'), w.get('spb'), ns) / 32768.0
        err = 20 * math.log10(max(1e-12, np.sqrt(np.mean((x - y) ** 2))) / max(1e-12, np.sqrt(np.mean(x ** 2))))
        print('%-55s samples %d/%d bytes %d/%d  re-encode error %.1f dB' % (w.name[-55:], ns, w.get('samples'), len(data), w.get('size'), err))
    # identity rebuild: no replacement -> byte-identical files
    a, b, _ = rebuild(whd, wav, {}, None, log=lambda *_: None)
    print('identity rebuild: WHD %s, WAV %s' % ('identical' if a == whd else 'DIFFERENT', 'identical' if b == wav else 'DIFFERENT'))


def snd_groups(snd):
    """-> [(object offset, name, volume)] of the .SND group objects (type 0x17, table 23; volume f32 at +0x24, the
    same value again at +0x30 in every stock group seen: sfx_weapons_shot_npc 0.35, _shot_player 0.7)"""
    T = struct.unpack_from('<I', snd, 0)[0]; H = T + 0x30
    n = struct.unpack_from('<I', snd, H + 0x10 + 4 * 22)[0]; tab = struct.unpack_from('<I', snd, H + 0x74 + 4 * 22)[0]
    out = []
    for i in range(n):
        o = struct.unpack_from('<I', snd, tab + 4 * i)[0]; p = struct.unpack_from('<I', snd, o + 8)[0]
        out.append((o, snd[p:snd.index(NUL, p)].decode('latin1'), struct.unpack_from('<f', snd, o + 0x24)[0],
                    struct.unpack_from('<f', snd, o + 0x30)[0]))
    return out


def cmd_groups(snd_path):
    for o, n, v, v2 in snd_groups(open(snd_path, 'rb').read()):
        print('%08x %-58s %.3f %.3f' % (o, n, v, v2))


def cmd_groupvol(snd_path, out_path, pairs):
    """groupvol <bank.SND> <out.SND> sfx_weapons_shot_npc=0.6 ... : in-place float write, same file size"""
    snd = bytearray(open(snd_path, 'rb').read()); gs = {n.split('/')[-1].split('#')[0]: (o, v) for o, n, v, _ in snd_groups(bytes(snd))}
    for pr in pairs:
        k, v = pr.split('='); o, old = gs[k]; v = float(v)
        struct.pack_into('<f', snd, o + 0x24, v); struct.pack_into('<f', snd, o + 0x30, v)
        print('  %-40s %.3f -> %.3f' % (k, old, v))
    assert out_path != snd_path
    open(out_path, 'wb').write(snd); print('written', out_path)


def main(a):
    snd = None
    if '--snd' in a: i = a.index('--snd'); snd = a[i + 1]; del a[i:i + 2]
    style = 'street'; tail = None; fit = '--fit' in a
    if fit: a.remove('--fit')
    if '--tail' in a: i = a.index('--tail'); tail = float(a[i + 1]); del a[i:i + 2]
    if '--style' in a: i = a.index('--style'); style = a[i + 1]; del a[i:i + 2]
    if not a: print(__doc__); return 1
    c = a[0]
    if c == 'list': cmd_list(*a[1:3])
    elif c == 'extract': cmd_extract(*a[1:4])
    elif c == 'refs': cmd_refs(*a[1:4])
    elif c == 'replace': cmd_replace(a[1], a[2], a[3], snd)
    elif c == 'heat': cmd_heat(a[1], a[2], a[3], style, snd, tail, fit)
    elif c == 'groupvol': cmd_groupvol(a[1], a[2], a[3:])
    elif c == 'groups': cmd_groups(a[1])
    elif c == 'selftest': cmd_selftest(a[1])
    else: print(__doc__); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
