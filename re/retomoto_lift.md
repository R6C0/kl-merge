# Retomoto lift: the jump fires 9 m before the car (2026-10-23)

## PROVEN LIVE 2026-10-23 04:45 (TEST LIFT4, hook out_3f_1023h_test, installed DM09 KLJoin.ini: Delay=2.5, CarMin/CarMax, CarWait=6)
The player entered box 9 at (2442, 19601, 1); the ride started and did NOT jump on entry. Re-entries during the ride were ignored. 8.5 s later
(Delay 2.5 + CarWait 6, the script never reached the car box) CarFallback jumped him from (2608, 19601, 480) to entry 5 '06_Exit'. He was at
(6411, 570, -6221) 500 ms later. Shots LIFT4_200s (inside the tower car) and LIFT4_203s (the lobby car, the lobby beyond the doors).
LIFT3 showed the cancel path: a route that left the box (x 2204, more than Slack 150 outside) gave 'CANCELLED', and so did a downed player.
Not yet seen: the jump from INSIDE the car box (a human walks there in about 3 s; the script was slowed by guards).
04:52 hop 6 NoHuman=1 INSTALLED in the live DM09 KLJoin.ini (backup KLJoin.ini.before-1023nohuman). TEST LIFT5: 'hop 6 held (NoHuman=1)'
every 30 s; at the ride's jump crewjoin moved 6 of the 7 bots from the tower (y 21000) to the lobby places (one was at the entry already), so the crew
now goes down WITH the human instead of vanishing to the street after 150 s.

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
