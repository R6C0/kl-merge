# The score-page crash (RN11) and the round counter

Written 2026-10-09 (agent g-crash). Offline only: nothing was run in the game, nothing installed.
Material: `<DD>\KLHook_3.dmp`, `KLHook_4.dmp`, `KLHook_stackoverflow.dmp` (all 08:49, run RN11),
`<work>\build\klhook\live\RN11.log` / `RN12.log`, kl2.exe read with `debug\dasm.py`, `debug\rtti.py`.

Words: **read** = read off the disassembly (address given) or off the dump's memory;
**ASSUMPTION** = fits the evidence, not proven; **not established** = unknown.

## 0. Summary

1. The crash is an **uninitialised member in kl2.exe**: `ZLeaderBoardServiceSteam`'s row count
   (`+0x31fc`). Its constructor never writes it; it is written only when a Steam leaderboard
   download comes back with at least one row. The score page asks the service "which row is
   mine?" as soon as the download has ended, successful or not, and that walk uses the count.
   In RN11 the count was heap garbage `0x1b1f5280`, the walk ran past the 114 rows the object
   holds and called through a null vtable at row 114 (read).
2. **No level data is involved.** Not the Dead Men map, not the graft, not the sound merge, not
   the post filter. The path is: stock HUD element `HeistStatusLeaderboard*` -> exe ->
   Steam. The same code runs on the score page of a stock Subway Arcade round.
3. Why once and not the next time: the garbage is whatever the heap block held when
   `ZOnlineServiceSteam` was built at boot. It crashes only when that dword is > 114 as a signed
   number; 0, a negative value or a small one is harmless (ASSUMPTION for the passing runs: no
   dump of them exists to read the value from).
4. The "stack overflow" is a second, separate fault **of the test harness**: klauto's
   unhandled-exception filter and wrap_oal.dll's filter each call the other as "previous"
   (18,003 nested rounds on the stack, read). Not a recursion in the game.
5. Fix: one data write by the hook (count = 0 before the first query). No level change. Section 4.

## 1. The fault

Registers (KLHook_3/4.dmp): `eip=00838922 edi=1b1eef00 ebx=1b1f20f8 esi=00000072 edx=0`,
read of address 0.

`0x8388e0` = `ZLeaderBoardServiceSteam@OnlineServices` vtable (0xbd5cc4) slot 6:
"find the row of this Steam id" (`rtti.py 8388e0`).

```
8388e0  this = edi; *out_row = -1; *out_rank = -1
838902  if [this+0x31f8] != 0 -> return 0            ; a request is still running
838915  for esi = 0; esi < [this+0x31fc]; esi++      ; ebx = this + 0x18 + esi*0x70
838920      edx = [ebx]            ; row vtable
838922      eax = [edx]   <== fault ; row slot 0 = flags
838928      if flags & 8 and row id == wanted id -> found: sprintf(out, "%s", row name), return 1
838956  return 0
```

