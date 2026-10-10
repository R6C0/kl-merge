# Review of the tuned map builds (`<work>\build\t_maps\M01 M02 M03 M06`)

2026-10-10, agent t-verify (adversarial review of re/map_tune.md, re/map_escape.md, re/map_ai.md,
re/map_guns.md). OFFLINE: nothing was installed, the game was not started, nothing was written into
the Dog Days folder. The four build folders were not changed (archive sha1 before and after:
`7dd39ac30aac`, `a07524f1534c`, `8f1d69c834f9`, `72e8d03c9fe1`); every checker that writes into its
folder ran on copies in the scratchpad. NOTHING HERE RAN IN THE GAME.
Status words: **seen** = read in the files / kl2.exe by me, **not established**, **ASSUMPTION**.

## 0. Verdict

| map | load it? | must be fixed before the owner plays to the escape | should be fixed or knowingly accepted |
|---|---|---|---|
| M02 Late Night Opening | yes - every checker and my own tests pass | **F1** (the 'vehicle called' list is written in a form no level of either game uses) | F3 (police told to hunt before their drive) |
| M01 diner | yes | **F1** | - |
| M03 the bank | yes | **F1** | F2 (police sent back INTO their car), F3 (squads told to hunt from their holding place outside the map) |
| M06 A Walk in the Park | yes | **F1** | - |

F1 does not touch the load; it is reached when the escape vehicle is called. Without a code change the
safe build is `python tools\kl_map_tune.py build <z_maps\Mxx> <out> --no-called` (leaves the list empty,
as on the build the owner played).

The three claims:

| claim | result |
|---|---|
| 'fixes the escape vehicle going under the map' | **The vehicle is not changed at all** (0 route points moved; nothing was wrong with them - confirmed independently, section 2). What is changed is the CAMERA of a player aboard, and that change stands up: the two code branches and the stock rows were re-read here (section 3). The owner's "van sometimes a bit weird" is NOT addressed by any build. |
| 'enemies harder with Retomoto's logic' | Partly. Seen in the files: health floors, rifles for the squads that arrive, timers / counters, 2 squads unleashed a map, 'wiped out' lists. Not established: everything that rests on a car squad acting (4 of 12 soldiers on M02, 4 of 13 on M01, 9 of 15 on M03) and on list 8 being 'wiped out'. The 'vehicle called' part is defect F1. Two plans send orders that can make a squad EASIER (F2, F3). |
| 'carries the Dead Men gun looks' | The files are consistent (section 5): every `KLGuns.ini` root is a model of its archive, exactly the look group is unhidden, nothing the level reached before was changed. Whether the hide bit hides a gun part in the game is still not established; one new open point (F5). Only 1 / 4 / 2 / 2 placed enemies hold a gun with a look. |

## 1. What was run

Checkers of the authors, on copies (`<scratch>\rv\Mxx`), each as its own process:

| | M01 | M02 | M03 | M06 |
|---|---|---|---|---|
| `kl_map_tune.py check` | PASS, exit 0 | PASS, exit 0 | PASS, exit 0 | PASS, exit 0 |
| `kl_maps.py audit` | PASS (0; 1 known) | PASS (0; 6 known) | PASS (0; 0 known) | PASS (0; 6 known) |
| `kl_map_escape.py check` | 0 faults | 0 faults | 0 faults | 0 faults |
| `kl_map_guns.py check` | problems: 0 | problems: 0 | problems: 0 | problems: 0 |
| preflight CRASH / RISK lines against `z_maps` | equal | equal | equal | equal |
| audit DEGRADED / BROKEN lines against `z_maps` | equal | equal | equal | equal |

My own scripts (scratchpad, not in the repository; they call no function of `kl_map_escape`,
`kl_map_ai`, `kl_map_guns`, `kl_guns`): `rv_escape.py` (routes and cameras against the collision AND
the navigation mesh), `rv_ai.py` (census of the 21 stock levels; every field of every object compared
between `z_maps` and the tuned build; who names what), `rv_root.py` / `rv_root3.py` (form of every
reference-list entry), `rv_guns.py` (KLGuns.ini against the .prm, chunk table, members, side files),
`rv_exe*.py` (kl2.exe: hide-bit and variant sites, the vehicle routs).

