#!/usr/bin/env python3
r"""kl_club_doors_1106.py - kick doors for Last Call (DM05A, slot F01), written 2026-11-06. OFFLINE only: nothing here is run in the game.

Owner 2026-11-05: "kickable doors toward the exit". This stages a doors variant ON TOP of the Last Call chain stage
(C:\kl_build_1024\lastcall_chain_1105\stage, plain zip c8dd18ee = life -> fight -> heli) and replaces that stage as the thing to install:
  1. kl_interact_graft.build   4 virtual kick doors (the doorways have no door leaf left: the four animated doors are sunk by the club build)
  2. kl_bots_kick_1025.build   the heister bots get a KickDoorBehaviourRout step where a leg crosses a door (else they walk into a shut door)
  3. [BotGate] sibling (kl_botsonline eAllTypes) + bots.base.md5, rebuilt from the final plain zip
  4. KLJoin.ini / KLGuns.ini Entries= set to the new .prm chunk count (the graft appends .prm chunks), checked with kl_fa_fedbody check
  5. install.py (all pinned to the live files, refuses while kl2.exe runs, backups '.before-1106doors') + INSTALL/UNDO bats

THE DOORS (all on the walk from the loot room to the roof pad; measured on the chain zip's walk mesh, see re/club_fight_1105.md 2026-11-06)
  B01  daughter-room door B  x 1500, opening z 3293..3433 (two nav wall points 140 cm apart), travel along x
  A02  daughter-room door A  x 2500, same opening z 3293..3433                                  (the 3 'Fight!Loot' guards stand between the two)
  F03  storage Firedoor_03   (-3190, 860, 2306), travel along z, in the 60 cm mesh strip that starts there
  F02  roof Firedoor_02      (-3790, 860, 3287), travel along z, in the 60 cm mesh strip
The stairs neck that the fight tool's --doors picked is NOT used: no distinct doorway shows on the mesh there (a ~80 cm hole between blocks).
Orientation: kl_interact_graft.virtual_host(hinge, cx): cx = direction from the free end TO the hinge; the leaf lies along -cx from the hinge.
Width: one scale per map (median over hosts), so every door is 140 wide x 240 high (stock 120 x 220).

usage (from tools/):  python kl_club_doors_1106.py stage [--src <chain stage dir>] [--out <dir>] [--no-bots]
"""
import hashlib, json, math, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_interact_graft as IG
import kl_bots_kick_1025 as KK
import kl_botsonline
import kl_prmgraph
import kl_fa_bots as KB

CHAIN = r'C:\kl_build_1024\lastcall_chain_1105\stage'
OUT = r'C:\kl_build_1024\lastcall_chain_doors_1106'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
CHAIN_PIN = 'c8dd18ee28b511db2ee46a10f9e86e11'
TAG = '.before-1106doors'
WIDTH, HEIGHT = 140.0, 240.0
# name, hinge point (x, y, z), cx (from the free end to the hinge)
DOORS = (('B01', (1500.0, 360.0, 3433.0), (0.0, 0.0, 1.0)),
         ('A02', (2500.0, 360.0, 3433.0), (0.0, 0.0, 1.0)),
         ('F03', (-3120.0, 860.0, 2306.0), (1.0, 0.0, 0.0)),
         ('F02', (-3720.0, 860.0, 3287.0), (1.0, 0.0, 0.0)))
INI_FILES = ('KLJoin.ini', 'KLGuns.ini')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def chunks(zp):
    import zipfile
    z = zipfile.ZipFile(zp)
    prm = [n for n in z.namelist() if n.lower().endswith('.prm')]
    return len(kl_prmgraph.read(z.read(prm[0])).chunks)


def patch_entries(path_in, n):
    txt = open(path_in, 'rb').read().decode('latin-1')
    new, c = re.subn(r'(?m)^(Entries\s*=\s*)\d+', lambda m: m.group(1) + str(n), txt)
    return new.encode('latin-1'), c


