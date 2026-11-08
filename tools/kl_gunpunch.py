#!/usr/bin/env python3
"""
kl_gunpunch.py - bring every gun's shot sample up to the S&W MP45's DELIVERY (owner 2026-11-08: "make the guns more raw, i still
feel like the mp45 is the best, none of the other guns give the same delivery as it"). Measurements: re/gunfeel_1108.md.

WHAT THE MEASUREMENTS SAY (live banks, first take of each gun; the MP45 plays the Desert Eagle clips, which every raw pass left alone):
  the MP45 is a CLEAN HARD-CLIPPED CRACK: a sharp front (transient 3.0 dB above its own 60-250 ms body), the energy in 120 Hz..2 kHz
  (83 %, only 4 % under 120 Hz), and a SHORT dry decay (tail -20.5 dB, 0.4-0.8 s after the shot, against the head).
  After gunraw_1107 every other gun has the same head level and flat-top share but a different SHAPE: the body shelf (+4..6 dB at
  120 Hz) and the hard-clip drive (+10..18 dB, which lifts the quiet tail by the same amount) turned them into a flat slab with a
  loud tail (tail -5..-15 dB, transient 0..2 dB, 30..80 % of the energy under 120 Hz): loud, but no front and no air, a wash.
WHAT THIS PASS DOES (data only, same records, same sizes, WHD / .SND / zips untouched, same md5-chained span installer):
  1. source = the record's pre-raw clip (.before-1025gunraw, else .before-1107gunraw): never re-encode an already driven clip;
  2. EQ: sub cut, SMALL low shelf, mid body + 2.8 kHz crack + a little air (the MP45's spectrum, not a boom);
  3. transient emphasis: the first ~10 ms after the onset get up to +6 dB before the saturation (the front of the MP45's crack);
  4. tanh saturation, then (outside body(): drive_raw) the same hard clip to the MP45 head level and flat-top share as gunraw;
  5. tail duck AFTER the clip: from 120 ms the clip falls to a per-class floor by 450 ms, so the loud tail the clip drive lifted goes
     back toward the MP45's dry decay. Rooms are the hook's job ([Echo]); distant and silenced layers keep their tails.
Toggle = INSTALL / UNDO .bat (data). Undo restores exactly the gunraw_1107 banks (md5-checked, backups *.WAV.before-1108gunpunch).
Every number in PUNCH is a starting taste and a GUESS: nobody has listened. `preview` writes before/after wavs.

    python kl_gunpunch.py build <outdir> [--groups maps,stock,story] [--force]
    python kl_gunpunch.py verify <outdir>
    python kl_gunpunch.py measure [bank base path]        read-only: the MP45 vs every gun table of a live bank (re/gunfeel_1108.md)
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gunsnd as G
import kl_gunsnd_match as M
import kl_gunsnd_all as A

R = M.R
# class -> sub cut Hz, low shelf dB@150, body dB@900, crack dB@2.8k, air dB@6k, transient boost (linear, extra gain at the onset), tanh drive,
#          wet (x dry peak) of the in-length tail, tail s, tail target dB (RMS 0.4-0.8 s vs the head; the clip is ducked only as far as needed to
#          reach it, never more than 'floor' dB, never up), duck start ms, duck end ms.  ALL GUESS (see header); the MP45's own tail is -20.5.
PUNCH = {
    'pistol':   dict(cut=70, low=1.5, body=2.0, crack=3.0, air=1.5, tr=1.0, drive=2.4, wet=0.12, tail=0.40, tgt=-20, floor=-9, d0=120, d1=450),
    'shotgun':  dict(cut=55, low=3.0, body=1.5, crack=2.5, air=1.0, tr=0.8, drive=2.4, wet=0.18, tail=0.55, tgt=-14, floor=-12, d0=150, d1=550),
    'rifle':    dict(cut=70, low=1.5, body=2.0, crack=3.0, air=1.5, tr=1.0, drive=2.4, wet=0.14, tail=0.45, tgt=-16, floor=-10, d0=120, d1=450),
    'smg':      dict(cut=70, low=1.0, body=2.0, crack=3.0, air=1.5, tr=1.0, drive=2.2, wet=0.10, tail=0.35, tgt=-18, floor=-10, d0=100, d1=400),
    'mg':       dict(cut=60, low=0.0, body=2.0, crack=2.5, air=1.0, tr=0.8, drive=2.2, wet=0.10, tail=0.40, tgt=-14, floor=-10, d0=100, d1=400),
    'distant':  dict(cut=40, low=2.0, body=0.0, crack=0.0, air=0.0, tr=0.0, drive=1.6, wet=0.75, tail=1.50, tgt=0, floor=0.0, d0=0, d1=0),
    'silenced': dict(cut=60, low=1.0, body=1.0, crack=0.0, air=0.0, tr=0.0, drive=1.4, wet=0.12, tail=0.40, tgt=0, floor=0.0, d0=0, d1=0),
}
FLOOR_ON = True      # tail duck after the clip (module toggle, tests)
CLS = {}             # record name -> class, filled by punch_body so punch_drive_raw knows which duck to apply (same call order as build_bank)
_LAST = [None]


def _shape(x, p, light):
    f = 0.6 if light else 1.0; r = R
    y = G._fft_filter(x[:, None], r, lambda fr: G._shelf(fr, 150, p['low'] * f) + G._peak(fr, 900, p['body'] * f, 1) + G._peak(fr, 2800, p['crack'] * f, 1)
                      + G._shelf(fr, 6000, p['air'] * f) - 24 * (1 / (1 + (fr / p['cut']) ** 4)))[:, 0]
    return y


def punch_body(x, cls, light=False):
    """float clip -> punchy body (see header). Same length as x; peak ~0.94. Remembers the class for punch_drive_raw."""
    p = PUNCH[cls]; _LAST[0] = (cls, light)
    x = x - x.mean(); x = x / (np.abs(x).max() + 1e-9)
    y = _shape(x, p, light)
    i = M.onset(y)
    if p['tr'] > 0:                                          # transient emphasis: +tr x exp(-t/4 ms) from the onset (the crack's front)
        t = np.arange(len(y)) - i
        y = y * (1 + np.where(t >= 0, p['tr'] * (0.0 + np.exp(-np.maximum(t, 0) / (0.004 * R))), 0.0) * (0.6 if light else 1.0))
    y = np.tanh(p['drive'] * y / max(1e-9, np.abs(y).max())) / np.tanh(p['drive'])
    if p['wet'] > 0:
        ir = G.synth_ir(R, 'street' if cls in ('pistol', 'shotgun', 'rifle', 'distant') else 'indoor', tail=min(p['tail'], len(x) / R))
        n = 1 << int(np.ceil(np.log2(len(y) + len(ir))))
        wet = np.fft.irfft(np.fft.rfft(y, n) * np.fft.rfft(ir, n), n)[:len(y)]
        wet = G._fft_filter(wet[:, None], R, lambda fr: -18 * (1 - 1 / (1 + (fr / 3500) ** 2)))[:, 0]
        y = y + wet * (p['wet'] * np.abs(y).max() / max(1e-9, np.abs(wet).max()))
    fd = min(len(y), int(0.08 * R)); y[-fd:] *= np.linspace(1, 0, fd)
    return y / (np.abs(y).max() + 1e-9) * 0.94


def tail_db(y):
    """RMS 0.4-0.8 s after the onset against the head RMS (dB); -99 when the clip is too short to have that window"""
    i = M.onset(y); t = y[i + int(0.4 * R):i + int(0.8 * R)]
    return float(20 * np.log10(np.sqrt((t ** 2).mean()) + 1e-9) - M.head_db(y)) if len(t) > 100 else -99.0


def duck_env(n, onset, p, drop):
    """gain 1 until onset + d0, a cosine fall of `drop` dB (negative) by onset + d1, held after"""
    g = np.ones(n); a = onset + int(p['d0'] / 1000 * R); b = onset + int(p['d1'] / 1000 * R)
    lo = 10 ** (drop / 20)
    if b <= a or a >= n: return g
    u = np.clip((np.arange(n) - a) / float(b - a), 0, 1)
    return 1 + (lo - 1) * (0.5 - 0.5 * np.cos(np.pi * u))


def punch_drive_raw(x, target_db, target_flat):
    """M.drive_raw (the hard clip to the MP45 head level + flat-top share), then the tail duck of the class body() just saw:
    only as far as needed to bring the 0.4-0.8 s tail down to the class target (floor limits it, a dry clip is left alone)"""
    y, d, h, fl = _drive_raw0(x, target_db, target_flat)
    cls, light = _LAST[0] or ('rifle', False)
    p = PUNCH[cls]
    if FLOOR_ON and p['floor'] < 0:
        drop = max(p['floor'], min(0.0, p['tgt'] - tail_db(y)))
        if drop < -0.5:
            y = y * duck_env(len(y), M.onset(y), p, drop)
            h, fl = M.head_db(y), M.flat_pct(y)
    return y, d, h, fl


_drive_raw0 = M.drive_raw


def install():
    """swap the three hooks of kl_gunsnd_all (module state of THIS process only)"""
    A.body = lambda x, cls, light=False: punch_body(x, cls, light)
    M.drive_raw = punch_drive_raw
    A.RAW = A.BODY = True
    A.TAG = '1108gunpunch'
    A.BODY_REF, A.BODY_FALLBACK = '.before-1107gunraw', '.before-1107gunraw'
    A.PREVIEW_NAME = 'punch1108'
    A.INST_WHAT = 'punchy gun sounds'
    A.INST_BLURB = ('PUNCHY gun sounds 1108 (recommended on): the MP45 delivery on every gun - sharper front, dry tight decay, no boom; on top of the raw gun sounds 1107, '
                    'KLExpansion maps + the 9 stock FA maps + story levels')


def main(a):
    if not a: print(__doc__); return 1
    c, r = a[0], list(a[1:])
    install()
    if c == 'build': return A.cmd_build_punch(r) if hasattr(A, 'cmd_build_punch') else _build(r)
    if c == 'verify': return A.cmd_verify(r)
    if c == 'measure': return _measure(r)
    print(__doc__); return 1


def _build(r):
    force = '--force' in r
    if force: r.remove('--force')
    groups = A.split_groups(r); out = r[0]
    args = [out, '--groups', ','.join(groups)] + (['--force'] if force else [])
    # cmd_build would reset TAG / flags only when --raw / --body are given; we give neither, our flags are already set by install()
    return A.cmd_build(args)


def _measure(r):
    sys.path.insert(0, HERE)
    import json
    base = r[0] if r else os.path.join(A.B.DD, 'Scenes', 'Locations', 'F02', 'F02_Main')
    whd = open(base + '.WHD', 'rb').read(); wav = open(base + '.WAV', 'rb').read(); seen = set()
    cols = ('peak', 'head', 'crest', 'trans', 'cent', 'lt120', 'b120_500', 'b500_2k', 'b2_6k', 'flat', 'tail', 'd20')
    print('%-30s' % 'gun' + ''.join('%8s' % c for c in cols))
    for w in G.waves(whd):
        if not (M.SEL.search(w.name) or M.REF.search(w.name)) or w.codec != 0x11 or w.streamed: continue
        k = w.name.split('/')[-2] if w.name.count('/') >= 2 else w.name
        if k in seen: continue
        seen.add(k); f = feats(G.decode_wave(wav, w)[:, 0])
        print('%-30s' % k[:30] + ''.join('%8.1f' % f[c] for c in cols))
    return 0


def feats(x):
    """the measurement of re/gunfeel_1108.md for one clip (floats): peak / head / crest dB, transient = RMS first 20 ms over RMS 60-250 ms (dB),
    centroid Hz and band shares % of the first 60 ms, flat-top % of the head window (DC kept: the clips carry DC), tail dB (0.4-0.8 s vs head),
    d20 = ms until the 10 ms-RMS envelope is 20 dB under its maximum"""
    flat = M.flat_pct(x)
    x = x - x.mean(); pk = np.abs(x).max(); i = M.onset(x); s = x[i:]
    rms = lambda q: float(np.sqrt((q ** 2).mean()) + 1e-12)
    n = lambda ms: int(ms / 1000 * R)
    h250, a20, b = rms(s[:n(250)]), rms(s[:n(20)]), rms(s[n(60):n(250)])
    seg = s[:n(60)] * np.hanning(len(s[:n(60)])); X = np.abs(np.fft.rfft(seg, 4096)) ** 2; fr = np.fft.rfftfreq(4096, 1 / R); T = X.sum() + 1e-12
    band = lambda lo, hi: 100 * X[(fr >= lo) & (fr < hi)].sum() / T
    t = s[n(400):n(800)]
    e = np.array([rms(s[k:k + n(10)]) for k in range(0, min(len(s) - n(10), n(1500)), n(5))]); d = np.nonzero(e < e.max() * 0.1)[0]
    return dict(peak=20 * np.log10(pk + 1e-9), head=20 * np.log10(h250), crest=20 * np.log10(pk / h250), trans=20 * np.log10(a20 / b),
                cent=float((fr * X).sum() / T), lt120=band(0, 120), b120_500=band(120, 500), b500_2k=band(500, 2000), b2_6k=band(2000, 6000),
                flat=flat, tail=(20 * np.log10(rms(t)) - 20 * np.log10(h250)) if len(t) > 100 else -99.0, d20=float((d[0] * 5) if len(d) else len(e) * 5))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
