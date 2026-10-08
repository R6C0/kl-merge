# Retomoto Tower as a Fragile Alliance map - survey of M09_A and M09_B

Survey date 2026-10-09. Sources: `DM\Scenes\Locations\M09_A\M09A_Main.zip` (tower: offices, roof) and
`M09_B\M09B_Main.zip` (lobby, square, street, bus terminal), read in memory with `tools/kl_gms.py`,
`kl_prp.py`, `kl_rtp.py` (schemas `re/kaneandlynch.json`, `re/kl2.json`), `kl_pf4.py`, `kl_tex.py`,
`kl_prm.py`, `kl_audio.py`. Nothing was converted, installed or run in the game.

How the numbers were made (so they can be re-made):
- **Node index** = index in the `.prp` node list = `.gms` entity index + 1 (node 0 = ROOT).
- **World position**: `.gms` record +4 rotation (9 floats, rows reversed then transposed, as in
  hbm-editor `gms/placements.ts`) and +8 translation, parent-relative, composed down the tree.
- **Box**: the `.prm` model record (64 bytes, min xyz at +0x20, max xyz at +0x2c) put through the world
  transform. Room extents are the boxes of each room's own `ZBOUND` children (`InsideBound_NN`), not
  the union of its contents (rooms hold far-away skyline pieces).
- **Units**: an elevator door is 230 units tall (node 4727, y 19599..19829), so 1 unit = 1 cm. ASSUMPTION
  only in the sense that nothing in the files says so. Y is up.
- "map / systems / campaign gameplay" is my split by top-level group name: systems = `AllLevels/*`,
  `CloneGroup_Effects/*`, `ZParticleController`, `TrackLinkObjects`; map = `Locations/*`,
  `CloneGroup_Locations/*`, `M09_Backdrop*`, top-level `Effects/*`; everything else is campaign gameplay.

Words used: A = M09_A, B = M09_B. "Not established" = I did not prove it. PROPOSAL = my suggestion, untested.

---------------------------------------------------------------------------------------------------

## 0. Short answers

1. **A and B are not one coordinate space.** The same tower is modelled twice: in B as a facade shell
   20,600 high over the lobby (footprint x 2550..9570, z -8830..-4150), in A as an interior (x -2800..6000,
   z -2200..2000, floors at y 19600 / 20300 / 21000, roof at y 25420). The only objects that sit in both
   levels with the same rotation and one common offset are 4 skyline blocks: **B = A + (3000, 0, -7000)**.
   The two exit/arrival elevator cars (same model, same rotation) give B = A + (3298, -19040, -7214).
   So horizontally the two agree to within a few metres, vertically the campaign jumps 190 m in a
   cutscene. Section 2.
2. **Left untransformed, the two parts do not collide**: A's interior hangs at y 19600..25900 over
   x -2800..6000, z -2200..2000; B's room bounds under it end at y 10373. Both parts could keep
   their baked data (octree, navigation mesh, gates, Havok) as they are. What is missing is a way for a
   player to get from y 19600 to y 560. Section 2.4 lists the options; none is proven.
3. **The statues are the samurai-armour display cases** (`SI0103_M09_Montre_SamuraiSuit_00`): 15 in the
   atrium (3 + 6 + 6 on its three floors). The developers call them statues themselves
   (`Markup!HeroCovers!Statues!PlayerCoverColiStatue#NN`). 4 sword cases are the other candidates. Section 3.2.
4. **The main room is the boardroom, `M09_A_Ins_Office_301`** (node 4019): it is the room behind the
   main window, holds 19 of the level's 79 enemy soldiers including Retomoto, and the campaign's own
   objectives there are `MissionObjective_030_KillAll` and `MissionObjective_040_Briefcase`. Section 3.3.
5. **The main window** is one assembly, `SI0200_M09_Window_Glass_A_02`, in the boardroom's outer wall at
   x 5850, y 20990..21660, z -990..790. The campaign breaks it with `WindowBlowup!BombWindow03`
   (node 11648, `Explode`), sound `M09_Explosion_Window_Office_01.wav`. Section 3.1.
6. **A's navigation mesh is refused by `kl_pf4.convert`**: it has 15 array-7 records. B's converts. Section 5.
7. **The music** is 7 clips `Music/InHouse/Japan/M09_A/*` played by 3 + 5 `PlayMusic` objects. None of them
   is in the current (merged) `DD\PC_Def.str`. No Fragile Alliance level of either game uses `PlayMusic`.
   Section 6.

---------------------------------------------------------------------------------------------------

## 1. Structure of each part

### 1.1 M09_A (tower) - 11,926 entities, 483 top-level groups

| first node | top-level group | groups | entities | with model | kept as |
|---:|---|---:|---:|---:|---|
| 3157 | `Locations/M09_A/M09A_Locations.zip` | 1 | 3434 | 2729 | MAP |
| 666 | `AllLevels/mainsceneincludes.zip` | 1 | 2491 | 705 | systems (drop) |
| 6757 | `CloneGroup_Effects/BulletImpacts.zip/*` | 54 | 2338 | 193 | systems (drop) |
| 9956 | `CloneGroup_Locations/M09_A/*` | 14 | 1129 | 1030 | MAP |
| 9509 | `CloneGroup_Effects/AllocMany/*` | 33 | 1002 | 160 | systems (drop) |
| 191 | `AI_Players!*` | 88 | 517 | 102 | campaign gameplay (drop / re-author) |
| 9095 | `CloneGroup_Effects/WeaponsEffects.zip/*` | 12 | 414 | 49 | systems (drop) |
| 19 | `Characters!*` | 35 | 196 | 42 | campaign gameplay (drop / re-author) |
| 6692 | `Markup!*` | 97 | 99 | 0 | campaign gameplay (drop / re-author) |
| 6592 | `CutScenes/M09/*.zip` | 4 | 64 | 35 | campaign gameplay (drop / re-author) |
| 6663 | `Music!*` | 20 | 46 | 0 | campaign gameplay (drop / re-author) |
| 11720 | `Locations/M09_A/M09A_Audio.zip!*` | 44 | 44 | 0 | MAP |
| 6605 | `Locations/M09_A/Effects.zip` | 1 | 41 | 33 | MAP |
| 6695 | `COOP!*` | 22 | 28 | 0 | campaign gameplay (drop / re-author) |
| 11905 | `Covers!*` | 20 | 20 | 0 | campaign gameplay (drop / re-author) |
| 13 | `WindowBlowup!*` | 9 | 14 | 1 | campaign gameplay (drop / re-author) |
| 6646 | `Effects/AllocMany/M09/AllocMany_BigWindow_M09.zip` | 1 | 13 | 0 | MAP |
| 6659 | `Locations/M09_A/M09A_Postfilter.zip` | 1 | 4 | 0 | MAP |
| 11 | `M09_Backdrop_A_00` | 1 | 2 | 1 | MAP |
| | *(11 smaller campaign groups not listed)* | | | | |
| | **total** map 4667, systems 6247, campaign gameplay 1012 | | **11926** | | |

### 1.2 M09_B (lobby and street) - 16,646 entities, 544 top-level groups

| first node | top-level group | groups | entities | with model | kept as |
|---:|---|---:|---:|---:|---|
| 10 | `Locations/M09_B/M09B_Locations.zip` | 1 | 7864 | 5063 | MAP |
| 13095 | `CloneGroup_Effects/BulletImpacts.zip/*` | 54 | 2338 | 193 | systems (drop) |
| 7874 | `AllLevels/mainsceneincludes.zip` | 1 | 2062 | 596 | systems (drop) |
| 10031 | `Enemies!*` | 102 | 1209 | 469 | campaign gameplay (drop / re-author) |
| 11649 | `CloneGroup_Effects/AllocMany/*` | 33 | 970 | 167 | systems (drop) |
| 12172 | `CloneGroup_Locations/M09_B/*` | 3 | 923 | 905 | MAP |
| 15433 | `CloneGroup_Effects/WeaponsEffects.zip/*` | 12 | 414 | 49 | systems (drop) |
| 11180 | `Civilians!*` | 24 | 383 | 171 | campaign gameplay (drop / re-author) |
| 16509 | `HeroCovers!*` | 118 | 118 | 0 | campaign gameplay (drop / re-author) |
| 9936 | `Mercenaries!*` | 14 | 92 | 5 | campaign gameplay (drop / re-author) |
| 11553 | `CutScenes/M09/*.zip` | 2 | 64 | 37 | campaign gameplay (drop / re-author) |
| 16426 | `Locations/M09_B/M09B_Audio.zip!*` | 44 | 44 | 0 | MAP |
| 11634 | `Music!*` | 21 | 29 | 0 | campaign gameplay (drop / re-author) |
| 1 | `Crowd!*` | 17 | 21 | 6 | campaign gameplay (drop / re-author) |
| 16300 | `COOP!*` | 19 | 19 | 0 | campaign gameplay (drop / re-author) |
| 16470 | `Traffic!*` | 19 | 19 | 5 | campaign gameplay (drop / re-author) |
| 11566 | `CutsceneStuff!*` | 6 | 16 | 0 | campaign gameplay (drop / re-author) |
| 16336 | `MapObjectives!*` | 16 | 16 | 0 | campaign gameplay (drop / re-author) |
| 11578 | `Locations/M09_B/M09B_Postfilter.zip` | 1 | 3 | 0 | MAP |
| 8 | `M09_Backdrop_A_00` | 1 | 2 | 1 | MAP |
| | *(15 smaller campaign groups not listed)* | | | | |
| | **total** map 8836, systems 5786, campaign gameplay 2024 | | **16646** | | |

Things to know about the split:
- `CloneGroup_Effects/AllocMany/*` (33 groups in each part; 1002 / 970 entities) is NOT pure system
  data. Map objects point into it by path: A 24 `ZAllocMany` nodes (-> `CloneGroup_Effects/AllocMany/M09/...`,
  one `.../M02/Shatter_Art...`), B 78 (44 of them -> `CloneGroup_Effects/BulletImpacts.zip/Bullet/...`).
  A graft that drops the Dead Men effects must keep or re-point these. In A, 36 `HavokShatter`
  controllers on map objects also point into `AllLevels/mainsceneincludes.zip`.
- B's map tree contains a system-like subtree: `Locations/M09_B/M09B_LOC_Inside.zip\Effects/BulletImpacts.zip`
  (node 7444, 429 entities: Grenade 123, Bullet 212, Bullet_Holes 81).
