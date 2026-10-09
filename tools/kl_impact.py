#!/usr/bin/env python3
"""
What a projectile impact looks up in a level, checked offline; and the repair of the one table the
graft left inconsistent (owner's crash of 2026-10-09 17:41, re/crash_owner_1009.md).

THE IMPACT PATH (kl2.exe; ZProjectileBase slot 36 = 0x512ca0)
  0x512ed7 -> 0x4e5040   surface row of the thing hit: rows + (index - 1) * row size, NO bounds test.
                         The index comes from the .HVK sub-part that was hit (kl_hvk.resurface).
  0x512fa5 -> 0x6367f0   the mark the hit leaves. Two cells of the surface row (property ids at
                         0x1538d98 / 0x1538d9c, read through 0x4e5040 / 0x6d3b80) give the entity
                         that holds the mark's picture. If the thing hit is a PERSON (0x7f7fb0) the
                         mark goes on the skinned mesh:
                           ZRenderDraw slot 21 (0x5c3490) -> 0x479c80 (ten marks per person, a ring)
                           -> 0x88c840:  matrices = 0x78c710(person)          48 B per bone
                                         table    = render vcall +0xc0       = skeleton table [5]
                                         bone     = table[ hit +0x28 ]        BONE ID -> bone index
                                         m        = matrices + 48 * bone      NO test for 0xff
                                         0x4c34a0(point, m + 0x24)            <- the fault
  hit +0x28 is a BONE ID. It is taken from the 64-byte bone definition of the bone the bullet
  struck: byte +0x3e = the bone's id, byte +0x3f = its body part (0x636b2a tests 2 / 3 for the
  head). Other readers of +0x3e: 0x763f00 (ZAppendage slot 13 0x462590), 0x56b0e0, ZPhysicsLinkage
  slot 14 (0x80bd20) - each sends the id back through table [5] (render vcall +0x24c / +0xc0).

So a skeleton holds its bone ids TWICE and the two must agree:
  table [5]  (256 B)           bone id -> bone index (0xff none)         kl_chars docstring
  bone definition +0x3e (u8)   bone index -> bone id                     NEW here
Stock: every bone of every skeleton of the 41 levels of both games agrees (`python kl_impact.py
stock`). kl_chars.reid() - which kl_graft runs on the skeletons of a Dead Men map and kl_chars.put
on a transplanted player model - rewrote table [5] alone. A bullet in a bone whose id had changed
then carried the OLD id; where the level's numbering has no bone of that model under that id the
table says 0xff and the engine reads matrix 255 (0x2fd0 bytes past the start of ~100 matrices):
garbage, and a fault when that address is not mapped. Retomoto: guard skeleton, bone 22
LEFT_FORETWIST1, id 0x68 in M09_A, 0x4f after reid; table[0x68] = 0xff.

    python kl_impact.py <built level: folder or *_Main.zip, or a stock level name> ...
    python kl_impact.py stock                      the 41 stock levels: problems 0
    python kl_impact.py fix <folder> <new folder>  a repaired copy of a built level (bone ids only)

For kl_graft (after the reid / rebind loop, before `prm_bytes = G.write(prm)`):
    done['bone id bytes'] += kl_impact.sync_bone_ids(prm, sks)
and in verify():  bad += kl_impact.bone_faults(G.read(out['.prm'], 'dd'))
For kl_chars.put (after `renamed = reid(ex, sk, ids)`):  kl_impact.sync_bone_ids(ex, [sk])
"""
import os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_prmgraph as G

BONE = 64            # bytes per bone definition (skeleton slot 1)
ID_AT = 0x3e         # the bone's id; +0x3f is its body part (1 trunk, 2 head, 4 / 5 left arm, 7 / 8 right arm, 6 / 9 legs: read off M09_A's guard, not decoded further)


def _skeletons(p):
    import kl_chars
    return kl_chars.skeletons(p)


def _name(d, b):
    return d[BONE * b + 0x1c:BONE * b + ID_AT].split(b'\0')[0].decode('latin1')


def bone_faults(p, sks=None, limit=4):
    """Skeletons whose two bone-id tables disagree: [text]. A fault is a bone b whose own id
    (definition +0x3e) does not lead back to b through table [5]; 'no bone' (0xff) is the crash,
    'another bone' puts the mark (and whatever ZPhysicsLinkage / ZAppendage attach) on the wrong bone."""
    bad = []
    for sk in (_skeletons(p) if sks is None else sks):
        h = struct.unpack('<20I', p.chunks[sk]); n = h[0]
        d, t5 = p.chunks[h[1]], p.chunks[h[5]]
        if len(d) < BONE * n or len(t5) < 256:
            bad.append('skeleton %d: bone definitions or id table too short' % sk); continue
        past = [i for i in range(256) if t5[i] != 0xff and t5[i] >= n]
        if past:
            bad.append('skeleton %d: id table names a bone past the %d of the model (ids %s)' % (sk, n, past[:limit]))
        none = [(b, d[BONE * b + ID_AT]) for b in range(n) if t5[d[BONE * b + ID_AT]] == 0xff]
        other = [(b, d[BONE * b + ID_AT]) for b in range(n) if t5[d[BONE * b + ID_AT]] not in (0xff, b)]
        if none:
            bad.append('skeleton %d (%d bones): %d bones carry an id the id table gives to NO bone - a hit there reads matrix 255 (kl2 0x88c8cb): %s' % (
                sk, n, len(none), ', '.join('%s %#x' % (_name(d, b), i) for b, i in none[:limit])))
        if other:
            bad.append('skeleton %d (%d bones): %d bones carry an id the id table gives to another bone: %s' % (
                sk, n, len(other), ', '.join('%s %#x -> %s' % (_name(d, b), i, _name(d, t5[i])) for b, i in other[:limit])))
    return bad


