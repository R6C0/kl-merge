# DM01 / DM03 host-only car cover ring (2026-11-01)

Status: PROBE staged offline, NOT run live, NOT committed. The cause is not proven; read "What is and is not known".

## Problem
Online, the CLIENT hits int3 asserts at kl2.exe 0x6567e8 0x845a8b 0x51d049 0x555900 0x4ede1b on DM01 and DM03. A soldier's cover POINT index is replicated by value from the host
(ObjDup -> 0x581b40 -> 0x656740 -> [soldier+0xe8]) and the client's CFFCoverList is shorter. Fallback already merged: [KLHook] AssertSoft (steps over the int3s).

## Evidence (coverdump logs build\klhook\solo\Q30_DM03, Q33_DM01; clustered by position, kl_coverdump_parse + a position grid)
- DM01: host-only points 347..354 = 2 clusters of 4 at (15399,-15,27165) and (16370,-15,27165), i.e. one ring of 8 around the ram truck (node 243, ZHavokCar, V_USA_RamTruck_A_Dynamic_00).
- DM03: 32 host-only points = 4 rings of 8 around nodes 6946, 7019 (police reinforcement cars), 7106 (V_USA_Sedan_A_Dynamic_00) and 7186 (Deliverycar_01). Node 6874 (EscSquad car, off the nav mesh) has none.
  NOTE: ce's list had 6874 and lacked 7186; the clusters say 6946 / 7019 / 7106 / 7186.
- Ring point format (exe report): pos + flags 0x368 written, +0x34 left as fill pattern, not the 0x71fc30 / 0x5dbed0 load-time path. Writer NOT found statically.
- Not ringed although on the main nav part: DM01 Bentley_01/02 (112, 168; NORMAL_CAR, [9]=0, CoverBox children), DM01 Cement_Truck (286; TRUCK, [9]=1, 1 CoverBox child, started by Civil\VehicleMoveBehaviour like the ram truck).
- Off nav, not ringed: DM03 6874, DM02 7280.
- Ringed cars have no single stored field in common that the unringed ones lack: the cement truck matches the ram truck in type, [9], model class, nav and driving. The CoverBox-child hypothesis fails (DM03 ringed cars have 3 boxes). The "driven car" hypothesis fails (cement truck). The `[9]=1` hypothesis fails (cement truck). So the trigger is UNKNOWN.

Review addendum (adversarial pass, same day): the HavokCarScriptRout controller's first bool is 0 ONLY on the DM01 ram truck (1 on Bentleys, cement truck and every DM03 car), so it is a third stored difference in DM01, but DM03's ringed cars have 1, so it cannot be the one common trigger either. All 10 cars sit in a BOUNDING_DynamicAutoAssign group. install.py now also moves `<name>.bots.base.md5` with the plain zip (backup `.before-1101carcover`, restored by --undo); without it kl_botgate_stage check / kl_entries_check report DRIFT. The prp edit is 2 bytes (DM01) / 4 bytes (DM03 --dm03), zip metadata identical.

## What is and is not known
Known: host-only, 8 points per ringed car, DM01 = 1 car, DM03 = 4 cars, only maps with such ZHavokCars diverge; the other 19 live maps are identical.
Unknown (GUESS everywhere below): the writer, its trigger, whether it is authority-gated.

## Chosen fix
A role-preserving DATA fix for DM03 does not exist on the evidence: the four ringed cars are the SWAT / police arrivals and the delivery car, and making them static changes the round. So:
1. Keep AssertSoft (shipped protection, unchanged).
2. DM01 data PROBE (tools/kl_dmcarcover_1101.py): on the ram truck's ZHavokCar give the two stored values the unringed Bentleys have: [1] TRUCK -> NORMAL_CAR, [9] 1 -> 0. .prp only; every other member and node byte-identical.
   Role: truck keeps model, position, spline drive, horn relays, effects. GUESS: NORMAL_CAR vs TRUCK may change handling/mass in the Havok sim; [9] is an unnamed flag. Nothing else changes.
3. DM03: unchanged by default. Opt-in `--dm03` probe: [9] 1 -> 0 only (type kept) on 6946, 7019, 7106, 7186. GUESS, role risk: if [9] is a simulate/drive flag the arrivals could stop. Do not ship without watching the cars arrive.
4. If the probe leaves the lists different, the real fix is the hook below (a data fix is then shown not to work with these two fields).

