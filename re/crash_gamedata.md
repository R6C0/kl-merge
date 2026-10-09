# Milestone B crash: "jump into ZFFGameData+0x3e3c" at Buffering 99 % (kl2.exe)

2026-10-09, agent b-static. Offline reading only (kl2.exe + dumps + built levels); nothing was
run by me. "ESTABLISHED" = read in the disassembly or in a dump; "INFERRED" = not proven.
Dumps used: `kl2_490_crash_2026_10_9T0_10_59C0`, `T0_13_52C0`, `T0_33_7C0` (the classic form),
`T0_37_51C0` (the same bug caught one step earlier), `T0_41_58C0` (the NEXT crash, section 8).
The game's .mdmp hold the stack only; `KLHook_N.dmp` hold .data but not the heap objects.

## 0. Answer in five lines

1. It is not a wrong jump. `0x8af460` is a Steam CEG thunk and it resolves correctly, to the
   **level-start save-state writer `0x65a4d0`** (ESTABLISHED, frame on the stack).
2. That function calls `Save(stream)` (`push esi; call [vtbl+0x54]`) on every event in a global
   table (`0xe09e38`). Events enter the table in their constructor; **the table has no
   "unregister"** (ESTABLISHED).
3. An event that was destroyed still sits in the table. Its vtable pointer is then
   `ZSerializable`'s (`0xb8fb30`, stamped last by the destructor `0x4cdbc0`), where "+0x54" happens
   to be `0x66b570` = a bare `ret`: the pushed argument stays on the stack, 4 bytes per dead event
   (ESTABLISHED). Nine dead events = 0x24 bytes; the writer's `pop edi / pop esi / pop ecx / ret`
   then all read the argument -> eip = esi = edi = ecx = the save object. If the freed memory was
   reused meanwhile, the call itself goes wild instead (dump `T0_37_51C0`, return address 0x65a5a0).
4. The nine dead events were the nine `OnlineSpeakTrigger` of Dead Men's AI_Enemies! / Civilians!:
   `ZOnlineSpeakTrigger` init (slot 13, `0x4eae60`) looks its line up in the level's sound bank
   (`0x828fa0`) and, when it is not there, deletes itself (`jmp [vtbl+0x78]`, `0x8da110`)
   (ESTABLISHED in code; that these nine are the ones was seen live by the live agent, see
   `kl_graft.mute_speech`). My own first guess from the count 9 (FlankingBehaviourRout, also
   exactly nine and never used by a stock level) was WRONG - section 6.
5. Same trap, other classes (section 4): anything that registers in its constructor and can delete
   itself in init. In the M01 graft: `OnlineMoneyContainer` (1). Check before every build.

## 1. The call chain (ESTABLISHED)

`ZFFGameData` vtable `0xbbee6c`: slot 5 `0x76c8c0` (reset; clears both tables through `0x451c30`),
slot 10 `0x705200` (scene start), slot 13 `0x4bca90` (update), slot 15 `0x530e60` / slot 16
`0x77aaf0` (register a save participant), slot 19 `0x4dc750`, slot 21 `0x66b570`.
`[0xdd265c]` = the ZFFGameData object.

### 1.1 `0x8af460` / `0x45d600`: CEG, and it works
    0x8af460  push ecx / mov eax,0x45d600 / call eax / pop ecx / jmp eax
`0x45d600` builds a context (`0x4ea2c0`), runs 23 rounds of `0x6633d0` over self-relative tables
(`0xb42d90`, `0xb453c8`, `0xb89b28`, `0xb7be30`), then `0x7890e0`, `0x4e5a20`, `0x879fd0`, and returns
`esi + ebx` with `ebx = (0xb27cb4 + [0xb27cb4]) - [0xb6cdc4]` (`[0xb6cdc4]` = 0x400000, the image
base): Valve CEG's "compute the address of the protected function" stub. Only two users exist:
`0x8af462` and `0x6ac7e0`. The protected function has no direct caller and no pointer to it in the
image. Its identity comes from the crash stack: the frame under the return address 0x4bccda is
exactly the prologue of `0x65a4d0` (`push ecx / push esi / push edi`, local := 0xb1e538):

    01b4f5cc  004bccda   return into ZFFGameData update
    01b4f5c8  00b1e538   written by 0x65a4da
    01b4f5c4  1acc66d0   saved esi = ZFFGameData (= save object 0x1acca50c - 0x3e3c)
    01b4f5c0  1acc7c58   saved edi = gamedata + 0x1588
    01b4f59c..01b4f5bc   NINE x 1acca50c   <- arguments nobody removed
    01b4f598  0065a648   return address of the last call 0x65a4d0 makes (listener loop)

