# Hot Coffee II (DM01B, F03): campaign leftovers vs the 340-hp crew one-shot (offline, 2026-10-19)

Live zip studied: ea8cbc82 (`C:\kl_build_1018\owner_1018\Maps\DM01B\F03_Main.zip`). Nothing was run in the game;
nothing in the Dog Days folder or KL_PortBackup was touched. CERTAIN = read from the files. GUESS = inferred.

## 1. Finding: a destructible campaign car stands 1.5 to 3.5 m from EVERY death site

The earlier notes (hotcoffee2_oneshot.md) looked for "car / explosive / kill volume near" and found none. Measured on
the .prp (controller `VehicleEffects`, world position from the .gms chain), nearest car per site (units: 100 = 1 m):

| site | position | nearest car (node, name) | car position | distance |
|---|---|---|---|---|
| A | (2102, 27058) | 1964 PcT0200_Police_a_00#14 | (1905, 3, 27296) | 3.1 m |
| B | (4383, 23956) | 2336 PC0200_JPN_Civilian_a_00#01 | (4057, -16, 23844) | 3.5 m |
| C | (2863, 25994) | 2142 PcT0200_Police_a_00#09 | (3169, -15, 26136) | 3.4 m |
| D | (5254, 23937) | 2376 PC0200_JPN_Civilian_a_00 | (5122, -16, 23861) | 1.5 m |
| E | (3015, 25950) | 2142 PcT0200_Police_a_00#09 | (3169, -15, 26136) | 2.4 m |

- CERTAIN: the level has 46 `VehicleEffects` cars (all campaign props, M01A_LOC_Outside / Inside); 45 have
  field 23 = `BlowupChanceDefinite`, one `BlowupChanceNone`.
- CERTAIN: Dog Days' own car in this slot's stock F03 (one VehicleEffects) differs from the campaign cars in the fields
  3 and 4: 8000 / 9000 stock against 600, 700 or 1000 / 1000 here, so the campaign cars are about 10x easier to wreck.
  Other differing fields (stock vs campaign): 14 (0 vs 1 on 41), 17 (2.5 vs 2.5/1/0/0.1), 18 (350 vs 500), 19 (100 vs 300),
  21 (100 vs 200 on 29), 15 (900 vs 900 on 36, 3000 on 9, 1100 on 1).
- GUESS: fields 3/4 are car health values, 15 and 18/19/21 are blast size / damage numbers (no property names exist in
  the exes, only the pairing with the stock values; the enum field 23 is certain). A car that dies with BlowupChanceDefinite
  explodes; the explosion reaches a bot next to it as a blast hit (damage kind 9 in re/crew_hits.md, which no sender
  was found for) and is a one-pass drop of the size seen (347 -> 0). klbalance has a CopToCrew scale for bullets only (GUESS:
  an explosion is not covered), which would explain why the 340 survived the balance pass.
- Why the bots are there: A..E are the places where the crew stops to fight beside the street cars (cover). Gunfire from
  police at the crew also hits the car, a 600-1000 hp car goes up in a few bursts.
- NOT proven: no log line says "a car blew up beside bot N". The recipe in section 5 would show it.

## 2. Table of the other leftovers (all inspected, none a plausible 340 one-shot)