## Hook design (no code) - the definitive path
1. Name the writer: DR0 write-watch on `[L+0x44] + 347*0x7c + 0x68` (L = [[0xdd265c]+0x15a0]); log the return chain. Also watch DM03 point 564.
   WARNING (c9 review): a DR0 watch in an ONLINE session got the host killed by the anti-tamper (ExitProcess from 0x8000dead 67-85 ms
   after arming, SP2, commit 2279376ec), which is why OnlineStackProbe=3 became a poll. So: first check whether the ring also appears in
   an Arcade (offline, local host) DM01 round with a coverdump; if yes, arm the watch there (no session). Online, only a per-tick poll of
   [pt+0x68] is safe: it times the write (and which game state is active), but cannot name the writer.
2. Preferred: make the client run the same writer for the same cars at the same moment. The ring centre is the car's bounding-box centre at its start pose, which the client can compute from the .prp, so indices come out equal (8 per car, in node order).
3. Alternative (cheap): receiver clamp at 0x656740 / 0x581b40: if idx >= local [L+0x68] store -1 (no cover) instead of the index. Check re/antitamper.md first: those ranges may be hashed (the 0x4e3f40 detour was refused in session runs). Use a veh() step-over like AssertSoft if so.
4. Do not block the writer on the host: it would change host AI cover use.

## Outputs (work folder `G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\carcover_1101\`)
| file | input md5 | output md5 |
|---|---|---|
| DM01\F01_Main.zip | fe9d5751dc0204fa8eb79541fb434e8a | e838c6fcf20444f1bd989700fde769d1 |
| DM01\F01_Main.bots.zip | 2fb07d3b60d59190d33c5268cf91a15d | 3278496adfaee742bb47d6ed423feb20 |
| DM03_probe\F03_Main.zip (--dm03) | c0fb50f7e2ab3d8066966f0ae898769c | dff72561bfe85865742006128e8a8d50 |
| DM03_probe\F03_Main.bots.zip (--dm03) | 30d7f1797e38c115e9870eaf8755933c | 19ab5cb695518878d31994c2ae4e5d7f |
Rebuild: `python tools\kl_dmcarcover_1101.py stage --dm03` (reads the game folder, writes only the work folder; deterministic).
Offline checks: only the .prp member differs; only the planned nodes' props differ (node list and paths identical); idempotent; debug\check.py output on DM01 identical for input and output except the path line; `python tools\kl_tests.py` RESULT: PASS - 45 pass, 0 fail, 5 skip.

## Install (NOT run by the agent)
`C:\kl_build_1024\c9_1028\carcover\install.py`: `python install.py --check` (read-only), `python install.py` (DM01), `--dm03` adds DM03, `--undo [--dm03]` restores byte for byte.
Pins the live md5 (install) and staged/backup md5 (undo), backups `<zip>.before-1101carcover`, refuses while kl2.exe runs, never touches KL_PortBackup.

## Bench (owner not playing; DM01 first, then DM03 with --dm03)
2 seats, DM01 and DM03, host on the .bots zip as usual, [KLHook] AssertSoft EMPTY on inst2 (the probe must stand without it).
Expect: `kl_coverdump_parse.py --compare <host log> <client log>` prints IDENTICAL on DM01; inst2 asserts=0, no 'soft assert'.
Also watch: truck still drives on the spline and honks (DM01); with --dm03 the SWAT/police cars still arrive with squads, the delivery car still comes.
If DM01 still diverges: revert (--undo), do the hook step 1.

## Writer search (11-01 evening)
Static only (kl2.exe read with debug\dasm.py + capstone, call/vtable xref scan of .text/.rdata; no game run, nothing written, not committed).

