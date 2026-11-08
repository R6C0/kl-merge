#!/usr/bin/env python3
"""
kl_gunsnd_all.py - ONE loudness for every gun-shot sample the game can play (owner 2026-10-24: "some guns arent at the same
loudness like i told you to make it at, needs to be applied to all maps").

kl_gunsnd_match.py (the MP45 pass) only knew the 27 KLExpansion\\Maps banks. This tool covers every bank that holds gun shots:
    maps   KLExpansion\\Maps\\<id>\\F0x_Main.{WHD,WAV}      27 banks (the earlier pass; re-checked, only real outliers change)
    stock  Scenes\\Locations\\F01..F09\\Fxx_Main.{WHD,WAV}   Dog Days' 9 stock Fragile Alliance maps (NOT processed before)
    story  Scenes\\Locations\\L00..L11\\Lxx_Main.{WHD,WAV}   Dog Days' campaign levels (NOT processed before)
(Scenes\\kaneandlynch.WAV and Loader_Sequence hold no gun shots; the *_Intro / *_LS banks neither: scanned, 0 matches.)

Same method and same targets as kl_gunsnd_match (head RMS of the first 250 ms after the onset; guns = the bank's own Desert
Eagle clips = what the S&W MP45 plays; silenced + Distant_Shot layers = reference - 3.7 dB; +18 dB gain cap; knee soft clipper;
every record re-encoded in place with the same sample and byte counts, so .WHD / .SND / zips stay byte-identical).
Differences:
  * a bank without the three Desert Eagle clips (L00, L09, L11 ...) uses FALLBACK_REF (-3.15 = the stock banks' Deagle head);
  * a record already within TOL (0.35 dB) of its target is NOT touched (idempotent, no ADPCM generation loss on re-runs);
  * input md5 pinning: every bank's live md5 must be listed in kl_gunsnd_all.pins.json (inputs or outputs of this tool),
    else build refuses that bank unless --force. `pin` records the current live md5s after you looked at `audit`.

    python kl_gunsnd_all.py audit  [--groups maps,stock,story] [--json f]   read-only table: outliers vs target per bank
    python kl_gunsnd_all.py pin    [--groups ...]                           accept the CURRENT live md5s as valid inputs
    python kl_gunsnd_all.py build <outdir> [--groups ...] [--force]         spans + manifest + report + INSTALL / UNDO scripts
    python kl_gunsnd_all.py verify <outdir>                                 independent re-check (apply, re-decode, undo)
    python kl_gunsnd_all.py build <outdir> --body [--groups ...] [--force]  RAW BODY pass (owner 11-07, re/gun_raw_1107.md): see BODY below

Not covered on purpose (reported, not changed): RocketLauncher_RPG7 launch (head -5), Rpg_Loop, explosions, reload / cock /
dry-fire clips, the npc (0.35) vs player (0.70) group volumes in the .SND (a design choice, not a sample level).
"""
import hashlib, json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gunsnd as G
import kl_dmgunsnd_build as B
import kl_gunsnd_match as M

TOL = 0.35                 # dB: a record this close to its target is left alone
FALLBACK_REF = -3.15       # dBFS head of the stock Desert Eagle clips (used where a bank has none)
SHORT = 0.5                # dB: a processed clip further under its target than this is reported (gain cap reached)
FALLBACK_FLAT = 19.8       # --raw: % flat tops in the Desert Eagle head window (DM07 measured 10-25)
FLAT_TOL = 3.0             # --raw: a 'gun' record within this many points of the reference share (and TOL in head) is left alone
RAW = False                # --raw (owner 10-25): 'gun' records also get the MP45's hard-clip density (M.drive_raw)
PINS = os.path.join(HERE, 'kl_gunsnd_all.pins.json')
TAG = '1024gunsnd2'
GROUPS = ('maps', 'stock', 'story')

