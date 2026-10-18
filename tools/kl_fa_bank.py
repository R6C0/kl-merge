#!/usr/bin/env python3
"""
The Fragile Alliance layer of THE VAULT: the bank the campaign way (Dead Men M03_A, chapter 3 'Withdrawal',
alone, under Dog Days F07) - a second bank map beside the Fragile Alliance bank M03_FA_A. Authored from stock
objects, offline, on the pattern of kl_fa_author.py (Retomoto Tower). The study: re/campaign_fa.md 4.1,
re/campaign_fa_bank.md 4.3 / 8.3 / 8.4; the build stage by stage, every check with its output and the list of
what only a live run can settle: re/bank_campaign.md. Nothing here installs anything or starts the game.

    python kl_fa_bank.py test <out> [--keep] [options]    build F07 + M03_A with the layer into <out> (build(): the
                                                          van's plan on a bare graft, then kl_maps.one inside
                                                          kl_map_escape.van_layer), finish() on the written level,
                                                          check(); exit 1 if a problem is left that is not in KNOWN
    python kl_fa_bank.py finish <built folder>            what needs the WRITTEN level, on a folder build() made: the
                                                          vault loot's briefcases, the level's own texts
    python kl_fa_bank.py check <built folder>             every check of this layer on a built folder
    python kl_fa_bank.py inventory <built folder>         the layer with world places read back from the level
    python kl_fa_bank.py bots <finished folder> <out>     the seven AI heisters into a copy (kl_fa_bots.build with
                                                          BOT_OPT and the vault gate: bots_gate), then bots-check
    python kl_fa_bank.py bots-check <folder>              the gate and the vault's loot window on a folder with the
                                                          squad, before or after kl_fa_bots_dyn's step
    python kl_fa_bank.py seal <folder>                    in place, the LAST step of the finishing chain: room list
                                                          entries that name an entity outside the map (the bots'
                                                          squad group took the id the graft parked them on) go to
                                                          the scene's free REF id
    python kl_fa_bank.py reverify <folder>                kl_graft.verify's cross-reference tests on the level as
                                                          WRITTEN (check does it too): exit 1 on a problem
    python kl_fa_bank.py hall-dash <folder>               in place, AFTER kl_fa_bots_dyn's step and before seal: the AI
                                                          heisters cross the banking hall in one go (sprint, no cover
                                                          hold between the foyer and the front entrance: DASH_BOX);
                                                          only the .prp member changes
    python kl_fa_bank.py crew-check <folder>              a folder with the squad: no place of an AI heister within
                                                          CREW_CLEAR of a man, cover point, flank point or defend
                                                          place of a hall / plaza squad; exit 1 on a FAIL
    options of 'test' (one flag each for the live runs):
      --doors-animate   the eleven door leaves of the route stay where the level has them and get 'Activate' at
                        the round start (default: they are OPEN AT BUILD TIME - sunk, their collision cut)
      --vault-open      the vault door is sunk at build time too (a first load in which no door can stop anybody)
      --door-early      hall police + hunt at the beat's end (old order); default: when the door's swing is over (DOOR_GONE)
      vault-blow <folder>  (a post-step, not a flag of test) the vault door is not swung but blown away WHOLE with the blast: group + body + hinge piece
                        deactivated (VAULT_BLOW's note), switched back on by the round reset. Default builds are unchanged.
      --vault-stays     the vault door is not switched off after its swing (default: it goes away DOOR_GONE s later)
      --vault-swing [S] the vault door's swing is played out: its body is switched off S s (default VAULT_SWING_END = 9, the
                        clip ends at 8) after the beat's end by a timer of its own (SWING_TIMER), not by the door timer, which
                        keeps its DOOR_GONE s and its blast / police / gate sum. Not with --vault-stays / --vault-open
                        With --reset, round 2 also starts with the door closed again (door 'Activate' then 'ForceStopAnim', GUESS)
      --vault-blocker   the campaign's PathBlocker_Vault stays: blocking from the load, unblocked by the door timer, blocked again at
                        a round start (--reset). Bots do not path through the closed door. Not with --vault-stays / --vault-open
      --loot-shown      the vault's loot lies there from the start (default: hidden until the beat's timer ends)
      --loot-bags       the vault's loot keeps F07's money bags (finish() leaves the models alone)
      --beat S          seconds from the ante-room box to the vault door (default BEAT)
      --no-ai           no squad of the campaign stays and none of F07's police: a round without enemies, for a first
                        live run (the beat, the loot and the music are as with them)
      --alarm-lights    the 22 lights of the alarm lamps keep their LightToggle and light at the alarm (default: the
                        controller is taken off and the lights hidden - a kind no stock Dog Days level runs)
      --music-layer4    the nine fades of the break-in set's fourth layer keep their controller and are named
                        (default: taken off - a value no stock Dog Days level has; needed once the clips play)
      --blast-real      the vault's blast with the campaign's own reach and damage (default: a harmless show)
      --no-blast        the vault stays intact: no blast, no swap to the blown vault
      --dead-men-rows   the campaign's soldiers keep Dead Men's rows (default: stock rows by weapon class)
      --str FILE        the stream file the build resolves streamed clips against (FILE + FILE.map.json; default
                        <work>/build/PC_Def.str): the one that holds the map's music (tools/kl_vault_str.py,
                        re/bank_campaign.md 'Music stage'). With it: --music-layer4
      --plan FILE       the van's plan from a file (the van.json beside an earlier build, or 'kl_map_escape.py
                        van-plan <bare graft> --points ... --json'): no bare graft is built for it (60 s less)
      --plaza-outside   THE CREW FIX AFTER RUN V2, part 1 (PLAZA_OUTSIDE): the plaza's seven squads stay on the plaza -
                        the places their routs go by are re-laid in front of the bank (PLAZA_PLACES) and they are
                        started by a box across the hall's south end (PLAZA_BOX), not by the foyer box
      --hall-gallery    part 2 (HALL_UP): F07's eight hall police stand on the hall's gallery (HALL_GALLERY), off the
                        floor the crew has to cross (default: on the floor, in a row before the front entrance)
      --crew-fix        both (what <work>/build/c_bank2 is built with; its chain then runs 'hall-dash')
      THE WAVES BUILD (2026-10-11 night; re/bank_campaign.md 'Waves'; every flag off = the crew-fix build byte for byte):
      --waves           police that keep coming: three CHAINS of parked squads (WAVE_TABLE: A 11 waves from the round's start, B 5 single men from the
                        ante-room box, D 8 from the plaza box; 54 men on top of the 61, one link every 24 .. 35 s, the floor
                        SUPPLY_MIN = 360 s); implies --crew-fix --crew-fix2 --teller-late --teller-more --van-late --reset
      --waves-extra N   men on top of the 61 (0 .. 79, default 54; a chain is cut from its end)   --waves-near M   the softer crew line (250)
      --waves-latch     add the 'wiped out' latch (ZSquadScript field 8 names the next wave's Fast node) - OFF by default: field 8 for a PARKED squad
                        is unproven and could start every wave at the load (second skeptic, fault 2); the chains are plain timer chains
      --crew-fix2       review points (a) DASH_BOX's north edge at the foyer door and (c) the hold timers of the dash steps
      --teller-late     the teller stacks lie hidden until the plaza box + TELLER_SHOW (20 s)      --reset  the round-restart objects
      --teller-more     (on with --waves, --no-teller-more) six stacks of 100,000 on the counters instead of four of 75,000
      --van-late        the van hidden until the foyer box + 6 s / the plaza box + 1 s / (backstop) the ante-room box + 120 s,
                        its FakeTarget off (--no-van-hide, --no-van-target-off)
    python kl_fa_bank.py extras <folder> <out>            the finishing chain's step that adds the waves, the reset and the
                                                          late van's show (flags: bank_opts.json beside the archive); after
                                                          hall-dash, before seal
    python kl_fa_bank.py waves-check <folder>             sight, posts, gating, reset coverage and the van, on a folder the
                                                          step has been through (check() runs it too)
      THE ROOM GATES (2026-10-12, after run W4; re/bank_campaign.md 'Gates, after run W4'; no flag = every build before, byte for byte):
      --gates           'test': eleven men (and one defend place) put off the crew's line (CLEAR_MEN); then 'bots' plans the gates (the planner of
                        kl_fa_bots_rt): before each of lobby / flights (the way in) and hall (the way out; the dock only with --gate-rooms) the seven hold at distinct cover places 1 m inside
                        the mesh until the room's men are dead or the game's 30 s are out; written to bank_opts.json, read by every later step
      --gate-rooms L    comma list of ROOMS to gate (default ROOM_ON = lobby,flights,hall - the dock is in the table and OFF since the second fix; 'airlock', 'front' too; the timetable refuses
                        past the round's budget)      --gates-seen  holds in sight at cover instead of hidden (ROOM_HIDE off)
    python kl_fa_bank.py bots <folder> <out> [--gates --gate-rooms L --gates-seen --loot-seconds N]   the seven AI heisters (+ the vault gate, + the room gates)
    python kl_fa_bank.py dyn <folder> <out>               kl_fa_bots_dyn.build, with room gates: no hold or timer of its own behind a gate, no fork between gates
    python kl_fa_bank.py rooms-check <folder>             the gates of a folder with the squad (bots-check runs it too)

THE ROUND
  START   roped down in the secure yard, two stacks of four beside the loading dock's roller door.
  IN      dock -> vault lobby -> two flights down -> the vault's ante-room. Six door sets stand in series on the
          way in and out (re/campaign_fa_bank.md 8.3): five of them are open from the load, the vault door is the beat.
          13 guards hold the dock and the vault lobby, three pairs the way down (STAGE 'start' / 'down': they come
          into the world SQUADS_AT seconds after the round-start event, just after GO).
  BEAT    a box in the ante-room starts, all at once: six timers that pull the vault door's six locking rods one
          by one, 14 police who come down behind the crew (they come into the world behind the airlock, off the
          way in: BEAT_MEN), the music's rise, and the beat's timer. The box fires ONCE. When the timer ends
          the vault door gets 'Activate', the loot appears, the alarm goes (sound, lamps), the music changes to
          the way-out set, five squads hunt into the vault and three of F07's own police squads take the banking
          hall. DOOR_GONE seconds later the door's body is switched off - the vault can be entered whatever the
          swing did - and the vault blows (VAULT_BLAST: a harmless show; the intact vault is swapped for the blown one).
  LOOT    seven briefcases in the vault (six at the deposit-box walls, one in the middle of the room), four
          stacks on the teller counters of the banking hall.
  OUT     up the airlock stairs into the hall; the foyer box brings the plaza's seven squads (20 men, two SWAT
          fours with rifles); out of the front entrance, onto the plaza: the exit box calls the van.
  ESCAPE  F07's first key-framed van on ROAD (kl_map_escape's way-point front end): it waits at the west end of
          the front square on the designers' own in-road, drives 48 m in 7.2 s to its stop in front of the plaza
          (nose east-north-east; its rear doors are 18 - 20 m from the front entrance), and leaves east along their away
          road, 71 m in 8.48 s, passing the campaign's east level bound 26 m after the stop as every stock van
          passes one. Boarding box, kill box, path blocker, in-van and fixed camera are the van's own, moved with
          it; F07's second and third van are not in the level (VAN). The escape marker stands beside the lane,
          4 m from the drive (ESC_AT), not on the van's stop.

HOW (as kl_fa_author: no new entity, no new controller - every object is a stock one, re-placed and re-wired)
  The nine names of kl_graft.AUTHOR_NAMES: HOST, prepare_host(S), strip(M), KEEP, DROP, layer_names(Jn),
  complete(Jn), wire(Jn), campaign_names(level). On top of them, because the interface has no place for it:
  1. THE DOORS AT BUILD TIME (Doors): three functions of kl_escape that kl_graft.build calls for every Dead Men
     map are wrapped for the length of ONE build - the recipe of the study's G:/kl_scratch/cfa_fill1/build_open.py
     (re/campaign_fa.md G1.1, with its two traps). prepare_host() puts the wrappers in, the last of them takes
     them out again; 'with doors(): ...' does the same from a script.
  2. finish(folder), on the written level (chunk numbers and the .LOC exist only then): the briefcase model
     (kl_fa_loot.case_model, into dead chunk indices), and the level's own texts (.LOC keys, settings fields).
  3. THE VAN (build()): its plan needs the collision of a BUILT level without the layer, and its collision
     placements are set in kl_hvk.join, which no name of the interface reaches - so build() makes a bare graft
     for the plan, hands it to prepare_host() / wire() (lay_van) and wraps the build in kl_map_escape.van_layer.
     'kl_maps.py one ... --author kl_fa_bank' alone therefore stops in prepare_host with a line that says so.

GUESS = a value that is not copied from a stock object or measured in the levels; ASSUMPTION = fits the
evidence, not proven. Every table entry carries its source. Rotation, box and 'hidden' facts: kl_fa_author's
docstring (the helpers are imported from there: rot9 / look9 / place / setv / ctrl_of / node_of).
"""
import collections, contextlib, math, os, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_graft, kl_fa, kl_maps, kl_gms, kl_scene, kl_escape, kl_hvk
import kl_prpjoin as J
import kl_fa_author as A                # the small tools only (place, setv ...); none of Retomoto's tables
import kl_map_escape as ESC             # the van: plan from way points, F07's keys laid on it, its check
from kl_prp import units

HOST, LEVEL = 'F07', 'M03_A'
TITLE = 'The Vault'                     # the map's name (for the menu page: kl_expansion's table, a later stage)
R = 'ROOT\\'
IN = 'Locations/M03_A/M03A_Locations.zip\\Locations/M03_A/M03A_LOC_Inside.zip\\'
VA = IN + 'Locations/M03_A/M03A_LOC_Ins_Vault.zip\\'
HIDDEN = 0x400
# problems kl_graft.verify reports that this layer cannot remove: (text looked for, why it stands)
KNOWN = (('stream clips are not in the merged stream file', 'the level\'s music (MUSIC_CLIPS), its vault ambience and nine guard lines have no record in '
          'the built .WHD - they are not in the installed PC_Def.str; a larger stream file is the owner\'s go-ahead (re/campaign_fa.md 3.1 K): those sounds '
          'are silent, nothing else. (The kept guards\' other one-liners DO stream from the merged file; result.json\'s list of names is longer than what '
          'is lost - check() reads the built .WHD: lost_clips)'),)
# ... and in a build without enemies ('--no-ai'), which check() knows by the level having no squad at all
KNOWN_NO_AI = ('no ZSquadScript', 'a round without enemies (NO_AI): the build for a first live run')

# ------------------------------------------------------------------ the bank (M03_A), measured
# Floors (collision, tools/kl_route.py stations on a built level): yard and loading dock y 200, vault lobby 240,
# vault and ante-room -960, banking hall and plaza 800, front street 700. Everything below is on ONE part of the
# navigation mesh (566 polygons; re/bank_campaign.md T3).
YARD = 200.0                            # (the dock's roller door M03_A_Garage_01a\SI0201_M03_BackDorAnim_01: doorway x 385..735, z -4706)
FRONT = (300.0, 800.0, -9350.0)         # the front entrance: no door, a 2.0 m gap between two glass wings (x 200..400, z -9410)
TO_DOOR = (0.0, -1.0)                   # from the yard at the dock door
# THE ESCAPE MARKER (the HUD's 'go here') stands BESIDE the van's lane, between the plaza and the place where the
# van's rear doors will be: MEASURED 425 from the drive's line and 357 from the boarding place, on the START's
# mesh part and on free floor (C:/kl_scratch/bank/fix_1/s/lane.py). The first three stages had it over the van's
# STOP: the van is called when the plaza is entered, 18 m away, and takes 7.2 s - a running player stood on the
# marker before the van's nose came, and the van's KillBox (180 wide, at its nose) 'kills what it runs over'
# (re/map_escape.md). Stock F07's marker stands 3 m off the nearest of its three stops, on none of them
# (review round 1). GUESS: the place itself (the bots' own waiting place beside the stop, kl_fa_bots' AllyEscapeBox)
ESC_AT = (316.0, 702.0, -11070.0)       # on the street's floor (y 700): the round's last station (ROUTE_OUT)
ESC_POI_UP = 188.0                      # the marker over the floor (F07: 190 over its road; Retomoto's)
ESC_POI = (ESC_AT[0], ESC_AT[1] + ESC_POI_UP, ESC_AT[2])
# START (re/campaign_fa.md 4.1 item 1): two stacks of four beside the dock door, under the back wall where the
# campaign's ropes end ((-35 / -151, 200, -4525)). GUESS: the stacks; MEASURED: each point on the mesh and on free
# floor (check()). A parked armoured transport (x -30..190, z -4130..-3590) stops the rows moving west.
START = [(float(x), YARD, -4350.0) for x in (150, 250, 350, 450, 700, 800, 900, 1000)]
TRAITOR = [(float(x), YARD, -4000.0) for x in (300, 530, 770, 1000)]            # GUESS: behind the stacks
# police who come back: the front street, at the places of the campaign's own plaza police (re/campaign_fa.md
# 4.1 item 7: 'Police_OutSide_01' west (x -1842..-1437), 'Police_Outside_Teargas_01' east). GUESS: the points inside
# those spans; the west row begins at x -1750: the campaign's own warn box of its west level bound reaches x -1805.
# Those squads STAY (STAGE 'plaza': their men stand at z -9686..-9397), so the rows are 2 m beyond them, towards
# the street (z -9900): no point or police body within POLICE_CLEAR of a squad's man (check())
POLICE = [(-1750.0, 705.0, -9900.0), (-1650.0, 705.0, -9900.0), (-1545.0, 705.0, -9900.0), (-1437.0, 705.0, -9900.0),
          (2016.0, 706.0, -9900.0), (2100.0, 706.0, -9900.0), (2178.0, 706.0, -9900.0)]
# team mode's respawn stages: vault lobby (campaign 'CP_03_PosP1'), ante-room (the campaign's box 'TB_VbByVault'),
# foyer and hall (campaign 'CP_05_PosP1' / 'CP_04_PosP2'). GUESS: the three points beside each marker
STAGE_B = [(394.0, 241.0, -7129.0), (294.0, 241.0, -7129.0), (494.0, 241.0, -7129.0), (394.0, 241.0, -7029.0)]
STAGE_C = [(460.0, -958.0, -12152.0), (334.0, -958.0, -12226.0), (234.0, -958.0, -12226.0), (400.0, -958.0, -11979.0)]
STAGE_D = [(295.0, 802.0, -6052.0), (297.0, 802.0, -6238.0), (195.0, 802.0, -6052.0), (395.0, 802.0, -6052.0)]
# ZSpawnPoint type -> (points, shift so that two kinds never share a point, facing: (dx, dz), or a place looked at)
SPAWN = {'eSPAWN_TYPE_FRAGILE_ALLIANCE_START': (START, (0, 0, 0), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TRAITOR': (TRAITOR, (0, 0, 0), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH': (POLICE, (0, 0, 0), FRONT),
         # the other modes' criminals stand in the yard too, in rows of their own
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC': (START, (0, 0, 100), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_MERC': (START, (0, 0, 100), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_TRAITOR': (TRAITOR, (0, 0, 120), TO_DOOR),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_UCC_POLICE': (POLICE, (0, 0, -120), FRONT),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC': (START, (100, 0, 200), TO_DOOR),      # 100: clear of the armoured transport
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC1': (STAGE_B, (0, 0, 0), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC2': (STAGE_C, (0, 0, 0), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC3': (STAGE_D, (0, 0, 0), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_MERC4': (STAGE_D, (0, 0, -120), (0.0, -1.0)),
         'eSPAWN_TYPE_FRAGILE_ALLIANCE_TEAM_POLICE': (POLICE, (0, 0, -240), FRONT)}
HENCH_SHIFT = (0.0, 0.0, -160.0)        # the eight police bodies (Heroes!Henchmen_0n) beside the AFTER_DEATH points

# ------------------------------------------------------------------ the loot
# THE VAULT (M03_A_Vault_01a, floor y -960): the six deposit-box walls SI0102_M03_BankVault_Wall2mBOXES_PRE_01..06
# stand at (600 / 400 / 200, -960, -13410) and (0, -960, -13230 / -13030 / -12830); the trolley
# PC0600_M03_VaultTrolley_01 at (199, -960, -13171) carries cartons whose top is y -844 (MEASURED in the collision).
# (place on the floor, degrees the case is turned, value). GUESS: every place, turn and value
# (the study: 'about 2.6 million'; F07's own loot: 5 x 800,000). The places are 100 in front of their wall:
# the blown vault 'Vault_POST', which the beat's blast shows in place of the intact one, has its rubble at the
# walls' feet (floors y -879 at z -13350 and x 70) and a heap of it at x 400..500, z -13310..-13200 (top y -891):
# a case must lie where BOTH vaults have bare floor (check(): 'buried'). So the south wall's cases lie at x 200,
# 300 and 600, and the big one in the middle of the room - not on the trolley's cartons, which go with the
# intact vault (the first half had it there).
VAULT_LOOT = [((200.0, -960.0, -13310.0), 8.0, 300000), ((300.0, -960.0, -13310.0), -6.0, 300000), ((600.0, -960.0, -13310.0), 11.0, 300000),
              ((110.0, -960.0, -13230.0), 96.0, 300000), ((110.0, -960.0, -13030.0), 84.0, 300000), ((110.0, -960.0, -12830.0), 101.0, 300000),
              ((430.0, -960.0, -12950.0), 20.0, 500000)]            # the last: the middle of the room, before the door
VAULT_BOX = ((-50.0, 1150.0), (-1000.0, -400.0), (-13560.0, -12650.0))      # the room, for finish() / check(): what lies in the vault. GUESS: the
                                                                            # box, drawn round the walls' places above with room to spare
# THE TELLERS (M03_A_Bank_Main_01): counters Pc0100_M03_Bankcounter_A_* at x -791 (z -7202, -7602, -8002) and x 1393
# (z -7206, -7606, -8006), their top y 899, a glass grille over it (MEASURED in the collision). The stack lies on the
# counter's public edge - the side the crew passes on its way out. GUESS: the edge distance (26) and the value
TELLER_LOOT = [((-765.0, 899.0, -7202.0), 75000), ((-765.0, 899.0, -8002.0), 75000), ((1367.0, 899.0, -7206.0), 75000), ((1367.0, 899.0, -8006.0), 75000)]


def teller_loot():
    """The teller stacks as the flags say: TELLER_LOOT (4 x 75,000: the build of every earlier delivery) or, with TELLER_MORE, six of TELLER_MORE_VALUE."""
    if not TELLER_MORE:
        return list(TELLER_LOOT)
    return [(p, TELLER_MORE_VALUE) for p, _v in TELLER_LOOT] + [(p, TELLER_MORE_VALUE) for p in TELLER_MORE_EXTRA]


LOOT_REACH = 125.0                      # TriggerBox2 radius: the value of all 117 stock OnlineMoneyContainer triggers (kl_escape.REACH)
GATE_VAULT = True                       # False ('--loot-shown'): the vault's loot lies there from the start
CASE = 'dm'                             # the vault's prop: Dead Men's Fragile Alliance briefcase (kl_fa_loot.CASES); None = F07's bags
CASE_SCALE = 1.25                       # GUESS, kl_fa_loot's for that model (36 wide x 1.25 = 45: a real attache case)

# ------------------------------------------------------------------ the doors
# Six door sets in series, each necessary, no way round any of them (re/campaign_fa_bank.md 8.3; tools/kl_route.py
# doors). (path below ROOT, stock world place, set). The glass leaves stand under a TURNED group, the others not.
LEAVES = [(IN + 'M03_A_Garage_01a\\SI0201_M03_BackDorAnim_01', (560, 550, -4706), 'dock roller door'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_01\\GlassDoor_LEFT', (125, 240, -6808), 'glass door 1'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_01\\GlassDoor_RIGHT', (-125, 240, -6808), 'glass door 1'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_02\\GlassDoor_LEFT', (525, 240, -7602), 'glass door 2'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_GlassDoor_02\\GlassDoor_RIGHT', (274, 240, -7602), 'glass door 2'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_01', (1215, 240, -7105), 'airlock'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_02', (1215, 240, -6895), 'airlock'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_03', (1000, 240, -6895), 'airlock'),
          (VA + 'M03_A_VaultLobby_01a\\SI0103_M03_BankVault_DDorSlide_04', (1000, 240, -7105), 'airlock'),
          (VA + 'M03_A_VaultLobbyFoyer_01a\\SI0103_M03_BankVault_DDorSlide_01', (195, 802, -5801), 'hall / foyer'),
          (VA + 'M03_A_VaultLobbyFoyer_01a\\SI0103_M03_BankVault_DDorSlide_02', (405, 802, -5801), 'hall / foyer')]
# the vault door: a ZGROUP with the MatPosAnim ('Activate', frames 0..200: 100 degrees at frame 60, rests at 95;
# one way - re/campaign_fa.md G1.8) and below it the body that owns the key-framed collision placement
VAULT_DOOR = VA + 'M03_A_VaultEntrance_01a\\SI0102_M03_BankVault_Door_PRE_01'
VAULT_BODY = VAULT_DOOR + '\\SI0102_M03_BankVault_Door_PRE'
VAULT_BODY_AT = (571, -760, -12510)
# DOORS, the lead's default (the owner has not answered): the eleven leaves are OPEN AT BUILD TIME - sunk DOOR_DY
# in world y, their collision placements cut - so that the first live load cannot be stopped by a Dead Men door
# animation that does not play. True ('--doors-animate'): the leaves stay; the round-start event sends each
# 'Activate', and the four glass leaves get their own LAST frame GLASS_LAST first: their clip goes to 135 degrees
# at frame 50 and BACK to 0 at frame 100, and a leaf that stores -1 / -1 plays the whole clip (G1.8).
DOORS_ANIMATE = False
DOOR_DY = -2500.0                       # the study's: under the map's lowest floor (the vault, y -960)
GLASS_LAST = 50                         # the campaign plays 0..50 on door 1 and 0..36 on door 2 (109 degrees)
MPA_MESSAGE, MPA_LAST = 0, 14           # MatPosAnim fields: the message that starts it, the last frame (13 = the first)
# THE VAULT DOOR is the beat and keeps its collision. Whatever its swing does in Dog Days, the vault must be
# enterable: DOOR_GONE seconds after its 'Activate' a DeactivateGeom switches the body off. ASSUMPTION that a
# body switched off at run time stops colliding (stock F07 takes its 'BlockVisionPlane' away so; Retomoto's blown
# window is walked through). If it does not, '--vault-open' sinks the door with the others.
VAULT_OPEN = False
VAULT_SWING_END = None                  # '--vault-swing [S]': seconds after the beat's end at which the door's body is switched off by SWING_TIMER (None = the door timer does it, DOOR_GONE s)
SWING_TIMER = 'Gameplay!010_FirstFight!Shutters!TimerShuttersClose_RIGHT'   # a free F07 TriggerDelay2 (kept only with the flag: KEEP)
SWING_DEFAULT = 9.0                     # the clip is 200 frames at rate 25 = 8 s; a second more. GUESS (the swing itself has not been SEEN in the game)
VAULT_DOOR_GOES = True                  # False ('--vault-stays'): once the swing has been SEEN to play and to let people in
BEAT = 48.0                             # s from the ante-room box to the door. GUESS: six rods at 8 s steps (the study)
BOX_PER_MAN = 15                        # TriggerBox field: 1 = fires for every criminal that enters, 0 = once (wire(): the census)
DOOR_WAIT = True                        # hall police + hunt go on the DOOR timer (swing over, body off), not on the beat's end: nobody is sent through a door that still swings / collides (owner 2026-10-17; '--door-early' = the old order)
# VAULT_BLOCKER ('--vault-blocker'): the campaign's own PathBlocker_Vault is kept (BLOCKER, a top-level node of the Vault part: ZBoxPrimitive
# across the opening, PathBlocker ['eUnblock', initial 'eBlocking', list [an audio object the build drops]]). It stands blocking from the load
# (bots do not path through the closed door), the door timer names it ('Activate' = the configured eUnblock, as the campaign's VaultDoors_Open
# does at the end of the swing) and a round-start object sends it 'Block' so that round 2 starts closed (AIDWrapper 'Block', kl2 0x710320).
# GUESS: that 'Activate' from a TriggerDelay2 list unblocks (the campaign wiring says so) and that the AIDWrapper's 'Block' reaches the handler.
VAULT_BLOCKER = False
# VAULT_BLOW ('vault-blow <folder>', a .prp-only post-step; bank_opts.json 'vault_blow'): the owner (2026-10-17) saw the door 'just sit there'.
# The door is then NOT swung (the beat's 'door' wrapper names nothing) and at the door timer's moment - the one that fires the three Explode
# and the blast sound - the DeactivateGeom 'door off' switches off the WHOLE door: the animated group, its body (8 meshes, KEYFRAMED
# collision shape in the .HVK) and the hinge piece Door_Add_PRE_01 (3 meshes, no HVK placement). Stock Dog Days deactivates the animated
# group itself (trains, vans). ASSUMPTION: the engine drops a key-framed body's collision with its geometry (not seen live).
# Round 2: the module's Reset_show names all three again (GUESS: ActivateGeom on a group restores its children).
VAULT_BLOW = False
VAULT_HINGE = VA + 'M03_A_VaultEntrance_01a\\SI0102_M03_BankVault_Door_Add_PRE_01'
BLOCKER = 'GamePlay!4_Vault_Part!PathBlocker_Vault'
# VAULT_SWING's round 2: --reset shows the door's body again but the MatPosAnim stays at its end pose (open, ~95 degrees). With the swing flag the
# round start also sends the door 'Activate' (kl2 0x59dce0 evaluates frame 0 at once = closed) and DOOR_POSE_DELAY s later a wrapper sends it
# 'ForceStopAnim' (kl2 0x5eacc0), so it stands closed and the clip does not run on. GUESS: the delay (any value < 1 frame-time of the clip's first
# step would do; 0.05 s = 1 frame at 25 fps is the smallest the timer gives) and that frame 0 is the closed pose with F7 'relative' = 1.
DOOR_POSE_DELAY = 0.05
DOOR_GONE = 6.0                         # s after the door's 'Activate'. GUESS: the swing is at its 100 degrees after 2.4 s

# ------------------------------------------------------------------ the host's layer
PARK = (0.0, -60000.0, 0.0)             # where a host object without a use is put (kl_fa_author.PARK)
BOX = (0.0, 1.0)                        # a box is laid in the world's axes (the turn that leaves local +Z where it is)
# host object -> (position, facing or None, half extents or None, source of the numbers)
PLACE = {
    # the round's markers and planes
    'FASpecials!POI!Trigger_POI_TheLootArea': ((575, 350, -4150), None, (700, 200, 450), 'GUESS: box round the START stacks in the yard (F07: round its start); it starts the loot marker\'s 11 s timer'),
    'FASpecials!POI!POI_TheLootArea': ((400, -800, -13000), None, None, 'the vault\'s middle; GUESS: 160 over its floor'),
    'FASpecials!PIP!EnterLootArea': ((560, 380, -4800), None, (250, 230, 50), 'GUESS: a plane 1 m inside the dock\'s roller door (doorway x 385..735, z -4706)'),
    'FASpecials!PIP!ExitLootArea': ((303, 974, -9407), None, (300, 200, 100), 'the front entrance: M03_FA_A\'s own ENTERS box there (Triggers!EnterBankTrigger_01), same world'),
    'FASpecials!POI!POI_TheEscapeArea': (ESC_POI, None, None, 'BESIDE the van\'s lane, not over its stop (ESC_POI); prepare_host() holds it against the PLAN\'s drive'),
    'FASpecials!POI!Trigger_POI_TheEscapeArea': ((300, 1075, -10550), None, (1500, 425, 1150), 'GUESS: plaza and street as the exit box (z -11700..-9400), y 650..1500. NOT the banking hall: '
                                                 'the box takes the loot marker away (GeomDeactivator_TheLootArea), and the hall is reached from the vault lobby without the vault (review round 1)'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaCP_OffenseOnlyRespawn': ((300, 1075, -10550), None, (1500, 425, 1150), 'as above'),
    'FASpecials!POI!Trigger_POI_TheEscapeAreaFA_RespawnOnly': ((300, 1075, -10550), None, (1500, 425, 1150), 'as above'),
    # the beat's box and the exit
    'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou': ((460.4, -714.0, -12151.8), None, (550.2, 254.0, 556.1), 'the campaign\'s own box GamePlay!4_Vault_Part!...\\TB_VbByVault: place and half extents'),
    'Gameplay!EscapeSetup!otrExitLevel': ((300, 800, -10550), None, (1500, 300, 1150), 'GUESS (the study): plaza and street in front of the entrance, from 50 beyond its gap: z -11700..-9400 - carried '
                                          '500 farther south than the study\'s, so that it holds the van\'s stop AND its boarding place as the box of every stock level does (12 vans of F01 F04 F05 F07)'),
    'Specials!LevelSpeak!TriggerBox': ((300, 930, -5650), None, (300, 180, 150), 'GUESS: the foyer, where the crew comes up into the hall (campaign Jump#120 (309, 803, -5624))'),
    'Specials!LevelSpeak!OnlineSpeakTrigger_01': ((300, 930, -5650), None, None, 'with its trigger box'),
    # spawn cameras (camera, look-at): all GUESS
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!Camera_000_A': ((575, 650, -3550), None, None, 'GUESS: over the yard'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_000_A!CameraLookAt_000_A': ((560, 320, -4700), None, None, 'the dock\'s roller door'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!Camera_010_B': ((700, 470, -6600), None, None, 'GUESS: vault lobby'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_010_B!CameraLookAt_010_B': ((394, 300, -7129), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!Camera_020_C': ((600, -700, -11400), None, None, 'GUESS: ante-room'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_020_C!CameraLookAt_020_C': ((400, -880, -12400), None, None, 'GUESS: towards the vault door'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!Camera_030_D': ((300, 1250, -7000), None, None, 'GUESS: banking hall'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_030_D!CameraLookAt_030_D': ((295, 870, -6052), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!Camera_000_Police': ((-1640, 1100, -10300), None, None, 'GUESS: over the street, west'),
    'FASpecials!SpawnPoint!TeamMode!SpawnCam_100_Police!CameraLookAt_000_Police': ((-1640, 760, -9580), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!Camera_000_Police_FA': ((-1640, 1100, -10300), None, None, 'GUESS'),
    'FASpecials!SpawnPoint!SpawnCam_000_Police_FA!CameraLookAt_000_Police_FA': ((-1640, 760, -9580), None, None, 'GUESS'),
    # team mode: the respawn stage moves when a criminal passes these
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_010_B': ((0, 340, -6900), None, (200, 150, 80), 'GUESS: behind glass door 1 (x -150..150, z -6810)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_020_C': ((400, -800, -11200), None, (400, 200, 100), 'GUESS: the ante-room\'s near end (the room is z -12600..-10800)'),
    'FASpecials!SpawnPoint!TeamMode!SpawnpointTrigger_030_D': ((300, 930, -5650), None, (300, 180, 150), 'GUESS: the foyer (floor y 800)'),
    # jump points (developer aids in stock levels; nothing names them): the campaign's own jump list
    'Specials!JumpPoints!01_Start': ((575, YARD, -4250), TO_DOOR, None, 'the yard, between the START stacks'),
    'Specials!JumpPoints!02_MarketMain': ((266, 202, -5002), TO_DOOR, None, 'M03_A Special!JumpPoints!Jump#131: the dock'),
    'Specials!JumpPoints!03_MarketOrange': ((422, 242, -6188), TO_DOOR, None, 'Jump#070: towards the vault lobby'),
    'Specials!JumpPoints!04_LootWarehouse': ((463, -956, -13238), (0.0, 1.0), None, 'Jump#100: the vault'),
    'Specials!JumpPoints!05_MarketGreen': ((377, 801, -8423), TO_DOOR, None, 'Jump#130: the banking hall'),
    'Specials!JumpPoints!06_Exit': ((291, 714, -11159), (1.0, 0.0), None, 'Jump#132: the front street'),
    # level bounds. Front: the campaign's own three stay (kl_maps.campaign_drop: Special!Levelbound!LevelBound_Outside_
    # Front (355, 943, -14140), _Left (3763, 843, -10211), _Right (-2837, 928, -10916)). Back: the yard is a closed box
    # (walls and hero-only collision on three sides: re/campaign_fa_bank.md 8.3); these two are for whoever gets out
    'Specials!LevelBound!040_LevelBound_AlleyTop!Bound': ((1000, 400, -320), None, (1700, 600, 220), 'GUESS: behind the yard\'s north wall (z -600; a walker comes to z -680), z -540..-100'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn01': ((1000, 400, -345), None, (1700, 600, 245), 'GUESS: from z -590'),
    'Specials!LevelBound!040_LevelBound_AlleyTop!Warn02': ((1000, 400, -345), None, (1700, 600, 245), 'as Warn01'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Bound': ((2800, 400, -2700), None, (250, 600, 2100), 'GUESS: behind the yard\'s east fence (x 2386; a walker comes to x 2300), x 2550..3050'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn01': ((2750, 400, -2700), None, (300, 600, 2100), 'GUESS: from x 2450'),
    'Specials!LevelBound!030_LevelBound_StreetLeft!Warn02': ((2750, 400, -2700), None, (300, 600, 2100), 'as Warn01'),
}
PARKED = ['Specials!LevelBound!%s!%s' % (g, b) for g in ('020_LevelBound_AlleyRight', '040_LevelBound_AlleyRight', '040_LevelBound_AlleyLeft',
                                                         '030_LevelBound_StreetRight') for b in ('Bound', 'Warn01', 'Warn02')]
# host objects that get a new job in wire(): role -> name (each a single top-level node)
ROLE = {'monitor': 'Gameplay!AIMonitor',
        'doors': 'Gameplay!010_FirstFight!RivalMercVan!Activator_OLD_VanGo',         # AIDWrapper 'Activate' -> the eleven leaves (DOORS_ANIMATE)
        'beat box': 'Gameplay!010_FirstFight!tb_LEFT_TheySpotYou',                   # TriggerBox in the ante-room
        'beat timer': 'Gameplay!010_FirstFight!RivalMercVan!Timer',                  # TriggerDelay2 BEAT: the gate of the round
        'door': 'Gameplay!010_FirstFight!RivalMercVan!Activator_VanSound',           # AIDWrapper 'Activate' -> the vault door
        'door timer': 'Gameplay!010_FirstFight!RivalMercVan!TimerVanGo',             # TriggerDelay2 DOOR_GONE
        'door off': 'Gameplay!010_FirstFight!RivalMercVan!GeomDeactivator_DriveInVan',   # DeactivateGeom -> the door's body
        'loot on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_LEFT',    # ActivateGeom -> the vault's hidden loot
        'speak box': 'Specials!LevelSpeak!TriggerBox', 'speak': 'Specials!LevelSpeak!OnlineSpeakTrigger_01',
        'exit': 'Gameplay!EscapeSetup!otrExitLevel',
        # the second half: the squads' start, the music, the six rods, the vault's blast
        'start timer': 'Gameplay!010_FirstFight!RivalMercs!Timer',                   # TriggerDelay2 SQUADS_AT -> the first squads
        'music timer': 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!Timer',  # TriggerDelay2 MUSIC_AT -> the break-in set
        'post on': 'Gameplay!010_FirstFight!Shutters!GeomActivator_TearGas_RIGHT',   # ActivateGeom -> the blown vault, fire, smoke
        'pre off': 'Gameplay!010_FirstFight!RivalMercs!DisableVisionBlocker!GeomDeactivator'}    # DeactivateGeom -> the intact vault
FF = 'Gameplay!010_FirstFight!'
ROLE.update(('rod timer %d' % (i + 1), FF + n) for i, n in enumerate((               # six TriggerDelay2, one a rod
    'RivalMercs!RandomizeFight!Timer_LEFT', 'RivalMercs!RandomizeFight!Timer_RIGHT', 'RivalMercs!DisableVisionBlocker!TimerInputAI',
    'RivalMercVan!Timer_PFBlocker', 'RivalMercVan!CoverStateChangerHero!Timer', 'RivalMercVan!TimerMercsVanExit')))
ROLE.update(('rod %d' % (i + 1), FF + n) for i, n in enumerate((                     # six AIDWrapper 'Activate' -> a rod
    'RivalMercVan!CoverStateChangerHero!ActivateCovers', 'RivalMercVan!CoverStateChangerHero!DeactivateCovers',
    'Shutters!Activator_Shutter_Close_RIGHT', 'Shutters!Activator_Shutter_Close_LEFT', 'Shutters!Activator_Shutter_LEFT',
    'Shutters!Activator_Shutters_RIGHT')))
# FOR THE NEXT STAGES. Free single top-level objects of F07 this file does not touch (add the name to KEEP_MORE, give
# it a ROLE): trigger boxes Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou, Gameplay!030_AfterLoot!tbExitFinancialAlley,
# Gameplay!020_Loot!tbExitLoot, Gameplay!020_Loot!FollowPlayers!tbCountPlayers, Gameplay!040_Escape!tbEscapeAI,
# Gameplay!RunToEscape!tbRunToEscape, ...!tbRunToEscape1Player; counters Gameplay!020_Loot!FollowPlayers!TriggerCounter,
# Gameplay!RunToEscape!tcRunToEscape; six more TriggerDelay2 (Gameplay!010_FirstFight!Shutters!TimerShuttersClose_RIGHT,
# ...TimerShuttersClose, ...TimerShuttersOpenDif, ...TimerShuttersOpen, ...PF_Blocker!Timer_PF_LEFT / _RIGHT) and the
# three of Gameplay!RunToEscape!. NO AIDWrapper, ActivateGeom or DeactivateGeom of F07 is free any more; the campaign has
# single ones (GamePlay!5_Lobby!LobbySlidedoors!LockLobbyDoor ...) that stay when campaign_names() names them.
# Five of the timers are named by F07's AIMonitor at the round start (RivalMercVan!Timer and TimerVanGo among them):
# wire() writes the monitor's list, so that a ROLE object is started only by what this file names.
KEEP_MORE = ()
# the escape: F07's first van, its relay, the exit trigger and the two 'last van' objects (the monitor is kept by
# kl_fa.host_keep) = kl_map_escape.VAN_KEEP + three. F07's SECOND AND THIRD VAN ARE NOT KEPT: a van without a use
# cannot be parked under the map as Retomoto's street layer did (its ZFakeTarget outside the rooms' bounds is the
# 0x686a66 crash, re/crash_686a66.md), and a level with ONE van is the form the three car maps on the owner's tab
# run (re/map_escape.md 10). The exit trigger names the one van in field 2 and nothing in 3..5.
VAN = 'Animation/F07/F07_Escape_Vehicle_01.zip'
VAN_GROUP = 'EscapeVehicle_Animation_F07'       # everything of the van with a place is below it (kl_fa_author.place_vans)
# THE VAN'S ROAD (re/bank_campaign.md T2.4: 'the passing plan'; kl_map_escape.van_plan_points makes the plan of it
# against the map's collision - keys, boarding box, camera, bounds - and van_prepare lays F07's keys on it):
#   arrive  the first three points of the designers' own in-road on the front square: the van waits at the first,
#           43 m west of the stop (48 m of drive), beyond the campaign's west bound - and IN SIGHT of the plaza: the
#           square is open (re/bank_campaign.md L3.4)
#   stop    in front of the plaza, the origin of the standing van. MEASURED: the lane is clear 220, 260 and 320 wide;
#           the first agent's stop (250, 707, -10700) has 4 m of lane (T2.4). The heading is the curve's (67: nose
#           east-north-east, the rear doors west-south-west); heading 90 passes too - taste, not chosen
#   leave   the designers' away road, and from its end (3958, 713, -11173) the same line carried on east to x 8600.
#           GUESS that it looks like a road out there: MEASURED are the collision floor (y 700.0, unbroken) and the
#           furniture beside it (out to x 8000); without the extension the drive away is 24 m, under MIN_OUT
#   cam     None = kl_map_escape.cam_spot's eye (GUESS: 18 m behind the stop, 330 over the square)
ROAD = dict(arrive=[(-3248, 710, -11859), (-1917, 712, -12126), (-231, 707, -12332)], stop=(949, 704, -11105),
            leave=[(2473, 705, -11177), (3958, 713, -11173), (8600, 705, -11173)], at='origin', heading=None, cam=None)
PLAN = None                             # the plan of ROAD (lay_van): prepare_host() and wire() lay the van on it
NO_PLAN = ('kl_fa_bank: the van has no plan: build with \'kl_fa_bank.py test <out>\' or kl_fa_bank.build() (the plan is made on a bare graft and '
           'kl_map_escape.van_layer has to stand round the build; \'kl_maps.py one ... --author kl_fa_bank\' can do neither)')
BOARD_NEAR = 30.0                       # the boarding place is a station of the round: on the START's mesh part and on free
                                        # floor within this (the measure of the spawn points)
LANE_CLEAR = 250.0                      # no spawn point, player body, squad's man, escape marker or station of the way out
                                        # nearer than this to the van's drive (the lane that is tested is 110 either side;
                                        # the van's kill box is 90). GUESS. The boarding place is the one exception: the box
                                        # rides on the van, a player goes there when the van STANDS
BOUND_AFTER = 1000.0                    # a level bound on the drive away at least this far after the stop: every stock
                                        # Dog Days van passes one with its passengers, the nearest 10.9 m after the stop
                                        # (F01; F07's own 18.6 .. 39.8 m; MEASURED C:/kl_scratch/bank/l3/s/stockbound.py)
ESCAPE =('Gameplay!EscapeSetup!otrExitLevel', 'Gameplay!EscapeSetup!RelayDestroyedEsc_01',
          'Gameplay!EscapeSetup!OnScreenMSG_LastEscapeVan', 'Gameplay!EscapeSetup!Timer_OSM_LastEscape')
_KEEP = ('FASpecials!', 'Specials!', VAN) + ESCAPE + tuple(v for v in ROLE.values() if v.startswith('Gameplay!0'))


def __getattr__(name):
    if name == 'KEEP':                  # kl_graft.build reads kl_fa_bank.KEEP at the moment of use
        more = tuple(KEEP_MORE) + (() if NO_AI else tuple(HALL))        # F07's three police squads of the banking hall
        more += (PLAZA_BOX,) if PLAZA_OUTSIDE else ()                   # ... and the box that starts the plaza's squads
        more += (SWING_TIMER,) if VAULT_SWING_END is not None else ()   # ... and the free timer that ends the vault door's swing
        return _KEEP + tuple(x for x in more if x not in _KEEP)
    raise AttributeError(name)

# F07's cover list goes: M03_A's own 'Special!CoverList' stays through the campaign pre-pass (kl_maps.PASSIVE), and
# a second FFCoverList is an assert in its init (kl2 0x6682c5; kl_fa_author.DROP)
DROP = ('Specials!CoverPoints!*',)

# ------------------------------------------------------------------ texts and lines
# The level's own .LOC keys (finish()). The start window is a text key of the level's .LOC (settings fields 12 / 13
# Fragile Alliance, 14 Cops & Robbers, 15 Undercover Cop; F07: 'Get the documents, then get to the back alley ...').
# Dead Men's own menu has the slots 'TitleDL01' / 'BriefingDL01 - Bank Vault' for a vault map that never shipped:
# the title and a briefing in the style of its four ('The money transport always arrives at The US Credit Bank ...')
# are written under those keys. Nothing in Dog Days reads the two: they are there for the menu page (a later stage).
# GUESS: every wording. The other eight languages get the English text.
START_KEY = 'AllLevels/Interface/Online/GameStart/M03A_%s_Start'
TEXTS = {START_KEY % 'FA': 'Get down to the vault, grab the cases and get out through the front. The van picks you up on the street.',
         START_KEY % 'Team_B': 'Stop the heist and retrieve as many cases as possible.',
         START_KEY % 'UCC': 'Get down to the vault, grab the cases and get out through the front. The van picks you up on the street.',
         'AllLevels/Menu/Online/Scenarios/TitleDL01': TITLE,
         'AllLevels/Menu/Online/Scenarios/BriefingDL01': 'The tellers at The US Credit Bank, Downtown district, only handle small change. The real money '
         'sits in the vault, three floors under the banking hall. We rope down into the secure yard, go in through the loading dock, '
         'crack the vault door and take the cases. Then up through the hall and out the front doors, where our getaway van will pick us up.'}
START_FIELDS = {12: 'FA', 13: 'FA', 14: 'Team_B', 15: 'UCC'}
# the briefing and reminder lines: stock F07's speak of a data theft. Lines of other stock levels that fit cash, a
# quiet way in and a street, all in F07's bank with their eight voices (kl_fa_author.RT_LINES does the same for
# Retomoto; re/bots_voice.md 6.2). settings field -> line. GUESS: the choice
LINES = {17: 'Multiplayer/F05/MissionBriefing_03_R',     # 'Keep it down. Get in and get the cash at any price.'
         18: 'Multiplayer/F05/MissionBriefing_02_R',     # 'Move in quietly. The fuckers wont know what hit 'em.'
         19: 'Multiplayer/F05/MissionBriefing_01_R',     # 'Keep it down and take 'em by surprise.'
         20: 'Multiplayer/F05/MissionBriefing_03_R',
         127: 'Multiplayer/F06/ReachlootArea_01_R',      # 'Alright! Grab the cash.'
         130: 'Multiplayer/F04/ExitLootArea_01_R',       # 'We got it! Let's keep moving!'
         136: 'Multiplayer/F06/MissionReminder_01_R',    # 'Just get the money.'
         137: 'Multiplayer/F09/MissionReminder_02_R'}    # 'We can do this. Be quick 'cause this is gonna turn nasty!'
EXIT_LINE = 'Multiplayer/F04/ExitHeist_01_R'             # 'Get out on the street! straight ahead!' (F07's: '... to the back alley')

NO_AI = False                           # True ('--no-ai'): no squad stays, no F07 police - the round without enemies of
                                        # the first live run (the beat, the loot, the van and the music are as with them)

# ------------------------------------------------------------------ the enemies
# THE CAMPAIGN'S SQUADS THAT STAY: kl_fa_author.squad_plan's rule (a subtree of plain squad objects with an actor
# and a behaviour rout; mini-cutscene controllers come off), asked of the real function with these name roots.
# 22 squads / 53 men (re/campaign_fa_bank.md 4.1, 8.2). What does NOT stay under the rule: the six police-car
# squads, the shield SWAT, both helicopters, the snipers, the eight hall guards (no rout), the story's own crew
# (every ZMercSquad / ZFusionSquad: the vault breaker's vault sequence among them) and 22 civilians.
SQUAD_ROOTS = ('GamePlay!', 'COOP!')
G3, G4, G5, CO = 'GamePlay!3_Garage_Part!', 'GamePlay!4_Vault_Part!', 'GamePlay!5_Lobby!', 'COOP!Squads_Lobby!'
# squad -> stage. A squad whose ZSquadScript field 3 is 0 is NOT IN THE WORLD until one of its routs is named
# (re/map_ai.md 2: seen live on Retomoto, 'they spawn in'); wire() names the start rout squad_plan found, by stage:
#   'start'  dock and vault lobby, 13 guards: the round's start timer (SQUADS_AT)
#   'down'   the three guard pairs of the way down (upper flight, cross corridor, ante-room): with them
#   'beat'   14 police: the ante-room box. Their defend places run down the stairs towards the ante-room (the last of
#            'Vault_Reinforcement_Police_03' is (396, -956, -12332)): they come down behind the crew. Three of these
#            squads and two of 'start' have the campaign's hunt (HUNT), named when the beat ends
#   'plaza'  the front street's seven squads / 20 men (two SWAT fours with rifles): the foyer box
# GUESS: the split (the study's: re/campaign_fa.md 4.1 items 3 - 7); MEASURED: where each stands (check())
STAGE = collections.OrderedDict([
    (G3 + 'PatrolGuards_01a', 'start'), (G4 + 'Guards_Reinforcement_StayUpstairs', 'start'), (G4 + 'Guards_Reinforcement_StayUpstairs#01', 'start'),
    (G4 + 'Guards_Reinforcement_01a', 'start'), (G4 + 'Guards_Reinforcement_01b', 'start'),
    (G4 + 'Guards_01', 'down'), (G4 + 'Guards_02', 'down'), (G4 + 'Guards_03', 'down'),
    (G4 + 'Police_Reinforcement_02', 'beat'), (G4 + 'Police_Reinforcement_03', 'beat'), (G4 + 'Police_Reinforcement_Teargas_01', 'beat'),
    (G4 + 'Police_Reinforcement_Teargas_01#01', 'beat'), (G4 + 'Vault_Reinforcement_Police_01', 'beat'),
    (G4 + 'Vault_Reinforcement_Police_02', 'beat'), (G4 + 'Vault_Reinforcement_Police_03', 'beat'),
    (G5 + 'Police_OutSide_01', 'plaza'), (G5 + 'Police_Outside_Teargas_01', 'plaza'), (CO + 'Police_OutSide_SWAT_02', 'plaza'),
    (CO + 'Police_OutSide_SWAT_03', 'plaza'), (CO + 'Police_OutSide_SWAT_02_ShieldSupport', 'plaza'),
    (CO + 'Police_OutSide_SWAT_03_ShieldSupport', 'plaza'), (CO + 'Police_Reinforce_Wave1_COOP_03', 'plaza')])
# the rout a stage names, where it is not the one squad_plan finds (the lowest-named rout a campaign trigger names).
# The two single SWAT men's is '080_Cutscene_MoveOutside' - a place ON the van's stop ((894, 709, -11061), the stop is
# (949, 702, -11105)); their '050_Move_In_01' takes them into the banking hall instead, as the campaign's own
# modifier '040_' does: the police follow in while the crew comes out
START_ROUT = {CO + 'Police_OutSide_SWAT_02_ShieldSupport': '050_Move_In_01', CO + 'Police_OutSide_SWAT_03_ShieldSupport': '050_Move_In_01'}
# five squads have the campaign's hunt: a modifier '49_SquadMod' (unleash, fire at will) that names '50_HuntBehaviour',
# whose search box is IN THE VAULT (427, -733, -12986). Named when the beat ends: they come for the crew at the loot
HUNT = '49_SquadMod'
SQUADS_AT = 10.0                        # s from the round-start event to the first squads. That event comes when the 8 s
                                        # countdown BEGINS, 8.4 - 8.8 s before GO (kl_fa_author.BLAST_DELAY's note, two clock
                                        # readings); a squad that waits is not in the world, so nobody is shot in the countdown
                                        # through the open dock door (Retomoto's run S2). GUESS: 10
MAN_OFF, MAN_IN = 60.0, 15.0            # snap_men: a man this far beside the mesh at most is put this far inside it. GUESS
# WHERE THE 14 POLICE OF THE BEAT COME INTO THE WORLD. The campaign has them in the dock and the vault lobby (seven
# within 4.5 m of the route's own station there, the nearest 165 from it): right for a story in which everybody is
# down at the vault when they come, wrong here - the box fires for the FIRST criminal in the ante-room (an AI heister,
# some 35 - 40 s after GO), and a human still fighting the 13 guards upstairs would get 14 police out of the air at
# arm's length (review round 1). So their men are re-placed (strip: beat_men) BEHIND THE AIRLOCK, off the way in:
# eight in the corridor that leads from the airlock to the hall's stairs (x 1467..1625, flat floor y 240 from
# z -7125 to -6050; round the corner from the airlock's doorway) and six on the landing above its stairs (floor
# y 420). From there their own defend routs bring them through the airlock and the lobby and down: they still come
# down behind the crew, on foot. MEASURED (C:/kl_scratch/bank/fix_1/s/beat_floor.py): each place on the START's mesh
# part and on free collision floor, the nearest 1195 from a station of the way in. GUESS: the places themselves, and
# 100 - 125 between two men. ASSUMPTION: a defend rout walks its men from wherever they stand on the mesh.
# None: the campaign's places stay (check() then fails on BEAT_CLEAR)
BEAT_MEN = [(1510, 240, -6700), (1585, 240, -6610), (1510, 240, -6520), (1585, 240, -6430), (1510, 240, -6340), (1585, 240, -6250),
            (1510, 240, -6160), (1585, 240, -6070),
            (1510, 420, -5620), (1585, 420, -5540), (1510, 420, -5460), (1585, 420, -5380), (1415, 420, -5510), (1415, 420, -5400)]
BEAT_CLEAR = 1000.0                     # no man of a squad that comes later than the round's start nearer than this to a
                                        # station of the round that lies BEFORE the squad's trigger (check()). GUESS
SQUAD_ACTIVE = A.SQUAD_ACTIVE           # ZSquadScript field 3, 'in the world from the load': 1 on the dock patrol only; 0 is
                                        # written, so that it waits for the start timer like the rest (kl_fa_author.ROOM_WAITS:
                                        # SEEN LIVE on Retomoto, run GW2)
# THE SOLDIER ROWS. As converted the 53 are eGuard / eArmy with a skill NAME (eN00b 1, eAmateur 24, eRegular 16,
# eVeteran 12: the name overwrites accuracy with 20 / 35 / 50 / 60, re/map_ai.md 1) and health 50 (13 of them 120) -
# against stock Fragile Alliance police at 100 / 175. Retomoto's cure is kl_arms' stock rows by the class of the
# weapon handed out (the owner, after it: 'guards good'); that pass is tied to kl_arms.SKILL_LEVELS and skips a man
# whose first three floats are not 50 / 50 / 50 - ten of the bank's police have 2 / 50 / 50. So the same rows
# (kl_arms.ROWS by kl_arms.SKILL: pistol 'cop' 50 / 100, SMG and shotgun 'swat' 50 / 175, rifle 'sharp' 75 / 175)
# are written here, in wire(), for every man of a kept squad. False: Dead Men's rows stay
STOCK_ROWS = True
# THE BANKING HALL. The campaign's eight hall guards have no rout ('GuardSquadForCutSeq'); the hall is held by
# three of stock F07's own police squads, re-placed (eight men: 3 + 3 + 2, each 'eArmy eCustom'). A squad is a
# ZGROUP + ZSquadScript with identity rotation whose children's places are offsets (kl_fa_street's docstring);
# it moves by moving the group and re-laying the children. squad -> (anchor, actors' places, the points of
# '10_RunToCover', the point of '10_Defend'); the point of '40_RunToEscape' (which nothing names here) goes to
# the anchor. Stock starts each from a box by naming '10_RunToCover'; here the beat's timer does (the alarm):
# they are in the hall when the crew comes up from the vault. GUESS: every point - MEASURED only that each is on
# the START's mesh part and on free floor (check()). The hall's floor is y 800; its middle (x 100..500,
# z -8200..-7000) and five rows of furniture (z -8800, -8200, -7600, -7000, -6400) are no mesh.
HALL_Y = 801.0
G30 = 'Gameplay!030_AfterLoot!'
HALL = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((-300, HALL_Y, -8600), [(-500, -9000), (-300, -9000), (-100, -9000)],       # the west side
                                           [(-500, -8400), (-300, -7800), (-500, -7200)], (-100, -8000))),
    (G30 + '030_FinancialAlleyExit_Right', ((900, HALL_Y, -8600), [(700, -9000), (900, -9000), (1100, -9000)],         # the east side
                                            [(1100, -8400), (900, -7800), (1100, -7200)], (700, -8000))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((300, HALL_Y, -8900), [(100, -9000), (500, -9000)],                   # before the entrance
                                                 [(100, -8600), (500, -8600)], (300, -8600)))])
HALL_START = '10_RunToCover'
# (review after run V2: nothing names '10_Defend' - '10_RunToCover' has an empty next list - so the hall's squads stay
# at their cover points for good; the table's last column is a place that is laid and never walked to.)

# ------------------------------------------------------------------ the crew fix after live run V2
# RUN V2 (2026-10-11, the full map, an idle human; re/bank_campaign.md 'Run V2, diagnosed from the build' and 'Crew fix
# after run V2'). MEASURED on its log: the AI heisters walked the right order - down, the vault's 2,300,000, up again -
# and five of them died in the BANKING HALL ON THE WAY OUT: 8 hall police stood in a row before the only exit, their
# places 39 .. 174 from the heisters' own on both aisles (two deaths by the point-blank rule,
# re/melee_damage.md), and the foyer box sent the plaza's 20 into the hall and onto its gallery through the 2 m front
# entrance (a SWAT flank point lies IN that gap). 28 guns on a 36 m crossing, the plaza left empty.
# Nobody is taken out: 61 men stay. What changes is WHERE the two fights are - the hall is held from its gallery by
# F07's eight, the plaza by the campaign's twenty - and that the heisters cross the hall without a stop.
# Every flag is OFF by default (= the level of runs V0 .. V2, <work>/build/c_bank); 'test --crew-fix' sets both.
#
# 1. PLAZA_OUTSIDE ('--plaza-outside'): the plaza's squads stay outside.
#    PLAZA_PLACES: squad -> {a place of one of its routs: (x, z) on the plaza's floor}. The campaign's flank points
#    (five squads, ten places: six on the hall's gallery, four on its floor), the two shield men's '050_Move_In_01'
#    and COOP_03's 'Cutscene_MoveOutside' (its Pos#01 stood 125 from a heister's place on the plaza) go to the two
#    sides of the plaza in front of the bank, west x -1450 .. -600, east x 1150 .. 1700, z -10650 .. -9900. GUESS:
#    every place. MEASURED (plaza_places on the campaign's mesh, check() and crew_check on each build): on the
#    START's mesh part and on free floor, clear of every place of an AI heister by CREW_CLEAR. West squads keep
#    the west side and east the east: nobody crosses in front of the door.
#    ASSUMPTION: a flanking rout sends its men to its two places and they fight from there; the two SWAT fours are
#    'eUnleashed' in the campaign and may come in after the crew all the same - which is a fight at the door, not
#    twenty men set up in the hall.
#    PLAZA_BOX: they are started by a box across the hall's SOUTH end (z -9200 .. -8200, the last 10 m before the
#    front entrance), not by the foyer box 36 m earlier: the police arrive while the crew leaves, instead of standing
#    set up before the one door for the 20 - 40 s the hall takes. The box is stock F07's own 'tbExitFinancialAlley'
#    - the very box that starts these hall squads' '10_RunToCover' in F07 (field 0 = 1, field 15 = 0: fires once) -
#    re-placed; a free object of the host (the list at ROLE). GUESS: the box's place.
#    Their men come into the world where the campaign has them: on the street at the bank's two corners
#    (x -2269 .. -1415 and 1968 .. 2201, z -9690 .. -9397), 17 m and more to either side of the front entrance.
PLAZA_OUTSIDE = False
PLAZA_BOX = 'Gameplay!030_AfterLoot!tbExitFinancialAlley'
PLAZA_BOX_AT = ((300, 930, -8700), (1700, 400, 500))            # place, half extents: x -1400..2000, y 530..1330 (the gallery too), z -9200..-8200
PLAZA_Y, PLAZA_UP = 700.0, 5.0          # the plaza's floor (the mesh's own height is taken); a place stands this far over it (the campaign's: 1 .. 11)
PLAZA_PLACES = collections.OrderedDict([
    (G5 + 'Police_OutSide_01', {'30_FlankingBehaviour\\LeftFlank#1': (-700, -9930), '30_FlankingBehaviour\\RightFlank#1': (-1150, -9900)}),
    (G5 + 'Police_Outside_Teargas_01', {'30_FlankingBehaviour\\LeftFlank#1': (1250, -10000), '30_FlankingBehaviour\\RightFlank#1': (1600, -9930)}),
    (CO + 'Police_OutSide_SWAT_02', {'FlankingBehaviour\\LeftFlank#1': (-1050, -10600), 'FlankingBehaviour\\RightFlank#1': (-830, -10600)}),
    (CO + 'Police_OutSide_SWAT_03', {'FlankingBehaviour\\LeftFlank#1': (1410, -10650), 'FlankingBehaviour\\RightFlank#1': (1700, -10600)}),
    (CO + 'Police_OutSide_SWAT_02_ShieldSupport', {'050_Move_In_01\\Pos#01': (-1450, -10050)}),
    (CO + 'Police_OutSide_SWAT_03_ShieldSupport', {'050_Move_In_01\\Pos#01': (-1450, -10350)}),
    (CO + 'Police_Reinforce_Wave1_COOP_03', {'FlankingBehaviour\\LeftFlank#1': (-600, -10200), 'FlankingBehaviour\\RightFlank#1': (1200, -10150),
                                             'Cutscene_MoveOutside\\Pos#01': (1150, -10350), 'Cutscene_MoveOutside\\Pos#02': (-650, -10380)})])
# 2. HALL_UP ('--hall-gallery'): F07's eight hall police on the hall's GALLERY (floor y 1220: both long sides,
#    x -764 .. -515 and 1115 .. 1381 from z -9284 to -6380, and the north end over the foyer door; four stairs at the
#    corners), in HALL's form with a height of its own per point. The three of each long side come into the world in
#    a group at the gallery's south end (x -1000 .. -800 / 1400 .. 1600, z -9100) and run to three places along the
#    rail; the pair of 'ExitStreet_Left' stands at the two north corners. So the hall is held from above on three
#    sides, the floor - both aisles and the east wall's way, all of which the heisters use - is the crew's, and no
#    policeman's place is within the point-blank rule's reach of a heister's (the nearest 420, straight up).
#    GUESS: every place. MEASURED (C:/kl_scratch/vault_fix/fix/cand.py on the delivered folder; check() on each
#    build): each on the START's mesh part and on free floor.
HALL_UP = False
GAL_Y = 1221.0
HALL_GALLERY = collections.OrderedDict([
    (G30 + '030_FinancialAlleyExit_Left', ((-640, GAL_Y, -8000), [(-1000, GAL_Y, -9100), (-900, GAL_Y, -9100), (-800, GAL_Y, -9100)],      # the west gallery
                                           [(-600, GAL_Y, -8700), (-600, GAL_Y, -7900), (-600, GAL_Y, -7100)], (-640, GAL_Y, -8300))),
    (G30 + '030_FinancialAlleyExit_Right', ((1250, GAL_Y, -8000), [(1400, GAL_Y, -9100), (1500, GAL_Y, -9100), (1600, GAL_Y, -9100)],     # the east gallery
                                            [(1200, GAL_Y, -8700), (1200, GAL_Y, -7900), (1200, GAL_Y, -7100)], (1250, GAL_Y, -8300))),
    (G30 + '030_FinancialAlleyExitStreet_Left', ((300, GAL_Y, -6100), [(-700, GAL_Y, -6100), (1350, GAL_Y, -6100)],                       # its two north corners
                                                 [(-600, GAL_Y, -6600), (1250, GAL_Y, -6600)], (300, GAL_Y, -6000)))])
# the banking hall with its gallery, for the tests: (x), (y), (z). MEASURED: the mesh's hall polygons lie inside it,
# the plaza squads' own men (x beyond -1415 / 1968) and every place of PLAZA_PLACES outside
HALL_BOX = ((-1200.0, 1800.0), (700.0, 1400.0), (-9450.0, -5750.0))
# 3. THE HEISTERS CROSS THE HALL IN ONE GO (hall_dash, 'kl_fa_bank.py hall-dash <folder>': a step of the finishing
#    chain after kl_fa_bots_dyn's and before seal). Run V2: three of the five died standing 9 - 25 s at cover holds
#    of the dynamic step in the open hall (its timers say 4 - 8 s; a bot under fire stays in its Defend place).
#    Every Defend step of an AI heister squad with a place inside DASH_BOX - the hall's floor from its first row of
#    furniture to the front entrance; the foyer, where the crew comes up, is NOT in it - gets 'eDMS_Sprint' (the
#    dynamic step's own form for the last dash to the van) and the hold timers those steps start go to 0 s (its own
#    form too: the first bot's '000_Timer_stagger' is 0 s). GUESS: that a sprint through is better than a hold
#    under fire from above; the box's north edge.
DASH_BOX = ((-1200.0, 1800.0), (700.0, 1000.0), (-9420.0, -6400.0))
DASH_MOVE, DASH_HOLD = 'eDMS_Sprint', '_Timer_hold'
# ------------------------------------------------------------------ the waves build (2026-10-11 night; every flag OFF by default)
# See re/bank_campaign.md 'Waves'. NOT RUN IN THE GAME. All of it is behind named flags; no flag = the build of the crew fix.
# CREW_FIX2 ('--crew-fix2'): the three open review points of the crew fix.
#   (a) DASH_BOX's north edge z -6400 -> DASH_NORTH, the foyer-to-hall door (READ: mesh polygon 815, x 235..364,
#       z -5799..-5744; the four live 6 - 8 s holds of Squad#04 / #07 lie at z -6235 .. -6116 and are inside the dash now;
#       the foyer room, z > -5744, is left alone). GUESS: that the door is where a hold stops being wanted.
#   (c) a dash step named [hold timer, RandomTrigger of covers] in ONE list with a 0 s timer: no precedent. The review's cure (the
#       cover branch out) does not check (DASH_CUT_COVER); the fallback is a hold timer of DASH_GAP seconds.
CREW_FIX2 = False
DASH_NORTH, DASH_GAP = -5800.0, 1.5
DASH_CUT_COVER = False                  # True: the review's own fix (c), the cover branch out of the dash steps' lists. TRIED, DOES NOT CHECK: the
                                        # cover steps and the RandomTrigger are then named by nothing and kl_fa_bots_dyn.check FAILS ('N step(s)
                                        # nothing starts', 4 squads); taking the nodes out needs an entity removal below the top level that
                                        # kl_prpjoin.join does not offer. FALLBACK (the default): the hold timer of a dash step is DASH_GAP
                                        # (1.5 s) - the form that ran live (a cover rout and a hold timer in one list, V0 .. V2: 4 - 8 s) with
                                        # a shorter number, instead of the 0 s of the crew fix, which has no precedent at all
# TELLER_LATE ('--teller-late'): the four teller stacks lie hidden from the load and come with the vault's loot when the
# beat ends (the proven form of hidden loot, 'loot on'). Review point (b): MEASURED that a stack pulls a bot sideways only
# inside the loot window (800 / 400 round it, kl_fa_bots); the crew crosses the hall only on the way OUT with the vault's
# money, so hiding them until the beat removes the pull on the way in (none: the way in does not touch the hall) and NOT on
# the way out. The way out's pull stays: it costs the dash seconds, not lives (GUESS). The lead decides about more.
TELLER_LATE = False
# VAN_LATE ('--van-late'): the owner, 2026-10-11 ~21:45: 'all the police outside the vault shoot the van straight away'.
# The van waits on the square from the load, in sight (re/bank_campaign.md L3.4), and carries F07's ZFakeTarget of faction
# 'Mercenary' (MEASURED: FakeTarget ['Mercenary', ...] on V_Van_00\Body\Body_Main) - the thing a police squad aims at.
#   hide: the van's group is hidden from the load and shown (ActivateGeom) VAN_SHOW s after the plaza box (the crew is in
#         the hall's south end then, 12 .. 20 s from the exit box). ASSUMPTION: a hidden keyed vehicle is fine until shown
#         (not seen: the first live run decides; '--no-van-hide' keeps the van where it stood).
#   no target ('--van-no-target', in VAN_LATE): the FakeTarget controller is taken off the van. ASSUMPTION that police aim at
#         it for that reason. The 0x686a66 rule (a FakeTarget outside the vision space) cannot bite with none. A waiting
#         van that keeps one does so because every stock van has one (12 vans of F01 F04 F05 F07).
VAN_LATE, VAN_HIDE, VAN_NO_TARGET, VAN_SHOW = False, True, True, 1.0     # shown 1 s after the plaza box (was 4: the review of the waves build measured the box 28 m before the exit trigger, ~5 s of a sprint)
VAN_BACKSTOP = 120.0                    # ... and, should that box never fire with bots in the crew, 120 s after the ante-room box (the van is no police target: its FakeTarget is off). GUESS
TELLER_SHOW = 20.0                      # TELLER_LATE: the teller stacks are shown this long after the plaza box = once the AI heisters' hall dash is past the registers (review fault 4:
                                        # at 2 s a bot at the box was still inside the loot window, 800, of a stack and was pulled back). GUESS: 20 s = ~60 m of a dash
# TELLER_MORE ('--teller-more', on with --waves): the owner, 21:45: 'put some money in the cash registers up top so people could hold the swat from coming in and get rewarded'.
# Six counters stand in the hall (x -791 and x 1393, z -7202 / -7602 / -8002 and -7206 / -7606 / -8006); the module used the outer four. The middle two get a stack
# too and every stack is worth TELLER_MORE_VALUE: 6 x 100,000 instead of 4 x 75,000. All on the public side, on the START's mesh (checked in check()). GUESS: the number.
TELLER_MORE, TELLER_MORE_VALUE = False, 100000
TELLER_MORE_EXTRA = [(-765.0, 899.0, -7602.0), (1367.0, 899.0, -7606.0)]
VAN_FOYER = 6.0                         # the van is also shown this long after the FOYER box (Specials!LevelSpeak!TriggerBox, 30 m before the plaza box = 6 .. 10 s of a sprint
                                        # earlier; ActivateGeom twice is idempotent). The plaza box has never fired live in the Vault (review fault 6). GUESS: the margin
# RESET ('--reset'): the owner, ~22:00: 'after the first round the vault door is open'. See Reset below.
RESET = False
# WAVES ('--waves'): police that keep coming. See waves() below.
WAVES, WAVES_EXTRA, WAVES_NEAR = False, 54, 250.0
OPTS_FILE = 'bank_opts.json'
DASH_BOX_V1 = DASH_BOX
# 4. THE TEST (crew_check, 'kl_fa_bank.py crew-check <folder>'): no place of an AI heister squad within CREW_CLEAR of
#    a man's start, a cover point, a flank point or a defend place of a squad of the hall or the plaza. 160 is the
#    point-blank rule's reach (kl2 0x8c62e0, re/melee_damage.md); GUESS: the margin of 240. The delivered folder of
#    runs V0 .. V2 FAILS it (39 in the hall, 43 at the front entrance: 28 of its 60 men and places).
CREW_CLEAR = 400.0

# ------------------------------------------------------------------ the beat
# the six locking rods of the vault door, in the campaign's order (its 'MatPosAnimProxy_Rod#01..#06' play frames
# 1..60 on each; the proxies sit inside the vault breaker's ZMercSquad, which cannot stay). Each rod has a
# MatPosAnim of its own with the in-message 'Activate' and stores -1 / -1 = its whole clip, one way
# (re/campaign_fa.md G1.8): a host AIDWrapper sends it. THE RODS ARE SHOW: the gate is the beat's timer
VE = VA + 'M03_A_VaultEntrance_01a\\'
RODS = [VE + 'Rod_%s01' % c for c in 'ABCDEF']
ROD_FIRST, ROD_STEP = 2.0, 8.0          # s from the ante-room box to the first rod, and between rods. GUESS (the study: 8 s)
# the campaign's single nodes that stay (campaign_names), by the job they have in wire(). Each keeps the list the
# campaign gave it unless wire() says otherwise
AUDIO = 'Special!Audio!'
CAMP = collections.OrderedDict(
    [('rod sound %d' % (i + 1), AUDIO + n) for i, n in enumerate(['GeomActivator_PlaysoundVaultRod0%d' % j for j in range(1, 6)] + ['GeomActivator_PlaysoundFinalRod'])] + [
     ('door sound', AUDIO + 'GeomActivator_PlaysoundVaultOpen'),                # ActivateGeom -> Audio!3D!Doors!Vault_Door_Open
     ('alarm sound', AUDIO + 'GeomActivator_PlaysoundAlarm'),                   # ActivateGeom -> Audio!3D!Alarm_01 / _02
     ('alarm lamps', G3 + 'Activator_AlarmRedLights'),                          # AIDWrapper 'Activate' -> the 11 lamps
     ('lights off', G3 + 'GeomDeactivator_Lights'),                             # DeactivateGeom -> the vault lobby's white light
     ('boom 1', G4 + 'BoomBox_BlowVault#01'), ('boom 2', G4 + 'BoomBox_BlowVault#02'), ('boom 3', G4 + 'BoomBox_BlowVault#03'),
     ('blast sound', G4 + 'Activator_SetOffAlarm'),                             # AIDWrapper 'Activate', empty in the campaign
     ('music', AUDIO + 'PlayMusic_Outside'),                                    # 4 layers 'BO_Sus_LOOP' + 41 layer fades
     ('music out', AUDIO + 'PlayMusic_Inside_Part2')])                          # 'M03A_Bustout_A_I' + 3 layer fades
# THE ALARM LAMPS: eleven 'Pc0100_M03_LampAlarm_Wall_*' in the vault lobby, both stair rooms and the ante-room. Each
# is a group with a RelayMessageList 'Activate' -> its glow (VertAnim) and its two lights, an omni and a spinning
# spot, which hold a LightToggle (state OFF, on at 'Activate'). LightToggle is registered in kl2.exe and used by NO
# stock Dog Days level: 'kl_maps.py preflight' calls the 22 a RISK (re/campaign_fa_bank.md 3.4). So, the lead's rule:
#   False (default)        the 22 LightToggle are TAKEN OFF before the join and the 22 lights - and the 8 slave spots
#                          the spinning ones have in the rooms next door - hidden (ZGEOM[3] = 1 and
#                          the .gms flag, the form the level's own fire lights have): the first live load runs no
#                          LightToggle code. The lamps still get 'Activate' at the alarm - their glow plays, no light.
#                          ASSUMPTION that a hidden light does not shine; if it does, eleven red lamps are lit all round
#   True ('--alarm-lights') the controllers stay; at the alarm the lamps light and the vault lobby's white halogen
#                          rows go off, as the campaign has it (its 'Timer_Alarm' names the same three objects)
ALARM_LIGHTS = False
LAMP = 'Pc0100_M03_LampAlarm_Wall_'
SLAVES = 'ZGateLightSpot[3]'            # a gate light's list of slave spots (8 of the 11 spinning spots reach into the room next door)
# THE VAULT'S OWN BLAST. The campaign blows the deposit boxes 15 s after the charges are set: three 'BoomBox'
# (Explode + its own AIDWrapper, #01 also a ShakeCamera), the explosion sound, the intact vault 'Vault_PRE' off and
# the blown one 'Vault_POST' on (26 objects each way: walls, overlays, burnt ceiling, the ante-room's carpet), the
# fire and smoke groups on. Here it goes off DOOR_GONE seconds after the door's 'Activate' - at the moment the
# door's body is switched off, so a door that did not swing is 'blown away'. The lists are the campaign's own, read
# from the stock level (blast_lists) less what is not in the build.
#   'show' (default, the lead's)  harmless: the Explode's two radii are set to 1 (kl_fa_author.BLAST_HARMLESS; GUESS
#                                 that fields 0 / 1 are its reach - a rocket 500 / 150, a gas tank 600 / 400)
#   'real' ('--blast-real')       the campaign's values: 1300 / 1000 and 800 / 800, field 4 = 30 (a stock grenade has
#                                 350 there, a gas tank 1000: GUESS that it is the damage, so even 'real' is a light hit)
#   None ('--no-blast')           the vault stays intact; nothing of the blast is named
# The fire is a picture in both: the campaign's two 'FireDamageBox' (EffectDmgBox, a kind no stock Dog Days level
# runs) are not kept.
VAULT_BLAST = 'show'
EXPLODE_REACH = (0, 1)                  # Dog Days Explode fields (18 in all), as kl_fa_author's wire() writes them
BLAST_FROM = 'GamePlay!4_Vault_Part!MercSqd_Valutbreaker_BlowingBoxes\\50_BlowingVault_RigC_DONOTDELETE\\'
BLAST_LISTS = {'post on': ('GeomActivator_POST_Vault', 'GeomActivator_Efx_Geoms'), 'pre off': ('GeomDeactivator_PRE_Vault',)}
BLAST_SOUND = 'Locations/M03_A/M03A_Audio.zip!Audio!3D!Sound_VaultExplosion'
VAULT_PRE, VAULT_POST = VA + 'M03_A_Vault_01a\\Vault_PRE', VA + 'M03_A_Vault_01a\\Vault_POST'
# THE MUSIC, wired through the campaign's own PlayMusic objects (they are silent until the stream file holds the
# clips: MUSIC_CLIPS, for the owner's go-ahead - kl_str.py builds no file here). The break-in set from the start;
# at the ante-room box the campaign's 'guards under fire' fades; when the beat ends its four 'vault explosion' fades
# (every layer to silence in 1 s) and the way-out set, which the campaign starts at the same place
# THE FOURTH LAYER. The break-in set has four layers and nine of its fades work on 'eLayer4' ('basic', the one that
# sounds from the start: -14 dB, the others silent). Dog Days' enum has the value, but no stock level fades a fourth
# layer: 'kl_maps.py preflight' calls the nine a RISK ('value'). The lead's rule for the alarm lamps, here too:
#   False (default)         the nine lose their PlayMusicLayerFade before the join and nothing names them. With the
#                           clips in the stream file the 'basic' layer then plays on under the way-out set
#                           (ASSUMPTION: a second PlayMusic does not stop the first - the campaign fades all four out
#                           before it starts the next): the stage that brings the music sets the flag
#   True ('--music-layer4') they stay and '03_Basic' / '23_Basic' are named with the rest
MUSIC_LAYER4 = False
LAYER4 = 'eLayer4'
MUSIC_AT = 1.0                          # s from the round-start event. GUESS
MUSIC_RISE = ('03_Ambient', '03_Basic', '03_Intense')
MUSIC_FADE = ('23_Ambient', '23_Basic', '23_Bass', '23_Intense')
MUSIC_CLIPS = ('Music/InHouse/M03A/BO_Sus_Layer1_Ambient_LOOP.wav', 'Music/InHouse/M03A/BO_Sus_Layer2_Bass_LOOP.wav',
               'Music/InHouse/M03A/BO_Sus_Layer3_Intense_LOOP.wav', 'Music/InHouse/M03A/BO_Sus_Layer4_Basic_LOOP.wav',
               'Music/InHouse/M03A/M03_Bustout_ActionV34.wav', 'Music/InHouse/M03A/M03_Bustout_IntenseClimax_Loop.wav')
_plan = {}


def rod_times():
    """Seconds from the ante-room box to each rod: ROD_STEP apart, nearer when BEAT is short ('--beat'): the last rod
    goes at least 4 s before the door."""
    step = min(ROD_STEP, max(0.5, (BEAT - ROD_FIRST - 4.0) / (len(RODS) - 1)))
    return [ROD_FIRST + i * step for i in range(len(RODS))]


def squad_plan():
    """kl_fa_author.squad_plan(M03_A) -> ({squad: (path of its start rout, actors, stripped kinds)}, {left: why}).
    That function reads its name roots from its own table SQUADS, which has Retomoto's two levels: the bank's
    entry is lent to it for the length of the call (no file of that module is edited)."""
    if NO_AI:
        return {}, {'*': 'a build without enemies (NO_AI)'}
    if 'plan' not in _plan:
        had = A.SQUADS.get(LEVEL)
        A.SQUADS[LEVEL] = SQUAD_ROOTS
        try:
            keep, left = A.squad_plan(LEVEL)
        finally:
            if had is None:
                del A.SQUADS[LEVEL]
            else:
                A.SQUADS[LEVEL] = had
        if set(keep) != set(STAGE):
            raise ValueError('kl_fa_bank: the squads that can stay are not the %d of STAGE: only in the plan %s, only in STAGE %s' % (
                len(STAGE), sorted(set(keep) - set(STAGE)), sorted(set(STAGE) - set(keep))))
        _plan['plan'] = keep, left
    return _plan['plan']


# ------------------------------------------------------------------ the options that travel with a build
def set_dash():
    """DASH_BOX for the flags in force (CREW_FIX2 moves its north edge to the foyer door)."""
    global DASH_BOX
    DASH_BOX = (DASH_BOX_V1[0], DASH_BOX_V1[1], (DASH_BOX_V1[2][0], DASH_NORTH if CREW_FIX2 else DASH_BOX_V1[2][1]))


def opts_now():
    return collections.OrderedDict(crew_fix2=CREW_FIX2, teller_late=TELLER_LATE, van_late=VAN_LATE, van_hide=VAN_HIDE, van_no_target=VAN_NO_TARGET,
                                   van_show=VAN_SHOW, reset=RESET, waves=WAVES, waves_extra=WAVES_EXTRA, waves_near=WAVES_NEAR,
                                   plaza_outside=PLAZA_OUTSIDE, hall_up=HALL_UP, no_ai=NO_AI, teller_more=TELLER_MORE, waves_latch=WAVES_LATCH,
                                   waves2=WAVES2, voice=VOICE, teller_foyer=TELLER_FOYER, room_gates=ROOM_GATES, room_on=list(ROOM_ON), room_hide=ROOM_HIDE, staging=STAGING, garrison=GARRISON,
                                   **({'vault_swing': VAULT_SWING_END} if VAULT_SWING_END is not None else {}),
                                   **({'vault_blocker': True} if VAULT_BLOCKER else {}),
                                   **({'vault_blow': True} if VAULT_BLOW else {}))


def apply_opts(o):
    """Set the module's flags from a dict (opts_now's form). -> o"""
    global CREW_FIX2, TELLER_LATE, VAN_LATE, VAN_HIDE, VAN_NO_TARGET, VAN_SHOW, RESET, WAVES, WAVES_EXTRA, WAVES_NEAR, TELLER_MORE, WAVES_LATCH
    global WAVES2, VOICE, TELLER_FOYER, WAVE_TABLE, ROOM_GATES, ROOM_ON, ROOM_HIDE, STAGING, GARRISON, VAULT_SWING_END, VAULT_BLOCKER, VAULT_BLOW
    VAULT_BLOW = bool(o.get('vault_blow', False))
    GARRISON = bool(o.get('garrison', False))
    VAULT_SWING_END, VAULT_BLOCKER = o.get('vault_swing'), bool(o.get('vault_blocker', False))
    ROOM_GATES, ROOM_HIDE = bool(o.get('room_gates', False)), bool(o.get('room_hide', True))
    STAGING = bool(o.get('staging', False))
    ROOM_ON = tuple(o.get('room_on', ROOM_ON))
    TELLER_MORE, WAVES_LATCH = bool(o.get('teller_more')), bool(o.get('waves_latch', False))
    WAVES2, VOICE, TELLER_FOYER = bool(o.get('waves2')), bool(o.get('voice')), bool(o.get('teller_foyer'))
    WAVE_TABLE = chain_table(v2=WAVES2)
    CREW_FIX2, TELLER_LATE, VAN_LATE = bool(o.get('crew_fix2')), bool(o.get('teller_late')), bool(o.get('van_late'))
    VAN_HIDE, VAN_NO_TARGET, VAN_SHOW = bool(o.get('van_hide', True)), bool(o.get('van_no_target', True)), float(o.get('van_show', VAN_SHOW))
    RESET, WAVES, WAVES_EXTRA, WAVES_NEAR = bool(o.get('reset')), bool(o.get('waves')), int(o.get('waves_extra', 54)), float(o.get('waves_near', 250.0))
    set_dash()
    return o


def write_opts(folder):
    import json
    with open(os.path.join(folder, OPTS_FILE), 'w') as f:
        json.dump(opts_now(), f, indent=1)


def read_opts(folder):
    """The flags a folder was built with (bank_opts.json, written by test()); a folder without the file is the build of the
    crew fix or older: every flag of this section off. -> dict, and the module's flags are set from it."""
    import json
    p = os.path.join(folder, OPTS_FILE)
    if not os.path.isfile(p):
        return apply_opts({})
    return apply_opts(json.load(open(p)))


# ------------------------------------------------------------------ small tools
def facing(p, face):
    """(dx, dz) of a table's facing: a direction as it stands, or the way from p to a place (x, y, z)."""
    if len(face) == 2:
        return face
    return (face[0] - p[0], face[2] - p[2])


def put(S, name, pos=None, face=None, half=None, hidden=None):
    """kl_fa_author.place, with a box laid in the world's axes (F07's own turn of a re-placed box means nothing here)."""
    return A.place(S, name, pos, face, half, hidden, turn=BOX if face is None and half is not None else None)


def values(sc, k, name):
    return [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][A.ctrl_of(sc, k, name)][1][1:-1])]


def world_of(e):
    """World place and rotation (rows) of an entity of a kl_scene.Scene, composed up its parents (kl_maps.world's rule)."""
    chain = []
    while e is not None:
        chain.append(e); e = e.parent
    Rm, T = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], (0.0, 0.0, 0.0)
    for e in reversed(chain):
        r = struct.unpack('<9f', e.rot[:36]); t = struct.unpack('<3f', e.trans[:12])
        m = [r[6:9], r[3:6], r[0:3]]
        m = [[m[j][i] for j in range(3)] for i in range(3)]
        T = tuple(T[i] + sum(Rm[i][j] * t[j] for j in range(3)) for i in range(3))
        Rm = [[sum(Rm[i][k] * m[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return T, Rm


# ------------------------------------------------------------------ 1. the host level before the graft
def van_plan(src, log=print):
    """The plan of ROAD (kl_map_escape.van_plan_points) against the collision of a BUILT F07 + M03_A folder WITHOUT
    the layer (a bare 'kl_maps.py one <out> F07 M03_A --campaign --keep': on a build that has the van, the planner
    takes the van's own camera for a designer's and lists it to be left out). A fault of the plan is an error."""
    P = ESC.van_plan_points(src, log=log, **ROAD)
    if P['faults']:
        raise ValueError('kl_fa_bank: no van on ROAD: %s' % '; '.join(P['faults']))
    return P


def plan_of(path):
    """A plan from a file: the JSON 'kl_map_escape.py van-plan ... --json' prints, or the van.json test() writes
    beside a build (the plan is its 'plan')."""
    import json
    with open(path, encoding='utf-8') as f:
        P = json.load(f, object_pairs_hook=collections.OrderedDict)
    P = P.get('plan', P)
    lack = [k for k in ('path', 'lin', 'lout', 'wait', 'stop', 'end', 'board', 'cam', 'points') if k not in P]
    if lack or P.get('faults'):
        raise ValueError('%s is no plan of the van without a fault (lacks %s; faults %s)' % (path, lack, P.get('faults')))
    road = {k: [list(map(float, p)) for p in v] if k in ('arrive', 'leave') else list(map(float, v)) if k == 'stop' else v for k, v in ROAD.items()}
    if any(P['points'].get(k) != v for k, v in road.items()):
        raise ValueError('%s is a plan of other way points than ROAD: %s' % (path, {k: P['points'].get(k) for k in road if P['points'].get(k) != road[k]}))
    return P


def lay_van(P):
    """The plan the next build lays the van on (prepare_host, wire). -> P."""
    global PLAN
    PLAN = P
    return P


def van_path():
    return R + VAN + '\\' + VAN_GROUP


def place_hall(S, log=print):
    """F07's three police squads of HALL into the banking hall: the group to its anchor, every child that has a
    place of its own (a non-zero local translation under parents that have none: actor groups, the points of the
    routs) to its place of the table, as an offset from the anchor. -> [(squad, actors)]"""
    sc, out = S.prp, []
    tr = lambda k: struct.unpack('<3f', S.ents[k - 1].trans[:12])
    y3 = lambda p: (p[0], HALL_Y, p[1]) if len(p) == 2 else tuple(p)    # HALL: (x, z) on the hall's floor; HALL_GALLERY: (x, y, z)
    for name, (anchor, actors, cover, defend) in (HALL_GALLERY if HALL_UP else HALL).items():
        top = A.node_of(sc, name)
        turned = max(abs(a - b) for a, b in zip(struct.unpack('<9f', S.ents[top - 1].rot[:36]), A.rot9(BOX)))
        if not kl_fa.has(sc, top, 'ZSquadScript') or turned > 1e-3 or not sc.resolve(R + name + '\\' + HALL_START):
            raise ValueError('%s: not a squad group without a turn that has a %s' % (name, HALL_START))
        own = []
        def go(k):
            for c in range(k + 1, sc.end[k]):
                if sc.parent[c] == k:
                    own.append(c) if any(abs(v) > 0.5 for v in tr(c)) else go(c)
        go(top)
        by = collections.defaultdict(list)
        for k in own:
            by['actors' if any(sc.cls(c) == 'ZFFActor' for c in range(k, sc.end[k])) else sc.names[sc.parent[k]]].append(k)
        want = {'actors': [y3(p) for p in actors], '10_RunToCover': [y3(p) for p in cover], '10_Defend': [y3(defend)], '40_RunToEscape': [anchor]}
        if {k: len(v) for k, v in by.items()} != {k: len(v) for k, v in want.items()}:
            raise ValueError('%s: placed children %s, the table has %s' % (name, {k: len(v) for k, v in by.items()}, {k: len(v) for k, v in want.items()}))
        A.place(S, top, anchor)
        for kind, ks in by.items():
            for k, p in zip(ks, want[kind]):
                A.place(S, k, tuple(p[a] - anchor[a] for a in range(3)))
        out.append((name, len(by['actors'])))
    log('  kl_fa_bank: the banking hall: %d of F07\'s police squads re-placed (%d men) %s; the beat\'s timer names their %s' % (
        len(out), sum(n for _s, n in out), 'ON ITS GALLERY (HALL_UP)' if HALL_UP else 'on its floor', HALL_START))
    return out


def prepare_host(S, log=print):
    """Re-place F07's Fragile Alliance layer for the bank. S: kl_graft.Level('F07'), unedited."""
    sc = S.prp
    if PLAN is None:                                    # before anything is armed: a caller that goes on in this process must
        raise ValueError(NO_PLAN)                       # not find kl_escape wrapped (review round 1)
    Doors.arm(log)                                      # the build that follows opens the doors (see Doors)
    for name, (pos, face, half, _why) in PLACE.items():
        put(S, name, pos, face, half)
    for name in PARKED:
        put(S, name, PARK)
    if PLAZA_OUTSIDE:                                   # the box that starts the plaza's squads: across the hall's south end
        if not kl_fa.has(sc, A.node_of(sc, PLAZA_BOX), 'TriggerBox'):
            raise ValueError('%s is no TriggerBox' % PLAZA_BOX)
        put(S, PLAZA_BOX, PLAZA_BOX_AT[0], None, PLAZA_BOX_AT[1])
        log('  kl_fa_bank: PLAZA_OUTSIDE: %s re-placed across the hall\'s south end: (%d, %d, %d), half extents %s' % (PLAZA_BOX, *PLAZA_BOX_AT[0], PLAZA_BOX_AT[1]))
    # spawn points by kind, and the sixteen player groups (a direct boot starts at Heroes!Hero_01)
    seen = collections.Counter()
    for t in sc.tops():
        if sc.cls(t) == 'ZSpawnPoint':
            kind = kl_fa.node_values(sc, t)[8]
            if kind not in SPAWN:
                raise KeyError('%s: no place for spawn points of kind %s' % (sc.names[t], kind))
            pts, d, face = SPAWN[kind]
            p = pts[seen[kind] % len(pts)]
            p = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            A.place(S, t, p, turn=facing(p, face))      # a spawn point looks along local +Z (kl_fa_author: SEEN LIVE)
            seen[kind] += 1
        elif sc.names[t].startswith('Heroes!'):
            crook = sc.names[t].startswith('Heroes!Hero_0')
            pts, face = (START, TO_DOOR) if crook else (POLICE, FRONT)
            n = seen[crook, 'hero']
            p = pts[n % len(pts)]
            if not crook:
                p = tuple(p[a] + HENCH_SHIFT[a] * (n // len(pts) + 1) for a in range(3))
            A.place(S, t, p, facing(p, face))           # ... a player group along local -Z
            seen[crook, 'hero'] += 1
    log('  kl_fa_bank: spawn points placed: %s' % {str(k).replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''): v for k, v in seen.items()})
    # loot: stacks of F07's drop pools become loot that lies in the map (kl_fa_author's way, the values of stock
    # F02's money bags). Taken: the last 8 of the 108 of every mode (leaves 100, as six stock levels have) and the
    # last of the team-mode 25. finish() gives the vault's ones the briefcase model on the written level.
    pool = collections.defaultdict(list)
    for k, i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if v[2] == 'ZMONEYCTRL_TYPE_DROP' and sc.parent[k] == 0:
            pool[v[0]].append((sc.names[k], k, i))
    spots = [(p, value, GATE_VAULT) for p, _yaw, value in VAULT_LOOT] + [(p, value, TELLER_LATE) for p, value in teller_loot()]
    take = (sorted(pool['ZMONEYCTRL_GAMEMODE_ALL'])[-8:] + sorted(pool['ZMONEYCTRL_GAMEMODE_TM_ONLY'])[8 - len(spots):])[:len(spots)]
    if len(take) != len(spots) or len(spots) < 8:
        raise ValueError('%d pool stacks for %d loot places' % (len(take), len(spots)))
    loot = []
    for (name, k, i), (p, value, hide) in zip(take, spots):
        def fn(us):
            for j, v in enumerate(('ZMONEYCTRL_GAMEMODE_ALL', value, 'ZMONEYCTRL_TYPE_NORMAL', 'ZMONEYCTRL_VARIANT_NORMAL', 15000, 0.2, 1, 30.0, 800.0, 1000.0, 0, 0)):
                A.setv(sc, us, j, v)
        kl_fa.edit(sc, k, i, fn)
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'TriggerBox2'), lambda us: A.setv(sc, us, 2, LOOT_REACH))
        A.place(S, k, p, hidden=hide)
        loot.append((name, hide))
    total = sum(v for _p, _y, v in VAULT_LOOT) + sum(v for _p, v in teller_loot())
    log('  kl_fa_bank: loot: %d in the vault (%s), %d at the tellers, %d in all' % (
        len(VAULT_LOOT), 'hidden until the beat\'s timer ends' if GATE_VAULT else 'shown', len(teller_loot()), total))
    # escape: the one van laid on the plan of ROAD - F07's own keys re-written in place, the boxes beside its drive
    # and its camera moved with it (kl_map_escape.van_prepare; the van's nodes must still stand where F07 has them);
    # the exit trigger names it alone (kl2 0x6c3f90 loops until one field is set). The escape marker stays where
    # PLACE has it, beside the lane: held against this plan's drive here (check() does it again on the written level)
    S.van = ESC.van_prepare(S, PLAN, log)
    if VAN_LATE:
        vg = A.node_of(sc, VAN + '\\' + VAN_GROUP)
        if VAN_NO_TARGET:                               # nothing for the police to aim at while it waits (VAN_LATE's note)
            gone = [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
            for k in gone:
                sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'FakeTarget']
            log('  kl_fa_bank: VAN_LATE: the van\'s FakeTarget (%d) taken off - the police have nothing to aim at while it waits' % len(gone))
        if VAN_HIDE:
            A.place(S, vg, hidden=True)
            log('  kl_fa_bank: VAN_LATE: the van\'s group is hidden from the load; %s shows it %.0f s after the plaza box' % ('bank_waves!Clock\\Van_show', VAN_SHOW))
    off = abs(ESC.Poly([tuple(p) for p in PLAN['path']]).project(ESC_AT)[1])
    if off < LANE_CLEAR:
        raise ValueError('kl_fa_bank: the escape marker\'s place %s is %d from the van\'s drive (%d wanted)' % (ESC_AT, off, LANE_CLEAR))
    log('  kl_fa_bank: the escape marker stands %d from the van\'s drive, %d from the boarding place at the stop' % (off, math.dist(ESC_AT, PLAN['board'])))
    van = van_path()
    k = A.node_of(sc, ROLE['exit'])
    kl_fa.edit(sc, k, A.ctrl_of(sc, k, kl_fa.EXIT), lambda us: [A.setv(sc, us, 2 + j, s) for j, s in enumerate((van, '', ''))])
    S.authored = {'loot': loot, 'van': van, 'hall': [] if NO_AI else place_hall(S, log)}
    return S.authored


# ------------------------------------------------------------------ 2. the campaign's own objects
def campaign_names(level):
    """Top-level names of M03_A the campaign pre-pass must leave in: the squads that stay and the campaign's
    single nodes of the beat. No door proxy is among them - every door takes 'Activate' itself
    (re/campaign_fa_bank.md 5, the second agent's note)."""
    if level != LEVEL:
        return ()
    return tuple(squad_plan()[0]) + tuple(CAMP.values()) + ((BLOCKER,) if VAULT_BLOCKER else ())


_dm = {}

def blast_lists():
    """{'post on': [...], 'pre off': [...]}: what the campaign's own blast shows and takes away, read from the stock
    Dead Men level (its three objects sit in the vault breaker's subtree, which is dropped: BLAST_LISTS)."""
    if 'blast' not in _dm:
        sc = J.Scene.load(LEVEL, 'dm')
        out = {}
        for role, names in BLAST_LISTS.items():
            out[role] = []
            for n in names:
                k = A.node_of(sc, BLAST_FROM + n)
                lists = [s for s in A.named(sc, k)]
                if not lists:
                    raise ValueError('%s names nothing in stock %s' % (n, LEVEL))
                out[role] += [s for s in lists if s not in out[role]]
        _dm['blast'] = out
    return _dm['blast']


def snap_men(M, keep, log=print):
    """Every man of a kept squad ON the navigation mesh: the campaign has three standing 10 - 32 beside it (at a
    wall's foot; Dead Men's own places). The man's group goes to the first point of the mesh on the way to the
    middle of the nearest polygon, at the mesh's height. More than MAN_OFF off the mesh is no such case: an error."""
    import kl_route
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
    moved = []
    for t in sc.tops():
        if sc.names[t] not in keep:
            continue
        for k in range(t, sc.end[t]):
            if sc.cls(k) != 'ZFFActor':
                continue
            g = sc.parent[k]                            # the man's group holds his place; 'Ground' sits at its origin
            w = world_of(M.ents[g - 1])[0]
            if mesh.on(*w) is not None:
                continue
            d, i = mesh.nearest(*w)
            if i is None or d > MAN_OFF:
                raise ValueError('%s stands %s off the navigation mesh at (%d, %d, %d)' % (sc.path[k], d, *w))
            mid = mesh.mid[i]
            for step in range(1, 201):
                x, z = w[0] + (mid[0] - w[0]) * step / 200.0, w[2] + (mid[2] - w[2]) * step / 200.0
                if mesh.inside(i, x, z) and math.hypot(x - w[0], z - w[2]) >= d + MAN_IN:
                    break
            new = (x, mesh.height(i, x, z), z)
            man_to(M, g, new, mesh)
            moved.append((sc.path[g][5:], round(d), math.dist(w, new)))
    log('  kl_fa_bank: %d men of the kept squads stood beside the navigation mesh and were put on it: %s' % (
        len(moved), ', '.join('%s %d off, moved %d' % (p.split('!')[-1], d, m) for p, d, m in moved) or '-'))
    return moved


def man_to(M, g, new, mesh):
    """A man's group g of the converted level M to the world place `new` (his turn stays): the place in his parent's
    frame, read back; the place must be on the navigation mesh."""
    par = M.ents[g - 1].parent
    T, Rm = world_of(par) if par is not None else ((0.0, 0.0, 0.0), [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]])
    dv = [new[a] - T[a] for a in range(3)]
    A.place(M, g, tuple(sum(Rm[b][a] * dv[b] for b in range(3)) for a in range(3)))   # the parent's turn undone (transpose)
    got = world_of(M.ents[g - 1])[0]
    if math.dist(got, new) > 1.0 or mesh.on(*got) is None:
        raise ValueError('%s: placed at %s, stands at %s%s' % (M.prp.path[g], new, got, '' if mesh.on(*got) else ', which is not on the mesh'))


def beat_men(M, keep, log=print):
    """The men of the squads the ante-room box starts (STAGE 'beat') to the places of BEAT_MEN, behind the airlock:
    in STAGE's order, a squad's men side by side. -> [(squad, man's group, from, to)]"""
    import kl_route
    if not BEAT_MEN or not keep:
        return []
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
    men = [(n, sc.parent[k]) for n, s in STAGE.items() if s == 'beat' for t in sc.tops() if sc.names[t] == n
           for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
    if len(men) != len(BEAT_MEN):
        raise ValueError('kl_fa_bank: %d men in the squads of the beat, BEAT_MEN has %d places' % (len(men), len(BEAT_MEN)))
    moved = []
    for (n, g), new in zip(men, BEAT_MEN):
        was = world_of(M.ents[g - 1])[0]
        man_to(M, g, tuple(float(v) for v in new), mesh)
        moved.append((n, sc.path[g][5:], was, new))
    log('  kl_fa_bank: the %d police of the beat (%d squads) re-placed behind the airlock, off the way in: from x %d..%d, z %d..%d to x %d..%d, z %d..%d' % (
        len(moved), len({n for n, _g, _w, _t in moved}), min(w[0] for _n, _g, w, _t in moved), max(w[0] for _n, _g, w, _t in moved),
        min(w[2] for _n, _g, w, _t in moved), max(w[2] for _n, _g, w, _t in moved), min(t[0] for t in BEAT_MEN), max(t[0] for t in BEAT_MEN),
        min(t[2] for t in BEAT_MEN), max(t[2] for t in BEAT_MEN)))
    return moved


def in_box(p, box):
    return all(lo <= v <= hi for v, (lo, hi) in zip(p, box))


def rout_places(sc, t):
    """The nodes the behaviour routs of squad group t go by: every ZBoxPrimitive / ZSTDOBJ child of a node that
    holds a behaviour rout (kl_fa_author.BEHAVE) - flank points, defend places, cover points, search boxes."""
    return [c for j in range(t + 1, sc.end[t]) if any(sc.p.key(nm) in A.BEHAVE for nm, _b in sc.nodes[j]['ctrls'])
            for c in range(j + 1, sc.end[j]) if sc.parent[c] == j and sc.cls(c) in ('ZBoxPrimitive', 'ZSTDOBJ')]


def plaza_places(M, keep, log=print):
    """PLAZA_OUTSIDE: the places of PLAZA_PLACES on the converted level M, each on the navigation mesh at the mesh's
    own height; afterwards NO place a rout of a plaza squad goes by may lie in the banking hall (HALL_BOX) - a
    place the table forgot is an error, not a man in the hall. -> [(squad, place, from, to)]"""
    import kl_route
    if not keep:
        return []
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
    moved = []
    for squad, places in PLAZA_PLACES.items():
        if squad not in keep or STAGE.get(squad) != 'plaza':
            raise ValueError('kl_fa_bank: PLAZA_PLACES names %s, which is no kept squad of the plaza' % squad)
        for rel, (x, z) in places.items():
            ks = sc.resolve(R + squad + '\\' + rel)
            hit = mesh.on(x, PLAZA_Y, z)
            if len(ks) != 1 or hit is None:
                raise ValueError('kl_fa_bank: %s: %s: %d nodes; (%d, %d) is %s the mesh at y %d' % (squad, rel, len(ks), x, z, 'on' if hit else 'NOT on', PLAZA_Y))
            was = world_of(M.ents[ks[0] - 1])[0]
            new = (float(x), hit[1] + PLAZA_UP, float(z))
            man_to(M, ks[0], new, mesh)
            moved.append((squad, rel, was, new))
    left = [(sc.path[c][5:], world_of(M.ents[c - 1])[0]) for t in sc.tops() if STAGE.get(sc.names[t]) == 'plaza' and sc.names[t] in keep
            for c in rout_places(sc, t) if in_box(world_of(M.ents[c - 1])[0], HALL_BOX)]
    if left:
        raise ValueError('kl_fa_bank: PLAZA_OUTSIDE: %d places of the plaza\'s squads are still in the banking hall: %s' % (
            len(left), ['%s (%d, %d, %d)' % (p, *w) for p, w in left]))
    log('  kl_fa_bank: PLAZA_OUTSIDE: %d places of %d plaza squads re-laid on the plaza (x %d..%d, z %d..%d), %d of them out of the banking hall; '
        'no place of their routs is left in it' % (len(moved), len(PLAZA_PLACES), min(t[0] for *_a, t in moved), max(t[0] for *_a, t in moved),
                                                 min(t[2] for *_a, t in moved), max(t[2] for *_a, t in moved), sum(in_box(w, HALL_BOX) for _s, _r, w, _t in moved)))
    return moved


def strip(M, log=print):
    """On the converted Dead Men level, before the join (nothing goes by controller index yet): the campaign's
    mini-cutscene controllers come off the squads that stay (kl_fa_author.STRIP). The door leaves are map nodes
    that stay as they are (they are sunk on the JOINED scene: Doors)."""
    if M.name != LEVEL:
        return 0
    sc, n = M.prp, 0
    keep = squad_plan()[0]
    for t in sc.tops():
        if sc.names[t] in keep:
            for k in range(t, sc.end[t]):
                nd = sc.nodes[k]
                left = [c for c in nd['ctrls'] if sc.p.key(c[0]) not in A.STRIP]
                n += len(nd['ctrls']) - len(left)
                nd['ctrls'] = left
    have = sum(1 for p, _at, _set in LEAVES if sc.resolve(R + p)) + bool(sc.resolve(R + VAULT_DOOR))
    log('  kl_fa_bank: %s: %d of %d door nodes of the route found; %d squads stay, %d mini-cutscene controllers taken off them' % (
        M.name, have, len(LEAVES) + 1, len(keep), n))
    snap_men(M, keep, log)
    beat_men(M, keep, log)
    clear_men(M, keep, log)
    garrison_men(M, keep, log)
    if PLAZA_OUTSIDE:
        plaza_places(M, keep, log)
    # the music's fourth layer (MUSIC_LAYER4): without the flag its nine fades lose their controller
    four = [(k, i) for k, i, v in kl_fa.controllers(sc, 'PlayMusicLayerFade') if v[0] == LAYER4 and sc.names[sc.top[k]] in (CAMP['music'], CAMP['music out'])]
    if len(four) != 9:
        raise ValueError('kl_fa_bank: %d fades of %s under the two music objects, 9 expected' % (len(four), LAYER4))
    if not MUSIC_LAYER4:
        for k in {k for k, _i in four}:
            sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'PlayMusicLayerFade']
    log('  kl_fa_bank: the music: %d fades of the fourth layer %s' % (len(four), 'stay (MUSIC_LAYER4)' if MUSIC_LAYER4 else
                                                                  'lose their controller (a value no stock Dog Days level has)'))
    # the alarm lamps' lights (ALARM_LIGHTS): without the flag the LightToggle comes off and the light is hidden
    lights = [k for k in range(1, len(sc.nodes)) if ('\\' + LAMP) in sc.path[k] and any(sc.p.key(c[0]) == 'LightToggle' for c in sc.nodes[k]['ctrls'])]
    if len(lights) != 22:
        raise ValueError('kl_fa_bank: %d lights with a LightToggle under the alarm lamps, 22 expected' % len(lights))
    # ... and with it every SLAVE of a spinning spot (ZGateLightSpot's last field: a ZSPOTLIGHT '<room>@<lamp>@Alarm_Spot
    # __slave' in the room next door, 8 in all). The engine carries a gate light's state to its slaves only at RUN time
    # (show / hide 0x8e4600 and light off 0x743240 walk the slave list; the LightToggle's init switches the master off
    # so): with the controller gone and the master hidden in the file neither call ever runs, and a slave left shown
    # could shine from the load with nothing to turn it off (review round 1; whether it would was not seen)
    slaves = sorted({j for k in lights if sc.cls(k) == 'ZGateLightSpot'
                     for s in kl_fa.node_values(sc, k)[J.labels('dd', 'ZGateLightSpot').index(SLAVES)] for j in sc.resolve(s)})
    if len(slaves) != 8 or any(not sc.names[j].endswith('__slave') for j in slaves):
        raise ValueError('kl_fa_bank: %d slave spots under the alarm lamps\' gate lights, 8 expected' % len(slaves))
    if not ALARM_LIGHTS:
        for k in lights + slaves:
            sc.nodes[k]['ctrls'] = [c for c in sc.nodes[k]['ctrls'] if sc.p.key(c[0]) != 'LightToggle']
            A.place(M, k, hidden=True)
    log('  kl_fa_bank: the alarm lamps: %d lights and %d slave spots of theirs in the rooms next door; %s' % (
        len(lights), len(slaves), 'their LightToggle stays (ALARM_LIGHTS)' if ALARM_LIGHTS else
        'the LightToggle taken off and all of them hidden (a kind no stock Dog Days level runs)'))
    return n


# ------------------------------------------------------------------ 3. the joined scene
def soldier_rows(sc, plan, log=print):
    """A stock Fragile Alliance soldier row (kl_arms.ROWS: skill eCustom and ZSoldier fields 4..17) for every man of
    the kept squads, by the class of the weapon kl_arms handed him (STOCK_ROWS). After kl_arms.arm, which runs
    before wire(). -> Counter of rows written."""
    import kl_arms
    cls_of = {t.lower(): c for c, pool in kl_arms.POOLS.items() for t, _w in pool}
    n = collections.Counter()
    for k, squad, w, _w2, _g1, _g2, _set in kl_arms.carriers(sc):
        if squad not in plan:
            continue
        kind = kl_arms.SKILL.get(cls_of.get(w.lower()))
        if kind is None:                                # unarmed, or a weapon of no pool: Dead Men's row stays
            n['none (%s)' % (w or 'unarmed')] += 1
            continue
        name, row = kl_arms.ROWS[kind]
        def fn(us, k=k, name=name, row=row):
            if len(us) != 23 or us[kl_arms.SKILL_FIELD][0][0] not in (0x0c, 0x0e) or any(us[j][0][0] != 0x0a for j in range(4, 18)):
                raise ValueError('%s: ZSoldier is not in the Dog Days layout' % sc.path[k])
            A.setv(sc, us, kl_arms.SKILL_FIELD, name)
            for j, x in enumerate(row):
                A.setv(sc, us, 4 + j, x)
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'ZSoldier'), fn)
        n[kind] += 1
    return n


def wire(sc, log=print):
    """Every reference of the layer that names a node of the map, and the layer's own chain. sc: the joined scene
    (kl_prpjoin.Scene). Values and reference lists of existing controllers only."""
    node = lambda n: A.node_of(sc, n)
    def must(paths):
        gone = [p for p in paths if not sc.resolve(p)]
        if gone:
            raise KeyError('kl_fa_bank: NOT IN THE LEVEL: %s' % gone)
        return list(paths)
    def put_(k, name, **fields):
        kl_fa.edit(sc, k, A.ctrl_of(sc, k, name), lambda us: [A.setv(sc, us, int(f[1:]), v) for f, v in fields.items()])
    def lists(role, name, **fields):
        put_(node(ROLE[role]), name, **fields)
    leaves = must([R + p for p, _at, _set in LEAVES])
    door, body = must([R + VAULT_DOOR, R + VAULT_BODY])
    for p in leaves + [door]:                           # each takes 'Activate' itself
        msg = [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == sc.resolve(p)[0]]
        if msg != ['Activate']:
            raise ValueError('%s: MatPosAnim in-message %s, not one \'Activate\'' % (p, msg))

    # ---- the enemies: who is named by which stage, the rows, the hunt
    plan = squad_plan()[0]
    stage = collections.defaultdict(list)
    for n, (first, _actors, _strip) in plan.items():
        if n in START_ROUT:
            first = R + n + '\\' + START_ROUT[n]
        stage[STAGE[n]] += must([first])
        k = node(n)
        if values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE] not in (0, 1):
            raise ValueError('%s: ZSquadScript field %d is %r' % (n, SQUAD_ACTIVE, values(sc, k, 'ZSquadScript')[SQUAD_ACTIVE]))
        put_(k, 'ZSquadScript', **{'f%d' % SQUAD_ACTIVE: 0})
    hunt = [R + n + '\\' + HUNT for n in plan if sc.resolve(R + n + '\\' + HUNT)]
    if GARRISON:                                        # the campaign's hunt (search box in the vault) is not named: the garrison keeps its places
        hunt = []
    hall = [] if NO_AI else must([R + n + '\\' + HALL_START for n in HALL])
    armed = soldier_rows(sc, plan, log) if STOCK_ROWS else {}
    if GARRISON:
        garrison_modes(sc, plan, log)

    # ---- round start: AIMonitor list 2 (event 2, kl2 0x8b5f60; it comes when the countdown begins). F07's own
    # list names five timers of its opening; what is a ROLE object here must not be started by it. Two timers of
    # this layer are: the squads' (SQUADS_AT) and the music's
    k = node(ROLE['monitor'])
    mine = {R + v for v in ROLE.values()}
    have = [s for s in values(sc, k, 'AIMonitor')[2] if sc.resolve(s) and s not in mine]
    start = [R + ROLE['start timer'], R + ROLE['music timer']] + ([R + ROLE['doors']] if DOORS_ANIMATE else [])
    lists('monitor', 'AIMonitor', f2=have + start)
    lists('start timer', 'TriggerDelay2', f0=SQUADS_AT, f4=stage['start'] + stage['down'])
    music, out = must([R + CAMP['music'], R + CAMP['music out']])
    lists('music timer', 'TriggerDelay2', f0=MUSIC_AT, f4=[music])
    lists('doors', 'AIDWrapper', f0=leaves if DOORS_ANIMATE else [], f1='Activate')
    if DOORS_ANIMATE:
        glass = [p for p in leaves if '\\GlassDoor_' in p]
        for p in glass:                                 # the clip goes there AND back: stop it at its open frame
            j = sc.resolve(p)[0]
            put_(j, 'MatPosAnim', **{'f%d' % MPA_LAST: GLASS_LAST})
        log('  kl_fa_bank: DOORS ANIMATE: %d leaves get \'Activate\' at the round start; %d glass leaves store LAST %d' % (len(leaves), len(glass), GLASS_LAST))

    # ---- the beat. The ante-room box starts, all at once: the six rod timers, the beat's timer, the 14 police of
    # stage 'beat', the music's rise. TriggerBox FIELD 15 = 0 (BOX_PER_MAN): by the stock data 0 is 'fires once', 1 'fires
    # for every criminal that enters' - of the 226 TriggerBox of F01..F09 the 125 with 0 start the squad routs and
    # the one-shot timers (this very object in F07 has 0), and not one of the 101 with 1 names a squad rout; F07's
    # 'tbRunToEscape' (1) feeds a TriggerCounter of three, its twin 'tbRunToEscape1Player' (0) a timer
    # (C:/kl_scratch/bank/review_round_1/tb.py). The first three stages wrote 1 on the opposite ASSUMPTION: the beat
    # would have begun again for each further criminal - seven AI heisters among them (review round 1).
    # ASSUMPTION still: the field's meaning is read off the census, not in kl2.exe
    rods = must([R + p for p in RODS])
    for p in rods:
        msg = [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == sc.resolve(p)[0]]
        if msg != ['Activate']:
            raise ValueError('%s: MatPosAnim in-message %s, not one \'Activate\'' % (p, msg))
    camp = {r: must([R + n])[0] for r, n in CAMP.items()}
    for i, p in enumerate(rods):
        lists('rod timer %d' % (i + 1), 'TriggerDelay2', f0=rod_times()[i], f4=[R + ROLE['rod %d' % (i + 1)], camp['rod sound %d' % (i + 1)]])
        lists('rod %d' % (i + 1), 'AIDWrapper', f0=[p], f1='Activate')
    fades = lambda names: [p for p in must([music + '\\' + n for n in names]) if kl_fa.has(sc, sc.resolve(p)[0], 'PlayMusicLayerFade')]
    rise = fades(MUSIC_RISE)                            # without MUSIC_LAYER4 the fourth layer's fades hold no controller: not named
    gone = VAULT_DOOR_GOES and not VAULT_OPEN
    swing = gone and VAULT_SWING_END is not None        # the door's body goes on a timer of its own, VAULT_SWING_END s after the beat's end
    late = (gone and not swing) or bool(VAULT_BLAST) or (DOOR_WAIT and not VAULT_OPEN) or VAULT_BLOCKER   # the door timer has something to do
    lists('beat box', 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', **{'f%d' % BOX_PER_MAN: 0},
          f17=[R + ROLE['beat timer']] + [R + ROLE['rod timer %d' % (i + 1)] for i in range(len(rods))] + stage['beat'] + rise)
    # ... when it ends: the door's swing and its sound, the loot, the alarm (sound, lamps), the music's change, the
    # hall's police, the hunt; DOOR_GONE later the door's body goes and the vault blows
    alarm = [camp['alarm sound'], camp['alarm lamps']] + ([camp['lights off']] if ALARM_LIGHTS else [])
    fade = fades(MUSIC_FADE)
    lists('beat timer', 'TriggerDelay2', f0=BEAT, f4=[R + ROLE['door'], camp['door sound'], R + ROLE['loot on']] + alarm + fade + [out] + ([] if DOOR_WAIT and not VAULT_OPEN else hall + hunt)
          + ([R + ROLE['door timer']] if late else []) + ([R + SWING_TIMER] if swing else []))
    if swing:
        put_(node(SWING_TIMER), 'TriggerDelay2', f0=VAULT_SWING_END, f4=[R + ROLE['door off']])
        log('  kl_fa_bank: VAULT_SWING: the door body goes %.0f s after the beat end, by %s (the door timer keeps its %.0f s)' % (
            VAULT_SWING_END, SWING_TIMER.split('!')[-1], DOOR_GONE))
    lists('door', 'AIDWrapper', f0=[] if VAULT_OPEN else [door], f1='Activate')
    lamps = values(sc, sc.resolve(camp['alarm lamps'])[0], 'AIDWrapper')
    if lamps[1] != 'Activate' or len(lamps[0]) != 11 or any(LAMP not in s or not sc.resolve(s) for s in lamps[0]):
        raise ValueError('%s does not send \'Activate\' to the eleven alarm lamps: %s' % (CAMP['alarm lamps'], lamps))
    hidden = [R + sc.names[t] for t in sc.tops() if sc.names[t].startswith('FASpecials!DropMoney!') and kl_fa.node_values(sc, t)[3]
              and any(v[2] == 'ZMONEYCTRL_TYPE_NORMAL' for kk, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if kk == t)]
    want_hidden = len(VAULT_LOOT) * bool(GATE_VAULT) + len(teller_loot()) * bool(TELLER_LATE)
    if len(hidden) != want_hidden:
        raise ValueError('%d hidden loot objects, %d wanted (the vault %d%s)' % (len(hidden), want_hidden, len(VAULT_LOOT) * bool(GATE_VAULT),
                                                                            ', the tellers %d (TELLER_LATE)' % len(teller_loot()) if TELLER_LATE else ''))
    lists('loot on', 'ActivateGeom', f0='AITrigger', f1=hidden)

    # ---- the blast (VAULT_BLAST), on the door's timer with the door's body
    boom = [camp['boom %d' % i] for i in (1, 2, 3)]
    on, off = [], []
    if VAULT_BLAST:
        got = blast_lists()
        on, off = [s for s in got['post on'] if sc.resolve(s)], [s for s in got['pre off'] if sc.resolve(s)]
        if R + VAULT_POST not in on or R + VAULT_PRE not in off:
            raise ValueError('the campaign\'s blast lists do not name the vault\'s two states: %d on, %d off' % (len(on), len(off)))
        for p in boom:
            k = sc.resolve(p)[0]
            v = values(sc, k, 'Explode')
            if len(v) != 18 or not all(isinstance(v[j], float) for j in EXPLODE_REACH) or values(sc, k, 'AIDWrapper')[:2] != [[p], 'Activate']:
                raise ValueError('%s: not an Explode in the Dog Days layout with a wrapper of its own: %s' % (p, v))
            if VAULT_BLAST == 'show':
                put_(k, 'Explode', **{'f%d' % j: 1.0 for j in EXPLODE_REACH})
        log('  kl_fa_bank: the vault\'s blast (%s): %d Explode%s, %d objects on (the blown vault, fire, smoke), %d off; of the campaign\'s lists %d / %d '
            'entries are not in the build' % (VAULT_BLAST, len(boom), ' with reach 1' if VAULT_BLAST == 'show' else ' as the campaign has them', len(on), len(off),
                                              len(got['post on']) - len(on), len(got['pre off']) - len(off)))
    if VAULT_BLOCKER:                                   # the kept campaign blocker: its audio list is dead (the build drops it), the door timer unblocks it
        put_(node(BLOCKER), 'PathBlocker', f2=[])
    lists('door timer', 'TriggerDelay2', f0=DOOR_GONE, f4=([R + ROLE['door off']] if gone and not swing else []) + ([R + BLOCKER] if VAULT_BLOCKER else []) + (hall + hunt if DOOR_WAIT and not VAULT_OPEN else []) + (
        boom + [camp['blast sound'], R + ROLE['post on'], R + ROLE['pre off']] if VAULT_BLAST else []))
    lists('door off', 'DeactivateGeom', f0='AITrigger', f1=[body] if gone else [])
    put_(sc.resolve(camp['blast sound'])[0], 'AIDWrapper', f0=must([R + BLAST_SOUND]) if VAULT_BLAST else [], f1='Activate')
    lists('post on', 'ActivateGeom', f0='AITrigger', f1=on)
    lists('pre off', 'DeactivateGeom', f0='AITrigger', f1=off)

    # ---- the way out: F07's 'exit heist' box in the foyer, with a line that fits a front door - and the plaza's
    # seven squads: the police are outside when a criminal comes up into the hall
    # PLAZA_OUTSIDE (the crew fix after run V2): the foyer box keeps the line; the plaza's squads are started by the
    # box across the hall's south end, in the stock form of a box that starts squad routs (field 0 = 1, 15 = 0: once)
    lists('speak box', 'TriggerBox', f14='ECPS_FA_MERCONLY', f17=[R + ROLE['speak']] + ([] if PLAZA_OUTSIDE else stage['plaza']))
    if PLAZA_OUTSIDE:
        put_(node(PLAZA_BOX), 'TriggerBox', f0=1, f14='ECPS_FA_MERCONLY', f17=list(stage['plaza']), **{'f%d' % BOX_PER_MAN: 0})
        log('  kl_fa_bank: PLAZA_OUTSIDE: %s (the hall\'s south end) starts the plaza\'s %d routs; the foyer box only the line' % (PLAZA_BOX, len(stage['plaza'])))
    lists('speak', 'OnlineSpeakPlayer', f1=EXIT_LINE)
    # ---- the escape: every exit trigger of the level (there is F07's one) calls the van - field 0 false, field 2
    # the van's group, 1 and 3..5 empty, the form the three car maps on the tab have (kl_map_escape.van_wire). The
    # rest of the round's last stage is F07's own and stays as the graft left it: the vehicle monitor's lists
    # (2 the escape sounds, 3 the relay of this van, 8 the 'last van' message and its timer)
    if PLAN is None:
        raise ValueError('kl_fa_bank: wire() without a plan of the van (see prepare_host)')
    ESC.van_wire(sc, PLAN, log)
    for k, i, v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        if len(v) != 340:
            raise ValueError('the settings object has %d fields' % len(v))
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, s)]) for f, s in LINES.items()])
    log('  kl_fa_bank: enemies: %d campaign squads (%d men): round start + %.0f s -> %d routs (dock, vault lobby, the way down); ante-room box -> %d; '
        'the beat\'s end -> %d hunts + %d of F07\'s squads in the hall; %s -> %d; stock soldier rows: %s' % (
            len(plan), sum(a for _f, a, _s in plan.values()), SQUADS_AT, len(stage['start'] + stage['down']), len(stage['beat']), len(hunt), len(hall),
            'the box at the hall\'s south end (PLAZA_OUTSIDE)' if PLAZA_OUTSIDE else 'foyer box', len(stage['plaza']), dict(armed) or ('none (NO_AI)' if NO_AI else 'Dead Men\'s rows stay')))
    log('  kl_fa_bank: sequence: ante-room box -> rods at %s s -> %.0f s -> the vault door %s, %d hidden loot objects on, alarm (%s), music -> way-out set%s' % (
        ', '.join('%.0f' % t for t in rod_times()), BEAT, 'is sunk already (VAULT_OPEN)' if VAULT_OPEN else 'gets \'Activate\'',
        len(hidden), 'sound, lamps, white light off' if ALARM_LIGHTS else 'sound, the lamps\' glow', '; -> %.0f s -> %s' % (
            DOOR_GONE, ' and '.join(x for x in ('the door\'s body off' if gone else '', 'the vault\'s blast (%s)' % VAULT_BLAST if VAULT_BLAST else '') if x)) if late else ''))
    log('  kl_fa_bank: wired: round start %s; music at %.0f s; %d briefing / reminder lines; exit line %s' % (
        '-> %d door leaves' % len(leaves) if DOORS_ANIMATE else 'starts no door (the leaves are open at build time)', MUSIC_AT, len(LINES), EXIT_LINE))
    return {'hidden': hidden, 'leaves': leaves, 'monitor': have + start, 'stage': dict(stage), 'hunt': hunt, 'hall': hall, 'on': on, 'off': off}


def layer_names(sc):
    """Top-level names of the layer in the joined scene: what kl_fa.repair's prune may cut dead references from."""
    camp = set(campaign_names(LEVEL))
    keep = __getattr__('KEEP')
    return tuple(sc.names[t] for t in sc.tops() if kl_graft.Select.match(sc.names[t], keep) or sc.names[t] in camp)


def complete(sc):
    """One map: the layer is wired in the one build there is."""
    return True


# ------------------------------------------------------------------ the doors at build time
class Doors:
    """THE FALL-BACK THAT WALKS OFFLINE: the leaves of the route are taken out at build time. kl_graft.build calls
    three functions of kl_escape for every Dead Men map (the code path of the Fragile Alliance bank's yard wall,
    which bots cross live); for the length of one build they are wrapped - the study's build_open.py, unchanged in
    what it does (re/campaign_fa.md G1.1, G1.2: twelve leaves out, verify as before, the route free):
      repair          + each node of sunk() is moved DOOR_DY in WORLD y in the joined .prp (ZGEOM[2]). A leaf may
                        stand under a turned group (the four glass leaves do: after a world move of 2,500 down their
                        .prp y is 12), so the move is turned into the parent's frame; kl_escape.open_wall refuses such nodes
      place_entities  the real one, handed each node's new place in the .gms record's OWN parent frame ('move' entry;
                        the .prp and the .gms do not always hold the same local place: G1.1 trap 2), the two world
                        places held against each other before and after; + the moved entities' REF ids
      cut_collision   the real one, on those REF ids: their key-framed placements leave the joined .HVK
    arm() puts the wrappers in (prepare_host calls it: a plain 'kl_maps.py one ... --author kl_fa_bank' has no other
    place), the last wrapper that runs takes them out; doors() is the same as a context manager."""
    real, state = None, None

    @classmethod
    def sunk(cls):
        """Paths (below ROOT) of the nodes this build takes out."""
        return ([] if DOORS_ANIMATE else [p for p, _at, _set in LEAVES]) + ([VAULT_BODY] if VAULT_OPEN else [])

    @classmethod
    def arm(cls, log=print):
        if cls.real is None:
            cls.real = (kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision)
            kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision = cls.repair, cls.place, cls.cut
        cls.state = {'sink': {}, 'old': {}, 'prp_w': {}}

    @classmethod
    def disarm(cls):
        if cls.real is not None:
            kl_escape.repair, kl_escape.place_entities, kl_escape.cut_collision = cls.real
            cls.real = None

    @staticmethod
    def prp_frame(sc, k):
        """World rotation (rows) of node k's PARENT frame from the .prp chain, and that parent's world place."""
        chain, j = [], sc.parent[k]
        while j > 0:
            chain.append(j); j = sc.parent[j]
        Rm, T = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], [0.0, 0.0, 0.0]
        for j in reversed(chain):
            lab = J.labels('dd', sc.cls(j))
            v = kl_fa.node_values(sc, j)
            t, r = v[lab.index('ZGEOM[2]')], v[lab.index('ZGEOM[1]')]
            T = [T[a] + sum(Rm[a][b] * t[b] for b in range(3)) for a in range(3)]
            m = [r[6:9], r[3:6], r[0:3]]
            m = [[m[b][a] for b in range(3)] for a in range(3)]
            Rm = [[sum(Rm[a][c] * m[c][b] for c in range(3)) for b in range(3)] for a in range(3)]
        return Rm, T

    @classmethod
    def prp_world(cls, sc, k):
        """World place of node k from the .prp chain alone."""
        Rm, T = cls.prp_frame(sc, k)
        t = kl_fa.node_values(sc, k)[J.labels('dd', sc.cls(k)).index('ZGEOM[2]')]
        return tuple(T[a] + sum(Rm[a][b] * t[b] for b in range(3)) for a in range(3))

    @classmethod
    def repair(cls, sc, log=print):
        done = cls.real[0](sc, log)
        st, tilted = cls.state, 0
        for path in cls.sunk() if sc.resolve(R + IN[:-1]) else ():      # only on a scene that holds the bank
            k = A.node_of(sc, path)
            lab = J.labels('dd', sc.cls(k))
            Rm, _T = cls.prp_frame(sc, k)
            d = [Rm[1][a] * DOOR_DY for a in range(3)]   # R^T (0, dy, 0): the world's y move in the parent's frame
            tilted += abs(d[1] - DOOR_DY) > 0.01
            old = list(kl_fa.node_values(sc, k)[lab.index('ZGEOM[2]')])
            new = [old[a] + d[a] for a in range(3)]
            before = cls.prp_world(sc, k)
            kl_fa.edit(sc, k, None, lambda us, lab=lab, new=new: A.setv(sc, us, lab.index('ZGEOM[2]'), new))
            st['sink'][k], st['old'][k], st['prp_w'][k] = DOOR_DY, old, (before, cls.prp_world(sc, k))
        if st['sink']:
            log('  kl_fa_bank: doors: %d nodes sunk by %g (world y) in the joined .prp; %d of them stand in a parent frame '
                'with another y axis than the world\'s' % (len(st['sink']), -DOOR_DY, tilted))
        return done

    @classmethod
    def place(cls, sc, ents, done, log=print):
        st = cls.state
        before = {k: world_of(ents[k - 1])[0] for k in st['sink']}
        other = 0
        for k in st['sink']:
            e = ents[k - 1]
            t = struct.unpack('<3f', e.trans[:12])
            other += max(abs(t[a] - st['old'][k][a]) for a in range(3)) > 0.05
            if max(abs(before[k][a] - st['prp_w'][k][0][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: world place by the .gms %s, by the .prp %s' % (sc.path[k], before[k], st['prp_w'][k][0]))
            Rm = world_of(e.parent)[1] if e.parent is not None else [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
            done['move'][k] = tuple(t[a] + Rm[1][a] * DOOR_DY for a in range(3))     # place_entities writes it into the record
        refs = set(cls.real[1](sc, ents, done, log))
        refs |= {ents[k - 1].ref for k in st['sink']}   # the leaves' REF ids, for cut_collision
        for k in sorted(st['sink']):
            e = ents[k - 1]
            after = world_of(e)[0]
            if abs(after[0] - before[k][0]) > 0.5 or abs(after[2] - before[k][2]) > 0.5 or abs(after[1] - before[k][1] - DOOR_DY) > 0.5:
                raise ValueError('%s moved %s -> %s, not straight down by %g' % (sc.path[k], before[k], after, -DOOR_DY))
            if max(abs(after[a] - st['prp_w'][k][1][a]) for a in range(3)) > 1.0:
                raise ValueError('%s: after the move the .gms says %s, the .prp %s' % (sc.path[k], after, st['prp_w'][k][1]))
        if st['sink']:
            log('  kl_fa_bank: doors: %d entities moved in the .gms (%d of them hold another local place there than in the .prp; '
                'the world places agree); %d REF ids go to cut_collision' % (len(st['sink']), other, len(refs)))
        if not refs:                                    # kl_graft does not call cut_collision then: the build is through
            cls.disarm()
        return refs

    @classmethod
    def cut(cls, hvk, refs, log=print):
        try:
            mine = collections.Counter(s.type for s in hvk.shapes for i in s.inst if kl_hvk.ref(i) in refs)
            h = cls.real[2](hvk, refs, log)
            left = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) in refs)
            if left:
                raise ValueError('%d placements are left in the .HVK under the %d REF ids taken out' % (left, len(refs)))
            log('  kl_fa_bank: doors: %d placements (by shape type %s) were under the %d REF ids; none is left' % (sum(mine.values()), dict(mine), len(refs)))
            return h
        finally:
            cls.disarm()


@contextlib.contextmanager
def doors(log=print):
    """For a script that builds: the wrappers of Doors for the length of the block, taken out whatever happens."""
    Doors.arm(log)
    try:
        yield Doors
    finally:
        Doors.disarm()


# ------------------------------------------------------------------ on the written level
def in_vault(p):
    return all(lo <= v <= hi for v, (lo, hi) in zip(p, VAULT_BOX))


def set_text(kids, key, text):
    """A text leaf at 'A/B/C' in a .LOC tree (kl_loc nodes), tables made on the way; an existing leaf gets the text."""
    import kl_loc
    tab = kids
    *path, name = [s.encode('latin1') for s in key.split('/')]
    for s in path:
        nxt = next((k for k in tab if k.name.lower() == s.lower()), None)
        if nxt is None:
            nxt = kl_loc.Node(s, kl_loc.TABLE, [])
            kl_loc._insert(tab, nxt)
        elif nxt.kids is None:
            raise ValueError('%s: %r is a leaf' % (key, s))
        tab = nxt.kids
    new = kl_loc.leaf(name, text.encode('latin1'), 0)
    old = next((k for k in tab if k.name.lower() == name.lower()), None)
    if old is None:
        kl_loc._insert(tab, new)
    else:
        old.flags, old.raw = new.flags, new.raw


def finish(folder, log=print):
    """What needs the WRITTEN level, in place, on a folder with <slot>_Main.zip -> [problems]. A level finished
    before is left as it is.
    0. The level is lightened (kl_graft's trim + slim, kl_fa_loot.lighten_first): F07's dead map models and the textures
       only they show go (.prm 85.7 -> 44 MB). It has to come before the dead chunk indices are handed out.
    1. The vault's loot shows a briefcase and stands on the floor turned as VAULT_LOOT
       says: kl_fa_loot's way - the model root comes from Dead Men's M01_FA_A into dead indices, its materials get
       compiled shaders.
       The teller stacks keep F07's money bag: a bag on a bank counter needs no other prop (GUESS, the owner's eyes).
    2. The level's own texts: TEXTS into every language's .LOC, the settings' start windows onto them."""
    import kl_fa_loot as L, kl_chars as C, kl_light, kl_loc, kl_texmat as T
    from kl_port_check import workdir
    E = L.Edit(folder)
    sc, bad = E.sc, []
    loot = [k for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2] and sc.parent[k] == 0]
    vault = [k for k in loot if in_vault(E.at(k))]
    pool = {E.ents[k - 1].model for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2]}
    dressed = not {E.ents[k - 1].model for k in vault} <= pool
    if len(vault) != len(VAULT_LOOT):
        bad.append('%d loot objects lie in the vault, VAULT_LOOT has %d' % (len(vault), len(VAULT_LOOT)))
    n0 = len(E.p.chunks)
    L.lighten_first(E, log)                             # always: what is checked and handed on is the lightened level
    if CASE and vault and not dressed:
        C.dead_indices(E.p, sc, E.raw, E.oct, E.extra, log)
        root, _box, slots = L.case_model(E, CASE, CASE_SCALE, log)
        lo, _hi = L._assets(E).bounds(root)             # of what is drawn: the model's underside goes onto the floor
        for k in vault:
            at = E.at(k)
            p, yaw, _value = min(VAULT_LOOT, key=lambda r: math.dist(r[0], at))
            if math.dist(p, at) > 1.0:
                bad.append('%s lies at (%d, %d, %d), which is no place of VAULT_LOOT' % (sc.names[k], *at))
                continue
            E.put(k, (p[0], p[1] - lo[1], p[2]), L.yaw9(yaw), root)
        if len(E.p.chunks) != n0:
            raise ValueError('the chunk table grew from %d to %d: not enough dead indices' % (n0, len(E.p.chunks)))
        if slots:                                       # a material without a compiled shader is not drawn (kl_fa_loot.dress)
            fxc = E.lv['.fxc']
            upath = os.path.join(workdir(), 'build', 'shared', 'union.fxc')
            if os.path.isfile(upath):
                fxc = T.merge_fxc(fxc, open(upath, 'rb').read())
            fit = kl_light.fit_shaders(E.mat, fxc, slots=slots, log=log)
            E.lv['.fxc'] = fxc
            bad += ['no compiled shader for %s' % v[0] for v in fit['unresolved'].values()]
        log('  kl_fa_bank: %d briefcases in the vault (model %d, x %.2f, its underside %.1f over its origin); chunk table %d entries, as before' % (
            len(vault), root, CASE_SCALE, lo[1], n0))
    elif dressed:
        log('  kl_fa_bank: %s: the vault\'s loot already shows models of its own: left as it is' % folder)
    # ---- texts
    langs = 0
    for ext in sorted(E.lv.ext):
        if not ext.lower().endswith('.loc'):
            continue
        kids = kl_loc.parse(E.lv[ext])
        if kids is None:                                # a stub (Dutch in every stock level)
            continue
        for key, text in TEXTS.items():
            set_text(kids, key, text)
        E.lv[ext] = kl_loc.build(kids)
        langs += 1
    for k, i, _v in kl_fa.controllers(sc, kl_fa.SETTINGS):
        kl_fa.edit(sc, k, i, lambda us: [us.__setitem__(f, [kl_fa._str(sc, START_KEY % w)]) for f, w in START_FIELDS.items()])
    log('  kl_fa_bank: %d text keys in %d languages (the English text in each); settings fields %s name the start windows' % (
        len(TEXTS), langs, sorted(START_FIELDS)))
    E.save(None, log)
    for b in bad:
        log('  PROBLEM: ' + b)
    return bad


# ------------------------------------------------------------------ the checks
# the round's way, for tools/kl_route.py: the stations of re/campaign_fa_bank.md 4.3 (AI heisters' row), MEASURED on the mesh
ROUTE_IN = [('START', START[1]), ('dock door', (550, 200, -4650)), ('dock', (266, 202, -5002)), ('vault lobby', (394, 241, -7129)),
            ('glass door 2', (399, 240, -7614)), ('upper flight', (-70, -158, -9200)), ('cross corridor', (-75, -558, -10600)),
            ('ante-room', (400, -959, -11800))]
ROUTE_VAULT = [('vault', (399, -960, -12818))]
ROUTE_OUT = [('ante-room', (400, -959, -11800)), ('vault lobby', (394, 241, -7129)), ('airlock', (1100, 240, -7000)), ('stairs', (1538, 355, -5822)),
             ('foyer', (309, 803, -5624)), ('hall', (377, 801, -8423)), ('front entrance', FRONT), ('plaza', (281, 812, -9700)),
             ('street', ESC_AT)]                        # beside the van's lane, under the escape marker - not ON the van's stop
# the five large blocks a level load asks of the 2 GB process (CLAUDE.md, 2026-10-10 01:35): 32.0 MB scratch, .fxc, .prm and
# .ANM + 0x60000 each, the whole .WAV beside the archive. No limit is known; the yardstick is what has loaded live many
# times in one process: the Retomoto build of 2026-10-10 (the owner's session of seven level loads in one process),
# 16.9 + 74.2 + 20.6 + 25.9 MB = 171 MB with the scratch block. (The tab's Retomoto of today is heavier - 180.3 MB by
# <work>/build/c_bank/blocks.txt - and plays; 171 is the figure a counted run stands behind, the safe side)
BLOCKS_LIVE = 171.0
# the chunk table: 69,632 entries is the tools' line (kl_impact.CHUNK_SAFE). The wardrobe and the gun looks come into
# DEAD indices. MEASURED on this level by the finishing chain: 'kl_chars.py wardrobe --plates=wolf,dallas,chains,hoxton'
# took 20,989 of the bare map's 23,690 (re/bank_campaign.md F.4; the study's 15,509 was a wardrobe without the four plates)
WARDROBE_CHUNKS = 20989
ACTORS_LIVE = (99, 55)                  # ZFFActor and squads of the largest build that runs live: Retomoto on the tab
                                        # (re/campaign_fa_tooling.md 5.4; stock Fragile Alliance: 35..57 and 20..36)
POLICE_CLEAR = 100.0                    # a returning policeman's point or body this far from a squad's man. GUESS
# the walk test of the loot's pick-up: (box x0, x1, z0, z1; a place the route test reaches) for the vault and the banking hall.
# GUESS: the two boxes (each room with a margin); the two places are stations of ROUTE_VAULT / ROUTE_OUT
LOOT_WALKS = (((-100.0, 1200.0, -13600.0, -12600.0), (399.0, -960.0, -12818.0)), ((-1300.0, 1900.0, -9500.0, -5700.0), (377.0, 801.0, -8423.0)))


def archive_of(folder):
    zips = [f for f in sorted(os.listdir(folder)) if f.lower().endswith('_main.zip')]
    if len(zips) != 1:
        raise ValueError('%s: expected one *_Main.zip' % folder)
    return os.path.join(folder, zips[0])


def read_built(folder):
    """-> (scene tree, kl_scene.Scene, its entities, {entity: world place}, kl_hvk.Hvk, .SND, English .LOC, sizes)."""
    arch = archive_of(folder)
    sc, snd, loc = kl_fa.load(arch)
    with zipfile.ZipFile(arch) as z:
        m = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        scene = kl_scene.Scene(kl_gms.unpack(z.read(m['.gms'])), z.read(m['.buf']))
        hvk = kl_hvk.Hvk(z.read(m['.hvk']))
        size = {e: z.getinfo(m[e]).file_size for e in ('.prm', '.fxc', '.anm', '.tex')}
        size['entries'] = struct.unpack_from('<I', z.read(m['.prm']), 4)[0]
    wav = [f for f in os.listdir(folder) if f.lower().endswith('_main.wav')]
    size['.wav'] = os.path.getsize(os.path.join(folder, wav[0])) if wav else 0
    return sc, scene, list(scene.entities()), kl_maps.world(scene), hvk, snd, loc, size


def lost_clips(folder, res):
    """(the clip names result.json lists as missing from the stream file, those of them WITHOUT a record in the built
    .WHD beside the archive, every name that has a record - lower case). Only the second are silent: a name with a
    record streams from the installed file. Names with '/'; ([], [], set()) when the folder has no list or no .WHD."""
    import kl_whd, kl_snd
    whd = [f for f in os.listdir(folder) if f.lower().endswith('_main.whd')]
    listed = [n.replace('\\', '/') for n in res.get('stream_clips_missing') or ()]
    if not listed or not whd:
        return [], [], set()
    b = open(os.path.join(folder, whd[0]), 'rb').read()
    have = {kl_snd.cs(b, f['name']).decode('latin1').replace('\\', '/').lower() for f in kl_whd.records('dd', b).values()}
    return listed, [n for n in listed if n.lower() not in have], have


def music_records(folder):
    """How many of MUSIC_CLIPS have a streamed PC_Def.str record in the built .WHD beside the archive (0 for the
    builds against the stream file without the music; 6 with it)."""
    import kl_whd, kl_snd
    whd = [f for f in os.listdir(folder) if f.lower().endswith('_main.whd')]
    if not whd:
        return 0
    b = open(os.path.join(folder, whd[0]), 'rb').read()
    have = {kl_snd.cs(b, f['name']).decode('latin1').replace('\\', '/').lower() for f in kl_whd.records('dd', b).values()
            if f['fmt'] & kl_whd.STREAMED and not f['fmt'] & kl_whd.LANGFILE}
    return sum(n.lower() in have for n in MUSIC_CLIPS)


def use_stream(path, log=print):
    """'--str': for THIS process kl_snd's 'merged' stream file is `path` (and stream_map() its .map.json) - what
    kl_snd.merge inside kl_maps.one resolves Dead Men's streamed clips against. kl_snd has one fixed place for that
    file (<work>/build/PC_Def.str, another session's, not to be overwritten); the function is replaced here the way
    Doors replaces kl_escape's three for the length of a build. The other names ('dd', 'stock') stay."""
    import kl_snd
    path = os.path.abspath(path)
    if not os.path.isfile(path) or not os.path.isfile(path + '.map.json'):
        raise ValueError('kl_fa_bank: --str %s: the file or its .map.json is not there' % path)
    real = kl_snd.stream_file
    kl_snd.stream_file = lambda which='merged': path if which == 'merged' else real(which)
    log('kl_fa_bank: streamed clips are resolved against %s (%d bytes) and its .map.json (%d blocks)' % (path, os.path.getsize(path), len(kl_snd.stream_map())))


def inventory(folder, log=print):
    """What the layer consists of in a built level, with world places read back from it."""
    import kl_arms
    sc, _scene, ents, pos, _hvk, _snd, _loc, _size = read_built(folder)
    at = lambda k: '(%6d %6d %6d)' % tuple(round(x) for x in pos[ents[k - 1]])
    ctl = lambda k: ','.join(sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls'])
    half = lambda k: ' half %s' % (tuple(round(x) for x in kl_fa.node_values(sc, k)[8:11]),) if sc.cls(k) == 'ZBoxPrimitive' else ''
    def row(k, note=''):
        log('  %-74s %-22s %s%s %s %s' % (sc.path[k][5:][-74:], sc.cls(k), at(k), half(k), ctl(k), note))
    def targets(k):
        for s in A.named(sc, k)[:20]:
            log('        -> %s%s' % (s[5:][-110:], '' if sc.resolve(s) else '   NOT IN THE LEVEL'))
    log('SPAWN POINTS (ZSpawnPoint) and player groups')
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint':
            row(k, kl_fa.node_values(sc, k)[8].replace('eSPAWN_TYPE_FRAGILE_ALLIANCE_', ''))
        elif sc.parent[k] == 0 and sc.names[k].startswith('Heroes!'):
            row(k)
    log('PLACED HOST OBJECTS (PLACE; source of each number in the table)')
    for name, (_p, _f, _h, why) in PLACE.items():
        row(A.node_of(sc, name), '<- ' + why)
    log('LOOT (OnlineMoneyCtrl that is no drop pool)')
    total = 0
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if 'DROP' not in v[2]:
            total += v[1]
            row(k, '%s %d model %d%s' % (v[2][16:], v[1], ents[k - 1].model, ' HIDDEN at start' if kl_fa.node_values(sc, k)[3] else ''))
    pools = collections.Counter(v[0][20:] for _k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' in v[2])
    log('  loot %d; drop pools left: %s' % (total, dict(pools)))
    log('THE CHAIN (ROLE) and what each object names')
    for role, name in ROLE.items():
        k = A.node_of(sc, name)
        row(k, '= ' + role)
        targets(k)
    log('THE CAMPAIGN\'S KEPT OBJECTS (CAMP) and what each names')
    for role, name in CAMP.items():
        for k in sc.resolve(R + name):
            row(k, '= ' + role)
            targets(k)
    log('SQUADS (stage, men with weapon and soldier row: skill, accuracy, health)')
    arms = {k: w for k, _s, w, _w2, _g1, _g2, _set in kl_arms.carriers(sc)}
    for t in sc.tops():
        if not kl_fa.has(sc, t, 'ZSquadScript'):
            continue
        stage = STAGE.get(sc.names[t], 'hall' if sc.names[t] in HALL else '-')
        row(t, '= %s' % stage)
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor':
                v = values(sc, k, 'ZSoldier')
                log('        man %s %-24s %s %g / %g' % (at(k), arms.get(k) or 'unarmed', v[3], v[4], v[7]))
    log('ESCAPE (the van at its waiting place; its boarding box, kill box and target ride on it: check() says where it stops)')
    for k in range(1, len(sc.nodes)):
        names = [sc.p.key(nm) for nm, _b in sc.nodes[k]['ctrls']]
        if any(n in names for n in (kl_fa.EXIT, kl_fa.MONITOR, 'OnlineEscAnimatedVehicle', 'FakeTarget')) or sc.names[k] == 'V_Van_00' and 'Reflection' not in sc.path[k]:
            row(k)
    log('LEVEL BOUNDS')
    for k, _i, _v in kl_fa.controllers(sc, 'LevelBound'):
        row(k)
    log('DOORS')
    for path, _stock, name in LEAVES + [(VAULT_BODY, VAULT_BODY_AT, 'THE VAULT DOOR')]:
        k = A.node_of(sc, path)
        log('  %-16s %-48s %s' % (name, sc.path[k][-48:], at(k)))


def check(folder, log=print, problems=None):
    """Every check of this layer on a built (and finished) folder -> [what is wrong]. problems: kl_graft.verify's
    list of the build, when the caller has it (else result.json beside the archive is read)."""
    import json, kl_route, kl_impact
    read_opts(folder)
    arch = archive_of(folder)
    import kl_fa_loot as L
    sc, scene, ents, pos, hvk, snd, loc, size = read_built(folder)
    bad = []
    def fail(s):
        bad.append(s); log('  FAIL: ' + s)
    # ---- kl_graft.verify, against KNOWN
    res = json.load(open(os.path.join(folder, 'result.json'))) if os.path.isfile(os.path.join(folder, 'result.json')) else {}
    if problems is None:
        problems = res.get('problems')
    if res.get('dangling'):                             # scene paths the build found naming nothing
        fail('the build left %d dangling scene paths: %s' % (len(res['dangling']), res['dangling'][:3]))
    every = [k for k, _i, _v in kl_fa.controllers(sc, 'ZSquadScript')]
    squads = [k for k in every if not sc.path[k][len(R):].startswith(BOT_SQUAD)]      # the enemies': the finishing chain's seven AI heisters are squads too
    known = KNOWN + (() if squads else (KNOWN_NO_AI,))  # what the BUILD is is read off the level: no squad of enemies = a NO_AI build
    for p in problems or ():
        why = next((w for t, w in known if t in p), None)
        log('  verify: %s %s%s' % ('known' if why else 'OPEN ', p[:200], '\n          = %s' % why if why else ''))
        if not why:
            fail('kl_graft.verify: ' + p[:200])
    # ... and what of the sound is really lost: result.json's 'stream_clips_missing' is a list by NAME (kl_maps.one's
    # reconstruction: a name is listed when any record of that name is a language-file one), the built .WHD says more
    listed, lost, have = lost_clips(folder, res)
    if listed:
        log('  sound: of the %d clip names result.json lists, %d have a streamed record in the built .WHD (they play from the installed stream file); '
            '%d have NO record = what a larger PC_Def.str would bring:%s' % (len(listed), len(listed) - len(lost), len(lost), ''.join('\n          ' + n for n in lost)))
        if any(n.lower() in have for n in MUSIC_CLIPS):
            fail('sound: MUSIC_CLIPS names %d clips that have a record in the built .WHD: the list for the owner is not the level\'s' % sum(n.lower() in have for n in MUSIC_CLIPS))
    # a build against a stream file that holds the music ('--str', the Music stage): all six clips or none
    in_whd = music_records(folder)
    if in_whd not in (0, len(MUSIC_CLIPS)):
        fail('sound: %d of the %d MUSIC_CLIPS have a streamed record in the built .WHD: a set is torn' % (in_whd, len(MUSIC_CLIPS)))
    if in_whd and listed:
        fail('sound: the music has its records but result.json still lists %d stream clips as missing' % len(listed))
    # ---- kl_fa.check on the written archive
    import kl_arms
    fa = kl_fa.check(sc, snd, loc, kl_arms.read_anm(arch))
    for f in fa:
        why = next((w for t, w in known if t in f.text), None) if f.sev <= kl_fa.BROKEN else None
        log('  kl_fa: %s%s' % (str(f)[:230], '\n          = known: %s' % why if why else ''))
        if f.sev <= kl_fa.BROKEN and not why:
            fail('kl_fa.check: ' + str(f)[:200])
    ncov = len(kl_fa.controllers(sc, 'FFCoverList'))
    log('  cover lists (FFCoverList): %d' % ncov)
    if ncov != 1:
        fail('%d cover lists (a level needs exactly one)' % ncov)
    # ---- the doors, read back: each leaf DOOR_DY under its stock place and without a placement, or in its place with one
    # (what the BUILD did is read off the level, not off this module's flags: a leaf is 'sunk' when it stands DOOR_DY low)
    per = collections.Counter(kl_hvk.ref(i) for s in hvk.shapes for i in s.inst)
    gates, vault_ref, state = [], None, {}
    for path, stock, name in LEAVES + [(VAULT_BODY, VAULT_BODY_AT, 'the vault door')]:
        k = A.node_of(sc, path)
        e = ents[k - 1]
        low = abs(pos[e][1] - stock[1] - DOOR_DY) < 2.0
        state[path] = low
        ok = (low or abs(pos[e][1] - stock[1]) < 2.0) and abs(pos[e][0] - stock[0]) < 2.0 and abs(pos[e][2] - stock[2]) < 2.0 and bool(per[e.ref]) != low
        log('  door %-16s %-34s REF %-6d at (%d, %d, %d), %d placement(s): %s' % (name, sc.names[k][-34:], e.ref, *pos[e], per[e.ref],
                                                                              'sunk, no collision' if low else 'in its place, collides'))
        if not ok:
            fail('door %s: at (%d, %d, %d) with %d placements; its place in the level is (%d, %d, %d)' % (sc.names[k], *pos[e], per[e.ref], *stock))
        if path == VAULT_BODY:
            vault_ref = e.ref
        if not low:
            gates.append(e.ref)
    animate, vault_open = not state[LEAVES[0][0]], state[VAULT_BODY]
    if len({state[p] for p, _at, _set in LEAVES}) != 1:
        fail('the eleven leaves are not all in one state: %s' % sorted(n.split('\\')[-1] for n, low in state.items() if low))
    lv = kl_route.load(folder)
    path_of = {e.ref: sc.path[k + 1] for k, e in enumerate(ents)}
    for ref, far in lv.moved():                         # the van's five key-framed bodies too: kl_map_escape.van_hvk puts them where it waits
        fail('REF %d (%s): its collision placement stands %d from its entity' % (ref, path_of.get(ref, '?')[-60:], far))
    # ---- every spawn point, player group and loot place: on the START's mesh part, on free floor
    pts, names = [START[1]], ['START']
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint' or sc.parent[k] == 0 and sc.names[k].startswith('Heroes!'):
            pts.append(pos[ents[k - 1]]); names.append(sc.names[k])
    rows = kl_route.stations(lv, pts, opened=gates, near=30)
    part = rows[0]['part']
    off = [(n, r) for n, r in zip(names, rows) if not (r['mesh'] and r['part'] == part and r['reached'])]
    log('  spawn points and player groups: %d places, %d on the mesh part of the START (%s polygons) and on free floor within 30' % (
        len(pts) - 1, len(pts) - 1 - len(off), rows[0].get('part_size')))
    for n, r in off:
        fail('%s at (%d, %d, %d): mesh %s, part %s, reached %s (gap %s)' % (n, *r['at'], r['mesh'], r['part'], r['reached'], r.get('gap')))
    # ---- nobody starts inside a level bound or one of its warning boxes, and no station of the round lies in one
    # (the campaign's own three stand at the front with warn boxes up to 10 m into the street: world boxes of the turned ones)
    fr, boxes = L.frames(scene), []
    for k, _i, v in kl_fa.controllers(sc, 'LevelBound'):
        for j in [k] + [j for lst in v[0:2] for s in lst for j in sc.resolve(s)]:
            Rm, T = fr[ents[j - 1]]
            ext = [sum(abs(Rm[a][b]) * h for b, h in enumerate(kl_fa.node_values(sc, j)[8:11])) for a in range(3)]
            boxes.append((sc.names[j], [T[a] - ext[a] for a in range(3)], [T[a] + ext[a] for a in range(3)]))
    held = [(n, p, b) for n, p in list(zip(names, pts)) + ROUTE_IN + ROUTE_VAULT + ROUTE_OUT for b, lo, hi in boxes
            if all(lo[a] <= (p[a] + (50 if a == 1 else 0)) <= hi[a] for a in range(3))]
    log('  level bounds: %d bound and warn boxes; %d of the %d spawn points, player groups and stations inside one' % (
        len(boxes), len(held), len(pts) + len(ROUTE_IN + ROUTE_VAULT + ROUTE_OUT)))
    for n, p, b in held:
        fail('%s at (%d, %d, %d) stands inside %s' % (n, *p, b))
    # loot: the pick-up test as read in kl2.exe (kl_fa_loot.in_reach: horizontal distance <= radius + 40, a height window)
    # from a place a walk reaches (kl_fa_loot.Floors), with MARGIN to spare. The walks start where the route test below
    # proves the crew comes: the vault's middle, the hall. Hidden things do not count here (the blown vault's rubble)
    loot = [(k, v) for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl') if 'DROP' not in v[2]]
    built = L.Built(arch)
    def named(role):
        return A.named(sc, A.node_of(sc, ROLE[role]))
    # the vault has TWO states when the blast is wired: what its ActivateGeom / DeactivateGeom name comes and goes
    # (whole subtrees). The loot must be takable, and not lie under rubble, in both
    sub = lambda paths: {ents[j - 1].ref for s in paths for k in sc.resolve(s) for j in range(k, sc.end[k])}
    on, off = sub(named('post on')), sub(named('pre off'))
    blast = bool(on or off)
    states = [('the vault intact', built.soft() | built.hidden)] + ([('blown', built.soft() | (built.hidden - on) | off)] if blast else [])
    walks = {}
    for what, skip in states:
        walks[what] = []
        for box, start in LOOT_WALKS:
            f = L.Floors(hvk, box, skip=skip)
            walks[what].append((f, f.flood([start])[0]))
    taken = 0
    for k, v in loot:
        at, radius = pos[ents[k - 1]], values(sc, k, 'TriggerBox2')[2]
        told, good = [], True
        for what, _skip in states:
            best = None
            for f, seen in walks[what]:
                place, h, n = f.stand(seen, at, radius)
                if place is not None and (best is None or h < best[1]):
                    best = (place, h, n)
            spare = radius + L.REACH_PAD - best[1] if best else None
            # buried: collision of that state 8..120 over the place, in its cell (the case itself has no collision)
            over = [built.name.get(r, str(r)).split('\\')[-1] for y, _fl, r in walks[what][0][0].w.grid.get(walks[what][0][0].w.cell(at[0], at[2])) or ()
                    if at[1] + 8 < y < at[1] + 120] if in_vault(at) else []
            told.append('%s: %s%s' % (what, 'from (%d, %d, %d), %d away, %d to spare' % (*best[0], best[1], spare) if best else 'OUT OF REACH',
                                    ', UNDER %s' % sorted(set(over))[:2] if over else ''))
            if best is None or spare < L.MARGIN:
                good = False
                fail('loot %s at (%d, %d, %d) cannot be taken (%s)%s' % (sc.names[k], *at, what, ' with %d to spare (%d wanted)' % (spare, L.MARGIN) if best else ''))
            if over:
                good = False
                fail('loot %s at (%d, %d, %d) lies under %s (%s)' % (sc.names[k], *at, sorted(set(over))[:3], what))
        log('  loot %-40s %7d at (%5d %5d %6d) %s; %s' % (sc.names[k][-40:], v[1], *at, 'hidden' if kl_fa.node_values(sc, k)[3] else 'shown ', '; '.join(told)))
        taken += good
    log('  loot: %d objects, %d; %d can be taken%s' % (len(loot), sum(v[1] for _k, v in loot), taken, ' in the intact and in the blown vault' if blast else ''))
    gated = {bool(kl_fa.node_values(sc, k)[3]) for k, _v in loot if in_vault(pos[ents[k - 1]])}
    for k, v in loot:
        tb = values(sc, k, 'TriggerBox2')
        hide = bool(kl_fa.node_values(sc, k)[3])
        teller_late = TELLER_LATE and not in_vault(pos[ents[k - 1]])        # TELLER_LATE: the stacks at the counters lie hidden too
        if hide != bool(ents[k - 1].flags & HIDDEN) or (hide and not in_vault(pos[ents[k - 1]]) and not teller_late) or len(gated) != 1 or (teller_late and not hide):
            fail('loot %s: hidden %s in the .prp, flag %#x in the .gms, in the vault %s' % (sc.names[k], hide, ents[k - 1].flags, in_vault(pos[ents[k - 1]])))
        if tb[2] != LOOT_REACH or tb[3] != 1:
            fail('loot %s: TriggerBox2 radius %s, people-only %s' % (sc.names[k], tb[2], tb[3]))
    # ---- the route in the built collision, nothing removed at test time; what still stands is a gate of the round
    way = [p for _n, p in ROUTE_IN + ROUTE_VAULT + ROUTE_OUT]
    crossing = lambda r: sorted({(o['ref'], o['name']) for leg in r['legs'] for c in leg.get('crossed') or () for o in c['objects']})
    say = lambda r: 'FREE, %d m' % r['length'] if r['free'] else 'NOT free; crossed: %s' % [n for _r, n in crossing(r)]
    shut = kl_route.route(lv, way)
    log('  route, %d stations, the level as built: %s' % (len(way), say(shut)))
    if shut['free'] != (not gates) or any(r not in gates for r, _n in crossing(shut)):
        fail('the route as built: free %s, crossed %s; the doors that stand: %d' % (shut['free'], [n for _r, n in crossing(shut)], len(gates)))
    if not vault_open and not animate:                  # the default: five sets open from the load, the vault door the one gate
        if [r for r, _n in crossing(shut)] != [vault_ref]:
            fail('with the vault door in its place the route should be shut by that door alone: %s' % [n for _r, n in crossing(shut)])
        gate = kl_route.route(lv, [p for _n, p in ROUTE_IN + ROUTE_OUT[1:]])
        log('  route without the vault (yard -> ante-room -> hall -> street), as built: %s' % say(gate))
        if not gate['free']:
            fail('the way in and out is not free without the vault')
    if gates:
        opened = kl_route.route(lv, way, opened=gates)
        log('  route with the %d standing door(s) out: %s' % (len(gates), say(opened)))
        if not opened['free']:
            fail('the route is not free with the standing doors out')
    if blast:                                           # kl_route counts hidden bodies: the runs above had BOTH vaults in the way
        after = kl_route.route(lv, way, opened=gates + sorted(off))
        log('  route after the blast (the standing door(s) and the %d bodies the blast takes away out, the blown vault in): %s' % (len(off), say(after)))
        if not after['free']:
            fail('the route is not free in the blown vault')
    # ---- the chain, read back
    camp = {r: (sc.resolve(R + n) or [None])[0] for r, n in CAMP.items()}
    for r, n in CAMP.items():
        if camp[r] is None:
            fail('the campaign\'s %s (%s) is not in the level' % (r, n))
    mine = [(ROLE[r], A.node_of(sc, ROLE[r])) for r in ROLE] + [(CAMP[r], k) for r, k in camp.items() if k is not None]
    for n, k in mine:
        for j in range(k, sc.end[k]):
            for s in A.named(sc, j):
                if not sc.resolve(s):
                    fail('%s names %s, which is no node' % (sc.path[j][5:], s))
    mon = named('monitor')
    starters = {R + ROLE['start timer'], R + ROLE['music timer']} | ({R + ROLE['doors']} if animate else set())
    if {s for s in mon if s[5:] in ROLE.values()} != starters:
        fail('the round start names %s of this layer\'s objects, wanted %s' % (sorted(s for s in mon if s[5:] in ROLE.values()), sorted(starters)))
    delay = lambda role: values(sc, A.node_of(sc, ROLE[role]), 'TriggerDelay2')[0]
    box, beat = named('beat box'), named('beat timer')
    if R + ROLE['beat timer'] not in box or R + ROLE['loot on'] not in beat:
        fail('the beat\'s chain is not box -> timer -> loot: %s / %s' % (box, beat))
    if values(sc, A.node_of(sc, ROLE['beat box']), 'TriggerBox')[BOX_PER_MAN]:      # 1 = again for every criminal that enters (wire())
        fail('the beat\'s box fires for every criminal that enters (TriggerBox field %d is not 0): the beat would begin again with each' % BOX_PER_MAN)
    rods = []
    for i in range(len(RODS)):
        t, w = 'rod timer %d' % (i + 1), 'rod %d' % (i + 1)
        got = [s for s in named(w)]
        ok = R + ROLE[t] in box and R + ROLE[w] in named(t) and got == [R + RODS[i]] and 0 < delay(t) < delay('beat timer') and (not rods or delay(t) > rods[-1])
        ok = ok and [v[MPA_MESSAGE] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == A.node_of(sc, RODS[i])] == [values(sc, A.node_of(sc, ROLE[w]), 'AIDWrapper')[1]]
        if not ok:
            fail('rod %d: the box names its timer %s, the timer (%.0f s) its wrapper %s, the wrapper %s' % (i + 1, R + ROLE[t] in box, delay(t), R + ROLE[w] in named(t), got))
        rods.append(delay(t))
    hid = [R + sc.names[k] for k, _v in loot if kl_fa.node_values(sc, k)[3]]
    ts = sc.resolve(R + CLOCK + '\\' + 'Teller_show')         # extras: the teller stacks come with their own switch after the hall
    tel = values(sc, ts[0], 'ActivateGeom')[1] if ts else []
    if sorted(named('loot on') + tel) != sorted(hid):
        fail('the loot\'s ActivateGeom names %d objects, %d are hidden' % (len(named('loot on')), len(hid)))
    last = {p: [v[MPA_LAST] for k, _i, v in kl_fa.controllers(sc, 'MatPosAnim') if k == A.node_of(sc, p)] for p, _at, _set in LEAVES if '\\GlassDoor_' in p}
    if animate and (sorted(named('doors')) != sorted(R + p for p, _at, _set in LEAVES) or any(v != [GLASS_LAST] for v in last.values())):
        fail('the leaves stand, but the round start names %d of them and the glass leaves store LAST %s' % (len(named('doors')), sorted(last.values())))
    if not animate and named('doors'):
        fail('the leaves are sunk, but the round start still sends %d of them \'Activate\'' % len(named('doors')))
    late = named('door timer')
    if (bool(named('door')) if VAULT_BLOW else vault_open == bool(named('door'))) or (bool(late) and R + ROLE['door timer'] not in beat):
        fail('the vault door is %s, but its wrapper names %s and its timer %s' % ('sunk' if vault_open else 'in its place', named('door'), late))
    # VAULT_SWING: the body goes on SWING_TIMER (named by the beat timer, S >= 8 s after it), not on the door timer
    sw = A.node_of(sc, SWING_TIMER) if sc.resolve(R + SWING_TIMER) else None
    swing = sw is not None and R + SWING_TIMER in beat
    if sw is not None and not swing:
        fail('%s is in the level but the beat timer does not name it' % SWING_TIMER)
    if VAULT_BLOW:                                      # vault_blow: the door timer (the blast's moment) switches off group + body + hinge
        sv = None
        offs = named('door off')
        if offs != [R + VAULT_DOOR, R + VAULT_BODY, R + VAULT_HINGE] or R + ROLE['door off'] not in late or not blast:
            fail('VAULT_BLOW: door off names %s, the door timer names it: %s, blast wired: %s' % ([x[-30:] for x in offs], R + ROLE['door off'] in late, bool(blast)))
        swing = False
    elif swing:
        sv = values(sc, sw, 'TriggerDelay2')
        if R + ROLE['door off'] in late or A.named(sc, sw) != [R + ROLE['door off']] or not named('door off') or sv[0] < 8.0:
            fail('the swing timer of the vault door: delay %s, names %s; the door timer also names the body: %s' % (sv[0], A.named(sc, sw), R + ROLE['door off'] in late))
    elif not VAULT_BLOW and bool(named('door off')) != (R + ROLE['door off'] in late):
        fail('the door\'s DeactivateGeom names %s and the door\'s timer %s it' % (named('door off'), 'names' if R + ROLE['door off'] in late else 'does not name'))
    booms = [camp[r] for r in ('boom 1', 'boom 2', 'boom 3') if camp[r] is not None]
    reach = sorted({tuple(values(sc, k, 'Explode')[j] for j in EXPLODE_REACH) for k in booms})
    if blast:
        want = [R + CAMP[r] for r in ('boom 1', 'boom 2', 'boom 3', 'blast sound')] + [R + ROLE['post on'], R + ROLE['pre off']]
        if any(s not in late for s in want) or R + VAULT_POST not in named('post on') or R + VAULT_PRE not in named('pre off') or camp['blast sound'] is None or not A.named(sc, camp['blast sound']):
            fail('the blast is wired in part only: the door\'s timer names %s' % [s.split('!')[-1] for s in late])
    elif any(R + CAMP[r] in late for r in ('boom 1', 'boom 2', 'boom 3', 'blast sound')):
        fail('no vault state is swapped, but the door\'s timer names the blast: %s' % late)
    lamps = [s for s in A.named(sc, camp['alarm lamps'])] if camp['alarm lamps'] is not None else []
    toggles = [k for k, _i, _v in kl_fa.controllers(sc, 'LightToggle')]
    lights = [k for k in range(1, len(sc.nodes)) if ('\\' + LAMP) in sc.path[k] and sc.cls(k) in ('ZOMNILIGHT', 'ZGateLightSpot')]
    # ... and the spinning spots' slaves in the rooms next door (strip): what a gate light's list names. Hidden with their masters
    slaves = sorted({j for k in lights if sc.cls(k) == 'ZGateLightSpot'
                     for s in kl_fa.node_values(sc, k)[J.labels('dd', 'ZGateLightSpot').index(SLAVES)] for j in sc.resolve(s)})
    is_dark = lambda k: bool(kl_fa.node_values(sc, k)[3] and ents[k - 1].flags & HIDDEN)
    dark, dark_s = [k for k in lights if is_dark(k)], [k for k in slaves if is_dark(k)]
    if len(lamps) != 11 or len(lights) != 22 or len(slaves) != 8 or (toggles and (dark or dark_s)) or (not toggles and len(dark + dark_s) != 30) \
            or R + CAMP['alarm lamps'] not in beat or (R + CAMP['lights off'] in beat) != bool(toggles):
        fail('the alarm: %d lamps named, %d lights and %d slave spots, %d LightToggle, %d + %d of them hidden; the white light goes off: %s' % (
            len(lamps), len(lights), len(slaves), len(toggles), len(dark), len(dark_s), R + CAMP['lights off'] in beat))
    music = [s for s in named('music timer')]
    live = lambda names: [p for p in (R + CAMP['music'] + '\\' + n for n in names) if sc.resolve(p) and kl_fa.has(sc, sc.resolve(p)[0], 'PlayMusicLayerFade')]
    four = sum(1 for _k, _i, v in kl_fa.controllers(sc, 'PlayMusicLayerFade') if v[0] == LAYER4)
    if music != [R + CAMP['music']] or R + CAMP['music out'] not in beat or any(p not in beat for p in live(MUSIC_FADE)) or any(p not in box for p in live(MUSIC_RISE)) \
            or len(live(MUSIC_FADE)) < 3 or four not in (0, 9):
        fail('the music: the round start\'s timer names %s; the beat\'s end the way-out set: %s' % (music, R + CAMP['music out'] in beat))
    log('  chain: round start -> %s; ante-room box -> rods at %s s, %d more -> %.0f s -> %d objects%s' % (
        [s.split('!')[-1] for s in mon], ', '.join('%.0f' % x for x in rods), len(box) - 1 - len(rods), delay('beat timer'), len(beat),
        '; -> %.0f s -> %s' % (delay('door timer'), [s.split('!')[-1].split('\\')[-1] for s in late]) if late else ''))
    log('  the beat: vault door %s; blast %s; alarm lamps %d, %s; music: break-in set at %.0f s, way-out set at the beat\'s end (%s)' % (
        'sunk at build time' if vault_open else 'is blown away whole with the blast (VAULT_BLOW)' if VAULT_BLOW else 'swings at the beat\'s end' + (', its body off %.0f s later%s' % (sv[0] if swing else delay('door timer'), ' (swing timer)' if swing else '') if named('door off') else ', stays'),
        'none (the vault stays intact)' if not blast else '%s: Explode reach %s, %d bodies come, %d go' % ('show' if reach == [(1.0, 1.0)] else 'REAL', reach, len(on), len(off)),
        len(lamps), '%d LightToggle' % len(toggles) if toggles else 'no LightToggle in the level, %d lights and %d slave spots hidden' % (len(dark), len(dark_s)),
        delay('music timer'), 'its %d clips have streamed records in the built .WHD: it plays once the stream file of the build is installed' % in_whd if in_whd
        else 'silent until the stream file has %d clips' % len(MUSIC_CLIPS))
        + '; %d fades of the fourth layer' % four)
    if in_whd and not four:                             # MUSIC_LAYER4's own note: without the nine fades the 'basic' layer is never faded out
        log('  NOTE: the music\'s clips are in the bank but the fourth layer\'s nine fades are not (build without --music-layer4): '
            'the break-in set\'s basic layer plays on under the way-out set (ASSUMPTION, MUSIC_LAYER4)')
    # ---- the enemies
    actors = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFActor']
    top_of = lambda k: sc.names[sc.top[k]]
    camp_sq, hall_sq = [k for k in squads if sc.names[k] in STAGE], [k for k in squads if sc.names[k] in HALL]
    more = sorted({top_of(k) for k in every} - set(STAGE) - set(HALL))
    men = [k for k in actors if top_of(k) in STAGE or top_of(k) in HALL]
    if squads:
        if len(camp_sq) != len(STAGE) or len(hall_sq) != len(HALL):
            fail('%d of the %d campaign squads and %d of the %d hall squads are in the level' % (len(camp_sq), len(STAGE), len(hall_sq), len(HALL)))
        # every man on the START's mesh part, on free floor (the doors that stand taken out: the plaza is beyond none)
        rows2 = kl_route.stations(lv, [START[1]] + [pos[ents[k - 1]] for k in men], opened=gates, near=30)
        off_mesh = [(k, r) for k, r in zip(men, rows2[1:]) if not (r['mesh'] and r['part'] == rows2[0]['part'] and r['reached'])]
        log('  enemies: %d campaign squads (%d men) + %d of F07\'s in the hall (%d men); %d of the %d men on the mesh part of the START and on free floor within 30' % (
            len(camp_sq), sum(top_of(k) in STAGE for k in men), len(hall_sq), sum(top_of(k) in HALL for k in men), len(men) - len(off_mesh), len(men)))
        for k, r in off_mesh:
            fail('%s at (%d, %d, %d): mesh %s, part %s, reached %s (gap %s)' % (sc.path[k][5:][-70:], *r['at'], r['mesh'], r['part'], r['reached'], r.get('gap')))
        # the places their routs name (cover, flank, defend, search): the hall's are this file's and must be on that part
        pts2, own = [], []
        pbox = sc.resolve(R + PLAZA_BOX)                # a build with PLAZA_OUTSIDE (read off the level): the box is in it
        plaza_sq = [t for t in camp_sq if STAGE[sc.names[t]] == 'plaza'] if pbox else []
        hall_sq_ = hall_sq + plaza_sq                   # ... and then the plaza squads' places are this file's too
        for t in camp_sq + hall_sq:
            for j in range(t + 1, sc.end[t]):
                if any(sc.p.key(nm) in A.BEHAVE for nm, _b in sc.nodes[j]['ctrls']):      # what its lists name, and its own children
                    for h in sorted({h for s in A.named(sc, j) for h in sc.resolve(s)} | {c for c in range(j + 1, sc.end[j]) if sc.parent[c] == j}):
                        if sc.top[h] == t and sc.cls(h) in ('ZBoxPrimitive', 'ZSTDOBJ') and all(sc.p.key(nm) == 'RunToCoverPosInfoRout' for nm, _b in sc.nodes[h]['ctrls']):
                            pts2.append(pos[ents[h - 1]]); own.append((h, t in hall_sq_))
        rows3 = kl_route.stations(lv, [START[1]] + pts2, opened=gates, near=86) if pts2 else [None]
        away = [(h, mine_, r) for (h, mine_), r in zip(own, rows3[1:]) if not (r['mesh'] and r['part'] == rows3[0]['part'])]
        log('  enemies: %d places their behaviour routs name; %d not on the START\'s mesh part (the campaign\'s own; a hunt\'s search box is a volume '
            'over the floor)%s' % (len(pts2), len(away), ''.join(
                '\n          %s (%d, %d, %d): %s off the mesh' % (sc.path[h][5:][-74:], *r['at'], r['off']) for h, _m, r in away[:12])))
        for h, mine_, r in away:
            if mine_:
                fail('the hall\'s %s at (%d, %d, %d) is not on the START\'s mesh part' % (sc.path[h][5:], *r['at']))
        # the crew fix after run V2, read off the level: where the hall's eight stand, and - when the plaza's squads
        # have a box of their own - that no place their routs go by is in the banking hall
        up = [k for k in men if top_of(k) in HALL and pos[ents[k - 1]][1] > 1000.0]
        if up and len(up) != sum(top_of(k) in HALL for k in men):
            fail('%d of the hall\'s %d police stand on the gallery, the others on the floor' % (len(up), sum(top_of(k) in HALL for k in men)))
        in_hall = [(h, r['at']) for (h, _m), r in zip(own, rows3[1:]) if sc.top[h] in plaza_sq and in_box(r['at'], HALL_BOX)]
        campaign = sum(1 for (h, _m), r in zip(own, rows3[1:]) if STAGE.get(sc.names[sc.top[h]]) == 'plaza' and in_box(r['at'], HALL_BOX))
        log('  enemies: the hall\'s police stand %s; the plaza\'s squads are started by %s; %d places of their routs lie in the banking hall%s' % (
            'ON THE GALLERY (HALL_UP)' if up else 'on the hall\'s floor', '%s at (%d, %d, %d), half %s (PLAZA_OUTSIDE)' % (
                PLAZA_BOX.split('!')[-1], *pos[ents[pbox[0] - 1]], tuple(round(x) for x in kl_fa.node_values(sc, pbox[0])[8:11])) if pbox else 'the foyer box',
            campaign, '' if pbox or not campaign else ' (the build of runs V0 .. V2: 28 guns in the hall - \'test --crew-fix\')'))
        for h, p in in_hall:
            fail('PLAZA_OUTSIDE: %s at (%d, %d, %d) is a place of a plaza squad inside the banking hall' % (sc.path[h][5:], *p))
        # nothing of a squad names a node that is not there; the kinds are the ones that ran live
        kinds = collections.Counter(sc.p.key(nm) for t in camp_sq + hall_sq for j in range(t, sc.end[t]) for nm, _b in sc.nodes[j]['ctrls'])
        for t in camp_sq + hall_sq:
            for j in range(t, sc.end[t]):
                for s in A.named(sc, j):
                    if not sc.resolve(s):
                        fail('%s names %s, which is no node' % (sc.path[j][5:], s))
        first = sorted(set(kinds) - A.PLAIN - A.BEHAVE)
        log('  enemies: controllers of the squads: %s' % dict(kinds))
        if first:
            fail('the squads hold controllers that are not kl_fa_author\'s plain squad kinds: %s' % first)
        # each squad is started by its stage's object and waits for it
        role_of = {'start': 'start timer', 'down': 'start timer', 'beat': 'beat box', 'plaza': 'plaza box' if pbox else 'speak box'}
        lists_ = {r: {sc.top[h] for s in named(r) for h in sc.resolve(s)} for r in ('start timer', 'beat box', 'speak box', 'beat timer')}
        if DOOR_WAIT and not VAULT_OPEN:                # the hall's police are named by the door's timer now
            lists_['beat timer'] |= {sc.top[h] for s in named('door timer') for h in sc.resolve(s)}
            hall_p = {R + n + '\\' + HALL_START for n in HALL}
            late_n = set(named('door timer')) | {x for s_ in named('door timer') for k in sc.resolve(s_) if kl_fa.has(sc, k, 'TriggerDelay2') for x in values(sc, k, 'TriggerDelay2')[4]} if not NO_AI else set()
            beat_n = set(named('beat timer')) | {x for s_ in named('beat timer') if s_ != R + ROLE['door timer'] for k in sc.resolve(s_) if kl_fa.has(sc, k, 'TriggerDelay2') for x in values(sc, k, 'TriggerDelay2')[4]}
            miss = sorted(p for p in hall_p if p not in late_n or p in beat_n) if not NO_AI else []
            if miss:
                fail('DOOR_WAIT: the hall police must fire from the door timer and not from the beat timer: %s' % miss[:3])
        if pbox:                                        # PLAZA_OUTSIDE: the box is no ROLE object (the default build does not keep it)
            lists_['plaza box'] = {sc.top[h] for s in A.named(sc, pbox[0]) for h in sc.resolve(s)}
            v = values(sc, pbox[0], 'TriggerBox')
            if (v[0], v[14], v[BOX_PER_MAN]) != (1, 'ECPS_FA_MERCONLY', 0) or lists_['speak box'] & set(plaza_sq):
                fail('PLAZA_OUTSIDE: %s has fields 0 / 14 / %d = %s, or the foyer box still names a plaza squad' % (PLAZA_BOX, BOX_PER_MAN, (v[0], v[14], v[BOX_PER_MAN])))
        wake_named = set()                              # STAGING: the squads of WAKE_SQUADS are named by the relays of their events (stage-check proves the rest)
        if STAGING:
            for ev in WAKE_EVENTS:
                for w in sc.resolve(R + CLOCK + '\\Wake_' + ev):
                    wake_named |= {sc.top[h] for s in A.named(sc, w) for h in sc.resolve(s)}
        by = collections.Counter()
        for t in camp_sq + hall_sq:
            r = role_of[STAGE[sc.names[t]]] if sc.names[t] in STAGE else 'beat timer'
            by[r] += 1
            if t not in lists_[r] and t not in wake_named:
                fail('%s is not named by %s' % (sc.names[t], ROLE.get(r, PLAZA_BOX)))
            if values(sc, t, 'ZSquadScript')[SQUAD_ACTIVE]:
                fail('%s is in the world from the load (ZSquadScript field %d)' % (sc.names[t], SQUAD_ACTIVE))
        # ... and nobody who comes LATER is put into the world where the crew may still be: no man of such a squad within
        # BEAT_CLEAR of a station of the round that lies before the squad's trigger, on that station's floor (a squad
        # that waits 'spawns in' when its rout is named: the 14 police of the beat stood in the vault lobby - BEAT_MEN)
        foyer = [n for n, _p in ROUTE_OUT].index('foyer')
        ahead = {'beat box': ROUTE_IN[:-1], 'beat timer': ROUTE_IN + ROUTE_VAULT, 'speak box': ROUTE_IN + ROUTE_VAULT + ROUTE_OUT[:foyer],
                 'plaza box': ROUTE_IN + ROUTE_VAULT + ROUTE_OUT[:foyer + 1]}
        close = []
        for k in men:
            r = role_of[STAGE[top_of(k)]] if top_of(k) in STAGE else 'beat timer'
            p = pos[ents[k - 1]]
            close += [(math.dist(p, q), sc.path[k][5:][-60:], n, p, top_of(k)) for n, q in ahead.get(r, ()) if abs(p[1] - q[1]) < 400.0]
        if GARRISON:                                    # the garrison's pockets are out of sight of every station of the way in (garrison_check (g), the exact ray): the distance rule does not apply to them
            close = [c for c in close if c[4] not in garrison_squads()]
        close.sort()
        log('  enemies: of the %d men who come after the round\'s start the nearest to a station that lies before his squad\'s trigger: %s' % (
            sum(top_of(k) not in STAGE or STAGE[top_of(k)] not in ('start', 'down') for k in men),
            '%s, %d from \'%s\'' % (close[0][1], close[0][0], close[0][2]) if close else '-'))
        for d, who, n, p, _sq in close:
            if d < BEAT_CLEAR:
                fail('%s at (%d, %d, %d) comes into the world %d from the station \'%s\', which the crew passes before his squad is started (%d wanted)' % (who, *p, d, n, BEAT_CLEAR))
        hunts = sum(1 for s in beat if s.endswith('\\' + HUNT))
        if GARRISON and hunts:
            fail('GARRISON: the beat timer names %d hunts' % hunts)
        rows_ = collections.Counter((values(sc, k, 'ZSoldier')[3], values(sc, k, 'ZSoldier')[4], values(sc, k, 'ZSoldier')[7]) for k in men if top_of(k) in STAGE)
        stock = sum(n for (skill, _a, _h), n in rows_.items() if skill == 'eCustom')
        log('  enemies: started by: %s; %d hunts at the beat\'s end; soldier rows of the campaign\'s men (skill, accuracy, health): %s' % (
            dict(by), hunts, ', '.join('%d x %s %g / %g' % (n, *r) for r, n in sorted(rows_.items(), key=lambda t: -t[1]))))
        if 0 < stock < sum(rows_.values()):
            fail('%d of the campaign\'s %d men have a stock row, the others Dead Men\'s' % (stock, sum(rows_.values())))
    else:
        log('  enemies: none (a build without squads)')
    if more:
        log('  enemies: squads that are not this file\'s: %s' % more[:8])
    # police who come back: the eight bodies (re/fed_respawn.md: 8 police bodies a level load) and their points, clear of the squads' men
    bodies = [k for k in range(1, len(sc.nodes)) if sc.parent[k] == 0 and sc.names[k].startswith('Heroes!Henchmen_')]
    back = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZSpawnPoint' and kl_fa.node_values(sc, k)[8] == 'eSPAWN_TYPE_FRAGILE_ALLIANCE_AFTER_DEATH']
    near = min([math.dist(pos[ents[a - 1]], pos[ents[b - 1]]) for a in bodies + back for b in men] or [9e9])
    log('  police who come back: %d bodies, %d AFTER_DEATH points; the nearest of the squads\' men stands %s from one' % (len(bodies), len(back), '%d' % near if men else '-'))
    if len(bodies) != 8 or len(back) != len(POLICE) or near < POLICE_CLEAR:
        fail('police who come back: %d bodies (8 wanted), %d points (%d), a squad\'s man %d from one (%d wanted)' % (len(bodies), len(back), len(POLICE), near, POLICE_CLEAR))
    # people: stock Fragile Alliance levels have 35..57 ZFFActor and 20..36 squads, Retomoto on the tab 99 / 55 (re/campaign_fa_tooling.md 5.4)
    cap = WAVES_ACTORS if WAVES else ACTORS_LIVE         # the waves build may pass what ran live (Retomoto 99 / 55) up to the largest stock story level (147) and the engine's 500 squads
    log('  people: %d ZFFActor in %d squads + 16 player bodies (ran live: %d actors, %d squads; allowed here: %d / %d%s)' % (
        len(actors), len(every), ACTORS_LIVE[0], ACTORS_LIVE[1], cap[0], cap[1], ' = the waves build: past what ran live' if cap is not ACTORS_LIVE and len(actors) > ACTORS_LIVE[0] else ''))
    if len(actors) > cap[0] or len(every) > cap[1]:
        fail('%d actors in %d squads: more than allowed (%d / %d)' % (len(actors), len(every), *cap))
    # ---- the escape: the one key-framed van on its road. kl_map_escape.van_check reads the WRITTEN files: who the
    # exit trigger calls, the keys against the road's height, the lane (five rays, every 20), the boxes at the stop,
    # the camera's eye and sight, the collision file; held against the plan in van.json when test() wrote one
    VL = ESC.Level(folder)
    plan, pj = None, os.path.join(folder, 'van.json')
    if os.path.isfile(pj):
        try:
            plan = plan_of(pj)
        except ValueError as x:
            fail('the van\'s plan beside the build: %s' % x)
    else:
        log('  van: no van.json beside the build: the drive is tested as the level has it, not against a plan')
    rep = ESC.van_check(VL, lambda s: log('  ' + s), plan)
    for x in rep['faults']:
        fail('van: ' + x)
    stop = wait = None
    if 'stop' not in rep:
        fail('van: %s' % '; '.join(rep['notes']))
    else:
        if any('FAEscCameraLAST' in x for x in rep['notes']):   # MEASURED: no such define in stock F07, F02, F05 either
            log('    (the stock form: no Dog Days Fragile Alliance level has that define - it is Dead Men\'s box, which the three car maps kept)')
        vans, fakes = kl_fa.controllers(sc, 'OnlineEscAnimatedVehicle'), kl_fa.controllers(sc, 'FakeTarget')
        N = ESC._van_nodes(sc, sc.top[vans[0][0]])
        ends_ = sorted({o for e in VL.ents for _p, oo in kl_graft.keys_tracks(e.raw) for o in oo} | {len(VL.scene.head)})
        K = ESC.VanKeys(VL.scene.head, VL.ents[N['V_Van_00'] - 1].raw, ends_, kl_graft.keys_tracks)
        drive = K.pos[:K.drive()]
        wait, stop, end, board = drive[0], drive[K.f2p[ESC._leg_frames(sc, N['F07_Escape_Vehicle_01'])['Activate_Enter'][1]]], drive[-1], tuple(rep['board'])
        # the road under the standing van (its origin stands VAN_UP over it)
        g = VL.G.under(stop[0], stop[1] + 20.0, stop[2])
        log('  van: the stop: origin y %.1f, the road under it y %s (%s); keys at most %.1f off the road\'s height on the whole drive; drive in %.0f m, away %.0f m' % (
            stop[1], '%.1f' % g[0] if g else '-', VL.name(g[1]) if g else 'NO GROUND', rep['height_off'], rep['length_in'] / 100.0, rep['length_out'] / 100.0))
        if g is None or abs(stop[1] - ESC.VAN_UP - g[0]) > 3.0:
            fail('van: the standing van\'s origin (y %.1f) is not %.0f over the road (%s)' % (stop[1], ESC.VAN_UP, '%.1f' % g[0] if g else 'no ground'))
        # the boarding place (the box rides on the van: in the file it stands at the waiting place): a station of the
        # round - on the START's mesh part, on free floor - and reached in the collision from the banking hall
        rows4 = kl_route.stations(lv, [START[1], board, tuple(stop)], opened=gates, near=BOARD_NEAR)
        b4 = rows4[1]
        out_way = [p for n, p in ROUTE_OUT if n in ('hall', 'front entrance', 'plaza')] + [board]
        walk = kl_route.route(lv, out_way, opened=gates)
        log('  van: boarding place at the stop (%d, %d, %d): mesh %s, part %s (the START\'s: %s), free floor within %d: %s; the van\'s stop: mesh %s, part %s; '
            'hall -> front entrance -> plaza -> boarding place in the collision: %s' % (*board, b4['mesh'], b4['part'], part, BOARD_NEAR, b4['reached'],
                                                                                     rows4[2]['mesh'], rows4[2]['part'], say(walk)))
        if not (b4['mesh'] and b4['part'] == part and b4['reached']):
            fail('van: the boarding place (%d, %d, %d) is no station of the round: mesh %s, part %s, reached %s (gap %s)' % (*board, b4['mesh'], b4['part'], b4['reached'], b4.get('gap')))
        if not walk['free']:
            fail('van: no free way from the banking hall to the boarding place: crossed %s' % [n for _r, n in crossing(walk)])
        # the van's own path blocker (eToggle: it blocks where the van STANDS): the boarding place must be outside it
        inside = lambda k, p, up=0.0: all(abs(sum(VL.frame(k)[0][a][b] * ((p[a] + (up if a == 1 else 0.0)) - VL.frame(k)[1][a]) for a in range(3)))
                                          <= VL.values(k)['ZBoxPrimitive[%d]' % b] for b in range(3))
        pb = N['PathBlockerVan']
        log('  van: PathBlockerVan at (%d, %d, %d) half %s: the boarding place is %s it' % (
            *VL.place(pb), tuple(round(VL.values(pb)['ZBoxPrimitive[%d]' % b]) for b in range(3)), 'INSIDE' if inside(pb, board, 50.0) else 'outside'))
        if inside(pb, board, 50.0):
            fail('van: the boarding place lies inside the van\'s path blocker: an AI heister cannot be sent there')
        # the exit box calls the van: entered on the plaza, on the way to the boarding place - not from inside the bank
        ex = [k for k, _i, _v in kl_fa.controllers(sc, kl_fa.EXIT)]
        where = {n: [inside(k, p, 50.0) for k in ex] for n, p in ROUTE_OUT if n in ('hall', 'front entrance', 'plaza')}
        # (and, the stock form: the box holds the van's stop and its boarding place - 12 of 12 stock vans of F01 F04 F05 F07)
        at_van = [any(inside(k, p, 50.0) for k in ex) for p in (stop, board)]
        log('  van: exit trigger(s) %s: holds the hall %s, the front entrance %s, the plaza %s, the van\'s stop %s, the boarding place %s; drive in %.1f s' % (
            [sc.names[k].split('!')[-1] for k in ex], *[any(where[n]) for n in ('hall', 'front entrance', 'plaza')], *at_van, rep['seconds'][0]))
        if len(ex) != 1 or any(where['hall']) or not any(where['plaza']) or not all(at_van):
            fail('van: %d exit trigger(s); the hall inside one: %s, the plaza: %s, the van\'s stop: %s, the boarding place: %s (wanted: one, no, yes, yes, yes)' % (
                len(ex), any(where['hall']), any(where['plaza']), *at_van))
        # level bounds: neither the stop nor the boarding place in a bound or warn box; a bound on the drive AWAY is
        # the stock form (every stock van passes one with its passengers aboard: BOUND_AFTER), not at the stop itself
        hold = [(n, b) for n, p in (('the van\'s stop', stop), ('the boarding place', board)) for b, lo, hi in boxes
                if all(lo[a] <= (p[a] + (50 if a == 1 else 0)) <= hi[a] for a in range(3))]
        for n, b in hold:
            fail('van: %s lies inside %s' % (n, b))
        for nm, a, b in rep['bounds']:
            ok = b < 0 or a >= BOUND_AFTER
            log('  van: the drive passes the level bound %s %.1f .. %.1f m %s the stop: %s' % (
                nm.split('!')[-2] if '!' in nm else nm, abs(a) / 100.0, abs(b) / 100.0, 'before' if b < 0 else 'after',
                'the van is empty there' if b < 0 else 'players aboard - the stock form (stock vans: 10.9 .. 105 m after their stops)' if ok else 'TOO NEAR THE STOP'))
            if not ok:
                fail('van: the level bound %s lies on the drive %d .. %d from the stop (after it: at least %d)' % (nm, a, b, BOUND_AFTER))
        # nobody starts in the lane: spawn points, player bodies, the squads' men (at the street's height: the
        # ante-room lies under the square) - and nobody is SENT into it: the escape marker and the stations of the way
        # out (the van is called from the plaza and its kill box rides at its nose: ESC_AT)
        P2 = ESC.Poly([tuple(p) for p in drive])
        sent = [('the escape marker', pos[ents[A.node_of(sc, 'FASpecials!POI!POI_TheEscapeArea') - 1]])] + [('station \'%s\'' % n, p) for n, p in ROUTE_OUT]
        near_ = sorted((abs(P2.project(p)[1]) if 0.0 < P2.project(p)[0] < P2.len else min(math.dist(p, drive[0]), math.dist(p, drive[-1])), n, p)
                       for n, p in list(zip(names, pts))[1:] + [(sc.path[k][5:][-50:], pos[ents[k - 1]]) for k in men] + sent if abs(p[1] - stop[1]) < 400.0)
        mark = next(d for d, n, _p in near_ if n == sent[0][0])
        log('  van: the escape marker stands %d from the drive, %d from the boarding place at the stop' % (mark, math.dist(sent[0][1][::2], board[::2])))
        log('  van: of %d spawn points, player bodies, men, the marker and stations of the way out at the street\'s height the nearest to the drive is %s' % (
            len(near_), '%s, %d from it' % (near_[0][1], near_[0][0]) if near_ else '-'))
        for d, n, p in near_:
            if d < LANE_CLEAR:
                fail('van: %s at (%d, %d, %d) stands %d from the van\'s drive (%d wanted)' % (n, *p, d, LANE_CLEAR))
        # is the waiting van seen from where the crew comes out? (said, not a rule: 'out of sight' is the lead's wish)
        eyes = [(n, (p[0], p[1] + 160.0, p[2])) for n, p in ROUTE_OUT if n in ('front entrance', 'plaza')] + [('the boarding place', (board[0], board[1] + 160.0, board[2]))]
        solid = lambda e: [VL.name(r) for _d, r in VL.G.between(e, (wait[0], wait[1] + 100.0, wait[2])) if 'ColiObj' not in VL.name(r)]   # a ColiObj is not drawn
        seen = ['%s: %s' % (n, 'hidden by %s' % solid(e)[0] if solid(e) else 'SEEN (%d m)' % (math.dist(e, wait) / 100.0)) for n, e in eyes]
        log('  van: waits at (%d, %d, %d), %.0f m from its stop; from %s' % (*wait, math.dist(wait, stop) / 100.0, '; from '.join(seen)))
        want_fakes = 0 if VAN_LATE and VAN_NO_TARGET else 1
        if len(vans) != 1 or len(fakes) != want_fakes:
            fail('van: %d OnlineEscAnimatedVehicle and %d FakeTarget in the level (one van, with %s, is wanted: an unused van\'s target is the 0x686a66 crash)' % (
                len(vans), len(fakes), 'no target (VAN_LATE: the police have nothing to aim at while it waits)' if not want_fakes else 'its one target'))
    # ---- the van's ZFakeTarget: inside the vision space, by kl_fa_bots_dyn's rule (the 0x686a66 crash: a target that
    # cannot register writes behind ZCheckVisible's table every frame; re/crash_686a66.md). The rule is for the place
    # at the LOAD; where the drive takes it is said beside it ('a registered target that later leaves the grid is
    # harmless': the note's section on 0x79bae0)
    try:
        import kl_fa_bots as FB, kl_fa_bots_dyn as D
        B = FB.Built(folder)
        space = D.vision_space(B)
        log('  ' + D.space_words(space)[:330])
        for f in D.fake_targets(B, space):
            good = space is not None and f['out'] is None and f['cell'][1] and f['cell_sure'][1]
            log('  FakeTarget %s at (%d, %d, %d): %s' % (f['path'].split('\\')[0], *f['at'], 'inside the vision space, kl2\'s arithmetic gives a record'
                                                      if good else 'OUTSIDE the vision space (%s)' % (f['out'],)))
            if not good:
                fail('FakeTarget %s at (%d, %d, %d) cannot register (outside by %s)' % (f['path'].split('\\')[0], *f['at'], f['out']))
            if stop is not None and space is not None:
                later = [(n, D.outside(space, tuple(f['at'][a] + p[a] - wait[a] for a in range(3)))) for n, p in (('the stop', stop), ('the end of the drive', end))]
                log('    on the drive: %s' % '; '.join('at %s %s' % (n, 'inside' if o is None else 'outside by (%d, %d, %d)' % o) for n, o in later))
    except (ImportError, AttributeError) as x:
        log('  FakeTarget: NOT CHECKED (%s: %s)' % (type(x).__name__, x))
    # ---- texts
    keys = kl_fa.loc_keys(loc) or set()
    st = kl_fa.controllers(sc, kl_fa.SETTINGS)[0][2]
    for f, w in START_FIELDS.items():
        if st[f] != START_KEY % w or st[f].lower() not in keys:
            fail('settings field %d is %r%s' % (f, st[f], '' if st[f].lower() in keys else ', which is no key of the level\'s .LOC (finish() not run?)'))
    for key in TEXTS:
        if key.lower() not in keys:
            fail('text key %s is not in the level\'s .LOC (finish() not run?)' % key)
    for f, s in LINES.items():
        if st[f] != s or not kl_fa.spoken(keys, s):
            fail('settings field %d is %r, wanted %r in the .LOC' % (f, st[f], s))
    log('  texts: %d keys of the level\'s own, %d lines' % (len(TEXTS), len(LINES)))
    # ---- weight
    for b in kl_impact.check(arch):
        fail('kl_impact: ' + b[:200])
    blocks = 32.0 + sum(size[e] + 0x60000 for e in ('.prm', '.fxc', '.anm')) / 1e6 + size['.wav'] / 1e6
    log('  chunk table: %d entries (the tools\' line: %d); .prm %.1f, .fxc %.1f, .ANM %.1f, .WAV %.1f MB; the five load blocks %.0f MB (the Retomoto build that loaded seven times in one process: %.0f)' % (
        size['entries'], kl_impact.CHUNK_SAFE, size['.prm'] / 1e6, size['.fxc'] / 1e6, size['.anm'] / 1e6, size['.wav'] / 1e6, blocks, BLOCKS_LIVE))
    if blocks > BLOCKS_LIVE:
        fail('the five load blocks are %.0f MB, more than has loaded live (%.0f)' % (blocks, BLOCKS_LIVE))
    import kl_chars as C
    E = L.Edit(folder)                                  # read only: nothing of it is saved
    dead, _saved = C.dead_indices(E.p, E.sc, E.raw, E.oct, E.extra, lambda *a: None)
    log('  chunk table: %d of its indices are dead (free for the wardrobe, which takes %d with the four plates, and the gun looks)' % (dead, WARDROBE_CHUNKS))
    worn = os.path.isfile(os.path.join(folder, 'KLWardrobe.ini'))      # the finishing chain's folder: the wardrobe is in, the room it wanted is taken
    if worn:
        log('  chunk table: KLWardrobe.ini is there - the wardrobe is in the level, no room is asked for it')
    if size['entries'] > kl_impact.CHUNK_SAFE or (dead < WARDROBE_CHUNKS and not worn):
        fail('chunk table %d entries (line %d) with %d dead indices (the wardrobe wants %d)' % (size['entries'], kl_impact.CHUNK_SAFE, dead, WARDROBE_CHUNKS))
    # ---- kl_graft.verify's cross-references on the level AS WRITTEN (the build's own verify ran before finish() and
    # before every step of the finishing chain)
    for b in reverify(folder, log):
        fail('written level: ' + b[:200])
    # ---- the waves, the reset and the late van (only a folder the step 'extras' has been through): the round-restart rule
    # (every node the module switches in a round is named by the reset list or is one of RESET_CANNOT) and the wave rules
    if os.path.isfile(os.path.join(folder, 'extras.json')):
        for b in waves_check(folder, lambda *a: None):
            fail('extras: ' + b[:240])
    # ---- the garrison (--garrison): the hard rules of garrison_check, on a folder the chain has given its bots (bots.json)
    log('  note: ' + STAGE2_NOTE)
    if GARRISON and os.path.isfile(os.path.join(folder, 'bots.json')):
        for b_ in garrison_check(folder, lambda *a: None):
            fail('garrison: ' + b_[:240])
    # ---- the voice (--voice): Dog Days cannot read IMA ADPCM speech from the stream file (re/luvsic_pass.md 1.1)
    left = streamed_singles(folder)
    log('  voice: %d streamed single IMA ADPCM record(s) in the built .WHD%s' % (len(left), '' if VOICE else ' (--voice is off in this build: reported, not judged)'))
    if VOICE and left:
        fail('voice: %d streamed single IMA ADPCM records are left (Dog Days cannot read them from the stream file; kl_voice.stream_clip refused them): %s' % (len(left), left[:3]))
    log('kl_fa_bank.check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ the seven AI heisters (the finishing chain)
# tools/kl_fa_bots.py plans the squad of this level without a table entry of its own: START row -> the dock's
# ENTERS box -> vault lobby -> the two flights -> the vault's loot -> back up -> airlock stairs -> hall -> the front
# entrance's EXITS box -> the exit box -> beside the van's stop (re/bank_campaign.md F.3). What it cannot know is
# THE VAULT DOOR: the mesh runs through it, the door's body stands until DOOR_GONE after the beat's end and the
# loot is hidden until then (a take message to a hidden object is dropped, kl2 0x6cdb65: kl_fa_bots.cannot_take).
# So bots() changes the PLAN between kl_fa_bots.plan and its apply (kl_fa_bots.plan is wrapped for the length of
# one build, as Doors wraps kl_escape): the last way station before the loot becomes seven places IN THE ANTE-ROOM,
# inside the beat's box, and a TriggerDelay2 stands behind it in every squad's chain - kl_fa_bots' own two-stop form
# (make(): a wait without loot is a plain timer), which kl_fa_bots_dyn reads as 'a rally' and holds at cover during.
# THE GATE IS A CLOCK, NOT THE EVENT, on purpose: a bot stands in the box, so the beat began when it arrived at the
# latest (ASSUMPTION: an AI heister trips an ECPS_FA_MERCONLY box - re/retomoto_bots_rooms.md 8, 'measured in
# effect'), and beat + DOOR_GONE later the door's body is off whatever the swing did. Naming the squads' next step
# from the beat's timer instead would start it while a hold timer of the way in may still be armed; that timer then
# starts a step of the way in for a bot that is in the vault and the chain cannot come back (a step starts once:
# re/retomoto_bots_rooms.md 9.1, 'the join'). The price: a bot that arrives when the vault is open still waits.
# If the assumption is wrong and no human is in the ante-room, the bots walk on to a shut door after the wait and
# their loot wait runs out: they leave without the vault's money (nothing worse).
BOT_SQUAD = 'Gameplay!merc_bot_squad!'  # kl_fa_bots.SQUAD (that module is imported only where the squad is made or read)
# kl_fa_bots.RECIPE's M03_FA_A row ('cases', 'lane', 'window') without its drop link. GUESS, this file's own: ONE stop (that
# row has kl_fa_bots.STOP_MAX; the tellers' stacks are left to the loot tactic) and a loot wait of 30 s
BOT_OPT = {'stops': 1, 'cases': 'glass', 'lane': True, 'window': True, 'loot_seconds': 30}
GATE_AT = (400.0, -960.0, -11900.0)     # GUESS: the ante-room's middle, 6 m before the vault door (z -12509); the seven places are the mesh's round it
GATE_REACH = 400.0                      # ... within this of it
GATE_MORE = 2.0                         # s on top of the beat's and the door's delay, both read from the built level. GUESS
GATE_NAME = '020_Timer_vault_opens'     # no 'done_looting' in it: kl_fa_bots.check and kl_fa_bots_dyn take it for a wait that is no loot wait
GATE_CLEAR = 100.0                      # a place before the gate keeps kl_fa_bots.LOOT_WINDOW + this from the vault's hidden loot. GUESS


def bots_gate(B, P, log=print):
    """kl_fa_bots' plan P of built level B (a kl_fa_bots.Built) with the vault gate -> P (changed in place)."""
    import kl_fa_bots as F
    sc = B.sc
    loot = [i for i, s in enumerate(P['stations']) if s['kind'] == 'loot']
    if len(loot) != 1 or len(P['waits']) != 1 or P['waits'][0]['cases'] or not P['waits'][0]['loot']:
        raise ValueError('kl_fa_bank.bots_gate: the plan has %d loot stations and %d waits (wanted: one stop, the vault, no case)' % (len(loot), len(P['waits'])))
    i_loot, i_gate = loot[0], loot[0] - 1
    at_loot = [B.at(k) for s in P['waits'][0]['loot'] for k in sc.resolve(s)]
    if i_gate < 1 or P['stations'][i_gate]['kind'] != 'way' or not all(in_vault(p) for p in at_loot):
        raise ValueError('kl_fa_bank.bots_gate: the richest loot is not the vault\'s, or no way station stands before it')
    delay = {sc.path[k]: v[0] for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2')}
    seconds = delay[R + ROLE['beat timer']] + delay[R + ROLE['door timer']] + GATE_MORE
    box = sc.resolve(R + ROLE['beat box'])[0]
    nav = F.Nav(B.scene.nav)
    home = nav.part[nav.at(*P['bots'][F.BOTS[0]]['start'])[0]]
    far = F.LOOT_WINDOW[0] + GATE_CLEAR
    cands = [c for c in nav.around(GATE_AT, GATE_REACH, home, dy=60.0)
             if B.in_box(box, c[:3]) and all(math.dist(c[:3], q) >= far for q in at_loot)]
    if ROOM_GATES:                              # ROOM_GATES: 400 from every post of a man of the ante-room's squad (start and defend place, whatever the room gates name)
        import kl_fa_bots_rt as RT
        sq_ = RT.enemy_squads(B)
        posts_ = RT.enemy_posts(B, sq_)
        mine_ = [q for t in sq_ if squad_stage(sc, t) == 'down' for _w, q, _r in posts_[t] if q[1] < -900.0]
        cands = [c for c in cands if all(abs(q[1] - c[1]) > RT.FLOOR_DY or RT.hdist(c, q) >= ROOM_POST_CLEAR for q in mine_)]
    got = nav.spots(cands, 7, F.SEP, ref=GATE_AT)
    if len(got) < 7:
        raise ValueError('kl_fa_bank.bots_gate: only %d places for seven round %s inside the beat\'s box and %d from the vault\'s loot' % (len(got), GATE_AT, far))
    st = P['stations'][i_gate]
    st.update(what='the ante-room: the hold until the vault is open (%g s)' % seconds, distinct_places=7, places=[[round(v, 1) for v in g[:3]] for g in got])
    for b, N in enumerate(F.BOTS):
        P['bots'][N]['places'][i_gate] = [round(v, 1) for v in got[b][:3]]
    # the chain as kl_fa_bots' two-stop form: stop 0 = the ante-room with a plain timer, stop 1 = the vault
    steps = []
    for s in [s for s in P['steps'] if s['leg'] == 'in']:
        idx = [i for i in s['stations'] if i != i_loot]
        if idx:
            steps.append({'name': '%03d_DefendBehaviour_to_loot' % (10 + len(steps)), 'leg': 'in', 'stop': 0, 'stations': idx})
    if steps[-1]['stations'][-1] != i_gate:
        raise ValueError('kl_fa_bank.bots_gate: the way in does not end at the ante-room')
    steps.append({'name': '030_DefendBehaviour_to_loot', 'leg': 'in', 'stop': 1, 'stations': [i_loot]})
    for m, s in enumerate(s for s in P['steps'] if s['leg'] == 'out'):
        steps.append(dict(s, name='%03d_DefendBehaviour_out' % (50 + m)))
    P['steps'] = steps
    w = P['waits'][0]
    w.update(name='040_Timer_done_looting', stop=1, timer='038_Timer_at_cases')
    P['waits'] = [collections.OrderedDict(name=GATE_NAME, stop=0, seconds=seconds, loot=[], worth=0, timer='018_Timer_at_cases', relays=[], cases={}), w]
    P['gate'] = {'station': i_gate, 'seconds': seconds, 'box': ROLE['beat box'], 'places': st['places'],
                 'nearest_hidden_loot': round(min(math.dist(g[:3], q) for g in got for q in at_loot))}
    note = ('THE VAULT GATE: station %d is seven places in the ante-room round (%d, %d, %d), inside %s and %d or more from the vault\'s loot; every squad '
            'waits %g s there (%s, a plain timer: the beat\'s %g s + the door\'s %g s + %g) before its step into the vault'
            % (i_gate + 1, *[sum(g[i] for g in got) / 7 for i in range(3)], ROLE['beat box'], P['gate']['nearest_hidden_loot'], seconds, GATE_NAME,
               delay[R + ROLE['beat timer']], delay[R + ROLE['door timer']], GATE_MORE))
    P['notes'].append(note)
    log('  NOTE ' + note)
    log('steps: %s' % [(s['name'], s['stations']) for s in steps])
    if ROOM_GATES:
        rooms_plan(B, P, log)
        if P.get('vault_gates'):
            rooms_note(P, log)
            log('steps: %s' % [(s['name'], s['stations']) for s in P['steps']])
        else:
            log('  NOTE ROOM_GATES: no man stands in any gated room - no gates (a build without enemies): the plan is the one without them')
    return P


def bots(src, dst, log=print, gates=None, rooms=None, hide=None):
    """The seven AI heisters into a COPY of a finished build of this level: kl_fa_bots.build with BOT_OPT and the
    vault gate (bots_gate) -> (kl_fa_bots' findings, its report). The dynamic step, cover, guns and talk are the
    other tools' own commands on the result (re/bank_campaign.md F)."""
    import kl_fa_bots as F
    global ROOM_GATES, ROOM_ON, ROOM_HIDE
    read_opts(src)
    if gates is not None:
        ROOM_GATES = bool(gates)
    if rooms is not None:
        ROOM_ON = tuple(rooms)
    if hide is not None:
        ROOM_HIDE = bool(hide)
    plan0, apply0 = F.plan, F.apply
    F.plan = lambda B, opt=None, log=print: bots_gate(B, plan0(B, opt, log), log)
    if ROOM_GATES:                              # the rooms' TriggerActorsDead nodes: kl_fa_bots_rt's Street.gate_nodes, called by apply (its `more`)
        import kl_fa_bots_rt as RT
        F.apply = lambda B, P, dst_, log_=print, more=None: apply0(B, P, dst_, log_, more=RT.Street(None, None, P['vault_gates']) if P.get('vault_gates') else more)
    try:
        out = F.build(src, dst, dict(BOT_OPT), log)
        if ROOM_GATES:                          # the file beside the archive keeps its keys (no_ai ... are not module flags that read_opts restores): the three of the gates are set in it
            import json
            fp = os.path.join(dst, OPTS_FILE)
            o_ = json.load(open(fp)) if os.path.isfile(fp) else {}
            o_.update(room_gates=True, room_on=list(ROOM_ON), room_hide=ROOM_HIDE)
            with open(fp, 'w') as f_:
                json.dump(o_, f_, indent=1)
        return out
    finally:
        F.plan, F.apply = plan0, apply0


def bots_check(folder, log=print):
    """What kl_fa_bots.check / kl_fa_bots_dyn.check do not know of this level, on a folder with the squad (with or
    without the dynamic step) -> list of faults: every squad's chain has the gate's timer, at least the beat's and
    the door's delay long, started by a step whose last place is inside the beat's box; and no place of any squad
    before the gate lies in the loot window of a vault object (hidden until the beat's end: a bot with a heist
    stage goes for it, kl2 0x8b94d0, and cannot take it)."""
    import kl_fa_bots as F
    read_opts(folder)
    B = F.Built(folder)
    sc, bad = B.sc, []
    def fail(s):
        bad.append(s); log('  FAIL ' + s)
    delay = {sc.path[k]: v[0] for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2')}
    need = delay[R + ROLE['beat timer']] + delay[R + ROLE['door timer']]
    box = sc.resolve(R + ROLE['beat box'])[0]
    money = [o for o in F.money_objects(B) if in_vault(o['at'])]
    hidden = [o for o in money if B.ents[o['node'] - 1].flags & HIDDEN]
    tops = [t for t in sc.tops() if sc.names[t].startswith(F.SQUAD + 'Squad#')]
    defend = {k: v for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout')}
    if len(tops) != len(F.BOTS):                        # a folder without the squad must not pass (review round 1)
        fail('%d squads of AI heisters in the level, %d wanted' % (len(tops), len(F.BOTS)))
    near, n_place, n_gate = None, 0, 0
    for t in tops:
        mine = range(t, sc.end[t])
        gate = [k for k in mine if sc.names[k] == GATE_NAME]
        if len(gate) != 1 or delay[sc.path[gate[0]]] < need:
            fail('%s: %d timer(s) %s%s (the beat\'s and the door\'s delay: %g s)' % (sc.names[t], len(gate), GATE_NAME,
                 ' of %g s' % delay[sc.path[gate[0]]] if gate else '', need))
            continue
        # who starts the timer: Defend steps of this squad (after the dynamic step also a RandomTrigger's ways' last steps)
        ends = [B.at(sc.resolve(v[1][-1])[0]) for k, v in defend.items() if k in mine and v[1] and any(j == gate[0] for s in v[7] for j in sc.resolve(s))]
        if not ends or not all(B.in_box(box, p) for p in ends):
            fail('%s: %d step(s) start %s, their last places %s: not all inside %s' % (sc.names[t], len(ends), GATE_NAME, [tuple(round(x) for x in p) for p in ends], ROLE['beat box']))
        n_gate += 1
        # the places BEFORE the gate: both tools number a chain's steps in blocks, the gate's block is GATE_NAME's
        before = lambda k: sc.names[sc.parent[k]][:3].isdigit() and int(sc.names[sc.parent[k]][:3]) < int(GATE_NAME[:3])
        for k in mine:
            if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#') and before(k):
                n_place += 1
                for o in money:
                    d = math.dist(B.at(k), o['at'])
                    near = d if near is None else min(near, d)
                    if F.in_window(B.at(k), o['at']):
                        fail('%s: place %s at (%d, %d, %d) before the gate is %d from the vault\'s %s: inside the loot window' % (
                            sc.names[t], sc.path[k].split('\\', 2)[-1], *B.at(k), d, sc.names[o['node']]))
    if ROOM_GATES:
        bad += rooms_check(folder, log)
    log('kl_fa_bank.bots_check %s: %d squads, %d with the gate (%s >= %g s); %d places before the gate, the nearest %s from one of the vault\'s %d money '
        'objects (%d hidden at the load; the window is %d): %s' % (folder, len(tops), n_gate, GATE_NAME, need, n_place, '%d' % near if near is not None else '-',
                                                                 len(money), len(hidden), F.LOOT_WINDOW[0], 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ ROOM GATES (after live run W4; 2026-10-12; OFFLINE: built and checked, NOT RUN IN THE GAME)
# RUN W4 (the full map, 100 actors, an idle human; re/bank_campaign.md 'Gates, after run W4'): ALL SEVEN AI HEISTERS DEAD GO + 29 .. 68 s, every one at heist stage 1, none past
# the vault lobby. MEASURED on the log (C:/kl_scratch/vault_gates/w4.py, analyse.py): the first hit comes at GO + 11 s IN THE START YARD, from the dock's guards through the open roller
# door (12 .. 18 m, a free line under the module's rules for the three bots on the START rows); the crew then walked the whole way in without a stop - dock, the stair up in the west,
# the corridor, the vault lobby - at 1 .. 2 hits a second from 3 .. 6 men, and two bots died by the point-blank rule ('ONE STEP', 203 and 118: re/melee_damage.md) beside the
# lobby guard whose start stands 29 from the way. What took Retomoto's crew from 'six dead by GO + 79 .. 122 s' to 'nobody dead before GO + 175 s' is built here
# (kl_fa_bots_rt GATES; Retomoto's planner is IMPORTED and called with this level's table, the way kl_fa_club does it; the helper pick_holds_bank is lifted from kl_fa_club.pick_holds_club
# with its score changed - a note where it came from at the function): the way is cut into ROOMS; before each room the seven HOLD at distinct cover places at its mouth and the chain goes
# on only through a TriggerActorsDead that names the room's men (dead, or the game's own limit: 0x7800 ticks = 30 s after the hold step called its place reached).
# THE BUDGET IS THE LIMIT. A gate that wins nothing costs 30 s. The no-enemy round (W3) called the van at GO + 164 s at the latest (MEASURED: 'heist stage 2 -> 3' 03:26:21.9 .. 03:26:27.2,
# GO 03:23:43.1), the round is 360 s from the round-start event (GO - 8.5 s) and the van must be called ROOM_VAN_MARGIN s before its end: 360 - 60 - 8.5 - 164 = 127 s = FOUR gates.
# So four rooms are gated (ROOM_ON): the dock (from the yard), the vault lobby (with the west corridor), the flights, and the banking hall on the way out; the airlock and the front are
# rooms of the table that stay OFF for the budget (--gate-rooms adds them, the timetable then refuses past the budget).
# 'dyn' (kl_fa_bank.py dyn): the dynamic step with NO hold of its own behind any gate and no fork between gates (the club's wrapper, lifted).
# MEN MOVED (CLEAR_MEN; applied in strip() under ROOM_GATES, nobody removed): every man of the 'start' and 'down' squads whose start stood less than ROOM_LINE_CLEAR (160 = the point-blank
# reach of re/melee_damage.md) from the crew's line - the stand-in path through the stations AND the places bots were hit in W4 - goes to the nearest place that is on the START's mesh part,
# at cover (70 .. 230 from a cover box), 200 or more from the line and 150 from the other men (C:/kl_scratch/vault_gates/finder.py).
ROOM_GATES = False                      # '--gates': the delivered flag set has it
ROOM_ON = ('lobby', 'flights', 'hall')      # the rooms gated: the budget above. SECOND FIX: the dock is OFF (no place in its hall is out of the line of 6 .. 8 of its nine men: re/bank_campaign.md G2.1)
ROOM_HIDE = True                        # holds prefer places no man of the room sees (the task's 'out of the room's sight where the mesh allows'); False ('--gates-seen'): in sight at cover
ROOM_WAIT_S = 30.0                      # TriggerActorsDead's own limit (READ in kl2, 0x7800 ticks); kl_fa_bots_rt.WAIT_S
ROUND_CLOCK = 360.0                     # the round's six minutes, from the round-start event
ROOM_VAN_MARGIN = 60.0                  # s the van call must still come before the round's end (call -> everybody aboard: 12 s in W3; the van drives in 7.2 s and waits 8 s). GUESS
GO_EVENT = 8.5                          # s from the round-start event to the GO (GO_AFTER_EVENT)
NOAI_CALL = 164.1                       # s after the GO: the slowest 'heist stage 2 -> 3' of W3 (no enemies, no gates). MEASURED
ROOM_POST_CLEAR = 400.0                 # no hold and no station within this of a post (start place) of a man who may be alive, on his floor
ROOM_AFTER_CLEAR = 300.0                # ... of a man of an EARLIER room (he may have outlived his gate's 30 s): the planner's rule is the 400 above, this the least
ROOM_LINE_CLEAR = 160.0                 # no man's start within this of the crew's line (the point-blank reach 1.6 m, with margin: re/melee_damage.md)
ROOM_LINE_WANT = 165.0                  # a man that is moved is put at least this far from every bot's line and from the other way down from the dock (second fix: the dock hall leaves no 200: f7.py). GUESS: 5 over the point-blank reach
ROOM_HOLD_RING = (60.0, 240.0)          # a hold lies this far from the middle of a cover box (kl_fa_bots_rt.HOLD_RING 70 .. 230 with a tolerance for rounding)
ROOM_HOLD_SEP = 80.0                    # two holds of one room at least this far apart
ROOM_SIGHT = ('sight', 'ray', 'hero')   # the rules a hold is hidden under in the planner (fast); the check also casts the exact ray
ROOM_MESH_MIN = 1.0                     # every one of the 16 probes of the game's 'down' test (kl_pf4_probe) must reach a full 1.0 = 1 m of free mesh round a hold
HOLD_GUNS = 3                           # guns that may bear on a hold of the seven (kl_fa_club.HOLD_GUNS: Withdrawal's heist stations 0..3, exact ray, squads in the world). A target the planner is asked for
HOLD_GUNS_MAX = 5                       # ... and the least rooms_check FAILS at (the skeptic: 'do not ship a hold with 6 or more guns'); between the two it NOTES (HOLD_GUNS_KNOWN)
HOLD_GUN_RANGE = 4000.0                 # a gun bears within 40 m on its floor with a free exact ray (kl_fa_club uses 60 m; the dock/lobby/flights of this map are 10 .. 25 m long). GUESS
HOLD_GUN_DY = 120.0
HOLD_GUNS_KNOWN = {'lobby': 4}          # MEASURED (rooms_check, b/t3): 4 dock men with a free exact ray to five of the lobby's seven holds; the dock hall leaves no place out of the ramp's view for the rest. gate name -> guns on its worst hold that the delivered build has over HOLD_GUNS (rooms_check says them)
ROOM_ALT_VIA = ((-450.0, 240.0, -5000.0), (398.0, 213.0, -5885.0))      # the two ways from the dock floor to the lobby's upper floor: the west stair (W4's hits lie there) and the south ramp: the line check walks both
ROOM_NAME_SEEN = True                   # the TriggerActorsDead names the men a hold can see; where none is seen it names every man of the room (the clock is then the gate)
# the rooms, in the order of the way. name; leg ('in' / 'out'); what; box (x0, x1, z0, z1) and y of the hold places; the direction the men are in (plan); dy: floor tolerance.
# GUESS: every box and direction; MEASURED: the holds they give (rooms_check prints them) are on the START's mesh part, at cover boxes, 1 m inside the mesh, 4 m and more from every
# post of a living man.
ROOMS = (
    dict(name='dock', leg='in', what='the dock\'s north end, inside the roller door (the dock\'s seven guards at its south end, the two patrol men; the yard side was tried: every place there is in the line of 6 .. 7 of the nine through the door, the doorway itself of all)',
         box=(-200.0, 1100.0, -5300.0, -4750.0), y=200.0, enemy=(0.0, -1.0), dy=100.0),
    dict(name='lobby', leg='in', what='the west corridor\'s south end before the vault lobby (the lobby\'s four guards)',
         box=(-1000.0, 800.0, -6400.0, -5850.0), y=241.0, enemy=(0.0, -1.0), dy=60.0),
    dict(name='flights', leg='in', what='the vault lobby end before the glass door and the stairs down (the six guards of the flights and the ante-room come up to it)',
         box=(-100.0, 900.0, -7500.0, -7150.0), y=241.0, enemy=(0.0, -1.0), dy=60.0),
    dict(name='airlock', leg='out', what='the vault lobby, east of the glass door, before the airlock (the police of the beat)',
         box=(300.0, 1000.0, -7700.0, -7000.0), y=241.0, enemy=(1.0, 0.3), dy=60.0),
    dict(name='hall', leg='out', what='the banking hall\'s north end at the foyer door (the hall\'s eight on the gallery)',
         box=(-1100.0, 1500.0, -6500.0, -5900.0), y=802.0, enemy=(0.0, -1.0), dy=60.0),
    dict(name='front', leg='out', what='the banking hall\'s south end before the front entrance (the plaza\'s twenty)',
         box=(-900.0, 1300.0, -9350.0, -8650.0), y=802.0, enemy=(0.0, -1.0), dy=60.0))
# the men moved (finder.py on the delivered bare folder; key = the man's group path, value = the place). GUESS: the places; MEASURED: on the mesh, at cover, off the line
CLEAR_MEN = collections.OrderedDict([
    ('GamePlay!3_Garage_Part!PatrolGuards_01a\\Guard_01', (-968, 240, -4908)),     # second fix (f6.py): the stair top's patrol to the upper west level's pocket, 293 / 479 from every line (the first fix's places were 7 and 86 from a line once all seven bots and the west stair were walked)
    ('GamePlay!3_Garage_Part!PatrolGuards_01a\\Guard_01#01', (-1038, 240, -4726)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs#01\\Guard_01#03', (-334, 240, -7164)),     # second fix (f4.py): 20 exact-ray lines to the flights' holds and zone -> 1, 308 from every bot's line
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\Guard_01#02', (761, 200, -5375)),     # (-39, 203, -5775) was tried: within 400 of the lobby's holds
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\Guard_01#04', (384, 200, -5223)),      # second fix (f7.py): out of the ramp's line to the lobby's holds (8 lines -> 0), 166 from every line
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\Guard_01#01', (-334, 240, -5132)),     # the upper west level, out of the ramp's line (7 -> 0)
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\Guard_01#01', (325, 200, -5366)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\Guard_01#02', (-603, 240, -5584)),     # STAGING (pressure fix): was (497, 240, -6684), in sight of four of the seven places of the flights' hold and of the stretch below it, so his squad could not be woken by the flights gate; (-603, 240, -5584) is the upper west level by the stair top and sees no hold or stretch of the way in (C:/kl_scratch/vault_pressure/mv2.py: 52 candidates, the nearest with 0 rows seen), 181 from a cover box
    ('GamePlay!4_Vault_Part!Guards_02\\Guard_01', (602, -560, -10623)),
    ('GamePlay!4_Vault_Part!Guards_02\\Guard_01#01', (748, -560, -10548)),
    ('GamePlay!4_Vault_Part!Guards_03\\Guard_01', (100, -960, -12445)),         # the ante-room's two guards to its south-west pocket (x 100, z -12450 .. -12200, against the west wall; second fix: 200 and more from every bot's vault walk, the first form's x 225 was 162 from it): the vault gate's hold
    ('GamePlay!4_Vault_Part!Guards_03\\Guard_01#01', (100, -960, -12200)),      # (the mesh's north half, z >= -11900) is 400 from them, the crew's line (x 400) 175. Their defend place goes with them
    ('GamePlay!4_Vault_Part!Guards_03\\DefendBehaviour\\Pos#01', (100, -960, -12330)),
    ('GamePlay!4_Vault_Part!Guards_01\\Guard_01', (628, -160, -9365)),
    ('GamePlay!4_Vault_Part!Guards_01\\Guard_01#01', (632, -160, -9045))])
# men that stay within ROOM_LINE_CLEAR of a place the crew may walk, and why (rooms_check says them): none yet
ROOM_STAY = collections.OrderedDict()
# ---- STAGING (after run W6; '--staging', needs '--gates'; re/bank_campaign.md 'Pressure and staging'). The yardstick is the tab's Withdrawal (kl_fa_club's, MEASURED the same way): at most 3 guns with a clear
# exact ray on a station of the heist (HOLD_GUNS) and 4 on a stretch between two (LEG_GUNS), counting the men of the squads that are in the world at that moment. The way in of the delivered
# c_bank6 build was 6 / 4 / 2 on the stations and 6 / 6 / 5 on the stretches (the dock's garrison in the open from GO + 1.5 s, START 7 guns at GO + 11 s: run W4). So the squads of the way in SLEEP
# (ZSquadScript field 3 = 0: 'not in the world until one of its routs is named', the form every squad of this module has) and are woken as stock wakes a parked squad, by NAMING THE SQUAD'S START
# ROUT: from the list of the gate before (TriggerActorsDead field 2, in all seven bots' copies), from a criminals-only box on the way into the room, and from a backstop timer. The three go through ONE relay
# per event (Wake_<event>, a TriggerDelay2 whose list is the routs; the proven form of the waves' Pace / Go links). WAKE_SQUADS was chosen by a search (C:/kl_scratch/vault_pressure/plan5.py: for every
# squad the latest event before any of its men can see the crew, at which none of its men sees the criminals who wake him - the box's floor on a 3 m lattice, the holds of the gate that wakes him - and
# the counts on the stations and stretches of the way in stay within the yardstick; a squad wakes as a whole, so its latest man decides). MEASURED: START rows 0 guns at GO / + 11 / + 30 / + 60 s (was 7);
# the way in 0 / 0 / 2 / 2 on the stations, 0 / 3 / 5 / 2 on the stretches (the flights' 5 = the four men of wave A on the landing + one of Guards_01: WAKE_KNOWN).
STAGING = False
WAKE_DELAY = 0.3                        # s the relay Wake_<event> waits before it names the routs (the relay is named by up to nine sources, TriggerDelay2 form of Pace_ / Go_). GUESS
# event -> dict(gate = the gate whose TriggerActorsDead list names the relay (None: no gate before it: the dock gate is off), box = (place, half extents) of the criminals-only box (None: the beat box, which exists),
# go = the backstop, seconds after the GO: the slowest crew of W3 / W4 reached the room at about GO + 35 / + 75 / + 130 s (GUESS: the backstop is a minute past that)
WAKE_EVENTS = collections.OrderedDict([
    ('lobby', dict(gate=None, box=((-100.0, 241.0, -6125.0), (900.0, 80.0, 275.0)), go=70.0, what='the west corridor\'s south end (ROOMS lobby\'s box)')),
    ('flights', dict(gate='lobby', box=((400.0, 241.0, -7325.0), (500.0, 80.0, 175.0)), go=100.0, what='the vault lobby end before the glass door (ROOMS flights\' box)')),
    ('ante', dict(gate=None, box=None, go=180.0, what='the ante-room box (the beat box)'))])      # SECOND FIX (skeptic): no gate - the flights gate would wake the 12 men while the crew still stands on the flights holds
WAKE_SQUADS = collections.OrderedDict([
    (G4 + 'Guards_Reinforcement_StayUpstairs#01', 'lobby'),
    (G4 + 'Guards_03', 'flights'),
    (G4 + 'Guards_Reinforcement_StayUpstairs', 'ante'), (G4 + 'Guards_Reinforcement_01b', 'ante'), (G4 + 'Guards_Reinforcement_01a', 'ante'),
    (G4 + 'Guards_02', 'ante'), (G4 + 'Guards_01', 'ante'),
    (G3 + 'PatrolGuards_01a', 'ante')])             # AFTER RUNS W7 / W8: the dock patrol was the one squad awake from GO + 1.5 s (hunters: see HUNT_REACH); it sleeps with the garrison
EVENT_T = {'lobby': 0.9, 'flights': 1.0, 'ante': 2.9}          # the earliest time index (station j = j, a stretch j -> j + 1 = j .. j + 1) at which the event can fire: the gate fires with the crew at its hold
LEG_GUNS = 4                            # guns that may bear on a stretch between two stations (kl_fa_club.LEG_GUNS: Withdrawal's heist legs, exact ray, squads in the world)
WAKE_KNOWN = {('leg', 2): (5, "the flights landing on the way down: wave A's four posts (wave_plan: 400 from every station) and one of Guards_01's two men; Guards_01 cannot be moved out of the leg's line "
                              "(C:/kl_scratch/vault_pressure/mv.py: 8 -> 6 rows seen at best); what it needs: wave A's four posts off the landing"),
              ('leg', 5): (5, 'the same landing on the way back'), ('leg', 6): (6, "the vault lobby on the way out: wave B's three posts and the lobby squad's men taken ALIVE (they are the lobby gate's men)"),
              ('hold', 7): (4, 'the airlock station: the same men'), ('leg', 11): (9, "the square: wave D (the owner's shootout on the square)"),
              ('hold', 12): (9, 'the square'), ('hold', 13): (36, 'the square'), ('hold', 14): (36, 'the square'), ('leg', 12): (36, 'the square'), ('leg', 13): (36, 'the square')}
# ---- HUNTERS (after runs W7 / W8, 2026-10-12). The first pressure table counted a man where he STANDS (and, from the second fix, at the Defend places he walks to). Runs W7 / W8 on c_bank7: the idle human at the
# START row was shot from GO + 16 s (W8: 'you lost 63.2' then 57.9 .. 64.0 every 0.06 s = one rifle, police -> you 1.0) and dead at GO + 99 s (W7); the table said 0 guns on the START rows at GO / 11 / 30 / 60 s.
# The only squad of the way in that was NOT staged is the dock patrol (PatrolGuards_01a, 2 men, named by the start timer = in the world from GO + 1.5 s); its modifier is eALM_Alert, the dock garrison's and
# the hunts' are eLM_Unleash. A man of such a squad does not stay at his place: he goes for what he sees, and the dock floor sees the START (a bot hit on the dock floor at (436, 200, -5240) in W8: START is
# in the exact ray's view from there, and the patrol's own Defend place (-496, 241, -5083) is 10 m from that floor). So a HUNTER counts at his place AND at every point of his mesh path towards the target
# up to HUNT_REACH (the nearest place he can reach: the path's first HUNT_REACH cm). HUNT_REACH is a GUESS (25 m; the game's leash length is not read); the evidence is W7 / W8 only.
HUNT_REACH = 2500.0
HUNT_STEP = 250.0
HUNT_ENUMS = (0, 'eLM_Unleash'), (6, 'eALM_Alert')        # SquadModifierBehaviour fields 0 (leash mode) and 6 (alert level): a squad with one of them is a hunter
_HUNT_CACHE = {}


def hunter_squads(sc):
    """The squads (names under ROOT\\) whose SquadModifierBehaviour sets eLM_Unleash or eALM_Alert -> set."""
    out = set()
    for k, _i, v in kl_fa.controllers(sc, 'SquadModifierBehaviour'):
        if any(len(v) > f and v[f] == e for f, e in HUNT_ENUMS):
            out.add(sc.path[sc.top[k]][len(R):])
    return out


def hunt_points(nav, o, p):
    """The points a hunter who stands at o can walk to on the way to p within HUNT_REACH (the stand-in mesh path, one point per HUNT_STEP) -> [(x, y, z)], o first; [] without a path."""
    import kl_fa_bots_rt as RT
    key = (id(nav), tuple(round(c) for c in o[:3]), tuple(round(c / 50.0) for c in p[:3]))
    if key not in _HUNT_CACHE:
        try:
            got = RT.way_samples(nav, tuple(o[:3]), tuple(p[:3]), HUNT_STEP)
        except Exception:
            got = None
        pts, run = [], 0.0
        for q in (got[0] if got else ()):                # (the path's corners come twice; the length run is the sum of the legs)
            q = tuple(q[:3])
            if pts:
                run += math.dist(pts[-1], q)
            if run > HUNT_REACH:
                break
            if not pts or q != pts[-1]:
                pts.append(q)
        _HUNT_CACHE[key] = pts
    return _HUNT_CACHE[key]


def man_bears(S, nav, m, p, rng, rules=('exact',), dy=HOLD_GUN_DY):
    """Does man m (a stage_men entry: 'at', and 'hunter' for the squads of hunter_squads) have a clear ray to the place p from where he stands or, a hunter, from a point of his way towards it?"""
    cand = [tuple(m['at'][:3])]
    if m.get('hunter') and nav is not None and math.dist(m['at'], p) <= rng + HUNT_REACH:
        cand += hunt_points(nav, m['at'], p)
    for q in cand:
        if (dy is None or abs(q[1] - p[1]) < dy) and math.dist(q, p) <= rng and S.sees_by(q, tuple(p[:3]), rules):
            return True
    return False


# ---- THE GARRISON (after runs W10 / W11 / W12, 2026-10-12; '--garrison', needs '--gates'; re/bank_campaign.md 'After runs W10-W12'). W12 (c_bank8, idle human, [CrewHop] Dry): four of seven bots
# dead - 'lost 237 / 136 / 138 ... ONE STEP' in the vault lobby at GO + 67 / + 141 / + 193 s, one at the banking hall's gallery GO + 233 s - and the idle human at the START shot for 140 s from GO + 100 s. READ in the built
# folder: the campaign's guards DEFEND PLACES lie on the crew's own way (the vault lobby (398, 243, -7469) / (395, 242, -7523) / (398, 242, -7554) / (400, 243, -7903): 5 .. 37 from a leg of the way in AND out, shared
# by FIVE squads; the flights (407, -158, -9308) .. (410, -158, -9540): 7 .. 25), the dock garrison, the patrol and the beat's police are 'eLM_Unleash' / 'eALM_Alert' hunters and the beat's end names the campaign's
# hunt (49_SquadMod -> 50_HuntBehaviour, search box IN the vault) for five of them: a man who WALKS the crew's line is inside the point-blank reach (160) of it, whatever the table of standing guns says.
# So: (1) every man of the way in / down / the beat is put with every place of his squad's routs into a POCKET off the crew's line (GARRISON_PLACES: the dock's upper west level for 11 squads, the lobby's east corner for the lobby's three, one side
# room of the flights for Guards_01 and Police_Reinforcement_02; each point MEASURED on the built level: on the mesh, >= 350 from every leg and 450 from every hold of the seven bots, a wall >= 20 away, an exact ray to no START row and - the squads that come in with the ante-room's event - to no station of the way in, within 400 of a cover box);
# (2) the squads KEEP their places: ZSquadScript attitude eStayBack, every SquadModifierBehaviour eLM_Unleash -> eLM_Leash (soldier+0x6fc: 'unleashed = no longer tied to the defend position', kl2 0x85f89f) and
# eALM_Alert -> eALM_NotSet; the campaign's hunt is NOT named at the beat's end. The way-out pressure then comes from the lobby's three, the hall's eight, the plaza and the waves (chain B, D).
GARRISON = False
GARRISON_PLACES = collections.OrderedDict([
    # Guards_Reinforcement_StayUpstairs#01: 3 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs#01\\Guard_01#03', (-450, 240, -7200)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs#01\\Guard_01#01', (-450, 240, -7300)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs#01\\Guard_01#02', (-450, 240, -7100)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs#01\\10_DefendBehaviour\\Pos#01', (-450, 240, -7200)),
    # PatrolGuards_01a: 2 men, pocket of 2 points
    ('GamePlay!3_Garage_Part!PatrolGuards_01a\\Guard_01', (-400, 200, -3400)),
    ('GamePlay!3_Garage_Part!PatrolGuards_01a\\Guard_01#01', (-300, 200, -3700)),
    ('GamePlay!3_Garage_Part!PatrolGuards_01a\\10_DefendBehaviour\\Pos#01', (-400, 200, -3400)),
    ('GamePlay!3_Garage_Part!PatrolGuards_01a\\30_DefendBehaviour\\Pos#01', (-400, 200, -3400)),
    # Guards_Reinforcement_StayUpstairs: 4 men, pocket of 4 points
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\Guard_01#04', (-950, 240, -4850)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\Guard_01#03', (-1050, 240, -4800)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\Guard_01#01', (-900, 240, -4800)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\Guard_01#02', (-950, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\10_DefendBehaviour\\Pos#02', (-950, 240, -4850)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_StayUpstairs\\10_DefendBehaviour\\Pos#01', (-1050, 240, -4800)),
    # Guards_Reinforcement_01b: 2 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\Guard_01#01', (-450, 240, -7400)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\Guard_01#02', (-450, 240, -7000)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\40_DefendBehaviour_Moveback\\Pos#01', (-450, 240, -7400)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\40_DefendBehaviour_Moveback\\Pos#03', (-450, 240, -7000)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\40_DefendBehaviour_Moveback\\Pos#02', (-450, 240, -7400)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\10_DefendBehaviour\\Pos#02', (-450, 240, -7400)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01b\\10_DefendBehaviour\\Pos#01', (-450, 240, -7000)),
    # Guards_Reinforcement_01a: 2 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\Guard_01#01', (-900, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\Guard_01#02', (-950, 240, -4800)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\40_DefendBehaviour_Moveback\\Pos#01', (-900, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\40_DefendBehaviour_Moveback\\Pos#03', (-950, 240, -4800)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\40_DefendBehaviour_Moveback\\Pos#02', (-1050, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\10_DefendBehaviour\\Pos#02', (-900, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_Reinforcement_01a\\10_DefendBehaviour\\Pos#01', (-950, 240, -4800)),
    # Guards_01: 2 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Guards_01\\Guard_01', (-1000, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_01\\Guard_01#01', (-1050, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_01\\20_DefendBehaviour\\Pos#02', (-1000, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_01\\20_DefendBehaviour\\Pos#01', (-1050, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_01\\10_DefendBehaviour\\Pos#03', (-1000, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_01\\10_DefendBehaviour\\Pos#02', (-1050, 240, -4750)),
    ('GamePlay!4_Vault_Part!Guards_01\\10_DefendBehaviour\\Pos#01', (-1000, 240, -4800)),
    # Police_Reinforcement_02: 2 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Police_Reinforcement_02\\Police_01', (750, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_02\\Police_02', (800, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_02\\40_DefendBehaviour_Moveback\\Pos#01', (750, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_02\\40_DefendBehaviour_Moveback\\Pos#03', (800, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_02\\40_DefendBehaviour_Moveback\\Pos#02', (750, -160, -8950)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_02\\10_DefendBehaviour\\Pos#01', (750, -160, -8900)),
    # Police_Reinforcement_03: 4 men, pocket of 4 points
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\Police_01', (800, -160, -9000)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\Police_02', (750, -160, -8950)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\Police_04', (900, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\Police_03', (750, -160, -9000)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\40_DefendBehaviour_Moveback\\Pos#01', (800, -160, -9000)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\40_DefendBehaviour_Moveback\\Pos#03', (750, -160, -8950)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\40_DefendBehaviour_Moveback\\Pos#02', (900, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\10_DefendBehaviour\\Pos#02', (800, -160, -9000)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_03\\10_DefendBehaviour\\Pos#01', (750, -160, -8950)),
    # Guards_02: 2 men, pocket of 2 points
    ('GamePlay!4_Vault_Part!Guards_02\\Guard_01', (-1000, 240, -4800)),
    ('GamePlay!4_Vault_Part!Guards_02\\Guard_01#01', (-1000, 240, -4700)),
    ('GamePlay!4_Vault_Part!Guards_02\\DefendBehaviour\\Pos#02', (-1000, 240, -4800)),
    ('GamePlay!4_Vault_Part!Guards_02\\DefendBehaviour\\Pos#01', (-1000, 240, -4700)),
    # Police_Reinforcement_Teargas_01: 1 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01\\Police_01', (900, -160, -9300)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01\\40_DefendBehaviour_Moveback\\Pos#01', (900, -160, -9300)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01\\40_DefendBehaviour_Moveback\\Pos#03', (850, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01\\40_DefendBehaviour_Moveback\\Pos#02', (900, -160, -9100)),
    # Police_Reinforcement_Teargas_01#01: 1 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01#01\\Police_01', (850, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01#01\\20_DefendBehaviour\\Pos#03', (850, -160, -8900)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01#01\\20_DefendBehaviour\\Pos#02', (900, -160, -9100)),
    ('GamePlay!4_Vault_Part!Police_Reinforcement_Teargas_01#01\\20_DefendBehaviour\\Pos#01', (900, -160, -8950)),
    # Vault_Reinforcement_Police_01: 2 men, pocket of 2 points
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_01\\Police_01', (850, -160, -8950)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_01\\Police_02', (900, -160, -8950)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_01\\20_DefendBehaviour\\Pos#01', (850, -160, -8950)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_01\\20_DefendBehaviour\\Pos#02', (900, -160, -8950)),
    # Vault_Reinforcement_Police_02: 2 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_02\\Police_01', (900, -160, -9100)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_02\\Police_02', (900, -160, -9050)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_02\\10_DefendBehaviour\\Pos#03', (900, -160, -9100)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_02\\10_DefendBehaviour\\Pos#02', (900, -160, -9050)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_02\\10_DefendBehaviour\\Pos#01', (900, -160, -9000)),
    # Vault_Reinforcement_Police_03: 2 men, pocket of 3 points
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_03\\Police_01', (900, -560, -10700)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_03\\Police_02', (900, -560, -10600)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_03\\20_DefendBehaviour\\Pos#03', (900, -560, -10700)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_03\\20_DefendBehaviour\\Pos#02', (900, -560, -10600)),
    ('GamePlay!4_Vault_Part!Vault_Reinforcement_Police_03\\20_DefendBehaviour\\Pos#01', (900, -560, -10500)),
])
GARRISON_HOLD, GARRISON_LEG = 400.0, 300.0     # outside the vault lobby (the first form; inside it GARRISON_OPEN). GUESS: the task's numbers
# SECOND FIX (skeptic of the first garrison build). (1) The stand-in legs are NOT where a real bot walks: W12's bot 4 died at (450, 336, -6714), 313 from the nearest stand-in leg of its own plan (MEASURED on c_bank9: w2/r1.py), the
# flights' StayUpstairs row of the first build stood 109 from that place. So a garrison place keeps the point-blank reach (ROOM_LINE_CLEAR) plus that measured deviation from every leg and every hold, and the five places
# where a real bot was shot in W12 are holds of their own (OBSERVED_PLACES; the three ONE STEP deaths and the two gallery spots of bot 6). (2) The way out is not made worse: WAY_OUT_BASE_AT = c_bank8's guns on the way-out
# stations / stretches (MEASURED, pressure-check), a --garrison build FAILS above them.
OBSERVED_DEV = 313.0                    # MEASURED: the largest distance of a real death from the stand-in legs (W12 bot 4); a pocket also keeps ROOM_LINE_CLEAR from the place of a real walk
OBSERVED_PLACES = (('W12 bot 4 ONE STEP (way in)', (450.0, 336.0, -6714.0)), ('W12 bot 1 ONE STEP (way out)', (433.0, 249.0, -8211.0)),
                   ('W12 bot 7 ONE STEP (way out)', (340.0, 335.0, -7660.0)), ('W12 bot 6 stairwell', (1520.0, 1144.0, -5780.0)), ('W12 bot 6 gallery', (1284.0, 1220.0, -6488.0)))
OBSERVED_STRAY = ('W12 bot 6 stairwell', 'W12 bot 6 gallery')          # the two spots of bot 6 up the stairwell: said in (e), not a rule (the hall's gallery police are the owner's design and the climb is not explained)
# c_bank8's way-out stations as pressure-check printed them (MEASURED, run W12's build): place -> (guns on a hold, guns on the stretch to the next station). The plan's station list is built from the squads' places
# (the rooms' holds), so the check matches by PLACE, not by index: a station within 150 of one of these takes its numbers; a station between two lies on the earlier one's stretch and takes that stretch's worst for both.
WAY_OUT_BASE_AT = (((405.0, -774.0, -11228.0), 3, 13), ((394.0, 240.0, -7876.0), 11, 15), ((1546.0, 240.0, -6970.0), 9, 9))


def way_out_base(rows):
    """{('hold'|'leg', i): c_bank8's guns} for the way-out rows of pressure_rows that WAY_OUT_BASE_AT covers (the stations from the first of its places on, up to the hall)."""
    out, last = {}, None
    for r in rows:
        hit = [b for b in WAY_OUT_BASE_AT if math.dist(b[0], r['at']) < 150.0]
        if hit:
            last = hit[0]
            out[('hold', r['i'])], out[('leg', r['i'])] = last[1], last[2]
        elif last is not None and r['kind'] == 'way' and r['at'][1] < 300.0 and r['at'][2] > -11500.0:       # a station inserted between two of them, on the stairs / corridors below the lobby
            out[('hold', r['i'])], out[('leg', r['i'])] = last[2], last[2]        # a point of the old stretch: the old stretch's worst (c_bank8 had no station there)
    return out
GARRISON_OPEN = 425.0                   # in the vault lobby (in_lobby) a garrison place keeps this from every hold and leg sample and from the places W12 shot bots. The reach is 160 and the deviation of a real walk from the stand-in leg was
                                        # MEASURED once at 313 (W12 bot 4, the lobby's EAST half): 473 would leave the lobby's three no place on the mesh; the only quiet strip is the west wall (x -450, 431 .. 445 from the diagonal leg 1>2)
                                        # and 425 is what it allows. KNOWN RISK, GUESS: that a walk does not wander 265+ to the west of that leg. Outside the lobby the first form's GARRISON_HOLD / GARRISON_LEG stay (no deviation was measured there)
LOBBY_BOX = (-8400.0, -5900.0, 90.0, 390.0)       # z from, z to, y from, y to: the vault lobby's floor and its stairs


def in_lobby(p):
    return LOBBY_BOX[0] <= p[2] <= LOBBY_BOX[1] and LOBBY_BOX[2] <= p[1] <= LOBBY_BOX[3]
WAKE_EARLIEST = {'lobby': 30.0, 'flights': 45.0, 'ante': 75.0}    # s after the GO: the earliest a gate's event can fire with the fastest crew seen (the beat box: GO + 70 .. 85 s in W10 - W12 from the idle human's first hit at +91 / +134 / +100 s less the garrison's walk). GUESS
YARD_GUNS = 3                           # guns that may bear on a START row at any time (the fed respawn and late bots stand there; HOLD_GUNS)
YARD_TIMES = (0.0, 11.0, 30.0, 60.0, 75.0, 90.0, 120.0, 180.0, 240.0, 300.0, 360.0)
GARRISON_SCOPE = ('start', 'down', 'beat', 'hall')      # the stages whose men and places the hard rule counts (the plaza's twenty are the shootout on the square; their places lie beside the van's lane by design)
STAGE2_NOTE = ('heist stage 2 comes only at the front exit (ExitLootArea at the hall\'s south end): a bot that loots the vault and the hall stays at heist stage 1 until then - normal here '
               '(W12: $755,000 .. $1,185,000 at stage 1)')


def garrison_squads():
    """The squads (names under ROOT\\) that GARRISON_PLACES moves: they hold the stricter rule (GARRISON_HOLD / GARRISON_LEG)."""
    return {rel.split('\\')[0] for rel in GARRISON_PLACES}


def garrison_men(M, keep, log=print):
    """GARRISON, on the converted level M in strip(), after clear_men: every man and every rout place of GARRISON_PLACES to its pocket (man_to checks that each stands on the navigation mesh). -> [(path, from, to)]"""
    import kl_route
    if not GARRISON or not keep:
        return []
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
    moved = []
    for rel, new in GARRISON_PLACES.items():
        hit = sc.resolve(R + rel)
        if len(hit) != 1 or sc.cls(hit[0]) not in ('ZGROUP', 'ZBoxPrimitive') or sc.names[sc.top[hit[0]]] not in keep:
            raise ValueError('kl_fa_bank: GARRISON_PLACES names %s: %d nodes (a ZGROUP or a place of a kept squad wanted)' % (rel, len(hit)))
        was = world_of(M.ents[hit[0] - 1])[0]
        man_to(M, hit[0], tuple(float(v) for v in new), mesh)
        moved.append((rel, was, new))
    log('  kl_fa_bank: GARRISON: %d men and %d rout places of %d squads put into pockets off the crew\'s line: %s' % (
        sum('\\Guard_01' in r.split('\\', 1)[1] and 'Defend' not in r for r, _w, _t in moved), sum('Defend' in r for r, _w, _t in moved), len(garrison_squads()),
        ', '.join('%s %d' % (r.split('!')[-1].split('\\')[0], math.dist(w, t)) for r, w, t in moved[::6])))
    return moved


def garrison_modes(sc, plan, log=print):
    """GARRISON, in wire() on the joined scene: the squads of the way in / down / the beat KEEP their places - ZSquadScript attitude eStayBack, SquadModifierBehaviour eLM_Unleash -> eLM_Leash and eALM_Alert -> eALM_NotSet
    (the leash: soldier+0x6fc, kl2 0x85f89f). -> dict of counts"""
    scope = {n for n in plan if STAGE.get(n) in ('start', 'down', 'beat')}
    n_att = n_unl = n_alert = 0
    for n in sorted(scope):
        k = A.node_of(sc, n)
        if values(sc, k, 'ZSquadScript')[0] != 'eStayBack':
            kl_fa.edit(sc, k, A.ctrl_of(sc, k, 'ZSquadScript'), lambda us: A.setv(sc, us, 0, 'eStayBack'))
            n_att += 1
    for k, i, v in kl_fa.controllers(sc, 'SquadModifierBehaviour'):
        if sc.path[sc.top[k]][len(R):] not in scope:
            continue
        ch = {}
        if v[0] == 'eLM_Unleash':
            ch[0] = 'eLM_Leash'; n_unl += 1
        if v[6] == 'eALM_Alert':
            ch[6] = 'eALM_NotSet'; n_alert += 1
        if ch:
            kl_fa.edit(sc, k, i, lambda us, ch=ch: [A.setv(sc, us, f, val) for f, val in ch.items()])
    log('  kl_fa_bank: GARRISON modes: %d squads; attitude eStayBack on %d, eLM_Unleash -> eLM_Leash on %d modifiers, eALM_Alert -> eALM_NotSet on %d; the campaign\'s hunt is not named' % (len(scope), n_att, n_unl, n_alert))
    return dict(squads=len(scope), attitude=n_att, unleash=n_unl, alert=n_alert)


def crew_ways(B, P, nav, step=50.0):
    """The ways of the crew: ([(label, [points of one leg])], [(label, station place)]). A leg is the stand-in mesh path of one bot from one of its places to the next, sampled every `step`; the human's route
    (ROUTE_IN, ROUTE_VAULT, ROUTE_OUT) is walked the same way. The stations are the seven bots' places, one per station of the plan."""
    import kl_fa_bots_rt as RT
    legs, holds = [], []
    for n, b in P['bots'].items():
        pl = [tuple(q[:3]) for q in b['places']]
        holds += [('bot %s station %d' % (n, j), q) for j, q in enumerate(pl)]
        for j, (a, c) in enumerate(zip(pl, pl[1:])):
            got = RT.way_samples(nav, a, c, step)
            legs.append(('bot %s leg %d>%d' % (n, j, j + 1), [tuple(q[:3]) for q in got[0]] if got else [a, c]))
    hum = [(nm, tuple(q)) for nm, q in ROUTE_IN + ROUTE_VAULT + ROUTE_OUT]
    for (na, a), (nb, c) in zip(hum, hum[1:]):
        got = RT.way_samples(nav, a, c, step)
        legs.append(('human %s>%s' % (na, nb), [tuple(q[:3]) for q in got[0]] if got else [a, c]))
    for n, b in P['bots'].items():              # the other ways down from the dock floor to the lobby's upper floor (ROOM_ALT_VIA, rooms_check's line): a -> via -> b for each via
        pl = [tuple(q[:3]) for q in b['places']]
        for j, (a_, c_) in enumerate(zip(pl, pl[1:])):
            if a_[1] < 225.0 <= c_[1] and c_[2] < -5900.0:
                for vi, v in enumerate(ROOM_ALT_VIA):
                    h = nav.at(v[0], v[1], v[2], dy=200.0)
                    if not h:
                        continue
                    s1, s2 = RT.way_samples(nav, a_, (v[0], h[1], v[2]), step), RT.way_samples(nav, (v[0], h[1], v[2]), c_, step)
                    if s1 and s2:
                        legs.append(('bot %s alt way %d via %d' % (n, j, vi), [tuple(q[:3]) for q in s1[0] + s2[0]]))
    return legs, holds


def hunted_squads(sc):
    """The squads whose campaign hunt (49_SquadMod, 50_HuntBehaviour) is named by something outside the squad -> set of squad names (under ROOT\\)."""
    tops = {sc.path[t][len(R):]: t for t in sc.tops()}
    out = set()
    for j in range(1, len(sc.nodes)):
        for s in A.named(sc, j):
            if s.endswith('\\' + HUNT) or s.endswith('\\50_HuntBehaviour'):
                sq = s[len(R):].rsplit('\\', 1)[0]
                if sq in tops and sc.top[j] != tops[sq]:
                    out.add(sq)
    return out


def garrison_rows(B, hunted):
    """Every man's start and every place of a rout of the squads in GARRISON_SCOPE -> [dict(squad, stage, kind, what, at)]. A hunt rout's search box counts only for a squad whose hunt is named (`hunted`)."""
    sc, rows = B.sc, []
    for t in sc.tops():
        st = squad_stage(sc, t)
        if st not in GARRISON_SCOPE:
            continue
        nm = sc.path[t][len(R):]
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor':
                rows.append(dict(squad=nm, stage=st, kind='man', what=sc.path[sc.parent[k]].split('\\')[-1], at=B.at(k)))
        for j in rout_places(sc, t):
            rout = sc.path[sc.parent[j]].split('\\')[-1]
            if rout.endswith('HuntBehaviour') and nm not in hunted:
                continue
            rows.append(dict(squad=nm, stage=st, kind='place', what=rout + ' ' + sc.path[j].split('\\')[-1], at=B.at(j)))
    return rows


def garrison_check(folder, log=print):
    """'kl_fa_bank.py garrison-check <folder>': THE HARD RULES after runs W10 - W12, on any folder of the bank (the flags are read from bank_opts.json; a build without --garrison is MEASURED, not exempt):
    (b) no man's start, no place of any rout and no hunt path of the squads of the way in, down, the beat and the hall within ROOM_LINE_CLEAR (160, the point-blank reach 1.6 m with margin) of a hold (a station of
        any of the seven bots) or a leg of the crew's way, in or out - the squad's men stand or walk there at some time (every squad can be awake); the plaza's twenty are the square's shootout and are left out;
    (a) the garrison and the beat (GARRISON_PLACES' squads, the lobby's three among them) keep GARRISON_HOLD from every hold and GARRISON_LEG from every leg, have no exact ray to a START row, keep their places
        (no eLM_Unleash / eALM_Alert modifier, attitude eStayBack) and have no hunt named; the lobby's three are out of reach of the lobby gate's holds (d);
    (c) the START rows over the WHOLE round: no gun of an old squad at any time of YARD_TIMES (the squads of the ante-room's event from WAKE_EARLIEST on, hunters counted), and never more than YARD_GUNS of all men;
    (e) no leg or hold of the crew goes up to the hall's gallery (y > HALL_Y + 300), where the eight gallery police stand;
    (g) a squad that comes into the world later has no exact ray from its men and places to the stations the crew passes before his event.
    -> list of faults"""
    import json
    import kl_fa_bots as F
    bad = []

    def fail(s):
        bad.append(s)
        log('  FAIL ' + s)
    o = read_opts(folder)
    P = json.load(open(os.path.join(folder, 'bots.json'), encoding='utf-8')).get('plan') or {}
    if not P.get('stations'):
        log('  garrison: bots.json has no plan: not checked')
        return bad
    B = F.Built(folder)
    sc = B.sc
    nav = F.Nav(B.scene.nav)
    S = Sight(folder, B, lambda *a: None)
    pj = os.path.join(folder, 'extras.json')
    ex = json.load(open(pj)) if os.path.isfile(pj) else None
    set_wake_built(ex)
    log('  garrison: %s' % STAGE2_NOTE)
    legs, holds = crew_ways(B, P, nav)
    obs = [(lab, q) for lab, q in OBSERVED_PLACES if lab not in OBSERVED_STRAY]
    holds = holds + obs                                              # SECOND FIX: where a real bot was shot on its planned way in W12 is a place of the crew's own
    flat = [(lab, q) for lab, ss in legs for q in ss] + obs
    hunted = hunted_squads(sc)
    rows = garrison_rows(B, hunted)
    strict = garrison_squads()
    three = G4 + 'Guards_Reinforcement_StayUpstairs#01'
    lobby_holds = [q for lab, q in holds if lab.endswith('station 1')]

    def nearest(p):
        dl, ll = min(((math.dist(p, q), lab) for lab, q in flat), default=(1e9, '-'))
        dh, lh = min(((math.dist(p, q), lab) for lab, q in holds), default=(1e9, '-'))
        return dl, ll, dh, lh
    worst = collections.defaultdict(lambda: (1e9, None))
    near, sever = [], []
    for r in rows:
        dl, ll, dh, lh = nearest(r['at'])
        r['dleg'], r['dhold'] = dl, dh
        d = min(dl, dh)
        key = (r['squad'].split('!')[-1], r['stage'])
        if d < worst[key][0]:
            worst[key] = (d, '%s %s at (%d, %d, %d): %d from %s' % (r['kind'], r['what'], *r['at'], d, ll if dl <= dh else lh))
        if d < ROOM_LINE_CLEAR:
            near.append((d, r, ll if dl <= dh else lh))
        lob_ = in_lobby(r['at'])
        wh_, wl_ = (GARRISON_OPEN, GARRISON_OPEN) if lob_ else (GARRISON_HOLD, GARRISON_LEG)        # SECOND FIX: the vault lobby is where a real walk was MEASURED to leave the stand-in leg (313)
        if r['squad'] in strict and (dh < wh_ or dl < wl_):
            sever.append((min(dh - wh_, dl - wl_), r, ll if dl <= dh else lh))
    log('  garrison: %d places (%d men, %d rout places) of %d squads; hunts named: %d squads %s' % (
        len(rows), sum(r['kind'] == 'man' for r in rows), sum(r['kind'] == 'place' for r in rows), len({r['squad'] for r in rows}), len(hunted), sorted(h.split('!')[-1] for h in hunted)[:6]))
    near.sort(key=lambda t: t[0])
    for d, r, lab in near:
        who = r['squad'].split('!')[-1]
        log('    within %3d of %s: %s (%s) %s %s at (%d, %d, %d)' % (d, lab, who, r['stage'], r['kind'], r['what'], *r['at']))
    if near:
        fail('(b) %d places of %d squads lie within %d of a hold or a leg of the crew (nearest %d: %s %s)' % (
            len(near), len({r['squad'] for _d, r, _l in near}), ROOM_LINE_CLEAR, near[0][0], near[0][1]['squad'].split('!')[-1], near[0][1]['what']))
    if sever:
        sever.sort(key=lambda t: t[0])
        for d_, r_, lab_ in sever[:40]:
            log('    (a) %s %s %s at (%d, %d, %d): %d from %s' % (r_['squad'].split('!')[-1], r_['kind'], r_['what'], *r_['at'], min(r_['dhold'], r_['dleg']), lab_))
        fail('(a) %d places of the garrison / beat squads are nearer than %d (in the vault lobby; %d to a hold and %d to a leg elsewhere) to a hold or a leg (worst: %s %s at (%d, %d, %d), %d from %s)' % (
            len(sever), GARRISON_OPEN, GARRISON_HOLD, GARRISON_LEG, sever[0][1]['squad'].split('!')[-1], sever[0][1]['what'], *sever[0][1]['at'], min(sever[0][1]['dhold'], sever[0][1]['dleg']), sever[0][2]))
    lt = [r for r in rows if r['squad'] == three]
    if lt:
        dd = min(math.dist(r['at'], q) for r in lt for q in lobby_holds)
        log('  garrison (d): the lobby gate\'s %d holds are %d from the nearest of the lobby\'s three (their %d places); wanted >= %d' % (len(lobby_holds), dd, len(lt), GARRISON_HOLD))
        if dd < GARRISON_HOLD:
            fail('(d) the lobby gate\'s holds are %d from the lobby\'s three (%d wanted)' % (dd, GARRISON_HOLD))
    # modes: nobody who hunts
    hunters = hunter_squads(sc)
    sq = {r['squad'] for r in rows if r['stage'] in ('start', 'down', 'beat')}
    att = [n for n in sq if values(sc, A.node_of(sc, n), 'ZSquadScript')[0] != 'eStayBack']
    bad_modes = sorted((hunters & sq) | set(att))
    log('  garrison: %d squads of the way in / down / the beat; %d hunt (Unleash / Alert / attitude): %s' % (len(sq), len(bad_modes), ', '.join(n.split('!')[-1] for n in bad_modes)[:200]))
    if bad_modes:
        fail('(b) %d squads hunt (eLM_Unleash / eALM_Alert / attitude eUnleashed), so their men walk the crew\'s line: %s' % (len(bad_modes), ', '.join(n.split('!')[-1] for n in bad_modes)[:160]))
    if hunted:
        fail('(b) the campaign\'s hunt is named for %d squads (the search box is in the vault: a hunt path IS the crew\'s line): %s' % (len(hunted), ', '.join(sorted(h.split('!')[-1] for h in hunted))[:160]))
    # (e) the gallery
    ymax = max([q[1] for _l, ss in legs for q in ss] + [q[1] for _l, q in holds if not _l.startswith('W12')])
    gal = [r for r in rows if r['stage'] == 'hall' and r['at'][1] > 1100 and r['kind'] == 'man']
    log('  garrison (e): the highest point of any leg or hold of the crew is y %d (the hall floor %d, the gallery %d with %d of the hall\'s police)' % (ymax, HALL_Y, GAL_Y, len(gal)))
    for lab_, q_ in OBSERVED_PLACES:
        if lab_ in OBSERVED_STRAY:
            near_ = min(((math.dist(q_, r['at']), r['squad'].split('!')[-1], r['what']) for r in rows if r['stage'] == 'hall'), default=(1e9, '-', '-'))
            log('  garrison (e) NOTED, not a rule: %s (%d, %d, %d) is %d from the hall squad place %s %s; the stand-in legs never go there (y <= %d), the own path of the game did in W12 and why is NOT established; '
                'log the places of the bots with [CrewHop] in the next run' % (lab_, *q_, near_[0], near_[1], near_[2], ymax))
    if ymax > HALL_Y + 300:
        fail('(e) a leg or hold of the crew goes up to y %d, the gallery\'s police stand at y %d' % (ymax, GAL_Y))
    # (c) the START rows over the whole round
    men = start_men(B, ex, bool(o.get('waves2')), earliest=True)
    res = start_pressure(S, men, times=YARD_TIMES, rules=('exact',), nav=nav)
    line = []
    for T, r in res.items():
        old = [n for n in r['bear']['exact'] if not any(m['name'] == n and m['kind'] == 'wave' for m in men)]
        line.append('+%g s %d' % (T, len(r['bear']['exact'])))
        if old:
            fail('(c) GO + %g s: %d guns of the old squads bear on a START row: %s' % (T, len(old), ' '.join(old)[:140]))
        elif len(r['bear']['exact']) > YARD_GUNS:
            fail('(c) GO + %g s: %d guns bear on a START row (%d allowed): %s' % (T, len(r['bear']['exact']), YARD_GUNS, ' '.join(r['bear']['exact'])[:140]))
    log('  garrison (c): guns on the START rows (exact ray, hunters counted, the ante-room squads from GO + %g s): %s' % (WAKE_EARLIEST['ante'], '  '.join(line)))
    # (g) spawn-in unseen
    later = [r for r in rows if r['stage'] in ('beat',) or (r['stage'] in ('start', 'down') and (WAKE_BUILT or WAKE_SQUADS).get(r['squad']) == 'ante')]
    stations = [(n, q) for n, q in ROUTE_IN[:3]]       # START, the dock door, the dock: where an idle human or a straggler stands. The flights' stations are NOTED below (a side room off the corridor sees it)
    seen, noted = [], 0
    for r in later:
        if r['squad'] not in strict:
            continue
        for n, q in stations:
            if abs(r['at'][1] - q[1]) < 400.0 and math.dist(r['at'], q) <= PRESSURE_RANGE and S.sees_by(r['at'], tuple(q), ('exact',)):
                seen.append((r['squad'].split('!')[-1], r['what'], n))
                break
    for r in later:
        if r['squad'] in strict and any(abs(r['at'][1] - q[1]) < 400.0 and math.dist(r['at'], q) <= PRESSURE_RANGE and S.sees_by(r['at'], tuple(q), ('exact',)) for _n, q in ROUTE_IN[3:-1]):
            noted += 1
    log('  garrison (g): %d of %d later-comers' % (len(seen), sum(r['squad'] in strict for r in later)) + ' (the ante-room event) have an exact ray to the START / dock door / dock stations: %s; NOTED: %d have one to a station of the vault lobby / flights' % (seen[:3], noted))
    if seen:
        fail('(g) %d places of later-comers are in view of a station of the way in: %s' % (len(seen), seen[:3]))
    log('kl_fa_bank.garrison_check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


BEAT_GONE_T = 5.5                       # the beat's 14 police leave their posts for the ante-room when the beat box fires: counted at their posts only until here (their later places are unknown)
T_FROM = {'start': 0.0, 'down': 0.0, 'waveA': 0.5, 'beat': 3.0, 'waveB': 3.0, 'hall': 4.0, 'plaza': 11.0, 'waveD': 11.0}      # time index from which a man of that stage is in the world (the plan's station index)


def clear_men(M, keep, log=print):
    """ROOM_GATES, on the converted level M in strip(): the men of CLEAR_MEN to their new places (man_to checks that each stands on the navigation mesh). -> [(group, from, to)]"""
    import kl_route
    if not ROOM_GATES or not keep:                      # (--no-ai: no squad stays, nobody to move)
        return []
    sc = M.prp
    mesh = kl_route.load(LEVEL).mesh()
    moved = []
    for rel, new in CLEAR_MEN.items():
        hit = sc.resolve(R + rel)
        if len(hit) != 1 or sc.cls(hit[0]) not in ('ZGROUP', 'ZBoxPrimitive') or sc.names[sc.top[hit[0]]] not in keep:
            raise ValueError('kl_fa_bank: CLEAR_MEN names %s: %d nodes (a ZGROUP or a place of a kept squad wanted)' % (rel, len(hit)))
        was = world_of(M.ents[hit[0] - 1])[0]
        man_to(M, hit[0], tuple(float(v) for v in new), mesh)
        moved.append((rel, was, new))
    log('  kl_fa_bank: ROOM_GATES: %d men of the start and the way down and %d defend place(s) put off the crew\'s line (%d or more from it, at cover): %s' % (
        sum('DefendBehaviour' not in r for r, _w, _t in moved), sum('DefendBehaviour' in r for r, _w, _t in moved), ROOM_LINE_WANT,
        ', '.join('%s %d' % (r.split('!')[-1].split('\\')[0], math.dist(w, t)) for r, w, t in moved)))
    return moved


def squad_stage(sc, t):
    """The stage of a kept squad (STAGE / HALL) or None."""
    nm = sc.path[t][len(R):]
    return STAGE.get(nm) or ('hall' if nm in HALL else None)


def room_of(stage, p):
    """The room (a ROOMS name) whose men a man of stage `stage` standing at p belongs to, or None. start / down: by the place (dock = the dock floor y < 225 south of the door and the west level above it north of z -5600, lobby = the
    upper floor y 225 .. 300 from the corridor to the glass door, flights = y < 100, the ante-room y < -900 is the flights' too); beat = the airlock, hall, plaza = the front."""
    x, y, z = p
    if stage in ('start', 'down'):
        if y < 100:
            return 'flights'
        if (y < 225 and z > -6000.0) or (225 <= y <= 300 and z > -5600.0):
            return 'dock'                       # (the west level above the dock, where the stair up begins: the two patrol men)
        if 225 <= y <= 300 and z > -7900.0:
            return 'lobby'
        return None
    return {'beat': 'airlock', 'hall': 'hall', 'plaza': 'front'}.get(stage)


def room_men(B):
    """{room: [(squad node, group node, post)]} of the built level B: every man of the kept campaign squads by room_of (the bots, the waves and the
    police that arrive in a wave are not these)."""
    import kl_fa_bots_rt as RT
    sc, out = B.sc, collections.OrderedDict((r['name'], []) for r in ROOMS)
    for t, groups in RT.enemy_squads(B).items():
        rel = sc.path[t][len(R):]
        if rel.startswith((BOT_SQUAD, WAVE_G)):
            continue
        stage = squad_stage(sc, t)
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups:
                room = room_of(stage, B.at(k))
                if room:
                    out[room].append((t, sc.parent[k], B.at(k)))
    return out


def pick_holds_bank(spots, n=7, seps=(110.0, 100.0, 90.0, ROOM_HOLD_SEP), tries=400):
    """Seven of the places kl_fa_bots_rt.hold_spots found -> (places, the separation asked for); ([], 0) when there are not seven. LIFTED from kl_fa_club.pick_holds_club (the same
    search: the widest separation of `seps` for which a set exists; a fixed order first, then shuffles of a fixed seed; the planner's own pick packs one cover box's places along a line and
    gives up where a box has 24 places in a 4 m strip) WITH ONE CHANGE to the score: a spot is (x, y, z, polygon, cover, behind, clearance, distance from the box, men who see it) and the score
    puts the number of HIDDEN holds first (ROOM_HIDE: no man of the room sees the place), then the number of different cover boxes, the holds behind their box, the least clearance."""
    import random
    if len(spots) < n:
        return [], 0.0
    if ROOM_HIDE:                               # second fix: a set of seven under HOLD_GUNS guns each, where one exists (the widest separation of `seps` for which it does), before any other
        low = [s for s in spots if len(s) > 8 and s[8] <= HOLD_GUNS]
        if len(low) >= n:
            got, sep = pick_holds_bank_all(low, n, seps, tries)
            if got:
                return got, sep
    return pick_holds_bank_all(spots, n, seps, tries)


def pick_holds_bank_all(spots, n, seps, tries):
    import random
    hd = lambda a, b: math.hypot(a[0] - b[0], a[2] - b[2])
    guns = lambda s: s[8] if len(s) > 8 and ROOM_HIDE else 0               # how many men in the world have a free exact line to the place (0 = hidden)
    key = lambda s: (guns(s), not s[5], abs(s[7] - 130.0), -s[6])
    rng = random.Random(7)
    for sep in seps:
        best = None
        for t in range(tries):
            order = sorted(spots, key=key) if t == 0 else rng.sample(spots, len(spots))
            got, used = [], collections.Counter()
            for rnd in (0, 1):
                for s in order:
                    if len(got) < n and not (rnd == 0 and used[s[4]]) and all(hd(s, o) >= sep for o in got):
                        got.append(s)
                        used[s[4]] += 1
            if len(got) >= n:
                score = (-sum(guns(g) for g in got), len(used), sum(1 for g in got if g[5]), min(g[6] for g in got))
                if best is None or score > best[0]:
                    best = (score, got[:n])
        if best:
            return best[1], sep
    return [], 0.0


class _Probe:
    """kl_pf4_probe on the folder's mesh: ok(p) = the 16 probes of the game's 'down' test (re/bots_down.md 9) all reach a full 1.0 (1 m of free mesh round the place)."""

    def __init__(self, folder):
        import glob
        import kl_pf4_probe as PP
        self.PP = PP
        self.M = PP.build(PP.Mesh(PP.nav_from_zip(sorted(glob.glob(os.path.join(folder, '*_Main.zip')))[0])))

    def fractions(self, p):
        pi, fr = self.PP.probes(self.M, p[0], p[1], p[2])
        return fr if pi is not None else []

    def ok(self, p):
        fr = self.fractions(p)
        return len(fr) == 16 and min(fr) >= ROOM_MESH_MIN


@contextlib.contextmanager
def rt_for_bank(gates, men, B, sight, probe, stats=None):
    """kl_fa_bots_rt with this level's table for one call of gates_plan (LIFTED from kl_fa_club.rt_for_club): GATES, EN_ (the squads are named in full), POST_KEEP, GATE_MAX, pick_holds,
    hold_spots, wake_map (no squad 'known': the start squads are timer-started and ARE the fight), near_post - put back afterwards. hold_spots is wrapped: the room's floor (dy), 1 m inside the
    mesh (the probes), 300 from a man of an earlier room, and every spot gets a 9th member: no man of the room sees it (ROOM_SIGHT)."""
    import kl_fa_bots_rt as RT
    saved = {k: getattr(RT, k) for k in ('GATES', 'EN_', 'POST_KEEP', 'GATE_MAX', 'pick_holds', 'hold_spots', 'wake_map', 'near_post')}
    spots0, wake0, near0 = RT.hold_spots, RT.wake_map, RT.near_post
    order = [r['name'] for r in gates]
    stats = stats if stats is not None else {}
    by_name = {B.sc.names[t]: t for t in RT.enemy_squads(B)}
    stage_of = {t: squad_stage(B.sc, t) for t in by_name.values()}
    esq = RT.enemy_squads(B)
    all_men = [(stage_of[t], B.at(k)) for t in by_name.values() if stage_of[t] for k in range(t + 1, B.sc.end[t]) if B.sc.cls(k) == 'ZFFActor' and B.sc.parent[k] in esq[t]]
    cur = {'free': set(), 'world': ('start', 'down')}

    def near(p, posts, among, keep=ROOM_POST_CLEAR):
        # the posts of a man the seven wait for (this gate's squads and the earlier gates') are where he STANDS (his start); the places his routs walk to are the fight itself - he comes to
        # the crew (Guards_01's rout runs from the landing up the stairs to the glass door: no hold on the flights could be 400 from it). The squads of later rooms count with every place.
        # ... and the squads that are not in the world yet are no post: the police of the beat come with the ante-room box (their routs run through the lobby's south end and down the
        # stairs: the way in's holds could not be 400 from them), the plaza's with the box at the hall's south end; a way-in gate counts the start and the down squads only
        return near0(p, {t: ([x for x in v if x[2] == 'start'] if t in cur['free'] else v) for t, v in posts.items() if stage_of.get(t) in cur['world']}, among, keep)

    def spots(B_, nav, home, covers, g, *rest):
        # the squads that count by their start place only: those of every room up to this gate's in the table's order, GATED OR NOT (second fix: with the dock off, its squads are no gate's
        # and the planner took every place their routs walk to for a post: no hold was left on the flights)
        upto = [r['name'] for r in ROOMS][:[r['name'] for r in ROOMS].index(g['name']) + 1]
        cur['free'] = {by_name[n] for r in gates[:order.index(g['name']) + 1] for n in r['squads'] if n in by_name} | {t for rm in upto for t, _g, _p in men.get(rm, ())}
        cur['world'] = ('start', 'down') if g['leg'] == 'in' else ('start', 'down', 'beat', 'hall')
        # a lattice four times as fine: the planner's step of 40 leaves a cover box's ring (HOLD_RING) with a few places only, and 1 m inside the mesh (the probes) is the
        # outer part of the ring (the box itself is a hole in the mesh) - so the covers are laid 20 aside in turn and the distance and the side are taken from the true box
        true, out, seen_ = dict(covers), [], set()
        ex, ez = g['enemy']
        nn = math.hypot(ex, ez) or 1.0
        for dx, dz in ((0.0, 0.0), (20.0, 0.0), (0.0, 20.0), (20.0, 20.0)):
            for s in spots0(B_, nav, home, [(k, (c[0] + dx, c[1], c[2] + dz)) for k, c in covers], g, *rest):
                c = true[s[4]]
                d = math.hypot(s[0] - c[0], s[2] - c[2])
                key = (round(s[0]), round(s[2]))
                if not (RT.HOLD_RING[0] <= d <= ROOM_HOLD_RING[1]) or key in seen_:
                    continue
                seen_.add(key)
                out.append((s[0], s[1], s[2], s[3], s[4], ((c[0] - s[0]) * ex + (c[2] - s[2]) * ez) / nn >= 0.5 * d, s[6], d))
        n0 = len(out)
        out = [s for s in out if abs(s[1] - g['y']) <= g.get('dy', 150.0)]
        n1 = len(out)
        out = [s for s in out if probe.ok(s)]
        n2 = len(out)
        prior = [p for r in order[:order.index(g['name'])] for _t, _g, p in men.get(r, ())]
        out = [s for s in out if not any(abs(p[1] - s[1]) <= RT.FLOOR_DY and RT.hdist(s, p) < ROOM_AFTER_CLEAR for p in prior)]
        # the 9th member = GUNS: the men of every squad that is in the world at this gate (not only the gate's room: second fix, the skeptic's fault 2) with a free EXACT ray to the place
        # within HOLD_GUN_RANGE on its floor - the number the check hold-guns counts (HOLD_GUNS)
        world_ = [p for stg, p in all_men if stg in cur['world']]
        tagged = []
        for s in out:
            n_seen = sum(1 for p in world_ if abs(p[1] - s[1]) < HOLD_GUN_DY and math.dist(p, s[:3]) < HOLD_GUN_RANGE and sight.sees_by(tuple(s[:3]), p, ('exact',)))
            tagged.append(tuple(s) + (n_seen,))
        stats[g['name']] = dict(planner=n0, on_floor=n1, inside_mesh=n2, after_clear=len(out), hidden=sum(1 for s in tagged if s[8] == 0),
                                fewest_guns=min([s[8] for s in tagged] or [0]))
        return tagged
    RT.GATES, RT.EN_, RT.POST_KEEP = tuple(gates), '', ROOM_POST_CLEAR
    RT.GATE_MAX = 99                            # the planner names whole squads; the TADs name the room's men (rooms_plan), at most 9 of them (rooms_check)
    RT.pick_holds, RT.hold_spots = pick_holds_bank, spots
    RT.wake_map = lambda B_, squads=None: (wake0(B_, squads)[0], {})
    RT.near_post = near                         # (the default of the original is bound at import: 300)
    try:
        yield RT
    finally:
        for k, v in saved.items():
            setattr(RT, k, v)


def rooms_plan(B, P, log=print):
    """ROOM_GATES: plan P (kl_fa_bots.plan of B after bots_gate: the vault gate is in) with the rooms' gates in front of the ante-room hold (the way in) and in the way out (before the last
    way place of the hall). P's stations, steps, every bot's places and the indices that name a station are rewritten; the gate list goes to P['vault_gates'] (kl_fa_bots_rt.Street's form,
    plus 'groups' = the men named, 'unnamed', 'seen_by_holds', 'stats', 'fractions'). -> P"""
    import copy
    import kl_fa_bots as F
    sc = B.sc
    nav = F.Nav(B.scene.nav)
    S = F.stations(B, nav)
    st = P['stations']
    kind_at = lambda k: [i for i, s in enumerate(st) if s['kind'] == k]
    i_enter, i_loot, i_ante, i_exit = kind_at('enter')[0], kind_at('loot')[0], P['gate']['station'], kind_at('exit')[0]
    outs = list(range(i_loot + 1, i_exit))
    if len(outs) < 2 or i_enter != 0 or i_ante != i_loot - 1:
        raise ValueError('kl_fa_bank.rooms_plan: the plan\'s stations are not enter .. ante-room hold, loot, ways, exit (%s)' % [s['kind'] for s in st])
    men = room_men(B)
    rooms = [r for r in ROOMS if r['name'] in ROOM_ON]
    empty = [r['name'] for r in rooms if not men[r['name']]]
    if empty:
        log('  rooms: no man stands in %s - no gate there' % ', '.join(empty))
    table, named = [], {}
    for r in rooms:
        ms = men[r['name']]
        if ms:
            table.append(dict(r, squads=tuple(dict.fromkeys(sc.names[t] for t, _g, _p in ms))))
            named[r['name']] = [R + sc.path[g][len(R):] for _t, g, _p in ms]
    if not table:
        return P
    sight = Sight(B.folder, B, lambda *a: None)
    probe = _Probe(B.folder)
    stats = {}
    places = lambda i: [tuple(P['bots'][N]['places'][i]) for N in F.BOTS]
    start = [tuple(P['bots'][N]['start']) for N in F.BOTS]

    def run(frm, to_places, tab):
        """One call of the planner: seven places before (frm) -> the holds of `tab`'s rooms -> seven places after (to_places) -> (gate dicts, the hold stations)."""
        if not tab:
            return [], []
        P2 = {'stations': [{'kind': 'loot', 'what': 'before', 'node': None, 'distinct_places': 7, 'places': [[round(v, 1) for v in p[:3]] for p in frm]},
                           {'kind': 'park', 'what': 'after', 'node': None, 'distinct_places': 7, 'places': [[round(v, 1) for v in p[:3]] for p in to_places]}],
              'steps': [], 'bots': {N: {'places': [list(frm[b][:3]), list(to_places[b][:3])]} for b, N in enumerate(F.BOTS)}}
        with rt_for_bank(tab, men, B, sight, probe, stats) as RT:
            try:
                got = RT.gates_plan(B, nav, S, P2, {'gate_names': None}, lambda s: log(s) if s.lstrip().startswith(('gate', 'to the car', 'NOTE', 'the seven')) else None)
            except ValueError:
                log('  rooms: the places left by each rule of the hold search (planner, on the floor, inside the mesh, clear of earlier rooms, hidden): %s' % stats)
                raise
        holds = [s for s in P2['stations'][1:-1] if s['kind'] == 'hold']
        if len(holds) != len(tab) or len(got) != len(tab):
            raise ValueError('kl_fa_bank.rooms_plan: %d holds / %d gates for %d rooms' % (len(holds), len(got), len(tab)))
        return got, holds
    g_in, h_in = run(start, places(i_ante), [t for t in table if t['leg'] == 'in'])
    g_out, h_out = run(places(outs[-2]), places(outs[-1]), [t for t in table if t['leg'] == 'out'])
    gates = g_in + g_out
    for g in gates:
        every = named[g['name']]
        g['groups'], g['room_men'], g['unnamed'] = every, len(every), []
        at = {R + sc.path[gp][len(R):]: p for _t, gp, p in men[g['name']]}
        ends = [tuple(h[:3]) for h in g['holds']]
        g['seen_by_holds'] = {x.split('!')[-1]: sorted({i for i, h in enumerate(ends) if sight.sees_by(h, at[x], RULES_X)}) for x in every}
        if ROOM_NAME_SEEN:
            seen = [x for x in every if g['seen_by_holds'][x.split('!')[-1]]]
            if seen:
                g['groups'], g['unnamed'] = seen, [x for x in every if x not in seen]
        g['men'] = len(g['groups'])
        g['wait'] = '%03d_TriggerActorsDead_%s' % (30 + [x['name'] for x in gates].index(g['name']), g['name'])
        g['seconds'] = ROOM_WAIT_S
        g['stats'] = stats.get(g['name'])
        g['fractions'] = [min(probe.fractions(h) or [0.0]) for h in ends]
    # ---- the new station list. old: enter, ways, ante hold (i_ante), loot, out ways (outs), exit .. park
    new, pl = [], {N: [] for N in F.BOTS}

    def put(s_old=None, i_old=None, s_new=None):
        new.append(copy.deepcopy(s_old if s_old is not None else s_new))
        for b, N in enumerate(F.BOTS):
            pl[N].append(list(P['bots'][N]['places'][i_old]) if i_old is not None else list(s_new['places'][b]))
        return len(new) - 1
    steps, idx = [], {}
    gstep = lambda g, k, leg, stop: {'name': '%03d_DefendBehaviour_out_%s' % (30 + gates.index(g), g['name']), 'leg': leg, 'stop': stop, 'stations': [k], 'gate': g['name']}
    if g_in:
        # [first gate's hold] [enter] [the other holds] [ante-room hold] [loot]: the stage-1 box is the dock's door, behind the first gate
        door_first = g_in[0]['name'] == 'dock'  # the dock's hold lies at the door, BEFORE the stage-1 station; any other first gate (no dock gate, second fix) comes after it
        if door_first:
            ks = [put(s_new=h) for h in h_in]
            k_enter = put(s_old=st[i_enter], i_old=i_enter)
        else:
            k_enter = put(s_old=st[i_enter], i_old=i_enter)
            steps.append({'name': '010_DefendBehaviour_to_loot', 'leg': 'in', 'stop': 0, 'stations': [k_enter]})
            ks = [put(s_new=h) for h in h_in]
        for n_, (g, k) in enumerate(zip(g_in, ks)):
            steps.append(gstep(g, k, 'in', 0))
            g['step'] = steps[-1]['name']
            if n_ == 0 and door_first:
                steps.append({'name': '010_DefendBehaviour_to_loot', 'leg': 'in', 'stop': 0, 'stations': [k_enter]})
        k_ante = put(s_old=st[i_ante], i_old=i_ante)
        steps.append({'name': '011_DefendBehaviour_to_loot', 'leg': 'in', 'stop': 0, 'stations': [k_ante]})
        idx[i_enter], idx[i_ante] = k_enter, k_ante
    else:
        for i in range(i_ante + 1):
            idx[i] = put(s_old=st[i], i_old=i)
        steps += [dict(s) for s in P['steps'] if s['leg'] == 'in' and s.get('stop', 0) == 0]
        for s in steps:
            s['stations'] = [idx[i] for i in s['stations']]
        k_enter, k_ante = idx[i_enter], idx[i_ante]
    idx[i_loot] = put(s_old=st[i_loot], i_old=i_loot)
    steps.append({'name': '030_DefendBehaviour_to_loot', 'leg': 'in', 'stop': 1, 'stations': [idx[i_loot]]})
    # the way out's own way stations that stand within ROOM_POST_CLEAR of the start place of a man of the start / down squads on their floor are DROPPED (the flights' landings: 12 m wide,
    # the line on the west side, the men east of it - a station in the middle is within 400 of them whatever they do); the order of the step is then longer (the game's pathfinder walks it:
    # the escort's and the boarding orders are 100 m, the hall gate's of Retomoto too)
    import kl_fa_bots_rt as RT_
    alive = [B.at(k) for t, gr in RT_.enemy_squads(B).items() if squad_stage(sc, t) in ('start', 'down') for k in range(t + 1, sc.end[t]) if sc.cls(k) == 'ZFFActor' and sc.parent[k] in gr]
    drop = [i for i in outs[:-1] if st[i]['kind'] == 'way' and any(abs(q[1] - p[1]) <= RT_.FLOOR_DY and RT_.hdist(p, q) < ROOM_POST_CLEAR for p in st[i]['places'] for q in alive)] if g_in else []
    for i in drop:
        log('  rooms: way-out station %d (%s) %s dropped: within %d of the start place of a man of the way in' % (i, st[i]['kind'], [round(v) for v in st[i]['places'][0]], ROOM_POST_CLEAR))
    for i in outs[:-1]:
        if i not in drop:
            idx[i] = put(s_old=st[i], i_old=i)
    ks_out = [put(s_new=h) for h in h_out]
    idx[outs[-1]] = put(s_old=st[outs[-1]], i_old=outs[-1])
    for i in range(i_exit, len(st)):
        idx[i] = put(s_old=st[i], i_old=i)
    for s in [s for s in P['steps'] if s['leg'] == 'out']:
        if outs[-1] in s['stations']:
            if s['stations'][0] != outs[-1]:
                raise ValueError('kl_fa_bank.rooms_plan: the hall way place is not the first of its step (%s)' % s['stations'])
            for g, k in zip(g_out, ks_out):
                steps.append(gstep(g, k, 'out', None))
                g['step'] = steps[-1]['name']
        if [i for i in s['stations'] if i in idx]:
            steps.append(dict(s, stations=[idx[i] for i in s['stations'] if i in idx]))
    P['stations'], P['steps'] = new, steps
    P['dropped_stations'] = drop
    for N in F.BOTS:
        P['bots'][N]['places'] = pl[N]
    P['gate']['station'] = k_ante
    P['window']['stage_1_station'] = k_enter
    for vc in P['vehicle_call'].values():
        vc['on_the_way_to_station'] = idx.get(vc['on_the_way_to_station'], vc['on_the_way_to_station'])
    P['vault_gates'] = gates
    return P


def rooms_timetable(P):
    """Seconds after the GO, from the plan: the slowest crew's van call (every room runs its clock out) against the budget. -> dict"""
    gates = P.get('vault_gates') or []
    call = NOAI_CALL + ROOM_WAIT_S * len(gates)
    latest = ROUND_CLOCK - ROOM_VAN_MARGIN - GO_EVENT
    return dict(rooms=len(gates), call=call, latest=latest, slack=latest - call, noai=NOAI_CALL)


def rooms_note(P, log=print):
    """The plan's note and the budget -> raises when the slowest crew calls the van too late."""
    tt = rooms_timetable(P)
    if tt['slack'] < 0:
        raise ValueError('kl_fa_bank.rooms_plan: %d gates of %g s: the slowest crew calls the van at GO + %d s, the budget is GO + %d s (%g s round, %g s margin, no-enemy baseline %g s)' % (
            tt['rooms'], ROOM_WAIT_S, tt['call'], tt['latest'], ROUND_CLOCK, ROOM_VAN_MARGIN, NOAI_CALL))
    note = ('THE ROOM GATES: %d rooms (%s); each is a hold of seven at distinct cover places, 1 m inside the mesh, and a TriggerActorsDead on the room\'s men (at most %g s). Worst case: the van is '
            'called at GO + %d s (the no-enemy baseline %g s + %d x %g s), the budget is GO + %d s' % (
                tt['rooms'], ', '.join(g['name'] for g in P['vault_gates']), ROOM_WAIT_S, tt['call'], NOAI_CALL, tt['rooms'], ROOM_WAIT_S, tt['latest']))
    P['notes'].append(note)
    log('  NOTE ' + note)
    return tt


def dyn(src, dst, log=print):
    """kl_fa_bots_dyn.build (the chain's dynamic step) with ONE difference while ROOM_GATES: no bot gets a hold at cover or a hold timer anywhere (kl_fa_bots_dyn.PERS' out_holds False for the
    seven and the last loot wait read as the first element, for the call only: every leg of the chain is then 'behind' it), and no leg but the last has a fork. LIFTED from kl_fa_club.dyn:
    behind a gate a hold of the dynamic step - a cover of ITS choosing and a timer of 4 .. 8 s - would be a second wait for a bot the gate has just let go (kl_fa_bots_rt's review, D3), and a
    fork's other way is a corridor the planner never looked at. What the step still adds: the stagger at the start (before the first gate), the opening modifier, the forks of the final leg."""
    import kl_fa_bots_dyn as D
    import json
    read_opts(src)
    saved, llw, forks0 = D.PERS, D.last_loot_wait, D.Routes.forks
    try:
        with open(os.path.join(src, 'bots.json'), encoding='utf-8') as f:
            gated = bool((json.load(f).get('plan') or {}).get('vault_gates'))
    except (OSError, ValueError):
        gated = False
    if ROOM_GATES and gated:                    # (a build without gates - no enemies - gets the dynamic step as it always did)
        D.PERS = {n: p._replace(out_holds=False) for n, p in saved.items()}
        D.last_loot_wait = lambda flat, cut_off, timers=True: -1

        def forks(self, q, flats, pers, opt, log=print):
            rep = forks0(self, q, flats, pers, opt, log)
            for flat in flats:
                n_leg = [i for i, (kind, _x) in enumerate(flat) if kind == 'leg']
                for i, (kind, leg) in enumerate(flat):
                    if kind == 'leg' and i != n_leg[-1]:
                        for pl in leg:
                            pl.pop('fork', None)
            return rep
        D.Routes.forks = forks
    try:
        return D.build(src, dst, None, log)
    finally:
        D.PERS, D.last_loot_wait, D.Routes.forks = saved, llw, forks0


def rooms_check(folder, log=print):
    """The room gates of a finished folder (before or after the dynamic step) -> list of faults. Reads bots.json's 'vault_gates' (a folder without has none: nothing to check, said).
    FAILS: a gate whose TriggerActorsDead is missing from a squad, has no clock (a group without an actor), names a missing group, another group than planned, a man a gate before it named,
    or field 1 other than 0; more than 9 groups; the seven holds of a room not at seven distinct places (ROOM_HOLD_SEP) / a hold not ROOM_HOLD_RING from a cover box / not 1 m inside the
    mesh; a hold or station within ROOM_POST_CLEAR of a post of a man who may be alive on his floor (a man of an earlier room: ROOM_AFTER_CLEAR); a start within ROOM_LINE_CLEAR of the line;
    a timer or a loot wait behind a gate (between the first gate and the last of its leg); a gate in front of the hold with no gate step; the timetable past the budget."""
    import json
    import kl_fa_bots as F
    import kl_fa_bots_rt as RT
    bad = []

    def fail(s):
        bad.append(s)
        log('  FAIL ' + s)
    try:
        with open(os.path.join(folder, 'bots.json'), encoding='utf-8') as f:
            P = json.load(f).get('plan') or {}
    except (OSError, ValueError):
        P = {}
    gates = P.get('vault_gates')
    if not gates:
        log('  rooms: bots.json has no room gates (a build without --gates): not checked')
        return bad
    read_opts(folder)
    B = F.Built(folder)
    sc = B.sc
    tops = [t for t in sc.tops() if sc.names[t].startswith(BOT_SQUAD + 'Squad#')]
    tad = {k: v for k, _i, v in kl_fa.controllers(sc, 'TriggerActorsDead')}
    defend = {k: v for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout')}
    NEXT = {'DefendBehaviourRout': 7, 'TriggerActorsDead': 2, 'TriggerDelay2': 4, 'TriggerLootDepleted': 4, 'TriggerCounter': 4}
    nxt = {k: [j for s in v[NEXT[cn]] for j in sc.resolve(s)] for cn in NEXT for k, _i, v in kl_fa.controllers(sc, cn)}
    kind = {k: cn for cn in NEXT for k, _i, v in kl_fa.controllers(sc, cn)}
    covers = RT.cover_boxes(B)
    sq = RT.enemy_squads(B)
    men = []                                           # (post, group path, squad path, stage)
    for t, groups in sq.items():
        rel = sc.path[t][len(R):]
        if rel.startswith((BOT_SQUAD, WAVE_G)):
            continue
        stage = squad_stage(sc, t)
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor' and sc.parent[k] in groups:
                men.append((B.at(k), sc.path[sc.parent[k]], rel, stage))
    probe = _Probe(folder)
    sight = Sight(folder, B, lambda *a: None)
    named_before, holds_seen, rows = set(), [], []
    ends_of = {}
    rank = {g['name']: i for i, g in enumerate(gates)}
    rank_room = {r['name']: i for i, r in enumerate(ROOMS)}
    for gi, g in enumerate(gates):
        found, ends = [], []
        for t in tops:
            hit = [k for k in range(t, sc.end[t]) if sc.names[k] == g['wait'] and k in tad]
            if len(hit) != 1:
                fail('%s: %d TriggerActorsDead %s (wanted 1)' % (sc.names[t], len(hit), g['wait']))
                continue
            v = tad[hit[0]]
            found.append(v)
            if sorted(s.lower() for s in v[0]) != sorted(s.lower() for s in g['groups']):
                fail('%s: %s names %d groups, the plan %d (%s)' % (sc.names[t], g['wait'], len(v[0]), len(g['groups']), [s.split('!')[-1] for s in v[0]][:4]))
            if v[1] != 0:
                fail('%s: %s field 1 is %s (stock: 0)' % (sc.names[t], g['wait'], v[1]))
            before = [k for k, d in defend.items() if t < k < sc.end[t] and any(hit[0] == j for s in d[7] for j in sc.resolve(s))]
            if not before:
                fail('%s: no step leads into %s' % (sc.names[t], g['wait']))
            for k in before:
                if defend[k][1]:
                    ends.append(B.at(sc.resolve(defend[k][1][-1])[0]))
        if len({tuple(v[0]) for v in found}) > 1:
            fail('gate %s: the seven squads name different groups' % g['name'])
        for s in (found[0][0] if found else []):
            hits = sc.resolve(s)
            if len(hits) != 1 or not any(sc.cls(c) == 'ZFFActor' and sc.parent[c] == hits[0] for c in range(hits[0], sc.end[hits[0]])):
                fail('gate %s names %s: %s' % (g['name'], s, 'no such group' if not hits else 'a group without an actor (a TriggerActorsDead then has no 30 s clock)'))
            if s.lower() in named_before:
                fail('gate %s names %s, which a gate before it already waited for' % (g['name'], s.split('\\')[-1]))
            named_before.add(s.lower())
        if len(found[0][0] if found else []) > 9:
            fail('gate %s names more than 9 groups (stock: 9 at most)' % g['name'])
        if len(ends) != 7 or any(math.dist(a, b) < ROOM_HOLD_SEP for i, a in enumerate(ends) for b in ends[i + 1:]):
            fail('gate %s: %d hold places, %s apart at least (wanted 7, %g)' % (g['name'], len(ends), round(min([math.dist(a, b) for i, a in enumerate(ends) for b in ends[i + 1:]] or [0])), ROOM_HOLD_SEP))
        ring, hid = [], 0
        mine = [p for p, gp, _r, _s in men if gp.lower() in {x.lower() for x in g['groups']}]
        for h in ends:
            d = min([RT.hdist(h, c) for _k, c in covers if abs(c[1] - h[1]) <= 260.0] or [1e9])
            ring.append(d)
            if not (ROOM_HOLD_RING[0] <= d <= ROOM_HOLD_RING[1]):
                fail('gate %s: a hold at (%d, %d, %d) is %d from the nearest cover box (wanted %d..%d)' % (g['name'], *h, d, *ROOM_HOLD_RING))
            fr = probe.fractions(h)
            if len(fr) != 16 or min(fr) < ROOM_MESH_MIN:
                fail('gate %s: a hold at (%d, %d, %d) is not 1 m inside the mesh (probes %s)' % (g['name'], *h, fr))
            if not any(sight.sees_by(h, p, ROOM_SIGHT) for p in mine):
                hid += 1
        for h in ends:                                  # the cash registers: a hold inside the loot window of a stack (800 / 400) would be a stop AT the registers (the loot tactic takes any stack in reach)
            near_t = [round(math.dist(h, q)) for q, _v in teller_loot() if abs(q[1] - h[1]) < 400.0 and math.dist(h, q) < 850.0]
            if near_t:
                fail('gate %s: a hold at (%d, %d, %d) is %d from a teller stack (the loot window is 800, 50 more kept)' % (g['name'], *h, near_t[0]))
        for h in ends:
            if any(math.dist(h, o) < 1.0 for o in holds_seen):
                fail('gate %s: a hold at (%d, %d, %d) is the place of a hold of an earlier gate' % (g['name'], *h))
        holds_seen += ends
        ends_of[g['name']] = ends
        lim = lambda p, rm: ROOM_AFTER_CLEAR if (rm in rank_room and g['name'] in rank_room and rank_room[rm] < rank_room[g['name']]) else ROOM_POST_CLEAR
        close = [(round(RT.hdist(h, p)), r.split('!')[-1], tuple(round(c) for c in p)) for h in ends for p, _gp, r, stg in men
                 if abs(p[1] - h[1]) <= RT.FLOOR_DY and RT.hdist(h, p) < lim(p, room_of(stg, p))]
        if close:
            fail('gate %s: %d hold(s) within %d of a post of a man who may be alive, e.g. %s' % (g['name'], len(close), ROOM_POST_CLEAR, close[0]))
        seen = sum(1 for p in mine if any(sight.sees_by(h, p, RULES_X) for h in ends))
        rows.append((g['name'], len(mine), seen, round(min(ring)), round(max(ring)), hid, g.get('room_men', len(mine)), [tuple(round(c) for c in h) for h in ends][:1]))
    for name, n_, seen, lo, hi, hid, all_, hs in rows:
        log('  room %-8s %d of its %d men named (the rest no hold can see), %d of the named in a free line (any rule, exact ray too) of a hold; holds %d..%d from a cover box, %d of 7 hidden from the room\'s men, '
            'none within %d of a living post, all 1 m inside the mesh; e.g. %s' % (name, n_, all_, seen, lo, hi, hid, ROOM_POST_CLEAR, hs[0]))
    # ---- the plan's stations (a station is where a bot stands at the end of a step) against the men who are in the world and not waited for: before the loot the start and the down
    # squads (every man, whatever a gate names: the way IN is fought room by room); behind it the hall's squads and any man of the start / down squads no gate names. The way out passes the
    # rooms of the way in (their men are dead or the gates' clocks have run) and the beat's police start where the airlock stations are (they have left for the ante-room by then:
    # the box that wakes them fires when the first criminal is in it).
    named_all = {x.lower() for g in gates for x in list(g['groups']) + list(g.get('unnamed') or [])}      # (the room's men: the clock covers those no hold sees)
    i_loot = max(i for i, s in enumerate(P['stations']) if s['kind'] == 'loot')
    for i, s in enumerate(P['stations']):
        if s['kind'] in ('hold', 'loot', 'exit', 'level', 'park'):
            continue
        who = [(q, r) for q, gp, r, stg in men if (stg in ('start', 'down') and (i < i_loot or gp.lower() not in named_all)) or (stg == 'hall' and i > i_loot)]
        for p in s['places']:
            near = [(round(RT.hdist(p, q)), r.split('!')[-1]) for q, r in who if abs(q[1] - p[1]) <= RT.FLOOR_DY and RT.hdist(p, q) < ROOM_POST_CLEAR]
            if near:
                fail('station %d (%s) place (%d, %d, %d) is within %d of a man of %s' % (i, s['kind'], *p, *near[0]))
    # ---- the men: no start within ROOM_LINE_CLEAR of the line. Second fix (the skeptic's faults 3 and 4): the line is the stand-in path of EVERY one of the seven bots through its places
    # (not the first bot's alone) and, for a leg from the dock floor to the lobby's upper floor, both ways the game's pathfinder may take (ROOM_ALT_VIA); a man that CLEAR_MEN moved
    # must be ROOM_LINE_WANT from all of them
    lines, alts = [], []
    nav = F.Nav(B.scene.nav)
    snap = lambda p: (lambda h: (p[0], h[1], p[2]) if h else None)(nav.at(p[0], p[1], p[2], dy=200.0))
    for N_, b_ in P['bots'].items():
        pl_ = b_['places']
        for a, b in zip(pl_, pl_[1:]):
            got = RT.way_samples(nav, tuple(a), tuple(b))
            if got:
                lines.append(got[0])
            if a[1] < 225.0 <= b[1] and b[2] < -5900.0:
                for v in (snap(V) for V in ROOM_ALT_VIA):
                    s1, s2 = (RT.way_samples(nav, tuple(a), v), RT.way_samples(nav, v, tuple(b))) if v else (None, None)
                    if s1 and s2:
                        alts.append(s1[0] + s2[0])
    def dline_(p, ls):
        return min([seg_dist(p, a, b) for pl in ls for a, b in zip(pl, pl[1:]) if abs(a[1] - p[1]) < 150] or [1e9])
    moved_at = {k.lower(): v for k, v in CLEAR_MEN.items()}
    near_line = []
    for p, gp, r, stg in men:
        if stg not in ('start', 'down'):
            continue
        d = dline_(p, lines)
        if d < ROOM_LINE_CLEAR:
            near_line.append((round(d), gp.split('!')[-1], tuple(round(c) for c in p)))
        if gp[len(R):].lower() in moved_at or gp.lower() in moved_at:
            d2 = min(d, dline_(p, alts))
            if d2 < ROOM_LINE_WANT - 1.0:
                fail('%s was moved to %s and stands %d from a bot\'s line or the other way down from the dock (%d wanted)' % (gp.split('!')[-1], tuple(round(c) for c in p), d2, ROOM_LINE_WANT))
    for d, gp, p in near_line:
        if gp not in ROOM_STAY:
            fail('%s starts at %s, %d from the crew\'s line (the point-blank reach: %d)' % (gp, p, d, ROOM_LINE_CLEAR))
    log('  lines: %d legs of the seven bots, %d other ways down from the dock floor' % (len(lines), len(alts)))
    # ---- HOLD-GUNS (second fix, the skeptic's faults 1 and 2): men of every squad in the world at a gate (all start / down men; the beat's and the hall's for the way out) with a free exact
    # ray to a hold, within HOLD_GUN_RANGE on its floor - the earlier rooms' men too, not the gate's room alone
    for g in ([] if STAGING else gates):                # (with STAGING pressure_check counts the men awake at each time instead)
        world = ('start', 'down') if g['name'] in ('dock', 'lobby', 'flights') else ('start', 'down', 'beat', 'hall')
        cnt, who = [], []
        for h in ends_of[g['name']]:
            w_ = [(round(math.dist(h, p) / 100), gp.split('!')[-1], r_.split('!')[-1]) for p, gp, r_, stg in men if stg in world and abs(p[1] - h[1]) < HOLD_GUN_DY
                  and math.dist(h, p) < HOLD_GUN_RANGE and sight.sees_by(tuple(h), p, ('exact',))]
            cnt.append(len(w_))
            who.append(w_)
        worst = max(cnt or [0])
        log('  hold-guns %-8s %s (exact ray, %d m, %d men in the world; wanted %d, fails at %d)' % (g['name'], cnt, HOLD_GUN_RANGE / 100, sum(1 for _p, _g, _r, stg in men if stg in world), HOLD_GUNS, HOLD_GUNS_MAX + 1))
        if worst > HOLD_GUNS_MAX:
            fail('hold-guns: gate %s: %d guns bear on a hold (at most %d): %s' % (g['name'], worst, HOLD_GUNS_MAX, '; '.join('%d m %s' % (d, n) for d, n, _r in who[cnt.index(worst)][:8])))
        elif worst > HOLD_GUNS:
            log('      NOTE KNOWN over the yardstick: %d guns on a hold (%d wanted; HOLD_GUNS_KNOWN %s)' % (worst, HOLD_GUNS, HOLD_GUNS_KNOWN.get(g['name'], '-')))
    # ---- no dynamic hold behind a gate: the step's hold timers are named '..._Timer_hold' (kl_fa_bots_dyn); with ROOM_GATES the step adds none (dyn above)
    for t in tops:
        holds_t = [sc.names[k] for k in range(t, sc.end[t]) if kind.get(k) == 'TriggerDelay2' and 'Timer_hold' in sc.names[k]]
        if holds_t:
            fail('%s: %d hold timer(s) of the dynamic step (%s ..) in a build with room gates' % (sc.names[t], len(holds_t), holds_t[0]))
    tt = rooms_timetable(P)
    if tt['slack'] < 0:
        fail('the timetable: the slowest crew calls the van at GO + %d s, the budget is GO + %d s' % (tt['call'], tt['latest']))
    log('  timetable: %d gates; the slowest crew (every room runs its %g s out) calls the van at GO + %d s (the no-enemy baseline of run W3: %g s), the budget is GO + %d s: slack %d s' % (
        tt['rooms'], ROOM_WAIT_S, tt['call'], NOAI_CALL, tt['latest'], tt['slack']))
    log('kl_fa_bank.rooms_check %s: %d gates, %d men in them, %d men started within %d of the line (%d said): %s' % (
        folder, len(gates), sum(r[6] for r in rows), len(near_line), ROOM_LINE_CLEAR, len(ROOM_STAY), 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


def stage_men(B, ex=None):
    """Every man of the level that can fire on the crew -> [dict(name, squad, group, stage, at)]: the kept campaign squads (stage by squad_stage) and, from extras.json's report `ex`, the waves' men at their posts
    (stage 'wave' + phase). The bots are not these."""
    sc, out = B.sc, []
    hunt = hunter_squads(sc)
    for t in sc.tops():
        st = squad_stage(sc, t)
        if not st:
            continue
        for k in range(t + 1, sc.end[t]):
            if sc.cls(k) == 'ZFFActor':
                out.append(dict(name='%s %s' % (sc.names[t].split('!')[-1], sc.path[sc.parent[k]].split(chr(92))[-1]), squad=sc.path[t][len(R):], group=sc.path[sc.parent[k]],
                                stage=st, at=B.at(k), hunter=sc.path[t][len(R):] in hunt))
    if STAGING:                                         # SECOND FIX (skeptic): a woken man WALKS to his Defend places (the vault lobby for the dock garrison): each defend place of a staged squad counts as a man from the wake event on
        for t in sc.tops():
            nm = sc.path[t][len(R):]
            if nm not in wake_map():
                continue
            for k in range(t + 1, sc.end[t]):
                if sc.cls(k) == 'ZBoxPrimitive' and 'DefendBehaviour' in sc.path[k]:
                    out.append(dict(name='%s %s' % (sc.names[t].split('!')[-1], sc.path[k].split(chr(92))[-1] + ' of ' + sc.path[sc.parent[k]].split(chr(92))[-1]), squad=nm,
                                    group=None, stage=squad_stage(sc, t), at=B.at(k), walker=True, hunter=nm in hunt))
    for w in (ex or {}).get('waves', ()):
        for j, (_e, q) in enumerate(w['men']):
            out.append(dict(name='%s_%d' % (w['name'], j + 1), squad=w['name'], group=None, stage='wave' + w['phase'], at=tuple(float(v) for v in q)))
    return out


WAKE_BUILT = None                       # {squad: event} as the FOLDER under test was built (extras.json 'staged' routs), set by pressure_check / start_guns; None = the module's WAKE_SQUADS


def wake_map():
    return WAKE_SQUADS if WAKE_BUILT is None else WAKE_BUILT


def set_wake_built(ex):
    """Take the staging of a finished folder from its extras.json report (so that a check run on an OLDER folder, c_bank7's, measures what that folder has and not what the module would build now)."""
    global WAKE_BUILT
    WAKE_BUILT = None
    if not ex or not ex.get('staged'):
        return
    WAKE_BUILT = collections.OrderedDict()
    for ev, spec in ex['staged'].items():
        for x in spec['routs']:
            WAKE_BUILT[x[len(R):].rsplit(chr(92), 1)[0]] = ev


def man_from(m):
    """The time index (the plan's station index; a stretch j -> j + 1 is j .. j + 1) from which man m is in the world: the event of WAKE_SQUADS (STAGING) or his stage's T_FROM."""
    if STAGING and m['squad'] in wake_map():
        return EVENT_T[wake_map()[m['squad']]]
    return T_FROM[m['stage']]


def pressure_rows(B, P, S, men, log=None, step=300.0, hunters=False):
    """The guns table of plan P on built level B: for every station i (the seven bots' places there) and every stretch i -> i + 1 (the mesh path of each bot sampled every `step`) the men awake at that time
    (man_from) with a free EXACT ray (hvk_ray, Sight.sees_by 'exact') from their eyes to a place's chest or head, within HOLD_GUN_RANGE * 1.5 = 60 m on its floor (HOLD_GUN_DY). The beat's police count at their
    posts only until BEAT_GONE_T. hunters=True: the men of hunter squads count at the points of their way towards each place too (HUNT_REACH). -> [dict(i, kind, what, at, hold = [guns on each of the seven], hold_worst, who_hold, leg_worst, leg_at, leg_who)]"""
    import kl_fa_bots as F
    import kl_fa_bots_rt as RT
    nav = F.Nav(B.scene.nav)
    st, bots = P['stations'], list(P['bots'])
    rng = HOLD_GUN_RANGE * 1.5

    def bear(p, t):
        out = []
        for m in men:
            if man_from(m) > t + 1e-9 or (m['stage'] == 'beat' and t > BEAT_GONE_T):
                continue
            if man_bears(S, nav if hunters else None, m, p, rng):
                out.append(m)
        return out
    rows = []
    for j, s in enumerate(st):
        hs = [tuple(P['bots'][n]['places'][j][:3]) for n in bots]
        cnt = [bear(h, float(j)) for h in hs]
        row = dict(i=j, kind=s['kind'], what=(s.get('what') or '')[:44], at=tuple(round(v) for v in hs[0]), hold=[len(c) for c in cnt], hold_worst=max(len(c) for c in cnt),
                   who_hold=sorted({m['name'] for c in cnt for m in c}))
        if j + 1 < len(st):
            seen, worst = set(), (0, None, [])
            for n in bots:
                got = RT.way_samples(nav, tuple(P['bots'][n]['places'][j]), tuple(P['bots'][n]['places'][j + 1]), step)
                ss = got[0] if got else []
                for q_i, q in enumerate(ss):
                    key = (round(q[0] / 100), round(q[1] / 100), round(q[2] / 100))
                    if key in seen:
                        continue
                    seen.add(key)
                    c = bear(q[:3], j + (q_i + 0.5) / (len(ss) + 1.0))
                    if len(c) > worst[0]:
                        worst = (len(c), tuple(round(v) for v in q[:3]), c)
            row.update(leg_worst=worst[0], leg_at=worst[1], leg_who=sorted(m['name'] for m in worst[2]))
        rows.append(row)
        if log:
            log('    %2d %-5s %-44s %s holds %s worst %d | leg to %d: %s at %s' % (j, row['kind'], row['what'], row['at'], row['hold'], row['hold_worst'], j + 1, row.get('leg_worst'), row.get('leg_at')))
    return rows


def pressure_check(folder, log=print):
    """'kl_fa_bank.py pressure-check <folder>': the guns table (pressure_rows) of a finished folder with its gates, and the START rows at GO / + 11 / + 30 / + 60 s. FAILS a station above HOLD_GUNS or a stretch above
    LEG_GUNS on the way IN (up to the loot) unless WAKE_KNOWN lists it with its number; the way out and the square are said, and listed as known where WAKE_KNOWN has them. -> list of faults"""
    import json
    import kl_fa_bots as F
    bad = []
    try:
        P = json.load(open(os.path.join(folder, 'bots.json'), encoding='utf-8')).get('plan') or {}
    except (OSError, ValueError):
        P = {}
    if not P.get('vault_gates'):
        log('  pressure: bots.json has no room gates: not checked')
        return bad
    o = read_opts(folder)
    B = F.Built(folder)
    S = Sight(folder, B, lambda *a: None)
    pj = os.path.join(folder, 'extras.json')
    ex = json.load(open(pj)) if os.path.isfile(pj) else None
    set_wake_built(ex)
    men = stage_men(B, ex)
    log('  pressure: %d men (%s); STAGING %s' % (len(men), ', '.join('%s %d' % (k, v) for k, v in collections.Counter(m['stage'] for m in men).items()), 'on' if STAGING else 'off'))
    sp = start_pressure(S, start_men(B, ex, bool(o.get('waves2'))), times=(0.0, 11.0, 30.0, 60.0), rules=('exact',), nav=F.Nav(B.scene.nav))
    for T, r in sp.items():
        log('  START rows, GO + %3.0f s: %2d men in the world, %d with a clear exact ray within %d m%s' % (T, r['in_world'], len(r['bear']['exact']), PRESSURE_RANGE / 100,
                                                                                                           ': ' + ' '.join(r['bear']['exact'])[:160] if r['bear']['exact'] else ''))
        if r['bear']['exact'] and STAGING:
            bad.append('START rows: %d guns (hunters counted) at GO + %g s: %s' % (len(r['bear']['exact']), T, ' '.join(r['bear']['exact'])[:120]))
            log('  FAIL ' + bad[-1])
    rows = pressure_rows(B, P, S, men, log)
    # HUNTERS on the stations and stretches: SAID, not failed (the yardstick of 3 / 4 was measured on men who stand; a hunter who may walk 25 m towards every place makes it unreachable for any map with a squad awake).
    # The START rows above are the rule that fails (runs W7 / W8).
    rows_h = pressure_rows(B, P, S, men, None, hunters=True)
    worse = ['%d:%s %d>%d' % (h['i'], 'hold' if h['hold_worst'] > r_['hold_worst'] else 'leg', max(h['hold_worst'], h.get('leg_worst') or 0), max(r_['hold_worst'], r_.get('leg_worst') or 0))
             for r_, h in zip(rows, rows_h) if h['hold_worst'] > r_['hold_worst'] or (h.get('leg_worst') or 0) > (r_.get('leg_worst') or 0)]
    log('  HUNTERS (reach %d m, said only): %s' % (HUNT_REACH / 100, ', '.join(worse) if worse else 'no station or stretch gains a gun'))
    i_loot = max(i for i, s in enumerate(P['stations']) if s['kind'] == 'loot')
    base_out = way_out_base(rows)
    for r in rows:
        for kind, n, cap in (('hold', r['hold_worst'], HOLD_GUNS), ('leg', r.get('leg_worst') or 0, LEG_GUNS)):
            if n <= cap:
                continue
            known = WAKE_KNOWN.get((kind, r['i']))
            way_in = r['i'] < i_loot if kind == 'leg' else r['i'] <= i_loot
            if known and n <= known[0]:
                log('      KNOWN %s %d: %d guns (%d wanted; %s)' % (kind, r['i'], n, cap, known[1]))
            elif STAGING and way_in:
                bad.append('%s %d (%s): %d guns bear (%d wanted)' % (kind, r['i'], r['what'].strip(), n, cap))
                log('  FAIL ' + bad[-1])
            elif GARRISON and not way_in and (kind, r['i']) in base_out and n > base_out[(kind, r['i'])]:
                bad.append('%s %d (way out): %d guns bear, more than c_bank8 had (%d) (SECOND FIX, skeptic: a garrison that rises the way-out fire is no cure)' % (kind, r['i'], n, base_out[(kind, r['i'])]))
                log('  FAIL ' + bad[-1])
            else:
                log('      OVER %s %d: %d guns (%d wanted)%s' % (kind, r['i'], n, cap, '' if way_in else ' - not the way in'))
    log('kl_fa_bank.pressure_check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


def dyn_check(folder, log=print):
    """'kl_fa_bank.py dyn-check <folder>': kl_fa_bots_dyn.check on a finished folder. With STAGING the gates' TriggerActorsDead lists name the relays Wake_<event> besides the chain's next step, which that checker
    (not this module's) does not know as a side item of a chain link; the check is run on the scene as it was before the staging step - the relay names are taken out of those lists IN MEMORY (F.Built is
    wrapped for the length of the call, nothing is written) - and stage-check proves the relays. -> list of faults"""
    import kl_fa_bots as F
    import kl_fa_bots_dyn as D
    read_opts(folder)
    orig = F.Built
    taken = []

    class Stripped(orig):
        def __init__(self, *a, **k):
            orig.__init__(self, *a, **k)
            if not STAGING:
                return
            sc = self.sc
            for k_, i_, v_ in list(kl_fa.controllers(sc, 'TriggerActorsDead')):
                keep = [x for x in v_[2] if not x.lower().startswith((R + CLOCK + '\\Wake_').lower())]
                if len(keep) != len(v_[2]):
                    taken.append(sc.names[k_])
                    kl_fa.edit(sc, k_, i_, lambda us, keep=keep, sc=sc: us.__setitem__(2, kl_fa._refs(sc, keep)))
    F.Built = Stripped
    try:
        out, _facts = D.check(folder, log)
    finally:
        F.Built = orig
    bad = [t for sev, t in out if sev == 'FAIL']
    if taken:
        log('  dyn-check: the relay names of %d gate lists (STAGING) were left out of the scene the checker saw (stage-check proves them)' % (len(taken) // 2 or len(taken)))
    log('kl_fa_bank.dyn_check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


def staging_check(folder, log=print):
    """'kl_fa_bank.py stage-check <folder>': a build with STAGING: every squad of WAKE_SQUADS is parked (field 3 = 0) and its start rout is named by NOTHING but its event's relay Wake_<event> (not by the start
    timer); the relay is named by the backstop timer (which the start timer starts), by the box (the beat box for 'ante') and, where an event has a gate, by that gate's TriggerActorsDead in each of the seven bots'
    squads; no man of an event's squads has an exact line to the box's floor (a 3 m lattice) or to the seven holds of the gate that wakes him; the backstop comes after the nominal arrival.
    -> list of faults"""
    import json
    import kl_fa_bots as F
    bad = []

    def fail(s):
        bad.append(s)
        log('  FAIL ' + s)
    read_opts(folder)
    if not STAGING:
        log('  stage: no staging in this build: nothing to check')
        return bad
    P = json.load(open(os.path.join(folder, 'bots.json'), encoding='utf-8')).get('plan') or {}
    B = F.Built(folder)
    sc = B.sc
    S = Sight(folder, B, lambda *a: None)
    nav = F.Nav(B.scene.nav)
    cp = lambda n: R + CLOCK + '\\' + n
    nxt = {}
    for cn, fld in (('TriggerDelay2', 4), ('TriggerBox', 17), ('TriggerActorsDead', 2)):
        for k, _i, v in kl_fa.controllers(sc, cn):
            nxt.setdefault(k, []).extend(s.lower() for s in v[fld])
    named_by = collections.defaultdict(list)
    for k, names in nxt.items():
        for s in names:
            named_by[s].append(k)
    tops = [t for t in sc.tops() if sc.names[t].startswith(BOT_SQUAD + 'Squad#')]
    gates = {g['name']: g['wait'] for g in P['vault_gates']}
    sq_node = {sc.path[t][len(R):]: t for t in sc.tops()}
    men = stage_men(B)
    start_k = sc.resolve(R + ROLE['start timer'])[0]
    for ev, spec in WAKE_EVENTS.items():
        squads = [s for s, e in WAKE_SQUADS.items() if e == ev]
        found = sc.resolve(cp('Wake_' + ev))
        if len(found) != 1:
            fail('%s: no relay Wake_%s' % (ev, ev))
            continue
        wk = found[0]
        listed = nxt.get(wk, [])
        for sq in squads:
            t = sq_node.get(sq)
            if t is None:
                fail('%s: squad %s is not in the level' % (ev, sq))
                continue
            if values(sc, t, 'ZSquadScript')[SQUAD_ACTIVE] != 0:
                fail('%s: %s is not parked (ZSquadScript field %d is %r)' % (ev, sq, SQUAD_ACTIVE, values(sc, t, 'ZSquadScript')[SQUAD_ACTIVE]))
            routs = [s for s in listed if s.startswith((R + sq + '\\').lower())]
            if len(routs) != 1:
                fail('%s: the relay names %d routs of %s (1 wanted)' % (ev, len(routs), sq))
                continue
            by = [k for k in named_by.get(routs[0], [])]
            if by != [wk]:
                fail('%s: the rout of %s is named by %s, by the relay only wanted' % (ev, sq, [sc.names[b] for b in by]))
        by = named_by.get(sc.path[wk].lower(), [])
        timer = [k for k in by if sc.names[k] == 'Timer_wake_' + ev]
        box = [k for k in by if sc.names[k] == 'Box_wake_' + ev] if spec['box'] else [k for k in by if sc.path[k] == R + ROLE['beat box']]
        if len(timer) != 1:
            fail('%s: %d backstop timer(s) name the relay' % (ev, len(timer)))
        elif sc.path[timer[0]].lower() not in nxt.get(start_k, []):
            fail('%s: the backstop timer is not started by the start timer' % ev)
        if len(box) != 1:
            fail('%s: %d box(es) name the relay (the %s)' % (ev, len(box), 'box of its own' if spec['box'] else 'beat box'))
        if spec['gate']:
            tad = [k for k in by if sc.path[k][len(R):].startswith(BOT_SQUAD) and sc.names[k] == gates[spec['gate']]]
            if len(tad) != len(tops):
                fail('%s: %d of the %d bots\' TriggerActorsDead %s name the relay' % (ev, len(tad), len(tops), gates[spec['gate']]))
        if spec['go'] < {'lobby': 40.0, 'flights': 70.0, 'ante': 110.0}[ev]:
            fail('%s: the backstop at GO + %g s is before the nominal arrival' % (ev, spec['go']))
        if spec['go'] > rooms_timetable(P)['latest']:
            fail('%s: the backstop at GO + %g s is after the van-call budget (GO + %g s)' % (ev, spec['go'], rooms_timetable(P)['latest']))
        # nobody woken sees the criminals who wake him: the box's floor on a 3 m lattice (the beat box: the ante-room hold), the seven holds of the gate that names the relay
        pts = []
        if spec['box']:
            (cx, cy, cz), (hx, _hy, hz) = spec['box']
            x = cx - hx
            while x <= cx + hx:
                z = cz - hz
                while z <= cz + hz:
                    h = nav.at(x, cy, z, dy=60.0)
                    if h:
                        pts.append((x, h[1], z))
                    z += 300.0
                x += 300.0
        else:
            pts += [tuple(P['bots'][n]['places'][P['gate']['station']][:3]) for n in P['bots']]
        if spec['gate']:
            gi = [g['name'] for g in P['vault_gates']].index(spec['gate'])
            hold_st = [i for i, s in enumerate(P['stations']) if s['kind'] == 'hold'][gi]
            pts += [tuple(P['bots'][n]['places'][hold_st][:3]) for n in P['bots']]
        seen = []
        for m in men:
            if m['squad'] in squads and not m.get('walker'):
                for p in pts:
                    if abs(m['at'][1] - p[1]) < HOLD_GUN_DY and math.dist(m['at'], p) <= HOLD_GUN_RANGE * 1.5 and S.sees_by(m['at'], p, ('exact',)):
                        seen.append((m['name'], tuple(round(c) for c in p)))
                        break
        if seen:
            fail('%s: %d man/men would appear in sight of the criminals who wake them: %s' % (ev, len(seen), seen[:4]))
        log('  wake %-8s %d squads (%d men) by %s + %s, the backstop at GO + %g s; %d lattice points checked' % (
            ev, len(squads), sum(1 for m in men if m['squad'] in squads and not m.get('walker')), ('the gate ' + spec['gate']) if spec['gate'] else 'no gate (' + ('the dock gate is off' if ev == 'lobby' else 'the box and the backstop only') + ')',
            ('the box %s' % (spec['box'][0],)) if spec['box'] else 'the beat box', spec['go'], len(pts)))
    log('kl_fa_bank.stage_check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


def P_steps_index(P, name):
    return next(i for i, s in enumerate(P['steps']) if s['name'] == name)


# ------------------------------------------------------------------ the crew fix after run V2: the bots' side
def dash_chain(sc, v, delay, rout):
    """The hold timers a Defend step (values v) starts: those its own list names, and - the review's fault 3 - those the cover
    branch of that list starts one or two steps on (step -> [RandomTrigger '..._cover' ->] a '_pos_cover' Defend rout -> its hold
    timer: Squad#02 / #03 / #04 051_Timer_hold kept 4 - 6 s at the hall's north end; MEASURED on the second round's folder: the
    step names the '_pos_cover' rout DIRECTLY, which the first form of this function did not follow). -> [node], without repeats."""
    out, seen = [], set()
    def walk(vals, depth):
        for s in (vals[7] or []):
            for j in sc.resolve(s):
                if j in delay and DASH_HOLD in sc.names[j]:
                    out.append(j)
                elif depth < 3 and '_cover' in sc.names[j] and j not in seen:
                    seen.add(j)
                    if j in rout:                                   # the step names a '_pos_cover' Defend rout directly (second round, Squad#02 / #03 / #04)
                        walk(rout[j], depth + 1)
                    elif kl_fa.has(sc, j, 'RandomTrigger'):         # ... or through the RandomTrigger '..._cover'
                        for s1 in A.named(sc, j):
                            for h in sc.resolve(s1):
                                if h in rout and h not in seen:
                                    seen.add(h)
                                    walk(rout[h], depth + 1)
    walk(v, 0)
    return list(dict.fromkeys(out))


def hall_dash(folder, log=print):
    """In place, on a folder kl_fa_bots_dyn's step is through with (before seal): every DefendBehaviourRout of an AI
    heister squad that has a place inside DASH_BOX gets DASH_MOVE, and every TriggerDelay2 such a step starts whose
    name holds DASH_HOLD goes to 0 s (DASH_BOX's note). Values of existing controllers only: the .prp member alone
    changes, no entity is added or removed. A second run changes nothing. -> {'steps', 'timers', 'squads'}"""
    import kl_fa_bots as F
    read_opts(folder)
    hold = DASH_GAP if CREW_FIX2 else 0.0               # CREW_FIX2: a short real hold, not 0 s (DASH_GAP's note)
    B = F.Built(folder)
    sc = B.sc
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'dash')              # kl_fa_bots_dyn.fake_fix's way of a .prp-only edit
    if J.fingerprints(Jn)[0] != J.fingerprints(sc)[0] or J.text(Jn, Jn.p.settings) != J.text(sc, sc.p.settings) or Jn.path != sc.path:
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    delay = {k: (i, v[0]) for k, i, v in kl_fa.controllers(Jn, 'TriggerDelay2')}
    steps, timers, squads, was, cut = [], [], set(), collections.Counter(), []
    drout = {kk: vv for kk, _ii, vv in kl_fa.controllers(Jn, 'DefendBehaviourRout')}
    for k, i, v in kl_fa.controllers(Jn, 'DefendBehaviourRout'):
        t = Jn.top[k]
        if not Jn.names[t].startswith(BOT_SQUAD + 'Squad#'):
            continue
        if ROOM_GATES and Jn.names[k].split('_DefendBehaviour_out_')[-1] in {r['name'] for r in ROOMS} and '_DefendBehaviour_out_' in Jn.names[k]:
            continue                                    # a gate's hold step stays a walk to its cover: the gate decides WHEN the crew crosses, the dash HOW FAST (the steps behind it)
        at = [B.at(j) for s in (v[1] or []) for j in Jn.resolve(s)]
        # ... and the covers this step's hold is AT: a hold's timer is started by the step BEFORE the cover (the
        # step names [the timer, a RandomTrigger that draws one of the covers]; or [the cover], which names the timer)
        nxt = [j for s in (v[7] or []) for j in Jn.resolve(s)]
        drawn = [h for j in nxt if kl_fa.has(Jn, j, 'RandomTrigger') and '_cover' in Jn.names[j] for s in A.named(Jn, j) for h in Jn.resolve(s)]
        held = [B.at(c) for h in drawn if kl_fa.has(Jn, h, 'DefendBehaviourRout') for c in range(h + 1, Jn.end[h]) if Jn.parent[c] == h and Jn.names[c].startswith('Pos#')]
        mine = any(in_box(p, DASH_BOX) for p in at)
        if not mine and not any(in_box(p, DASH_BOX) for p in held):
            continue
        squads.add(Jn.names[t])
        if CREW_FIX2 and mine:
            hold_ = [j for s in (v[7] or []) for j in Jn.resolve(s) if j in delay and DASH_HOLD in Jn.names[j]]
            covers = [s for s in (v[7] or []) if any(kl_fa.has(Jn, j, 'RandomTrigger') and '_cover' in Jn.names[j] for j in Jn.resolve(s))]
            if DASH_CUT_COVER and hold_ and covers:
                keep_ = [s for s in v[7] if s not in covers]
                kl_fa.edit(Jn, k, i, lambda us: A.setv(Jn, us, 7, keep_))
                cut.append((Jn.path[k][5:], len(covers)))
        if mine and v[4] != DASH_MOVE:
            was[v[4]] += 1
            kl_fa.edit(Jn, k, i, lambda us: A.setv(Jn, us, 4, DASH_MOVE))
            steps.append(Jn.path[k][5:])
        if CREW_FIX2:
            js = dash_chain(Jn, v, delay, drout)
        else:
            js = [j for s in (v[7] or []) for j in Jn.resolve(s) if j in delay and DASH_HOLD in Jn.names[j]]
        for j in js:
            if delay[j][1] != hold:
                kl_fa.edit(Jn, j, delay[j][0], lambda us: A.setv(Jn, us, 0, hold))
                timers.append((Jn.path[j][5:], delay[j][1]))
                delay[j] = (delay[j][0], hold)
    if steps or timers or cut:
        prp = Jn.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
            raise ValueError('the new .prp does not round-trip')
        new = dict(B.files)
        new[B.ext['.prp']] = prp
        tmp = B.zp + '.tmp'
        kl_graft.write_zip(tmp, [(n, new[n]) for n in B.order])
        os.replace(tmp, B.zp)
    log('kl_fa_bank.hall_dash %s: %d Defend steps of %d AI heister squads with a place in the banking hall (x %d..%d, z %d..%d) now %s (they were %s); '
        '%d hold timers those steps start set to 0 s (they were %s s)' % (folder, len(steps), len(squads), *DASH_BOX[0], *DASH_BOX[2], DASH_MOVE,
        dict(was) or '-', len(timers), sorted({x for _p, x in timers}) or '-'))
    if CREW_FIX2:
        log('kl_fa_bank.hall_dash: CREW_FIX2: the cover branch is out of the next lists of %d dash steps (DASH_CUT_COVER %s), '
            'the hold timers are %g s, the box reaches z %g' % (len(cut), DASH_CUT_COVER, hold, DASH_BOX[2][1]))
    for p, x in timers:
        log('    %-90s %g s -> %g' % (p[-90:], x, hold))
    return {'steps': steps, 'timers': timers, 'squads': sorted(squads), 'cover_cut': cut}


def vault_blow(folder, log=print):
    """VAULT_BLOW's note. In place, on a finished folder of a map whose vault door is in place (not --vault-open, not --vault-stays):
    .prp values only - no entity is added, so no seal and no .prm change. (1) the beat's 'door' wrapper names nothing (the door is not
    swung), (2) 'door off' (DeactivateGeom) names the animated group, its body and the hinge piece, (3) the door timer - the moment of
    the three Explode and the blast sound - names 'door off', (4) the round-start Reset_show names the three again. Writes bank_opts.json
    with vault_blow. A second run changes nothing. -> {'door off': [...], 'changed': [...]}"""
    import kl_fa_bots as F
    read_opts(folder)
    global VAULT_BLOW
    B = F.Built(folder, os.path.basename(archive_of(folder)).split('_Main')[0])      # the slot of the folder (F01 / F07 ...)
    sc = B.sc
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'blow')
    if J.fingerprints(Jn)[0] != J.fingerprints(sc)[0] or J.text(Jn, Jn.p.settings) != J.text(sc, sc.p.settings) or Jn.path != sc.path:
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    pieces = [R + VAULT_DOOR, R + VAULT_BODY, R + VAULT_HINGE]
    for p in pieces:
        if not Jn.resolve(p):
            raise ValueError('vault_blow: %s is not in the level' % p)
    role = lambda r: Jn.resolve(R + ROLE[r])[0]
    changed = []
    def ctrl(k, name):
        return next((i, v) for kk, i, v in kl_fa.controllers(Jn, name) if kk == k)
    def set_list(role_, cname, field, new, what):
        k = role(role_)
        i, v = ctrl(k, cname)
        if list(v[field]) != list(new):
            kl_fa.edit(Jn, k, i, lambda us: A.setv(Jn, us, field, list(new)))
            changed.append('%s: %d -> %d names' % (what, len(v[field]), len(new)))
    set_list('door', 'AIDWrapper', 0, [], 'door wrapper (no swing)')
    set_list('door off', 'DeactivateGeom', 1, pieces, 'door off')
    k = role('door timer')
    i, v = ctrl(k, 'TriggerDelay2')
    if R + ROLE['door off'] not in v[4]:
        kl_fa.edit(Jn, k, i, lambda us: A.setv(Jn, us, 4, list(v[4]) + [R + ROLE['door off']]))
        changed.append('door timer names door off')
    rs = Jn.resolve(R + CLOCK + '\\Reset_show')
    if rs:
        i, v = ctrl(rs[0], 'ActivateGeom')
        add = [p for p in pieces if p not in v[1]]
        if add:
            kl_fa.edit(Jn, rs[0], i, lambda us: A.setv(Jn, us, 1, list(v[1]) + add))
            changed.append('Reset_show + %d' % len(add))
    if changed:
        prp = Jn.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
            raise ValueError('the new .prp does not round-trip')
        new = dict(B.files)
        new[B.ext['.prp']] = prp
        tmp = B.zp + '.tmp'
        kl_graft.write_zip(tmp, [(n, new[n]) for n in B.order])
        os.replace(tmp, B.zp)
    VAULT_BLOW = True
    import json                                         # merge into the file: apply_opts does not restore plaza_outside / hall_up, so write_opts would reset them
    fp = os.path.join(folder, OPTS_FILE)
    o = json.load(open(fp)) if os.path.isfile(fp) else {}
    o['vault_blow'] = True
    with open(fp, 'w') as f:
        json.dump(o, f, indent=1)
    log('kl_fa_bank.vault_blow %s: %s' % (folder, '; '.join(changed) or 'nothing to change'))
    return {'door off': pieces, 'changed': changed}


# WAVE_FALLBACK ('wave-fallback <src> <dst>', a .prp-only post-step; bank_opts.json 'wave_fallback'): the audit of 2026-10-18 (cops, escape-phase
# pressure) found that waves B and D start only from boxes (the ante-room box for B, the hall's south-end box for D). A crew that leaves another way, or
# never gets there (a quiet round, a slow human, a downed crew), meets no push at all. The fallback names Pace_B01 and Pace_D01 from a node that runs on
# the ROUND CLOCK. No node is added (a new entity would change the .gms / .buf / .oct / .rmi / .rmc and every slot id): the node is the Go of the chain-A
# link whose WORST-case time (round-start event + start timer + Timer_A_late backstop + the Pace gaps up to it) is nearest WAVE_FALLBACK_S. In the
# installed Vault (waves2: Pace_A01 30 s, then 45 s a link, Timer_A_late 80 s, start timer 10 s) the four links fall at event + 120 / 165 / 210 / 255 s in
# the worst case (crew never passes the dock box), earlier by the time the crew needs to reach the box otherwise: Go_A04 is chosen.
# Pace and Go are one-shots (re-arm -1): whichever of the box and the fallback arrives FIRST starts the chain, the other is a no-op (a re-trigger of a
# Pace that is still counting down is the one case not seen: GUESS that it is ignored or restarts the same wait, which delays that one wave by <= its gap).
WAVE_FALLBACK_S = 240.0         # GUESS: s after the round-start event by which a quiet round still gets waves B and D (the first round is 360 s long; the van is called 60 s before its end)
WAVE_FALLBACK_MAX = 300.0       # the chosen link may not fall later than this in the worst case, else the push comes too late to matter (refused)


def wave_fallback(src, dst=None, log=print, target=None):
    """Names Pace_B01 and Pace_D01 from the Go node of a chain-A link (see WAVE_FALLBACK) in a finished waves build. dst: the folder to build (a copy of src
    with ONE member changed: the .prp); None = in place. Writes bank_opts.json 'wave_fallback'. A second run changes nothing.
    -> {'go': path, 'worst_s': float, 'changed': [..]}"""
    import json, shutil, kl_fa_bots as F
    target = WAVE_FALLBACK_S if target is None else target
    if dst:
        if os.path.exists(dst):
            raise ValueError('wave_fallback: %s exists' % dst)
        shutil.copytree(src, dst)
    folder = dst or src
    o = read_opts(folder)
    if not o.get('waves'):
        raise ValueError('wave_fallback: %s has no waves build (bank_opts.json waves)' % folder)
    B = F.Built(folder, os.path.basename(archive_of(folder)).split('_Main')[0])
    sc = B.sc
    Jn = sc                    # edited in place: B.sc.p.serialize() reproduces the stored .prp byte for byte (J.join does not: it renumbers controller ids)
    cl = R + CLOCK + '\\'
    def td(name):
        k = Jn.resolve(cl + name)
        return (k[0], values(Jn, k[0], 'TriggerDelay2')) if k else (None, None)
    for need in ('Pace_B01', 'Pace_D01', 'Pace_A01'):
        if td(need)[0] is None:
            raise ValueError('wave_fallback: %s is not in the level' % need)
    st = values(Jn, Jn.resolve(R + ROLE['start timer'])[0], 'TriggerDelay2')[0]
    late = td('Timer_A_late')[1]
    t = st + (late[0] if late is not None and o.get('waves2') else 0.0)       # worst case: Pace_A01 is armed by the backstop
    links = []
    for i in range(1, 100):
        nm = 'A%02d' % i
        pk, pv = td('Pace_' + nm)
        gk, gv = td('Go_' + nm)
        if pk is None or gk is None:
            break
        t += pv[0] + gv[0]
        links.append((abs(t - target), -t, nm, t))
    if not links:
        raise ValueError('wave_fallback: no chain-A link')
    _d, _nt, nm, worst = min(links)
    if worst > WAVE_FALLBACK_MAX:
        raise ValueError('wave_fallback: the nearest link %s falls at event + %.0f s in the worst case (> %.0f)' % (nm, worst, WAVE_FALLBACK_MAX))
    gk, gv = td('Go_' + nm)
    want = [cl + 'Pace_B01', cl + 'Pace_D01']
    if o.get('van_nests') == 'off':           # VAN_NESTS 'off' (van_nests() below): chain D stays out of the fallback too. Without the option this line changes nothing
        want = want[:1]
    changed = []
    add = [x for x in want if x not in gv[4]]
    if add:
        kl_fa.edit(Jn, gk, A.ctrl_of(Jn, gk, 'TriggerDelay2'), lambda us: A.setv(Jn, us, 4, list(gv[4]) + add))
        changed.append('Go_%s names %s' % (nm, ', '.join(x.rsplit('\\', 1)[-1] for x in add)))
        prp = Jn.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
            raise ValueError('the new .prp does not round-trip')
        new = dict(B.files)
        new[B.ext['.prp']] = prp
        tmp = B.zp + '.tmp'
        kl_graft.write_zip(tmp, [(n, new[n]) for n in B.order])
        os.replace(tmp, B.zp)
    fp = os.path.join(folder, OPTS_FILE)               # merged into the file (vault_blow's way): the module's own flags and opts_now() stay as they were
    d = json.load(open(fp)) if os.path.isfile(fp) else {}
    d['wave_fallback'] = {'go': cl + 'Go_' + nm, 'worst_s': round(worst, 1), 'target_s': target}
    with open(fp, 'w') as f:
        json.dump(d, f, indent=1)
    log('kl_fa_bank.wave_fallback %s: %s (worst case event + %.1f s, target %.0f s, GUESS)' % (folder, '; '.join(changed) or 'nothing to change', worst, target))
    return {'go': cl + 'Go_' + nm, 'worst_s': worst, 'changed': changed}


# VAN_NESTS ('van-nests <src> <dst> off|keep=N'; a .prp-values-only post-step; bank_opts.json 'van_nests'; default: not run, the output of every other step is unchanged).
# Live run L19 (vault_e7, 2026-10-18 04:14..04:19): only the player escaped; the four loyal bots, called to the van at the boarding place (627, 822, -11233),
# went down and died 9..27 m from it. The 'nests' that stand in stacks of 3 at (-1500..-1600, 700, -9380..-9480) and (2100..2200, 700, -9420..-9480) are the ENTRY
# places of chain D (E_RECESS_L / E_RECESS_R): Gameplay!bank_waves!Wave_D01..D08 / Wave_Dnn_0m / Ground, 3 men a wave, ZSquadScript parked until Go_Dnn names the wave's
# 10_Defend. Chain D starts from the plaza box (tbExitFinancialAlley, list 17: the crew's exit from the hall) 3 s after it fires, then one wave every 25 s, and
# (wave_fallback) from Go_A04 at the round clock's ~255 s. The census of L19 shows D01 leaving its nest 3 s after the box and D02 25 s later, both walking
# (-1560, -9440) -> (67, -10921) / (595, 800, -8948): onto the route of the crew's walk to the van; D05..D08 still sat at their nests at the end (dormant:
# they never shot). The stock street squads (5_Lobby / COOP, slots 9051..9152, also at the recess) were already dead by then (census 04:18:27: 0 of 20).
# Positions of entities cannot be moved by values alone (the .gms record and .prp ZGEOM are kept equal), so the static, values-only answer is to not start the
# chain, or to start fewer waves: 'off' = no Pace_D01 in the plaza box's list and none in the fallback's Go node (the stock street squads the box starts are untouched);
# 'keep=N' = the first N waves (3 men each) only: Go_DN no longer names Pace_D(N+1). GUESS: that nothing else starts a Wave_D*; that fewer waves is what the van phase needs.
# A run-time answer (switch the nests off once the van is called) needs a node the .prp has no form for: not done.
VAN_NESTS = None


def van_nests(src, dst=None, mode='off', log=print):
    """Chain D (the plaza police waves D01..D08 that stand at the street recess) in a finished waves build: mode 'off' = never started, 'keep=N' = only the first N
    waves (N >= 1). dst: the folder to build (a copy of src with ONE member changed: the .prp); None = in place. Writes bank_opts.json 'van_nests'. A second run changes nothing.
    -> {'mode': ..., 'changed': [..]}"""
    import json, shutil, kl_fa_bots as F
    if mode != 'off' and not (isinstance(mode, str) and mode.startswith('keep=') and mode[5:].isdigit() and int(mode[5:]) >= 1):
        raise ValueError("van_nests: mode is 'off' or 'keep=N' (N >= 1), not %r" % (mode,))
    if dst:
        if os.path.exists(dst):
            raise ValueError('van_nests: %s exists' % dst)
        shutil.copytree(src, dst)
    folder = dst or src
    o = read_opts(folder)
    if not o.get('waves'):
        raise ValueError('van_nests: %s has no waves build (bank_opts.json waves)' % folder)
    B = F.Built(folder, os.path.basename(archive_of(folder)).split('_Main')[0])
    Jn = B.sc                    # edited in place, as wave_fallback does
    cl = R + CLOCK + '\\'
    links = 0
    while Jn.resolve(cl + 'Go_D%02d' % (links + 1)) and Jn.resolve(cl + 'Pace_D%02d' % (links + 1)):
        links += 1
    if not links:
        raise ValueError('van_nests: no chain-D link in %s' % folder)
    keep = 0 if mode == 'off' else int(mode[5:])
    if keep >= links:
        raise ValueError('van_nests: keep=%d of %d waves is not a cut' % (keep, links))
    changed = []
    def cut(k, cname, field, name):
        for kk, i, v in kl_fa.controllers(Jn, cname):
            if kk == k and name in v[field]:
                kl_fa.edit(Jn, k, i, lambda us: A.setv(Jn, us, field, [x for x in v[field] if x != name]))
                changed.append('%s no longer names %s' % (Jn.path[k][5:], name.rsplit('\\', 1)[-1]))
    if keep == 0:
        first = cl + 'Pace_D01'
        box = Jn.resolve(R + PLAZA_BOX)
        if not box:
            raise ValueError('van_nests: %s is not in the level' % PLAZA_BOX)
        cut(box[0], 'TriggerBox', 17, first)
        for k, _i, _v in kl_fa.controllers(Jn, 'TriggerDelay2'):
            if Jn.names[k].startswith('Go_') and not Jn.names[k].startswith('Go_D'):
                cut(k, 'TriggerDelay2', 4, first)
    else:
        cut(Jn.resolve(cl + 'Go_D%02d' % keep)[0], 'TriggerDelay2', 4, cl + 'Pace_D%02d' % (keep + 1))
    left = []                    # nothing else may start a chain-D wave
    for cname, field in (('TriggerBox', 17), ('TriggerDelay2', 4)):
        for k, _i, v in kl_fa.controllers(Jn, cname):
            if not Jn.names[k].startswith(('Go_D', 'Pace_D')):
                left += [(Jn.path[k][5:], x) for x in v[field] if '\\Pace_D' in x or '\\Wave_D' in x]
    if keep == 0 and left:
        raise ValueError('van_nests: still named from outside the chain: %s' % left)
    if changed:
        prp = Jn.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
            raise ValueError('the new .prp does not round-trip')
        new = dict(B.files)
        new[B.ext['.prp']] = prp
        tmp = B.zp + '.tmp'
        kl_graft.write_zip(tmp, [(n, new[n]) for n in B.order])
        os.replace(tmp, B.zp)
    fp = os.path.join(folder, OPTS_FILE)
    d = json.load(open(fp)) if os.path.isfile(fp) else {}
    d['van_nests'] = mode
    with open(fp, 'w') as f:
        json.dump(d, f, indent=1)
    log('kl_fa_bank.van_nests %s: %s (chain D: %d waves of 3 men; %s)' % (folder, '; '.join(changed) or 'nothing to change', links,
        'none starts' if keep == 0 else 'the first %d start' % keep))
    return {'mode': mode, 'changed': changed}


# VAN_QUIET ('van-quiet <src> <dst> <group,group,...>|top'; a .prp-values-only post-step; bank_opts.json 'van_quiet'; default: not run, every other step's output is unchanged).
# The audit of 2026-10-18 (L19, vault_e7; van-nests 'off' = vault_e8 cut only chain D) named more police on the van route than chain D. Same method as van_nests:
# the group's entry is unlinked from every TriggerBox list (17) / TriggerDelay2 list (4) that names it, so nothing wakes it. No entity moves, no node is added.
#   plaza  : the 7 plaza-box squad entries (5_Lobby Teargas_01 / OutSide_01, COOP SWAT_02 / SWAT_03 / both ShieldSupport / Reinforce_Wave1_COOP_03; ~21 men),
#            cut from tbExitFinancialAlley. The box's Timer_van and Timer_teller_c stay. The squads' own inner links stay (they run only if the squad is awake).
#   waveb  : Pace_B01 (Wave_B01..B04, 4 men), cut from tb_LEFT_TheySpotYou and Go_A04 (the wave_fallback link).
#   wavea4 : Pace_A04 (Wave_A04, 1 man), cut from Go_A03, its only starter (2026-10-18, L24 census: it woke 04:49:04 and stood 10 m from rec 1 at its death;
#            GUESS: a killer). Go_A04 then never fires, so the wave_fallback link to Pace_B01 dies with it. A01..A03 stay (waves_check's supply). Not in 'top'.
#   exit   : the 3 FinancialAlleyExit squads (8 men, y 1221), cut from RivalMercVan\TimerVanGo. The audit rates them low (floor above the route): not in 'top'.
# 'top' = plaza + waveb (audit ranks 1 and 2). NOT offered: Wave_A (chain A is the supply that waves_check demands), the vault garrison (dead by the van call, GUESS),
# traitor Squad #03 (starter not traced).
# GUESS: that the plaza squads and Wave_B were the main killers of the called bots (the audit attributes only point-blank steps within 1.6 m; most kills were unattributed).
# GUESS: that nothing else wakes these squads (only TriggerBox / TriggerDelay2 lists are scanned; any other starter shows as a remaining name and is refused).
# Side effect, by design: the plaza stays empty of its stock police for the WHOLE round, not only the van phase (a run-time switch has no .prp form).
VAN_QUIET_GROUPS = {
    'plaza': ['gameplay!5_lobby!police_outside_teargas_01\\30_flankingbehaviour', 'gameplay!5_lobby!police_outside_01\\30_flankingbehaviour',
              'coop!squads_lobby!police_outside_swat_03_shieldsupport\\050_move_in_01', 'coop!squads_lobby!police_outside_swat_02_shieldsupport\\050_move_in_01',
              'coop!squads_lobby!police_reinforce_wave1_coop_03\\cutscene_moveoutside', 'coop!squads_lobby!police_outside_swat_03\\flankingbehaviour',
              'coop!squads_lobby!police_outside_swat_02\\flankingbehaviour'],
    'waveb': ['gameplay!bank_waves!clock\\pace_b01'],
    'wavea4': ['gameplay!bank_waves!clock\\pace_a04'],
    'exit': ['gameplay!030_afterloot!030_financialalleyexit_left\\10_runtocover', 'gameplay!030_afterloot!030_financialalleyexit_right\\10_runtocover',
             'gameplay!030_afterloot!030_financialalleyexitstreet_left\\10_runtocover'],
}
VAN_QUIET_TOP = ('plaza', 'waveb')


def van_quiet(src, dst=None, groups='top', log=print):
    """Unlinks the named threat groups (VAN_QUIET_GROUPS keys, comma separated, or 'top') from their starters in a finished waves build. dst: the folder to build (a
    copy of src with ONE member changed: the .prp); None = in place. Writes bank_opts.json 'van_quiet' (sorted list). A second run changes nothing.
    -> {'groups': [..], 'changed': [..]}"""
    import json, shutil, kl_fa_bots as F
    want = list(VAN_QUIET_TOP) if groups == 'top' else [g for g in groups.split(',') if g]
    if not want or any(g not in VAN_QUIET_GROUPS for g in want):
        raise ValueError("van_quiet: groups are %s or 'top', not %r" % (sorted(VAN_QUIET_GROUPS), groups))
    want = sorted(set(want))
    if dst:
        if os.path.exists(dst):
            raise ValueError('van_quiet: %s exists' % dst)
        shutil.copytree(src, dst)
    folder = dst or src
    o = read_opts(folder)
    if not o.get('waves'):
        raise ValueError('van_quiet: %s has no waves build (bank_opts.json waves)' % folder)
    B = F.Built(folder, os.path.basename(archive_of(folder)).split('_Main')[0])
    Jn = B.sc                    # edited in place, as van_nests does
    targets = {(R + t).lower(): g for g in want for t in VAN_QUIET_GROUPS[g]}
    changed, seen = [], set()
    for cname, field in (('TriggerBox', 17), ('TriggerDelay2', 4)):
        for k, i, v in kl_fa.controllers(Jn, cname):
            gone = [x for x in v[field] if x.lower() in targets]
            if gone:
                kl_fa.edit(Jn, k, i, lambda us: A.setv(Jn, us, field, [x for x in v[field] if x.lower() not in targets]))
                seen.update(x.lower() for x in gone)
                changed.append('%s no longer names %s' % (Jn.path[k][5:], ', '.join(x.rsplit('\\', 1)[-1] if x.lower().endswith(('pace_b01',)) else x[5:].split('!')[-1] for x in gone)))
    left = []                    # nothing else may still name a cut entry (reference lists of any class; the squads' own inner links are not starters)
    for k in range(1, len(Jn.nodes)):
        for s_ in A.named(Jn, k):
            if s_.lower() in targets and Jn.cls(k) != 'ZGROUP':        # a squad group naming its own sibling is an inner link, not a starter (GUESS: it runs only once the squad is awake)
                left.append((Jn.path[k][5:], s_[5:]))
    if left:
        raise ValueError('van_quiet: still named by %s' % left)
    if changed:
        prp = Jn.p.serialize()
        back = F.Prp(prp)
        if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
            raise ValueError('the new .prp does not round-trip')
        new = dict(B.files)
        new[B.ext['.prp']] = prp
        tmp = B.zp + '.tmp'
        kl_graft.write_zip(tmp, [(n, new[n]) for n in B.order])
        os.replace(tmp, B.zp)
    fp = os.path.join(folder, OPTS_FILE)
    d = json.load(open(fp)) if os.path.isfile(fp) else {}
    d['van_quiet'] = sorted(set(d.get('van_quiet', [])) | set(want))
    with open(fp, 'w') as f:
        json.dump(d, f, indent=1)
    log('kl_fa_bank.van_quiet %s: %s (groups %s)' % (folder, '; '.join(changed) or 'nothing to change', ', '.join(want)))
    return {'groups': want, 'changed': changed}


def crew_check(folder, log=print):
    """A folder with the AI heisters' squads (with or without the dynamic step) -> [faults]: no place of a heister
    squad within CREW_CLEAR of where a squad of the hall or the plaza stands or goes - a man's start, a cover
    point, a flank point, a defend place (CREW_CLEAR's note; run V2: two heisters died by the point-blank rule at
    such places and three stood at holds between them). The other stages' squads are reported, not judged: the
    guards of the way in stand ON the way by the map's design. Also said: how the heisters cross the hall."""
    import kl_fa_bots as F
    read_opts(folder)
    B = F.Built(folder)
    sc, bad = B.sc, []
    def fail(s):
        bad.append(s); log('  FAIL ' + s)
    P = lambda p: '(%d, %d, %d)' % tuple(round(x) for x in p)
    bots = [(k, B.at(k)) for t in sc.tops() if sc.names[t].startswith(F.SQUAD + 'Squad#')
            for k in range(t, sc.end[t]) if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#')]
    if not bots:
        fail('no place of an AI heister squad in the level')
    posts = collections.defaultdict(list)               # stage -> [(what, node, place)]
    for t in sc.tops():
        stage = STAGE.get(sc.names[t], 'hall' if sc.names[t] in HALL else None)
        if stage is None or not kl_fa.has(sc, t, 'ZSquadScript'):
            continue
        posts[stage] += [('man', k, B.at(k)) for k in range(t + 1, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        posts[stage] += [('place', c, B.at(c)) for c in rout_places(sc, t)]
    for stage in ('start', 'down', 'beat', 'hall', 'plaza'):
        judged = stage in ('hall', 'plaza')
        near = sorted((math.dist(p, q), k, c, what) for what, c, q in posts.get(stage, ()) for k, p in bots)
        if not near:
            log('  %-5s no squad of this stage in the level' % stage)
            continue
        close = [x for x in near if x[0] < CREW_CLEAR]
        d, k, c, what = near[0]
        log('  %-5s %3d men and places; the nearest to a heister\'s place: %d (%s %s %s - %s %s)%s' % (
            stage, len(posts[stage]), d, what, sc.path[c][5:][-60:], P(B.at(c)), sc.path[k][5:].split('!')[-1][-52:], P(B.at(k)),
            '' if not judged else '; %d pairs under %d' % (len(close), CREW_CLEAR)))
        if judged:
            seen = set()
            for d, k, c, what in close:
                if c not in seen:                       # one line per police place: its nearest heister place
                    seen.add(c)
                    fail('%s: %s %s at %s is %d from the heisters\' %s at %s (%d wanted)' % (
                        stage, what, sc.path[c][5:][-70:], P(B.at(c)), d, sc.path[k][5:].split('!')[-1][-52:], P(B.at(k)), CREW_CLEAR))
    # how the hall is crossed (hall_dash): said, not judged - a folder without the step is the build of runs V0 .. V2
    delay = {k: v[0] for k, _i, v in kl_fa.controllers(sc, 'TriggerDelay2')}
    n = collections.Counter()
    drout = {kk: vv for kk, _ii, vv in kl_fa.controllers(sc, 'DefendBehaviourRout')}
    if CREW_FIX2:           # the skeptic's test (waves review, fault 3): a hold timer of the heisters, 4 hops up the lists, a step with a place in the dash box
        named_by = collections.defaultdict(list)
        for kk in range(1, len(sc.nodes)):
            for s_ in A.named(sc, kk):
                for j in sc.resolve(s_):
                    named_by[j].append(kk)
        dbox = {kk for kk, vv in drout.items() if sc.names[sc.top[kk]].startswith(F.SQUAD + 'Squad#') and any(in_box(B.at(j), DASH_BOX) for s_ in (vv[1] or []) for j in sc.resolve(s_))}
        for j, d in delay.items():
            if d > DASH_GAP + 1e-6 and DASH_HOLD in sc.names[j] and sc.names[sc.top[j]].startswith(F.SQUAD + 'Squad#'):
                front, seen_ = [j], {j}
                for _hop in range(4):
                    front = [x for y in front for x in named_by.get(y, ()) if x not in seen_]
                    seen_.update(front)
                if seen_ & dbox:
                    fail('hold timer %s (%g s) is started, within 4 steps, by a Defend step with a place in the hall (%s)' % (sc.path[j][5:][-60:], d, sc.path[min(seen_ & dbox)][5:][-50:]))
    for k, _i, v in kl_fa.controllers(sc, 'DefendBehaviourRout'):
        if sc.names[sc.top[k]].startswith(F.SQUAD + 'Squad#') and any(in_box(B.at(j), DASH_BOX) for s in (v[1] or []) for j in sc.resolve(s)):
            n['steps'] += 1
            n['sprint'] += v[4] == DASH_MOVE
            n['hold s'] += sum(delay[j] for j in dash_chain(sc, v, delay, drout))        # ... and the cover branch's, one step on
            long_ = [(sc.path[j][5:][-50:], delay[j]) for j in dash_chain(sc, v, delay, drout) if delay[j] > DASH_GAP + 1e-6]
            if long_ and CREW_FIX2:
                fail('dash step %s: its hold timers (direct or through the cover branch) are longer than %g s: %s' % (sc.path[k][5:][-60:], DASH_GAP, long_[:3]))
            nx = [j for s in (v[7] or []) for j in sc.resolve(s)]
            tm = [delay[j] for j in nx if j in delay and DASH_HOLD in sc.names[j]]
            if tm and min(tm) < 0.05 and any(kl_fa.has(sc, j, 'RandomTrigger') and '_cover' in sc.names[j] for j in nx):
                n['mixed'] += 1
                if CREW_FIX2:
                    fail('dash step %s names a hold timer of %g s and a cover branch in ONE list (no stock precedent; CREW_FIX2 takes the cover out)' % (sc.path[k][5:][-70:], min(tm)))
    log('  the hall\'s crossing: %d Defend steps of the heisters have a place in the hall, %d of them %s; the hold timers they start add up to %g s%s' % (
        n['steps'], n['sprint'], DASH_MOVE, n['hold s'], ' (hall_dash has run)' if n['steps'] and n['sprint'] == n['steps'] and n['hold s'] <= (DASH_GAP if CREW_FIX2 else 0.0) * n['steps'] + 1e-6 else
        ' (no hall_dash: the heisters stop in the hall as in run V2)'))
    log('kl_fa_bank.crew_check %s: %d places of the AI heisters against %d men and places of the hall\'s and the plaza\'s squads (%d wanted between them): %s' % (
        folder, len(bots), len(posts['hall']) + len(posts['plaza']), CREW_CLEAR, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


# ------------------------------------------------------------------ the delivered level (after the finishing chain)
# TWO THINGS NO TOOL OF THE CHAIN DOES (review round 1):
# seal()     THE ROOMS' NEIGHBOUR LISTS. The graft sends a list entry whose entity did not come along to the scene's
#            free REF id (kl_scene.remap_refs: 'an id no entity has', it resolves to nothing: 229 entries of two rooms
#            here, the form Late Night Opening loaded and played with). Every tool that ADDS entities afterwards hands
#            exactly that id to its first new entity: after the bots' step the 229 entries name the squad group
#            'Gameplay!merc_bot_squad!Squad#02', which kl2 0x83dca0 then counts among 'the objects of the room' (no
#            crash by live precedent - the tab's maps carry it - but not what was meant). seal() sends every list entry
#            that names an entity outside the map's own subtrees ('Locations/...') to the free id of the WRITTEN
#            scene. It must be the chain's LAST step: a tool that adds an entity after it takes the id again.
# reverify() kl_graft.verify's cross-reference tests, on the written archive. audit and preflight only quote the
#            BUILD's result.json, and the chain takes some 160 entities out and puts some 530 in afterwards (slot ids
#            of the .oct / .rmi / .rmc move with each). Lifted from kl_graft.verify with the build-time arguments
#            taken out (the reviewer's C:/kl_scratch/bank/review_crash_1/s/verify2.py), plus seal()'s rule.
MAP_SIDE = 'Locations/'                 # top-level names of the map's own subtrees: what a room's list may name


def room_cells(sc, buf):
    """[(room node, offset in the .buf, kind)] of every REF id cell of the rooms' gates and neighbour lists
    (kl_scene.room_refs); kind 'gate' / 'head' (a list's own room) / 'entry'. Rooms whose two offsets lie outside
    the .buf are left out (reverify says so)."""
    out = []
    for k in range(1, len(sc.nodes)):
        lab = kl_graft.labels(sc.cls(k))
        if 'ZROOM[9]' not in lab:
            continue
        us = units(sc.nodes[k]['props'][1:-1])
        ng, nl = kl_graft.u32(us[lab.index('ZROOM[0]')][0]), us[lab.index('ZROOM[1]')][0][1][0]
        g, l = kl_graft.u32(us[lab.index('ZROOM[9]')][0]), kl_graft.u32(us[lab.index('ZROOM[10]')][0])
        if (ng and not 16 <= g <= len(buf) - 0x74 * ng) or (nl and not 16 <= l < len(buf)):
            continue
        gate, heads = {g + 0x74 * i + 0x30 for i in range(ng)}, {l + 12 * i for i in range(nl)}
        out += [(k, o, 'gate' if o in gate else 'head' if o in heads else 'entry') for o in kl_scene.room_refs(buf, 'dd', g, ng, l, nl)]
    return out


def strays(sc, scene, buf):
    """-> ([offsets of list entries that name an entity outside the map's subtrees], Counter of who they name, the
    number of entries that name no entity at all = the parked ones, the scene's free REF id)."""
    ents = list(scene.entities())
    by_ref = {e.ref: k + 1 for k, e in enumerate(ents)}
    free = scene.ref_slots
    if free in by_ref:
        raise ValueError('kl_fa_bank: REF id %d (the header\'s slot count) is taken by %s' % (free, sc.path[by_ref[free]]))
    offs, who, parked = [], collections.Counter(), 0
    for _room, o, kind in room_cells(sc, buf):
        v = struct.unpack_from('<I', buf, o)[0]
        if kind != 'entry' or v in (0, 0xffffffff):
            continue
        if v not in by_ref:
            parked += 1
        elif not sc.names[sc.top[by_ref[v]]].startswith(MAP_SIDE):
            offs.append(o); who[sc.path[by_ref[v]][len(R):]] += 1
    return offs, who, parked, free


def seal(folder, log=print):
    """In place, on a folder the finishing chain is through with: the room list entries that name an entity outside
    the map (strays) go to the scene's free REF id. Only the .buf member changes. -> the number of entries moved."""
    import kl_chars as C
    lv = C.Lv(folder)
    sc, raw = lv.scene()
    buf = lv['.buf']
    offs, who, parked, free = strays(sc, kl_scene.Scene(raw, buf), buf)
    if offs:
        new = bytearray(buf)
        for o in offs:
            struct.pack_into('<I', new, o, free)
        lv['.buf'] = bytes(new)
        tmp = lv.src + '.tmp'
        kl_graft.write_zip(tmp, [(n, lv.files[n]) for n in lv.order])
        os.replace(tmp, lv.src)
    log('kl_fa_bank.seal %s: %d room list entries named an entity outside the map (%s) and now name the free REF id %d; %d named no entity before' % (
        folder, len(offs), ', '.join('%d x %s' % (n, p) for p, n in who.most_common(3)) or '-', free, parked))
    return len(offs)


def reverify(folder, log=print):
    """kl_graft.verify's cross-reference tests on the WRITTEN level of a folder (bare, finished or delivered) ->
    [problems]. What it follows: .gms / .buf round trip and Scene.check; the property tree against the schemas and
    its scene paths; model = ZGEOM[4]; the .prm's materials, textures and .oct records; the .oct room trees by slot
    id under their room; .rmi / .rmc boxes; gates and neighbour lists; KEYS offsets; .HVK / .sgd / surface-table
    REFs; the .sgp's rooms; FDX; sound references; animation sets; registered classes."""
    import kl_prmgraph as G, kl_texmat as T, kl_octree as O, kl_members as MB, kl_anm, kl_snd
    from kl_prp import Prp
    arch = archive_of(folder)
    with zipfile.ZipFile(arch) as z:
        low = {n.rsplit('_Main', 1)[1].lower(): n for n in z.namelist() if '_Main' in n}
        get = lambda e: z.read(low[e.lower()])
        out = {e: get(e) for e in ('.gms', '.buf', '.prp', '.prm', '.TEX', '.MAT', '.oct', '.rmi', '.rmc', '.HVK', '.sgd', '.sgp', '.ANM')}
    Jn, snd, _loc = kl_fa.load(arch)
    sch, bad = J.schema('dd'), []
    sc = kl_scene.Scene(kl_gms.unpack(out['.gms']), out['.buf'])
    bad += sc.check()
    g2, b2 = sc.write()
    if kl_gms.pack(g2) != out['.gms'] or b2 != out['.buf']:
        bad.append('.gms / .buf do not round-trip')
    ents = list(sc.entities())
    by_slot, by_ref, head = {v + 2: e for e, v in sc.slots().items()}, {e.ref: e for e in ents}, len(sc.head)
    # .prp
    _data, misfits, paths, _names = J.check(Jn, log=lambda *_a: None)
    bad += ['%s: %s: %s' % (Jn.path[k], what, why) for k, what, why in misfits[:10]]
    bad += ['scene path does not resolve: %s %s -> %s' % (h, f, s) for _k, h, f, s in paths[:10]]
    twice = [n for n, c in collections.Counter(Jn.names[k] for k in Jn.tops()).items() if c > 1]
    if twice:
        bad.append('%d top-level names are used twice, e.g. %s' % (len(twice), twice[:3]))
    if len(Jn.nodes) != len(ents) + 1 or Jn.names[1:] != [e.name.decode('latin1') for e in ents] or Jn.tids[1:] != [e.tid for e in ents]:
        bad.append('.prp nodes and .gms entities differ')
    # .prm, .TEX, .MAT, .oct records
    p, prm = Prp(out['.prp']), G.read(out['.prm'], 'dd')
    proots = G.prp_roots(p, Jn.tids, sch, 'dd')
    geom = {w[0]: c for w, c, k in proots if w[0] != 'scene' and w[1] is None and k is None}
    wrong = sum(1 for k, e in enumerate(ents, 1) if e.model != geom.get(k, 0))
    if wrong:
        bad.append('%d entities: .gms model differs from ZGEOM[4]' % wrong)
    try:
        kinds, args = G.walk(prm, [(c, k) if k else c for _w, c, k in proots] + [e.model for e in ents if e.model])
    except ValueError as x:
        kinds, args = {}, {}
        bad.append('.prm: %s' % x)
    tex, mat = T.read_tex(out['.TEX']), T.read_mat(out['.MAT'])
    octj = O.Oct.parse(out['.oct'])
    if octj.pack() != out['.oct']:
        bad.append('.oct does not round-trip')
    recs, seen, miss = set(octj.record_refs()), collections.Counter(), collections.Counter()
    for i, k in kinds.items():
        for off, typ, _k in G.fields(prm, i, k, args.get(i, 0)):
            if typ == 'm' and prm.u16(i, off) not in mat.insts:
                miss['material'] += 1
            elif typ in 'tT' and prm.u32(i, off) and prm.u32(i, off) % G.SLOTS['dd'] not in tex.tex:
                miss['texture'] += 1
            elif typ == 'o':
                seen[prm.u32(i, off)] += 1
                miss['.oct record'] += prm.u32(i, off) not in recs
    bad += ['.prm names %d missing %ss' % (v, k) for k, v in miss.items() if v]
    if any(v > 1 for v in seen.values()):
        bad.append('.oct record named by two live model roots: %d' % sum(1 for v in seen.values() if v > 1))
    if mat.refs != T.material_refs(out['.prm']):
        bad.append('.MAT ref table is not the .prm\'s')
    lost = T.used_textures(mat) - set(tex.tex)
    if lost:
        bad.append('%d material textures are not in the .TEX' % len(lost))
    if any(not (0 < c < len(prm.chunks) and len(prm.chunks[c]) == 64 and prm.u16(c, 2) == 8) for _f, c in octj.tail):
        bad.append('.oct tail names a chunk that is not a 64-byte mesh')
    # rooms: the .oct trees by SLOT id, the room index, gates and lists by REF id
    is_room = kl_graft.is_room
    _e, ro = kl_graft.rooms_of(sc)
    if len(ro) != len(octj.rooms):
        bad.append('.oct has %d tree sets, the scene %d rooms' % (len(octj.rooms), len(ro)))
    def room_above(e):
        e = e.parent
        while e is not None and not is_room(e.tid):
            e = e.parent
        return e
    wr, nitems = collections.Counter(), 0
    for owner, five in zip(ro, octj.rooms):
        for ti, t in enumerate(five):
            for it in (t.items if t else ()):
                nitems += 1
                e = by_slot.get(it[0])
                if e is None:
                    wr['no entity'] += 1
                elif room_above(e) is not owner:
                    wr['other room'] += 1
                elif (ti == 4) != is_room(e.tid) or (ti < 4 and kl_gms.category(e.tid) != {0: 1, 1: 2, 2: 3, 3: 0}[ti]):
                    wr['wrong tree'] += 1
            if t:
                try:
                    t.check()
                except Exception as x:
                    wr['tree: %s' % x] += 1
    bad += ['.oct room trees: %d items: %s' % (v, k) for k, v in wr.items()]
    nbox = 0
    for ext in ('.rmi', '.rmc'):
        for b in O.RoomIndex.parse(out[ext]).boxes:
            nbox += 1
            if b.room not in by_slot or not is_room(by_slot[b.room].tid):
                bad.append('%s: box names slot id %d, not a room' % (ext, b.room))
            if b.second and b.second not in by_slot:
                bad.append('%s: second id %d is no entity' % (ext, b.second))
    buf = out['.buf']
    cells = room_cells(Jn, buf)
    rooms_in = {k for k, _o, _kind in cells}
    for k in range(1, len(Jn.nodes)):
        lab = kl_graft.labels(Jn.cls(k))
        if 'ZROOM[9]' in lab and k not in rooms_in:
            us = units(Jn.nodes[k]['props'][1:-1])
            if kl_graft.u32(us[lab.index('ZROOM[0]')][0]) or us[lab.index('ZROOM[1]')][0][1][0]:
                bad.append('%s: gates / lists outside the .buf' % Jn.path[k])
        for l in ('ZParticleEmitter[10]', 'ZParticleEmitter[11]'):
            if l in lab:
                v = kl_graft.u32(units(Jn.nodes[k]['props'][1:-1])[lab.index(l)][0])
                if v not in (0, 0xffffffff) and not 16 <= v < head:
                    bad.append('%s: %s outside the .buf head' % (Jn.path[k], l))
    for k, o, kind in cells:
        v = struct.unpack_from('<I', buf, o)[0]
        if o >= head:
            bad.append('%s: a gate / list cell lies outside the .buf head' % Jn.path[k])
        elif kind != 'entry' and (v not in by_ref or not is_room(by_ref[v].tid)) and not (kind == 'gate' and v in (0, 0xffffffff)):
            bad.append('%s: %s names REF %d, not a room' % (Jn.path[k], 'a gate' if kind == 'gate' else 'a list', v))
    stray, who, parked, free = strays(Jn, sc, buf)
    if stray:                                           # seal()'s rule
        bad.append('%d room list entries name an entity outside the map (%s): seal() not run after the last tool that adds entities?' % (
            len(stray), ', '.join('%d x %s' % (n, q) for q, n in who.most_common(3))))
    # KEYS, .HVK, .sgd, .sgp, the surface table, FDX
    nk = 0
    for e in ents:
        tr = kl_graft.keys_tracks(e.raw)
        nk += len(tr)
        if any(not 16 <= v < head for _p, ko in tr for v in ko):
            bad.append('%r: KEYS offset outside the .buf head' % e)
    h = kl_hvk.Hvk(out['.HVK'])
    if h.serialize() != out['.HVK']:
        bad.append('.HVK does not round-trip')
    n = sum(1 for s in h.shapes for i in s.inst if kl_hvk.ref(i) not in by_ref)
    if n:
        bad.append('.HVK: %d placements name no entity' % n)
    for name, payload in MB.sgd_read(out['.sgd']):
        if name in ('HavokShatterOctree', 'ExplodableOctree'):
            n = sum(1 for leaf in MB.Octree(payload).leaves if leaf[0] not in by_ref)
            if n:
                bad.append('.sgd %s: %d leaves name no entity' % (name, n))
    if sorted(r[0] for r in MB.Sgp(out['.sgp']).rooms) != sorted(Jn.path[k][5:] for k in range(1, len(Jn.nodes)) if is_room(Jn.tids[k])):
        bad.append('.sgp rooms are not the level\'s rooms')
    table = MB.SurfaceTable(sc.tail)
    if table.refs() - set(by_ref):
        bad.append('surface table names %d entities that are gone' % len(table.refs() - set(by_ref)))
    n = sum(1 for s in h.shapes for su, _f, _n in s.sub if su > len(table.materials))
    if n:
        bad.append('.HVK: %d sub-parts name a surface row past the %d of the table' % (n, len(table.materials)))
    if sc.fdx is not None:
        for r in MB.fdx_read(buf, sc.fdx)[1]:
            if kinds.get(r['model']) != 'root':
                bad.append('FDX record names chunk %d, not a model' % r['model'])
    # sound references, animation sets, registered classes
    objs = kl_snd.Snd('dd', snd).kind
    n = nsnd = 0
    for k in range(1, len(Jn.nodes)):
        for cls, holder, key in kl_graft.objects(Jn, k):
            for f, u in zip(sch.fields(cls), units(kl_graft.get_obj(holder, key)[1:-1])):
                if f.type in kl_graft.SOUND_TYPES and f.kind == 'I' and kl_graft.u32(u[0]):
                    nsnd += 1
                    n += kl_graft.u32(u[0]) not in objs and kl_graft.u32(u[0]) != kl_snd.LS_SOUND
    if n:
        bad.append('%d sound references name no object of the .SND' % n)
    lack = {s for s in p.keys if s.startswith(kl_anm.PREFIX)} - {c.name for c in kl_anm.Anm(out['.ANM'], 'dd').cols}
    if lack:
        bad.append('animation sets the .ANM lacks: %s' % sorted(lack))
    unreg = {hex(t): c for t, c in collections.Counter(e.tid for e in ents).items() if t not in sch.geoms}
    if unreg:
        bad.append('entity classes kl2.exe does not register: %s' % unreg)
    log('  the written level again (kl_graft.verify\'s cross-references): %d entities, %d reachable chunks of %d, %d room sets with %d tree items, %d room boxes, '
        '%d gate / list cells (%d list entries parked on the free REF id %d), %d KEYS tracks, %d sound references, %d .HVK placements, misfits %d: problems: %d' % (
            len(ents), len(kinds), len(prm.chunks), len(octj.rooms), nitems, nbox, len(cells), parked, free, nk, nsnd, sum(len(s.inst) for s in h.shapes), len(misfits), len(bad)))
    for b in bad[:40]:
        log('  PROBLEM (written level): ' + b[:300])
    return bad


# ------------------------------------------------------------------ the waves, the reset and the late van (chain step 'extras')
# 2026-10-11 night. NOT RUN IN THE GAME. A step of the finishing chain AFTER hall-dash and BEFORE seal (it adds entities):
#     python tools/kl_fa_bank.py extras <folder> <new folder>      (flags: bank_opts.json beside the archive, written by test())
#     python tools/kl_fa_bank.py waves-check <folder>              (the sight test, the posts, the gating)
#
# WHAT IT ADDS (everything is a clone of a node of the build itself, kl_fa_fed's way of writing; one top-level group
# 'Gameplay!bank_waves!Clock' holds the single nodes - the precedent of every tool that adds entities is a top-level
# GROUP with the nodes below it - and each wave squad is a top-level squad group):
#   RESET    (--reset)       two objects named FIRST by the round-start event (AIMonitor list 2): an ActivateGeom that shows
#                            again what the round switched OFF (the vault door's body, the intact vault) and a DeactivateGeom
#                            that hides again what it switched ON (the blown vault, fire, smoke, the vault's loot, the teller
#                            stacks, the alarm / door / rod sounds, the late van). The stock form: F02's AIMonitor list 2 ->
#                            GeomDeactivator ('money objects off at round start'), Retomoto's chair pair (both ways, every round).
#   VAN_LATE (--van-late)    'Van_show': an ActivateGeom that shows the van VAN_SHOW s after the plaza box (timer 'Timer_van').
#   WAVES    (--waves)       WAVE_TABLE: parked squads (ZSquadScript field 3 = 0: not in the world until a rout is named) cloned
#                            on the models of existing squads, each man with a post of his own (a DefendBehaviourRout, one
#                            Pos# box a man), each wave started by ONE TriggerDelay2 of the clock group that ONE existing trigger
#                            names: phase A the round-start timer (the way in), phase B the ante-room box (the crew is downstairs),
#                            phase D the plaza box (the crew is in the hall's south end). No free clock: a wave never starts from
#                            anything but the crew's own progress, and a phase has a last wave (the way out is never a spawn place).
WAVE_G = 'Gameplay!bank_waves!'
CLOCK = WAVE_G + 'Clock'
WAVE_WALL = 30.0                        # an entry or a post this far from a wall of the mesh at least. GUESS
POST_WALL = 45.0                        # a post this far from a wall of the mesh at least (the research's open posts: 60; a doorway is 100 wide). GUESS
WAVE_GAP = 70.0                         # two entries of a wave, and the entries of different waves: this far apart. GUESS
ENTRY_REUSE = 20.0                      # two waves of a phase may come into the world at the same place when they start this far apart (s). GUESS
POST_GAP = 150.0                        # two posts of the level (any waves): this far apart (design: 3 m; a man is 0.5 m wide). GUESS
POST_OLD_B = 100.0                      # phase B: the lobby is narrow (MEASURED: 8 posts only fit at 1 m from an old squad's place, 250 from the way). GUESS
POST_OLD = 150.0                        # a post this far from a place of an existing squad's man or rout. GUESS
# THE CREW'S OWN WAY (review of the waves build, fault 2): a man's entry and his post keep this far from every leg of the round's way
# (ROUTE_IN + ROUTE_VAULT + ROUTE_OUT, 3D, point to segment): phase B stood ON the leg vault lobby - airlock - stairs. GUESS: the numbers.
ROUTE_POST = {'A': 300.0, 'B': 300.0, 'D': 300.0}
ROUTE_ENTRY = {'A': 300.0, 'B': 300.0, 'D': 300.0}
POST_GAPS = {'A': (300.0, 220.0, 150.0), 'B': (300.0, 220.0, 150.0), 'D': (300.0, 220.0, 150.0)}       # review fault 7: 3 m where the mesh allows, then 2.2, never under 1.5 (POST_GAP_MIN)
# posts of the level this far apart: the first the mesh allows for the whole wave (review: 150 = 1.5 m is a bunch)
POST_GAP_MIN = 150.0
SIGHT_FAR = 9000.0                      # beyond 90 m in 3D a pair is not tested (the research's rule: ASSUMED not noticed)
BLIND_WAY = ('dock', 'lobby', 'flights', 'vault')               # the crew's regions on the way in / down (bank_waves research)
BLIND_OUT = ('hall', 'airlock', 'plaza')
# name, phase, delay after its trigger [s], men, regions it must be blind from, entry box, post box (x0, x1, z0, z1, y0, y1),
# template squad (the models and weapons come from its men). READ: the entries and posts are CHOSEN at build time in these boxes
# (wave_plan) and tested by waves-check; the boxes are the research's (C:/kl_scratch/vault_waves/bank/cands.txt, posts_250.txt).
# GUESS: every box and every delay; MEASURED in the research: the entry boxes are blind from the regions named (static
# collision, flag bit 0x10 = blocks sight ASSUMED), on the START's mesh part, 18 .. 90 m from where the men go.
# THE SUPPLY (review of the waves build, fault 1: 'a one-shot set of 24 men'). Each phase is a CHAIN of links; link i of a phase starts the
# parked squad Wave_<name> and arms link i + 1. A link is two TriggerDelay2 nodes of the clock group (a one-shot is spent after it fires, kl2 0x71e250):
#     Pace_<name>  the wait (the chain's gap)            -> Go_<name>
#     Go_<name>    0.1 s, one-shot: starts the wave      -> [the squad's Defend rout, Pace of the next link]
#     Fast_<name>  LATCH_DELAY s (ASSUMED, see below)    -> Go_<name>        named by the 'wiped out' list (ZSquadScript field 8) of the PREVIOUS wave
# Go is the only node that starts a wave and it fires once, so the timer and the latch can both reach it and the first one wins. The latch
# only ever brings a wave EARLIER (the crew has killed the last one); WITHOUT it (the default since the second skeptic: --waves-latch adds it) the chain is the plain timer chain.
# ASSUMED, never seen: that field 8 fires for a squad whose men all died (nothing in this level uses it; Retomoto's street chain was
# never watched). If it fired for a parked squad at the load, every Fast would run LATCH_DELAY after its Go: the supply would then
# take LATCH_DELAY a link, not the gap - which is why the floor (SUPPLY_MIN) is tested on the Pace chain alone and LATCH_DELAY is 12 s.
# The phases: A starts with the round (the ROUND-START timer), B with the ante-room box (once), D with the plaza box (once).
# THE FLOOR: chain A alone runs SUPPLY_MIN seconds from the start of the round, whatever the crew does (a human who takes his time in the
# dock, the lobby or the vault still has police arriving); B and D add pressure where the crew is. Nothing cancels an armed timer, the
# chains are finite (the last link names no timer) and end before SUPPLY_MAX; the round ends with the vehicle's departure.
# Totals (default table): A 11 waves / 25 men, B 5 / 5, D 8 / 24 = 24 squads of 1 .. 3 men and 54 men: actors 68 + 54 = 122 and squads
# 32 + 24 = 56, against 12 men a squad (engine), 500 squads (engine), the largest stock STORY level 147 actors, and what has run live in the
# game: Retomoto on the tab 99 actors / 55 squads - the actors are past that and under 147 (WAVES_ACTORS; --waves-extra thins it).
LATCH_DELAY, SUPPLY_MIN, SUPPLY_MAX, WAVES_LATCH, GO_DELAY = 12.0, 360.0, 600.0, False, 0.1
WAVES_ACTORS = (147, 500)              # ZFFActor / squads the waves may bring the level to (check()): the largest stock story level, the engine's squad limit
SQUAD_MEN_MAX = 12
E_YARD_E = (1800, 2350, -3500, -1500, 190, 215)        # the yard's east lane (A1 of the first build)
E_YARD_W = (-1050, -300, -3500, -1500, 190, 215)       # the yard's west end (READ in the survey: dock-region spots, 36 .. 60 m from the start)
P_DOCK = (0, 900, -5700, -4800, 190, 215)
P_YARD = (-1050, 2300, -4800, -800, 190, 215)
P_ARMOURY = (-1100, -500, -6300, -4700, 235, 245)
E_AIRLOCK = (1467, 1625, -7000, -6060, 235, 245)
P_LOBBY = (-700, 1600, -7700, -6400, 235, 245)
E_RECESS_L = (-1750, -1400, -9650, -9300, 695, 710)
E_RECESS_R = (2000, 2300, -9650, -9300, 695, 710)
P_PLAZA_L = (-3600, -700, -11800, -9900, 695, 710)
P_PLAZA_R = (1000, 3900, -11800, -9900, 695, 710)


# THE SECOND TUNING (--waves2, after run W2; re/bank_campaign.md 'Waves, after run W2'). Chain A no longer comes from the round-start timer: the
# parked squads' first Pace is named by a box just inside the dock door (DOCK_BOX_AT: 'the crew is inside'), plus a backstop timer for a crew that never
# passes it. Its men are not the yard's: they come into the world in the corridor behind the airlock (E_AIRLOCK, blind from the way) and stand at COVER
# on the flights' two landings and in the vault lobby, the rooms 'underneath' that the owner asked for. MEASURED (C:/kl_scratch/vault_tune/explore.py on
# c_bank4_fx/bank_vault, mesh + cover boxes + 3 sight rules): a post that is on the START's mesh part, 45 from a wall, within 4 m of a cover box, 15 m and blind
# from every START row and 1.5 m from every old place, and 4 m from every heister station, exists NOWHERE in the dock, the security side, the lobby, the airlock
# corridor or the upper landing, and 29 times on the lower landing + 1 in the cross corridor (3 .. 4 men at 2.2 .. 3 m apart); with 3 m from a station the lobby
# gets 15 spots, with 2.5 m the lobby 38, the upper landing 4, the lower landing 33. So the planner tries 4 m, then 3 m, then POST_STATION_MIN 2.5 m (a policeman's
# point-blank reach is 1.6 m: re/melee_damage.md) and A is four single-man links (MEASURED: a fifth finds no post, with 2 m from the crew's legs), not the first build's eleven links of 25 men.
DOCK_BOX_AT = ((560.0, 380.0, -4800.0), (250.0, 230.0, 50.0))   # = FASpecials!PIP!EnterLootArea (the dock door's plane: z -4850 .. -4750, the doorway is at z -4706)
DOCK_DOOR_Z = -4706.0
A_BACKSTOP = 80.0                       # s after the start timer (the round-start event + SQUADS_AT 10 s = GO + 1.5 s, so the backstop fires at GO + 81.5 s and the first backstopped man comes at GO + 111.5 s): chain A starts by itself, should nobody pass the box (a crew that went round: none can). GUESS
POST_STATION = (400.0, 300.0, 250.0)    # a post of chain A is this far from every heister station: the first the mesh allows for the whole wave
POST_STATION_MIN = 250.0
POST_ROUTE_MIN = 200.0                  # ... and never nearer than 2 m to a leg of the crew's way (the 3 m route rule is relaxed at cover, not dropped: re/melee_damage.md's point-blank reach is 1.6 m)
POST_COVER = 400.0                      # ... and this near a cover box's middle (a box is ~2 m wide)
START_CLEAR = 1500.0                    # no wave man's post, entry or walk within 15 m of a START row, none with a line to one
# SECOND SKEPTIC (after the second fix): chains B and D stood where the mesh allowed, not at cover, and one of B's posts on a heister station. So with --waves2
# EVERY chain's posts are at cover and POST_STATION from the heister stations; where the mesh has no such place the cover distance widens in COVER_LADDER
# steps (chain A stays at POST_COVER: MEASURED enough spots), and chain D's men of one squad stand D_GAPS apart (the first build's 3 m was 'bunched up').
# The radii a wave was planned with are stored in extras.json (post_cover, post_station) and waves-check tests each wave against ITS OWN.
COVER_LADDER = (400.0, 600.0, 800.0)
POST_GAPS_V2 = {'A': (300.0, 220.0, 150.0), 'B': (300.0, 220.0, 150.0), 'D': (500.0, 400.0, 300.0)}
RULES_X = ('sight', 'ray', 'hero', 'exact')    # the module's grid, hvk_ray's rule 0x20, 0x28, and hvk_ray's exact cast: a line under ANY of them counts
# The ENTRIES of chains A and B (E_AIRLOCK) are out of sight of the crew's way IN (BLIND_WAY), and since the second skeptic also of the stations of the
# way OUT (ROUTE_OUT): men must not 'plop out' in view of a crew that comes back up.
# The entries of chains A and B under --waves2 (the second skeptic: E_AIRLOCK has a free line to the 'stairs' station of the way OUT, 7.5 m away, at every
# one of its 246 spots). MEASURED (C:/kl_scratch/vault_tune/ent_scan2.py): on the whole mesh of the building's floors the spots blind from the way in AND the way out,
# 15 m from the START rows, 3 m from the way and 2.5 m from every heister station are 8: two small clusters in the armoury / security side. The men are
# single-man links 30 s and more apart, so one cluster each is enough (an entry may be reused after ENTRY_REUSE s).
E_ARM_A = (-1050, -950, -5520, -5400, 225, 255)
E_ARM_B = (-680, -620, -5660, -5600, 225, 255)
P_LAND1 = (-100, 900, -9400, -8800, -175, -145)         # the flights' upper landing (floor y -160)
P_LAND2 = (0, 800, -10800, -10300, -580, -540)          # the lower landing (floor y -560)
P_CROSS = (-300, 300, -10800, -9300, -580, -140)        # the cross corridor between
P_IN = (P_LAND2, P_CROSS, P_LAND1)
SUPPLY_MIN2 = 150.0                     # the second tuning: chain A runs this long at least after its trigger (the eleven links of the first needed the yard)


def chain_table(a_links=11, b_links=5, d_links=8, v2=False):
    """The default supply as WAVE_TABLE rows: (name, phase, GAP s since the chain's previous link (the first: since its trigger), men,
    regions it must be blind from, entry box, post box, template). Chain A: 12 s then every 35 s (11 links: the last at 362 s); chain B:
    22 s then every 30 s, ONE man a link (second skeptic, fault 1: the lobby takes 5 men at 3 m (MEASURED, cap.py), so the same 5 are spread over 142 s instead of 46 s); chain D: 3 s then every 25 s.
    v2 (WAVES2): chain A is four single-man links, 30 s then every 45 s after the dock box (the last at 165 s), entries E_AIRLOCK, posts P_IN."""
    rows = []
    A_POSTS = ((P_DOCK, P_YARD), (P_YARD, P_DOCK), (P_ARMOURY, P_DOCK, P_YARD))
    for i in range(4 if v2 else 0):
        rows.append(('A%02d' % (i + 1), 'A', 30.0 if i == 0 else 45.0, 1, BLIND_WAY, E_ARM_A, P_IN, G4 + 'Guards_Reinforcement_01a'))
    for i in range(0 if v2 else a_links):
        rows.append(('A%02d' % (i + 1), 'A', 12.0 if i == 0 else 35.0, 3 if i < 3 else 2, BLIND_WAY + BLIND_OUT, (E_YARD_E, E_YARD_W)[i % 2],
                     A_POSTS[i % 3], G4 + 'Guards_Reinforcement_01a'))
    for i in range(min(b_links, 4) if v2 else b_links):          # v2: the lobby has cover for four men (MEASURED: a fifth finds no post within 8 m of cover and 2.5 m off a station)
        rows.append(('B%02d' % (i + 1), 'B', 22.0 if i == 0 else 30.0, 1, BLIND_WAY, E_ARM_B if v2 else E_AIRLOCK, P_LOBBY, G4 + 'Police_Reinforcement_02'))
    for i in range(d_links):
        rows.append(('D%02d' % (i + 1), 'D', 3.0 if i == 0 else 25.0, 3, ('hall', 'airlock', 'plaza'), (E_RECESS_L, E_RECESS_R)[i % 2],
                     (P_PLAZA_L, P_PLAZA_R)[i % 2], CO + ('Police_OutSide_SWAT_02', 'Police_OutSide_SWAT_03')[i % 2]))
    return rows


# name, phase, gap [s] after the chain's previous link, men, regions it must be blind from, entry box, post box (x0, x1, z0, z1, y0, y1),
# template squad (the models and weapons come from its men). READ: the entries and posts are CHOSEN at build time in these boxes
# (wave_plan) and tested by waves-check. GUESS: every box and every number; MEASURED (survey.py, 11 s on a finished level): the dock region
# (the yard) has 105 spots 3 m apart, the lobby 3, the hall 160 and the plaza 490 - the lobby cannot take a supply, so chain B is 5 men.
WAVE_TABLE = chain_table()


def link_times(rows):
    """{name: seconds after the chain's trigger at which the link starts its wave}: the Pace gaps added up per phase."""
    t, out = collections.defaultdict(float), {}
    for r in rows:
        t[r[1]] += r[2]
        out[r[0]] = t[r[1]]
    return out


WAVE_TRIGGER = {'A': 'start timer', 'B': 'beat box', 'D': None}          # D: PLAZA_BOX (not a ROLE); WAVES2: A is the dock box of the clock group (DOCK_BOX) + the backstop
WAVE_LIST = {'A': ('TriggerDelay2', 4), 'B': ('TriggerBox', 17), 'D': ('TriggerBox', 17)}
DOCK_BOX, DOCK_LATE = CLOCK + '\\Box_in', CLOCK + '\\Timer_A_late'
RESET_CANNOT = ('MatPosAnim end poses: the vault door, the six rods (and the leaves with --doors-animate); the alarm lamps\' glow (VertAnim, '
                'AIDWrapper \'Activate\'); the Explode of the blast (one-shot); the music layers (PlayMusic: the round-start list starts them again)')


def route_dist(p):
    """3D distance of p to the nearest leg of the round's way (ROUTE_IN + ROUTE_VAULT + ROUTE_OUT)."""
    pts = [tuple(q) for _n, q in ROUTE_IN + ROUTE_VAULT + ROUTE_OUT]
    best = 1e18
    for a, b in zip(pts, pts[1:]):
        ab = [b[i] - a[i] for i in range(3)]
        L2 = sum(x * x for x in ab)
        t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, sum((p[i] - a[i]) * ab[i] for i in range(3)) / L2))
        best = min(best, math.dist(p, tuple(a[i] + ab[i] * t for i in range(3))))
    return best


class Sight:
    """Line of sight on a built level (kl_route.Grid of the collision, solid samples every 20, shapes with flag 0x10 block:
    the research's reading 'sight'); the crew's places by region. The code is the research's los.py, C:/kl_scratch/vault_waves/bank."""

    def __init__(self, folder, B, log=print):
        import bisect, kl_fa_bots as F, kl_route
        kl_route.WHO['sight'] = 0x10
        self.bisect, self.route = bisect, kl_route
        self.B, self.nav = B, F.Nav(B.scene.nav)
        self.g = kl_route.load(folder).grid('sight')
        self.grids = {'sight': self.g}                  # the other two rules are made where they are asked for (sees_by): 'ray' = flags & 0x20, 'hero' = flags & 0x28
        self.home = self.nav.part[self.nav.at(250, 200, -4350)[0]]
        sc = B.sc
        obs = []
        for t in sc.tops():
            if sc.names[t].startswith(F.SQUAD + 'Squad#'):
                for k in range(t, sc.end[t]):
                    if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#') or sc.cls(k) == 'ZFFActor':
                        obs.append(B.at(k))
        obs += [tuple(p) for p in START] + [o['at'] for o in F.money_objects(B)]
        obs += [tuple(p) for _n, p in ROUTE_IN + ROUTE_VAULT + ROUTE_OUT]       # a HUMAN walks the route's stations, not the bots' places
        self.places = obs
        seen, thin = set(), []
        for p in obs:
            h = self.nav.at(p[0], p[1], p[2], 260.0)
            y = h[1] if h else p[1]
            key = (round(p[0] / 120), round(y / 100), round(p[2] / 120))
            if key not in seen:
                seen.add(key); thin.append((p[0], y, p[2]))
        self.by = collections.defaultdict(list)
        for p in thin:
            self.by[self.region(p)].append(p)
        log('  sight: %d crew places, %d after thinning: %s' % (len(obs), len(thin), {r: len(v) for r, v in sorted(self.by.items())}))

    @staticmethod
    def region(p):
        x, y, z = p
        if y < -900: return 'vault'
        if y < 150: return 'flights'
        if y < 700:
            if x > 1000 and z < -5300: return 'airlock'
            if z > -5700: return 'dock'
            return 'lobby'
        return 'hall' if z > -9450 else 'plaza'

    def grid_of(self, rule):
        """The collision grid of a sight rule: 'sight' = the module's own (flag 0x10 blocks, ASSUMED from shape names), 'ray' = third_party/anp/
        scripts/hvk_ray.py's rule for a player's ray (a part blocks when flags & 0x20: MEASURED against five live rays), 'hero' = the same with the
        hero-only walls (flags & 0x28)."""
        if rule not in self.grids:
            self.grids[rule] = self.route.load(self.B.folder).grid({'ray': 'npc', 'hero': 'hero'}[rule])
        return self.grids[rule]

    def ray(self, a, b, rule='sight'):
        g, CELL = (self.g if rule == 'sight' else self.grid_of(rule)), self.route.CELL
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        n = int(math.sqrt(dx * dx + dy * dy + dz * dz) / 6.0) + 1
        k0 = min(n // 2, 5)
        yp, last = a[1] + dy * k0 / n, None
        for k in range(k0 + 1, n - k0 + 1):
            f = k / n
            y = a[1] + dy * f
            c = (int((a[0] + dx * f) // CELL), int((a[2] + dz * f) // CELL))
            if c != last:
                g.floors(c[0], c[1]); last = c
            s = g.so.get(c)
            if s:
                lo, hi = (yp, y) if yp < y else (y, yp)
                i = self.bisect.bisect_left(s, (lo - 6.0, -1))
                if i < len(s) and s[i][0] <= hi + 6.0:
                    return False
            yp = y
        return True

    def sees(self, o, p):
        if math.dist(o, p) > SIGHT_FAR:
            return False
        e = (o[0], o[1] + 160.0, o[2])
        return self.ray(e, (p[0], p[1] + 120.0, p[2])) or self.ray(e, (p[0], p[1] + 175.0, p[2]))

    def exact(self):
        """third_party/anp/scripts/hvk_ray.Collision of the folder's archive (the exact cast of a player's ray; loaded on first use)."""
        if getattr(self, '_exact', None) is None:
            import glob
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'third_party', 'anp', 'scripts'))
            import hvk_ray
            z = sorted(glob.glob(os.path.join(self.B.folder, '*_Main.zip')))
            self._exact = hvk_ray.Collision(z[0])
        return self._exact

    def sees_exact(self, e, q):
        """True when hvk_ray's cast from e to q is free under mask 0x20 or 0x28 (a part blocks when flags & mask). The module's grid over-blocks around thin or
        round shapes (second skeptic: ShatterPillar_09 blocked B04's line to the row at x 450, the exact ray passes beside it)."""
        C = self.exact()
        seg = (q[0] - e[0], q[1] - e[1], q[2] - e[2])
        return any(C.ray(e, seg, m) is None for m in (0x20, 0x28))

    def sees_by(self, o, p, rules=('sight', 'ray', 'hero')):
        """The rules (of RULES, and 'exact' = hvk_ray's cast) under which a man at o sees a man at p (eye 160 over the feet, target 120 and 175, SIGHT_FAR)."""
        if math.dist(o, p) > SIGHT_FAR:
            return []
        e = (o[0], o[1] + 160.0, o[2])
        out = [r for r in rules if r != 'exact' and (self.ray(e, (p[0], p[1] + 120.0, p[2]), r) or self.ray(e, (p[0], p[1] + 175.0, p[2]), r))]
        if 'exact' in rules and any(self.sees_exact(e, (p[0], p[1] + dy, p[2])) for dy in (120.0, 175.0)):
            out.append('exact')
        return out

    def seen_by(self, p, regions):
        """-> (region, observer) of the first crew place of the regions that sees the point p, else None."""
        for r in regions:
            for o in sorted(self.by.get(r, ()), key=lambda o: math.dist(o, p)):
                if self.sees(o, p):
                    return r, o
        return None


def lattice(box, step):
    x0, x1, z0, z1, y0, y1 = box
    x = math.ceil(x0 / step) * step
    while x <= x1:
        z = math.ceil(z0 / step) * step
        while z <= z1:
            yield float(x), (y0 + y1) / 2.0, float(z), (y1 - y0) / 2.0 + 60.0
            z += step
        x += step


# ------------------------------------------------------------------ guns on the START rows (run W2's diagnosis, and a check)
# Run W2 (2026-10-12): the idle human was dead 35 s after GO in the start yard and three AI heisters were dead at GO + 14 / + 25 / + 27 s; with the
# 61 enemies alone (run V2) the human lived the whole run. MEASURED on the built level (start_pressure): chain A's first wave stood its three
# posts 7.5 .. 12 m from the START rows (A01: (600, 200, -5100), (0, 200, -4850), (600, 200, -5500); the START rows are at z -4350) and the next
# wave's posts 2.5 .. 7 m from them: the wave posts were only kept 2.5 m from 'a heister station', and the START rows are stations of the
# dock region of S.places but the post rule `far` only tests the stations of the regions the wave names. start_pressure counts, for a time T after
# the GO, the men that are in the world and bear on a START row (distance <= PRESSURE_RANGE and a line free under the module's sight rule, the
# player ray 0x20 or the player ray with hero-only walls 0x28).
GO_AFTER_EVENT = 8.5                    # s from the round-start event to the GO (kl_fa_author.BLAST_DELAY's note: 8.4 .. 8.8). READ
MEN_SPEED = 300.0                       # a walking man, cm/s. ASSUMED (the module's)
ENTER_AT = 12.0                         # s after the GO at which the first criminal passes the dock door (MEASURED, runs V2 / W1 / W2: 'heist stage 0 -> 1' at GO + 12 .. 19 s)
PRESSURE_RANGE = 6000.0                 # a gun is said to bear on a row within 60 m (the research: the AI's fire is hardly aimed beyond that). GUESS
PRESSURE_TIMES = (12.0, 25.0, 35.0, 60.0)
VOICE = False                           # '--voice': the build is made with kl_snd.VOICE on: every streamed single IMA ADPCM line becomes an in-memory record (re/luvsic_pass.md 1.1)
TELLER_FOYER, TELLER_FOYER_S = False, 2.0       # '--teller-foyer' (WAVES2): the teller stacks are shown TELLER_FOYER_S after the FOYER box, not 20 s after the plaza box
WAVES2 = False                          # '--waves2': the second tuning (chain A from the dock box, inside posts, registers from the foyer): see the section 'Waves, after run W2'


def streamed_singles(folder):
    """The streamed single IMA ADPCM records (0x11, one clip, not a language file's) of the folder's built .WHD -> sorted names (kl_fa_club's way of counting)."""
    import kl_whd, kl_snd
    f = [x for x in os.listdir(folder) if x.lower().endswith('_main.whd')]
    if not f:
        return []
    b = open(os.path.join(folder, f[0]), 'rb').read()
    return sorted(kl_snd.cs(b, r['name']).decode('latin1').replace('\\', '/') for r in kl_whd.records('dd', b).values()
                  if r['fmt'] & kl_whd.STREAMED and not r['fmt'] & kl_whd.LANGFILE and not r['fmt'] >> 24 and r['fmt'] & 0xffff == 0x11)


def start_men(B, rep=None, waves2=False, earliest=False):
    """Every man of the level that can fire on the start yard in the first minute -> [dict(kind, name, t_in, places, post)]. t_in is in seconds after the
    round-start event: the old squads of stage 'start' and 'down' come at SQUADS_AT, a wave at its chain's trigger plus its delay (chain A: the round-start
    timer; with WAVES2 the dock box, ENTER_AT + GO_AFTER_EVENT after the event at the earliest). `places` are the points a man may stand at (his
    start and every defend place of his squad: the upper bound), `post` None for an old man, (entry, post) for a wave man."""
    sc, out = B.sc, []
    hunt = hunter_squads(sc)
    for t in sc.tops():
        if STAGE.get(sc.names[t]) in ('start', 'down') or (earliest and STAGE.get(sc.names[t]) == 'beat'):
            acts = [B.at(k) for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
            posts = [B.at(k) for k in range(t + 1, sc.end[t]) if sc.cls(k) == 'ZBoxPrimitive' and sc.names[k].startswith('Pos#')]
            for i, a in enumerate(acts):
                ev = wake_map().get(sc.path[t][len(R):]) if STAGING else None
                if earliest:                    # the garrison rule: the earliest a gate's event can fire (WAKE_EARLIEST), the beat's police with the ante-room's
                    t_old = WAKE_EARLIEST[ev or 'ante'] + GO_AFTER_EVENT if (ev or STAGE.get(sc.names[t]) == 'beat') else SQUADS_AT
                else:
                    t_old = WAKE_EVENTS[ev]['go'] + GO_AFTER_EVENT if ev else SQUADS_AT
                out.append(dict(kind='old', name='%s#%d' % (sc.names[t].split('!')[-1], i + 1), t_in=t_old, places=[a] + posts, post=None,
                            hunter=sc.path[t][len(R):] in hunt))
    for w in (rep or {}).get('waves', ()):
        base = 0.0
        if w['phase'] == 'A' and waves2:
            base = ENTER_AT + GO_AFTER_EVENT
        elif w['phase'] == 'B':
            base = 40.0 + GO_AFTER_EVENT            # the ante-room box: 'some 35 - 40 s after GO' (the beat's own note)
        elif w['phase'] == 'D':
            base = 190.0 + GO_AFTER_EVENT
        for j, (e, q) in enumerate(w['men']):
            out.append(dict(kind='wave', name='%s_%d' % (w['name'], j + 1), t_in=base + w['delay'], places=[tuple(e), tuple(q)], post=(tuple(e), tuple(q)), phase=w['phase']))
    return out


def start_pressure(S, men, times=PRESSURE_TIMES, rules=('sight', 'ray', 'hero'), rng=PRESSURE_RANGE, nav=None):
    """For each time T (s after the GO): the men in the world that bear on a START row -> {T: dict(in_world, bear: {rule: [names]}, any: [names], near15: n within
    15 m with a line, nearest: (dist, name, row))}. A man who walks (a wave man before he arrives) is taken on the straight line from his entry to his post; an old
    man at every place he may stand (an upper bound, the same for both builds)."""
    rows = [tuple(p) for p in START]
    res = collections.OrderedDict()
    for T in times:
        te = T + GO_AFTER_EVENT
        inw, bear, anyn, near, nearest = 0, {r: [] for r in rules}, [], 0, None
        for m in men:
            if te < m['t_in']:
                continue
            inw += 1
            if m['post']:
                e, q = m['post']
                arr = m['t_in'] + math.dist(e, q) / MEN_SPEED
                f = 1.0 if te >= arr else max(0.0, (te - m['t_in']) * MEN_SPEED / max(math.dist(e, q), 1.0))
                where = [tuple(e[a] + (q[a] - e[a]) * f for a in range(3))]
            else:
                where = m['places']
            hit, close = set(), False
            for o in where:
                for r in rows:
                    d = math.dist(o, r)
                    hunts = nav is not None and m.get('hunter') and d <= rng + HUNT_REACH        # HUNTERS: also from the points of his way towards the row
                    if d > rng and not hunts:
                        continue
                    for oo in ([o] + (hunt_points(nav, o, r) if hunts else [])):
                        d = math.dist(oo, r)
                        if d > rng:
                            continue
                        see = S.sees_by(oo, r, rules)
                        if see:
                            hit.update(see)
                            if nearest is None or d < nearest[0]:
                                nearest = (round(d), m['name'], tuple(round(x) for x in r))
                            close = close or d <= 1500.0
            for r_ in hit:
                bear[r_].append(m['name'])
            if hit:
                anyn.append(m['name'])
            near += 1 if close else 0
        res[T] = dict(in_world=inw, bear=bear, any=anyn, near15=near, nearest=nearest)
    return res


FAILED = []


def start_guns(folders, log=print):
    """'kl_fa_bank.py start-guns <folder> [<folder> ...]': start_pressure on each built folder (waves taken from its extras.json)."""
    import json, kl_fa_bots as KB
    out = {}
    for fo in folders:
        B = KB.Built(fo)
        pj = os.path.join(fo, 'extras.json')
        rep = json.load(open(pj)) if os.path.isfile(pj) else None
        o = read_opts(fo)
        set_wake_built(rep)
        S = Sight(fo, B, lambda *a: None)
        men = start_men(B, rep, bool(o.get('waves2')))
        nav = KB.Nav(B.scene.nav)
        res = start_pressure(S, men, nav=nav)
        out[fo] = res
        log('start_guns %s (%d old men, %d wave men; waves2 %s):' % (fo, sum(m['kind'] == 'old' for m in men), sum(m['kind'] == 'wave' for m in men), bool(o.get('waves2'))))
        for T, r in res.items():
            log('  GO+%3.0f s: %3d men in the world; bearing on a START row within %d m: sight %d, ray(0x20) %d, ray+hero(0x28) %d; any rule %d (%s); within 15 m with a line: %d; nearest %s' % (
                T, r['in_world'], PRESSURE_RANGE / 100, len(r['bear']['sight']), len(r['bear']['ray']), len(r['bear']['hero']), len(r['any']),
                ' '.join(r['any'])[:140], r['near15'], r['nearest']))
        # the START rule (runs W7 / W8): with the exact ray and the hunters counted, no gun on a START row at GO / + 11 / + 30 / + 60 s in a build with staging
        ex_ = start_pressure(S, men, times=(0.0, 11.0, 30.0, 60.0), rules=('exact',), nav=nav)
        for T, r in ex_.items():
            log('  START rule, GO+%3.0f s: %2d men in the world, exact ray (hunters counted, reach %d m): %d%s' % (T, r['in_world'], HUNT_REACH / 100, len(r['bear']['exact']),
                                                                                                            ' ' + ' '.join(r['bear']['exact'])[:160] if r['bear']['exact'] else ''))
            if r['bear']['exact'] and o.get('staging'):
                FAILED.append('%s: START rows: %d guns at GO + %g s' % (fo, len(r['bear']['exact']), T))
                log('  FAIL ' + FAILED[-1])
        log('kl_fa_bank.start_guns %s: %s' % (fo, 'not a staged build: said only' if not o.get('staging') else 'PASS' if not [x for x in FAILED if x.startswith(fo)] else 'FAILED'))
    return out


def seg_dist(p, a, b):
    """3D distance of the point p to the segment a-b."""
    ab = [b[i] - a[i] for i in range(3)]
    L2 = sum(x * x for x in ab)
    t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, sum((p[i] - a[i]) * ab[i] for i in range(3)) / L2))
    return math.dist(p, tuple(a[i] + ab[i] * t for i in range(3)))


def start_ok(S, p):
    """A wave man's entry or post keeps START_CLEAR from every START row and has no line to one under any of the three sight rules (run W2's fault)."""
    rows = [tuple(q) for q in START]
    return all(math.dist(p, r) >= START_CLEAR for r in rows) and not any(S.sees_by(p, r, RULES_X) for r in rows)


def way_out_sees(S, p):
    """The stations of the crew's way OUT (ROUTE_OUT) that see a man standing at p, under any rule of RULES_X -> [names]."""
    return [n for n, q in ROUTE_OUT if S.sees_by(tuple(q), p, RULES_X)]


def cover_dist(B, p, _cache={}):
    """Distance of p to the nearest shown cover box of the level on about its floor (kl_fa_bots_dyn.cover_boxes)."""
    import kl_fa_bots_dyn as KD
    key = id(B)
    if key not in _cache:
        _cache.clear()
        _cache[key] = [c['at'] for c in KD.cover_boxes(B) if not c['hidden']]
    return min([math.dist(p, c) for c in _cache[key] if abs(c[1] - p[1]) < 200] or [1e9])


def wave_plan(B, S, o, log=print):
    """The waves as built: [dict(name, phase, delay, template, men=[(entry, post)])] chosen in WAVE_TABLE's boxes, in table order
    while the men fit WAVES_EXTRA. An entry: on the START's mesh part, WAVE_WALL from a wall, blind from the wave's regions
    (Sight), WAVES_NEAR (phase D: CREW_CLEAR) from every crew place, WAVE_GAP from every entry chosen. A post: on the mesh,
    WAVE_WALL from a wall, that far from the crew's places, POST_OLD from an existing squad's place, POST_GAP from every post
    chosen, LANE_CLEAR from the van's drive. Nobody is taken out of the 61 already there. A wave that finds no place for
    its men is an ERROR (the tool does not build a smaller wave unasked).
    WAVES2 (the second tuning, after run W2): every entry, post and walk also keeps START_CLEAR from the START rows and has no line to one (start_ok);
    chain A's posts are AT COVER (POST_COVER from a cover box) and, in place of the 3 m route rule, POST_STATION from every heister station (the first
    of 4 m, 3 m, 2.5 m the mesh allows for the whole wave)."""
    import kl_fa_bots as F
    sc, nav = B.sc, S.nav
    v2 = bool(o.get('waves2'))
    old = [B.at(k) for t in sc.tops() if STAGE.get(sc.names[t]) or sc.names[t] in HALL
           for k in range(t + 1, sc.end[t]) if sc.cls(k) in ('ZFFActor', 'ZBoxPrimitive')]
    drive = ESC.Poly([tuple(p) for p in (PLAN or plan_of(os.path.join(B.folder, 'van.json')))['path']])
    used_e, used_p, plan, men = [], [], [], 0
    at_of, cut = link_times(WAVE_TABLE), set()
    for name, phase, gap_s, n, blind, ebox, pbox, template in WAVE_TABLE:
        delay = at_of[name]                         # seconds after the chain's trigger (the gaps added up)
        if phase in cut or men + n > o['waves_extra']:
            cut.add(phase)                          # the rest of the chain goes too: a chain with a hole in it would stop for good
            log('  waves: %s (%d men) left out: %d of %d men used' % (name, n, men, o['waves_extra']))
            continue
        near = CREW_CLEAR if phase == 'D' else o['waves_near']
        ref = [q for q in S.places if S.region(q) in blind]       # the stations of the regions the crew is in while this wave comes
        far = lambda p: all(math.dist(p, q) >= near for q in ref)
        ents, tries = [], 0
        cands = sorted(lattice(ebox, 20), key=lambda c: math.dist(c[:3], ((ebox[0] + ebox[1]) / 2, c[1], (ebox[2] + ebox[3]) / 2)))
        for x, y, z, dy in cands:
            hit = nav.at(x, y, z, dy, S.home)
            if hit is None or nav.clearance(x, hit[1], z) < WAVE_WALL:
                continue
            p = (x, hit[1], z)
            if not far(p) or route_dist(p) < ROUTE_ENTRY[phase] or any(math.dist(p, q) < WAVE_GAP for q in [e for e, ph, dl in used_e if ph == phase and abs(dl - delay) < ENTRY_REUSE] + ents):
                continue
            tries += 1
            if S.seen_by(p, blind) or (v2 and (not start_ok(S, p) or (phase in 'AB' and way_out_sees(S, p)))):
                continue
            ents.append(p)
            if len(ents) == n:
                break
        if len(ents) < n:
            raise ValueError('kl_fa_bank.wave_plan: wave %s found %d of %d entries unseen from %s in %s (%d tried)' % (name, len(ents), n, blind, ebox, tries))
        mid = tuple(sum(e[a] for e in ents) / n for a in range(3))
        at_cover = v2                                # every chain's posts are at cover (the second skeptic: B and D were not)
        posts, station, got_cover, got_gap = [], None, None, None
        boxes = pbox if isinstance(pbox[0], tuple) else (pbox,)          # a tuple of boxes: the first is preferred, the others take over when it is full
        pool = [c for b_ in boxes for c in sorted(lattice(b_, 50), key=(lambda c: route_dist(c[:3])) if phase in 'AB' else (lambda c: math.dist(c[:3], mid)))]
        covers = (POST_COVER,) if (phase == 'A' or not v2) else COVER_LADDER
        gaps = POST_GAPS_V2[phase] if v2 else POST_GAPS[phase]
        found = False
        for cov in covers if at_cover else (None,):
            for stn in (POST_STATION if at_cover else (None,)):
                for gap in gaps:
                    posts = []
                    for x, y, z, dy in pool:
                        hit = nav.at(x, y, z, dy, S.home)
                        if hit is None or nav.clearance(x, hit[1], z) < POST_WALL:
                            continue
                        p = (x, hit[1], z)
                        if at_cover:
                            if cover_dist(B, p) > cov or min(math.dist(p, q) for q in S.places) < stn or route_dist(p) < POST_ROUTE_MIN:
                                continue
                            if phase != 'A' and (not far(p) or route_dist(p) < ROUTE_POST[phase]):
                                continue
                        elif not far(p) or route_dist(p) < ROUTE_POST[phase]:
                            continue
                        if any(math.dist(p, q) < (POST_OLD_B if phase == 'B' else POST_OLD) for q in old) or any(math.dist(p, q) < gap for q in used_p + posts):
                            continue
                        if abs(drive.project(p)[1]) < LANE_CLEAR and phase == 'D':
                            continue
                        if v2 and not start_ok(S, p):
                            continue
                        posts.append(p)
                        if len(posts) == n:
                            break
                    if len(posts) == n:
                        found = True
                        break
                if found:
                    break
            if found:
                station, got_cover, got_gap = stn, cov, gap
                break
        if len(posts) < n or not found:
            raise ValueError('kl_fa_bank.wave_plan: wave %s found %d of %d posts in %s (%d from the crew, %d from old places, %d from each other, %d from the way%s)' % (
                name, len(posts), n, pbox, near, POST_OLD, POST_GAP_MIN, ROUTE_POST[phase], '; at cover within %s and %d from a heister station' % (covers, POST_STATION_MIN) if at_cover else ''))
        if at_cover and got_cover != POST_COVER:
            log('  waves: %s: NO post at %d from cover for %d men: the ladder went to %d' % (name, POST_COVER, n, got_cover))
        gap = got_gap
        log('  waves: %s posts %d apart%s, %d..%d from the way of the crew' % (name, gap, ', %d from every heister station' % station if station else '', min(route_dist(q) for q in posts), max(route_dist(q) for q in posts)))
        # a man to the nearest free post (greedy), so that nobody crosses another's way
        pairs, free = [], list(posts)
        for e in ents:
            q = min(free, key=lambda q: math.dist(e, q)); free.remove(q); pairs.append((e, q))
        if v2:
            for e, q in pairs:
                d_ = min(seg_dist(r, e, q) for r in START)
                if d_ < START_CLEAR:
                    raise ValueError('kl_fa_bank.wave_plan: wave %s: the walk %s -> %s passes %d from a START row (%d wanted)' % (name, tuple(map(round, e)), tuple(map(round, q)), d_, START_CLEAR))
        plan.append(dict(name=name, phase=phase, delay=delay, gap=gap_s, template=template, blind=list(blind), men=pairs, post_gap=gap, post_station=station, post_cover=got_cover))
        used_e += [(e, phase, delay) for e in ents]; used_p += posts; men += n
        log('  waves: %s (phase %s, +%.0f s): %d men in %s, %s' % (name, phase, delay, n, 'x %d..%d z %d..%d' % tuple(ebox[:4]), '; '.join(
            '(%d,%d,%d)->(%d,%d,%d) %d m' % (*e, *q, math.dist(e, q) / 100.0) for e, q in pairs)))
    return plan


def target_lists(sc, names):
    """{'show': [paths], 'hide': [paths]}: what the nodes `names` (paths with ROOT) switch OFF (a DeactivateGeom's targets: shown
    again at a round start) and ON (an ActivateGeom's: hidden again). Order of first appearance."""
    out = {'show': [], 'hide': []}
    for n in names:
        for k in sc.resolve(n):
            for kind, key in (('DeactivateGeom', 'show'), ('ActivateGeom', 'hide')):
                for kk, _i, v in kl_fa.controllers(sc, kind):
                    if kk == k:
                        for s in v[1]:
                            if s not in out[key]:
                                out[key].append(s)
    return out


def module_nodes(sc):
    """The nodes whose controllers switch things in a round: the host objects of ROLE and the campaign's of CAMP (both with the
    ones below them) and the clock group's own (less the two reset objects)."""
    names = [R + v for v in ROLE.values()] + [R + v for v in CAMP.values()]
    return names + [R + CLOCK + '\\' + c for c in ('Van_show', 'Teller_show') if sc.resolve(R + CLOCK + '\\' + c)]


def reset_lists(sc, o):
    """The two lists of the reset objects, read from the level itself: show = the targets of every DeactivateGeom the module
    switches in a round, hide = those of every ActivateGeom (+ the late van's group). -> (show, hide, conflicts)"""
    t = target_lists(sc, module_nodes(sc))
    show, hide = list(t['show']), list(t['hide'])
    if o.get('van_late') and o.get('van_hide', True):
        v = R + VAN + '\\' + VAN_GROUP
        if v not in hide:
            hide.append(v)
    return show, hide, [s for s in show if s in hide]


STAGE_TOP = G4 + 'Police_Reinforcement_02'


def teller_stacks(B):
    """The paths of the teller stacks: hidden NORMAL money of FASpecials!DropMoney! outside the vault (TELLER_LATE hides them)."""
    sc, out = B.sc, []
    for k, _i, v in kl_fa.controllers(sc, 'OnlineMoneyCtrl'):
        if sc.parent[k] == 0 and sc.names[k].startswith('FASpecials!DropMoney!') and v[2] == 'ZMONEYCTRL_TYPE_NORMAL' and kl_fa.node_values(sc, k)[3]                 and not in_vault(B.at(k)):
            out.append(R + sc.names[k])
    return out


def extras_make(B, o, plan, show, hide, stacks=()):
    """The nodes of the step -> (maker, [top Node], report). Every node is a clone of a node of the build itself (kl_fa_fed.clone_built)
    or of the stock bot squad's forms (kl_fa_bots.Maker.clone, as the AI heisters' squads are made)."""
    import kl_fa_bots as KB, kl_fa_fed as FED
    sc = B.sc
    M = KB.Maker()
    node = lambda path: sc.resolve(path)[0]
    # a plain group: a heister squad's group less its script (a build without enemies has it too); the delivered bare folder has no AI heisters yet
    # (it is the round-2 reset + late van only, no chain): the dock patrol's group is the same kind of node (ZGROUP + ZSquadScript, cleared here)
    src_ = sc.resolve(R + KB.SQUAD + 'Squad#02') or sc.resolve(R + next(iter(STAGE)))
    clock = FED.clone_built(M, B, src_[0], CLOCK)
    clock.ctrls = []
    M.place(clock, (0.0, 0.0, 0.0))
    tops = [clock]
    rep = collections.OrderedDict(timers=collections.defaultdict(list), waves=[], singles=[])
    made = {}
    def single(role, name, ctrl, fields):
        n = clock.add(FED.clone_built(M, B, node(R + ROLE[role]), name))
        M.place(n, (0.0, 0.0, 0.0))
        M.set(n, ctrl, fields)
        rep['singles'].append(name)
        made[name] = n
        return R + CLOCK + '\\' + name
    out = {}
    if o.get('reset'):
        out['reset'] = [single('loot on', 'Reset_show', 'ActivateGeom', {0: 'AITrigger', 1: show}),
                        single('door off', 'Reset_hide', 'DeactivateGeom', {0: 'AITrigger', 1: hide})]
        if o.get('vault_swing') is not None:        # the door's pose: 'Activate' (frame 0 at once), DOOR_POSE_DELAY s later 'ForceStopAnim' (see DOOR_POSE_DELAY, GUESS)
            door_ = R + VAULT_DOOR
            stop_ = single('door', 'Reset_door_stop', 'AIDWrapper', {0: [door_], 1: 'ForceStopAnim'})
            out['reset'] += [single('door', 'Reset_door_closed', 'AIDWrapper', {0: [door_], 1: 'Activate'}),
                             single('door timer', 'Reset_door_timer', 'TriggerDelay2', {0: float(DOOR_POSE_DELAY), 4: [stop_]})]
        if o.get('vault_blocker'):                  # round 2 starts with the way blocked again
            out['reset'] += [single('door', 'Reset_blocker', 'AIDWrapper', {0: [R + BLOCKER], 1: 'Block'})]
    if o.get('van_late') and o.get('van_hide', True):
        v = single('loot on', 'Van_show', 'ActivateGeom', {0: 'AITrigger', 1: [R + VAN + '\\' + VAN_GROUP]})
        out['van'] = single('start timer', 'Timer_van', 'TriggerDelay2', {0: float(o.get('van_show', VAN_SHOW)), 4: [v]})
        out['van_b'] = single('start timer', 'Timer_van_b', 'TriggerDelay2', {0: float(VAN_BACKSTOP), 4: [v]})
        out['van_c'] = single('start timer', 'Timer_van_c', 'TriggerDelay2', {0: float(VAN_FOYER), 4: [v]})
    if stacks:
        t = single('loot on', 'Teller_show', 'ActivateGeom', {0: 'AITrigger', 1: list(stacks)})
        if o.get('teller_foyer'):           # the owner's wish (hold the front, get paid): shown from the FOYER box; the plaza box is the backstop
            out['teller'] = single('start timer', 'Timer_teller', 'TriggerDelay2', {0: float(TELLER_FOYER_S), 4: [t]})
            out['teller_c'] = single('start timer', 'Timer_teller_c', 'TriggerDelay2', {0: 1.0, 4: [t]})
        else:
            out['teller'] = single('start timer', 'Timer_teller', 'TriggerDelay2', {0: float(TELLER_SHOW), 4: [t]})
    sq2 = lambda tail='': R + KB.SQUAD + 'Squad#02' + tail
    form = '\\020_DefendBehaviour_rout_merc_fight_left'
    cp = lambda n: R + CLOCK + '\\' + n
    by_phase = collections.defaultdict(list)
    for w in plan:
        by_phase[w['phase']].append(w)
    for w in plan:
        ch = by_phase[w['phase']]
        i = ch.index(w)
        nxt = ch[i + 1] if i + 1 < len(ch) else None
        top = FED.clone_built(M, B, node(R + w['template']), WAVE_G + 'Wave_' + w['name'])
        top.ctrls = [c for c in top.ctrls if M.p.key(c[0]) == 'ZSquadScript']
        M.place(top, (0.0, 0.0, 0.0))
        # ZSquadScript field 3 = 0: parked. Field 8 ('wiped out', ASSUMED) names the NEXT link's Fast node: the latch (WAVES_LATCH)
        M.set(top, 'ZSquadScript', {3: 0, **{j: [] for j in range(4, 19)}, **({8: [cp('Fast_' + nxt['name'])]} if nxt and o.get('waves_latch', WAVES_LATCH) else {})})
        me = R + WAVE_G + 'Wave_' + w['name']
        d = top.add(M.clone('F07', sq2(form), '10_Defend'))
        M.place(d, (0.0, 0.0, 0.0))
        refs = []
        for j, (e, q) in enumerate(w['men']):
            pp = d.add(M.clone('F07', sq2(form + '\\Pos#01'), 'Pos#%02d' % (j + 1)))
            M.place(pp, q)
            refs.append(me + '\\10_Defend\\Pos#%02d' % (j + 1))
        M.set(d, 'DefendBehaviourRout', {0: '', 1: refs, 2: 1, 3: 0, 4: 'eDMS_NotSet', 5: 'eDF_NotSet', 6: '', 7: [], 8: 1, 9: 0})
        t = node(R + w['template'])
        acts = [k for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
        for j, (e, q) in enumerate(w['men']):
            a = acts[j % len(acts)]
            grp = top.add(FED.clone_built(M, B, sc.parent[a], 'Wave_%s_%02d' % (w['name'], j + 1)))
            dx, dz = q[0] - e[0], q[2] - e[2]
            L = math.hypot(dx, dz) or 1.0
            M.place(grp, e, KB.rot9(dx / L, dz / L))
            grp.add(FED.clone_built(M, B, a))
        # the link: Pace (the wait) -> Go (once: the rout, the next Pace); Fast (the latch) -> Go
        go = cp('Go_' + w['name'])
        pace = single('start timer', 'Pace_' + w['name'], 'TriggerDelay2', {0: float(w['gap']), 4: [go]})
        single('start timer', 'Go_' + w['name'], 'TriggerDelay2', {0: GO_DELAY, 4: [me + '\\10_Defend'] + ([cp('Pace_' + nxt['name'])] if nxt else [])})
        fast = None
        if i > 0 and o.get('waves_latch', WAVES_LATCH):
            fast = single('start timer', 'Fast_' + w['name'], 'TriggerDelay2', {0: LATCH_DELAY, 4: [go]})
        if i == 0 and not (o.get('waves2') and w['phase'] == 'A'):
            rep['timers'][w['phase']].append(pace)
        rep['waves'].append(dict(name=w['name'], phase=w['phase'], squad=me, timer=pace, pace=pace, go=go, fast=fast, delay=w['delay'], gap=w['gap'], template=w['template'],
                                 post_gap=w.get('post_gap'), post_station=w.get('post_station'), post_cover=w.get('post_cover'), men=[[list(map(round, e)), list(map(round, q))] for e, q in w['men']]))
        tops.append(top)
    if o.get('waves2') and by_phase.get('A'):       # chain A starts when the crew is inside: a box behind the dock door (+ the backstop timer)
        pace = cp('Pace_' + by_phase['A'][0]['name'])
        out['dock'] = single('speak box', 'Box_in', 'TriggerBox', {17: [pace]})
        bn = made['Box_in']
        M.place(bn, DOCK_BOX_AT[0])
        M.set(bn, None, {'ZBoxPrimitive[0]': DOCK_BOX_AT[1][0], 'ZBoxPrimitive[1]': DOCK_BOX_AT[1][1], 'ZBoxPrimitive[2]': DOCK_BOX_AT[1][2]})
        out['late'] = single('start timer', 'Timer_A_late', 'TriggerDelay2', {0: float(A_BACKSTOP), 4: [pace]})
    if o.get('staging') and not o.get('no_ai'):
        # STAGING: the squads of WAKE_SQUADS leave the start timer's list; each event gets a relay (Wake_<event>: names the routs), a backstop timer (started by the start timer) and, except 'ante' (the beat box),
        # a criminals-only box of its own. The gates' TriggerActorsDead lists and the beat box name the relay in extras().
        have = list(values(sc, node(R + ROLE['start timer']), 'TriggerDelay2')[4])
        staged = collections.OrderedDict()
        for ev, spec in WAKE_EVENTS.items():
            squads = [s_ for s_, e in WAKE_SQUADS.items() if e == ev]
            routs = [x for x in have if any(x.startswith(R + s_ + '\\') for s_ in squads)]
            if len(routs) != len(squads):
                raise ValueError('kl_fa_bank.extras: STAGING %s: the start timer names %d routs of its %d squads (%s)' % (ev, len(routs), len(squads), routs))
            w = single('start timer', 'Wake_' + ev, 'TriggerDelay2', {0: WAKE_DELAY, 4: routs})
            t_ = single('start timer', 'Timer_wake_' + ev, 'TriggerDelay2', {0: float(spec['go'] + GO_AFTER_EVENT - SQUADS_AT), 4: [w]})
            b_ = None
            if spec['box']:
                b_ = single('speak box', 'Box_wake_' + ev, 'TriggerBox', {0: 1, 14: 'ECPS_FA_MERCONLY', BOX_PER_MAN: 0, 17: [w]})
                bn = made['Box_wake_' + ev]
                M.place(bn, spec['box'][0])
                M.set(bn, None, {'ZBoxPrimitive[0]': spec['box'][1][0], 'ZBoxPrimitive[1]': spec['box'][1][1], 'ZBoxPrimitive[2]': spec['box'][1][2]})
            staged[ev] = dict(wake=w, timer=t_, box=b_, routs=routs, gate=spec['gate'], go=spec['go'])
        out['staged'] = staged
    rep['timers'] = dict(rep['timers'])
    rep.update(out)
    return M, tops, rep


def extras(src, dst, log=print):
    """The finishing chain's step 'extras' (see the section's note): the flags of bank_opts.json decide what is added. A copy of
    kl_fa_fed.apply's writer (the .prp joined with the new subtrees, the .gms / .buf written again, the .oct / .rmi / .rmc and the .prm
    chunk table kept consistent). -> report dict, also written beside the archive as extras.json"""
    import json, shutil, kl_fa_bots as KB, kl_fa_fed as FED, kl_octree as O, kl_gms
    from kl_prp import Prp
    o = read_opts(src)
    B = KB.Built(src)
    sc = B.sc
    if os.path.abspath(dst) == os.path.abspath(B.folder):
        raise ValueError('the output folder is the build\'s own')
    plan, S = [], None
    if o['waves'] and not o.get('no_ai'):
        S = Sight(src, B, log)
        plan = wave_plan(B, S, o, log)
    elif o['waves']:
        log('  waves: a round without enemies (NO_AI): none')
    show, hide, clash = reset_lists(sc, o) if o['reset'] else ([], [], [])
    if clash:
        raise ValueError('kl_fa_bank.extras: %d objects are both shown and hidden again by the reset: %s' % (len(clash), clash[:3]))
    before = KB.sizes(B.folder)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    g0, b0 = B.scene.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(B.scene, octx, rmi, rmc)
    stacks = teller_stacks(B) if o.get('teller_late') else []
    M, tops, rep = extras_make(B, o, plan, show, hide, stacks)
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'extras')
    def add_to(path, ctrl, field, new, first=False):
        k = Jn.resolve(path)[0]
        ci = A.ctrl_of(Jn, k, ctrl)
        have = list(values(Jn, k, ctrl)[field])
        add = [s for s in new if s not in have]
        kl_fa.edit(Jn, k, ci, lambda us: A.setv(Jn, us, field, add + have if first else have + add))
        return len(add)
    wired = collections.OrderedDict()
    for phase, tms in rep['timers'].items():
        trig = R + (ROLE[WAVE_TRIGGER[phase]] if WAVE_TRIGGER[phase] else PLAZA_BOX)
        ctrl, field = WAVE_LIST[phase]
        wired[phase] = add_to(trig, ctrl, field, tms)
    if 'van' in rep:
        wired['van'] = add_to(R + PLAZA_BOX, 'TriggerBox', 17, [rep['van']])
        wired['van_b'] = add_to(R + ROLE['beat box'], 'TriggerBox', 17, [rep['van_b']])
        wired['van_c'] = add_to(R + ROLE['speak box'], 'TriggerBox', 17, [rep['van_c']])      # the foyer box: the earlier event (review fault 6)
    if 'teller' in rep:                                 # the stacks leave the beat's 'loot on' list and come after the hall has been crossed
        k = Jn.resolve(R + ROLE['loot on'])[0]
        ci = A.ctrl_of(Jn, k, 'ActivateGeom')
        keep = [x for x in values(Jn, k, 'ActivateGeom')[1] if x not in stacks]
        kl_fa.edit(Jn, k, ci, lambda us: A.setv(Jn, us, 1, keep))
        if 'teller_c' in rep:
            wired['teller'] = add_to(R + ROLE['speak box'], 'TriggerBox', 17, [rep['teller']])
            wired['teller_c'] = add_to(R + PLAZA_BOX, 'TriggerBox', 17, [rep['teller_c']])
        else:
            wired['teller'] = add_to(R + PLAZA_BOX, 'TriggerBox', 17, [rep['teller']])
    if 'late' in rep:
        wired['late'] = add_to(R + ROLE['start timer'], 'TriggerDelay2', 4, [rep['late']])
    if 'staged' in rep:                                 # STAGING: the routs leave the start timer, its list gains the backstops; the gates' lists and the beat box name the relays
        sk = Jn.resolve(R + ROLE['start timer'])[0]
        gone = {x for v in rep['staged'].values() for x in v['routs']}
        keep = [x for x in values(Jn, sk, 'TriggerDelay2')[4] if x not in gone]
        kl_fa.edit(Jn, sk, A.ctrl_of(Jn, sk, 'TriggerDelay2'), lambda us: A.setv(Jn, us, 4, keep))
        wired['staged_routs_off_the_start_timer'] = len(gone)
        wired['staged_backstops'] = add_to(R + ROLE['start timer'], 'TriggerDelay2', 4, [v['timer'] for v in rep['staged'].values()])
        with open(os.path.join(src, 'bots.json'), encoding='utf-8') as f:
            vg = (json.load(f).get('plan') or {}).get('vault_gates') or []
        wait = {g['name']: g['wait'] for g in vg}
        tads = 0
        for ev, v in rep['staged'].items():
            if v['gate']:
                if v['gate'] not in wait:
                    raise ValueError('kl_fa_bank.extras: STAGING %s: the gate %s is not in the build (bots.json has %s)' % (ev, v['gate'], list(wait)))
                for t in Jn.tops():
                    if Jn.names[t].startswith(BOT_SQUAD + 'Squad#'):
                        hit = [k for k in range(t, Jn.end[t]) if Jn.names[k] == wait[v['gate']]]
                        if len(hit) != 1:
                            raise ValueError('kl_fa_bank.extras: STAGING %s: %d TriggerActorsDead %s in %s' % (ev, len(hit), wait[v['gate']], Jn.names[t]))
                        tads += add_to(Jn.path[hit[0]], 'TriggerActorsDead', 2, [v['wake']])
            if v['box'] is None:
                wired['staged_beat_box'] = wired.get('staged_beat_box', 0) + add_to(R + ROLE['beat box'], 'TriggerBox', 17, [v['wake']])
        wired['staged_gate_lists'] = tads
    if 'reset' in rep:
        wired['reset'] = add_to(R + ROLE['monitor'], 'AIMonitor', 2, rep['reset'], first=True)
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    # ---- .gms / .buf
    Sc = B.scene
    slot0 = Sc.slots()
    nxt = max([Sc.ref_slots] + [e.ref + 1 for e in B.ents])
    made = {}
    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else Sc.roots).append(e)
        made[id(n)] = e
        for c in n.kids:
            ent(c, e)
    for t in tops:
        ent(t, None)
    Sc.ref_slots = nxt
    faults = Sc.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(Sc.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = Sc.write()
    slot1 = Sc.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    # the squad groups (and the clock group) in the root's group tree, as stock lists a parked police squad
    items = []
    for t in tops:
        pts = [k.pos for k in t.kids if k.pos] + [p.pos for k in t.kids for p in k.kids if p.pos]
        lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3)) if pts else (-10.0, -10.0, -10.0)
        hi = tuple(max(p[a] for p in pts) + (190.0 if a == 1 else 10.0) for a in range(3)) if pts else (10.0, 10.0, 10.0)
        items.append((slot1[made[id(t)]] + 2, lo, hi))
    root3 = octn.rooms[0][3]
    listed, repointed, new_prm = 0, 0, None
    if root3 is not None and items:
        octn.rooms[0][3] = O.join_trees(root3, O.build_tree(items, root3.origin, root3.scale))
        listed = len(items)
        octn.rooms[0][3].check()
        move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
        if move:
            prm = bytearray(B['.prm'])
            tt, nn = struct.unpack_from('<II', prm, 0)
            old = set(octx.record_refs())
            for i in range(1, nn):
                off, size = struct.unpack_from('<II', prm, tt + 16 * i)
                if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                    v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                    if v in move:
                        struct.pack_into('<I', prm, off + 0x1c, move[v]); repointed += 1
                    elif v and v not in old:
                        raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
            if not repointed:
                raise ValueError('%d .oct records moved and no model root names one' % len(move))
            new_prm = bytes(prm)
    post = KB.room_sets_check(Sc, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(dst, exist_ok=True)
    zp = kl_graft.write_zip(os.path.join(dst, os.path.basename(B.zp)), [(n, new[n]) for n in B.order])
    for f in os.listdir(B.folder):
        p = os.path.join(B.folder, f)
        if os.path.isfile(p) and p != B.zp and not f.startswith(('audit.', 'extras.')):
            shutil.copyfile(p, os.path.join(dst, f))
    after = KB.sizes(dst)
    if after != before:
        raise ValueError('a large block changed its size: %s -> %s' % (dict(before), dict(after)))
    rep.update(source=B.folder, members_changed=changed, entities_added=len(order), entities=len(ents), wired=wired, flags=o,
               men=sum(len(w['men']) for w in rep['waves']), reset_show=len(show), reset_hide=len(hide), cannot_reset=RESET_CANNOT,
               slot_ids_moved=moved, groups_listed=listed, prm_model_roots_repointed=repointed)
    rep['timers'] = {k: list(v) for k, v in rep['timers'].items()}
    with open(os.path.join(dst, 'extras.json'), 'w') as f:
        json.dump(rep, f, indent=1, default=str)
    sj = os.path.join(dst, 'steps.json')
    if os.path.isfile(sj):
        import kl_maps
        st = json.load(open(sj))
        st['extras'] = changed
        st['same'] = [e for e in st.get('same', []) if e not in changed]
        st['final'] = kl_maps.member_ids(dst)
        with open(sj, 'w') as f:
            json.dump(st, f, indent=1)
    with open(os.path.join(dst, 'graft.txt'), 'a') as f:
        f.write('kl_fa_bank.extras: %d entities, %d wave men in %d squads, reset %s, van late %s; flags %s\n' % (
            len(order), rep['men'], len(rep['waves']), 'on' if o['reset'] else 'off', 'on' if o['van_late'] else 'off', json.dumps(o, sort_keys=True)))
    log('kl_fa_bank.extras %s -> %s: %d entities added (%d wave men in %d squads; reset: %d shown / %d hidden again; van late: %s); lists extended: %s; '
        'members changed: %s; %d slot ids renumbered, %d groups listed in the root\'s group tree, %d model roots re-pointed' % (
            src, dst, len(order), rep['men'], len(rep['waves']), len(show), len(hide), 'yes' if 'van' in rep else 'no', dict(wired), ' '.join(changed),
            moved, listed, repointed))
    log('  the four large blocks: ' + ', '.join('%s %d -> %d' % (e, before[e], after[e]) for e in before))
    log('  CANNOT BE RESET BY DATA: ' + RESET_CANNOT)
    return rep


def waves_check(folder, log=print):
    """A folder after the step 'extras' -> [faults]. A folder without extras.json is a build with none of this (nothing to test).
      reset   every node the module switches in a round (ROLE, CAMP, the clock group's own) is named by the reset list or is one of
              RESET_CANNOT; the reset objects are the first two of the round-start event's list
      waves   every man: on the START's mesh part, WAVE_WALL from a wall, blind from the regions of his wave (Sight), far from the
              crew's places by the wave's rule; his post on the mesh and far in the same way; no two posts nearer than POST_GAP, none
              nearer than POST_OLD to a place of an old squad; phase D's posts LANE_CLEAR from the van's drive
      gating  each wave's squad is not in the world (field 3 = 0), is named only by its own timer, that timer only by ONE of the
              phase's trigger (start timer / beat box / plaza box), no free clock; no police behaviour names the van
      van     VAN_LATE: no FakeTarget on the van and its group hidden, shown by the clock group's 'Van_show' after the plaza box"""
    import json, kl_fa_bots as KB
    pj = os.path.join(folder, 'extras.json')
    if not os.path.isfile(pj):
        log('kl_fa_bank.waves_check %s: no extras.json: no waves, reset or late van in this folder' % folder)
        return []
    rep = json.load(open(pj))
    o = read_opts(folder)
    B = KB.Built(folder)
    sc, bad = B.sc, []
    def fail(s):
        bad.append(s); log('  FAIL ' + s)
    node = lambda path: (sc.resolve(path) or [None])[0]
    P = lambda p: '(%d, %d, %d)' % tuple(round(x) for x in p)
    # ---- who names what (one pass over every reference list of the level)
    named_by = collections.defaultdict(list)
    for k in range(1, len(sc.nodes)):
        for s in A.named(sc, k):
            named_by[s].append(k)
    # ---- reset
    if o['reset']:
        first = values(sc, node(R + ROLE['monitor']), 'AIMonitor')[2]
        r = [R + CLOCK + '\\Reset_show', R + CLOCK + '\\Reset_hide']
        if first[:2] != r:
            fail('the round-start event\'s list does not begin with the two reset objects: %s' % first[:3])
        show = values(sc, node(r[0]), 'ActivateGeom')[1] if node(r[0]) else []
        hide = values(sc, node(r[1]), 'DeactivateGeom')[1] if node(r[1]) else []
        want = target_lists(sc, module_nodes(sc))
        if o.get('van_late') and o.get('van_hide', True):
            want['hide'].append(R + VAN + '\\' + VAN_GROUP)
        for key, have, name in (('show', show, 'shown again'), ('hide', hide, 'hidden again')):
            lack = [s for s in want[key] if s not in have]
            if lack:
                fail('%d objects the module switches in a round are not %s by the reset: %s' % (len(lack), name, [x[-60:] for x in lack[:3]]))
        log('  reset: %d objects shown again, %d hidden again (what the round switches: the vault door\'s body and the intact vault come back; '
            'the blown vault, fire, smoke, the vault\'s loot%s, the sounds and the late van go); cannot be reset by data: %s' % (
                len(show), len(hide), ', the teller stacks' if o['teller_late'] else '', RESET_CANNOT))
    # ---- VAULT_SWING's round-2 pose and VAULT_BLOCKER
    cl = R + CLOCK + '\\'
    if o['reset'] and o.get('vault_swing') is not None:
        mon = values(sc, node(R + ROLE['monitor']), 'AIMonitor')[2]
        op, tm, st = node(cl + 'Reset_door_closed'), node(cl + 'Reset_door_timer'), node(cl + 'Reset_door_stop')
        if None in (op, tm, st) or cl + 'Reset_door_closed' not in mon or cl + 'Reset_door_timer' not in mon:
            fail('VAULT_SWING reset: the round start does not name the door pose objects: %s' % [x[-24:] for x in mon[:8]])
        elif (values(sc, op, 'AIDWrapper')[:2] != [[R + VAULT_DOOR], 'Activate'] or values(sc, st, 'AIDWrapper')[:2] != [[R + VAULT_DOOR], 'ForceStopAnim']
              or values(sc, tm, 'TriggerDelay2')[4] != [cl + 'Reset_door_stop'] or not 0 < values(sc, tm, 'TriggerDelay2')[0] < 1.0):
            fail('VAULT_SWING reset: the door pose objects do not send Activate then ForceStopAnim to %s' % VAULT_DOOR)
        else:
            log('  vault swing reset: round start -> door Activate -> %.2f s -> ForceStopAnim (round 2 starts with the door closed; GUESS)' % values(sc, tm, 'TriggerDelay2')[0])
    if o.get('vault_blocker'):
        pb = node(R + BLOCKER)
        if pb is None:
            fail('VAULT_BLOCKER: %s is not in the level' % BLOCKER)
        else:
            v = values(sc, pb, 'PathBlocker')
            if v[:2] != ['eUnblock', 'eBlocking'] or v[2] != [] or sc.cls(pb) != 'ZBoxPrimitive':
                fail('VAULT_BLOCKER: the blocker is %s %s, want ZBoxPrimitive [eUnblock, eBlocking, []]' % (sc.cls(pb), v[:3]))
            if R + BLOCKER not in values(sc, node(R + ROLE['door timer']), 'TriggerDelay2')[4]:
                fail('VAULT_BLOCKER: the door timer does not unblock %s' % BLOCKER)
            if o['reset']:
                rb = node(cl + 'Reset_blocker')
                if rb is None or values(sc, rb, 'AIDWrapper')[:2] != [[R + BLOCKER], 'Block']:
                    fail('VAULT_BLOCKER: no round-start Block of the blocker')
            else:
                log('  VAULT_BLOCKER without --reset: round 2 starts with the way open (no re-block)')
            log('  vault blocker: %s (eBlocking from the load) unblocked by the door timer at %.1f s after the beat' % (BLOCKER.split('!')[-1], DOOR_GONE))
    # ---- waves
    if rep['waves']:
        S = Sight(folder, B, log)
        old = [B.at(k) for t in sc.tops() if STAGE.get(sc.names[t]) or sc.names[t] in HALL for k in range(t + 1, sc.end[t]) if sc.cls(k) in ('ZFFActor', 'ZBoxPrimitive')]
        drive = ESC.Poly([tuple(p) for p in plan_of(os.path.join(folder, 'van.json'))['path']])
        every_post, every_entry, table = [], [], {w[0]: w for w in WAVE_TABLE}
        chains = {ph: [w for w in rep['waves'] if w['phase'] == ph] for ph in 'ABD'}
        for w in rep['waves']:
            tab = table[w['name']]
            near = CREW_CLEAR if w['phase'] == 'D' else o['waves_near']
            ref = [q for q in S.places if S.region(q) in tab[4]]
            t = node(w['squad'])
            if t is None:
                fail('wave %s: no squad %s' % (w['name'], w['squad'])); continue
            sv = values(sc, t, 'ZSquadScript')
            if sv[3] != 0:
                fail('wave %s: ZSquadScript field 3 is %r, the squad must not be in the world until its rout is named' % (w['name'], sv[3]))
            men = [(k, B.at(k)) for k in range(t, sc.end[t]) if sc.cls(k) == 'ZFFActor']
            d = node(w['squad'] + '\\10_Defend')
            posts = [B.at(c) for c in range(d + 1, sc.end[d]) if sc.parent[c] == d and sc.names[c].startswith('Pos#')] if d else []
            if len(men) != len(w['men']) or len(posts) != len(men):
                fail('wave %s: %d men and %d posts, %d planned' % (w['name'], len(men), len(posts), len(w['men'])))
            for k, p in men:
                nm = sc.path[k][5:].split('\\')[-2]
                h = S.nav.at(p[0], p[1], p[2], 120.0, S.home)
                if h is None:
                    fail('wave %s: %s at %s is not on the START\'s mesh part' % (w['name'], nm, P(p)))
                    continue
                if S.nav.clearance(p[0], h[1], p[2]) < WAVE_WALL - 1:
                    fail('wave %s: %s at %s is %d from a wall (%d wanted)' % (w['name'], nm, P(p), S.nav.clearance(p[0], h[1], p[2]), WAVE_WALL))
                seen = S.seen_by(p, tab[4])
                if seen:
                    fail('wave %s: %s at %s comes into the world IN SIGHT of a heister station of the %s at %s' % (w['name'], nm, P(p), seen[0], P(seen[1])))
                near_ = min(math.dist(p, q) for q in ref)
                if near_ < near:
                    fail('wave %s: %s at %s is %d from a heister station (%d wanted)' % (w['name'], nm, P(p), near_, near))
                if route_dist(p) < ROUTE_ENTRY[w['phase']]:
                    fail('wave %s: %s comes into the world at %s, %d from a leg of the way of the crew (%d wanted)' % (w['name'], nm, P(p), route_dist(p), ROUTE_ENTRY[w['phase']]))
                # run W2's fault: nobody comes into the world with a line to the START rows (where the human and the crew stand at the GO) or within 15 m of them
                if min(math.dist(p, r) for r in START) < START_CLEAR:
                    fail('wave %s: %s comes into the world at %s, %d from a START row (%d wanted)' % (w['name'], nm, P(p), min(math.dist(p, r) for r in START), START_CLEAR))
                lines = sorted({rl for r in START for rl in S.sees_by(p, tuple(r), RULES_X)})
                if lines:
                    fail('wave %s: %s comes into the world at %s WITH A LINE to a START row (%s)' % (w['name'], nm, P(p), ' '.join(lines)))
                if o.get('waves2') and w['phase'] in 'AB':
                    wo_ = way_out_sees(S, p)
                    if wo_:
                        fail('wave %s: %s comes into the world at %s IN SIGHT of the way out of the crew (%s): men would plop out in front of a returning crew' % (w['name'], nm, P(p), ', '.join(wo_)))
                for q, ph, dl, wn in every_entry:
                    if ph == w['phase'] and abs(dl - w['delay']) < ENTRY_REUSE and math.dist(p, q) < WAVE_GAP:
                        fail('wave %s: %s at %s is %d from the entry of a man of wave %s that comes at the same time' % (w['name'], nm, P(p), math.dist(p, q), wn))
                every_entry.append((p, w['phase'], w['delay'], w['name']))
            for p in posts:
                h = S.nav.at(p[0], p[1], p[2], 120.0, S.home)
                if h is None:
                    fail('wave %s: post %s is not on the START\'s mesh part' % (w['name'], P(p))); continue
                if S.nav.clearance(p[0], h[1], p[2]) < POST_WALL - 1:
                    fail('wave %s: post %s is %d from a wall (%d wanted)' % (w['name'], P(p), S.nav.clearance(p[0], h[1], p[2]), POST_WALL))
                for q in every_post:
                    if math.dist(p, q) < POST_GAP_MIN:
                        fail('wave %s: post %s SHARED: %d from another wave post (%d wanted)' % (w['name'], P(p), math.dist(p, q), POST_GAP_MIN))
                v2a = bool(o.get('waves2')) and w.get('post_cover') is not None            # every chain of a --waves2 build is at cover (the second skeptic)
                if route_dist(p) < ROUTE_POST[w['phase']] and not (v2a and w['phase'] == 'A'):
                    fail('wave %s: post %s stands %d from a leg of the way of the crew (%d wanted)' % (w['name'], P(p), route_dist(p), ROUTE_POST[w['phase']]))
                if v2a:                        # the route rule is relaxed ONLY at cover and POST_STATION_MIN from every heister station
                    if cover_dist(B, p) > w['post_cover'] + 1:
                        fail('wave %s: post %s is %d from a cover box (%d wanted: every chain stands at cover)' % (w['name'], P(p), cover_dist(B, p), w['post_cover']))

                    if route_dist(p) < POST_ROUTE_MIN - 1:
                        fail('wave %s: post %s stands %d from a leg of the way of the crew (%d wanted even at cover: the point-blank reach is 160)' % (w['name'], P(p), route_dist(p), POST_ROUTE_MIN))
                    if min(math.dist(p, q) for q in S.places) < POST_STATION_MIN - 1:
                        fail('wave %s: post %s is %d from a heister station (%d wanted)' % (w['name'], P(p), min(math.dist(p, q) for q in S.places), POST_STATION_MIN))
                    if w['phase'] != 'A' and route_dist(p) < ROUTE_POST[w['phase']] - 1:
                        fail('wave %s: post %s stands %d from a leg of the way of the crew (%d wanted)' % (w['name'], P(p), route_dist(p), ROUTE_POST[w['phase']]))
                if min(math.dist(p, r) for r in START) < START_CLEAR:
                    fail('wave %s: post %s is %d from a START row (%d wanted)' % (w['name'], P(p), min(math.dist(p, r) for r in START), START_CLEAR))
                lines = sorted({rl for r in START for rl in S.sees_by(p, tuple(r), RULES_X)})
                if lines:
                    fail('wave %s: post %s has a LINE to a START row (%s): the man would fire on the human at the GO' % (w['name'], P(p), ' '.join(lines)))
                every_post.append(p)
                if min(math.dist(p, q) for q in ref) < near:
                    fail('wave %s: post %s is %d from a heister station (%d wanted)' % (w['name'], P(p), min(math.dist(p, q) for q in ref), near))
                if min(math.dist(p, q) for q in old) < (POST_OLD_B if w['phase'] == 'B' else POST_OLD):
                    fail('wave %s: post %s is within %d of a place of an old squad' % (w['name'], P(p), POST_OLD_B if w['phase'] == 'B' else POST_OLD))
                if w['phase'] == 'D' and abs(drive.project(p)[1]) < LANE_CLEAR:
                    fail('wave %s: post %s is %d from the van\'s drive (%d wanted)' % (w['name'], P(p), abs(drive.project(p)[1]), LANE_CLEAR))
            # gating: rout <- Go <- (Pace [<- the previous Go or the phase's trigger], Fast [<- the previous squad's 'wiped out' list])
            rname = w['squad'] + '\\10_Defend'
            rout = node(rname)
            for what, path in (('Pace', w['pace']), ('Go', w['go'])) + ((('Fast', w['fast']),) if w.get('fast') else ()):
                if node(path) is None:
                    fail('wave %s: its %s node %s is not in the level' % (w['name'], what, path))
            by = [kk for kk in named_by.get(rname, ())]
            if by != [node(w['go'])]:
                fail('wave %s: its rout is named by %s, only by its Go node %s is wanted' % (w['name'], [sc.path[x][5:] for x in by], w['go']))
            gv = values(sc, node(w['go']), 'TriggerDelay2') if node(w['go']) else None
            if gv is not None:
                if abs(gv[0] - GO_DELAY) > 1e-6 or gv[2] >= 0:
                    fail('wave %s: Go is a delay of %g s with re-arm %g: a one-shot of %g s is wanted' % (w['name'], gv[0], gv[2], GO_DELAY))
                if w['go'] in gv[4] or rname not in gv[4]:
                    fail('wave %s: Go\'s list %s names itself or lacks the rout' % (w['name'], [x[-30:] for x in gv[4]]))
            ph_trig = R + (ROLE[WAVE_TRIGGER[w['phase']]] if WAVE_TRIGGER[w['phase']] else PLAZA_BOX)
            first = not chains[w['phase']] or chains[w['phase']][0] is w
            tb = [kk for kk in named_by.get(w['pace'], ())]
            want_pace = [node(ph_trig)] if first else [node(chains[w['phase']][chains[w['phase']].index(w) - 1]['go'])]
            if first and w['phase'] == 'A' and o.get('waves2'):             # the dock box and the backstop timer, no one else
                want_pace = sorted(x for x in (node(R + DOCK_BOX), node(R + DOCK_LATE)) if x)
                tb = sorted(tb)
            if first and w['phase'] in ('B', 'D') and o.get('wave_fallback'):      # WAVE_FALLBACK: the chain-A link's Go also names the first Pace of B and D
                want_pace = sorted(want_pace + [node(o['wave_fallback']['go'])])
                tb = sorted(tb)
            if o.get('van_nests') and w['phase'] == 'D':                  # VAN_NESTS: the cut link is named by nobody (off: the first). Without the option this block is not entered
                _kn = 0 if o['van_nests'] == 'off' else int(o['van_nests'][5:])
                if chains['D'].index(w) == _kn:
                    want_pace = []
            if 'waveb' in o.get('van_quiet', ()) and w['phase'] == 'B' and first:      # VAN_QUIET waveb: Pace_B01 is named by nobody. Without the option this block is not entered
                want_pace = []
            if 'wavea4' in o.get('van_quiet', ()) and w['phase'] == 'A' and chains['A'].index(w) == 3:      # VAN_QUIET wavea4: Pace_A04 is named by nobody. Without the option this block is not entered
                want_pace = []
            for e_, q_ in w['men']:                                       # the walk from the entry to the post keeps 15 m from the START rows
                dd_ = min(seg_dist(r, e_, q_) for r in START)
                if dd_ < START_CLEAR:
                    fail('wave %s: the walk %s -> %s passes %d from a START row (%d wanted)' % (w['name'], tuple(e_), tuple(q_), dd_, START_CLEAR))
            if tb != want_pace:
                fail('wave %s: its Pace is named by %s, only by %s is wanted' % (w['name'], [sc.path[x][5:] for x in tb], 'the trigger ' + ph_trig if first else 'the previous link\'s Go'))
            pv = values(sc, node(w['pace']), 'TriggerDelay2') if node(w['pace']) else None
            if pv is not None:
                if pv[0] < 0.05 or abs(pv[0] - w['gap']) > 1e-6 or pv[2] >= 0 or node(w['go']) not in [x for s_ in pv[4] for x in sc.resolve(s_)]:
                    fail('wave %s: Pace is %g s (re-arm %g) naming %s: a one-shot delay of %g s naming Go is wanted' % (w['name'], pv[0], pv[2], [x[-20:] for x in pv[4]], w['gap']))
            if w.get('fast'):
                fv = values(sc, node(w['fast']), 'TriggerDelay2')
                prev = chains[w['phase']][chains[w['phase']].index(w) - 1]
                if abs(fv[0] - LATCH_DELAY) > 1e-6 or fv[4] != [w['go']]:
                    fail('wave %s: Fast is %g s naming %s: %g s naming Go is wanted' % (w['name'], fv[0], fv[4], LATCH_DELAY))
                fb = [kk for kk in named_by.get(w['fast'], ())]
                if fb != [node(prev['squad'])] or values(sc, node(prev['squad']), 'ZSquadScript')[8] != [w['fast']]:
                    fail('wave %s: the latch: Fast is named by %s, only by the \'wiped out\' list of %s is wanted' % (w['name'], [sc.path[x][5:] for x in fb], prev['name']))
            elif o.get('waves_latch', False) and chains[w['phase']].index(w) > 0:
                fail('wave %s: no Fast node although the latch is on' % w['name'])
            if o.get('waves2') and w.get('post_cover') and w['phase'] != 'A' and w['post_cover'] > POST_COVER:
                log('  note: wave %s stands within %d of cover, not %d: the mesh has no place nearer for its men' % (w['name'], w['post_cover'], POST_COVER))
            log('  wave %-4s phase %s %+4.0f s (gap %g): %d men %s; posts %s (%s apart)' % (w['name'], w['phase'], w['delay'], w['gap'], len(men),
                                                                                  ' '.join(P(p) for _k, p in men), ' '.join(P(p) for p in posts), w.get('post_gap')))
        # ---- the chains as a whole: finite, in order, a delay in every loop of links, a floor of SUPPLY_MIN seconds for the first phase
        for ph, ch in chains.items():
            if not ch:
                continue
            t = 0.0
            for i_, w in enumerate(ch):
                t += w['gap']
                if abs(t - w['delay']) > 1e-6:
                    fail('chain %s: wave %s is stored at +%g s, the gaps add up to +%g s' % (ph, w['name'], w['delay'], t))
                go_ = node(w['go'])
                nxt_ = ch[i_ + 1] if i_ + 1 < len(ch) else None
                if ph == 'D' and o.get('van_nests') and o['van_nests'] != 'off' and i_ + 1 == int(o['van_nests'][5:]):
                    nxt_ = None                                       # VAN_NESTS keep=N: the chain ends here, by design
                if ph == 'A' and 'wavea4' in o.get('van_quiet', ()) and i_ + 1 == 3:
                    nxt_ = None                                       # VAN_QUIET wavea4: chain A ends at A03, by design
                # reachable from Go: Pace of the next link and nothing else of the chain
                names_ = [x for s_ in values(sc, go_, 'TriggerDelay2')[4] for x in sc.resolve(s_)] if go_ else []
                tim_ = [x for x in names_ if sc.cls(x) == 'ZBoxPrimitive' and x != node(w['squad'] + '\\10_Defend')]
                if o.get('wave_fallback') and go_ == node(o['wave_fallback']['go']):         # WAVE_FALLBACK: this Go also names the first Pace of B and D (shot once, they do not chain back)
                    _cl = o['wave_fallback']['go'].rsplit('\\', 1)[0] + '\\'
                    tim_ = [x for x in tim_ if x not in (node(_cl + 'Pace_B01'), node(_cl + 'Pace_D01'))]
                if nxt_ is None and tim_:
                    fail('chain %s ends in %s which still names %s: a chain that does not stop' % (ph, w['name'], [sc.path[x][5:] for x in tim_]))
                if nxt_ is not None and node(nxt_['pace']) not in names_:
                    fail('chain %s: Go of %s does not arm the Pace of %s' % (ph, w['name'], nxt_['name']))
            if t > SUPPLY_MAX:
                fail('chain %s runs %g s: past SUPPLY_MAX (%g s), a chain must end' % (ph, t, SUPPLY_MAX))
            log('  chain %s: %d links, the first %g s after its trigger, the last %g s, %d men; Pace gaps %s' % (ph, len(ch), ch[0]['delay'], t, sum(len(w['men']) for w in ch), sorted({w['gap'] for w in ch})))
        floor = SUPPLY_MIN2 if o.get('waves2') else SUPPLY_MIN
        _lastA = chains['A'][2] if chains['A'] and len(chains['A']) > 3 and 'wavea4' in o.get('van_quiet', ()) else (chains['A'][-1] if chains['A'] else None)   # VAN_QUIET wavea4: A04 never comes
        if chains['A'] and _lastA['delay'] < floor:
            fail('the supply ends at %g s, before the floor (%g s): chain A alone must outlast a human who takes his time' % (_lastA['delay'], floor))
        elif not chains['A']:
            fail('no chain A: nothing keeps the police coming from the start of the round')
        # ---- run W2's two other faults. (1) NO WAVE BEFORE THE CREW HAS LEFT THE YARD: chain A is named by the dock box (behind the door, criminals only, once) and
        # by a backstop of A_BACKSTOP s after the start timer - not by the round-start timer itself, which put three men among the START rows at GO + 3.5 s
        if chains['A']:
            first_ = chains['A'][0]
            by_ = sorted(sc.path[x][5:] for x in named_by.get(first_['pace'], ()))
            if not o.get('waves2'):
                fail('chain A starts from the round-start timer (%s): a wave comes into the yard while the crew stands in it (run W2); build with --waves2' % by_)
            else:
                bk = node(R + DOCK_BOX)
                bv = values(sc, bk, 'TriggerBox') if bk else None
                if bv is None:
                    fail('chain A: the dock box %s is not in the level' % DOCK_BOX)
                else:
                    bp, bh = B.at(bk), kl_fa.node_values(sc, bk)[8:11]
                    if bv[17] != [first_['pace']] or bv[14] != 'ECPS_FA_MERCONLY' or bv[BOX_PER_MAN] != 0:
                        fail('chain A: the dock box fires %r for %r (once = %r): only %s, criminals only, once, is wanted' % (bv[17], bv[14], bv[BOX_PER_MAN], first_['pace']))
                    if bp[2] + bh[2] >= DOCK_DOOR_Z - 20:
                        fail('chain A: the dock box reaches z %d, the dock door is at z %d: it must lie wholly beyond the door (the crew has left the yard)' % (bp[2] + bh[2], DOCK_DOOR_Z))
                    lt = node(R + DOCK_LATE)
                    lv_ = values(sc, lt, 'TriggerDelay2') if lt else None
                    if lv_ is None or lv_[4] != [first_['pace']] or lv_[0] < 60.0 or [sc.path[x][5:] for x in named_by.get(R + DOCK_LATE, ())] != [sc.path[node(R + ROLE['start timer'])][5:]]:
                        fail('chain A: the backstop timer is missing, under 60 s, or not named by the start timer alone')
                    log('  chain A: starts when a criminal passes the dock box (%d, %d, %d) half %s, or at the latest %g s after the start timer; first wave %g s later' % (*[round(v) for v in bp], tuple(round(v) for v in bh), A_BACKSTOP, first_['gap']))
        # (2) GUNS ON THE START ROWS in the first minute: the waves add none to the 61 enemies' (start_pressure, the three sight rules)
        men_ = start_men(B, rep, bool(o.get('waves2')))
        all_ = start_pressure(S, men_)
        old_ = start_pressure(S, [m_ for m_ in men_ if m_['kind'] == 'old'])
        for T_ in all_:
            extra_ = [n_ for n_ in all_[T_]['any'] if n_ not in old_[T_]['any']]
            if extra_ or all_[T_]['near15'] > old_[T_]['near15']:
                fail('GO+%g s: the waves add %d gun(s) bearing on a START row (%s) and %d within 15 m with a line: the 61 enemies alone bear %d (%d within 15 m)' % (
                    T_, len(extra_), ' '.join(extra_[:4]), all_[T_]['near15'] - old_[T_]['near15'], len(old_[T_]['any']), old_[T_]['near15']))
        log('  guns on the START rows (any of the three sight rules, within %d m): GO+%s s: with the waves %s, the 61 enemies alone %s' % (
            PRESSURE_RANGE / 100, '/'.join('%g' % T_ for T_ in all_), '/'.join(str(len(all_[T_]['any'])) for T_ in all_), '/'.join(str(len(old_[T_]['any'])) for T_ in old_)))
        # no loop of timers without a delay: every TriggerDelay2 of the clock group has a delay, and no node of the group names a node that comes before it in a chain
        for k_ in range(1, len(sc.nodes)):
            if sc.path[k_].startswith(R + CLOCK + '\\') and sc.cls(k_) == 'ZBoxPrimitive' and kl_fa.has(sc, k_, 'TriggerDelay2'):
                v_ = values(sc, k_, 'TriggerDelay2')
                if v_[0] < 0.05:
                    fail('%s: a delay of %g s (a loop of links would run without a delay)' % (sc.path[k_][5:], v_[0]))
                if sc.path[k_] in v_[4]:
                    fail('%s names itself' % sc.path[k_][5:])
                for s_ in v_[4]:
                    if not sc.resolve(s_):
                        fail('%s names %s, which is not in the level' % (sc.path[k_][5:], s_))
        log('  waves: %d men in %d squads, %d posts; every man blind from his wave\'s regions (sight shapes), clear of the crew\'s %d stations' % (
            len(every_entry), len(rep['waves']), len(every_post), len(S.places)))
    # ---- the teller stacks (TELLER_LATE): hidden at the load, off the beat's list, shown by the clock group after the plaza box
    if o['teller_late'] and rep.get('teller'):
        ts = node(R + CLOCK + '\\Teller_show')
        want = teller_stacks(B)
        have = values(sc, ts, 'ActivateGeom')[1] if ts else []
        if ts is None or sorted(have) != sorted(want) or not want:
            fail('TELLER_LATE: Teller_show names %d objects, %d teller stacks are hidden' % (len(have), len(want)))
        lo = values(sc, node(R + ROLE['loot on']), 'ActivateGeom')[1]
        if [s_ for s_ in lo if s_ in want]:
            fail('TELLER_LATE: the loot list of the beat still shows %d teller stack(s)' % len([s_ for s_ in lo if s_ in want]))
        tt = node(R + CLOCK + '\\Timer_teller')
        if o.get('teller_foyer'):
            tc = node(R + CLOCK + '\\Timer_teller_c')
            if tt is None or tc is None or [kk for kk in named_by.get(R + CLOCK + '\\Timer_teller', ())] != [node(R + ROLE['speak box'])] \
                    or [kk for kk in named_by.get(R + CLOCK + '\\Timer_teller_c', ())] != [node(R + PLAZA_BOX)]:
                fail('TELLER_FOYER: the teller timer is not named by the foyer box alone, or its backstop by the plaza box alone')
            elif abs(values(sc, tt, 'TriggerDelay2')[0] - TELLER_FOYER_S) > 1e-6 or values(sc, tt, 'TriggerDelay2')[4] != [R + CLOCK + '\\Teller_show']:
                fail('TELLER_FOYER: the foyer timer is not %g s naming Teller_show' % TELLER_FOYER_S)
            log('  tellers: %d stacks hidden at the load, shown %g s after the FOYER box (the crew is in the hall then: a human who holds the front is paid), or 1 s after the plaza box' % (len(want), TELLER_FOYER_S))
        else:
            if tt is None or [kk for kk in named_by.get(R + CLOCK + '\\Timer_teller', ())] != [node(R + PLAZA_BOX)]:
                fail('TELLER_LATE: the teller timer is not named by the plaza box alone')
            log('  tellers: %d stacks hidden at the load, shown %g s after the plaza box (the crew has crossed the hall), not by the beat' % (len(want), TELLER_SHOW))
    # ---- the van
    if o['van_late']:
        vg = node(R + VAN + '\\' + VAN_GROUP)
        fakes = [k for k in range(vg, sc.end[vg]) if any(sc.p.key(c[0]) == 'FakeTarget' for c in sc.nodes[k]['ctrls'])]
        if o['van_no_target'] and fakes:
            fail('VAN_LATE: the van still carries a FakeTarget (%d)' % len(fakes))
        if o['van_hide']:
            if not B.ents[vg - 1].flags & HIDDEN:
                fail('VAN_LATE: the van\'s group is not hidden at the load')
            vs = node(R + CLOCK + '\\Van_show')
            if vs is None or values(sc, vs, 'ActivateGeom')[1] != [R + VAN + '\\' + VAN_GROUP]:
                fail('VAN_LATE: no ActivateGeom of the van group in the clock group')
            tv = node(R + CLOCK + '\\Timer_van')
            if tv is None or [kk for kk in named_by.get(R + CLOCK + '\\Timer_van', ())] != [node(R + PLAZA_BOX)]:
                fail('VAN_LATE: the van\'s timer is not named by the plaza box alone')
            tb_ = node(R + CLOCK + '\\Timer_van_b')
            if tb_ is None or [kk for kk in named_by.get(R + CLOCK + '\\Timer_van_b', ())] != [node(R + ROLE['beat box'])]:
                fail('VAN_LATE: the backstop timer of the van is not named by the ante-room box alone')
            elif tv is not None and not values(sc, tv, 'TriggerDelay2')[0] < values(sc, tb_, 'TriggerDelay2')[0]:
                fail('VAN_LATE: the backstop is not later than the plaza box timer')
            tc_ = node(R + CLOCK + '\\Timer_van_c')                 # review fault 6: the earlier event, the foyer box
            if tc_ is None or [kk for kk in named_by.get(R + CLOCK + '\\Timer_van_c', ())] != [node(R + ROLE['speak box'])]:
                fail('VAN_LATE: the foyer timer of the van is not named by the foyer box alone')
            elif not values(sc, tc_, 'TriggerDelay2')[4] == [R + CLOCK + '\\Van_show']:
                fail('VAN_LATE: the foyer timer does not show the van')
            log('  van: shown by the foyer box + %g s, by the plaza box + %g s, or (backstop) by the ante-room box + %g s: the first of the three, the others do the same again' % (
                VAN_FOYER, VAN_SHOW, VAN_BACKSTOP))
        # nothing a police behaviour names, before the call: every rout / search box / squad list that names the van or below it
        vn = {R + sc.path[k][5:] if not sc.path[k].startswith(R) else sc.path[k] for k in range(vg, sc.end[vg])}
        bad_by = []
        for t in sc.tops():
            if STAGE.get(sc.names[t]) or sc.names[t] in HALL or sc.names[t].startswith(WAVE_G + 'Wave_'):
                for k in range(t, sc.end[t]):
                    if any(s in vn for s in A.named(sc, k)):
                        bad_by.append(sc.path[k][5:])
        if bad_by:
            fail('VAN_LATE: %d police behaviours name the van: %s' % (len(bad_by), bad_by[:3]))
        log('  van: %s; the group is %s at the load; nothing of the police names it (%d squad trees read)' % (
            'no FakeTarget on it' if not fakes else '%d FakeTarget(s) on it' % len(fakes), 'hidden' if B.ents[vg - 1].flags & HIDDEN else 'shown', len(
                [1 for t in sc.tops() if STAGE.get(sc.names[t]) or sc.names[t] in HALL])))
    log('kl_fa_bank.waves_check %s: %s' % (folder, 'PASS' if not bad else '%d FAILED' % len(bad)))
    return bad


def build(out, log=print, plan=None):
    """F07 + M03_A with the layer into <out>/F07+M03_A campaign -> (kl_maps.one's result, that folder, the van's
    plan, kl_map_escape's report of what it did to the van). plan: a plan of ROAD (plan_of / van_plan); None = made
    here, on a BARE graft of the two levels built into <out>/_bare (60 s, 310 MB) and deleted again - the plan
    needs a built level's collision and must not see the layer's own van (van_plan)."""
    import shutil
    name = '%s+%s campaign' % (HOST, LEVEL)
    if plan is None:
        bare = os.path.join(out, '_bare')
        r = kl_maps.one(bare, HOST, LEVEL, keep=True, campaign=True, tag=' campaign')
        try:
            if not r.get('ok'):
                raise ValueError('kl_fa_bank: the bare graft for the van\'s plan did not build: %s at %s' % (r.get('error'), r.get('where')))
            plan = van_plan(os.path.join(bare, name), log)
        finally:
            shutil.rmtree(bare, ignore_errors=True)
    lay_van(plan)
    r, st = {}, {}
    import kl_snd
    kl_snd.VOICE = True if VOICE else None              # the speech repairs of re/voice.md (kl_maps.ready_one's way; kl_fa_club's): streamed single ADPCM lines -> the .WAV
    try:
        with ESC.van_layer(plan, log) as st, doors(log):
            r = kl_maps.one(out, HOST, LEVEL, keep=True, campaign=True, tag=' campaign', author='kl_fa_bank')
    except ValueError:                                  # van_layer: 'a step of the van did not run'. After a build that
        if r.get('ok') or not r:                        # failed (r says why) that is no news; after one that did not, it is
            raise
    finally:
        kl_snd.VOICE = None
    return r, os.path.join(out, name), plan, {k: st.get(k) for k in ('van', 'wired', 'hvk')}


def test(out, keep=False, log=print, plan=None):
    """Build the level with the layer into <out>, finish it, check it. -> 0 or 1. Beside the archive: van.json
    (the van's plan, what was done to F07's van, kl_map_escape.van_check's report: kl_map_escape.van_build's form)."""
    import json
    r, folder, plan, did = build(out, log, plan)
    if not r.get('ok'):
        log('BUILD FAILED: %s at %s' % (r.get('error'), r.get('where')))
        return 1
    late = finish(folder, log)
    write_opts(folder)                                  # the flags in force travel with the build: the chain's steps and check() read them
    L = ESC.Level(folder)
    with open(os.path.join(folder, 'van.json'), 'w', encoding='utf-8') as f:
        json.dump(collections.OrderedDict(tag=LEVEL, plan=plan, van=did['van'], wired=did['wired'], hvk=did['hvk'], check=ESC.van_check(L, lambda *a: None, plan)),
                  f, indent=1, default=str)
    bad = check(folder, log, r['problems']) + late
    log('level: %d entities, %d rooms, %.0f MB' % (r['entities'], r['rooms'], r['archive_mb']))
    if not keep:
        for f in os.listdir(folder):
            if '_Main' in f:
                os.remove(os.path.join(folder, f))
    log('RESULT: %s' % ('PASS' if not bad else 'FAIL'))
    return 1 if bad else 0


def main():
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == 'test':
        global DOOR_WAIT, DOORS_ANIMATE, VAULT_OPEN, VAULT_DOOR_GOES, VAULT_SWING_END, GATE_VAULT, CASE, BEAT, NO_AI, ALARM_LIGHTS, VAULT_BLAST, STOCK_ROWS, MUSIC_LAYER4
        global PLAZA_OUTSIDE, HALL_UP, CREW_FIX2, TELLER_LATE, VAN_LATE, VAN_HIDE, VAN_NO_TARGET, RESET, WAVES, WAVES_EXTRA, WAVES_NEAR, TELLER_MORE, WAVES_LATCH
        global WAVES2, VOICE, TELLER_FOYER, WAVE_TABLE, ROOM_GATES, ROOM_ON, ROOM_HIDE, STAGING, GARRISON, VAULT_BLOCKER
        GARRISON = '--garrison' in a                        # the garrison and the beat's police in pockets off the crew's line, holding their places (GARRISON_PLACES); needs --gates and --staging
        if GARRISON and not ('--gates' in a and '--staging' in a):
            raise ValueError('--garrison needs --gates and --staging')
        STAGING = '--staging' in a                          # the squads of the way in sleep and are woken room by room (WAKE_SQUADS); needs --gates and enemies
        if STAGING and '--gates' not in a:
            raise ValueError('--staging needs --gates (the gates lists wake the next room)')
        ROOM_GATES = '--gates' in a                       # the room gates of run W4's fix (the delivered flag set has it)
        ROOM_HIDE = '--gates-seen' not in a
        if '--gate-rooms' in a:
            ROOM_ON = tuple(a[a.index('--gate-rooms') + 1].split(','))
        W = '--waves' in a or '--waves2' in a               # the waves build: implies the crew fix, its second part, the reset, the late van
        WAVES2 = '--waves2' in a                            # the second tuning (after run W2): chain A from the dock box, inside posts, registers from the foyer
        TELLER_FOYER = WAVES2 and '--no-teller-foyer' not in a
        VOICE = '--voice' in a
        WAVE_TABLE = chain_table(v2=WAVES2)
        PLAZA_OUTSIDE = '--plaza-outside' in a or '--crew-fix' in a or W   # the crew fix after run V2 (both off = the build of V0 .. V2)
        HALL_UP = '--hall-gallery' in a or '--crew-fix' in a or W
        CREW_FIX2 = '--crew-fix2' in a or W
        TELLER_LATE = '--teller-late' in a or W
        TELLER_MORE = '--teller-more' in a or (W and '--no-teller-more' not in a)
        WAVES_LATCH = '--waves-latch' in a
        VAN_LATE = '--van-late' in a or (W and '--no-van-late' not in a)
        VAN_HIDE = '--no-van-hide' not in a
        VAN_NO_TARGET = '--no-van-target-off' not in a
        RESET = '--reset' in a or W
        WAVES = W
        if '--waves-extra' in a:
            WAVES_EXTRA = int(a[a.index('--waves-extra') + 1])
            if not 0 <= WAVES_EXTRA <= WAVES_ACTORS[0] - 68:
                raise ValueError('--waves-extra: 0 .. %d (WAVES_ACTORS %d less the 68 actors there are)' % (WAVES_ACTORS[0] - 68, WAVES_ACTORS[0]))
        if '--waves-near' in a:
            WAVES_NEAR = float(a[a.index('--waves-near') + 1])
        set_dash()
        MUSIC_LAYER4 = '--music-layer4' in a
        NO_AI = '--no-ai' in a
        ALARM_LIGHTS = '--alarm-lights' in a
        VAULT_BLAST = None if '--no-blast' in a else 'real' if '--blast-real' in a else VAULT_BLAST
        STOCK_ROWS = '--dead-men-rows' not in a
        DOORS_ANIMATE = '--doors-animate' in a
        VAULT_OPEN = '--vault-open' in a
        DOOR_WAIT = '--door-early' not in a
        VAULT_DOOR_GOES = '--vault-stays' not in a
        VAULT_SWING_END = None
        if '--vault-swing' in a:                        # OPTION (optional seconds): the vault door's swing is played out, then its body goes
            if not VAULT_DOOR_GOES or VAULT_OPEN:
                raise ValueError('--vault-swing: the door must go at all (not with --vault-stays or --vault-open)')
            i_ = a.index('--vault-swing') + 1
            VAULT_SWING_END = float(a[i_]) if i_ < len(a) and not a[i_].startswith('-') and a[i_][:1].isdigit() else SWING_DEFAULT
            if VAULT_SWING_END < 8.0:
                raise ValueError('--vault-swing: the clip is 8 s long, the body must stay for it')
        VAULT_BLOCKER = '--vault-blocker' in a
        if VAULT_BLOCKER and (not VAULT_DOOR_GOES or VAULT_OPEN):
            raise ValueError('--vault-blocker: the door must go at all (not with --vault-stays or --vault-open); the path opens when it swings')
        GATE_VAULT = '--loot-shown' not in a
        CASE = None if '--loot-bags' in a else CASE
        if '--beat' in a:                               # OPTION, seconds from the ante-room box to the vault door
            BEAT = float(a[a.index('--beat') + 1])
        if '--str' in a:                                # OPTION: the stream file that holds the map's music (kl_vault_str.py)
            use_stream(a[a.index('--str') + 1])
        plan = plan_of(a[a.index('--plan') + 1]) if '--plan' in a else None
        sys.exit(test(a[1], '--keep' in a, plan=plan))
    elif len(a) == 2 and a[0] == 'finish':
        sys.exit(1 if finish(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'check':
        sys.exit(1 if check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'inventory':
        inventory(a[1])
    elif len(a) >= 3 and a[0] == 'bots':
        if '--loot-seconds' in a:   # the loot wait of every stop (GUESS; default BOT_OPT 30 unchanged)
            BOT_OPT['loot_seconds'] = int(a[a.index('--loot-seconds') + 1])
        out, _rep = bots(a[1], a[2], gates=True if '--gates' in a else None, hide=False if '--gates-seen' in a else None,
                         rooms=a[a.index('--gate-rooms') + 1].split(',') if '--gate-rooms' in a else None)       # --gate-rooms: the rooms gated (ROOMS names); the timetable refuses past the budget
        sys.exit(1 if any(x[0] == 'FAIL' for x in out) or bots_check(a[2]) else 0)
    elif len(a) == 3 and a[0] == 'dyn':
        out, _rep = dyn(a[1], a[2])
        sys.exit(1 if any(x == 'FAIL' for x, _t in out) else 0)
    elif len(a) == 2 and a[0] == 'garrison-check':
        sys.exit(1 if garrison_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'pressure-check':
        sys.exit(1 if pressure_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'dyn-check':
        sys.exit(1 if dyn_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'stage-check':
        sys.exit(1 if staging_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'rooms-check':
        sys.exit(1 if rooms_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'bots-check':
        sys.exit(1 if bots_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'seal':
        seal(a[1])
    elif len(a) == 2 and a[0] == 'hall-dash':
        hall_dash(a[1])
    elif len(a) == 2 and a[0] == 'vault-blow':
        vault_blow(a[1])
    elif len(a) in (2, 3) and a[0] == 'wave-fallback':      # <src> [<dst>]: waves B and D also from the round clock (WAVE_FALLBACK)
        wave_fallback(a[1], a[2] if len(a) == 3 else None)
    elif len(a) == 4 and a[0] == 'van-nests':                # <src> <dst> off|keep=N: chain D (the street recess police) not started / cut after N waves (VAN_NESTS)
        van_nests(a[1], a[2], a[3])
    elif len(a) == 4 and a[0] == 'van-quiet':                # <src> <dst> <plaza,waveb,wavea4,exit>|top: unlink more van-route police from their starters (VAN_QUIET)
        van_quiet(a[1], a[2], a[3])
    elif len(a) == 3 and a[0] == 'extras':
        extras(a[1], a[2])
    elif len(a) == 2 and a[0] == 'waves-check':
        sys.exit(1 if waves_check(a[1]) else 0)
    elif len(a) >= 2 and a[0] == 'start-guns':
        start_guns(a[1:])
        sys.exit(1 if FAILED else 0)
    elif len(a) == 2 and a[0] == 'crew-check':
        sys.exit(1 if crew_check(a[1]) else 0)
    elif len(a) == 2 and a[0] == 'reverify':
        bad = reverify(a[1])
        print('kl_fa_bank.reverify %s: problems: %d' % (a[1], len(bad)))
        sys.exit(1 if bad else 0)
    else:
        print(__doc__)


if __name__ == '__main__':
    import kl_fa_bank                   # kl_graft imports this file by name: one module, one set of flags
    kl_fa_bank.main()
