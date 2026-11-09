# Build validator: static node indices and the h[6] overlap lists of a converted level against its Dead Men source.
#
# Static node indices (clusters.node_order) are baked into the .oct/.sgp/.rmc/.rmi/.sgd/.hrd/.HVK, which are copied as
# is, and into the h[6] overlap lists (CListUser), so every Dead Men entity must keep its node index in the converted
# level, and every entity the converter adds (graft) must come after them.
#
# h[6] (pointer = h[6]+4, the runtime CListUser table, this+0x20): word 0 = word count, words 1..3 header; from word 4
# one slot per entity that has one: head word (0 on disk, the runtime bucket list) then entries v = node*stride + 0x10
# | flags (stride 0x70 Dead Men, 0x80 Dog Days); flag 1 = last entry, flag 2 = range: every node from v up to the next
# entry (kl2 0x8176f0). An entity's slot id (word index of its head) is its decl u4 (low 24 bits; 0 = no slot) =
# object +0x54 at run time. kl2 0x61edc0 (a mover) calls 0x4f8a60(this, [neighbour+0x54] & 0xffffff, ...) for every
# listed neighbour without checking for 0, and slot id 0 reads the table's word count as a bucket head (the M01
# 'CListUser guard (veh): bad bucket id=000000 head=000056cf' from 0x61ee1a). Stock data does list entities without a
# slot (mostly from light lists), so a reference to an id-0 target is only an error when the Dead Men source does not
# have the same reference.
#
# CLI (read only):  py tools\ovlcheck.py <DM _Main.zip or .gms> <converted _Main.zip or .gms> [...pairs]
#                   py tools\ovlcheck.py --all <build root, e.g. work\out_all6>
import os, sys, struct, zlib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clusters import read_ents, node_order

DM_STRIDE, DD_STRIDE = 0x70, 0x80

def _unpack(d):
    return d[9:] if d[8] else zlib.decompressobj(-15).decompress(d[9:])

def load_any(path):
    """raw gms bytes from a level _Main.zip (the .gms entry) or a .gms file"""
    if path.lower().endswith('.zip'):
        import zipfile
        z = zipfile.ZipFile(path)
        nm = [n for n in z.namelist() if n.lower().endswith('_main.gms')]
        assert len(nm) == 1, (path, nm)
        return _unpack(z.read(nm[0]))
    return _unpack(open(path, 'rb').read())

def _info(g):
    h = struct.unpack_from('<20I', g)
    n = struct.unpack_from('<I', g, h[0])[0]
    u4 = [struct.unpack_from('<II', g, h[0] + 4 + 8 * i)[1] & 0xffffff for i in range(n)]
    _, ents = read_ents(g)
    return h, ents, u4, node_order(ents)