### CONFIRMED (read in the disassembly)
- **WRITER = 0x81b6f0**, thiscall on the car SCRIPT object (ecx=edi; [edi+0x40] = ZHavokCar; the car points back to it at [car+0x968]).
  - `cmp byte [edi+0x1e8],0 / jne ret` is the done flag (set to 1 at 0x81bacb, so once per script). `cmp byte [edi+0x1e9],0 / jne skip` is "slots reserved".
  - 0x81b726..0x81b75f: 8x `mov ecx,[0xdd265c]; call 0x713130; mov ecx,eax; call 0x558350`. 0x558350 is `eax=[L+0x68]; [L+0x68]=eax+1; ret`, i.e. the REAL count bump, returning the index. Indices go to [edi+0x1c8+n*4], count to [edi+0x1c4]. Sets [edi+0x1e9]=1. This is the 347..354 growth. 0x558350 has only two callers: 0x795f22 (ZCreateActorCover, 1 point) and 0x81b73d (this ring).
  - 0x81b769 `call 0x72fdd0` on the car, then reads the car box [car+0x8f8/0x900/0x904/0x90c], margin doubles 0xb71b60 / 0xb3dde8, builds 8 vertices (chamfered rectangle) and transforms them with the car matrix (0x42a4d0 / 0x7b3020 / 0x6be1c0).
  - per point (loop of 8, 0x81b983..0x81bac5): physics probe `[0xdd2640]+0xac -> +0x8c -> vtable+0x264(...)`; `test al,al / je 0x81baba` SKIPS the point when it fails; else `call 0x713130; call 0x9015d0` (0x81baae / 0x81bab5).
  - NEW NOTE: the 8 slots are reserved BEFORE the probe. A car whose probe fails still grows [L+0x68] by 8 and leaves those points as unfilled spares (pos 0, flags 0x400), which a position-cluster cannot see. So the coverdump clustering cannot tell "ring not built" from "ring built, probe failed". GUESS, unproven: compare the host's real count with 347 + 8 x (cars whose writer ran).
- **0x9015d0** (point setter): nav query via `[[0xdd2640]+0xac+0xc]` vtable+0x7c; if ok, `imul idx,0x7c; add [L+0x44]; call 0x8a7d90`, then a vtable+0x1c call on the 0x2c-stride entry [L+0x58]+idx*0x2c. Callers: only 0x795fa9 (ZCreateActorCover) and 0x81bab5.
- **0x8a7d90** (point init): `and [pt+0x68],0x78` (clears the 0x400 spare bit), `or 2`, `or 0x200`, pos written at +0x28 and +0x30, more `or 0x10/8/0x20/0x1000`. No write to +0x34 seen. Ring points = pos + flags, +0x34 untouched: matches the evidence. The exact 0x368 value was not reconciled (no 0x100 bit seen in this function; it may come from the passed flags). Not needed for the plan.
- **Why the client asserts** (0x656740): `imul idx,0x7c; add [L+0x44]; mov eax,[pt+0x68]; test al,2; jne ok; test eax,0x200; jne ok; int3 (0x6567e8)`. A client spare has flags 0x400 only, no bit 2 and no 0x200, so int3. Ring points (flags above) pass. Matches the observation.
- **Callers of 0x81b6f0** (xref scan, all 6 calls + 1 jmp):

| site | function | what it is (via RTTI) |
|---|---|---|
| 0x8d631e | 0x8d6210 | ZHavokCar state setter (arg1 = state -> [car+0xa28], arg2 byte = active). Tail 0x8d6311 `mov ecx,[esi+0x968]; mov byte [esi+0x8c0],0; call 0x81b6f0` runs for BOTH active and inactive. Callers: 0x6df8d5 in 0x6df8c0 = ZAIInputRoadComponent slot 13 (vt 0xbcb9f8); 0x8f9d5f in 0x8f9c60 (callers 0x4bafc5 in 0x4bae30, 0x6deace in 0x6de6a0). Also a vtable pointer at 0xcd037c (class/slot not resolved). |
| 0x564758 | 0x564700 | ZHavokCarIdleGoal@CPPScript slot 2 (vt 0xbd16dc). NOT the "script Run thread" as first labelled. Waits while [car+0x8c0]!=0, then waits via 0x630b50/0x55b9f0, then `call 0x81b6f0` per pass until done. |
| 0x7cb06a | 0x7cb060 | slot 3 of ZVehicleMove / Fire / FireOnRoad / SpecialMoveBehaviour (vt 0xbcd740 0xbcd9c8 0xbcdaa0 0xbcdb78). Gate: [this+0x20] != 0, then `jmp 0x7fc330`. |
| 0x5c524f | 0x5c51b0 | ZVehicleExitBehaviour slot 2. |
| 0x62249f | 0x622470 | ZHavokCarScript slot 12 (stream reader): reads a bool, calls 0x6dbd70 (destroy), then `if bool: 0x81b6f0`. |
| 0x75ec44 | 0x75eb80 | plain function; callers 0x4d786c (in 0x4d7710), 0x550343 (in 0x550210); owner class not identified. |
| jmp 0x5c2d60 | 0x5c2d50 | thunk gated on byte [[this+0x1c]+0x2c] and [this+0x20]; callers 0x44f1ce, 0x7145e6, 0x8dc1e6. |

