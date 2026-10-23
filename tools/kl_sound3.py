"""kl_sound3.py - sound pass 3 (2026-10-23): per-map UNIQUE one-shots (Local / Panic groups of klhook/klambience.c) and
Payday 2 music by heist PHASE (the ASSAULT mood of klhook/klmusic.c). Reuses tools/kl_ambience.py (clip extraction, mp3 convert).

  python tools/kl_sound3.py build [--out DIR] [--dd DIR]     extract + convert the Local / Panic clips (ffmpeg) into DIR\\local, DIR\\panic
  python tools/kl_sound3.py ini   [--out DIR] [--ini FILE]   write DIR\\KLHook.sound3.patch.ini (full restated sections: the installed
                                                              KLHook.ini, read only, plus the new keys)
  python tools/kl_sound3.py check [--out DIR] [--ini FILE]   every file the patch names exists, decodes, lists <= 24 entries, PD2 tracks exist

DIR defaults to <work>\\build\\sound3_1023. Nothing here writes into the game folder; INSTALL sound3 1023.bat (made by `ini`) does that
and keeps a backup. Clips come from Dog Days' / Dead Men's own streams and banks (kl_audio / kl_gunsnd); they are never committed.
"""
import os, re, sys, shutil, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kl_ambience as A

try:
    import kl_port_check
    WORK = kl_port_check.workdir()
except Exception:
    WORK = r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools'
OUT = os.path.join(WORK, 'build', 'sound3_1023')
DD = A.DD
INI = os.path.join(DD, 'KLHook.ini')

# ---- the clip themes: (id, group, regex on the clip's full name, how many to keep) ---------------------------------------------
# Names were read from the exes' banks / streams (re/sound3_1023.md lists them); the regexes name real clips (checked by `build`).
# group: local = the Local one-shot group, panic = the Panic group. The number is a cap per theme (smallest files first is NOT tried:
# the first N in extraction order are kept).
THEMES = [
    # trains / planes / harbour / yard / machines
    ('train',    'local', r'Vehicles/Trains/Train_Brakes_Squeal/Train_Brake_Squeal_0\d\.wav$', 6),
    ('jet',      'local', r'Planes/Jet_Jumbo/(Plane_Jet_Flyby_01|Jet_Air_02|Jet_Steam_04)\.wav$', 3),
    ('planep',   'local', r'Planes/Planes_Passing/Plane_0\d\.wav$', 5),
    ('planei',   'local', r'MultiPlayer/F03/SFX/Planes_Idle/Plane_Idle_(0\d|Grind_0\d)\.wav$', 5),
    ('harbor',   'local', r'EffectSound/HarbourSounds_Muffled/HarbourSounds_\d+\.wav$', 5),
    ('hornh',    'local', r'Ships/HornsHarbour_Muffled/HornsHarbour_\d+\.wav$', 5),
    ('shipsq',   'local', r'Squeaks/Ship_Squeak_Reverbed/Ship_Squeak_\d+\.wav$', 4),
    ('crane',    'local', r'Machines/Crane/Crane_Mono/Crane_2D_\d+\.wav$', 4),
    ('hangar',   'local', r'HangarSounds_Metallic/HangarSounds/HangarSound_\d+\.wav$', 4),
    ('msq',      'local', r'EffectSound/Metal_Squeal/Metal_Squeal_\d+\.wav$', 5),
    ('mbend',    'local', r'Squeaks/Metal_Squeaks/(Metal_Bending|Metal_Crack)_\d+\.wav$', 4),
    ('shop',     'local', r'Environment/Workshop/Workshop_0\d\.wav$', 5),
    ('spark',    'local', r'Environment/Sparks/Sparks_Single_0\d\.wav$', 4),
    ('flicker',  'local', r'Lights/Fluorescent_Blink/Fluorescent_Blink_0\d\.wav$', 4),
    # traffic
    ('moped',    'local', r'Mopeds_Driving/Mopeds_0\d\.wav$', 4),
    ('mhorn',    'local', r'Moped_Horns/Horn_Moped_0\d\.wav$', 4),
    ('skid',     'local', r'Cars/Car_Skid/Car_Skid_0\d\.wav$', 4),
    ('bike',     'local', r'Bicycles_Bells/Bicycle_Bell_\d+\.wav$', 3),
    ('armor',    'local', r'Armoured_Transport/(Idle|Start|Stop|Running_Low)\.wav$', 3),
    # animals / weather
    ('cat',      'local', r'Animals/Cats/Cat_Roof_0\d\.wav$', 5),
    ('collie',   'local', r'Collie_Bark/CollieBark_0\d\.wav$', 5),
    ('cicada',   'local', r'Crickets/Cicadas/Cicadas_0\d\.wav$', 4),
    ('cricket',  'local', r'Insects/Crickets/Cricket_Once/[^/]+\.wav$', 3),
    ('wind',     'local', r'Weather/WindRumble/WindRumble_0\d\.wav$', 4),
    # offices / shops
    ('pc',       'local', r'Machines/Computers/Computer_0\d\.wav$', 4),
    ('cooler',   'local', r'Machines/WaterCooler/WaterCooler_\d+\.wav$', 3),
    ('kitchen',  'local', r'Environment/Kitchen/Kitchen_(Frying_02|MicrowaveOven|Refrigerator)\.wav$', 3),
    ('cash',     'local', r'Environment/Cash_Register/Cash_Register_01\.wav$', 1),
    ('bell',     'local', r'Environment/Bell/Bell\.wav$', 1),
    # Havana (GUESS: "Fly_xx / Flyimpact_xx" under Effects/M11_A are crash / fly-by effects of the campaign level; kept as distant crashes)
    ('m11',      'local', r'Effects/M11_A/5_Impacts_And_Chrash/Fly(impact)?_0\d\.wav$', 4),
    # Retomoto: lobby PA, lift bell, police-car radio static
    ('jpbus',    'local', r'M09_Bus_Announcement/Bus_Announcement_0\d\.wav$', 6),
    ('elev',     'local', r'Elevator_M09/Elevator_M09_Bell_01\.wav$', 1),
    ('jpstatic', 'local', r'PoliceCar/RadioStatic/Radio_Static_0\d\.wav$', 4),
    # panic: distant screams / crowd / English police megaphone
    ('scream',   'panic', r'Screams/Scream_Male/Scream_Male_A/Scream_Male_A_0\d\.wav$', 4),
    ('civpanic', 'panic', r'Civilians_Panic/Screams/Screams_00[0-9a-z]*_CivilianMale0\d\.wav$', 5),
    ('crowdp',   'panic', r'Voices/Crowd Panic/Crowd_Panic_01\.wav$', 1),
    ('mega',     'panic', r'Police Megaphone Shouts/Megaphone_01/[^/]+_0\d\.wav$', 6),
]
THEME_GROUP = {t[0]: t[1] for t in THEMES}

