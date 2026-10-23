# Balance pass 2, 2026-10-23 ("ironing out the balancing AI seems like its a bit too op")

Offline only: nothing launched, nothing written under the Dog Days folder. Branch `feat/1023-balance2`.

## 1. Measurement (KLHook.log, 546 MB, streamed; scripts were throwaway)
The honest result first: **there is no owner play after the pass-1 install** (02:14 on 10-23). Every session after
that is a scripted autotest (TEST hook, `build: TEST`, run ini with PlayerHealth x10 / CopToYou ~0, i.e. a god-mode
human), plus one 4-minute SHIP menu session at 05:38 with no round. So pass 1 itself has not been felt or measured yet.
What exists is the owner's SHIP play BEFORE pass 1 (CopToYou 1.30, health 412): 70 rounds, mean 131 s.
- 27 of 70 rounds had at least one knock-down of the human (39 downs); first down median 69 s into the round.
  On the older 1.00 / 0.73 setup: 37 rounds, 15 with a down, 33 downs, median 68 s. Mostly Retomoto (f06).
- Who put him down (attacker of the last bullet while on the floor, `down: rules` lines): police/guards 113 of 149 (76 %),
  AI heisters (team Ally) 36 of 149 (24 %). Median hit on the floor 5.2, max 67 (health 412).
- Traitor events: 3 BACKSTAB in the 70 rounds. Pass 1 already cut that (Backstab 20, TraitorsMax 1).
- Not in the log, so not measurable: damage per hit before the knock-down, head shots, AI accuracy by range
  (`LogCrewHits` only logs hits on the CREW; nothing logs hits on the human before he goes down).
Consequence: the numbers below are a judgment from the 76 / 24 split, the stock tables and the pass-1 note, not a fit.

## 2. What the Ramp does (why these keys are the right ones)
`[Balance] Risk=2, Ramp=1` writes police->you as max(CopToYou, stock row). Stock Arcade rows for police->you are
0.1 0.2 0.4 0.8 1.0 1.3 1.6 1.9 2.2 2.6 3.0 (level 1..11). So CopToYou=0.9 meant 9 x stock on level 1 and nothing from
level 5. Cutting it to 0.7 lowers the first four levels only. Same for CrewToYou (stock 0.1 0.2 0.4 0.8 1.0 ...; Risk=2
had it at 1.0 = 10 x stock on level 1). The AI heister bullet on the human was a quarter of the floor hits.

