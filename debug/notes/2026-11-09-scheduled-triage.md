# Scheduled check-in 2026-11-09 ~11:15 UTC (cloud; DD/DM attached by one access request)

## PC state (read only; nothing launched, installed or staged into the game folder)
- IDLE since 09:23 UTC (86 min at the start of this run): `<DD>\dinput8.dll` + `KLHook.ini` 09:23 (merged_1109land),
  `C:\kl_build_1024\merged_1109land\pins.json` 09:23, repo head a97e612 09:26 (kl_bench_1109 DM07PLANE kits). No bench dir written since.
  Still nothing launched from here: the DM07PLANE stage needs 426 MB on C: (131 MB free) and an owner-OK install.
- `KLHook.result` does not exist in the game folder (benches write their own `inst1\KLHook.result`; the last is dd10land1109 PASS 09:23).
- `KLHook.log` (35 MB) ends 11-08 17:52 with the owner's Alt+F4 on DD10 (round second 290, 241 fps, 8 frames over 33 ms in the last 10 s).
- Dumps: `kl2_490_crash_2026_11_8T14_22_44C0.mdmp` (11-08 14:22:44) is the only one newer than the last triage. ALREADY EXPLAINED AND FIXED:
  KLHook.log 14:22:42-44 = ASSERT 0x538f02 (eax -1, esi 0x1d) -> ASSERT 0x8707dd -> CRASH c0000005 at 0x538f47 reading 0, the moment the
  owner became police on DM11B (Hasta) with page II guns bought in shop rows 0 / 28: the police respawn 0x410710 found no free pool
  object. Fix = `[ShopPage] FedKeep` (klshoppage.c, in merged_1108e and later, so in the live merged_1109land; "NOT run live" per the ini).
  Nothing new to triage. KLHook_1..4.dmp of that crash are not in the game folder root (moved by a local session).

## Offline piece: the MOPP byte code is read now (`tools/kl_mopp.py`, `tools/kl_mopp_test.py` 115 checks with the real files)
Why: `tools/kl_dm07plane_1109.py` (the [06] DM07 gate fix waiting for disk + bench) rests on the GUESS "the list code only returns slot
256 / 248 for a query touching that slot's OLD volume", and `re/havok.md` on the ASSUMPTION "list terminal = child index in the 510-block
(the code was not interpreted)". Both decide whether the plane clones can close the mud hole (y 388..460) under the hidden panels (y 471..801).

Done: a reader of the Havok 4.x hkMoppCode byte code (opcode layout from the public niftools / PyNifly tables; the comparison rules
FITTED to the live `DM07\F06_Main.HVK` (zip f35e4133) and `DD10\F07_Main.HVK` (zip 1a0d94b0), .HVK members pulled on the PC into
`C:\kl_build_1024\sched_1109_hvk\` - no game file touched):
- SPLIT `a b j`: left when floor(c) <= a, right when floor(c) >= b; CUT `lo hi` inclusive; immediates big-endian (the DD10 HERO plane's
  24-bit x cut 0x00ba2e = exactly its 2 cm of margins); SCALE n: c' = (c - xyz) * 2^n for the 8-bit compares, but a 24-bit CUT reads the
  ROOT coordinate (DM07 block-0 child 108, a zero-thickness plane at x 1147, proved it); diagonal axes compare
  floor((sum of signed bytes + 256 per minus term) / terms) (4260 of 4272 centres with it, 3029 of 6060 with the plain sum).
- Result on the real files: 100 % byte coverage, no unknown opcode on all 2777 + 5837 placement codes and 18 list codes; 99.7 % of
  triangle centres reach their own terminal with `Code.query`; every full 510-block's list code has exactly the terminals 0..509, DM07's
  padded block 1 exactly 0..166 for its 167 real children (the 343 fillers after them are never returned), and every real child's world
  box lies inside the box of positions that reaches its terminal -> **"list terminal = child index" is PROVEN**, the padding rule holds.
- Side finding: the graft's systems blocks (DM07 children 1020..2776, DD10 4080..5836) are ALL filler (one placement of REF 20269
  repeated; 2104 of DM07's 2777 statics are filler) and their list codes DO return them (510 terminals each): harmless, the filler's
  own code only answers near its real quad at (-800, 670, 8445) cm. Nothing to fix.
- **DM07 answer**: slot 256 (4m_01) is reached for x -4622..-4526, y 464..817, z 9989..10395; slot 248 (4m_11) for the same x / y,
  z 10384..10843 (= the old boxes + the 2.7 cm quantisation; the two windows overlap, no seam). So the plane clones block any query box
  that touches y 464..817 over the whole gap z 9989..10843: a player's capsule (feet on the mud at 460) is always tested; only a body
  entirely below y 464 (4 cm over the mud top) or above 817 is never tested. The planned crawl / mud-edge bench steps are not needed
  for players; what remains to bench is the sub flags (0x108 vs 0x72) and the van. Written into the tool's docstring (MEASURED) and
  `re/havok.md` ("MOPP byte code read"; "Not established" item struck).
Run it: `python tools/kl_mopp.py <F06_Main.HVK> 248 256`; test: `KL_MOPP_HVK=<folder of .HVK> python tools/kl_mopp_test.py` (without
files the 33 synthetic checks run; kl_tests runs it).

## Test runner (`tools/kl_tests.py`): head a97e612 in the cloud was 46 pass / 2 FAIL / 78 skip -> now 48 / 0 / 79
- `kl_fallback_guns_test.py` FAILED on Linux only: `out_problem` split the path on `os.sep` so `D:\x\KL_PortBackup\X` was not refused
  (on Windows normcase makes it `\`). Now split on both separators + lower(): the KL_PortBackup refusal holds on every host (175 checks pass).
- `kl_gunpunch_test.py` FAILED as root (cloud sandboxes): its rollback checks make a bank read-only with chmod, root writes through it.
  New `PY_NOT_ROOT` table -> SKIP with the reason when euid == 0; unchanged elsewhere.
- `klshopset_test.c` was UNLISTED: tagged 'win' (it reads a KLShopPage.ini with GetPrivateProfileInt/StringA, not in the shim).

## Owner
- Nothing to install or decide from this run. Still yours: free C: for the DM07PLANE stage (426 MB needed, 131 MB free):
  `C:\kl_build_1024\dm07unhide_1109` (385 MB) + `dm07curtain_1109` (325 MB) are stale single-link stages; also `pd2rebase_1107_backup`
  (8.2 GB, a backup) if no longer wanted, and the D: scratch dirs named in the 08:50 / 09:00 notes. `C:\kl_build_1024\sched_1109_hvk`
  (3.3 MB, this run's .HVK copies) can go too.