and dump `T0_37_51C0` has `0x65a5a0` (the instruction after `call [vtbl+0x54]` in 0x65a4d0) directly
above 0x4bccda. Nothing level-dependent happens in the CEG part; stock levels take the same path.

### 1.2 `0x65a4d0(this = gamedata + 0x3e3c)`: write the save state
`gamedata+0x3e3c` is the save stream object (0xa70 bytes; `0xe0e640` = "current save object").
1. `0x54d560`, clear `0xe0e64c/50`, `[this+0xa69] = 1`, `inc [0xe0e644]` (registering is refused
   from here on), `0x6ba760`, `0x68a810`
2. table 1 `0xe0de38`, count `[0xe0e638]`, max 0x200: `push 0x7b; call 0x4af2a0` (marker),
   **`push esi; call [obj vtbl+0x44]`**, `0x461750`
3. table 2 `0xe09e38`, count `[0xe0e63c]`, max 0x1000: marker, **`push esi; call [obj vtbl+0x54]`**
4. `push esi; call [gamedata vtbl+0x4c]`, `push esi; call 0x475560`
5. `[0xe0e640] = esi`; 17 listeners at `0xe0f6fc` (count `0xe0f6f8`): `call [vtbl+0]`, no argument
6. `pop edi / [esi+0xa69] = 0 / pop esi / pop ecx / ret`
The loader counterpart is `0x5d5d80` (table 1 slots +0x4c and +0x48, table 2 slot +0x58).
Every one of these callees must remove its own argument (`ret 4`).

### 1.3 Who is in the tables
- Table 1 (geometry), entered through gamedata slot 15: ZFFActor (constructor), ZOnScreenDisplay2
  (constructor), ZFFPlayer / ZAnimatedVehicle / ZRopeLnkObj / ZSNDOBJ (vtable slot 82), ZHeli /
  ZHFlow* (slot 83).
- Table 2 (events = controllers), entered through gamedata slot 16 from 88 sites. Two kinds:
  - in the CONSTRUCTOR (dangerous, see 4): ZTriggerBase (so TriggerBox2, OnlineSpeakTrigger
    and the other classes built on it), ZRandomTrigger, ZBaseBehaviourRout (all ...BehaviourRout),
    ZOnlineMoneyContainer, ZOnlineMoneyCtrl, ZSoundLimiterFade, ZPlayAudio, ZPlayMusic,
    ZPlayerAction, ZPlayerMonitor, ZActorMonitor, ZActorHealer, ZKillBox, ZGateGroup, ZCoopGate,
    ZRoomGate, ZElevator, ZWeaponFilter, ZWoundedFilter, ZKickDoorController/Monitor,
    ZVehicleSpawnGroup, ZCivilianVehicleSpawnGroup, ZMatPosAnimProxy, ZDistanceRumbleCam,
    ZEndOfLevelTrigger, ZFAMissionBriefingTrigger, CFFCoverList, CLookActivate, ZFusionSquad ...
  - in init (vtable slot 13..16, only once the object is known good): CCheckInside,
    ZPostFilterBoxEvent, ZAnimSequence, ZAIDWrapper, ZHealthMonitor, ZConditionCounter,
    ZShotActivate / ZSmashActivate / ZActivateGeom / ZDeactivateGeom / ZStealthArea,
    ZOnline*Trigger, ZOnlineEsc*, ZMercSquad, ZLevelBound, ZCoopInvisibleWall ...
- Registration is bounds-checked (int3 at 0x809f77 / 0x8269b7); the only writers are the two
  appends and the clear. KLHook_2.dmp (run B1 of the graft, 39 s): 94 and 1228 entries, 17
  listeners - far from the limits, no overflow.

