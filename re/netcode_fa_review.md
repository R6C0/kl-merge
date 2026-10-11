# Review of track Q (re/netcode_fa.md, klhook/klnet.c, the [Net] sample in klhook/KLHook.ini)

Adversarial review, 2026-10-11. Offline: kl2.exe build 0490 re-read with `debug/dasm.py` / `debug/kl.py` (scratch
scripts: session scratchpad `qrev/a.py`, `qrev/b.py`), the three files read line by line, both compiles re-run.
NOTHING WAS RUN IN THE GAME by the worker or by this review. The worker's files were not changed.

## Verdict: ACCEPT WITH FIXES

Wiring klnet.c with `[Net] Log=1` (reads only) can go ahead as it stands. `[Net] Tune=1` must not be set on any
machine before MUST 1 is settled. The research note holds up at every address this review re-read; its plan is
sound, with the wording points below.

## What was re-read and holds (EXE, this review)

- **The twelve numbers.** 0x4825b0 read whole: tolerance objects 0x168f1e4 / f244 / f440 / f4b0 / f510 / f570 get
  30, 30, 20, 30, 40, 5 (floats 0xb7ee44, 0xb64cc8, 0xb52a74, 0xbcb330) through 0x990f00; the MIN globals 0xd34668,
  0xd34688, 0xd35424, 0xd3545c get B = `[sm+0x158]`, 0xd3547c gets 2 B, 0xd3549c gets 1.5 B (double 0xb82578 = 1.5).
  The MAX globals are 2000 and the MIN globals 150 in the file. The one caller of 0x4825b0 is 0x7ee35d in 0x7ee0c0.
  B = 100: `c7 86 58 01 00 00 64 00 00 00` at 0x8c4b5b.
- **The tolerance object.** 0x990f00(tol) = 0x990e40(tol, 0, 0, -1.0): `[+0]` = tol squared, `[+4] [+8] [+0xc] [+0x10]`
  = 0, `[+0x18]` = 0 (degree), `[+0x1c]` = -1.0; the constructor 0x990e10 zeroes +0..+0x14. So klnet's 'as expected'
  test (first float > 0, the next four 0, degree 0) is what the game leaves, and writing tol * tol at +0 is the
  right form. (0xb3e980 is -1.0, not 1.0 - of no consequence for klnet.)
- **Each (tolerance, MAX, MIN) triple of klnet_ds[] is used together in one sender routine**: 0x906ae6 / 0x906b55 /
  0x906af5; 0x7f8043 / 0x7f80b2 / 0x7f8052; 0x403b86 / 0x403bf5 / 0x403b95; 0x875243 / 0x8752b2 / 0x875252;
  0x660b53 / 0x660bc2 / 0x660b62; 0x66e8c6 / 0x66e935 / 0x66e8d5. In 0x403b93..0x403c10: elapsed < MIN -> no
  tolerance test; MIN <= 0 switches the test off; elapsed > MAX forces. klnet keeps MIN >= 16 and MAX > MIN.
- **All twelve addresses are in .data (0xcd7000..0x1692e5c) and in no hashed range** (klranges.h: no range between
  0xcd7000 and 0x1694000).
- **Session fields.** 0x7f6850: jump table {0x7f6865, 0x7f6865, 0x7f686e, 0x7f686e} on `[sm+0x54]` = roles 0 / 1
  answer 'game type == 4', roles 2 / 3 answer no. 0x4b0a40 `cmp [ecx+0x54],3`. 0x5be510 writes `[sm+0x5c]`;
  0x6c9ec0 `push 4`. 0x8e6a20 = `[sm+0x70]`. 0x4e7da0 copies 0x40 bytes to sm+8. 0x6c9ca0 `mov [esi+0xbf], bl`.
  0x5c9dd0 = `[sm+0x17c]`. RTTI of all nine vtables klnet names is as klnet says.
- **The index travels, not the name.** Host 0x6c5342..0x6c53d6 and client 0x491f77..0x491fe3: `MPMap` on the own
  command line ? D.mapname : game type 4 ? `[0x168f750]` vtbl+0x3c (slot 15) of 0x467ae0(D). Getters: 0x467ae0 =
  D+0x1ac -> 0x5b1400 `movsx byte [ecx+4] ^ 0xac`; 0x83f980 = D+0x10c -> 0x532840 `^ 0xdc`; 0x8dc7f0 = D+0x18c;
  0x4468a0 / 0x57b2d0 = D+0x230 / D+0x250 -> 0x962850 `mov eax,[ecx+4]`. klnet reads exactly these bytes.
