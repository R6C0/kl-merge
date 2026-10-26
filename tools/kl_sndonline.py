#!/usr/bin/env python3
"""
kl_sndonline.py - pass 2 of "all sounds at MP45 loudness" (owner 2026-10-26: "louder gunshots ... mp45 and glass destruction and any
other kind"). Derived from kl_fxsnd.py (same drive_raw: hard clip, head = the bank's Desert Eagle head, -3.15 fallback, flat tops
19.8 %, at most +0.6 dB). Tag 1026sndon2, backups *.WAV.before-1026sndon2, md5-chained on top of whatever is live
(1025gunraw -> 1025fxraw -> 1026sndon -> this). Never touches a gun record; only records no earlier pass changed.

WHICH RECORDS
  every bank (maps, stock, story):
    pcmfx    IN-MEMORY STEREO PCM destruction (codec 0x1, 2 ch: the 1026sndon pass could only do ADPCM mono): SFX/Explosions/*
             (DM03A Explosion_Vault_Inside_01, L04 Explosion_Distortion_Debriss_02) and *_Crash (DM03A GetawayCar_Crash).
             Gain is common to both channels (stereo image kept), hard clip per channel, head measured on the mono mix.
             NOT Implosion_Revert (a reverse sweep), NOT loops.
    wood     SFX/Impacts/Wood_Crack, Wood_Break/*, Plastic_Break/* (head -14 .. -4.7 dB; mono ADPCM, in no earlier pass)
  story banks (L00..L11 = the campaign; tier B of 1026sndon never covered them) ALSO get that pass's classes:
    glassimpact, shatter, break, canister + every Impacts/Bullet/* (as SNDON_BULLETS=1 tier B)
  optional (env, default OFF): SNDON_GRENADE=1  Impacts/Grenade/* (a grenade LANDING on soil / wood / metal, 0.3-0.6 s, -8 .. -14 dB)
                               SNDON_LONG=1     long collapse rumbles (F02 Bridge_FallApart_*, Bridge_Collapse_05: 5-26 s, -19 .. -27 dB):
                                                peak-normalised to full scale WITHOUT the hard clip (19.8 % flat tops over 20 s = noise), so
                                                they get a big boost but stay under the MP45 head: a judgement, not parity
NOT possible offline: streamed records (PC_Def.str Vorbis: Retomoto window blast M09_Explosion_Window_Office, head -4.9 dB, peak 0 dBFS,
  already within 1.7 dB of the MP45; nothing is changed); see re/sound_online_1026b.md.

    python kl_sndonline.py audit  [--groups maps,stock,story] [--dd <game folder>]
    python kl_sndonline.py build <outdir> [--groups ...] [--dd <game folder>] [--force]
    python kl_sndonline.py verify <outdir> [--dd <game folder>]
    python kl_sndonline.py selftest                              synthetic checks of the PCM stereo path (no game files needed)
    --dd: a friend's game folder (default: the owner's); --force: accept banks whose md5 is in no pin file (a friend's PC builds
    its own maps). The pass is idempotent: a record already at target is not touched, so a re-run changes nothing.
"""
import json, os, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = HERE
sys.path.insert(0, TOOLS)
DD_GIVEN = '--dd' in sys.argv                            # a friend's folder: their md5s never go into the repo pins file
if DD_GIVEN:                                   # set before kl_gunsnd_all lists banks (B.DD / B.MAPS are read at call time)
    _i = sys.argv.index('--dd'); _dd = sys.argv[_i + 1].replace('\\', '/'); del sys.argv[_i:_i + 2]
    import kl_dmgunsnd_build as _B
    _B.DD = _dd; _B.MAPS = _dd + '/KLExpansion/Maps'
import kl_gunsnd as G
import kl_gunsnd_match as M
import kl_gunsnd_all as A