- B has three ZROOMs outside the map tree: `Crowd!RoomStreet` (node 1), `Crowd!RoomBus` (4),
  `Crowd!RoomLobby` (6), holding the crowd flow (`ZHFlowFF2M09` x3, `ZHFlowLnkObj` x6). Each ZROOM owns
  trees in the `.oct`; dropping the crowd means dropping those trees too.

### 1.3 Rooms of A

| node | room (ZROOM) | entities | bound node | bound box min (x y z) | max (x y z) | floor m2 |
|---:|---|---:|---:|---|---|---:|
| 3159 | `M09_A_Ins_TopOffices_401` | 238 | 3160 | 3980 21718 -1240 | 6000 23882 1040 | 460 |
| 3397 | `M09_A_Ins_Atrium_201` | 488 | 3511 | -2800 20300 -2200 | 1400 21000 2000 | 1764 |
| 3885 | `M09_A_Ins_Reception_301` | 134 | 3956 | 2190 20995 -1517 | 2628 21510 -842 | 30 |
| 3885 | `M09_A_Ins_Reception_301` | 134 | 3957 | 2190 20995 644 | 2628 21510 1319 | 30 |
| 3885 | `M09_A_Ins_Reception_301` | 134 | 3958 | 1790 20995 -1550 | 2190 21510 -750 | 32 |
| 3885 | `M09_A_Ins_Reception_301` | 134 | 3959 | 1790 20995 550 | 2190 21510 1350 | 32 |
| 3885 | `M09_A_Ins_Reception_301` | 134 | 3992 | 2628 20995 -1550 | 3420 21510 1350 | 230 |
| 4019 | `M09_A_Ins_Office_301` | 706 | 4613 | 3420 20971 -1317 | 5852 21822 1117 | 592 |
| 4725 | `M09_A_Ins_Elevators_101` | 169 | 4889 | 1202 19600 -1804 | 3204 20177 1631 | 688 |
| 4894 | `M09_A_Ins_Atrium_301` | 467 | 4916 | 1790 21000 -875 | 2190 22400 675 | 62 |
| 4894 | `M09_A_Ins_Atrium_301` | 467 | 4965 | 2190 21000 -651 | 2490 21700 450 | 33 |
| 4894 | `M09_A_Ins_Atrium_301` | 467 | 4966 | -2800 21000 -2200 | 1801 22400 2000 | 1932 |
| 5361 | `M09_A_Ins_Atrium_101` | 226 | 5516 | -2800 19600 -2200 | 1400 20300 2000 | 1764 |
| 5742 | `M09_A_Out_CityScapeFront` | 311 | 5766 | 5986 21685 -3200 | 8596 23882 3300 | 1696 |
| 5742 | `M09_A_Out_CityScapeFront` | 311 | 5767 | 5751 17840 -3200 | 8596 21695 3300 | 1850 |
| 5742 | `M09_A_Out_CityScapeFront` | 311 | 5786 | 5751 23871 -3200 | 8596 28723 3300 | 1850 |
| 6053 | `M09_A_Out_CityScapeBack` | 31 | - | no ZBOUND | | |
| 6084 | `M09_A_Out_Roof_401` | 494 | 6487 | 5832 25362 -3200 | 8596 28323 3300 | 1797 |
| 6084 | `M09_A_Out_Roof_401` | 494 | 6488 | -5309 21900 -3200 | 5846 28330 3300 | 7251 |

Three rooms of systems (`Scope_Dragunov*`, nodes 669, 686, 702) and `ZBackdrop` node 11 are not listed.
Campaign names for the atrium floors: `060_Atrium_1st` = y 19600 (`Atrium_101`), `050_Atrium_2nd` = y 20300
(`Atrium_201`), `040_Atrium_3rd` = y 21000 (`Atrium_301`).

Side view of the tower in A (x to the right, y up; z spans -2200..2000 everywhere, centre line z = -100):

```
 y
 28330 . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
        Out_Roof_401: helipad, helicopter (4133 25521 122), radio tower (1862 25302 32)
 25420 ==================================================== roof ====o rappel box (5999 25483 -89)
                                                |  TopOffices_401   | :
 23882                                          |  x 3980..6000     | :  rope down the +x face
 21718                                          |__(set dressing)___| :  (Out_CityScapeFront,
 21822 +--------------------------+---------+-----------------------+ :   x 5751..8596)
       | Atrium_301  (3rd floor)  |Reception|  Office_301 BOARDROOM # <-- MAIN WINDOW x 5850
 21000 +--------------------------+--301----+--- y 20971..21822 ----+     y 20990..21660, z -990..790
       | Atrium_201  (2nd floor)  |
 20300 +--------------------------+------------+
       | Atrium_101  (1st floor)  | Elevators_101  5 elevators, exit car at (2974 19600 909)
 19600 +--------------------------+------------+
     x -2800                   1400 1202     3204/3420                5852
```

Plan of A's playable floors (x right, z up; one character is about 200 x 400 units):

```
 z  2000 +---------------------+
         |        ATRIUM       |-------+--------+-----------------+
         |  3 floors, open     | ELEV. | RECEP. |    BOARDROOM    #
  -100   |  centre; samurai    | LOBBY | 301    |  (Office_301)   # main window, faces +x
         |  cases round it     | 101   |        |                 #
         |                     |-------+--------+-----------------+
 -2200   +---------------------+
       x -2800               1400     1790     3420             5852
```

Vertical links inside A (all in the atrium; model boxes):

