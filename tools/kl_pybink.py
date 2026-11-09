"""Pure-Python Bink Audio decoder (Bink 1 .bik container, DCT and RDFT audio).

Used by the launcher music when the tester has no ffmpeg: Dead Men's Movies/Trailer.bik
audio is decoded on the tester's own PC, so no game audio ships.

Layout and decoder follow ffmpeg's libavformat/bink.c + libavcodec/binkaudio.c
(public format knowledge, rewritten): LSB-first bit reader, 'quant' per critical band,
RLE run lengths, DCT-III (or real inverse DFT) per channel block, 1/16 linear overlap.

API: bink_audio(bik_bytes_or_path, track=0, start_s=None, end_s=None)
       -> (array('h') interleaved, channels, rate); raises BinkError.
     bink_info(bik_bytes_or_path) -> dict (header + audio tracks).
Only array/math/struct/cmath imports.
"""
import array
import cmath
import math
import struct


class BinkError(Exception):
    pass


FLAG_16BITS = 0x4000
FLAG_STEREO = 0x2000
FLAG_DCT = 0x1000

CRITICAL_FREQS = (100, 200, 300, 400, 510, 630, 770, 920, 1080, 1270, 1480, 1720, 2000,
                  2320, 2700, 3150, 3700, 4400, 5300, 6400, 7700, 9500, 12000, 15500, 24500)
RLE_LENGTHS = (2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 32, 64)


class _Src:
    """read_at over bytes or an open file (no io import)."""

    def __init__(self, src):
        if isinstance(src, (bytes, bytearray, memoryview)):
            self.buf = memoryview(src)
            self.f = None
            self.size = len(self.buf)
        else:
            self.buf = None
            self.f = open(src, 'rb')
            self.f.seek(0, 2)
            self.size = self.f.tell()

    def read_at(self, off, n):
        if off < 0 or off + n > self.size:
            raise BinkError('read past end (%d+%d > %d)' % (off, n, self.size))
        if self.f is None:
            return bytes(self.buf[off:off + n])
        self.f.seek(off)
        return self.f.read(n)

    def close(self):
        if self.f is not None:
            self.f.close()


def _parse(src):
    head = src.read_at(0, 44)
    sig = head[:3]
    ver = head[3:4]
    if sig != b'BIK':
        raise BinkError('not a Bink 1 file (signature %r)' % head[:4])
    if ver not in (b'b', b'd', b'f', b'g', b'h', b'i', b'k'):
        raise BinkError('unsupported Bink version %r' % ver)
    (_size, frames, _largest, _frames2, width, height, fps_num, fps_den, vflags,
     ntracks) = struct.unpack_from('<10I', head, 4)
    if frames == 0 or frames > 1000000:
        raise BinkError('bad frame count %d' % frames)
    if ntracks > 256:
        raise BinkError('bad audio track count %d' % ntracks)
    off = 44
    tracks = []
    if ntracks:
        off += 4 * ntracks                      # max decoded size per track
        th = src.read_at(off, 8 * ntracks)
        for t in range(ntracks):
            rate, flags = struct.unpack_from('<HH', th, 4 * t)
            tid = struct.unpack_from('<I', th, 4 * ntracks + 4 * t)[0]
            tracks.append({'rate': rate, 'flags': flags, 'id': tid,
                           'channels': 2 if flags & FLAG_STEREO else 1,
                           'codec': 'dct' if flags & FLAG_DCT else 'rdft'})
        off += 8 * ntracks
    idx = src.read_at(off, 4 * (frames + 1))
    offs = struct.unpack_from('<%dI' % (frames + 1), idx)
    offsets = [o & ~1 for o in offs]
    for a, b in zip(offsets, offsets[1:]):
        if b < a:
            raise BinkError('frame index not increasing')
    if offsets[-1] > src.size:
        raise BinkError('frame index past end of file')
    return {'version': ver.decode(), 'frames': frames, 'width': width, 'height': height,
            'fps': fps_num / fps_den if fps_den else 0.0, 'video_flags': vflags,
            'tracks': tracks, 'offsets': offsets}


