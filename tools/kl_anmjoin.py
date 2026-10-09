#!/usr/bin/env python3
"""
Animation join for the graft: ONE Dog Days .ANM that holds the systems level's animation sets AND
every set the map names. Replaces the stand-in renaming of kl_graft.dm_rename / ANIM_FALLBACK and
kl_package.ANIM_SETS (see re/anmjoin.md for the evidence and the numbers).

    python kl_anmjoin.py join F07 F06 out.ANM [--donor F03]   S + what M's map names (levels or files)
    python kl_anmjoin.py join F07 M01_FA_A out.ANM --donor F03
    python kl_anmjoin.py needs                 per Dead Men map: the sets and slot names its map names
    python kl_anmjoin.py test [S ...]          every F level as S x (the other F levels + six Dead Men
                                               maps) as M; exit code 1 if a check fails
    python kl_anmjoin.py compact <in.ANM> <out.ANM> Set ...   keep only these sets (size experiment)

THE CALL (kl_graft.build, after kl_prpjoin.join made the joined .prp `Jn`):

    anm, rep = kl_anmjoin.join(S['.ANM'], M['.ANM'], Jn.p.keys, donors=[kl_anmjoin.stock_anm('F03')])
    bad = kl_anmjoin.verify(anm, rep)          # [] or the reasons
    copy['.ANM'] = anm.save()

S['.ANM'] and M['.ANM'] are the STOCK members (a Dead Men file is converted here). The strings are
the joined .prp's key table; from it come the set names ('anmcol:animationdatabase#X') and the slot
names the map mentions ('/Vehicles/Police_USA/Back_Left' in PassengerAnimPos[0], '(anim| /Level_
Specific/F06/Situations/Police_01)' inside a ZMiniCutsceneRout script). The .prp is NOT touched: every
set it names exists under that name in the result, so kl_graft renames no animation set any more.

WHAT A .ANM NAMES (data; kl_anm's docstring has the layout)
  set (collection) 'anmcol:animationdatabase#X'   named by ZLNKOBJ[2] of a character, a weapon, a car
  slot name '/Cover/Low/..'                       per file: name -> id (type 7), per set: id -> clips
  clip 'anim:Vehicles/VanTest_01#Open_Back_Left'  never named by a level (0 of 15 .prp key tables)
  The sets of a file share clips; the type 5 lists partition them (kl_anm.relist).
  Same-named sets of two Dog Days levels never disagree on a slot both have (0 of 2,3xx common
  slots in any of 462 ordered set pairs F01..F09); a level only adds 2 - 5 slots of its own.

RULES (S = base: none of its clips, data offsets, bone / pose indices or slot ids moves)
  For every set X the strings name:
  1 S has X                -> kept. If M has X too, X gains the slots S's X lacks ("widened"):
                              same game: all of them; Dead Men: only the slots the strings mention
                              and their directory neighbours ('/Vehicles/Police_USA/*').
  2 M (Dog Days) has X     -> the whole set from M.
  3 M (Dead Men) has X and X is NOT in STAND_IN (a car, a weapon: played by a Dead Men model that
                              the map brings)            -> the whole set, converted (kl_anm.convert).
  4 X is in STAND_IN (a Dead Men CHARACTER set: Dog Days' AI and weapon code drive the character and
                              ask for Dog Days slot names; of Dead Men's 1501 slot names only 356
                              exist in Dog Days) -> a copy of the first stand-in S has, else the
                              stand-in from a donor file, under the name X; then widened as in 1.
                              WHICH set stands in is a GUESS by role (STAND_IN).
  5 nobody has X           -> reported in rep['missing']; kl_graft decides (fail, or empty the name).
  Clips: a source clip whose name and whole event + data block (bone / pose indices compared by
  NAME) are already in the result is not copied. Same game: the record must agree too (all but the
  offsets, the size and +0x2C), else it becomes an alias record on the existing data - the
  mechanism the stock files use 27,610 times. Dead Men: Dog Days' own record of the clip is taken
  (its end vectors are real, the converted ones a copy of the start). A clip of the same name with
  OTHER data is added as a second clip of that name (stock files never have that: one name = one
  block in 41 of 41) and counted in rep['same name, other data'].

HEADER FIELDS RECOMPUTED (all by kl_anm.Anm.save; nothing else in the file depends on sizes)
  root: flags | extent, extent, child count (2 per set + 2)
  type 5: extent, name offset, clip count, child extent, the list (relist)   type 6: extent, K
  (used slots), S (table length), pair offsets                              type 7: extent, N,
  string offsets, the name-sorted index (kl2 0x68a730 does a binary search on it)
  type 4: dword 0 / 7 clip count, 1 data size, 2 / 3 / 4 name table sizes, 6 bone count, 8 pose count
  clip record of an ADDED clip: +0x0C data offset, +0x10 event offset, +0x24 size (0 = alias)
  clip data of an ADDED block: the bone index of every track, the pose index of every pose track
KEPT, NOT UNDERSTOOD (ASSUMPTIONS)
  type 4 dwords 9..12: S's. The loader (kl2 0x7079f0) stores 10 / 11 / 12 at manager +0x5c / +0x20
      / +0x24; none of the 68 functions that use the manager [0x1546f6c] was seen reading them, six
      stock levels have 0 there.
  clip +0x2C of an added clip: the SOURCE file's value. It differs between two records of the same
      clip and data inside one file and between files (HG_Default#Reload_UB: 0x2fc0 in F07, 0x59a0
      in F06), rises with the clip index in steps of about 144 and is not an offset into the data
      block (it lands in compressed key data). No reader found.
  condition bits of a Dead Men slot list (weapon / stance) are taken as Dog Days' (kl_anm: GUESS).
      Every '/Vehicles', '/Doors', '/Body' and '/Level_Specific' list of M01 / M03_FA_A, M09_A and
      M09_B has the bit-less default pair only (1,695 pairs), so for those the guess is moot.
EVENTS (exe): kl2 0x4a75d0 (clip record, event id, cursor*) scans the clip's table at data +
  record[+0x10] for ONE id and returns its frame or -1. Code pulls the events it wants; an id no
  code asks for does nothing. The Dead Men passenger clips fire ids 15..19, 37, 38, which no stock
  Dog Days clip fires (21 files) - and kl2.exe still asks for 15, 16, 17, 18, 19 and 38 (2 + 8 + 10
  + 2 + 2 + 1 call sites with a constant id). So the car passenger code is still there and the two
  games number these ids alike. rep['events'] lists the ids of added clips that S never fires.

TESTS (python kl_anmjoin.py test, 2026-10-09; nothing of this has run in the game)
  9 x 14 joins (every F level as S; the other eight F levels and M01 / M02 / M03 / M06_FA_A, M09_A,
  M09_B as M; donor F03): 126 joins, 0 failed, 0 sets missing. Result 20.3 .. 23.4 MB (S 19.8 ..
  21.9 MB): a join adds 0 .. 3.6 MB. F07 + M01_FA_A: 22.1 MB, +39 clips, +379,288 bytes of data,
  +13 bone names (the car bones), +42 slot names. F07 + M09_A + M09_B (chained): 23.8 MB.
  compact() to the sets a level names gives back 1 .. 2.4 MB only (the big first set of a file
  owns the clips every set shares), so it is not worth the renumbering.
FIRST LIVE TEST: see re/anmjoin.md.
"""
import collections, hashlib, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_anm
from kl_anm import Anm, Collection, PREFIX

