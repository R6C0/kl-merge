# Review of track F3 - the crash of the first live climb (re/climb_crash.md, klhook/klclimb.c fourth version, tools/kl_fa_climb.py)

2026-10-11, adversarial reviewer. OFFLINE: no game was started, the game folder was only read (the 21 stock
archives, for one count), nothing committed, no tool or source file changed; this file is the only thing written
in the repo. Scratch (not in the repo): `<scratchpad>\rev_f3\` - my own readers over `debug\kl.py` (`jt.py` the
switch tables and vtables, `stk.py` / `node.py` the dump's stack, player and channels, `callers.py` call sites with
the class and slot of each caller, `kind23.py`, `vcall.py`, `evids.py`, `evclass.py` / `evclass_all.py` event ids by
body class, `cmpzip.py`), the hook rebuilt in `hook_test\` / `hook_ship\`, the off-game test rebuilt in `simrun\`,
a rebuilt level (deleted again after the comparison).
Status words: **READ** = seen by me in the disassembly or the dump at the address given; **MEASURED** = counted by
a script of mine or by a tool I ran; **REASONED** = follows from the two, not looked at directly.

## Verdict: ACCEPT WITH FIXES

- **The cause stands.** I re-derived it from `KLHook_1.dmp` and `kl2.exe` without the worker's notes: the chain, the
  event (index 0, id 5, frame 6, handed out at channel frame 6.03), the object that is null (`[action+0xc]` of a
  `ZFFActionMiniAnim`, written 0 by its constructor) and the routine that uses it untested (`0x6370e7`). Every
  other candidate of the task's list is excluded by something in the dump or the code (section 1).
- **The fix does what it says, as far as reading and files can show.** An event id 105 reaches `0x6372d3`
  (`mov al, 1`) and id 6 goes there by the table; the level differs from its first form in exactly 7 dwords; the
  hook refuses a first-form level before anything is started. All checks the worker reports give the lines it
  reports; the level rebuilds to the same sha1; both hooks build; the off-game test rebuilds and passes.
- **No finding blocks the next live run** (`z_climb3\M03`, a TEST hook built from the tree, `[Climb] Enable=1
  Dry=0 Log=2`). One statement of the account is wrong as written and must be corrected (M1); the rest are
  SHOULD / NOTE.
- **The next fault of the same class**: I found one more way into the faulting routine that the account does not
  have (events of OTHER channels of the player, M1) and closed it for this build by reading and counting; I found
  no other (section 3).
- Nothing of the fourth version has run. What follows is evidence that the reading is consistent, not that the
  game agrees.

## 1. The cause, re-derived

| claim | how I checked | result |
|---|---|---|
| fault = `cmp dword [ecx+0x60], 0` at `0x47e400` with ecx = 0, called at `0x6370ef` | `debug\dump.py`, `dasm.py 47e400`, `637060` | READ. `0x47e400` has ONE call site in the exe, `0x6370ef` (`callers.py`: MEASURED) |
| the stack is the event hand-out | `stk.py`: esp+0x44 `0x8b76f3`, +0x50 `0x7c6ca2`, +0x64 `0x60c3c0`, +0x80 `0x8b6917`, +0xb8 `0x50af65`, +0x200 `0x74f043`, +0x288 `0x58085b`; `0x446200`, `0x818623`, `0x55c7ba`, `0x6934ad` lie inside locals | READ, as the worker has it |
| which event | esp+0x84 .. 0x90: channel `0x37542a0c`, time 6.0, frame 6.03, index 0; the record `0x79553a94` = {5, 6, 0xffff}{6, 20, 0xffff}; esp+0x4c = 20 (written at `0x6370cc`), eax = 6 (`0x6370d0`) | READ |
| the action is real and has no object | `0x0150d1c4`: vtable `0xbb4f0c` (RTTI `ZFFActionMiniAnim`), +4 = 0x23, +8 = the player, **+0xc = 0**, +0x18 = 0x9c9, +0x20 = the channel, +0x24 / +0x25 = 1 / 1; the dispatcher `0x3779e560` (vtable `0xba38d8`, RTTI `ZActionDispatcher`) holds it at +4; the constructor `0x6b2970` writes 0 at +0xc (`0x6b2987`); the destructor frees to the pool `0x15151c0` (`0x5c0301`) - the address inside the image is the pool's | READ |
| slot 13 of a mini animation is the generic action's routine | vtables `0xbb4e5c` / `0xbb4f0c`: slots 11, 12, 13 = `0x8b76e0`, `0x721060`, `0x637060` in both | READ |
| case 5 uses the object with no test | `0x637093 .. 0x6370ef`: `0x5a6ec0`, two `0x4a75d0`, `mov ecx, [esi+0xc]` / `call 0x47e400` | READ |
| the switch | `jt.py`: targets `0x6372e0` x 13, byte table `0x637314` x 49: 5 -> `0x637093`; 9, 24..29 -> `0x637135`; 10, 30..35 -> `0x637147`; 11, 20, 21, 42, 48, 49, 50, 51, 53 single cases; 6, 7, 8, 12..19, 22, 23, 36..41, 43..47, 52 -> `0x6372d3`; outside 5..53 `ja 0x6372d3` (`0x63707f`) | READ: the worker's table and `GENERIC_ACTS` are right |
| the queue | `0x153af6c`: count 2; entries {handler `0x60c370`, time 6.0, index 0} and {`0x60c370`, 20.0, index 1} | READ: one subscriber, event 6 still queued |
| who subscribes | `0x76d22e` (the mini animation's start) -> `0x7f60e0` -> `0x4011e0` | READ |
| the stagger never plays | `0x5022c0` passes `[player+0x25b0]`; the name `/Special_moves/Cover_From_Explosives` (`0x89cb31`) is in 0 of the 21 stock `.ANM` and not in the build's | MEASURED (`stagger.py`) |
| `ZFFActionMiniAct` returns at id 5 | `0x68ac6d` -> `0x68ad60` = `mov al, 1` | READ |
| the vault does not subscribe | `0x6a27e0` is not among the 23 callers of `0x7f60e0`; its slot 11 `0x557da0` = `mov al, 1` | MEASURED / READ |

**The other candidates.** (a) The hook's own `AlignTo`: not on the stack; the game's alignment state in the dump
is `[player+0xe8] = 0`, `[player+0xec] = 6.0` - the alignment the hook asked for (6 frames) was TAKEN (READ).
(b) Event 6: its entry is still queued. (c) 60 frames a second: the channel's own rate is 25 (`+0x10`), frame 6.03.
(d) Speed, body, rifle, money: none is read on the way from `0x50af60` to the fault (READ: `0x8b67d0`, `0x60c370`,
`0x89f480`, `0x9290f0`, `0x7c6c80`, `0x8b76e0`, `0x721060`, `0x4a75d0` and `0x637060` up to `0x6370ef`; `0x5a6ec0`,
'the channel that plays this clip', I did not read - it returned a channel, or case 5 would have left at `0x6370a4`).
(e) A channel that ended: all of his other channels the dump holds (1 .. 12) are in state 0 with **queue pointer
0** (`node.py`); 13 .. 15 are not in the dump. (f) `KLHook_2.dmp` is the same fault at the same registers.

## 2. What was re-run

| | my result |
|---|---|
| `kl_fa_climb.py check` on `z_climb3\M03` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)`; on `z_climb\M03` and `z_climb2\M03`: `FAIL (2 FAIL, 1 NOTE)` |
| `kl_impact.py` | `problems: 0 in 1 levels` |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 1 NOTE)`; against the same check on `z_cover3\M03` ONE line differs (`.ANM 22202616` / `22343864`) |
| `kl_maps.py audit` (on a copy) | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` |
| `kl_map_escape.py van-check` | `0 fault(s)` |
| `kl_anm.py check` | `byte-identical: 41 of 41` |
| the archive | `F01_Main.zip` sha1 0698b298de54bcebd8bfb1972c0509df01f43983, 200,895,904 bytes; 31 members, only `Scenes/Locations/F01/F01_Main.ANM` differs from `z_cover3\M03` and from `z_climb2\M03`; against `z_climb2` the member differs in 7 bytes = 7 dwords 5 -> 105 at 0x1502fd8, 0x1506a64, 0x150a7ac (frame 3), 0x150c888, 0x150e9a8, 0x151130c, 0x1513cf0 |
| `kl_fa_climb.py apply z_cover3\M03 <my scratch>` | the same archive sha1 and the same `KLJoin.ini`: the build is reproducible |
| `kl_fa_climb.py apply z_climb2\M03 <my scratch>` | refused, nothing written (`ValueError: Kane has the climb slots already and its clips ... carry an event id kl2 0x637060 acts on`) |
| `build_auto.bat` / `build.bat` into my scratch | both build; the one warning is `klhud.c(187)`; `cl /Zs /W4` names no line of `klclimb.c`. My DLLs: TEST a43efc24..., 485,888 bytes; SHIP d5b10f33..., 435,200 bytes (a hook carries its build time, and `klescort.c` changed at 10:52, after the worker's build: the SHIP size differs from its 434,688). The worker's two files have the sha1s it reports |
| the five new byte rows and the two vtable entries of `klq_code` | all equal `kl2.exe` |
| the off-game test, rebuilt from the worker's `sim.c` against the tree | `SIM: PASS (0 failed)`, 84 `ok` lines; the third version (git HEAD, sha1 5eeedfab...) `faults in the model at frame 6` |

## 3. The rest of the clip's life, looked at for the same class of fault

What I read beyond the worker's section 7:

- **Everybody who asks for a current action of kind 0x23** (`kind23.py`: of the 213 sites that load
  `[reg+0x388]` - the 'kind of the current action' slot among them - five go on to compare with 0x23).
  `ZFFActionMiniAct` has kind 0x23 too (`0x5c742f`). `0x649e6d` and `0x81cabb` read
  `[action+0x14]` and test it (the hook passes x = 0, as the stagger does); `0x69cb0e` calls the action's slot 14,
  which is `mov eax, 1` in a mini animation (`0x9a00e0`) and leaves; `0x424474` is a mini cutscene task (stops a
  mini action); `0x491386` is `ZSmallTalkCtrl` ('busy'). None faults for a mini animation started with (slot, 0,
  0, 1). READ.
- **An action that starts during the climb**: `0x869e10` has an `int3` when an action is current (`0x869e1c`),
  so every starter stops the current action first; the mini animation's End `0x6fb600` stops its channel
  (`0x63e600` -> `0x4ff500(channel, 1)`: the queue is thrown away). The climb's events 105 / 6 therefore never
  reach another action's handler. READ.
- **The natural end** (frame 51): `0x50af7f ..` vtable +0x22c (`0x86a420`: the clip's sound), state 4, queue freed;
  after the loop the report `0x7cc140` -> `0x8f0df0` -> dispatcher slot 7 `0x5d0260` -> `0x42b7f0` (answers byte
  +0x24 = 1 with endWithClip) -> `0x595b70` -> End (`Stop` returns for a channel that is not in state 1 or 3,
  `0x63e609 .. 0x63e617`) -> delete; then the movement object's vtable +0x4c. Nothing of it reads +0xc. READ. As
  the worker says: no stock run stands behind this path.
- **`[player+0x979]`** (set by `0x74c040` at the start): ten sites write 1 there, two a register, and the weapon
  update `0x6615b0` clears it (`0x661bcb`). The weapon code's own, as the worker says. MEASURED (`disp.py`).
- **Events of other channels**: finding M1.

## 4. Findings

### MUST

- **M1. 'Nothing else reaches a mini animation' is wrong as written: it is handed the clip events of EVERY
  subscribed channel of its player, not only of its own.** READ: the hand-out calls the entry's handler with
  `this` = the channel's owner `[channel+0x30]` (`0x8b68e1 .. 0x8b6915`); `0x60c370` passes the channel on to the
  owner's vtable +0x21c (`0x60c3be`); the dispatcher's slot 4 gives it to whatever action is current
  (`0x7c6c83 .. 0x7c6ca0`); slot 11 strips it to (clip, record) (`0x8b76e0`); nowhere is the channel compared with
  the action's own `[action+0x20]`. Case 5 then looks the channel up BY THE EVENT'S CLIP (`0x63709b`,
  `0x5a6ec0`) and goes on to the null object. So an id-5 event of another clip that plays on him while the mini
  animation is current faults at the same address - with a `started` line that says `none the game acts on`.
  **Closed for this build, by reading and counting** - which is why it does not block the run:
  - only an ACTION's start subscribes a player's channel: of the 23 call sites of `0x7f60e0`, twenty are in slot
    2 (the start) of nineteen `ZFFAction*` classes (ReleaseHumanShieldPvPShield, LooseHumanShield, GrabWeapon,
    PickupItem, ReleaseHumanShieldPvPCarrier, StruggleHumanShield, NoReloadHumanShield, StressBreaker,
    ReleaseHumanShield, ShootHumanShield, MiniAnim, CoopAirlockComplete, ChangeWeapon, KickDoor,
    HideItemOnPickup, Generic, CloseCombat twice, MiniAct, ShootHumanShieldPvP) and three in routines of the
    NPC acting states (`0x40a6b0`,
    `0x468640`, `0x6aa7b0`, called from `ZAnimTransition`, `ZActingAnim`, `ZLoopAnimState`,
    `ZInterpolationTransitionState`, `ZStandState`, `ZWounded` / `ZDownNotDeadNPC@CPPScript`; REASONED: not a
    player's). MEASURED (`callers.py`);
  - the hook starts only with no action current (`klq_refuse`), and the mini animation's own Play stops every
    playing channel of the full-body class and drops its queue (`0x4da283 .. 0x4da2be`: flag bit 0, state 1 or 3,
    class bit 15, `0x4ff500(channel, 1)`). READ. In the dump no other channel has a queue;
  - a channel of the OTHER class would survive that Play. In `z_climb3`'s `.ANM` the 872 clips of that class
    (`+0x28` bit 0x10) carry, of the ids the routine acts on, only **9 (15 clips) and 10 (69)**; the 330 clips
    with id 5 are all full-body. In the 21 stock files: 9 (344), 10 (1,424), 20 (4, in L01 / L07 / L09), no 5.
    MEASURED (`evclass.py`, `evclass_all.py`);
  - ids 9 and 10 are harmless in a mini animation: `0x428d90` / `0x77ca60` call `0x7de320` - which I read: a
    pure map of the id to 0x1f .. 0x24 or -1, no memory touched - then ask slot 12 and return when it answers 0
    (`0x428db0`, `0x77ca80`). READ.
  **To do** (text only, in the files the track may change): correct `re/climb.md` section 3 ('what an action is
  handed ... Nothing else reaches a mini animation'), `re/climb_crash.md` 7 ('What reaches a mini animation ...
  is section 3's list, nothing else') and 11 (the assumption covers only one direction), and the paragraph 'WHAT
  ELSE A MINI ANIMATION IS HANDED' of `klclimb.c`'s section 0; add to the 'same crash again' key of
  `re/climb_crash.md` 10 and of K2: **a fault at kl2.exe+0x7e400 at any OTHER moment than clip frame 6 is an
  id-5 event of another channel of his - in the dump esp+0x48 is that event's clip (not the climb's) and esp+0x54
  its channel.** Without that line the next reader takes such a fault for 'the table reading is wrong'.

### SHOULD

- **S1. 'The root IS at P1 at clip frame 6.03' is given as SEEN in three files and is not shown.** The dump does
  not hold his node (`[player+4]` = `0x5d6a3430` is not in it: `node.py`), nor his proxy. The vector (-2074.45,
  200.93, -671.98) at esp+0x1ac lies in the locals of `0x50ac80`, and in THIS frame the update had not reached its
  alignment part when it faulted (the hand-out `0x50af60` comes before `0x50b084 ..`): it is what an earlier
  frame left there, next to another vector (-2070.38, 329.50, -672.02) that nobody has explained. What the dump
  does show is that the alignment was TAKEN (`[player+0xec]` = 6.0, section 1). `re/climb_crash.md` 1 and 11 say
  ASSUMED; `re/climb_crash.md` 0 ('had WORKED'), `klclimb.c` section 0 ('the root IS at P1'), and `re/climb.md`
  (the fourth-version paragraph, 6.4, K2's 'SEEN up to here', section 9) say seen. Make them agree with the
  assumption - and let the next run show it: **the `frame 6.x: aligned to P2` line should print his node's place
  at that moment** (one `klq_node` read, as the 'started' line has it). It is the cheapest answer to 'did the
  first alignment bring him to P1', and nothing after frame 6 has ever been seen.
- **S2. Make M1's closure a rule instead of a count of today.** `kl_fa_climb.check` already walks the `.ANM`: FAIL
  (or NOTE) when a clip of the other body class (`+0x28` bit 0x10) carries an id of `GENERIC_ACTS` that is not
  one of the read-harmless ones (9, 10, 24 .. 35) - today 0 such clips. Optional in the hook: at the start and
  in `klq_follow`, another channel of his in state 1 or 3 with `[channel+0x34]` not 0 gets a line with its clip
  (Log=2); it costs 16 reads a frame.
- **S3. `klq_code` proves slots 12 and 13 of the mini animation, not the way to them.** The claim 'an event goes
  to `0x637060`' also rests on slot 11 = `0x8b76e0` (vtable `0xbb4f0c` +0x2c), the dispatcher's slot 4 =
  `0x7c6c80` (`0xba38d8` +0x10) and the player's vtable +0x21c = `0x9290f0` (`0xbb45f4` +0x21c). Three more
  `klh_rd32` compares; all three hold in build 0490 (READ).
- **S4. Say in K2's set-up what the run will be.** I agree with the worker's reading of the log: the last script
  line before the crash is `goto (-2075, -965) reached`, no line of the next goto follows, and +0x460 stood at z
  -751 - so the keys of that goto were most likely still down when the climb started. The gate measures the
  node's displacement (ticks 62 ms apart: the stand began at the first tick after `at the foot`, the start came 8
  ticks after it - the log's 499 ms), so a man running on the spot against the wall 'stands'. That is the gate as
  written, not a fault of it; but the rerun is K2b unless the lead's script lets go of W. For the lead, not for
  this track's files.

### NOTE

- N1. A third routine queues clip events, `0x812a50` (events of ONE id; its only caller `0x409170` asks for id
  500 with the handler `0x5b5550`: the clip's sound). Not in the account; it changes nothing - the queue in the
  dump holds exactly the two `0x60c370` entries.
- N2. Read by me and no longer 'not read': `0x7de320` (M1). Still not read by anybody: the cases for ids 11, 20,
  21, 42, 48 .. 51, 53 (`0x70dc00`, `0x7afc20`, `0x4fe5c0`, `0x87a8d0`, ...). The hook refuses them all; of them
  only id 20 exists in a clip of the other class, in three campaign levels.
- N3. `0x4a75d0` has 105 call sites (the worker's number). My split: 96 pass the id as a constant (1 .. 45; 8 ask
  for 5, 15 for 6), 9 pass a register (all in NPC acting states and their kin: `0x53bf00`, `0x69d390`, `0x6aa7b0`,
  `0x8a6280`). The worker has 90 / 15 and 14 for id 6. Either way no site asks for 105 by a constant.
- N4. `kl_fa_climb.py apply` on a first-form build ends in an uncaught `ValueError` (a traceback, exit 1). The
  text is right and nothing is written; a `sys.exit` with the same text would read better.
- N5. The 'likeliest failure' (a channel of his that ends): unchanged, as the worker says. In the dump his other
  channels are free, three of them with the full-body bit and the clips they last played; none has a queue.
- N6. For the lead, outside this track's files: `<work>\build\klhook\test_climb1` with `z_climb\M03` or
  `z_climb2\M03` is the crashing pair and still lies there; `CLAUDE.md` still calls `klclimb.c` 'NOT WIRED' and
  names `<work>/build/z_climb/M03`; the sample `klhook\KLHook.ini` has no `[Climb]` section at all (the keys are
  only in `klclimb.c`'s comment). The hooks in `G:\kl_scratch\f3` were built with another session's uncommitted
  `klescort.c` of 10:45, which has changed since: build the one to install from the tree.

## 5. What is still not shown

- That the game does nothing at event 105 and at event 6 in a mini animation: READ by two readers now, never run.
- Everything after clip frame 6: the second alignment, the hand-over, the natural end with endWithClip = 1 (no
  stock run behind it), where he stands.
- That the first alignment brought him to P1 (S1).
- That nothing subscribes a channel of a PLAYER besides an action's start (M1: REASONED from the callers' classes).
- Channels 13 .. 15 of his at the crash (not in the dump).
