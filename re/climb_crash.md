# The climb's first live start: the crash at kl2.exe+0x7e400

2026-10-11, track F3. OFFLINE work on a LIVE result: run `K2c_DM03_wall_hp` (10:02, the lead's), hook TEST
`<work>\build\klhook\test_climb1` (`klclimb.c` third version, wired), level `<work>\build\z_climb\M03`, a scripted
player with tenfold health who walked the bank and came to the foot of edge 2. Kept:
`<work>\research\crash_1011_climb\` (`K2c_DM03_wall_hp.log`, `KLHook_1.dmp` = the first-chance fault, `KLHook_2.dmp`).
Status words as in `re/climb.md`: **seen** = in the live log or the dump; **read** = in the disassembly at the address
given (`python debug\dasm.py <address>`); **measured** = counted on files, the command is named; **ASSUMED**; **not
established**. Nothing of the FIX has run in the game.

**Fix round, 2026-10-11, after the adversarial review `re/climb_crash_review.md`** (verdict: accept with fixes; one
MUST, text only; four SHOULDs; the next live run not blocked). Every finding was re-checked against `kl2.exe` and
the dump before anything was changed; **none is refuted**. What was done is section 12; the corrected places are
marked **(R)**. In one line each: the account's 'nothing else reaches a mini animation' was wrong - an action is
handed the clip events of EVERY subscribed channel of its player (M1; now a rule in the tool's check and in the
hook); 'the root is at P1' was never seen (S1; the hook's next `aligned to P2` line prints his node); `klq_code`
compares the way to the event routine too (S3); the first live start was most likely one with forward held (S4,
for the lead: section 8 and `re/climb.md` 7).

## 0. In short

- **Cause.** The game's animation update hands a clip's events to the current action, and `ZFFActionMiniAnim` has
  `ZFFActionGeneric`'s event routine (`0x637060`) as its own: at event id 5 that routine aligns the player to the
  place of the action's object `[action+0xc]` (`0x6370e7`: `mov ecx, [esi+0xc]` / `call 0x47e400`, no test) - a
  mini animation has none (its constructor writes 0 there, `0x6b2987`). Dead Men's climb clips mark their first
  alignment with exactly event id 5, at frame 6: 0.24 s into the clip the game read `[0 + 0x60]`.
- **Not the hook's calls**: its alignment had returned 14 frames earlier and the game had TAKEN it (`[player+0xe8]`
  = 0, `[player+0xec]` = 6.0 in the dump: a blend from clip frame 0 to frame 6). **(R)** That it brought him to P1
  is ASSUMED, not seen (section 1; this line said 'had WORKED'). It is the game's own flaw (a mini animation + a
  clip with event 5), which no stock clip walks into.
- **(R) One more way into the same fault** (the review's M1): the action is handed the clip events of every
  subscribed channel of the player, not only of its own - an id-5 event of ANOTHER clip that plays on him during
  the climb would fault at the same address. Closed for this build by reading and counting (section 7), and since
  the fix round a rule: `kl_fa_climb.py check` FAILs a build with such a clip in the body class the mini
  animation's Play does not stop, and the hook refuses (or calls off) a climb beside such a channel.
- **Fix.** In the level: the PLAYERS' climb clips carry event id **105** where Dead Men's have 5
  (`tools/kl_fa_climb.py`; one dword per clip, 7 clips); the routine does nothing at 105 and nothing at 6. In the
  hook: `klclimb.c` reads the first alignment's frame from id 105 and **refuses** to play a clip with any event id
  the game's routine acts on (asked of the game's own switch tables) - before the start, and once more after it.
- **Builds**: `<work>\build\z_climb3\M03` (= `z_cover3\M03` + the step in its new form). **`z_climb\M03` and
  `z_climb2\M03` are of the first form: they crash a hook that plays them** (the new hook refuses them with a line).

## 1. The run (seen)

    10:02:36.525 climb: node (-2079, 201, -763), +0x460 (-2079, 220, -763): 138 from the face of edge 2, ... speed 454, facing 1.00, 0 full-body channel(s) of his play
    10:02:36.713 climb: at the foot of edge 2: node (-2074, 201, -673), +0x460 (-2077, 220, -751), proxy (-2074, 201, -673), 48 from the face, speed 483, facing 1.00; the top is 202.5 over his feet = /Movement/Climb/Up/High, id 2505; 0 full-body channel(s) of his play as he arrives
    10:02:37.212 climb: edge 2: started /Movement/Climb/Up/High (slot 2505) from node (-2074, 201, -666), +0x460 (-2078, 220, -751), 41 from the face: action 0150d1c4, clip 78168c98 of 52 frames (flags 10c0), events 5 at 6 and 6 at 20; aligned to (-2074, 201, -672) in 6 frames
    10:02:37.212 climb: collision off (the climb starts; count 0 -> 1)
    10:02:37.452 CRASH c0000005 at kl2.exe+07e400 (0047e400)   reading address 00000060
                 eax=00000006 ebx=37542a0c ecx=00000000 edx=01b4f2e4 esi=0150d1c4 edi=37542a0c ebp=3779e3c0 esp=01b4f2d4

What that run settles of `re/climb.md`'s open points (all **seen**):

| question of K1 / K2 | answer |
|---|---|
| is the node's world place his place? | yes: it follows him at 450 - 600 a second, and at rest **the proxy reads the same place** to the unit |
| the floats at +0x460 | NOT his place at a wall: they stopped at z -751 (the navigation mesh's edge), 78 behind him; their height is the mesh's 220, the node's is 201 (the collision floor 200). The file takes place and height from the node (its rule: the node when that is within 40 of `Floor=`) - right |
| the sign of 'facing' | right: 1.00 while he ran straight at the face |
| the slot | found, id 2505 |
| does StartMiniAnim keep its action for this body and weapon (a wardrobe body, a rifle, heist stage 2, $550,000) | yes: action `0x0150d1c4` (the action pool's objects lie inside kl2.exe's image; `0x15151c0` is the pool) with vtable `0xbb4f0c`, kind 0x23, this player, slot 2505, a playing channel |
| the clip | 52 frames, record flags 0x10c0, events 5 at 6 and 6 at 20: Dead Men's `Up_High` (or `Up_High_No_Weapon`: both have these numbers) |
| does `AlignTo` take the hook's alignment | yes: the game's own record of it is in the dump - `[player+0xe8]` = 0, `[player+0xec]` = 6.0, the blend's start and target frame (`0x50b304 .. 0x50b331`: the correction is blended in by (frame - `+0xe8`) / (`+0xec` - `+0xe8`)). **(R) Whether it brought him to P1 is ASSUMED, not seen** - see below the table |
| the collision switch | count 0 -> 1 |
| other channels of his during the climb | none plays at clip frame 6: of the 13 of his 16 channels the dump holds, the climb's is in state 3, five are free (state 0, id -1) with the clips they last played - two of them of the other body class -, seven were never used; **(R)** all twelve have a queue pointer `[channel+0x34]` of 0. Channels 13 .. 15 are not in the dump |

**(R) Where he was at clip frame 6 is not in the dump** (the review's S1; re-read for the fix round, scratch
`dmp.py`). His node (`[player+4]` = `0x5d6a3430`) is not among the dump's memory, nor is his proxy. What the first
form of this account took for 'the aligned root' is the vector (-2074.45, 200.93, -671.98) at esp+0x1ac - P1 to the
unit (P1 = (x, his height, -672.0)). It lies in the locals of the animation update `0x50ac80` (its frame is
esp+0xbc .. esp+0x1ff: `sub esp, 0x134` and four pushes under the return address at esp+0x200), and the update
writes that part of its locals only in its ALIGNMENT part, which comes after the channel loop (`0x50b084 ..`; the
writes at `0x50b38c .. 0x50b45b`). This frame faulted inside the loop, at the hand-out `0x50af60`. **So an earlier
frame left it there**; whether it is the place the game was told or the place his root was at then cannot be read
off it (one frame before the target the two are under a unit apart: 0.9 at clip frame 5.6 by the clip's root keys,
`kl_fa_climb.root_keys`). Next to it, at esp+0x1a0, lies (-2070.38, 329.50, -672.02): not explained.
What the game's own record adds: from the target frame on the update runs another branch (`0x50b11a .. 0x50b131`:
`[player+0xe8]` := the old target, `[player+0xec]` := the channel's last frame, the correction whole). The dump has
0 and 6.0 there - that branch had not run, so **in every frame the game finished the blend was still short of its
target** (the frame that reached clip frame 6.03 is the one that faulted, before its alignment part). 'The first
alignment brought him to P1' is therefore the reading of `0x50b0f6 ..`, not something seen; the hook's `frame 6.x:
aligned to P2` line prints his node's place and its distance from P1 from now on (section 10).

Nothing after clip frame 6 has been seen: no second alignment, no hand-over, no end.

## 2. The stack, frame by frame (dump `KLHook_1.dmp`; read)

`python debug\dump.py <dump>` lists every kl2.exe return address it finds on the stack; four of the log's sixteen
'callers' are not frames but leftovers inside the locals of two routines (marked). The real chain, innermost first:

| at esp+ | return address | the routine that was called | what it is |
|---|---|---|---|
| 0x000 | `0x6370f4` | **`0x47e400`**, called at `0x6370ef` | 'the place of this object' (`this` in ecx): `cmp dword [ecx+0x60], 0` / `[ecx+0x58]` a handle, else `[[ecx+0x24]+4]` a node -> its world place (`0x7b3020`). Its ONLY caller is `0x6370ef`. **ecx = 0: the fault** |
| (0x02c, 0x03c) | `0x446200`, `0x818623` | - | not frames: old values inside the 0x34 bytes of locals of `0x637060` |
| 0x044 | `0x8b76f3` | **`0x637060`**, called at `0x8b76f1` through the action's vtable +0x34 | `ZFFActionGeneric`'s 'a clip event' (vtable slot 13; `ZFFActionMiniAnim`'s slot 13 is the same routine). `(clip, event record)`. Section 3 |
| 0x050 | `0x7c6ca2` | `0x8b76e0`, called at `0x7c6ca0` through the action's vtable +0x2c | slot 11 of `ZFFActionGeneric` / `MiniAnim` / `MiniAct`: hands `([channel], event record)` to slot 13 |
| 0x064 | `0x60c3c0` | `0x9290f0` (ZFFPlayer vtable +0x21c), called at `0x60c3be`; it is `mov ecx, [ecx+0x19c]` / `jmp [vtable+0x10]` = **the action dispatcher's slot 4, `0x7c6c80`** | 'a clip event for the player': no current action -> nothing; else the action's slot 11, and the action is ended if that answers 0 |
| 0x080 | `0x8b6917` | `0x60c370`, called at `0x8b6915` (the queue entry's handler) | the subscriber every action's start registers (`0x7f60e0`): finds the event record by its index (`0x89f480`), its text (none here: `0xffff`), and calls the owner's vtable +0x21c |
| 0x0b8 | `0x50af65` | `0x8b67d0`, called at `0x50af60` with ecx = the channel | 'hand out the channel's events that have come due': the queue `[channel+0x34]`, entries {time, handler, user value}; `[channel+0x2c]` = the frame it was last done for |
| (0x154, 0x158) | `0x55c7ba`, `0x6934ad` | - | not frames: inside the locals of `0x50ac80` |
| 0x200 | `0x74f043` | **`0x50ac80`**, called at `0x74f041` (vtable +0x2e8) | the animation update: every playing channel is advanced by the frame's step, then its events are handed out, then its end is tested |
| 0x288 | `0x58085b` | `0x74efc0` (ZPlayer's frame), called from `0x57fae0` (ZFFPlayer's frame, vtable +0x15c) | `re/climb.md` 3, 'who moves him' |

What lies between them, and in the registers (all **seen** in the dump):

- `esp+0x84 .. 0x90`, the handler's arguments: the channel `0x37542a0c`, **the event's time 6.0**, the channel's frame
  **6.03**, the entry's user value 0 = event index 0.
- `esp+0x54 .. 0x5c`, slot 11's arguments: the channel, the event record `0x79553a94`, the default text `0xb34850`.
- `esp+0x48`, `0x4c`, the event routine's two arguments: the clip `0x78168c98`, and **20** - the frame of event 6,
  which `0x6370cc` has written over its second argument. `eax = 6` is the frame of event 5 (`0x6370d0`, the result is
  not used). So the routine stood in **case 5**, past both lookups, at its first use of the object.
- `esi = 0x0150d1c4`: the action. Its bytes: vtable `0xbb4f0c` (`ZFFActionMiniAnim`), +4 = 0x23, +8 = the player
  `0x3779e3c0`, **+0xc = 0**, +0x10 = 0, +0x14 = 0, +0x18 = 0x9c9 = 2505, +0x1c = 0 (no align object), +0x20 = the
  channel, +0x24 = 1, +0x25 = 1 (ends with its clip). The dispatcher `0x3779e560` (vtable `0xba38d8`) has it at +4.
- The channel `0x37542a0c`: clip `0x78168c98`, frame 6.03, from 0 to 51, 25 a second, flags `0x8603` (plays, aligned,
  moves bone 0x39, full body), id 0x27d, +0x2c = 6.03, +0x30 = the player, +0x34 = the queue `0x0153af6c`
  (`ZPoolAllocLinkSortRefTab`) with **two entries: {index 0, handler `0x60c370`, time 6.0, flags 0} and {index 1,
  handler `0x60c370`, time 20.0, flags 0}**.
- The clip record: 52 frames, 25 a second, 2 events, flags 0x10c0, net root (-0.9, 172.0, -101.2). The event
  records `0x79553a94`: **{id 5, frame 6, text 0xffff}, {id 6, frame 20, text 0xffff}**, the clip's data right
  behind them.

The same with the repo's tools: `python debug\dump.py <dump>`; `python debug\mem.py <dump> 150d1c4 37542a0c
78168c98 79553a94 153afa0`; `python debug\dasm.py 637060 200`, `8b67d0 1a0`, `60c370 60`, `7c6c80 40`, `8b76e0 30`.

**(R) How a dump of 'the other way in' would differ** (section 7, the review's M1): the same fault address and
the same chain, but `esp+0x48` (the event's clip) is NOT the climb's clip, `esp+0x54` (the event's channel) is NOT
the action's own `[esi+0x20]`, and the time at `esp+0x88` is a frame of that other clip.

## 3. The machinery (read)

**Who gets a clip's events.** Nobody, unless the channel was subscribed. `0x4011e0(channel, handler, x)` walks the
clip's event table (`[[0x1546f6c]+0x10] + [clip+0x10]`, `[clip+6]` entries {u32 id, u16 frame, u16 text}) and queues
every event whose frame lies inside the channel's from .. to (`0x821600`: {time = the frame, handler, user = the
event's index, flags 0}; the queue object is made at the first entry). Two wrappers pass a handler: `0x7f60e0`
(handler `0x60c370`: 23 call sites, among them **the mini animation's start `0x76d22e`**, the generic action's
`0x789a8a` and the mini cutscene act's `0x8e8e87`) and `0x425280` (handler `0x5edc40`, 5 call sites). `Play` alone
subscribes nothing; the vault's start `0x6a27e0` is not among the 23; the NPC link mover `0x4a5160` is in neither
list.
**(R) The 23 and the 5, by who they are** (counted in the fix round with the class and slot of each caller's
routine, scratch `jt.py` / `who3.py`; the review's count, the same): 20 of the 23 are in vtable slot 2 - the start
- of 19 `ZFFAction*` classes (ReleaseHumanShieldPvPShield, LooseHumanShield, GrabWeapon, PickupItem,
ReleaseHumanShieldPvPCarrier, StruggleHumanShield, NoReloadHumanShield, StressBreaker, ReleaseHumanShield,
ShootHumanShield, **MiniAnim**, CoopAirlockComplete, ChangeWeapon, KickDoor, HideItemOnPickup, Generic, CloseCombat
twice, MiniAct, ShootHumanShieldPvP); the other 3 are in `0x40a6b0`, `0x468640`, `0x6aa7b0`, routines called from
slot 0 / 2 of `ZAnimTransition`, `ZActingAnim`, `ZLoopAnimState`, `ZInterpolationTransitionState`, `ZStandState`
and slot 12 of `ZWounded` / `ZDownNotDeadNPC@CPPScript` (the review takes these for the NPCs' acting states:
REASONED, not read). So **for a player only an action's start subscribes a channel** - as far as that reasoning
holds. The handler of `0x425280`, `0x5edc40`, does not go to the action: it sends the owner a message (vtable
+0x120; read). A third routine queues events as well, `0x812a50` (the review's N1): the events of ONE id; its
only caller is the sound starter `0x409170` (id 500, handler `0x5b5550`; `0x409170` has 10 call sites in 6
routines: Play, the animation update, `ZFFActionReloadItem`'s start, `ZFFActionThrow`'s slot 4, `ZPlayer`'s slot
392, `ZActor`'s slot 400). So a channel's queue pointer `[channel+0x34]` not being 0 does not say WHICH of the
three made the queue (no clip of the bank build has an event with id 500, measured: there the third makes none).

**When.** The animation update `0x50ac80`, per playing channel (state 1 or 3): advance, then `0x8b67d0` (at
`0x50af60`, its only caller): every queued entry whose time has come is taken out and its handler called; a handler
that answers 0 is an `int3` (`0x8b693a`). A stopped channel hands nothing out any more: `Stop` (`0x63e600`) calls
`0x4ff500(channel, 1)`, which calls only the entries with flag bit 0 (none of `0x4011e0`'s) and throws the queue away.

**To whom.** `0x60c370` -> the owner's vtable +0x21c = for a `ZFFPlayer` `0x9290f0` = the dispatcher's slot 4
`0x7c6c80` -> the current action's slot 11. The dispatcher (`0xba38d8`) has eight slots and they are all an action
is ever handed: 1 start (action slot 2), 2 -> action slot 4, 3 -> action slot 3, **4 -> slot 11 (a clip event)**,
5 / 6 stop / end (slot 5, then delete), **7 -> slot 10 (a channel ended)**.
**(R) Whose clip event? Any subscribed channel's of that player** (the review's M1; every step read again in the
fix round). The hand-out calls the entry's handler with `this` = the channel's OWNER (`0x8b68e1`: `mov eax,
[esi+0x30]`; `0x8b690b .. 0x8b6915`: `add ecx, eax` / `push esi` / `call edx`) and the channel as its first
argument; `0x60c370` passes that channel on to the owner's vtable +0x21c (`0x60c3bb .. 0x60c3be`); the dispatcher's
slot 4 hands it to whatever action is current (`0x7c6c83`: `cmp [esi+4], 0`; `0x7c6c8d .. 0x7c6ca0`); slot 11 takes
the clip out of it and calls slot 13 with (clip, record) (`0x8b76ea .. 0x8b76f1`). **Nowhere is the channel
compared with the action's own `[action+0x20]`.** Case 5 then looks for 'the channel that plays this clip' with the
EVENT's clip (`0x63709b` -> `0x5a6ec0`: the first of his 16 channels in a state other than 0, 2, 4 whose clip it
is - it finds the event's own channel) and goes on to `[action+0xc]`. The first form of this account said 'a
mini animation is handed its clip's events': it is handed the events of every clip that plays on him subscribed.

**`0x637060`, the event routine** (`ZFFActionGeneric` slot 13 and `ZFFActionMiniAnim` slot 13; `ZFFActionMiniAct`
calls it from its own slot 13). `this->vtable[0x30](id)` first - slot 12 `0x721060`, 'the action's object': `mov
eax, [ecx+0xc]` / `test` / 0 without one, so harmless. Then the switch `0x637077`: `lea ecx, [id-5]` / `cmp ecx,
0x30` / `ja 0x6372d3`; inside 5 .. 53 the byte table `0x637314` and the 13 targets `0x6372e0`. `0x6372d3` is `mov
al, 1` / `ret 8`. Decoded (scratch `jt.py`):

| ids | goes to | what |
|---|---|---|
| **5** | `0x637093` | the channel that plays the clip (`0x5a6ec0`); the frames of events 6 and 5 (`0x4a75d0`; without event 6 the channel's last frame); **`[this+0xc]->0x47e400(&pos)`, `[this+0xc]->0x86f150(&rot)`**, then `player->vtable[0x208]` = `AlignTo(rot, pos, frame of event 6 - the channel's frame)`. 'From event 5 on, be at the action's object by event 6.' The object is used with no test |
| 9, 24 .. 29 | `0x637135` | `0x428d90(this, id)`: `0x7de320(id)` first - **(R)** read: a pure map of ids 9 .. 35 to 0x1f .. 0x24 or -1, no memory touched - then slot 12 for the object, and `je` when there is none (`0x428db0 / 0x428db2`) |
| 10, 30 .. 35 | `0x637147` | `0x77ca60(this, id)`: the same shape (`je` at `0x77ca82`) |
| 11; 42 | `0x637159`; `0x637184` | **(R)** read: `0x70dc00` / `0x87a8d0`: slot 12, `je` when there is no object (`0x70dc0e`, `0x87a8de`); with one, it is sent the message `Activate` / `AITrigger` |
| 21 | `0x63716a` | **(R)** read: `0x4fe5c0` (slot 12, `je` at `0x4fe5cb`; with an object its vtable +0x54), then `0x77ca60(this, 10)` |
| 20 | `0x637195` | **(R)** read as far as this: `0x7afc20` asks the PLAYER for an object first (`0x86a130`: his vtable +0x4d4, else +0x4d0) and acts on that when there is one; only without one does it ask slot 12 (and return). **Not quiet in a mini animation** |
| 48; 49; 50; 51; 53 | `0x6371a6`; `0x6371e3`; `0x637202`; `0x637290`; `0x6372b6` | **(R)** read as far as this: none uses `[action+0xc]`; 48 sends a message to the object the player's node hangs on (after `0x432a20`), 49 / 51 / 53 call into the game data object `[0xdd265c]`, 50 pushes the intro menus (`EidosPresentsMenu` ..). **They act whatever the action is** |
| **6**, 7, 8, 12 .. 19, 22, 23, 36 .. 41, 43 .. 47, 52, and every id outside 5 .. 53 | `0x6372d3` | nothing: `mov al, 1` |

**`[action+0xc]`.** In a `ZFFActionGeneric` (kind 0x20, 0x14 bytes) it is the object the action is about, the third
argument of its constructor `0x70ca90` (called at `0x62fc1a`): its start `0x789a60` and its End `0x852810` use it
without a test as well. `ZFFActionMiniAnim`'s constructor `0x6b2970` (one caller: StartMiniAnim, `0x5ea3b5`) writes
**0** at +0xc and +0x10 (`0x6b2987`, `0x6b298a`); the argument 'x' goes to +0x14, the align object to +0x1c. No
routine of its vtable but slots 12 and 13 reads +0xc. `ZFFActionMiniAct`'s constructor `0x5c7420` writes 0 there
too.

## 4. The other candidates, and what excludes each

| candidate (the task's list) | excluded by |
|---|---|
| the end of the hook's 'aligned to ... in 6 frames' | `AlignTo` returned in the tick of the start, 14 game frames before the fault; the blend of a correction is done inside the animation update at `0x50b0f6 ..`, not on this stack - the fault came in the channel loop, before that part of this frame; and the game had taken the alignment (`[player+0xec]` = 6.0). **(R)** 'It worked: the root is at P1' stood here: assumed, not seen (section 1) |
| the 'action' the log prints is a static the hook mistook | it is the action: vtable `0xbb4f0c`, kind 0x23, this player, slot 2505, this channel (section 2). The pool hands out objects inside the image; the game's own dispatcher holds the same address |
| the clip's event 6 at frame 20 | the event's time on the stack is 6.0, the channel stands at 6.03, the entry's index is 0; the second entry (20.0) is still queued. And id 6 goes to `0x6372d3` |
| 0.24 s = frame 14 at 60 a second | the channel's own clock: 25 frames a second (`+0x10`), frame 6.03 |
| the arrival at speed 483 | he stood when it started: 7 units in the 499 ms between coming into reach and the start (section 8). The routine that faulted is reached by the clip's event whatever he did before |
| the wardrobe body / which set | the slot resolved, the action was kept, the clip is Dead Men's `Up_High`: the path does not depend on the body |
| the rifle, heist stage 2, the money bag | none of them is read on the path from `0x50af60` to `0x47e400` |
| clip record +0x2C (non-zero in 8 of the 12 added clips, `re/climb.md` 9) | 0x2330 in this clip; no routine of the chain reads it |
| a channel of his that ended (the second review's 'likeliest failure') | slot 10 is not on the stack; no other channel of his plays (section 1) |

## 5. How the game itself gets by

- **`ZFFActionMiniAct`** (the mini cutscene's act) has the same hole (+0xc = 0) and a slot 13 of its own, `0x68ac60`:
  `cmp eax, 5` / `je` -> `mov al, 1` (`0x68ac6d`); ids 0x27 and 0x7d3 it handles itself; only the rest goes to
  `0x637060`. Its authors knew id 5 must not reach the generic routine without an object.
- **The vault** (`ZFFActionVaultOver`): its start subscribes nothing and its slot 11 is `mov al, 1` (`0x557da0`); the
  clips it plays (`Cover_Vault_*_1M / 2M`) have no events (measured on the build).
- **The stagger** `0x5022c0`, the one caller of StartMiniAnim in ordinary play: its slot is the name
  `/Special_moves/Cover_From_Explosives` (`0x89cb31`), which **none of the 21 stock Dog Days `.ANM` files has**
  (measured, scratch `stock_stagger.py`) - so in the retail game its mini animation is over before it plays anything
  (`0x76d1f5`). `re/climb.md` took the stagger for a stock precedent of 'a mini animation on a walking player': the
  CALL is, the clip never plays.
- **The mini cutscene's move task** `0x607950` (`ZMiniPlayerMoveTask`, campaign scripts): the only stock maker of a
  mini animation that plays a clip, with endWithClip = 0. Which clips, and whether any has event 5: **not
  established** (it would fault the same way).
- Event id 5 is everywhere in Dog Days' own data - 4,166 clip blocks of the 21 stock files (cover enters, leaves,
  flips, throws ...; measured, scratch `ev.py`) - and harmless there: those clips are played by code that asks for
  the frame of 5 / 6 itself (`0x4a75d0`: 8 call sites ask for 5, **(R)** 15 for 6) or under a generic action that
  has its object. Event ids in stock data: 0 .. 53, 2000, 2001 (Dog Days); 0 .. 45, 2000, 2001, 2003 (Dead Men).
  **(R)** By body class in the bank build's `.ANM` (measured, scratch `evmax.py`): 325 FULL-BODY clips carry id 5
  (330 events); of the 872 clips of the other class (record +0x28 bit 0x10) none does - their ids are 3, 7, 8, 9,
  10, 12, 22, 23, 43.

So: Dog Days still means by event 5 what Dead Men's climb means by it - 'start aligning here, be there at event
6' - but does it INSIDE the generic action, to the action's own object. A mini animation was never meant to play
such a clip.

## 6. The fix, what it costs, what was not taken

**Taken: the events' ids in the level + a refusal in the hook.**

- `tools/kl_fa_climb.py` (`refoot`, `EV_FOOT_DD = 105`, `GENERIC_ACTS`; `merge`, `check`): in the clips the
  PLAYERS' three lists name - 7 clips: `Up_High`, `Up_High_No_Weapon`, `Up_Medium`, `Up_Medium_Pistol`,
  `Up_Medium_No_Weapon`, `Sprint_Low`, `Sprint_Low_No_Weapon` - the one event with id 5 is written with id 105;
  frame, event 6 and every byte of the clip's data stay. 105 is outside the switch's range (nothing but slot 12's
  tested read and `mov al, 1`), in no stock file of either game, and asked for by no call site of `0x4a75d0` (of
  its 105 sites 96 pass a constant, 1 .. 45, and 9 a register - those in `0x53bf00`, `0x69d390`, `0x6aa7b0`,
  `0x8a6280`, animation-state routines; **(R)** counted again in the fix round: the first count here, 90 / 15, had
  taken six constants for registers, the review's N3). The proofs now say: each added list equals its Dead
  Men source with 105 read as 5, exactly that entry differs, no players' clip has an id of `GENERIC_ACTS`.
  `check` FAILs a players' set whose climb clip carries such an id (on `z_climb\M03`: `RESULT (kl_fa_climb): FAIL
  (2 FAIL, 1 NOTE)`), and `merge` refuses to 'complete' a build of the first form.
  One players' clip, `Sprint_Low_No_Weapon`, is also in the NPC sets' Low lists (Dead Men's `Police` names it for
  its pistol / unarmed conditions) and has the new id there too. That changes nothing for an NPC: the link mover
  `0x4a5160` plays with `Play` alone, asks its clip for event 6 by number (`0x4a53aa`) and subscribes nothing. The
  five `*_NPC` clips keep 5 and 6.
- `klhook/klclimb.c`, fourth version: `KLQ_EV_FOOT = 105`; `klq_ev_acts(id)` = the game's own switch, read from its
  two tables (`klq_code` compares the routine's head, the switch, the 'nothing' target, slot 12 and the mini
  animation's vtable entries 12 / 13 first); `klq_clip` reports the first event the game would act on; `klq_climb`
  asks **before the start** for the clip `0x59d550` gives (the routine the start itself calls first, `0x76d1ea`) -
  such a clip: `NOT climbed: the clip ... has event id 5 at frame 6 ... NOTHING WAS STARTED` - and again for the
  channel's own clip after the start (stopped in the same tick: the game hands events out in its animation update,
  which has not run in between; a stop throws the queue away without calling anybody, section 3). The 'started'
  line prints the two ids, his speed and how long he stood.
- **(R) The fix round** (section 12): `tools/kl_fa_climb.py` - `GENERIC_QUIET` and the rule of `check` on the clips
  of the other body class; a refused `apply` ends in one line, not a traceback. `klhook/klclimb.c` - `klq_ev_to`,
  `klq_clip5`, `klq_others` (his other channels with an event queue: before the start, right after it, every
  frame of the climb), three more compares in `klq_code`, his node in the `aligned to P2` line, his movement kind
  and the count of those channels in the `started` line.

**What it costs.** The level differs from Dead Men's data in 7 dwords (5 -> 105). The level and the hook must
match: the THIRD version of the hook with the new level finds no event 5 and aligns once, to the top at event 6
(the NPC mover's way: no fault, not Dead Men's picture); the FOURTH version with a first-form level refuses. One
more draw from the game's generator per try (`0x59d550`; Arcade shares it with nobody). The alignment itself is
the hook's, as before - the game's own 'event 5' alignment is not used.

**Not taken.**

- *The clips merged without any event, the two frames written into `[Climb]`*: the frames differ per CLIP inside
  one class (Low: 6 / 16 with a rifle, 3 / 15 unarmed), a section is an edge; the hook would need a table by clip
  name. The id change keeps the number in the clip.
- *Giving the routine its object* (a fake object at `[action+0xc]`): a data write into the game's action and a
  made-up scene object, for an alignment the hook does itself (and the game's would aim at the object's place by
  event 6 only, without the foot alignment).
- *Another action class*: `ZFFActionMiniAct` swallows id 5, but it is the mini cutscene's (its start `0x8e8d00`
  wants a task and a script); the vault plays its own clips.
- *Dropping the channel's queue from the hook right after the start* (`0x4ff500(channel, 0)`, the routine the
  update calls at a channel's end): one more game call, no level change, every clip safe - and a call in a state
  the game never makes it in (on a channel that plays). The level fix makes the game do only what it does anyway.

## 7. The rest of the clip's life (read; none of it seen yet)

What reaches a mini animation between its start and its end is section 3's list - the dispatcher's slots - and
nothing else. **(R) But 'a clip event' in that list is the event of ANY subscribed channel of the player, not only
of the mini animation's own** (section 3, 'whose clip event'; the review's M1 - the first form of this section
had only the climb clip's two events in its table):

| when (High) | what | what it needs | fourth version |
|---|---|---|---|
| the start | `0x5ea340`: `[player+0xbe0]` and `[player+0xdbc]` flag bytes cleared (`0x8b7410`, `0x4c1a70`), StopAction, the pool, the constructor, StartAction -> `0x76d1d0`: `0x59d550`, the weapon lowered (`0x74c040`), `Play`, `0x7f60e0` (the events queued) | tested by `klq_refuse` | SEEN: it ran |
| every frame | the animation update: the channel advances, the alignment's correction is blended, the root delta moves the node (`re/climb.md` 3) | - | SEEN for 14 frames: no fault. **(R)** Where the root was: not in the dump (section 1) |
| frame 6 (3 for `Sprint_Low_No_Weapon`) | **event 105** -> `0x637060`: slot 12 (0), the switch's `ja` -> `mov al, 1` | nothing | read; it was id 5 that faulted |
| the hook's next tick | `AlignTo(P2, to the frame of event 6)` on the same channel | the channel is still the one `0x760120` finds | as before (the game took the first call of the same routine) |
| frame 20 (16; 15) | **event 6** -> `0x637060`: slot 12 (0), the table -> `0x6372d3` | nothing | read |
| **(R) any frame** | **a clip event of ANOTHER channel of his that somebody subscribed** -> the same `0x637060`, with THAT event's id | for id 5: the object a mini animation has not got - the same fault, at any frame of the climb | closed by reading and counting (below); since the fix round refused / called off by the hook (`klq_others`) and FAILed by the tool's check |
| any frame | 'a channel ended' (slot 10 `0x42b7f0`): with endWithClip the action ends | - | unchanged: the likeliest way it ends early (below) |
| frame 46 | the hook's hand-over: `0x4af5b0`, `0x686600` | `klq_carry_refuse` | as before |
| frame 51 | the channel's end: `player->vtable[0x22c]` (`0x86a420`: flags on an object of `[sysif+0xb00]`, not read further; `Stop` calls it too), state 4, the queue freed (`0x4ff500(channel, 0)`), the report -> slot 10 -> End `0x6fb600` (`Stop` on a channel that has stopped: nothing) -> delete | - | as before |

Left behind by a mini animation that ends with its clip: byte `[player+0x2758]` stays 0 (the start clears it; only
the 'no clip' and 'hold the pose' paths set it) - its two readers are the mini cutscene tasks' 'am I done' tests
(`0x4061b0`, `0x607a2d`), nothing of ordinary play. The weapon flag `[player+0x979]` set by `0x74c040`: the weapon
code's own business (`0x6615b0`), not read further.

**(R) The other channels' events: why they do not fault THIS build, and what makes a rule of it** (the review's
M1 and S2; each point read or counted again in the fix round):

- *Who can have a subscribed channel.* For a player only an action's start subscribes one (section 3: 20 of the 23
  call sites; the three others are animation-state routines, taken for the NPCs' - reasoned). The hook starts only
  with no action current (`klq_refuse`), and an action that starts later must end the mini animation first:
  `0x869e10` has an `int3` for 'an action is current' (`0x869e1c`), so every starter stops the current one, and
  the mini animation's End stops its channel, whose queue is thrown away (`0x63e600` -> `0x4ff500(channel, 1)`).
- *What the start's own Play does.* `Play(clip, 1)` stops every channel that plays (state 1 or 3) and is of the new
  clip's body class, and throws its queue away without a call (`0x4da294 .. 0x4da2be`; the entries `0x4011e0`
  makes have no 'on stop' flag). The climb clips are full-body (record +0x28 = 0): **no full-body channel
  outlives the start** - and all 325 clips with id 5 in the build are full-body.
- *What plays on.* A channel of the OTHER class. The 872 clips of that class in `z_climb3\M03`'s `.ANM` carry, of
  the ids the routine acts on, only **9 (15 clips) and 10 (69)** (measured again, scratch `evclass.py`; the same
  on `z_climb\M03` and `z_climb2\M03`). At 9 and 10 the routine returns when the action has no object (section 3).
  The 21 stock Dog Days files (counted again, scratch `evstock.py`; the review's numbers): 16,448 clips of that
  class, with 9 (344 clips), 10 (1,424), 20 (4, in L01 / L07 / L09) and no 5 - so a stock level cannot fault a
  mini animation this way either, and the three campaign levels with id 20 would FAIL the tool's rule.
- *The rule in the tool* (`kl_fa_climb.check`, `GENERIC_QUIET`): a build FAILs when a clip of the other body class
  carries an id of `GENERIC_ACTS` at which the routine does not simply return for an action without an object -
  everything but 9, 10, 11, 21, 24 .. 35, 42 (all read, section 3). On the build: `PASS  the 872 clips of the
  other body class ...: of the event ids kl2 0x637060 acts on they carry only 9 (15 clips), 10 (69 clips), at which
  it returns when the action has no object ...`. Negative control (a scratch copy with ONE id 9 of such a clip
  written as 5, then as 20; scratch `neg.py`): `FAIL  1 of the 872 clips of the other body class ... id 5 in 1
  (Special_Moves/Pick_Up#Crouch_Pick_Up)` and `RESULT (kl_fa_climb): FAIL (1 FAIL, 1 NOTE)`, both times.
- *The rule in the hook* (`klq_others`, reads only): his channels other than the climb's that play and have an
  event queue (`[channel+0x34]` not 0) are counted; one whose clip has an event the routine sends to its case 5
  (or whose events cannot be read) - **before the start**, among the channels the start's Play would leave
  playing: `NOT climbed: channel N of his plays the clip X with an event queue, and that clip has event id 5 at
  frame F ...: NOTHING WAS STARTED`; **right after the start**, among all the others: the action is stopped in
  the tick of its start; **in any frame of the climb**: `... the climb is called off`, stopped and given back as
  any call-off. The `started` line ends `; N other channel(s) of his play with an event queue (mask)`, and with
  `Log=2` every change of that set during a climb is a line (by the reading none can come: such a line says the
  reading is short of something). What the hook's rule is NOT: the queue is not walked (a queue made for sound
  events, or by `0x425280`, counts too - the rule can refuse more than it must); only case 5 is refused, not the
  other ids that act (20, 48 .. 51, 53: the tool's check has those); and a channel that is subscribed and whose
  id-5 event comes due inside ONE frame of the game, between two ticks, cannot be seen in time.

**New for the record: nothing in the retail game runs a mini animation to the natural end of a clip in an FA
level** (the stagger plays nothing; the move task holds its last frame until its script stops it). The end with
endWithClip = 1 is read (`0x42b7f0` -> `0x595b70` -> `0x6fb600`), never exercised by the game itself.

**The 'likeliest failure' (a channel of his that ends early).** Unchanged in kind, narrower in fact: at clip frame
6 no other channel of his was playing, so nothing was there to run out - the weapon and face channels the reviews
feared were not running 0.24 s after the start (who stopped the two of the other body class was not read; `Play`
stops only the full-body ones). It takes a channel that STARTS during the two seconds (a hit reaction, weapon
handling, a shout). And this crash adds what both reviews and the off-game model had missed: the events are a
second way into the action besides the channel report. With ids 105 and 6 nothing comes through it from the
climb's own clip; **(R)** what can come through it from his other channels is the paragraph above.

**The off-game test** (scratch, not in the repo: `G:\kl_scratch\f3\sim\sim.c`, `sim.exe`, `sim_old.exe`, their
`*_out.txt`; the third version's test with one thing added to its model: every frame the fake animation update
hands the clip's due events to a model of `0x637060` built from the game's own two tables, and case 5 FAULTS as
the game did).
`sim_old.exe` = the THIRD version of `klclimb.c` (git HEAD, sha1 5eeedfab..): with the first build's events (5 at
6, 6 at 20) - `the model's fault: YES at clip frame 6.25, event id 5; events handed out 1`, after exactly the three
lines of the live run; with a build of today's - no fault, ONE alignment (it prints `events 5 at -1 and 6 at 20`).
`CONTROL: the third version with the first build's clip faults in the model at frame 6, as in the game`.
`sim.exe` = the fourth version: `SIM: PASS (0 failed)`, 84 expectations - A .. R, the third version's 66, with a
build of today's events (one expectation changed: with `Fallback=1` and no climb clip the mini animation's start
is no longer called at all), and S .. W: S the whole climb (both events to 'nothing', two alignments, hand-over,
UP, one look at the clip, one start); T a first-form level (refused, nothing started, nothing switched, no event
handed out); U the start plays another clip than the one looked at, with event 5 (stopped in the tick of the start,
no event handed out); V id 9 (refused), ids 22 / 23 and a clip without events (started, one alignment), an
unreadable event table and a missing clip (not started); W the speed gate (section 8).
**(R) The fix round's test** (the same scratch files, extended; `sim_old4a.exe` and `..\old4a\klclimb.c` are new):
the model has ANOTHER channel of his that plays a second clip with an event queue - its due events go to the
model's `0x637060` whenever an action is current, as section 3 reads it - and the model's Play stops the full-body
channels that play. `sim.exe`: **`SIM: PASS (0 failed)`, 101 expectations** = the 84 above, unchanged, and 17 new:
X1 such a channel of the other body class whose clip has event 5 at frame 40, present before the start (`NOT
climbed: channel 5 of his plays the clip ...`, one look at the climb's clip, no start, the collision untouched,
that event handed to nobody, no fault); X2 it appears during the climb (the set's change logged, `the climb is
called off`, `CALLED OFF by this file (another channel ...)`, one stop, given back, no fault, `BACK AT THE FOOT`);
X3 the same channel with events 9 and 10 (started, `1 other channel(s) of his play with an event queue (0020)`,
its two events go to the model's routine too, no fault, UP); X4 a FULL-BODY channel with a queue and event 5 (not
a refusal: the start's Play stops it, `0 other channel(s) ...`, none of its events handed out, UP); X5 its event
table unreadable (refused); Y the `aligned to P2` line carries his node and its distance from P1, the `started`
line his movement kind, the dry run's line the count; each of the three new compares of `klq_code` set wrong:
`the game's routines are not the ones this build knows: nobody climbs`.
`sim_old4a.exe` = the fourth version as it was BEFORE the fix round (sha1 c1644259..) in X1's scenario: it starts
the climb (`... none the game acts on`), sets the second alignment, and `the model's fault: YES at CLIMB frame
23.33, event id 5` - the other channel's event. `CONTROL: before the fix round the fourth version faults in the
model on another channel's event 5`. (`sim_old.exe`, the third version's control, still gives its three lines.)
It is a test of the file against the reading; the model's fault is this document's reading of the dump.

## 8. The speed of the arrival

The gate did what it says, and it was not what let anything through: the `at the foot` line is printed when he
comes into reach whatever his speed (483, 'as he arrives'); the stand begins at the first tick (20 a second) at
which his node moved slower than `Speed` (150), any faster tick starts it anew, and the start comes `Dwell` (400 ms)
later. Here: into reach at 36.713, started at 37.212 = 499 ms = one or two ticks of slowing + the dwell; his node
moved from z -673 to -666 in that time, 14 a second on average: **he stood**. Why he stopped 41 from the face is
**not established**, but the likely reading is that the wall itself held him: the rig's `goto` judges by the floats
at +0x460 (klauto.c, `[Auto] PosOff`), which stayed at the mesh's edge at z -751, and the script's `reached` line
for that goto never came - so W was most likely still DOWN, and 41 is about a man's radius. If so, this start was
made with forward held (K2b's condition, `re/climb.md` 7) and the next run's will be too, unless the script's foot
place is one the mesh reaches; the rig and its script are not this track's to change. The gate is unchanged; the
`started` line now says `speed S after D ms at the foot under 150`.
**(R) The review's S4, for the lead.** It reads the log the same way (the last script line before the crash is
`goto (-2075, -965) reached`, no line of the next goto follows, +0x460 stood at z -751) and reckons the gate's
ticks: the hook's watch runs at ticks 50 ms or more apart, which with a tick count that steps by 15.6 ms is every
62 ms; the stand began at the first tick after `at the foot`, the start came 8 ticks after that line = the log's
499 ms (so `Dwell=400` was 437 ms). The gate measures his NODE's displacement between two ticks: **a man who runs
on the spot against the wall 'stands'**. That is the gate as written, not a fault of it - Dead Men's own
condition is speed and the USE tap, held stick or not. But it means **the rerun of K2 with the same script is
K2b (forward held through the clip), not K2**, until `tools/kl_playtest.py`'s wall script lets go of W before the
dwell is over. Nothing in the hook can see the keys; the `started` line now also prints `movement kind K` (2 =
Stand, 3 = BaseMove: whether that tells a stand from a run against a wall is NOT known - worth a look at the next
log).

Does a running start matter? For the fault no (section 4). For the clip: by the gate there is none. A WALK under
`Speed` does start it (off-game test W: at 100 a second he is started 400 ms after coming into reach, 20 from the
face, still walking) - Dead Men allows up to 375. To the game it is the same call: `Play` replaces whatever
full-body clip plays, the first alignment takes him to the stand-off (47 from the face) in 6 frames from wherever
he is inside 15 .. 70. What that looks like from a walk was not seen.

## 9. What was built, and the checks

| | |
|---|---|
| level | `<work>\build\z_climb3\M03` = `python tools\kl_fa_climb.py apply <work>\build\z_cover3\M03 <work>\build\z_climb3\M03`; `F01_Main.zip` sha1 0698b298de54bcebd8bfb1972c0509df01f43983, 200,895,904 bytes; `.ANM` 22,202,616 -> 22,343,864 (12 clips, slot ids 2505 High, 2506 Low, 2507 Medium), only that member differs from `z_cover3\M03` |
| against the first form on the same base (`z_climb2\M03`, the lead's of 09:22) | the two `.ANM` members differ in **7 dwords, each 5 -> 105**, nothing else |
| `kl_fa_climb.py check` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)`; on `z_climb\M03` and `z_climb2\M03`: `FAIL (2 FAIL, 1 NOTE)` (the two players' sets, 7 clips each with event 5). **(R)** With the fix round's rule the PASS has one line more (`the 872 clips of the other body class ...`, section 7); the counts are the same |
| **(R)** the build after the fix round | NOT rebuilt, and it need not be: `apply` with the tool as it is now, into a scratch folder, gives the same `F01_Main.zip` (sha1 0698b298..) and the same `KLJoin.ini` (sha1 bb3fec85..); only the build's own record of its check (`climb.txt` / `climb.json`) lacks the new line. Every check of this table was run again on it after the round: the same last lines |
| `kl_impact.py` | `problems: 0 in 1 levels` |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 1 NOTE)` - the 7 FAIL of `z_cover3\M03` itself (the civilian loot-window rule; the two outputs differ in one line, the `.ANM` size). Not this step's, not fixed |
| `kl_maps.py audit` | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` |
| `kl_map_escape.py van-check` | `0 fault(s)` |
| `kl_anm.py check` (the tool, untouched) | `byte-identical: 41 of 41` |
| hook | built from the tree as it is (other sessions' uncommitted files among it): `klhook\build_auto.bat G:\kl_scratch\f3\test`, `klhook\build.bat G:\kl_scratch\f3\ship`; no warning from `klclimb.c` (one from `klhud.c`, another track's). The sha1 of both DLLs is in the track's report (a hook carries its build time) |

## 10. The next live run

Level `z_climb3\M03`, a TEST hook built from the tree, `[Climb] Enable=1 Dry=0 Log=2`, the wall script. In order:

**(R) What the run will be** (section 8): with the wall script as it was, forward is most likely still held when
the climb starts - that is K2b of `re/climb.md` 7, not K2. Either the script lets go of W first, or the result is
read as K2b's (held input may end the mini animation early: `ended at frame N ... BEFORE the hand-over`).

1. `climb: edge N: started /Movement/Climb/Up/High (slot 2505) from node ..., 4x from the face, speed S after D ms at
   the foot under 150, movement kind K: action 0150d1c4, clip ... of 52 frames (flags 10c0), **events 105 (the foot)
   at 6 and 6 (the top) at 20, none the game acts on**; aligned to (x, 201, -672) in 6 frames; **0 other channel(s)
   of his play with an event queue (0000)**`, then `collision off (... count 0 -> 1)`. **(R)** A count over 0 is
   not a fault (the mask says which channels; none of their clips has an event for the game's case 5, or the
   climb would not have been started) - but say it: in the dump of the first start there was none.
2. **`climb: edge N: frame 6.x: aligned to P2 (x, 403 or 404, -672) in 13.x frames; his node is at (x, y, z) now =
   (dx, dy, dz) from P1 (x, 201, -672.0)`** - about 0.25 s later. This line is the fix seen: the game is past the
   frame it died in. **(R) And it answers what the dump could not** (section 1): if the first alignment brought
   him to P1, the three differences are small - expected (0, 0 .. +3.5, 0 .. +0.6): the correction is whole
   from frame 6 on and the clip's own root has by then risen 1.1 at frame 6.3, 3.5 at 7.0 and gone 0.2 .. 0.6
   towards the face (measured on `Up_High`'s root keys; a tick later than frame 7 reads more: +21 at frame 8).
   A dz of +6 or more (he stood 6 nearer to the face than P1; without the correction the clip's own root goes
   another 3 towards it by frame 6) or a dy far from that means the alignment did NOT move his node as read -
   tell the lead with the line.
3. Nothing at frame 20 (event 6 goes to 'nothing'), then K2's lines as `re/climb.md` 7 has them: `frame 46.x of 51:
   HAND-OVER ...`, `over after about 2080 ms ...`, `RESULT 2 s after the end: UP`.

**The same crash again** would be `CRASH c0000005 at kl2.exe+07e400`, `reading address 00000060`, about 0.24 s after
a `started` line, with no `aligned to P2` line between. With the fourth version that needs a clip with event id 5
that got past both tests - it cannot by the reading; if the `started` line says `events 105 (the foot) at -1`, the
level is not `z_climb3` and something else is wrong. With a first-form level the expected line is `NOT climbed: the
clip ... has event id 5 at frame 6 ... NOTHING WAS STARTED`, and no crash.
**(R) The same address at ANY OTHER moment of a climb** - after the `aligned to P2` line, or anywhere but clip
frame 6 - **is not 'the table reading is wrong': it is an id-5 event of ANOTHER channel of his** (section 7, the
review's M1) that got past `klq_others` (a channel subscribed and due inside one frame of the game; or one whose
queue the hook's reading of `[channel+0x34]` missed). In the dump: `esp+0x48` is that event's clip - not the
climb's clip of the `started` line -, `esp+0x54` its channel - not the action's `[esi+0x20]` -, `esi` the mini
animation. `python debug\mem.py <dump> <esp+0x40>` shows the three; the clip's name is in the level's `.ANM`.
The hook's own lines for that case, when it sees the channel in time: `NOT climbed: channel N of his plays the clip
...` (nothing started) or `frame F: channel N of his plays the clip ...: the climb is called off`.
A fault about 0.8 s after `started`, after the `aligned to P2` line (frame 20 = event 6): the table reading of id 6
is wrong - `python debug\triage.py --keep`. A fault elsewhere in `0x637060 .. 0x6372dc`: another case of the switch.
Any other end is K2's own list (`BACK AT THE FOOT` after `ended at frame N ... BEFORE the hand-over` = a channel of
his ended or an action came: say N).

## 11. Assumed, not established, not done

- **(R)** ASSUMED: that the first alignment brought his root to P1 by clip frame 6. The vector (-2074.45, 200.93,
  -671.98) in the animation update's locals is NOT evidence of it (an earlier frame's leftover, section 1); the
  dump shows only that the game took the alignment. The next run's `aligned to P2` line prints his node.
- **(R)** ASSUMED, in ONE direction only: that nothing but the current action is told of the events of the mini
  animation's own channel (its queue held the two entries of one subscriber). The other direction is READ and is
  the review's M1: the current action is told of the events of every other subscribed channel of the player too
  (sections 3, 7). REASONED, not read (the review's): that the three callers of `0x7f60e0` outside the actions'
  starts are the NPCs' and never subscribe a player's channel - the hook's per-frame watch of his channels is
  there to show it wrong.
- **(R)** Read in the fix round, no longer 'not read': `0x7de320` and the cases for ids 11, 21 and 42 (quiet
  without an object), and how far 20 and 48 .. 53 depend on the action's object (not at all: they act anyway;
  section 3). Still not read: what `0x7afc20` (id 20) does with the object it takes from the player, and the
  callees of cases 48 .. 53. The hook refuses every id the switch acts on in the climb's own clip; in his other
  channels' clips it refuses case 5 alone, the tool's check everything that is not quiet.
- Not established: the clips of the mini cutscene's move task; who stopped his two upper-body channels before
  frame 6; the three of his 16 channels the dump does not hold; everything of the climb after frame 6; **(R)**
  whether forward was held at the start (section 8); what the vector (-2070.38, 329.50, -672.02) beside P1 in the
  update's locals is; whether `[channel+0x34]` can be 0 on a channel that is subscribed (the queue object is made
  at the first entry and freed at the stop: read; nothing else looked at).
- Not done: nothing was run in the game (the lead's); no commit; `klhook.c`, `tools/kl_playtest.py` and the other
  hook files were not touched; `z_climb\M03` and `z_climb2\M03` were left as they are (first form: do not run them
  with `Dry=0` under the third version of the hook); the hook-only alternative of section 6 was not built; **(R)**
  the hook does not walk a channel's event queue (it cannot tell an action's subscription from a queue of sound
  events).

## 12. The fix round after the review (`re/climb_crash_review.md`), finding by finding

Each finding was checked against `kl2.exe` / the dump / the files again before anything was changed (scratch, not
in the repo: `<scratchpad>\f3fix\` - `jt.py` the switch tables, the vtable entries and the call sites with the class
and slot of each caller, `who3.py`, `dmp.py` the dump's player, stack and channels, `evclass.py` / `evmax.py` /
`evstock.py` event ids by body class, `rootat.py` the clip's root, `neg.py` the negative control of the new
rule). **None is refuted.**

| finding | re-checked how | holds? | what was done |
|---|---|---|---|
| **M1** must (text): the mini animation is handed the clip events of EVERY subscribed channel of its player | `dasm.py 8b67d0`, `60c370`, `9290f0`, `7c6c80`, `8b76e0`, `637060`, `5a6ec0` (new: the lookup by the event's clip), `4da260` (Play's stop loop), `4ff500`, `869e10`; the 23 callers of `0x7f60e0` by class and slot; the build's event ids by body class | yes, every step | `re/climb.md` 3 and 9, this file's 0, 2, 3, 7, 10, 11 and `klclimb.c` section 0 corrected; the 'same crash again' key has the other-moment case with what the dump would hold. And, beyond the text: the rule in the hook (`klq_others`) |
| **S1** should: 'the root IS at P1' is not shown | the dump: node and proxy not in it; the two vectors at esp+0x1a0 / +0x1ac; `[player+0xe8]` / `+0xec`; `0x50ac80` - where its locals are, that it writes them only behind the channel loop, the two branches of the blend | yes - and the game's own record says the blend was still short of its target in every finished frame | ASSUMED everywhere it said seen (this file 0, 1, 4, 7, 11; `klclimb.c` section 0 and 3; `re/climb.md` head, 6.4, 7, 9); the `frame 6.x: aligned to P2` line prints his node and its distance from P1 |
| **S2** should: make M1's closure a rule | the count reproduced (872 clips of the other class: 9 in 15, 10 in 69; the 21 stock files: 9, 10, and 20 in three campaign levels); `0x7de320`, `0x428d90`, `0x77ca60`, `0x70dc00`, `0x4fe5c0`, `0x87a8d0`, `0x7afc20` read | yes; and the 'harmless' set is larger than the review's (11, 21, 42 too), 20 is NOT in it | `kl_fa_climb.check` FAILs a clip of the other body class with an id outside `GENERIC_QUIET` (PASS on the build, FAIL on two negative controls); the optional hook part taken further than a `Log=2` line: refusal before the start, stop after it, call-off during the climb, and the `Log=2` line for a change of the set |
| **S3** should: `klq_code` does not prove the way to slot 13 | the three entries read from the exe: `0xbb4f0c`+0x2c = `0x8b76e0`, `0xba38d8`+0x10 = `0x7c6c80`, `0xbb45f4`+0x21c = `0x9290f0` | yes | three compares added (and 'id 5 goes to `0x637093`'); the off-game test sets each wrong in turn: nobody climbs |
| **S4** should (for the lead): the rerun is K2b unless the script lets go of W | the log's last script lines; the gate's code (`now - last < 50`, the node's displacement); 499 ms = 8 ticks of 62.4 | yes; that the ticks are 62 ms apart is reckoned from two intervals of the log, not seen per tick | written into section 8, 10 and `re/climb.md` 7 (set-up); `klclimb.c`'s comment says what the gate measures; the `started` line prints his movement kind. The script is not this track's file |
| N1 a third event-queueing routine `0x812a50` | `dasm.py 812a50`, `409170`, its callers | yes | section 3; it is why the hook cannot take a queue pointer for a subscription |
| N2 `0x7de320` read; 11, 20, 21, 42, 48 .. 53 unread | read now (above) | - | section 3's table; `GENERIC_QUIET` |
| N3 the split of `0x4a75d0`'s 105 call sites is 96 / 9, 15 ask for 6 | counted again; the six sites the first count took for registers looked at one by one (constants 7, 16, 17, 22, 6, 22) | yes | sections 5 and 6, the tool's comment |
| N4 `apply` on a first-form build ends in a traceback | run: it did | yes | `main` prints `kl_fa_climb: NOT applied: <the text> - nothing was written` and exits 1 |
| N5 the 'likeliest failure' unchanged | the dump's channels (above) | yes | nothing to change |
| N6 for the lead: the crashing pair still lies in the work folder; `CLAUDE.md` says 'NOT WIRED' and names `z_climb/M03`; the sample `KLHook.ini` has no `[Climb]` section; the scratch hooks carried another session's `klescort.c` | not this track's files | - | in the track's report; the hooks were built again from the tree at the end of the round |
