/*
 * klhud_popup.c - the expansion HUD's CENTRE POP-UPS and LOOT RING (2026-10-11 night, track P; second form after its
 * review, re\hud_popup_review.md -> re\hud_popup.md 10). NOT RUN IN THE GAME.
 *   [HUD] Popups=1    the game's own announcements ('Looting has started ...', 'You jumped into the getaway car',
 *                     'X escaped', the reward lines ...) on a white painted bar (HUD picture 111, chalk) with BLACK
 *                     letters; the one message 'you are a traitor now' in ORANGE letters inside a painted box (118 orange
 *                     outline over a dark fill)
 *   [HUD] LootRing=1  while the human takes money: a ring of 20 dabs (113) that fills, a dark disc (114), a thin ring
 *                     (115) and a faded green dollar sign (116)
 * Part of KLHook, an add-on of klhud.c: to be included by klhook.c DIRECTLY AFTER klhud.c (it uses klhud.c's klu / klu_r /
 * klu_draw_on / klu_pic / klu_pic_prep / klu_same_code / klu_rdata_ptr and klbot.c's klb_read). Both keys default 0 and
 * need [HUD] Enable=1: this part draws only while klhud.c draws (klu_draw_on: an Arcade round's states, the level not
 * stock unless Stock=1, the clock element wrapped, no fault). SHIP rule kept: no code byte of kl2.exe changes; one heap
 * dword (the announcement element's vtable pointer -> a private copy), one float of that element swapped and put back
 * inside its own Render call, and calls of the text objects' own SetColour / SetAlpha.
 * The reading, the list of every message, the live checks: re\hud_popup.md.
 *
 * 1. THE ANNOUNCEMENT ELEMENT (EXE = read in kl2.exe build 0490)
 *    ZFAAnnouncementDisplay = [osd+0x10a8], vtable 0xbbdd34, 0x3c bytes, FA / Arcade only (re\hud.md 2.2).
 *      +0x14 / +0x18  its place: x = [0x154d92c] x scale + 1280 x 0.5 = 640, y = [0xcedc78] (-60) x scale + 720 x 0.75 = 480
 *                     (Update, slot 6 = 0x71d9c0)
 *      +0x28          the text (ZCHAROBJ; style 0x14, colour [0xbbe494] = ffcccccc, layer 0x19), +0x2c its shadow (colour
 *                     [0xbbe4a4] = 80000000, layer 0x18), +0x38 the stock background frame (an object made from the
 *                     level's 'BackgroundFrame' template, layer 0x17)              (Init, slot 4 = 0x7cbce0)
 *      +0x30          float: the game clock (frames / 1024, [[0xdd2640]+0x48]) at which the message ends; -1.0 = none
 *      +0x34 / +0x35  the follow camera element's saved hide byte / 'put back'
 *    ONE routine sets a message: 0x468430(elem, const char *text, float seconds) - thiscall, NOT virtual, 27 callers
 *    (re\hud_popup.md 2 lists them); every caller passes the finished localised string and [0xbcb330] = 5.0 s (3.0 for
 *    the 'no friendly fire' lines); "" clears. So the element holds no message id: WHICH message shows can only be told
 *    by its text.
 *    Render (slot 2 = 0x4895b0), whole: Arcade / FA only; while clock < (int)([+0x30] x 1024) it sizes the frame from the
 *    STRING (first line's characters x 15 px, x 20 when it has five or more 'W' / 'w', + 15, at least 300; lines x 30 +
 *    40 - bytes 0xcedc7c..7e, floats 0xcedc80 / 0xcedc84), draws it at (x, y - 25) with alpha 0xff; then - ALWAYS, also
 *    after the end - the text at (x, y) and the shadow at (+2, +2). The Tick (slot 5 = 0x4f1ea0) clears the text when
 *    the clock has passed [+0x30].
 *    => the frame's top is 25 px above the text's y and it is 70 px high for one line: the text's y is its TOP and
 *       the frame is centred on x (25 + ~22 + 23). That reading places our bar (GUESS until a picture shows it).
 *
 * 2. WHAT THIS PART DOES IN THAT RENDER CALL (a private copy of the element's vtable, slot 2 = klpu_render_ann)
 *    While a message shows and klhud.c draws: the text's colour is set to ink (traitor: orange) with the object's own
 *    SetColour (vtable +0x20c = 0x8a0a30), the shadow's alpha to 0 with its own SetAlpha (+0x218 = 0x639700; the traitor
 *    box keeps the shadow), our pictures are added with klu_pic at the stock frame's own layer 0x17 (the fill one
 *    below), and the stock Render is called with [+0x30] swapped to -1.0 for the length of that one call - it then
 *    skips its frame and draws text + shadow as ever (EXE 0x48961b .. 0x489632: jge 0x48978a). The float is put back
 *    by a compare-and-swap, so a message the game sets in that instant is not overwritten. PopupFrame=1 leaves the
 *    stock frame drawn under ours (no swap at all).
 *    When no message shows, or klhud.c does not draw: a colour of ours still on the text is put back to ffcccccc and
 *    the shadow's alpha to what it was, in the same slot. THE PUT-BACK DOES NOT DEPEND ON THIS PART'S LEVEL STATE
 *    (review M1): the game sets the colour once, in Init, so a colour of ours left on the text would stay for the level.
 *    The render slot remembers by itself (klpu_dirty, render thread only) which element carries a colour / alpha of
 *    ours and puts it back at that element's next Render call whatever klpu_r says - after a fault of klhud.c, a round
 *    that ends, a rules object that changes (klpu_forget). The slot is reached only through the private vtable, which
 *    klpu_wrap installs only on an object that showed 0xbbdd34.
 *    THE PLACE: the game's is (640, 480 = the text's top); the draft's is (640, 520). PopupY=520 exchanges the
 *    element's y float [+0x18] for the one stock Render call (it is read once, EXE 0x48960d, for frame and texts) and
 *    puts it back by compare-and-swap; the bar is drawn at the same y. Default -1 = the game's place, no exchange.
 *    The stock frame is scaled by float [0xcee050] (1.0 in the file; EXE 0x4896c7); our bar is NOT - the log says
 *    so when that float is not 1.
 *    THE BAR'S SIZE: a ZCHAROBJ keeps its laid-out half extents at [[obj+4]+0x40] (x) and +0x44 (y): EXE
 *    ZUseActionDisplay::Render 0x7571e6 .. 0x757204 lays its icon out beside the text with 2 x [+0x40] and sizes ITS
 *    frame as (2 x [+0x40] + 68, 2 x [+0x44] + 38) (0x7573c9 .. 0x757430). That the unit is the 1280 x 720 virtual pixel
 *    is a GUESS (the routine adds it to virtual places). PopupMeasure=0, or a value out of range, falls back to the
 *    stock way: characters of the longest line x KLPU_CHAR_W.
 *    THE TRAITOR MESSAGE: 0x67ee80 (called from ZGameRulesHeist slot 129, 0x8fb0d0, at 0x8fb15a) shows the .LOC string
 *    'AllLevels/Interface/Online/Announcements' / 'FA_Become_Traitor' unchanged (no placeholder), only on the machine
 *    of the player who turned (0x67ef61 cmp al, bl). The tick fetches that string once a level through the game's own
 *    lookup ([[[0xdd2640]+0xac]+0x94]->vt[0](section, key, 0), as 0x67efb2 .. 0x67efdc does) and the render slot
 *    compares. The other sign is the human's traitor flag: 'this message was first drawn between 0.3 s before and
 *    0.7 s after the flag rose' (slot 129 sets mark and message in one call; the tick samples the flag every 50 ms).
 *      PopupTraitor=1 (default)  the string decides; the flag only when the lookup gave no string. A message that
 *                                came with the flag's rise and is NOT the string is said in the log (review S1)
 *      PopupTraitor=2            the string OR the flag
 *      PopupTraitor=0            the flag alone; the lookup is never called
 *    Why 1 and not 2: the game shows the traitor message only while [rules+0xe84] is 0 (EXE 0x8fb13a .. 0x8fb153) and
 *    0x6706b0 counts that dword up at every crew kill by a human (0x670a34), so a LATER betrayal raises the flag with
 *    no message at all - under 2 whatever other message came in that second (a 'no friendly fire' line) got the box.
 *
 * 3. THE LOOT RING
 *    THE GAME HAS NO LOOT PROGRESS DISPLAY. Taking money from a money OBJECT is not a hold action: a crew record
 *    (0x7c bytes, [rules+0x348]) keeps +0x15 the loot state (0 none, 1 looting, 2 'the trigger must fire again', 3 see
 *    below), +0x18 the seconds left of the PART being taken, +0x1c the ZOnlineMoneyCtrl (vtable 0xbc874c; +0x34 the
 *    amount left, +0x40 one part, +0x44 the seconds a part) - EXE 0x8e8750, 0x727cb0; re\bots_loot.md 1. So there is
 *    nothing stock to hide.
 *    STATE 3 = THE HUMAN TAKES MONEY OFF A PERSON (review S4; EXE 0x727ce3 .. 0x727d9d, 0x727db8 .. 0x727e5f): only for
 *    the human's record, state 0 becomes 3 while bit 0x02 of [player+0xa54] is set and [player+0xa84] holds an object
 *    that carries money; every step takes at most 20,000 (0x4e20) and sets the step clock [rec+0x18] to [0xba312c] =
 *    0.5 s; state 0 again at 0x727f38. That one IS held. The ring shows the step clock there (a turn every 0.5 s),
 *    whatever RingMode says: what the person carries in all is behind a virtual call this part does not make.
 *    Ours: while the human's record is in state 1 / 2 with a money object, the ring's filled part =
 *      RingMode=1 (default)  what he has taken off THIS stack since he began / what lay there when he began
 *      RingMode=2            the part being taken (1 - [+0x18] / the largest value seen since it last rose): a turn every
 *                            0.15 .. 0.7 s, sampled every 50 ms - coarse
 *    drawn at the use-action prompt's place ([osd+0x110c], ZUseActionDisplay 0xbbe844: x = 640, y = 720 - inset - 75)
 *    + (KLPU_RING_DX, KLPU_RING_DY), or at RingX / RingY. It is drawn from the announcement element's Render call (the
 *    one element this part wraps), so it is not drawn while the game hides the FA set.
 *
 * KLHook.ini, section [HUD] (all need Enable=1)
 *   Popups=0          1 = the painted pop-ups (default = [HUD] Draft)
 *   LootRing=0        1 = the loot ring (default = [HUD] Draft)
 *   PopupFrame=0      1 = leave the stock background frame drawn under ours
 *   PopupMeasure=1    0 = size the bar from the string's length, never from the text object
 *   PopupPadX=48 PopupPadY=11 PopupDY=3 the bar = the text + 48 wide, 27 + 11 = 38 high (quiet round 2026-10-11; the draft's .toast was 61.4 / 33.6 + 14.1 = 47.7 with 22.4 px letters; now the BIG font, cap 15); DY moves
 *                     the BAR ALONE (to seat it on the letters)
 *   PopupY=523        the BAR'S MIDDLE in virtual pixels (the draft's .toast: bottom 547, middle 523); the letters' capitals are centred on it
 *                     by the baked metric (see the 1:1 block). -1 = the game's own text top (480) + half a capital
 *   PopupTraitor=1    how the traitor message is told (section 2): 1 its string, 2 string or flag, 0 flag alone
 *   PopupLayer=23     the bar's layer byte (0x17 = the stock frame's; the text is 0x19, its shadow 0x18)
 *   PopupTest=0       TEST: 1 = every 8 s the tick shows a sample message through the game's own 0x468430, in turn a
 *                     plain one and the traitor one, and the ring sweeps round by itself
 *   RingMode=1 RingX=-1 RingY=-1            -1 = from the use-action element
 */
