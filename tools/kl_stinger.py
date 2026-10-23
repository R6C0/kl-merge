#!/usr/bin/env python3
"""
kl_stinger.py - stages the event-stinger clips for klhook/klstinger.c ([Stinger]) and the KLHook.ini block that names them.
OFFLINE: reads the game's sound data and the Payday 2 audio already extracted under <work>\\pd2; writes ONLY below --out
(default <work>\\build\\stinger_1023, on G:). Never writes into a game folder. Never commits audio (the repo holds this script only).
Needs ffmpeg + ffprobe on the PATH (or --ffmpeg). Nothing of the result has run in the game (2026-10-23).

    python kl_stinger.py build   [--out DIR] [--dd DIR] [--work DIR]   extract + cut + convert every clip of SPEC -> <out>/<event>/<id>.mp3
    python kl_stinger.py ini     [--out DIR] [--folder INSTALLED_DIR]  write <out>/KLHook.stinger.patch.ini
    python kl_stinger.py check   [--out DIR]                           every file the ini names exists, decodes, is 0.5..12.5 s and not silent
    python kl_stinger.py package [--out DIR] [--dll SHIP.dll]          copy the installer (tools/stinger_1023/*) next to the clips (+ dll\\dinput8.dll)

SOURCES
  * 'dd'  : Dog Days' own PC_Def.str clips under SFX/Music/Music_Moments/ (IMA-ADPCM "music moments": short one-shot music phrases of the
            Dead Men / Dog Days levels; tools/kl_audio.py). Chosen by NAME only: nobody has listened to them for this job (GUESS).
  * 'pd2' : an excerpt (start second, length) of a Payday 2 track already extracted under <work>\\pd2\\audio\\wav (files named in PD2). The
            excerpt offsets are GUESSES (not listened to); each gets a 20 ms fade in and a 1.2 s fade out.
OUTPUT: stereo 44.1 kHz mp3 96 kbps, at most 10 s, loudness-normalised. Event folders: loud loot down dead betray last30 open reached.
GUESS: which phrase suits which event is a guess from the file names; the `check` step only proves length and non-silence. The lead should
listen once (play the folders) and edit SPEC / the ini lists; nothing else depends on the choice.
"""
import os, re, subprocess, sys, shutil, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
# the fallback paths below are the owner's PC (WinGet links); other machines need ffmpeg on the PATH or --ffmpeg
FFMPEG = shutil.which('ffmpeg') or r'C:\Users\Henri\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe'
FFPROBE = shutil.which('ffprobe') or r'C:\Users\Henri\AppData\Local\Microsoft\WinGet\Links\ffprobe.exe'
MAXSEC = 10.0

def default_work():
    try:
        import kl_port_check
        return kl_port_check.workdir()
    except Exception:
        return os.path.join(r'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men', 'KL_PortTools')

WORK = default_work()
OUT = os.path.join(WORK, 'build', 'stinger_1023')

