r"""kl_dm02doorglass_1110.py - DM02 (Late Night Opening, slot F02): the jeweller shop-front DOORS and the vault GLASS. 2026-11-10. OFFLINE: reads the live
DM02 zips, writes a stage; nothing is installed, the game is not started.  (Own name: kl_dm02shop_1110.py is the other agent's shutter-prompt pass.)

OWNER (2026-11-10, playing): "i already said fix the door already and i want the glass back just make the ai heisters shoot it open".
Screenshot: the Hertzer & Sons jewellers front at the round start with a plain grey door leaf standing in the doorway.

WHICH DOOR (MEASURED on the live zip, report in build_report.json 'world'):
  The jewellers is M02_FA_A_Ins_StoreJewel_201a. Its two fronts carry the KICK DOOR leaves KL_Interact!1\KL_Door_3 \Door (REF 34449) and KL_Door_4 \Door
  (REF 34472): model 0xe404 = Metal_F03_Door_01a, the plain white/grey F03 slab (kl_dm02door_1108 docstring). They were ADDED by the kick-door graft
  (kl_interact_graft / kl_doors); the dm02door_1108 pass only re-skinned D1, D2 and D5 with the Dead Men glass pane, so 3, 4 and 6 stayed grey. Dead Men
  has no door there. The same graft put the leaves D1 / D2 (REF 34403 / 34426, glass-pane model) INTO the two vault glass doorways where Dead Men's own glass
  door SI0401_M02_FA_Door_Shatter_Glass_01!Whole04 (REF 23182 / 24258) stands: a doubled door. kl_dm02fix_1108 part vault hid both Whole04 (flag 0x400)
  AND cut their static collision out of the .HVK. This pass undoes that.

WHAT CHANGES (no entity added or removed: every slot id, .oct/.rmi/.rmc/.prm/.MAT/.TEX/.buf byte for byte):
 glass  (variant shop, default)
   1. the two Whole04 REFs lose the 0x400 hide flag (.gms record +28), back to the pre-dm02fix flags 0x2201e6 (checked against F02_Main.zip.before-dm02fix1108);
   2. their static type-1 HVK placements come back at the SAME static positions with the pre-dm02fix shape record and MOPP code, cut out of the filler run
      dm02fix left there: static count, order, list codes and every other record unchanged;
   3. a RelayMessageList {'AITrigger' -> 'ForceTriggerShotActivate', [itself], 0.0} on each Whole04 and a TriggerDelay2 (--glass-delay s) on KLShops_OpenTimer
      naming both: the glass breaks BY ITSELF that many seconds after the round start with the stock shatter. That is the data-only stand-in for "the heisters
      shoot it open": Dog Days bots shoot at nothing (re/bots.md 12.1); the hook (klhook/klbotglass_logic.h, [BotGlass], NOT built) is the real thing.
 doors  (both variants)
   4. a TriggerDelay2 (--door-delay s) on KLShops_OpenTimer names, per door D1..D4, KickDoor_Pathblocker_01 ('eUnblock' accepts the TriggerDelay2 activation)
      and KickableDoor_Proxy_Variation01Front_A_01 (MatPosAnimProxy frames 0..25 = the kick-open swing); the Audio_PlaySound controller of that proxy is taken
      off so no kick is heard at the round start;
   5. D1 / D2 leaves also get 0x400 (hidden): the glass door stands there again.

CHAIN: input = the live F02_Main.zip 43c088c2 (dm02fix -> dm02door -> dm02coop timer). The other agent's shutter-prompt pass (kl_dm02shop_1110.py) edits the same
zip: install whichever comes first, then re-stage the other (this tool: change the pins at the top, or `stage --live`). install.py refuses a non-pinned live zip.
This pass touches only Whole04 x2, their 2 HVK statics, KLShops_OpenTimer (2 TriggerDelay2 appended AFTER the existing ones), the D1..D4 proxies and 4 flag words.

usage (from tools/):
  python kl_dm02doorglass_1110.py build --variant shop|doors [--glass-delay 20] [--door-delay 1.5] --out <dir> [--live <F02_Main.zip>]
  python kl_dm02doorglass_1110.py stage [--out C:\kl_build_1024\dm02shop_1110\door] [--live <Maps\DM02>]    both variants + install.py / UNDO bat / README
  python kl_dm02doorglass_1110.py check <zip> [--live <F02_Main.zip>] [--variant shop]
"""
import collections, hashlib, json, math, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_hvk, kl_mopp
import kl_fa_bots as F
import kl_botsonline
import kl_dm02fix_1108 as FIX
import kl_dm02coop_1109 as COOP

