"""check_passes.py <_Main.zip | build folder> [--game dd|dm]   pre-flight for the two load-crash classes found on 2026-10-17, plus cheap
cross-member consistency. Read only, nothing is installed or launched. One line per check ('PASS' / 'FAIL' / 'SKIP'); exit status 1 if any FAIL.
A folder is searched recursively for *_Main.zip and each archive is checked. Typical cost: 10-40 s per map (the .prm is only read through its
chunk table and the 64-byte type-7 roots).

CRASH SITES
  A  kl2 0x6ad1c3 (vault door2, F07 build 3e39da4e): a .prm type-7 model root (64-byte chunk, header 00 01 07 00) holds at +0x1c a .oct byte
     offset: (record offset + 4) | 1, or 0 for no octree (loader 0x6ad0f9: type 7 -> +0x1c, bit 0 -> add the .oct base). After a member mix the
     offsets pointed into the middle of .oct trees and the engine read garbage (read 0x8000cb1b). Check: every such value is one of the offsets
     at which a real .oct record header starts. Records are found by walking the .oct (room trees by their sizes, then records up to the u32 -1),
     each record header is validated the way kl_octree.Oct.parse does. Also: the .oct tail's {first triangle, .prm chunk} pairs name chunks that exist.
  B  kl2 0x4c63f2 (Hasta M11B, build f44a4048): a top-level 'CloneGroup_*' holds ZAllocMany copies (+0x5e = 1) whose template was dropped, so the
     copy's template pointer (+0x58) stays null and the first ZParticleEmitter reads it. Check: kl_prpjoin.orphan_clone_groups(scene) is empty
     (kl_fa_hasta_layer.orphan_clones is the same rule, applied before the join).
  C  cross-member consistency (each of these is a precondition of the loader, none was a crash by itself yet):
     C1 .gms entity count + 1 (ROOT) = .prp node count   C2 every .gms record +0x0c (the .prm chunk of the model) < .prm chunk count
     C3 .rmi / .rmc box ids are SLOT ids (kl_scene slot + 2, NOT REF labels, see CLAUDE.md) of ZROOM-derived entities; a second id, when set,
     is any entity (a ZBOUND in stock files)

Verified 2026-10-17: FAIL on vault2 F07_Main.crashed-3e39da4e.zip (A) and on Hasta M11B f44a4048 (B); PASS on the installed DM03A 706cfc8d,
vault_door3_1017 70ad9bc5 and Hasta M11B_fix c23cb618.
"""
import glob, os, struct, sys, time, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import kl_gms, kl_scene, kl_octree as O
import kl_prpjoin as J
from kl_prp import Prp


class Report:
    def __init__(self, name):
        self.name, self.fails = name, 0

    def line(self, state, what, msg):
        if state == 'FAIL':
            self.fails += 1
        print('%-4s %-24s %s' % (state, what, msg), flush=True)


def oct_record_offsets(data):
    """-> (set of the values a type-7 root may hold for the records, tail pairs [(first triangle, chunk)]). Raises ValueError on a malformed file.
    Same walk as kl_octree.Oct.parse, without building the trees."""
    n = len(data)
    o = 0x10
    while True:                                           # room trees: five slots per room
        size = struct.unpack_from('<I', data, o)[0]
        if size == 0xffffffff or (size and struct.unpack_from('<I', data, o + 0x14)[0]):
            break
        for _ in range(5):
            size = struct.unpack_from('<I', data, o)[0]
            if not size:
                o += 16
            else:
                o += 0x20 + size
            if o > n - 4:
                raise ValueError('room trees run past the end of the file')
    refs = set()
    while struct.unpack_from('<I', data, o)[0] != 0xffffffff:
        size = struct.unpack_from('<I', data, o)[0]
        if size < 0x20 or o + size > n:
            raise ValueError('record at %#x has size %#x' % (o, size))
        zero = struct.unpack_from('<I', data, o + 0x1c)[0]
        if zero or data[o + 8:o + 0x18] != data[o + 0x24:o + 0x34]:
            raise ValueError('record header at %#x is not a ZOctreeCompiled record' % o)
        refs.add((o + 4) | 1)
        o += size
    if (n - o - 4) % 8:
        raise ValueError('tail is not made of pairs')
    return refs, [struct.unpack_from('<II', data, k) for k in range(o + 4, n, 8)]