| node | object | room | box |
|---:|---|---|---|
| 5575 | `SI0103_M09_Stairs_A_04` | Atrium_101 | (-2163 19597 -2582)-(-259 20408 -679) |
| 5574 | `SI0103_M09_Stairs_B_02` | Atrium_101 | (-2162 19597 479)-(-259 20413 2382) |
| 3867 | `SI0103_M09_Stairs_C_01` | Atrium_201 | (-2163 20267 -2582)-(-259 21111 -679) |
| 3866 | `SI0103_M09_Stairs_D_01` | Atrium_201 | (-2154 20267 731)-(-697 21108 1956) |
| 5323 | `SI0103_M09_StairsTop_A_01` | Atrium_301 | (-2210 20965 -2582)-(-259 21703 -631) |
| 5322 | `SI0103_M09_StairsTop_B_01` | Atrium_301 | (-2154 20967 731)-(-620 21704 1956) |
| 5371 | `SI0103_M09_ElevatorCarGroup_02` (atrium lift, the level's one `Elevator` controller) | Atrium_101 | at (-1700 19600 -100) |
| 6189, 6216, 6218, 6284 | `SO0200_M09_HelipadStair_A_05/04/03/01` | Out_Roof_401 | y 25327..25875 |

So 1st <-> 2nd floor by stairs A / B, 2nd <-> 3rd by stairs C / D; the boardroom and reception are on the
3rd-floor level only (y 20990..21000). **There is no walkable link between the roof (y 25420) and the
boardroom**: the campaign's only way down is the rappel. The boardroom's inner door is at x 3430
(`SI0200_M09_Office_DDoor_01_01`, node 4439, with a `_Broken_01` twin, node 4020; see section 4.3).

### 1.4 Rooms of B

| node | room (ZROOM) | entities | bound node | bound box min (x y z) | max (x y z) | floor m2 |
|---:|---|---:|---:|---|---|---:|
| 1 | `Crowd!RoomStreet` | 3 | - | no ZBOUND | | |
| 4 | `Crowd!RoomBus` | 2 | - | no ZBOUND | | |
| 6 | `Crowd!RoomLobby` | 2 | - | no ZBOUND | | |
| 12 | `M09_B_Skyscrapers_01b` | 4 | - | no ZBOUND | | |
| 16 | `M09_B_LightsCrowd` | 6 | 17 | -5 -10000 -5 | 5 -9990 5 | 0 |
| 2710 | `M09_B_Skyscrabers_01a` | 37 | - | no ZBOUND | | |
| 2747 | `M09_B_Hotel_Street_01a` | 256 | 2873 | -33510 -8200 -22715 | -24100 8200 49301 | 67769 |
| 2747 | `M09_B_Hotel_Street_01a` | 256 | 2874 | -24800 -1060 -4200 | -18400 15340 1200 | 3456 |
| 2747 | `M09_B_Hotel_Street_01a` | 256 | 2958 | -38470 4122 9107 | -29631 15340 22084 | 11471 |
| 3003 | `M09_B_Bus_Terminal_01a` | 875 | 3781 | -24300 -1200 6050 | -14100 4600 18350 | 12546 |
| 3878 | `M09_B_Overpass_01a` | 326 | 4110 | -14250 -600 6509 | -5600 4900 20701 | 12277 |
| 4204 | `M09_B_Street_01a` | 606 | 4745 | -5900 -100 -1650 | 6600 4900 33850 | 44375 |
| 4204 | `M09_B_Street_01a` | 606 | 4787 | -9184 -100 -1595 | -5475 4900 7466 | 3361 |
| 4810 | `M09_B_Retomoto_Square_01a` | 414 | 5109 | -8000 -405 -26550 | 0 10373 -1100 | 20360 |
| 4810 | `M09_B_Retomoto_Square_01a` | 414 | 5110 | -50 -717 -11800 | 2650 4000 -1100 | 2889 |
| 4810 | `M09_B_Retomoto_Square_01a` | 414 | 5111 | 2550 -715 -4100 | 3600 4000 -2500 | 168 |
| 4810 | `M09_B_Retomoto_Square_01a` | 414 | 5112 | 2600 -706 -2525 | 3950 4050 -1075 | 196 |
| 4810 | `M09_B_Retomoto_Square_01a` | 414 | 5113 | 2550 -712 -11800 | 3900 4000 -8800 | 405 |
| 4810 | `M09_B_Retomoto_Square_01a` | 414 | 5183 | -10720 3941 -11200 | -5977 8512 -1100 | 4791 |
| 5473 | `M09_B_Lobby_RetoMoto_Elevators_01a` | 15 | 5485 | 6052 393 -6967 | 6597 881 -6045 | 50 |
| 5488 | `M09_B_Lobby_RetoMoto_01a` | 1956 | 7306 | 2600 42 -8150 | 6109 1254 -4850 | 1158 |
| 5488 | `M09_B_Lobby_RetoMoto_01a` | 1956 | 7307 | 2550 39 -7300 | 2650 839 -5700 | 16 |
| 5488 | `M09_B_Lobby_RetoMoto_01a` | 1956 | 7423 | 6109 42 -5996 | 7860 1254 -4850 | 201 |
| 5488 | `M09_B_Lobby_RetoMoto_01a` | 1956 | 7424 | 6109 42 -8156 | 7861 1254 -7009 | 201 |
| 5488 | `M09_B_Lobby_RetoMoto_01a` | 1956 | 7425 | 6590 42 -7012 | 7860 1254 -5994 | 129 |

Plan of B (x right, z up = "north" in the object names; ground y is about 0..20 on the square and the
street, -980 in the bus terminal and the hotel street):

```
 z
 34000                     |      |
                           |STREET|   Street_01a  x -5900..6600, z -1650..33850
 20700  +--------+---------+ 01a  |   far north road block: police cars z 13131..14404,
        | BUS    |OVERPASS |      |     LevelBound_North at (-2565 85 13418)
  HOTEL | TERM.  | 01a     |      |   first road block: cars z 3602..3911
 STREET | y -980 |         |      |
  01a   |        |         |      |
  6050  +--------+---------+      |
                           |      +-------+
 -1100  ...................|ROAD  | fore-  |
                           |x-5700| court  +=========================+
                           | ..   | x -50  | LOBBY x 2600..6109      | elevator car
 -6490                     | -300 | ..2650 > entrance (x 2600,       | (6272 560 -6305)
                           |      |        |   z -7300..-5700)       |
                           |RETO- |        +=========================+   tower shell
 -11800 ...................|MOTO  |--------+                             x 2550..9570
                           |SQUARE|   south road block: SWAT van (-2208 0 -12506),
 -26550                    +------+     LevelBound_South z -11399..-12695
      x -33500  -24300  -14250 -8000  -50   2650        6109   7860
```

Main areas of B:

| area | room node | x | y | z | what it is |
|---|---:|---|---|---|---|
| lobby | 5488 | 2600..6109 (wings to 7860) | 42..1254 | -8150..-4850 | Retomoto lobby; floor about y 160, elevator landing y 560 |
| lobby elevator | 5473 | 6052..6597 | 393..881 | -6967..-6045 | campaign start of B |
| entrance | (bound 7307) | 2550..2650 | 39..839 | -7300..-5700 | doorway in the -x face of the tower |
| forecourt | 4810 (bound 5110) | -50..2650 | about 0..200 | -11800..-1100 | tiles and two Japanese gardens between door and road |
| road, square part | 4810 (bound 5109) | -8000..0 | 0..20 | -26550..-1100 | carriageway pieces x -5700..-300 |
| road, north part | 4204 | -5900..6600 | 0..20 | -1650..33850 | same road going north; freeway above (y about 1130) |
| overpass / underpass | 3878 | -14250..-5600 | -600..4900 | 6509..20701 | pedestrian link west |
| bus terminal | 3003 | -24300..-14100 | -1200..4600 | 6050..18350 | campaign end, ground y about -980 |
| hotel street | 2747 | -33510..-24100 | | -22715..49301 | campaign getaway street |

---------------------------------------------------------------------------------------------------

## 2. Do A and B share one world space? The seam

### 2.1 What was compared

| test | result |
|---|---|
| Objects with a model whose name occurs exactly once in each map tree | 25 names. Their A - B offsets: (-3000, 0, 7000) with identical rotation x4; (-3000, 1467, 9000) x2; 19 others all different |
| The 4 agreeing objects | `SO0301_RoofS1_01` (A 5842 / B 2737), `SO0301_RoofS1_11` (5869 / 2733), `SO0301_SkyH1_05` (5836 / 2738), `SO0301_SkyC1_08` (5801 / 2742): skyline blocks, in `M09_A_Out_CityScapeFront` and `M09_B_Skyscrabers_01a` |
| Large models (> 800 units) matched by box size, same rotation | 17 shapes in both; the same 4 pairs are the only offset that repeats more than twice |
| Shared room names | none (A rooms `M09_A_*`, B rooms `M09_B_*`) |
| Elevator cars `SI0101_JPN_Elevator_Main_A_00` | see table below |

| part | node | parent group | position | rotation | world box |
|---|---:|---|---|---|---|
| A | 4729 | `SI0101_JPN_Elevator_Int_A_05` | 2974 19600 -90 | identity | (2756 19600 -243)-(3189 19873 63) |
| A | 4738 | `SI0101_JPN_Elevator_Int_A_04` | 1953 19600 890 | 180 deg about Y | (1738 19600 738)-(2171 19873 1043) |
| A | 4747 | `SI0101_JPN_Elevator_Int_A_03` | 2974 19600 909 | identity | (2756 19600 756)-(3189 19873 1062) |
| B | 5482 | `SI0101_JPN_Elevator_Int_A_00` | 6272 560 -6305 | identity | (6054 560 -6458)-(6487 833 -6152) |

The campaign leaves A through the car at (2974 19600 909) (`Int_A_03`: `AnimProxy_OpenEscapeElevator`,
node 11700, opens `Ext_A_03` / `Int_A_03`; `EndOfLevelTrigger` node 11791 at (2938 19684 898)) and arrives in B
in the car at (6272 560 -6305). Same model, both unrotated: **B - A = (3298, -19040, -7214)**.

### 2.2 The tower in each part

| | A (interior) | B (shell) |
|---|---|---|
| footprint x | -2800..6000 (atrium -2800..1400, boardroom to 5852) | 2550..9570 (`SO0400_JPN_Facade_A/B/D/E_*` plane at x 2550..2650; `Side_Left/Right_*` to 8780; `Collapse_FacadeReto_01` to 9570) |
| footprint z | -2200..2000, centre -100 | -8830..-4150, centre -6490 |
| height | floors 19600 / 20300 / 21000; roof `SO0200_M09_TopRoof_01` y 24695..25891; `Facade_LOD_01` (node 6042) y 501..20501 at x 6007 | facade pieces from y 100 to 20600; `SO0400_JPN_Facade_TOP_01` (node 5134) y 20600..27096 |
| front | main window faces **+x** (x 5850) | entrance faces **-x** (x 2600), toward the square |
| inside | 7 rooms | lobby only (y 42..1254); no ZROOM and no ZBOUND between y 1254 and 20600 (whether any floor mesh exists there was not checked) |

With B = A + (3000, 0, -7000) the A interior lands at x 200..9000, z -9200..-5000: its z range fits the
shell to within 370..850 units, but it is 8800 long against a 7020-long shell (the atrium end would
stick 2350 units out through the entrance face), and **the main window (x 8850) would be on the shell's
back face, the side away from Retomoto Square.** The boardroom floor (20990) would be above the top of
the regular facade (20600), inside the `Facade_TOP_01` piece. So: same building, built twice to roughly
the same plan, not registered. No transform makes them one seamless model.

### 2.3 The seam in the campaign

| | end of A | start of B |
|---|---|---|
| trigger | `Markup!EndOfLevel!EndOfLevel` node 11791 `EndOfLevelTrigger` at (2938 19684 898), crew box 11792 | - |
| level change | `SceneChangerExitPoint` node 68 `SceneChanger` -> `Locations\M09_B\M09B_Main.zip` | - |
| cutscene | `CutScenes/M09/M09_Enter_Elevator.zip` (node 6704, 19 entities), `EndElevatorSounds` (6591), `Characters!FusionSquad` (19) | `CutScenes/M09/M09B_Exit_Elevator.zip` (node 11553, 13 entities), `CutsceneStuff!IntroCut!*` |
| player positions | `Pos_Hero` node 6706 at (2670 19600 768) | `Hero!Hero_01_Suit` (6428 563 -6306), `Hero!Lynch_COOP` (6428 563 -6235); mercenaries at (6219..6419, 562, -6390..-6205) |
| geometry on this side | elevator lobby `M09_A_Ins_Elevators_101`, y 19600..20177 | car and landing `M09_B_Lobby_RetoMoto_Elevators_01a`, then the lobby |
| what follows in B | | lobby -> entrance -> square -> road north -> overpass -> bus terminal -> `Endlevel!EndOfLevel!EndOfLevel` node 16629 at (-24400 -929 8986), `SceneChanger` node 16335 -> `Locations\M11_A\M11A_Main.zip` |

### 2.4 Joining them in one map (PROPOSALS; the lead designs this)

Facts that bound the design:
- Kept in their own coordinates the parts do not overlap where it matters: A's room bounds occupy
  x -5309..8596, y 17840..28723, z -3200..3300 (interior rooms x -2800..6000, z -2200..2000); B's highest
  room bound in that x/z area is y 10373 (`M09_B_Retomoto_Square_01a`, bound 5109). The B shell
  (z -8830..-4150) stands beside A's interior, about 20 m away in z.
  Only the two skylines overlap (both are huge), offset by (3000, 0, -7000) from each other.
- Every baked file of a part is in that part's world coordinates (`.oct` trees, navigation mesh, gate
  records in the `.buf`, `.rmi` / `.rmc` boxes, Havok). Moving either part means re-baking all of them
  for it. Not moving either is the cheap route.
- **No teleport is proven.** `TeleportList` is registered in both exes but its name is in the key table of
  no stock level: 21 Dog Days `.prp` (F01 backup, F02..F09, L00..L11) and 20 Dead Men `.prp` checked.
  `Elevator` occurs in exactly one level, M09_A (the atrium lift), and in no Dog Days level. Stock Dog
  Days FA levels do carry `OnlineSpawnpointTrigger` (2 to 5 per level, e.g. F01 node 15859
  `FASpecials!SpawnPoint!TeamMode!SpawnpointTriggerLoot`), which looks like a way to move the active
  spawn points when a trigger fires; what it does to living players is not established.

Options, cheapest first:
1. *No transform, spawn hand-over.* Tower at its own height; when the tower loot is done the round's
   spawn points move to the lobby (if `OnlineSpawnpointTrigger` does that). Heisters alive in the tower
   still need a way down: not solved by this alone.
2. *No transform, teleport at the elevator.* A trigger in car `Int_A_03` (2974 19600 909) moves a player
   to the B car (6272 560 -6305). Needs `TeleportList` (or a KLHook-side move) to work: unproven.