#ifndef KLHUD_POPUP_C
#define KLHUD_POPUP_C

#define KLPU_ANN_VT      0x00bbdd34u          /* ZFAAnnouncementDisplay */
#define KLPU_ANN_RENDER  0x004895b0u          /* its slot 2 */
#define KLPU_ANNOUNCE    0x00468430u          /* thiscall (elem, const char *, float seconds), ret 8 */
#define KLPU_SETALPHA    0x00639700u          /* ZCHAROBJ vtable +0x218: thiscall (byte), ret 4 */
#define KLPU_SETCOLOUR   0x008a0a30u          /* ZCHAROBJ vtable +0x20c */
#define KLPU_USE_VT      0x00bbe844u          /* ZUseActionDisplay */
#define KLPU_MONEY_VT    0x00bc874cu          /* ZOnlineMoneyCtrl */
#define KLPU_O_ANN       0x10a8               /* osd: ZFAAnnouncementDisplay * */
#define KLPU_O_USE       0x110c               /* osd: ZUseActionDisplay * */
#define KLPU_E_END       0x30                 /* the announcement: float, the clock / 1024 at which it ends (section 1) */
#define KLPU_T_STRING    0xa4                 /* ZCHAROBJ: -> string object, the characters at +0xc (0x489649 .. 0x48965a) */
#define KLPU_T_RGB       0x14                 /* ZCHAROBJ: the colour dword */
#define KLPU_T_STYLE     0x84                 /* ZCHAROBJ: the style byte SetStyle keeps (re\hud.md 191) */
#define KLPU_T_ALPHA     0x86                 /* ZCHAROBJ: the alpha byte SetAlpha keeps */
#define KLPU_T_GEOM      0x04                 /* ZCHAROBJ: -> the object whose +0x40 / +0x44 are the text's half extents */
#define KLPU_R_LOOT      0x15                 /* crew record: loot state byte */
#define KLPU_R_PART      0x18                 /* crew record: float, seconds left of the part */
#define KLPU_R_OBJ       0x1c                 /* crew record: the money object */
#define KLPU_M_LEFT      0x34                 /* ZOnlineMoneyCtrl: int, the amount left */
#define KLPU_NSLOT       12                   /* the vtable's dwords this part copies (11 slots of IDisplayInterface + one) */
#define KLPU_GONE        ((LONG)0xbf800000)   /* -1.0f: the game's own 'no message' ([0xb3e980]) */

