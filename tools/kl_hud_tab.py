"""
The new HUD on the owner's tab: bake every installed Dead Men map again with tools/kl_hud.py.

Nothing here writes into the game folder. It READS <DD>/KLExpansion/Maps/<id>/ (the installed maps) and writes
<out root>/<id>/ (default <work>/build/hud_tab). Installing the result is the game holder's job: re/hud_install.md.

    python tools/kl_hud_tab.py plan [--deep]       # table: id, slot, installed archive, sha1, source build, output
    python tools/kl_hud_tab.py build <out root> [ids ...]   # bake into <out root>/<id>/, check, manifest.json
    python tools/kl_hud_tab.py verify <out root> [ids ...]  # against the installed folders

THE SOURCE OF EVERY BAKE IS THE INSTALLED ARCHIVE ITSELF ("the builds as they are installed"). That is safe because
`kl_hud.py all --look deadmen` is idempotent (measured 2026-10-12, DM01): baking the installed archive twice gives
byte-identical members, and baking the installed (older look) archive gives the same fonts, plate pictures and
extra pictures as baking the build from before the first HUD step (fonts are rebuilt from the stock-order glyph
table each time, the plate pictures are re-made under the same ids, the extra pictures 3000.. are re-made in place
and the new ones 3008..3013 are added). `plan --deep` shows where each installed archive came from by comparing
members (the installer renames the F0x members of a build to its slot's name, so the zip bytes differ).

Side files of a map folder (.WHD .WAV .hti .SND, KLJoin.ini KLTalk.ini KLGuns.ini KLWardrobe.ini and anything else
that lies beside the archive) are copied unchanged; only the _Main.zip is replaced.
"""
import sys, os, json, hashlib, shutil, subprocess, zipfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
WORK = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools'
MAPS_DIR = os.path.join(DD, 'KLExpansion', 'Maps')
# most played first. slot = the stock level the menu redirects to (KLExpansion\Maps\<id>\<slot>_Main.zip)
MAPS = [('DM03', 'F03'), ('DM09', 'F06'), ('DM01', 'F01'), ('DM02', 'F02'), ('DM06', 'F04'), ('DM03A', 'F07'), ('DM05A', 'F01')]
# where the installed archive came from (found 2026-10-12 by member comparison; `plan --deep` re-checks).
# Informational only: the bake takes the installed archive. Paths are under <work>/build.
KNOWN_SRC = {
    'DM01': r'r_tab\DM01', 'DM02': r'r_tab\DM02', 'DM03': r'y_climb\slotted_e', 'DM06': r'r_tab\DM06',
    'DM09': r'y_rappel\DM09r2', 'DM03A': r'q_vault\DM03A_v2', 'DM05A': r'q_club\DM05A_cfx',
}


def sha1(path, chunk=1 << 22):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def installed_zip(mid):
    d = os.path.join(MAPS_DIR, mid)
    z = [f for f in sorted(os.listdir(d)) if f.lower().endswith('_main.zip')]
    if not z:
        raise SystemExit('no _Main.zip in ' + d)
    return os.path.join(d, z[0])


def side_files(d):
    return [f for f in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, f)) and not f.lower().endswith('_main.zip')]


def free_gb(path):
    return shutil.disk_usage(path).free / 1e9


def norm_members(zp, slot):
    """{member name with the slot name made neutral: sha1 of content}"""
    out = {}
    with zipfile.ZipFile(zp) as z:
        for n in z.namelist():
            k = n.replace('/' + slot + '/', '/<L>/').replace('/' + slot + '_Main', '/<L>_Main')
            for s in ('F01', 'F02', 'F03', 'F04', 'F06', 'F07'):          # a build is named for its test slot
                k = k.replace('/' + s + '/', '/<L>/').replace('/' + s + '_Main', '/<L>_Main')
            out[k] = hashlib.sha1(z.read(n)).hexdigest()
    return out


def cmd_plan(deep):
    print('%-6s %-4s %-18s %-10s %-9s %-40s %s' % ('id', 'slot', 'installed archive', 'MB', 'sha1', 'source build (under <work>\\build)', 'output'))
    for mid, slot in MAPS:
        zp = installed_zip(mid)
        s = sha1(zp)
        src = KNOWN_SRC.get(mid, '?')
        note = ''
        cand = os.path.join(WORK, 'build', src)
        if os.path.isdir(cand):
            cz = [f for f in os.listdir(cand) if f.lower().endswith('_main.zip')]
            if cz:
                cp = os.path.join(cand, cz[0])
                if os.path.getsize(cp) == os.path.getsize(zp) and sha1(cp) == s:
                    note = 'identical zip'
                elif deep:
                    a, b = norm_members(zp, slot), norm_members(cp, slot)
                    diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                    note = 'same members after slot rename' if not diff else '%d members differ: %s' % (len(diff), ', '.join(diff[:4]))
                else:
                    note = 'zip differs (slot rename?) - use --deep'
            else:
                note = 'no zip in the source folder'
        else:
            note = 'source folder missing'
        print('%-6s %-4s %-18s %-10.1f %-9s %-40s %s' % (mid, slot, os.path.basename(zp), os.path.getsize(zp) / 1e6, s[:8], src + ' (' + note + ')', os.path.join('<out root>', mid)))
    print('free space on G: %.1f GB' % free_gb(WORK))


