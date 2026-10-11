"""anm_lib - parser/writer for Glacier-1 level animation files (.ANM) of
Kane & Lynch: Dead Men (DM, 2007) and Kane & Lynch 2: Dog Days (DD, 2010).

Format summary (see ANM_FORMAT.md for the full spec and the exe evidence):

  file    = root chunk 'MNA\\0' (u32 0x00414E4D), flags 0x80000000 (has children)
  chunk   = u32 type, u32 sizeflags (bit31 children, bit30 array header, low 30 bits = total size incl. header)
            plain chunk (no flags): payload at +8, length size-8
            bit31 chunk: u32 dataOffset (from chunk start), u32 childCount, [bit30: u32 n, u32[n]], children..., data
  root children, in order: { type5 DBList, type6 Database } x nDB, type7 NameTable, type4 AnimData

DM and DD differ ONLY in the clip record size inside type 4 (0x50 vs 0x68 bytes) and in
the meaning of a few record fields (see ClipRecord). Everything else is binary-identical.
"""
import struct, bisect

U32 = struct.Struct('<I')
MAGIC = 0x00414E4D          # 'MNA\0'
F_CHILDREN = 0x80000000
F_ARRAY = 0x40000000
SIZE_MASK = 0x3FFFFFFF
DB_PREFIX = b'anmcol:animationdatabase#'
REC_DM = 0x50
REC_DD = 0x68
GROUND = 57                  # hard-coded root-bone index in both exes (DM 0x5bfb72, DD 0x5a514b)


def u32(b, o):
    return U32.unpack_from(b, o)[0]


def pad4(b):
    return b + b'\0' * ((-len(b)) % 4)


def cstr4(s):
    """NUL-terminated string padded to 4 bytes (how every name in the file is stored)."""
    return pad4(s + b'\0')


def read_cstr(b, o):
    e = b.index(b'\0', o)
    return b[o:e], e


class AnmError(Exception):
    pass


# ----------------------------------------------------------------------------------------------
# type 5 : per-database "new clips" list
# ----------------------------------------------------------------------------------------------
class DBList:
    """type-5 chunk. flags 0x80000000, dataOffset, childCount=1, one plain child chunk whose
    'type' field is the element count N and whose payload is N u32 clip indices; chunk data =
    resource name (same string as the following type-6 DB), NUL-terminated, padded to 4.
    The list holds, sorted, the clip indices that this DB references and that no earlier DB
    (in file order) references.  Not read by either exe (no code compares a chunk type with 5);
    kept consistent by the writer (recomputed from the DBs)."""
    type = 5

    def __init__(self, name, clips):
        self.name = name
        self.clips = list(clips)

    @classmethod
    def parse(cls, b, o):
        sf = u32(b, o + 4)
        tot = sf & SIZE_MASK
        if sf & 0xC0000000 != F_CHILDREN:
            raise AnmError('type5 flags %x' % sf)
        doff, nch = u32(b, o + 8), u32(b, o + 12)
        if nch != 1:
            raise AnmError('type5 child count %d' % nch)
        n, csz = u32(b, o + 16), u32(b, o + 20)
        if csz != 8 + 4 * n or 16 + csz != doff:
            raise AnmError('type5 child layout')
        clips = struct.unpack_from('<%dI' % n, b, o + 24)
        name, _ = read_cstr(b, o + doff)
        if cstr4(name) != b[o + doff:o + tot]:
            raise AnmError('type5 name padding')
        return cls(name, clips), tot

    def build(self):
        n = len(self.clips)
        child = struct.pack('<II', n, 8 + 4 * n) + struct.pack('<%dI' % n, *self.clips)
        data = cstr4(self.name)
        doff = 16 + len(child)
        tot = doff + len(data)
        return struct.pack('<IIII', 5, F_CHILDREN | tot, doff, 1) + child + data


