#!/usr/bin/env python3
"""
kl_dmgunsnd_build.py - Dead Men gun shots into the Dog Days banks of the KLExpansion maps (owner 2026-10-19: "i want
the dead men ones yes"). OFFLINE: reads the game folder, writes ONLY into <out>. Never touches a game file.

    python kl_dmgunsnd_build.py <out dir> [map ids ...]  [--target max|stock|live] [--distant-all]

For every <DD>\\KLExpansion\\Maps\\<id>\\ it writes <out>\\Maps\\<id>\\<Fnn>_Main.WHD + .WAV (the _Main.zip and its .SND are
NOT rewritten, see below), <out>\\preview\\*.wav (old / new pairs, from DM01's bank) and <out>\\report.json.

WHICH RECORD (READ from each map's own .SND, so a repointed bank is followed): for every Dog Days gun that wears a Dead
Men look (KLGuns.ini), the three '<gun>_shot_0N#sound' objects -> wave object (+0x14) -> .WHD record:
    Rifle_AK47   (M4A1 look)         <- Dead Men Assault_Rifle_M4 Shot_M4_01..03          (+ distant, below)
    Rifle_FN_SCAR(SG 552 look)       <- Assault_Rifle_Sig_552 Shot_Sig_552_01..03
    SMG_Type05   (P90 look)          <- Sub_MachineGun_FN_P90 Shot_FN_P90_01..03     (Type05 plays smg_mpi69: READ map_guns.md)
    SMG_MAC_10   (Steyr TMP look)    <- Sub_MachineGun_Steyr_TMP Shot_Steyr_TMP_01..03
    Rifle_Zastavam85 (MP5 look)      <- Sub_MachineGun_HK_MP5 Shot_MP5_01..03     (it plays smg_type79's clips)
    HG_M9Beretta (USP look)          <- Pistol_HK_USP Shot_Usp_01..03             (already these in the DM banks: skipped)
    distant, class-shared in Dog Days: AssualtRiffle <- _Common/DistantShot/M4 Distant_Shot_M4_01 (--distant-all also
    does SubMachineGuns <- MP5 and HandGuns <- USP)
The player set (#shot_player#set) and the NPC set (#shot_npc#set) of a gun hold the same three #sound objects (READ,
rifle_ak47 in F01: both sets point at 0x5af40), so one record change changes both; the group volumes differ (npc 0.35,
player 0.70, re/gun_sounds.md).

HOW (keeps every offset; kl_gunsnd.rebuild): the clip is level-matched (head RMS of the first 250 ms after the onset)
to the louder of (a) the Dog Days clip of that name in the STOCK bank and (b) the clip now in the map (--target stock /
live = only one of them; 'max' because the owner's earlier set raised some records, e.g. the rifle distant layer, and
lowered others), gain -12..+6 dB,
then soft-limited (knee 0.8, ceiling 0.99). It is cut with a cosine fade to the record's CURRENT length in samples,
so the record is rewritten IN PLACE: the .WAV does not grow, the .SND wave seconds (+0x18) stay right, the zip is not
touched (slot order / kl_netcheck: same by construction). A clip shorter than the record is zero-padded to its length (make()), so samples/pcm/size, the .WHD and the .SND seconds stay exactly as live.
32 kHz mono MS IMA 0x11, block 0x400 - the record's own format.
"""
import hashlib, json, os, re, struct, sys, zipfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gunsnd as G
import kl_dmgunsnd as D

DD = r'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
MAPS = DD + '/KLExpansion/Maps'
STOCK = {'F01': DD + '/KL_PortBackup/Scenes/Locations/F01/F01_Main'}   # F01's own slot holds test builds
for _i in range(2, 10): STOCK['F0%d' % _i] = DD + '/Scenes/Locations/F0%d/F0%d_Main' % (_i, _i)