- No explicit host / authority test exists inside 0x81b6f0, 0x558350, 0x9015d0, 0x8a7d90 or the thunks above (all read). 0x9425a0 (called at the start of 0x581b40) only tests [this+0x14] plus a lookup: not an is-master check.
- 0x6567e8, 0x81b6f0, 0x558350, 0x9015d0 and 0x8d6311 all lie in CEG-hashed ranges (ceg_ranges.py: 8 to 11 checks each). No code byte of them may be patched.

### REFUTED
- Load-time path 0x6d6a80 -> 0x603830 -> 0x71fc30 -> 0x5dbed0 / 0x56d610: never calls 0x558350, so not the writer.
- ZCreateActorCover 0x795ee0: same helper chain but ONE point, caller-owned: not the ring.
- ZDynamicCover routes (slot 14 0x5a7220, slot 26 0x71cbd0): edit cover records / dirty queue only (search result, not re-read here).
- "0x9425a0 = is-master": refuted.

### OPEN (host-only gate NOT found)
- GUESS: the ring is built lazily the first time something runs on the car's script/state: the AI road component (ZAIInputRoadComponent -> 0x8d6210), a vehicle behaviour start (0x7cb060), the idle goal or the exit behaviour. AI input components and behaviours run on the AI-simulating station only (netcode.md l.214, assumed host). The client gets the car through ObjDup but its script/AI may never start, so it never reaches 0x81b6f0 and never bumps [L+0x68]. Unproven: the client may create the script (0x81eac0 -> 0x4e40c0 -> [car+0x968]) and just not run it.
- Why the DM01 cement truck / Bentleys have no ring on the host: unknown. Candidates, all unverified: (a) lazy, its script had not reached the first call at dump time; (b) probe at vtable+0x264 failed so the points stayed spares (see NEW NOTE); (c) the gate byte in 0x5c2d50; (d) the HavokCarScriptRout bool (0 only on the ram truck, which argues against a plain bool -> ring link).
- Whether the client runs 0x81b6f0 at all, for any car: not measured.

### Hook plan (nothing built)
Constraints: no .text patch (hashed); no DR0 watch online (anti-tamper killed the host 67-85 ms after arming, re/antitamper.md); IAT / data writes and a VEH step-over like AssertSoft are fine.
1. Recommended, cheap, safe: the AssertSoft step-over at 0x6567e8. c9 check: klhook.c already resumes at Eip+1 = 0x6567e9 (`xor al,al`, "not valid cover"), so this site is handled that way ONCE the site matches (ce 11-01 ~21:50: AS1 showed it never matched, offsets vs VAs in the ini; fixed to VAs, AS2 regrades). Still open: and if possible store -1 into [esi+4] (the replicated index) so later readers never use a pos-0 point. The other four assert sites (0x845a8b 0x51d049 0x555900 0x4ede1b) have their own consumers and need their own check. Host unaffected.
2. Faithful but fragile: the client runs the same writer: `ecx=[car+0x968]; call 0x81b6f0` for every Dynamic ZHavokCar in node order, from the game thread (not a poll thread: it touches physics and the list), after the cover list is built and before any replicated index arrives, so 0x558350 returns 347.. like the host. Needs the same probe result and car start pose on both. Only worth it if (1) shows the soldier then misbehaves on the client.
3. To settle the gate without a watch: poll per tick [L+0x68] and each Dynamic car's [script+0x1e8]/[script+0x1e9] ([script]=[car+0x968]) on host and client (reads only, safe online). Or offline in an Arcade DM01 round log entry of 0x81b6f0 (execute breakpoint, return chain) to see which of 0x8d6210 / 0x7cb060 / 0x564700 builds the ram truck's ring and why not the cement truck's. If the client's [script+0x1e9] stays 0 while the host's is 1, plan 2 is justified.
4. The staged data probe (TRUCK -> NORMAL_CAR, [9]=0) is unsupported by this search: nothing read on the path to 0x81b6f0 depends on the car type or [9]. Expect the lists to stay different.

### c9 addendum (11-01 ~21:20)
- Timing: in Q33_DM01 both seats' coverdumps ran at 17:38:11, right after the load, and the host's points 347..354 ALREADY had positions there. So the ring is written at load / round start on the host, not lazily in play. That makes the SetActive / stream-reader / road-component start callers likelier than the idle goal.
- The coverdump does not log [L+0x68] (its window starts at +0x70). Next: a TEST-only [CoverRing] probe (poll [L+0x68] + each car script's +0x1c4/+0x1e8/+0x1e9 on both seats; offline-only execute breakpoint on 0x81b6f0 with the return chain). The CC1 data-probe bench is DROPPED: item 4 above says it cannot work.
