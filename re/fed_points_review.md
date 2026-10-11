# Review of track L: where a dead player comes back as a fed

**Verdict: ACCEPT WITH FIXES.**

Adversarial review, 2026-10-11, of `tools\kl_fa_fedpoints.py`, `re\fed_points.md` and the three builds under
`<work>\build\z_fedpts\`. OFFLINE: nothing was run in the game, no tool or source file was changed, nothing was
written into a build folder that existed (one rebuild went to a new `z_fedpts\_review` and was removed again).
The reviewer's scripts are in the session scratchpad, folder `rev\`; logs in `G:\kl_scratch\l_review\logs\`.

Status words: **READ** = disassembled or read in a source file by the reviewer. **MEASURED** = computed by the
reviewer from the builds' files or taken from the owner's `KLHook.log`. **REASONED** = follows from the two, not seen.

The worker's main claims hold. The rule is the one it says, the three builds differ from their sources only where
the step means to, and every check passes again. What is left is two integration points for the lead, one stale
file, one false sentence in the report, and the fact that the switch has never run.

## Can a round go on after a death?

- **Before the join: yes, as far as files can show (REASONED on MEASURED).** He comes back on the tower's top
  gallery, on a collision floor with flag 0x20, on the crew's mesh part, with a body-wide way down to the crew
  (87 m) and to the join box (129 m). The AI heisters stay in the tower and he hunts them. If he walks into the
  join box the hook jumps him and the crew to the lobby.
- **After the join: yes, if the lobby box's list hides and shows a `ZSpawnPoint` in the game (not shown).** That
  is live check P2 of `re\fed_points.md` section 6. Everything the reviewer could read says it will.
- A second round in the same process (P3) is not shown either way.

## MUST

**M1. Do not put `z_fedpts\retomoto_full` on the tab beside track K's lanes build: apply the step to K's build.**
Both come from `z_rooms\retomoto_full`, so installing one drops the other. The step is made for this
(`apply <K's build> <out>`, then `check`), and the worker says so in section 6. The reviewer could not try it:
`<work>\build\z_lanes\retomoto_full` did not exist at 15:22 (K was mid-rebuild). REASONED.

**M2. No fed build goes on the owner's tab before P0, P1 and P2 have run.** Four things have never happened in
any level of either game: a `ZSpawnPoint` in a `DeactivateGeom` / `ActivateGeom` list, a spawn point hidden at the
load, two geom controllers on this helper box, and the lobby box carrying a third list entry. The reading below
makes a fault unlikely, but a load fault would cost the owner his Retomoto. REASONED.

## SHOULD

**S1. `z_fedpts\M06` carries a stale audit, and the report's sentence about it is wrong.** The report says 'No
audit run on M01 / M06: neither source folder has one'. `z_route\M06` has `audit.json` and `audit.txt`; `apply`
copied both unchanged (`cmp` equal), so the output's audit names the source's content id `70765fe6...`. MEASURED.
The reviewer ran `kl_maps.py audit` (committed tools) on a scratch copy: `RESULT: PASS (0 findings that must be 0,
6 known and accepted)`, content id `9928e5a2...`, body identical to the source's from line 3 on. Fix: the lead
runs `kl_maps.py audit` on the folder, or `apply` stops copying `audit.*` / `preflight.*`. `z_route3\M01` really
has no audit.

**S2. `diff` does not compare everything it claims.** `kl_fa_fedpoints.py` line 1141 compares an entity's `rot`,
`trans`, `flags`, `tid`, `model`, `aux`, `ref`, `raw`, `group`, but not `links`, `lkey` or `walk`, and it lets a
changed `.buf` pass unread (line 1085). READ. On these three builds the reviewer's own comparison found them
equal (see 'Member by member'), so nothing is wrong today; the check should say what it checks.

