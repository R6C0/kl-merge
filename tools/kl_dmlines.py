#!/usr/bin/env python3
"""
Dead Men Fragile Alliance voice lines into an ALREADY BUILT Dog Days slot archive (re/bots_voice.md
1.1, 1.2; owner list 2026-10-17 items 11-13). No builder files needed: it reads the built archive,
its .WHD / .WAV beside it, grafts the lines the archive lacks (sound bank + .LOC leaves + the
K_C1..K_C9 variants), and writes the new archive, .WHD / .WAV and the KLTalk.ini variants.

    python kl_dmlines.py <map folder> <out folder> [--extra]

Lines (Dead Men's M01_FA_A bank; one voice per line, streamed PCM sets in Dead Men's PC_Def.str, which
kl_snd.merge maps into the merged stream file):
    Multiplayer/GameEnds/FA_AllDead                  'Got 'em all. Every last one of 'em - bunch of fucking amateurs.'
    Multiplayer/Shoot_Off_Money/FA_ShootOffMoney_01  'Drop the cash or I'll shoot!'
--extra adds the police-side families (GUESS: nothing says them yet; for e5's field repoints).

Outputs, in <out folder>: <slot>_Main.zip (only .SND and the nine .LOC members differ), .WHD, .WAV,
KLTalk.ini (UNCHANGED copy, or absent: safe with every installed hook), KLTalk.newhook.ini (the same
plus [Pool.n] On=Shoot / On=Won: needs the hook of the commit that added those words; an older hook
REFUSES a KLTalk.ini with an On word it does not know, and then says nothing on that level).
"""
import os, re, struct, sys, zipfile, collections, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_snd, kl_loc, kl_voice

SRC_LEVEL = 'M01_FA_A'
CORE = ['Multiplayer/GameEnds/FA_AllDead', 'Multiplayer/Shoot_Off_Money/FA_ShootOffMoney_01']
EXTRA = ['Multiplayer/GameEnds/FA_AllEscapedPolice', 'Multiplayer/GameEnds/FA_TimeOutPolice_01',
         'Multiplayer/GameEnds/FA_TimeOutPolice_02', 'Multiplayer/CallExitVehiclePolice/FA_CallExitVehiclePolice_01',
         'Multiplayer/CallExitVehiclePolice/FA_CallExitVehiclePolice_02', 'Multiplayer/PoliceReward/FA_PoliceReward_02']
POOLS = [('won', 'Won', CORE[0]), ('shoot', 'Shoot', CORE[1])]
WHO = ['Kane', 'Lynch', 'Any', 'Squad1', 'Squad2']


def slot_of(zf):
    for n in zf.namelist():
        if n.upper().endswith('_MAIN.SND'):
            return n[:-4], os.path.basename(n)[:-9]
    raise ValueError('no _Main.SND in the archive')


def pools_text(first):
    out, n = [], first
    for name, on, key in POOLS:
        for who in WHO:
            out += ['[Pool.%d]' % n, 'Name=dm_%s_%s' % (name, who.lower()), 'Who=%s' % who, 'On=%s' % on, 'Keys=1', 'Key.1=%s' % key]
            n += 1
    return out, n - 1


def ini_variant(old, count_of_pools_line=True):
    """old: bytes of the installed KLTalk.ini or None -> bytes of the new-hook variant."""
    if old is None:
        head = ['; written by tools/kl_dmlines.py - hook part kltalk, Shoot / Won pools only (Dead Men FA lines)',
                '[Talk]', 'Version=1', 'Map=DM', 'Kane=0', 'Lynch=0', 'StreamBytes=0',
                '[Chatter]', 'Gap=40,90', 'MemberGap=25', 'Quiet=8', 'EventChance=100', 'Once=1', 'Speakers=1']
        pl, _ = pools_text(1)
        return ('\r\n'.join(head + pl) + '\r\n').encode('latin1')
    t = old.decode('latin1')
    nums = [int(m) for m in re.findall(r'(?m)^\[Pool\.(\d+)\]', t)]
    first = max(nums or [0]) + 1
    if first + len(POOLS) * len(WHO) - 1 > 32:
        raise ValueError('KLK_NPOOL (32) would be exceeded: %d pools already' % (first - 1))
    pl, last = pools_text(first)
    nl = '\r\n' if '\r\n' in t else '\n'
    if not t.endswith('\n'):
        t += nl
    t = re.sub(r'(?m)^Pools=\d+', 'Pools=%d' % last, t)
    # a [Chatter] section the file lacks would leave the event chance at the hook default (50): fine
    return (t + nl.join(pl) + nl).encode('latin1')