3. *Lower the tower onto the lobby.* A moved by about (3298, -18300, -7214) so its 1st floor (19600) sits
   on the lobby ceiling (1254), with a hole or stair between. Needs new geometry, A fully re-baked, and
   the atrium end pokes through B's entrance facade (2.2). Most work, most "real".
4. *Tower only, or street only, first.* Each half is a complete space with its own navigation mesh; the
   tower half ends at the elevators, the street half starts in the lobby.

---------------------------------------------------------------------------------------------------

## 3. Objects the design needs

### 3.1 The main window and what blows it

| node | object | class | position / box | role |
|---:|---|---|---|---|
| 4615 | `SI0200_M09_Window_Glass_A_02!SI0200_M09_Window_Glass_Geom_Pre_00` | ZSTDOBJ | (5840 20983 -990)-(5860 21660 790) | intact window; `ShotActivate` swaps to the three below |
| 4617 | `...!SI0200_M09_Window_Glass_Geom_Post_00` | ZSTDOBJ | (4282 20983 -1060)-(5930 21661 900) | blown state (frame and debris reaching 15 m into the room) |
| 4444..4447 | `...!M09_GlassWindowGroup` \ `SI0200_M09_GlassWindow_00_A / _B / _C` | ZGROUP + 3 ZSTDOBJ | (5850 21020 -990)-(5850 21660 790) | glass panes; A and B carry `ShotActivate` |
| 4448, 4449 | `Window_Crackle_Sound`, `Window_Shatter_Sound` (in the group) | ZSNDOBJ | (5850 21036 -100) | 4448 -> `Impact_Window_Small_No_FlyIn_04.wav` |
| 4616 | `...!Window_Shatter_Sound` | ZSNDOBJ | (5820 20990 -100) | -> `SFX/Impacts/GlassBreak/Default/Glass_Break_Big.wav` |
| 4614, 4618..4632 | `...!glass_edges`, `Metal_Window_rim_NN`, `Mesh01` | ZSTDOBJ | x 5842..5855 | frame |
| 4467 | `SI0200_M09_Window_GlowPlane_02` | ZSTDOBJ | (5842 20501 -1574)-(5851 22201 1575) | glow card over the whole wall |
| 4585 | `SI0200_M09_Office_WallOut_A_02` | ZSTDOBJ | (5807 20990 -1600)-(5850 22050 1400) | the outer wall |

What breaks it in the campaign (all in the campaign-gameplay part, top-level `WindowBlowup!*`, nodes 13..18 and 11645..11652):

| node | object | controller | values as stored | what it does |
|---:|---|---|---|---|
| 11648 | `WindowBlowup!BombWindow03` (ZLNKOBJ, the bomb model) at (5867 21094 -66) | `Explode` | 600, 400, 2000, 3000, 0, 'Activate', -> `Effects/AllocMany/M09/AllocMany_BigWindow_M09.zip\Particles_M09_BigWindow`, 4.0, 1, sounds `Bomb_WarmUp.wav` + `M09_Explosion_Window_Office_01.wav`, 10.0, 0, 0, 1 | the explosion: particles, both sounds, damage |
| 6646..6658 | `Effects/AllocMany/M09/AllocMany_BigWindow_M09.zip` | (ZAllocMany + 11 ZParticleEmitter) | top-level, counted as map | the glass burst |
| 11650 | `WindowBlowup!InvisiBomb` at (5685 20997 -394) | `Explode` | 300, 100, 1000, 200, ... | kills the guard by the window (via 11652 `Activator_KillGuyNearWindow`) |
| 11651 | `WindowBlowup!InvisiBombKillPlayer` at (5925 21096 -81) | `Explode` | 80, 80, 0, 700, ... | kills a player who stays at the bomb |
| 11647, 11645, 11646 | `TriggerBox_FallingDebris` (5851 21016 -101), `Timer` (5 s), `Activator_FallingDebris` | `TriggerBox`, `TriggerDelay`, `AIDWrapper` | -> `M09_A_Ins_Office_301\Pillar01_00_Triggered\Pillar_Whole` (node 4040) | a pillar shatters after the blast |
| 414 | `...020_Office!Squad_Guards_Inside_01\Timer_ExplosionDelay_Kane` | `TriggerDelay` 4 s, 11 targets | chairs swap (`GeomActivator_ChairPost`, `GeomDeactivator_ChairsPre`), `Music!06_Explosion`, `SFX!GeomActivator_BoardroomSoundOFF`, `Cam_Explosion`, the two above | the moment of the blast |
| 14..18 | `WindowBlowup!Squad_HeroWalk\MiniCutScene_Kane` + `Pos_PlaceBomb` (5910 21017 -80), `ItemProxy_Bomb` | `MiniCutsceneRout` | anim `/Weapon_Handling/Plant` | Kane plants the bomb: rappel-only, drop |

The meaning of the individual `Explode` numbers is not established (the field list is in `re/kaneandlynch.json`).
For "the round opens as the window blows", the smallest working set is PROPOSED as: node 11648 with its
particle group 6646, fired at round start, plus the window assembly itself. `Explode` is registered in
Dog Days and used by every stock FA level (3 to 9 each), but Dog Days' `Explode` has 3 more fields
(F01 node 7406 shows 18 values against 15 here).

Where the heisters would stand: the campaign puts Kane at `Pos_PlaceBomb` (5910 21017 -80), i.e. 60 units
outside the glass, hanging on the rope. Whether there is a floor, collision or navigation mesh outside
the window is not established; `Markup!Jump_02` (node 11829, a debug jump point) is at (5947 21015 79).
Inside the room, `Markup!Jump_03` (node 11830) is at (4202 21006 -129) and the checkpoint positions
`Markup!CP_02_PosP1 / P2` (nodes 11797, 11795) at (4164 20994 -261) / (4168 20994 78).

### 3.2 The statues

All 19 breakable display cases of the level. "SamuraiSuit" = a suit of samurai armour in a glass
case on a plinth (case object about 150 x 350 x 150 units); "Swords" = a sword stand in a glass case.

| node | object (breakable glass, `HavokShatter` + `ShotActivate`) | group node / name | room | position x y z |
|---:|---|---|---|---|
| 3495 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 3468 `SI0103_M09_Montre_Small_Group_06` | `M09_A_Ins_Atrium_201` | -2163 20400 523 |
| 3498 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 3496 `SI0103_M09_Montre_Small_Group_05` | `M09_A_Ins_Atrium_201` | -73 20400 1362 |
| 3501 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 3499 `SI0103_M09_Montre_Small_Group_04` | `M09_A_Ins_Atrium_201` | -109 20400 -1578 |
| 3504 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 3502 `SI0103_M09_Montre_Small_Group_01` | `M09_A_Ins_Atrium_201` | 724 20400 -808 |
| 3507 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 3505 `SI0103_M09_Montre_Small_Group_03` | `M09_A_Ins_Atrium_201` | -2173 20400 -705 |
| 3510 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 3508 `SI0103_M09_Montre_Small_Group_02` | `M09_A_Ins_Atrium_201` | 726 20400 606 |
| 4537 | `SI0103_M09_Montre_Swords_Glass_01WHOLE` | `SI0103_M09_Montre_Swords_Group_02` | `M09_A_Ins_Office_301` | 5300 21081 -760 |
| 4540 | `SI0103_M09_Montre_Swords_Glass_01WHOLE` | `SI0103_M09_Montre_Swords_Group_01` | `M09_A_Ins_Office_301` | 5300 21081 540 |
| 4816 | `SI0103_M09_Montre_Swords_Glass_01WHOLE` | `SI0103_M09_Montre_Swords_Group_02` | `M09_A_Ins_Elevators_101` | 2465 19700 -339 |
| 4819 | `SI0103_M09_Montre_Swords_Glass_01WHOLE` | `SI0103_M09_Montre_Swords_Group_01` | `M09_A_Ins_Elevators_101` | 2465 19700 151 |
| 4897 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 4895 `SI0103_M09_Montre_Small_Group_09` | `M09_A_Ins_Atrium_301` | 726 21100 607 |
| 4900 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 4898 `SI0103_M09_Montre_Small_Group_08` | `M09_A_Ins_Atrium_301` | 724 21100 -807 |
| 4903 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 4901 `SI0103_M09_Montre_Small_Group_07` | `M09_A_Ins_Atrium_301` | -110 21100 -1578 |
| 4906 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 4904 `SI0103_M09_Montre_Small_Group_06` | `M09_A_Ins_Atrium_301` | -2162 21100 522 |
| 4909 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 4907 `SI0103_M09_Montre_Small_Group_05` | `M09_A_Ins_Atrium_301` | -73 21100 1362 |
| 4912 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 4910 `SI0103_M09_Montre_Small_Group_03` | `M09_A_Ins_Atrium_301` | -2172 21100 -705 |
| 5364 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 5362 `SI0103_M09_Montre_Small_Group_06` | `M09_A_Ins_Atrium_101` | 725 19700 606 |
| 5367 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 5365 `SI0103_M09_Montre_Small_Group_05` | `M09_A_Ins_Atrium_101` | 723 19700 -808 |
| 5370 | `SI0103_M09_Montre_SamuraiSuit_00_Whole` | 5368 `SI0103_M09_Montre_Small_Group_04` | `M09_A_Ins_Atrium_101` | -2293 19700 -131 |

Each samurai group (`SI0103_M09_Montre_Small_Group_NN!SI0103_M09_Montre_SamuraiSuit_00`) holds `_Whole`
(intact, with the controllers), `_Remain` (what is left) and, in the first group only, the shard set; next
to it in the room are a plinth object and a `CoverBoxM_00`. Shard sets for the others are in
`CloneGroup_Locations/M09_A/...` (9 x `..._SamuraiSuit_00_Shards`, nodes 10140..10340). The campaign adds
14 player-cover boxes `Markup!HeroCovers!Statues!PlayerCoverColiStatue#NN` (nodes 11860..11873) and
6 `Samurai_Light#NN` spot lights per upper floor (nodes 3877..3882, 5353..5358).
Breaking sound of every case: `SFX/Impacts/GlassBreak/Default/Glass_Break_Small.wav`.

