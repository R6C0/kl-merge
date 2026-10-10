#!/usr/bin/env python3
"""
The enemies of the four Dead Men Fragile Alliance maps under Dog Days: measured, compared with stock, and
made harder with what Retomoto got (owner, 2026-10-10, after Late Night Opening: 'the ai a bit too easy so just
probably take some logic from retomoto and put it in there and do the same fixes for the other maps').
Spec, the measurements and every table: re/map_ai.md.

    python kl_map_ai.py table <build folder | archive | stock level>   who is there: per squad people, soldier row
                                                                       (accuracy, health), weapons, what starts it
    python kl_map_ai.py stock                                           the nine stock Fragile Alliance levels in one
                                                                       table (people, hit points, accuracy, waves)
    python kl_map_ai.py apply <build folder> <out folder> [options]     the step: a FINISHED build (kl_maps ready)
                                                                       -> a copy with the AI changes. Only the .prp
                                                                       member of the archive changes
    python kl_map_ai.py check <before> <after>                          the before / after table of one map
    python kl_map_ai.py all <z_maps folder> <out folder> [M02 ...] [options]   apply + check + kl_maps.audit on M01 M02
                                                                       M03 M06 (or the ones named)
  options of apply / all (each switches one part off; default = everything on):
    --no-strength   (1) soldier rows and weapons by class stay as built
    --no-waves      (2) timers, counters, round-start list stay as built
    --no-chains     (3) no 'wiped out' lists (ZSquadScript field 8)
    --no-escape     (4) nothing is named when the escape vehicle is called
    --presets       (1) writes skill NAMES by class instead (NAMES: Retomoto's first table): LOWERS these maps'
                        accuracy, see below - for a comparison run only
    --health=1.5    (1) the health floors times this (default 1.0 = stock's numbers)
    --car-exit      (0) the VehicleExitBehaviourRout the converter drops is put back (default: by-passed with
                        values only) - see 'part 0' in the code; code no stock level runs

WHAT THE SOLDIER ROW IS (read in kl2.exe, 2026-10-10; property = ZSoldier field, 0-based)
  ZSoldierRout slot 4 (0x846340) copies the properties into a block D at rout+0x34 and calls 0x46e410; slot 13
  (0x622ae0) makes the soldier (0x761900), which keeps D at soldier+0x6d8. Readers found by that pointer:
    3  ESkillLevel   0x46e410 switches on it: eN00b / eAmateur / eRegular / eVeteran / eElite OVERWRITE fields
                     4, 5, 6, 13, 14 with (20, 0, 20, 100, 40) / (35, 20, 10, 70, 45) / (50, 50, 10, 50, 50) /
                     (60, 60, 5, 20, 55) / (90, 90, 10, 0, 60); eCustom keeps the level's numbers. Then field 4 is
                     multiplied by 1.1 (No_Mercenary; table at 0xd19328) and fields 4 and 6 are clamped to 0..100.
                     Dead Men's exe has the same table (0x724060) on its fields 4, 5, 6, 9, 10: that PROVES the
                     converter's pairing Dog Days 13 / 14 <- Dead Men 9 / 10 (re/pairings.md had it by values only).
    4  accuracy      per cent: 0x557ae0 and 0x719b00 use (1 - field 4 / 100) as the miss share
    5  (aim)         two ranges of globals 0xd18fa4.. are read at field 5 per cent (0x5a85a0; meaning ASSUMED: how
                     fast the aim settles) and one of the tuning table (0x622b57)
    7  HEALTH        0x8fbac0: skipped with the 'GodActors' option or when <= 0 (invulnerable); else a range of
                     the tuning table at field 7 per cent, times a team factor, times field 9..12 chosen by the
                     difficulty [0x156b5f0] (0..3), handed to the actor (virtual +0x674 / +0x670)
    8                a second pair for the actor (virtual +0x67c), -1 = none; not read further
    9..12            health factor per difficulty (new in Dog Days; 1.0 everywhere)
    13, 14           two more tuning ranges (0x784330); lower 13 / higher 14 = more skilled by the preset table
    15               a number 0x7842f0 returns times a factor of the squad object (+0x5c8). ASSUMPTION: the sight
                     range (stock 5000, these maps 6000..10000) - but the AI heisters have 1.0 there
  So: Dog Days makes its police hard by NUMBERS and HEALTH (28..50 soldiers a level, SWAT 175, accuracy 50 -> 55),
  Dead Men made its few guards hard by ACCURACY (12..15 soldiers, accuracy 98..100 = better than eElite, health
  100). A skill name by weapon class (Retomoto's first table) or a stock row (kl_arms.ROWS, Retomoto's second: accuracy
  50) would LOWER every soldier of M01 / M02 / M03 (eCustom 98..100 -> 38..66). Here the class of the weapon sets
  FLOORS instead: nobody gets worse. Note for kl_arms.ROWS: stock's 'eArmy eRegular 85 82 82' row is NOT sharper than
  SWAT - the name eRegular writes 50, 50, 10 over those three numbers (accuracy as used 55, health 150).

THE FOUR PARTS (all values and reference lists of objects the build already has; no entity, no controller added)
  1 STRENGTH  the class of the weapon an actor carries gives floors for accuracy, aim and health; ARMS re-arms
              named squads (the police that arrive get rifles, as 137 of stock's Fragile Alliance police)
  2 WAVES     the map's own reinforcement timers / counters are shortened and started with the round
              (AIMonitor field 2, the stock way: F07 starts eight timers there), squads that only stand are
              unleashed
  3 CHAINS    ZSquadScript field 8 of a squad names routs of its neighbours and the map's reinforcement
              trigger: stock F03 chains its four SWAT reinforcements that way, in a ring. ASSUMPTION (Retomoto's,
              still not seen live): the list is sent when the squad is WIPED OUT
  4 ESCAPE    OnlineEscVehicleMonitor field 4 names every squad's hunt / flank rout and the reinforcements. Read
              in kl2.exe: ZOnlineExitLevelTrigger slot 34 calls 0x6276e0 with the number 1..4 of the vehicle it
              picked (its fields 2..5), and that function sends the monitor's list at +0x48 / +0x4c / +0x50 /
              +0x54 = fields 4..7. A Dead Men map has one vehicle, in field 2 -> field 4. No stock level fills
              these four lists (they use boxes on the way to the van): the loop is the one of the lists stock
              does fill, but it has NOT run with entries in any level.
Nothing of this has run in the game. GUESS = a number that is not read from a stock object or the exe.
"""
import collections, json, math, os, random, shutil, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_arms, kl_gms, kl_scene
import kl_prpjoin as J
from kl_prp import units

R = 'ROOT\\'
SLOT = 'F01'
TAGS = collections.OrderedDict([('M01', 'M01_FA_A'), ('M02', 'M02_FA_A'), ('M03', 'M03_FA_A'), ('M06', 'M06_FA_A')])
BUDGET = ('.prm', '.ANM', '.fxc', '.TEX')           # members read into one block each; + the .WAV beside the archive

# ------------------------------------------------------------------ the soldier row (module docstring)
STYLE, SKILL, ACC, AIM, F6, HEALTH, F8, F13, F14, SIGHT, MERC = 0, 3, 4, 5, 6, 7, 8, 13, 14, 15, 19
PRESET = {'eN00b': (20, 0, 20, 100, 40), 'eAmateur': (35, 20, 10, 70, 45), 'eRegular': (50, 50, 10, 50, 50),
          'eVeteran': (60, 60, 5, 20, 55), 'eElite': (90, 90, 10, 0, 60)}       # kl2 0x46e410: fields 4, 5, 6, 13, 14
PRESET_FIELDS = (ACC, AIM, F6, F13, F14)
ACC_FACTOR = 1.1                                    # kl2 0xd19328, for No_Mercenary (0xd19330 = 1.0 for the others)