# Dead Men CHARACTER sets -> Dog Days sets that may stand in, best first. EVERY LINE IS A GUESS by
# role (who carries what); a set not listed here is taken from the Dead Men file as it is (cars,
# weapons). 'Swat_02', 'Kane_NPC', 'Lynch_NPC', 'Kane', 'Lynch' are in every F level; 'Police',
# 'Civilian', 'Thug', 'Dog' only in some (F03 has all four: the donor to pass).
STAND_IN = {
    'Police': ['Police', 'Swat_02'], 'Swat': ['Swat_02'], 'Army': ['Swat_02'],
    'Thug': ['Thug', 'Lynch_NPC', 'Swat_02'], 'Bouncer': ['Thug', 'Lynch_NPC', 'Swat_02'],
    'Female_Fighter': ['Thug', 'Lynch_NPC', 'Swat_02'],
    'Mercenary_01': ['Lynch_NPC', 'Kane_NPC'], 'Mercenary_04': ['Lynch_NPC', 'Kane_NPC'],
    'Mercenary_04_M05': ['Lynch_NPC', 'Kane_NPC'], 'Mercenary_05': ['Lynch_NPC', 'Kane_NPC'],
    'Civilian': ['Civilian', 'Kane_NPC'], 'Female': ['Civilian', 'Kane_NPC'], 'FatMale': ['Civilian', 'Kane_NPC'],
    'PlayerCharacter': ['Lynch', 'Kane'], 'Lynch_Coop': ['Lynch', 'Kane'],       # as kl_package.ANIM_SETS had it
}
TOKEN = re.compile(r'/[A-Za-z0-9_./ -]*[A-Za-z0-9_.-]')    # the characters of the 4,775 stock slot names


