"""heli_call_read.py [--build <heli_stage dir | _Main.zip>]   static proof of what the escape-vehicle CALL does to a CHOPPER.

Question (re/club_campaign.md AA step 5/6, ASSUMED): "calling 0x8154f0 with the chopper starts its Incomming rout via OnlineEscHavokCar field 0".
Method: capstone on kl2.exe (tools/kl_exe.py) for the code, and the built level's .prp/.gms for the data. Nothing is installed or launched.
Prints one line per check ('PASS' / 'FAIL' / 'NOTE') and ends with exactly one of
    RESULT: PASS | RESULT: FAIL <reason> | RESULT: UNKNOWN
PASS = every link from 0x8154f0 to the start of the HeliFlyBehaviourRout was read in the exe AND the build's data reaches it.
UNKNOWN = the exe side holds but there is no build to read (or the build has no chopper). FAIL = a link is missing; the reason names it.
Findings and the handover are in re/heli_call.md. Typical cost: 5-15 s.

GUESS list (kept short, each marked at the use):
  G1 message ids are interned by NAME (each static message object is registered in table 0xdd6728 by 0x6fb080 -> 0x5329b0), so the
     id word of the object that the handler compares equals the id word of the object that the sender posts when the names are equal.
     Not read: the id assignment inside 0x5329b0.
  G2 vtable +0x120 'send' / +0x124 'post' deliver to the controllers of the target entity (ZGROUP) the way they do for stock groups.
"""
import os, re, struct, sys, zipfile, glob, time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(HERE), 'tools')
sys.path.insert(0, TOOLS)

import capstone
import kl_exe

DD_EXE = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\kl2.exe'
HELI = 'ROOT\\EscapeSetup!EscapeChopper\\'
HIDDEN = 0x400                       # .gms entity flag, tools/kl_fa_club.py HIDDEN

fails, notes = [], []


def line(state, what, msg):
    if state == 'FAIL':
        fails.append('%s: %s' % (what, msg))
    print('%-5s %-26s %s' % (state, what, msg), flush=True)


# ---------------------------------------------------------------------------------------------------------- the exe
class Code:
    def __init__(self):
        self.e = kl_exe.Exe(DD_EXE)
        self.code, self.base = self.e.code()
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        self.md.skipdata = True
        self.rt = self.e.rtti()
        self._names = {}

    def dis(self, a, n):
        return [(i.address, i.mnemonic, i.op_str) for i in self.md.disasm(self.e.read(a, n), a) if i.mnemonic != 'int3']

    def name_of_id_word(self, w):
        """Message name of the static object whose id word (+8) sits at address w: the 'push <string>; mov ecx, <obj>' that builds it."""
        if w in self._names:
            return self._names[w]
        pat = b'\xb9' + struct.pack('<I', w - 8)
        out, i = None, -1
        while True:
            i = self.code.find(pat, i + 1)
            if i < 0:
                break
            if self.code[i - 5] == 0x68:
                out = self.e.cstr(struct.unpack_from('<I', self.code, i - 4)[0])
                break
        self._names[w] = out
        return out


def _registered(self, var):
    """Name registered into the global word `var` by the 'push <name>; ... call [vtbl+0x4c]; mov word [var], ax' form (the ZBaseBehaviourRout
    messages, registered at 0x78154b by the name->id registry [0xdd2640]+0xac; so ids ARE assigned per NAME)."""
    last = None
    for a, m, o in self.dis(0x78154b, 0x60):
        if m == 'push' and o.startswith('0xb7') and o not in ('0xb515fc',):
            last = hexs(o)
        if m == 'mov' and o == 'word ptr [0x%x], ax' % var and last:
            return self.e.cstr(last)
    return None


Code.registered = _registered


def hexs(m):
    return int(m, 16) if m.startswith('0x') else int(m)


