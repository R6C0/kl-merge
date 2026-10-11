# klhud Version 3 (values + weapon + popup wired) and the extras fix - adversarial review (2026-10-11)

Read line by line from the working tree: klhook/klhud.c (1108 lines), klhud_weapon.c (621), klhud_popup.c (538), klhud_values.c (622),
klhook.c wiring (includes at 583-585, ticks 638-639, inits 816-817), tools/kl_hud.py add_extras / hud_slots, re/hud_layout.md.
Checked against kl2.exe with debug/dasm.py + debug/kl.py: callee stack cleanup of every called routine, the vtable length of
every wrapped element, DrawChunk, the picture-slot loader 0x5e3810, the announcement lookup call site 0x67efb2. Nothing was run
in the game; no file of the repo was changed except this one.

## Verdict

ACCEPT WITH FIXES for the TEST checks A0 .. K1 on the bank (hook hud_v6_test, Log=2): I found no unguarded dereference in a
render-slot path, no stack imbalance, no vtable overrun, no text/picture overflow, nothing touching osd+0x10fc, and nothing that is
active on a stock level or outside Arcade. The extras fix is right: the hook will find slots 111..118 in hud_x2 builds.
NOT yet ready as "the draft": with Draft=1 the screen differs from the agreed draft in about twenty numbers (section 4), the two
biggest being a 31 px horizontal shift of everything and a 24 px row pitch against the draft's 30. Do not put Draft=1 into the
owner's SHIP ini until M1 and M2 below are done and checks Q1 / R1 / K1 have been looked at.

## MUST (before the owner sees Draft=1)

M1. Draft=1 does not set any position, so every element sits on the game's inset (0.05 -> 64 px / 36 px), not on the draft's margins.
    Evidence: klu_layout (klhud.c 462-496) takes cx = 1280 x inset = 64, mx = 1280 - 64 = 1216, cy = 36; hud_layout.md has the crew
    list at left 33, top 38, the right edge at 1247, the weapon dial centre at (1177, 598). Result: crew list +31 px right, the
    watch / escape dial / money box / round line -31 px left (watch centre 1181 against 1212, escape dial 1106 against 1137),
    weapon dial centre x 1145.5 against 1177. Fix: make Draft=1 default CrewX=33 CrewY=38 MoneyX=1247 and WeaponX=1177 (the keys exist; a
    set key still wins). Do NOT use Inset: x and y margins differ in the draft (2.6 % / 5.3 %) and Inset moves the game's own elements.
M2. Row geometry: klu.row defaults to 24 (klhud.c 1100), the draft's pitch is 30 and its row box is 219 x 28. With 8 rows the list is
    192 px high instead of 240, blocks are 24 high instead of 28, names at x 70 / y 66 + 24 i against (41, 72 + 30 i), cash right edge
    at 269 against 236 (draft: right edge - 8; code: - 6). Fix: under Draft=1 default Row=30, block height 28, name x = left + 8,
    cash x = right - 8, strike (name width + 12) x 4 (needs the name width estimate kluv_skull_x already has).
M3. The stock clock's escape line and vehicle icon are still drawn while the orange escape dial stands. Evidence: re/hud.md 376-380
    (ZFATimeDisplay::Render 0x81e090 draws the escape pair and the car / chopper icon whenever byte elem+0xbc is not 0); only
    klu_draw_stock (Draw=2) ever zeroes that byte; klu_clock_face / klu_render_elem do not. With Dials=1 and a waiting vehicle the
    player gets the stock "escape" text under the clock plus a second icon beside our dial. Not a crash. Fix: in klu_render_elem,
    when klu.dials && klu_draw_on, write elem+0xbc = 0 before the stock Render and restore it after (heap byte, same pattern as
    klu_draw_stock 297-299).

## SHOULD

S1. klwd_reset (klhud_weapon.c 600-604) memsets klwd_r WITHOUT klu_cs; klu_reset (klhud.c 887-896) calls it before EnterCriticalSection.
    The render slot klwd_render_elem holds klu_cs while it walks klwd_r.q[]. If the render thread is inside that loop when a
    round or level ends, it can draw one gun picture from a half-zeroed record (zero size or handle: nothing visible, no crash
    because the handle is tested first). Move klwd_reset inside the lock (after EnterCriticalSection in klu_reset).
