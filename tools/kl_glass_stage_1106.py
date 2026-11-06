r"""kl_glass_stage_1106.py - stages the glass-connectivity fix for Last Call (DM05A, slot F01), 2026-11-06. OFFLINE: nothing here is installed or run.

PROBLEM: online FA round 2 on Last Call freezes the main thread 21-29 s per seat (session state 0x25) because every shard group recomputes its
neighbour table (kl2 0x4dfd60 / 0x4a45a0, tools/kl_glass_conn.py) - the port stripped the .sgd section HavokShatterGlassConnectivity.
FIX: tools/kl_glass_conn.py build puts the section back (computed from the level's own shard meshes, byte-exact against Dead Men's shipped data).

Writes under <out> (default C:\kl_build_1024\lastcall_glass_1106):
  stage\       the CHAIN stage zip (c8dd18ee, life + fight + heli) + glass. install.py takes the live files from EITHER pinned state:
               stock live (e9fab045 ...: installs chain + glass in one step, also F01_Main_LS.SND) or chain installed (c8dd18ee ...: glass only).
  glass_only\  the stock live zip (e9fab045) + glass, nothing else. install.py pins the stock live files.
  Both: F01_Main.bots.zip ([BotGate] sibling, kl_botsonline eAllTypes, rebuilt from the final plain zip) + F01_Main.bots.base.md5,
  install.py (backups <name>.before-1106glass, --dry, --undo, --skip-run-check, --game), INSTALL / UNDO bats.
Install only ONE of the two. A later step that rebuilds the plain zip (doors, ...) must run kl_glass_conn.py build LAST (or the section is lost
only if the step re-joins the .sgd; steps that copy members keep it).

usage (from tools/):  python kl_glass_stage_1106.py [--chain <dir>] [--live <Maps\DM05A>] [--out <dir>]
"""
import hashlib, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_glass_conn
import kl_botsonline

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPDIR = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
CHAIN = r'C:\kl_build_1024\lastcall_chain_1105\stage'
OUT = r'C:\kl_build_1024\lastcall_glass_1106'
TAG = '.before-1106glass'
STOCK = {'F01_Main.zip': 'e9fab0453a5260369c2fddd01bed5534', 'F01_Main.bots.zip': '7a1024ed8cb031596136717f7256545e',
         'F01_Main.bots.base.md5': 'fe3373c87bd0385dbfbc4895bb8ec5ec', 'F01_Main_LS.SND': '3b21242cfdc622de588e0d4f2b4dd668'}
CHAIN_PIN = 'c8dd18ee28b511db2ee46a10f9e86e11'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


