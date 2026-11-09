#!/usr/bin/env python3
"""
kl_menu_sounds_1109_test.py - self-test of tools/kl_menu_sounds_1109.py on SYNTHETIC data (no game file).

Builds in a temp folder
  - a Dog Days-layout global pair Scenes\\kaneandlynch.WHD + .WAV (kl_whd.build 'dd', 17-dword records): five SFX/OSD/* records
    (IMA 32 kHz x2, PCM 22.05 kHz, IMA 44.1 kHz, an in-memory Vorbis one), a weapon record that must stay, a streamed record;
  - a Dead Men-layout front-end pair Scenes\\KaneAndLynch.WHD + .WAV (14-dword records): PCM stereo 44.1 kHz, IMA mono 22.05 kHz,
    PCM mono 32 kHz clicks, a 5 s ambience (LONG), a streamed record; a level pair under Scenes\\Locations\\M01_FA_A; a fake
    Dead Men PC_Def.str ('IOISNDSTREAM') with a PCM click and a long loop,
and checks probe (table, template GUESS pairs, what opened), the sinc resampler, stage in both length modes (proofs, record table,
decoded content, level match, gain, pins, refusals), proofs() against tampering, check, and install.py's variant / overlay
round trips on a scratch game copy (the stock pair is never written). exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py.
"""
import io, json, math, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import kl_whd as W
import kl_gunsnd as G
import kl_menu_sounds_1109 as M

fails = []
NCHECK = [0]


def check(cond, what):
    NCHECK[0] += 1
    print(('  ok   ' if cond else '  FAIL ') + what)
    if not cond:
        fails.append(what)


def tone(frames, freq, rate, amp=12000, ch=1, phase=0.0):
    t = np.arange(frames) / float(rate)
    x = (amp * np.sin(2 * math.pi * freq * t + phase)).astype(np.int16)
    return np.repeat(x[:, None], ch, 1) if ch > 1 else x[:, None]


def name_key(name):
    h = 0
    for b in name.encode('latin1'):
        h = (h * 5 + b) & 0xffffffff
    return h


# ------------------------------------------------------------------ builders
def build_pair(game, entries):
    """entries: [(name, dict of fields without name/off, data bytes or None)] -> (whd, wav). Data 16-aligned behind the .WAV head
    in entry order; the name dword of each record is set to the offset kl_whd.build gives the name (two passes)."""
    F = W.FIELDS[game]
    wav = bytearray(16)
    offs = []
    for _n, _f, data in entries:
        if data is None:
            offs.append(None); continue
        wav += bytes(-len(wav) % 16); offs.append(len(wav)); wav += data
    wav += bytes(-len(wav) % 16)
    struct.pack_into('<4I', wav, 0, 0, len(wav), 3, 4)

    def items(name_offs):
        out = []
        for i, (n, f, data) in enumerate(entries):
            f = dict(f); f['name'] = name_offs[i]
            if data is not None:
                f['off'] = offs[i]
                if game == 'dd':
                    f['offhi'] = 0
            for k in F:
                f.setdefault(k, 0)
            out.append(('name', 0, n.encode('latin1')))
            out.append(('rec', 0, tuple(f[k] for k in F)))
        return out
    # pass 1: any name dword that is not 0 (parse would read 0 as a record head only before the first name); use 1
    whd = W.build(game, items([1] * len(entries)))
    # the names stand at 16-aligned offsets: find them by scanning (names are unique in this fixture)
    name_offs = []
    p = 16
    for n, _f, _d in entries:
        at = whd.index(n.encode('latin1') + b'\0', p)
        name_offs.append(at); p = at + len(n)
    whd = W.build(game, items(name_offs))
    return bytes(whd), bytes(wav)


def ima_entry(name, pcm16, rate, block=0x400):
    data, spb = G.ima_encode(pcm16, block)
    ch = pcm16.shape[1]
    return (name, dict(fmt=0x11, rate=rate, bits=4, pcm=2 * len(pcm16) * ch, size=len(data), ch=ch, samples=len(pcm16), block=block, spb=spb, lip=4), data)


def pcm_entry(name, pcm16, rate):
    ch = pcm16.shape[1]; d = pcm16.astype('<i2').tobytes()
    return (name, dict(fmt=1, rate=rate, bits=16, pcm=len(d), size=len(d), ch=ch, samples=len(pcm16) * ch, block=ch * 2, spb=1, lip=4), d)