Budget, bytes, `z_maps` -> `t_maps` (my reading of the archives' directories; equal to re/map_tune.md):

| | .prm | chunk-table entries (limit 69,632) | .ANM | .fxc | F01_Main.WAV | .TEX |
|---|---|---|---|---|---|---|
| M01 | 55,088,000 -> 55,479,264 | 50,042 -> 50,136 | 22,061,764 = | 17,760,648 = | 21,722,704 = | 234,505,616 -> 242,724,752 |
| M02 | 54,619,216 -> 55,010,480 | 58,371 -> 58,465 | 22,202,472 = | 17,760,648 = | 22,527,568 = | 216,130,816 -> 224,349,952 |
| M03 | 60,469,040 -> 60,860,304 | 62,680 -> 62,774 | 22,202,616 = | 17,760,648 = | 22,716,752 = | 217,786,368 -> 225,939,136 |
| M06 | 49,585,744 -> 49,977,008 | 46,902 -> 46,996 | 21,642,576 = | 17,760,648 = | 21,775,744 = | 204,607,072 -> 212,826,208 |

Members: 31 in both, names and order equal; six differ (.MAT .TEX .gms .oct .prm .prp), 25 equal by
CRC and size. Files beside the archive: 20 -> 21, none missing, none changed (sha1), new: `KLGuns.ini`.
Every .WAV has its .WHD. Nothing grew but .prm (+391,264) and .TEX (+8.2 MB), both the gun step's.

## 2. The routes against the ground, recomputed

Independent of `kl_map_escape.py`: my own parse of the spline field, my own frames (checked: the
entity places I compose equal the .HVK placements of 1,594 .. 3,610 entities per map to 0.0), two
ground sources - (A) every non-convex triangle of the .HVK, all types, no 'Locations/' filter, no
upness filter; (B) the navigation mesh (gms +0x34: polygons from arrays 3 / 9 / 6; array 6 is
x, z, y + a 2-D normal) - and two walks, straight and a Catmull-Rom curve through the points,
sampled every 25 units.

| map | route | samples | lowest over the collision (straight / curve) | lowest over the nav mesh | samples with no floor below | a floor within 120 ABOVE a sample |
|---|---|---:|---|---|---:|---|
| M01 | incoming | 293 | 3.2 / 3.0 | 2.7 / 2.6 | 0 | none |
| M01 | escaping | 908 | 4.0 / 3.4 | 0.0 / 0.2 (the mesh lies 15 over the street's collision there) | 0 | none |
| M02 | incoming | 600 | 3.6 / 3.6 | 3.6 / 3.6 | 0 | none |
| M02 | escaping | 759 | 0.9 / 0.3 | 0.9 / 0.3 | 0 | none |
| M03 | incoming | 480 | 1.4 / 2.4 | 1.4 / 2.4 | 0 | none |
| M03 | escaping | 346 | 6.7 / 6.4 | 6.7 / 6.4 | 0 | none |
| M06 | incoming (helicopter) | 716 | 202 / 116 (over `PC0200_M06_ParkLamp_A_FA_21`) | 148 | 17 / 26 (over open water / outside) | none |
| M06 | escaping (helicopter) | 1,005 | 200 / 200 | 193 / 190 | 365 / 354 | none |

So the statement 'no route point is under the ground' holds by two sources and on a curve as well.
The per-point heights equal `escape.txt`'s (M02: 3.6 .. 11.6 and 0.9 .. 35.3). **Not refuted - and
nothing was changed, so nothing about the vehicle's own behaviour is different from the build the
owner played.**

## 3. The camera

- kl2.exe, re-read (`debug\dasm.py 0x447190`): 0x4471a1 `cmp [eax+0x180], 4` takes the place of
  `[eax]` (the box's own node) and then of `[eax+4]`; 0x447240 `cmp [eax+0x180], 3` takes the place of
  `[eax+4]` (field 9) and then of `[esi+0x540]`. `tools\dd_enums.json`: 3 = `eFMM_LookFromPos`,
  4 = `eFMM_LookFromPosFA`. As re/map_escape.md 1.2 says.
- Stock, my census: 18 `CCameraBox` in `eFMM_LookFromPos`, all escape-van cameras with field 9 a
  `CamPos` node, floats (0, 99999, 99999, 40 | 65, 0, 50 | 60), field 12 = 1, `eFMC_Unbreakable`.
- The tuned builds: one enum per camera differs from `z_maps` (5 cameras), nothing else of them.

| map | camera | eye (field 9) | over the collision | nav mesh below | to the stop | between eye and stop |
|---|---|---|---:|---|---|---|
| M01 | EscCamera01 | (4049, 526, 19454) | 526 | 0.0 | 24.8 m | nothing |
| M01 | EscCamera02 | (1803, 211, 27411) | 226 | 0.0 | 80 m (films the road out) | a phone booth at 50 m; `ColiObj_Camera_01` 251 over the eye |
| M02 | EscCamera01 | (981, 235, -9104) | 235 | 0.0 | 16.1 m | nothing |
| M03 | EscCamera01 | (1577, 329, 408) | 290 | 41 | 14.6 m | nothing |
| M06 | EscCamera01 | (246, 1819, -280) | 1,716 (over `water_plane_02`) | - | 64 m | nothing |

`EscCameraLAST` (mode FA, at the origin, field 13 = 1) is left as it was on all four.

Notes, none a defect of the build:
- The sixth float differs per camera (M02 30, M03 60, M01 40 and 80, M06 40); re/map_escape.md 1.1
  prints 40 for all. Stock uses 40 and 65.
- All 45 stock `OnlineEscCamTrigger` name the VAN in field 0; the Dead Men maps have '' there, i.e.
  the branch 'test the player's place against the box'. The owner's report shows that branch fires.
- M02: the escaping route's first point (-979, 5, -9426) lies exactly on the edge of
  `CameraTrigger01` (centre z -8614, half 812). The car carries the player out of the box 8 m after
  it starts. What the fixed camera does then is **not established** (`eFMC_Unbreakable`, by message
  only): if the view changes again as the car pulls away, that is the place.

## 4. The enemies

### F1. MUST FIX, all four maps: the 'vehicle called' list is written without `ROOT\`

Object: `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor`, controller `OnlineEscVehicleMonitor`,
field 4: M01 10 entries, M02 7, M03 9, M06 7 - all 33 in the form `AIEnemies!PoliceSwats\Gate\Way#01`,
not `ROOT\AIEnemies!...`.

Seen (`rv_root.py`, `rv_root3.py`):
- 21 stock Dog Days levels: reference lists of this field type (handler 39, loader 0x8c4dd0) hold
  30,406 entries with `ROOT\` and 24 without - and those 24 are EMPTY strings. `ZSquadScript`'s lists
  (handler 59): 5,845 with, 0 without. The stock monitors (F07, F03) write `ROOT\Gameplay!...`.
- Dead Men's own M01_FA_A, M02_FA_A, M03_FA_A, M06_FA_A, M09_A: no non-empty entry without `ROOT\`.
- The builds that ran in the game (`z_maps\M02`, `y_loot\retomoto_loot`, `rt_ai\retomoto_ai`): none.
- In the tuned builds these 33 entries are the ONLY ones; everything else the step wrote has `ROOT\`.

So no level of either game, and no build that has run, shows the game resolving that form.
`kl_map_ai.rooted()` says 'stock: ZSquadScript without ... Both forms are resolved by the game in
stock levels': the census contradicts it. Cause: `rooted()` returns `n[True] > n[False]`, which is
False for a controller whose lists are all empty (0 > 0) - the monitor's are, on every Dead Men map.
Why no checker saw it: `kl_map_ai.faults()` resolves `full(p)` (it ADDS the prefix before it looks),
and `kl_fa.prune` only tests entries that start with `ROOT\`.

What the game does with such an entry was not read (the element reader behind 0x640440). Best case
the entry names nothing and the escape response the note describes does not exist; worst case an
unresolved entry is walked by the send loop (0x6276e0) when the vehicle is called.

Fix (kl_map_ai.py, not my file): `refs()` must write `full(p)` always, or `rooted()` must return True
when the controller has no entry. Then rebuild; live check A4 of re/map_ai.md is the test.

### F2. M03: three 'wiped out' lists and the 'vehicle called' list send police back INTO their car

`Triggers!ArrivingCops_Timer` (2 s) names `AI_Enemies!ArrivingCops_Squad_02\VehicleEnterBehaviour`
(+ a sound). The tuned build names that timer from four new places: `ZSquadScript[8]` of
`AI_Enemies!ParkingLotSWAT_01`, `AI_Enemies!LoadingDockSquad_01`, `AI_Enemies!BankMainSquad_02`, and
the monitor's field 4 (named by 5 objects before, 9 now). The plan's own comment says 'No drive rout is
named here: a squad that has driven is not sent back to its car' - the timer is that, one step removed.
A squad that is out and fighting gets its ENTER rout again; and the rout that would bring it out again
(`VehicleExitBehaviourRout`) is the one the conversion lost. Dead Men's own boxes can do the same, so
this is more of an existing hazard, not a new kind; it works against 'harder'. Fix: take
`Triggers!ArrivingCops_Timer` out of the three chains and the escape list of `PLANS['M03_FA_A']`
(`Triggers!Parkinglot_SWAT_Timer` is harmless: it names no enter rout).

### F3. M02 and M03: a car squad can be told to hunt before it has driven

- M02 `AIEnemies!PoliceSwats\HuntBehaviour`: in Dead Men named only by its `HuntTimer`, after the
  drive. Now also by `AIEnemies!TransporterGuards` `ZSquadScript[8]` and by the monitor's field 4 -
  where the SAME list first names `AIEnemies!PoliceSwats\Gate\Way#01` (the drive). Two orders at once
  to one squad; which wins was not read.
- M03 `AI_Enemies!EscSquad\HuntBehaviour` (named by nothing before; now by its drive's end list, by
  `ArrivingCops_Squad_02` `ZSquadScript[8]` and the monitor) and
  `AI_Enemies!ArrivingCops_Squad_01\HuntBehaviour`: the men of both squads stand at ONE holding place,
  (-10262, 702, -6304), outside the navigation mesh (its x range is -9602 .. 8575), until their
  `VehicleEnterBehaviour` runs (`EscSquad`: only at the box `Triggers!EscSquad_Triggere`). A hunt
  order before that reaches two men who are not on the map.
Not established what the game does in either case. Fix: name a car squad's hunt rout only from lists
that run after its drive (as Dead Men did), or accept and watch run A1.

### What stands up

- `rv_ai.py`, every field of every object, `z_maps` against tuned: 43 / 33 / 35 / 41 fields differ on
  34 / 30 / 33 / 32 nodes; no node, class or controller list differs; no list lost an entry. The
  differences are exactly the three steps' (7 gun models per map in `ZLNKOBJ[4]`, 1 or 2 cameras, the
  ai step's values and list entries as its report prints them).
- Every list entry the step added resolves to exactly one node, and that node has a controller
  (behaviour rout, `TriggerDelay`, `TriggerCounter`, `GatePath`). No rout, timer or counter that was
  named before is named by nothing now. Named by nothing (as in `z_maps`): M02 `PoliceSwats\Gate\Way#02`,
  M06 `JPN_Boss\SquadModifier`, `JPN_DrugSquad_Island_01\PatrolBehaviour`.
- M02's car: `Gate\Way#01` is one way of a `GateGroup`; stock names `GatePath` nodes from squad lists
  (92 entries) and from the round start, so naming it is the stock form. The round-start list names a
  `TriggerDelay` in stock too (9 entries; 80 `TriggerDelay` in stock, field 0 an integer of 0 .. 100).
- kl2.exe 0x7cdbe9 .. 0x7cdc2b: the drive rout hands its end list (rout +0x5c, with the bool +0x60)
  to the behaviour object it makes (+0x30 / +0x34), the same shape as the exit rout's (0x63387e,
  +0x4c / +0x50 -> +0x20 / +0x24). So the by-pass entries (`PoliceSwats\FlankingBehaviour`,
  `PoliceSwats\HuntTimer` in `VehicleMoveBehaviourRout[4]`) are at least carried into the object that
  drives. When that list is sent was not read.
- Values the step WROTE, against my census of 1,413 stock soldiers: health 175 (141 in the FA levels),
  150 (28), 125 (0 in FA, 350 in the story levels); accuracy 90 (7 in FA), 60; aim 60; skill `eCustom`.
  All in stock use. Timers 45 s and 8 s are not among stock's 21 `TriggerDelay` values but inside
  their range.
- M06 `AI_Enemies!JPN_DrugSquad_Island_01\Island_JPN_Guards_02\Ground`: `eRegular` -> `eCustom`,
  fields 4 / 5 / 13 / 14 = 60 / 60 / 50 / 50 (stored before: 75 / 90 / 20 / 60, never used under the
  name). As used: accuracy 55 -> 66, aim 50 -> 60, 13 / 14 unchanged. Nobody got worse.
- Every `ZFFActor[1]` of every placed actor resolves to one `ZFFItemTemplateWeapon` of the build
  (16 / 15 / 20 / 14 actors, 0 unresolved).

### Not this step's doing, but outside stock (as on the builds already played)

- Accuracy 95 .. 100, aim 95 .. 100, fields 13 / 14 / 15 of Dead Men's rows: no stock soldier has
  them (stock accuracy tops at 90, aim at 82). Kept on purpose (floors).
- Skill name `eVeteran` on 5 soldiers of M06: no stock level uses it (stock: `eCustom`, `eRegular`,
  one `eElite`).

### F4. Not established, and it is most of 'harder'

The squads that arrive are the ones that got rifles and health 175: M02 `AIEnemies!PoliceSwats` (4),
M01 `AI_Enemies!FrontMall_01 / _02` (4), M03 the four car squads (9). Their exit rout is gone; the
by-pass gives them orders, nothing shows they act on them. Seen here in addition: M02's four police
are placed on foot in the car park, (1210 .. 1358, 2, -8159 .. -8327), 19 m from the escape car's
stop, 106 m from their car at (10308, 15, -13850), `ZSquadScript` field 3 = 1, exactly as in Dead
Men's level, whose car has four `PassengerAnimPos` seats (kept by the conversion). Whether Dog Days
seats them at the load is not known. First thing to look at in run A1: from the roof start, are four
police standing in the car park before any car has come?

## 5. The gun looks

`rv_guns.py`, per map (M01 / M02 / M03 / M06):
- `KLGuns.ini` Version 2, 6 guns, HideWord 28, HideBit 8388608. Roots 50057.. / 58386.. / 62695.. /
  46917..: each is a 64-byte model root of THIS archive's .prm; its object table has exactly
  Stock + Look parts entries; the template's `Ground` entity names it in the .gms and in
  `ZLNKOBJ[4]`; no entity is left on the old model (2483, 2892, 3453, 3687, 4005, 4187).
- Groups: stock parts all hidden, look 1 all unhidden, the Zastava's look 2 all hidden; the walk
  'hide bit, then variant 0 takes all' takes exactly the shown group; the shown group covers every
  detail bit the stock gun covers; every part is a 64-byte rigid one-bone part on a bone the gun has,
  with a descriptor, vertices and indices; no part is in another model's object table.
- Hide bit set on 41 more mesh objects than in `z_maps` (776 -> 817, 674 -> 715, 924 -> 965,
  725 -> 766) = the hidden parts of the six guns, nothing else.
- Of 50,042 / 58,371 / 62,680 / 46,902 chunk indices 2,598 hold other bytes and 94 are new; of the
  34,543 / 42,868 / 47,162 / 31,394 chunks the SOURCE level reaches (entities, .prp fields, the 16
  wardrobe roots) **0** changed; the tuned level reaches no empty chunk. The 16 `KLWardrobe.ini` roots
  are model roots of the tuned .prm.

kl2.exe, my scan of .text: `test dword [reg+0x1c], 0x800000` at 0x57ee43, 0x67cf77, 0x7581e1,
0x7af091 (as re/map_guns.md); the only two places that compare a mesh object's variant byte after a
chunk-table read (0x57ee77, 0x67cf8e) both test the hide bit just before. Not refuted.

### F5. New open point: two model queries ignore the hide bit

`ZPrimControlBase` / `ZPrimControlWintel` slot 27 (0x42a300) returns the HIGHEST variant byte of a
model's objects, slot 26 (0x8c7e20) whether a model has an object of variant n. Neither tests the
hide bit. A gun model answered 0 before; it answers 101 now (the Zastava 102), because the look parts
carry `kl_guns`' variant bytes 101 / 102. No direct caller exists (virtual calls; not followed). If a
caller ever gives an entity a variant from 1 .. highest, a gun instance with a variant other than 0
draws only parts of that variant: nothing for 1 .. 100. Run G1 shows it at once (an invisible gun).
Cheap way out if it happens: write variant byte 0 into the look parts (the hide bit is what selects).

### F6. For the lead: the hook and the slot tool

- `klhook\klgun.c` in the working tree now reads Version 2 (another session's change). re/map_tune.md 5
  ('the installed hook takes Version 1 only, so nothing happens') stops being true the moment that
  hook is installed. Then: (a) `debug\slot.py` `SIDE` must hold `KLGuns.ini` - today it neither copies
  nor removes it, and each map has other root numbers, so a file left from another build names chunks
  that are something else; (b) the owner's saved `[Guns] Start=2` shows look 2 on the Zastava, which is
  Dog Days' own AK-74, not a Dead Men gun.
- 'Dead Men guns show up': among the placed enemies 1 (M01), 4 (M02), 2 (M03), 2 (M06) hold a gun with
  a look. What the owner will mostly see is the starting rifle; that item 29 (Zastava) is the starting
  rifle is `kl_guns`' statement and was not checked here either.

## 6. Other notes

- M06: on a curve through the points the helicopter's incoming route passes 116 over the collision of
  `PC0200_M06_ParkLamp_A_FA_21` near (-1353, 382, -6360) (straight walk: 202). Dead Men's route,
  unchanged.
- `kl_map_ai.py` docstring of `rooted()` and re/map_ai.md 5 should lose the sentence about the two
  forms (F1).

## 7. Defects, in order

| # | map | object | what | found by |
|---|---|---|---|---|
| F1 | all | `Gameplay!EscapeSetup!OnlineEscapeVehicleMonitor` `OnlineEscVehicleMonitor[4]` | 33 entries without `ROOT\`: a form no level of either game and no build that ran has | census of every reference-list entry of 21 stock levels, 5 Dead Men levels, 3 played builds, 4 tuned builds |
| F2 | M03 | `ZSquadScript[8]` of `ParkingLotSWAT_01`, `LoadingDockSquad_01`, `BankMainSquad_02`; monitor field 4 -> `Triggers!ArrivingCops_Timer` -> `ArrivingCops_Squad_02\VehicleEnterBehaviour` | a fighting squad is sent to enter its car again; its exit rout is lost | who-names-what index of the tuned build against `z_maps` |
| F3 | M02, M03 | `PoliceSwats\HuntBehaviour` (from `TransporterGuards[8]`, monitor 4); `EscSquad\HuntBehaviour`, `ArrivingCops_Squad_01\HuntBehaviour` | hunt order to a car squad before its drive; M03's men stand outside the mesh until they enter | the same index + entity places |
| F4 | M01 M02 M03 | the car squads | whether they act without the exit rout: not established (authors say so too) | - |
| F5 | all | the six gun models | highest variant 101 / 102 reported by 0x42a300 regardless of the hide bit; callers unknown | scan of kl2.exe for readers of the variant byte |
| F6 | all | `debug\slot.py`, `klhook\klgun.c` | KLGuns.ini is not installed / removed with a build; the Version 2 hook is in the tree | reading both |

Claimed and not refuted: no route point under the ground (two ground sources, two walks); the camera
enum; every budget number; members and side files; chunk table; weapon templates; KLGuns.ini roots.
