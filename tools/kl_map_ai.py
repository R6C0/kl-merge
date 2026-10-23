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
    python kl_map_ai.py balance <build folder | stock level> ... [--dist=10] [--diff=1]
                                                                       what a bullet costs whom: hits to kill
                                                                       between the player, the police and the AI
                                                                       heisters, per Arcade level and under
                                                                       klhook/klbalance.c's Risk dial (re/balance.md)
    python kl_map_ai.py apply <build folder> <out folder> [options]     the step: a FINISHED build (kl_maps ready)
                                                                       -> a copy with the AI changes. Only the .prp
                                                                       member of the archive changes
    python kl_map_ai.py retomoto-style <build> <out>                    any finished build (no plan needed): rows by
                                                                       weapon class + fall-back chains + spawnfix --auto
                                                                       (run order: apply, then spawnfix). NOT RUN IN THE GAME
    python kl_map_ai.py cops-style <build> <out>                        Retomoto's police pattern WITHOUT spawnfix, for a
                                                                       finished staged build (Vault, Last Call, Hasta): soldier rows
                                                                       by weapon class, SWAT-path squads to rifles and the
                                                                       auto plan's wiped-out chains. Timers, waves, escape, who
                                                                       is in the world and the posts stay as built. Only the .prp
                                                                       changes; refuses a non-empty out folder. NOT RUN IN THE GAME
        --health-only                     (apply / cops-style) strength raises the health floors only: accuracy, aim and
                                          skill names stay as built (default off)
        --retomoto-rows                   (apply / cops-style) the strength floors are Retomoto's own rows (kl_arms.ROWS:
                                          rifle/MG/sniper 75/50 hp 175, SMG/shotgun 50/50 hp 175, pistol 50/50 hp 100;
                                          accuracy x1.1 as used) instead of the eVeteran / eElite ladder (default off)
    python kl_map_ai.py pistol-row <installed level zip> <out folder>   2026-10-23 balance: ONLY the .prp member is rebuilt,
                                                                       pistol / revolver carriers lowered to the stock
                                                                       guard row (accuracy 55 as used, aim 50); proves
                                                                       by CRC that no other member differs. (--pistol-row
                                                                       does the same inside `apply`.)
    python kl_map_ai.py check <before> <after>                          the before / after table of one map
    python kl_map_ai.py all <z_maps folder> <out folder> [M02 ...] [options]   apply + check + kl_maps.audit on M01 M02
                                                                       M03 M06 (or the ones named)
    python kl_map_ai.py pairfix <build folder> [<out folder>] [--levels=M09_A,M09_B]
                                                                       a build made BEFORE 2026-10-11: the squad event
                                                                       lists, trigger-box bools and two enums the
                                                                       converter paired wrongly, put right in place
                                                                       (re/convert_audit.md). Without an out folder:
                                                                       the list of what would change, nothing written.
                                                                       It also says, list by list, where else the
                                                                       targets are named ('in play'). NOT RUN IN THE
                                                                       GAME; a run of its output is a load check, it
                                                                       cannot show the pairing (re/convert_audit.md 9).
    python kl_map_ai.py spawns <build folder> ...                       WHO PLOPS OUT (owner, 2026-10-11): every enemy
                                                                       squad - in the world from the load or hidden
                                                                       until a box / timer first names it, and from
                                                                       inside that box how near a man appears and
                                                                       whether in sight (collision ray). Read only
    python kl_map_ai.py spawnplan <build folder> [options]              what spawnfix would write, nothing written
    python kl_map_ai.py spawnfix <build folder> <out folder> [options]  a FINISHED build -> a NEW folder: squads in the
                                                                       world from the load (ZSquadScript field 3 = 1)
                                                                       and, on Retomoto's street, every man of the
                                                                       waves at a post of his own behind his cover
                                                                       point. Tables: kl_fa_author.HALL_ACTIVE,
                                                                       kl_fa_street.ACTIVE / POSTED / POST_*. Only .prp
                                                                       and .gms change. NOT RUN IN THE GAME
        --asleep=hall,wave1,wave2,wave3   Retomoto: these sets stay hidden until their box (posts are still laid)
        --active=<squad>,<squad>          these squads instead of the map's table (scene paths without the ROOT part)
        --auto                            also every squad the audit calls PLOP (the way to use it on another map)
        --no-posts                        nobody is moved
    python kl_map_ai.py spawndiff <build folder> <out folder>           entity by entity: only a squad's field 3, an
                                                                       enemy actor group's place and the AFTER_DEATH
                                                                       points may differ; exit 1 otherwise
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
    7  HEALTH        0x8fbac0: skipped with the 'GodActors' option or when < 0 (invulnerable; 0 is NOT skipped, it
                     is health 0); else a range of
                     the tuning table at field 7 per cent, times a team factor, times field 9..12 chosen by the
                     difficulty [0x156b5f0] (0..3), handed to the actor (virtual +0x674 / +0x670)
                     (2026-10-10, re/balance.md: the range is 0..100, so field 7 IS hit points; the 'team factor'
                     is the difficulty row's NPC health 0.5 / 0.9 / 1.15 / 1.3 - Arcade takes the story rows)
                     (2026-10-11, re/convert_audit.md 4: DEAD MEN's range is 50..175 - its 0x722090 is the same
                     function on tuning +0x110 / +0x114 - so a Dead Men '100' was 175 hit points there and is 100
                     here. The converter carries the number; the floors below happen to give the rifle class 175.)
    8  REGENERATION  virtual +0x67c -> 0x8f9bf0: seconds before health comes back and seconds until it is whole,
                     both 15 .. 1 at field 8 per cent; -1 = none (SWAT and the AI heisters: 50 = 8 s / 8 s)
    9..12            health factor per difficulty (new in Dog Days; 1.0 everywhere)
  In ARCADE a hit is also multiplied by one of six numbers by who shoots whom, per Arcade level (level 1: police ->
  you 0.1, you -> police 2.0, police -> AI heister 0.01): `balance` below, re/balance.md, klhook/klbalance.c.
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

THE LIST RULES (after re/map_tune_review.md, 2026-10-10; faults() must be empty or apply() writes nothing)
  F1  every reference-list entry is written with 'ROOT\\' (refs()); bare() counts the entries of the WHOLE level
      without it: no level of either game has one
  F2  no 'wiped out' list and no 'vehicle called' list reaches a VehicleEnter / VehicleMove rout (through timers,
      counters, random triggers; a GatePath stops the walk): a squad that is out is not sent to its car again
  F3  ... nor anything inside another squad that comes by car: its orders belong to its drive's end list
  order_faults() walks the written level, not the plan, so a by-passed exit node or a timer one step away counts.
"""
import collections, json, math, os, random, re, shutil, struct, sys, zipfile

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
ACC_CAP = None                                      # --acc-cap=N: no floor above N (accuracy as used); None = off (default, unchanged)
AIM_CAP = None                                      # --aim-cap=N: no aim floor above N (aim as used); None = off (default, unchanged). N=75 for rifles is a GUESS (kl-merge-3f)
HEALTH_ONLY = False                                 # --health-only: strength changes the health floors only; accuracy, aim and skill names stay as built (default off, unchanged)
RT_ROWS = False                                     # --retomoto-rows: the floors are Retomoto's own rows (kl_arms.ROWS by kl_arms.SKILL: cop 50/50 hp 100, swat 50/50 hp 175, sharp 75/50 hp 175) instead of the eVeteran/eElite ladder (default off, unchanged)
PISTOL_ROW = None                                   # --pistol-row: (accuracy as used, aim) a PISTOL / REVOLVER carrier is held to (LOWERED to it, never raised); None = off.
                                                    # 2026-10-23 (owner: the AI is 'a bit too op'): stock guard row = accuracy 55, aim 50 (re/balance_1023.md)
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

SQUAD_DEAD = 8                                      # ZSquadScript: the list sent when the squad is wiped out. READ in kl2.exe
                                                    # 2026-10-11 (re/convert_audit.md 1.2): the update 0x47e440 sends list 4
                                                    # = field 8 through 0x87ebf0 when no member is left. Field 4 = the first
                                                    # death, 5 = EVERY death, 6 = half dead, 7 = one left; 10 / 11 = something
                                                    # noticed / a hostile seen, 13 = a member is attacked.
                                                    # A Dead Men map built before that date has its 'attacked' lists in field
                                                    # 12 (an event Dead Men does not have: a player starts close combat on a
                                                    # member, kl2 0x42dfa0): kl_convert.SQUAD_LISTS was wrong. In Dog Days a
                                                    # CIVILIAN sends field 13 too (kl2 0x7b4918), in Dead Men only a soldier.
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
        # the transporter guards dead -> the police are CALLED (the counter -> the gate -> their drive). NOT their
        # hunt rout: the police hunt from their own HuntTimer, which their drive's end list starts (review F3:
        # a hunt order before the drive reaches four men who have not come yet)
        'AIEnemies!TransporterGuards': ['Triggers!ReinforcementsCounter'],
    },
    # the car is called: the police car comes if it has not (through its gate), and every squad that is ON FOOT
    # hunts. The police's own hunt rout is not named: it follows their drive (F3)
    'escape': ['AIEnemies!PoliceSwats\\Gate\\Way#01', 'AIEnemies!TransporterGuards\\HuntBehaviour',
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
    # TWO RULES of re/map_tune_review.md, kept by order_faults():
    #   F2  'Triggers!ArrivingCops_Timer' is named by NO list of this plan: after 2 s it runs
    #       ArrivingCops_Squad_02\VehicleEnterBehaviour, and a squad that is out and fighting would be sent INTO
    #       its car again (the rout that got it out is the one the conversion lost). Dead Men's own five boxes
    #       still name it. 'Triggers!Parkinglot_SWAT_Timer' is not named either: it names no enter rout, but the
    #       exit nodes of ArrivingCops_Squad_01 and ParkingLotSWAT_01 - with the by-pass their hunt / flank routs
    #       (found by order_faults; the review took it for harmless). The loading dock's flank is named directly.
    #   F3  the four squads that come by car (ParkingLotSWAT_01, ArrivingCops_Squad_01 / _02, EscSquad) get NO
    #       hunt / flank order from another squad's list or from the van call: until their VehicleEnterBehaviour
    #       runs their men stand at a holding place outside the navigation mesh (seen for EscSquad and
    #       ArrivingCops_Squad_01: (-10262, 702, -6304)). They hunt from their drive's end list, as in Dead Men.
    #   So the chains and the van call order the six men who are ON FOOT (the hall's three squads, the loading dock).
    'chains': {
        # a squad of the hall down -> the others hunt and the loading dock comes round
        'AI_Enemies!BankMainSquad_01': ['AI_Enemies!BankMainSquad_02\\HuntBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour', 'AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour'],
        'AI_Enemies!BankMainSquad_02': ['AI_Enemies!BankMainSquad_01\\HuntBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour', 'AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour'],
        'AI_Enemies!BankMainSquad_03': ['AI_Enemies!BankMainSquad_01\\HuntBehaviour', 'AI_Enemies!BankMainSquad_02\\HuntBehaviour', 'AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour'],
        'AI_Enemies!LoadingDockSquad_01': ['AI_Enemies!BankMainSquad_01\\HuntBehaviour', 'AI_Enemies!BankMainSquad_02\\HuntBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour'],
        # a car squad down -> the men on foot come to the place
        'AI_Enemies!ParkingLotSWAT_01': ['AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'AI_Enemies!BankMainSquad_02\\HuntBehaviour'],
        'AI_Enemies!ArrivingCops_Squad_01': ['AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'AI_Enemies!BankMainSquad_01\\HuntBehaviour'],
        'AI_Enemies!ArrivingCops_Squad_02': ['AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'AI_Enemies!BankMainSquad_03\\HuntBehaviour'],
        'AI_Enemies!EscSquad': ['AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'AI_Enemies!BankMainSquad_02\\HuntBehaviour'],
    },
    # the van is called: everybody on foot hunts. No car is sent for and no car squad is ordered (F2, F3); the
    # map's own box Triggers!EscSquad_Triggere on the way to the van still brings the escape squad's car
    'escape': ['AI_Enemies!LoadingDockSquad_01\\FlankingBehaviour', 'AI_Enemies!BankMainSquad_01\\HuntBehaviour',
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
def plan_id(m_name):
    """A short id of a map's plan and of the way lists are written (map_ai.json 'plan'): two builds with the
    same id got the same orders. kl_map_tune compares a tuned map with the ai step run alone only then."""
    import hashlib
    return hashlib.sha1(json.dumps([PLANS[m_name], STRENGTH, 'refs: always ROOT', DRIVE, RELAY, GATE], sort_keys=True).encode()).hexdigest()[:12]


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
    """Field unit i = v in the token kind the field has (as kl_fa_author.setv); a reference list is written
    as given - put() hands it over through refs() (always with ROOT)."""
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


def refs(sc, name, paths):
    """A reference list as it is WRITTEN: every entry with 'ROOT\\', always (an empty string stays empty).
    WHY (re/map_tune_review.md F1): until 2026-10-10 this took 'the form the controller's lists have in this
    level' by majority, and a controller whose lists were all empty (the escape monitor's, on every Dead Men map)
    counted 0 > 0 = 'without': 33 entries went out as 'AI_Enemies!...'. The census says there is ONE form: 21
    stock levels have 30,406 + 5,845 entries with ROOT\\ and none without that is not empty; Dead Men's own
    levels and every build that ran in the game have none either. bare() / faults() keep it that way."""
    return [full(p) if p else p for p in paths]


def bare(sc):
    """Every NON-EMPTY entry of every reference list of the level (all nodes, their own properties and all
    their controllers - not only the lists this tool writes) that does not start with 'ROOT\\'. Must be empty:
    no level of either game and no build that ran has one (re/map_tune_review.md F1)."""
    out = []
    for k in range(1, len(sc.nodes)):
        nd = sc.nodes[k]
        for name, obj in [('(node)', nd['props'])] + [(sc.p.key(nm), b) for nm, b in nd['ctrls']]:
            for fi, u in enumerate(units(obj[1:-1])):
                if u[0][0] == 0x04 and len(u) > 1 and u[1][0] == 0x0c:
                    for x in u[1:]:
                        s = sc.p.key(x)
                        if s and s[:5].upper() != R.upper():
                            out.append('%s %s[%d]: %r is written without ROOT\\' % (sc.path[k], name, fi, s))
    return out


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
        if RT_ROWS:                                     # Retomoto's rows: accuracy, aim, health (_ROW indices 0, 1, 3) of kl_arms.ROWS[kl_arms.SKILL[cls]]
            row = kl_arms.ROWS[kl_arms.SKILL[cls]][1]
            acc, aim, hp = min(row[0] * fac, 100.0), float(row[1]), row[3]
        if ACC_CAP is not None:
            acc = min(acc, ACC_CAP)
        if AIM_CAP is not None:
            aim = min(aim, AIM_CAP)
        e, new = effective(v), {}
        if not HEALTH_ONLY and (e[ACC] < acc - 0.01 or e[AIM] < aim - 0.01):
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
    if PISTOL_ROW:
        rep += pistol_row(sc, log)
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


GATED = ('Wave', 'Reinforcement', 'Teargas', 'Garrison', 'Staged', 'COOP', 'merc_bot', 'bank_waves', 'Escort', 'Gate')
RUSH_ROUTS = ('HuntBehaviour', 'FlankingBehaviour', 'DefendBehaviour')


def _natkey(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', p)]


def autoplan(sc, same_part=False):
    """A plan for a map nobody wrote one for (The Vault, or any finished build). Three parts, all from the build:
      chains   squads of one parent group in natural path order (Squad_2 before Squad_10); when one is wiped out
               its list names the NEIGHBOUR'S behaviour rout (Hunt, else Flanking, else Defend: the rout's own
               children, as the hand plans do), not the squad node, so the neighbour moves. Squads that already
               have a list keep it; vehicle squads, Allies and gated spawns (GATED) are left out.
      arms     a squad whose path says SWAT/Assault gets rifles (kl_arms 'rifle'). GUESS: Retomoto's FORCE gave the
               rushers pistols and the holders SMG / rifle by role; the path names are the only role there is.
      unleash  an eStayBack squad of mostly pistol carriers that owns a Hunt or Flanking rout becomes eUnleashed
               (stock has 3..13 a level; Retomoto unleashes its rushers). GUESS: pistol men are the rushers.
    GUESS: path order is neighbour order (the Dead Men authors numbered squads along the route).
    same_part (OPTION, default off = unchanged): keep only chains whose two squads sit in one level part, i.e. share the
    path up to the last '!' (GamePlay!4_Vault_Part!Guards_01 -> ...Guards_02, never 3_Garage_Part -> 4_Vault_Part).
    On the Vault the two cross-part chains would wake the next part's guards before the door beat. GUESS: that prefix is the part."""
    by = collections.OrderedDict()
    arms, unleash = {}, []
    ff = kl_arms.fields()
    for k in range(1, len(sc.nodes)):
        cs = [n for _i, n, _v in ctrls(sc, k)]
        if 'ZSquadScript' not in cs or any('Vehicle' in n for n in cs):
            continue
        men = [c for c in range(k + 1, sc.end[k]) if sc.cls(c) == 'ZFFActor' and any(n == 'ZSoldier' for _i, n, _v in ctrls(sc, c))]
        if not men or any(sc.cls(c) == 'ZFFActor' and kl_fa.node_values(sc, c)[J.labels('dd', 'ZFFActor').index('ZFFActor[0]')] == 'Ally' for c in men):
            continue
        if any(w.lower() in sc.path[k].lower() for w in GATED):
            continue      # timed / gated spawns carry their own wiring
        _i, _n, v = ctrl(sc, k, 'ZSquadScript')
        routs = {}
        for c in range(k + 1, sc.end[k]):
            leaf = sc.path[c].rsplit(chr(92), 1)[-1]
            for r in RUSH_ROUTS:
                if r in leaf and r not in routs:
                    routs[r] = sc.path[c]
        wc = collections.Counter(weapon_class(kl_fa.node_values(sc, c)[ff[0]].rsplit(chr(92), 1)[-1]) for c in men)
        low = sc.path[k].lower()
        if 'swat' in low or 'assault' in low:
            arms[sc.path[k]] = 'rifle'
        if v[0] == 'eStayBack' and (routs.get('HuntBehaviour') or routs.get('FlankingBehaviour'))                 and wc.get('pistol', 0) * 2 > len(men):
            unleash.append(sc.path[k])
        if v[SQUAD_DEAD]:
            continue
        target = routs.get('HuntBehaviour') or routs.get('FlankingBehaviour') or routs.get('DefendBehaviour')
        if target:
            by.setdefault(sc.path[k].rsplit(chr(92), 1)[0], []).append((sc.path[k], target))
    chain = {}
    for _g, sq in by.items():
        sq.sort(key=lambda t: _natkey(t[0]))
        for (a, _ta), (b_, tb) in zip(sq, sq[1:]):
            if same_part and a.rsplit('!', 1)[0] != b_.rsplit('!', 1)[0]:
                continue
            chain[a] = [tb]
    return {'what': 'auto plan: %d chains, %d SWAT squads to rifles, %d unleashed' % (len(chain), len(arms), len(unleash)),
            'arms': arms, 'unleash': unleash, 'timers': {}, 'counters': {}, 'start': None, 'chains': chain, 'escape': []}