MM = 'SFX/Music/Music_Moments/'
# event -> [(id, 'dd', clip name) | (id, 'pd2', wav file, start s, length s)]    (ALL GUESSES, see the module doc)
SPEC = {
    'loud':    [('loud_1', 'dd', MM + 'L11_Moment_1.wav'), ('loud_2', 'dd', MM + 'L11_Moment_4.wav'), ('loud_3', 'dd', MM + 'L04_Street_Moments_11.wav'),
                ('loud_pd2_razormind', 'pd2', 'razormind_312174304.wav', 0, 7)],
    'loot':    [('loot_1', 'dd', MM + 'L11_Moment_11.wav'), ('loot_2', 'dd', MM + 'L04_Cathedral_Moments_03.wav'), ('loot_3', 'dd', MM + 'L04_Alley_Moments_07.wav')],
    'down':    [('down_1', 'dd', MM + 'L10_Xtra_1_Cat.wav'), ('down_2', 'dd', MM + 'L04_Street_Moments_02.wav'), ('down_3', 'dd', MM + 'L11_Moment_14.wav')],
    'dead':    [('dead_1', 'dd', MM + 'L04_Alley_Moments_05.wav'), ('dead_2', 'dd', MM + 'L11_Moment_6.wav'), ('dead_3', 'dd', MM + 'L02_Moment_Derelict_1.wav')],
    'betray':  [('betray_1', 'dd', MM + 'L02_Moment_Derelict_3.wav'), ('betray_2', 'dd', MM + 'L04_Cathedral_Moments_02.wav'),
                ('betray_pd2_deathwish', 'pd2', 'verify_deathwish_567609487.wav', 30, 8)],
    'last30':  [('last30_1', 'dd', MM + 'L11_Moment_7.wav'), ('last30_2', 'dd', MM + 'L07_HullConstruction_Moments_1.wav'), ('last30_3', 'dd', MM + 'L11_Moment_12.wav')],
    'open':    [('open_1', 'dd', MM + 'L11_Moment_9.wav'), ('open_2', 'dd', MM + 'L02_Moment_Freeway_5.wav')],
    'reached': [('reached_1', 'dd', MM + 'L11_Moment_15.wav'), ('reached_2', 'dd', MM + 'L04_Cathedral_Moments_01.wav'),
                ('reached_pd2_music', 'pd2', 'music_121224598.wav', 0, 10)],
}
# the ini key of each event folder (klstinger.c names)
KEYS = [('loud', 'Loud'), ('loot', 'Loot'), ('down', 'Down'), ('dead', 'Dead'), ('betray', 'Betray'), ('last30', 'Last30'), ('open', 'Open'), ('reached', 'Reached')]


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode: raise RuntimeError('%s failed: %s' % (os.path.basename(cmd[0]), r.stdout[-400:].decode('latin1')))
    return r.stdout.decode('latin1')


