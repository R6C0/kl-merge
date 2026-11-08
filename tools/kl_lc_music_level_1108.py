#!/usr/bin/env python3
r"""kl_lc_music_level_1108.py - Last Call (DM05A) club music LEVEL + OUTSIDE (2026-11-08, offline, stage only; built on the LIVE files).

Owner (after fix A + the .SND boost): "last call music so damn loud now ... in the building it plays outside too, muffle it outside and turn it down so it
matches the other maps with music".  Cause (read from the live zip, the exe and the bank): fix A (kl_lc_music_fix_1108.py) emptied both room lists of the 7 clean
limiters = always active map-wide (kl2 0x7e49c0), and the 1107 boost put group Ambient at 1.0 with the clean clips b1 100 (clips are ~5 dB hotter than DD's music).

PRP (field edits of 5 existing SoundLimiterFade controllers, no new node, no slot/REF change):
  2-D CLEAN layers 10765 (Club_01_Clean_Music_01) and 10770 (Club_02_Clean): OFF-list = [M05_A_Outside_Street_01a (entity 4651), M05_A_Outside_Roof_01a (3320)],
        ON-list stays empty. kl2 0x7e49c0 (read): lists not both empty -> the listener room is fetched ([[0xdd2640]+0xb00] vtable+0x164); NULL -> inactive;
        on-list empty -> starts ACTIVE (0x7e4ad6..ae3), an off-entry match -> inactive. So: clean everywhere EXCEPT while the listener room is an Outside room.
  MUFFLED layers 10766 (Club_01_Muffled_3D), 10769 (Club_01_Muffled_Music_01), 10775 (Club_02_Muffled): the two Outside rooms are APPENDED to the ON-list
        (their existing room/box entries stay), so outside = muffled only.
  The 5 clean 3-D layers (10760 10761 10762 10776 10778) are NOT gated: positional, so they fall off with distance outside, and they are the fallback that keeps
        the club audible inside if the listener room turns out to be NULL (then the gated 2-D + muffled layers are silent, the 3-D ones still play).
SND (same size, dword/byte edits, the .prp sound refs, .WHD, .WAV and _LS.SND stay byte-identical; the exact bytes are verified by check):
  b1 (byte at sound+0x2d; GUESS: percent volume, linear):  club_clean 100->28, club_2_clean 100->28, club_clean_3d 100->28, club_2_clean_3d 90->18 (keeps its
        stock 63:100 ratio against the others), club_muffled / club_2_muffled / club_muffled_3d 70->20.
  float at sound+0x18 (GUESS: 3-D radius) back to stock: club_clean_3d 9.0->6.0, club_2_clean_3d 3.0->2.0, club_muffled_3d 3.75->2.5 (undoes the x1.5 of the boost).
  Group Ambient (0x55730) is NOT touched: street / rooftop / club beds keep their boost (owner did not complain about them).
Level maths (GUESS, nothing measured live): decoded clip RMS, 2-D pair summed -8.0 dBFS, Retomoto's two action layers -13.3 dBFS at Music group 0.5
  (~-19 net). 28/100 = -11 dB -> ~-19 net. Muffled clip ~-10.8 dBFS single, 20/100 -> ~-25 net = ~6 dB under the clean pair.

  python tools/kl_lc_music_level_1108.py stage [--variant a|b] [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_lc_music_level_1108.py check [--variant a|b] [--in-dir <map dir>] [--out-root C:/kl_build_1024]
Never installs anything. REFUSES unless the live files are the expected md5s and every patched object holds the expected pre-edit value.
VARIANT B (--variant b, staged C:/kl_build_1024/lcmusiclevel_1108b, tag .before-lcmusiclevelb1108; the review of A said NOT PASS):
  NO room gate on the clean layers (fix A's empty lists stay: proven to play).  Only the 3 muffled limiters get the two Outside rooms appended (harmless if the
  listener room never matches).  The loudness comes down by the numbers alone (VARIANTS['b'] below has each value and the dBFS maths):
    group Ambient +0x24/+0x30 1.0 -> 0.5 (undo the boost's doubling), 2-D clean pair b1 100 -> 12 (faint map-wide bed), 3-D clean b1 100 -> 48 / 90 -> 30,
    muffled b1 70 -> 39 (stock), 3-D radius floats back to stock (6.0 / 2.0 / 2.5).
Undo: the staged install.py --undo (tag .before-lcmusiclevel1108 / .before-lcmusiclevelb1108). Fix B kit (lcmusic_b_1108) is pinned to the OLD base and is stale against this chain."""
import hashlib, os, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))
import kl_fa
import kl_snd as S
import kl_club_music2 as M
import kl_lc_music_fix_1108 as F          # limiter helpers, installer template writer, node_diff
import kl_skyline_1108 as SK

