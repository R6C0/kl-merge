#!/usr/bin/env python3
r"""kl_lc_music_fix_1108.py - Last Call (DM05A) club music SILENT: two separate stages, built from the LIVE files (2026-11-08, offline, stage only).

Owner: the club music still does not play (faint at the entrance, silent elsewhere) even after the .SND gain boost (kl_lc_music_1107.py).
Read-only triage: the streams resolve; nothing STARTS the music. The club music is 10 positional ZSNDOBJ layers (Inside!Music!*), each gated by a
SoundLimiterFade whose on-list holds ROOMS (ZROOM). kl2.exe 0x7e49c0: a limiter is active when (listener in any on-entry, or both lists empty) and in no
off-entry; the listener room comes from the .rmc/.rmi cell table. kl_fa_club ~1083 ASSUMED the layers "play from load" - only true if the limiters open.
It cannot be decided offline whether the Dance_Floor rooms never become the listener room (cause a) or the 4-layer PCM16 sets fail silently (cause b).

  FIX A  (lcmusic_a_1108)  clean layers ALWAYS ON: the on-list and the off-list of the 7 CLEAN layers' SoundLimiterFade become empty (= always active).
         Entities (node - 1) 10760 10761 10762 10765 10770 10776 10778. The 3 MUFFLED layers (10766 10769 10775) stay room-gated (all open = doubled sound).
         Field-only edit of existing controllers: no new node, no class count / slot / REF change, no .oct/.rmi change.
         Reads: audible from load if (a) is the cause (the 3D layers keep their positional distance attenuation); silent still = cause (b) -> Fix B.
  FIX B  (lcmusic_b_1108)  B1 only: ZOnlineGameplaySettings fields 157 and 158 (0 in the live zip) = the sound of the 'm05_a_club_clean' layer (kl_str.set_fa_music,
         kl2 0x88edba: played at once as a 2-D sound at the settings' Init, 158 replaces it when the local player turns traitor). One 2-D track from load,
         whatever the room; the layers still run on top (may double where a layer opens). B2 (a ZPlayMusic node, new object, slot renumbering) is NOT built.
  A2 (bool f5 1 -> 0) and A3 (room entries -> boxes) of the design are NOT built (A2 is an A/B of its own, A3 adds nodes).

Both stages change ONLY the .prp member of F01_Main.zip and of F01_Main.bots.zip (the sibling carries the same prp structure; the same patch is applied to it
and is verified on its own). Every other member is byte-identical. F01_Main.bots.base.md5 = md5 of the plain staged zip. KLGuns.ini is copied but is
NOT in install.py's FILES (same md5 both sides: nothing to back up).

  python tools/kl_lc_music_fix_1108.py stage a|b|all [--in-dir <map dir>] [--out-root C:/kl_build_1024]
  python tools/kl_lc_music_fix_1108.py check a|b|all [--in-dir <map dir>] [--out-root C:/kl_build_1024]
Never installs anything. REFUSES unless the live files are the expected md5s and every patched object is what the design says it is."""
import hashlib, os, re, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'debug'))
import kl_fa
import kl_snd
import kl_str
import kl_skyline_1108 as SK
from kl_prp import units

BS = chr(92)
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(GAME, 'KLExpansion', 'Maps', 'DM05A')
OUT_ROOT = 'C:/kl_build_1024'
TEMPLATE = 'C:/kl_build_1024/citylights_1108/install.py'
PRP = 'Scenes/Locations/F01/F01_Main.prp'
SND = 'Scenes/Locations/F01/F01_Main.SND'
LIVE_MD5 = {'F01_Main.zip': '80b5547c9852808d0c4f28abaf6dd6a1', 'F01_Main.bots.zip': '1e02dbe5503661a804f758541dc8d98a',
            'F01_Main.bots.base.md5': 'c009e5afbb4bd3bf57aff2182601c281', 'KLGuns.ini': '33432bb94d8c9ea009b7255cdb4a430e'}
STAGES = {'a': ('lcmusic_a_1108', '.before-lcmusica1108', 'LCMUSICA1108'), 'b': ('lcmusic_b_1108', '.before-lcmusicb1108', 'LCMUSICB1108')}
MUSIC = 'STREAMS' + '!Inside!Music!'