def retomoto_style(src, dst, log=print):
    """Retomoto's police pattern on any finished build: soldier rows by weapon class (floors), the auto plan's
    arms / unleash / fall-back chains, then spawnfix --auto (squads in the world from the load, men posted at
    cover points). Refuses dst == src and a dst that already holds something; the stage-1 folder is removed."""
    dst = dst.rstrip('/' + chr(92))
    if os.path.abspath(dst) == os.path.abspath(src.rstrip('/' + chr(92))):
        raise ValueError('the output folder is the source')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: not overwritten' % dst)
    tmp = dst + '_stage1'
    if os.path.isdir(tmp):
        raise ValueError('%s is left from an earlier run: delete it first' % tmp)
    try:
        rep = apply(src, tmp, parts=('strength', 'waves', 'chains'), log=log, auto=True)
        sf = spawnfix(tmp, dst, {'auto': True, 'posts': True, 'asleep': (), 'active': None}, log)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rep, sf


def cops_style(src, dst, log=print, strength_only=False, same_part=False, chains_only=False):
    """retomoto_style without its last step (spawnfix --auto would wake every squad of a staged build): apply with
    parts strength + chains and the auto plan. -> the apply report. Refuses dst == src and a non-empty dst."""
    dst = dst.rstrip('/' + chr(92))
    if os.path.abspath(dst) == os.path.abspath(src.rstrip('/' + chr(92))):
        raise ValueError('the output folder is the source')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: not overwritten' % dst)
    return apply(src, dst, parts=('chains',) if chains_only else ('strength',) if strength_only else ('strength', 'chains'), log=log, auto=True, same_part=same_part)


def apply(src, dst, parts=('strength', 'waves', 'chains', 'escape'), presets=False, log=print, car_exit=False, auto=False, same_part=False):
    """A finished build folder -> folder dst: the archive with a new .prp member, every other member and every
    file beside it copied. -> report dict (also written to <dst>/map_ai.json and map_ai.txt)."""
    import kl_graft
    zp = archive_of(src)
    m_name = map_of(src) or ('auto' if auto else None)
    if m_name not in PLANS and not auto:
        raise ValueError('%s: no plan for %r (plans: %s)' % (src, m_name, ', '.join(PLANS)))
    if os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the output folder is the build\'s own')
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    # auto: the hand plans are the campaign-FA maps' own (a Vault is M03_A, not M03_FA_A)
    plan = autoplan(sc, same_part) if auto else PLANS[m_name]
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if data != files[ext['.prp']] or bad:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte (%d misfits): not changed' % len(bad))
    lines = []
    def say(s):
        lines.append(str(s)); log(s)
    say('kl_map_ai: %s (%s): %s' % (m_name, zp, plan['what']))
    rep = collections.OrderedDict(map=m_name, source=zp, parts=list(parts), presets=presets, car_exit=car_exit, health_scale=HEALTH_SCALE,
                                  plan='auto' if auto else plan_id(m_name))
    if 'strength' in parts:
        rep['strength'] = strength(sc, files[ext['.ANM']], plan, say, presets)
    if 'waves' in parts:
        rep['cars'] = cars(sc, m_name, car_exit, say) if m_name in PLANS else []
        rep['waves'] = waves(sc, plan, say)
    if 'chains' in parts:
        rep['chains'] = chains(sc, plan, say)
    if 'escape' in parts:
        rep['escape'] = escape(sc, plan, say)
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if bad:
        raise ValueError('%d objects do not fit their class after the changes: %s' % (len(bad), bad[:3]))
    rep['dangling'] = faults(sc)                    # names nothing / written without ROOT / order rules F2, F3
    if rep['dangling']:
        raise ValueError('reference lists at fault (nothing is written): %s' % rep['dangling'][:8])
    say('  kl_map_ai: lists: 0 entries that name nothing, 0 without ROOT in the whole level, 0 against the order rules')
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


