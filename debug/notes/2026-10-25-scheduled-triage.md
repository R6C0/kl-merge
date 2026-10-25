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

# 2026-10-25 scheduled check-in, second run (cloud, 06:48-07:10 UTC): PC busy, no new crash, kl_slotcheck.py added

The folders were not connected to this scheduled session (connectedFolders empty); one access request was granted, so
the PC side stayed read-only as before. The VS Code sessions were working: dinput8.dll and KLHook.ini installed at
06:07 UTC, KLHook.result `state=PASS scene=F07_Main.gms loads=2 frames=65077 asserts=0 faults=0` (the DD10B run,
`script 50: DD10 DONE` at 06:07:27). Nothing launched, installed, or touched on screen.

## Dumps

`KLHook_1..4.dmp` (05:52:13-15 UTC, 40-41 MB each) belong to the run that ended `RESULT FAIL (unhandled exception
c0000005 at KL2.exe+0x1d20d2) ... asserts 4, faults 2, loads 1` at 05:52:15 - the DD10A first live load already
triaged in the log note "DD10 FIRST LIVE LOAD CRASHED" (asserts 0x7f5892 GetFileSize(F07_Main.sup) = -1, 0x4a2fe9,
0x820423, 0x5d20cb, then kl2+0x1d20d2 reading 0; cause: the install tree renamed only the file F01_Main.zip ->
F07_Main.zip, the members still said F01). The fix (kl_l05_build_1025.py rewrites the members) is in and the 06:07
DD10B run of the rebuilt F07_Main.zip (05:59) PASSED, so the dumps were not re-read. No game .mdmp is newer than
10-24 19:02 (the LAA test, already read). Other results since the last note: 05:30 `c0000005 at ReShade32.dll+0x11ac5b`
with loads=0 frames=0 (ReShade died before the menu; one run), 05:50 and 05:57 script-route FAILs (menu state), not crashes.

## Offline piece: tools/kl_slotcheck.py

Read-only verifier for what the DD10A crash was: every `Maps\<id>\Fxx_Main.zip` must hold `Scenes/Locations/Fxx/Fxx_Main*`
members for ITS slot and the 17 members the loader opens by name, the files beside it (`.WHD .WAV .hti _LS.SND
_LS_Default.*`) must carry the slot name, and every `KLHook.ini` `[Redirect*] Fxx=<id>` must point at a folder that serves
exactly that slot. 15-check self-test (includes kl_graft.member_name agreeing). Run on the live tree (29 map folders,
20 redirects): **0 FAIL**. `.hrd` was first listed as required and flagged DM05A, DM06B, DM09*, DM11B - all of them
play live, so `.hrd` is optional by evidence and the tool says so. Notes it leaves: `.hrd` absent in those 11 archives,
build .txt files in map folders, and nine folders no redirect names right now (DD10, DM09RB*, DM09RD, DM09RV*, T01).
Suggested use: `python tools/kl_slotcheck.py <stage dir>` before any INSTALL bat, and `python tools/kl_slotcheck.py`
on the live game after one.