# --body (owner 2026-11-07 "they all just sound like vanilla ... i want them to sound raw"; audit re/gun_raw_1107.md): the 10-24/10-25
# passes changed only LEVEL and clipping; timbre, tail and space were never touched. --body (implies --raw) rebuilds every gun-shot /
# distant / silenced record from its PRE-RAW source (the bank's .before-1025gunraw copy: same offsets, one ADPCM generation, never
# re-encode the live clip) with: (1) body EQ = low shelf at 120 Hz + 2.5 kHz crack + box cut + sub cut (kl_gunsnd.heat's EQ), (2) tanh
# saturation, (3) an echo tail synthesised INSIDE the record's stock length (kl_gunsnd.synth_ir convolution, high-cut, mixed under the
# dry shot: street tail for pistols / shotguns / distant, shorter indoor-style tail for rifles / SMGs / MGs so full auto does not stack
# a wall of overlapping voices), then (4) the existing hard clip to the MP45 head level + flat-top share (drive_raw; distant and
# silenced keep the knee clipper at the reference minus 3.7 dB). Record sizes are unchanged, so .WHD / .SND / zips stay byte-identical
# and the md5-chained span installer works as before. The Deagle (= MP45) clips are untouched (the reference).
# GUESS: every number in PROFILE (shelf dB, tail gain, tail style per class) is a starting taste, nobody has listened yet; the
# preview wavs under <outdir>\preview are there to audition BEFORE installing.
BODY = False
PREVIEW = ('stock/F02', 'maps/DM02')   # --body: these banks also get before/after .wav pairs under <outdir>/preview (audition before installing)
BODY_BAK = '.before-1025gunraw'      # the pre-raw copy of every bank (kept by the 1025 installer)
BODY_REF = None                      # kl_gunpunch (1108): bank suffix whose clips the correlation check compares against (None = the live bank)
BODY_FALLBACK = None                 # kl_gunpunch: bank suffix used as the source when the BODY_BAK clip fails the check (None = keep the live clip)
PREVIEW_NAME = 'raw1107'             # suffix of the 'after' preview wavs
INST_WHAT, INST_BLURB = 'raw gun sounds', 'RAW gun sounds 1107 (recommended on): body EQ + saturation + echo tail + MP45 hard clip on every gun / distant / silenced shot, KLExpansion maps + the 9 stock FA maps + story levels'
BODY_CORR = 0.5                      # live vs backup normalised-waveform correlation under this: a later pass replaced the clip -> use the live one
PROFILE = {      # class -> low shelf dB @120 Hz, crack dB @2.5 kHz, tanh drive, wet gain (x dry peak), IR style, IR tail s
    'pistol':   dict(low=5.0, crack=3.0, drive=2.2, wet=0.50, style='street', tail=0.80),
    'shotgun':  dict(low=6.0, crack=2.0, drive=2.2, wet=0.55, style='street', tail=0.90),
    'rifle':    dict(low=5.0, crack=3.0, drive=2.2, wet=0.38, style='street', tail=1.00),
    'smg':      dict(low=4.0, crack=3.0, drive=2.0, wet=0.28, style='indoor', tail=0.60),
    'mg':       dict(low=5.0, crack=2.0, drive=2.0, wet=0.28, style='indoor', tail=0.70),
    'distant':  dict(low=3.0, crack=0.0, drive=1.6, wet=0.75, style='street', tail=1.50),
    'silenced': dict(low=2.0, crack=0.0, drive=1.4, wet=0.15, style='indoor', tail=0.40),
}
CLASS_RX = [(re.compile(r'distant_shot', re.I), 'distant'), (re.compile(r'silenced', re.I), 'silenced'),
            (re.compile(r'/(HG_|Pistol|Revolver)', re.I), 'pistol'), (re.compile(r'shotgun', re.I), 'shotgun'),
            (re.compile(r'/(MG_|Machine|MiniMi)', re.I), 'mg'), (re.compile(r'/(SMG_|Sub)', re.I), 'smg')]
LIGHT = re.compile(r'(M9Beretta|TaurusJudge|Shotgun_TPS|Type88)', re.I)   # already raw in stock (audit table 2): milder EQ


def gun_class(name):
    for rx, c in CLASS_RX:
        if rx.search(name): return c
    return 'rifle'


def body(x, cls, light=False):
    """float clip -> body EQ + saturation + in-length echo tail (see BODY). Same length as x; peak ~0.94 before the clip stage."""
    p = PROFILE[cls]; f = 0.6 if light else 1.0; r = M.R
    x = x - x.mean(); x = x / (np.abs(x).max() + 1e-9)
    y = G._fft_filter(x[:, None], r, lambda fr: G._shelf(fr, 120, p['low'] * f) + G._peak(fr, 2500, p['crack'] * f, 1) + G._peak(fr, 450, -2, 1.2)
                      - 24 * (1 / (1 + (fr / 30) ** 4)))[:, 0]
    y = np.tanh(p['drive'] * y / max(1e-9, np.abs(y).max())) / np.tanh(p['drive'])
    ir = G.synth_ir(r, p['style'], tail=min(p['tail'], len(x) / r))
    n = 1 << int(np.ceil(np.log2(len(y) + len(ir))))
    wet = np.fft.irfft(np.fft.rfft(y, n) * np.fft.rfft(ir, n), n)[:len(y)]
    wet = G._fft_filter(wet[:, None], r, lambda fr: -18 * (1 - 1 / (1 + (fr / 3500) ** 2)))[:, 0]
    wet = wet * (p['wet'] * np.abs(y).max() / max(1e-9, np.abs(wet).max()))
    z = y + wet
    fd = min(len(z), int(0.08 * r)); z[-fd:] *= np.linspace(1, 0, fd)       # the tail ends inside the record: 80 ms fade, no cut
    return z / (np.abs(z).max() + 1e-9) * 0.94


