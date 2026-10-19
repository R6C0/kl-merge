# Hasta escape chopper destroyed with five bots aboard (owner run 2026-10-19 13:29)

Static reading and log statistics. Not tried in the game.

## What happened (lastrun.log 26340-26760, KLHook.log s226)
- 13:29:17.6 FollowOutHoldAlone stretched the wait timer from 1.9 to 46.9 s. Nothing was shielded: the chopper is kind 2 and has no ZAnimatedVehicle health object.
- 13:29:27.04 state 5, the chopper leaves:
  - About 37 s were still left on the wait timer.
  - The 'spare' line says no time was set for this departure.
  - The human was in play, outside the boarding box.
- 13:29:27.44 state 6, DESTROYED. The ZHeli had climbed only 7 units.
- 13:29:27.46 the human became the traitor. This is a consequence of the destruction, not its cause.
- 13:29:27.51 all five aboard died. The last bot then shot the human.
- The log has no damage line for the chopper.

## Static chain (kl2.exe; CERTAIN unless marked)
1. ProjectileHit reaches the VehicleEffects health model at 0x412430:
   - health is at +0x5ec, the maximum at +0xba0;
   - BlowupChance is at +0xbfc (Definite = 4).
2. Health at or under 15 % (0x412674) sends EscVehicleState 1. That reaches 0x594b10 and then rules slot 94 (0x6a1100) with grade 1:
   - the timer goes to 0, which means 'leave now';
   - BlowupChance does not gate this step;
   - it overwrites the hook's held timer.
3. Health at 0 with Definite (0x4127c3) calls the blow-up 0x877f30, which sends EscVehicleState 2. That reaches slot 94 with grade 2:
   - this is state 6, which kills everyone aboard;
   - it is the only state-6 writer for kind 2.
4. GUESS: the other callers of 0x877f30 (0x55f3ca, 0x7a73e1, 0x590480) also test BlowupChance. Not checked.
5. NOT TRACED: the writer of the human's traitor flag. It fires 16 ms after state 6.

## Log history (departures.csv in the 3f scratchpad; 216 departures from all logs)
- State 6 after a departure happened 12 times, all on Hasta (12 of 41). There were none on 25 DM05A departures with the same chopper, and none on about 136 other departures.
- All 12 reached state 6 within 0.19-4.9 s of state 5, never during the 20 s drive-out.
  - This points at damage around lift-off: a collision with Hasta geometry, or a burst of hits there.
  - Long waits survived: 53 s and 118 s, the latter unshielded.
- These do NOT separate destroyed departures from safe ones on Hasta:

  | Factor | Destroyed (of 12) | Safe (of 29) |
  |---|---|---|
  | Traitor aboard | 1 | 14 |
  | Human aboard | 4 | 10 |
  | Hold | 1 | 1 |

- Many awake police near the pad matched in builds s118-s172 (11 of 11 destroyed, 15 of 15 safe). It does NOT hold in later builds. GUESS.

## Fixes
- **tools/kl_escape_noblow.py** sets BlowupChance Definite to None.
  - It is data only and keeps the slot order.
  - It closes the only state-6 path, but NOT the 15 % early lift-off, so the human can still be left behind.
  - Builds are staged in C:\kl_build_1019\noblow for DM11B, DM05A and DM06, with INSTALL / UNDO noblow.bat.
- **klhook/klheliprobe.c** adds health to the 'heli:' line (hp=, blow=) and logs it on every drop.
  - The next Hasta run shows whether the drop is instant (collision) or gradual (gunfire).
- **Possible later fix, NOT done:** a hook guard at 0x594b10 that ignores grades 1 and 2 while a kind-2 vehicle is held. This is a code patch, so it needs a live test.
- **klescort.c** gains [Bots] FollowOutHoldUnshielded.
  - The default is 1, which is the old behaviour. 0 means an unshieldable vehicle is not held.
  - The hold is NOT the cause (above), so leave it at 1.
