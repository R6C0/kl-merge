#!/usr/bin/env python3
"""verify_merge.py MERGED.anm [DD_BASE.anm DM_SOURCE.anm [report.json]]

Re-parses a merged (Dog Days format) ANM and checks:
  structure  - root/chunk sizes, header totals, counts, canonical name tables (via anm_lib.parse),
               type-5 lists consistent with the databases
  databases  - every name id of every DB resolves to a variant list whose clips exist; the engine's
               variant selection returns a clip for an all-set and an empty condition mask;
               every DB is found by the engine's suffix lookup under its own name
  clips      - every clip's events/track block lie inside B, every bone/morph index is inside the
               C/E tables, every key stream decodes and lies inside the clip's blob
  base       - (with DD_BASE) every path of every base DB still resolves to byte-identical clip data
  source     - (with DM_SOURCE) every DM path of every merged DM DB resolves in its target DB; for
               paths that were added, the target's clips decode to exactly the DM key data
               (bone/morph indices compared by name)
"""
import sys, os, json, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anm_lib as L, anm_codec as C

errors = []


def err(msg):
    errors.append(msg)
    if len(errors) <= 30:
        print('ERROR', msg)


def clip_signature(a, i):
    """decoded, name-keyed content of a clip (for cross-file comparison)."""
    tb = a.track_block(i)
    r = a.recs[i]
    sig = {'frames': a.frames(i), 'events': a.events(i), 'u0': r[0] & 0xffff, 'fps': r[1] & 0xffff,
           'flags': r[2] & ~0x1000, 'misc': tuple(r[5:12]) if False else (r[5], r[6], r[7], r[8], r[10], r[11])}
    if tb['baked']:
        sig['baked'] = [a.C[b] for b in tb['bones']]
        return sig
    p, B = tb['p'], a.B
    tr = {}
    for oa, ob, oc, od, bone in tb['tracks']:
        fa = C.idxt_frames(B, p + oa); fc = C.idxt_frames(B, p + oc)
        q = C.rot_decode_all(B, p + ob, len(fa))
        pos = [struct.unpack_from('<3f', B, p + od + 12 * k) for k in range(len(fc))]
        tr[a.C[bone]] = (tuple(fa), tuple(q), tuple(fc), tuple(pos))
    sig['tracks'] = tr
    ch = {}
    for oi, ov, c in tb['channels']:
        fi = C.idxt_frames(B, p + oi)
        ch[a.E[c]] = (tuple(fi), struct.unpack_from('<%df' % len(fi), B, p + ov))
    sig['channels'] = ch
    sig['duration'] = tb['duration']
    return sig


def check_clip(a, i, owner_spans):
    r = a.recs[i]
    nB = len(a.B)
    if not 0 <= r[3] < nB:
        return err('clip %d track offset outside B' % i)
    s, sz = owner_spans(r[3])
    if s is None:
        return err('clip %d: track block not inside an owned blob' % i)
    if a.n_events(i) and not (s <= r[4] and r[4] + 8 * a.n_events(i) <= s + sz):
        err('clip %d: events outside blob' % i)
    tb = a.track_block(i)
    if tb['baked']:
        for b in tb['bones']:
            if b >= len(a.C): err('clip %d baked bone %d out of range' % (i, b))
        return
    if tb['frames'] != a.frames(i):
        err('clip %d frame count mismatch' % i)
    p, B = tb['p'], a.B
    lim = s + sz
    for k, (oa, ob, oc, od, bone) in enumerate(tb['tracks']):
        if bone >= len(a.C):
            err('clip %d track %d bone %d out of range' % (i, k, bone)); continue
        if k == 0 and bone != L.GROUND and a.C[bone] == b'GROUND':
            err('clip %d GROUND not at hard-coded index' % i)
        fa = C.idxt_frames(B, p + oa); fc = C.idxt_frames(B, p + oc)
        if p + oa + C.idxt_size(B, p + oa) > lim or p + oc + C.idxt_size(B, p + oc) > lim:
            err('clip %d track %d IdxT outside blob' % (i, k))
        if p + ob + C.rot_stream_size(B, p + ob, len(fa)) > lim or p + od + 12 * len(fc) > lim:
            err('clip %d track %d key data outside blob' % (i, k))
        if (fa and fa[-1] >= a.frames(i)) or (fc and fc[-1] >= a.frames(i)):
            err('clip %d track %d key frame beyond clip' % (i, k))
    for oi, ov, c in tb['channels']:
        if c >= len(a.E):
            err('clip %d morph channel %d out of range' % (i, c))
        fi = C.idxt_frames(B, p + oi)
        if p + ov + 4 * len(fi) > lim:
            err('clip %d morph data outside blob' % i)


def make_owner(a):
    import bisect
    spans = sorted({a.blob_span(i) for i in range(len(a.recs)) if a.recs[i][9] > 0})
    starts = [s for s, _ in spans]

    def owner(off):
        k = bisect.bisect_right(starts, off) - 1
        if k >= 0 and spans[k][0] <= off < spans[k][0] + spans[k][1]:
            return spans[k]
        return None, None
    return owner


