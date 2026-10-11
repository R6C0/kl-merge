"""
A Dead Men cloth blob in a Dog Days .prm can be 4, 8 or 12 bytes too short: Dog Days writes past its end.

    python tools/kl_fa_vaultfx.py check <build folder | level .zip> [...]     FAIL per blob that is too short
    python tools/kl_fa_vaultfx.py apply <build folder> <new folder>          the blobs padded; only the .prm differs
    python tools/kl_fa_vaultfx.py tree <KLExpansion tree> [...]              THE GATE: every Maps/<id>/*_Main.zip of a tree
    python tools/kl_fa_vaultfx.py stock                                      the rule against every stock Dog Days level

THE FAULT (owner's crash in The Vault, 2026-10-11 19:43:12, kl2 0x466597; re/crash_vault.md)
A cloth (ZCloth, ZPlant, ZTie) keeps its simulation in a .prm chunk, the 'cloth blob' (ZCloth[15]; many entities
share one). kl2 0x87df60 lays it out:
    +0x08 h, +0x0c n particles, +0x10 a constraints, +0x14 c, +0x18 b triangles
    +0x1c + 8 h      n x 12   rest places            (object +0x9c)
                     n x 4    weights                (+0xa8)
                     a x 16   constraints            (+0x90)
                     c x 2, b x 6
    x += x & 3       S x 0x2c simulation slots       (+0xa0; S = the OBJECT's slot count, ZCloth[0]: object +0x48)
    base = x rounded UP TO 16                        <- Dog Days only (0x87e041 .. 0x87e04f)
    slot k: [slot + 0] = base + its stored offset (k x 24 n); 24 n bytes of scratch each: two arrays of n places
Dead Men's twin (kaneandlynch 0x58ad70, 0x58aeac .. 0x58aeaf) takes base = x, NOT rounded, and its build tool sized
the chunk for that. So a Dead Men blob whose slot table does not end on a multiple of 16 is 16 - (x % 16) bytes
short of what Dog Days addresses, less the chunk's own padding: the scratch of the last slot ends 4, 8 or 12 bytes
INSIDE THE NEXT CHUNK. kl2 0x72a920 (a cloth takes a slot) fills both arrays with the n places: for h == 1 (object
+0x84; every blob of the bank) by its first branch, 0x72a941 - slot 8 of the object at [[obj+0x40]] called twice with
(0, n, dest) and (0, n, dest + 12 n) -, else by the float loop at 0x72a9b0 from the rest places. Either way the bytes
written past the end are the end of the last particle's place - over the first bytes of whatever chunk follows (the
dump holds exactly particle 192's rest y and z there).
WHEN (read in kl2, not seen live): only ZRenderEntryDeformerD3D's draw (slot 2, 0x7bf760) reaches it - it calls the
cloth's slot 120 (0x59c9a0), that calls slot 119 (0x8ac1d0), which takes a free slot (or the farthest cloth's) when
the game is not paused ([0xdd2640]+0x50 > 0) and the cloth's measure [obj+0x44] is unset (1e38: the entry's slot 9
0x5ee9d0 resets it, its slot 1 0x789f30 keeps the smallest of a frame) or below [obj+0x4c] (= ZCloth[1], 2000 on
the pots); with a measure at or over the limit the slot is given back. So the write follows a pot being DRAWN.
THE RULE IS OFFSET ARITHMETIC; the exe rounds the ABSOLUTE address. The two agree only while the .prm buffer starts
on a multiple of 16 (the game's own block and the hook's reserve both do: 0x04180010 in the owner's process).
In The Vault the chunk after the plant pots' blob (63165, 'SO0501_M03_Plantpot_01') is the SPRITE of the vault
fire's particle template 'Vault_Fire' (63166). Its header 00 00 02 00 | texture became two floats (9.30, -8.43 =
y and z of particle 192: the very dwords in the dump). The sprite factory (0x6bb690: word +2 == 2) then refuses the
chunk, a ZRenderEntryGeomD3D (0x1c8 bytes) is made instead of a ZRenderEntrySpriteD3D (0x1ec), and DrawChunk
(0x842d00 -> 0x926db0) uses +0x1dc .. +0x1e8 of it = the heap behind it: it frees a float as a pointer.

THE FIX: the chunk is made as long as Dog Days needs (zero bytes at its end, a multiple of 16). Nothing else moves:
every reference in a .prm is a chunk index (kl_prmgraph), the table is written again. fix_prm() is the same for a
build tool (kl_graft / kl_fa_bank after the Dead Men chunks are in the Dog Days .prm).

NOT RUN IN THE GAME. ASSUMED: ZCloth[0] is the slot count at object +0x48 (it equals the number of 0x2c records
with the tool's 0xcd fill in every blob looked at: check() tests that per blob and fails a blob where it is not so).

THE OTHER SIMULATION CHUNK, ZPlant[2] ('plant'): a count dword and 16-byte records {u16 a, b, c, ?; float; float},
read the same way by both games (kl2 slot 122 0x7ab5c0 / slot 82 0x7cfa20, kaneandlynch 0x58e120 / 0x58df40: same
stride, same fields, the float at +0xc written in place). check() fails one whose records do not fit or whose
indices pass the blob's particle count; all 10 stock ones and the bank's 3 are 4 + 16 count rounded up to 16.

THE GATE for a tree build (kl_expansion.py is not this tool's file): `tree <KLExpansion>` exits 1 when any map's
archive fails; gate(tree) -> the problem lines, for a build to refuse the tree on.
"""
import collections
import glob
import os
import shutil
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NAME = 'vaultfx'
SLOT = 0x2c                 # bytes of one simulation slot (kl2 0x87e02f imul 0x2c; 0x8ac2fe)
PLACE = 12                  # a particle's place; a slot's scratch is two arrays of them (kl2 0x72a920)


