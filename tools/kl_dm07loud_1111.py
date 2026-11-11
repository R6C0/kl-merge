r"""DM07 (The Dig) LOUD IMPACT FIX, stage only: writes the kit C:/kl_build_1024/dm07loud_1111 (install.py, pins.json, build_report.json, INSTALL/UNDO .bat, README.txt, previews).

CAUSE (MEASURED, 2026-11-11): the loudness passes (tools/kl_sndonline.py, owner rule "every sound at MP45 loudness", hard clip) boosted the impact
records of the DM07 bank <DD>\KLExpansion\Maps\DM07\F06_Main.WAV by +6..+17 dB over the Dead Men original, clipped at 0 dBFS. The map's own crane creaks
(set crane_creak_*, 2 emitters, wave SFX/Impacts/Shatter/Metal_Squeak/Metal_Squeak_*) went from rms -11..-14 dBFS to -2.6..-6.6 dBFS (peak 0): the loudest
map-specific sound after the group gain. The backup F06_Main.WAV.before-1026sndon holds the original data (equal to the Dead Men M07_A bank), same file
size and same record offsets, so the fix writes ONLY the selected records' byte ranges of the live WAV back from that backup (the .WHD is untouched).

VARIANTS (separate WAVs staged, choose at install time):
  creak    the 5 Metal_Squeak records (the prime culprit)
  impacts  creak + the other map emitter classes boosted by the same pass: Concrete_Burst (66 emitters), Metal_Fence_RigidBody (74), Metal_Throw (16),
           Wood_Break_Big (7..9)
GUESS: the owner's "loud ass thing" is the crane creak (nobody described it); the impacts variant covers the next candidates.

  python tools/kl_dm07loud_1111.py            stage the kit (reads the live files and the .before-1026sndon backup, writes only the kit)
  python tools/kl_dm07loud_1111.py --out DIR  another kit folder
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DD = r'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
MAPDIR = 'KLExpansion/Maps/DM07'
SRC_BAK = 'F06_Main.WAV.before-1026sndon'
OUT = r'C:/kl_build_1024/dm07loud_1111'
CREAK = ['/Shatter/Metal_Squeak/Metal_Squeak']
IMPACTS = CREAK + ['/Concrete_Break/Concrete_Burst', '/Metal_Fence_RigidBody/Metal_Fence_RigidBody', '/Shatter/Metal_Throw/Metal_Throw',
                   '/Wood_Break/Wood_Break_Big']
VARIANTS = {'creak': CREAK, 'impacts': IMPACTS}


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5b(b):
    return hashlib.md5(b).hexdigest()


def select(recs, patterns):
    """recs: [{'n': wave name, 'off', 'size', 'fmt'}] -> sorted [(off, size, name)] of in-memory records whose name contains a pattern (case-insensitive).
    Streamed (0x00800000) and language-stream (0x00400000) records live in other files and are skipped."""
    pats = [p.lower() for p in patterns]
    out = []
    for r in recs:
        if r['fmt'] & 0x00c00000:
            continue
        n = r['n'].replace('\\', '/').lower()
        if any(p in n for p in pats):
            out.append((r['off'], r['size'], r['n']))
    return sorted(out)


def patch(live, src, ranges):
    """live, src: bytes of equal length -> bytes: live with each (off, size, _) range taken from src (everything else untouched)."""
    if len(live) != len(src):
        raise ValueError('live and source WAV differ in size (%d vs %d)' % (len(live), len(src)))
    b = bytearray(live)
    for off, size, _ in ranges:
        if off < 0 or off + size > len(b):
            raise ValueError('range outside the WAV')
        b[off:off + size] = src[off:off + size]
    return bytes(b)


INSTALL_PY = r'''r"""Installs / undoes the DM07 LOUD IMPACT FIX (tools/kl_dm07loud_1111.py): replaces <DD>\KLExpansion\Maps\DM07\F06_Main.WAV by a copy whose
loud records are back at the Dead Men level (same size, same offsets; the .WHD is not touched). The old WAV is MOVED to F06_Main.WAV.before-dm07loud_1111.
Applies at the NEXT level load / game start.

  python install.py --variant creak|impacts   install (default creak)
  python install.py --undo                    put the old WAV back (byte-exact, md5-checked)
  python install.py --dry                     read-only: pins and what would happen
  --game <dir>                                another Dog Days folder (rehearsals); --skip-run-check for those
