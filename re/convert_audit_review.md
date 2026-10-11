# Review of the converter audit (track C, re/convert_audit.md) - 2026-10-11

Adversarial review, OFFLINE: nothing was launched, nothing written in a game folder, no tool or source file
edited, nothing committed. Read: `kaneandlynch.exe`, `kl2.exe` (capstone), the 20 + 21 stock levels, the six
Dead Men source levels, the five builds the audit names and four newer ones. My scripts are in the
scratchpad folder `CR\` (`rlib.py`, `r1` .. `r28`); they are not part of the repo.

**Verdict: ACCEPT WITH FIXES.** Every pairing the worker changed is right - I re-derived each from the code of
both exes with my own disassembly. The code changes do what they say and the offline checks reproduce to the
number. No defect of severity 'must'. What has to be put right is in what the lead is TOLD: the live checks
cannot tell a right pairing from a wrong one, and the effect on M06 and M02 is overstated.

## 1. Claims re-derived (my own commands)

Property record: `+0x10` = member offset; the member is at `this + offset + 4` in the class's virtual
functions (checked on five classes below).

| claim | what I saw | result |
|---|---|---|
| Enums are read by name | kl2 0x88c9f0: flag word `[reader+4]` bit 2 and bit 3 -> 4-byte key index -> `[reader+0x4c][index]` -> 0x847060, a strcmp walk of `{next, value, name}`; `push 0` is the default returned for a name the enum lacks. Flag word (header 0x0f) = 13 in 20 Dead Men + 21 Dog Days stock levels and the five builds | TRUE |
| `ZTriggerBox`: the new bool is DD8 | DM slot 25 = 0x69fff0: five flags (player, team 0, team 2, team 12, other); tests `[x+0x3d]` / `[x+0x44]`, `[x+0x45]` / `[x+0x46]`, `[x+0x47]`, `[x+0x48]` (other: enter only, 0x6a01eb), `[x+0x49]`. DD slot 25 = 0x42afd0: `[x+0x41]` / `[x+0x48]`, `[x+0x49]` / `[x+0x4a]`, `[x+0x4b]`, `[x+0x4c]` (other enters, 0x42b3e9) **and `[x+0x4d]` (other leaves, 0x42b3fc)**, `[x+0x4e]`. Records: DM 7 = 0x44, 8 = 0x45; DD 7 = 0x48, 8 = 0x49, 9 = 0x4a. Stock: DD field 8 set on 0 of 1,880 boxes, field 7 on 10 (`TB_GoonKicker` ...); DM field 7 on 66, field 8 on 35 of 926 | TRUE |
| `ZSquadScript` lists 0, 1, 2, 3 -> 0, 2, 3, 4 | DM 0x6ee110: `[x+0x58]` at alive <= n - 1, `[x+0x74]` at n / 2, `[x+0x90]` at 1, `[x+0xac]` at 0. DD 0x47e440: a loop over `[x+0x78]` (list 1, every death), then 0x51c8e0 `[x+0x5c]`, 0x649d30 `[x+0x94]`, 0x86b470 `[x+0xb0]`, 0x87ebf0 `[x+0xcc]` with the same four conditions | TRUE |
| lists 4, 5 -> 6, 7 | squad object: DM ctor 0x6ee300 puts lists 4..11 at +0x154..+0x170, DD ctor 0x7696f0 lists 5..14 at +0x164..+0x188. DM 0x72835d -> 0x6edd00 (+0x154), 0x728382 -> 0x6edc90 (+0x158); DD 0x4881cf -> 0x6831f0 (+0x168 = list 6), 0x4881f6 -> 0x720e70 (+0x16c = list 7) | TRUE |
| list 6 -> 9 ('attacked') | DM 0x72493f -> 0x6edcd0: `[squad+0x15c]` = list 6. DD 0x5a82b3 -> 0x7cc4a0: `[squad+0x174]` = list 9 (and it sends network id 9). The two callers are the same function (attacker stored, time + 0x2000) | TRUE |
| lists 8, 9 -> 11, 12 | message handlers DM 0x6edf90 / DD 0x8a9a60, same shape: third message -> DM `[squad+0x164]` (list 8) / DD `[squad+0x17c]` (list 11); fourth -> DM +0x168 (list 9) / DD +0x180 (list 12) | TRUE |
| lists 7, 10 -> 10, 13 by the save order | DM 0x6ede10 writes the 'sent' bytes 0x149, 0x14a, 0x14c, 0x14f, 0x14b, 0x14d, 0x14e, 0x150 = lists 4, 5, 7, 10, 6, 8, 9, 11; DD 0x44a1e0: 0x159, 0x15a, 0x15b, 0x15c, 0x15e, 0x161, 0x15d, 0x15f, 0x160, 0x162 = lists 5, 6, 7, 8, 10, 13, 9, 11, 12, 14. Without the new 5 and 8 it is Dead Men's order under the pairing | TRUE (indirect, as the worker says) |
| `ZFFActor` DM8 = DD18 | DM 0x5dda00 `cmp byte [ecx+0x680]` and DD 0x869b50 `cmp byte [ecx+0x820]`: the same function. Records: DM 8 = 0x67c; DD 18 = 0x81c, 19 = 0x81d. Stock DD: field 18 = 0 on 1,696 of 1,696, field 19 = 1 on 115 Neutral + 12 Enemy | TRUE |
| Soldier DD9..12 = health factor | kl2 0x8fbac0: `< 0` = invulnerable (0 is NOT skipped), range(tuning +0x364, +0x368, D+0x1c) x difficulty row x `[D + 0x24 + 4 x difficulty]`. DM 0x722090: the same with tuning +0x110 / +0x114 = 50.0 / 175.0 (constants 0x93859c, 0x96aec0) and the override D+0x38 | TRUE |
| DD16 / 17 read only with the flag | 0x4c1320: `cmp byte [soldier+0x6ac]` -> `[D+0x40]`, else tuning +0xc4; 0x7837a0 is the setter | TRUE |
| Vehicle DD5..8 = health factor, DD3 = health | kl2 0x42d6a6: switch on `[0x156b5f0]` -> `[v+0xbb8..0xbc4]` (records 5..8), health = `[v+0xbb0]` (field 3) x factor, or `[v+0xbb4]` (field 4) when `[0x168e59c] == 2`; DM 0x688e01 `[v+0xbac]` (field 3) -> `[v+0x5ec]` | TRUE |
| `ZTriggerCounter` | DM 0x6a0843 and DD 0x6fcfb3 test `[x+0x44]` at the same place; DD 0x6fcff8 `[x+0x45]` is new | TRUE |
| Kane / Lynch = the player slot | DD 0x42b231: value 2 needs the co-op flag and 0x8b60a0 (`gamedata+0x82c`), value 1 -> 0x432a20 (`gamedata+0x828`, or true without co-op); DM 0x6a00dc: 1 -> player 0, 2 -> player 1. Enum tables: DM KANEONLY 1 / LYNCHONLY 2, DD LYNCHONLY 1 / KANEONLY 2 | TRUE |

## 2. The diff

- `kl_convert.py`: `SQUAD_LISTS`, `LEVEL_MAPS['ZTriggerBox']`, `['ZFFActor']`, `ENUM_RENAME` in
  `Converter.value`, the log line. Logic is right. All 441 `LEVEL_MAPS` pairs have equal labels (my check).
  The category 'enum value replaced' is used by `kl_retype.test` as a category only: not broken.
- `kl_fa.py` `heli_attack` in `repair()`: stock Dog Days, 21 levels: 165 fly routs, 49 say attack, 49 of 49
  under a helicopter with a `HeliWeapon` whose field 3 is set; `heli_attack` changes 0. The M06 build with its
  two boss routs forced to GUN_ATTACK in memory: 2 set back, 0 misfits.
- `kl_map_ai.py` `pairfix`: logic read case by case (chains 5 -> 6 -> 7 and 12 -> 13 -> 14, a build made with
  the corrected converter, a second run): no double move, a clash is refused. No rule was weakened: `faults()`,
  `verify_levels.py` and `kl_fa.check` are untouched.
- Nothing outside the worker's five files is the worker's (the other modified files carry other tracks' work).

## 3. Checks re-run

| check | worker's line | mine |
|---|---|---|
| verify_levels (in memory, nothing written), corrected converter | problems 0 on six levels | problems 0 on M01_FA_A, M02_FA_A, M03_FA_A, M06_FA_A, M09_A, M09_B |
| objects that differ, HEAD's converter against the working tree's | ZSquadScript 26, ZHavokRigidBody 1, HeliFly 2, TriggerBox 1, ZFFActor 57 | the same, per level too (6 / 1 / 1 / 8 + 1 + 2 / 2 + 21 / 9 + 36) |
| `kl_fa.py stock` | 0 CRASH / BROKEN | 0 |
| pairfix report on the five builds | 6 / 1 / 0 + 1 enum / 8 + 1 box + 2 left / 2; faults 0, 0 | the same lines |
| pairfix written (M06, into my scratchpad, deleted) | only the .prp differs; 165 agree | 31 members, only `F01_Main.prp` differs; beside the archive only `steps.json`; a SECOND pairfix on the output lists 0 squads, 0 boxes; 154 list fields (all but field 8) filled / empty as a fresh conversion, 0 differ; 0 misfits, 0 dead paths, faults 0 |
| negative | - | the old builds are listed by pairfix (they 'fail'), the fixed output is not; the HEAD converter also passes verify_levels with 0 - that check cannot see a pairing fault, as expected |
| the five builds | soldiers 181 rows, fields 9..12 = 1; vehicles 97 rows, 5..8 = 1 | 20 + 19 + 22 + 21 + 99 rows, 9..12 = 1.0 on all, health 80..300, none <= 0; 9 + 7 + 10 + 3 + 68 vehicle rows, fields 4..9 = 1000, 1, 1, 1, 1, 1; Definite / None as reported |
| no Dead Men item enum, no grenade on an NPC | 0 | 0 `eFF2Item` on a node that is not on an F07 path; fields 3..5 empty on every actor but the one machine-gunner; the eight grenade / launcher renames go to the same template name in both games' bindings |
| no Kane / Lynch option on a Dead Men object | 0 | 0 (only `eONLY_LYNCH` on F07 paths) |

## 4. Counterexamples tried

- A squad with a misplaced list that pairfix misses: none. My own scan of every `ZSquadScript` of the five
  builds for entries in fields 5, 6, 7, 9, 12..18 finds exactly the squads pairfix lists (Retomoto: the two).
  M09_A / M09_B share no scene path among the objects pairfix looks at (197 objects, 0 collisions).
- A stock level with 'attack' on a helicopter without a weapon: none (49 of 49 armed).
- A stock box with DD field 8 set, a stock actor with DD field 18 set: none.
- An object called clean that is not: none found in soldiers, vehicles, items, enum names of the five builds.
- What is still open on the maps after the fixes (all named by the worker, none fixed): 5 squad modifiers of
  the Retomoto build have `eVIM_NotSet` where Dead Men said Double / Normal / Half range; the Dead Men-only
  modifier enums are dropped; the four helicopter routs of M06 lose three bools.

## 5. Defects

### S1 (should) - the proposed live checks cannot tell success from failure

- **M06 (check P1).** In the build, `Triggers!US_UnderFire_Counter` and `Triggers!JPN_UnderFire_Counter` both
  have count field 0 = 1 and each NAMES THE OTHER in its list. Seven of the eight squads have the US counter in their
  'hostile seen' list (Dog Days list 7, field 11), which was always paired right. So the first man who sees a
  hostile starts both counters, both boss timers and the hunts - before and after the fix. With seven AI
  heisters on the map that happens within seconds of GO. 'The gang's timer starts' will be seen on the OLD
  build too.
- **M01 (check P2), M02.** The 'attacked' entries of `CheckFront`, `KitchenBoy` and `3rdFloor_Guard_01` are a
  subset of the same squad's 'hostile seen' entries. A guard who is shot turns and sees: the same routs start.
- KLHook.log has no line for a squad event (the worker says so). So a run can only show 'loads, reaches GO, no
  fault'. If the lead writes 'pairing seen live' after P1 or P2 it is a false entry.
- Where a difference CAN show: M01's four `Civilians!` squads (`LeavingWoman`, `Waitress`, `LeavingMan`,
  `GangMembers`) have ONLY an 'attacked' list (-> `FrontMall_01` flank, `GangStartTimer`); Retomoto's
  `Squad_InFront` regroups at one man left instead of at half. Both need a build without the seven bots to be
  read cleanly. And three of the four M01 squads are ONE CIVILIAN each (`ZCivilian`): the two senders of
  'attacked' that were read are `CPPScript::ZSoldier` slot 105 (0x5a8140, the call at 0x5a82b3) and slot 96
  (0x8473a0, the call at 0x8474df); `CPPScript::ZCivilian` has other functions in those slots (0x49cb50, and a
  bare `ret` at 0x66b570) and does not derive from the soldier class. 0x7cc4a0 has two more callers, 0x582fc2
  (not read) and 0x61752e (beside the calls for lists 5 and 8: the network replay). So for a civilian's squad
  the list may never be sent, in either game. That leaves `Civilians!GangMembers` (two soldiers) as the one
  squad of the four maps where the fix can be SEEN.
- Fix: say in the audit that the live runs are regression checks only and the proof is the code. For a real
  proof either one log line in the hook at kl2 0x7cc4a0 (squad in ecx, list `[ecx+0x174]`, sent byte
  `[ecx+0x15d]`) and 0x42dfa0 (list 8), or a probe build where one squad's 'attacked' list alone names
  something unmistakable.

### S2 (should) - the effect on M06 and M02 is overstated, 'or never' is not what happens

The summary says the fix 'changes how the map plays' on M01, M02, M06 and section 1.2 says M06's gang timers
are today started 'by Dog Days list 8's event ..., or never'. They are started today, through list 7 and the
cross-linked counters (S1). M06 is the map with the most CHANGED OBJECTS (8 squads) and next to no changed
behaviour; M02 the same (a subset). The real change is at most M01's gang squad (the three civilian squads
probably never send the event, S1) and two Retomoto squads. The lead should plan the roll-out by that, not by
the object counts: the risk to the difficulty the owner likes is small, and so is what a run can show.

### S3 (should, small) - `ZFFActor` DD18 is let through although no stock level has it; the code does not say so

The pairing is right by code. But the same audit refuses 'attack without a weapon' on a helicopter because no
stock level has it and the code behind it was not read; DD18 = 1 is in the same position (0 of 1,696 stock
actors; what the branch at 0x869b79 does was not read), and Dog Days' own civilians carry DD19, which a
converted civilian now does not. Today 0 objects of any build (the 57 are M09 civilians, none in the Retomoto
build; every Fragile Alliance actor has 0 in Dead Men). The caveat is in the audit's assumptions, not in the
`kl_convert.py` comment. Fix: one line 'NOT RUN, no stock precedent' at `LEVEL_MAPS['ZFFActor']`, and read
what DD19 is before a build with civilians of M09 is made.

### Notes

- N1. Dog Days list 8 is a real event, not 'never': six stock squads use it (L03 `...Squad_Patrol\Gate_HS\Way#01`,
  L06 `Squad_CIV\Alert\Way#01` twice, L10 three). It is sent from 0x76eab0 to the squad of the actor passed
  IN (not the caller's own). So on the builds on the tab Dead Men's 'attacked' wiring fires at that event,
  whatever it is ('HS' may be the human shield - not read).
- N2. Dog Days list 5 is sent from 0x4fc859, inside `CPPScript::ZIdleWalkGoal` slot 2 (0x4fc7e0). Stock use
  also has list 10 and list 11 on one squad each (the audit's count stops at 9).
- N3. The trigger table is not the whole list of the levels. Missing, all on M09 only: `Filter` 11 / 9,
  `CoopGate` 4 / 4, `KaneLynchBox` 2, `JumpPoint` 6 / 2 (0 -> 1 fields), `CheckPointSave` 3 / 2 (5 -> 7),
  `LookActivate` 1 (8 -> 10), `EndOfLevelTrigger`, `Blocker`, `TriggerPsychoMode`, `Action`, `ZMercSquad`,
  `ZFusionSquad`, `CCameraBox`. None is on a non-F07 node of the Retomoto build (my census), so no build is
  affected; a campaign port is.
- N4. 'Dog Days-only fields checked for a 0' omits `ZPatrolBehaviourRout` DD4..7 (b, f, b, f = 1, 50, 1, 200
  by usual value; 5 objects on M02 / M06) and `ZIdleWalkPathRout` DD6 (a blank default, 5 objects). Not read.
- N5. `re/pairings.md`: the paste block still has the old comments for `ZSoldierRout` ('by values only ...
  GUESS') and `ZVehicleEffects` ('GUESSES') under rows that now say 'proven'.
- N6. The list of 'tab builds' is already old: the Retomoto on the tab was replaced tonight, and
  `z_route4`, `z_route7`, `z_loot3` (made 04:02 .. 04:50, the last after the converter changed at 04:41) all
  still carry the OLD pairing - pairfix lists the same 6 / 8 + 1 / 2 on them. None was made from a fresh
  graft, so none has silently taken the new pairings. Whatever goes on the tab next needs pairfix, or stays
  old on purpose.
- N7. A second pairfix run prints 'left as they are' for every object it already put right (11 lines on the
  fixed M06): 'moved already' cannot be told from 'a later step took them'. Cosmetic.
- N8. `<work>\dd_typical.json` now holds the corrected converter's field set. A session that still runs the
  old `kl_convert` (another checkout with the same work folder) rebuilds it (44 archives) and writes it back;
  two at once can read a half-written file. I saw the rebuild when I ran HEAD's converter on a copy.
- N9. Vehicles: the task asked for every vehicle with its setting before and after; the audit gives counts per
  map. The counts are right.
- N10. Not the worker's: `.claude/workflows/retomoto-level-design.js` starts with `okaexport const meta` (a
  stray keystroke, file time 02:41) - that script does not parse.

## 6. What a live run would have to show

1. Regression only: each pairfix output loads, the round reaches GO (session state 0x19), no fault line,
   RESULT clean exit. That is all KLHook.log can say today.
2. Nothing on M06 or M02 is expected to look different (S1).
3. On M01 without bots: hit one of the two `Civilians!GangMembers` with no guard of `CheckFront` /
   `KitchenBoy` in sight; after the fix the `FrontMall_01` squad comes and the gang's own timer starts, before
   it does not. The three civilian squads are no test (S1).
4. Not observable: the trigger box (its lists are empty), the foam prop's priority, `ZFFActor` (no object).

## 7. What was done about each defect (track C, the pass after this review, 2026-10-11)

Appended by the worker who finished the track; everything above is the reviewer's text, unchanged. OFFLINE:
nothing launched, nothing written in a game folder, nothing committed, no build of the tab touched. Files
changed: `tools/kl_convert.py` (comments only), `tools/kl_map_ai.py` (`pairfix`: report and one refusal case),
`re/pairings.md`, `re/convert_audit.md`. No pairing, no value the converter writes and no check was changed.
Scripts: scratchpad `CF\`.

| defect, by its 'where' | fixed or refuted | what |
|---|---|---|
| **S1** - the worker's live checks P1 (M06), P2 (M01), P3; audit section 7 | **FIXED** (and two of its side claims REFUTED, below) | Re-derived squad by squad on the five builds (`f1_delta.py`, `f3_lists.py`): 33 misplaced entries, 18 doubles of a right list of the same squad, 15 named by another object, 0 by nothing else. The checks are rewritten as REGRESSION ONLY with the sentence 'do not write pairing seen live' (audit 9.3, and the final report's live checks); `pairfix` prints the same account for any build ('in play') and says in its last line that a run of the result cannot show the pairing; the comment at `kl_convert.SQUAD_LISTS` says it too. For a real proof the audit (9.4) gives the hook's owner the exact entry points - the event helpers 0x51c8e0 / 0x649d30 / 0x86b470 / 0x87ebf0 (lists 0, 2, 3, 4), 0x56d0b0, 0x6831f0, 0x720e70, 0x42dfa0, 0x7cc4a0, 0x6fd630 (lists 5..10), or the two send routines 0x77b820 and 0x79d6d0 - and what a run with that line must show to pass or fail. NOT DONE: the hook line (klhook is not this track's) and a probe build (no map is to be built in this track; the hook line is cheaper and proves more). |
| S1, side claim 'for a civilian's squad the list may never be sent, in either game' | **REFUTED** | The third caller of 0x7cc4a0 that the review left unread, 0x582fc2, is in 0x582fb0, whose only caller is 0x7b4920 = `CPPScript::ZCivilian` slot 1 (0x7b48f0), the case of script event 0x1d (switch decoded with `f2_switch.py`: index table 0x7b4bd8, jump table 0x7b4bb4). The soldier's slot 1 (0x608050) sends the same event 0x1d to its slot 105. So Dog Days' civilian DOES send 'attacked', without asking who attacked; it is Dead Men's that does not (0x6edcd0 has two callers, both `CPPScript::ZSoldier`; the civilian's event 0x1d case 0x711718 runs the flee routine 0x710f00; no inlined copy). Consequence, new in the audit (1.2, 9.5): three M01 squads of one civilian get a live 'attacked' list for the first time in either game. |
| S1, side claim '`Civilians!GangMembers` is the one squad of the four maps where the fix can be SEEN' | **REFUTED** | Its three targets are in `CheckFront`'s and `KitchenBoy`'s 'a hostile is seen' lists, and the gang's timer also in the box `Triggers!EnterDiner` (`f3_lists.py --who=`). No build has a squad where it can be seen. |
| **S2** - the worker's 'WARNING FOR THE LEAD'; audit 1.2 ('or never') and section 7 | **FIXED** | Both passages rewritten (audit 1.2 'Effect today', 7 'How much this changes the maps in play'), table 9.1 gives the change per squad, and the final report no longer warns of a change in how the maps play. 'Or never' is replaced by what Dog Days list 8 is, READ: a player starts close combat on a member (0x42dfa0 <- 0x76eab0, a routine of `ZFFActionCloseCombat`, the action the player's slot 225 makes for number 0x21, called from `ZFFPlayer` slot 87's 0x612c20). The third caller is read (above). The roll-out advice is now 'by behaviour: next to nothing, ride on the next build made for another reason'. |
| S2, the review's own 'remaining real changes ... two Retomoto squads' | **REFUTED** for both | `Squad_InFront` has 3 members: 'half dead' is alive <= members / 2 in whole numbers (0x47e4d8: `cdq; sub eax, edx; sar eax, 1`; members = `[x+0x48]`, +1 per member at 0x7b3907) and 'one left' alive <= 1 (0x47e4f4), in the same update - no change. `Squad_AtrTop_Reception`'s 'attacked' entry (its own hunt rout) is already in its 'something is noticed' list. |
| **S3** - `tools/kl_convert.py` `LEVEL_MAPS['ZFFActor']` comment | **FIXED** | The comment says 'NOT RUN, no stock precedent' with the counts (0 of 1,696 stock actors; Dead Men 197 of 1,668, per level - `f6_actors.py`), and what was read after the review: the branch DD18 opens (0x869b79, `ZFFActor` slot 57, a hit / collision filter) is Dead Men's 0x5dda28 step for step, which is why it is let through while the helicopter's unread 'attack without a weapon' is not. DD19: its readers are found (`ZFFActor` slots 364, 400, 406..408, 421..423; accessor 0x5e1250 used by `ZLieWounded`, `ZWounded`, `ZHitAnimTask`, the session handlers), its meaning is NOT established - said in the comment, in audit 5 and in the not-done list. |
| N1, N2 | done | List 8 read (above). List 5's sender is `ZIdleWalkGoal` slot 2; list 10's is 0x6fd630 <- 0x8e5600; list 13 has no sender through the common helper; stock use of lists 10 and 11 added (`f10_use.py`). The whole sender map is in audit 1.2. |
| N3 | done | The trigger table has the M09-only classes, counted again (`f7_census.py`), with the two the review did not list (`AIMonitor`, `Elevator`: 1 + 1 in the Retomoto build, identical layouts). |
| N4 | done, and extended | `ZPatrolBehaviourRout` 4..7 and `ZIdleWalkPathRout` 6 are in the list and in the ranked table; the census of all 41 changed class levels with objects on Dead Men nodes (`f8_changed.py`, `f9_newfields.py`) added `ZMatPosAnimProxy` (2 on Retomoto, three new fields), `ZLightFlicker`, `ZGEOM`, `ZSNDOBJ`. None read in code. |
| N5 | done | `re/pairings.md` paste block: the two comments now say what is proven. |
| N6 | done | Read only, 05:50: the tree in the game folder is `z_route3\M01`, `z_m02s1\M02`, `z_cover3\M03`, `z_route\M06`, `z_route7\retomoto_full`; pairfix (report only) gives the same lines per map on all 18 builds looked at; the audit's scans were run on the two installed builds it had not named (`f12_installed.py`, `f13_scan.py`). |
| N7 | done | `pairfix` has a class 'right already'; a second run on its own output lists there what the first moved and moves nothing (five builds, `t_pairfix.py`). Two neighbouring lists that are both in place are recognised instead of refused (`t_chain.py`, in memory). |
| N8 | recorded | Audit section 7 and the final report: other sessions must take the corrected `kl_convert.py` before they convert. No code change. |
| N9 | done | Every vehicle by name with setting and health before and after (audit 3). |
| N10 | not this track's file | Passed to the lead in the final report (`.claude/workflows/retomoto-level-design.js` line 1). |

Checks run again after the last edit (last lines): `verify_levels.py` from the work folder `problems: 0 []` x 4;
`t_convert.py` 'all six levels: problems 0; total objects that differ: {ZSquadScript: 26, ZHavokRigidBody: 1,
HeliFlyBehaviourRout: 2, TriggerBox: 1, ZFFActor: 57} ... PASS' (against the converter committed at HEAD, compared
by name - a first run that compared flag lists by key index showed 36 `ZFFItemTemplateWeapon` nodes of M06 as
different: an artefact of the comparison, the new key shifts the indices); `kl_fa.py stock` '0 CRASH / BROKEN';
`t_heli.py` PASS; `t_pairfix.py` 'pairfix write test: PASS' (five builds written into the scratchpad and
deleted); `t_chain.py` PASS.
