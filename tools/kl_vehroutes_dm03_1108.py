r"""kl_vehroutes_dm03_1108.py - DM03 (Bank / slot F03): the escape van and the delivery car drove THROUGH parked template cars (vehicle audit 2026-11-08).
Written 2026-11-08, OFFLINE: reads the staged doors_1108 DM03 files (input pins below), writes NEW files, never the live ones.

CAUSE (kl_vehaudit_1108, DM03): 16 ZLNKOBJ spawn templates 'Traffic!Cars!Ground_USA_*' (set M03_FAA_Outside_03A, all 8 at the world origin, on the van's
arrival lane) and 'Trafiic!Cars!Ground_USA_*' (set M03_FAA_Outside_02A, at (-9726..-10874, 705, -9318), on the delivery car's route) are the models ZTrafficFlow
clones. Dead Men leaves them lying where the editor put them; they have NO .HVK collision, but they are drawn, so the escape van (keys 57..66) and the delivery
car visibly pass through four of them. They are not parked cars the player can use: nothing else refers to their place.
FIX: all 16 are moved to y = HIDE_Y straight below their place (same x / z; NOT deleted, still ZLNKOBJ nodes with their own names, so the traffic flow finds
its templates). The vehicles that matter (the van, the delivery car, the clones the flow spawns) keep their routes and stay drawn and shootable.
NOT -60000: a node at y -60000 caused an 'OUTSIDE octree' fake-target crash (debug crash_686a66); -3500 is a modest 35 m under the floor.
GUESSES: (1) the flow clones the template's CLASS and rig, not its position (the 16 templates sit at 2 places yet the flow spawns cars along its own spline, and
DM06B's kl_dm06b_traffic_1108 treats them the same way); (2) the octree entry of a moved node is stale (harmless: .oct is not rewritten, as in every
move of the vehroutes passes); (3) a template below the floor is not drawn (the floor tiles above it are opaque).
Plain and bots zips are edited the same way and must differ only in the .prp, as before. usage: python kl_vehroutes_dm03_1108.py stage <out dir> | check <zip>"""
import hashlib, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_bots as F, kl_gms, kl_graft
import kl_vehroutes_street_1108 as S

IN_DIR = r'C:\kl_build_1024\doors_1108\DM03'          # the doors_1108 DM03 stage = this pass's pinned input
PINS = {'F03_Main.zip': '33d1fa5f9d94013a35c952bee8241cb6', 'F03_Main.bots.zip': '2971ec6db9bdc5f4fe45abaad4cc37ff',
        'F03_Main.bots.base.md5': 'a14e01345267fd8e255e250adca82bd5'}
SLOT = 'F03'
HIDE_Y = -3500.0
PREFIXES = ('Traffic!Cars!Ground_', 'Trafiic!Cars!Ground_')     # sic: the 02A set's group is spelt 'Trafiic'
BUF = 'Scenes/Locations/F03/F03_Main.buf'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def templates(B):
    """-> node numbers of the spawn templates (names start with a PREFIX, 'Reflection' paths excluded), in node order."""
    sc = B.sc
    return [k for k in range(1, len(sc.names)) if sc.names[k].startswith(PREFIXES) and 'Reflection' not in sc.path[k]]


def build(src, log=print):
    """zip -> ({member: bytes} of the changed members, [(name, old pos, new pos)])."""
    B = F.Built(src)
    zf = zipfile.ZipFile(src)
    gms_name = next(n for n in zf.namelist() if n.lower().endswith('_main.gms'))
    prp_name = next(n for n in zf.namelist() if n.lower().endswith('_main.prp'))
    if B.scene.write()[0] != kl_gms.unpack(zf.read(gms_name)):
        raise ValueError('the .gms does not round-trip through kl_scene (stop: nothing was written)')
    if B.sc.p.serialize() != zf.read(prp_name):
        raise ValueError('the .prp does not round-trip (stop: nothing was written)')
    ks = templates(B)
    if len(ks) != 16:
        raise ValueError('want 16 spawn templates, found %d' % len(ks))
    moved = []
    for k in ks:
        t = struct.unpack('<3f', B.ents[k - 1].trans[:12])
        w = B.at(k)
        if any(abs(w[i] - t[i]) > 0.5 for i in range(3)):
            raise ValueError('%s: parents are not identity (local %r world %r)' % (B.sc.names[k], t, w))
        new = (t[0], HIDE_Y, t[2])
        S.put(B, k, pos=new)
        moved.append((B.sc.names[k], tuple(round(x) for x in t), tuple(round(x) for x in new)))
    gms, _buf = B.scene.write()
    out = {prp_name: B.sc.p.serialize(), gms_name: kl_gms.pack(gms)}
    log('kl_vehroutes_dm03_1108: %d templates moved to y %d' % (len(moved), HIDE_Y))
    return out, moved