# (1) class of the weapon carried -> (the skill name whose preset is the FLOOR for accuracy and aim, health floor).
# Retomoto's first table NAMED pistol eAmateur, SMG / shotgun eRegular, rifle / MG eVeteran, sniper eElite; here
# the same ladder stands one step higher and is a floor, because a name would write its preset over these maps'
# higher numbers. Health anchors READ from stock: 100 = the street cop, 175 = SWAT (eArmy eCustom, 138 of the
# nine levels' 316 soldiers), 65 = a guard; 125 / 150 / 200 between and above are GUESSES ('the higher the
# caliber the more advanced', owner on Retomoto). A floor never lowers a value: M01..M03's accuracy (98..100)
# stays, their health (100) is what rises; on M06 the riflemen's accuracy rises (82..96 -> 99).
STRENGTH = {'pistol': ('eRegular', 100), 'revolver': ('eRegular', 100), 'smg': ('eVeteran', 125), 'shotgun': ('eVeteran', 150),
            'rifle': ('eElite', 175), 'mg': ('eElite', 200), 'sniper': ('eElite', 100), 'rocket': ('eVeteran', 175)}
# '--presets': the skill NAMES Retomoto's first table gave by class (kl_arms.SKILL until 2026-10-10; kl_arms now
# writes whole stock rows on Retomoto, kl_arms.ROWS). A name's preset is written over the row: on these maps a loss
NAMES = {'pistol': 'eAmateur', 'revolver': 'eAmateur', 'smg': 'eRegular', 'shotgun': 'eRegular', 'rifle': 'eVeteran',
         'mg': 'eVeteran', 'sniper': 'eElite', 'rocket': 'eVeteran'}
HEALTH_SCALE = 1.0                                  # '--health=1.5': the health floors times this. These maps have a third
                                                    # of a stock level's soldiers; more health per man is the one way to
                                                    # more hit points without a new entity (bullet sponges: off by default)
OTHER = {'Rifle_zastavam85': 'rifle', 'Rifle_Type88': 'rifle', 'Rifle_Type95_C': 'rifle', 'SMG_SA61': 'smg', 'SMG_Type05_S': 'smg',
         'HG_DesertEagle': 'pistol', 'HG_M9Beretta_S': 'pistol', 'Shotgun_Hawk_SawnOff': 'shotgun'}    # stock NPC guns in no kl_arms pool
CLASS_OF = dict({t: c for c, pool in kl_arms.POOLS.items() for t, _w in pool}, **OTHER)

SQUAD_DEAD = 8                                      # ZSquadScript: the list sent when the squad is wiped out (ASSUMPTION;
                                                    # stock: 653 of the story levels' entries are 'all dead' counters)
MON_CALLED = 4                                      # OnlineEscVehicleMonitor: sent when the exit trigger calls its vehicle 1
START_LIST = 2                                      # AIMonitor: sent when the round starts (stock: timers)
BEHAVE = ('HuntBehaviourRout', 'FlankingBehaviourRout', 'DefendBehaviourRout', 'RunToCoverBehaviourRout', 'PatrolBehaviourRout',
          'VehicleMoveBehaviourRout', 'VehicleExitBehaviourRout', 'VehicleEnterBehaviourRout', 'HeliFlyBehaviourRout',
          'SquadModifierBehaviour', 'MiniCutsceneRout')


# ------------------------------------------------------------------ per map: the plan
# Every name is a scene path without 'ROOT\'. apply() refuses a plan with a name the build does not have.
#   arms      squad -> weapon class for all its armed actors (kl_arms.POOLS; the template by seed and path)
#   unleash   squads whose ZSquadScript field 0 becomes eUnleashed (stock: 3..13 squads a level)
#   timers    TriggerDelay / TriggerDelay2 -> seconds;  counters: TriggerCounter -> count
#   start     added to AIMonitor field 2 (the round's start)
#   chains    squad -> what its 'wiped out' list names
#   escape    what the monitor's 'vehicle called' list names
# The numbers are GUESSES against two stock facts: the stock waves come 10..20 s apart (TriggerDelay2: 20 s in 15 of
# F01's 44, 10 s in 5) and stock sends every squad to the van 62 s after its 'run' boxes (F07).
PLANS = {}

PLANS['M02_FA_A'] = {
    'what': 'Late Night Opening: 6 mall guards in 4 squads on three floors, 2 transporter guards, 4 police in ONE car',
    # the four who come by car are the only police of the map: rifles (Dead Men: M4A1), and the two transporter
    # guards who flank with them a rifle and a shotgun's worth of health
    'arms': {'AIEnemies!PoliceSwats': 'rifle', 'AIEnemies!TransporterGuards': 'rifle'},
    # the 3rd-floor guard and the jewel shop pair only stand (eStayBack): they come for the crew
    'unleash': ['AIEnemies!3rdFloor_Guard_02', 'AIEnemies!JewelShop_Guards'],
    # Dead Men: the police car comes 80 s after the first step into the mall, or when 2 squads were alarmed;
    # out of the car they hold 30 s before they hunt
    'timers': {'Triggers!ReinforcementsTimer': 45, 'AIEnemies!PoliceSwats\\HuntTimer': 8},
    'counters': {'Triggers!ReinforcementsCounter': 1},
    # ... and that timer now runs from GO, whatever the crew does (stock starts its timers with the round); its
    # two boxes at the mall's doors stay, and the car comes once: Dead Men put a gate before it
    'start': ['Triggers!ReinforcementsTimer'],
    'chains': {
        # a floor cleared -> the next floor's guards come down / up to the place (their flank routs) and the
        # police are called (the map's own counter; its count is 1 now)
        'AIEnemies!2ndFloor_Guards': ['AIEnemies!3rdFloor_Guard_01\\HuntBehaviour', 'AIEnemies!JewelShop_Guards\\FlankingBehaviour', 'Triggers!ReinforcementsCounter'],
        'AIEnemies!3rdFloor_Guard_01': ['AIEnemies!3rdFloor_Guard_02\\FlankingBehaviour', 'AIEnemies!JewelShop_Guards\\FlankingBehaviour', 'Triggers!ReinforcementsCounter'],
        'AIEnemies!3rdFloor_Guard_02': ['AIEnemies!3rdFloor_Guard_01\\HuntBehaviour', 'AIEnemies!JewelShop_Guards\\FlankingBehaviour', 'Triggers!ReinforcementsCounter'],
        'AIEnemies!JewelShop_Guards': ['AIEnemies!2ndFloor_Guards\\FlankingBehaviour', 'AIEnemies!3rdFloor_Guard_01\\HuntBehaviour', 'Triggers!ReinforcementsCounter'],
        # the police dead -> the transporter guards hunt (they are the last armed people of the map)
        'AIEnemies!PoliceSwats': ['AIEnemies!TransporterGuards\\HuntBehaviour'],
        'AIEnemies!TransporterGuards': ['AIEnemies!PoliceSwats\\HuntBehaviour'],
    },
    # the car is called: the police car comes if it has not, and everybody alive hunts
    'escape': ['AIEnemies!PoliceSwats\\Gate\\Way#01', 'AIEnemies!PoliceSwats\\HuntBehaviour', 'AIEnemies!TransporterGuards\\HuntBehaviour',
               'AIEnemies!3rdFloor_Guard_01\\HuntBehaviour', 'AIEnemies!2ndFloor_Guards\\FlankingBehaviour',
               'AIEnemies!3rdFloor_Guard_02\\FlankingBehaviour', 'AIEnemies!JewelShop_Guards\\FlankingBehaviour'],
}

