# Remote camera yaw (m_CamAngle): what it drives and where a smoother goes (static, 2026-10-23)

Workflow read + refute + design, kl2.exe only, nothing run. R = [P+0x274c] (replica), P' = [R+0x540] (== P online).
CERTAIN = seen in disassembly by both reader and checker; GUESS otherwise.

## Path (CERTAIN)
- Receiver 0x5d31c0 (ecx = R): `[P'+0x2808] = movsx [R+0xe0] / 162.97` (1024 units per turn), `[R+0x548] &= 0xf7`.
  Not in any vtable: only reached by `jmp` at 0x7dffa8 in thunk 0x7dffa0, whose only caller is 0x8b2949 in 0x8b28e0.
- 0x8b28e0 tests `[P+0x2720] & 2`. Local (bit set): yaw from the body matrix (0x429ff0) stored at 0x8b2925, then the sender
  0x645e10 -> 0x789820. Replica (bit clear): 0x5d31c0, then at once 0x8768c0(P, ...) builds a Y rotation from [P+0x2808].
- 0x8b28e0 <- 0x6d9a25 in 0x6d90a0 (movement interpreter: stick -> camera frame, move flags P+0x438, turn angle P+0xafc,
  turn flags 0x20/0x40) <- 0x821704 in 0x8216c0, gated by 0x876a80 != 0 (0x8216e8). 0x8216c0 has two callers: thunk 0x8ca6c0
  (slot 14 of vtable 0xbb0294, RTTI says CRigidBody - doubtful) and 0x498073 in event handler 0x498050. Per-frame: GUESS.
- [R+0xe0] is refreshed from the extrapolation model by 0x519e80 at 0x601435, inside 0x600eb0 (slot 393, which
  klnetsmooth.c already wraps). No smoothing between that and 0x5d31c0: only int16 quantisation. The refresh is skipped on
  0x600eb0's early exits ([P'+0x2760]>0, [P'+0xd5c]!=0, vtbl 0x1c8 / 0x3d0 true), so [R+0xe0] can go stale there.
- Send side (from re/netcode docs, not rechecked): camera 40 units (~14 deg) tolerance, 200 ms min, 2000 ms forced refresh.
  So a standing sender who turns the mouse moves the remote's [P'+0x2808] in coarse extrapolated steps.

## Other readers of [P'+0x2808]
- 0x4f8117 (BaseMove 0x7a51ac, grenade throw-back 0x54368d, 0x8527a4) and 0x64e4ca (ZFFPlayer slot 368, many callers):
  yaw-only orientation getters. 0x849763 in 0x849700 (from 0x58f8e0, 10 callers incl. BaseMove): sway/aim pose, GUESS.
- 0x4827df, 0x5f3fdf, 0x55327b (slot 411): eye offset (0,150,0) - yaw has no effect (Y rotation of a Y vector).
- 0x42cdd3: world vector -> camera-yaw 2D (slot 423, ZHitDirectionDisplay slot 5): local HUD, GUESS.

## Aim point m_FireAimPos (CERTAIN)
Receiver 0x4ca1a0 (ecx = R), called every slot-87 update via 0x4677c0 -> thunk 0x4a3cb0 (replica branch): refreshes R+0x170 into
R+0x178..0x17c, builds a vector from the body matrix, 0x724a10 stores it at [P'+0x27b0..]; slot 87 (0x580a58..0x580a86) copies
that into [P+0xd74..0xd7c], the remote's current aim vector. Second caller 0x63c44b sets [R+0x548] = 0xff first (full resync,
GUESS). Tolerance 5 units, 150 ms: jumps there are unlikely to be visible. Consumers of [P+0xd74]: not traced.

## Smoother design: opt-in `[NetSmooth] CamYaw=1` (not built)
- Hook: a `kns_camyaw(P)` step in the existing slot-393 wrapper `kns_update`, after the original 0x506350 returns. Require
  [R+0x540] == P, skip the local player ([P+0x2720] & 2, kns_local). Offline Arcade has no R: never write there.
- Only safe write target: int16 [R+0xe0] via klh_data (2 bytes, heap). The float [P'+0x2808] is overwritten by every
  0x5d31c0 call; 0x5d31c0 has no slot to wrap and SHIP refuses code patches.
- Restore at entry: if [R+0xe0] still equals what we wrote last frame, put the raw value back BEFORE the original runs, so
  0x519e80 never extrapolates from our number (whether it would is not traced) and the frame order vs 0x8b28e0 does not matter.
- Rule: wrap-aware (1024/turn, shortest path), critically damped spring like the body yaw; reset on first sight, dt > 0.25 s,
  position jump, [R+0x548] == 0xff, or error > ~150 deg; write `raw + round(wrap(s - raw))` (stays on raw's int16 branch).
  Keys (guessed defaults): CamYaw=0, CamSmoothMs=70, MaxCamDegPerSec=720, CamSnapDeg=150.
- Test (two-process System Link bench, TEST build, Log=1): the non-host turns the mouse while standing; log raw vs out per
  remote, a "movement saw our write n / m" counter (compare [P'+0x2808] with the written value at next entry), writes ==
  restores, 0 faults; then an Arcade round with no camyaw lines.
- Built 2026-10-23 on branch feat/1023-camyaw (commit 2e05551f9, TEST out_3f_1023d_test md5 51232608, SHIP out_3f_1023d
  md5 5dcac8b0; inis C:\kl_build_1019\live\solo\H6_host.ini / J6_join.ini). Live proof NOT yet obtained: H6, H6b, H6c failed
  before any round. The client's server browser lists nothing and it fails at waitwin FALobby (exit 26, 0 faults). The H7ctl and
  H7b controls with H5's exact hook (1023b TEST) and inis fail the same way, so this is not CamYaw. Common factor: every failing
  run came up at 640x480 / 59 Hz (owner's monitor off). H1, H4 and H5 (2560x1440) joined. In H7b the client never held a UDP
  socket while the host held 9100 + 9103. Rerun H6 when the display is on. Not merged into rtp-schemas until it passes.
- Open: who consumes [P+0xd74]; the true class of 0x8216c0 / 0x6d90a0; the frame order of slot 393 vs 0x8b28e0.
