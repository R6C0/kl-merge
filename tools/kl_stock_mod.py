#!/usr/bin/env python3
"""
The nine STOCK Fragile Alliance maps of Dog Days with the mods the Dead Men maps have (owner, 2026-10-10:
'also want the original FA dog days maps to have these mods in the game too so its changed all around makes
it a bit more fresh'). Offline: nothing here installs anything, starts the game or writes into the Dog Days
folder. Spec and results: re/stock_mod.md.

    python kl_stock_mod.py build F02 [<out root>] [--plates=wolf,dallas,chains,hoxton] [--no-guns] [--start=1] [--set=1]
    python kl_stock_mod.py all [<out root>] [F01 F02 ...] [same options]      default: all nine -> G:/kl_scratch/stock_mod
    python kl_stock_mod.py table [<out root>]                                 what each folder holds and costs

WHAT A MAP GETS (each step is another tool, run as its own command; this file changes none of them)
  1 wardrobe   tools/kl_chars.py wardrobe <Fnn> ... --plates=...   the eight Dead Men heisters as bodies, 8 Dog Days
               masks + the Payday 2 plates, the outfits: what the Heister page picks from (KLWardrobe.ini beside the
               archive). Seen live on stock F01 (<work>/build/pd2/pd2_F01) and on every Dead Men map.
  2 guns       tools/kl_map_guns.py build   the six Dead Men gun looks, baked, fitted to the Dog Days hold, with their
               class's sound (KLGuns.ini). Seen live on Retomoto; the enemies who carry those six guns show them too.
  ('--no-audit': kl_maps.audit measures a GRAFTED map against its systems level; on a stock level it compares the
  sound bank with the wrong base and reports ten sound findings, although the gun step proves it left .SND, .ANM and
  .fxc byte for byte alone. The gun step's own checks and `kl_map_guns.py check` on the written folder still run.)
  The stock archive is READ (tools find it under KL_PortBackup when its slot holds a build of ours); the result is a
  folder of its own. NOTHING OF THE MAP ITSELF CHANGES: its police, waves, loot, escape and AI heisters are stock's.

WHAT A MAP DOES NOT GET, AND WHY
  - Retomoto's soldier rows / skill by weapon: stock's police ARE those rows (kl_arms.ROWS was copied from them).
  - fall-back chains, elevator trigger, straightened van: authored for Retomoto's street, object by object. A stock map
    has its own designed waves; nothing generic was found that would not just be a guess per level.
  What else changes a stock round comes from the HOOK and so applies to every map without a build: random crew bodies,
  the AI heisters' tuning, talk (klhook; kl-merge-01's parts).

DELIVERY (not done here; the owner's and kl-merge-01's call): a modified stock map goes into its own folder under
KLExpansion/Maps with a [Redirect] line - no stock file is replaced. The hook's Steam guard treats such a map as NOT
stock: rounds on it write no stats, achievements or leaderboard scores. Online, every player needs the same build.
"""
import json, os, shutil, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
LEVELS = ['F0%d' % i for i in range(1, 10)]
OUT = 'G:/kl_scratch/stock_mod'
PLATES = 'wolf,dallas,chains,hoxton'
BUDGET = ('.prm', '.ANM', '.fxc', '.TEX')


def run(args, log):
    r = subprocess.run([sys.executable] + args, capture_output=True, text=True, cwd=HERE)
    with open(log, 'a', encoding='utf-8', errors='replace') as f:
        f.write('\n$ python %s\n%s%s\n(exit %d)\n' % (' '.join(args), r.stdout, r.stderr, r.returncode))
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()


def sizes(folder, slot):
    out = {}
    z = os.path.join(folder, slot + '_Main.zip')
    with zipfile.ZipFile(z) as f:
        for i in f.infolist():
            ext = '.' + i.filename.rsplit('.', 1)[-1]
            if ext in BUDGET:
                out[ext] = i.file_size
    wav = os.path.join(folder, slot + '_Main.WAV')
    out['.WAV'] = os.path.getsize(wav) if os.path.isfile(wav) else 0
    out['zip'] = os.path.getsize(z)
    return out


def stock_sizes(level):
    sys.path.insert(0, HERE)
    import kl_prpjoin as J
    z = J.level_zip(level)
    out = {}
    with zipfile.ZipFile(z) as f:
        for i in f.infolist():
            ext = '.' + i.filename.rsplit('.', 1)[-1]
            if ext in BUDGET:
                out[ext] = i.file_size
    wav = z[:-4] + '.WAV'
    out['.WAV'] = os.path.getsize(wav) if os.path.isfile(wav) else 0
    out['zip'] = os.path.getsize(z)
    return out


