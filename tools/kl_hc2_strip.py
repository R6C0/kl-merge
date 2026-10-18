"""kl_hc2_strip.py - OPT-IN post-pass for 'Hot Coffee II' (DM01B, slot F03). Reads a BUILT F03_Main.zip, writes a copy with the
campaign's leftover damage sources neutralised IN THE DATA. Does nothing unless run; no builder imports it. Written 2026-10-19
(re/hotcoffee2_campaign_leftovers.md has the findings behind it).

WHY: crew bots die from ONE 340 hp drop at five spots (A (2102,27058) B (4383,23956) C (2863,25994) D (5254,23937) E (3015,25950)).
Gunfire, PointBlankToCrew, the van and the human are refuted (re/hotcoffee2_oneshot.md). Measured on the live zip ea8cbc82:
  CARS  every one of the five spots has a campaign car (VehicleEffects controller) 1.5 .. 3.5 m away: A 3.1 m (Police_a_00#14),
        B 3.5 m (JPN_Civilian_a_00#01), C 3.4 m (Police_a_00#09), D 1.5 m (JPN_Civilian_a_00), E 2.4 m (Police_a_00#09).
        45 of the 46 cars in the level carry BlowupChanceDefinite; their field 3/4 are 600..1000 / 1000 where Dog Days' own car
        (F03's one) has 8000 / 9000: the campaign cars are ~10x more fragile and blow up for sure. A car explosion beside a bot is
        a blast hit (kind 9) of the size seen (GUESS: field names; the enum BlowupChance* is certain).
  SNIPERS  06_Squad_LeftSniper / RightSniper (two ZFFActor 'Ground', ZSoldier eArmy) start on the LevelSpeak box (4500,100,24250),
        the left one stands at (-3553,27030): the same z as site A, 56 m off. Their ZSoldier vector is the ordinary army one, the
        weapon is stock Rifle_Type88_S; a one-shot is NOT proven (GUESS).
WHAT IT CHANGES (nothing is removed; no entity added/removed, .gms/.buf/.oct untouched, only the .prp member differs):
  cars     VehicleEffects field 23 (enum BlowupChance*) BlowupChanceDefinite -> BlowupChanceNone, on every car of the level
           (--radius N: only cars within N units of one of the five spots). The car still takes damage and can burn (GUESS).
  snipers  the entries 'AI_Players!Enemies!06_DonutShop!06_Squad_{Left,Right}Sniper\\008_Defend' are dropped from the target list
           (field 17) of Specials!LevelSpeak!TriggerBox, so the box no longer starts them.
NOT touched: SM_SetHPToOne (eVM_OneHP) - it only applies to its own police squad (makes police weaker, helps the crew).
Usage (from tools/):  python kl_hc2_strip.py <in F03_Main.zip> <out F03_Main.zip> [--no-cars] [--no-snipers] [--radius N] [--list]
"""
import os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_graft, kl_scene, kl_map_ai as MA
import kl_fa_bank as BK
from kl_prp import units

SITES = {'A': (2102, 27058), 'B': (4383, 23956), 'C': (2863, 25994), 'D': (5254, 23937), 'E': (3015, 25950)}
BLOW_FIELD = 23                       # VehicleEffects: enum BlowupChance* (CERTAIN: BlowupChanceDefinite / None are its values)
SNIPER_TAGS = ('06_squad_leftsniper\\008_defend', '06_squad_rightsniper\\008_defend')
SPEAK_BOX = 'Specials!LevelSpeak!TriggerBox'
SPEAK_LIST = 17                       # TriggerBox: the target list that holds the squads the box starts


def _positions(zf):
    s = kl_scene.read(zf)
    out = [None]
    for e in s.entities():
        out.append(BK.world_of(e)[0])
    return out


def _ctrls(sc, k, name):
    return [i for i, (nm, b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == name]


def strip(src, dst, cars=True, snipers=True, radius=None, log=print):
    zf = zipfile.ZipFile(src)
    sc, _, _ = kl_fa.load(src)
    pos = _positions(zf) if radius else None
    changed = {'cars': [], 'snipers': []}
    for k in range(1, len(sc.nodes)):
        if cars:
            for ci in _ctrls(sc, k, 'VehicleEffects'):
                us = [list(u) for u in units(sc.nodes[k]['ctrls'][ci][1][1:-1])]
                if kl_fa.value(sc, us[BLOW_FIELD]) != 'BlowupChanceDefinite':
                    continue
                if radius:
                    p = pos[k]
                    near = min(((p[0] - x) ** 2 + (p[2] - z) ** 2) ** .5 for x, z in SITES.values())
                    if near > radius:
                        continue
                kl_fa.edit(sc, k, ci, lambda f: MA.setv(sc, f, BLOW_FIELD, 'BlowupChanceNone'))
                changed['cars'].append(sc.path[k])
        if snipers and sc.path[k].endswith(SPEAK_BOX):
            for ci in _ctrls(sc, k, 'TriggerBox'):
                us = [list(u) for u in units(sc.nodes[k]['ctrls'][ci][1][1:-1])]
                lst = kl_fa.value(sc, us[SPEAK_LIST])
                keep = [p for p in lst if not any(p.lower().endswith(t) for t in SNIPER_TAGS)]
                if len(keep) != len(lst):
                    kl_fa.edit(sc, k, ci, lambda f: MA.setv(sc, f, SPEAK_LIST, keep))
                    changed['snipers'] += [p for p in lst if p not in keep]
    members = []
    pn = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
    for n in zf.namelist():
        members.append((n, sc.p.serialize() if n == pn else zf.read(n)))
    kl_graft.write_zip(dst, members, kl_graft.load_options('level=9'))   # the live zip is level 9 (198 MB; level 1 gives 234 MB)
    log('kl_hc2_strip: %d cars -> BlowupChanceNone, %d sniper start entries dropped -> %s'
        % (len(changed['cars']), len(changed['snipers']), dst))
    return changed


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return 2
    src, dst = a[0], a[1]
    radius = int(a[a.index('--radius') + 1]) if '--radius' in a else None
    ch = strip(src, dst, cars='--no-cars' not in a, snipers='--no-snipers' not in a, radius=radius)
    if '--list' in a:
        for k, v in ch.items():
            for p in v:
                print(k, p)
    return 0


if __name__ == '__main__':
    sys.exit(main())