S2. klwd_render_elem, lock busy (klhud_weapon.c 270): returns 0 having drawn neither the stock panel nor ours, and klu_draw_ours
    skips the whole HUD in that frame too. The tick holds klu_cs for the whole compose (klb_read, loot scan, klwd_read, SetText calls),
    so every ~100 ms the HUD can blink for a frame. Count is logged (lock busy, Log=2); judge in W1. If it is visible, build the
    queue in the tick off-lock and swap a pointer under the lock.
S3. Popup swap race (klhud_popup.c 342, 351): the stock Render is called with [elem+0x30] = -1.0. If the announcement element's
    Tick (slot 5, clears the text when the clock has passed [+0x30]) runs on another thread inside that window it clears the message
    early. Probability is tiny; which thread runs Render is still "suspected" (re/hud.md 7). Same family: SetColour / SetAlpha from
    the render slot on the announcement and clock texts while the main thread may SetText the same object. The clock precedent
    (H1l) ran; the announcement has not. Watch Q2 for a message that vanishes early.
S4. No bound on the instance array: DrawChunk ends with [ctx+8][[ctx+4]++] = inst and no capacity test (0x842ec7-0x842ed4). The array
    lives in the stack frame of 0x678da0 (0x44c70 bytes; array near esp+0x26a80), so it is large, but I could not read its size.
    Worst case per frame with everything on: pictures at most 12 (crew) + 5 (bar) + 57 (watch + escape dial) + 35 (weapon) = 109
    queued (+14 with Grid) against KLU_NPIC 224, plus 3 gun pictures, popup <= 5, loot ring 23; texts 28 made, <= 56 draws, each one
    DrawChunk per glyph run (count 7 seen for a short string) = a few hundred. Add one Log=2 line with the largest [ctx+4] seen
    after the HUD draws, and look at it in A1 / W1 / Q1 / R1.
S5. Round line colour: klu_layout never sets KLU_T_ROUND coral (all texts start chalk, 473); the draft's round line is coral.
S6. Lives default is 1 even without Draft: with only Enable=1 the round line gains "LIVES n" when picture 178 was not prepared
    (Plates=0 Dials=0 Weapon=0 never run klu_pic_prep). The integrator's check A0 "looks like Version 2" will not hold. Either say so
    in re/hud_hook.md 10.4 or default Lives to 0 without Draft.
S7. Draft=1 on a level without the extras falls back silently (plain bars, no rings, no dials, no weapon dial); the stock player list
    is still hidden (HideStock) and the stock ammo panel remains. Acceptable, but then the screen is neither stock nor the draft.
    Print one "hud: draft: level has no extras" line.
S8. hud_x2/DM03 and hud_x2/F01 contain only the .zip (no .WHD/.WAV/.ini/.hti). A test must copy the support files from hud_x/DM03
    (the zip differs only in the HUD list, the .TEX and the fonts). Only DM03 and F01 exist; the five installed maps (DM01 DM02
    DM03 DM06 DM09) each need their archive rebuilt with the new kl_hud.py before Draft=1 has anything to draw rings with.
S9. Per round the HUD makes a new set of ~56 ZCHAROBJ (28 texts + shadows) on the same OSD and never frees them (klu_reset memsets
    klu_r; "the scene owns them"). Ten Arcade rounds in one level = ~560 objects. Small against the 2 GB address-space problem the
    project knows, but unbounded; keep the made objects with the OSD pointer and reuse them when the OSD is the same.

## NOTE

N1. Crash audit, all clear. Stack cleanup: 0x45d6e0 ret 8 (this, float*, 0) matches the fastcall typedef; 0x639700 ret 4, 0x8a0a30
    ret 4, 0x896e50 ret 4, 0x468430 ret 8, 0x5ec380 ret 8, 0x4895b0 ret 8, 0x81e090 ret 8, 0x5a3e90 ret 8, 0x5a6d40 ret 0x10,
    0x842d00 ret 0x1c: all agree with the typedefs. 0x67efb2 is a call SITE; the game does mov ecx,[loc]; call [[ecx]] with pushes
    0, "FA_Become_Traitor", "AllLevels/Interface/Online/Announcements": the hook's call is the same shape (callee's own ret not
    read; it is the game's lookup, 3 args by the site).