/* every place and size is a named number: NOTHING HERE HAS BEEN SEEN IN THE GAME (virtual 1280 x 720 pixels) */
#define KLPU_STOCK_RGB   0x00ccccccu          /* the announcement text's own colour, [0xbbe494] = ffcccccc */
#define KLPU_C_BOXFILL   0xe60c0c0du          /* the traitor box's dark fill */
#define KLPU_CHAR_W      9.5f                 /* the estimate: pixels a character (the stock frame takes 15, 20 for wide strings) */
#define KLPU_LINE_H      18.0f                /* the estimate: a line's height; KLPU_LINE_STEP from line to line (the stock frame: 30) */
#define KLPU_LINE_STEP   22.0f                /* the baked H1's line height (review S8; was 24) */
#define KLPU_BOX_GROW    5.0f                 /* the traitor box's outline stands this far outside its fill */
#define KLPU_OUTLINE     2.0f                 /* without picture 118: the outline's thickness */
#define KLPU_RING_DX     0.0f                 /* the ring's middle against the use-action prompt's place */
#define KLPU_RING_DY     (-58.0f)
#define KLPU_RING_X0     640.0f               /* without that element */
#define KLPU_RING_Y0     545.0f
#define KLPU_RING_N      32                   /* re\hud_layout.md: 20 dabs on r = 26, disc and thin ring 40, dollar 34 */
#define KLPU_RING_R      22.0f               /* quiet round: 26 -> 22 (disc 40 -> 34, dollar 34 -> 29, dabs 9 x 8 -> 8 x 7) */
#define KLPU_DAB_W       8.0f
#define KLPU_DAB_H       7.0f
#define KLPU_DISC        34.0f
#define KLPU_DOLLAR      29.0f
#define KLPU_C_DISC      0xff0f100fu
#define KLPU_C_THIN      0xff8d8982u
#define KLPU_C_DOLLAR    0xb063a65bu          /* green hi, faded */
#define KLPU_RING_LINGER 250                  /* ms the ring stays after the last looting sample */
#define KLPU_TRAITOR_EARLY 300u               /* the flag sign: the message was first drawn at most this many ms BEFORE the tick saw the flag rise ... */
#define KLPU_TRAITOR_LATE  700u               /* ... or this many after (section 2) */
#define KLPU_SCALE       0x00cee050u          /* float: the stock frame's scale (EXE 0x4896c7) */
#define KLPU_LOOT_PERSON 3                    /* crew record +0x15: the human takes money off a person (section 3) */
#define KLPU_MSG         128
/* 2026-10-11 1:1 round (owner: texts in the white boxes sit off the middle; draft = hud_mockup.html .toast). The review
   (re/hud_1to1_review.md MUST 1 / 2) refuted the style-0x44 way: the 3 px offset was measured on the STOCK font, and the new bake has
   other metrics. Now the stock top-aligned style stays and the letters are placed by the baked metric, as the crew rows are:
   kl_hud.py bakes header[9] = -cap, so the capitals of a text drawn at y span y .. y + cap (cap = [HUD] Cap0, the NAME font's).
   The draft's size 22.4 px has no slot of its own (H1 serves the total), so while a bar shows the two texts take the NAME font
   (H2, SetFont +0x23c, the original put back like the colour) and their top is bar centre - cap / 2.
   The bar's height is the draft's constant, not a measure: .toast = line-height 1.5 x 22.4 px = 33.6 + 2 x .55 cqw (14.1). */
#define KLPU_T_FONT      0xac                 /* ZCHAROBJ: the font object SetFont keeps (re\hud.md 3.1) */
#define KLPU_BAR_LINE    27.0f                /* the draft's one line of the bar: line-height 1.5 x font 22.4 px */

static struct { int popups, ring, frame, measure, layer, test, ringmode, traitor; float padx, pady, dy, y, ringx, ringy, liftgap; int lift; } klpu;

static struct {
    DWORD osd, ann;                           /* the level this part holds, its wrapped announcement element */
    int refused, loc_done, told_pics;
    DWORD loot_obj; long loot_start; float part_max, part_last; DWORD loot_seen;      /* loot_obj 1 = a person (state 3) */
    int was_traitor; DWORD test_at; int test_n;
} klpu_r;
static volatile LONG klpu_traitor_ok;         /* klpu_traitor[] holds the level's traitor string */
static char klpu_traitor[KLPU_MSG];
static volatile LONG klpu_traitor_at;         /* GetTickCount | 1 when the human's traitor flag rose, 0 = not / long ago */
static volatile LONG klpu_ring_on, klpu_ring_frac, klpu_ring_cx, klpu_ring_cy;      /* the three floats as bits */
static volatile LONG klpu_n_call, klpu_n_bar, klpu_n_box, klpu_n_ring, klpu_n_nopic;
static volatile LONG klpu_msg_new;            /* the render slot has filled klpu_msg; the tick logs it and clears this */
static struct { char text[KLPU_MSG]; float mw, mh, ew, eh, x, y, bw, bh, scale; int measured, traitor, byflag, lines, known, withflag; } klpu_msg;
static DWORD klpu_evt[KLPU_NSLOT + 1];        /* [0] RTTI locator, [1..] the slots */
static int klpu_evt_ready;
/* render thread only - NOT part of klpu_r and never cleared by klpu_forget: the put-back of section 2 lives on them */
static LONG klpu_last_end; static DWORD klpu_sh_obj; static BYTE klpu_sh_alpha;
static DWORD klpu_dirty;                      /* the element whose text / shadow may carry a colour / alpha of ours */
static LONG klpu_seen_end; static DWORD klpu_seen_at;        /* the message that shows (its end time's bits), GetTickCount when it was first drawn */

typedef void (__fastcall *klpu_set1_t)(void *, void *, DWORD);

static int klpu_str(DWORD p, char *out, int cap)
{   /* the characters at p, at most cap-1, any byte but NUL taken (a message may hold line feeds); never faults */
    int n = 0, i;
    out[0] = 0;
    while (p && n < cap - 1) {
        int k = (int)(0x1000 - ((p + n) & 0xfff)); if (k > cap - 1 - n) k = cap - 1 - n;
        if (!klh_rd(p + n, out + n, (SIZE_T)k)) break;
        for (i = 0; i < k; i++) if (!out[n + i]) return n + i;
        n += k;
    }
    out[n] = 0;
    return n;
}

static float klpu_f(LONG bits) { float f; memcpy(&f, &bits, 4); return f; }
static LONG klpu_bits(float f) { LONG b; memcpy(&b, &f, 4); return b; }

/* ---------------------------------------------------------------- the render slot (whichever thread renders) */