Refuses unless the live WAV / WHD md5s are the pins, while a real kl2.exe runs (zombies under 50 MB ignored), on a 2nd install, and (not --dry)
when less than the file + 64 MB are free. Never touches KL_PortBackup."""
import hashlib, os, shutil, subprocess, sys

GAME = r'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
HERE = os.path.dirname(os.path.abspath(__file__))
MAPDIR = 'KLExpansion/Maps/DM07'
WAV, WHD = 'F06_Main.WAV', 'F06_Main.WHD'
PIN_WAV, PIN_WHD = '@@PIN_WAV@@', '@@PIN_WHD@@'
STAGED = @@STAGED@@          # {variant: (staged file name, md5)}
BAK = '.before-dm07loud_1111'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def running():
    """True when a real kl2.exe runs (a zombie under 50 MB working set is ignored)."""
    try:
        out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    except OSError:
        return True
    for ln in out.splitlines():
        if 'kl2.exe' not in ln.lower():
            continue
        cells = [c.strip('"') for c in ln.split('","')]
        try:
            kb = int(''.join(ch for ch in cells[4] if ch.isdigit()))
        except (IndexError, ValueError):
            return True
        if kb >= 50 * 1024:
            return True
    return False


def main(a):
    undo, dry = '--undo' in a, '--dry' in a
    var = a[a.index('--variant') + 1] if '--variant' in a else 'creak'
    game = a[a.index('--game') + 1] if '--game' in a else GAME
    d = os.path.join(game, MAPDIR)
    wav, whd = os.path.join(d, WAV), os.path.join(d, WHD)
    if var not in STAGED:
        print('REFUSED: unknown variant %s (have %s)' % (var, ', '.join(sorted(STAGED)))); return 1
    if not dry and '--skip-run-check' not in a and running():
        print('REFUSED: kl2.exe is running: close the game first'); return 3
    for p in (wav, whd):
        if not os.path.isfile(p):
            print('REFUSED: %s is not there' % p); return 1
    if md5(whd) != PIN_WHD:
        print('REFUSED: %s md5 is not the pinned %s' % (whd, PIN_WHD)); return 1
    cur = md5(wav)
    print('%s live %s' % (WAV, cur))
    if undo:
        if not os.path.isfile(wav + BAK):
            print('REFUSED: no %s (nothing installed by this kit)' % (wav + BAK)); return 1
        if cur not in [m for _, m in STAGED.values()]:
            print('REFUSED: live WAV is not one of the staged files (not this kit files: left alone)'); return 1
        if md5(wav + BAK) != PIN_WAV:
            print('REFUSED: the backup is not the pinned original %s' % PIN_WAV); return 1
        if dry:
            print('would restore %s from %s' % (wav, wav + BAK)); return 0
        os.remove(wav); os.replace(wav + BAK, wav); print('restored %s %s' % (wav, md5(wav))); return 0
    name, m = STAGED[var]
    src = os.path.join(HERE, name)
    if cur != PIN_WAV:
        print('REFUSED: live WAV md5 %s is not the pinned %s (%s)' % (cur, PIN_WAV, 'already installed: --undo first' if cur in [x for _, x in STAGED.values()] else 'the map WAV changed: re-stage')); return 1
    if os.path.exists(wav + BAK):
        print('REFUSED: %s exists already' % (wav + BAK)); return 1
    if not os.path.isfile(src) or md5(src) != m:
        print('REFUSED: staged %s missing or not md5 %s' % (src, m)); return 1
    if not dry and shutil.disk_usage(game).free < os.path.getsize(src) + (64 << 20):
        print('REFUSED: less than the file + 64 MB free on the game drive'); return 1
    if dry:
        print('would move %s to %s and write %s (variant %s, md5 %s)' % (wav, wav + BAK, wav, var, m)); return 0
    try:
        shutil.copyfile(src, wav + '.tmp')
        if md5(wav + '.tmp') != m:
            raise OSError('copy md5 mismatch')
        os.replace(wav, wav + BAK)
        os.replace(wav + '.tmp', wav)
    except OSError as e:
        if os.path.isfile(wav + '.tmp'):
            os.remove(wav + '.tmp')
        if os.path.isfile(wav + BAK) and not os.path.isfile(wav):
            os.replace(wav + BAK, wav)
        print('FAILED (%s); nothing left behind' % e); return 2
    print('written %s %s (variant %s); applies at the next level load' % (wav, md5(wav), var))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
'''


def render_install(pin_wav, pin_whd, staged):
    return (INSTALL_PY.replace('@@PIN_WAV@@', pin_wav).replace('@@PIN_WHD@@', pin_whd)
            .replace('@@STAGED@@', repr(staged)))


def load_recs(whd_path):
    import kl_whd as W
    names, recs = {}, []
    for k, o, v in W.parse('dd', open(whd_path, 'rb').read())[0]:
        if k == 'name':
            names[o] = v.decode('latin1')
        else:
            f = dict(zip(W.FIELDS['dd'], v)); f['n'] = names.get(v[0], '?'); recs.append(f)
    return recs


def decode(f, wav):
    import numpy as np, kl_gunsnd as G
    d = wav[f['off']:f['off'] + f['size']]
    if (f['fmt'] & 0xffff) == 0x11:
        x = G.ima_decode(d, f['ch'], f['block'], f['spb'], f['samples'])
    else:
        x = np.frombuffer(d, '<i2').reshape(-1, f['ch'])
    return x.astype('int16'), f['rate']


def preview(recs, ranges, live, src, outdir):
    """~10 s WAV pair: the creak records one after the other with 0.4 s gaps, live (before) and restored (after)."""
    import numpy as np, kl_gunsnd as G
    byoff = {r['off']: r for r in recs}
    os.makedirs(outdir, exist_ok=True)
    for tag, wav in (('before', live), ('after', src)):
        parts, rate = [], None
        for off, size, n in ranges:
            x, rate = decode(byoff[off], wav)
            x = x[:, :1]
            parts += [x, np.zeros((int(rate * 0.4), 1), 'int16')]
        y = np.concatenate(parts)[:int(rate * 10)]
        G.write_wav(os.path.join(outdir, 'crane_creak_%s.wav' % tag), y, rate)


def rms_db(x):
    import numpy as np
    m = x.astype('float64') / 32768.0
    v = float(np.sqrt((m ** 2).mean()))
    return -120.0 if v <= 1e-6 else 20 * np.log10(v)


README = """DM07 (The Dig) loud sound fix, 2026-11-11 (NOT installed; staged only)

