#!/usr/bin/env python3
"""
kl_launcher_music_test.py - self-test of tools/kl_launcher_music.py on SYNTHETIC data: no game file, no network.

A fake Dead Men-layout 'IOISNDSTREAM' file is written into a temp folder with
  - a lone PCM stereo clip,
  - a 2-layer interleaved PCM set (L1 R1 L2 R2) behind a 'LIP ' block, named like the Retomoto action theme,
  - a 2-layer set of unequal rates (stereo 8 kHz + stereo 4 kHz: L R L R l r),
  - a mono IMA ADPCM clip encoded here (the decoder must give the encoder's own reconstruction, sample-exact),
  - a Vorbis clip under the first candidate's name (must be SKIPPED by the default pick),
  - a stereo ADPCM clip (must be refused),
and, for Ogg Vorbis (codec 4), framed Ogg pages with real CRCs plus fake and real decoders (ogg_tests), and the module's read, de-interleave, decode, trim, fade and .wav output are checked against the known samples.
exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py.
"""
import array, io, math, os, shutil, struct, subprocess, sys, tempfile, wave

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_launcher_music as M

fails = []
NCHECK = [0]


def check(cond, what):
    NCHECK[0] += 1
    if cond:
        print('  ok   ' + what)
    else:
        print('  FAIL ' + what)
        fails.append(what)


def name_key(name):
    h = 0
    for b in name.encode('latin1'):
        h = (h * 5 + b) & 0xffffffff
    return h


def tone(n, freq, rate, amp=12000, phase=0.0):
    return array.array('h', [int(amp * math.sin(2 * math.pi * freq * i / rate + phase)) for i in range(n)])


def stereo(l, r):
    out = array.array('h', bytes(4 * len(l)))
    out[0::2] = l
    out[1::2] = r
    return out


def ima_encode(samples, block=0x400):
    """Mono IMA ADPCM, MS block layout -> (bytes, reconstruction array('h')) ; the reconstruction is what a
    matching decoder must give."""
    spb = (block - 4) * 2 + 1
    out, recon = bytearray(), array.array('h')
    idx = 0
    for b in range(0, len(samples), spb):
        chunk = samples[b:b + spb]
        pred = chunk[0]
        out += struct.pack('<hBB', pred, idx, 0)
        recon.append(pred)
        nibbles = []
        for s in chunk[1:]:
            step = M._STEP[idx]
            diff = s - pred
            sign = 8 if diff < 0 else 0
            diff = abs(diff)
            delta, vp = 0, step >> 3
            if diff >= step:
                delta |= 4; diff -= step; vp += step
            step >>= 1
            if diff >= step:
                delta |= 2; diff -= step; vp += step
            step >>= 1
            if diff >= step:
                delta |= 1; vp += step
            pred = pred - vp if sign else pred + vp
            pred = max(-32768, min(32767, pred))
            recon.append(pred)
            idx = max(0, min(88, idx + M._IDX[delta]))
            nibbles.append(delta | sign)
        while len(nibbles) < (block - 4) * 2:
            nibbles.append(0)
        for i in range(0, len(nibbles), 2):
            out.append(nibbles[i] | (nibbles[i + 1] << 4))
    return bytes(out), recon


class Fake:
    """Builds a Dead Men-layout stream file."""

    def __init__(self):
        self.blocks = []            # (lip bool, audio bytes, [entries]) ; entry = dict(name, codec, samples, channels, rate, bits, size, layer, extra)

    def add(self, audio, entries, lip=False):
        self.blocks.append((lip, audio, entries))

    def write(self, path):
        f = io.BytesIO()
        f.write(b'IOISNDSTREAM' + struct.pack('<I', 9) + struct.pack('<Q', 0x46e11c9f))
        f.write(b'\0' * (0x100 - f.tell()))
        recs = []
        for lip, audio, entries in self.blocks:
            off = f.tell()
            if lip:
                f.write(b'LIP ' + struct.pack('<I', 16) + b'x' * 16 + b'\0' * (M.LIP - 24))
            f.write(audio)
            f.write(b'\0' * ((-f.tell()) % 0x100))
            for e in entries:
                recs.append((off, e))
        fmts = []
        for off, e in recs:
            fmt = struct.pack('<5I', e['codec'], e['samples'], e['channels'], e['rate'], e['bits']) + b'junkjunk' + e.get('extra', b'')
            fmts.append(fmt)
        fmt_at = []
        for fmt in fmts:
            fmt_at.append(f.tell()); f.write(fmt)
        name_at = []
        for off, e in recs:
            name_at.append(f.tell()); f.write(e['name'].encode('latin1') + b'\0')
        f.write(b'\0' * ((-f.tell()) % 4))
        index = f.tell()
        rows = []
        for i, (off, e) in enumerate(recs):
            key = name_key(e['name'])
            rows.append((key, struct.pack('<4Q2I4Q', i, off, e['size'], fmt_at[i], len(fmts[i]), key, len(e['name']), name_at[i],
                                          4 if e.get('lip') else 0, e['layer'])))
        rows.sort(key=lambda r: r[0])
        for _, r in rows:
            f.write(r)
        data = f.getvalue()
        data = data[:0x18] + struct.pack('<IIIIIH', index, len(recs), 0x100, 0, 1, 0x38) + data[0x18 + 22:]
        with open(path, 'wb') as out:
            out.write(data)
        return len(recs)


