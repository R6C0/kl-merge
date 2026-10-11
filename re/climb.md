# The climb Dead Men had and Dog Days dropped (the bank's yard wall first)

2026-10-11, track F. OFFLINE: static reading of `kl2.exe` (build 0490) and `kaneandlynch.exe`, the 20 + 21 stock
level files, and the bank build `<work>\build\z_hop\M03` (read only). **Nothing here ran in either game. Nothing is
installed, nothing is wired into the hook, nothing is committed.**
Three readers did parts A, B and C; their scratch notes are not in the repo, so what the plan rests on is written
out here. What the PLAN rests on was read again by the writer of this file: every kl2.exe routine of section 3,
the head of the vault test, `0x619790`, the vault's start, the NPC link mover (1.2 - 1.4), Dead Men's table, enter
and callback (2.1; the constants of its ray test were confirmed in the reader's listing, the routine itself was
not read a second time), the clip records and the merge (done again by the tool of 4.1), the wall's geometry.
The cover list of 1.1 and the stock counts of 1.5 are the reader's, taken over. kl2.exe addresses can be re-read
with `python debug\dasm.py f:<address>`. Where a reader's note was wrong it is corrected (section 6).
Status words: **read** = seen in the disassembly at the address given; **measured** = counted on the files, the
command is named; **ASSUMED**; **not established**.

Built with it (section 4): `tools/kl_fa_climb.py`, `<work>\build\z_climb\M03`, `klhook/klclimb.c` (NOT WIRED).

## 0. Verdicts

1. **Can a wall be crossed by Dog Days' own vault with level data alone? By the rule yes, as a climb no.** A low
   cover box (`*CoverBoxM*`) whose `PlayerCoverModifier` has the top state `ON_VAULT_ON` on the side one stands at
   gets flag 0x800, and the vault test `0x7a8480` answers yes on that flag before it looks at any geometry; the
   move runs with the player's collision off. But the clip is a 0.92 s hop made for a 1 m obstacle whose root
   does not rise: at the bank's wall (**203.5 over the yard floor**, 50 thick, the street 253.5 under its top)
   the man crouches at a wall taller than himself and slides through it. Without the forced flag the game
   refuses anything that reaches 145 over the feet. No stock level forces a vault on a box higher than 107.
   A drop on the far side is no obstacle (nothing looks for a floor; stock F04 / F06 vault into 4 m drops).
   Whether a low cover is ENTERED at a 2 m wall at all is not established.
