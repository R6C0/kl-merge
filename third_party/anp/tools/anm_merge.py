#!/usr/bin/env python3
"""anm_merge - merge Kane & Lynch: Dead Men animations into a Dog Days-format ANM.

    merge(dd_base_bytes, dm_bytes, db_map, extra_dbs) -> bytes
    merge_report(...)                                 -> (bytes, report dict)

CLI:
    python3 anm_merge.py DD_BASE.anm DM.anm OUT.anm [--map DM=DD ...] [--no-default-map]
                         [--extra NAME[=NEWNAME] ...] [--no-extra] [--pose-vectors start|drop]
                         [--report report.json]

What it does (see ANM_FORMAT.md):
  * output = everything in the DD base (its clips, clip data, names and DB entries keep their indices
    and bytes; new clips/names/DB entries are appended), plus:
  * for every DM DB mapped to a DD DB (db_map): every animation path the DM DB resolves and the DD
    DB does not resolve is added to the DD DB, pointing at the DM clip(s) converted to DD format;
    paths that the DD DB already resolves keep DD's clips.
  * DM DBs not in db_map are added as new DD DBs under their DM names (or merged into an existing
    DD DB of the same name, which the engine's name lookup would otherwise shadow).
  * converted DM clips: 0x50-byte record -> 0x68-byte record, clip blob (events + track block) copied
    verbatim except the per-track bone index (re-mapped by bone NAME into the output bone table)
    and the morph-channel index (re-mapped by morph NAME); new bone/morph names are appended.
"""
import sys, os, json, struct, bisect, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anm_lib as L

DEFAULT_MAP = {
    'PlayerCharacter': 'Kane',
    'Lynch_Coop': 'Lynch',
    'Army': 'Swat_02',
    'Police_USA': 'Police',
    'Mercenary_04': 'Thug',
    'Female': 'Civilian',
    'Civilian': 'Civilian',
}

POSE_FLAG = 0x1000      # DD clip flag: pose vectors (A,P,A2,P2) valid  (DD 0x8b427d / 0x8b42bf)

# event type ids DM clips use and DD never does (ANM_FORMAT.md §7); ANP_ANM_STRIP_DM_EVENTS=1 drops them
DM_ONLY_EVENTS = {1, 13, 14, 15, 16, 17, 18, 19, 21, 24, 30, 37, 38}
STRIP_DM_EVENTS = os.environ.get('ANP_ANM_STRIP_DM_EVENTS', '0') == '1'

# ANP_ANM_BACKFILL (default on): a DM character DB added under its own name (Mercenary_01/_04_M05/_05, Bouncer,
# FatMale, Swat, Female_Fighter) lacks every DD-only path kl2 caches by name, e.g. /Cover/<set>/Start_Fire|
# Start_Fire2|Start_Elevated_Fire (cover setup 0x730be0); ZStandState 0x583450 plays them via 0x59d550 with no
# null check (crash 0x5835a9 read 0x1c, M05). Fill each path the donor DD DB resolves and the DM DB does not
# (no clips added; DM's own paths keep their DM clips).
BACKFILL = os.environ.get('ANP_ANM_BACKFILL', '1') == '1'


def _backfill_donor(short):
    s = short.lower()
    return b'Swat_02' if (b'swat' in s or b'army' in s) else b'Thug'


def _b(s):
    return s if isinstance(s, bytes) else s.encode('latin1')


class _NameMap:
    """maps a source name-table index to the destination table by exact name, appending on demand."""

    def __init__(self, sn, dn, what, rep):
        self.sn, self.dn, self.what, self.rep = sn, dn, what, rep
        self.idx = {n: i for i, n in enumerate(dn)}
        self.low = {}
        for i, n in enumerate(dn):
            self.low.setdefault(n.lower(), i)
        self.cache = {}
        rep.setdefault('%s_names_added' % what, [])

    def __getitem__(self, i):
        j = self.cache.get(i)
        if j is not None:
            return j
        if i >= len(self.sn):
            raise L.AnmError('%s index %d out of range' % (self.what, i))
        n = self.sn[i]
        j = self.idx.get(n)
        if j is None:
            if n.lower() in self.low:
                self.rep.setdefault('%s_names_case_only_differences' % self.what, []).append(
                    '%s ~ %s' % (n.decode(), self.dn[self.low[n.lower()]].decode()))
            j = len(self.dn); self.dn.append(n); self.idx[n] = j
            self.rep['%s_names_added' % self.what].append(n.decode())
        if i < 0x43 and j != i:
            self.rep.setdefault('%s_low_index_moved' % self.what, []).append((i, n.decode(), j))
        self.cache[i] = j
        return j


