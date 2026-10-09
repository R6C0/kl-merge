# Retomoto Tower: the loot's props and whether it can be picked up

Owner, 2026-10-09 22:00, after playing `<work>\build\x_chunks\retomoto_wardrobe`: *'could you change the
props of the money - its bags all around on retomoto tower; it should be BRIEFCASES for sure in that
start room, and make the ones on the LEFT SIDE FROM SPAWN closer to the outer ring since u cant actually
pick the money up; the statue ones - use a good prop replacement for that'.*

Tool: `tools/kl_fa_loot.py` (agent y-loot). OFFLINE: nothing here was run in the game, nothing is
installed. Pictures and the full survey text: `<work>\research\loot\` (`final.txt`, `*.png`, `props\`).
GUESS = a value not copied from a stock object and not measured; ASSUMPTION = fits the evidence, not proven.

## 0. Result

| asked | built | proven offline | not proven |
|---|---|---|---|
| briefcases in the start room | the six boardroom stacks show Dead Men's Fragile Alliance briefcase (M01_FA_A `DropMoney!KillDrop!Suitcase`, the model whose materials are the campaign's Retomoto briefcase), 1.25 x | model root with vertex data, 3 materials each with a compiled shader, 5 textures, 18 chunks all in dead indices, lies on the table top inside its rim | that it is drawn, its size, how it reads from the door |
| the left ones cannot be picked up | they could not: the row at z -120 lay 134 in from the table's rim, 190 from the nearest place to stand, reach 120. All six now lie 33 in from the two long rims, radius 125 (reach 165) | walk test + the pick-up test read in kl2.exe: nearest standing place 75 .. 112 away, 52 .. 89 to spare | the pick-up test's branch (2), the E prompt |
| statue loot: a good prop | the loot at each of the 15 samurai cases IS that case's armour: a new model root over the case model's own two armour meshes; the case keeps frame, glass, hull. Taken = the armour is gone | drawn once (not by case and loot both), stands in its case, 2 new chunks in dead indices, reach as before (91 .. 98 away, reach 190) | that taking it hides it (as it hid the bags), how the '$' marker sits on it |

Final folder: `<work>\build\y_loot\retomoto_loot` (F01_Main.zip 212 MB, KLJoin.ini, KLWardrobe.ini,
chars.json, the sound files). `python tools/kl_fa_loot.py check <folder>`: kl_fa_loot.check 0 problems,
kl_fa.check 0 CRASH / BROKEN, kl_impact.check 0 (bones, chunk limit, surfaces), kl_chars.undrawn 0,
kl_arms check 0 findings. kl_graft.verify on the build: the one known problem of each step (27 particle
template names do not resolve, stock M09_B has 24; 39, stock M09_A 36). Chunk table 65,119 entries:
unchanged (re/prm_limit.md). The build was made twice from scratch (`kl_fa_loot.py test`, 22:25 and
23:45): all 30 members of the two archives are byte-identical; and `kl_fa_loot.py dress` of the lead's
`<work>uild\play3s` gives the members of `<work>uild\y_loot\light` byte for byte.

Against the level the owner plays, 29 nodes differ: the 21 loot objects (place, turn, model; the six on the
table also their TriggerBox2 radius) and the eight heroes' `Ground` model number (the wardrobe took other
dead indices). No entity and no controller was added or removed.

## 1. Every loot object of the level the owner played

`python tools/kl_fa_loot.py survey <work>\build\x_chunks\retomoto_wardrobe\F01_Main.zip` (text in
`research\loot\final.txt`). 133 objects carry an OnlineMoneyCtrl; 112 are F07's drop pool
(ZMONEYCTRL_TYPE_DROP: what a dead player drops) and are not loot. The 21 that are:

- class ZSTDOBJ, top-level `FASpecials!DropMoney!MoneyStack_093 .. _100` and
  `FASpecials!DropMoney!TeamModeDropMoney!TM_MoneyStack_013 .. _025` (kl_fa_author clones of F07's stacks);
- controllers `OnlineMoneyCtrl` (ALL, value, NORMAL, NORMAL, 15000, 0.2, 1, 30, 800, 1000, 0, 0) and
  `TriggerBox2` ([itself], 1, radius, 1, 0, AI_TRIGGER_WITH_ACTIVATOR, 0);
- model 1802 on every one = F07's money prop, ONE mesh, material `Sportsbag_01`, 48 x 39 x 82: the bag.
  F07 has no other money prop (stack / box): its 5 x 800,000 loot and its drop pool show the same bag.

| objects | where | value | radius | at load | pick-up (walk test, 2) |
|---|---|---|---|---|---|
| 15: MoneyStack_093..100, TM_013..019 | the samurai cases, three floors of the atrium (y 19700 / 20400 / 21100), at the case's own origin, inside the glass | 150,000 | 150 | shown | ok, all 15: a place to stand 91 .. 98 away, reach 190 |
| TM_021, 023, 025 | boardroom table, z 20 (the RIGHT row from the balcony), 9 in from the rim, the bag hanging over the edge | 300,000 | 80 | hidden until the room's squads are dead | ok: 50 away, reach 120 |
| TM_020, 022, 024 | boardroom table, z -120 (the LEFT row), 134 in from the rim | 300,000 | 80 | hidden, as above | **OUT OF REACH**: nearest place to stand 190 away, reach 120 |

**Left and right.** The heisters start on the balcony (x 5895..6151) facing -x into the room. Turning
right raises atan2(x, z) (klhook\klauto.c's heading against mouse counts, run PX3), so facing -x the left
hand is **-z**. The table (`PC0200_M09_ConferenceTable_A_01` at (4931, 20990, -100), not turned) has its
top at y 21070, boat-shaped: z -257..29 in the middle, -237..9 at the ends, x 4474..5388 (read off its top
mesh `Wood_Black_02a_M09` by `kl_fa_loot.table()`). kl_fa_author's rows stood at z -120 and z 20: the row
at -120 is the left one from the spawn, and it sits in the MIDDLE of a 286-wide table - the nearest
floor a player can stand on is beyond the rim at z -310 (the chairs' side), 190 away. That is the row the
owner means; the reason is 'on the far side of the table top from any place to stand, pick-up radius too
small', not collision around the stack itself. Nothing else of the 21 fails the test: no stack is inside
furniture, behind a wall or over the atrium's void.

'The outer ring' is read as the RIM of the table (the walkway round it, where a player stands). If the
owner meant something else - the ring of the atrium, the room's walls - section 7.

## 2. The pick-up, read in kl2.exe

A money object's `TriggerBox2` is ZTriggerBox2 (vtable 0xbc953c; init = slot 13, 0x750350; update = slot 25,
0x626ec0). The update asks the game data for the actors round its node (0x5891f0) and tests each with
0x783e60. With h = the HORIZONTAL distance between the actor's node (a player's: his feet) and the
trigger's node and R = stored field 2 + 40 (double at 0xb23668):

    h <= R    and    |actor y - node y| <= 100 + sqrt(R * R - h * h)        (double at 0xb3dde8 = 100)

So radius 80 takes from 120 away on the floor plan and from any height a table has; nothing in the test
looks at walls, glass or facing. By this test the stacks inside the glass cases can be taken from outside
the glass and the middle of the table cannot - which is what the owner reports for the table. (Which
stacks made up the owner's $2,080,000 on play2 is not known.)

ASSUMPTION: that a money trigger takes this branch. The update takes it when the byte at +0x3d is set,
else it asks the node's own volume (0x68d030); +0x3c / +0x3d are the object's two bools, and both stored
bools (fields 1 and 3) are 1 on every money trigger of this level and of stock F02.
NOT READ: what happens after the trigger fires (OnlineMoneyCtrl's handler, the E prompt, the hiding).

**The walk test** (`kl_fa_loot.walk`, kl_escape.Walk's grid of 20 x 20 cells with every floor of a cell kept
apart): collision with a player's bits only (ASSUMPTION `HERO_BITS` 0x28, kl_fa_author's), hidden entities
out, the blast's switches applied (16 off, 19 on), flooded from the eight START points; a place counts
when a body of radius 30 (ASSUMPTION `BODY`: run J1, re/retomoto_fa.md 10.1) fits. The boardroom's door
leaves are key-framed shapes that fill the doorway in the .HVK and do not stop a player in the game (runs
RT3 / RT4, every round the owner played), so two places a player has stood on beyond the door are further
starts (`WALKED`). 89,993 cells reached, floors y 19599..21040.

**Control on a stock level:** `kl_fa_loot.py survey F02` - all 24 of stock F02's bags pass (a place 8 .. 64
away, reach 120). The test does not fail what the game is known to allow. (Stock levels are walked
locally, from the floors round each bag: F02's heisters start in a train that static collision does not
join to the loot's wagon.)

## 3. Briefcases: every case prop of both games

`python tools/kl_fa_loot.py props <work>\research\loot\props` (entity names matching
briefcase | suitcase | alu_case | attache, with a model; one picture each, four views):

| game | prop | levels | model | note |
|---|---|---|---|---|
| DM | `DropMoney!KillDrop!Suitcase` | M01_FA_A x4 | 3 meshes Briefcase_Brass_01a / _Fabric_01a / _Side_01a, 36 x 9 x 34, lying flat | **Dead Men's own Fragile Alliance money case** (by its path: the kill drop) |
| DM | `Money!KillDrop!Briefcase` | M06_FA_A x4 | the same model | |
| DM | `Briefcase_Lid` / `_Bottom` / `_Handle` | M09_B x1 (cut scene `M09B_Bus_Station_Exit`) | the same three materials, in parts, standing open | the Retomoto briefcase the campaign level is about; a cut-scene rig, not a prop |
| DM | `Pc0100_M03_Suitcase_A` / `_B` | M03_A x2 each | black leather, OPEN, papers spilling, 183 x 195 | too large, open only |
| DM | `PC0104_JPN_Suitcase_A` | M09_B x1 | the same open shape with Japanese papers | open only |
| DD | `PC0200_F01_BriefcaseClosed` | F01 x3 | 1 mesh Plastic_F01_Briefcase_01a, 70 x 14 x 60, geometry off its origin | stock Subway's set dressing; option `--case dd` |
| DD | `PC0200_F01_BriefcaseOpen` | F01 x1 | 4 meshes, with documents | open, with papers - not money |
| DD | `Attach_loot_A` + `Attach03_suitcase_lid` + `Attach04_suitcase_lock` + `Attach_static_stuff` | F01 x58 | Metal_Alu_Case_Loot_01_F01 | Subway's aluminium LOOT CASE: an animated rig of four parts on a bone (`fake_sp01`), opened by a sequence - not one prop |
| DD | `Ground_Suitcase` | L01, L04 | 6 meshes, the Briefcase_* materials, standing upright | Dog Days kept Dead Men's case as airport baggage |
| DD | `TrolleySuitcase` | L01 x2 | Fabric_L11_Baggage, a trolley bag | not a money case |

F07 (the host of this graft) has none.

**Chosen: Dead Men's Fragile Alliance briefcase** (`CASES['dm']`). It is the game's own money case, it is the
prop of the level's story, it is one closed model with no rig, and it is small. It has no opened state;
neither Dead Men FA map swaps it. The only open / closed pair of either game that is a plain prop is
Subway's `PC0200_F01_BriefcaseClosed` / `Open`, and the open one shows papers. So: closed cases, and a
case that is taken disappears (as the bag did). An opening case would need Subway's four-part rig and its
sequence - not attempted.

How it gets in (`kl_fa_loot.case_model`): `kl_chars.Source('M01_FA_A')` (the converters kl_graft uses for a
Dead Men level: kl_prm / kl_mat / kl_tex) -> `kl_prmgraph.extract` of root 6380 -> the copy's vertices and
the root's box x 1.25 -> `kl_texmat.merge_tex` / `merge_mat` (3 material slots, 5 textures) ->
`kl_prmgraph.append` (18 chunks, all into dead indices; the build stops if the chunk table would grow) ->
`kl_light.fit_shaders` on the three new slots against the level's .fxc + the shared union (0 switched off,
0 unresolved). The root's octree record is left out (root +0x1c = 0, as 597 drawn ZSTDOBJ of stock F07):
a bullet leaves no mark on a case.

Size: GUESS `CASE_SCALES['dm']` 1.25 (Dead Men's model is 36 wide; 45 is a real attache case). No stock entity of
F02 / F07 has a scaled matrix, so the size is in the vertices. Turn: GUESS `CASE_YAW` (8, -6, 11 degrees
off square per column), handle toward the rim.

Places (`kl_fa_loot.dress`): for each of the three columns x 4750 / 5000 / 5250 the two stacks go to the
table top's own rim at that x, `RIM` 33 in (GUESS: the case's handle side 8 from the edge), y = the top:

| stack | was | now | side from spawn | stand | away | reach |
|---|---|---|---|---|---|---|
| TM_MoneyStack_020 | (4750, 21076, -120) | (4750, 21070, -220) | left | (4750, -310) | 89 | 165 |
| TM_MoneyStack_021 | (4750, 21076, 20) | (4750, 21070, -7) | right | (4750, 70) | 77 | 165 |
| TM_MoneyStack_022 | (5000, 21076, -120) | (5000, 21070, -222) | left | (4990, -310) | 87 | 165 |
| TM_MoneyStack_023 | (5000, 21076, 20) | (5000, 21070, -5) | right | (4990, 70) | 75 | 165 |
| TM_MoneyStack_024 | (5250, 21076, -120) | (5250, 21070, -214) | left | (5190, -310) | 112 | 165 |
| TM_MoneyStack_025 | (5250, 21076, 20) | (5250, 21070, -13) | right | (5250, 70) | 83 | 165 |

Radius 80 -> 125 (`ROOM_REACH`): the value of all 117 stock OnlineMoneyContainer triggers (re/escape.md
4.1); 80 was stock F02's bags, which lie on the floor. With 80 the left row would pass by 8 .. 33 only
(under `MARGIN` 20 for TM_024, where a chair narrows the standing room). The right row moved 27 IN: the
bags hung over the edge, a case's footprint has to be on the top (check).

Top view from the balcony (balcony below the page, up = -x, LEFT = -z as in the game; one cell 40 x 40;
`#` table top, `.` a place a player can stand, capitals = now, small = before):

             z -480          280
      x  4400  ...................
      x  4440  .....        ......
      x  4480  ..... ###### ......
      x  4520  ..... ###### ......
      x  4560  ..... ###### ... ..
      x  4600  ..... #######..  ..
      x  4640  ..... #######......
      x  4680  ..... #######......
      x  4720  ..... A##a#Bb......
      x  4760  ..... #######......
      x  4800  ..... #######  ....
      x  4840  ..... #######  ....
      x  4880   .... #######.....
      x  4920   .... #######.....
      x  4960   .... #######.....
      x  5000  ..... C##c#Dd......
      x  5040  ..... #######......
      x  5080  ..... #######......
      x  5120  ..... #######......
      x  5160  ..... #######......
      x  5200  ....  #######......
      x  5240  ...   E##e#Ff......
      x  5280  ..... ###### ......
      x  5320  ..... ###### ......
      x  5360  ..... ###### ......
      x  5400  ........  .........
      x  5440  ........  .........
                        [ window x 5850, balcony, spawn x 6000 ]

