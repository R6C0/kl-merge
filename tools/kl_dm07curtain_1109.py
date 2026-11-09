"""kl_dm07curtain_1109.py - DM07 van-pocket leak fix: a KillBox 'curtain' just west of the gate (.prp + .gms of the map, no entity added).

Cause (bench logs 2026-11-09): the gate fence panels Chainlink_Fence_4m_01 (z 9993..10393) and 4m_11 (z 10395..10795), x -4611..-4545, carry the .gms hide
flag 0x400, which REMOVES their collision; players walk through into the van pocket (x < -4600). Fix: the DM11B recipe of kl_arcade_fix_1026.killbox
(donor_kill): one inert top-level ZBoxPrimitive (DM07 has no inert *NoCover*: CameraOutside_01_SLF is used) with no controller (nothing names it, no .oct room lists it) is moved/resized and given
the stock F08 KillBox controller (CheckInsideEnter + FA_DieFromSelf). Nothing is added or renumbered.
Box (cm): x -4720..-4560, y 300..1100, z 9990..10800  -> centre (-4640, 700, 10395), half (80, 400, 405).
GUESS: a KillBox ignores a vehicle but kills an actor inside; the van driver may die while driving through the gate -> the bench decides.
GUESS: as in the recipe, ZSTDOBJ[1] is set to 0 (the stock KillBox value; leftover boxes carry 1).
Members changed per zip: only .prp and .gms (and .buf if its bytes differ), each patched from that zip's OWN members (CRC compare printed).
F06_Main.bots.base.md5 = md5 of the new plain zip (as kl_dm07sink_1109).

    python tools/kl_dm07curtain_1109.py stage [<live DM07 dir>] [<out dir>]
    python tools/kl_dm07curtain_1109.py check <zip>
"""
import os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_dm07sink_1109 as S

LIVE_DIR = S.LIVE_DIR
OUT = 'C:/kl_build_1024/dm07curtain_1109'
SLOT = 'F06'
LIVE_MD5 = S.LIVE_MD5
TAG = '.before-dm07curtain1109'
BOX_MIN, BOX_MAX = (-4720.0, 300.0, 9990.0), (-4560.0, 1100.0, 10800.0)
CENTRE = tuple((a + b) / 2 for a, b in zip(BOX_MIN, BOX_MAX))
HALF = tuple((b - a) / 2 for a, b in zip(BOX_MIN, BOX_MAX))
ZIPS = ('F06_Main.zip', 'F06_Main.bots.zip')
md5 = S.md5


def curtain(B, log=print):
    """Turn one inert *NoCover* ZBoxPrimitive of the Built scene B into the curtain KillBox. -> report dict."""
    import kl_fa, kl_prpjoin as J
    import kl_fa_bots as KB
    import kl_loot_1025 as LO
    import kl_arcade_fix_1026 as AF
    sc = B.sc
    if [1 for k, _i, _v in kl_fa.controllers(sc, 'KillBox') if sc.parent[k] == 0]:
        raise ValueError('the map has a top-level KillBox already')   # DM07 stock: only the van's own child KillBox (V_Van_00\KillBox, parent != 0)
    named = set()
    for _kk, _h, _f, _s, g in KB.J.references(sc):
        named.update(g or ())
    # DM07 has NO inert '*NoCover*' box: all 25 NoCoverBox nodes still carry their controller (the cover pass never ran on this map). The only inert
    # ZBoxPrimitives (no controller, named by no reference, 1 node, in no .oct room) are 6; the two top-level ones, ROOT\Specials!Audio!EscSoundHandling!
    # CameraOutside_01_SLF / _02_SLF (parked far outside the map at ~ (16589, 3200, 15636)), are used (01 first). GUESS: they are dead leftovers (no
    # reference names them); the other 4 are camera / explosion-FX children and are left alone.
    cands = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZBoxPrimitive' and sc.parent[k] == 0 and not sc.nodes[k]['ctrls']
             and k not in named and sc.end[k] == k + 1 and 'cameraoutside' in sc.path[k].lower()]
    cands = [k for k in cands if k not in LO.listed_in_oct(B, [k])]
    ident3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))

    def frame_ok(k):
        q = sc.parent[k]
        if q == 0:
            return True
        Rm = B.fr[B.ents[q - 1]][0]
        return all(abs(Rm[i][j] - ident3[i][j]) < 1e-6 for i in range(3) for j in range(3))
    cands = [k for k in cands if frame_ok(k)]    # GUESS: a parent rotated off identity would need the local rotation solved; skip those (the world box stays axis-aligned)
    if not cands:
        raise ValueError('no inert box to use as the KillBox')
    k = cands[0]
    q = sc.parent[k]
    loc = tuple(float(x) for x in (B.local(q, CENTRE) if q else CENTRE))
    lab = J.labels('dd', sc.cls(k))
    ident = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

    def fn(us):
        LO.AU.setv(sc, us, lab.index('ZGEOM[1]'), ident)
        LO.AU.setv(sc, us, lab.index('ZGEOM[2]'), list(loc))
        for i, v in enumerate(HALF):
            LO.AU.setv(sc, us, lab.index('ZBoxPrimitive[%d]' % i), float(v))
        LO.AU.setv(sc, us, lab.index('ZSTDOBJ[1]'), 0)
    LO.kl_graft.edit(sc.nodes[k], 'props', fn)
    e = B.ents[k - 1]
    e.rot = struct.pack('<9f', *ident) + bytes(12)
    e.trans = struct.pack('<3f', *loc) + bytes(4)
    nm, body, src = AF.donor_kill()
    sc.nodes[k]['ctrls'].append((AF.remap(nm, src, sc), [AF.remap(t, src, sc) for t in body]))
    log('  curtain: node %d (%s) -> world centre (%.0f, %.0f, %.0f), local %s, half (%.0f, %.0f, %.0f)' % (k, sc.path[k], *CENTRE, [round(v, 1) for v in loc], *HALF))
    return dict(node=k, name=sc.names[k], path=sc.path[k], local=list(loc), parent=q, centre=list(CENTRE), half=list(HALF), spare_boxes=len(cands) - 1)


