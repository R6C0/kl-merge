#!/usr/bin/env python3
"""
kl_ambience.py - builds the ambience library for klhook/klambience.c ([Ambience]) and the KLHook.ini block that uses it.
OFFLINE: reads the game's sound data, writes only below --out (default G:\\kl_build_1023\\ambience_1023). Never writes into a game
folder. Needs ffmpeg on the PATH (or --ffmpeg). Nothing of the result has run in the game (2026-10-23).

    python kl_ambience.py build  [--out DIR] [--dd DIR] [--only group,...]   extract + convert every clip of SPEC
    python kl_ambience.py ini    [--out DIR] [--folder INSTALLED_DIR]                                  write <out>/KLHook.ambience.patch.ini (the ini block)
    python kl_ambience.py music  [--out DIR]                                  <out>/KLHook.music2.patch.ini: more Payday 2 tracks per map
    python kl_ambience.py check  [--out DIR]                                  every file the ini block names exists and decodes (ffprobe)
    python kl_ambience.py ini2   [--out DIR] [--base DIR]                     <out>/KLHook.ambience2.patch.ini: only the sections the 2nd pass changes
  --only takes group names (bed) or single ids (bed_diner). --base = the first pass's library (default OUT): a list names files of --out
  and --base, so a second pass can be built into its own folder and still be checked against the whole library.

SOURCES (all of it the games' own sound, nothing from Payday 2 here; the Payday 2 music is [Music], see tools/klmusic_check.py):
  * streams in <DD>\\PC_Def.str  (IOISNDSTREAM; tools/kl_audio.py): the long ambience beds, the police radio lines
  * in-memory clips of a level bank (<DD>\\KLExpansion\\Maps\\*\\*_Main.WHD/.WAV; tools/kl_gunsnd.py): sirens, alarms, choppers, dogs,
    birds, horns, distant shots. The first bank that holds the clip name is used.
OUTPUT: <out>\\<group>\\<id>.mp3 (44.1 kHz; beds stereo 96 kbps, cut at 240 s; one-shots mono 64 kbps, cut at 40 s). The police radio
  lines get a radio treatment (band 450..3400 Hz, soft clip, a short squelch tail) so they read as chatter on a handset.
GUESS marks: which bed fits which map is a guess from the map's name (nobody has heard these on the maps yet).
"""
import os, re, subprocess, sys, shutil, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
OUT = r'G:\kl_build_1023\ambience_1023'
DM = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men'
DM_STR = os.path.join(DM, 'PC_Def.str')
FFMPEG = shutil.which('ffmpeg') or r'C:\Users\Henri\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'