def duration(path):
    return float(run([FFPROBE, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).strip())


def convert(src, dst, start=0.0, length=None):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    d = duration(src)
    t = min(MAXSEC, length if length else d, d - start)
    fo = max(0.0, t - 1.2)
    flt = 'afade=t=in:d=0.02,afade=t=out:st=%.2f:d=%.2f,loudnorm=I=-20:TP=-2:LRA=7' % (fo, min(1.2, t))
    cmd = [FFMPEG, '-y', '-v', 'error']
    if start: cmd += ['-ss', '%.2f' % start]
    cmd += ['-i', src, '-t', '%.2f' % t, '-af', flt, '-ar', '44100', '-ac', '2', '-codec:a', 'libmp3lame', '-b:a', '96k', dst]
    run(cmd)


def build(out=OUT, dd=DD, work=WORK, log=print):
    import kl_audio
    sf = kl_audio.StreamFile(os.path.join(dd, 'PC_Def.str'))
    byname = {c.name: c for c in sf.clips}
    tmp = tempfile.mkdtemp(prefix='klstg_'); done = []; miss = []
    wavdir = os.path.join(work, 'pd2', 'audio', 'wav')
    try:
        for ev, items in SPEC.items():
            for it in items:
                oid, kind = it[0], it[1]
                dst = os.path.join(out, ev, oid + '.mp3')
                if kind == 'dd':
                    c = byname.get(it[2])
                    if c is None: miss.append(it[2]); log('MISSING in PC_Def.str: ' + it[2]); continue
                    src = kl_audio.export(sf, c, os.path.join(tmp, 'dd'))
                    convert(src, dst); done.append((ev, oid, it[2]))
                else:
                    src = os.path.join(wavdir, it[2])
                    if not os.path.isfile(src): miss.append(it[2]); log('MISSING pd2 file: ' + src); continue
                    convert(src, dst, it[3], it[4]); done.append((ev, oid, 'pd2:%s @%ds +%ds' % (it[2], it[3], it[4])))
                log('%-22s <- %s' % (oid, done[-1][2]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    with open(os.path.join(out, 'MANIFEST.txt'), 'w') as f:
        for ev, oid, o in done: f.write('%s/%s.mp3\t%s\n' % (ev, oid, o))
    log('built %d files below %s (%d missing)' % (len(done), out, len(miss)))
    return 1 if miss else 0


def ini_text(out=OUT, folder=None):
    L = ['; KLHook.ini block for klstinger.c - made by tools/kl_stinger.py (2026-10-23). Append to KLHook.ini.',
         '[Stinger]', 'Enable=1', 'Volume=70', 'Folder=' + (folder or out), 'Log=1', 'Gap=3', 'LoudAfter=45', 'LastSec=30', 'LootEvery=0']
    for folder_, key in KEYS:
        d = os.path.join(out, folder_)
        fs = sorted(f for f in os.listdir(d) if f.endswith('.mp3')) if os.path.isdir(d) else []
        L.append('%s=%s' % (key, ';'.join('%s\\%s' % (folder_, f) for f in fs)))
    L.append('')
    return '\r\n'.join(L)


def check(out=OUT):
    bad = 0; rows = []
    for line in ini_text(out).split('\r\n'):
        if '=' not in line or line.startswith(';'): continue
        k, v = line.split('=', 1)
        if k not in [x[1] for x in KEYS]: continue
        if not v: print('EMPTY LIST', k); bad += 1
        for f in [x for x in v.split(';') if x]:
            p = os.path.join(out, f)
            if not os.path.isfile(p): print('MISSING', p); bad += 1; continue
            try:
                d = duration(p)
                vd = run([FFMPEG, '-v', 'info', '-i', p, '-af', 'volumedetect', '-f', 'null', '-'])
                m = re.search(r'mean_volume: (-?[\d.]+|-inf) dB', vd); mv = float(m.group(1)) if m and m.group(1) != '-inf' else -99.0
            except Exception as e:
                print('DECODE FAIL', p, e); bad += 1; continue
            flag = ''
            if d < 0.5 or d > 12.5: flag = ' LENGTH'; bad += 1
            if mv < -50: flag += ' SILENT'; bad += 1
            rows.append('%-28s %5.1f s  mean %6.1f dB%s' % (f, d, mv, flag))
    print('\n'.join(rows)); print('check: %d problems' % bad); return bad


def package(out=OUT, dll=None):
    src = os.path.join(HERE, 'stinger_1023')
    for fn in os.listdir(src): shutil.copy2(os.path.join(src, fn), os.path.join(out, fn))
    if dll:
        os.makedirs(os.path.join(out, 'dll'), exist_ok=True); shutil.copy2(dll, os.path.join(out, 'dll', 'dinput8.dll'))
    print('packaged into', out)


def main(a):
    out = OUT; dd = DD; work = WORK; folder = None; dll = None
    for flag in ('--out', '--dd', '--work', '--folder', '--dll', '--ffmpeg'):
        if flag in a:
            i = a.index(flag)
            if i + 1 >= len(a): print(flag, 'needs a value'); return 1
            v = a[i + 1]; del a[i:i + 2]
            if flag == '--out': out = v
            elif flag == '--dd': dd = v
            elif flag == '--work': work = v
            elif flag == '--folder': folder = v
            elif flag == '--dll': dll = v
            else:
                global FFMPEG; FFMPEG = v
    if not a: print(__doc__); return 1
    if a[0] == 'build': return build(out, dd, work)
    if a[0] == 'ini':
        p = os.path.join(out, 'KLHook.stinger.patch.ini')
        with open(p, 'w', newline='') as fh: fh.write(ini_text(out, folder))
        print('wrote', p); return 0
    if a[0] == 'check': return 1 if check(out) else 0
    if a[0] == 'package': package(out, dll); return 0
    print(__doc__); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