# ---- the per-map plan: key -> [theme, ...]  (GUESS: from the map names / which bank holds the clip; see re/sound3_1023.md) -----------
WEST_PANIC = ['scream', 'civpanic', 'crowdp', 'mega']
RETO_PANIC = ['scream', 'crowdp']
LOCAL = {
    'DM01':  ['jet', 'armor', 'kitchen', 'cash', 'moped', 'mhorn', 'shop'],                   # Hot Coffee: diner, airport trucks
    'DM01B': ['jet', 'armor', 'kitchen', 'skid', 'mhorn', 'spark'],
    'DM02':  ['cat', 'bell', 'skid', 'moped', 'flicker', 'spark', 'wind', 'cash'],            # night, jewel shop
    'DM03':  ['pc', 'cooler', 'cash', 'flicker', 'skid', 'spark', 'wind'],                    # bank
    'DM06':  ['cicada', 'bike', 'cricket', 'wind', 'collie'],                                 # the park
    'DM11B': ['m11', 'planep', 'moped', 'mhorn', 'hornh', 'wind'],                            # Havana
    'DD01':  ['train', 'shop', 'flicker', 'spark', 'wind', 'msq'],                            # Subway
    'DD02':  ['hornh', 'shipsq', 'mbend', 'wind', 'harbor'],                                  # Bridge
    'DD03':  ['planei', 'planep', 'hangar', 'flicker', 'wind'],                               # Airport
    'DD04':  ['collie', 'bike', 'cricket', 'wind', 'moped', 'mhorn'],
    'DD05':  ['harbor', 'hornh', 'msq', 'crane', 'spark', 'shipsq'],
    'DD06':  ['harbor', 'hangar', 'msq', 'flicker', 'shop', 'crane', 'moped'],
    'DD07':  ['pc', 'cooler', 'flicker', 'moped', 'mhorn', 'spark', 'shop'],
    'DD08':  ['crane', 'shop', 'spark', 'msq', 'flicker', 'wind'],
    'DD09':  ['cricket', 'cat', 'skid', 'bell', 'wind', 'moped'],
}
RETO_TOWER = ['jpbus', 'elev', 'jpstatic', 'pc', 'flicker']
RETO_STREET = ['skid', 'mhorn', 'moped', 'jpstatic', 'jpbus', 'wind']
for k in ('DM09', 'DM09RB', 'DM09RB2', 'DM09RB3', 'DM09RB4'): LOCAL[k] = RETO_TOWER
for k in ('DM09RD', 'DM09RV', 'DM09RV2'): LOCAL[k] = RETO_STREET
for i in range(1, 10): LOCAL['F0%d' % i] = LOCAL['DD0%d' % i]        # the stock slots F01..F09 play the Dog Days map of the same number
LOCAL_VOL = {'train': 0}   # (reserved) per-theme volume is not a thing: Local has one volume per map