def run_hud(src_dir, out_dir):
    """kl_hud.py all <src> <out> --look deadmen  (the same command as by hand); -> (log text, 'PASS' or the problems)"""
    p = subprocess.run([sys.executable, os.path.join(HERE, 'kl_hud.py'), 'all', src_dir, out_dir, '--look', 'deadmen'],
                       capture_output=True, text=True)
    log = p.stdout + p.stderr
    res = next((l[len('check:'):].strip() for l in log.splitlines() if l.startswith('check:')), None)
    if p.returncode != 0 or res is None:
        res = 'ERROR rc=%d: %s' % (p.returncode, log.strip().splitlines()[-1] if log.strip() else '')
    return log, res


def cmd_build(root, ids):
    os.makedirs(root, exist_ok=True)
    todo = [(m, s) for m, s in MAPS if not ids or m in ids]
    manifest_p = os.path.join(root, 'manifest.json')
    manifest = json.load(open(manifest_p)) if os.path.exists(manifest_p) else {}
    for mid, slot in todo:
        d = os.path.join(MAPS_DIR, mid)
        need = sum(os.path.getsize(os.path.join(d, f)) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))
        if free_gb(root) * 1e9 < need * 1.15 + 1.0e9:
            print('%s: NOT BUILT - %.2f GB needed, %.2f GB free on the output drive' % (mid, need / 1e9, free_gb(root)))
            continue
        out = os.path.join(root, mid)
        if os.path.isdir(out):
            shutil.rmtree(out)
        t = time.time()
        log, res = run_hud(d, out)                      # a folder: kl_hud finds the _Main.zip and copies the files beside it
        os.makedirs(out, exist_ok=True)
        for f in side_files(d):                          # belt and braces: whatever kl_hud did not copy
            q = os.path.join(out, f)
            if not os.path.exists(q):
                shutil.copyfile(os.path.join(d, f), q)
        ent = {'slot': slot, 'installed_sha1': sha1(installed_zip(mid)), 'check': res, 'seconds': round(time.time() - t, 1), 'files': {}}
        for f in sorted(os.listdir(out)):
            if os.path.isfile(os.path.join(out, f)):
                ent['files'][f] = {'bytes': os.path.getsize(os.path.join(out, f)), 'sha1': sha1(os.path.join(out, f))}
        manifest[mid] = ent
        json.dump(manifest, open(manifest_p, 'w'), indent=1)
        print('%s: kl_hud check %s, %d files, %.0f MB, %.0f s' % (mid, res, len(ent['files']), sum(v['bytes'] for v in ent['files'].values()) / 1e6, ent['seconds']))
    print('free space: %.1f GB' % free_gb(root))


def cmd_verify(root, ids):
    import kl_hud as H
    bad_all = 0
    for mid, slot in MAPS:
        if ids and mid not in ids:
            continue
        out = os.path.join(root, mid)
        if not os.path.isdir(out):
            print('%s: not built' % mid); continue
        d = os.path.join(MAPS_DIR, mid)
        probs = []
        a, b = set(side_files(d)), set(side_files(out))
        for f in sorted(a - b): probs.append('missing side file ' + f)
        for f in sorted(b - a): probs.append('extra file ' + f)
        for f in sorted(a & b):
            if os.path.getsize(os.path.join(d, f)) != os.path.getsize(os.path.join(out, f)) or sha1(os.path.join(d, f)) != sha1(os.path.join(out, f)):
                probs.append('side file differs: ' + f)
        zi, zo = installed_zip(mid), os.path.join(out, os.path.basename(installed_zip(mid)))
        if not os.path.exists(zo):
            probs.append('no archive in the output'); print('%s: FAIL %s' % (mid, probs)); bad_all += 1; continue
        with zipfile.ZipFile(zi) as x, zipfile.ZipFile(zo) as y:
            if x.namelist() != y.namelist():
                probs.append('member list / order differs')
            changed = [n for n in x.namelist() if n in y.namelist() and x.read(n) != y.read(n)]
        allowed = ('.tex', '.prp', '.prm')                 # fonts + pictures: .TEX pages, the HUD picture lists, the font chunks
        for n in changed:
            if not n.lower().endswith(allowed):
                probs.append('unexpected member changed: ' + n)
        chk = H.check(zi, out, pictures=True, extras=True, draft=True, log=lambda *_: None)
        probs += ['kl_hud.check: ' + c for c in chk]
        print('%s: %s; members changed: %s; side files identical: %d' % (mid, 'OK' if not probs else 'PROBLEMS', ', '.join(n.rsplit('.', 1)[1] for n in changed), len(a & b) - sum(1 for p in probs if p.startswith('side file differs'))))
        for p in probs:
            print('    ' + p)
        bad_all += bool(probs)
    print('verify:', 'PASS' if not bad_all else '%d map(s) with problems' % bad_all)
    return bad_all


def main():
    a = sys.argv[1:]
    if not a or a[0] not in ('plan', 'build', 'verify'):
        print(__doc__); return
    if a[0] == 'plan':
        cmd_plan('--deep' in a)
    elif a[0] == 'build':
        cmd_build(a[1], a[2:])
    else:
        sys.exit(1 if cmd_verify(a[1], a[2:]) else 0)


if __name__ == '__main__':
    main()
