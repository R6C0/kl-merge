#!/usr/bin/env python3
"""
kl_gunsnd_match.py - make every gun's fire sound as loud and as driven as the S&W MP45's (owner 2026-10-24: "please make the
guns wavesound like the sw mp45 - its got the best amount of loudness and like its getting distorted").

WHAT THE MP45 PLAYS (READ, re/map_guns.md "Stock Dog Days shares definitions": 'the SW MP45 plays hg_deserteagle'; in every
bank hg_sw_mp45 has no sound objects of its own): HG_DesertEagle_Shot_01..03. Measured in the live banks (head = RMS of the
first 250 ms after the onset): head -2.8 dBFS, crest (peak - head) 2.8 dB, ~7 % of all samples sit AT the clip ceiling
(= hard-clipped at the source), the envelope stays above -7 dB for 250 ms. Other guns: AK74 head -7, Type79 -6.5, MPi69 -8.3,
MAC-10 -8.8, silenced SMGs -9..-11.6, M9 -5, distant layers -8..-14, ~0.005..2 % of samples at the ceiling.

    python kl_gunsnd_match.py analyze [map ids ...]            # table: reference + every gun clip, per map (read-only)
    python kl_gunsnd_match.py build <outdir> [map ids ...]     # processed WHD/WAV per map + manifest + A/B previews
    python kl_gunsnd_match.py verify <outdir>                  # independent re-check of what build wrote
    python kl_gunsnd_match.py manifest <outdir>                # manifest.json for INSTALL / UNDO (spans, md5s)

HOW (keeps every offset; same as kl_dmgunsnd_build): each shot record is decoded, DC removed, gain-driven into a knee soft
clipper until its head RMS equals the reference's, and re-encoded into the SAME record: same sample count, same data bytes, so
the .WHD fields, the .SND wave seconds (+0x18), the zip and every other record stay byte-identical (only WAV bytes inside the
replaced spans change). The reference clips (DesertEagle) are not touched. Targets (dBFS head RMS):
    guns            = reference head (about -2.85)
    silenced guns   = reference - 3.7 (about -6.5; a suppressed shot that is as loud as an open one would be wrong)
    distant layers  = reference - 3.7 (they are mixed over the near shot)
Gain is capped at +18 dB (the clip's decay tail is lifted by the same gain: more cap = more hiss in the tails).
Not LUFS: head RMS of the transient, which is what a gunshot's loudness is; peak is 0 dBFS in every stock clip already.
"""
import hashlib, json, os, re, struct, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gunsnd as G
import kl_dmgunsnd_build as B

R = 32000
SEL = re.compile(r'(_Shot_0\d\.wav|Distant_Shot_\w+\.wav|Shotgun_Hawk_Police_0\d\.wav)$', re.I)
REF = re.compile(r'/HG_DesertEagle/HG_DesertEagle_Shot_0\d\.wav$', re.I)
SIL_DROP = 3.7          # silenced + distant sit this far under the reference head level
MAXGAIN = 18.0          # dB
KNEE = 0.8              # linear up to here, tanh beyond (asymptote 1.0)
CEIL = 0.99


def kind(name):
    n = name.lower()
    if 'distant_shot' in n: return 'distant'
    if 'silenced' in n: return 'silenced'
    return 'gun'


def onset(x):
    pk = np.abs(x).max(); i = int(np.argmax(np.abs(x) > 0.1 * pk)); return max(0, i - int(0.002 * R))


def head_db(x, ms=250):
    i = onset(x); s = x[i:i + int(ms / 1000 * R)]
    return float(20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9))


def stats(x):
    pk = np.abs(x).max(); h = head_db(x)
    return dict(peak=round(float(20 * np.log10(pk + 1e-9)), 2), head=round(h, 2), rms=round(float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)), 2),
                crest=round(float(20 * np.log10(pk + 1e-9)) - h, 2), atpeak_pct=round(float((np.abs(x) >= 0.98 * pk).mean() * 100), 2),
                secs=round(len(x) / R, 3))


def clip(u):
    a = np.abs(u); o = np.where(a <= KNEE, a, KNEE + (1 - KNEE) * np.tanh((a - KNEE) / (1 - KNEE)))
    return np.sign(u) * np.minimum(o, 1.0) * CEIL


def drive(x, target_db):
    """-> (processed float clip, gain dB used, achieved head dB). Bisect the gain so the head RMS after the clipper = target."""
    x = x - x.mean(); x = x / (np.abs(x).max() + 1e-9)
    lo, hi = -6.0, MAXGAIN
    f = lambda g: head_db(clip(x * 10 ** (g / 20)))
    if f(hi) < target_db: g = hi
    elif f(lo) > target_db: g = lo
    else:
        for _ in range(40):
            m = (lo + hi) / 2
            if f(m) < target_db: lo = m
            else: hi = m
        g = (lo + hi) / 2
    y = clip(x * 10 ** (g / 20))
    n = int(0.03 * R); y[-n:] *= np.linspace(1, 0, n)          # the very end: a 30 ms fade (the lifted tail must not click)
    return y, g, head_db(y)


