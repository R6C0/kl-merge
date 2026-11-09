"""Self-test for kl_pybink (no game file): synthetic Bink 1 files built here.
python tools/kl_pybink_test.py -> PASS/FAIL lines, exit 1 on a FAIL."""
import array
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_pybink as kb  # noqa: E402

FAILS = []
CHECKS = [0]


def check(ok, what):
    CHECKS[0] += 1
    if not ok:
        FAILS.append(what)
        print('FAIL', what)


class BitWriter:
    """LSB-first, like the decoder's reader."""

    def __init__(self):
        self.v = 0
        self.n = 0

    def put(self, val, bits):
        self.v |= (val & ((1 << bits) - 1)) << self.n
        self.n += bits

    def align32(self):
        self.n += -self.n & 31

    def bytes(self):
        return self.v.to_bytes((self.n + 7) // 8, 'little')


def put_float(bw, f):
    """Inverse of get_float: power 5 bits, mantissa 23, sign 1."""
    sign = f < 0
    f = abs(f)
    power = 0
    if f:
        _m, e = math.frexp(f)              # f < 2^e, so mantissa f * 2^(23-e) < 2^23
        power = max(0, min(31, e))
    mant = int(round(f * 2.0 ** (23 - power)))
    mant = min(mant, (1 << 23) - 1)
    bw.put(power, 5)
    bw.put(mant, 23)
    bw.put(1 if sign else 0, 1)


def encode_block(bw, dec, coeffs_per_ch, dct=True):
    """Encode one block: per channel 2 floats + band quant 0 + RLE runs of width 15 with a
    coefficient list (ints, applied with quant[0]) for i >= 2."""
    if dct:
        bw.put(0, 2)
    for co in coeffs_per_ch:
        put_float(bw, co[0])
        put_float(bw, co[1])
        for _ in range(dec.num_bands):
            bw.put(0, 8)                       # quant index 0 -> qtab[0] = root
        i = 2
        while i < dec.frame_len:
            j = min(i + 8, dec.frame_len)
            bw.put(0, 1)                       # no RLE flag -> 8 coefficients
            run = co[i:j]
            if not any(run):
                bw.put(0, 4)
            else:
                bw.put(15, 4)
                for c in run:
                    bw.put(abs(c), 15)
                    if c:
                        bw.put(1 if c < 0 else 0, 1)
            i = j


def make_bik(packets, rate=22050, flags=kb.FLAG_DCT | kb.FLAG_16BITS, ver=b'i', video=b'VV'):
    """Bink 1 file: one audio track, one frame per packet, a fake video payload per frame."""
    frames = len(packets)
    head_len = 44 + 4 + 4 + 4 + 4 * (frames + 1)
    body = b''
    offs = []
    for p in packets:
        offs.append(head_len + len(body))
        body += struct.pack('<I', len(p)) + p + video
    offs.append(head_len + len(body))
    head = b'BIK' + ver + struct.pack('<10I', head_len + len(body) - 8, frames, 0, frames, 64, 32,
                                      30, 1, 0, 1)
    head += struct.pack('<I', 0) + struct.pack('<HH', rate, flags) + struct.pack('<I', 0)
    head += struct.pack('<%dI' % (frames + 1), *[o | (1 if k == 0 else 0) for k, o in enumerate(offs)])
    assert len(head) == head_len
    return head + body


def packet(dec, blocks, reported):
    bw = BitWriter()
    bw.put(reported, 32)
    for b in blocks:
        encode_block(bw, dec, b)
        bw.align32()
    return bw.bytes()


def main():
    # --- decoder setup numbers (ffmpeg binkaudio.c init)
    d = kb._Decoder(48000, 2, True, False)
    check(d.frame_len == 2048 and d.overlap == 128, '48k dct frame 2048 / overlap 128')
    check(d.num_bands == 25 and d.bands[0] == 2 and d.bands[-1] == 2048, '48k bands 25')
    check(d.bands[1] == (100 * 2048 // 24000) & ~1, 'band 1 edge')
    d2 = kb._Decoder(22050, 1, True, False)
    check(d2.frame_len == 1024, '22.05k frame 1024')
    d3 = kb._Decoder(44100, 2, False, False)
    check(d3.frame_len == 4096 and d3.ch == 1, 'rdft stereo = interleaved mono, frame 4096')
    d4 = kb._Decoder(44100, 2, False, True)
    check(d4.frame_len == 2048, 'rdft version b keeps 2048')

    # --- DCT-III against the direct sum
    n = 64
    tx = kb._DCT3(n)
    X = [math.sin(k * 0.7) * (1 + k % 5) for k in range(n)]
    got = tx(X)
    want = [2.0 / n * (X[0] / 2 + sum(X[k] * math.cos(math.pi * k * (2 * m + 1) / (2 * n))
                                      for k in range(1, n))) for m in range(n)]
    check(max(abs(a - b) for a, b in zip(got, want)) < 1e-9, 'DCT-III matches the direct sum')

    # --- bit reader round trip through a synthetic file
    dec = kb._Decoder(22050, 1, True, False)
    fl = dec.frame_len
    keep = fl - dec.overlap
    coeffs = [0] * fl
    coeffs[2] = 3000
    coeffs[9] = -1200
    coeffs[40] = 77
    blocks = [[[0.0, 0.0] + coeffs[2:]]]
    p1 = packet(dec, [[[0.5, 0.0] + coeffs[2:]], [[0.0, -0.25] + coeffs[2:]]], keep * 2 * 2)
    p2 = packet(dec, blocks, keep * 2)
    bik = make_bik([p1, p2])
    info = kb.bink_info(bik)
    check(info['frames'] == 2 and info['version'] == 'i', 'header frames/version')
    check(info['tracks'] == [{'rate': 22050, 'flags': kb.FLAG_DCT | kb.FLAG_16BITS, 'id': 0,
                              'channels': 1, 'codec': 'dct'}], 'track header')
    pcm, ch, rate = kb.bink_audio(bik)
    check((ch, rate) == (1, 22050), 'mono 22050')
    check(len(pcm) == 3 * keep, 'sample count = blocks x (frame - overlap): %d' % len(pcm))

    # expected first block: direct DCT of the dequantised coefficients
    q = dec.root                               # quant index 0
    c = [0.5 * dec.root, 0.0] + [v * q for v in coeffs[2:]]
    c[0] /= 0.5
    ref = kb._DCT3(fl)(c)
    exp0 = [max(-32768, min(32767, round(v * 32768))) for v in ref[:keep]]
    check(list(pcm[:keep]) == exp0, 'block 1 decodes to the direct DCT')
    check(any(pcm[:keep]), 'block 1 not silent')

    # cut: start inside packet 2 equals the tail of the full decode
    full = list(pcm)
    st = (2 * keep + 100) / 22050.0
    cut, _, _ = kb.bink_audio(bik, 0, st, None)
    check(list(cut) == full[2 * keep + 100:], 'cut by start_s matches the full decode')
    cut2, _, _ = kb.bink_audio(bik, 0, 0, keep / 22050.0)
    check(list(cut2) == full[:keep], 'cut by end_s')

    # burst repair: a block far over full scale gets replaced by silence (mono)
    big = [0] * fl
    big[3] = 32767
    pb = packet(dec, [[[2.0e9, 0.0] + big[2:]]], keep * 2)
    bik2 = make_bik([pb])
    rep = []
    pcm2, _, _ = kb.bink_audio(bik2, burst_limit=4.0, report=rep)
    check(len(rep) == 1 and rep[0][0] == 0 and rep[0][1] == 0, 'burst found: %r' % rep[:1])
    check(not any(pcm2), 'burst repaired to silence on mono')
    pcm3, _, _ = kb.bink_audio(bik2)
    check(max(abs(v) for v in pcm3) >= 32767, 'burst kept (clipped) without burst_limit')

    # --- errors
    for bad, what in ((b'XXXX' + bik[4:], 'signature'), (bik[:3] + b'z' + bik[4:], 'version'),
                      (bik[:60], 'truncated index'),
                      (bik[:-10], 'truncated frame')):
        try:
            kb.bink_audio(bad)
            check(False, 'BinkError on bad ' + what)
        except kb.BinkError:
            check(True, what)
    try:
        kb.bink_audio(bik, track=1)
        check(False, 'BinkError on missing track')
    except kb.BinkError:
        check(True, 'track')

    print('RESULT: %s (%d checks, %d failed)' % ('FAIL' if FAILS else 'PASS', CHECKS[0], len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