MAPDIR = FIX.MAPDIR
OUT = r'C:\kl_build_1024\dm02shop_1110\door'
TAG = '.before-dm02door1110'
PRE_FIX = os.path.join(MAPDIR, 'F02_Main.zip.before-dm02fix1108')      # the zip before the vault cut (READ only)
LIVE_PIN = '43c088c2d0ac4131a2f8d6a1667f965a'
LIVE_BOTS_PIN = 'bb8f04cb6b8460b5f34df021da629c9f'
LIVE_BASE_PIN = '43c088c2d0ac4131a2f8d6a1667f965a'
GLASS = FIX.GLASS_DOORS                                  # {23182: hinge (x, z), 24258: ...}
GLASS_FLAGS = 0x2201e6                                   # the intact Whole04 (pre-fix); live = | 0x400
HIDE = 0x400
DOOR_REFS = {1: 34403, 2: 34426, 3: 34449, 4: 34472, 5: 34495, 6: 34518}
DEFAULT_OPEN = (1, 2, 3, 4)
DEFAULT_HIDE = (1, 2)
DEFAULT_GLASS_DELAY = 20.0
DEFAULT_DOOR_DELAY = 1.5
VARIANTS = ('shop', 'doors')
DEFAULT_VARIANT = 'shop'
FORCE_MSG = 'ForceTriggerShotActivate'                    # ShotActivate field 10 (MEASURED on every Whole04 in this map)
TIMER = 'KLShops_OpenTimer'

GUESSES = [
    "a TriggerDelay2 on KLShops_OpenTimer reaches a RelayMessageList controller on the glass node and the relay's out-message ForceTriggerShotActivate (the "
    "name stored in ShotActivate field 10 of that very node) shatters it like a bullet would; the stock bot relay uses 'Activate' on HavokShatterGlass nodes instead (re/bots.md 12.1)",
    "the shatter takes the static type-1 collision of the Whole04 away (the engine's shatter path 0x79bd10 handles list children); all other glass pairs of this map rely on it, "
    "but a Whole04 with its collision restored has never run here: if the broken door still blocks, the bench shows it and UNDO / the doors variant is the answer",
    "the forwarded message of KLShops_OpenTimer's TriggerDelay2 is accepted by PathBlocker ('eUnblock') and by MatPosAnimProxy as for the shutters (kl_dm02coop_1109)",
    "an opened KL leaf stays in its open pose (as every kicked door of the map does) and its type-4 body follows the node out of the doorway",
    "a bot that reaches an already opened door still plays its KickDoorBehaviour leg and replays frames 0..25 (the door may snap shut and swing open once)",
    "D1 / D2 leaf hidden with 0x400 renders nothing but its kick prompt box may still show: only the leaf entity is hidden",
]


def md5(p):
    return FIX.md5(p)


def _load(zp):
    return F.Built(zp, 'F02')


def static_view(h):
    """[(ref, shape record, placement bytes, mopp entry)] in STATIC order (what the list codes address)."""
    out = []
    for s in h.shapes:
        if s.type != kl_hvk.STATIC:
            continue
        rec = (s.flags, s.convex, s.vstride, s.verts, s.planes if s.convex else s.idx, tuple(s.sub))
        for i, m in zip(s.inst, s.mopp):
            out.append((kl_hvk.ref(i), rec, bytes(i), m))
    return out


def _static_index(h):
    return [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst))]