PLANS['M01_FA_A'] = {
    'what': 'Hot Coffee: 4 in the back room (the boss and three), 3 single guards in the diner / shop, 4 in two parked cars, 2 gang members',
    # the four who sit in the two cars in front are the map's reinforcement: rifles (Dead Men: P90)
    'arms': {'AI_Enemies!FrontMall_01': 'rifle', 'AI_Enemies!FrontMall_02': 'rifle'},
    # Retomoto: 'guys with pistols will rush you'. The two pistol men of the back room come out; the boss stays
    'unleash': ['AI_Enemies!BossFlank_01', 'AI_Enemies!BossFlank_02'],
    'timers': {}, 'counters': {}, 'start': [],
    'chains': {
        'AI_Enemies!CheckFront': ['AI_Enemies!KitchenBoy\\HuntBehaviour', 'AI_Enemies!CornerShop\\HuntBehaviour', 'AI_Enemies!FrontMall_01\\HuntBehaviour'],
        'AI_Enemies!KitchenBoy': ['AI_Enemies!CheckFront\\HuntBehaviour', 'AI_Enemies!CornerShop\\HuntBehaviour', 'AI_Enemies!FrontMall_02\\HuntBehaviour'],
        'AI_Enemies!CornerShop': ['AI_Enemies!FrontMall_01\\HuntBehaviour', 'AI_Enemies!FrontMall_02\\HuntBehaviour'],
        'AI_Enemies!FrontMall_01': ['AI_Enemies!FrontMall_02\\HuntBehaviour', 'Civilians!GangMembers\\FlankingBehaviour'],
        'AI_Enemies!FrontMall_02': ['AI_Enemies!FrontMall_01\\HuntBehaviour', 'Civilians!GangMembers\\FlankingBehaviour'],
        'AI_Enemies!BossFlank_01': ['AI_Enemies!BossFlank_02\\FlankingBehaviour', 'AI_Enemies!BossFlank_03\\FlankingBehaviour', 'AI_Enemies!TheBoss\\FlankingBehaviour'],
        'AI_Enemies!BossFlank_02': ['AI_Enemies!BossFlank_01\\FlankingBehaviour', 'AI_Enemies!BossFlank_03\\FlankingBehaviour', 'AI_Enemies!TheBoss\\FlankingBehaviour'],
        'AI_Enemies!BossFlank_03': ['AI_Enemies!BossFlank_01\\FlankingBehaviour', 'AI_Enemies!BossFlank_02\\FlankingBehaviour', 'AI_Enemies!TheBoss\\FlankingBehaviour'],
        'AI_Enemies!TheBoss': ['AI_Enemies!BossFlank_01\\FlankingBehaviour', 'AI_Enemies!BossFlank_02\\FlankingBehaviour', 'AI_Enemies!BossFlank_03\\FlankingBehaviour'],
    },
    # the map's own exit boxes (ExitDiner, ExitShop_01 / _02) already send seven squads; the call adds the rest
    'escape': ['AI_Enemies!CheckFront\\HuntBehaviour', 'AI_Enemies!KitchenBoy\\HuntBehaviour', 'AI_Enemies!CornerShop\\HuntBehaviour',
               'AI_Enemies!FrontMall_01\\HuntBehaviour', 'AI_Enemies!FrontMall_02\\HuntBehaviour', 'AI_Enemies!BossFlank_01\\FlankingBehaviour',
               'AI_Enemies!BossFlank_02\\FlankingBehaviour', 'AI_Enemies!BossFlank_03\\FlankingBehaviour', 'AI_Enemies!TheBoss\\FlankingBehaviour',
               'Civilians!GangMembers\\FlankingBehaviour'],
}

