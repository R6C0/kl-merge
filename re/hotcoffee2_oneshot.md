# Hot Coffee II (DM01B, slot F03): what kills a crew bot in one go

Offline, read-only recheck. Zip: `C:\kl_build_1018\owner_1018\Maps\DM01B\F03_Main.zip` (ea8cbc82).
Evidence: `L93.log` (3f, opt-in hit log, hook out_3f_1018d), L70 and L71 census series, own scene
dump of the zip (`kl_scene.read` + `kl_fa_bank.world_of`; units 100 = 1 m). Anything not read
directly from a log or the scene is marked GUESS. The cause is NOT identified yet.

## 1. L93, rec 1 (rechecked)

- Rec 1 died ALONE at 00:22:17.092: one census-to-census drop 347 -> 0, last drop 340. Not a run
  of bullets: a bullet is -1 to -5 at CopToCrew 0.01.
- Position: last census (2102, 27058), body (2196, 26991). This is NOT at the diner; it is about
  230 m from the human's spawn... the human stood idle AT SPAWN, so the human cannot be the source.
- No actor within 15 m of the bot at the last census. So no nearby guard fired or died.
- Van not present (van state 0 until 23:05), so no van-departure damage.
- Bot health 347 is far above the 30 percent botdown line: not a down, a kill from healthy.
- No explosion line anywhere in the log. The log is saturated after 00:20:24.9 (400 lines per
  round, 6 per second), so the last two minutes are not line by line; only the DIED line is read.
- The "100 -> 5 at 00:19:42" in the task text is not in the log: that entry is 378 -> 373 (chip).

## 2. L70 / L71

Deaths at A..E below. The census is every 2 s, so a short burst cannot be excluded there; only
L93 shows a single 340 step. The claim "guards die in the same interval next to the bot" is NOT
confirmed by L93 (no actor within 15 m). Treat it as unproven for L70/L71 too.

| site | where | scene x,z |
|---|---|---|
| A | L93 rec 1 (last census / body) | 2102,27058 / 2196,26991 |
| B | L70 rec 1 | 4383, 23956 |
| C | L70 rec 3 | 2863, 25994 |
| D | L71 rec 3 | 5254, 23937 |
| E | L71 rec 4 | 3015, 25950 |

PointBlankToCrew was refuted by magnitude (`re/hotcoffee2_losses.md`): the rewrite gives 5, not 340.

## 3. Scene near the sites (own scripts, nearest per class)

- No kill volume, no ZBOUND damage zone, no explosive prop within 15 m of A. Nearest things to A:
  parked police car PcT0200_Police_a at (1905, 27296), 422 away (static collision, no spline, no
  ZHavokCar); CoverBoxM/H props 315 and 378 away; a ZBoxPrimitive "Pos" 209 away; Police_Com_Box
  495 away. None explosive. The earlier "300 from A" for the police car was wrong (422).
- No moving car in the level.
- Campaign sniper squads and diner `SM_*` script groups are still in the graft. A sniper is
  z-aligned with A at about 56 m (GUESS: a leftover campaign sniper with a scripted target, not
  among the listed targeters, so not proven).
- The Dead Men `Sn_Rem700` template (compared with `Rifle_zastavam85`) is a sniper with fields
  that differ strongly from a rifle (e.g. ZItemTemplateWeapon[4] 400 vs 300, ZFFItemTemplateWeapon
  [2] 100 vs 1000, [47] 20 vs 60). Which field is damage is an ASSUMED pairing (GUESS); a sniper
  hit is unscaled by CopToCrew only if klbalance does not recognise its source (GUESS).
- Shatter props (ShatterPillar, FlowerBoxShatter): only near B to E, about 500 away; weak.

## 4. Ranked causes (revised)

| rank | cause | evidence | confidence |
|---|---|---|---|
| 1 | A damage source that is not scaled by the six klbalance factors (campaign script or sniper weapon, `SM_SetHPToOne` style) | single 340 step from healthy, nothing within 15 m, human idle at spawn, no van, no explosion | GUESS, best fit; source unnamed |
| 2 | Leftover campaign sniper squad shooting a crew bot with a Sn_Rem700 | sniper aligned at 56 m; sniper template unscaled-looking | GUESS |
| 3 | Shatter prop area effect | only near B..E, not A | GUESS, weak |
| 4 | Parked police-car props | static, no explosion class, 422 from A | unlikely |
| 5 | Plain gunfire, PointBlankToCrew, human, van, botdown | refuted (magnitude, position, state) | refuted |

Original cause 1 ("an unscaled damage source", with blasts and the van named as examples) is kept
only in generic form: the named examples (van, point-blank, human) are refuted for L93.

## 5. Proposed fixes and whether they are really opt-in

1. Diagnostic `[Balance] LogCrewHitsBig=N` in klbalance.c: bypass the line cap for any single
   drop over N, print position and nearest entities. Default 0 = off, so other maps are unchanged
   (the existing LogCrewHits is off by default at klbalance.c line ~1325, same pattern). OPT-IN.
2. `[Balance] CrewDropCap=N`, default 0 = off. If it is a hook key it applies to every map once
   set, so it must stay 0 in shipped ini files and be set only in a per-map `[Bots.<map>]`-style
   section if one exists for balance keys (UNCHECKED: klbalance has no per-map sections that I
   read). Treat as opt-in only if it reads from the DM01B section.
3. Builder flag `--no-campaign-kills` in `tools/kl_fa_v2_hotcoffee.py` (not read yet, GUESS that it
   can be a flag): affects only the DM01B build when given; the live zip stays identical without it.
   Only worth building once the source is named.

## 6. Corrections to the earlier report

1. Site A is not at the diner (earlier "diner end of the street").
2. Human position: idle at spawn, about 230 m away; the earlier "elsewhere on the route" was a GUESS and is replaced.
3. The nearby-guards-die claim is not supported for L93 (no actor within 15 m).
4. Police car distance from A is 422, not about 300.
5. Van-departure damage is excluded for L93 (van state 0).
6. Added: bot above the botdown line; no explosion line; sniper leftover and Sn_Rem700 as a new GUESS.
7. Fix 2 and 3 opt-in status qualified (see section 5).

## 7. Open items

- Decode the leftover sniper squad (targets, weapon, trigger) and `SM_SetHPToOne` for A..E.
- Re-run with LogCrewHitsBig on and read the DIED line.
