#!/usr/bin/env python3
"""
AI heisters on RETOMOTO TOWER: the squad of tools/kl_fa_bots.py on a map made of TWO navigation parts (the tower,
M09_A, and lobby + street, M09_B) that only the hook joins. Spec, the reading of kl2.exe it rests on, the hook part
(klhook/klcrew_rt.c), live checks: re/bots_retomoto.md. OFFLINE: nothing here installs anything or starts the game.

    python kl_fa_bots_rt.py build <build folder> <out folder> [options]   plan + write + every check; exit 1 on a FAIL
    python kl_fa_bots_rt.py plan  <build folder> [options]                the plan only (stations, places, notes)
    python kl_fa_bots_rt.py check <folder>                                kl_fa_bots.check + the checks of this module
    python kl_fa_bots_rt.py lanes <folder> <out.json>                     the street chain of a built folder as it is in its
                                                                          nodes: per squad and lane the places in order
                                                                          (for a picture, or to read place lines against)
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
      --no-lanes           the street chain as it was until 2026-10-11 noon (<work>\\build\\z_rooms\\retomoto_full; the
                           bots step is that build's byte for byte): all seven down the east pavement in one file,
                           sprinting from way place to way place. Default: THE STREET IN LANES (STREET_LANES below,
                           re/retomoto_bots_street.md) - a timed way inside the building in short bounds, its clock
                           laid for a slow walk (so a bot whose street step a late wait of the tower chain has taken
                           is ordered on again), then three lanes with holds at cover boxes: the east pavement, the
                           east carriageway and through the median to the far side, the far side from the square on;
                           three squads always take one lane each, four draw one of two per round (a RandomTrigger);
                           all meet at the rally. No sprint. No way within 2 m of a place the police are posted at.
                           The last legs are laid round the vehicles kl_fa_street parked there.
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
            lobby (EXITS_BANK on a ramp, stage 2) -> THE TIMED WAY through the lobby (short bounds by a clock that
            runs at V_SLOW, JOIN_SAFE seconds) -> THE DEAL (a RandomTrigger: one of the bot's lanes) -> THE LANE
            (over the square and up the road, holds at cover boxes with a timer each: this side of the road, or
            the far side; no leg within POST_WALL of a wall post of the police) -> a place before the
            level exit box (TriggerDelay2 --street-hold: the rally, where all lanes meet) -> into the box (stage 3;
            the van is called) -> round the parked bus to beside the van's stop, on the pavement side of its lane;
            boarding by ZBoardEscapeVehicleTactic (stock F07's form: these ARE F07's vans). (--no-lanes: lobby ->
            entrance -> forecourt -> east pavement -> rally -> box -> stop, one file.)
  What moves the ACTORS from the tower part to the street part is the hook (klhook/klcrew_rt.c, [CrewJoin] Enable=1):
  in the tick in which kljoin.c's jump request for that entry is pending - before the game moves the player and
  sends the 'AITrigger' - it calls the game's own actor teleport 0x62a900 (the routine 0x8f3fa0 itself uses on the
  story crew at 0x8f4128, and ZFFActor's own slot 18 on itself at 0x6ccdc1) for every AI crew record in play, with
  the places this module writes into the [CrewJoin] section of the build's KLJoin.ini. WITHOUT that hook part the street steps are
  started for bots that stand in the tower: what a DefendBehaviourRout does with a place on another navigation
  part is NOT established - use a --tower-only build then.

WHAT IS WRITTEN beyond kl_fa_bots.apply: the street steps (cloned F07 forms, as every other step; with the lanes
  also their timers - F07's Timer_start_bots form - and the deal's RandomTrigger, F07 Squad#02's), the room gate
  (a TriggerCounter cloned from F07, named by the room counter of kl_fa_author: the second edit of an existing node),
  the gates' TriggerActorsDead nodes (cloned from F07's bots; inside the squads, no existing node touched), ONE edit
  of an existing node for the join (field 0 of the JumpPoint controller of 06_Exit), the [CrewJoin] section appended
  to <out>/KLJoin.ini.

GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.
"""
import collections, heapq, json, math, os, re, struct, sys

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
            'room_gate': ROOM_GATE, 'room_wait': ROOM_WAIT, 'gates': TOWER_GATES, 'gate_names': None}     # (+ 'lanes', 'join_safe': below, at STREET_LANES)


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


HOP_MIN = 100.0         # a hop place lies at least this far (flat) from every hold of its gate (the holds are 110..200 apart: a mate's place is no hop;
                        # the hook itself sends a bot only to a hop 3 m or more from where it stands, klmove.c KLMV_OFF)
HOP_MAX = 1800.0        # ... and the hook only sends a bot to a hop within this of its hold (klmove.c RestlessHopMax): 18 m of walk
HOP_SEP = 150.0         # two hops of one gate are at least this far apart
HOP_GROW = 600.0        # the gate's box is grown by this on every side for the hop places (the rules that keep a place out of a later fight's box,
                        # out of the ring of a cover with a side in one, and POST_KEEP from the men still alive, stay)
HOP_TESTS = 150         # most candidate places tried a gate (each costs a stand-in path per hold within HOP_MAX)


def pick_hops(B, nav, spots, holds, boxes, no_way, mine, woken, walks_past, n, tally):
    """COVER TO COVER. Up to n more places of a gate, from the same list hold_spots() made (HOLD_RING from a cover box, inside the
    gate's box, flat, HOLD_CLEAR from a wall, in no box of a later fight, POST_KEEP from a post of a man who may be alive), that
    lie HOP_MIN or more from every hold and from each other, on the holds' floor - and whose way from EVERY hold within HOP_MAX
    of them (the hook sends a bot from the hold it stands at to a hop within that) goes through no box of a later fight (no_way)
    and does not walk past a post of this gate's men (the rule the holds are laid by). -> [(x, y, z, polygon, cover node, behind,
    clearance, distance from the box)], best first. The hook (klmove.c) chooses among them at run time; nothing in the level's
    nodes names them, so they cannot make a chain wait or fork: they are a list in KLJoin.ini ([Hops])."""
    quality = lambda s: (not s[5], s[6] < F.CLEAR, abs(s[7] - HOLD_BEST), -s[6])
    got, tests = [], 0
    for s in sorted(spots, key=quality):
        if len(got) >= n or tests >= HOP_TESTS:
            break
        if any(hdist(s, h) < HOP_MIN or abs(s[1] - h[1]) > FLOOR_DY for h in holds) or any(hdist(s, o) < HOP_SEP for o in got):
            continue
        tests += 1
        ok = True
        for h in holds:
            if hdist(s, h) > HOP_MAX:
                continue
            on = boxes_on(B, nav, list(boxes), h, s)
            if on is None or any(k in no_way for k in on) or walks_past(h, s, mine, woken) is not None:
                ok = False
                break
        if ok:
            got.append(s)
        else:
            tally['hop refused: a way from a hold'] += 1
    return got


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
        # COVER TO COVER (option 'hops', 2026-10-12, re/bots_active.md): more places of this gate a bot may shift to while it waits
        hops = []
        if opt.get('hops'):
            x0_, x1_, z0_, z1_ = g['box']
            wide = hold_spots(B, nav, home, covers, dict(g, box=(x0_ - HOP_GROW, x1_ + HOP_GROW, z0_ - HOP_GROW, z1_ + HOP_GROW)), no_way, keep_ring, posts, live,
                              collections.Counter())      # (the gate's own box is too small a room for a second set of covers: the holds took the best places)
            hops = pick_hops(B, nav, wide, holds, boxes, no_way, mine, woken, walks_past, int(opt.get('hops') or 0), refused)
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
            hops=[[round(v, 1) for v in h[:3]] for h in hops], hop_covers=[name(h[4]) for h in hops],
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


# ------------------------------------------------------------------ the street in lanes (2026-10-11, re/retomoto_bots_street.md)
# THE OWNER, after the gates build: 'when doing the run to the car they need to spread out more like some try going to
# the other side some stay on that side etc. they need to use the map a bit more'. What the seven did until now
# (runs J0 / J1 / B1_DM09, place lines every 5 s): one file - both lobby stairs, the middle of the front door, the
# north bays of the square, the east pavement (x -850..-1000) - and the five of J0 dead at the kerb of that pavement,
# z -4200..-150, 40..49 s after the join.
# NOW: behind the lobby's EXITS_BANK box every bot's street chain is
#   A. THE TIMED WAY (the first JOIN_SAFE seconds): through the lobby towards the door in short bounds, at cover
#      boxes where there are any, each bot its own ramp of the lobby and line towards its bay of the square. The form is
#      the plain one - a step to the next place, a timer, the next step (stock F07's rout -> timer) - but every place
#      lies within CALL_REACH of the place before. A step is 'reached' and sends its list within ARRIVE_3D of its place
#      (kl2 0x686c4c), so a step of this way is reached THE MOMENT IT STARTS: its timer runs while the bot walks the
#      bound, and for a bot on its way a timer is pending all the time - the chain runs by the clock. THE CLOCK RUNS
#      AT V_SLOW (a place's timer = its way at V_SLOW): a bot that walks V_SLOW or faster is at the place when its
#      timer fires - he stands the rest - and falls behind at no speed above it. (The first build's clock ran at
#      160..220 units / s: tight from 250 on, 3..10 s of the 31 without a pending timer at 150 - review S2.) The
#      timed way ends when its clock has run JOIN_SAFE, 31..41 m from the ramp, inside the building or at the door;
#      the rest of the bay's line is the first stretch of the bot's lane.
#      WHY: runs J1 / B1 showed what the gates' note 'THE JOIN' feared. A bot that stood at a gate with its wait armed
#      when the human took the tower car lost its street step up to 30 s later (the wait fired, the next TOWER step
#      started and took its place) and stood in the square for the rest of the run - B1: records 2 and 5, exactly at
#      their door holds at the join; J1: six of seven. A chain that only goes on when the bot ARRIVES is dead then.
#      Here the pending timer starts the next step all the same: for that bot it names a real place, he walks to it,
#      it is reached, and he is on the clock again. (One wait a bot can be armed, and none can be armed after the join.)
#   B. THE DEAL: a RandomTrigger (stock F07 Squad#02's form, as kl_fa_bots_dyn's forks) draws one of the bot's two
#      lanes, per bot and per round. DEAL gives three bots one lane each (no draw): no lane is ever empty.
#   C. THE LANE: holds at cover boxes a bound apart - a step to the hold, a timer, the next (the form of the tower's
#      gates, with a timer for the wait) - to the lane's last place before the rally. A hold's timer = the stand
#      wanted + the walk in at V_SLOW (hold_timer); the cover box a hold is nearest to is given to one bot (box_room);
#      NO WAY WITHIN POST_WALL OF A WALL POST of the police (wall_posts: the ground there is no ground for a way).
#   D. all lanes meet at the rally (the old chain's own: STREET_HOLD seconds outside the level exit box), then the
#      level exit box and the places beside the van's stop, laid round the vehicles kl_fa_street parked there.
# GUESS: every number below and every lane's line.
STREET_LANES = True     # False ('--no-lanes'): the street chain of 2026-10-11 noon (z_rooms\retomoto_full), node for node
JOIN_SAFE = 31.0        # s after the jump within which a wait of the tower chain can still fire: WAIT_S (and the loot wait's 30) + 1
V_PLAN = 300.0          # units / s a free bot walks, for the PACE the plan and the check say (measured between two place lines
                        # after the join, runs J0 / J1 / B1: 240..440 - but those steps were eDMS_Sprint)
V_SLOW = 150.0          # THE SLOWEST WALK THE CHAIN IS LAID FOR. The lanes' steps are eDMS_NotSet; such steps of the gates build
                        # in the tower, fights and stairs included, moved at a median 124..127 units / s over 5 s, 90 % under
                        # 259, top 368 (the review's speed.py on runs J1 / B1). The clock of the timed way runs at THIS speed
                        # (a bot that walks it or faster is at each place before its timer fires, so a timer is pending all
                        # the time) and a hold's timer counts the walk in at this speed. What the pace on the square under
                        # fire is, is NOT KNOWN: a bot slower than this falls behind the clock (check(): the walk model)
CLOCK_PAUSE = 1.2       # GUESS: seconds at each cover of the timed way, on top of the walk to it
CLOCK_START = 0.5       # GUESS: seconds at the EXITS_BANK place before the first bound (+ the bot's STAGGER)
CLOCK_MIN = 350.0       # the next place of the timed way lies at least this far along the way
CLOCK_REACH = 420.0     # ... its box within this of the way's line
CLOCK_END = 700.0       # the timed way ends within this of way of its bay's end place
GRID = 40.0             # the cell of the grid the ways are laid on (Walk)
FOOT_KEEP = 70.0        # a way and a place keep this far from the footprint of a vehicle kl_fa_street brought to the road
                        # (kl_fa_street.footprints(): the navigation mesh has no hole under them)
BOUND_BEST = 2400.0     # a lane's bound: the next hold lies about this far along the lane's line from the last - or the lane's
LANE_HOLDS = 5          # length over LANE_HOLDS + 1 where that is more. Stock F07's bots: a 'pos' step every ~25 m. (6 until the
                        # hold timers grew by the walk in at V_SLOW: a lane now begins at the timed way's end INSIDE the
                        # building, 20..40 m longer, and seven holds of 8..10 s put the far lanes at the rally after 2.5 min)
BOUND = (0.7, 1.4)      # ... between these shares of the bound (never under ARRIVE_3D + 100 in 3D: a step to a nearer hold would
                        # be 'reached' where the bot stands)
BOUND_FAR = 2.2         # where no free cover lies in that window: up to this share; beyond it the bot walks on without a hold
LANE_REACH = 520.0      # a lane's cover box lies within this of the lane's line
SPOT = (35.0, 170.0)    # a lane's hold place lies this far outside the edge of its cover box's own box (the model's box, which is
                        # what kl2 0x603830 makes the cover of; on the street the boxes are 0.5..6 m long and their origin is not
                        # always their middle), and within HOLD_COVER - 30 of the box's middle
SHARE_LEN = (200.0, 400.0)  # a cover box this long (its box's longer side) may be two / three bots' box, HOLD_SEP apart
COVER_OFF = 150.0       # (said in the plan: a box whose origin lies further than this from its box's middle - a bus's end.
                        # kl_fa_bots_dyn.check measures 'a hold within 500 of a cover box' from the ORIGIN; the lanes' holds are
                        # steps of the route form, which that rule does not look at, and check() here measures from the box)
POST_PASS = 300.0       # a way is laid this far round a post of the police where the ground has room (Walk.DANGER: a cost)
POST_WALL = 200.0       # ... and NEVER nearer than this to a WALL POST (wall_posts(): every post - a RunToCover point, a place
                        # a behaviour of a squad names, a start place): the ground within it is no ground for a way (Walk
                        # `walls`), and check() FAILs a leg that comes nearer. A soldier whose target
                        # is within 160 fires 100 bullets a burst step (kl2 0x8c62e0, re/melee_damage.md: 432 against a bot's
                        # 252 at the owner's CopToCrew 0.05) - the first build's ways passed 13..75 from such points
                        # (re/retomoto_bots_street_review.md M1). 160 + the 40 of a grid cell
POST_KEEP_ST = 400.0    # no hold of the street nearer than this to a post of the police: where a man stands at the load, a
                        # place a rout of his squad names, a RunToCover point (the campaign and F07 post their men at the same cars)
LINE_SLACK = (1.5, 500.0)   # a way between two holds is at most this much longer than the straight line (factor, plus)
END_GAP = 900.0         # no hold in the last stretch of a lane before its end place
LANE_STAND = {'E': 2.0, 'X': 1.5, 'W': 1.5}     # GUESS: seconds a bot is to STAND at a hold, by lane (longest on the short lane),
HOLD_OFF = {2: -0.5, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.5, 7: 0.5, 8: -0.5}      # + this by squad. A hold's TIMER starts when the step is
STAND_MIN = 1.0         # 'reached', ARRIVE_3D before the hold, so timer = the stand + THE WALK IN AT V_SLOW - by the walk model
                        # from where the step is reached, through the step's way places, to the hold: 6.7 s on a straight
                        # line, more round a corner (lanes_plan sets it per hold). A bot at V_SLOW stands the stand, one at
                        # V_PLAN about 3.3 s longer. check(): no hold's timer under ARRIVE_3D / V_SLOW + STAND_MIN, and by
                        # the walk model at V_SLOW a stand of STAND_MIN at every hold. (The first build's timers of 5..9 s
                        # were a stand of 1.7..5.7 s at V_PLAN and none at V_SLOW: review S1)