2. **Dead Men's climb needs no level data**: `ZFFPlayerMovementClimb` finds the edge with rays (25 < h <= 220
   over the feet; Low <= 120, Medium <= 170, High <= 220), is asked for by the USE tap while the player is slower
   than 375 a second, and is carried by the clip's own root motion, aligned twice. The bank's wall is `High`
   from the yard (203.5; the rule holds on the build's collision at 63 of 65 places tried, 4.2) and too high from
   the street (253.5), where Dead Men climbs dumpster, then wall.
3. **Dog Days still has the NPC half** (the navigation-link mover `0x4a5160` with the three slot names, called
   for links of kind 1) and **no player half**. No Dog Days `.ANM` has the slots or the clips. The clips can be
   put into a Dog Days file slot by slot (+141,248 bytes, 12 clips, 3 slot names, no bone name; every proof
   holds); `kl_anm.py merge` cannot do it (it merges whole collections).
4. **A hook can play Dead Men's clip on the player with three game routines the game uses itself**: the mini
   animation start `0x5ea340` (a full-body clip on a standing or walking player, with its own guard), the
   alignment `0x80fdc0` (the routine the NPC mover calls for these very clips) and the collision switch
   `0x5d6200` / `0x686600` (what the vault brackets itself with). The game's own vault can also be started at any
   place with one call, `0x619790` - with the vault's clip.
5. **The plan (section 5): (iii) first** - Dead Men's clip played by the hook at marked edges, at wall pieces that
   still STAND, **with (iv) kept in the same build**: the piece `kl_escape` sank stays sunk, so the way that works
   today and the AI heisters' drop link are untouched. (ii) is the fall-back mode of the same hook file. (i) is
   not worth building. **For the game as it is installed today the answer is (iv): the opened wall stays** -
   until live check K2 has shown a climb.
6. The AI heisters gain nothing from the hook part; their climb would be level data alone (clips, done here, +
   kind-1 links and two wall-top polygons in the mesh, not done). They cross by the drop link today.

## 1. A - Dog Days' vault (kl2.exe)

### 1.1 From a named box to the prompt (read)

| step | where | what |
|---|---|---|
| cover list | `CFFCoverList` slot 13 = 0x6d6a80 | every ZSTDOBJ-family entity (ZBoxPrimitive 0x2000e1 too: 313 stock covers are box primitives) whose NAME matches `*coverbox*`, at most 5,000 |
| a box | 0x603830 | record 0xa8 bytes: +0x08 car, +0x0c 12 modifier states, +0x4c type (0 low = `*coverboxm*` / `*coverboxl*` / `*coverboxcar*`, 1 high = `*coverboxh*`), +0x50.. HALF sizes, +0x90 four side pointers. Refused when the box is tilted (up axis y < 0.717) or has a `DynamicCover` controller |
| a side | 0x603450, 0x6e7740, 0x8e5690 | 0x58 bytes: +0x0c / +0x18 the two ends of the BOTTOM edge of the face, +0x24 / +0x28 / +0x3c flags of the left end, the right end, the top, +0x2c the outward normal, +0x54 depth = the box's full thickness. Side order 0 = +x, 1 = +z, 2 = -x, 3 = -z of the box's own axes (jump table 0x8e5858) |
| modifier | `ZPlayerCoverModifier`, controller `PlayerCoverModifier`, 96 enums `AUTO ON OFF ON_VAULT_ON ON_VAULT_OFF AUTO_VAULT_OFF` (0..5) | on a box it governs that box (slot 0); on a group its children named `*CoverBox*` take eight slots in order (0x7fe590, 0x4be840). Field i of a slot = side i // 3, part i % 3 (left end, right end, top) |
| side flags | 0x440de0 | top state on a LOW box: `ON_VAULT_ON` -> 0x40 and **0x800**; `ON_VAULT_OFF`, `AUTO_VAULT_OFF` -> 0x1000; `OFF` -> 0x80. AUTO: a ray from the side's middle at bottom + 110 (5 in front, 90 into the box) or a half height over 120 marks the top 'not open' |
| in cover | 0x849700 -> 0x797480 | a box is a candidate only when its BOTTOM is within 50 of the player's feet (0x797634); then the side test 0x653270 and a scoring that was not decoded (0x792e30, 0x77a100) |
| prompt | 0x58f8e0 -> bit 0x10 of [player+0x2d60] | in cover, movement kind 3, the box not high, and 0x7a8480 says yes |
| input | 0x44f260 at 0x44fc10 | bit 0x10, the stick INTO the cover, the cover key -> `0x6fd880(side, left)` |

### 1.2 The vault test, 0x7a8480 (read; the first lines re-read here)

```
if [player+0x2954] or not in cover (0x40f840)                 -> no
side = 0x7a26d0(player)                                       the cover side he is on
if side.top & 0x1000                                          -> no
if side.top & 0x800                                           -> YES (0x7a84c5: nothing else is looked at)
if the box is high or a car; BaseMove's byte +0x1e70; the ability bit 0x10 of [gamedata+0x4d48] clear  -> no
d = distance from the face                                    -> no when d > 100
land = 50 beyond the back face, at the player's own height; far = 110 beyond
two Havok triangle overlap queries (0x475dc0, radius 5, the player's layer 5):
   (player - 50 along the face, land, player + 50 along the face), all at feet + 150
   (far - 40, land at + 150, far + 40 at + 30)
a hit on anything the player collides with -> no
```
So without the forced flag: nothing may lie 145 .. 155 over the feet between him and the landing (no wall of 145
or more), nothing more than 30 higher than the take-off within 110 beyond. No depth limit. **No floor is looked
for: a drop is not tested.** With the forced flag none of it is evaluated.

### 1.3 How the player is moved (read; `0x619790` and the action's start re-read here)

- `0x619790 = bool __thiscall ZFFPlayer::StartVaultOver(cover *, char left, float pos[3], float rot[9], char given,
  char writeBack)`, `ret 0x18`. It tests nothing. From the cover record it reads +0x0c (3 floats), +0x2c (3
  floats), +0x54 (float) and stores the pointer at action +0x7c (read by nothing in the action's methods).
  End = player place - normal * (distance from the plane + depth + 50) (0xb71b60 = 50.0), **at the player's own
  height**; with `given` the caller's `pos` / `rot` are the end instead - that is the network receiver 0x60c610
  (the RMC `VaultOverCover(bLeft, x, y, z, angle)`). It takes action kind 0x2b from the player's factory (vtable
  +0x384 = 0x839740), stops the current action (+0x374) and starts the new one (+0x370). In Arcade it also
  writes one telemetry event (`FAVaultOverCover`, 0x447660), no Steam stat.
- `ZFFActionVaultOver` (vtable 0xbb5188, made only by `ZFFPlayer`'s factory). Start 0x6a27e0: leave cover
  (0x5fcb80), a Havok phantom that knocks things over, the clip slot by NAME - `/Cover/Vaulting/Cover_Vault_
  {Left|Right}_{1M|2M}`, **2M when the way start -> end is over 175.0** ([0xb5820c], 0x6a29d4), else 1M: the
  names are a length, not a height -, `player->vtable[0x560]()` = collision off, `Play(clip, 1)` (vtable +0x204;
  a null clip is a null read at 0x6a2a65), `AlignTo(end rot, end pos, frames - 1)` (vtable +0x208). End
  0x82f780: collision on (vtable +0x564). Its 'a channel ended' slot (0x553070) is `mov al, 1`: ANY ended or
  replaced channel report finishes it.
- Collision off, twice over: `[player+0x7a5] = 0` makes the stepwise collision of a move (ZMovementBase slot 34,
  0x7aa2b0) answer at once, and the body goes to Havok layer 0xc, which collides with no layer but 0 in the
  28 x 28 table built at 0x5afcf0 (level collision is layer 6).
- The clips (measured, `scratch recs.py` on the build): `Cover_Vault_*_1M` 23 frames, root (29, **0**, -189 /
  -204); `_2M` 29 frames, (30, 0, -281). The root does not rise: the body's hop is in the pose.

### 1.4 NPCs (read)

They never vault: action 0x2b exists only in `ZFFPlayer`'s factory (`ZFFActor`: kinds 3..15, 0x11, 0x12). An NPC
crosses a height difference only on a navigation link: `ZFFSpecialLink@Locomotion`, vtable 0xb78dd4, slot 1 =
**0x4a5160** (re-read here): it starts within 40 of the link's start (20 for kind 2); `dy = end y - start y`;
**kind 1: dy > 170 -> table +0xc `High`, > 120 -> +8 `Medium`, else +4 `Low`**; kind 2: |dy| > 160 -> `Fall_2m`,
else `Fall_1m`; kind 3 `Leap/Forward`. With a clip: matrix from MINUS the direction of travel (0x70fa70,
0x55f8f0), the frame of clip event 6 (0x4a75d0), Play (vtable +0x200), **AlignTo the link's END at event 6**
(vtable +0x208). No clip for the slot -> nothing is played. The table 0x15489e8 is filled at 0x579920, the only
reader of the three `/Movement/Climb/Up/*` strings. Stock Dog Days: 192 links, all kind 2.

### 1.5 Stock, measured (21 levels; the readers' `covers.py`, `farside.py`)

- 12,971 objects named `*coverbox*`: 5,388 low, 7,229 high, 299 car; 3,431 `PlayerCoverModifier`.
- Top state of the 21,552 sides of low boxes: AUTO 18,187, OFF 1,801, ON_VAULT_OFF 1,090, AUTO_VAULT_OFF 220,
  **ON_VAULT_ON 133** (80 boxes in 14 levels), ON 121.
- The 133 forced vaults: box height 86 .. 107, depth 8 .. 201 (median 100; one 785), the real obstacle under
  them 101 (median), 109 (third quartile). Floor beyond: median 0; 14 land more than 30 lower - F04
  `F04_Outside_EscapeStreet\CoverBoxM_05 / 09 / 13 / 14 / 24 / 30` (404 -> 0), F06
  `Money_Transporter_WarehouseCorridor\CoverBoxM_01..03` (-800 -> -1200, states `AUTO AUTO ON_VAULT_ON / OFF x 9`:
  one way), F02 `Bridge_Highway_01\CoverBoxM_Box14` (1810 down).

## 2. B - Dead Men's climb (kaneandlynch.exe) and its clips

### 2.1 `ZFFPlayerMovementClimb`

Vtable 0x966c44, size 0xec, movement id 0xb, made only for `ZFFPlayer` (0x5ef1c0). Read whole by the reader;
the table, the enter and the callback were read again here.

- Table (slot 20, 0x603340), three records at this+0x68:

  | slot (walking) | sprinting | height | distance |
  |---|---|---|---|
  | `/Movement/Climb/Up/Low` | `/Movement/Climb/Up/Sprint_Low` | 120 | 81 |
  | `/Movement/Climb/Up/Medium` | same | 170 | 47 |
  | `/Movement/Climb/Up/High` | same | 220 | 47 |

  81 / 47 are the stand-off from the face at which the clip wants the feet when it starts, not a height.
- The test (slot 14, 0x605b50). **No level data is asked for**: no flag, no name, no controller, no link.
  0.5 s since a stamp; speed under 0.75 x 500; no hand action; the USE tap one frame earlier (`TapUse`).
  Geometry, feet = 90 under the reference, `hd` = 25: four rays straight DOWN 310 from 310 over the feet, at
  25 / 40 / 55 / 70 in front; per top (near to far, a lower one than the last is skipped): **a clear way** 15
  over the top (from 15 behind him to 30 past the probe: must miss), **180 headroom** over the top (a hit
  refuses everything), **a face** 1 under the edge (must hit), **h > 25**, the first table record with height
  >= h (none: no). Refused on a `ZHavokCar` unless two car bytes allow.
- Carried (enter 0x602f30, callback 0x603160): play to the frame of clip event 5 and **align** (0x526620) the
  root to `P1` = the face's foot, distance D back from the wall, at feet level; then play on and align to
  `P2 = P1 + (0, h, 0)` at the frame of event 6; after that the clip's own root motion goes on. The clip's
  frames are 25 a second. He keeps his heading (the matrix is built from his own back vector).
- Far side: no second clip. He ends ON the obstacle (table below) and `ZFFPlayerMovementFall` takes what comes.
- A network path in the same routine replays the climb for remote players (replicated movement id 0xb).
- NPCs: `ZFFSpecialLink@Locomotion` (0x5e5690) on links of kind 1 - the routine kl2's 0x4a5160 is, instruction
  for instruction. Measured: 195 kind-1 links in 11 campaign levels, **none in a Fragile Alliance level**.

### 2.2 The campaign bank has the climb at our wall (measured by the reader on the navigation meshes)

`M03_A` (the campaign chapter 'Withdrawal'; the same building at the same coordinates as `M03_FA_A`,
re/campaign_fa_bank.md) has two lanes, x = -3210 and x = -2938, at wall piece `SO0101_M03_Wall_Low_8m_02` and
the dumpsters `SO0701_M03_Dumpster_A_03 / _02`:

| step | from -> to | kind up / down | dy | across | cost |
|---|---|---|---|---|---|
| yard <-> wall top | (x, 220, -660) -> (x, 404.5, -625) | 1 / 2 | 184.5 = High | 35.5 | 184 |
| wall top <-> lid | (x, 404.5, -575) -> (x, 284, -540) | 2 / 1 | 120.5 | 35.5 | 114 |
| lid <-> street | (x, 274, -480) -> (x, 150, -409) | 2 / 1 | 123.6 | 70.9 | 117 |

Wall-top polygons 132 / 133 are one-polygon areas (z -625 .. -575, y 404.5, area boxes y 304 .. 504), two
waypoints each, every waypoint on a border edge. `M03_FA_A` (and our build's mesh, 697 polygons) has no
wall-top polygon; the lid polygon is still there (544, area 41, no waypoint), the street polygon is 688, the
yard polygon 527. In the campaign the PLAYER comes the other way at the very start of the chapter: from the
back street (checkpoint 1 at (-2976, 154, -202)) over a dumpster and the wall into the car park
(re/campaign_fa_bank.md, beat 2).

### 2.3 The clips (measured: all 41 stock `.ANM`; `tools/kl_fa_climb.py check` prints the table for a build)

- All 20 Dead Men files hold the same 9 slot names (`/Movement/Climb/Up/Low | Medium | High | Sprint_Low`,
  `Down/Low | Medium | High`, `Ladder/Up | Down`) and the same 17 clips `anim:Movement/Soldier/Climb#...`.
  Nothing in either exe asks for the `Down` / `Ladder` names. **0 of 21 Dog Days files** has any of the slots or
  a clip with `Climb` in its name.
- Dead Men's sets: the player sets (`PlayerCharacter`) play the player-timed clips, every NPC character set
  (Police, Army, Civilian, Female ...) the `_NPC` ones. Lists are `condition:clip` pairs, the default last
  (condition 8 / 0x10: pistol / unarmed, ASSUMED from the clip names).
- The record's vector +0x18 is the clip's net ROOT translation (new; equal to last root key - first on every
  climb clip). The root track: clip data +0x24 = track 0 = {4 offsets, bone}, the root is bone 0x39 (GROUND) by
  number in both exes; position keys = an `IdxT` frame table + raw float triples (kaneandlynch 0x5bfa60 /
  0x5bdbd0; `kl_fa_climb.root_keys`). Vectors +0x30 / +0x3C are NOT root motion (a unit vector and a place,
  zero in the unarmed clips).
- The player's default clips (25 frames a second; y up, forward = -z; root relative to its first key):

  | class | clip | frames | events | root at event 6 | root at the end | after event 6 | ends (with Dead Men's alignment) |
  |---|---|---|---|---|---|---|---|
  | Low | `Climb#Sprint_Low` | 27 (1.08 s) | 5 at 6, 6 at 16 | (-7, 102.7, -60.8) | (-17, 106, -145) | 84.2 forward, 3.3 up | 3.2 past the face, 3.3 over the top |
  | Medium | `Climb#Up_Medium` | 37 (1.48 s) | 5 at 6, 6 at 16 | (0, 118.5, -0.5) | (-15.8, 118.5, -62.4) | 61.9 forward, 0 up | 14.9 past the face, on the top |
  | High | `Climb#Up_High` | 52 (2.08 s) | 5 at 6, 6 at 20 | (-0.1, 147.5, -9.8) | (-0.9, 172, -101.2) | 91.4 forward, 24.5 up | 44.4 past the face, **24.5 over the top** |

  NPC clips: `Up_High_NPC` 52 frames, event 6 at 25 with the root at (-0.5, 166, -39.9): the campaign's 35.5
  across fits it; `Up_Medium_NPC` 31, event 6 at 24; `Sprint_Low_NPC` 27, event 6 at 13.
  The 24.5 the High clip still rises after event 6 (the code puts the feet at top level AT event 6) is not
  established: a settle of that size at the end is what the numbers say. Stock Dog Days has the same shape in a
  path it does run: `Fall#Fall_1m_NPC` has its root at -93.2 at event 6 and ends at -100.
- All climb clips have record flags 0xc0 / 0x10c0 (0x40 = root motion, what kl2 0x760120 asks for) and +0x28 = 0
  (a full-body clip), like the vault clips.

## 3. C - how a clip is played on the player and how he is carried (kl2.exe)

Read again here, except the three rows marked (C): those are the reader's reading, taken over.

| what | address | notes |
|---|---|---|
| `ZFFPlayer` vtable | 0xbb45f4 | +0x200 Play 0x4da1d0, +0x204 Play whole clip 0x6f6830, **+0x208 AlignTo 0x80fdc0**, +0x214 'moved by animation' 0x41a6b0, +0x370 StartAction 0x542c00, +0x374 StopAction 0x8aef30, +0x384 CreateAction 0x839740, +0x388 current kind 0x76ea90, **+0x560 collision off 0x5d6200, +0x564 collision on 0x686600**, +0x5d8 movement kind 0x4cd950 = `[[player+0x6b4]+0x44]` |
| dispatcher | `[player+0x19c]`, vtable 0xba38d8 | +4 = the current action (one at a time). StartAction 0x869e10 has an int3 when one is current; ZFFPlayer's StartAction dereferences the action it is handed |
| movement kinds (C) | constants in 0x51d240 .. | 2 Stand, 3 BaseMove, 5 Guide, 8 StandCover, 10 Roll, 11 Fall, 13 / 14 passengers, 15 MountedWeapon, 16 Rappel, 17 CloseCombat, 18 Prone, 19 Die. No climb |
| alive / down | 0x6a88f0 | bit 0x40000 of `[player+0x438]`, or `[[player+0x2940]+0x24]` in 2..13 except 10 |
| slot name -> id | 0x426890 -> 0x68a730 | a binary search over `[player+0x80]` -> {n, n x {text offset, id} sorted by name, texts}; 0xffff = none. Pure |
| slot id -> clip | 0x59d550 -> 0x5c2f60 | draws one number from the game's generator (`[0xdd2640]+0xb30`); 0 = the set has no clip |
| clip event frame | 0x4a75d0 | table = `[[0x1546f6c]+0x10] + [clip+0x10]`, `[clip+6]` entries {u32 id, u16 frame} |
| **AlignTo** | 0x80fdc0 `(rot[9], pos[3], float frames) -> al`, ret 0xc | takes the running full-body channel whose clip has record flag 0x40 (0x760120; none -> returns 0), sets the target time = the channel's frame + `frames` (clamped to its end), stores the difference between where the clip alone would be then and the wanted transform, sets channel flag 0x200. The frame update (0x50b0f6) blends the correction in linearly, rotation and all three axes; **when the target time has passed the correction stays whole (0x50b11a .. 0x50b131) and the clip's own root motion goes on** |
| a rotation | 0x857110 `(node; rot out, pos out)` | **row 0 = the world image of local z, row 1 of y, row 2 of x**. A clip's root runs along -z, so row 0 is where the BACK points. 0x55f8f0 (ecx = out[9], edx = in[3]; pure, 128 callers) makes such a matrix from the vector that becomes row 0: the vault passes the cover's normal, the NPC mover minus the direction of travel |
| collision off / on | 0x5d6200 / 0x686600 | 0x8c5270: `++[player+0x7b4]`, `[player+0x7a5] = 0`; 0x8b41c0: the count back, `[player+0x7a5] = 1` at zero; both set the body's Havok layer (0xc / 5) through 0x40ed30 on `[[world+0x11840+4*[player+0x27cc]]]` |
| **StartMiniAnim** | 0x5ea340 `(u16 slot, x, alignObject, char endWithClip)`, ret 0x10 | writes through `[player+0xbe0]` and `[player+0xdbc]` (0x8b7410, 0x4c1a70), stops the current action, makes `ZFFActionMiniAnim` (kind 0x23, vtable 0xbb4f0c, 0x28 bytes from the pool 0x15151c0: +8 player, +0x18 slot, +0x1c alignObject, +0x20 the channel, +0x25 endWithClip) and starts it. A null action is handed on when the pool is empty (the game's own flaw) |
| its start | 0x76d1d0 | slot < 0 or no clip: `[player+0x2758] = 1`, the action is over at once, no fault. Else 0x74c040 (the weapon is lowered), `Play(clip, 1)` **with byte +0x24 cleared around it: its 'a channel ended' slot 0x42b7f0 ignores the reports that Play itself causes**; with an alignObject: AlignTo(its world transform, the frame of event 6 or the last) |
| who calls it | 0x5022c0 from 0x60b5c2 | ordinary play: a full-body clip (`[player+0x25b0]`) on a player with no action running. So this start HAS run from standing and walking players in every mode |
| the mini cutscene (C) | `MiniCutsceneRout` (vtable 0xbcdf14), script text in field 0 | a script entry with a `Lynch` head and an `act` task (`anim` = a slot name, `startpos` = a pos object) makes `ZMiniPlayerActTask` for the player in gamedata slot 0: put on the pos object (0x82cc40), collision off, the slot played with its own root motion, the last frame held, input back at the script's end (0x8e8d00, 0x447bd0). 2,339 uses in the 21 stock levels, 755 scripts with a Lynch head, 38 Lynch acts with a start place - **all in campaign levels, none in an FA level**. 0x872f70 / 0x5f6df0 have an int3 when the player's slot byte `[player+0x91d]` is not 0 or 1. Stock template: L02 `ROOT\AI!Friendly!Script_Door` (a `PlayerAction` box whose list starts `MC_Door_Lynch`) |
| placing a player (C) | 0x82cc40 `(rot, pos, char resetMove, char force, char sendNet)`, ret 0x14 | the round start uses (1, 0, 1). 0x62a900 (klcrew_rt.c) is the ACTOR's routine. kljoin.c's debug jump is the only placement seen live |
| `ZFFActionJumpOver` | kind 0x2c, vtable 0xbb51bc, constructor 0x594fa0, start 0x8f0440 | new here: the constructor resolves ONE slot, `/Cover/Vaulting/Sprint_Vault_Right_0.5M`; the start is Play + AlignTo(frames) + collision off, after a test 0x523e40. No site was found that asks the factory for kind 0x2c: a cut action. Not used |

What follows for a hook:
- The vault's own start is one call and brackets the collision itself, but its clip is the vault's and whether
  the action survives its start from a player who is NOT in cover is not established: its 'channel ended' slot
  finishes it on any replaced channel, and `Play(clip, 1)` reports every full-body channel it replaces. If it
  does not survive, the action is freed inside its own start.
- The mini animation start has that guard and is called by the game from walking players; it does not touch
  the collision and aligns only to a scene object. A hook adds the two things by the game's own routines:
  collision off before, AlignTo with places of its own, collision on when the action is gone.
- None of it reaches an AI heister (`ZFFActor` has neither action).

## 4. What was built (offline; nothing loaded, nothing installed)

### 4.1 `tools/kl_fa_climb.py` - the level's half, a step on a finished build

    python tools\kl_fa_climb.py rule
    python tools\kl_fa_climb.py edges <folder>
    python tools\kl_fa_climb.py check <folder>
    python tools\kl_fa_climb.py apply <folder> <out folder> [--players-only] [--no-edges]

`apply` adds two things and takes nothing away (the wall piece `kl_escape` sank stays sunk):
1. **`.ANM`**: the three slot lists with their clips, in the sets of the level's `ZFFPlayer` bodies (Kane, Lynch)
   from Dead Men's `PlayerCharacter`, and in every NPC character set (a set whose `Fall_1m` default is an
   `_NPC` clip: Thug, Swat_02, Lynch_NPC, Kane_NPC, Civilian, Police, Army, Female) from Dead Men's `Police`.
   The machinery is `kl_anmjoin`'s (`_Out`, `_Source`, `_add_lists`: the code of every graft's join). Proved
   on the result before anything is written: reads back to the same bytes; `kl_anm.audit` clean; the base is a
   prefix (clips, names, data, bone / pose / slot tables) and no base list changed; each of the 30 added lists
   plays its Dead Men source (name, events + data, bone NAMES, condition flags); no bone or pose name added;
   only the `.ANM` member of the archive differs. `tools/kl_anm.py` was not changed (`kl_anm.py check`:
   `byte-identical: 41 of 41`).
2. **`KLJoin.ini`**: `[Climb]` sections beside kl_fa_bots' `[CrewHop]` (which stays byte for byte). A section is
   the top edge of an obstacle (`A`, `B`, `Normal`, `Floor`, `Depth`) where **Dead Men's own rule** (2.1) holds
   on the build's collision: the tool walks `LINES` (per map, a seed) every 25 units, tries the rule from 30 /
   47 / 65 off the face with `kl_map_escape.Ground`'s triangles, wants level floor and room to stand at the
   foot and no movable body there, and writes the stretches that pass (50 off both ends, 150 or more left).
   Every number written is measured. `check` walks every section of a folder's file again.
It also continues `steps.json` ('climb') and, because `kl_fa_bots_dyn.check` FAILs a build whose large blocks
differ from the ones its step recorded, the `big_before` of the copied `dyn.json` (the numbers before are
kept as `big_before_climb`; said in `climb.txt`).

### 4.2 `<work>\build\z_climb\M03` = `z_hop\M03` + the two additions

`F01_Main.zip` sha1 2c93ab683542c0c6629699265976975eb9ddd1b1 (200,889,112 bytes); `.ANM` 22,202,616 ->
22,343,864 (+141,248: 12 clips, slot ids 2505 Medium, 2506 Low, 2507 High, bones 156 (+0), poses 36 (+0)).

    line 'the yard's north wall, from the yard': (-3500, -625) -> (-1900, -625), 65 samples every 25, 63 pass
      refused at (-2575, -625), (-2550, -625): the floor at the foot is not level   (a street light's base)
    [Climb]    A=-3450 403.5 -625  B=-2650 403.5 -625  Normal=0 -1  Floor=200  Depth=49.5
    [Climb.2]  A=-2475 403.5 -625  B=-1950 403.5 -625  Normal=0 -1  Floor=200  Depth=49.5

Both are `High` (203.5 over the floor), stand-off 47; the player ends 44.4 past the face, on the wall, 5.1
short of its far edge. Beyond the wall the floor is the street (253.5 down) and, at x -3284 .. -2876, the
dumpster lids (122.5 down), two boxes (156.5, 189.5). The stretch is pieces `SO0101_M03_Wall_Low_8m_02` and
`_01`, between the sunk piece and where the level itself says 'not here'. Controls with the same rule
(measured, scratch `piece3.py` / `over3.py`):

| stretch | samples that pass | refused because |
|---|---|---|
| pieces `_02` / `_01` from the yard, x -3500 .. -1900 | 63 of 65 | a street light's base (2) |
| piece `_03` from the yard, x -4250 .. -3550 | 2 of 29 (x -3575, -3550) | the way 15 over the top is not clear: a hero-only collision object `ColiObj_OnlyHero_01` over the wall from x -3600 west, the wall `SO0202_M03_Wall_ENTER_05_01` further on |
| the sunk piece from the yard, x -1850 .. -1150 | 0 of 29 | no top within 70 in front (no wall) |
| pieces `_02` / `_01` from the STREET | 0 of 61 | the top is 253.5 over the feet: over 220 (35); a dumpster or a box stands at the foot (26) |

So the offline rule gives Dead Men's own picture: the wall is climbed from the yard between x -3590 and the
east end, not from the street, and the level's hero-only wall closes it in the west.

| check on `z_climb\M03` | last line |
|---|---|
| `kl_fa_climb.py check` | `RESULT (kl_fa_climb): PASS (0 FAIL, 1 NOTE)` (the note: the side file's sections, 1 `[CrewHop]`, 2 `[Climb]`) |
| `kl_fa_bots_dyn.py check` | `RESULT (kl_fa_bots_dyn): FAIL (7 FAIL, 3 NOTE)` - **the same 7 FAIL and 3 NOTE as the source `z_hop\M03` gets today** (the two outputs differ in one line, the `.ANM` size): 'money object(s) inside the loot window ... that a bot cannot take there', a rule the loot track added to `kl_fa_bots.check` this night. Nothing of this step. The drop link and `[CrewHop]` are as they were |
| `kl_impact.py` | `problems: 0 in 1 levels` |
| `kl_maps.py audit` | `RESULT: PASS (0 findings that must be 0, 0 known and accepted)` |
| `kl_map_escape.py van-check` | `0 fault(s)` |
| `kl_anm.py check` (the tool, untouched) | `byte-identical: 41 of 41` |

With the hook that is installed today the build is `z_hop\M03` with 141 KB more animation data: the installed
hook reads no `[Climb]` section and nothing in the game asks for the three slots. That is live check K0.

### 4.3 `klhook/klclimb.c` - the hook's half, NOT WIRED

Its top comment is the spec. In short: Arcade only, a level that is not stock, the game's thread; off unless
`[Climb] Enable=1`; `Dry=1` logs and calls nothing. Twenty times a second the local human's node place is
held against the `[Climb]` edges; AT THE FOOT (15 .. 75 from the face, between A and B, his height within 40
of `Floor`) for `Dwell` ms (400), slower than `Speed` (150), looking at the face within `Angle` (60), with
`Key` down if one is set, no action running, standing or walking, collision not already off:
- `Mode=climb`: class by Dead Men's table from top - Floor; the slot name looked up in the level's own table
  (read); `StartMiniAnim(slot, 0, 0, 1)`; if the game kept the action: collision off, then Dead Men's two
  alignments by `AlignTo` - P1 (the face's foot, stand-off back, his own height) at the frame of event 5, then
  P2 = P1 raised by (top - his feet) at the frame of event 6 (`Align=1`: one alignment at the last frame to the
  same end place at top height). If the game finds no channel to align, the action is stopped and the
  collision switched on at once. Every frame the action is watched; when it is gone, collision on - only for
  an object that is still one of the game's 28 players. A climb that outlives its clip by 1.5 s is stopped.
- `Mode=vault` (or `Fallback=1`): one call of `0x619790` with a cover record of the file's own and the end
  place given (the middle of the top); both vault slots tested for a clip first; afterwards the action must be
  the vault's, else the line says the start did not survive.
Dead Men asks for the USE tap. The hook's default is no key - standing at the foot, facing the wall, is the
request (a scripted test run cannot press a key that `GetAsyncKeyState` sees; `Key=0x45` gives a key).
Calls: `0x5ea340`, `0x80fdc0`, `0x5d6200`, `0x686600`, `0x55f8f0` (and `0x8aef30` on a time-out); vault mode
`0x619790`, `0x59d550`. Each is known by its first 14 bytes and its vtable entry before the first call; what
`0x5ea340` and the collision switch dereference without a test is tested before (`klq_refuse`). No data write
of the hook's own, no code byte.
It passed a SYNTAX check behind `klhook.c` (`cl /Zs /W4` on a scratch file that includes both: no object file,
no DLL; no warning from this file). **No hook was built.** The three lines for `klhook.c`:

    #include "klclimb.c"        after  #include "klhop.c"
    klq_tick(game_thread);      in klh_tick, after  klv_tick(game_thread);
    klq_init();                 in the init list, after  klv_init();

## 5. The ranked plan

| | what | the player sees | the AI heisters | risks | first to be seen live |
|---|---|---|---|---|---|
| **(iii)** recommended | Dead Men's clips in the level's `.ANM` (4.1) + `klclimb.c` `Mode=climb` at the edges of 4.2. The sunk piece stays | at the wall pieces that stand: he pulls himself up in 2.08 s with Dead Men's own animation and stands on the wall; a step on and he drops to the street or a dumpster lid. Any place along 13 m of wall. From the street nothing (253 high), as in Dead Men | nothing new: the drop link through the sunk piece, as today | three game routines in a combination the game does not make itself; the hook owns the collision count for 2 s (guards: section 4.3); no input is taken away (K4); the facing test's sign and the node's height are read, not seen (K1 shows both); a parked car at the wall is passed through; Arcade only | K0, K1, K2 |
| (ii) fall-back | the same file, `Mode=vault` / `Fallback=1`: the game's own vault action to a given end place | a 1.16 s vault pose that carries him 2 m up onto the wall: a hop through the air, not a climb | nothing | one call, the collision is the game's - but whether the action survives its start outside cover is not established (section 3); if not, a use after free inside game code | K6, only if K2 fails |
| (i) level data only | (a) a `CoverBoxM` + `PlayerCoverModifier` `ON_VAULT_ON` at a standing piece; (b) a `MiniCutsceneRout` with a `Lynch` act on the merged clip, started by a `PlayerAction` | (a) he crouches at a 2 m wall and slides through it; (b) the real clip, from ONE fixed spot per place, no alignment | (a), (b) nothing. Their own climb is level data (below) | (a) the cover search may not take a low box at a high wall; (b) a Lynch head has never run in an FA level, acts on gamedata slot 0, int3 when the slot byte is off; both need entities added to a finished build (slot ids move) | not built |
| (iv) today | the piece `SO0101_M03_Wall_Low_8m_05` sunk, its collision cut | a gap in the wall, a 50 cm step down | the drop link (seen live) | none new | - |

**Recommendation.** Wire `klclimb.c`, build the hook, run K0 - K3 on `z_climb\M03`. (iv) stays in the build
whatever happens: the climb is offered beside the gap, not instead of it. Only when the owner has climbed and
likes it is the question 'close the gap again?' worth asking - and then the AI needs its own way first (below),
because the drop link runs through the gap.

**For the installed game the honest answer is (iv) for now**: nothing of (i) - (iii) has run.

### 5.1 The AI heisters' climb (level data alone; clips done, mesh NOT done)

`kl2.exe` plays it by itself once the data is there (1.4): the three slots in the NPC sets (in `z_climb\M03`
already) and, per lane, the campaign's chain (2.2) in the navigation mesh - a wall-top polygon as a one-polygon
area with two waypoints, link kind 1 yard -> wall top (cost 184), kind 2 wall top -> lid (114), kind 2 lid ->
street (117); polygon byte +1 raised (re/bots_bank.md 1). Not done because it needs new polygons and areas in
the mesh (kl_fa_bots.add_drop only adds waypoints and links to polygons that exist; `kl_pf4.DD_LINK_KINDS` is
`(2,)`), in files of other tracks. ASSUMED: Dog Days runs a kind-1 link (identical code, no stock level has
one). Not read: what an actor does at a kind-1 link when its set has no clip - which is why all eight NPC sets
got the slots.

### 5.2 If the sunk piece is ever to stand again

- On a finished build the cut cannot be undone from the build: `kl_escape.cut_collision` replaced the piece's
  static placement by a filler. The change for the lead is one line of `tools/kl_escape.py`: the entry of
  `OPEN` becomes `'M03_FA_A': []` (`open_wall` then moves nothing, `place_entities` gets no REF, `cut_collision`
  returns at once; `money_reach` and `board_box` run as before) - and the map is built again from the graft.
- Not before the AI has 5.1: its drop link (waypoints (-1704, 220, -766) -> (-1700, 150, -534)) crosses the
  piece, and the link mover makes no collision query (read; that an actor on a link is not held by level
  collision is ASSUMED) - the bots would be carried through a standing wall.
- Level data for (i)(a), should it be wanted all the same: one `ZBoxPrimitive` named `CoverBoxM_Climb_01` (a copy
  of the room's `NoCoverBox#01` without its controller), unrotated, bottom ON the yard floor, the wall's own
  thickness, e.g. centre (-2300, 250, -600), half sizes (200, 50, 25); controller `PlayerCoverModifier` with
  fields 0..10 `OFF`, 11 `ON_VAULT_ON` (side 3 = -z = the yard, its top), 12..95 `AUTO` - the row of stock L11
  `L11_Inside_Luggage_Handling_C\_coverBoxes!CoverBoxM#30`. Not built.

## 6. Corrections to the readers' notes

- Part B: 'every bone the Up clips move is among table entries 0 .. 60'. Measured again: one of the 57 is entry
  64, `head attacher`. All 41 stock tables agree on entries 0 .. 60; the 20 Dead Men tables agree among
  themselves on 0 .. 66 and so do the 21 Dog Days tables, and entry 64 is `head attacher` in all 41. The
  conclusion stands for a better reason: a merged clip names its bones by the BUILD's own table (kl_anmjoin
  renumbers by name) and every body of a build is bound to that table; `check` proves that every bone a climb
  clip moves is moved by other clips of the file too.
- Part B took the wall as 184 high (the navigation mesh's 220); the collision floor is 200, so the climb is
  203.5 - still `High`, with 16.5 to spare. Confirmed with Dead Men's rule on the collision (4.2).
- Part A: 'the cut cannot be undone on a finished build' - true from the build alone, and not needed: the plan
  climbs the pieces that still stand.
- Part C ranked the forced vault first for a hook. Its open question (does the action survive its own start
  outside cover) does not arise for the mini animation start, which has the guard and is called by the game
  from walking players. So the mini animation is the main form here and the vault the fall-back.
- Part C described a `klclimb.c` with boxes and `To=` places; the file written here marks EDGES and applies
  Dead Men's table, so one section serves a whole stretch of wall and every class.

## 7. Live checks, in order (none run)

`z_climb\M03` in the test slot; a TEST hook built from the tree with the three lines of 4.3; `[Bots] Enable=1
Log=1`, `[CrewHop]` as in re/bots_bank.md. Each check changes one thing.
For a scripted run (a suggestion; the yard way points are re/escape.md 6's): after `goto -1250 -1250 110 12000
sprint keep` a `goto -3000 -900 110 20000 sprint keep`, then `goto -3000 -400 110 15000 keep` - a point on the
street, so he runs into the wall at x -3000, stands at its foot looking at it, climbs, walks on over the top and
drops onto the dumpster lid there, then to the street (K2 and K3 in one go). The same at x -2300 has no lid
under it (253 down).

- **K0** (no new code; the hook as installed): the build loads, GO, the round plays as `z_hop\M03` did, the
  bots leave by the drop link (`hop: bot N left From of hop 1 by itself`, `bots: ... van 1`). Proves: the merged
  `.ANM` does no harm.
- **K1** `[Climb] Enable=1 Dry=1 Log=2`: walk to the wall at x -3000, face it. Lines: `climb: 2 edge(s) from
  ...KLJoin.ini for level f01\f01_main`, `climb: edge 1: (-3450, 404, -625) - (-2650, 404, -625), 800 long ...
  203.5 up = /Movement/Climb/Up/High, stand-off 47`, every second `climb: node (...), +0x460 (...): N from the
  face of edge 1 ... +0 / +0 to its floor, speed S, facing F`, then `climb: at the foot of edge 1: ... facing
  0.9x; slot /Movement/Climb/Up/High = id 2507` and `climb: edge 1: WOULD climb ... P1 (x, 200, -672) at event
  5, P2 (x, 403.5, -672) at event 6 - DRY RUN`. Proves: the gates, that the node's height is the floor (else the
  line says the height is taken from +0x460), **the sign of the facing number** (if it reads -0.9x while he
  looks at the wall: `Angle=0` until the sign is turned in the file), the slot id.
- **K2** `Dry=0`: `climb: collision off (the climb starts; count 0 -> 1)`, `climb: edge 1: started
  /Movement/Climb/Up/High (slot 2507) ... clip ... of 52 frames (flags 10c0), events 5 at 6 and 6 at 20; aligned
  to (...) in 6 frames`, `climb: edge 1: frame 6.x: aligned to P2 (...)`, `climb: collision on (the climb is
  over; count 1 -> 0)`, `climb: edge 1: over after ~2080 ms: node (x, 404 .. 428, about -581)`. Picture
  (`kl_autotest --shots`): Kane on top of the wall. If instead `NOT climbed: the game did not keep the action`:
  the body's set has no clip (which body? the wardrobe's 16 bodies use Kane x4 / Lynch x12).
- **K3** walk on: he drops to the street (y 150) or onto a lid (y ~281); `bots: ... van 1` when he is in the
  exit box (z from -540). No fault, input back, no damage that kills.
- **K4** during a climb: stick, fire, reload, the cover key - does anything move him or start an action (no
  input is taken away)? A second climb right after the first. A climb with a pistol / unarmed (the lists'
  condition pairs).
- **K5** `Align=1`: the same climb without the two-step alignment - by eye, which end looks right (the 24.5
  settle of K2 against a slightly late grab).
- **K6** only if K2 fails: `Mode=vault`: `climb: edge 1: the game's own VAULT started ... action ...`, or the
  line that the start did not outlive itself (which answers the open question of section 3).
- **K7** a second round in the same process: a climb again; `count 0 -> 1` again (the count is 0 at rest).
  A round that ends during a climb: the `collision on` line still comes.
- **K8** a bots round with `[Climb] Enable=1`: the bots still leave by the gap; nobody but the human climbs.

## 8. Dead Men itself - what to look at, if the lead starts it

The files cannot say how the climb LOOKS and where it ends. The campaign shows it in its first minute:
chapter 'Withdrawal' (`Scenes\Locations\M03_A`), from the start (checkpoint 1 in the back street at about
(-2976, 154, -202)); the first obstacle is our wall, from the STREET side, at the dumpsters x -3332 .. -2816.
1. Street -> dumpster lid (124 up) -> wall top (120.5 up): which clip each is (both sit at the border: Low up
   to 120, Medium above), whether USE is needed or running into it is enough, how far from the face he can
   stand when it starts.
2. Drop into the car park (our yard), turn round, climb the wall from the yard side (184 by the mesh, 203.5 by
   the collision: `High`): does he end ON the wall near its far edge (predicted 44 past the yard face of a
   50-thick wall), **is there a settle of about 25 at the end** (decides `Align=2` against `Align=1`), does he
   keep his heading or turn to the wall, how long (predicted 2.08 s).
3. Step off the wall to the street: which landing plays for 253 down and for 122 onto a lid.
4. From the street the bare wall must refuse (253 > 220).
5. The crew at the lanes x -3210 / -2938: the `_NPC` clips on the three links - the picture the AI heisters
   would give with 5.1.

## 9. Assumed, not established, not done

- Nothing ran. The clips have never been loaded by Dog Days; `klclimb.c` has never been part of a built hook.
- ASSUMED: the root motion of a full-body clip started by the mini animation moves the player as a vault's does
  (both are `Play(clip, 1)` + AlignTo; vtable +0x214 treats them alike) and the movement class does not fight
  it; that nothing but the action system needs to know (camera, weapon state).
- ASSUMED: the player's node is at his feet (the vault's own end place is 'the player's own height' on the
  floor; kljoin's live lines show +0x460 at floor height). `klclimb.c` takes whichever of the two is at `Floor`.
- ASSUMED: row 0 of a rotation = the back (read in 0x857110, 0x619790 and the NPC mover; not seen).
- ASSUMED: the condition bits of Dead Men's lists (8, 0x10) mean the same in Dog Days; if not, the default
  (rifle) clip plays - every variant is a climb of the same class.
- Not established: whether stick input does anything during the clip; what the camera does while he rises
  along a wall; fall damage from 253; what the game does when the player dies with the hook's collision count
  held (the count is given back at the next tick - reasoned, not seen).
- Not established (part A): whether a forced low cover is entered at a 2 m wall; the player's distance from
  the face in cover (decides 1M / 2M). Not needed for the plan.
- Not done: the AI heisters' kind-1 links (5.1); edges on the street side (dumpster, then wall: the way back,
  and what the campaign-bank map of re/campaign_fa_bank.md needs at its start); other maps (`LINES` has only
  `M03_FA_A`); finding climbable edges of a whole map by itself; a gamepad key; anything online.
- The build stands on `z_hop\M03`, which fails this night's loot-window rule of `kl_fa_bots.check` (4.2). When
  the loot track delivers a new bank build, run `kl_fa_climb.py apply <that> <new folder>` on it.