# entity (node - 1), layer name (path tail after Inside!Music!), sound (m05_a_<s>), muffled?, on-list entries, fade in/out  (design spec table, dump of the live zip)
LAYERS = [
    (10760, 'Club_01_Clean_3D_Music_', 'club_clean_3d', False, 1, 1.0, 2.0),
    (10761, 'Club_01_Clean_3D_Music_02', 'club_clean_3d', False, 1, 2.0, 2.0),
    (10762, 'Club_01_Clean_3D_Music_Stairs', 'club_clean_3d', False, 2, 2.0, 2.0),
    (10765, 'Club_01_Clean_Music_01', 'club_clean', False, 3, 1.0, 2.0),
    (10766, 'Club_01_Muffled_3D', 'club_muffled_3d', True, 1, 1.0, 1.0),
    (10769, 'Club_01_Muffled_Music_01', 'club_muffled', True, 7, 1.0, 1.0),
    (10770, 'Club_02_Clean', 'club_2_clean', False, 6, 1.0, 1.0),
    (10775, 'Club_02_Muffled', 'club_2_muffled', True, 3, 1.0, 1.0),
    (10776, 'Club_02_Clean_3D', 'club_2_clean_3d', False, 1, 1.0, 1.0),
    (10778, 'Club_02_Clean_3D_02', 'club_2_clean_3d', False, 2, 1.0, 1.0),
]
BOOLS = [0, 1, 1, 0]            # f4..f7 of every club music limiter in the live zip
B_SOUND = 'club_clean'          # Fix B1: the 2-D clean layer 'Club_01_Clean_Music_01' (entity 10765)
B_ENTITY = 10765


def fmd5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def limiter_index(sc, k):
    hit = [i for i, (n, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(n) == 'SoundLimiterFade']
    if len(hit) != 1:
        raise SystemExit('REFUSED: %s has %d SoundLimiterFade controllers' % (sc.path[k], len(hit)))
    return hit[0]


def limiter_fields(sc, k):
    i = limiter_index(sc, k)
    return i, [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][i][1][1:-1])]


def load(zpath):
    """-> (scene, .prp bytes, .SND bytes); REFUSES unless the .prp round-trips through the scene (so only the edit changes bytes)"""
    sc, snd, _loc = kl_fa.load(zpath)
    with zipfile.ZipFile(zpath) as z:
        prp = z.read(PRP)
    if sc.p.serialize() != prp:
        raise SystemExit('REFUSED: %s: the .prp does not round-trip through the scene reader' % zpath)
    return sc, prp, snd


def verify_layers(sc, snd):
    """Every music layer is exactly what the design says (name, class, sound, bools, empty off-list, on-list size, fades). -> {entity: node}"""
    bank = kl_snd.Snd('dd', snd, b'')
    nodes = {}
    for ent, name, sound, muffled, non, fin, fout in LAYERS:
        k = ent + 1
        if k >= len(sc.nodes) or not sc.path[k].endswith(MUSIC + name):
            raise SystemExit('REFUSED: node %d is %r, not ...%s%s' % (k, sc.path[k] if k < len(sc.nodes) else None, MUSIC, name))
        if sc.cls(k) != 'ZSNDOBJ':
            raise SystemExit('REFUSED: %s is %s, not ZSNDOBJ' % (name, sc.cls(k)))
        have = bank.name(kl_fa.node_values(sc, k)[8])
        want = ('audio:levelsetup/level/m05_a/music/m05_a_%s#sound' % sound).encode()
        if have != want:
            raise SystemExit('REFUSED: %s plays %r, not %r' % (name, have, want))
        i, f = limiter_fields(sc, k)
        if len(f) != 8 or f[4:8] != BOOLS or f[1] != [] or len(f[0]) != non or (f[2], f[3]) != (fin, fout):
            raise SystemExit('REFUSED: %s limiter is %r, expected on=%d off=[] fade %s/%s bools %s' % (name, f, non, fin, fout, BOOLS))
        nodes[ent] = k
    return nodes


