"""Down-not-dead for Dead Men's merc squads (ANP_MERC_DND=1; default 0 = off, nothing changed).

Dog Days L10 makes a squad "down not dead" with two child entities of the squad (type 0x100001, ZGROUP-like records):
  DownNotDeadBehaviour  component DownNotDeadBehaviourRout  (C0 b0 b0)
  SM_DND                component SquadModifierBehaviour     (13x NotSet, eDND_ForceDownNotDead, ..., eSC_Enabled, f1 b0 C0 b1 b0)
(work/scn/dd/L10_Main, squad 'AI!Enemies!GalleryCorridor_Squad_GalleryCampers', entities 388/389 = scene nodes 389/390.)

Targeting. A squad behaviour has no target field: the containers in its props are lists of OTHER behaviours/scripts to
fire (paths like ROOT\\...\\RunToCover), not targets, and in every stock Dog Days scene (1204 SquadModifierBehaviours
surveyed) the behaviour acts on the squad it is a child of; squads that drive another squad's behaviour do it by path,
and that behaviour still acts on its own parent. So "C0" = no follow-up behaviours, and the parent IS the target.
Children can only be added at the tail (node indices are baked, see CLAUDE.md), so the pair cannot go under the Dead
Men squad itself. But ZMercSquad membership is not the tree: it is the four slot enums of the ZMercSquad component
('Kane', 'Merc_05', ...). Dog Days uses exactly that for its buddy modifiers: L11 'AI!Friendly!A1!Lynch_A1_Modifier' is
a separate ZMercSquad ('Kane', No_Mercenary x3) whose only children are SquadModifierBehaviours for Lynch. So for every
distinct member set of the Dead Men merc squads we add such a modifier squad (same ZMercSquad slot enums) holding the
L10 pair, parent = that squad, exactly as in L10.

Which squads: every node whose component list has 'ZMercSquad' with at least one slot != No_Mercenary (Dead Men's
Characters!Mercenaries!*, hero-proxy and dialogue merc squads all name the same slots: Kane / Merc_05..07). One
modifier squad per distinct slot tuple (squads with the same slots are the same characters).

Placement (tail-only, like graft._graft_tail): a new ZGROUP 'ANP_DND' as the last child of the last group-type
entity gl (the last block; prio p = smallest with 8p >= every slot used in gl's block), holding the modifier squads.
Every new entity lands after all existing node indices; asserted here (0 moved).

API: add_merc_dnd(out, g, buf, rep) -> number of prp BeginObjects added (add to nobj).
  out: port_level.port()'s converted prp op list (list of (pos, op, value)), edited in place;
  g:   the converted .gms (raw, bytearray), edited in place;  buf: the .buf (bytearray), names appended;
  rep: collections.Counter report.
Normal build path: graft._graft_tail calls graft_hook() and builds ANP_DND as ANP_Tail's first child (all nodes new,
no port_level change). add_merc_dnd() is only for already-built levels / the self-test (host = FrameForOsd); do NOT
also call it from port_level when the graft runs. Former call-site suggestion (port_level.port), just before
  `prp_bytes=write_prp(prp.tokens,prp.flags,prp.is_raw,nobj,out)`:
      import dnd; nobj+=dnd.add_merc_dnd(out,g,buf,rep)

Self-test (writes nothing):  py tools\\dnd.py --selftest work\\out_gapA\\M09
  with --write <dir>: also writes <dir>\\<LV>\\<LV>_Main.zip (copy of the level zip, gms/prp/buf replaced) and runs
  ovlcheck against the Dead Men source.
"""
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clusters import read_ents, node_order, compute_blocks, basetype_guess

ZGROUP_T = 0x100001
NO_MERC = 'No_Mercenary'
REF_LEVEL = 'L10_Main'
REF_SQUAD = 'AI!Enemies!GalleryCorridor_Squad_GalleryCampers'
REF_KIDS = ('DownNotDeadBehaviour', 'SM_DND')
IDENT9 = (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0)


def enabled():
    return os.environ.get('ANP_MERC_DND', '0') == '1'


def _obj_end(ops, j):
    d = 0
    while True:
        b = ops[j][1] & 0x7f
        if b == 2: d += 1
        elif b == 0x7e:
            d -= 1
            if d == 0: return j + 1
        j += 1


def _node_spans(ops, k):
    from graft import node_spans
    return node_spans(ops, k)