TAG = '1026sndon2'      # + 'G' / 'L' below when SNDON_GRENADE / SNDON_LONG change the record set (review 8: other content must not share a tag)
WHAT = 'impact sounds pass 2'
FX_GAIN = 24.0
GRENADE = os.environ.get('SNDON_GRENADE') == '1'
LONG = os.environ.get('SNDON_LONG') == '1'
TAG += ('G' if GRENADE else '') + ('L' if LONG else '')
PINS = os.path.join(HERE, 'kl_sndonline2.pins.json')
FXPINS = os.path.join(TOOLS, 'kl_fxsnd.pins.json')   # live banks are the 1025fxraw output ...
SNDON1_PINS = (os.path.join(HERE, 'kl_sndonline.pins_B.json'), 'C:/kl_build_1024/sndonline_1026/kl_sndonline.pins_B.json')   # ... or the 1026sndon output (tier B)
CLS_STORY = (      # the 1026sndon tier B classes, for the story banks it never covered
    ('glassimpact', re.compile(r'(^SFX/Impacts/Bullet/Glass/|^SFX/Impacts/Glass_Crack/)', re.I)),
    ('shatter', re.compile(r'^SFX/Impacts/Shatter/(?!Glass/)', re.I)),
    ('break', re.compile(r'^SFX/Impacts/(Metal_Break|Metal_Crack|Concrete_Break)/', re.I)),
    ('canister', re.compile(r'^SFX/Impacts/Canisters/', re.I)),
    ('bullet', re.compile(r'^SFX/Impacts/Bullet/', re.I)),
)
CLS_ALL = (
    ('wood', re.compile(r'^SFX/Impacts/(Wood_Crack|Wood_Break|Plastic_Break)/', re.I)),
) + ((('grenade', re.compile(r'^SFX/Impacts/Grenade/', re.I)),) if GRENADE else ()) \
  + ((('long', re.compile(r'^SFX/MultiPlayer/F02/Bridge_Breakdown/(Bridge_FallApart_|Bridge_Collapse_0)', re.I)),) if LONG else ())
PCMFX = re.compile(r'(^SFX/Explosions/|_Crash/)', re.I)          # codec 1, 2 ch only; GUESS: "_Crash/" = the vehicle crash folders (M03_GetAwayCar_Crash)
NOT = re.compile(r'(Implosion_Revert|Elevator_Falling|Bomb_WarmUp|Loop(_|\d|\.|$))', re.I)     # Loop anchored (review 4): not 'Loophole'
OLD_FX = re.compile(r'(^SFX/Explosions/|^LevelSetup/All/Explosions/|/Capatulio_Explodes/|^SFX/Impacts/GlassBreak/|^SFX/Impacts/Shatter/Glass/|^SFX/Impacts/Bullet/Glass/Bottles/|^SFX/Environment/Fire/Cannisters/)', re.I)


def mono(x): return x.mean(axis=1) if x.ndim == 2 else x


def fx_class(name, group='maps', codec=0x11, ch=1):
    if M.SEL.search(name) or M.REF.search(name): return None
    if codec == 1:                                    # in-memory PCM: stereo explosions / crashes only
        return 'pcmfx' if ch == 2 and PCMFX.search(name) and not NOT.search(name) else None
    if NOT.search(name) and not (LONG and name.startswith('SFX/MultiPlayer/F02/Bridge_Breakdown/')): return None
    if OLD_FX.search(name): return None
    for c, rx in CLS_ALL + (CLS_STORY if group == 'story' else ()):
        if rx.search(name): return c
    return None


def usable(w):
    fr = w.get('samples') // (w.get('ch') if w.codec == 1 else 1)          # PCM records count samples x channels (kl_gunsnd.encode_for)
    if w.streamed or fr < 2 * int(0.03 * w.get('rate')) + 8: return False  # drive_raw fades the last 30 ms: shorter clips would crash it
    return (w.codec == 0x11 and w.get('ch') == 1) or (w.codec == 1 and w.get('ch') == 2)


def rated(w, fn, *a):
    """kl_gunsnd_match measures at a fixed 32 kHz; destruction records come at 9012..32000 Hz: set its rate per record"""
    old = M.R; M.R = w.get('rate')
    try: return fn(*a)
    finally: M.R = old


def md5(b): return A.md5(b)


def drive_pcm(x2, ref, rf, long=False):
    """stereo float [n,2] -> (stereo float, gain dB). ONE linear gain for both channels (image kept): the gain drive_raw finds for the mono mix,
    applied to both channels with a hard clip each; head re-checked on the mono mix and scaled down if > ref + RAW_OVER; 30 ms fade out.
    long=True: peak-normalise only (no hard clip), see the module doc. GUESS: head / flat of a stereo clip are judged on (L+R)/2."""
    xc = x2 - x2.mean(axis=0, keepdims=True)
    if long:
        pk = np.abs(xc).max() + 1e-9; g = min(FX_GAIN, 20 * np.log10(M.RAW_CEIL / pk))
        y = xc * 10 ** (g / 20)
    else:
        m = xc.mean(axis=1); pk = np.abs(m).max() + 1e-9
        _, g, _, _ = M.drive_raw(m, ref, rf)
        y = np.clip(xc / pk * 10 ** (g / 20), -1.0, 1.0) * M.RAW_CEIL
        h = M.head_db(y.mean(axis=1))
        if h > ref + M.RAW_OVER: y = y * 10 ** ((ref + M.RAW_OVER - h) / 20)
    n = int(0.03 * M.R); y[-n:] *= np.linspace(1, 0, n)[:, None]
    return y, g


