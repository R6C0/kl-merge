"""
Animation file (.ANM) of Kane & Lynch: Dead Men (dm) and Dog Days (dd): read, write (byte-identical on
all 41 stock files), convert Dead Men -> Dog Days, and merge Dead Men collections into a Dog Days file.

  python kl_anm.py check                      round trip + layout checks on every stock level of both games
  python kl_anm.py compare <dm level> <dd level>   converted Dead Men clip headers against Dog Days' own
  python kl_anm.py convert <dm.ANM> <out.ANM>
  python kl_anm.py merge <dd.ANM> <dm.ANM> <out.ANM> Name[=NewName] ...
  python kl_anm.py info <file.ANM>

Sources: (exe) = read in the disassembly, kl2.exe / kaneandlynch.exe addresses; (data) = counted over the
20 Dead Men + 21 Dog Days stock files (33,682 + 66,261 clips, 909 collections); GUESS = not established.

FILE  chunk file: {type, flags|extent, ...}. Root 'ANM\\0' (flags bit 31, +8 extent again, +0xC child
count), children from +0x10 in this order (data, 41/41): one (type 5, type 6) pair per collection, then
one type 7, then one type 4. Finder by type: kl2 0x74f710 / dm 0x4318e0; the level loader (kl2 0x820300,
dm 0x4594e0) asks only for type 4. The code that consumes types 5, 6, 7 was NOT found: their layout
below is from data (every rule holds on all 909 collections / 41 files), their meaning partly a GUESS.

  type 5  collection clip list: {5, 0x80000000|extent, +8 name offset, 1} + child chunk
          {type = n, extent = 8+4n, n clip indices (sorted, unique)} + name 'anmcol:animationdatabase#X'.
          The lists PARTITION the clips (data, 909 collections / 41 files, no exception): a collection
          lists exactly the clips its type 6 pool names that no EARLIER collection of the file lists
          (so the first collection holds the bulk, 'Generic' / 'SIG_552' may list none). relist()
          writes that rule; audit() checks it.
  type 6  collection: name, then K = number of used slots, a pool of (condition flags, clip index)
          pairs, one 0 dword, S, and S slot entries: -1 or the byte offset (from K) of the slot's first
          pair. A slot's list runs to the first pair with flags 0 (the default). S <= slot count.
          The condition bits (weapon / stance?) are NOT decoded and may differ between the games: GUESS.
  type 7  slot names, shared by all collections of the file: N, N x {string offset, slot id} sorted by
          name, strings in id order, each padded to 4. kl2 0x68a730 is a binary search over exactly this
          shape (name -> u16; reached from the player setup 0x493700 -> 0x770ba0 -> 0x426890). Slot ids
          are per file: '/Cover/Low/Low/Cover_Switch_L_To_R_Short' -> id -> collection table -> clip.
  type 4  manager block, read by kl2 0x7079f0 / dm 0x5be690 (exe; identical but for the clip size):
          13 dwords: 0 clip count, 1 data size, 2 / 3 / 4 byte sizes of the bone / clip / pose name
          tables, 5 (0 everywhere; non-zero would mean a further table after the pose names), 6 bone
          count, 7 clip name count (= clip count), 8 pose count, 9, 10, 11, 12. Dwords 10 and 11 vary
          per level (0 in six Dog Days levels), 9 and 12 are 0; the loader only stores them and no
          reader was found: NOT understood, kept as they are.
          Then the clip records (0x50 dm / 0x68 dd), the data block, the three name tables (NUL
          separated, each table padded to 4). The loader walks the clip names in order and stores each
          clip's name pointer into its record (dm +0x4C, dd +0x64): that dword is 0 in the file.

CLIP RECORD (dm offsets; dd is the same up to +0x2F)
  +0x00 s16 ?   +0x02 s16 frames   +0x04 s16 frames per second   +0x06 s16 event count
  +0x08 flags: 0x10 = uncompressed data (exe; no stock clip has it), 0x1000 = Dog Days only, set
        exactly when the vectors below are non-zero (data, 66,261/66,261; tested at kl2 0x8b427d)
  +0x0C offset of the clip's data in the data block (exe: kl2 0x901850, dm 0x5be830)
  +0x10 offset of the event table = +0x0C - 8 * events (data: every clip with events, both games);
        entries {u32 event id, u16 frame, u16 ?} (exe: kl2 0x4a75d0 / 0x89f480, dm 0x5bfa00 / 0x5bf9d0).
        Meaningless without events - that is the "large negative" value of Dead Men.
  +0x14 float, +0x18 vec3  +0x24 size of events + data; 0 = alias of the clip of the same name whose
        data starts at the same +0x0C (data: 2,767 dm + 24,843 dd records)  +0x28 0 / 8 / 24 (follows the flags)
  +0x2C non-zero in 14% (dm) / 38% (dd) of clips, values in steps of ~144, no reader found: NOT
        understood, copied.
  +0x30 vec3, +0x3C vec3   dd: +0x30 and +0x3C are the first vector at clip start and end, +0x48 and
        +0x54 the second (kl2 0x8b4200 blends start -> end, or takes the start alone if flags bit 0).
  +0x48 float -> dd +0x60   +0x4C name pointer -> dd +0x64
  Dead Men has one value per vector, so convert() writes it to both start and end: exact for loops,
  an approximation for one-shot clips (compare prints how often Dog Days' own end differs).

CLIP DATA (same in both games: 2,622 same-named clips of M01FAA/M09A/M02FAA vs F01/L03/L07 have
byte-identical event + data blocks): +0x14 float seconds, +0x18 frames, +0x1C tracks, +0x20 pose
tracks, +0x24 tracks x {4 offsets, bone index}, then pose tracks x {2 offsets, pose index}. The bone
index points into THIS file's bone name table (0x39 = GROUND is hard-coded: kl2 0x5a5060, dm
0x5bfab3), and the tables differ per level, so merge() renumbers the tracks. Pose index -> pose name
table is a GUESS (the reader goes through a caller-supplied word map, dm 0x5be8e6).
Event ids are an enum inside the exe; that both games number it alike is a GUESS backed only by the
identical blocks above.
"""
import struct, sys