def read_wav(path):
    with wave.open(path, 'rb') as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        s = array.array('h'); s.frombytes(w.readframes(n))
        if sys.byteorder != 'little':
            s.byteswap()
    return ch, width, rate, n, s


def ogg_page(serial, seq, htype, payload, granule=0, bad_crc=False):
    segs = []
    n = len(payload)
    while n >= 255:
        segs.append(255); n -= 255
    segs.append(n)
    page = bytearray(b'OggS' + struct.pack('<BBqIII', 0, htype, granule, serial, seq, 0) + bytes([len(segs)]) + bytes(segs) + payload)
    crc = M.ogg_crc(bytes(page))
    struct.pack_into('<I', page, 22, (crc ^ 1) if bad_crc else crc)
    return bytes(page)


def fake_ogg(npages=3, bad_at=None):
    """A framed Ogg stream: page 0 starts with a Vorbis id header, the rest is junk (decoders must fail on it)."""
    out = ogg_page(7, 0, 2, b'\x01vorbis' + b'\0' * 23, bad_crc=(bad_at == 0))
    for i in range(1, npages):
        out += ogg_page(7, i, 0, bytes((j * 7 + i) & 255 for j in range(600)), bad_crc=(bad_at == i))
    return out


def riff_tests(d, out, py, menuwav, mrate):
    """The default riff + menu loop: a fake Movies/Trailer.bik decoder (a script printing a known WAV), the menu from the
    caller's working fake Vorbis decoder (4 s at mrate)."""
    rr = 2000
    a0, a1 = int(M.RIFF_START * rr), int(M.RIFF_END * rr)
    src = stereo(tone(rr * 45, 50, rr, 20000), tone(rr * 45, 70, rr, 20000, 1.0))
    def fake_bik(secs):
        p = os.path.join(d, 'trailer%d.wav' % secs)
        with open(p, 'wb') as f:
            f.write(M.wav_bytes(src[:2 * rr * secs], 2, rr))
        sp = os.path.join(d, 'fakebik%d.py' % secs)
        with open(sp, 'w') as f:
            f.write('import sys\nsys.stdout.buffer.write(open(%r, "rb").read())\n' % p)
        return lambda path: [('fakebik', [py, sp])]
    real_bd, real_pb = M.bink_decoders, M.py_bink
    M.py_bink = lambda: None
    try:
        lines = []
        M.bink_decoders = fake_bik(45)
        c = M.extract(d, out, None, 2.0, lines.append)
        check(c.name == 'SFX/UserInterface/MenuLoop_01.wav' and any('riff loop skipped' in l and 'Trailer.bik' in l for l in lines),
              'riff: no Movies/Trailer.bik -> skipped with the reason, MenuLoop_01 alone')
        mov = os.path.join(d, 'Movies'); os.makedirs(mov)
        open(os.path.join(mov, 'Trailer.bik'), 'wb').close()
        lines = []
        c = M.extract(d, out, None, 2.0, lines.append)
        ch, width, r, frames, s = read_wav(out)
        R, n, mfr = a1 - a0, int(M.RIFF_SEAM * rr), 4 * rr
        x = min(int(M.RIFF_XFADE * rr), R, mfr // 2)
        check(c.name == 'SFX/UserInterface/MenuLoop_01.wav' and any(l.startswith('wrote') and 'riff x2' in l for l in lines),
              'riff: Trailer.bik decodes -> the riff loop is written (default, no --clip)')
        check((ch, width, r, frames) == (2, 2, rr, 2 * R - n + mfr - x),
              'riff: stereo at the trailer rate, length = 2 riffs - seam + menu - crossfade (%d frames)' % frames)
        check(s[0] == 0 and s[-1] == 0 and s[-2] == 0, 'riff: starts at 0 (10 ms fade-in) and ends faded to 0 (the loop seam)')
        k = [j for j in range(40, R - n) if abs(src[2 * (a0 + j)]) > 15000][:5]
        g = [float(s[2 * j]) / src[2 * (a0 + j)] for j in k]
        check(len(g) == 5 and max(g) - min(g) < 0.002 and 0 < g[0] <= 1, 'riff: the riff is the trailer from RIFF_START, one gain (%.3f)' % g[0])
        same = all(s[2 * (R - n + j) + q] == s[2 * j + q] for j in range(n, R - n - x, 97) for q in (0, 1))
        check(same, 'riff: after the seam the 2nd riff repeats the 1st sample for sample')
        check(M.main(['extract', '--dm', d, '--out', out, '--no-riff']) == 0 and read_wav(out)[2] == mrate,
              'riff: --no-riff writes MenuLoop_01 alone (at its own rate)')
        check(M.main(['extract', '--dm', d, '--out', out, '--clip', 'FA_SlashMixPrison']) == 0 and read_wav(out)[3] == 3 * mrate,
              'riff: --clip names one clip -> that clip, no riff')
        M.bink_decoders = fake_bik(30)
        lines = []
        c = M.extract(d, out, None, 2.0, lines.append)
        check(read_wav(out)[2] == mrate and any('riff loop skipped' in l and 'decoded by fakebik' in l for l in lines),
              'riff: a 30 s trailer (short read) is refused -> MenuLoop_01 alone')
        M.bink_decoders = lambda path: []
        lines = []
        M.extract(d, out, None, 2.0, lines.append)
        check(any('neither ffmpeg nor kl_pybink' in l for l in lines), 'riff: no Bink decoder -> skipped, the log names ffmpeg and kl_pybink')
        class PB(object):
            @staticmethod
            def bink_audio(path, track, a, b):
                return src[2 * int(a * rr):2 * int(b * rr)], 2, rr
        M.py_bink = lambda: PB
        lines = []
        M.extract(d, out, None, 2.0, lines.append)
        check(read_wav(out)[2] == rr and any('(kl_pybink)' in l for l in lines), 'riff: no ffmpeg -> kl_pybink decodes the window')
    finally:
        M.bink_decoders, M.py_bink = real_bd, real_pb
    up = M.regain(array.array('h', [0, 0, 100, -100, 200, -200]), 2, 4000, 8000, 1.0)
    check(list(up) == [0, 0, 50, -50, 100, -100, 150, -150, 200, -200, 200, -200], 'regain: 4 -> 8 kHz linear midpoints, per channel')
    check(list(M.regain(array.array('h', [1000, -1000]), 2, 8000, 8000, 0.5)) == [500, -500], 'regain: same rate = gain only')
    check(list(M.to_stereo(array.array('h', [1, 2]), 1)) == [1, 1, 2, 2], 'to_stereo doubles a mono clip')


def ogg_tests(tmp, M):
    good = fake_ogg(3)
    check(M.ogg_check(good) == 3, 'ogg_check: 3 framed pages with good CRCs pass')
    for what, blob in (('a bad CRC in the middle page', fake_ogg(3, bad_at=1)),
                       ('a bad CRC in the first page', fake_ogg(3, bad_at=0)),
                       ('a cut-off last page', good[:-10]),
                       ('trailing junk after the last page', good + b'xx'),
                       ('a non-Ogg record', b'RIFF' + b'\x55' * 3000),
                       ('an empty record', b''),
                       ('an Ogg stream that is not Vorbis', ogg_page(1, 0, 2, b'\x7fFLAC' + bytes(30)))):
        try:
            M.ogg_check(blob); check(False, 'ogg_check refuses ' + what)
        except M.NoClip as e:
            check(True, 'ogg_check refuses %s (%s)' % (what, e))
    # a codec-4 clip in a stream file: framed Ogg + junk payload -> CRC ok but no decoder can decode it
    rate = 32000
    fk = Fake()
    fk.add(good, [dict(name='SFX/UserInterface/MenuLoop_01.wav', codec=M.VORBIS, samples=rate * 154, channels=2, rate=rate, bits=0, size=len(good), layer=0)])
    tone_n = rate * 3
    t = stereo(tone(tone_n, 220, rate), tone(tone_n, 330, rate))
    fk.add(t.tobytes(), [dict(name='Music/InHouse/FA_Slash/FA_SlashMixPrison.wav', codec=M.PCM, samples=tone_n, channels=2, rate=rate, bits=16, size=len(t) * 2, layer=0, extra=struct.pack('<I', 4))])
    d = os.path.join(tmp, 'ogg'); os.makedirs(d)
    strpath = os.path.join(d, 'PC_Def.str')
    fk.write(strpath)
    out = os.path.join(d, 'o.wav')
    real, real_py = M.vorbis_decoders, M.py_vorbis
    M.py_vorbis = lambda: None                                    # the external-decoder cases first; kl_pyvorbis below
    st = M.Stream(strpath)
    c0 = st.clips[0]
    try:
        # (a) neither decoder -> MenuLoop skipped with a clear reason, falls to the next candidate (the PCM one)
        M.vorbis_decoders = lambda: []
        lines = []
        c = M.extract(d, out, None, 2.0, lines.append)
        check(c.name.endswith('FA_SlashMixPrison.wav'), 'decoder missing: falls to the next candidate (%s)' % c.name)
        check(any('neither' in l and 'kl_oggdec' in l and 'ffmpeg' in l for l in lines), 'decoder missing: the log names both decoders')
        check(M.main(['extract', '--dm', d, '--out', out, '--clip', 'MenuLoop_01']) == 2, 'decoder missing: --clip of the Vorbis clip -> exit 2')
        # (b) a bad CRC is refused BEFORE any decoder is looked for
        ran = []
        M.vorbis_decoders = lambda: ran.append(1) or []
        try:
            M.decode_vorbis(c0, fake_ogg(3, bad_at=2), 5); check(False, 'bad CRC refused')
        except M.NoClip as e:
            check('CRC' in str(e) and not ran, 'bad CRC refused before a decoder is looked for (%s)' % e)
        # (c) a decoder that fails -> next decoder; the second one works -> its samples (trimmed) come back
        pcm = stereo(tone(rate * 4, 440, rate), tone(rate * 4, 550, rate))
        wav = M.wav_bytes(pcm, 2, rate)
        py = sys.executable
        script = os.path.join(d, 'fakedec.py')
        with open(script, 'w') as f:
            f.write('import sys\nsys.stdin.buffer.read()\nsys.stderr.write("boom")\nsys.exit(3)\n')
        wavpath = os.path.join(d, 'pcm.wav')
        with open(wavpath, 'wb') as f:
            f.write(wav)
        script2 = os.path.join(d, 'fakedec2.py')
        with open(script2, 'w') as f:
            f.write('import sys\nsys.stdin.buffer.read()\nsys.stdout.buffer.write(open(%r, "rb").read())\n' % wavpath)
        M.vorbis_decoders = lambda: [('bad', [py, script], 'wav'), ('good', [py, script2], 'wav')]
        s, ch, r = M.decode_vorbis(c0, good, 1.5)
        check((ch, r, len(s)) == (2, rate, 2 * int(1.5 * rate)) and s == pcm[:len(s)], 'first decoder fails, second is used; trimmed to 1.5 s exact')
        M.vorbis_decoders = lambda: [('bad', [py, script], 'wav')]
        try:
            M.decode_vorbis(c0, good, 1.5); check(False, 'all decoders failing is refused')
        except M.NoClip as e:
            check('boom' in str(e), 'all decoders failing -> NoClip with the decoder message')
        # (d) the full extract path with a working fake decoder: MenuLoop is CANDIDATES[0] and wins
        M.vorbis_decoders = lambda: [('good', [py, script2], 'wav')]
        c = M.extract(d, out, None, 2.0, lambda l: None)
        check(c.name == 'SFX/UserInterface/MenuLoop_01.wav', 'MenuLoop_01 is the default pick when it decodes')
        ch, width, r, frames, s = read_wav(out)
        check((ch, width, r, frames) == (2, 2, rate, 2 * rate) and s[0] == 0 and s[-1] == 0, 'extract of the Vorbis clip: 2.0 s, faded, clip rate')
        riff_tests(d, out, py, wavpath, rate)
        # (e) no exe and no ffmpeg: kl_pyvorbis is tried last; on the junk payload it fails and the error is named
        M.vorbis_decoders = lambda: []
        M.py_vorbis = real_py
        if real_py():
            try:
                M.decode_vorbis(c0, good, 1.5); check(False, 'junk Ogg refused by kl_pyvorbis')
            except M.NoClip as e:
                check('kl_pyvorbis' in str(e), 'no exe/ffmpeg: kl_pyvorbis is tried and its refusal named (%s)' % e)
        else:
            check(False, 'kl_pyvorbis.py is beside kl_launcher_music.py')
    finally:
        M.vorbis_decoders, M.py_vorbis = real, real_py
    check(M.CANDIDATES[0][0] == 'SFX/UserInterface/MenuLoop_01.wav', 'CANDIDATES[0] = the Dead Men main menu loop')
    check(len(M.CANDIDATES) >= 5 and M.CANDIDATES[1][0].endswith('FA_SlashMixPrison.wav'), 'the older candidates follow it')
    # parse_wav16: streamed header (sizes 0xffffffff, as ffmpeg pipes write it)
    blob = bytearray(wav); struct.pack_into('<I', blob, 40, 0xffffffff); struct.pack_into('<I', blob, 4, 0xffffffff)
    s, ch, r = M.parse_wav16(bytes(blob))
    check((ch, r, len(s)) == (2, rate, len(pcm)) and s == pcm, 'parse_wav16 accepts a streamed (size 0xffffffff) header')
    # real decoders (only when this PC has them): encode a sine with ffmpeg/libvorbis, ogg_check it, decode with each decoder
    ff = shutil.which('ffmpeg')
    if ff:
        ogg = os.path.join(d, 'sine.ogg')
        rr = subprocess.run([ff, '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3:sample_rate=32000', '-ac', '2', '-c:a', 'libvorbis', ogg], capture_output=True)
        if rr.returncode == 0 and os.path.isfile(ogg):
            blob = open(ogg, 'rb').read()
            check(M.ogg_check(blob) >= 2, 'a real ffmpeg-made Ogg Vorbis file passes ogg_check (CRC of every page)')
            decs = real()
            check(len(decs) >= 1, 'a decoder is found on this PC (%s)' % ', '.join(x[0] for x in decs))
            for label, argv, _ in decs:
                M.vorbis_decoders = lambda a=argv, l=label: [(l, a, 'wav')]
                try:
                    s, ch, r2 = M.decode_vorbis(c0, blob, 10)
                finally:
                    M.vorbis_decoders = real
                peak = max(abs(x) for x in s)
                check(ch == 2 and r2 == 32000 and abs(len(s) // 2 - 96000) < 2400 and 1000 < peak < 32767, '%s decodes a real Ogg: 32 kHz stereo ~3 s, sane peak (%d)' % (label, peak))
            # kl_pyvorbis on the same file vs ffmpeg's own decode: same frames, at most a few LSB apart
            ref = subprocess.run([ff, '-v', 'error', '-nostdin', '-i', ogg, '-f', 'wav', '-acodec', 'pcm_s16le', 'pipe:1'], capture_output=True)
            if ref.returncode == 0:
                fs, fch, frate = M.parse_wav16(ref.stdout)
                ps, pch, prate = real_py().vorbis_decode(blob, 10 ** 9)
                diff = max(abs(x - y) for x, y in zip(ps, fs)) if len(ps) == len(fs) else -1
                check((pch, prate, len(ps)) == (fch, frate, len(fs)) and 0 <= diff <= 2, 'kl_pyvorbis = ffmpeg on a real Ogg (%d vs %d samples, max diff %d)' % (len(ps), len(fs), diff))
        else:
            print('  note ffmpeg has no libvorbis here: real-Ogg checks skipped')
    else:
        print('  note no ffmpeg: real-Ogg checks skipped')
    st.close()


def main():
    tmp = tempfile.mkdtemp(prefix='klmusic_test_')
    try:
        return run(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(tmp):
    print('kl_launcher_music_test: synthetic stream in ' + tmp)
    rate, lo = 8000, 4000
    secs = 6
    n = rate * secs
    pcm_extra = struct.pack('<I', 4)
    fk = Fake()
    # 1. lone stereo PCM
    solo_l, solo_r = tone(n, 220, rate), tone(n, 330, rate, phase=1.0)
    solo = stereo(solo_l, solo_r)
    fk.add(solo.tobytes(), [dict(name='Music/InHouse/Test/Solo.wav', codec=M.PCM, samples=n, channels=2, rate=rate, bits=16, size=4 * n, layer=0, extra=pcm_extra)])
    # 2. 2-layer stereo set behind a LIP block (L1 R1 L2 R2)
    l1 = stereo(tone(n, 110, rate), tone(n, 165, rate, phase=0.5))
    l2 = stereo(tone(n, 440, rate, amp=6000), tone(n, 660, rate, amp=6000, phase=2.0))
    inter = array.array('h', bytes(8 * n))
    inter[0::4] = l1[0::2]; inter[1::4] = l1[1::2]; inter[2::4] = l2[0::2]; inter[3::4] = l2[1::2]
    L1 = 'Music/InHouse/Japan/M09_A/TakyoAction_V3_44_Layer1_Loop.wav'
    L2 = 'Music/InHouse/Japan/M09_A/TakyoAction_Layer2_TAmbient_Loop.wav'
    SETN = 'LevelSetup/Level/M09_A/Music/TokyoAction1'
    fk.add(inter.tobytes(), [dict(name=L1, codec=M.PCM, samples=n, channels=2, rate=rate, bits=16, size=4 * n, layer=1, extra=pcm_extra),
                             dict(name=L2, codec=M.PCM, samples=n, channels=2, rate=rate, bits=16, size=4 * n, layer=2, extra=pcm_extra),
                             dict(name=SETN, codec=M.SET, samples=n, channels=2, rate=rate, bits=16, size=8 * n, layer=2, extra=struct.pack('<I', 2), lip=True)],
           lip=True)
    # 3. unequal-rate set: stereo 8 kHz + stereo 4 kHz -> L R L R l r per period (2 frames of the fast layer, 1 of the slow)
    hi = stereo(tone(n, 200, rate), tone(n, 300, rate))
    slow_n = n // 2
    sl = stereo(tone(slow_n, 50, lo, amp=3000), tone(slow_n, 75, lo, amp=3000))
    mix = array.array('h')
    for p in range(slow_n):
        mix.extend(hi[4 * p:4 * p + 4]); mix.extend(sl[2 * p:2 * p + 2])
    fk.add(mix.tobytes(), [dict(name='Music/InHouse/Test/Fast.wav', codec=M.PCM, samples=n, channels=2, rate=rate, bits=16, size=4 * n, layer=1, extra=pcm_extra),
                           dict(name='Music/InHouse/Test/Slow.wav', codec=M.PCM, samples=slow_n, channels=2, rate=lo, bits=16, size=4 * slow_n, layer=2, extra=pcm_extra),
                           dict(name='LevelSetup/Level/Test/Music/Mixed', codec=M.SET, samples=n, channels=2, rate=rate, bits=16, size=6 * n, layer=2, extra=struct.pack('<I', 2))])
    # 4. mono IMA ADPCM
    mono = tone(n, 180, rate, amp=9000)
    adp, recon = ima_encode(mono)
    fk.add(adp, [dict(name='Music/InHouse/Test/Adpcm.wav', codec=M.ADPCM, samples=n, channels=1, rate=rate, bits=4, size=len(adp), layer=0, extra=struct.pack('<II', 0x400, 0x7f9))])
    # 5. Vorbis under the FIRST candidate's name, and a stereo ADPCM clip
    fk.add(b'OggS' + b'\x55' * 3000, [dict(name='Music/InHouse/FA_Slash/FA_SlashMixPrison.wav', codec=M.VORBIS, samples=rate * 251, channels=2, rate=rate, bits=0, size=3004, layer=0)])
    fk.add(b'\x11' * 2048, [dict(name='Music/InHouse/Test/StereoAdpcm.wav', codec=M.ADPCM, samples=2000, channels=2, rate=rate, bits=4, size=2048, layer=0, extra=struct.pack('<II', 0x400, 0x7f9))])
    path = os.path.join(tmp, 'PC_Def.str')
    count = fk.write(path)

    # ---- read
    st = M.Stream(path)
    check(st.game == 'dm' and st.count == count == 10, 'reads the Dead Men header and %d index records' % count)
    check(st.find('Music/InHouse/Test/Solo.wav').codec == M.PCM, 'find() exact name')
    check(st.find('music/inhouse/test/solo') is not None, 'find() case-insensitive, .wav optional')
    check(st.find('TakyoAction_Layer2_TAmbient_Loop') is not None, 'find() by unique suffix')
    check(st.find('nothing_here') is None, 'find() unknown -> None')
    c2 = st.find(L2)
    check([x.name for x in st.layers(c2)] == [L1, L2], 'layers() gives the set parts in layer order without the set entry')
    check(st.has_lip(c2.offset), 'the set block carries a LIP block')
    check(st.find(SETN).nclips == 2, 'set entry: number of clips read from the format')
    ad = st.find('Music/InHouse/Test/Adpcm.wav')
    check((ad.block, ad.spb) == (0x400, 0x7f9), 'ADPCM block / samples-per-block read from the format')

    # ---- decode: lone PCM, full length (no trim)
    s, ch, r = M.decode(st, st.find('Music/InHouse/Test/Solo.wav'), 60)
    check((ch, r, len(s)) == (2, rate, 2 * n) and s == solo, 'lone PCM decodes sample-exact')
    # trim
    s, ch, r = M.decode(st, st.find('Music/InHouse/Test/Solo.wav'), 2.5)
    check(len(s) == 2 * int(2.5 * rate) and s == solo[:2 * int(2.5 * rate)], 'trim to 2.5 s keeps the first frames exactly')
    # set layers (behind the LIP block)
    s1, ch, r = M.decode(st, st.find(L1), 60)
    s2, ch2, r2 = M.decode(st, c2, 60)
    check(s1 == l1 and (ch, r) == (2, rate), 'set layer 1 de-interleaved sample-exact')
    check(s2 == l2 and (ch2, r2) == (2, rate), 'set layer 2 de-interleaved sample-exact (LIP block skipped)')
    s3, ch3, r3 = M.decode(st, st.find(SETN), 60)
    check(s3 == l1, 'the set entry itself decodes to layer 1 (the driving layer)')
    s2t, _, _ = M.decode(st, c2, 1.25)
    check(len(s2t) == 2 * int(1.25 * rate) and s2t == l2[:len(s2t)], 'set layer trim to 1.25 s exact')
    # unequal rates
    sf, chf, rf = M.decode(st, st.find('Music/InHouse/Test/Fast.wav'), 60)
    ss, chs, rs = M.decode(st, st.find('Music/InHouse/Test/Slow.wav'), 60)
    check(sf == hi and (chf, rf) == (2, rate), 'unequal-rate set: fast layer (2 frames per period) exact')
    check(ss == sl and (chs, rs) == (2, lo), 'unequal-rate set: slow layer (1 frame per period) exact')
    sst, _, _ = M.decode(st, st.find('Music/InHouse/Test/Slow.wav'), 1.0)
    check(len(sst) == 2 * lo and sst == sl[:2 * lo], 'unequal-rate set: slow layer trim to 1 s exact')
    # ADPCM
    sa, cha, ra = M.decode(st, ad, 60)
    check((cha, ra, len(sa)) == (1, rate, n) and sa == recon, 'mono IMA ADPCM decodes to the encoder reconstruction, sample-exact')
    sat, _, _ = M.decode(st, ad, 0.7)
    check(len(sat) == int(0.7 * rate) and sat == recon[:len(sat)], 'ADPCM trim exact')
    # refusals
    for nm, why in (('Music/InHouse/FA_Slash/FA_SlashMixPrison.wav', 'Vorbis is refused'), ('Music/InHouse/Test/StereoAdpcm.wav', 'stereo ADPCM is refused')):
        try:
            M.decode(st, st.find(nm), 60); check(False, why)
        except M.NoClip as e:
            check(True, why + ' (%s)' % e)
    st.close()

    # ---- Ogg Vorbis (codec 4)
    ogg_tests(tmp, M)

    # ---- fade + wav
    s = array.array('h', [10000] * (2 * 6 * rate))
    M.fade(s, 2, rate)
    check(s[0] == 0 and s[1] == 0 and s[-1] == 0 and s[-2] == 0, 'fade: first and last frames are silent')
    check(s[2 * int(1.5 * rate)] == 10000 and s[2 * int(2.5 * rate) + 1] == 10000, 'fade: the middle (between 1 s in and 3 s out) is untouched')
    check(0 < s[2 * int(0.5 * rate)] < 10000 and 0 < s[-2 * int(1.5 * rate)] < 10000, 'fade: ramps are between 0 and full')
    blob = M.wav_bytes(array.array('h', [1, -2, 3, -4]), 2, 32000)
    check(blob[:4] == b'RIFF' and blob[8:12] == b'WAVE' and struct.unpack_from('<I', blob, 4)[0] == len(blob) - 8, 'wav_bytes: RIFF sizes')
    check(struct.unpack_from('<HHIIHH', blob, 20) == (1, 2, 32000, 128000, 4, 16), 'wav_bytes: fmt chunk 16-bit PCM stereo 32 kHz')

    # ---- extract (the CLI): default pick skips the Vorbis candidate and lands on the Retomoto bed
    out = os.path.join(tmp, 'music', 'deadmen_launcher.wav')
    lines = []
    c = M.extract(path, out, None, 2.0, lines.append)
    check(c.name == L2, 'default pick = %s (first candidate Vorbis -> skipped)' % L2.split('/')[-1])
    check(any('skipped' in l and 'Ogg' in l for l in lines), 'the log says why the (non-Ogg) FA theme was skipped')
    ch, width, r, frames, s = read_wav(out)
    check((ch, width, r, frames) == (2, 2, rate, 2 * rate), 'written .wav: stereo 16-bit, clip rate, 2.0 s')
    check(s[0] == 0 and s[-1] == 0, 'written .wav is faded')
    check(sorted(os.listdir(os.path.dirname(out))) == ['deadmen_launcher.wav'], 'nothing but the one .wav was written')
    rc = M.main(['extract', '--dm', tmp, '--out', out, '--clip', 'Music/InHouse/Test/Solo.wav', '--seconds', '1.5'])
    check(rc == 0, 'CLI extract --clip -> exit 0')
    ch, width, r, frames, s = read_wav(out)
    mid = 2 * (rate * 3 // 4)
    check(frames == int(1.5 * rate) and ch == 2, 'CLI: trimmed to 1.5 s')
    # with 1.5 s the fade-out covers 0.5 s (frames - n_in): the sample at 0.75 s is on the out ramp but not at the fade-in -> compare after undoing nothing: just check it is a scaled solo sample
    check(abs(s[mid]) <= abs(solo[mid]), 'CLI: samples are the clip, faded')
    rc = M.main(['extract', '--dm', tmp, '--out', out, '--clip', 'Music/InHouse/FA_Slash/FA_SlashMixPrison.wav'])
    check(rc == 2, 'CLI: a Vorbis --clip -> exit 2')
    rc = M.main(['extract', '--dm', tmp, '--out', out, '--clip', 'no/such/clip.wav'])
    check(rc == 2, 'CLI: unknown --clip -> exit 2')
    rc = M.main(['extract', '--dm', os.path.join(tmp, 'nowhere'), '--out', out])
    check(rc == 2, 'CLI: no PC_Def.str -> exit 2')
    empty = os.path.join(tmp, 'empty')
    os.makedirs(empty)
    with open(os.path.join(empty, 'PC_Def.str'), 'wb') as f:
        f.write(b'IOISNDSTREAM' + b'\0' * 100)
    rc = M.main(['extract', '--dm', empty, '--out', os.path.join(tmp, 'x', 'y.wav')])
    check(rc == 2 and not os.path.exists(os.path.join(tmp, 'x', 'y.wav')), 'CLI: a broken stream file -> exit 2, nothing written')
    with open(path, 'rb') as f:
        trunc = f.read()[:-100]
    tp = os.path.join(tmp, 'trunc')
    os.makedirs(tp)
    with open(os.path.join(tp, 'PC_Def.str'), 'wb') as f:
        f.write(trunc)
    check(M.main(['extract', '--dm', tp, '--out', out]) == 2, 'CLI: a truncated stream file -> exit 2')
    nocand = Fake()
    nocand.add(solo.tobytes(), [dict(name='Music/Other/Tune.wav', codec=M.PCM, samples=n, channels=2, rate=rate, bits=16, size=4 * n, layer=0, extra=pcm_extra)])
    np_ = os.path.join(tmp, 'nocand'); os.makedirs(np_); nocand.write(os.path.join(np_, 'PC_Def.str'))
    check(M.main(['extract', '--dm', np_, '--out', out]) == 2, 'CLI: no candidate in the file -> exit 2')
    check(M.main(['extract', '--dm', np_, '--out', out, '--clip', 'Tune']) == 0, 'CLI: ... but --clip of a clip it has -> exit 0')
    check(M.main(['extract', '--dm', tmp, '--out', out, '--seconds', '0']) == 1, 'CLI: --seconds 0 -> usage exit 1')
    check(M.main([]) == 1, 'CLI: no command -> exit 1')
    # list
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M.main(['list', '--dm', tmp, 'Japan'])
    txt = buf.getvalue()
    check(rc == 0 and L1 in txt and L2 in txt and 'Solo' not in txt and '2 clips' in txt, 'CLI list with a filter')
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M.main(['extract', '--dm', tmp, '--out', out, '--list'])
    check(rc == 0 and 'FA_SlashMixPrison' in buf.getvalue() and 'vorbis' in buf.getvalue(), 'extract --list lists the Music/ clips with their codec')
    # the candidate table names real Dead Men paths and each has a reason
    check(all(nm.startswith(('Music/', 'SFX/')) and nm.endswith('.wav') and why for nm, why in M.CANDIDATES), 'CANDIDATES are Music/...wav names with a reason each')
    check('GUESS' in M.__doc__ and 'PROVEN' in M.__doc__, 'the module marks what is proven and what is guessed')

    if fails:
        print('RESULT: FAIL %d check(s): %s' % (len(fails), '; '.join(fails)[:400]))
        return 1
    print('RESULT: PASS (%d checks)' % NCHECK[0])
    return 0


if __name__ == '__main__':
    sys.exit(main())
