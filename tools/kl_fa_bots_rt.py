#!/usr/bin/env python3
"""
AI heisters on RETOMOTO TOWER: the squad of tools/kl_fa_bots.py on a map made of TWO navigation parts (the tower,
M09_A, and lobby + street, M09_B) that only the hook joins. Spec, the reading of kl2.exe it rests on, the hook part
(klhook/klcrew_rt.c), live checks: re/bots_retomoto.md. OFFLINE: nothing here installs anything or starts the game.

    python kl_fa_bots_rt.py build <build folder> <out folder> [options]   plan + write + every check; exit 1 on a FAIL
    python kl_fa_bots_rt.py plan  <build folder> [options]                the plan only (stations, places, notes)
    python kl_fa_bots_rt.py check <folder>                                kl_fa_bots.check + the checks of this module
    python kl_fa_bots_rt.py diff  <build folder> <out folder>             kl_fa_bots.diff, the JumpPoint allowed
    options
      --tower-only         no second leg: the bots end beside the tower car in an AllyEscapeBox and are taken from
                           there when a van waits in the street (re/bots.md 6.3). No JumpPoint list, no [CrewJoin] section.
                           The form that needs NO hook part - for an A / B run.
      --loot-seconds N     the wait at the boardroom table: until its six briefcases are gone or N s (default 30, GUESS:
                           the table's loot only appears when the room's guards are dead, kl_fa_author GATE_MAIN_ROOM)
      --enter-after-blast  the bots walk in AFTER_BLAST s after the blast (as before 2026-10-11); default: they wait
                           at the window until the boardroom's three squads are dead (the room counter), or
                           --room-wait S (75) after the blast at the latest
      --no-gates           the tower's way out as it was until 2026-10-11 afternoon: behind the loot wait the seven
                           sprint from way place to way place to the tower car. Default: EVERY ROOM FIRST (GATES) -
                           seven holds at cover boxes on the way down, each behind the trigger box that wakes one
                           fight's squads and short of the next one's (at the foot of a stair: AT the fight), and
                           behind each hold a TriggerActorsDead that names those squads' actor groups: the bot goes
                           on when they are dead, or after the 30 s the game gives such a wait. No sprint on that
                           way. re/retomoto_bots_rooms.md
      --gates a,b,..       only these of the gates (door reception atrium gallery floor2 floor1 lobby). The way
                           between two that are left is then ONE order without sprint and without way places (to
                           'floor1' alone: 138 m from the table) - so this is NOT 'the old chain with fewer gates';
                           an A / B run against the old chain is --no-gates against the default
      --after-blast S      Timer_start_bots = the level's own blast timer + S (default 1.0, GUESS): the bots stand on
                           the balcony until the window has gone
      --street-hold S      seconds the squad waits at the last place BEFORE the level exit box (default 10, GUESS;
                           0 = no wait). A bot inside that box calls the van (kl2 0x6cd8e0, re/bots.md 11), and
                           Retomoto has ONE van (kl_fa_street.ONE_VAN).
      --no-tree            as kl_fa_bots

THE DESIGN (the three ways weighed: re/bots_retomoto.md 2)
  ONE squad of seven, the same seven actors and crew records from the balcony to the van - so loot, money, heist
  stage and the traitor flag carry over. The route is two chains:
    tower   the room gate (the boardroom's squads dead, or Timer_start_bots: ROOM FIRST below) -> in through the
            window (ENTERS_BANK, stage 1) -> the boardroom table (TriggerLootDepleted) -> seven times [a hold at
            cover -> TriggerActorsDead {that fight's men}] down the tower (GATES below) -> a place BESIDE the tower
            car's jump box, inside an AllyEscapeBox (kl_fa_bots' --park form; the fall-back when the hook part is
            off: re/bots.md 6.3)
            THE JOIN IS NOT PROVEN FOR THESE WAITS (check(): the NOTE 'THE JOIN'): one that is armed when the human
            takes the tower car fires up to 30 s later and starts a tower step for a bot the hook has moved to the
            street. Limit N3 of re/bots_retomoto.md, once for the loot wait, now once more per gate.
    street  started by the JUMP: `Specials!JumpPoints!06_Exit`'s reference list names the first street step of each
            squad. kl2 0x57e110, after it has placed the local player at a jump entry, calls 0x72e0f0(the entry's
            ZJumpPoint), which sends 'AITrigger' (word [0x1689020], registered by jumppoint.cpp) to every object of
            that list ([jp+0x34]); a DefendBehaviourRout takes 'AITrigger' in its slot 26 (0x4ebed0, word
            [0x168d804]) and starts. Stock form: campaign L05 `Jumppoints!Jump05` names `AI!Friendly!B6!Kane_B6\\
            FollowLynch` (a friendly AI's step), L02 has six such lists.
            lobby (EXITS_BANK on the stairs, stage 2) -> entrance -> forecourt -> east pavement of the road -> a
            place before the level exit box (TriggerDelay2 --street-hold) -> into the box (stage 3; the van is
            called) -> beside the van's stop, on the pavement side of its lane; boarding by ZBoardEscapeVehicleTactic
            (stock F07's form: these ARE F07's vans).
  What moves the ACTORS from the tower part to the street part is the hook (klhook/klcrew_rt.c, [CrewJoin] Enable=1):
  in the tick in which kljoin.c's jump request for that entry is pending - before the game moves the player and
  sends the 'AITrigger' - it calls the game's own actor teleport 0x62a900 (the routine 0x8f3fa0 itself uses on the
  story crew at 0x8f4128, and ZFFActor's own slot 18 on itself at 0x6ccdc1) for every AI crew record in play, with
  the places this module writes into the [CrewJoin] section of the build's KLJoin.ini. WITHOUT that hook part the street steps are
  started for bots that stand in the tower: what a DefendBehaviourRout does with a place on another navigation
  part is NOT established - use a --tower-only build then.

WHAT IS WRITTEN beyond kl_fa_bots.apply: the street steps (cloned F07 forms, as every other step), the room gate
  (a TriggerCounter cloned from F07, named by the room counter of kl_fa_author: the second edit of an existing node),
  the gates' TriggerActorsDead nodes (cloned from F07's bots; inside the squads, no existing node touched), ONE edit
  of an existing node for the join (field 0 of the JumpPoint controller of 06_Exit), the [CrewJoin] section appended
  to <out>/KLJoin.ini.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_fa_bots as F
import kl_fa_author as au
from kl_prp import units
import kl_fa_van as van
import kl_fa_street as street

R_ = F.R_
JOIN_NAME = au.ROLE['join']             # 'Specials!JumpPoints!06_Exit': the entry KLJoin.ini jumps the player to
BLAST_TIMER = au.ROLE['blast timer']    # the level's TriggerDelay2 that swaps the glass (kl_fa_author.wire)
AFTER_BLAST = 1.0       # GUESS: the bots' start timer runs this long after the blast timer
# THE ROOM FIRST (2026-10-11, after runs HP / T1 / T2_DM09: the seven walked in and looted while the boardroom's guards
# lived, and died to their bullets in 95-150 s; the owner's design: the main room is looted 'once everyone in it is
# dead'). The bots' chain is now started by kl_fa_author's room counter (ROLE['counter'], the TriggerCounter the three
# room squads' field 8 feeds; it switched the table loot on and nothing else) through a one-shot gate counter, and by
# Timer_start_bots as the FALL-BACK ROOM_WAIT s after the blast (stock pairs 'those enemies are dead' with a timer,
# re/bots_dynamic.md 3) - so an idle player or a hiding guard does not leave the seven on the balcony for the round.
# Until then they stand at the blown window and shoot at what shows. GUESS: ROOM_WAIT; ASSUMPTION: a TriggerCounter
# with field 0 = 1 fires its list once when first named (stock F07 tcRunToEscape's form, fields 2 / 3 = 0).
ROOM_GATE = True        # False ('--enter-after-blast'): Timer_start_bots alone, AFTER_BLAST after the blast, as before
ROOM_WAIT = 75.0        # GUESS: the fall-back, seconds after the blast timer
ROOM_COUNTER = au.ROLE['counter']
GATE_NAME = F.SQUAD + 'Counter_room_clear'
# EVERY ROOM FIRST, ALL THE WAY DOWN (2026-10-11, re/retomoto_bots_rooms.md; after runs T7 / R7a..d / V1_DM09: nobody dies
# in the boardroom any more, and six of seven die 40..60 m further in - the campaign's own trigger boxes wake the next
# squads as the first bot walks through them, and the seven arrive in a string, sprinting). The tower's way out is now
# cut at GATES: before each fight the seven go to HOLD places at cover boxes - beyond the trigger box that wakes that
# fight's squads, short of the next one - and each bot's chain goes on only through a TriggerActorsDead that names the
# actor groups of exactly those squads.
#   THE FORM is stock's own: F07 Gameplay!merc_bot_squad!Squad#02 020_DefendBehaviour_rout_merc_fight_left ->
#   020_TriggerActorsDead_Lootarea {0: [ROOT\<squad>\<actor group>, ..], 1: 0, 2: [next step]} (120 uses in F01 F03 F04
#   F05 F06 F07: 2..9 groups, each a ZGROUP with one ZFFActor, field 1 = 0). kl_fa_bots.make clones the same node for
#   --wait-guards.
#   THE FALL-BACK IS BUILT IN (READ in kl2.exe, slots 26 / 25 of ZTriggerActorsDead, 0x4afb80 / 0x8def80): 'AITrigger'
#   arms it once (bytes +0x41 armed, +0x42 spent) and sets a deadline 0x7800 ticks = 30 s ahead; its update - only in
#   session state 0x19, as every trigger's - sends its list when every named group is dead OR the deadline has passed,
#   then never again. 'Dead' (0x5f4470) = the group's actor has state byte +0x576 == 0. The byte (ZActor slot 354,
#   0x7e72d0; re/retomoto_bots_rooms_review.md 1): 0 dead, 1 in play - written when an actor is entered in the game's
#   table of actors (0x546eca) and by the heal action -, 2 GOING DOWN (ZBecomeRagdoll passes it at 0x6772ad and 0 when
#   the man is dead, 0x677504): a man who is down and not dead holds a gate until then. What an actor of a squad that
#   has not been woken holds was not read; most likely 1 - not dead either way, so naming one costs the whole 30 s.
#   'ARMED' IS NOT 'ARRIVED': the hold step sends its list when its Defend goal calls the place reached, and that is
#   within 10 m of it in 3D for a step like ours (0x686c4c: radius 1000.0 unless the rout's second enum is 1; ASSUMED
#   that enum is field 5, eDF, which is eDF_NotSet on every step here). So the 30 s start up to 10 m before the hold -
#   where two holds of a bot lie nearer than that, at the hold before - and no clock runs for a bot that never comes
#   within 10 m of its hold (as in stock).
#   WHY NOT THE ROOM'S COUNTER FORM (ZSquadScript field 8 -> TriggerCounter -> gate) for these: kl_fa_bots.check,
#   kl_fa_bots_rt.check and kl_fa_bots_dyn walk a bot's chain through behaviour and wait controllers only; a
#   TriggerCounter BETWEEN two steps ends the walk (the room gate passes because it stands before the first step). A
#   TriggerActorsDead is a link of the chain all three know, needs no edit of an enemy squad, and kl_fa_bots_dyn keeps
#   it as it is. The room gate itself stays the counter (it fired GO+20..43 in nine live runs, never by its fall-back).
#   ONCE ONLY, everywhere (READ): a DefendBehaviourRout with field 8 = 1 starts once (0x4ebf01: byte +0x42 = field 8,
#   +0x40 = was started), a TriggerDelay2 with field 2 < 0 and a TriggerCounter with field 1 < 0 fire once (0x744d42,
#   0x54134b). So no wait of this chain can start a step a second time.
# GUESSES: every region below, the side of a box a bot is put on, that 30 s is enough or not too much.
TOWER_GATES = True      # False ('--no-gates'): the chain of 2026-10-11 morning (room first, then straight to the tower car)
EN_ = 'AI_Players!Enemies!'
HOLD_RING = (70.0, 230.0)   # a hold place lies this far from the middle of its cover box (kl_fa_bots_dyn.RING: DefendCover
                            # takes a cover within 500 of the defend position, kl2 0x84dc90; stock bots stand 165..291 off)
HOLD_BEST = 130.0           # of a box's places the one nearest to this distance (kl_fa_bots_dyn.RING_BEST)
HOLD_CLEAR = 35.0           # least distance of a hold place from a mesh edge without a neighbour (kl_fa_bots_dyn.HOLD_CLEAR)
HOLD_SEP = 110.0            # two hold places of one gate are at least this far apart (F.SEP)
HOLD_COVER = 500.0          # check(): a hold farther than this from every cover box FAILS
# WHAT THE REVIEW OF THE FIRST GATES BUILD ADDED (re/retomoto_bots_rooms_review.md D3 / D4; every number a GUESS):
RING_R = (80.0, 160.0, 230.0, 270.0)    # A COVER'S STANDING RING. DefendCover takes ANY cover box within HOLD_COVER of the
RING_N = 16                 # defend position and chooses the side of it itself. So a hold is tested with every box in
                            # its reach, not as a point: no place round such a box (its middle and RING_N places on each of
                            # these radii - HOLD_RING's outer one and 40 more) may lie in the trigger box of a later
                            # fight. The first build put the reception's seven within reach of three boxes whose west side
                            # is inside TriggerBox_EnterAtrium (ten men), and the west side is the sheltered one against
                            # the reception's own men.
REACH_DY = 260.0            # ... a box counts as in reach when it is within this height of the place (the check's own number)
POST_KEEP = 300.0           # no hold nearer than this to a POST of a man who may be alive: a place an enemy stands at when he
                            # is woken or is sent to by a rout of his squad (enemy_posts). The first build had two holds
                            # 0.3 m from one (the campaign puts its men at the same cover boxes).
FLOOR_DY = 200.0            # two places are 'on one floor' within this height (the floors are 700 apart)
PASS_NEAR = 600.0           # check(): the way to a hold PASSES a post when it comes this near to it on the post's floor ...
PASS_ON = 1000.0            # ... and FAILS when more than this of the way is still to walk then: the bot goes on with its back
                            # to a man this gate is meant to wait for (the first build's floor2 hold lay 20..26 m past them)
ENGAGE = 2500.0             # an EARLIER gate has dealt with a post - so passing it is the design, not a fault - only when one of
                            # its holds is on the post's floor within this much of path: naming men from another floor
                            # (the gallery names four across the open atrium) is a bet on a line of fire nothing here reads
WAIT_S = 30.0               # the 0x7800 ticks of 0x4afbbd, in seconds: a TriggerActorsDead's own time limit (counted from the
                            # moment the hold step calls its place reached: within ARRIVE_3D of it)
ARRIVE_3D = 1000.0          # kl2 0x686c4c (re/retomoto_bots_rooms_review.md D5): a Defend goal of a step like ours is 'there'
                            # within this of its place, in 3D
GATE_MAX = 9                # most groups one stock TriggerActorsDead names (F06, F07)
WAY_EVERY = 0.0             # 0: a leg from hold to hold (20..45 m, two of them down a stair) is ONE step whose only place is
                            # the hold - the game's pathfinder finds the way, as it does for the escort's and the boarding
                            # orders (run E3_DM01: ~100 m from one order). F.SPACING (1800, kl_fa_bots' rule) puts a way
                            # station every 18 m of THIS module's stand-in path instead; that path runs through the middles
                            # of polygon edges, and a station common to all seven pulled them into a corner of the reception.
# A gate: name; what (for the texts); squads = the enemy squads its wait names (top-level names behind EN_);
# pass = squads the way to the hold wakes that are NOT waited for (they go to another floor or side: said in the check);
# box = (x0, x1, z0, z1), y: where the hold places are looked for (GUESS); enemy = the direction in the plan the
# squads come from, for the side of the cover box (GUESS); cross = trigger boxes of a LATER fight the way to the hold
# cannot go round, because A STAIR ENDS INSIDE THEM (gates_plan holds the name against the geometry): the first bot
# off the stair has tripped such a box before anybody holds, so the hold may stand in it and its covers may reach
# into it. Every other box of a later fight is kept out of: the place, and the standing ring of every cover box in
# its reach (RING_R).
# WHERE A HOLD LIES (the second form, after the review): beyond the box that wakes its fight, short of the next
# fight's box, POST_KEEP from every post of a man who may be alive - and AT its fight where a stair leaves no room
# short of it: both flights end among the men of the floor below (the campaign posts them at the foot's own cover
# boxes), so the holds of floor2 and floor1 are the first cover at the foot. The first form put floor2's hold beyond
# the stair-end box, 20..26 m past the men it waits for, the way to it 0.5..6 m from their posts.
GATES = (
    {'name': 'door', 'what': 'the boardroom\'s door end (the reception\'s five come to the doorway)',
     'squads': ('030_Reception!Squad_Hallway#01', '030_Reception!Squad_ShootBeforeStorm', '030_Reception!Squad_Hallway'), 'pass': (),
     'box': (3520.0, 4125.0, -1150.0, 760.0), 'y': 20995.0, 'enemy': (-1.0, 0.0)},
    # (the reception's own three stand EAST of this hold, x 2900..3330, and are named again in case they outlived
    # the door's 30 s; the two it is for come from the WEST. So a bot here may take either side of its cover: the
    # ring rule keeps the hold out of reach of the three boxes at x 1700..1760 whose west side is in the atrium's box)
    {'name': 'reception', 'what': 'the reception, east of its desk (the two who sneak in from the atrium)',
     'squads': ('040_Atrium_3rd!Squad_AtrTop_Reception', '030_Reception!Squad_Hallway#01', '030_Reception!Squad_ShootBeforeStorm',
                '030_Reception!Squad_Hallway'), 'pass': (),
     'box': (1690.0, 3150.0, -1150.0, 950.0), 'y': 21000.0, 'enemy': (-1.0, 0.0)},
    {'name': 'atrium', 'what': 'the atrium\'s mouth on the third floor',
     'squads': ('040_Atrium_3rd!Atrium_3rd_RecepRCharge_Squad_01#01', '040_Atrium_3rd!Atrium_3rd_RecepSneakup_Squad_01',
                '040_Atrium_3rd!Atrium_3rd_RecepSneakup_Squad_01#01'),
     'pass': ('040_Atrium_3rd!Atrium_3rd_RecepRCharge_Squad_01', '040_Atrium_3rd!Atrium_3rd_RecepLCharge_Squad_01',
              '050_Atrium_2nd!Atrium_2nd_Atrium2nd_LeftCharge_Squad_01'),       # they take places one floor down, on the far side
     'box': (790.0, 1010.0, -1100.0, 900.0), 'y': 21000.0, 'enemy': (-1.0, 0.0)},
    # (the stairs: both flights run down WESTWARD side by side along the ring, so the way is third floor -> west end of
    # the second -> back east along its gallery -> the second flight -> west end of the atrium floor. The men of the
    # second floor stand where the first flight ends. The first form of this gate named four of them from above,
    # across the open atrium - 22 m, 7 m down: a bet on a line of fire nothing here reads. THE BET IS LOST, run G1_DM09
    # (2026-10-11 09:31, the first gates build, idle player): this wait ran its whole 30 s and one bot was shot dead AT
    # his gallery hold while it ran. So the gallery waits for the third floor's own men only; the men at the foot of
    # the flight are the next gate's, whose hold is at them.)
    {'name': 'gallery', 'what': 'the south gallery, before the stairs down',
     'squads': ('040_Atrium_3rd!Atrium_3rd_RecepRCharge_Squad_01', '040_Atrium_3rd!Atrium_3rd_RecepRCharge_Squad_01#01',
                '040_Atrium_3rd!Atrium_3rd_RecepSneakup_Squad_01'),
     'pass': ('050_Atrium_2nd!Atrium_2nd_Atrium2nd_RightCharge_Squad_01',),      # second floor, north-west: the next gate's
     'cross': ('040_Atrium_3rd!TriggerBox_EnterAtriumFurther',),                 # it lies across the whole mouth of the ring: no way round it
     'box': (100.0, 660.0, -1300.0, -600.0), 'y': 21000.0, 'enemy': (-1.0, -0.3)},     # (east of the post of RCharge#01, (-220, -1683))
    # (AT the foot of the first flight: the two pillars' cover boxes there. LCharge's post is 2 m from the foot, the
    # men of both 2nd-floor charges 6..13 m west and north along the west gallery; the one man who comes up the second
    # flight ends on the way on. The two who come up on the north side are not waited for.)
    {'name': 'floor2', 'what': 'the second floor, at the foot of the first flight of stairs',
     'squads': ('040_Atrium_3rd!Atrium_3rd_RecepLCharge_Squad_01', '050_Atrium_2nd!Atrium_2nd_Atrium2nd_LeftCharge_Squad_01',
                '050_Atrium_2nd!Atrium_2nd_Atrium2nd_RightCharge_Squad_01', '040_Atrium_3rd!Atrium_3rd_RecepRCharge_Squad_01#01',
                '050_Atrium_2nd!Atrium_2nd_Atrium2nd_LeftBehindStairs_Squad_01'),
     'pass': ('050_Atrium_2nd!Atrium_2nd_Atrium2nd_RightBehindStairs_Squad_01',),
     'cross': ('050_Atrium_2nd!Trigger_2ndFloorStairEnd',),                      # the first flight ends in it: the first floor's men set out
     'box': (-2350.0, -450.0, -1750.0, -600.0), 'y': 20300.0, 'enemy': (-0.5, 0.87)},
    # (the man of InfrontElevator walks the whole floor and ends 4 m from this hold, (-2445, -121): he is this gate's.
    # 010_Squad_Elevators, woken as the second flight ends, take places 21..30 m east, beside the next hold: the next gate's.)
    {'name': 'floor1', 'what': 'the atrium floor, at the foot of the second flight of stairs',
     'squads': ('060_Atrium_1st!Atrium_1st_CoverMiddle_Squad_01', '060_Atrium_1st!Atrium_1st_CoverMiddle_Squad_02',
                '060_Atrium_1st!Atrium_1st_PillarCover_Squad_01', '060_Atrium_1st!Atrium_1st_InfrontElevator_Squad_01'),
     'pass': ('070_Elevators!010_Squad_Elevators',),
     'cross': ('050_Atrium_2nd!Trigger_1stFloorStairEnd',),                      # the second flight ends in it
     'box': (-2100.0, -900.0, -1500.0, 0.0), 'y': 19600.0, 'enemy': (1.0, 0.3)},
    # (010_Squad_Elevators_GuardingElevator, one man, is woken on the way here and NOT waited for any more: he stands
    # at (2330, -1042), inside the lift lobby round the corner - no hold is within 25 m of path of him, none has a
    # straight line on the mesh to him. Named here he made the LAST wait before the tower car one that can only run
    # out: 30 s of every round, and the one wait most likely to be armed when the human takes the join. The seven meet
    # him and the two of Last_Stand_02 at the car, in tight defence.)
    {'name': 'lobby', 'what': 'the atrium floor, before the way to the lifts (the man with the machine gun holds it)',
     'squads': ('060_Atrium_1st!Squad_MG-Guy', '070_Elevators!010_Squad_Elevators',
                '060_Atrium_1st!Atrium_1st_PillarCover_Squad_01', '060_Atrium_1st!Atrium_1st_InfrontElevator_Squad_01'),
     'pass': ('070_Elevators!010_Squad_Elevators_GuardingElevator',),
     # (from the boulders in the middle of the floor, x -340..-40, the way to the lifts is seen along its length - the
     # machine gun's post (2005, -16) is at its far end; from the cases and pillars beside its mouth it is not)
     'box': (-300.0, 1350.0, -1000.0, 800.0), 'y': 19600.0, 'enemy': (1.0, 0.0)},
)
LOOT_SECONDS = 30       # GUESS (docstring)
STREET_HOLD = 10.0      # GUESS (docstring)
WARP = 15.0             # a polygon whose corners lie farther than this from the plane kl_fa_bots.Nav fits through its
                        # first three is not used for a place: the fitted height is wrong there (measured: the pentagon
                        # through the main window, corners y 20996 / 21025, fitted heights up to 21118)
BOMB_KEEP = 170.0       # GUESS: no bot within this of the charge on the glass (its radii are 1.0 on this build:
                        # kl_fa_author.BLAST_HARMLESS; this is for the look, not for damage)
INVISI_KEEP = 330.0     # the InvisiBomb's first radius is 300 (kl_fa_author.INVISIBOMB): no bot inside it
PARK_GAP = 150.0        # the gather square beside the tower car begins at least this far from the jump box (GUESS: the
                        # human has to walk INTO that box; seven bots standing in it would be in his way)
PARK_SQUARE = 160.0     # half side of the gather square (kl_fa_bots puts the seven within ALLY_SIZE * INSIDE = 157)
ARRIVE = (300.0, 900.0)  # the bots arrive this far in front of the jump entry (the entry is INSIDE the lobby car:
                        # kl_fa_author.CAR_B; car A's box is 433 deep, so its door is ~216 from the middle)
ARRIVE_SEP = 120.0      # between two arrival places (the game's own crew jump puts them 100 apart: kl2 0x8f4100)
STOP_RING = (150.0, 650.0)   # the last places: this far from the boarding box at the van's stop (kl_fa_bots.PARK is
                        # 150..400; here the lane itself is kept clear, which costs 350 of it)
LANE_SOUTH = 800.0      # the van's lane is kept clear from this far south of its waiting place (GUESS) to the end of the map
EXIT_SHARE = 0.9        # a 'level exit' place lies within this share of the box's half extents (0.45 would leave no
                        # place on the pavement side of the lane: the box is x -5700..-300, the lane x -1850)
DEFAULTS = {'tower_only': False, 'loot_seconds': LOOT_SECONDS, 'after_blast': AFTER_BLAST, 'street_hold': STREET_HOLD, 'tree': True,
            'room_gate': ROOM_GATE, 'room_wait': ROOM_WAIT, 'gates': TOWER_GATES, 'gate_names': None}


# ------------------------------------------------------------------ small things
def warp(nav, i):
    return max(abs(nav.height(i, v[0], v[2]) - v[1]) for v in nav.pv[i])


def flat(nav, c):
    return warp(nav, c[3]) <= WARP


def hdist(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def rect_dist(p, box):
    """Distance in the plan from point p to the rectangle of a ((x0, x1), (y0, y1), (z0, z1)) box."""
    dx = max(box[0][0] - p[0], 0.0, p[0] - box[0][1])
    dz = max(box[2][0] - p[2], 0.0, p[2] - box[2][1])
    return math.hypot(dx, dz)


def blast_seconds(B):
    """Field 0 of the level's blast timer (seconds after the round-start event), or None."""
    hit = B.sc.resolve(R_ + BLAST_TIMER)
    for k, _i, v in kl_fa.controllers(B.sc, 'TriggerDelay2'):
        if hit and k == hit[0]:
            return float(v[0])
    return None