LIVE = F.LIVE
OUT_ROOT = F.OUT_ROOT
NAME, TAG, TITLE = 'lcmusiclevel_1108', '.before-lcmusiclevel1108', 'LCMUSICLEVEL1108'
LIVE_MD5 = {'F01_Main.zip': '0c0980c45a53ee09d8319222feefd090', 'F01_Main.bots.zip': '2f719e08001dd8fca0100648247525a0',
            'F01_Main.bots.base.md5': '0344d4c939ee8df503c70c889a719170', 'KLGuns.ini': '33432bb94d8c9ea009b7255cdb4a430e'}
PRP, SND = F.PRP, M.M_SND
F.LIVE_MD5, F.STAGES = LIVE_MD5, {'level': (NAME, TAG, TITLE)}   # make_install reads these module globals

OUTSIDE = (4651, 3320)                    # entities (node-1): M05_A_Outside_Street_01a, M05_A_Outside_Roof_01a (ZROOM)
OUTSIDE_NAMES = ('M05_A_Outside_Street_01a', 'M05_A_Outside_Roof_01a')
CLEAN_2D = (10765, 10770)                 # gated: off-list = Outside
MUFFLED = (10766, 10769, 10775)           # gated: Outside appended to the on-list
# sound suffix -> (expected b1 now, new b1); GUESS: b1 is a linear percent volume
B1 = {'m05_a_club_clean': (100, 28), 'm05_a_club_2_clean': (100, 28), 'm05_a_club_clean_3d': (100, 28), 'm05_a_club_2_clean_3d': (90, 18),
      'm05_a_club_muffled': (70, 20), 'm05_a_club_2_muffled': (70, 20), 'm05_a_club_muffled_3d': (70, 20)}
# sound suffix -> (expected radius now, stock radius); GUESS: +0x18 is the 3-D radius (the 1107 boost multiplied it by 1.5)
RADIUS = {'m05_a_club_clean_3d': (9.0, 6.0), 'm05_a_club_2_clean_3d': (3.0, 2.0), 'm05_a_club_muffled_3d': (3.75, 2.5)}
G_AMBIENT = M.G_AMBIENT
GATE_CLEAN = True                         # variant a: the 2-D clean limiters get the Outside off-list; variant b: they stay always-on (fix A)
GROUP = None                              # variant b: (old, new) float for group Ambient +0x24 and +0x30 (GUESS: the group gain); a: untouched

# VARIANT B values.  Level maths (all GUESS-based: b1 = linear percent volume, group = linear multiplier, clip RMS from the decoded PCM, no engine-bus
# measurement, no listener distance law known).  Reference = Retomoto: its two action layers sum to -13.3 dBFS RMS, b1 70 (-3.1 dB) in group Music 0.5
# (-6.0 dB) -> net -22.4 dBFS.  Club clips: 2-D Club_Clean -11.6, Club_2_Clean -10.5 (sum -8.0 dBFS at b1 100); 3-D variants -11.5 and -10.4.
#  group Ambient 0.5 = -6.0 dB for everything below.
#  2-D clean pair, b1 12 (-18.4 dB): -8.0 - 6.0 - 18.4 = -32.4 dBFS = a faint bed, ~10 dB under Retomoto on the street (map-wide, no gate).
#  3-D clean, club_clean_3d b1 48 and club_2_clean_3d b1 30 (keeps ~ the stock 63:100 ratio), one emitter of each at full level:
#      10log(10^-1.15 * .48^2 + 10^-1.04 * .30^2) = -16.1 dBFS at group 1.0 -> -22.1 dBFS at group 0.5, + the faint 2-D bed (-32.4) = -21.7 dBFS
#      on the dance floor (standing between emitters it is a few dB lower: a pair at full is the upper bound, the same basis as Retomoto's -13.3
#      for its two layers).  club_2_clean_3d gets 30, not its stock 63: at 63 alone it would already be -20.4 dBFS.
#  muffled b1 39 (stock, -8.2 dB; clip ~ -10.8): -10.8 - 8.2 - 6.0 = -25.0 dBFS: they play only in their rooms (+ Outside rooms if the listener room ever matches).
VARIANTS = {
    'a': dict(name='lcmusiclevel_1108', tag='.before-lcmusiclevel1108', title='LCMUSICLEVEL1108', gate=True, group=None,
              b1=dict(B1), radius=dict(RADIUS)),
    'b': dict(name='lcmusiclevel_1108b', tag='.before-lcmusiclevelb1108', title='LCMUSICLEVELB1108', gate=False, group=(1.0, 0.5),
              b1={'m05_a_club_clean': (100, 12), 'm05_a_club_2_clean': (100, 12), 'm05_a_club_clean_3d': (100, 48),
                  'm05_a_club_2_clean_3d': (90, 30), 'm05_a_club_muffled': (70, 39), 'm05_a_club_2_muffled': (70, 39),
                  'm05_a_club_muffled_3d': (70, 39)},
              radius=dict(RADIUS)),     # GUESS +0x18 = distance at which the 3-D falloff starts, in metres (1 world unit = 1 cm): stock 6 / 2 / 2.5 m
}


