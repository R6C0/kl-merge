# Gun looks on the map builds (2026-10-10, agents t-guns and g-fit)

**Second pass, 2026-10-10 afternoon (agent g-fit): sections 8 to 11.** The owner played the first build that
showed a look (`rt_guns/retomoto_ai2_guns`): *"it holds the mp5 weird and if i try for the ak 74 starter game goes
grey feels like it crashed weird but it didnt because i could back out then equip the mp5 i dont like how it uses
the ak sound too"*. So the hide bit of section 2 WORKS in the game (the MP5 was drawn alone in the hands). Sections
1 to 7 are the first pass as written; where 8 to 11 differ (the P90's pairing, the table in 3, the sheet) the later
section holds. Builds of the second pass: `<work>/build/t_guns2/<M01|M02|M03|M06>`, `<work>/build/rt_guns2/retomoto_ai2_guns`.

The owner on Late Night Opening (build `z_maps/M02`): *"dead men guns dont show up in the late night"*.
Everything below is offline work: files read, kl2.exe disassembled, builds made and checked. Nothing was run in
the game, nothing was installed. Tool: `tools/kl_map_guns.py`. Builds: `<work>/build/t_guns/<M01|M02|M03|M06|RT>`.

## 1. Which "Dead Men guns" failed

**The gun LOOKS (the Guns page), not the enemies' weapons.** Evidence:

- `<DD>/KLHook.log`, the owner's session: 30 lines `guns: menu set KLGunStart = ..` / `KLGunSet = ..` between
  11:52:34 and 11:58:16, around three loads of the slot (11:54:23, 11:55:00, 11:58:34). `KLHook.ini` ends with
  `[Guns] Start=2 Set=1`. The owner chose looks on the page and then looked for them.
- Not one `guns: level ... has N gun(s) with looks` line: the slot had no `KLGuns.ini` (the four map builds and
  Retomoto were made without `kl_guns`). With no file the hook does nothing, by design.
- The enemies (section 4) carry Dog Days guns on purpose (`kl_arms`), all drawn; no Dead Men weapon entity is left
  on the map side of any build (61 `ZFFItemTemplateWeapon`, all of the systems level; `dangling_templates` 0).

## 2. A second fault behind the first: the looks could not have worked as built

`kl_guns` hides a look by giving its parts a variant byte (100 + n) that "matches nothing"; `klgun.c` shows a
group by writing 0 into its variant bytes. kl2.exe does not draw that way. The walk over a model's mesh objects
(function 0x67cc60; disassembled here with `debug/dasm.py 0x67cf40 70`, and already quoted in
`re/pd2_klside.md` 5 and `re/firstperson_assets.md`):

```
0x67cf68  mov  ebp, [eax*4 + 0xeac7b0]          ; the mesh object (chunk table)
0x67cf77  test dword [ebp+0x1c], 0x800000       ; HIDE bit in the object's draw-mode word
0x67cf7e  jne  skip
0x67cf84  mov  al, [ebx+0x158]                  ; the entity's variant
0x67cf8a  test al, al
0x67cf8c  je   take                             ; variant 0: EVERY object is taken
0x67cf8e  cmp  byte [ebp+0xf], al
0x67cf91  jne  skip
```

The same pair of tests at 0x57ee43 .. 0x57ee7a (function 0x57ed50). A gun entity's variant is 0 (all 61 weapon
templates' `Ground` in every build looked at), so:

- a `kl_guns` build draws **every part of every group at once** - the Zastava, the MP5 and the AK-74 inside one
  another (the right-hand column of `<work>/build/t_guns/M02_sheet.png` is that picture) - with any hook or none;
- `klgun.c`'s variant-byte writes change nothing.

This is static reading; `guns_F01` was never run, so nothing live contradicts or confirms it. `kl_guns.py`'s
"ASSUMPTION: an object is drawn when its variant byte equals the entity's" holds only for entities whose variant
is not 0 (people).

**What does hide a part:** bit 0x00800000 of the mesh object's dword +0x1c. All four places in kl2.exe that
`test dword [reg+0x1c], 0x800000` (byte search over .text: 0x57ee43, 0x67cf77, 0x7581e1, 0x7af091) are walks
that take a mesh object out of the chunk table and skip it when the bit is set. Stock Dog Days uses the bit on
4,432 mesh objects of five levels counted (F01 711, F02 459, F07 856, L03 1,196, L10 1,210), 24 of them rigid
one-bone parts like a gun's. No weapon template part has it in stock F01 (299 parts: words 0x880, 0x80880, 0x80).

NOT KNOWN: whether 0x67cc60 runs every frame or once per instance. `0x88c810` (the look change of a person)
notifies the renderer after storing the variant, which suggests the result is kept per instance. It decides only
whether a switch during a round shows on guns that already exist (section 5), not what a build shows.

## 3. What `tools/kl_map_guns.py` does

`python tools/kl_map_guns.py build <build folder> <out folder> [--start=1] [--set=1]`
(`all` = the five builds into `<work>/build/t_guns/<tag>`; `check`, `weapons`, `sizes`; docstring = the spec).

1. `kl_guns.build()` on the folder, unchanged (it works on a wardrobe build: `kl_chars.put` keeps the wardrobe's
   roots alive through `KLWardrobe.ini`, the Dead Men gun models go into dead chunk indices).
2. The stock parts of the six gun models become private copies (35 objects of 64 bytes; geometry shared), so a
   hide bit never reaches another model that names the same mesh object.
3. Hide bit on every group but the one to show. **The look is baked into the build**: `--start` / `--set` are the
   Guns page's two numbers (default 1 / 1 = MP5 on the Zastava and the Dead Men look on the other five). No hook
   is needed for the baked look to be drawn.
4. `KLGuns.ini` **Version=2** beside the archive (Version 1's keys + `HideWord=28`, `HideBit=8388608`, per gun
   `Shown=<group>`). The installed hook (dinput8.dll sha1 c120880a, contains klgun.c as in the repository)
   accepts `Version == 1` only and leaves the file alone without a log line: its variant writes would be
   meaningless here, and a false "now shows MP5" line with them.
5. `steps.json` gets a `guns` entry and the new member ids (without that `kl_maps.audit` refuses the folder:
   "changed after the steps were recorded"); `kl_maps.preflight` and `kl_maps.audit` are run again on the result.

Checks run by the command on the WRITTEN folder: the game's walk (hide bit, then variant) takes exactly the shown
group of each gun and something of it at full detail; every part is a rigid one-bone part on a bone of the Dog
Days gun; no part is in two models' object tables; `kl_chars.check`; `kl_impact.check` (bone ids, chunk limit,
surface table); every one of the 61 weapon templates has a model the walk takes at full detail and no material
of a taken part lacks a compiled shader; `kl_maps.audit`.