def bank(mid):
    folder = os.path.join(B.MAPS, mid)
    if not os.path.isdir(folder): return None
    f = [x for x in os.listdir(folder) if re.match(r'F0\d_Main\.WHD$', x)]
    if not f: return None
    slot = f[0][:3]; base = os.path.join(folder, slot + '_Main')
    return slot, base, open(base + '.WHD', 'rb').read(), open(base + '.WAV', 'rb').read()


def maps():
    return sorted(d for d in os.listdir(B.MAPS) if bank(d))


def reference(whd, wav):
    hs = [head_db(G.decode_wave(wav, w)[:, 0]) for w in G.waves(whd) if REF.search(w.name)]
    assert len(hs) == 3, 'reference clips missing'
    return float(np.mean(hs))


def targets(whd):
    return [w for w in G.waves(whd) if SEL.search(w.name) and not REF.search(w.name)]


def cmd_analyze(ids):
    for mid in ids or maps():
        slot, base, whd, wav = bank(mid); ref = reference(whd, wav)
        print('== %s (%s) reference head %.2f dBFS' % (mid, slot, ref))
        for w in G.waves(whd):
            if not (SEL.search(w.name)): continue
            s = stats(G.decode_wave(wav, w)[:, 0])
            print('  %-40s %-8s peak %6.2f head %6.2f rms %6.2f crest %5.2f atpeak %5.2f%%' % (
                w.name.split('/')[-1][:40], 'REF' if REF.search(w.name) else kind(w.name), s['peak'], s['head'], s['rms'], s['crest'], s['atpeak_pct']))


def build_map(mid, out, pdir, log=print):
    slot, base, whd, wav = bank(mid); ref = reference(whd, wav)
    ws = {w.rec_off: w for w in G.waves(whd)}
    repl = {}; rep = []; offs = {}
    for w in targets(whd):
        assert w.codec == 0x11 and w.get('rate') == R and w.get('ch') == 1 and not w.streamed, w.name
        k = kind(w.name); tgt = ref if k == 'gun' else ref - SIL_DROP
        x = G.decode_wave(wav, w)[:, 0]
        o = w.get('off')
        assert o not in offs, 'two records share data %s / %s' % (offs[o], w.name); offs[o] = w.name
        y, g, ach = drive(x, tgt)
        data, ns, pcmb = G.encode_for(w, y[:, None], R)
        assert ns == w.get('samples') and len(data) == w.get('size'), (w.name, ns, len(data))     # in place, identical size
        repl[w.rec_off] = (data, ns, pcmb, ns / R)
        rep.append(dict(record=w.name, kind=k, target_head=round(tgt, 2), gain_db=round(g, 2), before=stats(x), after=stats(y), _y=y, _x=x, _w=w.rec_off))
        if mid == pdir[0]:
            tag = w.name.split('/')[-1][:-4]
            G.write_wav(os.path.join(pdir[1], tag + '_A_before.wav'), G.to_i16(x[:, None]), R)
            G.write_wav(os.path.join(pdir[1], tag + '_B_after.wav'), G.to_i16(y[:, None]), R)
    nwhd, nwav, _ = G.rebuild(whd, wav, repl, None, log=lambda *a: None)
    # checks
    assert len(nwav) == len(wav) and len(nwhd) == len(whd) and nwav[:8] == wav[:8]
    assert nwhd == whd, 'WHD must be byte-identical (same sizes and sample counts)'
    olds = sorted((ws[r].get('off'), ws[r].get('off') + ws[r].get('size')) for r in repl)
    diff = np.nonzero(np.frombuffer(wav, np.uint8) != np.frombuffer(nwav, np.uint8))[0]
    st = np.array([a for a, _ in olds]); en = np.array([b for _, b in olds]); kk = np.searchsorted(st, diff, side='right') - 1
    assert (kk >= 0).all() and (diff < en[kk]).all(), 'WAV changed outside the replaced spans'
    nws = {w.rec_off: w for w in G.waves(nwhd)}; mins = []
    for e in rep:
        d = G.decode_wave(nwav, nws[e['_w']])[:, 0]; assert len(d) == len(e['_y'])
        c = float(np.corrcoef(d, e['_y'])[0, 1]); mins.append(c); assert c > 0.95, (e['record'], c)
        e['decoded'] = stats(d)
        del e['_y'], e['_x'], e['_w']
    # the disk is full (G: 88 KB free, C: 5 GB): stage SPANS, not 27 x 23 MB WAVs. spans = [offset, length] of each replaced
    # record's data; <id>.new = their new bytes back to back, <id>.old = the live bytes (for UNDO)
    os.makedirs(os.path.join(out, 'Maps'), exist_ok=True)
    spans = [(a, b - a) for a, b in olds]
    open(os.path.join(out, 'Maps', mid + '.new'), 'wb').write(b''.join(nwav[a:a + n] for a, n in spans))
    open(os.path.join(out, 'Maps', mid + '.old'), 'wb').write(b''.join(wav[a:a + n] for a, n in spans))
    man = dict(map=mid, slot=slot, spans=spans, reference_head=round(ref, 2), whd_untouched=True,
               live_md5={'WHD': hashlib.md5(whd).hexdigest(), 'WAV': hashlib.md5(wav).hexdigest()},
               new_md5={'WHD': hashlib.md5(nwhd).hexdigest(), 'WAV': hashlib.md5(nwav).hexdigest()},
               records=len(repl), wav_bytes_changed=int(len(diff)), min_corr=round(min(mins), 4), detail=rep)
    log('%-8s %s: %d records, ref head %.2f, WAV bytes changed %d, min corr %.4f' % (mid, slot, len(repl), ref, len(diff), min(mins)))
    return man


