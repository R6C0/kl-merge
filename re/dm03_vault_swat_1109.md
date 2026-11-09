# DM03 Withdrawal (slot F03): SWAT at the back + a blow-up vault door with loot + more kick doors (design, 2026-11-09)

Owner (11-09, live): (a) "more SWAT at the back, even where the van spawns"; the front of the store stays normal police (11-08: "no swat cops at the
front of the store, just the normal cops", the `frontcops` part of `tools/kl_dm03cops_1108.py` stands). (b) "more loot rooms. The door just before the
garage is two doors in the original game, like a vault in the campaign FA: make that a door you can BLOW UP with a good bit of loot behind it. More
doors you can kick down. It needs to feel interactive and make the player more immersed."

Written in the cloud WITHOUT the game files. Everything below comes from the repo (file / line cited); what needs the zip is marked
**NEEDS ZIP**. The read-only scanner `tools/kl_dm03_scan_1109.py` answers those lines in one run:

    python tools/kl_dm03_scan_1109.py C:\kl_build_1024\dm03cops_1108\F03_Main.zip --out C:\kl_build_1024\dm03scan_1109.json
    python tools/kl_dm03_scan_1109.py <zip> --near 0,240,-6400 --radius 2500        (the garage / vault lobby / security hall only)

Code delivered with this note: the `backswat` part of `tools/kl_dm03cops_1108.py` (default OFF; `tools/kl_dm03cops_1108_test.py`), the scanner
(`tools/kl_dm03_scan_1109_test.py`). The vault-door tool is NOT written: its entity data is not certain from the repo (section 2.1).

## 1. SWAT at the back

### 1.1 The SWAT form in DM03's own data (what makes a man SWAT)

| field | police (what frontcops / allpolice write) | SWAT | source |
|---|---|---|---|
| ZFFActor field 4 + entity model | 59361 | **59891** | `kl_dm03cops_1108.py` docstring lines 15-20 ("Army-form (model 59891)"); `re/fed_kit.md` 3.2: "The map's own Dead Men SWAT: `--body reinforcement` (59891)"; `re/fed.md` 151: M03 `ArrivingCops_Squad_02\Reinforcement_03 / 04` (model 59891) |
| ZFFActor field 10 (animation set) | `...#Police` (`front_edit` checks `tp[10].endswith('#Police')`, line 138) | the 59891 men's own string | **NEEDS ZIP** (the suffix; the guard `SWAT['anm_not'] = '#Police'` only refuses a police set) |
| ZFFActor field 20 (weapon) | `SMG_Type79` / `Shotgun_Hawk_Bullpup` (`FRONT_MEN`, line 60) | each 59891 man's own weapon (field 20), cycled | **NEEDS ZIP** for the names (GUESS: rifles, as M02's PoliceSwats carry AK-74 / SCAR, `re/fed.md` 150) |
| ZSoldier controller (the soldier row: class, health, accuracy) | the BankMain police's (eGuard, 125 hp; `POLICE_TMPL` 7029) | the 59891 man's own controller, copied whole | `front_edit` copies the template's ZSoldier body (lines 156-158); the SWAT row's values **NEEDS ZIP** (GUESS eArmy-class, ~175 hp like M02's PoliceSwats) |

Template entities in DM03 (live node ids, from the cops tool): `ParkingLotSWAT_01` men **7036, 7038, 7045** and `ArrivingCops_Squad_02` men **6953, 6955**
are 59891 in the live pre-cops zip (`FRONT_MEN`, line 60: `front_edit` asserts model 59891 on each before the swap) - but the cops stage turns exactly
these into police, so in the cops OUTPUT they are no template any more. The men that STAY 59891 after `frontcops` + `allpolice` are
`AI_Enemies!ArrivingCops_Squad_01` and `AI_Enemies!EscSquad` (docstring line 17/19: "NOT touched ... stay Army"); their node ids are not in the repo
(**NEEDS ZIP**; the tool resolves them by path at build time: `SWAT['template_squads']`). KL_Cover!Squad_01..03 cops (6, z -7300..-9990) were 59891
too and are police since `allpolice`.

Decision: the SWAT form = the first ZFFActor of model 59891 under those two squads (node order, deterministic), fields 4 / 10 / 20 + ZSoldier copied,
weapons cycled over all template men's own weapons. It is the exact reverse of the proven `frontcops` swap (DM03_1109 bench: 0 faults, "cops hit
bots"). GUESS (same class as frontcops' GUESS): the SWAT animation set runs Defend / Hunt routs. If the scan shows the ArrivingCops_Squad_01 /
EscSquad actors carry a seat-specific ZSoldier (car arrivals), take `ParkingLotSWAT_01`'s values from the LIVE pre-cops zip instead (`--parts` of a full
restage: not built, the increment path is the one coded).

