# Combat on a Dead Men map: the execution crash, what the enemies carry, ammunition

Agent s-combat, 2026-10-09, OFFLINE (nothing launched, nothing installed, nothing written into the Dog Days
folder). Build played by the owner: `<work>\build\play2` (F07 systems + M09_B + M09_A, balcony start, street
layer, SHIP hook). Material: `<work>\research\owner_round_1009_1820\` (hook log, `KLHook_1.dmp`, `KLHook_2.dmp`,
the game's own dump) and the watcher's pictures `<work>\research\watch\20261009_180847\`.

## 0. Summary

| the owner said | cause | status |
|---|---|---|
| 'game crashed when i went to execute' | read of 0 at kl2 0x4098a1: the define `ExecutionBloodSpatter` names the blood spatter's clone TEMPLATE instead of one of its pooled copies, because a Dead Men graft puts the clone groups before the systems subtree. Every Dead Men map built so far has it; the victim does not matter | **fixed in the tool** (`kl_fa.define_master`), checked (`kl_fa.check` CRASH `define-order`). Not run live |
| 'they all have the same pistol' | `kl_graft.dm_rename` replaced a missing Dead Men weapon by 'one of S's whose name starts alike'; the first `HG_` of the tree is `HG_M9Beretta_Human_Shield`. 57 of the 65 Dead Men characters carried the pistol of a player behind a human shield (a 58th as sidearm) | **fixed**: `tools/kl_arms.py`, a table by weapon class, depth and seed. Not run live |
| 'i run out of ammo' | stock Fragile Alliance has no ammunition on the map at all: a player re-arms from the guns the dead drop. Here 57 of the dead dropped the human-shield pistol and the seven AI heisters of an Arcade round are missing | weapons fixed (above); the missing bots are reported, not built (section 3) |
| 'the gun fire outside is sick' | F07's own police with their stock guns | untouched: those 26 actors are byte-equal before and after |

Two builds are ready, neither installed (section 4).

## 1. The crash: kl2 0x4098a1, 18:20:23

### 1.1 What the dump says

`python debug\dump.py KLHook_1.dmp`: c0000005 reading address 0 at 0x4098a1 in 0x4097c0 =
**ZFFActionShootHumanShield slot 11** (the action's event handler), `this` = 0x150d1c4, event id 0x14.

```
4097d3  ecx = [this+0x10]                        ; the player, 0x6d93ef20 (ZFFPlayer, RTTI)
4097e6  [this+0x14] != 0                         ; the victim, 0x6d933200 (its memory is NOT in the dump)
40980d  bone 7 of the victim -> its position -> the spatter's place
409854  defs = [[0xdd2640]+0xac] + 0x116c        ; the scene's define table (0x566c10)
409871  defs->slot +0x7c ("ExecutionBloodSpatter", &ref)
409887  ent = 0x8ccde0(ref) ; 40988d cast 0x5e1a20 ; 409895 [0x1548e80] = ent
40989e  eax = [ent + 0x58]                       ; = 0
4098a1  edx = [eax]                              ; <== the fault
4098b8  call [edx + 0x194] (room, position, matrix, 0, 1) -> the clone ; then message "Activate"
```

`[0x1548e80]` in the dump = 0x6d8c4700 = a **ZAllocMany** (vtable 0xba215c). Its fields: word +0x50 = 8 (pool
size), byte +0x5e = 0 (not a copy), dword +0x60 = 0x2a (the REF of its clone group), +0x68 = a pointer (its array
of copies), **+0x58 = 0**. That is a template with eight copies, not a copy.

### 1.2 Who writes +0x58

ZAllocMany slot 84 (0x48e1b0), run on a template (`[+0x5e] == 0`, pool size != 0): it resolves the clone group
`[+0x60]`, walks the group's children and stores on each child object `[copy + 0x58] = this` (0x48e1f3) and the
copy in `[this + 0x68][i]`. So **+0x58 is a copy's pointer to its template** and is 0 on the template itself.
The execution code wants a COPY: it asks the copy's template for a clone.

### 1.3 Why the define names the template here and a copy in stock

`ExecutionBloodSpatter` is set by a controller `ZSetZDefine` (Init = slot 13, 0x5c9b20: stores name -> its own
entity through the define table's slot +0x54). The template
`...equipment.zip\AllLevels/MaterialDefinitions.zip\Effects/BulletImpacts.zip\Bullet\Blood_02` carries it, and so
does each of its eight copies under the top-level group `CloneGroup_Effects/BulletImpacts.zip/Bullet/Blood_02`.
Nine setters of one name; the last one to run wins.

| level | first setter | last setter |
|---|---|---|
| all 21 stock Dog Days levels (F01..F09, L00..L11) | the template | **a copy** |
| `build\play2` (played) | a copy (node 4270) | **the template** (node 18169) |

(`kl_fa.define_order`; table from a scratch census of all 21 levels.) Stock levels have the systems subtree before
the clone groups. A graft takes the top-level order of the MAP (`kl_prpjoin.graft_picks`), and a Dead Men map has
its clone groups first: in play2 the clone groups are top-level entries 30..537 of 850 and
`AllLevels/mainsceneincludes_multiplayer.zip` comes after them.

'The last Init wins' was not read in the define table's code (its vtable is not in the dump). It rests on the
two facts above: the dump holds the template, which is the last setter of that build and the first of every
stock level. 'Init order = scene order' is the ASSUMPTION behind 'last'.

### 1.4 The victim

Not established and not needed. `[this+0x14]` = 0x6d933200 is outside the dump's memory. The player had gone
through the join 71 s before (hook log 18:19:11, at (6380, 570, -6345) = the street), stood in a ZROOM
(0x7822f6a0), and the watcher's last picture (`0086_693s.jpg`) shows him holding a man in a black helmet with
a white band in front of a burning car. The fault is in the effect lookup, after the victim's bone was read
without trouble: any execution, of anyone, anywhere on the map, takes this path.

### 1.5 Who is exposed

`python tools\kl_fa.py check <archive>` -> `CRASH define-order`:

| build | define-order | special NPC weapons |
|---|---|---|
| `play2` Retomoto (played) | CRASH | 58 x HG_M9Beretta_Human_Shield, 1 x Mg_Minimi_SPW_L10_Heli |
| `expansion\KLExpansion\Maps\DM01` (M01) | CRASH | 7 x human-shield pistol |
| `...\DM02` (M02) | CRASH | 4 x |
| `...\DM03` (M03, the bank) | CRASH | 6 x |
| `...\DM06` (M06) | CRASH | none (13 x SMG_UMP_SBR, DEGRADED) |
| `...\DM09` (Retomoto) | CRASH | 56 x + the helicopter gun |
| nine stock FA levels (`kl_fa.py stock`) | 0 CRASH / BROKEN | 0 |
| `s_combat\...` and `s_combat\play2_combat` (new) | none | none |

So every Dead Men map delivered so far crashes on the first execution. The earlier rounds did not meet it
because nobody executed a human shield.

### 1.6 The fix

`kl_fa.define_master(sc)` (called by `kl_fa.repair`, so by every `kl_graft.build` with the FA layer): a clone
template that sets a define AFTER its pooled copies gets the define name `<name>_Template`. The last setter of the
real name is then the last copy, exactly as in stock. Only a string value of one controller changes; no entity
moves, no controller is removed. GUESS: one more name in the define table is harmless (stock levels have 22..27).

Not chosen: putting S's systems subtree before its clone groups in `kl_prpjoin.graft_picks` (not my file; it
would restore the stock order for everything that may depend on it, at the price of moving thousands of slots).
Worth a thought for the lead: this crash is one consequence of the reversed order, there may be others.

Seen beside it, not acted on: M09_B brings a template of its own
(`Locations/M09_B/...\Effects/BulletImpacts.zip\Bullet\Blood_02`, pool size 5, no define) that names the same
clone group as S's template (pool size 8). Both claim the copies in their slot 84; the later one (S's) owns all
eight `+0x58` pointers in the end. Two templates hand out the same copies. No fault known from it.

## 2. What the enemies carry

### 2.1 Played build, before (`python tools\kl_arms.py table <work>\build\play2\F01_Main.zip`)

Weapon = `ZFFActor[1]` (field 20 of the object), secondary `[3]` (22), grenades `[4]` `[5]` (23, 24).

| who | actors | Dead Men gave | the played build had |
|---|---|---|---|
| tower guards (`AI_Players!Enemies!020_Office` .. `070_Elevators`, 24 squads) | 45 | 44 x HG_HK_USP_01; the MG guy Mg_Minimi_SPW_01 + USP | 44 x **HG_M9Beretta_Human_Shield**; **Mg_Minimi_SPW_L10_Heli** + shield pistol |
| street, Dead Men's police (`Enemies!010_RetoBldFront`, `020_Street`, 10 squads) | 20 | 13 x USP (5 with a tear-gas launcher as secondary), 6 x Smg_MP5-A3_01, 1 x launcher | 13 x shield pistol (5 + launcher), 6 x **SMG_UMP_SBR**, 1 x Launcher_HK69A1_01TearGas |
| street, F07's police moved there (`Gameplay!020_Loot` .. `040_Escape`, 14 squads + a dog) | 27 | - | Rifle_AK74 17, SMG_Type05 5, Rifle_Type88 2, HG_SW_MP45 2 (stock, unchanged) |

Dead Men's whole campaign levels, for the record: M09_A has 73 x USP, 22 x MP5 (the 'civilians' carry it in the
data), 2 x M4A1, 2 x SG552, 2 x Minimi, 1 Remington, 1 P90; M09_B 85 x MP5, 30 x USP, 7 x Remington 870,
3 x M4A1, 2 x SG552, 2 x Sn_Rem700, 1 Minimi, 8 launchers. The level's designers really did give Retomoto's
guards one pistol for all; variety is the owner's wish, not a restoration.

### 2.2 Why 'the same pistol', and what was wrong with it

`dm_rename` took the first of S's templates whose name starts like the missing one. No stock Dog Days level
gives an NPC a human-shield pistol, a UMP or a helicopter gun (census of all 21, `STOCK_NPC` in kl_arms.py).

Animations: kl2.exe builds `/Weapon_Handling/%s/...` from a table indexed by the item enum (0x154a650, filled by
0x4b1530; entries 1..50 read from the code, e.g. `Rifle_Type95_L09_NPC` -> `Rifle_Type95`). A stock character
set has 29..57 slots in the folder of a real weapon and **3** in `HG_M_77B_Human_Shield`, which the table's last
two entries name (ASSUMPTION that these are the two shield pistols; the index for items above 50 was not read).
What an NPC does without aim / reload / cover clips was not established - the owner fought them, so they shot.
Control: with this table every armed NPC of all 21 stock levels has its folder in its own animation set
(`python tools\kl_arms.py stock` -> 0 findings).

### 2.3 Every weapon template of F07's equipment tree (`python tools\kl_arms.py templates F07`)

All 61 are in every Fragile Alliance level. NPCs: carried as primary in the nine FA levels / the twelve story
levels / as secondary anywhere.

| class | in a pool (stock NPC weapon) | stock NPC weapon, in no pool | never given to an NPC by stock |
|---|---|---|---|
| pistol | HG_M9Beretta 26/27/1, HG_M-77B 18/37/2, HG_SigSauer226 7/0/0, HG_SW_MP45 4/0/0 | HG_DesertEagle 1/5/12, HG_M9Beretta_S 0/1/1 | HG_TT-33, HG_TaurusJudge, HG_M-77B_S; **HG_M9Beretta_Human_Shield, HG_M-77B_Human_Shield** (special) |
| revolver | HG_Revolver_Police 0/29/0 | | HG_ColtCobra |
| SMG | SMG_Type79 35/100/0, SMG_Type05 26/103/0, SMG_MPi69 20/0/1, SMG_MAC_10 13/84/0, SMG_HK_sp89 5/1/0 | SMG_Type05_S 0/81/0, SMG_SA61 0/41/0 | SMG_UMP, SMG_UMP_SBR, SMG_UMP_Silenced, SMG_MAC_10_Silenced |
| rifle | Rifle_AK74 137/39/0, Rifle_FN_SCAR 6/0/0, Rifle_Type81 2/0/0 | Rifle_zastavam85 68/43/1 (the bots' gun), Rifle_Type88 2/47/0, Rifle_Type95_C 0/134/0 | Rifle_AK47, Rifle_Type95_S; Rifle_Type95_L09_NPC 0/50/0 and Rifle_Type88_L09_NPC (level-tuned: special) |
| marksman | Rifle_Type88_S 4/10/0 | | Sn_Rem700 |
| shotgun | Shotgun_Hawk_Police 0/54/0, Shotgun_Hawk_Bullpup 0/53/0 | Shotgun_Hawk_SawnOff 0/30/1 | Shotgun_Remington_870, Shotgun_Spas12, Shotgun_TPS |
| machine gun | MG_GP_Type88 0/9/0 | | Mg_Minimi_SPW; the six `_Heli` / `_Player` / `_L09_NPC` variants (special) |
| launcher / rocket | RPG_7V 0/8/0 | | the three Launcher_HK69A1, RPG_7V_Hind |
| grenades | | | all five (no stock NPC has one in its grenade fields) |

No stock FA level gives an NPC a shotgun or a machine gun; those two pools are proven in the story levels only.

### 2.4 The rule (tools/kl_arms.py, docstring = the full text)

1. Dead Men weapon -> class (`DM`: all 36 templates of Dead Men's 20 levels, by their own `WT_` enum) -> pool of
   Dog Days templates (`POOLS`). In a pool only: stock gives it to an NPC, and it is no special variant. Handed
   out only if the level has the template and the actor's animation set has its folder (20 slots or more).
2. The class the designer gave is the default: the MG guy keeps an MG (MG_GP_Type88), a rifleman a rifle.
3. Variety (`MIX`, **all numbers are GUESSES**): the pistol carriers of a zone become pistol 70 -> 30 %,
   SMG 25 -> 35 %, shotgun 5 -> 20 %, rifle 0 -> 15 % from depth 0 to 1; the SMG carriers SMG 85 -> 55 %,
   rifle 10 -> 30 %, shotgun 5 -> 15 %. Zone = the first three-digit number of the squad name
   (`020_Office` .. `070_Elevators`), ranked within the map; `LEVEL_DEPTH` puts the tower on 0.0..0.6 and the
   street on 0.6..1.0 (GUESS: the street is the second half of the round); other maps 0.2..0.8.
4. Who of a zone is upgraded and which template of a pool an actor gets follow crc32(seed | scene path): seed
   2026 by default (`build(arms_seed=...)`), the same map and seed give the same weapons.
5. Conservative choices, each one switch in `arm()`: **launchers are not handed out** (no stock Dog Days NPC
   carries one; the launcher man gets an SMG, a launcher secondary is emptied - Retomoto loses its five
   tear-gas secondaries and one launcher) and **grenade fields are emptied** (none in 21 stock levels).
6. An actor whose set has no weapon folder (Dead Men's civilians) gets no weapon, as stock civilians.
7. Sounds need nothing: a template's sounds are offsets into S's bank, which the graft never moves. The 24
   weapon animation sets and the character sets are S's; a Dead Men character set is a copy of a Dog Days one.

### 2.5 After (`python tools\kl_arms.py compare <play2> <new>` prints every squad)

| who | after |
|---|---|
| tower, 44 pistol carriers | pistols 26 (HG_M9Beretta 10, HG_SigSauer226 6, HG_SW_MP45 6, HG_M-77B 4), SMG 12 (Type79 4, Type05 4, HK_sp89 3, MPi69 1), shotguns 6 (Hawk_Police 4, Bullpup 2) |
| tower, the MG guy | MG_GP_Type88 + HG_SW_MP45 |
| street, Dead Men's police, 20 | SMG 9, shotguns 4, pistols 4, rifles 3 (AK74 2, Type81 1) |
| F07's police | unchanged |
| whole level, 92 | Rifle_AK74 19, SMG_Type05 13, HG_M9Beretta 11, HG_SW_MP45 10, HG_SigSauer226 7, Shotgun_Hawk_Police 7, SMG_HK_sp89 6, SMG_Type79 4, HG_M-77B 4, Shotgun_Hawk_Bullpup 3, SMG_MPi69 2, Rifle_Type88 2, one each of MG_GP_Type88, SMG_MAC_10, Rifle_Type81; the dog none |

Examples: boardroom `Squad_Guards_Inside_03` SigSauer, Beretta, silenced HK; `Squad_Guards_Inside_01` SW MP45 and a
Hawk shotgun; `070_Elevators!010_Squad_Elevators` two pistols and a shotgun.

## 3. Ammunition

- **Stock Fragile Alliance has no ammunition and no weapon lying on the map.** Map-side objects of the item
  classes in the nine FA levels: 0 (only helicopter guns). The classes exist - story level L03 has
  `ZFFItemWeapon` pick-ups (`Special!Pickups!SMG_Mac10_Labyrinth`, a template path and 90 rounds) - but FA does
  not use them. So none were added.
- Every weapon has its own ammunition template (`equipment.zip\Ammo\<weapon>`, 54 of them, identical in the
  played build and in F07): a player gets rounds by picking up a gun, his own kind to top up or another to swap.
  A dead NPC drops its weapon's `Ground` item (template field 31). So the supply IS the enemies' guns.
- On the played build 57 of the 65 armed Dead Men characters dropped the human-shield pistol. Whether a player
  can pick that item up at all was not established; nothing in stock ever drops one. With the table the dead
  drop what stock FA police drop.
- **The missing bots.** `kl_fa.check` on this map: 'no bot squads (TriggerLootDepleted 0, stock 7)'. In a
  stock Arcade round seven AI heisters (`Gameplay!merc_bot_squad`, Rifle_zastavam85 x 7 in F07) fight beside
  the player; here he meets 91 armed enemies alone. That, more than any ammunition rule, is why one player runs
  dry - the owner's guess 'with more heisters its fine' is right for a real match, and for Arcade it needs the
  bot squad. Not built: it belongs to the authored FA layer (tools\kl_fa_author.py, not this agent's file).
- Not established: ZFFActor fields 25 / 26. Stock FA actors hold pairs like 20/40, 30/40, 20/30, 4/10 (the
  Type88, clip 10), story actors mostly -1/-1 or 90/90, 27/27; Dead Men's converted actors have -1/-1. They LOOK
  like the rounds in a dropped weapon (min / max); the readers were not found (member offsets +0x7dc / +0x7e0
  are too common to trace by scanning). Left as they are: -1 is what most story enemies have.

## 4. Code, tests, builds

Code (not committed):
- `tools/kl_arms.py` (new): `arm`, `check`, `table`, `transplant`, `patch`; commands templates / table /
  compare / check / patch / stock.
- `tools/kl_fa.py`: `define_order`, `define_master` (in `repair`); `check(sc, snd, loc, anm=None)` adds CRASH
  `define-order`, BROKEN `npc-weapon` / `npc-weapon-anim`, DEGRADED `npc-weapon`; command `defines`.
- `tools/kl_graft.py`: `dm_rename(..., arms=True)` no longer guesses weapons; `build(arms=True,
  arms_seed=None)` calls `kl_arms.arm` right after the join; `verify` hands the joined .ANM to `kl_fa.check`;
  flag `--no-arms`.

Tests run:
```
python tools\kl_arms.py stock            21 stock levels: 0 findings; census equals STOCK_NPC: True
python tools\kl_fa.py stock              nine stock FA levels: 0 CRASH / BROKEN findings
python tools\kl_fa.py check <play2>      CRASH define-order; BROKEN npc-weapon (59 NPCs)          = the owner's round
python tools\kl_fa.py check <DM01 DM02 DM03 DM06 DM09>     CRASH define-order in all five (table 1.5)
python tools\kl_fa_street.py test <work>\build\s_combat --keep
                                         RESULT: PASS. kl_graft.verify 1 problem, known ('39 particle template names
                                         do not resolve (stock M09_A: 36)'); kl_fa.check DEGRADED bots only;
                                         kl_fa_street 0 faults; 25,725 entities, 313 MB
python tools\kl_arms.py check <new>      0 findings        python tools\kl_impact.py <new>   problems: 0
python tools\kl_arms.py patch <play2> <new archive> <work>\build\s_combat\play2_combat
                                         65 actors re-armed, 1 define renamed; the .prp is the only member that differs
```

Builds, both with Retomoto's `KLJoin.ini` copied in from `build\expansion\KLExpansion\Maps\DM09` (the box and
target the hook logged in the owner's round; `kl_graft.install` REMOVES the slot's file when the folder has none):

| folder | what it is | differs from the played build in |
|---|---|---|
| `<work>\build\s_combat\play2_combat\` | **the played build + only these two fixes** | the .prp: 65 ZFFActor objects (weapon fields) and one ZSetZDefine string. Every other member byte-equal |
| `<work>\build\s_combat\R09+M09_A (R09 = F07+M09_B)\` | a fresh build from the working tree at 18:35 | the same 66 objects AND the other agents' uncommitted work of that moment (3,547 ZSTDOBJ, 98 ZSHADOWMESHOBJ, lights, .MAT, .prm, .oct, .buf, .gms differ) |

For the owner's next round the first is the smaller step: `python tools\kl_graft.py install F01 --from
"<work>\build\s_combat\play2_combat"`.

## 5. Not known

- Nothing here has run in the game: not the execution, not one of the re-armed guards.
- That the last ZSetZDefine wins, and that Init runs in scene order (1.3).
- What else depends on the systems subtree coming before the clone groups (1.6).
- How NPCs with a shotgun or the Type88 machine gun behave in a Fragile Alliance round: stock gives those to
  NPCs in the story only.
- Which class each MIX share should be: they are a first guess at 'mostly pistols with some SMGs, heavier deeper
  in'. One line each in `kl_arms.MIX`, `POOLS`, `LEVEL_DEPTH`.
- Tear gas: Dog Days has the launcher templates, their folder (35 slots) and the item enums, and the played
  build carried six of them for 70 s on the street without a fault being traced to them. Whether its police can
  use them is open; `arm(launchers=True)` hands them back.