hold_stand = lambda key, N: max(STAND_MIN, LANE_STAND.get(key, 2.0) + HOLD_OFF.get(N, 0.0))
hold_timer = lambda key, N: round(hold_stand(key, N) + ARRIVE_3D / V_SLOW, 1)
STREET_SEP = HOLD_SEP   # two bots' places of the street - a hold of a lane, a place of the timed way - are at least this far apart
STAGGER = {2: 0.0, 3: 3.0, 4: 1.0, 5: 4.0, 6: 2.0, 7: 5.0, 8: 1.5}      # seconds a bot waits longer at its first cover in the lobby
PHASE = {2: 0.75, 3: 1.0, 4: 0.85, 5: 1.2, 6: 1.3, 7: 0.9, 8: 1.1}      # the first bound of a lane x this: not all at the same cars
WEIGHTS = (3, 3)        # the RandomTrigger's weights (stock: 3 / 3 on 147 of the bots' RandomTriggers)
# THE LANES. key; what; via = the line from the square to the lane's last place, as points (x, z) the way is laid
# through (GUESS, read off the top views <work>\build\z_lanes\maps); end = its last place, short of the rally.
#   E  stays on this side: the east pavement, the old line
#   X  the east carriageway among the taxis, then through the gap of the median at z 0 (the carriageway is shut at
#      z 2000 by the bus kl_fa_street laid across it) and up the inner side of the west carriageway; back east just
#      north of the median's end (z 4900: between two of the bollards that stand 1.2 m apart from there to z 8840)
#   W  the other side at once: west across the open road in front of the square, up the west carriageway's parked row,
#      back east at z 6700 (another gap of the bollards), south of the bus beside the median and of the van's waiting place
#   The police's road block (z 3450..3960) shuts the west carriageway from the median to 2 m short of the kerb: X goes
#   round its west end along the kerb, W over the west pavement.
#   A LINE CHOOSES THE HOLDS, NOT THE WAY: the way from hold to hold is the cheapest on the grid (Walk.leg). As built
#   the X ways cross the median at its slit at z 1440 (#02, #03, #08) or south of its end at z -1730 (#06) and come
#   back east through bollard gaps at z 5280..5320 or 6480; W crosses the open road at z -5390..-4350 and comes back
#   at z 6480 / 6920. No way of the build uses the gap at z 0 (MEASURED: scratch K2\cross2.py on the build's nodes).
LANES = (
    {'key': 'E', 'what': 'this side: the east pavement',
     'via': ((-760.0, -4080.0), (-900.0, -2600.0), (-880.0, -900.0), (-880.0, 900.0), (-930.0, 2700.0), (-980.0, 4500.0), (-900.0, 6200.0)),
     'end': (-1000.0, 7350.0)},
    {'key': 'X', 'what': 'the middle: the east carriageway, through the median\'s gap at z 0, the west carriageway\'s inner side',
     'via': ((-1250.0, -4040.0), (-2330.0, -3300.0), (-2380.0, -1900.0), (-2420.0, -600.0), (-3050.0, -15.0), (-3480.0, 500.0), (-3520.0, 2000.0),
             (-4250.0, 2950.0), (-4800.0, 3700.0), (-3700.0, 4550.0), (-3000.0, 4900.0), (-2350.0, 5500.0), (-1650.0, 6850.0)),
     'end': (-1280.0, 7300.0)},
    {'key': 'W', 'what': 'the other side: across the road in front of the square, the west carriageway\'s parked row',
     'via': ((-1650.0, -5560.0), (-2750.0, -5950.0), (-3980.0, -5250.0), (-3950.0, -2800.0), (-3980.0, -1300.0), (-3930.0, 0.0), (-3980.0, 1900.0),
             (-4950.0, 2850.0), (-5080.0, 3800.0), (-4350.0, 4950.0), (-3800.0, 6250.0), (-3000.0, 6700.0), (-2100.0, 7050.0)),
     'end': (-1500.0, 7300.0)},
)
# THE DEAL. Squad -> its lanes: one = it always takes it (#05 E, #02 X, #04 W: no lane is empty WHILE THOSE THREE
# LIVE), two = a RandomTrigger draws per round (the first is the way branch set 0 of the checks walks). E has 1..3 of
# the seven, X 1..4, W 1..4; 16 deals. #08 draws X or W, not E: the east pavement has ten cover boxes and none between
# z -100 and 5400, and the squad that chooses last got ONE hold in 135 m on it - alone and first in every wake box,
# as run J1's record 5 (dead at +37.7 s; review S3). With the squad that always takes a lane dead before the join
# that lane is empty in 2 of 16 deals for X (#03 E, #06 W, #08 W) and for W (#06 X, #07 E, #08 X), in 4 of 16 for E
# (#03 X, #07 W) - a deal by who is alive cannot be made in level data (review S6).
DEAL = {2: ('X',), 3: ('E', 'X'), 4: ('W',), 5: ('E',), 6: ('X', 'W'), 7: ('W', 'E'), 8: ('X', 'W')}
# THE SQUARE. The points (x, z) each bot's timed way is laid through behind the door, the last = where it ends and the
# lanes start: the west end of a way down from the terrace between the square's four planters (x 550..1600).
#   n = down the steps at the terrace's north-east corner and along the north side of the first planter
#   a = the bay between the first planter and the second
# (The bays further south are ramps whose polygons are no planes - fitted heights off by 1..2 m, WARP - and they open
# on the police cars of Squad_InFront: not used.)
BAYS = {'n': ((2270.0, -4740.0), (1750.0, -4330.0), (1150.0, -4720.0), (520.0, -4760.0)), 'a': ((430.0, -5600.0),)}
BAY = {2: 'a', 3: 'n', 4: 'a', 5: 'n', 6: 'a', 7: 'a', 8: 'n'}
WARP_WAY = 30.0         # a place of the timed way WITHOUT a cover box may stand on a polygon this uneven (the terrace in front of
                        # the door is one polygon of 8 x 13 m whose corners lie 24 off the fitted plane; nobody stands at such
                        # a place, the bot walks through it)
RAMP = {2: 's', 3: 'n', 4: 's', 5: 'n', 6: 's', 7: 's', 8: 'n'}     # the lobby's ramp a bot takes down from the lift landing (north / south)
CALL_REACH = 600.0      # a place of the timed way lies within this (3D) of the place before - so the step that names it is
                        # 'reached' (ARRIVE_3D) the moment it starts, also for a bot that is up to 4 m short of the place
                        # before (780 until the review's S2: tight only from 250 units / s on)
LANE_MIN_HOLDS = 3      # check(): every way of the deal has this many holds at cover (the first build's #08 on E had one: review S3)
LANE_PRE = {'E': '061', 'X': '062', 'W': '063'}
LANE_TAG = '_DefendBehaviour_lane_'     # a lane's step: <pre>_DefendBehaviour_lane_<key>_<nn> (a hold: a timer <pre>_Timer_lane_.. follows)
TIMED_TAG = '_DefendBehaviour_out_'     # a step of the timed way (the tower's own way out is ..._DefendBehaviour_out_<gate> in chain 1)
CLOCK_MARGIN = 150.0    # check(): a place of the timed way lies within ARRIVE_3D less this of the place before
ROAD_MID = -3000.0      # the road's middle: the median (x -3145..-2854 from z -1410 to 4666)
DEFAULTS.update(lanes=STREET_LANES, join_safe=JOIN_SAFE)


def cover_geom(B):
    """The cover boxes as BOXES -> [dict]: node, at (the origin), mid (the middle of the model's box in the world), fp
    (x0, x1, z0, z1 of that box in the plan), y (its floor), off (origin to middle in the plan), high. kl2 0x603830 builds
    a cover from the entity's box (middle +0x30, half size +0x40: re/bots_dyn_build.md 13); the model's 64-byte root
    holds the same box at +0x20 (kl_fa_cover.all_boxes). A box without such a root: its origin, 50 round it."""
    sc, prm, out = B.sc, B['.prm'], []
    t, n = struct.unpack_from('<II', prm, 0)
    for k, at in cover_boxes(B):
        e, bb = B.ents[k - 1], None
        if 0 < e.model < n:
            o, size = struct.unpack_from('<II', prm, t + 16 * e.model)
            if size == 64 and prm[o:o + 4] == b'\0\1\7\0':
                bb = struct.unpack_from('<6f', prm, o + 0x20)
        if bb:
            cs = [B.world(k, (x, y, z)) for x in (bb[0], bb[3]) for y in (bb[1], bb[4]) for z in (bb[2], bb[5])]
            fp = (min(c[0] for c in cs), max(c[0] for c in cs), min(c[2] for c in cs), max(c[2] for c in cs))
            y0 = min(c[1] for c in cs)
        else:
            fp, y0 = (at[0] - 50.0, at[0] + 50.0, at[2] - 50.0, at[2] + 50.0), at[1]
        mid = ((fp[0] + fp[1]) / 2, y0, (fp[2] + fp[3]) / 2)
        out.append({'node': k, 'at': at, 'mid': mid, 'fp': fp, 'y': y0, 'off': hdist(at, mid), 'high': 'coverboxh' in sc.names[k].lower()})
    return out


def box_room(c):
    """How many bots a cover box (cover_geom) takes: one - a box SHARE_LEN[0] long two, one SHARE_LEN[1] long three,
    HOLD_SEP apart (a car's middle box is 2 m, the square's low walls 6 m: run J1 had five of the seven in a row
    behind one such wall, a metre apart, of the game's own choosing)."""
    return 1 + sum(1 for n in SHARE_LEN if max(c['fp'][1] - c['fp'][0], c['fp'][3] - c['fp'][2]) >= n)


def fp_dist(fp, x, z):
    """Distance in the plan from (x, z) to the rectangle fp = (x0, x1, z0, z1); 0 inside it."""
    return math.hypot(max(fp[0] - x, 0.0, x - fp[1]), max(fp[2] - z, 0.0, z - fp[3]))


def street_posts(B, squads=None):
    """[(squad node, what, place)] - every post of the police below the tower: enemy_posts() and the RunToCover points
    (a child with a RunToCoverPosInfoRout controller: where F07's squads are sent first)."""
    sc = B.sc
    squads = squads if squads is not None else enemy_squads(B)
    out = [(t, what, q) for t, ps in enemy_posts(B, squads).items() for what, q, _r in ps if q[1] < 5000.0]
    of = {k: t for t in squads for k in range(t, sc.end[t])}
    for k, _i, _v in kl_fa.controllers(sc, 'RunToCoverPosInfoRout'):
        if k in of and B.at(k)[1] < 5000.0:
            out.append((of[k], 'RunToCover ' + sc.names[k], B.at(k)))
    return out


def wall_posts(posts):
    """THE WALL POSTS of street_posts()' list -> [(squad node, what, place)]: the posts no way may pass within
    POST_WALL of. ALL OF THEM: every RunToCover point, every place a behaviour of a squad names (where its men are
    sent) and every start place (where a man stands at the load - a road block's man is sent 1.3 m and stays; a
    squad that is sent 50 m away has LEFT its start place when a lane comes by, every wave being woken by the first
    bot on the road, but nothing here rests on that: the street has room for the ways without those places too)."""
    return list(posts)