### 1.2 The `backswat` part (coded, default OFF, an increment on the cops output)

`python tools/kl_dm03cops_1108.py stage --parts backswat --in-dir C:\kl_build_1024\dm03cops_1108` (or `...\doors_1108\DM03`) -> `C:\kl_build_1024\dm03backswat_1109`
with install.py / INSTALL / UNDO bats (tag `.before-dm03backswat_1109`), build_report.json (template, weapons, van anchor, the 4 cells).
Input pins (`BS_INPUTS`): the cops output da7b3642 / 0b90ab32 or the doors output 33d1fa5f / 2971ec6d; `--accept-input` takes another zip and pins it.
It runs ALONE (`validate_parts`), never with the five 1108 parts; `--parts` default is still the five, so the 1108 stage is byte-identical.

1. In place: the 6 `KL_Garage!Back` + 5 `KL_Ramp!Wave` police (model 59361, asserted) take the SWAT form of 1.1 (`swat_edit`). The ramp wave then comes
   down the ramp and through the garage as SWAT (the `ramp` part's Hunt rout is untouched).
2. One new squad `KL_BackSwat!Van` (4 men, `VAN_SWAT['n']`), its own clock `KL_BackSwat!Clock\Go` (0.1 s, appended to the AIMonitor start list as
   `KL_Squads!Clock\Go` is), Defend-only on 4 home-part nav cells chosen at build time round the escape van's STOP (`kl_fa_bots.van_drives`, key
   `VAN_SWAT['anchor']`): within 15 m, at least 5 m from it, 2.5 m off the van's lane (`kl_fa_bots.lane_dist`), outside every escape box
   (`kl_doors_clear_1108.escape_things`, grown 1.3), 2.2 m apart, 60 cm wall clearance, each man facing the van. Men are clones of the BankMain police
   groups (as the garage squad's) re-formed to SWAT in Maker space (`reform_node`), so no car-seat group is cloned.
   `anchor='wait'` would put them at the van's hidden start pocket instead (DM03 van start is HIDDEN, `re/vehicle_routes_1108.md` 72; likely off-mesh -> the
   build refuses when no cells are found). GUESS: 4 SWAT at the stop is what "SWAT where the van spawns" means to the owner.
3. Budget: cops output 44 actors / 29 squads -> **48 / 30** of the engine-proven 99 / 55 (`budget_ok`, census asserted after the join).
4. Unchanged: front street (`frontcops`), `EscSquad` / `ArrivingCops_Squad_01` (SWAT already), `KL_Cover` cops (police), `carexit` routs.
   Members changed: .prp .gms .buf .oct .rmi .rmc (.prm root re-pointing only when records move), both zips; `kl_fa_bank.seal` / `reverify` run as in 1108.

Van facts from the repo: DM03 van = stock F07's key-framed `V_Van_00` laid on the Dead Men alley; drive (-2555, 558) -> (10290, -1103) in the plan, keys
57..66 pass (-62..12, 105..108, 71..78) (`re/vehicle_routes_1108.md` 24, 72); Dead Men's own FA used `Triggers!ExitTrigger_01` (408, 396, 460) and
`BoardingTrigger_Car` (3252, 133, -20) (`re/campaign_fa_bank.md` 147-150). The exact STOP **NEEDS ZIP** (the scanner prints wait / stop / board / end).

