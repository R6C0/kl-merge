/*
 * klhud.c - the expansion's Fragile Alliance / Arcade HUD, Version 2 (2026-10-11 evening, track V): THE OWNER'S DRAFT
 * https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2 on the draw path that works.
 *   top left   the CREW LIST ('DEAD MEN' + '5 / 8', a painted rule, one row a heister: name, tag, the cash he carries;
 *              own row a chalk block with dark letters, a traitor an orange block, dead faded red and struck through,
 *              escaped grey 'OUT')
 *   top right  under the game's own clock: 'ROUND n  LIVES n', then the MONEY BOX: TOTAL (bright green), a framed bar,
 *              LOOT, REWARDS
 *   kept       the game's clock, escape marker, ammo panel, announcements (the draft keeps them; their look is the level
 *              data's: tools\kl_hud.py --look deadmen)
 *   hidden     the stock top-left block (ZFAPlayerListDisplay: name / 'Total score' / 'Round' and the stock list)
 * Part of KLHook (included by klhook.c after klbot.c and klsteam.c; SHIP and TEST alike). OFF unless [HUD] Enable=1.
 * VERSION 2 HAS NOT RUN IN THE GAME. What IS proven, what is not, the layout and the live checks: re\hud_hook.md.
 *
 * 1. HOW THE GAME DRAWS ITS HUD (re\hud.md 1 - 4, 8, 9; EXE = read in kl2.exe build 0490)
 *    osd = the active ZOnScreenDisplay2 (vtable 0xbbe504). Its render (slot 55 = 0x558370) runs 0x8bf300 for the HUD
 *    camera: every element with +0x24 != 0 and +0x25 == 0 gets Render(ctx, cam) (slot 2); its Tick (slot 5) runs
 *    whatever +0x25 says (re\hud.md 2.3: a hidden element keeps its state up to date). A text is a
 *    ZCHAROBJ (vtable 0xbab45c) made at the element's Init (0x452390): tmpl = 0x8ccde0([osd+0xd4c]), font =
 *    0x8ccde0([osd+0xd54]), parent = 0x598460([tmpl+4]), obj = tmpl->vt[+0x19c](parent, 'ZCOB', 0, 0, 0, 0), then
 *    SetStyle(+0x220) SetColour(+0x20c) SetFont(+0x23c) SetLayer(+0x234) SetText(+0x244), and once a frame
 *    obj->Draw(+0x1e8 = 0x5a6d40)(ctx, cam, &xform9, &pos3): pos3 = (x, y, 0) on the 1280 x 720 virtual screen (origin
 *    top left), xform9 = what 0x7f07a0 writes = {0,0,1, 0,1,0, 1,0,0}. Style 0x12 = right-aligned at x (the clock at
 *    x 1216), 0x44 = left (the player list). A shadow is a second object, colour 0x80000000, at (+2, +2), one layer
 *    below. A picture is ZDrawBufferSimple::DrawChunk (0x842d00) - section 3.
 *
 * 2. THE TWO WAYS A TEXT IS DRAWN HERE (key Draw)
 *    Draw=1 (default)  our own call of obj->Draw with the xform above. Until 16:34 the hook passed {0,0,0, 0,0,0, 1,0,0}
 *                      and every Draw it issued was invisible (runs H1c .. H1n); the owner's probe round measured the
 *                      instance that call made - 0 / 0 / 0.005972 at (-x, -0, 0) against the stock 1.0 / 0.005972 /
 *                      0.005972 at (x, y, 6.0) - which is exactly what the wrong xform gives (re\hud.md 9). THE CALL
 *                      WITH THE RIGHT XFORM HAS NOT RUN: [HUD] Probe=1 logs the instance of our first Draw beside the
 *                      stock clock's ('hud: probe: ... SAME SHAPE' = it is on the HUD plane).
 *    Draw=2            the PROVEN way (the probe round's step E3, picture research\watch\20261011_160216\0029_1895s.jpg:
 *                      'TOTAL $145,000' in our colour at (640, 300), right-aligned at x): the stock ZFATimeDisplay::
 *                      Render (0x81e090, EXE read whole) is called once a text with OUR text + shadow in the element's
 *                      two slots (+0x28, +0x2c), our place in +0x14 / +0x18 and its 'escape part' byte +0xbc at 0 (so
 *                      it draws the one pair and nothing else); all four are put back in the same call. It draws only
 *                      in session state 0x19 (its own test, 0x81e0c3) and needs a shadow object a text - so with
 *                      Draw=2 every text gets a shadow (the Grid labels too) and ours is shown, and the stock block
 *                      hidden, ONLY in state 0x19: in the countdown the stock block stays. The fall-back if H1 shows
 *                      nothing.
 *    Both run INSIDE the element loop: the timer element (osd+0x10cc) gets a private copy of its 11-slot vtable (RTTI
 *    locator kept) whose slot 2 is klu_render_elem = the stock Render first, then ours with the same ctx / cam. One
 *    heap dword written; no code byte of kl2.exe changes.
 *
 * 3. PICTURES (keys Plates, PicTest; NEVER RUN - every picture part is off by default)
 *    The clock's own vehicle icon (0x81e20b..0x81e275): place = 0x5a3e90(T = [elem+0xc], &out3, &in2) = (x * T[+0x14],
 *    y * T[+0x18], 0) + origin; [elem+0x70] = [elem+0x3c] (the colour into desc+0x30); ctx->DrawChunk([[elem+8] +
 *    12 * n] = the sprite of HUD picture n, desc = elem+0x40 (0x34 bytes: [+0] = 1, [+8] = &record, the 40-byte record
 *    lies inside it at +0xc: vec3 offset | 0, 1.0, 1.0, 0 | +0x1c width, +0x20 height | +0x24 ARGB), &xform9, &out3,
 *    layer, 1, 0). klu_pic copies the element's desc (every field this reading did not decode stays the game's), sets
 *    width / height / colour and points [+8] at a record in the hook's own static table. EXE 0x842de9 .. 0x842e03:
 *    DrawChunk copies desc[0], desc[1] and memcpy's count x size bytes FROM [desc+8] into its own buffer, so only the
 *    pointed-at record is read and nothing of ours is kept after the call. The record's size comes from the chunk's
 *    type dword [chunk+0xc] (chunk = [0xeac7b0 + 4 * handle], or handle & 0x7fffffff when its top bit is set; jump
 *    table 0x842ee4: type 1 = 24 bytes, 5 = 40, 6 / 8 = 0x74, 7 = 0x54 + 64 n): the tick reads the type of pictures
 *    181 and 170 once a level and a picture whose chunk is not type 5 is NOT drawn (logged).
 *    GUESSES, none read in the exe, PicTest decides them: (a) width / height are 'virtual pixels x T[+0xc] / T[+0x10]'
 *    (no instruction cited: PicTest's A, asked for as 200 x 24, against B, the element's own size, shows it);
 *    (b) (x, y) is the sprite's middle (PicAnchor=1) and not its top-left corner; (c) UI_White (picture 181) takes
 *    the colour as a tint. [HUD] PicTest=1 (three shapes at y 500) and Grid=1 with Plates=1 on one screenshot.
 *
 * 4. THE DATA (main-thread tick, every 100 ms; klbot.c's klb_read: Arcade session, ZGameRulesHeist, the crew records)
 *    row = a crew record in use, in record order. name = the C string at [[record+0]+8] (EXE 0x841e50; klcrew.c writes
 *    the same). status 0 in play / 4 aboard / 6 escaped / 7 dead, record flags 1 = AI, 2 = traitor (klbot.c 1, seen
 *    live). score = [rules+0x5f8]: cash carried [score+0x150 + 4 * i]; the per-client flag dword [score+0x1d4 + 4 * i]
 *    (klfedkit.c: 1 traitor, 8 police) - ASSUMED indexed like the money, as klfedkit.c takes client 0 for the human;
 *    rewards [score+0x184 + 4 * i] (the column the stock list's rows read, slot 55 = 0x6c05f0; klfedkit.c 6); Total =
 *    what the stock 'Total score' shows, 0x807520(rules) computed from data: record 0's money + the dwords score+0x04
 *    .. +0x10, +0x18 .. +0x24, +0x2c and +0x38; round = byte score+0x45; lives = byte score+0x44 (the copy the HUD
 *    shows, re\leaderboard.md 2.3). A FED human (klfed.c) keeps record 0, in play, with flag 8: his row reads 'FED' in
 *    blue and his 'LOOT' is the money he holds (the outro's 'finder's fee').
 *    Shown while: session state 0x17 .. 0x19 (the stock player list's own window), the clock element enabled and not
 *    hidden (the game's cut-scene hide 0x75f780 hides it with the player list), osd+0x1225 'HUD off' clear - and the
 *    level is NOT stock (klsteam.c's verdict 2, the test klfedkit.c uses) unless Stock=1. The round-over page, the
 *    intro and the score page are other elements and other states: nothing of ours is drawn there, the stock block is
 *    shown again.
 *
 * 5. THE STOCK BLOCK AND klfedkit.c's HudFade
 *    HideStock=1 writes byte +0x25 = 1 of ZFAPlayerListDisplay (osd+0x10c4, vtable checked) while ours draws and 0
 *    when it does not: every way the tick stops drawing with a live OSD goes through klu_stand_down (state left, a
 *    fault, the vtable wrap refused, the transform not 1280 x 720, a stock level). THE GAME WRITES THE SAME BYTE: its
 *    own hide 0x75f780(osd, b) sets +0x25 of the clock (0x75f796) AND of the player list (0x75f7a8) - six call sites,
 *    ten times in the owner's round of 16:32. So before the hook writes 0 it reads the CLOCK's +0x25: 1 = the game
 *    has hidden the whole set, the hide is the game's now, the byte is left and ours is forgotten (the game's own
 *    'show' writes 0 to both, and the next tick hides the list again).
 *    klfedkit.c's HudFade writes the SAME element's cross-fade state (+0xee0, +0xf00) when it reads 1: other fields,
 *    a hidden element's Tick still runs, the two never write the same byte - with HideStock=1 the cross-fade is
 *    simply not seen any more. HideStock=0 leaves the stock block drawn UNDER ours (same place): only for a
 *    comparison picture, and the first TEST run may use it.
 *
 * 5b. WHEN A LEVEL IS OVER (the objects are the scene's, never freed by the hook)
 *    The state is dropped - and a new set made at the next round - when the scene name changes, the OSD's address
 *    changes, the Arcade rules object changes (a new one a round: klbot.c) or the session state is below 0x16. One
 *    failed read of the scene name while the OSD still stands is ignored for up to 1 s (nothing is done in those
 *    ticks). The render slot reads its objects directly (no system call a text); what guards it is one checked read
 *    of the OSD's and of text 0's vtable a clock-element call, and the tick's check of every text and shadow.
 *
 * 6. STOCK ARCADE ('for FA & Arcade going forward'): Stock=1 draws the same layout on a stock level. Nothing else is
 *    needed in the hook (the rules object and the OSD are the same classes; runs H1b .. H1q made and set the texts on
 *    stock Subway) and nothing is written to Steam by this part. What a stock level does NOT have is the LOOK (font,
 *    brush pictures): that is level data (tools\kl_hud.py on a copy of the level, as tools\kl_stock_mod.py builds).
 *    FA online: not done (klb_read is Arcade only; other players' names and cash come from another reader).
 *
 * KLHook.ini
 *   [HUD]
 *   Enable=0          1 = on
 *   Stock=0           1 = also on a stock level (section 6)
 *   Log=1             0 none, 1 on / objects made / stock block hidden / faults, 2 + every text change and counters
 *   Crew=1 Money=1 Round=1     the three blocks
 *   OnlineBots=1 (recommended on)  online crew box: one row per AI heister (Ally actors; GUESS none of the humans is team 2)
 *   HideKilledBy=1 (recommended on)  blank the STOCK death panel's 'Killed by' text (kllocname.c: LOC lookups from 0x500670 and the key KilledBy answer an empty string; Arcade and online, any map), so only our KILLED BY line shows
 *   KilledBy=1 (recommended on)  "KILLED BY name" in the HUD style while dead (offline); ScoreboardShopLead=30  tenths of a s cut off the 10 s round-over count (shop opens at 7)
 *   HideStock=1       hide the stock top-left block while ours draws
 *   Draw=1            1 = our own Draw, 2 = through the stock clock's Render (section 2)
 *   Shadow=1          drop shadows (forced on with Draw=2)
 *   Tags=1            'TRAITOR' / 'OUT' / 'FED' after the name
 *   CashShort=1       the crew rows' cash as $540K / $1.2M (the draft); 0 = $540,000
 *   TotalFont=0       1 = the TOTAL value in the headline font (osd+0xd50; its size on screen was never seen)
 *   Plates=0          1 = the picture parts: rule, own / traitor row blocks, strike-through, the money bar (section 3)
 *   PicAnchor=1       1 = a picture's (x, y) is its middle (GUESS), 0 = its top-left corner
 *   PicTest=0         1 = three test pictures at y 500
 *   Grid=0            1 = the layout's boxes labelled with their corners; 2 = and the draft's eight sample rows
 *   Probe=0           1 = every 5 s the render instance of the stock clock, of our first text and of our first picture
 *   Inset=-1          -1 = leave the game's [0xceeebc] (0.05 = 64 / 36 px); 0.026 = the draft's margin (moves the
 *                     game's own elements too); our blocks follow it. The game's value is put back at the next scene
 *                     change (a stock level after it has its own margin)
 *   CrewX=-1 CrewY=-1 CrewW=211 Row=24 Rows=8          -1 = the inset
 *   MoneyX=-1 MoneyY=-1 MoneyW=211 RoundY=-1           MoneyX = the RIGHT edge; -1 = inset, inset + 87, inset + 58
 *   Layer=13          the texts' layer byte (shadows one below, plates two below; 15 = the clock's)
 *   LeftStyle=17      0x11 = KLU_STYLE_LEFT (proven live, run H1_DM03_hud: low nibble 1 left / 2 right / 4 centre)
 *
 * VERSION 3 (2026-10-11 night): THE PARTS WIRED. re\hud_hook.md 10 has the live checks in order.
 *   Draft=0           1 = the whole draft at once: Plates, Dials, Weapon, Popups, LootRing, RoundOf default to 1 (HideStock
 *                     and Lives are on by default anyway). 'Enable=1' + 'Draft=1' is the owner's ini; every single key below
 *                     still overrides (Dials=0 with Draft=1 = no dials)
 *   --- klhud_values.c (included BEFORE this file; reads only; re\hud_values.md) ---
 *   Lives=1           0 none, 1 three skull pictures (178) in your row ('LIVES n' in the round line when the level has no 178),
 *                     2 TEST: skull glyphs after your name, 3 'LIVES n' in the round line
 *   RoundOf=0         1 = 'ROUND n OF m' with the game's own m (10; whether a session ends there is not established)
 *   --- klhud_weapon.c (included inside this file; re\hud_weapon.md) ---
 *   Weapon=0          1 = the weapon dial, the stock ammo panel's Render is skipped while it stands (needs pictures 113 / 114)
 *   WeaponX=-1 WeaponY=-1 WeaponSmall=0.8 WeaponOther=0
 *   --- klhud_popup.c (included by klhook.c after this file; re\hud_popup.md) ---
 *   Popups=0 LootRing=0 PopupFrame=0 PopupMeasure=1 PopupPadX=62 PopupPadY=12 PopupDY=0 PopupY=-1 PopupLayer=23
 *   PopupTraitor=1 PopupTest=0 RingMode=1 RingX=-1 RingY=-1
 *   THE KNOCK-DOWN PROMPT (kldown.c) is the game's own ZMiniGameButtonMashingDisplay at osd+0x10fc: no part of the HUD
 *   reads, hides, wraps or restyles that element. The elements the parts touch: +0x10cc clock (wrapped, this file),
 *   +0x10c4 player list (hide byte), +0x1110 ammo panel (wrapped, klhud_weapon.c), +0x10a8 announcements (wrapped,
 *   klhud_popup.c); +0x110c use-action is only read.
 */
#ifndef KLHUD_C
#define KLHUD_C

#define KLU_OSD_VT      0x00bbe504u           /* ZOnScreenDisplay2 (re\hud.md 1) */
#define KLU_TEXT_VT     0x00bab45cu           /* ZCHAROBJ (re\hud.md 3.1) */
#define KLU_CREATE      0x00817810u           /* ZCHAROBJ vtable +0x19c, the create-child the elements use */
#define KLU_REFOBJ      0x008ccde0u           /* cdecl (REF id) -> object */
#define KLU_PARENT      0x00598460u           /* thiscall on [tmpl+4] -> [[this+0x50]+0x60] or 0 */
#define KLU_DRAW        0x005a6d40u           /* ZCHAROBJ vtable +0x1e8 */
#define KLU_PLIST_VT    0x00bbdf6cu           /* ZFAPlayerListDisplay (re\hud.md 2.2) */
#define KLU_TIME_VT     0x00bbdfecu           /* ZFATimeDisplay (re\hud.md 2.2) */
#define KLU_TIME_RENDER 0x0081e090u           /* its slot 2 (section 2) */
#define KLU_INSET       0x00ceeebcu           /* float 0.05, the 5 % inset (re\hud.md 4.2) */
#define KLU_TAG         0x5a434f42u           /* 'ZCOB' */
#define KLU_DRAWCHUNK   0x00842d00u           /* ZDrawBufferSimple slot 5 */
#define KLU_CTX_VT      0x00b55484u           /* ZDrawBufferSimple */
#define KLU_PLACE       0x005a3e90u
#define KLU_CHUNKTAB    0x00eac7b0u           /* the chunk table DrawChunk indexes with a handle (0x842d2e) */
#define KLU_PICTYPE     5                     /* [chunk+0xc]: the type whose record is 40 bytes (0x842e19) */
#define KLU_OSDHOLD     0x15dc               /* gamedata: -> { osd, byte != 0xff } (0x588680, 0x4ddae0; klfedkit.c 7 reaches the OSD this way, live) */

#define KLU_O_TEMPLATE  0xd4c                 /* REF of the ZCHAROBJ template */
#define KLU_O_BIGFONT   0xd50                 /* REF of the headline font (re\hud.md 6.4) */
#define KLU_O_FONT      0xd54                 /* REF of the font the FA elements register with */
#define KLU_O_XFORM     0x1130                /* the screen transform: +0x1c = 1280.0, +0x20 = 720.0 once the HUD has drawn */
#define KLU_O_PLIST     0x10c4                /* ZFAPlayerListDisplay * */
#define KLU_O_TIME      0x10cc                /* ZFATimeDisplay * */
#define KLU_O_HUDOFF    0x1225                /* 'HUD off' */
#define KLU_E_ENABLED   0x24                  /* IDisplayInterface +0x24 enabled, +0x25 hidden */
#define KLU_E_HIDDEN    0x25
#define KLU_E_POS       0x14                  /* the clock element: its place (x, y, z) */
#define KLU_E_TEXT      0x28                  /* its text, +0x2c its shadow */
#define KLU_E_ESCAPE    0xbc                  /* byte: not 0 = its Render also draws the escape line and the vehicle icon (0x81e142) */
#define KLU_ELEM_NSLOT  11                    /* IDisplayInterface: 11 slots, then RTTI */

#define KLU_VT_CREATE   0x19c
#define KLU_VT_DRAW     0x1e8
#define KLU_VT_COLOUR   0x20c
#define KLU_VT_STYLE    0x220
#define KLU_VT_LAYER    0x234
#define KLU_VT_FONT     0x23c
#define KLU_VT_TEXT     0x244

#define KLU_S_MONEY     0x150                 /* score: cash carried, one int a crew record (klbot.c) */
#define KLU_S_REWARDS   0x184                 /* score: rewards, one int a client (klfedkit.c 6) */
#define KLU_S_FLAGS     0x1d4                 /* score: one dword a client: 1 traitor, 8 police (klfedkit.c 5) */
/* (KLU_S_LIVES 0x44 is gone: that byte is the number of rounds, the lives are [score+0x6c] - klhud_values.c a) */

#define KLU_ROWS        12                    /* 2026-10-26: was 8; online FA is up to 12 players. [HUD] Rows12=0 caps the list at KLU_ROWS_OLD again */
#define KLU_ROWS_OLD    8
#define KLU_T_HEAD      0                     /* 'DEAD MEN' */
#define KLU_T_COUNT     1                     /* '5 / 8' */
#define KLU_T_NAME(i)   (2 + 2 * (i))
#define KLU_T_CASH(i)   (3 + 2 * (i))
#define KLU_T_ROUND     (2 + 2 * KLU_ROWS)
#define KLU_T_MLABEL(k) (KLU_T_ROUND + 1 + 2 * (k))        /* k = 0 TOTAL, 1 LOOT, 2 REWARDS */
#define KLU_T_MVALUE(k) (KLU_T_ROUND + 2 + 2 * (k))
#define KLU_T_GRID      (KLU_T_MVALUE(2) + 1)
#define KLU_NSWEEP      8                     /* Grid: one label per candidate style byte */
#define KLU_NGRID       (10 + KLU_NSWEEP)
#define KLU_T_WEAP      (KLU_T_GRID + KLU_NGRID)      /* klhud_weapon.c: the first gun's count, the other gun's, the label */
#define KLU_NWEAP       5                     /* the first gun's count, the other gun's, the label (the name, or the whole text in the old look), the slash, the reserve */
#define KLU_T_KILL      (KLU_T_WEAP + KLU_NWEAP)      /* klhud_kill.c: the kill / reward line under REWARDS (2026-10-13) */
#define KLU_T_ESC       (KLU_T_KILL + 1)              /* the van card's time (2026-10-13) */
/* THE TAB CARD (2026-10-13, the owner: 'when you press tab ... optional overview'): [HUD] TabCard=1 - while Tab is held the crew list is
   drawn as a card in the middle of the screen (an ink stroke, 'CREW', a row a heister: name, a status word, cash) instead of stepping
   aside for the stock list, which then stays hidden. TabCard=0 (default): the stock list as before (TabList). */
#define KLU_CARD_W      440.0f
#define KLU_CARD_Y      196.0f                /* the card's head line */
#define KLU_CARD_ST     0.62f                 /* the status column's middle, a part of the width */
#define KLU_CARD_INK    0xd80c0c0du           /* the painted bands */
#define KLU_CARD_UNDER  0x9c0c0c0du           /* the solid ink under them */
#define KLU_CARD_BAND   28.0f                 /* a band's height (they overlap by 6) */
#define KLU_VDISC       (1.0f / 0.6f)         /* 2026-10-14: picture 170 / 171 (the vehicle disc) is baked with its disc at 0.6 of the picture (tools/kl_hud_marks.py VEHICLE_DISC: the world marker draws it at a fixed size); every place here that draws it grows by this, so it looks as before */
#define KLU_CARD_STDY   5.0f                  /* the status word lower by this: live (run v45_KL, 80 s) its capitals sat 5 px above the name's (the label font's ascent is not the baked one) */
#define KLU_T_DEATH     (KLU_T_ESC + 1)               /* 2026-10-25: 'KILLED BY name' in the new look while you are dead (the stock death panel's line is an XML text in the level archive) */
#define KLU_T_TABST(i)  (KLU_T_DEATH + 1 + (i))  /* the Tab card's status column, one a row (2026-10-13) */
#define KLU_NTEXT       (KLU_T_TABST(KLU_ROWS))   /* LAST: every part that adds texts goes before this line (klhud_values.c / klhud_popup.c add none) */
#define KLU_NPIC        300                   /* the queue; the rings are baked arcs + a run of dabs (klu_arc): about 230 a frame at worst; the draw list holds 280 without trouble (run S1), keep it under ~320 */
#define KLU_TEXTLEN     64
#define KLU_STYLE_LEFT  (klu.left)        /* [HUD] LeftStyle: 0x44 turned out CENTRED at x (run H1_DM03_hud); 0x11 is a GUESS until the sweep of Grid shows it */
#define KLU_STYLE_CENTRE 0x44
#define KLU_STYLE_RIGHT 0x12
#define KLU_SHADOW_RGB  0x80000000u
#define KLU_SHADOW_SMALL 0x60000000u          /* about half as dark for the labels, names and small figures (GUESS: the top byte is the shadow's alpha, as 0x80 of the stock shadow) */

