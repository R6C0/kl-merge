#!/usr/bin/env python3
r"""
KL Merge release tool (Nexus package): patch maker + installer for the mod's files.

    kl_release.py make <outdir> [--dd <DD>] [--dm <DM>] [--pd2 <PD2>] [--only DM03,DD10,core,stream,stockwav,audio,overlay]
                                [--workers N] [--keep-going]
    kl_release.py install   <DD folder> [--dm <folder>] [--pd2 <folder>] [--pkg <package folder>] [--only ...] [--yes]
    kl_release.py uninstall <DD folder> [--yes]
    kl_release.py verify    <DD folder> [--pkg <package folder>] [--only ...]
    (no arguments: console menu Install / Uninstall / Verify)

WHAT SHIPS: only our own code and config (dinput8.dll = KLHook, the KL*.ini files) as plain bytes, and PATCHES (.klp)
whose source is the player's own stock Dog Days / Dead Men / Payday 2 files. A patch is a list of "copy N bytes from the
source pool at offset X" operations plus the literal bytes that exist in no source (zstd compressed). Map archives
(.zip) are rebuilt member by member: the zip's own headers ("skeleton", metadata only) are stored, each member's bytes
are patched, then deflated again with the zlib level that reproduces the live archive byte for byte (checked when the
package is made; members that no level reproduces are stored as raw deflate streams in the patch).
Everything is sha1-checked: sources before anything is written, every output before it replaces a file.

Stock files that the mod replaces are MOVED to <DD>\KL_PortBackup\ (never deleted, never overwritten). The journal
<DD>\KLMergeInstall.json lets `uninstall` put everything back. Steam launch options are never touched.

The installer half uses only the standard library + zstandard (frozen into KLMergeSetup.exe). The maker half also
needs numpy.
"""
import os, sys, io, json, struct, zlib, hashlib, time, shutil, zipfile, mmap, re, bisect, ctypes, traceback, argparse

try:
    import zstandard as zstd
except ImportError:                                  # pragma: no cover
    zstd = None

VERSION = '1.0.0'
MAGIC = b'KLP1'
CREDITS = 'KL Merge - made in contribution with luvsic'
STOCK_KL2_SHA1 = '9d99e01d57f3cef404e1269851d67cb971335e4c'
BACKUP = 'KL_PortBackup'
JOURNAL = 'KLMergeInstall.json'
TMPDIR = 'KLMergeTmp'


# ---------------------------------------------------------------- small helpers
def low_priority():
    try:
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)   # BELOW_NORMAL
    except Exception:
        pass


def sha1_file(path, with_md5=False, block=1 << 24):
    h = hashlib.sha1(); m = hashlib.md5() if with_md5 else None
    with open(path, 'rb') as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
            if m:
                m.update(b)
    return (h.hexdigest(), m.hexdigest()) if with_md5 else h.hexdigest()


def put_varint(out, v):
    while v >= 0x80:
        out.append((v & 0x7f) | 0x80)
        v >>= 7
    out.append(v)


def zig(v):
    return (v << 1) if v >= 0 else ((-v << 1) - 1)


def unzig(u):
    return (u >> 1) if not (u & 1) else -((u + 1) >> 1)


def varints(data):
    """generator over the varints of a bytes-like"""
    mv = memoryview(data); i = 0; n = len(mv)
    while i < n:
        v = 0; s = 0
        while True:
            b = mv[i]; i += 1
            v |= (b & 0x7f) << s
            if b < 0x80:
                break
            s += 7
        yield v


def zc(level=19, threads=0):
    p = zstd.ZstdCompressionParameters.from_level(level, window_log=27, enable_ldm=(level >= 15), threads=threads)
    return zstd.ZstdCompressor(compression_params=p)


def zdecomp(b, size=None):
    d = zstd.ZstdDecompressor()
    return d.decompress(b, max_output_size=size or (1 << 31))


def fmt(n):
    for u in ('B', 'KB', 'MB', 'GB'):
        if n < 1024 or u == 'GB':
            return '%.1f %s' % (n, u) if u != 'B' else '%d B' % n
        n /= 1024.0


# ---------------------------------------------------------------- pool of source pieces
class Pool:
    """Concatenation (virtual address space) of source pieces. A piece is a whole file (mmap) or a zip member
    (decompressed, or raw deflate payload when ref kind is 'raw'). loader(ref, member) -> buffer."""
    def __init__(self, loader, cap=1_500_000_000):
        self.loader = loader; self.pieces = []; self.starts = []; self.total = 0
        self.cache = {}; self.order = []; self.cap = cap; self.held = 0

    def add(self, ref, member, size):
        self.pieces.append((ref, member, size, self.total)); self.starts.append(self.total); self.total += size

    def buf(self, i):
        b = self.cache.get(i)
        if b is None:
            ref, member, size, _ = self.pieces[i]
            b = self.loader(ref, member)
            if len(b) != size:
                raise ValueError('source piece %s %s has %d bytes, the package expects %d' % (ref, member or '', len(b), size))
            if size < self.cap:
                while self.held + size > self.cap and self.order:
                    j = self.order.pop(0); self.held -= len(self.cache.pop(j))
                self.cache[i] = b; self.order.append(i); self.held += size
        return b

    def locate(self, g):
        return bisect.bisect_right(self.starts, g) - 1

    def read(self, g, n):
        out = []
        while n > 0:
            i = self.locate(g); b = self.buf(i); o = g - self.pieces[i][3]; k = min(n, len(b) - o)
            if k <= 0:
                raise ValueError('copy beyond the source pool')
            out.append(bytes(b[o:o + k])); g += k; n -= k
        return out[0] if len(out) == 1 else b''.join(out)


# ---------------------------------------------------------------- patch encode (maker only: numpy)
MINMATCH = 24


def _np():
    import numpy as np
    return np


def anchors(buf, bits):
    """content defined 8 byte anchors: (keys uint64, positions int64) of the positions whose hashed word has `bits`
    leading zero bits (density 1/2**bits)."""
    np = _np()
    n = len(buf)
    if n < 8:
        return np.empty(0, np.uint64), np.empty(0, np.int64)
    arr = np.frombuffer(buf, dtype=np.uint8)
    C = np.uint64(0x9E3779B97F4A7C15); sh = np.uint64(64 - bits)
    ks = []; ps = []; CH = 1 << 23
    for s in range(0, n - 7, CH):
        e = min(s + CH, n - 7)
        seg = arr[s:e + 7]
        w = np.ndarray(shape=(e - s,), dtype='<u8', buffer=seg, offset=0, strides=(1,))
        h = w * C
        sel = np.flatnonzero((h >> sh) == 0)
        if len(sel):
            ks.append(h[sel]); ps.append(sel.astype(np.int64) + s)
    if not ks:
        return np.empty(0, np.uint64), np.empty(0, np.int64)
    return np.concatenate(ks), np.concatenate(ps)


