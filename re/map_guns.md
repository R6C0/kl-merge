# Gun looks on the map builds (2026-10-10, agent t-guns)

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