def graft(src, dst, log):
    orig = IG.virtual_host
    IG.virtual_host = lambda hinge, cx, width=WIDTH, height=HEIGHT: orig(hinge, cx, width, height)
    try:
        return IG.build(src, dst, ext=0, doors=[('at', h, cx) for _n, h, cx in DOORS], log=log)
    finally:
        IG.virtual_host = orig


def stage(src_dir, out, bots=True, log=print):
    st, work = os.path.join(out, 'stage'), os.path.join(out, '_work')
    for d in (st, work):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    src = os.path.join(src_dir, 'F01_Main.zip')
    if md5(src) != CHAIN_PIN:
        raise ValueError('%s md5 %s is not the chain stage %s (re-stage the chain first)' % (src, md5(src), CHAIN_PIN))
    g = os.path.join(work, 'grafted.zip')
    rep = {'doors': [[n, list(h), list(c)] for n, h, c in DOORS]}
    rep['graft'] = graft(src, g, log)
    final = os.path.join(st, 'F01_Main.zip')
    if bots:
        rep['kick'] = KK.build(g, 'F01', final, log=log)
    else:
        shutil.copyfile(g, final)
    rep['md5_plain'] = md5(final)
    rep['chunks'] = chunks(final)
    kl_botsonline.convert(final, os.path.join(st, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(st, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(rep['md5_plain'] + '\n')
    shutil.copyfile(os.path.join(src_dir, 'F01_Main_LS.SND'), os.path.join(st, 'F01_Main_LS.SND'))
    for n in INI_FILES:
        data, c = patch_entries(os.path.join(MAPDIR, n), rep['chunks'])
        if c != 1:
            raise ValueError('%s: %d Entries= lines' % (n, c))
        open(os.path.join(st, n), 'wb').write(data)
    files = {}
    for n in sorted(os.listdir(st)):
        old = os.path.join(MAPDIR, n)
        files[n] = (md5(old), md5(os.path.join(st, n)))
    rep['files'] = files
    chain_install = open(os.path.join(src_dir, 'install.py'), encoding='utf-8').read()
    fl = 'FILES = [   # name, live md5 before, staged md5 after\n' + ''.join("    (%r, %r, %r),\n" % (n, o, w) for n, (o, w) in files.items() if o != w) + ']\n'
    inst = re.sub(r'FILES = \[.*?\n\]\n', lambda m: fl, chain_install, flags=re.S)
    inst = inst.replace("'.before-1105chain'", repr(TAG)).replace('before-1105chain', 'before-1106doors')
    inst = inst.replace('Installs / undoes the Last Call CHAIN pass (2026-11-05): life + fight + heli on top of the live DM05A files, in one step.',
                        'Installs / undoes the Last Call CHAIN + DOORS pass (2026-11-06): life + fight + heli + 4 kick doors (tools/kl_club_doors_1106.py),\nINSTEAD of install.py of the chain stage (same live files; install only one of them).')
    inst = inst.replace('KLJoin.ini / KLGuns.ini need no change\n(.prm chunk count stays 54305 = their Entries=).', 'KLJoin.ini / KLGuns.ini Entries= follow the new .prm chunk count.')
    open(os.path.join(st, 'install.py'), 'w', newline='\n').write(inst)
    open(os.path.join(st, 'INSTALL last call chain doors 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py"\r\npause\r\n')
    open(os.path.join(st, 'UNDO last call chain doors 1106.bat'), 'w', newline='\r\n').write('@echo off\r\npython "%~dp0install.py" --undo\r\npause\r\n')
    with open(os.path.join(st, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    shutil.rmtree(work, ignore_errors=True)
    log('staged %s  plain md5 %s, chunks %d' % (st, rep['md5_plain'], rep['chunks']))
    return rep


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a or a[0] != 'stage':
        print(__doc__)
        return 2
    stage(opt('--src', CHAIN), opt('--out', OUT), bots='--no-bots' not in a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
