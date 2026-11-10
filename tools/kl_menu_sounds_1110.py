#!/usr/bin/env python3
r"""
kl_menu_sounds_1110.py - a PER-EVENT menu sound choice (Dog Days / Dead Men / off / any Dead Men UI clip) for the Dead Men menu look
(T9 stage 4b, 2026-11-10). Replaces the baked "all Dead Men" bank of tools/kl_menu_sounds_1109.py, which the owner heard as "no click when you
press into something, and I still hear the Dog Days version" (the Dog Days confirm may not be the record that stage swapped: GUESS).

WHAT IS STAGED (beside the live pair, never over it):
    kaneandlynch_deadmen.WHD   = the STOCK Dog Days .WHD, byte for byte (so with every pick 'dd' the menu is exactly stock);
    kaneandlynch_deadmen.WAV   = the stock .WAV plus, APPENDED (16-aligned, header size updated), one encoded clip per (event, choice) in the
                                 format of the event's own record (IMA ADPCM / PCM, its rate and channels);
    kaneandlynch_deadmen.klms  = the table (klhook\klmenusounds_logic.h): per event the record and per choice the five record dwords
                                 (pcm size samples off offhi) to write.
At game start klslot.c (kls_menulook -> kls_menusounds) reads the table and [MenuSounds] of KLHook.ini, writes the picked dwords into an
in-memory copy of the .WHD and opens THAT (%TEMP%\klms_<hash>.WHD). A pick is dd | dm | off | a clip name; the bank is read at game start,
so a change applies at the NEXT START. Nothing in the .WAV before the appended part changes, so every stock record plays exactly as before.

EVENTS (key = the [MenuSounds] key; record = the Dog Days SFX/OSD record it re-points; dm = its Dead Men counterpart, a choice named 'dm'):
    Navigate  Up_Down      dm = UserInterface/Up_Down        Confirm  Select       dm = Select      Back     Back           dm = Back
    Toggle    Toggle_01    dm = Toggle                       Slider   Slide        dm = Slide
    Menu      Menu         (no dm: stock until a clip is named)        Window   OpenWindow_04   (no dm)
CLIP CHOICES (each event can take each): up_down slide toggle back select menu options openwindow_03 openwindow_04 (Dead Men
SFX/UserInterface/*, Scenes\KaneAndLynch.WHD; a long one is cut to 1.5 s with a 60 ms fade) and 'off' (50 ms of silence). --clip NAME adds
another Dead Men clip (choice name = its file stem, lower case). The streamed Menu_BG_* ambience records and MenuLoop_01 (Vorbis) cannot be
swapped (a streamed record has no data in the .WAV): menu ambience is NOT offered.

    python tools\kl_menu_sounds_1110.py clips  --dm <DM>
        lists the Dead Men SFX/UserInterface/* clips this tool can use (name, codec, rate, channels, ms).
    python tools\kl_menu_sounds_1110.py stage  --dd <DD> --dm <DM> [--out <dir>] [--accept-input] [--clip NAME ...] [--previews] [--prev <1109 stage dir> ...]
        Writes the three files, build_report.json, pins.json (--accept-input on the first run: md5s of the stock pair), install.py + .bat files,
        previews\<event>_{stock,dm}.wav. Refuses (nothing written) unless every proof passes.
    python tools\kl_menu_sounds_1110.py check <stage dir> --dd <DD>
        re-runs the proofs against the live stock pair.

PROOFS: (1) the staged .WHD == the live stock .WHD; (2) the .WAV prefix == the stock .WAV except the header size; the header is {0, size, 3, 4}
with size = length; the appended part is 16-aligned and every choice lies inside the file; (3) for EVERY choice, the .WHD with that choice written
(Python mirror of klms_apply) passes kl_menu_sounds_1109.proofs against the stock pair with that record as the only mapped one (only pcm/size/samples/
off/offhi differ, pcm == 2 * samples (* ch for IMA), size a multiple of the block, every IMA block head valid, no span overlap,
kl_gunsnd.check_bank_preserved) - done in rounds (the k-th choice of every event at once); (4) the table's WHD length + FNV-1a hash match
the staged .WHD; (5) the table's own records are the events' records by name.
GUESS (each also in the code): which record the game plays for a confirm / menu / window sound (the table carries Menu and Window so the owner can try
them); the level match (rms, as 1109); the engine reads the .WHD from the %TEMP% path and does not reopen the bank by another name mid-session.
Never writes the stock pair, a level pair or KL_PortBackup; the stage folder is outside the repo.
"""
import argparse, collections, datetime, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_menu_sounds_1109 as M          # Bank, DMSources, fit_clip, proofs, check_pins, decode_record, write_wav16, Refused, variant_names
import kl_whd as W