def rows_of(b, whd, wav):
    """-> (ref, how, rf, [(w, class, head, flat)], [(w, class, why)] skipped)"""
    ref, how = A.ref_of(whd, wav); rf = A.FALLBACK_FLAT        # ONE flat-top target, as the gun --raw pass (DM Deagle clips measure 0.3 %)
    rows = []; skip = []
    for w in G.waves(whd):
        c = fx_class(w.name, b.group, w.codec, w.get('ch'))
        if not c: continue
        if not usable(w): skip.append((w, c, 'codec %#x ch %d%s' % (w.codec, w.get('ch'), ' streamed' if w.streamed else ''))); continue
        x = mono(G.decode_wave(wav, w))
        rows.append((w, c, rated(w, M.head_db, x), float(np.abs(G.decode_wave(wav, w)).max() * 100) if c == 'long' else rated(w, M.flat_pct, x)))
    return ref, how, rf, rows, skip


def untouched(c, h, fl, t, rf):
    """a record already as loud (and as flat) as the target is NOT touched: nothing is turned down, re-runs change nothing.
    pcmfx: head only (a stereo mix of two hard-clipped channels shows fewer flat tops than each channel). long: fl holds the PEAK in % (no clip target)."""
    if c == 'long': return fl >= 90.0
    if c == 'pcmfx': return h >= t - 0.6          # hard clip + fade of a stereo mix lands up to ~0.5 dB under the target (selftest): wider than A.TOL so a re-run is a no-op
    return h >= t - A.TOL and (fl >= rf - A.FLAT_TOL or h >= t + M.RAW_OVER)


def pinned_gun_state(b, m5):
    for f in (A.PINS, FXPINS) + SNDON1_PINS + (PINS,):    # live = gun pass output, the 1025fxraw output, the 1026sndon output, or this pass's (re-run)
        pins = json.load(open(f)) if os.path.exists(f) else {}
        e = pins.get(b.key)
        if e and (m5 in e['inputs'] or m5 in e['outputs']): return True
    return False


def cmd_audit(a):
    groups = A.split_groups(a); H0 = []; F0 = []; per = {}
    for b in A.banks(groups):
        whd, wav = b.load(); ref, how, rf, rows, skip = rows_of(b, whd, wav)
        if not rows and not skip: continue
        todo = [r for r in rows if not untouched(r[1], r[2], r[3], ref, rf)]
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
        if untouched(c, h, fl, ref, rf): continue
        x = G.decode_wave(wav, w)
        old = (M.R, M.MAXGAIN); M.R = w.get('rate'); M.MAXGAIN = FX_GAIN
        try:
            if c in ('pcmfx', 'long'): y, g = drive_pcm(x, ref, rf, long=(c == 'long'))
            else: y, g, ach, _ = M.drive_raw(x[:, 0], ref, rf); y = y[:, None]
        finally: M.R, M.MAXGAIN = old
        data, ns, pcmb = G.encode_for(w, y, w.get('rate'), rail=True)
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
        w = nws[e['_w']]; d = mono(G.decode_wave(nwav, w)); c = float(np.corrcoef(d, mono(e['_y']))[0, 1]); mins.append(c); assert c > 0.95, (e['record'], c)
        e['after_head'] = round(rated(w, M.head_db, d), 2); e['after_flat'] = round(float(np.abs(G.decode_wave(nwav, w)).max() * 100) if e['kind'] == 'long' else rated(w, M.flat_pct, d), 1); e['rec'] = e.pop('_w'); del e['_y']
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
    pins_out = os.path.join(out, 'kl_sndonline2.pins.json') if (force or DD_GIVEN) else PINS     # review 1: only the owner's default run updates the repo copy
    for m in res:
        e = pins.setdefault(m['key'], dict(inputs=[], outputs=[]))
        if m['live_md5'] not in e['inputs'] and m['live_md5'] not in e['outputs']: e['inputs'].append(m['live_md5'])
        if not m.get('unchanged') and m['output_md5'] not in e['outputs']: e['outputs'].append(m['output_md5'])
    json.dump(pins, open(pins_out, 'w'), indent=1, sort_keys=True)
    if pins_out != PINS: print('pins written to %s (not the repo copy: --force / --dd)' % pins_out)
    with open(os.path.join(out, 'AB_LIST.txt'), 'w') as f:
        f.write('%-12s %-9s %-52s %6s %7s %7s %6s %7s %6s %6s\n' % ('bank', 'class', 'record', 'rate', 'before', 'target', 'gain', 'after', 'flat0', 'flat1'))
        for m in changed:
            for e in m['detail']:
                f.write('%-12s %-9s %-52s %6d %7.2f %7.2f %6.2f %7.2f %6.1f %6.1f\n' % (m['key'], e['kind'], e['record'].split('SFX/')[-1][-52:], e['rate'], e['before_head'],
                        e['target_head'], e['gain_db'], e['after_head'], e['before_flat'], e['after_flat']))
    A.write_installer(out, TAG, WHAT, 'Glass-hit / shatter / metal+concrete break / canister impact sounds' + ' (stereo PCM explosions / crashes, wood, and the story levels 1026sndon never did) at the S&W MP45 loudness, hard clip (on top of 1025fxraw + 1026sndon)')
    ip = os.path.join(out, 'install_gunsnd2.ps1')      # review 7: the shared writer's header is the 10-24 gun pass; replace its first lines
    t = open(ip, newline='').read().split('\r\n')
    t[0] = '# Impact sounds pass 2 (tools/kl_sndonline.py, tag %s, staged 2026-10-26): stereo PCM explosions / crashes, wood / plastic breaks, story banks. ALSO changes Dog Days stock banks (Arcade too).' % TAG
    t[1:6] = ['# Records listed in manifest.json are re-driven to the S&W MP45 loudness; only their data spans inside each .WAV change. UNDO writes Banks\\<group>\\<id>.old back.',
              '# Before the first patch a bank .WAV is copied to <name>.WAV.before-%s (never overwritten). Do NOT prune that file: it is the undo chain (see re/sound_online_1026b.md).' % TAG,
              '# md5-chained: ALL banks must be exactly the build input (or already the output) or nothing is written. Refuses while kl2.exe runs.', '#', '#', '#']
    open(ip, 'w', newline='').write('\r\n'.join(t))
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
                e = names[w.rec_off]; x = mono(G.decode_wave(nv, w)); assert len(x) == w.get('samples') // (w.get('ch') if w.codec == 1 else 1)
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
    if c == 'selftest': return cmd_selftest()
    print(__doc__); return 1


