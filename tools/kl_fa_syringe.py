#!/usr/bin/env python3
"""
DEAD MEN'S ADRENALINE SHOT, the exact clip, for a build (worker 'syringe', 2026-10-15; design: ../syringe_adrenaline_anim.md).
OFFLINE: reads a build folder, writes a COPY; installs nothing, starts no game.

    python kl_fa_syringe.py facts                       the heal / revive clips of Dead Men and of Dog Days, and how far apart
    python kl_fa_syringe.py apply <build folder> <out>  the build + slot '/Special_moves/Heal_wounded_DM' = Dead Men's OWN player clip
                                                        (M01_FA_A PlayerCharacter 'Heal_Wounded_01') in the sets Kane, Lynch, Kane_NPC,
                                                        Lynch_NPC; only the .ANM member differs; last line RESULT
WHY A SECOND SLOT: every Dog Days .ANM (stock and our builds) already has '/Special_moves/Heal_wounded' with a clip of the SAME NAME,
55 frames, but Dog Days re-did its arms: measured against Dead Men's (kl_fa_rappel._pose_gap, local rotations) 4 .. 21 degrees mean
over the body, the right hand / forearm 58 .. 110 degrees in frames 10 .. 54 (Dead Men's hand holds the syringe). The base slot is not
touched (kl2 never plays it for anybody: its player name table 0x78d9d0 resolves it at +0x28 but the heal action kind 0x12 plays
'/Special_moves/Heal_Down_not_dead'); klhook kladren.c [Adrenaline] Anim plays the _DM slot when the level has it, else the base slot.
The machinery is kl_anmjoin's (_Out / _Source / _add_lists), as tools/kl_fa_climb.py merge() uses it; credit luvsic for clip +0x2C.
"""
import collections, json, os, shutil, sys, zipfile
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools'))
import kl_anm, kl_anmjoin
import kl_port_check                                    # the game folders: the Windows guesses, plus the Linux VM's mounts (worker runs)
for _g, _p in ((kl_port_check.DM_GUESSES, '~/mnt/Kane and Lynch Dead Men'), (kl_port_check.DD_GUESSES, '~/mnt/Kane & Lynch 2 - Dog Days')):
    _p = os.path.expanduser(_p)
    if os.path.isdir(_p) and _p not in _g:
        _g.append(_p)

SOURCE = 'M01_FA_A'
SRC_SET = 'PlayerCharacter'
SRC_SLOT = '/Special_moves/Heal_wounded'
NEW_SLOT = '/Special_moves/Heal_wounded_DM'
SETS = ('Kane', 'Lynch', 'Kane_NPC', 'Lynch_NPC')


def _archive(folder):
    hit = [f for f in os.listdir(folder) if f.lower().endswith('_main.zip')]
    if len(hit) != 1:
        raise ValueError('%s: %d level archives' % (folder, len(hit)))
    return os.path.join(folder, hit[0])


