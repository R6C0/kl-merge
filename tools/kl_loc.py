#!/usr/bin/env python3
"""
Kane & Lynch .LOC (text and voice-line table of a level, one member per language): tree reader,
writer, and the graft of one level's leaves into another's. Spec: re/audio.md section 5.

    python kl_loc.py test          every .LOC of both games round-trips; graft / alias on a small tree
                                   (the graft on real levels: python kl_snd.py test)
    python kl_loc.py keys <level> [prefix]

File = one table. Table: u8 n, (n - 1) x i32 offsets of children 2..n counted from the first
child, then the children. Child: name\\0, u8 flags, then a table (flag 0x10) or the leaf's data:
text\\0 + u32 if flag 0x01, then u32 sound id if flag 0x20. Flag 0x08 is set on every leaf.
- The sound id is the offset of a 'sound' object in the level's .SND (398,672 + 294,475 ids).
- The dword after the text equals the sound id in 364,280 of 364,280 Dog Days leaves that have
  both; what it is in a leaf without a sound is NOT ESTABLISHED (written 0 here).
- Children are in lower-case order in every Dead Men table and 38,176 of 38,944 Dog Days tables;
  how the engine searches a table is NOT ESTABLISHED. graft() keeps a table's own order and
  puts each new child before the first one that sorts after it (ASSUMPTION).
- A file of 9 bytes or less is a stub (Dutch in all 21 Dog Days levels): left as it is.
- Dog Days looks a key K up as K_C1 .. K_C9 (character voices) and then K (kl2 0x6b879d); Dead
  Men keys have no such variants. ASSUMPTION that the plain key is spoken; aliases() makes the
  nine variants if it is not.
"""
import collections, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

LANGS = ['English', 'German', 'French', 'Spanish', 'Italian', 'Dutch', 'Russian', 'Polish', 'Japanese']
TEXT, LEAF, TABLE, SOUND = 0x01, 0x08, 0x10, 0x20


class Node:
    __slots__ = ('name', 'flags', 'kids', 'raw')      # raw: a leaf's bytes after the flags byte

    def __init__(self, name, flags, kids=None, raw=None):
        self.name, self.flags, self.kids, self.raw = name, flags, kids, raw


def parse(d):
    """-> list of top-level Nodes, or None for a stub"""
    def table(t, bound):
        n = d[t]
        base = t + 4 * n - 3
        offs = [0] + list(struct.unpack_from('<%di' % (n - 1), d, t + 1)) if n else []
        pos, out = [base + o for o in offs], []
        for i, no in enumerate(pos):
            e = d.index(b'\0', no)
            nxt = pos[i + 1] if i + 1 < n else bound
            if d[e + 1] & TABLE:
                out.append(Node(d[no:e], d[e + 1], table(e + 2, nxt)))
            else:
                out.append(Node(d[no:e], d[e + 1], None, d[e + 2:nxt]))
        return out
    return table(0, len(d)) if len(d) > 9 else None


def build(kids):
    parts = [k.name + b'\0' + bytes([k.flags]) + (build(k.kids) if k.kids is not None else k.raw) for k in kids]
    offs, p = [], 0
    for x in parts[:-1]:
        p += len(x); offs.append(p)
    return bytes([len(kids)]) + struct.pack('<%di' % len(offs), *offs) + b''.join(parts)


def leaves(kids, path=()):
    """-> (key 'A/B/C', Node) of every leaf"""
    for k in kids:
        p = path + (k.name.decode('latin1'),)
        if k.kids is not None:
            yield from leaves(k.kids, p)
        else:
            yield '/'.join(p), k


def fields(k):
    """-> (text, dword after the text, sound id, bytes not understood) of a leaf"""
    r, text, x, sid, q = k.raw, None, None, None, 0
    if k.flags & TEXT:
        e = r.index(b'\0'); text = r[:e]; q = e + 1
        if len(r) >= q + 4:
            x = struct.unpack_from('<I', r, q)[0]; q += 4
    if k.flags & SOUND and len(r) >= q + 4:
        sid = struct.unpack_from('<I', r, q)[0]; q += 4
    return text, x, sid, len(r) - q


def leaf(name, text, sid):
    """A leaf in the form Dog Days writes: text, the dword after it (= the id), the id."""
    if sid:
        return Node(name, LEAF | TEXT | SOUND, None, (text or b'') + b'\0' + struct.pack('<II', sid, sid))
    return Node(name, LEAF | TEXT, None, (text or b'') + b'\0' + bytes(4))


def _insert(kids, node):
    key = node.name.lower()
    at = next((i for i, k in enumerate(kids) if k.name.lower() > key), len(kids))
    kids.insert(at, node)


def graft(dst, src, want, sndmap, path=()):
    """Insert every leaf of src whose key satisfies want() and that dst does not have; its sound
    id goes through sndmap ({source .SND offset: new offset}; no entry or 0 = a leaf without
    sound). dst's own nodes are not touched. -> number of leaves added."""
    added = 0
    have = {k.name.lower(): k for k in dst}
    for k in src:
        p = path + (k.name.decode('latin1'),)
        mine = have.get(k.name.lower())
        if k.kids is not None:
            if mine is None:
                mine = Node(k.name, TABLE, [])
                n = graft(mine.kids, k.kids, want, sndmap, p)
                if n:
                    _insert(dst, mine); added += n
            elif mine.kids is not None:
                added += graft(mine.kids, k.kids, want, sndmap, p)
        elif mine is None and want('/'.join(p)):
            text, _x, sid, _left = fields(k)
            _insert(dst, leaf(k.name, text, sndmap.get(sid, 0) if sid else 0))
            added += 1
    return added


