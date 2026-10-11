"""Graft a Dog Days entity subtree (with its PRP nodes, GUI sprite prims and textures) into a ported level.
The grafted subtree hangs under a wrapper placed so that no existing node index moves (ANP_GRAFT_HOST=tail, the
default: under a new ANP_Tail group at the very end of the node table, see _graft_tail; ANP_GRAFT_HOST=old: under the
last group entity's nearest plain-ZGROUP ancestor, which in Dead Men levels is a ZAllocMany pool group).  Used for
Dog Days menu resources (Menu_genericresources), which register themselves through their ZAddResourcesFrontend
event, so their location in the tree is free."""
import struct, collections, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from prp import PRP
from gms import GMS
from clusters import read_ents, compute_blocks, basetype_guess

def node_spans(ops, k):
    """preorder list of (start, end) op-index spans, one per node (props..children), starting at op k"""
    spans = []
    def skip_obj(j):
        d = 0
        while True:
            b = ops[j][1] & 0x7f
            if b == 2: d += 1
            elif b == 0x7e:
                d -= 1
                if d == 0: return j + 1
            j += 1
    def node(j):
        me = len(spans); spans.append(None); s = j
        j = skip_obj(j)
        assert ops[j][1] & 0x7f == 4; nev = ops[j][2]; j += 1
        for e in range(nev):
            j += 1; j = skip_obj(j)
        assert ops[j][1] & 0x7f == 4; nch = ops[j][2]; j += 1
        for c in range(nch): j = node(j)
        spans[me] = (s, j)
        return j
    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))
    end = node(k)
    return spans, end

class Donor:
    def __init__(s, base, prm_bytes, tex_path):
        s.P = PRP(open(base + '.prp', 'rb').read()); s.ops = list(s.P.instrs())
        s.G = GMS(base + '.gms', base + '.buf'); s.G.depth_tree()
        s.k = next(i for i, (p, op, v) in enumerate(s.ops) if op & 0x7f == 2)
        s.spans, _ = node_spans(s.ops, s.k)
        s.prm = prm_bytes
        off, cnt, _, _ = struct.unpack_from('<4I', prm_bytes)
        s.pdesc = [struct.unpack_from('<4I', prm_bytes, off + i * 16) for i in range(cnt)]
        s.tex_path = tex_path
        with open(tex_path, 'rb') as f: hdr = f.read(0xc020)
        s.t0 = struct.unpack_from('<4096I', hdr, 0x20); s.t1 = struct.unpack_from('<4096I', hdr, 0x4020)
    def chunk(s, i):
        o, sz, _, _ = s.pdesc[i]; return s.prm[o:o + sz]
    def tex_entry(s, slot):
        with open(s.tex_path, 'rb') as f:
            f.seek(s.t0[slot]); fs = struct.unpack('<I', f.read(4))[0]; f.seek(s.t0[slot])
            return f.read(fs) + b'\0' * ((-fs) & 15)

def is_sprite(c):
    if len(c) < 64: return 0
    n = struct.unpack_from('<I', c)[0]
    if not 1 <= n <= 64 or len(c) != (56 * n + 8 + 15) // 16 * 16: return 0
    if struct.unpack_from('<I', c, 4 * (10 * n + 1))[0] != n: return 0
    return n

FONT_TYPES = (0x20003a, 0x20004c)        # ZTTFONT, ZKerningFont
OSD_TYPE = 0x200483                      # ZOnScreenDisplay2
TEX_BIAS = 4096                          # Dog Days .TEX table size = text-glyph texture key bias

def is_font(c):
    """Dog Days font chunk: +0x10 glyph count, +0x18 kerning pair count, glyphs (32 bytes) from +0x28, then the
    kerning pairs (8 bytes). Format from JC's kl-merge (tools/kl_prmgraph.py, 'font'; Dead Men glyphs are 20 bytes)."""
    if len(c) < 48: return 0
    n, kk = struct.unpack_from('<I', c, 0x10)[0], struct.unpack_from('<I', c, 0x18)[0]
    if not 1 <= n <= 0x10000 or kk > 0x10000 or len(c) != (40 + 32 * n + 8 * kk + 15) // 16 * 16: return 0
    return n

def _strip_events(ops, drop):
    """ops = one node (props, events, children) as a flat op list; returns (new ops, events removed) with every event
    whose name is in drop taken out of every node (event counts fixed)."""
    out = []; nrem = [0]
    def node(j):
        e = _obj_end(ops, j); out.extend(ops[j:e]); j = e
        assert ops[j][1] & 0x7f == 4; nev = ops[j][2]; ci = len(out); out.append(list(ops[j])); j += 1; kept = 0
        for _ in range(nev):
            e = _obj_end(ops, j + 1)
            if ops[j][2] in drop: nrem[0] += 1
            else: out.extend(ops[j:e]); kept += 1
            j = e
        out[ci][2] = kept
        assert ops[j][1] & 0x7f == 4; nch = ops[j][2]; out.append(ops[j]); j += 1
        for _ in range(nch): j = node(j)
        return j
    end = node(0); assert end == len(ops), (end, len(ops))
    return out, nrem[0]

def _obj_end(ops, j):
    d = 0
    while True:
        b = ops[j][1] & 0x7f
        if b == 2: d += 1
        elif b == 0x7e:
            d -= 1
            if d == 0: return j + 1
        j += 1

def _reset_transform(ops):
    """first [9] array (stored 3x3) -> identity [0,0,1,0,1,0,1,0,0], next [3] array (position) -> origin"""
    want = {9: [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0], 3: [0.0, 0.0, 0.0]}; j = 0
    while want and j < len(ops):
        if ops[j][1] & 0x7f == 1 and ops[j][2] in want:
            vals = want.pop(ops[j][2])
            for q, v in enumerate(vals): ops[j + 1 + q][2] = v
            j += 1 + len(vals); continue
        j += 1

