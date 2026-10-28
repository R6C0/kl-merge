# Retomoto lift doors: why they stop open, what closes them (2026-10-28, offline RE)

Marks: READ = disassembled from kl2.exe (base 0x400000) or read from the DM09 F06_Main.zip; GUESS = not established.
Data read: `<DD>\KLExpansion\Maps\DM09\F06_Main.zip` (.prp via kl_fa.load, .gms/.buf via kl_scene.read).

## 1. The leaf stops because of a LAST FRAME, and the clip is longer than the played range
READ. The ZMatPosAnim leaf (vtable 0xba8f3c, ctor 0x8ff4b0, size 0xe0) owns an inline play head P at leaf+0x34
(ctor 0x472330; setter 0x572300). P layout: +0 start ms, +4 rate (int-converted, 25 here), +8 loop byte, +0xc clip (the node's
KEYS chunk), +0x10 FIRST frame (float), +0x14 LAST frame (float), +0x18 current position. So leaf +0x44/+0x48/+0x4c = first/last/current.
- `0x78f190(P, f)` sets first = f clamped into the clip range [clip+4 .. clip+8]; `0x505550(P, l)` sets last, same clamp.
- Leaf update, vtable slot 0x7e95e0 (runs per tick while [leaf+0x99]): `if [leaf+0xd0]: 78f190(first)`; `if [leaf+0xd4]: 505550(last)`
  (a 0 means "do not override"); then `0x422c50` evaluates the head.
- `0x422c50` (READ): position in 1/1024 frames = first*1024 + elapsed_ms*rate (the constant 0xb39f70 is -1024.0, so `sub ebp,eax` adds).
  Not looping ([P+8]==0): when position >= last*1024 it sets "finished", clamps to last and holds (0x422d6b..0x422d8b). THAT is the hold.
  Reverse play exists: the head runs backwards when last < first (0x422c7e: fcompp of [P+0x10],[P+0x14], reverse flag set when last < first),
  then position = first*1024 - elapsed*rate and it holds at last.
- Frame unit seen by the probe: the KEYS chunk step is 5 (see 2), 0x422e08 does `fidiv [clip block+0xc]`, so the probe's "frame 15" = 75/5.
  The leaves therefore reached the proxy's LAST FRAME 75 and held; they were not cut off early.

## 2. The clip is a full open-then-close cycle, 160 frames; the proxy plays only 0..75
READ (door KEYS in the .gms raw block, `SYEK`, 0x30: 33 keys, 0, last 160, step 5). DrExt_A/B and DrInt_A/B of M09_A (nodes 1803/1804/1808/1809)
and of M09_B (13440/13441/13444/13445) all carry the SAME chunk. Position table (z offset per key, DrExt_A):
`0, -0.3, -1.8, -5, -10.8, -18.9, -28.8, -39.7, -51, -61.9, -71.8, -80, -85.5, -88.5, -89.8, -90, -90, -89.8, -88.7, -85.7, -80, -70.8, -59, -45.8, -32.5, -20.4, -10.8, -5, -2.3, -0.8, -0.1, 0, 0, 0`
(DrExt_B mirrors it with +; DrInt_A/B are the same curve one key later). Fully open at keys 15/16 = frames 75..80, back at 0 by key 31 = frame ~155.
Key spacing is uniform 5 frames = GUESS from the smooth symmetric curve (the per-frame index tables were not decoded). 25 fps (leaf fields 50.0/25.0)
and rate 25: frames 0..75 = 3.0 s, matching the probe (z 909 -> 819 in 3 s). Frames ~80..160 are the CLOSING half.

## 3. How the proxy sets the range
READ, handler 0x7ed520 (`thiscall`, 2 stack args, `ret 8`):
- returns silently if [proxy+0x30] (collected leaf count) is 0, or if the low word of arg1 is neither [proxy+0x268] (own message id, .prp field 6
  'AITrigger') nor word [0x1689640] ('Activate').
- posts the same message to every target in the list at proxy+0x244 (.prp field 5, `[]` here) through vtable +0x50/+0x60 -> [target+0x124].
- for each leaf: `[leaf+0xd0] = [proxy+0x23c]` (field 1, first = 0), `[leaf+0xd4] = [proxy+0x240]` (field 2, last = 75),
  `78f190(leaf+0x34, first)`, `505550(leaf+0x34, last)`, then `0x59dce0(leaf)`.
- `0x59dce0`: `[leaf+0x99]=1`, start ms (P+0) = game ms [[0xdd2640]+0x48], `0x6b32b0(leaf,0)`, posts message id [0x1538c58], and
  tail-calls vtable +0x64. So every accepted message RESTARTS the clock; there is no continue.
- Proxy field map (READ vs the .prp lists): f1 = +0x23c first, f2 = +0x240 last, f3 = leaf list (inline array at +0x34), f4 = +0x238, f5 = +0x244 forward list,
  f6 = +0x268 message, f7 = ? (0).