def use_variant(v):
    """Select a variant: sets the module globals the stage/check/installer code reads."""
    global NAME, TAG, TITLE, B1, RADIUS, GATE_CLEAN, GROUP
    d = VARIANTS[v]
    NAME, TAG, TITLE, GATE_CLEAN, GROUP = d['name'], d['tag'], d['title'], d['gate'], d['group']
    B1, RADIUS = d['b1'], d['radius']
    F.STAGES['level'] = (NAME, TAG, TITLE)


def fmd5(p):
    return F.fmd5(p)


def outside_paths(sc):
    out = []
    for ent, nm in zip(OUTSIDE, OUTSIDE_NAMES):
        k = ent + 1
        if sc.cls(k) != 'ZROOM' or not sc.path[k].endswith('\\' + nm):
            raise SystemExit('REFUSED: node %d is %s %r, not ZROOM ...%s' % (k, sc.cls(k), sc.path[k], nm))
        out.append(sc.path[k])
    return out


def edit_prp(sc, snd, log):
    # (F.verify_layers pins the PRE-fix-A state, so the layer checks are done here: clean ones must already be always-on)
    outs = outside_paths(sc)
    for ent, name, _s, muffled, non, fin, fout in F.LAYERS:
        k = ent + 1
        if not sc.path[k].endswith(F.MUSIC + name) or sc.cls(k) != 'ZSNDOBJ':
            raise SystemExit('REFUSED: node %d is not the %s layer' % (k, name))
        i, f = F.limiter_fields(sc, k)
        if len(f) != 8 or f[4:8] != F.BOOLS or (f[2], f[3]) != (fin, fout):
            raise SystemExit('REFUSED: %s limiter is %r (bools/fades differ from the design)' % (name, f))
        if muffled:
            if f[1] != [] or len(f[0]) != non:
                raise SystemExit('REFUSED: muffled %s limiter lists are %r (expected on=%d off=[])' % (name, f[:2], non))
        elif f[0] != [] or f[1] != []:
            raise SystemExit('REFUSED: clean %s limiter is not always-on (lists %r): fix A is not in this zip' % (name, f[:2]))
    for ent in (CLEAN_2D if GATE_CLEAN else ()):
        k = ent + 1
        i = F.limiter_index(sc, k)
        kl_fa.edit(sc, k, i, lambda us: us.__setitem__(1, kl_fa._refs(sc, outs)))
        log('  clean 2-D %d %s: off-list = Outside street + roof' % (ent, sc.path[k].rsplit('!', 1)[-1]))
    for ent in MUFFLED:
        k = ent + 1
        i, f = F.limiter_fields(sc, k)
        kl_fa.edit(sc, k, i, lambda us: us.__setitem__(0, kl_fa._refs(sc, list(f[0]) + outs)))
        log('  muffled %d %s: on-list %d -> %d (+ Outside street + roof)' % (ent, sc.path[k].rsplit('!', 1)[-1], len(f[0]), len(f[0]) + 2))


