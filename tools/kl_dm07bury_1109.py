"""kl_dm07bury_1109.py - DM07 van gate, variant "BURY": the two gate fence panels get their COLLISION back and lose their LOOK by moving only the render place down.

Background: tools/kl_vehroutes_dm07_1108.py opens the escape-van gate by HIDING (gms flag 0x400, flags 0x201e6 -> 0x205e6) the chain-link panels
SO0301_USA_Chainlink_Fence_4m_01 (REF 21457) and _4m_11 (REF 21449), x -4611..-4545, z 9993..10795. PROVEN live (benches 2026-11-09): 0x400 removes PLAYER
collision too, so players walk out west into the van pocket; a KillBox curtain proved inert. This variant:
  * both panels: flags 0x205e6 -> 0x201e6 (collision back, proven to block when un-hidden),
  * both panels: RENDER place y -= 500 cm (471.456 -> -28.544): .prp ZGEOM[2] (what the Dog Days loader reads) and the .gms translation (the same value, kept in step),
    so the panel (a ~2.4 m fence) lies wholly under the mud (388..460 cm) and is not seen,
  * the .HVK is NOT touched (asserted byte-identical): the static collision placement (y 4.715 m = 471.5 cm) stays where it was.
GUESS (the bench decides): the runtime static body keeps the HVK placement when the entity's place moves. Static evidence in re/havok.md: the type 1 (static)
handler 0x4de4b0 -> 0x4acd90 builds a WORLD-SPACE hkMeshShape from the placement alone (vertices already transformed) and appends it to the static list; only
types 2 and 4 look up `entity = table[REF-1]` and take/give a matrix. Against it: the hide flag DOES remove static collision at runtime, so some entity -> static
link exists (by REF; how is not decoded), and if that link also re-syncs the transform at load, the collision sinks with the render and the variant fails.
GUESS: a buried panel can still be drawn (the .oct room lists keep the slot; nothing here moves the model's culling box), which would only show the fence through the mud.
GUESS: x/z are not changed so the REF-keyed surface table / gates stay valid.

What changes per zip (each patched from its OWN members; the .gms unpacked must equal across both zips, as kl_dm07unhide_1109):
  .gms  4 bytes of flags word x2 (one byte each: 0x05 -> 0x01) + the translation y float of each panel (up to 4 bytes x2)
  .prp  the ZGEOM[2] y float of each panel (up to 4 bytes x2)
  every other member (.HVK, .prm, .buf, .oct ...) byte-identical. F06_Main.bots.base.md5 = md5 of the new plain zip.

    python tools/kl_dm07bury_1109.py stage [<live DM07 dir>] [<out dir>]     (defaults: <DD>/KLExpansion/Maps/DM07, C:/kl_build_1024/dm07bury_1109)
    python tools/kl_dm07bury_1109.py check <zip>                             both panels: flags, render y (.gms + .prp), HVK placement y
    python tools/kl_dm07bury_1109_test.py                                    off-game self-test (skips without the pinned live zip)
"""
import os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm07sink_1109 as S

LIVE_DIR = S.LIVE_DIR
OUT = 'C:/kl_build_1024/dm07bury_1109'
SLOT = 'F06'
LIVE_MD5 = S.LIVE_MD5
TAG = '.before-dm07bury1109'
ZIPS = ('F06_Main.zip', 'F06_Main.bots.zip')
HIDE = 0x400
OLD_FLAGS, NEW_FLAGS = 0x205e6, 0x201e6
DROP = 500.0                                         # cm, render only
PANELS = {'SO0301_USA_Chainlink_Fence_4m_01': 21457, 'SO0301_USA_Chainlink_Fence_4m_11': 21449}   # name -> REF (= HVK static placement label)
md5 = S.md5


def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]


