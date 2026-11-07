#!/usr/bin/env python3
"""pd2_pick_template_test.py - pure checks of pd2_guns_multi's template picker (candidates / pick_template / check_override) on FAKE equipment rows.
No level, no game files. Run: python tools/pd2_pick_template_test.py"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pd2_guns_multi as M

fails = 0


def check(cond, what):
    global fails
    if not cond:
        fails += 1
        print('FAIL', what)


def row(name, wt, itemno, folder='x'):
    return dict(name=name, wt=wt, itemno=itemno, folder=folder)


MG = 'WT_MACHINEGUN'
ROWS = [
    row('MG_Shop', MG, 20),                                  # a shop item: never offered
    row('MG_Heli', MG, 42), row('MG_Hind', MG, 43), row('MG_Player', MG, 44),        # heli / hind / player: never offered
    row('MG_Plain', MG, 40), row('MG_L09_NPC', MG, 41),
    row('MG_NoFolder', MG, 45, folder=''),
    row('Rifle_Plain', 'WT_RIFLE', 33), row('Rifle_T95', 'WT_RIFLETYPE95', 38), row('Rifle_L10_NPC', 'WT_RIFLETYPE88', 35),
    row('HG_Plain', 'WT_PISTOL', 52), row('HG_Shield', 'WT_PISTOL', 62), row('HG_Human_Shield_L09', 'WT_PISTOL', 63),
    row('Rev', 'WT_REVOLVER', 54),
    row('Rpg', 'WT_ROCKETLAUNCHER', 50),
]
mg = dict(key='T', kind='light machine gun')
rifle = dict(key='R', kind='assault rifle')
pistol = dict(key='P', kind='pistol')

# class of a spec
check(M.spec_class(mg) == 'mg' and M.spec_class(rifle) == 'rifle' and M.spec_class(pistol) == 'pistol', 'class of kind')
check(M.spec_class(dict(kind='pistol', cls='rocket')) == 'rocket', 'explicit cls wins')
# every spec of the real table has a class and a WT set
check(all(M.spec_class(s) in M.CLASS_WT for s in M.SPECS), 'every SPEC has a known class')
# tiers
check(M.tier_of('MG_Plain', 'mg') == 0 and M.tier_of('MG_L09_NPC', 'mg') == 1, 'plain < _Lnn_NPC')
check(M.tier_of('HG_M-77B_Human_Shield', 'pistol') == 2 and M.tier_of('HG_M-77B_Human_Shield', 'mg') is None, 'human shield only for pistols')
check(all(M.tier_of(t, 'mg') is None for t in ('MG_L09_Heli', 'RPG_7V_Hind', 'MG_L09_Heli_Player', 'x_HELI', 'y_PLAYER')), 'heli / hind / player never')
# candidates
c = M.candidates(mg, ROWS)
check(c == ['MG_Plain', 'MG_L09_NPC'], 'mg candidates, best tier first: %r' % c)
check(M.candidates(mg, ROWS, taken=['mg_plain']) == ['MG_L09_NPC'], 'a taken template (any case) is skipped')
check(M.candidates(dict(mg, item=41), ROWS) == ['MG_L09_NPC'], 'a spec with an item takes only that item')
c = M.candidates(rifle, ROWS)
check(c == ['Rifle_Plain', 'Rifle_T95', 'Rifle_L10_NPC'], 'rifle class = RIFLE + RIFLETYPE95 + RIFLETYPE88, tiers first: %r' % c)
c = M.candidates(pistol, ROWS)
check(c == ['HG_Plain', 'HG_Shield', 'HG_Human_Shield_L09'], 'pistol: plain first, the human shield variant last: %r' % c)
check('Rev' not in c, 'a revolver is not a pistol class')
check(M.candidates(dict(kind='sniper rifle', key='S'), ROWS) == [], 'no sniper rows = no candidates')
# pick_template: first by tier without a cost function, cheapest under the threshold with one
t, note, tried = M.pick_template(None, mg, eq={r['name']: r for r in ROWS}, log=lambda s: None)
check(t == 'MG_Plain' and tried[0][0] == 'MG_Plain', 'no cost function: the first (best tier) wins: %r' % (t,))
cost = {'MG_Plain': 2.5, 'MG_L09_NPC': 1.4}
t, note, tried = M.pick_template(None, mg, cost_fn=lambda sp, tpl: cost[tpl], eq={r['name']: r for r in ROWS}, log=lambda s: None)
check(t == 'MG_L09_NPC' and len(tried) == 2, 'the cheapest under 2.1 wins, an over-threshold plain one loses')
cost = {'MG_Plain': 1.5, 'MG_L09_NPC': 1.5}
t, _n, _t = M.pick_template(None, mg, cost_fn=lambda sp, tpl: cost[tpl], eq={r['name']: r for r in ROWS}, log=lambda s: None)
check(t == 'MG_Plain', 'a tie goes to the better tier')
cost = {'MG_Plain': 3.0, 'MG_L09_NPC': 2.2}
t, note, _t = M.pick_template(None, mg, cost_fn=lambda sp, tpl: cost[tpl], eq={r['name']: r for r in ROWS}, log=lambda s: None)
check(t is None and note == 'skipped: no mg template', 'nothing fits: None and the report note: %r' % note)
t, note, _t = M.pick_template(None, dict(kind='sniper rifle', key='S'), eq={r['name']: r for r in ROWS}, log=lambda s: None)
check(t is None and note == 'skipped: no sniper template', 'no candidate at all: skipped note')
t, note, _t = M.pick_template(None, mg, cost_fn=lambda sp, tpl: None, eq={r['name']: r for r in ROWS}, log=lambda s: None)
check(t is None, 'an unfittable template (cost None) is not picked')
# a heli template is never picked even when it is the only one of the class
only = {r['name']: r for r in ROWS if r['name'] in ('MG_Heli', 'MG_Hind', 'MG_Player')}
t, note, _t = M.pick_template(None, mg, eq=only, log=lambda s: None)
check(t is None and note == 'skipped: no mg template', 'heli / hind / player rows only: skipped')
# the pinned-override refusal
for tpl in ('MG_GP_Type88_L09_Heli', 'RPG_7V_Hind', 'MG_GP_Type88_L09_Heli_Player', 'x_heli'):
    try:
        M.check_override(dict(key='X', template=tpl)); check(False, 'override %s refused' % tpl)
    except ValueError:
        pass
check(M.check_override(dict(key='X', template='MG_GP_Type88_L09_Heli', allow_heli=True)) == 'MG_GP_Type88_L09_Heli', 'allow_heli=True lets a heli template through')
check(M.check_override(dict(key='X', template='MG_GP_Type88')) == 'MG_GP_Type88' and M.check_override(dict(key='X')) is None, 'a plain pin and no pin pass')
# the real table: only the legacy specs pin a heli template, each says allow_heli, and no NEW spec does
for s in M.SPECS:
    heli = bool(M.HELI_RE.search(s['template']))
    check(heli == bool(s.get('allow_heli')), '%s: allow_heli matches its template' % s['key'])
    check(not heli or s['key'] in M.LEGACY_HELI, '%s: a heli pin is a legacy spec' % s['key'])
    try:
        M.check_override(s)
    except ValueError:
        check(False, '%s: its own pin is refused' % s['key'])
new = {s['key']: s for s in M.SPECS}
check(new['MG42_41']['template'] == 'MG_GP_Type88_L09_NPC' and new['MG42_41']['item'] == 41, 'MG42 on item 41 / the NPC MG')
check(new['AKM33']['max_cost'] == M.FIT_MAX and new['AKM33']['skip_if_akm'], 'AKM33 is cost-gated and skipped where an AKM is baked')
print('pd2_pick_template_test: %d failed' % fails)
sys.exit(1 if fails else 0)
