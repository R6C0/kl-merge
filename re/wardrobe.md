# Wardrobe: Dead Men player models, any mask, and the heister page

2026-10-09. The owner released stage 2 (player models) and asked for a customisation screen (character and
mask). Built OFFLINE while live runs were paused: **nothing here has run in the game.** "Established" = read
in kl2.exe or measured on the files as stated; "ASSUMPTION" and "not run" are meant literally.

Three parts: data (`tools/kl_chars.py wardrobe`), hook (`klhook/klchar.c`), menu (`klhook/mkoverlay.py`).
Pictures without the game: `tools/kl_view.py`.

## 1. What the player gets

Arcade page -> new button **Heister** -> three rows:

| row | values |
|---|---|
| Character | Game default; J.C., Tommy, Pierre, Liam, Jean, Elwood, Bud, Mitchel (Dog Days); Kane, Lynch, Dead Men crew 1..6 |
| Mask | Game option (the stock 'Criminal Masks' switch); No mask; Mask of J.C. ... Mask of Mitchel |
| Outfit | Standard; Armoured (Dead Men bodies: the vest of Dead Men's equipment level 3) |

Any of the 16 bodies with any of the 8 masks or its own face. The choice is kept in KLHook.ini `[Character]`.
Arcade only; online Fragile Alliance is stage 4 (section 6).

## 2. Facts the design rests on (kl2.exe build 0490, read 2026-10-09)

- **A model is a number.** `[[entity+4]+0x68]` is the model's chunk index in the level's .prm, resolved through
  the table 0xeac7b0 wherever it is used (0x6ad0db). The loader 0x45f260 fills that table for every chunk whose
  table entry has a non-zero refcount - not only for models an entity names.
- **The game swaps bodies at run time itself.** Every heister object registers its model with the rules object
  (`ZGameRulesHeist` slot 135, 0x5684f0: `heroes[rank] = model` at rules+0x208; callers 0x50a1c0 / 0x627b50 pass
  type `[player+0x273c]`, rank `[player+0x2740]`, model `[[player+4]+0x68]`). Slot 137 (0x8f5e90) gives the local
  player `heroes[byte rules+0x33d]` through 0x783fb0 -> 0x792290 (`[node+0x68] = model`, notify the renderer,
  rebuild) and hands the AI heister that wore it the player's old model. rules = `[[0x168e9e4]+0x54]` while
  `[[0x168e598]+0x5c] == 4`; local player = `[gamedata+0x828+4*(char)[gamedata+0x898]]` (0x660b00).
- **A look is a variant.** Mesh objects carry a variant byte (+0x0f); `[player+0x50]` selects, set by 0x88c810
  (three callers: the two mask routines 0x4b5b20 / 0x822830). Stock heisters have 1 (face) and 2 (own mask).
- **The masks are whole heads** (seen with kl_view): variant 2 of a Dog Days heister is a body without head plus
  a full-head mask, so a mask is not tied to its owner's face. The eight Dog Days and eight Dead Men hero
  skeletons are the same rig (characters_graft.md 4); body bones agree at rest to 0.26 units, face bones differ
  by up to 3.
- **Skinned vertex** (52 bytes; checked on 28,513 + 22,629 + 281,952 vertices): +0 position (model space), +12
  three weights (the fourth is the rest), +24 four bytes = 3 * index into the object's bone palette; the palette
  is the object's bone runs `{12 * count, 12 * first bone}` expanded (+0x38 run count, +0x3c chunk).
- **Low detail.** Objects with LOD mask 0x7c use only the leading bones (skeleton detail words 1..5: 34 / 36);
  LOD 0x01 and 0x02 objects use any bone (733 object x bit pairs of F01; the earlier reading "word[bit]" is wrong
  for bit 1).
- **Menu options.** A `ToggleText` reads and writes its option straight through the option object: slot 36 /
  37 of the widget (0x81ad20 / 0x5cc990) call slot 2 `Get(name, player)` / slot 5 `Set(name, value, player)` of
  `[widget+0xa4]` = ZMercsOptionsInterface (vtable 0xbb7dec, 15 slots; names are plain `char *`). Slots 9 / 10
  = IsEnabled / GetBounds. The other name-taking slots (3, 4, 6, 8) fall through harmlessly for unknown names.

## 3. Data: `python tools/kl_chars.py wardrobe <base> <out folder> [--level=M01_FA_A] [--slot=F01]`

base = a stock level name or a build folder (the folder that holds `<X>_Main.zip`).

1. The eight Dead Men heroes join the .prm with their own skeletons (`put()` with picks that have no target:
   converted model, free bone, bone ids, animation numbers - characters_graft.md), outfits = Dead Men variants
   1 and 4.
2. Parts: Dog Days variant 2 = mask objects (material `Merc_Masks`) + masked body (the rest, bag and glasses
   included); Dead Men = head (materials head / hair / eyelash / eye / headset / glass) + body.
3. New models, all with the same variant numbers:
   `variant = 10 * outfit + (1 own face | 2 own mask | 2 + m mask of heister m)`
   - Dog Days heister n: a NEW root = the stock objects (1, 2 unchanged) + variants 3..10. The eight heister
     objects and the AI heisters that share their models are re-pointed to it (.gms +0x0c, .prp ZGEOM[4]).
   - Dead Men hero n: its root gets variants 1..10 and 11..20 (armoured), each with the MONEY BAG of Dog Days
     heister n (a Dead Men model has none), 2 = the mask of heister n. No entity names these roots.
   An object that moves to another skeleton gets its bone runs rewritten by bone NAME. A bone the receiver lacks,
   or has more than 0.3 units elsewhere at rest, becomes its nearest fitting ancestor: a borrowed mask follows
   the head but not the jaw (433 palette entries in F01). Geometry is shared; a copy costs 64 bytes + runs.
4. `KLWardrobe.ini` beside the archive: the sixteen model roots of THIS build, for the hook.

Checks (`check_wardrobe` + the existing `check`): every variant at every level of detail, bones inside the
skeleton and inside the low-detail prefix, vertex palette indices inside the palette, and everything `check`
tests (materials, textures, shaders, .oct record per root, skeleton tables against the .ANM).

Kept builds (`<work>\build\chars\`), `problems: 0`, NOT installed:

| build | base | .prm |
|---|---|---|
| `wardrobe_F01` | stock F01 | 66.6 -> 76.5 MB, 24,843 -> 30,045 chunks |
| `wardrobe_bank` | the grafted bank (`i_bank`, F07 systems + M03_FA_A), heroes from M03_FA_A | 86.6 -> **96.5 MB** |

RISK: the bank's .prm passes the 90 MB above which kl_graft trims (a 28.9 MB HeapAlloc failed once, crash
0x8e5bbd). Not known whether 96.5 MB loads; dropping the armoured outfit would save about half of the 10 MB.

## 4. Hook: `klhook/klchar.c` (in the SHIP build; data writes, one private vtable, two game calls)

- **Options.** The menu's option object gets a private vtable (antitamper.md 4.4) whose slots 2, 5, 9, 10 answer
  `KLChar` (0..16), `KLMask` (0..9), `KLOutfit` (0..1) and pass every other name to the stock functions. The
  object is rebuilt for every scene; the tick re-installs. Values live in the DLL and in KLHook.ini.
- **Body.** Once rules, local player and all eight table entries have stood still for 300 ms: write
  `heroes[slot]` = the chosen model, write the byte rules+0x33d = slot, and if the player does not wear the model
  call slot 137 - the game's own routine, including its swap of the AI heister. Kane takes J.C.'s place in the
  crew, Lynch Tommy's, and so on; the AI heister of that place keeps his Dog Days body.
- **Look.** When `[player+0x50]` is not the variant the choice asks for, call 0x88c810(player, variant).
- Both calls only from the game's own thread (the SteamAPI_RunCallbacks tick) and only after the first bytes of
  both routines compare equal to the known ones.
- Without KLWardrobe.ini beside the level's archive: Dog Days characters and mask off / own mask still work
  (variants 1 / 2); a Dead Men choice is ignored and logged.

## 5. Menu: `klhook/mkoverlay.py`

Adds the button 'Heister' to the Arcade page (first added row; expansion map pages follow, now 2..4) and the
window `KLHeister`: the story map page's 'Difficulty' row three times, bound to the three options. Texts are
literal, English. Checked by script: names unique and defined, templates exist, entry counts, the window parses
as XML on its own (the stock file as a whole does not pass a strict parser either). Without the hook DLL the
rows read 0 and drop changes.

## 6. Not established - the live checks, in this order (one variable per run)

1. **W1 stock looks unchanged.** `wardrobe_F01` in the slot, ORIGINAL hook: a round as before (the heisters now
   use the new roots; variants 1 / 2 are the stock objects).
2. **W2 options.** New hook + overlay, stock level: the Heister page opens, three rows move, the log shows
   `character: menu set KLChar = n`; values back after a restart. (Private vtable on the option object: not run.)
3. **W3 mask.** KLMask=5 on `wardrobe_F01`, default body: variant 6 is drawn (a variant above 2 on a ZFFPlayer:
   stock uses 1 and 2 on players, up to 6 on actors).
4. **W4 Dog Days body.** KLChar=3: log `body: ... the player now has <root>`; the AI Pierre wears the player's
   former body. (Calling slot 137 a second time: not run. Whether it can run BEFORE the game's own first call
   without harm: the 300 ms settle is a guess.)
5. **W5 Dead Men body.** KLChar=9 (Kane): **a model no entity names is drawn** - the largest unknown. If it is
   not (invisible player, or a fault in the renderer's per-mesh object 0x4aa8d0), the fallback is to give the
   Dead Men roots an entity each, or to put the Dead Men looks into the Dog Days roots as further variants.
   Then: weapon in hand, cover, the bag, ragdoll, armoured outfit, a borrowed mask's collar (the mask's neck
   pokes through shirt collar and tie on the suits - seen in kl_view).
6. **W6 the bank.** `wardrobe_bank`: does a 96.5 MB .prm load.

Also open: the HUD name stays the slot's (C1..C8); AI heisters cannot be given Dead Men bodies from the menu;
voice sets (Dead Men's are not in the level .SND); online (the body follows a session number at 0x74ee10 and a
look would have to be replicated - `m_iUseMask` is a bool); the masks have no names because nobody has seen
their textures (kl_view draws shapes only).