def edit_snd(snd, ls, log):
    """-> (new snd, [(label, offset, old, new)]). REFUSES unless every target holds its expected pre-edit value."""
    if S.cs(snd, S.u32(snd, G_AMBIENT + 0x3c)) != b'Ambient':
        raise SystemExit('REFUSED: 0x55730 is not group Ambient')
    names = M.sounds_by_suffix(S.Snd('dd', snd, ls).walk())
    out, done = bytearray(snd), []
    if GROUP:
        for off in (0x24, 0x30):
            cur = struct.unpack_from('<f', snd, G_AMBIENT + off)[0]
            if cur != GROUP[0]:
                raise SystemExit('REFUSED: group Ambient +%#x is %r, expected %r' % (off, cur, GROUP[0]))
            struct.pack_into('<f', out, G_AMBIENT + off, GROUP[1])
            done.append(('group Ambient +%#x' % off, G_AMBIENT + off, GROUP[0], GROUP[1]))
    for suf, (old, new) in B1.items():
        hit = sorted(set(names.get(suf, [])))
        if len(hit) != 1:
            raise SystemExit('REFUSED: %s: %d sounds' % (suf, len(hit)))
        o = hit[0]
        if snd[o + 0x2d] != old:
            raise SystemExit('REFUSED: %s b1 is %d, expected %d' % (suf, snd[o + 0x2d], old))
        out[o + 0x2d] = new
        done.append((suf + ' b1', o + 0x2d, old, new))
    for suf, (old, new) in RADIUS.items():
        o = names[suf][0]
        cur = struct.unpack_from('<f', snd, o + 0x18)[0]
        if cur != old:
            raise SystemExit('REFUSED: %s radius is %r, expected %r' % (suf, cur, old))
        struct.pack_into('<f', out, o + 0x18, new)
        done.append((suf + ' +0x18', o + 0x18, old, new))
    return bytes(out), done


def read_zip(p):
    with zipfile.ZipFile(p) as z:
        return [(i.filename, z.read(i.filename)) for i in z.infolist()]