def timbre(x):
    """centroid Hz of the head, % energy under 200 Hz, tail dB (RMS 0.4-0.8 s vs head), seconds above -50 dBFS: the audit's columns"""
    r = M.R; i = M.onset(x); h = x[i:i + int(0.25 * r)]; X = np.abs(np.fft.rfft(h * np.hanning(len(h)))) ** 2; fr = np.fft.rfftfreq(len(h), 1 / r)
    t = x[i + int(0.4 * r):i + int(0.8 * r)]
    th = float(20 * np.log10(np.sqrt((t ** 2).mean()) + 1e-9) - M.head_db(x)) if len(t) > 100 else -99.0
    env = np.abs(x); d = np.nonzero(env > 10 ** (-50 / 20))[0]
    return dict(centroid=round(float((fr * X).sum() / (X.sum() + 1e-12))), lf=round(float(100 * X[fr < 200].sum() / (X.sum() + 1e-12)), 1),
                tail_db=round(th, 1), dur=round(float((d[-1] - i) / r) if len(d) else 0.0, 2))


def md5(b): return hashlib.md5(b).hexdigest()


class Bank:
    def __init__(self, group, bid, base):
        self.group, self.id, self.base = group, bid, base
        self.key = group + '/' + bid
        self.rel = os.path.relpath(base + '.WAV', B.DD).replace('/', '\\')

    def load(self):
        return open(self.base + '.WHD', 'rb').read(), open(self.base + '.WAV', 'rb').read()


def banks(groups=GROUPS):
    out = []
    if 'maps' in groups:
        for d in sorted(os.listdir(B.MAPS)):
            f = [x for x in os.listdir(os.path.join(B.MAPS, d)) if re.match(r'F0\d_Main\.WHD$', x)]
            if f: out.append(Bank('maps', d, os.path.join(B.MAPS, d, f[0][:-4])))
    loc = os.path.join(B.DD, 'Scenes', 'Locations')
    for grp, pat in (('stock', r'F0\d$'), ('story', r'L\d\d$')):
        if grp in groups:
            for d in sorted(os.listdir(loc)):
                p = os.path.join(loc, d, d + '_Main')
                if re.match(pat, d) and os.path.exists(p + '.WHD') and os.path.exists(p + '.WAV'): out.append(Bank(grp, d, p))
    return out


def ref_of(whd, wav):
    hs = [M.head_db(G.decode_wave(wav, w)[:, 0]) for w in G.waves(whd) if M.REF.search(w.name)]
    return (float(np.mean(hs)), 'bank') if len(hs) == 3 else (FALLBACK_REF, 'fallback')


def ref_flat(whd, wav):
    """flat-top share of the bank's Desert Eagle head window (--raw); FALLBACK_FLAT where the bank has none"""
    fs = [M.flat_pct(G.decode_wave(wav, w)[:, 0]) for w in G.waves(whd) if M.REF.search(w.name)]
    return float(np.mean(fs)) if len(fs) == 3 else FALLBACK_FLAT


def shots(whd): return [w for w in G.waves(whd) if M.SEL.search(w.name) and not M.REF.search(w.name)]


def target(ref, name): return ref if M.kind(name) == 'gun' else ref - M.SIL_DROP


def rows_of(b, whd=None, wav=None):
    """-> (ref, how, [(wave, kind, head, target)]) for one bank"""
    if whd is None: whd, wav = b.load()
    ref, how = ref_of(whd, wav)
    return ref, how, [(w, M.kind(w.name), M.head_db(G.decode_wave(wav, w)[:, 0]), target(ref, w.name)) for w in shots(whd)]