def pistol_row(sc, log=print, row=None, classes=('pistol', 'revolver')):
    """Pistol / revolver carriers (not AI heisters, not eDog) are LOWERED to the stock guard row: accuracy as used
    55, aim 50 (PISTOL_ROW or `row`). Riflemen, SMG and shotgun men are not looked at. A preset skill name becomes
    eCustom with its preset numbers first (as strength() does), then the two numbers are capped. Health unchanged.
    -> report rows [(actor, what changed)]."""
    # classes (2026-10-23, --row-classes=rifle,smg,... --row=75,70): the same LOWER-only cap for other weapon classes.
    # Accuracy is the value AS THE GAME USES IT (effective(): preset written over it, x1.1 for No_Mercenary, clamp 100),
    # so a cap of 75 means 75 in play and the stored number is written as 75/1.1 for a No_Mercenary man. Aim is capped
    # as stored/preset (no factor). What aim MEANS in play is unproven; an aim cap such as 70 is a GUESS.
    # Only men above the cap change; Ally (AI heisters) and eDog are never touched.
    row = row or PISTOL_ROW
    acc_t, aim_t = float(row[0]), float(row[1])
    f, rep = kl_arms.fields(), []
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
            continue
        cls = weapon_class(nv[f[0]].rsplit('\\', 1)[-1])
        if cls not in classes or v[STYLE] == 'eDog':
            continue
        fac = ACC_FACTOR if v[MERC] == 'No_Mercenary' else 1.0
        e, new = effective(v), {}
        if e[ACC] <= acc_t + 0.01 and e[AIM] <= aim_t + 0.01:
            continue
        if v[SKILL] != 'eCustom':
            new[SKILL] = 'eCustom'
            for fi, x in zip(PRESET_FIELDS, PRESET[v[SKILL]]):
                new[fi] = float(x)
        new[ACC] = min(new.get(ACC, v[ACC]), round(acc_t / fac, 1))
        new[AIM] = min(new.get(AIM, v[AIM]), aim_t)
        new = {fi: x for fi, x in new.items() if x != v[fi]}
        if new:
            kl_fa.edit(sc, k, i, lambda us, new=new: [setv(sc, us, fi, x) for fi, x in new.items()])
            after = effective([new.get(fi, x) for fi, x in enumerate(v)])
            rep.append((sc.path[k], '%s: row: accuracy as used %s -> %s, aim %s -> %s' % (
                cls, _n(round(e[ACC], 1)), _n(round(after[ACC], 1)), _n(e[AIM]), _n(after[AIM]))))
    log('  kl_map_ai: row (accuracy %g, aim %g) for %s: %d men lowered' % (acc_t, aim_t, '/'.join(classes), len(rep)))
    return rep