## 2. The blow-up vault door with loot behind it

### 2.1 Which door ("two doors in the original game, just before the garage")

The route (`re/campaign_fa_bank.md` 143-150, 665 of `re/bank_campaign.md`): START plaza -> `Triggers!EnterBankTrigger_01` (303, 974, -9407) -> banking
hall (y 800) -> stairs -> vault lobby (`M03_A_VaultLobby_01a`, y 240, x -600..1709, z -7800..-5447) -> the loading dock = THE loot room (`MapIconMainLoot`
(667, 242, -6334); `M03_FAA_Garage_01a`, the FA-only enlarged dock; eight piles 795..802) -> `ExitBankTrigger_01` (291, 399, -4668) -> yard -> alley -> van.

Candidates for the owner's door (all **NEEDS ZIP** for node ids / state in M03_FA_A; the campaign level M03_A is what the repo measured):

| candidate | where | evidence | fits "two doors before the garage"? |
|---|---|---|---|
| **A. `VaultLobby_01a\SI0201_M03_DoorSteel_A_01 / _02`** | x -150 / +150, z -6530..-6430, y 240: the north wall of the vault lobby, i.e. between the lobby and the dock | `re/campaign_fa_bank.md` 714 ("steel side doors ... no way round") | YES: a PAIR, 300 cm apart (a pillar between: two single steel leaves side by side), exactly where the lobby meets the garage. Likeliest. |
| B. `SecurityHall_01a\SI0201_M03_DoorSteel_B_01` = kick host **1076** | hinge 60 cm from `Triggers!ExitBankTrigger_02`; swung it cuts a corridor (41..456 cells) off every `SpawnPoint_Dead_NN` | `tools/kl_doors_1108.py` 42-43; `re/open_work_log.md` 11-08 18:00 F1; `re/playtest_review3.md` 150-152: the fed way passes `Garage_Wall_3xM_Door_03 / _02` and then `DoorSteel_B_01` | PARTLY: it is a door INTO the garage from the security hall (west), with TWO frames (`Garage_Wall_3xM_Door_02 / _03`) in that wall - "two doors" could be these two openings. It sits on a corridor the dead-respawn walk uses: a blown door (leaf gone) is HARMLESS there, a swung leaf is not. |
| C. `SecurityHall_01a\SI0201_M03_DoorSteel_A_01` | (-1190, 242, -4750), the hall's west door to the yard | `re/campaign_fa_bank.md` 715: FA leaves it open | no (open, outer wall) |
| D. the dock's roller door / `BackDorAnim_01 / _02` | (40, 550, -4706), two animated leaves | `re/campaign_fa_bank.md` 713 | no: the bank exit itself, animated (key data), not a loot gate |