**S3. All three tower points are on the top floor (y 21000).** A man who dies late, with the crew at the lifts on
y 19600, comes back 129 m of stairs away. The rule in the tool (line 741, `band=` the START row's floor) allows
nothing else. One point on a lower atrium floor would shorten that; the owner's call. MEASURED distance, REASONED
effect.

**S4. `klfed.c`'s place line reads a tick early on some maps.** The owner's log has `at (0, 0, 0)` at 12:43:29,
12:44:04, 15:06:59 and 15:14:34. MEASURED. P1, P2, P5 and P6 are judged by that line; a second line half a second
later (the worker's own suggestion, track M's file) should exist before those runs.

## NOTE - the rule in kl2.exe, re-read by the reviewer (READ)

- `0x4b29b7..0x4b29c6`: `push 0 / push 2 / push ebx / call [vtable + 0x31c]`. `0x518e30` is slot 199 of
  `ZGameRulesHeist` and of no other class (`debug\rtti.py`).
- `0x5614f0`: list `[[0x168e9f8] + 4]`; an entry is a candidate when `[point + 0x14] == type` (`0x56154f`) and bit
  0x400 of `[[point + 4] + 0x3c]` is clear (`0x561557..0x561562`). The draw is `seed * 0x10dcd + 1`,
  `(seed >> 8) & 0x7fff`, times `[0xb59200]` (`0x561593..0x5615bf`). No other test in either loop.
- `0x518e30`: -1 twice returns without placing (`0x518e49..0x518e5b`); one ray from 10 above (`0xb5cde8`) with
  mask 0x20 through the collision world's vtable +0x264 (`0x518ec1..0x518efe`); on a hit height + `[0xb62258]`.
- `0x824950` / `0x55c9f0` (slot 26 of `ZDeactivateGeom` / `ZActivateGeom`): two message words each, then every
  list entry through `0x8ccde0` to `ZSessionManager` slot 9 `0x668160` / slot 8 `0x4c4900`. Slot 9 returns for an
  object already hidden (`0x668169..0x668177`), slot 8 for one that is shown (`0x4c4909..0x4c4916`).
- **Stronger than the worker's 'ASSUMED'.** `ZSpawnPoint` (vtable `0xbd2954`), `ZSTDOBJ`, `ZGROUP` and
  `ZBoxPrimitive` hold the SAME functions in slots 20, 21, 22 (`0x5f7940`, `0x46fe10`, `0x63f370`). Stock levels
  hide and show model-less boxes and groups through exactly these, so nothing class-specific runs for a spawn point.
- **The lobby box, which the worker left as 'not read'.** `ZTriggerBox` slot 26 `0x6e8b80`: a message only starts
  a box that is not started (`[box + 0x40]`), it does not fire its list. So `TriggerBox_OpenExitElevator` in the
  tower, which names the lobby box, cannot fire the switch early. The update `0x42afd0` counts qualifying players
  inside and fires on the edge when the count reaches `[box + 0x44]` (`0x42b20f`). In this build the box's fields
  are `[1, 1, 1, ...]`: started at the load, fire on entering, count 1. One criminal inside is enough.
  Whether the AI heisters the hook puts into the box count was not read; either way it fires no later than the
  human's first steps out of the lift.
- `0x8f3fa0` (the jump) takes the local player from `0x660b00` and skips only a hidden entity or one with
  `[player + 0xd44]` set (`0x8f3fc9..0x8f3fe4`). The 8 / 3 it tests comes from vtable +0x5d8 = `0x4cd950`, the
  player's current action, not his kind. `kljoin.c` lines 244-258 read the same slot and test nothing about the
  player's side. So a police human is jumped: READ; never run.
- Not re-read: the multiplayer pickers `0x4d0b80` / `0x4de590`, the save / restore slots, slot 210.

## NOTE - the rule in the owner's own log (MEASURED)

`C:\Steam\...\KLHook.log`, `fed: YOU ARE A FED ... at`:
- Retomoto 12:31:46 `(1804, 19601, 812)` and 14:46:30 `(1904, 19601, 818)`. The tab's points Dead_05 and Dead_06
  stand at (1800, 19601, 812) and (1904, 19601, 818); the eight police bodies stand at z 972..1138. He was put on
  the points, not left at a body's place.
- The bank 14:30:24 `(-4469, 300, -3578)`: Dead_05 is at (-4457, 393, -3593), floor 300; the bodies are parked at
  (10657, 439, 3127). The ray's hit is used.

## NOTE - the points called good, checked against collision and doors (MEASURED)

`kl_escape.Walk` leaves out convex shapes, rigid bodies and hidden entities, so the reviewer listed exactly those,
and measured every door leaf in world space.

- **Withdrawal (`z_cover3\M03`)**: every door of the stairway room is a static, non-convex `ZSTDOBJ` with no
  controller, so it is in the walk test. The pair `DoorSteelWin_A_05 / _06` (x -4911..-4883, z -3620..-3380) is
  SHUT: that is the double door of the lead's picture. The other three doorways each have one leaf turned open:
  gaps of 110 (z -3102..-2992 at x -4500), 109 (z -3208..-3099 at x -4100) and 211 (at x -3700). The worker's way
  goes through them. Nothing left out of the walk test stands within 2 m of a point.
- **Late Night Opening (`z_loot3\M02`)**: `DoorSteel_A_01` shut (z -2520..-2400), `DoorSteel_A_02` turned open;
  gap 115 at x 4020, and the way crosses it at z -2352. Only chairs and cups are left out.
- **The three outputs**: under all 19 points the floor carries flag 0x20 and nothing lies between the floor and
  250 above it. No convex shape, rigid body or hidden-at-load object comes within 2 m of a point; the street's
  cars and the SWAT truck (convex, so invisible to the walk test) are 3 m or more away. Hidden-at-load collision
  in the tower is the atrium's broken glass panes only; in the street none.
- `Player_Cover!WareHouseDoor_PlayerCover_03 / _04` beside Hot Coffee's new points are cover markers, not walls
  (`re\bots_dynamic.md` line 234).

A gap of 110 passes the tool's body of 60. Whether it passes Dog Days' player capsule is P8.

## NOTE - member by member (MEASURED, the reviewer's own comparison)

| build | members that differ | `.prp` nodes | `.gms` entity fields | `.buf` | files beside |
|---|---|---|---|---|---|
| `retomoto_full` | `.prp`, `.gms` of 30 | 11: 7 points (`ZGEOM[1]`, `[2]`, and `[3]` 0 -> 1 on the street four), the switch (list + a new `ActivateGeom`), the lobby box (+1 entry), `ChairPost` (+3), `ChairsPre` (+4) | `rot` 7, `trans` 7, `flags` 4 (0 -> 0x400) | same | all equal, + `fedpoints.json` / `.txt` |
| `M01` | `.prp`, `.gms` of 31 | 7 points, `ZGEOM[1]`, `[2]` | `rot` 7, `trans` 7 | same | `steps.json`, + the two |
| `M06` | `.prp`, `.gms` of 31 | 5 points, `ZGEOM[1]`, `[2]` | `rot` 5, `trans` 5 | same | `steps.json`, + the two |

Entity `links`, names, type ids and the scene's `head`, `nav`, `tail`, `dyn`, `tags`, budget and REF slot count
are equal. The unpacked `.gms` grows by 336 bytes on Retomoto and M01 = 7 new 48-byte matrices; all eight header
offsets move by exactly that. The padding after every matrix and place is zero before and after. The new
matrices have determinant -1, as the old ones and Dead Men's own.

## NOTE - checks run again

Archives: `518223a2...`, `e28a4ab8...`, `710efed7...`, as reported. `apply` run again on `z_rooms\retomoto_full`
gave `518223a2...` once more.

With the working tree's tools: `kl_fa_fedpoints.py check z_fedpts\retomoto_full` = `PASS (0 FAIL, 8 NOTE); 7
point(s): 7 good, 0 doubtful, 0 bad; START half 3, jump half 4`.

With the COMMITTED tools (`git archive HEAD tools`, because other tracks have `kl_fa_bots_rt.py` and
`kl_fa_bots_dyn.py` open), on source and output alike:

| build | `kl_fa_bots_rt check` | `kl_fa_bots_dyn check` | `kl_impact` |
|---|---|---|---|
| `z_fedpts\retomoto_full` | PASS (0 FAIL, 9 NOTE), jump list 7, [CrewJoin] places 7 | PASS (0 FAIL, 8 NOTE) | problems: 0 |
| `z_fedpts\M01` | - | FAIL (7 FAIL, 2 NOTE), the source's own seven | problems: 0 |
| `z_fedpts\M06` | - | PASS (0 FAIL, 3 NOTE) | problems: 0 |

Each output's log equals its source's line for line, folder name aside. `KLTalk.ini` of the Retomoto output is
`6c78c079...`, the approved one. Not run again: `kl_map_guns`, `kl_fa_street report`, `kl_fa_author ledge`,
`kl_fa_talk` (the worker's logs were read).

## NOTE - the hook

No hook file of the fed part was changed (`git diff HEAD -- klhook/klfed.c klhook/kljoin.c klhook/klcrew_rt.c`
is empty). Built from a clean snapshot of HEAD `28953d8` in `G:\kl_scratch\l_review`: both compile, one warning
(`klhud.c(188)` C4101). TEST `6d78e0ceaeee8e25b5bfb066892efc362d92b39f`, SHIP
`7deff5ec956963799f6a6ba282103570eb2f7248`. These are the tree's own hook, not a hook of this track.

`klhook\KLHook.ini` lines 504-506 (committed in b421ddc) name `tools\kl_fa_fedpoints.py` and `re\fed_points.md`,
which are still untracked.

## NOTE - cases asked for

- **Thread, freed object**: none; the answer is level data, the game's own controllers run on its own thread.
- **Stock level**: untouched; the step only writes a new build folder.
- **A level without a join**: one half, points moved only where bad or doubtful, nothing hidden; `check` FAILs a
  hidden point there (line 1009). READ.
- **A police human**: can take the join (above). He does not open the tower's escape lift
  (`TriggerBox_OpenExitElevator` is `ECPS_FA_MERCONLY`), which does not matter: the join box is the floor before
  the car. REASONED.
- **A second death**: final in the game; no point is drawn.
- **A second round**: the blast pair re-arms the points 16.5 s after the round-start event. If the game does not
  restore hidden states itself, the points are the wrong way round for those 16.5 s (about 8 s after GO). READ in
  the build, REASONED.
- **No candidate at all**: cannot happen in these builds (three shown at the load; the two switches never leave
  both sets hidden); `check` FAILs it (line 1003).

## Not shown

- Anything in the game: P0..P8 are all owed.
- That an Arcade round start restores hidden states.
- That the AI heisters count for the lobby box.
- What a `LevelBound` box does to a police player; whether a Dog Days player survives the 2.7 .. 4.3 m drops of
  the tab's M01 and M06 (if he does, `z_fedpts\M01` and `M06` are spare).
- The team modes' and Undercover Cop's police points on Retomoto still stand in the lifts and under the square
  (MEASURED: `UCC!SpawnPoint_Dead_0N`, `TeamMode!SpawnPoint_TEAM_Police#0N`); Arcade does not draw from them.
