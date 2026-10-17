"""snd5: the owner's own reference recordings (build/snd5/ref, given in chat 2026-10-16) used as the shots, kept as recorded:
mono, 35 Hz high-pass, peak -1 dB, a fade only where the next shot of the file starts. M4 / USP: Snake's 5.56 / 9mm, clean
(no camera clip, no AGC, no hiss), the M4 with a light street slapback."""
import sys, os, math, numpy as np
sys.path.insert(0, os.path.expanduser('~/mnt/kl-merge/kl-merge/tools')); import kl_gunsnd as G
R = 32000; REF = os.path.expanduser('~/mnt/Kane and Lynch Dead Men/KL_PortTools/build/snd5/ref'); OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SN = os.path.expanduser('~/work_snd4/src')
def rd(p):
    x, r = G.read_wav(p); m = x.mean(1)
    if r != R:
        nn = 1 << int(math.ceil(math.log2(len(m) * 2))); X = np.fft.rfft(m, nn); fr = np.fft.rfftfreq(nn, 1 / r); X[fr > 15000] = 0
        m = G.resample(np.fft.irfft(X, nn)[:len(m)][:, None], r, R)[:, 0]
    return m
def eq_hp(x, f0=35.0):
    n = 1 << int(math.ceil(math.log2(len(x) * 2))); X = np.fft.rfft(x, n); fr = np.fft.rfftfreq(n, 1 / R)
    return np.fft.irfft(X / np.sqrt(1 + (f0 / np.maximum(fr, 1e-3)) ** 4), n)[:len(x)]
def onsets(x):
    m = np.abs(x); w = int(0.005 * R); e = np.array([m[i:i + w].max() for i in range(0, len(m) - w, w)]); edb = 20 * np.log10(e + 1e-9)
    on = [i for i in range(1, len(e)) if edb[i] - edb[max(0, i - 2):i].max() > 10 and edb[i] > edb.max() - 8]
    res = []
    for i in on:
        if not res or i - res[-1] > 30: res.append(i)          # 150 ms apart at least: a new shot, not its own echo
    out = [i * w + int(np.argmax(m[i * w:(i + 1) * w] > 0.3 * e[i])) for i in res]
    first = int(np.argmax(m > 0.3 * m.max()))
    if not out or out[0] - first > int(0.1 * R): out = [first] + out
    return out
def cut(x, k=0, dur=1.2, pre=0.002):
    o = onsets(x); k = k % len(o); a = max(0, o[k] - int(pre * R)); end = o[k + 1] - int(0.01 * R) if k + 1 < len(o) else len(x)
    s = x[a:min(end, a + int(dur * R))].copy()
    if k + 1 < len(o) and end < a + int(dur * R): f = int(0.015 * R); s[-f:] *= np.linspace(1, 0, f)
    s[:int(0.001 * R)] *= np.linspace(0, 1, int(0.001 * R))
    return np.pad(s, (0, int(dur * R) - len(s))), len(o)
def norm(y): y = eq_hp(y); return y / (np.abs(y).max() + 1e-12) * 10 ** (-1 / 20)
def pitch(y, f): return np.interp(np.arange(0, len(y), f), np.arange(len(y)), y)
def slaps(x, taps):
    y = x.copy()
    for d, db in taps: k = int(d * R); y[k:] += x[:len(y) - k] * 10 ** (db / 20)
    return y
P = []; info = []
def add(tag, desc, y): P.append((tag, desc, norm(y)))
mp5a, mp5b, sp5a, sp5b, sp5c, mp7 = (rd(os.path.join(REF, n + '.wav')) for n in ('mp5_a', 'mp5_b', 'sp5_a', 'sp5_b', 'sp5_c', 'mp7'))
for n, x in [('mp5_a', mp5a), ('mp5_b', mp5b), ('sp5_a', sp5a), ('sp5_b', sp5b), ('sp5_c', sp5c), ('mp7', mp7)]: info.append('%s onsets %s' % (n, [round(o / R, 2) for o in onsets(x)]))
add('SMG_Type79_Shot_01', 'MP5: owner ref mp5_a (single MP5 9mm) as recorded', cut(mp5a)[0])
add('SMG_Type79_Shot_02', 'MP5: owner ref mp5_b (single MP5A3 9mm) as recorded', cut(mp5b)[0])
add('SMG_Type79_Shot_03', 'MP5: owner ref sp5_a (single SP5A3 9mm) as recorded', cut(sp5a)[0])
add('SMG_MPI69_Shot_01', 'P90: owner ref mp7 (H&K MP7) as recorded', cut(mp7)[0])
add('SMG_MPI69_Shot_02', 'P90: owner ref sp5_b (SP5A3) as recorded', cut(sp5b)[0])
add('SMG_MPI69_Shot_03', 'P90: owner ref mp7 pitched up 5 %', pitch(cut(mp7)[0], 1.05)[:int(1.2 * R)])
nc = len(onsets(sp5c))
for i in range(3):
    add('SMG_MAC_10_Shot_0%d' % (i + 1), 'TMP: owner ref sp5_c (SP5A3 singles) shot %d as recorded' % (i % nc), cut(sp5c, i % nc)[0])
s9 = rd(os.path.join(SN, '9mm_Single.wav')); s9d = rd(os.path.join(SN, '9mm_Double_Tap.wav'))
add('HG_M9Beretta_Shot_01', 'USP: Snake 9mm single, clean', cut(s9)[0])
add('HG_M9Beretta_Shot_02', 'USP: Snake 9mm double tap 2nd shot, clean', cut(s9d, -1 if len(onsets(s9d)) > 1 else 0)[0])
add('HG_M9Beretta_Shot_03', 'USP: Snake 9mm single pitched down 3 %, clean', pitch(cut(s9)[0], 0.97)[:int(1.2 * R)])
s56 = rd(os.path.join(SN, '556_Single_WAV.wav')); s56d = rd(os.path.join(SN, '556_Double_Tap_WAV.wav'))
ST = [(0.09, -11), (0.17, -14), (0.28, -17), (0.43, -20)]
add('Rifle_AK74_Shot_01', 'M4A1: Snake 5.56 single, clean + light street slaps', slaps(cut(s56)[0], ST))
add('Rifle_AK74_Shot_02', 'M4A1: Snake 5.56 double tap 2nd shot, clean + light street slaps', slaps(cut(s56d, -1 if len(onsets(s56d)) > 1 else 0)[0], ST))
add('Rifle_AK74_Shot_03', 'M4A1: Snake 5.56 single pitched up 4 %, clean + light street slaps', slaps(pitch(cut(s56)[0], 1.04)[:int(1.2 * R)], ST))
for tag in ('Distant_Shot_HandGuns_01', 'Distant_Shot_SubMachineGuns_01'):
    x, r = G.read_wav(os.path.expanduser('~/work_snd4/clips/%s.wav' % tag)); P.append((tag, 'distant: as snd4', x[:, 0]))
lines = []
for tag, desc, y in P:
    G.write_wav(os.path.join(OUT, tag + '.wav'), G.to_i16(y[:, None]), R); lines.append(tag + '\t' + desc)
open(os.path.join(OUT, 'clips.txt'), 'w').write('\n'.join(lines) + '\n'); print('\n'.join(info + lines))