def exe_side(C):
    ok = True

    # 1. 0x8154f0: the call itself
    ins = C.dis(0x8154f0, 0xc0)
    t = ' | '.join('%s %s' % (m, o) for _a, m, o in ins)
    need = [('state test [esi+0x1dc]', r'cmp byte ptr \[esi \+ 0x1dc\], 0'),
            ('stores the vehicle ref into [[esi+0x5f8]+0x5c]', r'mov dword ptr \[ecx \+ 0x5c\], edi'),
            ('calls a rules slot at +0x308 with 1 or 2', r'mov edx, dword ptr \[edx \+ 0x308\]'),
            ('clears [esi+0xe88]', r'mov byte ptr \[esi \+ 0xe88\], 0')]
    miss = [w for w, rx in need if not re.search(rx, t)]
    if miss:
        line('FAIL', '0x8154f0 shape', 'not as read on 2026-10-17: ' + '; '.join(miss))
        ok = False
    else:
        line('PASS', '0x8154f0 shape', 'needs [rules+0x1dc]==0 (state 0), stores the vehicle ref at [[rules+0x5f8]+0x5c], then rules slot +0x308 (state) with 1/2; '
             'it sends NO message itself')

    # 2. 0x8fa6d0 state 1: the escape state machine sends the RESET message to the vehicle entity (kind != 3 branch)
    ins = C.dis(0x8fa6d0, 0x200)
    seen = [(a, o) for a, m, o in ins if m == 'movzx' and re.search(r'word ptr \[0x[0-9a-f]+\]$', o)]
    names = []
    for a, o in seen:
        w = int(re.search(r'0x[0-9a-f]+', o.split('[')[-1]).group(0), 16)
        n = C.name_of_id_word(w)
        if n:
            names.append((a, n))
    reset_sent = any(n == 'ZMOVEMENT_MSG_RESET' for _a, n in names)
    # the non-kind-3 branch is the one the sample read named: 0x8fa7c4 movzx edx, word [0x168eb14] then call [eax+0x120]
    has_call = any(a == 0x8fa7c4 for a, _o in seen) and any(m == 'mov' and o == 'eax, dword ptr [eax + 0x120]' for a, m, o in ins if 0x8fa7c4 < a < 0x8fa7d4)         and any(m == 'call' and o == 'eax' for a, m, o in ins if 0x8fa7c4 < a < 0x8fa7d4)
    if reset_sent and has_call:
        line('PASS', '0x8fa6d0 state 1', 'posts ZMOVEMENT_MSG_RESET (id word 0x168eb14) with vtable +0x120 at 0x8fa7c4 for a ZHeli (kind 2) / ZHavokCar (kind 1) escape vehicle')
    else:
        line('FAIL', '0x8fa6d0 state 1', 'the RESET send at 0x8fa7c4 was not found (messages seen: %s)' % [n for _a, n in names])
        ok = False

    # 3. ZOnlineEscHavokCar handler (vtable +0x68)
    h = C.rt.by_name['ZOnlineEscHavokCar']
    h = h[0] if isinstance(h, list) else h
    hand = C.e.u32(h + 0x68)
    if hand != 0x5497a0:
        line('FAIL', 'OnlineEscHavokCar vtbl', 'handler is %#x, not 0x5497a0' % hand)
        return False
    ins = C.dis(0x5497a0, 0xc0)
    idv = [(a, hexs(re.search(r'0x[0-9a-f]+', o.split('[')[-1]).group(0))) for a, m, o in ins if m in ('cmp', 'movzx') and 'word ptr [0x' in o or (m == 'cmp' and 'dword ptr [0x' in o)]
    first = [w for a, w in idv if a < 0x549805][0]
    c0 = C.name_of_id_word(first)
    # the posts of the RESET case: (message id word, field offset of [esi]) in order
    posts, cur, fld = [], None, None
    for a, m, o in ins:
        if a >= 0x549860:
            break
        mm = re.match(r'(eax|ecx|edx), (?:dword|word) ptr \[(0x[0-9a-f]+)\]$', o)
        if m == 'movzx' and mm:
            cur = hexs(mm.group(2))
        mm = re.match(r'(eax|edx), dword ptr \[esi \+ (0x3[0-9a-f])\]$', o)
        if m == 'mov' and mm:
            fld = hexs(mm.group(2))
        if m == 'call' and o in ('eax', 'edx') and cur and a > 0x5497e0 and fld is not None:
            posts.append((C.name_of_id_word(cur), fld))
            cur, fld = None, None
    want = [('SetCompletionTime', 0x30), ('AITrigger', 0x30), ('ZMOVEMENT_MSG_RESET', 0x30), ('Show', 0x3c)]
    posts_f = [p for p in posts if p[0]]
    if c0 == 'ZMOVEMENT_MSG_RESET' and posts_f[:4] == want:
        line('PASS', '0x5497a0 handler', 'on ZMOVEMENT_MSG_RESET it posts (vtable +0x124) SetCompletionTime, AITrigger, ZMOVEMENT_MSG_RESET to the object at '
             '[ctrl+0x30] = OnlineEscHavokCar FIELD 0 (Incomming), then Show to [ctrl+0x3c] = FIELD 3 (EscapeChopper_OnMap)')
    else:
        line('FAIL', '0x5497a0 handler', 'first message %s, posts %s (wanted %s)' % (c0, posts_f[:5], want))
        ok = False

    # 4. ZBaseBehaviourRout handler: AITrigger starts the rout; ZHeliFlyBehaviourRout uses the same handler
    for cls in ('ZHeliFlyBehaviourRout', 'ZBaseBehaviourRout'):
        h = C.rt.by_name[cls]
        h = h[0] if isinstance(h, list) else h
        if C.e.u32(h + 0x68) != 0x4ebed0:
            line('FAIL', cls + ' vtbl', 'slot +0x68 is %#x, not 0x4ebed0' % C.e.u32(h + 0x68))
            ok = False
    start = C.e.u32(C.rt.by_name['ZHeliFlyBehaviourRout'][0] + 0x88) if isinstance(C.rt.by_name['ZHeliFlyBehaviourRout'], list) else C.e.u32(C.rt.by_name['ZHeliFlyBehaviourRout'] + 0x88)
    ins = C.dis(0x4ebed0, 0x60)
    t = ' | '.join('%s %s' % (m, o) for _a, m, o in ins)
    n_block, n_trig = C.registered(0x168d800), C.registered(0x168d804)
    shape = (re.search(r'cmp dx, word ptr \[0x168d800\].*mov byte ptr \[esi \+ 0x41\], 1', t) and
             re.search(r'cmp dx, word ptr \[0x168d804\].*cmp byte ptr \[esi \+ 0x41\], 0', t) and
             re.search(r'mov edx, dword ptr \[eax \+ 0x88\].*call edx.*mov byte ptr \[esi \+ 0x40\], 1', t))
    if n_block == 'AIBlocker' and n_trig == 'AITrigger' and shape:
        line('PASS', '0x4ebed0 rout handler', 'AITrigger: if not blocked ([rout+0x41]==0) calls the rout\'s start (vtable +0x88; ZHeliFlyBehaviourRout = %#x) and sets '
             '[rout+0x40]=1; AIBlocker sets [rout+0x41]=1 (a rout that was blocked never starts)' % start)
    else:
        line('FAIL', '0x4ebed0 rout handler', 'AITrigger %r AIBlocker %r shape %s' % (n_trig, n_block, bool(shape)))
        ok = False
    line('NOTE', 'G1 (guess)', 'same-name message objects are taken to carry the same id (registry 0xdd6728); the id assignment (0x5329b0) was not read')
    return ok