### 1.4 Why a dead event unbalances the stack
- Of the 413 classes deriving from ZEventBase, 412 have a `+0x54` function that ends `ret 4` (the
  413th, ZWarnBehaviourRout, forwards to `[this+0x48]->vtbl+0x2c`; it is in no level here); all 151
  classes deriving from ZGEOM have a `+0x44` function that ends `ret 4` (walked every RTTI vtable,
  following tail jumps; slots 0..33 of the event hierarchy agree on their argument sizes
  everywhere). A live, correctly typed object cannot cause the imbalance.
- Event destructor chain: class dtor -> ... -> `0x4cdbc0` (ZEventBase: detaches from its node via
  node vtbl+0x140, three list removals) which ends `mov [esi], 0xb8fb30` = ZSerializable's vtable.
  That vtable has 12 slots; "+0x54" lies in the next vtable and is `0x66b570` = `ret`.
  (For table 1 the same accident gives `0x6faab0`, which removes 8 bytes: the imbalance would go
  the other way.)
- So: dead event, memory not reused yet -> 4 silent bytes; memory reused -> a call through
  whatever lies there (`T0_37_51C0`: object 0x530d4420, first dword 0x530d42b0 = heap, target
  0x07c51124 = heap; loop index edi = 2).

## 2. The path to the call - nothing level-specific (ESTABLISHED)

`0x4bca90` (update) before 0x4bccd5: a timer at +0x1588 against game time `[0xdd2640]+0x48`;
`[0x156b348]` -> `0x746630`; `0x5be7f0`; `[this+0x15ac]+0x177c` -> `0x69fdb0` (the chain of the earlier
ZHavokCarScript crash); if `[0x168e598]+0x5c == 4` an early save (first call site, 0x4bcb83);
`[this+0x15c0]` -> `0x425f50`; the object at +0x4cf0 with timers +0x4cf4 / +0x4cf8; timer +0x4d20;
then **`if ([this+0x48ac]) { save([this+0x48ac]); [this+0x48ac] = 0; }`** - unconditional.
`0x705200` (slot 10, scene start) sets `[this+0x48ac] = this+0x3e3c` unless `[0xdd2640]+0xb44 != 0`
or the scene name (scene vtbl+0x18) matches "KaneAndLynch." / "AttractMode." in `0x7472b0` (then
`0x8b5f60(2)` instead). It also sets +0x8b4 to 2 or 8 and calls slot 0 of the objects in the list
+0x4d08..+0x4d0c. No settings object, game mode, hero count, spawn point, escape object or
level bound is read on the way: every level started this way takes the checkpoint on its first
update. What differs between levels is only the content of the two tables.

## 3. The nine: `OnlineSpeakTrigger` whose line is not in the bank (ESTABLISHED in code)

`ZOnlineSpeakTrigger` (vtable `0xbc98fc`; ZTriggerBox2 -> ZTriggerBase, whose constructor
`0x881180` registers), slot 13 `0x4eae60`:

    buf = alloc(0x204); [this+0x7c] = buf
    if (0x828fa0(scene[+0x94] /*sound database*/, [this+0x70]+0xc /*line name*/, buf) == 0) {
        free(buf); [this+0x7c] = 0;  jmp [vtbl+0x78]      // 0x8da110: delete this
    }
    ... jmp 0x750350                                       // ZTriggerBox2 init (registers again)

The graft keeps S's (F07's) .SND, so no Dead Men line exists in it; M01_FA_A has nine such
triggers (AI_Enemies!*\FBI-Agents_01, Civilians!*\...). Stock levels: the line is always in their
own bank. `kl_graft.mute_speech` (live agent) now removes them and verify() refuses a build that
has one; the run of 01:40 got past the checkpoint (its crash stack no longer holds 0x4bccda but
0x5c7170, the next call of the frame - section 8).

## 4. The same trap elsewhere - check these before a build

Hazard = registers in the constructor AND has a "delete myself" exit later. Found by scanning
every event vtable function for a call through `[vtbl+0x78]` on itself (a LOWER BOUND: deletes
done by helpers or by other objects are not found this way):