# ----------------------------------------------------------------------------------------------
# type 6 : animation database
# ----------------------------------------------------------------------------------------------
class Database:
    """type-6 plain chunk. payload:
         name (cstr4) | u32 nLists | nLists variant lists | u32 reserved (0) | u32 nIds | u32 off[nIds]
       variant list = (u32 key, u32 clipIndex)* terminated by an entry with key==0 (whose clip is the
       default).  off[nameId] = byte offset of the list relative to the nLists field, 0xFFFFFFFF = none.
       key bits 3..31 = condition mask (all must be set in the actor's state flags, actor+0x84),
       bits 0..2 = weight modifiers (bit2 -> w=0.1, bit1 -> w*=0.33, bit0 -> w*=0.5; base 1.0).
       Evidence: DD 0x824d00 (lookup), 0x864750 (holder init), 0x876940 (id->list), 0x7c6750 (select);
                 DM 0x524360, 0x4290b0."""
    type = 6
    NONE = 0xFFFFFFFF

    def __init__(self, name, lists=None, index=None, reserved=0):
        self.name = name
        self.lists = lists if lists is not None else []      # list of [(key, clip), ...] incl. terminator
        self.index = index if index is not None else []      # nameId -> list number or None
        self.reserved = reserved

    @property
    def short(self):
        return self.name[len(DB_PREFIX):] if self.name.startswith(DB_PREFIX) else self.name

    @classmethod
    def parse(cls, b, o):
        sf = u32(b, o + 4)
        if sf & 0xC0000000:
            raise AnmError('type6 flags %x' % sf)
        tot = sf & SIZE_MASK
        end = o + tot
        name, e = read_cstr(b, o + 8)
        q = (e + 1 + 3) & ~3
        if b[e:q] != b'\0' * (q - e):
            raise AnmError('type6 name pad')
        base = q
        n = u32(b, q); q += 4
        lists, starts = [], {}
        for _ in range(n):
            starts[q - base] = len(lists)
            lst = []
            while True:
                k, c = u32(b, q), u32(b, q + 4); q += 8
                lst.append((k, c))
                if k == 0:
                    break
            lists.append(lst)
        reserved = u32(b, q); q += 4
        cnt = u32(b, q); q += 4
        offs = struct.unpack_from('<%dI' % cnt, b, q); q += 4 * cnt
        if q != end:
            raise AnmError('type6 size mismatch %d' % (end - q))
        index = []
        for x in offs:
            if x == cls.NONE:
                index.append(None)
            elif x in starts:
                index.append(starts[x])
            else:
                raise AnmError('type6 offset not at list start')
        return cls(name, lists, index, reserved), tot

    def build(self):
        out = [cstr4(self.name), U32.pack(len(self.lists))]
        offs, pos = [], 4
        for lst in self.lists:
            if not lst or lst[-1][0] != 0 or any(k == 0 for k, _ in lst[:-1]):
                raise AnmError('bad variant list in %r' % self.name)
            offs.append(pos)
            out.append(b''.join(struct.pack('<II', k, c) for k, c in lst))
            pos += 8 * len(lst)
        out.append(U32.pack(self.reserved))
        out.append(U32.pack(len(self.index)))
        out.append(b''.join(U32.pack(self.NONE if i is None else offs[i]) for i in self.index))
        payload = b''.join(out)
        return struct.pack('<II', 6, 8 + len(payload)) + payload

    def referenced_clips(self):
        return {c for lst in self.lists for _, c in lst}

    def get(self, name_id):
        if 0 <= name_id < len(self.index) and self.index[name_id] is not None:
            return self.lists[self.index[name_id]]
        return None

    def set(self, name_id, lst):
        while len(self.index) <= name_id:
            self.index.append(None)
        self.lists.append(list(lst))
        self.index[name_id] = len(self.lists) - 1

    @staticmethod
    def select(lst, mask, rnd=0.0):
        """engine variant selection (DD 0x7c6750 / DM 0x4290b0): returns (clip, default_clip)"""
        cands, grp, wsum = [], None, 0.0
        for k, c in lst:
            cond = k & ~7
            if cond & mask == cond and (grp is None or grp == cond):
                w = 0.1 if k & 4 else 1.0
                if k & 2: w *= 0.33
                if k & 1: w *= 0.5
                grp = cond; wsum += w; cands.append((wsum, c))
            if k == 0:
                break
        default = lst[-1][1]
        if not cands:
            return None, default
        t = rnd * wsum
        for acc, c in cands:
            if t < acc:
                return c, default
        return cands[-1][1], default