# ---------------------------------------------------------------------------------------------------------- the data
def find_zip(arg):
    if arg and os.path.isfile(arg):
        return arg
    if arg and os.path.isdir(arg):
        hit = sorted(glob.glob(os.path.join(arg, '**', '*_Main.zip'), recursive=True))
        return hit[0] if hit else None
    return None


def default_build():
    try:
        import kl_prpjoin as J
        base = J.find(J.DM_GUESSES, J.DM_EXE)
        z = os.path.join(base, 'KL_PortTools', 'build', 'club_heli_1017', 'DM05A', 'heli')
        return find_zip(z)
    except Exception:
        return None


def load(zpath, game):
    import kl_prpjoin as J, kl_gms, kl_scene
    sc = J.Scene.from_zip(zpath, game)
    with zipfile.ZipFile(zpath) as zf:
        prp = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
        raw = kl_gms.unpack(zf.read(prp[:-4] + '.gms'))
        buf = zf.read(prp[:-4] + '.buf')
        hvk = [n for n in zf.namelist() if n.lower().endswith('.hvk')]
        hv = zf.read(hvk[0]) if hvk else None
    ks = kl_scene.Scene(raw, buf)
    ents = list(ks.entities())
    return sc, ents, hv


def groups(sc):
    import kl_fa
    return kl_fa.controllers(sc, 'OnlineEscHavokCar')


def ctrl_names(sc, k):
    return [sc.p.key(n) for n, _ in sc.nodes[k]['ctrls']]