CLIP = {'dm': 0x50, 'dd': 0x68}
ROOT = 0x00414e4d                                       # b"MNA\0" on disk
PREFIX = 'anmcol:animationdatabase#'


def pad4(b):
    return b + b'\0' * (-len(b) % 4)


def ztable(names):
    return pad4(b''.join(n.encode('latin1') + b'\0' for n in names))


def zsplit(raw, count):
    """The first `count` names of a NUL-separated table; the rest must be padding."""
    parts = raw.split(b'\0')
    names = [p.decode('latin1') for p in parts[:count]]
    if ztable(names) != raw:
        raise ValueError('name table is not %d names padded to 4' % count)
    return names


class Collection:
    """name (without the 'anmcol:animationdatabase#' prefix is .short), clips = the type 5 index list,
    pool = [(flags, clip)], table[slot] = index of the slot's first pool pair or -1."""

    def __init__(self, name, clips, pool, table):
        self.name, self.clips, self.pool, self.table = name, list(clips), list(pool), list(table)

    @property
    def short(self):
        return self.name.split('#', 1)[-1]

    def lists(self):
        """{slot id: [(flags, clip), ...]} - each list ends with its flags == 0 pair."""
        out = {}
        for slot, i in enumerate(self.table):
            if i >= 0:
                j = i
                while self.pool[j][0]:
                    j += 1
                out[slot] = self.pool[i:j + 1]
        return out

    def chunks(self):
        name = pad4(self.name.encode('latin1') + b'\0')
        n = len(self.clips)
        c5 = struct.pack('<6I', 5, 0x80000000 | (0x18 + 4 * n + len(name)), 0x18 + 4 * n, 1, n, 8 + 4 * n)
        c5 += struct.pack('<%dI' % n, *self.clips) + name
        body = struct.pack('<I', sum(1 for i in self.table if i >= 0))
        body += b''.join(struct.pack('<II', f, c) for f, c in self.pool)
        body += struct.pack('<II', 0, len(self.table))
        body += struct.pack('<%di' % len(self.table), *[-1 if i < 0 else 4 + 8 * i for i in self.table])
        return c5 + struct.pack('<II', 6, 8 + len(name) + len(body)) + name + body