# (Dog Days gun, label, DM name template with %02d)
SHOTS = [
    ('rifle_ak47', 'M4A1 look', 'SFX/Weapons/Assault_Rifle_M4/Shot/Shot_M4_%02d.wav'),
    ('rifle_fn_scar', 'SG 552 look', 'SFX/Weapons/Assault_Rifle_Sig_552/Shot/Shot_Sig_552_%02d.wav'),
    ('smg_mpi69', 'P90 look (SMG_Type05)', 'SFX/Weapons/Sub_MachineGun_FN_P90/Shot/Shot_FN_P90_%02d.wav'),
    ('smg_mac_10', 'Steyr TMP look', 'SFX/Weapons/Sub_MachineGun_Steyr_TMP/Shot/Shot_Steyr_TMP_%02d.wav'),
    ('smg_type79', 'MP5 look (Zastava)', 'SFX/Weapons/Sub_MachineGun_HK_MP5/Shot/Shot_MP5_%02d.wav'),
    ('hg_m9beretta', 'USP look', 'SFX/Weapons/Pistol_HK_USP/Shot/Shot_Usp_%02d.wav'),
]
DISTANT = [('rifle_ak47', 'AssualtRiffle layer (all rifles) <- M4', 'SFX/Weapons/_Common/DistantShot/M4/Distant_Shot_M4_01.wav')]
DISTANT_ALL = [('smg_mac_10', 'SubMachineGuns layer <- MP5', 'SFX/Weapons/_Common/DistantShot/MP5/Distant_Shot_MP5_01.wav'),
               ('hg_m9beretta', 'HandGuns layer <- USP', 'SFX/Weapons/_Common/DistantShot/USP/Distant_Shot_USP_01.wav')]
R = 32000


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 22), b''): h.update(c)
    return h.hexdigest()


def dm_clips():
    bf = [f for b, f in D.banks() if b == D.PREFERRED][0]; out = {}
    want = {t % i for _, _, t in SHOTS for i in (1, 2, 3)} | {n for _, _, n in DISTANT + DISTANT_ALL}
    want = {x.lower() for x in want}
    for nm, o, w in D.records(bf):
        if nm.lower() in want:
            out[nm.lower()] = (nm, w, D.decode(w, D.read_clip(bf, w))[:, 0] / 32768.0)
    assert len(out) == len(want), sorted(want - set(out))
    return out


def onset(x):
    pk = np.abs(x).max(); i = int(np.argmax(np.abs(x) > 0.1 * pk)); return max(0, i - int(0.002 * R))


def head_db(x, ms=250):
    i = onset(x); s = x[i:i + int(ms / 1000 * R)]
    return 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9)


def stats(x):
    return dict(head_db=round(float(head_db(x)), 2), peak_db=round(float(20 * np.log10(np.abs(x).max() + 1e-9)), 2),
                rms_db=round(float(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)), 2), seconds=round(len(x) / R, 3))


def softlimit(y, knee=0.8, ceil=0.99):
    a = np.abs(y); o = np.where(a <= knee, a, knee + (ceil - knee) * np.tanh((a - knee) / (ceil - knee)))
    return np.sign(y) * o


def make(src, cap, target_db):
    """DM clip (float mono 32 kHz) -> (int16-quantised float clip, info). cap = samples the record holds."""
    # bisect the gain so the head RMS AFTER the soft limiter lands on the target (peaky clips need more gain than
    # target - head); boost capped at +9 dB, cut at -12 dB
    lo, hi = -12.0, 9.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if head_db(softlimit(src * 10 ** (mid / 20))) < target_db: lo = mid
        else: hi = mid
    g_db = float(np.clip((lo + hi) / 2, -12, 9)); y = softlimit(src * 10 ** (g_db / 20))
    limited = float((np.abs(src * 10 ** (g_db / 20)) > 0.8).mean())
    cut = len(y) > cap; tail_db = None
    if cut:
        e_all = (y ** 2).sum(); e_cut = (y[cap:] ** 2).sum(); tail_db = round(float(10 * np.log10(e_cut / e_all + 1e-12)), 1)
        y = y[:cap].copy(); fd = min(cap, int(0.08 * R)); y[-fd:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, fd)))
    padded = len(y) < cap
    if padded: y = np.concatenate([y, np.zeros(cap - len(y))])   # keep the record's sample count: .SND seconds stay right
    y = G.to_i16(y[:, None])[:, 0] / 32768.0
    return y, dict(padded=bool(padded), gain_db=round(g_db, 2), pct_samples_in_limiter=round(100 * limited, 2), cut=bool(cut), cut_energy_db=tail_db, **stats(y), target_head_db=round(float(target_db), 2))