## 3. Changes
Ini (patch `<work>\build\balance2_1023\KLHook.balance2.patch.ini`):
| key | pass 1 | pass 2 |
|---|---|---|
| [Balance] PointBlankToYou | 6.0 | 4.5 |
| [Balance] CopToYou | 0.9 | 0.7 |
| [Balance] CrewToYou | (Risk=2: 1.0) | 0.6 |
| [Balance] PlayerHealth | 0.9 (495) | 1.0 (550, the game's) |
| [Balance] CopToYouFar / NearAt / FarAt | none | 0.6 / 12 / 40 (needs the new hook) |
Left alone: CrewHealth 1.25, FreeSeconds 10, Backstab 20, TraitorsMax 1, Regen 6/6.

Code (`klhook/klbalance.c`, only): new key `[Balance] CopToYouFar` (0.2 .. 1; absent or 1 = off = old behaviour),
`CopToYouNearAt` (m, default 12), `CopToYouFarAt` (m, default 40). It multiplies the table's police->you float by
1 within NearAt, by CopToYouFar from FarAt on, linear between, priced for the distance from the human to the man who fired
the last bullet that hit him. Same mechanism and write path as the existing YouToCrewFar (steps of 0.02, data write
through klh_data, no log line per step). Not for a police human, not for the traitor, only while the dial acts (non-stock
level, Arcade). Log=2 prints `balance: copfar: last bullet on you came from ... at X m: police->you x Y`. Boot line:
`balance: CopToYouFar=0.60: ...`.
Not changed: klhook.c wiring, klmusic.c, klambience.c. The guard accuracy at range is level data (`kl_map_ai.py`), not touched.

## 4. GUESS list (also in code comments)
1. `[player+0x2778]` is the attacker of the last bullet that hit the human and is already set when the table float is
   read for that bullet. kldown.c uses it the same way (reads only). If it is set after, the first bullet of a new shooter
   is priced for the previous shooter.
2. Attacker team at `[[att+0x54]+4]` != 2 (Ally) means police/guard (kldown.c's reading).
3. One float serves all police: with several shooters, the last one's distance prices every shooter.
4. The falloff shape and numbers (12 m / 40 m / 0.6) are a first guess; Dog Days maps are mostly short range so 40 m
   will mostly matter on Retomoto's lobby/street and DM03.
5. The ini numbers (4.5, 0.7, 0.6, 1.0) are a judgment (section 1): no post-pass-1 owner data exists.

## 5. Builds
SHIP `klhook/out_balance2_1023/dinput8.dll` sha1 6ef813b9df3a7cd1aea965e3ae51a78fc77b6233
TEST `klhook/out_balance2_1023_test/dinput8.dll` sha1 cc9fd87fcd1b423d113dc655bd1cc2547793172e
(built with `build.bat <dir>` and `build_auto.bat <dir>`; the out dirs are untracked.) Copies and the install
kit are in `<work>\build\balance2_1023\` (G:, about 0.5 MB).

## 6. Install / undo (the lead; game closed)
`<work>\build\balance2_1023\INSTALL balance2 1023.bat` (ini + hook) or `... ini` (ini only, old hook: CopToYouFar is
ignored). Undo: `UNDO balance2 1023.bat` (restores KLHook.ini and dinput8.dll from `.before-1023balance2`).
NOTE: at 09:14 the installed KLHook.ini was a test state (PointBlankToYou=0.0, CopToYou=0.001, PlayerHealth=10). The
patch writes absolute values so it works on either, but restore the owner's ini first or the backup will hold the test one.

## 7. Live test for the lead (use the TEST hook `test\dinput8.dll` with the scripted round on a non-stock map)
Ini keys: pass-2 patch above, plus `[Balance] Log=2`; the test ini must NOT carry the god-mode values (PlayerHealth=10,
CopToYou=0.001). Route: the Retomoto round (f06) or DM03, the human walks into the police at range; or any round
where police fire at the human from over 40 m.
Log lines that prove it:
1. At boot: `balance: CopToYouFar=0.60: a policeman's bullet on you costs police->you x 1 within 12 m, x 0.60 from 40 m on`.
2. In the round: `balance: copfar: last bullet on you came from <actor> at <d> m: police->you x <m>` with m = 1.00 for d <= 12,
   0.60 for d >= 40 and in between linear. Seeing both ends proves the mapping.
3. The table write is a data write: `down: rules:` lines (when he is down) list `the table holds police -> you ...`; with
   CopToYou=0.7 on level 1 and a 40+ m shooter it must read 0.42 (0.7 x 0.6), at 12 m or less 0.70.
4. Pass criteria: a `RESULT PASS` exit; no `copfar` line with m outside 0.60 .. 1.00; no `copfar` lines at all when
   `CopToYouFar` is removed from the ini (old behaviour); with the key removed the table reads exactly pass 1's values.
Optional proof of GUESS 1: with Log=2, compare the first `copfar` line after a new shooter's first hit with the next one;
if the first one carries the previous shooter's range, GUESS 1 is wrong in the "after" direction.

## 8. Open risks
- No data on the real feel after pass 1; the cuts are on top of a pass that has not been played. If the owner finds
  pass 1 enough, install `ini` with only PointBlankToYou/CopToYou lines removed from the patch.
- CopToYouFar writes the shared float on every pass at 50 ms; a stale attacker pointer is validated by the ZFFActor vtable
  check only (a freed-and-reused slot of another class makes the multiplier 1.0, harmless).
- Ramp makes everything vanish at level 5+; nothing here eases high levels (stock 1.0 .. 3.0). Intended.
