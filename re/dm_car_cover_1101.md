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