def short(name):
    return name.split('#', 1)[-1]


def stock_anm(level, game=None):
    """The .ANM member of a stock level ('F03', 'M01_FA_A')."""
    import zipfile
    import kl_prpjoin as J
    with zipfile.ZipFile(J.level_zip(level, game)) as zf:
        return zf.read(next(n for n in zf.namelist() if n.lower().endswith('.anm')))


def _anm(x):
    return x if isinstance(x, Anm) or x is None else Anm(bytes(x))


def _mask(rec):
    """A clip record without what a join rewrites (+0x0C, +0x10, +0x24) and without +0x2C (per file)."""
    return bytes(rec[:0xc]) + bytes(rec[0x14:0x24]) + bytes(rec[0x28:0x2c]) + bytes(rec[0x30:])


def _off(rec):
    return struct.unpack_from('<i', rec, 0xc)[0]


def event_ids(a):
    """The event ids the clips of a file fire (entries {u32 id, u16 frame, u16 ?} before the data)."""
    ids = set()
    for (start, _size), ev in set(kl_anm.owners(a).values()):
        ids.update(struct.unpack_from('<I', a.data, start + 8 * k)[0] for k in range(ev))
    return ids


def signature(a, i, own=None, cache=None):
    """What clip i plays, independent of the file it sits in: (name, events + data with the bone and
    pose indices zeroed, the bone names, the pose names). verify() compares these."""
    blk, oev = (own or kl_anm.owners(a))[_off(a.clips[i])]
    if cache is not None and (a.names[i], blk) in cache:
        return cache[a.names[i], blk]
    b = bytearray(a.data[blk[0]:blk[0] + blk[1]])
    bones, poses = kl_anm.tracks(b, 0, oev)
    bn = tuple(a.bones[struct.unpack_from('<i', b, p)[0]] for p in bones)
    pn = tuple(a.poses[struct.unpack_from('<i', b, p)[0]] for p in poses)
    for p in bones + poses:
        b[p:p + 4] = bytes(4)
    sig = a.names[i], hashlib.blake2b(bytes(b), digest_size=16).digest(), bn, pn
    if cache is not None:
        cache[a.names[i], blk] = sig
    return sig


def view(a, c, own=None):
    """{slot name: [(flags, clip signature)]} of a collection."""
    own = own or kl_anm.owners(a)
    return {a.slots[s]: [(f, signature(a, i, own)) for f, i in lst] for s, lst in c.lists().items()}


class _Out:
    """The growing result: S plus indexes to find a clip that is already there."""

    def __init__(self, s):
        self.a = a = Anm(s.save())
        self.data = bytearray(a.data)
        self.bone = {n: i for i, n in reversed(list(enumerate(a.bones)))}
        self.pose = {n: i for i, n in reversed(list(enumerate(a.poses)))}
        self.slot = {n: i for i, n in enumerate(a.slots)}
        self.blocks, self.recs, self.first = {}, {}, {}  # (name, digest) -> +0x0C; (name, masked record, +0x0C) -> clip; (name, +0x0C) -> clip
        self.owned = set(a.names)                        # names of clips that have data here
        self.events = event_ids(a)                       # ids S's own clips fire
        self.strange = collections.Counter()             # ids of added clips that S never fires
        for i, n in enumerate(a.names):
            b, ev = a.block(i), max(a.events(i), 0)
            if b and b[1]:
                self.blocks.setdefault((n, hashlib.blake2b(a.data[b[0]:b[0] + b[1]], digest_size=16).digest()), b[0] + 8 * ev)
            self.note(i)
        self.st = collections.Counter()

    def note(self, i):
        a = self.a
        self.recs.setdefault((a.names[i], _mask(a.clips[i]), _off(a.clips[i])), i)
        self.first.setdefault((a.names[i], _off(a.clips[i])), i)

    @staticmethod
    def index(table, names, name):
        if name not in table:
            table[name] = len(names)
            names.append(name)
        return table[name]


