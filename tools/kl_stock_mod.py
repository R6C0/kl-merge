#!/usr/bin/env python3
"""
The nine STOCK Fragile Alliance maps of Dog Days with the mods the Dead Men maps have (owner, 2026-10-10:
'also want the original FA dog days maps to have these mods in the game too so its changed all around makes
it a bit more fresh'). Offline: nothing here installs anything, starts the game or writes into the Dog Days
folder. Spec and results: re/stock_mod.md.

    python kl_stock_mod.py build F02 [<out root>] [--plates=wolf,dallas,chains,hoxton] [--no-guns] [--start=1] [--set=1]
    python kl_stock_mod.py all [<out root>] [F01 F02 ...] [same options]      default: all nine -> G:/kl_scratch/stock_mod
    python kl_stock_mod.py gunsnd [<out root>] [F01 ...|all] [--no-zastava]   the owner's gun-sound set + Zastava->MP5 shots, in place
    python kl_stock_mod.py package [<out root>] [F01 ...|all] [--dest=<dir>] [--copy]   Maps/DDnn + BuildInfo/DDnn (hard links unless --copy)
    python kl_stock_mod.py testslot [<out root>] F06 [--dest=<dir>]   Maps/T06 = Maps/DD06 built for slot F01 (the only slot -o DefaultScene boots)
    python kl_stock_mod.py table [<out root>]                             what each folder holds and costs

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


def build(level, root=OUT, plates=PLATES, guns=True, start=1, sets=1, log=print, hud=True):
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
    if hud:      # the owner's HUD look baked into the archive (2026-10-18): the hook's weapon dial / round dials / crew plates need these pictures (klhud_weapon.c: 'the level has no picture 113 / 114')
        h = os.path.join(work, '3_hud')
        rc, out = run(['kl_hud.py', 'all', last, h, '--look', 'deadmen'], logf)
        tail = [l for l in out if l.startswith('check:')][-1:]
        rep['steps'].append({'step': 'hud', 'exit': rc, 'last': tail})
        log('  %s hud: exit %d  %s' % (level, rc, ' | '.join(tail)))
        if rc or not tail or 'PASS' not in tail[0]:
            return rep
        last = h
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


# ------------------------------------------------------------------------------------------------ gun sounds (step 3)
# The owner's gun-sound set (tools/gunsnd_owner/make_v6.py + build_long.py, re/gun_sounds.md), applied to a stock overlay
# map's own bank (<Fnn>_Main.WHD/.WAV beside the zip, .SND inside it): his M4 recordings on Rifle_AK74_Shot_01..03, MP5 on
# SMG_Type79, P90 on SMG_MPI69, USP (Dead Men Shot_Usp) on HG_M9Beretta, TMP (stock) on SMG_MAC_10, the two distant layers.
# Clips = the 17 files the installed DM banks were built from (build/snd11/*/clips, identical in every map; copied once to
# <root>/gunsnd_clips). LONG ones keep their natural length (record appended to the .WAV, .SND wave seconds rewritten, as
# build_long.py); SHORT ones and the distant layers are fitted to the record's own stock length (build_long.py fit()).
# The Zastava M85's three shot sounds are repointed at SMG_Type79's wave objects (kl_gunsnd.repoint_snd, same as
# build/zast_1017/run.py): the Zastava then uses the MP5 shots.
CLIPS_SRC = 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/snd11/DM01/clips'
LONG = ['SMG_Type79_Shot_0%d' % i for i in (1, 2, 3)] + ['Rifle_AK74_Shot_0%d' % i for i in (1, 2, 3)] + \
       ['SMG_MPI69_Shot_0%d' % i for i in (1, 2, 3)] + ['HG_M9Beretta_Shot_0%d' % i for i in (1, 2, 3)]
SHORT = ['SMG_MAC_10_Shot_0%d' % i for i in (1, 2, 3)]
DIST = {'Distant_Shot_HandGuns_01': 'SFX/Weapons_KL2_Final/Common/Distant_Shots/HandGuns/Distant_Shot_HandGuns_01.wav',
        'Distant_Shot_SubMachineGuns_01': 'SFX/Weapons_KL2_Final/Common/Distant_Shots/SubMachineGuns/Distant_Shot_SubMachineGuns_01.wav'}


def _fit(y, n, r):
    import numpy as np
    y = y[:n].copy(); y = np.pad(y, (0, n - len(y))); fd = min(int(0.3 * n), int(0.12 * r))
    y[n - fd:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, fd))); return y


def gunsnd(level, root=OUT, zastava=True, log=print):
    """Apply the owner's gun-sound set to <root>/<level>. -> report dict (['ok'], md5s, checks). Rewrites the folder's
    <level>_Main.WHD/.WAV/.zip in place (new files are written beside them, checked, then moved over)."""
    import hashlib, numpy as np
    sys.path.insert(0, HERE)
    import kl_gunsnd as G
    from kl_hud_menu import _rezip
    folder = os.path.join(root, level); whdp = os.path.join(folder, level + '_Main.WHD')
    wavp, zp = whdp[:-4] + '.WAV', os.path.join(folder, level + '_Main.zip')
    cdir = os.path.join(root, 'gunsnd_clips')
    if not os.path.isdir(cdir):
        shutil.copytree(CLIPS_SRC, cdir)
    whd, wav = open(whdp, 'rb').read(), open(wavp, 'rb').read()
    z = zipfile.ZipFile(zp)
    nm = [n for n in z.namelist() if n.upper().endswith('.SND') and not n.upper().endswith('_LS.SND')]
    assert len(nm) == 1, nm
    nm = nm[0]; snd = z.read(nm)
    ws = {w.name.lower(): w for w in G.waves(whd)}
    recs = {t: 'SFX/Weapons_KL2_Final/%s/%s.wav' % (t.rsplit('_Shot', 1)[0], t) for t in LONG + SHORT}
    recs.update(DIST)
    repl, srcs = {}, {}
    for tag, name in recs.items():
        w = ws[name.lower()]; r = w.get('rate'); x, rr = G.read_wav(os.path.join(cdir, tag + '.wav')); assert rr == r, (tag, rr, r)
        y = x[:, 0] if tag in LONG else _fit(x[:, 0], w.get('samples'), r)
        y16 = G.to_i16(y[:, None]); srcs[w.rec_off] = (w.name, y16[:, 0] / 32768.0)
        data, ns, pcmb = G.encode_for(w, y16 / 32768.0, r)
        repl[w.rec_off] = (data, ns, pcmb, ns / w.get('rate'))
    nwhd, nwav, nsnd = G.rebuild(whd, wav, repl, snd, log=lambda *a: None)
    zlog = []
    if zastava:
        nsnd, zlog = G.repoint_snd(nsnd, 'rifle_zastavam85', 'smg_type79')
    chk = {}
    ow, nw = G.waves(whd), G.waves(nwhd)
    chk['records'] = (len(ow), len(nw)); assert len(ow) == len(nw)
    assert [w.name for w in ow] == [w.name for w in nw]
    tgt = set(repl)
    for a, b in zip(ow, nw):
        if a.rec_off not in tgt:
            assert a.f == b.f, a.name                        # untouched records: every field the same
        else:
            changed = [k for k in G.F if a.get(k) != b.get(k)]
            assert set(changed) <= {'off', 'size', 'samples', 'pcm', 'offhi'}, (a.name, changed)
    assert len(nwhd) == len(whd)
    diffw = [i for i in range(len(whd)) if whd[i] != nwhd[i]]
    spans = [(r, r + G.REC) for r in tgt]
    assert all(any(a <= i < b for a, b in spans) for i in diffw), 'WHD bytes changed outside the target records'
    olds = [(w.get('off'), w.get('off') + w.get('size')) for w in ow if w.rec_off in tgt]
    bad = [i for i in range(8, len(wav)) if wav[i] != nwav[i] and not any(a <= i < b for a, b in olds)]
    assert not bad, 'WAV changed outside the old spans of replaced clips (%d bytes)' % len(bad)
    cors = []
    for w in nw:
        if w.rec_off in tgt:
            nm_, s = srcs[w.rec_off]; d = G.decode_wave(nwav, w)[:, 0]; n = min(len(d), len(s))
            c = float(np.corrcoef(d[:n], s[:n])[0, 1]); cors.append((nm_.rsplit('/', 1)[-1], round(c, 5)))
            assert len(d) == w.get('samples')
    chk['min_corr'] = min(c for _, c in cors); chk['clips'] = len(cors)
    assert chk['min_corr'] >= 0.99, cors
    assert len(nsnd) == len(snd)                              # .SND: only target waves' seconds floats + zastava pointers
    so = G.snd_wave_objects(snd); allow = set()
    for ro in tgt:
        for wo, _ in so.get(ro, []):
            allow.add(wo + 0x18)
    zo = {n_: o for n_, o in G.snd_sound_objects(snd).items() if '/rifle_zastavam85/rifle_zastavam85_shot_0' in n_ and n_.endswith('#sound')}
    if zastava:
        assert len(zo) == 3; allow |= {o + 0x14 for o in zo.values()}
    sd = sorted({i & ~3 for i in range(len(snd)) if snd[i] != nsnd[i]})
    assert set(sd) <= allow, [hex(i) for i in sd if i not in allow][:10]
    chk['snd_dwords_changed'] = len(sd); chk['zastava_repointed'] = len(zlog)
    tz = zp + '.new'
    _rezip(zp, tz, {nm.lower(): nsnd})
    a, b = zipfile.ZipFile(zp), zipfile.ZipFile(tz)
    assert [i.filename for i in a.infolist()] == [i.filename for i in b.infolist()]
    for i in a.infolist():
        assert a.getinfo(i.filename).compress_type == b.getinfo(i.filename).compress_type
        if i.filename != nm:
            assert a.read(i.filename) == b.read(i.filename), i.filename
    assert b.read(nm) == nsnd
    a.close(); b.close(); z.close()
    open(whdp + '.new', 'wb').write(nwhd); open(wavp + '.new', 'wb').write(nwav)
    for p_ in (whdp, wavp, zp):
        os.replace(p_ + '.new', p_)
    md5 = {}
    for f in (level + '_Main.zip', level + '_Main.WHD', level + '_Main.WAV'):
        h = hashlib.md5()
        with open(os.path.join(folder, f), 'rb') as fh:
            for c in iter(lambda: fh.read(1 << 22), b''):
                h.update(c)
        md5[f] = h.hexdigest()
    rep = {'level': level, 'ok': True, 'md5': md5, 'checks': chk, 'wav_bytes': (len(wav), len(nwav)), 'corr': cors,
           'zastava': [(n_, hex(o), hex(w)) for n_, o, w in zlog]}
    sj = os.path.join(folder, 'stock_mod.json')
    try:
        j = json.load(open(sj)); j['gunsnd'] = {k: v for k, v in rep.items() if k != 'corr'}; json.dump(j, open(sj, 'w'), indent=1)
    except Exception:
        pass
    log('  %s gunsnd: PASS %d clips, min corr %.4f, WAV %d -> %d, .SND dwords %d, zastava %d, zip %s' % (
        level, chk['clips'], chk['min_corr'], len(wav), len(nwav), len(sd), len(zlog), md5[level + '_Main.zip']))
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


# ---------------------------------------------------------------- step 3: the expansion folders (2026-10-17)
# Overlay map id DDnn = stock Fnn with the mods. The folder is what the hook's [Redirect] reads: KLExpansion\Maps\DDnn\ holds
# Fnn_Main.zip and every file beside it that the engine or the hook opens. Why this is NOT kl_expansion.adopt()/EXTRA: adopt
# wants a kl_maps build (result.json), re-packs the zip under another slot name (here the slot is already Fnn: nothing to
# rename, and a re-pack would change the bytes the gun-sound step just verified) and EXTRA entries become menu-page entries
# with a title and picture (the DD maps have no page of their own: page-0 [Redirect] serves the STOCK menu page).
# The notes (chars.json, guns.json, map_guns.json, stock_mod.json) stay in BuildInfo\DDnn, like adopt()'s info folder.
SIDE_FILES = ('KLWardrobe.ini', 'KLGuns.ini')          # the hook's per-map files this build makes (KLJoin.ini / KLTalk.ini: none exist for a stock map)
NOTES = ('chars.json', 'guns.json', 'map_guns.json', 'stock_mod.json')


def _sha1(path):
    import hashlib
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def package(level, root, dest, link=True, log=print):
    r"""root\<level> -> dest\Maps\DD<nn> (files the game opens) + dest\BuildInfo\DD<nn> (notes). Hard links when `link` and
    the volume allows (no second 250 MB per map on the nearly full G:), else a checked copy. Reads the folder only.
    Checks: one *_Main.zip named <level>_Main.zip; the zip/.WHD/.WAV md5 equal the gun-sound step's record; KLGuns.ini
    Version 2 with Entries = the .prm chunk count; KLWardrobe.ini present. -> {file: [bytes, sha1]} of Maps\DDnn."""
    src = os.path.join(root, level)
    mid = 'DD' + level[1:]
    rec = json.load(open(os.path.join(src, 'stock_mod.json')))
    if not rec.get('ok') or not rec.get('gunsnd', {}).get('ok'):
        raise SystemExit('%s: stock_mod.json says the build or the gun-sound step is not ok' % src)
    names = sorted(f for f in os.listdir(src) if f.startswith(level + '_Main') and os.path.isfile(os.path.join(src, f)))
    if level + '_Main.zip' not in names:
        raise SystemExit('%s: no %s_Main.zip' % (src, level))
    for f in SIDE_FILES:
        if not os.path.isfile(os.path.join(src, f)):
            raise SystemExit('%s: %s missing' % (src, f))
    import hashlib
    for f, want in rec['gunsnd']['md5'].items():
        h = hashlib.md5()
        with open(os.path.join(src, f), 'rb') as fh:
            for b in iter(lambda: fh.read(1 << 22), b''):
                h.update(b)
        if h.hexdigest() != want:
            raise SystemExit('%s: %s is not the file the gun-sound step recorded (md5 %s, expected %s)' % (src, f, h.hexdigest(), want))
    txt = open(os.path.join(src, 'KLGuns.ini'), encoding='latin-1').read()
    if 'Version=2' not in txt or not any(l.startswith('Entries=') for l in txt.splitlines()):
        raise SystemExit('%s: KLGuns.ini is not Version 2 with Entries=' % src)
    mp, ip = os.path.join(dest, 'Maps', mid), os.path.join(dest, 'BuildInfo', mid)
    for x in (mp, ip):
        shutil.rmtree(x, ignore_errors=True); os.makedirs(x)       # these are our own output folders
    out, linked = {}, 0
    for f in names + list(SIDE_FILES):
        s, d = os.path.join(src, f), os.path.join(mp, f)
        try:
            if not link:
                raise OSError
            os.link(s, d); linked += 1
        except OSError:
            shutil.copyfile(s, d)
        if os.path.getsize(s) != os.path.getsize(d):
            raise SystemExit('%s: size differs after the copy' % d)
        out[f] = [os.path.getsize(d), _sha1(d)]
    for f in NOTES:
        if os.path.isfile(os.path.join(src, f)):
            shutil.copyfile(os.path.join(src, f), os.path.join(ip, f))
    json.dump({'map': mid, 'slot': level, 'from': os.path.abspath(src), 'files': out}, open(os.path.join(ip, 'package.json'), 'w'), indent=1)
    log('%s <- %s: %d files, %.1f MB, %d hard-linked' % (mid, level, len(out), sum(v[0] for v in out.values()) / 1e6, linked))
    return out


def testslot(level, root, dest, slot='F01', log=print):
    r"""A copy of Maps\DDnn built for the F01 SLOT, as Maps\T<nn>: the Steam launch options (-o DefaultScene=Locations/F01/F01_Main.gms,
    never to be changed) boot slot F01 only, so any other stock map can be autotested only as 'F01 = this map'
    ([Redirect] F01=T<nn>). Same rename as kl_expansion.adopt(): member and file names only (kl_graft.member_name), the
    members' bytes are untouched (read back: same CRCs, same order). The sound/ini files are hard-linked under the new names.
    GUESS: nothing inside a level names its slot (adopt()'s docstring; proven for F07-systems grafts, not for a stock level).
    -> the folder."""
    import kl_graft, zipfile
    mp = os.path.join(dest, 'Maps', 'DD' + level[1:])
    tp = os.path.join(dest, 'Maps', 'T' + level[1:])
    shutil.rmtree(tp, ignore_errors=True); os.makedirs(tp)
    with zipfile.ZipFile(os.path.join(mp, level + '_Main.zip')) as z:
        members = [(kl_graft.member_name(n, level, slot), z.read(n)) for n in z.namelist()]
        crc = [(i.CRC, i.file_size) for i in z.infolist()]
    out = kl_graft.write_zip(os.path.join(tp, slot + '_Main.zip'), members, kl_graft.load_options(''))
    with zipfile.ZipFile(out) as z:
        if [(i.CRC, i.file_size) for i in z.infolist()] != crc:
            raise SystemExit('%s: the archive written for slot %s is not the folder\'s' % (level, slot))
    for f in sorted(os.listdir(mp)):
        if f == level + '_Main.zip':
            continue
        d = os.path.join(tp, slot + f[len(level):] if f.startswith(level + '_Main') else f)
        try:
            os.link(os.path.join(mp, f), d)
        except OSError:
            shutil.copyfile(os.path.join(mp, f), d)
    log('T%s <- %s as slot %s: %s' % (level[1:], level, slot, ', '.join(sorted(os.listdir(tp))[:4])) + ' ...')
    return tp


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    opt = {x.split('=')[0]: (x.split('=') + [''])[1] for x in sys.argv[1:] if x.startswith('--')}
    kw = dict(plates=opt.get('--plates', PLATES), guns='--no-guns' not in opt, hud='--no-hud' not in opt, start=int(opt.get('--start', 1)), sets=int(opt.get('--set', 1)))
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
    elif a[:1] == ['gunsnd']:
        rest = a[1:]
        root = rest.pop(0) if rest and rest[0] not in LEVELS and rest[0] != 'all' else OUT
        for lv in (LEVELS if rest in ([], ['all']) else rest):
            gunsnd(lv, root, zastava='--no-zastava' not in opt)
        print('RESULT: PASS')
    elif a[:1] == ['package']:
        rest = a[1:]
        root = rest.pop(0) if rest and rest[0] not in LEVELS and rest[0] != 'all' else OUT
        dest = opt.get('--dest', root)
        man = {}
        for lv in (LEVELS if rest in ([], ['all']) else rest):
            man['DD' + lv[1:]] = package(lv, root, dest, link='--copy' not in opt)
        json.dump(man, open(os.path.join(dest, 'Maps.manifest.json'), 'w'), indent=1)
        print('RESULT: PASS')
    elif a[:1] == ['testslot'] and len(a) >= 2:      # testslot [<root>] F06 : Maps\T06 beside Maps\DD06 (run package first)
        rest = a[1:]
        root = rest.pop(0) if rest and rest[0] not in LEVELS else OUT
        for lv in rest:
            testslot(lv, root, opt.get('--dest', root))
        print('RESULT: PASS')
    elif a[:1] == ['table']:
        table(a[1] if len(a) > 1 else OUT)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