# ---- Payday 2 music by phase (the owner's mp3 folders, played in place) -------------------------------------------------------
# key -> specs; a number = soundtrack file 'NN_*.mp3', a string = B-Sides prefix (same convention as kl_ambience.MUSIC)
ASSAULT = {
    'DD01': [31, 1, '12 The Enforcer', 4],         'DD02': [28, 14, '11 Meat and Machine Guns', 33],
    'DD03': [4, 31, '24 Caves of Cagliostro', 1],  'DD04': [32, 28, '15 Duel', '22 Longbow'],
    'DD05': [1, 14, '13 Bad Attitude', 33],        'DD06': [4, 28, '14 Collide', 31],
    'DD07': [14, 1, '23 Cries of the City', '25 They Chose Vlad'],  'DD08': [33, 31, '12 The Enforcer', '27 Fault Line'],
    'DD09': [32, 4, '03 Showdown', '24 Caves of Cagliostro'],
    'DM01': [1, 31, '13 Bad Attitude', 28],        'DM02': [33, 4, '25 They Chose Vlad', 14],
    'DM03': [4, 1, '12 The Enforcer', '23 Cries of the City'],       'DM06': [28, 32, '22 Longbow', '15 Duel'],
}
CALM_EXTRA = {
    'DD01': ['07 An Unexpected Call'], 'DD02': ['28 Sunrise', 26], 'DD03': ['26 Change of Pace'], 'DD04': ['16 Pilgrim', 44],
    'DD05': ['08 This is Goodbye'],    'DD06': ['17 Heroes of the Past'], 'DD07': [26, '26 Change of Pace'], 'DD08': ['28 Sunrise'],
    'DD09': ['07 An Unexpected Call', 44], 'DM01': ['16 Pilgrim'], 'DM02': ['08 This is Goodbye', 26],
    'DM03': ['26 Change of Pace', '07 An Unexpected Call'], 'DM06': ['28 Sunrise', 44],
}
GLOBAL_ASSAULT = [31, 1, 4, 14, 28, 33, 32, '12 The Enforcer', '13 Bad Attitude', '14 Collide']       # maps without their own pool
GLOBAL_CALM_EXTRA = [26, 44, '07 An Unexpected Call', '08 This is Goodbye', '28 Sunrise']
MUSIC_KEYS = list(ASSAULT) + ['F0%d' % i for i in range(1, 10)]
ASSAULT_AFTER = 150     # s after the round turned ACTION (GUESS: a Fragile Alliance heist is loud ~2.5 min before the police surge)