/* the draft's colours (its CSS variables) */
#define KLU_C_CHALK     0xfff3f0eau
#define KLU_C_CORAL     0xfff0475au           /* labels */
#define KLU_C_ORANGE    0xffe8831fu           /* traitor */
#define KLU_C_DEAD      0xff8c3138u
#define KLU_C_DEADCASH  0xff5f2a2fu
#define KLU_C_OUT       0xffa9a59du
#define KLU_C_GREEN     0xff4f8f49u           /* money */
#define KLU_C_GREENHI   0xff63a65bu           /* the total, the crew's cash */
#define KLU_C_INK       0xff0c0c0du           /* letters on a painted block */
#define KLU_C_INKCASH   0xff1f4a1du           /* own cash on the chalk block */
#define KLU_C_BLUE      0xff6ea3d6u           /* own row without plates, a fed */

/* TYPE (2026-10-11, the owner: 'its all that one font ... 1:1 with the draft'; tools/kl_hud.py DRAFT_SPECS bakes them). The HUD reaches
   four of the level's eight fonts by REF in the OSD: +0xd54 (the FA font), +0xd50 (the headline font), +0xd58, +0xd48. WHICH
   baked slot name sits behind which offset is ASSUMED (re/hud.md 2.2: d50 = ammo / announcements = H1, d54 = list / names = H2,
   d58 = tracker / text display = H3, d48 = DebugText); [HUD] FontName / FontBig / FontLabel / FontSmall re-point a role to
   another offset without a rebuild. A text's font decides its SIZE (the bake) and its face; fnt: 0 names, 1 big, 2 labels, 3 small. */
/* 1:1 ROUND (2026-10-11): the roles are H2 = names / money rows / weapon count (+0xd54), H1 = the total (+0xd50), LABEL = DebugText
   (+0xd5c: nothing stock draws with it, so Segoe UI Black labels have no side effect), SMALL = H3 (+0xd58: cash, counts; stock:
   subtitles, tracker). +0xd5c AS DebugText is read from re/hud_data.md's property order, NOT seen live; when it is not a font object
   the label role takes the SMALL font (logged). The label font's tracking (KLU_TRACK) is added back for right / centre alignment. */
#define KLU_TRACK       3.0f
#define KLU_NFONT       4
#define KLU_FNT_NAME    0
#define KLU_FNT_BIG     1
#define KLU_FNT_LABEL   2
#define KLU_FNT_SMALL   3
/* CENTRING: the game puts a text's baseline at y - header[9] (the ascent offset; LIVE: row 1 of V3, Draw y 102, stock H2 header -13, the
   capitals ran from y - 1.5 to y + 13). kl_hud.py bakes header[9] = -cap, so with fonts baked by DRAFT_SPECS the capitals' TOP lies at the y
   given to Draw and their height is cap (default {16, 24, 9, 13} = what DRAFT_SPECS gave in the 1:1 round, kl_hud.py prints the line; [HUD] Cap0..Cap3). A text with cen = 0 keeps the
   baseline the stock font gave it (y + 13); cen = 1: y is the top of its capitals (klu_cen). */
#define KLU_BASE_OLD    13.0f
/* SIZES, 2026-10-11 'quiet round' (owner: the small spaced labels are right, the heavy texts shout; 'so its not all in your face, just a nice touch').
   The caps below are what tools/kl_hud.py bakes (DRAFT_SPECS_ANTON: Anton 12 / 17 / 11 px, Montserrat 12 px): names 11, total + pop-up 15, labels 10,
   small 10. The draft layout (Draft=1) follows from them; every number is a [HUD] key too (Row, CrewW ...) or a constant here. Before -> after:
   row pitch 30 -> 21, block 28 -> 19 high, text y under the head 34 -> 28 (block top cy + 24), name inset 8 -> 6, rule 5 -> 3 high, strike 4 -> 2, money lines
   TOTAL / LOOT / REWARDS at +0 / +34 / +52 (was +0 / +40 / +64), the bar 8 -> 6 high at +22 (was +26), the total under the round line at +99 (was +114). */
#define KLU_D_ROW        21.0f
#define KLU_D_YOFF       28.0f                /* the first row's text y under the crew list's top (head label baseline cy + 13, rule cy + 17.5 .. + 20.5) */
#define KLU_D_BLOCKUP    4.0f                 /* the painted block starts this far above the text's y: block top = cy + 24 */
#define KLU_D_BLOCKH     19.0f
#define KLU_D_PADX       6.0f
#define KLU_D_RULE_Y     17.5f                /* the painted rule under 'DEAD MEN' */
#define KLU_D_RULE_H     3.0f
#define KLU_D_STRIKE_H   2.0f                 /* a dead heister's strike (was 4) */
#define KLU_D_STRIKE_PAD 8.0f                 /* it reaches this far beyond the name's width (was 12) */
#define KLU_D_MONEY_DY   99.0f                /* the money box's top (the TOTAL text's y) under the inset line, with the dials */
#define KLU_D_MLINE0     34.0f                /* LOOT's y under the TOTAL's */
#define KLU_D_MLINE      18.0f                /* LOOT -> REWARDS */
#define KLU_D_BAR_Y      22.0f                /* the framed bar under TOTAL */
#define KLU_D_BAR_H      6.0f                 /* its frame; the fill is 4 higher, 2 above and below the frame */
#define KLU_D_MONEY_H    66.0f
#define KLU_MFILL_PIC    117                  /* the watch look's painted fill of the money bar (tools/kl_hud.py EXTRAS_NEW 'mfill') */
#define KLU_W_BAR_Y      22.0f                /* the watch look: the frame's top under the TOTAL's y (as KLU_D_BAR_Y) */
#define KLU_W_BAR_H      8.0f                 /* its height: the draft's 12 at the quiet scale (was 6) */
#define KLU_W_FILL_OVER  2.0f                 /* the fill stands this far above and below the frame (the draft: 1.4 of 12) */
#define KLU_W_FILL_OUT   1.5f                 /* ... and this far left of it */
#define KLU_W_MLINE0     37.0f                /* LOOT's y under the TOTAL's in the watch look: the taller bar's fill ends at +32, LOOT's capitals start 5 below (was 34 / 2) */                /* the Grid box of the money lines */
static float klu_cap_of(int f);
static const int klu_sweep[8] = { 0x11, 0x14, 0x21, 0x41, 0x01, 0x10, 0x42, 0x24 };
struct klu_text { DWORD obj, shadow, shcol; float sa; float x, y; int on, style, big, plain, noshadow, fnt, cen; DWORD colour, want_colour; char cur[KLU_TEXTLEN], want[KLU_TEXTLEN]; };
struct klu_picq { int n; float x, y, w, h; DWORD argb; int layer; };

static struct {
    int left;                                 /* LeftStyle */
    int fontset;                              /* Fonts: the four roles (names / big / labels / small) take their own fonts; the level must be baked by kl_hud.py --look deadmen from 2026-10-11 on */
    float cap[KLU_NFONT]; DWORD fofs[KLU_NFONT];      /* Cap0..3, FontName / FontBig / FontLabel / FontSmall */
    int extraflags;                           /* ExtraFlags: give the eight extra pictures a stock picture's chunk flags */
    int weapon;                               /* Weapon: the weapon dial (klhud_weapon.c) */
    int draft;                                /* Draft: the defaults of every part of the draft are 1 */
    int lives, roundof;                       /* Lives, RoundOf (klhud_values.c) */
    int onbots, killed, on, log, stock, crew, money, round, hide, shadow, tags, cashshort, totalfont, draw, plates, anchor, pictest, grid, probe, layer, rows, dials;
    int wstyle, wini, wseconds, wwear, wlast, labelbar, labelslash, mfill, vanicon, tablist, tabcard, hidesrc, hideonl, oprobe;   /* wini = [HUD] WatchStyle as set; wstyle = the look THIS level gets (klu_choose_look) */
      /* the watch look (section 14 of re\hud_hook.md): WatchStyle (1 = new, 0 = the old textures and sizes), WatchSeconds, WatchWear, WatchLast, LabelBar (0 text only, 1 painted bar, 2 plain), LabelSlash */
    float inset, crew_x, crew_y, crew_w, row, money_x, money_y, money_w, round_y;
    float yoff, blockup, blockh, padx;        /* the rows: the text's y under the head, the block's rise above it, its height, the text's side margin (the draft: 34 / 5 / 28 / 8) */
} klu;
#define KLU_DRY()        (klu.wstyle ? 111 : 112)      /* the 'dry stroke' of the old look is gone: slot 112 became the dial's wear */

static struct {
    DWORD osd, elem, tmpl, font, bigfont, parent, rules; char scene[160];
    DWORD fonts[KLU_NFONT];                   /* the four font objects a text may take (klu_font_of): 0 names, 1 big, 2 labels, 3 small - each the FA font when its REF is not usable */
    DWORD handle[200];                        /* the sprite handle of every HUD picture whose chunk is type 5, else 0 (section 3; klu_pic_prep) */
    float clock_max; int watch;               /* Dials: the longest round clock seen this round; 1 = the watch stands for the stock clock's digits */
    int made, fault, hid, inset_done, told_stock, pic_done, tab, card;     /* card: this compose lays the crew out as the Tab card */
    float cx, cy, mx, my, ry, wy;             /* the layout of this level (the keys, or the inset) */
    struct klu_text t[KLU_NTEXT];
    struct klu_picq pic[KLU_NPIC]; int npic;
} klu_r;
static volatile LONG klu_draw_on;             /* read by the render slot: 1 = objects exist and the round shows the HUD */
static volatile LONG klu_n_call, klu_n_try, klu_n_draw, klu_n_refused, klu_n_pic, klu_n_picno, klu_n_maxinst;
static volatile LONG klu_probe_want, klu_probe_ready;
static struct { float stock[14], ours[14], pic[14]; LONG nstock, nours, npic; } klu_pr;
static CRITICAL_SECTION klu_cs;
static char klu_kill_txt[64];                 /* klhud_kill.c hands the points pop-up's line here (under klu_cs) ... */
static LONG klu_kill_at, klu_kill_ms = 3500;
/* 2026-10-26 (the online port's open items 'stock kill popup still swallowed online' / 'stock van panel still blanked'): a stock element
   is taken off the screen ONLY while this compose draws its replacement. klu_compose publishes, once per compose (no 0 window between
   a reset and a set: the render thread reads these), KLU_KEEP_KILL when the kill line under REWARDS is live (klu_kill_line with on) and
   KLU_KEEP_VAN when the van card is live (klu_van_card with [HUD] Money). klhud_kill.c swallows the points pop-up only with the first;
   klhud_escape.c (EscapeCard=1) hides the stock panel's time / icon / bar only with the second. Online with [HUD] OnlineFeed=0 /
   OnlineVan=0 (the defaults) or without OnlineCrew, and in Arcade with Money=0, both are 0 and the stock elements draw as the game's own. */
#define KLU_KEEP_KILL   1
#define KLU_KEEP_VAN    2
static volatile LONG klu_keep;                  /* the published bits */
static int klu_keep_now;                        /* the bits this compose gathers (game thread only) */
static int klu_hideidle = 1, klu_hideidle_dry;   /* [HUD] HideIdleEscape / HideIdleEscapeDry (2026-10-24) */
static volatile LONG klu_esc_rst;   /* 2026-10-17 review: set by klu_reset (scene change): the van card block drops its latched state, no ghost card in the next level */
static volatile LONG klu_esc_at, klu_esc_frac, klu_esc_slot, klu_esc_time;     /* klhud_escape.c (EscapeCard): a frame the stock panel would draw, its health share (float bits), the icon slot, its time text object */
#define KLU_ESC_GAP     8.0f                  /* the van card: under the kill line */
#define KLU_ESC_H       30.0f
#define KLU_ESC_HOLD   2500          /* ms the van card stays after the stock panel's last draw. 2026-10-17: the owner's v81 log showed the stock panel skipping up to 1.64 s while the van was there, so 1 s was too short; 2.5 s covers it. GUESS: no longer gap was seen, not proven. */
#define KLU_ESC_LOGGAP 1000          /* ms: van card ON/off log lines at most this often (the log reached 29 MB); the skipped ones are counted */
#define KLU_ESC_FIN    150
#define KLU_ESC_FOUT   300
static DWORD klu_fa(DWORD c, float a) { DWORD al = (DWORD)((float)(c >> 24) * (a < 0 ? 0 : a > 1 ? 1 : a) + 0.5f); return (c & 0x00ffffffu) | (al << 24); }
#define KLU_ESC_TOFF    (KLU_ESC_H * 0.5f)    /* ... with GetTickCount | 1 when it came; compose shows it klu_kill_ms long */
static DWORD klu_evt[KLU_ELEM_NSLOT + 1];     /* [0] RTTI locator, [1..] the slots */
static int klu_evt_ready;
/* 2026-10-25 owner: 'the old HUD stuff deleted entirely from the match, I see it when I tab'. The +0x25 hide byte is the game's own and a
   Tab / focus change / re-show may rewrite it for a tick. HideSrc=1 wraps slot 2 (Render) of ZFAPlayerListDisplay in a private heap vtable
   (SHIP-safe, a data write): while klu_skip_list is 1 the stock Render is simply not called, whatever the byte says. */
static DWORD klu_pvt[KLU_ELEM_NSLOT + 1]; static int klu_pvt_ready;
static volatile LONG klu_skip_list;
static float klu_prec[KLU_NPIC + 3][10];      /* the pictures' records (section 3): one a picture, rewritten with the same numbers every frame */

typedef DWORD (__fastcall *klu_create_t)(void *, void *, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD);
typedef void (__fastcall *klu_set1_t)(void *, void *, DWORD);
typedef void (__fastcall *klu_draw_t)(void *, void *, void *, void *, const float *, const float *);
typedef char (__fastcall *klu_render_t)(void *, void *, void *, void *);

static int klu_same_code(DWORD va, const BYTE *bytes, int n)
{
    BYTE c[16];
    return n <= (int)sizeof c && klh_rd((DWORD_PTR)KLH_VA(va), c, n) && !memcmp(c, bytes, n);
}

/* ---------------------------------------------------------------- the render slot (whichever thread renders; reads our prepared data only) */

static int klu_draw_one(DWORD obj, void *ctx, void *cam, float x, float y)
{   /* Draw=1: -> 0 refused by the checks, 1 Draw called. The xform is what 0x7f07a0 writes (fld1; fst [+0x18]; fldz; five
       zero stores, the last a POP; the 1.0 left on the stack goes to [+0x10] and [+8]) - re\hud.md 9 */
    float xform[9] = { 0, 0, 1.0f, 0, 1.0f, 0, 1.0f, 0, 0 };
    float pos[3];
    pos[0] = x; pos[1] = y; pos[2] = 0;                              /* the stock call passes elem+0x1c, which is 0 for the clock */
    /* a direct read (section 5b): the object was checked by the tick and by this call's canary; ZCHAROBJ's slot +0x1e8
       was checked against 0x5a6d40 when the texts were made */
    if (!obj || *(const DWORD *)(DWORD_PTR)obj != KLU_TEXT_VT) return 0;
    ((klu_draw_t)(DWORD_PTR)KLH_VA(KLU_DRAW))((void *)(DWORD_PTR)obj, 0, ctx, cam, xform, pos);
    return 1;
}

static int klu_draw_stock(void *el, void *ctx, void *cam, DWORD obj, DWORD shadow, float x, float y)
{   /* Draw=2: the stock clock Render draws OUR pair at OUR place (section 2; the probe round's step E3). el is the clock
       element the game is rendering in this very call (klu_render_elem checked it), so its fields are read and written
       directly; all four are put back before this returns. */
    DWORD e = (DWORD)(DWORD_PTR)el, *slot = (DWORD *)(DWORD_PTR)(e + KLU_E_TEXT), s0, s1; float *pos = (float *)(DWORD_PTR)(e + KLU_E_POS), p0, p1;
    BYTE *esc = (BYTE *)(DWORD_PTR)(e + KLU_E_ESCAPE), b;
    if (!obj || !shadow || *(const DWORD *)(DWORD_PTR)obj != KLU_TEXT_VT || *(const DWORD *)(DWORD_PTR)shadow != KLU_TEXT_VT) return 0;
    s0 = slot[0]; s1 = slot[1]; p0 = pos[0]; p1 = pos[1]; b = *esc;
    slot[0] = obj; slot[1] = shadow; pos[0] = x; pos[1] = y; *esc = 0;
    ((klu_render_t)(DWORD_PTR)KLH_VA(KLU_TIME_RENDER))(el, 0, ctx, cam);
    slot[0] = s0; slot[1] = s1; pos[0] = p0; pos[1] = p1; *esc = b;
    return 1;
}

static int klu_pic(void *el, void *ctx, int slot, int n, float x, float y, float w, float h, DWORD argb, int layer)
{   /* section 3. w <= 0: the width / height the element's own record has. -> 1 = DrawChunk called.
       No system call here (section 5b): el is the clock element the game is rendering in this very call and ctx its
       argument; the handle is the one klu_pic_prep read and type-checked in the tick (0 = that picture is not drawn),
       which also checked ZDrawBufferSimple's slot 5 */
    DWORD e = (DWORD)(DWORD_PTR)el, T = *(const DWORD *)(DWORD_PTR)(e + 0xc), handle = n >= 0 && n < 200 ? klu_r.handle[n] : 0;
    DWORD desc[13]; float *rec, in[2], out[3] = { 0, 0, 0 }; const float *t;
    float xform[9] = { 0, 0, 1.0f, 0, 1.0f, 0, 1.0f, 0, 0 };
    if (slot < 0 || slot >= KLU_NPIC + 3 || !T || !handle || !ctx || *(const DWORD *)ctx != KLU_CTX_VT) return 0;
    memcpy(desc, (const void *)(DWORD_PTR)(e + 0x40), sizeof desc);
    if (desc[0] != 1) return 0;
    t = (const float *)(DWORD_PTR)(T + 0xc);
    rec = klu_prec[slot];
    memcpy(rec, &desc[3], 40);                                       /* the element's own record: offset, the four middle fields, its size */
    if (w > 0) {
        rec[7] = w * t[0]; rec[8] = h * t[1];                        /* GUESS (section 3 a): T+0xc, T+0x10 = virtual pixel -> the record's units */
        if (klu.anchor) { x += w * 0.5f; y += h * 0.5f; }            /* GUESS (section 3 b): the place is the sprite's middle */
    }
    memcpy(&rec[9], &argb, 4);
    desc[2] = (DWORD)(DWORD_PTR)rec;                                 /* DrawChunk memcpy's the record from here (0x842dfd) */
    in[0] = x; in[1] = y;
    ((void (__fastcall *)(void *, void *, float *, float *))(DWORD_PTR)KLH_VA(KLU_PLACE))((void *)(DWORD_PTR)T, 0, out, in);
    ((DWORD (__fastcall *)(void *, void *, DWORD, DWORD *, float *, float *, DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLU_DRAWCHUNK))(ctx, 0, handle, desc, xform, out, (DWORD)layer, 1, 0);
    return 1;
}

static void klu_inst(void *ctx, DWORD index, float out[14])
{   /* the render instance DrawChunk appended as number `index` of this frame: its floats +0x28 .. +0x5c
       (scale x at +0x28, y at +0x30 / +0x38, the place at +0x44 .. +0x4c - the HUD plane is z 6.0) */
    DWORD c = (DWORD)(DWORD_PTR)ctx, base = klh_rd32(c + 8), inst = base ? klh_rd32(base + 4 * index) : 0;
    if (!inst || !klh_rd(inst + 0x28, out, 14 * sizeof(float))) memset(out, 0, 14 * sizeof(float));
}

static void klu_draw_ours(void *el, void *ctx, void *cam, DWORD n_before, DWORD n_stock)
{
    const DWORD *cnt = (const DWORD *)ctx + 1;    /* ctx+4: the number of instances appended this frame (the live argument: read directly) */
    int i, want, first_text = 1, first_pic = 1, live;
    if (!klu_draw_on || !ctx || (DWORD)(DWORD_PTR)el != klu_r.elem) return;
    if (!TryEnterCriticalSection(&klu_cs)) { InterlockedIncrement(&klu_n_try); return; }    /* the tick is changing a text: this frame goes without ours */
    /* the canary (section 5b): the only two checked reads of this call. The objects of a level go together; when the
       OSD or text 0 no longer shows its vtable nothing of ours is touched in this frame */
    live = klu_draw_on && klu_r.made && !klu_r.fault && klh_rd32(klu_r.osd) == KLU_OSD_VT && klh_rd32(klu_r.t[0].obj) == KLU_TEXT_VT;
    if (!live && klu_draw_on) InterlockedIncrement(&klu_n_refused);
    if (live) {
        want = klu.probe && InterlockedExchange(&klu_probe_want, 0);
        if (want) { memset(&klu_pr, 0, sizeof klu_pr); klu_pr.nstock = (LONG)(n_stock - n_before); if (n_stock > n_before) klu_inst(ctx, n_before, klu_pr.stock); }
        for (i = 0; i < klu_r.npic; i++) {
            const struct klu_picq *p = &klu_r.pic[i]; DWORD a = *cnt;
            if (klu_pic(el, ctx, i, p->n, p->x, p->y, p->w, p->h, p->argb, p->layer)) InterlockedIncrement(&klu_n_pic); else InterlockedIncrement(&klu_n_picno);
            if (want && first_pic) { DWORD b = *cnt; first_pic = 0; klu_pr.npic = (LONG)(b - a); if (b > a) klu_inst(ctx, a, klu_pr.pic); }
        }
        for (i = 0; i < KLU_NTEXT; i++) {
            const struct klu_text *t = &klu_r.t[i]; DWORD a; int ok;
            if (!t->on || !t->obj) continue;
            a = *cnt;
            float ty = t->y + (klu.fontset && !t->cen ? KLU_BASE_OLD - klu_cap_of(t->fnt) : 0.0f);      /* the baseline stays where it was; cen: y is the capitals' top */
            float tx = t->x + (klu.fontset && t->fnt == KLU_FNT_LABEL && !t->plain ? ((t->style & 15) == 2 ? KLU_TRACK : (t->style & 15) == 4 ? KLU_TRACK * 0.5f : 0.0f) : 0.0f);      /* the baked tracking follows the LAST letter too */
            if (klu.draw == 2) ok = klu_draw_stock(el, ctx, cam, t->obj, t->shadow, tx, ty);
            else {
                if (klu.shadow && t->shadow && !t->noshadow) { float so = t->fnt == KLU_FNT_BIG ? 2.0f : 1.0f; klu_draw_one(t->shadow, ctx, cam, tx + so, ty + so); }     /* 0xbbe4ec / 0xbbe4f0 = 2.0 (the stock offset): 2 px for the big font only, 1 px for the small ones (2026-10-12: the black drops were heavy at the small sizes) */
                ok = klu_draw_one(t->obj, ctx, cam, tx, ty);
            }
            if (ok) InterlockedIncrement(&klu_n_draw); else InterlockedIncrement(&klu_n_refused);
            if (want && first_text && ok) { DWORD b = *cnt; first_text = 0; klu_pr.nours = (LONG)(b - a); if (b > a) klu_inst(ctx, b - 1, klu_pr.ours); }   /* the last one appended = the text itself (the shadow comes first with Draw=1) */
        }
        if (want) InterlockedExchange(&klu_probe_ready, 1);
        if ((LONG)*cnt > klu_n_maxinst) InterlockedExchange(&klu_n_maxinst, (LONG)*cnt);      /* S4: DrawChunk has no capacity test; the largest count seen after our draws */
    }
    if (klu.pictest && live) {             /* TEST [HUD] PicTest=1: are pictures drawn, how large, anchored where, tinted?
                                                      A = UI_White (picture 181) 200 x 24 px in coral, asked for at (400, 500)
                                                      B = UI_White with the clock element's own record size, chalk, at (700, 500)
                                                      C = the car icon (170) with the element's own size, white, at (900, 500) */
        static DWORD said; DWORD now = GetTickCount(); int a, b, c2;
        a = klu_pic(el, ctx, KLU_NPIC, 181, 400.0f, 500.0f, 200.0f, 24.0f, KLU_C_CORAL, klu.layer);
        b = klu_pic(el, ctx, KLU_NPIC + 1, 181, 700.0f, 500.0f, 0, 0, KLU_C_CHALK, klu.layer);
        c2 = klu_pic(el, ctx, KLU_NPIC + 2, 170, 900.0f, 500.0f, 0, 0, 0xffffffffu, klu.layer);
        if (klu.log && now - said >= 5000) { said = now; klog("hud: pictest: A (white 200x24 coral at 400,500, PicAnchor=%d) %d, B (white, own size, at 700,500) %d, C (car icon at 900,500) %d; 1 = DrawChunk called", klu.anchor, a, b, c2); }
    }
    LeaveCriticalSection(&klu_cs);
}

/* klhud_tags.c (included after klhud_escape.c): the head tags; its render step runs after ours, its tick after the hide tick, its init at the end of klu_init */
static void klht_render(void *el, void *ctx, void *cam);
static void klsb_state_render(void *el, void *ctx, void *cam);      /* klhud_board2.c: [HUD] OnlineBoardState */
static void klht_tick(DWORD osd, const struct klb_snap *s, int show);
static void klht_init(void);
static void klht_reset(void);

/* slot 2 (Render(ctx, cam), thiscall ret 8) of the private vtable of the clock element: runs inside 0x8bf300's element loop */
static void klu_clock_face(void *el)
{   /* Dials. The clock's Update has just written this frame's digits into its text and shadow (elem+0x28 / +0x2c); the
       hijack test of run H1l showed a SetText here, right before the stock Render, is what gets drawn. Only while our
       HUD draws (klu_draw_on) and only on the element this part wrapped. */
    DWORD e = (DWORD)(DWORD_PTR)el, a, b;
    if (!klu.dials || !klu_draw_on || e != klu_r.elem) return;
    a = *(const DWORD *)(DWORD_PTR)(e + KLU_E_TEXT); b = *(const DWORD *)(DWORD_PTR)(e + KLU_E_TEXT + 4);
    if (!a || klh_rd32(a) != KLU_TEXT_VT) return;
    if (klu_r.watch) {
        ((klu_set1_t)(DWORD_PTR)KLH_VA(0x896e50))((void *)(DWORD_PTR)a, 0, (DWORD)(DWORD_PTR)" ");
        if (b && klh_rd32(b) == KLU_TEXT_VT) ((klu_set1_t)(DWORD_PTR)KLH_VA(0x896e50))((void *)(DWORD_PTR)b, 0, (DWORD)(DWORD_PTR)" ");
    } else if ((*(const DWORD *)(DWORD_PTR)(a + 0x14) & 0xffffff) != (KLU_C_CORAL & 0xffffff))
        ((klu_set1_t)(DWORD_PTR)KLH_VA(0x8a0a30))((void *)(DWORD_PTR)a, 0, KLU_C_CORAL);
}

static char __fastcall klu_render_elem(void *el, void *edx, void *ctx, void *cam)
{
    char r; DWORD n0, n1; (void)edx;
    InterlockedIncrement(&klu_n_call);
    n0 = ctx ? ((const DWORD *)ctx)[1] : 0;       /* the stock Render reads the same object two instructions on */
    klu_clock_face(el);
    if (klu.dials && klu_draw_on && (DWORD)(DWORD_PTR)el == klu_r.elem && klu_r.handle[113] && klu_r.handle[114] && klu_r.handle[170]) {
        /* M3: our escape dial stands for the stock escape line + vehicle icon (byte elem+0xbc, 0x81e142): off around the stock
           Render, put back after it (a heap byte of the element the game is rendering in this very call, as klu_draw_stock) */
        BYTE *esc = (BYTE *)(DWORD_PTR)((DWORD)(DWORD_PTR)el + KLU_E_ESCAPE), b = *esc;
        *esc = 0;
        r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLU_TIME_RENDER))(el, 0, ctx, cam);
        *esc = b;
    } else
        r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLU_TIME_RENDER))(el, 0, ctx, cam);
    n1 = ctx ? ((const DWORD *)ctx)[1] : 0;
    klu_draw_ours(el, ctx, cam, n0, n1);
    klsb_state_render(el, ctx, cam);                /* klhud_board2.c: the online end card when the outro element is absent ([HUD] OnlineBoardState) */
    klht_render(el, ctx, cam);                      /* klhud_tags.c: the tags over the heisters' heads (the stock element's first loop, run by the hook) */
    return r;
}