def target(sc, ref):
    if not isinstance(ref, str) or not ref:
        return None
    ix = sc.index.get(ref.lower())
    return ix[0] if ix else None


def data_side(zpath, game, tag, expect_flow=True):
    """The wiring of one level's OnlineEscHavokCar groups. Returns the list of (group node, summary dict)."""
    import kl_fa
    sc, ents, _hv = load(zpath, game)
    res = []
    for k, i, vals in groups(sc):
        f = [vals[j] if j < len(vals) else None for j in range(4)]
        t = [target(sc, x) for x in f]
        d = dict(group=k, path=sc.path[k], cls=sc.cls(k), fields=f, tnodes=t,
                 inc_ctrls=ctrl_names(sc, t[0]) if t[0] else None,
                 esc_ctrls=ctrl_names(sc, t[1]) if t[1] else None,
                 hidden_prop=kl_fa.node_values(sc, k)[3], hidden_flag=bool(ents[k - 1].flags & HIDDEN),
                 kids=[sc.cls(c) for c in range(k + 1, sc.end[k]) if sc.parent[c] == k])
        res.append(d)
    return sc, ents, res


def wiring(zpath):
    import kl_fa, kl_prpjoin as J
    sc, ents, res = data_side(zpath, 'dd', 'build')
    L = os.path.basename(zpath)
    if not res:
        line('NOTE', 'build', '%s has no OnlineEscHavokCar group' % L)
        return None
    ok = True
    mine = [d for d in res if d['path'].startswith(HELI)]
    if len(mine) != 1:
        line('NOTE', 'build', '%s: %d chopper group(s) under %s (all groups: %s)' % (L, len(mine), HELI, [d['path'] for d in res]))
        return None
    d = mine[0]
    k = d['group']
    # the four fields
    f0 = d['inc_ctrls'] or []
    if d['cls'] == 'ZGROUP' and 'HeliFlyBehaviourRout' in f0 and 'MsgForward' in f0:
        line('PASS', 'field 0 (Incomming)', '%s is a rout group with HeliFlyBehaviourRout + MsgForward: AITrigger from the handler lands on a fly rout' % d['fields'][0])
    else:
        line('FAIL', 'field 0 (Incomming)', 'target %r controllers %s' % (d['fields'][0], f0))
        ok = False
    f1 = d['esc_ctrls'] or []
    if 'HeliFlyBehaviourRout' in f1:
        line('PASS', 'field 1 (Escaping)', '%s has a HeliFlyBehaviourRout (the flight out; started by the vehicle state machine, not by this call)' % d['fields'][1])
    else:
        line('FAIL', 'field 1 (Escaping)', 'target %r controllers %s' % (d['fields'][1], f1))
        ok = False
    # rout details: the Incomming rout names its spline as a child and a ForceNoLoop target
    inc = d['tnodes'][0]
    kids = [sc.cls(c) for c in range(inc + 1, sc.end[inc]) if sc.parent[c] == inc]
    if 'ZEditorSpline' in kids:
        line('PASS', 'Incomming spline', 'child ZEditorSpline present (%s)' % sc.path[inc])
    else:
        line('FAIL', 'Incomming spline', 'children %s' % kids)
        ok = False
    # MsgForward target
    for n, b in sc.nodes[inc]['ctrls']:
        if sc.p.key(n) == 'MsgForward':
            v = [kl_fa.value(sc, u) for u in kl_fa.units(b[1:-1])]
            tg = target(sc, v[0])
            if tg and 'ZHeliNetSync' in [sc.p.key(x) for x, _ in sc.nodes[tg]['ctrls']] + [sc.cls(tg)]:
                line('PASS', 'MsgForward target', '%s (ZHeliNetSync: net copy of the flight)' % v[0])
            else:
                line('NOTE', 'MsgForward target', '%r -> node %s %s %s' % (v[0], tg, sc.cls(tg) if tg else None, ctrl_names(sc, tg) if tg else None))
    # OnMap
    om = d['tnodes'][3]
    if om:
        line('PASS', 'field 3 (OnMap)', '%s exists (%s): receives Show' % (d['fields'][3], sc.cls(om)))
    else:
        line('FAIL', 'field 3 (OnMap)', 'target %r not found' % d['fields'][3])
        ok = False
    # hidden convention
    if d['hidden_prop'] == 1 and d['hidden_flag']:
        line('PASS', 'hidden at start', 'group ZGEOM[3]=1 and .gms flag 0x400: hidden until a ZActivateGeom (the club\'s van-on timer)')
    elif d['hidden_prop'] == 1 or d['hidden_flag']:
        line('FAIL', 'hidden at start', 'ZGEOM[3]=%r but .gms flag 0x400=%s: the two disagree' % (d['hidden_prop'], d['hidden_flag']))
        ok = False
    else:
        line('NOTE', 'hidden at start', 'group is NOT hidden at start (ZGEOM[3]=%r flag=%s)' % (d['hidden_prop'], d['hidden_flag']))
    # exit trigger -> the group
    ex = kl_fa.controllers(sc, 'OnlineExitLevelTrigger')
    named = [(kk, sc.path[kk]) for kk, _i, v in ex if len(v) > 2 and isinstance(v[2], str) and v[2].lower() == sc.path[k].lower()]
    if len(ex) >= 1 and len(named) == len(ex):
        line('PASS', 'exit trigger target', '%d OnlineExitLevelTrigger(s) name the chopper group: %s' % (len(ex), [p for _k, p in named]))
    else:
        line('FAIL', 'exit trigger target', '%d trigger(s), %d name %s' % (len(ex), len(named), sc.path[k]))
        ok = False
    # AllyEscapeBox
    ab = kl_fa.controllers(sc, 'AllyEscapeBox')
    line('PASS' if ab else 'NOTE', 'AllyEscapeBox', '%d box(es): %s' % (len(ab), [sc.path[x[0]] for x in ab]))
    # the unhide wire: an ActivateGeom that names the group, itself named by a timer (the club's 'van on', F07's TearGas_LEFT)
    def flat(x):
        if isinstance(x, (list, tuple)):
            for y in x:
                yield from flat(y)
        else:
            yield x
    gp = sc.path[k].lower()
    act = [kk for kk in range(1, len(sc.nodes)) for n, b in sc.nodes[kk]['ctrls'] if sc.p.key(n) == 'ActivateGeom'
           and any(isinstance(y, str) and y.lower() == gp for y in flat([kl_fa.value(sc, u) for u in kl_fa.units(b[1:-1])]))]
    fed = [(sc.path[kk], sc.p.key(n), v[0]) for a_ in act for kk in range(1, len(sc.nodes)) for n, b in sc.nodes[kk]['ctrls']
           for v in [[kl_fa.value(sc, u) for u in kl_fa.units(b[1:-1])]]
           if any(isinstance(y, str) and y.lower() == sc.path[a_].lower() for y in flat(v))]
    hidden = d['hidden_prop'] == 1 or d['hidden_flag']
    if not hidden:
        line('NOTE', 'unhide wire', 'group is not hidden at start, so it needs no unhide wire (%d ActivateGeom name it)' % len(act))
    elif act and fed:
        line('PASS', 'unhide wire', 'ActivateGeom %s shows the group; sent by %s (delay s: %s). The call itself does NOT unhide (Show goes to OnMap)' % (
            [sc.path[x] for x in act], [f[0].split('!')[-1] + ':' + f[1] for f in fed], [f[2] for f in fed]))
    else:
        line('FAIL', 'unhide wire', 'group is hidden but %d ActivateGeom name it and %d sender(s) name those: the chopper never appears' % (len(act), len(fed)))
        ok = False
    # schema misfits of the chopper subtree
    bad = [(kk, w, why) for kk, w, why in J.misfits(sc) if k <= kk < sc.end[k] or kk in (d['tnodes'][0], d['tnodes'][1], d['tnodes'][3])]
    if bad:
        line('FAIL', 'kl_rtp misfits', '%d in the chopper groups, e.g. %s' % (len(bad), bad[:2]))
        ok = False
    else:
        line('PASS', 'kl_rtp misfits', '0 misfits in the %d nodes of the chopper group (and its three targets)' % (sc.end[k] - k))
    return ok