def bink_info(src):
    s = _Src(src)
    try:
        info = _parse(s)
        info = dict(info)
        info.pop('offsets')
        return info
    finally:
        s.close()


def _audio_packets(s, info, track):
    """Yield (frame, packet bytes incl. the leading u32 reported size) for one track."""
    offsets = info['offsets']
    ntracks = len(info['tracks'])
    for fr in range(info['frames']):
        pos, end = offsets[fr], offsets[fr + 1]
        for t in range(ntracks):
            if pos + 4 > end:
                raise BinkError('frame %d: audio size past frame end' % fr)
            asz = struct.unpack('<I', s.read_at(pos, 4))[0]
            pos += 4
            if asz > end - pos:
                raise BinkError('frame %d: audio packet %d past frame end' % (fr, asz))
            if t == track and asz >= 4:
                yield fr, s.read_at(pos, asz)
            pos += asz


# ---------------------------------------------------------------- transforms

_FFT_TW = {}


def _fft(x):
    """Forward-sign-free complex DFT, X[k] = sum x[n] e^{+2 pi i k n / N} (N power of 2)."""
    n = len(x)
    if n == 1:
        return x
    if n == 2:
        a, b = x
        return [a + b, a - b]
    e = _fft(x[0::2])
    o = _fft(x[1::2])
    tw = _FFT_TW.get(n)
    if tw is None:
        tw = _FFT_TW[n] = [cmath.exp(2j * math.pi * k / n) for k in range(n // 2)]
    t = [w * v for w, v in zip(tw, o)]
    return [a + b for a, b in zip(e, t)] + [a - b for a, b in zip(e, t)]


class _DCT3:
    """x[n] = 2/N (X[0]/2 + sum_{k>=1} X[k] cos(pi k (2n+1) / 2N))  (Makhoul, one N-point FFT).
    The 2/N scale is MEASURED against ffmpeg 9.0.2 on Dead Men's Trailer.bik (fit 1/1025.01)."""

    def __init__(self, n):
        self.n = n
        self.pre = [cmath.exp(1j * math.pi * k / (2 * n)) * (2.0 / n) for k in range(n)]
        self.pre[0] *= 0.5

    def __call__(self, c):
        n = self.n
        v = _fft([a * b for a, b in zip(c, self.pre)])
        out = [0.0] * n
        h = n // 2
        re = [z.real for z in v]
        out[0::2] = re[:h]
        out[1::2] = re[n - 1:h - 1:-1]          # x[2m+1] = v[N-1-m]
        return out


class _IRDFT:
    """Real inverse DFT of ffmpeg's packed layout: c[0]=DC, c[1]=Nyquist, c[2k],c[2k+1]=re,im of bin k.
    GUESS (calibrated against ffmpeg only for the DCT path; no RDFT sample on this PC):
    x[n] = c0/2 + (-1)^n c1/2 + sum_k (re cos(2 pi k n/N) + im sin(2 pi k n/N))."""

    def __init__(self, n):
        self.n = n

    def __call__(self, c):
        n = self.n
        h = n // 2
        z = [0j] * n
        z[0] = complex(c[0] * 0.5, 0.0)
        z[h] = complex(c[1] * 0.5, 0.0)
        for k in range(1, h):
            v = complex(c[2 * k], -c[2 * k + 1]) * 0.5
            z[k] = v
            z[n - k] = v.conjugate()
        return [w.real for w in _fft(z)]


# ---------------------------------------------------------------- decoder

class _Decoder:
    def __init__(self, rate, channels, use_dct, version_b):
        if channels < 1 or channels > 2:
            raise BinkError('bad channel count %d' % channels)
        if rate < 1:
            raise BinkError('bad sample rate %d' % rate)
        self.use_dct = use_dct
        self.version_b = version_b
        bits = 9 if rate < 22050 else 10 if rate < 44100 else 11
        if use_dct:
            self.ch = channels
        else:
            # RDFT audio is interleaved: one channel at rate * channels.
            rate *= channels
            self.ch = 1
            if not version_b:
                bits += channels.bit_length() - 1
        self.frame_len = fl = 1 << bits
        self.overlap = fl // 16
        half = (rate + 1) // 2
        if use_dct:
            self.root = fl / (math.sqrt(fl) * 32768.0)
            self.tx = _DCT3(fl)
        else:
            self.root = 2.0 / (math.sqrt(fl) * 32768.0)
            self.tx = _IRDFT(fl)
        self.qtab = [math.exp(i * 0.15289164787221953823) * self.root for i in range(96)]
        nb = 1
        while nb < 25:
            if half <= CRITICAL_FREQS[nb - 1]:
                break
            nb += 1
        self.num_bands = nb
        self.bands = [2] + [(CRITICAL_FREQS[i - 1] * fl // half) & ~1 for i in range(1, nb)] + [fl]
        self.prev = [None] * self.ch
        self.first = True
        self.burst_limit = None
        self.bursts = []                            # (block number, channel, peak)
        self.nblock = 0

    def packet(self, data):
        """Decode one audio packet (with its leading u32) -> list of per-channel float lists."""
        if len(data) < 4:
            raise BinkError('audio packet under 4 bytes')
        nwords = (len(data) + 3) // 4
        words = list(struct.unpack('<%dI' % nwords, data + b'\0' * (4 * nwords - len(data))))
        words += [0, 0, 0]
        total = len(data) * 8
        pos = 32                                    # skip the reported size
        outs = [[] for _ in range(self.ch)]
        fl, ov, ch = self.frame_len, self.overlap, self.ch
        keep = fl - ov
        while True:
            blk, pos = self._block(words, pos, total)
            if self.burst_limit is not None:
                self._fix_bursts(blk)
            self.nblock += 1
            for c in range(ch):
                o = blk[c]
                if not self.first:
                    p = self.prev[c]
                    cnt = ov * ch
                    j = c
                    for i in range(ov):
                        o[i] = (p[i] * (cnt - j) + o[i] * j) / cnt
                        j += ch
                self.prev[c] = o[keep:]
                outs[c].extend(o[:keep])
            self.first = False
            pos += -pos & 31                        # get_bits_align32
            if pos >= total:
                break
        return outs

    def _fix_bursts(self, blk):
        """Replace a channel block whose peak is over burst_limit (x full scale) with the other
        channel's block, or silence. MEASURED: Trailer.bik block 842 left = peak 347270 x full
        scale (ffmpeg decodes the same burst), a 43 ms click at 33.68 s; real audio stays < 2."""
        peaks = [max(max(o), -min(o)) for o in blk]
        lim = self.burst_limit
        for c, p in enumerate(peaks):
            if p > lim:
                self.bursts.append((self.nblock, c, p))
                good = [o for o, q in zip(blk, peaks) if q <= lim]
                blk[c] = list(good[0]) if good else [0.0] * self.frame_len

    def _block(self, w, pos, total):
        def get(n):
            nonlocal pos
            i = pos >> 5
            v = ((w[i] | (w[i + 1] << 32)) >> (pos & 31)) & ((1 << n) - 1)
            pos += n
            return v

        fl, bands, nb, qtab = self.frame_len, self.bands, self.num_bands, self.qtab
        if self.use_dct:
            pos += 2
        blk = []
        for _ in range(self.ch):
            c = [0.0] * fl
            for slot in (0, 1):
                if self.version_b:
                    lo = get(16)
                    c[slot] = struct.unpack('<f', struct.pack('<I', lo | (get(16) << 16)))[0] * self.root
                else:
                    power = get(5)
                    f = math.ldexp(get(23), power - 23)
                    if get(1):
                        f = -f
                    c[slot] = f * self.root
            if total - pos < nb * 8:
                raise BinkError('audio block truncated (bands)')
            quant = [qtab[min(get(8), 95)] for _ in range(nb)]
            k = 0
            q = quant[0]
            i = 2
            vb = self.version_b
            while i < fl:
                if vb:
                    j = i + 16
                elif get(1):
                    j = i + RLE_LENGTHS[get(4)] * 8
                else:
                    j = i + 8
                if j > fl:
                    j = fl
                width = get(4)
                if width == 0:
                    i = j
                    while bands[k] < i:
                        q = quant[k]
                        k += 1
                else:
                    mask = (1 << width) - 1
                    while i < j:
                        if bands[k] == i:
                            q = quant[k]
                            k += 1
                        # inline get(width) + sign bit
                        x = pos >> 5
                        coeff = ((w[x] | (w[x + 1] << 32)) >> (pos & 31)) & mask
                        pos += width
                        if coeff:
                            x = pos >> 5
                            if (w[x] >> (pos & 31)) & 1:
                                c[i] = -q * coeff
                            else:
                                c[i] = q * coeff
                            pos += 1
                        i += 1
                if pos > total + 64:
                    raise BinkError('audio block overran its packet')
            if self.use_dct:
                c[0] /= 0.5
            blk.append(self.tx(c))
        return blk, pos


def _to_s16(chans):
    n = min(len(c) for c in chans)
    out = array.array('h', bytes(2 * n * len(chans)))
    nc = len(chans)
    for ci, c in enumerate(chans):
        out[ci::nc] = array.array('h', [32767 if v >= 32767 else -32768 if v <= -32768 else v
                                         for v in (round(s * 32768.0) for s in c[:n])])
    return out


def bink_audio(src, track=0, start_s=None, end_s=None, burst_limit=None, report=None):
    """Decode one audio track to interleaved int16. start_s/end_s cut in seconds; decoding
    starts one packet before the cut (the overlap needs the previous block) and skips the rest
    by the packets' reported sizes. burst_limit (e.g. 4.0, default off = ffmpeg-faithful):
    repair corrupt blocks, see _Decoder._fix_bursts; report (a list) receives the repairs."""
    s = _Src(src)
    try:
        info = _parse(s)
        if not 0 <= track < len(info['tracks']):
            raise BinkError('no audio track %d (%d tracks)' % (track, len(info['tracks'])))
        t = info['tracks'][track]
        rate, chn = t['rate'], t['channels']
        dec = _Decoder(rate, chn, t['codec'] == 'dct', info['version'] == 'b')
        dec.burst_limit = burst_limit
        if report is not None:
            dec.bursts = report
        first = 0 if start_s is None else max(0, int(round(start_s * rate)))
        last = None if end_s is None else max(first, int(round(end_s * rate)))
        chans = [[] for _ in range(chn)]
        pending = None                          # (pts, packet) just before the cut
        pts = 0                                 # sample position by reported sizes
        out_pts = None                          # sample position of chans[*][0]
        for _fr, pkt in _audio_packets(s, info, track):
            nsamp = struct.unpack_from('<I', pkt)[0] // (2 * chn)
            if last is not None and pts >= last:
                break
            if out_pts is None and pts + nsamp <= first:
                pending = (pts, pkt)
                pts += nsamp
                continue
            if out_pts is None:
                if pending is not None:
                    dec.packet(pending[1])      # warm the overlap, drop its samples
                out_pts = pts
            got = dec.packet(pkt)
            if dec.ch == 1 and chn == 2:        # RDFT: interleaved mono stream
                g = got[0]
                got = [g[0::2], g[1::2]]
            for c in range(chn):
                chans[c].extend(got[c])
            pts += nsamp
        if out_pts is None:
            return array.array('h'), chn, rate
        a = first - out_pts
        b = None if last is None else last - out_pts
        chans = [c[a:b] for c in chans]
        return _to_s16(chans), chn, rate
    finally:
        s.close()


if __name__ == '__main__':
    import sys
    import time
    import wave
    if len(sys.argv) < 3:
        print('usage: kl_pybink.py IN.bik OUT.wav [start_s end_s]')
        sys.exit(2)
    st = float(sys.argv[3]) if len(sys.argv) > 3 else None
    en = float(sys.argv[4]) if len(sys.argv) > 4 else None
    t0 = time.time()
    pcm, ch, rate = bink_audio(sys.argv[1], 0, st, en)
    w = wave.open(sys.argv[2], 'wb')
    w.setnchannels(ch)
    w.setsampwidth(2)
    w.setframerate(rate)
    w.writeframes(pcm.tobytes())
    w.close()
    print('%d frames, %d ch, %d Hz, %.1f s decode' % (len(pcm) // ch, ch, rate, time.time() - t0))
