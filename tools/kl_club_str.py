#!/usr/bin/env python3
"""
The stream file for LAST CALL (kl_fa_club.py: Dead Men M05_A under F07): the stream file The Vault needs (tools/kl_vault_str.py:
the installed file + the Vault's sixteen clips) + the clips the club's sound lacks in it (re/club_campaign.md D6 and
'Fix after runs C0-C2'). A DRIVER, like kl_vault_str.py, whose functions it calls with the club's level and clip list: the
writing is tools/kl_str.py's merge(), the base is the Vault's file and its .map.json as `prior`. Nothing here starts the game; only
`put` (kl_vault_str's) writes into the game folder, and that is for the session that holds the game.

    python kl_club_str.py need                          the club's clips: Dead Men block, bytes, form (from M05_A's .WHD)
    python kl_club_str.py build <base.str> <out.str>    out = base + those blocks (+ <out>.map.json extended, the base's .bain.json
                                                        carried), then `proof`; exit 1 on a problem. base = the Vault's file
                                                        (<work>/build/v_vault/PC_Def.str, 1,753,469,945 bytes), READ ONLY
    python kl_club_str.py proof <base.str> <out.str>    the five statements of kl_vault_str.py (every old byte, clip and map
                                                        entry is where it was; every appended block is Dead Men's)
    python kl_club_str.py whd <out.str> <folder> [--no-ai]   the bank of a build of the club: every streamed record resolves into
                                                        <out>; the club's clips have their record and the index entry there is the clip
    python kl_club_str.py tab <base.str> <out.str> <folder> ...   built maps (the Vault's, the club's): every streamed record names a
                                                        block of <out> that <base> has at the same place with the same clips
    python kl_club_str.py levels <out.str> [level ...]  kl_str.check_levels on <out>
    python kl_club_str.py stamp <out.str> <folder> ...  <folder>/stream.json
    python kl_club_str.py installed|put ...             kl_vault_str's, unchanged (the install side is the same file mechanics)

THE CLIPS (names as M05_A's .WHD has them; the music is two INTERLEAVED four-layer sets, each ONE block that must come whole)
  music     'M05_A_Club_Layers' (Clean, Clean_3D, Muffled, Muffled_3D; 32.4 MB) and 'M05_A_Club_2_Layers' (2_Clean, 2_Clean_3D,
            2_Muffled and 2_Muffled_3D, the last named by no object of the level: it comes with its block; 49.5 MB)
  ambience  five beds (club entrance, the club, Yoko's office, the rooftop, the street)
The same GUESS / ASSUMED notes as kl_vault_str.py. NOTHING written by this file has run in the game.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_str, kl_vault_str as V

V.LEVEL = 'M05_A'                       # kl_vault_str.source() reads this module global at the call
MUSIC = tuple('Music/InHouse/Japan/M05_A/M05_A_Club_%s.wav' % n for n in ('Clean', 'Clean_3D', 'Muffled', 'Muffled_3D',
                                                                         '2_Clean', '2_Clean_3D', '2_Muffled', '2_Muffled_3D'))
AMBIENCE = ('SFX/Ambiences/M05_A/Inside/Club_Entrance_Ambience.wav', 'SFX/Ambiences/M05_A/Inside/M05_Club_Ambience_01.wav',
            'SFX/Ambiences/M05_A/Inside/Yoko_Office_Ambience.wav', 'SFX/Ambiences/M05_A/Outside/Roftop/Ambience_Rooftop_M05_A.wav',
            'SFX/Ambiences/M05_A/Outside/Street/Street_01.wav')
CLIPS = MUSIC + AMBIENCE


def show_need(log=print):
    want = V.need(CLIPS)
    dm = kl_str.Stream(kl_str.paths()['dm'])
    total = 0
    for o in sorted(want):
        n = dm.copy_length(o)
        total += n
        log('  Dead Men %#11x  %9d bytes  %s%s' % (o, n, 'LIP + ' if dm.has_lip(o) else '', ' | '.join(
            '%s %d Hz %d ch %.1f s layer %d  %s' % (kl_str.CODEC.get(c.codec, c.codec), c.rate, c.channels, c.samples / max(1, c.rate), c.layer, c.name)
            for c in dm.blocks[o])))
        for n in want[o]:
            log('      .WHD name  %s' % n)
    log('%d blocks, %d .WHD names, %d bytes (%.2f MB)' % (len(want), sum(len(v) for v in want.values()), total, total / 2.0 ** 20))
    dm.close()
    return want


def build(base_path, out_path, log=print):
    """out = base + need()'s blocks by kl_str.merge (prior = the base's map), the .bain.json carried. -> [problems]"""
    import shutil
    P = kl_str.paths()
    out_abs = os.path.abspath(out_path).lower().replace(V.BS, '/')
    for banned in ('/kl_portbackup/', '/build/v_bain/over_talk/', '/build/w_tab', '/build/v_vault/'):
        if banned in out_abs:
            raise ValueError('kl_club_str: %s is not a place this tool writes to' % out_path)
    if out_abs in (os.path.abspath(p).lower().replace(V.BS, '/') for p in (P['merged'], P['installed'], P['stock'], base_path)):
        raise ValueError('kl_club_str: the output is one of the files that must stay')
    prior = kl_str.load_map(base_path + '.map.json')
    log('the clips:')
    want = show_need(log)
    have = sorted(o for o in want if o in prior)
    if have:
        log('  %d of the blocks are in the base already (not copied again)' % len(have))
    res = kl_str.merge(base_path, P['dm'], want, out_path, prior, log)
    if os.path.isfile(base_path + '.bain.json'):
        shutil.copyfile(base_path + '.bain.json', out_path + '.bain.json')
    log('  %d blocks added, %d index entries; %d names stand twice in the index (kl_str.merge: a Dead Men name that is a Dog Days name too)' % (
        res['blocks_added'], len(res['added']), res['names_twice']))
    return V.proof(base_path, out_path, log)


def tab(base_path, out_path, folders, log=print):
    """kl_vault_str.tab's test, with the club's own news allowed: every streamed PC_Def.str record of every folder names a block of <out>; a block
    that is not the base's must be one of the NEW blocks of <out> (the club's seven) and only the club's folders may name one. -> [problems]"""
    b, m = kl_str.Stream(base_path), kl_str.Stream(out_path)
    new = {o for o in m.blocks if o not in b.blocks}
    bad = []
    for folder in folders:
        _recs, st = V._streamed(V._whd_of(folder))
        miss = [o for _a, _f, o in st if o not in m.blocks]
        other = [o for _a, _f, o in st if o in m.blocks and (o not in b.blocks or [(c.name, c.size, c.fmt, c.layer) for c in b.blocks[o]]
                                                              != [(c.name, c.size, c.fmt, c.layer) for c in m.blocks[o]])]
        over = [o for _a, f, o in st if o in m.blocks and not f['fmt'] >> 24 and f['size'] > m.audio(o)]
        news = [o for o in other if o in new]
        log('%s: %d streamed PC_Def.str records on %d blocks: %d name no block of the new file, %d a block that is not the base\'s (%d of them new blocks of %s), %d larger than their block' % (
            folder, len(st), len({o for _a, _f, o in st}), len(miss), len(other), len(news), os.path.basename(out_path), len(over)))
        club = os.path.basename(os.path.dirname(os.path.abspath(folder + os.sep))) .startswith('c_club') or 'club' in os.path.basename(folder)
        if miss or over or [o for o in other if o not in new] or (news and not club):
            bad.append('%s: %d / %d / %d stream records do not resolve as before' % (folder, len(miss), len(other) - len(news), len(over)))
    b.close(); m.close()
    log('TAB: %s' % ('PASS' if not bad else 'FAIL'))
    return bad


def main(a):
    cmd = a[0] if a else ''
    if cmd == 'need':
        show_need()
        return 0
    if cmd == 'build' and len(a) == 3:
        return 1 if build(a[1], a[2]) else 0
    if cmd == 'whd' and len(a) in (3, 4):
        # --no-ai: a build without enemies still names every music and ambience clip (the guards' lines are not clips of this list)
        return 1 if V.whd(a[1], a[2], names=CLIPS) else 0
    if cmd == 'tab' and len(a) >= 4:
        return 1 if tab(a[1], a[2], a[3:]) else 0
    if cmd in ('proof', 'stamp', 'levels', 'installed', 'put'):
        return V.main(a)
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
