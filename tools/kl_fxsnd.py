#!/usr/bin/env python3
"""
kl_fxsnd.py - destruction sounds as loud and as raw as the S&W MP45 (owner 2026-10-25: "i want destruction e.g. vehicle explosions,
fire extinguishers and glass breaking to be louder like how the mp45 is").

Sibling of kl_gunsnd_all (imports its bank discovery, md5 pins, installer and the kl_gunsnd_match drive_raw: hard clip to full
scale, head = RMS of the first 250 ms after the onset). Starts from the banks AS INSTALLED (the 1025gunraw pass is in them, every
live .WAV md5 must be a pinned input / output of kl_gunsnd_all) and never touches a gun record (SEL / REF names are refused).

WHICH RECORDS (full record name, codec 0x11 mono only; stereo PCM / streamed ones are listed as skipped, not changed):
    explosion  SFX/Explosions/*  (cars, tyres, pre-explosion, barrels = what an extinguisher / fuel can plays (GUESS), helicopter,
               wall, mine, vault, elevator, propane, implosions) + LevelSetup/All/Explosions + Capatulio_Explodes
               NOT: Implosion_Revert (stereo), Elevator_Falling (a fall), Bomb_WarmUp (beeps)
    glass      SFX/Impacts/GlassBreak/*, SFX/Impacts/Shatter/Glass/* (Small/Medium/Big), SFX/Impacts/Bullet/Glass/Bottles (bottle breaks)
               NOT: Glass_Crack, footsteps on glass, Montre (display-case bullet impacts), door kicks
    burst      SFX/Environment/Fire/Cannisters/Fire_01..03 (the only canister / extinguisher-like record by name; GUESS)
               NOT: fire LOOPS (car fire, flames, flares)
Target: head = the bank's own Desert Eagle head (what the MP45 plays; -3.15 fallback), flat tops = FALLBACK_FLAT %, at most +0.6 dB.
A record already as loud (head >= target - 0.35) with flat tops (or already > target + 0.6) is NOT touched: nothing is turned down.
Same sample count / same byte span per record as the gun pass: tails keep their length, .WHD / .SND / zips stay byte-identical.
Gain cap 24 dB (the gun pass uses 18): glass shatters sit at -25 dB heads.

    python kl_fxsnd.py audit  [--groups maps,stock,story]       read-only: every destruction record, head / flat, per bank
    python kl_fxsnd.py build <outdir> [--groups ...] [--force]  spans + manifest + report + INSTALL / UNDO scripts (tag 1025fxraw)
    python kl_fxsnd.py verify <outdir>                          independent re-check (apply, re-decode, undo, guns untouched)
"""
import json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gunsnd as G
import kl_gunsnd_match as M
import kl_gunsnd_all as A

TAG = '1025fxraw'
WHAT = 'destruction sounds'
FX_GAIN = 24.0
PINS = os.path.join(HERE, 'kl_fxsnd.pins.json')
CLASSES = (
    ('explosion', re.compile(r'(^SFX/Explosions/|^LevelSetup/All/Explosions/|/Capatulio_Explodes/)', re.I)),
    ('glass', re.compile(r'(^SFX/Impacts/GlassBreak/|^SFX/Impacts/Shatter/Glass/|^SFX/Impacts/Bullet/Glass/Bottles/)', re.I)),
    ('burst', re.compile(r'^SFX/Environment/Fire/Cannisters/', re.I)),
)
NOT = re.compile(r'(Implosion_Revert|Elevator_Falling|Bomb_WarmUp)', re.I)


def fx_class(name):
    if M.SEL.search(name) or M.REF.search(name) or NOT.search(name): return None
    for c, rx in CLASSES:
        if rx.search(name): return c
    return None


def usable(w): return w.codec == 0x11 and w.get('ch') == 1 and not w.streamed


def rated(w, fn, *a):
    """kl_gunsnd_match measures at a fixed 32 kHz; destruction records come at 9012..32000 Hz: set its rate per record"""
    old = M.R; M.R = w.get('rate')
    try: return fn(*a)
    finally: M.R = old


def md5(b): return A.md5(b)