def part_hvk(live_files, B, pre_zip, rep):
    """Restore the two glass statics from the pre-dm02fix HVK. -> new HVK bytes."""
    with zipfile.ZipFile(pre_zip) as z:
        pre = kl_hvk.Hvk(z.read([n for n in z.namelist() if n.lower().endswith('.hvk')][0]))
    live = kl_hvk.Hvk(live_files[B.ext['.HVK']])
    pv, lv = static_view(pre), static_view(live)
    if len(pv) != len(lv):
        raise ValueError('static count pre %d live %d' % (len(pv), len(lv)))
    fix_at = {}
    for r in GLASS:
        at = [n for n, x in enumerate(pv) if x[0] == r]
        if len(at) != 1:
            raise ValueError('REF %d is placed %d times in the pre-fix .HVK' % (r, len(at)))
        if any(x[0] == r for x in lv):
            raise ValueError('REF %d is placed in the live .HVK already (nothing to restore)' % r)
        fix_at[at[0]] = r
    rep['hvk_other_diffs_vs_prefix'] = len([n for n in range(len(pv)) if n not in fix_at and pv[n][0] != lv[n][0]])
    for n in sorted(fix_at, reverse=True):                 # back to front so the record numbers of the earlier ones hold
        si, j = _static_index(live)[n]
        s = live.shapes[si]
        psi, pj = _static_index(pre)[n]
        ps = pre.shapes[psi]
        if lv[n][0] != 20069:
            raise ValueError('static %d of the live .HVK is REF %d, not the filler 20069' % (n, lv[n][0]))
        new = []
        if j:
            new.append(s.clone(s.inst[:j], s.mopp[:j]))
        new.append(ps.clone([ps.inst[pj]], [ps.mopp[pj]]))
        if j + 1 < len(s.inst):
            new.append(s.clone(s.inst[j + 1:], s.mopp[j + 1:]))
        live.shapes[si:si + 1] = new
    data = live.serialize()
    back = kl_hvk.Hvk(data)
    bv = static_view(back)
    if back.serialize() != data or back.static_count() != pre.static_count() or len(bv) != len(lv):
        raise ValueError('.HVK read-back differs')
    for n in range(len(bv)):
        want = pv[n] if n in fix_at else lv[n]
        if bv[n] != want:
            raise ValueError('static %d is not what it should be' % n)
    rep['hvk'] = collections.OrderedDict(static=back.static_count(), restored_static_index={n: r for n, r in fix_at.items()}, bytes=(len(live_files[B.ext['.HVK']]), len(data)))
    return data


def find_nodes(B):
    sc = B.sc
    glass = {}
    for k in range(1, len(sc.names)):
        if B.ents[k - 1].ref in GLASS:
            glass[B.ents[k - 1].ref] = k
    if sorted(glass) != sorted(GLASS):
        raise ValueError('glass REFs %s not all found' % sorted(glass))
    doors = {}
    for n in DOOR_REFS:
        g = [k for k in range(1, len(sc.names)) if sc.path[k] == 'ROOT\\KL_Interact!1\\KL_Door_%d' % n]
        if len(g) != 1:
            raise ValueError('KL_Door_%d: %d nodes' % (n, len(g)))
        kids = {sc.names[j]: j for j in range(1, len(sc.names)) if sc.parent[j] == g[0]}
        leaf = kids['Door']
        if B.ents[leaf - 1].ref != DOOR_REFS[n]:
            raise ValueError('KL_Door_%d Door is REF %d, not %d' % (n, B.ents[leaf - 1].ref, DOOR_REFS[n]))
        doors[n] = dict(group=g[0], leaf=leaf, proxy=kids['KickableDoor_Proxy_Variation01Front_A_01'], pb=kids['KickDoor_Pathblocker_01'])
    timer = [k for k in range(1, len(sc.names)) if sc.names[k] == TIMER]
    if len(timer) != 1:
        raise ValueError('%s: %d nodes' % (TIMER, len(timer)))
    return glass, doors, timer[0]


def relay_template(sc):
    for k in range(1, len(sc.names)):
        for nm, body in sc.nodes[k]['ctrls']:
            if sc.p.key(nm) == 'RelayMessageList':
                v = [kl_fa.value(sc, u) for u in kl_fa.units(body[1:-1])]
                if len(v) == 4 and v[0] == 'AITrigger' and v[1] == 'Activate' and isinstance(v[2], list) and v[3] == 0.0:
                    return nm, list(body)
    raise ValueError('no RelayMessageList template')


def add_timer(sc, tk, delay, paths):
    cs = sc.nodes[tk]['ctrls']
    j = [i for i, (nm, _b) in enumerate(cs) if sc.p.key(nm) == 'TriggerDelay2']
    if not j:
        raise ValueError('%s has no TriggerDelay2' % TIMER)
    cs.append((cs[j[0]][0], list(cs[j[0]][1])))

    def ft(us):
        if len(us) != 5:
            raise ValueError('TriggerDelay2 is not 5 fields')
        us[0] = [(0x0a, struct.pack('<f', delay))]
        us[4] = kl_fa._refs(sc, paths)
    kl_fa.edit(sc, tk, len(cs) - 1, ft)