np = M.np
Refused = M.Refused

STAGE = 'menusounds_1110'
OUT_DEFAULT = r'C:\kl_build_1024\menulook_1109\sounds1110'
UI_PREFIX = 'SFX/UserInterface/'
MAX_CLIP_MS = 1500.0
OFF_MS = 50.0
# event key, Dog Days record, the Dead Men clip that is its 'dm' counterpart (None = no dm choice; the table default is dd)
EVENTS = [('Navigate', 'SFX/OSD/Up_Down.wav', 'up_down'), ('Confirm', 'SFX/OSD/Select.wav', 'select'), ('Back', 'SFX/OSD/Back.wav', 'back'),
          ('Toggle', 'SFX/OSD/Toggle_01.wav', 'toggle'), ('Slider', 'SFX/OSD/Slide.wav', 'slide'),
          ('Menu', 'SFX/OSD/Menu.wav', None), ('Window', 'SFX/OSD/OpenWindow_04.wav', None)]
# choice name -> Dead Men clip (file name under SFX/UserInterface/)
CLIPS = collections.OrderedDict([('up_down', 'Up_Down'), ('slide', 'Slide'), ('toggle', 'Toggle'), ('back', 'Back'), ('select', 'Select'),
                                 ('menu', 'Menu'), ('options', 'Options'), ('openwindow_03', 'OpenWindow_03'), ('openwindow_04', 'OpenWindow_04')])
RESERVED = ('dd', 'dm', 'off')
FIELDS = ('pcm', 'size', 'samples', 'off', 'offhi')       # the five dwords of a record a choice writes (klms_logic.h KLMS_NF)
FNV0 = 2166136261


def fnv1a(b, h=FNV0):
    for c in b:
        h = ((h ^ c) * 16777619) & 0xffffffff
    return h


def field_offsets():
    """Byte offset of each FIELDS dword inside a record = 4 * its index in kl_whd.DD_F (rec_off is the record's first dword)."""
    return [4 * W.DD_F.index(k) for k in FIELDS]


# ---------------------------------------------------------------- the table (Python mirror of klmenusounds_logic.h)
def table_text(whd_len, whd_hash, wav_len, events, choices):
    """events: [(key, rec_off, default choice name, record name)], choices: [(event key, name, (pcm, size, samples, off, offhi))]."""
    fo = field_offsets()
    L = ['# tools/kl_menu_sounds_1110.py: per-event menu sound choices for klslot.c kls_menusounds (klmenusounds_logic.h). Do not edit by hand.',
         'KLMS 1', 'WHD %d %x' % (whd_len, whd_hash), 'WAV %d' % wav_len,
         'F ' + ' '.join('%s %d' % (k, o) for k, o in zip(FIELDS, fo))]
    for key, rec_off, dflt, recname in events:
        # the hook reserves dd / dm as pick words: the table names the default by its clip and carries no 'dm' C line
        L.append('E %s %x %s %s' % (key, rec_off, ({e[0]: e[2] for e in EVENTS}.get(key) or 'dd') if dflt == 'dm' else dflt, recname))
        for ek, name, v in choices:
            if ek == key and name != 'dm':
                L.append('C %s %s %s' % (key, name, ' '.join(str(x) for x in v)))
    return '\n'.join(L) + '\n'