def cmd_build(out, ids):
    os.makedirs(out, exist_ok=True); pd = os.path.join(out, 'preview'); os.makedirs(pd, exist_ok=True)
    ids = ids or maps(); res = [build_map(m, out, ('DM01', pd)) for m in ids]
    json.dump(dict(maps=res), open(os.path.join(out, 'report.json'), 'w'), indent=1)
    # A/B list (first map, one row per record)
    with open(os.path.join(out, 'AB_LIST.txt'), 'w') as f:
        m = res[0]; f.write('A/B list from %s (head = RMS of the first 250 ms, dBFS; reference MP45 = DesertEagle head %.2f)\n' % (m['map'], m['reference_head']))
        f.write('%-42s %-8s %6s %6s %6s %6s %6s %6s %6s\n' % ('clip', 'kind', 'tgt', 'gain', 'pk0', 'head0', 'rms0', 'head1', 'rms1'))
        for e in m['detail']:
            f.write('%-42s %-8s %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f\n' % (e['record'].split('/')[-1][:42], e['kind'], e['target_head'], e['gain_db'],
                    e['before']['peak'], e['before']['head'], e['before']['rms'], e['decoded']['head'], e['decoded']['rms']))
    return 0


def cmd_verify(out):
    rep = json.load(open(os.path.join(out, 'report.json'))); n = 0
    for m in rep['maps']:
        mid, slot = m['map'], m['slot']; lb = os.path.join(B.MAPS, mid, slot + '_Main')
        lw, lv = open(lb + '.WHD', 'rb').read(), open(lb + '.WAV', 'rb').read()
        assert hashlib.md5(lw).hexdigest() == m['live_md5']['WHD'] and hashlib.md5(lv).hexdigest() == m['live_md5']['WAV'], 'live bank changed since the build: ' + mid
        new = open(os.path.join(out, 'Maps', mid + '.new'), 'rb').read(); old = open(os.path.join(out, 'Maps', mid + '.old'), 'rb').read()
        nv = bytearray(lv); p = 0
        for a, ln in m['spans']:
            assert bytes(nv[a:a + ln]) == old[p:p + ln], 'old bytes differ from live'; nv[a:a + ln] = new[p:p + ln]; p += ln
        assert p == len(new) == len(old)
        assert hashlib.md5(bytes(nv)).hexdigest() == m['new_md5']['WAV'], mid
        nv = bytes(nv)                                                       # UNDO leg: put the old bytes back
        un = bytearray(nv); p = 0
        for a, ln in m['spans']: un[a:a + ln] = old[p:p + ln]; p += ln
        assert hashlib.md5(bytes(un)).hexdigest() == m['live_md5']['WAV'], 'undo does not restore ' + mid
        ref = reference(lw, nv); names = {e['record'] for e in m['detail']}; tot = 0
        for w in G.waves(lw):
            if w.name in names:
                d = G.decode_wave(nv, w)[:, 0]; assert len(d) == w.get('samples'); h = head_db(d)
                tgt = ref if kind(w.name) == 'gun' else ref - SIL_DROP
                assert h <= tgt + 0.6, (mid, w.name, h, tgt); tot += 1
        assert tot == m['records']; n += 1
        print('verify %-8s %2d records re-decoded (head at/below target), apply+undo reproduce the md5s, WHD untouched' % (mid, tot))
    print('verify: %d maps PASS' % n)
    return 0


def cmd_manifest(out):
    """manifest.json for the installer: per map the live WAV's path, its md5 before / after, the spans (flattened [off,len,...])"""
    rep = json.load(open(os.path.join(out, 'report.json'))); man = {}
    for m in rep['maps']:
        man[m['map']] = dict(file=m['slot'] + '_Main.WAV', input_md5=m['live_md5']['WAV'], output_md5=m['new_md5']['WAV'],
                             spans=[x for sp in m['spans'] for x in sp], bytes=sum(sp[1] for sp in m['spans']))
    json.dump(dict(tag='1024gunsnd', maps=man), open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    print('manifest: %d maps' % len(man)); return 0


def main(a):
    if not a: print(__doc__); return 1
    if a[0] == 'analyze': return cmd_analyze(a[1:]) or 0
    if a[0] == 'build': return cmd_build(a[1], a[2:])
    if a[0] == 'verify': return cmd_verify(a[1])
    if a[0] == 'manifest': return cmd_manifest(a[1])
    print(__doc__); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