static void klpu_shadow(DWORD shadow, int show)
{   /* the shadow's alpha: 0 under dark letters on the chalk bar, what it was before otherwise */
    BYTE a;
    if (!shadow) return;
    a = *(const BYTE *)(DWORD_PTR)(shadow + KLPU_T_ALPHA);
    if (!show && a) {
        klpu_sh_obj = shadow; klpu_sh_alpha = a;
        ((klpu_set1_t)(DWORD_PTR)KLH_VA(KLPU_SETALPHA))((void *)(DWORD_PTR)shadow, 0, 0);
    } else if (show && klpu_sh_obj == shadow) {
        if (!a && klpu_sh_alpha) ((klpu_set1_t)(DWORD_PTR)KLH_VA(KLPU_SETALPHA))((void *)(DWORD_PTR)shadow, 0, (DWORD)klpu_sh_alpha);
        klpu_sh_obj = 0; klpu_sh_alpha = 0;                          /* put back: nothing of this object is kept (review N4) */
    }
}

static void klpu_colour(DWORD text, DWORD rgb)
{
    if ((*(const DWORD *)(DWORD_PTR)(text + KLPU_T_RGB) & 0xffffff) != (rgb & 0xffffff))
        ((klpu_set1_t)(DWORD_PTR)KLH_VA(KLPU_SETCOLOUR))((void *)(DWORD_PTR)text, 0, rgb);
}

static float klpu_top;                         /* render thread only: the text top the last bar asked for */
static DWORD klpu_font_obj[2], klpu_font_orig[2], klpu_font_set[2];
static void klpu_font(DWORD obj, int slot, int on)
{   /* on = 1: the text takes the NAME font (the object's own SetFont); 0: back to the font it had, if it still holds ours */
    DWORD cur, want;
    if (!obj) return;
    cur = klh_rd32(obj + KLPU_T_FONT);
    if (on) {
        want = klu.fontset ? klu_r.fonts[KLU_FNT_BIG] : 0;      /* quiet round: the BIG role (H1, cap 15) - the names' font is cap 11 now */
        if (!want || !cur || cur == want) return;
        klpu_font_obj[slot] = obj; klpu_font_orig[slot] = cur; klpu_font_set[slot] = want;
        klu_set(obj, KLU_VT_FONT, want);
    } else if (klpu_font_obj[slot] == obj) {
        if (cur == klpu_font_set[slot] && klpu_font_orig[slot]) klu_set(obj, KLU_VT_FONT, klpu_font_orig[slot]);
        klpu_font_obj[slot] = 0;
    }
}

static void klpu_restore(DWORD text, DWORD shadow)
{   /* section 2: nothing of ours is left on the stock objects when we do not draw */
    DWORD rgb = *(const DWORD *)(DWORD_PTR)(text + KLPU_T_RGB) & 0xffffff;
    if (rgb == (KLU_C_INK & 0xffffff) || rgb == (KLU_C_ORANGE & 0xffffff)) klpu_colour(text, KLPU_STOCK_RGB);
    klpu_shadow(shadow, 1);
    klpu_font(text, 0, 0); klpu_font(shadow, 1, 0);
    klpu_dirty = 0;
}

static void klpu_restore_el(DWORD e)
{   /* review M1: the put-back for an element this part no longer holds (klpu_r.ann is 0 or another): its two texts,
       vtable-checked as klpu_popup does; e is the 'this' of the running Render call */
    DWORD text = *(const DWORD *)(DWORD_PTR)(e + 0x28), shadow = *(const DWORD *)(DWORD_PTR)(e + 0x2c);
    klpu_dirty = 0;
    if (!text || klh_rd32(text) != KLU_TEXT_VT) return;
    if (shadow && klh_rd32(shadow) != KLU_TEXT_VT) shadow = 0;
    klpu_restore(text, shadow);
}

static void *klpu_clock(void)
{   /* the clock element klu_pic borrows its picture desc and transform from: klhud.c's, still wrapped by it */
    DWORD el = klu_r.elem;
    return el && klu_r.pic_done && klh_rd32(el) == (DWORD)(DWORD_PTR)&klu_evt[1] ? (void *)(DWORD_PTR)el : 0;
}