def parse_table(text):
    """-> dict(whdlen, whdhash, wavlen, fo [5], events [(key, rec, dflt, recname)], choices {(key, name_lower): (5 values)}) or raises Refused."""
    t = dict(whdlen=None, whdhash=None, wavlen=None, fo=None, events=[], choices=collections.OrderedDict(), order=[])
    magic = False
    for ln, raw in enumerate(text.replace('\r', '').split('\n'), 1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        tok = line.split()
        if tok[0] == 'KLMS':
            if tok[1:] != ['1']:
                raise Refused('table line %d: KLMS version %s' % (ln, tok[1:]))
            magic = True
        elif not magic:
            raise Refused('table line %d: no KLMS header' % ln)
        elif tok[0] == 'WHD':
            t['whdlen'], t['whdhash'] = int(tok[1]), int(tok[2], 16)
        elif tok[0] == 'WAV':
            t['wavlen'] = int(tok[1])
        elif tok[0] == 'F':
            got = dict(zip(tok[1::2], (int(x) for x in tok[2::2])))
            if sorted(got) != sorted(FIELDS):
                raise Refused('table line %d: F fields %s' % (ln, sorted(got)))
            t['fo'] = [got[k] for k in FIELDS]
        elif tok[0] == 'E':
            t['events'].append((tok[1], int(tok[2], 16), tok[3], ' '.join(tok[4:])))
        elif tok[0] == 'C':
            key = (tok[1].lower(), tok[2].lower())
            if key in t['choices']:
                raise Refused('table line %d: choice %s twice' % (ln, tok[1:3]))
            if tok[2].lower() in ('dd', 'dm') and tok[2].lower() == 'dd':
                raise Refused('table line %d: dd is reserved' % ln)
            t['choices'][key] = tuple(int(x) for x in tok[3:3 + len(FIELDS)])
            t['order'].append((tok[1], tok[2]))
        else:
            raise Refused('table line %d: unknown line %r' % (ln, tok[0]))
    if None in (t['whdlen'], t['whdhash'], t['wavlen'], t['fo']) or not t['events']:
        raise Refused('table: a header line is missing')
    return t


def apply_choice(whd, rec_off, fo, vals):
    """Python mirror of klms_apply for one record: writes the five dwords (whd is a bytearray)."""
    for o, v in zip(fo, vals):
        struct.pack_into('<I', whd, rec_off + o, v)


# ---------------------------------------------------------------- build
def silence_for(r):
    return np.zeros((max(1, int(r.f['rate'] * OFF_MS / 1000.0)), max(1, r.f['ch'])), dtype=np.int16)


def clip_name(path_or_name):
    return os.path.splitext(path_or_name.replace('\\', '/').rsplit('/', 1)[-1])[0].lower()


def build(bank, src, clips, log=print):
    """-> (wav1 bytes, events [(key, rec_off, default, recname)], choices [(key, name, 5 values)], rows [report dicts], alias {key: clip name})."""
    wav = bytearray(bank.wav)
    events, choices, rows = [], [], []
    decoded = {}
    for cname, dm_name in clips.items():
        hit = src.find(dm_name)
        if hit is None:
            log('  clip %-14s %s: not found in the Dead Men banks - skipped' % (cname, dm_name))
            continue
        a, rate, desc = src.decode(hit)
        if len(a) == 0:
            log('  clip %-14s decodes to nothing - skipped' % cname)
            continue
        decoded[cname] = (a, rate, desc, dm_name)
    if not decoded:
        raise Refused('none of the Dead Men clips could be decoded (%d banks opened, %d failed)' % (len(src.opened), len(src.failed)))
    for key, recname, dm_clip in EVENTS:
        r = bank.find(recname)
        if r is None:
            raise Refused('event %s: %s is no record of %s' % (key, recname, bank.whd_path))
        M.swappable(r)
        stock, _ = M.decode_record(bank, r)
        peak = int(np.abs(stock.astype(np.int32)).max()) if len(stock) else 0
        rms = float(np.sqrt(np.mean(stock.astype(np.float64) ** 2))) if len(stock) else 0.0
        have_dm = dm_clip in decoded
        events.append((key, r.rec_off, 'dm' if have_dm else 'dd', recname))
        blobs = collections.OrderedDict()
        todo = [(cn, decoded[cn][0], decoded[cn][1], 'rms') for cn in decoded] + [('off', silence_for(r), r.f['rate'], 'none')]
        for cn, a, rate, lv in todo:
            data, samples, pcm, seconds, notes = M.fit_clip(a, rate, r, peak, False, False, lv, 0.0, False, rms, cn != 'off', MAX_CLIP_MS)
            wav += bytes(-len(wav) % 16)
            off = len(wav)
            wav += data
            vals = (pcm, len(data), samples, off, 0)
            choices.append((key, cn, vals))
            blobs[cn] = vals
            rows.append(collections.OrderedDict([('event', key), ('choice', cn), ('record', recname), ('rec_off', '%#x' % r.rec_off), ('ms', round(1000.0 * seconds, 1)),
                                                 ('size', len(data)), ('samples', samples), ('off', '%#x' % off), ('notes', notes)]))
        if have_dm:
            choices.append((key, 'dm', blobs[dm_clip]))                                     # the alias shares the clip's data
            rows.append(collections.OrderedDict([('event', key), ('choice', 'dm'), ('record', recname), ('alias_of', dm_clip)]))
        log('  %-9s %-24s stock %6.0f ms, %2d choices%s' % (key, recname, r.ms(), len(blobs) + int(have_dm), ' (dm = %s)' % dm_clip if have_dm else ' (no dm counterpart: stock until a clip is named)'))
    wav += bytes(-len(wav) % 16)
    struct.pack_into('<I', wav, 4, len(wav))
    return bytes(wav), events, choices, rows


def prove(whd0, wav0, wav1, events, choices, table, log=print):
    """-> (problems, counts). See the module doc, PROOFS 2 to 5 (1 is made by the caller: the staged .WHD is the stock one)."""
    bad, n = [], collections.OrderedDict()
    fo = field_offsets()
    if len(wav1) < len(wav0) or wav1[:4] != wav0[:4] or wav1[8:len(wav0)] != wav0[8:] or struct.unpack_from('<I', wav1, 4)[0] != len(wav1):
        bad.append('.WAV: the stock part is not kept / the header size is not the length')
    if len(wav1) % 16:
        bad.append('.WAV length %d is not 16-aligned' % len(wav1))
    n['wav bytes'] = len(wav1); n['wav grew by'] = len(wav1) - len(wav0)
    t = parse_table(table)
    if t['whdlen'] != len(whd0) or t['whdhash'] != fnv1a(whd0) or t['wavlen'] != len(wav1):
        bad.append('table WHD/WAV length or hash does not match the staged files')
    if t['fo'] != fo:
        bad.append('table F offsets %s != kl_whd.DD_F %s' % (t['fo'], fo))
    recs = {o: dict(zip(W.DD_F, v)) for k, o, v in W.parse('dd', whd0)[0] if k == 'rec'}
    names = {}
    items = W.parse('dd', whd0)[0]
    nm = {o: v.decode('latin1') for k, o, v in items if k == 'name'}
    for key, rec_off, dflt, recname in events:
        f = recs.get(rec_off)
        if f is None or nm.get(f['name'], '?') != recname:
            bad.append('event %s: %#x is not the record %s' % (key, rec_off, recname))
        names[key] = rec_off
    per = collections.OrderedDict()
    for key, name, v in choices:
        per.setdefault(key, []).append((name, v))
        if not (16 <= v[3] and v[3] + v[1] <= len(wav1)) or v[4] != 0:
            bad.append('%s/%s: data %#x+%#x outside the .WAV' % (key, name, v[3], v[1]))
        if v[3] % 16 and name != 'dm':
            bad.append('%s/%s: data offset %#x not 16-aligned' % (key, name, v[3]))
        if name == 'dm':
            continue                                            # 'dm' is not a table line: the E line's default names its clip
        if (key.lower(), name.lower()) not in t['choices'] or t['choices'][(key.lower(), name.lower())] != tuple(v):
            bad.append('%s/%s: not in the table or different' % (key, name))
    rounds = max(len(v) for v in per.values())
    n['choices'] = len(choices); n['rounds'] = rounds
    for k in range(rounds):
        whd = bytearray(whd0)
        mapped = set()
        for key, lst in per.items():
            if k < len(lst):
                apply_choice(whd, names[key], fo, lst[k][1]); mapped.add(names[key])
        pb, cnt = M.proofs(whd0, wav0, bytes(whd), wav1, mapped, False)
        bad += ['round %d: %s' % (k, b) for b in pb]
    # the base: the stock .WHD against the grown .WAV
    pb, _ = M.proofs(whd0, wav0, whd0, wav1, set(), False)
    bad += ['stock .WHD + new .WAV: %s' % b for b in pb]
    return bad, n


INSTALL = r'''r"""Installs / undoes the DEAD MEN MENU SOUNDS PICKER stage @STAGE@ (tools/kl_menu_sounds_1110.py): three files BESIDE the stock pair
<DD>\Scenes\kaneandlynch.WHD / .WAV (the stock pair is NEVER written, asserted on every path):
    kaneandlynch_deadmen.WHD  (= the stock .WHD)   kaneandlynch_deadmen.WAV  (stock + the appended clips)   kaneandlynch_deadmen.klms  (the table)
Played by klslot.c [MenuLook] DeadMen=1 + [MenuSounds] (klhook\ini_menusounds_1110.txt; a DLL with kls_menusounds, built in klhook\out_menusounds1110).
Applies at the NEXT game start.

  python install.py            write the three files; REFUSES when one exists, except a file of the 1109 stage (md5 in PREV) with --replace,
                               which MOVES it to <name>.before-menusounds_1110 first (--undo puts it back)
  python install.py --replace  see above
  python install.py --undo     remove what this wrote (md5-checked) and restore the .before-menusounds_1110 copies
  python install.py --dry      read-only: pins and what would happen
  --overlay-variant            the siblings beside the overlay copy (KLExpansion\Overlay\Scenes\), like the 1109 stage
  --game <dir>                 another Dog Days folder (rehearsals); --skip-run-check for those / a zombie kl2.exe only
Refuses unless the live stock pair's md5s are the pins, unless the staged files are the md5s build_report.json names, while kl2.exe runs, and
(not --dry) when less than the files + 64 MB are free. All or nothing."""
import hashlib, os, shutil, subprocess, sys

GAME = r'@GAME@'
HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = @STOCK@            # [(live stock file name under Scenes, pinned md5)]
STAGED = @STAGED@          # [(staged file name, md5)]
PREV = @PREV@              # {staged file name: [md5 of a file an older stage may have written there]}
BAK = '.before-menusounds_1110'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    try:
        return 'kl2.exe' in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout.lower()
    except OSError:
        return True


def main(a):
    undo, dry, replace, ov = '--undo' in a, '--dry' in a, '--replace' in a, '--overlay-variant' in a
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    scenes = os.path.join(game, 'Scenes')
    base = os.path.join(game, 'KLExpansion', 'Overlay', 'Scenes') if ov else scenes
    stock_paths = {os.path.normcase(os.path.join(scenes, n)) for n, _ in STOCK}
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    for n, pin in STOCK:
        p = os.path.join(scenes, n)
        if not os.path.isfile(p):
            print('REFUSED: stock %s is not there' % p); return 1
        cur = md5(p)
        print('%-24s live %s' % (n, cur))
        if cur != pin:
            print('REFUSED: %s md5 is not the pinned %s (the stock pair changed: re-stage with --accept-input)' % (n, pin)); return 1
    if ov and not undo and not os.path.isfile(os.path.join(base, STOCK[0][0])):
        print('REFUSED: no overlay copy %s: the hook would never look for a sibling there (use the plain install)' % os.path.join(base, STOCK[0][0])); return 1
    plan = []                                                  # (src, dst, backup action)
    for name, m in STAGED:
        src, dst = os.path.join(HERE, name), os.path.join(base, name)
        if os.path.normcase(dst) in stock_paths:
            print('REFUSED: target %s is the stock file (never written)' % dst); return 1
        if undo:
            if os.path.isfile(dst) and md5(dst) != m:
                print('REFUSED: %s is not the staged md5 %s (not this stage\'s file: left alone)' % (dst, m)); return 1
            if not os.path.isfile(dst) and not os.path.isfile(dst + BAK):
                print('REFUSED: %s is not there' % dst); return 1
            plan.append((src, dst, 'restore' if os.path.isfile(dst + BAK) else None))
            continue
        if not os.path.isfile(src) or md5(src) != m:
            print('REFUSED: staged %s missing or not md5 %s' % (src, m)); return 1
        act = None
        if os.path.exists(dst):
            if md5(dst) == m:
                print('REFUSED: %s is this stage already (nothing to do; --undo removes it)' % dst); return 1
            if not (replace and md5(dst) in PREV.get(name, [])):
                print('REFUSED: %s exists and is %s (never overwritten%s)' % (dst, 'an older stage\'s file' if md5(dst) in PREV.get(name, []) else 'not this stage\'s',
                                                                           '; --replace moves an older stage\'s file aside' if md5(dst) in PREV.get(name, []) else '')); return 1
            if os.path.exists(dst + BAK):
                print('REFUSED: %s exists already' % (dst + BAK)); return 1
            act = 'move'
        plan.append((src, dst, act))
    if not undo:
        need = sum(os.path.getsize(s) for s, _, _ in plan) + (64 << 20)
        if shutil.disk_usage(game).free < need:
            print('REFUSED: less than the files + 64 MB free on the game drive'); return 1
    if dry:
        for src, dst, act in plan:
            print('would %s %s%s' % ('remove' if undo else 'write', dst, ' and restore ' + dst + BAK if undo and act == 'restore' else (' (moving the old one to ' + dst + BAK + ')' if act == 'move' else '')))
        return 0
    done = []
    try:
        for src, dst, act in plan:
            if undo:
                if os.path.isfile(dst):
                    os.remove(dst); print('removed %s' % dst)
                if act == 'restore':
                    os.replace(dst + BAK, dst); print('restored %s' % dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if act == 'move':
                    os.replace(dst, dst + BAK); done.append(('moved', dst))
                shutil.copyfile(src, dst + '.tmp'); os.replace(dst + '.tmp', dst); done.append(('wrote', dst))
                print('written %s %s' % (dst, md5(dst)))
    except OSError as e:
        for what, d in reversed(done):
            try:
                if what == 'wrote':
                    os.remove(d)
                elif os.path.isfile(d + BAK):
                    os.replace(d + BAK, d)
            except OSError:
                pass
        print('FAILED (%s); %s' % (e, 'nothing left behind' if not undo else 'rerun --undo')); return 2
    if not undo:
        print('Done. The picks are the [MenuSounds] lines of KLHook.ini (klhook\\ini_menusounds_1110.txt); a change applies at the next game start.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def write_install(stage_dir, game, stock, staged, prev, log=print):
    src = (INSTALL.replace('@GAME@', game).replace('@STAGE@', os.path.basename(os.path.normpath(stage_dir))).replace('@STOCK@', repr(stock))
           .replace('@STAGED@', repr(staged)).replace('@PREV@', repr(prev)))
    open(os.path.join(stage_dir, 'install.py'), 'w', newline='\n').write(src)
    for nm, arg in (('INSTALL menu sounds 1110.bat', ' --replace'), ('UNDO menu sounds 1110.bat', ' --undo')):
        open(os.path.join(stage_dir, nm), 'w', newline='\r\n').write('@echo off\r\ncd /d "%~dp0"\r\npython install.py' + arg + '\r\npause\r\n')
    log('  install.py + 2 bats written')


def prev_md5s(prev_dirs):
    """{staged file name: [md5]} of the files an older stage dir (build_report.json 'staged') wrote under the same names."""
    out = {}
    for d in prev_dirs or []:
        rp = os.path.join(d, 'build_report.json')
        if os.path.isfile(rp):
            for ent in json.load(open(rp)).get('staged', []):
                out.setdefault(ent[0], []).append(ent[1])
    return out


def list_clips(dm, log=print):
    src = M.DMSources(dm, levels=False, log=log, lazy=False, load_wav=False)
    seen = []
    for p in src.paths:
        b = src.banks.get(p)
        for r in (b.records if b else []):
            if r.name.replace('\\', '/').lower().startswith(UI_PREFIX.lower()):
                seen.append(r)
    log('%-44s %-7s %6s %2s %8s %s' % ('name', 'codec', 'rate', 'ch', 'ms', 'usable'))
    for r in seen:
        log('%-44s %-7s %6d %2d %8.1f %s' % (r.name, M.CODEC_NAME.get(r.codec, '%#x' % r.codec), r.f['rate'], r.f['ch'], r.ms(),
                                           'streamed (the stream file, MenuLoop-like: ambience)' if r.streamed else ('yes (cut to %.1f s)' % (MAX_CLIP_MS / 1000.0) if r.ms() > MAX_CLIP_MS else 'yes')))
    for o in src.opened + ['FAILED ' + x for x in src.failed]:
        log('  ' + o)
    return seen


def stage(dd, dm, out_dir=OUT_DEFAULT, accept=False, extra=(), previews=False, prev_dirs=(), game_for_install=None, log=print):
    if np is None:
        raise Refused('numpy is needed for stage (kl_gunsnd uses it)')
    whd_p, wav_p = M.dd_pair(dd)
    bank = M.Bank('dd', whd_p, wav_p)
    if bank.wav is None:
        raise Refused('no .WAV beside %s' % whd_p)
    found = collections.OrderedDict([(os.path.basename(whd_p), M.md5b(bank.whd)), (os.path.basename(wav_p), M.md5b(bank.wav))])
    log('stock pair %s (%d records) md5 %s / %s' % (whd_p, len(bank.records), found[os.path.basename(whd_p)][:8], found[os.path.basename(wav_p)][:8]))
    M.check_pins(found, out_dir, accept, log)
    clips = collections.OrderedDict(CLIPS)
    for name in extra:
        cn = clip_name(name)
        if cn in RESERVED or not re.match(r'^[a-z0-9_.-]{1,40}$', cn):
            raise Refused('--clip %r: the choice name %r is reserved or not [a-z0-9_.-]' % (name, cn))
        clips[cn] = name if '/' in name or '\\' in name else UI_PREFIX + name
    src = M.DMSources(dm, levels=False, log=log)
    for cn, v in list(clips.items()):
        if '/' not in v:
            clips[cn] = UI_PREFIX + v + '.wav'
    wav1, events, choices, rows = build(bank, src, clips, log)
    table = table_text(len(bank.whd), fnv1a(bank.whd), len(wav1), events, choices)
    bad, counts = prove(bank.whd, bank.wav, wav1, events, choices, table, log)
    for b in bad:
        log('  PROOF FAILED: ' + b)
    if bad:
        raise Refused('%d proof(s) failed: nothing written' % len(bad))
    os.makedirs(out_dir, exist_ok=True)
    v_whd, v_wav = M.variant_names(whd_p, wav_p)
    v_tab = os.path.splitext(v_whd)[0] + '.klms'
    open(os.path.join(out_dir, v_whd), 'wb').write(bank.whd)
    open(os.path.join(out_dir, v_wav), 'wb').write(wav1)
    open(os.path.join(out_dir, v_tab), 'w', newline='\n').write(table)
    staged = [(v_whd, M.md5b(bank.whd)), (v_wav, M.md5b(wav1)), (v_tab, M.md5b(table.encode('latin1')))]
    stock = [(os.path.basename(whd_p), found[os.path.basename(whd_p)]), (os.path.basename(wav_p), found[os.path.basename(wav_p)])]
    rep = collections.OrderedDict([
        ('tool', 'kl_menu_sounds_1110.py stage'), ('when', datetime.datetime.now().isoformat(timespec='seconds')), ('dd', dd), ('dm', dm),
        ('stock', stock), ('staged', staged), ('events', [dict(key=k, rec_off='%#x' % o, default=d, record=n) for k, o, d, n in events]),
        ('clips', {k: v for k, v in clips.items()}), ('rows', rows), ('proof_counts', counts), ('proofs', 'PASS'),
        ('dm_opened', src.opened), ('dm_failed', src.failed),
        ('GUESS', ['which record the game plays for confirm / menu / window sounds', 'the rms level match (as 1109)',
                   'the engine reads the .WHD from the %TEMP% path and does not reopen the bank by another name'])])
    json.dump(rep, open(os.path.join(out_dir, 'build_report.json'), 'w'), indent=1)
    write_install(out_dir, game_for_install or dd, stock, staged, prev_md5s(prev_dirs), log)
    if previews:
        pd = os.path.join(out_dir, 'previews'); os.makedirs(pd, exist_ok=True)
        fo = field_offsets()
        for key, rec_off, dflt, recname in events:
            r0 = bank.find(recname)
            M.write_wav16(os.path.join(pd, '%s_stock.wav' % key), *M.decode_record(bank, r0))
            for ek, name, v in choices:
                if ek == key and name in ('dm', 'off') or (ek == key and dflt == 'dd' and name in ('menu', 'openwindow_04')):
                    whd = bytearray(bank.whd); apply_choice(whd, rec_off, fo, v)
                    b1 = M.Bank('dd', os.path.join(out_dir, v_whd), os.path.join(out_dir, v_wav))
                    b1.whd = bytes(whd); b1.items, b1.T = W.parse('dd', b1.whd)
                    f1 = dict(zip(W.DD_F, [vv for k2, o2, vv in b1.items if k2 == 'rec' and o2 == rec_off][0]))
                    r1 = M.Rec('dd', recname, rec_off, f1, r0.index)
                    M.write_wav16(os.path.join(pd, '%s_%s.wav' % (key, name)), *M.decode_record(b1, r1))
        log('  previews in %s' % pd)
    log('STAGED %s + %s + %s in %s (%d events, %d choices, .WAV %+d bytes); proofs PASS; NOT installed' % (v_whd, v_wav, v_tab, out_dir, len(events), len(choices), len(wav1) - len(bank.wav)))
    return rep


def check(stage_dir, dd, log=print):
    """-> problems [] (empty = PASS)."""
    bad = []
    rp = os.path.join(stage_dir, 'build_report.json')
    if not os.path.isfile(rp):
        return ['no build_report.json in %s' % stage_dir]
    rep = json.load(open(rp))
    whd_p, wav_p = M.dd_pair(dd)
    bank = M.Bank('dd', whd_p, wav_p)
    live = {os.path.basename(whd_p): M.md5b(bank.whd), os.path.basename(wav_p): M.md5b(bank.wav)}
    for n, m in rep['stock']:
        if live.get(n) != m:
            bad.append('live stock %s md5 %s != the stage\'s %s' % (n, live.get(n), m))
    files = {}
    for n, m in rep['staged']:
        p = os.path.join(stage_dir, n)
        if not os.path.isfile(p):
            bad.append('staged %s missing' % n); continue
        if M.fmd5(p) != m:
            bad.append('staged %s md5 != build_report' % n)
        files[os.path.splitext(n)[1].lower()] = p
    if len(files) == 3 and not bad:
        whd1, wav1 = M.read(files['.whd']), M.read(files['.wav'])
        table = open(files['.klms'], encoding='latin1').read()
        if whd1 != bank.whd:
            bad.append('staged .WHD is not the live stock .WHD')
        t = parse_table(table)
        events = [(k, o, d, n) for k, o, d, n in t['events']]
        choices = [(k, c, t['choices'][(k.lower(), c.lower())]) for k, c in t['order']]
        pb, counts = prove(bank.whd, bank.wav, wav1, events, choices, table, log)
        bad += pb
        for k, v in counts.items():
            log('  %s: %s' % (k, v))
    for b in bad:
        log('  FAIL ' + b)
    log('check %s: %s' % (stage_dir, 'PASS' if not bad else '%d problem(s)' % len(bad)))
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    c0 = sub.add_parser('clips'); c0.add_argument('--dm', required=True)
    s = sub.add_parser('stage'); s.add_argument('--dd', required=True); s.add_argument('--dm', required=True); s.add_argument('--out', default=OUT_DEFAULT)
    s.add_argument('--accept-input', action='store_true'); s.add_argument('--clip', action='append', default=[]); s.add_argument('--previews', action='store_true')
    s.add_argument('--prev', action='append', default=[], help='an older stage dir (menusounds_1109) whose files install.py --replace may move aside')
    c = sub.add_parser('check'); c.add_argument('stage_dir'); c.add_argument('--dd', required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'clips':
            list_clips(a.dm); return 0
        if a.cmd == 'stage':
            stage(a.dd, a.dm, a.out, a.accept_input, a.clip, a.previews, a.prev); return 0
        if a.cmd == 'check':
            return 1 if check(a.stage_dir, a.dd) else 0
    except Refused as e:
        print('REFUSED: %s' % e)
        return 1
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