def find(B):
    """{name: node k} of the two panels; exactly one entity per name, REF as pinned, hidden (flags OLD_FLAGS), identity parent frame, no kids."""
    sc, out = B.sc, {}
    for name, ref in PANELS.items():
        hit = [k for k in range(1, len(B.ents) + 1) if sc.names[k] == name]
        if len(hit) != 1:
            raise ValueError('want exactly 1 entity named %s, found %d' % (name, len(hit)))
        k = hit[0]
        e = B.ents[k - 1]
        if e.ref != ref:
            raise ValueError('%s: REF %d, want %d' % (name, e.ref, ref))
        if e.flags != OLD_FLAGS:
            raise ValueError('%s: flags %#x, want %#x (the live hidden gate); already buried or another pass?' % (name, e.flags, OLD_FLAGS))
        q = sc.parent[k]
        Rm, T = B.fr[B.ents[q - 1]] if q else (None, None)
        if q and (any(abs(Rm[i][j] - (i == j)) > 1e-6 for i in range(3) for j in range(3)) or any(abs(t) > 1e-6 for t in T)):
            raise ValueError('%s: parent frame is not the identity (a local y would not be the world y)' % name)
        if e.kids:
            raise ValueError('%s has children' % name)
        out[name] = k
    return out


def bury(B, log=print):
    """Edit the Built scene B in memory -> (new .prp bytes, new unpacked .gms bytes, report). Asserts the byte diffs are only the intended words."""
    import kl_gms, kl_prpjoin as J
    import kl_loot_1025 as LO
    sc = B.sc
    ks = find(B)
    prp0, gms0 = B.files[B.ext['.prp']], bytes(kl_gms.unpack(B.files[B.ext['.gms']]))
    if sc.p.serialize() != prp0:
        raise ValueError('the .prp does not round-trip through the schema (stop: nothing was written)')
    if B.scene.write()[0] != gms0:
        raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
    ents = list(kl_gms.entities(gms0))
    gms = bytearray(gms0)
    rep, tr_offsets = {}, {}
    # translation blocks are shared between entities only when their bytes are equal: refuse if a panel's block is pointed at by another record
    ptr = {}
    for i in range(len(ents)):
        rec = 4 * (ents[i][0] & 0xffffff)
        ptr.setdefault(struct.unpack_from('<I', gms0, rec + 8)[0], []).append(i)
    for name, k in ks.items():
        e = B.ents[k - 1]
        rec = 4 * (ents[k - 1][0] & 0xffffff)
        if struct.unpack_from('<I', gms0, rec + 28)[0] != OLD_FLAGS:
            raise ValueError('%s: flags word is not at gms record +28' % name)
        tro = struct.unpack_from('<I', gms0, rec + 8)[0]
        if ptr[tro] != [k - 1]:
            raise ValueError('%s: its translation block is shared with entities %s' % (name, [i for i in ptr[tro] if i != k - 1]))
        old = struct.unpack_from('<3f', gms0, tro)
        if tuple(struct.unpack_from('<3f', e.trans)) != old:
            raise ValueError('%s: scene translation differs from the .gms block' % name)
        new_y = f32(old[1] - DROP)
        struct.pack_into('<I', gms, rec + 28, NEW_FLAGS)
        struct.pack_into('<f', gms, tro + 4, new_y)
        # .prp: ZGEOM[2] must equal the .gms translation (the loader reads the .prp), else refuse
        v = B.values(k)['ZGEOM[2]']
        if tuple(f32(x) for x in v) != old:
            raise ValueError('%s: .prp ZGEOM[2] %s differs from the .gms translation %s' % (name, v, old))
        lab = J.labels('dd', sc.cls(k))
        newpos = [old[0], new_y, old[2]]

        def fn(us, lab=lab, newpos=newpos):
            LO.AU.setv(sc, us, lab.index('ZGEOM[2]'), newpos)
        LO.kl_graft.edit(sc.nodes[k], 'props', fn)
        rep[name] = dict(node=k, ref=e.ref, rec=rec, tr=tro, old=list(old), new=newpos)
        tr_offsets[name] = (rec + 28, tro + 4)
    gms = bytes(gms)
    prp = sc.p.serialize()
    # byte diffs: gms = 2 flag bytes + 2 floats' bytes, prp = only inside the 2 floats
    dg = [i for i in range(len(gms0)) if gms0[i] != gms[i]]
    if len(gms) != len(gms0):
        raise ValueError('.gms length changed')
    ok_g = set()
    for fo, yo in tr_offsets.values():
        ok_g.update(range(fo, fo + 4)); ok_g.update(range(yo, yo + 4))
    if not dg or not set(dg) <= ok_g:
        raise ValueError('.gms byte diff outside the intended words: %s' % dg[:12])
    dp = [i for i in range(len(prp0)) if prp0[i] != prp[i]] if len(prp) == len(prp0) else None
    if dp is None:
        raise ValueError('.prp length changed (%d -> %d): a float was not rewritten in place' % (len(prp0), len(prp)))
    clusters = []
    for i in dp:
        if clusters and i - clusters[-1][-1] <= 3:
            clusters[-1].append(i)
        else:
            clusters.append([i])
    if not dp or len(clusters) > 2 or any(c[-1] - c[0] > 3 for c in clusters):
        raise ValueError('.prp byte diff is not <= 2 float words: %s' % dp[:12])
    rep['_gms_diff'], rep['_prp_diff'] = dg, dp
    # re-read check on the in-memory result: the .gms must still parse as a scene (translation dedup unaffected) and re-write byte-exact
    import kl_scene
    sc2 = kl_scene.Scene(gms, B.files[B.ext['.buf']])
    if sc2.write()[0] != gms:
        raise ValueError('patched .gms does not round-trip through kl_scene')
    for name, k in ks.items():
        e2 = list(sc2.entities())[k - 1]
        if e2.flags != NEW_FLAGS or abs(struct.unpack_from('<3f', e2.trans)[1] - rep[name]['new'][1]) > 0:
            raise ValueError('%s: re-read scene does not carry the new flags / y' % name)
    log('  gms bytes differing %d %s; prp bytes differing %d %s' % (len(dg), dg, len(dp), dp))
    for name in ks:
        r = rep[name]
        log('  %s node %d REF %d: flags %#x -> %#x, render y %.3f -> %.3f (x %.3f, z %.3f kept)' % (name[-5:], r['node'], r['ref'], OLD_FLAGS, NEW_FLAGS, r['old'][1], r['new'][1], r['old'][0], r['old'][2]))
    return prp, gms, rep


