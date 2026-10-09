"""
Kane & Lynch .prm geometry converter (Dead Men -> Dog Days).

The file is a table of chunks that name each other by index; kl_prmgraph.py describes every
chunk kind and finds them by walking from the roots (.gms record +0x0c and the .prp fields in
kl_prmgraph.PRP_FIELDS). Nothing here is found by size: the earlier size heuristic
(find_descriptors, removed) missed every mesh descriptor with baked lighting, 26,705 of the
91,960 in Dead Men, and left them in Dead Men's 32-byte form.

convert() keeps every chunk index, so the .gms, the .prp and the .oct (which name chunks) need
no rewriting; new chunks are appended. What it changes, and what is lost:

  mesh descriptor   32 -> 48 bytes: Dead Men [vertex count, vtx, number, idx, lit, lit5, 0, 0]
                    -> Dog Days [vertex count, vtx, 0, 0, 0, number, idx, 0 x5]. Dog Days [5] =
                    Dead Men [2] (equal in 388 of 388 meshes whose vertex and index chunks are
                    byte-identical in both games; what the number means is not established).
  baked lighting    a lit descriptor names a per-instance stream (8 bytes per vertex: a colour
                    and 0) and a shared 16-byte light record; its mesh has draw-mode bit
                    0x01000000 (+0x1c). Dog Days has neither field and never sets the bit (0 of
                    94,851 meshes). The fields are dropped and the bit cleared.
                    LOST: the baked contribution of static lights on those meshes (M02_FA 1375,
                    M03_FA 2250, M09_A 755, M09_B 966 meshes); they will be lit by Dog Days'
                    own lighting only.
  scatter (lType 9) Dead Men's record is 256 bytes (procedural vegetation: material class
                    ScatterNew, three data chunks), Dog Days' is 144 bytes (hand-placed light
                    billboards: class ScatterManual, instance list in the next chunk). The render
                    object is chosen by the MATERIAL CLASS, not by the entity: ZScatterObj
                    overrides nothing of ZSTDOBJ but the property list (vtable diff, both exes),
                    and kl2.exe still registers a class "ScatterNew" (factory 0x7ba570, record at
                    0xcdbeb0) next to "ScatterManual" (0x5526e0) - but no Dog Days shader cache
                    has a compiled ScatterNew.fx, so the Dead Men record cannot be drawn there,
                    and read as a ScatterManual record its count (+0x5c) is float garbage.
                    DECISION: each scatter object becomes an ordinary mesh that draws nothing:
                    a copy of the smallest plain 40-byte-vertex mesh object of the same file
                    (so material, flags and vertex format are a combination Dog Days already
                    draws) with one zero-area triangle at the scatter's bounding-box corner. The
                    object keeps its index, so roots, entities and .oct stay as they are.
                    LOST: all scattered grass / bushes / leaves (M01_FA 4 objects, M06_FA 145,
                    M09_A 1, M09_B 11). ASSUMPTION: a root whose only object is such a mesh is
                    harmless; nothing like it is in a stock level (stock L05 has one mesh with 0
                    vertices among five objects of a root, which is why 3 real vertices are used).
  water (lType 11)  Dead Men only (5 objects in the whole game, none in the FA maps or M09):
                    treated like scatter. Untested in a level that matters.
  prop slot 2       Dead Men only (a 16-byte record [1, colour, 0, 1.0] on flat floor models;
                    the root has flag 0x10 at +0x0c exactly when its prop has slot 2, which
                    convert() asserts). Slot and flag are cleared. LOST: whatever it drove
                    (ASSUMPTION: the planar "Reflection2D" floors, a Dead Men-only material feature).
  font              glyph record 20 -> 32 bytes and texture bias 2048 -> 4096 (the .TEX table
                    size, see kl_prmgraph). Layout from the data of both games, NOT from code
                    (the reader was not found in either exe): ASSUMPTION throughout.
                      Dead Men: u32 char, u32 texture, u8 x0 y0 x1 y1, u8 w h, s8 dx dy,
                                u8 advance, u8 line height, u8 flag, u8 pad (0xcd)
                      Dog Days: the same fields as u16 / s16, pad 0xcdcd
                    Checked on 11,688 Dead Men and 11,352 Dog Days glyphs: w = (x1 - x0) * page
                    width / N and h likewise, with N = 128 in Dead Men and 512 in Dog Days
                    (whatever the page size: 128 and 256 pixel pages there, 512 and 256 here), so
                    coordinates are multiplied by 4. Header dword 8 is 2 in every Dead Men font
                    and 3 in every Dog Days font: written as 3 (ASSUMPTION: a version). Header
                    dword 7 (4..10 in Dead Men, always 2 in Dog Days) is copied: unknown.
                    The kerning table after the glyphs (u16 a, u16 b, s32) is the same.
                    A graft takes HUD and menus from Dog Days, so this path is for completeness.
  unreferenced      the light streams, light records, scatter data and prop-2 records nothing
                    names any more are cut to 16 zero bytes (indices must stay).
Not changed (same in both games): roots, object tables, 64- and 128-byte mesh objects, vertex
and index data, skeletons, sprites, lights, window pictures, post-filter chunks. Left as they
are although Dog Days' files differ: the matrix in 128-byte static-shadow meshes (+0x38; Dog Days
stores a placeholder 0..15 there) and variant ids above 6 on character meshes.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_prmgraph as G

LIT = 0x01000000                                 # mesh +0x1c: has a baked light stream (Dead Men)
PROP2 = 0x10                                     # root +0x0c: prop slot 2 is set (Dead Men)
DROPPED = ('lit', 'lit5', 'scat0', 'scat1', 'scat2', 'prop2')


def _put(c, off, fmt, *v):
    return c[:off] + struct.pack(fmt, *v) + c[off + struct.calcsize(fmt):]


def _pad(b):
    return b + bytes(-len(b) % 16)


def convert_font(c):
    """Dead Men font chunk -> Dog Days font chunk (see the docstring: ASSUMPTION)."""
    h = list(struct.unpack_from('<10I', c, 0))
    n, kern = h[4], h[6]
    if h[:2] != [1, 8] or h[8] != 2 or 0x28 + 20 * n + 8 * kern > len(c):
        raise ValueError('not a Dead Men font chunk')
    h[8] = 3
    out = [struct.pack('<10I', *h)]
    for k in range(n):
        ch, tex, x0, y0, x1, y1, w, hh, dx, dy, adv, lh, flag, _pad_ = struct.unpack_from('<II4B2B2b4B', c, 0x28 + 20 * k)
        if tex >= G.SLOTS['dm']:
            tex += G.SLOTS['dd'] - G.SLOTS['dm']
        out.append(struct.pack('<II4H2H2h3HH', ch, tex, 4 * x0, 4 * y0, 4 * x1, 4 * y1, w, hh, dx, dy, adv, lh, flag, 0xcdcd))
    out.append(c[0x28 + 20 * n:0x28 + 20 * n + 8 * kern])
    return _pad(b''.join(out))


def _donor(p, kinds):
    """The smallest plain mesh object whose vertices are 40 bytes: (mesh chunk, first vertex)."""
    best = None
    for i, k in kinds.items():
        c = p.chunks[i]
        if k != 'mesh' or len(c) != 64 or c[0x0c] != 0:
            continue
        d = p.u32(p.u32(i, 0x28), 0)
        nv, vtx = p.u32(d, 0), p.u32(d, 4)
        size = len(p.chunks[vtx]) if 0 < vtx < len(p.chunks) else 0
        # 40 bytes per vertex and not also explainable as 36 or 52
        if nv >= 3 and size == (40 * nv + 15 & ~15) and size not in (36 * nv + 15 & ~15, 52 * nv + 15 & ~15):
            if best is None or (nv, i) < best[:2]:
                best = (nv, i, vtx)
    if best is None:
        raise ValueError('no plain 40-byte-vertex mesh to model an empty object on')
    return best[1], p.chunks[best[2]][:40]


def convert(dm_data, roots, strip=True):
    """Dead Men .prm -> Dog Days .prm. roots: what points into the file, as for
    kl_prmgraph.walk (chunk indices from the .gms plus (index, kind) pairs from prp_roots;
    kl_dmassets.prm_roots collects both). Unreferenced model roots of the file are converted
    too, but a font is only found through its .prp root. Returns (bytes, report); report:
    chunks, descriptors, lit (descriptors that lost baked lighting), lit_meshes (objects whose
    draw-mode bit was cleared), scatter / water (objects replaced by an empty mesh),
    scatter_roots (model roots that now draw nothing: the entities using them can be dropped),
    fonts, glyphs, prop2 (props cleared), prop2_roots, stripped (chunks cut to 16 bytes),
    added (chunks appended), unknown (unreached chunks of no recognised shape, left alone)."""
    p = G.read(dm_data, 'dm')
    roots = list(roots)
    kinds, args = G.walk(p, roots)
    orphan = G.orphans(p, kinds)
    dead = [(i, 'root') for i, lab in sorted(orphan.items()) if lab == 'dead root']
    if dead:
        kinds, args = G.walk(p, roots + dead)
    rep = dict(chunks=len(p.chunks) - 1, descriptors=0, lit=0, lit_meshes=0, scatter=0, water=0, scatter_roots=[],
               fonts=0, glyphs=0, prop2=0, prop2_roots=0, stripped=0, added=0,
               unknown=sum(1 for lab in orphan.values() if lab == 'unknown'))
    new = list(p.chunks)
    refs = list(p.refs)
    empty = {}                                   # replaced scatter / water objects
    donor = None
    for i, k in sorted(kinds.items()):
        c = p.chunks[i]
        if k == 'desc':
            if len(c) != 32:
                raise ValueError('mesh descriptor %d is %d bytes, not Dead Men\'s 32' % (i, len(c)))
            u = struct.unpack('<8I', c)
            if u[6] or u[7] or bool(u[4]) != bool(u[5]):
                raise ValueError('mesh descriptor %d: unexpected tail %r' % (i, u[4:]))
            new[i] = struct.pack('<12I', u[0], u[1], 0, 0, 0, u[2], u[3], 0, 0, 0, 0, 0)
            rep['descriptors'] += 1; rep['lit'] += bool(u[4])
        elif k == 'mesh':
            mode = p.u32(i, 0x1c)
            d = p.u32(p.u32(i, 0x28), 0)
            if bool(mode & LIT) != bool(p.u32(d, 0x10)):
                raise ValueError('mesh %d: draw-mode light bit and descriptor disagree' % i)
            if mode & LIT:
                new[i] = _put(c, 0x1c, '<I', mode & ~LIT); rep['lit_meshes'] += 1
        elif k in ('scatter', 'water'):
            if k == 'scatter' and len(c) != 256:
                raise ValueError('scatter object %d is %d bytes, not Dead Men\'s 256' % (i, len(c)))
            if donor is None:
                donor = _donor(p, kinds)
            empty[i] = struct.unpack_from('<3f', c, 0x28) if k == 'scatter' else (0.0, 0.0, 0.0)
            rep[k] += 1
        elif k == 'font':
            new[i] = convert_font(c); rep['fonts'] += 1; rep['glyphs'] += p.u32(i, 0x10)
        elif k == 'prop' and p.u32(i, 8):
            new[i] = _put(c, 8, '<I', 0); rep['prop2'] += 1
        elif k == 'root':
            flags, prop = p.u32(i, 0x0c), p.u32(i, 0x10)
            if bool(flags & PROP2) != bool(prop and p.u32(prop, 8)):
                raise ValueError('root %d: flag 0x10 and prop slot 2 disagree' % i)
            if flags & PROP2:
                new[i] = _put(c, 0x0c, '<I', flags & ~PROP2); rep['prop2_roots'] += 1
    if empty:
        # one index chunk for all (index chunks are shared in stock files too); a vertex chunk,
        # descriptor and table per object because the triangle sits at the object's own corner
        mesh, vertex = donor
        idx = len(new); new.append(_pad(struct.pack('<5H', 1, 3, 0, 1, 2))); refs.append(1)
        for i, corner in sorted(empty.items()):
            v = struct.pack('<3f', *corner) + vertex[12:]
            base = len(new)
            new += [_pad(v * 3), struct.pack('<12I', 3, base, 0, 0, 0, 0, idx, 0, 0, 0, 0, 0), struct.pack('<4I', base + 1, 0, 0, 0)]
            refs += [1, 1, 1]
            m = _put(p.chunks[mesh], 0x28, '<I', base + 2)
            m = _put(m, 0x1c, '<I', p.u32(mesh, 0x1c) & ~LIT)
            new[i] = _put(m, 0x38, '<II', 0, 0)
        for i, k in kinds.items():
            if k == 'root' and p.u32(i, 0x14) and all(o in empty for o in
                                                     struct.unpack_from('<%dI' % p.u32(i, 0x14), p.chunks[p.u32(i, 0x18)])):
                rep['scatter_roots'].append(i)
    rep['scatter_roots'].sort()
    rep['added'] = len(new) - len(p.chunks)
    out = G.Prm('dd', new, refs)
    k2, a2 = G.walk(out, roots + dead)           # raises on anything Dog Days' rules do not fit
    if strip:
        for i, k in kinds.items():
            if i not in k2:
                if k not in DROPPED:
                    raise ValueError('chunk %d (%s) lost its last reference' % (i, k))
                new[i] = bytes(16); rep['stripped'] += 1
    data = G.write(out)
    check(data, roots + dead, kinds)
    return data, rep


def check(dd_data, roots, before=None):
    """Read a converted file under Dog Days' rules and prove it holds nothing of Dead Men's:
    every root reachable, every descriptor 48 bytes with index and vertex chunk, no scatter
    object that is not 144 bytes, no water, no light bit, no prop slot 2, fonts with 32-byte
    glyphs that fit the chunk. With `before` ({chunk: kind} of the source walk) also: every
    chunk reached before is still reached, as the same kind, unless it was dropped on purpose.
    Returns the kind counts."""
    p = G.read(dd_data, 'dd')
    if G.read(dd_data).game != 'dd':
        raise ValueError('the file does not read as a Dog Days .prm')
    kinds, args = G.walk(p, roots)
    count = {}
    for i, k in kinds.items():
        c = p.chunks[i]
        count[k] = count.get(k, 0) + 1
        if k == 'desc':
            u = struct.unpack('<12I', c) if len(c) == 48 else None
            if u is None or any(u[2:5]) or any(u[7:]):
                raise ValueError('descriptor %d is not in Dog Days form' % i)
            if (not u[1] and u[0]) or (u[1] and len(p.chunks[u[1]]) < 16 * max(u[0], 1)):
                raise ValueError('descriptor %d: vertex chunk too small' % i)     # stock L05 has one with
                                                                                 # 0 vertices and no chunk
            one, n = struct.unpack_from('<HH', p.chunks[u[6]], 0)
            if one != 1 or 4 + 2 * n > len(p.chunks[u[6]]) or n % 3:
                raise ValueError('descriptor %d: index chunk is not a triangle list' % i)
            if u[0] and max(struct.unpack_from('<%dH' % n, p.chunks[u[6]], 4), default=0) >= u[0]:
                raise ValueError('descriptor %d: index past the vertex count' % i)
        elif k == 'mesh' and p.u32(i, 0x1c) & LIT:
            raise ValueError('mesh %d still has the baked-light bit' % i)
        elif k == 'scatter' and (len(c) != 144 or len(p.chunks[i + 1]) != (28 * p.u16(i, 0x5c) + 15 & ~15)):
            raise ValueError('scatter object %d is not in Dog Days form' % i)
        elif k == 'water':
            raise ValueError('water object %d: Dog Days levels have none' % i)
        elif k == 'prop' and p.u32(i, 8):
            raise ValueError('prop %d still has slot 2' % i)
        elif k == 'root' and p.u32(i, 0x0c) & PROP2:
            raise ValueError('root %d still has flag 0x10' % i)
        elif k == 'font':
            n, kern = p.u32(i, 0x10), p.u32(i, 0x18)
            if p.u32(i, 0x20) != 3 or len(c) != (0x28 + 32 * n + 8 * kern + 15 & ~15):
                raise ValueError('font %d is not in Dog Days form' % i)
    if before is not None:
        for i, k in before.items():
            if k in DROPPED:
                continue
            want = 'mesh' if k in ('scatter', 'water') else k
            if kinds.get(i) != want:
                raise ValueError('chunk %d was %s and is now %s' % (i, k, kinds.get(i)))
    return count