# ---- the library: id -> (group, source regex on the clip name, kind) -------------------------------------------------------
# kind: bed (stereo, long), shot (mono), radio (mono + radio filter). regex is matched with re.search on the clip's full name.
SPEC = [
    # beds (streams)
    ('bed_crowded_muffled', 'bed',  r'Ambiences/OutSide/Crowded_Street_Mufled_01\.wav$'),
    ('bed_crowded_street',  'bed',  r'Ambiences/OutSide/Crowded_Street_01\.wav$'),
    ('bed_big_street',      'bed',  r'Ambiences/OutSide/Big_Street_01\.wav$'),
    ('bed_alley',           'bed',  r'Ambiences/OutSide/Alley_01\.wav$'),
    ('bed_backalley',       'bed',  r'Ambiences/OutSide/BackAlleyAmbience\.wav$'),
    ('bed_alley_big',       'bed',  r'Ambiences/OutSide/Alley_Big_Ambience_01\.wav$'),
    ('bed_harbour',         'bed',  r'Ambiences/OutSide/Harbour_Ambience_Muffled_01\.wav$'),
    ('bed_harbour_nohorns', 'bed',  r'Ambiences/OutSide/Harbour_Ambience_NoHorns_01\.wav$'),
    ('bed_highway',         'bed',  r'Ambiences/Layered_FL/OutSide/Highway_Medium_Loop\.wav$'),
    ('bed_openarea',        'bed',  r'Ambiences/OutSide/OpenArea_01_2D_Layer01\.wav$'),
    ('bed_construction',    'bed',  r'Ambiences/M07_A/Outside/Construction_Site_01\.wav$'),
    ('bed_street_m01',      'bed',  r'Ambiences/M01_A/Outside/Street_City_01\.wav$'),
    ('bed_street_m05',      'bed',  r'Ambiences/M05_A/Outside/Street/Street_01\.wav$'),
    ('bed_restaurant',      'bed',  r'Ambiences/Inside/Restaurant_01\.wav$'),
    ('bed_hallways',        'bed',  r'Ambiences/M02_A/Inside/M02_FA_Ambience_InsideHallways\.wav$'),
    ('bed_parking',         'bed',  r'Ambiences/M03_A/Outside/Ambience_Parkinglot_1_M03\.wav$'),
    ('bed_havana',          'bed',  r'Ambiences/M11_A/Outside/Ambience_Outside_Default\.wav$'),
    ('bed_airport',         'bed',  r'Ambiences/MultiPlayer/F03/Airport_Ambience_01\.wav$'),
    ('bed_bridge',          'bed',  r'Ambiences/MultiPlayer/F02/Bridge_Ambience_Muffled\.wav$'),
    ('bed_rooftop',         'bed',  r'Ambiences/M09_A/Outside/Ambience_Rooftop_M09\.wav$'),
    # 2nd pass (2026-10-23): interior / exterior beds of the campaign levels the FA maps are built from. Each regex names ONE stream
    # (a bed regex that matches several keeps the last). Not used: M09_A Atrium/Office/Rooftop and M09_B Lobby (Retomoto's own, BedSkip).
    ('bed_diner',           'bed',  r'Ambiences/M01_A/Inside/Diner\.wav$'),
    ('bed_alley_m01',       'bed',  r'Ambiences/M01_A/Outside/Street_Alley_01\.wav$'),
    ('bed_bank_main',       'bed',  r'Ambiences/M03_A/Inside/Bank_Main_Ambience\.wav$'),
    ('bed_bank_lobby',      'bed',  r'Ambiences/M03_A/Inside/Ambience_Lobby_M03\.wav$'),
    ('bed_capatulio',       'bed',  r'Ambiences/M11_B/Outside/Ambience_Outside_Capatulio\.wav$'),
    # police radio (streams, Police01..03 voices) + the F02 bank's radio-com lines (memory)
    ('radio_{n}', 'radio', r'Oneliners/Police/PoliceRadio/PoliceRadio_0[1-5]0_Police0[123]\.wav$'),
    ('radiocom_{n}', 'radio', r'Dialog/AllLevels/PoliceRadioCom/Police_RadioCom_0\d\.wav$'),
    # alarms
    ('alarm_{n}', 'shot', r'SFX/Environment/Alarms/Alarm_003\.wav$|SFX/Environment/Alarms/Alarm_Buzzer_01\.wav$|Vehicles/CarAlarm/Car_Alarm\.wav$'),
    # helicopters
    ('heli_{n}', 'shot', r'Vehicles/Choppers/Chopper_Flying/Chopper_Flying_0\d\.wav$|Chopper_Bell_Rotor_01\.wav$|Chopper_Bell_SuperSonic_01\.wav$'),
    # distant fighting
    ('distant_{n}', 'shot', r'Common/Distant_Shots/[A-Za-z]+/Distant_Shot_[A-Za-z]+_01\.wav$|Distant_Explosion/Debris_Explosion_0\d\.wav$'),
    # sirens
    ('siren_{n}', 'shot', r'Environment/Sirens/Sirens/Siren_(0[1-9]|1[01])\.wav$|Police_Siren_onCar_0\d\.wav$'),
    # city life
    ('dog_{n}',   'shot', r'Dog_Barking_Distant/Dog_Barking_Distant_0\d\.wav$'),
    ('horn_{n}',  'shot', r'Cars/Car_Horns/Horn_0\d\.wav$'),
    ('gull_{n}',  'shot', r'SeaGulls_Muffled/SeaGulls_0\d\.wav$'),
    ('bird_{n}',  'shot', r'Birds/Warbler/Bird_Warbler_0\d\.wav$'),
    ('ship_{n}',  'shot', r'Vehicles/Ships/Ship_Horn_Distant_Mono_01\.wav$'),
    ('plane_{n}', 'shot', r'Planes/L11/L11_LandingFlight_M\.wav$|Planes_Propeller/Plane_Propeller_02\.wav$'),
    # Retomoto's Japanese police (2nd pass), kind 'shot' = no radio filter: megaphone shouts (10, ADPCM) and the AllLevels police
    # warning / order lines (6 + 5, ADPCM). NOT taken, because re/retomoto_audio.md 4.3 already puts them into the DM09 game stream:
    # EmergencyAnnounce_Japanese_Male_01 and Dialog/M09/.../M09B_OneLiners/PoliceWarning_010..050 (these two regexes cannot match them).
    ('jpmega_{n}', 'shot', r'SFX/Environment/Japanese Police Megaphone Shouts/Megaphone_0[12]/[^/]+\.wav$'),
    ('jpwarn_{n}', 'shot', r'Oneliners/Police/(PoliceWarning/PoliceWarning|PoliceOrders/PoliceOrders)_0[1-6]0_JapanesePolice\.wav$'),
]

