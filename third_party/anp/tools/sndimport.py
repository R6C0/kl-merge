"""Import Dog Days sound records into a converted level bank (ANP_SND_IMPORT_DD, 15 Oct).

The merged ANM keeps the Dog Days F03 donor clips, whose clip sound id (+0x2c) names a record of F03's .SND.  clipsnd
re-points them by record name, but about 960 of the 1,240 donor clips name sequences the Dead Men bank does not have
(crouch, sneak, cover, transitions, strafe, Dog Days reloads), so they were cleared and those animations were silent.
This module copies exactly the records those clips need (and everything they reference) from F03's .SND, with their
.WHD wave headers and in-memory .WAV data, into the converted level's banks.  clipsnd then points the clips at the copies.

.SND objects (Dog Days layout, offsets are file offsets; checked on F03/L01 and the Dead Men banks):
  record  [type, cdcd, name*, cdcd0000|nattr, attrs*, ...]          every record is listed in directory list <type>
    type 1 sound     0x40  +0x14 wave* (type 4, or a localized wave whose first dword is 0)
    type 2 random    0x30  +0x14 u32 array of record*, +0x18 n|n<<16
    type 3 sequence  0x20  +0x14 array of 12-byte items [kind, time ms, record*] (kinds 2/4/5 name a record), +0x18 n|n<<16
    type 4 wave      0x20  +0x14 .WHD record offset
  attrs = array of nattr pointers to 16-byte attribute nodes [kind, a, b, c]; kind 0x12 = group binding (a = type-23
  group record*).  The directory's (count, offset) pair <kind> after the 25 type lists is a table that lists the node once
  per referencing record (F03: table counts == reference counts for every kind), terminated by 0xcdcdcdcd.  Dead Men
  banks have 33 pairs (kinds 0..32), Dog Days 34: kind 33 attributes (Dog Days only) are dropped from imported records.
.WHD record (Dog Days, 16 words): w5 decoded size, w6 bytes in the .WAV, w8/w9 data offset (64 bit), flags w2>>16:
  0x80 streamed (data in a .str: not importable, the stream names belong to Dead Men), 0x40 language file; byte w2>>24
  layered group (not imported).  .WAV = [0, size, 3, 4] + data.

Not imported (the record and every parent that is left with nothing to play): localized waves (dialogue), streamed waves,
layered waves, '/level_specific/' roots.  Records whose name the level bank already has (same type) are reused.
Group bindings map by name, else by GROUP_MAP, else to audio:groups/sfx#group.
"""
import struct, collections

CD = 0xcdcdcdcd
REC_SIZE = {1: 0x40, 2: 0x30, 3: 0x20, 4: 0x20}
GROUP_MAP = {
    b'audio:groups/sfx_weapons_load#group': b'audio:groups/weapons#group',
    b'audio:groups/sfx_weapons#group': b'audio:groups/weapons#group',
    b'audio:groups/sfx_character#group': b'audio:groups/sfx#group',
    b'audio:groups/sfx_cutscene#group': b'audio:groups/cutscene#group',
    b'audio:groups/sfx_footstep#group': b'audio:groups/footsteps#group',
    b'audio:groups/dialog_user#group': b'audio:groups/dialoguser#group',
    b'audio:groups/sfx_user#group': b'audio:groups/sfxuser#group',
}
GROUP_FALLBACK = b'audio:groups/sfx#group'
SKIP_ROOT_PARTS = (b'/level_specific/',)


def _u(d, o, n=1):
    return struct.unpack_from('<%dI' % n, d, o)


def _name(d, off):
    if not off or off % 4 or off + 12 > len(d):
        return None
    t, c, nm = _u(d, off, 3)
    if c != CD or t >= 0x19 or not (0 < nm < len(d)):
        return None
    e = d.find(b'\0', nm)
    return d[nm:e] if e > nm else None