def rows_of(b, whd, wav):
    """-> (ref, how, rf, [(w, class, head, flat)], [(w, class, why)] skipped)"""
    ref, how = A.ref_of(whd, wav); rf = A.FALLBACK_FLAT        # ONE flat-top target, as the gun --raw pass (DM Deagle clips measure 0.3 %)
    rows = []; skip = []
    for w in G.waves(whd):
        c = fx_class(w.name)
        if not c: continue
        if not usable(w): skip.append((w, c, 'codec %#x ch %d%s' % (w.codec, w.get('ch'), ' streamed' if w.streamed else ''))); continue
        x = G.decode_wave(wav, w)[:, 0]
        rows.append((w, c, rated(w, M.head_db, x), rated(w, M.flat_pct, x)))
    return ref, how, rf, rows, skip


def untouched(h, fl, t, rf): return h >= t - A.TOL and (fl >= rf - A.FLAT_TOL or h >= t + M.RAW_OVER)


def pinned_gun_state(b, m5):
    pins = json.load(open(A.PINS)) if os.path.exists(A.PINS) else {}
    e = pins.get(b.key)
    return bool(e and (m5 in e['inputs'] or m5 in e['outputs']))


def cmd_audit(a):
    groups = A.split_groups(a); H0 = []; F0 = []; per = {}
    for b in A.banks(groups):
        whd, wav = b.load(); ref, how, rf, rows, skip = rows_of(b, whd, wav)
        if not rows and not skip: continue
        todo = [r for r in rows if not untouched(r[2], r[3], ref, rf)]
        print('%-12s ref %6.2f (%s) flat %4.1f  %3d fx records, %3d to change, %d skipped' % (b.key, ref, how, rf, len(rows), len(todo), len(skip)))
        for w, c, h, fl in rows:
            H0.append(h); F0.append(fl)
            if '-v' in a: print('      %-9s head %6.2f flat %5.1f %s' % (c, h, fl, w.name.split('SFX/')[-1]))
        for w, c, why in skip: print('      SKIP %-9s %s (%s)' % (c, w.name.split('SFX/')[-1], why))
        per[b.key] = len(rows)
    print('TOTAL %d records in %d banks, head median %.2f, flat median %.1f' % (len(H0), len(per), np.median(H0), np.median(F0)))
    return 0