def part_prp(B, variant, glass_delay, door_delay, open_doors, hide_doors, rep):
    sc = B.sc
    glass, doors, tk = find_nodes(B)
    n0 = len(sc.nodes[tk]['ctrls'])
    if variant == 'shop':
        rt = relay_template(sc)
        for r, k in sorted(glass.items()):
            names = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
            if names != ['ShotActivate']:
                raise ValueError('glass %d controllers %s' % (r, names))
            sc.nodes[k]['ctrls'].append((rt[0], list(rt[1])))

            def fr(us, k=k):
                if len(us) != 4:
                    raise ValueError('RelayMessageList is not 4 fields')
                us[1] = [kl_fa._str(sc, FORCE_MSG)]
                us[2] = kl_fa._refs(sc, [sc.path[k]])
            kl_fa.edit(sc, k, len(sc.nodes[k]['ctrls']) - 1, fr)
        add_timer(sc, tk, glass_delay, [sc.path[glass[r]] for r in sorted(glass)])
    if open_doors:
        tg = []
        for n in open_doors:
            d = doors[n]
            tg += [sc.path[d['pb']], sc.path[d['proxy']]]
            cs = sc.nodes[d['proxy']]['ctrls']
            keep = [(nm, b) for nm, b in cs if sc.p.key(nm) != 'Audio_PlaySound']
            if [sc.p.key(nm) for nm, _b in keep] != ['MatPosAnimProxy']:
                raise ValueError('D%d proxy controllers %s' % (n, [sc.p.key(nm) for nm, _b in cs]))
            sc.nodes[d['proxy']]['ctrls'] = keep
        add_timer(sc, tk, door_delay, tg)
    rep['prp'] = collections.OrderedDict(
        glass=sorted(glass) if variant == 'shop' else [], glass_delay=glass_delay if variant == 'shop' else None,
        doors_opened=list(open_doors), door_delay=door_delay if open_doors else None, doors_hidden=list(hide_doors),
        timer_ctrls=(n0, len(sc.nodes[tk]['ctrls'])))
    prp = sc.p.serialize()
    if F.Prp(prp).serialize() != prp:
        raise ValueError('the patched .prp does not round-trip')
    return prp, glass, doors


def part_gms(B, variant, glass, doors, hide_doors, pre_zip, rep):
    raw = bytearray(kl_gms.unpack(B['.gms']))
    ents = list(kl_gms.entities(bytes(raw)))
    changed = []

    def setflags(k, fn, want_old):
        e = B.ents[k - 1]
        rec = 4 * (ents[k - 1][0] & 0xffffff)
        cur = struct.unpack_from('<I', raw, rec + 28)[0]
        if cur != e.flags or (want_old is not None and cur != want_old):
            raise ValueError('node %d flags %#x (entity %#x, expected %s)' % (k, cur, e.flags, want_old))
        struct.pack_into('<I', raw, rec + 28, fn(cur))
        changed.append((e.ref, hex(cur), hex(fn(cur))))
    if variant == 'shop':
        pre = _load(pre_zip)
        for r, k in sorted(glass.items()):
            pe = [e for e in pre.ents if e.ref == r]
            if len(pe) != 1 or pe[0].flags != GLASS_FLAGS:
                raise ValueError('pre-fix Whole04 %d flags' % r)
            setflags(k, lambda f: f & ~HIDE, GLASS_FLAGS | HIDE)
    for n in hide_doors:
        setflags(doors[n]['leaf'], lambda f: f | HIDE, None)
    rep['gms_flags'] = changed
    return kl_gms.pack(bytes(raw))