def _node_parts(ops, s):
    """node at op s -> (props (s0,e0), [(event name, (a,b) incl. name op)], children container op index)"""
    e0 = _obj_end(ops, s)
    assert ops[e0][1] & 0x7f == 4
    j = e0 + 1; evs = []
    for _ in range(ops[e0][2]):
        a = j; nm = ops[j][2]; j = _obj_end(ops, j + 1); evs.append((nm, (a, j)))
    assert ops[j][1] & 0x7f == 4
    return (s, e0), evs, j


_REF = None
def reference():
    """the L10 squad + its DND pair: gms records (64 bytes) and prp ops, verified against the expected layout"""
    global _REF
    if _REF: return _REF
    from anp_paths import WORK
    from scene import Scene
    S = Scene(os.path.join(WORK, 'scn', 'dd', REF_LEVEL))
    G = S.gms
    sq = next(e['i'] for e in G.ents if e['name'] == REF_SQUAD)
    kids = {G.ents[c - 1]['name']: c for c in S.nodes[sq + 1]['children']}
    ref = dict(rec={}, props={}, event={})
    for nm in ('SQUAD',) + REF_KIDS:
        node = sq + 1 if nm == 'SQUAD' else kids[nm]
        e = G.ents[node - 1]
        assert e['type'] == ZGROUP_T, (nm, hex(e['type']))
        ref['rec'][nm] = bytes(G.g[e['off']:e['off'] + 64])
        n = S.nodes[node]
        ref['props'][nm] = [tuple(o) for o in n['props']]
        if nm != 'SQUAD':
            assert len(n['events']) == 1 and not n['children'], nm
            ref['event'][nm] = (n['events'][0][0], [tuple(o) for o in n['events'][0][1]])
    # layout checks: the exact L10 values the task names
    ev = ref['event']
    assert ev['DownNotDeadBehaviour'][0] == 'DownNotDeadBehaviourRout'
    assert [(o[1] & 0x7f, o[2]) for o in ev['DownNotDeadBehaviour'][1]] == [(4, 0), (6, 0), (6, 0)]
    nm, sm = ev['SM_DND']
    assert nm == 'SquadModifierBehaviour'
    vals = [o[2] for o in sm]
    assert vals[13] == 'eDND_ForceDownNotDead' and vals[22] == 'eSC_Enabled' and len(vals) == 29, vals
    assert [(o[1] & 0x7f, o[2]) for o in sm[24:]] == [(10, 1.0), (6, 0), (4, 0), (6, 1), (6, 0)], sm[24:]
    _REF = ref
    return ref


def _sig(ops):
    return [o[1] & 0x7f for o in ops]


def merc_groups(out, spans, names, rep):
    """slot tuple -> [(entity, name, ZMercSquad event ops)] for the merc squads (module doc)"""
    groups = collections.OrderedDict()
    for i in range(len(spans) - 1):
        _, evs, _ = _node_parts(out, spans[i + 1][0])
        for nm, (a, b) in evs:
            if nm != 'ZMercSquad': continue
            ev = [tuple(o) for o in out[a + 2:b - 1]]   # inside the event object
            slots = tuple(o[2] for o in ev if o[1] & 0x7f == 14)
            if all(s == NO_MERC for s in slots):
                rep['merc dnd: squad without mercs skipped'] += 1; continue
            groups.setdefault(slots, []).append((i, names[i], ev))
    return groups


def build_subtree(groups, prio=0):
    """ANP_DND + one modifier ZMercSquad per slot tuple + the L10 pair.
    -> (recs [(64-byte record template, name, depth below ANP_DND's parent (0 = ANP_DND), has children, prio)],
        prp ops of the whole subtree (one node), BeginObject count, plan)"""
    R = reference()
    sq_props = R['props']['SQUAD']
    for nm in REF_KIDS: assert _sig(R['props'][nm]) == _sig(sq_props), nm
    recs = [(R['rec']['SQUAD'], 'ANP_DND', 0, True, prio)]
    ops = [(0, 2, None)] + list(sq_props) + [(0, 0x7e, None), (0, 4, 0), (0, 4, len(groups))]
    nobj = 1; plan = []
    for slots, srcs in groups.items():
        sname = 'ANP_DND_' + '_'.join(s for s in slots if s != NO_MERC)
        recs.append((R['rec']['SQUAD'], sname, 1, True, 0))
        ops += [(0, 2, None)] + list(sq_props) + [(0, 0x7e, None), (0, 4, 1),
                (0, 12, 'ZMercSquad'), (0, 2, None)] + list(srcs[0][2]) + [(0, 0x7e, None), (0, 4, len(REF_KIDS))]
        nobj += 2
        for kn in REF_KIDS:
            recs.append((R['rec'][kn], kn, 2, False, None))
            evn, evops = R['event'][kn]
            ops += [(0, 2, None)] + list(R['props'][kn]) + [(0, 0x7e, None), (0, 4, 1),
                    (0, 12, evn), (0, 2, None)] + list(evops) + [(0, 0x7e, None), (0, 4, 0)]
            nobj += 2
        plan.append((sname, slots, [x[1] for x in srcs]))
    return recs, ops, nobj, plan


