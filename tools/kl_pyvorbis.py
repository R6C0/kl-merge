"""kl_pyvorbis.py (by session 6b, 11-09) - pure-Python Ogg Vorbis decoder (floor 1, residue 0/1/2, square-polar coupling), written from the
Vorbis I specification for kl_launcher_music.py's no-exe fallback.  vorbis_decode(ogg_bytes, max_frames) ->
(array('h') interleaved, channels, rate).  Raises VorbisError (floor 0 and malformed streams)."""
import array, cmath, math, struct


class VorbisError(Exception):
    pass


class _EOP(Exception):
    pass


def ogg_packets(data):
    """Ogg pages -> the packets of the (single) logical stream, in order."""
    packets, cur, pos, n = [], [], 0, len(data)
    while pos + 27 <= n:
        if data[pos:pos + 4] != b'OggS':
            raise VorbisError('no Ogg page at %#x' % pos)
        nseg = data[pos + 26]
        lace = data[pos + 27:pos + 27 + nseg]
        p = pos + 27 + nseg
        for l in lace:
            cur.append(data[p:p + l])
            p += l
            if l < 255:
                packets.append(b''.join(cur))
                cur = []
        pos = p
    return packets


class _Bits(object):
    """LSB-first bit reader over one packet; past the end reads zeros and sets eop."""
    __slots__ = ('v', 'pos', 'n', 'eop')

    def __init__(self, data):
        self.v = int.from_bytes(data, 'little')
        self.pos = 0
        self.n = 8 * len(data)
        self.eop = False

    def read(self, k):
        if k == 0:
            return 0
        x = (self.v >> self.pos) & ((1 << k) - 1)
        self.pos += k
        if self.pos > self.n:
            self.eop = True
        return x


def _ilog(x):
    return x.bit_length() if x > 0 else 0


def _float32(x):
    m, e = x & 0x1fffff, (x & 0x7fe00000) >> 21
    v = math.ldexp(m, e - 788)
    return -v if x & 0x80000000 else v