def verify(merged_bytes, base_bytes=None, dm_bytes=None, report=None):
    st = collections.Counter()
    m = L.AnmFile.parse(merged_bytes)            # structural checks happen here
    a = m.anim
    if a.rs != L.REC_DD:
        err('merged file is not DD format')
    h = a.hdr
    # header totals
    root_n = struct.unpack_from('<I', merged_bytes, 12)[0]
    if root_n != len(m.entries): err('root child count')
    if struct.unpack_from('<I', merged_bytes, 8)[0] != len(merged_bytes): err('root size')
    if not (h[0] == len(a.recs) == h[7] == len(a.D)): err('clip counts %r' % h[:8])
    if h[6] != len(a.C) or h[8] != len(a.E) or h[1] != len(a.B): err('table counts')
    if m.check_dblists(): err('type-5 lists inconsistent: %r' % m.dblist_mismatch[:5])
    if len(m.names.names) > 0x7FFF: err('name ids exceed signed 16 bit')
    st['clips'] = len(a.recs); st['dbs'] = len(m.dbs); st['names'] = len(m.names.names)
    # databases
    N = len(a.recs)
    for db in m.dbs:
        if m.find_db(db.short) is not db:
            err('DB %s is shadowed in the engine lookup by %s' % (db.short, m.find_db(db.short).short))
        if len(db.index) > len(m.names.names):
            err('DB %s index longer than name table' % db.short)
        for nid, li in enumerate(db.index):
            if li is None:
                continue
            lst = db.lists[li]
            st['db_entries'] += 1
            for k, c in lst:
                if c >= N:
                    err('DB %s name %s -> clip %d out of range' % (db.short, m.names.names[nid], c))
            c1, d1 = L.Database.select(lst, 0xFFFFFFF8, 0.5)
            c0, d0 = L.Database.select(lst, 0, 0.5)
            if c1 is None or c0 is None:
                err('DB %s name %s selects no clip' % (db.short, m.names.names[nid]))
    # clips
    owner = make_owner(a)
    for i in range(N):
        check_clip(a, i, owner)
    st['tracks'] = sum(len(a.track_block(i).get('tracks', [])) for i in range(N))
    # base preservation
    if base_bytes is not None:
        b = L.AnmFile.parse(base_bytes); ba = b.anim
        if a.recs[:len(ba.recs)] != ba.recs: err('base clip records changed')
        if a.B[:len(ba.B)] != ba.B: err('base clip data changed')
        if a.C[:len(ba.C)] != ba.C or a.E[:len(ba.E)] != ba.E or a.D[:len(ba.D)] != ba.D: err('base tables changed')
        if m.names.names[:len(b.names.names)] != b.names.names: err('base name ids changed')
        for bdb in b.dbs:
            mdb = m.db_by_short(bdb.short)
            if mdb is None:
                err('base DB %s missing' % bdb.short); continue
            for nid, li in enumerate(bdb.index):
                if li is None: continue
                if mdb.get(nid) != bdb.lists[li]:
                    err('base DB %s path %s changed' % (bdb.short, b.names.names[nid]))
                st['base_paths_checked'] += 1
    # source correspondence
    if dm_bytes is not None:
        s = L.AnmFile.parse(dm_bytes); sa = s.anim
        rep = report or {}
        dbr = rep.get('databases', {})
        sigcache = {}

        def ssig(i):
            if ('s', i) not in sigcache: sigcache[('s', i)] = clip_signature(sa, i)
            return sigcache[('s', i)]

        def msig(i):
            if ('m', i) not in sigcache: sigcache[('m', i)] = clip_signature(a, i)
            return sigcache[('m', i)]
        for sdb in s.dbs:
            info = dbr.get(sdb.short.decode())
            if info is None:
                continue
            tdb = m.db_by_short(info['into'].split('+')[0].encode())
            added = set(info.get('added', []))
            for nid, li in enumerate(sdb.index):
                if li is None: continue
                path = s.names.names[nid]
                mid = m.names.id_of(path)
                lst = tdb.get(mid) if mid is not None else None
                if lst is None:
                    err('DM %s path %s does not resolve in %s' % (sdb.short, path, tdb.short)); continue
                st['dm_paths_resolved'] += 1
                if path.decode() in added:
                    slist = sdb.lists[li]
                    if [k for k, _ in slist] != [k for k, _ in lst]:
                        err('DM %s path %s condition keys differ' % (sdb.short, path))
                    for (k1, c1), (k2, c2) in zip(slist, lst):
                        if ssig(c1) != msig(c2):
                            err('DM %s path %s clip %d -> %d data differs' % (sdb.short, path, c1, c2))
                        if sa.D[c1] != a.D[c2]:
                            err('clip name differs for %s' % path)
                    st['dm_added_paths_verified'] += 1
        st['dm_clips_compared'] = len([k for k in sigcache if k[0] == 's'])
    return st


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    mb = open(sys.argv[1], 'rb').read()
    bb = open(sys.argv[2], 'rb').read() if len(sys.argv) > 2 else None
    db = open(sys.argv[3], 'rb').read() if len(sys.argv) > 3 else None
    rep = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else None
    st = verify(mb, bb, db, rep)
    for k, v in st.items():
        print('%-26s %s' % (k, v))
    print('RESULT:', 'PASS' if not errors else 'FAIL (%d errors)' % len(errors))
    return 0 if not errors else 1


if __name__ == '__main__':
    sys.exit(main())