# ---- the per-map plan (GUESS: from the map names; see re/ambience_1023.md) --------------------------------------------------
# key -> (BedVol, [bed ids], [spot groups]); spot groups: city = dogs + horns, sea = gulls + ship, park = birds + dogs, air = planes
MAPS = {
    # Dead Men maps (KLExpansion\Maps)
    'DM01':  (45, ['bed_restaurant', 'bed_street_m01', 'bed_diner', 'bed_alley_m01'], ['city']),   # Hot Coffee (diner)
    'DM01B': (45, ['bed_restaurant', 'bed_street_m01', 'bed_diner', 'bed_alley_m01'], ['city']),
    'DM02':  (40, ['bed_backalley', 'bed_crowded_muffled', 'bed_hallways'], ['city']),            # Late Night Opening (jewel shop, night)
    'DM03':  (45, ['bed_parking', 'bed_street_m05', 'bed_big_street', 'bed_bank_main', 'bed_bank_lobby'], ['city']),   # Withdrawal (bank)
    'DM06':  (40, ['bed_openarea', 'bed_highway'],                      ['park']),                 # A Walk in the Park
    'DM11B': (45, ['bed_havana', 'bed_capatulio'],                      ['city', 'sea']),          # Hasta (Havana)
    # engine-music / engine-ambience maps: no bed (BedSkip), one-shots only
    # Dog Days stock FA maps (copies DD01..DD09 and the F0x slots): they have their own ambience on F01/F02/F03/F06/F07 (MultiPlayer
    # ambience clips), so a quiet distance layer only; F04/F05/F08/F09 had none of that name (GUESS: thin), so a fuller bed.
    'DD01':  (25, ['bed_highway'],                                      ['city']),                 # Subway
    'DD02':  (25, ['bed_harbour', 'bed_highway'],                       ['sea', 'city']),          # Bridge
    'DD03':  (25, ['bed_highway'],                                      ['air', 'city']),          # Airport
    'DD04':  (40, ['bed_openarea', 'bed_highway'],                      ['park']),
    'DD05':  (40, ['bed_big_street', 'bed_crowded_muffled'],            ['city']),
    'DD06':  (25, ['bed_alley_big'],                                    ['city']),                 # warehouse
    'DD07':  (25, ['bed_crowded_street'],                               ['city']),                 # financial
    'DD08':  (40, ['bed_construction', 'bed_highway'],                  ['city']),
    'DD09':  (40, ['bed_big_street', 'bed_alley'],                      ['city']),
}
# Retomoto: no bed, no city Spot; the Radio list is the Japanese police pool instead of the English global one (small pool: long intervals)
RETOMOTO = ['DM09', 'DM09RB', 'DM09RB2', 'DM09RB3', 'DM09RB4', 'DM09RD', 'DM09RV', 'DM09RV2']
RETOMOTO_RADIO = ['jpmega', 'jpwarn']
RETOMOTO_RADIO_MIN, RETOMOTO_RADIO_MAX = 25, 60
BASE = OUT          # the first pass's library (see --base)
NEW_MAPS = ['DM01', 'DM01B', 'DM02', 'DM03', 'DM11B']      # maps whose Bed list the 2nd pass changes
BEDSKIP = ['DM09', 'DM09RB', 'DM09RB2', 'DM09RB3', 'DM09RB4', 'DM09RD', 'DM09RV', 'DM09RV2', 'DM06B', 'DM03A', 'DM05A', 'T01']
SPOTS = {'city': ['dog', 'horn'], 'sea': ['gull', 'ship'], 'park': ['bird', 'dog'], 'air': ['plane', 'dog']}
STOCK_SLOTS = {'F01': 'DD01', 'F02': 'DD02', 'F03': 'DD03', 'F04': 'DD04', 'F05': 'DD05', 'F06': 'DD06', 'F07': 'DD07', 'F08': 'DD08', 'F09': 'DD09'}


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode: raise RuntimeError('%s failed: %s' % (cmd[0], r.stdout[-400:].decode('latin1')))
    return r.stdout