/* -> 1 = our bar / box was drawn for the message that shows now (the caller then keeps the stock frame away) */
static int klpu_popup(DWORD e, void *ctx)
{
    DWORD text = *(const DWORD *)(DWORD_PTR)(e + 0x28), shadow = *(const DWORD *)(DWORD_PTR)(e + 0x2c), sys, geom;
    LONG endbits = *(const LONG *)(DWORD_PTR)(e + KLPU_E_END), frame = 0; float end = klpu_f(endbits), ext[2] = { 0, 0 };
    float x, y, w, h, ew, eh, bw, bh, x0, y0, cap; char s[KLPU_MSG]; const char *p; void *clock; DWORD str;
    int showing, n, lines = 1, cur = 0, longest = 0, traitor = 0, byflag = 0, withflag = 0, same, measured = 0, bar, drew = 0;
    if (!(end > 0) && klpu_dirty != e) return 0;                     /* no message and nothing of ours on it: no guarded read at all (review N2) */
    if (!text || klh_rd32(text) != KLU_TEXT_VT) return 0;
    if (shadow && klh_rd32(shadow) != KLU_TEXT_VT) shadow = 0;
    showing = end > 0 && (sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) != 0 && klh_rd(sys + 0x48, &frame, 4) && frame < (LONG)(end * 1024.0f);
    n = showing && (str = klh_rd32(text + KLPU_T_STRING)) != 0 ? klpu_str(str + 0xc, s, sizeof s) : 0;
    clock = klu_draw_on ? klpu_clock() : 0;
    bar = klu_r.handle[111] ? 111 : klu_r.handle[181] ? 181 : -1;
    if (!showing || !n || !clock || bar < 0) {
        if (showing && n && klu_draw_on && bar < 0) InterlockedIncrement(&klpu_n_nopic);
        klpu_restore(text, shadow);
        return 0;
    }
    for (p = s; *p; p++) { if (*p == '\n') { lines++; if (cur > longest) longest = cur; cur = 0; } else cur++; }
    if (cur > longest) longest = cur;
    /* which message (section 2) */
    if (endbits != klpu_seen_end) { klpu_seen_end = endbits; klpu_seen_at = GetTickCount(); }
    same = klpu_traitor_ok && !strcmp(s, klpu_traitor);
    { LONG at = klpu_traitor_at; withflag = at && (DWORD)(klpu_seen_at - (DWORD)at + KLPU_TRAITOR_EARLY) < KLPU_TRAITOR_EARLY + KLPU_TRAITOR_LATE; }
    if (same) traitor = 1;
    else if (withflag && (klpu.traitor != 1 || !klpu_traitor_ok)) traitor = byflag = 1;
    if (klu.fontset) { klpu_dirty = e; klpu_font(text, 0, 1); klpu_font(shadow, 1, 1); }      /* the NAME font first: the measure below is of the text in it */
    /* how large (section 2): the object's own half extents, else from the string as the stock frame is sized */
    ew = longest * KLPU_CHAR_W; eh = KLPU_LINE_H + KLPU_LINE_STEP * (lines - 1);
    geom = *(const DWORD *)(DWORD_PTR)(text + KLPU_T_GEOM);
    if (klpu.measure && geom && klh_rd(geom + 0x40, ext, 8) && ext[0] > 2.0f && ext[0] < 600.0f && ext[1] > 2.0f && ext[1] < 120.0f) measured = 1;
    w = measured ? 2.0f * ext[0] : ew; h = measured ? 2.0f * ext[1] : eh;
    cap = klu.fontset ? klu_cap_of(KLU_FNT_BIG) : 15.0f;
    x = *(const float *)(DWORD_PTR)(e + 0x14);
    y = klpu.y >= 0 ? klpu.y : *(const float *)(DWORD_PTR)(e + 0x18) + cap * 0.5f;     /* the bar's middle: PopupY, else the game's own text top + half a capital */
    bw = w + klpu.padx; bh = KLPU_BAR_LINE + klpu.pady + KLPU_LINE_STEP * (float)(lines - 1);      /* the draft: text + 61.4 wide, 33.6 + 14.1 = 47.7 high */
    x0 = x - bw * 0.5f;                                              /* the low style nibble 4 centres the text on x */
    y0 = y + KLPU_LINE_STEP * (float)(lines - 1) * 0.5f - bh * 0.5f + klpu.dy;       /* a block of several lines: the bar's middle follows the block's */
    klpu_top = (float)floor(y - cap * 0.5f + 0.5f);                   /* the capitals span klpu_top .. + cap (header[9] = -cap): their middle is the bar's middle (+ 0.5 px at most) */
    if (klpu.lift && klpu_ring_on) {                                  /* v22 (audit P1): the loot ring sits under the bar's lower edge (R1p 111 s): lift bar + letters clear of it */
        float rt = klpu_f(klpu_ring_cy) - KLPU_RING_R - KLPU_DAB_H - klpu.liftgap, lift = y0 + bh - rt;
        if (lift > 0 && lift < 90.0f) { lift = (float)floor(lift + 0.5f); y -= lift; y0 -= lift; klpu_top -= lift; }
    }
    if (traitor) {
        klpu_dirty = e; klpu_colour(text, KLU_C_ORANGE); klpu_shadow(shadow, 1); klpu_font(text, 0, 1); klpu_font(shadow, 1, 1);
        if (klu_r.handle[181]) drew |= klu_pic(clock, ctx, KLU_NPIC, 181, x0, y0, bw, bh, KLPU_C_BOXFILL, klpu.layer - 1);
        if (klu_r.handle[118]) drew |= klu_pic(clock, ctx, KLU_NPIC, 118, x0 - KLPU_BOX_GROW, y0 - KLPU_BOX_GROW, bw + 2 * KLPU_BOX_GROW, bh + 2 * KLPU_BOX_GROW, KLU_C_ORANGE, klpu.layer);
        else if (klu_r.handle[181]) {                                /* no painted box in this level: four plain bars */
            klu_pic(clock, ctx, KLU_NPIC, 181, x0, y0, bw, KLPU_OUTLINE, KLU_C_ORANGE, klpu.layer);
            klu_pic(clock, ctx, KLU_NPIC, 181, x0, y0 + bh - KLPU_OUTLINE, bw, KLPU_OUTLINE, KLU_C_ORANGE, klpu.layer);
            klu_pic(clock, ctx, KLU_NPIC, 181, x0, y0, KLPU_OUTLINE, bh, KLU_C_ORANGE, klpu.layer);
            klu_pic(clock, ctx, KLU_NPIC, 181, x0 + bw - KLPU_OUTLINE, y0, KLPU_OUTLINE, bh, KLU_C_ORANGE, klpu.layer);
        }
        if (drew) InterlockedIncrement(&klpu_n_box);
    } else {
        klpu_dirty = e; klpu_colour(text, KLU_C_INK); klpu_shadow(shadow, 0); klpu_font(text, 0, 1); klpu_font(shadow, 1, 1);
        drew = klu_pic(clock, ctx, KLU_NPIC, bar, x0, y0, bw, bh, KLU_C_CHALK, klpu.layer);
        if (drew) InterlockedIncrement(&klpu_n_bar);
    }
    if (!drew) { klpu_restore(text, shadow); return 0; }             /* no picture went out: the stock look, whole */
    if (endbits != klpu_last_end && !klpu_msg_new) {                 /* a new message: one line for the log (written by the tick) */
        klpu_last_end = endbits;
        memcpy(klpu_msg.text, s, sizeof klpu_msg.text);
        klpu_msg.mw = 2.0f * ext[0]; klpu_msg.mh = 2.0f * ext[1]; klpu_msg.ew = ew; klpu_msg.eh = eh; klpu_msg.x = x; klpu_msg.y = y; klpu_msg.bw = bw; klpu_msg.bh = bh;
        klpu_msg.measured = measured; klpu_msg.traitor = traitor; klpu_msg.byflag = byflag; klpu_msg.lines = lines;
        klpu_msg.known = klpu_traitor_ok != 0; klpu_msg.withflag = withflag; klpu_msg.scale = *(const float *)(DWORD_PTR)KLH_VA(KLPU_SCALE);
        InterlockedExchange(&klpu_msg_new, 1);
    }
    return 1;
}

static void klpu_ring_draw(void *ctx)
{   /* section 3; re\hud_layout.md 'loot ring' */
    void *clock; float cx, cy, frac; int k, n, drew = 0;
    if (!klpu_ring_on || !klu_draw_on || !klu_r.handle[113] || !(clock = klpu_clock())) return;
    cx = klpu_f(klpu_ring_cx); cy = klpu_f(klpu_ring_cy); frac = klpu_f(klpu_ring_frac);
    if (!(frac >= 0)) frac = 0; if (frac > 1.0f) frac = 1.0f;
    if (klu.wstyle && klu_r.handle[KLU_DAB_PIC]) { float d = KLPU_DISC / KLU_DAB_INK;      /* 2026-10-13: 114 of the watch bake is the watch face - the loot ring's disc is a plain dab there */
        drew |= klu_pic(clock, ctx, KLU_NPIC, KLU_DAB_PIC, cx - d * 0.5f, cy - d * 0.5f, d, d, KLPU_C_DISC, klu.layer - 2); }
    else if (klu_r.handle[114]) drew |= klu_pic(clock, ctx, KLU_NPIC, 114, cx - KLPU_DISC * 0.5f, cy - KLPU_DISC * 0.5f, KLPU_DISC, KLPU_DISC, KLPU_C_DISC, klu.layer - 2);
    klu_track(clock, ctx, cx, cy, KLPU_DISC * 0.5f, KLPU_C_THIN, klu.layer - 1);                 /* 115 = the thin ring at the disc's rim (re-baked 2026-10-12 at 0.40 of its square) */
    if (klu_r.handle[116]) klu_pic(clock, ctx, KLU_NPIC, 116, cx - KLPU_DOLLAR * 0.5f, cy - KLPU_DOLLAR * 0.5f, KLPU_DOLLAR, KLPU_DOLLAR, KLPU_C_DOLLAR, klu.layer - 1);
    if (frac < 0.012f) frac = 0.012f;                                 /* a stub stands as soon as he loots */
    (void)n; (void)k;
    klu_arc(clock, ctx, cx, cy, KLPU_RING_R, 0, 0.0f, frac, KLU_C_CHALK, klu.layer);     /* 2026-10-12: ONE painted stroke (klhud.c klu_arc, family A), the FILLED part from the top clockwise */
    drew = 1;
    if (drew) InterlockedIncrement(&klpu_n_ring);
}

