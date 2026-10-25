# 2026-10-25 scheduled check-in (cloud, 02:48-03:30 UTC): no new dump; the PC was busy; klhigh.c written

Nothing was launched or installed and the screen was not taken. The PC was in a live run when the check-in started:
KLHook.log was being written (02:48 UTC), dinput8.dll and KLHook.ini were installed at 02:41 UTC, KLHook.result said
`state=RUNNING reason=loaded scene=F01_Main.gms loads=2` — the e8 session's DM05A run (the F01 slot redirected to
KLExpansion/Maps/DM05A, log 02:42:29). So this run stayed read-only.

## Dumps

- `KLHook_1.dmp` (01:59 UTC) and `KLHook_2.dmp` (01:33 UTC) are **0 bytes**: no dump was written (the hook pre-opens the
  file, or MiniDumpWriteDump failed — the log around those times holds only perf lines, no CRASH / FAULT line). Nothing
  to read.
- The newest game dump is `kl2_490_crash_2026_10_24T19_2_42C0.mdmp` (the LAA test), already read in
  `2026-10-24-scheduled-triage-laa.md`. No dump is newer than the last log note.

## What the live log said at 02:48 (DM05A, round 1, ~6 min in)

`memory: every 10 s: free address space 16 MB, largest piece 0.1 MB; the reserve holds 13 block(s), 61.6 of 128 MB;
refused small requests so far 277; modules 264 MB, mapped 64, private committed 1363, private reserved only 340; thread
stacks: 1 of 4 MB or more (4 MB, deepest 1296 KB), 145 smaller (131 MB, deepest 204 KB), 0 game thread(s) given 4 MB`
— the address-space wall again, with OtherStackKB on (145 stacks in 131 MB; the line's own words: "0 game thread(s)
given 4 MB" — read the k48h census line for what that counts). 41-46 fps, 24-33 frames over 33 ms per 10 s. The round was still alive (bots: 1 you in-play, 6 dead,
1 traitor dead; $140000).

## Offline piece taken

The wall is address space, and the 4 GB flag was ruled out because the GAME's heap blocks above 2 GB collide with the
engine's bit-31 pointer tag. `klhook/klhigh.c` (+ `klhigh_test.c`, `klhigh_bits_test.c`, `re/high_half_1025.md`) keeps
the game below 2 GB by reserving the whole upper half at DllMain and gives that half only to the listed foreign modules
(driver, ReShade, overlay) through their own import slots of VirtualAlloc / VirtualFree. `[Memory] High=1` measures
first (no flag needed). Off by default; not run live; compiled with MinGW only.
