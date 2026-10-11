"""Glacier 1 (K&L DM / DD) animation track codec - decoder only (used for verification/analysis).
Reverse-engineered from DM 0x5bdbd0 (IdxT) / 0x5bdd30 (rotation) and DD 0x6663b0 / 0x834170."""
import struct, math

def _bits(buf, pos, n):
    """read n bits (n<=25) at bit position pos, LSB-first, as the engine does (32-bit little-endian window)."""
    o = pos >> 3
    w = int.from_bytes(buf[o:o + 4].ljust(4, b'\0'), 'little')
    return (w >> (pos & 7)) & ((1 << n) - 1)

def idxt_header(buf, off=0):
    """'IdxT' key-frame index stream. returns (bitsPerFrame, keyCount, lowbits)."""
    assert buf[off:off + 4] == b'IdxT', buf[off:off + 4]
    w = struct.unpack_from('<I', buf, off + 4)[0]
    return (w >> 2) & 0xf, (w >> 6) & 0xffff, w & 3

def idxt_frames(buf, off=0):
    b, k, _ = idxt_header(buf, off)
    base = off * 8 + 0x36
    return [_bits(buf, base + i * b, b) for i in range(k)]

def idxt_size(buf, off=0):
    b, k, _ = idxt_header(buf, off)
    return (0x36 + b * k + 7) // 8

def rot_decode_all(buf, off, nkeys):
    """decode all rotation keys of a rotation stream -> list of quaternions (x,y,z,w)
    component order as stored by the engine in its 4-float output (index 0..3)."""
    h = buf[off]
    L = h & 3; const = (h >> 2) & 1; bits = (h >> 3) & 0x1f
    out = []
    if bits == 31:  # raw floats, 16 bytes per key starting at off+4
        for i in range(nkeys):
            out.append(struct.unpack_from('<4f', buf, off + 4 + 16 * i))
        return out
    pos = off * 8 + 8
    def sx(v, n):
        return v - (1 << n) if v & (1 << (n - 1)) else v
    mins = []
    for _ in range(3):
        mins.append(sx(_bits(buf, pos, bits), bits)); pos += bits
    scale = 1.0 / ((1 << (bits - 1)) - 1)
    others = [i for i in range(4) if i != L]
    def build(s, sign):
        q = [0.0] * 4
        for k, i in enumerate(others): q[i] = s[k]
        ss = min(1.0, s[0] * s[0] + s[1] * s[1] + s[2] * s[2])
        q[L] = math.sqrt(1.0 - ss) * (-1.0 if sign else 1.0)
        return tuple(q)
    if const:
        s = [m * scale for m in mins]
        sign = _bits(buf, pos, 1)
        return [build(s, sign)] * max(nkeys, 1)
    n0 = _bits(buf, pos, 5); n1 = _bits(buf, pos + 5, 5); n2 = _bits(buf, pos + 10, 5); pos += 15
    rec = n0 + n1 + n2 + 1
    for i in range(nkeys):
        p = pos + rec * i
        sign = _bits(buf, p, 1); p += 1
        d0 = _bits(buf, p, n0) if n0 else 0; p += n0
        d1 = _bits(buf, p, n1) if n1 else 0; p += n1
        d2 = _bits(buf, p, n2) if n2 else 0
        out.append(build([(mins[0] + d0) * scale, (mins[1] + d1) * scale, (mins[2] + d2) * scale], sign))
    return out

def rot_stream_size(buf, off, nkeys):
    h = buf[off]; const = (h >> 2) & 1; bits = (h >> 3) & 0x1f
    if bits == 31: return 4 + 16 * nkeys
    nb = 8 + 3 * bits
    if const: nb += 1
    else:
        n0 = _bits(buf, off * 8 + nb, 5); n1 = _bits(buf, off * 8 + nb + 5, 5); n2 = _bits(buf, off * 8 + nb + 10, 5)
        nb += 15 + (n0 + n1 + n2 + 1) * nkeys
    return (nb + 7) // 8