class FakeStream(object):
    """A Dead Men-layout stream file of lone clips (kl_launcher_music_test.Fake, PCM only)."""

    def __init__(self):
        self.blocks = []

    def add(self, name, pcm16, rate):
        self.blocks.append((name, pcm16.astype('<i2').tobytes(), pcm16.shape[1], rate, len(pcm16) * pcm16.shape[1]))

    def write(self, path):
        f = io.BytesIO()
        f.write(b'IOISNDSTREAM' + struct.pack('<I', 9) + struct.pack('<Q', 0x46e11c9f))
        f.write(b'\0' * (0x100 - f.tell()))
        recs = []
        for name, audio, ch, rate, samples in self.blocks:
            off = f.tell(); f.write(audio); f.write(b'\0' * ((-f.tell()) % 0x100))
            recs.append((off, name, audio, ch, rate, samples))
        fmts, fmt_at, name_at = [], [], []
        for off, name, audio, ch, rate, samples in recs:
            fmt = struct.pack('<5I', 2, samples, ch, rate, 16) + b'junkjunk' + struct.pack('<I', 2 * ch)
            fmts.append(fmt); fmt_at.append(f.tell()); f.write(fmt)
        for off, name, audio, ch, rate, samples in recs:
            name_at.append(f.tell()); f.write(name.encode('latin1') + b'\0')
        f.write(b'\0' * ((-f.tell()) % 4))
        index = f.tell()
        rows = []
        for i, (off, name, audio, ch, rate, samples) in enumerate(recs):
            key = name_key(name)
            rows.append((key, struct.pack('<4Q2I4Q', i, off, len(audio), fmt_at[i], len(fmts[i]), key, len(name), name_at[i], 0, 0)))
        rows.sort(key=lambda r: r[0])
        for _, r in rows:
            f.write(r)
        data = f.getvalue()
        data = data[:0x18] + struct.pack('<IIIIIH', index, len(recs), 0x100, 0, 1, 0x38) + data[0x18 + 22:]
        open(path, 'wb').write(data)
        return {off: name for off, name, *_ in recs}