def overlap_slots(g, stride):
    """[(slot word index, [(entry word index, flags, node list)])]: each entry expanded like kl2 0x8176f0"""
    h = struct.unpack_from('<20I', g)
    if not (0 < h[6] < len(g)): return 0, []
    o6 = h[6] + 4; n7 = struct.unpack_from('<I', g, o6)[0]
    res = []; i6 = 4
    while i6 < n7:
        s = i6; i6 += 1; seq = []
        while True:
            v = struct.unpack_from('<I', g, o6 + 4 * i6)[0]; seq.append((i6, v)); i6 += 1
            if v & 1: break
        ents = []
        for k, (w, v) in enumerate(seq):
            x = v & ~7
            if not x: ents.append((w, v & 7, [])); continue
            xs = [x]
            if v & 2 and k + 1 < len(seq):
                y = seq[k + 1][1] & ~7; z = x + stride
                while z < y: xs.append(z); z += stride
            ents.append((w, v & 7, [((q - 0x10) // stride) if (q - 0x10) % stride == 0 else None for q in xs]))
        res.append((s, ents))
    return n7, res

def validate(g_dm, g_out, names=None, max_list=8):
    """-> (errors, stats). names(i) (optional) names original entity i in messages."""
    err = []; st = collections.Counter()
    def nm(i): return ('%d %s' % (i, names(i))) if names else str(i)
    h0, e0, u0, nd0 = _info(g_dm)
    h1, e1, u1, nd1 = _info(g_out)
    n0, n1 = len(e0), len(e1)
    # converted entity -> original: original records stay in place (the converter edits them in place; grafted ones
    # are appended), so the record offset identifies them
    by_off = {e['off']: i for i, e in enumerate(e0)}
    orig = [by_off.get(e['off']) for e in e1]
    pos = {}
    for j, i in enumerate(orig):
        if i is None: continue
        if i in pos: err.append('original entity %s appears twice in the converted list (%d, %d)' % (nm(i), pos[i], j))
        pos[i] = j
    missing = [i for i in range(n0) if i not in pos]
    if missing: err.append('%d original entities missing from the converted list (first: %s)' % (len(missing), ', '.join(nm(i) for i in missing[:max_list])))
    # 1. node order: original index i keeps node_order(DM)[i]
    moved = [(i, nd0[i], nd1[pos[i]]) for i in range(n0) if i in pos and nd1[pos[i]] != nd0[i]]
    st['entities'] = n0; st['new entities'] = n1 - len(pos); st['nodes moved'] = len(moved)
    if moved:
        why = collections.Counter('%x->%x' % (e0[i]['type'], e1[pos[i]]['type']) for i in range(n0)
                                  if i in pos and e0[i]['type'] != e1[pos[i]]['type'])
        err.append('%d original entities moved node (first: %s); type changes in this level: %s' % (
            len(moved), '; '.join('%s node %d -> %d' % (nm(i), a, b) for i, a, b in moved[:max_list]),
            ', '.join('%s x%d' % kv for kv in why.most_common(12))))
    newn = sorted(nd1[j] for j in range(n1) if orig[j] is None)
    if newn and newn[0] <= n0:
        err.append('added entities take node %d (must come after the %d original nodes)' % (newn[0], n0))
    # slot ids: unchanged on originals, none on added entities
    chg = [i for i in range(n0) if i in pos and u1[pos[i]] != u0[i]]
    if chg: err.append('%d original entities changed overlap slot id (first: %s)' % (len(chg), ', '.join('%s %#x -> %#x' % (nm(i), u0[i], u1[pos[i]]) for i in chg[:max_list])))
    newslot = [j for j in range(n1) if orig[j] is None and u1[j]]
    if newslot: err.append('%d added entities claim an overlap slot (first converted index %d, slot %#x)' % (len(newslot), newslot[0], u1[newslot[0]]))
    # 2. overlap lists
    w0, s0 = overlap_slots(g_dm, DM_STRIDE)
    w1, s1 = overlap_slots(g_out, DD_STRIDE)
    if w0 != w1 or [s for s, _ in s0] != [s for s, _ in s1]:
        err.append('overlap table layout differs (words %#x -> %#x, slots %d -> %d)' % (w0, w1, len(s0), len(s1)))
        return err, st
    ent0 = {v: i for i, v in enumerate(nd0)}; ent1 = {v: j for j, v in enumerate(nd1)}
    slot_owner0 = {u: i for i, u in enumerate(u0) if u}
    bad = collections.Counter(); ex = collections.defaultdict(list)
    def note(kind, msg):
        bad[kind] += 1
        if len(ex[kind]) < max_list: ex[kind].append(msg)
    for (s, ea), (_, eb) in zip(s0, s1):
        own = slot_owner0.get(s)
        for (w, fa, la), (_, fb, lb) in zip(ea, eb):
            if fa != fb: note('flags changed', 'word %#x' % w); continue
            if len(la) != len(lb): note('range length changed', 'word %#x: %d -> %d nodes' % (w, len(la), len(lb))); continue
            for a, b in zip(la, lb):
                st['overlap references'] += 1
                if b is None or b < 1 or b not in ent1:
                    note('invalid node', 'slot %#x (%s) word %#x -> node %s' % (s, nm(own) if own is not None else '-', w, b)); continue
                j = ent1[b]; i = ent0.get(a)
                if orig[j] is None:
                    note('grafted target', 'slot %#x (%s) -> node %d (added entity)' % (s, nm(own) if own is not None else '-', b)); continue
                if orig[j] != i:
                    note('different target', 'slot %#x (%s) -> node %d: %s in Dead Men, %s converted' % (
                        s, nm(own) if own is not None else '-', b, nm(i) if i is not None else '?', nm(orig[j])))
                    continue
                if u1[j] == 0:
                    if i is not None and u0[i] != 0:
                        note('slot id 0 target (introduced)', 'slot %#x (%s) -> node %d %s' % (s, nm(own) if own is not None else '-', b, nm(orig[j])))
                    else: st['references to slot id 0 targets (as in Dead Men)'] += 1
    for k in sorted(bad):
        err.append('overlap: %d %s (first: %s)' % (bad[k], k, '; '.join(ex[k])))
    return err, st

def names_from(g, buf):
    h = struct.unpack_from('<20I', g)
    _, ents = read_ents(g)
    def f(i):
        o = struct.unpack_from('<I', g, ents[i]['off'])[0]
        try: return bytes(buf[o:buf.index(b'\0', o)]).decode('latin1')[-60:]
        except ValueError: return '?'
    return f

def check_or_die(g_dm, g_out, buf_dm, rep, label=''):
    err, st = validate(g_dm, g_out, names_from(g_dm, buf_dm))
    for k, v in st.items(): rep['validate %s %s' % (k, v)] += 1
    if err:
        raise SystemExit('BUILD VALIDATION FAILED%s (node order / overlap lists; ANP_VALIDATE=0 skips):\n  %s' % (
            ' ' + label if label else '', '\n  '.join(err)))
    rep['validate OK: node order and overlap lists match the Dead Men source'] += 1

# ---- CLI ----
DM_SCENE = {'M01': 'M01_A', 'M02': 'M02_A', 'M03': 'M03_A', 'M03B': 'M03_B', 'M05': 'M05_A', 'M06': 'M06_A', 'M07': 'M07_A',
            'M08': 'M08_A', 'M09': 'M09_A', 'M09B': 'M09_B', 'M11': 'M11_A', 'M11B': 'M11_B', 'M12': 'M12_A', 'M13': 'M13_A',
            'M13B': 'M13_B', 'M14': 'M14_A'}

def dm_zip(level):
    from anp_paths import game_dir, DM_FOLDER
    f = DM_SCENE[level]
    return os.path.join(game_dir('ANP_DM_GAME', DM_FOLDER), 'Scenes', 'Locations', f, f.replace('_', '') + '_Main.zip')

def _dm_buf(path):
    import zipfile
    z = zipfile.ZipFile(path); nm = [n for n in z.namelist() if n.lower().endswith('_main.buf')]
    return z.read(nm[0])

def run_pair(dm_path, out_path, label):
    g0 = load_any(dm_path); g1 = load_any(out_path)
    buf = _dm_buf(dm_path) if dm_path.lower().endswith('.zip') else open(dm_path[:-4] + '.buf', 'rb').read()
    err, st = validate(g0, g1, names_from(g0, buf))
    print('%-6s %s  %s' % (label, 'FAIL' if err else 'OK', ', '.join('%s %s' % kv for kv in sorted(st.items()))))
    for e in err: print('    ' + e)
    return not err

if __name__ == '__main__':
    a = sys.argv[1:]
    ok = True
    if a and a[0] == '--all':
        root = a[1]
        for lv in DM_SCENE:
            p = os.path.join(root, lv, lv + '_Main.zip')
            if not os.path.exists(p): print('%-6s missing %s' % (lv, p)); ok = False; continue
            ok &= run_pair(dm_zip(lv), p, lv)
    else:
        for k in range(0, len(a), 2): ok &= run_pair(a[k], a[k + 1], os.path.basename(a[k + 1]))
    sys.exit(0 if ok else 1)