def common_prefix(a, ai, b, bi, n):
    np = _np()
    k = 0; step = 256
    while k < n:
        m = min(step, n - k)
        x = a[ai + k:ai + k + m]; y = b[bi + k:bi + k + m]
        if x == y:
            k += m; step = min(step * 2, 1 << 20)
        else:
            xa = np.frombuffer(x, np.uint8); ya = np.frombuffer(y, np.uint8)
            return k + int(np.argmax(xa != ya))
    return n


def common_suffix(a, ai, b, bi, n):
    """how many bytes before a[ai] / b[bi] are equal (at most n)"""
    np = _np()
    k = 0; step = 256
    while k < n:
        m = min(step, n - k)
        x = a[ai - k - m:ai - k]; y = b[bi - k - m:bi - k]
        if x == y:
            k += m; step = min(step * 2, 1 << 20)
        else:
            xa = np.frombuffer(x, np.uint8)[::-1]; ya = np.frombuffer(y, np.uint8)[::-1]
            return k + int(np.argmax(xa != ya))
    return n


class PoolIndex:
    def __init__(self, pool, bits, anchor_cache=None, cache_refs=(), only=None):
        np = _np()
        self.pool = pool; self.bits = bits
        ks = []; ps = []
        for i, (ref, member, size, start) in enumerate(pool.pieces):
            if only is not None and i not in only:
                continue
            key = (ref, member, bits)
            ent = anchor_cache.get(key) if anchor_cache is not None else None
            if ent is None:
                ent = anchors(pool.buf(i), bits)
                if anchor_cache is not None and ref in cache_refs:
                    anchor_cache[key] = ent
            k, p = ent
            if len(k):
                ks.append(k); ps.append(p + start)
        if ks:
            keys = np.concatenate(ks); pos = np.concatenate(ps)
            order = np.argsort(keys, kind='stable')
            keys = keys[order]; pos = pos[order]
            u, idx = np.unique(keys, return_index=True)
            self.keys = u; self.pos = pos[idx]
        else:
            self.keys = np.empty(0, np.uint64); self.pos = np.empty(0, np.int64)

    def find_ops(self, T):
        """-> list of (tgt_off, length, src_global)"""
        np = _np()
        if len(T) < 16 or not len(self.keys):
            return []
        tk, tp = anchors(T, self.bits)
        if not len(tk):
            return []
        i = np.searchsorted(self.keys, tk)
        i[i >= len(self.keys)] = len(self.keys) - 1
        ok = self.keys[i] == tk
        hq = tp[ok]; hs = self.pos[i[ok]]
        pool = self.pool; nT = len(T)
        if not len(hq):
            return []
        starts = np.array(pool.starts, dtype=np.int64)
        pidx = np.searchsorted(starts, hs, side='right') - 1
        order = np.lexsort((hq, pidx))                 # by source piece, then target position: each piece is loaded once
        hq = hq[order].tolist(); hs = hs[order].tolist(); pidx = pidx[order].tolist()
        cands = []
        k = 0; nh = len(hq)
        while k < nh:
            pi = pidx[k]
            pb = pool.buf(pi); pstart = pool.pieces[pi][3]; pend = pstart + len(pb)
            covered = 0
            while k < nh and pidx[k] == pi:
                t = hq[k]; s = hs[k]; k += 1
                if t < covered:
                    continue
                lo = s - pstart
                f = common_prefix(T, t, pb, lo, min(nT - t, pend - s))
                if f < 8:
                    continue
                b = common_suffix(T, t, pb, lo, min(t, lo)) if min(t, lo) > 0 else 0
                if f + b >= MINMATCH:
                    cands.append((t - b, f + b, s - b)); covered = t + f
        cands.sort()
        ops = []; covered = 0
        for (t, ln, s) in cands:
            if t < covered:
                cut = covered - t
                t += cut; s += cut; ln -= cut
            if ln >= MINMATCH:
                ops.append((t, ln, s)); covered = t + ln
        return ops


def encode_unit(T, idx, whole_hint=None):
    """target bytes T against the pool index -> (ops_bytes, literal_bytes, nops, copied)"""
    ops = idx.find_ops(T) if idx is not None else []
    ob = bytearray(); lits = []; pos = 0; exp = 0; copied = 0
    for (t, ln, s) in ops:
        put_varint(ob, t - pos)                 # literal bytes before
        put_varint(ob, ln)
        put_varint(ob, zig(s - exp))
        if t > pos:
            lits.append(bytes(T[pos:t]))
        pos = t + ln; exp = s + ln; copied += ln
    if pos < len(T):
        lits.append(bytes(T[pos:]))
    return bytes(ob), b''.join(lits), len(ops), copied


def apply_unit(pool, ops_bytes, lits, nops, out_write, size):
    """run the operations; out_write(bytes) receives the output in order; returns bytes written"""
    it = varints(ops_bytes); lp = 0; exp = 0; w = 0
    for _ in range(nops):
        ll = next(it); ml = next(it); d = unzig(next(it))
        if ll:
            out_write(lits[lp:lp + ll]); lp += ll; w += ll
        g = exp + d
        left = ml
        while left:
            k = min(left, 1 << 26)
            out_write(pool.read(g, k)); g += k; left -= k
        exp = g; w += ml
    if lp < len(lits):
        out_write(lits[lp:]); w += len(lits) - lp
    if w != size:
        raise ValueError('patch produced %d bytes, expected %d' % (w, size))
    return w