Pictures: `research\loot\new_briefcase.png` (the prop), `before_table_from_above.png` /
`new_table_from_above.png` and `..._from_balcony.png` (the table with its six, textured, kl_view).

## 4. The statue loot: the armour itself

A samurai case is `...Montre_SamuraiSuit` with two models: `_Whole` (steel frame, glass, hull, and the
armour: mesh `Fabric_Samurai_01a_M09` with its dark lining `Textureless_01_2sided`, 993 vertices, 91 x 200 x
78) and `_Remain` (the bare wooden stand, shown when the glass is shot). All 15 cases share ONE `_Whole`
model (root 54765 in this build). These are what the owner calls statues - so do the developers
(`Markup!HeroCovers!Statues!PlayerCoverColiStatue#NN`, re/retomoto.md 3.2). The level's only other display
pieces are the 4 sword cases (`SI0103_M09_Montre_Swords_*`: 2 in the boardroom, 2 in the elevator lobby);
no loot stands at them, and a sword lifted out of one would be a different prop from what each of the 15
cases shows. The only swap the campaign has for an armour case is `_Whole` -> `_Remain`, and that one
removes the glass as well. The armour is the one artefact these 15 cases hold.

So the loot is the thing in the case (`STATUE = 'suit'`, `kl_fa_loot.suit_models`): a new model root (2
chunks, dead indices) lists the two armour meshes - the mesh chunks themselves are shared, nothing is
copied - with the flags and prop chunk of the case's own `_Remain` root; the case model's object table
loses them (it keeps 4 objects). Each of the 15 loot objects gets that root and the case's own world frame
(place and turn), so the armour stands exactly where it stood. Read back: the armour is drawn once,
0 from its case. Value, radius 150, controllers: untouched. Why this and not a bag or a case of money:
it is what a thief takes from a display case; it is consistent across all 15; it needs no new art; and the
case visibly empties when it is looted, which tells the next player the case is done.