def write_zip(src, dst, log=print):
    out, moved = build(src, log)
    zin = zipfile.ZipFile(src)
    members = [(n, out[n] if n in out else zin.read(n)) for n in zin.namelist()]
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))
    with zipfile.ZipFile(dst) as a:
        if a.namelist() != zin.namelist():
            raise ValueError('member list changed')
        diff = sorted(n for n in a.namelist() if a.read(n) != zin.read(n))
    if diff != sorted(out):
        raise ValueError('members changed %s, expected %s' % (diff, sorted(out)))
    return moved


def check(zp, log=print):
    """Proofs on a staged zip -> list of problems: 16 templates, all at HIDE_Y, names and count kept."""
    B = F.Built(zp)
    bad = []
    ks = templates(B)
    if len(ks) != 16:
        bad.append('%d templates' % len(ks))
    for k in ks:
        y = struct.unpack('<3f', B.ents[k - 1].trans[:12])[1]
        if abs(y - HIDE_Y) > 0.01 or abs(B.at(k)[1] - HIDE_Y) > 0.01:
            bad.append('%s at y %.1f' % (B.sc.names[k], y))
    log('  %d templates, all at y %d: %s' % (len(ks), HIDE_Y, 'ok' if not bad else bad))
    return bad


def stage(out, in_dir=IN_DIR, log=print):
    import kl_botsonline
    for n, h in PINS.items():
        if md5(os.path.join(in_dir, n)) != h:
            raise ValueError('refusing: %s is not the pinned %s (stage doors_1108 DM03 first)' % (n, h))
    if open(os.path.join(in_dir, 'F03_Main.bots.base.md5')).read().strip() != PINS['F03_Main.zip']:
        raise ValueError('bots.base.md5 is not the plain zip md5')
    os.makedirs(out, exist_ok=True)
    rep = {}
    for n in ('F03_Main.zip', 'F03_Main.bots.zip'):
        rep[n] = write_zip(os.path.join(in_dir, n), os.path.join(out, n), log)
    with zipfile.ZipFile(os.path.join(out, 'F03_Main.zip')) as a, zipfile.ZipFile(os.path.join(out, 'F03_Main.bots.zip')) as b:
        diff = [m for m in a.namelist() if a.read(m) != b.read(m)]
    if any(not m.lower().endswith('.prp') for m in diff):
        raise ValueError('plain and bots zips differ outside the .prp: %s' % diff)
    plain = md5(os.path.join(out, 'F03_Main.zip'))
    with open(os.path.join(out, 'F03_Main.bots.base.md5'), 'w', newline='\n') as fh:
        fh.write(plain + '\n')
    files = [(n, PINS[n], md5(os.path.join(out, n))) for n in PINS]
    write_kit(out, files)
    for f in files:
        log('  %-24s %s -> %s' % f)
    return files, rep


def write_kit(out, files):
    """install.py = the DM01B vehroutes kit's with this map's folder, tag and pins (needs doors_1108/DM03 installed first)."""
    t = open(r'C:\kl_build_1024\vehroutes_1108\DM01B\install.py', encoding='utf-8').read()
    nl = chr(10)
    i, j = t.index('FILES = ['), t.index(nl + ']' + nl) + 3
    t = t[:i] + 'FILES = [   # name, live md5 before, staged md5 after' + nl + nl.join('    (%r, %r, %r),' % f for f in files) + nl + ']' + nl + t[j:]
    t = t.replace("MAP, TAG = 'DM01B', '.before-vehroutes1108'", "MAP, TAG = 'DM03', '.before-vehroutes1108dm03'")
    t = t.replace("LIVE_ZIP_MD5 = '74d3723323dc1aa03d3166b522ae5448'", 'LIVE_ZIP_MD5 = %r' % PINS['F03_Main.zip'])
    t = t.replace('DM01B VAN DRIVE-AWAY 1108 (tools/kl_vehroutes_1108.py)',
                  'DM03 TEMPLATE CARS OFF THE VAN / DELIVERY LANES 1108 (tools/kl_vehroutes_dm03_1108.py; install doors_1108/DM03 FIRST, and dm03cops_1108 before that)')
    t = t.replace('on the live DM01B files', 'on the live DM03 files').replace('<name>.before-vehroutes1108 NEXT', '<name>.before-vehroutes1108dm03 NEXT')
    t = t.replace('another pass changed it: re-stage)', 'another pass changed it; install dm03cops_1108 then doors_1108/DM03 first: re-stage)')
    if 'DM01B' in t:
        raise ValueError('install.py still names DM01B')
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline=nl).write(t)
    cr = chr(13)
    for nm, arg in (('INSTALL', ''), ('UNDO', ' --undo')):
        open(os.path.join(out, '%s DM03 vehroutes 1108.bat' % nm), 'w', newline=cr + nl).write('@echo off' + cr + nl + 'python "%~dp0install.py"' + arg + cr + nl + 'pause' + cr + nl)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['stage'] and len(a) == 2:
        stage(a[1])
    elif a[:1] == ['check'] and len(a) == 2:
        bad = check(a[1])
        print('PROBLEMS:' if bad else 'check: ok', bad)
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)
        sys.exit(2)