## 4. (1) Does any data path close the doors? NO.
Read in the DM09 .prp:
- Open proxies: `AI_Players!Enemies!070_Elevators!AnimProxy_OpenEscapeElevator` (node 7858) and `Mercenaries!VideoProxy!MatPosAnimProxy` (17205), both
  `[0, 0, 75, <4 leaves>, 0, [], 'AITrigger', 0]`.
- Their only sender: `TriggerBox_OpenExitElevator` (7857; f10 = 10? the log says fires once; eTGS_AllInside, MERCONLY) lists them plus the ding/open audio
  geom activators, `Enemies!020_Street!Timer`, a flanking behaviour. `TriggerBox_1_LeaveElevator` (17204) targets only `Squad_InFront\Regroup`,
  `020_Street!Timer`, `GeomDeactivator_DriveInVan`. `TriggerBox_PreLastTrigger` targets squads.
- Nothing else names the proxies or the leaves (scanned every non-MatPosAnim controller for the proxy, trigger and leaf paths). The only other
  references are the group `RelayMessageList ['Activate','Activate',[leaf A, leaf B],0.0]` nodes (Ext_A_01..05, Int_A_03..05 of M09_A; M09_B ones),
  which nobody sends to (kl_doorfix points the proxies at the leaves, not the groups). Audio nodes: ElevatorDing, ElevatorOpen; no "close" sound.
- The leaves' own MatPosAnim `'Activate'` (message 'Activate', loop 0): a direct 'Activate' to a leaf would play the whole clip (open AND close) with
  no proxy range = GUESS (leaf message handler not read; P.last default from 0x572300 not read).
- No proxy has a range above 75. Stock Dog Days uses a separate proxy per range on one clip: F07 van `AnimProxy_RearDoors_Open [0,0,10,..,'AITrigger']`,
  `AnimProxy_RearDoors_Close [0,24,33,..,'Activate_Exit']` with a RelayMessage beside it (READ in the DM09 zip, nodes 24963/24964).
So the campaign's 0..75 range is the opening half only, the trigger fires once, and the closing frames 75..160 are never requested.

## 5. (2) Minimal change to close them after the car leaves
Both need the SAME mechanism: a second request with first >= 75 and last = 160, i.e. a restart that plays the tail of the clip.
No continuation is needed: the pose at frame 75 equals the held pose (-89.8..-90), so restarting at 75 is seamless (GUESS only for sub-frame
alignment).

A. Data (stock-like, no code). Per car (tower node 7858 list, lobby node 17205 list):
   1. new MatPosAnimProxy node, fields `[0, 75, 160, <same 4 leaves>, 0, [], 'Activate_Exit', 0]` (like F07 `RearDoors_Close`; clone node 7858/17205,
      edit f1/f2/f6 with kl_fa.edit; 160 is clamped to the clip by 0x505550 anyway, so 165 is harmless).
   2. a `RelayMessageList ['AITrigger','Activate_Exit',[new proxy], delay]` node (field layout as the group relays; delay unit = seconds is a GUESS)
      appended to TriggerBox_OpenExitElevator's target list (tower) / fired by the lobby box, so the close comes `delay` s after the open
      (open takes 3 s; delay ~ 12-15 s leaves boarding time). Or send 'Activate_Exit' from a box the car-leaving event already uses.
   Risk: a fixed delay can shut the door on a slow human; the ride has CarWait 6 s + CarFallback, so 10+ s after the box is safe.
B. kljoin.c re-fire (no data change): after the ride jump (or after CarStall/CarFallback), for each lift proxy P:
   `*(DWORD*)(P+0x23c) = 75; *(DWORD*)(P+0x240) = 160;` then call the handler `0x7ed520` thiscall with arg1 low word = word [P+0x268]
   (klprobe.c line 152 already reads it) and the second arg 0 (second arg meaning not read = GUESS; klprobe wraps the same slot, copy its call).
   That rewrites [leaf+0xd0/0xd4], the heads' first/last, restarts the clock and sets [leaf+0x99]=1. The proxy pointer is what klprobe already finds
   (init slot 14 / handler wrap). Restore +0x23c/+0x240 to 0/75 afterwards if the box could fire again (it fires once, so optional).
   Cheaper variant without the proxy: for each of the 4 leaves write `[leaf+0xd0]=75 [leaf+0xd4]=160`, call `0x59dce0(leaf)` (thiscall, no args).
   Reverse alternative: first=75, last=1 (not 0: a 0 in +0xd4 is skipped by the tick) plays 75 -> 1 backwards, which is the same pose sequence as the
   opening in reverse (a slow start, not the authored closing curve); prefer 75 -> 160.

## 6. Not checked / next
- Live check of A or B with the leaf probe: expect [ctl+0x4c] to climb 15 -> 32 (frame 160/5) and z back to 909/999.
- 0x1689640 and [0x1538c58] are the 'Activate' and a start event id by name only (GUESS).
- DrInt_B's second MatPosAnim (flags 1,..,1; probably a loop/at-load) was not decoded.
- The M09_A shaft doors (Elevators_101 groups 01..05) are other nodes; only the escape pair is driven.