def split_groups(a):
    g = GROUPS
    if '--groups' in a:
        i = a.index('--groups'); g = tuple(x for x in a[i + 1].split(',') if x); del a[i:i + 2]
        assert set(g) <= set(GROUPS), g
    return g


def cmd_audit(a):
    js = None
    if '--json' in a: i = a.index('--json'); js = a[i + 1]; del a[i:i + 2]
    groups = split_groups(a); res = {}; tot = off = 0
    pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
    for b in banks(groups):
        whd, wav = b.load(); ref, how, rows = rows_of(b, whd, wav)
        bad = [(w.name.split('/')[-1], k, h, t) for w, k, h, t in rows if abs(h - t) > TOL]
        tot += len(rows); off += len(bad)
        pin = pins.get(b.key); m5 = md5(wav)
        st = 'unpinned' if pin is None else ('in' if m5 in pin['inputs'] else ('out' if m5 in pin['outputs'] else 'CHANGED'))
        print('%-14s ref %6.2f (%s) %2d clips, %2d off target by > %.2f dB  md5 %s [%s]' % (b.key, ref, how, len(rows), len(bad), TOL, m5[:8], st))
        for n, k, h, t in sorted(bad, key=lambda r: -abs(r[2] - r[3]))[:6 if not js else 99]:
            print('      %-44s %-8s head %6.2f target %6.2f  (%+.1f dB)' % (n[:44], k, h, t, h - t))
        res[b.key] = dict(ref=round(ref, 2), how=how, md5=m5, clips=[dict(name=w.name, kind=k, head=round(h, 2), target=round(t, 2)) for w, k, h, t in rows])
    print('TOTAL: %d gun-shot records, %d off target by more than %.2f dB' % (tot, off, TOL))
    if js: json.dump(res, open(js, 'w'), indent=1)
    return 0


def cmd_pin(a):
    groups = split_groups(a); pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
    for b in banks(groups):
        m5 = md5(open(b.base + '.WAV', 'rb').read()); e = pins.setdefault(b.key, dict(inputs=[], outputs=[]))
        if m5 not in e['inputs'] and m5 not in e['outputs']: e['inputs'].append(m5)
    json.dump(pins, open(PINS, 'w'), indent=1, sort_keys=True); print('pinned %d banks -> %s' % (len(pins), PINS)); return 0