def build_zip(src, dst, log=print):
    import kl_gms
    import kl_fa_bots as KB
    import kl_loot_1025 as LO
    B = KB.Built(src, SLOT)
    prp, gms, rep = bury(B, log)
    repl = {B.ext['.prp']: prp, B.ext['.gms']: kl_gms.pack(gms)}
    LO.patch_zip(src, dst, {n: b for n, b in repl.items() if b != B.files[n]})
    A = KB.Built(dst, SLOT)
    bad = []
    for n in B.files:
        if n not in repl and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if A.order != B.order:
        bad.append('member order changed')
    hv = next(n for n in B.files if n.lower().endswith('_main.hvk'))
    if A.files[hv] != B.files[hv]:
        bad.append('HVK changed')
    if bytes(kl_gms.unpack(A.files[A.ext['.gms']])) != gms:
        bad.append('re-read .gms differs from the intended bytes')
    if A.sc.p.serialize() != prp or A.files[A.ext['.prp']] != prp:
        bad.append('re-read .prp differs from the intended bytes')
    for name in PANELS:
        k = next(k for k in range(1, len(A.ents) + 1) if A.sc.names[k] == name)
        if A.ents[k - 1].flags != NEW_FLAGS or abs(A.values(k)['ZGEOM[2]'][1] - rep[name]['new'][1]) > 0:
            bad.append('%s: re-read flags / ZGEOM[2] wrong' % name)
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep['gms_raw'] = gms
    return rep


