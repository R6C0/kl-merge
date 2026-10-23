# Retomoto lift: the jump fires 9 m before the car (2026-10-23)

## What the log says (KLHook.log of the game folder, read only, 487 MB, last sessions)
All 15 `join: player 0 entered box 9` lines of the file sit on the EDGE of the box, never at the car:
(2330, 19601, 257..388) = the west face, or (2475..2715, 19601, 0..1) = the south face. The car is at (2974, 19600, 909) and the box is
x 2330..3150, z 0..1100 (it was widened on 2026-10-15 so a fed in the lift hall also jumps). So the player is thrown to the lobby the moment he
steps into the hall, 6-9 m before the car, while its doors (75 frames) have not opened: no ride, no door, no sound.
The mechanism itself works (last session 10:55:50: request, crewjoin moved 2 bots, 6 already carried by hop 2, player in the lobby car 500 ms later,
0 "did NOT land", 0 GIVE UP). A fed in the tower at (2481, 19601, -622) stayed outside the box and was not jumped.
Hop 6 in the INSTALLED KLJoin.ini (md5 0b557e40) has no `NoHuman=1`: it carries the crew away after 150 s in the tower even when the human still fights.
The source (klhop.c line 167, 415) has the gate; the staged `C:\kl_build_1019\rt_hop6_living\DM09_nohuman\KLJoin.ini` uses it.

## What was built (klhook/kljoin.c, keys in [Join], default = old behaviour)
- `Delay=2.5` seconds from the feet entering the box to the jump. The request (the two data writes) is made only then, so klcrew_rt.c / klhop.c, which
  watch the request, carry the bots at the real jump exactly as before.
- Checked at the end of the delay: player still exists, health > 0 ([player+0xa48]+4), not down ([[player+0x2948]+4] == 0), node flag bit 10 clear,
  [player+0xd44] == 0 (the game's own jump skips such a player), feet within `Slack` (default 150) of the box. Else the ride is cancelled (log).
  Cancelled too on a scene change and in a network session ([Net] OnlineSafe, as the instant jump).
- `CarMin=` `CarMax=` (kl_fa_author.JOIN_BOX_CAR) optional second box: the jump waits for the feet inside the car; `CarWait=6` seconds after Delay it
  gives up waiting, then `CarFallback=1` (default) jumps from where he stands, 0 cancels.
- NOT built, on purpose: sound (the ding/open sounds are the level's PlayAudio nodes, not .LOC keys kltalk.c's klk_say can say), fade (no proven
  full-screen HUD fade), hold (no proven way to freeze the HUMAN; the delay is the player standing / walking in the car).
- `tools/kl_rt_joinini.py SRC OUT --delay 2.5 [--car] [--no-car-fallback] [--ini-only]` inserts the keys after the last key of [Join].

## Log lines
`join: box 9 rides: jump 2500 ms after the feet enter, with the feet inside its CarMin/CarMax box (slack 150)` at load,
`join: player 0 entered box 9 at (...): ride starts, jump to entry 5 '...06_Exit' in 2500 ms`,
`join: player 0 rode in box 9 at (...): jump to entry 5 ... requested`, `join: ride of player 0 in box 9 ended with the jump after N ms`,
or `join: ride of player 0 in box 9 CANCELLED after N ms: <why>`. `join: player 0 is at (6411, 570, -6238) 500 ms after the request` follows as before.