What follows from it, for the owner's eyes: before, shooting the glass swapped `_Whole` for `_Remain` and
the armour vanished with the glass; now the armour stays on the stand until someone takes it. The loot
object is 200 tall where a bag was 40: where the game draws its '$' marker on such an object was not read.

Pictures: `research\loot\new_armour.png`, `new_armour_in_case.png` (with and without: the case when
looted), `new_case_empty_and_stand.png`.

## 5. In the build

Everything works on the WRITTEN level (chunk numbers exist only then):

- `kl_fa_loot.dress(folder)` (in place, or a copy with `dst`), `kl_fa_loot.check(folder)`,
  `kl_fa_loot.finish` = both. `kl_fa_loot.hook()` appends `finish` to `kl_fa_author.FINISH`;
  `kl_fa_author.test` and `kl_fa_blast.test` run that list after the archive is written. Both mains call
  `hook()` unless `--loot-bags` is given.
- **For the lead** (kl_graft.py / kl_maps.py are not my files): `kl_maps.py chain ... --author` does not
  run the list. One line after the last step of a chain is written gives it the same level:
  `for fn in kl_fa_author.FINISH: fn(<folder the level was written to>, log)`. Until then the dressed
  level comes from `kl_fa_blast.py test`, `kl_fa_loot.py test` or `kl_fa_loot.py dress <built> <out>`
  (the last also works on a level that already has its wardrobe).