def build(level, root=OUT, plates=PLATES, guns=True, start=1, sets=1, log=print):
    """One stock level -> <root>/<level> (wardrobe + plates + gun looks). -> report dict; ['ok']."""
    work, final = os.path.join(root, '_work', level), os.path.join(root, level)
    for d in (work, final):
        if os.path.isdir(d):
            shutil.rmtree(d)
    os.makedirs(work)
    logf = os.path.join(root, level + '.log')
    if os.path.isfile(logf):
        os.remove(logf)
    rep = {'level': level, 'steps': [], 'ok': False, 'stock': stock_sizes(level)}
    w = os.path.join(work, '1_wardrobe')
    rc, out = run(['kl_chars.py', 'wardrobe', level, w, '--slot=' + level] + (['--plates=' + plates] if plates else []), logf)
    rep['steps'].append({'step': 'wardrobe', 'exit': rc, 'last': out[-1:] and out[-1][:300]})
    log('  %s wardrobe: exit %d  %s' % (level, rc, out[-1][:200] if out else ''))
    if rc:
        return rep
    last = w
    if guns:
        g = os.path.join(work, '2_guns')
        rc, out = run(['kl_map_guns.py', 'build', w, g, '--start=%d' % start, '--set=%d' % sets, '--no-audit'], logf)
        tail = [l for l in out if 'RESULT' in l or 'problems' in l.lower()][-2:]
        rep['steps'].append({'step': 'guns', 'exit': rc, 'last': tail})
        log('  %s guns: exit %d  %s' % (level, rc, ' | '.join(t[:160] for t in tail)))
        if rc:
            return rep
        last = g
        rc, out = run(['kl_map_guns.py', 'check', g], logf)
        rep['steps'].append({'step': 'guns check', 'exit': rc, 'last': out[-1:] and out[-1][:300]})
        if rc:
            log('  %s guns check: exit %d  %s' % (level, rc, out[-1][:200] if out else ''))
            return rep
    shutil.move(last, final)
    rep['sizes'] = sizes(final, level)
    rep['side'] = sorted(f for f in os.listdir(final) if f.lower().endswith(('.ini', '.json')))
    rep['ok'] = True
    with open(os.path.join(final, 'stock_mod.json'), 'w') as f:
        json.dump(rep, f, indent=1)
    s, t = rep['stock'], rep['sizes']
    log('  %s: PASS  .prm %.1f -> %.1f MB, .TEX %.1f -> %.1f, .ANM %.1f, .fxc %.1f, .WAV %.1f; %s' % (
        level, s['.prm'] / 1e6, t['.prm'] / 1e6, s['.TEX'] / 1e6, t['.TEX'] / 1e6, t['.ANM'] / 1e6, t['.fxc'] / 1e6, t['.WAV'] / 1e6, ', '.join(rep['side'])))
    return rep


def table(root=OUT, log=print):
    log('| map | .prm stock -> now (MB) | .TEX | .ANM | .fxc | .WAV | archive (MB) | beside it |')
    log('|---|---|---|---|---|---|---|---|')
    for lv in LEVELS:
        p = os.path.join(root, lv, 'stock_mod.json')
        if not os.path.isfile(p):
            log('| %s | not built | | | | | | |' % lv)
            continue
        r = json.load(open(p))
        s, t = r['stock'], r['sizes']
        log('| %s | %.1f -> %.1f | %.1f -> %.1f | %.1f | %.1f | %.1f | %.0f -> %.0f | %s |' % (
            lv, s['.prm'] / 1e6, t['.prm'] / 1e6, s['.TEX'] / 1e6, t['.TEX'] / 1e6, t['.ANM'] / 1e6, t['.fxc'] / 1e6, t['.WAV'] / 1e6,
            s['zip'] / 1e6, t['zip'] / 1e6, ', '.join(x for x in r['side'] if x.endswith('.ini'))))


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = {x.split('=')[0]: (x.split('=') + [''])[1] for x in sys.argv[1:] if x.startswith('--')}
    kw = dict(plates=opt.get('--plates', PLATES), guns='--no-guns' not in opt, start=int(opt.get('--start', 1)), sets=int(opt.get('--set', 1)))
    if a[:1] == ['build'] and len(a) >= 2:
        r = build(a[1], a[2] if len(a) > 2 else OUT, **kw)
        print('RESULT: %s' % ('PASS' if r['ok'] else 'FAIL'))
        sys.exit(0 if r['ok'] else 1)
    elif a[:1] == ['all']:
        rest = a[1:]
        root = rest.pop(0) if rest and rest[0] not in LEVELS else OUT
        os.makedirs(root, exist_ok=True)
        res = [build(lv, root, **kw) for lv in (rest or LEVELS)]
        table(root)
        bad = [r['level'] for r in res if not r['ok']]
        print('RESULT: %s' % ('PASS' if not bad else 'FAIL (%s)' % ', '.join(bad)))
        sys.exit(1 if bad else 0)
    elif a[:1] == ['table']:
        table(a[1] if len(a) > 1 else OUT)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