def graft_hook(out, spans, names, rep):
    """called by graft._graft_tail (ANP_MERC_DND=1): ANP_DND built as ANP_Tail's first child in the same pass.
    -> None (off / no merc squads) or build_subtree(...)"""
    if not enabled(): return None
    groups = merc_groups(out, spans, names, rep)
    if not groups:
        rep['merc dnd: no merc squads'] += 1; return None
    res = build_subtree(groups)
    for sname, slots, srcs in res[3]:
        rep['merc dnd: %s %s <- %s' % (sname, '/'.join(slots), ', '.join(x[-40:] for x in srcs))] += 1
    return res


def add_merc_dnd(out, g, buf, rep, force=None):
    """see module doc. Returns the number of BeginObjects added to the prp (0 when ANP_MERC_DND is off)."""
    if not (enabled() if force is None else force):
        return 0
    R = reference()
    h = list(struct.unpack_from('<20I', g, 0))
    n = struct.unpack_from('<I', g, h[0])[0]
    pairs = [struct.unpack_from('<II', g, h[0] + 4 + i * 8) for i in range(n)]
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
    g0 = bytes(g)
    _, eOld = read_ents(g0); node_old = node_order(eOld)
    tk = next(i for i, o in enumerate(out) if o[1] & 0x7f == 2)
    spans, _ = _node_spans(out, tk)
    assert len(spans) == n + 1, (len(spans), n)
    groups = merc_groups(out, spans, names, rep)
    if not groups:
        rep['merc dnd: no merc squads'] += 1; return None
    res = build_subtree(groups)
    for sname, slots, srcs in res[3]:
        rep['merc dnd: %s %s <- %s' % (sname, '/'.join(slots), ', '.join(x[-40:] for x in srcs))] += 1
    return res