def layout(c, slots):
    """The blob `c` as kl2 0x87df60 lays it out for an object with `slots` simulation slots ->
    dict(n, places, table, base, offsets, end, form). end = the first byte Dog Days does NOT address;
    form = [] or why the blob is not the known shape (then end is not to be trusted)."""
    form, note = [], []
    if len(c) < 0x1c:
        return dict(n=0, places=0, table=0, base=0, offsets=[], end=0, form=['shorter than its header'], note=note)
    h, n, a, cc, b = struct.unpack_from('<5I', c, 8)
    places = 0x1c + 8 * h
    x = places + PLACE * n + 4 * n + 16 * a + 2 * cc + 6 * b
    x += x & 3                                          # as the exe does it (0x87e032 .. 0x87e037), not a round-up
    table = x
    base = (table + SLOT * slots + 15) & ~15
    if c[0] != 0:
        form.append('byte 0 is %d, not 0: the game would take the slots\' offsets as already fixed up' % c[0])
    if table + SLOT * slots > len(c):
        form.append('the slot table (%d x 0x2c at %#x) does not fit the chunk' % (slots, table))
        return dict(n=n, places=places, table=table, base=base, offsets=[], end=base + 2 * PLACE * n * slots, form=form, note=note)
    offsets = [struct.unpack_from('<I', c, table + SLOT * k)[0] for k in range(slots)]
    # Dead Men's tool stores k x 24 n, Dog Days' k x (24 n rounded up to 16): any even step that holds a slot is the shape
    step = offsets[1] if slots > 1 else 2 * PLACE * n
    if offsets != [step * k for k in range(slots)] or not 2 * PLACE * n <= step < 2 * PLACE * n + 16:
        form.append('the slots\' offsets are %s, not k x %d (or that rounded up to 16)' % (offsets[:4], 2 * PLACE * n))
    elif slots > 1 and step % 16:
        # stock Dog Days stores steps rounded up to 16 (every slot's scratch 16-aligned); Dead Men's tool stores 24 n.
        # The padding below makes such a blob long enough, but slots 1.. then start off a multiple of 16: whether
        # anything in Dog Days needs them aligned was NOT read. None of the builds of 2026-10-11 has one.
        note.append('%d slots %d bytes apart, not a multiple of 16 as in every stock blob: slots 1.. are not 16-aligned '
                    '(long enough once padded; whether Dog Days needs the alignment is not known)' % (slots, step))
    filled = 0
    while c[table + SLOT * filled + 12:table + SLOT * (filled + 1)] == b'\xcd' * 32:
        filled += 1
    if filled != slots:
        form.append('%d slot records carry the build tool\'s fill, the objects say %d slots (ZCloth[0])' % (filled, slots))
    return dict(n=n, places=places, table=table, base=base, offsets=offsets,
                end=base + (max(offsets) if offsets else 0) + 2 * PLACE * n, form=form, note=note)