def make_games(root):
    dd, dm = os.path.join(root, 'DD'), os.path.join(root, 'DM')
    os.makedirs(os.path.join(dd, 'Scenes')); os.makedirs(os.path.join(dm, 'Scenes', 'Locations', 'M01_FA_A'))
    # Dog Days global pair
    dd_entries = [
        ima_entry('SFX/OSD/Up_Down.wav', tone(5507, 2000, 32000, 20000), 32000),          # 3 blocks, like the dump
        ima_entry('SFX/OSD/Menu.wav', tone(9000, 1200, 32000, 15000), 32000),
        pcm_entry('SFX/OSD/Error.wav', tone(4410, 440, 22050, 10000), 22050),
        ima_entry('SFX/OSD/Back.wav', tone(8820, 900, 44100, 18000), 44100),
        ('SFX/OSD/Ogg.wav', dict(fmt=0x1000, rate=32000, bits=0, pcm=4000, size=64, ch=1, samples=2000, block=0, spb=0, lip=4), b'OggS' + bytes(60)),
        ima_entry('SFX/Weapons_KL2_Final/Pistol/Pistol_Shot_01.wav', tone(12000, 300, 44100, 30000), 44100),
        ('Music/Menu/Loop.wav', dict(fmt=0x00801000, rate=32000, bits=0, pcm=0, size=0x3000, ch=2, samples=100000, off=0x12300, block=0, spb=0, lip=0, x3c=0, x40=0x10), None),
    ]
    whd, wav = build_pair('dd', dd_entries)
    open(os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'), 'wb').write(whd)
    open(os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'), 'wb').write(wav)
    # Dead Men stream
    fs = FakeStream()
    scroll = tone(8000, 2500, 32000, 9000)                                                 # 250 ms, longer than Up_Down's 172 ms
    fs.add('SFX/UserInterface/Streamed_Scroll.wav', scroll, 32000)
    fs.add('SFX/UserInterface/MenuLoop_01.wav', tone(32000 * 4, 220, 32000, 8000, ch=2), 32000)
    offs = fs.write(os.path.join(dm, 'PC_Def.str'))
    scroll_off = [o for o, n in offs.items() if 'Scroll' in n][0]
    # Dead Men front-end pair (GUESS name KaneAndLynch) + a level pair
    click = tone(6000, 1500, 44100, 20000, ch=2)                                           # 136 ms stereo
    click[:, 1] = tone(6000, 1500, 44100, 10000)[:, 0]                                     # unequal channels: the mean is tested
    back = tone(5000, 700, 22050, 16000)
    err = tone(6400, 350, 32000, 12000)
    dm_entries = [
        pcm_entry('SFX/UserInterface/Menu_Click.wav', click, 44100),
        ima_entry('SFX/UserInterface/Menu_Back.wav', back, 22050),
        pcm_entry('SFX/UserInterface/Menu_Error.wav', err, 32000),
        pcm_entry('SFX/Ambiences/Menu_Room_Long.wav', tone(32000 * 5, 100, 32000, 3000), 32000),
        ('SFX/UserInterface/Streamed_Scroll.wav', dict(fmt=0x00800001, rate=32000, bits=16, pcm=16000, size=16000, ch=1, samples=8000, off=scroll_off, block=2, spb=1, lip=0), None),
    ]
    whd, wav = build_pair('dm', dm_entries)
    open(os.path.join(dm, 'Scenes', 'KaneAndLynch.WHD'), 'wb').write(whd)
    open(os.path.join(dm, 'Scenes', 'KaneAndLynch.WAV'), 'wb').write(wav)
    whd, wav = build_pair('dm', [pcm_entry('SFX/UserInterface/Level_Only_Click.wav', tone(3000, 1000, 32000, 9000), 32000),
                                 ima_entry('SFX/Weapons/Rifle_Shot_01.wav', tone(20000, 200, 44100, 25000), 44100)])
    open(os.path.join(dm, 'Scenes', 'Locations', 'M01_FA_A', 'M01_FA_A_Main.WHD'), 'wb').write(whd)
    open(os.path.join(dm, 'Scenes', 'Locations', 'M01_FA_A', 'M01_FA_A_Main.WAV'), 'wb').write(wav)
    open(os.path.join(dm, 'Scenes', 'Locations', 'M01_FA_A', 'M01_FA_A_Main_LS.WHD'), 'wb').write(b'junk')   # must be skipped
    return dd, dm, dict(scroll=scroll, click=click, back=back, err=err)


# ------------------------------------------------------------------ tests
def test_fixture(dd, dm):
    print('fixture')
    b = M.Bank('dd', os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'))
    check(len(b.records) == 7 and [r.name for r in b.records][0] == 'SFX/OSD/Up_Down.wav', 'dd pair parses: 7 records, names resolved')
    check(all(16 <= r.data_off and r.data_off + r.f['size'] <= len(b.wav) for r in b.records if not r.streamed), 'dd in-memory data inside the .WAV')
    r = b.find('SFX/OSD/Up_Down.wav')
    check(r is not None and r.codec == M.ADPCM and r.f['size'] == 0xc00 and r.frames() == 5507 and abs(r.ms() - 172.1) < 0.2, 'Up_Down: ima, 3 blocks, 5507 frames, 172 ms (as the dump)')
    check(b.find('sfx\\osd\\menu') is b.find('SFX/OSD/Menu.wav') and b.find('Error.wav') is b.find('SFX/OSD/Error.wav'), 'find: case / slash / bare name')
    a, rate = M.decode_record(b, r)
    check(a.shape == (5507, 1) and rate == 32000 and abs(int(np.abs(a.astype(np.int32)).max()) - 20000) < 1200, 'decode_record ima: shape, rate, peak ~20000 (IMA overshoot allowed)')
    e = b.find('SFX/OSD/Error.wav'); a, rate = M.decode_record(b, e)
    check(a.shape == (4410, 1) and rate == 22050 and abs(int(np.abs(a.astype(np.int32)).max()) - 10000) < 5, 'decode_record pcm: exact')
    dmb = M.Bank('dm', os.path.join(dm, 'Scenes', 'KaneAndLynch.WHD'))
    check(len(dmb.records) == 5 and dmb.find('Menu_Click.wav').f['ch'] == 2 and dmb.find('Streamed_Scroll').streamed, 'dm pair parses (14-dword records), streamed flag')
    paths = M.dm_whd_paths(dm)
    check(len(paths) == 2 and paths[0].endswith('KaneAndLynch.WHD') and paths[1].endswith('M01_FA_A_Main.WHD'), 'dm_whd_paths: front-end first, level second, _LS skipped: %s' % [os.path.basename(p) for p in paths])
    check(M.dm_whd_paths(dm, levels=False) == paths[:1], 'dm_whd_paths --no-levels')
    check(M.variant_names('x/kaneandlynch.WHD', 'x/kaneandlynch.WAV') == ('kaneandlynch_deadmen.WHD', 'kaneandlynch_deadmen.WAV'), 'variant names')


def test_resample():
    print('resample')
    rate_in, rate_out = 44100, 32000
    n = 8820
    t = np.arange(n) / rate_in
    x = np.sin(2 * math.pi * 1000 * t)[:, None]
    y = M.resample_sinc(x, rate_in, rate_out)
    check(len(y) == round(n * rate_out / rate_in), 'sinc: output length %d' % len(y))
    ty = np.arange(len(y)) / rate_out
    ideal = np.sin(2 * math.pi * 1000 * ty)
    m = slice(200, len(y) - 200)
    err = np.sqrt(np.mean((y[m, 0] - ideal[m]) ** 2))
    check(err < 0.003, 'sinc: 1 kHz 44.1 -> 32 kHz rms error %.5f (< 0.003)' % err)
    hi = np.sin(2 * math.pi * 19000 * t)[:, None]                                      # above the new Nyquist 16 kHz: must go
    yh = M.resample_sinc(hi, rate_in, rate_out)
    att = 20 * math.log10(max(1e-9, np.sqrt(np.mean(yh[m, 0] ** 2))) / np.sqrt(0.5))
    check(att < -40, 'sinc: 19 kHz alias band at %.1f dB (< -40)' % att)
    yl = G.resample(hi, rate_in, rate_out)
    att_l = 20 * math.log10(np.sqrt(np.mean(yl[m, 0] ** 2)) / np.sqrt(0.5))
    check(att_l > -12, 'linear (kl_gunsnd.resample) keeps the alias at %.1f dB: the sinc is the better default' % att_l)
    up = M.resample_sinc(x[:4410], 44100, 48000)
    tu = np.arange(len(up)) / 48000.0
    err_u = np.sqrt(np.mean((up[100:-100, 0] - np.sin(2 * math.pi * 1000 * tu[100:-100])) ** 2))
    check(len(up) == 4800 and err_u < 0.003, 'sinc: upsample 44.1 -> 48 kHz length 4800, rms error %.5f' % err_u)
    check(M.resample_sinc(x, 32000, 32000) is x and len(M.resample_sinc(np.zeros((0, 1)), 1, 2)) == 0, 'sinc: identity on equal rates / empty')
    st = np.concatenate([x, 0.5 * x], 1)
    ys = M.resample_sinc(st, rate_in, rate_out)
    check(ys.shape[1] == 2 and abs(ys[m, 1].std() / ys[m, 0].std() - 0.5) < 0.01, 'sinc: channels kept apart')
    mono = M.to_channels(st, 1)
    check(abs(mono[:, 0] - 0.75 * x[:, 0]).max() < 1e-12 and M.to_channels(x, 2).shape == (n, 2), 'to_channels: mean / copy')


def test_probe(dd, dm, out):
    print('probe')
    rep, mapping = M.probe(dd, dm, out, log=lambda *a: None)
    names = [d['name'] for d in rep['dd_osd']]
    check(names == ['SFX/OSD/Up_Down.wav', 'SFX/OSD/Menu.wav', 'SFX/OSD/Error.wav', 'SFX/OSD/Back.wav', 'SFX/OSD/Ogg.wav'], 'probe: the 5 OSD records in file order')
    ud = rep['dd_osd'][0]
    check(ud['codec'] == 'ima' and ud['rate'] == 32000 and ud['ch'] == 1 and ud['frames'] == 5507 and ud['size'] == 0xc00, 'probe: Up_Down fields')
    check(len(rep['dm_opened']) == 3 and not rep['dm_failed'], 'probe: opened 2 Dead Men banks + the stream, 0 failed: %s' % [x.split(' (')[0][-24:] for x in rep['dm_opened']])
    dmn = {d['name']: d for d in rep['dm_clips']}
    check({'SFX/UserInterface/Menu_Click.wav', 'SFX/UserInterface/Menu_Back.wav', 'SFX/UserInterface/Menu_Error.wav',
           'SFX/UserInterface/Streamed_Scroll.wav', 'SFX/UserInterface/Level_Only_Click.wav', 'SFX/UserInterface/MenuLoop_01.wav',
           'SFX/Ambiences/Menu_Room_Long.wav'} <= set(dmn), 'probe: UI-looking Dead Men clips listed (banks, level bank, stream)')
    check('SFX/Weapons/Rifle_Shot_01.wav' not in dmn, 'probe: a weapon clip is not listed')
    check(not dmn['SFX/Ambiences/Menu_Room_Long.wav']['short'] and not dmn['SFX/UserInterface/MenuLoop_01.wav']['short'] and dmn['SFX/UserInterface/Menu_Click.wav']['short'],
          'probe: LONG flagged on the 5 s and 4 s clips')
    check(dmn['SFX/UserInterface/Menu_Click.wav']['ch'] == 2 and dmn['SFX/UserInterface/Menu_Click.wav']['rate'] == 44100 and abs(dmn['SFX/UserInterface/Menu_Click.wav']['ms'] - 136.1) < 0.2,
          'probe: Dead Men click rate / channels / ms')
    sc = [d for d in rep['dm_clips'] if d['name'].endswith('Streamed_Scroll.wav')]
    check(len(sc) == 2 and {d['source'].split()[0] for d in sc} == {'bank', 'stream'}, 'probe: the streamed name appears as a bank record and as a stream clip')
    check(mapping['SFX/OSD/Menu.wav'] == 'SFX/UserInterface/Menu_Click.wav' and mapping['SFX/OSD/Back.wav'] == 'SFX/UserInterface/Menu_Back.wav'
          and mapping['SFX/OSD/Error.wav'] == 'SFX/UserInterface/Menu_Error.wav', 'template: Menu / Back / Error GUESS pairs by name')
    check(mapping['SFX/OSD/Up_Down.wav'] == 'SFX/UserInterface/Streamed_Scroll.wav', 'template: Up_Down -> a "scroll" clip (SYN table)')
    check(all(c[0] != 'SFX/Ambiences/Menu_Room_Long.wav' for c in mapping['_candidates']['SFX/OSD/Menu.wav']), 'template: long clips are no candidate')
    cs = [c[0] for c in mapping['_candidates']['SFX/OSD/Up_Down.wav']]
    check(len(cs) == len(set(cs)), 'template: candidates unique (bank + stream copies of one name folded)')
    check(all(os.path.isfile(os.path.join(out, f)) for f in ('probe.json', 'probe.txt', 'mapping.json')), 'probe: probe.json, probe.txt, mapping.json written')
    txt = open(os.path.join(out, 'probe.txt')).read()
    check('SFX/OSD/Up_Down.wav' in txt and 'Menu_Click.wav' in txt and 'LONG' in txt and 'opened 3' in txt, 'probe.txt readable table')
    rep2, _ = M.probe(dd, None, out, log=lambda *a: None)
    check('dm_clips' not in rep2 and os.path.isfile(os.path.join(out, 'mapping.template.json')), 'probe without --dm: DD only, template beside the existing mapping.json')
    json.dump({'SFX/OSD/Up_Down.wav': 'SFX/UserInterface/Streamed_Scroll.wav',
               'SFX/OSD/Menu.wav': 'SFX/UserInterface/Menu_Click.wav',
               'SFX/OSD/Error.wav': {'clip': 'SFX/UserInterface/Menu_Error.wav', 'gain_db': -6.0, 'level': 'none'},
               'SFX/OSD/Back.wav': 'Menu_Back',
               'SFX/OSD/Ogg.wav': None, '_note': 'edited'}, open(os.path.join(out, 'mapping.json'), 'w'))
    return json.load(open(os.path.join(out, 'mapping.json')))


def test_stage(dd, dm, out, mapping, sig):
    print('stage (grow)')
    quiet = lambda *a: None
    try:
        M.stage(dd, dm, mapping, out, accept=False, log=quiet)
        check(False, 'stage without pins refuses')
    except M.Refused as e:
        check('accept-input' in str(e), 'stage without pins refuses: %s' % str(e)[:60])
    rep = M.stage(dd, dm, mapping, out, accept=True, previews=True, log=quiet)
    check(rep['proofs'] == 'PASS' and len(rep['pairs']) == 4 and os.path.isfile(os.path.join(out, 'pins.json')), 'stage: 4 pairs, proofs PASS, pins.json')
    whd0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'), 'rb').read(); wav0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'), 'rb').read()
    whd1 = open(os.path.join(out, 'kaneandlynch_deadmen.WHD'), 'rb').read(); wav1 = open(os.path.join(out, 'kaneandlynch_deadmen.WAV'), 'rb').read()
    check(len(whd1) == len(whd0) and whd1 != whd0, 'stage: .WHD same length, fields changed')
    b0, b1 = M.Bank('dd', os.path.join(dd, 'Scenes', 'kaneandlynch.WHD')), M.Bank('dd', os.path.join(out, 'kaneandlynch_deadmen.WHD'))
    check([(r.name, r.rec_off) for r in b0.records] == [(r.name, r.rec_off) for r in b1.records], 'stage: every record name + offset unchanged')
    for nm in ('SFX/Weapons_KL2_Final/Pistol/Pistol_Shot_01.wav', 'Music/Menu/Loop.wav', 'SFX/OSD/Ogg.wav'):
        r0, r1 = b0.find(nm), b1.find(nm)
        same = r0.f == r1.f and (r0.streamed or b0.data(r0) == b1.data(r1))
        check(same, 'stage: non-mapped %s fields + data identical' % nm.rsplit('/', 1)[-1])
    rows = {r['dd']: r for r in rep['pairs']}
    ud = rows['SFX/OSD/Up_Down.wav']
    check(ud['how'].startswith('appended') and ud['new_samples'] == 8000 and ud['dm_source'].startswith('stream'), 'Up_Down: 250 ms stream clip appended (longer than the 172 ms record): %s' % ud['how'])
    check(len(wav1) > len(wav0) and struct.unpack_from('<I', wav1, 4)[0] == len(wav1), 'stage: .WAV grew, size field right')
    r1 = b1.find('SFX/OSD/Up_Down.wav'); a1, rate1 = M.decode_record(b1, r1)
    ref = sig['scroll'][:, 0].astype(np.float64)
    ref = ref / np.abs(ref).max() * 20000                                                   # peak matched to the stock record's peak ~20000
    err = np.sqrt(np.mean((a1[:, 0].astype(np.float64) - ref[:len(a1)]) ** 2)) / 20000
    check(a1.shape == (8000, 1) and rate1 == 32000 and err < 0.08, 'Up_Down decoded: 8000 frames, 32 kHz, rms error vs the peak-matched source %.3f (IMA re-encode)' % err)
    check(abs(int(np.abs(a1.astype(np.int32)).max()) - int(np.abs(M.decode_record(b0, b0.find('SFX/OSD/Up_Down.wav'))[0].astype(np.int32)).max())) < 1500, 'Up_Down: peak matched to the stock record (GUESS rule, IMA tolerance)')
    me = rows['SFX/OSD/Menu.wav']
    check(me['how'] == 'in place' and me['dm_ch'] == 2 and me['dm_rate'] == 44100 and any('44100 -> 32000' in n for n in me['notes']) and any('channels 2 -> 1' in n for n in me['notes']),
          'Menu: stereo 44.1 kHz click -> mono 32 kHz in place')
    r1 = b1.find('SFX/OSD/Menu.wav'); a1, _ = M.decode_record(b1, r1)
    want = round(6000 * 32000 / 44100)
    check(len(a1) == want and r1.f['size'] == 0xc00 and r1.f['off'] == b0.find('SFX/OSD/Menu.wav').f['off'], 'Menu: %d frames (3 blocks), same data offset, size shrank from 5 blocks' % want)
    ty = np.arange(want) / 32000.0
    ideal = np.sin(2 * math.pi * 1500 * ty); ideal = ideal / np.abs(ideal).max()
    a = a1[:, 0].astype(np.float64); a = a / np.abs(a).max()
    c = np.corrcoef(a[50:-50], ideal[50:-50])[0, 1]
    check(c > 0.98, 'Menu decoded is the 1.5 kHz tone resampled (corr %.3f)' % c)
    er = rows['SFX/OSD/Error.wav']
    r1 = b1.find('SFX/OSD/Error.wav'); a1, rate1 = M.decode_record(b1, r1)
    pk = int(np.abs(a1.astype(np.int32)).max())
    check(er['level'] == 'none' and er['gain_db'] == -6.0 and rate1 == 22050 and abs(pk - 12000 * 10 ** (-6 / 20.0)) < 40 and r1.codec == M.PCM,
          'Error (PCM record): level none, -6 dB -> peak %d (12000 x 0.501), 22050 Hz PCM' % pk)
    check(r1.f['samples'] == len(a1) and r1.f['pcm'] == 2 * len(a1) and r1.f['size'] == r1.f['pcm'], 'Error: PCM fields (samples = frames x ch, pcm = size)')
    bk = rows['SFX/OSD/Back.wav']
    r1 = b1.find('SFX/OSD/Back.wav'); a1, rate1 = M.decode_record(b1, r1)
    check(bk['dm_source'].startswith('bank') and 'ima' in bk['dm_source'] and any('22050 -> 44100' in n for n in bk['notes']) and rate1 == 44100 and len(a1) == 10000,
          'Back: Dead Men IMA 22.05 kHz bank record (bare name) -> 44.1 kHz, 10000 frames')
    check(r1.f['size'] % 0x400 == 0 and r1.f['pcm'] == 2 * r1.f['samples'] and M.ima_blocks_ok(b1.data(r1), 0x400, 1), 'Back: block geometry + heads valid')
    check(os.path.isfile(os.path.join(out, 'install.py')) and len([f for f in os.listdir(out) if f.endswith('.bat')]) == 4 and os.path.isfile(os.path.join(out, 'build_report.json')),
          'stage: install.py, 4 bats, build_report.json')
    pv = os.path.join(out, 'previews')
    check(os.path.isfile(os.path.join(pv, 'Up_Down_stock.wav')) and os.path.isfile(os.path.join(pv, 'Up_Down_deadmen.wav')) and len(os.listdir(pv)) == 8, 'previews: 4 pairs of .wav')
    rep2 = M.stage(dd, dm, mapping, out, accept=False, log=quiet)
    check(rep2['proofs'] == 'PASS', 'stage again with the pins: PASS')
    # refusals
    def refused(mp, why, **kw):
        try:
            M.stage(dd, dm, mp, out, log=quiet, **kw)
            check(False, 'refuses: ' + why)
        except M.Refused as e:
            check(True, 'refuses: %s (%s)' % (why, str(e)[:70]))
    refused({'SFX/OSD/Ogg.wav': 'Menu_Click'}, 'a Vorbis record as target')
    refused({'Music/Menu/Loop.wav': 'Menu_Click'}, 'a streamed record as target')
    refused({'SFX/OSD/Menu.wav': 'SFX/UserInterface/Nothing.wav'}, 'an unknown Dead Men clip')
    refused({'SFX/OSD/Nope.wav': 'Menu_Click'}, 'an unknown Dog Days record')
    refused({'SFX/OSD/Menu.wav': None, '_x': 1}, 'an all-null mapping')
    refused({'SFX/OSD/Menu.wav': 5}, 'a bad mapping value')
    refused({'SFX/OSD/Menu.wav': 'Menu_Click', 'sfx/osd/menu.wav': 'Menu_Back'}, 'the same record twice')
    lv = {'SFX/OSD/Menu.wav': 'Level_Only_Click'}
    r = M.stage(dd, dm, lv, out, log=quiet)
    check(r['pairs'][0]['dm_source'].startswith('bank M01_FA_A_Main.WHD'), 'a clip only in a level bank is found (%s)' % r['pairs'][0]['dm_source'][:34])
    refused(lv, 'a level-only clip with --no-levels', levels=False)
    M.stage(dd, dm, mapping, out, accept=False, log=quiet)       # back to the 4-pair stage for check / install
    return rep


def test_keep(dd, dm, out, mapping):
    print('stage (--keep-length)')
    quiet = lambda *a: None
    out2 = out + '_keep'
    rep = M.stage(dd, dm, mapping, out2, accept=True, keep_length=True, linear=True, rail=True, level='none', log=quiet)
    whd0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'), 'rb').read(); wav0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'), 'rb').read()
    whd1 = open(os.path.join(out2, 'kaneandlynch_deadmen.WHD'), 'rb').read(); wav1 = open(os.path.join(out2, 'kaneandlynch_deadmen.WAV'), 'rb').read()
    check(whd1 == whd0, 'keep: .WHD byte-identical')
    check(len(wav1) == len(wav0), 'keep: .WAV same length')
    rows = {r['dd']: r for r in rep['pairs']}
    check(any('trimmed' in n for n in rows['SFX/OSD/Up_Down.wav']['notes']) and rows['SFX/OSD/Up_Down.wav']['new_samples'] == 5507, 'keep: Up_Down trimmed to 5507 frames with a fade')
    check(any('padded' in n for n in rows['SFX/OSD/Menu.wav']['notes']) and rows['SFX/OSD/Menu.wav']['new_samples'] == 9000, 'keep: Menu padded to 9000 frames')
    check(all('linear' in ' '.join(r['notes']) for r in rep['pairs'] if r['dm_rate'] != r['dd_rate']) and rep['mode']['resample'] == 'linear' and rep['mode']['rail'], 'keep: --linear / --rail recorded')
    b1 = M.Bank('dd', os.path.join(out2, 'kaneandlynch_deadmen.WHD'))
    a1, _ = M.decode_record(b1, b1.find('SFX/OSD/Up_Down.wav'))
    check(len(a1) == 5507 and abs(int(a1[-1, 0])) < 200 and int(np.abs(a1[:4000].astype(np.int32)).max()) > 8000, 'keep: Up_Down ends faded, body present (level none)')
    changed = {int(x, 16) for x in rep['mapped_rec_offs']}
    A = np.frombuffer(wav0, np.uint8); B = np.frombuffer(wav1, np.uint8)
    diff = np.flatnonzero(A != B)
    spans = [(r.data_off, r.data_off + r.f['size']) for r in M.Bank('dd', os.path.join(dd, 'Scenes', 'kaneandlynch.WHD')).records if r.rec_off in changed]
    check(len(diff) > 0 and all(any(a <= d < e for a, e in spans) for d in diff), 'keep: every changed .WAV byte lies in a mapped record\'s span')


