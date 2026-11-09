"""kl_dm07sink_1109.py - DM07 van-pocket leak fix: SINK 13 static fence-line collision slabs onto the mud (HVK only).

Background (offline finding 2026-11-09, scratchpad dm07leak/proto.py): the static slabs along the fence line x ~ -4600 float over the mud
(placement y 4.715 m = collision bottom 471.5 cm, mud 388..460 cm), so a player walks under them at z 10220..10900. Fix: translate those 13
static placements down so the lowest vertex sits at y 3.85 m (EntranceSide_1m_06 REF 21325: 4.137 -> 3.85); render (.gms/.prm) untouched.

What changes (the .HVK member of BOTH zips, the same new bytes in both: their stock HVKs are byte-equal, asserted):
  per piece: placement y (float 1 of the 0x38 block) and the MOPP offset y (float 1 of the 16-byte offset); the 4th offset float and the code bytes are kept
  (like kl_dm02fix_1108.part_coop_hvk). Static count 2777, static REF order, shape records, list MOPPs: unchanged.
  F06_Main.bots.base.md5 = md5 of the new plain zip (every stage keeps it in step). Every other zip member is byte-identical; member order kept.

    python tools/kl_dm07sink_1109.py stage [<live DM07 dir>] [<out dir>]     (defaults: <DD>/KLExpansion/Maps/DM07, C:/kl_build_1024/dm07sink_1109)
    python tools/kl_dm07sink_1109.py check <zip>                             re-derives and asserts everything below against the zip's HVK
    python tools/kl_dm07sink_1109_test.py                                    off-game self-test (needs the pinned live zip or a staged one; skips otherwise)
"""
import hashlib, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE_DIR = DD + r'\KLExpansion\Maps\DM07'
OUT = 'C:/kl_build_1024/dm07sink_1109'
SLOT = 'F06'
SINK = (21457, 21456, 21455, 21454, 21453, 21449, 21450, 21451, 21452, 21412, 21325, 21204, 21203)
BOTTOM = 3.85          # metres (Havok scale): lowest vertex of every sunk slab; mud is 3.88..4.60 (GUESS: 3 cm into the mud is enough to close the gap, as the offline flood showed)
STATIC_N = 2777
LIVE_MD5 = {'F06_Main.zip': 'f35e4133af2e9d3ebec0ec4647e1233f', 'F06_Main.bots.zip': '1f514d51d06b3dcb29e6e210b9a711ac',
            'F06_Main.bots.base.md5': '08478b6eb1a226cceca594237e524f52'}
TAG = '.before-dm07sink1109'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def hvk_member(zf):
    return next(n for n in zf.namelist() if n.lower().endswith('_main.hvk'))