class _Source:
    """One file clips are taken from (Dog Days layout; `cross` = it was a Dead Men file)."""

    def __init__(self, out, src, cross, label):
        self.o, self.src, self.cross, self.label = out, src, cross, label
        self.own = kl_anm.owners(src)
        self.placed, self.map = {}, {}                   # block -> [+0x0C in the result, still needs an owner record]; clip -> clip

    def clip(self, i):
        if i in self.map:
            return self.map[i]
        o, src, st = self.o, self.src, self.o.st
        a, name = o.a, src.names[i]
        rec, ev = bytearray(src.clips[i]), max(src.events(i), 0)
        if src.flags(i) & 0x10:
            raise ValueError('clip %d (%s) is uncompressed: its bone list is not handled' % (i, name))
        blk, oev = self.own[_off(rec)]
        if blk not in self.placed:
            b = bytearray(src.data[blk[0]:blk[0] + blk[1]])
            bones, poses = kl_anm.tracks(b, 0, oev)
            for p in bones:
                struct.pack_into('<i', b, p, o.index(o.bone, a.bones, src.bones[struct.unpack_from('<i', b, p)[0]]))
            for p in poses:
                struct.pack_into('<i', b, p, o.index(o.pose, a.poses, src.poses[struct.unpack_from('<i', b, p)[0]]))
            key = name, hashlib.blake2b(bytes(b), digest_size=16).digest()
            at = o.blocks.get(key)
            if at is None:
                if name in o.owned:
                    st['same name, other data'] += 1
                o.owned.add(name)
                at = o.blocks[key] = len(o.data) + 8 * oev
                o.data += b
                for k in range(oev):
                    e = struct.unpack_from('<I', b, 8 * k)[0]
                    if e not in o.events:
                        o.strange[e] += 1
                st['data blocks added'] += 1
                st['data bytes added'] += len(b)
                self.placed[blk] = [at, True]
            else:
                st['data blocks found in the base'] += 1
                self.placed[blk] = [at, False]
        at, fresh = self.placed[blk]
        size = 0
        if fresh:
            # the first record on a new block owns it. An alias record with fewer events than the
            # owner never occurs (0 of 27,610), so the size is the whole block
            if ev != oev:
                raise ValueError('clip %d (%s): %d events, the owner of its data has %d' % (i, name, ev, oev))
            size, self.placed[blk][1] = blk[1], False
        else:
            hit = o.recs.get((name, _mask(rec), at))
            if hit is None and self.cross:
                hit = o.first.get((name, at))            # Dog Days' own record of this Dead Men clip
            if hit is not None:
                st['clips reused'] += 1
                self.map[i] = hit
                return hit
            st['alias records added'] += 1
        struct.pack_into('<ii', rec, 0xc, at, at - 8 * ev)
        struct.pack_into('<i', rec, 0x24, size)
        k = self.map[i] = len(a.clips)
        a.clips.append(rec)
        a.names.append(name)
        o.note(k)
        st['clips added'] += 1
        return k

    def lists(self, c, only=None):
        """[(slot name, [(flags, source clip)])] of collection c in pool order; only = slot names."""
        ls = sorted(c.lists().items(), key=lambda kv: c.table[kv[0]])
        return [(self.src.slots[s], lst) for s, lst in ls if only is None or self.src.slots[s] in only]


def _add_lists(out, col, src, lists):
    """Append slot lists taken from a source to collection col of the result. Returns the slot names."""
    table = {s: i for s, i in enumerate(col.table) if i >= 0}
    done = []
    for name, lst in lists:
        s = out.index(out.slot, out.a.slots, name)
        if s in table:
            raise ValueError('%s already has slot %s' % (col.short, name))
        table[s] = len(col.pool)
        col.pool += [(f, src.clip(i)) for f, i in lst]
        done.append(name)
    col.table = [table.get(s, -1) for s in range(max(table) + 1 if table else 0)]
    return done


def mentions(strings, slots):
    """The slot names (of the set `slots`) that the strings hold: whole, or inside a script."""
    hit = set()
    for k in strings:
        if '/' in k:
            if k in slots:
                hit.add(k)
            else:
                hit.update(t for t in TOKEN.findall(k) if t in slots)
    return hit


