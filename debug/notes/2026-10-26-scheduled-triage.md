# 2026-10-26 scheduled check-in (cloud, 13:58-14:40 UTC): PC busy, no new crash; [CopSquad] static review, 3 fixes

The DD and DM folders were not connected to this scheduled session; one access request was granted (read-only use, as
in the earlier runs). The PC was BUSY: KLHook.log / KLHook.result / dinput8.dll / KLHook.ini written 13:53 UTC (5 min
before this run), KLHook.result `state=PASS reason=script reached pass scene=F03_Main.gms loads=2 asserts=0 faults=0
frames=54110` (the BOS_DD05 bench of the 13:52 log note), the log tail a clean F03 round (`RESULT PASS` 13:53:13).
Nothing launched, installed, staged into the game or touched on screen.

## Dumps

`KLHook_1.dmp` 08:11 UTC and `KLHook_2/3.dmp` 03:20 UTC: both older than the last log note (13:52) and both already
written up there - 08:50 "COVER13b crashed in d3d9.dll+0x5feeb at a C tap (driver fault)" and 03:45 "camera pool
crash explained" (assert 0x60a5bf / crash 0x586eb4). Newest game .mdmp is 10-25 19:18 (older than the notes). No
dump to triage.

## Offline piece: static review of klhook/klcopsquad.c (cd8476d, "NOT RUN LIVE")

kl2.exe staged read-only from the PC (sha1 9d99e01d...) and read with debug/kl.py + capstone (a small wrapper that
puts the staged exe in DD_GUESSES). Every call the module makes and every GUESS of re/cop_squads.md re-read; the table
in `re/cop_squads.md` section 8 has the addresses. The findings that changed code:

1. **Follow(all) walks the player SQUAD (`[sc+0xa4]`, members `+0xc0` count / `+0xc4[12]`), not the receiver list**
   `sc+0x1c`, and takes a member only when 0x6c8510 passes (`[s+0x4f4] == [sc+0xa4]`, `[s+0x6a4] != 0`, `[body+0x576]
   == 1`, body vt+0x680() false). The module's `listed` check read the receiver list only; a soldier that Recruit listed
   but 0x7b3490 did not add to the squad (count 12, or `[body+0x77c]` null) would have counted as recruited and never
   moved. Now `[s+0x4f4] == [sc+0xa4]` is read back (`insquad` in the log) and both must hold; `[sc+0xa4]` must be
   non-null (0x7b3490 reads it unchecked) and the member count < 12 before each Recruit; `[s+0x6a4]` (commandable,
   1 from the ZSoldier constructor 0x761900) joins `klcq_soldier`.
2. **One pass per round**: a cop whose first pass (10 s in) saw no free police soldier got no squad all round. Retried
   every 500 ms until something is recruited, at most 40 passes (~20 s).
3. The recruit log line printed `cand[0].d2` as every soldier's distance.

Upgraded from GUESS to VERIFIED: the aim handle `[[P+0xbd4]+0x2ac]` (0x86a9c0 stores 0x8fcb50(3) there, which ends in
0x6ece90(nearest actor in the aim cone) = a handle or 0; stale handles resolve to 0 through the generation word in
0x40a880) and the aim point `P+0x27b0` (0x4677c0 while aiming, setter 0x724a10). Corrected: 0x7b3020 in Recruit is a
node-local-to-world transform of a stack vector, not a "node place"; DD's own Recruit calls in the soldier init 0x615c90
are gated on game TYPE 2 (co-op) and role <= 1, and on every other type a soldier with `[s+0x6e8]` not 0 / 1 (team
value 0 -> 13) is Recruited into PLAYER 0's squad control at load, so a host that is player 0 and a cop starts with
receivers (the `nr0` figure). Still GUESS, now instrumented: the used byte +9 as the human mark (both type-3 pickers set
it; the table reset 0x56f360 clears it together with the entry's first word, an owner object - logged per type-3 entry
at Log=2).

Checks: `tools/run_harness_linux.sh --check-hook` (MinGW installed here) 0 errors, no warning in klcopsquad.c for SHIP
and TEST; `klcs_test.c` builds (logic.h unchanged; not run - no Wine in this container). Not compiled with MSVC, not run.

Owner / local sessions: nothing new to install. When the C&R bench of re/cop_squads.md section 7 runs, read the
`recruit ... listed %d insquad %d (members %lu)` lines and, with Log=2, the `table entry %d: policeman player ... used %d
owner word %08lx` lines (which of the two marks the human cops carry).

---

