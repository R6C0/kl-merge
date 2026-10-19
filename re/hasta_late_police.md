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
