# Wardrobe: Dead Men player models, any mask, and the heister page

2026-10-09. The owner released stage 2 (player models) and asked for a customisation screen (character and
mask). "Established" = read in kl2.exe or measured on the files as stated; "ASSUMPTION" and "not run" are meant
literally. Sections 1 - 5 describe what the tools build NOW (wardrobe version 2, built offline 2026-10-09 evening);
what ran in the game is the earlier version 1 (section 6, 'Live outcome').

> **LABEL FIX: READY (2026-10-09, agent v-wardrobe).** Hook builds with it: `<work>\build\klhook\test_char` and
> `ship_char` (rebuilt 20:30 with the 24 outfits as well). The fix is in the HOOK (`klchar.c`: slot 10 is not
> wrapped any more). Cause, established in kl2.exe: section 5a. Live check L1: section 6. NOT seen live yet.
>
> **ALL FA OUTFITS: READY, offline** (same hook builds; data `<work>\build\v_wardrobe\`; overlay
> `<work>\build\v_wardrobe\overlay\Overlay\Patch01.zip`). KLWardrobe.ini is now **Version 2**; the hook still reads
> a Version 1 build. What Fragile Alliance had in both games: section 7.

Three parts: data (`tools/kl_chars.py wardrobe`), hook (`klhook/klchar.c`), menu (`klhook/mkoverlay.py`).
Pictures without the game: `tools/kl_view.py`.

## 1. What the player gets

Arcade page -> new button **Heister** -> three rows:

| row | option | values |
|---|---|---|
| Character | KLChar 0..16 | Game default; J.C., Tommy, Pierre, Liam, Jean, Elwood, Bud, Mitchel (Dog Days); Kane, Lynch, Ashkanan, Meldal, Red, Parker, Standen, Hutchison (Dead Men) |
| Mask | KLMask 0..13 | Game option (the stock 'Criminal Masks' switch); No mask; Moustache - J.C.; Black beard - Tommy; Red opera - Pierre; Orange face - Liam; Skull - Jean; Porcelain doll - Elwood; Red and white opera - Bud; Blue opera - Mitchel; **Wolf, Dallas, Chains, Hoxton (Payday 2)** - face plates over the character's own head, 2026-10-10, tools/kl_pd2mask.py, re/pd2_*.md; variant step 14, HEAD_BASE 113, top variant 128 (the byte is compared unsigned) |
| Outfit | KLOutfit 0..23 | Plain clothes / Light vest / Tactical vest / Heavy armour, each also with ', black shirt', and each of those eight with ', dark balaclava' and ', black balaclava' (Dead Men bodies; a Dog Days body has one outfit) |

Any of the 16 bodies with any of the 8 masks or its own face, a Dead Men body in any of its 24 looks. The choice
is kept in KLHook.ini `[Character]` (Char= Mask= Outfit=). Arcade only; online Fragile Alliance is stage 4.
Names and what each look is: section 7.

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

## 3. Data: `python tools/kl_chars.py wardrobe <base> <out folder> [--level=M01_FA_A] [--slot=F01] [--armour=0,1,2,3] [--fix-bones]`

base = a stock level name or a FINISHED BUILD FOLDER (the folder that holds `<X>_Main.zip`): the wardrobe goes on
top of it, and everything else in that folder travels along (the `<X>_Main*` sound files, **KLJoin.ini**,
graft.txt ...). The out folder must be another folder. `--slot` renames (default: the base's own name).
`--armour=0,3` leaves body meshes out (sizes below); `--fix-bones` also repairs the bone-id bytes of the base's own
skeletons (a base grafted before kl_graft called kl_impact: the tool lists such faults as the BASE's and does not
count them).

1. The eight Dead Men heroes join the .prm with their own skeletons (`put()` with picks that have no target:
   converted model, free bone, bone ids - now with the bones' own id bytes, `kl_impact.sync_bone_ids`, so no
   `kl_impact.py fix` afterwards - animation numbers; characters_graft.md), with ALL 24 Dead Men variants.
   Three materials get a darkened copy of their diffuse texture (`TINT`, section 7: the black shirt and the two
   darker balaclavas; 3 textures in the .TEX, nothing in the .prm).
2. Parts: Dog Days variant 2 = mask objects (material `Merc_Masks`) + masked body (the rest, bag and glasses
   included); Dead Men = head (materials head / hair / eyelash / eye / headset / glass) + body.
3. New models, all with the same variant numbers (**KLWardrobe.ini Version 2**; `kl_chars.variant_of`,
   `klchar.c klc_variant`, compared for all 864 cases by the off-game test, section 5b):
   ```
   outfit  = body + 8 * head        body = armour 0..3 + 4 * shirt 0..1, head 0..2   (= Dead Men variant - 1)
   variant = 10 * body + (1 own face | 2 own mask | 2 + m mask of heister m)          1..80
   variant = 81 + 8 * (head - 1) + body      own face with head 1 / 2                 81..96
   ```
   A mask replaces the head, so the head choice exists with the own face only: 96 variants instead of 240, all
   below 128 (the variant is a byte of the mesh object; whether the engine compares it signed was not looked up).
   Version 1 was `10 * outfit + ...` with two outfits; variants 1..10 mean the same in both.
   - Dog Days heister n: a NEW root = the stock objects (1, 2 unchanged) + variants 3..10. The eight heister
     objects and the AI heisters that share their models are re-pointed to it (.gms +0x0c, .prp ZGEOM[4]).
   - Dead Men hero n: its root gets all 96, each with the MONEY BAG of Dog Days heister n (a Dead Men model has
     none), 2 = the mask of heister n. No entity names these roots.
   An object that moves to another skeleton gets its bone runs rewritten by bone NAME. A bone the receiver lacks,
   or has more than 0.3 units elsewhere at rest, becomes its nearest fitting ancestor: a borrowed mask follows
   the head but not the jaw (433 palette entries in F01). Geometry is shared; a copy costs 64 bytes + runs.
4. `KLWardrobe.ini` beside the archive: the sixteen model roots of THIS build, per character Outfits / Bodies /
   Heads, and HeadBase, for the hook.

Checks, all run by the command itself: `check_wardrobe` (every variant at every level of detail, bones inside the
skeleton and inside the low-detail prefix, vertex palette indices inside the palette, no variant above 127),
`check` (materials, textures, shaders, .oct record per root, skeleton tables against the .ANM, now also
`kl_impact.bone_faults` on every skeleton) and `undrawn` (everybody an entity names). Afterwards, separately:
`python tools/kl_impact.py <folder>` and `python tools/kl_chars.py invisible <folder>`.

Builds of 2026-10-09 evening in `<work>\build\v_wardrobe\`, NOT installed, never in the game:

| build | base | .prm | chunks | result |
|---|---|---|---|---|
| `wardrobe_F01` | stock F01, heroes from M01_FA_A | 66.6 -> **84.0 MB** | 24,843 -> 40,352 | problems: 0; kl_impact 0; invisible: 65 people, 65 ok |
| `wardrobe_bank` | the grafted bank (`i_bank`), heroes from M03_FA_A, `--fix-bones` (649 id bytes of the old graft repaired) | 86.6 -> **104.1 MB** | 62,656 -> 78,188 | problems: 0; kl_impact 0; invisible: 36 people, 36 ok |
| (measured, not kept) the bank with `--armour=0,3` | same | 86.6 -> 97.4 MB | 77,880 | 31 faults, all the base's own old bone ids (no --fix-bones in that run) |

**What it costs in the .prm** (measured on `wardrobe_F01`; nothing can be shared further - no two large chunks
of the eight models are byte-identical):

| part | MB |
|---|---|
| the eight Dead Men models with everything | 16.4 |
| - of that, per armour level over the eight heroes: plain clothes / light vest / tactical vest / heavy armour | 3.0 / 2.9 / 3.7 / 4.9 (per hero 0.26 - 0.71) |
| - heads, shirt parts, skeletons (needed whatever the armour) | 3.0 |
| all mask / shirt / head variants of all sixteen (11,818 mesh objects of 64 bytes, bone runs shared) | 1.0 |
| black shirt, dark and black balaclava | 0 (three textures in the .TEX: +3 texture ids) |

So the shirts, the balaclavas and the masks are nearly free and the armour levels are the price: the two middle
levels cost 6.6 MB.

**RISK - the bank at 104.1 MB.** The largest .prm that has loaded is 96.5 MB (run W6, once). The .prm is one
HeapAlloc; crash 0x8e5bbd (re/crash_owner_1009.md) is that allocation failing in a 2 GB process, intermittently, at
60.7 MB already. Nothing offline says where the limit is. If the full bank does not load: rebuild with
`--armour=0,3` (97.4 MB; the vest outfits then show the plain clothes, the menu and the numbering stay) or
`--armour=0` (about 92.5 MB by the table).
Also new and not seen live: a model root with 1080 - 1608 mesh objects (the stock heister has 21 - 24, a Dead Men
hero in its own game 216 - 528, the version 1 roots that ran had 222 - 302).

## 4. Hook: `klhook/klchar.c` (in the SHIP build; data writes, one private vtable, two game calls)

- **Options.** The menu's option object gets a private vtable (antitamper.md 4.4) whose slots 2, 5, 9 answer
  `KLChar` (0..16), `KLMask` (0..9), `KLOutfit` (0..23) and pass every other name to the stock functions (slot 10
  is NOT wrapped: section 5a). The object is rebuilt for every scene; the tick re-installs. Values live in the
  DLL and in KLHook.ini.
- **Body.** Once rules, local player and all eight table entries have stood still for 300 ms: write
  `heroes[slot]` = the chosen model, write the byte rules+0x33d = slot, and if the player does not wear the model
  call slot 137 - the game's own routine, including its swap of the AI heister. Kane takes J.C.'s place in the
  crew, Lynch Tommy's, and so on; the AI heister of that place keeps his Dog Days body.
- **Look.** When `[player+0x50]` is not the variant the choice asks for (`klc_variant`: the formula of section
  3 with the Bodies / Heads of the model the player wears; an outfit the model does not have falls back to its
  first), call 0x88c810(player, variant). A Version 1 KLWardrobe.ini is still read: armour 3 selects its second
  outfit, everything else its first.
- Both calls only from the game's own thread (the SteamAPI_RunCallbacks tick) and only after the first bytes of
  both routines compare equal to the known ones.
- Without KLWardrobe.ini beside the level's archive: Dog Days characters and mask off / own mask still work
  (variants 1 / 2); a Dead Men choice is ignored and logged.

## 5. Menu: `klhook/mkoverlay.py`

Adds the button 'Heister' to the Arcade page (first added row; expansion map pages follow, now 2..4) and the
window `KLHeister`: the story map page's 'Difficulty' row three times, bound to the three options. Texts are
literal, English: 17 characters, 10 masks, 24 outfits (the lists at the top of the HEISTER block; the outfit
words are `kl_chars.outfit_name`'s, compared by script). **The entry counts are the options' ranges** (5a), so
they must stay equal to klchar.c's KLC_NCHAR + 1, KLC_MASKS + 2, KLC_OUTFITS. Checked by script: names unique
and defined, templates exist, entry counts. Without the hook DLL the rows read 0 and drop changes.
For an already transformed wardrobe build, use `python tools/kl_chars.py plates <build> <out>`
(implemented by `tools/kl_add_plates.py`) rather than rerunning `kl_chars.py wardrobe`; the latter
intentionally rejects non-stock model variant sets.
NOT SEEN: whether the longest value text (43 characters, 'Heavy armour, black shirt, black balaclava') fits
between the arrows - the stock Difficulty row has short words only.

## 5a. Why the value texts were empty (run W2), and the fix

Read in kl2.exe (`debug/dasm.py`), every address below seen:

- Option interface slot 10 (0x611be0, called "GetBounds" above) returns `al = 1` for eleven options only (ids
  0x1f and 0x21..0x2c: resolution, refresh rate ... - values that exist at run time only) and `xor al, al`
  (0x611ddb) for every other name, `Difficulty` included.
- The widget's set-up (ZOption, 0x597960) stores that answer: `call [iface+0x28]` at 0x597a14, `mov [widget+0x9b],
  al` at 0x597a19. So +0x9b means **"this option writes its own value text"**, not "bounds valid".
- ZToggleText's text update (vtable 0xbaee74 slot 38 = 0x6712b0; called by Increase / Decrease, slots 41 / 42,
  after slot 37 Set, and at set-up) reads the value through slot 36 (Get) and then:
  - `+0x9b == 0`: returns if value >= number of `<Text>` children (0x6712ed), else takes child [value]'s text
    (0x671351; the index is the VALUE itself, no lower bound is subtracted); a text starting with '%' is used
    from its second character (0x671375 / 0x67138c), anything else goes through the LOC lookup (slot 25);
  - `+0x9b != 0`: takes the text from `0x8b70d0` = `[iface+0x18](name, &string)` = slot 6 (0x6994c0), whose
    switch covers ids 0x21..0x2c and leaves the string EMPTY for any other name;
  - either way the text is handed to the receiver `[widget+0x130]` through its slot 31 (`+0x7c`).
- The first klchar.c wrapped slot 10 and returned 1 for KLChar / KLMask / KLOutfit. So +0x9b was 1, slot 6 was
  asked, knew no KL name, and the receiver was given an empty string - while Get / Set worked, as the log showed.

Not the cause (checked): the markup (same attributes as PlayMenu's Difficulty row), the receivers' type (a plain
`TextBlock`, as stock `DifficultyData`), name shadowing (mkoverlay's check: every KLH_ name is defined once and
first in KLHeister), the '%' texts (handled in the widget itself, no LOC), the text index.

**Fix:** slot 10 is no longer wrapped (klchar.c). The stock function answers 0 for the unknown names, the range is
0 .. children - 1 (0x694500 sets UpperBound as children are added), and the `<Text>` children are shown. The XML's
entry counts are therefore the ranges; `klc_upper[]` in klchar.c must agree with mkoverlay.py's lists.
Proof offline: the reading above (the instructions at 0x597a14 / 0x597a19, 0x6712e2 .. 0x67138c, 0x611ddb and
0x694500 were disassembled again on 2026-10-09 evening and say what is written here). The widget's own routine
was not run off-game (it needs the menu manager, the font and the engine heap; the hook's off-game harness under
the scratchpad's khook folder has no menu), so **only a live look confirms the picture.**

## 5b. Off-game test of klchar.c (run 2026-10-09, PASS)

`chartest.c` (scratchpad `vw\chartest\`; klchar.c compiled as it is against stand-ins for the six klhook.c helpers
it uses): the wrappers Get / Set / IsEnabled answer the three names, clamp to 16 / 9 / 23, write KLHook.ini and
leave other names alone; `klc_level_open` reads the real `v_wardrobe\wardrobe_F01\KLWardrobe.ini` (16 characters,
version 2, HeadBase 81, Kane 8 bodies 3 heads); `klc_variant` equals `kl_chars.variant_of` in 864 cases (both
body kinds, 24 outfits, 10 mask choices, the game's own 1 / 2 kept under KLMask=0 from nine current variants);
a Version 1 file maps as said. `RESULT: PASS (0 faults)`. It does not test the two game calls or anything live.

## 6. The live checks

**To do now, in this order (one variable per run; hook `<work>\build\klhook\test_char`, or `ship_char`):**

- **L1 the labels.** Stock F01 in the slot is enough (no wardrobe needed), overlay
  `<work>\build\v_wardrobe\overlay\Overlay\Patch01.zip` (or the lead's own overlay rebuilt with today's
  mkoverlay.py), ini = `<work>\build\klhook\live\W2.ini` (the run that opened the Heister page), picture
  at the same moment. MUST SHOW: text between the arrows on all three rows - 'Game default' / 'Game option' /
  'Plain clothes' at 0; after the script's Increase messages the names of the values the log reports
  (`menu set KLChar = 2` -> 'Tommy', `KLMask = 3` -> 'Black beard - Tommy', `KLOutfit = 1` -> 'Light vest').
  Also look at: does a long outfit text fit. If the rows are still empty the cause is not slot 10 alone - then
  log `[widget+0x9b]`, `[widget+0x128] - [widget+0x124]` and `[widget+0x130]` of the three ToggleTexts.
- **L2 the new data, small level.** `v_wardrobe\wardrobe_F01` in the slot, `[Character] Char=11 Mask=0 Outfit=19`
  (Ashkanan, heavy armour, black balaclava): log `wardrobe (version 2)`, `look: variant .. -> 92`; picture: a man
  in a grey suit with a black vest and thigh holsters, BLACK balaclava, bag on his back. This one run tests the
  root with 1368 objects, a variant above 80, armour level 3 and the darkened texture.
- **L3 shirt and a middle armour.** `Char=9 Mask=6 Outfit=5` (Kane, light vest, black shirt, the skull): `-> 57`;
  black shirt under the jacket, skull mask.
- **L4 the bank at 104.1 MB.** `v_wardrobe\wardrobe_bank`: does it load (twice: the failure is intermittent). If
  not: `--armour=0,3` and say so in section 3.
- Then the open items of the version 1 runs below: W4 on its own, ragdoll / cover / death in a Dead Men body, the
  choice across a game restart, the SHIP build, a second round.

**The first plan (version 1), kept for the record:**

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

### Live outcome (2026-10-09 18:41-19:11; TEST hook build/klhook/test_char, klauto menu route, Hooks=0)

All on the bone-repaired builds `<work>/build/u_live/wardrobe_F01` and `wardrobe_bank` (`kl_impact.py fix`;
before the repair kl_impact reported 8 and 47 problems). Every run: PASS, 0 asserts, 0 faults.

| run | what | result |
|---|---|---|
| W1 | stock Subway + wardrobe models, no choice | round starts, heisters look as stock |
| W5 | Char=9 (Kane), no mask | **a model no entity names IS drawn**: log `heister table entry 0: model 26141 -> 25831 (Kane)`, `body: ... the player now has 25831`; Kane in his suit with the nose bandage, bag on his back, rifle in hand, walks and turns (research/wardrobe_W5_225s.png) |
| W3L | Char=10 (Lynch), Mask=5 | `look: variant 1 -> 6`; Lynch's suit with a borrowed Dog Days mask (wardrobe_W3L_208s.png). W3 and W5 in one run |
| W2 | overlay + Heister page | sixth Arcade button opens window KLHeister; `character: menu set KLChar = 1, 2`, `KLMask = 1..3`, `KLOutfit = 1`, values kept on re-opening the page. DEFECT: the value text between the arrows is EMPTY on all three rows (wardrobe_W2_60s.png) although the option changes; stock togglers with literal '%' texts exist (VOAspect) and the XML matches the stock PlayMenu rows - cause not found |
| W6 | wardrobe_bank (Dead Men bank, 96.5 MB .prm), Char=10, Outfit=1 | loads; `look: variant 1 -> 11`; Lynch on the bank's plaza at GO (wardrobe_W6_258s.png) |

Not run: W4 as its own run (a Dog Days body by the swap: the same routine as W5 with a model that is
already in the table), ragdoll / cover / death with a Dead Men body, the choice surviving a game restart
(the ini is rewritten by each test run), the SHIP build of this hook (test_char only), a second round.

## 7. What Fragile Alliance had, in both games (measured 2026-10-09)

**Dog Days.** The eight heister models are the same objects in all nine stock FA levels (F01..F09: same object
counts, same vertex data digest per heister) and carry exactly two variants: 1 = face, 2 = own mask. Nothing
else exists for them - no further outfit to add. Variants above 2 exist on other people only (street police 1..4,
security guards and SWAT 1..2; the respawn policeman has 1): the later stage. The masks have no names in the game
(one material `Merc_Masks`, one shared 1024 x 1024 picture); named by look, `research\v_wardrobe\masks.png`:

| KLMask | worn in stock by | look | label |
|---|---|---|---|
| 2 | J.C. | pale face, rosy cheeks, brown moustache | Moustache - J.C. |
| 3 | Tommy | white and black paint, red cheeks, black beard | Black beard - Tommy |
| 4 | Pierre | white with red opera pattern | Red opera - Pierre |
| 5 | Liam | plain orange-red face, frowning | Orange face - Liam |
| 6 | Jean | skull | Skull - Jean |
| 7 | Elwood | white woman's face, small red mouth | Porcelain doll - Elwood |
| 8 | Bud | grey / red / white opera face, open mouth | Red and white opera - Bud |
| 9 | Mitchel | blue / red / yellow opera face | Blue opera - Mitchel |

All are a face plate taped (grey tape) over a black hood: whole heads, as section 2 says.

**Dead Men.** The eight hero models are identical in the four FA maps (`python tools/kl_chars.py looks`: one
digest per hero over objects, materials and vertex data, equal in M01 / M02 / M03 / M06_FA_A). **No per-map
difference, no masked version** (Kane and Lynch show their faces in every variant; the other six wear a
balaclava in every variant). Each carries 24 variants: `variant = 1 + armour + 4 * shirt + 8 * head`.

| part | values | what it is in the files | the game's own words (.LOC loading tips) |
|---|---|---|---|
| armour 0..3 | plain clothes; light vest (plain black vest); tactical vest (pouches, one thigh holster); heavy armour (heavier vest, two thigh holsters) | four body meshes, material Merc_Rank3_8, e.g. Kane 3114 / 3540 / 4464 / 5037 vertices | tip 13: 'The better weapon pack you buy, the better tactical arm...' |
| shirt 0..1 | as painted; black | material playstyle_01a / playstyle_04 on the SAME mesh (609 vertices in plain clothes, 158 under a vest); Parker has no such part | tip 4: 'Traitors spawn with a black shirt in the next round' |
| head 0..2 | as painted; dark; black | material multiplayer_headset01_Rank_01 / 02 / 03: on Kane and Lynch a 12-vertex earpiece, on the six others the balaclava (the whole head; a second, larger mesh at heavy armour, painted darker already) | tip 10: 'Balaclavas show who is leading: the darker it is, the h...' |

**The shirt and head choices are not pictures in Dead Men's files.** playstyle_01a and playstyle_04 are the same
material instance but for the name; headset 01 / 02 / 03 too (02 and 03 differ from 01 in the cull mode only) -
same textures, same constants, compared node by node in M01_FA_A's .MAT. Dead Men's exe must colour them at run
time by material (not looked up where); Dog Days' exe does not, so untouched the 24 variants are drawn as 4.
The wardrobe makes them real with darkened copies of the diffuse texture: black shirt x 0.16, dark balaclava
x 0.50, black balaclava x 0.22. **ASSUMPTION: the three shades** (`kl_chars.TINT`) - Dead Men's own values are not
in its level files; that the result is a black shirt and darker balaclavas is seen in
`research\v_wardrobe\outfits_dm.png` (kl_view now draws the diffuse textures). On Kane and Lynch the head choice
changes the earpiece only: nothing to see.

Names: `AllLevels/Menu/Online/Profile/FragileAllianceRank_01..08` of Dead Men's .LOC = 'Kane, no1 of The7',
'Lynch, Psycho7', 'Ashkanan, no2 of The7', 'Meldal, no3 of The7', 'Red, no4 of The7', 'Parker, no5 of The7',
'Standen, no6 of The7', 'Hutchison, no7 of The7'. **ASSUMPTION: rank n is the model Hero_0n** - true for 01 and 02
by their head materials; nothing in the level files ties 03..08 to a name (no name string, no template).

| KLChar | name | model | body in plain clothes (outfits_dm.png, top to bottom) | objects in the build |
|---|---|---|---|---|
| 9 | Kane | Hero_01 | grey suit, white shirt, face with the nose plaster | 1512 |
| 10 | Lynch | Hero_02 | grey suit, tie, glasses, long hair | 1608 |
| 11 | Ashkanan | Hero_03 | grey suit and tie, balaclava | 1368 |
| 12 | Meldal | Hero_04 | white short-sleeved shirt, tie, balaclava | 1368 |
| 13 | Red | Hero_05 | white long-sleeved shirt, green trousers, balaclava | 1368 |
| 14 | Parker | Hero_06 | green jacket, balaclava (no shirt part) | 1080 |
| 15 | Standen | Hero_07 | blue shirt over white sleeves, balaclava | 1344 |
| 16 | Hutchison | Hero_08 | grey-brown shirt, blue jeans, balaclava | 1272 |

Pictures (`<work>\research\v_wardrobe\`, all from the built files by `tools/kl_view.py`, textured): `masks.png`
(the eight masks, front and side), `outfits_dm.png` (eight rows = Kane .. Hutchison; columns = outfits 0, 1, 2, 3,
4, 7, 8, 16, 11, 19), `wardrobe_F01.png` (all sixteen: face, a borrowed mask, heavy armour with own mask; front and
back, in the test pose), `bank_lynch_looks.png` (the bank build: Lynch variants 1, 34, 76, 96).

Not done: names in the HUD (still the slot's C1..C8), Dead Men bodies or outfits for the AI heisters, voice sets,
online, the police / respawn looks (later stage), other languages for the labels.

## 8. Chunk limit (2026-10-09 21:30; `re/prm_limit.md`)

The full wardrobe adds 15,500 chunks (11,818 of them 64-byte mesh-object copies). kl2.exe's chunk
pointer table has 73,728 slots, shared with the chunks the game makes while it runs, and nothing
tests the count: Retomoto + wardrobe at 80,628 entries wrote over the globals behind the table
(run P4, crash at 0x607280). `kl_chars.put` / `wardrobe` now write every new chunk INTO the index
of a dead chunk of the base (S's removed map: 23,000 - 24,000 free indices in a grafted level) and
only grow the file when those run out; nothing live moves. `--no-reuse` gives the old behaviour.

- Lighten the base first (`kl_graft.py lighten`), then the wardrobe: the wardrobe turns the unused
  dead chunks into stubs, after which trim / slim find nothing to work from.
- The Dead Men roots are named by no entity. Anything that decides "live" from the level's files
  must add `kl_chars.wardrobe_roots(<folder>)` (KLWardrobe.ini), or it treats the eight heroes as
  dead: `kl_graft lighten` on a wardrobe build would empty 15.8 MB of them (lines in prm_limit.md).
- The wardrobe command prints the chunk-table line and fails the build past `kl_impact.CHUNK_SAFE`
  (69,632 entries).
- Builds: `<work>\build\x_chunks\retomoto_wardrobe` (65,119 entries, .prm 77.8 MB) and
  `bank_wardrobe` (62,657, 60.5 MB; `bank_wardrobe_noslim` on a trim-only base). Model roots are
  different numbers from the earlier builds (now 9,000 - 10,300): KLWardrobe.ini beside each archive
  has them, and must be installed with its own archive as before.
