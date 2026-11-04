# Traitor bot drift online (bs46r DD05: 40 m -> 120-190 m) - 2026-11-04

Research only (read-only on logs and exe). GUESSES are marked GUESS. S = the bot's AI soldier.
Sources: re/attackfromcover_1104.md, re/closein_run_1104.md, re/closein_gates_1104.md, re/bots_escort.md,
klhook/klbrain.c (AfcProbe, RunProbe, HolderSet), klhook/klranges.h, logs of bs46r DD05 and bs47 DM03.

## Verdict
The drift is explained by (a) and (b) together, not by (c).
- The Defend block [S+0x64c] (0x1c bytes: +0..8 xyz, +0xc style, +0x10 given, +0x11 changed, +0x12 queued,
  +0x14 = the soldier, +0x18 scale 1.0) is the anchor for DefendCover (0x84dc90: cover within 500.0 of the
  block, const 0xb3d5e4) and for AFC point paths (modes 1 and 3, when the bot is farther than scale*1000 cm
  from the block and [[[S+0x40]+0x54]+4] != 0). If the block holds a far place, both tactics walk there.
- ZCloseIn (eval 0x6724e0, run 0x76e8c0) writes its own dest into the block (direct branch: dest; cover branch:
  cover position; path-error branch: the bot's own position). The dest is a nav point 550 cm short of the holder
  [S+0xac]. The walk runs to completion (no re-target mid-walk), so a stale holder gives a stale far dest.
- The holder flips: scan 0x767510 (HASHED) has no team test; LosGate hides blocked humans from Sense, so a
  non-human ZSoldier (flags 0x10) wins; HolderSet (0x8bd420, hashed) re-asserts the human, racing the
  1024 ms stock scan.

## Hypotheses

### H-a: the defend place is far from the humans (SUPPORTED, DM03 clearly)
- DM03 AfcProbe: bot walks to a place ~119 m from the human through DefendCover; ddef falls to ~0 while dhum
  rises to 11877 cm.
- Writer of the far place at ~12:00:58-59 UNKNOWN. [S+0x4fc] going 1 -> 0 looks like the signature of an order
  via 0x760e50 (HASHED; sets [S+0x4fc]=0, [S+0x720]=0, snaps the place into the block). Candidates (GUESS):
  hook puppeteer/ledger, Restless, the game's route chain.
- Prove: log block xyz + blk+0x14 each second and an event line on every change (previous place, winner,
  [S+0x4fc]); a change with winner = CloseIn is H-b, with winner none and 4fc 1->0 is an order.
- Disprove: ddef stays > 10 m while the bot moves toward a human, or the block equals the human's position.

### H-b: CloseIn/AFC target is not the human (SUPPORTED, DD05 clearly)
- DD05: CloseIn arm #1 and #7 target the human (dest 526 cm from the human). From arm #8 the dest is 119-168 m
  away; holder shows entities 0x38f / 0x3c0 with flags 0x10 (non-human) alternating with HolderSet's 0x1aa.
  CloseIn commits to the stale dest.
- Prove: at each CloseIn eval and arm log [S+0xac], [S+0xb0], [S+0xa8], their class/flags (+0x10 bit) and
  distance to the nearest human, plus dest-to-human distance.
- Disprove: holder always has human flags at arm time while dest is still far.

### H-c: movement request / path code differs online (DISFAVOURED)
- The bot reaches its dests at ~3.3 m/s, run-task states ([S+0x56c] via 0x5faeb0 / 0x800630) are normal.
- Prove only if a bot with block ~ human and holder = human still does not approach (task state stuck).

## Smallest lever (default off, ini-gated, marked traitor only, no detour in hashed ranges)
L-A: per tick, when blk = [S+0x64c] has blk+0x14 == S and the bot is a marked traitor, if the block place is
> N m (suggest 25) from the nearest human, overwrite block xyz (+0..8) with that human's position (write data
only; hashed 0x412910 is not called). Also set +0x11 changed only if the Defend loop needs it (GUESS: it reads
+0x11 on the next eval; side effects on puppeteer, leash and Restless are unread).
L-B (add if H-b persists): keep the holder human via HolderSet (already in klbrain) while a marked bot is in
Defend, skipping non-human ZSoldiers.
L-C (weak): [S+0x88]=2 so AFC mode 2 anchors on the bot itself; matters only when the bot is > 10 m from the block.
Hooks must sit in free ranges (0x84dc90, 0x76e8c0, 0x6724e0, 0x509f30, 0x4fee00, 0x5faeb0, 0x800630, 0x4a7e60)
or run as a per-tick klbrain data write; never in 0x760e50, 0x412910, 0x85f6c0, 0x7acb30, 0x6e65f0, 0x7f71e0,
0x8602bc, 0x85fa50, 0x85ff6e, 0x5c4360, 0x7b3020, 0x8bd420, 0x767510.

## Probe fields for the next bench
- Block each second: xyz, +0x10, +0x11, +0x12, +0x14 (== S?), and a change event line with previous place,
  winner, [S+0x4fc], [S+0x720].
- [S+0xac], [S+0xb0], [S+0xa8] with class/flags and distance to the nearest human, at every CloseIn eval/arm.
- CloseIn dest vs human distance; [[[S+0x40]+0x54]+4] override word.
- [Bots] OrderTrace=1 ('otrace:' / 'by=GAME?' lines; probably covers KLB/Arcade records only, GUESS).
- arc47 comparison: same probes in the Arcade baseline.