def stock_compare():
    """The same wiring in the stock levels that use a chopper (F02, F03, F06, F08 in Dog Days; M06_FA_A in Dead Men).
    Dog Days' own levels point field 0 at a RandomTrigger (+ MsgForward) that picks one of several Incoming_X rout groups; Dead Men's M06 (and the club)
    point it straight at the rout group. Both end in a HeliFlyBehaviourRout, which takes AITrigger itself (0x4ebed0), so the shapes are equivalent."""
    import kl_prpjoin as J, kl_fa
    rows, hid = [], {}
    for lv, game in (('F02', 'dd'), ('F03', 'dd'), ('F06', 'dd'), ('F08', 'dd'), ('M06_FA_A', 'dm')):
        try:
            z = J.level_zip(lv, game)
            sc, ents, res = data_side(z, game, lv)
        except Exception as x:
            line('NOTE', 'stock ' + lv, 'unreadable: %r' % (x,))
            continue
        for d in res:
            if not (d['kids'] and 'ZHeli' in d['kids']):
                continue
            f0 = d['inc_ctrls'] or []
            rows.append((lv, d['path'], 'rout' if 'HeliFlyBehaviourRout' in f0 else 'RandomTrigger' if 'RandomTrigger' in f0 else '?', 'MsgForward' in f0))
        # ZGEOM[3] against the .gms hidden flag over every ZGROUP
        for k in range(1, len(sc.nodes)):
            if sc.cls(k) == 'ZGROUP':
                key = (kl_fa.node_values(sc, k)[3], bool(ents[k - 1].flags & HIDDEN))
                hid[key] = hid.get(key, 0) + 1
    for r in rows:
        line('NOTE', 'stock chopper', '%s %s: field 0 = %s, MsgForward %s' % r)
    if rows and all(r[2] in ('rout', 'RandomTrigger') for r in rows):
        line('PASS', 'stock structure', '%d stock chopper group(s) (%s): field 0 is a rout group or a RandomTrigger chain (which ends in HeliFlyBehaviourRout groups)' % (
            len(rows), ', '.join(sorted({r[0] for r in rows}))))
    else:
        line('NOTE', 'stock structure', 'unexpected field 0 shapes: %s' % rows)
    line('NOTE', 'stock hidden', 'ZGROUP (ZGEOM[3], flag 0x400) counts over the five stock levels: %s' % sorted(hid.items()))
    if hid.get((1, False), 0) == 0 and hid.get((1, True), 0) > 0:
        line('PASS', 'ZGEOM[3]=1 is hidden', '%d groups with ZGEOM[3]=1, all of them have .gms flag 0x400, none without' % hid[(1, True)])
    else:
        line('FAIL', 'ZGEOM[3]=1 is hidden', 'counts %s' % sorted(hid.items()))