Loot mechanism seen in stock Dog Days F01 (for whoever authors it; behaviour not tested here): the loot
object is a group with `OnlineMoneyContainer` (F01 node 2471, `PC0800_F01_Alu_Case_8_38`) whose child
`Attach_loot_A_00` carries `OnlineMoneyCtrl` ('ZMONEYCTRL_GAMEMODE_ALL', 68000, 'ZMONEYCTRL_TYPE_CONTAINER',
...). Per stock FA level: `OnlineMoneyCtrl` 133..183, `OnlineMoneyContainer` 0..58, `TriggerLootDepleted` 7
(always on `Gameplay!merc_bot_squad!Squad#NN\050_Timer_done_looting`, i.e. it tells the bot heisters the loot
is gone; it is NOT a "room cleared" trigger).

### 3.3 The main room - candidates

Soldiers counted by start position inside the room's bound (several squads start elsewhere and walk
in, so read this as a guide):

| room | node | bound (x y z)-(x y z) | floor | soldiers | cases | notes |
|---|---:|---|---:|---:|---:|---|
| `M09_A_Ins_Office_301` (boardroom) | 4019 | (3420 20971 -1317)-(5852 21822 1117) | 592 m2 | 19 | 2 sword | behind the main window; `020_Office` squads: `Squad_Retomoto` (boss `C_RetomotoBoss_01_Tokyo_00`, node 299 group), `Squad_AroundTable` (8), `Squad_Guards_Inside_01..04` (10); objectives `MissionObjective_030_KillAll` (node 11817) and `_040_Briefcase` (11834) |
| `M09_A_Ins_Reception_301` | 3885 | (2628 20995 -1550)-(3420 21510 1350) + 4 small | 230 m2 | 12 | 0 | corridor between boardroom and atrium |
| `M09_A_Ins_Atrium_301` | 4894 | (-2800 21000 -2200)-(1801 22400 2000) | 1932 m2 | 4 | 6 samurai | top gallery |
| `M09_A_Ins_Atrium_201` | 3397 | (-2800 20300 -2200)-(1400 21000 2000) | 1764 m2 | 7 | 6 samurai | middle gallery |
| `M09_A_Ins_Atrium_101` | 5361 | (-2800 19600 -2200)-(1400 20300 2000) | 1764 m2 | 18 | 3 samurai | atrium floor |
| `M09_A_Ins_Elevators_101` | 4725 | (1202 19600 -1804)-(3204 20177 1631) | 688 m2 | 19 | 2 sword | elevator lobby |

"Once everyone in it is dead": the campaign already counts deaths with `TriggerCounter` fed from
`ZSquadScript` (e.g. `070_Elevators!TriggerCounter_AllDeadElevator`, node 11704: count 9 -> `Music!14_AllDead`).
Both controllers are registered in Dog Days. That is a mechanism the level itself uses; wiring it to
loot is authoring, not tested.

### 3.4 Front entrance, road, places for a van (B)

| node | object | position / box | note |
|---:|---|---|---|
| 7082 | `SI0400_JPN_Entrance01!SI0400_JPN_Entrance_Root` | (2320 10 -7327)-(3397 1870 -5653) | the entrance structure |
| 7307 | `InsideBound_02` of the lobby | (2550 39 -7300)-(2650 839 -5700) | the doorway: 16 m wide, centre (2600, -6490) |
| 7080, 7081 | `SI0400_JPN_Entrance01!CoverBoxH_104 / _103` | (2605 160 -7230), (2605 160 -5750) | cover at both door jambs |
| 6946 | `Doors_PROJECT` | (3257 23 -5925) | door object (no model box) |
| 5102 | `SO0400_JPN_Facade_Entrance_A_01` | (2320 -100 -8837)-(9200 2730 -2595) | facade around it |
| 16342, 16349 | `MapObjectives!Arrow_01a`, `Arrow_01b` | (2521 22 -6524), (3920 46 -6476) | campaign arrows through the door |
| 5086 | `SO0102_JPN_Tiles_A_01` | (-300 0 -11700)-(5300 206 -1300) | forecourt paving |
| 5184, 5187 | `SO0102_JPN_JapanGarden_A_01 / _02` | around (900 0 -3000), (900 0 -10000) | gardens left and right of the path |
| 5080, 5078, 5084, 5081, 5083, 5085 | `SO0100_JPN_Street_Wide_*` | x -5700..-300, z -17500..-1500 | the road in front of the tower (centre line x -3000) |
| 4844 | `SO0100_JPN_Street_T_Section_D_01` | (-8700 -1 -23900)-(2700 20 -17500) | T junction at the south end |

Road pieces `SO0100_JPN_Street* / Sidewalk*` per room: Retomoto_Square 16, x -8700..2700, z -23900..-1500;
Street_01a 37, z -1500..34900; Overpass 15; Bus_Terminal 27 (y -980); Hotel_Street 35 (y -1056..-775).

The road is straight along z at x -5700..-300. From the door (2600, -6490) the campaign's play space on
it runs from the south level bound (z about -11400..-12700) to the far north road block (z about 13400):
roughly 250 m of street.

Places a van could wait (PROPOSALS; positions of things that already exist there):

| place | position | distance from the door | what is there now |
|---|---|---:|---|
| south road block | (-2208 0 -12506) | about 77 m | static `Vehicles_static!Police!V_JPN_SWAT_Van_South` (node 1476, 14 entities) and police car 1590 at (-1189 32 -12382) |
| first north road block | z 3602..3911, x -4090..-1901 | about 115 m | 3 static cars (nodes 1790, 1840, 1940) |
| SWAT truck north | (-3588 2 10886) | about 185 m | static `V_JPN_SWAT_North` (node 1462) |
| far north road block | z 13131..14404, x -4228..-2426 | about 210 m | 4 static cars (1490, 1540, 1640, 1690); `LevelBound_North` here |
| campaign's own van | (-24630 -979 8958) | 313 m in a straight line, longer by the route | `V_USA_GetawayVan_Chase_00` (node 11585, 31 entities) inside `CutScenes/M09/M09B_Bus_Station_Exit.zip`: a real van model, in the bus terminal |
| campaign getaway car | (-25545 -979 19131) | further | `Civilians!010_GetawayStreet!GetawayCar\Getawaycar\Ground_01` (ZHavokCar, node 11205); driver `Mercenaries!MercDriverSquad` at (-32620 -998 13107) |

