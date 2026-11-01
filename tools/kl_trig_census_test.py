"""
kl_trig_census_test.py - self-test of tools/kl_trig_census.py on SYNTHETIC boxes (no game files).

    python tools/kl_trig_census_test.py          -> RESULT: PASS / FAIL
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_trig_census as T

FAILS = []


def check(cond, what):
    if not cond:
        FAILS.append(what)
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))


class Sc:
    def __init__(self, paths):
        self.path = ['ROOT'] + paths


R = 'ROOT\\'
PATHS = [
    R + 'Triggers!Start_Heist',                    # 1 cop wave box, bot-eligible
    R + 'Triggers!DoorBox',                         # 2 door box, team-2 flag set
    R + 'Triggers!LeaveBox',                        # 3 on-leave
    R + 'Triggers!HumanOnly',                       # 4 ECPS human only
    R + 'FA!PC0402_M02_Cashdrawer_01',              # 5 TB2 pick-up
    R + 'Civilians!Waitress\\Fat_Waitress_01',      # 6 TB2 npc/civ self target
    R + 'Triggers!GarageBox2',                      # 7 TB2 door, players only
    R + 'Triggers!Everyone',                        # 8 TB2 every object
    R + 'Triggers!PoliceSwats_01_Trigger',          # 9 online box
]


def tb(enabled=1, enter=1, count=1, left=0, team2=0, rearm=0xffffffff, tracked=None, ecps='ECPS_BOTH', local=0, efamps='EFAMPS_ALL_MODES', targets=()):
    return [enabled, enter, count, left, 0, 0, team2, 0, 0, 0, rearm, '', tracked or [], 'eTGS_AllInside', ecps, local, efamps, list(targets)]


CTRLS = {
    'TriggerBox': [
        (1, 0, tb(targets=[R + 'AI_Enemies!Squad_A\\SquadModifier'])),
        (2, 0, tb(team2=1, targets=[R + 'Doors!Leaf_01\\Open'])),
        (3, 0, tb(left=1, targets=[R + 'Timer!T'])),
        (4, 0, tb(ecps='ECPS_LYNCHONLY', targets=[R + 'AI_Enemies!Squad_B'])),
    ],
    'TriggerBox2': [
        (5, 0, [[R + 'FA!PC0402_M02_Cashdrawer_01'], 1, 90.0, 1, 0, 'AI_TRIGGER_WITH_ACTIVATOR', 0]),
        (6, 0, [[R + 'Civilians!Waitress\\Fat_Waitress_01'], 1, 90.0, 1, 0, 'X', 0]),
        (7, 0, [[R + 'Garage!Door_01'], 1, 90.0, 1, 0, 'X', 0]),
        (8, 0, [[R + 'Garage!Door_02'], 1, 90.0, 0, 0, 'X', 0]),
    ],
    'OnlineTriggerBox': [
        (9, 0, [[R + 'AIEnemies!PoliceSwats\\PoliceSquad_01'], 1, 0, 1, 'AITrigger', 4]),
    ],
}


def controllers(sc, name):
    return CTRLS.get(name, [])


def main():
    sc = Sc(PATHS)
    check(T.kind_of(R + 'DropMoney!TM_MoneyStack_001') == 'loot' and T.kind_of('PC0406_Watches_M4_02') == 'loot', 'kind: money stacks and watches are loot')
    check(T.kind_of('AI_Enemies!Squad_A\\HuntBehaviour') == 'cop' and T.kind_of('Doors!Leaf_01') == 'door' and T.kind_of('Timer!T') == 'script', 'kind: cop / door / script by keyword')
    check(T.level_kind(R + 'AI_Players!Enemies!X!TriggerBox_OpenExitElevator', [R + 'AI_Players!Enemies!AnimProxy_OpenEscapeElevator']) == 'door'
          and T.level_kind(R + 'AI_Players!Enemies!T_NearWindow', []) == 'script', 'kind: a parent group (AI_Players!Enemies!) is never matched, only the leaf names')
    bs = T.boxes(sc, controllers)
    check(len(bs) == 9, 'nine boxes read (%d)' % len(bs))
    by = {b['path']: b for b in bs}
    b1, b2, b3, b4 = (by[PATHS[i]] for i in range(4))
    check(b1['bot_eligible'] and b1['kind'] == 'cop' and b1['oneshot'] and not b1['gap'], 'TB 1: cop wave, eligible, one-shot, the hook covers it')
    check(b2['team2_flag'] and b2['kind'] == 'door', 'TB 2: team-2 flag set (the game reaches a bot by itself)')
    check(b3['gap'] == 'left', 'TB 3: on-leave action = a hook gap')
    check(not b4['bot_eligible'], 'TB 4: ECPS_LYNCHONLY is not eligible for a bot')
    check(by[PATHS[4]]['kind'] == 'loot' and by[PATHS[5]]['kind'] == 'civ', 'TB2: cash drawer = loot, waitress = civ')
    check(by[PATHS[6]]['players_only'] and by[PATHS[6]]['kind'] == 'door' and not by[PATHS[7]]['players_only'], 'TB2: players-only flag from field 3')
    check(by[PATHS[8]]['players_only'] and by[PATHS[8]]['kind'] == 'cop', 'OnlineTB: players-only (GUESS field 1), cop by name')
    s = T.summarize(bs)
    check(s['TriggerBox'][('cop', 'missed')] == 1 and s['TriggerBox'][('door', 'ok')] == 1 and s['TriggerBox'][('gap', 'left')] == 1, 'summary TB: cop missed, door ok (team flag), gap left')
    check(s['TriggerBox2'][('door', 'missed')] == 1 and s['TriggerBox2'][('loot', 'missed')] == 1, 'summary TB2: door missed, loot missed (ignored in Needs)')
    row = T.row_of('DMx', 'F01', bs)
    check(len(row) == 9, 'row has the column count')
    check(row[2] == '4' and row[3].startswith('2 (') and row[4].startswith('1 (') and row[6] == '1 (1)', 'row: TB 4, TB missed 2 (cop + left), TB2 1, OnlineTB 1 (1) (%s)' % row)
    check('OnlineTriggers=1' in row[7] and 'OnlineTriggersExtra=1' in row[7] and row[8] == 'left 1', 'row: needs both keys; gap left 1')
    g = T.boxes(Sc([PATHS[0]]), lambda sc, name: [(1, 0, tb(count=9, targets=[R + 'AI_Enemies!Squad_A']))] if name == 'TriggerBox' else [])
    check(g[0]['gap'] == 'count' and T.row_of('DMg', 'F01', g)[8] == 'count 1', 'a count outside 1..8 is a printed hook gap')
    row0 = T.row_of('DMy', 'F02', [])
    check(row0[7] == 'none', 'an empty level needs nothing')
    check(T.main(['--root', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'no_such_root'), '--maps', 'DM01']) == 1, 'main: exit 1 when no level could be read')
    print('RESULT: %s' % ('FAIL (%d)' % len(FAILS) if FAILS else 'PASS'))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