# ---------------------------------------------------------------- zip layout (skeleton + members)
class ZipLayout:
    """The bytes of a zip that are not member payload (local headers, central directory, ...) and where each
    member's raw payload sits."""
    def __init__(self, path):
        self.path = path
        z = zipfile.ZipFile(path)
        infos = sorted(z.infolist(), key=lambda i: i.header_offset)
        self.members = []
        with open(path, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            prev = 0
            skel = bytearray()
            for i in infos:
                h = mm[i.header_offset:i.header_offset + 30]
                if h[:4] != b'PK\x03\x04':
                    raise ValueError('%s: bad local header of %s' % (path, i.filename))
                n, m = struct.unpack('<HH', h[26:30])
                start = i.header_offset + 30 + n + m
                if start < prev:
                    raise ValueError('%s: overlapping members' % path)
                skel += mm[prev:start]
                self.members.append(dict(name=i.filename, method=i.compress_type, start=start, csize=i.compress_size,
                                         usize=i.file_size, crc=i.CRC, skel_pos=len(skel)))
                prev = start + i.compress_size
            skel += mm[prev:]
            self.skel = bytes(skel)
            self.size = len(mm)
            mm.close()
        z.close()


def raw_payload(path, m):
    with open(path, 'rb') as f:
        f.seek(m['start'])
        return f.read(m['csize'])


def member_bytes(path, m):
    raw = raw_payload(path, m)
    if m['method'] == 0:
        return raw
    if m['method'] == 8:
        return zlib.decompress(raw, -15)
    z = zipfile.ZipFile(path)
    try:
        return z.read(m['name'])
    finally:
        z.close()


CHUNKS = (1 << 20, 0, 1 << 16, 8192, 1 << 22, 1 << 18, 1 << 14)
LEVELS = (6, 9, 1, 2, 3, 4, 5, 7, 8)


def deflate(d, level, chunk, memlevel=8):
    c = zlib.compressobj(level, zlib.DEFLATED, -15, memlevel)
    out = []
    if chunk == 0 or len(d) <= chunk:
        out.append(c.compress(d))
    else:
        mv = memoryview(d)
        for k in range(0, len(d), chunk):
            out.append(c.compress(mv[k:k + chunk]))
    out.append(c.flush())
    return b''.join(out)


def find_deflate(d, raw):
    """(level, chunk) that reproduces the raw deflate stream `raw` of `d`, else None"""
    small = len(d) <= (1 << 16)
    pre = bytes(d[:1 << 22])
    for lv in LEVELS:
        for ch in ((0,) if small else CHUNKS):
            if not small:
                c = zlib.compressobj(lv, zlib.DEFLATED, -15, 8)
                out = []
                if ch == 0:
                    out.append(c.compress(pre))
                else:
                    for k in range(0, len(pre), ch):
                        out.append(c.compress(pre[k:k + ch]))
                o = b''.join(out)
                if raw[:len(o)] != o:
                    continue
            if deflate(d, lv, ch) == raw:
                return (lv, ch)
    return None


# ---------------------------------------------------------------- patch container (.klp)
def write_klp(path, hdr, blocks):
    """hdr: dict (json); blocks: list of bytes appended after the header; hdr['blocks'] gets [off, len]"""
    offs = []
    o = 0
    for b in blocks:
        offs.append([o, len(b)])
        o += len(b)
    hdr = dict(hdr)
    hdr['blocks'] = offs
    hb = zlib.compress(json.dumps(hdr, separators=(',', ':')).encode('utf8'), 9)
    with open(path, 'wb') as f:
        f.write(MAGIC)
        f.write(struct.pack('<I', len(hb)))
        f.write(hb)
        for b in blocks:
            f.write(b)
    return os.path.getsize(path)


def read_klp(path):
    f = open(path, 'rb')
    if f.read(4) != MAGIC:
        raise ValueError('%s is not a KL Merge patch' % path)
    n = struct.unpack('<I', f.read(4))[0]
    hdr = json.loads(zlib.decompress(f.read(n)))
    base = 8 + n

    def block(i):
        off, ln = hdr['blocks'][i]
        f.seek(base + off)
        return f.read(ln)
    return hdr, block, f


class Sources:
    """Opens source pieces (files or zip members) through a resolver ref -> path."""
    def __init__(self, resolve):
        self.resolve = resolve
        self.layouts = {}
        self.mm = {}

    def path(self, ref):
        return self.resolve(ref)

    def layout(self, ref):
        if ref not in self.layouts:
            self.layouts[ref] = ZipLayout(self.path(ref))
        return self.layouts[ref]

    def load(self, ref, member):
        p = self.path(ref)
        if member is None:
            if os.path.getsize(p) == 0:
                return b''
            mm = self.mm.get(ref)
            if mm is None:
                f = open(p, 'rb')
                mm = self.mm[ref] = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            return mm
        for m in self.layout(ref).members:
            if m['name'] == member:
                return member_bytes(p, m)
        raise KeyError('%s has no member %s' % (ref, member))




# ---------------------------------------------------------------- build one blob from a patch (installer side)
def build_blob(hdr, block, sources, dest_path):
    """Reconstruct one blob (file or zip) from a patch into dest_path. Returns the sha1 hex of what was written."""
    pool = Pool(sources.load)
    for ref, member, size in hdr['pieces']:
        pool.add(ref, member, size)
    ops_all = memoryview(zdecomp(block(hdr['ops']))) if hdr.get('ops') is not None else memoryview(b'')
    lit_all = memoryview(zdecomp(block(hdr['lit']))) if hdr.get('lit') is not None else memoryview(b'')
    h = hashlib.sha1()
    f = open(dest_path, 'wb', buffering=1 << 20)

    def out(b):
        h.update(b)
        f.write(b)
    try:
        if hdr['kind'] == 'file':
            u = hdr['units'][0]
            apply_unit(pool, ops_all[u['oo']:u['oo'] + u['ol']], lit_all[u['lo']:u['lo'] + u['ll']], u['on'], out, u['n'])
        else:
            skel = zdecomp(block(hdr['skel']))
            prev = 0
            for u in hdr['units']:
                out(skel[prev:u['skel_pos']])
                prev = u['skel_pos']
                mode = u['mode']
                if mode == 'rl':                              # raw payload shipped as is
                    out(lit_all[u['lo']:u['lo'] + u['ll']])
                elif mode == 'rc':                            # raw payload copied from a source zip member
                    lay = sources.layout(u['ref'])
                    m = [x for x in lay.members if x['name'] == u['member']][0]
                    pl = raw_payload(sources.path(u['ref']), m)
                    if len(pl) != u['csize']:
                        raise ValueError('source payload size differs for %s' % u['name'])
                    out(pl)
                else:
                    if u.get('src'):
                        buf = sources.load(u['src'][0], u['src'][1])
                    else:
                        buf = bytearray()
                        apply_unit(pool, ops_all[u['oo']:u['oo'] + u['ol']], lit_all[u['lo']:u['lo'] + u['ll']],
                                   u['on'], buf.extend, u['n'])
                    if len(buf) != u['n'] or zlib.crc32(buf) & 0xffffffff != u['crc']:
                        raise ValueError('member %s: crc mismatch after patching' % u['name'])
                    if u.get('comp') is None:
                        out(bytes(buf))
                    else:
                        out(deflate(bytes(buf), u['comp'][0], u['comp'][1]))
                    del buf
            out(skel[prev:])
    finally:
        f.close()
    return h.hexdigest()


# ---------------------------------------------------------------- maker
def mm_file(path):
    if os.path.getsize(path) == 0:
        return b''
    f = open(path, 'rb')
    return mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)


EXCLUDE_RE = re.compile(r'(\.before-|\.absent$|\.delays-|\.state\.json$|_journal\.json$|\.of-test-build|\.locked_)')
STOCK_MTIME = time.mktime((2026, 9, 14, 0, 0, 0, 0, 0, -1))      # the Steam install was 2026-09-13
WIN_SLOTS = ['F%02d' % i for i in range(1, 10)] + ['L%02d' % i for i in range(0, 12)]
OWN_ROOT = ['dinput8.dll', 'KLHook.ini', 'KLShopPage.ini', 'KL_MOD_SETTINGS.txt']
KEEP_USER = ('KLHook.ini', 'KLShopPage.ini')                       # never overwritten when the player already has one


def nrm(p):
    return p.replace('\\', '/')