def join_point(B):
    """(node, place, facing in the plan) of the jump entry. A JumpPoint's entry direction is its local -Z
    (kl_fa_author, read in run RT5): for 06_Exit (-1, 0), out of the car's door."""
    hit = B.sc.resolve(R_ + JOIN_NAME)
    if len(hit) != 1 or not kl_fa.has(B.sc, hit[0], 'JumpPoint'):
        raise ValueError('no JumpPoint %s in the build' % JOIN_NAME)
    Rm = B.fr[B.ents[hit[0] - 1]][0]
    return hit[0], B.at(hit[0]), (-Rm[0][2], -Rm[2][2])


def lane(p):
    """Is p in the strip the van drives through (waiting place .. the end of its drive)?"""
    return abs(p[0] - van.LANE_X) < street.VAN_CLEAR and p[2] >= van.WAIT_Z - LANE_SOUTH


def walk(nav, pts):
    """The mesh path through `pts` [(x, y, z, polygon)] in order, as points; None when a leg has no path."""
    out = [pts[0][:3]]
    for a, b in zip(pts, pts[1:]):
        got = nav.path(a, b)
        if got is None:
            return None
        out += got[0][1:]
    return out


def samples(poly, step=20.0):
    for p, q in zip(poly, poly[1:]):
        n = max(1, int(math.dist(p, q) // step))
        for t in range(n + 1):
            yield tuple(p[i] + (q[i] - p[i]) * t / n for i in range(3))


def straight(nav, part, a, b):
    """Does the straight line from a to b stay on the mesh of `part` (a sample every 20, each within 120 of the
    line's height) and out of the van's lane?"""
    return all(not lane(m) and nav.at(m[0], m[1], m[2], dy=120.0, part=part) is not None for m in samples([a[:3], b[:3]]))


def rides_with_van(B, act):
    """Is the boarding action a child of the van standing at kl_fa_van's waiting place? (kl_fa_street lays the box
    BOARD_BACK behind the van's origin; the van's keys take it to STOP_Z.)"""
    ap = B.at(act)
    return '\\V_Van_' in B.sc.path[act] and abs(ap[2] - (van.WAIT_Z - street.BOARD_BACK)) < 5.0 and abs(ap[0] - van.LANE_X) < 5.0


# ------------------------------------------------------------------ the tower's fights: who wakes whom, where to hold
def cover_boxes(B):
    """The objects kl2 0x6d6a80 makes covers of (re/bots_dynamic.md 3.1): ZSTDOBJ, name *coverbox*, flag bit 0x400
    clear -> [(node, place)]. As kl_fa_bots_dyn.cover_boxes (that module imports this one)."""
    sc = B.sc
    return [(k, B.at(k)) for k in range(1, len(sc.nodes))
            if 'coverbox' in sc.names[k].lower() and sc.cls(k) == 'ZSTDOBJ' and not B.ents[k - 1].flags & 0x400]


def enemy_squads(B):
    """{squad node: [actor group node]} of every squad with an Enemy actor (the group = the actor's parent, the
    thing a stock TriggerActorsDead names)."""
    sc, out = B.sc, collections.OrderedDict()
    for t, _i, _v in kl_fa.controllers(sc, 'ZSquadScript'):
        g = [sc.parent[k] for k in range(t + 1, sc.end[t]) if sc.cls(k) == 'ZFFActor' and B.values(k)['ZFFActor[0]'] == 'Enemy']
        if g:
            out[t] = g
    return out


RELAYS = ('TriggerDelay', 'TriggerDelay2', 'TriggerCounter')    # field 4 of each = what it sends 'AITrigger' to


def wake_map(B, squads=None):
    """-> ({trigger box node: {squad node}}, {squad node: what starts it besides a box}). A box 'wakes' a squad when
    its list (TriggerBox field 17) names the squad or a node of it, directly or through timers / counters. A box
    with field 0 = 0 waits to be switched on and is left out. Squads no box names: 'active' (ZSquadScript field 3 =
    1: in the world from the load), 'timer' (a timer or counter outside every squad names it: the blast), or None."""
    sc = B.sc
    squads = squads if squads is not None else enemy_squads(B)
    of = {k: t for t in squads for k in range(t, sc.end[t])}
    relay = {k: [j for s in v[4] for j in sc.resolve(s)] for cn in RELAYS for k, _i, v in kl_fa.controllers(sc, cn)}

    def reach(first):
        todo, seen, hit = list(first), set(), set()
        while todo:
            j = todo.pop()
            if j in seen:
                continue
            seen.add(j)
            if j in of:
                hit.add(of[j])
            elif j in relay:
                todo += relay[j]
        return hit
    boxes = {}
    for k, _i, v in kl_fa.controllers(sc, 'TriggerBox'):
        if len(v) == 18 and v[0]:
            hit = reach(j for s in v[17] for j in sc.resolve(s))
            if hit:
                boxes[k] = hit
    by_box = {t for hit in boxes.values() for t in hit}
    other = {}
    active = {t: v[3] for t, _i, v in kl_fa.controllers(sc, 'ZSquadScript')}
    timed = reach(j for k, js in relay.items() if k not in of for j in js)
    for t in squads:
        if t not in by_box:
            other[t] = 'active' if active.get(t) else 'timer' if t in timed else None
    return boxes, other


def in_trigger(B, k, p):
    """Is a walker at p inside trigger box k (feet or chest, as kl_fa_bots.in_exit tests a level exit box)?"""
    return B.in_box(k, p) or B.in_box(k, (p[0], p[1] + F.CHEST, p[2]))


def enemy_posts(B, squads=None):
    """{squad node: [(what, place, role)]} - THE POSTS of every enemy squad: where its men stand at the load (role
    'start') and every place a behaviour of the squad names (a Defend rout's Pos#, a Flanking rout's flanks, a Hunt
    box): the children without a controller that a *Behaviour* controller of the squad points at. Where a living man
    of that squad may be met. A rout of several places is walked in the order of its list (the campaign's 'sneak up'
    squads cross a whole floor that way): role 'first' / 'mid' / 'last' says where on it a place lies, 'only' = a
    rout of one place or a place the men go to directly (a flank, a box)."""
    sc, out = B.sc, collections.OrderedDict()
    squads = squads if squads is not None else enemy_squads(B)
    for t, groups in squads.items():
        posts = [('start', B.at(k), 'start') for k in range(t + 1, sc.end[t]) if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups]
        for k in range(t + 1, sc.end[t]):
            for nm, body in sc.nodes[k]['ctrls']:
                cn = sc.p.key(nm)
                if 'Behaviour' not in cn:
                    continue
                row = []
                for x in [kl_fa.value(sc, u) for u in units(body[1:-1])]:
                    for s in ([x] if isinstance(x, str) else x if isinstance(x, list) else []):
                        if not isinstance(s, str) or '\\' not in s:
                            continue
                        for h in sc.resolve(s if s.upper().startswith('ROOT\\') else R_ + s):
                            if t < h < sc.end[t] and not sc.nodes[h]['ctrls'] and sc.cls(h) != 'ZFFActor' and h not in groups and h not in row:
                                row.append(h)
                walked = cn == 'DefendBehaviourRout' and len(row) > 1
                for i, h in enumerate(row):
                    posts.append(('%s\\%s' % (sc.names[k], sc.names[h]), B.at(h),
                                  'only' if not walked else 'first' if i == 0 else 'last' if i == len(row) - 1 else 'mid'))
        out[t] = posts
    return out


def near_post(p, posts, among, keep=POST_KEEP):
    """The nearest post of the squads `among` within `keep` of place p on p's floor -> (distance, squad, what, place) or None."""
    best = None
    for t in among:
        for what, q, _role in posts.get(t, ()):
            if abs(q[1] - p[1]) <= FLOOR_DY and hdist(p, q) < keep and (best is None or hdist(p, q) < best[0]):
                best = (hdist(p, q), t, what, q)
    return best


def posts_then(posts, t, woken_before):
    """Where the men of squad t may be met when a bot walks a leg -> [(what, place)]. A squad that an EARLIER leg has
    woken has had a gate's time to walk its routs: it is at the END of each (role 'last' / 'only'). One that this
    leg itself wakes, or nothing yet, stands at its start places and goes to the FIRST place of its routs - the
    later places of a walked rout it reaches by walking, and the campaign's sneak-up routs end BEHIND the seven
    (Squad_AtrTop_Reception's at the boardroom's door, where they have just held)."""
    if t in woken_before:
        return [(w, q) for w, q, r in posts.get(t, ()) if r in ('last', 'only')]
    return [(w, q) for w, q, r in posts.get(t, ()) if r in ('start', 'first', 'only')]


def ring_points(c, y):
    """Where a bot that uses the cover box at c may come to stand (RING_R / RING_N), at height y."""
    out = [(c[0], y, c[2])]
    for r in RING_R:
        out += [(c[0] + r * math.cos(2 * math.pi * i / RING_N), y, c[2] + r * math.sin(2 * math.pi * i / RING_N)) for i in range(RING_N)]
    return out


def ring_in(B, c, y, boxes):
    """{trigger box of `boxes`: share of the standing ring of the cover box at c that lies inside it} (those with any)."""
    pts = ring_points(c, y)
    out = {}
    for k in boxes:
        n = sum(1 for p in pts if in_trigger(B, k, p))
        if n:
            out[k] = n / len(pts)
    return out


def reach_covers(covers, p):
    """The cover boxes DefendCover may take for a defend position at p: within HOLD_COVER in the plan, REACH_DY in height."""
    return [(ck, c) for ck, c in covers if abs(c[1] - p[1]) <= REACH_DY and hdist(c, p) <= HOLD_COVER]


def mesh_line(nav, part, a, b, step=20.0, dy=120.0):
    """Does the straight line a -> b stay on the mesh of `part` (a sample every `step`, each within dy of the line's
    height)? The one line of sight that can be had offline: no wall, no drop and no other floor between - a prop
    that stands on the mesh is not seen, and a line across open air (the atrium's well) is 'no' although it may be
    clear. So True = very likely a line of fire, False = not known."""
    return all(nav.at(m[0], m[1], m[2], dy=dy, part=part) is not None for m in samples([a[:3], b[:3]], step))


def passes(pts, posts3):
    """THE WALK PAST. pts = a way as points (way_samples), posts3 = [(squad, what, place)]. A way passes a post when
    it comes within PASS_NEAR of it on the post's floor; what counts is how much of the way is LEFT when it has
    come out of that reach again (0 when the way ends inside it: a hold AT the fight). -> the post with the most
    way left, if that is more than PASS_ON: (squad, what, place, nearest, way left); else None."""
    worst = None
    for t, what, q in posts3:
        near = [i for i, m in enumerate(pts) if abs(m[1] - q[1]) <= FLOOR_DY and hdist(m, q) < PASS_NEAR]
        if not near:
            continue
        left = sum(math.dist(u, w) for u, w in zip(pts[near[-1]:], pts[near[-1] + 1:]))
        if left > PASS_ON and (worst is None or left > worst[4]):
            worst = (t, what, q, min(hdist(pts[i], q) for i in near), left)
    return worst


def stair_end(B, boxes, pts, y):
    """The trigger boxes of `boxes` in which a way that changes floor arrives on the floor of its end: the boxes that
    hold the first of its points (pts: way_samples) from which on it stays within 60 of height y. A stair that ENDS
    in a box: nobody can come down it without tripping the box. [] when the way stays on one floor."""
    if not pts or abs(pts[0][1] - y) <= FLOOR_DY:
        return []
    i = len(pts) - 1
    while i > 0 and abs(pts[i - 1][1] - y) <= 60.0:
        i -= 1
    return [k for k in boxes if in_trigger(B, k, pts[i])]


def cuts_off(B, nav, k, a, h):
    """Does trigger box k lie ACROSS every way on the mesh from place a to place h? The polygons the box touches (a
    corner or the middle inside it, feet or chest) are closed and a way is looked for again. Only said of a place h
    that lies in none of those polygons: for one inside the box the question has no meaning."""
    a4 = a if len(a) > 3 else (lambda t: t and tuple(a[:3]) + (t[0],))(nav.at(a[0], a[1], a[2], dy=260.0))
    h4 = h if len(h) > 3 else (lambda t: t and tuple(h[:3]) + (t[0],))(nav.at(h[0], h[1], h[2], dy=260.0))
    if not a4 or not h4:
        return False
    part = nav.part[h4[3]]
    key = (B, nav, k, part)                             # (the objects themselves: an id may be used again)
    if key not in _TOUCHED:
        _TOUCHED[key] = {i for i in range(len(nav.pv)) if nav.ok[i] and nav.part[i] == part
                         and any(in_trigger(B, k, v) for v in list(nav.pv[i]) + [nav.mid[i]])}
    ban = _TOUCHED[key]
    if h4[3] in ban or not ban:
        return False
    return nav.path(tuple(a4[:4]), tuple(h4[:4]), ban) is None


_TOUCHED = {}       # {(build, mesh, trigger box, mesh part): the polygons the box touches} (cuts_off)


def cannot_go_round(B, nav, boxes, a, h):
    """The trigger boxes of `boxes` that a bot walking from place a to its hold h trips whatever way it takes: a stair
    ends in the box (stair_end), or the box lies across every way (cuts_off). Such a box is tripped before anybody
    holds - a hold may stand in it, a cover's ring may reach into it - and GATES names it under 'cross'."""
    got = way_samples(nav, a, h)
    if got is None:
        return []
    out = stair_end(B, boxes, got[0], h[1])
    return out + [k for k in boxes if k not in out and cuts_off(B, nav, k, a, h)]


def way_samples(nav, a, b, step=20.0, dy=260.0):
    """Points every `step` along the stand-in mesh path from place a to place b (3- or 4-tuples), or None when the
    mesh has no path. The path runs through the middles of the polygons' shared edges: this module's stand-in for
    the game's pathfinder, as in kl_fa_bots."""
    ha = (a[3],) if len(a) > 3 else (lambda h: h and (h[0],))(nav.at(a[0], a[1], a[2], dy=dy))
    hb = (b[3],) if len(b) > 3 else (lambda h: h and (h[0],))(nav.at(b[0], b[1], b[2], dy=dy))
    got = ha and hb and nav.path(tuple(a[:3]) + ha, tuple(b[:3]) + hb)
    if not got:
        return None
    return list(samples(got[0], step)), got[1]


def boxes_on(B, nav, boxes, a, b):
    """The trigger boxes of `boxes` the stand-in path a -> b is inside at some point, in the order met; None: no path."""
    got = way_samples(nav, a, b)
    if got is None:
        return None
    out = []
    for m in got[0]:
        for k in boxes:
            if k not in out and in_trigger(B, k, m):
                out.append(k)
    return out


def hold_spots(B, nav, home, covers, g, keep_out, keep_ring=None, posts=None, live=(), tally=None):
    """The places a bot can hold at for gate g: HOLD_RING from the middle of a cover box, inside the gate's box, on
    a flat polygon of the START row's part, HOLD_CLEAR from a wall, in none of the trigger boxes `keep_out`; NO cover
    box in reach of the place (reach_covers: the box it is planned at and every other DefendCover may take) has a
    place of its standing ring in one of the boxes `keep_ring` (default: keep_out); POST_KEEP from every post of the
    squads `live` (enemy_posts).
    -> [(x, y, z, polygon, cover node, behind, clearance, distance from the box)]; behind = the box lies between the
    place and the enemy. tally (a Counter): how many places each rule refused."""
    x0, x1, z0, z1 = g['box']
    ex, ez = g['enemy']
    n = math.hypot(ex, ez) or 1.0
    tally = tally if tally is not None else collections.Counter()
    keep_ring = keep_out if keep_ring is None else keep_ring
    dirty = {ck for ck, c in covers if abs(c[1] - g['y']) <= REACH_DY + 150.0 and ring_in(B, c, g['y'], keep_ring)}
    out = []
    for ck, c in covers:
        if abs(c[1] - g['y']) > 260.0 or not (x0 - HOLD_RING[1] <= c[0] <= x1 + HOLD_RING[1] and z0 - HOLD_RING[1] <= c[2] <= z1 + HOLD_RING[1]):
            continue
        k = int(HOLD_RING[1] // 40) + 1
        for ix in range(-k, k + 1):
            for iz in range(-k, k + 1):
                x, z = c[0] + ix * 40.0, c[2] + iz * 40.0
                d = math.hypot(x - c[0], z - c[2])
                if not (HOLD_RING[0] <= d <= HOLD_RING[1] and x0 <= x <= x1 and z0 <= z <= z1):
                    continue
                hit = nav.at(x, g['y'], z, dy=150.0, part=home)
                if hit is None or warp(nav, hit[0]) > WARP:
                    continue
                p = (x, hit[1], z)
                cl = nav.clearance(x, hit[1], z)
                if cl < HOLD_CLEAR or any(in_trigger(B, t, p) for t in keep_out):
                    continue
                tally['places'] += 1
                if any(ck2 in dirty for ck2, _c2 in reach_covers(covers, p)):
                    tally['refused: a cover box in reach has a side in a later fight\'s box'] += 1
                    continue
                if posts is not None and near_post(p, posts, live):
                    tally['refused: within %d of a post of a man who may be alive' % POST_KEEP] += 1
                    continue
                behind = ((c[0] - x) * ex + (c[2] - z) * ez) / n >= 0.5 * d      # within 60 degrees of straight behind it
                out.append((x, hit[1], z, hit[0], ck, behind, cl, d))
    return out


def pick_holds(spots, n=7):
    """n of the places -> (places, the least distance between two of them asked for); ([], 0) when there are not n.
    The boxes take turns (one bot a box while boxes last, the box's best place first: behind it, F.CLEAR from a wall,
    HOLD_BEST off its middle). Where the boxes are few (the atrium's mouth has two for seven bots) a box's places are
    packed along it instead, and as a last resort the bots stand closer than HOLD_SEP (never under 90; stock: ~100)."""
    by = collections.defaultdict(list)
    for s in spots:
        by[s[4]].append(s)
    order = sorted(by, key=lambda ck: (-len(by[ck]), ck))
    quality = lambda s: (not s[5], s[6] < F.CLEAR, abs(s[7] - HOLD_BEST), -s[6])
    sweeps = (quality, lambda s: (s[2], s[0]), lambda s: (-s[2], s[0]), lambda s: (s[0], s[2]), lambda s: (-s[0], s[2]))
    for sep in (HOLD_SEP, 100.0, 90.0):
        for pool in (lambda s: s[5], lambda s: True):               # behind the box only, then any side of it
            for sweep in sweeps:
                packs = {}
                for ck in order:
                    packs[ck] = []
                    for s in sorted((s for s in by[ck] if pool(s)), key=sweep):
                        if all(hdist(s, o) >= sep for o in packs[ck]):
                            packs[ck].append(s)
                got = []
                while len(got) < n and any(packs.values()):
                    for ck in order:
                        while packs[ck]:
                            s = packs[ck].pop(0)
                            if all(hdist(s, o) >= sep for o in got):
                                got.append(s)
                                break
                        if len(got) >= n:
                            break
                if len(got) >= n:
                    return got[:n], sep
    return [], 0.0


def assign(prev, holds):
    """Which bot takes which hold: the pairing with the least sum of plan distances (7! = 5040 orders). A hold on
    ANOTHER floor that lies within ARRIVE_3D of the bot's place before counts 100 m more: the step to it would be
    'there' at once - the floors are 7 m apart, the way down a stair 30..45 m - and the hold's wait would have run a
    third of its 30 s before the bot stands at it (the foot of the second flight lies under the foot of the first)."""
    import itertools
    cost = [[hdist(p, h) + (10000.0 if abs(p[1] - h[1]) > FLOOR_DY and math.dist(p[:3], h[:3]) < ARRIVE_3D + 50.0 else 0.0) for h in holds] for p in prev]
    best = None
    for perm in itertools.permutations(range(len(holds))):
        d = sum(cost[b][j] for b, j in enumerate(perm))
        if best is None or d < best[0]:
            best = (d, perm)
    return [holds[j] for j in best[1]]


def gates_plan(B, nav, S, P, opt, log=print):
    """The tower's way out of plan P (kl_fa_bots.plan: .. loot place, way places, the place beside the tower car)
    laid anew: loot place -> [way places] -> HOLD of gate 1 -> .. -> HOLD of gate n -> the place beside the car.
    P['stations'], P['steps'] and every bot's places are rewritten behind the last loot station; -> [gate dict]
    for Street.nodes (which puts each gate's TriggerActorsDead behind its hold step) and for the report."""
    sc, home = B.sc, S['home']
    name = lambda k: sc.path[k][5:]
    want = opt.get('gate_names')
    table = [g for g in GATES if want is None or g['name'] in want]
    if want is not None and len(table) != len(set(want)):
        raise ValueError('--gates: %s is no gate (the gates: %s)' % (sorted(set(want) - {g['name'] for g in GATES}), ', '.join(g['name'] for g in GATES)))
    squads = enemy_squads(B)
    by_name = {sc.names[t]: t for t in squads}
    boxes, other = wake_map(B, squads)
    covers = cover_boxes(B)
    posts = enemy_posts(B, squads)
    st = P['stations']
    i_loot = max(i for i, x in enumerate(st) if x['kind'] == 'loot')
    if st[-1]['kind'] != 'park':
        raise ValueError('the plan does not end beside the tower car (station %s)' % st[-1]['kind'])
    park = st[-1]
    prev = [tuple(P['bots'][N]['places'][i_loot]) for N in F.BOTS]
    new, steps, gates, woken, counted = [], [], [], set(), set()
    known = {t for t, why in other.items() if why}                         # started by the blast or in the world from the load
    engaged = set()                                                         # the posts an earlier gate has dealt with (ENGAGE)
    pkey = lambda q: tuple(round(v) for v in q)

    def path_len(a, b):
        got = way_samples(nav, a, b)
        return None if got is None else got[1]

    def walks_past(a, h, mine_, woken_before):
        """Does the way a -> hold h pass a post of a squad of this gate that no earlier gate has dealt with, and go on
        for more than PASS_ON? -> (squad, what, post, nearest, way left) or None. Which posts: posts_then()."""
        got = way_samples(nav, a, h)
        if got is None:
            return None
        return passes(got[0], [(t, what, q) for t in mine_ for what, q in posts_then(posts, t, woken_before) if pkey(q) not in engaged])

    def way_stations(a, b, keep_out, what):
        """Way stations (7 places each) every WAY_EVERY along the stand-in path from place a to place b (none when
        WAY_EVERY is 0) -> (stations, the length of that path)."""
        got = way_samples(nav, a, b)
        if got is None:
            raise ValueError('%s: no path on the mesh from (%d, %d, %d) to (%d, %d, %d)' % (what, *a[:3], *b[:3]))
        pts, length = got
        out, run, nxt = [], 0.0, WAY_EVERY
        for p, q in zip(pts, pts[1:]):
            run += math.dist(p, q)
            if WAY_EVERY > 0 and run >= nxt and length - nxt > WAY_EVERY * 0.5:
                c = [x for x in nav.around(q, 260.0, home, dy=200.0) if flat(nav, x) and not any(in_trigger(B, t, x[:3]) for t in keep_out)]
                s = nav.spots(c, 7, F.SEP, ref=q)
                if len(s) < 7:
                    s = nav.spots(c, 7, 50.0, ref=q) or s
                if s:
                    out.append({'kind': 'way', 'what': 'on the way to %s' % what, 'node': None, 'distinct_places': len(s),
                                'places': [[round(v, 1) for v in s[b_ % len(s)][:3]] for b_ in range(7)]})
                nxt += WAY_EVERY
        return out, length

    def leg(stations, gname):
        """Stations -> the steps of one leg (F.STEP_MAX places a step, the last place the leg's own end)."""
        idx = list(range(i_loot + 1 + len(new) - len(stations), i_loot + 1 + len(new)))
        n_leg = len(gates) if gname != 'car' else len(table)
        for m in range(0, len(idx), F.STEP_MAX):
            steps.append({'name': '%03d_DefendBehaviour_out_%s%s' % (30 + n_leg, gname, '_%s' % 'bcdef'[m // F.STEP_MAX - 1] if m else ''),
                          'leg': 'out', 'stop': None, 'stations': idx[m:m + F.STEP_MAX], 'gate': gname})
        return steps[-1]['name']

    for gi, g in enumerate(table):
        miss = [s for s in g['squads'] + tuple(g.get('pass', ())) if EN_ + s not in by_name]
        if miss:
            raise ValueError('gate %s: no squad %s in the build' % (g['name'], ', '.join(miss)))
        mine = [by_name[EN_ + s] for s in g['squads']]
        later = {by_name[EN_ + s] for h in table[gi + 1:] for s in h['squads']} - set(mine) - counted
        # the boxes this hold must stay out of: every box that wakes a squad of a LATER gate and none of this one's
        # (a box that starts both - the campaign re-uses a box - is this gate's)
        keep_out = [k for k, hit in boxes.items() if hit & later and not hit & (set(mine) | counted | woken)]
        cross = [k for k in keep_out if sc.names[k] in [EN_ + c for c in g.get('cross', ())]]
        no_way = [k for k in keep_out if k not in cross]
        # (a box a stair ends in is tripped before anybody holds: only the others bind the hold. And of those the
        # RING rule takes the ones that wake men who have a post on this floor - men who then come to, or stand on,
        # the floor the seven wait on; a box whose men all go to another floor is left to the check to name)
        keep_ring = [k for k in no_way if any(abs(q[1] - g['y']) <= FLOOR_DY for t in boxes[k] & later for _w, q, _r in posts.get(t, ()))]
        # the men who may be alive round this hold: everybody but the room's squads and the squads an earlier gate
        # has waited for and this one does not name again
        live = set(squads) - known - (counted - set(mine))
        refused = collections.Counter()
        spots = hold_spots(B, nav, home, covers, g, no_way, keep_ring, posts, live, refused)
        tried, past, soft = 0, None, None
        while True:
            holds, sep = pick_holds(spots)
            if not holds and soft is not None:
                holds = soft[1]                                 # (no seven without a wait armed a stair early: the fewest that could be had)
                break
            if not holds:
                raise ValueError('gate %s: only %d hold places at %d cover boxes in x %d..%d, z %d..%d (wanted 7, %d apart); refused: %s%s'
                                 % (g['name'], len(spots), len({s[4] for s in spots}), *g['box'], HOLD_SEP, dict(refused),
                                    '; the last way refused walked past %s %s (%d, %d, %d): %d from it, then %d on to the hold'
                                    % (name(past[0]).split('!')[-1], past[1], *past[2], past[3], past[4]) if past else ''))
            holds = assign(prev, holds)
            # every bot's way to its hold: on the mesh, never through a box of a later fight, and not PAST a post of
            # a man this gate waits for (PASS_NEAR / PASS_ON: the hold is short of its fight or at it, never beyond)
            bad = None
            for b, h in enumerate(holds):
                on = boxes_on(B, nav, list(boxes), prev[b], h)
                if on is None or any(k in no_way for k in on):
                    bad = h
                    break
                wp = walks_past(prev[b], h, mine, woken)
                if wp is not None:
                    bad, past = h, wp
                    break
            if bad is None:
                # SOFT: no hold on another floor within ARRIVE_3D of its bot's place before (assign() has already paired
                # the seven to avoid it). Where a pairing still has one, that place is given up and the seven are picked
                # again; the pick with the fewest is kept in case none is free of them.
                soon = [h for b, h in enumerate(holds) if abs(prev[b][1] - h[1]) > FLOOR_DY and math.dist(prev[b][:3], h[:3]) < ARRIVE_3D + 50.0]
                if soft is None or len(soon) < soft[0]:
                    soft = (len(soon), holds)
                if not soon or tried > 200:
                    holds = soft[1]
                    break
                bad = soon[0]
            spots = [s for s in spots if s[:3] != bad[:3]]
            tried += 1
            if tried > 200 and soft is not None:
                holds = soft[1]
                break
            if tried > 200:
                raise ValueError('gate %s: no seven hold places whose ways stay out of the next fight\'s trigger boxes and do not walk past its own men%s'
                                 % (g['name'], ' (the last: %s %s (%d, %d, %d), %d from the way, %d of way left)'
                                    % (name(past[0]).split('!')[-1], past[1], *past[2], past[3], past[4]) if past else ''))
        # what the ways to the holds wake (the first bot through a box wakes its squads for all)
        met, ends_in = [], []
        for b, h in enumerate(holds):
            for k in boxes_on(B, nav, list(boxes), prev[b], h):
                if k not in met:
                    met.append(k)
            ends_in += [k for k in cannot_go_round(B, nav, met, prev[b], h) if k not in ends_in]
        wrong = [name(k) for k in cross if k not in ends_in]
        if wrong:
            raise ValueError('gate %s: \'cross\' names %s, but none of the seven ways to the hold has to go through it (no stair ends in it and '
                             'it does not lie across the way)' % (g['name'], ', '.join(wrong)))
        woken |= {t for k in met for t in boxes[k]}
        asleep = [t for t in mine if t not in woken and t not in known]
        # the covers in reach of the holds whose ring reaches into a later fight's box all the same (men who go to
        # another floor: keep_ring leaves those out), and what this gate can be said to have dealt with
        early = collections.OrderedDict()
        for h in holds:
            for ck, c in reach_covers(covers, h):
                for k, share in ring_in(B, c, h[1], [k for k in no_way if k not in keep_ring]).items():
                    early.setdefault(name(k), set()).update(name(t) for t in boxes[k] & later)
        sight = collections.OrderedDict()
        for t in mine:
            here = [(w_, q) for w_, q, _r in posts.get(t, ()) if abs(q[1] - g['y']) <= FLOOR_DY]
            seen = [(w_, q) for w_, q in here if any(mesh_line(nav, home, h, q) for h in holds)]
            near = [(w_, q) for w_, q in here if any((path_len(h, q) or 1e9) <= ENGAGE for h in holds)]
            engaged |= {pkey(q) for _w, q in near}
            sight[name(t)] = {'posts': len(posts.get(t, ())), 'on_this_floor': len(here), 'straight_line_on_the_mesh': len(seen),
                              'within_%d_m_of_path' % (ENGAGE / 100): len(near)}
        b0 = max(range(7), key=lambda b: hdist(prev[b], holds[b]))                 # the way stations lie along the longest of the seven ways
        ways, length = way_stations(prev[b0], holds[b0], no_way, 'the hold of gate %s' % g['name'])
        new += ways
        new.append({'kind': 'hold', 'what': 'HOLD %s: %s' % (g['name'], g['what']), 'node': None, 'distinct_places': 7,
                    'places': [[round(v, 1) for v in h[:3]] for h in holds], 'gate': g['name'],
                    'covers': [name(h[4]) for h in holds]})
        step = leg(ways + [new[-1]], g['name'])
        groups = [R_ + name(a) for t in mine for a in squads[t]]
        if len(groups) > GATE_MAX:
            raise ValueError('gate %s names %d actor groups (stock: at most %d a list)' % (g['name'], len(groups), GATE_MAX))
        d_cover = [hdist(h, B.at(h[4])) for h in holds]
        apart = min(hdist(a, c) for i, a in enumerate(holds) for c in holds[i + 1:])
        d_post = [min([hdist(h, q) for t in live for _w, q, _r in posts.get(t, ()) if abs(q[1] - h[1]) <= FLOOR_DY] or [1e9]) for h in holds]
        legs = [path_len(prev[b], h) for b, h in enumerate(holds)]
        early_armed = sum(1 for b, h in enumerate(holds) if math.dist(prev[b][:3], h[:3]) < ARRIVE_3D)
        early_way = max([legs[b] for b, h in enumerate(holds) if math.dist(prev[b][:3], h[:3]) < ARRIVE_3D] or [0.0])
        gates.append(collections.OrderedDict(
            name=g['name'], what=g['what'], step=step, wait='%03d_TriggerActorsDead_%s' % (30 + gi, g['name']), seconds=WAIT_S,
            squads=[name(t) for t in mine], groups=groups, men=len(groups),
            boxes_on_the_way=[name(k) for k in met], kept_out_of=[name(k) for k in keep_out],
            crossed_of_a_later_fight=[name(k) for k in met if k in cross], not_awake=[name(t) for t in asleep],
            woken_not_counted=[name(t) for t in sorted(woken - counted - set(mine) - known)],
            holds=[[round(v, 1) for v in h[:3]] for h in holds], covers=[name(h[4]) for h in holds],
            behind_its_box=sum(1 for h in holds if h[5]), from_cover=[round(min(d_cover)), round(max(d_cover))], apart=round(apart),
            clearance=[round(min(h[6] for h in holds)), round(max(h[6] for h in holds))], path=round(length), way_stations=len(ways),
            legs=[round(x) for x in legs], from_a_post=[round(min(d_post)), round(max(d_post))], places_refused=dict(refused),
            covers_in_reach=len({ck for h in holds for ck, _c in reach_covers(covers, h)}),
            stair_ends_in=[name(k) for k in ends_in], woken_early_by_a_cover_in_reach={k: sorted(v) for k, v in early.items()},
            sight=sight, waits_armed_at_the_hold_before=early_armed, longest_way_of_those=round(early_way)))
        counted |= set(mine)
        log('  gate %-9s %d squads / %d men; hold round (%d, %d, %d): 7 places at %d cover boxes, %d..%d from the box, %d of 7 behind it, %d apart at least, '
            'clearance %d..%d; %d of path, %d way station(s); boxes on the way: %s'
            % (g['name'], len(mine), len(groups), sum(h[0] for h in holds) / 7, holds[0][1], sum(h[2] for h in holds) / 7, len({h[4] for h in holds}),
               min(d_cover), max(d_cover), sum(1 for h in holds if h[5]), apart, min(h[6] for h in holds), max(h[6] for h in holds), length, len(ways),
               ', '.join(name(k).split('!')[-1].split(chr(92))[-1] for k in met) or 'NONE'))
        log('       the seven ways to it %d..%d of path; nearest post of a man who may be alive %d..%d from a hold; %d cover boxes within %d of a hold, '
            'none with a side in a later fight\'s box%s%s; places refused: %s'
            % (min(legs), max(legs), min(d_post), max(d_post), len({ck for h in holds for ck, _c in reach_covers(covers, h)}), HOLD_COVER,
               ' (but: %s)' % '; '.join('%s, which wakes %s - no post of theirs on this floor' % (k.split('!')[-1], ', '.join(x.split('!')[-1] for x in sorted(v)))
                                       for k, v in early.items()) if early else '',
               '; no way round %s' % ', '.join(name(k).split('!')[-1] for k in ends_in) if ends_in else '', dict(refused) or 'none'))
        far = [name(t).split('!')[-1] for t in mine if not sight[name(t)]['within_%d_m_of_path' % (ENGAGE / 100)]]
        if far:
            log('       NOTE OUT OF REACH: %s - no post of theirs is on this floor within %d m of path of a hold: the wait runs out unless these men come '
                'to the seven (run G1_DM09: the first gallery gate named four such men and ran its whole %d s)' % (', '.join(far), ENGAGE / 100, WAIT_S))
        blind = [(name(t).split('!')[-1], sight[name(t)]) for t in mine if not sight[name(t)]['straight_line_on_the_mesh']]
        if blind:
            log('       NOTE no straight line on the mesh from any hold to any post of: %s. Whether these men can be hit from the holds is not read '
                '(a line across open air, over a rail or past a prop is not a line on the mesh); if not, the wait runs its %d s'
                % ('; '.join('%s (%s)' % (n_, 'its posts are on another floor' if not s_['on_this_floor'] else '%d post(s) on this floor' % s_['on_this_floor'])
                             for n_, s_ in blind), WAIT_S))
        if early_armed:
            log('       NOTE %d of the seven holds lie within %d m (3D) of the bot\'s place before: that wait is armed before the bot has left it '
                '(kl2 0x686c4c), up to %d of way = about %d s early' % (early_armed, ARRIVE_3D / 100, early_way, early_way / 400.0))
        if asleep:
            log('    NOTE gate %s: %s not woken by any box on the way to the hold: its wait can only run out (%d s)'
                % (g['name'], ', '.join(name(t).split('!')[-1] for t in asleep), WAIT_S))
        prev = [tuple(h[:4]) for h in holds]
    # the last leg: to the places beside the tower car (kl_fa_bots' own station, inside the AllyEscapeBox)
    pk = [tuple(p) for p in park['places']]
    b0 = max(range(7), key=lambda b: hdist(prev[b], pk[b]))
    ways, length = way_stations(prev[b0], pk[b0], [], 'the tower car')
    new += ways + [park]
    leg(ways + [park], 'car')
    met = []
    for b in range(7):
        for k in boxes_on(B, nav, list(boxes), prev[b], pk[b]) or []:
            if k not in met:
                met.append(k)
    woken |= {t for k in met for t in boxes[k]}
    log('  to the car   %d of path, %d way station(s); boxes on the way: %s; woken and never waited for: %s'
        % (length, len(ways), ', '.join(name(k).split('!')[-1].split(chr(92))[-1] for k in met) or 'none',
           ', '.join(name(t).split('!')[-1] for t in sorted(woken - counted - known)) or 'nobody'))
    P['stations'] = st[:i_loot + 1] + new
    P['steps'] = [s for s in P['steps'] if s['leg'] != 'out'] + steps
    for b, N in enumerate(F.BOTS):
        P['bots'][N]['places'] = P['bots'][N]['places'][:i_loot + 1] + [x['places'][b] for x in new]
    return gates


# ------------------------------------------------------------------ the tower half
def tower_park(B, nav, home, log=print):
    """Where the seven gather: a square of mesh beside the jump box of KLJoin.ini, not in it. -> (x, y, z)."""
    jb = au.JOIN_BOX
    mid = tuple((a + b) / 2 for a, b in jb)
    c = nav.around(mid, 900.0, home, dy=200.0)
    if not c:
        raise ValueError('no mesh of the START row\'s part within 900 of the jump box')
    best = None
    for q in c:
        if rect_dist(q, jb) - PARK_SQUARE < PARK_GAP:
            continue
        n = sum(1 for o in c if abs(o[0] - q[0]) <= PARK_SQUARE and abs(o[2] - q[2]) <= PARK_SQUARE and abs(o[1] - q[1]) < 30.0)
        key = (n, -rect_dist(q, jb))                    # the fullest square, then the nearest to the box
        if best is None or key > best[0]:
            best = (key, q)
    if best is None:
        raise ValueError('no place for a gather square beside the jump box')
    (n, d), q = best
    log('tower: the seven gather round (%d, %d, %d): %d of %d grid places of the square are mesh; its edge is %d from the jump box x %d..%d z %d..%d'
        % (*q[:3], n, (2 * int(PARK_SQUARE // 40) + 1) ** 2, -d - PARK_SQUARE, *jb[0], *jb[2]))
    return q[:3]


def ledge_starts(B, nav, S, log=print):
    """Seven places on the balcony outside the main window (kl_fa_author.LEDGE), beside the START stacks, clear of
    the charge and of the InvisiBomb -> [(x, y, z, polygon)]."""
    (x0, x1), (z0, z1) = au.LEDGE
    home = S['home']
    c = [q for q in nav.around((sum(au.LEDGE[0]) / 2, au.LEDGE_Y, sum(au.LEDGE[1]) / 2), 1300.0, home)
         if x0 <= q[0] <= x1 and z0 <= q[2] <= z1 and flat(nav, q)
         and F.START_NEAR <= min(hdist(q, p) for p, _f in S['starts']) <= F.START_FAR
         and hdist(q, au.BOMB) >= BOMB_KEEP and hdist(q, au.INVISIBOMB) >= INVISI_KEEP]
    # The balcony's mesh is 170 wide: 'nearest to the middle first' (Nav.spots) finds six. So: a greedy pick along
    # the balcony, in several orders, the widest spacing that gives seven, of those the pick with the most clearance.
    c = [q for q in c if nav.clearance(*q[:3]) >= F.CLEAR_MIN + 10.0]
    got = []
    for sep in (F.SEP + 20.0, F.SEP, 90.0):             # stock: at least ~100 apart; kl_fa_bots.check wants 80
        tries = []
        for key in (lambda q: (q[2], q[0]), lambda q: (q[2], -q[0]), lambda q: (-q[2], q[0]), lambda q: (-q[2], -q[0]),
                    lambda q: (-nav.clearance(*q[:3]), q[2])):
            pick = []
            for q in sorted(c, key=key):
                if len(pick) < 7 and all(hdist(q, o) >= sep for o in pick):
                    pick.append(q)
            if len(pick) == 7:
                tries.append(pick)
        if tries:
            got = max(tries, key=lambda pk: (min(nav.clearance(*q[:3]) for q in pk), -max(hdist(q, au.BOMB) for q in pk)))
            got.sort(key=lambda q: q[2])
            break
    if len(got) < 7:
        raise ValueError('only %d places for the seven bots on the balcony (%d candidates)' % (len(got), len(c)))
    log('tower: the seven start on the balcony (x %d..%d, glass at x 5860): x %d..%d, z %d..%d, y %d; %d..%d from the charge, %d..%d from the InvisiBomb, clearance %d..%d'
        % (x0, x1, min(g[0] for g in got), max(g[0] for g in got), min(g[2] for g in got), max(g[2] for g in got), got[0][1],
           min(hdist(g, au.BOMB) for g in got), max(hdist(g, au.BOMB) for g in got),
           min(hdist(g, au.INVISIBOMB) for g in got), max(hdist(g, au.INVISIBOMB) for g in got),
           min(nav.clearance(*g[:3]) for g in got), max(nav.clearance(*g[:3]) for g in got)))
    return got


def flatten(B, nav, S, P, log=print):
    """kl_fa_bots.plan put places on polygons whose fitted height is wrong (WARP): each is moved to the nearest
    place on a flat polygon of the same part - inside the same trigger box when the station is one."""
    home, moved = S['home'], 0
    for si, st in enumerate(P['stations']):
        node = B.sc.resolve(R_ + st['node'])[0] if st['node'] else None
        for b, N in enumerate(F.BOTS):
            p = st['places'][b]
            hit = nav.at(p[0], p[1], p[2], dy=15.0)
            if hit and warp(nav, hit[0]) <= WARP:
                continue
            others = [st['places'][o] for o in range(7) if o != b]
            c = [q for q in nav.around(p, 400.0, home, dy=260.0) if flat(nav, q) and (node is None or B.in_box(node, q[:3]))]
            c.sort(key=lambda q: (min([hdist(q, o) for o in others] or [1e9]) < F.SEP * 0.5, nav.clearance(*q[:3]) < F.CLEAR_MIN + 10, hdist(q, p)))
            if not c:
                raise ValueError('station %d (%s): no flat polygon for the place (%d, %d, %d)' % (si + 1, st['what'], *p))
            q = [round(v, 1) for v in c[0][:3]]
            st['places'][b] = q
            P['bots'][N]['places'][si] = q
            moved += 1
    if moved:
        log('tower: %d places moved off polygons whose fitted height is off by more than %d (the window\'s pentagon)' % (moved, WARP))
    return moved


def tower_plan(B, opt, log=print):
    nav = F.Nav(B.scene.nav)
    S = F.stations(B, nav)
    blast = blast_seconds(B)
    if blast is None:
        raise ValueError('no blast timer %s in the build: is it a Retomoto build of kl_fa_author?' % BLAST_TIMER)
    delay = blast + float(opt['after_blast'])
    log('tower: the level\'s blast timer runs %.1f s after the round-start event; Timer_start_bots = %.1f s' % (blast, delay))
    park = tower_park(B, nav, S['home'], log)
    P = F.plan(B, {'park': list(park), 'ally_box': 'on', 'start_delay': delay, 'loot_seconds': int(opt['loot_seconds']), 'tree': opt['tree']}, log)
    stand = ledge_starts(B, nav, S, log)
    for b, N in enumerate(F.BOTS):
        P['bots'][N]['start'] = [round(v, 1) for v in stand[b][:3]]
        P['bots'][N]['face'] = [-1.0, 0.0]              # into the room (kl_fa_author.IN), as the START points face
    flatten(B, nav, S, P, log)
    gates = []
    if opt.get('gates'):
        log('tower: every room first - the way from the loot to the tower car in %d legs, each ending at a hold in cover where the chain waits '
            'until the squads of that fight are dead, %d s at most (TriggerActorsDead, stock F07\'s form)' % (len(GATES) + 1, WAIT_S))
        gates = gates_plan(B, nav, S, P, opt, log)
    P['rt'] = collections.OrderedDict(blast_timer=blast, tower_park=[round(v, 1) for v in park], options=dict(opt), gates=gates)
    return nav, S, P


# ------------------------------------------------------------------ the street half
def street_plan(B, nav, S, opt, log=print):
    """-> dict: part, arrive (7 places for the hook), stations [{kind, what, node, places (7)}], steps, notes."""
    sc, notes = B.sc, []
    name = lambda k: sc.path[k][5:]
    jp, jpos, face = join_point(B)
    hit = nav.at(jpos[0], jpos[1], jpos[2], lo=jpos[1] - 300.0, hi=jpos[1] + 100.0)
    if hit is None:
        raise ValueError('the jump entry %s at (%d, %d, %d) is not over the navigation mesh' % (JOIN_NAME, *jpos))
    part = nav.part[hit[0]]
    if part == S['home']:
        raise ValueError('the jump entry is on the START row\'s own mesh part: this map needs no second leg (use kl_fa_bots)')
    j0 = (jpos[0], hit[1], jpos[2], hit[0])
    log('street: jump entry %s at (%d, %d, %d), floor %d, facing (%g, %g); its mesh part has %d polygons (the START row\'s %d)'
        % (JOIN_NAME, *jpos, hit[1], *face, nav.part_size[part], nav.part_size[S['home']]))
    lane_z0 = van.WAIT_Z - LANE_SOUTH
    # ---- where the hook puts the seven: in front of the car's door
    c = [q for q in nav.around(j0, ARRIVE[1], part, dy=60.0)
         if flat(nav, q) and (q[0] - jpos[0]) * face[0] + (q[2] - jpos[2]) * face[1] >= ARRIVE[0] and hdist(q, jpos) <= ARRIVE[1]]
    arrive = nav.spots(c, 7, ARRIVE_SEP, ref=(jpos[0] + face[0] * ARRIVE[0], hit[1], jpos[2] + face[1] * ARRIVE[0]))
    if len(arrive) < 7:
        raise ValueError('only %d arrival places in front of the jump entry (%d candidates)' % (len(arrive), len(c)))
    a1 = arrive[0]
    # ---- the van's stop
    act = S['action']
    ap = B.at(act)
    veh = S['vehicle'] and S['vehicle'][2]
    if rides_with_van(B, act):
        stop = (ap[0], ap[1], ap[2] + van.STOP_Z - van.WAIT_Z)
        log('street: the boarding box %s stands at (%d, %d, %d) = the van\'s waiting place (kl_fa_van WAIT_Z %d - %d behind its origin); it rides '
            'with the van to the stop: (%d, %d, %d)' % (name(act), *ap, van.WAIT_Z, street.BOARD_BACK, *stop))
    else:
        stop = ap
        notes.append('the boarding box %s at (%d, %d, %d) is not at kl_fa_van\'s waiting place: its own place is taken as the stop' % (name(act), *ap))
    sh = nav.at(stop[0], stop[1], stop[2], part=part, lo=stop[1] - 400.0, hi=stop[1] + 200.0)
    if sh is None:
        raise ValueError('the van\'s stop (%d, %d, %d) is not over the mesh part of the jump entry' % stop)
    s0 = (stop[0], sh[1], stop[2], sh[0])
    # ---- THE LANE. The van stands at its waiting place and drives north through the stop to the end of the map
    # (kl_fa_van: one straight line x = LANE_X); its nose carries a KillBox (kl_fa_street.VAN_CLEAR). The road's
    # polygons are 20 m wide, so the lane cannot be cut out of the mesh: instead every place from LANE_SOUTH before
    # the waiting place on lies on ONE side of the lane - the side the way from the lobby comes up on - and the
    # last legs are laid as straight lines that are tested to stay on the mesh and out of the lane.
    got = nav.path(a1, s0)
    if got is None:
        raise ValueError('no path on the mesh from the lobby to the van\'s stop')
    side = 1.0
    for p in got[0]:
        if p[2] >= lane_z0:
            break
        side = 1.0 if p[0] > van.LANE_X else -1.0
    good = lambda q: flat(nav, q) and (q[2] < lane_z0 or (q[0] - van.LANE_X) * side >= street.VAN_CLEAR)
    d_from = nav.dist_map(a1[3], a1[:3])[0]
    d_to = nav.dist_map(s0[3], s0[:3])[0]
    ring = [q for q in nav.around(s0, STOP_RING[1], part, dy=120.0) if good(q) and STOP_RING[0] <= hdist(q, s0) <= STOP_RING[1] and q[3] in d_from]
    if not ring:
        raise ValueError('no place %d..%d from the van\'s stop on the %s side of its lane' % (*STOP_RING, 'east' if side > 0 else 'west'))
    park0 = min(ring, key=lambda q: (hdist(q, s0), abs(q[2] - s0[2])))
    ring = [q for q in ring if hdist(q, park0) <= 420.0]

    def best(k, share, what, cost):
        c = [q for q in F.box_places(B, nav, k, part, share=share) if good(q) and q[3] in d_from and q[3] in d_to]
        if not c:
            notes.append('%s %s at (%d, %d, %d): no place inside it on the way' % (what, name(k), *B.at(k)))
            return None
        least = min(cost(q) for q in c)
        return max((q for q in c if cost(q) <= least + 120.0), key=lambda q: nav.clearance(*q[:3])), [q for q in c if cost(q) <= least + 400.0]

    seq = [('arrive', 'the lobby, in front of the car', a1, None, None)]
    for k in S['triggers'].get('EXITS', [])[:1]:
        got = best(k, F.INSIDE, 'EXITS_BANK', lambda q: d_from[q[3]] + d_to[q[3]])
        if got:
            seq.append(('exit', 'EXITS_BANK %s (stage 2)' % name(k), got[0], k, got[1]))
    lev = None
    for k in S['exits']:
        got = best(k, EXIT_SHARE, 'level exit', lambda q: d_from[q[3]] + math.dist(q[:3], nav.mid[q[3]]) + hdist(q, park0))
        if got and (lev is None or d_from[got[0][3]] < d_from[lev[2][3]]):
            lev = ('level', 'level exit %s (stage 3; a bot inside it calls the van: kl2 0x6cd8e0)' % name(k), got[0], k, got[1])
    if lev is None:
        raise ValueError('no level exit box with a place on the street part: the bots would never board')
    seq.append(lev)
    seq.append(('park', 'beside the van\'s stop, %d..%d from the boarding box, on the %s side of its lane' % (*STOP_RING, 'east' if side > 0 else 'west'), park0, None, ring))
    exits = S['exits']
    inbox = lambda q: bool(F.in_exit(B, exits, q))
    route, total = [], 0.0
    for (ka, _wa, a, _na, _ca), (kb, wb, b, nb_, cb) in zip(seq, seq[1:]):
        if straight(nav, part, a, b):
            pts = [a[:3], b[:3]]
        else:
            got = nav.path(a, b)
            if got is None:
                raise ValueError('no path on the street part from %s to %s' % (ka, kb))
            pts = got[0]
        length = sum(math.dist(p, q) for p, q in zip(pts, pts[1:]))
        total += length
        run, nxt = 0.0, F.SPACING
        for p, q in zip(pts, pts[1:]):
            d = math.dist(p, q)
            while d > 0 and run + d >= nxt and length - nxt > F.SPACING * 0.5:
                t = (nxt - run) / d
                m = tuple(p[i] + (q[i] - p[i]) * t for i in range(3))
                c = [x for x in nav.around(m, 260.0, part, dy=260.0) if good(x) and (kb != 'level' or not inbox(x))]
                s = (nav.spots(c, 1, 0.0, ref=m) or [None])[0]
                if s:
                    route.append(('way', 'on the way to %s' % kb, s, None, None))
                nxt += F.SPACING
            run += d
        route.append((kb, wb, b, nb_, cb))
    # the hold: the last station before the level exit box must lie outside it
    i_lev = next(i for i, r in enumerate(route) if r[0] == 'level')
    hold = float(opt['street_hold'])
    if hold > 0 and i_lev == 0:
        notes.append('no station before the level exit box: no hold')
        hold = 0.0
    places = []
    for i, (kind, what, anchor, node, cands) in enumerate(route):
        if cands:
            got = nav.spots(cands, 7, F.SEP, ref=anchor)
            if len(got) < 7:
                got = nav.spots(cands, 7, 50.0, ref=anchor) or got
        else:
            c = [x for x in nav.around(anchor, 260.0, part) if good(x) and (i > i_lev or not inbox(x))]
            got = nav.spots(c, 7, F.SEP, ref=anchor) or [anchor]
        if hold > 0 and i == i_lev - 1:
            kind, what = 'rally', 'the rally place before the level exit box (hold %g s)' % hold
        places.append({'kind': kind, 'what': what, 'node': name(node) if node else None, 'distinct_places': len(got),
                       'places': [[round(v, 1) for v in got[b % len(got)][:3]] for b in range(7)]})
        log('  %-6s %-84s round (%6d %5d %6d): %d distinct places, clearance %d..%d' % (
            kind, what[:84], *anchor[:3], len(got), min(nav.clearance(*g[:3]) for g in got), max(nav.clearance(*g[:3]) for g in got)))
    # steps: up to STEP_MAX places each; the hold splits them; a step does not END on a place all seven share
    # (kl_fa_bots: they would hold on the stairs)
    steps = []
    def cut(idx, base, word):
        chunk, n = [], 0
        for i in idx:
            chunk.append(i)
            keep = []
            if len(chunk) == F.STEP_MAX and places[i]['distinct_places'] < 7 and i != idx[-1]:
                keep = [chunk.pop()]
            if i == idx[-1] or len(chunk) >= F.STEP_MAX or keep:
                steps.append({'name': '%03d_DefendBehaviour_%s' % (base + n, word), 'stations': chunk})
                chunk, n = keep, n + 1
    first = list(range(i_lev)) if hold > 0 else list(range(len(places)))
    cut(first, 50, 'street')
    if hold > 0:
        steps.append({'name': '070_Timer_rally', 'hold': hold})
        cut(list(range(i_lev, len(places))), 80, 'to_van')
    if any(int(s['name'][:3]) >= 70 for s in steps if 'stations' in s and 'street' in s['name']):
        raise ValueError('too many street steps for the names')
    log('street: %d of path from the lobby to the stop, %d stations in %d steps%s; arrival places x %d..%d z %d..%d, %d..%d from the jump entry'
        % (total, len(places), len([s for s in steps if 'stations' in s]), ', a hold of %g s before the level exit box' % hold if hold > 0 else '',
           min(a[0] for a in arrive), max(a[0] for a in arrive), min(a[2] for a in arrive), max(a[2] for a in arrive),
           min(hdist(a, jpos) for a in arrive), max(hdist(a, jpos) for a in arrive)))
    for n in notes:
        log('  NOTE ' + n)
    return collections.OrderedDict(
        join={'node': JOIN_NAME, 'at': [round(v, 1) for v in jpos], 'facing': list(face), 'floor': round(hit[1], 1)},
        mesh_part_polygons=nav.part_size[part], arrive=[[round(v, 1) for v in a[:3]] for a in arrive],
        stop=[round(v, 1) for v in s0[:3]], boarding_box=name(act), vehicle=veh, lane_side='east' if side > 0 else 'west',
        lane_from_z=lane_z0, path_length=round(total), hold=hold, stations=places, steps=steps, notes=notes)


SQ = lambda N, tail='': '%s%sSquad#0%d%s' % (R_, F.SQUAD, N, tail)
LAST = '090_SquadModifier_tight_defense_van'


class Street:
    """The second leg, for kl_fa_bots.apply(more=...): nodes(M, tops) adds the street steps to the seven squads,
    edit(Jn) writes the JumpPoint's list. Every node is a clone of the F07 form kl_fa_bots.make uses."""

    def __init__(self, st, room=None, gates=None):
        self.st = st
        self.firsts = []
        self.room = room          # {'fallback': seconds after the round-start event} or None
        self.gates = gates or []  # gates_plan(): the holds of the tower's way out

    def gate_nodes(self, M, tops):
        """Behind the hold step of every gate a TriggerActorsDead (a clone of stock F07 Squad#02
        020_TriggerActorsDead_Lootarea, the node kl_fa_bots.make clones for --wait-guards): {0: the actor groups of
        the gate's squads, 1: 0, 2: the step kl_fa_bots.make had linked the hold step to}. And no sprint on the
        tower's way out: kl_fa_bots.make sprints every step behind the loot wait, and a bot that sprints was seen to
        run past its enemies (GUESS that it does not shoot: re/bots_dynamic.md 4; stock bots sprint on 92 of 1,100
        steps)."""
        waits = {g['step']: g for g in self.gates}
        for b, N in enumerate(F.BOTS):
            top = tops[b]
            if top.name != F.SQUAD + 'Squad#0%d' % N:
                raise ValueError('kl_fa_bots.make: squad %d is %s' % (N, top.name))
            done = 0
            for kid in list(top.kids):
                i = next((i for i, (nm, _b) in enumerate(kid.ctrls) if M.p.key(nm) == 'DefendBehaviourRout'), None)
                if i is None or '_DefendBehaviour_out_' not in kid.name:
                    continue
                M.set(kid, 'DefendBehaviourRout', {4: 'eDMS_NotSet'})
                g = waits.get(kid.name)
                if g is None:
                    continue
                nxt = [M.p.key(tok) for tok in [list(u) for u in units(kid.ctrls[i][1][1:-1])][7][1:]]
                if len(nxt) != 1:
                    raise ValueError('%s\\%s: %d next steps' % (top.name, kid.name, len(nxt)))
                w = top.add(M.clone('F07', SQ(2, '\\020_TriggerActorsDead_Lootarea'), g['wait']))
                M.place(w, (0.0, 0.0, 0.0))
                M.set(w, 'TriggerActorsDead', {0: list(g['groups']), 1: 0, 2: nxt})
                M.set(kid, 'DefendBehaviourRout', {7: [SQ(N, '\\' + g['wait'])]})
                done += 1
            if done != len(self.gates):
                raise ValueError('%s: %d of %d gates have a hold step' % (top.name, done, len(self.gates)))

    def nodes(self, M, tops):
        st, Sx = self.st, 'F07'
        if self.gates:
            self.gate_nodes(M, tops)
        if self.room:
            t = next(n for n in tops if n.name == F.SQUAD + 'Timer_start_bots')
            body = next(b for nm, b in t.ctrls if M.p.key(nm) == 'TriggerDelay2')
            first = [M.p.key(tok) for tok in [list(u) for u in units(body[1:-1])][4][1:]]      # the seven first steps
            gate = M.clone(Sx, R_ + 'Gameplay!RunToEscape!tcRunToEscape', GATE_NAME)
            M.place(gate, (0.0, 0.0, 0.0))
            M.set(gate, 'TriggerCounter', {0: 1, 1: 4294967295, 2: 0, 3: 0, 4: first})
            tops.append(gate)
            M.set(t, 'TriggerDelay2', {0: float(self.room['fallback']), 4: [R_ + GATE_NAME]})
        if st is None:
            return
        for b, N in enumerate(F.BOTS):
            top = tops[b]
            if top.name != F.SQUAD + 'Squad#0%d' % N:
                raise ValueError('kl_fa_bots.make: squad %d is %s' % (N, top.name))
            chain = [s['name'] for s in st['steps']] + [LAST]
            nxt = {a: [SQ(N, '\\' + c)] for a, c in zip(chain, chain[1:])}
            for s in st['steps']:
                if 'hold' in s:
                    w = top.add(M.clone(Sx, R_ + F.SQUAD + 'Timer_start_bots', s['name']))
                    M.place(w, (0.0, 0.0, 0.0))
                    M.set(w, 'TriggerDelay2', {0: float(s['hold']), 1: 0.0, 2: -1.0, 3: 0, 4: nxt[s['name']]})
                    continue
                g = top.add(M.clone(Sx, SQ(2, '\\020_DefendBehaviour_rout_merc_fight_left'), s['name']))
                M.place(g, (0.0, 0.0, 0.0))
                refs = []
                for j, si in enumerate(s['stations']):
                    box = g.add(M.clone(Sx, SQ(2, '\\020_DefendBehaviour_rout_merc_fight_left\\Pos#01'), 'Pos#%02d' % (j + 1)))
                    M.place(box, st['stations'][si]['places'][b])
                    refs.append(SQ(N, '\\%s\\Pos#%02d' % (s['name'], j + 1)))
                # eDMS_Sprint as on kl_fa_bots' way out (re/bots.md 8: ASSUMPTION that it suits)
                M.set(g, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_Sprint', 5: 'eDF_NotSet', 6: '', 7: nxt[s['name']], 8: 1, 9: 0})
            g = top.add(M.clone(Sx, SQ(2, '\\100_SquadModifier_tight_defense_van'), LAST))
            M.place(g, (0.0, 0.0, 0.0))
            M.set(g, 'SquadModifierBehaviour', {0: 'eLM_Leash', 9: 'eDM_Tight', 26: []})
            self.firsts.append(SQ(N, '\\' + chain[0]))

    def edit(self, Jn):
        if self.room:
            c = Jn.resolve(R_ + ROOM_COUNTER)[0]
            ci = next(i for i, (nm, _b) in enumerate(Jn.nodes[c]['ctrls']) if Jn.p.key(nm) == 'TriggerCounter')
            def fc(us):
                have = [Jn.p.key(t) for t in us[4][1:]]
                us[4] = kl_fa._refs(Jn, have + [R_ + GATE_NAME])
            kl_fa.edit(Jn, c, ci, fc)
        if self.st is None:
            return
        k = Jn.resolve(R_ + JOIN_NAME)[0]
        i = next(i for i, (nm, _b) in enumerate(Jn.nodes[k]['ctrls']) if Jn.p.key(nm) == 'JumpPoint')
        firsts = self.firsts
        def fn(us):
            have = [Jn.p.key(t) for t in us[0][1:]]
            us[0] = kl_fa._refs(Jn, have + [f for f in firsts if f.lower() not in [h.lower() for h in have]])
        kl_fa.edit(Jn, k, i, fn)


CREW_HEAD = """
; ---- [CrewJoin]: written by tools\\kl_fa_bots_rt.py. Read by KLHook's klcrew_rt.c, and only when KLHook.ini has
; [CrewJoin] Enable=1. The tower's navigation mesh does not reach the lobby, so the AI heisters cannot walk there.
; When kljoin.c's jump request for the entry named here is pending (the tick BEFORE the game moves the player), every
; AI heister still in play is put on one of the places below by the game's own actor teleport (kl2 0x62a900). The
; game then moves the player and sends 'AITrigger' to the entry's own list, which starts the bots' street route.
; Late form (the request was not seen pending): the same when a local player stands within Radius of Target after
; he was farther than From from it.
; Places = feet on the lobby's navigation mesh in front of the car's door, record order (the n-th AI crew record
; in play gets Place.n). Lift = added to the height of every place (0: the mesh height, as the level places a bot).
"""


def write_ini(dst, st, log=print):
    """Append the [CrewJoin] section to <dst>/KLJoin.ini (the file kl_fa_bots.apply copied from the source build)."""
    p = os.path.join(dst, 'KLJoin.ini')
    if not os.path.isfile(p):
        raise ValueError('%s: no KLJoin.ini (the build has no join)' % dst)
    text = open(p, encoding='latin1').read()
    if '[CrewJoin]' in text:
        text = text[:text.index('[CrewJoin]')].rstrip('\n')
        text = text[:text.rindex('; ---- [CrewJoin]')].rstrip('\n') + '\n' if '; ---- [CrewJoin]' in text else text + '\n'
    j = st['join']
    lines = [CREW_HEAD.rstrip('\n'), '[CrewJoin]', 'Name=%s' % JOIN_NAME.split('!')[-1], 'Target=%g %g %g' % tuple(j['at']), 'Tolerance=8',
             'Radius=300', 'From=2000', 'Lift=0', 'Places=%d' % len(st['arrive'])]
    lines += ['Place.%d=%g %g %g' % (i + 1, *a) for i, a in enumerate(st['arrive'])]
    with open(p, 'w', encoding='latin1', newline='\r\n') as f:
        f.write(text.rstrip('\n') + '\n' + '\n'.join(lines) + '\n')
    log('written %s: [CrewJoin] with %d places' % (p, len(st['arrive'])))


def read_ini(folder):
    """{'join': {...}, 'crew': {...}} of <folder>/KLJoin.ini (plain reading, as GetPrivateProfileString would)."""
    out, sec = collections.defaultdict(dict), None
    p = os.path.join(folder, 'KLJoin.ini')
    if not os.path.isfile(p):
        return out
    for ln in open(p, encoding='latin1'):
        ln = ln.strip()
        if ln.startswith('[') and ln.endswith(']'):
            sec = ln[1:-1].lower()
        elif sec and '=' in ln and not ln.startswith(';'):
            k, v = ln.split('=', 1)
            out[sec][k.strip().lower()] = v.strip()
    return out


def vec(s):
    return tuple(float(x) for x in s.replace(',', ' ').split())


# ------------------------------------------------------------------ the check of this module
def check(folder, log=print):
    """What kl_fa_bots.check does not look at: the balcony start, the gather place, the JumpPoint's list, the street
    chain on ITS mesh part, the van's lane, the [CrewJoin] places. -> ([(severity, text)], facts)."""
    B = F.Built(folder)
    sc, nav, out = B.sc, F.Nav(B.scene.nav), []
    fail = lambda s: out.append(('FAIL', s))
    note = lambda s: out.append(('NOTE', s))
    name = lambda k: sc.path[k][5:]
    res = sc.resolve
    S = F.stations(B, nav)
    home = S['home']
    facts = collections.OrderedDict()
    allies = sorted((k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor' and B.values(k)['ZFFActor[0]'] == 'Ally'), key=lambda k: sc.names[sc.top[k]])
    # 1. the start: on the balcony, outside the glass, after the blast
    (x0, x1), (z0, z1) = au.LEDGE
    feet = [B.at(k) for k in allies]
    off = [f for f in feet if not (x0 <= f[0] <= x1 and z0 <= f[2] <= z1)]
    if off:
        fail('%d bots do not start on the balcony (x %d..%d, z %d..%d), e.g. (%d, %d, %d): the glass at x 5860 keeps the players out until the blast'
             % (len(off), x0, x1, z0, z1, *off[0]))
    near = [f for f in feet if hdist(f, au.INVISIBOMB) < 300.0]
    if near:
        fail('%d bots start inside the InvisiBomb\'s first radius (300)' % len(near))
    blast = blast_seconds(B)
    tv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2') if res(R_ + F.SQUAD + 'Timer_start_bots') and k == res(R_ + F.SQUAD + 'Timer_start_bots')[0]]
    delay = tv[0][0] if tv else None
    facts['start'] = {'blast_timer': blast, 'Timer_start_bots': delay, 'bots': [[round(v) for v in f] for f in feet]}
    if blast is None or delay is None:
        fail('no blast timer or no Timer_start_bots')
    elif delay <= blast:
        fail('Timer_start_bots (%.1f s) does not wait for the blast timer (%.1f s): the bots would walk at the intact glass' % (delay, blast))
    gate = res(R_ + GATE_NAME)
    if gate:
        gv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if k == gate[0]][0]
        cv = [v for k, _i, v in kl_fa.controllers(sc, 'TriggerCounter') if res(R_ + ROOM_COUNTER) and k == res(R_ + ROOM_COUNTER)[0]]
        fed = cv and any(s.lower() == (R_ + GATE_NAME).lower() for s in cv[0][4])
        facts['room_gate'] = {'counter_names_gate': bool(fed), 'gate_count': gv[0], 'gate_names': len(gv[4]), 'fallback': delay}
        if not fed:
            fail('the room counter %s does not name %s' % (ROOM_COUNTER, GATE_NAME))
        if gv[0] != 1 or len(gv[4]) != len(F.BOTS) or any(not res(s) for s in gv[4]):
            fail('%s: count %d, names %d of %d first steps' % (GATE_NAME, gv[0], len(gv[4]), len(F.BOTS)))
        if tv and [s.lower() for s in tv[0][4]] != [(R_ + GATE_NAME).lower()]:
            fail('Timer_start_bots does not name the gate alone: %s' % tv[0][4])
    # 2. the chains
    NEXT = {'DefendBehaviourRout': 7, 'SquadModifierBehaviour': 26, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerActorsDead': 2}
    mine = {k for t in sc.tops() if sc.names[t].startswith(F.SQUAD) for k in range(t, sc.end[t])}
    ctrl_of = {}
    for cn in NEXT:
        for k, _i, v in kl_fa.controllers(sc, cn):
            if k in mine:
                ctrl_of[k] = (cn, v)

    # A RandomTrigger between two steps (kl_fa_bots_dyn's random routes; this module makes none): the chain forks.
    # As in kl_fa_bots.check, a chain is then walked once per BRANCH SET v: branch v mod (number of branches) at
    # every fork - so every branch of every fork is walked and checked. forks[0] = the widest fork met.
    rand_of = F.fork_branches(sc, mine)
    forks = [1]

    def chain(k, variant=0):
        """-> (places [node], index of the first place after a wait or None, ends tight, the wait's seconds, faults)"""
        places, seen, tight, n_wait, secs, bad = [], set(), False, None, None, []
        while k is not None and k not in seen:
            seen.add(k)
            if k in rand_of and k not in ctrl_of:
                br = rand_of[k]
                forks[0] = max(forks[0], len(br))
                k = br[variant % len(br)] if br else None
                continue
            cn, v = ctrl_of.get(k, (None, None))
            if cn is None:
                bad.append('the chain reaches %s, which has no behaviour or wait controller' % name(k)); break
            if cn == 'DefendBehaviourRout':
                places += [j for s in ([v[0]] if v[0] else []) + list(v[1]) for j in res(s)]
            elif cn == 'SquadModifierBehaviour':
                tight = v[9] == 'eDM_Tight'
            elif n_wait is None:
                n_wait, secs = len(places), v[0] if cn == 'TriggerDelay2' else v[1]
            nx = [j for s in v[NEXT[cn]] for j in res(s)]
            k = nx[0] if nx else None
        return places, n_wait, tight, secs, bad

    timer = res(R_ + F.SQUAD + 'Timer_start_bots')
    firsts = tv[0][4] if tv else []
    if gate:
        # (the room gate stands between the timer and the first steps. Until 2026-10-11 afternoon this check took the
        # timer's own list here - the gate alone - found no chain in any squad and SKIPPED the tests below without a
        # word: rt_full7 and z_route7 passed them unlooked at.)
        firsts = gv[4]
    jb = au.JOIN_BOX
    ally_boxes = [k for k, _i, _v in kl_fa.controllers(sc, 'AllyEscapeBox')]
    tower_end = {}
    first_of = {}
    for k in allies:
        top = sc.top[k]
        f = [j for s in firsts for j in res(s) if sc.top[j] == top]
        # (the tower's LAST place is behind every fork: a fork's branches rejoin before it. The places of the
        # tower's branches are kl_fa_bots.check's business, which walks every branch set)
        places, _nw, _t, _secs, _bad = chain(f[0]) if f else ([], None, False, None, [])
        if not places:
            fail('%s: no tower chain is started for it (Timer_start_bots%s names no step of its squad)' % (sc.names[top], ' / the room gate' if gate else ''))
            continue
        first_of[k] = f[0]
        last = B.at(places[-1])
        tower_end[sc.names[top]] = [round(v) for v in last]
        if rect_dist(last, jb) < 60.0:
            fail('%s: its last tower place (%d, %d, %d) is in or at the jump box of KLJoin.ini (x %d..%d, z %d..%d): the bots would stand where the '
                 'human has to walk' % (sc.names[top], *last, *jb[0], *jb[2]))
        if rect_dist(last, jb) > 1200.0:
            note('%s: its last tower place is %d from the jump box' % (sc.names[top], rect_dist(last, jb)))
        if not any(B.in_box(a, last) for a in ally_boxes):
            fail('%s: its last tower place is in no AllyEscapeBox (the fall-back when the hook part is off)' % sc.names[top])
    facts['tower_end'] = tower_end
    # 2b. the gates of the tower's way out: every TriggerActorsDead of a tower chain (TOWER_GATES; a build without
    # them has none and is only said so). What is tested is what the build HOLDS, read back from its nodes - with
    # kl_fa_bots_dyn's forks every branch set, as above.
    bj = os.path.join(B.folder, 'bots.json')
    planned = [g['wait'] for g in ((json.load(open(bj)).get('plan') or {}).get('rt') or {}).get('gates') or []] if os.path.isfile(bj) else None
    e_squads = enemy_squads(B)
    squad_of = {g: t for t, gs in e_squads.items() for g in gs}
    boxes, other = wake_map(B, e_squads)
    known = {t for t, why in other.items() if why}
    covers = cover_boxes(B)
    short = lambda t: name(t).split('!')[-1]
    g_said, g_facts, g_lists, g_never = set(), collections.OrderedDict(), {}, collections.OrderedDict()
    g_woken, g_asked, g_base, g_recs, g_join = collections.OrderedDict(), [], {}, [], collections.OrderedDict()
    posts = enemy_posts(B, e_squads)
    pkey = lambda q: tuple(round(x) for x in q)

    def g_fail(s):
        if s not in g_said:
            g_said.add(s); fail(s)

    def g_note(s):
        if s not in g_said:
            g_said.add(s); note(s)

    def items(k, variant):
        out, seen = [], set()
        while k is not None and k not in seen:
            seen.add(k)
            if k in rand_of and k not in ctrl_of:
                br = rand_of[k]
                forks[0] = max(forks[0], len(br))
                k = br[variant % len(br)] if br else None
                continue
            if k not in ctrl_of:
                break
            cn, v = ctrl_of[k]
            out.append((k, cn, v))
            nx = [j for s in v[NEXT[cn]] for j in res(s)]
            nx = [j for j in nx if j in ctrl_of] or [j for j in nx if j in rand_of]
            k = nx[0] if nx else None
        return out

    g_jobs = [(k, 0) for k in allies if k in first_of]
    for k, variant in g_jobs:
        sq = sc.names[sc.top[k]]
        forks[0] = 1
        its = items(first_of[k], variant)
        if variant == 0 and forks[0] > 1:
            g_jobs += [(k, v_) for v_ in range(1, forks[0])]
        waits = [(i, it) for i, it in enumerate(its) if it[1] == 'TriggerActorsDead']
        named = []                                      # per wait: the squads it names
        for _i, (wk, _cn, v) in waits:
            ts = set()
            for s in v[0]:
                hit = res(s)
                acts = [c for j in hit for c in range(j, sc.end[j]) if sc.cls(c) == 'ZFFActor']
                if len(hit) != 1 or len(acts) != 1 or hit[0] not in squad_of:
                    g_fail('%s: %s names %s: %d node(s), %d actor(s), %s (stock: one ZGROUP with ONE Enemy ZFFActor - a group with several is '
                           '\'dead\' as soon as one of them is, kl2 0x5f44d0)' % (sq, sc.names[wk], s[5:], len(hit), len(acts),
                                                                               'an Enemy\'s group' if hit and hit[0] in squad_of else 'not the group of an Enemy actor'))
                else:
                    ts.add(squad_of[hit[0]])
            for t in sorted(ts):
                got = sum(1 for s in v[0] for j in res(s) if squad_of.get(j) == t)
                if got != len(e_squads[t]):
                    g_fail('%s: %s names %d of the %d men of %s: the others are not waited for' % (sq, sc.names[wk], got, len(e_squads[t]), short(t)))
            if not v[0]:
                g_fail('%s: %s names nobody (an empty list is \'all dead\': it fires at once)' % (sq, sc.names[wk]))
            if len(v[0]) > GATE_MAX:
                g_note('%s names %d groups (stock: %d at most)' % (sc.names[wk], len(v[0]), GATE_MAX))
            if v[1]:
                g_note('%s: field 1 is %s (0 in all 120 stock uses)' % (sc.names[wk], v[1]))
            named.append(ts)
            g_lists.setdefault(sc.names[wk], {})[sq] = tuple(sorted(s.lower() for s in v[0]))
        prev, woken, counted, wi, hold, hold_step, length, entered, told = B.at(k), set(), set(), 0, None, None, 0.0, set(), set()
        leg_from, leg_pts, leg_boxes = B.at(k), [], []          # the way since the last wait: where it began, its points, the boxes it is in
        for i, (nk, cn, v) in enumerate(its):
            if cn == 'DefendBehaviourRout':
                for j in [j for s in ([v[0]] if v[0] else []) + list(v[1]) for j in res(s)]:
                    p = B.at(j)
                    if nav.at(p[0], p[1], p[2], dy=15.0) is None or nav.part[nav.at(p[0], p[1], p[2], dy=15.0)[0]] != home:
                        break                           # (the street chain is not walked here; kl_fa_bots.check FAILs a tower place off the mesh)
                    got = way_samples(nav, prev, p)
                    if got is not None:
                        length += got[1]
                        leg_pts += got[0]
                        for m in got[0]:
                            for bk in boxes:
                                if in_trigger(B, bk, m):
                                    woken |= boxes[bk]
                                    entered.add(bk)
                                    if bk not in leg_boxes:
                                        leg_boxes.append(bk)
                    prev, hold, hold_step = p, p, (nk, v)
            elif cn == 'TriggerLootDepleted':
                leg_from, leg_pts, leg_boxes = prev, [], []
            elif cn == 'TriggerActorsDead':
                ts = named[wi]
                later = set().union(*named[wi + 1:]) - set().union(*named[:wi + 1]) if named[wi + 1:] else set()
                if hold is None:
                    g_fail('%s: %s stands before the first place of the chain' % (sq, sc.names[nk]))
                    wi += 1
                    continue
                near = min([math.dist(hold, c) for _ck, c in covers if abs(c[1] - hold[1]) <= 260.0] or [1e9])
                if near > HOLD_COVER:
                    g_fail('%s: its hold before %s, (%d, %d, %d), is %d from the nearest cover box (DefendCover takes one within %d of the defend '
                           'position, kl2 0x84dc90): it would fight standing in the open' % (sq, sc.names[nk], *hold, near, HOLD_COVER))
                # (who is awake: the first criminal through a box wakes its squads for everybody, so this is asked of
                # all seven ways together, behind the loop)
                g_woken.setdefault(sc.names[nk], set()).update(woken)
                g_asked.append((sq, sc.names[nk], set(ts), set(woken)))
                # another way of a fork (kl_fa_bots_dyn's random routes) goes through no trigger box that wakes somebody
                # and that the build's own way to the same hold keeps out of (kl_fa_bots_dyn.Routes.wakes_more: its
                # first try sent one bot, one round in three, round the north of the atrium alone)
                if variant == 0:
                    g_base[(sq, sc.names[nk])] = set(entered)
                elif entered - g_base.get((sq, sc.names[nk]), set()) - told:
                    more = sorted(entered - g_base.get((sq, sc.names[nk]), set()) - told)
                    told.update(more)                   # (said at the first hold behind it, not at every one after)
                    g_fail('%s: one of the other ways of a fork before %s goes through %s, which wakes %s: a trigger box the build\'s own way '
                           'to that hold keeps out of' % (sq, sc.names[nk], ', '.join(name(bk).split('!')[-1] for bk in more),
                                                           ', '.join(sorted({short(t) for bk in more for t in boxes[bk]}))))
                # (the hold against the boxes of later fights, the posts of the men and the way past them: behind the
                # loop, where all seven holds of a gate and what the gates before it have dealt with are known)
                g_recs.append({'sq': sq, 'w': sc.names[nk], 'variant': variant, 'hold': hold, 'from': leg_from, 'pts': leg_pts, 'on': list(leg_boxes),
                               'ts': set(ts), 'before': set().union(*named[:wi]) if wi else set(), 'later': later})
                leg_from, leg_pts, leg_boxes = hold, [], []
                if hold_step[1][4] == 'eDMS_Sprint':
                    g_note('%s: the step to the hold before %s sprints (a sprinting bot was seen to run past its enemies)' % (sq, sc.names[nk]))
                counted |= ts
                if variant == 0:
                    g_facts.setdefault(sc.names[nk], collections.OrderedDict(squads=[short(t) for t in sorted(ts)], men=len(v[0]), holds={}, from_cover=[],
                                                                             path_so_far=[], woken_for_a_later_gate=set()))
                    f_ = g_facts[sc.names[nk]]
                    f_['holds'][sq[-2:]] = [round(x) for x in hold]
                    f_['from_cover'].append(round(near)); f_['path_so_far'].append(round(length))
                    f_['woken_for_a_later_gate'] |= {short(t) for t in woken & later}
                wi += 1
        if variant == 0:
            g_join[sq] = ([sc.names[it[0]] for _i, it in waits], [sc.names[it[0]] for it in its if it[1] == 'TriggerLootDepleted'])
            g_never[sq] = sorted(short(t) for t in woken - counted - known)
            if planned is not None and [sc.names[it[0]] for _i, it in waits] != planned:
                g_fail('%s: bots.json says the build was made with the gates %s; its chain has %s' % (sq, planned, [sc.names[it[0]] for _i, it in waits]))
    for wname in g_woken:
        ts = set().union(*[t_ for _sq, w_, t_, _own in g_asked if w_ == wname])
        asleep = sorted(t for t in ts if t not in g_woken[wname] and t not in known)
        if asleep:
            g_fail('%s: no bot\'s way to its hold goes through a trigger box that wakes %s: a squad that has not been woken is not dead (its '
                   'actors\' state byte is not 0, kl2 0x5f449c), the wait can only run out (%d s)' % (wname, ', '.join(short(t) for t in asleep), WAIT_S))
        alone = sorted({sq_[-2:] for sq_, w_, t_, own in g_asked if w_ == wname and any(t not in own and t not in known for t in t_)})
        if alone and not asleep and wname in g_facts:
            g_facts[wname]['woken_by_the_others_for'] = alone
    # THE HOLDS AGAINST THE FIGHTS (after the review of the first gates build, re/retomoto_bots_rooms_review.md D3 / D4),
    # gate by gate in the order of the chain:
    #   a. no cover box in reach of a hold (HOLD_COVER) has a place of its standing ring in the trigger box of a LATER
    #      fight, and no hold stands in one - but for a box the seven cannot go round (a stair ends in it, or it lies
    #      across the way: tripped before anybody holds) and a box whose men have no post on the hold's floor (said);
    #   b. no hold within POST_KEEP of a post of a man who may be alive;
    #   c. no way to a hold - every way of a fork - walks PAST a post of a squad this gate names and no earlier gate
    #      has dealt with: within PASS_NEAR of it and then more than PASS_ON further;
    #   d. said, not failed: the squads of a gate none of whose posts has a straight line on the mesh from a hold
    #      (whether they can be hit from there is a bet), and the waits that are armed before the bot has left the
    #      place before (ARRIVE_3D).
    engaged, woken_prev, all_named = set(), set(), set().union(*[r['ts'] for r in g_recs]) if g_recs else set()
    for wname in g_woken:
        recs = [r for r in g_recs if r['w'] == wname]
        r0 = [r for r in recs if r['variant'] == 0]
        if not r0:
            continue
        ts = set().union(*[r['ts'] for r in recs])
        before = set().union(*[r['before'] for r in recs])
        later = set().union(*[r['later'] for r in recs])
        live = set(e_squads) - known - (before - ts)
        forced = []
        for r in r0:
            forced += [bk for bk in cannot_go_round(B, nav, r['on'], r['from'], r['hold']) if bk not in forced]
        f_ = g_facts.get(wname, {})
        early, in_reach, d_post = collections.OrderedDict(), set(), []
        for r in r0:
            sq, hold = r['sq'], r['hold']
            # a. the boxes of later fights. ('A hold INSIDE the trigger box of a later fight' is the first round's rule;
            # the one thing taken out of it since is a box the seven cannot go round - `forced`, measured on the mesh
            # here, not taken from the plan: it is tripped before anybody holds, and the holds at the foot of the two
            # flights of stairs stand in such boxes on purpose.)
            mine_or_awake = lambda bk: boxes[bk] & (ts | before)
            inside = [bk for bk in boxes if in_trigger(B, bk, hold) and boxes[bk] & later and not mine_or_awake(bk) and bk not in forced]
            if inside:
                g_fail('%s: its hold before %s, (%d, %d, %d), lies INSIDE %s, the trigger box of a later fight (%s): it wakes them while it '
                       'waits for the others' % (sq, wname, *hold, name(inside[0]), ', '.join(short(t) for t in sorted(boxes[inside[0]] & later))))
            for ck, c in reach_covers(covers, hold):
                in_reach.add(ck)
                for bk, share in ring_in(B, c, hold[1], [bk for bk in boxes if not mine_or_awake(bk) and bk not in forced]).items():
                    lat, nobody = boxes[bk] & later, boxes[bk] - known - all_named
                    if lat and any(abs(q[1] - hold[1]) <= FLOOR_DY for t in lat for _w, q, _r in posts.get(t, ())):
                        g_fail('%s: its hold before %s, (%d, %d, %d), is within %d of the cover box %s at (%d, %d), and %d %% of the places round that '
                               'box lie in %s, the trigger box of a later fight (%s): DefendCover takes any box in that reach and chooses the side '
                               'itself' % (sq, wname, *hold, HOLD_COVER, sc.names[ck], c[0], c[2], 100 * share, name(bk).split('!')[-1],
                                           ', '.join(short(t) for t in sorted(lat))))
                    elif lat or nobody:
                        early.setdefault(name(bk).split('!')[-1], set()).update(short(t) for t in (lat or nobody))
            # b. the posts
            np_ = near_post(hold, posts, live)
            d_post.append(min([hdist(hold, q) for t in live for _w, q, _r in posts.get(t, ()) if abs(q[1] - hold[1]) <= FLOOR_DY] or [1e9]))
            if np_:
                g_fail('%s: its hold before %s, (%d, %d, %d), is %d from a post of %s (%s at (%d, %d, %d)), a man who may be alive when the bot '
                       'stands there (the campaign posts its men at the same cover boxes): wanted %d' % (sq, wname, *hold, np_[0], short(np_[1]), np_[2], *np_[3], POST_KEEP))
        # c. the walk past, every way of every fork
        for r in recs:
            wp = passes(r['pts'], [(t, what, q) for t in r['ts'] for what, q in posts_then(posts, t, woken_prev) if pkey(q) not in engaged])
            if wp:
                g_fail('%s: %s way to its hold before %s passes %d from a post of %s (%s at (%d, %d, %d)) and goes on for %d: the hold lies BEYOND '
                       'men this gate waits for and no gate before it has dealt with - the bot walks on with its back to them (wanted: at most %d '
                       'of way left once it is within %d of such a post)'
                       % (r['sq'], 'its' if r['variant'] == 0 else 'another', wname, wp[3], short(wp[0]), wp[1], *wp[2], wp[4], PASS_ON, PASS_NEAR))
        # d. what this gate can be said to have dealt with; what is only a bet
        holds0 = [r['hold'] for r in r0]
        blind, far, sight = [], [], collections.OrderedDict()
        for t in sorted(ts):
            here = [q for _w, q, _r in posts.get(t, ()) if abs(q[1] - holds0[0][1]) <= FLOOR_DY]
            seen = [q for q in here if any(mesh_line(nav, home, h, q) for h in holds0)]
            near = [q for q in here if any(((way_samples(nav, h, q) or (None, 1e9))[1]) <= ENGAGE for h in holds0)]
            engaged |= {pkey(q) for q in near}
            sight[short(t)] = {'posts': len(posts.get(t, ())), 'on_this_floor': len(here), 'straight_line_on_the_mesh': len(seen), 'dealt_with': len(near)}
            if not seen:
                blind.append('%s (%s)' % (short(t), 'its posts are on another floor' if not here else '%d post(s) on this floor' % len(here)))
            if not near:
                far.append(short(t))
        if far:
            g_note('%s names %s, and no post of theirs is on the holds\' floor within %d m of path of a hold: OUT OF REACH - the wait runs out unless '
                   'these men come to the seven (run G1_DM09: the first gallery gate named four such men, ran its whole %d s, and a bot was shot '
                   'dead at his hold while it ran)' % (wname, ', '.join(far), ENGAGE / 100, WAIT_S))
        if blind:
            g_note('%s: no straight line on the mesh from any hold to any post of %s. Whether these men can be hit from the holds is not read (a '
                   'line across open air, over a rail or past a prop is not one on the mesh); if not, the wait runs its %d s' % (wname, '; '.join(blind), WAIT_S))
        if early:
            g_note('%s: a cover box in reach of a hold has places in %s - not failed: %s' % (wname, ', '.join(early), '; '.join(
                '%s wakes %s' % (b_, ', '.join(sorted(v_)) + (' (a later gate\'s men; no post of theirs on this floor)' if any(x in {short(t) for t in later} for x in v_)
                                                             else ' (waited for by no gate)')) for b_, v_ in early.items())))
        soon = [r for r in r0 if math.dist(r['from'], r['hold']) < ARRIVE_3D]
        stair = [r for r in soon if abs(r['from'][1] - r['hold'][1]) > FLOOR_DY]
        if stair:
            g_note('%s: %d of the seven holds lie within %d m (3D) of the bot\'s place before ON ANOTHER FLOOR: the step is \'there\' at once (kl2 '
                   '0x686c4c) and the wait is armed a stair\'s way before the bot stands at the hold' % (wname, len(stair), ARRIVE_3D / 100))
        if f_ is not None and wname in g_facts:
            f_.update(nearest_post=[round(min(d_post)), round(max(d_post))], covers_in_reach=len(in_reach), no_way_round=[name(bk).split('!')[-1] for bk in forced],
                      sight=sight, armed_before_the_bot_has_left=len(soon), of_those_on_another_floor=len(stair))
        woken_prev = set(g_woken[wname])
    for wname, per in g_lists.items():
        if len(per) != len(allies) or len(set(per.values())) != 1:
            g_fail('%s: %d of %d squads have it, with %d different lists (a gate names the same men for all seven)' % (wname, len(per), len(allies), len(set(per.values()))))
    for f_ in g_facts.values():
        f_['woken_for_a_later_gate'] = sorted(f_['woken_for_a_later_gate'])
        f_['from_cover'] = [min(f_['from_cover']), max(f_['from_cover'])]
        f_['path_so_far'] = [min(f_['path_so_far']), max(f_['path_so_far'])]
    facts['gates'] = g_facts
    never = sorted({t for ts in g_never.values() for t in ts})
    facts['woken_and_never_waited_for'] = never
    if g_facts:
        if never:
            note('the tower chains walk through trigger boxes that wake %d squad(s) no gate waits for: %s' % (len(never), ', '.join(never)))
    else:
        note('NO GATES: the tower chain has no TriggerActorsDead - behind the loot wait the seven walk to the tower car without a stop '
             '(a build made with --no-gates, or before 2026-10-11 afternoon; runs T7 / R7a..d_DM09: six of seven dead 40..60 m further in)')
    # 3. the JumpPoint and the street chain
    ini = read_ini(B.folder)
    jp = res(R_ + JOIN_NAME)
    jv = [v for k, _i, v in kl_fa.controllers(sc, 'JumpPoint') if jp and k == jp[0]]
    lst = jv[0][0] if jv else []
    facts['jump_list'] = len(lst)
    if not lst:
        note('TOWER ONLY: %s names nothing; the bots end beside the tower car and board through the AllyEscapeBox' % JOIN_NAME)
        if 'crewjoin' in ini:
            fail('KLJoin.ini has a [CrewJoin] section but the JumpPoint starts no street route: the hook would move bots that have no way on')
    else:
        # THE JOIN AND THE WAITS OF THE TOWER CHAIN (re/retomoto_bots_rooms_review.md D1). The jump starts the street
        # step of every squad and the hook moves the bots; nothing ends the tower chain. A wait of it that is ARMED at
        # that moment still fires - a TriggerActorsDead at the latest 30 s after it was armed (kl2 0x4afbbd / 0x8df00b),
        # the loot wait after its seconds - and sends 'AITrigger' to the next TOWER step, which has not run and so
        # starts (0x4ebed0) for a bot that stands in the street: ASSUMED to replace its street step, which cannot be
        # started again (field 8). The chain of 2026-10-11 morning had one such wait a bot (the loot table), a gates
        # build has one more per gate. Not armed = not exposed: a bot that walks between two holds, and one at a hold
        # whose men are dead (its wait fires at once). Said here with the number; what such a bot does is NOT
        # established - no joined run with bots has been made at all.
        n_g = sorted({len(a) for a, _b in g_join.values()})
        n_l = sorted({len(b) for _a, b in g_join.values()})
        facts['join_waits'] = {'gates': n_g, 'loot': n_l}
        if n_g and n_g[-1]:
            note('THE JOIN: every bot has %s gate wait(s) and %s loot wait(s) in its tower chain. One that is armed when the human takes the join '
                 'fires up to 30 s later and starts the next TOWER step for a bot the hook has moved to the street; a bot that walks, or holds '
                 'where the men are dead, has none armed. What the late step does to that bot is NOT ESTABLISHED: one joined run with bots '
                 'waiting at a gate is owed before this build goes on the tab (re/retomoto_bots_rooms.md 7, run J1; [Bots] BoardAll=1 raises a '
                 'bot that stands once the van has been called)' % ('..'.join(str(x) for x in n_g), '..'.join(str(x) for x in n_l)))
        jpos = B.at(jp[0])
        j = ini.get('join', {})
        if j.get('name', '') not in JOIN_NAME or 'target' not in j or max(abs(a - b) for a, b in zip(vec(j['target']), jpos)) > float(j.get('tolerance', 8)):
            fail('KLJoin.ini [Join] (Name %s, Target %s) does not name %s at (%d, %d, %d)' % (j.get('name'), j.get('target'), JOIN_NAME, *jpos))
        hit = nav.at(jpos[0], jpos[1], jpos[2], lo=jpos[1] - 300.0, hi=jpos[1] + 100.0)
        part = hit and nav.part[hit[0]]
        if hit is None or part == home:
            fail('the jump entry is not on a mesh part of its own')
        tgt = [x for s in lst for x in res(s)]
        if len(tgt) != len(lst):
            fail('%s: %d of its %d list entries do not resolve' % (JOIN_NAME, len(lst) - len(tgt), len(lst)))
        tops = collections.Counter(sc.top[x] for x in tgt)
        if set(tops) != {sc.top[k] for k in allies} or any(n != 1 for n in tops.values()):
            fail('%s names %d steps in %d squads (wanted: one first street step in each of the %d)' % (JOIN_NAME, len(tgt), len(tops), len(allies)))
        if any(ctrl_of.get(x, (None,))[0] != 'DefendBehaviourRout' for x in tgt):
            fail('%s names something that is no DefendBehaviourRout step (kl2 0x72e0f0 sends it \'AITrigger\')' % JOIN_NAME)
        act = S['action']
        ap = B.at(act)
        stop = (ap[0], ap[1], ap[2] + van.STOP_Z - van.WAIT_Z) if rides_with_van(B, act) else ap
        if hit and nav.at(stop[0], stop[1], stop[2], part=part, lo=stop[1] - 400.0, hi=stop[1] + 200.0) is None:
            fail('the van\'s stop (%d, %d, %d) is not over the street\'s mesh part: ZBoardEscapeVehicleTactic\'s path test would fail' % stop)
        crew = ini.get('crewjoin', {})
        arr = [vec(crew['place.%d' % (i + 1)]) for i in range(int(crew.get('places', 0))) if 'place.%d' % (i + 1) in crew]
        facts['crew_places'] = [[round(v) for v in a] for a in arr]
        if len(arr) < len(allies):
            fail('KLJoin.ini [CrewJoin] has %d places for %d bots' % (len(arr), len(allies)))
        if crew and (crew.get('name', '') not in JOIN_NAME or max(abs(a - b) for a, b in zip(vec(crew.get('target', '0 0 0')), jpos)) > 8):
            fail('KLJoin.ini [CrewJoin] Name / Target do not name the jump entry')
        ah = []
        for a in arr:
            h = nav.at(a[0], a[1], a[2], dy=15.0, part=part)
            if h is None or warp(nav, h[0]) > WARP:
                fail('[CrewJoin] place (%d, %d, %d) is not on a flat polygon of the street part at its height' % a); continue
            ah.append(tuple(a) + (h[0],))
            if nav.clearance(*a) < F.CLEAR_MIN:
                fail('[CrewJoin] place (%d, %d, %d) is %d from a mesh edge without a neighbour' % (*a, nav.clearance(*a)))
            if hdist(a, jpos) < 150.0:
                fail('[CrewJoin] place (%d, %d, %d) is %d from the jump entry: a bot would be put into the player' % (*a, hdist(a, jpos)))
        apart = min([hdist(a, b) for i, a in enumerate(arr) for b in arr[i + 1:]] or [0])
        if arr and apart < 80.0:
            fail('two [CrewJoin] places are %d apart' % apart)
        routes = collections.OrderedDict()
        enters_exit = S['triggers'].get('EXITS', [])
        jobs = [(x, 0) for x in sorted(tgt, key=lambda x: sc.names[sc.top[x]])]
        said, variant = set(), 0
        fail = lambda s: None if (variant and ('FAIL', s) in said) else (said.add(('FAIL', s)), out.append(('FAIL', s)))[0]
        note = lambda s: None if (variant and ('NOTE', s) in said) else (said.add(('NOTE', s)), out.append(('NOTE', s)))[0]
        branch_sets = collections.OrderedDict()
        for x, variant in jobs:                         # (a further branch set of a forking chain: findings said once)
            sq = sc.names[sc.top[x]]
            forks[0] = 1
            places, n_wait, tight, secs, bad = chain(x, variant)
            if variant == 0 and forks[0] > 1:
                jobs += [(x, n_v) for n_v in range(1, forks[0])]
                branch_sets[sq] = forks[0]
            for t in bad:
                fail('%s (street): %s' % (sq, t))
            pts, low, ok = [], 1e9, True
            for jn in places:
                p = B.at(jn)
                h = nav.at(p[0], p[1], p[2], dy=15.0)
                if h is None:
                    fail('%s (street): %s at (%d, %d, %d) is not on a walkable polygon within 15 of the mesh\'s height' % (sq, name(jn), *p)); ok = False; continue
                if nav.part[h[0]] != part:
                    fail('%s (street): %s at (%d, %d, %d) is not on the jump entry\'s mesh part' % (sq, name(jn), *p)); ok = False; continue
                if warp(nav, h[0]) > WARP:
                    fail('%s (street): %s stands on a polygon whose fitted height is off by %d' % (sq, name(jn), warp(nav, h[0])))
                c = nav.clearance(*p)
                low = min(low, c)
                if c < F.CLEAR_MIN:
                    fail('%s (street): %s at (%d, %d, %d): %d from a mesh edge without a neighbour' % (sq, name(jn), *p, c))
                if lane(p):
                    fail('%s (street): %s at (%d, %d, %d) is in the van\'s lane (x %d +- %d from z %d): its nose carries a KillBox' % (sq, name(jn), *p, van.LANE_X, street.VAN_CLEAR, van.WAIT_Z - LANE_SOUTH))
                pts.append(tuple(p) + (h[0],))
            if not ok or not pts:
                continue
            # a way from EVERY [CrewJoin] place (the hook gives places by record order, not by squad) through the places
            length, cross = 0.0, 0
            for a in ah:
                poly = walk(nav, [a] + pts)
                if poly is None:
                    fail('%s (street): no path on the mesh from [CrewJoin] place (%d, %d, %d) along its places' % (sq, *a[:3])); break
                length = max(length, sum(math.dist(p, q) for p, q in zip(poly, poly[1:])))
            # the van's lane: from LANE_SOUTH before its waiting place on, every place on ONE side of it, and the
            # straight line from each place to the next on the mesh and out of the lane (the road's polygons are too
            # large for this module's portal path to say where a walker goes; a straight line that is all mesh is
            # the way any pathfinder takes)
            zone = [i for i, p in enumerate(pts) if p[2] >= van.WAIT_Z - LANE_SOUTH]
            sides = {p[0] > van.LANE_X for i, p in enumerate(pts) if i in zone}
            if len(sides) > 1:
                fail('%s (street): its places lie on BOTH sides of the van\'s lane: it would cross it' % sq)
            for i in zone:
                if i and not straight(nav, part, pts[i - 1], pts[i]):
                    cross += 1
            if cross:
                note('%s (street): %d legs near the van are not a straight line on the mesh clear of its lane (the pathfinder\'s way there is not known)' % (sq, cross))
            st2 = any(B.in_box(t, p[:3]) for t in enters_exit for p in pts)
            st3 = [i for i, p in enumerate(pts) if F.in_exit(B, S['exits'], p[:3])]
            if not st2:
                note('%s (street): no place inside an EXITS_BANK box (stage 2 is skipped; stage 3 does not need it)' % sq)
            if not st3:
                fail('%s (street): no place inside the level exit box: no stage 3, the bot never boards (kl2 0x4faf60)' % sq)
            elif n_wait is not None and st3[0] < n_wait:
                fail('%s (street): place %d is inside the level exit box BEFORE the hold: the van is called before the squad has gathered' % (sq, st3[0] + 1))
            call = F.first_exit_entry(B, nav, S['exits'], [ah[0]] + pts) if S['exits'] and ah else None
            if call and n_wait is not None and call[1] <= n_wait:
                fail('%s (street): the path enters the level exit box on the way to place %d of the %d before the hold' % (sq, call[1], n_wait))
            d = hdist(pts[-1], stop)
            if not STOP_RING[0] - 1 <= d <= STOP_RING[1] + 1:
                fail('%s (street): its last place is %d from the boarding box at the stop (wanted %d..%d)' % (sq, d, *STOP_RING))
            if not tight:
                note('%s (street): the chain does not end in a tight-defense SquadModifierBehaviour' % sq)
            route = {'places': [[round(v) for v in p[:3]] for p in pts], 'path_length_longest': round(length), 'least_clearance': round(low),
                     'stage_2': st2, 'stage_3_from_place': st3[0] + 1 if st3 else None, 'places_before_the_hold': n_wait, 'hold_seconds': secs,
                     'first_inside_the_exit_box': call and {'path': round(call[0]), 'place': call[1]}, 'last_place_from_the_stop': round(d),
                     'legs_near_the_van_not_straight': cross, 'side_of_the_lane': 'east' if sides == {True} else 'west' if sides == {False} else None}
            if variant == 0:
                routes[sq] = route
            else:
                facts.setdefault('street_branches', collections.OrderedDict()).setdefault(sq, []).append(route)
        variant = 0
        if branch_sets:
            log('street forks (a RandomTrigger between two steps): every branch walked and checked, in up to %d branch sets a squad' % max(branch_sets.values()))
        facts['street'] = routes
        facts['stop'] = [round(v) for v in stop]
    facts['big'] = F.sizes(folder)
    out.sort(key=lambda x: x[0] != 'FAIL')
    for sev, text in out:
        log('%-4s %s' % (sev, text))
    for nm, r in facts.get('street', {}).items():
        log('  %s street: %d places, longest path %d, least clearance %d, stage 2 %s, stage 3 from place %s, hold after place %s (%s s), last place %d from the stop'
            % (nm, len(r['places']), r['path_length_longest'], r['least_clearance'], r['stage_2'], r['stage_3_from_place'], r['places_before_the_hold'], r['hold_seconds'], r['last_place_from_the_stop']))
    for wname, f_ in facts.get('gates', {}).items():
        hs = list(f_['holds'].values())
        log('  gate %-34s %d men of %s; the seven hold x %d..%d z %d..%d y %d, %d..%d from a cover box, %d..%d of path from the balcony%s%s%s'
            % (wname, f_['men'], ', '.join(f_['squads']), min(h[0] for h in hs), max(h[0] for h in hs), min(h[2] for h in hs), max(h[2] for h in hs),
               hs[0][1], *f_['from_cover'], *f_['path_so_far'],
               '; on the way a later gate\'s men are woken: %s' % ', '.join(f_['woken_for_a_later_gate']) if f_['woken_for_a_later_gate'] else '',
               '; squads %s hold short of the box that wakes some of these men (the others\' ways go through it)' % ' '.join(f_['woken_by_the_others_for'])
               if f_.get('woken_by_the_others_for') else '',
               '; nearest post of a man who may be alive %d..%d; %d cover boxes within %d of a hold%s; posts with a straight line on the mesh from a hold: %s'
               % (*f_['nearest_post'], f_['covers_in_reach'], HOLD_COVER,
                  '; no way round %s' % ', '.join(f_['no_way_round']) if f_['no_way_round'] else '',
                  ', '.join('%s %d of %d' % (n_.replace('Atrium_', '').replace('_Squad_01', ''), s_['straight_line_on_the_mesh'], s_['posts'])
                            for n_, s_ in f_['sight'].items())) if 'nearest_post' in f_ else ''))
    log('RESULT (kl_fa_bots_rt): %s (%d FAIL, %d NOTE); start delay %s s after a blast at %s s; %d gate(s) on the tower\'s way out; jump list %d; [CrewJoin] places %d'
        % ('PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL', sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out),
           delay, blast, len(facts.get('gates', {})), len(lst), len(facts.get('crew_places', []))))
    return out, facts


# ------------------------------------------------------------------ build
def plan(B, opt=None, log=print):
    opt = dict(DEFAULTS, **(opt or {}))
    nav, S, P = tower_plan(B, opt, log)
    st = None
    if not opt['tower_only']:
        st = street_plan(B, nav, S, opt, log)
        P['rt']['street'] = st
    return P, st


def build(src, dst, opt=None, log=print):
    lines = []
    def say(s=''):
        lines.append(str(s)); log(s)
    opt = dict(DEFAULTS, **(opt or {}))
    B = F.Built(src)
    say('kl_fa_bots_rt build %s -> %s (%s)' % (src, dst, 'tower only' if opt['tower_only'] else 'tower + street'))
    P, st = plan(B, opt, say)
    room = {'fallback': blast_seconds(B) + float(opt['room_wait'])} if opt['room_gate'] else None
    if room:
        say('tower: the room first - the bots\' chain starts from %s through %s; fall-back Timer_start_bots at %.1f s after the round-start event (blast + %.0f s)' % (
            ROOM_COUNTER, GATE_NAME, room['fallback'], float(opt['room_wait'])))
    gates = P['rt']['gates']
    more = Street(st, room, gates) if (st or room or gates) else None
    rep = F.apply(B, P, dst, say, more=more)
    if st:
        write_ini(dst, st, say)
    out, facts = F.check(dst, say)
    out2, facts2 = check(dst, say)
    rep.update(plan=P, check=[list(x) for x in out], facts=facts, check_rt=[list(x) for x in out2], facts_rt=facts2)
    with open(os.path.join(dst, 'bots.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'bots.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out + out2, rep


def options(a):
    opt = {}
    if '--tower-only' in a:
        a.remove('--tower-only'); opt['tower_only'] = True
    if '--no-tree' in a:
        a.remove('--no-tree'); opt['tree'] = False
    if '--enter-after-blast' in a:
        a.remove('--enter-after-blast'); opt['room_gate'] = False
    if '--no-gates' in a:
        a.remove('--no-gates'); opt['gates'] = False
    for flag, key, conv in (('--loot-seconds', 'loot_seconds', int), ('--after-blast', 'after_blast', float), ('--street-hold', 'street_hold', float),
                            ('--room-wait', 'room_wait', float), ('--gates', 'gate_names', lambda s: [x for x in s.split(',') if x])):
        if flag in a:
            i = a.index(flag)
            opt[key] = conv(a[i + 1]); del a[i:i + 2]
    return opt


def main():
    a = sys.argv[1:]
    opt = options(a)
    if len(a) == 3 and a[0] == 'build':
        out, _rep = build(a[1], a[2], opt)
        sys.exit(1 if any(s == 'FAIL' for s, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'plan':
        P, st = plan(F.Built(a[1]), opt)
        for N, b in P['bots'].items():
            print('Squad#0%d: starts at %s; tower places %s' % (N, tuple(b['start']), b['places']))
            if st:
                print('          street places %s' % [s['places'][N - 2] for s in st['stations']])
        if st:
            print('[CrewJoin] places: %s' % st['arrive'])
            print('street steps: %s' % [(s['name'], s.get('stations', s.get('hold'))) for s in st['steps']])
    elif len(a) == 2 and a[0] == 'check':
        out, _f = F.check(a[1])
        out2, _f2 = check(a[1])
        sys.exit(1 if any(s == 'FAIL' for s, _t in out + out2) else 0)
    elif len(a) == 3 and a[0] == 'diff':
        sys.exit(1 if F.diff(a[1], a[2], also=(JOIN_NAME, ROOM_COUNTER)) else 0)     # (the room gate: the room counter names it)
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
