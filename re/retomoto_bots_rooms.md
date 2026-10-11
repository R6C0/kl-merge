# Retomoto Tower: the AI heisters fight every room first, all the way down

Track G, 2026-10-11. **Second form**: written again after the adversarial review (`re/retomoto_bots_rooms_review.md`,
verdict ACCEPT WITH FIXES) and after the first live run of the first form (G1_DM09, the lead's, 09:31). Section 10
says what was done about each defect; the first form's builds, logs and pictures are kept in
`<work>\build\z_rooms\round1\`.
OFFLINE: nothing here was run in the game by this track, nothing was installed, committed or pushed.
Files: `tools/kl_fa_bots_rt.py` (the gates), `tools/kl_fa_bots_dyn.py` (five rules), this note.
Builds: `<work>\build\z_rooms\retomoto_full` (gates) and `retomoto_full_r` (gates + dynamic step with routes) -
**both are the SECOND form now; the build run G1 used is `z_rooms\round1\retomoto_full`** (archive 218,935,710 bytes).
Words: **READ** = disassembled in `kl2.exe` at the address given; **MEASURED** = counted on the build or the live
logs; **ASSUMED** / **GUESS** = not established. Distances in world units (100 = 1 m) unless 'm'.

## 0. Short answers

- The seven die in a string because the tower is STAGED by the campaign's own trigger boxes: the first bot
  through a box wakes the next squads, and the chain of rt_full7 sent the seven on, sprinting, from way place to
  way place (section 1).
- The tower's way out is cut at **seven gates**: a HOLD at cover boxes and behind it, in every bot's chain, a
  `TriggerActorsDead` (stock F07's own wait) that names the actor groups of that fight's squads. It lets the bot
  go on when they are dead, **or 30 s after it was armed - built into the game** (READ; and MEASURED live: 34.0 ..
  36.5 s between the escort's steps at six gates of run G1).
- **G1_DM09, the first live run of the first form** (idle player; section 1.4): loads, no fault; nobody dies
  before GO+175 (the old chain lost six by GO+69..122 in six of its seven full runs; V1: four, GO+127..170); four
  of six get to the first floor, one to the lifts; all six are dead by GO+323. **Six of the seven gates ran out their 30 s.** With nobody helping, a
  gate is a pause in cover (health comes back: 96 -> 242 in 42 s), not a won fight: the men mostly hold their own
  posts out of sight, and after the 30 s the seven walk into them. The gates are for a round in which the human
  clears the rooms - a dead squad opens its gate at once, so the seven follow one fight behind instead of running
  ahead. That round has not been played.
- **The join is NOT proven** (the review's 'must', D1; section 9.1). A wait that is armed when the human takes the
  tower car fires up to 30 s later and starts a TOWER step for a bot the hook has moved to the street. What that
  bot then does nobody has seen: no joined run with bots exists for any build. Both checks now say so in a NOTE
  ('THE JOIN'), `kl_fa_bots_dyn` no longer adds timers of its own to that hazard (it had 36), and the joined run
  is written (`<work>\build\z_rooms\live\J1_DM09_join.ini`, control `J0_..oldchain.ini`). **Neither build
  belongs on the owner's tab before J1.**
- What the second form changes in the holds (section 4): the reception's hold is out of reach of the three cover
  boxes whose far side lies in the atrium's trigger box; no hold lies within 3 m of a post of a man who may be
  alive; **floor2's hold is AT the foot of the first flight**, among the men it waits for, instead of 20 m past
  them (G1: the four who walked that leg lost 81..288 health on it); the gallery no longer names four men one
  floor down (G1: that wait ran out and a bot was shot dead at his gallery hold meanwhile); the man who ends
  beside the floor1 hold belongs to the floor1 gate; the last gate no longer names a man round the corner.
- Both builds pass every check; the talk check FAILs on the countdown rule exactly as `rt_full6\retomoto_full`
  does, because the owner's two delays are in (section 6.3).

## 1. What the logs say (MEASURED; `<work>\build\klhook\live\*_DM09.log`)

GO = `session: state 0x18 -> 0x19`. The round-start event is 8.4..8.8 s before GO, the blast 16.5 s after the
event = GO+8. Record r is `Squad#0(r+1)`. The idle player stands at (6000, 21020, 530); one bot is the hook's
escort and stays beside him.

### 1.1 The first minute: the room gate, and what does not wait for it

| run | build | crew off stage | stage 0 -> 1, GO + s | the escort's chain has started (its route place) | first place of the way out | dead, GO + s |
|---|---|---|---|---|---|---|
| T7 | rt_full7 | 0.5 | 19 19 19 29 33 35 35 | by 37 | 67 | 6: 73..115 |
| R7a | z_route7 | 0.5 | 19..21 | after 23, by 32 | 72 | 6: 85..113 |
| R7b | z_route7 | 0.5 | 19..20 | after 20, by 34 | 79 | 6: 92..121 |
| R7c | z_route7 | 0.5 | 18..20, one 34 | after 29, by 43 | 84 | 6: 77..108 |
| R7d | z_route7 | 1.0 | 18..21 | after 33, by 38 | 55 | 6: 69..115 |
| V1 | retomoto_tab_fix | 1.0 | 18..20 | by 27 | 60 | 4: 127..170 |
| I5 | retomoto_tab_fix | 1.0 | 18..20 | by 26 | 59 | 6: 79..99 |
| V0, V2a, V2b (133 s runs) | z_route7, rt_full7, retomoto_tab_fix | 1.0 | 18..23, one 29 | after 33 by 38, after 21 by 29, after 23 by 28 | - | none by GO+60 |
| **G1** | **the first gates build** | 1.0 | 19 19 20 20 23 27 29 | by 31 | 60 (the door's hold) | 6: 175..323 |

- **The room gate fires GO+20..43 in all eleven runs** (by the escort's first route place; in I5 and G1 by GO+26
  and GO+31), the fall-back (GO+83) was never needed.
- **The bots do not wait for it.** Three to seven of them have heist stage 1 at GO+18..21, ten seconds after the
  blast, in every run; no step of theirs has run then. 'Room first' delays the LOOT and the route, not the
  entry. Nobody died of it.
- The loot wait runs its full 30 s (T7: gate ~33, way out at 67; G1: loot place 31, door 60).

### 1.2 Where they died with the old chain

| run | hook | deaths by place: record, GO + s, (x, y, z), m of way |
|---|---|---|
| T7 | 0.5 | r4 73 (2032, 21000, -846) 56 ONE STEP 236; r3 85 (1654, 21096, -492) 62; r5 89 (514, 21094, 358) 76; r2 90 (544, 21000, -1078) 81; r1 108 (161, 21096, -1271) 85; r7 114 (817, 21093, -408) 73 |
| R7a | 0.5 | r1 85 (-1307, 20675, 1378) 102; r6 105 (-1638, 20581, -1478) 106; r7 106 (-1825, 20444, -1293) 109; r5 110 (-1739, 20476, -1285) 108; r4 111 (-1334, 20745, -1550) 105; r2 113 (-21, 21000, -1188) 86 |
| R7b | 0.5 | r7 92 (-1474, 20674, -1535) 104; r4 99 (-1628, 20561, -1392) 106; r1 101 (-1355, 20740, -1567) 103; r3 105 (-19, 21096, -1185) 86; r5 117 (-542, 21000, -1589) 93; r2 121 (-82, 21000, -1410) 88 |
| R7c | 0.5 | r7 77 (1169, 21095, -400) 70; r1 82 (497, 21096, -1096) 81; r5 86 (230, 21093, 744) 82; r6 96 (1788, 21000, -734) 59; r2 100 (2099, 21000, -838) 56; r4 108 (1438, 21000, -522) 63 |
| R7d | 1.0 | r1 69 (2261, 21096, -889) 51 ONE STEP 206; r5 104 (-203, 21091, -1302) 89; r4 109 (-1812, 20436, -1280) 109; r6 113 (-1377, 20300, 1038) 119; r3 113 (-1671, 20300, -931) 113; r2 115 (-1289, 20778, -1584) 102 |
| V1 | 1.0 | r3 127 (1014, 19695, -491) 177; r1 136 (2419, 19600, 710) 199; r6 143 (2114, 19696, 164) 191; r5 170 (2542, 19696, 116) 197 |
| I5 | 1.0 | r2 79 (813, 21096, -493); r1 84 (24, 21000, -1161); r7 86 (3260, 21000, 447); r4 92 (604, 21000, -1049); r3 99 (142, 21095, -1106); r6 99 (592, 21094, -626) |

- 30 of the first 34 (T7 .. V1) lie between the reception and the foot of the first flight of stairs, 51..119 m
  of way; I5's six lie in the same stretch.
- **The old chain has no 'control' run.** V1 (crew off stage 1.0) brought all seven to the first floor and lost
  four at the lifts; I5, the same build and the same factor an hour and a half later, lost six on the third floor
  by GO+99. What a gates run has to be held against is the spread V1 .. I5, not one of them (the first form of
  this note called V1 the control: wrong).

### 1.3 The one-step kills (not this track's question)

T7 record 4: 236 of 252 in one step at (2032, 21000, -846); R7d record 1: 206 at (2261, 21096, -889). Both the
first bot at the reception's south-west corner. Cause NOT found. None in G1 or I5.

### 1.4 G1_DM09: the first gates build, live (the lead's run, 09:31..09:38; hook test_climb1, idle player, Escort=1, BoardAll=1, Log=2)

Its archive line: `f06\f06_main.zip ... 218935710 bytes` = `z_rooms\round1\retomoto_full`. 370 s, clean exit, no
fault, no assert: 49 `TriggerActorsDead` nodes load and run.

**The gates' clock, by the escort.** The hook holds record 6 beside the idle player; his chain runs on without
him (as in T7), and each `escort: record 6 re-pointed .. its route place (x, y, z)` line comes a few seconds
after his next step has started. His route places are his squad's holds of the first form, in order:

| GO + s | route place | = | the wait before it took at most |
|---|---|---|---|
| 30.6 | (5447, 20996, 184) | the loot place | - |
| 60.1 | (4097, 20996, -345) | door | (the loot wait: 29.5) |
| 96.6 | (2025, 21000, -135) | reception | door 36.5 |
| 105.1 | (911, 21000, 519) | atrium | **reception 8.5** |
| 140.1 | (631, 21000, -654) | gallery | atrium 35.0 |
| 174.6 | (-589, 20300, -1884) | floor2 | gallery 34.5 |
| 208.6 | (-1995, 19601, -1218) | floor1 | floor2 34.0 |
| 242.6 | (1148, 19601, 299) | lobby | floor1 34.0 |
| 276.6 | (2410, 19601, 396) | the car | lobby 34.0 |

- So a wait of his is armed although he never comes near the hold (why his steps count as reached was not
  read; the hook's order is the suspect), and it fires by itself: **30 s + the few seconds to the hook's next
  line, six times of seven.** The 30 s of section 3.1 is what runs in the game.
- One gate was WON: the reception's seven men (the two who sneak in from the atrium and the reception's own
  three, named a second time) were dead 8.5 s after his wait was armed. They come to the seven; the others do
  not.
- His is the EARLIEST clock of each gate (he does not walk). The other six arm theirs when they get there.

**Where the six were hit** (their 'lost' lines; no place log on this map, section 7.3):

| GO + s | floor | health lost | hits |
|---|---|---|---|
| 0..30 | third (the boardroom) | 113 | 18 |
| 90..180 | third (reception, atrium, gallery) | 553 | 74 |
| **180..210** | **second** | **677** | **73** |
| 180..240 | second / third, the rest | 142 | 11 |
| 210..330 | first | 1,298 | 118 |

- Nobody is hit between GO+30 and GO+98: the door's hold is quiet, and the full 252 are back by the reception.
- **GO+180..210, the second floor, is the worst half minute of the run**: the four who came down the first
  flight (records 1, 2, 5, 7) lost 82 + 61, 212 + 76, 156 and 81 on its last steps and on the 20 m east to the
  hold - past the men the gate names, as the review said (D4). None died of it; record 5 was down to 96 and had
  242 again 42 s later.
- Deaths: r4 GO+175 (138, 21096, -1089) - AT his gallery hold (134, -1094), shot there for 16 s (236 -> 0)
  while his wait ran; r3 GO+189 (-1966, 20393, 275) - on the second floor's WEST side, north of the stairs, 251
  -> 0 in 5.7 s by hits of 18..23: first hit at (-1929, 20300, 375) and moving SOUTH, so he had come down
  another way than this module's stand-in path (the north flight; not seen, his 60 s before are without a hit)
  and walked, alone, past the posts of `2nd RightCharge` (shotgun, SMG), whom no gate of the first form waited
  for; r5
  GO+249 (-838, 19600, -1038) and r1 GO+295 (-471, 19714, -536) on the atrium floor, walking from the floor1
  hold to the lobby hold after that gate had run out, 3..5 m from posts of `CoverMiddle_01` and `PillarCover`;
  r7 GO+313 (2241, 19601, 341) at the lifts; r2 GO+323 (744, 19600, 452), 2..3 m from the posts of
  `010_Squad_Elevators` and `PillarCover`, on his way from the lobby hold to the car.
- So: one death at a hold, one off the way, four on a leg BEHIND a gate that had run out.
- Bots were hit metres from their hold and at other cover boxes than the plan's: record 4 at (277, 876), 5.7 m
  from his atrium hold, beside `CoverBoxh_22` - and inside `Trigger_RecepLeftGoRight`, a box the stand-in way
  keeps out of. A hold is where a bot is SENT, not where it stays; and the way it takes is the game's, not the
  stand-in path's. Every rule here that speaks of a hold place or a way is an approximation by that much.

## 2. The tower's fights (MEASURED on the build; the same level in every build of this track)

### 2.1 The way

Three floors (y 21000, 20300, 19600) on one navigation part of 359 polygons. Third floor, east to west:
balcony (x 5900..6100) - boardroom (3430..5850, the table in its east half) - door (x 3430, z -400..200; the
mesh has a hole at x 3390..3600, z -340..140 there: something stands in the doorway's inner side) - reception
(1900..3400) - the atrium's mouth (850..1900) - the atrium, a ring gallery round an open well (middle (-700,
-100), gallery 12..19 m out). Both flights of stairs run down WESTWARD side by side along the ring's south
side: third floor (x -700) -> second floor's WEST end (x -1825) -> back east along its gallery to x -680 ->
second flight -> first floor's west end (x -1840). The ring has the same two flights on its north side. First
floor: the atrium's whole floor, then a passage (x 1300..2100, z about +-250) to the lift lobby (2100..2700),
the tower car at (2972, 19730, 909).

### 2.2 The squads (24 squads, 45 men; every one `ZSquadScript` field 3 = 0: asleep until a rout of theirs is named)

Row = `ZSoldier` field 4 (accuracy, per cent) and 7 (health), `eCustom` unless said. POSTS = where a squad's
men stand at the load and every place a behaviour of theirs names (`kl_fa_bots_rt.enemy_posts`).

| squad | men | weapons | accuracy, health | they stand | their routs send them to | woken by | gate |
|---|---|---|---|---|---|---|---|
| `020_Office!Squad_Guards_Inside_01` | 2 | 2 pistols | 50, 100 | (5770, 21011, -347) (5122, 20993, 308) | flank (3700, 700) (3700, -900) | the blast timer | room |
| `020_Office!Squad_Guards_Inside_03` | 3 | 3 pistols | 50, 100 | x 3618..3699 | flank (3100, 900) (3100, -1100); unleashed 6 s later | the blast timer | room |
| `020_Office!Squad_Guards_Inside_02` | 4 | 4 SMG | 50, 175 | x 3596..4101 | flank (3300, 500) (3300, -700) | the blast timer | room |
| `030_Reception!Squad_ShootBeforeStorm` | 2 | 2 SMG | 50, 175 | (3033, -8) (2917, -189) | (3218, -77); attitude eUnleashed | `tb_LEFT_TheySpotYou` | door, reception |
| `030_Reception!Squad_Hallway#01` | 2 | 2 FN SCAR | **75**, 175 | (3109, -1137) (2961, -990) | flank (3332, -258) (3330, 47): the door's jambs | `tb_LEFT_TheySpotYou` | door, reception |
| `030_Reception!Squad_Hallway` | 1 | shotgun | 50, 175 | (2961, -990) | (2926, -920) | `tb_LEFT_TheySpotYou` | door, reception |
| `040_Atrium_3rd!Squad_AtrTop_Reception` | 2 | 2 pistols | 50, 100 | (-502, 21004, 1384) (-254, 21005, -1397) | walk (1605, -91) -> (1945, -74) -> (3218, -33) = the boardroom's door; hunt box (1631, -65) | `tb_RIGHT_TheySpotYou`, its own box x 2603..2803 | reception |
| `..!Atrium_3rd_RecepRCharge_Squad_01#01` | 2 | shotgun, SMG | 50, 175 | (-1901, 21008, -1542) (-869, 21006, -1899) | (-220, 21009, -1683); then down to (-2125, 20304, -843) | `TriggerBox_EnterAtrium`; `Trigger_2ndFloorStairs` | atrium, gallery, floor2 |
| `..!Atrium_3rd_RecepSneakup_Squad_01` | 1 | SMG | 50, 175 | (-1304, 20302, -1883) | walk (-1887, 20303, -1174) -> (-603, 21001, -1623) -> (-1791, 21002, -842) | `TriggerBox_EnterAtrium` + 3 s | atrium, gallery |
| `..!Atrium_3rd_RecepSneakup_Squad_01#01` | 1 | pistol | 50, 100 | (-1249, 20303, 1703) | walk (-1928, 20302, 992) -> (-541, 21004, 1394) -> (-1771, 21003, 500) | `TriggerBox_EnterAtrium` + 3 s | atrium |
| `..!Atrium_3rd_RecepRCharge_Squad_01` | 2 | 2 pistols | 50, 100 | (-1812, 20301, 1414) (-1571, 20302, 1563) | (-2017, 20301, 987); then up to (-1863, 21002, -1171) | `TriggerBox_EnterAtrium`; `Trigger_RecepRightGoLeft` | gallery |
| `..!Atrium_3rd_RecepLCharge_Squad_01` | 2 | SMG, pistol | 50, 175 / 100 | (-1110, 20302, -1950) (-1563, 20302, -1796) | (-2018, 20305, -1234) = where the first flight ends; (-2082, 21006, -838) only by the NORTH box | `TriggerBox_EnterAtrium`; `Trigger_RecepLeftGoRight` | floor2 |
| `050_Atrium_2nd!..LeftCharge_Squad_01` | 2 | 2 pistols | 50, 100 | (-2209, 19601, -1315) (-2099, 19602, -1422) | flank (-2252, 20303, -587) (-2498, 20303, -811) | `TriggerBox_EnterAtrium` | floor2 |
| `050_Atrium_2nd!..RightCharge_Squad_01` | 2 | shotgun, SMG | 50, 175 | (-2190, 19604, 1136) (-2109, 19604, 1230) | flank (-2257, 20303, 401) (-2522, 20303, 511): the second floor's north-west | `TriggerBox_EnterAtriumFurther` | floor2 |
| `050_Atrium_2nd!..LeftBehindStairs_Squad_01` | 1 | pistol | 50, 100 | (-553, 19603, -1946) | walk (-1847, 19602, -1002) -> (-647, 20302, -1746) -> (-1, 20305, -1137); (498, 20303, 369) | `Trigger_2ndFloorStairs`; `Trigger_2ndLeftGoRight` | floor2 |
| `050_Atrium_2nd!..RightBehindStairs_Squad_01` | 2 | pistol, SMG | 50, 100 / 175 | (-417, 19603, 1773) (-592, 19603, 1762) | walk (-1918, 19602, 852) -> (-536, 20304, 1347) -> (4, 20304, 1011); (583, 20304, -574) | `Trigger_2ndFloorStairs`; `Trigger_2ndRightGoLeft` | none |
| `060_Atrium_1st!..CoverMiddle_Squad_01` | 2 | SMG, pistol | 50, 175 / 100 | (2256, -902) (2275, -1195) | flank (117, 19623, 279) (-232, 19626, -339) | `Trigger_2ndFloorStairEnd` | floor1 |
| `060_Atrium_1st!..CoverMiddle_Squad_02` | 2 | SMG, pistol | 50, 175 / 100 | (2256, 951) (2275, 658) | flank (-820, 193) (-859, 527) | `Trigger_2ndFloorStairEnd` | floor1 |
| `060_Atrium_1st!..PillarCover_Squad_01` | 2 | shotgun, pistol | 50, 175 / 100 | (2671, 1287) (2449, 1319) | flank (246, -920) (245, 759) | `Trigger_2ndFloorStairEnd` | floor1, lobby |
| `060_Atrium_1st!..InfrontElevator_Squad_01` | 1 | pistol | 50, 100 | (2652, 694) | walk (1931, -113) -> (-581, 754) -> (-2445, -121): across the whole floor to its west end | `Trigger_2ndFloorStairEnd` | floor1, lobby |
| `070_Elevators!010_Squad_Elevators` | 3 | shotgun, 2 pistols | 50, 175 / 100 | (2340, 1238) (2534, 882) (2604, -1063) | flank (919, 488) (873, -788) | `Trigger_1stFloorStairEnd` | lobby |
| `060_Atrium_1st!Squad_MG-Guy` | 1 | machine gun | 30, **300**, eRegular (so accuracy 50) | (2908, 19601, -68) | (2005, 19603, -16), eDMS_Run: the passage's lift end | `TriggerBox_PreLastTrigger` | lobby |
| `070_Elevators!010_Squad_Elevators_GuardingElevator` | 1 | SMG | 50, 175 | (2484, -1554) | (2330, -1042) | `TriggerBox_PreLastTrigger` | none |
| `070_Elevators!020_Squad_Elevators_Last_Stand_02` | 2 | SMG, pistol | 50, 175 / 100 | (2675, 959) (2461, -1239) | flank (2261, -524) (2238, 334) | `TriggerBox_OpenExitElevator` | none |

### 2.3 The trigger boxes on the way (`ECPS_FA_MERCONLY` but the one marked; world boxes)

| box | x | z | y | wakes (or sends on) |
|---|---|---|---|---|
| `Gameplay!010_FirstFight!tb_LEFT_TheySpotYou` | 4140..4260 | -1300..1100 | 20950..21450 | the reception's three squads |
| `Gameplay!010_FirstFight!tb_RIGHT_TheySpotYou` | 3370..3490 | -400..200 | 20950..21450 | `Squad_AtrTop_Reception` (the boardroom's door) |
| `040_Atrium_3rd!Squad_AtrTop_Reception\TriggerBox` (ECPS_BOTH) | 2603..2803 | -1306..1093 | 20986..21286 | the same squad, alerted |
| `040_Atrium_3rd!TriggerBox_EnterAtrium` | 1434..1634 | -1294..1105 | 20926..21426 | RCharge#01, RCharge, LCharge, both Sneakups (3 s later), 2nd LeftCharge: 10 men |
| `040_Atrium_3rd!TriggerBox_EnterAtriumFurther` | 572..772 | -1694..1505 | 20986..21486 | 2nd RightCharge. It lies across the whole mouth of the ring: no way round it |
| `040_Atrium_3rd!Trigger_RecepRightGoLeft` | 4..603 | -1748..-953 | 20991..21491 | RCharge comes up to the third floor |
| `040_Atrium_3rd!Trigger_RecepLeftGoRight` | -2..533 | 759..1588 | 20993..21493 | LCharge comes up (the north gallery: not on the stand-in way; G1's record 4 was in it) |
| `050_Atrium_2nd!Trigger_2ndFloorStairs` | -977..-877 | -2094..1905 | 20918..21518 | RCharge#01 goes down; the two BehindStairs squads come up to the second floor |
| `050_Atrium_2nd!Trigger_2ndFloorStairEnd` | -2098..-1698 | -2120..1879 | 20280..20880 | the first floor's four squads set out for the atrium floor (BOTH first flights END in this box) |
| `050_Atrium_2nd!Trigger_2ndRightGoLeft` | -1145..-815 | -2130..-1235 | 20185..20685 | RightBehindStairs moves |
| `050_Atrium_2nd!Trigger_1stFloorStairEnd` | -1930..-1530 | -2120..1879 | 19584..20184 | `010_Squad_Elevators` (the second flight ends in it) |
| `070_Elevators!TriggerBox_PreLastTrigger` | -35..364 | -2168..1831 | 19591..19891 | the machine gun, GuardingElevator |
| `070_Elevators!TriggerBox_OpenExitElevator` | 1949..2149 | -1509..1290 | 19590..19890 | Last_Stand_02; the car's doors; and the STREET's `Squad_Teargasguys` through `Enemies!020_Street!Timer` |

That bots trip these boxes is MEASURED: with an idle human the squads behind them killed bots in every run.

### 2.4 The lobby / street half (read only; `kl_fa_street.py report`, `<work>\build\z_rooms\checks_full\street_report.log`)

The bots' street chain (14 stations, about 215 m of path from the lobby car, the east pavement x -850..-1000):

| m of way | what the first criminal there starts | squads / men |
|---|---|---|
| 0 | `Mercenaries!TriggerBox_1_LeaveElevator` (x 5801..6001: the [CrewJoin] places lie inside it) | `Squad_InFront` 3 run to their police car; 5 s later `Squad_Teargasguys` 2 |
| 33 | `Gameplay!030_AfterLoot!tbExitFinancialAlley` (the front door) | `Squad_InFront` holds tight |
| 75..80 | `Gameplay!020_Loot!tbExitLoot` (x -1100..-500, z -11900..-1100: the first step on the road's east side) | wave 1: five F07 squads, 10 men, in the traffic north; from BEHIND four campaign squads, 11 men |
| 83 | `021_FinancialAlley_Dog\tbReleaseDog` (z -3600..-3000) | wave 2: the road block at z 3600..3900, six F07 squads 13 men, the dog, four campaign men |
| 137 | `Gameplay!040_Escape!tbEscapeAI` (z 1700..2300) | wave 3: 3 men at the SWAT truck (-3600, 10300) |
| 182 | `Gameplay!RunToEscape!tbRunToEscape1Player` (z 6200..6800) | 20 s + 8 s later every F07 squad walks to its place round the van |
| 192 | the bots' own rally, `070_Timer_rally` 10 s at (-1207, 7995) | - |
| 205.. | the level exit box (z 8300..12800): stage 3, the van is called; `tbCountPlayers` (z 9200..9800) unleashes wave 3 | - |

47 enemy actors; 13 squads have a fall-back list (field 8). NOTHING of this half is changed and no gate
stands on it: why, section 9.

## 3. The device

### 3.1 `TriggerActorsDead` (READ: `ZTriggerActorsDead` slots 26 / 25 = 0x4afb80 / 0x8def80; the test 0x5f4470; the review re-derived all of it)

- Fields: 0 = a list of scene paths, 1 = a bool (0 in all stock uses), 2 = the list it sends 'AITrigger' to.
- 'AITrigger' ARMS it - once: byte +0x41 armed, +0x42 spent, both make it deaf - and sets a deadline
  **0x7800 ticks = 30.0 s** ahead (0x4afbbd; a tick is 1/1024 s).
- Its update runs only in session state 0x19 and sends the list when EVERY entry is dead **or the deadline has
  passed** (0x8df00b); then it is spent for good. An empty list fires at once.
- Dead (0x5f4470): no object -> dead; an actor -> state byte `actor+0x576` is 0; a group -> dead as soon as
  ONE actor below it is. So an entry must be a group with ONE actor: what all 120 stock uses name.
- The state byte (`ZActor` slot 354, 0x7e72d0): **0 dead; 1 in play** (written when an actor is entered in the
  game's table of actors, 0x546eca, and by the heal action); **2 going down** - `ZBecomeRagdoll` passes 2
  (0x6772ad) and 0 once the man is dead (0x677504, 0x677a12). So a man who is DOWN and not dead holds a gate
  until then. What an actor of a squad that has not been woken holds was not read; most likely 1. Not dead
  either way: **naming a sleeping squad costs the whole 30 s** (the first form of this note said 'state 2 = not
  in the world': wrong word, same conclusion). The plan and the check hold every gate to squads its own way
  wakes.
- **ARMED is not ARRIVED.** A hold step sends its list when its Defend goal calls the place reached, and that
  is **within 10 m of it in 3D** for a step like ours (0x686c4c: radius 1000.0 unless goal +0x40 is 1; goal
  +0x40 is the rout's second enum member - ASSUMED field 5, `eDF`, which is `eDF_NotSet` on every step here).
  So the 30 s start up to 10 m before the hold; where a bot's next hold lies within 10 m of the last, at the
  last (door 2 of the seven, reception 1, gallery 3: 1..4 s early); and **no clock runs for a bot that never
  comes within 10 m of its hold** - as in stock. The floors are 7 m apart and the foot of the second flight
  lies under the foot of the first: the plan pairs bots and holds so that no hold on another floor is within
  10 m of the bot's place before (a wait armed a stair's way early would have run a third of its time).
- Stock model, cloned field for field: F07 `Gameplay!merc_bot_squad!Squad#02\020_TriggerActorsDead_Lootarea`
  (a ZBoxPrimitive), behind `020_DefendBehaviour_rout_merc_fight_left`.

### 3.2 What starts once (READ)

| node | routine | what was read |
|---|---|---|
| `DefendBehaviourRout` | slot 26, 0x4ebed0 | **'AITrigger'** ([0x168d804]) starts it unless byte +0x41 (set by 'AIBlocker', [0x168d800]) or (+0x42 and +0x40): +0x42 is **field 8**, +0x40 'was started'. Field 8 is 1 on every step of ours and of stock: a step is started by 'AITrigger' once. Two more messages: the one whose id is at [0x168d844] starts it with NO test, the one at [0x168d850] makes it send 'AITrigger' to its own list. Both are objects of 0x6fb080 (name, id), made at 0xafff20 / 0xafff40: **'DebugTrigger' and 'DebugTriggerSignals'**. No sender of either was found |
| `TriggerDelay2` | 0x71e250, 0x744c30 | armed once (+0x49), deaf while armed; delay = field 0 + field 1 x random; after firing: field 2 < 0 -> spent (+0x4a), else deaf for field 2 seconds |
| `TriggerCounter` | 0x541220 | EVERY 'AITrigger' counts, whoever sends it; at 0 it sends its list; field 1 < 0 -> dead (+0x4c = 0). So `Counter_room_clear` {1, -1, 0, 0} fires once |
| `JumpPoint` | 0x72e0f0 | sends 'AITrigger' to the entries of its list **in the list's order**, index 0 first (the loop at 0x72e110..0x72e152) |

So a late wait cannot pull a bot back to a hold it has left. It CAN start the step behind it - which is the
join's hazard (9.1).

### 3.3 Why not the room's counter form for these gates

The brief asked for 'a counter fed by exactly the squads of that fight, the form the room counter has'. Not
built, for three reasons:

1. `kl_fa_bots.check` (not this track's file), `kl_fa_bots_rt.check` and `kl_fa_bots_dyn` walk a bot's chain
   through behaviour and wait controllers only. A `TriggerCounter` BETWEEN two steps ends the walk.
2. A `TriggerActorsDead` is the stock bots' own answer to 'these men first', carries the fall-back itself,
   and needs no edit of an enemy squad (the counter form writes field 8 of 19 Dead Men squads).
3. `kl_fa_bots_dyn` keeps such a wait as it is and re-points only its field 2.

What it costs: the fall-back cannot be made LONGER than 30 s. It could be made shorter - a `TriggerDelay2`
beside the wait in the hold step's list - and is not: that is a timer behind the loot wait of a chain the jump
cuts off, which `kl_fa_bots_dyn.check` FAILs for the reason of 9.1. And each bot waits from ITS OWN arming, so
where a gate runs out the seven leave apart by as much as they came apart, and **the last to come is left
alone at the hold** (G1: record 4, dead at his gallery hold 17 s after he got there). A remedy is sketched in
9.4 and not built.

## 4. The gates (as built; `GATES` in `tools/kl_fa_bots_rt.py`)

| # | gate | the seven hold at (x, z; y) | cover boxes (in reach of a hold) | m of way from the balcony | the seven ways to it, m | boxes on the way | its wait names (men) | nearest post of a man who may be alive, m |
|---|---|---|---|---|---|---|---|---|
| 0 | room (as before) | the balcony | - | 0 | - | - | the room counter: `020_Office` x 3 (9); fall-back blast + 75 s | - |
| 1 | door | 3570..4099, -1118..313; 20995 | 4 (4) | 34..46 | 11..25 | `tb_LEFT_TheySpotYou` | Hallway#01, ShootBeforeStorm, Hallway (5) | 4.7..9.2 |
| 2 | reception | **2067..3090**, -950..749; 21000: its east half | 5 (9) | 52..82 | 14..43 | `tb_RIGHT_TheySpotYou`, AtrTop's own box | AtrTop_Reception + the reception's three again (7) | 3.5..8.9 |
| 3 | atrium | 837..919, -964..763; 21000: both sides of the mouth | 2 (2) | 92..105 | 18..43 | `TriggerBox_EnterAtrium` | RCharge#01, both Sneakups (4) | 12.8..17.0 |
| 4 | gallery | 134..637, -1094..-644; 21000: the south gallery | 2 (2) | 102..122 | 6..24 | `EnterAtriumFurther` (no way round), `Trigger_RecepRightGoLeft` | **RCharge, RCharge#01, Sneakup (5)** | 6.9..13.5 |
| 5 | floor2 | **-1935..-740, -1614..-1055; 20300: AT the foot of the first flight** | 3 (4) | 139..160 | 37..43 | `Trigger_2ndFloorStairs`, `..StairEnd` (the flight ends in it), `..RightGoLeft` | **LCharge, 2nd LeftCharge, 2nd RightCharge, RCharge#01, LeftBehindStairs (9)** | 3.1..5.3 |
| 6 | floor1 | -2085..-1012, -1341..-130; 19600: the foot of the second flight | 3 (10) | 179..206 | 28..48 | `Trigger_1stFloorStairEnd` (the flight ends in it) | **CoverMiddle x 2, PillarCover, InfrontElevator (7)** | 3.6..12.8 |
| 7 | lobby | -203..1157, -764..603; 19600: the boulders, the show cases, the pillars at the passage | 6 (9) | 202..227 | 21..35 | `TriggerBox_PreLastTrigger` | **the machine gun, `010_Squad_Elevators`, PillarCover and InfrontElevator again (7)** | 3.0..9.3 |
| - | the tower car | 2317..2497, 397..577; 19601 (kl_fa_bots' own places, in the AllyEscapeBox) | - | 238..263 | up to 36 | `TriggerBox_OpenExitElevator` | none: tight defence, the end of the tower chain | - |

Bold = changed against the first form. Fall-back of gates 1..7: 30 s each from the arming (3.1). Every hold:
80..226 from the middle of its cover box, 113 or more from the next bot.

### 4.1 The rules a hold is laid by (`gates_plan`, `hold_spots`) and read back by (`check`, section 2b)

1. A place 70..230 from the middle of a cover box inside the gate's search box (GUESS, per gate), on a flat
   polygon of the bots' mesh part, 35 from a wall.
2. **In no trigger box of a LATER fight - and no cover box within 500 of it has a place of its standing ring
   in one** (the box's middle and 16 places on each of four rings out to 270). `DefendCover` takes ANY cover
   within 500 of the defend position and picks the side itself (the review's D3: the first reception hold was in
   reach of three boxes whose west side lies in `TriggerBox_EnterAtrium`, ten men - the sheltered side against
   the reception's own). 137 of 180 places at the reception fall to this rule; what is left is its east half.
   Two exceptions, both said by the check: a box the seven **cannot go round** - a stair ends in it, or it lies
   across every way (`cannot_go_round`; GATES names it under `cross` and the plan holds the name against the
   mesh) - is tripped before anybody holds; and a box whose men have **no post on the hold's floor** only gets
   a NOTE (the atrium's two show cases reach into `EnterAtriumFurther`, which wakes two men who take places
   one floor down; there is no other cover at the mouth).
3. **300 from every post of a man who may be alive** (review D4: two holds of the first form were 0.3 m from
   one; the campaign posts its men at the same cover boxes). 'May be alive' = every squad but the room's and
   those an earlier gate has waited for and this one does not name again. 61 of 113 places fall to it at the
   foot of the first flight, 105 of 289 at the lobby.
4. **No way to a hold walks PAST a post of a man this gate waits for** and no earlier gate has dealt with:
   within 6 m of it on its floor and then more than 10 m further (`passes`; review D4: floor2's first hold lay
   20..26 m beyond such men). 'Dealt with' = an earlier gate named the squad and has a hold on the post's floor
   within 25 m of path. Which posts count on a leg (`posts_then`): a squad woken by an earlier leg stands at
   the END of its routs; one this leg wakes, at its start places and the FIRST place of a walked rout - the
   campaign's sneak-up routs end behind the seven (`Squad_AtrTop_Reception`'s at the boardroom's door).
5. One bot a box while boxes last; the pairing of bots and holds with the least sum of distances.

**Where a stair leaves no room short of the fight, the hold is AT it.** Both flights end among the men of the
floor below (`LCharge`'s post is 2 m from the foot of the first, the pillar there is their cover box). The
review offered two ways for the first flight: a hold at its head tested against the collision, or the sprint
back on that leg. Neither was taken:
- at its head no straight line on the mesh reaches any post at its foot from any of 38 + 64 + 25 places at the
  three cover boxes there (the flight follows the ring), the collision itself is not read by any tool here,
  and two of those boxes reach into `Trigger_2ndFloorStairs`;
- a sprint through, to a hold 20 m beyond, leaves nine living men above the second flight and above the
  atrium floor, where G1 lost two more.
So floor2's seven stop at the first cover at the foot: two at the pillar beside it (3.1 and 4.1 m from
`LCharge`'s post), three at the next pillar (3.7..5.3 m), two 11 m east. From there 8 of the 11 posts of that
gate's squads on that floor have a straight line on the mesh from a hold. **This is the riskiest choice of the
second form** (GUESS that seven in cover at 3..13 m win that fight; in G1 they walked through it and lost
81..288 each without a death) - section 7 says how a run tells.

### 4.2 Who a gate names, and what G1 took out

- A squad whose posts are all out of reach of the holds makes the wait a 30 s pause for nothing - and a bot
  that waits is a target. G1: the first gallery gate named `LCharge` and `2nd LeftCharge`, one floor down
  across the well; it ran out and record 4 died at his hold meanwhile. They are floor2's now, whose hold is at
  them. The check NOTEs a squad none of whose posts is on the holds' floor within 25 m of path ('OUT OF
  REACH'); no gate has one now.
- `2nd RightCharge` (shotgun, SMG; the second floor's north-west, 9..13 m from the foot of the first flight)
  was waited for by no gate; G1's record 3 died to them. Floor2 names them.
- `InfrontElevator`'s one man walks the whole atrium floor and ends 3.6 m from a floor1 hold: he is floor1's
  (and the lobby's again). `010_Squad_Elevators`, woken as the second flight ends, take places 21..30 m east,
  3 m from the lobby's holds: the lobby's.
- `GuardingElevator` (one man, round the corner in the lift lobby, no hold within 25 m of path) is no longer
  named by the lobby: he made the LAST wait before the car one that can only run out - and the one most likely
  to be armed when the human takes the join.
- Woken on the way and waited for by NO gate (the check says it): `RightBehindStairs` (2, the second floor's
  north side), `GuardingElevator` (1) and `Last_Stand_02` (2) at the lifts, where the seven end in tight
  defence, and the street's `Squad_Teargasguys`.
- The check also says which squads of a gate have NO post with a straight line on the mesh from a hold - the
  only line of sight that can be had offline (true = no wall, drop or floor between; false = not known: a line
  across open air or past a prop is not one on the mesh): door `Hallway#01`, `Hallway` (they come to the
  doorway); atrium `RCharge#01`; gallery `RCharge`, `RCharge#01`; floor1 `CoverMiddle` x 2, `PillarCover`.
  G1: door, atrium, gallery and floor1 all ran out.

### 4.3 With `kl_fa_bots_dyn` on top (`retomoto_full_r`)

What the dynamic step adds on the tower's way out is **only**: the way between two holds forks (0..3 forks a
bot, 14 in all - and 29 on the street; another way goes through no trigger box the build's way keeps out of,
and past no post of an enemy the build's way keeps clear of), the starts are 0 / 3 / 5 / 8 s apart, the opening
modifier. **No hold and no timer of its own behind the loot table** (the first `_r` had 36 such holds of
4..12 s, 25 of them within 6 m of an enemy's post: review D2), and nobody's wait at the table is cut to 15 s
(the point man and the runner would be 15 s ahead at every gate). The gates' holds and waits are the gates
build's own, place for place. On the way IN (the boardroom) and on the street it holds at cover as on every
other map.

## 5. What changed

### 5.1 `tools/kl_fa_bots_rt.py`

First round:
- `GATES`, `gates_plan()`: the tower's way out of `kl_fa_bots.plan` is laid anew behind the loot station:
  hold of gate 1 -> .. -> hold of gate 7 -> the place beside the car. Steps `030_DefendBehaviour_out_door`
  .. `036_.._lobby`, `037_.._car`; `Street.gate_nodes()`: behind each hold step `03n_TriggerActorsDead_<gate>`
  {0: the actor groups, 1: 0, 2: the next step}; no sprint on that way.
- Options: `--no-gates` = the chain as rt_full7 has it (its archive is rt_full7's byte for byte, section 6.4).
  `--gates a,b,..` = only these gates: the way between two that are left is then ONE order without sprint and
  without way places (to `floor1` alone: 138 m from the table), so this is NOT 'the old chain with fewer
  gates' (the first form of this note offered it as that: wrong).
- `check()` section 2b reads the gates back from the nodes (every branch set of a forked chain); the repair of
  5.3.

Second round (the review):
- New: `enemy_posts`, `posts_then`, `near_post`, `ring_points` / `ring_in`, `reach_covers`, `mesh_line`,
  `passes`, `stair_end` / `cuts_off` / `cannot_go_round`; `hold_spots` takes the rules 2 and 3 of 4.1,
  `gates_plan` rule 4 and the pairing rule of 3.1 (`assign`), and says per gate what it refused and why.
- `GATES`: the reception's box reaches east to x 3150; floor2's box is the foot of the first flight; the
  squads of gallery, floor2, floor1 and lobby as in 4.2; `cross` for the gallery (`EnterAtriumFurther`).
- `check()`: FAILs a hold within reach of a cover box with places in a later fight's box, a hold within 300 of
  a post of a man who may be alive, a way (every way of every fork) that walks past a man the gate waits for;
  NOTEs squads out of reach, squads without a straight line on the mesh, a wait armed a stair early, covers that
  reach into a box of men of another floor, and **'THE JOIN'** (9.1) with the number of waits a bot has. The
  text about 'actor state 2' is corrected.
- **One rule of the first round is NARROWER now, on purpose - say so if it is not wanted:** 'a hold INSIDE the
  trigger box of a later fight' (FAIL) no longer applies to a box the seven cannot go round. The check measures
  that itself on the mesh (`cannot_go_round`: a stair ends in the box, or closing the polygons the box touches
  leaves no way to a hold outside them); it does not take the plan's word. Without it two of floor2's holds,
  which stand in `Trigger_2ndFloorStairEnd` at the foot of the first flight, would FAIL (and the new ring rule
  would FAIL the cover box of one of floor1's, which reaches into `Trigger_1stFloorStairEnd`); and two of the
  gallery's stand in `EnterAtriumFurther` as they did in the first form, where that box woke nobody a gate
  waited for. The planted fault `inbox` (the reception's holds
  in `TriggerBox_EnterAtrium`, which CAN be gone round: it is entered only by going there) still FAILs.

### 5.2 `tools/kl_fa_bots_dyn.py` (all five only where a chain has a `TriggerActorsDead`; the plan of the five builds without one is the committed module's byte for byte, 6.4)

1. No cover hold of its own at a place a `TriggerActorsDead` follows (first round).
2. Another way of a fork goes through no trigger box that wakes an enemy squad and that the build's own way
   keeps out of (`Routes.wakes_more`, first round).
3. **'The last loot wait' of a chain the jump cuts off is the TABLE's wait, not the last gate**
   (`last_loot_wait`; review D1 / D2). A gate counted as a loot wait; the rule 'no timer behind the last loot
   wait of a chain that the jump cuts off' therefore guarded the last leg alone, the step put 36 timed holds
   between the gates and its own check passed them. Now `post` is true from the table on: no hold, no timer.
   `check()` uses the same reading, FAILs such a timer again (the first `_r` build: 14 FAIL lines, 6.4), and
   NOTEs the build's own gate waits as the same hazard ('THE JOIN').
4. Another way of a fork comes within 6 m of no post of an enemy that the build's way keeps clear of, and
   walks on no farther past one (`Routes.passes_more`). First try on the second gates build: the runner's way
   to his lobby hold went 2.9 m from a place of `PillarCover` and 11 m on; `kl_fa_bots_rt.check` FAILed it.
5. Nobody's loot wait is cut short when gates follow it (4.3).

### 5.3 A fault of the room-gate edit, repaired (first round)

Since the room gate (be66e7b) `kl_fa_bots_rt.check` took the first steps from `Timer_start_bots`' own list,
which is the gate alone; it found no chain in any squad and skipped 'the last tower place is in or at the
jump box / in no AllyEscapeBox' without a word. They run now; a squad without a started chain is a FAIL.

## 6. Builds and checks

### 6.1 How they were made (`<work>\build\z_rooms\checks.txt` is the run's own record; logs in `z_rooms\steps\`)

Base = the pre-bots base of rt_full7: `<work>\build\rt_full6\1_guns`. Every step as rt_full7's:

1. `kl_fa_bots_rt.py build <1_guns> z_rooms\steps\2_bots` - 367 entities added.
2. `kl_fa_talk.py build 2_bots 3_talk --map retomoto`.
3. `kl_bain.py build 3_talk 4_bain --stream <work>\build\v_talk\str\PC_Def.str`; the stream file it wrote was
   rt_full7's byte for byte (= the installed one) and was DELETED again (1.7 GB): `kl_bain.py check <build>
   <work>\build\rt_full7\PC_Def.str`.
4. `kl_fa_bots_dyn.py fake-fix 4_bain z_rooms\retomoto_full` - 2 FakeTarget controllers off, nothing else.
5. `KLTalk.ini`: the two delays of rt_full6 (6.3).
6. `kl_fa_bots_dyn.py build z_rooms\retomoto_full z_rooms\retomoto_full_r` (defaults: routes, no fork gap).

### 6.2 The checks (last line of each)

| check | `retomoto_full` | `retomoto_full_r` |
|---|---|---|
| `kl_fa_bots_rt.py check` | `RESULT (kl_fa_bots_rt): PASS (0 FAIL, 9 NOTE); start delay 91.5 s after a blast at 16.5 s; 7 gate(s) on the tower's way out; jump list 7; [CrewJoin] places 7` (and kl_fa_bots: `RESULT: PASS (0 FAIL, 10 NOTE); 7 bots, 367 squad nodes`) | `RESULT (kl_fa_bots_rt): PASS (0 FAIL, 14 NOTE); .. 7 gate(s) ..` (kl_fa_bots: `RESULT: PASS (0 FAIL, 10 NOTE); 7 bots, 1165 squad nodes`) |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 8 NOTE)`; FakeTargets 1, outside the vision space 0; loot window: no place has an object in reach that a bot cannot take | `RESULT (kl_fa_bots_dyn): PASS (0 FAIL, 5 NOTE)`; FakeTargets 1, outside 0; loot window the same |
| archive | 218,935,706 bytes (rt_full7: 218,932,836; the first gates build: 218,935,710) | 218,967,053 bytes |
| `kl_impact.py` | `problems: 0 in 1 levels` | same |
| `kl_map_guns.py check` | `6 guns with looks .. problems: 0` | same |
| `kl_fa_talk.py check` | `FAIL the countdown's NOW! starts at [7.51], the blast is at 16.50`, `findings: FAIL 1, NOTE 0` - the same line `rt_full6\retomoto_full` gives (6.3); as built in step 2: `FAIL 0, NOTE 0` | same |
| `kl_bain.py check` | `26 Bain sounds .. 0 not in PC_Def.str ..; 0 problems` | same |
| `kl_fa_street.py report` | exit 0, 47 actors, 0 with a drawing fault | same |
| large members | .prm 79,879,056, .ANM 21,642,904, .fxc 17,760,648, .WAV 27,802,960 = rt_full7's | same |
| side files | `KLJoin.ini`, `KLGuns.ini`, `KLWardrobe.ini` = rt_full7's byte for byte; `KLTalk.ini` = rt_full6's (sha1 6c78c079) = `z_route4\retomoto_tab_fix`'s as the lead left it at 08:34 | the gates build's |
| `kl_fa_bots_rt.py diff` (2_bots against 1_guns) | `RESULT: only the squad was added` | `kl_fa_bots_dyn.py diff`: `RESULT: only the squad's steps were made anew` |

The 9 NOTEs of the gates build's own check: four gates with squads that have no straight line on the mesh
from a hold (door, atrium, gallery, floor1), two 'a cover in reach has places in a box - not failed' (atrium:
`EnterAtriumFurther`, men of another floor; floor2: `Trigger_2ndRightGoLeft`, which wakes `RightBehindStairs`,
waited for by no gate), the four squads woken and never waited for, THE JOIN, and one street leg near the van
that is no straight line on the mesh (as in rt_full7).

### 6.3 The talk delays

`rt_full6\retomoto_full\KLTalk.ini` (the build the owner heard: 'the bang goes ON Kane's NOW!') has
`countdown Delay=0.30` and `balcony Delay=11.50`, set by hand after the Bain step. `rt_full7\retomoto_full`
and everything made from it had the tool's own `9.29` and `0.60`. Found by this track in the first round; **the
lead put rt_full6's file back** in `z_route4\retomoto_tab_fix`, the tree and the game folder at 08:34 (commit
c99d16c), so the first form's 'on the owner's tab' is no longer true. Both z_rooms builds carry rt_full6's file
byte for byte (G1's log: `talk: scene countdown .. starts at 0.31 s`). `kl_fa_talk.py check` counts the delay
from the round-start event and so FAILs exactly these values, on rt_full6 too: the check's clock is the
fault, not the file (`kl_fa_talk.py` is not this track's).

### 6.4 Proofs beside the checks (`<work>\build\z_rooms\neg_tests\`, `summary.txt` = one line each)

(The planted faults, the first form's builds and the dynamic step's plan with the code as it is at the end of
the round; the two byte-for-byte builds and the reviewer's `rev2` / `rev4` just before its last change, which
narrowed one exemption of one FAIL rule of the check and touches nothing that is built.)

- **The check has teeth**: one planted fault a build, the PLAN made with the rule in question switched off,
  the build written, the check as it is run on it, the build thrown away (scratch `G2\neg2.py`). `control` PASS;
  `asleep` (the door gate also names the machine gun) -> 'no bot's way to its hold goes through a trigger box
  that wakes Squad_MG-Guy'; `partial` -> 'names 1 of the 2 men of Squad_Hallway#01'; `inbox` (the reception's
  holds inside `TriggerBox_EnterAtrium`) -> 'lies INSIDE'; **`ring`** (the reception's holds where the first form
  had them) -> '.. places round that box lie in TriggerBox_EnterAtrium, the trigger box of a later fight';
  **`onpost`** (holds round the place `Squad_AtrTop_Reception` is sent to) -> 'is N from a post of
  Squad_AtrTop_Reception'; **`past`** (floor2's hold where the first form had it) -> 'the hold lies BEYOND'.
  All six FAIL as they must.
- **The first form's builds through the checks as they are now**: `round1\retomoto_full` (the build of G1):
  `kl_fa_bots_rt` FAIL, 21 lines - 7 holds with a cover box in reach that has places in a later fight's box (all
  at the reception), 6 holds within 300 of a post (three at the reception, three at floor2), 8 ways that walk
  past (all seven to floor2, one to the lobby). `round1\retomoto_full_r`: `kl_fa_bots_dyn` FAIL, 14 lines 'timer
  .. runs behind the last loot wait of a chain that the jump cuts off'.
- **The reviewer's own scripts on the new builds** (scratch `Grev\`, run as they are): `rev5.py` on
  `retomoto_full_r`: '0 holds of the dynamic step between the gates' (the first: 36, 25 within 6 m of an enemy
  rout place). `rev3.py`: behind the loot wait a bot's tower chain holds 7 `TriggerActorsDead` and nothing else,
  in both builds. `rev4.py` on `retomoto_full`: reception **0** (the first: all seven holds); its total of 24
  is the three cases the check names and section 4.1 gives the reason for - atrium 7 and gallery 5
  (`EnterAtriumFurther`: men with no post on that floor; for the gallery no way round it), floor2 7 + floor1 1
  (the box a flight of stairs ends in) and floor2 4 (`Trigger_2ndRightGoLeft`: men no gate waits for).
- `--no-gates` is the old chain: its archive is `rt_full7\2_bots`' byte for byte (sha1 c8eb1e86).
- The code as it is builds `steps\2_bots` again byte for byte (sha1 e8e634de).
- The dynamic step is unchanged where no gate is: its plan of `z_gate\M01`, `z_final\M02`, `M03`, `M06` and
  `rt_full7\retomoto_full` by the committed module and by the working tree is the same, byte for byte.

## 7. The live checks

### 7.1 What G1 already answered (the first form; section 1.4)

Loads and runs (old L1). The 30 s is what runs (old L2). Nobody dies at the door or the reception; the full
30 s at door, atrium, gallery, floor2, floor1, lobby (old L5: more than the three candidates). One bot off the
stand-in way, one shot at his hold, four dead on a leg behind a gate that had run out (old L3 / L4).

The review said of the old L2 that an escort who never comes within 10 m of his hold shows a route place that
stands for ever. G1 shows the other thing: his route place went from hold to hold every 34..36.5 s. So his
lines ARE a clock of the gates - the earliest one, because he does not walk - and they say nothing about where
the other six are.

### 7.2 J1: THE JOIN - before anything else, and before either build goes on the tab

`<work>\build\z_rooms\live\J1_DM09_join.ini` (+ `.route.txt`, `.expect.txt`; made by track H's
`tools/kl_playtest.py script .. --until join --linger 80 --build z_rooms\retomoto_full`, NOT RUN): the scripted
player walks record 1's places from the balcony to the tower car, 238 m in 69 way points, never shoots, and is
in the jump box about 111 s after the round's clock starts; the script then stays 83 s. `[Bots] Log=2
Escort=0 BoardAll=0`, `[CrewJoin] Enable=1`, `[CrewHop] Enable=1 Dry=1 Log=2`. It needs Maps\DM09 = the gates
build. For the place lines the map's `KLJoin.ini` must carry a `[CrewHop]` nobody can stand at: the lead's
`live.py --poslog` does not write one for a map that has a KLJoin.ini of its own, so
`z_rooms\live\KLJoin_with_poslog.ini` is the build's file with that block appended (TEST ONLY; the build's own
file stays rt_full7's).

He trips every box and kills nobody, so at the join the seven are spread over the first gates with their
waits ARMED: the case of D1.

| read | says |
|---|---|
| `crewjoin: .. the AI heisters in play are moved first` / `crewjoin: N moved` | N = the bots alive |
| `bots: record N (bot): heist stage 1 -> 2` within about 10 s of the join | its street step has started: the EXITS_BANK box on the lobby's stairs is the street chain's FIRST station, 6 m from where the hook puts the bots |
| `.. heist stage 2 -> 3` within about 75 s of the join | it walked the street chain to the level exit box (190 m and the 10 s rally) - **good** |
| alive at the script's end, 83 s after the join, with stage 2 | its street step was taken from it on the way: a late wait of the tower chain started a tower step - **the gates break the join** (its last 'lost' / `hop:` places say where it stopped) |
| `hop: bot N stage 1: node (x, y, z)` with its arrival place (y about 563) 45 s after the join | its street step never started |

**Said beforehand:** J1 is good if every bot that is alive at the script's end has stage 3 or is aboard; it fails
if it leaves more bots alive at stage 1 or 2 there than the control does. Control **J0**
(`J0_DM09_join_oldchain.ini`, the same walk on `z_route4\retomoto_tab_fix`): the old chain has no wait armed at
GO+111, so J0 says whether the join works for bots AT ALL and how many the street's police stop by themselves -
if J0 fails too, the gates are not what breaks it.

If J1 fails: 9.1 names the two remedies; neither is built.

### 7.3 G2..G4: do the gates of the second form do better than the first

Idle player, the hook and settings of G1, `[Bots] Log=2`, to the round's own end (the session leaves state 0x19
at GO+360 when nobody escapes; G1 was stopped at GO+370). **Three runs**, held against G1 and against the old
chain's spread (V1: four dead, at the lifts; I5: six dead by GO+99).

| seconds after GO | every fight won on arrival | G1 (the first form, the escort's clock) | every wait runs out |
|---|---|---|---|
| in by themselves | 18..21 | 19..29 | - |
| room gate | 20 | by 31 | 43 (fall-back 83) |
| the table, until | 55 | 60 | 78 |
| door reached / left | 61 | 60 / 97 | 84 / 114 |
| reception | 72 | 97 / 105 | 125 / 155 |
| atrium | 83 | 105 / 140 | 166 / 196 |
| gallery | 89 | 140 / 175 | 202 / 232 |
| floor2 | 100 | 175 / 209 | 243 / 273 |
| floor1 | 112 | 209 / 243 | 285 / 315 |
| lobby | 121 | 243 / 277 | 324 / 354 |
| the car | 130 | 277 | 363 |

(GUESS: 4 m/s without sprint; the legs' longest ways: 25, 43, 43, 24, 43, 48, 35, 36 m.) With every wait run
out the car is 3 s past the round's end. In a played round that does not bind: the join moves every bot when
the HUMAN takes the car, wherever it is.

Every record's holds (x, z), to read the 'lost .. at x y z' lines against:

| record (squad) | start | loot | door | reception | atrium | gallery | floor2 | floor1 | lobby | car |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 (#02) | 5998, -577 | 4670, -460 | 4019, -510 | 2282, 349 | 839, 443 | 294, -974 | -1935, -1534 | -1332, -575 | -167, -79 | 2407, 487 |
| 2 (#03) | 6078, -457 | 4750, 232 | 4099, 153 | 2282, 749 | 839, 763 | 134, -1094 | -860, -1440 | -2074, -1341 | 557, -764 | 2407, 577 |
| 3 (#04) | 6038, -297 | 5160, -422 | 4019, -998 | 3050, -590 | 917, -884 | 597, -924 | -1855, -1614 | -1212, -655 | 1157, 301 | 2497, 487 |
| 4 (#05) | 5918, 142 | 5160, 274 | 4019, 313 | 3090, 550 | 839, 643 | 334, -854 | -1495, -1135 | -1012, -375 | 559, 603 | 2497, 577 |
| 5 (#06) | 6078, 142 | 5370, -414 | 4019, -1118 | 2067, -608 | 877, -764 | 557, -764 | -1615, -1135 | -1332, -375 | -203, 206 | 2317, 487 |
| 6 (#07) | 5998, 262 | 5450, 186 | 4099, -350 | 3050, 390 | 919, 523 | 637, -644 | -1695, -1055 | -2085, -130 | -163, 406 | 2407, 397 |
| 7 (#08) | 6078, 382 | 4590, -540 | 3570, -1040 | 2282, -950 | 837, -964 | 254, -1094 | -740, -1440 | -1092, -655 | 1157, -501 | 2317, 577 |

What to read, and what was said beforehand:

- **The foot of the first flight** (the second form's riskiest change). G1's four lost 81, 143, 156 and 288
  there and on the 20 m beyond, in GO+180..212, and nobody died. The second form stops them at the foot for up
  to 30 s. **Worse than the first form** if two or more of those who come down the south flight die on the
  second floor (y 20300..20900, z < -800) in two of three runs; **better** if the floor2 gate opens before its
  30 s (the escort's lines: floor2 -> floor1 in under 25 s) in two of three, which G1's never did. If it is
  worse, the first form's floor2 hold is one edit away (the gate's `box` back to (-1250, 120, -1980, -880)) -
  but the plan's own rule 4 then refuses it, on purpose: say which is wanted.
- **The gallery**: its wait names five men of that floor now. Shorter than G1's 34.5 s (the escort's lines) in
  two of three = they can be killed from there; nobody dead at a gallery hold.
- **Nobody dead on the second floor's north-west** (x < -1800, z > -200): floor2 waits for `2nd RightCharge`
  now. A bot hit there has taken the north flight (G1's record 3): 9.3.
- The whole: G1 had four of six on the first floor (alive at GO+240) and none at the car. Better = three or
  more of six within 10 m of their car place alive, in two of three runs. With an idle player that is asking
  for six won fights; G1 says expect less. The run that matters is a PLAYED one.
- A gate passed in under 2 s with no 'lost' line of any bot within 15 m of its holds in the 20 s before: either
  its men were dead (the reception's are, legitimately, when the door's wait saw them die) or its entries read
  dead although they live. Suspect at the door, the atrium, floor1 and the lobby, whose men are woken on that
  very leg; no line of the hook says an enemy's state.
- Place lines of all seven need the `[CrewHop]` block of 7.2 in the installed map's KLJoin.ini.

## 8. ASSUMED and GUESS, in one place

- GUESS: every gate's search box, the enemy direction and so the side of the cover box; POST_KEEP 300,
  PASS_NEAR 600, PASS_ON 1000, ENGAGE 2500, the ring's radii; the 4 m/s of section 7.
- GUESS: which squads a gate names (4.2), most of all that the seven at the foot of the first flight win.
- ASSUMED: a line of fire from a hold. Nothing here reads the collision. 'A straight line on the mesh' is the
  one proxy, and it says 'not known' for a line across the well or past a prop.
- ASSUMED: this module's stand-in path (the shortest way through the middles of the polygons' shared edges)
  is the way a bot takes. G1: one of the six came down to the second floor another way, a second was hit
  inside a trigger box the stand-in way keeps out of.
- ASSUMED: a bot sent to a hold stays near it. G1: one was hit 5.7 m from his, at another cover box; where the
  others stood when nobody hit them is not in the log.
- ASSUMED: `DefendCover` may take any cover within 500 of the defend position (so every one is tested).
- ASSUMED: the arrival radius' enum is field 5 (3.1).
- ASSUMED, as before: a started step replaces the squad's running one; an AI heister trips a MERCONLY box
  (measured in effect); the game's pathfinder finds a way of 20..48 m over a stair from one order (G1: yes).
- NOT KNOWN: what a late tower step does to a bot in the street (9.1).

## 9. Not done, limits, proposals

### 9.1 The join (review D1, the 'must')

The gates do not touch the JumpPoint's list or the street chain, and the hook still moves every bot in play.
But the tower chain is not ENDED by the join. A wait that is armed then - a gate's, up to 30 s; the table's
loot wait, up to its 30 s (limit N3 of re/bots_retomoto.md) - fires later and sends 'AITrigger' to the next
TOWER step, which has not run and so starts (3.2), for a bot that stands in the street. ASSUMED to take the
place of its street step, which cannot be started again (field 8). The old chain had one such wait a bot,
this one has eight.

Who is exposed: a bot AT a hold whose men live when the human steps into the car. Not exposed: a bot that
walks between two holds (its step has not arrived, its wait is not armed; the hook moves it more than 10 m
from every tower place) and one at a hold whose men are dead (the wait fires at once). So a human who clears
the rooms leaves few waits armed behind him, one who runs past living men leaves most. It is also why
`GuardingElevator` left the last gate (4.2).

What was done: the dynamic step adds nothing to it any more and its guard is back (5.2, 3); both checks
count the waits and say it; J1 and J0 are written (7.2). `[Bots] BoardAll=1` raises a bot that stands once the
van has been called.

What was NOT done - a data remedy. Two are possible, both new mechanisms on a join nobody has seen work for
bots; they wait for J1:
- **The jump list names every tower step of each squad before its street step.** READ: the JumpPoint sends
  'AITrigger' in the list's order (0x72e0f0), and a step started once is deaf to a later 'AITrigger'
  (0x4ebed0). So every tower step would be started and replaced within the one call, the street step last, and
  every late wait would find its step spent. Cost: 8 more entries a squad (63 in the list; stock lists hold
  one to six), eight orders to unreachable places for every bot at every join, and work in three checks -
  `kl_fa_bots_rt.check` wants one street step a squad in that list, `kl_fa_bots_dyn.parse` / `graph` take every
  step named from outside for the start of a chain, and the dynamic step's forks put a RandomTrigger behind a
  wait, which nothing can spend.
- **A re-order from the hook** some seconds after the teleport (the lead's file).

### 9.2 No gate on the street half

Its police are waves that come at the crew and fall back to the van by design, the round's clock runs there,
no run has shown where bots die on it, and `kl_fa_bots_rt.check`'s street rules take the chain's FIRST wait
for the rally. Wanted first: J1.

### 9.3 The way a bot takes is the game's

G1's record 3 came down to the second floor's north-west, not by the south flight the stand-in path takes,
and met two men alone. A way place at the head of the south flight in that leg's step would pin the flight
(`WAY_EVERY` has the machinery; one shared station pulled the seven into a corner in the first round, so it
would have to be seven places). Not built: one bot in one run.

### 9.4 The last to come is left alone

Each bot's wait runs from its own arming. Where a gate runs out, the first to come leaves first and the last
stands alone for the rest of his 30 s (G1: record 4). A remedy that fits what was read: every bot's wait at a
gate names the next step of ALL seven - the first wait to fire moves the squad as one, and the others find
their steps spent. It breaks three walkers that follow a chain by its first next link only where that link is
the bot's own (kept first in the list, they would hold) and `kl_fa_bots_dyn.parse`, which refuses a link that
names two steps. Not built; proposed for after G2..G4.

### 9.5 The rest

- The room gate is unchanged: the bots still walk in before it fires (1.1).
- `Last_Stand_02`, `GuardingElevator`, `RightBehindStairs` are waited for by no gate (4.2).
- `kl_fa_bots.py` line 2952: its test 'TriggerActorsDead names N groups, M without an actor (it has no time
  limit)' is nested under `if shut:`, so it almost never runs; and the wait HAS a time limit. Not this
  track's file. `kl_fa_talk.py`'s countdown rule: 6.3.
- The pictures of the plan (top views per floor: walls, cover boxes, trigger boxes, squads with their posts,
  the 49 holds, 40 deaths: the 34 of the old chain and G1's six) are in `<work>\build\z_rooms\maps\`.

## 10. After the review: what was done about each defect (`re/retomoto_bots_rooms_review.md`)

| defect | where | fixed / refuted | what |
|---|---|---|---|
| **D1 must** - the join; the dynamic step's guard off on a gates build | `kl_fa_bots_dyn.py` program / check, both builds, this note | **fixed as far as it can be offline; NOT proven** | (b) done: `last_loot_wait` - the table's wait is 'the last loot wait' on a chain the jump cuts off; no hold or timer of the dynamic step behind it (36 -> 0 by the review's own `rev5.py`); the check FAILs such a timer again (the first `_r`: 14 FAIL lines) and NOTEs the gate waits; `kl_fa_bots_rt.check` NOTEs them too. (a) the joined run is WRITTEN, not run (this track is offline): J1 + control J0, 7.2. (c) not built, 9.1 - with the order of the jump list now READ. Exposure made smaller: the last gate no longer names a man who cannot be reached |
| **D2 should** - 36 holds of the dynamic step between the gates | `retomoto_full_r`, `kl_fa_bots_dyn.py` program | **fixed** | by D1 (b); `_r` rebuilt; 4.3 says what the step still adds. Also: another way of a fork passes no post the build's way keeps clear of, and nobody's loot wait is cut short |
| **D3 should** - the reception's covers straddle the atrium's box | `kl_fa_bots_rt.py` GATES[1], hold_spots, check 2b | **fixed** | the whole standing ring of EVERY cover box within 500 of a hold is tested, in the plan and in the check (FAIL); the reception's hold is its east half (x 2067..3090). The review's own `rev4.py` on the new build: 6.4. The atrium's case (men of another floor) is a NOTE, as the review weighed it |
| **D4 should** - floor2's hold lies beyond its men; two holds on a post | `kl_fa_bots_rt.py` GATES[4], GATES[3], check; this note 4 | **fixed, by a third way** | check lines: a hold within 300 of a post (FAIL), a way that walks past (FAIL), squads out of reach / without a line on the mesh (NOTE). The hold is AT the foot of the first flight (4.1 says why not the head and why not the sprint; it is a GUESS that it is better, and 7.3 says how a run tells). The gallery no longer names the men across the well. Backed by G1 (1.4) |
| **D5 should** - the live checks cannot tell success from failure | this note 7 | **fixed** | section 7 written anew: the joined run first, three runs against a spread, numbers said beforehand, the sign of a gate that opens for no reason, the place log and why this map has none. The review's point about L2 is partly refuted by G1 (7.1) |
| note - 'arrival' is 'within 10 m' | 3.3 / 4, WAIT_S | **corrected** | 3.1; `ARRIVE_3D`; the plan avoids a hold on another floor within 10 m of the place before (floor1: 4 -> 0), the check NOTEs one |
| note - state 2 | GATES comment, FAIL text, 3.1 | **corrected** | |
| note - 'a step starts once' | 3.2 | **corrected** | and the two other messages are named: 'DebugTrigger', 'DebugTriggerSignals' |
| note - three over-statements | 0, 3.3, 9 | **corrected** | the fall-back can be made shorter (3.3); `--gates` (5.1 and the tool's own text); the talk delays (6.3); V1 is no control (1.2) |

Scratch (session scratchpad `...\1e45a579-...\scratchpad\G2\`): `chain2.sh` (the builds and every check),
`proofs.sh` + `neg2.py` (6.4), `tables2.py` (the tables of 4 and 7), `geo.py` / `sight.py` / `dbg_line.py` (posts,
lines on the mesh); the first round's are in `..\G\`, the reviewer's in `..\Grev\`.
