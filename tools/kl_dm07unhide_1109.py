"""kl_dm07unhide_1109.py - TOGGLE TEST for the DM07 van pocket leak: stage the LIVE DM07 with the fence panel 4m_01 UN-hidden (gms flag 0x400 cleared).

Background: tools/kl_vehroutes_dm07_1108.py hid two chain-link panels (SO0301_USA_Chainlink_Fence_4m_01 and _4m_11, flags 0x201e6 -> 0x205e6, HIDE = 0x400)
so the van can drive through the gate. Bench DM07GATE_1109 run 1: a live player walks through the hidden 4m_01 at floor height while the visible 4m_02 blocks.
Static reading says 0x400 is render-only and the collision (HVK) is intact, floating 58-70 cm over the mud under 4m_01. This stage decides it:
4m_01 back to 0x201e6, nothing else changed (4m_11 stays hidden). If the same crossing now BLOCKS, the hide flag removes player collision at runtime.

What changes (a TEST build, never meant to stay installed - the van needs the gate open):
  F06_Main.zip       only the .gms member: ONE 4-byte flags word of ONE record (0x205e6 -> 0x201e6).
  F06_Main.bots.zip  GUESS-free but a deviation from "plain zip only": the ONLINE bench plays the bots zip (klslot.c: gate ON loads <slot>_Main.bots.zip,
                     the plain zip only with the gate OFF), so the same word is cleared there too (its .gms must equal the plain zip's .gms byte for byte, else refuse).
  F06_Main.bots.base.md5  = md5 of the new plain zip (the file the bots zip was derived from; every stage keeps it in step).
  KLJoin.ini and everything else: untouched.

    python tools/kl_dm07unhide_1109.py stage [<live DM07 dir>] [<out dir>]     (defaults: <DD>/KLExpansion/Maps/DM07, C:/kl_build_1024/dm07unhide_1109)
    python tools/kl_dm07unhide_1109.py check <zip>                             prints flags of the two panels
"""
import hashlib, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE_DIR = DD + r'\KLExpansion\Maps\DM07'
OUT = 'C:/kl_build_1024/dm07unhide_1109'
SLOT = 'F06'
HIDE = 0x400
TARGET = 'SO0301_USA_Chainlink_Fence_4m_01'
KEEP_HIDDEN = 'SO0301_USA_Chainlink_Fence_4m_11'
OLD_FLAGS = 0x205e6
LIVE_MD5 = {'F06_Main.zip': 'f35e4133af2e9d3ebec0ec4647e1233f', 'F06_Main.bots.zip': '1f514d51d06b3dcb29e6e210b9a711ac',
            'F06_Main.bots.base.md5': '08478b6eb1a226cceca594237e524f52'}
TAG = '.before-dm07unhide1109'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def gms_member(zf):
    return next(n for n in zf.namelist() if n.lower().endswith('_main.gms'))


def locate(src):
    """-> (gms member name, unpacked raw bytes, record offset of TARGET, flags of TARGET and KEEP_HIDDEN). Refuses unless the .gms round-trips through kl_scene,
    exactly one entity is named TARGET and its flags are OLD_FLAGS (the flags word is at gms record +28, as kl_vehroutes_dm07_1108 checked)."""
    import kl_fa_bots as F, kl_gms
    B = F.Built(src, SLOT)
    sc = B.sc
    zf = zipfile.ZipFile(src)
    name = gms_member(zf)
    raw = kl_gms.unpack(zf.read(name))
    if B.scene.write()[0] != bytes(raw):
        raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
    ents = list(kl_gms.entities(bytes(raw)))
    hit = [k for k in range(1, len(B.ents) + 1) if sc.names[k] == TARGET]
    if len(hit) != 1:
        raise ValueError('want exactly 1 entity named %s, found %d' % (TARGET, len(hit)))
    other = [k for k in range(1, len(B.ents) + 1) if sc.names[k] == KEEP_HIDDEN]
    if len(other) != 1:
        raise ValueError('want exactly 1 entity named %s, found %d' % (KEEP_HIDDEN, len(other)))
    k = hit[0]
    e = B.ents[k - 1]
    rec = 4 * (ents[k - 1][0] & 0xffffff)
    word = struct.unpack_from('<I', raw, rec + 28)[0]
    if word != e.flags:
        raise ValueError('flags word of %s is not at record +28' % TARGET)
    if word != OLD_FLAGS:
        raise ValueError('%s flags are %#x, want %#x' % (TARGET, word, OLD_FLAGS))
    ok = B.ents[other[0] - 1].flags
    if not ok & HIDE:
        raise ValueError('%s is not hidden (flags %#x): not the live gate' % (KEEP_HIDDEN, ok))
    return name, bytes(raw), rec, (word, ok)


def patched(raw, rec):
    out = bytearray(raw)
    struct.pack_into('<I', out, rec + 28, OLD_FLAGS & ~HIDE)
    return bytes(out)