def edit_a(sc, snd, log):
    nodes, done = verify_layers(sc, snd), []
    for ent, name, sound, muffled, non, _fi, _fo in LAYERS:
        if muffled:
            continue                                         # the muffled layers stay room-gated
        k = nodes[ent]
        i = limiter_index(sc, k)
        # both lists empty = always active (kl2 0x7e49c0, design spec A); fades, bools and everything else untouched
        kl_fa.edit(sc, k, i, lambda us: (us.__setitem__(0, kl_fa._refs(sc, [])), us.__setitem__(1, kl_fa._refs(sc, []))))
        done.append((ent, name, non))
    log('  A: %d clean layers open (on-list -> empty): %s' % (len(done), ', '.join('%d %s (was %d)' % d for d in done)))
    return done


def edit_b(sc, snd, log):
    nodes = verify_layers(sc, snd)
    off = kl_fa.node_values(sc, nodes[B_ENTITY])[8]
    if kl_snd.Snd('dd', snd, b'').name(off) != ('audio:levelsetup/level/m05_a/music/m05_a_%s#sound' % B_SOUND).encode():
        raise SystemExit('REFUSED: entity %d no longer plays %s' % (B_ENTITY, B_SOUND))
    st = [(k, i, v) for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS) if len(v) == 340]
    if len(st) != 1 or st[0][2][157] != 0 or st[0][2][158] != 0:
        raise SystemExit('REFUSED: expected one settings object with fields 157/158 = 0, got %r' % [(k, v[157], v[158]) for k, _i, v in st])
    # GUESS: field 157 starts as a 2-D sound at level load and 158 replaces it when the player turns traitor (kl_str.set_fa_music doc, kl2 0x88edba);
    # both = the same sound so the track carries on. Unproven live that it plays in an FA round at all (Retomoto uses a PlayMusic controller instead).
    for field in (157, 158):
        if kl_str.set_fa_music(sc, off, field, lambda *a: None) != 1:
            raise SystemExit('REFUSED: set_fa_music(%d) did not write exactly one settings object' % field)
    log('  B1: settings fields 157 and 158 = %#x (%s) on 1 settings object' % (off, B_SOUND))
    return [off]


def patch_zip(src, dst, which, log):
    sc, prp, snd = load(src)
    (edit_a if which == 'a' else edit_b)(sc, snd, log)
    new = sc.p.serialize()
    if new == prp:
        raise SystemExit('REFUSED: the edit changed nothing')
    with zipfile.ZipFile(src) as z:
        members = [(i.filename, z.read(i.filename)) for i in z.infolist()]
    members = [(n, new if n == PRP else d) for n, d in members]
    SK.write_zip(dst, members, SK.tex_level(src))


