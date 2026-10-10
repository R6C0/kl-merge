# Review: kltalk.c (new), klcrew.c and klcrew_rt.c (changed), as wired into klhook.c

2026-10-10, adversarial review. **Offline only**: the game was not started, nothing was installed, nothing was
written into the Dog Days folder. This file is the only one written in the repository; the builds and scripts are
in the session scratch folder. Reviewed as they stood at 17:15:
`klhook/kltalk.c` (sha1 29147fd4), `klhook/klcrew.c` (d6363d89), `klhook/klcrew_rt.c` (e9d19468),
`klhook/klhook.c` (86f2ad9a), `klhook/KLHook.ini` (baaeadc3).

Words: **RAN** = a command of this session, with its result; **EXE** = read in kl2.exe in this session
(`debug\dasm.py`, `debug\kl.py`); **READ** = by reading the source; **LOG** = a line of an earlier live run's
KLHook.log; **NOT ESTABLISHED** = nobody knows yet.

## 0. Verdicts

| file | verdict | what and where |
|---|---|---|
| `kltalk.c` | **Install switched off. First live check: `[Talk] Enable=1 LogOnly=1`** (calls nothing, section 3.4). **Before `LogOnly=0`: one check to add** | `klk_say`, the block at lines 405-409: also require `[rules+0x5f8]` non-null. The game's routine reads through it without a test (3.2 a). Everything else found is a note, not a blocker |
| `klcrew.c` | **Install switched off; may be switched on for a first live check** (`[Crew] Random=1`, `Names=0`), after a control run with the key off | Nothing blocks. Recommended, not required: line 414, raise the state gate from 0x12 to 0x15 (0x12 is the level load, 2.3 a); line 509, write the voice bytes on the game's thread only (2.3 b) |
| `klcrew_rt.c` | **Install switched off; may be switched on for a first live check** (`[CrewJoin] Enable=1`, `Retrigger=0`) | Nothing blocks with `Retrigger=0`. Before `Retrigger=1`: line 258, test that `jp` is a ZJumpPoint (vtable 0xbc268c) - it is called through unchecked (1.3 a) |
| `klhook.c` (all three, and klchar.c / klbot.c before them) | **One thing to settle before any of the three is switched on for the owner's own play** | `klh_w_runcallbacks`, line 606: `game_thread = 1` is given for ALL TWELVE call sites of SteamAPI_RunCallbacks, not only the main loop's (section 4). Not new, and klchar.c has run live with it; but it is where 'game functions only from the game's own thread, at the main loop' is not what the code does |

With all three keys absent the three files do nothing: section 5 (compiled both ways, the tick compared).

## 1. `klcrew_rt.c` (the AI crew follows the jump)

### 1.1 Addresses and conventions (EXE, all confirmed)

| claim | found |
|---|---|
| 0x62a900 `(actor, rot, pos, a, b)` | `sub esp,0x90`, three pushes, `rot = [esp+0xa0]`, `pos = [esp+0xa4]`, `a = [esp+0xa8]`, `b = [esp+0xac]`; the first 14 bytes are `tele_code`. The hook's cast (ecx, dummy edx, four stack arguments) fits |
| `vtable[0x5bc](0.0)`, `vtable[0x2a8](rot, pos)`, `vtable[0x5d4](pos, 1, 0)` | 0x62a90f, 0x62a92d, 0x62a944, as written |
| `mov edx,[esi+0x7c0]` / `mov [edx],0` without a test | 0x62a998 / 0x62a99e. With `a != 0` and `vtable[0x3d0]() == 0` the same pointer is also `this` of 0x6270d0 (0x62a986) |
| int3 when `+0x77c` and `+0x780` are both zero | 0x62a9b8; the second at 0x62aa43 only with `b != 0` and `0x863a60([0x168e598])` true |
| `cmp [eax+0xec],0` on the non-zero one of the pair | 0x62a9d2 |
| call through `[[actor+0x50c]]+0xac` without a test | 0x62a9e8 .. 0x62a9fc |
| 0x72e0f0: `this` only, plain `ret`; reads `[this+0x34]`, calls through its vtable `+0x14` / `+0x34`, and through `[this+0x24]` | as written; 14 bytes = `trig_code`; one caller, 0x57e1da |
| 0x57e110 clears `[0x156b358]` and `[0x156b35c]`, takes `[gamedata+0x8d4]`, 0x8f3fa0, then `0x72e0f0([entry+0x1c])` | as written |
| vtables 0xbb3bac = ZFFActor, 0xbd3514 = ZGameRulesHeist | RTTI |

### 1.2 Gates (READ)