# ----------------------------------------------------------------------------------------------
# type 7 : animation path name table
# ----------------------------------------------------------------------------------------------
class NameTable:
    """type-7 plain chunk. payload: u32 n | n x (u32 strOffset, u32 nameId) sorted by string
    (unsigned strcmp, binary searched by DD 0x68a730) | string block: names in nameId order, each
    NUL-terminated and padded to 4.  strOffset is relative to the string block.  The nameId is the
    index into every Database's off[] table.  Located by DD 0x534ea0 / DM 0x4293a0."""
    type = 7

    def __init__(self, names):
        self.names = list(names)                  # index = nameId
        self._rebuild()

    def _rebuild(self):
        self.ids = {n: i for i, n in enumerate(self.names)}

    @classmethod
    def parse(cls, b, o):
        sf = u32(b, o + 4)
        if sf & 0xC0000000:
            raise AnmError('type7 flags')
        tot = sf & SIZE_MASK
        n = u32(b, o + 8)
        ent = [struct.unpack_from('<II', b, o + 12 + 8 * k) for k in range(n)]
        sb = o + 12 + 8 * n
        names = [None] * n
        for so, i in ent:
            names[i], _ = read_cstr(b, sb + so)
        if None in names:
            raise AnmError('type7 ids not a permutation')
        nt = cls(names)
        if nt.build() != b[o:o + tot]:
            raise AnmError('type7 not canonical')
        return nt, tot

    def build(self):
        offs, blk, pos = [], [], 0
        for s in self.names:
            e = cstr4(s); offs.append(pos); blk.append(e); pos += len(e)
        order = sorted(range(len(self.names)), key=lambda i: self.names[i])
        ent = b''.join(struct.pack('<II', offs[i], i) for i in order)
        payload = U32.pack(len(self.names)) + ent + b''.join(blk)
        return struct.pack('<II', 7, 8 + len(payload)) + payload

    def id_of(self, s):
        return self.ids.get(s)

    def add(self, s):
        i = self.ids.get(s)
        if i is None:
            i = len(self.names); self.names.append(s); self.ids[s] = i
        return i