def stage(live_dir=LIVE_DIR, out=OUT, log=print):
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))
    os.makedirs(out, exist_ok=True)
    gms_ref = None
    for n in ZIPS:
        src, dst = os.path.join(live_dir, n), os.path.join(out, n)
        log('== %s' % n)
        rep = build_zip(src, dst, log)
        if gms_ref is None:
            gms_ref = rep['gms_raw']
        elif rep['gms_raw'] != gms_ref:
            raise ValueError('%s: patched unpacked .gms differs from the plain zip\'s: refusing' % n)
        with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
            ca = {i.filename: i.CRC for i in a.infolist()}
            diff = [i.filename for i in b.infolist() if i.CRC != ca[i.filename]]
        log('    CRC-differing members: %s (of %d); .HVK byte-identical (asserted)' % (diff, len(ca)))
        if not all(m.lower().endswith(('.prp', '.gms')) for m in diff):
            raise ValueError('CRC diff outside .prp/.gms: %s' % diff)
    with open(os.path.join(out, 'F06_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(os.path.join(out, 'F06_Main.zip')) + '\n')
    files = []
    for n in ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5'):
        files.append((n, LIVE_MD5[n], md5(os.path.join(out, n))))
        log('  %-24s %s -> %s' % files[-1])
    write_kit(out, files)
    return files


def kit_text(files):
    t = S.INSTALL_TEMPLATE.replace('.before-dm07sink1109', TAG).replace('DM07 SINK 1109 (tools/kl_dm07sink_1109.py)', 'DM07 BURY 1109 (tools/kl_dm07bury_1109.py)')
    t = t.replace('Static fence-line slabs sunk to the mud (collision only).', 'Gate fence panels: collision back (unhidden), render buried 5 m (.prp + .gms).')
    t = t.replace('@LIVEZIP@', repr(LIVE_MD5['F06_Main.zip'])).replace('@FILES@', '\n'.join('    (%r, %r, %r),' % f for f in files))
    assert 'sink' not in t.lower(), 'template still mentions sink'
    return t


def write_kit(out, files):
    nl, cr = chr(10), chr(13)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(kit_text(files))
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 bury 1109.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


def check(zp):
    """Both panels: flags, render y in the .gms and in the .prp, the HVK placement y + collision bottom (unchanged by this variant). -> True if buried."""
    import kl_fa_bots as KB, kl_hvk
    B = KB.Built(zp, SLOT)
    sc, ok = B.sc, True
    with zipfile.ZipFile(zp) as z:
        raw = z.read(S.hvk_member(z))
    h = kl_hvk.Hvk(raw)
    if h.serialize() != raw:
        raise ValueError('HVK does not round-trip byte-exact')
    place = {}
    for s in h.shapes:
        if s.type != kl_hvk.STATIC:
            continue
        for inst in s.inst:
            r = kl_hvk.ref(inst)
            if r in PANELS.values():
                lowv = min(struct.unpack_from('<3f', s.verts, j * s.vstride)[1] for j in range(len(s.verts) // s.vstride))
                y = struct.unpack_from('<f', inst, 4)[0]
                place[r] = (y, y + lowv)
    for name, ref in PANELS.items():
        k = next(k for k in range(1, len(B.ents) + 1) if sc.names[k] == name)
        e = B.ents[k - 1]
        gy, py = struct.unpack_from('<3f', e.trans)[1], B.values(k)['ZGEOM[2]'][1]
        hy, hb = place[ref]
        state = ('HIDDEN' if e.flags & HIDE else 'collides') + (', BURIED' if gy < 0 and abs(gy - py) < 1e-6 else (', render y differs gms/prp' if abs(gy - py) > 1e-6 else ', render at stock height'))
        print('%s REF %d flags %#x (%s) | render y: .gms %.3f cm, .prp %.3f cm | HVK placement y %.4f m, collision bottom %.4f m' % (name, ref, e.flags, state, gy, py, hy, hb))
        ok = ok and e.flags == NEW_FLAGS and gy < 0 and abs(gy - py) < 1e-6
    print('RESULT: %s' % ('both panels buried (collision flag back, render y < 0, HVK as shipped)' if ok else 'NOT the bury zip (stock zip or other)'))
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage']:
        stage(*(a[1:3]))
    elif a[:1] == ['check'] and len(a) == 2:
        check(a[1])
    else:
        print(__doc__)