- Off: `klt_tick` line 224 returns on `!klt.on`. Arcade: line 225, session mode 4. Rules object: line 229, vtable.
- Round: states 0x12..0x19 only, once per round (`klt_r.done`).
- Level: there is NO call of `klx_level_verdict` in this file. The gate is the file: `klt_source` takes the level
  key and file from kljoin.c, and `klj_level_open` (kljoin.c 152) drops a KLJoin.ini whose archive has verdict 1.
  So: never on a stock archive, never at the menu (no level key, line 226). **Difference from the other two
  files**: an archive of verdict 3 ('could not be read as a zip') with a KLJoin.ini beside it is accepted here,
  refused by klcrew.c and kltalk.c. Harmless in practice; say so in the comment or add the verdict test.
- Thread: both game calls sit behind `game_thread` (lines 242, 255). No data write.
- Every pointer handed to 0x62a900 is tested first (line 203-208): actor vtable, node and its flag, the int3
  pair, `+0xec` of the non-zero one, `[actor+0x7c0]` writable, `[actor+0x50c]` with a code address at vtable
  `+0xac`. A record that is aboard or dead is skipped before any of it (line 199).

### 1.3 Findings

a. **`Retrigger=1` calls through an untested pointer** (line 258-259). `jp` is `[entry+0x1c]` of the jump list,
   tested for non-zero only; 0x72e0f0 reads `[jp+0x34]`, calls through its vtable and through `[jp+0x24]`. The
   game's own caller hands over the same field, so a living level has it right; the fix is one line:
   `klh_rd32(jp) == 0xbc268c` (ZJumpPoint, RTTI). Off by default; fix before the key is used.
b. `klt_code` (line 184) accepts any address of the image above the header, .data included, as 'code'. Weak but
   only a plausibility test. Tighten to .text (0x401000 .. 0xb10000) when the file is next touched.
c. EARLY can only be seen when kljoin.c wrote its request in a tick on the game's thread: `klt_tick` runs
   directly after `klj_tick` in the same tick, as the design needs (klhook.c 595-596, RAN: the compiled tick has
   the call there). If the fallback thread wrote it, line 242 says so once and the late form follows.
d. NOT ESTABLISHED (only a run): what an actor in cover or mid-animation does when it is moved with `a = 1`;
   whether a step that is still running in the tower pulls a bot back. As the file says.

## 2. `klcrew.c` (random AI heister looks, and 'who wears whom')

### 2.1 Addresses and conventions (EXE, all confirmed)

| routine | found |
|---|---|
| 0x783fb0 `(entity, model)`, `ret 4` | `0x792290([this+4], model)`; `this->vtable[0x1dc]()`; `[0x541960()]->vtable[0x70](node, 1)`; 14 bytes = `model_code` |
| 0x792290 | 12 bytes = `node_code` |
| 0x88c810 `(entity, variant)`, `ret 4` | `[this+0x50] = v`; the same refresh; 10 bytes = `variant_code` |
| 0x83e2e0 `ret 4`, 0x469250 `ret 0xc` | 15 / 12 bytes match |
| ZFFActor slot 119 | `[0xbb3bac + 4*119] = 0x417a60` |

### 2.2 Gates (READ)

- Off: `klw_tick` line 519. Arcade: line 395. Level: lines 397-405, `klx_on` and verdict 2 exactly; the menu
  gives verdict 0 and returns silently; a stock level and an unseen archive are said once per scene.
- Every game call behind `game_thread` (lines 485, 495, 501). A record aboard or dead is not touched (467).
- `klw_who_now` (new, 220-252) only reads. It needs Arcade, the rules vtable and a level key, so it returns 0
  at the menu. It is called by kltalk.c only when `[Talk] Enable=1`.
- With klchar.c in the same tick: klchar.c goes first (its own body call 0x8f5e90 may hand a bot the player's
  old model); the player's model is part of this file's signature (line 444), so a change restarts the 600 ms
  wait and no bot is touched in the tick klchar.c acted in. The ping-pong is bounded: 3 tries there, `Tries`
  per bot here.

### 2.3 Findings

a. **The state gate includes the level load.** Line 414 lets the file act in states 0x12..0x19. LOG
   (`research\owner_1010_0904\KLHook_0904.log`): `0x0 -> 0x12` comes BEFORE the level archive is opened and
   `0x12 -> 0x15` 1.3 - 2.3 s later, so 0x12 is the load; and through most loads the tick stays 'driven by the
   game's main loop', which can only be the loader's pump (0x48a1e0, section 4). So a game-thread tick can come
   in the middle of a load. What keeps the file out today is only that its conditions (the player object, eight
   heister models, AI actors with models, all unchanged for 600 ms) are not met that early: klchar.c, which has
   no state gate at all, acted 0.3 s after `-> 0x15` in every logged load. Recommended: `state < 0x15` at line
   414. Not a blocker.