def convert(src, dst, kind):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if kind == 'bed':
        af = ['-ac', '2', '-b:a', '96k', '-t', '240']
        flt = 'loudnorm=I=-26:TP=-3:LRA=11'
    elif kind == 'radio':
        af = ['-ac', '1', '-b:a', '64k', '-t', '30']
        flt = ('highpass=f=450,lowpass=f=3400,acompressor=threshold=-24dB:ratio=6:attack=3:release=60,'
               'volume=2.2,alimiter=limit=0.8,aecho=0.7:0.4:20:0.15,apad=pad_dur=0.12,loudnorm=I=-22:TP=-2:LRA=7')
    else:
        af = ['-ac', '1', '-b:a', '64k', '-t', '40']
        flt = 'loudnorm=I=-24:TP=-2:LRA=9'
    run([FFMPEG, '-y', '-v', 'error', '-i', src, '-af', flt, '-ar', '44100', '-codec:a', 'libmp3lame'] + af + [dst])


def collect(dd, log=print):
    """-> {outname: (src file, kind)} extracted into a temp folder; returns (items, tmpdir)"""
    import kl_audio, kl_gunsnd
    tmp = tempfile.mkdtemp(prefix='klamb_'); items = {}
    sf = kl_audio.StreamFile(os.path.join(dd, 'PC_Def.str'))
    sf2 = kl_audio.StreamFile(DM_STR) if os.path.isfile(DM_STR) else None      # Dead Men's own streams (fallback)
    banks = []
    for root in (os.path.join(dd, 'Scenes', 'Locations'), os.path.join(dd, 'KLExpansion', 'Maps'), os.path.join(DM, 'Scenes', 'Locations')):
        if not os.path.isdir(root): continue
        for m in sorted(os.listdir(root)):
            if not os.path.isdir(os.path.join(root, m)): continue
            for fn in os.listdir(os.path.join(root, m)):
                if fn.upper().endswith('_MAIN.WHD') and os.path.isfile(os.path.join(root, m, fn[:-4] + '.WAV')): banks.append(os.path.join(root, m, fn))
    seen_bank = {}
    def bank_waves(b):
        if b not in seen_bank:
            try: seen_bank[b] = kl_gunsnd.waves(open(b, 'rb').read())
            except Exception as e: log('bank %s unreadable (%s) - skipped' % (b, e)); seen_bank[b] = []
        return seen_bank[b]
    for oid, kind, rx in SPEC:
        pat = re.compile(rx); n = 0; taken = set()
        # streams first
        for src_sf in (sf, sf2):
            if src_sf is None or (n and kind == 'bed'): continue
            for c in src_sf.clips:
                if c.codec == 26 or not pat.search(c.name): continue
                base = c.name.replace('\\', '/').split('/')[-1][:-4]
                if base in taken: continue
                taken.add(base)
                p = kl_audio.export(src_sf, c, os.path.join(tmp, 'str'))
                n += 1; name = oid.format(n=n) if '{n}' in oid else oid
                items[name] = (p, kind, c.name)
        # then memory clips: the first bank holding each distinct clip
        for b in banks:
            if kind == 'bed': break
            for w in bank_waves(b):
                if w.streamed or not pat.search(w.name): continue
                base = w.name.replace('\\', '/').split('/')[-1][:-4]
                if base in taken: continue
                taken.add(base)
                wav = open(b[:-4] + '.WAV', 'rb').read()
                x = kl_gunsnd.decode_wave(wav, w)
                p = os.path.join(tmp, 'mem', base + '_%08x.wav' % w.rec_off); os.makedirs(os.path.dirname(p), exist_ok=True)
                kl_gunsnd.write_wav(p, kl_gunsnd.to_i16(x), w.get('rate'))
                n += 1; name = oid.format(n=n) if '{n}' in oid else oid
                items[name] = (p, kind, w.name)
        log('%-14s %2d clip(s)  %s' % (oid, n, rx[:60]))
    return items, tmp