def build_bank(b, out, force, log):
    whd, wav = b.load(); m5 = md5(wav)
    pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
    pin = pins.get(b.key)
    if not (pin and (m5 in pin['inputs'] or m5 in pin['outputs'])) and not force:
        raise SystemExit('REFUSED %s: live .WAV md5 %s is not pinned in %s (run audit, then pin, or pass --force)' % (b.key, m5, PINS))
    ref, how, rows = rows_of(b, whd, wav)
    # --raw: ONE flat-top target (the Dog Days Desert Eagle = what the MP45 plays). The Dead Men banks' own Deagle clips measure
    # 0.1..0.3 % flat but are dense right under the peak (+1 dB drive = 16 % flat, +1 dB head); the MP45 is the owner's
    # reference ("mp45 was perfect"), so it stays untouched everywhere
    rf = FALLBACK_FLAT if RAW else None
    ws = {w.rec_off: w for w in G.waves(whd)}; repl = {}; rep = []; offs = {}; short = []
    bak = bakwav = None; nsrc = [0, 0]                      # --body: [records taken from the pre-raw copy, records kept on the live clip]
    refwav = fbwav = None
    if BODY:
        bp = b.base + '.WAV' + BODY_BAK
        if os.path.exists(bp):
            bakwav = open(bp, 'rb').read()
            if len(bakwav) != len(wav): bakwav = None       # a different layout: never mix offsets
        if BODY_REF:                                         # live = an earlier pass's OUTPUT: compare against and fall back to its input
            for suf, nm in ((BODY_REF, 'ref'), (BODY_FALLBACK, 'fb')):
                q = b.base + '.WAV' + suf if suf else None
                if q and os.path.exists(q):
                    z = open(q, 'rb').read()
                    if len(z) == len(wav):
                        if nm == 'ref': refwav = z
                        else: fbwav = z
    for w, k, h, t in rows:
        assert w.codec == 0x11 and w.get('rate') == M.R and w.get('ch') == 1 and not w.streamed, w.name
        o = w.get('off'); assert o not in offs, 'two records share data %s / %s' % (offs[o], w.name); offs[o] = w.name
        x = G.decode_wave(wav, w)[:, 0]; raw = RAW and k == 'gun'; fl = M.flat_pct(x); tb0 = timbre(x) if BODY else None
        if BODY:                                            # every record is rebuilt: no 'already on target' skip
            src = x
            if refwav is not None or fbwav is not None:     # chained pass: x is an earlier output; source = its pre-raw clip, else its own input
                xr = G.decode_wave(refwav, w)[:, 0] if refwav is not None else None
                cand = G.decode_wave(bakwav, w)[:, 0] if bakwav is not None else None
                if cand is not None and xr is not None:
                    n = min(len(cand), len(xr))
                    c = float(np.corrcoef(cand[:n] / (np.abs(cand).max() + 1e-9), xr[:n] / (np.abs(xr).max() + 1e-9))[0, 1])
                    if c >= BODY_CORR: src = cand; nsrc[0] += 1
                    elif fbwav is not None: src = G.decode_wave(fbwav, w)[:, 0]; nsrc[1] += 1
                    else: nsrc[1] += 1
                elif fbwav is not None: src = G.decode_wave(fbwav, w)[:, 0]; nsrc[1] += 1
                else: nsrc[1] += 1
            elif bakwav is not None:
                xb = G.decode_wave(bakwav, w)[:, 0]; n = min(len(xb), len(x))
                c = float(np.corrcoef(xb[:n] / (np.abs(xb).max() + 1e-9), x[:n] / (np.abs(x).max() + 1e-9))[0, 1])
                if c >= BODY_CORR: src = xb; nsrc[0] += 1
                else: nsrc[1] += 1
            else: nsrc[1] += 1
            x = body(src, gun_class(w.name), bool(LIGHT.search(w.name)))
        elif raw:
            if fl >= rf - FLAT_TOL and t - TOL <= h <= t + M.RAW_OVER + 0.1: continue
        elif abs(h - t) <= TOL: continue
        if raw: y, g, ach, _ = M.drive_raw(x, t, rf)
        else: y, g, ach = M.drive(x, t)
        data, ns, pcmb = G.encode_for(w, y[:, None], M.R, rail=raw)
        assert ns == w.get('samples') and len(data) == w.get('size'), (w.name, ns, len(data))
        repl[w.rec_off] = (data, ns, pcmb, ns / M.R)
        rep.append(dict(record=w.name, kind=k, before_head=round(h, 2), target_head=round(t, 2), gain_db=round(g, 2), raw=raw,
                        before_flat=round(fl, 1), target_flat=None if rf is None else round(rf, 1), _y=y, _w=w.rec_off,
                        cls=gun_class(w.name) if BODY else None, before_timbre=tb0))
        if ach < t - SHORT: short.append((w.name, round(ach, 2), round(t, 2)))
    man = dict(key=b.key, group=b.group, id=b.id, file=b.rel, ref_head=round(ref, 2), ref_from=how, clips=len(rows), changed=len(repl),
               live_md5=m5, short_of_target=short, body_src_backup=nsrc[0], body_src_live=nsrc[1])
    if not repl:
        log('%-14s ref %.2f (%s): %d clips, all within %.2f dB, nothing to change' % (b.key, ref, how, len(rows), TOL)); man['unchanged'] = True
        return man, None
    nwhd, nwav, _ = G.rebuild(whd, wav, repl, None, log=lambda *a: None)
    assert nwhd == whd, 'WHD must be byte-identical'
    assert len(nwav) == len(wav) and nwav[:8] == wav[:8]
    olds = sorted((ws[r].get('off'), ws[r].get('off') + ws[r].get('size')) for r in repl)
    diff = np.nonzero(np.frombuffer(wav, np.uint8) != np.frombuffer(nwav, np.uint8))[0]
    st = np.array([a for a, _ in olds]); en = np.array([c for _, c in olds]); kk = np.searchsorted(st, diff, side='right') - 1
    assert (kk >= 0).all() and (diff < en[kk]).all(), 'WAV changed outside the replaced spans'
    nws = {w.rec_off: w for w in G.waves(nwhd)}; mins = []
    for e in rep:
        d = G.decode_wave(nwav, nws[e['_w']])[:, 0]; c = float(np.corrcoef(d, e['_y'])[0, 1]); mins.append(c); assert c > 0.95, (e['record'], c)
        e['after_head'] = round(M.head_db(d), 2); e['after_flat'] = round(M.flat_pct(d), 1)
        if BODY:
            e['after_timbre'] = timbre(d)
            if b.key in PREVIEW:
                pd = os.path.join(out, 'preview', b.key.replace('/', '_')); os.makedirs(pd, exist_ok=True); nm = e['record'].split('/')[-1][:-4]
                G.write_wav(os.path.join(pd, nm + '_live.wav'), G.to_i16(G.decode_wave(wav, ws[e['_w']])), M.R)
                G.write_wav(os.path.join(pd, nm + '_' + PREVIEW_NAME + '.wav'), G.to_i16(G.decode_wave(nwav, nws[e['_w']])), M.R)
        del e['_y'], e['_w']
    spans = [(a, c - a) for a, c in olds]
    d = os.path.join(out, 'Banks', b.group); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, b.id + '.new'), 'wb').write(b''.join(nwav[a:a + n] for a, n in spans))
    open(os.path.join(d, b.id + '.old'), 'wb').write(b''.join(wav[a:a + n] for a, n in spans))
    man.update(spans=[x for sp in spans for x in sp], output_md5=md5(nwav), wav_bytes_changed=int(len(diff)), min_corr=round(min(mins), 4), detail=rep)
    log('%-14s ref %.2f (%s): %d/%d records changed, WAV bytes %d, min corr %.4f%s' % (b.key, ref, how, len(repl), len(rows), len(diff), min(mins),
        '' if not short else ', %d short of target (gain cap)' % len(short)))
    return man, True