def join(s, m, strings, donors=(), stand_in=STAND_IN, log=None):
    """S's .ANM (Dog Days) + what the joined level names of M's .ANM (either game, or None)
    -> (Anm, report). strings = the joined .prp's key table (or any strings holding the set names
    'anmcol:animationdatabase#X' and the slot names in use); donors = further Dog Days .ANM files
    a stand-in set may come from. See the module docstring for the rules. The report:
      'sets'    {set: what was done}            'missing'  [sets nobody has]
      'guesses' [stand-ins used, in words]      'stats'    Counter (clips / blocks / bytes added ...)
      'bones', 'poses', 'slots'  names added to the tables   'size' (S, M, result) in bytes
      'events'  {event id: uses} in added clips, of ids no clip of S fires
      'taken'   [(set, slot name, source label)] - what verify() checks against the sources."""
    s, m = _anm(s), _anm(m)
    donors = [_anm(d) for d in donors]
    if s.game != 'dd' or any(d.game != 'dd' for d in donors):
        raise ValueError('the base and the donors must be Dog Days files')
    strings = list(strings)
    named = [short(k) for k in strings if k.startswith(PREFIX)]
    named = sorted(set(named) - {''})
    out = _Out(s)
    a = out.a
    cross = m is not None and m.game == 'dm'
    sizes = [len(s.save()), len(m.save()) if m is not None else 0]
    mm = kl_anm.convert(m) if cross else m
    srcs = {}                                            # label -> _Source

    def source(label, anm, x=False):
        if label not in srcs:
            srcs[label] = _Source(out, anm, x, label)
        return srcs[label]

    M = source('M', mm, cross) if mm is not None else None
    mcols = {c.short: c for c in mm.cols} if mm is not None else {}
    said = mentions(strings, set(mm.slots)) if mm is not None else set()
    dirs = {n.rsplit('/', 1)[0] for n in said}
    rep = {'sets': {}, 'missing': [], 'guesses': [], 'taken': [], 'named slots': sorted(said)}
    have = {c.short: c for c in a.cols}
    stock = {c.short: (list(c.pool), list(c.table)) for c in a.cols}     # S's sets before any is widened
    n0 = len(a.bones), len(a.poses), len(a.slots)

    def new(name):
        c = Collection(PREFIX + name, [], [], [])
        a.cols.append(c)
        have[name] = c
        return c

    def take(col, src, c, only=None):
        got = _add_lists(out, col, src, [(n, l) for n, l in src.lists(c, only)])
        rep['taken'] += [(col.short, n, src.label) for n in got]
        return len(got)

    def widen(x, col):
        """Slots M's X has and col lacks: all (same game) or the mentioned ones and their neighbours."""
        if x not in mcols:
            return 0
        mine = {a.slots[i] for i in col.lists()}
        want = {mm.slots[i] for i in mcols[x].lists()} - mine
        if cross:
            want = {n for n in want if n in said or n.rsplit('/', 1)[0] in dirs}
        return take(col, M, mcols[x], want) if want else 0

    order = [x for x in mcols if x in named] + [x for x in named if x not in mcols]      # M's file order first
    for x in order:
        if x in have:                                                                 # rule 1
            n = widen(x, have[x])
            rep['sets'][x] = 'kept' + (', %d slots added from M' % n if n else '')
        elif x in mcols and not cross:                                                # rule 2
            take(new(x), M, mcols[x])
            rep['sets'][x] = 'added from M'
        elif x in mcols and x not in stand_in:                                        # rule 3
            take(new(x), M, mcols[x])
            rep['sets'][x] = 'added from M, converted from Dead Men'
        else:                                                                         # rule 4
            for cand in stand_in.get(x, [x]):
                if cand in stock and cand != x:
                    col = new(x)                         # S's set as it was: what M adds to `cand` is M's `cand`, not M's X
                    col.pool, col.table = list(stock[cand][0]), list(stock[cand][1])
                    what = 'copy of %s' % cand
                    break
                d = next((k for k, dn in enumerate(donors) if any(c.short == cand for c in dn.cols)), None)
                if d is not None:
                    src = source('donor %d' % d, donors[d])
                    take(new(x), src, donors[d].col(cand))
                    what = '%s of donor %d' % (cand, d)
                    break
            else:
                rep['missing'].append(x)
                rep['sets'][x] = 'MISSING: neither file has it and no stand-in is at hand'
                continue
            n = widen(x, have[x])
            rep['sets'][x] = what + (', %d slots added from M' % n if n else '')
            if cand != x or x in mcols:
                rep['guesses'].append('%s plays %s (STAND_IN: a guess by role)' % (x, what))
    a.data = bytes(out.data)
    kl_anm.relist(a)
    rep['stats'] = out.st
    rep['events'] = dict(out.strange)                    # event id -> uses, of ids no clip of S fires
    if cross and out.strange:
        rep['guesses'].append('event ids S never fires, in added Dead Men clips: %s' % ', '.join('%#x x%d' % kv for kv in sorted(out.strange.items())))
    rep['bones'], rep['poses'], rep['slots'] = a.bones[n0[0]:], a.poses[n0[1]:], a.slots[n0[2]:]
    rep['size'] = tuple(sizes + [len(a.save())])
    rep['sources'] = {'S': s, **{k: v.src for k, v in srcs.items()}}
    if cross:
        rep['guesses'].append('Dead Men clip records: both vectors written as start and end value (kl_anm.convert)')
    if len(a.bones) > 255:
        rep['guesses'].append('%d bone names: no stock file has more than 239' % len(a.bones))
    if log:
        describe(rep, log)
    return a, rep