class Maker:
    def __init__(self, dd, dm, pd2, out, level=15, log=print):
        self.dd, self.dm, self.pd2, self.out = dd, dm, pd2, out
        self.level = level; self.log = log
        self.shacache_path = os.path.join(out, 'sha1cache.json')
        try:
            self.shacache = json.load(open(self.shacache_path))
        except Exception:
            self.shacache = {}
        self.anchor_cache = {}
        self.sources = Sources(self.resolve)
        self.warn = []
        self.pd2_skipped = []
        self.cand = None

    # -- source resolution: the player's stock file for a reference
    def stock_dd(self, rel):
        b = os.path.join(self.dd, BACKUP, rel)
        if os.path.exists(b):
            return b
        p = os.path.join(self.dd, rel)
        o = p + '.before-1024gunsnd2'
        if os.path.exists(o) and os.path.getmtime(o) < STOCK_MTIME:
            return o
        if os.path.getmtime(p) >= STOCK_MTIME:
            raise RuntimeError('no stock proof for DD file %s (modified after the Steam install)' % rel)
        return p

    def resolve(self, ref):
        k, rel = ref.split(':', 1)
        if k == 'dd':
            return self.stock_dd(rel)
        if k == 'dm':
            return os.path.join(self.dm, rel)
        if k == 'pd':
            return os.path.join(self.pd2, rel)
        raise ValueError(ref)

    def sha(self, path, cache=True):
        if not cache:                      # live files are always read, never cached
            return sha1_file(path)
        st = os.stat(path)
        key = '%s|%d|%d' % (path, st.st_size, int(st.st_mtime))
        v = self.shacache.get(key)
        if v is None:
            v = sha1_file(path)
            self.shacache[key] = v
            tmp = self.shacache_path + '.tmp%d' % os.getpid()
            json.dump(self.shacache, open(tmp, 'w'))
            os.replace(tmp, self.shacache_path)
        return v

    # -- candidate source zips
    def scan(self):
        if self.cand is not None:
            return
        c = {}
        if os.path.exists(os.path.join(self.dd, 'Patch01.zip')):
            c['dd:Patch01.zip'] = None
        for root, dirs, files in os.walk(os.path.join(self.dd, 'Scenes')):
            for fn in files:
                if fn.lower().endswith('.zip'):
                    rel = nrm(os.path.relpath(os.path.join(root, fn), self.dd))
                    try:
                        self.stock_dd(rel)
                    except RuntimeError:
                        continue
                    c['dd:' + rel] = None
        for root, dirs, files in os.walk(os.path.join(self.dm, 'Scenes')):
            for fn in files:
                if fn.lower().endswith('.zip'):
                    c['dm:' + nrm(os.path.relpath(os.path.join(root, fn), self.dm))] = None
        for ref in c:
            try:
                z = zipfile.ZipFile(self.resolve(ref))
                c[ref] = [(i.filename, i.CRC, i.file_size) for i in z.infolist()]
                z.close()
            except Exception as e:
                self.log('   skip candidate %s: %s' % (ref, e))
        self.cand = {k: v for k, v in c.items() if v}
        self.log('candidate source zips: %d' % len(self.cand))

    # -- patch writer helpers
    def _finish(self, hdr, ops_all, lit_all, skel, outpath, pieces_refs):
        blocks = []
        cz = zc(self.level, -1)
        if skel is not None:
            hdr['skel'] = len(blocks); blocks.append(zc(19).compress(skel))
        hdr['ops'] = len(blocks); blocks.append(zc(19).compress(bytes(ops_all)))
        hdr['lit'] = len(blocks); blocks.append(cz.compress(bytes(lit_all)) if lit_all else zc(1).compress(b''))
        hdr['version'] = VERSION
        return write_klp(outpath, hdr, blocks)

    def make_file(self, live, refs, outpath, bits=None):
        """patch for one plain file against whole-file stock sources `refs`"""
        pool = Pool(self.sources.load)
        for r in refs:
            pool.add(r, None, os.path.getsize(self.resolve(r)))
        T = mm_file(live)
        idx = None
        if pool.total and len(T):
            bits = bits or (5 if pool.total < (1 << 28) else 6 if pool.total < (1 << 30) else 7)
            idx = PoolIndex(pool, bits, self.anchor_cache, ())
        ops, lits, nops, copied = encode_unit(T, idx)
        hdr = dict(kind='file', pieces=[[r, None, pool.pieces[i][2]] for i, r in enumerate(refs)],
                   units=[dict(n=len(T), oo=0, ol=len(ops), on=nops, lo=0, ll=len(lits))])
        size = self._finish(hdr, ops, lits, None, outpath, refs)
        return size, copied, len(T) - copied

    def make_zip(self, live, outpath, hints=()):
        self.scan()
        L = ZipLayout(live)
        tkeys = {(m['crc'], m['usize']): m for m in L.members}
        score = []
        for ref, idx in self.cand.items():
            ov = 0
            seen = set()
            for (n, c, u) in idx:
                if (c, u) in tkeys and (c, u) not in seen and u > 64:
                    seen.add((c, u)); ov += u
            if ov:
                score.append((ov, ref))
        score.sort(reverse=True)
        score_all = list(score)
        hinted = []
        for h in hints:
            for ref in sorted(self.cand):
                if (ref == h or (('/%s/' % h) in ref and ref.endswith('_Main.zip'))) and ref not in hinted:
                    hinted.append(ref)
        chosen = hinted + [r for ov, r in score if r not in hinted][:max(0, 6 - len(hinted))]
        self.log('   sources: ' + ', '.join(chosen))
        exact = {}
        for ref in hinted + [r for ov, r in score_all if r not in hinted]:
            for (n, c, u) in self.cand[ref]:
                exact.setdefault((c, u), (ref, n))
        exts = {os.path.splitext(m['name'])[1].lower() for m in L.members}
        pool = Pool(self.sources.load)
        by_ext = {}
        seen = set()
        for ref in chosen:
            for (n, c, u) in self.cand[ref]:
                e = os.path.splitext(n)[1].lower()
                if e in exts and u > 256 and (c, u) not in seen:
                    seen.add((c, u))
                    by_ext.setdefault(e, set()).add(len(pool.pieces))
                    pool.add(ref, n, u)
        data = open(live, 'rb')
        mm = mmap.mmap(data.fileno(), 0, access=mmap.ACCESS_READ)
        idxs = {}
        ops_all = bytearray(); lit_all = bytearray(); units = []
        prevp = 0
        st = dict(rc=0, x=0, d=0, rl=0, copied=0, lit=0, rawfail=0)
        for m in L.members:
            raw = mm[m['start']:m['start'] + m['csize']]
            name = m['name']
            u = dict(name=name, skel_pos=m['skel_pos'], n=m['usize'], crc=m['crc'], csize=m['csize'])
            if m['method'] not in (0, 8):
                raise RuntimeError('%s: unsupported zip method %d' % (name, m['method']))
            d = bytes(raw) if m['method'] == 0 else zlib.decompress(raw, -15)
            key = (m['crc'], m['usize'])
            comp = None
            if m['method'] == 8:
                comp = find_deflate(d, raw)
                if comp is None:
                    u.update(mode='rl', lo=len(lit_all), ll=len(raw)); lit_all += raw; st['rl'] += 1; st['rawfail'] += len(raw)
                    self.warn.append('%s: %s deflate not reproducible, raw stream shipped (%s)' % (os.path.basename(live), name, fmt(len(raw))))
                    units.append(u); continue
                u['comp'] = list(comp)
            ex = exact.get(key) if m['usize'] else None
            if ex:
                sref, sname = ex
                sl = self.sources.layout(sref)
                sm = [x for x in sl.members if x['name'] == sname][0]
                if sm['method'] == m['method'] and sm['csize'] == m['csize'] and \
                        raw_payload(self.sources.path(sref), sm) == bytes(raw):
                    u.update(mode='rc', ref=sref, member=sname); st['rc'] += 1
                else:
                    u.update(mode='d', src=[sref, sname], oo=0, ol=0, on=0, lo=0, ll=0); st['x'] += 1
                units.append(u); continue
            e = os.path.splitext(name)[1].lower()
            idx = None
            if e in by_ext and len(d) >= 64:
                if e not in idxs:
                    tot = sum(pool.pieces[i][2] for i in by_ext[e])
                    idxs[e] = PoolIndex(pool, 5 if tot < (1 << 28) else 6, None, (), only=by_ext[e])
                idx = idxs[e]
            ops, lits, nops, copied = encode_unit(d, idx)
            u.update(mode='d', oo=len(ops_all), ol=len(ops), on=nops, lo=len(lit_all), ll=len(lits))
            ops_all += ops; lit_all += lits
            st['d'] += 1; st['copied'] += copied; st['lit'] += len(lits)
            units.append(u)
        mm.close(); data.close()
        hdr = dict(kind='zip', pieces=[[r, mem, sz] for (r, mem, sz, _) in pool.pieces], units=units)
        size = self._finish(hdr, ops_all, lit_all, L.skel, outpath, chosen)
        self.log('   members: rc %(rc)d  x %(x)d  patched %(d)d  rawlit %(rl)d | copied %(copied)d literal %(lit)d' % st)
        return size, st['copied'], st['lit'] + st['rawfail'], chosen