class _Book(object):
    __slots__ = ('dims', 'entries', 'table', 'tbits', 'long', 'vq')

    def __init__(self, b):
        if b.read(24) != 0x564342:
            raise VorbisError('bad codebook sync')
        self.dims, self.entries = b.read(16), b.read(24)
        lengths = [0] * self.entries
        if b.read(1):                                               # ordered
            i, cur = 0, b.read(5) + 1
            while i < self.entries:
                num = b.read(_ilog(self.entries - i))
                for j in range(i, min(i + num, self.entries)):
                    lengths[j] = cur
                i += num
                cur += 1
        else:
            sparse = b.read(1)
            for i in range(self.entries):
                if not sparse or b.read(1):
                    lengths[i] = b.read(5) + 1
        # codewords as libvorbis _make_words: lowest free code of each length, entry order, MSB first
        marker, codes = [0] * 33, [0] * self.entries
        for i, l in enumerate(lengths):
            if not l:
                continue
            entry = marker[l]
            codes[i] = entry
            for j in range(l, 0, -1):
                if marker[j] & 1:
                    marker[j] = marker[1] + 1 if j == 1 else marker[j - 1] << 1
                    break
                marker[j] += 1
            for j in range(l + 1, 33):
                if (marker[j] >> 1) == entry:
                    entry = marker[j]
                    marker[j] = marker[j - 1] << 1
                else:
                    break
        # the stream is read LSB first, so a codeword shows up bit-reversed in the peeked bits
        used = [l for l in lengths if l]
        single = len(used) == 1
        self.tbits = min(max(used), 10) if used else 0
        self.table = [None] * (1 << self.tbits)
        self.long = {}
        for i, l in enumerate(lengths):
            if not l:
                continue
            if single:                                              # one entry: decodes from 1 bit, whatever it is
                self.tbits = 1
                self.table = [(i, 1), (i, 1)]
                break
            r = int(format(codes[i], '0%db' % l)[::-1], 2)
            if l <= self.tbits:
                for hi in range(0, 1 << self.tbits, 1 << l):
                    self.table[r | hi] = (i, l)
            else:
                self.long[(l, r)] = i
        self.vq = None
        kind = b.read(4)
        if kind in (1, 2):
            mn, delta = _float32(b.read(32)), _float32(b.read(32))
            vbits, seq = b.read(4) + 1, b.read(1)
            if kind == 1:
                nv = int(math.floor(self.entries ** (1.0 / self.dims))) if self.dims else 0
                while (nv + 1) ** self.dims <= self.entries:
                    nv += 1
                while nv > 0 and nv ** self.dims > self.entries:
                    nv -= 1
            else:
                nv = self.entries * self.dims
            mult = [b.read(vbits) for _ in range(nv)]
            vq = []
            for e in range(self.entries):
                last, vec, div = 0.0, [], 1
                for k in range(self.dims):
                    off = (e // div) % nv if kind == 1 else e * self.dims + k
                    x = mult[off] * delta + mn + last
                    if seq:
                        last = x
                    vec.append(x)
                    div *= nv
                vq.append(vec)
            self.vq = vq
        elif kind:
            raise VorbisError('codebook lookup type %d' % kind)

    def decode(self, b):
        if b.pos >= b.n:
            raise _EOP()
        x = (b.v >> b.pos) & 0xffffffff
        hit = self.table[x & ((1 << self.tbits) - 1)]
        if hit is not None:
            b.pos += hit[1]
            if b.pos > b.n:
                raise _EOP()
            return hit[0]
        for (l, r), i in self.long.items():
            if x & ((1 << l) - 1) == r:
                b.pos += l
                if b.pos > b.n:
                    raise _EOP()
                return i
        raise _EOP()                                                # no codeword matches: treat as end of packet


_FLOOR1_RANGE = (256, 128, 86, 64)
# the spec's floor 1 dB table is this geometric series in float32 (computed here: < 1e-6 relative difference)
_FLOOR1_DB = [1.0649863e-07 * (1.0 / 1.0649863e-07) ** (i / 255.0) for i in range(256)]


def _render_point(x0, y0, x1, y1, x):
    dy, adx = y1 - y0, x1 - x0
    off = abs(dy) * (x - x0) // adx
    return y0 - off if dy < 0 else y0 + off


def _render_line(x0, y0, x1, y1, v, n):
    dy, adx = y1 - y0, x1 - x0
    ady = abs(dy)
    base = ady // adx
    if dy < 0:
        base = -base
    sy = base - 1 if dy < 0 else base + 1
    ady -= abs(base) * adx
    y, err = y0, 0
    if x0 < n:
        v[x0] = y
    for xx in range(x0 + 1, min(x1, n)):
        err += ady
        if err >= adx:
            err -= adx
            y += sy
        else:
            y += base
        v[xx] = y


class _Floor1(object):
    def __init__(self, b):
        parts = b.read(5)
        self.pclass = [b.read(4) for _ in range(parts)]
        ncls = max(self.pclass) + 1 if self.pclass else 0
        self.cdim, self.csub, self.cmaster, self.cbooks = [], [], [], []
        for _ in range(ncls):
            self.cdim.append(b.read(3) + 1)
            sub = b.read(2)
            self.csub.append(sub)
            self.cmaster.append(b.read(8) if sub else -1)
            self.cbooks.append([b.read(8) - 1 for _ in range(1 << sub)])
        self.mult = b.read(2) + 1
        rb = b.read(4)
        self.x = [0, 1 << rb]
        for c in self.pclass:
            for _ in range(self.cdim[c]):
                self.x.append(b.read(rb))
        n = len(self.x)
        self.lo, self.hi = [0] * n, [0] * n
        for i in range(2, n):
            lo = hi = None
            for j in range(i):
                if self.x[j] < self.x[i] and (lo is None or self.x[j] > self.x[lo]):
                    lo = j
                if self.x[j] > self.x[i] and (hi is None or self.x[j] < self.x[hi]):
                    hi = j
            self.lo[i], self.hi[i] = lo, hi
        self.order = sorted(range(n), key=lambda i: self.x[i])

    def read(self, b, books):
        """-> Y list, or None when the channel's floor is unused in this packet."""
        if not b.read(1):
            return None
        bits = _ilog(_FLOOR1_RANGE[self.mult - 1] - 1)
        y = [b.read(bits), b.read(bits)]
        for c in self.pclass:
            cbits = self.csub[c]
            cval = books[self.cmaster[c]].decode(b) if cbits else 0
            for _ in range(self.cdim[c]):
                book = self.cbooks[c][cval & ((1 << cbits) - 1)]
                cval >>= cbits
                y.append(books[book].decode(b) if book >= 0 else 0)
        return y

    def curve(self, y, n2):
        rng = _FLOOR1_RANGE[self.mult - 1]
        x = self.x
        cnt = len(x)
        fy, step = [0] * cnt, [False] * cnt
        fy[0], fy[1] = y[0], y[1]
        step[0] = step[1] = True
        for i in range(2, cnt):
            lo, hi = self.lo[i], self.hi[i]
            pred = _render_point(x[lo], fy[lo], x[hi], fy[hi], x[i])
            val = y[i]
            hroom, lroom = rng - pred, pred
            room = (hroom if hroom < lroom else lroom) * 2
            if val:
                step[lo] = step[hi] = step[i] = True
                if val >= room:
                    fy[i] = val - lroom + pred if hroom > lroom else pred - val + hroom - 1
                else:
                    fy[i] = pred - ((val + 1) >> 1) if val & 1 else pred + (val >> 1)
            else:
                fy[i] = pred
        out = [0] * n2
        m = self.mult
        o = self.order
        lx, ly = 0, fy[o[0]] * m
        hx = hy = 0
        for i in o[1:]:
            if step[i]:
                hy, hx = fy[i] * m, x[i]
                _render_line(lx, ly, hx, hy, out, n2)
                lx, ly = hx, hy
        if hx < n2:
            _render_line(hx, hy, n2, hy, out, n2)
        db = _FLOOR1_DB
        return [db[v if 0 <= v < 256 else (0 if v < 0 else 255)] for v in out]


class _Residue(object):
    def __init__(self, b, kind):
        self.kind = kind
        self.begin, self.end = b.read(24), b.read(24)
        self.psize, self.ncls, self.cbook = b.read(24) + 1, b.read(6) + 1, b.read(8)
        casc = []
        for _ in range(self.ncls):
            low, hi = b.read(3), 0
            if b.read(1):
                hi = b.read(5)
            casc.append(hi * 8 + low)
        self.books = [[b.read(8) if c & (1 << j) else -1 for j in range(8)] for c in casc]

    def decode(self, b, books, vecs, skip, n2):
        if self.kind == 2:
            if all(skip):
                return
            ch = len(vecs)
            flat = [0.0] * (n2 * ch)
            self._decode(b, books, [flat], [False], n2 * ch, 1)
            for c in range(ch):
                vecs[c][:] = flat[c::ch]
            return
        self._decode(b, books, vecs, skip, n2, self.kind)

    def _decode(self, b, books, vecs, skip, size, fmt):
        lb, le = min(self.begin, size), min(self.end, size)
        ps = self.psize
        nparts = (le - lb) // ps
        if nparts <= 0:
            return
        cb = books[self.cbook]
        cw, ncls = cb.dims, self.ncls
        cls = [[0] * (nparts + cw) for _ in vecs]
        try:
            for pas in range(8):
                p = 0
                while p < nparts:
                    if pas == 0:
                        for j in range(len(vecs)):
                            if skip[j]:
                                continue
                            t = cb.decode(b)
                            for i in range(cw - 1, -1, -1):
                                cls[j][p + i] = t % ncls
                                t //= ncls
                    for _ in range(cw):
                        if p >= nparts:
                            break
                        for j, vec in enumerate(vecs):
                            if skip[j]:
                                continue
                            bk = self.books[cls[j][p]][pas]
                            if bk < 0:
                                continue
                            book = books[bk]
                            vq, dims = book.vq, book.dims
                            off = lb + p * ps
                            if fmt == 0:
                                stepn = ps // dims
                                for i in range(stepn):
                                    e = vq[book.decode(b)]
                                    for k in range(dims):
                                        vec[off + i + k * stepn] += e[k]
                            else:
                                i = 0
                                while i < ps:
                                    e = vq[book.decode(b)]
                                    for k in range(dims):
                                        vec[off + i] += e[k]
                                        i += 1
                        p += 1
        except _EOP:
            pass


_FFT_CACHE = {}


def _fft(a):
    n = len(a)
    plan = _FFT_CACHE.get(n)
    if plan is None:
        rev, j = list(range(n)), 0
        for i in range(1, n):
            bit = n >> 1
            while j & bit:
                j ^= bit
                bit >>= 1
            j |= bit
            rev[i] = j
        stages, m = [], 2
        while m <= n:
            stages.append((m, m // 2, [cmath.exp(-2j * math.pi * k / m) for k in range(m // 2)]))
            m *= 2
        plan = _FFT_CACHE[n] = (rev, stages)
    rev, stages = plan
    a = [a[r] for r in rev]
    for m, h, tw in stages:
        for s in range(0, n, m):
            for k in range(h):
                u = a[s + k]
                t = a[s + k + h] * tw[k]
                a[s + k] = u + t
                a[s + k + h] = u - t
    return a


_IMDCT_CACHE = {}


def imdct(X):
    """y[i] = sum_k X[k] cos(2 pi / n (i + 1/2 + N/2)(k + 1/2)), n = 2N, via a DCT-IV on an N/2-point FFT."""
    N = len(X)
    H = N // 2
    tw = _IMDCT_CACHE.get(N)
    if tw is None:
        tw = _IMDCT_CACHE[N] = ([cmath.exp(-1j * math.pi * (4 * k + 1) / (4 * N)) for k in range(H)],
                                [cmath.exp(-1j * math.pi * k / N) for k in range(H)])
    pre, post = tw
    Z = _fft([complex(X[2 * k], X[N - 1 - 2 * k]) * pre[k] for k in range(H)])
    u = [0.0] * N
    for j in range(H):
        t = Z[j] * post[j]
        u[2 * j] = t.real
        u[N - 1 - 2 * j] = -t.imag
    return u[H:] + [-x for x in reversed(u)] + [-x for x in u[:H]]


def _window(n, left, right):
    w = [0.0] * n
    ls = n // 4 - left // 2
    rs = 3 * n // 4 - right // 2
    for i in range(left):
        w[ls + i] = math.sin(math.pi / 2 * math.sin((i + 0.5) / left * math.pi / 2) ** 2)
    for i in range(ls + left, rs):
        w[i] = 1.0
    for i in range(right):
        w[rs + i] = math.sin(math.pi / 2 * math.sin((i + 0.5) / right * math.pi / 2 + math.pi / 2) ** 2)
    return w, ls, ls + left, rs, rs + right


def vorbis_decode(data, max_frames):
    pk = ogg_packets(data)
    if len(pk) < 3 or pk[0][:7] != b'\x01vorbis' or pk[2][:7] != b'\x05vorbis':
        raise VorbisError('no identification / setup header')
    ch, rate = pk[0][11], struct.unpack_from('<I', pk[0], 12)[0]
    bs = (1 << (pk[0][28] & 15), 1 << (pk[0][28] >> 4))
    last = data.rfind(b'OggS')
    total = struct.unpack_from('<q', data, last + 6)[0] if last >= 0 else -1      # granule of the last page
    b = _Bits(pk[2][7:])
    books = [_Book(b) for _ in range(b.read(8) + 1)]
    for _ in range(b.read(6) + 1):
        b.read(16)
    floors = []
    for _ in range(b.read(6) + 1):
        if b.read(16) != 1:
            raise VorbisError('floor 0 (not decoded here)')
        floors.append(_Floor1(b))
    residues = []
    for _ in range(b.read(6) + 1):
        kind = b.read(16)
        if kind > 2:
            raise VorbisError('residue type %d' % kind)
        residues.append(_Residue(b, kind))
    mappings = []
    for _ in range(b.read(6) + 1):
        if b.read(16) != 0:
            raise VorbisError('mapping type')
        subs = b.read(4) + 1 if b.read(1) else 1
        coup = []
        if b.read(1):
            for _ in range(b.read(8) + 1):
                coup.append((b.read(_ilog(ch - 1)), b.read(_ilog(ch - 1))))
        b.read(2)
        mux = [b.read(4) for _ in range(ch)] if subs > 1 else [0] * ch
        sm = []
        for _ in range(subs):
            b.read(8)
            sm.append((b.read(8), b.read(8)))
        mappings.append((coup, mux, sm))
    modes = []
    for _ in range(b.read(6) + 1):
        flag = b.read(1)
        b.read(32)
        modes.append((flag, b.read(8)))
    if b.eop:
        raise VorbisError('setup header cut short')
    mbits = _ilog(len(modes) - 1)
    out = array.array('h')
    want = max_frames * ch
    lim = min(want, total * ch) if total >= 0 else want
    prev, first, wcache = None, True, {}
    for p in pk[3:]:
        b = _Bits(p)
        if b.read(1):
            continue
        flag, mapn = modes[b.read(mbits)]
        n = bs[flag]
        if flag:
            pw, nw = b.read(1), b.read(1)
            left = n // 2 if pw else bs[0] // 2
            right = n // 2 if nw else bs[0] // 2
        else:
            left = right = n // 2
        key = (n, left, right)
        if key not in wcache:
            wcache[key] = _window(n, left, right)
        w, lws, lwe, rws, rwe = wcache[key]
        n2 = n // 2
        coup, mux, sm = mappings[mapn]
        fl = [None] * ch
        try:
            for c in range(ch):
                fl[c] = floors[sm[mux[c]][0]].read(b, books)
        except _EOP:
            pass
        used = [f is not None for f in fl]
        for m, a in coup:
            if used[m] or used[a]:
                used[m] = used[a] = True
        vecs = [[0.0] * n2 for _ in range(ch)]
        for si, (_, resn) in enumerate(sm):
            cs = [c for c in range(ch) if mux[c] == si]
            residues[resn].decode(b, books, [vecs[c] for c in cs], [not used[c] for c in cs], n2)
        for m, a in reversed(coup):
            M, A = vecs[m], vecs[a]
            for j in range(n2):
                mv, av = M[j], A[j]
                if mv > 0:
                    if av > 0:
                        M[j], A[j] = mv, mv - av
                    else:
                        M[j], A[j] = mv + av, mv
                else:
                    if av > 0:
                        M[j], A[j] = mv, mv + av
                    else:
                        M[j], A[j] = mv - av, mv
        cur = []
        for c in range(ch):
            if fl[c] is None:
                cur.append([0.0] * n)
                continue
            curve = floors[sm[mux[c]][0]].curve(fl[c], n2)
            spec = vecs[c]
            y = imdct([spec[j] * curve[j] for j in range(n2)])
            cur.append([y[i] * w[i] for i in range(n)])
        # output = previous right slope + this left slope, then the flat middle; the first block from its centre
        if first:
            seg = [cur[c][n2:rws] for c in range(ch)]
            first = False
        else:
            seg = []
            for c in range(ch):
                pr, cc = prev[c], cur[c]
                seg.append([pr[i] + cc[lws + i] for i in range(lwe - lws)] + cc[lwe:rws])
        prev = [cur[c][rws:rwe] for c in range(ch)]
        for i in range(len(seg[0])):
            for c in range(ch):
                v = int(round(seg[c][i] * 32768.0))
                out.append(32767 if v > 32767 else -32768 if v < -32768 else v)
        if len(out) >= lim:
            break
    del out[lim:]
    return out, ch, rate


if __name__ == '__main__':
    import sys, time, wave
    t = time.time()
    s, ch, rate = vorbis_decode(open(sys.argv[1], 'rb').read(), 10 ** 9)
    with wave.open(sys.argv[2], 'wb') as wf:
        wf.setnchannels(ch)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(s.tobytes())
    print('%d frames, %d ch, %d Hz, %.1f s decode' % (len(s) // ch, ch, rate, time.time() - t))
