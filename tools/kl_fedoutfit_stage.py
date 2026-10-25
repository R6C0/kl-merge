#!/usr/bin/env python3
"""kl_fedoutfit_stage.py - the player's fed outfit on the Dead Men maps, staged pinned on the CURRENT live zips. OFFLINE, installs nothing.

  python tools/kl_fedoutfit_stage.py [--out C:/kl_build_1024/fedoutfit_1025a] [--only DM01,DM09] [--no-graft] [--no-rehearse]

Owner 2026-10-25: 'it still makes me the chinese fed' (the fed of a Dead Men Fragile Alliance map is a DD police body: model 1919 = Shanghai SWAT).
Cause (klhook/klfedkit.c): [Fed] Body defaults to 0 and the installed KLHook.ini has no Body= line, so the body routine never runs; and the
maps' KLJoin.ini [FedBody] Entries= (the .prm chunk count) had gone stale as the zips were rebuilt. This tool re-derives every [FedBody] from
the LIVE zip with kl_fa_fedbody.apply (so Entries= is exact) and stages, per map, a md5-chained KLJoin.ini install/undo (tools/kl_fedoutfit.ps1).
Last Call (DM05A) has no police-type actor to name, so its stage is a graft (kl_fedoutfit_dm05a.py: the zip itself changes, Entries= unchanged).
The hook line Body=1 is NOT staged here: HOOK_PROPOSAL.md (kl-merge-e8 owns KLHook.ini).
Re-run after ANY rebuild of a map's zip (Entries= goes stale whenever the .prm changes); the install refuses a zip it was not built for.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa_fedbody as FB

DEFAULT_OUT = r'C:\kl_build_1024\fedoutfit_1025a'
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS_DIR = os.path.join(DD, 'KLExpansion', 'Maps')
TAG = '.before-1025fedoutfit'
# (map folder, zip name, kl_fa_fedbody options, what the fed looks like, how sure)
HOOK = [
    ('DM01', 'F01_Main.zip', [], "Hot Coffee: an FBI agent (FBI-Agents_01), looks 1-8", 'chosen before, now fixed'),
    ('DM01B', 'F03_Main.zip', ['--root', '41940', '--variants', '1,2'], 'Hot Coffee 2: a US SWAT man, looks 1-2', 'my choice, unproven'),
    ('DM02', 'F02_Main.zip', ['--body', 'policeswats'], 'Late Night mall: a US SWAT man (PoliceSwats_01)', 'my choice, unproven'),
    ('DM03A', 'F07_Main.zip', ['--root', '63017', '--variants', '1,2'], 'Withdrawal: a US SWAT man, looks 1-2', 'my choice, unproven'),
    ('DM06', 'F04_Main.zip', [], "Park: a yakuza drug-squad biker (Bridge_JPN_DrugGuy_01), looks 1,3,4", 'owner asked for this on 10-11'),
    ('DM09', 'F06_Main.zip', [], "Retomoto: a Japanese SWAT man (SWAT_Beam03)", 'chosen before, now fixed'),
    ('DM09RB', 'F06_Main.zip', [], 'Retomoto copy RB: Japanese SWAT', 'same as DM09'),
    ('DM09RB2', 'F06_Main.zip', [], 'Retomoto copy RB2: Japanese SWAT', 'same as DM09'),
    ('DM09RB3', 'F06_Main.zip', [], 'Retomoto copy RB3: Japanese SWAT', 'same as DM09'),
    ('DM09RB4', 'F06_Main.zip', [], 'Retomoto copy RB4: Japanese SWAT', 'same as DM09'),
    ('DM09RD', 'F06_Main.zip', [], 'Retomoto copy RD: Japanese SWAT', 'same as DM09'),
    ('DM09RV', 'F06_Main.zip', [], 'Retomoto copy RV: Japanese SWAT', 'same as DM09'),
    ('DM09RV2', 'F06_Main.zip', [], 'Retomoto copy RV2: Japanese SWAT', 'same as DM09'),
    ('DM11B', 'F04_Main.zip', ['--root', '42080', '--variants', '1,2,3,4,5,6,7,8'], 'Hasta: a Cuban rebel soldier, looks 1-8', 'my choice, unproven'),
]
GRAFT = ('DM05A', 'F01_Main.zip', 'Last Call: a Japanese police officer (JPN_Police_AllinOne, from DM09/M09_B), grafted into the map', 'guess')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def write(path, text, crlf=True):
    with open(path, 'w', encoding='ascii', newline='') as f:
        f.write(text.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else text)


def bats(folder, ps1, name):
    for label, arg in (('INSTALL', ''), ('UNDO', ' -Undo')):
        write(os.path.join(folder, '%s %s.bat' % (label, name)),
              '@echo off\ncd /d "%%~dp0"\npowershell -NoProfile -ExecutionPolicy Bypass -File "%%~dp0%s"%s\npause\n' % (ps1, arg))


def manifest(folder, m, pins, files, extra):
    d = dict(m=m, tag=TAG, pins=pins, files=files, **extra)
    with open(os.path.join(folder, 'fedoutfit.json'), 'w') as f:
        json.dump(d, f, indent=1)
    shutil.copyfile(os.path.join(HERE, 'kl_fedoutfit.ps1'), os.path.join(folder, 'fedoutfit.ps1'))
    bats(folder, 'fedoutfit.ps1', 'fedoutfit')


def stage_hook(out, m, zipname, opt, look, sure, log):
    live = os.path.join(MAPS_DIR, m, zipname)
    zmd5 = md5(live)
    ini_live = os.path.join(MAPS_DIR, m, 'KLJoin.ini')
    old = md5(ini_live) if os.path.isfile(ini_live) else None
    folder = os.path.join(out, m, 'stage')
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    tmp = os.path.join(out, '_apply_' + m)
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    _o, sec = FB.apply(live, tmp, {k.lstrip('-'): v for k, v in zip(opt[::2], opt[1::2])}, log=lambda *_: None)
    if sec is None:
        raise SystemExit('%s: kl_fa_fedbody refused (see its log)' % m)
    shutil.copyfile(os.path.join(tmp, 'KLJoin.ini'), os.path.join(folder, 'KLJoin.ini'))
    shutil.copyfile(os.path.join(tmp, 'fedbody.txt'), os.path.join(folder, 'fedbody.txt'))
    shutil.rmtree(tmp)
    new = md5(os.path.join(folder, 'KLJoin.ini'))
    if md5(live) != zmd5:
        raise SystemExit('%s: the live zip changed while staging, run again' % m)
    manifest(folder, m, [dict(n=zipname, md5=zmd5)], [dict(n='KLJoin.ini', old=old, new=new)],
             dict(entries=sec['Entries'], root=sec['Root'], variants=sec.get('Variants'), look=look, sure=sure, zip_md5=zmd5))
    log('%-8s zip %s  ini %s -> %s  Entries=%s Root=%s Variants=%s  (%s)' % (m, zmd5[:8], (old or 'absent')[:8], new[:8], sec['Entries'], sec['Root'], sec.get('Variants'), look))
    return dict(m=m, zip=zmd5, ini_old=old, ini_new=new, entries=sec['Entries'], root=sec['Root'], look=look, sure=sure)


def stage_graft(out, log):
    m, zipname, look, sure = GRAFT
    live = os.path.join(MAPS_DIR, m, zipname)
    zmd5 = md5(live)
    folder = os.path.join(out, m, 'stage')
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    import kl_fedoutfit_dm05a as G
    G.build(live, os.path.join(folder, zipname), pin=zmd5[:8], log=log)
    if md5(live) != zmd5:
        raise SystemExit('%s: the live zip changed while staging, run again' % m)
    new = md5(os.path.join(folder, zipname))
    manifest(folder, m, [], [dict(n=zipname, old=zmd5, new=new)], dict(look=look, sure=sure, zip_md5=zmd5))
    log('%-8s zip %s -> %s (graft)  (%s)' % (m, zmd5[:8], new[:8], look))
    return dict(m=m, zip=zmd5, zip_new=new, look=look, sure=sure)


def ps(args, log, ok=(0,)):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass'] + args, capture_output=True, text=True)
    log('    ' + (r.stdout.strip() + r.stderr.strip()).replace('\n', '\n    '))
    return r.returncode


def tree_md5(root, maps):
    return {os.path.join(m, f): md5(os.path.join(root, m, f)) for m in maps for f in sorted(os.listdir(os.path.join(root, m)))
            if os.path.isfile(os.path.join(root, m, f))}


def rehearse(out, rows, log):
    """Scratch game folder (hard links to the live files; the scripts only rename / remove / create directory entries): install, again,
    dry-run undo, undo; every file must be byte identical afterwards. Plus two refusals: a pinned zip that differs, an ini that differs."""
    scratch = os.path.join(out, 'rehearse')
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    game = os.path.join(scratch, 'Game')
    maps = [r['m'] for r in rows]
    for m in maps:
        d = os.path.join(game, 'KLExpansion', 'Maps', m)
        os.makedirs(d)
        for f in os.listdir(os.path.join(MAPS_DIR, m)):
            a = os.path.join(MAPS_DIR, m, f)
            if os.path.isfile(a) and '.before-' not in f and f.lower().endswith(('.zip', '.ini')):
                if f.lower().endswith('.ini'):
                    shutil.copyfile(a, os.path.join(d, f))
                else:
                    os.link(a, os.path.join(d, f))
    open(os.path.join(game, 'kl2.exe'), 'wb').write(b'MZ')
    root = os.path.join(game, 'KLExpansion', 'Maps')
    before = tree_md5(root, maps)
    live_before = {m: md5(os.path.join(MAPS_DIR, m, z)) for m, z in ((r['m'], [x for x in os.listdir(os.path.join(MAPS_DIR, r['m'])) if x.endswith('_Main.zip')][0]) for r in rows)}
    allps = os.path.join(out, 'fedoutfit_all.ps1')
    base = ['-File', allps, '-Game', game, '-Rehearsal']
    fails = []
    def step(name, extra, want):
        log('  rehearsal: ' + name)
        rc = ps(base + extra, log)
        if rc != want:
            fails.append('%s: exit %d, wanted %d' % (name, rc, want))
    step('install dry run', ['-DryRun'], 0)
    if tree_md5(root, maps) != before:
        fails.append('dry run changed files')
    step('install', [], 0)
    after = tree_md5(root, maps)
    if after == before:
        fails.append('install changed nothing')
    step('install again (already installed)', [], 0)
    if tree_md5(root, maps) != after:
        fails.append('second install changed files')
    step('undo dry run', ['-Undo', '-DryRun'], 0)
    step('undo', ['-Undo'], 0)
    back = tree_md5(root, maps)
    left = [os.path.join(m, f) for m in maps for f in os.listdir(os.path.join(root, m)) if 'fedoutfit' in f or f.endswith('.tmp1025fo')]
    if back != before:
        fails.append('undo is not byte identical: %s' % sorted(set(back.items()) ^ set(before.items()))[:4])
    if left:
        fails.append('left over after undo: %s' % left)
    step('undo again (already undone)', ['-Undo'], 0)
    # refusals: a map whose pinned zip is not the one built for / whose ini changed in between: SKIP (4), nothing changed, other maps go
    m0 = next((r['m'] for r in rows if r.get('ini_old')), rows[0]['m'])
    ini0 = os.path.join(root, m0, 'KLJoin.ini')
    if os.path.isfile(ini0):
        open(ini0, 'a').write('; changed in between\n')
        mod = tree_md5(root, maps)
        step('install with a changed live ini (map %s must SKIP)' % m0, [], 4)
        now = tree_md5(root, maps)
        if now[os.path.join(m0, 'KLJoin.ini')] != mod[os.path.join(m0, 'KLJoin.ini')]:
            fails.append('SKIP still changed the ini of ' + m0)
    shutil.rmtree(scratch)
    live_after = {m: md5(os.path.join(MAPS_DIR, m, [x for x in os.listdir(os.path.join(MAPS_DIR, m)) if x.endswith('_Main.zip')][0])) for m in maps}
    if live_after != live_before:
        fails.append('LIVE zip md5 changed during the rehearsal!')
    log('rehearsal: %s' % ('PASS' if not fails else 'FAIL ' + '; '.join(fails)))
    return fails


def verify(out, log=print):
    """Is every stage still built for the live files? 0 = all current."""
    bad = 0
    for r in json.load(open(os.path.join(out, 'stage.json'))):
        m = r['m']
        zipname = [x for x in os.listdir(os.path.join(MAPS_DIR, m)) if x.endswith('_Main.zip')][0]
        cur = md5(os.path.join(MAPS_DIR, m, zipname))
        ini = os.path.join(MAPS_DIR, m, 'KLJoin.ini')
        ini_now = md5(ini) if os.path.isfile(ini) else None
        done = cur == r.get('zip_new') or ini_now == r.get('ini_new')
        ok = done or (cur == r['zip'] and (r.get('ini_old', ini_now) == ini_now))
        log('%-8s %s  zip %s (built for %s)%s' % (m, 'INSTALLED' if done else ('current' if ok else 'STALE - rebuild'), cur[:8], r['zip'][:8],
                                                  '' if 'ini_old' not in r or ini_now in (r['ini_old'], r['ini_new']) else '  ini %s (built for %s)' % ((ini_now or 'absent')[:8], (r['ini_old'] or 'absent')[:8])))
        bad += not ok
    return bad


def main():
    a = sys.argv[1:]
    if a[:1] == ['verify']:
        return 1 if verify(a[a.index('--out') + 1] if '--out' in a else DEFAULT_OUT) else 0
    out = a[a.index('--out') + 1] if '--out' in a else DEFAULT_OUT
    only = a[a.index('--only') + 1].split(',') if '--only' in a else None
    lines = []
    def log(s=''):
        print(s); lines.append(str(s))
    os.makedirs(out, exist_ok=True)
    rows = []
    if not (only and 'DM05A' not in only) and '--no-graft' not in a:
        rows.append(stage_graft(out, log))
    for m, z, opt, look, sure in HOOK:
        if only and m not in only:
            continue
        rows.append(stage_hook(out, m, z, opt, look, sure, log))
    order = [r['m'] + '\\stage' for r in rows]
    write(os.path.join(out, 'maps.txt'), '\n'.join(order) + '\n')
    shutil.copyfile(os.path.join(HERE, 'kl_fedoutfit_all.ps1'), os.path.join(out, 'fedoutfit_all.ps1'))
    for label, arg in (('INSTALL', ''), ('UNDO', ' -Undo')):
        write(os.path.join(out, '%s-ALL.bat' % label),
              '@echo off\ncd /d "%%~dp0"\npowershell -NoProfile -ExecutionPolicy Bypass -File "%%~dp0fedoutfit_all.ps1"%s\npause\n' % arg)
    write(os.path.join(out, 'live_md5.txt'), ''.join('%s %s%s\n' % (r['m'], r['zip'], ' (graft: new %s)' % r['zip_new'] if 'zip_new' in r else '') for r in rows))
    with open(os.path.join(out, 'stage.json'), 'w') as f:
        json.dump(rows, f, indent=1)
    fails = [] if '--no-rehearse' in a else rehearse(out, rows, log)
    with open(os.path.join(out, 'stage.log'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