def describe(rep, log=print):
    st = rep['stats']
    log('  .ANM joined: %.1f MB (S %.1f MB%s); clips +%d (%d reused, %d alias records), data +%d bytes in %d blocks, '
        '%d blocks already in S; bones +%d, slot names +%d' % (
            rep['size'][2] / 1e6, rep['size'][0] / 1e6, ', M %.1f MB' % (rep['size'][1] / 1e6) if rep['size'][1] else '',
            st['clips added'], st['clips reused'], st['alias records added'], st['data bytes added'], st['data blocks added'],
            st['data blocks found in the base'], len(rep['bones']), len(rep['slots'])))
    for x, what in rep['sets'].items():
        if what != 'kept':
            log('    %-16s %s' % (x, what))
    if st['same name, other data']:
        log('    %d clips share a name with a clip of S but hold other data (added as second clips)' % st['same name, other data'])
    for g in rep['guesses']:
        log('    GUESS %s' % g)
    if rep['missing']:
        log('    MISSING %s' % rep['missing'])


def verify(anm, rep):
    """Checks of a join: [] or the reasons. 1 re-read: the saved file parses and saves to the same
    bytes; 2 kl_anm.audit (layout rules, every clip listed once and played, offsets inside the data,
    bone / pose indices inside the tables, flag 0x1000); 3 S untouched: its clips, data, names, bone
    / pose / slot tables are a prefix of the result, dwords 9..12 are S's, every slot list of every
    set of S is still there pair for pair; 4 every slot list taken from a source plays the same
    clips as in the source (name, events + data, bones and poses BY NAME); 5 every set named exists."""
    bad = []
    raw = anm.save()
    re_ = Anm(raw, 'dd')
    if re_.save() != raw:
        bad.append('the saved file does not read back to the same bytes')
    bad += kl_anm.audit(re_)[:20]
    s = rep['sources']['S']
    n = len(s.clips)
    for what, x, y in (('clip records', re_.clips[:n], s.clips), ('clip names', re_.names[:n], s.names),
                       ('data', re_.data[:len(s.data)], s.data), ('bone names', re_.bones[:len(s.bones)], s.bones),
                       ('pose names', re_.poses[:len(s.poses)], s.poses), ('slot names', re_.slots[:len(s.slots)], s.slots),
                       ('manager dwords 9..12', re_.head[9:13], s.head[9:13])):
        if x != y:
            bad.append('S changed: %s' % what)
    cols = {c.short: c for c in re_.cols}
    if [c.name for c in re_.cols[:len(s.cols)]] != [c.name for c in s.cols]:
        bad.append('S changed: order of the sets')
    for c in s.cols:
        mine, theirs = cols[c.short].lists() if c.short in cols else {}, c.lists()
        if any(mine.get(k) != v for k, v in theirs.items()):
            bad.append('S changed: slot lists of %s' % c.short)
    own, owns, views, mine, ids_ = kl_anm.owners(re_), {}, {}, {}, {n: i for i, n in enumerate(re_.slots)}
    for x, slot, label in rep['taken']:
        src = rep['sources'][label]
        if label not in owns:
            owns[label] = kl_anm.owners(src), {}
        key = label, x
        if key not in views:
            # the set the lists came from: X itself, or the stand-in of a donor
            name = x if label == 'M' else rep['sets'][x].split(' of donor')[0]
            views[key] = src.col(name).lists(), {n: i for i, n in enumerate(src.slots)}
        lists, ids = views[key]
        want = [(f, signature(src, i, *owns[label])) for f, i in lists[ids[slot]]]
        if x not in views:
            views[x] = cols[x].lists()
        got = views[x].get(ids_[slot])
        if got is None or [(f, signature(re_, i, own, mine)) for f, i in got] != want:
            bad.append('%s %s: not the clips of the source' % (x, slot))
    for x, what in rep['sets'].items():
        if x not in cols and x not in rep['missing']:
            bad.append('set %s is not in the result' % x)
    return bad