class Level:
    """A build folder or a level archive, read as far as the check needs."""

    def __init__(self, src):
        import kl_gms, kl_rtp, kl_prmgraph as G, kl_prpjoin as J
        from kl_prp import Prp
        if os.path.isdir(src):
            z = sorted(f for f in os.listdir(src) if f.lower().endswith('_main.zip'))
            if len(z) != 1:
                raise ValueError('%s: expected one *_Main.zip' % src)
            self.folder, self.zip = src, os.path.join(src, z[0])
        else:
            self.folder, self.zip = None, src
        with zipfile.ZipFile(self.zip) as zf:
            self.order = zf.namelist()
            self.files = {m: zf.read(m) for m in self.order if m.rsplit('.', 1)[-1].lower() in ('gms', 'buf', 'prp', 'prm')}
        self.ext = {m.rsplit('.', 1)[-1].lower(): m for m in self.files}
        self.raw = kl_gms.unpack(self.files[self.ext['gms']])
        names, tids, buf = ['ROOT'], [kl_rtp.ROOT_TYPE], self.files[self.ext['buf']]
        for decl, tid, _prio in kl_gms.entities(self.raw):
            o = struct.unpack_from('<I', self.raw, 4 * (decl & 0xffffff))[0]
            names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
        self.sc = J.Scene(Prp(self.files[self.ext['prp']]), names, tids, 'dd', os.path.basename(self.zip))
        self.prm = G.read(self.files[self.ext['prm']], 'dd')
        self.roots = G.prp_roots(self.sc.p, self.sc.tids, J.schema('dd'), 'dd')
        self.gms = G.gms_roots(self.raw)
        self._kinds = None

    def wardrobe_roots(self):
        # beside the archive: a build folder and a tree's Maps\<id> both keep the side file there
        p = os.path.join(self.folder or os.path.dirname(os.path.abspath(self.zip)), 'KLWardrobe.ini')
        if not os.path.isfile(p):
            return []
        with open(p) as fh:
            return [int(l.split('=')[1]) for l in fh if l.startswith('Root=')]

    def cloths(self):
        """{cloth chunk: [node]} from ZCloth[15] of every node."""
        out = collections.defaultdict(list)
        for where, ch, kind in self.roots:
            if kind == 'cloth' and isinstance(where[0], int):
                out[ch].append(where[0])
        return out

    def plants(self):
        """[(plant chunk, node)] from ZPlant[2] of every node."""
        return sorted({(ch, where[0]) for where, ch, kind in self.roots if kind == 'plant' and isinstance(where[0], int)})

    def cloth_of(self, node):
        import kl_fa, kl_prpjoin as J
        return int(dict(zip(J.labels('dd', self.sc.cls(node)), kl_fa.node_values(self.sc, node)))['ZCloth[15]'])

    def slots(self, node):
        """ZCloth[0] of a node: the object's simulation slot count (object +0x48; the exe makes 0 a 1)."""
        import kl_fa, kl_prpjoin as J
        v = dict(zip(J.labels('dd', self.sc.cls(node)), kl_fa.node_values(self.sc, node)))
        return max(1, int(v['ZCloth[0]']))

    def kinds(self):
        if self._kinds is None:
            import kl_prmgraph as G
            self._kinds = G.walk(self.prm, G.level_roots(self.sc.p, self.sc.tids, self.raw, self.wardrobe_roots()))[0]
        return self._kinds

    def named_by(self, chunk):
        """Scene paths of the nodes that name a chunk (.gms record or a .prp field)."""
        out = [self.sc.path[k + 1] for k, m in enumerate(self.gms) if m == chunk]
        out += [self.sc.path[w[0]] for w, ch, _k in self.roots if ch == chunk and isinstance(w[0], int) and self.sc.path[w[0]] not in out]
        return out

    def emitters_of(self, template_path):
        """ZParticleEmitter nodes with a reference to the template (a string value that ends with its path's tail)."""
        import kl_fa
        tail = template_path.split('\\')[-1].lower()

        def names(x):                                   # the value's last name is the template's (by NAME: a guide, not a proof)
            x = x.lower()
            return x.endswith(tail) and not (x[:-len(tail)][-1:].isalnum() or x[:-len(tail)][-1:] == '_')
        out = []
        for k in range(1, len(self.sc.nodes)):
            if self.sc.cls(k) == 'ZParticleEmitter' and any(isinstance(x, str) and names(x) for x in kl_fa.node_values(self.sc, k)):
                out.append(self.sc.path[k])
        return out