# 2026-10-26 scheduled check-in, second run (cloud, 14:48-15:10 UTC): PC busy (game running), no new crash; UCC P2 built

Folders connected on request (read-only use). The PC was BUSY: `KLHook.result` `state=RUNNING pid=41656 scene=F04_Main
loads=2 asserts=0 faults=0 frames=15989` (a bench round in progress, dinput8.dll / KLHook.ini written 14:47 UTC, the log
tail a clean HUD / stall-probe stream at 14:49). Nothing launched, installed, staged into the game or touched on screen.

## Dumps

Newest hook dump `KLHook_1.dmp` 08:11 UTC and game dump `kl2_490_crash_2026_10_25T19_18_39` are older than the last log
note and already written up. Nothing to triage.

## Offline piece: Undercover Cop P2 (police AI vs the hidden UCC)

kl2.exe (sha1 9d99e01d...) staged read-only and read with debug/kl.py + capstone (a byte-pattern scan for displacement
reads plus function listings). Finding and build: `re/ucc_police_aim.md`, `klhook/klucc_aim.c`, `klucc_aim_logic.h`,
`klua_test.c` (27/27 with gcc and MinGW), `tools/run_harness_linux.sh --check-hook` 0 errors (MinGW installed here). Not
compiled with MSVC, not run.

Owner / local sessions: nothing to install. Decide re/ucc_police_aim.md section 5 (keep the stock cop-killer exposure as
"caught in the act", or swallow it while hidden); the bench of section 6 needs two System Link instances.

# 2026-10-26 scheduled check-in (cloud, 22:48-23:20 UTC): PC idle, no new crash; online HUD gaps closed (not run live)

Folders were connected on request again (read-only use). PC IDLE: newest game-folder writes KLHook.ini 19:54 UTC
(the [CharOnline] turn-on), dinput8.dll 19:28 (hook 1026f), KLHook.log 19:04 (the owner's Steam private FA session,
ended by Alt+F4 at 19:04:57, asserts 0 faults 0), `<work>\build\hire_1026` 20:07, last commit 20:26. KLHook.result is
still the 16:14 F04 bench PASS. Nothing launched, installed or touched on screen.

## Dumps

KLHook_1/2/3.dmp (08:11 / 03:20 UTC) and the newest .mdmp (10-25 19:18) are all older than the 21:40 log note and were
triaged in the 08:50 / 03:45 notes. Nothing to triage.

## The owner's 18:58-19:04 online session (log read)

Two loads in one process (DM09 in F06, then DM02 in F02, OnlineSet=2). On the SECOND load the heap's largest free piece
was 28.4 MB and klmem answered 5 refused requests from the 128 MB reserve: 32.0 + 16.0 + 16.9 + 21.2 + 23.1 = 109 MB
(KLHook_map_refused_0/1.txt written 19:01/19:02). The reserve frees each block with the level, so a 10-round mixed-map
match (live ini: RoundsMax=10, OnlineSet=9) rests on that per-level free; `[Memory] RoomMB=128 ReserveMB=176` (klmem.c
'THE NEXT STEP') is still NOT RUN IN THE GAME. Worth a look after the owner's first long online match: how many
'memory: HeapAlloc ... FAILED' lines per load, and whether any says the reserve had no gap.
Also seen: 'scoreboard: the wrap failed 30 tick(s) ... the stock panel stays' at the online round end (expected: the
online outro is log-only until [HUD] OnlineBoard is on), and the KLWardrobe 'not usable (entry 17...)' lines (the
voice-offset else-branch, misleading, see the 20:45 note).

## Offline piece: the online port's two open HUD items (klhook, --check-hook SHIP/TEST 0 errors, warnings unchanged)

'stock kill popup still swallowed online' and 'stock van panel still blanked': klhud.c now publishes `klu_keep` once per
compose (KLU_KEEP_KILL = klu_kill_line ran with [HUD] Money; KLU_KEEP_VAN = klu_van_card ran with Money), one
InterlockedExchange after klu_compose_in, cleared in klu_reset. klhud_kill.c keeps the points pop-up off the screen
only with the KILL bit; klhud_escape.c runs the EscapeCard=1 restyle (time / icon / bar hidden for the card) only with
the VAN bit, else the stock panel is left whole. Effect: online with the default OnlineFeed=0 / OnlineVan=0, or without
OnlineCrew, and in Arcade with Money=0, the stock pop-up and the stock van panel draw as the game's own; with the port's
keys on, nothing changes. Not MSVC-built, not run live.
