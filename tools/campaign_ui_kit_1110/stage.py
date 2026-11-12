"""stage.py - builds the campaign_ui_1110 kit folder (default C:\\kl_build_1024\\campaign_ui_1110\\kit) from the live game files, READ ONLY on the
game folders: menu copies (tools/kl_campui_menu.py) + their pins, the SHIP/TEST dll copies, install.py, INSTALL.bat / UNDO.bat.

    py -I tools/campaign_ui_kit_1110/stage.py [--kit DIR] [--dd DIR] [--dm DIR]
"""
import argparse, hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MENU_TOOL = os.path.join(REPO, 'tools', 'kl_campui_menu.py')
BASES = [r'KLExpansion\Overlay\Patch01.zip', r'KLExpansion\Overlay\Patch01_deadmen.zip', r'KLExpansion\Overlay\Patch01_rows12.zip',
         r'KLExpansion\Overlay\Patch01_rows12_deadmen.zip', r'Patch01.zip']


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kit', default=r'C:\kl_build_1024\campaign_ui_1110\kit')
    ap.add_argument('--dd', default=r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
    ap.add_argument('--dm', default=r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men')
    ap.add_argument('--ship', default=os.path.join(REPO, 'klhook', 'out_campaign_ui_1110', 'dinput8.dll'))
    ap.add_argument('--test', default=os.path.join(REPO, 'klhook', 'out_campaign_ui_1110_test', 'dinput8.dll'))
    a = ap.parse_args()
    os.makedirs(os.path.join(a.kit, 'menu'), exist_ok=True)
    pins = {}
    for rel in BASES:
        base = os.path.join(a.dd, rel)
        if not os.path.isfile(base): print('skip (not there): ' + base); continue
        kitname = rel.replace('\\', '__')
        tmp = os.path.join(a.kit, 'menu', '_tmp'); shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        r = subprocess.run([sys.executable, '-I', MENU_TOOL, '--base', base, '--out-dir', tmp, '--dd', a.dd, '--dm', a.dm, '--enable-all'],
                           capture_output=True, text=True)
        if r.returncode: sys.exit('menu build failed for %s:\n%s%s' % (base, r.stdout[-1500:], r.stderr[-1500:]))
        stem, ext = os.path.splitext(os.path.basename(rel))
        built = os.path.join(tmp, stem + '_campui' + ext)
        target_rel = os.path.join(os.path.dirname(rel), stem + '_campui' + ext)
        dest = os.path.join(a.kit, 'menu', target_rel.replace('\\', '__'))
        os.replace(built, dest); shutil.rmtree(tmp)
        pins[target_rel] = dict(base=md5(base), copy=md5(dest))
        print('menu copy %s  (base %s, copy %s)' % (target_rel, pins[target_rel]['base'][:8], pins[target_rel]['copy'][:8]))
    json.dump(pins, open(os.path.join(a.kit, 'menu', 'menu_pins.json'), 'w'), indent=1)
    for name, src in (('dinput8.dll', a.ship), ('dinput8_TEST.dll', a.test)):
        shutil.copyfile(src, os.path.join(a.kit, name))
    open(os.path.join(a.kit, 'dinput8.dll.md5'), 'w').write('%s dinput8.dll (SHIP)\n' % md5(os.path.join(a.kit, 'dinput8.dll')))
    shutil.copyfile(os.path.join(HERE, 'install.py'), os.path.join(a.kit, 'install.py'))
    for b in ('INSTALL.bat', 'UNDO.bat', 'README.txt'):
        shutil.copyfile(os.path.join(HERE, b), os.path.join(a.kit, b))
    print('kit staged in', a.kit)


if __name__ == '__main__':
    main()