def build(live, outdir, variant=DEFAULT_VARIANT, glass_delay=DEFAULT_GLASS_DELAY, door_delay=DEFAULT_DOOR_DELAY, open_doors=DEFAULT_OPEN,
          hide_doors=DEFAULT_HIDE, pre_zip=PRE_FIX, log=print):
    if variant not in VARIANTS:
        raise ValueError('variant %s' % variant)
    B = _load(live)
    rep = collections.OrderedDict(variant=variant, live=live, live_md5=md5(live))
    prp, glass, doors = part_prp(B, variant, glass_delay, door_delay, open_doors, hide_doors, rep)
    gms = part_gms(B, variant, glass, doors, hide_doors, pre_zip, rep)
    files = dict(B.files)
    files[B.ext['.prp']], files[B.ext['.gms']] = prp, gms
    if variant == 'shop':
        files[B.ext['.HVK']] = part_hvk(B.files, B, pre_zip, rep)
    os.makedirs(outdir, exist_ok=True)
    plain = os.path.join(outdir, 'F02_Main.zip')
    kl_graft.write_zip(plain, [(n, files[n]) for n in B.order])
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        if a.namelist() != b.namelist():
            raise ValueError('member list changed')
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    want = {'F02_Main.prp', 'F02_Main.gms'} | ({'F02_Main.HVK'} if variant == 'shop' else set())
    if set(diff) != want:
        raise ValueError('members changed %s, expected %s' % (diff, sorted(want)))
    rep['members_changed'] = diff
    kl_botsonline.convert(plain, os.path.join(outdir, 'F02_Main.bots.zip'), 'eAllTypes', 'F02', log=lambda *a: None)
    with open(os.path.join(outdir, 'F02_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(plain) + '\n')
    rep['out_md5'] = md5(plain)
    rep['bots_md5'] = md5(os.path.join(outdir, 'F02_Main.bots.zip'))
    log('dm02doorglass_1110 %s -> %s (%s) members %s' % (variant, plain, rep['out_md5'], diff))
    return rep


# ---------------------------------------------------------------- checks
def check(plain, live, variant=DEFAULT_VARIANT, open_doors=DEFAULT_OPEN, hide_doors=DEFAULT_HIDE, pre_zip=PRE_FIX, log=print):
    bad = []
    A, N = _load(live), _load(plain)
    pre = _load(pre_zip)
    with zipfile.ZipFile(live) as a, zipfile.ZipFile(plain) as b:
        diff = sorted(n.rsplit('/', 1)[-1] for n in a.namelist() if a.read(n) != b.read(n))
    want = ['F02_Main.HVK', 'F02_Main.gms', 'F02_Main.prp'] if variant == 'shop' else ['F02_Main.gms', 'F02_Main.prp']
    if diff != want:
        bad.append('members changed: %s' % diff)
    for m in ('.oct', '.rmi', '.rmc', '.prm', '.MAT', '.TEX', '.buf'):
        if A[m] != N[m]:
            bad.append('%s changed' % m)
    sa, sn = A.scene.slots(), N.scene.slots()
    if [e.name for e in A.ents] != [e.name for e in N.ents] or [sa[e] for e in A.ents] != [sn[e] for e in N.ents]:
        bad.append('entity names / slot ids changed')
    glass, doors, tk = find_nodes(N)
    exp = {}
    if variant == 'shop':
        for r in GLASS:
            exp[r] = lambda f: f & ~HIDE
    for n in hide_doors:
        exp[DOOR_REFS[n]] = lambda f: f | HIDE
    for k, (a, b) in enumerate(zip(A.ents, N.ents), 1):
        same = (a.tid, a.model, a.rot, a.trans, a.aux, a.ref, a.group, a.raw) == (b.tid, b.model, b.rot, b.trans, b.aux, b.ref, b.group, b.raw)
        if not same:
            bad.append('entity %d changed beyond flags' % k)
        want_f = exp[a.ref](a.flags) if a.ref in exp else a.flags
        if b.flags != want_f:
            bad.append('entity REF %d flags %#x, want %#x' % (a.ref, b.flags, want_f))
    if variant == 'shop':
        for r in GLASS:
            pe = next(e for e in pre.ents if e.ref == r)
            ne = next(e for e in N.ents if e.ref == r)
            if pe.flags != ne.flags:
                bad.append('Whole04 %d flags %#x differ from the pre-fix %#x' % (r, ne.flags, pe.flags))
    # .prp
    ca, pa = COOP._ctrl_map(A)
    cb, pb = COOP._ctrl_map(N)
    if list(ca) != list(cb) or pa != pb:
        bad.append('node list / node properties changed')
    sc = N.sc
    chg = {p for p in ca if ca[p] != cb[p]}
    allowed = {sc.path[tk]}
    if variant == 'shop':
        allowed |= {sc.path[k] for k in glass.values()}
    allowed |= {sc.path[doors[n]['proxy']] for n in open_doors}
    if not chg <= allowed or (sc.path[tk] not in chg and (variant == 'shop' or open_doors)):
        bad.append('controllers changed on %s' % sorted(chg ^ allowed)[:4])
    ptk = sc.path[tk]
    tm_a = [c for c in ca[ptk] if c[0] == 'TriggerDelay2']
    tm_b = [c for c in cb[ptk] if c[0] == 'TriggerDelay2']
    nadd = (1 if variant == 'shop' else 0) + (1 if open_doors else 0)
    if tm_b[:len(tm_a)] != tm_a or len(tm_b) != len(tm_a) + nadd or [c for c in cb[ptk] if c[0] != 'TriggerDelay2'] != [c for c in ca[ptk] if c[0] != 'TriggerDelay2']:
        bad.append('OpenTimer: %d -> %d TriggerDelay2 (want +%d, old ones first, nothing else)' % (len(tm_a), len(tm_b), nadd))
    added = [c[1] for c in tm_b[len(tm_a):]]
    gp = sorted(sc.path[glass[r]] for r in GLASS)
    if variant == 'shop':
        if not added or added[0][0] <= 1.0 or sorted(added[0][4]) != gp:
            bad.append('glass timer: %s' % (added[:1],))
        for r, k in glass.items():
            cs = cb[sc.path[k]]
            if [c[0] for c in cs] != ['ShotActivate', 'RelayMessageList'] or cs[1][1][:2] != ['AITrigger', FORCE_MSG] or cs[1][1][2] != [sc.path[k]] or cs[1][1][3] != 0.0:
                bad.append('Whole04 %d controllers %s' % (r, [(c[0], c[1][:2]) for c in cs]))
            if cs[0] != ca[sc.path[k]][0]:
                bad.append('Whole04 %d ShotActivate changed' % r)
    if open_doors and added:
        dl = added[-1]
        want_t = []
        for n in open_doors:
            want_t += [sc.path[doors[n]['pb']], sc.path[doors[n]['proxy']]]
        if sorted(dl[4]) != sorted(want_t) or dl[0] <= 0:
            bad.append('door timer: %s' % (dl,))
        for n in open_doors:
            cs = cb[sc.path[doors[n]['proxy']]]
            old = next(c for c in ca[sc.path[doors[n]['proxy']]] if c[0] == 'MatPosAnimProxy')
            if [c[0] for c in cs] != ['MatPosAnimProxy'] or cs[0] != old:
                bad.append('D%d proxy: %s' % (n, [c[0] for c in cs]))
            if cs[0][1][1:3] != [0, 25] or cs[0][1][3] != [sc.path[doors[n]['leaf']]]:
                bad.append('D%d proxy frames / target %s' % (n, cs[0][1][:4]))
    # .HVK
    ha, hb, hp = kl_hvk.Hvk(A['.HVK']), kl_hvk.Hvk(N['.HVK']), kl_hvk.Hvk(pre['.HVK'])
    va, vb, vp = static_view(ha), static_view(hb), static_view(hp)
    if variant == 'doors':
        if A['.HVK'] != N['.HVK']:
            bad.append('hvk changed in the doors variant')
    else:
        if len(va) != len(vb) or hb.static_count() != ha.static_count() or ha.lists != hb.lists or ha.box != hb.box or ha.tail != hb.tail:
            bad.append('hvk: static count / list codes / box / tail changed')
        else:
            dif = [n for n in range(len(va)) if va[n] != vb[n]]
            gi = [n for n in range(len(vp)) if vp[n][0] in GLASS]
            if dif != gi or any(vb[n] != vp[n] for n in gi) or any(va[n][0] != 20069 for n in gi):
                bad.append('hvk: statics changed at %s, wanted exactly %s (the pre-fix glass records)' % (dif, gi))
        nonstat = lambda h: [(s.type, s.flags, tuple(bytes(i) for i in s.inst), tuple(s.mopp), s.verts) for s in h.shapes if s.type != kl_hvk.STATIC]
        if nonstat(ha) != nonstat(hb):
            bad.append('hvk: a non-static shape changed')
        if [x[0] for x in vb if x[0] not in GLASS] != [x[0] for x in va if x[0] != 20069 or True and False] and False:
            pass
        placed = lambda h: sorted(kl_hvk.ref(i) for s in h.shapes for i in s.inst if kl_hvk.ref(i) in GLASS)
        if placed(hb) != sorted(GLASS) or placed(ha):
            bad.append('hvk: glass placements live %s new %s' % (placed(ha), placed(hb)))
    mo = lambda X: [(o['node'], o['amount'], o['kind'], o['container']) for o in F.money_objects(X)]
    if mo(A) != mo(N):
        bad.append('bots: the money census changed')
    return bad


def world_report(B, glass, doors):
    """World coordinates (cm) of the touched things for the proof."""
    out = collections.OrderedDict()
    for r, k in sorted(glass.items()):
        out['Whole04 %d' % r] = [round(v, 1) for v in B.at(k)]
    for n, d in sorted(doors.items()):
        out['KL_Door_%d leaf REF %d' % (n, DOOR_REFS[n])] = [round(v, 1) for v in B.at(d['leaf'])]
    return out


# ---------------------------------------------------------------- install.py / stage
def make_install_py(staged):
    src = COOP.INSTALL_PY
    src = src.replace('DM02 CO-OP SHUTTERS 1109 (key-framed shutter bodies that open)', 'DM02 SHOP DOORS + VAULT GLASS 1110')
    src = src.replace('--variant coop|timer pick the variant (timer: opens by itself after the delay; coop: two players in the boxes / the solo Lift Door)',
                      '--variant shop|doors pick the variant (shop: glass back + breaks itself + doors open; doors: only the door part)')
    return src % dict(tag=TAG, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, staged=repr(staged), default=DEFAULT_VARIANT)


README = r'''DM02 SHOP DOORS + VAULT GLASS 1110 (Late Night Opening, slot F02)     built OFFLINE, NOT installed, NOT run in the game
=======================================================================================================================
Owner: "fix the door already and i want the glass back, just make the ai heisters shoot it open".
The door: the plain grey leaf in the Hertzer & Sons (jewellers, StoreJewel_201a) front = the KICK DOOR leaves KL_Door_3 and KL_Door_4 (model 0xe404, added by the
kick-door graft). They now swing open %(ddelay)s s after the round starts (KLShops_OpenTimer), so the front reads as an open doorway like Dead Men's.
KL_Door_1 / _2 (in the two vault glass doorways) open AND are hidden: the glass door stands there again.
The glass: the two SI0401_M02_FA_Door_Shatter_Glass_01!Whole04 (REF 23182 / 24258) are drawn again and BLOCK again (their static HVK placements are restored at the
same static positions from the pre-dm02fix zip) and shatter by themselves %(gdelay)s s after the round starts (stock shatter: Remains, sound, particles).
That is the data-only stand-in for the heisters shooting: Dog Days bots shoot at nothing (re/bots.md 12.1). The real thing is the hook design
klhook/klbotglass_logic.h + klbotglass_test.c + [BotGlass] (written, NOT built; see its header).
Variants (install.py --variant): shop (default) = doors + glass; doors = door part only (glass stays as dm02fix left it).

Install (game closed): INSTALL dm02 shop 1110.bat   or   python install.py [--variant doors] [--dry] [--game <dir> --skip-run-check]
Undo: UNDO dm02 shop 1110.bat (byte exact; BEFORE any layer installed later on DM02).   Backups: <name>%(tag)s next to the live files.
Pins: live F02_Main.zip %(live)s, bots %(bots)s, base %(base)s.
CHAIN: the shutter-prompt pass (kl_dm02shop_1110.py, stage ...\dm02shop_1110\prompt) edits the same zip. Install one, then re-stage the other on the new live md5s.
Staged: shop zip %(szip)s bots %(sbots)s | doors zip %(dzip)s bots %(dbots)s

Proven offline (kl_dm02doorglass_1110.py check + _test): only .prp / .gms / .HVK change (doors variant: .prp / .gms); every slot id and entity equal, only the flag
word of the 2 Whole04 (0x2205e6 -> 0x2201e6 = the pre-fix value) and of the D1 / D2 leaves (+0x400) differ; .HVK: static count, order, list codes, box, tail and
every other record unchanged, exactly the two glass statics are back and equal to the pre-fix records; .prp: only the two Whole04 (+RelayMessageList),
KLShops_OpenTimer (+2 TriggerDelay2, old ones first) and the D1..D4 Variation01 proxy (Audio_PlaySound off) change; bots money census unchanged.

GUESSes (the bench decides):
%(guesses)s

BENCH PLAN (owner not playing; one bench at a time, TEST dll): 0. df; install.py --dry; install. 1. SOLO DM02: shot of the jewellers front at the start (door
swings open at %(ddelay)s s). 2. walk to the vault glass doors: drawn and blocking before %(gdelay)s s, shattered after, walk through. 3. 2 seats: both see it.
4. bots: with the hook off they stop at the glass until it breaks (lower --glass-delay if so).
If the broken door still blocks: UNDO and use the doors variant.
Change delays: python tools/kl_dm02doorglass_1110.py stage --glass-delay 12 --door-delay 1
'''


def stage(live_dir, out, glass_delay=DEFAULT_GLASS_DELAY, door_delay=DEFAULT_DOOR_DELAY, log=print):
    live = os.path.join(live_dir, 'F02_Main.zip')
    bots = os.path.join(live_dir, 'F02_Main.bots.zip')
    if md5(live) != LIVE_PIN or md5(bots) != LIVE_BOTS_PIN:
        raise SystemExit('live DM02 zip / bots zip are not the pinned %s / %s (another layer changed them: re-pin on the live md5s)' % (LIVE_PIN, LIVE_BOTS_PIN))
    base = open(os.path.join(live_dir, 'F02_Main.bots.base.md5')).read().strip()
    if base != LIVE_BASE_PIN:
        raise SystemExit('live bots.base.md5 is %s, not %s' % (base, LIVE_BASE_PIN))
    os.makedirs(out, exist_ok=True)
    for n in os.listdir(out):
        p = os.path.join(out, n)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    reps, staged = {}, {}
    for v in VARIANTS:
        d = os.path.join(out, 'variant_' + v)
        reps[v] = build(live, d, v, glass_delay, door_delay, log=log)
        bad = check(os.path.join(d, 'F02_Main.zip'), live, v, log=log)
        if bad:
            raise SystemExit('check failed (%s): %s' % (v, bad))
        staged[v] = {n: md5(os.path.join(d, n)) if n != 'F02_Main.bots.base.md5' else md5(os.path.join(d, n)) for n in ('F02_Main.zip', 'F02_Main.bots.zip', 'F02_Main.bots.base.md5')}
        reps[v]['check'] = 'ok'
    B = _load(live)
    glass, doors, _tk = find_nodes(B)
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(make_install_py(staged))
    for nm, arg in (('INSTALL dm02 shop 1110', ''), ('UNDO dm02 shop 1110', ' --undo')):
        with open(os.path.join(out, nm + '.bat'), 'w', newline='\r\n') as fh:
            fh.write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    with open(os.path.join(out, 'README.txt'), 'w', newline='\n') as fh:
        fh.write(README % dict(gdelay='%.0f' % glass_delay, ddelay='%.1f' % door_delay, live=LIVE_PIN, bots=LIVE_BOTS_PIN, base=LIVE_BASE_PIN, tag=TAG,
                               szip=staged['shop']['F02_Main.zip'], sbots=staged['shop']['F02_Main.bots.zip'],
                               dzip=staged['doors']['F02_Main.zip'], dbots=staged['doors']['F02_Main.bots.zip'],
                               guesses='\n'.join(' %d. GUESS: %s' % (i + 1, g) for i, g in enumerate(GUESSES))))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(dict(reports=reps, staged=staged, world=world_report(B, glass, doors)), fh, indent=1, default=str)
    log(json.dumps(staged, indent=1))
    return reps, staged


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    live = opt('--live', os.path.join(MAPDIR, 'F02_Main.zip'))
    if a and a[0] == 'build':
        out = opt('--out', OUT)
        v = opt('--variant', DEFAULT_VARIANT)
        build(live, out, v, float(opt('--glass-delay', DEFAULT_GLASS_DELAY)), float(opt('--door-delay', DEFAULT_DOOR_DELAY)))
        bad = check(os.path.join(out, 'F02_Main.zip'), live, v)
        if bad:
            print('check failed:', *bad, sep='\n'); return 1
        return 0
    if a and a[0] == 'stage':
        stage(opt('--live', MAPDIR), opt('--out', OUT), float(opt('--glass-delay', DEFAULT_GLASS_DELAY)), float(opt('--door-delay', DEFAULT_DOOR_DELAY)))
        return 0
    if len(a) >= 2 and a[0] == 'check':
        bad = check(a[1], live, opt('--variant', DEFAULT_VARIANT))
        print('problems: %d' % len(bad), *bad, sep='\n')
        return 1 if bad else 0
    sys.exit(__doc__)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