/* slot 2 (Render(ctx, cam), thiscall ret 8) of the private vtable of the announcement element */
static char __fastcall klpu_render_ann(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el; LONG old = 0, oldy = 0, newy = 0; int swapped = 0, moved = 0, mine; char r; (void)edx;
    InterlockedIncrement(&klpu_n_call);
    mine = ctx && e == klpu_r.ann && *(const DWORD *)ctx == KLU_CTX_VT;      /* DRAWING needs this part's level state ... */
    if (mine && klpu.popups) {
        if (klpu_popup(e, ctx)) {
            if (!klpu.frame) {
                /* section 2: the stock Render sees 'no message' for this one call and leaves its frame out; text and
                   shadow are drawn whatever the float says */
                old = InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + KLPU_E_END), KLPU_GONE); swapped = 1;
            }
            newy = klpu_bits(klpu_top);                               /* the letters go where the bar's middle wants them */
            oldy = InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + 0x18), newy); moved = 1;
        }
    } else if (klpu_dirty == e) klpu_restore_el(e);                  /* ... THE PUT-BACK DOES NOT (review M1; section 2) */
    r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLPU_ANN_RENDER))(el, 0, ctx, cam);
    if (swapped) InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLPU_E_END), old, KLPU_GONE);    /* only if nobody set a message meanwhile */
    if (moved) InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + 0x18), oldy, newy);                 /* only if Update has not written it meanwhile */
    if (klpu.ring && mine) klpu_ring_draw(ctx);
    return r;
}

/* ---------------------------------------------------------------- main thread */

static int klpu_wrap(DWORD osd)
{   /* -> 1 while the announcement element's first dword is ours (installed here when it shows the stock one) */
    static const BYTE render_code[10] = { 0x81, 0xec, 0xcc, 0x00, 0x00, 0x00, 0xa1, 0xe0, 0x9e, 0xd4 };       /* 0x4895b0 sub esp,0xcc ; mov eax,[0xd49ee0] */
    static const BYTE say_code[8]     = { 0x56, 0x57, 0x8b, 0x7c, 0x24, 0x0c, 0x8b, 0xc7 };                   /* 0x468430 */
    static const BYTE alpha_code[8]   = { 0x83, 0xec, 0x0c, 0x53, 0x8a, 0x5c, 0x24, 0x14 };                   /* 0x639700 */
    static const BYTE colour_code[8]  = { 0x51, 0x8b, 0x44, 0x24, 0x08, 0x56, 0x8b, 0xf1 };                   /* 0x8a0a30 */
    DWORD el, cur = 0, vt;
    if (!(el = klh_rd32(osd + KLPU_O_ANN)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klpu_evt_ready) {
        if (!klu_same_code(KLPU_ANN_RENDER, render_code, sizeof render_code) || !klu_same_code(KLPU_ANNOUNCE, say_code, sizeof say_code) ||
            !klu_same_code(KLPU_SETALPHA, alpha_code, sizeof alpha_code) || !klu_same_code(KLPU_SETCOLOUR, colour_code, sizeof colour_code) ||
            klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + 0x218)) != KLPU_SETALPHA || klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + KLU_VT_COLOUR)) != KLPU_SETCOLOUR ||
            !klh_rd((DWORD_PTR)KLH_VA(KLPU_ANN_VT - 4), klpu_evt, sizeof klpu_evt) || klpu_evt[1 + 2] != KLPU_ANN_RENDER) {
            klog("hud: popup: a routine of the announcement path is not the one this build knows (0x4895b0 / 0x468430 / 0x639700 / 0x8a0a30, ZFAAnnouncementDisplay slot 2 = %08lx): pop-ups and the ring stay stock", klpu_evt[1 + 2]);
            return 0;
        }
        klpu_evt[1 + 2] = (DWORD)(DWORD_PTR)klpu_render_ann;
        klpu_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klpu_evt[1];
    if (cur == vt) { klpu_r.ann = el; return 1; }
    if (cur != KLPU_ANN_VT) { klog("hud: popup: the element at osd+0x10a8 = %08lx has vtable %08lx, not ZFAAnnouncementDisplay's: pop-ups and the ring stay stock", el, cur); return 0; }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the announcement element's vtable (private copy, slot 2 wrapped)")) return 0;
    klpu_r.ann = el;
    if (klu.log) klog("hud: popup: element %08lx (the announcements) now renders through the private vtable (slot 2 -> klpu_render_ann, then the stock 0x4895b0); Popups=%d LootRing=%d", el, klpu.popups, klpu.ring);
    return 1;
}

static void klpu_loc(void)
{   /* section 2: the level's own text of the traitor message, through the game's lookup (once a level, game thread) */
    DWORD sys, db, loc, vt, fn; char sec[9], s[KLPU_MSG]; const char *p;
    klpu_r.loc_done = 1;
    InterlockedExchange(&klpu_traitor_ok, 0);
    if (!klpu.traitor) return;                                       /* PopupTraitor=0: the flag alone, the game's lookup is not called */
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(db = klh_rd32(sys + 0xac)) || !(loc = klh_rd32(db + 0x94)) || !(vt = klh_rd32(loc)) ||
        !klu_rdata_ptr(vt) || !(fn = klh_rd32(vt)) || klh_kind((const void *)(DWORD_PTR)KLH_VA(fn), 4, sec) != 'x') {
        klog("hud: popup: the text lookup [[[0xdd2640]+0xac]+0x94] is not there: the traitor message is told by the traitor flag's rise instead"); return;
    }
    p = ((const char *(__fastcall *)(void *, void *, const char *, const char *, DWORD))(DWORD_PTR)fn)((void *)(DWORD_PTR)loc, 0, "AllLevels/Interface/Online/Announcements", "FA_Become_Traitor", 0);
    if (!p || klpu_str((DWORD)(DWORD_PTR)p, s, sizeof s) < 2) { klog("hud: popup: this level's text file gave nothing for Announcements / FA_Become_Traitor: the traitor message is told by the traitor flag's rise instead"); return; }
    memcpy(klpu_traitor, s, sizeof klpu_traitor);
    InterlockedExchange(&klpu_traitor_ok, 1);
    if (klu.log) klog("hud: popup: the traitor message of this level is '%s' (Announcements / FA_Become_Traitor): that one is drawn orange in a box", klpu_traitor);
}

static void klpu_forget(void)
{   /* the level went, or klhud.c dropped its level state (a fault: for good; 'session state below 0x16' / 'rules object
       changed': until it is taken up again). The element is not touched from here and stays wrapped: its render slot
       puts the stock colour and the shadow back by itself at its next call, from statics this routine does NOT clear
       (klpu_dirty, klpu_sh_obj / klpu_sh_alpha: review M1, N4); a freed level takes its objects with it */
    InterlockedExchange(&klpu_ring_on, 0);
    InterlockedExchange(&klpu_traitor_ok, 0);
    InterlockedExchange(&klpu_traitor_at, 0);
    memset(&klpu_r, 0, sizeof klpu_r);
}