def findings(L):
    """One dict per cloth blob of the level: chunk, size, users, slots, the layout, over (bytes past the end), and
    for over > 0 what is hit."""
    out = []
    for ch, nodes in sorted(L.cloths().items()):
        c = L.prm.chunks[ch]
        counts = sorted({L.slots(k) for k in nodes})
        lay = layout(c, counts[-1])
        f = dict(chunk=ch, size=len(c), users=len(nodes), user=L.sc.path[nodes[0]], slots=counts, over=max(0, lay['end'] - len(c)), **lay)
        if len(counts) > 1:
            f['form'] = f['form'] + ['its users disagree on the slot count: %s' % counts]
        if f['over']:
            n, p = lay['n'], lay['places']
            f['written'] = c[p + PLACE * n - f['over']:p + PLACE * n]            # the end of the last particle's rest place
            nx = ch + 1
            f['next'] = nx
            if nx < len(L.prm.chunks):
                f['next_kind'] = L.kinds().get(nx, 'no live root reaches it')
                f['next_head'] = L.prm.chunks[nx][:f['over']]
                f['next_named'] = L.named_by(nx)
                f['next_emitters'] = [e for t in f['next_named'] if f['next_kind'] == 'sprite' for e in L.emitters_of(t)]
            else:
                f['next_kind'] = 'past the file: the first chunk the game makes while it runs (kl2 0x509970)'
        out.append(f)
    return out


def plant_faults(L):
    """(number of plant chunks, problem lines): ZPlant[2] is a count dword + 16-byte records whose first three words
    are particle indices of the node's cloth blob (kl2 0x7ab5c0, 0x7cfa20; the same in Dead Men)."""
    seen, bad = set(), []
    for ch, node in L.plants():
        c, blob = L.prm.chunks[ch], L.prm.chunks[L.cloth_of(node)]
        n = struct.unpack_from('<I', blob, 0xc)[0] if len(blob) >= 0x10 else 0
        if (ch, n) in seen:
            continue
        seen.add((ch, n))
        cnt = struct.unpack_from('<I', c, 0)[0] if len(c) >= 4 else 0
        if len(c) < 4 or 4 + 16 * cnt > len(c):
            bad.append('plant chunk %d (%s): %d records of 16 bytes do not fit its %d bytes' % (ch, L.sc.path[node].split('\\')[-1], cnt, len(c)))
            continue
        mx = max((max(struct.unpack_from('<3H', c, 4 + 16 * k)) for k in range(cnt)), default=-1)
        if mx >= n:
            bad.append('plant chunk %d (%s): particle index %d, its cloth blob has %d' % (ch, L.sc.path[node].split('\\')[-1], mx, n))
    return len({ch for ch, _n in seen}), bad