def hvk_compare(zpath):
    """Where the key-framed placement of the ZHeli sits: stock M06 / F03 / F06 (all at the origin?) against the build."""
    import kl_hvk
    out = []
    for lv, game, z in [(l, g, None) for l, g in (('M06_FA_A', 'dm'), ('F03', 'dd'), ('F06', 'dd'))] + [('build', 'dd', zpath)]:
        try:
            import kl_prpjoin as J
            zz = z or J.level_zip(lv, game)
            sc, ents, res = data_side(zz, game, lv)
            _s, _e, hv = load(zz, game)
            mine = [d for d in res if d['kids'] and 'ZHeli' in d['kids']]
            if not mine or hv is None:
                line('NOTE', 'hvk ' + lv, 'no chopper group or no .HVK')
                continue
            k = mine[0]['group']
            refs = {ents[j - 1].ref for j in range(k, sc.end[k])}
            h = kl_hvk.Hvk(hv)
            pos = []
            for s in h.shapes:
                if s.type == kl_hvk.STATIC:
                    continue
                for inst in s.inst:
                    if kl_hvk.ref(inst) in refs:
                        pos.append((s.type,) + tuple(round(x) for x in struct.unpack_from('<3f', inst, 0)))
            out.append((lv, pos))
            line('NOTE', 'hvk ' + lv, 'non-static placements of the chopper group\'s REFs (type, x, y, z in m): %s' % pos)
        except Exception as x:
            line('NOTE', 'hvk ' + lv, 'unreadable: %r' % (x,))
    return out