def resolve(snd, ws_by_off, gun, part):
    """record offsets of '<gun>_<part>#sound' objects (part 'shot_01' ...) and the objects' names that share them"""
    so = G.snd_sound_objects(snd); wo = G.snd_wave_objects(snd); w2r = {o: r for r, lst in wo.items() for o, _ in lst}
    key = '/%s/%s_%s#sound' % (gun, gun, part); hit = [(n, o) for n, o in so.items() if n.endswith(key)]
    if len(hit) != 1: raise ValueError('%s: %d sound objects' % (key, len(hit)))
    wv, = struct.unpack_from('<I', snd, hit[0][1] + 0x14)
    return w2r[wv]


def snd_of(zp):
    z = zipfile.ZipFile(zp)
    nm = [n for n in z.namelist() if n.upper().endswith('.SND') and not n.upper().endswith('_LS.SND')]
    assert len(nm) == 1, nm
    return z.read(nm[0])


def build_map(mid, dm, out, target, distant, prev=None, log=print):
    folder = os.path.join(MAPS, mid); whdp = [f for f in os.listdir(folder) if re.match(r'F0\d_Main\.WHD$', f)][0]
    slot = whdp[:3]; base = os.path.join(folder, slot + '_Main')
    whd = open(base + '.WHD', 'rb').read(); wav = open(base + '.WAV', 'rb').read(); snd = snd_of(base + '.zip')
    ws = {w.rec_off: w for w in G.waves(whd)}; so = G.snd_sounds(snd); wobj = G.snd_wave_objects(snd)
    sw = open(STOCK[slot] + '.WHD', 'rb').read(); swav = open(STOCK[slot] + '.WAV', 'rb').read()
    stock = {w.name.lower(): w for w in G.waves(sw)}
    jobs = []   # (gun, label, dm name, part, idx)
    for gun, lab, tpl in SHOTS: jobs += [(gun, lab, tpl % i, 'shot_%02d' % i) for i in (1, 2, 3)]
    for gun, lab, nm in DISTANT + (DISTANT_ALL if distant else []): jobs.append((gun, lab, nm, 'distant_shot_01'))
    repl = {}; srcs = {}; rep = []; used = {}
    for gun, lab, dmname, part in jobs:
        ro = resolve(snd, ws, gun, part); w = ws[ro]
        if ro in used: raise ValueError('%s: record %s targeted twice (%s, %s)' % (mid, w.name, used[ro], dmname))
        used[ro] = dmname
        assert w.codec == 0x11 and w.get('rate') == R and w.get('ch') == 1 and not w.streamed, w.name
        _, dw, src = dm[dmname.lower()]
        live = G.decode_wave(wav, w)[:, 0]; st = G.decode_wave(swav, stock[w.name.lower()])[:, 0]
        n = min(len(live), len(src), int(0.5 * R)); a = live[:n] - live[:n].mean(); b = src[:n] - src[:n].mean()
        already = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
        e = dict(gun=gun, look=lab, record=w.name, dm=dmname.split('SFX/Weapons/')[1], live=stats(live), stock=stats(st),
                 dm_src=stats(src), corr_live_vs_dm=round(already, 3),
                 sharers=sorted({x.split('weapons_kl2_final/')[-1].split('/')[0] for o, _ in wobj.get(ro, []) for x in so.get(o, [])}),
                 snd_seconds_ok=all(abs(s - w.seconds) < 0.002 for _, s in wobj.get(ro, [])))
        if already > 0.95 and part != 'x':
            e['action'] = 'skipped: the bank already holds this Dead Men clip'; rep.append(e); continue
        tgt = {'live': head_db(live), 'stock': head_db(st)}.get(target) if target != 'max' else max(head_db(live), head_db(st))
        y, info = make(src, w.get('samples'), tgt)
        data, ns, pcmb = G.encode_for(w, y[:, None], R)
        assert len(data) <= w.get('size'), (w.name, len(data), w.get('size'))      # in place, no WAV growth
        repl[ro] = (data, ns, pcmb, ns / R); srcs[ro] = y; e.update(info); e['action'] = 'replaced in place'; rep.append(e)
        if prev is not None and mid == prev['map']:
            tag = '%s_%s' % (gun, part)
            G.write_wav(os.path.join(prev['dir'], tag + '_old_live.wav'), G.to_i16(live[:, None]), R)
            G.write_wav(os.path.join(prev['dir'], tag + '_old_stock.wav'), G.to_i16(st[:, None]), R)
            G.write_wav(os.path.join(prev['dir'], tag + '_new.wav'), G.to_i16(y[:, None]), R)
    nwhd, nwav, _ = G.rebuild(whd, wav, repl, None, log=lambda *a: None)
    # ---- checks
    chk = {}
    assert len(nwav) == len(wav) and nwav[:8] == wav[:8] and len(nwhd) == len(whd), 'size changed'
    ow, nw = G.waves(whd), G.waves(nwhd); assert [w.name for w in ow] == [w.name for w in nw]
    for a, b in zip(ow, nw):
        if a.rec_off in repl:
            assert set(k for k in G.F if a.get(k) != b.get(k)) <= {'size', 'samples', 'pcm'}, a.name       # offset kept
        else: assert a.f == b.f, a.name
    spans = [(r, r + G.REC) for r in repl]
    assert all(any(a <= i < b for a, b in spans) for i in range(len(whd)) if whd[i] != nwhd[i]), 'WHD outside records'
    olds = sorted((ws[r].get('off'), ws[r].get('off') + ws[r].get('size')) for r in repl)
    diff = np.nonzero(np.frombuffer(wav, np.uint8) != np.frombuffer(nwav, np.uint8))[0]
    starts = np.array([a for a, _ in olds]); ends = np.array([b for _, b in olds])
    k = np.searchsorted(starts, diff, side='right') - 1
    assert (k >= 0).all() and (diff < ends[k]).all(), 'WAV changed outside the replaced spans'
    chk['wav_bytes_changed'] = int(len(diff)); chk['records_replaced'] = len(repl)
    cors = []
    for w in nw:
        if w.rec_off in repl:
            d = G.decode_wave(nwav, w)[:, 0]; s = srcs[w.rec_off]; assert len(d) == w.get('samples') == len(s)
            c = float(np.corrcoef(d, s)[0, 1]); cors.append(c); assert c >= 0.99, (w.name, c)
    chk['min_corr_decoded_vs_source'] = round(min(cors), 5) if cors else None
    a, b, _ = G.rebuild(nwhd, nwav, {}, None, log=lambda *x: None); chk['identity_rebuild'] = (a == nwhd and b == nwav); assert chk['identity_rebuild']
    od = os.path.join(out, 'Maps', mid); os.makedirs(od, exist_ok=True)
    open(os.path.join(od, slot + '_Main.WHD'), 'wb').write(nwhd); open(os.path.join(od, slot + '_Main.WAV'), 'wb').write(nwav)
    man = dict(map=mid, slot=slot, live_md5={'WHD': hashlib.md5(whd).hexdigest(), 'WAV': hashlib.md5(wav).hexdigest()},
               new_md5={'WHD': hashlib.md5(nwhd).hexdigest(), 'WAV': hashlib.md5(nwav).hexdigest()},
               zip_untouched=True, checks=chk, records=rep)
    log('%-8s %s: %d records replaced, %d skipped, WAV bytes changed %d, min corr %s' % (
        mid, slot, len(repl), sum(1 for e in rep if e['action'].startswith('skipped')), chk['wav_bytes_changed'], chk['min_corr_decoded_vs_source']))
    return man