class _ClipConverter:
    """converts clips of `src` (DM or DD variant) into the DD-variant AnimData `dst` (in place)."""

    def __init__(self, src, dst, rep, pose_mode):
        self.s, self.d, self.rep, self.pose_mode = src, dst, rep, pose_mode
        self.cmap = {}            # src clip index -> dst clip index
        self.span_map = {}        # src owner span start -> dst offset
        # owner spans (clips with size>0 own their bytes; size-0 clips are aliases into them)
        spans = sorted({src.blob_span(i) for i in range(len(src.recs)) if src.recs[i][9] > 0})
        self.span_starts = [s for s, _ in spans]
        self.spans = spans
        # track blocks inside each owner span
        self.blocks = collections.defaultdict(set)
        for i in range(len(src.recs)):
            sp = self._owner(src.recs[i][3])
            self.blocks[sp[0]].add(src.recs[i][3])
        self.pflags = {}
        for i in range(len(src.recs)):
            self.pflags.setdefault(src.recs[i][3], src.recs[i][2])
        # name maps (lazy: only names actually used by converted clips are added)
        self.bmap = _NameMap(src.C, dst.C, 'bone', rep)
        self.emap = _NameMap(src.E, dst.E, 'morph', rep)
        if len(src.C) > L.GROUND and src.C[L.GROUND] == b'GROUND' and self.bmap[L.GROUND] != L.GROUND:
            raise L.AnmError('GROUND bone would move')
        self.dup_names = 0
        self._dst_names = set(dst.D)

    def _owner(self, off):
        k = bisect.bisect_right(self.span_starts, off) - 1
        if k < 0:
            raise L.AnmError('offset %x before first blob' % off)
        s, sz = self.spans[k]
        if not s <= off < s + sz:
            raise L.AnmError('offset %x not inside an owned blob' % off)
        return s, sz

    def _copy_span(self, s, sz):
        if s in self.span_map:
            return self.span_map[s]
        S, D = self.s, self.d
        blob = bytearray(S.B[s:s + sz])
        for p in self.blocks[s]:
            q = p - s
            flags = self.pflags[p]
            if flags & 0x10:                        # baked-matrix layout: u32 n, u32 bone[n]
                n = L.u32(blob, q)
                for k in range(n):
                    o = q + 4 + 4 * k
                    struct.pack_into('<I', blob, o, self.bmap[L.u32(blob, o)])
                continue
            ntr, nch = L.u32(blob, q + 0x1c), L.u32(blob, q + 0x20)
            for k in range(ntr):
                o = q + 0x24 + 0x14 * k + 0x10
                struct.pack_into('<I', blob, o, self.bmap[L.u32(blob, o)])
            x = q + 0x24 + 0x14 * ntr
            for k in range(nch):
                o = x + 12 * k + 8
                struct.pack_into('<I', blob, o, self.emap[L.u32(blob, o)])
        # append (4-aligned) to the destination B
        if not isinstance(D.B, bytearray):
            D.B = bytearray(D.B)
        pad = (-len(D.B)) % 4
        newoff = len(D.B) + pad
        D.B += b'\0' * pad
        D.B += blob
        self.span_map[s] = newoff
        self.rep['bytes_added'] = self.rep.get('bytes_added', 0) + pad + sz
        return newoff

    def clip(self, ci):
        if ci in self.cmap:
            return self.cmap[ci]
        S, D = self.s, self.d
        r = S.recs[ci]
        s, sz = self._owner(r[3])
        delta = self._copy_span(s, sz) - s
        nev = S.n_events(ci)
        if nev:
            es, _ = self._owner(r[4])
            if es != s:
                raise L.AnmError('clip %d events and tracks in different blobs' % ci)
        f = lambda x: struct.unpack('<f', struct.pack('<I', x))[0]
        if S.rs == L.REC_DM:
            A, P, fend = r[12:15], r[15:18], r[18]
            A2, P2 = A, P
            flags = r[2]
            has_pose = any(f(x) != 0.0 for x in A + P)
        else:
            A, A2, P, P2, fend = r[12:15], r[15:18], r[18:21], r[21:24], r[24]
            flags = r[2]
            has_pose = bool(flags & POSE_FLAG)
        if self.pose_mode == 'drop' or not has_pose:
            flags &= ~POSE_FLAG
            A = A2 = P = P2 = (0, 0, 0)
        else:
            flags |= POSE_FLAG
        nr = list(r[0:3]) + [r[3] + delta, (r[4] + delta) if nev else 0] + list(r[5:12]) \
            + list(A) + list(A2) + list(P) + list(P2) + [fend, 0]
        nr[2] = flags
        if nev and STRIP_DM_EVENTS:
            # events must stay right before the track block: move the kept ones to the end of the table
            # (order kept), start the table after the dropped ones and lower the count
            eo = nr[4]
            evs = [bytes(D.B[eo + 8 * k:eo + 8 * k + 8]) for k in range(nev)]
            drop = [e for e in evs if L.u32(e, 0) in DM_ONLY_EVENTS]
            if drop:
                keep = [e for e in evs if L.u32(e, 0) not in DM_ONLY_EVENTS]
                D.B[eo:eo + 8 * nev] = b''.join(drop + keep)
                nr[4] = (eo + 8 * len(drop)) if keep else 0
                nr[1] = (nr[1] & 0xffff) | (len(keep) << 16)
                self.rep['dm_events_stripped'] = self.rep.get('dm_events_stripped', 0) + len(drop)
        assert len(nr) == 26
        D.recs.append(nr)
        name = S.D[ci]
        if name in self._dst_names:
            self.dup_names += 1
        D.D.append(name)
        ni = len(D.recs) - 1
        self.cmap[ci] = ni
        return ni