def build_zip(src, dst, log=print):
    import kl_gms
    import kl_fa_bots as KB
    import kl_loot_1025 as LO
    B = KB.Built(src, SLOT)
    rep = curtain(B, log)
    prp = B.sc.p.serialize()
    gms, buf = B.scene.write()
    new = {B.ext['.prp']: prp, B.ext['.gms']: kl_gms.pack(gms), B.ext['.buf']: buf}
    repl = {n: b for n, b in new.items() if b != B.files[n]}
    LO.patch_zip(src, dst, repl)
    A = KB.Built(dst, SLOT)
    bad = []
    for n in A.files:
        if n not in repl and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if A.files[B.ext['.prm']] != B.files[B.ext['.prm']]:
        bad.append('.prm changed')
    if A.sc.names != B.sc.names or len(A.sc.nodes) != len(B.sc.nodes):
        bad.append('node list changed')
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep['members_changed'] = sorted(repl)
    return rep


def crc_compare(src, dst, log=print):
    with zipfile.ZipFile(src) as a, zipfile.ZipFile(dst) as b:
        if [i.filename for i in a.infolist()] != [i.filename for i in b.infolist()]:
            raise ValueError('member list / order changed')
        ca = {i.filename: i.CRC for i in a.infolist()}
        diff = [i.filename for i in b.infolist() if i.CRC != ca[i.filename]]
    log('    CRC-differing members: %s (of %d)' % (diff, len(ca)))
    return diff


def stage(live_dir=LIVE_DIR, out=OUT, log=print):
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))
    os.makedirs(out, exist_ok=True)
    reps = {}
    for n in ZIPS:
        src, dst = os.path.join(live_dir, n), os.path.join(out, n)
        log('== %s' % n)
        reps[n] = build_zip(src, dst, log)
        diff = crc_compare(src, dst, log)
        if sorted(diff) != reps[n]['members_changed'] or not all(m.lower().endswith(('.prp', '.gms', '.buf')) for m in diff):
            raise ValueError('CRC diff %s != intended %s' % (diff, reps[n]['members_changed']))
    with open(os.path.join(out, 'F06_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(md5(os.path.join(out, 'F06_Main.zip')) + '\n')
    files = []
    for n in ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5'):
        files.append((n, LIVE_MD5[n], md5(os.path.join(out, n))))
        log('  %-24s %s -> %s' % files[-1])
    write_kit(out, files)
    return files


def write_kit(out, files):
    t = S.INSTALL_TEMPLATE.replace('.before-dm07sink1109', TAG).replace('DM07 SINK 1109 (tools/kl_dm07sink_1109.py)', 'DM07 CURTAIN 1109 (tools/kl_dm07curtain_1109.py)')
    t = t.replace('Static fence-line slabs sunk to the mud (collision only).', 'KillBox curtain west of the gate (.prp + .gms).')
    t = t.replace('@LIVEZIP@', repr(LIVE_MD5['F06_Main.zip'])).replace('@FILES@', '\n'.join('    (%r, %r, %r),' % f for f in files))
    assert 'sink' not in t.lower(), 'template still mentions sink'
    nl, cr = chr(10), chr(13)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 curtain 1109.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


def check(zp):
    """Report the donor box (name, world box, controller) and prove by a schema round trip that re-serialising changes nothing. -> True if the curtain is there."""
    import kl_fa
    import kl_fa_bots as KB
    B = KB.Built(zp, SLOT)
    sc = B.sc
    ks = [x for x in kl_fa.controllers(sc, 'KillBox') if sc.parent[x[0]] == 0]     # the van's own child KillBox is not the curtain
    print('top-level KillBox controllers: %d' % len(ks))
    ok = len(ks) == 1
    for k, i, _v in ks:
        print('  node %d %s class %s ctrl #%d: %s' % (k, sc.path[k], sc.cls(k), i, sc.nodes[k]['ctrls'][i][0]))
        t = struct.unpack_from('<3f', B.ents[k - 1].trans)
        print('  .gms place %s (want %s), half %s' % ([round(v, 1) for v in t], list(CENTRE), list(HALF)))
        ok = ok and all(abs(a - b) < 1e-3 for a, b in zip(t, CENTRE))
    rt = sc.p.serialize() == B.files[B.ext['.prp']]
    print('prp schema round trip byte-exact: %s' % rt)
    ok = ok and rt
    print('RESULT: %s' % ('curtain present and clean' if ok else 'NOT the curtain zip (stock zip or other)'))
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage']:
        stage(*(a[1:3]))
    elif a[:1] == ['check'] and len(a) == 2:
        check(a[1])
    else:
        print(__doc__)
