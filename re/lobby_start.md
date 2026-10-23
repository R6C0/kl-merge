# What starts a hosted Fragile Alliance System Link round (static, kl2.exe 0490)

Read 2026-10-23 with tools/kl_exe + capstone. Nothing was run. FACT = read in code; GUESS = marked.
sm = [0x168e598] (ZSessionManagerMultiplayer, vtbl 0xbd1ebc). Fields: +0x54 role (2 server, 3 client), +0x5c game type
(4 = FA family), +0x64 ?, +0x70 state, +0xb8 max, +0xb9 "min" (see 0), +0x194 countdown (float), +0x1f4 byte.

## 0. What [sm+0xb9] really is
It is the lobby's TARGET size, not a floor. Two uses of the same byte:
- start gate (section 1): connected >= [b9] lets the countdown run;
- join gate 0x5067c7 (0x506780 = ZSessionHandlerServer slot 49, "a peer asks for a player slot"; ebx = peer record):
  `0x7cc240()==0` (sm state not 0x29 / 0x2d..0x2e) and `0x8e8010(peer)==0xff` (xor-coded byte at peer+0xdc, = -1 / not yet
  assigned: a NEW peer), then `if (b9 <= connected) 0x464750(1)` = REFUSE (0x464750 builds message 0x404 with a reason code and
  sends it to the peer; send failure -> 0x89e080; 0x77b0e4 uses the same sender with reason 3 for a kick), else (b9 > connected)
  fall through to 0x5067f5.. which allocates the player (0x605790, 0x6fc950, 0x7a0730, [sm+0x2c] vtbl+0x94 ...).
  So a lobby refuses joiners once it holds b9 players. Held at 2: host + 1 client fits (host counted: GUESS, see 3), a 3rd peer is refused.
  (If the joiner were already counted at 0x5067c7, a normal b9=4 lobby could never take its 4th player, so it is not counted yet: reasoning, not proof.)
- 0x739f20 (setter) clamps to [connected, 12]; the menu floors of 4 (6 in Cops & Robbers) are in the menu code only.

## 1. The start path (FACT unless noted): sm vtbl slot 27 = 0x6c49a0, every frame, dt = [esp+0x108]
State jump table 0x6c5870 / 0x6c58cc: 0xd -> 0x6c4baa, 0xe -> 0x6c4de4, 0xf -> 0x6c5063, 0x10 -> 0x6c521b, 0x11 -> 0x6c5300 (load, then 0x12).
SetState = sm vtbl +0x68. Role test 0x4b0a40 = (role==3). Authority test 0x8df480: roles 0/1 -> type==4, roles 2/3 -> role==2.
- Countdown gate (0x6c4d8e..0x6c4dd3 in state 0xd, copy 0x6c4f74..0x6c4fb6 in state 0xe): timer [sm+0x194] -= dt only while ALL hold:
  connected(0x698250) >= [b9]; byte [sm+0x1f4] != 0; map-ok flag; [sm+0x5c]==4. Otherwise timer := 15.0 (const 0xb750c0).
  - [sm+0x1f4] is set to 1 in the sm constructor (0x8c4c17) and no other byte store to +0x1f4 exists in .text: always true.
  - map-ok (0x6c4cf5..0x6c4d8c): host's level list says "available" for MP_SelectedLevel AND each of the 12 client slots (0x8fdf90)
    that has a client reports the level (0x7ca830). Stock maps: true. Slot-redirected Dead Men maps: see re/private_match_mapsync.md.
- State 0xd -> 0xe: 0x6c4c80: if timer < 0 (15 s of an unbroken gate) and connected >= [b9] -> SetState(0xe).
  So once both are in the lobby the host's own countdown is 15 s; no button needed.
- State 0xe -> 0xf (0x6c4fb6..0x6c500c): connected >= [b9] AND 0x8df480() AND handler(vtbl+0x60 = 0x7d1590) >= 0xe -> SetState(0xf),
  then 0x5abac0(connected) (handler vtbl+0x5c = store the count). 0x7d1590 = MINIMUM over all peer records of their replicated state
  byte (0x8f3620 = xor-coded byte at record+0xf8; 0xff or >= 0x2d drops the record; empty list returns 0x2f). So every client must have
  reported state >= 0xe: that is the per-player "ready". It is NOT a button: it is the client's own state machine reaching 0xe.