Recommendation: the scanner's PAIR table decides. If A exists in the FA zip as two shut static leaves (REF with a STATIC .HVK placement each) it is the
vault door; the room behind it is then the dock itself - already the loot room, so "a good bit of loot behind it" = the loot moved / added INSIDE the
double door's lobby side or the dock (2.4). If the FA map has A open or missing, take B (and show both frames: the second opening gets a leaf too, or
stays a kick door). Also list `SecurityHall02_01a` (FA-only, 48 placed, `re/campaign_fa_bank.md` 140): a second security hall beside the dock is the
natural "more loot rooms" candidate if its nav cells are a pocket reached through one door (the scanner prints both sides' nav part per leaf).

### 2.2 What the engine offers (proven vs guessed)

| mechanism | status | source |
|---|---|---|
| Explode + ShakeCamera cloned token for token from the systems' `Rocket_RPG7`, radii 1 cm, tinnitus 0, rocket sound, fireball cluster `FX_Grenade_RPG_01`, message `AITrigger` from a TriggerDelay | PROVEN to load and run (Retomoto window blast live; HASTA1109 bench PASS: wall hidden, wreck shown, 0 faults; the boom itself unseen by the log) | `tools/kl_hasta_blast_1108.py` dress()/hook(); `tools/kl_fa_blast.py` 33-71 |
| TriggerDelay2 in the AIMonitor start list (round-start timer) | PROVEN (dm01squads, dm03cops Go/Go2, Hasta backstop) | `kl_dm03cops_1108.make_nodes` 223-231 |
| TriggerCounter counting dead squads -> a beat (Hasta: 2 squads dead or 30 s backstop) | PROVEN (HASTA1109) | `kl_fa_hasta_layer.py` 266-280 |
| TriggerBox (f14 `ECPS_FA_MERCONLY`, f15 0 = any heister, f10 0 = every enter edge, f17 = event list): a heister walking into a box fires a list | PROVEN live (DD10 van call benches dd10called1109 / dd10land1109) | `tools/kl_dd10_vancall_1108.py` 17, 127 |
| AIDWrapper: receives `AITrigger`, sends `Activate` to its list (the blast "fan") | PROVEN (Retomoto live) | `kl_fa_blast.py` 52-56, `kl_fa_hasta_blast.dress` fan |
| DeactivateGeom on a STATIC Dead Men object | hides the MODEL (0x6edd50 sets flag 0x400 only); the player stayed BLOCKED at the DM02 shutters' static plane until `kl_escape.cut_collision` removed it | `tools/kl_dm02_coop_1026.py` 655-668; `re/open_work_log.md` 10-26 |
| kl_escape.cut_collision (a static placement removed at BUILD time) | PROVEN live (DM03 yard wall, run H0) but the door is then open from the first second | `re/escape.md` 5.1 |
| Kick door graft (own leaf, key-framed slab type 4): E kicks, state 1 -> 3, leaf swings, WALK-THROUGH | PROVEN (DM01 x2, DM03 176, DM03A 6516, DM02 x2; DM02_1109 run d) | `re/open_work_log.md` 11-09 06:05 / 08:50 |
| MatPosAnimProxy driven by a message list other than the KickDoor controller (the co-op airlock's completion list plays its leaves this way) | stock pattern (F04 / F06), not yet done by us | `re/interactivity.md` 45-55 |
| PlayerAction as a one-player "press E" that fires a list | GUESS, unproven (dm02 co-op notes) | `tools/kl_dm02_coop_1026.py` 17, 190 |

Consequence: a static leaf cannot be "blown away" by hiding it - its collision is baked in the list MOPP. The leaf must own a RUN-TIME body: the
kick-door graft's key-framed slab (type 4, follows the leaf's keyed swing; walk-through proven) is the one proven way to clear a door's collision in
the game, and `cut_collision` is the proven way to have none at all.

### 2.3 The breach beat (pick: simplest proven path, everything stock-form)

Build: both leaves become OWN-LEAF kick doors through `kl_interact_graft.build(own_leaf=True)` (the `kl_doors_1108` path: leaf keeps its model, 6 cm slab,
stock PC0800 kids) **minus the player kick**: the `KickDoor_Controller`, its action boxes, arrows and the `PathBlocker` are not cloned (so bots' routes
and the kick prompt do not change; the door is a closed static-looking leaf with a keyed body until the beat). Kept: the leaf, its two
`KickableDoor_Proxy_*` MatPosAnimProxies, the door sound node. New top group `KL_Vault!1` at the origin:

    KL_Vault!1\Arm        TriggerBox 'ECPS_FA_MERCONLY', f15 0, f10 0, half (150, 120, 150), 2 m in FRONT of the double door (the lobby side), f17 -> [Fuse]
    KL_Vault!1\Fuse       TriggerDelay2 3.0 s (GUESS: a charge's fuse), list -> [Fan]        (+ 'Backstop' TriggerDelay2 240 s in the AIMonitor start list -> [Fan])
    KL_Vault!1\Fan        AIDWrapper 'Activate' -> [Boom, leaf 1 front proxy, leaf 2 front proxy]
    KL_Vault!1\Boom       ZBoxPrimitive at the door middle 1.2 m up: Explode (rocket clone, radii 1, tinnitus 0, fire cluster, rocket sound) + ShakeCamera 3.0 / 8000, message 'Activate'

Player experience: walk up to the double door -> 3 s -> boom, shake, fireball, both leaves swing open (their keyed swing, slabs follow, walk-through) ->
the loot behind. Nobody is hurt (radii 1 cm). Backstop opens it at 240 s for everyone. Round 2: the stock kick door is one-shot and its proxies re-arm
with the level reset (GUESS, same as every kick door we grafted; DM03_1109 round 2 PASS).
GUESSES to bench: (1) a MatPosAnimProxy answers 'Activate' from an AIDWrapper as it answers the KickDoor controller (stock airlock precedent); (2) a
TriggerBox fires in the bank cellar as it does on the DD10 street; (3) the swing direction (away from the player) = the stock leaf's keys; the own-leaf
mirror rule (`kl_interact_graft.make_door` 712-730) applies; (4) 3 s fuse and 240 s backstop read well.
Fallback if (1) fails: plain `kl_doors_1108 --hosts DM03=...,<leaf1>,<leaf2>` kick doors (proven) + the Boom box appended to each `KickDoor_Controller`'s
front-proxy list (GUESS that the controller sends 'Activate' down that list): the player kicks, the door blows. Second fallback: timer / counter beat +
`cut_collision` at build + DeactivateGeom hide (door passable from the start: what the owner disliked on Hasta).
Safety checks to carry over from `kl_doors_clear_1108`: the swung leaves must not cut a spawn walk or touch an escape box (host 1076 FAILED that
swung; a leaf that blows OPEN keeps the same footprint problem, so if B is the door, swing it INTO the garage, or hide it instead of swinging:
`DeactivateGeom` of the leaf entity + its keyed slab is a run-time body - whether the body goes with the hidden entity is a GUESS the bench answers).

### 2.4 Loot behind it (kl_loot pattern)

Live DM03 loot: four cash drawers 1774, 1781, 2106, 2113 and eight garage piles 795..802 (`tools/kl_lanes_stage_1025.py` 42-46, scaled to the map total
**7,000,000** by `kl_loot_scale_1026.TARGETS['DM03']`; "$7M paid" in bs log `re/open_work_log.md` 1169), plus 30,000 on two civilians. The ten parked
`Money!ContainerMoney!Box_Money_01..10` (12445..12454) lost their money controllers in lanes_1025: not reusable as loot.
Option L1 (no new entity, `kl_loot_1025.move` + `amount`; .oct check `listed_in_oct` refuses a listed node): move THREE of the eight garage piles behind the
vault door (the lobby side of A, or the hall side of B) and re-split the 7,000,000 so the three carry 3,000,000 (1,000,000 each) and the five left in the
dock 3,000,000; the drawers keep 1,000,000. Total unchanged. Bots: their [CrewHop] plan (KLJoin.ini) and loot window stay; they take what remains in
the dock and never queue at a shut door (`re/bots_loot.md` "cannot take" rule: run `kl_fa_bots.window_report` on the stage; the moved piles must be
OUTSIDE every hop window or the backstop must open the door before the bots' dock leg).
Option L2 (raise the total, stated): add four briefcase stacks behind the door (clones of pile 799's group, Maker pattern as the squads) at 250,000 each
-> **8,000,000** (= DM03A's tier; the owner's rule is only "every map between 4M and 8M", `kl_loot_scale_1026.py` 4). New entities -> the renumbering
pass of `rebuild()`; `kl_fa_bots.plan` NOT re-run (bots ignore them).
Pick L1 first (one tool run, no renumbering); L2 if the owner wants the dock as rich as today. Props: the piles are the FA map's own `PC0500_M03_MoneyBox_*`
(briefcase / money boxes, `re/campaign_fa_bank.md` 141); a stack must stand on a floor cell with 60 cm clearance (nav), on the far side of the leaves'
swing footprints.

## 3. More kick doors

The 11-08 scan (`tools/kl_doors_1108.py` MAPS['DM03'] + comments 42-45, `re/open_work_log.md` 11-08 18:00) found FIVE own-leaf hosts in DM03: **176, 64, 546,
1076, 1255** (names: 1076 = `SecurityHall_01a DoorSteel_B_01`; the other names **NEEDS ZIP** - the scanner prints them). Staged: 176, 64, 546, 1255
(`KL_Interact!1`, doors 1..4). Left out: 1076 (swung -90 / -120 cuts 41..456 cells off every `SpawnPoint_Dead_NN` = a corridor; hinge 60 cm from
`ExitBankTrigger_02`). `door_hosts` is strict: width 110..126, height 228..246, thickness <= 40, 'door' / 'dor' in the name, mesh on one side
(`kl_interact_graft.py` 501-549); `own_host` also wants the width along local x and the origin at a leaf edge (664-676).
Safe additions: (1) 1076 as the BLOWN leaf of 2.3 B (no swing: hide + slab), never as a swung kick door; (2) leaves the strict scan skipped because of
size: the scanner lists EVERY door-like ZSTDOBJ with its extents - a 100..110 or 126..140 wide leaf is a host once `door_hosts(w_tol=)` is widened
(the slab is cut from the own bb, so width is free; GUESS: the stock keys turn any width about the hinge). Candidates from the room table
(`re/campaign_fa_bank.md` 47): `ControlRm_01a`, `Armory_01a`, `BreakRm_01a` doors off the security hall (x -1196..-200, z -6400..-4633) = small rooms
= the owner's "more loot rooms" with a drawer each (L2 clones). Every new host goes through `kl_doors_clear_1108.check_map` (spawn walks, escape
boxes) before it is staged; a host that cuts >= MIN_CUT cells swung is a blow-up candidate, not a kick door.

## 4. Bench recipe (kl_bench_1109 kit style) and install order

Install order (each pins the previous output's md5): dm03cops_1108 (da7b3642) -> doors_1108/DM03 (33d1fa5f) -> [vehroutes_dm03_1108] -> **backswat_1109**
(input must be the zip the increment was staged from: re-stage with `--in-dir` = the installed chain's last stage, or `--accept-input`) -> vault_1109 (when
written). UNDO in reverse. Live today is c586d445 / 143f95f8 (`kl_bench_1109.K['DM03_1109']`): **NEEDS the local session to say which stage that is**
before `--in-dir` is chosen.
Kit `DM03BS_1109` (2 seats, online pair, round 1 -> shop -> round 2, host moves): pins = the staged md5s; items: (1) `ents` of the 11 garage / ramp men and
the 4 van men at 10 s: model 59891, not hidden, at their cells (build_report.json `van_cells`); (2) tele the host to the dock at 60 s, 120 s: shots show
SWAT bodies (visor / vest), not police caps; (3) tele to the van stop at 150 s: 4 SWAT standing off the lane, facing it; the van arrives and stops without
pushing a man (`waitvan` state, no man inside the lane box); (4) log: 0 faults / dumps, census line 48 / 30, round 2 reached, 0x25 dwell; KLHook.log no
0x8e5bbd / 0x607272; (5) a bot boards (Board tactic) - the van squad must not stop boarding. Vault kit (later): tele to the arm box at 45 s, shots at
+1 / +3 / +5 s (fireball, open leaves), walk-through at +8 s (goto reached), loot taken behind, backstop at 240 s on a second run without arming.
Cover lines: `bench_cover_lines.txt` of the stage (AssertSoft / ClientBuild* / ClientRewrite / ClientRingSync).

## 5. NEEDS ZIP (one scanner run answers all)

- Node ids, names, state (shut / open, hidden, static vs animated) and .HVK placements of candidates A (VaultLobby DoorSteel_A_01 / _02) and B
  (host 1076 + `Garage_Wall_3xM_Door_02 / _03`); the PAIR table; both sides' nav parts; `ExitBankTrigger_02`'s place.
- The SWAT template men under `ArrivingCops_Squad_01` / `EscSquad`: ids, field 10 suffix, weapons, ZSoldier values (the stage logs them).
- The van's stop / board / wait places and the 4 cells the build picks (build_report.json).
- The names of hosts 176 / 64 / 546 / 1255 and the extents of every door-like leaf the strict scan skipped.
- Which stage the live c586d445 is.
