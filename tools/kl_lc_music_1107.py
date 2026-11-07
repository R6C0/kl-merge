#!/usr/bin/env python3
r"""kl_lc_music_1107.py - Last Call (DM05A) club music AUDIBILITY boost, rebuilt on the CURRENT live base (2026-11-07, offline, stage only).

WHY: kl_club_music2.py stage A ("Club music boost (recommended on)") was never installed: its pins (SND 498cc81d, _LS 3b21242c) no longer match the live bank
(life pass 1105 appended 1776 bytes to the .SND; _LS and .WAV changed since). This rebuilds ONLY its in-place byte edits against whatever SND the live
zip holds, WITHOUT the Dead Men OST bed (that one adds a sound + a .WHD record + needs a .prp edit and is unproven), so nothing moves:
  1. mixer group 'Ambient' (0x55730) +0x24 and +0x30: 0.5 -> 1.0   (GUESS: group gain; every club music layer and bed sits in this group)
  2. b1 (byte 1 of the dword at sound+0x2c) of the muffled layers 39 -> 70, Club_02 3D 63 -> 90, club beds 5/12/11 -> 20/25/20   (GUESS: percent volume)
  3. float at sound+0x18 of the three 3D music layers x1.5   (GUESS: attenuation radius; revert by setting RADIUS_MUL = 1)
Same size, same offsets, so the .prp sound references, .WHD, .WAV and _LS.SND (its first dword depends on the SND length only) stay byte-identical.
Applied to BOTH F01_Main.zip and F01_Main.bots.zip (both carry the same .SND member); bots.base.md5 is the plain zip's md5.

  python tools/kl_lc_music_1107.py stage [--in-dir <map dir>] [--out <dir>]       (default in-dir: the live map, only READ; out C:\kl_build_1024\lcmusic_1107)
  python tools/kl_lc_music_1107.py check <out>

The install is the chain installer's install.py (tag .before-lcmusic1107): all or nothing, pins the live md5s, refuses while kl2.exe runs, --undo.
"""
import hashlib, json, os, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd as S
import kl_club_music2 as M
import kl_lastcall_chain_1106 as CH
import kl_zip_member as ZM

OUT = r'C:\kl_build_1024\lcmusic_1107'
TAG = '.before-lcmusic1107'
RADIUS_MUL = M.BOOST_RADIUS
md5 = lambda b: hashlib.md5(b).hexdigest()


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def edit_snd(snd, ls, log=print):
    """-> (new snd, list of edits). Raises ValueError unless every target is exactly what the live bank is expected to hold."""
    base = S.Snd('dd', snd, ls).walk()
    out = bytearray(snd)
    if S.cs(out, S.u32(out, M.G_AMBIENT + 0x3c)) != b'Ambient':
        raise ValueError('0x55730 is not group Ambient')
    done = []
    for off in (0x24, 0x30):
        v = struct.unpack_from('<f', out, M.G_AMBIENT + off)[0]
        if v == M.GROUP_GAIN:
            continue                                            # idempotent
        if v != 0.5:
            raise ValueError('group Ambient +%#x is %r, not 0.5' % (off, v))
        struct.pack_into('<f', out, M.G_AMBIENT + off, M.GROUP_GAIN)
        done.append(('Ambient +%#x' % off, 0.5, M.GROUP_GAIN))
    names = M.sounds_by_suffix(base)
    for suf, v in M.B1.items():
        hit = sorted(set(names.get(suf, [])))
        if len(hit) != 1:
            raise ValueError('%s: %d sounds' % (suf, len(hit)))
        o = hit[0]
        old = out[o + 0x2d]
        out[o + 0x2d] = max(old, v) if old < v else old       # never turn a sound DOWN
        if out[o + 0x2d] != old:
            done.append((suf + ' b1', old, out[o + 0x2d]))
    for suf in M.RADIUS:
        hit = sorted(set(names.get(suf, [])))
        if len(hit) != 1:
            raise ValueError('%s: %d sounds' % (suf, len(hit)))
        f = struct.unpack_from('<f', out, hit[0] + 0x18)[0]
        struct.pack_into('<f', out, hit[0] + 0x18, f * RADIUS_MUL)
        done.append((suf + ' +0x18', f, f * RADIUS_MUL))
    out = bytes(out)
    if len(out) != len(snd):
        raise ValueError('size changed')
    # only the expected dwords differ
    sounds = {o for o, t in base.kind.items() if t == 1}
    for i in range(0, len(snd), 4):
        if snd[i:i + 4] != out[i:i + 4]:
            if i in (M.G_AMBIENT + 0x24, M.G_AMBIENT + 0x30) or any(i == s + 0x2c or i == s + 0x18 for s in sounds):
                continue
            raise ValueError('unexpected change at %#x' % i)
    return out, done


