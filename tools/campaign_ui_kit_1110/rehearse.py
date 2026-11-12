"""rehearse.py - runs the kit's install / second install / undo in a SCRATCH game folder (never the real one), 3 levels M01 M14 M07F.
    py -I tools/campaign_ui_kit_1110/rehearse.py [--kit DIR] [--scratch DIR]
Prints PASS/FAIL per step and a final RESULT line; exit 1 on a FAIL."""
import argparse, hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS); sys.dont_write_bytecode = True
import kl_campaign as K

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
IDS = ['M01', 'M14', 'M07F']
fails = []


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def tree(root):
    r = {}
    for d, _, fs in os.walk(root):
        for f in fs: r[os.path.relpath(os.path.join(d, f), root)] = md5(os.path.join(d, f))
    return r


def check(name, ok, extra=''):
    print(('PASS ' if ok else 'FAIL ') + name + (' ' + extra if extra else ''))
    if not ok: fails.append(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kit', default=r'C:\kl_build_1024\campaign_ui_1110\kit')
    ap.add_argument('--scratch', default=r'C:\kl_build_1024\campaign_ui_1110\scratch')
    ap.add_argument('--old-out', default=r'C:\kl_build_1024\campaign_1109\anp_out')
    a = ap.parse_args()
    shutil.rmtree(a.scratch, ignore_errors=True)
    dd, kit = os.path.join(a.scratch, 'dd'), os.path.join(a.scratch, 'kit')
    os.makedirs(dd)
    shutil.copytree(a.kit, kit)
    for f in ('dinput8.dll', 'KLHook.ini', 'Patch01.zip'):
        shutil.copy2(os.path.join(DD, f), os.path.join(dd, f))
    os.makedirs(os.path.join(dd, 'KLExpansion', 'Overlay'))
    for f in ('Patch01.zip', 'Patch01_deadmen.zip', 'Patch01_rows12.zip', 'Patch01_rows12_deadmen.zip'):
        shutil.copy2(os.path.join(DD, 'KLExpansion', 'Overlay', f), os.path.join(dd, 'KLExpansion', 'Overlay', f))
    for i in IDS: K.install_level(i, a.old_out, dd, a.scratch + r'\w', running=lambda: False, log=lambda *x: None)
    before = tree(dd)
    env = dict(os.environ, KLCAMP_DD=dd, KLCAMP_IDS=' '.join(IDS))
    inst = os.path.join(kit, 'install.py')

    def run(*args):
        r = subprocess.run([sys.executable, '-I', inst, *args], env=env, capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr).strip()

    rc, out = run('--dry'); check('install --dry ok', rc == 0, out[-120:]); check('dry wrote nothing', tree(dd) == before)
    rc, out = run('--undo', '--dry'); check('undo before install refused', rc != 0, out[-100:])
    rc, out = run(); check('install ok', rc == 0, out[-200:])
    after = tree(dd)
    new = sorted(set(after) - set(before)); chg = sorted(k for k in before if after.get(k) != before[k])
    check('menu copies added (5)', sum(1 for n in new if n.endswith('_campui.zip')) == 5, str([n for n in new if 'campui' in n]))
    check('dll swapped to kit build', md5(os.path.join(dd, 'dinput8.dll')) == md5(os.path.join(kit, 'dinput8.dll')))
    ini = open(os.path.join(dd, 'KLHook.ini'), 'rb').read().decode('ascii')
    check('ini has [CampaignUI] Menu=1', '[CampaignUI]' in ini and 'Menu=1' in ini)
    stock = [k for k in chg if not (k.startswith('Scenes') or k in ('dinput8.dll', 'KLHook.ini'))]
    check('no stock menu archive changed', not stock, str(stock))
    check('level files changed', any(k.startswith('Scenes') for k in chg), '%d changed' % len([k for k in chg if k.startswith('Scenes')]))
    rc, out = run(); check('second install refused', rc != 0 and 'REFUSED' in out, out[:160])
    check('second install changed nothing', tree(dd) == after)
    rc, out = run('--undo', '--dry'); check('undo --dry ok', rc == 0, out[-100:]); check('undo dry wrote nothing', tree(dd) == after)
    rc, out = run('--undo'); check('undo ok', rc == 0, out[-200:])
    final = tree(dd)
    check('undo byte-exact (levels, manifests, dll, ini, menus)', final == before,
          str(sorted(set(final) ^ set(before))[:5] + [k for k in before if final.get(k) != before[k]][:5]))
    check('kit backup + state gone', not os.path.exists(os.path.join(kit, 'installed.json')) and not os.path.exists(os.path.join(kit, 'backup')))
    rc, out = run(); check('reinstall after undo ok', rc == 0, out[-100:])
    rc, out = run('--undo'); check('second undo ok, byte-exact', rc == 0 and tree(dd) == before)
    print('RESULT: %s (%d fails)' % ('FAIL' if fails else 'PASS', len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