- **Order matters:** `dress()` LIGHTENS FIRST (`kl_graft.lighten` trim + slim, when the level still has
  dead model roots). Taking dead chunk indices turns every dead chunk into a stub, and 'slim' finds the
  removed map's textures by walking its dead model roots: a level dressed first came out of `lighten`
  with '0 dead model roots ... 0 shrunk' and a 337 MB archive instead of 212 (seen, first build). A later
  `kl_graft.py lighten` of the dressed level finds nothing left and changes nothing; `kl_chars.py
  wardrobe` after it works as before (15,509 dead indices taken, 7,880 still free).
- `python tools/kl_fa_loot.py test <out>` = the whole thing: kl_snd.VOICE on, `kl_fa_blast.test` (author +
  street + blast, loot dressed), KLJoin.ini copied beside the archive, lighten -> `<out>\light`, wardrobe ->
  `<out>\retomoto_loot`, every check. About 12 minutes.

Options (kl_fa_loot.py and kl_fa_blast.py test): `--case dm | dd | bag`, `--case-scale X`,
`--statue suit | bag`, `--room-reach R`, `--loot-bags` (bags everywhere; kl_fa_author's old places).
With `--case bag` the table's six still move to the rims (`RIM_BAG` 50) and get radius 125: the reach
fix does not depend on the prop. Each was built from `play3s` with `dress` and read back with `check`:
`--case dd`, `--case-scale 1.6`, `--statue bag`, `--loot-bags`: 0 problems each (the first two only after
two faults this test found were fixed: Dog Days' case was scaled 1.25 too and stood 3.8 over the top; a
larger Dead Men case hung over the rim - the inset now grows with the size).

## 6. What only the owner's eyes can settle

1. The briefcases: drawn at all (a model no stock Dog Days level has, in this slot), black with silver
   clasps, lit like the table; size (1.25 x - too small to spot from the balcony? `--case-scale 1.6`, or
   `--case dd` for Subway's 70-wide one).
2. They appear when the room's nine are dead (unchanged gate), three along each long side of the table,
   and all six can be taken standing at the table - the left row above all.
3. The '$' marker on the cases and on the armour: where it sits, whether it reads.
4. The armour: in its case as before; taken -> gone, the case empty. With the glass shot first: the armour
   stands on the wooden stand until taken.
5. Is the armour the right 'good prop' - or should it stay in the case and something smaller be the loot
   (`--statue bag` brings the bags back; another prop is one entry in `kl_fa_loot`).
6. 'Outer ring' = the table's rim: if the six should rather stand on the floor along the room's walls or
   the window side, say where.

## 7. Every GUESS and ASSUMPTION

| what | value | kind |
|---|---|---|
| `CASE_SCALES['dm']` | 1.25 | GUESS (45 wide) |
| `CASE_YAW` | 8, -6, 11 degrees | GUESS (looks put down by hand) |
| `RIM` / `RIM_BAG` | 33 / 50 in from the rim | GUESS |
| `MARGIN` | 20 to spare for 'in reach' | GUESS |
| `BODY` | 30: how near a wall a player's feet get | ASSUMPTION (run J1) |
| `HERO_BITS` | 0x28 stops a player | ASSUMPTION (kl_fa_author's) |
| the pick-up test's branch | +0x3d set on a money trigger | ASSUMPTION (2) |
| 'left from spawn' = -z | from klauto's heading sign | ASSUMPTION (not from a picture of the owner's round) |
| 'outer ring' = the table's rim | | ASSUMPTION about the owner's words |
| a root without an octree record is drawn and harmless | as 597 stock F07 props | ASSUMPTION for a prop that is loot |
| a loot object hides its model when taken, whatever the model | as it did the bag | ASSUMPTION (handler not read) |
| `ROOM_REACH` | 125 | copied (stock containers), not a guess |
| statue value / radius, room value, the gate | kl_fa_author's | unchanged GUESSES of re/retomoto_fa.md |