def verify(out, log=print):
    """independent re-read of the written files: every record not in the report's 'replaced' list is byte-identical to
    the live one (WHD fields and WAV spans), every replaced record decodes to its sample count and correlates >= 0.9 (the +9 dB TMP gain runs into the limiter)
    with the Dead Men source (shape only: gain/limiter/cut differ), WAV/WHD sizes equal live, kl_gunsnd selftest runs."""
    rep = json.load(open(os.path.join(out, 'report.json'))); dm = dm_clips(); bad = 0; mins = []
    for m in rep['maps']:
        mid, slot = m['map'], m['slot']; lb = os.path.join(MAPS, mid, slot + '_Main'); nb = os.path.join(out, 'Maps', mid, slot + '_Main')
        lw, lv = open(lb + '.WHD', 'rb').read(), open(lb + '.WAV', 'rb').read(); nw, nv = open(nb + '.WHD', 'rb').read(), open(nb + '.WAV', 'rb').read()
        assert hashlib.md5(lw).hexdigest() == m['live_md5']['WHD'] and hashlib.md5(lv).hexdigest() == m['live_md5']['WAV'], 'live bank changed since the build: ' + mid
        assert hashlib.md5(nw).hexdigest() == m['new_md5']['WHD'] and hashlib.md5(nv).hexdigest() == m['new_md5']['WAV'], mid
        assert len(lw) == len(nw) and len(lv) == len(nv) and lv[:8] == nv[:8], mid
        rn = {e['record'].lower(): e for e in m['records'] if e['action'].startswith('replaced')}
        ol, nl = G.waves(lw), G.waves(nw); same = 0; rpl = 0
        for a, b in zip(ol, nl):
            if a.name.lower() in rn:
                rpl += 1; d = G.decode_wave(nv, b)[:, 0]; assert len(d) == b.get('samples'); _, _, src = dm[('SFX/Weapons/' + rn[a.name.lower()]['dm']).lower()]
                n = min(len(d), len(src)); c = float(np.corrcoef(d[:n], src[:n])[0, 1]); mins.append(c); assert c >= 0.9, (mid, a.name, c)
            else:
                assert a.f == b.f and (a.streamed or lv[a.get('off'):a.get('off') + a.get('size')] == nv[a.get('off'):a.get('off') + a.get('size')]), (mid, a.name); same += 1
        assert rpl == len(rn)
        # outside every record's data span the WAV is identical
        spans = sorted((w.get('off'), w.get('off') + w.get('size')) for w in ol if w.name.lower() in rn)
        diff = np.nonzero(np.frombuffer(lv, np.uint8) != np.frombuffer(nv, np.uint8))[0]
        st = np.array([a for a, _ in spans]); en = np.array([b for _, b in spans]); k = np.searchsorted(st, diff, side='right') - 1
        assert (k >= 0).all() and (diff < en[k]).all(), mid
        log('verify %-8s replaced %2d (decode ok), %d other records identical, WAV bytes changed only inside replaced spans' % (mid, rpl, same))
    log('verify: all %d maps PASS, min correlation to the Dead Men source %.4f' % (len(rep['maps']), min(mins)))
    for m in rep['maps'][:1] + rep['maps'][-1:]:
        nb = os.path.join(out, 'Maps', m['map'], m['slot'] + '_Main'); G.cmd_selftest(nb + '.WHD')


def main(a):
    if a[:1] == ['verify']: return verify(a[1]) or 0
    target = 'max'; distant = '--distant-all' in a
    if '--target' in a: i = a.index('--target'); target = a[i + 1]; del a[i:i + 2]
    a = [x for x in a if x != '--distant-all']
    if not a: print(__doc__); return 1
    out = a[0]; ids = a[1:] or sorted(d for d in os.listdir(MAPS) if os.path.isdir(os.path.join(MAPS, d)))
    os.makedirs(out, exist_ok=True); pdir = os.path.join(out, 'preview'); os.makedirs(pdir, exist_ok=True)
    dm = dm_clips(); res = []
    for mid in ids:
        res.append(build_map(mid, dm, out, target, distant, prev=dict(map='DM01', dir=pdir)))
    json.dump(dict(target=target, distant_all=distant, maps=res), open(os.path.join(out, 'report.json'), 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