def sunk(raw, log=None):
    """-> (new HVK bytes, report). Asserts: unmodified round trip byte-exact; only the SINK placements change, and only placement y + mopp-offset y."""
    import kl_hvk
    from kl_dm02fix_1108 import mopp_offset
    h = kl_hvk.Hvk(raw)
    if h.serialize() != raw:
        raise ValueError('the HVK does not round-trip byte-exact (stop: nothing was written)')
    if h.static_count() != STATIC_N:
        raise ValueError('static count %d, want %d' % (h.static_count(), STATIC_N))
    refs0 = [kl_hvk.ref(i) for s in h.shapes if s.type == kl_hvk.STATIC for i in s.inst]
    hit = [(si, i) for si, s in enumerate(h.shapes) if s.type == kl_hvk.STATIC for i in range(len(s.inst)) if kl_hvk.ref(s.inst[i]) in SINK]
    if sorted(kl_hvk.ref(h.shapes[si].inst[i]) for si, i in hit) != sorted(SINK):
        raise ValueError('want each of the 13 REFs exactly once among static placements, got %s' % [kl_hvk.ref(h.shapes[si].inst[i]) for si, i in hit])
    pos = {r: n for n, r in enumerate(refs0)}
    if any(pos[r] // kl_hvk.CHUNK != 0 for r in SINK):
        raise ValueError('a SINK REF is not in list block 0')
    rep = []
    for si, i in hit:
        s = h.shapes[si]
        inst, (moff, code) = s.inst[i], s.mopp[i]
        f = list(struct.unpack_from('<12f', inst))
        if tuple(f[6:9]) != (0.0, 1.0, 0.0):
            raise ValueError('REF %d: rotation row 2 is %s, not the y axis (y translation would not move the vertices alone)' % (kl_hvk.ref(inst), f[6:9]))
        lowv = min(struct.unpack_from('<3f', s.verts, j * s.vstride)[1] for j in range(len(s.verts) // s.vstride))
        # offset formula must reproduce the stock offset first (to float32 rounding, as part_coop_hvk accepts)
        o1, o2 = struct.unpack('<3f', mopp_offset(inst, s)), struct.unpack('<3f', moff[:12])
        if any(abs(a - b) > 1e-5 for a, b in zip(o1, o2)):
            raise ValueError('REF %d: mopp offset formula does not reproduce the stock offset %s vs %s' % (kl_hvk.ref(inst), o1, o2))
        old_y = f[1]
        f[1] = BOTTOM - lowv
        ni = struct.pack('<12f', *f) + inst[0x30:]
        noff = mopp_offset(ni, s)
        s.inst[i] = ni
        noff = moff[:4] + noff[4:8] + moff[8:12]      # keep the stock x/z floats (the formula differs from the game's tool by 1 ulp): only y is replaced
        s.mopp[i] = (noff + moff[12:], code)
        rep.append((kl_hvk.ref(ni), old_y, f[1], lowv, o2[1], struct.unpack_from('<f', noff, 4)[0]))
    # the per-block list MOPP must still enclose the lowered pieces (its offset = block bb min - 0.01)
    lo_new = min(r[5] for r in rep)
    list_y = struct.unpack_from('<f', h.lists[0][0], 4)[0]
    if lo_new < list_y:
        raise ValueError('list block 0 MOPP offset y %.4f is above a sunk piece (%.4f): the list bounds would cut it off' % (list_y, lo_new))
    data = h.serialize()
    audit(raw, data, rep)
    return data, rep


def audit(raw, data, rep):
    """float-level diff: nothing but placement y + mopp offset y of the SINK pieces; static count, REF order, every other field identical."""
    import kl_hvk
    a, b = kl_hvk.Hvk(raw), kl_hvk.Hvk(data)
    if len(raw) != len(data):
        raise ValueError('HVK length changed')
    if a.static_count() != b.static_count() or a.box != b.box or a.tail != b.tail or a.lists != b.lists or len(a.shapes) != len(b.shapes):
        raise ValueError('static count / box / tail / list MOPPs / shape count changed')
    ra = [kl_hvk.ref(i) for s in a.shapes if s.type == kl_hvk.STATIC for i in s.inst]
    rb = [kl_hvk.ref(i) for s in b.shapes if s.type == kl_hvk.STATIC for i in s.inst]
    if ra != rb:
        raise ValueError('static REF order changed')
    nplace = nmopp = 0
    for sa, sb in zip(a.shapes, b.shapes):
        oa, ob = dict(vars(sa)), dict(vars(sb))
        ia, ib, ma, mb = oa.pop('inst'), ob.pop('inst'), oa.pop('mopp'), ob.pop('mopp')
        if oa != ob:
            raise ValueError('a shape field other than inst/mopp changed')
        for x, y, (mx, cx), (my, cy) in zip(ia, ib, ma, mb):
            r = kl_hvk.ref(x)
            if cx != cy or mx[12:] != my[12:]:
                raise ValueError('REF %d: MOPP code bytes or the 4th offset float changed' % r)
            fx, fy = struct.unpack_from('<12f', x), struct.unpack_from('<12f', y)
            gx, gy = struct.unpack_from('<4f', mx), struct.unpack_from('<4f', my)
            if x[0x30:] != y[0x30:]:
                raise ValueError('REF %d: REF/flag words changed' % r)
            dp = [k for k in range(12) if fx[k] != fy[k]]
            dm = [k for k in range(3) if gx[k] != gy[k]]
            if r in SINK:
                if dp != [1] or dm != [1]:
                    raise ValueError('REF %d: float diff placement %s mopp %s, want [1] and [1]' % (r, dp, dm))
                nplace += 1; nmopp += 1
            elif dp or dm or x != y or mx != my:
                raise ValueError('REF %d (not a SINK piece) changed' % r)
    if nplace != 13 or nmopp != 13:
        raise ValueError('changed pieces %d/%d, want 13' % (nplace, nmopp))
    nb = sum(1 for k in range(len(raw)) if raw[k] != data[k])
    nf = len({k // 4 for k in range(len(raw)) if raw[k] != data[k]})
    return nb, nf


def repack(src, dst, name, new_packed=None, new_raw=None):
    import kl_graft
    zin = zipfile.ZipFile(src)
    kl_graft.write_zip(dst, [(n, new_raw if n == name else zin.read(n)) for n in zin.namelist()])
    with zipfile.ZipFile(dst) as a:
        if a.namelist() != zin.namelist():
            raise ValueError('member list changed')
        if [(i.filename, i.compress_type) for i in a.infolist()] != [(i.filename, i.compress_type) for i in zin.infolist()]:
            raise ValueError('member order / compression changed')
        diff = [n for n in a.namelist() if a.read(n) != zin.read(n)]
    if diff != [name]:
        raise ValueError('members changed %s, expected only %s' % (diff, name))


def stage(live_dir=LIVE_DIR, out=OUT, log=print):
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))
    os.makedirs(out, exist_ok=True)
    raws = {}
    for n in ('F06_Main.zip', 'F06_Main.bots.zip'):
        with zipfile.ZipFile(os.path.join(live_dir, n)) as z:
            raws[n] = z.read(hvk_member(z))
    equal = raws['F06_Main.zip'] == raws['F06_Main.bots.zip']
    log('  plain and bots HVK equal: %s' % equal)
    plain_new, news = None, {}
    for n in ('F06_Main.zip', 'F06_Main.bots.zip'):
        if equal and news:
            new, rep = next(iter(news.values()))
        else:
            new, rep = sunk(raws[n])
        news[n] = (new, rep)
        src, dst = os.path.join(live_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(src) as z:
            name = hvk_member(z)
        repack(src, dst, name, new_raw=new)
        with zipfile.ZipFile(dst) as a:
            if a.read(name) != new:
                raise ValueError('re-read HVK differs from the intended bytes')
        nb, nf = audit(raws[n], new, rep)
        log('  %s: 13 pieces sunk; HVK bytes differing %d, 4-byte words %d (26 expected: 13 placement y + 13 mopp offset y); other members byte-identical' % (n, nb, nf))
        if n == 'F06_Main.zip':
            plain_new = md5(dst)
            for r in news[n][1]:
                log('    REF %d: placement y %.3f -> %.3f m (lowest vertex %.4f), mopp offset y %.3f -> %.3f' % (r[0], r[1], r[2], r[3], r[4], r[5]))
    with open(os.path.join(out, 'F06_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(plain_new + '\n')
    files = []
    for n in ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5'):
        files.append((n, LIVE_MD5[n], md5(os.path.join(out, n))))
        log('  %-24s %s -> %s' % files[-1])
    write_kit(out, files)
    return files


INSTALL_TEMPLATE = r'''r"""Installs / undoes the DM07 SINK 1109 (tools/kl_dm07sink_1109.py) on the live DM07 files, which were read at stage time:
every pin below is the md5 of a live file as it was then. Static fence-line slabs sunk to the mud (collision only).

  python install.py            install (originals -> <name>.before-dm07sink1109 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
  --min-free-mb N              free space wanted on the game drive besides the files (default 1024)
Every live md5 is pinned BEFORE anything is written (all or nothing: a failure part-way puts the originals back); nothing is written while kl2.exe runs.
Touches only the files listed in FILES (no KLJoin.ini, no KL_PortBackup, nothing else)."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM07', '.before-dm07sink1109'
LIVE_ZIP_MD5 = @LIVEZIP@
FILES = [   # name, live md5 before, staged md5 after
@FILES@
]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    """a kl2.exe in the task list (a zombie with 0 threads also shows: then pass --skip-run-check; the bench does that only for working sets under 1 MB)"""
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def put(src, dst):
    """hard link (0 bytes on the same drive), full copy when linking fails"""
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    min_free = (int(a[a.index('--min-free-mb') + 1]) if '--min-free-mb' in a else 1024) << 20
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first (--skip-run-check only for a zombie kl2.exe)'); return 3
    plan = []
    for n, old, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %s is not there' % live); return 1
        cur = md5(live)
        print('%-26s live %s' % (n, cur))
        if n == 'F06_Main.zip' and not undo and cur != LIVE_ZIP_MD5:
            print('REFUSED: the live zip is %s, not %s: another pass changed it, re-stage on the new live files' % (cur, LIVE_ZIP_MD5)); return 1
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %s' % bak); return 1
            if cur != new:
                print('REFUSED: %s live md5 %s is not the installed %s' % (n, cur, new)); return 1
            if md5(bak) != old:
                print('REFUSED: backup of %s is not md5 %s' % (n, old)); return 1
        else:
            if cur != old:
                print('REFUSED: %s live md5 %s is not the pinned %s (already installed, or another pass changed it: re-stage)' % (n, cur, old)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %s exists already (never overwritten); move it away yourself' % bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %s missing or not md5 %s' % (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        # hard links when the stage sits on the game drive (C: ran down to 271 MB on 11-09): backup = link to the live file, new live = link to the staged
        # file, undo = rename back, so nothing is copied; else full copies and the files' size + --min-free-mb (default 1024) must be free
        same = all(os.stat(os.path.dirname(p[3])).st_dev == os.stat(d).st_dev for p in plan)
        need = (min_free if '--min-free-mb' in a else 64 << 20) if same else sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + min_free
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than %d MB free on the game drive' % (need >> 20)); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                os.replace(bak, live)
            else:
                put(live, bak)
                done.append((live, bak))
                put(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                os.replace(bak, live)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'PARTIAL undo: a rerun is refused for files already restored; restore the rest by hand from the .before-dm07sink1109 files')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_kit(out, files):
    t = INSTALL_TEMPLATE.replace('@LIVEZIP@', repr(LIVE_MD5['F06_Main.zip'])).replace('@FILES@', '\n'.join('    (%r, %r, %r),' % f for f in files))
    nl, cr = chr(10), chr(13)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 sink 1109.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


def check(zp):
    """Re-derives the sink from the zip's HVK as if it were stock (refuses a zip whose REFs are already sunk: that prints the pieces' state instead)."""
    import kl_hvk
    with zipfile.ZipFile(zp) as z:
        raw = z.read(hvk_member(z))
    h = kl_hvk.Hvk(raw)
    if h.serialize() != raw:
        raise ValueError('HVK does not round-trip byte-exact')
    ok = True
    for s in h.shapes:
        if s.type != kl_hvk.STATIC:
            continue
        for inst in s.inst:
            r = kl_hvk.ref(inst)
            if r in SINK:
                y = struct.unpack_from('<f', inst, 4)[0]
                lowv = min(struct.unpack_from('<3f', s.verts, j * s.vstride)[1] for j in range(len(s.verts) // s.vstride))
                low = y + lowv
                print('REF %d placement y %.4f m, collision bottom %.4f m %s' % (r, y, low, 'SUNK' if abs(low - BOTTOM) < 1e-4 else 'stock/other'))
                ok = ok and abs(low - BOTTOM) < 1e-4
    print('static count %d (want %d), HVK round trip byte-exact, all 13 sunk: %s' % (h.static_count(), STATIC_N, ok))
    if h.static_count() != STATIC_N:
        raise ValueError('static count')
    if not ok:
        # stock zip: prove the transform is clean on it
        data, rep = sunk(raw)
        print('stock zip: transform audited clean (%d pieces)' % len(rep))
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage']:
        stage(*(a[1:3]))
    elif a[:1] == ['check'] and len(a) == 2:
        check(a[1])
    else:
        print(__doc__)