### Results (all: problems 0)

Bytes of the four members that are read into one block each, before -> after. `.ANM`, `.fxc`, `.WAV`: unchanged
in all five (byte-identical members). The chunk table has 69,632 usable entries.

| build | .prm | table entries | dead indices before / still free | .ANM | .fxc | .WAV | .TEX (MB) | archive | audit |
|---|---|---|---|---|---|---|---|---|---|
| M01 diner | 55,088,000 -> 55,479,264 | 50,042 -> 50,136 | 11,433 / 11,142 | 22,061,764 | 17,760,648 | 21,722,704 | 234.5 -> 242.7 | 201 MB, sha1 6e3808e0 | PASS (0; 1 known) |
| M02 Late Night Opening | 54,619,216 -> 55,010,480 | 58,371 -> 58,465 | 11,437 / 11,146 | 22,202,472 | 17,760,648 | 22,527,568 | 216.1 -> 224.3 | 182 MB, sha1 b1814e64 | PASS (0; 6 known) |
| M03 bank | 60,469,040 -> 60,860,304 | 62,680 -> 62,774 | 11,452 / 11,161 | 22,202,616 | 17,760,648 | 22,716,752 | 217.8 -> 225.9 | 192 MB, sha1 ec5ba62f | PASS (0; 0 known) |
| M06 park | 49,585,744 -> 49,977,008 | 46,902 -> 46,996 | 11,442 / 11,151 | 21,642,576 | 17,760,648 | 21,775,744 | 204.6 -> 212.8 | 181 MB, sha1 90a2563f | PASS (0; 6 known) |
| RT Retomoto (`rt_ai/retomoto_ai`) | 79,269,328 -> 79,440,352 | 65,119 -> 65,213 | 5,062 / 4,771 | 21,642,904 | 17,760,648 | 23,041,360 | 256.8 -> 264.9 | 219 MB, sha1 7805749e | see below |

- What is added and why: `.prm` +0.39 MB (Retomoto +0.17: the stubs of dead chunks save 0.4 MB) = six Dead Men
  gun models (MP5, SG 552, M4A1, P90, Steyr TMP, USP; one put) in 291 dead indices, and 94 chunks at the END
  of the table (59 of `kl_guns.build`: part copies, six roots, six object tables; 35 private stock parts).
  `kl_guns.build` reads the file afresh after the put, so its own chunks do not go into dead indices; 94 entries
  is 0.13 % of the table. `.TEX` +8.2 MB = the guns' textures. `.MAT` +15 KB, `.oct` +12 empty records.
- Retomoto: `kl_maps.audit` does not run on it (its systems level is `R09`, no stock level:
  `FileNotFoundError: R09`; the source folder has no audit either). Instead the checkers that need no stock level
  (`kl_fa.check` BROKEN, `kl_arms.check` BROKEN, `kl_chars.undrawn`, `kl_chars.check`) on source and result:
  1 finding on the source, the same 1 now, 0 new. `KLJoin.ini` and `KLWardrobe.ini` (with the Payday 2 masks) are
  carried along.
