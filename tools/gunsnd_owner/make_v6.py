"""snd6 (owner 2026-10-16 19:02): P90 = his MP7 only; TMP = the game's ORIGINAL clips (stock bank, before heat);
USP = Dead Men's own Shot_Usp_01..03 (M01_FA_A bank); MP5 = his mp5_b / sp5_a / sp5_c (not mp5_a);
M4 = his four new recordings (m4_a..m4_d) with a light saturation 'distortion' tweak."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.expanduser('~/mnt/kl-merge/kl-merge/tools')); import kl_gunsnd as G, kl_whd as W
sys.path.insert(0, os.path.expanduser('~/work_snd5'))
R = 32000; OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
REF = os.path.expanduser('~/mnt/Kane and Lynch Dead Men/KL_PortTools/build/snd5/ref')
import importlib.util
spec = importlib.util.spec_from_file_location('mr', os.path.expanduser('~/work_snd5/make_ref.py'))
src = open(os.path.expanduser('~/work_snd5/make_ref.py')).read(); src = src[:src.index('P = []; info = []')]
ns = {'__file__': 'x', '__name__': 'mr'}; sys.argv_bak = sys.argv; sys.argv = ['x', '/tmp/claude_unused']; exec(compile(src, 'make_ref', 'exec'), ns); sys.argv = sys.argv_bak
rd, cut, norm, pitch, onsets, eq_hp = ns['rd'], ns['cut'], ns['norm'], ns['pitch'], ns['onsets'], ns['eq_hp']
P = []
def add(tag, desc, y, do_norm=True): P.append((tag, desc, norm(y) if do_norm else y))
def at(x, t, dur=1.2, nxt=None):
    a = max(0, int((t - 0.004) * R)); e = int((nxt - 0.012) * R) if nxt else a + int(dur * R)
    s = x[a:min(e, a + int(dur * R))].copy(); f = int(0.015 * R)
    if nxt and len(s) > f: s[-f:] *= np.linspace(1, 0, f)
    return np.pad(s, (0, int(dur * R) - len(s)))
def eqf(x, fn):
    n = 1 << int(math.ceil(math.log2(len(x) * 2))); X = np.fft.rfft(x, n); fr = np.fft.rfftfreq(n, 1 / R)
    return np.fft.irfft(X * 10 ** (fn(fr) / 20), n)[:len(x)]
def dirt(x, drive=2.5, mid_db=3.0):
    """the 'distortion' tweak: low-mid push (the owner's M4 recordings sit at 150-600 Hz) then a soft tanh clip"""
    x = eqf(x, lambda f: mid_db * np.exp(-0.5 * (np.log2(np.maximum(f, 1) / 320.0) * 1.5) ** 2))
    x = x / (np.abs(x).max() + 1e-12); return np.tanh(drive * x) / math.tanh(drive)
# MP5
mp5b, sp5a, sp5c, mp7 = (rd(os.path.join(REF, n + '.wav')) for n in ('mp5_b', 'sp5_a', 'sp5_c', 'mp7'))
def runon(x, nxt_rel, donor, dur=1.3, xf=0.03):
    # x, donor: cut at their onsets; x's next round at nxt_rel s -> crossfade into donor's tail, level-matched
    n = int(dur * R); x = np.pad(x[:n], (0, max(0, n - len(x)))); d = np.pad(donor[:n], (0, max(0, n - len(donor))))
    f = int(xf * R); c0 = int((nxt_rel - 0.006) * R) - f
    g = np.sqrt((x[c0 - int(0.02 * R):c0] ** 2).mean() / ((d[c0 - int(0.02 * R):c0] ** 2).mean() + 1e-12))
    w = np.concatenate([np.ones(c0), np.linspace(1, 0, f), np.zeros(n - c0 - f)]); return x * w + d * g * (1 - w)
# MP5 (owner 20:20: 'the only sound I hear on the MP5 is the bullet dropping'): the bang only - each shot's first 0.30 s
# (crack + room), then faded out by 0.55 s, so no shell / casing tail; mp5_b, sp5_a, sp5_b
def bang(x, keep=0.30, end=0.55):
    y0 = cut(x, dur=1.0)[0]; W = int(0.005 * R); e = [np.sqrt((y0[i:i + W] ** 2).mean()) for i in range(0, int(0.35 * R), W)]
    k0 = max(0, int(np.argmax(e)) * W - int(0.002 * R)); y = y0[k0:k0 + int(end * R)].copy(); y = np.pad(y, (0, int(end * R) - len(y)))
    k = int(keep * R); n = len(y)
    y[k:] *= np.linspace(1, 0, n - k) ** 2; return y
add('SMG_Type79_Shot_01', 'MP5: owner mp5_b, the bang only (0.30 s + fade to 0.55 s)', bang(mp5b))
add('SMG_Type79_Shot_02', 'MP5: owner sp5_a, the bang only', bang(sp5a))
add('SMG_Type79_Shot_03', 'MP5: owner sp5_b, the bang only', bang(rd(os.path.join(REF, 'sp5_b.wav'))))
# P90: MP7 only
add('SMG_MPI69_Shot_01', 'P90: owner MP7 as recorded', cut(mp7)[0])
add('SMG_MPI69_Shot_02', 'P90: owner MP7 +4 %', pitch(cut(mp7)[0], 1.04)[:int(1.2 * R)])
add('SMG_MPI69_Shot_03', 'P90: owner MP7 -3 %', pitch(cut(mp7)[0], 0.97)[:int(1.2 * R)])
# TMP: the game's original clips (stock DM09 bank, *.before-heat)
mp = os.path.expanduser('~/mnt/Kane & Lynch 2 - Dog Days/KLExpansion/Maps/DM09/F06_Main')
ws = {w.name.lower(): w for w in G.waves(open(mp + '.WHD.before-heat', 'rb').read())}; wb = open(mp + '.WAV.before-heat', 'rb').read()
for i in (1, 2, 3):
    w = ws[('SFX/Weapons_KL2_Final/SMG_MAC_10/SMG_MAC_10_Shot_0%d.wav' % i).lower()]; x = G.decode_wave(wb, w)
    x = x[:, 0] if x.ndim > 1 else x; x = x.astype(float); x = x / 32768 if np.abs(x).max() > 2 else x
    add('SMG_MAC_10_Shot_0%d' % i, 'TMP: the game\'s original SMG_MAC_10_Shot_0%d (stock bank)' % i, x, do_norm=False)
# USP: Dead Men's own
d = os.path.expanduser('~/mnt/Kane and Lynch Dead Men/Scenes/Locations/M01_FA_A/M01FAA_Main')
b = open(d + '.WHD', 'rb').read(); wv = open(d + '.WAV', 'rb').read(); items, T = W.parse('dm', b)
dm = {}
for k, o, v in items:
    if k == 'rec':
        r = dict(zip(W.DM_F, v)); dm[b[v[0]:b.index(b'\0', v[0])].decode('latin1')] = r
def dmclip(name):
    r = dm[name]; data = wv[r['off']:r['off'] + r['size']]
    x = G.ima_decode(data, r['ch'], r['block'], r['spb'], r['samples']); x = np.asarray(x, float).reshape(-1)
    return x / 32768 if np.abs(x).max() > 2 else x
for i in (1, 2, 3):
    add('HG_M9Beretta_Shot_0%d' % i, 'USP: Dead Men Shot_Usp_0%d (M01_FA_A bank)' % i, dmclip('SFX/Weapons/Pistol_HK_USP/Shot/Shot_Usp_0%d.wav' % i), do_norm=False)
# M4: owner's recordings + distortion tweak
m4a, m4b, m4c, m4d = (rd(os.path.join(REF, n + '.wav')) for n in ('m4_a', 'm4_b', 'm4_c', 'm4_d'))
# shot = the LAST shot of a burst (its own tail is free of the next shot); 2 ms high-passed peaks, fire period ~44 ms
# M4 (owner 19:22: 'stop making the sounds cut out, extend the shell coming out'): nothing is cut short any more. A shot that
# its recording follows with the next round within the clip runs on into the free tail (the shell / the echo) after auto_a's LAST
# round (1.245 s, nothing after it), level-matched and crossfaded at the same time after the onset. Layer: one auto_a round at -3 dB.
autoa = rd(os.path.join(REF, 'auto_a.wav'))
def onset_in(x, t, win=0.03):
    a = int((t - win) * R); seg = np.abs(x[a:a + int(2 * win * R)]); return (a + int(np.argmax(seg > 0.5 * seg.max()))) / R
DON = onset_in(autoa, 1.245)
def ext(x, t, nxt, dur=1.3, xf=0.03):
    t = onset_in(x, t); a = int((t - 0.004) * R); n = int(dur * R); y = x[a:a + n].copy(); y = np.pad(y, (0, n - len(y)))
    d = autoa[int((DON - 0.004) * R):int((DON - 0.004) * R) + n].copy(); d = np.pad(d, (0, n - len(d)))
    if nxt is not None:
        c = int((nxt - t - 0.006) * R); f = int(xf * R); c0 = max(f, c - f)
        g = np.sqrt((y[c0 - int(0.02 * R):c0] ** 2).mean() / ((d[c0 - int(0.02 * R):c0] ** 2).mean() + 1e-12))
        w = np.concatenate([np.ones(c0), np.linspace(1, 0, f), np.zeros(n - c0 - f)])
        y = y * w + d * g * (1 - w)
    return y
def m4(t1, n1, t2, n2, db=-3.0):
    a = ext(m4a, t1, n1); b = ext(autoa, t2, n2); a /= np.abs(a[:int(0.05 * R)]).max() + 1e-12; b /= np.abs(b[:int(0.05 * R)]).max() + 1e-12
    y = a + b * 10 ** (db / 20); f = int(0.12 * R); y[-f:] *= np.linspace(1, 0, f) ** 2; return y
add('Rifle_AK74_Shot_01', 'M4A1: owner m4_a shot 0.345 s + auto_a round 0.715 s at -3 dB, tails run on (no cut)', m4(0.345, 1.02, 0.715, 0.995))
add('Rifle_AK74_Shot_02', 'M4A1: owner m4_a shot 1.64 s + auto_a last round 1.245 s at -3 dB, tails run on', m4(1.64, 2.495, 1.245, None))
add('Rifle_AK74_Shot_03', 'M4A1: owner m4_a shot 1.02 s + auto_a round 0.715 s at -4 dB, tails run on', m4(1.02, 1.45, 0.715, 0.995, db=-4.0))
# distant: Dead Men's own USP distant for handguns; SMG distant as snd4
add('Distant_Shot_HandGuns_01', 'handgun distant: Dead Men Distant_Shot_USP_01', dmclip('SFX/Weapons/_Common/DistantShot/USP/Distant_Shot_USP_01.wav'), do_norm=False)
x, r = G.read_wav(os.path.expanduser('~/work_snd4/clips/Distant_Shot_SubMachineGuns_01.wav')); P.append(('Distant_Shot_SubMachineGuns_01', 'SMG distant: as snd4', x[:, 0]))
def to_bang(y, look=0.35):
    # owner 2026-10-17: 'the first few milliseconds - the round leaving, not the actual shot - is what plays in the game':
    # in auto fire each round restarts the clip, so only its first ~70 ms are heard. Start the clip AT the loudest 5 ms
    # (the bang itself), 2 ms before it; what came before it (mechanism / pre-crack) is dropped.
    W = int(0.005 * R); n = int(look * R); e = [np.sqrt((y[i:i + W] ** 2).mean()) for i in range(0, min(n, len(y) - W), W)]
    k = max(0, int(np.argmax(e)) * W - int(0.002 * R)); z = y[k:].copy(); z[:int(0.001 * R)] *= np.linspace(0, 1, int(0.001 * R))
    return z / (np.abs(z).max() + 1e-12) * 10 ** (-1 / 20)
BANG = [t for t, _, _ in P if t.startswith(('SMG_Type79', 'Rifle_AK74', 'SMG_MPI69'))]
P = [(t, d + ('; starts at the bang' if t in BANG else ''), to_bang(np.asarray(y, float)) if t in BANG else y) for t, d, y in P]
lines = []
for tag, desc, y in P:
    y = np.asarray(y, float); G.write_wav(os.path.join(OUT, tag + '.wav'), G.to_i16(y[:, None]), R)
    lines.append('%s\t%s\t(peak %.1f dB, %.2f s)' % (tag, desc, 20 * np.log10(np.abs(y).max() + 1e-12), len(y) / R))
open(os.path.join(OUT, 'clips.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