static void klpu_ring_tick(DWORD osd, const struct klb_snap *s, int have, DWORD now)
{
    DWORD at, obj = 0, uel; BYTE st = 0; long left = 0; float part = 0, frac = 0, pos[2] = { 0, 0 }, cx, cy; int looting = 0;
    if (klpu.test) {                                                 /* TEST: the ring at 60 % in the third 4 s of every 12 (klpu_test_tick shows the two messages before it) */
        if ((now % 12000) >= 8000) { frac = 0.6f; looting = 1; }
    } else if (have && s->state == 0x19 && s->human >= 0 && (at = s->r[s->human].at) != 0 && klh_rd(at + KLPU_R_LOOT, &st, 1) && (st == 1 || st == 2) &&
               klh_rd(at + KLPU_R_OBJ, &obj, 4) && obj && klh_rd32(obj) == KLPU_MONEY_VT && klh_rd(obj + KLPU_M_LEFT, &left, 4) && klh_rd(at + KLPU_R_PART, &part, 4)) {
        looting = 1;
        if (obj != klpu_r.loot_obj || left > klpu_r.loot_start) {    /* another stack, or this one was filled again */
            klpu_r.loot_obj = obj; klpu_r.loot_start = left; klpu_r.part_max = part; klpu_r.part_last = part;
            if (klu.log >= 2) klog("hud: ring: you loot money object %08lx: %ld left, %.2f s a part", obj, left, part);
        }
        if (part > klpu_r.part_last + 0.01f || part > klpu_r.part_max) klpu_r.part_max = part;      /* the part's clock was set again */
        klpu_r.part_last = part;
        if (klpu.ringmode == 2) frac = klpu_r.part_max > 0.01f ? 1.0f - part / klpu_r.part_max : 0;
        else frac = klpu_r.loot_start > 0 ? (float)(klpu_r.loot_start - left) / (float)klpu_r.loot_start : 0;
    } else if (have && s->state == 0x19 && s->human >= 0 && (at = s->r[s->human].at) != 0 && klh_rd(at + KLPU_R_LOOT, &st, 1) && st == KLPU_LOOT_PERSON &&
               klh_rd(at + KLPU_R_PART, &part, 4)) {
        /* section 3, state 3: money off a person - the step clock, whatever RingMode says */
        looting = 1;
        if (klpu_r.loot_obj != 1) {
            klpu_r.loot_obj = 1; klpu_r.loot_start = 0; klpu_r.part_max = part > 0.5f ? part : 0.5f; klpu_r.part_last = part;
            if (klu.log >= 2) klog("hud: ring: you take money off a person (loot state 3): the step clock %.2f s", part);
        }
        if (part > klpu_r.part_max) klpu_r.part_max = part;
        klpu_r.part_last = part;
        frac = part > 0 ? 1.0f - part / klpu_r.part_max : 1.0f;
    }
    if (looting) klpu_r.loot_seen = now | 1;
    else if (klpu_r.loot_seen && now - klpu_r.loot_seen >= KLPU_RING_LINGER) { klpu_r.loot_seen = 0; klpu_r.loot_obj = 0; klpu_r.loot_start = 0; }
    if (!klpu_r.loot_seen) { InterlockedExchange(&klpu_ring_on, 0); return; }
    /* where: the use-action prompt's place, read from its element (Update 0x51f4a0 writes it every frame) */
    cx = KLPU_RING_X0; cy = KLPU_RING_Y0;
    if ((uel = klh_rd32(osd + KLPU_O_USE)) != 0 && klh_rd32(uel) == KLPU_USE_VT && klh_rd(uel + 0x14, pos, 8) && pos[0] > 0 && pos[0] < 1280.0f && pos[1] > 0 && pos[1] < 720.0f) {
        cx = pos[0] + KLPU_RING_DX; cy = pos[1] + KLPU_RING_DY;
    }
    if (klpu.ringx >= 0) cx = klpu.ringx;
    if (klpu.ringy >= 0) cy = klpu.ringy;
    if (looting) InterlockedExchange(&klpu_ring_frac, klpu_bits(frac));      /* while it lingers the last value stands */
    InterlockedExchange(&klpu_ring_cx, klpu_bits(cx)); InterlockedExchange(&klpu_ring_cy, klpu_bits(cy));
    InterlockedExchange(&klpu_ring_on, 1);
}

static void klpu_test_tick(DWORD now)
{   /* TEST [HUD] PopupTest=1, a round of 12 s on the wall clock so ONE idle run shows all three looks in pictures taken every
       2 s: 0-4 s a plain message (chalk bar, ink letters), 4-8 s the traitor message (orange letters, painted box), 8-12 s the
       loot ring at 60 % (klpu_ring_tick). The messages go through the game's own 0x468430 (game thread, between frames) and last 3.8 s. */
    const char *msg; DWORD ph = (now % 12000) / 4000;
    if (!klpu_r.ann || klh_rd32(klpu_r.ann) != (DWORD)(DWORD_PTR)&klpu_evt[1] || !klu_draw_on) return;
    if (ph > 1) { klpu_r.test_n = 0; return; }                       /* the ring's phase: the next round's messages may go again */
    if (klpu_r.test_n == (int)ph + 1000) return;                     /* this phase's message is out already */
    klpu_r.test_n = (int)ph + 1000; klpu_r.test_at = now | 1;
    if (ph == 1 && !klpu_traitor_ok) {                               /* the level's text lookup gave nothing: the draft's own words stand in, the box is told by the string */
        strcpy(klpu_traitor, "You're now a traitor."); InterlockedExchange(&klpu_traitor_ok, 1);
    }
    msg = ph == 1 ? klpu_traitor : "Looting has started. Trust no-one";
    ((void (__fastcall *)(void *, void *, const char *, float))(DWORD_PTR)KLH_VA(KLPU_ANNOUNCE))((void *)(DWORD_PTR)klpu_r.ann, 0, msg, 3.8f);
    if (klu.log) klog("hud: popup: TEST message '%s' shown through 0x468430 (phase %d of 3: plain / traitor / ring at 60 %%)", msg, (int)ph);
}