def pistol_zip(zp, dst, log=print, row=(55, 50), classes=('pistol', 'revolver')):
    """An INSTALLED (or any) Dog Days level archive -> folder dst: the same archive with ONLY the .prp member rebuilt,
    pistol carriers held to the stock guard row. The source is read, never written. Proves per member (CRC, size)
    that nothing but the .prp differs. -> report dict."""
    import kl_graft
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    data, bad, _p, _n2 = J.check(sc, log=lambda *_a: None)
    if data != files[ext['.prp']] or bad:
        raise ValueError('%s: the .prp does not re-serialise byte for byte (%d misfits): not changed' % (zp, len(bad)))
    rows = pistol_row(sc, log, row, classes)
    data, bad, _p, _n2 = J.check(sc, log=lambda *_a: None)
    if bad:
        raise ValueError('%d objects do not fit their class after the changes: %s' % (len(bad), bad[:3]))
    if faults(sc):
        raise ValueError('reference lists at fault: %s' % faults(sc)[:5])
    arms = kl_arms.check(sc, files[ext['.ANM']])
    if any(s == 1 for s, _c, _t in arms):
        raise ValueError('kl_arms.check: %s' % arms)
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, data if n == ext['.prp'] else files[n]) for n in order])
    with zipfile.ZipFile(zp) as a, zipfile.ZipFile(out) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename for i in ia] != [i.filename for i in ib]:
            raise ValueError('member list or order differs')
        diff = [x.filename for x, y in zip(ia, ib) if (x.CRC, x.file_size) != (y.CRC, y.file_size)]
    if diff != [ext['.prp']] and not (not rows and diff == []):
        raise ValueError('more than the .prp differs: %s' % diff)
    log('kl_map_ai: written %s; members that differ (CRC / size): %s' % (out, diff))
    rep = {'source': zp, 'out': out, 'changed': rows, 'members differ': diff}
    with open(os.path.join(dst, 'pistol_row.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    return rep


DRIVE = ('VehicleMoveBehaviourRout', 'VehicleEnterBehaviourRout')      # a squad with one of these COMES BY CAR
RELAY = ('TriggerDelay', 'TriggerDelay2', 'TriggerCounter', 'RandomTrigger')    # pass an order on (their lists are followed)
GATE = ('GatePath',)                                # lets an order through once (Dead Men put one before M02's car):
                                                    # ASSUMPTION, as re/map_ai.md 11; the walk stops there


def order_faults(sc):
    """The two order rules of re/map_tune_review.md on the lists that run LATE in a round - every squad's
    'wiped out' list (ZSquadScript field 8) and the escape monitor's 'vehicle n called' lists (fields 4..7).
    Each entry is followed through timers, counters and random triggers (not through a gate):
      F2  it must not reach a VehicleEnter / VehicleMove rout: a squad that has driven and is out fighting
          would be sent to its car again (M03: Triggers!ArrivingCops_Timer)
      F3  it must not reach a rout or timer INSIDE another squad that comes by car: that squad's orders belong
          to its drive's end list; before the drive its men are not at the place (M02 PoliceSwats, M03 EscSquad,
          ArrivingCops_Squad_01). A gate before the drive is the one thing of such a squad a list may name.
    The source builds have all these lists empty, so every finding is something a step wrote. -> texts."""
    names = lambda k: [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
    squads = [k for k in range(1, len(sc.nodes)) if kl_fa.has(sc, k, 'ZSquadScript')]
    drives = {k for k in squads if any(set(names(c)) & set(DRIVE) for c in range(k + 1, sc.end[k]))}
    def squad_of(c):
        hit = [k for k in squads if k < c < sc.end[k]]
        return max(hit) if hit else None                # the innermost
    lists = [(k, 'ZSquadScript', SQUAD_DEAD, v[SQUAD_DEAD]) for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript')]
    lists += [(k, 'OnlineEscVehicleMonitor', fi, v[fi]) for k, _i, v in kl_fa.controllers(sc, 'OnlineEscVehicleMonitor') for fi in range(4, 8)]
    out = []
    for owner, cname, fi, entries in lists:
        todo, seen = [(p, '') for p in entries if isinstance(p, str) and p], set()
        while todo:
            p, via = todo.pop(0)
            for c in sc.resolve(full(p)):
                if c in seen:
                    continue
                seen.add(c)
                cn = names(c)
                where = '%s %s[%d]: %s%s' % (sc.path[owner][5:], cname, fi, sc.path[c][5:], ' (through %s)' % via.strip(' >') if via else '')
                if set(cn) & set(GATE):
                    continue
                if set(cn) & set(DRIVE):
                    out.append('F2 %s sends a squad to its car, with no gate before it' % where)
                    continue
                s = squad_of(c)
                if s in drives and s != owner:
                    out.append('F3 %s orders the car squad %s outside its drive' % (where, sc.path[s][5:]))
                    continue
                for _i, n, v in ctrls(sc, c):
                    if n in RELAY:
                        todo += [(q, '%s > %s' % (via, sc.path[c][5:])) for x in v if isinstance(x, list) for q in x if isinstance(q, str) and q]
    return out


def faults(sc):
    """Everything that must be empty on a level this tool wrote (apply() refuses to write otherwise;
    kl_map_tune's checker 'kl_map_ai' runs it on the written folder):
      - entries of the lists this tool writes that name nothing. The entry is resolved AS WRITTEN: until
        2026-10-10 the prefix was added before the look-up, which is why F1 passed
      - bare(): any reference-list entry of the whole level without ROOT (F1)
      - order_faults(): the order rules F2 and F3."""
    out = []
    for name, fs in (('ZSquadScript', range(4, 19)), ('AIMonitor', (START_LIST,)), ('OnlineEscVehicleMonitor', range(0, 9))):
        for k, _i, v in kl_fa.controllers(sc, name):
            for fi in fs:
                for p in v[fi] if isinstance(v[fi], list) else ():
                    if p and not sc.resolve(p):
                        out.append('%s %s[%d]: %s names nothing' % (sc.path[k], name, fi, p))
    return out + bare(sc) + order_faults(sc)


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


# ------------------------------------------------------------------ what a bullet costs whom (re/balance.md)
# Read in kl2.exe 2026-10-10 (section 13 of re/map_ai.md has the short form). klhook/klbalance.c writes the same
# numbers at run time: keep ARCADE and RISK in step with its klr_code / klr_dial.
FACTORS = ('police->crew', 'crew->police', 'police->you', 'you->police', 'crew->you', 'you->crew')
ARCADE = {                                          # Arcade level: the six floats at R+0x00..+0x14 (0x524050)
    1: (0.01, 3.0, 0.1, 2.0, 0.1, 0.25), 2: (0.05, 2.6, 0.2, 1.75, 0.2, 0.5), 3: (0.1, 2.2, 0.4, 1.5, 0.4, 1.0),
    4: (0.15, 1.9, 0.8, 1.25, 0.8, 0.9), 5: (0.2, 1.6, 1.0, 1.0, 1.0, 0.8), 6: (0.25, 1.3, 1.3, 0.9, 1.1, 0.7),
    7: (0.3, 1.0, 1.6, 0.8, 1.2, 0.6), 8: (0.35, 0.8, 1.9, 0.7, 1.3, 0.5), 9: (0.4, 0.4, 2.2, 0.6, 1.4, 0.4),
    10: (0.45, 0.2, 2.6, 0.5, 1.5, 0.3), 11: (0.5, 0.1, 3.0, 0.3, 1.7, 0.1)}
RAMP = (1, -1, 1, -1, 1, 0)                         # klbalance.c Ramp=1: at least stock / at most stock / as given
RISK = {                                            # [Balance] Risk: the six factors, the player's health factor, his
    1: ((0.5, 1.5, 0.5, 1.5, 0.5, 1.0), 1.0, None),         # regeneration (s before it starts, s to be whole; None = stock)
    2: ((1.0,) * 6, 0.73, (8.0, 8.0)),
    3: ((1.0,) * 6, 0.51, (8.0, 8.0))}
DIFF_HEALTH = (0.5, 0.9, 1.15, 1.3)                 # NPC health by the campaign difficulty option (tuning +0x434 .. : 0x831f00)
PLAYER_HEALTH, PLAYER_REGEN = 550.0, (4.0, 4.0)     # Arcade: tuning +0x614, +0x60c, +0x610 (0x4206f0, 0x410781, 0x6ef3e9)
BODY_NPC = {'head': 10.0, 'body': 1.0, 'types 4, 7': 0.5, 'types 6, 9': 0.2}       # 0x572f60, floats at 0xcdefe4..
BODY_PLAYER = {k: 1.0 + (min(v, 4.0) - 1.0) * 0.25 for k, v in BODY_NPC.items()}   # 0x4db7ff: head 1.75
# ZFFItemTemplateWeapon / ZFFItemTemplateAmmo fields, by the object offsets 0x46ef60 reads (offset = record + 4)
W_AMMO, W_RANGE, W_MULT, W_RPM, W_NPC, W_MP, W_BAND = 18, (21, 22, 23, 24), 25, 27, 37, 38, (39, 40, 41, 42)
A_DAMAGE = (17, 18, 19, 20)


def factors(level, risk=0, ramp=True):
    """The six factors of an Arcade level as the game has them (risk 0) or as klbalance.c writes them."""
    stock = ARCADE[min(max(level, 1), 11)]
    if not risk:
        return stock
    return tuple(s if ramp and ((k > 0 and s > d) or (k < 0 and s < d)) else d for d, s, k in zip(RISK[risk][0], stock, RAMP))


def guns(sc):
    """{weapon template: {'r' 4 ranges, 'd' the ammo's 4 damages, 'mult', 'npc', 'mp', 'band' 4, 'rpm'}} of a level."""
    out = {}
    for name, t in kl_arms.equipment(sc).items():
        k = next(iter(sc.resolve(t['path'])), None)
        v = kl_fa.node_values(sc, k) if k else None
        if not v or len(v) <= W_BAND[-1] or not v[W_AMMO]:
            continue
        a = sc.resolve(full(v[W_AMMO][0]))
        if len(a) != 1:
            continue
        av = kl_fa.node_values(sc, a[0])
        out[t['name']] = {'r': [v[i] for i in W_RANGE], 'd': [av[i] for i in A_DAMAGE], 'mult': v[W_MULT], 'npc': v[W_NPC],
                          'mp': v[W_MP], 'band': [v[i] for i in W_BAND], 'rpm': v[W_RPM]}
    return out


def bullet(g, dist, npc):
    """Damage of one bullet in an Arcade round before the who-shoots-whom factor and the body part (0x46ef60), or
    None for a weapon that is not a bullet gun (a range or damage of -1: grenades, launchers, the sniper rifle)."""
    r, d = g['r'], g['d']
    if min(r) <= 0 or min(d) < 0:
        return None

    def join(i):
        return d[i] if r[i + 1] <= r[i] else d[i] + (d[i + 1] - d[i]) * (dist - r[i]) / (r[i + 1] - r[i])
    if dist <= r[0]:
        dmg, band = d[0], 0
    elif dist <= r[1]:
        dmg, band = join(0), 0
    elif dist <= r[2]:
        dmg, band = join(1), 1
    elif dist <= r[3]:
        dmg, band = join(2), 2
    else:
        dmg, band = d[3], 3
    return dmg * g['mult'] * (g['npc'] if npc else g['mp']) * g['band'][band]


def crowd(sc):
    """-> {team: [(weapon template, health, ZSoldier field 8)]} of every ZFFActor with a ZSoldier."""
    lab, f = J.labels('dd', 'ZFFActor'), kl_arms.fields()
    team, out = lab.index('ZFFActor[0]'), collections.defaultdict(list)
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) != 'ZFFActor':
            continue
        sol = next((v for _i, n, v in ctrls(sc, k) if n == 'ZSoldier'), None)
        if sol is not None:
            nv = kl_fa.node_values(sc, k)
            out[nv[team]].append((nv[f[0]].rsplit('\\', 1)[-1], sol[HEALTH], sol[F8]))
    return out


def _span(v):
    v = sorted(v)
    if not v:
        return '-'
    m = v[len(v) // 2]
    return '%d' % m if v[0] == v[-1] else '%d (%d-%d)' % (m, v[0], v[-1])


def balance(src, dist=10.0, diff=1, gun='Rifle_zastavam85', log=print):
    """Hits to kill, body shots at <dist> metres, no regeneration: for every armed enemy of the level against the
    player and an AI heister and back, on five stock Arcade levels and under klbalance.c's three Risk rows.
    Shotguns are left out of the counts (a shell is several pellets; their number was not read). -> the rows."""
    sc = kl_fa.load(archive_of(src))[0]
    G, C = guns(sc), crowd(sc)
    hits = lambda hp, dmg: int(math.ceil(hp / dmg - 1e-6)) if dmg > 0 else 10 ** 6
    cops = [(w, h) for t in ('Enemy', 'Enemy2') for w, h, _r in C.get(t, ()) if w in G and weapon_class(w) != 'shotgun' and bullet(G[w], dist, True)]
    crew = [(w, h) for w, h, _r in C.get('Ally', ()) if w in G and bullet(G[w], dist, True)]
    mine = bullet(G[gun], dist, False)
    log('%s: %d armed police / guards counted (%d shotguns left out), %d AI heisters; body shots at %.0f m; NPC health x %.2f (difficulty option %d); the player shoots a %s (%.1f a bullet)' % (
        os.path.basename(os.path.dirname(archive_of(src))) or src, len(cops), sum(weapon_class(w) == 'shotgun' for t in ('Enemy', 'Enemy2') for w, _h, _r in C.get(t, ())),
        len(crew), dist, DIFF_HEALTH[diff], diff, gun, mine))
    log('  a bullet at %.0f m, from an NPC / from the player: %s' % (dist, ', '.join('%s %.0f / %.0f' % (w, bullet(G[w], dist, True), bullet(G[w], dist, False))
                                                                           for w in sorted({w for w, _h in cops + crew}))))
    log('  %-22s %6s  %-14s %-14s %-14s %-14s %-12s %-12s' % ('', 'you', 'police kill', 'you kill a', 'police kill', 'a heister', 'a heister', 'you kill a'))
    log('  %-22s %6s  %-14s %-14s %-14s %-14s %-12s %-12s' % ('hits to kill', 'health', 'you', 'policeman', 'a heister', 'kills police', 'kills you', 'heister'))
    rows = []
    for name, lvl, risk in [('stock, Arcade level %d' % L, L, 0) for L in (1, 3, 5, 8, 11)] + [('Risk=%d (level %d)' % (r, L), L, r) for r in (1, 2, 3) for L in (1, 11)]:
        a, b, c, d, e, f = factors(lvl, risk)
        php = PLAYER_HEALTH * (RISK[risk][1] if risk else 1.0)
        k = DIFF_HEALTH[diff]
        row = (name, php,
               _span([hits(php, bullet(G[w], dist, True) * c) for w, _h in cops]),
               _span([hits(h * k, mine * d) for _w, h in cops]),
               _span([hits(bh * k, bullet(G[w], dist, True) * a) for w, _h in cops for _bw, bh in crew[:1]]),
               _span([hits(h * k, bullet(G[bw], dist, True) * b) for _w, h in cops for bw, _bh in crew[:1]]),
               _span([hits(php, bullet(G[bw], dist, True) * e) for bw, _bh in crew[:1]]),
               _span([hits(bh * k, mine * f) for _bw, bh in crew[:1]]))
        rows.append(row)
        log('  %-22s %6.0f  %-14s %-14s %-14s %-14s %-12s %-12s' % row)
    return rows


# ------------------------------------------------------------------ pairfix: the converter's pairings found wrong on 2026-10-11
# re/convert_audit.md. kl_convert is corrected, so a build made from now on is right; this step puts a build made
# BEFORE that date right without re-making it (values and reference lists of objects it already has; only the .prp
# member changes). It touches an object only when (a) the object has the scene path of a Dead Men object of the
# build's own Dead Men level(s) and (b) it still holds exactly what the old converter wrote there.
#
# WHAT A LIVE RUN OF A pairfix BUILD CAN SHOW (review of 2026-10-11, re/convert_audit.md 9): that it loads and plays
# as before - NOT that the pairing is right. On the five builds of the tab every target of a moved list is also
# reached through a list that was always in its place (the same squad's 'a hostile is seen' list, another squad's,
# a counter, a trigger box), and KLHook.log has no line for a squad event. The proof of the pairing is the code of
# both exes. pairfix therefore prints, for every list it moves, where else its targets are named ('in play').
OLD_SQUAD_LISTS = (0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13)     # kl_convert.SQUAD_LISTS until 2026-10-11
SQUAD_FIRST = 4                                                 # ZSquadScript: the Dog Days field of list 0 (Dead Men: 3)
LIST_NAME = ('the first member is dead', 'half the squad is dead', 'one member is left', 'the squad is wiped out',
             'something is noticed', 'a hostile is seen', 'a member is attacked', '(Dead Men list 7)', 'VehicleDead',
             'DriverDead', '(Dead Men list 10)', '(Dead Men list 11)')
DD_LIST_NAME = ('the first member is dead', 'EVERY death', 'half the squad is dead', 'one member is left',
                'the squad is wiped out', '(Dog Days list 5)', 'something is noticed', 'a hostile is seen',
                'a player starts close combat on a member', 'a member is attacked', '(Dog Days list 10)', 'VehicleDead',
                'DriverDead', '(Dog Days list 13)', '(Dog Days list 14)')


def _named(sc, skip=()):
    """{lower-case scene path: [(node, controller name, field)]} of every reference-list entry of every controller
    of the scene, without the ZSquadScript lists (node, field) in skip."""
    out = {}
    for k in range(1, len(sc.nodes)):
        for nm, body in sc.nodes[k]['ctrls']:
            n = sc.p.key(nm)
            for i, u in enumerate(units(body[1:-1])):
                if u[0][0] != 0x04 or (n == 'ZSquadScript' and (k, i) in skip):
                    continue
                x = kl_fa.value(sc, u)
                if isinstance(x, list):
                    for s in x:
                        if isinstance(s, str) and s:
                            out.setdefault(s.lower(), []).append((k, n, i))
    return out


def _squad_members(sc, k):
    """(soldiers, civilians) of the squad at node k, as the level file has them."""
    names = [sc.p.key(nm) for j in range(k, sc.end[k]) for nm, _b in sc.nodes[j]['ctrls']]
    return names.count('ZSoldier'), names.count('ZCivilian')


def dead_men_levels(src):
    """The Dead Men levels a build folder was made from (result.json of kl_maps: 'M' and, for the two-part
    Retomoto build, the level named in 'tag')."""
    import re
    d = src if os.path.isdir(src) else os.path.dirname(src)
    rj = os.path.join(d, 'result.json')
    if not os.path.isfile(rj):
        return []
    r = json.load(open(rj))
    out = [r['M']] if str(r.get('M', '')).startswith('M') else []
    out += [m for m in re.findall(r'M\d\d(?:_FA)?_[A-Z]', str(r.get('tag', ''))) if m not in out]
    return out


def _dead_men(levels):
    """{lower-case scene path: {controller name or '(node)': (class, [Dead Men field values])}} of the objects
    pairfix looks at, from the stock Dead Men levels (map side only: the graft drops the rest)."""
    want = ('ZSquadScript', 'TriggerBox', 'HeliFlyBehaviourRout')
    out = {}
    for lv in levels:
        sc = J.Scene.load(lv, 'dm')
        side = J.sides(sc)
        for k in range(1, len(sc.nodes)):
            if side[k] != 'map':
                continue
            nd = sc.nodes[k]
            for nm, body in nd['ctrls']:
                n = sc.p.key(nm)
                if n in want:
                    out.setdefault(sc.path[k].lower(), {})[n] = (n, [kl_fa.value(sc, u) for u in units(body[1:-1])])
            if sc.cls(k) == 'ZHavokRigidBody':
                lab = J.labels('dm', 'ZHavokRigidBody')
                out.setdefault(sc.path[k].lower(), {})['(node)'] = ('ZHavokRigidBody', kl_fa.node_values(sc, k)[lab.index('ZHavokRigidBody[2]')])
    return out


def pairfix(src, dst=None, levels=None, log=print):
    """A finished build folder made before 2026-10-11 -> folder dst with the four things the converter paired
    wrongly put right (dst None: only the report, nothing is written). -> report dict.
      squads   the event lists of a Dead Men squad sit in the list the old kl_convert.SQUAD_LISTS gave: each list
               Dead Men had entries in is moved to the list of the same event (kl_convert.SQUAD_LISTS now)
      boxes    a Dead Men TriggerBox with 'another actor enters' (Dead Men field 7) has it in Dog Days field 8
               ('the last of them leaves'): moved to field 7
      enums    HeliFlyBehaviourRout FRONT_GUN / LAUNCHER and a rigid body's PRIORITY_CRITICAL that became Dog Days'
               usual value (kl_convert.ENUM_RENAME)
      right    what is in its place already (a second run on its own output lists everything here and moves nothing)
      play     for every moved list: how many of its targets are also in a list of the same squad whose pairing never
               changed, how many more another object names, how many nothing else names. Read off the lists, NOT RUN.
    Not here: ZFFActor field 18 / 19 - no actor of the five maps has the Dead Men bool set."""
    import kl_graft, kl_convert as K
    zp = archive_of(src)
    levels = levels or dead_men_levels(src)
    if not levels:
        raise ValueError('%s: no result.json names the Dead Men level; give --levels=M01_FA_A' % src)
    if dst and os.path.abspath(dst) == os.path.abspath(os.path.dirname(zp)):
        raise ValueError('the output folder is the build\'s own')
    order, files, ext, sc, _live, _hud = kl_graft.open_built(zp)
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if data != files[ext['.prp']] or bad:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte (%d misfits): not changed' % len(bad))
    dm = _dead_men(levels)
    before = faults(sc)                         # what the build has anyway (a tab build has none; counted, not judged)
    new = K.SQUAD_LISTS
    if len(new) != 12 or list(new) != sorted(set(new)) or max(new) > 14 or tuple(new) == OLD_SQUAD_LISTS:
        raise ValueError('kl_convert.SQUAD_LISTS is not a 12 -> 15 pairing other than the old one')
    rep = collections.OrderedDict(source=zp, levels=levels, squads=[], boxes=[], enums=[], right=[], left=[], play=[])
    lines = []
    def say(s):
        lines.append(str(s)); log(s)
    say('kl_map_ai pairfix: %s, Dead Men level(s) %s' % (zp, ', '.join(levels)))
    # 1. squads. First the plan - nothing is changed yet, so that 'who else names this target' is read off the
    #    build as it stands.
    plan = []                                   # (node, field values, [(from field, to field, Dead Men list)])
    for k, _i, v in kl_fa.controllers(sc, 'ZSquadScript'):
        d = dm.get(sc.path[k].lower(), {}).get('ZSquadScript')
        if d is None or len(v) != 21:
            continue
        dv = d[1]
        low = {i: {s.lower() for s in v[i]} for i in range(SQUAD_FIRST, SQUAD_FIRST + 15)}
        # every list Dead Men had entries in and the old pairing misplaced
        moves = []
        for j in range(12):
            if OLD_SQUAD_LISTS[j] == new[j] or not dv[3 + j]:
                continue
            a, b = SQUAD_FIRST + OLD_SQUAD_LISTS[j], SQUAD_FIRST + new[j]
            want = {s.lower() for s in dv[3 + j]}
            if want & low[b] and not want & low[a]:
                # Dead Men's entries stand in the field of their own event and none of them in the old field: right
                # already (an earlier pairfix, or a build converted after 2026-10-11); what field a holds, if
                # anything, belongs to another event
                rep['right'].append('%s: "%s" is in field %d' % (sc.path[k].replace(R, ''), LIST_NAME[j], b))
            elif not v[a]:
                rep['left'].append('%s: Dead Men had %d entries for "%s"; the build has none in field %d and field %d does not hold them either (a later step took or renamed them)' % (
                    sc.path[k], len(dv[3 + j]), LIST_NAME[j], a, b))
            else:
                moves.append((a, b, j))
        if not moves:
            continue
        srcs = {a for a, _b, _j in moves}
        # a destination that is not itself moved away must be empty, or the entries of two events would be mixed
        clash = sorted(b for _a, b, _j in moves if b not in srcs and v[b])
        if clash:
            rep['left'].append('%s: field(s) %s already hold entries of another event: NOT changed' % (sc.path[k], clash))
            continue
        plan.append((k, v, moves))
    # what a move changes IN PLAY, read off the lists (nothing here was run): a target that is also in a list of
    # the same squad whose pairing never changed, or that another object names, is reached without the move too
    named = _named(sc, {(k, a) for k, _v, moves in plan for a, _b, _j in moves}) if plan else {}
    kept = [(SQUAD_FIRST + new[j], LIST_NAME[j]) for j in range(12) if OLD_SQUAD_LISTS[j] == new[j]]
    tot = collections.Counter()
    for k, v, moves in plan:
        sol, civ = _squad_members(sc, k)
        own = {}
        for fi, nm in kept:
            for s in v[fi]:
                own.setdefault(s.lower(), nm)
        f = {a: [] for a, _b, _j in moves}
        for a, b, j in moves:
            f[b] = f.get(b, []) + list(v[a])
            rep['squads'].append('%s: "%s", %d entries: field %d -> field %d' % (sc.path[k].replace(R, ''), LIST_NAME[j], len(v[a]), a, b))
            same = [s for s in v[a] if s.lower() in own]
            rest = [s for s in v[a] if s.lower() not in own]
            other = [s for s in rest if named.get(s.lower())]
            alone = [s for s in rest if not named.get(s.lower())]
            tot.update({'entries': len(v[a]), 'same squad': len(same), 'another object': len(other), 'nothing else': len(alone)})
            s = '%s (%d soldier(s), %d civilian(s)), "%s" (was in the field of "%s"): of %d entries %d are also in this squad\'s own %s' % (
                sc.path[k].replace(R, ''), sol, civ, LIST_NAME[j], DD_LIST_NAME[a - SQUAD_FIRST], len(v[a]), len(same),
                ' / '.join('"%s"' % x for x in sorted({own[q.lower()] for q in same})) or 'lists that never moved')
            if other:
                k2, n2, i2 = named[other[0].lower()][0]
                s += '; %d more also named by another object (e.g. %s by %s @%s field %d)' % (
                    len(other), other[0].replace(R, ''), sc.path[k2].replace(R, ''), n2, i2)
            s += '; %d by nothing else%s' % (len(alone), (' (%s)' % ', '.join(x.replace(R, '') for x in alone)) if alone else '')
            if j == 2 and 2 <= sol + civ <= 3:
                # kl2 0x47e4d8: half dead = alive <= members / 2 (whole numbers), one left = alive <= 1, one update
                s += ' - with %d members "half dead" and "one left" fall in the same update (kl2 0x47e4d8): the move changes nothing in play' % (sol + civ)
            if j == 6 and civ and not sol:
                s += ' - a squad of civilians: Dead Men\'s civilian never sent this event (its sender 0x6edcd0 is called by the soldier script only), Dog Days\' does (kl2 0x7b4918 -> 0x582fb0)'
            rep['play'].append(s)
        put(sc, k, 'ZSquadScript', **{'f%d' % i: x for i, x in f.items()})
    rep['play totals'] = dict(tot)
    # 2. trigger boxes
    for k, _i, v in kl_fa.controllers(sc, 'TriggerBox'):
        d = dm.get(sc.path[k].lower(), {}).get('TriggerBox')
        if d is None or len(v) != 18 or not d[1][7]:
            continue
        if v[7] == 0 and v[8] == 1:
            put(sc, k, 'TriggerBox', f7=1, f8=0)
            rep['boxes'].append('%s: "another actor enters" was in field 8 ("the last of them leaves"): field 7 = 1, field 8 = 0' % sc.path[k].replace(R, ''))
            if not v[12] and not v[17] and not _named(sc).get(sc.path[k].lower()):
                rep['play'].append('%s: both lists of the box are empty and nothing names it: the move changes nothing in play' % sc.path[k].replace(R, ''))
        elif v[7] == 1 and v[8] == 0:
            rep['right'].append('%s: "another actor enters" is in field 7' % sc.path[k].replace(R, ''))
        else:
            rep['left'].append('%s: fields 7, 8 = %s, %s (not what the old converter wrote)' % (sc.path[k], v[7], v[8]))
    # 3. the renamed enums. A fly rout's FRONT_GUN / LAUNCHER comes back only on a helicopter that carries a
    #    weapon: kl_fa.heli_attack says why the pair 'attack' + 'no weapon' (M06's boss helicopter) is not written
    for k, _i, v in kl_fa.controllers(sc, 'HeliFlyBehaviourRout'):
        d = dm.get(sc.path[k].lower(), {}).get('HeliFlyBehaviourRout')
        want = K.ENUM_RENAME['EHeliAttackMode'].get(d[1][6]) if d else None
        if want and len(v) == 16 and v[6] == 'NO_ATTACK':
            par = sc.parent[k]
            armed = any(sc.cls(j) == 'ZHeli' and any(n == 'HeliWeapon' and w[3] for _x, n, w in ctrls(sc, j)) for j in range(par, sc.end[par]))
            if armed:
                put(sc, k, 'HeliFlyBehaviourRout', f6=want)
                rep['enums'].append('%s: attack mode %s was NO_ATTACK: %s' % (sc.path[k].replace(R, ''), d[1][6], want))
            else:
                rep['left'].append('%s: Dead Men says %s, but its helicopter carries no weapon: NO_ATTACK stays (kl_fa.heli_attack)' % (sc.path[k], d[1][6]))
    for k in range(1, len(sc.nodes)):
        d = dm.get(sc.path[k].lower(), {}).get('(node)')
        if d and sc.cls(k) == 'ZHavokRigidBody' and d[1] == 'PRIORITY_CRITICAL':
            fi = J.labels('dd', 'ZHavokRigidBody').index('ZHavokRigidBody[2]')
            now = kl_fa.node_values(sc, k)[fi]
            if now == 'COLLISION_PRIORITY_NORMAL':
                kl_fa.edit(sc, k, None, lambda us: setv(sc, us, fi, 'COLLISION_PRIORITY_CRITICAL'))
                rep['enums'].append('%s: collision priority was NORMAL: COLLISION_PRIORITY_CRITICAL' % sc.path[k].replace(R, ''))
            elif now == 'COLLISION_PRIORITY_CRITICAL':
                rep['right'].append('%s: collision priority is COLLISION_PRIORITY_CRITICAL' % sc.path[k].replace(R, ''))
    head = {'right': 'right already (an earlier pairfix, or converted after 2026-10-11)', 'left': 'left as they are'}
    for key in ('squads', 'boxes', 'enums', 'right', 'left'):
        say('  %s: %d' % (head.get(key, key), len(rep[key])))
        for r in rep[key]:
            say('      ' + r)
    if rep['play']:
        say('  in play (read off the build\'s lists, NOT RUN; old place of "a member is attacked" = Dog Days\' "a player starts close combat on a member", kl2 0x42dfa0):')
        for r in rep['play']:
            say('      ' + r)
        if tot:
            say('      squad entries moved: %d - %d also in a list of the same squad that never moved, %d more also named by another object, %d named by nothing else' % (
                tot['entries'], tot['same squad'], tot['another object'], tot['nothing else']))
        say('      a live run of the result can show that it loads and plays as before, not that the pairing is right (re/convert_audit.md 9)')
    data, bad, _paths, _names = J.check(sc, log=lambda *_a: None)
    if bad:
        raise ValueError('%d objects do not fit their class after the changes: %s' % (len(bad), bad[:3]))
    after = faults(sc)                          # entries are moved, none is written: the count cannot grow
    rep['list faults'] = (len(before), len(after))
    if len(after) > len(before):
        raise ValueError('reference lists at fault after the changes (nothing is written): %s' % [x for x in after if x not in before][:8])
    say('  kl_map_ai.faults (names nothing / without ROOT / order rules): %d before, %d after' % (len(before), len(after)))
    rep['prp bytes'] = (len(files[ext['.prp']]), len(data))
    rep['changed'] = data != files[ext['.prp']]
    if not dst:
        say('  nothing written (no output folder given)')
        return rep
    files[ext['.prp']] = data
    os.makedirs(dst, exist_ok=True)
    kl_graft.write_zip(os.path.join(dst, os.path.basename(zp)), [(n, files[n]) for n in order])
    for x in os.listdir(os.path.dirname(zp)):
        q = os.path.join(os.path.dirname(zp), x)
        if os.path.isfile(q) and q != zp and not x.startswith('pairfix.'):
            shutil.copyfile(q, os.path.join(dst, x))
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        old, now = st.get('final') or [[], []], kl_maps.member_ids(dst)
        diff = [a[0] for a, b in zip(old[0], now[0]) if a != b] + [a[0] for a, b in zip(old[1], now[1]) if a != b]
        if diff not in ([], ['.prp']) or [a[0] for a in old[0]] != [a[0] for a in now[0]] or len(old[1]) != len(now[1]):
            raise ValueError('more than the .prp member differs from the build: %s' % diff)
        st['pairfix'], st['final'] = diff, now
        st['same'] = [e for e in st.get('same', []) if e not in diff]
        with open(sj, 'w') as fh:
            json.dump(st, fh, indent=1)
    with open(os.path.join(dst, 'pairfix.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    with open(os.path.join(dst, 'pairfix.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    say('  written: %s' % dst)
    return rep


# ------------------------------------------------------------------ SPAWNS: nobody plops out (owner, 2026-10-11)
# Owner, after Retomoto: 'with the lmg guy and the two pistol guy at the elevator they always spawn in too late, make
# them spawn a bit early so its not like they just plop out try and do that with other parts if you can' and, as a fed
# on the street, 'the npc swat are like all bunched together, they should be in position waiting'.
# READ in kl2.exe (re/retomoto_spawns.md 1): a squad whose ZSquadScript field 3 is 0 has its men HIDDEN and taken
# out of the actor tables at the level's start (controller phase 5 = vtable slot 16, 0x787a10 -> 0x8d2e20: every
# member's node gets ZGEOM's Hide; the loader 0x8b2120 stores the field inverted at +0x58), and they are shown again
# the moment the squad is handed its first goal (0x7f6750 -> 0x7c0d50) - that is: when a box, a timer or a 'wiped out'
# list first names a rout of theirs. Seen from the box that does it, that is a man appearing out of thin air.
PLOP_NEAR = 4000.0              # GUESS: a man who appears in sight within this of where the waker stands 'plops out'
SIGHT_FAR = 9000.0              # sight is not looked for beyond this
EYE, CHEST = 150.0, 120.0       # above the floor: where the waker looks from, where the man is looked at


def _sp_quiet(*_a):
    pass


def _sp_floor(L, p):
    """The collision floor a man at place p stands on (a place may have the navigation mesh's height, which lies up
    to 70 under the collision on Retomoto's street) -> (y, found)."""
    G = L.ground(L.half_of(p))
    for up in (60.0, 150.0):
        _c, fy, _near = G.under((p[0], p[1] + up, p[2]))
        if fy is not None:
            return fy, True
    return p[1], False


def _sp_sight(G, a, b, step=12.0, slack=8.0, skip=45.0):
    """Is b seen from a? The straight line through the walk test's collision samples (kl_escape.Walk: every triangle
    of the static and key-framed shapes sampled every 10; convex shapes - crates, cars - are not in it, and a pane
    of glass with collision stops the line): no sample within `slack` of the line's height in any cell it crosses.
    Outside the box the ground was read for nothing is known: the line is clear there."""
    return G.sight(a, b, step, slack, skip)                 # kl_fa_fedpoints.Ground.sight


def _sp_stand(L, k, step=100.0):
    """Where somebody can stand inside trigger box k -> [(x, floor y, z)]: the box's footprint sampled every `step`,
    each sample on a polygon of the navigation mesh inside the box's height (any part), at the collision floor."""
    B = L.B
    hx, hy, hz = B.box(k)
    out = []
    nx, nz = max(1, int(2 * hx / step)), max(1, int(2 * hz / step))
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, y, z = B.world(k, (-hx + 2 * hx * i / nx, 0.0, -hz + 2 * hz * j / nz))
            hit = L.polys.at(x, y, z, y - hy - 170.0, y + hy)
            if hit is None:
                continue
            fy, _ok = _sp_floor(L, (x, hit[1], z))
            out.append((x, fy, z))
    return out


def spawn_rows(L):
    """Every enemy squad of a loaded build (kl_fa_fedpoints.Lv) -> rows (dicts): men, places, in the world from the
    load or not, what first shows it, and from there how near a man appears and whether in sight.
    verdict: 'active' (in the world from the load) | 'PLOP' (shown in sight within PLOP_NEAR of where its waker can
    stand) | 'in sight, far' | 'out of sight' | 'by a timer' (no place to judge) | 'never' (nothing names it)."""
    import kl_fa_bots_rt as RT
    B, sc = L.B, L.sc
    squads = RT.enemy_squads(B)
    boxes, other = RT.wake_map(B, squads)
    f = {t: v for t, _i, v in kl_fa.controllers(sc, 'ZSquadScript')}
    of = {k: t for t in squads for k in range(t, sc.end[t])}
    fall = collections.defaultdict(list)                # squad -> squads whose 'wiped out' list (field 8) names it
    for t, v in f.items():
        for s in v[8] if isinstance(v[8], list) else []:
            for j in sc.resolve(s):
                if j in of and of[j] != t and sc.names[t] not in fall[of[j]]:
                    fall[of[j]].append(sc.names[t])
    stand = {}
    rows = []
    for t, groups in squads.items():
        men = [B.at(k) for k in range(t + 1, sc.end[t]) if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups]
        r = collections.OrderedDict(squad=sc.path[t][5:], node=t, men=len(men), places=[[round(x) for x in m] for m in men],
                                    active=bool(f[t][3]), wakers=[], fall_back_of=fall.get(t, []))
        h = L.half_of(men[0])
        mine = sorted((k for k, hit in boxes.items() if t in hit), key=lambda k: math.dist(B.at(k), h.anchor))
        G = L.ground(h)
        for k in mine:
            if k not in stand:
                stand[k] = _sp_stand(L, k)
            S = stand[k]
            near = seen = None
            for m in men:
                my, _ok = _sp_floor(L, m)
                tgt = (m[0], my + CHEST, m[2])
                order = sorted(S, key=lambda s: math.dist(s, (m[0], my, m[2])))
                if order and (near is None or math.dist(order[0], (m[0], my, m[2])) < near):
                    near = math.dist(order[0], (m[0], my, m[2]))
                for s in order[:400]:
                    d = math.dist(s, (m[0], my, m[2]))
                    if d > SIGHT_FAR or (seen is not None and d >= seen):
                        break
                    if _sp_sight(G, (s[0], s[1] + EYE, s[2]), tgt):
                        seen = d
                        break
            r['wakers'].append(collections.OrderedDict(box=sc.path[k][5:], at=[round(x) for x in B.at(k)], half=[round(x) for x in B.box(k)],
                                                       stand=len(S), nearest=None if near is None else round(near), in_sight=None if seen is None else round(seen)))
        if r['active']:
            r['verdict'] = 'active'
        elif r['wakers']:
            w = r['wakers'][0]                          # the box nearest the crew's start: ASSUMED the first one crossed
            r['verdict'] = 'out of sight' if w['in_sight'] is None else 'PLOP' if w['in_sight'] <= PLOP_NEAR else 'in sight, far'
        elif other.get(t) == 'timer':
            r['verdict'] = 'by a timer'
        elif r['fall_back_of']:
            r['verdict'] = 'by a timer'                 # (a 'wiped out' list: no place to judge either)
        else:
            r['verdict'] = 'never'
        rows.append(r)
    return rows


FED_NEAR = 1500.0                       # a sleeping squad's man this near (horizontal, same floor +-400) to a fed point = he is seen to appear (GUESS)


def sleeping_near_fed(L, rows=None, near=FED_NEAR):
    """Review M1 / S4: -> [(squad, men near, nearest distance, fed point name)] for every squad still hidden from the load
    (ZSquadScript field 3 = 0) with a man within `near` of an AFTER_DEATH point of the build."""
    rows = rows if rows is not None else spawn_rows(L)
    pts = [(r['name'], L.at(k)) for k, r in L.survey()]
    out = []
    for r in rows:
        if r['active']:
            continue
        hit = None
        for m in r['places']:
            for nm, p in pts:
                if abs(m[1] - p[1]) < 400.0 and math.hypot(m[0] - p[0], m[2] - p[2]) < near:
                    d = math.hypot(m[0] - p[0], m[2] - p[2])
                    if hit is None or d < hit[1]:
                        hit = (nm, d)
        if hit:
            out.append((r['squad'], hit[1], hit[0]))
    return out


def spawns(src, log=print, L=None):
    """The audit of one build, printed. -> rows."""
    import kl_fa_fedpoints as FP
    L = L or FP.Lv(src, _sp_quiet)
    rows = spawn_rows(L)
    log('%s: map %s - %d enemy squads, %d men; PLOP = shown in sight within %d m of a place inside the box that first names it' % (
        src, L.map or '?', len(rows), sum(r['men'] for r in rows), PLOP_NEAR / 100))
    log('  %-62s %3s  %-14s %s' % ('squad', 'men', 'verdict', 'first named by (box: nearest a man appears to somebody inside it, m / nearest IN SIGHT, m)'))
    for r in rows:
        ws = '; '.join('%s: %s / %s' % (w['box'].split('!')[-1].split('\\')[-1], '-' if w['nearest'] is None else '%.0f' % (w['nearest'] / 100),
                                         'none' if w['in_sight'] is None else '%.0f' % (w['in_sight'] / 100)) for w in r['wakers'])
        if not ws:
            ws = 'in the world from the load' if r['active'] else 'a timer / the round start' if r['verdict'] == 'by a timer' else 'NOTHING names it'
        if r['fall_back_of']:
            ws += '; also when %s is wiped out' % ', '.join(n.split('!')[-1] for n in r['fall_back_of'])
        log('  %-62s %3d  %-14s %s' % (r['squad'][-62:], r['men'], r['verdict'], ws))
    c = collections.Counter(r['verdict'] for r in rows)
    m = collections.Counter()
    for r in rows:
        m[r['verdict']] += r['men']
    log('RESULT (kl_map_ai spawns): ' + ', '.join('%s %d squad(s) / %d men' % (k, c[k], m[k]) for k in ('PLOP', 'in sight, far', 'out of sight', 'by a timer', 'active', 'never') if c[k]))
    return rows


def _sp_legs(folder):
    """The legs of the AI heisters' street ways as the build's bots.json has them (kl_fa_bots_rt: facts_rt.street /
    street_branches: each squad's places in order) -> [((x, y, z), (x, y, z))]; [] without that file."""
    p = os.path.join(folder, 'bots.json')
    if not os.path.isfile(p):
        return []
    fr = json.load(open(p)).get('facts_rt') or {}
    rows = [v.get('places') or [] for v in (fr.get('street') or {}).values()]
    rows += [b.get('places') or [] for v in (fr.get('street_branches') or {}).values() for b in v]
    return [(tuple(a), tuple(b)) for r in rows for a, b in zip(r, r[1:])]


def _sp_leg_dist(legs, p):
    best = 1e9
    for a, b in legs:
        dx, dz = b[0] - a[0], b[2] - a[2]
        n = dx * dx + dz * dz
        t = 0.0 if n < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / n))
        best = min(best, math.hypot(p[0] - a[0] - t * dx, p[2] - a[2] - t * dz))
    return best


def _sp_vehicles(L):
    """The static vehicles of the street -> [(node, half width, half length)]: the walk test does not see them (their
    collision is a convex box, V_Coli_Hero_01, and kl_escape.Walk leaves convex shapes out), so a 'free cell' may lie
    inside a car. Sizes: kl_fa_street.BUS / CAR (measured there); the SWAT truck and van as a bus's width and 4 m of
    half length (GUESS). A vehicle's length lies along its local Z (kl_fa_street.footprints)."""
    import kl_fa_street as st
    sc, out = L.sc, []
    for k in range(1, len(sc.nodes)):
        n = sc.names[k]
        if n.startswith('Vehicles_static!') and sc.cls(k) == 'ZGROUP' and not L.B.ents[k - 1].flags & 0x400:
            hw, hl = (st.BUS[0], st.BUS[1]) if 'Bus' in n else (st.BUS[0], 400.0) if 'SWAT' in n else (st.CAR[0], st.CAR[1])
            out.append((k, hw, hl))
    return out


def _sp_in_vehicle(L, veh, p, body=70.0):
    for k, hw, hl in veh:
        at = L.B.at(k)
        if abs(at[0] - p[0]) > hl + body + 1.0 or abs(at[2] - p[2]) > hl + body + 1.0 or abs(at[1] - p[1]) > 400.0:
            continue
        q = L.B.local(k, (p[0], at[1], p[2]))
        if abs(q[0]) <= hw + body and abs(q[2]) <= hl + body:
            return L.sc.names[k].split('!')[-1]
    return None


def _sp_named(sc, names, what):
    out = []
    for n in names:
        hit = sc.resolve(full(n))
        if len(hit) != 1 or not any(sc.p.key(nm) == 'ZSquadScript' for nm, _b in sc.nodes[hit[0]]['ctrls']):
            raise ValueError('%s: %s is not one squad of this build' % (what, n))
        out.append(hit[0])
    return out


def spawn_plan(L, opt=None, log=print):
    """What spawnfix writes -> dict: 'active' [squad path] (ZSquadScript field 3 -> 1), 'moves' [dict(node, was, to,
    why)] (an actor group's place), 'audit' (spawn_rows before), 'notes'.
    opt: 'active' = None (the map's table: Retomoto = kl_fa_author.HALL_ACTIVE + kl_fa_street.ACTIVE; another map:
    nothing) | [squad paths]; 'auto' = True adds every squad the audit calls PLOP; 'asleep' = set names of
    kl_fa_street.ACTIVE left asleep ('hall' = kl_fa_author's four); 'posts' = False: nobody is moved."""
    import kl_fa_fedpoints as FP
    import kl_fa_bots_rt as RT
    opt = dict({'active': None, 'auto': False, 'asleep': (), 'posts': True}, **(opt or {}))
    B, sc = L.B, L.sc
    rows = spawn_rows(L)
    P = collections.OrderedDict(folder=L.folder, map=L.map, options={k: (sorted(v) if isinstance(v, (set, tuple)) else v) for k, v in opt.items()},
                                audit=rows, active=[], moves=[], notes=[])
    retomoto = L.map == 'M09_A' and len(L.halves) == 2
    posted = []
    if opt['active'] is not None:
        act = _sp_named(sc, opt['active'], '--active')
    elif retomoto:
        import kl_fa_author as au
        import kl_fa_street as st
        sets = collections.OrderedDict([('hall', au.HALL_ACTIVE)] + list(st.ACTIVE.items()))
        unknown = set(opt['asleep']) - set(sets)
        if unknown:
            raise ValueError('--asleep: %s is none of %s' % (sorted(unknown), list(sets)))
        act = [t for name, names in sets.items() if name not in opt['asleep'] for t in _sp_named(sc, names, name)]
        posted = _sp_named(sc, st.POSTED, 'POSTED') if opt['posts'] else []
    else:
        act = []
    if opt['auto']:
        act += [r['node'] for r in rows if r['verdict'] == 'PLOP' and r['node'] not in act]
    f3 = {t: v[3] for t, _i, v in kl_fa.controllers(sc, 'ZSquadScript')}
    for t in act:
        if f3[t]:
            P['notes'].append('%s is in the world from the load already' % sc.names[t])
        else:
            P['active'].append(sc.path[t][5:])
    if not posted:
        return P
    # ---- the posts (Retomoto's street)
    import kl_fa_street as st
    h = L.halves[1]
    L.ground(h)
    legs = _sp_legs(L.folder)
    if not legs:
        P['notes'].append('no bots.json with the AI heisters\' street ways beside the archive: the posts are not held off their legs')
    squads = RT.enemy_squads(B)
    cover_of, covers = {}, []                           # actor group -> its own RunToCover point; every such point
    for k, _i, v in kl_fa.controllers(sc, 'RunToCoverPosInfoRout'):
        covers.append(B.at(k))
        first = sc.names[sc.parent[k]].startswith('10_')
        for g in sc.resolve(v[5]) if isinstance(v[5], str) and v[5] else []:
            if g not in cover_of or first:
                cover_of[g] = B.at(k)
    veh = _sp_vehicles(L)
    npcs, L.npcs = L.npcs, []                           # (candidates() keeps NPC_FAR from where the men stand NOW)
    try:
        mine = {g for t in posted for g in squads.get(t, [])}
        taken = [B.at(g) for t, gs in squads.items() for g in gs if g not in mine and B.at(g)[1] < 5000.0]
        for t in posted:
            for g in sorted(squads.get(t, [])):
                was = B.at(g)
                cv = cover_of.get(g)
                want = (cv[0], cv[2] + st.POST_BACK) if cv else (was[0], was[2])
                pool = []
                for c in FP.candidates(L, h, centre=want, radius=st.POST_SNAP, step=1, bot_far=st.POST_HOLD, far_from_start=0.0):
                    if any(FP.hdist(c, q) < st.POST_APART for q in taken):
                        continue
                    if any(FP.hdist(c, q) < st.POST_COVER for q in covers if q is not cv):
                        continue
                    if legs and _sp_leg_dist(legs, c) < st.POST_LEG:
                        continue
                    if _sp_in_vehicle(L, veh, c):
                        continue
                    pool.append(c)
                if not pool:
                    P['notes'].append('%s: no free cell within %d of (%d, %d) passes every test - he stays at (%d, %d)' % (sc.path[g][5:], st.POST_SNAP, *want, was[0], was[2]))
                    taken.append(was)
                    continue
                c = min(pool, key=lambda c: (round(math.hypot(c[0] - want[0], c[2] - want[1]) / 20.0), c[0], c[2]))
                # his height: as far above the navigation mesh as he stood (F07's men are laid AT the mesh's height by
                # kl_fa_street.relay, the campaign's 45 above it at the collision floor's: both stand in the game)
                hit = L.polys.at(c[0], c[1], c[2], c[1] - 120.0, c[1] + 60.0, part=h.part)
                old = L.polys.at(was[0], was[1], was[2], was[1] - 120.0, was[1] + 60.0, part=h.part)
                to = (c[0], (hit[1] + (was[1] - old[1] if old else 0.0)) if hit else was[1], c[2])
                taken.append(to)
                if FP.hdist(to, was) < 1.0:
                    continue
                P['moves'].append(collections.OrderedDict(
                    node=sc.path[g][5:], squad=sc.path[t][5:], was=[round(x, 1) for x in was], to=[round(x, 1) for x in to],
                    cover=None if cv is None else [round(x, 1) for x in cv], moved=round(FP.hdist(to, was)),
                    leg=round(_sp_leg_dist(legs, to)) if legs else None,
                    why=('%d north of his cover point (%d, %d)' % (st.POST_BACK, cv[0], cv[2]) if cv else 'no cover point of his own: where he stood') +
                        ', the nearest free cell %d from that place' % math.hypot(c[0] - want[0], c[2] - want[1])))
    finally:
        L.npcs = npcs
    return P


def _sp_show(P, log=print):
    log('  IN THE WORLD FROM THE LOAD (ZSquadScript field 3: 0 -> 1): %d squad(s)' % len(P['active']))
    men = {r['squad']: r for r in P['audit']}
    for s in P['active']:
        r = men.get(s, {})
        log('    %-66s %d men, was: %s' % (s[-66:], r.get('men', 0), r.get('verdict', '?')))
    log('  POSTS: %d man/men moved' % len(P['moves']))
    for m in P['moves']:
        log('    %-58s (%6d %5d %6d) -> (%6d %5d %6d)  %4d moved%s; %s' % (m['node'][-58:], *m['was'], *m['to'], m['moved'],
                                                                         '' if m['leg'] is None else ', %d from the nearest leg of a heister' % m['leg'], m['why']))
    for s in P['notes']:
        log('  NOTE: ' + s)


def spawnfix(src, dst, opt=None, log=print):
    """A FINISHED build -> a NEW folder with the squads of the plan in the world from the load and the street's men at
    posts of their own. Only .prp (ZSquadScript field 3; an actor group's ZGEOM[2]) and .gms (those groups' place)
    change: no entity is added, removed or changes pool. -> the report (also spawnfix.json / spawnfix.txt)."""
    import hashlib
    import kl_graft
    import kl_fa_fedpoints as FP
    import kl_fa_bots as KB
    if os.path.exists(dst) and os.listdir(dst):
        raise ValueError('%s exists and is not empty: this step writes into a new folder only' % dst)
    L = FP.Lv(src, _sp_quiet)
    B, sc = L.B, L.sc
    if sc.p.serialize() != B['.prp']:
        raise ValueError('the build\'s .prp does not re-serialise byte for byte: not changed')
    KB._roundtrip(B)
    _d0, bad0, paths0, _n0 = J.check(sc, log=lambda *_a: None)
    P = spawn_plan(L, opt, log)
    res = lambda s: sc.resolve(full(s))[0]
    for s in P['active']:
        put(sc, res(s), 'ZSquadScript', f3=1)
    for m in P['moves']:
        g = res(m['node'])
        par = sc.parent[g]
        loc = B.local(par, tuple(m['to'])) if par else tuple(m['to'])
        e = B.ents[g - 1]
        old = struct.unpack('<3f', e.trans[:12])
        if max(abs(a - b) for a, b in zip(B.local(par, B.at(g)) if par else B.at(g), old)) > 0.5:
            raise ValueError('%s: its record\'s place is not its place in its parent\'s frame' % m['node'])
        FP._set_point(L, g, loc, None, None)
    data, bad, paths, _n = J.check(sc, log=lambda *_a: None)
    if len(bad) > len(bad0) or len(paths) > len(paths0):
        raise ValueError('after the change %d objects do not fit their class (%d before) and %d paths do not resolve (%d before)' % (len(bad), len(bad0), len(paths), len(paths0)))
    faults_ = B.scene.check()
    if faults_:
        raise ValueError('kl_scene.check: %s' % faults_[:3])
    gms, buf = B.scene.write()
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = data, kl_gms.pack(gms), buf
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    if not set(changed) <= {'.prp', '.gms'}:
        raise ValueError('members changed: %s' % changed)
    os.makedirs(dst, exist_ok=True)
    out = kl_graft.write_zip(os.path.join(dst, os.path.basename(L.zip)), [(n, new[n]) for n in B.order])
    for fn in os.listdir(src):
        q = os.path.join(src, fn)
        if os.path.isfile(q) and q != L.zip and not fn.startswith('spawnfix.') and fn not in FP.STALE:
            shutil.copyfile(q, os.path.join(dst, fn))
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        stp = json.load(open(sj))
        stp['spawnfix'], stp['final'] = changed, kl_maps.member_ids(dst, L.slot)
        stp['same'] = [e for e in stp.get('same', []) if e not in changed]
        with open(sj, 'w') as fh:
            json.dump(stp, fh, indent=1)
    # read back
    L2 = FP.Lv(dst, _sp_quiet)
    rows2 = spawn_rows(L2)
    v2 = {L2.sc.path[t][5:]: v[3] for t, _i, v in kl_fa.controllers(L2.sc, 'ZSquadScript')}
    probs = ['%s: field 3 reads %r' % (s, v2.get(s)) for s in P['active'] if not v2.get(s)]
    for m in P['moves']:
        at = L2.B.at(L2.sc.resolve(full(m['node']))[0])
        if math.dist(at, m['to']) > 1.0:
            probs.append('%s stands at (%d, %d, %d), not at its post' % (m['node'], *at))
    rep = collections.OrderedDict(source=src, source_sha1=hashlib.sha1(open(L.zip, 'rb').read()).hexdigest(), out=dst,
                                  out_sha1=hashlib.sha1(open(out, 'rb').read()).hexdigest(), members_changed=changed, active=P['active'],
                                  moves=P['moves'], notes=P['notes'], options=P['options'], problems=probs,
                                  audit_before=[{k: v for k, v in r.items() if k != 'node'} for r in P['audit']],
                                  audit_after=[{k: v for k, v in r.items() if k != 'node'} for r in rows2])
    with open(os.path.join(dst, 'spawnfix.json'), 'w') as fh:
        json.dump(rep, fh, indent=1)
    lines = ['kl_map_ai spawnfix: %s (archive sha1 %s) -> %s (sha1 %s)' % (src, rep['source_sha1'], out, rep['out_sha1']),
             '  members changed: %s' % (' '.join(changed) or 'none')]
    _sp_show(P, lines.append)
    c = collections.Counter(r['verdict'] for r in rows2)
    lines.append('  read back: ' + ', '.join('%s %d' % (k, n) for k, n in c.items()) + '; problems: %d' % len(probs))
    lines += ['  PROBLEM: ' + s for s in probs]
    lines.append('  NOT RUN IN THE GAME: live checks S0 .. S4 of re/retomoto_spawns.md before this build goes on the owner\'s tab')
    with open(os.path.join(dst, 'spawnfix.txt'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    for s in lines:
        log(s)
    log('RESULT (kl_map_ai spawnfix): %s' % ('PASS' if not probs else 'FAIL (%d)' % len(probs)))
    return rep


def spawndiff(src, dst, log=print):
    """What differs between two builds of one level, entity by entity, judged against what spawnfix and
    kl_fa_fedpoints mean to change -> True when nothing else does. Allowed: members .prp and .gms; in the .prp a
    ZSquadScript's field 3, the place (ZGEOM[2]) of a group that holds an enemy actor, ZGEOM[1..3] of an AFTER_DEATH
    spawn point; in the .gms those groups' place and the points' matrix, place and flag 0x400; beside the archive
    spawnfix.*, fedpoints.*, steps.json. Every other property, controller value and record field of every entity is
    compared (name, type, model, aux, REF, raw block, group, parent, children, list key, list links)."""
    import hashlib
    import kl_fa_fedpoints as FP
    A, Bn = FP.Lv(src, _sp_quiet), FP.Lv(dst, _sp_quiet)
    ok = [True]
    def bad(s):
        ok[0] = False
        log('  UNEXPECTED: ' + s)
    with zipfile.ZipFile(A.zip) as a, zipfile.ZipFile(Bn.zip) as b:
        ia, ib = a.infolist(), b.infolist()
        if [i.filename.rsplit('_Main', 1)[-1] for i in ia] != [i.filename.rsplit('_Main', 1)[-1] for i in ib]:
            bad('the member list changed')
        for i, j in zip(ia, ib):
            e, same = i.filename.rsplit('_Main', 1)[-1], (i.CRC, i.file_size) == (j.CRC, j.file_size)
            log('  member %-14s %s' % (e, 'same (CRC, %d bytes)' % i.file_size if same else 'CHANGED %d -> %d bytes' % (i.file_size, j.file_size)))
            if not same and e not in ('.prp', '.gms'):
                bad('member %s differs' % e)
    sha = lambda p: hashlib.sha1(open(p, 'rb').read()).hexdigest()
    fa = {f[len(A.slot):] if f.startswith(A.slot) else f: f for f in os.listdir(src) if not f.lower().endswith('_main.zip')}
    fb = {f[len(Bn.slot):] if f.startswith(Bn.slot) else f: f for f in os.listdir(dst) if not f.lower().endswith('_main.zip')}
    free = lambda f: f.startswith(('spawnfix.', 'fedpoints.')) or f == 'steps.json' or f in FP.STALE
    same = 0
    for f in sorted(set(fa) | set(fb)):
        if f not in fa or f not in fb:
            log('  beside: %-28s %s' % (f, 'NEW' if f not in fa else 'GONE'))
            if not free(f):
                bad('file %s is %s' % (f, 'new' if f not in fa else 'gone'))
        elif sha(os.path.join(src, fa[f])) != sha(os.path.join(dst, fb[f])):
            log('  beside: %-28s CHANGED' % f)
            if not free(f):
                bad('file %s differs' % f)
        else:
            same += 1
    log('  beside: %d other file(s) equal' % same)
    sa, sb = A.sc, Bn.sc
    if sa.names != sb.names or sa.tids != sb.tids:
        bad('the entities differ')
        return False
    pts = set(A.points)
    lab = J.labels('dd', 'ZSpawnPoint')
    pt_ok = {lab.index('ZGEOM[%d]' % i) for i in (1, 2, 3)}
    grp = {sa.parent[k] for k in range(1, len(sa.nodes)) if sa.cls(k) == 'ZFFActor' and A.B.values(k).get('ZFFActor[0]') == 'Enemy'}
    n_sq, n_mv, n_pt = [], [], []
    for k in range(1, len(sa.nodes)):
        na, nb = sa.nodes[k], sb.nodes[k]
        if J.text(sa, na['props']) != J.text(sb, nb['props']):
            va, vb = kl_fa.node_values(sa, k), kl_fa.node_values(sb, k)
            d = {i for i in range(max(len(va), len(vb))) if i >= len(va) or i >= len(vb) or va[i] != vb[i]}
            if k in pts and d <= pt_ok:
                n_pt.append(k)
            elif k in grp and d == {J.labels('dd', sa.cls(k)).index('ZGEOM[2]')}:
                n_mv.append(k)
            else:
                bad('node %s: properties %s differ' % (sa.path[k], sorted(d)))
        ca = [(sa.p.key(nm), [kl_fa.value(sa, u) for u in units(b[1:-1])]) for nm, b in na['ctrls']]
        cb = [(sb.p.key(nm), [kl_fa.value(sb, u) for u in units(b[1:-1])]) for nm, b in nb['ctrls']]
        if ca == cb:
            continue
        if [c[0] for c in ca] == [c[0] for c in cb] and all(x == y or (x[0] == 'ZSquadScript' and x[1][:3] + x[1][4:] == y[1][:3] + y[1][4:] and (x[1][3], y[1][3]) == (0, 1))
                                                           for x, y in zip(ca, cb)):
            n_sq.append(k)
        else:
            bad('node %s: controllers differ: %s' % (sa.path[k], [c[0] for c, c2 in zip(ca, cb) if c != c2]))
    log('  .prp: %d squad(s) with field 3 0 -> 1, %d enemy actor group(s) with another place, %d AFTER_DEATH point(s) with another matrix / place / hidden flag' % (len(n_sq), len(n_mv), len(n_pt)))
    for k in n_sq:
        log('      active   %s' % sa.path[k][5:])
    for k in n_mv:
        log('      moved    %-70s (%6d %5d %6d) -> (%6d %5d %6d)' % (sa.path[k][5:][-70:], *A.B.at(k), *Bn.B.at(k)))
    for k in n_pt:
        log('      point    %-70s (%6d %5d %6d) -> (%6d %5d %6d)' % (sa.path[k][5:][-70:], *A.B.at(k), *Bn.B.at(k)))
    ia, ib = {id(e): n for n, e in enumerate(A.B.ents)}, {id(e): n for n, e in enumerate(Bn.B.ents)}
    def rest(e, ix):
        at = lambda t: None if t is None else ix.get(id(t), -1)
        return (e.name, e.tid, e.model, e.aux, e.ref, e.raw, e.group, at(e.parent), [at(c) for c in e.kids], e.lkey,
                None if e.links is None else [(at(t), bits) for t, bits in e.links])
    ne = 0
    if len(A.B.ents) != len(Bn.B.ents):
        bad('.gms: %d entity records -> %d' % (len(A.B.ents), len(Bn.B.ents)))
    for k, (ea, eb) in enumerate(zip(A.B.ents, Bn.B.ents), 1):
        ra, rb = rest(ea, ia), rest(eb, ib)
        if (ea.rot, ea.trans, ea.flags) != (eb.rot, eb.trans, eb.flags) or ra != rb:
            ne += 1
            if ra != rb:
                bad('.gms record of %s differs: %s' % (sa.path[k], ', '.join(n for n, x, y in zip(
                    ('name', 'type', 'model', 'aux', 'REF', 'raw', 'group', 'parent', 'children', 'list key', 'list links'), ra, rb) if x != y)))
            elif k in pts:
                if (ea.flags ^ eb.flags) & ~0x400:
                    bad('.gms record of %s: flags %#x -> %#x' % (sa.path[k], ea.flags, eb.flags))
            elif k not in grp or ea.rot != eb.rot or ea.flags != eb.flags:
                bad('.gms record of %s differs (matrix / place / flags)' % sa.path[k])
    log('  .gms: %d entity record(s) differ (the place of the moved groups; matrix, place, flag 0x400 of the AFTER_DEATH points); every other field of all %d records is equal' % (ne, len(A.B.ents)))
    log('RESULT (kl_map_ai spawndiff): %s' % ('only what the steps mean to change differs' if ok[0] else 'UNEXPECTED DIFFERENCES'))
    return ok[0]


def main():
    global HEALTH_SCALE, ACC_CAP, AIM_CAP, HEALTH_ONLY, RT_ROWS, PISTOL_ROW
    a =[x for x in sys.argv[1:] if not x.startswith('--')]
    o = {x for x in sys.argv[1:] if x.startswith('--')}
    HEALTH_SCALE = next((float(x.split('=')[1]) for x in o if x.startswith('--health=')), HEALTH_SCALE)
    ACC_CAP = next((float(x.split('=')[1]) for x in o if x.startswith('--acc-cap=')), ACC_CAP)
    AIM_CAP = next((float(x.split('=')[1]) for x in o if x.startswith('--aim-cap=')), AIM_CAP)
    HEALTH_ONLY = HEALTH_ONLY or '--health-only' in o
    RT_ROWS = RT_ROWS or '--retomoto-rows' in o
    if '--pistol-row' in o:
        PISTOL_ROW = (55, 50)
    car = '--car-exit' in o
    parts = tuple(p for p in ('strength', 'waves', 'chains', 'escape') if '--no-' + p not in o)
    if len(a) == 2 and a[0] == 'table':
        show(measure(a[1]), routs='--short' not in o)
    elif a == ['stock']:
        stock()
    elif len(a) >= 2 and a[0] == 'balance':
        for src in a[1:]:
            balance(src, dist=next((float(x.split('=')[1]) for x in o if x.startswith('--dist=')), 10.0),
                    diff=next((int(x.split('=')[1]) for x in o if x.startswith('--diff=')), 1))
    elif len(a) == 3 and a[0] == 'apply':
        apply(a[1], a[2], parts, '--presets' in o, car_exit=car)
    elif len(a) in (2, 3) and a[0] == 'pairfix':
        lv = next((x.split('=')[1].split(',') for x in o if x.startswith('--levels=')), None)
        pairfix(a[1], a[2] if len(a) == 3 else None, lv)
    elif len(a) >= 2 and a[0] == 'spawns':
        for src in a[1:]:
            spawns(src)
    elif len(a) in (2, 3) and a[0] in ('spawnplan', 'spawnfix'):
        so = {'auto': '--auto' in o, 'posts': '--no-posts' not in o,
              'asleep': tuple(x for y in o if y.startswith('--asleep=') for x in y.split('=', 1)[1].split(',') if x),
              'active': next(([x for x in y.split('=', 1)[1].split(',') if x] for y in o if y.startswith('--active=')), None)}
        if a[0] == 'spawnplan' and len(a) == 2:
            import kl_fa_fedpoints as FP
            _sp_show(spawn_plan(FP.Lv(a[1], _sp_quiet), so))
        elif a[0] == 'spawnfix' and len(a) == 3:
            sys.exit(1 if spawnfix(a[1], a[2], so)['problems'] else 0)
        else:
            print(__doc__)
    elif len(a) == 3 and a[0] == 'retomoto-style':
        _r, sf = retomoto_style(a[1], a[2])
        sys.exit(1 if sf['problems'] else 0)
    elif len(a) == 3 and a[0] == 'cops-style':
        cops_style(a[1], a[2], strength_only='--strength-only' in o, same_part='--same-part' in o, chains_only='--chains-only' in o)
    elif len(a) == 3 and a[0] == 'spawndiff':
        sys.exit(0 if spawndiff(a[1], a[2]) else 1)
    elif len(a) == 3 and a[0] == 'pistol-row':
        rc = next((tuple(x.split('=')[1].split(',')) for x in o if x.startswith('--row-classes=')), ('pistol', 'revolver'))
        rw = next((tuple(float(t) for t in x.split('=')[1].split(',')) for x in o if x.startswith('--row=')), (55, 50))
        pistol_zip(a[1], a[2], row=rw, classes=rc)
    elif len(a) == 3 and a[0] == 'check':
        compare(a[1], a[2])
    elif len(a) >= 3 and a[0] == 'all':
        r = run_all(a[1], a[2], parts, '--presets' in o, car_exit=car, tags=a[3:] or None)
        sys.exit(1 if any(v['audit bad'] for v in r.values()) else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