# ---- extraction -----------------------------------------------------------------------------------------------------------
def convert(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    A.run([A.FFMPEG, '-y', '-v', 'error', '-i', src, '-af', 'loudnorm=I=-24:TP=-2:LRA=9', '-ar', '44100', '-codec:a', 'libmp3lame',
           '-ac', '1', '-b:a', '64k', '-t', '25', dst])


def build(out=OUT, dd=DD, log=print):
    A.SPEC = [(t[0] + '_{n}', 'shot', t[2]) for t in THEMES]            # kl_ambience.collect reads its module-level SPEC
    items, tmp = A.collect(dd, log)
    done = []
    try:
        by = {}
        for name in items:
            theme, n = name.rsplit('_', 1); by.setdefault(theme, []).append((int(n), name))
        cap = {t[0]: t[3] for t in THEMES}
        for theme, lst in sorted(by.items()):
            i = 0
            for n, name in sorted(lst):
                if i >= cap[theme]: break
                dst = os.path.join(out, THEME_GROUP[theme], '%s_%d.mp3' % (theme, i + 1))
                convert(items[name][0], dst)
                if os.path.getsize(dst) < 1500:        # a click / blink too short to be heard as an ambience one-shot: take the next clip
                    os.remove(dst); log('  dropped %s (too short)' % items[name][2]); continue
                i += 1; done.append((dst, items[name][2]))
        missing = [t[0] for t in THEMES if t[0] not in by]
        if missing: log('NO CLIP FOUND for theme(s): %s (their maps just get fewer clips)' % ', '.join(missing))
        with open(os.path.join(out, 'MANIFEST.txt'), 'w') as f:
            for p, o in done: f.write('%s\t%s\n' % (os.path.relpath(p, out).replace('\\', '/'), o))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    log('built %d files below %s' % (len(done), out))


def lib(out, theme):
    g = THEME_GROUP[theme]; d = os.path.join(out, g)
    if not os.path.isdir(d): return []
    fs = sorted((f for f in os.listdir(d) if re.match(r'%s_\d+\.mp3$' % theme, f)), key=lambda f: int(f.rsplit('_', 1)[1][:-4]))
    return ['%s\\%s' % (g, f) for f in fs]


# ---- the installed ini, read only ----------------------------------------------------------------------------------------------
def read_sections(path):
    secs = {}; order = []; cur = None
    for line in open(path, encoding='latin1').read().splitlines():
        m = re.match(r'^\[(.+)\]\s*$', line.strip())
        if m: cur = m.group(1); secs.setdefault(cur, []); order.append(cur) if cur not in order else None; continue
        if cur is not None: secs[cur].append(line)
    return secs


def put(lines, key, val):
    """set key=val in a section's line list (replace the first line with that key, else append before trailing blanks)"""
    new = '%s=%s' % (key, val)
    for i, l in enumerate(lines):
        if l.split('=', 1)[0].strip().lower() == key.lower() and '=' in l and not l.lstrip().startswith(';'): lines[i] = new; return
    j = len(lines)
    while j and not lines[j - 1].strip(): j -= 1
    lines.insert(j, new)


def getv(lines, key):
    for l in lines:
        if '=' in l and not l.lstrip().startswith(';') and l.split('=', 1)[0].strip().lower() == key.lower(): return l.split('=', 1)[1]
    return ''


def track_list(specs, miss):
    out = []
    for sp in specs:
        f = A.find_track(sp)
        if f: out.append(f)
        else: miss.append(sp)
    return out


def merge_names(old, new):
    cur = [x for x in old.split(';') if x]
    return ';'.join(cur + [x for x in new if x not in cur])


MAXLIST = 24      # the hook's per-group file cap
CUT = []          # (map key, planned, dropped) for every Local list that had to be cut to MAXLIST; `check` reports it


def interleave(lists):
    out = []
    for i in range(max([len(l) for l in lists] or [0])):
        out.extend(l[i] for l in lists if i < len(l))
    return out


def ini_text(out=OUT, ini=INI):
    del CUT[:]
    secs = read_sections(ini); miss = []; L = []
    def emit(name, lines):
        L.append('[%s]' % name); L.extend(l for l in lines if True)
        while L and not L[-1].strip(): L.pop()
        L.append('')
    # --- Ambience: global block gains the Local / Panic timing + the shared Panic list
    g = []      # review fix: [Ambience] / [Music] carry ONLY the new keys; the installer merges them key by key into the live ini
    for k, v in (('LocalVol', 50), ('LocalAfter', 10), ('LocalMin', 25), ('LocalMax', 70),
                 ('PanicVol', 50), ('PanicAfter', 20), ('PanicMin', 40), ('PanicMax', 110)): put(g, k, v)
    put(g, 'Panic', ';'.join(f for t in WEST_PANIC for f in lib(out, t)))
    L.append('; KLHook.ini patch: sound pass 3 (2026-10-23). Made by tools/kl_sound3.py ini. [Ambience] and [Music] hold only the new keys and are MERGED key by key')
    L.append('; (Calm is unioned); every other [section] below REPLACES the same section of the installed KLHook.ini.')
    emit('Ambience', g)
    for key in LOCAL:
        base = list(secs.get('Ambience.' + key, [])); 
        files = interleave([lib(out, t) for t in LOCAL[key]])        # round-robin over the themes, so a cut drops the tails of every theme
        if len(files) > MAXLIST:
            CUT.append((key, len(files), len(files) - MAXLIST)); files = files[:MAXLIST]
        put(base, 'Local', ';'.join(files))
        if key.startswith('DM09'): put(base, 'Panic', ';'.join(f for t in RETO_PANIC for f in lib(out, t)))
        emit('Ambience.' + key, base)
    # --- Music: global block gains the Assault tier; per-map pools gain Assault + a longer Calm
    gm = list(secs.get('Music', [])); m = []         # gm = the installed global block (read only, for the Action de-dupe); m = the new keys
    gact = getv(gm, 'Action').split(';')
    put(m, 'Assault', ';'.join(t for t in track_list(GLOBAL_ASSAULT, miss) if t not in gact))     # a track in Action is not repeated as Assault
    put(m, 'AssaultAfter', ASSAULT_AFTER); put(m, 'AssaultOnDown', 1); put(m, 'AssaultMoney', 0)
    put(m, 'Calm', ';'.join(track_list(GLOBAL_CALM_EXTRA, miss)))       # the installer unions this with the live Calm
    emit('Music', m)
    for key in MUSIC_KEYS:
        src = key if key in ASSAULT else 'DD0' + key[2]
        base = list(secs.get('Music.' + key, []))
        act = (getv(base, 'Action') or getv(gm, 'Action')).split(';')
        put(base, 'Assault', ';'.join(t for t in track_list(ASSAULT[src], miss) if t not in act))
        put(base, 'Calm', merge_names(getv(base, 'Calm'), track_list(CALM_EXTRA[src], miss)))
        emit('Music.' + key, base)
    for key in ('DM01B', 'DM11B'):      # review fix: owner-tuned maps without a pool of their own: Assault filtered against THEIR Action list
        base = list(secs.get('Music.' + key, []))
        act = (getv(base, 'Action') or getv(gm, 'Action')).split(';')
        put(base, 'Assault', ';'.join(t for t in track_list(GLOBAL_ASSAULT, miss) if t not in act))
        emit('Music.' + key, base)
    if miss: L.insert(1, '; MISSING (dropped): %s' % miss)
    return '\r\n'.join(L) + '\r\n', miss


def check(out=OUT, ini=INI):
    bad = 0; text, miss = ini_text(out, ini)
    if miss: print('MISSING PD2 tracks:', miss); bad += 1
    for key, planned, dropped in CUT: print('note: Local list of %s cut from %d to %d (round-robin over themes: the tail of every theme is dropped)' % (key, planned, planned - dropped))
    for line in text.split('\r\n'):
        if '=' not in line or line.startswith(';'): continue
        k, v = line.split('=', 1)
        if k in ('Local', 'Panic'):
            fl = [x for x in v.split(';') if x]
            if len(fl) > MAXLIST: print('MORE THAN 24 in', k, line[:50]); bad += 1
            for f in fl:
                p = os.path.join(out, f)
                if not os.path.isfile(p) or os.path.getsize(p) < 1500: print('MISSING/EMPTY', p); bad += 1; continue
                r = subprocess.run([A.FFMPEG, '-v', 'error', '-i', p, '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if r.returncode or r.stdout.strip(): print('DECODE FAIL', p); bad += 1
    for key, th in LOCAL.items():
        if not any(lib(out, t) for t in th): print('map %s has an EMPTY Local list' % key); bad += 1
    print('check: %d problems' % bad); return bad


def main(a):
    out = OUT; dd = DD; ini = INI
    if '--out' in a: i = a.index('--out'); out = a[i + 1]; del a[i:i + 2]
    if '--dd' in a: i = a.index('--dd'); dd = a[i + 1]; del a[i:i + 2]
    if '--ini' in a: i = a.index('--ini'); ini = a[i + 1]; del a[i:i + 2]
    if not a: print(__doc__); return 1
    if a[0] == 'build': build(out, dd)
    elif a[0] == 'ini':
        t, miss = ini_text(out, ini); p = os.path.join(out, 'KLHook.sound3.patch.ini'); os.makedirs(out, exist_ok=True)
        open(p, 'w', newline='', encoding='latin1').write(t); print('wrote', p, 'missing tracks:', miss)
        for fn in ('sound3_1023.ps1', 'INSTALL sound3 1023.bat', 'UNDO sound3 1023.bat'):      # the installer travels with the staged files
            shutil.copyfile(os.path.join(HERE, fn), os.path.join(out, fn))
    elif a[0] == 'check': return 1 if check(out, ini) else 0
    else: print(__doc__); return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