def compact(anm, keep):
    """EXPERIMENT (not for the first live test): a copy of a Dog Days file with only the sets in
    `keep`, the clips they play and the data those clips use. Clip indices and data offsets of what
    stays CHANGE (nothing outside the .ANM is known to hold either: 0 clip names in 15 .prp key
    tables), slot ids and bone / pose indices do not. Returns (Anm, {old clip: new clip})."""
    anm = _anm(anm)
    out = Anm(anm.save())
    out.cols = [c for c in out.cols if c.short in set(map(short, keep))]
    used = sorted({i for c in out.cols for _f, i in c.pool})
    own = kl_anm.owners(anm)
    data, placed, clips, names, cmap = bytearray(), {}, [], [], {}
    owner = {}                                           # block -> the record that owns it afterwards
    for i in used:                                       # the stock owner if it stays, else the first alias
        blk, _oev = own[_off(anm.clips[i])]
        if blk not in owner or struct.unpack_from('<i', anm.clips[i], 0x24)[0]:
            owner[blk] = i
    for i in used:
        rec, ev = bytearray(anm.clips[i]), max(anm.events(i), 0)
        blk, oev = own[_off(rec)]
        if blk not in placed:
            placed[blk] = len(data) + 8 * oev
            data += anm.data[blk[0]:blk[0] + blk[1]]
        at = placed[blk]
        struct.pack_into('<ii', rec, 0xc, at, at - 8 * ev)
        struct.pack_into('<i', rec, 0x24, blk[1] if owner[blk] == i else 0)
        cmap[i] = len(clips)
        clips.append(rec)
        names.append(anm.names[i])
    out.clips, out.names, out.data = clips, names, bytes(data)
    for c in out.cols:
        c.pool = [(f, cmap[i]) for f, i in c.pool]
    kl_anm.relist(out)
    return out, cmap


# ---- what a level names ---------------------------------------------------------------------------

def level_strings(level, game=None, side=None):
    """The strings of a stock level's property tree (side 'map' / 'systems' as kl_prpjoin.sides
    cuts it, None = all): what the joined .prp would hold of this level."""
    import kl_prpjoin as J
    sc = J.Scene.load(level, game)
    sides = J.sides(sc)
    for k in range(1, len(sc.nodes)):
        if sc.game == 'dm' and sc.names[sc.top[k]] == 'CoverList':
            sides[k] = 'map'                             # as kl_graft.DeadMen
    out = set()
    for k in range(1, len(sc.nodes)):
        if side is None or sides[k] == side:
            for _holder, _lab, u in J.fields(sc, k):
                out.update(J.strings(sc, u))
    return out


def needs(levels=('M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A', 'M09_A', 'M09_B'), log=print):
    """Per Dead Men map: the sets its MAP side names, by class, and the slot names it mentions."""
    import kl_prpjoin as J
    dd = {}
    for f in ['F%02d' % i for i in range(1, 10)]:
        for c in Anm(stock_anm(f)).cols:
            dd.setdefault(c.short, []).append(f)
    res = {}
    for lv in levels:
        sc = J.Scene.load(lv, 'dm')
        a = Anm(stock_anm(lv, 'dm'))
        sides = J.sides(sc)
        who = collections.defaultdict(collections.Counter)
        strings = set()
        for k in range(1, len(sc.nodes)):
            if sides[k] != 'map' and sc.names[sc.top[k]] != 'CoverList':
                continue
            for holder, lab, u in J.fields(sc, k):
                for s_ in J.strings(sc, u):
                    strings.add(s_)
                    if s_.startswith(PREFIX) and short(s_):
                        who[short(s_)][holder.split(' ')[0]] += 1
        said = mentions(strings, set(a.slots))
        cols = {c.short: c for c in a.cols}
        log('%s  (map side: %d sets named, %d slot names mentioned)' % (lv, len(who), len(said)))
        for x in sorted(who):
            c = cols.get(x)
            fam = collections.Counter(a.slots[s_].split('/')[1] for s_ in c.lists()) if c else {}
            kind = 'character -> stand-in %s' % '/'.join(STAND_IN[x]) if x in STAND_IN else 'NO Dog Days equivalent: converted' if x not in dd else 'Dog Days has it'
            log('  %-15s %-28s %4d slots %-34s %s' % (x, ', '.join('%s x%d' % kv for kv in who[x].items()), len(c.lists()) if c else 0,
                                                    '(' + ', '.join('%s %d' % kv for kv in fam.most_common(3)) + ')', kind))
        fam = collections.Counter('/'.join(n.split('/')[:3]) for n in said)
        if said:
            log('  slot names: %s' % ', '.join('%s x%d' % kv for kv in sorted(fam.items())))
        res[lv] = dict(who), said
    return res