| class (controller) | init | deletes itself when | in the M01 graft |
|---|---|---|---|
| ZOnlineSpeakTrigger | 0x4eae60 | line not in the level's .SND | 9 (now removed) |
| ZOnlineMoneyContainer | 0x837000 | `[this+0x30] == 0` or `[this+0x30]->vtbl+0x14() == 0` (its first reference does not resolve) | 1: `...\M01FAA_Ins_Diner_101a\PC1000_M01_CashRegister_01\CashRegister` (on a ZSTDOBJ; its `Money_Attachroot` / `Drawer_Attachroot` paths do resolve in the joined .prp, so INFERRED safe) |
| ZHeliFlyBehaviourRout | 0x815aa0 (slot 14) | not read | 0 |
| ZVehicleMoveOnRoadBehaviourRout | 0x4628c0 (slot 14) | not read | 0 |
| ZVehicleFireOnRoadBehaviourRout | 0x5eb2f0 (slot 14) | not read | 0 |

Safe by construction (read: they test first and register afterwards, in init): CCheckInside
(0x50c4b0: deletes itself when the reference at +0x30 does not resolve), ZPostFilterBoxEvent
(0x716100). Register in init and also have a delete exit, order NOT read: ZHealthMonitor
(0x776510), ZPhysicsBasedAnimated (0x5daf70).
Any OTHER way an event dies between load and the first update has the same effect: a node deleted
with its controllers, CTimeOutDelete, a script that deletes a controller. Stock levels evidently
never do it before the checkpoint.

## 5. Inputs compared (graft = F07 systems + M01_FA_A, 14,993 nodes, 3,265 controllers)

Controller-on-class combinations of the graft that occur in none of F01..F09, L01, L05:
NoCoverBox on ZBoxPrimitive 21, RelayMessage on ZSTDOBJ 19, PassengerAnimPos on ZSTDOBJ 16,
ShotActivate on ZHavokRigidBody 13, **FlankingBehaviourRout on ZGROUP 9**, OnlineVehicleOnSpline 4,
VehicleMoveBehaviourRout 4, SmashActivate on ZSTDOBJ 4, Audio_PlaySound on ZParticleEmitter 3,
IdleWalkPathRout 2, **MatPosAnim / ParamAnim on ZCAMERA 2 + 2** (`M01_Backdrop_A_00\AnimatedRumbleCamera`),
OnlineTriggerBox 1, CheckInsideByType 1, DistanceRumbleCam on ZTrafficFlow 1,
OnlineMoneyContainer on ZSTDOBJ 1, ZSetZDefine on ZLIST 1.
Save participants of the graft: table 1 - ZSNDOBJ 168, ZFFActor 16, ZFFPlayer 16,
ZOnScreenDisplay2 2 (F09: 80 / 54 / 16 / 2 + ZAnimatedVehicle 3). Table 2 by controller name -
TriggerBox2 307, OnlineMoneyCtrl 306, ShotActivate 140, SoundLimiterFade 29, PostFilterBox 18,
FlankingBehaviourRout 9, TriggerBox 8, HuntBehaviourRout 5, OnlineGamePlayTrigger 5,
VehicleMoveBehaviourRout 4, SmashActivate 4, DefendBehaviourRout 3, TriggerDelay 3, AIDWrapper 3,
IdleWalkPathRout 2, OnlineExitLevelTrigger 2, and one each of OnlineEscHavokCar, ActivateGeom,
DeactivateGeom, DistanceRumbleCam, OnlineMoneyContainer, FFCoverList, PlayerAction, CheckVisible
(+ 9 OnlineSpeakTrigger before they were removed). All of them come from the Dead Men side;
F07's systems contribute none at load.
Dead Men squads are `ZGROUP @ZSquadScript` with behaviour children like stock ones
(`AI_Enemies!BossFlank_03`: FlankingBehaviour @FlankingBehaviourRout + two flank boxes,
`FBI-Agents_01\Ground` ZFFActor @ZSoldier); stock squads use Defend / RunToCover / SquadModifier.

