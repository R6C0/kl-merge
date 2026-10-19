"""
Slot-order fingerprint of a map, for the private-match question "will two PCs agree on net ids?".

    python tools/kl_netcheck.py <zip or .gms> [<zip or .gms>]

Prints one line per map: fingerprint (sha1 prefix), entity count, md5 of the file as given (the whole
zip for a zip). With two maps it also says SAME SLOT ORDER or DIFFERENT and, for DIFFERENT, the first
entity index where they part and why. Read only; writes nothing but stdout.

Background (re/private_match.md): the net id of a level-loaded object is its loader pool slot index
+ 1 (tag 0). The loader (kl2 0x8ad7c0) gives each entity a 128-byte slot from pool
[category + 8 * pool group] of its parent group's block, in .gms entity-table order.

CHECKED (from that file and kl_gms.rebuild_clusters): the fingerprint covers exactly what decides the
slot of every entity - the entity table order, each entity's type id, its pool group (record +0x35),
its category (kl_gms.category, kl2 0x829b10), the parent group's cluster block, its ordinal inside
that block's pool, the tree shape (pops / children bits of the table word) and the cluster table
itself (pool counts per block, as stored in the file). Nothing else enters.
GUESS / NOT COVERED: the .prp values, .buf, .oct, .HVK, textures and sounds also feed the simulation and
are NOT in the fingerprint; no version or hash check was found in the engine. So the same fingerprint
is NECESSARY for equal ids, not sufficient (use the zip md5 for that). Also a GUESS: the loader's 0x80
blocks are contiguous and the pool capacity is the same on both PCs (it depends on the first map loaded).
A DIFFERENT result is reliable only as far as the model above is right: the slots do differ then.
"""
import sys, os, struct, zipfile, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_gms


def read_gms(path):
    """-> (gms bytes, md5 of the file as given). A zip is searched for its single .gms."""
    data = open(path, 'rb').read()
    md5 = hashlib.md5(data).hexdigest()
    if path.lower().endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith('.gms')]
            if len(names) != 1:
                raise ValueError('%s: expected one .gms, found %s' % (path, names))
            data = z.read(names[0])
    return data, md5


def slot_model(f):
    """-> (rows, cluster table bytes). rows[i] = (type id, pool group, category, parent block,
    pool index, ordinal in that pool, pops, has children), in entity-table order."""
    raw = kl_gms.unpack(f)
    ents = kl_gms.entities(raw)
    ctab = struct.unpack_from('<I', raw, 0x14)[0]
    nblocks = struct.unpack_from('<I', raw, ctab)[0]
    cl = raw[ctab:ctab + 4 + 96 * nblocks]
    counts = {}
    rows = []
    stack, nxt, pending = [0], 1, None
    for decl, tid, prio in ents:
        pops = decl >> 25
        for _ in range(pops):
            stack.pop()
        if pending is not None:
            stack.append(pending); pending = None
        cat = kl_gms.category(tid)
        pool = cat + 8 * prio
        blk = stack[-1]
        ordinal = counts.get((blk, pool), 0)
        counts[(blk, pool)] = ordinal + 1
        rows.append((tid, prio, cat, blk, pool, ordinal, pops, bool(decl & 0x1000000)))
        mine = None
        if tid & kl_gms.GROUP:
            mine = nxt; nxt += 1
        if decl & 0x1000000:
            if mine is None:
                raise ValueError('non-group entity %#x has children' % tid)
            pending = mine
    return rows, cl


def fingerprint(rows, cl):
    h = hashlib.sha1()
    for r in rows:
        h.update(struct.pack('<IBBIBIIB', r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]))
    h.update(cl)
    return h.hexdigest()[:16]


WHY = ('type id', 'pool group', 'category', 'cluster block (parent group)', 'pool', 'ordinal in pool',
       'tree pops', 'has children')


def compare(a, b):
    (ra, ca), (rb, cb) = a, b
    for i in range(min(len(ra), len(rb))):
        if ra[i] != rb[i]:
            why = [WHY[k] + ' %s vs %s' % (hex(ra[i][k]) if k == 0 else ra[i][k],
                                            hex(rb[i][k]) if k == 0 else rb[i][k])
                   for k in range(8) if ra[i][k] != rb[i][k]]
            return 'entity %d: %s' % (i, '; '.join(why))
    if len(ra) != len(rb):
        return 'entity %d: one map ends (%d vs %d entities)' % (min(len(ra), len(rb)), len(ra), len(rb))
    if ca != cb:
        nb = min(len(ca), len(cb)) // 4
        k = next((j for j in range(nb) if ca[4 * j:4 * j + 4] != cb[4 * j:4 * j + 4]), nb)
        return ('same entity list, cluster table differs at dword %d (block %d, pool %d)'
                % (k, max(k - 1, 0) // 24, max(k - 1, 0) % 24))
    return None


def main(argv):
    if not 1 <= len(argv) <= 2:
        print(__doc__)
        return 2
    models = []
    for p in argv:
        f, md5 = read_gms(p)
        m = slot_model(f)
        models.append(m)
        print('%s  fingerprint %s  entities %d  md5 %s' % (p, fingerprint(*m), len(m[0]), md5))
    if len(models) == 2:
        d = compare(*models)
        print('SAME SLOT ORDER' if d is None else 'DIFFERENT, first at ' + d)
        print('(necessary, not sufficient: .prp / .buf / .oct / .HVK are not compared)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
