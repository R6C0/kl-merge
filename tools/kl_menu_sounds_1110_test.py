#!/usr/bin/env python3
"""Self-test of tools/kl_menu_sounds_1110.py on SYNTHETIC banks (no game files): stage, proofs (every choice of every event), the table
(a Python mirror of klmenusounds_logic.h), check, refusals (pins, a corrupted stage), the install/undo script in a scratch game folder.
    python tools\\kl_menu_sounds_1110_test.py        -> 'RESULT: PASS'
"""
import hashlib, json, os, shutil, struct, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import kl_whd as W
import kl_menu_sounds_1109 as M
import kl_menu_sounds_1109_test as T
import kl_menu_sounds_1110 as S

fails = []
NCHECK = [0]


def check(cond, what):
    NCHECK[0] += 1
    print(('  ok   ' if cond else '  FAIL ') + what)
    if not cond:
        fails.append(what)


def quiet(*a, **k):
    pass


def make(root):
    dd, dm = os.path.join(root, 'DD'), os.path.join(root, 'DM')
    os.makedirs(os.path.join(dd, 'Scenes')); os.makedirs(os.path.join(dm, 'Scenes'))
    tone = T.tone
    dd_entries = [
        T.ima_entry('SFX/OSD/Up_Down.wav', tone(5507, 2000, 32000, 20000), 32000),
        T.ima_entry('SFX/OSD/Toggle_01.wav', tone(4000, 1500, 32000, 18000), 32000),
        T.pcm_entry('SFX/OSD/Select.wav', tone(4410, 440, 22050, 10000), 22050),
        T.ima_entry('SFX/OSD/Back.wav', tone(8820, 900, 44100, 18000), 44100),
        T.ima_entry('SFX/OSD/Menu.wav', tone(9000, 1200, 22514, 15000), 22514),
        T.ima_entry('SFX/OSD/OpenWindow_04.wav', tone(9000, 800, 24580, 15000), 24580),
        T.pcm_entry('SFX/OSD/Slide.wav', tone(3000, 600, 32000, 9000), 32000),
        T.ima_entry('SFX/Weapons/Pistol_Shot_01.wav', tone(12000, 300, 44100, 30000), 44100),
        ('Music/Menu/Loop.wav', dict(fmt=0x00801000, rate=32000, bits=0, pcm=0, size=0x3000, ch=2, samples=100000, off=0x12300, block=0, spb=0, lip=0, x3c=0, x40=0x10), None),
    ]
    whd, wav = T.build_pair('dd', dd_entries)
    open(os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'), 'wb').write(whd)
    open(os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'), 'wb').write(wav)
    dm_entries = []
    for i, nm in enumerate(['Up_Down', 'Slide', 'Toggle', 'Back', 'Select']):
        dm_entries.append(T.pcm_entry('SFX/UserInterface/%s.wav' % nm, tone(3000 + 300 * i, 700 + 100 * i, 44100, 14000, ch=2), 44100))
    for nm in ('Menu', 'OpenWindow_03', 'OpenWindow_04', 'Options'):
        dm_entries.append(T.pcm_entry('SFX/UserInterface/%s.wav' % nm, tone(32000 * 5, 300, 32000, 9000), 32000))     # 5 s: kept at full length
    whd, wav = T.build_pair('dm', dm_entries)
    open(os.path.join(dm, 'Scenes', 'KaneAndLynch.WHD'), 'wb').write(whd)
    open(os.path.join(dm, 'Scenes', 'KaneAndLynch.WAV'), 'wb').write(wav)
    return dd, dm


def md5f(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    root = tempfile.mkdtemp(prefix='klmenusnd10_')
    try:
        dd, dm = make(root)
        out = os.path.join(root, 'stage')
        print('field offsets / fnv')
        check(S.field_offsets() == [4 * W.DD_F.index(k) for k in ('pcm', 'size', 'samples', 'off', 'offhi')], 'field offsets = 4 * index in kl_whd.DD_F')
        check(S.fnv1a(b'') == 2166136261 and S.fnv1a(b'a') == 0xe40c292c, 'fnv1a known values')
        print('clips')
        lines = []
        seen = S.list_clips(dm, lines.append)
        check(len(seen) == 9, 'clips lists the 9 UserInterface records (%d)' % len(seen))
        print('stage')
        try:
            S.stage(dd, dm, out, accept=False, log=quiet)
            check(False, 'first stage without --accept-input is refused')
        except M.Refused:
            check(True, 'first stage without --accept-input is refused (pins)')
            check(not os.path.exists(os.path.join(out, 'kaneandlynch_deadmen.klms')), 'nothing written on a refusal')
        rep = S.stage(dd, dm, out, accept=True, previews=True, log=quiet)
        whd0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WHD'), 'rb').read()
        wav0 = open(os.path.join(dd, 'Scenes', 'kaneandlynch.WAV'), 'rb').read()
        whd1 = open(os.path.join(out, 'kaneandlynch_deadmen.WHD'), 'rb').read()
        wav1 = open(os.path.join(out, 'kaneandlynch_deadmen.WAV'), 'rb').read()
        tab = open(os.path.join(out, 'kaneandlynch_deadmen.klms')).read()
        check(whd1 == whd0, 'staged .WHD is the stock .WHD byte for byte')
        check(wav1[8:len(wav0)] == wav0[8:] and struct.unpack_from('<I', wav1, 4)[0] == len(wav1) and len(wav1) % 16 == 0 and len(wav1) > len(wav0), '.WAV = stock + appended, 16-aligned, size field = length')
        t = S.parse_table(tab)
        check(len(t['events']) == 7 and [e[0] for e in t['events']] == [e[0] for e in S.EVENTS], 'table has the 7 events in order')
        dflt = {e[0]: e[2] for e in t['events']}
        check(all(dflt[k] == c for k, c in (('Navigate', 'up_down'), ('Confirm', 'select'), ('Back', 'back'), ('Toggle', 'toggle'), ('Slider', 'slide'))) and dflt['Menu'] == 'dd' and dflt['Window'] == 'dd', 'defaults: the dm clip name for the five with a counterpart, dd for Menu / Window')
        check(t['whdlen'] == len(whd0) and t['whdhash'] == S.fnv1a(whd0) and t['wavlen'] == len(wav1), 'table WHD length + hash + WAV length')
        names = {k: [c for (kk, c) in t['choices'] if kk == k.lower()] for k, *_ in S.EVENTS}
        check(all('off' in v and 'up_down' in v for v in names.values()) and 'dm' not in names['Confirm'] and 'dm' not in names['Menu'], 'choices: off + every clip per event, no dm line (hook reserves it; the E default names the clip)')
        check(all(rep['proofs'] == 'PASS' for _ in [0]) and rep['proof_counts']['choices'] == len(t['choices']) + 5, 'stage report: proofs PASS, choice count matches the table')
        print('applying picks')
        fo = S.field_offsets()
        recs = {e[0]: e[1] for e in t['events']}
        for pick in ('select', 'off', 'options'):
            whd = bytearray(whd0)
            S.apply_choice(whd, recs['Confirm'], fo, t['choices'][('confirm', pick)])
            pb, _ = M.proofs(whd0, wav0, bytes(whd), wav1, {recs['Confirm']}, False)
            check(not pb, 'Confirm=%s: proofs vs stock pair clean %s' % (pick, pb[:1]))
        whd = bytearray(whd0)
        S.apply_choice(whd, recs['Menu'], fo, t['choices'][('menu', 'menu')])
        b = M.Bank('dd', os.path.join(out, 'kaneandlynch_deadmen.WHD'), os.path.join(out, 'kaneandlynch_deadmen.WAV'))
        b.whd = bytes(whd); b.items, b.T = W.parse('dd', b.whd)
        f1 = dict(zip(W.DD_F, [v for k, o, v in b.items if k == 'rec' and o == recs['Menu']][0]))
        r1 = M.Rec('dd', 'SFX/OSD/Menu.wav', recs['Menu'], f1, 0)
        a, rate = M.decode_record(b, r1)
        check(rate == 22514 and int(22514 * 4.9) <= len(a) <= int(22514 * 5.0) + 2 and int(np.abs(a).max()) > 1000, 'Menu=menu decodes: stock rate %d, %d frames (full 5 s), audible' % (rate, len(a)))
        whd = bytearray(whd0)
        S.apply_choice(whd, recs['Navigate'], fo, t['choices'][('navigate', 'off')])
        f2 = dict(zip(W.DD_F, [v for k, o, v in W.parse('dd', bytes(whd))[0] if k == 'rec' and o == recs['Navigate']][0]))
        b.whd = bytes(whd); b.items, b.T = W.parse('dd', b.whd)
        a, _ = M.decode_record(b, M.Rec('dd', 'x', recs['Navigate'], f2, 0))
        check(int(np.abs(a).max()) < 50 and len(a) < 2000, 'Navigate=off decodes to ~silence (%d frames)' % len(a))
        check(os.path.isfile(os.path.join(out, 'previews', 'Confirm_dm.wav')) and os.path.isfile(os.path.join(out, 'previews', 'Confirm_stock.wav')), 'previews written')
        print('check')
        check(S.check(out, dd, quiet) == [], 'check: PASS on the fresh stage')
        p = os.path.join(out, 'kaneandlynch_deadmen.WAV')
        data = bytearray(open(p, 'rb').read()); data[len(wav0) + 40] ^= 0x55
        open(p, 'wb').write(bytes(data))
        check(any('md5' in x for x in S.check(out, dd, quiet)), 'check: a flipped appended byte is caught (md5)')
        open(p, 'wb').write(wav1)
        tp = os.path.join(out, 'kaneandlynch_deadmen.klms')
        bad = tab.replace('WHD %d' % len(whd0), 'WHD %d' % (len(whd0) + 1), 1)
        try:
            S.parse_table(bad.replace('KLMS 1', 'KLMS 2'))
            check(False, 'a wrong table version is refused')
        except M.Refused:
            check(True, 'a wrong table version is refused')
        # the proofs themselves must catch a table that points a record at the wrong place
        evs = [(k, o, d, n) for k, o, d, n in t['events']]
        chs = [(k, c, t['choices'][(k.lower(), c.lower())]) for k, c in t['order']]
        chs[0] = (chs[0][0], chs[0][1], (chs[0][2][0], chs[0][2][1], chs[0][2][2], len(wav1) + 64, 0))
        pb, _ = S.prove(whd0, wav0, wav1, evs, chs, tab)
        check(bool(pb), 'prove: a choice pointing outside the .WAV fails (%d problems)' % len(pb))
        evs2 = [(k, o + 4 if k == 'Back' else o, d, n) for k, o, d, n in evs]
        pb, _ = S.prove(whd0, wav0, wav1, evs2, [(k, c, t['choices'][(k.lower(), c.lower())]) for k, c in t['order']], tab)
        check(bool(pb), 'prove: an event at a wrong record offset fails')
        print('install')
        game = os.path.join(root, 'GAME'); shutil.copytree(dd, game)
        scenes = os.path.join(game, 'Scenes')
        run = lambda *a: subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--game', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
        before = {f: md5f(os.path.join(scenes, f)) for f in os.listdir(scenes)}
        r = run('--dry')
        check(r.returncode == 0 and os.listdir(scenes) and sorted(os.listdir(scenes)) == sorted(before), 'install --dry: rc 0, nothing written')
        r = run()
        check(r.returncode == 0 and all(os.path.isfile(os.path.join(scenes, n)) for n, _ in rep['staged']), 'install: three files beside the stock pair (%s)' % r.stdout.strip().splitlines()[-1:])
        check(all(md5f(os.path.join(scenes, f)) == m for f, m in before.items()), 'install: the stock pair is untouched')
        r = run()
        check(r.returncode != 0 and 'already' in r.stdout, 'install twice: refused')
        r = run('--undo')
        check(r.returncode == 0 and sorted(os.listdir(scenes)) == sorted(before), 'undo: back to the stock pair only')
        # an older stage's file: refused without --replace, moved aside with it, undo restores it
        old = os.path.join(scenes, 'kaneandlynch_deadmen.WHD')
        open(old, 'wb').write(b'OLD1109')
        rp = json.load(open(os.path.join(out, 'install.py').replace('install.py', 'build_report.json')))
        src = open(os.path.join(out, 'install.py')).read().replace('PREV = {}', 'PREV = {"kaneandlynch_deadmen.WHD": ["%s"]}' % hashlib.md5(b'OLD1109').hexdigest())
        ip = os.path.join(out, 'install_prev.py'); open(ip, 'w').write(src)
        run2 = lambda *a: subprocess.run([sys.executable, ip, '--game', game, '--skip-run-check'] + list(a), capture_output=True, text=True)
        r = run2()
        check(r.returncode != 0 and open(old, 'rb').read() == b'OLD1109', 'an older stage file without --replace: refused, left alone')
        r = run2('--replace')
        check(r.returncode == 0 and open(old + '.before-menusounds_1110', 'rb').read() == b'OLD1109' and md5f(old) == rp['staged'][0][1], '--replace moved the old file aside and installed')
        r = run2('--undo')
        check(r.returncode == 0 and open(old, 'rb').read() == b'OLD1109' and not os.path.exists(old + '.before-menusounds_1110'), 'undo restored the older stage file')
        os.remove(old)
        # a changed stock pair is refused
        open(os.path.join(scenes, 'kaneandlynch.WAV'), 'ab').write(b'x')
        r = run()
        check(r.returncode != 0 and 'pinned' in r.stdout, 'install: a changed stock pair is refused')
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print('%d checks, %d failed%s' % (NCHECK[0], len(fails), ': ' + '; '.join(fails) if fails else ''))
    print('RESULT: ' + ('PASS' if not fails else 'FAIL'))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