def add_merc_dnd(out, g, buf, rep, force=None):
    """see module doc. Returns the number of BeginObjects added to the prp (0 when ANP_MERC_DND is off)."""
    if not (enabled() if force is None else force):
        return 0
    R = reference()
    h = list(struct.unpack_from('<20I', g, 0))
    n = struct.unpack_from('<I', g, h[0])[0]
    pairs = [struct.unpack_from('<II', g, h[0] + 4 + i * 8) for i in range(n)]
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
    g0 = bytes(g)
    _, eOld = read_ents(g0); node_old = node_order(eOld)
    tk = next(i for i, o in enumerate(out) if o[1] & 0x7f == 2)
    spans, _ = _node_spans(out, tk)
    assert len(spans) == n + 1, (len(spans), n)
    # ---- the Dead Men merc squads ----
    groups = collections.OrderedDict()      # slot tuple -> [(entity, name, event ops)]
    for i in range(n):
        _, evs, _ = _node_parts(out, spans[i + 1][0])
        for nm, (a, b) in evs:
            if nm != 'ZMercSquad': continue
            ev = [tuple(o) for o in out[a + 2:b - 1]]   # inside the event object
            slots = tuple(o[2] for o in ev if o[1] & 0x7f == 14)
            if all(s == NO_MERC for s in slots):
                rep['merc dnd: squad without mercs skipped'] += 1; continue
            groups.setdefault(slots, []).append((i, names[i], ev))
    if not groups:
        rep['merc dnd: no merc squads'] += 1
        return 0
    # ---- host: last group-type entity (last block) ----
    host = os.environ.get('ANP_MERC_DND_HOST', 'last')   # tail/sibling move 2353/2355 nodes on M09 (kept for testing)
    if host in ('tail', 'sibling') and 'ANP_Tail' in names:
        gl = names.index('ANP_Tail')
        if host == 'sibling': gl = par[gl]
    else: gl = max(i for i in range(n) if typ[i] & 0x100000)
    end = gl + 1
    while end < n and dep[end] > dep[gl]: end += 1
    kids_gl = [i for i in range(gl + 1, end) if par[i] == gl]
    mx = max([g0[roff[c] + 0x35] * 8 + basetype_guess(typ[c]) for c in kids_gl] or [0])
    pgrp = next(p_ for p_ in range(4) if 8 * p_ >= mx)
    # ---- shared data ----
    def add_name(s):
        while len(buf) % 4: buf.append(0)
        o = len(buf); buf.extend(s.encode('latin1') + b'\0'); return o
    while len(g) % 16: g.append(0)
    idm = len(g); g.extend(struct.pack('<9f', *IDENT9) + b'\0' * 12)
    idp = len(g); g.extend(struct.pack('<3f', 0.0, 0.0, 0.0) + b'\0' * 4)
    nid = h[15]
    new_recs = []           # (record offset, has children, depth, type)
    def add_rec(tpl, name, depth, kids_, prio=None):
        nonlocal nid
        r = bytearray(tpl)
        struct.pack_into('<I', r, 0, add_name(name))
        struct.pack_into('<II', r, 4, idm, idp)
        struct.pack_into('<I', r, 0x1c, struct.unpack_from('<I', r, 0x1c)[0] & ~0x400)
        struct.pack_into('<I', r, 48, nid); nid += 1
        if prio is not None: r[0x35] = prio
        while len(g) % 16: g.append(0)
        off = len(g); g.extend(r); new_recs.append((off, kids_, depth, struct.unpack_from('<I', r, 0x14)[0]))
    sq_props = R['props']['SQUAD']
    # group props in this level must have the same layout as the L10 squad's (both Dog Days ZGROUP props)
    s0 = spans[gl + 1][0]; gp = out[s0 + 1:_obj_end(out, s0) - 1]
    assert _sig(gp) == _sig(sq_props), 'group props layout differs from L10'
    d0 = dep[gl] + 1
    recs, new_ops, nobj, plan = build_subtree(groups, pgrp)
    for tpl, nm, rd, kd, pr in recs: add_rec(tpl, nm, d0 + rd, kd, pr)
    nsq = len(groups)
    host_path = 'ROOT\\' + '\\'.join(reversed([names[y] for y in _anc(gl, par)]))
    # ---- PRP: gl gets one more child, the new subtree goes at the end of gl's span ----
    _, _, cj = _node_parts(out, spans[gl + 1][0])
    ins = spans[gl + 1][1]
    out[ins:ins] = new_ops
    out[cj] = (out[cj][0], out[cj][1], out[cj][2] + 1)
    # ---- GMS: decls (new records after gl's subtree), h4, h5, h15 ----
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
    nt = struct.unpack_from('<I', g, h[4])[0]
    tab4 = [list(struct.unpack_from('<3I', g, h[4] + 4 + i * 12)) for i in range(nt)]
    addc = collections.Counter(t_ for _, _, _, t_ in new_recs)
    have = {r_[0]: r_ for r_ in tab4}
    for t_, c_ in addc.items():
        if t_ in have: have[t_][1] += c_
        else: tab4.append([t_, c_, 0])
    while len(g) % 16: g.append(0)
    h[4] = len(g); g.extend(struct.pack('<I', len(tab4)) + b''.join(struct.pack('<3I', *r_) for r_ in tab4))
    struct.pack_into('<20I', g, 0, *h)
    _, eL = read_ents(bytes(g))
    blocks = compute_blocks(eL, basetype_guess)
    while len(g) % 16: g.append(0)
    h[5] = len(g); g.extend(struct.pack('<I', len(blocks)) + b''.join(struct.pack('<24I', *b_) for b_ in blocks))
    struct.pack_into('<20I', g, 0, *h)
    # ---- no existing node may move ----
    node_new = node_order(eL); nn = len(new_recs)
    oldpos = list(range(end)) + list(range(end + nn, len(eL)))
    moved = sum(1 for i in range(n) if node_old[i] != node_new[oldpos[i]])
    assert moved == 0, 'merc dnd moved %d existing nodes' % moved
    newn = sorted(node_new[end:end + nn])
    assert newn == list(range(n + 1, n + 1 + nn)), 'merc dnd: new nodes not at the tail'
    rep['merc dnd: %d modifier squad(s) under %s\\ANP_DND (prio %d), entities %d at nodes %d..%d, moved 0' % (
        nsq, host_path[-60:], pgrp, nn, newn[0], newn[-1])] += 1
    for sname, slots, srcs in plan:
        rep['merc dnd: %s %s <- %s' % (sname, '/'.join(slots), ', '.join(s[-40:] for s in srcs))] += 1
    add_merc_dnd.last = dict(plan=plan, host=host_path, nodes=(newn[0], newn[-1]), new_ops=new_ops, prio=pgrp)
    return nobj