# ---------------------------------------------------------------- what the live mod consists of
# source levels of each map (from KLExpansion/BuildInfo/<map>/result.json where it exists; the three marked GUESS have none)
MAP_HINTS = {
    'DM01': ('M01_FA_A', 'F07'), 'DM01B': ('M01_A', 'M01_FA_A', 'F07'),            # DM01B GUESS
    'DM02': ('M02_FA_A', 'F07'), 'DM03': ('M03_FA_A', 'F07'), 'DM03A': ('M03_A', 'F07'),
    'DM05A': ('M05_A', 'F07'), 'DM06': ('M06_FA_A', 'F07'), 'DM06B': ('M06_A', 'M06_FA_A', 'F07'),   # DM06B GUESS
    'DM07': ('M07_A', 'F07'), 'DM09': ('M09_A', 'M09_B', 'F07'),
    'DM11B': ('M11_B', 'M11_A', 'F07'),                                           # DM11B GUESS
    'DD10': ('L05', 'F07'),
}
for _i in range(1, 10):
    MAP_HINTS['DD%02d' % _i] = ('F%02d' % _i,)


def hint_levels(mapid):
    return MAP_HINTS.get(mapid, ('F07',))


def list_files(root, skip=EXCLUDE_RE):
    out = []
    for r, dirs, files in os.walk(root):
        for fn in files:
            if skip.search(fn):
                continue
            out.append(os.path.join(r, fn))
    return sorted(out)


def enumerate_targets(mk, only):
    """-> list of dict(group, rel, live, kind, hints/refs, stock)"""
    dd = mk.dd
    T = []

    def want(g):
        return only is None or g in only or g.split(':')[0] in only

    if want('core'):
        for fn in OWN_ROOT:
            p = os.path.join(dd, fn)
            if os.path.exists(p):
                T.append(dict(group='core', rel=fn, live=p, kind='lit'))
        p = os.path.join(dd, 'KLExpansion', 'KLHook.expansion.ini')
        if os.path.exists(p):
            T.append(dict(group='core', rel='KLExpansion/KLHook.expansion.ini', live=p, kind='lit'))
    if want('overlay'):
        base = os.path.join(dd, 'KLExpansion', 'Overlay')
        for p in list_files(base):
            rel = nrm(os.path.relpath(p, dd))
            if p.lower().endswith('.zip'):
                src = 'dd:' + nrm(os.path.relpath(p, base))                        # Patch01.zip, Scenes/kaneandlynch.zip
                T.append(dict(group='overlay', rel=rel, live=p, kind='zip', hints=(src,)))
            else:
                T.append(dict(group='overlay', rel=rel, live=p, kind='lit'))
    if want('audio'):
        for sub in ('Ambience', 'Stinger'):
            for p in list_files(os.path.join(dd, 'KLExpansion', sub)):
                if 'pd2' in os.path.basename(p).lower():           # Payday 2 audio: not shippable, see the report
                    mk.pd2_skipped.append(nrm(os.path.relpath(p, dd)))
                    continue
                T.append(dict(group='audio', rel=nrm(os.path.relpath(p, dd)), live=p, kind='lit'))
    mapsdir = os.path.join(dd, 'KLExpansion', 'Maps')
    for mid in sorted(os.listdir(mapsdir)):
        if not want('map:' + mid) and not want(mid):
            continue
        base = os.path.join(mapsdir, mid)
        for p in list_files(base):
            rel = nrm(os.path.relpath(p, dd))
            fn = os.path.basename(p)
            if fn.lower().endswith('.zip'):
                T.append(dict(group='map:' + mid, rel=rel, live=p, kind='zip', hints=hint_levels(mid)))
            elif fn.lower().endswith('.ini'):
                T.append(dict(group='map:' + mid, rel=rel, live=p, kind='lit'))
            else:
                T.append(dict(group='map:' + mid, rel=rel, live=p, kind='loose', mapid=mid))
    if want('stockwav'):
        for s in WIN_SLOTS:
            d = os.path.join(dd, 'Scenes', 'Locations', s)
            if not os.path.isdir(d):
                continue
            for fn in sorted(os.listdir(d)):
                if EXCLUDE_RE.search(fn) or fn.lower().endswith(('.zip', '.ini')):
                    continue
                rel = 'Scenes/Locations/%s/%s' % (s, fn)
                try:
                    sp = mk.stock_dd(rel)
                except RuntimeError:
                    continue
                if mk.sha(sp) != mk.sha(os.path.join(dd, rel), cache=False):
                    T.append(dict(group='stockwav', rel=rel, live=os.path.join(dd, rel), kind='file', refs=['dd:' + rel],
                                  stock=mk.sha(sp)))
    if want('pcdef'):
        T.append(dict(group='pcdef', rel='PC_Def.str', live=os.path.join(dd, 'PC_Def.str'), kind='file',
                      refs=['dd:PC_Def.str', 'dm:PC_Def.str'], stock=mk.sha(mk.stock_dd('PC_Def.str'))))
    return T


def loose_refs(mk, mapid, fn):
    suffix = fn.split('_', 1)[1] if '_' in fn else fn
    refs = []
    lv = hint_levels(mapid)
    for h in lv:
        if h[0] in 'FL' and len(h) == 3:
            rel = 'Scenes/Locations/%s/%s_%s' % (h, h, suffix)
            if os.path.exists(os.path.join(mk.dd, rel)):
                try:
                    mk.stock_dd(rel); refs.append('dd:' + rel)
                except RuntimeError:
                    pass
        else:
            d = os.path.join(mk.dm, 'Scenes', 'Locations', h)
            if os.path.isdir(d):
                for f2 in sorted(os.listdir(d)):
                    if f2.endswith('_' + suffix):
                        refs.append('dm:Scenes/Locations/%s/%s' % (h, f2))
    return refs