def merge_report(dd_base_bytes, dm_bytes, db_map=None, extra_dbs=None, pose_mode='start', path_filter=None):
    """returns (merged_bytes, report).  db_map: {dm_db_name: dd_db_name}; extra_dbs: None = add every
    unmapped DM DB, a list/set = only those, a dict = {dm_name: output_name}."""
    if db_map is None:
        db_map = DEFAULT_MAP
    base = L.AnmFile.parse(dd_base_bytes)
    src = L.AnmFile.parse(dm_bytes)
    if base.anim.rs != L.REC_DD:
        raise L.AnmError('base file is not Dog Days format')
    rep = collections.OrderedDict()
    rep['base'] = dict(clips=len(base.anim.recs), dbs=[d.short.decode() for d in base.dbs],
                       names=len(base.names.names), bones=len(base.anim.C))
    rep['source'] = dict(variant=src.anim.variant, clips=len(src.anim.recs),
                         dbs=[d.short.decode() for d in src.dbs], names=len(src.names.names))
    conv = _ClipConverter(src.anim, base.anim, rep, pose_mode)
    names = base.names
    sn = src.names.names
    dbrep = collections.OrderedDict()
    skipped = []
    bmap = {_b(k): _b(v) for k, v in db_map.items()}
    if extra_dbs is None:
        extra = None
    elif isinstance(extra_dbs, dict):
        extra = {_b(k): _b(v) for k, v in extra_dbs.items()}
    else:
        extra = {_b(k): _b(k) for k in extra_dbs}
    n_clips_before = len(base.anim.recs)

    def conv_list(lst, where):
        out = []
        for k, c in lst:
            if c >= len(src.anim.recs):
                raise L.AnmError('%s: clip %d out of range' % (where, c))
            out.append((k, conv.clip(c)))
        return out

    # several DM DBs may feed one DD DB (Female + Civilian -> Civilian): the DM DB whose name equals
    # the target is processed first, then the others in file order; the first one to add a path wins.
    order = sorted(src.dbs, key=lambda d: 0 if bmap.get(d.short, b'').lower() == d.short.lower() else 1)
    added_by = {}          # (target name, path) -> DM DB that added it
    new_dbs = []           # DBs created under a DM name (ANP_ANM_BACKFILL)
    for sdb in order:
        short = sdb.short
        target, mode = None, None
        if short in bmap:
            target = base.db_by_short(bmap[short])
            mode = 'mapped'
            if target is None:
                target = L.Database(L.DB_PREFIX + bmap[short])
                mode = 'mapped-created' if base.add_db(target) else 'mapped-created(shadowed!)'
        else:
            if extra is not None and short not in extra:
                skipped.append(dict(db=short.decode(), reason='not in db_map and not selected in extra_dbs'))
                continue
            outname = extra[short] if extra is not None else short
            same = [d for d in base.dbs if d.short.lower() == outname.lower()]
            if same:
                target, mode = same[0], 'same-name-merged'
            else:
                target = L.Database(L.DB_PREFIX + outname)
                mode = 'new' if base.add_db(target) else 'new(shadowed!)'
                new_dbs.append(target)
        r = dbrep.setdefault(short.decode(), collections.OrderedDict(
            into=target.short.decode(), mode=mode, paths_added=0, paths_kept_dd=0, added=[], case_variants=[]))
        if r['into'] != target.short.decode():
            r['into'] += '+' + target.short.decode()
        before = len(base.anim.recs)
        for nid, li in enumerate(sdb.index):
            if li is None:
                continue
            path = sn[nid]
            if path_filter is not None and mode.startswith('mapped') and not path_filter(path):
                r['paths_filtered'] = r.get('paths_filtered', 0) + 1
                continue
            mid = names.id_of(path)
            if mid is not None and target.get(mid) is not None:
                prev = added_by.get((target.name, path))
                if prev is None:
                    r['paths_kept_dd'] += 1
                else:
                    r['paths_already_added_by'] = r.get('paths_already_added_by', {})
                    r['paths_already_added_by'][prev] = r['paths_already_added_by'].get(prev, 0) + 1
                continue
            try:
                lst = conv_list(sdb.lists[li], '%s %s' % (short.decode(), path.decode()))
            except L.AnmError as e:
                skipped.append(dict(db=short.decode(), path=path.decode(), reason=str(e)))
                continue
            if mid is None:
                low = [n for n in names.names if n.lower() == path.lower()]
                if low:
                    r['case_variants'].append('%s (DD has %s)' % (path.decode(), low[0].decode()))
                mid = names.add(path)
            target.set(mid, lst)
            added_by[(target.name, path)] = short.decode()
            r['paths_added'] += 1
            r['added'].append(path.decode())
        r['clips_converted_for_db'] = len(base.anim.recs) - before
        if not r['case_variants']:
            del r['case_variants']

    if BACKFILL:
        bf = rep.setdefault('backfill', collections.OrderedDict())
        for db in new_dbs:
            if not any(li is not None and names.names[i].startswith(b'/Movement/') for i, li in enumerate(db.index)):
                continue          # vehicles / props (Van, Police_USA, Generic, ...)
            dn = _backfill_donor(db.short); donor = base.db_by_short(dn)
            if donor is None or donor is db:
                continue
            n = 0
            for nid, li in enumerate(donor.index):
                if li is not None and db.get(nid) is None:
                    db.set(nid, donor.lists[li]); n += 1
            bf[db.short.decode()] = '%s +%d' % (dn.decode(), n)

    # engine DB lookup = first DB whose name ends (case-insensitively) with the requested name
    shadow = []
    dbs = base.dbs
    for i, db in enumerate(dbs):
        for prev in dbs[:i]:
            if prev.name.lower().endswith(db.short.lower()):
                shadow.append('%s is shadowed by earlier %s' % (db.short.decode(), prev.short.decode()))
    a = base.anim
    sa = src.anim
    # unknown header sizes 10..12: keep the larger of the two (no reader found in either exe)
    for k in (10, 11, 12):
        a.hdr[k] = max(a.hdr[k], sa.hdr[k])
    nlimit = 0x7FFF   # name ids are handled as signed 16-bit (DD 0x5c2f60, 0x876940)
    if len(names.names) > nlimit:
        raise L.AnmError('too many animation names (%d)' % len(names.names))
    names._rebuild()
    out = base.build()
    rep['databases'] = collections.OrderedDict((d.short.decode(), dbrep[d.short.decode()]) for d in src.dbs
                                               if d.short.decode() in dbrep)
    rep['skipped'] = skipped
    rep['shadowed_db_names'] = shadow
    rep['clips_added'] = len(a.recs) - n_clips_before
    rep['clip_name_duplicates_of_base'] = conv.dup_names
    rep['names_total'] = len(names.names)
    rep['pose_vectors'] = pose_mode
    rep['output'] = dict(size=len(out), clips=len(a.recs), dbs=len(base.dbs), bones=len(a.C), morphs=len(a.E))
    return out, rep