def test(bases=None, log=print):
    """Every F level as S against every other F level and the six Dead Men maps as M, with F03 (the
    one F level that has Police, Thug, Civilian and Dog) as donor. Strings = S's systems side +
    M's map side. Returns the number of failed joins."""
    fs = ['F%02d' % i for i in range(1, 10)]
    dms = ['M01_FA_A', 'M02_FA_A', 'M03_FA_A', 'M06_FA_A', 'M09_A', 'M09_B']
    raw = {l: stock_anm(l) for l in fs + dms}
    log('reading the property trees ...')
    sysk = {l: level_strings(l, 'dd', 'systems') for l in (bases or fs)}
    mapk = {l: level_strings(l, None, 'map') for l in fs + dms}
    donor = Anm(raw['F03'])
    failed = n = 0
    for sl in bases or fs:
        S = Anm(raw[sl])
        for ml in fs + dms:
            if ml == sl:
                continue
            a, rep = join(S, Anm(raw[ml]), sysk[sl] | mapk[ml], donors=[donor])
            bad = verify(a, rep)
            n += 1
            failed += bool(bad or rep['missing'])
            st = rep['stats']
            log('S %s M %-8s %5.1f MB (S %4.1f)  clips +%-4d reused %-4d alias +%-3d data +%-8d bones +%-2d slots +%-3d %s%s%s' % (
                sl, ml, rep['size'][2] / 1e6, rep['size'][0] / 1e6, st['clips added'], st['clips reused'], st['alias records added'],
                st['data bytes added'], len(rep['bones']), len(rep['slots']),
                '; '.join('%s: %s' % (x, w) for x, w in rep['sets'].items() if w != 'kept'),
                '  MISSING %s' % rep['missing'] if rep['missing'] else '', '  FAILED %s' % bad[:3] if bad else ''))
    log('%d joins, %d failed' % (n, failed))
    return failed


def main(argv):
    def load(x):
        return open(x, 'rb').read() if os.path.isfile(x) else stock_anm(x)

    def strings(x, side):
        return level_strings(x, None, side) if not os.path.isfile(x) else set()

    if argv[:1] == ['join'] and len(argv) >= 4:
        donors = [load(argv[i + 1]) for i, w in enumerate(argv) if w == '--donor']
        sets = [w for i, w in enumerate(argv) if i and argv[i - 1] == '--sets']
        keys = strings(argv[1], 'systems') | strings(argv[2], 'map') | {PREFIX + x for w in sets for x in w.split(',')}
        a, rep = join(load(argv[1]), load(argv[2]), keys, donors=donors, log=print)
        bad = verify(a, rep)
        print('verify: %s' % (bad or 'ok'))
        open(argv[3], 'wb').write(a.save())
        return 1 if bad or rep['missing'] else 0
    if argv[:1] == ['needs']:
        needs(*([argv[1:]] if argv[1:] else []))
        return 0
    if argv[:1] == ['test']:
        return 1 if test(argv[1:] or None) else 0
    if argv[:1] == ['compact'] and len(argv) >= 4:
        a, _ = compact(load(argv[1]), argv[3:])
        bad = kl_anm.audit(a)
        open(argv[2], 'wb').write(a.save())
        print('%d clips, %.1f MB; audit: %s' % (len(a.clips), len(a.save()) / 1e6, bad[:5] or 'ok'))
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