N2. Vtable sizes, read in the exe: ZFATimeDisplay 0xbbdfec, ZWeaponDisplay 0xbbe8c0: 11 slots then the next class's RTTI (copy of 12
    dwords is complete). ZFAAnnouncementDisplay 0xbbdd34: 12 slots (slot 11 = 0x63d590, slot 12 = 0) and klhud_popup copies 12 slots
    + RTTI = right. No element wrapped by two parts: clock (klhud), ammo panel (weapon), announcements (popup); the player list
    is only hidden by byte, never wrapped; ZMiniGameButtonMashingDisplay at osd+0x10fc appears in klhud files only in a comment.
    The return value of a wrapped Render is ignored by the element loop (0x8bf5fb call edx, then inc ebx), so returning 0 is safe.
N3. Gating is correct: klu_tick allows only klx_level_verdict == 2 (or Stock=1) and an Arcade session (klb_read); weapon and popup
    are reached only through klu_compose / klu_r.made, so a stock level never gets a private vtable. A private vtable lives on a
    heap element of one level; the next level's element has the stock vtable and is re-wrapped only if allowed.
N4. Restoration: every exit that does not draw goes through klu_stand_down (hide byte back, klwd_draw_on = 0 = the stock ammo panel
    again at once); the colour / alpha of the announcement texts are put back by the render slot itself (klpu_dirty, statics not
    cleared by klpu_forget). The stock clock's coral colour set in the last minute (klu_clock_face) is NOT put back: a second round
    in the same level may start with a coral clock if our HUD does not draw. Cosmetic.
N5. Picture queue: KLU_NPIC 224, klu_prec has 227 slots (224..226 for PicTest / popup); worst case 109 queued, klu_addpic drops
    overflow silently. Text slots: KLU_NTEXT = 25 + 18 + 3 = 46; Grid fills exactly its 18; weapon texts are the last three.
N6. klpu_tick, klu_tick, klu_compose each take a full klb_snap (32 records) three times per 100 ms: on the stack of the main thread,
    fine. Loot scan is cached to once a second. Per-frame cost on the render thread is the queue walk (<= ~110 klu_pic calls, each a
    52-byte copy, 0x5a3e90 and DrawChunk) plus two extra SetText calls on the stock clock while the watch shows: small.
N7. The 83-check unit test of klhud_values was not rerun against the wired klhud.c (integrator says so). Do it: kluv_kind and
    kluv_lives now decide rows and skulls.
N8. Unproven and not crash-capable beyond what is guarded: "OF 10" (no compare of n with m in the exe), skull 178 may not take the
    tint, the weapon dial layout, 0x45d6e0 as text size (the call is correct in shape: it compares [this+0x1c] / [+0x20] with the
    floats and calls [vtable+0x1f0]).

## Questions the task asked

- Unguarded dereference in a render-slot path: none. Direct reads are of the element 'this' the game passes, of ctx (a non-null
  argument, vtable compared before use) and of objects whose vtable the tick checked under the lock; popup reads of text objects are
  vtable-checked in the slot itself.
- Hidden element not restored: see N4; the one thing left behind is the clock colour.
- Two private vtables on one element: none (N2).
- Anything touching osd+0x10fc: no.
- Active on a stock level / outside Arcade: no (N3).
- Draft=1 turning on something unproven that can crash without a fall-back: Weapon (skips the stock Render through a private
  vtable, falls back to the stock Render on any failed read or when the game hides the panel), Popups (private vtable on the
  announcement element, one float of it swapped for one call and restored by compare-and-swap, SetColour / SetAlpha from the render
  slot), LootRing (draws from the announcement slot, all reads checked). Each has a pass-through or put-back; the only calls into the
  game from the render thread are SetColour / SetAlpha on game text objects (clock precedent ran live) and DrawChunk. The residual risk is
  S3, a race, not a bad address.

## 4. Where the result will differ from the draft (draft number from re/hud_layout.md vs the code at Draft=1, game inset 0.05)