def build_bank(b, out, force, log):
    whd, wav = b.load(); m5 = md5(wav)
    if not pinned_gun_state(b, m5) and not force:
        raise SystemExit('REFUSED %s: live .WAV md5 %s is not a pinned state of kl_gunsnd_all (the gun pass is not in it?)' % (b.key, m5))
    pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
    ref, how, rf, rows, skip = rows_of(b, whd, wav)
    ws = {w.rec_off: w for w in G.waves(whd)}; repl = {}; rep = []; offs = {}
    for w, c, h, fl in rows:
        o = w.get('off'); assert o not in offs, 'two records share data %s / %s' % (offs[o], w.name); offs[o] = w.name
        assert not M.SEL.search(w.name), 'gun record in the fx set: ' + w.name
        if untouched(h, fl, ref, rf): continue
        x = G.decode_wave(wav, w)[:, 0]
        old = (M.R, M.MAXGAIN); M.R = w.get('rate'); M.MAXGAIN = FX_GAIN
        try: y, g, ach, _ = M.drive_raw(x, ref, rf); h1 = M.head_db(y)
        finally: M.R, M.MAXGAIN = old
        data, ns, pcmb = G.encode_for(w, y[:, None], w.get('rate'), rail=True)
        assert ns == w.get('samples') and len(data) == w.get('size'), (w.name, ns, len(data))
        repl[w.rec_off] = (data, ns, pcmb, ns / w.get('rate'))
        rep.append(dict(record=w.name, kind=c, rate=w.get('rate'), before_head=round(h, 2), target_head=round(ref, 2), gain_db=round(g, 2),
                        before_flat=round(fl, 1), target_flat=round(rf, 1), _y=y, _w=w.rec_off))
    man = dict(key=b.key, group=b.group, id=b.id, file=b.rel, ref_head=round(ref, 2), ref_flat=round(rf, 1), ref_from=how, clips=len(rows), changed=len(repl),
               live_md5=m5, skipped=[(w.name, why) for w, c, why in skip])
    if not repl:
        log('%-12s %d fx records, nothing to change' % (b.key, len(rows))); man['unchanged'] = True; return man
    nwhd, nwav, _ = G.rebuild(whd, wav, repl, None, log=lambda *a: None)
    assert nwhd == whd, 'WHD must be byte-identical'
    assert len(nwav) == len(wav) and nwav[:8] == wav[:8]
    olds = sorted((ws[r].get('off'), ws[r].get('off') + ws[r].get('size')) for r in repl)
    diff = np.nonzero(np.frombuffer(wav, np.uint8) != np.frombuffer(nwav, np.uint8))[0]
    st = np.array([x for x, _ in olds]); en = np.array([y_ for _, y_ in olds]); kk = np.searchsorted(st, diff, side='right') - 1
    assert (kk >= 0).all() and (diff < en[kk]).all(), 'WAV changed outside the replaced spans'
    nws = {w.rec_off: w for w in G.waves(nwhd)}; mins = []
    for e in rep:
        w = nws[e['_w']]; d = G.decode_wave(nwav, w)[:, 0]; c = float(np.corrcoef(d, e['_y'])[0, 1]); mins.append(c); assert c > 0.95, (e['record'], c)
        e['after_head'] = round(rated(w, M.head_db, d), 2); e['after_flat'] = round(rated(w, M.flat_pct, d), 1); e['rec'] = e.pop('_w'); del e['_y']
    for r in ws.values():                                       # no gun record changed: every gun record's bytes are identical
        if M.SEL.search(r.name):
            o = r.get('off'); assert wav[o:o + r.get('size')] == nwav[o:o + r.get('size')], 'gun record changed: ' + r.name
    spans = [(x, y_ - x) for x, y_ in olds]
    d = os.path.join(out, 'Banks', b.group); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, b.id + '.new'), 'wb').write(b''.join(nwav[x:x + n] for x, n in spans))
    open(os.path.join(d, b.id + '.old'), 'wb').write(b''.join(wav[x:x + n] for x, n in spans))
    man.update(spans=[x for sp in spans for x in sp], output_md5=md5(nwav), wav_bytes_changed=int(len(diff)), min_corr=round(min(mins), 4), detail=rep)
    log('%-12s ref %.2f flat %.1f: %d/%d records changed, WAV bytes %d, min corr %.4f' % (b.key, ref, rf, len(repl), len(rows), len(diff), min(mins)))
    return man