def repack(src, dst, name, new_gms_packed):
    import kl_graft
    zin = zipfile.ZipFile(src)
    kl_graft.write_zip(dst, [(n, new_gms_packed if n == name else zin.read(n)) for n in zin.namelist()])
    with zipfile.ZipFile(dst) as a:
        if a.namelist() != zin.namelist():
            raise ValueError('member list changed')
        diff = [n for n in a.namelist() if a.read(n) != zin.read(n)]
    if diff != [name]:
        raise ValueError('members changed %s, expected only %s' % (diff, name))


def stage(live_dir=LIVE_DIR, out=OUT, log=print):
    import kl_gms
    for n, h in LIVE_MD5.items():
        if md5(os.path.join(live_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned live %s' % (n, h))
    os.makedirs(out, exist_ok=True)
    files = []
    plain_new = None
    gms_ref = None
    for n in ('F06_Main.zip', 'F06_Main.bots.zip'):
        src = os.path.join(live_dir, n)
        name, raw, rec, (w, w2) = locate(src)
        if gms_ref is None:
            gms_ref = raw
        elif raw != gms_ref:
            raise ValueError('%s: unpacked .gms differs from the plain zip\'s: refusing' % n)
        new = patched(raw, rec)
        diff = [i for i in range(len(raw)) if raw[i] != new[i]]
        if len(raw) != len(new) or not diff or not (rec + 28 <= diff[0] and diff[-1] < rec + 32):      # 0x205e6 -> 0x201e6 changes one byte inside the 4-byte word
            raise ValueError('byte diff is not the one flags word: %s' % diff[:8])
        dst = os.path.join(out, n)
        repack(src, dst, name, kl_gms.pack(new))
        with zipfile.ZipFile(dst) as a:
            back = kl_gms.unpack(a.read(name))
        d2 = [i for i in range(len(raw)) if raw[i] != back[i]]
        if len(back) != len(raw) or d2 != diff or back != new:
            raise ValueError('re-read .gms differs from the intended bytes')
        log('  %s: %s flags %#x -> %#x at gms record +28 (rec byte %d), 4m_11 %#x stays; bytes differing %d (%s); other members byte-identical'
            % (n, TARGET[-5:], w, struct.unpack_from('<I', new, rec + 28)[0], rec, w2, len(diff), diff))
        if n == 'F06_Main.zip':
            plain_new = md5(dst)
    with open(os.path.join(out, 'F06_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(plain_new + '\n')
    for n in ('F06_Main.zip', 'F06_Main.bots.zip', 'F06_Main.bots.base.md5'):
        files.append((n, LIVE_MD5[n], md5(os.path.join(out, n))))
        log('  %-24s %s -> %s' % files[-1])
    write_kit(out, files)
    return files


INSTALL_TEMPLATE = r'''r"""Installs / undoes the DM07 UNHIDE TOGGLE TEST 1109 (tools/kl_dm07unhide_1109.py) on the live DM07 files, which were read at stage time:
every pin below is the md5 of a live file as it was then. A TEST build: fence panel 4m_01 visible again (the van gate is closed on it): undo after the bench.

  python install.py            install (originals -> <name>.before-dm07unhide1109 NEXT TO the file; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a copy); --skip-run-check for those / a zombie kl2.exe only
  --min-free-mb N              free space wanted on the game drive besides the files (default 1024)
Every live md5 is pinned BEFORE anything is written (all or nothing: a failure part-way puts the originals back); nothing is written while kl2.exe runs.
Touches only the files listed in FILES (no KLJoin.ini, no KL_PortBackup, nothing else)."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM07', '.before-dm07unhide1109'
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
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + min_free
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + %d MB free on the game drive' % (min_free >> 20)); return 1
    if dry:
        for p in plan:
            print('would %s %s' % ('restore' if undo else 'install', p[0]))
        return 0
    done = []
    try:
        for n, live, bak, src in plan:
            if undo:
                shutil.copyfile(bak, live + '.tmp'); os.replace(live + '.tmp', live); os.remove(bak)
            else:
                shutil.copyfile(live, bak)
                done.append((live, bak))
                shutil.copyfile(src, live + '.tmp'); os.replace(live + '.tmp', live)
            print('%s: %s %s' % (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%s); %s' % (e, 'originals put back' if not undo else 'PARTIAL undo: a rerun is refused for files already restored; restore the rest by hand from the .before-dm07unhide1109 files')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_kit(out, files):
    t = INSTALL_TEMPLATE.replace('@LIVEZIP@', repr(LIVE_MD5['F06_Main.zip'])).replace('@FILES@', '\n'.join('    (%r, %r, %r),' % f for f in files))
    nl, cr = chr(10), chr(13)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM07 unhide 1109.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


def check(zp):
    import kl_fa_bots as F
    B = F.Built(zp, SLOT)
    for k in range(1, len(B.ents) + 1):
        if B.sc.names[k] in (TARGET, KEEP_HIDDEN):
            print('%s flags %#x %s' % (B.sc.names[k], B.ents[k - 1].flags, 'HIDDEN' if B.ents[k - 1].flags & HIDE else 'visible'))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage']:
        stage(*(a[1:3]))
    elif a[:1] == ['check'] and len(a) == 2:
        check(a[1])
    else:
        print(__doc__)