def patch_refs(hdr):
    r = set(p[0] for p in hdr['pieces'])
    for u in hdr['units']:
        for k in ('ref',):
            if u.get(k):
                r.add(u[k])
        if u.get('src'):
            r.add(u['src'][0])
    return sorted(r)


def cmd_make(a):
    low_priority()
    out = a.outdir
    os.makedirs(os.path.join(out, 'patches'), exist_ok=True)
    os.makedirs(os.path.join(out, 'parts'), exist_ok=True)
    mk = Maker(a.dd, a.dm, a.pd2, out, level=a.level)
    only = [x for x in a.only.split(',')] if a.only else None
    T = enumerate_targets(mk, only)
    # snapshot of the small own files (they change while other chats install hooks)
    snap = os.path.join(out, '_snap')
    for t in T:
        if t['kind'] == 'lit' and os.path.getsize(t['live']) < (64 << 20):
            dst = os.path.join(snap, t['rel'])
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(t['live'], dst)
            t['live'] = dst
    groups = {}
    for t in T:
        groups.setdefault(t['group'], []).append(t)
    for g, items in groups.items():
        part = os.path.join(out, 'parts', g.replace(':', '_') + '.json')
        entries = []
        t0 = time.time()
        mk.log('== %s: %d files' % (g, len(items)))
        for t in items:
            live = t['live']
            st0 = os.stat(live)
            sha = mk.sha(live, cache=False)
            pname = '%s.klp' % sha[:20]
            pfile = os.path.join(out, 'patches', pname)
            ent = dict(group=g, rel=t['rel'], size=st0.st_size, sha1=sha, patch=pname)
            if t.get('stock'):
                ent['stock'] = t['stock']
            if t['rel'] in KEEP_USER:
                ent['keep_user'] = True
            if not os.path.exists(pfile):
                tt = time.time()
                mk.log(' %s (%s)' % (t['rel'], fmt(st0.st_size)))
                if t['kind'] == 'zip':
                    size = mk.make_zip(live, pfile, t.get('hints', ()))[0]
                elif t['kind'] == 'file':
                    size = mk.make_file(live, t['refs'], pfile)[0]
                elif t['kind'] == 'loose':
                    size = mk.make_file(live, loose_refs(mk, t['mapid'], os.path.basename(live)), pfile)[0]
                else:
                    size = mk.make_file(live, [], pfile)[0]
                mk.log('   -> %s  (%.0fs)' % (fmt(size), time.time() - tt))
            hdr, block, f = read_klp(pfile)
            f.close()
            ent['patch_size'] = os.path.getsize(pfile)
            ent['refs'] = {r: [os.path.getsize(mk.resolve(r)), mk.sha(mk.resolve(r))] for r in patch_refs(hdr)}
            st1 = os.stat(live)
            if (st1.st_size, int(st1.st_mtime)) != (st0.st_size, int(st0.st_mtime)):
                mk.warn.append('%s changed while it was read' % t['rel'])
            entries.append(ent)
        json.dump(dict(group=g, entries=entries, warn=mk.warn), open(part, 'w'), indent=1)
        mk.log('== %s done in %.0fs' % (g, time.time() - t0))
    merge_manifest(out)
    for w in mk.warn:
        print('WARN', w)
    if mk.pd2_skipped:
        print('NOT SHIPPED (Payday 2 audio):', ', '.join(mk.pd2_skipped))
        json.dump(mk.pd2_skipped, open(os.path.join(out, 'parts', '_pd2_skipped.txt'), 'w'))


def cmd_checklive(a):
    """re-read every live file now and compare with the manifest (run before tests and before reporting)"""
    man = json.load(open(os.path.join(a.outdir, 'manifest.json')))
    snap = os.path.join(a.outdir, '_snap')
    bad = 0
    for e in man['entries']:
        p = os.path.join(a.dd, e['rel'])
        if not os.path.exists(p):
            say('MISSING', e['rel']); bad += 1; continue
        if sha1_file(p) != e['sha1']:
            say('CHANGED since made:', e['rel']); bad += 1
    say('checklive: %d files, %d changed/missing' % (len(man['entries']), bad))
    return 1 if bad else 0


def merge_manifest(out):
    ents = []
    for fn in sorted(os.listdir(os.path.join(out, 'parts'))):
        if fn.endswith('.json'):
            ents += json.load(open(os.path.join(out, 'parts', fn)))['entries']
    man = dict(name='KL Merge', version=VERSION, credits=CREDITS, kl2_sha1=STOCK_KL2_SHA1, entries=ents)
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    seen = set(); tot = 0
    for e in ents:
        if e['patch'] not in seen:
            seen.add(e['patch']); tot += e['patch_size']
    print('manifest: %d files, %d patches, %s of patches' % (len(ents), len(seen), fmt(tot)))