def stage(in_dir, out_root, log=print):
    for n, want in LIVE_MD5.items():
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != want:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DM05A changed: re-stage on the new live files)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', want))
    ls = open(os.path.join(in_dir, 'F01_Main_LS.SND'), 'rb').read()
    out = os.path.join(out_root, NAME)
    os.makedirs(out, exist_ok=True)
    log('stage -> %s' % out)
    snds = set()
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        src, dst = os.path.join(in_dir, n), os.path.join(out, n)
        log(n)
        sc, prp, snd = F.load(src)
        snds.add(snd)
        edit_prp(sc, snd, log)
        newprp = sc.p.serialize()
        newsnd, done = edit_snd(snd, ls, log)
        members = [(m, newprp if m == PRP else newsnd if m == SND else d) for m, d in read_zip(src)]
        SK.write_zip(dst, members, SK.tex_level(src))
    if len(snds) != 1:
        raise SystemExit('REFUSED: the plain and bots zips carry different .SND members')
    for d in done:
        log('  SND %-28s @%#x %s -> %s' % d)
    with open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, 'F01_Main.zip')) + '\n')
    with open(os.path.join(in_dir, 'KLGuns.ini'), 'rb') as a, open(os.path.join(out, 'KLGuns.ini'), 'wb') as b:
        b.write(a.read())
    sm = {n: fmd5(os.path.join(out, n)) for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')}
    F.make_install(out, sm, 'level', in_dir)
    for n in sorted(os.listdir(out)):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


def check(in_dir, out_root, log=print):
    out = os.path.join(out_root, NAME)
    bad = []

    def need(ok, msg):
        log('  %s %s' % ('ok  ' if ok else 'FAIL', msg))
        if not ok:
            bad.append(msg)
    log('check (%s)' % out)
    ls = open(os.path.join(in_dir, 'F01_Main_LS.SND'), 'rb').read()
    want_prp = sorted([(e + 1, F.limiter_index(F.load(os.path.join(in_dir, 'F01_Main.zip'))[0], e + 1)) for e in (CLEAN_2D if GATE_CLEAN else ()) + MUFFLED])
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = [m for m in zb.namelist() if zb.read(m) != zs.read(m)]
            need(sorted(changed) == sorted([PRP, SND]), '%s: only .prp and .SND differ (changed: %s)' % (n, changed))
            sa, sb = zb.read(SND), zs.read(SND)
        sb_, _p, _s = F.load(base)
        ss, _p2, _s2 = F.load(stg)
        diff = F.node_diff(sb_, ss)
        need(sorted(diff) == want_prp, '%s: exactly the %d gated limiters changed %s' % (n, len(want_prp), sorted(diff)))
        outs = outside_paths(sb_)
        for e in CLEAN_2D:
            f0, f1 = F.limiter_fields(sb_, e + 1)[1], F.limiter_fields(ss, e + 1)[1]
            if GATE_CLEAN:
                need(f1 == [f0[0], outs] + f0[2:] and f0[0] == [] and f0[1] == [], '%s: clean 2-D %d on=[] off=Outside x2, fades/bools unchanged' % (n, e))
            else:
                need(f1 == f0 and f0[0] == [] and f0[1] == [], '%s: clean 2-D %d limiter untouched (always on, fix A)' % (n, e))
        for e in MUFFLED:
            f0, f1 = F.limiter_fields(sb_, e + 1)[1], F.limiter_fields(ss, e + 1)[1]
            need(f1 == [f0[0] + outs, f0[1]] + f0[2:] and f0[1] == [], '%s: muffled %d on-list = old + Outside x2 (%d entries)' % (n, e, len(f1[0])))
        for e in (10760, 10761, 10762, 10776, 10778):
            need(F.limiter_fields(sb_, e + 1) == F.limiter_fields(ss, e + 1), '%s: clean 3-D %d limiter untouched' % (n, e))
        # SND: exactly the intended bytes
        names = M.sounds_by_suffix(S.Snd('dd', sa, ls).walk())
        allowed = {}
        for suf, (old, new) in B1.items():
            allowed[names[suf][0] + 0x2d] = new
        for suf, (old, new) in RADIUS.items():
            for j, b in enumerate(struct.pack('<f', new)):
                allowed[names[suf][0] + 0x18 + j] = b
        for off in ((0x24, 0x30) if GROUP else ()):
            for j, b in enumerate(struct.pack('<f', GROUP[1])):
                allowed[G_AMBIENT + off + j] = b
        diffs = [i for i in range(len(sa)) if sa[i] != sb[i]]
        need(len(sa) == len(sb) and all(i in allowed and sb[i] == allowed[i] for i in diffs), '%s: .SND same size, %d bytes differ, all intended with intended values' % (n, len(diffs)))
        need(all(sb[i] == allowed[i] for i in allowed), '%s: every intended .SND byte holds its new value' % n)
        need(S.u32(sb, 0) == S.u32(sa, 0) and S.Snd('dd', sb, ls).walk().T == S.u32(sb, 0), '%s: _LS first dword (T) still matches' % n)
    md = open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip()
    need(md == fmd5(os.path.join(out, 'F01_Main.zip')), 'bots.base.md5 = md5 of the plain staged zip')
    need(fmd5(os.path.join(out, 'KLGuns.ini')) == LIVE_MD5['KLGuns.ini'], 'KLGuns.ini copied byte for byte')
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    need("'%s'" % TAG in inst and "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5['F01_Main.zip'] in inst, 'install.py TAG %s and LIVE_ZIP_MD5 pinned' % TAG)
    try:
        import check as CK
        zp = os.path.join(out, 'F01_Main.zip')
        with zipfile.ZipFile(zp) as z:
            m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
            probs, _n = CK.problems(lambda e: z.read(m['.' + e.lstrip('.').lower()]))
        zb = zipfile.ZipFile(os.path.join(in_dir, 'F01_Main.zip'))
        bprobs, _n = CK.problems(lambda e: zb.read(m['.' + e.lstrip('.').lower()]))
        need(set(probs) <= set(bprobs), 'debug/check.py: %d layout findings, none new against the live zip (%d there)' % (len(probs), len(bprobs)))
    except SystemExit:
        raise
    except Exception as e:
        log('  skip debug/check.py (%s: %s)' % (type(e).__name__, e))
    r = subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--dry'], capture_output=True, text=True)
    need(r.returncode == 0, 'install.py --dry exit %d: %s' % (r.returncode, (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1][:120]))
    log('check: %s' % ('OK' if not bad else '%d FAIL' % len(bad)))
    return not bad


def main(a):
    if not a or a[0] not in ('stage', 'check'):
        print(__doc__)
        return 2
    get = lambda k, d: a[a.index(k) + 1] if k in a else d
    use_variant(get('--variant', 'a'))
    in_dir, out_root = get('--in-dir', LIVE), get('--out-root', OUT_ROOT)
    if a[0] == 'stage':
        stage(in_dir, out_root)
    return 0 if check(in_dir, out_root) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