def aliases(kids, keys, n=9):
    """For each key K in keys add K_C1 .. K_Cn with K's text and sound (see the docstring).
    -> number of leaves added."""
    added = 0
    def walk(tab, path):
        nonlocal added
        for k in list(tab):
            p = path + (k.name.decode('latin1'),)
            if k.kids is not None:
                walk(k.kids, p)
            elif '/'.join(p) in keys:
                have = {x.name.lower() for x in tab}
                for i in range(1, n + 1):
                    nm = k.name + b'_C%d' % i
                    if nm.lower() not in have:
                        _insert(tab, Node(nm, k.flags, None, k.raw)); added += 1
    walk(kids, ())
    return added


def members(zf):
    """-> {language: member name} of an open level archive"""
    out = {}
    for n in zf.namelist():
        if n.upper().endswith('.LOC'):
            lang = n.rsplit('_Main', 1)[1][:-4]
            out[lang] = n
    return out


def graft_level(s_files, m_files, want, sndmap, log=print):
    """s_files, m_files: {language: .LOC bytes} of the slot level and of the level the leaves
    come from. Text is taken from the same language, English where the source has none (Dead Men
    has no Russian, Polish, Japanese). -> ({language: new bytes}, leaves added per real file)."""
    out, added = {}, None
    for lang, d in s_files.items():
        t = parse(d)
        src = m_files.get(lang)
        if src is None or parse(src) is None:
            src = m_files['English']
        if t is None:                                    # stub
            out[lang] = d; continue
        n = graft(t, parse(src), want, sndmap)
        out[lang] = build(t)
        if added not in (None, n):
            log('  .LOC %s: %d leaves added, another language %d' % (lang, n, added))
        added = n
    return out, added or 0


def selftest(log=print):
    import kl_snd
    fails = 0
    for g in ('dd', 'dm'):
        tot = collections.Counter()
        for lv in kl_snd.stock_levels(g):
            with zipfile.ZipFile(kl_snd.level_zip(lv, g)) as zf:
                keys = None
                for lang, n in sorted(members(zf).items()):
                    d = zf.read(n); tot['files'] += 1
                    t = parse(d)
                    if t is None:
                        tot['stubs'] += 1; continue
                    tot['round trip identical'] += build(t) == d
                    ks = []
                    for p, k in leaves(t):
                        text, x, sid, left = fields(k)
                        ks.append((p, sid)); tot['leaves'] += 1
                        tot['leaves with bytes not understood'] += left != 0
                        tot['sound ids'] += bool(sid)
                        tot['dword after the text == sound id'] += bool(sid) and x == sid
                        tot['leaves with text and sound'] += bool(sid) and x is not None
                    tot['same keys and ids as the level\'s other languages'] += keys in (None, ks)
                    keys = ks
        fails += tot['files'] - tot['stubs'] != tot['round trip identical']
        log('%s .LOC: %s' % (g, dict(tot)))
    # graft and aliases on a small tree: order kept, own leaves untouched, ids through the map
    dst = [Node(b'Zeta', TABLE, [leaf(b'b', b'own', 0x40)]), Node(b'alpha', TABLE, [leaf(b'x', b'own', 0)])]
    src = [Node(b'Multi', TABLE, [leaf(b'K', b'hello', 0x100), leaf(b'L', b'mute', 0x200), leaf(b'no', b'', 0)]),
           Node(b'zeta', TABLE, [leaf(b'a', b'new', 0x300), leaf(b'B', b'other', 0x300)])]
    n = graft(dst, src, lambda p: not p.endswith('no'), {0x100: 0x9000, 0x300: 0x9100})
    n2 = aliases(dst, {'Multi/K'})
    got = [(p, fields(k)[0], fields(k)[2]) for p, k in leaves(parse(build(dst)))]
    want = [('Multi/K', b'hello', 0x9000)] + [('Multi/K_C%d' % i, b'hello', 0x9000) for i in range(1, 10)] +            [('Multi/L', b'mute', None), ('Zeta/a', b'new', 0x9100), ('Zeta/b', b'own', 0x40), ('alpha/x', b'own', None)]
    ok = (n, n2) == (3, 9) and got == want
    log('graft / aliases on a small tree: %s' % ('as expected' if ok else 'WRONG: %s' % got))
    return fails + (not ok)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['test']:
        sys.exit(1 if selftest() else 0)
    elif a[:1] == ['keys'] and len(a) >= 2:
        import kl_snd
        with zipfile.ZipFile(kl_snd.level_zip(a[1])) as zf:
            for p, k in leaves(parse(zf.read(members(zf)['English']))):
                if p.startswith(a[2] if len(a) > 2 else ''):
                    text, x, sid, left = fields(k)
                    print('%-70s %#8x %s' % (p, sid or 0, (text or b'').decode('latin1')[:60]))
    else:
        print(__doc__)