b. The voice bytes are written off the game's thread too (line 503-513, by design). Between this tick's vtable
   test and the write the main thread may be ending the session; the byte would then go into a freed block.
   One byte 0..7, a window of microseconds - but there is no reason to take it: put `game_thread &&` in front.
c. `Root=` of KLWardrobe.ini goes into 0x783fb0 unchecked (line 468, 488), as in klchar.c. The file is the one
   beside the archive that was opened, so it belongs to the build; a hand-edited or stale one is a crash in the
   game's model code. No test is possible from the hook side short of reading the .prm chunk table.
d. In round 2 and later the level is not loaded again (LOG: `0x26 -> 0x16 -> 0x18 -> 0x19` within 10 ms, no
   archive opened), so the new draw lands about 0.6 s INTO the running round: bodies change in view during the
   countdown. Not a fault. Whether the actors are new objects then is NOT ESTABLISHED (if they are the same, a
   `Tries` budget of a new draw is fresh: `klw_dress` resets it).
e. Seven Dead Men roots at once mean seven more bone-array sets in a process that has already failed large
   allocations (0x8e5bbd). NOT ESTABLISHED; watch the address-space line of the first run.
f. /W4: C4459 three times (`seen` hides klhook.c's global), harmless. No other warning.

## 3. `kltalk.c` (Kane / Lynch scenes and chatter)

### 3.1 Addresses and conventions (EXE)

| claim | found |
|---|---|
| 0x828fa0 `(this, key, entry)`, `ret 8` | confirmed; 16 bytes = `lookup_code`. An empty key: `[entry] = 0`, answer 0. A key that CONTAINS `alllevels/menu/options/audio/volumevoicechat` or `.../enablemicrophone` is answered from a language table (0x828fcc, 0x829055) - not ours |
| it does not use `this` | confirmed: `edi = ecx` is only handed on to 0x594210, which overwrites ecx before any read |
| the tree is 'the global block 0xe100b8' | confirmed, and more: 0x594210 reads the tree IN PLACE at 0xe100b8 (`movzx ebp, byte [eax]` with eax = 0xe100b8). The found pointer is an address inside kl2.exe's own .data. **So `[entry]` can never point at freed memory**; a stale entry could at worst name another level's text, and the generation key (rules object + scene name) rules that out for one scene |
| 0x860b30 copies the key to `+4` and `+0x104`, then `.wav` | confirmed; needs key length + 5 <= 0x100: the hook's keys are under 100 |
| 0x421c70 `(this, line, other, speaker, last)`, `ret 0x10` | confirmed (`add esp,0x1c ; ret 0x10`); 15 bytes = `say_code` |
| return at once when `[mgr+0x956] != 0` or `[[0x168e598]+0x15d] == 0` | 0x421c8b, 0x421ca6 |
| a plain line (`[line+0x20] == 0`) | 0x421e81: `[line] != 0`; if `[line+0x1c] == 0.0` then `rules->vtable[0xac]()` into it; `0x578840(this = [mgr+0x974], [line], [line+0x24], speaker, float 0xb3ef8c, last)`; with `other == 0` done |
| the line pointer is kept by nothing | confirmed by every use of esi in 0x421c70: `+0`, `+0x1c`, `+0x20`, `+0x24` (and `+4`, `+8`, `+0x14` only when the flag is set). The hook's layout is the constructor's (0x667610: 0, 0xbc998c, 0, 3, 1, malloc(12), 0.0, 0, -1) |
| the queue: count at `[queue]`, ten records of 20 bytes | 0x578865 `cmp [esi],0xa`; 0x57890b .. 0x57892e |

Two things the file's comment does not have (EXE):

- **The ENTRY is kept in two places**, not one: the queue records, and `[queue+0xd8]` = the line that plays now
  (0x7d0f45). 'Never freed' is therefore right and necessary.
- **A queued line does wait for the one that plays** (the comment lists it as not established): 0x7d0e80
  answers 0 while `[sysif+0x28]` is below the time kept at `[queue+0xcc]`, which it sets from the playing
  sound's length (0x7d0f4b .. 0x7d0f7b); 0x578840 then queues. Consequence for the countdown: a clip that is
  longer than the gap to the next one pushes every later line back; the six do not stay on the blast by
  themselves. Check T1 should compare the clip lengths with the `at` values.
- The speaker is used: 0x7d0e80 asks `rules->vtable[0x138](speaker)` (in use, below the count), takes the record
  (0x7fd930), and for an AI record hands `[record+4]` (the actor), for a human `0x5c3b10([record])`, to the HUD
  (0x59fb20 -> 0x7aad00). If the speaker is NOT a record in use it answers 0 AFTER the sound was started, and
  0x578840 queues the line as well: it would be said twice. The hook only passes records in use (3.3 d).

### 3.2 Findings

a. **One unchecked pointer on the path of every say: add the test before `LogOnly=0`.** With `last == 0` (what
   the hook passes) 0x7d0e80 calls 0x4658f0 (0x7d0ec6), which calls `rules->vtable[0x1c8](local player)` =
   0x771a10: `mov ecx,[ecx+0x5f8] ; mov eax,[ecx+eax*4+0x1d4]` - no test of `[rules+0x5f8]`. The game itself
   treats a null there as possible: slot `0xac` of the same class (0x75dd60) tests it and answers 0.0. In state
   0x19 it is most likely set (the chatter part reads the members' money through it, line 615), but the hook's
   rule is 'every pointer checked'. Fix, in `klk_say` beside the manager tests (line 405): read
   `[rules+0x5f8]`, refuse and say so when it is zero.
b. Arcade is tested as `[session+0x5c] == 4` (klcrew.c 224). The game's own test 0x7f6850 also wants
   `[session+0x54]` not 2 or 3. Followed through: with 2 or 3 there 0x421c70 takes its other branch
   (0x421f07), which gets the rules object by 0x7bb2a0 (mode 4 only) and ends in the same 0x578840 call. No
   fault either way; what `+0x54` is, is NOT ESTABLISHED.
c. A member that is ABOARD (status 4) counts as 'there' (line 429) and can be the speaker of a scene line. For
   an AI record the game then hands `[record+4]` to the HUD. klcrew.c's own comment says of such a record 'its
   actor may be gone'. `klw_who_now` gives a character only to a record whose actor still has the ZFFActor
   vtable, read in the same tick, and the game's own lines carry the same exposure; still, for the first runs
   prefer 'in play' for AI speakers (status 0), aboard for the human only.
d. 'Speech is off' is logged for EVERY attempt (line 410): with chatter that is up to one line a second for a
   whole round, each one an open / append / close of KLHook.log on the game's thread. Say it once per round.
   The same for line 382.
e. `klw_who_now` runs every frame of a round: about ten reads plus four per crew record, each a
   ReadProcessMemory system call, and `klk_source` / `klw_source` take klchar.c's lock every frame. klnudge.c
   showed what a per-frame millisecond costs; this is far below that, but a 100 ms throttle on the chatter half
   costs nothing.
f. A NaN in `Gap=` of KLTalk.ini passes the clamps (line 350-352) and makes the idle test true every tick; the
   `Quiet` clamp still holds it to one line a second. Our own file; reject non-finite numbers when next there.
g. Memory: a line is 0x34 bytes per say, an entry 0x204 per key and level generation, at most 320 entries
   (165 KB) a generation. Nothing is handed to the game's allocator. Fine.
h. No /W4 warning from this file.

### 3.3 Gates (READ)

a. Off: `klk_tick` line 521. Arcade, rules vtable, level key: `klw_who_now` (522). Level: `klx_on` and verdict
   2 exactly (523-528); the menu has no level key and returns before that. Round: state 0x19 only (536).
b. Thread: line 530 returns for a fallback tick BEFORE `klk_source` and everything after it; `klk_say` and
   `klk_entry` are reached from `klk_tick` only.
c. Before each call: both code prefixes, manager, `+0x956`, queue and its count <= 10, session `+0x15d`
   (lines 401-410); the lookup's `this` chain (381) - which the routine does not even use.
d. The speaker is always `w.m[..].rec` of a record `klw_who_now` found in use in this tick.
e. With klbot.c / klchar.c in one tick: kltalk.c runs after klchar.c and klcrew.c and takes its own snapshot at
   its start, so it sees the models they have just set; klbot.c runs after it. `klh_tick_busy` keeps a second
   tick out while a game call is running (a call that pumps Steam re-enters the wrapper, not the tick).

### 3.4 Why `LogOnly=1` is safe as the first run

READ: `klk_say` line 400 returns on `klk.logonly` before the code comparison, before `klk_entry` and before
either call; nothing else in the file calls or writes the game. So T1 exercises the whole script (triggers,
Needs, who wears whom, timing) with reads only.

## 4. The tick's 'game thread' is wider than the main loop (klhook.c, concerns all three)

EXE: the import slot of SteamAPI_RunCallbacks (0xb107bc) has **twelve** call sites. Two are in the main loop's
routine 0x87a930 (0x87a9e6, 0x87aa7c). The others:

| site | in | what it is |
|---|---|---|
| 0x48a1f4 | 0x48a1e0, twelve callers, one of them 0x53ac96 just before a scene is loaded | the loader's pump (`SetThreadExecutionState`, RunCallbacks, session update) |
| 0x4e4b43, 0x81a856 | 0x4e4b30, 0x81a840 (vtable slots) | session / lobby update |
| 0x64ba20, 0x6fc302 | 0x64ba10, 0x6fc1c0 | network receive (`SteamNetworking`), network send loop |
| 0x456033, 0x45f5a3, 0x5b2173, 0x87bfe3, 0x8a7543 | five three-instruction getters (`RunCallbacks ; return [this+n]`) | whoever asks a Steam-backed object for its state |

`klh_w_runcallbacks` (line 606) calls `klh_tick(1)` for every one of them. So 'on the game's thread' means 'in
whatever routine polled Steam': in the middle of a level load (LOG, 2.3 a), inside a session update, or - if
any of these runs on another thread, which is NOT ESTABLISHED - off the main thread altogether.
`klh_main_tid` is recorded (line 582) but never compared.

This is not new: klchar.c and klbot.c have made their game calls under it in live rounds. But the three new
files add six more game routines to it. A fix of a few lines in klhook.c, for the lead to decide:
`game_thread = GetCurrentThreadId() == klh_main_tid && (return address is 0x87a9ec or 0x87aa82)` (the two
main-loop sites; `_ReturnAddress()` in the wrapper), with `klh_main_tid` taken from the first call that has one
of those return addresses. Until then the state gates (0x19 for kltalk.c, the settle wait for klcrew.c, a
pending request for klcrew_rt.c) are what keeps the calls out of a load.

## 5. All keys absent: the three files are inert (RAN)

Two copies of `klhook\` in scratch: as in the tree ('with'), and with the nine lines of the three files taken
out of klhook.c ('without'). Each built SHIP (`build.bat`) and TEST (`build_auto.bat`) with
`KLHOOK_CFLAGS=/FAs /W4`: four builds, exit 0. DLL sizes: SHIP 275,968 / 237,056, TEST 324,608 / 286,720.

`_klh_tick` of the two SHIP listings, instruction by instruction (diff of the code lines; labels aside):

| with | without |
|---|---|
| after `klj_tick`: `push edi ; call _klt_tick ; add esp,4` | - |
| after klchar.c's part: `cmp _klw,0 ; je ; cmp _klh_exe_ok,0 ; je ; call _klw_level_tick` (`klw_tick` inlined) | - |
| `push edi ; call _klk_tick` | - |
| `push edi ; call _klb_tick` ... | the same |

Nothing else differs. What the added calls do with the keys absent:

- `_klt_tick`: frame of 328 bytes, stack cookie, three locals set, `cmp _klt,0 ; je` to the cookie check and
  `ret`. No read of the game.
- `klw_tick`: the two compares above; `_klw_level_tick` is not entered.
- `_klk_tick`: `push ebp ; and esp,-64 ; sub esp,2036`, cookie, five locals set, `cmp _klk,edi ; je` to the
  cookie check and `ret`. No read of the game. (2 KB of the main thread's stack for the length of the call.)

Start-up (READ): `klt_init` three, `klw_init` fifteen, `klk_init` six profile reads of KLHook.ini and a memset
of about 120 KB of the DLL's own .bss; no log line, no game memory, no import slot. `GetPrivateProfileIntA`
answers the default 0 for a section that is not in the file, so an installed KLHook.ini without `[Crew]`,
`[CrewJoin]` and `[Talk]` leaves all three off. The sample `klhook\KLHook.ini` has the three keys at 0.
Order (RAN, the DllMain listing): `klj_init` before `klt_init`, `klc_init` before `klw_init` and `klk_init` -
the two locks they use exist before the ticker thread starts.

## 6. For the first live checks, in this order

1. The new DLL with the three keys absent: a control round on the owner's build. Expect no `crewjoin:`,
   `crew:` or `talk:` line at all.
2. `[Talk] Enable=1 LogOnly=1`: the script's timing, reads only (3.4).
3. `[Crew] Random=1` (Names=0): watch for `crew: bot N ... it now has M`; a fault here is in 0x783fb0 on an actor.
4. `[CrewJoin] Enable=1` (Retrigger=0) on the full Retomoto build.
5. `[Talk] LogOnly=0` only after 3.2 a is in.
One key at a time: three unrun parts in one run cannot be told apart in a dump.
