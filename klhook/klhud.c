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

#define KLU_ROWS        8
#define KLU_T_HEAD      0                     /* 'DEAD MEN' */
#define KLU_T_COUNT     1                     /* '5 / 8' */
#define KLU_T_NAME(i)   (2 + 2 * (i))
#define KLU_T_CASH(i)   (3 + 2 * (i))
#define KLU_T_ROUND     18
#define KLU_T_MLABEL(k) (19 + 2 * (k))        /* k = 0 TOTAL, 1 LOOT, 2 REWARDS */
#define KLU_T_MVALUE(k) (20 + 2 * (k))
#define KLU_T_GRID      25
#define KLU_NSWEEP      8                     /* Grid: one label per candidate style byte */
#define KLU_NGRID       (10 + KLU_NSWEEP)
#define KLU_T_WEAP      (KLU_T_GRID + KLU_NGRID)      /* klhud_weapon.c: the first gun's count, the other gun's, the label */
#define KLU_NWEAP       3
#define KLU_NTEXT       (KLU_T_WEAP + KLU_NWEAP)      /* LAST: every part that adds texts goes before this line (klhud_values.c / klhud_popup.c add none) */
#define KLU_NPIC        224                   /* rings are drawn dab by dab (Dials) */
#define KLU_TEXTLEN     64
#define KLU_STYLE_LEFT  (klu.left)        /* [HUD] LeftStyle: 0x44 turned out CENTRED at x (run H1_DM03_hud); 0x11 is a GUESS until the sweep of Grid shows it */
#define KLU_STYLE_CENTRE 0x44
#define KLU_STYLE_RIGHT 0x12
#define KLU_SHADOW_RGB  0x80000000u

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

static const int klu_sweep[8] = { 0x11, 0x14, 0x21, 0x41, 0x01, 0x10, 0x42, 0x24 };
struct klu_text { DWORD obj, shadow; float x, y; int on, style, big, plain, noshadow; DWORD colour, want_colour; char cur[KLU_TEXTLEN], want[KLU_TEXTLEN]; };
struct klu_picq { int n; float x, y, w, h; DWORD argb; int layer; };

static struct {
    int left;                                 /* LeftStyle */
    int extraflags;                           /* ExtraFlags: give the eight extra pictures a stock picture's chunk flags */
    int weapon;                               /* Weapon: the weapon dial (klhud_weapon.c) */
    int draft;                                /* Draft: the defaults of every part of the draft are 1 */
    int lives, roundof;                       /* Lives, RoundOf (klhud_values.c) */
    int on, log, stock, crew, money, round, hide, shadow, tags, cashshort, totalfont, draw, plates, anchor, pictest, grid, probe, layer, rows, dials;
    float inset, crew_x, crew_y, crew_w, row, money_x, money_y, money_w, round_y;
    float yoff, blockup, blockh, padx;        /* the rows: the text's y under the head, the block's rise above it, its height, the text's side margin (the draft: 34 / 5 / 28 / 8) */
} klu;

static struct {
    DWORD osd, elem, tmpl, font, bigfont, parent, rules; char scene[160];
    DWORD handle[200];                        /* the sprite handle of every HUD picture whose chunk is type 5, else 0 (section 3; klu_pic_prep) */
    float clock_max; int watch;               /* Dials: the longest round clock seen this round; 1 = the watch stands for the stock clock's digits */
    int made, fault, hid, inset_done, told_stock, pic_done;
    float cx, cy, mx, my, ry, wy;             /* the layout of this level (the keys, or the inset) */
    struct klu_text t[KLU_NTEXT];
    struct klu_picq pic[KLU_NPIC]; int npic;
} klu_r;
static volatile LONG klu_draw_on;             /* read by the render slot: 1 = objects exist and the round shows the HUD */
static volatile LONG klu_n_call, klu_n_try, klu_n_draw, klu_n_refused, klu_n_pic, klu_n_picno, klu_n_maxinst;
static volatile LONG klu_probe_want, klu_probe_ready;
static struct { float stock[14], ours[14], pic[14]; LONG nstock, nours, npic; } klu_pr;
static CRITICAL_SECTION klu_cs;
static DWORD klu_evt[KLU_ELEM_NSLOT + 1];     /* [0] RTTI locator, [1..] the slots */
static int klu_evt_ready;
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
            if (klu.draw == 2) ok = klu_draw_stock(el, ctx, cam, t->obj, t->shadow, t->x, t->y);
            else {
                if (klu.shadow && t->shadow && !t->noshadow) klu_draw_one(t->shadow, ctx, cam, t->x + 2.0f, t->y + 2.0f);     /* 0xbbe4ec / 0xbbe4f0 = 2.0 */
                ok = klu_draw_one(t->obj, ctx, cam, t->x, t->y);
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
    return r;
}