# ---------------------------------------------------------------- installer
def steam_libraries():
    libs = []
    roots = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'),
                          (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')):
            try:
                k = winreg.OpenKey(hive, key)
                v = winreg.QueryValueEx(k, 'SteamPath' if hive == winreg.HKEY_CURRENT_USER else 'InstallPath')[0]
                roots.append(v.replace('/', '\\'))
            except OSError:
                pass
    except ImportError:
        pass
    roots += [r'C:\Program Files (x86)\Steam', r'C:\Steam']
    for r in roots:
        if os.path.isdir(r) and r not in libs:
            libs.append(r)
        vdf = os.path.join(r, 'steamapps', 'libraryfolders.vdf')
        if os.path.exists(vdf):
            try:
                for m in re.finditer(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf8', errors='replace').read()):
                    p = m.group(1).replace('\\\\', '\\')
                    if os.path.isdir(p) and p not in libs:
                        libs.append(p)
            except OSError:
                pass
    return libs


def find_game(folder):
    for lib in steam_libraries():
        p = os.path.join(lib, 'steamapps', 'common', folder)
        if os.path.isdir(p):
            return p
    return None


class Fail(Exception):
    pass


def free_bytes(path):
    return shutil.disk_usage(path).free


def load_manifest(pkg):
    p = os.path.join(pkg, 'manifest.json')
    if not os.path.exists(p):
        raise Fail('no manifest.json in %s (use --pkg <package folder>)' % pkg)
    return json.load(open(p))


def select_entries(man, only):
    ents = man['entries']
    if only:
        o = [x.strip() for x in only.split(',') if x.strip()]
        ents = [e for e in ents if e['group'] in o or e['group'].split(':')[0] in o or e['group'].split(':')[-1] in o]
    return ents


class Env:
    def __init__(self, dd, dm, pd2):
        self.dd, self.dm, self.pd2 = dd, dm, pd2
        self.shac = {}

    def resolve(self, ref):
        k, rel = ref.split(':', 1)
        root = {'dd': self.dd, 'dm': self.dm, 'pd': self.pd2}[k]
        if not root:
            raise Fail('%s is needed but its folder was not given' % {'dd': 'Dog Days', 'dm': 'Dead Men', 'pd': 'Payday 2'}[k])
        return os.path.join(root, rel)

    def sha(self, p):
        if p not in self.shac:
            self.shac[p] = sha1_file(p)
        return self.shac[p]


def say(*a):
    print(*a, flush=True)


def preflight(env, ents, log=say):
    """check every source file (size + sha1) before anything is written; returns (usable entries, problems, skipped)"""
    need = {}
    for e in ents:
        for r, (sz, sh) in e['refs'].items():
            need.setdefault(r, (sz, sh))
    problems = []
    bad_refs = set()
    for r, (sz, sh) in sorted(need.items()):
        try:
            p = env.resolve(r)
        except Fail as ex:
            problems.append(str(ex)); bad_refs.add(r); continue
        if r.startswith('dd:') and not os.path.exists(p):
            p2 = os.path.join(env.dd, BACKUP, r[3:])
            p = p2 if os.path.exists(p2) else p
        if not os.path.exists(p):
            problems.append('missing source file: %s' % p); bad_refs.add(r); continue
        if os.path.getsize(p) != sz:
            problems.append('%s has %d bytes, expected %d (not the stock file?)' % (p, os.path.getsize(p), sz)); bad_refs.add(r); continue
    if problems:
        return problems, bad_refs
    n = 0
    for r, (sz, sh) in sorted(need.items()):
        n += 1
        p = env.resolve(r)
        if r.startswith('dd:') and not os.path.exists(p):
            p = os.path.join(env.dd, BACKUP, r[3:])
        if env.sha(p) != sh:
            problems.append('%s does not match the stock file this package was made from (sha1 differs)' % p)
            bad_refs.add(r)
    return problems, bad_refs


def rt(fn, *a):
    """retry a file operation: antivirus scanners and indexers briefly lock freshly written files"""
    for k in range(12):
        try:
            return fn(*a)
        except PermissionError:
            if k == 11:
                raise
            time.sleep(1.0 + k)


def now_tag():
    return time.strftime('%Y%m%d-%H%M%S')


def journal_path(dd):
    return os.path.join(dd, JOURNAL)


def load_journal(dd):
    p = journal_path(dd)
    if os.path.exists(p):
        return json.load(open(p))
    return dict(version=VERSION, entries=[], dirs=[])


def save_journal(dd, j):
    tmp = journal_path(dd) + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(j, f, indent=1)
    for k in range(8):                       # antivirus / indexers can hold the file for a moment
        try:
            os.replace(tmp, journal_path(dd))
            return
        except PermissionError:
            time.sleep(0.5 * (k + 1))
    shutil.copyfile(tmp, journal_path(dd))


def make_parent(path, j, dd):
    d = os.path.dirname(path)
    miss = []
    while d and not os.path.isdir(d) and len(d) > len(dd):
        miss.append(d); d = os.path.dirname(d)
    for m in reversed(miss):
        os.mkdir(m)
        j['dirs'].append(nrm(os.path.relpath(m, dd)))


def cmd_install(a):
    low_priority()
    dd = a.dd or find_game('Kane & Lynch 2 - Dog Days')
    dm = a.dm or find_game('Kane and Lynch Dead Men')
    pd2 = a.pd2 or find_game('PAYDAY 2')
    if not dd or not os.path.isdir(dd):
        raise Fail('Dog Days folder not found; pass it as the first argument')
    say('Dog Days : %s' % dd)
    say('Dead Men : %s' % (dm or 'NOT FOUND'))
    say('Payday 2 : %s' % (pd2 or 'not found (optional)'))
    pkg = a.pkg or os.path.dirname(os.path.abspath(sys.argv[0] if not getattr(sys, 'frozen', False) else sys.executable))
    man = load_manifest(pkg)
    exe = os.path.join(dd, 'kl2.exe')
    if not os.path.exists(exe):
        raise Fail('kl2.exe not found in %s' % dd)
    if sha1_file(exe) != man['kl2_sha1']:
        raise Fail('kl2.exe is not the stock Steam build this mod was made for (sha1 differs). Supported: Steam, unmodified.')
    ents = select_entries(man, a.only)
    if not dm:
        raise Fail('Kane & Lynch: Dead Men (Steam) was not found; pass --dm <folder>')
    skipped = []
    use = []
    for e in ents:
        if any(r.startswith('pd:') for r in e['refs']) and not pd2:
            skipped.append(e['rel']); continue
        use.append(e)
    if skipped:
        say('skipping %d files that need Payday 2' % len(skipped))
    env = Env(dd, dm, pd2)
    j = load_journal(dd)
    done = {x['rel']: x for x in j['entries']}
    say('checking the stock source files ...')
    todo = []
    for e in use:
        dest = os.path.join(dd, e['rel'])
        if os.path.exists(dest) and os.path.getsize(dest) == e['size'] and env.sha(dest) == e['sha1']:
            continue
        todo.append(e)
    if not todo:
        say('everything is already installed and identical.')
        return 0
    problems, bad = preflight(env, [e for e in todo if e['refs']])
    if problems:
        say('')
        say('CANNOT INSTALL. These source files are missing or are not the stock files this package was made from:')
        for p in problems[:40]:
            say('  ' + p)
        say('Nothing was written. (If you installed another version of this mod before, uninstall it first.)')
        return 2
    bk = os.path.join(dd, BACKUP)
    # disk space
    uniq = {}
    for e in todo:
        uniq.setdefault(e['sha1'], e)
    need = sum(e['size'] for e in uniq.values()) + (1 << 30)
    if free_bytes(dd) < need:
        raise Fail('not enough free disk space on the Dog Days drive: need %s, have %s' % (fmt(need), fmt(free_bytes(dd))))
    if not a.yes:
        say('%d files will be written (%s). Replaced stock files are moved to %s, never deleted.' % (len(todo), fmt(sum(e['size'] for e in todo)), bk))
        if input('Continue? [y/N] ').strip().lower() != 'y':
            return 1
    tmpd = os.path.join(dd, TMPDIR)
    os.makedirs(tmpd, exist_ok=True)
    sources = Sources(lambda r: _resolve_build(env, r))
    built = {}
    t0 = time.time()
    n = 0
    for e in todo:
        n += 1
        if e['sha1'] in built:
            continue
        tp = os.path.join(tmpd, '%s.part' % e['sha1'][:20])
        say('[%d/%d] building %s (%s)' % (n, len(todo), e['rel'], fmt(e['size'])))
        if os.path.exists(tp) and os.path.getsize(tp) == e['size'] and sha1_file(tp) == e['sha1']:
            built[e['sha1']] = tp                  # left over from an interrupted run, verified
            continue
        hdr, block, f = read_klp(os.path.join(pkg, 'patches', e['patch']))
        try:
            sha = build_blob(hdr, block, sources, tp)
        finally:
            f.close()
        if sha != e['sha1']:
            raise Fail('internal check failed for %s (built %s, expected %s). Nothing has been installed.' % (e['rel'], sha, e['sha1']))
        built[e['sha1']] = tp
    say('all %d files built and verified in %.0f s. Installing ...' % (len(built), time.time() - t0))
    tag = now_tag()
    used = set()
    for e in todo:
        dest = os.path.join(dd, e['rel'])
        rec = dict(rel=e['rel'], sha1=e['sha1'], group=e['group'], size=e['size'])
        if os.path.exists(dest):
            if e.get('keep_user'):
                alt = dest + '.new-' + VERSION
                rt(shutil.copyfile, built[e['sha1']], alt)
                rec.update(action='kept', note='your existing file was kept; the packaged one is %s' % os.path.basename(alt), alt=nrm(os.path.relpath(alt, dd)))
                say('  kept your %s (new default saved as %s)' % (e['rel'], os.path.basename(alt)))
                j['entries'] = [x for x in j['entries'] if x['rel'] != e['rel']] + [rec]
                save_journal(dd, j)
                continue
            if e.get('stock') and not os.path.exists(os.path.join(bk, e['rel'])):
                bdest = os.path.join(bk, e['rel'])
            else:
                bdest = os.path.join(bk, '_klmerge_replaced', tag, e['rel'])
            os.makedirs(os.path.dirname(bdest), exist_ok=True)
            rec.update(action='replaced', backup=nrm(os.path.relpath(bdest, dd)))
            j['entries'] = [x for x in j['entries'] if x['rel'] != e['rel']] + [rec]
            save_journal(dd, j)                      # written BEFORE the move, so an interrupted run can be undone
            rt(shutil.move, dest, bdest)
        else:
            rec.update(action='new')
            make_parent(dest, j, dd)
            j['entries'] = [x for x in j['entries'] if x['rel'] != e['rel']] + [rec]
            save_journal(dd, j)
        src = built[e['sha1']]
        if e['sha1'] in used or sum(1 for x in todo if x['sha1'] == e['sha1']) > 1:
            rt(shutil.copyfile, src, dest)
            used.add(e['sha1'])
        else:
            rt(os.replace, src, dest)
            used.add(e['sha1'])
        j['entries'] = [x for x in j['entries'] if x['rel'] != e['rel']] + [rec]
        save_journal(dd, j)
    shutil.rmtree(tmpd, ignore_errors=True)
    say('')
    say('Done. %s' % CREDITS)
    say('Start Dog Days from Steam as usual. Your Steam launch options were not touched.')
    return 0


def _resolve_build(env, ref):
    p = env.resolve(ref)
    if ref.startswith('dd:') and not os.path.exists(p):
        p = os.path.join(env.dd, BACKUP, ref[3:])
    return p


def cmd_uninstall(a):
    dd = a.dd or find_game('Kane & Lynch 2 - Dog Days')
    if not dd:
        raise Fail('Dog Days folder not found')
    j = load_journal(dd)
    if not j['entries']:
        say('nothing to uninstall (no %s).' % JOURNAL)
        return 0
    if not a.yes:
        if input('Remove the mod files and restore the original files from %s? [y/N] ' % BACKUP).strip().lower() != 'y':
            return 1
    tag = now_tag()
    left = []
    for rec in reversed(j['entries']):
        dest = os.path.join(dd, rec['rel'])
        act = rec['action']
        if act == 'kept':
            alt = os.path.join(dd, rec.get('alt', ''))
            if rec.get('alt') and os.path.exists(alt):
                rt(os.remove, alt)
            continue
        if os.path.exists(dest):
            if sha1_file(dest) == rec['sha1']:
                rt(os.remove, dest)
            else:
                ed = dest + '.edited-' + tag
                rt(os.replace, dest, ed)
                say('  you changed %s: kept as %s' % (rec['rel'], os.path.basename(ed)))
        if act == 'replaced':
            b = os.path.join(dd, rec['backup'])
            if os.path.exists(b):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                rt(os.replace, b, dest)
            else:
                left.append(rec)
                say('  WARNING: backup of %s is missing (%s)' % (rec['rel'], rec['backup']))
    for d in sorted(set(j['dirs']), key=len, reverse=True):
        try:
            os.rmdir(os.path.join(dd, d))
        except OSError:
            pass
    rp = os.path.join(dd, BACKUP, '_klmerge_replaced')
    if os.path.isdir(rp):
        for r, ds, fs in os.walk(rp, topdown=False):
            try:
                os.rmdir(r)
            except OSError:
                pass
    j['entries'] = left
    j['dirs'] = []
    if left:
        save_journal(dd, j)
    else:
        rt(os.remove, journal_path(dd))
    say('Uninstall finished.')
    return 0


def cmd_verify(a):
    dd = a.dd or find_game('Kane & Lynch 2 - Dog Days')
    pkg = a.pkg or os.path.dirname(os.path.abspath(sys.argv[0]))
    man = load_manifest(pkg)
    ents = select_entries(man, a.only)
    bad = 0
    for e in ents:
        dest = os.path.join(dd, e['rel'])
        if not os.path.exists(dest):
            say('MISSING  ' + e['rel']); bad += 1; continue
        if os.path.getsize(dest) != e['size'] or sha1_file(dest) != e['sha1']:
            if e.get('keep_user'):
                say('edited   %s (yours)' % e['rel'])
            else:
                say('DIFFERS  ' + e['rel']); bad += 1
    say('verify: %d files checked, %d problems' % (len(ents), bad))
    return 1 if bad else 0


def menu():
    say(CREDITS + '   v' + VERSION)
    while True:
        say('')
        say('  1) Install   2) Uninstall   3) Verify   4) Quit')
        c = input('> ').strip()
        ns = argparse.Namespace(dd=None, dm=None, pd2=None, pkg=None, only=None, yes=False)
        try:
            if c == '1':
                cmd_install(ns)
            elif c == '2':
                cmd_uninstall(ns)
            elif c == '3':
                cmd_verify(ns)
            elif c == '4':
                return 0
        except Fail as e:
            say('ERROR: %s' % e)
        except Exception:
            traceback.print_exc()


def main(argv=None):
    ap = argparse.ArgumentParser(description=CREDITS)
    sub = ap.add_subparsers(dest='cmd')
    m = sub.add_parser('make'); m.add_argument('outdir'); m.add_argument('--dd', required=True); m.add_argument('--dm', required=True)
    m.add_argument('--pd2'); m.add_argument('--only'); m.add_argument('--level', type=int, default=15)
    c = sub.add_parser('checklive'); c.add_argument('outdir'); c.add_argument('--dd', required=True)
    for name in ('install', 'uninstall', 'verify'):
        s = sub.add_parser(name)
        s.add_argument('dd', nargs='?'); s.add_argument('--dm'); s.add_argument('--pd2'); s.add_argument('--pkg')
        s.add_argument('--only'); s.add_argument('--yes', action='store_true')
    a = ap.parse_args(argv)
    if a.cmd is None:
        return menu()
    try:
        return {'make': cmd_make, 'install': cmd_install, 'uninstall': cmd_uninstall, 'verify': cmd_verify, 'checklive': cmd_checklive}[a.cmd](a) or 0
    except Fail as e:
        say('ERROR: %s' % e)
        return 2


if __name__ == '__main__':
    sys.exit(main())