# ----------------------------------------------------------------------------------------------
# type 4 : clip data
# ----------------------------------------------------------------------------------------------
class AnimData:
    """type-4 plain chunk. payload:
         u32 hdr[13] | ClipRecord[N] | B (clip blobs) | C bone names | D clip names | E morph names | F
       hdr: 0 N, 1 |B|, 2 |C|, 3 |D|, 4 |E|, 5 |F|, 6 #C, 7 #D(=N), 8 #E, 9 #F, 10..12 unknown sizes
       C/D/E: NUL separated strings, block padded to 4.  Loader: DM 0x5be690, DD 0x7079f0.
       Clip records: DM 0x50 bytes, DD 0x68 bytes (the only structural DM/DD difference)."""
    type = 4

    def __init__(self, rs, hdr, recs, B, C, D, E, F):
        self.rs, self.hdr, self.recs, self.B = rs, list(hdr), recs, B
        self.C, self.D, self.E, self.F = C, D, E, F

    @property
    def variant(self):
        return 'dd' if self.rs == REC_DD else 'dm'

    @staticmethod
    def _names(blk, cnt):
        parts = blk.split(b'\0')
        if len(parts) < cnt:
            raise AnmError('name block too short')
        names = parts[:cnt]
        if pad4(b''.join(n + b'\0' for n in names)) != blk:
            raise AnmError('name block not canonical')
        return names

    @staticmethod
    def _blk(names):
        return pad4(b''.join(n + b'\0' for n in names))

    @classmethod
    def parse(cls, b, o, rs=None):
        sf = u32(b, o + 4)
        if sf & 0xC0000000:
            raise AnmError('type4 flags')
        tot = sf & SIZE_MASK
        p = o + 8
        hdr = struct.unpack_from('<13I', b, p)
        n = hdr[0]
        rest = sum(hdr[1:6])
        if rs is None:
            for cand in (REC_DD, REC_DM):
                if 52 + n * cand + rest == tot - 8:
                    rs = cand
            if rs is None:
                raise AnmError('cannot determine clip record size')
        if 52 + n * rs + rest != tot - 8:
            raise AnmError('type4 size mismatch')
        q = p + 52
        recs = [list(struct.unpack_from('<%dI' % (rs // 4), b, q + i * rs)) for i in range(n)]
        q += n * rs
        B = b[q:q + hdr[1]]; q += hdr[1]
        C = cls._names(b[q:q + hdr[2]], hdr[6]); q += hdr[2]
        D = cls._names(b[q:q + hdr[3]], hdr[7]); q += hdr[3]
        E = cls._names(b[q:q + hdr[4]], hdr[8]); q += hdr[4]
        F = b[q:q + hdr[5]]; q += hdr[5]
        if hdr[7] != n or hdr[9] != 0 or hdr[5] != 0:
            raise AnmError('unexpected type4 header %r' % (hdr,))
        return cls(rs, hdr, recs, B, C, D, E, F), tot

    def build(self):
        h = self.hdr
        Cb, Db, Eb = self._blk(self.C), self._blk(self.D), self._blk(self.E)
        h[0], h[1], h[2], h[3], h[4], h[5] = len(self.recs), len(self.B), len(Cb), len(Db), len(Eb), len(self.F)
        h[6], h[7], h[8] = len(self.C), len(self.D), len(self.E)
        if h[7] != h[0]:
            raise AnmError('clip/name count mismatch')
        w = self.rs // 4
        recs = b''.join(struct.pack('<%dI' % w, *r) for r in self.recs)
        payload = struct.pack('<13I', *h) + recs + self.B + Cb + Db + Eb + self.F
        return struct.pack('<II', 4, 8 + len(payload)) + payload

    # --- clip helpers -------------------------------------------------------------------------
    def frames(self, i):
        return self.recs[i][0] >> 16

    def n_events(self, i):
        return self.recs[i][1] >> 16

    def flags(self, i):
        return self.recs[i][2]

    def blob_span(self, i):
        """(start, size) of the clip's data in B: events (8 bytes each) immediately followed by the
        track block; record field 9 is the total size.  Several clips may share one blob."""
        r = self.recs[i]
        start = r[4] if self.n_events(i) else r[3]
        if self.n_events(i) and r[3] != r[4] + 8 * self.n_events(i):
            raise AnmError('clip %d: events not adjacent to tracks' % i)
        return start, r[9]

    def events(self, i):
        r = self.recs[i]
        return [struct.unpack_from('<IHh', self.B, r[4] + 8 * k) for k in range(self.n_events(i))]

    def track_block(self, i):
        """returns dict describing the track block of clip i (offsets relative to its start p)."""
        r = self.recs[i]
        p = r[3]
        B = self.B
        if r[2] & 0x10:      # baked-matrix layout (DM 0x5be9a0 / 0x5bfa90): u32 n, u32 bone[n], 7 floats per bone per frame
            n = u32(B, p)
            return dict(baked=True, p=p, n=n, bones=list(struct.unpack_from('<%dI' % n, B, p + 4)))
        hz = struct.unpack_from('<5I', B, p)
        dur = struct.unpack_from('<f', B, p + 0x14)[0]
        nfr, ntr, nch = u32(B, p + 0x18), u32(B, p + 0x1c), u32(B, p + 0x20)
        tracks = [struct.unpack_from('<5I', B, p + 0x24 + 0x14 * k) for k in range(ntr)]
        x = p + 0x24 + 0x14 * ntr
        chans = [struct.unpack_from('<3I', B, x + 12 * k) for k in range(nch)]
        return dict(baked=False, p=p, zero=hz, duration=dur, frames=nfr, tracks=tracks, channels=chans,
                    reserved=B[x + 12 * nch:x + 12 * nch + 36])

    def to_dict_record(self, i):
        return ClipRecord.unpack(self.recs[i], self.rs)


class ClipRecord:
    """Field map (u32 index -> meaning).  DM record = 20 u32, DD record = 26 u32.
         0  u16 lo: unknown (0..1607, same value in DM and DD for the same clip) | u16 hi: frame count
         1  u16 lo: fps (25, a few 24)                                            | s16 hi: event count
         2  flags: 0x1 looping(?) 0x8/0x40/0x80 unknown, 0x10 baked-matrix layout,
                   DD only: 0x1000 = pose vectors valid (A,P,A2,P2 used by DD 0x8b4200), 0x800 see spec
         3  track block offset in B            4  event table offset in B (DD stores a dummy for 0 events)
         5  float (0..10)                      6-8 vec3 (root offset?)            9  blob size (events+tracks)
         10 0/8/24                             11 u32 (same in DM/DD for same clip)
       DM: 12-14 A (unit vec, 'start')  15-17 P (vec3 'start')  18 float (~96.7)  19 name ptr (0 in file)
       DD: 12-14 A start  15-17 A end   18-20 P start  21-23 P end  24 float (~96.7)  25 name ptr (0)
       A/P are blended over the active clips by DM 0x5c4b40 (start values only) and by DD 0x8b4200
       (start->end lerp by normalised clip time, only for clips with flag 0x1000)."""

    @staticmethod
    def unpack(r, rs):
        f = lambda x: struct.unpack('<f', struct.pack('<I', x))[0]
        d = dict(u0=r[0] & 0xffff, frames=r[0] >> 16, fps=r[1] & 0xffff, events=r[1] >> 16, flags=r[2],
                 track_off=r[3], event_off=r[4], f5=f(r[5]), v6=[f(x) for x in r[6:9]], size=r[9], f10=r[10],
                 f11=r[11])
        if rs == REC_DM:
            d.update(A=[f(x) for x in r[12:15]], P=[f(x) for x in r[15:18]], f_end=f(r[18]))
        else:
            d.update(A=[f(x) for x in r[12:15]], A2=[f(x) for x in r[15:18]], P=[f(x) for x in r[18:21]],
                     P2=[f(x) for x in r[21:24]], f_end=f(r[24]))
        return d


class RawChunk:
    def __init__(self, type_, raw):
        self.type, self.raw = type_, raw

    def build(self):
        return self.raw


# ----------------------------------------------------------------------------------------------
# whole file
# ----------------------------------------------------------------------------------------------
class AnmFile:
    def __init__(self, entries):
        self.entries = entries

    # -- accessors --
    @property
    def anim(self):
        return next(e for e in self.entries if isinstance(e, AnimData))

    @property
    def names(self):
        return next(e for e in self.entries if isinstance(e, NameTable))

    @property
    def dbs(self):
        return [e for e in self.entries if isinstance(e, Database)]

    @property
    def variant(self):
        return self.anim.variant

    def find_db(self, req):
        """engine lookup (DD 0x824d00 / DM 0x524360): first type-6 whose name ends with the
        requested string, case-insensitive (DD 0x80b970 -> _stricmp)."""
        r = req.lower() if isinstance(req, bytes) else req.encode().lower()
        for db in self.dbs:
            if db.name.lower().endswith(r):
                return db
        return None

    def db_by_short(self, short):
        s = short if isinstance(short, bytes) else short.encode()
        for db in self.dbs:
            if db.short == s:
                return db
        return None

    def resolve(self, db, path, mask=0xFFFFFFF8):
        """path -> list of clip indices the DB can return (all variants) or None"""
        p = path if isinstance(path, bytes) else path.encode()
        i = self.names.id_of(p)
        if i is None:
            return None
        lst = db.get(i)
        return None if lst is None else lst

    # -- parse / build --
    @classmethod
    def parse(cls, b, rs=None):
        if u32(b, 0) != MAGIC:
            raise AnmError('bad magic')
        sf = u32(b, 4)
        if sf != (F_CHILDREN | len(b)) or u32(b, 8) != len(b):
            raise AnmError('root header/size mismatch')
        n = u32(b, 12)
        o, ents = 16, []
        for _ in range(n):
            t = u32(b, o)
            if t == 5:
                e, sz = DBList.parse(b, o)
            elif t == 6:
                e, sz = Database.parse(b, o)
            elif t == 7:
                e, sz = NameTable.parse(b, o)
            elif t == 4:
                e, sz = AnimData.parse(b, o, rs)
            else:
                sz = u32(b, o + 4) & SIZE_MASK
                e = RawChunk(t, b[o:o + sz])
            ents.append(e)
            o += sz
        if o != len(b):
            raise AnmError('trailing data')
        f = cls(ents)
        f.check_dblists()
        return f

    def recompute_dblists(self):
        """type-5 list = sorted clips referenced by the DB and by no earlier DB."""
        seen = set()
        pending = None
        for e in self.entries:
            if isinstance(e, DBList):
                pending = e
            elif isinstance(e, Database):
                refs = e.referenced_clips()
                if pending is None or pending.name != e.name:
                    raise AnmError('type5/type6 pairing broken at %r' % e.name)
                pending.clips = sorted(refs - seen)
                seen |= refs
                pending = None

    def check_dblists(self):
        seen, pending, bad = set(), None, []
        for e in self.entries:
            if isinstance(e, DBList):
                pending = e
            elif isinstance(e, Database):
                refs = e.referenced_clips()
                if pending is None or pending.name != e.name or list(pending.clips) != sorted(refs - seen):
                    bad.append(e.name)
                seen |= refs
                pending = None
        self.dblist_mismatch = bad
        return bad

    def build(self, recompute=True):
        if recompute:
            self.recompute_dblists()
        body = b''.join(e.build() for e in self.entries)
        tot = 16 + len(body)
        return struct.pack('<IIII', MAGIC, F_CHILDREN | tot, tot, len(self.entries)) + body

    # -- convenience --
    def add_db(self, db):
        """insert a new (type5,type6) pair.  The engine returns the FIRST database whose name ends
        (case-insensitively) with the requested name, so the new DB is placed after every DB whose
        short name is a suffix of its own and before every DB that has its short name as a suffix
        (e.g. 'Police' must precede 'HG_Revolver_Police').  Otherwise it goes after the last DB.
        Returns False if no position satisfies both constraints (DB placed last, will be shadowed)."""
        dbi = [i for i, e in enumerate(self.entries) if isinstance(e, Database)]
        me = db.short.lower()
        lo = dbi[-1]                       # default: after the last DB
        must_follow = [i for i in dbi if me.endswith(self.entries[i].short.lower())]
        must_precede = [i for i in dbi if self.entries[i].short.lower().endswith(me)]
        ok = True
        if must_precede:
            pos = must_precede[0] - 1      # the type-5 entry before that DB
            if must_follow and max(must_follow) > pos:
                ok = False
                pos = dbi[-1] + 1
        else:
            pos = lo + 1
        self.entries[pos:pos] = [DBList(db.name, []), db]
        return ok


def load(path, rs=None):
    with open(path, 'rb') as fh:
        return AnmFile.parse(fh.read(), rs)


def summary(f):
    a = f.anim
    lines = ['variant %s  clips %d  B %d  bones %d  morph %d  names %d  dbs %d' % (
        a.variant, len(a.recs), len(a.B), len(a.C), len(a.E), len(f.names.names), len(f.dbs))]
    for db in f.dbs:
        lines.append('  %-32s lists %5d ids %5d clips %5d' % (db.short.decode(), len(db.lists), len(db.index),
                                                            len(db.referenced_clips())))
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        print(p)
        print(summary(load(p)))