def cmd_build(a):
    global RAW, TAG, BODY
    force = '--force' in a
    if force: a.remove('--force')
    if '--raw' in a: a.remove('--raw'); RAW = True; TAG = '1025gunraw'
    if '--body' in a: a.remove('--body'); RAW = BODY = True; TAG = '1107gunraw'
    groups = split_groups(a); out = a[0]; os.makedirs(out, exist_ok=True); res = []
    for b in banks(groups): res.append(build_bank(b, out, force, print)[0])
    changed = [m for m in res if not m.get('unchanged')]
    json.dump(dict(tag=TAG, raw=RAW, body=BODY, banks=res), open(os.path.join(out, 'report.json'), 'w'), indent=1)
    mf = {m['key']: dict(file=m['file'], input_md5=m['live_md5'], output_md5=m['output_md5'], spans=m['spans'], group=m['group'], id=m['id']) for m in changed}
    json.dump(dict(tag=TAG, banks=mf), open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
    for m in changed:                                       # the output md5 is a valid input of a re-run (idempotent)
        e = pins.setdefault(m['key'], dict(inputs=[], outputs=[]))
        if m['output_md5'] not in e['outputs']: e['outputs'].append(m['output_md5'])
    json.dump(pins, open(PINS, 'w'), indent=1, sort_keys=True)
    with open(os.path.join(out, 'AB_LIST.txt'), 'w') as f:
        f.write('%-14s %-44s %-8s %7s %7s %6s %7s %6s %6s %6s\n' % ('bank', 'record', 'kind', 'before', 'target', 'gain', 'after', 'flat0', 'flatT', 'flat1'))
        for m in changed:
            for e in m['detail']:
                f.write('%-14s %-44s %-8s %7.2f %7.2f %6.2f %7.2f %6.1f %6s %6.1f\n' % (m['key'], e['record'].split('/')[-1][:44], e['kind'], e['before_head'], e['target_head'],
                        e['gain_db'], e['after_head'], e['before_flat'], '-' if not e['raw'] else '%.1f' % e['target_flat'], e['after_flat']))
    if BODY: write_installer(out, what=INST_WHAT, blurb=INST_BLURB)
    else: write_installer(out)
    print('built: %d banks checked, %d need changes, %d records, %.1f MB of new spans' % (len(res), len(changed), sum(m['changed'] for m in changed),
          sum(os.path.getsize(os.path.join(out, 'Banks', m['group'], m['id'] + '.new')) for m in changed) / 1e6))
    return 0


def cmd_verify(a):
    out = a[0]; rep = json.load(open(os.path.join(out, 'report.json'))); n = 0; worst = 0.0
    for m in rep['banks']:
        b = [x for x in banks((m['group'],)) if x.key == m['key']][0]; whd, wav = b.load()
        assert md5(wav) == m['live_md5'], 'live bank changed since the build: ' + m['key']
        if m.get('unchanged'):
            ref, how, rows = rows_of(b, whd, wav)
            assert all(abs(h - t) <= TOL or (rep.get('raw') and k == 'gun' and t - TOL <= h <= t + M.RAW_OVER + 0.1) for _, k, h, t in rows), m['key']; print('verify %-14s untouched, all %d clips within %.2f dB' % (m['key'], len(rows), TOL)); n += 1; continue
        d = os.path.join(out, 'Banks', m['group']); new = open(os.path.join(d, m['id'] + '.new'), 'rb').read(); old = open(os.path.join(d, m['id'] + '.old'), 'rb').read()
        nv = bytearray(wav); p = 0; sp = m['spans']
        for i in range(0, len(sp), 2):
            a0, ln = sp[i], sp[i + 1]; assert bytes(nv[a0:a0 + ln]) == old[p:p + ln], 'old bytes differ from live'; nv[a0:a0 + ln] = new[p:p + ln]; p += ln
        assert p == len(new) == len(old) and md5(bytes(nv)) == m['output_md5'], m['key']
        nv = bytes(nv); un = bytearray(nv); p = 0
        for i in range(0, len(sp), 2): un[sp[i]:sp[i] + sp[i + 1]] = old[p:p + sp[i + 1]]; p += sp[i + 1]
        assert md5(bytes(un)) == m['live_md5'], 'undo does not restore ' + m['key']
        ref, how, rows = rows_of(b, whd, nv); names = {e['record'] for e in m['detail']}
        for w, k, h, t in rows:
            over = M.RAW_OVER + 0.15 if rep.get('raw') and M.kind(w.name) == 'gun' else 0.3      # --raw: flat tops may cost up to RAW_OVER
            assert abs(h - t) <= TOL + 0.2 or (m['short_of_target'] and any(s[0] == w.name for s in m['short_of_target'])) or h <= t + over, (m['key'], w.name, h, t)
            worst = max(worst, abs(h - t) if w.name not in {s[0] for s in m['short_of_target']} else 0)
        assert names <= {w.name for w, *_ in rows} | ({w.name for w in G.waves(whd) if M.REF.search(w.name)} if rep.get('raw') else set())
        print('verify %-14s %2d/%2d records changed, all %d clips at target, apply+undo reproduce the md5s, WHD untouched' % (m['key'], m['changed'], m['clips'], len(rows))); n += 1
    print('verify: %d banks PASS (worst residual %.2f dB, excluding clips at the gain cap)' % (n, worst)); return 0


def write_installer(out, tag=None, what='gun sounds', blurb=None):
    ps = r'''# Gun sounds at ONE loudness on every map (tools/kl_gunsnd_all.py), staged 2026-10-24. Every gun-shot / distant record in the banks
# listed in manifest.json is re-driven to the S&W MP45 (= Desert Eagle clip) loudness. Only those records' data spans inside each
# .WAV change; .WHD / .SND / zips / .hti are NOT touched, file sizes are identical. Patched IN PLACE from Banks\<group>\<id>.new,
# UNDO writes Banks\<group>\<id>.old back. Before the first patch of a bank its .WAV is copied to <name>.WAV.before-1024gunsnd2
# (never overwritten if it exists). md5-chained: ALL banks must be exactly the build input (or already the build output) or nothing
# is written. Refuses while kl2.exe runs. -Groups maps,stock,story limits it. -Root <folder> = rehearsal on a copy of the game folder.
param([switch]$Undo, [string]$Root = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [string]$Groups = 'maps,stock,story')
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
if (Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 }) { 'kl2.exe is running: close the game first'; exit 1 }
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
function Patch($file, $spans, $bytes) {
  $fs = [System.IO.File]::Open($file, 'Open', 'ReadWrite', 'None')
  try { $p = 0
    for ($i = 0; $i -lt $spans.Count; $i += 2) { $fs.Position = [int64]$spans[$i]; $fs.Write($bytes, $p, [int]$spans[$i + 1]); $p += [int]$spans[$i + 1] }
    $fs.Flush() } finally { $fs.Close() }
}
$want = $Groups.Split(',')
$man = Get-Content -LiteralPath "$here\manifest.json" -Raw | ConvertFrom-Json
$todo = @(); $bad = @()
foreach ($p in $man.banks.PSObject.Properties) {
  $e = $p.Value
  if ($want -notcontains $e.group) { continue }
  $t = "$Root\$($e.file)"
  if (-not (Test-Path -LiteralPath $t)) { "skip $($p.Name): not installed"; continue }
  $cur = md5 $t
  if ($Undo) {
    if ($cur -eq $e.input_md5) { "ok   $($p.Name): already the original"; continue }
    if ($cur -ne $e.output_md5) { $bad += "$($p.Name): .WAV is neither the original nor what this script wrote"; continue }
  } else {
    if ($cur -eq $e.output_md5) { "ok   $($p.Name): already has the new gun sounds"; continue }
    if ($cur -ne $e.input_md5) { $bad += "$($p.Name): .WAV is not the one these sounds were built from (changed since)"; continue }
  }
  $f = "$here\Banks\$($e.group)\$($e.id)." + $(if ($Undo) { 'old' } else { 'new' })
  if (-not (Test-Path -LiteralPath $f)) { "ABORT: missing $f"; exit 4 }
  $todo += [pscustomobject]@{ Key = $p.Name; Target = $t; Src = $f; Spans = @($e.spans); In = $e.input_md5; Out = $e.output_md5 }
}
if ($bad.Count) { "REFUSED, nothing written:"; $bad | ForEach-Object { "  $_" }; exit 3 }
if (-not $Undo) {
  $need = 0; foreach ($x in $todo) { if (-not (Test-Path -LiteralPath "$($x.Target).before-1024gunsnd2")) { $need += (Get-Item -LiteralPath $x.Target).Length } }
  $drv = (Get-Item -LiteralPath $Root).PSDrive; if ($drv.Free -lt ($need + 200MB)) { "ABORT: not enough free space for the backups ($([int]($need/1MB)) MB + 200 MB)"; exit 6 }
  foreach ($x in $todo) { $b = "$($x.Target).before-1024gunsnd2"; if (-not (Test-Path -LiteralPath $b)) { Copy-Item -LiteralPath $x.Target -Destination $b; if ((md5 $b) -ne $x.In) { "FAILED backup of $($x.Key)"; exit 7 } } }
}
foreach ($x in $todo) {
  Patch $x.Target $x.Spans ([System.IO.File]::ReadAllBytes($x.Src))
  $w = if ($Undo) { $x.In } else { $x.Out }
  if ((md5 $x.Target) -ne $w) { "FAILED md5 check: $($x.Key) - run the other script (UNDO / INSTALL) to repair"; exit 5 }
  "done $($x.Key)"
}
if ($Undo) { "banks restored: $($todo.Count)" } else { "banks updated: $($todo.Count). Backups: *.WAV.before-1024gunsnd2. Undo: UNDO gun sounds all maps.bat" }
'''
    tag = tag or TAG
    ps = ps.replace('before-1024gunsnd2', 'before-' + tag)        # --raw / kl_fxsnd builds back up under their own tag
    if what != 'gun sounds':                                       # kl_fxsnd.py: same installer, other wording
        ps = ps.replace('the new gun sounds', 'the new ' + what).replace('UNDO gun sounds all maps.bat', 'UNDO %s all maps.bat' % what)
        ps = ps.replace('# Gun sounds at ONE loudness on every map (tools/kl_gunsnd_all.py)', '# %s (%s)' % (what, 'tools/kl_gunsnd_all.py build --body, re/gun_sounds_1107.md' if BODY else 'tools/kl_fxsnd.py on kl_gunsnd_all'))
    blurb = blurb or ('Every gun-shot sample at the S&W MP45 loudness%s: KLExpansion maps, the 9 stock FA maps, the story levels' % (' and hard clip' if RAW else ''))
    open(os.path.join(out, 'install_gunsnd2.ps1'), 'w', newline='\r\n').write(ps)
    open(os.path.join(out, 'INSTALL %s all maps.bat' % what), 'w', newline='\r\n').write(
        '@echo off\r\nrem %s (md5-checked; copies kept as .before-%s).\r\n' % (blurb, tag) + ('echo %s\r\n' % blurb.split(':')[0] if BODY else '') +
        'powershell -ExecutionPolicy Bypass -File "%~dp0install_gunsnd2.ps1"\r\npause\r\n')
    open(os.path.join(out, 'UNDO %s all maps.bat' % what), 'w', newline='\r\n').write(
        '@echo off\r\nrem Puts the previous %s back (md5-checked).\r\npowershell -ExecutionPolicy Bypass -File "%%~dp0install_gunsnd2.ps1" -Undo\r\npause\r\n' % what)


def main(a):
    if not a: print(__doc__); return 1
    c, r = a[0], list(a[1:])
    if c == 'audit': return cmd_audit(r)
    if c == 'pin': return cmd_pin(r)
    if c == 'build': return cmd_build(r)
    if c == 'verify': return cmd_verify(r)
    print(__doc__); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