def graft(donor, subtree_name, wrapper_name, out, g, buf, prm_cnt, tex_used, rep, path_prefix_old=None, patch=None,
          squads=None, strip_events=(), font_hook=None, osd_hook=None):
    """subtree names: 'Name', 'Name@entindex' (pick one of several same-named donor entities) and/or
    'Name=NewName' (rename the grafted root; lets one donor subtree be grafted several times).
    patch(k, newname, ops): called with each root's copied PRP ops (props..children) before splicing.
    squads: {NewName: (squad name, donor squad name)} puts that root inside a new squad group: a copy of the donor
    squad's group (transform reset to identity at the origin) with only its ZSquadScript event. Every Dog Days
    MiniCutscene sits directly under a squad (ZMercSquad / ZSquadScript / ZFusionSquad: 2339 of 2339 in L00-L11,
    F01-F09); one without a squad parent does not run.
    strip_events: event names removed from every grafted node (e.g. 'PostFilter': its chunk is a post-filter set
    whose values index the DONOR scene's PostFilterPalettes blob, so it cannot be carried to another level).
    font_hook(font entity name, Dog Days font chunk with this level's .TEX keys) -> chunk bytes or None: a returned
    chunk is appended to the .prm and the grafted font entity's chunk int points at it (ANP_DM_FONTS: Dead Men
    typefaces under the Dog Days font names; the Dog Days chunks and their pages stay, for glyphs Dead Men lacks).
    osd_hook(tables, new_tex, extra): edits the grafted OSD texture tables after their ids are remapped (see there).
    Followed chunk references: ZWINPIC sprites (-> sprite bindings -> .TEX), ZTTFONT/ZKerningFont font chunks
    (glyph .TEX keys) and ZOnScreenDisplay2's 200 .TEX ids."""
    D = donor; G = D.G
    specs = [subtree_name] if isinstance(subtree_name, str) else list(subtree_name)
    names = []; pick = []; renames = []
    for sp in specs:
        nn = None
        if '=' in sp: sp, nn = sp.split('=', 1)
        ix = None
        if '@' in sp: sp, ix = sp.rsplit('@', 1); ix = int(ix)
        names.append(sp); pick.append(ix); renames.append(nn or sp)
    kids = collections.defaultdict(list)
    for e in G.ents: kids[e['parent']].append(e['i'])
    byi = {x['i']: x for x in G.ents}
    def path_of(i):
        p = []; e = byi.get(i)
        while e: p.append(e['name']); e = byi.get(e['parent'])
        return 'ROOT\\' + ''.join(x + '\\' for x in reversed(p))
    roots = []; sub = []; rel = {}; sub_ops = []; prefixes = []; heads = []; font_ops = []; osd_ops = []; font_name = {}
    for k_nm, nm in enumerate(names):
        root = G.ents[pick[k_nm]] if pick[k_nm] is not None else next(e for e in G.ents if e['name'] == nm)
        assert root['name'] == nm, (root['name'], nm)
        roots.append(root)
        part = []
        def walk(i):
            part.append(i)
            for c in kids[i]: walk(c)
        walk(root['i'])
        assert part == list(range(part[0], part[-1] + 1)), 'subtree not contiguous'
        sq = (squads or {}).get(renames[k_nm])
        for i in part: rel[i] = G.ents[i]['depth'] - root['depth'] + (1 if sq else 0)
        s0, s1 = D.spans[root['i'] + 1]
        part_ops = [list(x) for x in D.ops[s0:s1]]
        # font chunks (ZTTFONT / ZKerningFont prop) and the HUD's 200 .TEX ids (ZOnScreenDisplay2 field 7: JC's
        # kl-merge kl_texmat.py; L01: 183 non-zero ids, every one an occupied .TEX slot) are remapped below; the op
        # objects are kept, so later splicing (patch, event strip) does not lose them
        for i in part:
            t = G.ents[i]['type']
            if t not in FONT_TYPES and t != OSD_TYPE: continue
            p0 = D.spans[i + 1][0]; p1 = _obj_end(D.ops, p0)
            pops = part_ops[p0 - s0:p1 - s0]
            if t in FONT_TYPES:
                fr = [o for o in pops if o[1] & 0x7f == 9 and 0 < o[2] < len(D.pdesc) and is_font(D.chunk(o[2]))]
                assert fr, 'font %s has no font chunk' % G.ents[i]['name']
                font_ops += fr
                for o in fr: font_name[id(o)] = G.ents[i]['name']
            else:
                arr = [q for q, o in enumerate(pops) if o[1] & 0x7f == 1 and o[2] == 200]
                assert len(arr) == 1, ('OSD texture table', G.ents[i]['name'], len(arr))
                tab_ = pops[arr[0] + 1:arr[0] + 201]
                assert all(o[1] & 0x7f == 9 for o in tab_)
                osd_ops += tab_
        if patch: patch(k_nm, renames[k_nm], part_ops)
        if strip_events:
            part_ops, nrem = _strip_events(part_ops, strip_events)
            if nrem: rep['graft events stripped (%s) under %s' % ('/'.join(sorted(strip_events)), renames[k_nm])] += nrem
        if sq:
            sq_name, sq_src = sq
            se = next(e for e in G.ents if e['name'] == sq_src)
            assert se['i'] not in rel and se['type'] == 0x100001, (sq_src, hex(se['type']))
            q0, _ = D.spans[se['i'] + 1]; pe_ = _obj_end(D.ops, q0)
            sprops = [list(x) for x in D.ops[q0:pe_]]; _reset_transform(sprops)
            sev = None; e0_ = pe_ + 1                     # events: name string, then the object
            for _ in range(D.ops[pe_][2]):
                e1_ = _obj_end(D.ops, e0_ + 1)
                if D.ops[e0_][2] == 'ZSquadScript': sev = [list(x) for x in D.ops[e0_:e1_]]
                e0_ = e1_
            assert sev, 'squad donor %s has no ZSquadScript' % sq_src
            part_ops = sprops + [[0, 4, 1]] + sev + [[0, 4, 1]] + part_ops
            rel[se['i']] = 0
            sub.append((se['i'], sq_name)); rep['graft squad %s around %s' % (sq_name, renames[k_nm])] += 1
        sub += [(i, renames[k_nm] if i == root['i'] else None) for i in part]
        sub_ops += part_ops
        prefixes.append((path_of(root['parent']) if root['parent'] != -1 else 'ROOT\\') + nm + '\\')
        heads.append((sq[0] + '\\' if sq else '') + renames[k_nm])
    wrap_src = G.ents[roots[0]['parent']]                 # donor parent group (record/props template)
    ws0, ws1 = D.spans[wrap_src['i'] + 1]
    j = ws0; d = 0
    while True:
        b = D.ops[j][1] & 0x7f
        if b == 2: d += 1
        elif b == 0x7e:
            d -= 1
            if d == 0: break
        j += 1
    wrap_props = [list(x) for x in D.ops[ws0:j + 1]]
    new_prefix = 'ROOT\\' + wrapper_name + '\\'
    npath = 0; sprite_ids = set(); not_sprite = set(id(o) for o in font_ops + osd_ops)
    for o in sub_ops:
        b = o[1] & 0x7f
        if b == 12 and isinstance(o[2], str):
            for nm, pre in zip(heads, prefixes):
                if (o[2] + '\\').startswith(pre):
                    o[2] = new_prefix + nm + '\\' + o[2][len(pre):]; o[2] = o[2].rstrip('\\') if o[2].endswith('\\') else o[2]; npath += 1; break
        elif b == 9 and isinstance(o[2], int) and 0 < o[2] < len(D.pdesc) and id(o) not in not_sprite and is_sprite(D.chunk(o[2])):
            sprite_ids.add(o[2])
    # ---------- PRM: sprites + texture bindings ----------
    prm_extra = []; cmap = {}; tex_need = {}
    def new_chunk(data):
        prm_extra.append(bytes(data)); return prm_cnt + len(prm_extra) - 1
    for sid in sorted(sprite_ids):
        c = bytearray(D.chunk(sid)); n = is_sprite(c)
        w = 10 * n + 2
        for q in range(n):
            bi = struct.unpack_from('<I', c, 4 * (w + q))[0]
            if bi not in cmap:
                bc = bytearray(D.chunk(bi))
                assert len(bc) == 32 and struct.unpack_from('<I', bc)[0] == 0x00020101, (bi, bc[:8])
                slot = struct.unpack_from('<I', bc, 4)[0]
                tex_need.setdefault(slot, []).append(bc)
                cmap[bi] = new_chunk(bc)
            struct.pack_into('<I', c, 4 * (w + q), cmap[bi])
        cmap[sid] = new_chunk(c)
    for o in sub_ops:
        if o[1] & 0x7f == 9 and o[2] in sprite_ids and id(o) not in not_sprite: o[2] = cmap[o[2]]
    # fonts: glyph +4 = .TEX id, + TEX_BIAS for text pages (kl-merge: 'the plain texture id for characters from
    # 0xe000'; in L01 0xf000..0xf002 also use the biased text page) -> keep the bias bit, remap the slot
    fmap = {}; font_idx = []; nglyph = 0
    for o in font_ops:
        fid = o[2]
        if fid not in fmap:
            c = D.chunk(fid); n = is_font(c)
            for q in range(n):
                key = struct.unpack_from('<I', c, 40 + 32 * q + 4)[0]
                assert key < 2 * TEX_BIAS and key % TEX_BIAS, (fid, q, hex(key))
                tex_need.setdefault(key % TEX_BIAS, [])
            nglyph += n
            fmap[fid] = new_chunk(c); font_idx.append(fmap[fid] - prm_cnt)
        o[2] = fmap[fid]
    for o in osd_ops:
        if o[2]:
            assert 0 < o[2] < TEX_BIAS and D.t0[o[2]], ('OSD texture id not in donor .TEX', o[2])
            tex_need.setdefault(o[2], [])
    # ---------- TEX ----------
    free = (s for s in range(1, 4096) if s not in tex_used and s >= 128)
    tex_extra = []; tmap = {}
    for slot in sorted(tex_need):
        if D.t1[slot]: rep['graft tex animated skipped'] += 1
        ns = next(free); tmap[slot] = ns
        e = bytearray(D.tex_entry(slot)); struct.pack_into('<I', e, 12, ns)
        tex_extra.append((ns, bytes(e)))
    # patch binding chunks (they are already in prm_extra by reference -> rebuild)
    for i, data in enumerate(prm_extra):
        if len(data) == 32 and struct.unpack_from('<I', data)[0] == 0x00020101:
            b = bytearray(data); b[4:8] = struct.pack('<I', tmap[struct.unpack_from('<I', data, 4)[0]]); prm_extra[i] = bytes(b)
    for i in font_idx:
        b = bytearray(prm_extra[i]); n = is_font(b)
        for q in range(n):
            key = struct.unpack_from('<I', b, 40 + 32 * q + 4)[0]
            struct.pack_into('<I', b, 40 + 32 * q + 4, (key // TEX_BIAS) * TEX_BIAS + tmap[key % TEX_BIAS])
        prm_extra[i] = bytes(b)
    if font_hook:
        for o in font_ops:
            nc = font_hook(font_name[id(o)], prm_extra[o[2] - prm_cnt])
            if nc is not None:
                o[2] = new_chunk(nc); rep['graft font %s -> new chunk %d' % (font_name[id(o)], o[2])] += 1
    for o in osd_ops:
        if o[2]: o[2] = tmap[o[2]]
    if osd_hook and osd_ops:
        # osd_hook(tables, new_tex, extra): tables = one list of 200 op lists per grafted ZOnScreenDisplay2 (edit
        # op[2] = this level's .TEX id); new_tex(entry bytes) adds a .TEX entry and returns its id; extra = {id: entry}
        # of the grafted Dog Days textures (ANP_DM_HUD: tools/dmhud.py)
        def new_tex(blob):
            ns = next(free); e = bytearray(blob); struct.pack_into('<I', e, 12, ns)
            e += b'\0' * ((-len(e)) & 15); tex_extra.append((ns, bytes(e))); return ns
        assert len(osd_ops) % 200 == 0, len(osd_ops)
        osd_hook([osd_ops[q:q + 200] for q in range(0, len(osd_ops), 200)], new_tex, dict(tex_extra))
    rep['graft fonts %d (%d glyphs), HUD texture ids %d' % (len(font_idx), nglyph, sum(1 for o in osd_ops if o[2]))] += 1
    if os.environ.get('ANP_GRAFT_HOST', 'tail').lower() not in ('old', 'legacy'):
        r = _graft_tail(D, out, g, buf, rep, wrapper_name, wrap_src, wrap_props, sub, rel, len(roots), sub_ops, new_prefix)
        rep['graft %s entities' % '+'.join(names)] += r['nnew']
        rep['graft sprites'] += len(sprite_ids); rep['graft textures'] += len(tex_extra)
        rep['graft path strings rewritten'] += npath
        return dict(prm_extra=prm_extra, tex_extra=tex_extra, heads=heads, **r)
    # ---------- where to hang the wrapper (ANP_GRAFT_HOST=old) ----------
    # Static handles baked into the level (collision octree records, overlap lists ...) are runtime node-table
    # indices, and nodes are allocated block-major (see clusters.node_order).  A node added to any block but the
    # last shifts every later node.  So the wrapper goes under the last group-type entity's nearest plain-ZGROUP
    # ancestor-or-self, directly after that ancestor's subtree: its node then lands at (or next to) the end of
    # the table, and the grafted subtree's own blocks are created after every existing block.
    from clusters import read_ents, node_order
    h = list(struct.unpack_from('<20I', g, 0))
    n = struct.unpack_from('<I', g, h[0])[0]
    pairs = [struct.unpack_from('<II', g, h[0] + 4 + i * 8) for i in range(n)]
    hh, eOld = read_ents(bytes(g)); node_old = node_order(eOld)
    par = []; dep = []; path = [-1]
    for i, (decl, u4) in enumerate(pairs):
        rd = decl >> 25
        if rd: path = path[:len(path) - rd]
        par.append(path[-1]); dep.append(len(path) - 1)
        if decl & 0x1000000: path = path + [i]
    typ = [struct.unpack_from('<I', g, 4 * (d & 0xffffff) + 0x14)[0] for d, u in pairs]
    glast = max(i for i in range(n) if typ[i] & 0x100000)
    P = glast
    while P != -1 and typ[P] != 0x100001: P = par[P]
    if os.environ.get('ANP_GRAFT_AT_ROOT') == '1': P = -1
    if P == -1: rep['graft parent fell back to ROOT'] += 1
    end = P + 1
    if P != -1:
        while end < n and dep[end] > dep[P]: end += 1
    else: end = n
    rep['graft parent ent %d' % P] += 1
    # ---------- PRP splice into target ops ----------
    tk = next(i for i, (p_, op, v) in enumerate(out) if op & 0x7f == 2)
    tspans, tend = node_spans(out, tk)
    assert len(tspans) == n + 1, (len(tspans), n)
    if P == -1: pspan = tspans[0]; ins_at = len(out) - 1
    else: pspan = tspans[P + 1]; ins_at = pspan[1]
    j = pspan[0]; d = 0
    while True:
        b_ = out[j][1] & 0x7f
        if b_ == 2: d += 1
        elif b_ == 0x7e:
            d -= 1
            if d == 0: break
        j += 1
    j += 1; assert out[j][1] & 0x7f == 4; nev = out[j][2]; j += 1
    for e_ in range(nev):
        j += 1; d = 0
        while True:
            b_ = out[j][1] & 0x7f
            if b_ == 2: d += 1
            elif b_ == 0x7e:
                d -= 1
                if d == 0: break
            j += 1
        j += 1
    assert out[j][1] & 0x7f == 4
    p_, op_, nch = out[j]; out[j] = (p_, op_, nch + 1)
    # path strings inside the subtree: ROOT\<path to P>\<wrapper>\...
    pp = []; q = P
    while q != -1:
        nm_off = struct.unpack_from('<I', g, 4 * (pairs[q][0] & 0xffffff))[0]
        pp.append(bytes(buf[nm_off:buf.index(b'\0', nm_off)]).decode('latin1')); q = par[q]
    real_prefix = 'ROOT\\' + ''.join(x + '\\' for x in reversed(pp)) + wrapper_name + '\\'
    for o in sub_ops:
        if o[1] & 0x7f == 12 and isinstance(o[2], str) and o[2].startswith(new_prefix):
            o[2] = real_prefix + o[2][len(new_prefix):]
    ins = [tuple(x) for x in wrap_props] + [(0, 4, 0), (0, 4, len(roots))] + [tuple(x) for x in sub_ops]
    out[ins_at:ins_at] = ins
    nobj = sum(1 for x in ins if x[1] & 0x7f == 2)
    # ---------- GMS ----------
    tf1, tf2 = 0x60, None
    for decl, u4 in pairs:
        off = 4 * (decl & 0xffffff); t = struct.unpack_from('<I', g, off + 0x14)[0]
        if t == 0x200046:
            tf1, tf2 = struct.unpack_from('<II', g, off + 4); break
    assert tf2 is not None, 'no GUI geom template in target'
    while len(g) % 16: g.append(0)
    nid = h[15]
    new_recs = []          # (offset, has_children, depth)
    IDENT9 = (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0)
    own_tf = {}            # donor (matrix, position) -> offsets of a copy in the target gms
    def rec_transform(src_off):
        """record +4/+8 point at the entity's 3x3 matrix and position. Identity entities share the target's GUI
        template; any other transform (e.g. L01's OSD cameras: rotated, at y 1000) is copied so the gms keeps
        agreeing with the prp"""
        m_off, p_off = struct.unpack_from('<II', G.g, src_off + 4)
        try:
            m = struct.unpack_from('<9f', G.g, m_off); p = struct.unpack_from('<3f', G.g, p_off)
        except struct.error:
            return tf1, tf2
        if m == IDENT9 and p == (0.0, 0.0, 0.0): return tf1, tf2
        key = (m, p)
        if key not in own_tf:
            while len(g) % 16: g.append(0)
            mo = len(g); g.extend(struct.pack('<9f', *m))
            while len(g) % 16: g.append(0)
            po = len(g); g.extend(struct.pack('<3f', *p))
            own_tf[key] = (mo, po); rep['graft gms transforms kept (non-identity)'] += 1
        return own_tf[key]
    def add_record(src_off, name, kids, depth):
        nonlocal nid
        r = bytearray(G.g[src_off:src_off + 64])
        while len(buf) % 4: buf.append(0)
        noff = len(buf); buf.extend(name.encode('latin1') + b'\0')
        struct.pack_into('<III', r, 0, noff, *rec_transform(src_off))
        struct.pack_into('<I', r, 48, nid); nid += 1
        while len(g) % 16: g.append(0)
        off = len(g); g.extend(r)
        new_recs.append((off, kids, depth))
    wdep = (dep[P] + 1) if P != -1 else 0
    add_record(wrap_src['off'], wrapper_name, True, wdep)
    for i, rn in sub:
        e = G.ents[i]
        add_record(e['off'], rn or e['name'], bool(e['decl'] & 0x1000000), wdep + 1 + rel[i])
    # rebuild the decl list from (offset, has_children, depth)
    seq = [(4 * (d_ & 0xffffff), bool(d_ & 0x1000000), dep[i], u_) for i, (d_, u_) in enumerate(pairs)]
    seq = seq[:end] + [(o_, k_, dd, 0) for o_, k_, dd in new_recs] + seq[end:]
    allp = []; openl = 0
    for off, kids, depth in ((s[0], s[1], s[2]) for s in seq):
        rd = openl - depth; assert rd >= 0, 'bad depth sequence'
        allp.append([(off // 4) | (0x1000000 if kids else 0) | (rd << 25), 0])
        openl = depth + (1 if kids else 0)
    for k_, s in enumerate(seq): allp[k_][1] = s[3]
    # sanity: unchanged prefix reproduces the original decls exactly
    assert all(tuple(allp[i]) == pairs[i] for i in range(end)), 'decl rebuild mismatch'
    while len(g) % 16: g.append(0)
    h[0] = len(g)
    g.extend(struct.pack('<I', len(allp)) + b''.join(struct.pack('<II', *p_) for p_ in allp))
    new_pairs = new_recs
    h[15] = nid
    # class stats h[4]
    addc = collections.Counter([G.ents[wrap_src['i']]['type']] + [G.ents[i]['type'] for i, _ in sub])
    nt = struct.unpack_from('<I', g, h[4])[0]
    tab4 = [list(struct.unpack_from('<3I', g, h[4] + 4 + i * 12)) for i in range(nt)]
    have = {r[0]: r for r in tab4}
    for t, c in addc.items():
        if t in have: have[t][1] += c
        else: tab4.append([t, c, 0]); rep['graft h4 new type %x' % t] += 1
    while len(g) % 16: g.append(0)
    h[4] = len(g); g.extend(struct.pack('<I', len(tab4)) + b''.join(struct.pack('<3I', *r) for r in tab4))
    # pool blocks h[5]
    struct.pack_into('<20I', g, 0, *h)
    hh, eL = read_ents(bytes(g))
    blocks = compute_blocks(eL, basetype_guess)
    while len(g) % 16: g.append(0)
    h[5] = len(g); g.extend(struct.pack('<I', len(blocks)) + b''.join(struct.pack('<24I', *b_) for b_ in blocks))
    struct.pack_into('<20I', g, 0, *h)
    # node shifts of existing entities -> remap the static overlap lists (h[6]: idx*0x80+0x10 | flags)
    node_new = node_order(eL)
    oldpos = list(range(end)) + list(range(end + len(new_recs), len(eL)))
    nmap = {node_old[i]: node_new[oldpos[i]] for i in range(n)}
    moved = {a: b_ for a, b_ in nmap.items() if a != b_}
    rep['graft existing nodes shifted'] += len(moved)
    inv_old = {node_old[i]: i for i in range(n)}
    for a in sorted(moved)[:12]:
        i = inv_old[a]; rep['graft shifted: ent %d type %x' % (i, typ[i])] += 1
    if moved and 0 < h[6] < len(g):
        o6 = h[6] + 4; n7 = struct.unpack_from('<I', g, o6)[0]; i6 = 4; nre = 0
        while i6 < n7:
            i6 += 1
            while True:
                v = struct.unpack_from('<I', g, o6 + 4 * i6)[0]; x = v & ~7
                if x:
                    k_ = (x - 0x10) // 0x80
                    if k_ in moved: struct.pack_into('<I', g, o6 + 4 * i6, moved[k_] * 0x80 + 0x10 | (v & 7)); nre += 1
                i6 += 1
                if v & 1: break
        rep['graft overlap entries remapped'] += nre
    rep['graft %s entities' % '+'.join(names)] += len(new_pairs)
    rep['graft sprites'] += len(sprite_ids); rep['graft textures'] += len(tex_extra)
    rep['graft path strings rewritten'] += npath
    # end / nnew: the grafted records sit at entity positions end .. end+nnew-1 (existing entity i >= end -> i+nnew)
    return dict(prm_extra=prm_extra, tex_extra=tex_extra, nobj=nobj, prefix=real_prefix, end=end, nnew=len(new_recs),
                heads=heads)

# ---------------------------------------------------------------------------------------------------------------------
# ANP_GRAFT_HOST=tail (default): where the wrapper hangs.
# An existing node keeps its static index only if every new node lands in the LAST block (the last group-type entity
# gl's block) at a slot >= every slot already used there, or in blocks created after it (clusters.node_order). In every
# Dead Men story level gl is a ZAllocMany clone (or sits inside one). ZAllocMany stage 3 (vt slot 84, kl2 0x48e1b0)
# walks EVERY child of a template's pool group, writes child+0x58 = template and copies[i] = child into the template's
# count-sized array (+0x68): a wrapper hung under the pool (the old host) is written out of bounds and overflows that
# array on every load. Slot 83 (0x9087f0) also hides a clone's whole subtree (flag 0x400) and spawn (slots 100/101)
# moves and re-attaches clones, so the wrapper cannot live inside a clone either.
# So the tail pool is retired in place and rebuilt at the very end of the node table:
#   - every clone K of the tail pool group P is retyped to ZGROUP (same group basetype 0 -> no index moves), its
#     ZAllocMany props (count, message, clone flag, pool path) dropped and its subtree's ZSetZDefine events removed;
#   - the clones other than C (the one holding gl) are hidden like stock templates (ZGEOM[3]=1, record flag 0x400 on
#     the subtree); C..gl (the chain) stays visible at world identity, every other branch below C is hidden;
#   - C is renamed ANP_TailHost (its siblings share its name; paths resolve to the first match);
#   - gl gets a new last child ANP_Tail (ZGROUP, prio p = smallest with 8p >= the largest slot in gl's block) holding
#     ANP_Pool (ZGROUP) with N fresh copies of the first clone, and the wrapper with the grafted subtree;
#   - the templates that named P are pointed at ANP_Pool.
# No existing node moves (asserted). M01..M14: 0 moves, the new nodes run from old max + 1.
ALLOC_T = 0x1000ca
ZGROUP_T = 0x100001

def _z3_index(ops, s0):
    """op index of ZGEOM[3] (the first bool after the position array) in the props object starting at ops[s0]"""
    j = s0 + 1; ends = 0
    while True:
        b = ops[j][1] & 0x7f
        if b == 0x7c:
            ends += 1
            if ends == 2:
                assert ops[j + 1][1] & 0x7f == 6, ('ZGEOM[3] not a bool', ops[j + 1])
                return j + 1
        assert b != 0x7e, 'no ZGEOM[3]'
        j += 1

def _alloc_tail(ops, s0, pe):
    """ZAllocMany props: the last four values (count int16, message, clone flag, pool path) -> their op index"""
    t = ops[pe - 5:pe - 1]
    assert [o[1] & 0x7f for o in t] == [8, 12, 6, 12] and ops[pe - 1][1] & 0x7f == 0x7e, ('ZAllocMany props', t)
    return pe - 5

def _graft_tail(D, out, g, buf, rep, wrapper_name, wrap_src, wrap_props, sub, rel, nroots, sub_ops, new_prefix):
    from clusters import read_ents, node_order
    G = D.G
    g0 = bytes(g)
    h = list(struct.unpack_from('<20I', g, 0))
    n = struct.unpack_from('<I', g, h[0])[0]
    pairs = [struct.unpack_from('<II', g, h[0] + 4 + i * 8) for i in range(n)]
    _, eOld = read_ents(g0); node_old = node_order(eOld)
    par = []; dep = []; path = [-1]
    for i, (decl, u4) in enumerate(pairs):
        rd = decl >> 25
        if rd: path = path[:len(path) - rd]
        par.append(path[-1]); dep.append(len(path) - 1)
        if decl & 0x1000000: path = path + [i]
    roff = [4 * (d_ & 0xffffff) for d_, u_ in pairs]
    typ = [struct.unpack_from('<I', g, o + 0x14)[0] for o in roff]
    def ename(i):
        o = struct.unpack_from('<I', g, roff[i])[0]; return bytes(buf[o:buf.index(b'\0', o)]).decode('latin1')
    names = [ename(i) for i in range(n)]
    kids = collections.defaultdict(list)
    for i in range(n): kids[par[i]].append(i)
    def sub_end(i):
        e = i + 1
        while e < n and dep[e] > dep[i]: e += 1
        return e
    tk = next(i for i, (p_, op, v) in enumerate(out) if op & 0x7f == 2)
    spans, _ = node_spans(out, tk)
    assert len(spans) == n + 1, (len(spans), n)
    def props_rng(i):
        s0 = spans[i + 1][0]; return s0, _obj_end(out, s0)
    def add_name(s):
        while len(buf) % 4: buf.append(0)
        o = len(buf); buf.extend(s.encode('latin1') + b'\0'); return o
    while len(g) % 16: g.append(0)
    idm = len(g); g.extend(struct.pack('<9f', 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0) + b'\0' * 12)
    idp = len(g); g.extend(struct.pack('<3f', 0.0, 0.0, 0.0) + b'\0' * 4)
    gl = max(i for i in range(n) if typ[i] & 0x100000)
    end = sub_end(gl)
    C = gl
    while C != -1 and typ[C] != ALLOC_T: C = par[C]
    edits = []              # (op start, op end, replacement ops) on existing nodes, disjoint
    nobj = 0
    pool = None
    def first_match(x):     # path components resolve to the first child with the name
        return next(c for c in kids[par[x]] if names[c] == names[x]) == x
    if C != -1:
        P = par[C]
        assert P != -1 and typ[P] == ZGROUP_T, ('tail clone parent', P, P != -1 and hex(typ[P]))
        K = kids[P]; N = len(K)
        assert all(typ[c] == ALLOC_T for c in K), 'tail pool has non-ZAllocMany children'
        q = par[P]
        while q != -1: assert typ[q] != ALLOC_T, 'ZAllocMany above the tail pool'; q = par[q]
        allK = []
        for c in K: allK += list(range(c, sub_end(c)))
        assert all(typ[q] != ALLOC_T for q in allK if q not in K), 'ZAllocMany inside a tail clone'
        for c in K:
            s0, pe = props_rng(c); a = _alloc_tail(out, s0, pe)
            assert out[a + 2][2] == 1, ('tail pool child not a clone', c)
        chain = [gl]
        while chain[-1] != C: chain.append(par[chain[-1]])
        chain.reverse()                                   # C .. gl
        x = P
        while x != -1: assert first_match(x), ('path component not first match', names[x]); x = par[x]
        for x in chain[1:]: assert first_match(x), ('chain name not first match', names[x])
        assert not any(names[c] == 'ANP_TailHost' for c in K), 'ANP_TailHost taken'
        pool_old = 'ROOT\\' + ''.join(names[y] + '\\' for y in reversed(_anc(P, par))).rstrip('\\')
        T = []
        for i in range(n):
            if typ[i] != ALLOC_T or i in K: continue
            s0, pe = props_rng(i); a = _alloc_tail(out, s0, pe)
            if out[a + 2][2] == 0 and out[a + 3][2] == pool_old:
                assert out[a][2] == N, ('template count != pool size', i, out[a][2], N); T.append(i)
        # step 1: copy the first clone (converted ops + records) before anything is edited
        c0, c1 = spans[K[0] + 1]
        copy_ops = [list(o) for o in out[c0:c1]]
        copy_ents = list(range(K[0], sub_end(K[0])))
        # steps 2-3: retype, strip ZSetZDefine, hide
        chainset = set(chain); hidden = set(); top = set()
        for c in K:
            if c != C: top.add(c); hidden.update(range(c, sub_end(c)))
        for q in chain:
            for ch in kids[q]:
                if ch not in chainset: top.add(ch); hidden.update(range(ch, sub_end(ch)))
        nzdef = 0
        for q in allK:
            s0, pe = props_rng(q)
            pr = [list(o) for o in out[s0:pe]]
            z = _z3_index(pr, 0)
            if q in chainset: pr[z][2] = 0; _reset_transform(pr)
            elif q in top: pr[z][2] = 1
            if q in K: pr = pr[:_alloc_tail(pr, 0, len(pr))] + pr[-1:]
            edits.append((s0, pe, [tuple(o) for o in pr]))
            assert out[pe][1] & 0x7f == 4
            nev = out[pe][2]; j = pe + 1; keep = []; nd = 0
            for _ in range(nev):
                e1 = _obj_end(out, j + 1)
                if out[j][2] == 'ZSetZDefine': nd += 1; nobj -= sum(1 for o in out[j:e1] if o[1] & 0x7f == 2)
                else: keep += out[j:e1]
                j = e1
            if nd: edits.append((pe, j, [(out[pe][0], out[pe][1], nev - nd)] + keep)); nzdef += nd
            o = roff[q]; fl = struct.unpack_from('<I', g, o + 0x1c)[0]
            fl = (fl | 0x400) if q in hidden else (fl & ~0x400)
            struct.pack_into('<I', g, o + 0x1c, fl)
        for c in K: struct.pack_into('<I', g, roff[c] + 0x14, ZGROUP_T)
        for q in chain: struct.pack_into('<II', g, roff[q] + 4, idm, idp)
        # step 4: C -> ANP_TailHost
        struct.pack_into('<I', g, roff[C], add_name('ANP_TailHost')); names[C] = 'ANP_TailHost'
        rep['graft tail pool: %d clone(s) of %s retired (ZGROUP, %d hidden, chain %s), %d template(s) retargeted, '
            'ZSetZDefine stripped %d' % (N, names[P][-60:], len(hidden), '/'.join(names[q] for q in chain), len(T), nzdef)] += 1
        grp_tpl = P
    else:
        rep['graft tail: last group %d (%s) is not in a clone' % (gl, names[gl][-50:])] += 1
        grp_tpl = next(i for i in range(n) if typ[i] == ZGROUP_T)
        T = []
    host_path = 'ROOT\\' + ''.join(names[y] + '\\' for y in reversed(_anc(gl, par)))
    tail_path = host_path + 'ANP_Tail'
    pool_path = tail_path + '\\ANP_Pool'
    # step 6: templates -> ANP_Pool
    for t in T:
        s0, pe = props_rng(t); a = _alloc_tail(out, s0, pe) - s0
        pr = list(out[s0:pe]); pr[a + 3] = (pr[a + 3][0], pr[a + 3][1], pool_path)
        edits.append((s0, pe, pr))
    # step 5: new nodes, as the last child of gl
    mx = max([g0[roff[c] + 0x35] * 8 + basetype_guess(typ[c]) for c in kids[gl]] or [0])
    ptail = next(p_ for p_ in range(4) if 8 * p_ >= mx)
    assert ptail <= 2, ('no prio for ANP_Tail', mx)
    s0, pe = props_rng(grp_tpl)
    gprops = [list(o) for o in out[s0:pe]]; _reset_transform(gprops); gprops[_z3_index(gprops, 0)][2] = 0
    gprops = [tuple(o) for o in gprops]
    nid = h[15]
    new_recs = []           # (record offset, has children, depth, type)
    def add_rec(r, name_off, tf, depth, kids_, prio=None):
        nonlocal nid
        r = bytearray(r); struct.pack_into('<I', r, 0, name_off)
        if tf: struct.pack_into('<II', r, 4, *tf)
        struct.pack_into('<I', r, 48, nid); nid += 1
        if prio is not None: r[0x35] = prio
        while len(g) % 16: g.append(0)
        off = len(g); g.extend(r); new_recs.append((off, kids_, depth, struct.unpack_from('<I', r, 0x14)[0]))
    def grp_rec(name, depth, prio):
        r = bytearray(g0[roff[grp_tpl]:roff[grp_tpl] + 64])
        struct.pack_into('<I', r, 0x1c, struct.unpack_from('<I', r, 0x1c)[0] & ~0x400)
        add_rec(r, add_name(name), (idm, idp), depth, True, prio)
    d0 = dep[gl] + 1
    grp_rec('ANP_Tail', d0, ptail)
    # ANP_MERC_DND=1 (tools/dnd.py): ANP_DND (down-not-dead modifier squads for the Dead Men merc squads) as ANP_Tail's
    # first child, built in this pass so all its nodes are new; off -> nothing changes
    import dnd
    dres = dnd.graft_hook(out, spans, names, rep)
    new_ops = list(gprops) + [(0, 4, 0), (0, 4, (2 if T else 1) + (1 if dres else 0))]
    if dres:
        drecs, dops, _, _ = dres
        for tpl, nm_, rd_, kd_, pr_ in drecs:
            r_ = bytearray(tpl); struct.pack_into('<I', r_, 0x1c, struct.unpack_from('<I', r_, 0x1c)[0] & ~0x400)
            add_rec(r_, add_name(nm_), (idm, idp), d0 + 1 + rd_, kd_, pr_)
        new_ops += dops
        rep['merc dnd: ANP_DND under %s, %d entities' % (tail_path[-50:], len(drecs))] += 1
    if T:
        grp_rec('ANP_Pool', d0 + 1, 0)
        new_ops += list(gprops) + [(0, 4, 0), (0, 4, N)]
        pe_c = _obj_end(copy_ops, 0); a = _alloc_tail(copy_ops, 0, pe_c)
        copy_ops[a][2] = N; copy_ops[a + 2][2] = 1; copy_ops[a + 3][2] = pool_path
        for _ in range(N):
            new_ops += [tuple(o) for o in copy_ops]
            for q in copy_ents:
                # same name, transform and flags as the first clone (shared .buf/.gms data, like the stock template
                # and its clones); new id; decl u4 0
                add_rec(g0[roff[q]:roff[q] + 64], struct.unpack_from('<I', g0, roff[q])[0], None,
                        d0 + 2 + dep[q] - dep[K[0]], bool(pairs[q][0] & 0x1000000))
        rep['graft tail: ANP_Pool with %d copies of %d entities, ANP_Tail prio %d' % (N, len(copy_ents), ptail)] += 1
    # the wrapper + grafted subtree
    real_prefix = tail_path + '\\' + wrapper_name + '\\'
    for o in sub_ops:
        if o[1] & 0x7f == 12 and isinstance(o[2], str) and o[2].startswith(new_prefix):
            o[2] = real_prefix + o[2][len(new_prefix):]
    new_ops += [tuple(x) for x in wrap_props] + [(0, 4, 0), (0, 4, nroots)] + [tuple(x) for x in sub_ops]
    own_tf = {}
    IDENT9 = (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0)
    def rec_transform(src_off):
        m_off, p_off = struct.unpack_from('<II', G.g, src_off + 4)
        try:
            m = struct.unpack_from('<9f', G.g, m_off); p = struct.unpack_from('<3f', G.g, p_off)
        except struct.error:
            return idm, idp
        if m == IDENT9 and p == (0.0, 0.0, 0.0): return idm, idp
        if (m, p) not in own_tf:
            while len(g) % 16: g.append(0)
            mo = len(g); g.extend(struct.pack('<9f', *m))
            while len(g) % 16: g.append(0)
            po = len(g); g.extend(struct.pack('<3f', *p))
            own_tf[(m, p)] = (mo, po); rep['graft gms transforms kept (non-identity)'] += 1
        return own_tf[(m, p)]
    wdep = d0 + 1
    add_rec(G.g[wrap_src['off']:wrap_src['off'] + 64], add_name(wrapper_name), rec_transform(wrap_src['off']), wdep, True)
    for i, rn in sub:
        e = G.ents[i]
        add_rec(G.g[e['off']:e['off'] + 64], add_name(rn or e['name']), rec_transform(e['off']), wdep + 1 + rel[i],
                bool(e['decl'] & 0x1000000))
    nobj += sum(1 for x in new_ops if x[1] & 0x7f == 2)
    # ---------- PRP: edits, then ANP_Tail as gl's last child ----------
    s0, pe = props_rng(gl); j = pe + 1
    for _ in range(out[pe][2]): j = _obj_end(out, j + 1)
    assert out[j][1] & 0x7f == 4
    edits.append((j, j + 1, [(out[j][0], out[j][1], out[j][2] + 1)]))
    edits.append((spans[gl + 1][1], spans[gl + 1][1], new_ops))
    edits.sort(key=lambda x: (x[0], x[1]))
    for (a0, b0, _), (a1, b1, _) in zip(edits, edits[1:]): assert b0 <= a1, 'overlapping prp edits'
    for a_, b_, ops_ in reversed(edits): out[a_:b_] = ops_
    # ---------- GMS: decls, h4, h5 ----------
    seq = [(roff[i], bool(pairs[i][0] & 0x1000000) or i == gl, dep[i], pairs[i][1]) for i in range(n)]
    seq = seq[:end] + [(o_, k_, dd, 0) for o_, k_, dd, _ in new_recs] + seq[end:]
    allp = []; openl = 0
    for off, kids_, depth, u_ in seq:
        rd = openl - depth; assert rd >= 0, 'bad depth sequence'
        allp.append(((off // 4) | (0x1000000 if kids_ else 0) | (rd << 25), u_))
        openl = depth + (1 if kids_ else 0)
    assert all(allp[i] == pairs[i] for i in range(end) if i != gl), 'decl rebuild mismatch'
    while len(g) % 16: g.append(0)
    h[0] = len(g); g.extend(struct.pack('<I', len(allp)) + b''.join(struct.pack('<II', *p_) for p_ in allp))
    h[15] = nid
    addc = collections.Counter(t_ for _, _, _, t_ in new_recs)
    if C != -1:
        addc[ALLOC_T] -= N; addc[ZGROUP_T] += N
    nt = struct.unpack_from('<I', g, h[4])[0]
    tab4 = [list(struct.unpack_from('<3I', g, h[4] + 4 + i * 12)) for i in range(nt)]
    have = {r_[0]: r_ for r_ in tab4}
    for t_, c_ in addc.items():
        if t_ in have: have[t_][1] += c_; assert have[t_][1] >= 0, hex(t_)
        else: assert c_ > 0; tab4.append([t_, c_, 0]); rep['graft h4 new type %x' % t_] += 1
    while len(g) % 16: g.append(0)
    h[4] = len(g); g.extend(struct.pack('<I', len(tab4)) + b''.join(struct.pack('<3I', *r_) for r_ in tab4))
    struct.pack_into('<20I', g, 0, *h)
    _, eL = read_ents(bytes(g))
    blocks = compute_blocks(eL, basetype_guess)
    while len(g) % 16: g.append(0)
    h[5] = len(g); g.extend(struct.pack('<I', len(blocks)) + b''.join(struct.pack('<24I', *b_) for b_ in blocks))
    struct.pack_into('<20I', g, 0, *h)
    # no existing node may move: static handles are baked into .oct/.sgp/.rmc/.rmi/.sgd/.hrd/.HVK and the overlap lists
    node_new = node_order(eL); nn = len(new_recs)
    oldpos = list(range(end)) + list(range(end + nn, len(eL)))
    moved = sum(1 for i in range(n) if node_old[i] != node_new[oldpos[i]])
    assert moved == 0, 'graft tail host moved %d existing nodes' % moved
    newn = sorted(node_new[end:end + nn])
    assert newn == list(range(n + 1, n + 1 + nn)), 'new nodes not at the tail'
    rep['graft tail host ent %d (%s), new entities %d at nodes %d..%d, existing nodes moved 0' % (
        gl, names[gl][-40:], nn, newn[0], newn[-1])] += 1
    return dict(nobj=nobj, prefix=real_prefix, end=end, nnew=nn)

def _anc(i, par):
    """i and its ancestors, nearest first"""
    r = []
    while i != -1: r.append(i); i = par[i]
    return r
