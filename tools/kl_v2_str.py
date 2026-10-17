#!/usr/bin/env python3
"""
The stream file for the two V2 campaign maps (2026-10-17): DM06B 'A Walk in the Park II' (Dead Men M06_A under F07,
tools/kl_fa_v2_park.py) and DM01B 'Hot Coffee II' (M01_A under F07, tools/kl_fa_v2_hotcoffee.py). Their builds say
'sound: N stream clips are not in the merged stream file (kl_audio.merge)': the music / ambience beds of the campaign levels
have no block in any PC_Def.str of the chain, so kl_snd.merge dropped the wave objects (the sound stays, without a wave = silent).

A DRIVER like tools/kl_club_str.py (same method: tools/kl_str.py merge(), base = the chain's newest file and its .map.json as
`prior`, every old byte / clip / map entry stays where it was, appended blocks are Dead Men's bytes). Nothing here starts the game
or writes into the game folder; `put` (kl_vault_str's) is for the session that holds the game.

    python kl_v2_str.py need                          the clips: Dead Men block, bytes, form (from M06_A's and M01_A's .WHD)
    python kl_v2_str.py build <base.str> <out.str>    out = base + those blocks (+ <out>.map.json, the base's .bain.json carried), then `proof`
                                                      base = the chain's newest file (C:/kl_build/v_club/PC_Def.str), READ ONLY
    python kl_v2_str.py proof <base.str> <out.str>    kl_vault_str's five statements
    python kl_v2_str.py whd <out.str> <level> <folder>   <level> = M06_A | M01_A: the bank of a build against <out>: every streamed record
                                                      resolves into <out>, the level's clips have their record there and it is the clip

THE CLIPS (names as the level's Dead Men .WHD has them; MEASURED by re-reading the builds' own lost list, see re/campaign_v2_plan.md)
  M06_A  'RetoMotoAction_Layer1_Main_Loop / Layer2_Bass_Loop / Layer3_Intense_Loop' (ONE interleaved block, Dead Men 920408064)
         and 'SFX/Ambiences/M07_A/Outside/Construction_Site_01.wav' (M06_A's WHD carries a M07_A ambience)
  M01_A  'SFX/Ambiences/M01_A/Inside/Garage.wav', 'SFX/Ambiences/M01_A/Outside/Street_Alley_Muffled_01.wav'
         (the two the hot coffee build lists; its propane clips and 80 guard lines already have records in the chain)
The M01_A music tracks (M01_Bustout_*, M01_Prison_Ambient, BustoutIntenseClimax_GUITARS) are in the level's .WHD but no wave of the
FA build uses them (GUESS: the build lists none as lost); they are NOT merged.
NOTHING written by this file has run in the game.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_str, kl_vault_str as V

SETS = {
    'M06_A': tuple('Music/InHouse/M06/RetoMotoAction_Layer%s.wav' % n for n in ('1_Main_Loop', '2_Bass_Loop', '3_Intense_Loop'))
             + ('SFX/Ambiences/M07_A/Outside/Construction_Site_01.wav',),
    'M01_A': ('SFX/Ambiences/M01_A/Inside/Garage.wav', 'SFX/Ambiences/M01_A/Outside/Street_Alley_Muffled_01.wav'),
}


def need(log=None):
    """{level: {Dead Men block offset: [.WHD names]}} (kl_vault_str.need per level; each interleaved group whole)."""
    out = {}
    for lvl, names in SETS.items():
        V.LEVEL = lvl
        out[lvl] = V.need(names)
    return out


def merged_want(per):
    want = {}
    for lvl, w in per.items():
        for o, names in w.items():
            want.setdefault(o, [])
            want[o] += [n for n in names if n not in want[o]]
    return want


def show_need(log=print):
    per = need()
    dm = kl_str.Stream(kl_str.paths()['dm'])
    total, seen = 0, set()
    for lvl, w in per.items():
        log('%s:' % lvl)
        for o in sorted(w):
            n = dm.copy_length(o)
            if o not in seen:
                total += n
                seen.add(o)
            log('  Dead Men %#11x  %9d bytes  %s%s' % (o, n, 'LIP + ' if dm.has_lip(o) else '', ' | '.join(
                '%s %d Hz %d ch %.1f s layer %d  %s' % (kl_str.CODEC.get(c.codec, c.codec), c.rate, c.channels, c.samples / max(1, c.rate), c.layer, c.name)
                for c in dm.blocks[o])))
    log('%d blocks, %d bytes (%.2f MB)' % (len(seen), total, total / 2.0 ** 20))
    dm.close()
    return per


def build(base_path, out_path, log=print):
    """out = base + need()'s blocks by kl_str.merge (prior = the base's map), the .bain.json carried. -> [problems]"""
    import shutil
    P = kl_str.paths()
    out_abs = os.path.abspath(out_path).lower().replace(V.BS, '/')
    for banned in ('/kl_portbackup/', '/build/v_bain/over_talk/', '/build/w_tab', '/build/v_vault/', '/kl_build/v_club/'):
        if banned in out_abs:
            raise ValueError('kl_v2_str: %s is not a place this tool writes to' % out_path)
    if out_abs in (os.path.abspath(p).lower().replace(V.BS, '/') for p in (P['merged'], P['installed'], P['stock'], base_path)):
        raise ValueError('kl_v2_str: the output is one of the files that must stay')
    prior = kl_str.load_map(base_path + '.map.json')
    log('the clips:')
    per = show_need(log)
    want = merged_want(per)
    have = sorted(o for o in want if o in prior)
    if have:
        log('  %d of the blocks are in the base already (not copied again)' % len(have))
    res = kl_str.merge(base_path, P['dm'], want, out_path, prior, log)
    if os.path.isfile(base_path + '.bain.json'):
        shutil.copyfile(base_path + '.bain.json', out_path + '.bain.json')
    log('  %d blocks added, %d index entries; %d names stand twice in the index' % (res['blocks_added'], len(res['added']), res['names_twice']))
    return V.proof(base_path, out_path, log)


def main(a):
    cmd = a[0] if a else ''
    if cmd == 'need':
        show_need()
        return 0
    if cmd == 'build' and len(a) == 3:
        return 1 if build(a[1], a[2]) else 0
    if cmd == 'whd' and len(a) == 4 and a[2] in SETS:
        V.LEVEL = a[2]
        return 1 if V.whd(a[1], a[3], names=SETS[a[2]]) else 0
    if cmd in ('proof', 'stamp', 'levels', 'installed', 'put'):
        return V.main(a)
    print(__doc__)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
