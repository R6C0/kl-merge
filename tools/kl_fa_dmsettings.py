#!/usr/bin/env python3
"""
Repoint the Fragile Alliance settings' shoot-off-money lines (fields 66-71) and the police-side All_Dead line
(field 171) of a BUILT Dog Days slot folder to the Dead Men lines kl_dmlines.py grafts.

    python kl_fa_dmsettings.py <map folder> <out folder>     # run kl_dmlines.py on <out folder> afterwards

Only the .prp member of <slot>_Main.zip changes (two field groups of ZOnlineFragileAllianceSettings); every other member
and every side file is copied as it was. Default tools are untouched; this is a separate step.
Fields 66-71 are 'flag 1' fields (looked up as K_C1..K_C9): kl_dmlines aliases the grafted key to K_C1..K_C9.
Field 171 is flag 0 (the key itself). GUESS: field 171 (All_Dead) is said for the police side as the audit table
(re/audio.md) puts it; the Dead Men line 'Got 'em all' is a criminal-side voice line, used because the owner asked.
"""
import os, shutil, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_voice, kl_prpjoin as J

SHOOT = 'Multiplayer/Shoot_Off_Money/FA_ShootOffMoney_01'
ALLDEAD = 'Multiplayer/GameEnds/FA_AllDead'
FIELDS = {f: SHOOT for f in range(66, 72)}
FIELDS[171] = ALLDEAD


def run(folder, out, log=print):
    folder, out = os.path.abspath(folder), os.path.abspath(out)
    zn = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
    zp = os.path.join(folder, zn)
    sc, _snd, _loc = kl_fa.load(zp)
    sets = kl_voice.settings(sc)
    if len(sets) != 1:
        raise SystemExit('expected one settings controller, found %d' % len(sets))
    k, i, v = sets[0]
    was = {f: v[f] for f in FIELDS}

    def fn(us):
        for f, s in FIELDS.items():
            us[f] = [kl_fa._str(sc, s)]
    kl_fa.edit(sc, k, i, fn)
    data, bad, _paths, _n = J.check(sc, log=lambda *_a: None)
    if bad:
        raise SystemExit('%d objects do not fit after the repoint' % len(bad))
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(folder):
        if f != zn:
            shutil.copyfile(os.path.join(folder, f), os.path.join(out, f))
    with zipfile.ZipFile(zp) as zin, zipfile.ZipFile(os.path.join(out, zn), 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as zo:
        for zi in zin.infolist():
            d = data if zi.filename.lower().endswith('_main.prp') else zin.read(zi.filename)
            ni = zipfile.ZipInfo(zi.filename, zi.date_time)
            ni.compress_type, ni.external_attr = zi.compress_type, zi.external_attr
            zo.writestr(ni, d)
    log('repointed %d fields on node %d: %s' % (len(FIELDS), k, {f: (was[f], FIELDS[f]) for f in (66, 171)}))
    return was


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(2)
    run(sys.argv[1], sys.argv[2])