def stage(in_dir=CH.MAPDIR, out=OUT, log=print):
    live = CH.read_live(in_dir)
    zp, bp = os.path.join(in_dir, 'F01_Main.zip'), os.path.join(in_dir, 'F01_Main.bots.zip')
    with zipfile.ZipFile(zp) as z:
        snd = z.read(M.M_SND)
    with zipfile.ZipFile(bp) as z:
        if md5(z.read(M.M_SND)) != md5(snd):
            raise ValueError('the bots zip carries another .SND than the plain zip')
    ls = open(os.path.join(in_dir, 'F01_Main_LS.SND'), 'rb').read()
    new, done = edit_snd(snd, ls, log)
    if new == snd:
        raise ValueError('nothing to change (already applied)')
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    f = os.path.join(out, '_snd.bin')
    open(f, 'wb').write(new)
    for name in ('F01_Main.zip', 'F01_Main.bots.zip'):
        ZM.replace(os.path.join(in_dir, name), M.M_SND, f, os.path.join(out, name))
    os.remove(f)
    plain = fmd5(os.path.join(out, 'F01_Main.zip'))
    open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n').write(plain + '\n')
    for n in CH.INIS:
        shutil.copyfile(os.path.join(in_dir, n), os.path.join(out, n))
    files = {n: (live[n], fmd5(os.path.join(out, n))) for n in CH.FILES5}
    CH.write_install(out, files, ['lcmusic1107'], TAG)
    json.dump(dict(in_dir=in_dir, files=files, edits=[list(map(str, d)) for d in done]), open(os.path.join(out, 'build_report.json'), 'w'), indent=1)
    bad = check(out, in_dir, log)
    for n, (o, w) in files.items():
        log('  %-26s live %s -> %s%s' % (n, o[:8], w[:8], '' if o != w else '  (unchanged, not installed)'))
    log('edits: %s' % done)
    log('CHECK: %s' % ('PASS' if not bad else 'FAIL ' + '; '.join(bad)))
    return bad


def check(out, in_dir=CH.MAPDIR, log=print):
    bad = []
    for name in ('F01_Main.zip', 'F01_Main.bots.zip'):
        a, b = zipfile.ZipFile(os.path.join(in_dir, name)), zipfile.ZipFile(os.path.join(out, name))
        if [i.filename for i in a.infolist()] != [i.filename for i in b.infolist()]:
            bad.append('%s: member list/order differs' % name)
            continue
        for i in a.infolist():
            if i.filename == M.M_SND:
                continue
            ia = b.getinfo(i.filename)
            if (ia.CRC, ia.file_size, ia.compress_type) != (i.CRC, i.file_size, i.compress_type):
                bad.append('%s: member %s differs' % (name, i.filename))
        sa, sb = a.read(M.M_SND), b.read(M.M_SND)
        if len(sa) != len(sb):
            bad.append('%s: SND size changed' % name)
    if open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip() != fmd5(os.path.join(out, 'F01_Main.zip')):
        bad.append('base.md5 is not the plain zip md5')
    ls = open(os.path.join(in_dir, 'F01_Main_LS.SND'), 'rb').read()
    with zipfile.ZipFile(os.path.join(out, 'F01_Main.zip')) as z:
        s = z.read(M.M_SND)
    if S.u32(s, 0) != S.Snd('dd', s, ls).walk().T:
        bad.append('_LS first dword no longer matches the SND (T)')
    return bad


def main(a):
    def opt(k, d):
        return a[a.index(k) + 1] if k in a else d
    if a[:1] == ['stage']:
        return 1 if stage(opt('--in-dir', CH.MAPDIR), opt('--out', OUT)) else 0
    if a[:1] == ['check'] and len(a) >= 2:
        bad = check(a[1], opt('--in-dir', CH.MAPDIR))
        print('CHECK:', 'PASS' if not bad else bad)
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