INSTALL_PY = r'''r"""Installs / undoes the Last Call GLASS pass (2026-11-06): the .sgd section HavokShatterGlassConnectivity (tools/kl_glass_conn.py) for all 50 shard
groups, so round 2 no longer freezes 21-29 s while the engine recomputes the neighbour tables.  Variant: %(variant)s
%(blurb)s
  python install.py            install (originals -> <name>%(tag)s; an existing backup is NEVER overwritten: refuses)
  python install.py --undo     put every original back byte for byte (only when each live file is exactly what this wrote)
  python install.py --dry      read-only: print every pin and what would happen (also usable with --undo)
  --game <dir>                 a Dog Days folder other than the default (rehearsals on a scratch copy); --skip-run-check for those only
Every live md5 is pinned before anything is written; nothing is written while kl2.exe runs. Never touches KL_PortBackup or any other file."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAP, TAG = 'DM05A', '%(tag)s'
FILES = [   # name, live md5 before (any of these), staged md5 after
%(files)s]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, 'KLExpansion', 'Maps', MAP)
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    plan = []
    for n, olds, new in FILES:
        live, bak, src = os.path.join(d, n), os.path.join(d, n + TAG), os.path.join(HERE, n)
        if not os.path.isfile(live):
            print('REFUSED: %%s is not there' %% live); return 1
        cur = md5(live)
        print('%%-26s live %%s' %% (n, cur))
        if undo:
            if not os.path.isfile(bak):
                print('REFUSED: no backup %%s' %% bak); return 1
            if cur != new:
                print('REFUSED: %%s live md5 %%s is not the installed %%s' %% (n, cur, new)); return 1
            if md5(bak) not in olds:
                print('REFUSED: backup of %%s is not one of the pinned originals %%s' %% (n, olds)); return 1
        else:
            if cur == new:
                print('REFUSED: %%s is already the staged file (installed already)' %% n); return 1
            if cur not in olds:
                print('REFUSED: %%s live md5 %%s is not a pinned original %%s (another pass changed it: re-stage)' %% (n, cur, olds)); return 1
            if os.path.exists(bak):
                print('REFUSED: backup %%s exists already (never overwritten); move it away yourself' %% bak); return 1
            if not os.path.isfile(src) or md5(src) != new:
                print('REFUSED: staged %%s missing or not md5 %%s' %% (src, new)); return 1
        plan.append((n, live, bak, src))
    if not undo:
        need = sum(os.path.getsize(p[3]) + os.path.getsize(p[1]) for p in plan) + (1 << 30)
        if shutil.disk_usage(d).free < need:
            print('REFUSED: less than the files + 1 GB free on the game drive'); return 1
    if dry:
        for p in plan:
            print('would %%s %%s' %% ('restore' if undo else 'install', p[0]))
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
            print('%%s: %%s %%s' %% (n, 'restored' if undo else 'installed', md5(live)))
    except OSError as e:
        if not undo:
            for live, bak in reversed(done):
                shutil.copyfile(bak, live); os.remove(bak)
        print('FAILED (%%s); %%s' %% (e, 'originals put back' if not undo else 'rerun --undo')); return 2
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def stage_dir(d, plain_in, files_old, extra, blurb, variant, log=print):
    """d: output dir; plain_in: zip to add the section to; files_old {name: [old md5, ...]}; extra {name: source} files copied as they are."""
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    plain = os.path.join(d, 'F01_Main.zip')
    items = kl_glass_conn.insert(plain_in, plain)
    log('  %s: %d panes, %d records' % (variant, len(items), sum(len(r) for _, r in items)))
    kl_botsonline.convert(plain, os.path.join(d, 'F01_Main.bots.zip'), 'eAllTypes', log=lambda *a: None)
    open(os.path.join(d, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(md5(plain) + '\n')
    for n, src in extra.items():
        shutil.copyfile(src, os.path.join(d, n))
    rows = ''.join('    (%r, %r, %r),\n' % (n, olds, md5(os.path.join(d, n))) for n, olds in files_old.items())
    open(os.path.join(d, 'install.py'), 'w', newline='\n').write(INSTALL_PY % dict(variant=variant, blurb=blurb, tag=TAG, files=rows))
    open(os.path.join(d, 'INSTALL last call glass 1106.bat'), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py\r\npause\r\n')
    open(os.path.join(d, 'UNDO last call glass 1106.bat'), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py --undo\r\npause\r\n')
    return {n: md5(os.path.join(d, n)) for n in sorted(os.listdir(d))}


def main(a):
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    chain, live, out = opt('--chain', CHAIN), opt('--live', MAPDIR), opt('--out', OUT)
    czip = os.path.join(chain, 'F01_Main.zip')
    if md5(czip) != CHAIN_PIN:
        raise SystemExit('%s md5 is not the chain stage %s' % (czip, CHAIN_PIN))
    for n, m in STOCK.items():
        if md5(os.path.join(live, n)) != m:
            raise SystemExit('live %s is not the pinned stock md5 %s (already changed: stage from the right base)' % (n, m))
    # chain stage files that the chain install.py changes, with the md5 each is when the chain is already installed
    chain_new = {n: md5(os.path.join(chain, n)) for n in STOCK}
    rep = {}
    files = {n: [STOCK[n], chain_new[n]] for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')}
    files['F01_Main_LS.SND'] = [STOCK['F01_Main_LS.SND'], chain_new['F01_Main_LS.SND']]
    # the chain's LS.SND is not touched by this pass but installs with the chain when the live files are still stock: the stage carries it
    sd = os.path.join(out, 'stage')
    rep['stage'] = stage_dir(sd, czip, files, {'F01_Main_LS.SND': os.path.join(chain, 'F01_Main_LS.SND')},
                             'Starts from the Last Call CHAIN stage (life + fight + heli, plain zip c8dd18ee) and adds the glass section. The live\n'
                             'files may be the stock ones (e9fab045 ...: chain + glass in one step) or the chain already installed (c8dd18ee ...: glass only).',
                             'chain + glass')
    # the .bots.zip of the chain differs from the stock one in more than the section, so the glass-only variant rebuilds from the stock live zip
    tmp = os.path.join(out, '_live')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    shutil.copyfile(os.path.join(live, 'F01_Main.zip'), os.path.join(tmp, 'F01_Main.zip'))          # read-only copy of the live file
    gd = os.path.join(out, 'glass_only')
    only = {n: [STOCK[n]] for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')}
    rep['glass_only'] = stage_dir(gd, os.path.join(tmp, 'F01_Main.zip'), only, {},
                                  'Starts from the STOCK live zip (e9fab045) and adds only the glass section: no chain content. Pins the stock live files.',
                                  'glass only (stock live e9fab045)')
    shutil.rmtree(tmp, ignore_errors=True)
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