/* ---------------------------------------------------------------- the private vtable (main thread) */

#define KLU_PLIST_RENDER 0x005e60f0u
static char __fastcall klu_plist_render(void *el, void *edx, void *ctx, void *cam)
{
    (void)edx;
    if (klu_skip_list) return 1;                  /* not drawn: the same as the game's hide byte, but one the game cannot rewrite */
    return ((klu_render_t)(DWORD_PTR)KLH_VA(KLU_PLIST_RENDER))(el, 0, ctx, cam);
}

static void klu_plist_wrap(DWORD osd)
{
    DWORD el, cur;
    if (!klu.hidesrc || !(el = klh_rd32(osd + KLU_O_PLIST)) || !klh_rd(el, &cur, 4)) return;
    if (!klu_pvt_ready) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLU_PLIST_VT - 4), klu_pvt, sizeof klu_pvt) || klu_pvt[1 + 2] != KLU_PLIST_RENDER) { klu.hidesrc = 0; klog("hud: slot 2 of ZFAPlayerListDisplay is not %08lx: HideSrc is off", KLU_PLIST_RENDER); return; }
        klu_pvt[1 + 2] = (DWORD)(DWORD_PTR)klu_plist_render; klu_pvt_ready = 1;
    }
    if (cur == (DWORD)(DWORD_PTR)&klu_pvt[1]) return;
    if (cur == KLU_PLIST_VT) {
        DWORD vt = (DWORD)(DWORD_PTR)&klu_pvt[1];
        if (klh_data((void *)(DWORD_PTR)el, &vt, 4, "the stock player list's vtable (private copy, Render wrapped)") && klu.log) klog("hud: the stock player list (%08lx) now renders through a private vtable: skipped while our HUD stands", el);
    }
}


static int klu_is_plist(DWORD el)
{   /* the FA player list element: the stock vtable, or our private copy once klu_plist_wrap ([HUD] HideSrc) swapped it in
       (10-27 bench Q27_DD01ce3: the online tags waited at gate 2 for the whole round because only the stock one passed) */
    DWORD vt = klh_rd32(el);
    return el && (vt == KLU_PLIST_VT || (klu_pvt_ready && vt == (DWORD)(DWORD_PTR)&klu_pvt[1]));
}

static int klu_vtable_tick(DWORD osd)
{   /* -> 1 while the clock element's first dword is ours (installed here when it shows the stock one) */
    static LONG told; DWORD el, vt, cur;
    if (!(el = klh_rd32(osd + KLU_O_TIME)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klu_evt_ready) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLU_TIME_VT - 4), klu_evt, sizeof klu_evt)) return 0;
        if (klu_evt[1 + 2] != KLU_TIME_RENDER) {
            if (!InterlockedExchange(&told, 1)) klog("hud: slot 2 of ZFATimeDisplay is %08lx, not %08lx: the HUD is off", klu_evt[1 + 2], KLU_TIME_RENDER);
            return 0;
        }
        klu_evt[1 + 2] = (DWORD)(DWORD_PTR)klu_render_elem;
        klu_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klu_evt[1];
    if (cur == vt) { klu_r.elem = el; return 1; }
    if (cur != KLU_TIME_VT) {
        if (!InterlockedExchange(&told, 1)) klog("hud: the element at osd+0x10cc = %08lx has vtable %08lx, not ZFATimeDisplay's: the HUD is off", el, cur);
        return 0;
    }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the clock element's vtable (private copy, slot 2 wrapped)")) return 0;
    klu_r.elem = el;
    if (klu.log) klog("hud: element %08lx (the clock) now renders through the private vtable (slot 2 -> klu_render_elem: the stock 0x81e090 first, then ours)", el);
    return 1;
}

/* ---------------------------------------------------------------- making the texts (main thread) */

static int klu_rdata_ptr(DWORD v)
{   /* a vtable pointer of the game: read-only bytes of kl2.exe's image */
    char sec[9];
    return v && klh_kind((const void *)(DWORD_PTR)KLH_VA(v), 4, sec) == 'r';
}

static void klu_set(DWORD obj, DWORD off, DWORD v)
{
    DWORD fn = klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + off));
    ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, v);
}

static float klu_cap_of(int f) { return f >= 0 && f < KLU_NFONT ? klu.cap[f] : klu.cap[0]; }

static DWORD klu_font_of(const struct klu_text *t)
{   /* the font object of a text: its role's (Fonts=1), else the old rule (TotalFont: the headline font) */
    if (klu.fontset) return klu_r.fonts[t->fnt >= 0 && t->fnt < KLU_NFONT ? t->fnt : 0];
    return t->big && klu_r.bigfont ? klu_r.bigfont : klu_r.font;
}

static float klu_cen(float centre, int f)
{   /* the y to give a text of font f so that its capitals' middle lies on `centre` (whole pixels: the ink spans y .. y + cap) */
    return (float)floor(centre - klu_cap_of(f) * 0.5f + 0.5f);
}

static DWORD klu_make_obj(DWORD tmpl, DWORD font, int style, DWORD colour, int layer, char why[160])
{
    DWORD obj, vt = 0;
    obj = ((klu_create_t)(DWORD_PTR)KLH_VA(KLU_CREATE))((void *)(DWORD_PTR)tmpl, 0, klu_r.parent, KLU_TAG, 0, 0, 0, 0);
    if (!obj) { strcpy(why, "the template's create-child returned 0"); return 0; }
    if (!klh_rd(obj, &vt, 4) || vt != KLU_TEXT_VT) { snprintf(why, 160, "the created object %08lx has vtable %08lx, not ZCHAROBJ's", obj, vt); return 0; }
    klu_set(obj, KLU_VT_STYLE, (DWORD)style); klu_set(obj, KLU_VT_COLOUR, colour); klu_set(obj, KLU_VT_FONT, font);
    klu_set(obj, KLU_VT_LAYER, (DWORD)layer); klu_set(obj, KLU_VT_TEXT, (DWORD)(DWORD_PTR)"");
    return obj;
}

/* the crew list's texts at the list's place (klu_r.cx / cy, klu.crew_w): the corner list, or - while klu_r.card - the Tab card in the
   middle of the screen (klu_compose moves the place for its call and puts the numbers back; the texts stay where this put them) */
static void klu_place_crew(void)
{
    float x0 = klu_r.cx, x1 = klu_r.cx + klu.crew_w, y; int i;
    klu_r.t[KLU_T_HEAD].x = x0; klu_r.t[KLU_T_HEAD].y = klu_r.cy;
    klu_r.t[KLU_T_COUNT].x = x1; klu_r.t[KLU_T_COUNT].y = klu_r.cy;
    for (i = 0; i < KLU_ROWS; i++) {
        y = klu_r.cy + klu.yoff + klu.row * i;
        klu_r.t[KLU_T_NAME(i)].x = x0 + klu.padx; klu_r.t[KLU_T_CASH(i)].x = x1 - klu.padx; klu_r.t[KLU_T_TABST(i)].x = x0 + klu.crew_w * KLU_CARD_ST;
        if (klu.fontset) {                                   /* centred on the block's middle (the block: y - blockup, blockh high) */
            float rc = y + klu.blockh * 0.5f - klu.blockup;
            klu_r.t[KLU_T_NAME(i)].y = klu_cen(rc, KLU_FNT_NAME); klu_r.t[KLU_T_CASH(i)].y = klu_cen(rc, KLU_FNT_SMALL); klu_r.t[KLU_T_TABST(i)].y = klu_cen(rc, KLU_FNT_LABEL) + KLU_CARD_STDY;
        } else klu_r.t[KLU_T_NAME(i)].y = klu_r.t[KLU_T_CASH(i)].y = klu_r.t[KLU_T_TABST(i)].y = y;
    }
}

/* the places of every text of this level (1280 x 720 virtual pixels); re\hud_hook.md 3 has the same numbers as a table */
static void klu_layout(void)
{
    float inset = 0.05f, y; int i, k;
    klh_rd((DWORD_PTR)KLH_VA(KLU_INSET), &inset, 4);
    if (!(inset >= 0 && inset < 0.25f)) inset = 0.05f;
    klu_r.cx = klu.crew_x >= 0 ? klu.crew_x : 1280.0f * inset;
    klu_r.cy = klu.crew_y >= 0 ? klu.crew_y : 720.0f * inset;
    klu_r.mx = klu.money_x >= 0 ? klu.money_x : 1280.0f - 1280.0f * inset;
    klu_r.wy = 720.0f * inset + 30.0f;                                       /* Dials: the watch's middle (66 at the game's inset) */
    klu_r.ry = klu.round_y >= 0 ? klu.round_y : 720.0f * inset + (klu.dials ? 72.0f : 58.0f);      /* under the clock's two lines (y, y + 28), or under the watch */
    klu_r.my = klu.money_y >= 0 ? klu.money_y : 720.0f * inset + (klu.dials ? (klu.draft ? KLU_D_MONEY_DY : 100.0f) : 87.0f);   /* run T1: the 33 px total stood in the round line - 14 lower under Draft */     /* 123 at the game's inset = the draft's 9.6 % of the width */
    for (i = 0; i < KLU_NTEXT; i++) { klu_r.t[i].style = KLU_STYLE_LEFT; klu_r.t[i].want_colour = KLU_C_CHALK; }
    klu_r.t[KLU_T_HEAD].want_colour = KLU_C_CORAL;
    klu_r.t[KLU_T_COUNT].style = KLU_STYLE_RIGHT;
    for (i = 0; i < KLU_ROWS; i++) { klu_r.t[KLU_T_CASH(i)].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_TABST(i)].style = KLU_STYLE_CENTRE; }
    klu_place_crew();
    klu_r.t[KLU_T_ROUND].x = klu_r.mx; klu_r.t[KLU_T_ROUND].y = klu_r.ry; klu_r.t[KLU_T_ROUND].style = KLU_STYLE_RIGHT;
    if (klu.draft) klu_r.t[KLU_T_ROUND].want_colour = klu.fontset ? KLU_C_CHALK : KLU_C_CORAL;      /* the draft's CSS: .clock .round { color: chalk } (S5 had coral) */
    for (k = 0; k < 3; k++) {
        y = klu_r.my + (k == 0 ? 0.0f : klu.draft ? (klu.wstyle ? KLU_W_MLINE0 : KLU_D_MLINE0) + KLU_D_MLINE * (k - 1) : 40.0f + 24.0f * (k - 1));            /* TOTAL, the bar under it, LOOT, REWARDS (the quiet draft: +0 / +34 / +52; stock-font layout +0 / +40 / +64) */
        klu_r.t[KLU_T_MLABEL(k)].x = klu_r.mx - klu.money_w; klu_r.t[KLU_T_MLABEL(k)].y = y; klu_r.t[KLU_T_MLABEL(k)].want_colour = KLU_C_CORAL;
        klu_r.t[KLU_T_MVALUE(k)].x = klu_r.mx; klu_r.t[KLU_T_MVALUE(k)].y = y; klu_r.t[KLU_T_MVALUE(k)].style = KLU_STYLE_RIGHT;
        klu_r.t[KLU_T_MVALUE(k)].want_colour = k == 0 ? KLU_C_GREENHI : KLU_C_GREEN;
    }
    klu_r.t[KLU_T_MVALUE(0)].big = klu.totalfont;
    klu_r.t[KLU_T_ESC].x = klu_r.mx - 6.0f; klu_r.t[KLU_T_ESC].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_ESC].want_colour = KLU_C_CHALK;
    klu_r.t[KLU_T_KILL].x = klu_r.mx; klu_r.t[KLU_T_KILL].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_KILL].want_colour = KLU_C_GREEN;
    klu_r.t[KLU_T_KILL].y = klu_r.my + (klu.draft ? (klu.wstyle ? KLU_W_MLINE0 : KLU_D_MLINE0) + KLU_D_MLINE * 2.0f : 88.0f);      /* one line under REWARDS */
    klu_r.t[KLU_T_DEATH].x = 640.0f; klu_r.t[KLU_T_DEATH].y = 150.0f; klu_r.t[KLU_T_DEATH].style = KLU_STYLE_CENTRE; klu_r.t[KLU_T_DEATH].fnt = KLU_FNT_NAME; klu_r.t[KLU_T_DEATH].want_colour = KLU_C_CORAL;   /* GUESS: top centre, under the watch row; position not seen live */
    klu_r.t[KLU_T_ESC].y = klu_r.t[KLU_T_KILL].y + 18.0f + KLU_ESC_GAP + KLU_ESC_TOFF;      /* the van card's middle; the text is centred on it below */
    if (klu.fontset) {                                   /* TYPE: which font each text takes (see the block at KLU_NFONT) */
        for (i = 0; i < KLU_NTEXT; i++) klu_r.t[i].fnt = KLU_FNT_NAME;
        klu_r.t[KLU_T_HEAD].fnt = KLU_FNT_LABEL; klu_r.t[KLU_T_COUNT].fnt = KLU_FNT_SMALL; klu_r.t[KLU_T_ROUND].fnt = KLU_FNT_LABEL;
        for (i = 0; i < KLU_ROWS; i++) {                 /* the row's text is centred on its block's middle (klu_place_crew) */
            klu_r.t[KLU_T_NAME(i)].fnt = KLU_FNT_NAME; klu_r.t[KLU_T_CASH(i)].fnt = KLU_FNT_SMALL; klu_r.t[KLU_T_TABST(i)].fnt = KLU_FNT_LABEL;
            klu_r.t[KLU_T_NAME(i)].cen = klu_r.t[KLU_T_CASH(i)].cen = klu_r.t[KLU_T_TABST(i)].cen = 1;
        }
        klu_place_crew();
        for (k = 0; k < 3; k++) { klu_r.t[KLU_T_MLABEL(k)].fnt = KLU_FNT_LABEL; klu_r.t[KLU_T_MVALUE(k)].fnt = k == 0 ? KLU_FNT_BIG : KLU_FNT_NAME; }
        klu_r.t[KLU_T_KILL].fnt = KLU_FNT_LABEL; klu_r.t[KLU_T_ESC].fnt = KLU_FNT_NAME; klu_r.t[KLU_T_ESC].cen = 1; klu_r.t[KLU_T_ESC].y = klu_cen(klu_r.t[KLU_T_ESC].y, KLU_FNT_NAME);
        klu_r.t[KLU_T_WEAP + 0].fnt = KLU_FNT_NAME; klu_r.t[KLU_T_WEAP + 1].fnt = KLU_FNT_SMALL;      /* the draft's dial: on-gun count 1.6cqw = 20.5 px (the NAME font), off-gun 1.15cqw */ klu_r.t[KLU_T_WEAP + 2].fnt = KLU_FNT_LABEL;
    }
    klu_r.t[KLU_T_WEAP + 0].style = klu_r.t[KLU_T_WEAP + 1].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_WEAP + 2].style = klu.wstyle ? KLU_STYLE_RIGHT : KLU_STYLE_CENTRE;
    klu_r.t[KLU_T_WEAP + 3].style = klu_r.t[KLU_T_WEAP + 4].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_WEAP + 3].fnt = klu_r.t[KLU_T_WEAP + 4].fnt = KLU_FNT_LABEL;      /* klhud_weapon.c: the counts right-aligned, the label centred under the disc */
    {   /* the Grid labels: their style is fixed when the object is made (klu_grid fills the same order) */
        int gs[KLU_NGRID] = { KLU_STYLE_LEFT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_LEFT, KLU_STYLE_RIGHT, KLU_STYLE_LEFT, KLU_STYLE_RIGHT };
        for (i = 0; i < KLU_NSWEEP; i++) gs[10 + i] = klu_sweep[i];
        for (i = 0; i < KLU_NGRID; i++) { klu_r.t[KLU_T_GRID + i].plain = 1; klu_r.t[KLU_T_GRID + i].style = gs[i]; klu_r.t[KLU_T_GRID + i].want_colour = KLU_C_CORAL; }
    }
}

/* WHICH LOOK THIS LEVEL WAS BAKED WITH (cloud session 2026-10-12, re\hud_cloud_review.md W2; tested off-game by klwatch_test.c 'look').
   tools\kl_hud.py bakes slot 112 as the dry stroke 256 x 32 (--watch 0) or the dial's wear 128 x 128 (--watch 1); the OSD's picture table
   holds {handle, u16 width, u16 height} per slot at osd+0x3ec + 12 n (re\hud.md 1, filled by 0x5e3810 from the texture's info).
   When the level tells, ITS look is drawn (a hook and a level that disagree would draw the wear texture as strike-throughs or rings of the
   wrong width - the watch review's MUST 2); [HUD] WatchStyle decides only when slot 112 is empty or of another size. Called before the
   layout of the texts, so every part of the level sees one look. -> 1 watch bake, 0 old bake, -1 not known */
#define KLU_O_PICTAB     0x3ec
static int klu_baked_look(DWORD osd)
{
    DWORD h = 0; WORD wh[2] = { 0, 0 };
    if (!osd || !klh_rd(osd + KLU_O_PICTAB + 12u * 112u, &h, 4) || !h || !klh_rd(osd + KLU_O_PICTAB + 12u * 112u + 4u, wh, 4)) return -1;
    if (wh[0] == 128 && wh[1] == 128) return 1;
    if (wh[0] == 256 && wh[1] == 32) return 0;
    return -1;
}

static void klu_choose_look(DWORD osd)
{
    static int said = -2; int b = klu_baked_look(osd), now = b >= 0 ? b : klu.wini;
    if (now != klu.wini || said != b) {
        if (klu.log && b >= 0 && now != klu.wini) klog("hud: watch: [HUD] WatchStyle=%d but this level is baked with the %s look (slot 112 %s): the %s look is drawn for it", klu.wini, b ? "WATCH" : "OLD", b ? "128 x 128" : "256 x 32", b ? "watch" : "old");
        else if (klu.log > 1) klog("hud: watch: look %d (WatchStyle=%d, the level's bake %s)", now, klu.wini, b < 0 ? "not told by slot 112" : b ? "watch" : "old");
        said = b;
    }
    klu.wstyle = now;
}