static void klpu_tick(int game_thread)
{
    static DWORD last, said; DWORD now = GetTickCount(), osd; struct klb_snap s; int have, human_traitor = 0;
    if ((!klpu.popups && !klpu.ring) || !klu.on || !klh_exe_ok || !game_thread || now - last < 50) return;
    last = now;
    /* this part lives on klhud.c's level state: its OSD, made texts, no fault (klu_tick runs just before this) */
    osd = klu_r.osd;
    if (!osd || !klu_r.made || klu_r.fault || !klu_r.elem || klh_rd32(osd) != KLU_OSD_VT) { if (klpu_r.osd) klpu_forget(); return; }
    if (osd != klpu_r.osd) { klpu_forget(); klpu_r.osd = osd; }
    if (klpu_r.refused) return;
    if (!klu_r.pic_done) klu_pic_prep(klu_r.elem);                   /* klhud.c reads the picture handles only with Plates / Dials / PicTest */
    if (!klpu_wrap(osd)) { klpu_r.refused = 1; InterlockedExchange(&klpu_ring_on, 0); return; }
    if (!klpu_r.told_pics) {
        klpu_r.told_pics = 1;
        if (klu.log) klog("hud: popup: pictures of this level: bar %s, traitor box %s, ring dab %s, disc %s, thin ring %s, dollar %s",
                          klu_r.handle[111] ? "111 (the painted stroke)" : klu_r.handle[181] ? "181 (plain white: no extras in this level)" : "NONE - the pop-ups stay stock",
                          klu_r.handle[118] ? "118" : "four plain bars", klu_r.handle[113] ? "113" : "NONE - no ring", klu_r.handle[114] ? "114" : "none", klu_r.handle[115] ? "115" : "none", klu_r.handle[116] ? "116" : "none");
    }
    if (klpu.popups && !klpu_r.loc_done) klpu_loc();
    have = klb_read(&s);
    if (have && s.human >= 0) {                                      /* the fall-back's clock: when the human's traitor flag rose */
        DWORD fl = 0;
        klh_rd(s.score + KLU_S_FLAGS + 4 * s.human, &fl, 4);         /* indexed by the crew record: EXE 0x8e878e */
        human_traitor = (s.r[s.human].flags & 2) || (fl & 1);
    }
    if (human_traitor && !klpu_r.was_traitor) InterlockedExchange(&klpu_traitor_at, (LONG)(now | 1));
    if (!human_traitor) InterlockedExchange(&klpu_traitor_at, 0);
    klpu_r.was_traitor = human_traitor;
    if (klpu.ring) klpu_ring_tick(osd, &s, have, now);
    if (klpu.test && klpu.popups) klpu_test_tick(now);
    if (klpu_msg_new) {
        if (klu.log) klog("hud: popup: '%s' (%d line(s)) -> %s; the text object says %.0f x %.0f (%s), the string's length %.0f x %.0f; text at (%.0f, %.0f)%s, bar %.0f x %.0f, layer %d",
                          klpu_msg.text, klpu_msg.lines, klpu_msg.traitor ? (klpu_msg.byflag ? "ORANGE BOX (told by the traitor flag's rise)" : "ORANGE BOX (the traitor message)") : "chalk bar, ink letters",
                          klpu_msg.mw, klpu_msg.mh, klpu_msg.measured ? "used" : "NOT used", klpu_msg.ew, klpu_msg.eh, klpu_msg.x, klpu_msg.y, klpu.y >= 0 ? " (PopupY)" : "", klpu_msg.bw, klpu_msg.bh, klpu.layer);
        if (klu.log && klpu_msg.withflag && !klpu_msg.traitor)
            klog("hud: popup: NOTE: that message came with the rise of your traitor flag and is NOT this level's traitor string '%s': it got the chalk bar (PopupTraitor=2 would box it)", klpu_traitor);
        if (klu.log && klpu_msg.byflag && klpu_msg.known)
            klog("hud: popup: NOTE: the box above was given by the flag alone: the message differs from this level's traitor string '%s'", klpu_traitor);
        if (klu.log && !(klpu_msg.scale > 0.999f && klpu_msg.scale < 1.001f))
            klog("hud: popup: NOTE: the game's frame scale [0xcee050] is %.3f, not 1: the stock frame follows it, the painted bar does not", klpu_msg.scale);
        InterlockedExchange(&klpu_msg_new, 0);
    }
    if (klu.log >= 2 && now - said >= 5000) {
        said = now;
        klog("hud: popup: %ld announcement-element calls, %ld bars, %ld traitor boxes, %ld ring frames, %ld message frames without a picture (ring on %ld, %.0f %%)",
             InterlockedExchange(&klpu_n_call, 0), InterlockedExchange(&klpu_n_bar, 0), InterlockedExchange(&klpu_n_box, 0), InterlockedExchange(&klpu_n_ring, 0), InterlockedExchange(&klpu_n_nopic, 0),
             klpu_ring_on, 100.0f * klpu_f(klpu_ring_frac));
    }
}

static void klpu_init(void)
{   /* after klu_init (klhud.c): its ini helpers and its Enable */
    if (!klu.on) return;
    klpu.popups = klu_inii("Popups", klu.draft, 0, 1); klpu.ring = klu_inii("LootRing", klu.draft, 0, 1);      /* [HUD] Draft=1 turns both on by default (klhud.c) */
    if (!klpu.popups && !klpu.ring) return;
    klpu.frame = klu_inii("PopupFrame", 0, 0, 1); klpu.measure = klu_inii("PopupMeasure", 1, 0, 1);
    klpu.layer = klu_inii("PopupLayer", 0x17, 2, 0x18); klpu.test = klu_inii("PopupTest", 0, 0, 1); klpu.ringmode = klu_inii("RingMode", 1, 1, 2);
    klpu.traitor = klu_inii("PopupTraitor", 1, 0, 2);
    klpu.lift = klu_inii("PopupLift", 1, 0, 1); klpu.liftgap = klu_inif("PopupLiftGap", "6");      /* v22: lift the bar while the ring shows */
    klpu.padx = klu_inif("PopupPadX", "48"); klpu.pady = klu_inif("PopupPadY", "11"); klpu.dy = klu_inif("PopupDY", "3");   /* run T1: the letters sat 4 px under the bar's middle - the BAR goes 4 down */ klpu.y = klu_inif("PopupY", "523");
    klpu.ringx = klu_inif("RingX", "-1"); klpu.ringy = klu_inif("RingY", "-1");
    if (!(klpu.padx >= 0 && klpu.padx <= 400)) klpu.padx = 48.0f; if (!(klpu.pady >= 0 && klpu.pady <= 200)) klpu.pady = 11.0f;
    if (!(klpu.dy >= -200 && klpu.dy <= 200)) klpu.dy = 0;
    if (!(klpu.y >= 40 && klpu.y <= 680)) klpu.y = -1;
    if (!(klpu.ringx <= 1280)) klpu.ringx = -1; if (!(klpu.ringy <= 720)) klpu.ringy = -1;
    klog("hud: popup: on; Popups=%d LootRing=%d PopupFrame=%d PopupMeasure=%d PopupPadX=%.0f PopupPadY=%.0f PopupDY=%.0f PopupY=%.0f PopupLayer=%d PopupTraitor=%d PopupTest=%d RingMode=%d RingX=%.0f RingY=%.0f; only while the HUD of klhud.c draws; NOT RUN IN THE GAME",
         klpu.popups, klpu.ring, klpu.frame, klpu.measure, klpu.padx, klpu.pady, klpu.dy, klpu.y, klpu.layer, klpu.traitor, klpu.test, klpu.ringmode, klpu.ringx, klpu.ringy);
}

#endif /* KLHUD_POPUP_C */