def sync_bone_ids(p, sks=None):
    """Bone definition +0x3e of every bone set to the id table [5] gives it, table [5] being what
    kl_chars.reid() wrote. A bone that already carries one of its ids keeps it (alias_free_bone gives
    GROUND a second id, 33). The definitions become a NEW chunk at the end (a data chunk can serve two
    skeletons, and no index moves). Returns the number of bones changed. Raises for a bone table [5]
    does not name at all: there is no id to write (never in a stock level, never after reid)."""
    changed = 0
    for sk in (_skeletons(p) if sks is None else sks):
        h = list(struct.unpack('<20I', p.chunks[sk])); n = h[0]
        d, t5 = bytearray(p.chunks[h[1]]), p.chunks[h[5]]
        ids = {}
        for i in range(255, -1, -1):                    # the smallest id wins
            if t5[i] != 0xff:
                ids[t5[i]] = i
        k = 0
        for b in range(n):
            if t5[d[BONE * b + ID_AT]] == b:
                continue
            if b not in ids:
                raise ValueError('skeleton %d: bone %d (%s) has no id in table [5]' % (sk, b, _name(d, b)))
            d[BONE * b + ID_AT] = ids[b]; k += 1
        if k:
            p.chunks.append(bytes(d)); p.refs.append(1)
            h[1] = len(p.chunks) - 1
            p.chunks[sk] = struct.pack('<20I', *h)
            changed += k
    return changed


def surface_faults(gms, buf, hvk):
    """The two impact lookups kl_graft.verify already tests, here for any archive: an .HVK sub-part
    naming a surface row past the table (kl2 0x4e5068, run M02b) and a surface cell naming an
    entity that is not in the level (REF label)."""
    import kl_gms, kl_scene, kl_hvk, kl_members as MB
    bad = []
    sc = kl_scene.Scene(kl_gms.unpack(gms), buf)
    table = MB.SurfaceTable(sc.tail)
    refs = {e.ref for e in sc.entities()}
    gone = table.refs() - refs
    if gone:
        bad.append('surface table: %d cells name an entity that is not in the level (REF %s)' % (len(gone), sorted(gone)[:4]))
    past = sum(1 for s in kl_hvk.Hvk(hvk).shapes for su, _f, _n in s.sub if su > len(table.materials))
    if past:
        bad.append('.HVK: %d sub-parts name a surface row past the %d of the table' % (past, len(table.materials)))
    return bad


def _open(src):
    """(label, game, {'.prm': bytes ...}) of a folder with one *_Main.zip, an archive, or a stock level name."""
    game = 'dd'
    if os.path.isdir(src):
        src = next(os.path.join(src, f) for f in sorted(os.listdir(src)) if f.lower().endswith('_main.zip'))
    elif not os.path.isfile(src):
        import kl_prpjoin as J
        game = 'dm' if src.startswith('M') else 'dd'
        src = J.level_zip(src, game)
    with zipfile.ZipFile(src) as z:
        files = {n.rsplit('_Main', 1)[1]: z.read(n) for n in z.namelist() if '_Main' in n and n.rsplit('.', 1)[-1] in ('prm', 'gms', 'buf', 'HVK')}
    return src, game, files


def check(src, game=None, surface=True):
    """Every impact reference of a level that would index out of range or resolve to nothing: [text]."""
    path, g, files = _open(src)
    game = game or g
    bad = bone_faults(G.read(files['.prm'], game))
    if surface and game == 'dd':                        # Dead Men's .gms / .HVK are not what kl_scene / kl_hvk were proven on here
        bad += surface_faults(files['.gms'], files['.buf'], files['.HVK'])
    return bad


def fix(src, dst, log=print):
    """A copy of the built level in folder `src` with the bone ids repaired, in folder `dst`."""
    import kl_chars
    lv = kl_chars.Lv(src)
    p = G.read(lv['.prm'], 'dd')
    n = sync_bone_ids(p)
    lv['.prm'] = G.write(p)
    left = bone_faults(G.read(lv['.prm'], 'dd'))
    if left:
        raise ValueError('still wrong after the repair: %s' % left[:3])
    path = lv.write(dst, lv.name)
    log('%s: %d bone ids rewritten -> %s' % (src, n, path))
    return path


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == 'fix':
        fix(a[1], a[2]); sys.exit(0)
    if a[0] == 'stock':
        import kl_chars
        todo = [(z, game) for game, _name_, z in kl_chars.stock_levels()]
    else:
        todo = [(x, None) for x in a]
    total = 0
    for src, game in todo:
        bad = check(src, game)
        total += len(bad)
        print('%s: %s' % (src, 'problems: 0' if not bad else 'problems: %d' % len(bad)))
        for b in bad:
            print('   ' + b)
    print('problems: %d in %d levels' % (total, len(todo)))
    sys.exit(1 if total else 0)
