# 2026-11-10 scheduled check-in: DM01B doorfix load crash, independent cloud triage = the local fix ec59d91, rebuilt stage pre-flighted

Offline, cloud. PC busy (commits 06:48-06:55, bench kits written 06:49): nothing launched, installed or written into the game.
No dump readable (DD / DM folders are not connected to the scheduled task); the triage is of the kit zips, staged from C:\kl_build_1024.

## Crash
bench dm01blive1110 06:38:11: `FATAL unhandled exception c0000005 at <no module>+0xbf7fc0c0`, caller 0x6ad1d9, loads 1, level_loaded 0,
3/3 at every DM01B load of dm01bdoorfix_1109 (F03_Main.zip 5eab5ecc). Junk EIP = a call through a garbage pointer inside the
.prm/.oct loader 0x6ad0f9..0x6ad1d9: the function of the 2026-10-17 vault door2 crash (0x6ad1c3) = debug/check_passes.py crash site A.

## Finding (reached in parallel with the local session; ec59d91 landed the same fix at 06:55 while this ran)
`python debug/check_passes.py` (1 s per zip):
- 778b075c (pre-doorfix, live again): `PASS A oct-offsets  4154 type-7 roots, 514 without an octree, 3656 .oct records`
- 5eab5ecc (doorfix 1109):          `FAIL A oct-offsets  4156 roots ...; 3640 roots point INTO the .oct, not at a record (first: chunk 198 value 0x2fa35, record 0x2fa30)`
The doorfix .oct's room-tree part is 16 bytes shorter (164768 -> 164752: two group item boxes out, two leaf boxes in, net one item), so
all 3656 original records moved -16 (first record 0x283a0 -> 0x28390; every new ref == old ref - 16), while the 3640 live type-7 roots
kept the 778b075c values byte for byte. Only the 2 appended roots (chunks 49724, 49746, the restored door models) pointed at records.
Cause in tools/kl_dm01b_undoor_1109.py model_leg: `held = mat_octj.record_refs()` on the already EDITED Oct -> old == new -> 0 moved.
Every other tree-editing tool zips the UNEDITED octx with octn (kl_dm01b_gas_1025, kl_bots_kick_1025, kl_club_*, kl_cover_*).

## Proof that the fix is right, on the real files
- Re-pointing the 5eab5ecc .prm through dict(zip(778b075c .oct refs, 5eab5ecc .oct refs)) moves 3640 roots -> 0 stale, round-trips,
  and a copy of 5eab5ecc with only that .prm swapped passes check A (4156 roots, 3658 records, 0 bad).
- The local rebuild C:\kl_build_1024\dm01bdoorfix_1110 (F03_Main.zip 476aec5f, bots a056edbd, 06:53) differs from 5eab5ecc in ONE
  member, F03_Main.prm, and that .prm is BYTE-IDENTICAL to the cloud's independently re-pointed one (84,103,376 bytes).
- check_passes.py on 476aec5f and on a056edbd: PASS A (4156 / 514 / 3658), C1 23303+1, C2, B, C3 all PASS (the usual Shards_Group_A WARN).
The rebuilt stage is load-safe by the loader's rule; what is left is the bench (dm01bdoorfix1110 kit) and the owner's look at the doors.

## Lesson for every chain
`python debug\check_passes.py <stage dir>` before any bench: 1 s per map, it would have failed this kit on 11-09 without a game run.