| object | class / controller | position | what | can it hit a crew bot at A..E |
|---|---|---|---|---|
| 06_Squad_LeftSniper (275/285 group, actor 293 `Ground`) | ZFFActor + ZSoldier eArmy | (-3553, 0, 27030) | ordinary army ZSoldier vector (same as 17 other police), stock Rifle_Type88_S; squad started only by Specials!LevelSpeak!TriggerBox (node 20867, box (4500,100,24250), field 17 list of 8 squads incl. both 008_Defend) | LOS to A: same z, 56 m, in sight-range-50m+ edge; to B 85 m. A rifle bullet cannot do 340 (bullet scale 0.01, refuted before). Unlikely; GUESS |
| 06_Squad_RightSniper (actor 283) | same | (11781, -13, 26233) | same | 90+ m from every site: no |
| 010_MC_Kill_Hero / TRACK_HERO (279/289) | ZGROUP / ZSTDOBJ with no controllers | (0,0,0) | inert (no controller) | no |
| SM_SetHPToOne (43, 107) | SquadModifierBehaviour, field 7 = eVM_OneHP, empty target list | (5049,-10,24745), (3248,-10,25124) | sets the ONE-HP rule of its own police squad (police die in one hit); acts on the squad, not the crew | no, it helps the crew. Left alone |
| 16 SquadModifier eLM_Leash / 3 Unleash | SquadModifierBehaviour field 0 | various | leash radius of police squads | no |
| KillBox (20577) | ZBoxPrimitive `KillBox` under `V_Van_00` (F07 escape vehicle, stock Dog Days) | (5192, 80, 30800) | the van's own kill box, stock | only at the van (z 30800), none of A..E |
| Projectile_* (14743..14752), Rocket_RPG7 (14728/38) | `Projectile` | (0,..) | Dog Days system templates; RPG7 field 0 = 406816 vs stock 487344 (a handle, GUESS) | rockets are fired by no leftover squad |
| PhysicsEffect x13 | hanging diner lamps (8670..8694) | y 442, 14-20 m from D | CONSTANT effect, no damage fields | no |
| HavokShatter x50, HavokShatterGlass, SmashActivate x16, ShotActivate x178 | pillars, diner wood, glass, shop signs | around B..E | break on shots, fields are shatter quality / piece counts | no (debris only; GUESS no damage) |
| MC_ShootTeargasAtDiner (19), MC_ShootAtDiner (62, 78) | ZGROUP, no controller | (5007,-10,26127) | markers; squads' own teargas grenade is a police shot | tear gas is not a 340 drop |

Also checked and refuted: Sn_Rem700 is Dog Days stock (present in F01, F03, F05, F07; no actor holds it), so
hotcoffee2_oneshot.md's "Dead Men template" remark is wrong; the snipers use Rifle_Type88_S.

## 3. The post-pass: tools/kl_hc2_strip.py (NEW, opt-in, nothing imports it)

`python tools/kl_hc2_strip.py <in F03_Main.zip> <out F03_Main.zip> [--no-cars] [--no-snipers] [--radius N] [--list]`

- cars: VehicleEffects field 23 `BlowupChanceDefinite` -> `BlowupChanceNone` on all 45 (`--radius N`: only cars within N units
  of one of the five sites). No health values changed (GUESS which are health).
- snipers: the two `...06_Squad_{Left,Right}Sniper\008_Defend` entries are dropped from the LevelSpeak box's target list
  (8 -> 6 entries). The sniper actors stay in the level.
- Only the .prp member is rewritten (level 9, as the live zip). No entity added or removed. SM_SetHPToOne is left.
- To bisect: run with `--no-snipers` (cars only) or `--no-cars` (snipers only).

## 4. Staged build