def build(out=OUT, dd=DD, only=None, log=print):
    items, tmp = collect(dd, log)
    try:
        done = []
        for name in sorted(items):
            src, kind, orig = items[name]
            grp = name.split('_')[0]
            if only and grp not in only and name not in only: continue
            dst = os.path.join(out, grp, name + '.mp3')
            convert(src, dst, kind); done.append(name)
        with open(os.path.join(out, 'MANIFEST.part.txt' if only else 'MANIFEST.txt'), 'w') as f:      # a partial build never overwrites the full list
            for name in done: f.write('%s/%s.mp3\t%s\n' % (name.split('_')[0], name, items[name][2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    log('built %d files below %s' % (len(done), out))


def files_of(out, prefix):
    g = prefix.split('_')[0]; fs = set()
    for root in dict.fromkeys((out, BASE)):
        d = os.path.join(root, g)
        if os.path.isdir(d): fs.update(f for f in os.listdir(d) if f.startswith(prefix) and f.endswith('.mp3'))
    return sorted(fs)


def where(out, rel):
    """-> the path of a library file below --out, else below --base"""
    p = os.path.join(out, rel)
    return p if os.path.isfile(p) else os.path.join(BASE, rel)


def ini_text(out=OUT, folder=None, only=None, retomoto_radio=False):
    """only = a list of map keys: write just their [Ambience.<key>] sections (the patch of a later pass), no global block.
    retomoto_radio: the RETOMOTO sections also get the Japanese police Radio list (jpmega + jpwarn) with RETOMOTO_RADIO_MIN/MAX."""
    def lst(prefix, sub=None):
        fs = files_of(out, prefix)
        return ';'.join('%s\\%s' % (f.split('_')[0], f) for f in fs)
    L = ['; KLHook.ini block for klambience.c - made by tools/kl_ambience.py (2026-10-23). Append to KLHook.ini.',
         '[Ambience]', 'Enable=1', 'Volume=60', 'BedVol=40', 'Fade=2500', 'Folder=' + (folder or out), 'Log=1', 'ActionAfter=20',
         'BedSkip=' + ','.join(BEDSKIP),
         '; Radio: police chatter every 40-90 s once the heist is loud (60 s after the round began); Alarm: one bell when it goes loud',
         'Radio=' + ';'.join(lst('radio') .split(';') + lst('radiocom').split(';')).strip(';'),
         'RadioVol=60', 'RadioAfter=60', 'RadioMin=40', 'RadioMax=90',
         'Alarm=' + lst('alarm'), 'AlarmVol=55', 'AlarmAfter=0',
         'Heli=' + lst('heli'), 'HeliVol=70', 'HeliAfter=90', 'HeliMin=150', 'HeliMax=300',
         'Distant=' + lst('distant'), 'DistantVol=55', 'DistantAfter=10', 'DistantMin=30', 'DistantMax=80',
         'Siren=' + lst('siren'), 'SirenVol=60', 'SirenAfter=30', 'SirenMin=60', 'SirenMax=150',
         'Spot=' + ';'.join(lst('dog').split(';') + lst('horn').split(';')).strip(';'), 'SpotVol=50', 'SpotAfter=15', 'SpotMin=45', 'SpotMax=120', '']
    spot = {k: [s for p in v for s in lst(p).split(';') if s] for k, v in SPOTS.items()}
    def spots(groups):
        out_ = []
        for g in groups: out_ += spot[g]
        return ';'.join(dict.fromkeys(out_))
    if only: L = L[:1]
    for key, (bv, beds, groups) in MAPS.items():
        if only and key not in only: continue
        L += ['[Ambience.%s]' % key, 'BedVol=%d' % bv, 'Bed=' + ';'.join(lst(b).split(';')[0] for b in beds), 'Spot=' + spots(groups), '']
    # Retomoto and the other engine maps: one-shots only (global lists apply), horns and dogs would sit oddly in a tower: no Spot
    # (2nd pass: with retomoto_radio their Radio list is the Japanese police pool, rarer because the pool is small; BedSkip is untouched)
    for key in RETOMOTO:
        if only and key not in only: continue
        extra = []
        if retomoto_radio:
            jp = [s for p in RETOMOTO_RADIO for s in lst(p).split(';') if s]
            extra = ['Radio=' + ';'.join(jp), 'RadioMin=%d' % RETOMOTO_RADIO_MIN, 'RadioMax=%d' % RETOMOTO_RADIO_MAX]
        L += ['[Ambience.%s]' % key, 'Spot='] + extra + ['']
    if only: return '\r\n'.join(L)
    # the stock slots F01..F09 (the maps that are not redirected) use the DD lists
    for slot, dd in STOCK_SLOTS.items():
        bv, beds, groups = MAPS[dd]
        L += ['[Ambience.%s]' % slot, 'BedVol=%d' % bv, 'Bed=' + ';'.join(lst(b).split(';')[0] for b in beds), 'Spot=' + spots(groups), '']
    return '\r\n'.join(L)


def check(out=OUT):
    bad = 0
    for line in (ini_text(out) + '\r\n' + ini_text(out, only=NEW_MAPS + RETOMOTO, retomoto_radio=True)).split('\r\n'):
        if '=' not in line or line.startswith(';'): continue
        k, v = line.split('=', 1)
        if k in ('Bed', 'Radio', 'Alarm', 'Heli', 'Distant', 'Siren', 'Spot'):
            for f in [x for x in v.split(';') if x]:
                p = where(out, f)
                if not os.path.isfile(p) or os.path.getsize(p) < 2000: print('MISSING/EMPTY', p); bad += 1
                elif p.startswith(out):          # files of this pass: decode them (the first pass's files had their own check)
                    r = subprocess.run([FFMPEG, '-v', 'error', '-i', p, '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    if r.returncode or r.stdout.strip(): print('DECODE FAIL', p, r.stdout[-200:]); bad += 1
            if len([x for x in v.split(';') if x]) > 24: print('MORE THAN 24 in', line[:60]); bad += 1
    print('check: %d problems' % bad); return bad


# ---- more Payday 2 music per map (the [Music] pools of klhook/klmusic.c; files are the owner's own, played in place) -------------
PD2_A = r'C:\Steam\steamapps\common\PAYDAY 2\PAYDAY 2 the Soundtrack'
PD2_B = r'C:\Steam\steamapps\common\PAYDAY 2\Payday 2 - B-Sides'
# key -> (calm, action, escape, down); a number n = the soundtrack file 'NN_*.mp3', a string = a B-Sides prefix ('02 SWAT Attack')
MUSIC = {
    'DD01': ([7, 27, 21, 36], [35, 42, 38, 39, '02 SWAT Attack'], [24, 30, 46], [12, 17]),
    'DD02': ([20, 32, 25], [41, 19, '11 Meat and Machine Guns', 43], [13, 11, 47], [18, 12]),
    'DD03': ([3, 8, 28], [9, 16, 31, '12 The Enforcer'], [46, 30, 24], [17, 18]),
    'DD04': ([5, 29, 26], [37, 45, 6, '15 Duel'], [11, 13, 47], [12, 18]),
    'DD05': ([2, 22, 23], [40, 10, '03 Showdown'], [24, 30], [17]),
    'DD06': ([8, 33, 36], [19, 41, 39, '13 Bad Attitude'], [13, 47], [12]),
    'DD07': ([25, 2, 15], [43, 35, '23 Cries of the City'], [30, 46], [18]),
    'DD08': ([20, 21, 29], [16, 42, 38, '14 Collide'], [24, 11], [17]),
    'DD09': ([3, 7, 44], [6, 10, '27 Fault Line'], [47, 30], [12]),
    'DM01': ([2, 5, 26], [45, 6, 10, 37], [13, 11], [12, 18]),
    'DM02': ([36, 20, 29], [19, 40, 41, 38], [24, 30], [17]),
    'DM03': ([2, 3, 25, 8], [35, 43, 16, '01 Enter the Hallway', '03 Showdown'], [13, 46, 11], [18, 12]),
    'DM06': ([5, 28, 21], [37, '15 Duel', 42], [47, 11], [12]),
}
# the music maps the owner already tuned in KLHook.ini ([Music.DM01B], [Music.DM11B]) are left alone


def find_track(spec):
    for d, isA in ((PD2_A, True), (PD2_B, False)):
        if not os.path.isdir(d): continue
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith('.mp3'): continue
            if isA and isinstance(spec, int) and re.match(r'%02d_' % spec, f): return f
            if (not isA) and isinstance(spec, str) and f.startswith(spec): return f
    return None


def music_text():
    miss = []; L = ['; KLHook.ini block: more Payday 2 music per map for klmusic.c ([Music.<key>] pools). Made by tools/kl_ambience.py music.',
                    '; The global [Music] Folder / FolderB already point at the soundtrack and the B-Sides.']
    def lst(specs):
        out = []
        for sp in specs:
            f = find_track(sp)
            if f: out.append(f)
            else: miss.append(sp)
        return ';'.join(out)
    sections = list(MUSIC) + [k for k in MUSIC if k.startswith('DD')]
    for key in list(MUSIC) + ['F0' + k[3] for k in MUSIC if k.startswith('DD')]:
        src = MUSIC[key if key in MUSIC else 'DD0' + key[2]]
        L += ['[Music.%s]' % key, 'Calm=' + lst(src[0]), 'Action=' + lst(src[1]), 'Escape=' + lst(src[2]), 'Down=' + lst(src[3]), '']
    if miss: L.insert(0, '; MISSING (dropped): %s' % miss)
    return '\r\n'.join(L), miss


def main(a):
    out = OUT; dd = DD; only = None
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; del a[i:i + 2]
    folder = None
    if '--folder' in a: i = a.index('--folder'); folder = a[i + 1]; del a[i:i + 2]
    global BASE
    if '--base' in a: i = a.index('--base'); BASE = a[i + 1]; del a[i:i + 2]
    if '--dd' in a: i = a.index('--dd'); dd = a[i + 1]; del a[i:i + 2]
    if '--only' in a: i = a.index('--only'); only = a[i + 1].split(','); del a[i:i + 2]
    if not a: print(__doc__); return 1
    if a[0] == 'build': build(out, dd, only)
    elif a[0] == 'ini':
        p = os.path.join(out, 'KLHook.ambience.patch.ini'); open(p, 'w', newline='').write(ini_text(out, folder)); print('wrote', p)
    elif a[0] == 'ini2':
        p = os.path.join(out, 'KLHook.ambience2.patch.ini')
        t = ('; KLHook.ini patch: ambience 2nd pass (only the sections that change; each replaces the same section of the first block). Made by tools/kl_ambience.py ini2.\r\n'
             + ini_text(out, folder, only=NEW_MAPS + RETOMOTO, retomoto_radio=True).split('\r\n', 1)[1] + '\r\n')
        open(p, 'w', newline='').write(t); print('wrote', p)
    elif a[0] == 'music':
        t, miss = music_text(); p = os.path.join(out, 'KLHook.music2.patch.ini'); open(p, 'w', newline='').write(t); print('wrote', p, 'missing:', miss)
    elif a[0] == 'check': return 1 if check(out) else 0
    else: print(__doc__); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