def _anc(i, par):
    r = []
    while i != -1: r.append(i); i = par[i]
    return r


# ---------------- self-test ----------------
def _selftest(level_dir, write_dir=None):
    import zipfile, zlib
    from prp import PRP, OPN
    from prpwrite import write_prp
    lv = os.path.basename(os.path.normpath(level_dir))
    zp = os.path.join(level_dir, lv + '_Main.zip')
    z = zipfile.ZipFile(zp)
    def ent(ext):
        return next(x for x in z.namelist() if x.lower().endswith('_main.' + ext))
    graw = z.read(ent('gms')); flag = graw[8]
    g = bytearray(graw[9:] if flag else zlib.decompressobj(-15).decompress(graw[9:]))
    buf = bytearray(z.read(ent('buf')))
    prp = PRP(z.read(ent('prp')))
    out = list(prp.instrs())
    nobj0 = prp.nobjects
    assert out[-1][1] & 0x7f == 0x7f
    rep = collections.Counter()
    add = add_merc_dnd(out, g, buf, rep, force=True)
    for k_, v_ in rep.items(): print('  %s%s' % (k_, '' if v_ == 1 else ' x%d' % v_))
    L = getattr(add_merc_dnd, 'last', None)
    if L:
        print('new prp ops (%d BeginObjects, prp nobjects %d -> %d):' % (add, nobj0, nobj0 + add))
        ops_ = L['new_ops']; j = 0; line = []
        def short(o):
            b_ = o[1] & 0x7f
            if b_ == 2: return '{'
            if b_ == 0x7e: return '}'
            if b_ in (4, 6): return '%s%d' % ('C' if b_ == 4 else 'b', o[2])
            if b_ == 10: return 'f%g' % o[2]
            return repr(o[2]) if b_ in (12, 14, 9) else None
        for o in ops_:
            t = short(o)
            if o[1] & 0x7f == 12 and line: print('     ' + ' '.join(line)); line = []
            if t is not None: line.append(t)
        print('     ' + ' '.join(line))
    if write_dir:
        from port_level import gms_pack
        prp_b = write_prp(prp.tokens, prp.flags, prp.is_raw, nobj0 + add, out)
        # round trip: the written prp parses back to the same ops
        back = list(PRP(prp_b).instrs())
        assert [(o[1], o[2]) for o in back] == [(o[1], o[2]) for o in out], 'prp round trip'
        od = os.path.join(write_dir, lv); os.makedirs(od, exist_ok=True)
        op_ = os.path.join(od, lv + '_Main.zip')
        rp = {ent('gms'): gms_pack(bytes(g)), ent('prp'): prp_b, ent('buf'): bytes(buf)}
        with zipfile.ZipFile(op_, 'w') as zo:
            for info in z.infolist():
                if info.filename in rp: zo.writestr(info, rp[info.filename], compress_type=info.compress_type)
                elif info.filename.lower().endswith(('.gms', '.prp', '.buf', '.zgf', '.sup')):
                    zo.writestr(info, z.read(info), compress_type=info.compress_type)
                # the rest (TEX, prm, ...) is not needed by ovlcheck: left out of the scratch copy
        print('written', op_)
        import ovlcheck
        ok = ovlcheck.run_pair(ovlcheck.dm_zip(lv), op_, lv + '+dnd')
        ok0 = ovlcheck.run_pair(ovlcheck.dm_zip(lv), zp, lv)
        print('ovlcheck', 'OK' if ok else 'FAIL', '(original build:', 'OK' if ok0 else 'FAIL', ')')
        return ok
    return True


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] != '--selftest':
        print(__doc__); sys.exit(2)
    wd = a[a.index('--write') + 1] if '--write' in a else None
    sys.exit(0 if _selftest(a[1], wd) else 1)