## 6. Candidates as I ranked them, and how it came out

1. (my first pick, WRONG) the nine FlankingBehaviourRout: count 9, class unused by every stock
   level. Read afterwards: its functions are ordinary (save = base `0x70efb0`, `ret 4`; init
   `0x6bb0f0` allocates a ZFlankingBehaviourGoal; nothing deletes it). Not the cause.
2. (RIGHT, found live by the other agent, then read here) the nine OnlineSpeakTrigger, section 3.
3. Still open as risks of the same kind: section 4's table; and whatever else destroys an event
   before the first update.
Lesson for next time: a count match is not evidence; the object's vtable is. See 7.

## 7. Cheapest tests / tools for this class of bug

- Live, exact, 20 lines in KLHook (not my file): at `0x4bccd5` (ecx = save object) walk
  `0xe09e38[0 .. [0xe0e63c])` and log every index whose first dword is not a vtable of the image
  with a `.text` pointer at +0x54 that ends `ret 4` - in practice: first dword == `0xb8fb30` or
  outside 0xb00000..0xcd7000. The index maps to a controller by load order (constructor-registering
  controllers in .prp node order; `OnlineSpeakTrigger` etc. count at construction).
- Better: log in the event destructor `0x4cdbc0` (ecx = event, `[ecx]` = its class vtable at that
  moment is already ZEventBase's, so log the caller's return addresses and `[ecx+0x24]` = owner
  node) whenever `[0xe0e644] == 0` and the scene is loaded. Names the class and the node at once.
- Robust engine-side fix (makes every future map immune): in the same hook remove `ecx` from
  table 2 (and a geometry destructor's `this` from table 1) - the "unregister" the engine lacks.
  ASSUMPTION to check: nothing else keeps an index into the tables (the loader `0x5d5d80` walks
  them in order against the saved stream, so removal must happen before the checkpoint is
  written, which it does when done in the destructor).
- Offline pre-flight (belongs in kl_graft.verify / debug/check.py): for every controller of a
  class in section 4's table, evaluate its delete condition. OnlineSpeakTrigger is done
  (`mute_speech`); OnlineMoneyContainer: its first reference list must resolve to an existing node.

## 8. What else the stacks hold

- No entity or scene name: the frames between the update and the crash are the save writer's
  only. Above them: `0x5c7168` (in 0x5c7100, the per-frame call of gamedata slot 13) < `0x87aa7c`
  (0x87a930, frame function) < `0x584073` < `0x7549bf` < `0x926aa6` < `0x8016ca` < `0x4c36af` <
  `0x476d35` (WinMain, with the command line `"main.ini" -dx10 -o DefaultScene=Locations/F01/
  F01_Main.gms -o AutoExit=120` and `...\Kane & Lynch 2 - Dog Days\KL2.ini` on the stack).
  `0x408022` in every dump is a stale local, not a frame.
- edx = 0xe0f740 = `0xe0f6fc + 4*17`: the end of the listener loop, i.e. the writer ran to its
  last instruction before the bad `ret`.
- NEXT crash (run 01:40, dump `T0_41_58C0`, kl2+0x41e714, reading 0x28f47650), first reading only:
  same frame, one call later (`0x5c7170`): `0x70dab0` -> `0x7471c0` (ZLIST_ActionController update)
  -> `0x617590` (ZBaseConRout slot 27) -> ZBaseCamera slot 25 `0x5aaf90` -> ZMatPosAnim slot 25
  `0x51a120` -> `0x7b9590` -> `0x422c50` -> `0x7afb00` -> `0x81e6f0(keys, index)`: a bit-packed key
  read with element width 0x52 bits and index 0x13b4f (80,719) at time 3.125 - the key block is
  not what the reader expects. A MatPosAnim on a camera: the graft's only ones are the two on
  `ROOT\M01_Backdrop_A_00\AnimatedRumbleCamera` (with two ParamAnim; never on a ZCAMERA in stock).
  INFERRED suspect: that node's key data (KEYS tracks / .buf offsets). Cheapest test: build with
  `--m-drop M01_Backdrop_A_00` or drop the four controllers of node `AnimatedRumbleCamera`.