def post_gap(walls, a, b, step=20.0):
    """The nearest a straight leg a -> b comes to a wall post on its floor -> (distance, post) or (1e9, None)."""
    best = (1e9, None)
    n = max(1, int(math.dist(a[:3], b[:3]) // step))
    for t in range(n + 1):
        m = [a[i] + (b[i] - a[i]) * t / n for i in range(3)]
        for w in walls:
            q = w[2]
            if abs(q[1] - m[1]) <= 260.0:
                d = math.hypot(m[0] - q[0], m[2] - q[2])
                if d < best[0]:
                    best = (d, w)
    return best


def walk_model(steps, v, start=None):
    """THE WALK MODEL (this module's and the review's reading of kl2 0x686c4c; nothing of it was seen in the game):
    steps = [(name, [place ..], seconds of the timer behind it or None)] in the order they run. The bot walks at v
    units / s in straight lines through a step's places; a step is 'reached' when he is within ARRIVE_3D (3D) of
    its LAST place; a timer starts then, and the next step starts when it fires (at once without a timer), from
    where the bot is. -> rows {name, start, reached, arrive (bodily at the last place, were he left to walk),
    next, timer, stood (seconds at the last place before the next step starts), no_timer (seconds between the
    step's start and its 'reached': nothing is pending for the bot then)}."""
    t, pos, rows = 0.0, start, []
    for name, pts, timer in steps:
        if not pts:
            continue
        if pos is None:
            pos = tuple(pts[0])
        last, path = tuple(pts[-1]), [tuple(pos)] + [tuple(p) for p in pts]
        reached, tt, cur = (t if math.dist(pos, last) <= ARRIVE_3D else None), t, tuple(pos)
        for q in path[1:]:
            seg = math.dist(cur, q)
            if reached is None:
                n = max(1, int(seg / 10))
                for j in range(1, n + 1):
                    p = tuple(cur[x] + (q[x] - cur[x]) * j / n for x in range(3))
                    if math.dist(p, last) <= ARRIVE_3D:
                        reached = tt + seg * j / n / v
                        break
            tt += seg / v
            cur = q
        if reached is None:
            reached = tt
        fire = reached + (timer or 0.0)
        if fire >= tt:
            nxt, stood = last, fire - tt
        else:                                           # still walking when the next step starts
            rem, cur = (fire - t) * v, tuple(pos)
            for q in path[1:]:
                seg = math.dist(cur, q)
                if rem <= seg:
                    cur = tuple(cur[x] + (q[x] - cur[x]) * rem / max(seg, 1e-6) for x in range(3))
                    break
                rem, cur = rem - seg, q
            nxt, stood = cur, 0.0
        rows.append({'name': name, 'start': t, 'reached': reached, 'arrive': tt, 'next': fire, 'timer': timer, 'stood': stood, 'no_timer': reached - t})
        t, pos = fire, nxt
    return rows


class Ground:
    """nav.at() and nav.clearance() for many calls: the polygons of one mesh part and the mesh's open edges in buckets."""
    CELL = 400.0

    def __init__(self, nav, part):
        self.nav, self.part = nav, part
        self.b, self.w = collections.defaultdict(list), collections.defaultdict(list)
        c = self.CELL
        for i, bx in enumerate(nav.box):
            if nav.ok[i] and nav.part[i] == part:
                for gx in range(int(bx[0] // c), int(bx[1] // c) + 1):
                    for gz in range(int(bx[2] // c), int(bx[3] // c) + 1):
                        self.b[(gx, gz)].append(i)
        for wl in nav.walls:
            for gx in range(int(min(wl[0], wl[2]) // c), int(max(wl[0], wl[2]) // c) + 1):
                for gz in range(int(min(wl[1], wl[3]) // c), int(max(wl[1], wl[3]) // c) + 1):
                    self.w[(gx, gz)].append(wl)

    def under(self, x, z):
        """[(polygon, its height there)] of the part's polygons under (x, z)."""
        nav = self.nav
        return [(i, nav.height(i, x, z)) for i in self.b.get((int(x // self.CELL), int(z // self.CELL)), ())
                if nav.box[i][0] <= x <= nav.box[i][1] and nav.box[i][2] <= z <= nav.box[i][3] and nav.inside(i, x, z)]

    def at(self, x, y, z, dy=F.DY):
        best = None
        for i, h in self.under(x, z):
            if abs(h - y) <= dy and (best is None or abs(h - y) < abs(best[1] - y)):
                best = (i, h)
        return best

    def clearance(self, x, y, z, limit=400.0):
        """As kl_fa_bots.Nav.clearance (walls of every part, within 150 of height y), up to `limit`."""
        best, c = limit, self.CELL
        for gx in range(int((x - limit) // c), int((x + limit) // c) + 1):
            for gz in range(int((z - limit) // c), int((z + limit) // c) + 1):
                for x0, z0, x1, z1, wy in self.w.get((gx, gz), ()):
                    if abs(wy - y) > 150.0:
                        continue
                    dx, dz = x1 - x0, z1 - z0
                    L = dx * dx + dz * dz
                    t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((x - x0) * dx + (z - z0) * dz) / L))
                    best = min(best, math.hypot(x - x0 - t * dx, z - z0 - t * dz))
        return best


class Walk:
    """THE GROUND A WAY MAY BE LAID ON: the street's mesh part as a grid of GRID, inside `region` (x0, x1, z0, z1).
    A cell is FREE when a polygon of the part lies under it that is `usable` and it is FOOT_KEEP clear of every
    rectangle of `blocks` (the vehicles kl_fa_street parked on the road: the mesh has no hole under them, so the
    game's pathfinder - and this module's stand-in path - walks through them; the van's lane; for the lanes the level
    exit box) and POST_WALL from every place of `walls` on its floor (the wall posts of the police). OPEN: free, and so are its neighbours to both sides along x or along z (a gap two cells wide can be
    walked: the bollards north of the median stand 120 apart); WIDE: all four are. A way costs NARROW times its
    length over cells that are not wide, so it keeps a cell from the mesh's edge where it can, and DANGER times near
    a place of `danger`.
    leg(a, b) = the cheapest way over open cells, pulled straight: [a, .., b] with every piece a straight line over
    open cells. All of it is this module's own reading of 'a way a bot can take'; what a build's legs really are is
    tested again on the mesh itself (straight_clear, check())."""
    NARROW = 3.0
    NARROW_MIN = 33.0       # an open cell that is not wide lies at least this far from the mesh's edge: a gap of 111 (the
                            # bollards north of the median: holes of 89 every 200) is walked. MEANT to shut the slit in the
                            # median at z 1387..1473 - IT DOES NOT: the row of cells at z 1440 lies 33 from both edges and is
                            # open, and three of the four X ways of the build (and record 1's of the first build) cross
                            # the median THERE, not at the gap at z 0 the lane's line is drawn through: a way between two
                            # holds is the cheapest on the grid, the line only chooses the holds. Left so: the mesh is
                            # drawn in from what stands on it, so by the mesh both are walked, and the ways back east go
                            # through bollard gaps of the same kind. (re/retomoto_bots_street.md 3.3; a bot standing at
                            # (-2960, 1440) in a live run = the game does not walk it: raise this to 36)
    DANGER = 4.0            # a way costs this many times its length within POST_PASS of a place of `danger` (a post of the
                            # police): it goes round where the ground lets it (inside 1.6 m a bullet counts x 100: kl2 0x8c62e0)

    def __init__(self, G, blocks=(), usable=None, step=GRID, region=None, danger=(), walls=()):
        self.G, self.step, self.blocks = G, step, [tuple(b) for b in blocks]
        self.cells, nav = {}, G.nav
        wb = collections.defaultdict(list)              # the wall posts (places x, y, z) in buckets of 400
        wr = POST_WALL + 0.75 * step                    # (a line over free cells runs up to 0.71 of a cell from their middles)
        for q in walls:
            for gx in range(int((q[0] - wr) // 400), int((q[0] + wr) // 400) + 1):
                for gz in range(int((q[2] - wr) // 400), int((q[2] + wr) // 400) + 1):
                    wb[(gx, gz)].append(q)
        walled = lambda x, h, z: any(abs(q[1] - h) <= 260.0 and math.hypot(x - q[0], z - q[2]) < wr for q in wb.get((int(x // 400), int(z // 400)), ()))
        for i, bx in enumerate(nav.box):
            if not (nav.ok[i] and nav.part[i] == G.part) or (usable is not None and not usable(i)):
                continue
            if region is not None and (bx[1] < region[0] or bx[0] > region[1] or bx[3] < region[2] or bx[2] > region[3]):
                continue
            for ix in range(int(math.ceil(bx[0] / step)), int(math.floor(bx[1] / step)) + 1):
                for iz in range(int(math.ceil(bx[2] / step)), int(math.floor(bx[3] / step)) + 1):
                    x, z = ix * step, iz * step
                    if region is not None and not (region[0] <= x <= region[1] and region[2] <= z <= region[3]):
                        continue
                    if nav.inside(i, x, z) and not self.blocked(x, z):
                        h = nav.height(i, x, z)
                        if walled(x, h, z):
                            continue
                        cur = self.cells.get((ix, iz))
                        if cur is None or h < cur[0]:          # (two floors over one another: the lower one)
                            self.cells[(ix, iz)] = (h, i)
        near = lambda c, dx, dz: abs(self.cells.get((c[0] + dx, c[1] + dz), (1e9,))[0] - self.cells[c][0]) <= 50.0
        self.wide = {c for c in self.cells if near(c, 1, 0) and near(c, -1, 0) and near(c, 0, 1) and near(c, 0, -1)}
        self.open = set(self.wide)
        for c in self.cells:
            if c not in self.wide and ((near(c, 1, 0) and near(c, -1, 0)) or (near(c, 0, 1) and near(c, 0, -1))) \
                    and G.clearance(c[0] * step, self.cells[c][0], c[1] * step, 80.0) >= self.NARROW_MIN:
                self.open.add(c)
        self.cost = {}
        r = int(POST_PASS // step) + 1
        for d in danger:
            c0 = (int(round(d[0] / step)), int(round(d[2] / step)))
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    c = (c0[0] + dx, c0[1] + dz)
                    if c in self.cells and abs(self.cells[c][0] - d[1]) <= 260.0 and math.hypot(c[0] * step - d[0], c[1] * step - d[2]) <= POST_PASS:
                        self.cost[c] = self.DANGER
        self.comp, n = {}, 0                            # the open cells' connected parts (a planter's inside is one of its own)
        for c0 in self.open:
            if c0 in self.comp:
                continue
            self.comp[c0], todo = n, [c0]
            while todo:
                c = todo.pop()
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (c[0] + dx, c[1] + dz)
                    if q in self.open and q not in self.comp and abs(self.cells[q][0] - self.cells[c][0]) <= 50.0:
                        self.comp[q] = n; todo.append(q)
            n += 1

    def blocked(self, x, z, keep=FOOT_KEEP):
        return any(b[0] - keep <= x <= b[1] + keep and b[2] - keep <= z <= b[3] + keep for b in self.blocks)

    def cell(self, p):
        return (int(round(p[0] / self.step)), int(round(p[2] / self.step)))

    def snap(self, p, reach=6):
        """The open cell nearest to place p (within reach cells, at about its height), or None."""
        c0, best = self.cell(p), None
        for dx in range(-reach, reach + 1):
            for dz in range(-reach, reach + 1):
                c = (c0[0] + dx, c0[1] + dz)
                if c in self.open and abs(self.cells[c][0] - p[1]) <= 150.0:
                    d = math.hypot(c[0] * self.step - p[0], c[1] * self.step - p[2])
                    if best is None or d < best[0]:
                        best = (d, c)
        return best and best[1]

    def point(self, c):
        return (c[0] * self.step, self.cells[c][0], c[1] * self.step)

    def clear(self, a, b):
        """Is the straight line a -> b over free cells (a sample every 20, each within 120 of the line's height) - and,
        but for its first and last 80, over WIDE ones? (So a line of any length keeps a cell from the mesh's edge, and
        a narrow gap is walked in pieces of at most 160.)"""
        d = math.dist(a[:3], b[:3])
        n = max(1, int(d // 20))
        for t in range(n + 1):
            m = [a[i] + (b[i] - a[i]) * t / n for i in range(3)]
            c = self.cell(m)
            got = self.cells.get(c)
            if got is None or abs(got[0] - m[1]) > 120.0 or self.blocked(m[0], m[2]):
                return False
            if c not in self.wide and min(d * t / n, d * (n - t) / n) > 80.0:
                return False
        return True

    def cells_path(self, c0, c1, limit=60000):
        """A* over the open cells from c0 to c1 -> [cell] or None."""
        if c0 == c1:
            return [c0]
        s = self.step
        hfun = lambda c: math.hypot(c[0] - c1[0], c[1] - c1[1]) * s
        dist, prev, pq, done = {c0: 0.0}, {}, [(hfun(c0), 0.0, c0)], 0
        while pq:
            _f, d, c = heapq.heappop(pq)
            if c == c1:
                out = [c]
                while c in prev:
                    c = prev[c]; out.append(c)
                return out[::-1]
            if d > dist.get(c, 1e30):
                continue
            done += 1
            if done > limit:
                return None
            h0 = self.cells[c][0]
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                q = (c[0] + dx, c[1] + dz)
                if q not in self.open or abs(self.cells[q][0] - h0) > 50.0:
                    continue
                if dx and dz and ((c[0] + dx, c[1]) not in self.open or (c[0], c[1] + dz) not in self.open):
                    continue
                nd = d + s * (1.41421356 if dx and dz else 1.0) * (1.0 if q in self.wide else self.NARROW) * self.cost.get(q, 1.0)
                if nd < dist.get(q, 1e30):
                    dist[q], prev[q] = nd, c
                    heapq.heappush(pq, (nd + hfun(q), nd, q))
        return None

    def leg(self, a, b):
        """A way a -> b (places x, y, z): ([a, turning points .., b], its length) or None."""
        if self.clear(a, b):
            return [tuple(a[:3]), tuple(b[:3])], math.dist(a[:3], b[:3])
        c0, c1 = self.snap(a), self.snap(b)
        if c0 is None or c1 is None or self.comp[c0] != self.comp[c1]:
            return None
        cs = self.cells_path(c0, c1)
        if cs is None:
            return None
        pts = [tuple(a[:3])] + [self.point(c) for c in cs] + [tuple(b[:3])]
        out, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self.clear(pts[i], pts[j]):
                j -= 1
            out.append(pts[j]); i = j
        return out, sum(math.dist(p, q) for p, q in zip(out, out[1:]))


def straight_clear(G, blocks, a, b, keep=FOOT_KEEP - 10.0, dy=120.0, walls=(), wall=POST_WALL):
    """THE TEST A BUILD'S LEG IS HELD TO (the plan and check()): the straight line a -> b stays on the mesh of the
    street's part (a sample every 20, each within dy of the line's height), out of the van's lane, `keep` clear of
    the vehicles parked on the road and `wall` from every wall post of `walls` [(squad, what, place)]. A straight
    line that is all mesh is the way any pathfinder takes."""
    n = max(1, int(math.dist(a[:3], b[:3]) // 20))
    for t in range(n + 1):
        m = [a[i] + (b[i] - a[i]) * t / n for i in range(3)]
        if lane(m) or G.at(m[0], m[1], m[2], dy=dy) is None:
            return False
        if any(bx[0] - keep <= m[0] <= bx[1] + keep and bx[2] - keep <= m[2] <= bx[3] + keep for bx in blocks):
            return False
    return not walls or post_gap(walls, a, b)[0] >= wall


class Line:
    """A lane's line: points with the length run up to each; where(p) = (how far along it, how far to its side) for
    the nearest point of it."""

    def __init__(self, pts):
        self.pts = [tuple(p[:3]) for p in pts]
        self.run = [0.0]
        for p, q in zip(self.pts, self.pts[1:]):
            self.run.append(self.run[-1] + math.hypot(q[0] - p[0], q[2] - p[2]))
        self.length = self.run[-1]

    def where(self, p):
        best = (1e18, 0.0)
        for i, (a, b) in enumerate(zip(self.pts, self.pts[1:])):
            dx, dz = b[0] - a[0], b[2] - a[2]
            L = dx * dx + dz * dz
            t = 0.0 if L < 1e-9 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[2] - a[2]) * dz) / L))
            d = math.hypot(p[0] - a[0] - t * dx, p[2] - a[2] - t * dz)
            if d < best[0]:
                best = (d, self.run[i] + t * math.sqrt(L))
        return best[1], best[0]

    def at(self, s):
        s = max(0.0, min(self.length, s))
        for i in range(len(self.pts) - 1):
            if s <= self.run[i + 1] or i == len(self.pts) - 2:
                L = self.run[i + 1] - self.run[i]
                t = 0.0 if L < 1e-9 else (s - self.run[i]) / L
                a, b = self.pts[i], self.pts[i + 1]
                return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))

    def heading(self, s):
        a, b = self.at(s - 60.0), self.at(s + 60.0)
        n = math.hypot(b[0] - a[0], b[2] - a[2]) or 1.0
        return ((b[0] - a[0]) / n, (b[2] - a[2]) / n)


def program_steps(items, key):
    """A bot's program (lanes_plan: step / timer / fork items) along lane `key` -> [[name, [place ..], timer seconds
    or None]] for walk_model()."""
    out = []
    for it in items:
        if it['kind'] == 'step':
            out.append([it['name'], [tuple(p) for p in it['places']], None])
        elif it['kind'] == 'timer' and out:
            out[-1][2] = float(it['seconds'])
        elif it['kind'] == 'fork':
            out += program_steps(next(w for w in it['ways'] if w['lane'] == key)['items'], key)
    return out


def parked(B):
    """[(name, x0, x1, z0, z1)] of kl_fa_street's parked vehicles (COVER_PLACE) that stand on the road in THIS build."""
    out = []
    for (nm, x0, x1, z0, z1), path in zip(street.footprints(), street.COVER_PLACE):
        hit = B.sc.resolve(R_ + path)
        if len(hit) == 1 and hdist(B.at(hit[0]), ((x0 + x1) / 2, 0.0, (z0 + z1) / 2)) < 60.0:
            out.append((nm, x0, x1, z0, z1))
    return out


STREET_WINDOW = (-6600.0, 7300.0, -9200.0, 13400.0)     # x0, x1, z0, z1: the lobby, the square and the road (not the bus terminal)


def street_ground(B, nav, part, exits=(), danger=(), walls=()):
    """-> (Ground, Walk, blocks) of the street's mesh part: the grid without the pedestrian bridge (polygons over the
    road, y > 150 west of the lobby), without the parked vehicles and without the van's lane (lane()); with `exits`
    (level exit box nodes) without those boxes too: a bot inside one calls the van; with `walls` (places) without
    the ground within POST_WALL of each."""
    G = Ground(nav, part)
    blocks = [f[1:] for f in parked(B)]
    # (... and without the polygons that are no planes: fitted heights off by more than WARP_WAY - the two southern
    # bays of the square, 1.1 and 2.3 m, which open on Squad_InFront's cars. Since the timed way ends inside the
    # building - its clock runs at V_SLOW - the lanes' own ways cross the square)
    usable = lambda i: not (nav.mid[i][0] < 2400.0 and max(v[1] for v in nav.pv[i]) > 150.0) and warp(nav, i) <= WARP_WAY
    k = FOOT_KEEP
    more = [(van.LANE_X - street.VAN_CLEAR + k, van.LANE_X + street.VAN_CLEAR - k, van.WAIT_Z - LANE_SOUTH + k, 1e9)]
    for e in exits:
        s_ = B.box(e)
        cs = [B.world(e, (sx * s_[0], 0.0, sz * s_[2])) for sx in (-1, 1) for sz in (-1, 1)]
        more.append((min(c[0] for c in cs) + k, max(c[0] for c in cs) - k, min(c[2] for c in cs) + k - 60.0, max(c[2] for c in cs) - k))
    return G, Walk(G, blocks + more, usable, region=STREET_WINDOW, danger=danger, walls=walls), blocks


def lanes_plan(B, nav, S, st, opt, log=print):
    """THE STREET IN LANES: the stations of street_plan()'s plan `st` between the lobby's EXITS_BANK box and the rally
    laid anew - per bot the timed way out of the building, its lane(s), the rally, the level exit box and the place
    beside the van's stop (each leg a straight line clear of the parked vehicles). st is rewritten: 'lanes' holds the
    plan (per bot its program: the items Street.lane_nodes turns into nodes), 'stations' the same places in the old
    shape (one row a station, a place a bot: kl_playtest walks them; a bot's row is its first lane)."""
    sc, notes = B.sc, []
    name = lambda k: sc.path[k][5:]
    r1 = lambda p: [round(v, 1) for v in p[:3]]
    _jp, jpos, _face = join_point(B)
    part = nav.part[nav.at(jpos[0], jpos[1], jpos[2], lo=jpos[1] - 300.0, hi=jpos[1] + 100.0)[0]]
    posts = street_posts(B)
    walls = wall_posts(posts)
    wall_q = [q for _t, _w, q in walls]
    G, W, blocks = street_ground(B, nav, part, S['exits'], [q for _t, _w, q in posts], wall_q)
    log('lanes: the street\'s mesh part as a grid of %d: %d free cells, %d open, %d with room on all sides; %d parked vehicle(s) of kl_fa_street on '
        'the road (no hole in the mesh under them): %s' % (GRID, len(W.cells), len(W.open), len(W.wide), len(blocks),
                                                          ', '.join(f[0].split('_')[-1] for f in parked(B)) or 'none'))
    main = collections.Counter(W.comp.values()).most_common(1)[0][0]     # the ground the ways are laid on: the grid's largest connected part
    exits = S['exits']
    inbox = lambda q: bool(F.in_exit(B, exits, q))
    post_d = lambda q: min([hdist(q, p) for _t, _w, p in posts if abs(p[1] - q[1]) <= 260.0] or [1e9])
    covers = [c for c in cover_geom(B) if G.at(c['mid'][0], c['y'], c['mid'][2], dy=400.0) is not None
              or any(G.at(c['mid'][0] + dx, c['y'], c['mid'][2] + dz, dy=400.0) is not None for dx, dz in ((260, 0), (-260, 0), (0, 260), (0, -260)))]
    anchors = covers
    log('lanes: %d cover boxes at the street part (%d with the origin over %d from their box\'s middle: a bus\'s end); %d posts of the police, %d of them '
        'WALL posts (no way within %d: a start place, a place a behaviour names, a RunToCover point)'
        % (len(covers), sum(1 for c in covers if c['off'] > COVER_OFF), COVER_OFF, len(posts), len(walls), POST_WALL))
    _spots = {}

    def spots(c):
        """The hold places of cover box c: [(x, y, z, polygon, clearance, distance from the box's edge)]."""
        if c['node'] not in _spots:
            fp, out = c['fp'], []
            for ix in range(int((fp[0] - SPOT[1]) // 40), int((fp[1] + SPOT[1]) // 40) + 2):
                for iz in range(int((fp[2] - SPOT[1]) // 40), int((fp[3] + SPOT[1]) // 40) + 2):
                    x, z = ix * 40.0, iz * 40.0
                    d = fp_dist(fp, x, z)
                    if not SPOT[0] <= d <= SPOT[1] or math.hypot(x - c['mid'][0], z - c['mid'][2]) > HOLD_COVER - 30.0:
                        continue
                    hit = G.at(x, c['y'], z, dy=150.0)
                    if hit is None or warp(nav, hit[0]) > WARP or W.blocked(x, z) or lane((x, hit[1], z)):
                        continue
                    # (c must be the box NEAREST to the place: 'one bot a box' is counted by the box a hold is nearest to -
                    # the first build had three squads round one sign of 1.7 m, each at a neighbour box's place: review S5)
                    if any(o is not c and abs(o['y'] - c['y']) < 260.0 and fp_dist(o['fp'], x, z) < max(25.0, d) for o in covers):
                        continue
                    cl = G.clearance(x, hit[1], z)
                    cell = cl >= HOLD_CLEAR and W.snap((x, hit[1], z), 3)
                    if not cell or W.comp[cell] != main:    # (not on the ground the ways are laid on: inside a planter, behind a rail)
                        continue
                    out.append((x, hit[1], z, hit[0], cl, d))
            _spots[c['node']] = out
        return _spots[c['node']]

    def place_of(xz, what):
        """A point (x, z) of a table above as a place on the grid: the open cell nearest to it."""
        hs = sorted(h for _i, h in G.under(xz[0], xz[1]) if h <= 700.0)
        c = W.snap((xz[0], hs[0] if hs else 0.0, xz[1]), 8)
        if c is None:
            raise ValueError('lanes: %s (%d, %d) is not on open ground of the street part' % (what, xz[0], xz[1]))
        return W.point(c)

    def leg_ok(a, b, slack=LINE_SLACK):
        """A way a -> b whose pieces are straight on the mesh and clear -> (points, length) or None."""
        got = W.leg(a, b)
        if got is None or got[1] > slack[0] * math.dist(a[:3], b[:3]) + slack[1]:
            return None
        if not all(straight_clear(G, blocks, p, q, walls=walls) for p, q in zip(got[0], got[0][1:])):
            return None
        return got

    i_exit = next((i for i, x in enumerate(st['stations']) if x['kind'] == 'exit'), None)
    i_rally = next((i for i, x in enumerate(st['stations']) if x['kind'] == 'rally'), None)
    if i_exit is None or i_rally is None:
        raise ValueError('lanes: the street plan has no EXITS_BANK place or no rally (--street-hold 0?): build with --no-lanes')
    taken, held = {}, []                                # {cover node: [squad]}, [(squad, hold place)]
    # one bot a box - but a box SHARE_LEN[0] long takes two and one SHARE_LEN[1] long three, HOLD_SEP apart (a car's
    # middle box is 2 m, the square's low walls 6 m: run J1 had five of the seven in a row behind one such wall, a
    # metre apart, of the game's own choosing)
    room = box_room
    free = lambda c, N: N in taken.get(c['node'], ()) or len(taken.get(c['node'], ())) < room(c)
    take = lambda c, N: taken.setdefault(c['node'], []).append(N) if N not in taken.get(c['node'], ()) else None
    apart = lambda q, N: all(n == N or hdist(q, o) >= STREET_SEP for n, o in held)
    bots = collections.OrderedDict()
    order = [N for N in (2, 7, 4, 5, 3, 6, 8) if N in F.BOTS]       # who chooses his covers first (kl_fa_bots_dyn.ORDER)

    # ---- A. the timed way out of the building
    # e0: a bot's place in the EXITS_BANK box (stage 2; the box lies across the lobby between the lift landing and the
    # two ramps down, so every way out passes it) - the ramp of its side, the place with the most room. Bots share it:
    # nobody stands there, the step that names it is 'reached' from where the hook puts them.
    ek = S['triggers'].get('EXITS', [])[:1]
    ec = [q for k in ek for q in F.box_places(B, nav, k, part, share=F.INSIDE) if flat(nav, q) and W.snap(q, 3) is not None]
    ramp = {}
    for r_, keep in (('n', lambda q: q[2] > jpos[2]), ('s', lambda q: q[2] <= jpos[2])):
        c = [q for q in ec if keep(q)]
        if not c:
            raise ValueError('lanes: no place inside the EXITS_BANK box on the %s ramp of the lobby' % {'n': 'north', 's': 'south'}[r_])
        ramp[r_] = max(c, key=lambda q: (min(G.clearance(*q[:3]), 150.0), -abs(q[0] - sum(x[0] for x in c) / len(c))))
    for N in order:
        e0 = ramp[RAMP[N]]
        pts = [tuple(e0[:3])]
        for v in BAYS[BAY[N]]:
            q = place_of(v, 'a point of bay %s' % BAY[N])
            got = W.leg(pts[-1], q)
            if got is None:
                raise ValueError('lanes: Squad#0%d: no way on the grid from (%d, %d, %d) to (%d, %d) of its bay %s' % (N, *pts[-1], q[0], q[2], BAY[N]))
            pts += got[0][1:]
        line = Line(pts)
        near = [c for c in anchors if line.where(c['mid'])[1] <= CLOCK_REACH + 300.0]
        cur, s_cur, timed = e0, 0.0, []
        safe = float(opt.get('join_safe', JOIN_SAFE))
        on_clock = lambda: STAGGER.get(N, 0.0) + CLOCK_START + sum(t['seconds'] for t in timed)
        # THE CLOCK RUNS AT V_SLOW: a place's timer = its way at V_SLOW (+ CLOCK_PAUSE at a cover), so a bot that walks
        # V_SLOW or faster is AT the place when the timer fires, the next step is 'reached' as it starts, and a timer
        # is pending all the time. The timed way ends when the clock has run JOIN_SAFE (or at its bay's end); the rest
        # of the bay's line is the first stretch of the bot's lane (bay_rest), walked by arrivals as every lane.
        while line.length - s_cur > CLOCK_END and on_clock() < safe:
            # the next place: a cover box's, within CALL_REACH of this one (so its step is 'reached' as it starts and
            # its timer runs while the bot walks) and CLOCK_MIN further along; where there is none, a place on the way
            cands = []
            for c in near:
                if not free(c, N):
                    continue
                for q in spots(c):
                    s, d = line.where(q)
                    if d > CLOCK_REACH or s < s_cur + CLOCK_MIN or math.dist(q[:3], cur[:3]) > CALL_REACH:
                        continue
                    if post_d(q) < POST_KEEP_ST or not apart(q, N) or inbox(q) or post_gap(walls, cur, q)[0] < POST_WALL:
                        continue
                    hd = line.heading(s)
                    behind = (c['mid'][0] - q[0]) * hd[0] + (c['mid'][2] - q[2]) * hd[1] > 0.3 * hdist(c['mid'], q)
                    cands.append((s + (0.0 if behind else -250.0) + min(q[4], F.CLEAR) - 0.5 * d, q, c))
            pick = None
            for _key, q, c in sorted(cands, key=lambda x: -x[0])[:12]:
                way = W.leg(cur, q)
                if way is not None and way[1] <= CALL_REACH * 1.5:
                    pick = (q, c, way[1]); break
            if pick is None:                            # no cover box in reach: a place on the way (as far on as may be), or beside it
                s_try = s_cur + CALL_REACH - 100.0
                while pick is None and s_try >= s_cur + 160.0:
                    m, hd = line.at(s_try), line.heading(s_try)
                    for off in (0.0, 80.0, -80.0, 160.0, -160.0, 240.0, -240.0):
                        cell = W.snap((m[0] - hd[1] * off, m[1], m[2] + hd[0] * off), 1)
                        q = cell and W.point(cell)
                        if q and W.comp[cell] == main and math.dist(q, cur[:3]) <= CALL_REACH and warp(nav, W.cells[cell][1]) <= WARP_WAY \
                                and G.clearance(*q) >= F.CLEAR and line.where(q)[0] >= s_cur + 120.0 and not inbox(q) and apart(q, N) \
                                and post_gap(walls, cur, q)[0] >= POST_WALL:
                            way = W.leg(cur, q)
                            if way is not None and way[1] <= CALL_REACH * 1.5:
                                pick = (q + (W.cells[cell][1], G.clearance(*q), 0.0), None, way[1]); break
                    s_try -= 40.0
            if pick is None:
                raise ValueError('lanes: Squad#0%d: no next place on its timed way within %d of (%d, %d, %d), %d along it' % (N, CALL_REACH, *cur[:3], s_cur))
            q, c, plen = pick
            held.append((N, q))                         # (a place without a cover box too: no two bots are sent to one point)
            if c is not None:
                take(c, N)
            timed.append({'place': r1(q), 'cover': c and name(c['node']), 'cover_at': c and r1(c['mid']), 'path': round(plen), 'from_the_last': round(math.dist(q[:3], cur[:3])),
                          'from_a_post': round(post_d(q)), 'seconds': round(plen / V_SLOW + (CLOCK_PAUSE if c is not None else 0.2) + 0.05, 1)})
            cur, s_cur = q, line.where(q)[0]
            if len(timed) > 14:
                raise ValueError('lanes: Squad#0%d: over 14 places on its timed way' % N)
        bay_rest = [p for p, r_ in zip(line.pts, line.run) if r_ > s_cur + 80.0]     # the bay's line from the timed way's last place on
        short = safe - on_clock()
        at_cover = [t for t in timed if t['cover']] or timed
        if short > 0:                                   # (the clock must run as long as a wait of the tower chain can still fire)
            for t in at_cover:
                t['seconds'] = round(t['seconds'] + short / len(at_cover) + 0.05, 1)
        bots[N] = collections.OrderedDict(squad='Squad#0%d' % N, ramp=RAMP[N], bay=BAY[N], exit=r1(e0), start_seconds=round(STAGGER.get(N, 0.0) + CLOCK_START, 1),
                                          timed=timed, timed_seconds=round(STAGGER.get(N, 0.0) + CLOCK_START + sum(t['seconds'] for t in timed), 1),
                                          timed_path=round(sum(t['path'] for t in timed)), bay_rest=[r1(p) for p in bay_rest], lanes=collections.OrderedDict())
        log('  Squad#0%d  %s ramp, timed way towards bay %s: %d places (%d at a cover box), %d of way, each %d..%d from the last; %.1f s on the clock at %d units / s '
            '(%g s of it at the ramp); the last at (%d, %d, %d), %d of the bay\'s line still to walk'
            % (N, {'n': 'north', 's': 'south'}[RAMP[N]], BAY[N], len(timed), sum(1 for t in timed if t['cover']),
               bots[N]['timed_path'], min(t['from_the_last'] for t in timed), max(t['from_the_last'] for t in timed),
               bots[N]['timed_seconds'], V_SLOW, bots[N]['start_seconds'], *timed[-1]['place'], line.length - s_cur))

    # ---- D (first: the lanes end at it). The rally, the level exit box, the places beside the van's stop
    side = 1.0 if st['lane_side'] == 'east' else -1.0
    _G2, W2, _b2 = street_ground(B, nav, part, walls=wall_q)    # (the ground with the level exit box in it)
    good = lambda q: flat(nav, q) and not W2.blocked(q[0], q[2]) and W2.snap(q, 3) is not None \
        and (q[2] < st['lane_from_z'] or (q[0] - van.LANE_X) * side >= street.VAN_CLEAR)
    anchor = tuple(st['stations'][i_rally]['places'][0])
    c = [x for x in nav.around(anchor, 360.0, part) if good(x) and not inbox(x) and post_d(x) >= POST_KEEP_ST * 0.5]
    rally = nav.spots(c, 7, F.SEP, ref=anchor)
    if len(rally) < 7:
        raise ValueError('lanes: only %d rally places round (%d, %d, %d) clear of the parked vehicles' % (len(rally), *anchor))
    s0 = tuple(st['stop'])
    ring = [q for q in nav.around(s0, STOP_RING[1], part, dy=120.0) if good(q) and STOP_RING[0] <= hdist(q, s0) <= STOP_RING[1]]
    if not ring:
        raise ValueError('lanes: no place %d..%d from the van\'s stop clear of the parked vehicles' % STOP_RING)
    park0 = min(ring, key=lambda q: (hdist(q, s0), abs(q[2] - s0[2])))
    park = nav.spots([q for q in ring if hdist(q, park0) <= 420.0], 7, F.SEP, ref=park0)
    if len(park) < 7:
        park = nav.spots([q for q in ring if hdist(q, park0) <= 420.0], 7, 80.0, ref=park0)
    lev_k = next((k for k in exits if any(x.get('node') == name(k) for x in st['stations'])), exits[0])
    lc = [q for q in F.box_places(B, nav, lev_k, part, share=EXIT_SHARE) if good(q) and post_d(q) >= POST_KEEP_ST * 0.5]
    lc.sort(key=lambda q: hdist(q, anchor))
    level = None
    for ref in lc[:60]:                                 # the place inside the box nearest to the rally from which seven fit, each a straight way in
        pick = nav.spots([q for q in lc if hdist(q, ref) <= 420.0], 7, F.SEP, ref=ref)
        if len(pick) == 7 and all(straight_clear(G, blocks, r, q, walls=walls) for r, q in zip(rally, pick)):
            level = pick; break
    if level is None or len(park) < 7:
        raise ValueError('lanes: no seven places inside the level exit box with a straight way from the rally, or beside the van\'s stop (%d)' % len(park))
    tail = {}
    for N in F.BOTS:
        b = N - 2
        got = W2.leg(level[b], park[b])
        if got is not None and not all(straight_clear(G, blocks, p_, q_, walls=walls) for p_, q_ in zip(got[0], got[0][1:])):
            got = None
        if got is None:
            raise ValueError('lanes: Squad#0%d: no clear way from its place in the level exit box (%d, %d, %d) to its place beside the van (%d, %d, %d)'
                             % (N, *level[b][:3], *park[b][:3]))
        tail[N] = got
    log('lanes: rally round (%d, %d, %d); in the level exit box round (%d, %d, %d); beside the stop round (%d, %d, %d): the ways from box to stop %d..%d long, '
        '%d..%d turning point(s) (round the parked vehicles)' % (*anchor, *level[0][:3], *park0[:3], min(t[1] for t in tail.values()), max(t[1] for t in tail.values()),
                                                                min(len(t[0]) - 2 for t in tail.values()), max(len(t[0]) - 2 for t in tail.values())))

    # ---- C. the lanes
    table = {L['key']: L for L in LANES}
    ends = {L['key']: place_of(L['end'], 'the end of lane %s' % L['key']) for L in LANES}
    vias = {L['key']: [place_of(v, 'a point of lane %s' % L['key']) for v in L['via']] for L in LANES}
    population = collections.Counter()
    ways_drawn = []
    for N in order:
        me = bots[N]
        start = tuple(me['timed'][-1]['place'])
        for li, key in enumerate(DEAL[N]):
            pts = [start]
            chain_ = [tuple(p) for p in me['bay_rest']] + vias[key]
            for a_, b_ in zip([start] + chain_, chain_ + [ends[key]]):
                got = W.leg(a_, b_)
                if got is None:
                    raise ValueError('lanes: lane %s for Squad#0%d: no way on the grid from (%d, %d, %d) to (%d, %d, %d)' % (key, N, *a_[:3], *b_[:3]))
                pts += got[0][1:]
            line = Line(pts)
            near = [c_ for c_ in anchors if line.where(c_['mid'])[1] <= LANE_REACH + 300.0]
            cur, s_cur, holds, first, open_run = start, 0.0, [], True, 0
            # (a lane's bound: its length over LANE_HOLDS + 1, at least BOUND_BEST - the far side is twice as long as
            # this side, and a bot that stops as often on it comes a minute late)
            best = max(BOUND_BEST, line.length / (LANE_HOLDS + 1.0))
            secs = hold_timer(key, N)
            while True:
                lo, hi = s_cur + best * BOUND[0], s_cur + best * BOUND[1]
                if lo > line.length - END_GAP:
                    break
                want = s_cur + best * (PHASE.get(N, 1.0) if first else 1.0)
                pick = None
                for reach in (hi, s_cur + best * BOUND_FAR):
                    cands = []
                    for c_ in near:
                        if not free(c_, N):
                            continue
                        for q in spots(c_):
                            s, d = line.where(q)
                            if d > LANE_REACH or not lo <= s <= min(reach, line.length - END_GAP):
                                continue
                            if post_d(q) < POST_KEEP_ST or not apart(q, N) or inbox(q) or math.dist(q[:3], cur[:3]) < ARRIVE_3D + 100.0:
                                continue
                            hd = line.heading(s)
                            behind = (c_['mid'][0] - q[0]) * hd[0] + (c_['mid'][2] - q[2]) * hd[1] > 0.3 * hdist(c_['mid'], q)
                            cands.append((abs(s - want) + (0.0 if behind else 500.0) + (0.0 if q[4] >= F.CLEAR else 150.0) + 0.5 * d, s, q, c_))
                    for _key, s, q, c_ in sorted(cands, key=lambda x: x[0])[:40]:
                        got = leg_ok(cur, q)
                        on = got and W.leg(q, line.at(min(s + 700.0, line.length)))     # (no hold in a dead end, behind the median)
                        if on is not None and on[1] <= 1.6 * math.dist(q[:3], on[0][-1]) + 700.0:
                            pick = (s, q, c_, got); break
                    if pick:
                        break
                if pick is None:
                    # no cover in reach: the bot walks on (a way place on the lane's line, no wait)
                    q = W.snap(line.at(s_cur + best), 6)
                    q = q and W.point(q)
                    got = q and leg_ok(cur, q, (2.5, 800.0))
                    if not got:
                        raise ValueError('lanes: lane %s for Squad#0%d: no hold and no clear way on from (%d, %d, %d), %d along the lane' % (key, N, *cur[:3], s_cur))
                    holds.append({'place': r1(q), 'cover': None, 'ways': [r1(p) for p in got[0][1:-1]], 'seconds': 0.0, 'path': round(got[1]), 'along': round(s_cur + best)})
                    cur, s_cur, open_run = q, s_cur + best, open_run + 1
                    continue
                s_cur, q, c_, got = pick
                take(c_, N); held.append((N, q))
                holds.append({'place': r1(q), 'cover': name(c_['node']), 'cover_at': r1(c_['mid']), 'ways': [r1(p) for p in got[0][1:-1]],
                              'seconds': secs, 'path': round(got[1]), 'along': round(s_cur), 'from_cover': round(q[5]), 'from_a_post': round(post_d(q))})
                cur, first = q, False
            # the lane's last piece: to its end place, and on to the bot's rally place (the last line into the rally is straight)
            g1, g2 = leg_ok(cur, ends[key], (2.5, 800.0)), leg_ok(ends[key], rally[N - 2], (2.5, 800.0))
            if g1 is None or g2 is None:
                raise ValueError('lanes: lane %s for Squad#0%d: no clear way from its last hold (%d, %d, %d) to the lane\'s end or from there to the rally'
                                 % (key, N, *cur[:3]))
            end_ways = [r1(p) for p in g1[0][1:] + g2[0][1:-1]]
            n_hold = sum(1 for h in holds if h['cover'])
            walk_len = sum(h['path'] for h in holds) + g1[1] + g2[1]
            me['lanes'][key] = collections.OrderedDict(
                what=table[key]['what'], holds=holds, end_ways=end_ways, length=round(walk_len), n_holds=n_hold, open_stretches=open_run,
                hold_seconds=round(sum(h['seconds'] for h in holds), 1))
            population[key] += 1
            ways_drawn.append({'bot': N - 1, 'squad': N, 'lane': key, 'main': li == 0,
                               'pts': [me['exit']] + [t['place'] for t in me['timed']] + [p for h in holds for p in h['ways'] + [h['place']]] + end_ways + [r1(rally[N - 2])]})
            log('  Squad#0%d  lane %s%s: %d holds at cover (a timer of %g s or more each: the walk in at %d units / s, %g s on a straight line, + a stand of %g s)%s, %d of way '
                'from the timed way\'s end to the rally' % (N, key, ' (always)' if len(DEAL[N]) == 1 else ' (drawn, %d : %d)' % WEIGHTS if li == 0 else ' (the other draw)', n_hold,
                                                           secs, V_SLOW, round(ARRIVE_3D / V_SLOW, 1), hold_stand(key, N),
                                                           ', %d stretch(es) without a cover in reach' % open_run if open_run else '', walk_len))
    for N in F.BOTS:
        b = N - 2
        bots[N]['rally'], bots[N]['level'], bots[N]['park'] = r1(rally[b]), r1(level[b]), r1(park[b])
        bots[N]['tail_ways'] = [r1(p) for p in tail[N][0][1:-1]]
        ways_drawn.append({'bot': N - 1, 'squad': N, 'lane': 'to the van', 'main': True, 'pts': [r1(rally[b])] + [r1(p) for p in tail[N][0]]})
    if any(population[L['key']] == 0 for L in LANES):
        raise ValueError('lanes: DEAL leaves a lane empty: %s' % dict(population))
    always = collections.Counter(DEAL[N][0] for N in DEAL if len(DEAL[N]) == 1)
    for L in LANES:
        if not always[L['key']]:
            notes.append('lane %s has no bot that always takes it: in some rounds it is empty' % L['key'])
    # ---- the programs: what Street.lane_nodes writes, per bot, in the order it runs
    hold_s = float(opt['street_hold'])
    for N in F.BOTS:
        me, items = bots[N], []
        # (050 keeps its name - the JumpPoint names it: the bot's place in the EXITS_BANK box; then the timed way)
        items.append({'kind': 'step', 'name': '050_DefendBehaviour_street', 'places': [me['exit']]})
        items.append({'kind': 'timer', 'name': '050_Timer_out_start', 'seconds': me['start_seconds']})
        for k, t in enumerate(me['timed']):
            items.append({'kind': 'step', 'name': '051_DefendBehaviour_out_%02d' % (k + 1), 'places': [t['place']], 'timed': True})
            items.append({'kind': 'timer', 'name': '051_Timer_out_%02d' % (k + 1), 'seconds': t['seconds']})
        ways = []
        for key in DEAL[N]:
            pre, its, run = LANE_PRE[key], [], []
            for i, h in enumerate(me['lanes'][key]['holds']):
                run += h['ways'] + [h['place']]
                if h['cover'] is None:                  # (a stretch without cover: its place is a way place of the next step)
                    continue
                while len(run) > F.STEP_MAX:
                    its.append({'kind': 'step', 'name': '%s_DefendBehaviour_lane_%s_%02d_way%s' % (pre, key, i + 1, 'abcdefghijklmnopqrstuvwxyz'[len([x for x in its if ('_%02d_way' % (i + 1)) in x['name']])]),
                                'places': run[:F.STEP_MAX]})
                    run = run[F.STEP_MAX:]
                its.append({'kind': 'step', 'name': '%s_DefendBehaviour_lane_%s_%02d' % (pre, key, i + 1), 'places': run, 'hold': True})
                its.append({'kind': 'timer', 'name': '%s_Timer_lane_%s_%02d' % (pre, key, i + 1), 'seconds': h['seconds']})
                run = []
            run += me['lanes'][key]['end_ways']
            n = 0
            while run:
                its.append({'kind': 'step', 'name': '%s_DefendBehaviour_lane_%s_in%s' % (pre, key, '' if not n else '_' + 'bcdefghijklmnopqrstuvwxyz'[n - 1]), 'places': run[:F.STEP_MAX]})
                run, n = run[F.STEP_MAX:], n + 1
            ways.append({'lane': key, 'items': its})
        if len(ways) == 1:
            items += ways[0]['items']
        else:
            items.append({'kind': 'fork', 'name': '060_RandomTrigger_lane', 'ways': [dict(w, weight=WEIGHTS[i]) for i, w in enumerate(ways)]})
        items.append({'kind': 'step', 'name': '069_DefendBehaviour_rally', 'places': [me['rally']]})
        if hold_s > 0:
            items.append({'kind': 'timer', 'name': '070_Timer_rally', 'seconds': hold_s})
        run, n = [me['level']] + me['tail_ways'] + [me['park']], 0
        while run:
            items.append({'kind': 'step', 'name': '%03d_DefendBehaviour_to_van' % (80 + n), 'places': run[:F.STEP_MAX]})
            run, n = run[F.STEP_MAX:], n + 1
        me['program'] = items
        # A HOLD'S TIMER = its stand + the walk in at V_SLOW by the walk model (a timer that has fired before a slow
        # bot is at the hold orders him on from the open: review S1). One pass serves: with every timer at least the
        # walk in, the bot is AT the hold when the next step starts, whatever the timers before were.
        timer_of = {}
        def index(its):
            for it in its:
                if it['kind'] == 'timer':
                    timer_of[it['name']] = it
                elif it['kind'] == 'fork':
                    for w_ in it['ways']:
                        index(w_['items'])
        index(items)
        for key in DEAL[N]:
            hs_plan = [h for h in me['lanes'][key]['holds'] if h['cover']]
            rows_ = [r_ for r_ in walk_model(program_steps(items, key), V_SLOW) if LANE_TAG in r_['name'] and r_['timer'] is not None]
            if len(rows_) != len(hs_plan):
                raise ValueError('lanes: Squad#0%d lane %s: %d hold steps for %d holds' % (N, key, len(rows_), len(hs_plan)))
            for r_, h in zip(rows_, hs_plan):
                secs = max(hold_timer(key, N), round(r_['arrive'] - r_['reached'] + hold_stand(key, N) + 0.05, 1))
                h['seconds'] = secs
                h['walk_in_slow'] = round(r_['arrive'] - r_['reached'], 1)
                timer_of[r_['name'].replace('_DefendBehaviour_lane_', '_Timer_lane_')]['seconds'] = secs
            me['lanes'][key]['hold_seconds'] = round(sum(h['seconds'] for h in hs_plan), 1)
        # THE PACE BY THE WALK MODEL (walk_model: a hold's timer starts ARRIVE_3D before the hold, so it is NOT added
        # whole to the walk - the first note's table did that: review S7), at V_PLAN and at V_SLOW
        for key in DEAL[N]:
            pace = collections.OrderedDict()
            for v in (V_PLAN, V_SLOW):
                rows_ = walk_model(program_steps(items, key), v)
                rl = next(r_ for r_ in rows_ if r_['name'] == '069_DefendBehaviour_rally')
                hs_ = [r_ for r_ in rows_ if LANE_TAG in r_['name'] and r_['timer'] is not None]
                pace[str(int(v))] = collections.OrderedDict(
                    at_the_rally=round(rl['arrive'], 1), leaves_the_rally=round(rl['next'], 1),
                    no_timer_on_the_timed_way=round(sum(r_['no_timer'] for r_ in rows_[1:] if TIMED_TAG in r_['name']), 1),
                    stands_at_a_hold=[round(min(r_['stood'] for r_ in hs_), 1), round(max(r_['stood'] for r_ in hs_), 1)] if hs_ else None)
            me['lanes'][key]['pace'] = pace
            a_, b_ = pace[str(int(V_PLAN))], pace[str(int(V_SLOW))]
            log('  Squad#0%d  lane %s by the walk model: at the rally %d s after its first street step at %d units / s (stands %s s at a hold), %d s at %d (stands %s s); '
                'seconds of the timed way without a pending timer: %g / %g' % (N, key, a_['at_the_rally'], V_PLAN, '..'.join('%g' % x for x in a_['stands_at_a_hold'] or []) or '-',
                                                                             b_['at_the_rally'], V_SLOW, '..'.join('%g' % x for x in b_['stands_at_a_hold'] or []) or '-',
                                                                             a_['no_timer_on_the_timed_way'], b_['no_timer_on_the_timed_way']))
    # ---- the old shape, for what reads it (kl_playtest walks a bot's row): a bot's first lane
    rows = collections.OrderedDict()
    for N in F.BOTS:
        me = bots[N]
        lane0 = me['lanes'][DEAL[N][0]]
        rows[N] = [t['place'] for t in me['timed']] + [p for h in lane0['holds'] for p in h['ways'] + [h['place']]] + lane0['end_ways']
    n_way = max(len(r) for r in rows.values())
    stations = [dict(st['stations'][i_exit], places=[bots[N]['exit'] for N in F.BOTS], distinct_places=len({tuple(bots[N]['exit']) for N in F.BOTS}))]
    for j in range(n_way):
        stations.append({'kind': 'way', 'what': 'the timed way and the first lane of each bot, place %d (a bot with fewer: its last)' % (j + 1), 'node': None,
                         'distinct_places': 7, 'places': [rows[N][min(j, len(rows[N]) - 1)] for N in F.BOTS]})
    stations.append({'kind': 'rally', 'what': 'the rally place before the level exit box (hold %g s)' % hold_s, 'node': None, 'distinct_places': 7,
                     'places': [bots[N]['rally'] for N in F.BOTS]})
    stations.append({'kind': 'level', 'what': 'level exit %s (stage 3; a bot inside it calls the van: kl2 0x6cd8e0)' % name(lev_k), 'node': name(lev_k),
                     'distinct_places': 7, 'places': [bots[N]['level'] for N in F.BOTS]})
    for j in range(max(len(bots[N]['tail_ways']) for N in F.BOTS)):
        stations.append({'kind': 'way', 'what': 'round the parked vehicles to the van\'s stop, place %d' % (j + 1), 'node': None, 'distinct_places': 7,
                         'places': [(bots[N]['tail_ways'] + [bots[N]['park']])[min(j, len(bots[N]['tail_ways']))] for N in F.BOTS]})
    stations.append({'kind': 'park', 'what': 'beside the van\'s stop, %d..%d from the boarding box, on the %s side of its lane' % (*STOP_RING, st['lane_side']),
                     'node': None, 'distinct_places': 7, 'places': [bots[N]['park'] for N in F.BOTS]})
    st['stations'] = stations
    st['steps'] = [{'name': it['name'], 'kind': it['kind']} for it in bots[F.BOTS[0]]['program']]
    # ---- the lanes as stations (for the pictures and the report)
    lanes_out = []
    for L in LANES:
        hs = [(N, h) for N in F.BOTS if L['key'] in bots[N]['lanes'] for h in bots[N]['lanes'][L['key']]['holds'] if h['cover']]
        lanes_out.append(collections.OrderedDict(
            key=L['key'], what=L['what'], bots_always=[N for N in DEAL if DEAL[N] == (L['key'],)], bots_drawn=[N for N in DEAL if L['key'] in DEAL[N] and len(DEAL[N]) > 1],
            holds=len(hs), boxes=len({h['cover'] for _n, h in hs}), x=[round(min(h['place'][0] for _n, h in hs)), round(max(h['place'][0] for _n, h in hs))] if hs else None,
            z=[round(min(h['place'][2] for _n, h in hs)), round(max(h['place'][2] for _n, h in hs))] if hs else None,
            from_a_post=[round(min(h['from_a_post'] for _n, h in hs)), round(max(h['from_a_post'] for _n, h in hs))] if hs else None,
            stations=[{'n': i + 1, 'squad': n, 'places': [h['place']], 'cover_at': [h['cover_at']]} for i, (n, h) in enumerate(hs)]))
        log('lanes: lane %s (%s): always Squad %s, drawn by %s; %d holds at %d cover boxes for those, x %s, z %s; nearest post of the police %s from a hold'
            % (L['key'], L['what'], ' '.join('#0%d' % n for n in lanes_out[-1]['bots_always']) or '-', ' '.join('#0%d' % n for n in lanes_out[-1]['bots_drawn']) or '-',
               lanes_out[-1]['holds'], lanes_out[-1]['boxes'], lanes_out[-1]['x'], lanes_out[-1]['z'], lanes_out[-1]['from_a_post']))
    for n in notes:
        log('  NOTE ' + n)
    st['notes'] = st.get('notes', []) + notes
    st['lanes'] = collections.OrderedDict(
        deal={str(N): list(DEAL[N]) for N in F.BOTS}, bay={str(N): BAY[N] for N in F.BOTS}, weights=list(WEIGHTS), join_safe=float(opt.get('join_safe', JOIN_SAFE)),
        v_plan=V_PLAN, v_slow=V_SLOW, post_wall=POST_WALL, wall_posts=len(walls), parked=[list(f) for f in parked(B)], lanes=lanes_out, ways=ways_drawn, bots=collections.OrderedDict((str(N), bots[N]) for N in F.BOTS))
    return st


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
        if st.get('lanes'):
            return self.lane_nodes(M, tops)
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

    def lane_nodes(self, M, tops):
        """THE STREET IN LANES (lanes_plan): every bot's program as nodes. A step = stock F07 Squad#02
        020_DefendBehaviour_rout_merc_fight_left with its Pos boxes (the route form: field 1 = the places, the last
        the place the bot defends), eDMS_NotSet - no sprint anywhere, as on the tower's way out; a timer = F07's
        Timer_start_bots {seconds, 0.0, -1.0, 0, [next]}; the deal = F07 Squad#02 060_RandomTrigger_BeforeStreet
        {0: 1, weights, one target list a weight}, the node kl_fa_bots_dyn clones for its forks."""
        st, Sx, L = self.st, 'F07', self.st['lanes']
        unit0 = M.unit                                  # (a RandomTrigger's weights are 16-bit fields: as kl_fa_bots_dyn.Maker)
        M.unit = lambda old, v: [(0x08, struct.pack('<H', v))] if old[0][0] == 0x08 else unit0(old, v)
        try:
            for b, N in enumerate(F.BOTS):
                top = tops[b]
                if top.name != F.SQUAD + 'Squad#0%d' % N:
                    raise ValueError('kl_fa_bots.make: squad %d is %s' % (N, top.name))
                path = lambda nm, N=N: SQ(N, '\\' + nm)
                have = {k.name.lower() for k in top.kids}

                def emit(items, after, top=top, path=path, have=have):
                    for i, it in enumerate(items):
                        nxt = [path(items[i + 1]['name'])] if i + 1 < len(items) else list(after)
                        if it['name'].lower() in have:
                            raise ValueError('%s: two nodes named %s' % (top.name, it['name']))
                        have.add(it['name'].lower())
                        if it['kind'] == 'step':
                            g = top.add(M.clone(Sx, SQ(2, '\\020_DefendBehaviour_rout_merc_fight_left'), it['name']))
                            M.place(g, (0.0, 0.0, 0.0))
                            refs = []
                            for j, pl in enumerate(it['places']):
                                box = g.add(M.clone(Sx, SQ(2, '\\020_DefendBehaviour_rout_merc_fight_left\\Pos#01'), 'Pos#%02d' % (j + 1)))
                                M.place(box, pl)
                                refs.append(path('%s\\Pos#%02d' % (it['name'], j + 1)))
                            if not 1 <= len(refs) <= F.STEP_MAX:
                                raise ValueError('%s: step %s has %d places' % (top.name, it['name'], len(refs)))
                            M.set(g, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: nxt, 8: 1, 9: 0})
                        elif it['kind'] == 'timer':
                            w = top.add(M.clone(Sx, R_ + F.SQUAD + 'Timer_start_bots', it['name']))
                            M.place(w, (0.0, 0.0, 0.0))
                            M.set(w, 'TriggerDelay2', {0: float(it['seconds']), 1: 0.0, 2: -1.0, 3: 0, 4: nxt})
                        elif it['kind'] == 'fork':
                            ways = it['ways']
                            if not 2 <= len(ways) <= 4 or any(not w['items'] for w in ways) or not nxt:
                                raise ValueError('%s: fork %s: %d ways' % (top.name, it['name'], len(ways)))
                            r = top.add(M.clone(Sx, SQ(2, '\\060_RandomTrigger_BeforeStreet'), it['name']))
                            M.place(r, (0.0, 0.0, 0.0))
                            wt = [int(ways[j]['weight']) if j < len(ways) else 0 for j in range(4)]
                            lists = [[path(ways[j]['items'][0]['name'])] if j < len(ways) else [] for j in range(4)]
                            M.set(r, 'RandomTrigger', {0: 1, 1: wt[0], 2: wt[1], 3: wt[2], 4: wt[3], 5: lists[0], 6: lists[1], 7: lists[2], 8: lists[3]})
                            for w in ways:
                                emit(w['items'], nxt)
                        else:
                            raise ValueError('%s: item %s of kind %s' % (top.name, it['name'], it['kind']))

                prog = L['bots'][str(N)]['program']
                emit(prog, [path(LAST)])
                g = top.add(M.clone(Sx, SQ(2, '\\100_SquadModifier_tight_defense_van'), LAST))
                M.place(g, (0.0, 0.0, 0.0))
                M.set(g, 'SquadModifierBehaviour', {0: 'eLM_Leash', 9: 'eDM_Tight', 26: []})
                self.firsts.append(path(prog[0]['name']))
        finally:
            del M.unit

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


HOPS_HEAD = """
; ---- [Hops]: written by tools\\kl_fa_bots_rt.py (option --hops, command `hops`). Read by KLHook's klmove.c and klfedkit.c,
; and only when KLHook.ini has [Bots] RestlessHop=1 (a bot that has stood RestlessHold seconds at its own hold shifts to one
; of the hop places of ITS gate instead of a random side of it) or [Fed] Hunted=1 (a bot that is hit while the human is a fed moves to
; one of them). Cover places of the tower's gates (kl_fa_bots_rt.pick_hops: the rules the holds are
; laid by - a cover box's standing ring, flat, clear of walls, in no box of a later fight, far from the men still alive -
; and a way from every hold within Max through no box of a later fight and past no post of the gate's men). Max = the most
; the hook walks a bot from its hold to a hop (100 = 1 m). Nothing in the level's nodes names these places.
"""


def write_hops(dst, gates, log=print):
    """Append (or replace) the [Hops] section of <dst>/KLJoin.ini: per gate its holds and its hop places."""
    p = os.path.join(dst, 'KLJoin.ini')
    if not os.path.isfile(p):
        raise ValueError('%s: no KLJoin.ini (the build has no join)' % dst)
    text = open(p, encoding='latin1').read().replace('\r\n', '\n')
    m = re.search(r'^\[Hops\][ \t]*$', text, re.M)        # (the section's own line: the comment above it says '[Hops]' too)
    if m:
        head, rest = text[:m.start()], text[m.end():]
        mm = re.search(r'^\[', rest, re.M)
        tail = rest[mm.start():] if mm else ''
        if '; ---- [Hops]' in head:
            head = head[:head.rindex('; ---- [Hops]')]
        text = head.rstrip('\n') + '\n' + ('\n' + tail if tail else '')
    gs = [g for g in gates if g.get('hops')]
    n = sum(len(g['hops']) for g in gs)
    if not n:
        log('[Hops]: no gate has a hop place - the file is as it was')
        return 0
    lines = [HOPS_HEAD.rstrip('\n'), '[Hops]', 'Max=%d' % HOP_MAX, 'Gates=%d' % len(gs)]
    for gi, g in enumerate(gs, 1):
        lines.append('; gate %s: its holds (a bot is taken to be at this gate when its chain place is within 150 of one) and the places it may hop to' % g['name'])
        lines += ['Gate.%d.Holds=%d' % (gi, len(g['holds']))] + ['Gate.%d.Hold.%d=%g %g %g' % (gi, j, *h) for j, h in enumerate(g['holds'], 1)]
        lines += ['Gate.%d.Hops=%d' % (gi, len(g['hops']))] + ['Gate.%d.Hop.%d=%g %g %g' % (gi, j, *h) for j, h in enumerate(g['hops'], 1)]
        if g.get('progress'):
            lines.append('; gate %s: progress along the route (arc length, 100 = 1 m) of each place, same order as Hold.j / Hop.j: a hop must not be more than Slack behind the bot' % g['name'])
            lines += ['Gate.%d.HoldS.%d=%g' % (gi, j, s) for j, s in enumerate(g['progress'], 1)] + ['Gate.%d.HopS.%d=%g' % (gi, j, s) for j, s in enumerate(g['progress'], 1)]
    with open(p, 'w', encoding='latin1', newline='\r\n') as f:
        f.write(text.rstrip('\n') + '\n' + '\n'.join(lines) + '\n')
    log('written %s: [Hops] with %d places in %d gate(s)' % (p, n, len(gs)))
    return n


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
        # starts (0x4ebed0) for a bot that stands in the street. The chain of 2026-10-11 morning had one such wait a
        # bot (the loot table), a gates build has one more per gate. Not armed = not exposed: a bot that walks between
        # two holds, and one at a hold whose men are dead (its wait fires at once).
        # WHAT IT DOES TO THE BOT IS KNOWN SINCE RUNS J1 / B1_DM09 (2026-10-11 11:10 / 11:28; re/retomoto_bots_street.md
        # 1): it loses its street step and stands. B1: the two bots that stood exactly at their door holds at the join
        # (records 2 and 5) stopped in the lobby and the square within 11 s and stood 40 s, until [Bots] BoardAll raised
        # them; the four that were between two holds walked the street. J1: six of seven stopped within 16..42 s.
        # The note is said below, behind the street's own rules: a street chain that runs by the clock for JOIN_SAFE
        # (STREET_LANES) gives such a bot an order again.
        n_g = sorted({len(a) for a, _b in g_join.values()})
        n_l = sorted({len(b) for _a, b in g_join.values()})
        facts['join_waits'] = {'gates': n_g, 'loot': n_l}
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
        uneven = set()                                  # places of the timed way on a polygon between WARP and WARP_WAY
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
            places_of_step = collections.OrderedDict()
            for jn in places:
                places_of_step.setdefault(sc.parent[jn], []).append(jn)
            for jn in places:
                p = B.at(jn)
                h = nav.at(p[0], p[1], p[2], dy=15.0)
                if h is None:
                    fail('%s (street): %s at (%d, %d, %d) is not on a walkable polygon within 15 of the mesh\'s height' % (sq, name(jn), *p)); ok = False; continue
                if nav.part[h[0]] != part:
                    fail('%s (street): %s at (%d, %d, %d) is not on the jump entry\'s mesh part' % (sq, name(jn), *p)); ok = False; continue
                # (a place nobody stands at - a place of the timed way, a WAY place of a lane's step - may lie on the terrace)
                par = sc.parent[jn]
                timed_place = TIMED_TAG in sc.names[par] or (LANE_TAG in sc.names[par] and jn != places_of_step.get(par, [jn])[-1])
                if warp(nav, h[0]) > (WARP_WAY if timed_place else WARP):
                    fail('%s (street): %s stands on a polygon whose fitted height is off by %d' % (sq, name(jn), warp(nav, h[0])))
                elif warp(nav, h[0]) > WARP:
                    uneven.add(tuple(round(v) for v in p))
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
        if uneven:
            note('%d place(s) of the way out of the building (the timed way, way places of a lane\'s first steps) stand on a polygon whose fitted height is '
                 'off by %d..%d (the terrace before the door, one polygon of 8 x 13 m): places a bot walks through, nobody stands there' % (len(uneven), WARP, WARP_WAY))
        # 3b. THE STREET IN LANES (STREET_LANES; re/retomoto_bots_street.md). Read from the build's nodes, every branch set:
        #   a. THE CLOCK: behind the first street step (the EXITS_BANK place) the steps of the timed way: one place each,
        #      within ARRIVE_3D - CLOCK_MARGIN of the place before - so each is 'reached' as it starts and its timer
        #      runs while the bot walks - a timer behind each, the timers together at least JOIN_SAFE: as long as a wait
        #      of the tower chain can still fire and take a bot's street step (runs J1 / B1)
        #   b. THE DEAL: two lanes at least; every lane has a squad that always takes it (no lane is empty whatever is
        #      drawn); one lane with a hold west of the road's middle and one without (some go to the other side, some
        #      stay); a fork's ways are two different lanes with a weight each
        #      ... and BY THE WALK MODEL (walk_model) at V_SLOW no second of the timed way is without a pending timer
        #   c. HOLDS AT COVER: a lane's hold (the last place of a lane step a timer follows) is within SPOT[1] + 30 of
        #      the box of a cover box, POST_KEEP_ST from every post of the police, ARRIVE_3D from the place the bot
        #      waited at before (else its step is reached where he stands), out of the level exit box; its timer is
        #      at least ARRIVE_3D / V_SLOW + STAND_MIN (the timer starts ARRIVE_3D before the hold: under that a bot at
        #      V_SLOW is ordered on before he has stood)
        #   d. NO TWO BOTS ON ONE HOLD: two squads' holds - of any lane either may draw - are STREET_SEP apart, and the
        #      cover box a hold is NEAREST to has no more squads at it than box_room() gives it
        #   g. NO LEG AT A POLICE POST: no leg of the street chain - from its first place to the place beside the van,
        #      every branch set - comes within POST_WALL of a wall post (wall_posts(): point-blank is 160, kl2 0x8c62e0)
        #   e. A LANE'S WAY STAYS ON THE MESH: from the timed way's last place to the place beside the van every leg is
        #      a straight line on the street's mesh part, clear of the parked vehicles and of the van's lane
        #   f. no place inside the level exit box before the rally's timer, and no leg through it (the old chain's rule
        #      took the chain's FIRST wait for the rally; here the rally is found by its name)
        Gs = Ground(nav, part)
        vblocks = [f[1:] for f in parked(B)]
        vnames = [f[0] for f in parked(B)]
        cg = cover_geom(B)
        sposts = street_posts(B, e_squads)
        swalls = wall_posts(sposts)
        post_least = [1e9, None]                        # the nearest any leg comes to a wall post
        cg_of = {c['node']: c for c in cg}
        near_posts, pace_f = [], collections.OrderedDict()
        rand_v = {k: v for k, _i, v in kl_fa.controllers(sc, 'RandomTrigger') if k in mine}
        lanes_f, sq_f, all_holds = collections.OrderedDict(), collections.OrderedDict(), []
        n_lane_squads = 0
        for x in sorted(tgt, key=lambda x: sc.names[sc.top[x]]):
            sq = sc.names[sc.top[x]]
            forks[0] = 1
            sets = [items(x, 0)]
            sets += [items(x, v_) for v_ in range(1, forks[0])]
            if not any(LANE_TAG in sc.names[k] for its in sets for k, _cn, _v in its):
                continue
            n_lane_squads += 1
            f_sq = sq_f.setdefault(sq[-2:], collections.OrderedDict(lanes=[], timed_places=0, clock_seconds=0.0, holds={}, seconds={}))
            keys_of = []
            for vi, its in enumerate(sets):
                # the chain as (step name, [places]) and what follows each step
                steps = [(i, sc.names[k], [B.at(j) for s_ in v[1] for j in res(s_)] + [B.at(j) for j in (res(v[0]) if v[0] else [])])
                         for i, (k, cn, v) in enumerate(its) if cn == 'DefendBehaviourRout']
                timer_after = lambda i: (lambda nx: nx[2][0] if nx and nx[1] == 'TriggerDelay2' else None)(its[i + 1] if i + 1 < len(its) else None)
                key_of = lambda nm: nm.split(LANE_TAG)[1][:1] if LANE_TAG in nm else None
                keys = [k_ for k_ in dict.fromkeys(key_of(nm) for _i, nm, _p in steps) if k_]
                keys_of.append(keys)
                if len(keys) != 1:
                    fail('%s: branch set %d of its street chain walks %d lanes (%s): a way of the deal is one lane' % (sq, vi + 1, len(keys), ' '.join(keys) or 'none'))
                    continue
                key = keys[0]
                # a. the clock
                if vi == 0:
                    clock, prev, n_t, bad = 0.0, None, 0, False
                    for i, nm, pl in steps:
                        first, timed = i == steps[0][0], TIMED_TAG in nm
                        if not (first or timed):
                            break
                        t = timer_after(i)
                        if len(pl) != 1 or t is None:
                            fail('%s: %s of the timed way has %d places and %s behind it (wanted: one place, a timer)' % (sq, nm, len(pl), 'a timer' if t is not None else 'no timer'))
                            bad = True; break
                        if prev is not None and math.dist(pl[0], prev) > ARRIVE_3D - CLOCK_MARGIN:
                            fail('%s: %s of the timed way lies %d (3D) from the place before: over %d its step is not \'reached\' as it starts (kl2 0x686c4c: within '
                                 '%d), no timer runs while the bot walks the bound, and a bot whose street step a late wait of the tower chain has taken '
                                 'stands for good (runs J1 / B1)' % (sq, nm, math.dist(pl[0], prev), ARRIVE_3D - CLOCK_MARGIN, ARRIVE_3D))
                        clock, prev, n_t = clock + t, pl[0], n_t + timed
                    f_sq['timed_places'], f_sq['clock_seconds'] = n_t, round(clock, 1)
                    if not bad and n_t:
                        way_t = [(nm, pl, timer_after(i)) for i, nm, pl in steps if i == steps[0][0] or TIMED_TAG in nm]
                        gap = {v_: round(sum(r_['no_timer'] for r_ in walk_model(way_t, v_)[1:]), 1) for v_ in (V_PLAN, V_SLOW, 120.0, 100.0)}
                        f_sq['no_timer_by_speed'] = {str(int(v_)): g_ for v_, g_ in gap.items()}
                        if gap[V_SLOW] > 0.05:
                            fail('%s: by the walk model a bot at %d units / s is %.1f s of its timed way without a pending timer (a step that is not '
                                 '\'reached\' as it starts: the clock is faster than he walks): a wait of the tower chain that fires then takes his street '
                                 'step for good' % (sq, V_SLOW, gap[V_SLOW]))
                    if not bad and (n_t == 0 or clock < JOIN_SAFE - 0.05):
                        fail('%s: the timed way out of the building runs %.1f s on %d places: under %g s a wait of the tower chain that was armed at the join '
                             'can still fire AFTER it and take the bot\'s street step for good' % (sq, clock, n_t, JOIN_SAFE))
                # c. the holds, e. the legs, f. the level exit box
                seq = [(nm, p_, i) for i, nm, pl in steps for p_ in pl]
                i_rally = next((i for i, (k, cn, _v) in enumerate(its) if cn == 'TriggerDelay2' and 'Timer_rally' in sc.names[k]), None)
                i_lane0 = next((n for n, (nm, _p, _i) in enumerate(seq) if LANE_TAG in nm), len(seq))
                wait_at = None                          # the place the bot last waited at (a timer ran there)
                holds_n, hold_s = 0, 0.0
                for n, (nm, p_, i) in enumerate(seq):
                    if i_rally is not None and i < i_rally and F.in_exit(B, S['exits'], p_):
                        fail('%s: %s at (%d, %d, %d) is inside the level exit box BEFORE the rally: the van is called before the squad has gathered' % (sq, nm, *p_))
                    hit = [vn for vn, bx in zip(vnames, vblocks) if bx[0] - 20.0 <= p_[0] <= bx[1] + 20.0 and bx[2] - 20.0 <= p_[2] <= bx[3] + 20.0]
                    if hit:
                        fail('%s: %s at (%d, %d, %d) stands in the footprint of %s, a vehicle kl_fa_street parked on the road' % (sq, nm, *p_, hit[0]))
                    last_of_step = n + 1 == len(seq) or seq[n + 1][2] != i
                    t = timer_after(i) if last_of_step else None
                    if n >= 1:
                        gp = post_gap(swalls, seq[n - 1][1], p_)
                        if gp[0] < post_least[0]:
                            post_least = [gp[0], '%s lane %s, %s: %s %s at (%d, %d)' % (sq[-8:], key, nm, sc.names[gp[1][0]].split('!')[-1], gp[1][1], gp[1][2][0], gp[1][2][2])]
                        if gp[0] < POST_WALL - 5.0:
                            near_posts.append((gp[0], sq, key, nm))
                            fail('%s: lane %s: the leg from (%d, %d, %d) to %s at (%d, %d, %d) passes %d from a post of the police (%s, %s at (%d, %d)): '
                                 'under %d a way is at point-blank range of a man posted there (160: kl2 0x8c62e0 - 100 bullets a burst step)'
                                 % (sq, key, *seq[n - 1][1], nm, *p_, gp[0], sc.names[gp[1][0]].split('!')[-1], gp[1][1], gp[1][2][0], gp[1][2][2], POST_WALL))
                    if n >= max(1, i_lane0) and not straight_clear(Gs, vblocks, seq[n - 1][1], p_):
                        fail('%s: lane %s: the leg from (%d, %d, %d) to %s at (%d, %d, %d) is no straight line on the street\'s mesh, clear of the parked '
                             'vehicles and of the van\'s lane: where the bot walks there is not known' % (sq, key, *seq[n - 1][1], nm, *p_))
                    if LANE_TAG in nm and t is not None and 'Timer_lane' in sc.names[its[i + 1][0]]:
                        holds_n, hold_s = holds_n + 1, hold_s + t
                        d_box = min([(math.hypot(max(c['fp'][0] - p_[0], 0.0, p_[0] - c['fp'][1]), max(c['fp'][2] - p_[2], 0.0, p_[2] - c['fp'][3])), c['node'])
                                     for c in cg if abs(c['y'] - p_[1]) <= 260.0] or [(1e9, None)])
                        if d_box[0] > SPOT[1] + 30.0:
                            fail('%s: lane %s: its hold %s at (%d, %d, %d) is %d from the box of the nearest cover box (wanted within %d): it would wait '
                                 'standing in the open' % (sq, key, nm, *p_, d_box[0], SPOT[1] + 30.0))
                        d_post = min([(hdist(p_, q), sc.names[t_].split('!')[-1], w_) for t_, w_, q in sposts if abs(q[1] - p_[1]) <= 260.0] or [(1e9, '', '')])
                        if d_post[0] < POST_KEEP_ST - 20.0:
                            fail('%s: lane %s: its hold %s at (%d, %d, %d) is %d from a post of the police (%s, %s): wanted %d' % (sq, key, nm, *p_, d_post[0], d_post[1], d_post[2], POST_KEEP_ST))
                        if t < ARRIVE_3D / V_SLOW + STAND_MIN - 0.05:
                            fail('%s: lane %s: its hold %s has a timer of %g s: the timer starts %d before the hold, so under %.1f s (%d at %d units / s + '
                                 '%g s) a slow bot is ordered on before he has stood there' % (sq, key, nm, t, ARRIVE_3D, ARRIVE_3D / V_SLOW + STAND_MIN, ARRIVE_3D, V_SLOW, STAND_MIN))
                        if wait_at is not None and math.dist(p_, wait_at) < ARRIVE_3D:
                            fail('%s: lane %s: its hold %s lies %d (3D) from the place the bot waited at before: within %d the step to it is \'reached\' where he '
                                 'stands and its timer runs out before he is there' % (sq, key, nm, math.dist(p_, wait_at), ARRIVE_3D))
                        all_holds.append((sq, key, nm, p_, d_box[1]))
                        L_ = lanes_f.setdefault(key, {'always': set(), 'drawn': set(), 'holds': [], 'boxes': set()})
                        L_['holds'].append(p_); L_['boxes'].add(d_box[1])
                    if t is not None:
                        wait_at = p_
                    if its[i][2][4] == 'eDMS_Sprint' and LANE_TAG in nm:
                        note('%s: lane %s: step %s sprints (a sprinting bot was seen to run past its enemies; the old chain\'s five were dead 40..49 s after the join)' % (sq, key, nm))
                call = F.first_exit_entry(B, nav, S['exits'], [p_ for _nm, p_, _i in seq]) if S['exits'] else None
                n_before = sum(1 for _nm, _p, i in seq if i_rally is not None and i < i_rally)
                if i_rally is None:
                    fail('%s: its street chain has no 070_Timer_rally: nothing holds the squad before the level exit box' % sq)
                elif call and call[1] < n_before:
                    fail('%s: lane %s: the stand-in path is inside the level exit box on the way to place %d of the %d before the rally' % (sq, key, call[1] + 1, n_before))
                f_sq['holds'][key], f_sq['seconds'][key] = holds_n, round(hold_s, 1)
                if holds_n < LANE_MIN_HOLDS:
                    fail('%s: lane %s: %d hold(s) at cover on its whole way (wanted %d at least): it walks the street without a stop, ahead of the others, '
                         'the first bot in every wake box - run J1\'s record 5, alone on the east pavement, dead 37.7 s after the join' % (sq, key, holds_n, LANE_MIN_HOLDS))
                # the pace by the walk model (a NOTE's numbers, no rule)
                way_all = [(nm, pl, timer_after(i)) for i, nm, pl in steps]
                pr = collections.OrderedDict()
                for v_ in (V_PLAN, V_SLOW):
                    rows_ = walk_model(way_all, v_)
                    rl = [r_ for r_ in rows_ if 'DefendBehaviour_rally' in r_['name']]
                    hs_ = [r_['stood'] for r_ in rows_ if LANE_TAG in r_['name'] and r_['timer'] is not None]
                    if v_ == V_SLOW:
                        for r_ in rows_:
                            if LANE_TAG in r_['name'] and r_['timer'] is not None and r_['stood'] < STAND_MIN - 0.15:
                                fail('%s: lane %s: by the walk model a bot at %d units / s stands %.1f s at its hold %s (timer %g s, %.1f s of them the walk in '
                                     'through the step\'s way places): under %g s he is ordered on as he arrives, or before'
                                     % (sq, key, V_SLOW, r_['stood'], r_['name'], r_['timer'], r_['arrive'] - r_['reached'], STAND_MIN))
                    pr[str(int(v_))] = {'at_the_rally': round(rl[0]['arrive'], 1) if rl else None, 'stands': [round(min(hs_), 1), round(max(hs_), 1)] if hs_ else None}
                pace_f.setdefault(sq[-2:], collections.OrderedDict())[key] = pr
                lanes_f.setdefault(key, {'always': set(), 'drawn': set(), 'holds': [], 'boxes': set()})
            flat_keys = [k_ for ks in keys_of for k_ in ks]
            f_sq['lanes'] = flat_keys
            if len(sets) == 1 and flat_keys:
                lanes_f[flat_keys[0]]['always'].add(sq[-2:])
            else:
                for k_ in flat_keys:
                    lanes_f[k_]['drawn'].add(sq[-2:])
                if len(set(flat_keys)) != len(flat_keys):
                    fail('%s: the deal draws between %s: two ways into one lane are no draw' % (sq, ' '.join(flat_keys)))
            for k, v in rand_v.items():
                if sc.top[k] == sc.top[x] and 'RandomTrigger_lane' in sc.names[k]:
                    ws = [w for w, lst in zip(v[1:5], v[5:9]) if w and lst]
                    if v[0] != 1 or len(ws) != len(sets) or any(bool(w) != bool(lst) or len(lst) > 1 for w, lst in zip(v[1:5], v[5:9])):
                        fail('%s: %s: field 0 %s, weights %s for %d lanes (stock: 1; one target for every weight that is not 0)' % (sq, sc.names[k], v[0], list(v[1:5]), len(sets)))
        if not n_lane_squads:
            note('NO LANES: the street chain is one file down the east pavement for all seven (a build made with --no-lanes, or before 2026-10-11 '
                 'afternoon; runs J0 / J1 / B1_DM09)')
        else:
            if n_lane_squads != len(allies):
                fail('%d of %d squads have a street chain in lanes' % (n_lane_squads, len(allies)))
            if len(lanes_f) < 2:
                fail('the street has %d lane(s): nobody spreads' % len(lanes_f))
            for key, L_ in lanes_f.items():
                if not L_['always']:
                    fail('lane %s has no squad that always takes it (drawn by %s): in some rounds it is empty' % (key, ' '.join(sorted(L_['drawn'])) or 'nobody'))
            west = [key for key, L_ in lanes_f.items() if any(h[0] < ROAD_MID for h in L_['holds'])]
            if not west or len(west) == len(lanes_f):
                fail('%s lane has a hold west of the road\'s middle (x %d): %s' % ('no' if not west else 'every', ROAD_MID,
                                                                                  'nobody goes to the other side' if not west else 'nobody stays on this side'))
            clash = 0
            for a_ in range(len(all_holds)):
                for b_ in range(a_ + 1, len(all_holds)):
                    u, w = all_holds[a_], all_holds[b_]
                    if u[0] != w[0] and hdist(u[3], w[3]) < STREET_SEP - 10.0 and abs(u[3][1] - w[3][1]) < 150.0:
                        clash += 1
                        if clash <= 3:
                            fail('%s (lane %s, %s) and %s (lane %s, %s) hold %d apart at (%d, %d, %d): two bots on one hold (wanted %d)'
                                 % (u[0][-8:], u[1], u[2], w[0][-8:], w[1], w[2], hdist(u[3], w[3]), *u[3], STREET_SEP))
            by_box = collections.defaultdict(set)
            for sq_, key_, nm_, p_, node_ in all_holds:
                if node_ is not None:
                    by_box[node_].add(sq_)
            for node_, sqs in sorted(by_box.items()):
                if len(sqs) > box_room(cg_of[node_]):
                    c_ = cg_of[node_]
                    fail('cover box %s (%d x %d at (%d, %d)) is the nearest box of holds of %d squads (%s): a box of that length takes %d (two bots at one '
                         'small box: one of them stands on its open side)' % (sc.names[node_], c_['fp'][1] - c_['fp'][0], c_['fp'][3] - c_['fp'][2], c_['mid'][0], c_['mid'][2],
                                                                           len(sqs), ' '.join(sorted(x[-8:] for x in sqs)), box_room(c_)))
            facts['lane_pace'] = pace_f
            facts['nearest_leg_to_a_post'] = [round(post_least[0]), post_least[1]]
            note('NO LEG AT A POLICE POST: the nearest any leg of the street chain (every branch set, straight lines between its places) comes to one of the %d '
                 'posts of the police - start places, places their behaviours name, RunToCover points - is %d (%s); the rule is %d, point-blank is 160. What the '
                 'game\'s pathfinder makes of a leg is not this straight line (it lays its own path on the mesh)' % (len(swalls), post_least[0], post_least[1], POST_WALL))
            facts['wall_posts'] = len(swalls)
            rs = [pr_[str(int(V_PLAN))]['at_the_rally'] for d_ in pace_f.values() for pr_ in d_.values() if pr_[str(int(V_PLAN))]['at_the_rally'] is not None]
            rs2 = [pr_[str(int(V_SLOW))]['at_the_rally'] for d_ in pace_f.values() for pr_ in d_.values() if pr_[str(int(V_SLOW))]['at_the_rally'] is not None]
            if rs and rs2:
                note('THE PACE by the walk model (a step is \'reached\' %d before its place, a hold\'s timer starts then; NOT SEEN IN THE GAME): the bots are at the '
                     'rally %d..%d s after their first street step at %d units / s, %d..%d s at %d; a human who is at the van before that leaves them to the '
                     'hook ([Bots] FollowOut calls them when HE has stage 3; FollowOutHold lets the van wait for them)'
                     % (ARRIVE_3D, min(rs), max(rs), V_PLAN, min(rs2), max(rs2), V_SLOW))
            facts['lanes'] = collections.OrderedDict(
                (key, collections.OrderedDict(always=sorted(L_['always']), drawn=sorted(L_['drawn']), holds=len(L_['holds']), cover_boxes=len(L_['boxes'] - {None}),
                                              x=[round(min(h[0] for h in L_['holds'])), round(max(h[0] for h in L_['holds']))] if L_['holds'] else None,
                                              z=[round(min(h[2] for h in L_['holds'])), round(max(h[2] for h in L_['holds']))] if L_['holds'] else None))
                for key, L_ in lanes_f.items())
            facts['lane_squads'] = sq_f
            facts['parked_vehicles'] = vnames
            # the first step against where the hook puts the bots: reached at once only within ARRIVE_3D
            e0s = {sq_: B.at([j for s_ in ctrl_of[x_][1][1] for j in res(s_)][0]) for x_ in tgt for sq_ in [sc.names[sc.top[x_]]]}
            ds = [math.dist(a_, e_) for a_ in arr for e_ in e0s.values()]
            facts['crew_place_to_first_place'] = [round(min(ds)), round(max(ds))] if ds else None
            if ds and max(ds) > ARRIVE_3D:
                note('the first street step\'s place (in the EXITS_BANK box, on a ramp of the lobby) is %d..%d (3D) from the [CrewJoin] places: over %d a bot '
                     'the hook puts on the far side of the lift landing has to walk up to %d before that step is \'reached\' and the clock starts'
                     % (min(ds), max(ds), ARRIVE_3D, max(ds) - ARRIVE_3D))
        clock = min([f_['clock_seconds'] for f_ in sq_f.values()] or [0.0])
        if n_g and (n_g[-1] or n_l[-1]):
            note('THE JOIN: every bot has %s gate wait(s) and %s loot wait(s) in its tower chain. One that is armed when the human takes the join fires '
                 'up to 30 s later and starts the next TOWER step for a bot the hook has moved to the street: that bot LOSES ITS STREET STEP (runs '
                 'J1 / B1_DM09: the bots that stood at a gate with living men at the join stopped ADVANCING within 11..26 s - they move about where they are, none goes on). %s'
                 % ('..'.join(str(x) for x in n_g), '..'.join(str(x) for x in n_l),
                    'This build\'s street chain runs by the clock for its first %.1f s (a timer is pending while the bot walks; no wait can be armed after '
                    'the join, so none fires later than %g s after it): the next timer orders such a bot on. NOT SEEN IN THE GAME' % (clock, JOIN_SAFE - 1.0)
                    if n_lane_squads and clock >= JOIN_SAFE - 0.05 else
                    'This build\'s street chain goes on only when the bot ARRIVES somewhere: nothing orders such a bot again but the hook ([Bots] '
                    'BoardAll once the van waits, FollowOut once the human has stage 3)'))
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
    for key, f_ in facts.get('lanes', {}).items():
        log('  lane %s: always %s, drawn by %s; %d holds at %d cover boxes, x %s, z %s' % (
            key, ' '.join('#' + x for x in f_['always']) or '-', ' '.join('#' + x for x in f_['drawn']) or '-', f_['holds'], f_['cover_boxes'], f_['x'], f_['z']))
    for nm, f_ in facts.get('lane_squads', {}).items():
        log('  Squad#%s lanes %s: the timed way %d places, %.1f s on the clock, seconds of it without a pending timer by walking speed %s; holds %s, seconds of their timers %s; '
            'by the walk model %s' % (nm, ' / '.join(f_['lanes']), f_['timed_places'], f_['clock_seconds'], f_.get('no_timer_by_speed'), dict(f_['holds']), dict(f_['seconds']),
                                      '; '.join('%s at the rally %s s at %d (stands %s), %s s at %d (stands %s)' % (
                                          k_, pr_[str(int(V_PLAN))]['at_the_rally'], V_PLAN, pr_[str(int(V_PLAN))]['stands'], pr_[str(int(V_SLOW))]['at_the_rally'], V_SLOW,
                                          pr_[str(int(V_SLOW))]['stands']) for k_, pr_ in facts.get('lane_pace', {}).get(nm, {}).items())))
    log('RESULT (kl_fa_bots_rt): %s (%d FAIL, %d NOTE); start delay %s s after a blast at %s s; %d gate(s) on the tower\'s way out; %s; jump list %d; [CrewJoin] places %d'
        % ('PASS' if not any(s == 'FAIL' for s, _t in out) else 'FAIL', sum(s == 'FAIL' for s, _t in out), sum(s == 'NOTE' for s, _t in out),
           delay, blast, len(facts.get('gates', {})), '%d lane(s) on the street' % len(facts['lanes']) if facts.get('lanes') else 'no lanes on the street',
           len(lst), len(facts.get('crew_places', []))))
    return out, facts


def lanes_of(folder):
    """The street chain of a built folder, read from its nodes -> {squad name: [{'lane': key or None, 'steps': [(step
    name, [place], seconds of the timer behind it or None)]}]} - one entry a branch set (a squad without a draw: one)."""
    B = F.Built(folder)
    sc, res = B.sc, B.sc.resolve
    NEXT = {'DefendBehaviourRout': 7, 'SquadModifierBehaviour': 26, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerActorsDead': 2}
    mine = {k for t in sc.tops() if sc.names[t].startswith(F.SQUAD) for k in range(t, sc.end[t])}
    ctrl_of = {k: (cn, v) for cn in NEXT for k, _i, v in kl_fa.controllers(sc, cn) if k in mine}
    rand_of = F.fork_branches(sc, mine)
    jp = res(R_ + JOIN_NAME)
    lst = [v for k, _i, v in kl_fa.controllers(sc, 'JumpPoint') if jp and k == jp[0]]
    out = collections.OrderedDict()
    for x in sorted([j for s in (lst[0][0] if lst else []) for j in res(s)], key=lambda x: sc.names[sc.top[x]]):
        sets, variant, widest = [], 0, 1
        while variant < widest:
            k, seen, steps = x, set(), []
            while k is not None and k not in seen:
                seen.add(k)
                if k in rand_of and k not in ctrl_of:
                    widest = max(widest, len(rand_of[k]))
                    k = rand_of[k][variant % len(rand_of[k])] if rand_of[k] else None
                    continue
                if k not in ctrl_of:
                    break
                cn, v = ctrl_of[k]
                if cn == 'DefendBehaviourRout':
                    steps.append([sc.names[k], [[round(c, 1) for c in B.at(j)] for s in ([v[0]] if v[0] else []) + list(v[1]) for j in res(s)], None])
                elif cn == 'TriggerDelay2' and steps:
                    steps[-1][2] = v[0]
                nx = [j for s in v[NEXT[cn]] for j in res(s)]
                nx = [j for j in nx if j in ctrl_of] or [j for j in nx if j in rand_of]
                k = nx[0] if nx else None
            keys = [nm.split(LANE_TAG)[1][:1] for nm, _p, _t in steps if LANE_TAG in nm]
            sets.append({'lane': keys[0] if keys else None, 'steps': steps})
            variant += 1
        out[sc.names[sc.top[x]]] = sets
    return out


# ------------------------------------------------------------------ build
def plan(B, opt=None, log=print):
    opt = dict(DEFAULTS, **(opt or {}))
    nav, S, P = tower_plan(B, opt, log)
    st = None
    if not opt['tower_only']:
        st = street_plan(B, nav, S, opt, log)
        if opt.get('lanes'):
            st = lanes_plan(B, nav, S, st, opt, log)
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
    if opt.get('hops'):
        write_hops(dst, gates, say)
    out, facts = F.check(dst, say)
    out2, facts2 = check(dst, say)
    rep.update(plan=P, check=[list(x) for x in out], facts=facts, check_rt=[list(x) for x in out2], facts_rt=facts2)
    with open(os.path.join(dst, 'bots.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    with open(os.path.join(dst, 'bots.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return out + out2, rep


def street_hops(folder, dedup=60.0):
    """THE STREET HALF (2026-10-12): hop places for the lobby and the street, from the finished build's own plan (bots.json, plan.rt.street.lanes):
    the place each step of every bot's program ends at (the place the bot defends: the lanes' holds at cover boxes, the timed way's
    stations, the rally, the stop), every way of every fork, places less than `dedup` apart kept once. They were laid by the lanes'
    rules (clear of the parked vehicles, POST_WALL from a wall post of the police, POST_KEEP_ST from a post, on the mesh part of the
    street). ONE group: its holds and its hops are the same list - a bot that stands at one of them may shift to another within the
    hook's Max (18 m) and on its floor. ASSUMED: walkable between them (the stations of one lane are 5 .. 24 m apart; across the
    road the way is not checked). -> a gate dict {'name', 'holds', 'hops'} or None."""
    bj = os.path.join(folder, 'bots.json')
    if not os.path.isfile(bj):
        return None
    lanes = (((json.load(open(bj)).get('plan') or {}).get('rt') or {}).get('street') or {}).get('lanes') or {}
    pts = []

    def walk(items):
        for it in items:
            if it['kind'] == 'step' and it.get('places'):
                pts.append(tuple(it['places'][-1]))
            elif it['kind'] == 'fork':
                for w in it['ways']:
                    walk(w['items'])
    for b in (lanes.get('bots') or {}).values():
        walk(b.get('program') or [])
    out = []
    for q in pts:
        if all(math.hypot(q[0] - o[0], q[2] - o[2]) >= dedup or abs(q[1] - o[1]) > 200 for o in out):
            out.append(q)
    if not out:
        return None
    pl = [[round(v, 1) for v in q[:3]] for q in out]
    # PROGRESS (2026-10-12, round 3): a hop must never undo progress (the owner's log: 'record 2 hops ... to (4280, 160, -6440)' from
    # (2797, 131, -6286) = 15 m back towards the doors). The programme's step order IS the route: take bot 2's programme (first way of every fork)
    # as the reference line and give every place the ARC LENGTH of its nearest point on that line. A bot then hops only to a place whose
    # progress is at least its own less PROG_SLACK ('level with it across the lane'). The line is the lobby -> street way of one bot; the other
    # bots' lanes run beside it (same direction), so the projection orders them the same way.
    ref = []

    def first_way(items):
        for it in items:
            if it['kind'] == 'step' and it.get('places'):
                ref.append(tuple(it['places'][-1]))
            elif it['kind'] == 'fork':
                first_way(it['ways'][0]['items'])
    prog = (lanes.get('bots') or {}).get('2') or next(iter((lanes.get('bots') or {}).values()))
    first_way(prog.get('program') or [])
    cum = [0.0]
    for a_, b_ in zip(ref, ref[1:]):
        cum.append(cum[-1] + math.dist(a_, b_))

    def progress(q):
        best, bs = 1e18, 0.0
        for k in range(len(ref) - 1):
            a_, b_ = ref[k], ref[k + 1]
            dx, dz = b_[0] - a_[0], b_[2] - a_[2]
            L2 = dx * dx + dz * dz
            u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - a_[0]) * dx + (q[2] - a_[2]) * dz) / L2))
            d = math.hypot(q[0] - (a_[0] + u * dx), q[2] - (a_[2] + u * dz))
            if d < best:
                best, bs = d, cum[k] + u * math.sqrt(L2)
        return round(bs, 1)
    sp = [progress(q) for q in out]
    return collections.OrderedDict(name='street', holds=pl, hops=pl, places_refused={}, progress=sp)


LOBBY_START = {2: 0.5, 3: 0.5, 4: 1.0, 5: 1.0, 6: 1.5, 8: 1.5, 7: 2.0}     # seconds at the doors before a bot's first bound (was 0.5 / 3.5 / 1.5 / 4.5 / 2.5 / 5.5 / 2.0)


def lobby_fix(src, dst, log=print):
    """`lobby <finished build> <new folder>` (2026-10-12, owner: 'no cover inside they go to they just stand there they dont even rush out the
    door straight away'). The seven stand at the EXITS_BANK place just inside the glass doors until their own '050_Timer_out_start' has run (the
    lane stagger: 0.5 / 3.5 / 1.5 / 4.5 / 2.5 / 5.5 / 2.0 s, armed when the step is reached within ARRIVE_3D = 10 m, so on top of the walk from the
    lift landing) - in a row, in the open. This step shortens the seven timers to LOBBY_START (0.5 .. 2.0 s, the order of the lanes: the south ramp
    and the north ramp interleaved) and nothing else: the .prp member alone (same method as kl_fa_bots_dyn.fake_fix: kl_prpjoin.join, one field of
    seven nodes, round-trip proven); bots.json / steps.json follow. The places are not touched (the exit place, the lanes).
    THE CLOCK STAYS: the timed way must run JOIN_SAFE (31) s or more (check(): a tower wait armed at the join can still fire up to 31 s later and
    take the bot's street step), and the stagger was part of it. What a bot no longer stands at the doors is therefore put on the
    '051_Timer_out_NN' timers of its own timed way, share and share alike (a stand of 0.1 .. 0.6 s more at each of its 6 .. 8 stations,
    which lie at cover boxes / on the way out): the total is the same to the tenth of a second. -> report dict."""
    import shutil
    import kl_prpjoin as J
    import kl_graft
    B = F.Built(src)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    if os.path.isdir(dst) and os.listdir(dst):
        raise ValueError('%s is there and not empty' % dst)
    Jn = J.join(sc, [(sc, t_) for t_ in sc.tops()], 'lobby')
    if J.fingerprints(Jn)[0] != J.fingerprints(sc)[0] or J.text(Jn, Jn.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    done, add_out = {}, {}
    for N in F.BOTS:
        hit = Jn.resolve(SQ(N, '\\050_Timer_out_start'))
        if len(hit) != 1:
            raise ValueError('squad %d: %d nodes named 050_Timer_out_start' % (N, len(hit)))
        k = hit[0]
        i = next(i for i, (nm, _b) in enumerate(Jn.nodes[k]['ctrls']) if Jn.p.key(nm) == 'TriggerDelay2')
        was = []

        def fn(us, N=N, was=was):
            if us[0][0][0] != 0x0a or len(us[0]) != 1:
                raise ValueError('TriggerDelay2 field 0 is not one float')
            was.append(struct.unpack('<f', us[0][0][1])[0])
            us[0] = [(0x0a, struct.pack('<f', float(LOBBY_START[N])))]
        kl_fa.edit(Jn, k, i, fn)
        delta = was[0] - LOBBY_START[N]
        outs = sorted(n_ for n_ in range(1, 20) if len(Jn.resolve(SQ(N, '\\051_Timer_out_%02d' % n_))) == 1)
        share = delta / len(outs) if outs else 0.0
        for n_ in outs:
            k2 = Jn.resolve(SQ(N, '\\051_Timer_out_%02d' % n_))[0]
            i2 = next(i2 for i2, (nm, _b) in enumerate(Jn.nodes[k2]['ctrls']) if Jn.p.key(nm) == 'TriggerDelay2')
            old2 = []

            def fn2(us, old2=old2, share=share):
                old2.append(struct.unpack('<f', us[0][0][1])[0])
                us[0] = [(0x0a, struct.pack('<f', old2[0] + share))]
            kl_fa.edit(Jn, k2, i2, fn2)
            add_out.setdefault(N, {})['051_Timer_out_%02d' % n_] = old2[0] + share
        done[N] = (round(was[0], 2), LOBBY_START[N])
        log('squad %d: 050_Timer_out_start %.1f s -> %.1f s, the %.2f s put on its %d out timers (+%.2f s each)' % (N, was[0], LOBBY_START[N], delta, len(outs), share))
    prp = Jn.p.serialize()
    back = F.Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    new = dict(B.files)
    new[B.ext['.prp']] = prp
    os.makedirs(dst, exist_ok=True)
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        pth = os.path.join(B.folder, f)
        if os.path.isfile(pth) and pth != B.zp and not f.startswith('audit.'):
            shutil.copyfile(pth, os.path.join(dst, f))
    before, after = F.sizes(B.folder), F.sizes(dst)
    bj = os.path.join(dst, 'bots.json')
    if os.path.isfile(bj):
        d = json.load(open(bj))
        L = (((d.get('plan') or {}).get('rt') or {}).get('street') or {}).get('lanes') or {}
        for N, b in (L.get('bots') or {}).items():
            b['start_seconds'] = LOBBY_START[int(N)]
            for it in b.get('program') or []:
                if it.get('name') == '050_Timer_out_start':
                    it['seconds'] = LOBBY_START[int(N)]
                elif it.get('name') in add_out.get(int(N), {}):
                    it['seconds'] = round(add_out[int(N)][it['name']], 4)
        with open(bj, 'w') as f:
            json.dump(d, f, indent=1, default=str)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['bots'] = sorted(set(st.get('bots') or []) | {'.prp'})
        st['same'] = [e for e in st.get('same', []) if e != '.prp']
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_bots_rt lobby: the seven 050_Timer_out_start shortened to %s s (was %s); the .prp member alone, nothing else of %s changed\n'
                % (sorted(LOBBY_START.items()), sorted((n, w) for n, (w, _v) in done.items()), B.folder))
    log('written %s: the .prp member %d -> %d bytes; the large blocks %s' % (zp, len(B['.prp']), len(prp), 'unchanged' if before == after else 'CHANGED %s -> %s' % (before, after)))
    if before != after:
        raise ValueError('a large block changed its size')
    return done


SPREAD_R = (500.0, 1400.0)      # v82: the arrival places lie in a fan this far from the jump entry (the old 7 stood in ONE 6 m line, 4 m west of the landing)
SPREAD_SEP = 220.0              # at least this far apart (check() wants 80; the game's own crew jump uses 100)


def spread_command(folder, opt=None, log=print):
    """`spread <finished build folder>` (2026-10-17): the [CrewJoin] places of the build's KLJoin.ini laid in a FAN (7 targets at angles -90..+90 degrees
    round the jump entry's facing, radius alternating SPREAD_R) instead of the old line, each snapped to the nearest flat polygon of the street part with
    mesh clearance; the ini's other [CrewJoin] keys (Near, Radius, ...) stay. The archive is not touched. -> the places."""
    B = F.Built(folder)
    nav = F.Nav(B.scene.nav)
    jp, jpos, face = join_point(B)
    hit = nav.at(jpos[0], jpos[1], jpos[2], lo=jpos[1] - 300.0, hi=jpos[1] + 100.0)
    part = nav.part[hit[0]]
    cands = [q for q in nav.around((jpos[0], hit[1], jpos[2], hit[0]), SPREAD_R[1] + 100.0, part, dy=60.0)
             if flat(nav, q) and SPREAD_R[0] - 100.0 <= hdist(q, jpos) and nav.clearance(q[0], q[1], q[2]) >= F.CLEAR_MIN]
    out = []
    for k in range(7):
        ang = math.radians(-90.0 + 30.0 * k)
        r = SPREAD_R[0] + (SPREAD_R[1] - SPREAD_R[0]) * (0.35 if k % 2 else 0.8)
        fx, fz = face
        dx, dz = fx * math.cos(ang) - fz * math.sin(ang), fx * math.sin(ang) + fz * math.cos(ang)
        t = (jpos[0] + dx * r, hit[1], jpos[2] + dz * r)
        best = None
        for q in cands:
            if any(math.hypot(q[0] - o[0], q[2] - o[2]) < SPREAD_SEP for o in out):
                continue
            d = math.hypot(q[0] - t[0], q[2] - t[2]) - 0.5 * min(nav.clearance(q[0], q[1], q[2]), 200.0)
            if best is None or d < best[0]:
                best = (d, q)
        if best is None:
            raise ValueError('no fan place for target %d' % k)
        out.append(best[1])
    p = os.path.join(folder, 'KLJoin.ini')
    text = open(p, encoding='latin1', newline='').read().replace('\r\n', '\n')
    a = text.index('[CrewJoin]')
    head, tail = text[:a], text[a:]
    tail = re.sub(r'^Place\.\d+=.*\n', '', tail, flags=re.M)
    block = 'Places=7\n' + ''.join('Place.%d=%g %g %g\n' % (n + 1, q[0], q[1], q[2]) for n, q in enumerate(out))
    tail = re.sub(r'^Places=.*\n', lambda m: block, tail, count=1, flags=re.M)
    with open(p, 'w', encoding='latin1', newline='\r\n') as f:
        f.write(head + tail)
    for i, q in enumerate(out):
        log('  fan place %d: (%g, %g, %g)  %d from the entry' % (i + 1, q[0], q[1], q[2], hdist(q, jpos)))
    return out


def hops_command(src, final, opt):
    """`hops <the bots build's SOURCE folder> <a finished build's folder> [--hops N]`: the gates' hop places (pick_hops) planned on the
    source build (the tower half only: the same plan, the same holds - they are compared with the finished build's bots.json) and
    written into the finished build's KLJoin.ini as [Hops]. The archive is not touched. Exit 1 when the holds differ."""
    opt = dict(DEFAULTS, **(opt or {}))
    if not opt.get('hops'):
        opt['hops'] = 6
    B = F.Built(src)
    _nav, _S, P = tower_plan(B, opt)
    gates = P['rt']['gates']
    bj = os.path.join(final, 'bots.json')
    bad = []
    if os.path.isfile(bj):
        was = {g['name']: g['holds'] for g in ((json.load(open(bj)).get('plan') or {}).get('rt') or {}).get('gates') or []}
        for g in gates:
            if was.get(g['name']) != g['holds']:
                bad.append(g['name'])
        print('holds against %s: %s' % (bj, 'THE SAME in all %d gates' % len(gates) if not bad else 'DIFFER in %s' % ', '.join(bad)))
    if opt.get('street', True):
        sg = street_hops(final)
        if sg:
            gates = list(gates) + [sg]
            print('street: %d place(s) that are holds and hops at once' % len(sg['holds']))
    n = write_hops(final, gates)
    for g in gates:
        print('  gate %-9s %d hop(s): %s   [places %s, hop ways refused %s]' % (g['name'], len(g['hops']), ' '.join('(%d,%d)' % (h[0], h[2]) for h in g['hops']),
                                                                         g['places_refused'].get('places'), g['places_refused'].get('hop refused: a way from a hold', 0)))
    print('%d hop place(s) in all' % n)
    sys.exit(1 if bad or not n else 0)


def standing_command(folder):
    """`standing <finished build>`: how long the chain PLANS to make each bot stand, from the build's bots.json. A WAIT is a place where
    the chain gives no order for a while: the room (until the boardroom's squads are dead, at most room_wait after the blast), the
    loot wait, every gate's TriggerActorsDead (at most WAIT_S, the game's own limit), the street's holds (stand per hold by lane:
    LANE_STAND + the timed way's pause) and the rally (street_hold). UPPER BOUNDS - a wait that its men's deaths end early is shorter
    (the owner's round 14:10 Retomoto: gates 150 s in all). Also the longest single wait: that is what a player sees as 'always
    stands still'."""
    d = json.load(open(os.path.join(folder, 'bots.json')))
    rt = d['plan']['rt']
    opt = rt['options']
    gates = rt['gates']
    tower = {'room (window, until the 3 room squads are dead)': float(opt['room_wait']) + float(opt['after_blast']), 'loot wait (table)': float(opt['loot_seconds'])}
    for g in gates:
        tower['gate ' + g['name']] = float(g['seconds'])
    st = rt.get('street') or {}
    lanes = st.get('lanes') or {}
    street = collections.OrderedDict()
    for N, b in sorted((lanes.get('bots') or {}).items()):
        holds, timed = 0.0, 0.0
        def walk(items, lane=None):
            nonlocal holds, timed
            for it in items:
                if it['kind'] == 'timer':
                    nm = it['name']
                    if '_Timer_lane_' in nm:
                        holds += LANE_STAND.get(nm.split('_Timer_lane_')[1][0], 1.5)
                    elif '_Timer_out_' in nm:
                        timed += CLOCK_PAUSE
                elif it['kind'] == 'fork':
                    ways = it['ways']
                    # a fork is one way a round: take the mean of its ways
                    sub = []
                    for w in ways:
                        h0, t0 = holds, timed
                        walk(w['items'])
                        sub.append((holds - h0, timed - t0))
                        holds, timed = h0, t0
                    holds += sum(s[0] for s in sub) / len(sub)
                    timed += sum(s[1] for s in sub) / len(sub)
        walk(b.get('program') or [])
        street[N] = holds + timed + float(opt['street_hold'])
    t_sum = sum(tower.values())
    print('PLANNED STANDING (upper bounds, seconds a bot may be held by its chain; %s)' % folder)
    for k, v in tower.items():
        print('  tower  %-52s %5.1f' % (k, v))
    print('  tower  total                                                %5.1f   longest single wait %.0f s' % (t_sum, max(tower.values())))
    if street:
        v = sorted(street.values())
        print('  street per bot (lane holds + timed pauses + the rally %.0f s): %s  mean %.1f' % (float(opt['street_hold']), ' '.join('%.1f' % x for x in v), sum(v) / len(v)))
    print('  whole round: %.0f s planned standing per bot (tower %.0f + street %.0f)' % (t_sum + (sum(street.values()) / len(street) if street else 0.0), t_sum,
                                                                                 sum(street.values()) / len(street) if street else 0.0))
    return t_sum, tower, street


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
    if '--no-lanes' in a:
        a.remove('--no-lanes'); opt['lanes'] = False
    for flag, key, conv in (('--hops', 'hops', int), ('--loot-seconds', 'loot_seconds', int), ('--after-blast', 'after_blast', float), ('--street-hold', 'street_hold', float),
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
    elif len(a) == 3 and a[0] == 'lobby':
        lobby_fix(a[1], a[2])
    elif len(a) == 2 and a[0] == 'spread':
        spread_command(a[1])
    elif len(a) == 3 and a[0] == 'hops':
        hops_command(a[1], a[2], opt)
    elif len(a) == 2 and a[0] == 'standing':
        standing_command(a[1])
    elif len(a) == 3 and a[0] == 'lanes':
        got = lanes_of(a[1])
        with open(a[2], 'w') as f:
            json.dump(got, f, indent=1)
        for sq, sets in got.items():
            for st_ in sets:
                holds = [(p[-1], t) for nm, p, t in st_['steps'] if LANE_TAG in nm and t is not None]
                print('%s lane %s: %d steps, %d places; holds at %s' % (sq[-8:], st_['lane'], len(st_['steps']), sum(len(p) for _n, p, _t in st_['steps']),
                                                                         ' '.join('(%d, %d) %gs' % (p[0], p[2], t) for p, t in holds) or '-'))
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    main()