- **Private / ranked.** 0x518b50 = word +8 bit 4 (and dword +0 bit 4); 0x810df0 = bit 5; 0x6c9da5..0x6c9dfe as the
  note says (private when the option is 1, ranked when the option is 0, both -> private cleared). CreateSession
  0x8e4fe0: 8 dwords to S+0x370, `[S+0x36f]` = bit 5, `[S+0x35c]` = 1, the pointer S+0x35e handed on; lobby type
  0x8e514b: ranked -> 3, else (private byte == 0) + 1 = 2 public / 1 friends only.
- **The game's own 'everybody has this map' gate** 0x6c4d11..0x6c4dd9: as the note says, and it also answers one
  of the note's open questions: the countdown runs only while the player count 0x698250 is >= `[sm+0xb9]` (min
  players), byte `[sm+0x1f4]` is set and the game type is 4.
- **0x53919c**: `call 0x57b2d0`, eax overwritten by the next instruction - no compare. Holds.
- **Hook parts.** klgun.c line 365 tests only `[sm+0x5c] == 4` (confirmed: it would write in an online FA round);
  kljoin.c has no session test at all; klbot / klfed / klbalance refuse roles 2 / 3 and need vtable 0xbd3514; klcrew,
  klcrew_rt, klchar need 0xbd3514; klhop / klescort / klhud / klclimb / klgrudge go through `klb_read`.
- **Files touched**: `git status` / `git diff klhook/KLHook.ini` = one appended hunk of 25 lines; klnet.c and
  netcode_fa.md are new; klhook.c untouched. Nothing of this track is committed. (Other modified files in the tree
  belong to other tracks.)
- **Compile, re-run by the review**: fresh `git archive HEAD klhook` into `G:\kl_scratch\Q\rev\src`, klnet.c copied
  in (byte-identical to the worker's compiled copy), the same three lines. Last lines:
  `built G:\kl_scratch\Q\rev\test\dinput8.dll (TEST)` (sha1 4f8ed99d...), `built G:\kl_scratch\Q\rev\ship\dinput8.dll
  (SHIP)` (sha1 6159d98d...). No warning from klnet.c (the only warning is klhud.c(188), old). The sha1s differ from
  the worker's because the path / build stamp is in the DLL; the worker's two files have the sha1s he reported.
- **klnet.c as code**: no game call, no Steam call, no .text write (only `klh_data`, which refuses hashed ranges and
  non-writable pages); every key defaults to off; `Tune=1` without a number writes nothing; the put-back only
  restores a number that still holds what the hook wrote; a Net-Z restart under the tune is handled.

## MUST

1. **The tune acts on a CLIENT in any lobby that is not ranked - public ones included.** klnet.c line 269: the
   'private' test is `role == 2 && !priv` only. The task's rule is 'PRIVATE lobbies only, nothing may touch public
   matchmaking'. A client cannot prove 'private' from memory: JoinSession (0x6d8640, found by this review) writes
   the lobby id (`[S+0x35e]` from the search result +0x6d / +0x71) and the ranked byte (`[S+0x36f]` from its second
   argument, 0x6d874c) but NOT the property block S+0x370 - on a client that block is what the last CreateSession
   on this machine left, or zeros. With the plan's own stage-0 setting (`[Expansion] Page=2` forced) a quick match
   into a public lobby on slots F01-F04 / F06 gives verdict 2 and the tune writes. Fix before `Tune=1` is used
   anywhere: on role 3 the tune stays off unless the owner says so by a key of its own (e.g. `TuneClient=1`, 'I
   joined a friends-only lobby by invitation'), or until the lobby datum of 2.4 exists; and the init line / the ini
   text must say that the client side rests on the player's word. (Log=1 is not affected.)

## SHOULD

2. **On a client the lobby line prints a kind it cannot know.** klnet.c lines 310-313 derive 'PRIVATE (friends only,
   type 1)' / 'PUBLIC' from `props[8]`, which a join never writes (see 1). In check N2 the friend's log can say
   PRIVATE or PUBLIC at random (whatever he last hosted). For role 3 print the lobby id and the ranked byte only and
   say 'kind not known on a client'. The same stale bit 5 (`rank`) can make the client's tune refuse with 'the
   session is RANKED' after he once hosted a ranked game: use `[S+0x36f]` alone on a client.
3. **Upgrade two ASSUMED items the exe settles**: `[S+0x35e]` IS the lobby id on a client (0x6d8739 / 0x6d8746);
   'a client's property bits mean anything' is REFUTED (they are stale). Correct section 8, the klnet.c header and
   the line-312 text.
4. **The log's change signatures are never reset when the session becomes local** (line 280 returns before them):
   a second identical lobby in one process (same role, handler, rules, index, map) prints no 'net: session:' line,
   so a repeated N1 looks like a FAIL. Reset `sig0`, `dsig0`, `lobsig0`, `numsig0`, `scene0`, `state0` when `!net`.
5. **The 'not stock' verdict can be the PREVIOUS level's for the first moments of state 0x12** (klh_scene still
   names the old scene while the next archive is opened): after a round on a Dead Men map the tune can write for
   the start of a stock map's load and put the numbers back when the scene name changes. Harmless in size, but it
   is a write in a stock-level session: require the scene's own slot to match the session's level index, or start
   at the first state after the load.