def merge(raw, snd, log=print):
    base = kl_anm.Anm(raw)
    if base.game != 'dd':
        raise ValueError('the base is not a Dog Days .ANM')
    if NEW_SLOT in base.slots:
        raise ValueError('the build has %s already' % NEW_SLOT)
    dm = kl_anm.convert(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dm')))
    have = {c.short for c in base.cols}
    sets = [x for x in SETS if x in have]
    out = kl_anmjoin._Out(base)
    src = kl_anmjoin._Source(out, dm, True, 'M')
    a = out.a
    cols = {c.short: c for c in a.cols}
    lst = [(NEW_SLOT, l) for n, l in src.lists(dm.col(SRC_SET), {SRC_SLOT})]
    if len(lst) != 1:
        raise ValueError('Dead Men %s %s: no list' % (SRC_SET, SRC_SLOT))
    for x in sets:
        kl_anmjoin._add_lists(out, cols[x], src, lst)
    a.data = bytes(out.data)
    kl_anm.relist(a)
    snd_rep = dict(kl_anm.fix_clip_sounds(a, len(base.clips), kl_anmjoin.stock_snd(SOURCE, 'dm'), snd)) if snd is not None else None
    res = a.save()
    bad = []
    re_ = kl_anm.Anm(res, 'dd')
    if re_.save() != res:
        bad.append('does not read back to the same bytes')
    bad += ['audit: ' + b for b in kl_anm.audit(re_)[:10]]
    n = len(base.clips)
    if re_.clips[:n] != base.clips or re_.data[:len(base.data)] != base.data or re_.slots[:len(base.slots)] != base.slots:
        bad.append('the base changed')
    for c in base.cols:
        if any(re_.col(c.short).lists().get(k) != v for k, v in c.lists().items()):
            bad.append('slot lists of %s changed' % c.short)
    own_r, own_s = kl_anm.owners(re_), kl_anm.owners(dm)
    want = [(f, kl_anmjoin.signature(dm, i, own_s)) for f, i in dm.col(SRC_SET).lists()[dm.slots.index(SRC_SLOT)]]
    for x in sets:
        got = [(f, kl_anmjoin.signature(re_, i, own_r)) for f, i in re_.col(x).lists()[re_.slots.index(NEW_SLOT)]]
        if got != want:
            bad.append('%s %s: not Dead Men\'s clip' % (x, NEW_SLOT))
    if bad:
        raise ValueError('; '.join(bad))
    log('  %s + %s (Dead Men %s %s, %d clip record(s) / %d data byte(s) added) in %s; +0x2C: %s; %d -> %d bytes' % (
        os.path.basename(SOURCE), NEW_SLOT, SOURCE, SRC_SET, len(re_.clips) - n, len(re_.data) - len(base.data), ', '.join(sets), snd_rep, len(raw), len(res)))
    return res, dict(sets=sets, bytes=[len(raw), len(res)], clips_added=len(re_.clips) - n)


def apply(src, dst, log=print):
    import kl_graft
    zp = _archive(src)
    dst = os.path.abspath(dst)
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty' % dst)
    with zipfile.ZipFile(zp) as z:
        order = z.namelist()
        files = {k: z.read(k) for k in order}
    an = [k for k in order if k.lower().endswith('.anm')][0]
    sn = [k for k in order if k.lower().endswith('.snd') and '_LS' not in k.upper()]
    new, rep = merge(files[an], files[sn[0]] if sn else None, log)
    files[an] = new
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(k, files[k]) for k in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and '.before' not in x:
            shutil.copyfile(q, os.path.join(dst, x))
    with zipfile.ZipFile(zp) as za, zipfile.ZipFile(out) as zb:
        diff = [i.filename for i, j in zip(za.infolist(), zb.infolist()) if (i.CRC, i.file_size) != (j.CRC, j.file_size)]
    if diff != [an]:
        raise ValueError('more than the .ANM differs: %s' % diff)
    rep.update(source=zp, out=out, members_changed=diff)
    json.dump(rep, open(os.path.join(dst, 'syringe.json'), 'w'), indent=1)
    log('RESULT (kl_fa_syringe): OK - %s written; only %s differs' % (out, an))
    return rep


def facts(log=print):
    import kl_animsheet as S
    from kl_fa_rappel import _pose_gap
    dm = kl_anm.convert(kl_anm.Anm(kl_anmjoin.stock_anm(SOURCE, 'dm')))
    dd = kl_anm.Anm(kl_anmjoin.stock_anm('F07', 'dd'))
    for a, lab in ((dm, 'Dead Men ' + SOURCE), (dd, 'Dog Days F07')):
        for c in a.cols:
            for s, l in c.lists().items():
                if 'Heal' in a.slots[s] or 'Rise_From_Stomach' in a.slots[s]:
                    log('%s %-20s %-42s %s' % (lab, c.short, a.slots[s], [(hex(f), a.names[i].split('#')[-1], (a.clips[i][2] | a.clips[i][3] << 8)) for f, i in l]))
    nm = 'anim:Special_Moves/Heal_Wounded#Heal_Wounded_01'
    c1 = S.Clip(dm, kl_anm.owners(dm), dm.names.index(nm)); c2 = S.Clip(dd, kl_anm.owners(dd), dd.names.index(nm))
    for f in (0, 10, 20, 26, 30, 40, 50, 54):
        g, top = _pose_gap(c1, f, c2, f)
        log('Heal_Wounded_01 Dead Men vs Dog Days, frame %2d: %.1f deg mean; most %s' % (f, g, [(round(x, 1), b) for x, b in top]))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['facts']:
        facts()
    elif a[:1] == ['apply'] and len(a) == 3:
        apply(a[1], a[2])
    else:
        print(__doc__)
        sys.exit(2)
