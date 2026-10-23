# Retomoto lift: the jump fires 9 m before the car (2026-10-23)

## THE DOORS SOLVED ON THE ENGINE SIDE (2026-10-23 09:15, TESTS LIFT9-11, probe hook out_3f_1023p_test)
- `klhook/klprobe.c` (KLHOOK_TEST only; `[KLHook] SessionSafe=0`, `[Probe] DoorProxy=1`) wraps proxy init (0xbc36bc slot 14), the proxy
  handler (slot 26 = 0x7ed520) and the trigger box's fire (0xbc232c slot 34). Node names print '?' (the name offset is a GUESS).
- LIFT9: each proxy collects count 5 (the 4 leaves + DrInt_B's second MatPosAnim), not 0. LIFT10: the box fires when the player crosses it
  (09:00:42), both proxies log 'accepted (own id)'. LIFT11: a BOT fired it (09:11:40): MERCONLY takes AI heisters in FA; it fires once.
  So box -> AITrigger -> proxies -> leaves works; with kl_doorfix2 (TEST, blast timer also fires them) the same accept lines come at 16.5 s.
- Why the doors LOOKED shut: the test route, not the scene. The old script goto (2720,760)->(2900,909) crosses x 2793 at z~820 = the doorway
  frame's corner (doorway z 816..1004); in LIFT8 the player stood at (2704,705) against the wall outside it. LIFT10's aligned route (z 910)
  walked freely (2624,859)->(2723,1044) in 0.7 s; it only timed out because the fight slowed the scripted walk (8 s).
- Product state: kl_doorfix stays on DM09 (harmless; other DM09-family folders staged in `<work>\build\doorfix_1023`, NOT installed);
  kl_doorfix2 is NOT for the owner (doors open at the blast = part 1 can be skipped). CarWait 6 s + CarFallback carry the ride when a human
  is slow.
- SEEN OPEN (LIFT13, 09:31): proxies accepted at 09:30:46; the player went down in the hall at (2692, 19601, 881) and lay facing the
  car: shots LIFT13_201s / 205s show the lit car interior and its patterned wall THROUGH the doorway (LIFT10_196s = the shut steel panels).
  Not seen: a human stepping into the car box before CarWait ends.

## THE DOORS (2026-10-23 08:50): still shut with a living mercenary; the scene chain is right on paper
- kl_doorfix (commit 51798e693, installed on DM09 only, backup `<work>\build\doorfix_1023_backup\DM09`): both MatPosAnimProxy lists name the 4
  leaves (DrExt_A/B_00, DrInt_A/B_00) as stock F01 AnimProxy_RearDoors_Open does. LIFT7 (player died 08:24:04, back as police: MERCONLY box
  cannot fire for him) and LIFT8 (test ini CopToYou=0.001, PointBlankToYou=0.0: alive the whole route) both exit clean; in LIFT8 the doors are
  still visibly closed, the player stands against the wall at x~2704 and the CarWait fallback jumps him.
- Read (workflow wf_e3f89e40, verified): TriggerBox_OpenExitElevator (node 7857, f10=-1 = fires ONCE, f13 eTGS_AllInside, MERCONLY also takes AI
  heisters in FA) posts 'AITrigger' (slot 34 0x45f5d0) straight to both proxies; proxy fields match stock exactly; leaf MatPosAnim
  ['Activate',...,loop 0, relative 1, start-at-load 0] = stock. Handler 0x7ed520 returns SILENTLY when [proxy+0x30] (collected count) is 0;
  init slot 14 (0x4093c0) disables the proxy when it collects nothing; a controller only answers GetMatPosAnim in state [ctrl+0x21] 1..5.
- Open candidates (not yet separated): the box fires early (a bot spends the single shot) or never; the proxy collects 0 controllers; the play
  cannot tick (node flag 0x400, missing KEYS); a separate static blocker at x~2700 (the player stops 70-100 units short of the leaves).
  DrInt_B_00 has a second, start-at-load MatPosAnim. On 10-09 the GROUP form fired from the blast timer showed the doorway open (campaign_fa G1.9).
- Next: test hook with a probe at 0x4093c0 / 0x7ed520 / 0x45f5d0, and a DM09 variant (kl_doorfix2) that also fires both proxies from the blast.

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