def exe_flight(C):
    """Flight start (2026-10-17): 0x80dcd0 -> 0x791090, link 0x4aff50, init 0x815aa0. Shape checks on the disassembly; returns False on FAIL."""
    ok = True
    def txt(a, n):
        return ' | '.join('%s %s' % (m, o) for _a, m, o in C.dis(a, n))
    for what, a, n, need in [
        ('0x80dcd0 start', 0x80dcd0, 0x30, [r'mov eax, dword ptr \[ecx \+ 0x74\]', r'call 0x791090']),
        ('0x791090 deliver', 0x791090, 0x200, [r'dword ptr \[edi \+ 0x38\]', r'call 0x81b1f0', r'call 0x48c0f0', r'call 0x7f6750']),
        ('0x815aa0 init', 0x815aa0, 0x400, [r'0x1535878', r'0x168ce48', r'call 0x469910']),
        ('0x4aff50 squad link', 0x4aff50, 0x300, [r'call 0x598460'])]:
        t = txt(a, n)
        miss = [rx for rx in need if not re.search(rx, t)]
        if miss:
            ok = False
            line('FAIL', what, 'not as read: ' + '; '.join(miss))
        else:
            line('PASS', what, 'shape as read')
    # adversarial pass (2026-10-17): the early-outs the first reading left out, and what the goal object really is
    t = txt(0x791090, 0x200)
    for rx, msg in [(r'cmp byte ptr \[eax \+ 0xbc\], 0', '0x791110: exits when [actor+0xbc] != 0 (one-shot flag, set at 0x791138 when [rout+0x43])'),
                    (r'cmp dword ptr \[eax \+ 0x8c\], 0', '0x7910c1: with 0x81b1f0 true and [actor+0x8c]==0 a goal whose class name != ZVehicleSpecialMoveBehaviour is dropped')]:
        if re.search(rx, t):
            line('NOTE', 'extra early-out', msg)
        else:
            ok = False
            line('FAIL', 'extra early-out', 'not as read: ' + msg)
    t = txt(0x7f6750, 0x100)
    if re.search(r'cmp dword ptr \[esi \+ 0x8c\], 0', t) and re.search(r'mov dword ptr \[esi \+ 0x154\], edi', t) and re.search(r'je 0x7f682a', t):
        line('NOTE', 'extra early-out', '0x7f6750 stores [actor+0x154]=goal only if [actor+0x8c] or [actor+0x90] is set OR goal vfunc +0x34 is true (else je 0x7f682a returns)')
    else:
        ok = False
        line('FAIL', 'add-goal shape', '0x7f6750 not as read')
    vt = 0xbcd65c
    nm = C.rt.by_vtable.get(vt)
    s24, s34, s1c = C.e.u32(vt + 0x24), C.e.u32(vt + 0x34), C.e.u32(vt + 0x1c)
    stub = txt(s24, 4) if s24 else ''
    if nm and 'ZHeliFlyBehaviour' in str(nm) and s24 == s34 and 'xor al, al' in stub:
        line('PASS', 'goal class', 'the goal built by 0x469910 is %s (vtable %#x), NOT ZHeliFlyGoal; its vfuncs +0x24/+0x34 return false, so 0x7f6750 relies on [actor+0x8c]/[actor+0x90]' % (nm, vt))
    else:
        ok = False
        line('FAIL', 'goal class', 'vtable %#x is %r, slots %s %s' % (vt, nm, s24, s34))
    t = txt(0x74a940, 0x60)
    if 'call 0x78d6e0' in t and '0xbd17ac' in t:
        line('NOTE', 'ZHeliFlyGoal', 'ZHeliFlyGoal (vtable 0xbd183c) is built by 0x78d6e0 inside the controller ctor 0x74a940 (vtable 0xbd17ac, kept at ZHeli+0x7bc, goal at +0x8c): a member of the heli, not the goal of the rout')
    else:
        ok = False
        line('FAIL', 'ZHeliFlyGoal', '0x74a940 not as read')
    return ok