def cmd_build(a):
    force = '--force' in a
    if force: a.remove('--force')
    groups = A.split_groups(a); out = a[0]; os.makedirs(out, exist_ok=True)
    res = [build_bank(b, out, force, print) for b in A.banks(groups)]
    res = [m for m in res if m['clips'] or m['skipped']]
    changed = [m for m in res if not m.get('unchanged')]
    json.dump(dict(tag=TAG, banks=res), open(os.path.join(out, 'report.json'), 'w'), indent=1)
    mf = {m['key']: dict(file=m['file'], input_md5=m['live_md5'], output_md5=m['output_md5'], spans=m['spans'], group=m['group'], id=m['id']) for m in changed}
    json.dump(dict(tag=TAG, banks=mf), open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    pins = json.load(open(PINS)) if os.path.exists(PINS) else {}
    for m in res:
        e = pins.setdefault(m['key'], dict(inputs=[], outputs=[]))
        if m['live_md5'] not in e['inputs'] and m['live_md5'] not in e['outputs']: e['inputs'].append(m['live_md5'])
        if not m.get('unchanged') and m['output_md5'] not in e['outputs']: e['outputs'].append(m['output_md5'])
    json.dump(pins, open(PINS, 'w'), indent=1, sort_keys=True)
    with open(os.path.join(out, 'AB_LIST.txt'), 'w') as f:
        f.write('%-12s %-9s %-52s %6s %7s %7s %6s %7s %6s %6s\n' % ('bank', 'class', 'record', 'rate', 'before', 'target', 'gain', 'after', 'flat0', 'flat1'))
        for m in changed:
            for e in m['detail']:
                f.write('%-12s %-9s %-52s %6d %7.2f %7.2f %6.2f %7.2f %6.1f %6.1f\n' % (m['key'], e['kind'], e['record'].split('SFX/')[-1][-52:], e['rate'], e['before_head'],
                        e['target_head'], e['gain_db'], e['after_head'], e['before_flat'], e['after_flat']))
    A.write_installer(out, TAG, WHAT, 'Destruction sounds (vehicle / barrel / extinguisher explosions, glass breaking) at the S&W MP45 loudness, hard clip, all banks')
    allr = [e for m in changed for e in m['detail']]
    print('built: %d banks with fx records, %d need changes, %d records changed (%d distinct names), %.1f MB of new spans' % (
        len(res), len(changed), len(allr), len({e['record'] for e in allr}), sum(os.path.getsize(os.path.join(out, 'Banks', m['group'], m['id'] + '.new')) for m in changed) / 1e6))
    if allr:
        print('median head %.2f -> %.2f dB, median flat %.1f -> %.1f %%' % (np.median([e['before_head'] for e in allr]), np.median([e['after_head'] for e in allr]),
              np.median([e['before_flat'] for e in allr]), np.median([e['after_flat'] for e in allr])))
    return 0


def cmd_verify(a):
    out = a[0]; rep = json.load(open(os.path.join(out, 'report.json'))); n = 0; guns = 0
    for m in rep['banks']:
        b = [x for x in A.banks((m['group'],)) if x.key == m['key']][0]; whd, wav = b.load()
        assert md5(wav) == m['live_md5'], 'live bank changed since the build: ' + m['key']
        if m.get('unchanged'): print('verify %-12s untouched, %d fx records already at target' % (m['key'], m['clips'])); n += 1; continue
        d = os.path.join(out, 'Banks', m['group']); new = open(os.path.join(d, m['id'] + '.new'), 'rb').read(); old = open(os.path.join(d, m['id'] + '.old'), 'rb').read()
        nv = bytearray(wav); p = 0; sp = m['spans']
        for i in range(0, len(sp), 2):
            a0, ln = sp[i], sp[i + 1]; assert bytes(nv[a0:a0 + ln]) == old[p:p + ln], 'old bytes differ from live'; nv[a0:a0 + ln] = new[p:p + ln]; p += ln
        assert p == len(new) == len(old) and md5(bytes(nv)) == m['output_md5'], m['key']
        nv = bytes(nv); un = bytearray(nv); p = 0
        for i in range(0, len(sp), 2): un[sp[i]:sp[i] + sp[i + 1]] = old[p:p + sp[i + 1]]; p += sp[i + 1]
        assert md5(bytes(un)) == m['live_md5'], 'undo does not restore ' + m['key']
        ref = m['ref_head']; hit = 0
        names = {e['rec']: e for e in m['detail']}          # record names repeat inside a bank (dialog): key by WHD record offset
        for w in G.waves(whd):
            o, sz = w.get('off'), w.get('size')
            if w.streamed: continue                                  # streamed records live in other files (their 'off' is not a .WAV offset)
            if M.SEL.search(w.name) or M.REF.search(w.name):          # guns: byte-identical
                assert wav[o:o + sz] == nv[o:o + sz], 'gun record changed: ' + w.name; guns += 1
            elif w.rec_off not in names:
                assert wav[o:o + sz] == nv[o:o + sz], 'unlisted record changed: ' + w.name
        for w in G.waves(whd):
            if w.rec_off in names:
                e = names[w.rec_off]; x = G.decode_wave(nv, w)[:, 0]; assert len(x) == w.get('samples')
                h = rated(w, M.head_db, x); fl = rated(w, M.flat_pct, x)
                assert h <= ref + M.RAW_OVER + 0.15, (m['key'], w.name, h, ref)          # never above the MP45 + 0.6 dB
                assert h >= e['before_head'] - 0.01, (m['key'], w.name, 'got quieter')
                assert abs(h - e['after_head']) < 0.02 and abs(fl - e['after_flat']) < 0.2, (m['key'], w.name)
                hit += 1
        assert hit == m['changed'], (m['key'], hit, m['changed'])
        print('verify %-12s %2d/%2d records changed, heads <= MP45 +0.6, no gun record touched, apply+undo reproduce the md5s, WHD untouched' % (m['key'], m['changed'], m['clips'])); n += 1
    print('verify: %d banks PASS (%d gun records checked byte-identical)' % (n, guns)); return 0


def main(a):
    if not a: print(__doc__); return 1
    c, r = a[0], list(a[1:])
    if c == 'audit': return cmd_audit(r)
    if c == 'build': return cmd_build(r)
    if c == 'verify': return cmd_verify(r)
    print(__doc__); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