Static vehicles on the map (V_Bus_Japan_Static x20, V_JPN_Civilian_B2_A x12, Taxi_Classic_Red x10, Taxi_Classic_Green x7, V_JPN_Civilian_B x5, V_JPN_Civilian_A x2, V_JPN_Civilian_D x2, V_Car01 x1, V_JPN_Civilian_E x1, V_JPN_Civilian_D2 x1, V_JPN_Civilian_D3 x1, V_JPN_Police_RetoFront02 x1, V_JPN_SWAT_North x1, V_JPN_SWAT_Van_South x1, V_JPN_Police_A_Group_00#02_South x1, V_JPN_Police_RetoFront01 x1) block and furnish the road; police ones:

| node | static vehicle group | position x y z |
|---:|---|---|
| 1412 | `Vehicles_static!Police!V_JPN_Police_RetoFront02` | 147 21 -6408 |
| 1462 | `Vehicles_static!Police!V_JPN_SWAT_North` | -3588 2 10886 |
| 1476 | `Vehicles_static!Police!V_JPN_SWAT_Van_South` | -2208 0 -12506 |
| 1490 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#10` | -4228 5 14367 |
| 1540 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#06` | -2531 5 14404 |
| 1590 | `Vehicles_static!Police!V_JPN_Police_A_Group_00#02_South` | -1189 32 -12382 |
| 1640 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#05` | -2426 5 13131 |
| 1690 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#07` | -3456 5 14149 |
| 1740 | `Vehicles_static!Police!V_JPN_Police_RetoFront01` | 38 21 -7382 |
| 1790 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#01` | -1901 5 3911 |
| 1840 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#03` | -3493 5 3805 |
| 1890 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#08` | -3337 1126 7188 |
| 1940 | `Vehicles_static!Police!V_JPN_Civilian_B2_A_Group_00#04` | -4090 5 3602 |

Stock Dog Days FA escape vehicles come with their own objects (F01: `Animation/` 549 entities,
`AllyEscapeBox` in F02 / F06 / F08), so the van itself would be Dog Days'; only its place is needed here.

---------------------------------------------------------------------------------------------------

## 4. Campaign scripting to remove

### 4.1 By controller (campaign-gameplay part only)

| controller | M09_A | M09_B | registered in Dog Days |
|---|---:|---:|---|
| MiniCutPosObject | 102 | 161 | yes |
| ZSoldier | 83 | 96 | yes |
| NoCoverBox | 18 | 83 | yes |
| ZSquadScript | 43 | 57 | yes |
| TriggerDelay | 46 | 52 | yes |
| MiniCutsceneRout | 38 | 55 | yes |
| SquadModifierBehaviour | 24 | 61 | yes |
| PlayerCoverCollision | 40 | 35 | yes |
| PassengerAnimPos | 0 | 66 | yes |
| TriggerBox | 26 | 35 | yes |
| ZCivilian | 21 | 36 | yes |
| DefendBehaviourRout | 21 | 28 | yes |
| PlayMusicLayerFade | 26 | 6 | yes |
| FlankingBehaviourRout | 14 | 13 | yes |
| AIDWrapper | 13 | 13 | yes |
| TriggerCounter | 7 | 17 | yes |
| Filter | 11 | 9 | yes |
| MiniCutSlot | 15 | 4 | yes |
| VehicleEffects | 0 | 18 | yes |
| VehicleMoveOnRoadBehaviourRout | 0 | 17 | yes |
| HavokCarScriptRout | 0 | 17 | yes |
| GatePath | 9 | 8 | yes |
| VehicleExitBehaviourRout | 0 | 16 | yes |
| CutSequence | 8 | 7 | yes |
| CCameraBox | 14 | 0 | yes |
| DeactivateGeom | 3 | 10 | yes |
| MatPosAnimProxy | 11 | 2 | yes |
| Ingamemap | 8 | 5 | **no** (engine skips it) |
| Appendage | 12 | 0 | yes |
| ZMercSquad | 8 | 4 | yes |
| GateGroup | 5 | 7 | yes |
| MatPosAnim | 1 | 9 | yes |
| MiniCutItemProxy | 8 | 1 | yes |
| Blocker | 2 | 7 | yes |
| LevelBound | 0 | 9 | yes |
| AttachGeomToBone | 0 | 9 | yes |
| PlayMusic | 3 | 5 | yes |
| CoopGate | 4 | 4 | yes |
| JumpPoint | 6 | 2 | yes |
| ActivateGeom | 3 | 4 | yes |
| PlayAudio | 5 | 2 | yes |
| PsychoticController | 3 | 4 | yes |
| ObjectiveReminder | 4 | 2 | **no** (engine skips it) |
| PathBlocker | 5 | 1 | yes |
| MiniCutCutProxy | 3 | 3 | yes |
| CheckPointSave | 3 | 2 | yes |
| CutSequenceList | 3 | 2 | yes |
| CutSequenceCamera | 3 | 2 | yes |
| CutSequencePostFilterCollection | 3 | 2 | yes |
| PostFilter | 3 | 2 | yes |
| Explode | 5 | 0 | yes |
| CutSequencePlayer | 3 | 2 | yes |
| ZFusionSquad | 2 | 2 | yes |
| SetPsychoModeDuration | 1 | 3 | yes |
| MiniCutSignal | 4 | 0 | yes |
| VehicleEnterBehaviourRout | 0 | 4 | yes |
| MapControl | 2 | 2 | **no** (engine skips it) |
| AdoptVisibility | 0 | 3 | yes |
| EndOfLevelTrigger | 1 | 1 | yes |
| RegisterSceneValName | 2 | 0 | yes |
| AIMonitor | 1 | 1 | yes |
| KaneLynchBox | 0 | 2 | yes |
| Cage | 2 | 0 | yes |
| FFCoverList | 1 | 1 | yes |
| MoveTo | 0 | 2 | yes |
| SceneChanger | 1 | 1 | yes |
| WarnBehaviourRout | 0 | 2 | yes |
| LookActivate | 1 | 0 | yes |
| PatrolBehaviourRout | 0 | 1 | yes |
| RappelCheckPoint | 1 | 0 | yes |
| AlteredVisionArea | 0 | 1 | yes |
| ZSetZDefine | 1 | 0 | yes |
| VideoPlayer | 0 | 1 | yes |
| Action | 1 | 0 | yes |
| RappellingBox | 1 | 0 | yes |
| AnimSequence | 1 | 0 | yes |
| WoundedFilter | 0 | 1 | yes |
| PlayerAction | 1 | 0 | yes |
| TriggerPsychoMode | 0 | 1 | yes |
| HuntBehaviourRout | 1 | 0 | yes |

Grouped by purpose (counts A / B):
- **Cut sequences**: `CutSequence` 8 / 7, `CutSequenceList` 3 / 2, `CutSequenceCamera` 3 / 2, `CutSequencePlayer`
  3 / 2, `CutSequencePostFilterCollection` 3 / 2; the five `CutScenes/M09/*.zip` groups (A: `M09_Scar_Retomoto_CAM`
  13, `M09_Enter_Elevator` 19, `M09A_Intro` 13, `M09A_Conference_Room` 19; B: `M09B_Exit_Elevator` 13,
  `M09B_Bus_Station_Exit` 51); `RegisterSceneValName` 2 / 0; `VideoPlayer` 0 / 1; `AlteredVisionArea` 0 / 1.
- **Mini cutscenes (in-game scripted animation)**: `MiniCutsceneRout` 38 / 55, `MiniCutPosObject` 102 / 161,
  `MiniCutSlot` 15 / 4, `MiniCutItemProxy` 8 / 1, `MiniCutSignal` 4 / 0, `MiniCutCutProxy` 3 / 3.
- **Mission / objectives**: `Ingamemap` 8 / 5, `ObjectiveReminder` 4 / 2, `MapControl` 2 / 2 (none of the three
  is registered in Dog Days), `EndOfLevelTrigger` 1 / 1, `SceneChanger` 1 / 1.
- **Checkpoints / saves**: `CheckPointSave` 3 / 2, `RappelCheckPoint` 1 / 0, `JumpPoint` 6 / 2.
- **Rappel**: `RappellingBox` 1 (node 11672), `RappelCheckPoint` 1, 5 `ZRopeLnkObj`
  under `Ropes!*` (nodes 1..10), 14 `CCameraBox` (most are `RappelCB_*`), `LookActivate` 1, `Blocker` 2,
  `Characters!Mercenaries!020_MercSquad_Rappel` (node 142), `Music!PlayMusic_Rappel`, `Rappel_Postfilter_Box` (6660).
- **Co-op airlocks**: `CoopGate` 4 / 4, `GateGroup` 5 / 7, `GatePath` 9 / 8, `Filter` 11 / 9, `KaneLynchBox` 0 / 2,
  `SetPsychoModeDuration` 1 / 3, `TriggerPsychoMode` 0 / 1, `PsychoticController` 3 / 4 (top-level `COOP!*`: 28 / 19 entities).
- **Squad scripts tied to campaign beats**: `ZSquadScript` 43 / 57, `SquadModifierBehaviour` 24 / 61,
  `DefendBehaviourRout` 21 / 28, `FlankingBehaviourRout` 14 / 13, `HuntBehaviourRout` 1 / 0, `PatrolBehaviourRout` 0 / 1,
  `WarnBehaviourRout` 0 / 2, `ZMercSquad` 8 / 4, `ZFusionSquad` 2 / 2, `TriggerBox` 26 / 35, `TriggerDelay` 46 / 52,
  `TriggerCounter` 7 / 17, `AIMonitor` 1 / 1; vehicles in B: `HavokCarScriptRout` 17, `VehicleMoveOnRoadBehaviourRout` 17,
  `VehicleExitBehaviourRout` 16, `VehicleEnterBehaviourRout` 4, `PassengerAnimPos` 66, `VehicleEffects` 18 (17 `ZHavokCar`,
  17 `ZRoad`, 7 `ZTrafficFlow`, 24 `ZEditorSpline`).
- **Bounds**: `LevelBound` 0 / 9 (B only; A has none).

### 4.2 Controllers on map objects (these stay with the map)

| controller (on map objects) | M09_A | M09_B | registered in Dog Days |
|---|---:|---:|---|
| ShotActivate | 179 | 459 | yes |
| HavokShatter | 302 | 29 | yes |
| NoCoverBox | 20 | 131 | yes |
| MsgForward | 103 | 0 | yes |
| VehicleEffects | 1 | 67 | yes |
| Audio_PlaySound | 3 | 59 | yes |
| MatPosAnim | 27 | 35 | yes |
| DeactivateGeom | 60 | 0 | yes |
| VertAnim | 1 | 48 | yes |
| PlayerCoverCollision | 29 | 14 | yes |
| SoundLimiterFade | 28 | 7 | yes |
| Spin | 21 | 1 | yes |
| MoveTo | 17 | 0 | yes |
| RelayMessageList | 10 | 4 | yes |
| AIDWrapper | 12 | 1 | yes |
| CoverStateChanger | 6 | 4 | yes |
| SoundSplineFollow | 2 | 6 | yes |
| ParamAnim | 0 | 7 | yes |
| PostFilterBox | 3 | 2 | yes |
| HavokShatterGlass | 0 | 4 | yes |
| PathBlocker | 0 | 4 | yes |
| AdoptVisibility | 0 | 2 | yes |
| Audio_GroupSources | 0 | 2 | yes |
| SoundSpline | 0 | 1 | yes |
| Elevator | 1 | 0 | yes |
| HavokDynamicsExtend | 1 | 0 | yes |
| PhysicsTest | 1 | 0 | **no** (engine skips it) |
| PhysicsBasedAnimated | 1 | 0 | yes |
| PhysicsEffect | 1 | 0 | yes |
| AIMonitor | 0 | 1 | yes |
| SoundVolumetricSource | 0 | 1 | yes |
| CheckInsideByType | 0 | 1 | yes |

### 4.3 Dropped scripts that hold geometry in the state the map needs

References from campaign objects into the map tree (audio excluded):

| part | controller | refs | targets | consequence if the script is just dropped |
|---|---|---:|---|---|
| A | `MatPosAnimProxy` | 17 (9 targets) | elevator groups `SI0101_JPN_Elevator_Ext_A_02 / _03 / _04`, `Int_A_03 / _04 / _05`; `SI0200_M09_Office_DDoor_Broken_01` | **elevator doors and the boardroom door are opened only by these.** Without them the doors keep their load-time state |
| A | `ActivateGeom` / `DeactivateGeom` | 11 / 3 | `M09_A_Ins_Office_301\Chairs_Post!PC0200_M09_OfficeChair_*_Static_NN`, `Chairs_Pre`, `SI0200_M09_Office_DDoor_01_01` | boardroom has two chair sets (before / after the blast) and two doors (whole node 4439 / broken node 4020); the scripts pick one |
| A | `AIDWrapper`, `AnimSequence`, `MiniCutPosObject` | 1 each | `Pillar01_00_Triggered\Pillar_Whole`, `Chairs_Pre`, `Pos_retom` | debris pillar; chair animation |
| B | `VehicleEffects` | 53 (4 targets) | `M09B_LOC_Outside.zip\Effects/AllocMany/...` car fire, tyre blow-out, SWAT explosion | effect templates only |
| B | `AdoptVisibility` | 11 (5 targets) | the five street / lobby rooms | crowd visibility |
| B | `MatPosAnimProxy` | 2 | lobby elevator `Ext_A_00` / `Int_A_00` | lobby elevator doors |
| B | `AIDWrapper` | 1 | `M09_B_Overpass_01a\SO0506_JPN_Facade_V_SlideDrs_01` | sliding doors at the overpass (`Activator_SlideDoors`, node 16320) |

Which of each pair is visible at load (door whole or broken, chairs pre or post, window pre or post)
is stored in the objects' own properties and was not decoded here: **not established**. For an FA round
that starts after the blast the map wants: window in `Post` state, `Chairs_Post`, door `Broken` (open).

---------------------------------------------------------------------------------------------------

## 5. Enemies, cover, navigation

`ZFFActor`: A 104, B 132. `ZFFPlayer`: 2 in each. No object or property string contains
"Retomoto_Squad" in either part; the nearest name is `AI_Players!Enemies!020_Office!Squad_Retomoto` in A (the boss).

A, by campaign area:

| first actor node | group prefix | squads | actors | controller | start positions box (x y z)-(x y z) |
|---:|---|---:|---:|---|---|
| 55 | `Characters!Hero!` | 1 | 2 | MapControl | (1243 25363 -877)-(1454 25363 -858) |
| 80 | `Characters!Mercenaries!` | 4 | 4 | ZSoldier | (1218 25357 -1152)-(1445 25358 -1032) |
| 199 | `AI_Players!Civilians!010_WindowsLife!` | 7 | 13 | ZCivilian | (4815 22301 -860)-(5932 23302 596) |
| 253 | `AI_Players!Civilians!020_Reception!` | 1 | 8 | ZCivilian | (-1781 19604 -1041)-(2125 21009 1272) |
| 273 | `AI_Players!Enemies!010_Roof!` | 2 | 7 | ZSoldier | (3721 25370 -782)-(5748 25529 401) |
| 313 | `AI_Players!Enemies!020_Office!` | 6 | 19 | ZSoldier | (3596 20991 -1037)-(5770 21012 502) |
| 417 | `AI_Players!Enemies!070_Elevators!` | 5 | 11 | ZSoldier | (1800 19601 -1555)-(3081 19606 1238) |
| 459 | `AI_Players!Enemies!060_Atrium_1st!` | 5 | 8 | ZSoldier | (2256 19602 -1196)-(2909 19603 1320) |
| 505 | `AI_Players!Enemies!050_Atrium_2nd!` | 4 | 7 | ZSoldier | (-2210 19602 -1947)-(-417 19605 1774) |
| 539 | `AI_Players!Enemies!030_Reception!` | 5 | 12 | ZSoldier | (2917 21001 -1138)-(3306 21005 730) |
| 601 | `AI_Players!Enemies!040_Atrium_3rd!` | 7 | 15 | ZSoldier | (-1901 19613 -1951)-(-255 21009 1703) |

B, by campaign area:

| first actor node | group prefix | squads | actors | controller | start positions box (x y z)-(x y z) |
|---:|---|---:|---:|---|---|
| 9989 | `Mercenaries!` | 5 | 5 | ZSoldier | (-32620 -998 -6390)-(6419 562 13107) |
| 10026 | `Hero!` | 2 | 2 | MapControl | (6428 563 -6306)-(6428 563 -6235) |
| 10041 | `Enemies!040_Busterminal!` | 7 | 20 | ZSoldier | (-24429 -977 8876)-(-3228 108 11270) |
| 10178 | `Enemies!010_RetoBldFront!` | 9 | 18 | ZSoldier | (-2615 3 -8147)-(5772 565 2739) |
| 10454 | `Enemies!020_Street!` | 25 | 51 | ZSoldier,AttachGeomToBone | (-7183 0 -19697)-(-788 1130 27589) |
| 11177 | `Enemies!030_Underpass!` | 1 | 2 | ZSoldier | (-6805 26 -18917)-(-6484 26 -18902) |
| 11223 | `Civilians!010_Underpass!` | 6 | 26 | ZCivilian | (-14934 -966 5434)-(196 34 14301) |
| 11369 | `Civilians!010_Street!` | 5 | 5 | ZCivilian | (-3343 -101 1066)-(1626 563 15118) |
| 11530 | `Civilians!000_Lobby!` | 1 | 5 | ZCivilian | (5756 562 -7807)-(6958 563 -7070) |

Enemy soldiers (`ZSoldier`, mercenaries excluded): A 79, B 91. A's are `C_Henchmen_01/02/03_Tokyo_*`,
`JPN_Guard_*`, `Henchman_Shooter`, `C_RetomotoBoss_01_Tokyo_00`; B's are `JPN_Police_*`, `SWAT_*`,
`JPN_Teargas_Police_01`, `Sniper_01`. Each squad is a top-level group `...!Squad_*` with a `ZSquadScript`,
behaviour children (`DefendBehaviourRout` etc.) and its actors as `<character>\Ground` (`ZFFActor` +
`ZSoldier`). Patrol data: one `PatrolBehaviourRout` in B, none in A; everything else is defend / flank
boxes and scripted moves. 24 `ZEditorSpline` in B's gameplay are vehicle roads, not foot patrols.
All of this is campaign pacing (waves released by trigger boxes) and would be re-authored, not reused.

Cover:

| | A | B |
|---|---:|---:|
| `CoverBox*` objects in the map (ZSTDOBJ) | 88 (`CoverBoxH` 34, `CoverBoxM` 27, `CoverBoxh` 27) | 392 |
| `CoverBox*` as ZBoxPrimitive in the map | 5 | 14 |
| `CoverBox*` in campaign gameplay | 1 | 44 |
| `PlayerCoverCollision` (map / gameplay) | 29 / 40 | 14 / 35 |
| `NoCoverBox` (map / gameplay) | 20 / 18 | 131 / 83 |
| `CoverStateChanger` (map) | 6 | 4 |
| `FFCoverList` | 1 (node 11677, empty list) | 1 (node 16355, empty list) |

Navigation mesh (`.gms` header +0x34; `kl_pf4.counts`, 13 x u16; header + arrays = block size in both):

| | offset | size | arrays 0..12 | `kl_pf4.convert` |
|---|---|---:|---|---|
| A | 0x158d80 | 117,674 | 2302, 1027, 109, 502, 48, 68, 1391, **15**, 0, 2407, 68, 0, 0 | **REFUSED**: array 7 not empty |
| B | 0x1caa30 | 365,268 | 7526, 3215, 354, 1739, 60, 138, 3877, 0, 0, 7993, 138, 0, 0 | converts |

A's 15 array-7 records (10 bytes each, as 5 x s16): (118, n, 47, 6658, -1) for n = 0..4;
(4433, n, 46, 6662, -1) for n = 1..5; (118, n, 44, -14847, -1) for n = 0, 2, 3, 4, 9. Three sets of five.
What they are is not established (A has 5 ropes and 5 elevators; that is a coincidence until shown
otherwise). M03's single array-7 record is the only other one known. **The tower cannot be converted
until array 7 is understood or shown to be safe to drop.** Arrays 8, 11, 12 are empty in both parts.
A also has `.gms` header +0x38 = 0x3f50 (B: -1); the converter overwrites it with -1; what A keeps there
is not established.

---------------------------------------------------------------------------------------------------

## 6. Music and sounds

A sound reference in a controller is an offset into the level's `.SND`; the definition there names the
`audio:` path and the wave (`+8` -> name, `+0x14` -> record -> `+8` wave path). Resolved for every
`PlayMusic`, `PlayAudio` and `Explode` of the two parts:

| part | node | object | controller | clip (wave name in the .SND bank) |
|---|---:|---|---|---|
| A | 6591 | `EndElevatorSounds` | PlayAudio | `LevelSetup/Level/M09_A/Cuts/M09A_Enter_Elevator/M09A_Enter_Elevator.wav` |
| A | 6663 | `Music!PlayMusic_TokyoAction` | PlayMusic | `Music/InHouse/Japan/M09_A/TakyoAction_V3_44_Layer1_Loop.wav`<br>`Music/InHouse/Japan/M09_A/TakyoAction_Layer2_TAmbient_Loop.wav` |
| A | 6685 | `Music!PlayMusic_Rappel` | PlayMusic | `Music/InHouse/Japan/M09_A/TokyoRappel_Loop_V2_44_Wind.wav` |
| A | 6686 | `Music!PlayMusic_Rooftop` | PlayMusic | `Music/InHouse/Japan/M09_A/Rooftop_V2_New_44_Layer1_Loop.wav`<br>`Music/InHouse/Japan/M09_A/Rooftop_Layer2_TAmbient_Loop.wav` |
| A | 11648 | `WindowBlowup!BombWindow03` | Explode | `SFX/Explosions/Bomb/Bomb_WarmUp/Bomb_WarmUp.wav`<br>`SFX/Explosions/Bomb/M09_Explosion_Window_Office/M09_Explosion_Window_Office_01.wav` |
| A | 11898 | `SFX!Introsounds` | PlayAudio | `LevelSetup/Level/M09_A/Cuts/M09A_Intro/M09A_Intro.wav` |
| A | 11899 | `SFX!CuttingRetomoto_Sound` | PlayAudio | `LevelSetup/Level/M09_A/Cuts/M09A_Scar_Retomoto/M09A_Scar_Retomoto.wav` |
| B | 9951 | `Mercenaries!000_EscapeSquad\EndofLevelSound` | PlayAudio | `SFX/Cutsequences/M09_B/M09_Tokyo_Exit.wav` |
| B | 11636 | `Music!PlayMusic_Tom#01` | PlayMusic | (no clip resolved) |
| B | 11637 | `Music!PlayMusic_Overpass` | PlayMusic | `Music/InHouse/Japan/M09_A/TokyoAction2a_MainGuitar_Layer1.wav`<br>`Music/InHouse/Japan/M09_A/TokyoAction2b_MainGuitarEtnic_Layer2.wav` |
| B | 11639 | `Music!PlayMusic_Tom` | PlayMusic | (no clip resolved) |
| B | 11640 | `Music!PlayMusic_End` | PlayMusic | `Music/InHouse/Japan/M09_A/TakyoAction_V3_44_Layer1_Loop.wav` |
| B | 11645 | `Music!PlayMusic_Start` | PlayMusic | `Music/InHouse/Japan/M09_A/TokyoAction2a_MainGuitar_Layer1.wav`<br>`Music/InHouse/Japan/M09_A/TokyoAction2b_MainGuitarEtnic_Layer2.wav` |

- B's `Music!PlayMusic_Tom` and `PlayMusic_Tom#01` (nodes 11639, 11636) name no clip ("tom" is Danish for empty).
- All 7 clips of `Music/InHouse/Japan/M09_A/` are used: `TakyoAction_V3_44_Layer1_Loop` +
  `TakyoAction_Layer2_TAmbient_Loop` (the action theme; started in A by `Music!06_Explosion`, i.e. at the
  window blast), `Rooftop_V2_New_44_Layer1_Loop` + `Rooftop_Layer2_TAmbient_Loop` (roof),
  `TokyoRappel_Loop_V2_44_Wind` (rappel), `TokyoAction2a_MainGuitar_Layer1` +
  `TokyoAction2b_MainGuitarEtnic_Layer2` (B, street). Each `PlayMusic` has two layers; 26 (A) + 6 (B)
  `PlayMusicLayerFade` children set the layer volumes at campaign beats (`Music!NN_*` `TriggerDelay`s).
- In `DM\PC_Def.str` (6739 clips): those 7 (32 kHz stereo; PCM codec 2 except the rappel clip, codec 4),
  8 clips `Music/InHouse/Japan/M05_A/*` (another level's club music - not Retomoto's), and
  `LevelSetup/Level/M09_A/Music/TokyoAction1`, `TokyoAction2`, `M09A_Rooftop` (codec 26, same lengths as
  the layer pairs: 211.2 s, 114.0 s, 220.7 s). That is the "15 + LevelSetup" of CLAUDE.md: 7 of the 15
  belong to this level.
- **None of the 18 is in the current `DD\PC_Def.str`** (9102 clips; 147 of the 306 clips with "M09" or
  "Japan" in the name are there, all dialogue) nor in the stock backup (5926 clips). The merge filter
  took Fragile Alliance clips only.
- `PlayMusic` / `PlayMusicLayerFade` are in the key tables of 10 of 12 Dog Days story levels and of **no**
  Fragile Alliance level of either game (F01..F09, M01/M02/M03/M06_FA_A). How an FA round gets its music
  is not established; do not assume a `PlayMusic` object simply works in an FA round.

Window and glass:

| sound | wave | where the wave is |
|---|---|---|
| window explosion | `SFX/Explosions/Bomb/M09_Explosion_Window_Office/M09_Explosion_Window_Office_01.wav` | `DM\PC_Def.str` (streamed); named in `M09A_Main.WHD` and `M09B_Main.WHD` |
| bomb warm-up | `SFX/Explosions/Bomb/Bomb_WarmUp/Bomb_WarmUp.wav` | `M09A_Main.WHD` / `.WAV` |
| window shatter | `SFX/Impacts/GlassBreak/Default/Glass_Break_Big.wav` (node 4616) | `M09A_Main.WHD` / `.WAV` |
| window crackle | `SFX/Impacts/Bullet/Glass/Window/Small/No_FlyIn/Impact_Window_Small_No_FlyIn_04.wav` (node 4448) | level bank |
| display cases | `SFX/Impacts/GlassBreak/Default/Glass_Break_Small.wav` | level bank |
| boardroom panic loop | `SFX/Ambiences/M09_A/Outside/Panic_Boardroom_01.wav` (node 11762 at (5477 21220 -104); switched by `SFX!GeomActivator_BoardroomSound` / `...OFF`) | `DM\PC_Def.str` |
| planting the bomb | `SFX/Environment/Effects/M09_A/M09_A_PlaceBomb_Kyd_01.wav` | `DM\PC_Def.str` |

Ambience objects (`Locations/M09_A/M09A_Audio.zip!*` 44 entities, `M09B_Audio.zip!*` 44) belong to the
map: atrium, office, roof, ventilators, elevator ding / door / music in A; lobby, crowd, highway, bus
terminal, street, police megaphone lines, siren in B. B's objects (map and gameplay together) carry 416 `Glass_Break_Small` and 85
car-fire sound references.

---------------------------------------------------------------------------------------------------

## 7. Size, limits, trouble

### 7.1 Counts

| | A | B | A + B | note |
|---|---:|---:|---:|---|
| entities | 11,926 | 16,646 | 28,572 | |
| - systems (dropped) | 6,247 | 5,786 | | |
| - map | 4,667 | 8,836 | **13,503** | pool categories 0/1/2/3: A 314 / 4097 / 70 / 186, B 924 / 7347 / 85 / 480 |
| - campaign gameplay | 1,012 | 2,024 | | categories A 297 / 694 / 0 / 21, B 630 / 1377 / 1 / 16 |
| map + level-specific `CloneGroup_Effects/AllocMany` | 5,669 | 9,806 | 15,475 | if those clone groups have to stay (1.2) |
| REF slots (`.gms` header[15]) | 67,193 | 26,927 | | REF ids are unique but sparse: A max 67,192 for 11,926 entities |
| textures (`.TEX` entries) | 1,086 (ids 128..1213) | 1,332 (ids 128..1459) | 2,418 | 17 / 18 animated lists |
| - distinct by (name, format, w, h, byte size) | 637 | 824 | 1,020 | 441 in both. Pixel data not compared: an estimate |
| - distinct names | 452 | 571 | 711 | 103 entries without a name in each |
| `.prm` chunks | 17,380 | 24,219 | | 29.7 MB / 34.7 MB |
| models used by entities (distinct `.prm` model records) | 1,526 (map 1,203) | 2,050 (map 1,783) | | entities with a model: map 3,793 / 5,969 |
| ZROOM in the map | 10 | 10 (+3 `Crowd!`) | | `.rmi` 20 / 24 boxes, `.rmc` 11 / 12 |
| file sizes | TEX 120 MB, ANM 15.5 MB, HVK 2.5 MB, SND 1.6 MB, oct 331 KB | TEX 154 MB | | |

Against Dog Days: with stock F01's systems (`mainsceneincludes_multiplayer.zip` 3417 + `CloneGroup_Effects`
5087 + `Heroes!` 32, per CLAUDE.md) the combined map is about 13,500 + 8,500 = 22,000 entities before the
authored FA layer; the largest stock level has 42,915. Textures: 2,418 + the donor's (about 1,270) stay
under the 4096 table even with no de-duplication. Whether a REF id as high as 67,192 matters depends on
the graft renumbering REF ids: not established.