/* ---------------------------------------------------------------- the private vtable (main thread) */

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

/* the places of every text of this level (1280 x 720 virtual pixels); re\hud_hook.md 3 has the same numbers as a table */
static void klu_layout(void)
{
    float inset = 0.05f, x0, x1, y; int i, k;
    klh_rd((DWORD_PTR)KLH_VA(KLU_INSET), &inset, 4);
    if (!(inset >= 0 && inset < 0.25f)) inset = 0.05f;
    klu_r.cx = klu.crew_x >= 0 ? klu.crew_x : 1280.0f * inset;
    klu_r.cy = klu.crew_y >= 0 ? klu.crew_y : 720.0f * inset;
    klu_r.mx = klu.money_x >= 0 ? klu.money_x : 1280.0f - 1280.0f * inset;
    klu_r.wy = 720.0f * inset + 30.0f;                                       /* Dials: the watch's middle (66 at the game's inset) */
    klu_r.ry = klu.round_y >= 0 ? klu.round_y : 720.0f * inset + (klu.dials ? 72.0f : 58.0f);      /* under the clock's two lines (y, y + 28), or under the watch */
    klu_r.my = klu.money_y >= 0 ? klu.money_y : 720.0f * inset + (klu.dials ? 100.0f : 87.0f);     /* 123 at the game's inset = the draft's 9.6 % of the width */
    for (i = 0; i < KLU_NTEXT; i++) { klu_r.t[i].style = KLU_STYLE_LEFT; klu_r.t[i].want_colour = KLU_C_CHALK; }
    x0 = klu_r.cx; x1 = klu_r.cx + klu.crew_w;
    klu_r.t[KLU_T_HEAD].x = x0; klu_r.t[KLU_T_HEAD].y = klu_r.cy; klu_r.t[KLU_T_HEAD].want_colour = KLU_C_CORAL;
    klu_r.t[KLU_T_COUNT].x = x1; klu_r.t[KLU_T_COUNT].y = klu_r.cy; klu_r.t[KLU_T_COUNT].style = KLU_STYLE_RIGHT;
    for (i = 0; i < KLU_ROWS; i++) {
        y = klu_r.cy + klu.yoff + klu.row * i;
        klu_r.t[KLU_T_NAME(i)].x = x0 + klu.padx; klu_r.t[KLU_T_NAME(i)].y = y;
        klu_r.t[KLU_T_CASH(i)].x = x1 - klu.padx; klu_r.t[KLU_T_CASH(i)].y = y; klu_r.t[KLU_T_CASH(i)].style = KLU_STYLE_RIGHT;
    }
    klu_r.t[KLU_T_ROUND].x = klu_r.mx; klu_r.t[KLU_T_ROUND].y = klu_r.ry; klu_r.t[KLU_T_ROUND].style = KLU_STYLE_RIGHT;
    if (klu.draft) klu_r.t[KLU_T_ROUND].want_colour = KLU_C_CORAL;                     /* S5: the draft's round line is coral */
    for (k = 0; k < 3; k++) {
        y = klu_r.my + (k == 0 ? 0.0f : 40.0f + 24.0f * (k - 1));            /* TOTAL, the bar at +26 .. +34, LOOT +40, REWARDS +64 */
        klu_r.t[KLU_T_MLABEL(k)].x = klu_r.mx - klu.money_w; klu_r.t[KLU_T_MLABEL(k)].y = y; klu_r.t[KLU_T_MLABEL(k)].want_colour = KLU_C_CORAL;
        klu_r.t[KLU_T_MVALUE(k)].x = klu_r.mx; klu_r.t[KLU_T_MVALUE(k)].y = y; klu_r.t[KLU_T_MVALUE(k)].style = KLU_STYLE_RIGHT;
        klu_r.t[KLU_T_MVALUE(k)].want_colour = k == 0 ? KLU_C_GREENHI : KLU_C_GREEN;
    }
    klu_r.t[KLU_T_MVALUE(0)].big = klu.totalfont;
    klu_r.t[KLU_T_WEAP + 0].style = klu_r.t[KLU_T_WEAP + 1].style = KLU_STYLE_RIGHT; klu_r.t[KLU_T_WEAP + 2].style = KLU_STYLE_CENTRE;      /* klhud_weapon.c: the counts right-aligned, the label centred under the disc */
    {   /* the Grid labels: their style is fixed when the object is made (klu_grid fills the same order) */
        int gs[KLU_NGRID] = { KLU_STYLE_LEFT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_RIGHT, KLU_STYLE_LEFT, KLU_STYLE_RIGHT, KLU_STYLE_LEFT, KLU_STYLE_RIGHT };
        for (i = 0; i < KLU_NSWEEP; i++) gs[10 + i] = klu_sweep[i];
        for (i = 0; i < KLU_NGRID; i++) { klu_r.t[KLU_T_GRID + i].plain = 1; klu_r.t[KLU_T_GRID + i].style = gs[i]; klu_r.t[KLU_T_GRID + i].want_colour = KLU_C_CORAL; }
    }
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
    klu_layout();
    for (i = 0; i < KLU_NTEXT; i++) {
        struct klu_text *t = &klu_r.t[i];
        if (i >= KLU_T_GRID && i < KLU_T_WEAP && !klu.grid) continue;
        if (i >= KLU_T_WEAP && !klu.weapon) continue;
        t->colour = t->want_colour;
        if (!(t->obj = klu_make_obj(tmpl, t->big && big ? big : font, t->style, t->colour, klu.layer, why))) { klog("hud: osd %08lx: text %d: %s; the HUD stands down for this level", osd, i, why); return 0; }
        n++;
        if (klu.shadow && (!t->plain || klu.draw == 2)) {      /* Draw=2: the stock Render draws a pair, so the Grid labels get a shadow too */
            if (!(t->shadow = klu_make_obj(tmpl, t->big && big ? big : font, t->style, KLU_SHADOW_RGB, klu.layer - 1, why))) { klog("hud: osd %08lx: shadow %d: %s; the HUD stands down for this level", osd, i, why); return 0; }
            ns++;
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

static void klu_addpic(int n, float x, float y, float w, float h, DWORD argb, int layer)
{
    struct klu_picq *p;
    if (klu_r.npic >= KLU_NPIC || w <= 0 || h <= 0) return;
    p = &klu_r.pic[klu_r.npic++];
    p->n = n; p->x = x; p->y = y; p->w = w; p->h = h; p->argb = argb; p->layer = layer;
}

static void klu_outline(float x, float y, float w, float h, DWORD argb, int layer)
{   /* four 1 px bars */
    klu_addpic(181, x, y, w, 1.0f, argb, layer); klu_addpic(181, x, y + h - 1.0f, w, 1.0f, argb, layer);
    klu_addpic(181, x, y, 1.0f, h, argb, layer); klu_addpic(181, x + w - 1.0f, y, 1.0f, h, argb, layer);
}

/* DIALS ([HUD] Dials=1; re\hud_layout.md; NOT RUN IN THE GAME). A ring that empties is n brush dabs (picture 113) on a
   circle: dab k stands at 2 pi k / n clockwise from the top, and only the dabs of the part that is LEFT are drawn - the
   empty part begins at the top and grows clockwise, as on the owner's draft. */
static void klu_ring(float cx, float cy, float r, int n, float left, float dw, float dh, DWORD argb, int layer)
{
    int k, first;
    if (!klu_r.handle[113]) return;
    if (!(left > 0)) return;
    if (left > 1.0f) left = 1.0f;
    first = (int)((1.0f - left) * n + 0.5f);
    for (k = first; k < n; k++) {
        float a = 6.2831853f * (float)k / (float)n;
        klu_addpic(113, cx + r * (float)sin(a) - dw * 0.5f, cy - r * (float)cos(a) - dh * 0.5f, dw, dh, argb, layer);
    }
}

static void klu_dials(const struct klb_snap *s)
{
    float clock = 0, cx = klu_r.mx - 35.0f, cy = klu_r.wy; int i;
    klu_r.watch = 0;
    if (!klu.dials || !klu_r.handle[113] || !klu_r.handle[114]) return;
    /* the round watch: the float the stock clock prints, [rules+0x4c], against the round's length [score+0x3c]
       (klhud_values.c f); a clock above the length (something set a longer time) is measured against left + played */
    if (klu.grid == 2) { clock = 219.0f; klu_r.clock_max = 360.0f; }
    else { clock = kluv_round_left(s); klu_r.clock_max = kluv_round_len(s); if (clock > klu_r.clock_max) klu_r.clock_max = clock + kluv_round_played(s); }
    if (clock > 60.0f && klu_r.clock_max > 60.0f) {
        float left = clock / klu_r.clock_max, a = 6.2831853f * (1.0f - left);
        klu_addpic(114, cx - 34.5f, cy - 34.5f, 69.0f, 69.0f, 0x9c080809u, klu.layer - 2);
        klu_ring(cx, cy, 29.0f, 40, left, 8.0f, 8.0f, KLU_C_CHALK, klu.layer);       /* run V2: 24 dabs read as beads - 40 overlap into a painted ring */
        for (i = 1; i <= 5; i++)                                   /* the hand: five small dabs from the hub to the ring's edge of 'now' */
            klu_addpic(113, cx + 4.4f * i * (float)sin(a) - 2.5f, cy - 4.4f * i * (float)cos(a) - 2.5f, 5.0f, 5.0f, KLU_C_CHALK, klu.layer);
        klu_addpic(113, cx - 4.0f, cy - 4.0f, 8.0f, 8.0f, KLU_C_CHALK, klu.layer);
        klu_r.watch = 1;                                           /* the render slot blanks the stock clock's digits while this is set */
    }
    /* the escape dial: the vehicle waits (state 3 / 4), [rules+0x1d8] = the seconds it still waits, 8 s a visit (klbot.c) */
    i = kluv_vehicle_pic(s) == KLUV_PIC_CHOPPER && klu_r.handle[KLUV_PIC_CHOPPER] ? KLUV_PIC_CHOPPER : KLUV_PIC_CAR;      /* a ZHeli: the helicopter (171); both kinds of car: 170 (klhud_values.c e) */
    if ((s->veh == 3 || s->veh == 4 || klu.grid == 2) && klu_r.handle[i]) {
        float ex = cx - 75.0f, ey = cy + 5.0f, left = klu.grid == 2 ? 0.35f : s->timer / 8.0f;
        klu_addpic(114, ex - 27.5f, ey - 27.5f, 55.0f, 55.0f, 0x9c080809u, klu.layer - 2);
        klu_ring(ex, ey, 23.0f, 32, left, 7.0f, 7.0f, KLU_C_ORANGE, klu.layer);
        klu_addpic(i, ex - 15.0f, ey - 15.0f, 30.0f, 30.0f, KLU_C_CHALK, klu.layer);
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
    if (block) klu_addpic(klu_r.handle[111] ? 111 : 181, klu_r.cx - 4.0f, y - klu.blockup, klu.crew_w + 8.0f, klu.blockh, kind == 1 ? KLU_C_CHALK : KLU_C_ORANGE, klu.layer - 2);   /* 111 = the painted stroke (kl_hud extras) */
    if (kind == 3) {
        if (klu.draft) {                                           /* M2, the draft: (name width + 12) x 4 from x 33 + 2, centred on the row (name y + 7) */
            const unsigned char *c; float w = 0;
            for (c = (const unsigned char *)name; *c; c++) if ((*c & 0xc0) != 0x80) w += KLUV_NAME_CHARW;
            klu_addpic(klu_r.handle[112] ? 112 : 181, klu_r.cx + 2.0f, y + 7.0f, w + 12.0f, 4.0f, KLU_C_DEAD, klu.layer);
        } else klu_addpic(klu_r.handle[112] ? 112 : 181, klu_r.cx + 2.0f, y + 6.0f, klu.crew_w * 0.62f, klu_r.handle[112] ? 8.0f : 3.0f, KLU_C_DEAD, klu.layer);       /* the strike-through, over the name: 112 = the dry stroke */
    }       /* the strike-through, over the name: 112 = the dry stroke */
}

/* the own row's lives (re\hud_layout.md): three skull pictures (178) after the name, the lost ones faint. The name's
   width is an estimate and every number a named guess in klhud_values.c (a) until a picture has shown the row */
static void klu_lives_row(int row, const char *name, int lives, int block)
{
    float y = klu_r.cy + klu.yoff + klu.row * row + (klu.draft ? 3.0f : kluv_skull_y(klu.row)); int k;      /* the draft: the block's middle (28 high, 5 above the text) */
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
    box[2].name = "MONEY"; box[2].x0 = klu_r.mx - klu.money_w; box[2].y0 = klu_r.my; box[2].x1 = klu_r.mx; box[2].y1 = klu_r.my + 86.0f;
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

/* -> every text's wanted string and colour and the picture list; 0 = nothing to show (no Arcade round) */
static int klu_compose(int *state_ok)
{
    struct klb_snap s; int i, row = 0, human, used = 0, alive = 0; long total = 0, loot = 0, rewards = 0; DWORD cat[0x3c / 4]; char name[56]; int lives = 0, rn = 0, rm = 0;
    *state_ok = 0;
    if (!klb_read(&s)) return 0;                              /* klbot.c 1: Arcade, ZGameRulesHeist, the records */
    /* the stock player list's own window (its Tick 0x76db00). Draw=2: the stock clock Render draws nothing outside
       state 0x19 (0x81e0c3), so ours is 'shown' - and the stock block hidden - only there */
    *state_ok = klu.draw == 2 ? s.state == 0x19 : s.state >= 0x17 && s.state <= 0x19;
    for (i = 0; i < KLU_NTEXT; i++) { klu_r.t[i].on = 0; klu_r.t[i].noshadow = 0; }
    klu_r.npic = 0;
    human = s.human >= 0 ? s.human : 0;
    lives = klu.grid == 2 ? 2 : kluv_lives(&s);               /* byte [score+0x6c]; +0x44 is the number of rounds (klhud_values.c a, c) */
    if (klu.grid == 2) {                                    /* the draft's own eight rows: every state on one picture */
        static const struct { const char *n; long m; int kind; } demo[KLU_ROWS] = { { "J.C.", 540000, 1 }, { "KANE", 310000, 0 }, { "LYNCH", 0, 0 }, { "PARKER", 860000, 2 },
                                                                                    { "TOMMY", 120000, 0 }, { "RED", 400000, 4 }, { "MELDAL", 0, 3 }, { "ASHKANAN", 1250000, 3 } };
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
        if (!name[0]) snprintf(name, sizeof name, r->flags & 1 ? "Heister %d" : "You", i);
        kind = kluv_kind(&s, i);                              /* klhud_values.c g: THE row decision (dead / waiting, escaped, fed before traitor, traitor, you, crew) */
        if (i == human && (kind == KLUV_K_YOU || kind == KLUV_K_TRAITOR)) {
            if (klu.lives == 2) {                             /* TEST: the stock list's own way, skull glyphs U+E018 appended to the name (0x6f3116) */
                size_t l = strlen(name); int nl = lives > KLUV_LIVES_MAX ? KLUV_LIVES_MAX : lives;
                if (nl && l + 4 * (size_t)nl < sizeof name) kluv_skulls(name + l, (int)(sizeof name - l), nl);
            } else {                                          /* the draft: three skull pictures after the name (and after the tag, when the row carries one) */
                char full[96];
                snprintf(full, sizeof full, "%s%s", name, kind == KLUV_K_TRAITOR && klu.tags ? "  TRAITOR" : "");
                klu_lives_row(row, full, lives, klu.plates);
            }
        }
        klu_row(row++, name, (long)r->money, kind);
    }
    if (klu.crew) {
        strcpy(klu_r.t[KLU_T_HEAD].want, "DEAD MEN"); klu_r.t[KLU_T_HEAD].on = 1; klu_r.t[KLU_T_HEAD].want_colour = KLU_C_CORAL;
        snprintf(klu_r.t[KLU_T_COUNT].want, KLU_TEXTLEN, "%d / %d", alive, used); klu_r.t[KLU_T_COUNT].on = 1;
        if (klu.plates) {                                     /* the painted rule: the draft's pic 112, 211 x 5, centre y 22 under the head */
            if (klu.draft) klu_addpic(klu_r.handle[112] ? 112 : 181, klu_r.cx, klu_r.cy + 19.5f, klu.crew_w, 5.0f, KLU_C_CHALK, klu.layer - 2);
            else klu_addpic(181, klu_r.cx, klu_r.cy + 22.0f, klu.crew_w, 3.0f, KLU_C_CHALK, klu.layer - 2);
        }
    }
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
        {
            char of[16] = "", lv[16] = "";
            if (klu.roundof && rm > 0) snprintf(of, sizeof of, " OF %d", rm);          /* the game's own number: 10 in Arcade */
            if (klu.lives == 3 || (klu.lives == 1 && !klu_r.handle[KLUV_SKULL_PIC])) snprintf(lv, sizeof lv, "   LIVES %d", lives);   /* digits: on request, or when this level has no skull picture */
            snprintf(klu_r.t[KLU_T_ROUND].want, KLU_TEXTLEN, "ROUND %d%s%s", rn, of, lv);
        }
        klu_r.t[KLU_T_ROUND].on = klu.round;
        if (klu.plates && klu.money) {                        /* the framed bar under TOTAL (re\hud_layout.md): what the crew holds of the level's loot ([rules+0xdd0], klhud_values.c d); a level that registered no loot: how much of your total you carry */
            float x = klu_r.mx - klu.money_w, y = klu_r.my + 26.0f, f = total > 0 && loot > 0 ? (float)loot / (float)total : 0.0f;
            if (klu.grid == 2) f = 0.16f;
            else if (kluv_loot_total(&s) > 0) f = kluv_loot_share(&s);
            if (f > 1.0f) f = 1.0f;
            klu_outline(x, y, klu.money_w, 8.0f, KLU_C_CHALK, klu.layer - 2);
            klu_addpic(181, x - 2.0f, y - 2.0f, klu.money_w * f, 12.0f, KLU_C_CHALK, klu.layer - 2);
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
    }
}

/* the stock top-left block: hidden while we draw, shown again when we do not (section 5) */
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
            if (ck && klh_rd32(ck + 0xc) == KLU_PICTYPE) { klu_r.handle[k] = hk; if (k >= 111 && k <= 118) extra++; }
            if (k >= 111 && k <= 118 && ck && klh_rd32(ck + 0xc) == KLU_PICTYPE && klh_rd32(ck + 0x10) == 0x10 && klu.extraflags) {
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
        if (klu.draft && extra < 8) klog("hud: draft: this level has %d of the 8 extra pictures: Draft=1 falls back to plain bars, no rings, no dials, no weapon dial (the level needs the archive of tools/kl_hud.py all, build/hud_x2)", extra);
        if (klu.log) klog("hud: pictures: %d of the 8 extra pictures (slots 111..118, tools/kl_hud.py --look deadmen) are in this level%s", extra, extra == 8 ? "" : " - plates fall back to UI_White, rings are not drawn");
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
    memset(&klu_r, 0, sizeof klu_r);
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
    DWORD now = GetTickCount(), osd, vt = 0; float wh[2] = { 0, 0 }; char scene[160], why[200]; int state_ok = 0, show, data, allowed, have;
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
    have = klb_read(&pre);                    /* klbot.c 1: an Arcade session with its rules object, whatever the state */
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
    allowed = scene[0] && (klu.stock || (klx_on && klx_level_verdict(scene, why) == 2));
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
    data = klu_r.made && !klu_r.fault ? klu_compose(&state_ok) : 0;
    show = data && state_ok && klu_fa_shown(osd);
    if (data) klu_apply();                                   /* may latch a fault */
    LeaveCriticalSection(&klu_cs);
    if (klu_r.fault || !show) klu_stand_down(osd);
    if (klu_r.fault) return;
    if (klu_r.made && (klu.plates || klu.pictest || klu.dials || klu.weapon) && !klu_r.pic_done) klu_pic_prep(klu_r.elem);      /* before the first frame that draws */
    InterlockedExchange(&klu_draw_on, show);
    klwd_show(show);
    if (show && klu.hide && klu.crew) klu_hide_tick(osd, 1);
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
    klu.crew = klu_inii("Crew", 1, 0, 1); klu.money = klu_inii("Money", 1, 0, 1); klu.round = klu_inii("Round", 1, 0, 1);
    klu.hide = klu_inii("HideStock", 1, 0, 1);
    klu.draw = klu_inii("Draw", 1, 1, 2);
    klu.shadow = klu_inii("Shadow", 1, 0, 1); if (klu.draw == 2) klu.shadow = 1;     /* the stock Render draws a pair */
    klu.tags = klu_inii("Tags", 1, 0, 1); klu.cashshort = klu_inii("CashShort", 1, 0, 1); klu.totalfont = klu_inii("TotalFont", 0, 0, 1);
    klu.draft = klu_inii("Draft", 0, 0, 1);              /* the whole draft: the defaults of Plates, Dials, Weapon, RoundOf (and klhud_popup.c's Popups, LootRing) become 1; a key that is set still wins */
    klu.dials = klu_inii("Dials", klu.draft, 0, 1);      /* the round watch + the escape dial (needs the level's extra pictures 113 / 114) */
    klu.weapon = klu_inii("Weapon", klu.draft, 0, 1); klwd_init();      /* the weapon dial (klhud_weapon.c; needs 113 / 114 too) */
    klu.lives = klu_inii("Lives", klu.draft, 0, 3);              /* 0 none, 1 three skull pictures (178) in your row - 'LIVES n' in the round line when the level has no such picture -, 2 TEST: skull glyphs after your name (the stock way), 3 'LIVES n' in the round line */
    klu.roundof = klu_inii("RoundOf", klu.draft, 0, 1);  /* 1 = 'ROUND n OF m' with the game's own m (10 in Arcade; whether a session ends there is not established) */
    klu.plates = klu_inii("Plates", klu.draft, 0, 1); klu.anchor = klu_inii("PicAnchor", 1, 0, 1); klu.left = klu_inii("LeftStyle", 0x11, 0, 255); klu.extraflags = klu_inii("ExtraFlags", 1, 0, 1); klu.pictest = klu_inii("PicTest", 0, 0, 1);
    klu.grid = klu_inii("Grid", 0, 0, 2); klu.probe = klu_inii("Probe", 0, 0, 1);
    klu.layer = klu_inii("Layer", 0xd, 3, 15);
    klu.rows = klu_inii("Rows", KLU_ROWS, 1, KLU_ROWS);
    klu.inset = klu_inif("Inset", "-1"); if (!(klu.inset > 0 && klu.inset < 0.25f)) klu.inset = -1;
    klu.crew_x = klu_inif("CrewX", klu.draft ? "33" : "-1"); klu.crew_y = klu_inif("CrewY", klu.draft ? "38" : "-1"); klu.crew_w = klu_inif("CrewW", "211");
    klu.money_x = klu_inif("MoneyX", klu.draft ? "1247" : "-1"); klu.money_y = klu_inif("MoneyY", "-1"); klu.money_w = klu_inif("MoneyW", "211"); klu.round_y = klu_inif("RoundY", "-1");
    klu.row = klu_inif("Row", klu.draft ? "30" : "24"); if (!(klu.row >= 8 && klu.row <= 64)) klu.row = klu.draft ? 30.0f : 24.0f;
    klu.yoff = klu.draft ? 34.0f : 30.0f; klu.blockup = klu.draft ? 5.0f : 4.0f; klu.blockh = klu.draft ? 28.0f : klu.row; klu.padx = klu.draft ? 8.0f : 6.0f;      /* M2 (re/hud_layout.md: names at +8 / y 72 + 30 i, cash at right - 8, block 219 x 28) */
    if (!(klu.crew_x <= 1280)) klu.crew_x = -1; if (!(klu.crew_y <= 720)) klu.crew_y = -1; if (!(klu.money_x <= 1280)) klu.money_x = -1;
    if (!(klu.money_y <= 720)) klu.money_y = -1; if (!(klu.round_y <= 720)) klu.round_y = -1;
    if (!(klu.crew_w >= 80 && klu.crew_w <= 640)) klu.crew_w = 211; if (!(klu.money_w >= 80 && klu.money_w <= 640)) klu.money_w = 211;
    klog("hud: on (Version 3: the draft's crew list, round line, money box + the parts: values, weapon dial, pop-ups; Draft=%d Dials=%d Weapon=%d Lives=%d RoundOf=%d); Stock=%d Log=%d Crew=%d Money=%d Round=%d HideStock=%d Draw=%d (1 own Draw with the 16:34 xform, 2 through the stock clock's Render) Shadow=%d Tags=%d CashShort=%d TotalFont=%d Plates=%d PicAnchor=%d PicTest=%d Grid=%d Probe=%d Layer=%d Rows=%d Inset=%.3f; Arcade only; VERSION 2 HAS NOT RUN IN THE GAME",
         klu.draft, klu.dials, klu.weapon, klu.lives, klu.roundof, klu.stock, klu.log, klu.crew, klu.money, klu.round, klu.hide, klu.draw, klu.shadow, klu.tags, klu.cashshort, klu.totalfont, klu.plates, klu.anchor, klu.pictest, klu.grid, klu.probe, klu.layer, klu.rows, klu.inset);
}

#endif /* KLHUD_C */