def flight_data(zpath):
    """Per build: the inputs the flight start reads (squad controller on the parent, spline child, ZHeli with HeliScriptRout, target refs)."""
    import kl_fa
    sc, ents, res = data_side(zpath, 'dd', 'build')
    mine = [d for d in res if d['path'].startswith(HELI)]
    if len(mine) != 1:
        line('UNKNOWN', 'flight data', 'no single chopper group')
        return
    d = mine[0]
    k = d['group']
    par = sc.parent[k]
    pc = ctrl_names(sc, par)
    line('PASS' if 'ZSquadScript' in pc else 'FAIL', 'squad on parent', '%s controllers %s (0x4aff50 needs ZSquadScript/ZMercSquad/ZFusionSquad/ZProxySquad)' % (sc.path[par], pc))
    for lbl, i in (('Incomming', 0), ('Escaping', 1)):
        t = d['tnodes'][i]
        if not t:
            line('FAIL', lbl, 'field %d does not resolve' % i)
            continue
        kids = [sc.cls(c) for c in range(t + 1, sc.end[t]) if sc.parent[c] == t]
        spl = [c for c in kids if 'Spline' in str(c)]
        rc = [n for n in ctrl_names(sc, t) if 'HeliFly' in n]
        line('PASS' if (spl and rc) else 'FAIL', lbl + ' rout group', 'spline child %s, rout %s (0x815aa0 returns with no goal without the spline child)' % (spl, rc))
        if rc:
            try:
                import struct as _st
                v = [vv for n, vv in sc.nodes[t]['ctrls'] if sc.p.key(n) == 'HeliFlyBehaviourRout'][0]
                ints = [_st.unpack('<i', b)[0] for ty, b in v if ty == 4]
                fl = [_st.unpack('<f', b)[0] for ty, b in v if ty == 10]
                line('NOTE', lbl + ' values', 'floats (speed, ...) %s, ints (two EHeliFacingMode-like enums, 0=FACE_SPLINE, 1=FACE_SPLINE_90DEG_CW) %s; stock DD incoming routs are (0,1) mostly, (1,1) in F02/F06 too' % (fl, ints))
                spl = [c for c in range(t + 1, sc.end[t]) if sc.parent[c] == t and 'Spline' in str(sc.cls(c))]
                if spl and (ents[spl[0] - 1].flags & HIDDEN):
                    line('FAIL', lbl + ' spline flag', '0x815aa0 skips children whose [+0x3c] bit 10 is set: the spline carries 0x400')
            except Exception:
                pass
    heli = [c for c in range(par + 1, sc.end[par]) if str(sc.cls(c)) == 'ZHeli']
    hs = [c for c in heli if 'HeliScriptRout' in ctrl_names(sc, c)]
    if heli and any(ents[c - 1].flags & HIDDEN for c in heli):
        line('FAIL', 'ZHeli flag', '0x815b96 skips a ZHeli whose [+0x3c] bit 10 is set: it carries 0x400')
    line('PASS' if hs else 'FAIL', 'ZHeli under parent', 'ZHeli nodes %s, with HeliScriptRout %s (0x815aa0 needs the HeliScript object)' % (heli, hs))
    line('UNKNOWN', 'motion mechanism', 'how ZHeli control state (+0x7d0..0x86c) becomes body motion: not located')
    line('UNKNOWN', 'HVK start pose', 'consumer of the type-3 placement list (wrapper+0x14c4) not located')


def main():
    t0 = time.time()
    arg = sys.argv[sys.argv.index('--build') + 1] if '--build' in sys.argv else None
    C = Code()
    ok_exe = exe_side(C)
    ok_exe = exe_flight(C) and ok_exe
    zpath = find_zip(arg) if arg else default_build()
    if arg and not zpath:
        line('FAIL', 'build', 'no *_Main.zip under %s' % arg)
    ok_data = None
    if zpath:
        print('build: %s' % zpath, flush=True)
        try:
            ok_data = wiring(zpath)
        except Exception as x:
            line('FAIL', 'build wiring', 'unreadable: %r' % (x,))
        try:
            flight_data(zpath)
        except Exception as x:
            line('NOTE', 'flight data', 'failed: %r' % (x,))
        try:
            stock_compare()
        except Exception as x:
            line('NOTE', 'stock', 'compare failed: %r' % (x,))
        try:
            hvk_compare(zpath)
        except Exception as x:
            line('NOTE', 'hvk', 'compare failed: %r' % (x,))
    else:
        line('NOTE', 'build', 'no heli build found: only the exe side was proven')
    line('NOTE', 'still unknown', 'what ZHeliFlyBehaviourRout start (%s) does after AITrigger (goal object at [rout+0x74], 0x791090) was followed to the goal hand-over (see exe_flight) but not to the first body movement; '
         'a live run is the proof (log lines "hud: van card ON ... picture 171", "van 1+")' % '0x80dcd0')
    print('elapsed %.1f s' % (time.time() - t0))
    if fails:
        print('RESULT: FAIL ' + fails[0])
    elif not ok_exe:
        print('RESULT: FAIL exe side')
    elif ok_data is None:
        print('RESULT: UNKNOWN')
    else:
        print('RESULT: PASS')


if __name__ == '__main__':
    main()
