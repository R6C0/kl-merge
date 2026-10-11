# Review of track A ('AI heisters held by loot they cannot take'): re/bots_loot.md, tools/kl_fa_bots.py, <work>\build\z_loot3

2026-10-11, adversarial reviewer. OFFLINE: the game was not started, nothing was written in the game folder or in
any build folder (kl_maps.audit was run with its two report files redirected to the scratchpad), nothing committed,
no tool edited. Scripts of this review: scratchpad `rev\` (imm.py, callers.py, people.py, objs.py, money.py,
chain.py, legs.py, stage.py, holds.py, relays.py, stock.py, stockwin.py, crc.py, audit_ro.py).

**Verdict: ACCEPT WITH FIXES.** The code reading is right where I re-read it, every reported check line and sha1
reproduces, the builds reproduce byte for byte from the tools as they stand, the new rule fails the old builds and
I found no place, leg or loot-pull on the four new builds that the rule itself would call a trap. What is NOT
established is why the clerk held the bots - and one of the worker's own two candidates would make the fix for
exactly that clerk miss. One sentence of the report is wrong about that (D1), one piece of live evidence is
misread (D2), the check has blind spots (D3, D4) and the live check as written cannot show its own second
criterion (D5).

## 1. Re-derived in kl2.exe (own disassembly, capstone through debug/kl.py)

| claim | what I saw | verdict |
|---|---|---|
| the window 800 / 400, 400 / 200 | 0x8b9555..0x8b9589 load tuning +0xc1c / +0xc20 / +0xc24 / +0xc28; list one: `fabs` of the vector's 2nd component against +0xc20 (0x8b9641, `jnp` skips when larger), squared length against (+0xc1c)^2 (0x8b9678). Constructor: 0x530aa2 `fld [0xb3f4ac]` = 800.0 -> +0xc1c, 0x530ad8 `[0xb243f4]` = 400.0 -> +0xc20, 0x530b0e 400.0 -> +0xc24, 0x530b44 `[0xb18ba0]` = 200.0 -> +0xc28 (objects with vtable 0xb5ec74 = FloatVar, freed in the loop 0x530c20, 0x312 of them) | TRUE |
| 'no file feeds them' | 0x52ad20 has one caller (0x50b132); 0x776270 (the copy) is named only by a vtable slot at 0xbc0fb8. I did not follow that slot | plausible, not proven |
| byte +0x6c: set for every type, cleared by taken / 'Deactivate' | init 0x4d8e80: type 2 -> `mov [esi+0x74], al` (= 0) at 0x4d8ea6, type 1 -> +0x6d = 1, then `mov [esi+0x6c], bl` (= 1) at 0x4d8ec4 for all. 0x4e3f76 and 0x4c95e6 `mov [esi+0x6c], 0`, both behind the host test 0x8df480. Candidate filter 0x8b95f2 `cmp byte [edx+0x6c], 0`; taken = 0x4536e0 `[ecx+0x34] <= 0` | TRUE |
| the message ids | registration stubs: 0xafac00 'AI_TRIGGER_WITH_ACTIVATOR' -> object 0x168c3c0 (id +8 = 0x168c3c8), 0xafac20 'Activate' -> 0x168c3d4, 0xafac40 'Deactivate' -> 0x168c3e0, 0xafac60 'DoorOpened' -> 0x168c3ec | TRUE |
| slot 26, 0x6cdb40 | order of the tests: 'Activate' first (0x6cdb48); then the node's flag bit 10 (0x6cdb65..0x6cdb76: set -> return 1, nothing done); then state +0x64 in {2, 3} -> return 0 (0x6cdb78); then the take (needs +0x74, 0x6cdb8f), 'DoorOpened' (0x6cdc06), **'Deactivate' last (0x6cdc1b -> 0x4c95d0)** | TRUE - and see D1 |
| 'Deactivate' = 0x4c95d0 | host: +0x6c = 0; if stored field 6 (+0x48) then 0x4bf120(node); state = 3; tail 0x7f3110 = the marker routine with icon type 0 (0x571b40 is the same routine with type 0x12 / 0x13). The engine calls 0x4c95d0 itself from 0x5f1b33 (session state 0x1f, every object still in play), 0x7e3949 and 0x8ea5eb - so 'state 3 with money left' is an engine state, not a new one | TRUE; safe as an operation |
| the test 0x451920 | 4.0 s (tuning +0xc34) since `[[actor+0x54]+0x30]` (0x451935..0x451968); record +0x78 >= 1 (0x4519d4); stage 3 and vehicle 3 / 4 -> 0; five candidates; status bit 0x2000 -> 1.0 (0x451a59); field 11 -> 0x454c20 (0x451a88); else path, `cmp [ebp-0xb0], 1 / jg` -> 1.0 (0x451b36) | TRUE |
| the action 0x7bc7d0 | nothing while bit 0x2000 (0x7bc8ca); from index `[this+0x2c]`; first candidate with path count > 1 -> 0x8997a0 (0x7bcab7); it never reads +0x5c. NEW: with count <= 1 it waits 0.5..0.6 s (0x7bc9be..0x7bca0c) and tries the next candidate; none -> flag 8 of actor +0x57d | TRUE |
| the trigger 0x626ec0 | class [0x1548c7c] or, in Arcade (0x7f6850), class [0x1547b24] with `[[obj+0x54]+4] == 2` (0x626fb2); byte +0x44 = 'people only'; inside test 0x783e60: entity +0x30..+0x38 of both, radius +0x40 + 40.0 (0x783f06) | TRUE |
| rules slot 201 / the grab | 0x56f6e0: Arcade 0x19; actor: virtual +0x3d0 must be false, record index != -1 -> 0x8e8750. State machine 0x727cb0, jump table 0x728204 = [0x727ce3, 0x727f82, 0x7281ba, 0x727db8]: state 1 stops on taken / object state != 1 / bot's +0x576 != 1, else sets state 2; pays min(field 4, left) when the clock is up (0x72806d..0x728087) | TRUE |
| the controllers beside the money | ZTriggerBox2 and ZOnlineSpeakTrigger slot 26 = 0x4774b0, which compares with `[0x1688f34]`, registered at 0x8811d0 as 'AIBlocker'; ZGROUP slot 89 (+0x164) = 0x547000 = `xor eax, eax` | TRUE |
| 'children get nothing' (0x7592e0 -> slot 71 = 0x446010) | not read to the end | not re-derived |
| the container chain 0x419f80 -> 0x766e50 -> 0x868fb0 -> 0x4fb580, the KickDoor test 0x454c20 | not re-read | not re-derived |

Stock (stock.py, stockwin.py over F01..F09 and L00..L11): a TriggerDelay2 names up to 18 targets, a RelayMessageList at
most 10 (F01, L04); no stock sender of 'Deactivate' has a target with an OnlineMoneyCtrl; the controller key is
'KickDoor'; stock money sits in self-opening containers, plain objects and on armed people only (F05 F07 F09) -
none on a civilian, no CONTAINER object without a container; **no route box of a stock squad lies inside 800 / 400
of an object the new rule calls un-takeable.** So no stock level has the form the rule forbids.

## 2. The diff of tools/kl_fa_bots.py (592 lines; the only tool the worker changed)

- With `window` off `plan` / `make` take the old branches (objs = [], no `timer_station`, no `off` key, no split).
  Proven: I rebuilt M02 with `--no-window` into the scratchpad - archive sha1 257a45ff9cdf = `z_final\M02`.
- With `window` on, rebuilt bots builds M01 / M02 / M03 from the tool as it stands NOW (it was last saved 05:08,
  after the builds of 04:41..04:48): sha1 b01afabc1fd9 / 4761bc51e6ce / 34d8638e9325 = `z_loot3\_bots\*`.
- The dynamic step re-run with track B's kl_fa_bots_dyn.py of 05:36 (it was edited twice after the builds):
  `z_loot3\M01 M02 M03` come out byte for byte (4eedd127bef4, 52b00efdda21, ed62f58763b6). M06 = `z_route\M06`
  (1d799830eeee), its bots build = `z_final\M06` (042c10e62cf5).
- One existing rule WAS widened (the report says 'no existing rule changed', the .md says it): a squad relay that
  sends 'Deactivate' to nodes with an OnlineMoneyCtrl used to FAIL and passes now - for ANY money node (D8).
- Nothing outside the worker's files: the other modified files in the tree are tracks B / C / E (kl_fa_bots_dyn.py,
  kl_fa.py, kl_convert.py, kl_map_ai.py, klhook/*); every folder written between 04:41 and 04:50 is under z_loot3.

## 3. Checks re-run (logs: scratchpad `rev\out\`)

All lines as reported: `kl_fa_bots.py check` on the bots builds PASS (3 / 2 / 3 / 2 NOTE), `diff` ('only the squad was
added', + 2 exit boxes cut on M01, + 1 drop link on M03), `kl_fa_bots_dyn.py check` PASS (2 / 4 / 3 / 3 NOTE; again
PASS with the 05:36 tool), `kl_impact.py` problems: 0 x 4, `kl_maps.py audit` PASS (1 / 6 / 0 / 6 known), `kl_map_guns.py
check` problems: 0 x 4, `van-check` 0 fault(s) x 3, sizes equal to the tab's builds. Relays of M02: 21 'Activate' /
21 'Open' / 14 'Deactivate', 23 panes, 23 containers, 3 civilians, largest list 10, 0 unresolved, every glass-only
case named by all seven squads. Negative tests: `z_route\M02` FAIL (14), `z_m02s1\M02` FAIL (14; M6_01 / M5_01 for
Squad#02 495 / 510, #04 633 / 640, #06 409), `z_route3\M01` FAIL (7), `z_hop\M03` FAIL (7), `z_route\M06` PASS,
`rt_full7\retomoto_full` PASS (9 NOTE); every FAIL line of the old builds is a loot-window line (0 others).

## 4. Counterexamples tried

1. **The loot pull is transitive, the rule is not** (chain.py). A bot pulled to a takeable object up to 800 away
   stands there with a new window. Closure over takeable candidates, six hops, with the relay state of each place:
   nothing un-takeable comes into reach on `z_loot3\M01 M02 M03 M06` (it finds the waitress at hop 1 on
   `z_route3\M01`, so the search bites).
2. **A bot walks between the places** (legs.py). Mesh paths (Nav.path) between consecutive places sampled every
   40, from the leg into the first ENTERS place on: no sample inside the window of something un-takeable on the four
   new builds (on `z_route3\M01`: the waitress, 57 from a leg).
3. **Stage 1 comes earlier than the rule assumes** (stage.py) - D3. On `z_loot3\M02` in 12 of 21 walks the mesh path
   crosses the one ENTERS box (EnterBankTrigger_01, x 711..2011, z 1399..2999) one or two places BEFORE the first
   place inside it, and Squad#02 / #04 have side holds inside the box that hang on the place before i1 and are
   therefore skipped. No trap follows here (018 fired long before); the rule would not have seen one.
4. **Stock**: section 1 - none.
5. **The live logs against the theory** (money.py; objs.py for the part sizes) - D2:

   | run | jewel store (21 objects, 1,800,000 with the male clerk) | then |
   |---|---|---|
   | L8 | 1,600,000 by 02:44:12; one object paid in 20,000 parts: bot 3 alone, +20,000 +40,000 +40,000 | watch shop +460,000; held at the clerk |
   | L10 | 1,600,000 by 03:02:21; 03:02:13.2 bots 1, 2, 3, 6 +20,000 each in ONE log tick, 03:02:14.3 bot 1 +20,000 | watch shop +460,000; held at the clerk |
   | L11 | 1,700,000 by 03:13:53; bot 4 alone +20,000 +20,000 +40,000 +40,000 | bot 5 +50,000 +50,000 at stage 3 (the credit card) |

   The jewel store has TWO objects of 100,000 paid in 20,000 parts: `male_clerk` (0.7 s, radius 75) and the
   self-opening `PC0406_M02_FA_Cashdrawer_01\Money_Attachroot` at (1318, 575, 2589) (0.5 s, radius 125). In every
   run exactly ONE of them was paid, never both. Four bots getting their first part in the same tick (L10) is what a
   container that becomes active under bots already standing there looks like; a clerk who is 'takeable from the
   start' would be paid as each bot arrives. So 'four bots took the male clerk's 100,000' is not established, and
   with it goes the only live observation of a bot taking a civilian's money at all.
   The same sums say: in L8 and L10 the bots LEFT the jewel store with 200,000 untaken inside the window of all
   their places (100,000 of relay-opened jewel cases + the clerk or the drawer). 'A candidate that is not taken
   holds the bot for the round' (section 0.3 of the .md) is therefore not generally true; it is confirmed for a
   shut case (L11: two bots in front of M6_01 / M5_01 while the van came three times) and seen for one clerk.

## 5. Defects

**D1 (must) - 'the fix does not depend on which [A or B]' is wrong for B.** The handler tests the hidden bit and the
state BEFORE it looks for 'Deactivate' (0x6cdb65..0x6cdb7f against 0x6cdc1b). If the clerk's group is hidden once
she has gone (candidate B of the .md, left open), a 'Deactivate' that arrives after that is dropped exactly like
the take message and byte +0x6c stays set: the same hold as L8 / L10. In `z_loot3\M02` `female_clerk` and the cafe's
`Clerk_Female` are named only by `038_Relay_money_off`, which fires when a bot has LEFT the jewel store (in L10's
times after 03:02:21; the bots found her gone at 03:03:10). Fix, cheap: name every civilian in the FIRST timer of
the route (018: about half a minute after GO instead of two; the money is lost to everybody either way - it only
narrows B's time, it does not rule B out), or take the OnlineMoneyCtrl
and its TriggerBox2 off the civilians' groups in the build (stored, needs no message; kl_fix_lean's `--ctrl` is the
form). Correct the sentence in the .md and the report.

**D2 (should) - the male clerk 'was paid' is not shown; the cash drawer fits better** (section 4.5). Consequences in
the .md: section 0.4 / 3 ('as four bots took the male clerk's'), assumption A's timing argument ('reached 85 s
after GO ... she had time to go'), 'the human gets it by standing at the clerk'. Say 'not established'; say that the
bots left 200,000 at the jewel store in L8 / L10 and why that does not contradict the rule (or that it does).

**D3 (should) - check(): where stage 1 begins.** `i1` = the first PLACE of the main chain inside an ENTERS box. A bot
has the stage from the moment its body is in the box: on the leg before, at a hold beside the chain (`at_n > i1`
drops the holds that hang on place i1 - 1 even when they lie in the box: Squad#02 (1118, 500, 2069) and (1179, 500,
2452), Squad#04 (1256, 500, 1580) on `z_loot3\M02`). Fix: start the walk at i1 - 1 with its side holds, or take the
first sample of the path inside the box (first_exit_entry does that for the exit boxes).

**D4 (should) - check() says nothing about a plain object nobody on the bots' mesh can stand in the trigger of.**
census() prints it (Retomoto `TM_MoneyStack_022` 300,000, Late Night Opening's two office jewels 250,000), check()
neither FAILs nor NOTEs it, although the .md itself calls it 'the first suspect'. For the office jewels the live
runs answer it (the bots left the jewel store three times); for the Retomoto stack nothing does. At least a NOTE.

**D5 (should) - live check W1 cannot show its second criterion, and one bound is wrong.** (a) The `hop: bot n stage s:
node (...)` lines of L10 came from a KLJoin.ini with a dummy [CrewHop] (From (0, 9000, 0), Dry=1) in the installed
map folder; `z_loot3\M02` has no KLJoin.ini, so 'no block of hop lines at (-1772, 500, 2792)' is true whatever
happens. (b) 'the bots' total at most 2,160,000' - the credit card (100,000, taken by bot 5 in L11) and the cafe's
drawer (60,000) are takeable off the route: up to 2,320,000 is healthy. (c) Nothing in the log says whether
'Deactivate' arrived. See section 6.

**D6 (should) - what the human sees needs the lead's / owner's word before the tab is swapped.** All glass of the
jewel store and four watch cases burst by themselves while the first bot is still in the upper mall (about half a
minute after GO: the worker's estimate from L10, not measured; Squad#08 has no hold before its timer and fires
first), the other eight when the first bot leaves the jewel store; 215,000 / 40,000 / 30,000 of money on civilians
is gone for the human too. The early time is not the loot window's doing but CASE_GUARD 1150 (track B's hold in
front of the kept timer, .md section 9).
The male clerk held nobody in three runs; the waitress and the bank's civilians held nobody in R13 / H0. Only the
watch shop's clerk is known to hold. The report says all this; it is listed because it is a decision, not a detail.

**D7 (note) - plan() switches off any civilian's money without looking at stored field 6.** With field 6 set
0x4c95d0 hides the node (0x4c95e2..0x4c95f6 -> 0x4bf120) - the civilian's group. All five civilians of the three maps
have 0 (people.py); a guard (skip + NOTE, or FAIL) costs one line.

**D8 (note) - the relay rule accepts 'Deactivate' to any OnlineMoneyCtrl.** A squad relay that switches off real loot
passes. Accept it only for money on a ZCivilian's group (what plan() makes).

**D9 (note) - the FAIL text states more than is known.** 'Its own loot tactic holds a bot in front of such an object
to the end of the round' is printed for cases that are opened at the door (the form that looted both stores in L8 /
L10) and for the male clerk. The .md says 'the stricter rule'; the tool should too.

**D10 (note) - small things in the code.** `'bcdefghij'[i // RELAY_MAX - 1]` raises above 100 targets of one message;
with `window` on bots.txt still prints 'cases of stop n: ... each is opened by 3 bots' (line 30 / 31 of
`z_loot3\_bots\M02\bots.txt`) beside the loot-window lines that say 'every squad', and `w['containers']` / `w['glass']`
of a stop whose units all moved to the stop before keep the old numbers; the module docstring's 'WHAT A SQUAD IS'
is the form of 2026-10-10 (the worker says so).

**D11 (note) - the builds stand on another track's uncommitted tool.** They reproduce with kl_fa_bots_dyn.py of 05:36
(section 2); run the dynamic step and its check again from `z_loot3\_bots` / `_pre\M01` when track B is committed.

## 6. What a live run has to show

Late Night Opening, `z_loot3\M02` (after D1), TEST hook, [Bots] Enable=1 Log=1, the player idle. Put the dummy
KLJoin.ini of L10 beside the archive (one [CrewHop] far off the map, Dry=1, Log=2) or the position lines do not exist.

- SUCCESS: every living bot `heist stage 0 -> 1`; money at the jewel store about 1,600,000..1,700,000 in 50,000+
  steps (L8 / L10 / L11), then 20,000 / 5,000 steps at the watch shop to about +460,000; then `1 -> 2`, `-> 3`, van
  state 3, `aboard` / `status6`; no living bot `in-play g1` at the end; no run of `hop:` lines with one `node` for
  several bots. One clean run is fair evidence (the hold came twice of twice, for every living bot); two are better.
- FAILURE A: bots again on (-1772, 500, 2792) with 75,000 less than everything = 'Deactivate' did not take (D1's
  case, or the message does not reach the controller at all).
- FAILURE B: bots on one point somewhere else = an object the rule does not know; `kl_fa_bots.py census` for the
  object nearest to that node (D4).
- To tell WHY the clerk held them (one extra run, a human at the keys): stand at `female_clerk` (-1769, 503, 2801) in
  the first minute - is the '$' there, is her 75,000 paid at her post, does it follow her when she runs, is it gone
  after the first bot left the jewel store. That separates A from B and says whether D1 matters.
- W2 of the worker (the glass, the male clerk's '$') is a look, not a criterion: if the glass stands and the jewels
  go, the build still works.

## 7. Appended by the worker's second pass (2026-10-11, about 06:30): what was done about each defect

OFFLINE; changed `tools/kl_fa_bots.py` and `re/bots_loot.md` only; nothing committed. The builds this review looked
at are now in `<work>\build\z_loot3\_v1\` (their sha1 are the ones of section 2 above) and are SUPERSEDED - they
fail the check as it stands. The new builds are `<work>\build\z_loot3\M01 M02 M03 M06` (sha1 0a0ad56244ad,
a004c014c5ce, 5f014f12ee6c, 1d799830eeee); every check of the task was run again on them, last lines in
`re/bots_loot.md` 8, logs in `z_loot3\logs\` (`neg_summary.log` for the builds that must fail). Scripts of the pass:
`<work>\research\agent_scripts\a-loot\pass2\`.

| | what was done |
|---|---|
| D1 (must) | FIXED, by the stored form, not by the cheaper of the two proposals. I re-read 0x6cdb40 .. 0x6cdb93: `'Activate'` is compared at 0x6cdb48, then 0x6cdb65 .. 0x6cdb76 return 1 when bit 10 of `[[this+0x24]+4]+0x3c` is set, 0x6cdb78 .. 0x6cdb84 return 0 for state 2 / 3, and only then come the take (0x6cdb87, needing `+0x74` at 0x6cdb8f) and the later messages. So a late `'Deactivate'` under B is dropped: confirmed. Naming the civilians in the first timer would only narrow B, so `build()` now takes the `OnlineMoneyCtrl` and its own `TriggerBox2` off the civilian's group (`strip_money`; diff allows exactly that; no `'Deactivate'` relay is made). What is left is the form of five civilians the same maps already run (ZGROUP + OnlineSpeakTrigger + a ZCivilian's actor: Hot Coffee 2, Withdrawal 3). M01 M02 M03 rebuilt. The sentence is corrected (`re/bots_loot.md` 3) |
| D2 (should) | FIXED in the notes. Reproduced: `objs.py` on `z_route\M02` shows `male_clerk` 100,000 / 20,000 / 0.7 s and `PC0406_M02_FA_Cashdrawer_01\Money_Attachroot` 100,000 / 20,000 / 0.5 s, self-opening, at (1318, 575, 2589); `money.py` on L8 / L10 / L11 shows exactly one object in 20,000 parts paid at the jewel store per run (L10: four bots in one tick). The claim is withdrawn, the 200,000 left behind is said, the hold is called 'seen for a shut case and for one clerk' (sections 0.3, 0.4, 3, 5) |
| D3 (should) | FIXED in `check()`: the stage begins at the place the bot is walking to when the stand-in path (sampled every 20, feet or chest) is first inside ANY stage box (ENTERS, EXITS, BOARDS, level exit: 0x5dd890 only raises, the test wants >= 1), or at a hold beside the chain that lies in / is reached through one. On the new M02 that is one or two places earlier for five squads; no trap there. The old builds fail as before (14 / 17 / 7 / 7), the park and Retomoto pass |
| D4 (should) | FIXED as NOTEs: a plain object in the window whose trigger no point of the bots' mesh part reaches (Retomoto `TM_MoneyStack_022`: `rt_full7` now PASS with 10 NOTE; the two office jewels), and the same window test on the way between the places (every 40; a NOTE because a bot was seen held only where it stood). Not a FAIL: the office jewels held nobody in three runs and nothing is known about the stack |
| D5 (should) | FIXED in the notes (`re/bots_loot.md` 10): the success criteria are those of section 6 above; the position lines through the lead's `live.py --poslog`; the bound 2,320,000 (2,570,000 in the level after the edit, 250,000 out of reach); 'did Deactivate arrive' is gone with the message; the human run that separates A from B stays, on the tab's build where she still has the money |
| D6 (should) | NOT DECIDED HERE - it is the owner's. Laid out with the choice per map (M02 needed; M01 / M03 optional against the tab's builds that ran clean) in `re/bots_loot.md` 6, in the RECIPE comment and in a NOTE of every check of such a build. No waiver was put into the check. The early glass is unchanged (it is the guard for track B's hold); `--case-guard N` is there for when that step emits the kept timer before its hold |
| D7 (note) | gone: nothing sends `'Deactivate'` |
| D8 (note) | FIXED: the relay rule is the one of before the first pass (a `'Deactivate'` relay FAILs; the `_v1` builds now fail on it) |
| D9 (note) | FIXED: the FAIL text carries what is known per reason (`WHY_KNOWN`) |
| D10 (note) | FIXED: numbered suffix beyond `_j`; no stale 'cases of stop' lines or counts with the option; docstring updated |
| D11 (note) | Re-run three times with three states of track B's file (7613e7602a74 at 06:08, 12fdbedb87f5 at 06:14, aa7f65f8d592 at 06:32): the same four archives each time. Still uncommitted and still being edited: once more when it is committed |

One thing found on the way that the review did not ask about: `diff`'s new civilian rule was tested to bite
(`difftest.py`: the group also without its speak trigger / the civilian without a controller / the edit not declared
in bots.json - each UNEXPECTED), and a `--no-window` build of M02 is still `z_final\M02` byte for byte.