def make_install(out, stage_md5, which, in_dir):
    name, tag, title = STAGES[which]
    t = open(TEMPLATE, encoding='utf-8').read()
    rows = ["    ('F01_Main.zip', '%s', '%s')," % (LIVE_MD5['F01_Main.zip'], stage_md5['F01_Main.zip']),
            "    ('F01_Main.bots.zip', '%s', '%s')," % (LIVE_MD5['F01_Main.bots.zip'], stage_md5['F01_Main.bots.zip']),
            "    ('F01_Main.bots.base.md5', '%s', '%s')," % (LIVE_MD5['F01_Main.bots.base.md5'], stage_md5['F01_Main.bots.base.md5'])]
    # KLGuns.ini is left out of FILES: same md5 before and after, nothing to back up
    t, k = re.subn(r"FILES = \[.*?\n\]\n", lambda m: "FILES = [   # name, live md5 before, staged md5 after (KLGuns.ini unchanged: not listed)\n" + '\n'.join(rows) + "\n]\n", t, flags=re.S)
    if k != 1:
        raise SystemExit('REFUSED: template has no single FILES block')
    t, k = re.subn(r"TAG = 'DM05A', '\.before-[a-z0-9]+'", "TAG = 'DM05A', '%s'" % tag, t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single TAG line')
    t, k = re.subn(r"LIVE_ZIP_MD5 = '[0-9a-f]{32}'", "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5['F01_Main.zip'], t)
    if k != 1:
        raise SystemExit('REFUSED: template has no single LIVE_ZIP_MD5 line')
    t = t.replace('CITYLIGHTS1108 (bench only) (tools/kl_skyline_1108.py)', '%s (bench only) (tools/kl_lc_music_fix_1108.py)' % title)
    t = t.replace('.before-skyline1108', tag)
    open(os.path.join(out, 'install.py'), 'w', encoding='utf-8', newline='\n').write(t)


def stage(which, in_dir, out_root, log=print):
    name, tag, title = STAGES[which]
    out = os.path.join(out_root, name)
    for n, want in LIVE_MD5.items():
        p = os.path.join(in_dir, n)
        if not os.path.isfile(p) or fmd5(p) != want:
            raise SystemExit('REFUSED: %s is %s, expected %s (the live DM05A changed: re-stage on the new live files)' % (p, fmd5(p) if os.path.isfile(p) else 'missing', want))
    os.makedirs(out, exist_ok=True)
    log('stage %s -> %s' % (which.upper(), out))
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        log(n)
        patch_zip(os.path.join(in_dir, n), os.path.join(out, n), which, log)
    with open(os.path.join(out, 'F01_Main.bots.base.md5'), 'w', newline='\n') as f:
        f.write(fmd5(os.path.join(out, 'F01_Main.zip')) + '\n')
    with open(os.path.join(in_dir, 'KLGuns.ini'), 'rb') as a, open(os.path.join(out, 'KLGuns.ini'), 'wb') as b:
        b.write(a.read())
    sm = {n: fmd5(os.path.join(out, n)) for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5')}
    make_install(out, sm, which, in_dir)
    for n in sorted(os.listdir(out)):
        log('  %-26s %s' % (n, fmd5(os.path.join(out, n))))
    return out


def node_diff(a, b):
    """[(node, 'props'|ctrl index)] where the two scenes differ"""
    if len(a.nodes) != len(b.nodes):
        return [('node count', len(a.nodes), len(b.nodes))]
    out = []
    for k in range(1, len(a.nodes)):
        na, nb = a.nodes[k], b.nodes[k]
        if na['props'] != nb['props']:
            out.append((k, 'props'))
        if len(na['ctrls']) != len(nb['ctrls']):
            out.append((k, 'ctrl count'))
            continue
        for i, (x, y) in enumerate(zip(na['ctrls'], nb['ctrls'])):
            if x != y:
                out.append((k, i))
    return out


def check(which, in_dir, out_root, log=print):
    name, tag, title = STAGES[which]
    out = os.path.join(out_root, name)
    bad = []
    def need(ok, msg):
        log('  %s %s' % ('ok  ' if ok else 'FAIL', msg))
        if not ok:
            bad.append(msg)
    log('check %s (%s)' % (which.upper(), out))
    for n in ('F01_Main.zip', 'F01_Main.bots.zip'):
        base, stg = os.path.join(in_dir, n), os.path.join(out, n)
        with zipfile.ZipFile(base) as zb, zipfile.ZipFile(stg) as zs:
            need(zb.namelist() == zs.namelist(), '%s: same member list and order (%d)' % (n, len(zb.namelist())))
            changed = [m for m in zb.namelist() if zb.read(m) != zs.read(m)]
            need(changed == [PRP], '%s: only the .prp differs (changed: %s)' % (n, changed))
        sb, _p, sndb = load(base)
        ss, _p2, snds = load(stg)
        nodes = verify_layers(sb, sndb)
        diff = node_diff(sb, ss)
        if which == 'a':
            want = sorted((nodes[e], limiter_index(sb, nodes[e])) for e, _n, _s, m, _o, _fi, _fo in LAYERS if not m)
            need(sorted(diff) == want, '%s: exactly the 7 clean limiters changed %s' % (n, sorted(diff)))
            for e, nm, sound, m, non, fin, fout in LAYERS:
                i, f = limiter_fields(ss, nodes[e])
                fb = limiter_fields(sb, nodes[e])[1]
                if m:
                    if f != fb:
                        need(False, '%s: muffled %s changed' % (n, nm))
                else:
                    if not (f[0] == [] and f[1] == [] and f[2:] == fb[2:]):
                        need(False, '%s: %s limiter is %r' % (n, nm, f))
        else:
            sets = [(k, i) for k, i, v in kl_fa.controllers(sb, kl_fa.SETTINGS) if len(v) == 340]
            need(sorted(diff) == sorted(sets), '%s: exactly the settings controller changed %s' % (n, sorted(diff)))
            _k, _i, v = [x for x in kl_fa.controllers(ss, kl_fa.SETTINGS) if len(x[2]) == 340][0]
            want = kl_fa.node_values(sb, nodes[B_ENTITY])[8]
            need(v[157] == want and v[158] == want, '%s: settings f157/f158 = %#x/%#x = the %s sound %#x' % (n, v[157], v[158], B_SOUND, want))
            vb = [x for x in kl_fa.controllers(sb, kl_fa.SETTINGS) if len(x[2]) == 340][0][2]
            need([x for j, x in enumerate(v) if j not in (157, 158)] == [x for j, x in enumerate(vb) if j not in (157, 158)], '%s: every other settings field equal' % n)
    md = open(os.path.join(out, 'F01_Main.bots.base.md5')).read().strip()
    need(md == fmd5(os.path.join(out, 'F01_Main.zip')), 'bots.base.md5 = md5 of the plain staged zip')
    need(fmd5(os.path.join(out, 'KLGuns.ini')) == LIVE_MD5['KLGuns.ini'], 'KLGuns.ini copied byte for byte')
    inst = open(os.path.join(out, 'install.py'), encoding='utf-8').read()
    compile(inst, 'install.py', 'exec')
    for n in ('F01_Main.zip', 'F01_Main.bots.zip', 'F01_Main.bots.base.md5'):
        need(("'%s', '%s', '%s')" % (n, LIVE_MD5[n], fmd5(os.path.join(out, n)))) in inst, 'install.py pins %s live %s -> staged %s' % (n, LIVE_MD5[n][:8], fmd5(os.path.join(out, n))[:8]))
    need("'%s'" % tag in inst and "LIVE_ZIP_MD5 = '%s'" % LIVE_MD5['F01_Main.zip'] in inst, 'install.py TAG %s and LIVE_ZIP_MD5 pinned' % tag)
    # debug/check.py: every node/controller record against the layouts Dog Days' own levels store (offline, read-only)
    try:
        import check as CK
        zp = os.path.join(out, 'F01_Main.zip')
        with zipfile.ZipFile(zp) as z:
            m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
            probs, nent = CK.problems(lambda e: z.read(m['.' + e.lstrip('.').lower()]))
        bprobs, _n = (lambda zb: CK.problems(lambda e: zb.read(m['.' + e.lstrip('.').lower()])))(zipfile.ZipFile(os.path.join(in_dir, 'F01_Main.zip')))
        need(set(probs) <= set(bprobs), 'debug/check.py: %d layout findings, none new against the live zip (%d there)' % (len(probs), len(bprobs)))
    except SystemExit:
        raise
    except Exception as e:                                   # the tool needs the Dog Days exe + stock zips; say so rather than hide it
        log('  skip debug/check.py (%s: %s)' % (type(e).__name__, e))
    r = subprocess.run([sys.executable, os.path.join(out, 'install.py'), '--dry'], capture_output=True, text=True)
    need(r.returncode == 0, 'install.py --dry exit %d: %s' % (r.returncode, (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1][:120]))
    log('check %s: %s' % (which.upper(), 'OK' if not bad else '%d FAIL' % len(bad)))
    return not bad


def main(a):
    if len(a) < 2 or a[0] not in ('stage', 'check') or a[1] not in ('a', 'b', 'all'):
        print(__doc__); return 2
    get = lambda k, d: a[a.index(k) + 1] if k in a else d
    in_dir, out_root = get('--in-dir', LIVE), get('--out-root', OUT_ROOT)
    ok = True
    for w in (('a', 'b') if a[1] == 'all' else (a[1],)):
        if a[0] == 'stage':
            stage(w, in_dir, out_root)
        ok = check(w, in_dir, out_root) and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