The object (constructor `0x659790`, the only writer of the vtable besides the destructor; its
only caller is `ZOnlineServiceSteam`'s constructor at `0x879faa`, allocation `0x89e850(0x3208)`):

| offset | meaning | written by |
|---|---|---|
| +0x04 | owner (`ZOnlineServiceSteam`) | ctor |
| +0x08 / +0x0c | board id / request mode of the rows held | ctor 0, slot 4 |
| +0x10 / +0x14 | first / past-last index held | ctor -1, slot 4 |
| +0x18 | 114 rows of 0x70 bytes, `ZLeaderboardEntry` (vtable 0xb56f68, ctor `0x903070`): `lea ebx,[ebp+0x71]` ... `sub ebx,1; jns` = 0x72 = 114 | ctor |
| +0x31f8 | running request (0 = none) | ctor 0, slot 4 |
| **+0x31fc** | **row count** | **slot 4 only (`0x5554aa`), and only when the request returned > 0 rows** |
| +0x3200 | total entries on the board | ctor 0, slot 4 |
| +0x3204 | never touched | - |

Every instruction in kl2.exe that names offset 0x31fc was listed (byte search for `fc 31 00 00`
in .text, 5 hits): one write (`0x5554aa`), four reads (`0x6117b7`, slot 7 `0x827c50`, and the two
in slot 6). The constructor is not among the writers.

In the dump: 114 * 0x70 + 0x18 = 0x31f8, so "row 114" (`esi = 0x72`, `ebx = this+0x31f8`) is the
object's own tail: `[this+0x31f8] = 0` is read as the row's vtable -> `mov eax,[0]`.
`[this+0x31fc] = 0x1b1f5280` (a heap pointer 0x6380 past the object: the block's previous
content), `+0x3204 = 0x1f`. Rows 0..5 and 111..113 are in the dump and carry the row vtable.

State of the service at the fault (read from the dump): board 3, mode 1, first = 0, past-last = 0,
request = 0, total = 0. `past-last = first` proves that no row was ever stored in this process:
slot 4 sets `+0x14 = first + n` in the same block that writes the count.

## 2. Who calls it, and with what

`0x5b65af` in `0x5b5f40` = `ZMercsShowInfoFA` slot 8 (the HUD text provider). For the elements
`HeistStatusLeaderboardRank / Name / Points / Rounds` (`0x5b6488` .. `0x5b64c6`) it runs a small
state machine on the global `[0xced370]`:

```
service = [[0x168e598]->slot 11]->slot 79      ; session manager +0x17c = ZOnlineServiceSteam, its +0x198
state -1 (5b64d6): service->slot4(board, mode 1, index 0, buf); state = -3
state -3 (5b6514): if service->slot12()  (= [+0x31f8] != 0, 0x755750)  -> slot4 again (polls), leave
                   else (5b6558) service->slot6(my Steam id, &row, &rank, name)      <== RN11
                        found -> state = row ; not found -> state = -2
```

In the dump `[0xced370]` is not captured, but the stack at the fault holds the text
`76561199125667746` (the Steam id being looked for) and two `ZMercsShowInfoFA` objects.

Slot 4 = `0x5553c0`: creates a request (`0x49f440` -> `0x789700`:
`SteamUserStats()->FindOrCreateLeaderboard(name[board], 2, 1)`, names at `0xd36aa8`: board 3 =
`KL2_Heist0_TotalMoney`, i.e. the Arcade board of slot 0 = F01), polls it, and when it is done:

```
555461  if request->status() == 1:  n = request->rows()
555491      if n > 0:  copy rows to this+0x18 ; [this+0x31fc] = n ; [this+0x3200] = total ; [this+0x14] = [this+0x10] + n
5554c5  delete request ; [this+0x31f8] = 0
```

Mode 1 is mapped to Steam's request type 2 = friends only (`0x755230`). So the count stays
unwritten when the download fails (no Steam connection: status 3 at `0x789770` / `0x6ddb2d`) **or**
when it succeeds with no row - an account with no friends on the board and no entry of its own.
Which of the two happened in RN11 is not established (the request object is freed and gone from
the dump); either way the walk at `0x838915` then runs on the constructor's leftover.

The crash came 0.55 s after the window came up (RN11.log 08:49:23.918 -> 08:49:24.469): the time
the Steam call took to come back.

## 3. Why RN11 and not RN6 / RN7 / RN8 / RN10 / RN12

- The service is built once per process, in `ZOnlineServiceSteam`'s constructor. The allocator
  (`0x4a2fd0` -> `0x4aa010`, the game's own heap) does not clear the block - the pointer found at
  +0x31fc is the proof.
- `jle` at `0x83891b` is a signed test. The walk is harmless when the leftover is <= 0, and when
  it is 1..114 (default rows: slot 0 returns flags without bit 8 - ASSUMPTION, `0x6e2650` not
  read). It faults for every value > 114, at row 114, because `[this+0x31f8]` is 0 whenever the
  walk is allowed to start.
- So the outcome is decided at boot by what the 0x3208-byte block last held. ASSUMPTION: in the
  passing runs it was 0 or negative. No dump of a passing run holds the object (all dumps under
  `<DD>` and `%TEMP%\kl_triage` were scanned for the vtable 0xbd5cc4; only the three RN11 dumps
  have it), so the passing value was not read.
- The other reading - the leftover is always large and RN11 differs because the Steam download
  failed that once while the other runs got a row - is not excluded. It does not change the fix.
- Nothing from the round feeds it: not who was alive, not the score, not the player count. The
  wanted id is the local Steam id; the rows are Steam's.
- Grafted data: none on the path. The window and its four elements belong to the host's
  `AllLevels/mainsceneincludes_multiplayer.zip`; `ZMercsShowInfoFA`, the service and the request
  are exe objects created at boot, before any level is read. A stock Subway Arcade round runs the
  same instructions at its score page. ASSUMPTION on why stock players rarely see it: Steam's
  friends request includes the user, so an account that has ever posted a score on the board
  gets its own row back and count >= 1 is written before the walk.

### The stack overflow is the harness

`KLHook_stackoverflow.dmp` has no exception record (`debug\dump.py` raises on it; read with a
direct stack scan instead). From 0x1753000 up to 0x1b4ec78 the stack is one group of frames
repeated 18,003 times at a spacing of 0xe8 bytes:

```
dinput8.dll+0x7ae6 / +0x7a60   (klauto: kla_uef, the branch 'came back N times' -> kla_prev_uef(ep))
KERNELBASE.dll+0x10eaab
wrap_oal.dll+0x42dd9
wrap_oal.dll+0x4921d           (inside wrap_oal's own top-level filter at +0x491ba)
```

RN11.log, boot of that run: `unhandled-exception filter re-installed over 226591BA` and
`... over 22A591BA` = wrap_oal.dll (0x22a10000) + 0x491ba. OpenAL's wrapper installs a filter that
chains to the one it replaced (klauto's); klauto's timer (`klauto.c` line 1653) then installs
itself again and remembers wrap_oal's as *its* previous. Each now calls the other. The first
unhandled fault of a run is logged and dumped and then handed on; the hand-on never returns.
The log's "came back 10 / 100 / 1000 times" lines are stamped in the same millisecond: nested
calls, not the game resuming the fault.

So: `RESULT FAIL (stack overflow)` means "an unhandled fault happened" and nothing more. The
predecessor's report line "the game's filter resumes the fault endlessly" is wrong for this run.

For klauto.c (not my file): when re-arming, do not take a filter as `kla_prev_uef` that was
installed after klauto's own first install - keep the first previous (the game's, 0x73FB2571 in
the log is not kl2.exe either; the game's own is set at 0x58ffca) - or guard `kla_uef` with a
thread-local depth counter and return `EXCEPTION_CONTINUE_SEARCH` when entered a second time.

## 4. Fix and the experiment

### The cheapest experiment (one run, no rebuild of the level)

Log the count before the round and at the score page. klauto's `peek` follows one pointer; this
needs three: `[[[0x168e598]+0x17c]+0x198]+0x31fc` (only valid when `[[0x168e598]]` = 0xbd1ebc,
`ZSessionManagerMultiplayer`; the base class returns 0 from slot 11). With a `peek` that takes a
chain, put it at script line 21 (after the load) and at label `score`:

- value <= 114 and no crash, value > 114 and crash, over a handful of boots -> hypothesis
  "boot leftover" confirmed; the rate of the crash is the rate of a positive leftover.
- the same large value in passing runs, with `+0x14` > `+0x10` (rows arrived) -> hypothesis
  "Steam answer differs".

Also peek `+0x10` / `+0x14` (first / past-last) at the score page: equal = no row came.

### The fix: a data write in the hook, not a level change

Nothing in kl_fa / kl_graft can reach this: the object is not level data.

In KLHook (the shipped dinput8 proxy, and klauto for tests), once per process, as soon as the
chain resolves (first frame on which `[0x168e598]` is a `ZSessionManagerMultiplayer` whose +0x17c
is non-null and whose +0x198 has vtable 0xbd5cc4):

```
lb = [[[0x168e598] + 0x17c] + 0x198]
if [lb+0x10] == -1 and [lb+0x14] == -1 and [lb+0x31f8] == 0:      // never queried: ctor state
    [lb+0x31fc] = 0
```

It is a heap write of the value the constructor should have stored; no code byte changes, so it
is outside what `re/antitamper.md` describes. After a successful query the game maintains the
field itself. (Alternative without the hook: none found - there is no ini key on the path, and
the element names cannot be removed from the host HUD without losing the score page.)

Side effect to know about (read, not judged): the Arcade score page talks to the real Steam
board `KL2_Heist0_TotalMoney` from the F01 test slot. Whether a round on a grafted map also
*uploads* a score there was not read here; if it does, test rounds post Dead Men-map scores to
the public Subway board. Worth a look before many more rounds are run.

## 5. 'Round: 1' in round 2: stock Arcade behaviour

Not a graft effect. In Arcade the number is the stage reached, and it only goes up when the
player ESCAPES. RN8 / RN10 / RN12 all ended by death or by the clock, so 1 is the right number.

Read:

- HUD element `HeistRoundsCounter` (`0x5ba918` in `ZMercsShowInfoFA` slot 8): text =
  `sprintf("%s %d", loc("/Menu/Heist/Round"), 0x7d85b0([0x168e9e4]))`. The label is a .LOC key
  of the host, the element is the host's; neither comes from Dead Men's layer.
- `0x7d85b0`: with game mode 4 (`[[0x168e598]+0x5c]`) it returns the byte
  `[[rules+0x54]+0x5f8]+0x45`, rules = `ZGameRulesHeist`, +0x5f8 = its replicated state block.
- That block's constructor (`0x835512`): `+0x45 = 1` (round), `+0x44 = 3` (lives).
- The only increment in the exe: `0x74bcf0` `inc byte [state+0x45]`, in `ZGameRulesHeist` slot 7
  (per-frame update, `0x74b6d0`), case session state 0x22 (jump table `0x74be30` / `0x74be58`),
  guarded by `0x74bce4 cmp byte [[this+0x348]+0x10], 6`: player record 0 (records are 0x7c
  bytes) must be in state 6.
- State 6 is written in one place, `0x805367`, the escape pass `0x805120`: players in state 4
  (aboard) go to 5 and then 6, their 'rounds escaped' counter is incremented (`0x8053a7`).
  `0x70b955` (round end) banks the carried money of a state-6 player into his total and zeroes
  everybody else's - which is the 'Total score: $0' of RN12_240s after $100,000 was looted and
  the player died.
- Pictures agree: RN12_160s 'FRAGILE ALLIANCE ARCADE - ROUND 1, Lives left: 3 skulls';
  RN12_240s / 290s (second round) two skulls, 'Round: 1', '$0'. A death costs a life, the stage
  stays.

So 'Round' will become 2 on the first run that reaches the van. Until the escape works
(`re/fa_round.md` section 6) every repeat is stage 1 with one life less, and after three deaths
the session ends. No settings field and no HUD text object needs changing.

Not read: where the lives byte is decremented (it is set through `0x8632b0`, reached by a
virtual call), and what stage > 1 changes (the squad `eHeistOnly` waves, see `re/fa_round.md`).

## 6. The single fault at kl2 0x8e5bbd (run RD1, stock L01 loading)

`0x8e5ba0(ptr, align, size)` stamps a block header: `p = (ptr + align-1) & ~(align-1)`,
`[p] = 0x12345678`, links it into the list at `0xe05578 / 0xe0557c`. Its caller `0x7bb2c0`
(the big-block path of the game heap, behind `0x4aa010` / `0x4a2fd0` / operator new `0x89e850`):

```
7bb336  eax = HeapAlloc([heap+0x10f8], 0, size + 0x2f & ~0xf + 0x10)
7bb34f  0x8e5ba0(eax, 0x10, size)          ; no test for NULL
```

In RD1's log (kept inside `live\M01D.log`, 06:00:58): `eax = 0`, `edx = 0` (the pointer),
`ebx = 0x01b82224` (the size: 28.9 MB), write to address 0, caller `0x8205b9` =
`ZEngineDataBase` slot 8 reading a scene file into one block. So: **HeapAlloc returned NULL for a
28.9 MB block and the game does not check.** kl2.exe is not large-address-aware (PE
characteristics 0x103), so it has 2 GB and needs a 29 MB hole in it.

Can klauto's detours cause it? Not by what they do - none of the callers is a detoured site and
the fault is in plain allocation. What the hook adds is memory pressure (ASSUMPTION, not
measured): the run had loaded the menu scene and L00 and went into L01 1.2 s after L00 finished
loading (the script skipped the intro), and klhook wrote a 33 - 48 MB minidump at the start of
every load (three before the fault, the last 6.6 s before it, each for Steam's anti-debug probe
0xa8e3cb, which is not a crash). RD3 took the same route without a fault, as did the stock game
always. It is an out-of-address-space event, not a data fault, and it does not concern the graft.

For klhook.c (not my file): do not dump for the fault address 0xa8e3cb (klauto's own handler
already steps over it, `klauto.c` line 1545); that also frees the MaxDumps budget for real
faults. Cheapest check if it ever comes back: log the largest free block (VirtualQuery walk) at
each LOAD start.
