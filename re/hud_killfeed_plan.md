# Kill lines ("POLICE -$5000" + skull) and the grey "$" loot marker in the new look - PLAN (cloud session, 2026-10-12)

No code, nothing built, baked or run (2026-10-23: step 0's bake option exists offline, section 2; still nothing run). Facts are from re/hud.md 2.2, re/hud_popup.md 3, re/hud_data.md 2; everything else is marked GUESS.

## 1. Which element draws what

| on screen | element (re/) | established | not established |
|---|---|---|---|
| the kill / money line ('POLICE -$5000', 'You killed a criminal. $0', the traitor mark) | **ZHeistPointsPopupDisplay** `[osd+0x10b8]`, vtable 0xbbde64, 14 slots, font d50 | text `+0x28` / shadow `+0x2c` (style 0x14, layers 0xf / 0xe, Init 0x5ab8b0); place (640, 270) from Update 0x635420; end time float `+0x30` (game clock / 1024); a queue from `+0x34`; setter 0x433140(elem, text); texts from `AllLevels/Interface/Online/Kill/` + key with the reward (0x4ae130; Heist slot 16 0x485740 -> 0x485b7b), the traitor fine 0x6706b0 / 0x670941, Heist slot 129's 0x8fb200. **Render 0x549480 moves and fades the pair in the call**: offset `(t, 30 t)`, `t = (clock/1024 - end) / 1.5`, alpha `2 t * 255` while `t < 0.5`, through the text's `vt[+0x218]` (re/hud_popup.md 3) | Tick slot number / address; whether the Render draws any picture |
| the SKULL beside it | NOT established. Candidates: (a) ZHitEnemyDisplay `[osd+0x1120]` (vtable 0xbbea00, 'hit marker') with the KillEnemy pictures in 127..160 ('HitEnemy / KillEnemy (+Shotgun)'); (b) the small icon 178 'Kill' (32 px, `UI_KL2_Small_Icons_01`) drawn by the points pop-up itself | re/hud_data.md 2 lists the pictures | which element, which slot |
| the grey "$" over loot | NOT established. Candidates: ZPointOfInterestDisplay `[osd+0x10e4]` (vtable 0xbbe77c, font d54; re/hud_names.md: 'loot / escape markers, not looked at in depth') or ZActionMarkerDisplay `[osd+0x1090]` (0xbbdba4); pictures 52 / 53 (Loot 128, Money 128), 172 (Money, an escape-marker icon), 175 (small Money) | the picture list | which element, which slot, whether it tints the picture (grey = the picture or a tint?) |

## 2. Step 0: identify by DATA, not by code (local, one test bake + one run)

A test-only bake option for tools/kl_hud.py, e.g. `--mark-slots 52,53,127-160,172,175,178`: each listed HUD picture repainted as a flat
colour with its slot number written large in it (same id, same size, same format - the rule of re/hud_data.md 2: 'a restyle of the stock
elements' ART is a .TEX record swap by id'). One run on the bank with a kill and a loot pick-up, pictures every 1 s: the number on the
skull and on the "$" names the slot. No hook change, no element read. This is a test archive only - never for the owner's tab.
(GUESS: the KillEnemy picture is the skull and 172 or 175 the "$"; the run decides.)

DONE offline 2026-10-23 (cloud, no game files, nothing run): `kl_hud.mark_slots` / `stamp_pixels` / `apply_marks`. It keeps the stock
picture and stamps the slot number in its top-left corner (an ink box, coral edge, chalk 3 x 5 digits; 2 px strokes on a 32 or 64 px
picture, 4 on 128, 9 on 256; a texture that sits in two slots, as 109 / 193, gets both numbers stacked), decoded from DXT1 / DXT3 /
DXT5 / ABGR (kl_hud_marks.decode, DXT3 added) and written back as an ABGR record of the same size under the same id, the plate bake's
record shape. Test: `python tools/kl_hud_marks_test.py` (synthetic .TEX, 52 checks: stamped in the corner, nothing else in the picture
changed, unlisted textures and record words byte-identical, the step a no-op when the flag is off, the CLI refusals).

How to run (the bank build the owner's tab was baked from, i.e. the `all --look deadmen` input):
```
python tools\kl_hud.py all <build> <work>\build\hud_K1_TEST --look deadmen --test-bake --mark-slots
python tools\kl_hud.py all <build> <work>\build\hud_K1_TEST --look deadmen --test-bake --mark-slots 52-56,127-160,170-179
```
Without a list every slot of the 200-entry list is stamped (the extras 111..118 too), which is the better first run since the
candidates above are guesses. Guards: `--mark-slots` needs `--test-bake` AND an output folder whose name contains TEST, else the
tool stops before it writes anything; `check:` prints FAIL with 'TEST BAKE with slot numbers stamped' on purpose, so the install
habit ('check must PASS') stops it too; the folder gets `TEST_BAKE_mark_slots.txt` (slot -> texture id -> stock name, the key for
reading the shots). The plain bake (no flags, kl_stock_mod / kl_graft call it that way) does not go through the step.
What a picture drawn much smaller than its texture (the 12 px lives skulls in the list) shows is a smudge: read the kill line's
skull, drawn larger, and zoom the shot. Install into the F01 test slot only, as any other test archive.

## 3. The "$" loot marker: art only (recommended)

Once the slot is known, restyle it in the normal bake (`kl_hud.py all --look deadmen`): the draft's loot language = the faded green
dollar of the loot ring (picture 116: green hi, brush-cut) on a small dark disc, light wear only. Same id, same size, power of two,
aspect kept. If the element TINTS the picture grey (desc record `rec[9]`, as klu_pic writes the tint), bake it in chalk / green
lighter than wanted and judge the tinted result in the run; only if the tint makes it unreadable, wrap the element (section 4 pattern)
to change `rec[9]` for its call - a second step, not planned.
Cost: none at run time; the bake grows by nothing (same texture). Risk class: data only.

## 4. The kill line: wrap ZHeistPointsPopupDisplay's Render (pattern of klhud_popup.c / klhud_escape.c)

New part `klhud_kill.c` (`[HUD] KillLines=0` default; Draft does NOT switch it on before a live check):
1. **Wrap** (main thread): the element at `[osd+0x10b8]` must show vtable 0xbbde64; copy 14 slots + RTTI (`klh_rd` of `0xbbde64 - 4`), check
   slot 2 == 0x549480 and its first code bytes (`klu_same_code`; the bytes to be read locally), write the element's vtable pointer to the copy
   with `klh_data` (one heap dword). Retry 3 s, then refuse for the OSD (board2's rule). Forget on OSD / rules change.
2. **In the wrapper** (render thread, `klu_draw_on` and the clock element wrapped, i.e. state 0x19 - kills happen there):
   - read the text object `+0x28` (vtable must be ZCHAROBJ's) and its string, and classify: police kill (a '-' amount), crew / civilian,
     a '+$' reward, the traitor mark. Classification by text is the only way (the setter passes the finished string, as for the
     announcements). klhud_popup.c already does this for its traitor message: `klpu_str` reads a string and, once a level on the game
     thread, the level's own text of the message comes through the game's lookup (klhud_popup.c, the routine at its line ~423) - the same
     lookup for the `Online/Kill/*` keys gives the prefixes to match (the key names to be listed locally from the level's .LOC).
   - colour: police / penalty = coral 0xfff0475a, reward = green hi, traitor = orange; set with the object's own SetColour (+0x20c =
     0x8a0a30) and put back after the call (klhud_popup.c's `klpu_dirty` discipline: the put-back does not depend on the part's state).
     The stock Render then applies ITS alpha fade with `vt[+0x218]` on top - so ours keeps the fade and the drift for free.
   - font: the draft's quiet size = the NAMES role (H2, cap 11) for the text, via SetFont (+0x23c) as klhud_popup.c does, put back after.
   - optional bar (`KillBar=1`, GUESS whether wanted): a dry-brush underline (picture 112, chalk at the text's alpha) under the line.
     To follow the stock drift the bar must use the SAME `t`: compute it from `+0x30` and the game clock exactly as 0x549480 does, place
     `(640 + t, 270 + 30 t + cap + 3)`, alpha `2 t * 255` clipped - pictures through `klu_pic` borrowing the clock element (klpu_clock
     pattern). Off by default: the owner's "quiet" rule argues for colour + face only.
   - shadow: kept (it reads on bright walls); alpha follows the stock.
   - the stock Render is ALWAYS called (nothing replaced), so any failure = the stock line in our colour or in stock colour.
3. **Skull**: once step 0 names it - if it is a picture of the level (KillEnemy / 178), restyle it in the bake (coral brush skull matching
   the scoreboard's lives skulls, 178 is ALREADY used there as the lives icon: a repaint of 178 changes both, which is the consistent
   choice). No hook code.

Never touched: `[osd+0x10fc]` (kldown.c's knock-down prompt), the announcement element (klhud_popup.c's), the hit-direction / splatter
elements (re/hud_audit.md lists the red discs as a separate candidate).

## 5. Risks

1. String classification: localised strings; the owner plays English (GUESS that the .LOC is the English one in every map we build).
   A line not recognised keeps the stock colour.
2. SetFont on the points pop-up's text: proven on the announcement text (klhud_popup.c), not on this one - the same class (ZCHAROBJ).
3. The queue at `+0x34`: several kills in a row - the element shows one line at a time (GUESS from 'a queue'); the wrapper only acts
   on the line being drawn, so nothing to manage.
4. Render thread: no system call, no wait on a lock (TryEnter only), as every HUD part.

## 6. Live checks (local, owner away; the bank)

- K1 (step 0): the `--mark-slots` test archive (section 2, the first command: every slot stamped); kill a policeman, kill a civilian,
  pick up loot near a marker; pictures every 1 s. What to look for in the shots: (a) the number in the corner of the skull beside
  'POLICE -$5000' (expected 178 'Kill' or one of 127..160 KillEnemy; a number from 173..179 means the small-icons sheet); (b) the
  number on the grey "$" over a dropped bag and over the loot the marker points at (candidates 52 / 53 / 54, 172, 175; which of 53 / 54
  is the bag marker is open, tools/kl_hud_marks.py); (c) whether the skull or the "$" shows NO number: then it is not a picture of the 200
  list at all (a font page-1 glyph, re/hud_data.md 3, or drawn by the element from another texture) and step 3 of section 4 becomes a
  hook job. Also note the number on the lives skulls in the crew list (178 expected: a repaint of 178 then changes both). Write the
  three numbers into section 1's table and delete the test folder.
  Owner: the hud_K1_TEST archive must NOT be installed except for this one check, and never into the owner's tab; it is a test
  bake with numbers painted over every HUD picture, its `check:` says FAIL by design, and `tools/RESTORE Dog Days originals.bat` or
  the normal bake puts the F01 slot back.
- K2: `KillLines=1`, normal archive: the police line coral in the names face, drifting and fading as stock; a reward line green; one
  traitor line orange (Tune=1 run); the announcement pop-up unchanged. Log: wrap line, one line per classified message, no stand-down.
- K3: the rebaked "$" and skull in the normal bake (after K1), one round; the owner judges.
