# Online feel: receiver-side heading smoother (klhook/klnetsmooth.c)

Status 2026-10-19: static reading plus a compile check. NOTHING has run in the game.

## Where a remote player's displayed heading is applied (READ in kl2.exe)
- ZFFPlayer vtable 0xbb45f4, slot 393 (dword at 0xbb4c18) = 0x506350, called every frame, no arguments.
  `[P+0x2720] & 2` set -> 0x616050 (the owner's own variant); clear -> 0x4a1890 -> 0x600eb0 (replica receiver,
  argument `[P+0x274c]`, whose `+0x540` is the player).
- 0x600eb0 samples the data objects (positions 0x8df1c0, the heading raw), builds a matrix (0x64ecc0 / 0x8c51b0) and
  places the body with `B->vtbl[0x8c](mat, pos)` (call at 0x600ff5), B = `[[[P+4]+0x50]+0x60]` (0x598460).
  The heading is used raw: no turn-rate limit, no damping. A late/doubled/forced-refresh packet is a one-frame snap.
- Actor (AI) replicas: 0x569eb0, called from 0x82b7f0 (callers 0x5d07dc, 0x6b8388). The vtable that owns it was not
  found; NOT covered.
- Players are listed at `[[0xdd265c] + 0x828 + 4*i]` (i < 28); local = index `[gd+0x898]`.

## What the module does
Private copy (512 dwords) of the ZFFPlayer vtable with slot 393 -> our wrapper; the vtable POINTER of each remote
ZFFPlayer is swapped (heap write only). The wrapper runs the stock update, then reads the body matrix; if it is a
pure yaw it runs a critically damped spring on the yaw with a speed cap and writes the matrix back through the
game's own 0x8c call. Restored when disabled, when the session stops being online/unranked, at level end, and
objects that no longer show our table are forgotten. Nothing hashed is written (klranges.h).

Keys `[NetSmooth]`: Enable=0, MaxTurnDegPerSec=540, SmoothMs=90, SnapUnits=300, Log=0.

## Sender side / ping
- Send throttle is the Net-Z tolerance + interval (<= 1 update per 100 ms, forced refresh 2 s): klnet.c `Tune`
  already raises the rate; nothing further is safe to add. Steam P2P tries a direct route first and relays only as a
  fallback; the send is 0x883dd0 through the SteamNetworking accessor (IAT 0xb107ec). A flag change there was not
  attempted (not decoded, would need a wrapper around a Steam interface call). Ping itself is the network's.
- Position delay/interpolation was not implemented: the body is steered by stick bytes + correction and teleported
  past 1000 units, so a display-only delay would fight the game's own correction.

## CERTAIN vs GUESS
CERTAIN (disassembly): slot, branches, B chain, 0x8c call shape, player array, no cap on heading change.
GUESS: bit 2 = "owned here"; `[R+0x540]` is the player; matrix row-major Y-up with the transform at `[B+4]`
(3x3 + pos at +0x24); slot 0x8c is the body's placement and takes (mat, pos); the game rebuilds the body matrix from
the raw heading each frame; display-only (hit tests use +0xc14 / aim data, not touched - not proven).

## Live tests (two PCs, FA, not ranked)
1. `Enable=1 Log=1`: log shows "remote player ... flags" (expect bit 2 clear) and `placed` growing.
2. Watch the other player turn fast, stop, spin the mouse: body should follow smoothly, never snap.
3. Own character unchanged; check aiming/hits against the remote player still land.
4. Leave the match / change level: log shows vtables given back, no crash.
Failure signs: remote bodies frozen (matrix not pure yaw -> `skipped` counts), twisted bodies (axis guess wrong) -> Enable=0.

## Review 2026-10-19 (adversarial, kl2.exe re-read)
Re-verified in disassembly: slot 393 = 0x506350 (vtable 0xbb45f4, ZFFPlayer by RTTI; slot address 0xbb4c18), flag test `[P+0x2720]&2`
(set -> 0x616050, clear -> 0x4a1890 -> 0x600eb0), B = [[[player+4]+0x50]+0x60] via 0x598460 with player = [[P+0x274c]+0x540], the 0x8c call
at 0x600ff5 (args: matrix first, position second, callee pops 8; the matrix is 9 floats, copied by 0x64ecc0). The vtable address occurs only
twice as an immediate in code (constructor/destructor stores), so no vtable-identity compare sees the private copy.
NOT verified: the body's transform layout. The code dereferences [B+4] as a pointer to 0x30 bytes (3x3 + pos at +0x24, the shape of the
animation frames 0x600f8f reads); the body class behind slot 0x8c was not identified. A wrong guess fails safe (matrix not a pure yaw -> skipped).
Fixed: tick runs on the game thread only (the fallback ticker could swap/restore while the game thread frees players); the local player
being unknown now swaps nothing (before, me=0 could swap the local player); a fault that switches the smoother off now hands the vtables back;
IsBadReadPtr size lowered to 0x2750.
