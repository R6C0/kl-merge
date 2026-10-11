# klhud.c - the expansion's HUD, Version 1 (built 2026-10-11, NOT RUN IN THE GAME)

Part of KLHook: `klhook/klhud.c`, included by `klhook.c` after `klbalance.c`; section `[HUD]` of KLHook.ini, OFF
unless `Enable=1`. Spec: `re/hud.md` (the draw code), `re/hud_data.md` (pictures and fonts), the design draft
https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2 . Words: **established** = read in the code; **ASSUMPTION** =
fits the evidence, the deciding code was not read or the thing was never run.

Builds (compile only): `<work>/build/klhook/hud_ship` (SHIP) and `hud_test` (TEST), each with `dinput8.dll`,
`dinput8.dll.sha1` and the sample KLHook.ini (`[HUD] Enable=0`). sha1s in the sha1 files and in the commit message.

## 1. What Version 1 does

- **Crew list** top-left (`CrewX=64, CrewY=36`, `Row=22` px, up to `Rows=8`): every crew record in use, in record
  order, `NAME  $1,234,567` (the cash he carries now: `score+0x150+4*i`, klbot.c's reader). Colour: you
  (`flags & 1 == 0`) blue `0xff6fb3ff`, a traitor (`flags & 2`) amber `0xffe0962e`, dead (status 7) grey
  `0xff6a6a66`, escaped (status 6) green `0xff7fd27a`, else `0xffece8df`. The name is the C string at
  `[[record+0]+8]` - what the stock refresh takes for a row in Arcade (`0x841e50`; klcrew.c writes the same string
  with `Names=1`); a record without one shows `You` / `Heister N`.
- **Money box** right-aligned (`MoneyX=1216`) UNDER the stock round timer (`MoneyY=100`: the timer sits at y 36 with
  a second line at 64 and Version 1 keeps it): `TOTAL $..` (amber), `LOOT $..` (what you carry), `BANKED $..`
  (Total minus Loot), `ROUND N`. Total is computed as the game's `0x807520(rules)` does (established): record 0's
  money if in use + the score object's dwords +0x04..+0x10, +0x18..+0x24, +0x2c and +0x38. The single meanings of
  those dwords are NOT established, so the third row is `BANKED`, not the draft's `Rewards`.
- **Stock block hidden** (`HideStock=1`): byte `+0x25 = 1` of ZFAPlayerListDisplay (`osd+0x10c4`, vtable checked),
  re-applied whenever it reads 0; it draws the top-left name / 'Total score' / 'Round' AND the stock crew list
  (re/hud.md 2.2) - ours replaces both. The round-end lists are other elements and stay. Put back to 0 when the hook
  stands down with the object alive. `ROUND N` lives in our money box so nothing of the hidden block is lost.
- **Drop shadows** (`Shadow=1`): a second text, colour `0x80000000`, at (+2, +2), one layer below - as the timer.
- Drawn only while: an Arcade session with a ZGameRulesHeist object is up (klbot.c `klb_read`), session state
  0x17..0x19 (the stock player list's own window), ZFATimeDisplay (`osd+0x10cc`) enabled and not hidden (the proxy
  for the game's cut-scene hide, since we hide the player list ourselves) and `osd+0x1225` ('HUD off') is 0.
- `Inset=` (default -1): a value in (0, 0.25) is written once per level to `[0xceeebc]` (.data). Not restored.

## 2. How (section 1 and 2 of klhud.c have the detail)

- **Render path**: the OSD at `[0x154da50]` gets a private copy of its 119-slot vtable (RTTI locator kept) with
  slot 55 (`Render(ctx, cam)`, `0x558370`) wrapped - the same trick klchar.c plays on the option object; ONE heap
  dword written, no code byte (a SHIP build writes import slots and data only). The wrapper calls the stock routine,
  repeats its four tests (`[0xce2e9c]`, `[cam+0x14c]` against `osd+0x1220 / +0x121c / +0x1210`) to know that the
  HUD branch (`0x8bf300`) ran, and then draws our texts with the same ctx / cam: `obj->vt[+0x1e8](ctx, cam, &xform,
  &pos)`. **The argument order is (ctx, cam, &xform, &pos)**, read from the timer's Render 0x81e090 (it pushes pos,
  xform, cam, ctx); re/hud.md 3.1 writes the last two the other way round.
- **Texts**: made once per OSD on the main-thread tick through the elements' own path (0x452390): `tmpl =
  0x8ccde0([osd+0xd4c])`, `font = 0x8ccde0([osd+0xd54])`, `parent = 0x598460([tmpl+4])`, `obj = tmpl->vt[+0x19c]
  (parent, 'ZCOB', 0,0,0,0)` (slot must be 0x817810), SetStyle (0x44 left / 0x12 right-aligned), SetColour,
  SetFont, SetLayer (`Layer=13`, shadows 12), SetText. 24 objects (12 rows x shadow + text). The first bytes of
  0x8ccde0, 0x598460, 0x817810, 0x896e50, 0x5a6d40 and six ZCHAROBJ vtable entries are compared first.
- **Threads**: the tick (main loop, `klh_tick(1)`) reads the round, composes the strings and calls SetText /
  SetColour only when a row changed, under a critical section; the render wrapper (whichever thread the renderer
  uses: not established) TRIES the section and skips the frame when the tick holds it - it never waits, so it cannot
  deadlock against an engine lock. The fallback thread (`[KLHook] Tick=0`) does nothing here (said once).
- **Lifetime**: a new `[0x154da50]` or a new scene name drops our pointers; the objects are never freed by the hook.
- **Faults**: any failed check logs once and the part stands down for that OSD (texts already made stay with the
  scene; the stock block is shown again).

## 3. Log lines

`hud: on; ...` (init), `hud: osd X now renders through the private vtable ...`, `hud: osd X, 24 texts made
(template, font, parent; ...)`, `hud: stock block hidden (ZFAPlayerListDisplay X +0x25 = 1 ...)`, `hud: osd X is
over (...)`; Log=2: `hud: text N: 'old' -> 'new'` and colour changes. Faults: `hud: ... : no text is made` /
`the HUD stands down for this level` / `the HUD is off`.

## 4. Live checks (owner away; TEST hook `hud_test`, or the SHIP one with Enable=1 in the ini)

- **H0** `[HUD] Enable=0` (as shipped): no `hud:` line at all, the game as before. (The part is not even initialised.)
- **H1** `Enable=1 Log=2`, stock Subway, Arcade: expect in order `hud: on`, `... private vtable`, `... texts made`,
  `... stock block hidden`, then text lines as money changes. ON SCREEN: top-left the crew list (you blue, the
  stock bots white, names right), the stock name / Total score / Round gone; under the timer TOTAL / LOOT / BANKED /
  ROUND. Watch: are our texts drawn at all (the riskiest assumption, 5 a); is the font the FA one; do the rows
  overlap something; does TOTAL equal what the stock block showed before (compare with HideStock=0 in a second
  run: both blocks visible); does a dead bot go grey, an escaped one green; a full round + score page + a second
  round in the same process (a new OSD: `is over` then `texts made` again); Quit to the menu and back.
- **H2** on a grafted map (the tab's Withdrawal with bots): the same, with seven bots and a traitor (klbot
  Backstab=100 for amber); money up to $800,000 fits the row.
- **H3** `HideStock=0`: both blocks drawn, nothing hidden. `Crew=0` / `Money=0`: one block each.
- Any `CRASH` in the render wrapper (callers 0x5583c6 missing; our DLL in the stack) = stop, the dump says which call.

## 5. ASSUMPTIONS (in the order they could bite)

a. A ZCHAROBJ made by the hook at run time through `+0x19c` (mid-level, not at the OSD's Init) is drawable with
   `Draw(ctx, cam, &xform, &pos)` from inside slot 55 like the elements' own texts - i.e. the create-child needs
   nothing else (no registration with the scene's draw lists, no second init) and the text mesh built by SetText is
   complete. Never run.
b. The scene owns and frees those objects with the level (re/hud.md 6.4). If not, 24 small objects leak per level.
c. Calling SetText / SetColour on the main-thread tick while the renderer may draw the same object on another thread
   is what the stock elements do too (Tick sets texts, Render draws), so it is taken to be fenced by the engine.
d. Style byte 0x12 right-aligns at the given x (the timer at x 1216 does), 0x44 left-aligns; the exact meaning of
   the bytes is not established (re/hud.md 7).
e. `+0xd4c` is the template REF and `+0xd54` the FA font REF (re/hud.md's note on [0]/[1]); both are checked by
   vtable (ZCHAROBJ) and by 'a vtable in .rdata' (the font) before use.
f. The private vtable: nothing in the game compares `[osd]` with the stock vtable address (klchar.c's precedent
   held live on the option object); the destructor runs through our copy's unchanged slot 0.
g. ZFATimeDisplay's +0x24 / +0x25 are a faithful proxy for 'the FA set is shown' (0x75f780 hides it with the player
   list; established) - a state where the game hides only the player list would leave ours drawn.
h. Writing the vtable dword and the hide byte from the main thread while the renderer reads them: single aligned
   dword / byte writes.

## 6. Left out of Version 1

Plates (UI_White tinted) behind the blocks: DrawChunk's 0x34-byte descriptor and the scaled transform are not
established in detail (re/hud.md 3.2) and a wrong one is a crash in the renderer. Strike-through / translucent dead
rows (SetColour keeps the alpha). Moving the stock timer or any other element. The ammo panel. FA online
(klb_read is Arcade only). Localised labels (TOTAL / LOOT / BANKED / ROUND are English constants, not .LOC keys).