def merge(dd_base_bytes, dm_bytes, db_map=None, extra_dbs=None, pose_mode='start'):
    return merge_report(dd_base_bytes, dm_bytes, db_map, extra_dbs, pose_mode)[0]


def print_report(rep, verbose=False):
    print('base: %d clips, %d DBs   source (%s): %d clips, %d DBs' % (
        rep['base']['clips'], len(rep['base']['dbs']), rep['source']['variant'], rep['source']['clips'],
        len(rep['source']['dbs'])))
    for k, v in rep['databases'].items():
        print('  %-18s -> %-20s %-18s added %5d paths (%4d clips)  kept DD %5d' % (
            k, v['into'], v['mode'], v['paths_added'], v['clips_converted_for_db'], v['paths_kept_dd']))
        for prev, n in v.get('paths_already_added_by', {}).items():
            print('        %d paths already added by DM %s (first wins)' % (n, prev))
        if verbose:
            for p in v['added']:
                print('        +', p)
        for c in v.get('case_variants', [])[:10]:
            print('        case-only variant:', c)
    for s in rep['skipped']:
        print('  SKIPPED', s)
    for s in rep['shadowed_db_names']:
        print('  WARNING', s)
    for k in ('bone_names_added', 'morph_names_added'):
        if rep.get(k):
            print('  %s (%d): %s' % (k, len(rep[k]), ', '.join(rep[k])))
    for k in ('bone_names_case_only_differences', 'bone_low_index_moved', 'morph_low_index_moved'):
        if rep.get(k):
            print('  NOTE %s: %s' % (k, rep[k]))
    print('clips added %d (%d share a name with a base clip), %d bytes of clip data added, %d names total' % (
        rep['clips_added'], rep['clip_name_duplicates_of_base'], rep.get('bytes_added', 0), rep['names_total']))
    print('output: %(size)d bytes, %(clips)d clips, %(dbs)d DBs, %(bones)d bones, %(morphs)d morph channels' % rep['output'])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('base'); ap.add_argument('dm'); ap.add_argument('out')
    ap.add_argument('--map', action='append', default=[], help='DM_DB=DD_DB (adds to / overrides default map)')
    ap.add_argument('--no-default-map', action='store_true')
    ap.add_argument('--extra', action='append', default=None, help='DM DB to add as new DB (NAME or NAME=NEWNAME); '
                    'default: all unmapped DM DBs')
    ap.add_argument('--no-extra', action='store_true', help='do not add unmapped DM DBs')
    ap.add_argument('--pose-vectors', choices=['start', 'drop'], default='start')
    ap.add_argument('--report'); ap.add_argument('-v', '--verbose', action='store_true')
    a = ap.parse_args(argv)
    m = {} if a.no_default_map else dict(DEFAULT_MAP)
    for kv in a.map:
        k, v = kv.split('=', 1); m[k] = v
    extra = None
    if a.no_extra:
        extra = []
    elif a.extra:
        extra = {}
        for kv in a.extra:
            k, _, v = kv.partition('='); extra[k] = v or k
    base = open(a.base, 'rb').read(); dm = open(a.dm, 'rb').read()
    out, rep = merge_report(base, dm, m, extra, a.pose_vectors)
    with open(a.out, 'wb') as fh:
        fh.write(out)
    print_report(rep, a.verbose)
    if a.report:
        with open(a.report, 'w') as fh:
            json.dump(rep, fh, indent=1)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