### 7.2 Classes in the map

| class (map objects) | M09_A | M09_B | note |
|---|---:|---:|---|
| ZSTDOBJ | 3658 | 5715 |  |
| ZParticleEmitter | 200 | 1111 |  |
| ZGROUP | 180 | 817 |  |
| ZSNDOBJ | 164 | 455 |  |
| ZBoxPrimitive | 79 | 243 |  |
| ZAllocMany | 123 | 96 |  |
| ZSHADOWMESHOBJ | 98 | 54 | kl_gms.RETYPE -> ZSTDOBJ |
| ZScatterObj | 14 | 117 | scatter: .prm record differs (256 B vs 144 B) |
| ZLNKOBJ | 1 | 71 |  |
| ZOMNILIGHT | 19 | 52 |  |
| ZSPOTLIGHT | 27 | 15 |  |
| ZBOUND | 18 | 20 |  |
| ZHavokRigidBody | 8 | 28 |  |
| ZParticleTemplate | 33 | 0 |  |
| ZROOM | 10 | 10 |  |
| ZGateLightOmni | 12 | 0 |  |
| ZENVIRONMENT | 5 | 7 |  |
| ZAMBIENTOCCLUSION | 4 | 5 |  |
| ZGateLightSpotSquare | 2 | 7 |  |
| ZSPOTLIGHTSQUARE | 5 | 4 |  |
| ZEditorSpline | 1 | 5 |  |
| ZCloth | 3 | 0 |  |
| ZBackdrop | 1 | 1 |  |
| ZEnvSampler | 1 | 0 | kl_gms.RETYPE -> ZSTDOBJ |
| ZBloodSplatters | 0 | 1 |  |
| ZBloodStains | 0 | 1 |  |
| ZBulletMarks | 0 | 1 |  |
| ZDummy | 1 | 0 |  |