`C:\kl_build_1019\hc2_nocampaign\DM01B\` = full copy of the live folder (21 files), with F03_Main.zip replaced.

| file | md5 |
|---|---|
| live F03_Main.zip (ea8cbc82) | ea8cbc820898eeae1dc2922170dab2c2 |
| staged F03_Main.zip (cars + snipers) | c160bdc66ac5cb3a7353205391daa663 (c160bdc6) |
| tools/kl_hc2_strip.py | 3cdd2487798d130d1567a26ee06bb44e |

Diff against the live zip (decoded node by node): 31 members, ONLY `Scenes/Locations/F03/F03_Main.prp` differs; node count,
names, props and controller names identical; the changed fields are exactly 45 x VehicleEffects field 23 and 1 x TriggerBox
field 17 (8 -> 6). The other 20 files of the folder (KLTalk.ini, KLWardrobe.ini, .WAV/.WHD/.SND/.hti) are byte-identical.
Checks: debug/check_passes.py PASS (A, C1, C2, B, C3; the one B warning is in the live zip too); debug/check.py output identical
to the live zip's (0 layout problems); tools/klt_audit.py on the staged ini + zip gives the live result (its missing-key
warnings for DM01B pools 9/10 exist in the live build). The pass round-trips the .prp byte for byte when nothing is changed.

## 5. Test recipe for 3f (hook live a57d9ce7 + hit log out_3f_1018d)

1. Install the staged folder as DM01B (the live one is ea8cbc82; rollback = copy it back). It needs the owner's install
   path as usual; the hook is not changed.
2. Run the same L93-style round (hit log hook out_3f_1018d: `LogCrewHits=1`; with the 1019a build also `LogCrewHitsBig=100`).
3. In KLHook.log grep for: `DIED` and `BIG` lines, and in the line before a death the `hp` drop: a 300+ drop in one pass with
   `NO TARGETER and a big loss`. Compare the positions with A..E (2102,27058 / 4383,23956 / 2863,25994 / 5254,23937 / 3015,25950).
4. Reading the result:
   - No big drops and no one-shot: cars are the cause (then try `--radius 1500` to keep far cars as scenery).
   - Same drops at the same spots: not the cars; rerun `--no-cars` vs `--no-snipers` is not needed, instead look at
     the next candidates (HavokShatter pillars at (3101,25502)/(3099,25105) are 4-8 m from C/E: GUESS, shatter pieces falling).
   - Drops only beside cars that are NOT neutralised (a run with `--radius` smaller than 3500): confirms it.
5. Cars that never explode is a visible change; tell the owner if it is kept.

## 6. Verify (independent recheck, 2026-10-19; nothing run in the game, nothing written outside C:\kl_build_1019\hc2_nocampaign\)

Method: own scripts (kl_fa.load + kl_scene.read + kl_fa_bank.world_of) on the live zip ea8cbc82 and the staged zip c160bdc6.

CERTAIN (re-measured):
- Distances to the nearest VehicleEffects car: A 309, B 344, C 337, D 152, E 242 units. Table in section 1 holds. 46 cars, 45 of them BlowupChanceDefinite.
- Staged zip vs live: same member list, only `Scenes/Locations/F03/F03_Main.prp` differs; 46 nodes differ, 45 same-length VehicleEffects edits
  plus 1 TriggerBox (list 8 -> 6); no node added, none removed, paths identical. The other 20 files of the folder are byte-identical (cmp).
- check_passes: PASS C1, C2, B, C3 (the single WARN Shards_Group_A is in the live zip too). Disk: C: 11 GB and G: 6.4 GB free (>= 4 GB).
- Crash risk: LOW. No object is removed, so no empty pool and no dangling reference (CLAUDE.md "Pool category is exact" does not apply).
  BlowupChanceNone is already used by one car of this level (same field, same size). TriggerBox field 17 is a count-prefixed list whose
  length varies in the stock files (this level: 0, 1, 3, 5, 6, 8). The dropped sniper squads still exist; they are simply never started.
  UNCHECKED (GUESS): whether anything waits for the snipers' 008_Defend to run (wave or end-of-fight logic).

NOT SOUND (the culprit identification is weaker than claimed):
1. Confound: the cars ARE the cover. Only 6 of the 46 cars stand in the street (x 1500..6000, z 23500..27500): ids 1851, 1964, 2142, 2296, 2336, 2376.
   Bots stop at cover, so deaths beside cars are expected whatever kills them. The random baseline is also not small: 12.6 % of random
   street points lie within 3.5 m of a car (median 8.1 m). Five-for-five is less striking than it looks; C and E share one car.
2. "Campaign cars ~10x more fragile" is not unique: Dog Days' own F02 has two cars with fields 3/4 = 1000/1000 and all stock cars are
   BlowupChanceDefinite (F02, F03, F06, F08). Only F03's car has 8000/9000 and it is one car. Stock maps hold 0 to 2 cars.
3. Mechanism unproven: the cars here are static props (no ZHavokCar, no spline, earlier note section 3). Whether a static VehicleEffects car takes
   damage, wrecks and explodes at all is UNKNOWN. No log line shows an explosion near any death.
4. Magnitude: a blast of exactly 340 on a bot at 347 is a coincidence to explain, and the L93 log has no kind-9 hit (it was saturated after 00:20:24.9).
Verdict: cars are a reasonable, cheap experiment, a candidate (GUESS), not an identification. Same for the snipers (unchanged: unlikely).

Change made in this verify: bisection variant so one run attributes the effect.
- `C:\kl_build_1019\hc2_nocampaign\DM01B_carsonly\` = live folder + F03_Main.zip with ONLY the 45 car edits
  (`kl_hc2_strip.py ... --no-snipers`), md5 21c6ed495d5a7398d6b3ec8ac210bf23 (21c6ed49). check_passes run on it, see above.
- Recommended order for 3f: DM01B_carsonly first (the sniper edit adds an unrelated behaviour change and muddies the result).
  If the one-shots stay, restore ea8cbc82 and look at the HavokShatter pillars (section 5) and at LogCrewHitsBig output instead.
- Test-recipe note: with LogCrewHitsBig=100 set, the 1019a build lists the 340 drop with position, which is the direct evidence missing today.
