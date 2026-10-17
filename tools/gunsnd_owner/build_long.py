"""snd7: like snd2's build_banks, but the gun clips keep their NATURAL length (no cut to the stock length): longer clips are
appended to the .WAV, the .WHD record points at them, and the .SND wave objects' seconds (+0x18) are updated in the zip.
TMP (the game's original) and the distant layers keep the stock length.
usage: build_long.py <clips> <out root>"""
import sys, os, subprocess, zipfile, numpy as np
TOOLS = os.path.expanduser('~/mnt/kl-merge/kl-merge/tools'); sys.path.insert(0, TOOLS)
import kl_gunsnd as G
from kl_hud_menu import _rezip
MAPS = os.path.expanduser('~/mnt/Kane & Lynch 2 - Dog Days/KLExpansion/Maps')
CLIPS, OUT = sys.argv[1], sys.argv[2]
LONG = ['SMG_Type79_Shot_0%d' % i for i in (1, 2, 3)] + ['Rifle_AK74_Shot_0%d' % i for i in (1, 2, 3)] + \
       ['SMG_MPI69_Shot_0%d' % i for i in (1, 2, 3)] + ['HG_M9Beretta_Shot_0%d' % i for i in (1, 2, 3)]
SHORT = ['SMG_MAC_10_Shot_0%d' % i for i in (1, 2, 3)]
RECS = {t: 'SFX/Weapons_KL2_Final/%s/%s.wav' % (t.rsplit('_Shot', 1)[0], t) for t in LONG + SHORT}
RECS['Distant_Shot_HandGuns_01'] = 'SFX/Weapons_KL2_Final/Common/Distant_Shots/HandGuns/Distant_Shot_HandGuns_01.wav'
RECS['Distant_Shot_SubMachineGuns_01'] = 'SFX/Weapons_KL2_Final/Common/Distant_Shots/SubMachineGuns/Distant_Shot_SubMachineGuns_01.wav'
def natural(y, r, floor_db=-42.0, maxs=1.3):
    y = y[:int(maxs * r)].copy(); a = np.abs(y); W = int(0.01 * r)
    e = np.array([a[i:i + W].max() for i in range(0, len(a) - W, W)]); edb = 20 * np.log10(e + 1e-9) - 20 * np.log10(a.max())
    above = np.where(edb > floor_db)[0]; n = min(len(y), (above[-1] + 1) * W + int(0.05 * r) if len(above) else len(y))
    y = y[:n]; f = min(int(0.08 * r), n // 3); y[n - f:] *= np.linspace(1, 0, f) ** 2; return y
def fit(y, n, r):
    y = y[:n].copy(); y = np.pad(y, (0, n - len(y))); fd = min(int(0.3 * n), int(0.12 * r)); y[n - fd:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, fd))); return y
for m in (sys.argv[3].split(',') if len(sys.argv) > 3 else ['DM01', 'DM02', 'DM03', 'DM03A', 'DM05A', 'DM06', 'DM09', 'T01']):
    d = os.path.join(MAPS, m); whd = [f for f in os.listdir(d) if f.endswith('_Main.WHD')][0]; slot = whd[:3]
    base = os.path.join(d, whd); zp = os.path.join(d, slot + '_Main.zip')
    z = zipfile.ZipFile(zp); sndname = [n for n in z.namelist() if n.lower().endswith('_main.snd')][0]
    od = os.path.join(OUT, m); fdir = os.path.join(od, 'clips'); os.makedirs(fdir, exist_ok=True)
    sndp = os.path.join(od, 'orig_' + os.path.basename(sndname)); open(sndp, 'wb').write(z.read(sndname))
    ws = {w.name.lower(): w for w in G.waves(open(base, 'rb').read())}; lines = []
    for tag, name in RECS.items():
        w = ws[name.lower()]; r = w.get('rate'); x, rr = G.read_wav(os.path.join(CLIPS, tag + '.wav')); assert rr == r
        y = natural(x[:, 0], r) if tag in LONG else fit(x[:, 0], w.get('samples'), r)
        p = os.path.join(fdir, tag + '.wav'); G.write_wav(p, G.to_i16(y[:, None]), r); lines.append('%s = %s' % (name, p))
    mp = os.path.join(od, 'map.txt'); open(mp, 'w').write('\n'.join(lines) + '\n')
    rc = subprocess.run([sys.executable, '-I', os.path.join(TOOLS, 'kl_gunsnd.py'), 'replace', base, od, mp, '--snd', sndp], capture_output=True, text=True)
    print('==', m, rc.stdout.count('appended'), 'appended,', rc.stdout.count('in place'), 'in place;', [l for l in rc.stdout.splitlines() if l.startswith('verify')], rc.stderr[-500:])
    assert rc.returncode == 0
    newsnd = open(os.path.join(od, os.path.basename(sndp)), 'rb').read()
    _rezip(zp, os.path.join(od, slot + '_Main.zip'), {sndname.lower(): newsnd})
    print('   zip written; .SND changed bytes:', sum(1 for a, b in zip(newsnd, z.read(sndname)) if a != b), 'size same:', len(newsnd) == len(z.read(sndname)))
