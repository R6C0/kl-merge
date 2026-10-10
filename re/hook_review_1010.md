# Adversarial review of klhook\klbot.c and klhook\klgun.c (2026-10-10, agent h-review)

Offline only. Nothing was installed, the game was not started. What was done: both files read whole, with
klhook.c (guard, tick), klsteam.c (level-open, ship policy), klmem.c (reserve), klchar.c (the session tests);
every address below disassembled again from kl2.exe build 0490 with debug\kl.py / dasm.py; both builds compiled.

## Compile check

    klhook\build.bat      <scratch>\ship   -> exit 0, no warning at /W3   sha1 816ce2a5053254b0042c79b5d90bd82d1792f9bc
    klhook\build_auto.bat <scratch>\test   -> exit 0, no warning at /W3   sha1 086f8cf07b965c91c404a239352594342c799256

(The sha1 changes with every build: __DATE__ / __TIME__ are compiled in.)

## Verdicts

| feature | switched off | first live check | condition |
| --- | --- | --- | --- |
| klbot, no [Bots] Enable | SAFE to install | - | inert: `klb_tick` returns on `!klb.on`, `klb_init` reads one key, no log line |
| klbot Log (Enable=1 only) | - | SAFE | reads only (ReadProcessMemory), at most 10 passes a second, at most one line a second |
| klbot Tune | - | SAFE on a grafted map or with the TEST build | B1 before it is used on a STOCK level with the SHIP build |
| klbot Backstab | - | SAFE on a grafted map / TEST build | B1 |
| klbot Bribe | - | SAFE on a grafted map / TEST build | B1; B4 is a behaviour note |
| klbot Leave | - | SAFE on a grafted map / TEST build | B1 |
| klbot Van=1 | - | SAFE after B2 (two lines) | B1, B2 |
| klbot Van=2 | - | MUST BE FIXED FIRST: B2, B3 | then TEST build only, after K1 has shown what record +4 is |
| klgun, no [Guns] Enable=1 | SAFE to install | - | inert: every entry point returns on `!klg_on`; one 'guns: off' line a start |
| klgun Enable=1 | - | SAFE | G1 (stale KLGuns.ini) should be closed before it is left on for the owner |

No finding is an integrity-check risk: neither file writes an image byte. Every write goes through `klh_may_write`
and lands in the heap (rules object, crew records, score object, tuning object, .prm block); the only image
addresses touched are READ (0x168e598, 0x168e9e4, 0x168d7c0, 0xdd265c, 0xeac7a0/a4/b0 - all .data - and 16 code
bytes at 0x6a1100, vtable 0xbd3514 + 4 * 94). klranges.h has no range in .data. The one game call (0x6a1100) is a
call, not a patch.

## What was checked against kl2.exe (all confirmed unless said)

klbot.c
- 0x7f6850: session = [0x168e598], `[+0x54]` above 3 or jump table 0x7f6874 = {0x7f6865, 0x7f6865, 0x7f686e,
  0x7f686e} -> 0 / 1 test `[+0x5c] == 4`, 2 / 3 false. As `klb_read` does it.
- vtable 0xbd3514 is ZGameRulesHeist (RTTI); slots 11 = 0x704610, 16 = 0x485740, 33 = 0x4d8a30, 94 = 0x6a1100,
  129 = 0x8fb0d0, 149 = 0x757510, 151 = 0x8b8b40, 182 = 0x4a4020, 194 = 0x8fa6d0, 195 = 0x55ec70.
- 0x6a1100: `sub esp,8 / push esi / mov esi,ecx / mov eax,[esi+0x5f8] / mov cl,[esp+0x10]` = the 16 bytes in
  `code[]`; one stack argument, every exit is `ret 4` - the `__fastcall (this, 0, int)` call matches. Grade 0
  returns; grade 1: announcement 0x764f60 and, in state 3 / 4, `[+0x1d8] = 0.0`; grade 2: jump table 0x6a12b0 =
  state 0 and 6 return 0, states 1..5 -> slot 194 (6), then per record with status 4: 0x544550, then slot 16 for a
  record with flag 1 (actor = [rec+4], attacker = 0x6ece90([rules+0x1e8])) or slot 11 for a player.
  CORRECTION to the top comment: `[score+0x60] = grade` is written for EVERY grade (0x6a1114), not '= 1'.