class _Dir:
    def __init__(self, d):
        self.h0 = _u(d, 0)[0]
        head = _u(d, self.h0, 16)
        self.nl = head.index(CD, 1) - 1
        self.c0 = 1 + self.nl + 4
        self.w = list(_u(d, self.h0, (len(d) - self.h0) // 4))
        p0 = self.c0 + 50
        self.npairs = 0
        while p0 + 2 * self.npairs < len(self.w) and self.w[p0 + 2 * self.npairs] != CD:
            self.npairs += 1
        self.p0 = p0

    def lst(self, d, t):
        n, o = self.w[self.c0 + t], self.w[self.c0 + 25 + t]
        return list(_u(d, o, n)) if n else []

    def tab(self, d, k):
        n, o = self.w[self.p0 + 2 * k], self.w[self.p0 + 2 * k + 1]
        return list(_u(d, o, n)) if n else []


def import_dd(snd, dsnd, dwhd, dwav, roots, whd, wav_len, rep=None):
    """snd: converted level .SND (Dog Days directory); dsnd/dwhd/dwav: donor (F03) banks; roots: donor record offsets the
    clips need; whd: converted level main .WHD; wav_len: size of the level main .WAV.
    Returns (snd, whd, wav_append_bytes, {donor offset: new offset}, stats)."""
    st = collections.Counter() if rep is None else rep
    L = _Dir(snd)
    body = bytearray(snd[:L.h0])
    # level indexes
    lidx = {}
    for t in range(25):
        for r in L.lst(snd, t):
            if r < L.h0:
                n = _name(snd, r)
                if n and _u(snd, r)[0] == t:
                    lidx.setdefault(n, r)
    lgroups = {n: r for n, r in lidx.items() if _u(snd, r)[0] == 23}
    lnodes = {}
    for k in range(L.npairs):
        for p in L.tab(snd, k):
            if p + 16 <= L.h0:
                lnodes.setdefault(bytes(snd[p:p + 16]), p)
    add_list = collections.defaultdict(list)     # type -> new record offsets
    add_tab = collections.defaultdict(list)      # kind -> node offsets (one per reference)
    strings = {}

    def alloc(data, align=16):
        while len(body) % align:
            body.append(0)
        o = len(body)
        body.extend(data)
        return o

    def string(off):
        e = dsnd.index(b'\0', off)
        s = dsnd[off:e + 1]
        if s not in strings:
            strings[s] = alloc(s)
        return strings[s]

    # .WHD / .WAV
    wh0 = _u(whd, 0)[0]
    wbody = bytearray(whd[:wh0])
    wtail = bytes(whd[wh0:])
    wav = bytearray()
    whdmap = {}

    def wave_rec(o):
        if o in whdmap:
            return whdmap[o]
        w = list(_u(dwhd, o, 16))
        fl = (w[2] >> 16) & 0xff
        res = None
        if fl & 0x80:
            st['import: streamed wave skipped'] += 1
        elif fl & 0x40:
            st['import: language-file wave skipped'] += 1
        elif w[2] >> 24:
            st['import: layered wave skipped'] += 1
        elif w[9] or w[8] + w[6] > len(dwav) or not w[6]:
            st['import: wave with bad data range skipped'] += 1
        else:
            while (wav_len + len(wav)) % 16:
                wav.append(0)
            doff = wav_len + len(wav)
            wav.extend(dwav[w[8]:w[8] + w[6]])
            e = dwhd.index(b'\0', w[1])
            while len(wbody) % 16:
                wbody.append(0)
            noff = len(wbody)
            wbody.extend(dwhd[w[1]:e + 1])
            while len(wbody) % 16:
                wbody.append(0)
            w[1] = noff
            w[8] = doff
            w[9] = 0
            res = len(wbody)
            wbody.extend(struct.pack('<16I', *w))
            st['import: waves copied'] += 1
            st['import: wave bytes'] += w[6]
        whdmap[o] = res
        return res

    def attrs(w):
        na = w[3] & 0xffff
        if not na or not w[4]:
            return 0, 0
        out = []
        for p in _u(dsnd, w[4], na):
            node = list(_u(dsnd, p, 4))
            k = node[0]
            if k >= L.npairs:
                st['import: attribute kind %d dropped (no table in the level bank)' % k] += 1
                continue
            if k == 0x12:
                gn = _name(dsnd, node[1])
                g = lgroups.get(gn) or lgroups.get(GROUP_MAP.get(gn)) or lgroups.get(GROUP_FALLBACK)
                if not g:
                    st['import: group binding dropped (%s)' % gn] += 1
                    continue
                if gn not in lgroups:
                    st['import: group %s -> %s' % (gn.decode(), _name(snd, g).decode())] += 1
                node[1] = g
            b = struct.pack('<4I', *node)
            q = lnodes.get(b)
            if q is None:
                q = alloc(b)
                lnodes[b] = q
                st['import: attribute nodes added'] += 1
            add_tab[k].append(q)
            out.append(q)
        if not out:
            return 0, 0
        return alloc(struct.pack('<%dI' % len(out), *out), 4), len(out)

    memo = {}
    busy = set()

    def rec(r):
        if r in memo:
            return memo[r]
        if r in busy:
            st['import: reference cycle cut'] += 1
            return None
        w = list(_u(dsnd, r, 8))
        t = w[0]
        if w[1] != CD:
            st['import: %s skipped' % ('localized wave' if t == 0 else 'non-record')] += 1
            memo[r] = None
            return None
        nm = _name(dsnd, r)
        q = lidx.get(nm)
        if q is not None and _u(snd, q)[0] == t:
            st['import: reused level record (same name)'] += 1
            memo[r] = q
            return q
        if t not in REC_SIZE:
            st['import: record type %d skipped' % t] += 1
            memo[r] = None
            return None
        busy.add(r)
        w = list(_u(dsnd, r, REC_SIZE[t] // 4))
        ok = True
        if t == 1:
            v = rec(w[5])
            ok = v is not None
            w[5] = v or 0
        elif t == 2:
            n = w[6] & 0xffff
            kids = [rec(x) for x in _u(dsnd, w[5], n)] if n else []
            kids = [x for x in kids if x is not None]
            ok = bool(kids) or n == 0
            if kids:
                w[5] = alloc(struct.pack('<%dI' % len(kids), *kids), 4)
            elif ok:
                w[5] = 0
            w[6] = (len(kids) | len(kids) << 16) if (w[6] >> 16) == n else (w[6] & 0xffff0000) | len(kids)
            if len(kids) < n:
                st['import: random-list entries dropped'] += n - len(kids)
        elif t == 3:
            n = w[6] & 0xffff
            items = []
            for k in range(n):
                it = list(_u(dsnd, w[5] + 12 * k, 3))
                if it[0] in (2, 4, 5):
                    v = rec(it[2])
                    if v is None:
                        st['import: sequence steps dropped'] += 1
                        continue
                    it[2] = v
                items.append(it)
            ok = bool(items) or n == 0
            if items:
                w[5] = alloc(b''.join(struct.pack('<3I', *it) for it in items), 4)
            elif ok:
                w[5] = 0
            w[6] = (len(items) | len(items) << 16) if (w[6] >> 16) == n else (w[6] & 0xffff0000) | len(items)
        elif t == 4:
            v = wave_rec(w[5])
            ok = v is not None
            w[5] = v or 0
        busy.discard(r)
        if not ok:
            memo[r] = None
            st['import: type-%d record dropped (nothing playable)' % t] += 1
            return None
        a, na = attrs(w)
        w[4] = a
        w[3] = (w[3] & 0xffff0000) | na
        w[2] = string(w[2])
        q = alloc(struct.pack('<%dI' % len(w), *w))
        add_list[t].append(q)
        st['import: type-%d records copied' % t] += 1
        memo[r] = q
        return q

    imap = {}
    for r in sorted(roots):
        nm = _name(dsnd, r)
        if nm is None:
            continue
        if any(s in nm for s in SKIP_ROOT_PARTS):
            st['import: root skipped (level specific)'] += 1
            continue
        if _u(dsnd, r)[0] not in (1, 2, 3):
            continue
        v = rec(r)
        if v is not None:
            imap[r] = v
    st['import: roots imported'] += len(imap)
    st['import: roots not importable'] += len(roots) - len(imap)
    if not imap:
        return snd, whd, b'', {}, st
    # directory: rebuilt type lists and attribute tables (old arrays stay, unused)
    dw = list(L.w)
    for t, new in sorted(add_list.items()):
        old = L.lst(snd, t)
        o = alloc(struct.pack('<%dI' % (len(old) + len(new)), *(old + new)), 16)
        dw[L.c0 + t] = len(old) + len(new)
        dw[L.c0 + 25 + t] = o
    for k, new in sorted(add_tab.items()):
        old = L.tab(snd, k)
        o = alloc(struct.pack('<%dI' % (len(old) + len(new)), *(old + new)), 16)
        dw[L.p0 + 2 * k] = len(old) + len(new)
        dw[L.p0 + 2 * k + 1] = o
    while len(body) % 16:
        body.append(0)
    nh0 = len(body)
    out = body + struct.pack('<%dI' % len(dw), *dw)
    struct.pack_into('<II', out, 0, nh0, len(out))
    st['import: snd bytes added'] += len(out) - len(snd)
    # .WHD
    while len(wbody) % 16:
        wbody.append(0)
    wh = len(wbody)
    wout = wbody + wtail
    struct.pack_into('<II', wout, 0, wh, len(wout))
    st['import: whd bytes added'] += len(wout) - len(whd)
    st['import: wav bytes added'] += len(wav)
    return bytes(out), bytes(wout), bytes(wav), imap, st


def append_wav(wav, extra):
    """level .WAV [0, size, 3, 4] + data -> with the imported data appended (offsets were taken from len(wav))"""
    if not extra:
        return wav
    h = _u(wav, 0, 4)
    if h[0] != 0 or h[1] != len(wav) or h[2:] != (3, 4):
        raise ValueError('level .WAV header %r unexpected' % (h,))
    out = bytearray(wav) + extra
    struct.pack_into('<I', out, 4, len(out))
    return bytes(out)
