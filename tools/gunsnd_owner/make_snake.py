"""snd4: real gunshots with their own natural outdoor reverb (Snake's Authentic Gun Sounds 1 + 2, itch.io f8studios,
'All sounds can be used commercially, and credit is not needed'; the author calls them public domain). Kept raw:
mono, a light camera band, a little preamp clip on the crack, a gentle camera AGC dip. The M4 gets a Heat street slapback."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.expanduser('~/mnt/kl-merge/kl-merge/tools'))
sys.path.insert(0, os.path.expanduser('~/mnt/Kane and Lynch Dead Men/KL_PortTools/build/snd2/scripts'))
import kl_gunsnd as G
from onsets2 import onsets
sys.path.insert(0, os.path.expanduser('~/work_snd3'))
R = 32000; OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True); rng = np.random.default_rng(3)
_c = {}
def load(n):
    if n not in _c:
        x, r = G.read_wav(os.path.join('src', n + '.wav')); m = x.mean(1) if x.ndim > 1 else x
        nn = 1 << int(math.ceil(math.log2(len(m) * 2))); X = np.fft.rfft(m, nn); fr = np.fft.rfftfreq(nn, 1 / r)
        X[fr > 15000] = 0; m = np.fft.irfft(X, nn)[:len(m)]
        _c[n] = G.resample(m[:, None], r, R)[:, 0]
    return _c[n]
def onsets(x, R):
    m = np.abs(x); w = int(0.005 * R); e = np.array([m[i:i + w].max() for i in range(0, len(m) - w, w)]); edb = 20 * np.log10(e + 1e-9)
    on = [i for i in range(2, len(e)) if edb[i] - max(edb[i - 2], edb[i - 1]) > 8 and edb[i] > edb.max() - 15]
    out = []
    for i in on:
        if not out or i - out[-1] > 6: out.append(i)
    res = [i * w + int(np.argmax(m[i * w:(i + 1) * w] > 0.5 * e[i])) for i in out]
    first = int(np.argmax(m > 0.3 * m.max()))
    if not res or res[0] - first > int(0.03 * R): res = [first] + res
    return res
def last_shot(n, which=-1, pre=0.002, dur=1.0):
    x = load(n); o = onsets(x, R); o = o[which]; a = max(0, o - int(pre * R))
    s = x[a:a + int(dur * R)].copy(); return np.pad(s, (0, int(dur * R) - len(s))), len(onsets(x, R))
def eq(x, fn):
    n = 1 << int(math.ceil(math.log2(len(x) * 2))); X = np.fft.rfft(x, n); fr = np.fft.rfftfreq(n, 1 / R)
    return np.fft.irfft(X * 10 ** (fn(fr) / 20), n)[:len(x)]
def hp(fr, f0, o=2): return 10 * np.log10(1 / (1 + (f0 / np.maximum(fr, 1e-3)) ** (2 * o)))
def lp(fr, f0, o=2): return 10 * np.log10(1 / (1 + (np.maximum(fr, 1e-3) / f0) ** (2 * o)))
def pk(fr, f0, db, q=1.0): return db * np.exp(-0.5 * (np.log2(np.maximum(fr, 1) / f0) * 2 * q) ** 2)
def slaps(x, taps):
    y = x.copy()
    for d, db, cut in taps:
        k = int(d * R); e = eq(x, lambda f: lp(f, cut, 1)) * 10 ** (db / 20); y[k:] += e[:len(y) - k]
    return y
def cam(x, drive_db=6, duck_db=-6, rel=0.4, hpf=100, lpf=12000, presence=1.5):
    x = eq(x, lambda f: hp(f, hpf, 2) + lp(f, lpf, 2) + pk(f, 2800, presence))
    x = x / (np.abs(x).max() + 1e-12); y = np.clip(x * 10 ** (drive_db / 20), -0.9, 1.0)
    t = np.arange(len(y)) / R; g = np.where(t < 0.012, 0.0, duck_db * np.exp(-(t - 0.012) / rel)) * np.clip((t - 0.012) / 0.006, 0, 1)
    y = y * 10 ** (g / 20) + rng.standard_normal(len(y)) * 10 ** (-60 / 20)
    return y / (np.abs(y).max() + 1e-12) * 10 ** (-0.3 / 20)
HEAT = [(0.090, -9, 5000), (0.165, -12, 3800), (0.270, -15, 2800), (0.420, -18, 2000), (0.600, -21, 1600)]
PLAN, info = [], []
def add(tag, desc, y): PLAN.append((tag, desc, y))
srcs556 = [('556_Single_WAV', 0), ('556_Double_Tap_WAV', -1), ('556_Spray_WAV', -1)]
for i, (n, w) in enumerate(srcs556):
    if n == '556_Spray_WAV':
        n, w = '556_Single_WAV', 0
        s, k = last_shot(n, w); s = np.interp(np.arange(0, len(s), 1.04), np.arange(len(s)), s); s = np.pad(s, (0, int(1.0 * R) - len(s)))
    else:
        s, k = last_shot(n, w)
    info.append('%s: %d onsets' % (n, k))
    add('Rifle_AK74_Shot_0%d' % (i + 1), 'M4A1: Snake 5.56 %s shot %d (natural reverb) + Heat street slaps, camera clip +8 dB' % (n, w), cam(slaps(s, HEAT), drive_db=8, duck_db=-9, rel=0.3))
srcs9 = [('9mm_Single', 0), ('9mm_Double_Tap', -1), ('9mm_Burst', -1), ('9mm_Spray', -1), ('9mm_Slow_Burst', -1)]
for i, (n, w) in enumerate(srcs9[:3]):
    s, k = last_shot(n, w); info.append('%s: %d onsets' % (n, k))
    add('SMG_Type79_Shot_0%d' % (i + 1), 'MP5: Snake 9mm %s shot %d, natural reverb, short slap, camera clip +6 dB' % (n, w), cam(slaps(s, [(0.07, -9, 4500), (0.14, -12, 3000)]), drive_db=6))
for i, (n, w) in enumerate([srcs9[3], srcs9[4], srcs9[1]]):
    s, k = last_shot(n, w)
    add('SMG_MPI69_Shot_0%d' % (i + 1), 'P90: Snake 9mm %s shot %d, brighter / snappier, camera clip +7 dB' % (n, w), cam(s, drive_db=7, hpf=170, presence=3.0, lpf=13000))
for i, (n, w) in enumerate([srcs9[2], srcs9[3], srcs9[0]]):
    s, k = last_shot(n, w)
    add('SMG_MAC_10_Shot_0%d' % (i + 1), 'TMP: Snake 9mm %s shot %d, tight, camera clip +6 dB' % (n, w), cam(s, drive_db=6, hpf=180, rel=0.25))
for i, (n, w) in enumerate([srcs9[0], srcs9[1], srcs9[4]]):
    s, k = last_shot(n, w)
    add('HG_M9Beretta_Shot_0%d' % (i + 1), 'USP: Snake 9mm %s shot %d, natural reverb, camera clip +5 dB' % (n, w), cam(s, drive_db=5))
def distant(s, cut): return cam(slaps(eq(s, lambda f: lp(f, cut, 2)), HEAT), drive_db=2, duck_db=-3, lpf=4000, hpf=180)
add('Distant_Shot_HandGuns_01', 'handgun distant: Snake 9mm single, lp 2 kHz + street slaps', distant(last_shot('9mm_Single', 0)[0], 2000))
add('Distant_Shot_SubMachineGuns_01', 'SMG distant: Snake 9mm spray last shot, lp 2 kHz + street slaps', distant(last_shot('9mm_Spray', -1)[0], 2000))
lines = []
for tag, desc, y in PLAN:
    G.write_wav(os.path.join(OUT, tag + '.wav'), G.to_i16(y[:, None]), R); lines.append(tag + '\t' + desc)
open(os.path.join(OUT, 'clips.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(info + lines))