def run(folder, out, extra=False, log=print):
    folder, out = os.path.abspath(folder), os.path.abspath(out)
    zp = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('_main.zip')][0]
    prefix = zp[:-4]
    sname = os.path.basename(zp)[:-4]                      # F07_Main
    os.makedirs(out, exist_ok=True)
    keys = CORE + (EXTRA if extra else [])
    with zipfile.ZipFile(zp) as zf:
        snd_name, _slot = slot_of(zf)
        snd = zf.read(snd_name + '.SND')
        locs = {lang: zf.read(n) for lang, n in kl_loc.members(zf).items()}
    whd, wav = kl_snd.read(prefix + '.WHD'), kl_snd.read(prefix + '.WAV')
    ls = kl_snd.read(prefix + '_LS.SND')
    base = kl_snd.Snd('dd', snd, ls).walk()           # walked WITH its loading-sound bank
    with zipfile.ZipFile(kl_snd.level_zip(SRC_LEVEL, 'dm')) as zf:
        m_loc = {lang: zf.read(n) for lang, n in kl_loc.members(zf).items()}
    have = {p.lower() for p, _k in kl_loc.leaves(kl_loc.parse(locs['English']))}
    src_leaves = {p.lower(): (p, k) for p, k in kl_loc.leaves(kl_loc.parse(m_loc['English']))}
    want, sids, missing = set(), {}, []
    for k in keys:
        if k.lower() not in src_leaves:
            missing.append(k); continue
        if k.lower() in have:
            continue
        p, leaf = src_leaves[k.lower()]
        want.add(p); sids[p] = kl_loc.fields(leaf)[2] or 0
    info = {'map': os.path.basename(folder), 'archive': sname, 'missing in Dead Men': missing, 'grafted': sorted(want)}
    if not want:
        log('%s: nothing to add (%s)' % (info['map'], 'all present' if not missing else 'missing in source: %s' % missing))
        return info
    src = kl_snd.bank(SRC_LEVEL, 'dm')
    st = collections.Counter()
    roots = {v for v in sids.values() if v}
    nsnd, nwhd, nwav, omap = kl_snd.merge(base, src, whd, wav, kl_snd.read(kl_snd.beside(SRC_LEVEL, '.WHD', 'dm')),
                                          kl_snd.read(kl_snd.beside(SRC_LEVEL, '.WAV', 'dm')), roots, log=log, stats=st,
                                          inmem=kl_voice.stream_clip)
    files, n = kl_loc.graft_level(locs, m_loc, lambda p: p in want, omap, log)
    for lang, d in list(files.items()):                     # K_C1..K_C9 for the Any pools (Dead Men recorded one voice)
        t = kl_loc.parse(d)
        if t is not None:
            kl_loc.aliases(t, want, 9)
            files[lang] = kl_loc.build(t)
    nls = kl_snd.ls_bank(ls, kl_snd.u32(nsnd, 0))
    problems, cnt = kl_snd.verify(base, nsnd, nwhd, nwav, nls, omap)
    info.update(counts=dict(st + cnt), problems=problems, sound_ids_without_form=[p for p in want if not omap.get(sids[p])])
    # rewrite the archive: every member as it was except the .SND and the .LOC files
    newmem = {snd_name + '.SND': nsnd}
    newmem.update({m: files[lang] for lang, m in kl_loc.members(zipfile.ZipFile(zp)).items()})
    dst = os.path.join(out, sname + '.zip')
    with zipfile.ZipFile(zp) as zin, zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as zo:
        for zi in zin.infolist():
            data = newmem.get(zi.filename)
            if data is None:
                data = zin.read(zi.filename)
            ni = zipfile.ZipInfo(zi.filename, zi.date_time)
            ni.compress_type, ni.external_attr = zi.compress_type, zi.external_attr
            zo.writestr(ni, data)
    open(os.path.join(out, sname + '.WHD'), 'wb').write(nwhd)
    open(os.path.join(out, sname + '.WAV'), 'wb').write(nwav)
    open(os.path.join(out, sname + '_LS.SND'), 'wb').write(nls)
    ini = os.path.join(folder, 'KLTalk.ini')
    old = open(ini, 'rb').read() if os.path.isfile(ini) else None
    have_wardrobe = os.path.isfile(os.path.join(folder, 'KLWardrobe.ini'))
    if old is not None:
        shutil.copyfile(ini, os.path.join(out, 'KLTalk.ini'))
    if have_wardrobe or old is not None:
        open(os.path.join(out, 'KLTalk.newhook.ini'), 'wb').write(ini_variant(old))
    log('%s: %d keys grafted, problems %s' % (info['map'], len(want), problems or 'none'))
    return info


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if len(a) != 2:
        print(__doc__); sys.exit(2)
    run(a[0], a[1], '--extra' in sys.argv)