- 0x757510 (pay the driver): slot 151 (0), `[+0x1b3] = index`, slot 182, money -= money >> 1, slot 129 (index, -1),
  `[+0x1d8] = 0.0`, 0x65c620. As the comment says, step for step.
- 0x8fb0d0 (slot 129) does call 0x660b00 / 0x70f770 on the LOCAL player whatever index it is given (0x8fb1b9):
  the author's reason for not calling the rule for a bot holds.
- 0x4322f0: `[+0x33c] = (1 << index) & [+0x33c]`, and the `inc [+0x338]` sits behind `or edi,ecx / jne`: as the
  comment says (the game's own oddity, mirrored exactly). 0x488ecd `or byte [eax+0x79], 2` then `call 0x4322f0`.
- 0x78f470: a bot's record is found by `test byte [rec+0x79], 1` and `cmp [rec+4], actor`; record size 0x7c;
  +0x348 / +0x34c / +0x354 as used.
- Tuning: 0x43ffdd `cmp ecx, [L*0x70 + [0x168d7c0] + 0x718]` (= 0x6ac + 0x6c, an int), 0x46d505 `fld [.. + 0x6cc]`
  (= 0x6ac + 0x20), 0x6a1c64 `lea esi, [.. + 0x6ac]` / `fld [esi+0x18]`. Level clamp 1..11 as in `klb_read`.
- `[rules+0x1b3]`: readers in this class are slot 129 only (0x8fb0e7). The second `cmp byte [esi+0x1b3], 0xff`
  (0x72775f, function 0x727610) belongs to another rules class (its records are 0x74 bytes, it is in no slot of
  0xbd3514). Writers 0x424070 / 0x7de590 / 0x785fa0 write +0x1b2 and +0x1b3 together (state copy; not read further).
- `[rules+0x1e8]`: slot 33 = `mov [ecx+0x1e8], eax / ret 4` - a RAW pointer, no reference count.

klgun.c
- 0x67cf68 `mov ebp,[eax*4+0xeac7b0]`, 0x67cf77 `test dword [ebp+0x1c], 0x800000`, 0x67cf84 `mov al,[ebx+0x158]`,
  0x67cf8e `cmp [ebp+0xf], al`, 0x67cca3 `cmp word [eax+2], 7`: as quoted. The loop takes one object at a time
  (0x67cf45 .. 0x67d253 `cmp esi,[eax+0x14]`): no count-then-fill pair in THIS function that a flip between two
  passes could overrun. The other three sites (0x57ee43, 0x7581e1, 0x7af091) were not read for that.
- 0x8007f0: `[0xeac7a0] = file + [file]`, `memset(0xeac7b0, 0, 0x48000)`, `[0xeac7a4] = [0xeac7a8] = [file+4]`.
  ADDITION: there are THREE loaders that set and clear 0xeac7a0, not two: 0x8007f0, 0x496d80 and 0x45f260
  (0x45f2ab sets, 0x45f52a clears). The guard `loading != 0 -> return` covers all three. One more reader, 0x69ad38.

## Findings

### B1 (klbot; stats / leaderboard) - the gameplay parts act on a STOCK level while Steam writes are open
`klb_read` (klbot.c:231-233) asks only for 'Arcade session + ZGameRulesHeist'. It does not ask what level runs.
The SHIP policy of klsteam.c (`klx_ship_blocked`, klsteam.c:291) PASSES stats, achievements and the leaderboard
upload when the level's archive is the stock one. So with a SHIP build and Tune / Backstab / Bribe / Leave / Van
on, a round on stock Subway (which has its own AI crew) is played under changed rules - bots that turn where
stock forbids it, a vehicle that leaves early, money halved, everybody aboard killed - and its result (a lost
life, the session's last life = the upload) goes to the real board and into the owner's real stats.
On a grafted map the guard blocks everything, and a TEST build blocks always: the first live checks are not
affected. It matters the day these keys sit in the owner's KLHook.ini and they pick a stock map.
Fix, either: (a) klbot acts only when the level is not stock - needs one forward declaration, klsteam.c is
included after klbot.c: `static int klx_level_verdict(const char *scene, char *why);` and act only on verdict 2;
or (b) the first write of klb_tune_tick / klb_act sets klsteam's 'until restart' mark (`klx_taint`), which is
the honest version: the round was not a stock round. The log line of each action should say which.
The Log part needs no fix.

### B2 (klbot Van; crash, MUST FIX before Van=2, two lines before Van=1) - the attacker pointer is left behind
klbot.c:517 writes the bot's actor into `[rules+0x1e8]` when it is null and never takes it back. The field is a
raw pointer (slot 33 = 0x4d8a30) and the game dereferences it later with no check of its own:
0x6a11c3 `mov ecx,[esi+0x1e8] / test / je / call 0x7aace0` -> `mov eax,[ecx] / call [eax+0x30]`, and
0x6ece90 -> 0x86ca10 reads `[attacker+4]`. The write is made for grade 1 too, where the rule never reads it.
After a Van=1 call the pointer stays for the rest of the rules object's life; if the vehicle is later destroyed
by the game's own path without slot 33 being called first (not established that it always is), or in a later
round after that actor is gone, the game calls through a dead object's vtable.
Fix: write it only when `klb.van == 2`, and write the old value (0) back right after the call returns.

### B3 (klbot Van=2; crash, ASSUMPTION not proven) - what record +4 is
The write above hands record +4 to code that expects an ENTITY: 0x7aace0 calls its vtable slot 12 with no
argument and compares the result with the class id at [0x1548c7c] (ZFFPlayer's slot 12 = 0x4a7c60 returns exactly
that global); 0x86ca10 takes `[obj+4]` as a pointer into the entity pool and divides. If record +4 is a ZFFActor
(vtable 0xbb3bac; its slot 12 = 0x557ba0 `mov eax,[0x1547b24] / ret`, the same kind of getter) this is fine. The
hook checks only 'vtable somewhere in the image' (klbot.c:515). An object of another family whose slot 12 takes
stack arguments would unbalance the stack inside the game.
Fix: require `avt == 0xbb3bac` (or a short list) before the write and the call; and make the 'record N appears'
line of the log print the actor's vtable, so check K1 settles it before Van=2 is ever switched on.
Alternative that avoids B2 and B3 together: do not write +0x1e8 at all. The game's own code passes a null there
in the bot branch (0x6a1221 calls 0x6ece90 with no test; 0x86ca10 returns 0 for null) and tests it before the
player branch's class test (0x6a11c9). What slot 11 / slot 16 do further in with attacker 0 was not read to the
end by the author or by me - so this is a choice between two unproven paths; the vtable check is the cheaper one.

### B4 (klbot Bribe; behaviour, no crash) - `[rules+0x1b3]` stays the bot's index until the next vehicle
The hook sets +0x1b3 = bot index (klbot.c:479). It is reset only by slot 195 (0x55ee62) at the next vehicle.
While it is not 0xff, slot 129 skips its guards (flags 1 / 0x20 / 0x40 of the caller, the announcement 0x67ee80)
and goes straight to 0x8fb193: a player who shoots a crew member in that window is marked traitor without the
usual announcement. Stock has the same window after the player's own bribe. Say it in the comment; no change.

### B5 (klbot; low) - a 'new round' is assumed whenever the sum of stages drops
klbot.c:424: `stages < klb_r.stages` resets `klb_r` whole, including `bribed`, `leave_rolled`, `van_rolled`
and the backstab pick. If a record is ever released in the middle of a round (not established; a dead member keeps
status 7) the once-per-vehicle limits start again: a second bribe, a second Van call. For grade 2 the second call
returns 0 (state 6 is in the jump table as 'return'), for grade 1 it only zeroes the timer again. Harmless today;
keep the per-vehicle flags out of that reset.

### B6 (klbot; note) - log volume
Log=1: one line (up to ~1 KB with eight records) whenever anything changed, at most one a second, and every 10 s;
the words lines only on a change. Worst case about 60 KB a minute, each line an fopen / fclose on the game's
thread (as every other part of the hook). Tune: 11 lines once per process, then two lines per round ('tuning
written' / 'stock tuning restored'), because `klb_read` is false between rounds and the table is restored and
written again each time. Acceptable.

### G1 (klgun; wrong picture, no crash) - a stale KLGuns.ini is accepted when the counts happen to fit
The file is tied to its build only by the model's object count and the part types. `Entries=` would tie it to the
.prm, but tools\kl_map_guns.py does not write it (the hook's own comment says so), so `klg_f.entries` is 0 and
that test is skipped (klgun.c:331). If a new build goes into the slot and the old KLGuns.ini stays beside the
archive, a Root index can land on another rigid model with the same number of objects (two guns of the same
build are the obvious case): its 'look' parts get hidden, i.e. parts of the wrong gun vanish for everyone who
carries it. Every write still goes to a checked 64-byte rigid mesh object inside the .prm block, so nothing
breaks.
Change wanted in kl_map_guns.py (not my file): write `Entries=<chunk count>`; then make the hook REFUSE a
Version 2 file without it.

### G2 (klgun; residual race, accepted) - the pass can run on KLHook's thread
During a load the fallback thread runs the full pass. Checks, then `klg_poke` (VirtualQuery, WriteProcessMemory):
if the game frees the block in between, the write fails cleanly when the pages are gone (klmem.c decommits a
reserve block on free) and otherwise flips bit 0x80 of one byte in memory the heap may have handed to somebody
else. The window is microseconds and only open while the main loop has been silent for 500 ms. The
read-modify-write of byte +0x1e is not atomic against the game either; no instruction that writes that byte was
looked for beyond the hide bit itself (the author says the same). Not a reason to hold the first live check.

### G3 (klgun; note) - cost of the periodic pass
Every 64th tick a full pass is made even when nothing changed: `klg_file` (a VirtualQuery walk and up to 32
header reads) plus about three ReadProcessMemory calls per part. For the 6-gun file that is a few hundred system
calls about once a second, on the game's thread, well under a millisecond. With the maximum the file format
allows (16 guns x 96 parts) it would be about 5,000. Fine as built; not something to grow.

### G4 (klgun; note) - dependencies that make it silently inert
`klg_level_open` is reached only through klsteam.c's `klh_level_open`, which returns at once when the Steam
guard is off (`!klx_on`, klsteam.c:224) and only for `<folder>\<file>.zip` under Scenes\Locations. With
[Steam] off the gun looks never switch (the level shows what was baked) and nothing in the log says why.
Also: klgun and klchar test only `[session+0x5c] == 4`; klbot adds the `[session+0x54]` test of the game's own
0x7f6850. For a picture-only change that difference does not matter.

## Behaviour in the cases the job named

- No KLGuns.ini / stock level / campaign: `klg_f.on` stays 0 (the file is memset at every archive open; Version
  reads 0), `klg_tick` returns at its first line. Campaign with a file: mode is not 4, nothing is written.
- Frontend after a round (mode still 4, the menu's .prm in the table): the root index is past the count or its
  block is under 8 MB -> 'left alone' once after 3 s, no write.
- No bots: `nb == 0`, no backstab roll; Bribe / Leave / Van need a record with flag 1; nothing acts.
- Stock level: klbot ACTS (B1). klgun does not (no ini).
- Ini keys absent: both inert (first rows of the table).
- Level loading / menu / session end: klbot writes round data only on the game's thread in session state 0x19
  with the record re-read just before each write (`klb_still`); the tuning (plain values in a process-long
  object) may be written from either thread. The Van call is made from the tick, i.e. from the main loop right
  after SteamAPI_RunCallbacks, the same place klchar.c calls 0x8f5e90 from.
- Locks: klg_cs -> klm_cs only in that order; klog and GetPrivateProfile* inside klg_cs use the DLL's own
  imports, not kl2.exe's wrapped slots, so no re-entry into klmem / klslot. The tick is single-entry
  (`klh_tick_busy`), so klb_act and the tuning never run at the same time.

## Order I would run the live checks in
K0, K1 on a TEST build (prints what record +4 is once B3's log change is in) -> K2 .. K5 on a grafted map ->
Van=1 after B2 -> Van=2 only after B2 + B3. Guns: G1 of re\map_guns.md as planned; write `Entries=` first.