def cmd_selftest():
    """synthetic stereo clip: gain common to both channels, head reaches the target (+0.6 dB at most), image kept, quiet clip gets louder, loud clip untouched"""
    M.R = 32000; M.MAXGAIN = FX_GAIN; rng = np.random.default_rng(7); n = 32000 * 2
    env = np.exp(-np.arange(n) / 4000.0); l = rng.standard_normal(n) * env * 0.12; r = l * 0.5 + rng.standard_normal(n) * env * 0.01
    x = np.stack([l, r], 1); ref, rf = -3.15, A.FALLBACK_FLAT
    h0 = M.head_db(mono(x)); y, g = drive_pcm(x, ref, rf)
    h1 = M.head_db(mono(y)); ratio0 = np.abs(x[:, 1]).mean() / np.abs(x[:, 0]).mean(); ratio1 = np.abs(y[:, 1]).mean() / np.abs(y[:, 0]).mean()
    print('selftest: head %.2f -> %.2f dB (target %.2f), gain %.1f dB, R/L level %.2f -> %.2f' % (h0, h1, ref, g, ratio0, ratio1))
    assert h0 < ref - 6 and ref - 0.5 < h1 <= ref + M.RAW_OVER + 0.05 and np.abs(y).max() <= 1.0 and abs(y[-1]).max() < 1e-3
    assert abs(ratio1 - ratio0) / ratio0 < 0.5, "stereo image moved"
    assert untouched('pcmfx', h1, 0, ref, rf) and not untouched('pcmfx', h0, 0, ref, rf)
    yl, gl = drive_pcm(x, ref, rf, long=True); assert abs(np.abs(yl).max() - 1.0) < 0.01 or gl == FX_GAIN, 'long: peak-normalised'
    assert untouched('long', 0, 100.0, ref, rf) and not untouched('long', 0, 20.0, ref, rf)
    assert fx_class('SFX/Explosions/Vault_Plasters_Inside/Explosion_Vault_Inside_01.wav', 'maps', 1, 2) == 'pcmfx'
    assert fx_class('SFX/Explosions/Implosions/Implosion_Revert.wav', 'maps', 1, 2) is None
    assert fx_class('SFX/Environment/Vehicles/Cars/M03_GetAwayCar_Crash/GetawayCar_Crash.wav', 'maps', 1, 2) == 'pcmfx'
    assert fx_class('SFX/Impacts/Wood_Break/Wood_Break_Big/x.wav', 'maps') == 'wood' and fx_class('SFX/Impacts/Bullet/Concrete/x.wav', 'maps') is None
    assert fx_class('SFX/Impacts/Bullet/Concrete/x.wav', 'story') == 'bullet' and fx_class('SFX/Weapons/x_shot_01.wav', 'story') is None
    print('selftest PASS'); return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
