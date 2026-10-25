#!/usr/bin/env python3
"""kl_fedoutfit_dm05a.py - Last Call (DM05A): the player's fed gets a Japanese police body. OFFLINE, writes only the out folder.

  python tools/kl_fedoutfit_dm05a.py build <live DM05A F01_Main.zip> <out F01_Main.zip> [--pin <md5 prefix>]

Why a graft here and not [FedBody]: the club has no police actor (only yakuza, bodyguards, a bouncer, civilians), so the hook's
[FedBody] (klfedkit.c: one of the map's OWN models) has nothing to name. kl_chars.put brings Dead Men's JPN_Police_AllinOne (M09_B, the
`Teargas_Police_01` actor of the street squad, the same man DM09's model 52248 is) into the .prm and points the 8 police player objects
(ZFFPlayer, type MULTIPLAYER_POLICEMAN, stock model 1919) at it. No hook change: the fed spawns from those objects as before.
GUESSES, said plainly: that a ZFFPlayer of type MULTIPLAYER_POLICEMAN draws and animates an NPC model with the police set 'Lynch' (same
assumption as klfedkit.c's [FedBody]; the heroes' Dead Men models are proven live, a police-type player is not); the look choice (variant 1).
The cost is ~250 chunks / ~1.4 MB (extract_cost.py), well under re/prm_limit.md. C.put merges build/shared/union.fxc into the shader cache:
slimmed back afterwards exactly as kl_club_lastcall5 does (one heap block at load; a bigger cache is a crash risk for nothing).
"""
import hashlib
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_chars as C
import kl_fa_fedbody as FB

LEVEL = 'M09_B'
SOURCE = '20804'          # Squad_Teargasguys\JPN_Teargas_Police_01#02\Ground in M09_B (found by Source.person; DM09's 52248 after conversion)
VARIANT = 1               # JPN_Police_AllinOne, JPN_Headset_02, eye_Outer_Alpha (survey_DM09.txt variant 1)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def probs(zp):
    with tempfile.TemporaryDirectory() as t:
        shutil.copy(zp, os.path.join(t, 'F01_Main.zip'))
        lv = C.Lv(t)
        return C.check(lv, log=lambda *_: None) + ['people: ' + x for x in C.undrawn(lv)]


def graft_police(lv, log=print):
    """lv: a kl_chars.Lv of a DM05A build (edited in place). For a pipeline that builds the zip itself (kl_club_lastcall5): call this as a last
    step instead of staging the finished zip. Returns the kl_chars.put report. The .fxc is slimmed back (see the module doc)."""
    import kl_light
    import kl_fa
    sc, _raw = lv.scene()
    paths = [sc.path[k].replace('ROOT' + chr(92), '', 1) for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFPlayer' and
             'eZFFP_TYPE_MULTIPLAYER_POLICEMAN' in [x for x in kl_fa.node_values(sc, k) if isinstance(x, str)]]
    if not paths:
        raise ValueError('no police player object')
    rep = C.put(lv, [C.Pick(tuple(paths), LEVEL, SOURCE, {1: VARIANT, 2: VARIANT})], log=lambda *_: None)
    lv['.fxc'], frep = kl_light.slim_cache(C.T.read_mat(lv['.MAT']), lv['.fxc'], log=lambda *_: None)
    rep['fxc'] = frep
    return rep


def build(src, dst, pin=None, log=print):
    h = md5(src)
    if pin and not h.startswith(pin):
        raise SystemExit('refusing: %s md5 %s does not start with %s' % (src, h, pin))
    W = tempfile.mkdtemp(prefix='fedoutfit_dm05a_')
    try:
        os.makedirs(os.path.join(W, 'src'))
        shutil.copyfile(src, os.path.join(W, 'src', 'F01_Main.zip'))
        # The ini files beside the zip name models NO entity names (KLWardrobe.ini Root=, KLGuns.ini Root=). kl_chars.put reuses every chunk the
        # scene does not reach, and only knows these roots when the ini sits beside the zip it edits (Lv.side, wardrobe_roots). Without them the
        # 16 wardrobe models of Last Call were turned into 16-byte stubs (found by the 1025 adversarial review, 17130 chunks).
        for ini in ('KLWardrobe.ini', 'KLGuns.ini'):
            if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(src)), ini)):
                shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(src)), ini), os.path.join(W, 'src', ini))
        model, aset, paths = FB.Level(os.path.join(W, 'src')).police()
        paths = [p.replace('ROOT' + chr(92), '', 1) for p in paths]
        log('police player objects: %d on model %s, set %s' % (len(paths), model, aset))
        lv = C.Lv(os.path.join(W, 'src'))
        n0 = len(C.G.read(lv['.prm'], 'dd').chunks) - 1
        t0 = len(lv['.TEX'])
        rep = graft_police(lv)
        frep = rep['fxc']
        n1 = len(C.G.read(lv['.prm'], 'dd').chunks) - 1
        log('.prm chunks %d -> %d, .TEX %.1f -> %.1f MB, fxc slim: %s' % (n0, n1, t0 / 1e6, len(lv['.TEX']) / 1e6, frep))
        # guard: every chunk reachable from a KLWardrobe.ini / KLGuns.ini root must be byte identical to the live zip's
        import re
        live_prm = C.G.read(zipfile.ZipFile(src).read('Scenes/Locations/F01/F01_Main.prm'), 'dd')
        for ini in ('KLWardrobe.ini', 'KLGuns.ini'):
            ip = os.path.join(os.path.dirname(os.path.abspath(src)), ini)
            if not os.path.isfile(ip):
                continue
            roots = [int(x) for x in re.findall(r'^Root=(\d+)', open(ip).read(), re.M)]
            kinds, _a = C.G.walk(live_prm, roots)
            new_prm = C.G.read(lv['.prm'], 'dd')
            bad = [i for i in kinds if live_prm.chunks[i] != new_prm.chunks[i]]
            if bad:
                raise SystemExit('%s: %d chunks under its roots changed by the graft (first %s)' % (ini, len(bad), bad[:5]))
        out = os.path.join(W, 'out')
        lv.write(out, 'F01')
        zp = os.path.join(out, 'F01_Main.zip')
        base, new = set(probs(src)), [p for p in probs(zp) if p not in set(probs(src))]
        log('kl_chars.check: %d new problems (the live zip has %d of its own)' % (len(new), len(base)))
        for p in new[:20]:
            log('PROBLEM: ' + p)
        if new:
            raise SystemExit(1)
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        shutil.copyfile(zp, dst)
        log('built %s md5 %s (%.1f MB), picks: %s' % (dst, md5(dst), os.path.getsize(dst) / 1e6, [r.get('new_model') for r in rep['picks']]))
    finally:
        shutil.rmtree(W, ignore_errors=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    pin = a[a.index('--pin') + 1] if '--pin' in a else None
    if len(a) >= 3 and a[0] == 'build':
        build(a[1], a[2], pin)
    else:
        print(__doc__)
        sys.exit(2)