def test_proofs(dd, out):
    print('proofs against tampering')
    whd0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'), 'rb').read(); wav0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'), 'rb').read()
    whd1 = open(os.path.join(out, 'kaneandlynch_deadmen.WHD'), 'rb').read(); wav1 = open(os.path.join(out, 'kaneandlynch_deadmen.WAV'), 'rb').read()
    rep = json.load(open(os.path.join(out, 'build_report.json')))
    mapped = {int(x, 16) for x in rep['mapped_rec_offs']}
    bad, n = M.proofs(whd0, wav0, whd1, wav1, mapped, False)
    check(not bad and n['mapped'] == 4 and n['bytes changed outside the mapped spans'] == 0, 'proofs PASS on the stage (%s)' % dict(n))
    bad, _ = M.proofs(whd0, wav0, whd0, wav0, set(), False)
    check(not bad, 'proofs PASS on the stock pair against itself')
    b = M.Bank('dd', os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'))
    pistol = b.find('SFX/Weapons_KL2_Final/Pistol/Pistol_Shot_01.wav')
    t = bytearray(wav1); t[pistol.data_off + 100] ^= 1
    bad, _ = M.proofs(whd0, wav0, whd1, bytes(t), mapped, False)
    check(any('not mapped' in x and 'differs' in x for x in bad) and any('outside the mapped' in x for x in bad), 'tampered non-mapped data: reported')
    t = bytearray(whd1); struct.pack_into('<I', t, pistol.rec_off + 8, 22050)
    bad, _ = M.proofs(whd0, wav0, bytes(t), wav1, mapped, False)
    check(any('not mapped' in x and 'rate' in x for x in bad), 'tampered non-mapped record field: reported')
    ud = b.find('SFX/OSD/Up_Down.wav')
    t = bytearray(whd1); struct.pack_into('<I', t, ud.rec_off + 8, 22050)
    bad, _ = M.proofs(whd0, wav0, bytes(t), wav1, mapped, False)
    check(any('mapped record' in x and 'rate' in x for x in bad), 'mapped record with a changed rate: reported (only pcm/size/samples/off may)')
    t = bytearray(whd1); t[ud.f['name']] ^= 0x20
    bad, _ = M.proofs(whd0, wav0, bytes(t), wav1, mapped, False)
    check(any('name' in x for x in bad), 'changed name byte: reported')
    bad, _ = M.proofs(whd0, wav0, whd1, wav1, mapped, True)
    check(any('keep-length' in x for x in bad), 'grown stage judged as keep-length: reported')
    bad, _ = M.proofs(whd0, wav0, whd1, wav1[:-16], mapped, False)
    check(any('header' in x or 'outside' in x for x in bad), 'truncated .WAV: reported')
    t = bytearray(wav1); r1 = M.Bank('dd', os.path.join(out, 'kaneandlynch_deadmen.WHD')).find('SFX/OSD/Up_Down.wav'); t[r1.data_off + 2] = 90
    bad, _ = M.proofs(whd0, wav0, whd1, bytes(t), mapped, False)
    check(any('IMA block head' in x for x in bad), 'bad step index in a mapped block head: reported')
    check(M.ima_blocks_ok(bytes([0, 0, 88, 0]) + bytes(1020), 0x400, 1) and not M.ima_blocks_ok(bytes([0, 0, 89, 0]) + bytes(1020), 0x400, 1)
          and not M.ima_blocks_ok(bytes([0, 0, 5, 1]) + bytes(1020), 0x400, 1), 'ima_blocks_ok: 88 ok, 89 / reserved byte bad')
    check(M.parse_mapping({'a': 'b', '_n': 1, 'c': None, 'd': {'clip': 'e', 'gain_db': 2}}) == [('a', 'b', 0.0, None), ('d', 'e', 2.0, None)], 'parse_mapping')


def test_check(dd, out):
    print('check')
    quiet = lambda *a: None
    check(M.check(out, dd, log=quiet) == [], 'check PASS on the stage')
    p = os.path.join(out, 'kaneandlynch_deadmen.WAV'); b = bytearray(open(p, 'rb').read()); b[20] ^= 1; open(p, 'wb').write(bytes(b))
    bad = M.check(out, dd, log=quiet)
    check(any('md5' in x for x in bad), 'check: a tampered staged file -> md5 FAIL')
    b[20] ^= 1; open(p, 'wb').write(bytes(b))
    check(M.check(out, dd, log=quiet) == [], 'check PASS again')
    sp = os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'); s = open(sp, 'rb').read(); open(sp, 'wb').write(s[:40] + bytes([s[40] ^ 1]) + s[41:])
    bad = M.check(out, dd, log=quiet)
    check(any('live stock' in x for x in bad), 'check: a changed stock pair -> FAIL')
    open(sp, 'wb').write(s)
    check(M.check(os.path.join(out, 'nowhere'), dd, log=quiet) != [], 'check: no report -> FAIL')


def test_install(dd, out):
    print('install.py (scratch game copy)')
    game = dd + '_scratch'
    shutil.copytree(dd, game)
    inst = os.path.join(out, 'install.py')
    stock = [os.path.join(game, 'Scenes', 'kaneandlynch.WHD'), os.path.join(game, 'Scenes', 'kaneandlynch.WAV')]
    m0 = [M.fmd5(p) for p in stock]
    src = open(inst).read()
    check("r'%s'" % dd in src and 'kaneandlynch_deadmen.WHD' in src and 'KLExpansion' in src, 'install.py names the game, the variants, the overlay')

    def run(*args):
        r = subprocess.run([sys.executable, inst, '--game', game, '--skip-run-check'] + list(args), capture_output=True, text=True, cwd=out)
        return r.returncode, r.stdout + r.stderr
    rc, o = run('--dry')
    check(rc == 0 and 'would write' in o and 'kaneandlynch_deadmen.WHD' in o, 'dry: would write the variants')
    rc, o = run()
    var = [os.path.join(game, 'Scenes', 'kaneandlynch_deadmen.WHD'), os.path.join(game, 'Scenes', 'kaneandlynch_deadmen.WAV')]
    check(rc == 0 and all(os.path.isfile(p) for p in var), 'variant install: siblings written')
    check([M.fmd5(p) for p in stock] == m0, 'stock pair untouched')
    check([M.fmd5(p) for p in var] == [M.fmd5(os.path.join(out, os.path.basename(p))) for p in var], 'siblings = the staged files')
    rc, o = run()
    check(rc == 1 and 'exists already' in o, 'second variant install refused (never overwritten)')
    rc, o = run('--overlay')
    ov = [os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', 'kaneandlynch.WHD'), os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', 'kaneandlynch.WAV')]
    check(rc == 0 and all(os.path.isfile(p) for p in ov) and 'Overlay=1' in o, 'overlay install: KLExpansion\\Overlay\\Scenes\\kaneandlynch.* written, Overlay=1 note')
    check([M.fmd5(p) for p in stock] == m0, 'stock pair still untouched')
    rc, o = run('--undo')
    check(rc == 0 and not any(os.path.exists(p) for p in var) and all(os.path.isfile(p) for p in ov), 'variant undo: siblings removed, overlay copies kept')
    rc, o = run('--undo')
    check(rc == 1 and 'not there' in o, 'variant undo again refused')
    with open(ov[0], 'ab') as f:
        f.write(b'x')
    rc, o = run('--overlay', '--undo')
    check(rc == 1 and 'not the staged md5' in o and os.path.isfile(ov[0]), 'overlay undo refuses a file that is not this stage\'s')
    shutil.copyfile(os.path.join(out, 'kaneandlynch_deadmen.WHD'), ov[0])
    rc, o = run('--overlay', '--undo')
    check(rc == 0 and not any(os.path.exists(p) for p in ov), 'overlay undo: both removed')
    rc, o = run('--overlay-variant')
    check(rc == 1 and 'no overlay copy' in o, 'overlay-variant without an overlay copy: refused (the hook would not look there)')
    rc, o = run('--overlay')
    rc2, o2 = run('--overlay-variant')
    ovv = [os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', 'kaneandlynch_deadmen.WHD'), os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes', 'kaneandlynch_deadmen.WAV')]
    check(rc == 0 and rc2 == 0 and all(os.path.isfile(p) for p in ovv + ov), 'overlay copy + overlay-variant siblings written')
    rc, o = run('--overlay-variant', '--undo'); rc2, o2 = run('--overlay', '--undo')
    check(rc == 0 and rc2 == 0 and not any(os.path.exists(p) for p in ovv + ov), 'both undone')
    with open(stock[1], 'r+b') as f:
        f.seek(40); b = f.read(1); f.seek(40); f.write(bytes([b[0] ^ 1]))
    rc, o = run()
    check(rc == 1 and 'pinned' in o and not os.path.exists(var[0]), 'a changed stock pair: install refused, nothing written')
    r = subprocess.run([sys.executable, inst, '--game', game, '--dry'], capture_output=True, text=True, cwd=out)
    check(r.returncode in (0, 1, 3), 'dry without --skip-run-check runs (tasklist missing here -> treated as running: %d)' % r.returncode)
    check([M.fmd5(p) for p in stock][0] == m0[0], 'stock .WHD untouched throughout')


def main():
    root = tempfile.mkdtemp(prefix='klmenusnd_')
    try:
        dd, dm, sig = make_games(root)
        out = os.path.join(root, 'stage')
        test_fixture(dd, dm)
        test_resample()
        mapping = test_probe(dd, dm, out)
        test_stage(dd, dm, out, mapping, sig)
        test_keep(dd, dm, out, mapping)
        test_proofs(dd, out)
        test_check(dd, out)
        test_install(dd, out)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print('%d checks, %d failed%s' % (NCHECK[0], len(fails), ': ' + '; '.join(fails) if fails else ''))
    print('RESULT: ' + ('PASS' if not fails else 'FAIL'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
