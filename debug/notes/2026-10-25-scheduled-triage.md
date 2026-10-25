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

# 2026-10-25 scheduled check-in, third run (cloud, 10:47-11:10 UTC): PC idle, nothing new; klhigh.c reviewed, 4 fixes

The folders were again not connected to the scheduled session; one access request was granted (read-only use). The PC
was IDLE: the newest files in the game folder are KLHook.ini / dinput8.dll / KLHook.log / KLHook.result from 06:07 UTC
(4 h 40 min before), KLHook.result still the DD10B `state=PASS scene=F07_Main.gms loads=2 frames=65077 asserts=0
faults=0`, and the newest build folder in KL_PortTools\build is 10-24 17:29. No dump is newer than `KLHook_1..4.dmp`
(05:52, the DD10A member-name crash, triaged above and fixed). Nothing launched, installed, or touched on screen.

## Offline piece: adversarial review of klhook/klhigh.c (the high half), written by the 03:20 check-in and never reviewed

Read against the documented VirtualAlloc / VirtualFree contract. Four real defects, all fixed in place
(`klhigh.c`, header note "Review 2026-10-25"); the carving bit maps were correct (20-check `klhigh_bits_test.c`, gcc, PASS):

1. **`VirtualAlloc(0, n, MEM_COMMIT, prot)` was passed through uncounted.** MEM_COMMIT alone with a null address is the
   documented reserve+commit shortcut and allocators use it constantly. The wrapper only treated `MEM_RESERVE` as a new
   block, so in High=1 the measure line would have MISSED every such block (the number the whole idea hinges on) and in
   High=2 those blocks would have stayed in the low half. Now `addr == 0 && (type & (MEM_RESERVE|MEM_COMMIT))` is a new block.
2. **`VirtualFree(p, 0, MEM_DECOMMIT)` inside the high half** went to the real call. Size 0 means "the whole block" and
   Windows then requires the region's own base - which is OUR CHUNK. For a block not at a chunk's start the call fails
   (ERROR_INVALID_ADDRESS, the module sees a failed decommit); for the block AT a chunk's start it decommits the whole
   64 MB chunk - every neighbouring carved block's pages with it, i.e. the driver's live data gone. Now answered for the
   carved block (its size from the bit maps: new `klvh_block_pages`), refused for a non-start address as Windows would.
3. **A listed module reloaded at its old base was never re-wrapped** (`klvh_seen` saw "same base" and left the fresh
   IAT alone; the 10 s rescan had the same blind spot). The Ldr notification's UNLOADED reason now forgets the module.
4. **A chunk-limit shortfall was silent.** 48 chunks with 9 size classes can run out when the high half has images in
   it (the census will say); a free piece left above 2 GB is where the game's heap or a stack lands once the low half
   is full - the LAA tag crash, delayed. KLVH_CHUNKS 48 -> 96 and `klvh_high_left()` walks the high half after the
   takeover and logs a WARNING line naming any free piece (0 expected).

Also tightened: an explicit address inside a carved block with MEM_RESET / other flags now reaches the real call (only a
pure re-reserve is answered locally). Not changed, still documented risks: VirtualQuery by a module on its own carved block
sees the chunk, and a release through another module's slot leaks high. `klhigh_test.c` (Windows, LAA, not run) gained the
checks for 1, 2 and 4 (commit-only block goes high; size-0 decommit of the block at the chunk's start leaves its
neighbour committed; nothing free above 2 GB). klhigh.c syntax-checked with gcc against a stub windows.h (no MinGW in
this sandbox), warnings only from the stub's LONG. MSVC build and the measure run remain the Owner's.

# 2026-10-25 scheduled check-in, fourth run (cloud, 14:48-15:05 UTC): PC busy, no PC access this run; Entries= check folded into kl_slotcheck

## State
- origin/rtp-schemas had a commit 5 minutes before the fetch (866fd42, 14:43 UTC: the stale-Entries fix on 6 maps) and the log's newest
  note says the owner is at the PC ("install all", "owner playing"): the VS Code sessions are live. Nothing launched, installed or staged.
- The DD and DM folders were NOT connected to this scheduled session (device_list_dir returned a names-only skeleton), so KLHook.result,
  the log tail and any new dump could not be read. No folder-access prompt was raised (the owner is busy; a prompt would only interrupt).
  Earlier scheduled runs today had them: if the next one lacks them too, the task's folder list needs re-attaching in the desktop app.

## Dumps
- Not checked this run (no PC access). The last triaged set is KLHook_1-4.dmp 05:52 (DD10A), fixed in f3e0cb8e6.

## Offline piece: tools/kl_slotcheck.py now checks Entries= (the 14:55 find, as a pre-install rule)
The 14:55 note set a RULE: any .prm rebuild must re-run kl_entries_check before install. kl_entries_check reads the LIVE Maps folder only
and parses the whole .prm graph; kl_slotcheck is the tool the notes already say to run on a stage tree before an INSTALL bat. So the same
test now lives there: for every Maps\<id>\<slot>_Main.zip, the .prm member's dword +4 (the chunk count the hook compares with [0xeac7a4];
read with z.open().read(8), no inflate of the 50 MB member) against KLGuns.ini [Guns] Entries and KLJoin.ini [FedBody] Entries beside it -
exactly the two keys klgun.c / klfedkit.c read. Mismatch = FAIL (the hook silently leaves the file alone: gun looks / fed outfits off);
KLGuns.ini without Entries = FAIL (klgun.c refuses the file); KLJoin.ini without [FedBody] = note; no ini = nothing. Self-test 15 -> 21
checks (stale guns, exact FedBody, missing key, missing section, a clean tree with an exact ini stays clean, a .prm rebuild under an
unchanged ini is one FAIL). pyflakes clean. Not run against the live tree (no PC access): `python tools/kl_slotcheck.py` on the PC should
now print `ok ... Entries=N = the .prm chunk count` for the 6 maps fixed at 14:55 and 0 FAIL.