class Anm:
    """game 'dm' / 'dd'; cols [Collection]; slots [name by slot id]; head = the 13 manager dwords;
    clips [bytearray record]; names [clip name]; data = the data block; bones, poses [name]."""

    def __init__(self, raw, game=None):
        typ, flags, ext, count = struct.unpack_from('<4I', raw, 0)
        if typ != ROOT or flags != 0x80000000 | len(raw) or ext != len(raw):
            raise ValueError('not an .ANM chunk file')
        top, o = [], 0x10
        for _ in range(count):
            t, f = struct.unpack_from('<II', raw, o)
            top.append((t, f >> 30, o, o + (f & 0x3fffffff)))
            o = top[-1][3]
        kinds = [t[0] for t in top]
        if o != len(raw) or kinds != [5, 6] * ((count - 2) // 2) + [7, 4]:
            raise ValueError('unexpected chunk order %r' % kinds[-6:])
        # type 7: slot names
        _, _, o, end = top[-2]
        n = struct.unpack_from('<I', raw, o + 8)[0]
        ent = struct.unpack_from('<%dI' % (2 * n), raw, o + 12)
        pool = o + 12 + 8 * n
        self.slots = [None] * n
        for i in range(n):
            s = pool + ent[2 * i]
            self.slots[ent[2 * i + 1]] = raw[s:raw.index(b'\0', s)].decode('latin1')
        # collections
        self.cols = []
        for (_, f5, o5, e5), (_, f6, o6, e6) in zip(top[0:-2:2], top[1:-2:2]):
            dofs, one, m, cext = struct.unpack_from('<4I', raw, o5 + 8)
            name = raw[o5 + dofs:raw.index(b'\0', o5 + dofs)].decode('latin1')
            clips = struct.unpack_from('<%dI' % m, raw, o5 + 0x18)
            p = o6 + 8 + len(pad4(name.encode('latin1') + b'\0'))
            d = struct.unpack_from('<%di' % ((e6 - p) // 4), raw, p)
            # the table length S stands right before the table; the pool has an odd number of dwords
            # (pairs + the 0), so S is the first self-consistent count seen walking back from the end
            at = next(i for i in range(len(d) - 1, 0, -1) if d[i] == len(d) - 1 - i and i % 2 == 0 and d[i - 1] == 0)
            pairs = [(d[i] & 0xffffffff, d[i + 1]) for i in range(1, at - 1, 2)]
            table = [-1 if x < 0 else (x - 4) // 8 for x in d[at + 1:]]
            self.cols.append(Collection(name, clips, pairs, table))
        # type 4: manager
        _, _, o, end = top[-1]
        m = o + 8
        self.head = h = list(struct.unpack_from('<13i', raw, m))
        fits = [g for g in CLIP if m + 0x34 + h[0] * CLIP[g] + h[1] + h[2] + h[3] + h[4] == end]
        if game is None and len(fits) != 1 or game is not None and game not in fits:
            raise ValueError('clip record size does not fit: %r' % fits)
        self.game = game or fits[0]
        size = CLIP[self.game]
        p = m + 0x34
        self.clips = [bytearray(raw[p + i * size:p + (i + 1) * size]) for i in range(h[0])]
        p += h[0] * size
        self.data = raw[p:p + h[1]]
        p += h[1]
        self.bones = zsplit(raw[p:p + h[2]], h[6])
        self.names = zsplit(raw[p + h[2]:p + h[2] + h[3]], h[7])
        self.poses = zsplit(raw[p + h[2] + h[3]:end], h[8])
        if h[7] != h[0]:
            raise ValueError('clip name count differs from clip count')

    def save(self):
        out = [c.chunks() for c in self.cols]
        order = sorted(range(len(self.slots)), key=lambda i: self.slots[i].encode('latin1'))
        offs, strings = [], b''
        for s in self.slots:
            offs.append(len(strings))
            strings += pad4(s.encode('latin1') + b'\0')
        body = struct.pack('<I', len(order)) + b''.join(struct.pack('<II', offs[i], i) for i in order) + strings
        out.append(struct.pack('<II', 7, 8 + len(body)) + body)
        bones, names, poses = ztable(self.bones), ztable(self.names), ztable(self.poses)
        h = self.head
        h[0] = h[7] = len(self.clips)
        h[1], h[2], h[3], h[4], h[6], h[8] = len(self.data), len(bones), len(names), len(poses), len(self.bones), len(self.poses)
        body = struct.pack('<13i', *h) + b''.join(bytes(c) for c in self.clips) + bytes(self.data) + bones + names + poses
        out.append(struct.pack('<II', 4, 8 + len(body)) + body)
        size = 0x10 + sum(map(len, out))
        return struct.pack('<4I', ROOT, 0x80000000 | size, size, 2 * len(self.cols) + 2) + b''.join(out)

    # clip record fields (the same offsets in both games)
    def events(self, i):
        return struct.unpack_from('<h', self.clips[i], 6)[0]

    def flags(self, i):
        return struct.unpack_from('<I', self.clips[i], 8)[0]

    def block(self, i):
        """(start, size) of clip i's events + data in the data block; None if it lies outside."""
        off, size = struct.unpack_from('<i', self.clips[i], 0xc)[0], struct.unpack_from('<i', self.clips[i], 0x24)[0]
        start = off - 8 * max(self.events(i), 0)
        return (start, size) if 0 <= start and size >= 0 and start + size <= len(self.data) else None

    def col(self, name):
        hit = [c for c in self.cols if name in (c.name, c.short)]
        if len(hit) != 1:
            raise KeyError('collection %r: %d matches among %s' % (name, len(hit), [c.short for c in self.cols]))
        return hit[0]

    def lookup(self, collection, slot_name, flags=0):
        """Clip index a collection plays for a slot name: the pair whose flags match, else the default."""
        lst = self.col(collection).lists().get(self.slots.index(slot_name))
        return None if lst is None else next((c for f, c in lst if f == flags), lst[-1][1])


def tracks(data, start, events):
    """Positions of the bone indices and pose indices inside a clip's data (see CLIP DATA)."""
    o = start + 8 * events
    n, n2 = struct.unpack_from('<ii', data, o + 0x1c)
    return [o + 0x34 + 0x14 * k for k in range(n)], [o + 0x24 + 0x14 * n + 8 + 0xc * k for k in range(n2)]


def owners(a):
    """{data offset: ((block start, size), events)} of the clips that own data. A record with size 0 is
    an alias: its +0x0C is the data offset of another clip of the same name and frame count (data:
    2,767 dm + 24,843 dd records, no exception) and its events, if any, are that clip's."""
    out = {}
    for i in range(len(a.clips)):
        b, ev = a.block(i), max(a.events(i), 0)
        if b and b[1]:
            out.setdefault(b[0] + 8 * ev, (b, ev))
    return out


def convert(dm):
    """Dead Men file -> Dog Days layout. Only the clip records change (see CLIP RECORD): the two vectors
    are written as start AND end value, 0x1000 is set where they are non-zero. Data, events, names,
    collections and slot names are the same format and stay as they are."""
    if isinstance(dm, (bytes, bytearray)):
        dm = Anm(dm)
    if dm.game != 'dm':
        raise ValueError('convert() wants a Dead Men file')
    out = Anm(dm.save())
    out.game = 'dd'
    for i, c in enumerate(dm.clips):
        r = bytearray(c[:0x30] + c[0x30:0x3c] * 2 + c[0x3c:0x48] * 2 + c[0x48:0x50])
        if any(c[0x30:0x48]):
            struct.pack_into('<I', r, 8, dm.flags(i) | 0x1000)
        out.clips[i] = r
    return out


def merge(dd, dm, wanted, reuse=True):
    """dd + the Dead Men collections in `wanted` ([name] or {name: new name}; names with or without
    the 'anmcol:animationdatabase#' prefix) and the clips they list. Returns a new Dog Days Anm.
    - clips: appended after Dog Days' own (indices of stock clips do not move). With reuse, a Dead Men
      clip whose name and whole event + data block equal a Dog Days clip's uses that clip instead.
    - data: each distinct block appended; record +0x0C / +0x10 point at the copy (alias records at
      their owner's copy); bone and pose indices of its tracks renumbered into the merged name tables (missing names appended).
    - slot names: Dead Men names missing in the file get new ids after the existing ones, so no stock
      collection table changes; the new collections are renumbered to the merged ids.
    A collection name that already exists must be given a new name (and the level's properties must
    then ask for that name)."""
    if dm.game == 'dm':
        dm = convert(dm)
    out = Anm(dd.save())
    if out.game != 'dd':
        raise ValueError('merge() wants a Dog Days file as base')
    wanted = dict(wanted) if isinstance(wanted, dict) else {w: w for w in wanted}
    cols = [(dm.col(k), PREFIX + v.split('#', 1)[-1]) for k, v in wanted.items()]
    have = {c.name for c in out.cols}
    for _, new in cols:
        if new in have:
            raise ValueError('%s exists in the Dog Days file: merge it under another name' % new)
        have.add(new)
    bone = {n: i for i, n in reversed(list(enumerate(out.bones)))}
    pose = {n: i for i, n in reversed(list(enumerate(out.poses)))}
    slot = {n: i for i, n in enumerate(out.slots)}

    def index(table, names, name):
        if name not in table:
            table[name] = len(names)
            names.append(name)
        return table[name]

    data = bytearray(out.data)
    mine = {}                                           # Dog Days clips by (name, block bytes)
    if reuse:
        for i, n in enumerate(out.names):
            b = out.block(i)
            if b and b[1]:
                mine.setdefault((n, out.data[b[0]:b[0] + b[1]]), i)
    owner = owners(dm)
    placed, clipmap = {}, {}                            # block -> (data offset in the merged block, stock clip or None)
    need = sorted({c for col, _ in cols for c in list(col.clips) + [p[1] for p in col.pool]})
    for i in need:
        rec, ev = bytearray(dm.clips[i]), max(dm.events(i), 0)
        if dm.flags(i) & 0x10:
            raise ValueError('clip %d (%s) is uncompressed: its bone list is not handled' % (i, dm.names[i]))
        blk, oev = owner[struct.unpack_from('<i', rec, 0xc)[0]]
        if blk not in placed:
            b = bytearray(dm.data[blk[0]:blk[0] + blk[1]])
            bones, poses = tracks(b, 0, oev)
            for p in bones:
                struct.pack_into('<i', b, p, index(bone, out.bones, dm.bones[struct.unpack_from('<i', b, p)[0]]))
            for p in poses:
                struct.pack_into('<i', b, p, index(pose, out.poses, dm.poses[struct.unpack_from('<i', b, p)[0]]))
            hit = mine.get((dm.names[i], bytes(b)))
            if hit is None:
                placed[blk] = len(data) + 8 * oev, None
                data += b
            else:
                placed[blk] = struct.unpack_from('<i', out.clips[hit], 0xc)[0], hit
        at, hit = placed[blk]
        if hit is not None and out.names[hit] == dm.names[i]:
            clipmap[i] = hit
            continue
        struct.pack_into('<ii', rec, 0xc, at, at - 8 * ev)
        clipmap[i] = len(out.clips)
        out.clips.append(rec)
        out.names.append(dm.names[i])
    out.data = bytes(data)
    if len(out.bones) > 255:                            # the uncompressed-clip reader maps bone index -> u8 (kl2 0x5a50..): limit not established
        print('warning: %d bone names in the merged table' % len(out.bones), file=sys.stderr)
    for col, new in cols:
        table = {}
        for s, first in enumerate(col.table):
            if first >= 0:
                table[index(slot, out.slots, dm.slots[s])] = first
        out.cols.append(Collection(new, [], [(f, clipmap[c]) for f, c in col.pool],
                                   [table.get(s, -1) for s in range(max(table) + 1 if table else 0)]))
    relist(out)                                         # was: the source's list mapped, which listed reused stock clips twice
    return out


def relist(a):
    """Rewrite every type 5 clip list by the rule of the stock files (see FILE, type 5): the clips of
    the collection's pool that no earlier collection lists. On a stock file this changes nothing."""
    seen = set()
    for c in a.cols:
        mine = {clip for _f, clip in c.pool}
        c.clips = sorted(mine - seen)
        seen |= mine
    return a


# ---- checks -------------------------------------------------------------------------------------

def stock():
    """(game, level, bytes) of every stock .ANM; Dog Days' F01 from the backup (the installed one is ours)."""
    import glob, os, zipfile
    from kl_port_check import find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE
    for game, root in (('dm', find(DM_GUESSES, DM_EXE)), ('dd', find(DD_GUESSES, DD_EXE))):
        for z in sorted(glob.glob(os.path.join(glob.escape(root), 'Scenes', 'Locations', '*', '*_Main.zip'))):
            level = os.path.basename(os.path.dirname(z))
            if game == 'dd' and level == 'F01':
                z = os.path.join(root, 'KL_PortBackup', 'Scenes', 'Locations', 'F01', 'F01_Main.zip')
            with zipfile.ZipFile(z) as zf:
                for n in zf.namelist():
                    if n.lower().endswith('.anm'):
                        yield game, level, zf.read(n)


def audit(a):
    """Problems with the layout rules the docstring claims, as a list of strings (empty = all hold)."""
    bad = []
    for c in a.cols:
        used = [i for i in c.table if i >= 0]
        if len(set(used)) != len(used) or any(i >= len(c.pool) for i in used):
            bad.append('%s: slot table entries not distinct pool positions' % c.short)
            continue
        cover = sorted(i + k for i, lst in ((c.table[s], l) for s, l in c.lists().items()) for k in range(len(lst)))
        if cover != list(range(len(c.pool))):
            bad.append('%s: pool is not exactly the slot lists' % c.short)
        if len(c.table) > len(a.slots):
            bad.append('%s: more slots than slot names' % c.short)
        if c.clips != sorted(set(c.clips)) or c.clips and c.clips[-1] >= len(a.clips):
            bad.append('%s: clip list not sorted / out of range' % c.short)
    seen = set()
    for c in a.cols:                                    # type 5 lists: the partition rule
        mine = {clip for _f, clip in c.pool}
        if c.clips != sorted(mine - seen):
            bad.append('%s: clip list is not its pool clips that no earlier collection lists' % c.short)
        seen |= mine
    if len(seen) != len(a.clips):
        bad.append('%d clips that no collection plays' % (len(a.clips) - len(seen)))
    if len(set(c.name for c in a.cols)) != len(a.cols):
        bad.append('duplicate collection names')
    if len(set(a.slots)) != len(a.slots):
        bad.append('duplicate slot names')
    own = owners(a)
    for i in range(len(a.clips)):
        blk, ev = a.block(i), max(a.events(i), 0)
        if struct.unpack_from('<i', a.clips[i], 0xc)[0] not in own:
            bad.append('clip %d %s: no clip owns the data it points at' % (i, a.names[i]))
        if blk is None:
            bad.append('clip %d %s: block outside the data' % (i, a.names[i]))
        elif blk[1]:
            if ev and struct.unpack_from('<i', a.clips[i], 0x10)[0] != blk[0]:
                bad.append('clip %d: event offset is not data offset - 8 * events' % i)
            bones, poses = tracks(a.data, blk[0], ev)
            if 0x24 + 0x14 * len(bones) + 0xc * len(poses) > blk[1] - 8 * ev:
                bad.append('clip %d: track tables larger than the block' % i)
            elif any(not 0 <= struct.unpack_from('<i', a.data, p)[0] < len(a.bones) for p in bones):
                bad.append('clip %d: bone index outside the bone table' % i)
            elif any(not 0 <= struct.unpack_from('<i', a.data, p)[0] < len(a.poses) for p in poses):
                bad.append('clip %d: pose index outside the pose table' % i)
        if a.game == 'dd' and bool(a.flags(i) & 0x1000) != any(a.clips[i][0x30:0x60]):
            bad.append('clip %d: flag 0x1000 does not follow the vectors' % i)
    return bad


def check():
    import collections
    files = same = 0
    notes = collections.Counter()
    for game, level, raw in stock():
        a = Anm(raw)
        files += 1
        ok = a.game == game and a.save() == raw
        same += ok
        bad = audit(a)
        for b in bad:
            notes['%s: %s' % (game, b.split(':', 1)[-1].strip() if b.startswith('clip') else b)] += 1
        print('%s %-9s %5d clips %3d bones %2d poses %2d collections %4d slots  round trip %s  %s' % (
            game, level, len(a.clips), len(a.bones), len(a.poses), len(a.cols), len(a.slots),
            'identical' if ok else 'DIFFERS', '%d rule breaks' % len(bad) if bad else ''))
    print('byte-identical: %d of %d' % (same, files))
    for k, v in sorted(notes.items()):
        print('  %5d x %s' % (v, k))
    return same == files


def compare(dm, dd):
    """Converted Dead Men records against Dog Days' own for clips of the same name: per field, in how
    many clips the bytes agree - over all pairs and over the pairs whose event + data blocks are identical."""
    conv = convert(dm)
    theirs = {}
    for i, n in enumerate(dd.names):
        theirs.setdefault(n, i)
    fields = [('+00 s16 ?', 0, 2), ('+02 frames', 2, 4), ('+04 fps', 4, 6), ('+06 events', 6, 8), ('+08 flags', 8, 0xc),
              ('+14 float', 0x14, 0x18), ('+18 vec3', 0x18, 0x24), ('+24 size', 0x24, 0x28), ('+28', 0x28, 0x2c),
              ('+2C', 0x2c, 0x30), ('+30 vec A start', 0x30, 0x3c), ('+3C vec A end', 0x3c, 0x48),
              ('+48 vec B start', 0x48, 0x54), ('+54 vec B end', 0x54, 0x60), ('+60 float', 0x60, 0x64), ('+64 name', 0x64, 0x68)]
    rows = {f[0]: [0, 0] for f in fields}
    pairs = twins = 0
    seen = set()
    for i, n in enumerate(conv.names):
        j = theirs.get(n)
        if j is None or n in seen:
            continue
        seen.add(n)
        pairs += 1
        ba, bb = conv.block(i), dd.block(j)
        twin = bool(ba and bb and ba[1] and conv.data[ba[0]:ba[0] + ba[1]] == dd.data[bb[0]:bb[0] + bb[1]])
        twins += twin
        for name, lo, hi in fields:
            eq = conv.clips[i][lo:hi] == dd.clips[j][lo:hi]
            rows[name][0] += eq
            rows[name][1] += eq and twin
    print('%d clip names in both, %d of them with identical event + data blocks' % (pairs, twins))
    for name, lo, hi in fields:
        print('  %-18s equal in %5d of %d   identical-data pairs: %5d of %d' % (name, rows[name][0], pairs, rows[name][1], twins))
    return rows, pairs, twins


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['check']:
        sys.exit(0 if check() else 1)
    elif a[:1] == ['compare'] and len(a) == 3:
        got = {(g, l): raw for g, l, raw in stock() if (g, l) in (('dm', a[1]), ('dd', a[2]))}
        compare(Anm(got['dm', a[1]]), Anm(got['dd', a[2]]))
    elif a[:1] == ['convert'] and len(a) == 3:
        open(a[2], 'wb').write(convert(open(a[1], 'rb').read()).save())
    elif a[:1] == ['merge'] and len(a) >= 5:
        m = merge(Anm(open(a[1], 'rb').read()), Anm(open(a[2], 'rb').read()), dict((w.split('=') * 2)[:2] for w in a[4:]))
        open(a[3], 'wb').write(m.save())
        print('%d clips, %d bones, %d poses, %d slots, %d collections' % (len(m.clips), len(m.bones), len(m.poses), len(m.slots), len(m.cols)))
    elif a[:1] == ['info'] and len(a) == 2:
        f = Anm(open(a[1], 'rb').read())
        print('%s: %d clips, %d bones, %d poses, %d slot names, data %d bytes' % (f.game, len(f.clips), len(f.bones), len(f.poses), len(f.slots), len(f.data)))
        for c in f.cols:
            print('  %-28s %5d clips %5d slots used' % (c.short, len(c.clips), sum(1 for i in c.table if i >= 0)))
    else:
        sys.exit(__doc__)