def prm_table(prm):
    t, n, t2, z = struct.unpack_from('<4I', prm, 0)
    if t != t2 or z or t + 16 * n != len(prm):
        raise ValueError('not a .prm chunk table')
    return t, n


def check_zip(path, game=None):
    rep = Report(path)
    t0 = time.time()
    print('== %s' % path, flush=True)
    try:
        zf = zipfile.ZipFile(path)
    except Exception as x:
        rep.line('FAIL', 'open', repr(x))
        return rep
    mem = {}
    for nm in zf.namelist():
        low = nm.lower()
        if '_main.' in low and low.rsplit('.', 1)[-1] in ('prp', 'gms', 'buf', 'oct', 'rmi', 'rmc', 'prm'):
            mem[low.rsplit('.', 1)[-1]] = nm
    need = [e for e in ('prp', 'gms', 'buf', 'oct', 'prm') if e not in mem]
    if need:
        rep.line('FAIL', 'members', 'missing .%s' % ', .'.join(need))
        return rep
    rd = lambda e: zf.read(mem[e])
    prm, oct_ = rd('prm'), rd('oct')

    # ---- A: .prm type-7 roots -> .oct records
    try:
        refs, tail = oct_record_offsets(oct_)
        t, n = prm_table(prm)
        n7 = zero = 0
        bad = []
        for i, (off, size, _r, _z) in enumerate(struct.iter_unpack('<4I', memoryview(prm)[t:t + 16 * n])):
            if size == 64 and i and prm[off:off + 4] == b'\0\1\7\0':
                n7 += 1
                v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                if v == 0:
                    zero += 1
                elif v not in refs:
                    bad.append((i, v))
        badtail = sum(1 for _a, c in tail if not 0 < c < n)
        st = 'FAIL' if bad or badtail else 'PASS'
        msg = '%d type-7 roots, %d without an octree, %d .oct records' % (n7, zero, len(refs))
        if bad:
            msg += '; %d roots point INTO the .oct, not at a record (first: chunk %d value %#x, record %#x)' % (
                len(bad), bad[0][0], bad[0][1], (bad[0][1] & ~1) - 4)
        if badtail:
            msg += '; %d .oct tail pairs name no .prm chunk' % badtail
        rep.line(st, 'A oct-offsets', msg + '  [kl2 0x6ad1c3]')
    except Exception as x:
        rep.line('FAIL', 'A oct-offsets', 'unreadable: %r  [kl2 0x6ad1c3]' % (x,))
        n = None

    # ---- scene
    sc = None
    try:
        prp = Prp(rd('prp'))
        raw = kl_gms.unpack(rd('gms'))
        buf = rd('buf')
        ents = kl_gms.entities(raw)
        nprp = len(prp.nodes())
        if nprp == len(ents) + 1:
            rep.line('PASS', 'C1 node count', '.gms %d entities + ROOT = .prp %d nodes' % (len(ents), nprp))
        else:
            rep.line('FAIL', 'C1 node count', '.gms %d entities + ROOT, but .prp has %d nodes' % (len(ents), nprp))
            ents = None
    except Exception as x:
        rep.line('FAIL', 'C1 node count', 'unreadable: %r' % (x,))
        ents = None

    # ---- C2: .gms record +0x0c < chunk count
    if ents is not None and n is not None:
        bad = []
        for k, (decl, _tid, _prio) in enumerate(ents):
            c = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff) + 0x0c)[0]
            if c >= n:
                bad.append((k + 1, c))
        rep.line('FAIL' if bad else 'PASS', 'C2 gms model chunks',
                 ('%d of %d records name a chunk >= %d (first: node %d -> %d)' % (len(bad), len(ents), n, bad[0][0], bad[0][1]))
                 if bad else 'all %d records < %d chunks' % (len(ents), n))
    else:
        rep.line('SKIP', 'C2 gms model chunks', 'needs C1 and the .prm table')

    # ---- B: orphan clone groups
    if ents is not None:
        try:
            g = game or kl_scene.Scene(raw, buf).game
            names, tids = ['ROOT'], [J.kl_rtp.ROOT_TYPE]
            for decl, tid, _p in ents:
                o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
                names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
            sc = J.Scene(prp, names, tids, g, path)
            orph = J.orphan_clone_groups(sc)
            # stock Dead Men levels (M02, M03, M06 ...) hold NESTED groups 'CloneGroup_ROOT/CloneGroup_<x>': copies of a ZAllocMany that itself lives
            # in the clone group 'CloneGroup_<x>', so the template exists (inside a clone group) and orphan_clone_groups, which looks outside the
            # clone groups only, flags them. The installed DM05A heli (loaded live) carries one: not an orphan.
            nest = 'CloneGroup_ROOT/CloneGroup_'
            inner = []
            for k in range(1, len(sc.nodes)):
                if sc.cls(k) == 'ZAllocMany':
                    top = sc.path[k].split('\\')[1] if '\\' in sc.path[k] else ''
                    if top.startswith('CloneGroup_') and not top.startswith('CloneGroup_ROOT'):
                        inner.append(J.tpl_key(sc.path[k]).replace('clonegroup_', ''))
            orph = [t for t in orph if not (sc.names[t].startswith(nest) and any(h.endswith(sc.names[t][len(nest):].lower()) for h in inner))]
            ncg = sum(1 for t in sc.tops() if sc.names[t].startswith('CloneGroup_'))
            # the proven crash is the copy's ParticleEmitter reading the null template; an orphan group of plain geometry (Shards_Group_A of the
            # vault and Hasta builds, which the installed 706cfc8d carries and loads) is reported but does not fail
            emit = [t for t in orph if any(sc.cls(k) == 'ZParticleEmitter' for k in range(t, sc.end[t]))]
            quiet = [t for t in orph if t not in emit]
            short = lambda ts: ', '.join(sc.names[t].split('/')[-1] for t in ts)
            if emit:
                rep.line('FAIL', 'B orphan clones', '%d clone group(s) with ZParticleEmitter copies and no template: %s  [kl2 0x4c63f2]' % (len(emit), short(emit)))
            else:
                rep.line('PASS', 'B orphan clones', '%d clone groups, none with emitters and no template' % ncg)
            if quiet:
                rep.line('WARN', 'B orphan (no emitters)', '%d without a template but no ZParticleEmitter under them: %s' % (len(quiet), short(quiet)))
        except Exception as x:
            rep.line('FAIL', 'B orphan clones', 'unreadable: %r' % (x,))
    else:
        rep.line('SKIP', 'B orphan clones', 'needs C1')

    # ---- C3: .rmi / .rmc ids are slot ids of rooms
    try:
        ks = kl_scene.Scene(raw, buf)
        sch = J.schema(ks.game)
        by_slot = {s + 2: e for e, s in ks.slots().items()}
        for ext in ('rmi', 'rmc'):
            if ext not in mem:
                rep.line('SKIP', 'C3 %s ids' % ext, 'no .%s member' % ext)
                continue
            boxes = O.RoomIndex.parse(rd(ext)).boxes
            bad = [b for b in boxes if b.room not in by_slot or 'ZROOM' not in sch.bases(sch.geoms.get(by_slot[b.room].tid, ''))]
            bad2 = [b for b in boxes if b.second and b.second not in by_slot]
            if bad or bad2:
                rep.line('FAIL', 'C3 %s ids' % ext, '%d of %d boxes name no room slot (first id %d), %d second ids name no entity  [kl2 0x719884]' % (
                    len(bad), len(boxes), bad[0].room if bad else 0, len(bad2)))
            else:
                rep.line('PASS', 'C3 %s ids' % ext, 'all %d boxes name a ZROOM slot id' % len(boxes))
    except Exception as x:
        rep.line('FAIL', 'C3 rmi/rmc ids', 'unreadable: %r' % (x,))

    print('     %s: %s in %.0f s' % ('FAILED' if rep.fails else 'ok', os.path.basename(path), time.time() - t0), flush=True)
    return rep


def main(argv):
    game = None
    if '--game' in argv:
        i = argv.index('--game')
        game = argv[i + 1]
        del argv[i:i + 2]
    if len(argv) != 1:
        sys.exit(__doc__.split('\n')[0])
    src = argv[0]
    zips = [src] if os.path.isfile(src) else sorted(glob.glob(os.path.join(glob.escape(src), '**', '*_Main.zip'), recursive=True))
    if not zips:
        sys.exit('no _Main.zip under %s' % src)
    fails = sum(check_zip(z, game).fails for z in zips)
    print('%d archive(s), %d failed check(s)' % (len(zips), fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