| element | draft | code |
|---|---|---|
| crew list left / top | 33 / 38 | 64 / 36 (M1) |
| row pitch / row box | 30 / 219 x 28 | 24 / 219 x 24 (M2) |
| name x / y | 41 / 72 + 30 i | 70 / 66 + 24 i |
| cash right edge | 236 | 269 |
| count "n / 8" right edge | 244 | 275 |
| rule under the label | pic 112, 211 x 5, centre y 60 | pic 181 (UI_White), 211 x 3, top y 58 |
| dead strike | pic 112, (name width + 12) x 4, centred on the name | pic 112, 131 x 8 (0.62 x 211), starts at left + 2, any name length |
| traitor tag | "TRAITOR" in the label font | appended to the name in the same font and ink |
| font sizes | H1 total / timer, H2 names / values, H3 labels | one size for all (TotalFont=0 default) |
| watch centre | (1212, 66) | (1181, 66) |
| watch in the last minute | dial gone, "mm:ss" right at (1247, 44), H1, coral | stock clock text stays at the stock place (1216, 36), stock size, recoloured coral |
| escape dial centre | (1137, 71) | (1106, 71); stock escape line + icon also drawn (M3) |
| round line | right (1247, 106), coral | right (1216, 108), chalk (S5) |
| money block top | 123 (TOTAL value, H1) | 136 with Dials (36 + 100), right edge 1216 |
| money labels left | 1036 | 1005 |
| loot bar | frame pic 117 centre (1141, 163) 211 x 12, fill pic 111 | four 1 px bars of 181, 211 x 8 at y 162, fill pic 181 211 x f by 12 high (overshoots the frame 2 px each side) |
| LOOT / REWARDS y | 178 / 204 labels, 174 / 200 values | 176 / 200 |
| weapon dial centre | (1177, 598) | (1145.5, 598) |
| weapon label | centre (1177, 684) | top at cy + 78 = 676, centred |
| pop-up y | centre 520 | the game's own 480 (text top), bar centred on the text; PopupY default -1 |
| pop-up bar | pic 111, text + 62 x 34 | pic 111, text + 62 x (text height + 12) - 34 only if the text is 22 high |
| loot ring | r 26, disc 40, ring 40, dollar 34 | same numbers; centred 64 above the use-action prompt |
| skulls | 12 x 12 from x 33 + name width + 8 | 12 x 12, name width ESTIMATED at 9 px a character |

Matches (checked): watch ring 24 dabs 9 x 11 r 29, hand 5 + hub, disc 69; escape ring 24 dabs 7 x 9 r 23, icon 30, disc 55; weapon
disc 141, 32 dabs 12 x 16 r 62, counts at (cx - 7, cy - 32) and (cx - 5, cy + 20), pictures 64 at (+28, -26) and 36 at (+21, +24),
divider 87 x 2 at cy + 2; all colours; loot ring numbers; labels TOTAL / LOOT / REWARDS in coral; label 'DEAD MEN' coral; money width 211.

## The extras fix (tools/kl_hud.py, re/hud_extras.md)

Diagnosis confirmed on the files: hud_slots of the old hud_x/DM03 has 183 entries and slots 111..118 absent while the .TEX holds
3000..3007 (the earlier add_extras edited Prp.tokens, which serialize() ignores). hud_x2/DM03 and hud_x2/F01 now read 111..118 =
3000..3007, 170 / 171 / 178 / 181 = 1089 / 1090 / 1097 / 1100 (DM03) and 1167 / 1168 / 1175 / 1178 (F01), 191 entries, and all eight
textures are in the .TEX. The loader agrees: 0x5e3810 walks all 200 entries at [osd+0xd68], a zero id is skipped, a slot with no row in
the 0xcee058 table gets flags 0 and type 5 (lea edi,[eax+5]), then calls the texture loader vtable+0x104 with (id, flags | 0x10, 5, 1)
and stores the handle at [osd+0x3ec+12 n]. klu_pic_prep reads exactly that table (el+8) and keeps type 5 handles, so slots 111..118
will be found and the log line should read "8 of the 8 extra pictures". Residual guess (also in the doc): the type-5 default for a slot
without a row has never been exercised by a stock slot. Run P1 with Log=2: it prints slots 108..120.

## Suggested order for the live checks

A0, A1 (skulls, bar, watch, escape dial: look at M3), W1 (log "stock panel calls skipped", lock busy count), Q1 with PopupFrame=1 first,
R1, K1 (down with [Down] Flop=3: the game's own mash bar must show - nothing of the HUD references that element), D0, second round of
the same process, a stock level (nothing of ours should draw). Stop on any caller among klwd_, klpu_, 0x5ec380, 0x4895b0, 0x842d00,
0x45d6e0, 0x639700.