PLANS['M03_FA_A'] = {
    'what': 'Withdrawal (the bank): 4 guards inside in 3 squads, 2 at the loading dock, 9 police in four cars',
    'arms': {},                                     # the nine police have rifles already (Dead Men: M4A1)
    'unleash': ['AI_Enemies!BankMainSquad_01', 'AI_Enemies!BankMainSquad_03'],      # the single guards of the hall
    'timers': {},
    'counters': {'Triggers!CivilWar_Counter': 2},   # Dead Men: 4 alarmed civilian squads bring the second police car
    'start': [],
    'chains': {
        # a squad of the hall down -> the others hunt and the next car is called (the map's own timers; Dead Men
        # itself names ArrivingCops_Timer from five boxes)
        'AI_Enemies!BankMainSquad_01': ['AI_Enemies!BankMainSquad_02\\HuntBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour', 'Triggers!Parkinglot_SWAT_Timer'],
        'AI_Enemies!BankMainSquad_02': ['AI_Enemies!BankMainSquad_01\\HuntBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour', 'Triggers!ArrivingCops_Timer'],
        'AI_Enemies!BankMainSquad_03': ['AI_Enemies!BankMainSquad_01\\HuntBehaviour', 'AI_Enemies!BankMainSquad_02\\HuntBehaviour', 'Triggers!Parkinglot_SWAT_Timer'],
        'AI_Enemies!LoadingDockSquad_01': ['AI_Enemies!ParkingLotSWAT_01\\HuntBehaviour', 'Triggers!ArrivingCops_Timer'],
        'AI_Enemies!ParkingLotSWAT_01': ['AI_Enemies!ArrivingCops_Squad_01\\HuntBehaviour', 'AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'Triggers!ArrivingCops_Timer'],
        'AI_Enemies!ArrivingCops_Squad_01': ['AI_Enemies!ArrivingCops_Squad_02\\HuntBehaviour', 'AI_Enemies!ParkingLotSWAT_01\\HuntBehaviour'],
        'AI_Enemies!ArrivingCops_Squad_02': ['AI_Enemies!ArrivingCops_Squad_01\\HuntBehaviour', 'AI_Enemies!EscSquad\\HuntBehaviour'],
        'AI_Enemies!EscSquad': ['AI_Enemies!ArrivingCops_Squad_02\\HuntBehaviour', 'AI_Enemies!ParkingLotSWAT_01\\HuntBehaviour'],
    },
    # the van is called: the last car is sent for and everybody alive hunts. No drive rout is named here: a
    # squad that has driven is not sent back to its car
    'escape': ['Triggers!ArrivingCops_Timer', 'AI_Enemies!EscSquad\\HuntBehaviour', 'AI_Enemies!ParkingLotSWAT_01\\HuntBehaviour',
               'AI_Enemies!ArrivingCops_Squad_01\\HuntBehaviour', 'AI_Enemies!ArrivingCops_Squad_02\\HuntBehaviour',
               'AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'AI_Enemies!BankMainSquad_01\\HuntBehaviour',
               'AI_Enemies!BankMainSquad_02\\HuntBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour'],
}

PLANS['M06_FA_A'] = {
    'what': 'A Walk in the Park: two gangs at a deal, 7 + 7 in nine squads, a boss helicopter; the escape is a helicopter',
    'arms': {},
    'unleash': [],
    # after the first shot the American side holds 45 s before it hunts. The Japanese timer (50 s) also flies the
    # boss out (its list starts the helicopter): not touched
    'timers': {'Timers!US_Boss_Timer': 20},
    'counters': {}, 'start': [],
    'chains': {
        'AI_Enemies!US_DrugSquad_Bridge_01': ['AI_Enemies!US_DrugSquad_Bridge_02\\HuntBehaviour', 'AI_Enemies!US_DrugSquad_Secure_Boss\\FlankingBehaviour'],
        'AI_Enemies!US_DrugSquad_Bridge_02': ['AI_Enemies!US_DrugSquad_Bridge_01\\HuntBehaviour', 'AI_Enemies!US_Boss\\FlankingBehaviour'],
        'AI_Enemies!US_DrugSquad_Island_01': ['AI_Enemies!US_DrugSquad_Bridge_01\\HuntBehaviour', 'AI_Enemies!US_DrugSquad_Bridge_02\\HuntBehaviour'],
        'AI_Enemies!US_DrugSquad_Secure_Boss': ['AI_Enemies!US_Boss\\FlankingBehaviour', 'AI_Enemies!US_DrugSquad_Bridge_01\\HuntBehaviour'],
        'AI_Enemies!US_Boss': ['AI_Enemies!US_DrugSquad_Secure_Boss\\FlankingBehaviour', 'AI_Enemies!US_DrugSquad_Bridge_01\\HuntBehaviour', 'AI_Enemies!US_DrugSquad_Bridge_02\\HuntBehaviour'],
        'AI_Enemies!JPN_DrugSquad_Bridge_01': ['AI_Enemies!JPN_DrugSquad_Island_01\\FlankingBehaviour', 'AI_Enemies!JPN_DrugSquad_Secure_Chopper_01\\FlankingBehaviour'],
        'AI_Enemies!JPN_DrugSquad_Island_01': ['AI_Enemies!JPN_DrugSquad_Bridge_01\\HuntBehaviour', 'AI_Enemies!JPN_DrugSquad_Secure_Chopper_01\\FlankingBehaviour'],
        'AI_Enemies!JPN_DrugSquad_Secure_Chopper_01': ['AI_Enemies!JPN_DrugSquad_Bridge_01\\HuntBehaviour', 'AI_Enemies!JPN_DrugSquad_Island_01\\FlankingBehaviour'],
    },
    'escape': ['AI_Enemies!US_DrugSquad_Bridge_01\\HuntBehaviour', 'AI_Enemies!US_DrugSquad_Bridge_02\\HuntBehaviour', 'AI_Enemies!US_Boss\\FlankingBehaviour',
               'AI_Enemies!US_DrugSquad_Secure_Boss\\FlankingBehaviour', 'AI_Enemies!JPN_DrugSquad_Bridge_01\\HuntBehaviour',
               'AI_Enemies!JPN_DrugSquad_Island_01\\FlankingBehaviour', 'AI_Enemies!JPN_DrugSquad_Secure_Chopper_01\\HuntBehaviour'],
}


# ------------------------------------------------------------------ reading
def archive_of(src):
    if os.path.isdir(src):
        return next(os.path.join(src, x) for x in sorted(os.listdir(src)) if x.lower().endswith('_main.zip'))
    return src if os.path.isfile(src) else J.level_zip(src)


def map_of(src):
    """The Dead Men map a build folder holds (result.json of kl_maps), or None (a stock level)."""
    d = src if os.path.isdir(src) else os.path.dirname(src)
    rj = os.path.join(d, 'result.json')
    if os.path.isfile(rj):
        return json.load(open(rj)).get('M')
    return None


def full(p):
    return p if p.startswith(R) or p == 'ROOT' else R + p


def node(sc, name):
    hit = sc.resolve(full(name))
    if len(hit) != 1:
        raise KeyError('%s: %d nodes named %s' % (sc.label, len(hit), name))
    return hit[0]


def ctrls(sc, k):
    return [(i, sc.p.key(nm), [kl_fa.value(sc, u) for u in units(b[1:-1])]) for i, (nm, b) in enumerate(sc.nodes[k]['ctrls'])]


def ctrl(sc, k, *names):
    for i, n, v in ctrls(sc, k):
        if n in names:
            return i, n, v
    raise KeyError('%s has no %s' % (sc.path[k], ' / '.join(names)))


def effective(v):
    """A ZSoldier's fields as the game uses them: the preset of its skill name written over fields 4, 5, 6, 13, 14,
    accuracy times 1.1 for a soldier that is no mercenary, clamped (kl2 0x46e410)."""
    v = list(v)
    if v[SKILL] in PRESET:
        for f, x in zip(PRESET_FIELDS, PRESET[v[SKILL]]):
            v[f] = float(x)
    if v[MERC] == 'No_Mercenary':
        v[ACC] = v[ACC] * ACC_FACTOR
    v[ACC], v[F6] = min(max(v[ACC], 0.0), 100.0), min(max(v[F6], 0.0), 100.0)
    return v


def weapon_class(t):
    return CLASS_OF.get(t) or ('-' if not t else '?')


def positions(archive):
    """{node index: (x, y, z)} of a built level."""
    import kl_maps
    with zipfile.ZipFile(archive) as z:
        m = {n.rsplit('_Main', 1)[1]: n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
    ents = list(scene.entities())
    pos = kl_maps.world(scene)
    return {k + 1: pos[e] for k, e in enumerate(ents)}


def reverse(sc):
    """{path, lower case, with ROOT: [(node, controller name, field, its values)]}: who names an object in a list."""
    rev = collections.defaultdict(list)
    for k in range(1, len(sc.nodes)):
        for _i, n, v in ctrls(sc, k):
            for fi, x in enumerate(v):
                if isinstance(x, list):
                    for p in x:
                        if isinstance(p, str) and p:
                            rev[full(p).lower()].append((k, n, fi, v))
    return rev


def started_by(sc, rev, k, depth=0, seen=None):
    """What names node k, as short texts: a box, the round's start, a timer (+ its seconds), a counter, an event
    list of a squad, the end of another rout. Followed up to four objects back."""
    seen = seen or set()
    out = []
    short = lambda j: sc.path[j][5:].split('!', 1)[-1] if sc.path[j].count('!') else sc.path[j][5:]
    for j, n, fi, v in rev.get(sc.path[k].lower(), ()):
        if (j, n, fi) in seen or depth > 4:
            continue
        seen = seen | {(j, n, fi)}
        up = lambda: started_by(sc, rev, j, depth + 1, seen) or ['(nothing names %s)' % short(j)]
        if n in ('TriggerBox', 'OnlineTriggerBox'):
            out.append('box %s' % short(j))
        elif n == 'AIMonitor':
            out.append('ROUND START')
        elif n == 'OnlineEscVehicleMonitor':
            out.append('VEHICLE CALLED' if fi == MON_CALLED else 'escape monitor list %d' % fi)
        elif n in ('TriggerDelay', 'TriggerDelay2'):
            out += ['%s + %g s' % (u, v[0]) for u in up()]
        elif n == 'TriggerCounter':
            out += ['%s (x%d: %s)' % (u, v[0], short(j)) for u in up()]
        elif n == 'ZSquadScript':
            out.append('%s of squad %s' % ('WIPED OUT' if fi == SQUAD_DEAD else 'event %d' % fi, short(j)))
        elif n in ('GatePath', 'RandomTrigger', 'AIDWrapper'):
            out += up()
        elif n in BEHAVE:
            out.append('after %s' % short(j))
        else:
            out.append('%s %s' % (n, short(j)))
    return sorted(set(out))


def measure(src):
    """-> dict: 'squads' [row per squad with a soldier or civilian], 'totals', 'sizes'. A row: name, attitude,
    active (ZSquadScript field 3), people [(path, style, skill, accuracy as used, health, weapon, class)],
    civilians, routs {name: [started by]}, dead (its 'wiped out' list), place (centre of its actors), far (metres
    from the START row)."""
    zp = archive_of(src)
    sc = kl_fa.load(zp)[0]
    rev, pos = reverse(sc), positions(zp)
    f = kl_arms.fields()
    starts = [pos[k] for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint'
              and any(x == kl_fa.START for x in kl_fa.node_values(sc, k))]
    c0 = tuple(sum(p[i] for p in starts) / len(starts) for i in range(3)) if starts else None
    rows = []
    for k in range(1, len(sc.nodes)):
        if not kl_fa.has(sc, k, 'ZSquadScript'):
            continue
        sq = ctrl(sc, k, 'ZSquadScript')[2]
        people, civ, routs, where, ally = [], 0, collections.OrderedDict(), [], 0
        for c in range(k + 1, sc.end[k]):
            cs = ctrls(sc, c)
            if sc.cls(c) == 'ZFFActor':
                nv = kl_fa.node_values(sc, c)
                sol = next((v for _i, n, v in cs if n == 'ZSoldier'), None)
                if nv[J.labels('dd', 'ZFFActor').index('ZFFActor[0]')] == 'Ally':
                    ally += 1
                elif sol is None:
                    civ += 1
                else:
                    e = effective(sol)
                    w = nv[f[0]].rsplit('\\', 1)[-1]
                    people.append((sc.path[c], sol[STYLE], sol[SKILL], e[ACC], sol[HEALTH], w, weapon_class(w)))
                    where.append(pos[c])
            if any(n in BEHAVE for _i, n, _v in cs):
                routs[sc.path[c][len(sc.path[k]) + 1:]] = started_by(sc, rev, c)
        if not people and not civ:
            continue
        place = tuple(sum(p[i] for p in where) / len(where) for i in range(3)) if where else None
        rows.append({'name': sc.path[k][5:], 'attitude': sq[0], 'active': sq[3], 'people': people, 'civilians': civ, 'bots': ally,
                     'routs': routs, 'dead': [p.replace(R, '') for p in sq[SQUAD_DEAD]],
                     'events': {i: [p.replace(R, '') for p in sq[i]] for i in range(4, 19) if i != SQUAD_DEAD and sq[i]},
                     'place': place, 'far': math.dist(place, c0) / 100.0 if place and c0 else None})
    ppl = [p for r in rows for p in r['people']]
    team = J.labels('dd', 'ZFFActor').index('ZFFActor[0]')
    bots = sum(1 for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and kl_fa.node_values(sc, k)[team] == 'Ally')
    mon = [v for _k, _i, v in kl_fa.controllers(sc, 'OnlineEscVehicleMonitor')]
    aim = [v for _k, _i, v in kl_fa.controllers(sc, 'AIMonitor')]
    with zipfile.ZipFile(zp) as z:
        sizes = {e: i.file_size for i in z.infolist() for e in BUDGET if i.filename.endswith('_Main' + e)}
    wav = os.path.join(os.path.dirname(zp), os.path.basename(zp)[:-4] + '.WAV')
    sizes['.WAV'] = os.path.getsize(wav) if os.path.isfile(wav) else 0
    tot = collections.OrderedDict((
        ('soldiers', len(ppl)), ('civilians', sum(r['civilians'] for r in rows)), ('AI heisters', bots),
        ('squads with soldiers', sum(bool(r['people']) for r in rows)),
        ('hit points (health added up)', int(sum(p[4] for p in ppl))),
        ('health mean', round(sum(p[4] for p in ppl) / len(ppl), 1) if ppl else 0),
        ('accuracy mean (as used)', round(sum(p[3] for p in ppl) / len(ppl), 1) if ppl else 0),
        ('skill names', dict(collections.Counter(p[2] for p in ppl))),
        ('weapon classes', dict(collections.Counter(p[6] for p in ppl).most_common())),
        ('unleashed squads', sum(r['attitude'] == 'eUnleashed' and bool(r['people']) for r in rows)),
        ('squads not in the world at the load (field 3 = 0)', sum(not r['active'] and bool(r['people']) for r in rows)),
        ('soldiers in those', sum(len(r['people']) for r in rows if not r['active'])),
        ('squads with a wiped-out list', sum(bool(r['dead']) and bool(r['people']) for r in rows)),
        ('named at the round start (AIMonitor 2)', sum(len(v[START_LIST]) for v in aim)),
        ('named when the vehicle is called (monitor 4..7)', sum(len(v[i]) for v in mon for i in range(4, 8))),
        ('FakeTarget (police shoot the vehicle)', len(kl_fa.controllers(sc, 'FakeTarget'))),
        ('timers s', sorted(round(float(v[0]), 1) for n in ('TriggerDelay', 'TriggerDelay2') for _k, _i, v in kl_fa.controllers(sc, n))),
    ))
    return {'squads': rows, 'totals': tot, 'sizes': sizes, 'archive': zp}


def show(m, log=print, routs=True):
    log('%s' % m['archive'])
    for r in m['squads']:
        if not r['people']:
            continue
        log('  %-44s %-10s %s %2d  %s%s' % (
            r['name'][-44:], r['attitude'][1:], 'in world' if r['active'] else 'LATER   ', len(r['people']),
            '%4.0f m from the start row' % r['far'] if r['far'] is not None else '', '  + %d civilian' % r['civilians'] if r['civilians'] else ''))
        for _p, style, skill, acc, hp, w, c in r['people']:
            log('      %-10s %-8s accuracy %3.0f  health %3.0f  %-22s %s' % (style[1:], skill[1:], acc, hp, w or '(unarmed)', c))
        if routs:
            for name, by in r['routs'].items():
                log('      rout %-28s <- %s' % (name[:28], '; '.join(by)[:150] if by else 'NOTHING NAMES IT'))
            if r['dead']:
                log('      WIPED OUT -> %s' % ', '.join(r['dead'])[:170])
            for i, v in r['events'].items():
                log('      event %-2d  -> %s' % (i, ', '.join(v)[:170]))
    for k, v in m['totals'].items():
        log('  %-52s %s' % (k, v))
    log('  sizes MB: ' + ', '.join('%s %.1f' % (e, m['sizes'].get(e, 0) / 1e6) for e in BUDGET + ('.WAV',)))


# ------------------------------------------------------------------ writing
def setv(sc, us, i, v):
    """Field unit i = v in the token kind the field has (as kl_fa_author.setv); a reference list keeps the form
    its level uses (with or without ROOT) - see refs()."""
    op = us[i][0][0]
    if op == 0x0a:
        us[i] = [(op, struct.pack('<f', v))]
    elif op == 0x09:
        us[i] = [(op, struct.pack('<I', int(v)))]
    elif op in (0x05, 0x06, 0x07):
        us[i] = [(op, bytes([int(v)]))]
    elif op in (0x0c, 0x0e):
        us[i] = [(op, struct.pack('<I', sc.p.key_index(v)))]
    elif op == 0x04:
        us[i] = kl_fa._refs(sc, v)
    else:
        raise ValueError('field %d: token %#x' % (i, op))


def rooted(sc, name):
    """Does this level write the reference lists of controller `name` with 'ROOT\\'? Majority of what is there
    (stock: ZSquadScript without, TriggerBox with; a converted Dead Men map: mostly without). Both forms are
    resolved by the game in stock levels."""
    n = collections.Counter()
    for _k, _i, v in kl_fa.controllers(sc, name):
        for x in v:
            if isinstance(x, list):
                n.update(p.startswith(R) for p in x if isinstance(p, str))
    return n[True] > n[False]


def refs(sc, name, paths):
    r = rooted(sc, name)
    return [full(p) if r else full(p)[len(R):] for p in paths]


def put(sc, k, names, **f):
    """Fields fN = value of the controller `names` of node k. -> the old values of those fields."""
    i, n, v = ctrl(sc, k, *((names,) if isinstance(names, str) else names))
    old = {}
    def fn(us):
        for a, x in f.items():
            j = int(a[1:])
            old[j] = v[j]
            setv(sc, us, j, refs(sc, n, x) if isinstance(x, list) else x)
    kl_fa.edit(sc, k, i, fn)
    return old


def add(sc, k, names, field, paths):
    """Append paths to a reference list (no entry twice). -> how many were new."""
    _i, n, v = ctrl(sc, k, *((names,) if isinstance(names, str) else names))
    have = [full(p).lower() for p in v[field]]
    new = [p for p in paths if full(p).lower() not in have]
    if new:
        put(sc, k, n, **{'f%d' % field: list(v[field]) + new})
    return len(new)


def strength(sc, anm, plan, log=print, presets=False, seed=kl_arms.SEED):
    """Part 1. -> report rows [(actor, what changed)]."""
    eq, hand, f = kl_arms.equipment(sc), kl_arms.handling(anm), kl_arms.fields()
    root = next(i['path'].rsplit('\\', 1)[0] + '\\' for i in eq.values())
    rep = []
    # ARMS first: the floors follow the weapon that is carried in the end
    for squad, cls in plan.get('arms', {}).items():
        k = node(sc, squad)
        for c in range(k + 1, sc.end[k]):
            if sc.cls(c) != 'ZFFActor' or not any(n == 'ZSoldier' for _i, n, _v in ctrls(sc, c)):
                continue
            nv = kl_fa.node_values(sc, c)
            old = nv[f[0]].rsplit('\\', 1)[-1]
            if not old or weapon_class(old) == cls:
                continue                                # unarmed stays unarmed; the class is right already
            fo = kl_arms.folders_of(hand, nv[f[4]])
            pool = [(t, w) for t, w in kl_arms.POOLS[cls] if t.lower() in eq and fo.get(eq[t.lower()]['folder'], 0) >= kl_arms.FOLDER_MIN]
            if not pool:
                rep.append((sc.path[c], 'KEEPS %s: its animation set has no %s folder' % (old, cls)))
                continue
            r = random.Random(kl_arms._rank(seed, sc.path[c]))
            x = r.uniform(0, sum(w for _t, w in pool))
            new = pool[-1][0]
            for t, w in pool:
                x -= w
                if x <= 0:
                    new = t
                    break
            kl_fa.edit(sc, c, None, lambda us, new=new: us.__setitem__(f[0], [kl_fa._str(sc, root + new)]))
            rep.append((sc.path[c], 'weapon %s -> %s (%s)' % (old, new, cls)))
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor':
            continue
        hit = [(i, v) for i, n, v in ctrls(sc, k) if n == 'ZSoldier']
        if not hit:
            continue
        i, v = hit[0]
        if len(v) != 23:
            raise ValueError('%s: ZSoldier is not in the Dog Days layout' % sc.path[k])
        nv = kl_fa.node_values(sc, k)
        if nv[J.labels('dd', 'ZFFActor').index('ZFFActor[0]')] == 'Ally':
            continue                                    # an AI heister (kl_fa_bots): not ours
        cls = weapon_class(nv[f[0]].rsplit('\\', 1)[-1])
        if cls not in STRENGTH or v[STYLE] == 'eDog':
            continue
        if presets:                                     # Retomoto's way, for the comparison run
            name = NAMES[cls]
            if v[SKILL] != name:
                kl_fa.edit(sc, k, i, lambda us, name=name: setv(sc, us, SKILL, name))
                rep.append((sc.path[k], 'skill %s -> %s (accuracy as used %.0f -> %.0f)' % (
                    v[SKILL], name, effective(v)[ACC], effective(v[:SKILL] + [name] + v[SKILL + 1:])[ACC])))
            continue
        floor, hp = STRENGTH[cls]
        fac = ACC_FACTOR if v[MERC] == 'No_Mercenary' else 1.0
        acc, aim = min(PRESET[floor][0] * fac, 100.0), float(PRESET[floor][1])     # accuracy as the game USES it
        e, new = effective(v), {}
        if e[ACC] < acc - 0.01 or e[AIM] < aim - 0.01:
            # below the floor: the row becomes eCustom, with the preset's numbers where a preset was in force
            # (they are what the soldier had; a name left in place would write over the new numbers). An
            # eVeteran loses whatever 0x60fd40 does for that name alone (not read)
            if v[SKILL] != 'eCustom':
                new[SKILL] = 'eCustom'
                for fi, x in zip(PRESET_FIELDS, PRESET[v[SKILL]]):
                    new[fi] = float(x)
            new[ACC] = max(new.get(ACC, v[ACC]), round(acc / fac, 1))
            new[AIM] = max(new.get(AIM, v[AIM]), aim)
        hp = float(round(hp * HEALTH_SCALE))
        if 0 < v[HEALTH] < hp:                          # <= 0 = invulnerable (kl2 0x8fbac0): not touched
            new[HEALTH] = float(hp)
        new = {fi: x for fi, x in new.items() if x != v[fi]}
        if new:
            kl_fa.edit(sc, k, i, lambda us, new=new: [setv(sc, us, fi, x) for fi, x in new.items()])
            after = effective([new.get(fi, x) for fi, x in enumerate(v)])
            what = []
            if SKILL in new:
                what.append('skill %s -> eCustom (its preset numbers kept)' % v[SKILL])
            if abs(after[ACC] - e[ACC]) > 0.05:
                what.append('accuracy as used %s -> %s' % (_n(round(e[ACC], 1)), _n(round(after[ACC], 1))))
            if after[AIM] != e[AIM]:
                what.append('aim %s -> %s' % (_n(e[AIM]), _n(after[AIM])))
            if HEALTH in new:
                what.append('health %s -> %s' % (_n(v[HEALTH]), _n(new[HEALTH])))
            rep.append((sc.path[k], '%s: %s' % (cls, ', '.join(what))))
    log('  kl_map_ai: strength: %d changes on %d actors%s' % (len(rep), len({p for p, _t in rep}), ' (PRESETS: Retomoto\'s skill names)' if presets else ''))
    return rep


def _n(x):
    return ('%g' % x) if isinstance(x, float) else str(x)


def waves(sc, plan, log=print):
    """Part 2. -> report lines."""
    rep = []
    for squad in plan.get('unleash', ()):
        old = put(sc, node(sc, squad), 'ZSquadScript', f0='eUnleashed')[0]
        if old != 'eUnleashed':
            rep.append('%s: %s -> eUnleashed' % (squad, old))
    for name, s in plan.get('timers', {}).items():
        k = node(sc, name)
        _i, n, v = ctrl(sc, k, 'TriggerDelay', 'TriggerDelay2')
        put(sc, k, n, f0=float(s) if n == 'TriggerDelay2' else int(s))
        rep.append('%s: %g s -> %g s' % (name, v[0], s))
    for name, c in plan.get('counters', {}).items():
        old = put(sc, node(sc, name), 'TriggerCounter', f0=int(c))[0]
        rep.append('%s: count %d -> %d' % (name, old, c))
    if plan.get('start'):
        mon = kl_fa.controllers(sc, 'AIMonitor')
        if len(mon) != 1:
            raise ValueError('%d AIMonitor objects' % len(mon))
        n = add(sc, mon[0][0], 'AIMonitor', START_LIST, [_must(sc, p) for p in plan['start']])
        rep.append('round start (AIMonitor field %d): + %d: %s' % (START_LIST, n, ', '.join(plan['start'])))
    log('  kl_map_ai: waves: %d changes' % len(rep))
    return rep


def _must(sc, p):
    node(sc, p)
    return p


# ------------------------------------------------------------------ part 0: the police that come by car
# FOUND 2026-10-10: every Dead Men squad that arrives in a car ends its drive with a VehicleExitBehaviourRout
# (M01 2, M02 1, M03 4: 4 + 4 + 9 of the 13 / 12 / 15 soldiers), and kl_convert REMOVES that controller on every
# map ('ctrl_removed'): its field 2 has a type handler no stock Dog Days level stores (index 54, loader
# 0x43e060), so kl_rtp knows no shape for it. The node stays, empty; what it started is started by nothing:
# M02's four police never get FlankingBehaviour or their HuntTimer, M03's ArrivingCops / EscSquad never hunt.
# Read: the loader 0x43e060 is the generic flag-set reader (0x7cc520) with the enum EBoneType pushed, byte for
# byte the shape of the known 'k' loaders (0x44e940, 0x7f30b0), and Dead Men's field is that same enum: the
# token is the same in both games (0x0f, a count and that many names; 0 names in all seven objects).
#   bypass (default)  every list that names the empty node also names what its rout started: values only.
#                     The squad gets its orders; what gets it OUT of the car without the rout is NOT KNOWN
#   --car-exit        the controller is put back, token for token from Dead Men's level. Dog Days registers
#                     the class (ZVehicleExitBehaviourRout) but NO stock level has one: its code has never run
EXIT = 'VehicleExitBehaviourRout'
EXIT_CLASS = 'ZVehicleExitBehaviourRout'


def teach_schema():
    """kl_rtp has no shape for the type of field 2 (never seen in a stock level): 'k', as read from its loader.
    In memory only - the place for it is kl_rtp.build / re/kl2.json (re/map_ai.md, changes for the lead)."""
    fs = J.schema('dd').fields(EXIT_CLASS)
    for i, f in enumerate(fs):
        if f.kind is None:
            fs[i] = f._replace(kind='k')


def lost_exits(sc, m_name):
    """[(node of the build, Dead Men's scene, Dead Men's tokens, [what the rout starts])] for every exit rout of
    Dead Men's level that the build's node of that path lacks."""
    dm = J.Scene.load(m_name)
    out = []
    for k, i, v in kl_fa.controllers(dm, EXIT):
        hit = sc.resolve(dm.path[k])
        if len(hit) != 1:
            raise KeyError('%s: %d nodes in the build' % (dm.path[k], len(hit)))
        if not kl_fa.has(sc, hit[0], EXIT):
            out.append((hit[0], dm, dm.nodes[k]['ctrls'][i][1], [p for p in v[0]]))
    return out


def cars(sc, m_name, restore=False, log=print):
    """Part 0 (with 'waves'). -> report lines."""
    rep = []
    lost = lost_exits(sc, m_name)
    if restore:
        teach_schema()
        for k, dm, toks, starts in lost:
            for p in starts:
                _must(sc, p)
            new = [(op, struct.pack('<I', sc.p.key_index(dm.p.keys[struct.unpack('<I', pl)[0]]))) if op in (0x0c, 0x0e) else (op, pl)
                   for op, pl in toks]
            sc.nodes[k]['ctrls'].append((kl_fa._str(sc, EXIT), new))
            rep.append('%s: %s put back (starts %s)' % (sc.path[k][5:], EXIT, ', '.join(p.replace(R, '') for p in starts)))
    else:
        rev = reverse(sc)
        for k, _dm, _toks, starts in lost:
            n = 0
            for j, name, fi, _v in rev.get(sc.path[k].lower(), ()):
                n += add(sc, j, name, fi, [_must(sc, p) for p in starts]) > 0
            rep.append('%s: its rout is gone; the %d lists that name it now also name %s' % (
                sc.path[k][5:], n, ', '.join(p.replace(R, '') for p in starts)))
    log('  kl_map_ai: cars: %d exit routs lost in the conversion, %s' % (len(lost), 'put back' if restore else 'by-passed'))
    return rep


def chains(sc, plan, log=print):
    """Part 3: ZSquadScript field 8. A squad that has a list already keeps its entries (none of the four has)."""
    rep = []
    for squad, names in plan.get('chains', {}).items():
        n = add(sc, node(sc, squad), 'ZSquadScript', SQUAD_DEAD, [_must(sc, p) for p in names])
        rep.append('%s wiped out -> %s' % (squad, ', '.join(names)))
        if n != len(names):
            rep[-1] += '  (%d were there)' % (len(names) - n)
    log('  kl_map_ai: chains: %d squads name their neighbours when wiped out' % len(rep))
    return rep


def escape(sc, plan, log=print):
    """Part 4: the escape monitor's 'vehicle 1 called' list."""
    names = plan.get('escape') or []
    if not names:
        return []
    mon, ex = kl_fa.controllers(sc, 'OnlineEscVehicleMonitor'), kl_fa.controllers(sc, 'OnlineExitLevelTrigger')
    if len(mon) != 1 or len(mon[0][2]) != 17:
        raise ValueError('the level has %d escape monitors (17 fields expected)' % len(mon))
    if not ex or any(not v[2] or any(v[3:6]) for _k, _i, v in ex):
        raise ValueError('an exit trigger does not have its one vehicle in field 2: the called list would not be field %d' % MON_CALLED)
    n = add(sc, mon[0][0], 'OnlineEscVehicleMonitor', MON_CALLED, [_must(sc, p) for p in names])
    log('  kl_map_ai: escape: the vehicle call names %d objects (%d exit trigger(s))' % (n, len(ex)))
    return ['vehicle called (monitor field %d) -> %s' % (MON_CALLED, ', '.join(names))]


def apply(src, dst, parts=('strength', 'waves', 'chains', 'escape'), presets=False, log=print, car_exit=False):
    """A finished build folder -> folder dst: the archive with a new .prp member, every other member and every
    file beside it copied. -> report dict (also written to <dst>/map_ai.json and map_ai.txt)."""
    import kl_graft
    zp = archive_of(src)
    m_name = map_of(src)
    if m_name not in PLANS:
        raise ValueError('%s: no plan for %r (plans: %s)' % (src, m_name, ', '.join(PLANS)))
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the output folder is the build\'s own')
    plan = PLANS[m_name]
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if data != files[ext['.prp']] or bad:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte (%d misfits): not changed' % len(bad))
    lines = []
    def say(s):
        lines.append(str(s)); log(s)
    say('kl_map_ai: %s (%s): %s' % (m_name, zp, plan['what']))
    rep = collections.OrderedDict(map=m_name, source=zp, parts=list(parts), presets=presets, car_exit=car_exit, health_scale=HEALTH_SCALE)
    if 'strength' in parts:
        rep['strength'] = strength(sc, files[ext['.ANM']], plan, say, presets)
    if 'waves' in parts:
        rep['cars'] = cars(sc, m_name, car_exit, say)
        rep['waves'] = waves(sc, plan, say)
    if 'chains' in parts:
        rep['chains'] = chains(sc, plan, say)
    if 'escape' in parts:
        rep['escape'] = escape(sc, plan, say)
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if bad:
        raise ValueError('%d objects do not fit their class after the changes: %s' % (len(bad), bad[:3]))
    rep['dangling'] = faults(sc)
    if rep['dangling']:
        raise ValueError('references that name nothing: %s' % rep['dangling'][:5])
    arms = kl_arms.check(sc, files[ext['.ANM']])
    if any(s == 1 for s, _c, _t in arms):
        raise ValueError('kl_arms.check: %s' % arms)
    before = {n: len(files[n]) for n in order}
    files[ext['.prp']] = data
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and not x.startswith('map_ai.'):
            shutil.copyfile(q, os.path.join(dst, x))
    # kl_maps' record of the steps after the verified build: this one is added and proved (CRC and size of every
    # member, sha1 of every file beside the archive) to have changed the .prp and nothing else
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        old, now = st.get('final') or [[], []], kl_maps.member_ids(dst)
        diff = [a[0] for a, b in zip(old[0], now[0]) if a != b] + [a[0] for a, b in zip(old[1], now[1]) if a != b]
        if diff != ['.prp'] or [a[0] for a in old[0]] != [a[0] for a in now[0]] or len(old[1]) != len(now[1]):
            raise ValueError('more than the .prp member differs from the build: %s' % diff)
        st['map_ai'], st['final'] = diff, now
        st['same'] = [e for e in st.get('same', []) if e not in diff]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    rep['members changed'] = [n for n in order if n == ext['.prp']]
    rep['prp bytes'] = (before[ext['.prp']], len(data))
    for key in ('strength', 'cars', 'waves', 'chains', 'escape'):
        for r in rep.get(key, ()):
            say('    %s' % (r if isinstance(r, str) else '%s: %s' % (r[0][5:], r[1])))
    say('kl_map_ai: written %s; only the .prp member differs (%d -> %d bytes)' % (out, before[ext['.prp']], len(data)))
    with open(os.path.join(dst, 'map_ai.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    with open(os.path.join(dst, 'map_ai.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return rep


def faults(sc):
    """Entries of the lists this tool writes that name nothing (must be empty)."""
    out = []
    for name, fs in (('ZSquadScript', range(4, 19)), ('AIMonitor', (START_LIST,)), ('OnlineEscVehicleMonitor', range(0, 9))):
        for k, _i, v in kl_fa.controllers(sc, name):
            for fi in fs:
                for p in v[fi] if isinstance(v[fi], list) else ():
                    if not sc.resolve(full(p)):
                        out.append('%s %s[%d]: %s' % (sc.path[k], name, fi, p))
    return out


# ------------------------------------------------------------------ the check: before / after
def compare(a, b, log=print):
    """Two builds of one map (folders or archives): the before / after table. -> (measure a, measure b)."""
    A, B = measure(a), measure(b)
    log('BEFORE %s\nAFTER  %s' % (A['archive'], B['archive']))
    sa, sb = {r['name']: r for r in A['squads']}, {r['name']: r for r in B['squads']}
    log('  %-40s | %-52s | %s' % ('squad', 'before', 'after'))
    for name in list(sa) + [n for n in sb if n not in sa]:
        x, y = sa.get(name), sb.get(name)
        if not (x and x['people']) and not (y and y['people']):
            continue
        def cell(r):
            if not r:
                return '(not in the level)'
            return '%d  %-9s %s' % (len(r['people']), r['attitude'][1:], 'in world' if r['active'] else 'later')
        log('  %-40s | %-52s | %s' % (name[-40:], cell(x), cell(y)))
        for i in range(max(len(x['people']) if x else 0, len(y['people']) if y else 0)):
            def man(r):
                if not r or i >= len(r['people']):
                    return ''
                _p, style, skill, acc, hp, w, c = r['people'][i]
                return '%-8s acc %3.0f hp %3.0f %s' % (skill[1:], acc, hp, w or '(unarmed)')
            log('  %-40s |   %-50s |   %s' % ('', man(x), man(y)))
        for key, label in (('dead', 'wiped out ->'),):
            if (x and x[key]) or (y and y[key]):
                log('  %-40s |   %-50s |   %s' % (label, ', '.join(p.split('!', 1)[-1] for p in (x or {}).get(key, [])) or '-',
                                                  ', '.join(p.split('!', 1)[-1] for p in (y or {}).get(key, [])) or '-'))
        ra, rb = (x or {}).get('routs', {}), (y or {}).get('routs', {})
        for rout in list(ra) + [n for n in rb if n not in ra]:
            if ra.get(rout) != rb.get(rout):
                log('  %-40s |   %-50s |   %s' % ('  rout ' + rout[:32], '; '.join(ra.get(rout, [])) or 'nothing names it', '; '.join(rb.get(rout, [])) or 'nothing names it'))
    log('  totals')
    for k in A['totals']:
        log('  %-52s %-34s %s%s' % (k, str(A['totals'][k])[:34], B['totals'][k], '' if A['totals'][k] == B['totals'][k] else '   <'))
    log('  member sizes, bytes (the four blocks + the .WAV beside the archive)')
    for e in BUDGET + ('.WAV',):
        log('  %-52s %-34d %d%s' % (e, A['sizes'].get(e, 0), B['sizes'].get(e, 0), '' if A['sizes'].get(e) == B['sizes'].get(e) else '   DIFFERS'))
    return A, B


def stock(log=print):
    """The nine stock Fragile Alliance levels, one line each, and the soldier rows they use."""
    rows = collections.Counter()
    log('%-4s %8s %6s %7s %8s %9s %8s %8s %7s %7s %6s' % ('', 'soldiers', 'squads', 'hit pts', 'hp mean', 'acc mean', 'later sq', 'later men', 'wiped', 'at start', 'bots'))
    out = {}
    for i in range(1, 10):
        L = 'F%02d' % i
        m = measure(L)
        t = m['totals']
        out[L] = t
        log('%-4s %8d %6d %7d %8.1f %9.1f %8d %8d %7d %7d %6d' % (
            L, t['soldiers'], t['squads with soldiers'], t['hit points (health added up)'], t['health mean'], t['accuracy mean (as used)'],
            t['squads not in the world at the load (field 3 = 0)'], t['soldiers in those'], t['squads with a wiped-out list'],
            t['named at the round start (AIMonitor 2)'], t['AI heisters']))
        for r in m['squads']:
            for _p, style, skill, acc, hp, _w, c in r['people']:
                rows[style, skill, round(acc), round(hp), c] += 1
        if t['named when the vehicle is called (monitor 4..7)']:
            log('     %s FILLS the monitor\'s vehicle-called lists' % L)
    log('soldier rows of the nine levels (style, skill, accuracy as used, health, weapon class): count')
    for (style, skill, acc, hp, c), n in rows.most_common(24):
        log('  %4d  %-12s %-9s accuracy %3d  health %3d  %s' % (n, style, skill, acc, hp, c))
    return out


def run_all(src, dst, parts, presets=False, log=print, car_exit=False, tags=None):
    import kl_maps
    res = collections.OrderedDict()
    if car_exit:
        teach_schema()                                  # the checkers of kl_maps.audit fit every object to its class
    for tag in tags or TAGS:
        a, b = os.path.join(src, tag), os.path.join(dst, tag)
        if not os.path.isdir(a):
            log('%s: no build in %s' % (tag, a))
            continue
        lines = []
        def say(s=''):
            lines.append(str(s)); log(s)
        apply(a, b, parts, presets, say, car_exit)
        A, B = compare(a, b, say)
        au = kl_maps.audit(b, log=lambda *_a: None)
        say('%s: kl_maps.audit: %s' % (tag, 'PASS (bad: 0, known: %d)' % len(au['known']) if not au['bad'] else 'FAIL: ' + '; '.join(au['bad'])[:500]))
        with open(os.path.join(b, 'map_ai_check.txt'), 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
        res[tag] = {'before': A['totals'], 'after': B['totals'], 'sizes before': A['sizes'], 'sizes after': B['sizes'], 'audit bad': au['bad']}
    with open(os.path.join(dst, 'map_ai_all.json'), 'w') as fh:
        json.dump(res, fh, indent=1)
    return res


def main():
    global HEALTH_SCALE
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    o = {x for x in sys.argv[1:] if x.startswith('--')}
    HEALTH_SCALE = next((float(x.split('=')[1]) for x in o if x.startswith('--health=')), HEALTH_SCALE)
    car = '--car-exit' in o
    parts = tuple(p for p in ('strength', 'waves', 'chains', 'escape') if '--no-' + p not in o)
    if len(a) == 2 and a[0] == 'table':
        show(measure(a[1]), routs='--short' not in o)
    elif a == ['stock']:
        stock()
    elif len(a) == 3 and a[0] == 'apply':
        apply(a[1], a[2], parts, '--presets' in o, car_exit=car)
    elif len(a) == 3 and a[0] == 'check':
        compare(a[1], a[2])
    elif len(a) >= 3 and a[0] == 'all':
        r = run_all(a[1], a[2], parts, '--presets' in o, car_exit=car, tags=a[3:] or None)
        sys.exit(1 if any(v['audit bad'] for v in r.values()) else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