def check(src, log=print, L=None):
    """-> (problem lines, findings). A problem per blob Dog Days writes past, per blob of an unknown shape and per
    plant chunk that does not hold its records; a NOTE (no problem) per blob whose slots are not 16-aligned."""
    L = L or Level(src)
    fs, bad, notes = findings(L), [], 0
    log('%s: %d cloth blob(s), %d chunk-table entries' % (L.zip, len(fs), len(L.prm.chunks)))
    for f in fs:
        log('  blob %d: %d bytes, %d particles, %d slot(s), %d user(s) (%s); Dog Days\' scratch ends at %#x of %#x%s' % (
            f['chunk'], f['size'], f['n'], f['slots'][-1], f['users'], f['user'].split('\\')[-1], f['end'], f['size'],
            ': FITS' if not f['over'] else ': %d BYTES PAST THE END' % f['over']))
        for w in f['form']:
            bad.append('cloth blob %d is not the known shape: %s' % (f['chunk'], w))
            log('    FAIL ' + bad[-1])
        for w in f['note']:
            notes += 1
            log('    NOTE cloth blob %d: %s' % (f['chunk'], w))
        if f['over']:
            s = 'cloth blob %d (%s, %d users) is %d bytes short for Dog Days: a cloth that takes a slot writes %s over the first %d bytes of chunk %d (%s%s)' % (
                f['chunk'], f['user'].split('\\')[-1], f['users'], f['over'], f['written'].hex(' ', 4), f['over'], f['next'], f['next_kind'],
                ', now %s' % f['next_head'].hex(' ', 4) if 'next_head' in f else '')
            bad.append(s)
            log('    FAIL ' + s)
            for t in f.get('next_named', []):
                log('      chunk %d is named by %s' % (f['next'], t))
            for e in f.get('next_emitters', []):
                log('        emitter %s' % e)
            if f['next_kind'] == 'sprite':
                log('      a sprite without its header is refused by the sprite factory (kl2 0x6bb690): the next render entry made for it is a '
                    'ZRenderEntryGeomD3D, and DrawChunk (0x842d00 / 0x926db0) reads +0x1dc of it = the heap behind it')
    np, pbad = plant_faults(L)
    log('  %d plant chunk(s) (ZPlant[2]): %s' % (np, 'records fit, indices inside their blob' if not pbad else '%d FAULTY' % len(pbad)))
    for s in pbad:
        bad.append(s)
        log('    FAIL ' + s)
    log('check (%s): %s%s' % (NAME, 'PASS' if not bad else 'FAIL (%d)' % len(bad), ', %d NOTE' % notes if notes else ''))
    return bad, fs


def gate(tree, log=print):
    """THE GATE for a tree build: every Maps\\<id>\\*_Main.zip of a KLExpansion tree (or of a folder that holds one)
    through check(). -> ['<id>: <problem>']; an empty list = the tree may go out. A tree without maps is a problem."""
    root = tree if os.path.isdir(os.path.join(tree, 'Maps')) else os.path.join(tree, 'KLExpansion')
    maps = sorted(glob.glob(os.path.join(glob.escape(os.path.join(root, 'Maps')), '*', '*_Main.zip')))
    if not maps:
        return ['%s: no Maps\\<id>\\*_Main.zip found' % tree]
    out = []
    for zp in maps:
        mid = os.path.basename(os.path.dirname(zp))
        out += ['%s: %s' % (mid, s) for s in check(zp, log)[0]]
    log('gate (%s) %s: %d map(s), %s' % (NAME, root, len(maps), 'PASS' if not out else 'FAIL (%d)' % len(out)))
    return out


def fix_prm(prm, slots_of):
    """Every cloth blob of the kl_prmgraph.Prm made as long as Dog Days addresses. slots_of: {cloth chunk: slot count
    (the largest ZCloth[0] of its users)}. -> {chunk: (old size, new size)}. A blob of an unknown shape raises."""
    done = {}
    for ch, slots in sorted(slots_of.items()):
        c = prm.chunks[ch]
        lay = layout(c, slots)
        if lay['form']:
            raise ValueError('cloth blob %d is not the known shape (%s): not padded' % (ch, '; '.join(lay['form'])))
        if lay['end'] > len(c):
            new = (lay['end'] + 15) & ~15
            prm.chunks[ch] = c + bytes(new - len(c))
            done[ch] = (len(c), new)
    return done