No map class is missing from Dog Days' exe. `ZIngameMapGroup` (the one Dead Men-only class) occurs once
per part, in the systems. In campaign gameplay only: `ZHavokCar` 17 (B), `ZRoad` 17 (B), `ZTrafficFlow` 7 (B),
`ZHFlowFF2M09` 3 + `ZHFlowLnkObj` 6 (B crowd), `ZRopeLnkObj` 5 (A), `ZFFActor`, `ZFFPlayer`, `ZFadeFullScreen`.

Controllers used by these two levels and not registered in Dog Days: `Ingamemap`, `ObjectiveReminder`,
`MapControl` (campaign gameplay) and `PhysicsTest` (1, on a map object in A). The engine skips unknown
controller names.

### 7.3 Trouble for the conversion, most serious first

1. **A's navigation mesh: array 7 has 15 records** - `kl_pf4.convert` refuses the level (section 5).
2. **Baked lighting in the `.prm`.** `kl_prm.find_descriptors` (32-byte descriptors with a zero tail)
   finds 1,897 in A and 2,957 in B. Another 755 (A) and 966 (B) 32-byte chunks name a valid vertex chunk
   and a valid index chunk but have a non-zero tail - the shape CLAUDE.md describes for descriptors
   with baked lighting. Heuristic count, not a model-graph walk. Both parts also carry per-room light
   objects (`Light0..Light5_<room>_Chunk0` models, e.g. A nodes 6046, 6082, 6489; B node 5198).
3. **Scatter objects**: `ZScatterObj` 14 in A, 117 in B (all in the map). Their `.prm` records are 256
   bytes in Dead Men and 144 in Dog Days with unrelated content. The number of lType-9 records in the
   `.prm` files was not counted.
4. **References from the map into Dead Men's systems** (1.2): A 60, B 78. Dropped targets leave dangling paths.
5. **Paired states** (4.3): window pre / post, chairs pre / post, door whole / broken, elevator doors -
   the initial state must be set by hand once the campaign scripts are gone.
6. **`Explode`** has 15 values here and 18 in Dog Days (F01 node 7406); it goes through the schema
   converter like any other controller, but 3 values will be defaults.
7. **Rooms with skylines**: `M09_A_Out_CityScapeFront` (311 entities) and `M09_B_Skyscrabers_01a` /
   `M09_B_Street_01a` hold two copies of the city, 30 m x 70 m apart. In one map one of them should go,
   but each is a ZROOM with octree trees and gates: removing a room is a re-bake of that part's `.oct`.
8. **`.ANM`**: A's is 15.5 MB; campaign animation (mini cutscenes, cut sequences) is most of what would be
   dropped, but map objects with `MatPosAnim` (27 / 35) and `VertAnim` (1 / 48) need their clips. The
   `.ANM` converter does not exist yet (CLAUDE.md).
9. **Retyped classes in the map**: `ZSHADOWMESHOBJ` 98 / 54 and `ZEnvSampler` 1 / 0 are flattened to ZSTDOBJ
   by `kl_gms.RETYPE` today.
10. **Sound**: 164 (A) + 455 (B) `ZSNDOBJ` on the map and hundreds of `ShotActivate` / `HavokShatter`
    sound references index the Dead Men `.SND` of each part; two parts means two banks to merge.

Not looked at: `.MAT` contents, `.HVK`, `.sgd`, `.sgp`, gate records, the `.oct` itself, which room each
`.rmi` box names (my REF lookup did not resolve them to rooms, so no claim is made).