- "Nothing but the guns changed", measured on M02, M03 and Retomoto (scratch `same.py`): members changed are
  `.MAT .TEX .gms .oct .prm .prp`, no file beside the archive; of the 42,868 / 47,162 / 56,138 chunks the source
  level reaches **0** differ in the gun build; the wardrobe models (13,956 / 13,956 / 19,372 chunks) are byte for
  byte the same; the scene differs in seven objects, the six guns' `Ground` and `HG_M9Beretta_Human_Shield\Ground`
  (it shares the Beretta's model, so the human-shield pistol shows the USP too).
- Every look covers at least the detail levels its Dog Days gun covers (stock guns: levels 0..4; MP5, SG 552,
  M4A1, Steyr TMP, USP: 0..7; P90, AK-74: 0..4). 0 parts had to be put on an ancestor bone.
- Pictures (kl_view, `kl_guns.py sheet`): `<work>/build/t_guns/M02_sheet.png` - stock, look, both over each
  other, from the M02 build: the looks sit on the Dog Days guns' grips as on stock F01.

## 4. What the enemies carry, and what lies on the floor

`python tools/kl_map_guns.py weapons <folder>`. `kl_arms` hands every Dead Men character a Dog Days template;
a dropped gun is the same template's model, so the floor shows what the hands showed. All 61 templates' models
are drawn in all five builds (0 problems); `kl_chars.undrawn` 0 people in the four maps.

| build | placed actors' primary weapons | of those with a Dead Men look in the t_guns build |
|---|---|---|
| M01 | SMG_Type05 4, HG_SW_MP45 2, Shotgun_Hawk_Police 2, HG_M-77B 1, Rifle_AK74 1, Rifle_Type81 1, SMG_MAC_10 1, SMG_Type79 1 | 1 of 13: MAC-10 -> Steyr TMP |
| M02 | Rifle_AK74 3, SMG_MPi69 3, HG_M9Beretta 2, Rifle_FN_SCAR 2, SMG_Type79 1, Shotgun_Hawk_Police 1 (+ 3 unarmed civilians) | 4 of 12: Beretta x2 -> USP, SCAR x2 -> SG 552 |
| M03 | Rifle_AK74 5, Rifle_Type81 3, SMG_Type79 2, HG_M9Beretta 1, HG_SigSauer226 1, HG_SW_MP45 1, Rifle_FN_SCAR 1, Shotgun_Hawk_Bullpup 1 | 2 of 15 |
| M06 | SMG_Type79 3, Rifle_AK74 2, SMG_MPi69 2, SMG_Type05 2, Rifle_FN_SCAR 1, Rifle_Type81 1, Shotgun_Hawk_Police 1, SMG_HK_sp89 1, SMG_MAC_10 1 | 2 of 14 |
| RT | Rifle_AK74 19, SMG_Type05 13, HG_M9Beretta 11, HG_SW_MP45 10, Shotgun_Hawk_Police 7, SMG_Type79 7, SMG_HK_sp89 6, HG_M-77B 4, HG_SigSauer226 3, ... | 14 of 91: Beretta x11, SCAR x2, MAC-10 x1 |

So with the owner's six pairings most guards still show Dog Days models: the pairings are shop guns, and
`kl_arms` prefers other templates for guards (P90 carriers get the MPi69, MP5 carriers the Type 05, M4A1 / AK-74
carriers the Dog Days AK-74). If guards should visibly carry Dead Men guns, the looks belong on the templates
guards carry. A table that would do it (NOT built; every pairing a GUESS for the owner to decide, because it
also changes what those shop guns look like for the player): MP5 on SMG_Type05, P90 on SMG_MPi69, Steyr TMP on
SMG_Type79, USP on HG_SW_MP45 / HG_SigSauer226 / HG_M-77B, Dead Men's AK-74 (`Rifle_AK74_01`, 3 parts) on
Rifle_AK74, Remington 870 on Shotgun_Hawk_Police, SG 552 on Rifle_Type81. `klgun.c` holds 16 guns
(`KLG_NGUN`); the six of today plus these nine is 15.

The player's guns: no object of the level names a weapon template for a player (searched every property and
controller of the M02 build: only the templates' own collision boxes) - the loadout comes from the exe by item
number. That item 29 (Zastava) is the starting rifle is `kl_guns` / `klgun.c`'s statement; not checked here.
The seven AI heisters of a stock level carry it (`re/bots_squad.md`), so they will show the MP5 once they exist
on these maps.

## 5. For the Guns page to SWITCH: the change `klhook/klgun.c` needs (not this agent's file)

With a t_guns build and today's hook the page's two options are saved but change nothing; the build shows what
was baked (MP5 + the five Dead Men looks). To make the page work:

- `klg_level_open`: accept `Version` 1 or 2 and keep it; for 2 read `HideWord` (28 = 0x1c) and `HideBit`
  (8388608 = 0x00800000), refuse other values.
- `klg_apply`, Version 2: for object i of group g read the dword at `objs[i] + 0x1c`; the bit must be SET when
  `g != want`, CLEAR when `g == want`; write the one byte `objs[i] + 0x1e` (bit 0x80) through `klh_data`. Leave
  the variant bytes alone. Version 1 files (the old `guns_F01`) should be refused with a log line: their groups
  cannot be hidden by variant.
- Everything else (the table walk, the checks, `KLGunStart` / `KLGunSet`, the page) stays.
- Open, live only: whether the bit is read per frame or kept per gun instance (section 2). If kept, a change
  made in the menu before the level is loaded still needs the write to land before the round's guns are made;
  the tick runs about once a second and a level loads in about 2 s. Safer: apply from `klg_level_open`'s side as
  soon as the chunk table is filled, not from the tick.

Change `tools/kl_guns.py` needs (not this agent's file): its docstring / `write_ini` / `check` describe the
variant mechanism; `gun_node` should also take `Ground01` (section 6). `kl_map_guns.py` works around both from
outside (it sets `kl_guns.LOOKS` / `kl_guns.gun_node` for the call and restores them).

Suggested for `kl_maps.audit` (not this agent's file): print `steps.json`'s `guns` list beside `lighten` and
`wardrobe` in the "since that verify" line.

## 6. Dead Men guns without a look, and what adding them takes

Dead Men's 36 weapon templates are in M01_FA_A's equipment tree with a model each (scratch `dmguns.py`). With a
look today: MP5, SG 552, M4A1, P90, Steyr TMP, USP (+ Dog Days' own AK-74 on the Zastava).

| Dead Men gun | model | state |
|---|---|---|
| Ruger Mini-14 `Rifle_RugerMini14_01` | 5 rigid parts; model object named `Ground01` | `kl_guns` says "in no level's equipment tree": wrong, `gun_node` only looks for `Ground`. Tried here (`--extra`, on Rifle_Type88): builds, all checks pass, but the picture shows it **about 30 degrees nose-up** against the Dog Days rifle - its parts are not in the model space `kl_guns` assumes. Needs the rest frame of its `w_bone_frame` applied to the look's vertices (private geometry instead of shared). |
| Taurus `Gun_Taurus_01` | 17 rigid parts, `Ground01`; cylinder and bullet bones exist on Dog Days' HG_ColtCobra too (0 parts folded) | Tried (`--extra`, on HG_ColtCobra): builds and passes, orientation right, but **about 1.4 times the Colt's size** in the picture; needs a look at whether that is the real size difference or a scale. |
| AK-74 `Rifle_AK74_01` | 3 rigid parts | fits as it is; no pairing chosen (Dog Days has its own AK-74) |
| Remington 870, PKM, Minimi, Rem 700, USP silenced, HK69 launcher, RPG-7 | 6 / 6 / 4 / 6 / 6 / 4 / 3 rigid parts | fit the mechanism; need a pairing (Dog Days sells a Remington 870 and has an RPG-7 of its own) |
| SPAS-12 `Rifle_Spas12_01` | 4 objects, none a rigid one-bone part | `kl_guns._part` refuses it; needs weighted parts handled |

Picture of the two tried: `<work>/build/t_guns/_extra/M02_sheet.png` (last two rows). `--extra` stays in the tool
as that experiment and is off by default; **do not ship an `--extra` build**.

## 7. For the lead

Order among the steps on a finished build: the gun step ADDS chunks (94 at the end, 291 into dead indices) and
`KLGuns.ini` names chunk indices of this `.prm`. Run it after anything that renumbers or stubs chunks
(`kl_graft lighten`, the wardrobe, `kl_add_plates`); steps that only edit values (`.prp`, `.gms`) may come after
it. A later `kl_chars.dead_indices` pass is safe (the six new roots are named by entities). After any later
step: `python tools/kl_map_guns.py check <folder>` (re-reads the written folder; exit 1 on a problem).
The command refuses a folder that already has `KLGuns.ini`.

To bake other looks: `--start=0|1|2` (Zastava: own model, MP5, AK-74) and `--set=0|1` (the other five). The
owner's saved choice is `Start=2 Set=1`; the builds here use 1 / 1 because the complaint was about Dead Men
guns and the AK-74 is a Dog Days model. `--start=0 --set=0` gives a build that looks stock and can still be
switched once the hook is changed.

### What the owner does to see a Dead Men gun (with a t_guns build in the slot, today's hook)

Nothing in the menu: the looks are in the build. In Late Night Opening the two pistol guards (third floor, second
floor) hold a USP and two men of the police / transporter squads an SG 552; whoever holds a Zastava holds an MP5,
a bought UMP is a P90, MAC-10 a Steyr TMP, AK-47 an M4A1, M9 Beretta a USP. The shop's name and picture still say
the Dog Days gun. The Guns page does nothing until section 5 is done.

### Live checks, in order (none run)

- **G1 load and look**: `t_guns/M02` in the slot, today's hook. The level loads, the round starts, no
  `guns:` line beyond `guns: on` (the hook must leave the Version 2 file alone). A Beretta guard's pistol is ONE
  gun (a USP), not two in each other. This is the test of section 2: if the pistol is a Beretta, the hide bit or
  the build is wrong; if both show, the bit is not what hides.
- **G2 the player's gun**: buy an M9 Beretta or a UMP; in the hands: USP / P90. Fire,
  reload: the magazine leaves and returns at the Dog Days gun's pivot (parts are on the Dog Days bones).
- **G3 drop and pick up**: kill a SCAR carrier; the gun on the floor is the SG 552; pick it up.
- **G4 far away**: a gun at distance does not vanish or change into the Dog Days model (detail levels).
- **G5 the other four** builds load (`t_guns/M01`, `M03`, `M06`, `RT`); Retomoto: Kane + a Payday 2 mask still
  drawn (wardrobe untouched: byte-identical chunks, but not seen).
- **G6 after the hook change** (section 5): the page switches Start 0 / 1 / 2 and Set 0 / 1 between two loads;
  then during a round (is the bit read per frame or per instance?).
- **G7 memory**: second load of the level in one process with the gun build (.prm + 0.4 MB, .TEX + 8.2 MB).

## 8. The hold: why the MP5 sat wrong, and the fit

**Dog Days holds every gun 10 degrees nose-down against Dead Men's model space, and a little higher.** `kl_guns`
assumed "the same axes, scale and grip place"; the scale is the same (centimetres: the AK-74 is 94.2 long in both
games), the axes are not.

Measured on the three guns both games ship as the same mesh (scratch `icp.py`: trimmed nearest-point fit of the
full-detail vertices, turn about z and shift solved together):

| gun | Dead Men -> Dog Days turn | then shift (x along the barrel, y up, z) | residual |
|---|---|---|---|
| AK-74 (`Rifle_AK74_01` -> `Rifle_AK74`) | -10.00 degrees | (1.04, 1.41, -0.14) | 0.06 |
| Minimi (`Mg_Minimi_SPW_01` -> `Mg_Minimi_SPW`) | -10.00 | (0.68, 1.59, -2.50) | 0.05 |
| SPAS-12 (`Rifle_Spas12_01` -> `Shotgun_Spas12`) | -10.01 | (0.02, 4.20, 0.19) | 0.10 |

The same angle is in the skeletons: `w_bone_frame` rests with rows (0.985, -0.170, ..), (0.170, 0.985, ..) on every
Dog Days gun (9.8 degrees) and with the identity on Dead Men's. Only the HK69 launcher is the Dead Men model
untouched in Dog Days (turn 0.0, residual 0.00). The first pass's own picture shows it (`t_guns/M02_sheet.png`: every
Dog Days gun slopes down to the right, every look lies level) - it was read as "the looks sit on the grips".

So a look put on as it is points 10 degrees UP out of the hands, and its fore-end is 3 to 7.5 cm above where the left
hand is. That is the weird hold. It was true of all six looks, not only the MP5.

**The fit** (`kl_map_guns.refit`, on by default, `--no-fit` = as before): every Dead Men look is turned by -10
degrees about the model's z axis and shifted by the AK-74's (1.04, 1.41, -0.14). Its parts get geometry of their own
(sub table, descriptor, vertex chunk; the index chunk stays shared; the Dead Men model the parts were copied from is
not touched). The rigid vertex is 40 bytes: +0 position, +12 normal, +16 colour, +20 texture coordinate, +28
tangent, +32 binormal (packed B, G, R, 0 as in `re/pd2_klside.md` 1; all three unit length on the gun parts) -
position, normal, tangent and binormal are turned alike. The AK-74 look of the Zastava is a Dog Days model and is
left alone.

- ESTABLISHED: the turn (three guns, one number).
- ASSUMPTION: the shift. Dog Days re-seated each gun (three guns, three shifts, 1 to 4 cm up); the AK-74's is used
  for every look. Finding it per pairing by laying grip on grip was tried and dropped: on the same mesh it returns
  the true shift to 0.01, between two different guns the answer moves by +-1.5 cm with the choice of the zone
  (scratch `seat2.py`) - more than the shifts differ. `seat()` stays as the table's "off" column.
- NOT DONE: the root's bounding box (+0x20, six floats: min, max) is still the Dog Days gun's; the MP5's stock
  reaches 18 cm behind it. Left alone on purpose (the first build drew the MP5 with it as it is). The support-hand
  bone of the gun (`l hand attacher`) is not moved either: it is the Dog Days gun's skeleton, which the stock parts
  need when a hook switches back.
- NOT KNOWN: whether Dog Days places the left hand by the gun's `l hand attacher` or by the handling animation of
  the gun's folder alone. Either way that bone is where the game's makers meant the hand to be.

### The pairings in numbers (`python tools/kl_map_guns.py fit`; stock F01 and M01_FA_A)

Centimetres in the Dog Days gun's space, before -> after the fit. *grip gap* = mean distance of the two guns'
surfaces around the right hand (it cannot reach 0 between different guns); *support hand* = the look's place for it
minus the Dog Days gun's `l hand attacher`, along the barrel and up (Dead Men rests that bone beside the gun, Dog
Days on its axis: the AK-74 of both games gives the constant (0, -1.96, -8.86) used to compare them - along the
barrel the two agree to 0.01); *mag* = magazine centre minus the Dog Days gun's (the look's magazine swings about
the Dog Days gun's magazine bone at a reload); *rear / front* = how far the look reaches past the gun's ends.

| look on gun | grip gap | support hand along the barrel | support hand up | mag | length | rear / front |
|---|---|---|---|---|---|---|
| MP5 on Zastava M85 | 1.2 -> 1.4 | -3.0 -> **-0.8** | 7.5 -> **2.2** | (2.9, 1.3) | x1.11 | 18.2 / -11.3 |
| AK-74 (Dog Days') on Zastava M85 | 1.0 (in place) | 0.6 | -0.2 | (1.8, -0.4) | x1.56 | 20.1 / 13.7 |
| SG 552 on FN SCAR | 0.7 -> 0.9 | -3.6 -> **-1.9** | 3.1 -> **-2.3** | (1.5, 0.3) | x0.79 | -2.9 / -17.4 |
| M4A1 on AK-47 | 1.0 -> 0.9 | -2.7 -> **-0.7** | 6.6 -> **1.1** | (-3.5, -0.8) | x1.02 | 2.0 / -0.1 |
| P90 on UMP (first pairing) | 1.2 -> 1.2 | -15.7 -> **-15.0** | -2.3 -> -5.3 | (-14.0, 12.0) | x0.77 | 1.9 / -16.8 |
| **P90 on Type 05 (new)** | 1.0 -> 1.0 | 0.8 -> **1.5** | -5.0 -> -8.0 | (12.2, 10.1) | x0.99 | 0.7 / -1.1 |
| Steyr TMP on MAC-10 | 0.7 -> 0.9 | one-handed | | (0.3, 2.5) | x1.12 | -0.8 / 3.9 |
| USP on M9 Beretta | 0.6 -> 0.6 | one-handed | | (2.7, 2.1) | x0.88 | -1.6 / -1.3 |

The grip gap does not move with the fit: the turn is about the hand, so the grip stays under it; what the fit
changes is everything away from the hand - the support-hand columns.

Decisions:

- **Five pairings stay.** After the fit the support hand of each two-handed one is within 2 cm of its place along
  the barrel. No other Dog Days gun is clearly better for the SG 552, the M4A1, the Steyr TMP or the USP (the best
  alternatives are within 1.5 cm on every column: SG 552 on the UMP, M4A1 on the SCAR, TMP on the MPi69, USP on the
  Desert Eagle).
- **The P90 moves from the UMP to the Type 05** (`SMG_Type05`, item 27, $24,000 in the shop). On the UMP the left
  hand is 15 cm in front of the P90's fore grip - past its muzzle - and the P90 is three quarters of the UMP's
  length. The Type 05 is a short bullpup of the P90's length (x0.99) with the hand 1.5 cm from the P90's along the
  barrel. It is still the worst of the six: the P90's fore grip is 8 cm lower than the Type 05's hand place (the
  hand will be in the body of the gun) and its magazine lies on top, where no Dog Days gun reloads.
  Consequences: the UMP has no look now; `kl_arms` gives guards the Type 05 (Retomoto 13, M01 4, M06 2), so those
  guards carry P90s; `mkoverlay.py`'s `GUNS_NOTE` still says "P90 on the UMP" (the lead's file).
  `--first-pairs` builds the old table.
- **The MP5 stays on the Zastava** - it is the starting rifle and the owner equips it. By the table the UMP would
  fit it better (same length, magazine 1.8 cm off instead of 3.2, nothing behind the grip), but the Zastava needs a
  look and every Dead Men long gun has a stock the Zastava folds: the MP5 is the shortest of them. Its stock ends
  16 cm behind the hand, where the UMP's does (-16.8), and the UMP has the Zastava's skeleton to the last digit
  (frame (13.38, 1.74, 0.65), `l hand attacher` (41.01, 0.52, 1.58)). ASSUMPTION that the two are shouldered alike;
  if the stock goes through the arm in the game, the answer is the MP5 on the UMP and the Dead Men AK-74
  (`Rifle_AK74_01`, fits its Dog Days twin to 0.1 cm) or nothing on the Zastava.

Pictures: `<work>/build/t_guns2/M02_fit_sheet.png` (`kl_map_guns.py sheet`): per look the Dog Days gun, the look as
`kl_guns` put it (red, level), as built (blue, sloping with the Dog Days gun), and the two over each other; yellow
squares = the right hand (origin) and the Dog Days gun's support-hand place. Before: `<work>/build/t_guns/M02_sheet.png`.

## 9. The sound of a look

A weapon template (`ZFFItemTemplateWeapon`, 60 stored fields by `kl_rtp`) has two sound fields: field 13 (type 70),
0 on all 61 templates, and **field 15 (type 46)**, an offset into the level's `.SND` that names a `#def` object: a
list of 13 slots.

| slot | Zastava `rifle_zastavam85#def` | Type 79 `smg_type79#def` |
|---|---|---|
| 0 dry fire | `common/dryfire/dry_fire_rifle` | `common/dryfire/dry_fire_smg` |
| 1 shot, heard from others | `rifle_zastavam85_shot_npc` (set) | `smg_type79_shot_npc` |
| 2 fly-by | `flyby_01` | the same |
| 4 shot, the player's | `rifle_zastavam85_shot_player` | `smg_type79_shot_player` |
| 5 shell drop | `handguns` | the same |
| 7 pick up ammo | `pick_up_ammo` | the same |
| 8 weapon change | `weaponchange_medium_01` | `weaponchange_big_01` |
| 3, 6, 9..12 | empty | empty |

(The slot names are read off the object names; which slot the game plays when was not traced in the exe.)

Stock Dog Days shares definitions between guns in exactly this way (same bank, another template's offset): the UMP
plays `smg_mac_10`, the UMP SBR `rifle_zastavam85`, the Type 05 `smg_mpi69`, the Type 81 `rifle_ak74`, the SW MP45
`hg_deserteagle`. So re-pointing field 15 is something the game's own data does.

`kl_map_guns.resound` (on by default, `--no-sound` = off): a gun that SHOWS a look of another weapon class than its
own gets field 15 of a stock Dog Days gun of the look's class, the first of `SOUND_OF[class]` the level has (not
silenced, not itself); a look can name its donor. Nothing is added: `.SND`, `.WHD`, `.WAV` are byte for byte the
source build's (checked in `build`), only one `.prp` field per gun changes.

| gun | shows | class of gun / look | sounds like, before | after |
|---|---|---|---|---|
| Zastava M85 | MP5 (`--start=1`, the default) | rifle / SMG | `rifle_zastavam85` | **`smg_type79`** |
| Zastava M85 | AK-74 (`--start=2`) | rifle / rifle, donor named | `rifle_zastavam85` | **`rifle_ak74`** (the look IS Dog Days' AK-74) |
| Zastava M85 | its own model (`--start=0`) | | `rifle_zastavam85` | unchanged |
| FN SCAR | SG 552 | rifle / rifle | `rifle_fn_scar` | unchanged |
| AK-47 | M4A1 | rifle / rifle | `rifle_ak47` | unchanged |
| Type 05 | P90 | SMG / SMG | `smg_mpi69` | unchanged |
| MAC-10 | Steyr TMP | SMG / SMG | `smg_mac_10` | unchanged |
| M9 Beretta | USP | pistol / pistol | `hg_m9beretta` | unchanged |

- The Type 79 is a GUESS among the SMG definitions: it is the two-handed SMG with a definition of its own
  (`smg_mac_10` is already the voice of the UMP and the MAC-10, so of the Steyr TMP; `smg_mpi69` of the Type 05, so
  of the P90). To try another: reorder `SOUND_OF['WT_SUBMACHINEGUN']`.
- NOT changed: the reload sound. The bank has `<gun>/reload/<gun>#seq` objects, but no `.prp` field names one (0
  hits for their offsets in the `.prp` of F01); the reload animation is the Dog Days gun's folder
  (`/Weapon_Handling/Rifle_Zastavam85/Reload/..`) and the sound comes with it. NOT established where from.
- Everyone who fires that template is heard with it (AI heisters with the Zastava), as everyone is seen with the look.
- The sound is baked for the SHOWN look. When `klgun.c` (Version 2) switches the look in the menu, the sound stays
  what the build has: a Zastava switched back to its own model in a `--start=1` build fires like a Type 79. A hook
  could write the template's field in memory; not looked at.

## 10. The grey round (owner, 12:49 on 2026-10-10)

What the owner did, from `<DD>/KLHook.log` (read only) of the process started 12:48:54 (SHIP hook of 07:01:09,
dinput8.dll sha1 c120880a; slot = `rt_guns/retomoto_ai2_guns`, archive 218,697,470 bytes):

| time | line |
|---|---|
| 12:48:54.412 | `guns: on; starting rifle look 2, shop guns Dead Men looks` (KLHook.ini had Start=2 from an earlier session) |
| 12:49:09.7 - 11.3 | `guns: menu set KLGunStart = 1, 2, 1, 0, 1, 2` - left on **2** (AK-74) |
| 12:49:13.250 | session 0x0 -> 0x12; the level loads (76.1 MB block into the reserve, use 1) |
| 12:49:15.617 / 17.298 / 17.305 / 17.609 | 0x15, 0x16, 0x18, **0x19 = the round runs** |
| 12:49:25.658 | 0x19 -> 0x28: session end = the owner backed out, **8.0 s** into the round |
| 12:49:29 - 30 | `KLGunStart = 1, 0, 1` - left on **1** (MP5) |
| 12:49:31.437 - 36.028 | the same level again, round runs; ended by the owner after 58.3 s (12:50:34) |

ESTABLISHED:

- **The hook did nothing to the level for that choice.** No `guns: level ... has N gun(s) with looks` line in the
  whole process: the installed hook takes `Version == 1` only (`klg_level_open`; the DLL holds the string `gun part
  variant` and no `HideBit`), so `klg_f.on` stays 0 and `klg_tick` returns before `klg_apply`. No variant byte, no
  hide bit, no model was written in either round.
- **`Start` reaches nothing else.** In `klgun.c` as installed (commit 2dbcc77; the working tree's copy is being
  changed by another agent today) `klg_start` is read in one place, `klg_tick`'s choice of the group to show.
  `KLG_START_ITEM` (29) is only compared with the file's `Item`; nothing writes a starting item, an inventory or a
  template. The menu option never reaches the game's own option store: `klchar.c`'s private vtable answers
  `KLGunStart` / `KLGunSet` itself (`klc_get`, `klc_set` return before the stock 0x504b40 / 0x472450), `klg_put`
  writes `[Guns] Start=` to KLHook.ini and logs.
- **The page is two toggles and nothing more.** The installed overlay (`<DD>/KLExpansion/Overlay/Patch01.zip`,
  `menu/frontend.xml`): window `KLGuns` = two `ToggleText` (`Option="KLGunStart"` with three texts, `Option=
  "KLGunSet"` with two) and their arrows; `KLGun` appears nowhere else in the file but the button that opens the
  window.
- So the two rounds ran the SAME level bytes with the SAME hook behaviour; both showed the baked MP5. What the owner
  took for "equip the MP5" changed nothing either - the second round was simply fine.
- `Start=2` alone is harmless: the process of 12:09 - 12:36 started with `starting rifle look 2` and played three
  rounds of 359, 299 and 261 s (on the build before the gun looks).
- No fault, no assert, no dump in the grey round; the session states are the normal ones.

What differs between the grey round and the good one, measured:

- It was the **first level load of the process**; the good round was the second.
- State 0x16 lasted 7 ms and 0x18 304 ms. In the other 58 rounds the log holds (every first round start with all
  four state lines, 2026-10-09 12:58 to 2026-10-10 13:11), 0x18 lasts 3 to 31 ms in all but two (146 ms, 321 ms;
  the 321 ms one was a normal round of 307 s). 0x16 varies from 2 ms to 27 s.
- The main loop turned FASTER than in a drawn round: 103,409 `GetForegroundWindow` calls in the 10 s that hold the
  last 2.1 s of the load and the 8 s of the round, against 10,365 in the good round's first 9.4 s and 3,000 - 4,000
  per 10 s later. Less was being drawn - which fits a screen that shows no level - but the window also holds load
  time, so this is an indication, not a count.

NOT ESTABLISHED: what was on the screen and why. No picture exists (`kl_watch` was not running). Two readings that
fit the lines: the level was not drawn during the countdown of that first load (a start-of-round fade or the camera
somewhere empty), or a one-off of the first load with this build. The lead's load check RTG on the same archive
(12:45, TEST hook, first load of its process) reached GO with pictures of the level.

To settle it live (the lead): fresh process, `kl_watch` on, the gun build in the slot; first round with Start=1,
quit, fresh process, first round with Start=2. If grey follows the FIRST round and not the choice, it is not the
guns page. With the Version 2 hook, Start=2 will really switch to the AK-74 - then it is a different test.

## 11. The second builds

`python tools/kl_map_guns.py build <src> <out>` (defaults: `--start=1 --set=1`, fit on, sound on).

All five: `problems: 0`; `kl_map_guns.py check` 0, `kl_impact` 0 on each written folder. The four members the game
reads into one block each, source -> second build (bytes); the chunk table has 69,632 usable entries:

| build (source -> out) | .prm | table entries | .ANM | .fxc | .WAV | .TEX (MB) | archive | audit |
|---|---|---|---|---|---|---|---|---|
| M01 diner (`z_maps/M01` -> `t_guns2/M01`) | 55,088,000 -> 55,917,968 | 50,042 -> 50,254 | 22,061,764 | 17,760,648 | 21,722,704 | 234.5 -> 242.7 | 201,015,949 bytes, sha1 437b17cf | `kl_maps.py audit` PASS (0; 1 known) |
| M02 Late Night Opening (`z_maps/M02` -> `t_guns2/M02`) | 54,619,216 -> 55,449,184 | 58,371 -> 58,583 | 22,202,472 | 17,760,648 | 22,527,568 | 216.1 -> 224.3 | 181,858,558, c0d5b9fe | PASS (0; 6 known) |
| M03 bank (`z_maps/M03` -> `t_guns2/M03`) | 60,469,040 -> 61,299,008 | 62,680 -> 62,892 | 22,202,616 | 17,760,648 | 22,716,752 | 217.8 -> 225.9 | 192,585,100, c01e05eb | PASS (0; 0 known) |
| M06 park (`z_maps/M06` -> `t_guns2/M06`) | 49,585,744 -> 50,415,712 | 46,902 -> 47,114 | 21,642,576 | 17,760,648 | 21,775,744 | 204.6 -> 212.8 | 181,686,561, 5ecac3b6 | PASS (0; 6 known) |
| Retomoto (`rt_ai2/retomoto_ai2` -> `rt_guns2/retomoto_ai2_guns`) | 79,269,328 -> 79,879,056 | 65,119 -> 65,331 | 21,642,904 | 17,760,648 | 27,158,864 | 256.8 -> 264.9 | 218,912,546, eff550aa | no stock systems level (`R09`): the four checkers of section 3, 1 finding on the source, 1 now, 0 new |

- `.ANM`, `.fxc`, `.WAV` unchanged in all five; every one of the 18 files beside the archive (`.WAV`, `.WHD`, the
  `_LS` banks, `.hti`) is byte for byte the source's; the archive members that differ from the source are
  `.MAT .TEX .gms .oct .prm .prp` and no other (so `.SND`, `.ANM`, `.fxc`, `.LOC`, `.HVK` ... are the source's).
- Against the first pass (`t_guns`): `.prm` +0.44 MB (the fitted looks' own vertex chunks: 41 parts, 6 Dead Men
  guns) and 118 more table entries (212 instead of 94 at the end of the table); `.TEX` the same.
- Each build shows: Zastava = MP5, SCAR = SG 552, AK-47 = M4A1, **Type 05 = P90**, MAC-10 = Steyr TMP, M9 Beretta
  = USP; the UMP is itself. The Zastava sounds like `smg_type79` in all five, nothing else changed its sound.
- Placed actors that now show a look: M01 Type 05 x4 (P90), MAC-10 x1; M02 Beretta x2, SCAR x2; M03 Beretta x1,
  SCAR x1; M06 SCAR x1, MAC-10 x1, Type 05 x2; Retomoto Beretta x11, SCAR x2, MAC-10 x1, **Type 05 x13**.
- The P90 on 13 Retomoto guards is the one change here that is a matter of taste (its left-hand fit is the worst of
  the six, section 8). For the lead to choose from, the same build with the first pairings (P90 on the UMP, which
  nobody placed carries): `<work>/build/rt_guns2/retomoto_ai2_guns_p90_on_ump` (`--first-pairs`).
- Pictures: `<work>/build/t_guns2/M02_fit_sheet.png`, `<work>/build/rt_guns2/retomoto_ai2_guns_fit_sheet.png`.

Order among steps, hook and page: as in section 7. For the lead:

- `KLGuns.ini` is still Version 2 with the same keys; `[Gun.4]` is now `SMG_Type05`, `Item=27` (was `SMG_UMP`, 20).
  Comment lines say what is turned and what the Zastava sounds like.
- `mkoverlay.py` `GUNS_NOTE`: "P90 on the UMP" -> "P90 on the Type 05".
- `debug/slot.py` must copy `KLGuns.ini` (already noted in CLAUDE.md).
- `kl_guns.py` is unchanged: `kl_map_guns` hands it its own table for the call (`pairs()`), as before.

### Live checks owed (none run)

- **H1 the hold**: Retomoto second build, today's hook. The MP5 lies in both hands, barrel in line with the forearm,
  left hand on the handguard. Does the stock go through the arm or the chest (section 8, the ASSUMPTION)?
- **H2 the sound**: the starting gun fires with the Type 79's sound, not the Zastava's; reload still sounds (the
  Zastava's).
- **H3 the P90**: a Type 05 guard (Retomoto has 13) or a bought Type 05 shows the P90; where is the left hand?
- **H4 the UMP** is a UMP again; SCAR / AK-47 / MAC-10 / Beretta show SG 552 / M4A1 / Steyr TMP / USP level in the
  hands.
- **H5 the grey round**: the test of section 10.
- G3 (drop / pick up), G4 (far away), G7 (second load) of section 7 still stand.