def cloth_slots(sc, roots=None):
    """{cloth chunk: the largest ZCloth[0] of the nodes that name it} of a Dog Days kl_prpjoin.Scene."""
    import kl_fa, kl_prmgraph as G, kl_prpjoin as J
    out = {}
    for where, ch, kind in (roots if roots is not None else G.prp_roots(sc.p, sc.tids, J.schema('dd'), 'dd')):
        if kind == 'cloth' and isinstance(where[0], int):
            v = dict(zip(J.labels('dd', sc.cls(where[0])), kl_fa.node_values(sc, where[0])))
            out[ch] = max(out.get(ch, 1), int(v['ZCloth[0]']))
    return out


def fix_level(prm, sc):
    """FOR A BUILD TOOL: once the Dead Men chunks are in the Dog Days .prm and the .prp names them (ZCloth[15]),
    pad every short cloth blob in place. prm: kl_prmgraph.Prm, sc: kl_prpjoin.Scene of the finished level.
    -> {chunk: (old size, new size)}."""
    return fix_prm(prm, cloth_slots(sc))


def apply(src, dst, log=print):
    """The build of folder `src` written to the NEW folder `dst` with the short cloth blobs padded. Raises before
    anything is written when there is nothing to do or a proof fails."""
    import kl_graft, kl_prmgraph as G
    L = Level(src)
    if not L.folder:
        raise ValueError('apply wants a build folder')
    dst = os.path.abspath(dst)
    if dst == os.path.abspath(L.folder):
        raise ValueError('the out folder is the build itself')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: a build folder is never written into' % dst)
    lines = []

    def say(s=''):
        log(s)
        lines.append(s)
    say('kl_fa_vaultfx apply: %s -> %s' % (L.zip, dst))
    before, fs = check(src, say, L)
    if not any(f['over'] for f in fs):
        raise ValueError('nothing to pad: no cloth blob of %s is short' % src)
    old = list(L.prm.chunks)
    done = fix_prm(L.prm, {f['chunk']: f['slots'][-1] for f in fs})
    data = G.write(L.prm)
    # proofs on the bytes that will be written
    q = G.read(data, 'dd')
    if len(q.chunks) != len(old):
        raise ValueError('the chunk count changed')
    for i in range(1, len(old)):
        if i in done:
            if q.chunks[i][:len(old[i])] != old[i] or any(q.chunks[i][len(old[i]):]) or len(q.chunks[i]) != done[i][1]:
                raise ValueError('cloth blob %d is not its old bytes + zeros' % i)
        elif q.chunks[i] != old[i]:
            raise ValueError('chunk %d changed' % i)
    if len(data) - len(L.files[L.ext['prm']]) != sum(b - a for a, b in done.values()):
        raise ValueError('the .prm did not grow by exactly the padding')
    with zipfile.ZipFile(L.zip) as zf:
        members = [(m, data if m == L.ext['prm'] else zf.read(m)) for m in L.order]
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(L.zip)), members)
    skip = (NAME + '.txt',)
    for x in os.listdir(L.folder):
        p = os.path.join(L.folder, x)
        if os.path.isfile(p) and p != L.zip and x not in skip:
            shutil.copyfile(p, os.path.join(dst, x))
    with zipfile.ZipFile(L.zip) as za, zipfile.ZipFile(out) as zb:
        ia, ib = za.infolist(), zb.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('the member list changed')
        diff = [i.filename for i, j in zip(ia, ib) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != [L.ext['prm']]:
        raise ValueError('not exactly the .prm differs from the build: %s' % diff)
    for ch, (a, b) in sorted(done.items()):
        say('  blob %d: %d -> %d bytes (+%d zero bytes)' % (ch, a, b, b - a))
    # THE FOLDER'S SIZE RECORD. kl_fa_bots_dyn check fails a folder whose .prm is not the size its dyn.json wrote down
    # ('a large block changed its size': the guard against a later step that grows a block unnoticed). This step grows
    # the .prm on purpose, by the padding and nothing else (proved above), so the COPY of dyn.json in the new folder
    # gets the new size where it held the old one, and says so under its own key.
    dj, a, b = os.path.join(dst, 'dyn.json'), len(L.files[L.ext['prm']]), len(data)
    if os.path.isfile(dj):
        import json
        d, n = json.load(open(dj)), 0
        for key in ('big_before', 'big_after'):
            if isinstance(d.get(key), dict) and d[key].get('.prm') == a:
                d[key]['.prm'] = b; n += 1
        if n:
            d[NAME] = {'.prm': [a, b], 'padded': {str(ch): list(v) for ch, v in sorted(done.items())},
                       'note': 'kl_fa_vaultfx apply grew the .prm by the cloth blobs\' padding and moved big_before / big_after with it'}
            with open(dj, 'w') as fh:
                json.dump(d, fh, indent=1)
            say('  dyn.json (the copy): the recorded .prm size %d -> %d in %d place(s), noted under \'%s\' - without it '
                'kl_fa_bots_dyn check reads the %d bytes as \'a large block changed its size\'' % (a, b, n, NAME, b - a))
    say('  only %s differs from the build (%d members; %d -> %d bytes; %d of its %d chunks longer, every other chunk equal); '
        '%d files beside the archive copied' % (L.ext['prm'], len(L.order), len(L.files[L.ext['prm']]), len(data), len(done), len(old) - 1,
                                               len(os.listdir(dst)) - 1))
    say('')
    after, _fs = check(dst, say)
    if after:
        raise ValueError('the written build still fails the check')
    say('NOT RUN IN THE GAME.')
    with open(os.path.join(dst, NAME + '.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return dict(src=L.zip, out=out, padded=done, before=before)


def stock(log=print):
    """The rule against every stock Dog Days level: no blob may be short, and the blobs where Dead Men's layout
    (base not rounded) would have made a SHORTER chunk are counted - they are what shows the rounding in the data."""
    from kl_port_check import find, DD_GUESSES, DD_EXE
    dd = find(DD_GUESSES, DD_EXE)
    tot = short = odd = tell = exact = 0
    for zp in sorted(glob.glob(os.path.join(glob.escape(dd), 'Scenes', 'Locations', '*', '*_Main.zip'))):
        try:
            L = Level(zp)
        except Exception as e:                           # a slot that holds one of our builds is still a Dog Days level
            log('%s: not read (%s)' % (zp, e)); continue
        n = s = 0
        for f in findings(L):
            n += 1; tot += 1
            s += bool(f['over']); short += bool(f['over']); odd += bool(f['form'])
            dm_end = f['table'] + SLOT * f['slots'][-1] + (f['end'] - f['base'])       # Dead Men: base = the table's end
            tell += ((dm_end + 15) & ~15) < f['size']
            exact += ((f['end'] + 15) & ~15) == f['size']
        log('%-14s %3d cloth blobs, %d short' % (os.path.basename(zp), n, s))
    log('stock Dog Days: %d cloth blobs; short for Dog Days\' layout: %d; not the known shape: %d; exactly as long as the layout '
        'asks (to 16): %d; longer than Dead Men\'s layout would need: %d' % (tot, short, odd, exact, tell))
    return short + odd


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'check':
        bad = 0
        for src in a[1:]:
            bad += len(check(src)[0])
        return 1 if bad else 0
    if len(a) >= 2 and a[0] == 'tree':
        bad = 0
        for t in a[1:]:
            bad += len(gate(t))
        return 1 if bad else 0
    if len(a) == 3 and a[0] == 'apply':
        apply(a[1], a[2])
        return 0
    if a == ['stock']:
        return 1 if stock() else 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