- State 0xf (0x6c5063): map still available (error dialog path if not), 0x6e7640, SetState(0x10) at once. State 0x10 (0x6c521b):
  waits on the object [sm+0x2c] (vtbl +0x94, +0x98 booleans, +0x120(dt) tick; GUESS: scene/world ready), then host SetState(0x11) -> load.
- The per-player "state >= 0xe" of 0x452860 / 0x5d4920 is not used by this path; 0x5d4920 is the FAQuitLobbyConfirm path.

## 2. 0x5a9920..0x5a9b5e: the host's lobby action (the "start now" button)
- Called only from 0x7dcf45: message id 0x7f in the FA lobby selector's message handler (same class as the LEFT 0x7dc4f9 / RIGHT 0x7dcb57
  row handlers; 0x81 -> 0x649a20, 0x82 -> 0x7fb0f0). What key/button sends 0x7f is NOT read (GUESS: the lobby's Ready/Start select).
- X (esi) = 2 if [sm+0x5c]==2 (0x87c980), else 4, or 6 when [0x168e59c]==2 (Cops & Robbers). For FA, X = 4. It is the menu floor.
- State 0xd, press: pick the map index (host list vtbl+0x14, or +0x18 in mode 2); unavailable -> return 2; else SetState(0xe); if
  authority also 0x48e410(1), 0x4a0650, 0x549e80. This skips the 15 s timer wait (still subject to step 5 of section 3).
- State 0xe, press (0x5a9974): needs authority AND connected >= X AND [b9] > X. Then it IS "start with whoever is here":
  n = connected; 0x739f20(n) (b9 := n), 0x6f7fb0(n,1) (max := n, published to lobby data), 0x6484d0(n) (-> 0x80ef80: replicated
  variable D+0x14c, see 4), 0x541e20(n), builds/sends an object, and SetState(0xf) DIRECTLY (skips the "all clients >= 0xe" wait).
  Else it returns 1 and does nothing. With X = 4 it cannot fire for 2 players; with b9 held at 2 (b9 > X false) it cannot fire either.

## 3. Bottom line: min held at 2, host + 1 client connected
It should start by itself, with no host button, if ALL of these hold (each cited above):
1. connected (0x698250 = used slots of the server handler's list [h+8]: [list+0xc]-[list+8]) is 2, i.e. the HOST IS COUNTED.
   Evidence: HUD status rows iterate row < 0x698250 including the local player (re/hud_menu.md); GUESS, not proven.
2. b9 on the host is still 2 when the join request is handled: the join gate refuses when b9 <= connected, so b9 must be above the count
   BEFORE the client is added (1); no LEFT/RIGHT press may have bumped it (kllobby re-holds it every 200 ms).
3. map-ok (stock FA map: yes) and +0x1f4 (always 1).
4. 15 s unbroken countdown (the timer resets to 15 whenever any term drops), then host state 0xd -> 0xe.
5. The CLIENT's own state reaches >= 0xe (its record byte at +0xf8). The client runs the same 0x6c49a0, so its own gate needs ITS OWN
   connected >= ITS OWN [b9]. See 4: that is the risk.
A press of the 0x7f lobby action in state 0xd moves to 0xe at once; a second press does nothing at X=4.

## 4. RISK for the hook (klhook/kllobby.c)
kllobby writes [sm+0xb9] on the host only and bypasses the replication the real LEFT/RIGHT path uses (setter 0x739f20, then 0x6484d0 ->
0x80ef80 sets the replicated variable D+0x14c, D = [sm+0x84] DDL_ZServer; its on-change callback 0x574040 (registered at 0x76c46b)
calls 0x739f20 with the new value on the clients). So a client keeps the b9 it got from the replicated value (the lobby's old number,
default 6: GUESS from kllobby's note) and its own gate (connected 2 >= b9 6) stays false: its state never reaches 0xe, and the host stays
in 0xe waiting on 0x7d1590. Whether a client can instead be pulled forward by the host's state ([sm+0x64] in (0xe,0x19) -> SetState(0xf)
at 0x6c4cc4 and 0x6c501d) is NOT settled: [sm+0x64] may be the host's state or the previous state. Suggested hook fix (not tested):
when the hook changes b9 on the host, also call 0x6484d0(n) on sm (thiscall, one stack arg, authority-only inside) so D+0x14c carries n
and the client's callback sets ITS b9; do it before the client joins. Verify with a log line on the client printing [sm+0xb9], [sm+0x70].
Live signs: client stuck in state 0xd, or host stuck in 0xe, = this risk.