static int klu_make_all(DWORD osd)
{
    static const BYTE refobj_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 };       /* 0x8ccde0 */
    static const BYTE parent_code[8]  = { 0x8b, 0x41, 0x50, 0x85, 0xc0, 0x75, 0x01, 0xc3 };                   /* 0x598460 */
    static const BYTE create_code[8]  = { 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x56, 0x8b, 0xf1 };                   /* 0x817810 */
    static const BYTE text_code[8]    = { 0x53, 0x8b, 0x5c, 0x24, 0x08, 0x56, 0x8b, 0xf1 };                   /* 0x896e50 SetText */
    static const BYTE draw_code[8]    = { 0x0f, 0xb6, 0x91, 0x87, 0x00, 0x00, 0x00, 0x8b };                   /* 0x5a6d40 Draw */
    static const BYTE render_code[8]  = { 0x83, 0xec, 0x48, 0x56, 0x8b, 0xf1, 0x8b, 0x0d };                   /* 0x81e090 sub esp,0x48 ; push esi ; mov esi,ecx ; mov ecx,[..] */
    static const BYTE place_code[8]   = { 0x8b, 0x44, 0x24, 0x08, 0x8b, 0xd1, 0xd9, 0x42 };                   /* 0x5a3e90 mov eax,[esp+8] ; mov edx,ecx ; fld [edx+0x18] */
    static const struct { DWORD off, fn; } slots[7] = { { KLU_VT_CREATE, 0x817810 }, { KLU_VT_DRAW, KLU_DRAW }, { KLU_VT_COLOUR, 0x8a0a30 },
                                                        { KLU_VT_STYLE, 0x41a470 }, { KLU_VT_LAYER, 0x514720 }, { KLU_VT_FONT, 0x641ba0 }, { KLU_VT_TEXT, 0x896e50 } };
    DWORD tref = 0, fref = 0, bref = 0, tmpl, font, big = 0, tvt = 0, fvt = 0; int i, k, n = 0, ns = 0; char why[160];
    klu_choose_look(osd);                          /* W2: before the layout reads klu.wstyle */
    if (!klu_same_code(KLU_REFOBJ, refobj_code, sizeof refobj_code) || !klu_same_code(KLU_PARENT, parent_code, sizeof parent_code) ||
        !klu_same_code(KLU_CREATE, create_code, sizeof create_code) || !klu_same_code(0x896e50, text_code, sizeof text_code) || !klu_same_code(KLU_DRAW, draw_code, sizeof draw_code) ||
        !klu_same_code(KLU_TIME_RENDER, render_code, sizeof render_code) || !klu_same_code(KLU_PLACE, place_code, sizeof place_code)) {
        klog("hud: osd %08lx: a routine of the text path is not the one this build knows (0x8ccde0 / 0x598460 / 0x817810 / 0x896e50 / 0x5a6d40 / 0x81e090 / 0x5a3e90): nothing is made", osd); return 0;
    }
    for (k = 0; k < 7; k++) if (klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + slots[k].off)) != slots[k].fn) {
        klog("hud: osd %08lx: ZCHAROBJ vtable +0x%lx is %08lx, not %08lx: nothing is made", osd, slots[k].off, klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + slots[k].off)), slots[k].fn); return 0;
    }
    if (!klh_rd(osd + KLU_O_TEMPLATE, &tref, 4) || !klh_rd(osd + KLU_O_FONT, &fref, 4) || !tref || !fref) { klog("hud: osd %08lx: no template / font REF (+0xd4c %08lx, +0xd54 %08lx): nothing is made", osd, tref, fref); return 0; }
    tmpl = (DWORD)(DWORD_PTR)((void *(__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLU_REFOBJ))(tref);
    font = (DWORD)(DWORD_PTR)((void *(__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLU_REFOBJ))(fref);
    if (!tmpl || !font || !klh_rd(tmpl, &tvt, 4) || tvt != KLU_TEXT_VT || !klh_rd(font, &fvt, 4) || !klu_rdata_ptr(fvt)) {
        klog("hud: osd %08lx: template REF %08lx -> %08lx (vtable %08lx), font REF %08lx -> %08lx (vtable %08lx): not a ZCHAROBJ template and a font object: nothing is made", osd, tref, tmpl, tvt, fref, font, fvt); return 0;
    }
    if (klu.totalfont) {                         /* the headline font: must be the same class of object as the FA font, else the FA font */
        DWORD bvt = 0;
        if (klh_rd(osd + KLU_O_BIGFONT, &bref, 4) && bref) big = (DWORD)(DWORD_PTR)((void *(__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLU_REFOBJ))(bref);
        if (!big || !klh_rd(big, &bvt, 4) || bvt != fvt) { klog("hud: osd %08lx: the headline font (+0xd50 REF %08lx -> %08lx, vtable %08lx against the FA font's %08lx) is not usable: TOTAL in the FA font", osd, bref, big, bvt, fvt); big = 0; }
    }
    klu_r.parent = (DWORD)(DWORD_PTR)((void *(__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLU_PARENT))((void *)(DWORD_PTR)klh_rd32(tmpl + 4), 0);
    if (!klu_r.parent) { klog("hud: osd %08lx: the template %08lx has no parent node (0x598460 gave 0): nothing is made", osd, tmpl); return 0; }
    klu_r.tmpl = tmpl; klu_r.font = font; klu_r.bigfont = big;
    for (i = 0; i < KLU_NFONT; i++) klu_r.fonts[i] = font;
    if (klu.fontset) {                           /* the four roles: each REF must resolve to an object of the FA font's class, else that role keeps the FA font */
        for (i = 0; i < KLU_NFONT; i++) {
            DWORD ref = 0, obj = 0, ovt = 0;
            if (klu.fofs[i] && klh_rd(osd + klu.fofs[i], &ref, 4) && ref) obj = (DWORD)(DWORD_PTR)((void *(__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLU_REFOBJ))(ref);
            if (obj && klh_rd(obj, &ovt, 4) && ovt == fvt) klu_r.fonts[i] = obj;
            else if (klu.log) klog("hud: osd %08lx: font role %d (+0x%lx REF %08lx -> %08lx, vtable %08lx against %08lx) is not usable: the FA font", osd, i, (DWORD)klu.fofs[i], ref, obj, ovt, fvt);
        }
        if (klu_r.fonts[KLU_FNT_LABEL] == font && klu_r.fonts[KLU_FNT_SMALL] != font) {      /* +0xd5c is no font here: the labels take the small figures' */
            klu_r.fonts[KLU_FNT_LABEL] = klu_r.fonts[KLU_FNT_SMALL]; klu.cap[KLU_FNT_LABEL] = klu.cap[KLU_FNT_SMALL];
            klog("hud: fonts: the label role (+0x%lx) is no font object: labels take the small role's font, cap %.0f", (DWORD)klu.fofs[KLU_FNT_LABEL], klu.cap[KLU_FNT_LABEL]);
        }
        for (i = 0; i < KLU_NFONT; i++) for (k = i + 1; k < KLU_NFONT; k++)
            if (klu_r.fonts[i] == klu_r.fonts[k]) klog("hud: fonts: WARNING roles %d and %d resolve to ONE object %08lx: their baked sizes cannot differ (a role offset is wrong, or this level's fonts are the stock ones)", i, k, klu_r.fonts[i]);
        if (klu.log) klog("hud: fonts: names %08lx (+0x%lx), big %08lx (+0x%lx), labels %08lx (+0x%lx), small %08lx (+0x%lx); caps %.0f %.0f %.0f %.0f", klu_r.fonts[0], (DWORD)klu.fofs[0], klu_r.fonts[1], (DWORD)klu.fofs[1], klu_r.fonts[2], (DWORD)klu.fofs[2], klu_r.fonts[3], (DWORD)klu.fofs[3], klu.cap[0], klu.cap[1], klu.cap[2], klu.cap[3]);
    }
    klu_layout();
    for (i = 0; i < KLU_NTEXT; i++) {
        struct klu_text *t = &klu_r.t[i];
        if (i >= KLU_T_GRID && i < KLU_T_WEAP && !klu.grid) continue;
        if (i >= KLU_T_WEAP && i < KLU_T_KILL && !klu.weapon) continue;
        if (i >= KLU_T_TABST(0) && !klu.tabcard) continue;     /* the Tab card's status column */
        t->colour = t->want_colour;
        if (!(t->obj = klu_make_obj(tmpl, klu_font_of(t), t->style, t->colour, klu.layer, why))) { klog("hud: osd %08lx: text %d: %s; the HUD stands down for this level", osd, i, why); return 0; }
        n++;
        if (klu.shadow && (!t->plain || klu.draw == 2)) {      /* Draw=2: the stock Render draws a pair, so the Grid labels get a shadow too */
            if (!(t->shadow = klu_make_obj(tmpl, klu_font_of(t), t->style, t->fnt == KLU_FNT_BIG ? KLU_SHADOW_RGB : KLU_SHADOW_SMALL, klu.layer - 1, why))) { klog("hud: osd %08lx: shadow %d: %s; the HUD stands down for this level", osd, i, why); return 0; }
            t->shcol = t->fnt == KLU_FNT_BIG ? KLU_SHADOW_RGB : KLU_SHADOW_SMALL; ns++;
        }
    }
    if (klu.log) klog("hud: osd %08lx, %d texts + %d shadows made (template %08lx, font %08lx, headline font %08lx, parent %08lx); crew list at (%.0f, %.0f) %.0f wide, %.0f px a row; round line right-aligned at (%.0f, %.0f); money box right edge %.0f, top %.0f, %.0f wide; layer %d; Draw=%d",
                      osd, n, ns, tmpl, font, big, klu_r.parent, klu_r.cx, klu_r.cy, klu.crew_w, klu.row, klu_r.mx, klu_r.ry, klu_r.mx, klu_r.my, klu.money_w, klu.layer, klu.draw);
    return 1;
}

/* ---------------------------------------------------------------- the data (main thread, under the lock) */

static void klu_dollars(char *out, int cap, long v)
{   /* $1,234,567 */
    char d[24], *p = d + sizeof d - 1; unsigned long u = v < 0 ? (unsigned long)-v : (unsigned long)v; int k = 0;
    *p = 0;
    do { if (k && k % 3 == 0) *--p = ','; *--p = (char)('0' + u % 10); u /= 10; k++; } while (u);
    snprintf(out, cap, "%s$%s", v < 0 ? "-" : "", p);
}

static void klu_cash(char *out, int cap, long v)
{   /* the crew rows: $540K, $1.2M (the draft); CashShort=0 = in full */
    unsigned long u = v < 0 ? (unsigned long)-v : (unsigned long)v;
    if (!klu.cashshort || u < 1000) { klu_dollars(out, cap, v); return; }
    if (u >= 1000000) snprintf(out, cap, "%s$%lu.%luM", v < 0 ? "-" : "", u / 1000000, (u % 1000000) / 100000);
    else snprintf(out, cap, "%s$%luK", v < 0 ? "-" : "", u / 1000);
}

/* klhud_board2.c (the round-over scoreboard) lends the tick's picture helpers (klu_outline / klu_arc / klu_dabs) its own queue: while klu_addpic_q is set, klu_addpic writes there (main thread only, set and cleared around the calls) */
static struct klu_picq *klu_addpic_q; static int *klu_addpic_n, klu_addpic_cap;

static void klu_addpic(int n, float x, float y, float w, float h, DWORD argb, int layer)
{
    struct klu_picq *p;
    if (klu_addpic_q) {
        if (*klu_addpic_n >= klu_addpic_cap || w <= 0 || h <= 0) return;
        p = &klu_addpic_q[(*klu_addpic_n)++];
        p->n = n; p->x = x; p->y = y; p->w = w; p->h = h; p->argb = argb; p->layer = layer;
        return;
    }
    if (klu_r.npic >= KLU_NPIC) {              /* review 2026-10-12 SHOULD 4: say it once, the late parts (weapon label, pop-ups) are what is lost */
        static int said; if (!said && w > 0 && h > 0) { said = 1; klog("hud: the picture queue is full (%d): later pictures are dropped this frame", KLU_NPIC); }
        return;
    }
    if (w <= 0 || h <= 0) return;
    p = &klu_r.pic[klu_r.npic++];
    p->n = n; p->x = x; p->y = y; p->w = w; p->h = h; p->argb = argb; p->layer = layer;
}

static void klu_outline(float x, float y, float w, float h, DWORD argb, int layer)
{   /* four 1 px bars */
    klu_addpic(181, x, y, w, 1.0f, argb, layer); klu_addpic(181, x, y + h - 1.0f, w, 1.0f, argb, layer);
    klu_addpic(181, x, y, 1.0f, h, argb, layer); klu_addpic(181, x + w - 1.0f, y, 1.0f, h, argb, layer);
}

/* RINGS AS ONE PAINTED STROKE (2026-10-12; the owner after run S1: 'i dont want the circles to have that circle circle' - the
   rings were strings of round dabs). Every number here is tools/kl_hud.py's (ARC_N, ARC_KR, ARC_FAM, RING_STROKE). A ring is
   KLU_ARC_N = 3 baked slices of 120 degrees, clockwise from the top: each is a square texture that holds the WHOLE ring's bounding
   square with only its slice painted (centre-line radius 0.40 of the side, stroke 0.23 of that radius in family A = pictures
   123 / 124 / 125: watch, escape dial, loot ring; 0.12 in family B = 126 / 185 / 190: weapon dial), so the slices drawn at the
   ring's square join into one ring; slice 0 has a round cap at 0 degrees and slice 2 at 360. What is left of the stroke at
   its MOVING end (the slice it stands in) is a run of overlapping round dabs (picture 113, ink 0.9 of its picture, spaced at
   most 1.5 px and a quarter of the stroke): a ring that is partly empty = the slices wholly inside the part that is left + ONE run of
   dabs, so the end can stand anywhere and the stroke has no gaps. Picture 115 = the thin track ring at the same radius.
   Worst case a frame (review S1, step 0.4 of the stroke, at most 2.5 px): the weapon ring about 45 (one dab run under 1/3 of a circle + its slices), the
   watch about 50 with its hand of 20 + hub, the escape dial about 28, the loot ring about 25 (drawn from the render slot, not queued): about 205 pictures a frame in all. */
#define KLU_ARC_N        3
#define KLU_ARC_KR       0.40f
#define KLU_DAB_PIC      113
#define KLU_DAB_INK      0.90f
#define KLU_TRACK_PIC    115
#define KLU_DAB_MAXSTEP  2.5f                 /* review S1: 0.4 of the stroke, at most 2.5 px (was 0.25 / 1.5): worst case ~200 pictures a frame */
static const int klu_arc_slot[2][KLU_ARC_N] = { { 123, 124, 125 }, { 126, 185, 190 } };
static const float klu_arc_ratio[2] = { 0.23f, 0.12f };
static const float klu_arc_ratio_w[2] = { 0.13f, 0.10f };   /* the watch look's strokes (tools/kl_hud.py ARC_FAM_NEW) */
#define KLU_TRACK_C      0xff4a4844u          /* the draft's faint track (#55524d on the dark disc), a touch darker */

static int klu_sink(void *clk, void *ctx, int n, float x, float y, float w, float h, DWORD argb, int layer)
{   /* clk NULL: the tick's queue; else the render slot's own call (the shared record slot KLU_NPIC) */
    if (!clk) { klu_addpic(n, x, y, w, h, argb, layer); return 1; }
    return klu_pic(clk, ctx, KLU_NPIC, n, x, y, w, h, argb, layer);
}

static int klu_arc_ok(int fam)
{
    int j;
    if (!klu_r.handle[KLU_DAB_PIC]) return 0;
    for (j = 0; j < KLU_ARC_N; j++) if (!klu_r.handle[klu_arc_slot[fam][j]]) return 0;
    return 1;
}

static void klu_dabs(void *clk, void *ctx, float cx, float cy, float r, float ta, float tb, float stroke, DWORD argb, int layer)
{   /* overlapping round dabs on the circle of radius r from fraction ta to tb (clockwise from the top), both ends included */
    float size = stroke / KLU_DAB_INK * 0.97f, len = r * 6.2831853f * (tb - ta), step = stroke * 0.4f; int k, n;      /* 0.97: soft edges compound, the dabs read fatter than the baked slices (review S2) */
    if (step > KLU_DAB_MAXSTEP) step = KLU_DAB_MAXSTEP;
    if (!(len > 0)) len = 0;
    n = (int)(len / step) + 1;
    for (k = 0; k <= n; k++) {
        float a = 6.2831853f * (ta + (tb - ta) * (float)k / (float)n);
        klu_sink(clk, ctx, KLU_DAB_PIC, cx + r * (float)sin(a) - size * 0.5f, cy - r * (float)cos(a) - size * 0.5f, size, size, argb, layer);
    }
}

static void klu_arc(void *clk, void *ctx, float cx, float cy, float r, int fam, float t0, float t1, DWORD argb, int layer)
{   /* the part of the ring from fraction t0 to t1 (clockwise from the top; 0 .. 1) as one stroke */
    float D = r / KLU_ARC_KR, stroke = (klu.wstyle ? klu_arc_ratio_w[fam] : klu_arc_ratio[fam]) * r, cur; int j;
    if (t0 < 0) t0 = 0;
    if (t1 > 1.0f) t1 = 1.0f;
    if (!(t1 > t0)) return;
    if (!klu_arc_ok(fam)) {                                    /* review S4: a level baked without the slices (hud_x2 .. x5): the whole stroke as dabs, if there are dabs */
        if (klu_r.handle[KLU_DAB_PIC]) klu_dabs(clk, ctx, cx, cy, r, t0, t1, stroke, argb, layer);
        return;
    }
    cur = t0;
    for (j = 0; j < KLU_ARC_N; j++) {
        float a = (float)j / KLU_ARC_N, b = (float)(j + 1) / KLU_ARC_N;
        if (t0 <= a + 1e-4f && t1 >= b - 1e-4f) {              /* the slice lies wholly in the part: its picture */
            if (cur < a - 1e-4f) klu_dabs(clk, ctx, cx, cy, r, cur, a, stroke, argb, layer);
            klu_sink(clk, ctx, klu_arc_slot[fam][j], cx - D * 0.5f, cy - D * 0.5f, D, D, argb, layer);
            cur = b;
        }
    }
    if (cur < t1 - 1e-4f) klu_dabs(clk, ctx, cx, cy, r, cur, t1, stroke, argb, layer);
}

static void klu_track_f(void *clk, void *ctx, float cx, float cy, float r, int fam, DWORD argb, int layer)
{   /* the track under a ring's stroke: the old look = the thin ring at the same radius (picture 115); the watch look = a DIM FULL RING of the same family's slices (115 is the bezel there and must not be drawn as a track) */
    float D = r / KLU_ARC_KR;
    if (klu.wstyle) { klu_arc(clk, ctx, cx, cy, r, fam, 0.0f, 1.0f, argb, layer); return; }
    if (klu_r.handle[KLU_TRACK_PIC]) klu_sink(clk, ctx, KLU_TRACK_PIC, cx - D * 0.5f, cy - D * 0.5f, D, D, argb, layer);
}
static void klu_track(void *clk, void *ctx, float cx, float cy, float r, DWORD argb, int layer)
{   /* family A (the escape dial's, the loot ring's, the scoreboard's) */
    klu_track_f(clk, ctx, cx, cy, r, 0, argb, layer);
}

/* ================================================================ THE WATCH LOOK (2026-10-12; re\hud_hook.md section 14; the model is tools/kl_hud_watch.py,
   whose numbers these are; the preview draws that model with the level's real textures). [HUD] WatchStyle=1 (default) = this look, 0 = the look
   of the morning (the old textures: 112 dry stroke, 114 plain disc, 115 thin ring - the level must be baked with kl_hud.py --watch to match).
   Baked textures (alpha only, tinted here): 114 = the worn dial (disc radius 0.46875 of its side), 112 = wear, 115 = the bezel (pips out to 0.47 of
   its side, batons, the triangles at 12), 123..125 / 126 185 190 = the ring slices (stroke 0.13 / 0.10 of the centre-line radius). NOTHING OF IT
   HAS RUN IN THE GAME: the hands are runs of round dabs (113), bilinear, edges soft; the call order inside one layer is what lays hub over hand. */
#define KLW_DISC_K       0.46875f
#define KLW_BEZ_OUT      0.470f
#define KLW_R_CASE       36.2f
#define KLW_R_FACE       34.0f
#define KLW_R_BEZEL      33.0f
#define KLW_R_STROKE     26.0f                /* the time-left stroke's centre line, inside the pips' band */
#define KLW_ESC_K        (22.5f / 33.0f)      /* the escape dial is the watch at this scale (50 px across) */
#define KLW_ESC_DX       62.0f                /* its centre = the watch's - 62 (1150 beside the watch at 1212) */
#define KLW_C_CASE       0xe807080au
#define KLW_C_FACE       0xdc14161au
#define KLW_C_WEAR       0x4de9e6dfu
#define KLW_C_PIPS       0xb2e9e6dfu
#define KLW_C_PIPS_ESC   0x80e9e6dfu
#define KLW_C_CHALK      0xffe9e6dfu
#define KLW_C_BEZEL      0xff9a9a97u
#define KLW_C_RED        0xffe8303fu
#define KLW_C_ORANGE     0xffff8a2au
#define KLW_C_FACEDAB    0xff14161au
#define KLW_C_COUNTDOWN  0xfff0475au          /* the optional seconds hand: coral */

static void klu_dab_at(float x, float y, float ink, DWORD argb, int layer)
{   /* one round dab of ink diameter `ink` (picture 113's ink is 0.9 of the picture) */
    float s = ink / KLU_DAB_INK;
    klu_addpic(KLU_DAB_PIC, x - s * 0.5f, y - s * 0.5f, s, s, argb, layer);
}

static void klu_hand(float cx, float cy, float deg, float len, float tail, float w_tail, float w_base, float w_mid, float pos, float w_tip, float step, DWORD argb, int layer)
{   /* a hand as a run of overlapping dabs from -tail to len along `deg` (clockwise from 12); width (ink): w_tail behind the hub, w_base -> w_mid up to pos * len, -> w_tip */
    float t = deg * 0.017453293f, dx = (float)sin(t), dy = -(float)cos(t); int k, n = (int)((len + tail) / step + 0.5f);
    if (n < 1) n = 1;
    for (k = 0; k <= n; k++) {
        float s = -tail + (len + tail) * (float)k / (float)n, w;
        if (s < 0) w = w_tail;
        else if (s <= pos * len) w = w_base + (w_mid - w_base) * s / (pos * len);
        else w = w_mid + (w_tip - w_mid) * (s - pos * len) / (len * (1.0f - pos));
        klu_dab_at(cx + dx * s, cy + dy * s, w, argb, layer);
    }
}

static void klu_dial_base(float cx, float cy, float k, DWORD pips, int layer)
{   /* case, face, wear, bezel pips; layers never decrease with the call order (layer - 4 .. layer - 2) */
    float s;
    klu_addpic(114, cx - KLW_R_CASE * k / KLW_DISC_K * 0.5f, cy - KLW_R_CASE * k / KLW_DISC_K * 0.5f, KLW_R_CASE * k / KLW_DISC_K, KLW_R_CASE * k / KLW_DISC_K, KLW_C_CASE, layer - 4);
    s = KLW_R_FACE * k / KLW_DISC_K;
    klu_addpic(114, cx - s * 0.5f, cy - s * 0.5f, s, s, KLW_C_FACE, layer - 3);
    if (klu.wwear && klu_r.handle[112]) klu_addpic(112, cx - s * 0.5f, cy - s * 0.5f, s, s, KLW_C_WEAR, layer - 3);
    if (klu_r.handle[115]) { s = KLW_R_BEZEL * k / KLW_BEZ_OUT; klu_addpic(115, cx - s * 0.5f, cy - s * 0.5f, s, s, pips, layer - 2); }
}

static void klu_watch_look(float cx, float cy, float clock)
{   /* the round watch: the hour hand = the minutes left (30 degrees a minute), the sword hand = the seconds of the minute (6 a second, whole seconds),
       the stroke = from the sword's tip to 12 (the time left), both hands and the stroke red in the last minute */
    /* review 2026-10-12 MUST 1: both hands run CLOCKWISE (the angle is the time PLAYED): hour = 360 - minutes_left * 30, sword = (60 - seconds_left_in_minute) * 6;
       the stroke runs from the hour tip to 12 (= the minutes left, draining) while more than 60 s remain, from the sword tip to 12 (= the seconds left, 360 -> 0) in the last minute.
       At 1:00 the stroke goes from 30 to 360 degrees on purpose (the switch to the red last minute); GUESS that the owner accepts it. */
    float hdeg, sdeg, t0; int red = clock <= 60.0f, sl; DWORD sc;
    hdeg = (float)fmod(360.0f - clock / 60.0f * 30.0f + 720.0f * 100.0f, 360.0f);
    sl = (int)floor(clock); if (!red) sl %= 60;
    sdeg = (float)fmod((60 - sl) * 6.0f, 360.0f);
    if (red) t0 = (60 - sl) * 6.0f / 360.0f;                    /* 60 s -> 0 (a full ring), 1 s -> 354 degrees in */
    else { t0 = 1.0f - clock / 60.0f * 30.0f / 360.0f; if (t0 < 0.0f) t0 = 0.0f; }
    klu_dial_base(cx, cy, 1.0f, KLW_C_PIPS, klu.layer);
    sc = red ? KLW_C_RED : KLW_C_BEZEL;
    klu_arc(NULL, NULL, cx, cy, KLW_R_STROKE, 0, t0, 1.0f, sc, klu.layer - 1);
    klu_hand(cx, cy, hdeg, 19.0f, 3.6f, 2.6f, 3.0f, 3.0f, 0.8f, 0.8f, 1.0f, KLW_C_CHALK, klu.layer);                 /* the Mercedes hand: a shaft ... */
    {   float t = hdeg * 0.017453293f, rx = cx + (float)sin(t) * 19.0f * 0.62f, ry = cy - (float)cos(t) * 19.0f * 0.62f;
        klu_dab_at(rx, ry, 7.0f, KLW_C_CHALK, klu.layer);                                                            /* ... a ring at 62 % of it: a chalk dab ... */
        klu_dab_at(rx, ry, 3.7f, KLW_C_FACEDAB, klu.layer); }                                                        /* ... with the dial's colour over it */
    klu_hand(cx, cy, sdeg, 29.0f, 5.0f, 2.2f, 2.2f, 3.4f, 0.55f, 1.4f, 1.2f, red ? KLW_C_RED : KLW_C_CHALK, klu.layer);   /* the sword hand */
    if (klu.wseconds) klu_hand(cx, cy, (float)fmod(360.0f - (float)fmod(clock, 60.0f) * 6.0f, 360.0f), 30.4f, 6.0f, 1.1f, 1.1f, 1.1f, 0.5f, 1.1f, 1.1f, KLW_C_COUNTDOWN, klu.layer);
    klu_dab_at(cx, cy, 5.6f, KLW_C_CHALK, klu.layer);                                                                /* the hub */
    klu_dab_at(cx, cy, 2.2f, KLW_C_FACEDAB, klu.layer);
}

static void klu_escape_look(float cx, float cy, float left, int icon)
{
    float k = KLW_ESC_K;
    klu_dial_base(cx, cy, k, KLW_C_PIPS_ESC, klu.layer);
    klu_arc(NULL, NULL, cx, cy, KLW_R_STROKE * k, 0, 1.0f - left, 1.0f, KLW_C_ORANGE, klu.layer - 1);
    klu_addpic(icon, cx - 13.0f * KLU_VDISC, cy - 13.0f * KLU_VDISC, 26.0f * KLU_VDISC, 26.0f * KLU_VDISC, KLW_C_CHALK, klu.layer);      /* the watch chalk, as tools/kl_hud_watch.py draw_escape (C vs model check, cloud 2026-10-12) */
}


/* THE MONEY BAR in the watch look (cloud session 2026-10-12; the owner: 'sort the bar ... i want it to look good like' the draft; tested off-game by
   klwatch_test.c 'bar' against tools/kl_hud_watch.py draw_money_bar). The draft's `.money .frame` = a thin solid chalk frame, and its `.fill` = chalk
   painted with the dry filter, overhanging the frame above, below and on the left. Here: the frame = four bars of 181 (UI_White: crisp, proven), 8 high
   (the quiet scale of the draft's 12), 1 px line; the fill = picture 117 'mfill' (tools/kl_hud.py --watch 1: the menus' approved kit stroke + light dry
   streaks), 2 px above and below the frame and 1.5 px left of it, its width the share f of the frame's inside. Without picture 117 (a level baked before
   this) the old flat bar is drawn instead (klu_compose). f = 0: the frame alone. */
static void klu_money_bar(float x, float y, float w, float f, int layer)
{
    float fw;
    klu_outline(x, y, w, KLU_W_BAR_H, KLU_C_CHALK, layer);
    if (!(f > 0)) return;
    if (f > 1.0f) f = 1.0f;
    fw = KLU_W_FILL_OUT + (w - 1.0f) * f;
    klu_addpic(KLU_MFILL_PIC, x - KLU_W_FILL_OUT, y - KLU_W_FILL_OVER, fw, KLU_W_BAR_H + 2.0f * KLU_W_FILL_OVER, KLU_C_CHALK, layer);
}

static void klu_dials(const struct klb_snap *s)
{
    float clock = 0, cx = klu_r.mx - 35.0f, cy = klu_r.wy; int i;
    klu_r.watch = 0;
    if (!klu.dials || !klu_r.handle[113] || !klu_r.handle[114]) return;
    /* the round watch: the float the stock clock prints, [rules+0x4c], against the round's length [score+0x3c]
       (klhud_values.c f); a clock above the length (something set a longer time) is measured against left + played */
    if (klu.grid == 2) { clock = 219.0f; klu_r.clock_max = 360.0f; }
    else if (s->online) {                                  /* [HUD] Online: [rules+0x4c] is the base class's (slot 73 = 0x61d070 is ONE function for Heist, Sv and Cl). The length is not
                                                              known online (the score object is Heist's): GUESS = the largest time seen since the round began, so the first sample of the round sets it */
        static DWORD lrules; static float lmax;
        if (!klh_rd(s->rules + KLUV_R_LEFT, &clock, 4) || !kluv_secs(clock)) clock = 0.0f;
        if (s->rules != lrules || s->state != 0x19) { lrules = s->rules; lmax = 0.0f; }
        if (clock > lmax) lmax = clock;
        klu_r.clock_max = lmax;
    } else { clock = kluv_round_left(s); klu_r.clock_max = kluv_round_len(s); if (clock > klu_r.clock_max) klu_r.clock_max = clock + kluv_round_played(s); }
    if (klu.wstyle) {
        if (clock > 0.0f && klu_r.clock_max > 0.0f) {
            klu_watch_look(cx, cy, clock);
            klu_r.watch = clock > 60.0f || klu.wlast;                 /* the render slot blanks the stock clock's digits while this is set; in the last minute the stock red digits show (WatchLast=1: never) */
        }
    } else if (clock > 60.0f && klu_r.clock_max > 60.0f) {
        float left = clock / klu_r.clock_max, a = 6.2831853f * (1.0f - left);
        klu_addpic(114, cx - 34.5f, cy - 34.5f, 69.0f, 69.0f, 0x9c080809u, klu.layer - 2);
        klu_track(NULL, NULL, cx, cy, 29.0f, KLU_TRACK_C, klu.layer - 1);
        klu_arc(NULL, NULL, cx, cy, 29.0f, 0, 1.0f - left, 1.0f, KLU_C_CHALK, klu.layer);       /* the draft: the empty part begins at the top and grows clockwise */
        {   /* the hand: a short painted line from the hub to the stroke's start (the draft: 3.2 wide, 18 of the radius 24 long, x 1.2 here) */
            float hs = 3.9f / KLU_DAB_INK, dx = (float)sin(a), dy = -(float)cos(a); int k, n = (int)(21.0f / 1.1f);
            for (k = 1; k <= n; k++) klu_addpic(KLU_DAB_PIC, cx + dx * 1.1f * k - hs * 0.5f, cy + dy * 1.1f * k - hs * 0.5f, hs, hs, KLU_C_CHALK, klu.layer);
            klu_addpic(KLU_DAB_PIC, cx - 4.3f, cy - 4.3f, 8.6f, 8.6f, KLU_C_CHALK, klu.layer);
        }
        klu_r.watch = 1;                                           /* the render slot blanks the stock clock's digits while this is set */
    }
    /* the escape dial: the vehicle waits (state 3 / 4), [rules+0x1d8] = the seconds it still waits, 8 s a visit (klbot.c) */
    i = kluv_vehicle_pic(s) == KLUV_PIC_CHOPPER && klu_r.handle[KLUV_PIC_CHOPPER] ? KLUV_PIC_CHOPPER : KLUV_PIC_CAR;      /* a ZHeli: the helicopter (171); both kinds of car: 170 (klhud_values.c e) */
    if ((s->veh == 3 || s->veh == 4 || s->veh == 5 || klu.grid == 2) && klu_r.handle[i]) {      /* 5 = it drives out with its own countdown (run T2: 'van 5 8.5s'): the dial stays, emptying again */
        float ex = cx - 75.0f, ey = cy + 5.0f, left = klu.grid == 2 ? 0.35f : s->timer / 8.5f;
        if (left > 1.0f) left = 1.0f;
        if (klu.wstyle) { klu_escape_look(cx - KLW_ESC_DX, cy, left, i); return; }
        klu_addpic(114, ex - 27.5f, ey - 27.5f, 55.0f, 55.0f, 0x9c080809u, klu.layer - 2);
        klu_track(NULL, NULL, ex, ey, 23.0f, KLU_TRACK_C, klu.layer - 1);
        klu_arc(NULL, NULL, ex, ey, 23.0f, 0, 1.0f - left, 1.0f, KLU_C_ORANGE, klu.layer);
        klu_addpic(i, ex - 21.0f * KLU_VDISC, ey - 21.0f * KLU_VDISC, 42.0f * KLU_VDISC, 42.0f * KLU_VDISC, KLU_C_CHALK, klu.layer);      /* run T2: at 30 the icon's own margin left a 14 px car */
    }
}

#include "klhud_weapon.c"                     /* the weapon dial: klwd_compose / klwd_show / klwd_reset / klwd_init (re\hud_weapon.md) */

/* one crew row: kind 0 crew, 1 you, 2 traitor, 3 dead, 4 escaped, 5 fed */
static void klu_row(int row, const char *name, long money, int kind)
{
    struct klu_text *tn = &klu_r.t[KLU_T_NAME(row)], *tc = &klu_r.t[KLU_T_CASH(row)];
    const char *tag = !klu.tags ? "" : kind == 2 ? "  TRAITOR" : kind == 4 ? "  OUT" : kind == 5 ? "  FED" : "";
    float y = klu_r.cy + klu.yoff + klu.row * row; int block = klu.plates && (kind == 1 || kind == 2);
    snprintf(tn->want, sizeof tn->want, "%s%s", name, tag);
    klu_cash(tc->want, sizeof tc->want, money);
    if (klu_r.card) {                                            /* the Tab card: the row's state as a word in its own column */
        static const char *const word[6] = { "ALIVE", "YOU", "TRAITOR", "DEAD", "ESCAPED", "FED" };
        static const DWORD col[6] = { KLU_C_OUT, KLU_C_BLUE, KLU_C_ORANGE, KLU_C_DEAD, KLU_C_GREENHI, KLU_C_BLUE };
        struct klu_text *ts = &klu_r.t[KLU_T_TABST(row)]; int b = 0;          /* 2026-10-14 (owner's picture): the word stands beside the painted block, not on it */
        strcpy(ts->want, word[kind >= 0 && kind < 6 ? kind : 0]);
        ts->want_colour = b ? KLU_C_INK : col[kind >= 0 && kind < 6 ? kind : 0]; ts->noshadow = b; ts->on = klu.crew;
    }
    tn->on = tc->on = klu.crew;
    tn->noshadow = tc->noshadow = block;                         /* dark letters on a painted block carry no shadow */
    switch (kind) {
    case 1:  tn->want_colour = block ? KLU_C_INK : KLU_C_BLUE; tc->want_colour = block ? KLU_C_INKCASH : KLU_C_GREENHI; break;
    case 2:  tn->want_colour = block ? KLU_C_INK : KLU_C_ORANGE; tc->want_colour = block ? KLU_C_INK : KLU_C_ORANGE; break;
    case 3:  tn->want_colour = KLU_C_DEAD; tc->want_colour = KLU_C_DEADCASH; break;
    case 4:  tn->want_colour = KLU_C_OUT; tc->want_colour = KLU_C_GREENHI; break;
    case 5:  tn->want_colour = KLU_C_BLUE; tc->want_colour = KLU_C_GREENHI; break;
    default: tn->want_colour = KLU_C_CHALK; tc->want_colour = KLU_C_GREENHI; break;
    }
    if (!klu.plates || !klu.crew) return;
    if (block) klu_addpic(klu_r.handle[111] ? 111 : 181, klu_r.cx - 4.0f, y - klu.blockup, klu_r.card ? klu.crew_w * KLU_CARD_ST - 44.0f : klu.crew_w + 8.0f, klu.blockh, kind == 1 ? KLU_C_CHALK : KLU_C_ORANGE, klu.layer - 2);   /* the Tab card: the block ends before the status column (the cash then reads on ink) */   /* 111 = the painted stroke (kl_hud extras) */
    if (kind == 3) {
        if (klu.draft) {                                           /* M2, the draft: (name width + 12) x 4 from x 33 + 2, centred on the row (name y + 7) */
            const unsigned char *c; float w = 0;
            for (c = (const unsigned char *)name; *c; c++) if ((*c & 0xc0) != 0x80) w += KLUV_NAME_CHARW;
            klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, klu_r.cx + 2.0f, y + klu.blockh * 0.5f - klu.blockup - KLU_D_STRIKE_H * 0.5f, w + KLU_D_STRIKE_PAD, KLU_D_STRIKE_H, KLU_C_DEAD, klu.layer);      /* KLU_D_STRIKE_H high (was 4), on the block's middle */
        } else klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, klu_r.cx + 2.0f, y + 6.0f, klu.crew_w * 0.62f, klu_r.handle[KLU_DRY()] ? (klu.wstyle ? 5.0f : 8.0f) : 3.0f, KLU_C_DEAD, klu.layer);       /* the strike-through, over the name: 112 = the dry stroke */
    }       /* the strike-through, over the name: 112 = the dry stroke */
}

/* the own row's lives (re\hud_layout.md): three skull pictures (178) after the name, the lost ones faint. The name's
   width is an estimate and every number a named guess in klhud_values.c (a) until a picture has shown the row */
static void klu_lives_row(int row, const char *name, int lives, int block)
{
    float y = klu_r.cy + klu.yoff + klu.row * row + (klu.draft ? klu.blockh * 0.5f - klu.blockup - KLUV_SKULL_SIZE * 0.5f : kluv_skull_y(klu.row)); int k;      /* the draft: centred on the block's middle */      /* the draft: the block's middle (28 high, 5 above the text) */
    if (!klu.crew || klu.lives != 1 || !klu_r.handle[KLUV_SKULL_PIC]) return;
    for (k = 0; k < KLUV_LIVES_MAX; k++)
        klu_addpic(KLUV_SKULL_PIC, klu_r.cx + kluv_skull_x(name, klu.crew_w, k), y, KLUV_SKULL_SIZE, KLUV_SKULL_SIZE, kluv_skull_argb(k, lives, block), klu.layer);
}

static void klu_grid(void)
{   /* (the style sweep: eight labels '|xx' at x 640, y 420 + 22 i, each made with style byte xx - the one whose bar
       stands at 640 with the text to its right is LEFT) */   /* Grid: every box of the layout named with its top-left corner above it and its bottom-right corner under it, and
       marks at the screen's middle and edges - one screenshot at any resolution shows where everything sits (the labels
       are in virtual 1280 x 720 pixels). With Plates=1 each box also gets a 1 px coral outline: text and picture
       coordinates on one picture. */
    struct { const char *name; float x0, y0, x1, y1; } box[3]; int i, k = KLU_T_GRID; struct klu_text *t;
    box[0].name = "CREW";  box[0].x0 = klu_r.cx; box[0].y0 = klu_r.cy; box[0].x1 = klu_r.cx + klu.crew_w; box[0].y1 = klu_r.cy + klu.yoff + klu.row * klu.rows;
    box[1].name = "ROUND"; box[1].x0 = klu_r.mx - klu.money_w; box[1].y0 = klu_r.ry; box[1].x1 = klu_r.mx; box[1].y1 = klu_r.ry + 22.0f;
    box[2].name = "MONEY"; box[2].x0 = klu_r.mx - klu.money_w; box[2].y0 = klu_r.my; box[2].x1 = klu_r.mx; box[2].y1 = klu_r.my + (klu.draft ? KLU_D_MONEY_H : 86.0f);
    for (i = 0; i < 3; i++) {
        t = &klu_r.t[k++]; t->x = box[i].x0; t->y = box[i].y0 - 18.0f; t->style = KLU_STYLE_LEFT; t->on = 1; t->want_colour = KLU_C_CORAL;
        if (i == 0) { t->x = box[i].x1 + 8.0f; t->y = box[i].y0; }            /* the crew box's label beside it: above it the screen ends */
        if (i == 2) { t->x = box[i].x0 - 8.0f; t->y = box[i].y0; t->style = KLU_STYLE_RIGHT; }   /* the money box's label left of it: above it stands the round line */
        if (i == 1) { t->x = box[i].x0 - 8.0f; t->y = box[i].y0; t->style = KLU_STYLE_RIGHT; }
        snprintf(t->want, sizeof t->want, "%s %.0f,%.0f", box[i].name, box[i].x0, box[i].y0);
        t = &klu_r.t[k++]; t->x = box[i].x1; t->y = box[i].y1 + 2.0f; t->style = KLU_STYLE_RIGHT; t->on = 1; t->want_colour = KLU_C_CORAL;
        snprintf(t->want, sizeof t->want, "%.0f,%.0f", box[i].x1, box[i].y1);
        if (klu.plates) klu_outline(box[i].x0, box[i].y0, box[i].x1 - box[i].x0, box[i].y1 - box[i].y0, KLU_C_CORAL, klu.layer);
    }
    t = &klu_r.t[k++]; t->x = 640.0f; t->y = 360.0f; t->style = KLU_STYLE_LEFT; t->on = 1; t->want_colour = KLU_C_CORAL; strcpy(t->want, "+640,360 LEFT-ALIGNED");
    t = &klu_r.t[k++]; t->x = 640.0f; t->y = 384.0f; t->style = KLU_STYLE_RIGHT; t->on = 1; t->want_colour = KLU_C_CORAL; strcpy(t->want, "RIGHT-ALIGNED 640,384+");
    t = &klu_r.t[k++]; t->x = 0.0f; t->y = 500.0f; t->style = KLU_STYLE_LEFT; t->on = 1; t->want_colour = KLU_C_CORAL; strcpy(t->want, "0,500");
    t = &klu_r.t[k++]; t->x = 1280.0f; t->y = 698.0f; t->style = KLU_STYLE_RIGHT; t->on = 1; t->want_colour = KLU_C_CORAL; strcpy(t->want, "1280,698");
    for (i = 0; i < KLU_NSWEEP; i++) { t = &klu_r.t[k++]; t->x = 640.0f; t->y = 420.0f + 22.0f * i; t->style = klu_sweep[i]; t->on = 1; t->want_colour = KLU_C_CHALK; snprintf(t->want, sizeof t->want, "|STYLE %02X AT 640", klu_sweep[i]); }
    if (klu.plates) { klu_addpic(181, 640.0f, 356.0f, 1.0f, 60.0f, KLU_C_CORAL, klu.layer); klu_addpic(181, 610.0f, 360.0f, 60.0f, 1.0f, KLU_C_CORAL, klu.layer); }   /* a cross whose arms meet at (640, 360) */
}

/* 2026-10-26 online crew rows. The flag dword of an online record is the one the rules' slot 114 returns (0x625be0 -> [[rules+0x2c]+0x98+4i]); its bits are the Arcade
   score flags (4 dead, 0x40 escaped, 0x8 police, 0x10 / 0x4000 waiting, 0x1 traitor, 0x80 / 0x1000 under / dirty cop): the SAME decision as kluv_state (klhud_values.c). GUESS: the bit meanings carry over (4/0x10/0x40 are the ones klroundkeep.c reads). */
static int klu_online_kind(DWORD f, int local)
{
    if (f & (KLUV_F_WAITING | KLUV_F_DEAD)) return KLUV_K_DEAD;
    if (f & KLUV_F_ESCAPED) return KLUV_K_ESCAPED;
    if (f & (KLUV_F_DIRTYCOP | KLUV_F_POLICE | KLUV_F_UNDERCOP)) return KLUV_K_FED;
    if (f & KLUV_F_TRAITOR) return KLUV_K_TRAITOR;
    if (f & 0x10) return KLUV_K_DEAD;
    return local ? KLUV_K_YOU : KLUV_K_CREW;
}

/* the online reader's row of a seat (klonline_read.c). A seat with no row answers a 'none' (used 0, seat -1, killer -1): the old zeroed one said 'killed by seat 0' (review #2). */
static const struct klor_row *klu_onrow(const struct klor_snap *o, int seat)
{
    static const struct klor_row none = { .seat = -1, .killer = -1 };
    int i;
    for (i = 0; i < o->n; i++) if (o->r[i].seat == seat) return &o->r[i];
    return &none;
}
/* 2026-10-26 online ports on klonline_read.c ([Online] Read=1 too), every one its own [HUD] key, default 0 until benched */
static int klu_onkillai;     /* OnlineKilledAI */
static int klu_onnames, klu_onkill, klu_onround;     /* OnlineNames / OnlineKilled / OnlineRound */
static int klu_onvanicon;                                                    /* [HUD] OnlineVanIcon (default 0): the ABOARD / ESCAPED van icon online */
static int klu_onfeed, klu_onskull, klu_onloot, klu_ontab, klu_onvan;     /* OnlineFeed / OnlineSkulls / OnlineLoot / OnlineTab / OnlineVan */
static char klu_kf_txt[64]; static LONG klu_kf_at; static DWORD klu_kf_col;     /* the ONLINE kill-feed line (set by klu_compose under klu_cs; klu_kill_line shows the newer of this and the stock pop-up's) */

/* the AI heisters online: ZFFActors of team 2 (Ally), found as klbotfill.c's census does (the entity table, ZFFActor vtable 0xbb3bac, team [[a+0x54]+4] == 2; health [[a+0x5fc]+4] float).
   They have no crew record. ONE scan and ONE order with klonline_read.c: klor_bots_sorted (cached 3 s, the living first) - so row number bi here is bot bi of the reader (review #3).
   -> their number (<= 8); *alive = how many have health > 0. [HUD] OnlineBots=0 -> 0.
   GUESS: no human heister's actor is team 2 (the botfill census text treats Ally count = AI count). */
static int klu_online_bots(int *alive)
{
    DWORD act[KLOR_NBOT];
    *alive = 0;
    if (!klu.onbots) return 0;
    return klor_bots_sorted(act, alive);
}

/* the name of online seat k: the heister CHARACTER (chars=1, [HUD] OnlineNames / OnlineKilled), else the Steam name read from the client struct, else You / Player n */
static void klu_on_name(const struct klor_snap *o, int have, const struct klb_snap *s, int k, int loc, int chars, char *nm, size_t cap)
{
    const struct klor_row *r = have ? klu_onrow(o, k) : 0;
    if (chars && r && r->used && r->name[0]) snprintf(nm, cap, "%s", r->name);
    else if (k >= 0 && k < 16 && s->on_name[k][0]) snprintf(nm, cap, "%s", s->on_name[k]);
    else if (k == loc) snprintf(nm, cap, "You");
    else snprintf(nm, cap, "Player %d", k + 1);
}

/* the own row's lives, shared by the Arcade and the online list (2026-10-26: moved out of klu_compose): glyphs appended to the name (Lives=2) or skull pictures after it */
static void klu_own_lives(int row, char *name, size_t cap, int kind, int lives)
{
    if (klu.lives == 2) {                                 /* TEST: the stock list's own way, skull glyphs U+E018 appended to the name (0x6f3116) */
        size_t l = strlen(name); int nl = lives > KLUV_LIVES_MAX ? KLUV_LIVES_MAX : lives;
        if (nl && l + 4 * (size_t)nl < cap) kluv_skulls(name + l, (int)(cap - l), nl);
    } else {                                              /* the draft: three skull pictures after the name (and after the tag, when the row carries one) */
        char full[96];
        snprintf(full, sizeof full, "%s%s", name, kind == KLUV_K_TRAITOR && klu.tags ? "  TRAITOR" : "");
        klu_lives_row(row, full, lives, klu.plates);
    }
}

/* the round line, shared: 'ROUND n OF m' (+ 'LIVES k' digits on request). lives < 0 = no digits (online without [HUD] OnlineSkulls) */
static void klu_round_text(int rn, int rm, int lives)
{
    char of[16] = "", lv[16] = "";
    if (klu.roundof && rm > 0) snprintf(of, sizeof of, " OF %d", rm);          /* the game's own number: 10 in Arcade */
    if (lives >= 0 && (klu.lives == 3 || (klu.lives == 1 && !klu_r.handle[KLUV_SKULL_PIC]))) snprintf(lv, sizeof lv, "   LIVES %d", lives);   /* digits: on request, or when this level has no skull picture */
    snprintf(klu_r.t[KLU_T_ROUND].want, KLU_TEXTLEN, "ROUND %d%s%s", rn, of, lv);
}

/* the kill / reward line under REWARDS, shared: the newer of the stock pop-up's text (klhud_kill.c) and the online feed's. on = klu.money as Arcade */
static void klu_kill_line(int on)
{
    DWORD now = GetTickCount(); const char *txt = klu_kill_txt; LONG at = klu_kill_at; DWORD col = 0;
    if (on) klu_keep_now |= KLU_KEEP_KILL;                      /* the pop-up's text has a place on the screen this compose: klhud_kill.c may keep the stock line */
    if (klu_kf_at && (!klu_kill_at || (LONG)((DWORD)klu_kf_at - (DWORD)klu_kill_at) > 0)) { txt = klu_kf_txt; at = klu_kf_at; col = klu_kf_col; }
    if (at && (LONG)(now - (DWORD)at) < klu_kill_ms) {
        const char *d = strchr(txt, '$');
        snprintf(klu_r.t[KLU_T_KILL].want, KLU_TEXTLEN, "%s", txt);
        klu_r.t[KLU_T_KILL].want_colour = col ? col : d && d > txt && d[-1] == '-' ? KLU_C_CORAL : KLU_C_GREEN;
        klu_r.t[KLU_T_KILL].on = on;
    }
}

/* the framed bar under TOTAL, shared (re\hud_layout.md): f = the filled share 0..1 */
static void klu_loot_bar(float f)
{
    float x = klu_r.mx - klu.money_w, y = klu_r.my + (klu.draft ? KLU_D_BAR_Y : 26.0f), bh = klu.draft ? KLU_D_BAR_H : 8.0f;
    if (f > 1.0f) f = 1.0f;
    if (f * klu.money_w < 1.5f) f = 0.0f;
    if (klu.wstyle && klu.draft && klu.mfill && klu_r.handle[KLU_MFILL_PIC]) klu_money_bar(x, klu_r.my + KLU_W_BAR_Y, klu.money_w, f, klu.layer - 2);
    else {
        klu_outline(x, y, klu.money_w, bh, KLU_C_CHALK, klu.layer - 2);
        klu_addpic(181, x - 2.0f, y - 2.0f, klu.money_w * f, bh + 4.0f, KLU_C_CHALK, klu.layer - 2);
    }
}

/* the Tab card, shared: begin = the list's place moves to the middle for this compose (n_ = rows), put back when the card is off; end = the numbers back */
static float klu_card_save[3]; static int klu_card_tags, klu_card_placed;
static void klu_card_begin(int n_)
{
    if (klu_r.card) {
        if (n_ > klu.rows) n_ = klu.rows;
        klu_card_save[0] = klu_r.cx; klu_card_save[1] = klu_r.cy; klu_card_save[2] = klu.crew_w; klu_card_tags = klu.tags;
        klu_r.cx = 640.0f - KLU_CARD_W * 0.5f; klu_r.cy = KLU_CARD_Y; klu.crew_w = KLU_CARD_W; klu.tags = 0;
        klu_place_crew(); klu_card_placed = 1;
        if (klu.plates) {                                     /* run v42: ONE stroke (111, 256 x 32) stretched to the card's height read as shreds - a faint solid
                                                                 ink under painted bands of row height, as the corner list's blocks */
            float top = klu_r.cy - 18.0f, h = klu.yoff + klu.row * (float)n_ + 30.0f, yb;
            klu_addpic(181, klu_r.cx - 16.0f, top + 3.0f, KLU_CARD_W + 32.0f, h - 6.0f, KLU_CARD_UNDER, klu.layer - 4);
            if (klu_r.handle[111]) for (yb = top; yb < top + h - 4.0f; yb += KLU_CARD_BAND - 6.0f)
                klu_addpic(111, klu_r.cx - 22.0f, yb, KLU_CARD_W + 44.0f, yb + KLU_CARD_BAND > top + h ? top + h - yb : KLU_CARD_BAND, KLU_CARD_INK, klu.layer - 3);
        }
    } else if (klu_card_placed) { klu_place_crew(); klu_card_placed = 0; }      /* back in the corner */
}
static void klu_card_end(void)
{
    if (klu_r.card) { klu_r.cx = klu_card_save[0]; klu_r.cy = klu_card_save[1]; klu.crew_w = klu_card_save[2]; klu.tags = klu_card_tags; }    /* the numbers back; the texts stay at the card until the next compose */
}

/* the van card (the owner 2026-10-13 / 10-17 / 10-24; klhud_escape.c feeds the klu_esc_* mirrors from the stock panel). Moved out of klu_compose 2026-10-26 so the online branch
   draws the SAME card ([HUD] OnlineVan). veh = the vehicle state byte (Arcade s.veh / online [rules+0x1dc]); mir_ok = 1 when the online mirrors may stand in for a silent stock panel. */
static void klu_van_card(int veh, int mir_ok, float mir_timer)
{
    /* 2026-10-13, the owner (a picture of the escape panel: a chalk smear left of an orange car box, the time above it, an empty frame):
       'fix the van symbol like i want it revamped too since it looks broken'. The van card, in the money box's column under the kill
       line: a dark painted stroke, the vehicle icon in chalk, the time right-aligned, a thin health bar under it (coral when low).
       klhud_escape.c (EscapeCard=1) keeps the stock panel's prompts and makes its plate, icon, bar and time invisible, and sets
       klu_esc_at for every frame the stock panel would have drawn. */
    /* 2026-10-17 (owner: 'fixing how the escape van ones appear'): the card used to live only while the stock panel drew within the last
       250 ms, so a skipped panel frame made it flicker or come late. Now: the last good time text / health share / icon slot are LATCHED,
       the card stays KLU_ESC_HOLD ms after the last stock draw, fades in over KLU_ESC_FIN ms and out over KLU_ESC_FOUT ms (alpha of every
       colour scaled; the plate, icon, bar and text). GUESS: 1 s hold and these fade times are the lead's numbers, not the owner's. */
    {
        static DWORD seen, last, loglast; static int on, lslot, logskip, idle, idle_was; static float lfrac, alpha; static char ltt[32];
        DWORD now = GetTickCount(), at = (DWORD)klu_esc_at;
        int fresh; float al, dt; int want;
        if (InterlockedExchange(&klu_esc_rst, 0)) { idle = idle_was = 0; seen = 0; alpha = 0.0f; on = 0; last = 0; ltt[0] = 0; at = 0; }
        if (klu.money) klu_keep_now |= KLU_KEEP_VAN;           /* the card is live this compose: klhud_escape.c may hide the stock panel's time / icon / bar */
        fresh = at && (DWORD)(now - at) < 250 && klu.money;    /* unsigned: a signed compare turned true again after 24.9 days */
        dt = last ? (float)(LONG)(now - last) : 0.0f; if (dt < 0.0f || dt > 200.0f) { if (dt > 200.0f && !fresh) alpha = 0.0f; dt = 200.0f; } last = now;   /* compose paused (menu, pause): no stale half-faded card on return */
        if (fresh) {
            DWORD tobj = (DWORD)klu_esc_time, str; LONG fb = klu_esc_frac; float f;
            if (!on && alpha <= 0.0f) ltt[0] = 0;       /* a new appearance never shows the previous van's time */
            memcpy(&f, &fb, 4); if (!(f >= 0)) f = 0; if (f > 1.0f) f = 1.0f; lfrac = f; lslot = (int)klu_esc_slot; seen = now ? now : 1;
            if (tobj && klh_rd32(tobj) == KLU_TEXT_VT && (str = klh_rd32(tobj + 0xa4)) != 0) { char t2[32] = ""; klh_rdstr(str + 0xc, t2, sizeof t2); if (t2[0]) memcpy(ltt, t2, sizeof ltt); }
            /* 2026-10-24 (owner: 'get that van escape thing on the right gone if the van isnt there'): the stock panel's gates (+0x24, +0x28) stay open
               with no vehicle, so the card sat there reading 00:00 all round. [HUD] HideIdleEscape=1: a time text with no non-zero digit while the
               vehicle state (veh) is not 3 / 4 / 5 = no vehicle: the card is not latched and drops at once. GUESS: the idle text reads '00:00'
               (the owner's picture); an unreadable text never counts as idle. HideIdleEscapeDry=1 only logs the verdict. */
            idle = 0;
            if (klu_hideidle && tobj && klh_rd32(tobj) == KLU_TEXT_VT && (str = klh_rd32(tobj + 0xa4)) != 0) {
                char t3[32] = ""; int k, nz = 0, z = 0, rd = klh_rdstr(str + 0xc, t3, sizeof t3);
                for (k = 0; t3[k] && k < 31; k++) { if (t3[k] >= '1' && t3[k] <= '9') nz = 1; if (t3[k] == '0') z = 1; }
                if (rd > 0 && z && !nz && veh != 3 && veh != 4 && veh != 5) idle = 1;   /* read, and all zeros (an empty / unread text is not idle) */
            }
            if (idle != idle_was) { idle_was = idle; if (klu.log) klog("hud: van card: %s (time text, vehicle state %d)%s", idle ? "IDLE, no vehicle" : "vehicle there", (int)veh, klu_hideidle_dry ? " [Dry=1: not hidden]" : ""); }
            if (idle && !klu_hideidle_dry) seen = 0;
        }
        if (!fresh && mir_ok && klu.money) {              /* ONLINE (2026-10-26, [HUD] OnlineVan): the stock panel is not drawing: the card from the rules' mirrors
                                                               ([rules+0x1d8] timer, vehicle state [rules+0x1dc] in 3..5, set by the caller). GUESS: the state numbers and the mm:ss form carry over from Arcade; the icon is the car (170), the health share is kept */
            int t = (int)mir_timer; snprintf(ltt, sizeof ltt, "%02d:%02d", t / 60, t % 60); lslot = 170; seen = now ? now : 1;
        }
        want = klu.money && seen && (DWORD)(now - seen) < KLU_ESC_HOLD;
        if (want && !on) { on = 1; if (klu.log && (LONG)(now - loglast) >= KLU_ESC_LOGGAP) { loglast = now; if (logskip) { klog("hud: van card: %d on/off lines skipped", logskip); logskip = 0; } klog("hud: van card ON at (%.0f, %.0f) %.0f wide, icon slot %d (picture %s), health share %.2f, time '%s'%s", klu_r.mx - klu.money_w, klu_r.t[KLU_T_KILL].y + 18.0f + KLU_ESC_GAP, klu.money_w, lslot, lslot > 0 && lslot < 200 && klu_r.handle[lslot] ? "loaded" : "MISSING", lfrac, ltt, ltt[0] ? "" : " (EMPTY: the placeholder shows)"); } else if (klu.log) logskip++; }
        if (!want && on) { on = 0; if (klu.log && (LONG)(now - loglast) >= KLU_ESC_LOGGAP) { loglast = now; klog("hud: van card off (%s)", klu.money ? "the stock panel stopped drawing for 2.5 s" : "[HUD] Money=0"); } else if (klu.log) logskip++; }
        /* one alpha that is ramped by the frame time, so a stock draw that returns mid-fade carries on from where the fade stood */
        if (want) alpha += dt / (float)KLU_ESC_FIN; else alpha -= dt / (float)KLU_ESC_FOUT;
        if (!klu.money) alpha = 0.0f;
        if (alpha > 1.0f) alpha = 1.0f; if (alpha < 0.0f) alpha = 0.0f;
        al = alpha;
        klu_r.t[KLU_T_ESC].sa = al;
        if (al > 0.0f) {
            float y0 = klu_r.t[KLU_T_KILL].y + 18.0f + KLU_ESC_GAP, w = klu.money_w, x0 = klu_r.mx - w; int slot = lslot;
            snprintf(klu_r.t[KLU_T_ESC].want, KLU_TEXTLEN, "%s", ltt[0] ? ltt : "--:--"); klu_r.t[KLU_T_ESC].on = 1;
            klu_r.t[KLU_T_ESC].want_colour = klu_fa(KLU_C_CHALK, al);
            klu_addpic(klu_r.handle[111] ? 111 : 181, x0 - 8.0f, y0, w + 14.0f, KLU_ESC_H, klu_fa(0xd80c0c0du, al), klu.layer - 3);
            if (slot > 0 && slot < 200 && klu_r.handle[slot]) klu_addpic(slot, x0 + 15.0f - 13.0f * KLU_VDISC, y0 + KLU_ESC_H * 0.5f - 13.0f * KLU_VDISC, 26.0f * KLU_VDISC, 26.0f * KLU_VDISC, klu_fa(KLU_C_CHALK, al), klu.layer);
            klu_addpic(181, x0, y0 + KLU_ESC_H + 3.0f, w, 3.0f, klu_fa(0x6cf3f0eau, al), klu.layer - 2);
            if (lfrac > 0.005f) klu_addpic(181, x0, y0 + KLU_ESC_H + 3.0f, w * lfrac, 3.0f, klu_fa(lfrac < 0.3f ? KLU_C_CORAL : KLU_C_CHALK, al), klu.layer - 1);
        }
    }
}

/* -> every text's wanted string and colour and the picture list; 0 = nothing to show (no Arcade round) */
static int klu_compose_in(int *state_ok);
static int klu_compose(int *state_ok)
{   /* the texts and pictures of this tick, then the sink bits in ONE write (see klu_keep): what the render-thread wrappers may keep off the screen */
    int r;
    klu_keep_now = 0;
    r = klu_compose_in(state_ok);
    InterlockedExchange(&klu_keep, (LONG)(r ? klu_keep_now : 0));
    return r;
}

static int klu_compose_in(int *state_ok)
{
    struct klb_snap s; int i, row = 0, human, used = 0, alive = 0; long total = 0, loot = 0, rewards = 0; DWORD cat[0x3c / 4]; char name[56]; int lives = 0, rn = 0, rm = 0;
    *state_ok = 0;
    if (!klb_read_hud(&s)) return 0;                          /* klbot.c 1: Arcade, ZGameRulesHeist, the records; [HUD] Online: the online rules' snapshot (no records) */
    if (s.online) {                                           /* local, cosmetic parts only: the watch and the weapon dial. No crew list, money, rows, tags: their data is Heist's */
        *state_ok = klu.draw == 2 ? s.state == 0x19 : s.state >= 0x17 && s.state <= 0x19;
        for (i = 0; i < KLU_NTEXT; i++) { klu_r.t[i].on = 0; klu_r.t[i].noshadow = 0; klu_r.t[i].sa = 1.0f; }
        klu_r.npic = 0;
        klu_dials(&s);
        klwd_compose();
        if (klb_hud_crew && klu.crew && s.on_n > 0) {         /* [HUD] OnlineCrew: the online crew list (2026-10-26: the rows, names, states, counts and money boxes as Arcade's) */
            int k, rows = 0, nu = 0, na = 0, nb, ba = 0, bi, nrows = 0, olives = 0; long tot = 0; char nm[56]; struct klor_snap or_; int have; BYTE loc = 0; int loc_pend = 0; int locst = -1; long lloot = 0, lrew = 0;
            { DWORD el = klh_rd32(klu_r.osd + KLU_O_PLIST); DWORD li = 0; if (el && klh_rd(el + 0xefc, &li, 1) && li < 16) loc = (BYTE)li; }
            loc_pend = loc < s.on_n && s.on_used[loc];
            have = klor_read(&or_, (int)loc);                    /* the reader: heister character names, killer, round, loot, feed (off unless [Online] Read=1). BEFORE the rows loop (review #1: 'have' was tested before it was set) */
            if (have) klgrd_note_online(&or_);                     /* klhud_grades.c: [Grades] the seats' experience / rating */
            if (have) olives = KLUV_LIVES_MAX - or_.deaths < 0 ? 0 : KLUV_LIVES_MAX - or_.deaths;   /* GUESS: Arcade's 3 lives; online has none, so a skull is a death mark: 3 - deaths of the local seat this match */
            nb = klu_online_bots(&ba);                          /* the AI heisters have no record: rows from the Ally actors, like Arcade's bot rows */
            if (klu_r.card) { for (k = 0; k < s.on_n; k++) nrows += s.on_used[k] != 0; nrows += nb; }
            klu_card_begin(nrows);                               /* the Tab card (OnlineTab; klu_r.card is only set online with it) */
            strcpy(klu_r.t[KLU_T_HEAD].want, "DEAD MEN"); klu_r.t[KLU_T_HEAD].on = 1; klu_r.t[KLU_T_HEAD].want_colour = KLU_C_CORAL;   /* 2026-10-25 owner: the Arcade crew box is headed DEAD MEN, online said CREW */
            for (k = 0; k < s.on_n; k++) {
                int kind;
                if (!s.on_used[k]) continue;
                nu++; tot += s.on_money[k];
                kind = klu_online_kind(klucc_hud_flags(s.on_flags[k], (int)loc, k), k == loc);     /* [Ucc] Rows (klucchide_logic.h): a hidden UCC is crew to a heister viewer */
                if (kind != KLUV_K_DEAD && kind != KLUV_K_ESCAPED) na++;
                if (k == loc) { locst = kind; lloot = s.on_loot[k]; lrew = s.on_rew[k]; }
                if (rows + (k != loc && loc_pend) >= klu.rows) continue;     /* the local player's row is reserved: a high slot (a client's own index) is never the one cut */
                if (k == loc) loc_pend = 0;
                klu_on_name(&or_, have, &s, k, (int)loc, have && klu_onnames, nm, sizeof nm);     /* the heister CHARACTER's name (the owner's order 16:45) */
                klgrd_decorate(nm, sizeof nm, 1, k, k == loc);     /* klhud_grades.c: [Grades] Badge */
                if (klu_onskull && have && k == loc && (kind == KLUV_K_YOU || kind == KLUV_K_TRAITOR)) klu_own_lives(rows, nm, sizeof nm, kind, olives);     /* [HUD] OnlineSkulls: death marks, as Arcade's lives row */
                klu_row(rows++, nm, s.on_money[k], kind);
            }
            for (bi = 0; bi < nb; bi++) {
                int dead = bi >= ba; nu++; if (!dead) na++;
                if (rows >= klu.rows) continue;
                if (have && klu_onnames && bi < or_.nbots && or_.bot[bi].name[0]) snprintf(nm, sizeof nm, "%s", or_.bot[bi].name); else snprintf(nm, sizeof nm, "Heister %d", bi + 1);
                klgrd_decorate_rank(nm, sizeof nm, klgrd_bot_rank());
                klu_row(rows++, nm, 0, dead ? KLUV_K_DEAD : KLUV_K_CREW);
            }
            snprintf(klu_r.t[KLU_T_COUNT].want, KLU_TEXTLEN, klu_r.card ? "%d / %d ALIVE" : "%d / %d", na, nu); klu_r.t[KLU_T_COUNT].on = 1;
            if (klu_r.card) strcpy(klu_r.t[KLU_T_HEAD].want, "CREW");
            { static int told; if (!told && klu.log) { told = 1; klog("hud: ONLINE parity: crew box = DEAD MEN + rule + alive/used + per-row state from the flag dwords [S+0x98+4i]; names %s; bots %d row(s); reader %s; ports by key: names %d killed %d round %d feed %d skulls %d loot %d tab %d van %d (re/hud_online.md)", s.on_named ? "read from the client structs" : "NOT readable (You / Player n)", nb, have ? "ON" : "off ([Online] Read=0)", klu_onnames, klu_onkill, klu_onround, klu_onfeed, klu_onskull, klu_onloot, klu_ontab, klu_onvan); } }
            if (klu.plates) {                                 /* the same painted rule as the Arcade box */
                if (klu.draft) klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, klu_r.cx, klu_r.cy + KLU_D_RULE_Y, klu.crew_w, KLU_D_RULE_H, KLU_C_CHALK, klu.layer - 2);
                else klu_addpic(181, klu_r.cx, klu_r.cy + 22.0f, klu.crew_w, 3.0f, KLU_C_CHALK, klu.layer - 2);
            }
            klu_card_end();                                   /* the numbers back (the Arcade order: after the rule) */
            if (klu.money) {                                  /* TOTAL / LOOT / REWARDS like Arcade (GUESS: which online array is loot and which rewards, see klbot.c) */
                static const char *label[3] = { "TOTAL", "LOOT", "REWARDS" }; long v[3]; int q;
                v[0] = tot; v[1] = lloot; v[2] = lrew;
                for (q = 0; q < 3; q++) {
                    strcpy(klu_r.t[KLU_T_MLABEL(q)].want, label[q]); klu_r.t[KLU_T_MLABEL(q)].on = 1;
                    klu_dollars(klu_r.t[KLU_T_MVALUE(q)].want, KLU_TEXTLEN, v[q]); klu_r.t[KLU_T_MVALUE(q)].on = 1;
                }
            }
            if (klu_onloot && klu.plates && klu.money) {      /* [HUD] OnlineLoot: the framed bar under TOTAL = the share of the map's loot taken so far (loot on the map vs the largest seen this round, klonline_read.c; 0 until read) */
                float f = have && or_.loot_ok ? klor_loot_share(or_.loot_init, or_.loot_rem) : 0.0f;
                klu_loot_bar(f);
            }
            if (klu_onvan && klu.money) klu_van_card(have ? (int)or_.esc_state : 0, have && or_.esc_state >= 3 && or_.esc_state <= 5 && or_.esc_timer > 0, have ? or_.esc_timer : 0.0f);   /* [HUD] OnlineVan: the Arcade van card, fed by the stock panel and, silent, the rules' mirrors */
            if (klu_onfeed) {                                 /* [HUD] OnlineFeed: the kill-feed line under REWARDS. Events = a seat's status bit 4 going 0 -> 1 with its KillerIndex (klonline_read.c); the stock pop-up's own text shows too */
                if (have) for (k = 0; k < or_.nev; k++) {
                    char vn[40], kn[40];
                    klu_on_name(&or_, have, &s, or_.ev[k].victim, (int)loc, 1, vn, sizeof vn);
                    if (or_.ev[k].killer >= 0 && or_.ev[k].killer != or_.ev[k].victim && or_.ev[k].killer < KLOR_SEATS && s.on_used[or_.ev[k].killer]) {
                        klu_on_name(&or_, have, &s, or_.ev[k].killer, (int)loc, 1, kn, sizeof kn);
                        snprintf(klu_kf_txt, sizeof klu_kf_txt, "%s KILLED %s", kn, vn);
                    } else snprintf(klu_kf_txt, sizeof klu_kf_txt, "%s DIED", vn);          /* no seat killed him: a bot, the police or a fall (suicide too) */
                    klor_upper(klu_kf_txt);
                    klu_kf_col = or_.ev[k].victim == (int)loc ? KLU_C_CORAL : or_.ev[k].killer == (int)loc ? KLU_C_GREEN : KLU_C_CHALK;
                    klu_kf_at = (LONG)GetTickCount() | 1;
                }
                klu_kill_line(klu.money);
            }
            if (klu.killed && (locst == KLUV_K_DEAD)) {       /* the same KILLED BY line as offline: the killer's name; the police when no seat did it (Arcade's own fallback); YOURSELF for a suicide / fall onto oneself (review #2) */
                char kn[40]; kn[0] = 0;
                if (have && klu_onkill) { const struct klor_row *lr = klu_onrow(&or_, (int)loc);
                    if (lr->used && lr->killer >= 0 && lr->killer < KLOR_SEATS) {
                        if (lr->killer == (int)loc) strcpy(kn, "YOURSELF");
                        else if (lr->killer < s.on_n && s.on_used[lr->killer]) { klu_on_name(&or_, have, &s, lr->killer, (int)loc, 1, kn, sizeof kn); klor_upper(kn); }
                    }
                    else if (klu_onkillai && lr->used && lr->ai_killer[0]) { snprintf(kn, sizeof kn, "%s", lr->ai_killer); klor_upper(kn); }   /* [HUD] OnlineKilledAI: an AI heister's bullet; the police stay THE POLICE */
                }
                snprintf(klu_r.t[KLU_T_DEATH].want, KLU_TEXTLEN, "KILLED BY  %s", kn[0] ? kn : "THE POLICE"); klu_r.t[KLU_T_DEATH].on = 1; klu_r.t[KLU_T_DEATH].want_colour = KLU_C_CORAL;
            }
            if (have && klu_onround && or_.ok && or_.round > 0 && klu.round) {     /* ROUND n OF m (bytes S+0x350 / S+0x3d4, ^0xac): the Arcade round text */
                klu_round_text(or_.round, or_.rounds, klu_onskull ? olives : -1); klu_r.t[KLU_T_ROUND].on = 1;
            }
        }
        if (klu_onvanicon && s.on_n > 0 && klu_r.handle[170]) {   /* [HUD] OnlineVanIcon (default 0): Arcade's VanIcon block (below) is skipped online; like Arcade: ABOARD green, ESCAPED bright green. Local drawing, read-only */
            DWORD el = klh_rd32(klu_r.osd + KLU_O_PLIST), li = 0; int lc = -1;
            if (el && klh_rd(el + 0xefc, &li, 1) && li < 16) lc = (int)li;
            /* PROVEN live 10-27 (bench BOSE4, c9): the local seat's score status word s.on_flags[lc] goes 0 -> 0x20 (ABOARD, after E at the van) -> 0x40 (ESCAPED), on host and client */
            if (lc >= 0 && lc < s.on_n && s.on_used[lc] && (s.on_flags[lc] & (KLUV_F_ABOARD | KLUV_F_ESCAPED))) {
                float ix = klu_r.mx - 35.0f - 66.0f, iy = klu_r.wy;     /* the same place as the Arcade icon: left of the watch */
                if (klu_r.handle[KLU_DAB_PIC]) klu_dab_at(ix, iy, 46.0f, 0xc80c0c0du, klu.layer - 2);
                klu_addpic(170, ix - 15.0f * KLU_VDISC, iy - 15.0f * KLU_VDISC, 30.0f * KLU_VDISC, 30.0f * KLU_VDISC, (s.on_flags[lc] & KLUV_F_ESCAPED) ? KLU_C_GREENHI : KLU_C_GREEN, klu.layer);
            }
        }
        return 1;
    }
    /* the stock player list's own window (its Tick 0x76db00). Draw=2: the stock clock Render draws nothing outside
       state 0x19 (0x81e0c3), so ours is 'shown' - and the stock block hidden - only there */
    *state_ok = klu.draw == 2 ? s.state == 0x19 : s.state >= 0x17 && s.state <= 0x19;
    for (i = 0; i < KLU_NTEXT; i++) { klu_r.t[i].on = 0; klu_r.t[i].noshadow = 0; klu_r.t[i].sa = 1.0f; }
    klu_r.npic = 0;
    human = s.human >= 0 ? s.human : 0;
    lives = klu.grid == 2 ? 2 : kluv_lives(&s);               /* byte [score+0x6c]; +0x44 is the number of rounds (klhud_values.c a, c) */
    {                                                         /* the Tab card (klu_card_begin): the list's place moves to the middle for this compose (put back after the crew part) */
        int n_ = 0;
        if (klu_r.card) { for (i = 0; i < s.n; i++) n_ += s.r[i].used != 0; if (klu.grid == 2) n_ = KLU_ROWS; }
        klu_card_begin(n_);
    }
    if (klu.grid == 2) {                                    /* the draft's own eight rows: every state on one picture */
        static const struct { const char *n; long m; int kind; } demo[KLU_ROWS] = { { "J.C.", 540000, 1 }, { "KANE", 310000, 0 }, { "LYNCH", 0, 0 }, { "PARKER", 860000, 2 },
                                                                                    { "TOMMY", 120000, 0 }, { "RED", 400000, 4 }, { "MELDAL", 0, 3 }, { "ASHKANAN", 1250000, 3 },
                                                                                    { "HOYT", 90000, 0 }, { "GOGGLES", 0, 0 }, { "SHEPPARD", 220000, 2 }, { "BRENNAN", 0, 3 } };
        for (row = 0; row < klu.rows; row++) klu_row(row, demo[row].n, demo[row].m, demo[row].kind);
        klu_lives_row(0, demo[0].n, lives, klu.plates);
        used = 8; alive = 5;
    } else for (i = 0; i < s.n; i++) {
        const struct klb_rec *r = &s.r[i]; DWORD blk, str = 0; int kind;
        if (!r->used) continue;
        used++; if (r->status != 7 && r->status != 6) alive++;
        if (row >= klu.rows) continue;
        name[0] = 0;
        if ((blk = klh_rd32(r->at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, name, sizeof name);     /* [[record]+8]: 0x841e50 */
        klnm_name(r->at, name, sizeof name);                  /* klhud_names.c: the character this record wears (falls back to the game's name) */
        if (!name[0]) snprintf(name, sizeof name, r->flags & 1 ? "Heister %d" : "You", i);
        kind = kluv_kind(&s, i);                              /* klhud_values.c g: THE row decision (dead / waiting, escaped, fed before traitor, traitor, you, crew) */
        if (i == human) klgrd_decorate(name, sizeof name, 0, i, 1); else klgrd_decorate_rank(name, sizeof name, klgrd_bot_rank());     /* klhud_grades.c: [Grades] Badge (off unless on) */
        if (i == human && (kind == KLUV_K_YOU || kind == KLUV_K_TRAITOR)) klu_own_lives(row, name, sizeof name, kind, lives);
        klu_row(row++, name, (long)r->money, kind);
    }
    klu_van_card((int)s.veh, 0, 0.0f);              /* 2026-10-26: the card is klu_van_card (the online branch draws it too, [HUD] OnlineVan) */
    /* 2026-10-13, the owner: 'for when u escape / in the van should be an icon to let the person know': while YOUR record is aboard the
       vehicle or escaped, the level's own car icon (170, the escape panel's) in green on a dark dab, left of the watch. [HUD] VanIcon=0: off */
    if (klu.vanicon && human >= 0 && klu_r.handle[170]) {
        int st = kluv_state(&s, human);
        if (st == KLUV_ST_ABOARD || st == KLUV_ST_ESCAPED) {
            float ix = klu_r.mx - 35.0f - 66.0f, iy = klu_r.wy;
            if (klu_r.handle[KLU_DAB_PIC]) klu_dab_at(ix, iy, 46.0f, 0xc80c0c0du, klu.layer - 2);
            klu_addpic(170, ix - 15.0f * KLU_VDISC, iy - 15.0f * KLU_VDISC, 30.0f * KLU_VDISC, 30.0f * KLU_VDISC, st == KLUV_ST_ESCAPED ? KLU_C_GREENHI : KLU_C_GREEN, klu.layer);
        }
    }
    if (klu.killed && human >= 0) {                           /* [HUD] KilledBy=1 (recommended on): the death line in the HUD's style: coral, capitals, the killer's character name */
        int st = kluv_state(&s, human);
        if (st == KLUV_ST_DEAD || st == KLUV_ST_WAITING) {
            int k = kluv_killer(&s, human); char kn[40] = "";
            if (k >= 0 && k < s.n && s.r[k].used) { DWORD blk, str = 0; if ((blk = klh_rd32(s.r[k].at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, kn, sizeof kn); klnm_name(s.r[k].at, kn, sizeof kn); }
            { size_t q; for (q = 0; kn[q]; q++) if (kn[q] >= 'a' && kn[q] <= 'z') kn[q] -= 32; }
            snprintf(klu_r.t[KLU_T_DEATH].want, KLU_TEXTLEN, "KILLED BY  %s", kn[0] ? kn : "THE POLICE"); klu_r.t[KLU_T_DEATH].on = 1;
            klu_r.t[KLU_T_DEATH].want_colour = KLU_C_CORAL;
            { static int told; if (!told && klu.log) { told = 1; klog("hud: KILLED BY drawn in the HUD style ('%s'); the stock death panel text (XML FARespawn KilledBy) is NOT hidden by the hook - see report", klu_r.t[KLU_T_DEATH].want); } }
        }
    }
    if (klu.crew) {
        strcpy(klu_r.t[KLU_T_HEAD].want, "DEAD MEN"); klu_r.t[KLU_T_HEAD].on = 1; klu_r.t[KLU_T_HEAD].want_colour = KLU_C_CORAL;
        snprintf(klu_r.t[KLU_T_COUNT].want, KLU_TEXTLEN, "%d / %d", alive, used); klu_r.t[KLU_T_COUNT].on = 1;
        if (klu_r.card) { strcpy(klu_r.t[KLU_T_HEAD].want, "CREW"); snprintf(klu_r.t[KLU_T_COUNT].want, KLU_TEXTLEN, "%d / %d ALIVE", alive, used); }
        if (klu.plates) {                                     /* the painted rule: the draft's pic 112, 211 x 5, centre y 22 under the head */
            if (klu.draft) klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, klu_r.cx, klu_r.cy + KLU_D_RULE_Y, klu.crew_w, KLU_D_RULE_H, KLU_C_CHALK, klu.layer - 2);
            else klu_addpic(181, klu_r.cx, klu_r.cy + 22.0f, klu.crew_w, 3.0f, KLU_C_CHALK, klu.layer - 2);
        }
    }
    klu_card_end();
    /* Total as 0x807520(rules) (EXE): record 0's money when in use, + the score object's dwords +4..+0x10, +0x18..+0x24, +0x2c, + [+0x38] */
    if (klh_rd(s.score + 4, cat, sizeof cat)) {
        static const int add[10] = { 0, 1, 2, 3, 5, 6, 7, 8, 10, 13 };     /* dword indices from +4: +4 +8 +c +10 +18 +1c +20 +24 +2c +38 */
        static const char *label[3] = { "TOTAL", "LOOT", "REWARDS" };
        long v[3];
        for (i = 0; i < 10; i++) total += (long)cat[add[i]];
        if (s.r[0].used) total += (long)s.r[0].money;
        loot = s.human >= 0 ? (long)s.r[human].money : 0;
        klh_rd(s.score + KLU_S_REWARDS + 4 * human, &rewards, 4);
        if (!kluv_round(&s, &rn, &rm)) rn = s.level;          /* n = byte [score+0x45], m = byte [score+0x44] (10 in Arcade) */
        if (klu.grid == 2) { total = 3400000; loot = 540000; rewards = 0; }
        v[0] = total; v[1] = loot; v[2] = rewards;
        for (i = 0; i < 3; i++) {
            strcpy(klu_r.t[KLU_T_MLABEL(i)].want, label[i]); klu_r.t[KLU_T_MLABEL(i)].on = klu.money;
            klu_dollars(klu_r.t[KLU_T_MVALUE(i)].want, KLU_TEXTLEN, v[i]); klu_r.t[KLU_T_MVALUE(i)].on = klu.money;
        }
        klu_kill_line(klu.money);                             /* klhud_kill.c: the latest kill / reward line, under REWARDS */
        klu_round_text(rn, rm, lives);
        klu_r.t[KLU_T_ROUND].on = klu.round;
        if (klu.plates && klu.money) {                        /* the framed bar under TOTAL (re\hud_layout.md): what the crew holds of the level's loot ([rules+0xdd0], klhud_values.c d); a level that registered no loot: how much of your total you carry */
            float f = total > 0 && loot > 0 ? (float)loot / (float)total : 0.0f;
            if (klu.grid == 2) f = 0.16f;
            else if (kluv_loot_total(&s) > 0) f = kluv_loot_share(&s);
            if (klu.grid != 2 && total <= 0) f = 0.0f;           /* 2026-10-12 (run S1: a stub of fill at TOTAL $0): no money, no fill */
            klu_loot_bar(f);
        }
    }
    if (klu.log >= 2) kluv_dump(&s, human);                   /* 'hud: values: ...': looked at once a second, said when a value other than the clock changed */
    klu_dials(&s);
    klwd_compose();                                           /* klhud_weapon.c: straight after the dials (it adds its texts and pictures to the same queues); a no-op without Weapon=1 */
    if (klu.grid) klu_grid();
    return 1;
}

/* SetText / SetColour of every text whose wanted string or colour differs (main thread, under the lock) */
static void klu_apply(void)
{
    int i;
    for (i = 0; i < KLU_NTEXT; i++) {
        struct klu_text *t = &klu_r.t[i]; DWORD vt;
        if (!t->obj) continue;
        /* every text and shadow, shown or not: the render slot reads them without a checked read (section 5b) */
        if (!klh_rd(t->obj, &vt, 4) || vt != KLU_TEXT_VT || (t->shadow && (!klh_rd(t->shadow, &vt, 4) || vt != KLU_TEXT_VT))) {
            klu_r.fault = 1; klog("hud: text %d (%08lx, shadow %08lx) no longer has ZCHAROBJ's vtable: the HUD stands down for this level", i, t->obj, t->shadow); return;
        }
        if (!t->on) continue;
        if (strcmp(t->want, t->cur)) {
            klu_set(t->obj, KLU_VT_TEXT, (DWORD)(DWORD_PTR)t->want);
            if (t->shadow) klu_set(t->shadow, KLU_VT_TEXT, (DWORD)(DWORD_PTR)t->want);
            if (klu.log >= 2) klog("hud: text %d: '%s' -> '%s'", i, t->cur, t->want);
            strcpy(t->cur, t->want);
        }
        if (t->want_colour != t->colour) {
            klu_set(t->obj, KLU_VT_COLOUR, t->want_colour);
            if (klu.log >= 2) klog("hud: text %d ('%s'): colour %08lx -> %08lx", i, t->cur, t->colour, t->want_colour);
            t->colour = t->want_colour;
        }
        if (t->shadow && t->sa < 1.0f + 1e-6f) {      /* the shadow fades with its text (only the van card sets sa below 1) */
            DWORD wc = klu_fa(t->fnt == KLU_FNT_BIG ? KLU_SHADOW_RGB : KLU_SHADOW_SMALL, t->sa);
            if (wc != t->shcol) { klu_set(t->shadow, KLU_VT_COLOUR, wc); t->shcol = wc; }
        }
    }
}

/* the stock top-left block: hidden while we draw, shown again when we do not (section 5) */
/* 2026-10-13, the owner: 'when you press tab also in game it shows another scoreboard but the new ui always overwrites it ... make sure the
   dead men disappears when youre holding tab'. Tab is the game's TriggerPlayerlist / IngameScores (kl2.exe's GameplayInput text); 0x473530
   sets ZFAPlayerListDisplay +0xed8 by the player's option GamePlayerNames (held / toggle / always). That list is the very element HideStock
   hides, so: while Tab is HELD with the game window in front, our crew list (DEAD MEN, rows, lives, its pictures) is not drawn and the
   stock block is shown again; on release ours comes back. The key is read with user32's GetAsyncKeyState (looked up here: the hook links
   no user32); a TEST build also takes klauto's scripted key. [HUD] TabList=0: off. */
#ifdef KLHOOK_TEST
static int kla_key_held(int dik);
#endif
static int klu_tab_held(void)
{
    static int init; static SHORT (WINAPI *gaks)(int); static HWND (WINAPI *fg)(void); static DWORD (WINAPI *pidof)(HWND, LPDWORD);
    HWND w; DWORD pid = 0;
    if (!klu.tablist) return 0;
#ifdef KLHOOK_TEST
    if (kla_key_held(0x0f)) return 1;                                  /* DIK_TAB, a scripted key */
#endif
    if (!init) {
        HMODULE u = GetModuleHandleA("user32.dll");
        init = 1;
        if (u) { *(FARPROC *)&gaks = GetProcAddress(u, "GetAsyncKeyState"); *(FARPROC *)&fg = GetProcAddress(u, "GetForegroundWindow"); *(FARPROC *)&pidof = GetProcAddress(u, "GetWindowThreadProcessId"); }
    }
    if (!gaks || !fg || !pidof || !(w = fg()) || !pidof(w, &pid) || pid != GetCurrentProcessId()) return 0;
    if ((gaks(0x10) & 0x8000) || (gaks(0x12) & 0x8000)) return 0;       /* run v42: Shift+Tab (the Steam overlay) and Alt+Tab are not the scoreboard key */
    return (gaks(0x09) & 0x8000) != 0;                                   /* VK_TAB */
}

static void klu_hide_tick(DWORD osd, int want)
{
    DWORD el, vt = 0, cl; BYTE h = 0, ch = 0;
    if (!(el = klh_rd32(osd + KLU_O_PLIST)) || !klh_rd(el, &vt, 4) || vt != KLU_PLIST_VT || !klh_rd(el + KLU_E_HIDDEN, &h, 1)) return;
    if (!want && klu_r.hid && h && (cl = klh_rd32(osd + KLU_O_TIME)) != 0 && klh_rd(cl + KLU_E_HIDDEN, &ch, 1) && ch) {
        /* section 5: the game's own hide 0x75f780 has set the clock's +0x25 - and the list's, the byte we hold. The
           hide is the game's now: the byte stays, ours is forgotten. Its 'show' writes 0 to both. */
        klu_r.hid = 0;
        if (klu.log >= 2) klog("hud: the game has hidden the FA set itself (the clock's +0x25 is 1): the stock block's hide is left to the game (%08lx)", el);
        return;
    }
    if (want && h && !klu_r.hid) {
        /* hidden, and not by this state: the list is hidden only by 0x75f780, together with the clock (re\hud.md 2.3).
           With the clock SHOWN the byte is one of ours whose state was dropped (section 5b): taken back, so that it
           is put right when we stand down */
        if ((cl = klh_rd32(osd + KLU_O_TIME)) != 0 && klh_rd(cl + KLU_E_HIDDEN, &ch, 1) && !ch) { klu_r.hid = 1; if (klu.log >= 2) klog("hud: the stock block is already hidden and the clock is not: the hide is taken as ours (%08lx)", el); }
        return;
    }
    if (want && !h) {
        h = 1;
        if (klh_data((void *)(DWORD_PTR)(el + KLU_E_HIDDEN), &h, 1, "ZFAPlayerListDisplay hidden")) {
            if (!klu_r.hid && klu.log) klog("hud: stock block hidden (ZFAPlayerListDisplay %08lx +0x25 = 1: the top-left name / Total score / Round and the stock crew list)", el);
            klu_r.hid = 1;
        }
    } else if (!want && klu_r.hid && h) {
        h = 0;
        if (klh_data((void *)(DWORD_PTR)(el + KLU_E_HIDDEN), &h, 1, "ZFAPlayerListDisplay shown again")) { klu_r.hid = 0; if (klu.log) klog("hud: stock block shown again (%08lx)", el); }
    }
}

/* THE one way the tick stops drawing while an OSD stands: ours off, the stock block shown again (unless the game
   hides it itself - klu_hide_tick) */
static void klu_stand_down(DWORD osd)
{
    InterlockedExchange(&klu_draw_on, 0);
    InterlockedExchange(&klu_skip_list, 0);
    klwd_show(0);                              /* the weapon dial: every call of the ammo panel goes to the stock Render again */
    if (osd && klu_r.hid) klu_hide_tick(osd, 0);
}

/* S5: the game's inset, put back when the level it was changed for is over */
static float klu_inset_old; static int klu_inset_put;
static void klu_inset_back(void)
{
    if (!klu_inset_put) return;
    if (klh_data(KLH_VA(KLU_INSET), &klu_inset_old, 4, "HUD inset [0xceeebc] put back")) { klu_inset_put = 0; if (klu.log) klog("hud: inset [0xceeebc] put back to %.3f (the scene changed)", klu_inset_old); }
}

/* section 3: the sprite handles of pictures 181 (UI_White) and 170 (the car icon), once a level; a picture whose chunk
   is not the 40-byte-record type is not drawn */
static int klu_extra_slot(int k)
{   /* the picture slots tools/kl_hud.py's EXTRAS fill: 111..118 and the ring arcs 123..126, 185, 190 (0 in every stock level's lists) */
    return (k >= 111 && k <= 118) || (k >= 123 && k <= 126) || k == 185 || k == 190;
}
#define KLU_NEXTRA 14

static void klu_pic_prep(DWORD el)
{
    static const int num[2] = { 181, 170 }; DWORD tbl = klh_rd32(el + 8), T = klh_rd32(el + 0xc), h[2] = { 0, 0 }, type[2] = { 0, 0 }; int i;
    klu_r.pic_done = 1;
    if (!tbl || !T || klh_rd32((DWORD_PTR)KLH_VA(KLU_CTX_VT + 0x14)) != KLU_DRAWCHUNK) {
        klog("hud: pictures: the clock element %08lx has no picture table / transform (%08lx, %08lx) or ZDrawBufferSimple's slot 5 is not 0x842d00: no picture is drawn", el, tbl, T); return;
    }
    for (i = 0; i < 2; i++) {
        DWORD chunk;
        if (!klh_rd(tbl + 12 * (DWORD)num[i], &h[i], 4) || !h[i]) { h[i] = 0; continue; }
        chunk = (h[i] & 0x80000000u) ? (h[i] & 0x7fffffffu) : klh_rd32((DWORD_PTR)KLH_VA(KLU_CHUNKTAB) + 4 * h[i]);      /* 0x842d22 .. 0x842d2e */
        type[i] = chunk ? klh_rd32(chunk + 0xc) : 0;
    }
    memset(klu_r.handle, 0, sizeof klu_r.handle);
    {   /* every slot: the same two reads and the same type test (the extras 111..118 of tools/kl_hud.py, the weapon
           pictures, the icons) */
        int k, extra = 0;
        for (k = 0; k < 200; k++) {
            DWORD hk = 0, ck;
            if (!klh_rd(tbl + 12 * (DWORD)k, &hk, 4) || !hk) continue;
            ck = (hk & 0x80000000u) ? (hk & 0x7fffffffu) : klh_rd32((DWORD_PTR)KLH_VA(KLU_CHUNKTAB) + 4 * hk);
            if (ck && klh_rd32(ck + 0xc) == KLU_PICTYPE) { klu_r.handle[k] = hk; if (klu_extra_slot(k)) extra++; }
            if (klu_extra_slot(k) && ck && klh_rd32(ck + 0xc) == KLU_PICTYPE && klh_rd32(ck + 0x10) == 0x10 && klu.extraflags) {
                /* run V1 (2026-10-11): the eight extras load and DRAW NOTHING. The game's per-slot table (0xcee058) has
                   no row for 111..118, so 0x5e3810 loads them with flags 0x10 alone; every stock HUD picture has
                   0x60200 (or 0x60002) | 0x10 at chunk+0x10. A DATA write on the level's own chunk: the flags of
                   UI_White's chunk are copied (GUESS that the draw reads them from the chunk each time). */
                DWORD h181 = 0, c181, f181;
                klh_rd(tbl + 12 * 181u, &h181, 4);
                c181 = !h181 ? 0 : (h181 & 0x80000000u) ? (h181 & 0x7fffffffu) : klh_rd32((DWORD_PTR)KLH_VA(KLU_CHUNKTAB) + 4 * h181);
                f181 = c181 ? klh_rd32(c181 + 0x10) : 0;
                if ((f181 & 0xfff00000u) == 0 && (f181 & 0x60000u)) { *(DWORD *)(DWORD_PTR)(ck + 0x10) = f181; if (klu.log) klog("hud: pictures: slot %d: flags 00000010 -> %08lx (UI_White's)", k, f181); }
            }
            if (klu.log > 1 && ((k >= 108 && k <= 120) || k == 181)) klog("hud: pictures: slot %d: handle %08lx chunk %08lx type %lu, head %08lx %08lx %08lx %08lx", k, hk, ck, ck ? klh_rd32(ck + 0xc) : 0, ck ? klh_rd32(ck) : 0, ck ? klh_rd32(ck + 4) : 0, ck ? klh_rd32(ck + 8) : 0, ck ? klh_rd32(ck + 0x10) : 0);
        }
        if (klu.draft && extra < KLU_NEXTRA) klog("hud: draft: this level has %d of the 14 extra pictures: Draft=1 falls back to plain bars, no rings, no dials, no weapon dial (the level needs the archive of tools/kl_hud.py all, build/hud_x2)", extra);
        if (klu.log) klog("hud: pictures: %d of the 14 extra pictures (slots 111..118, 123..126, 185, 190, tools/kl_hud.py --look deadmen) are in this level%s", extra, extra == KLU_NEXTRA ? "" : " - plates fall back to UI_White, rings are not drawn");
    }
    if (klu.log) klog("hud: pictures: 181 (UI_White) handle %08lx chunk type %lu, 170 (the car icon) handle %08lx chunk type %lu; type %d = the 40-byte record this part writes%s%s",
                      h[0], type[0], h[1], type[1], KLU_PICTYPE, klu_r.handle[181] ? "" : " - 181 IS NOT DRAWN (no plates, bars, outlines)", klu_r.handle[170] ? "" : " - 170 is not drawn");
}

static int klu_fa_shown(DWORD osd)
{   /* the proxy for 'the game shows the FA set now': the clock element enabled and not hidden, 'HUD off' clear */
    DWORD el, vt = 0; BYTE en = 0, h = 1, off = 1;
    if (!(el = klh_rd32(osd + KLU_O_TIME)) || !klh_rd(el, &vt, 4) || (vt != KLU_TIME_VT && vt != (DWORD)(DWORD_PTR)&klu_evt[1])) return 0;   /* ours once wrapped */
    if (!klh_rd(el + KLU_E_ENABLED, &en, 1) || !klh_rd(el + KLU_E_HIDDEN, &h, 1) || !klh_rd(osd + KLU_O_HUDOFF, &off, 1)) return 0;
    return en && !h && !off;
}

static void klu_reset(const char *why, DWORD osd)
{
    if (klu_r.osd && klu.log) klog("hud: osd %08lx is over (%s): texts dropped%s", klu_r.osd, why, klu_r.made ? " (the scene owns them: not freed by the hook)" : "");
    InterlockedExchange(&klu_draw_on, 0);
    EnterCriticalSection(&klu_cs);
    klwd_reset();                                              /* S1: inside the lock, the render slot walks klwd_r under it */
    klht_reset();                                              /* M1 of the tags review: klht_r holds pointers into the scene that just ended */
    memset(&klu_r, 0, sizeof klu_r);
    InterlockedExchange(&klu_esc_at, 0); InterlockedExchange(&klu_esc_rst, 1);
    InterlockedExchange(&klu_keep, 0);                        /* no replacement is drawn now: the stock pop-up and panel are the game's own again */
    klu_r.osd = osd;
    LeaveCriticalSection(&klu_cs);
}

/* ---------------------------------------------------------------- finding the OSD (main thread) */
static DWORD klu_cand[4]; static int klu_ncand, klu_scan_fails; static DWORD klu_scan_t, klu_wait_t;

static int klu_osd_ok(DWORD osd)
{   /* a ZOnScreenDisplay2 with the FA player list whose transform the HUD render has written (1280 x 720) */
    DWORD vt = 0, el, evt = 0; float wh[2] = { 0, 0 };
    return osd && klh_rd(osd, &vt, 4) && vt == KLU_OSD_VT && (el = klh_rd32(osd + KLU_O_PLIST)) != 0 && klh_rd(el, &evt, 4) && evt == KLU_PLIST_VT &&
           klh_rd(osd + KLU_O_XFORM + 0x1c, wh, 8) && wh[0] == 1280.0f && wh[1] == 720.0f;
}

static DWORD klu_osd_direct(int *pending)
{   /* as the game reaches it (0x588680, 0x4ddae0): [[gamedata+0x15dc]] when the byte beside it is not 0xff. klfedkit.c 7
       went this way in the owner's game (its 'cross-fade cut' lines, 18:57). *pending = the holder HAS a
       ZOnScreenDisplay2 that is not ready yet (no player list or the transform not written: the first tick of a
       level, log 16:32:53 / 16:37:44) - the caller waits for it instead of scanning. */
    DWORD gd, hold, osd; BYTE none = 0xff;
    *pending = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(hold = klh_rd32(gd + KLU_OSDHOLD)) || !klh_rd(hold + 4, &none, 1) || none == 0xff) return 0;
    osd = klh_rd32(hold);
    if (klu_osd_ok(osd)) return osd;
    if (osd && klh_rd32(osd) == KLU_OSD_VT) *pending = 1;
    return 0;
}

static int klu_find_osd(void)
{   /* the fall-back: every ZOnScreenDisplay2 in the committed private read-write memory (0.1 - 0.3 s on the main thread:
       only in an Arcade session's round states, at most every 2 s, every 15 s after three empty scans of a scene) */
    MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; static BYTE buf[0x10000]; DWORD t0 = GetTickCount();
    if (klu_scan_t && t0 - klu_scan_t < (klu_scan_fails < 3 ? 2000u : 15000u)) return klu_ncand;
    klu_ncand = 0;
    while ((DWORD_PTR)a < 0x7ffe0000 && VirtualQuery(a, &mbi, sizeof mbi)) {
        if (mbi.State == MEM_COMMIT && mbi.Type == MEM_PRIVATE && (mbi.Protect == PAGE_READWRITE || mbi.Protect == PAGE_EXECUTE_READWRITE)) {
            SIZE_T o, k;
            for (o = 0; o < mbi.RegionSize; o += sizeof buf) {
                SIZE_T n = mbi.RegionSize - o < sizeof buf ? mbi.RegionSize - o : sizeof buf;
                if (!klh_rd((DWORD_PTR)mbi.BaseAddress + o, buf, n)) continue;
                for (k = 0; k + 4 <= n; k += 8) {
                    DWORD v = *(DWORD *)(buf + k);
                    if (v == KLU_OSD_VT && klu_ncand < 4) klu_cand[klu_ncand++] = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + k);
                }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    klu_scan_t = GetTickCount();
    if (klu.log > 1 || (klu.log && klu_ncand)) klog("hud: %d ZOnScreenDisplay2 object(s) found by the scan in %lu ms", klu_ncand, klu_scan_t - t0);
    return klu_ncand;
}

static DWORD klu_current_osd(int may_scan)
{
    DWORD vt, osd; int i, pending;
    if (klu_r.osd && klh_rd(klu_r.osd, &vt, 4) && vt == KLU_OSD_VT) return klu_r.osd;
    if (!may_scan) return 0;                   /* only in an Arcade session's round states */
    if ((osd = klu_osd_direct(&pending)) != 0) { klu_wait_t = 0; return osd; }
    if (pending) {
        /* the game's own OSD is there and not ready: wait for it, no scan (the scan is 0.1 - 0.3 s on the main thread,
           in the countdown). Only when it has not become ready in 10 s does the scan run, as before. */
        DWORD now = GetTickCount();
        if (!klu_wait_t) { klu_wait_t = now | 1; if (klu.log > 1) klog("hud: the game's OSD is there and not ready yet (no FA player list or its transform not written): waiting, no scan"); }
        if (now - klu_wait_t < 10000) return 0;
    }
    if (!klu_find_osd()) { klu_scan_fails++; return 0; }
    for (i = 0; i < klu_ncand; i++) if (klu_osd_ok(klu_cand[i])) { klu_scan_fails = 0; return klu_cand[i]; }
    klu_scan_fails++;
    return 0;
}

static void klu_tick(int game_thread)
{
    static DWORD last, said; static int toldthread, empty;
    DWORD now = GetTickCount(), osd, vt = 0; float wh[2] = { 0, 0 }; char scene[160], why[200]; int state_ok = 0, show, data, allowed, have, tab = 0, crew;
    struct klb_snap pre;
    if (!klu.on || !klh_exe_ok || now - last < 100) return;
    last = now;
    if (!game_thread) {                       /* every call of the game goes between two of its own frames */
        if (!toldthread++ && klu.log > 1) klog("hud: a tick off the game's thread (the first ticks of a start, or [KLHook] Tick=0): nothing is done on those");
        return;
    }
    if (!klh_scene(scene, sizeof scene)) scene[0] = 0;
    /* section 5b: one failed read of the scene name while the level's OSD still stands is not a scene change (it would
       drop the state - the hide forgotten, the byte still 1 - and make a second set of objects). Nothing is done in
       such a tick; after 1 s of it the level is taken to be over. */
    if (!scene[0] && klu_r.scene[0] && klu_r.osd && klh_rd32(klu_r.osd) == KLU_OSD_VT && empty < 10) { empty++; return; }
    empty = 0;
    if (strcmp(scene, klu_r.scene)) {
        /* the old OSD is not touched (it went with its level; its hidden element went with it) */
        klu_reset("the scene changed", 0);
        snprintf(klu_r.scene, sizeof klu_r.scene, "%s", scene);
        klu_scan_fails = 0; klu_scan_t = 0; klu_wait_t = 0;
        klu_inset_back();
    }
    have = klb_read_hud(&pre);                /* klbot.c 1: an Arcade session with its rules object, whatever the state ([HUD] Online: or an online one) */
    /* section 5b: a new round under the same scene name, or at the same address. The round's rules object is another
       one, or the session is before the countdown: what we hold belongs to a level that is over. The stock block is
       shown again first, in case that level still stands: klu_hide_tick writes its one byte only into an element that
       reads as the player list with +0x25 = 1. (In every round seen so far the scene name changed first, and then
       nothing of the old level is touched. ASSUMED harmless otherwise: one byte 1 -> 0.) */
    if (klu_r.osd && have && (pre.state < 0x16 || (klu_r.rules && pre.rules != klu_r.rules))) {
        klu_stand_down(klu_r.osd);
        klu_reset(pre.state < 0x16 ? "the session state is below 0x16" : "the Arcade rules object changed", 0);
        snprintf(klu_r.scene, sizeof klu_r.scene, "%s", scene);
    }
    /* section 4 / 6: a level that is not stock, or any level with Stock=1 */
    allowed = scene[0] && (klu.stock || klb_online_session() || (klx_on && klx_level_verdict(scene, why) == 2));       /* online: any level (cosmetic only; Steam stays blocked by klsteam.c as before) */
    if (scene[0] && !allowed) {
        if (!klu_r.told_stock && have && pre.state == 0x19) { klu_r.told_stock = 1; if (klu.log) klog("hud: this level is stock or not judged ([Expansion] %s): nothing is drawn (Stock=1 draws here too)", klx_on ? "on" : "off"); }
        klu_stand_down(klu_r.osd);
        return;
    }
    /* gate for the search: an Arcade session in the states the FA HUD exists in (0x16 countdown .. 0x19 GO) */
    osd = scene[0] ? klu_current_osd(have && pre.state >= 0x16 && pre.state <= 0x19) : 0;
    if (osd != klu_r.osd) {
        klu_reset("the OSD object changed", osd);
        snprintf(klu_r.scene, sizeof klu_r.scene, "%s", scene);
        if (osd && klu.log) klog("hud: osd %08lx (ZOnScreenDisplay2 with the FA player list at %08lx)", osd, klh_rd32(osd + KLU_O_PLIST));
    }
    /* from here on EVERY exit that does not draw goes through klu_stand_down: the stock block is never left hidden
       with ours not drawing (a fault latched in an earlier tick, the transform, the vtable wrap) */
    if (!osd || !scene[0] || klu_r.fault) { klu_stand_down(osd); return; }
    /* live and drawing: the transform 0x8bf300 writes every HUD frame says 1280 x 720 (re\hud.md 4.1) */
    if (!klh_rd(osd, &vt, 4) || !klh_rd(osd + KLU_O_XFORM + 0x1c, wh, 8) || wh[0] != 1280.0f || wh[1] != 720.0f) { klu_stand_down(osd); return; }
    if (!klu_vtable_tick(osd)) { klu_r.fault = 1; klu_stand_down(osd); return; }
    klu_plist_wrap(osd);
    if (klu.inset > 0 && !klu_r.inset_done) {
        float cur = 0;
        klu_r.inset_done = 1;
        if (klh_rd((DWORD_PTR)KLH_VA(KLU_INSET), &cur, 4) && cur != klu.inset && klh_data(KLH_VA(KLU_INSET), &klu.inset, 4, "HUD inset [0xceeebc]")) {
            if (!klu_inset_put) { klu_inset_old = cur; klu_inset_put = 1; }
            if (klu.log) klog("hud: inset [0xceeebc] %.3f -> %.3f (the game's own elements move with it; put back at the next scene change)", cur, klu.inset);
        }
    }
    EnterCriticalSection(&klu_cs);
    if (!klu_r.made && klu_fa_shown(osd) && have && pre.state >= 0x17 && pre.state <= 0x19) {     /* the layout must exist before the first compose (it reads the places) */
        if (klu_make_all(osd)) { klu_r.made = 1; klu_r.rules = pre.rules; } else klu_r.fault = 1;
    }
    tab = klu_tab_held();
    klu_r.card = tab && klu.tabcard && klu.crew && (!pre.online || klu_ontab);     /* online only with [HUD] OnlineTab=1 */
    if (tab != klu_r.tab) { klu_r.tab = tab; if (klu.log) klog("hud: tab %s: %s", tab ? "HELD" : "released", !tab ? "the crew list is back" : klu_r.card ? "the crew list is drawn as the card in the middle (TabCard=1)" : "the crew list steps aside, the stock list is shown"); }
    crew = klu.crew; if (tab && !klu_r.card) klu.crew = 0;               /* compose / klu_row / klu_lives_row read klu.crew */
    data = klu_r.made && !klu_r.fault ? klu_compose(&state_ok) : 0;
    klu.crew = crew;
    show = data && state_ok && klu_fa_shown(osd);
    if (data) klu_apply();                                   /* may latch a fault */
    LeaveCriticalSection(&klu_cs);
    if (klu_r.fault || !show) klu_stand_down(osd);
    if (klu_r.fault) return;
    if (klu_r.made && (klu.plates || klu.pictest || klu.dials || klu.weapon) && !klu_r.pic_done) klu_pic_prep(klu_r.elem);      /* before the first frame that draws */
    InterlockedExchange(&klu_draw_on, show);
    klwd_show(show);
    if (show && klu.hide && klu.crew && !pre.online && (!tab || klu_r.card)) klu_hide_tick(osd, 1);      /* online the stock list is the only one with data: never hidden */
    else if (tab && !klu_r.card && klu_r.hid) klu_hide_tick(osd, 0);                   /* Tab: the stock list shows (its Tick kept it current) */
    /* the stock list's Render: skipped offline exactly when the byte is wanted (Tab card or not), and ONLINE whenever HideOnline=1 and the HUD
       stands (the owner wants the old HUD gone from online matches too; re\hud_online.md) - 2026-10-26: and only with [HUD] OnlineCrew=1, else
       nothing replaced the stock list online (owner's Steam private match: 'the HUD is missing') */
    InterlockedExchange(&klu_skip_list, klu.hidesrc && (pre.online ? klu.hideonl && klb_hud_crew && (!klu_ontab || !tab || klu_r.card) :(show && klu.hide && klu.crew && (!tab || klu_r.card))));
#ifdef KLHOOK_TEST
    if (klu.oprobe && have) klb_online_probe(&pre, osd, KLU_PLIST_VT);
#endif
    klht_tick(osd, have ? &pre : 0, show);                    /* klhud_tags.c: after the hide (it acts only while klu_r.hid says the stock element is hidden by us) */
    if (klu.probe && klu_probe_ready) {
        const float *a = klu_pr.stock, *b = klu_pr.ours, *p = klu_pr.pic; int same = klu_pr.nours > 0 && b[0] == a[0] && b[2] == a[2] && b[4] == a[4] && b[9] == a[9] && a[0] != 0;
        klu_probe_ready = 0;
        klog("hud: probe: the stock clock appended %ld instance(s); the first: scale %.3f / %.6f / %.6f at (%.3f, %.3f, %.3f)", klu_pr.nstock, a[0], a[2], a[4], a[7], a[8], a[9]);
        klog("hud: probe: our first text (Draw=%d) appended %ld; its instance: scale %.3f / %.6f / %.6f at (%.3f, %.3f, %.3f) - %s", klu.draw, klu_pr.nours, b[0], b[2], b[4], b[7], b[8], b[9],
             same ? "SAME SHAPE as the stock clock's: it is on the HUD plane" : klu_pr.nours > 0 ? "NOT the stock shape: it will not be seen (try Draw=2)" : "NOTHING appended");
        if (klu_r.npic) klog("hud: probe: our first picture appended %ld; its instance: scale %.3f / %.6f / %.6f at (%.3f, %.3f, %.3f)", klu_pr.npic, p[0], p[2], p[4], p[7], p[8], p[9]);
    }
    if (now - said >= 5000 && klu_r.osd) {
        said = now;
        if (klu.probe) InterlockedExchange(&klu_probe_want, 1);
        if (klu.log >= 2) {
            if (!klu_r.made) klog("hud: waiting: FA set shown %d, fault %d", klu_fa_shown(osd), klu_r.fault);
            klog("hud: render: %ld clock-element calls, %ld text draws, %ld refused by the checks, %ld pictures, %ld pictures refused, %ld lock busy (draw_on %ld, %d pictures a frame, largest instance count after our draws %ld)",
                 InterlockedExchange(&klu_n_call, 0), InterlockedExchange(&klu_n_draw, 0), InterlockedExchange(&klu_n_refused, 0), InterlockedExchange(&klu_n_pic, 0), InterlockedExchange(&klu_n_picno, 0),
                 InterlockedExchange(&klu_n_try, 0), klu_draw_on, klu_r.npic, InterlockedExchange(&klu_n_maxinst, 0));
        }
    }
}

static float klu_inif(const char *key, const char *def)
{
    char t[32];
    GetPrivateProfileStringA("HUD", key, def, t, sizeof t, klh_ini);
    return (float)atof(t);
}

static int klu_inii(const char *key, int def, int lo, int hi)
{
    int v = (int)GetPrivateProfileIntA("HUD", key, def, klh_ini);
    return v < lo ? lo : v > hi ? hi : v;
}

static void klu_init(void)
{
    InitializeCriticalSection(&klu_cs);
    klu.on = GetPrivateProfileIntA("HUD", "Enable", 0, klh_ini) != 0;
    if (!klu.on) return;
    klu.log = klu_inii("Log", 1, 0, 2);
    klu.stock = klu_inii("Stock", 0, 0, 1);
    klb_hud_online = klu_inii("Online", 0, 0, 1);         /* 2026-10-18: the local, cosmetic parts in a network FA round (klbot.c klb_read_hud; re/hud_online.md). Default 0: never run online */
    klu_onnames = klu_inii("OnlineNames", 0, 0, 1); klu_onkill = klu_inii("OnlineKilled", 0, 0, 1); klu_onround = klu_inii("OnlineRound", 0, 0, 1);
    klu_onkillai = klu_inii("OnlineKilledAI", 0, 0, 1); klor_aikill = klu_onkillai;
    klu_onfeed = klu_inii("OnlineFeed", 0, 0, 1); klu_onskull = klu_inii("OnlineSkulls", 0, 0, 1); klu_onloot = klu_inii("OnlineLoot", 0, 0, 1); klu_ontab = klu_inii("OnlineTab", 0, 0, 1); klu_onvan = klu_inii("OnlineVan", 0, 0, 1); klu_onvanicon = klu_inii("OnlineVanIcon", 0, 0, 1);
    klu.onbots = klu_inii("OnlineBots", 1, 0, 1); klu.killed = klu_inii("KilledBy", 1, 0, 1); klu.crew = klu_inii("Crew", 1, 0, 1); klu.money = klu_inii("Money", 1, 0, 1); klu.round = klu_inii("Round", 1, 0, 1);
    klu.hide = klu_inii("HideStock", 1, 0, 1);
    klu.draw = klu_inii("Draw", 1, 1, 2);
    klu.shadow = klu_inii("Shadow", 1, 0, 1); if (klu.draw == 2) klu.shadow = 1;     /* the stock Render draws a pair */
    klu_hideidle = klu_inii("HideIdleEscape", 1, 0, 1); klu_hideidle_dry = klu_inii("HideIdleEscapeDry", 0, 0, 1);
    kluv_early = klu_inii("TraitorEarly", 0, 0, 1); kluv_ucchide = klu_inii("UccHide", 1, 0, 1);       /* re/ucc_tell_audit.md S10 */       /* 2026-10-13: 0 = no row / fate shows a bot's planned betrayal (klhud_values.c) */
    klu.tags = klu_inii("Tags", 1, 0, 1); klu.cashshort = klu_inii("CashShort", 1, 0, 1); klu.totalfont = klu_inii("TotalFont", 0, 0, 1);
    klu.draft = klu_inii("Draft", 0, 0, 1);              /* the whole draft: the defaults of Plates, Dials, Weapon, RoundOf (and klhud_popup.c's Popups, LootRing) become 1; a key that is set still wins */
    klu.wini = klu.wstyle = klu_inii("WatchStyle", 0, 0, 1);       /* review MUST 2: default 0 (old extras on the installed maps); set 1 ONLY with maps baked by kl_hud.py --watch 1 */ klu.wseconds = klu_inii("WatchSeconds", 0, 0, 1); klu.wwear = klu_inii("WatchWear", 1, 0, 1); klu.wlast = klu_inii("WatchLast", 1, 0, 1); klu.mfill = klu_inii("MoneyFill", 1, 0, 1); klu.vanicon = klu_inii("VanIcon", 1, 0, 1); klu.tablist = klu_inii("TabList", 1, 0, 1); klu.tabcard = klu_inii("TabCard", 0, 0, 1); klu.hidesrc = klu_inii("HideSrc", 1, 0, 1); klu.hideonl = klu_inii("HideOnline", 1, 0, 1); klu.oprobe = klu_inii("OnlineProbe", 0, 0, 1); klb_hud_crew = klu_inii("OnlineCrew", 0, 0, 1);       /* 2026-10-13: slot 117 is 256 x 32 in BOTH watch bakes (the old 'frame' before 652db0c, 'mfill' after), so the hook cannot tell them apart - MoneyFill=0 keeps the old flat bar on maps baked before 652db0c (the owner's hud_tab_wm set), where 117 would draw an empty outline */       /* review SHOULD 3: blank the stock red digits in the last minute (they would sit on the hands) */
    klu.labelbar = klu_inii("LabelBar", 1, 0, 2); klu.labelslash = klu_inii("LabelSlash", 1, 0, 1);      /* the watch look (re\hud_hook.md 14): the level must be baked with kl_hud.py --watch <the same 0 / 1> */
    klu.dials = klu_inii("Dials", klu.draft, 0, 1);      /* the round watch + the escape dial (needs the level's extra pictures 113 / 114) */
    klu.weapon = klu_inii("Weapon", klu.draft, 0, 1); klwd_init();      /* the weapon dial (klhud_weapon.c; needs 113 / 114 too) */
    klu.lives = klu_inii("Lives", klu.draft, 0, 3);              /* 0 none, 1 three skull pictures (178) in your row - 'LIVES n' in the round line when the level has no such picture -, 2 TEST: skull glyphs after your name (the stock way), 3 'LIVES n' in the round line */
    klu.roundof = klu_inii("RoundOf", klu.draft, 0, 1);  /* 1 = 'ROUND n OF m' with the game's own m (10 in Arcade; whether a session ends there is not established) */
    klu.plates = klu_inii("Plates", klu.draft, 0, 1); klu.anchor = klu_inii("PicAnchor", 1, 0, 1); klu.left = klu_inii("LeftStyle", 0x11, 0, 255); klu.extraflags = klu_inii("ExtraFlags", 1, 0, 1); klu.pictest = klu_inii("PicTest", 0, 0, 1);
    klu.fontset = klu_inii("Fonts", klu.draft, 0, 1);       /* TYPE: roles -> fonts and the centring (needs a level baked by kl_hud.py --look deadmen from 2026-10-11) */
    {   static const char *kn[KLU_NFONT] = { "FontName", "FontBig", "FontLabel", "FontSmall" }; static const char *dflt[KLU_NFONT] = { "0xd54", "0xd50", "0xd5c", "0xd58" };
        static const char *cn[KLU_NFONT] = { "Cap0", "Cap1", "Cap2", "Cap3" }; static const char *cd[KLU_NFONT] = { "11", "15", "10", "10" }   /* the Anton / Montserrat bake of kl_hud.py, quiet sizes (2026-10-11; before 19 / 30 / 10 / 15, run T1) */; int fi;
        for (fi = 0; fi < KLU_NFONT; fi++) {
            char t[32]; GetPrivateProfileStringA("HUD", kn[fi], dflt[fi], t, sizeof t, klh_ini); klu.fofs[fi] = (DWORD)strtoul(t, 0, 0);
            if (klu.fofs[fi] < 0xd40 || klu.fofs[fi] > 0xd5c || (klu.fofs[fi] & 3)) klu.fofs[fi] = (DWORD)strtoul(dflt[fi], 0, 0);
            klu.cap[fi] = klu_inif(cn[fi], cd[fi]); if (!(klu.cap[fi] >= 4 && klu.cap[fi] <= 60)) klu.cap[fi] = (float)atof(cd[fi]);
        }
    }
    klu.grid = klu_inii("Grid", 0, 0, 2); klu.probe = klu_inii("Probe", 0, 0, 1);
    klu.layer = klu_inii("Layer", 0xd, 4, 15);      /* min 4 (cloud review W3): the dial case is drawn at layer - 4, and a negative layer is the byte 0xff = on top */
    klu.rows = klu_inii("Rows", KLU_ROWS, 1, KLU_ROWS);
    if (!klu_inii("Rows12", 1, 0, 1) && klu.rows > KLU_ROWS_OLD) klu.rows = KLU_ROWS_OLD;      /* [HUD] Rows12=0 (default 1, "recommended on"): the old 8-row cap; Rows=n still lowers it. Rows shown = players present, never padded to 12 */
    klu.inset = klu_inif("Inset", "-1"); if (!(klu.inset > 0 && klu.inset < 0.25f)) klu.inset = -1;
    klu.crew_x = klu_inif("CrewX", klu.draft ? "33" : "-1"); klu.crew_y = klu_inif("CrewY", klu.draft ? "38" : "-1"); klu.crew_w = klu_inif("CrewW", "211");
    klu.money_x = klu_inif("MoneyX", klu.draft ? "1247" : "-1"); klu.money_y = klu_inif("MoneyY", "-1"); klu.money_w = klu_inif("MoneyW", "211"); klu.round_y = klu_inif("RoundY", "-1");
    klu.row = klu_inif("Row", klu.draft ? "21" : "24"); if (!(klu.row >= 8 && klu.row <= 64)) klu.row = klu.draft ? KLU_D_ROW : 24.0f;
    klu.yoff = klu.draft ? KLU_D_YOFF : 30.0f; klu.blockup = klu.draft ? KLU_D_BLOCKUP : 4.0f; klu.blockh = klu.draft ? KLU_D_BLOCKH : klu.row; klu.padx = klu.draft ? KLU_D_PADX : 6.0f;      /* M2 (re/hud_layout.md: names at +8 / y 72 + 30 i, cash at right - 8, block 219 x 28) */
    if (!(klu.crew_x <= 1280)) klu.crew_x = -1; if (!(klu.crew_y <= 720)) klu.crew_y = -1; if (!(klu.money_x <= 1280)) klu.money_x = -1;
    if (!(klu.money_y <= 720)) klu.money_y = -1; if (!(klu.round_y <= 720)) klu.round_y = -1;
    if (!(klu.crew_w >= 80 && klu.crew_w <= 640)) klu.crew_w = 211; if (!(klu.money_w >= 80 && klu.money_w <= 640)) klu.money_w = 211;
    klht_init();                                              /* klhud_tags.c: [HUD] HeadTags / HeadShadow / HeadLine */
    klog("hud: on (Version 3: the draft's crew list, round line, money box + the parts: values, weapon dial, pop-ups; Draft=%d Dials=%d Weapon=%d Lives=%d RoundOf=%d); Stock=%d Log=%d Crew=%d Money=%d Round=%d HideStock=%d Draw=%d (1 own Draw with the 16:34 xform, 2 through the stock clock's Render) Shadow=%d Tags=%d CashShort=%d TotalFont=%d Plates=%d PicAnchor=%d PicTest=%d Grid=%d Probe=%d Layer=%d Rows=%d Inset=%.3f; Arcade only; VERSION 2 HAS NOT RUN IN THE GAME",
         klu.draft, klu.dials, klu.weapon, klu.lives, klu.roundof, klu.stock, klu.log, klu.crew, klu.money, klu.round, klu.hide, klu.draw, klu.shadow, klu.tags, klu.cashshort, klu.totalfont, klu.plates, klu.anchor, klu.pictest, klu.grid, klu.probe, klu.layer, klu.rows, klu.inset);
}

#endif /* KLHUD_C */