6. **The state window 0x12..0x1f is Arcade knowledge** (0x12 load, 0x19 round, 0x1f score); whether an online
   session between two rounds leaves it was not read. If it does, the tune puts back and rewrites every round and
   logs 'the session is over' each time (wrong text, right effect); if online rounds use states above 0x1f the tune
   silently never acts. Mark it ASSUMED in the file and let N3 list the 'net: state' lines to check it.
7. **Wording in the note / header**: (a) '0x7ee0c0 = slot 1 of both handlers' - slot 1 is 0x66a820 (server) /
   0x5f6690 (client); 0x5f66a3 CALLS 0x7ee0c0 with ecx = sm (the server's call was not followed by this review).
   (b) The init line and the ini say 'never in a ranked session' flatly: true for a host; for a client it rests on
   JoinSession's second argument, whose caller nobody read. (c) 0x990f00's fourth argument is -1.0.
8. **Stage 0 (`Page=2` forced on both machines) has no guard at all, and the note says so - make the check say it
   too.** Add to N2 as steps, not prose: join ONLY by invitation / friends list, never Quick Match or the server
   browser while the line is in the ini; both remove `Page=2` before leaving the evening; if the friend's log has
   no redirect line his machine is on stock Airport and, hook or not, his klsteam verdict is 'stock' - HIS stats
   and rank are written for a desynced round. Stop before the countdown, not after.
9. **N1 can answer more than it asks**: with the gate read above, add 'net: session: ... players <min>..<max>' to
   the PASS list and note the min - it decides whether one person can start a lobby alone (stage S's open question).
10. **Not re-read by this review, and resting on the worker alone**: the receiver side (0x600eb0, 0x5f21c0, the
    reading of 0x992f10 as 'no cap' - its first 0x190 bytes do show a two-sample linear form), 0x6300f0, the online
    fed chain (0x46bd40 / 0x6bb910 / 0x6ee860), system link 0x77e220, the 62 / 66 shared vtable slots, the int16
    position claim (0x5a0ff0), the SteamMatchMaking008 slot numbers of 2.4. None of them carries code in klnet.c;
    all are marked EXE or ASSUMED by the worker. They carry the PLAN (stages 1-4), so stage 1's code needs its own
    review of those addresses.

## For the lead

- Wire as given (`#include "klnet.c"` below klvis.c, `klnet_init();` below `klvis_init();`,
  `klnet_tick(game_thread);` below `klvis_tick();`) - compiles TEST and SHIP. With `[Net] Log=0 Tune=0` it does
  nothing and says nothing (one exception: a number key outside its range is said even then).
- klgun.c line 365 wants `[sm+0x54]` not 2 / 3 (confirmed; the lead's file).
- Until MUST 1 is fixed: `Tune` stays 0 in every ini; checks N0, N1, N2 may run; N3(b) may not.