Cause (measured): the "every sound at MP45 loudness" pass boosted the map's impact records of F06_Main.WAV up to +17 dB over Dead Men and clipped them.
The crane creaks (Metal_Squeak_*, set crane_creak_*) are the loudest map-specific sound: rms -2.6..-6.6 dBFS, peak 0 (Dead Men: -11..-14).
GUESS: that is the owner's "loud ass thing"; nobody described the sound.

Variants (previews\\crane_creak_before.wav / crane_creak_after.wav let you hear the creak):
  creak    the 5 creak records back at Dead Men level                      (INSTALL DM07 loud fix 1111.bat)
  impacts  creak + Concrete_Burst, Metal_Fence_RigidBody, Metal_Throw, Wood_Break_Big  (INSTALL DM07 loud fix 1111 (impacts).bat)

Install needs the game closed. It MOVES <DD>\\KLExpansion\\Maps\\DM07\\F06_Main.WAV to F06_Main.WAV.before-dm07loud_1111 and writes the fixed one
(same size and offsets, .WHD untouched). Pins: live WAV {wav}; creak {c}; impacts {i}.
Undo: UNDO DM07 loud fix 1111.bat (byte-exact). python install.py --dry shows what would happen. Applies at the next level load.
"""


def stage(game=DD, out=OUT):
    d = os.path.join(game, MAPDIR)
    wp, hp, bp = os.path.join(d, 'F06_Main.WAV'), os.path.join(d, 'F06_Main.WHD'), os.path.join(d, SRC_BAK)
    for p in (wp, hp, bp):
        if not os.path.isfile(p):
            raise SystemExit('missing %s' % p)
    live, src = open(wp, 'rb').read(), open(bp, 'rb').read()
    recs = load_recs(hp)
    byoff = {r['off']: r for r in recs}
    os.makedirs(out, exist_ok=True)
    staged, report = {}, {'live_wav': md5b(live), 'whd': md5(hp), 'source': SRC_BAK, 'source_md5': md5b(src), 'variants': {}}
    for var, pats in VARIANTS.items():
        ranges = select(recs, pats)
        new = patch(live, src, ranges)
        name = 'F06_Main.WAV.%s' % var
        with open(os.path.join(out, name), 'wb') as f:
            f.write(new)
        staged[var] = (name, md5b(new))
        rows = []
        for off, size, n in ranges:
            a, b = decode(byoff[off], live), decode(byoff[off], new)
            rows.append({'wave': n, 'off': off, 'size': size, 'changed': live[off:off + size] != new[off:off + size],
                         'rms_before': round(float(rms_db(a[0])), 1), 'rms_after': round(float(rms_db(b[0])), 1)})
        report['variants'][var] = {'md5': md5b(new), 'records': len(ranges), 'changed': sum(r['changed'] for r in rows), 'rows': rows}
    creak = select(recs, CREAK)
    preview(recs, creak, live, patch(live, src, creak), os.path.join(out, 'previews'))
    json.dump({'F06_Main.WAV': report['live_wav'], 'F06_Main.WHD': report['whd']}, open(os.path.join(out, 'pins.json'), 'w'), indent=1)
    json.dump(report, open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as f:
        f.write(render_install(report['live_wav'], report['whd'], staged))
    for fn, body in (('INSTALL DM07 loud fix 1111.bat', '@echo off\r\ncd /d "%~dp0"\r\npython install.py --variant creak\r\npause\r\n'),
                     ('INSTALL DM07 loud fix 1111 (impacts).bat', '@echo off\r\ncd /d "%~dp0"\r\npython install.py --variant impacts\r\npause\r\n'),
                     ('UNDO DM07 loud fix 1111.bat', '@echo off\r\ncd /d "%~dp0"\r\npython install.py --undo\r\npause\r\n')):
        with open(os.path.join(out, fn), 'w', newline='') as f:
            f.write(body)
    with open(os.path.join(out, 'README.txt'), 'w') as f:
        f.write(README.format(wav=report['live_wav'], c=staged['creak'][1], i=staged['impacts'][1]))
    return report


if __name__ == '__main__':
    o = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else OUT
    rep = stage(out=o)
    for v, r in rep['variants'].items():
        print(v, r['md5'], 'records', r['records'], 'changed', r['changed'])
        for row in r['rows']:
            print('   %-90s %7.1f -> %7.1f' % (row['wave'][-90:], row['rms_before'], row['rms_after']))
