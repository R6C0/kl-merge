# Hasta (DM11B, slot F04): why the 8 "late" plaza police of --rest-late never start (2026-10-19, rechecked)

Offline, static. First written by one agent, then every claim re-checked independently against tools/kl_fa_hasta_layer.py, the staged zips
(tools/kl_fa.py load), kl2.exe build 0490 (debug/dasm.py) and the L100 section of `<DD>\KLHook.log` (read only, file lines 1418720 .. 1437640,
01:15:41 .. 01:22:56). Nothing launched, nothing written but this file.
FACT = read in code or data by the recheck. MEASURED = computed from the L100 log. GUESS = not proven.

## 0. Answer

1. FACT. In police2 (131c8c2b) and police3 (43a7c699) Way#01 and Way#02 are two GatePath nodes under ONE GateGroup (node 19991). A GateGroup
   lets exactly one of its paths through, once (kl2 0x7fd5a0: `if [group+0x30]==0 { [group+0x30]=1; send to the list } else return`).
   The stair-top box fires Way#01 first and takes the pass. The delay's message to Way#02 (45 s or 120 s later) is dropped by that check.
   So the 8 men get no start message from this wiring, whatever S is. The `--rest-late` design cannot work as built.
2. MEASURED (L100) agrees: the two ExitStreet_Left men (Way#01) moved and died; the other 8 never changed position or health in 195 lists.
3. The census counts the 8 from level start, so its alive count cannot show a late start. Position and health can.
4. Fix proposal (not applied): the delay names the three `10_RunToCover` entries itself, bypassing the gate (section 5).

## 1. What `--rest-late=S` writes (FACT, builder and both zips)

Flag parse: tools/kl_fa_hasta_layer.py line 1573; allowed 1..600 s; refused with --floor-late (line 1574). `REST_KEEP = ('ExitStreet_Left',)`.
`wire()` lines 991-1009 with REST_LATE set:
- Way#01 GatePath f0 = the ExitStreet_Left `10_RunToCover` (kept); Way#02 f0 = the other three squads' entries (Exit_Left, Exit_Right, ExitStreet_Right).
- Spare one-shot `Gameplay!010_FirstFight!RivalMercVan!TimerVanGo` (node 20000, TriggerDelay2): f0 = S, f1 = 0, f2 = -1, f3 = 0, f4 = [Way#02].
- Floor box `tb_RIGHT_TheySpotYou` (19996, TriggerBox, eTGS_AllInside, ECPS_FA_MERCONLY): its list ends `..., DisableVisionBlocker!Timer, Way#01, TimerVanGo`.
- Backstop `RivalMercVan!Timer` (20001, 300 s) no longer names Way#02; its list is DisableVisionBlocker!Timer, 070_..Timer_SandbagsDeactive, 070_..Timer.
- Decoded from the zips: 19991 is a ZGROUP with controller GateGroup (no fields); 19992 Way#02 and 19993 Way#01 are ZBoxPrimitive with GatePath. The only
  objects naming a Way are the floor box (Way#01) and node 20000 (Way#02). police2 and police3 differ only in node 20000's 120.0 vs 45.0
  (zip md5 131c8c2b58550bc5df4289fbe1111229 / 43a7c69972e80d9943a09e963902fd93; both 259,430,078 bytes).
- NAMING TRAP: the role `'van timer'` in the builder (line 462) is `RivalMercs!DisableVisionBlocker!Timer` (8 s, tear-gas shutters and a speak trigger).
  It is NOT a van call. `TimerVanGo` is a leftover name of F07's spare delay. The escape vehicle is called by the escape setup, not by either.

## 2. kl2.exe (FACT unless marked)

- GatePath slot 26 `0x56a7e0` on AITrigger (the id at `[0x1689820]`) calls `0x7fd5a0` (not for a mode-3 client). `0x7fd5a0` reads the group pointer at `[this+0x34]`,
  checks and sets the byte `[group+0x30]`, then for each entry of f0 resolves the reference (0x8ccde0) and sends AITrigger through the target's virtual +0x120.
- GatePath init `0x449120` fetches the controller named "GateGroup" from an owner reached through `[node+0x50] -> +0x60` (0x598460) and stores it at `[this+0x34]`.
  That this owner is the node's PARENT group is read from the node names (`RunToEscapeGate\Way#01`), not from the 0x598460 code. GUESS (small).
- No reset found. Evidence is stronger than the first write-up: the GateGroup vtable 0xbc3cf4 is referenced only by its constructor (0x451f01), the string
  "GateGroup" is used by code only at 0x449139 (the GatePath init), and none of the 34 vtable slots writes `[this+0x30]`. Slot 21 (0x4edd70) writes the byte
  to a stream, slot 22 (0x5073a0) reads it back (save/restore). Slot 26 is `xor eax,eax` (no message). So the byte is never cleared inside a load.
- CORRECTION: the first write-up called `0x5b4873` "a multi-way message function I did not read, probably network sync". It is a two-instruction thunk
  (`add ecx,-0x30; call 0x7fd5a0`): a receiver embedded at GatePath+0x30 delivering to the same one-pass function. It is another way IN to the same check, not a reset.
- ZTriggerDelay2 (vtable 0xbc25fc): slot 26 `0x71e250` arms on AITrigger (id `[0x1688fa0]`) unless `[+0x34]` (disabled), `[+0x49]` (running) or `[+0x4a]` (done) is set
  or the clock `[[0xdd2640]+0x48]` is below `[+0x54]`; it sets `[+0x4c] = now - round((f0 + f1*rand) * -1024.0)` (constant at 0xb39f70 is -1024.0, so the clock
  is in 1/1024 s). Slot 25 `0x744c30` fires when `now > [+0x4c]` and sends AITrigger to every list entry through the OWNER's virtual +0x124. So the clock starts
  when the delay receives its message (when the floor box fires), not at level start. Whether f2 = -1.0 makes it one-shot via `[+0x4a]` (0x744d40): GUESS on the exact branch.
- Delivery differs: a GatePath resolves each reference and calls +0x120 on the target; a delay calls the owner's +0x124 with the reference. Both reach a behaviour
  rout's AITrigger handler; that they act identically for a `10_RunToCover` entry is a GUESS (but see precedent in section 5).
- `RunToCoverBehaviourRout` (vtable 0xbcf3cc): slot 26 `0x4ebed0` runs slot 34 `0x637400` on AITrigger unless `[+0x41]` is set or (`[+0x42]` and `[+0x40]` already ran);
  slot 34 -> `0x791090(rout, [rout+0x48])` -> squad goal / show code (re/retomoto_spawns.md 1). Reading, not run for these squads.
- That the four squads are HIDDEN at load (ZSquadScript f3 = 0 -> 0x787a10 -> 0x8d2e20) is the retomoto_spawns reading applied here: GUESS for these squads.
  Their `moved` evidence (section 3) shows Way#01 shows and sends two men, nothing more.

## 3. L100 (MEASURED, hook zi census, Every=2000 ms)

- Header line count 206, of which 195 non-empty lists (01:16:27.205 .. 01:22:55.201), 43 ZFFActor in each; "alive" went 43 -> 17 (01:20:27 on, constant to the end).
  The count of listed actors never changed, so a spawn or show could not raise it. 43 -> 17 is deaths of other actors.
- The ten plaza police (slots of builds 131c8c2b/43a7c699):

| slot | squad | start post (x, z) | result over 195 lists |
|---|---|---|---|
| 20240, 20242 | ExitStreet_Left (Way#01) | 25000,25600 / 25300,25700 | first moved in the sample at 01:18:51.2; health 0 at 01:20:03 / 01:20:21 |
| 20254, 20255 | ExitStreet_Right | 29000,25600 / 29300,25700 | 1 distinct position, health 157.5 / 135 to the end |
| 20269, 20270, 20272 | Exit_Right | 28300,25200 / 28500,25000 / 28700,25200 | 1 position, full health |
| 20285, 20287, 20289 | Exit_Left | 25900,25200 / 26100,25000 / 26300,25200 | 1 position, full health |

- Stair top is therefore between 01:18:49 and 01:18:51 (2 s cadence). Delay due at stair top + S: 01:19:34-36 for S = 45.
- Escape-vehicle state (`bots:` lines): state 1 at 01:20:06.9, 3 at 01:20:17.9, 5 at 01:21:10.9, 7 at 01:21:30.9, 0 at 01:21:32.9, then visit 2 (2/4/5) and
  state 8 at 01:22:36 (human aboard), session state 0x1f at 01:22:39, RESULT PASS 01:22:56. Lift-off about 160 s after the stair top. With a working gate S = 45
  would have started the 8 about 115 s before lift-off in this run. S is a per-run guess.
- NOT PROVEN: which of police2/police3 was running. The log shows only the zip size (259,430,078), identical for both. Irrelevant to the conclusion (the gate blocks both).
- NOT CHECKED: the first write-up's remark that L90's "0 ZFFActor" came from a census taken before actors existed; L90's log is not in the current file. In L100 the
  lists read 0 until 01:16:27, which fits it. Treat as GUESS for L90.

## 4. Cheapest proof for a run

No new code. In the census lines follow slots 20254 20255 20269 20270 20272 20285 20287 20289 (re-derive by position from the first list if the zip changes).
PASS = their coordinates change within a few seconds of stair top + S and health falls when shot; FAIL = identical to the first list to the end, as in L100.
The `bots:` lines give lift-off; police->crew hit lines near x 25000-29500, z 24600-25800 would also show them acting.
Optional new field (PROPOSAL only, klhook/klcensus.c belongs to another session): in `klcs_tick`, `nd = klh_rd32(o + 4)` and print `(klh_rd32(nd + 0x3c) >> 10) & 1`
as `hid` (the hidden bit of retomoto_spawns.md 1). That would turn the hidden-at-load GUESS into a measurement.

## 5. Fix options (none applied)

- A (smallest): in `wire()` line 1002 change `f4=[ways[1]]` to `f4=[e for e in arrive if e not in kept]` so the delay names the three `10_RunToCover` entries. The
  layer's own wiring check (lines ~1473-1510, `_w2` expected as the delay's only target) must change with it. Precedent now READ, not guessed: stock delays in this very level
  already name squad behaviour routs (`RivalMercs!Timer` node 19997 names 060_Capitolio...\DefendBehaviour entries; `merc_bot_squad` timers name Defend routs),
  and kl_fa_bank.py's plaza-late (lines 4535-4600) does exactly this form for the Vault (a timer naming the plaza squads' entries). Residual GUESS: RunToCover routs
  answer a delay's message like DefendBehaviour routs do (same slot-26 handler 0x4ebed0, different slot 34).
- B: give Way#02 its own parent group with its own GateGroup (new node, reparent).
- C: drop Way#02 and let Way#01 name all four squads (ce42dcc9 behaviour, i.e. no late police).
- Other builders: kl_fa_bank.py has no GatePath or GateGroup, so it does NOT have this trap. UNCHECKED: kl_fa_club.py, kl_fa_v2_park.py, kl_fa_v2_hotcoffee.py,
  the club campaign's second gate and M11_A's gate squads (campaign_fa_havana.md) each use GatePath; any that expects two paths of one group to both pass is affected.
  re/club_campaign.md B5 ("only the first of the gate's two paths passes, GateGroup not read in kl2.exe") is right about the behaviour; the code IS read, at 0x7fd5a0.

## Verify

1. `python tools/kl_fa.py` load of both zips: GatePath 19992/19993 lists, node 20000 = [120.0 | 45.0, 0, -1, 0, [Way#02]], floor box names Way#01 and TimerVanGo, nothing else names Way#02. Done, matches section 1.
2. `python debug/dasm.py 7fd5a0 90`: byte `[group+0x30]` tested then set to 1 before the send loop. Done.
3. Reset search: vtable 0xbc3cf4 has one reference (0x451f01); "GateGroup" string one code reference (0x449139). Done.
4. L100 slots 20254..20289 identical in all 195 lists; 20240/20242 moved from 01:18:51 and died. Done.
5. Not done: any live run of fix A; the hidden-bit census field; police2 vs police3 identity of L100; the other GatePath builders.

## police4: fix A built as an opt-in flag (2026-10-19, offline, not run in the game)

FACT = measured here. GUESS = not proven.

### Flag
`python tools/kl_fa_hasta_layer.py test <out> ... --rest-late=S --rest-late-direct` (also `kl_fa_hasta.py chain ... --rest-late=S --rest-late-direct`; the chain only passes the flag on).
- Only valid with `--rest-late` (exits otherwise). Default off. `van.json` flags gain `REST_LATE_DIRECT: true` only when set.
- Effect: node 20000 (TimerVanGo, TriggerDelay2) list = the three `10_RunToCover` entries (Exit_Left, Exit_Right, ExitStreet_Right) instead of `[Way#02]`.
- Way#02 is KEPT unchanged (still holds the same three entries, now named by nobody). Reason: removing or reparenting it changes the node count, the pools (kl_gms.category, CLAUDE.md "Pool category is exact") and every REF/slot id after it; keeping it changes one list inside one node.
- The layer's own check (`check()`, rest-delay branch) accepts both forms. Direct form: delay f0 > 0 and one-shot, delay list == Way#02's list, no entry also on Way#01, no dangling entry, nobody names Way#02, only the floor box names the delay, floor box names Way#01.
- Files touched: tools/kl_fa_hasta_layer.py (flag, wire, check, flags_of), tools/kl_fa_hasta.py (chain passthrough only).

### Default unchanged (FACT)
The chain's `post.py` / `reslot.py` steps (adopt_list line 146) do not exist anywhere in the repo or the work folders, so the full 43a7c699 delivery could not be rebuilt. What was proven instead: the layer step 1 of the police3 recipe
(`test --keep --blast --lock-wing --lock-show --corner-floor --heli-escape --heli-hvk-origin --rest-late=45`) built with the HEAD tools (git archive) and with the edited tools gives the SAME `F01_Main.zip`, md5 **5c4d108b62dd...**, both RESULT: PASS (20,282 entities, 372 MB). With `--rest-late-direct` the same step gives md5 286407ae1c3b..., PASS. police3 file 43a7c699 itself is untouched.

### Staged (C:\kl_build_1019\hasta_police4\)
Method: police3 zip with node 20000's list replaced (same mechanism as kl_fa_hasta_police.py; the list equals the one the new flag builds, checked by loading both), rewritten with deflate level 3. Scratch script is not in the repo.
| folder | S | F04_Main.zip md5 | bytes |
|---|---|---|---|
| DM11B | 45 | d49627cf9091... | 219,773,994 |
| DM11B_S90 | 90 | a9ee0ebe5277... | 219,773,995 |
- Side files (KLJoin.ini 437c96ee, KLGuns, KLTalk, KLWardrobe, .WHD, .hti, WAV, LS files) copied from police3, identical.
- Diff vs police3: all 30 members have the same names and content except `Scenes/Locations/F04/F04_Main.prp` (+10 bytes: two more 5-byte references in node 20000's list; bytes differ from offset 3,734,399 on because of the shift). Compressed size is smaller (219.8 MB vs 259.4 MB) because of the zip compression level only. S90 differs from S45 only in the 4-byte float of node 20000 f0.
- Checks (FACT): debug/check_passes.py PASS (A, B, C1-C3); debug/check.py 0 records with a layout Dog Days never stores; tools/klt_audit.py DM11B pools 12, miss 0, Fed/AllDead/Shoot yes; kl_fa_hasta_police.py check PASS (Way#01 = ExitStreet_Left, Way#02 = the other three, all squads active 0); layer check on the flagged bare build PASS (also with --corner-floor).

### Choose S (GUESS)
L100: stair top r~120 (floor box starts the delay then), escape call r~197, lift-off r~280. Recommend **S = 90** (delay due r~210): the 8 start about 13 s after the van is called, while the crew is on the plaza and boarding, and about 70 s before lift-off, so they have time to be seen and to fight. S=45 (r~165) would have them awake before the call, when the crew is still on the stair/alley. Staged both; S90 is the recommendation. A slower crew moves everything later: S is a per-run guess. Residual GUESS: a `10_RunToCover` entry answers a delay's message (owner's +0x124) like a GatePath's (+0x120); precedent: stock delays name behaviour routs here and in kl_fa_bank's plaza-late.

### Test recipe for the other session
Install police4 (S90 first) in slot F04 with KLJoin 437c96ee, hook zi, script PT_DM11B_p. In the census follow slots 20254 20255 20269 20270 20272 20285 20287 20289 (re-derive from the first list by start position: ExitStreet_Right 29000,25600 / 29300,25700; Exit_Right 28300,25200 / 28500,25000 / 28700,25200; Exit_Left 25900,25200 / 26100,25000 / 26300,25200).
- PASS: their x/z change, or health falls, within a few seconds of stair top + S (stair top = when 20240/20242 first move, ~r120; so about r210 for S90).
- FAIL: identical to the first list to the end, as in L100 (then the GUESS about the RunToCover answer is wrong; next try fix B).
- Also watch the heli: the point of police2/3 was the heli is shot down with ~10 police alive (L44-49). If it dies after lift-off with these awake, S is too early or the men are too many.

### Audit: GatePath / GateGroup in other builders (report only, no edits)
The trap is: two paths of ONE GateGroup given DIFFERENT lists, the second meant to fire after the first. kl2 0x7fd5a0 lets one path through once.
| builder | gate | Way#01 list | Way#02 list | senders | trap? |
|---|---|---|---|---|---|
| kl_fa_hasta_layer.py default | RunToEscapeGate | arrive (4 police squads) | same | floor box -> Way#01; backstop 300 s -> Way#02 | no, identical lists, Way#02 is a fallback |
| kl_fa_hasta_layer.py --rest-late | same | 1 squad | other 3 | box -> Way#01, delay -> Way#02 | YES (this finding); fixed by --rest-late-direct |
| kl_fa_hasta_police.py post-pass | same | kept | kept (same list written to both) | as default | no |
| kl_fa_club.py (1542-1609) | RunToEscapeGate | enemies_in | enemies_in | floors counter -> Way#01; seal timer and van timer b -> Way#02 | no by lists. Behaviour to know: whichever fires first wins; if the beat finishes before the alarm, the police come at the beat and the alarm's Way#02 is dropped (GUESS this is intended: comments say "once") |
| kl_fa_v2_park.py (611-629) | same | arrive | arrive | floor box -> Way#01; backstop -> Way#02 | no |
| kl_fa_v2_hotcoffee.py (612-651) | same | arrive | arrive | speak box -> Way#01; backstop -> Way#02 | no |
| kl_map_ai.py | stock Dead Men gates (e.g. M02 PoliceSwats Gate Way#01) | n/a, read only | | treated as "let an order through once" | no |
| kl_fa_bank.py | none | | | | no GatePath |
| M11_A gate squads (campaign_fa_havana.md: 11 on the big square, 1 GateGroup on the market square) | campaign-stock | | | no builder exists yet | not applicable; when one is written, never split lists across paths of one group |
| club campaign second gate (`SecondRun!Rt\Way#01`) | campaign-stock, not authored | | | | not applicable; re/club_campaign.md B5 is right, the code is read at 0x7fd5a0 |
No other instance of the trap found. club's comment at kl_fa_club.py line 550 ("GateGroup was not read in kl2.exe") is out of date.

## Verify (police4) (2026-10-19, independent check, offline, nothing run in the game)

FACT = measured here. GUESS = not proven.

- Flag is opt-in (FACT). The diff of tools/kl_fa_hasta_layer.py and tools/kl_fa_hasta.py only changes behaviour under `REST_LATE_DIRECT` (wire line ~1004, check, flags_of; chain passes `--rest-late-direct` only when `rest_late` is set). I rebuilt layer step 1 of the police3 recipe (`--blast --lock-wing --lock-show --corner-floor --heli-escape --heli-hvk-origin --rest-late=45`) with the HEAD tools (git archive + re/*.json) and with the edited tools: both give F04-slot zip md5 5c4d108b62dd, both PASS. With `--rest-late-direct`: 286407ae1c3b, PASS. The full 43a7c699 delivery cannot be rebuilt (no post.py / reslot.py in the repo, C:\kl_build_1018 or C:\kl_scratch: searched), so "default unchanged" is proven at the layer step only. police3's own zip is untouched (md5 still 43a7c69972e8).
- police4 vs police3 (FACT, both zips decoded, 30 members): same names; only `Scenes/Locations/F04/F04_Main.prp` differs (3,931,392 -> 3,931,402 bytes). Loaded with kl_fa: node 20000 (TimerVanGo, TriggerDelay2) f0 45.0 (S90: 90.0), f1 0, f2 -1, f3 0; f4 = [Exit_Left\10_RunToCover (19977), Exit_Right\10_RunToCover (19960), ExitStreet_Right\10_RunToCover (19946)], police3 had [Way#02]. Way#01 (19993) = [ExitStreet_Left], Way#02 (19992) = the other three, group 19991: all unchanged. KLJoin.ini 437c96ee identical in both folders. S45 and S90 differ only in the f0 float. The size drop (259.4 -> 219.8 MB) is deflate level 3 only.
- Does the new wiring reach the squads? Partly proven.
  - FACT: the three targets are RunToCoverBehaviourRout nodes (the same nodes Way#02 reached). Nothing else in the level names them now. In kl2 a delay fires through the owner's +0x124 (this file, section 2), a GatePath through the target's +0x120; both end in the rout's AITrigger handler 0x4ebed0.
  - FACT (new): a TriggerDelay2 naming RunToCoverBehaviourRout nodes directly is stock Dog Days wiring. Stock F01: `Gameplay!Timer_SwatMoreForward` names `SwatExit#02\12_RunToCover` (1 of 50 delay refs); stock L03: `...TvGuys_Reinforce\RunToCover_OnAlert\Timer_RTC_Delay` (3 of 106). Both are cross-subtree names like this one. Stock F07 has none, so the precedent is other levels, not F07.
  - GUESS: that the rout, when started this way, shows and sends the squads exactly as it did via Way#01 for ExitStreet_Left (L100 saw that squad move). The census for slots 20254 20255 20269 20270 20272 20285 20287 20289 settles it.
- Checks on both police4 folders (FACT): debug/check_passes.py PASS (B, C1-C3, A); debug/check.py 0 records with a layout Dog Days never stores (identical output to police3); tools/klt_audit.py (needs a Maps\ layout; run on hardlinks) pools 12, miss 0, Fed/AllDead/Shoot yes; kl_fa_hasta_police.py check PASS.
- Gate-trap audit (spot-checked FACT): kl_fa_club.py line 1542 and kl_fa_v2_park.py line 614 / kl_fa_v2_hotcoffee.py line 615 write ONE list (`enemies_in` / `arrive`) to every Way, so the one-pass gate loses nothing; only the layer's --rest-late split the lists (lines 995-999). kl_maps.py only mentions GatePath in an owner note. The audit table above stands.
- Disk: C: 5.7 GB free, G: 6.3 GB free after cleanup. My scratch builds were removed.
- Remaining risk, unchanged: S is a guess (90 recommended above); the live test decides. If the census shows no movement, next try is fix B (a second GateGroup for Way#02).
