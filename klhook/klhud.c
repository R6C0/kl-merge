/*
 * klhud.c - the expansion's Fragile Alliance / Arcade HUD, Version 1: a CREW LIST (every heister with the cash he
 * carries) top-left and a MONEY BOX (Total / Loot / Banked / Round) under the round timer top-right, drawn with the
 * game's own text objects; the stock top-left block (name / 'Total score' / 'Round' and the stock crew list) hidden.
 * The owner, 2026-10-11: 'merge the two UIs, gritty yet polished, for FA and Arcade going forward' - design draft
 * https://claude.ai/artifact/ARZVji4pNmpkFz5SFtyTL2, data side re\hud_data.md, the draw code re\hud.md (the hud_re
 * agent's static reading; EXE = read again in kl2.exe build 0490 for this file, debug\dasm.py, 2026-10-11).
 * Part of KLHook (included by klhook.c after klbalance.c; SHIP and TEST alike). NOTHING HERE HAS RUN IN THE GAME.
 * OFF unless [HUD] Enable=1. Live checks and what is assumed: re\hud_hook.md.
 *
 * 1. HOW THE GAME DRAWS ITS HUD (re\hud.md 0, 1, 3; EXE)
 *    osd = the active ZOnScreenDisplay2 (vtable 0xbbe504, 119 slots). NOT [0x154da50]: that global is the class's
 *    static property pair registered by RTP at 0xaedb48 (setter 0x47d800; run H1_stock read 0x54 there). The
 *    instances are found by their vtable in the committed private memory, as klauto.c finds the players (klu_find_osd);
 *    the active one is the candidate whose ZFAPlayerListDisplay (+0x10c4) is real and whose transform (+0x1130+0x1c)
 *    the HUD render has written (1280 x 720). The renderer calls its vtable
 *    slot 55 = 0x558370 Render(ctx, cam) (thiscall, ret 8): `if ([0xce2e9c] == 0) return; id = [cam+0x14c]; if
 *    ([osd+0x1220] && id == [osd+0x1220]) -> 0x64f930 (MenuCam); if (id == [osd+0x121c]) -> 0x4deda0; if (id ==
 *    [osd+0x1210]) -> 0x4942f0; else 0x8bf300(osd, ctx, cam)` = the HUD: it updates every element and draws every
 *    element whose +0x24 != 0 and +0x25 == 0. A text is a ZCHAROBJ (vtable 0xbab45c) the element made at its Init
 *    (0x452390, EXE): tmpl = 0x8ccde0([osd+0xd4c]), font = 0x8ccde0([osd+0xd54] for the FA elements), parent =
 *    0x598460([tmpl+4]), obj = tmpl->vt[+0x19c](parent, 'ZCOB', 0, 0, 0, 0); then obj->SetStyle(+0x220, byte),
 *    SetColour(+0x20c, ARGB), SetFont(+0x23c, font), SetLayer(+0x234, byte); SetText(+0x244, const char *) at any
 *    time; and once a frame obj->Draw(+0x1e8)(ctx, cam, &xform, &pos3) with xform = nine floats {0,0,0, 0,0,0,
 *    1,0,0} (what 0x7f07a0 writes) and pos3 = {x, y, 0} on the 1280 x 720 virtual screen (origin top-left). The
 *    timer's Render 0x81e090 pushes pos, then xform, then cam, then ctx: the argument order is (ctx, cam, &xform,
 *    &pos) - re\hud.md 3.1 names the last two the other way round; the disassembly is followed here. A shadow is
 *    a second object with colour 0x80000000 drawn at (x+2, y+2) one layer below. Style 0x12 = right-aligned (the
 *    timer at x 1216), 0x44 = the player list's (left). Hiding a stock element = byte element+0x25 = 1.
 *
 * 2. WHAT THE HOOK DOES (heap data writes, one private vtable, game calls from the main thread only)
 *    a. THE HOOK on the render path: as klchar.c does for the option object, the OSD's first dword gets a private
 *       copy of its vtable (RTTI locator kept) whose slot 55 is klu_render: it calls the stock 0x558370 and, when
 *       that call took the HUD branch (the same four tests as above, read from the osd and cam), draws our texts
 *       with the same ctx / cam. No code byte of kl2.exe changes (a SHIP build writes import slots and data only).
 *    b. THE TEXTS: made once per OSD instance on the game's main thread through the exact path of 1 (the create
 *       slot of the template must be 0x817810, every routine's first bytes are compared before it is called);
 *       never freed by the hook - ASSUMPTION (re\hud.md 6.4): the scene owns children made by +0x19c and frees
 *       them with the level, as it frees the elements' own texts. A new OSD object or a new scene name = a new
 *       set. Each row is a pair (shadow, text). SetText / SetColour are called from the main-thread tick only when
 *       the string / colour changed (the stock elements do the same in their Tick); the render hook only calls
 *       Draw, under a critical section it TRIES (a busy lock skips the frame, never waits).
 *    c. THE DATA (main-thread tick, every 100 ms): klbot.c's klb_read (Arcade session, rules object, the crew
 *       records: index, actor, status 0 in play / 4 aboard / 6 escaped / 7 dead, stage, flags 1 = AI 2 = traitor,
 *       money = score+0x150+4*i). A record's name = the C string at [[record+0]+8] (EXE 0x841e50, what the stock
 *       refresh 0x6f3000 takes for a row in Arcade; klcrew.c 2 writes the same string). Total = what the stock
 *       'Total score' shows, 0x807520(rules) computed from data (EXE): money of record 0 (if in use) + the dwords
 *       score+0x04 .. +0x10, +0x18 .. +0x24, +0x2c and +0x38; Loot = the human's carried money (his record);
 *       Banked = Total - Loot (what is not in his hands: the previous rounds and the categories of the score
 *       object - their single meanings are NOT established, so the row is called 'Banked', not the draft's
 *       'Rewards'); Round = byte score+0x45. The hook draws only while the session state is 0x17..0x19 (the stock
 *       player list's own window), the ZFATimeDisplay element is enabled and not hidden (the game's cut-scene hide
 *       0x75f780 hides the time display together with the player list: it is the proxy, since we hide the player
 *       list ourselves) and osd+0x1225 ('HUD off') is 0.
 *    d. HIDING: HideStock=1 writes byte +0x25 = 1 of ZFAPlayerListDisplay (osd+0x10c4, vtable checked) once per
 *       OSD and again whenever it reads 0; it is put back to 0 when the hook stands down with the object alive.
 *       That element draws the top-left block AND the stock crew list (re\hud.md 2.2) - ours replaces both. The
 *       end-of-round lists are other elements (ZFAOutroDisplay, ZHeistOutroDisplay) and are not touched.
 *    e. FAULTS: any check that fails (pointer, vtable, code bytes, a null from the game) is logged once and the
 *       part stands down for that OSD; the next level starts afresh.
 *
 * 3. NOT IN VERSION 1 (and why)
 *    Plates behind the blocks: DrawChunk's 0x34-byte descriptor and the scaled xform a 256 x 256 UI_White sprite
 *    needs to become a plate are 'not established in detail' (re\hud.md 3.2); a wrong descriptor is a crash in the
 *    renderer. Strike-through / alpha for a dead heister: SetColour keeps the alpha byte (re\hud.md 3.1), so dead
 *    is grey. Moving the stock timer; the ammo panel; FA online (klb_read is Arcade-only).
 *
 * KLHook.ini
 *   [HUD]
 *   Enable=0          1 = on
 *   Log=1             0 none, 1 'hud: on', the texts made, the stock block hidden, faults; 2 + every text change
 *   Crew=1            the crew list top-left (x CrewX=64, first row y CrewY=36, Row=22 px per row, at most Rows=8)
 *   Money=1           the money box right-aligned at MoneyX=1216 from MoneyY=100 (under the stock timer's two lines)
 *   HideStock=1       hide the stock top-left block (ZFAPlayerListDisplay)
 *   Inset=-1          -1 = leave the game's [0xceeebc] (0.05); else written once per level (e.g. 0.03)
 *   Layer=13          the texts' layer byte (shadows one below); 15 is the timer's
 *   Shadow=1          0 = no drop shadows
 */
#ifndef KLHUD_C
#define KLHUD_C

#define KLU_OSD_PTR     0x0154da50u           /* NOT the instance (run H1_stock read 0x54): the class's static property pair, setter 0x47d800 registered at 0xaedb48. Unused. */
#define KLU_OSD_VT      0x00bbe504u           /* ZOnScreenDisplay2 (re\hud.md 1) */
#define KLU_OSD_NSLOT   119                   /* slots 0..118 (debug\vtfuncs.py ZOnScreenDisplay2: 119 code pointers, then RTTI) */
#define KLU_OSD_RENDER  0x00558370u           /* slot 55 Render(ctx, cam) (re\hud.md 1; section 1 above) */
#define KLU_HUD_GATE    0x00ce2e9cu           /* dword: 0x558370 draws nothing while it is 0 (its first instruction) */
#define KLU_TEXT_VT     0x00bab45cu           /* ZCHAROBJ (re\hud.md 3.1) */
#define KLU_CREATE      0x00817810u           /* ZCHAROBJ vtable +0x19c, the create-child the elements use (re\hud.md 3.1) */
#define KLU_REFOBJ      0x008ccde0u           /* cdecl (REF id) -> object (re\hud.md 3.1; EXE: mov eax,[esp+4] / mov ecx,[0xe0ff90] / push eax / call 0x796ff0) */
#define KLU_PARENT      0x00598460u           /* thiscall on [tmpl+4] -> [[this+0x50]+0x60] or 0 (re\hud.md 3.1, EXE) */
#define KLU_PLIST_VT    0x00bbdf6cu           /* ZFAPlayerListDisplay (re\hud.md 2.2) */
#define KLU_TIME_VT     0x00bbdfecu           /* ZFATimeDisplay (re\hud.md 2.2) */
#define KLU_INSET       0x00ceeebcu           /* float 0.05, the 5 % inset (re\hud.md 4.2) */
#define KLU_TAG         0x5a434f42u           /* 'ZCOB': the class type id of ZCHAROBJ as four chars (re\hud.md 3.1) */

#define KLU_O_TEMPLATE  0xd4c                 /* REF of the ZCHAROBJ template (re\hud.md 1, note on [0]/[1]: 0x4d57f0 pushes it as the first Init argument) */
#define KLU_O_FONT      0xd54                 /* REF of the font the FA elements register with (re\hud.md 2.2: player list, time display, escape: d54) */
#define KLU_O_XFORM     0x1130                /* the screen transform (re\hud.md 4.1): +0x1c = 1280.0, +0x20 = 720.0 once the HUD has drawn */
#define KLU_O_PLIST     0x10c4                /* ZFAPlayerListDisplay * (re\hud.md 2.2) */
#define KLU_O_TIME      0x10cc                /* ZFATimeDisplay * (re\hud.md 2.2) */
#define KLU_O_CAM_MENU  0x1220                /* camera ids 0x558370 compares with [cam+0x14c] (section 1) */
#define KLU_O_CAM_B     0x121c
#define KLU_O_CAM_C     0x1210
#define KLU_O_HUDOFF    0x1225                /* 'HUD off' (re\hud.md 1, 2.3) */
#define KLU_E_ENABLED   0x24                  /* IDisplayInterface +0x24 enabled, +0x25 hidden (re\hud.md 2.1) */
#define KLU_E_HIDDEN    0x25
#define KLU_CAM_ID      0x14c                 /* [cam+0x14c] (0x558387) */

#define KLU_VT_CREATE   0x19c                 /* ZCHAROBJ vtable offsets (re\hud.md 3.1) */
#define KLU_VT_DRAW     0x1e8
#define KLU_VT_COLOUR   0x20c
#define KLU_VT_STYLE    0x220
#define KLU_VT_LAYER    0x234
#define KLU_VT_FONT     0x23c
#define KLU_VT_TEXT     0x244

#define KLU_ROWS        8                     /* crew rows at most (8 criminals in a Fragile Alliance round) */
#define KLU_MONEY       4                     /* Total, Loot, Banked, Round */
#define KLU_NTEXT       (KLU_ROWS + KLU_MONEY)
#define KLU_TEXTLEN     64
#define KLU_STYLE_LEFT  0x44                  /* the player list's style byte (re\hud.md 3.1) */
#define KLU_STYLE_RIGHT 0x12                  /* the timer's: right-aligned at its x (re\hud.md 4.2) */
#define KLU_SHADOW_RGB  0x80000000u           /* [0xbbe4a4] (re\hud.md 3.1) */

/* the draft's colours (ARGB; SetColour takes the RGB, the alpha byte of the object stays) */
#define KLU_C_TEXT      0xffece8dfu
#define KLU_C_YOU       0xff6fb3ffu
#define KLU_C_TRAITOR   0xffe0962eu
#define KLU_C_DEAD      0xff6a6a66u           /* the draft's 0x55ece8df needs alpha, which SetColour keeps: grey instead */
#define KLU_C_ESCAPED   0xff7fd27au
#define KLU_C_TOTAL     0xffe0962eu

struct klu_text { DWORD obj, shadow; float x, y; int on, style; DWORD colour, want_colour; char cur[KLU_TEXTLEN], want[KLU_TEXTLEN]; };

static struct {
    int on, log, crew, money, hide, shadow, layer, rows; float inset, crew_x, crew_y, money_x, money_y, row;
} klu;

static struct {
    DWORD osd, tmpl, font, parent; char scene[160];
    int made, fault, hid, inset_done, visible;
    struct klu_text t[KLU_NTEXT];
} klu_r;
static volatile LONG klu_draw_on;             /* read by the render hook: 1 = texts exist and the round shows the HUD */
static CRITICAL_SECTION klu_cs;
static DWORD klu_vt[KLU_OSD_NSLOT + 1];       /* [0] RTTI locator, [1..] the slots (as klchar.c's klc_vt) */
static int klu_vt_ready;

typedef DWORD (__fastcall *klu_create_t)(void *, void *, DWORD, DWORD, DWORD, DWORD, DWORD, DWORD);
typedef void (__fastcall *klu_set1_t)(void *, void *, DWORD);
typedef void (__fastcall *klu_draw_t)(void *, void *, void *, void *, const float *, const float *);

static int klu_same_code(DWORD va, const BYTE *bytes, int n)
{
    BYTE c[16];
    return n <= (int)sizeof c && klh_rd((DWORD_PTR)KLH_VA(va), c, n) && !memcmp(c, bytes, n);
}

/* ---------------------------------------------------------------- the render hook (any thread; reads only) */

/* The four tests of 0x558370 (section 1): did the stock call just take the HUD branch? */
static int klu_hud_branch(DWORD osd, DWORD cam)
{
    DWORD gate = 0, id = 0, menu = 0, b = 0, c = 0;
    if (!klh_rd((DWORD_PTR)KLH_VA(KLU_HUD_GATE), &gate, 4) || !gate) return 0;
    if (!klh_rd(cam + KLU_CAM_ID, &id, 4) || !klh_rd(osd + KLU_O_CAM_MENU, &menu, 4) || !klh_rd(osd + KLU_O_CAM_B, &b, 4) || !klh_rd(osd + KLU_O_CAM_C, &c, 4)) return 0;
    if (menu && id == menu) return 0;
    if (id == b || id == c) return 0;
    return 1;
}

static void klu_draw_one(DWORD obj, void *ctx, void *cam, float x, float y)
{
    float xform[9] = { 0, 0, 0, 0, 0, 0, 1.0f, 0, 0 };      /* what 0x7f07a0 writes: [+0x18] = 1.0, the rest 0 */
    float pos[3]; DWORD vt, fn;
    pos[0] = x; pos[1] = y; pos[2] = 0;
    if (!obj || !klh_rd(obj, &vt, 4) || vt != KLU_TEXT_VT || !klh_rd(vt + KLU_VT_DRAW, &fn, 4) || fn != 0x5a6d40) return;
    ((klu_draw_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, ctx, cam, xform, pos);
}

/* slot 55 of the private vtable: Render(ctx, cam), thiscall ret 8 (a __fastcall wrapper cleans the same 8 bytes) */
static char __fastcall klu_render(void *osd, void *edx, void *ctx, void *cam)
{
    char r; int i; (void)edx;
    r = ((char (__fastcall *)(void *, void *, void *, void *))(DWORD_PTR)KLH_VA(KLU_OSD_RENDER))(osd, 0, ctx, cam);
    if (!klu_draw_on || (DWORD)(DWORD_PTR)osd != klu_r.osd || !klu_hud_branch((DWORD)(DWORD_PTR)osd, (DWORD)(DWORD_PTR)cam)) return r;
    if (!TryEnterCriticalSection(&klu_cs)) return r;            /* the tick is changing a text: this frame goes without ours */
    if (klu_draw_on && klu_r.made && !klu_r.fault)
        for (i = 0; i < KLU_NTEXT; i++) {
            const struct klu_text *t = &klu_r.t[i];
            if (!t->on || !t->obj) continue;
            if (klu.shadow && t->shadow) klu_draw_one(t->shadow, ctx, cam, t->x + 2.0f, t->y + 2.0f);     /* 0xbbe4ec / 0xbbe4f0 = 2.0 */
            klu_draw_one(t->obj, ctx, cam, t->x, t->y);
        }
    LeaveCriticalSection(&klu_cs);
    return r;
}

/* ---------------------------------------------------------------- the private vtable (main thread) */

static int klu_vtable_tick(DWORD osd)
{   /* -> 1 while the OSD's first dword is ours (installed here when it shows the stock one) */
    static LONG told; DWORD vt, cur;
    if (!klh_rd(osd, &cur, 4)) return 0;
    if (!klu_vt_ready) {
        if (!klh_rd((DWORD_PTR)KLH_VA(KLU_OSD_VT - 4), klu_vt, sizeof klu_vt)) return 0;
        if (klu_vt[1 + 55] != KLU_OSD_RENDER) {
            if (!InterlockedExchange(&told, 1)) klog("hud: slot 55 of ZOnScreenDisplay2 is %08lx, not %08x: the HUD is off", klu_vt[1 + 55], KLU_OSD_RENDER);
            return 0;
        }
        klu_vt[1 + 55] = (DWORD)(DWORD_PTR)klu_render;
        klu_vt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klu_vt[1];
    if (cur == vt) return 1;
    if (cur != KLU_OSD_VT) {
        if (!InterlockedExchange(&told, 1)) klog("hud: the object at [0x154da50] = %08lx has vtable %08lx, not ZOnScreenDisplay2's %08x: the HUD is off", osd, cur, KLU_OSD_VT);
        return 0;
    }
    if (!klh_data((void *)(DWORD_PTR)osd, &vt, 4, "the OSD's vtable (private copy, slot 55 wrapped)")) return 0;
    if (klu.log) klog("hud: osd %08lx now renders through the private vtable (slot 55 -> klu_render, then the stock 0x558370 first)", osd);
    return 1;
}

/* ---------------------------------------------------------------- making the texts (main thread) */

static int klu_rdata_ptr(DWORD v)
{   /* a vtable pointer of the game: read-only bytes of kl2.exe's image */
    char sec[9];
    return v && klh_kind((const void *)(DWORD_PTR)KLH_VA(v), 4, sec) == 'r';
}

static DWORD klu_make_obj(DWORD tmpl, DWORD font, int style, DWORD colour, int layer, char why[160])
{
    DWORD obj = 0, vt = 0, fn;
    obj = ((klu_create_t)(DWORD_PTR)KLH_VA(KLU_CREATE))((void *)(DWORD_PTR)tmpl, 0, klu_r.parent, KLU_TAG, 0, 0, 0, 0);
    if (!obj) { strcpy(why, "the template's create-child returned 0"); return 0; }
    if (!klh_rd(obj, &vt, 4) || vt != KLU_TEXT_VT) { snprintf(why, 160, "the created object %08lx has vtable %08lx, not ZCHAROBJ's", obj, vt); return 0; }
    fn = klh_rd32(vt + KLU_VT_STYLE);  ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, (DWORD)style);
    fn = klh_rd32(vt + KLU_VT_COLOUR); ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, colour);
    fn = klh_rd32(vt + KLU_VT_FONT);   ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, font);
    fn = klh_rd32(vt + KLU_VT_LAYER);  ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, (DWORD)layer);
    fn = klh_rd32(vt + KLU_VT_TEXT);   ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)obj, 0, (DWORD)(DWORD_PTR)"");
    return obj;
}

static int klu_make_all(DWORD osd)
{
    static const BYTE refobj_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x0d, 0x90, 0xff, 0xe0, 0x00 };       /* 0x8ccde0 */
    static const BYTE parent_code[8]  = { 0x8b, 0x41, 0x50, 0x85, 0xc0, 0x75, 0x01, 0xc3 };                   /* 0x598460 */
    static const BYTE create_code[8]  = { 0xa1, 0x40, 0x26, 0xdd, 0x00, 0x56, 0x8b, 0xf1 };                   /* 0x817810 */
    static const BYTE text_code[8]    = { 0x53, 0x8b, 0x5c, 0x24, 0x08, 0x56, 0x8b, 0xf1 };                   /* 0x896e50 SetText */
    static const BYTE draw_code[8]    = { 0x0f, 0xb6, 0x91, 0x87, 0x00, 0x00, 0x00, 0x8b };                   /* 0x5a6d40 Draw */
    static const struct { DWORD off, fn; } slots[6] = { { KLU_VT_CREATE, 0x817810 }, { KLU_VT_DRAW, 0x5a6d40 }, { KLU_VT_COLOUR, 0x8a0a30 },
                                                        { KLU_VT_STYLE, 0x41a470 }, { KLU_VT_LAYER, 0x514720 }, { KLU_VT_FONT, 0x641ba0 } };
    DWORD tref = 0, fref = 0, tmpl, font, tvt = 0, fvt = 0; int i, k, n = 0; char why[160];
    if (!klu_same_code(KLU_REFOBJ, refobj_code, sizeof refobj_code) || !klu_same_code(KLU_PARENT, parent_code, sizeof parent_code) ||
        !klu_same_code(KLU_CREATE, create_code, sizeof create_code) || !klu_same_code(0x896e50, text_code, sizeof text_code) || !klu_same_code(0x5a6d40, draw_code, sizeof draw_code)) {
        klog("hud: osd %08lx: a routine of the text path is not the one this build knows (0x8ccde0 / 0x598460 / 0x817810 / 0x896e50 / 0x5a6d40): no text is made", osd); return 0;
    }
    for (k = 0; k < 6; k++) if (klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + slots[k].off)) != slots[k].fn) {
        klog("hud: osd %08lx: ZCHAROBJ vtable +0x%lx is %08lx, not %08lx: no text is made", osd, slots[k].off, klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + slots[k].off)), slots[k].fn); return 0;
    }
    if (!klh_rd(osd + KLU_O_TEMPLATE, &tref, 4) || !klh_rd(osd + KLU_O_FONT, &fref, 4) || !tref || !fref) { klog("hud: osd %08lx: no template / font REF (+0xd4c %08lx, +0xd54 %08lx): no text is made", osd, tref, fref); return 0; }
    tmpl = (DWORD)(DWORD_PTR)((void *(__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLU_REFOBJ))(tref);
    font = (DWORD)(DWORD_PTR)((void *(__cdecl *)(DWORD))(DWORD_PTR)KLH_VA(KLU_REFOBJ))(fref);
    if (!tmpl || !font || !klh_rd(tmpl, &tvt, 4) || tvt != KLU_TEXT_VT || !klh_rd(font, &fvt, 4) || !klu_rdata_ptr(fvt)) {
        klog("hud: osd %08lx: template REF %08lx -> %08lx (vtable %08lx), font REF %08lx -> %08lx (vtable %08lx): not a ZCHAROBJ template and a font object: no text is made", osd, tref, tmpl, tvt, fref, font, fvt); return 0;
    }
    klu_r.parent = (DWORD)(DWORD_PTR)((void *(__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLU_PARENT))((void *)(DWORD_PTR)klh_rd32(tmpl + 4), 0);
    if (!klu_r.parent) { klog("hud: osd %08lx: the template %08lx has no parent node (0x598460 gave 0): no text is made", osd, tmpl); return 0; }
    klu_r.tmpl = tmpl; klu_r.font = font;
    for (i = 0; i < KLU_NTEXT; i++) {
        struct klu_text *t = &klu_r.t[i];
        int money = i >= KLU_ROWS;
        memset(t, 0, sizeof *t);
        t->style = money ? KLU_STYLE_RIGHT : KLU_STYLE_LEFT;
        t->colour = money && i == KLU_ROWS ? KLU_C_TOTAL : KLU_C_TEXT;
        t->x = money ? klu.money_x : klu.crew_x;
        t->y = money ? klu.money_y + klu.row * (i - KLU_ROWS) : klu.crew_y + klu.row * i;
        if (!(t->obj = klu_make_obj(tmpl, font, t->style, t->colour, klu.layer, why))) { klog("hud: osd %08lx: text %d: %s; the HUD stands down for this level", osd, i, why); return 0; }
        n++;
        if (klu.shadow && !(t->shadow = klu_make_obj(tmpl, font, t->style, KLU_SHADOW_RGB, klu.layer - 1, why))) { klog("hud: osd %08lx: shadow %d: %s; the HUD stands down for this level", osd, i, why); return 0; }
        n += klu.shadow != 0;
    }
    if (klu.log) klog("hud: osd %08lx, %d texts made (template %08lx, font %08lx, parent %08lx; %d crew rows at (%.0f, %.0f), money box right-aligned at (%.0f, %.0f), %.0f px a row, layer %d)",
                      osd, n, tmpl, font, klu_r.parent, klu.rows, klu.crew_x, klu.crew_y, klu.money_x, klu.money_y, klu.row, klu.layer);
    return 1;
}

/* ---------------------------------------------------------------- the data (main thread) */

static void klu_dollars(char *out, int cap, long v)
{   /* $1,234,567 */
    char d[24], *p = d + sizeof d - 1; unsigned long u = v < 0 ? (unsigned long)-v : (unsigned long)v; int k = 0;
    *p = 0;
    do { if (k && k % 3 == 0) *--p = ','; *--p = (char)('0' + u % 10); u /= 10; k++; } while (u);
    snprintf(out, cap, "%s$%s", v < 0 ? "-" : "", p);
}

/* -> every row's wanted text and colour; 0 = nothing to show (no Arcade round, or outside its states) */
static int klu_compose(int *state_ok)
{
    struct klb_snap s; int i, row = 0, human; long total = 0, loot = 0; DWORD cat[0x3c / 4]; char money[24], name[40];
    *state_ok = 0;
    if (!klb_read(&s)) return 0;                              /* klbot.c 1: Arcade, ZGameRulesHeist, the records */
    *state_ok = s.state >= 0x17 && s.state <= 0x19;           /* the stock player list's own window (its Tick 0x76db00) */
    for (i = 0; i < KLU_NTEXT; i++) klu_r.t[i].on = 0;
    human = s.human >= 0 ? s.human : 0;
    for (i = 0; i < s.n && row < klu.rows && row < KLU_ROWS; i++) {
        const struct klb_rec *r = &s.r[i]; struct klu_text *t = &klu_r.t[row]; DWORD blk, str = 0;
        if (!r->used) continue;
        name[0] = 0;
        if ((blk = klh_rd32(r->at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, name, sizeof name);     /* [[record]+8]: 0x841e50 */
        if (!name[0]) snprintf(name, sizeof name, r->flags & 1 ? "Heister %d" : "You", i);
        klu_dollars(money, sizeof money, (long)r->money);
        snprintf(t->want, sizeof t->want, "%s  %s", name, money);
        /* status 0 in play, 4 aboard, 6 escaped (seen live, run K1), 7 dead; flags 1 = AI, 2 = traitor (klbot.c 1) */
        t->want_colour = r->status == 7 ? KLU_C_DEAD : r->status == 6 ? KLU_C_ESCAPED : !(r->flags & 1) ? KLU_C_YOU : (r->flags & 2) ? KLU_C_TRAITOR : KLU_C_TEXT;
        t->on = klu.crew;
        row++;
    }
    /* Total as 0x807520(rules) (EXE): record 0's money when in use, + the score object's dwords +4..+0x10, +0x18..+0x24, +0x2c, + [+0x38] */
    if (klh_rd(s.score + 4, cat, sizeof cat)) {
        static const int add[10] = { 0, 1, 2, 3, 5, 6, 7, 8, 10, 13 };     /* dword indices from +4: +4 +8 +c +10 +18 +1c +20 +24 +2c +38 */
        for (i = 0; i < 10; i++) total += (long)cat[add[i]];
        if (s.r[0].used) total += (long)s.r[0].money;
        loot = s.human >= 0 ? (long)s.r[human].money : 0;
        klu_dollars(money, sizeof money, total); snprintf(klu_r.t[KLU_ROWS].want, KLU_TEXTLEN, "TOTAL  %s", money);
        klu_dollars(money, sizeof money, loot); snprintf(klu_r.t[KLU_ROWS + 1].want, KLU_TEXTLEN, "LOOT  %s", money);
        klu_dollars(money, sizeof money, total - loot); snprintf(klu_r.t[KLU_ROWS + 2].want, KLU_TEXTLEN, "BANKED  %s", money);
        snprintf(klu_r.t[KLU_ROWS + 3].want, KLU_TEXTLEN, "ROUND  %d", s.level);      /* byte score+0x45, clamped as every reader does (klb_read) */
        for (i = 0; i < KLU_MONEY; i++) { klu_r.t[KLU_ROWS + i].on = klu.money; klu_r.t[KLU_ROWS + i].want_colour = i == 0 ? KLU_C_TOTAL : KLU_C_TEXT; }
    }
    return 1;
}

/* SetText / SetColour of every row whose wanted text or colour differs (game thread, under the lock) */
static void klu_apply(void)
{
    int i;
    for (i = 0; i < KLU_NTEXT; i++) {
        struct klu_text *t = &klu_r.t[i]; DWORD vt, fn;
        if (!t->obj || !t->on) continue;
        if (!klh_rd(t->obj, &vt, 4) || vt != KLU_TEXT_VT) { klu_r.fault = 1; klog("hud: text %d (%08lx) no longer has ZCHAROBJ's vtable: the HUD stands down for this level", i, t->obj); return; }
        if (strcmp(t->want, t->cur)) {
            fn = klh_rd32(vt + KLU_VT_TEXT);
            ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)t->obj, 0, (DWORD)(DWORD_PTR)t->want);
            if (klu.shadow && t->shadow) ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)t->shadow, 0, (DWORD)(DWORD_PTR)t->want);
            if (klu.log >= 2) klog("hud: text %d: '%s' -> '%s'", i, t->cur, t->want);
            strcpy(t->cur, t->want);
        }
        if (t->want_colour != t->colour) {
            fn = klh_rd32(vt + KLU_VT_COLOUR);
            ((klu_set1_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)t->obj, 0, t->want_colour);
            if (klu.log >= 2) klog("hud: text %d: colour %08lx -> %08lx", i, t->colour, t->want_colour);
            t->colour = t->want_colour;
        }
    }
}

/* the stock top-left block: hidden while we draw, shown again when we do not */
static void klu_hide_tick(DWORD osd, int want)
{
    DWORD el, vt = 0; BYTE h = 0;
    if (!(el = klh_rd32(osd + KLU_O_PLIST)) || !klh_rd(el, &vt, 4) || vt != KLU_PLIST_VT || !klh_rd(el + KLU_E_HIDDEN, &h, 1)) return;
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

static int klu_fa_shown(DWORD osd)
{   /* the proxy for 'the game shows the FA set now': ZFATimeDisplay enabled and not hidden, 'HUD off' clear */
    DWORD el, vt = 0; BYTE en = 0, h = 1, off = 1;
    if (!(el = klh_rd32(osd + KLU_O_TIME)) || !klh_rd(el, &vt, 4) || vt != KLU_TIME_VT) return 0;
    if (!klh_rd(el + KLU_E_ENABLED, &en, 1) || !klh_rd(el + KLU_E_HIDDEN, &h, 1) || !klh_rd(osd + KLU_O_HUDOFF, &off, 1)) return 0;
    return en && !h && !off;
}

static void klu_reset(const char *why, DWORD osd)
{
    if (klu_r.osd && klu.log) klog("hud: osd %08lx is over (%s): texts dropped%s", klu_r.osd, why, klu_r.made ? " (the scene owns them: not freed by the hook)" : "");
    InterlockedExchange(&klu_draw_on, 0);
    EnterCriticalSection(&klu_cs);
    memset(&klu_r, 0, sizeof klu_r);
    klu_r.osd = osd;
    LeaveCriticalSection(&klu_cs);
}

/* ---------------------------------------------------------------- finding the OSD (main thread) */
static DWORD klu_cand[4]; static int klu_ncand, klu_scan_fails; static DWORD klu_scan_t;

static int klu_find_osd(void)
{   /* every ZOnScreenDisplay2 (stock vtable, or ours once wrapped) in the committed private read-write memory, as
       klauto.c's kla_find_players: 0.1 - 0.3 s on the main thread, so only in an Arcade session's round states (the
       caller's gate), at most every 2 s, and every 15 s after three scans of a scene found no usable one. */
    MEMORY_BASIC_INFORMATION mbi; BYTE *a = (BYTE *)0x10000; static BYTE buf[0x10000]; DWORD t0 = GetTickCount();
    DWORD mine = (DWORD)(DWORD_PTR)&klu_vt[1];
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
                    if ((v == KLU_OSD_VT || (klu_vt_ready && v == mine)) && klu_ncand < 4) klu_cand[klu_ncand++] = (DWORD)((DWORD_PTR)mbi.BaseAddress + o + k);
                }
            }
        }
        a = (BYTE *)mbi.BaseAddress + mbi.RegionSize;
    }
    klu_scan_t = GetTickCount();
    if (klu.log > 1 || (klu.log && klu_ncand)) klog("hud: %d ZOnScreenDisplay2 object(s) found in %lu ms", klu_ncand, klu_scan_t - t0);
    return klu_ncand;
}

static DWORD klu_current_osd(int may_scan)
{   /* the OSD held, while it still is one; else the candidate that has the FA player list element and whose
       transform the HUD render has written (1280 x 720): only one instance is rendered per frame. 0 = none yet. */
    DWORD vt, mine = (DWORD)(DWORD_PTR)&klu_vt[1]; float wh[2]; int i;
    if (klu_r.osd && klh_rd(klu_r.osd, &vt, 4) && (vt == KLU_OSD_VT || (klu_vt_ready && vt == mine))) return klu_r.osd;
    if (!may_scan) return 0;                   /* the scan runs only in an Arcade session's round states (no hitch in menus, loads, the campaign) */
    if (!klu_find_osd()) { klu_scan_fails++; return 0; }
    for (i = 0; i < klu_ncand; i++) {
        DWORD el, evt;
        if (!(el = klh_rd32(klu_cand[i] + KLU_O_PLIST)) || !klh_rd(el, &evt, 4) || evt != KLU_PLIST_VT) continue;
        if (!klh_rd(klu_cand[i] + KLU_O_XFORM + 0x1c, wh, 8) || wh[0] != 1280.0f || wh[1] != 720.0f) continue;
        klu_scan_fails = 0;
        return klu_cand[i];
    }
    klu_scan_fails++;
    return 0;
}

static void klu_tick(int game_thread)
{
    static DWORD last; static int toldthread;
    DWORD now = GetTickCount(), osd, vt = 0; float wh[2] = { 0, 0 }; char scene[160]; int state_ok = 0, show, data;
    if (!klu.on || !klh_exe_ok || now - last < 100) return;
    last = now;
    if (!game_thread) {                       /* every call of the game goes between two of its own frames */
        if (!toldthread++) klog("hud: the tick is not on the game's thread ([KLHook] Tick=0?): the HUD does nothing");
        return;
    }
    if (!klh_scene(scene, sizeof scene)) scene[0] = 0;
    if (strcmp(scene, klu_r.scene)) {
        /* the old OSD is not touched (it went with its level; its hidden element went with it) */
        klu_reset("the scene changed", 0);
        snprintf(klu_r.scene, sizeof klu_r.scene, "%s", scene);
        klu_scan_fails = 0; klu_scan_t = 0;
    }
    {   /* gate for the scan: an Arcade session (klb_read) in the states the FA HUD exists in (0x16 countdown .. 0x19 GO) */
        struct klb_snap pre; int arcade = klb_read(&pre) && pre.state >= 0x16 && pre.state <= 0x19;
        osd = scene[0] ? klu_current_osd(arcade) : 0;
    }
    if (osd != klu_r.osd) {
        klu_reset("the OSD object changed", osd);
        snprintf(klu_r.scene, sizeof klu_r.scene, "%s", scene);
        if (osd && klu.log) klog("hud: osd %08lx (ZOnScreenDisplay2 with the FA player list at %08lx)", osd, klh_rd32(osd + KLU_O_PLIST));
    }
    if (!osd || !scene[0] || klu_r.fault) { InterlockedExchange(&klu_draw_on, 0); return; }
    /* live and drawing: the transform 0x8bf300 writes every HUD frame says 1280 x 720 (re\hud.md 4.1) */
    if (!klh_rd(osd, &vt, 4) || !klh_rd(osd + KLU_O_XFORM + 0x1c, wh, 8) || wh[0] != 1280.0f || wh[1] != 720.0f) { InterlockedExchange(&klu_draw_on, 0); return; }
    if (!klu_vtable_tick(osd)) { klu_r.fault = 1; InterlockedExchange(&klu_draw_on, 0); return; }
    if (klu.inset > 0 && !klu_r.inset_done) {
        float cur = 0;
        klu_r.inset_done = 1;
        if (klh_rd((DWORD_PTR)KLH_VA(KLU_INSET), &cur, 4) && cur != klu.inset && klh_data(KLH_VA(KLU_INSET), &klu.inset, 4, "HUD inset [0xceeebc]") && klu.log)
            klog("hud: inset [0xceeebc] %.3f -> %.3f", cur, klu.inset);
    }
    EnterCriticalSection(&klu_cs);
    data = klu_compose(&state_ok);
    show = data && state_ok && klu_fa_shown(osd);
    if (show && !klu_r.made) {
        if (klu_make_all(osd)) klu_r.made = 1;
        else { klu_r.fault = 1; show = 0; }
    }
    if (klu_r.made && !klu_r.fault && data) klu_apply();
    LeaveCriticalSection(&klu_cs);
    if (klu_r.fault) { InterlockedExchange(&klu_draw_on, 0); klu_hide_tick(osd, 0); return; }
    InterlockedExchange(&klu_draw_on, show && klu_r.made);
    if (klu.hide && (klu.crew || klu.money)) klu_hide_tick(osd, show && klu_r.made);
}

static float klu_inif(const char *key, const char *def)
{
    char t[32];
    GetPrivateProfileStringA("HUD", key, def, t, sizeof t, klh_ini);
    return (float)atof(t);
}

static void klu_init(void)
{
    InitializeCriticalSection(&klu_cs);
    klu.on = GetPrivateProfileIntA("HUD", "Enable", 0, klh_ini) != 0;
    if (!klu.on) return;
    klu.log = (int)GetPrivateProfileIntA("HUD", "Log", 1, klh_ini); if (klu.log < 0) klu.log = 0; if (klu.log > 2) klu.log = 2;
    klu.crew = GetPrivateProfileIntA("HUD", "Crew", 1, klh_ini) != 0;
    klu.money = GetPrivateProfileIntA("HUD", "Money", 1, klh_ini) != 0;
    klu.hide = GetPrivateProfileIntA("HUD", "HideStock", 1, klh_ini) != 0;
    klu.shadow = GetPrivateProfileIntA("HUD", "Shadow", 1, klh_ini) != 0;
    klu.layer = (int)GetPrivateProfileIntA("HUD", "Layer", 0xd, klh_ini); if (klu.layer < 2) klu.layer = 2; if (klu.layer > 15) klu.layer = 15;
    klu.rows = (int)GetPrivateProfileIntA("HUD", "Rows", KLU_ROWS, klh_ini); if (klu.rows < 1) klu.rows = 1; if (klu.rows > KLU_ROWS) klu.rows = KLU_ROWS;
    klu.inset = klu_inif("Inset", "-1"); if (!(klu.inset > 0 && klu.inset < 0.25f)) klu.inset = -1;
    klu.crew_x = klu_inif("CrewX", "64"); klu.crew_y = klu_inif("CrewY", "36");
    klu.money_x = klu_inif("MoneyX", "1216"); klu.money_y = klu_inif("MoneyY", "100");
    klu.row = klu_inif("Row", "22"); if (!(klu.row >= 8 && klu.row <= 64)) klu.row = 22;
    if (!(klu.crew_x >= 0 && klu.crew_x <= 1280)) klu.crew_x = 64; if (!(klu.crew_y >= 0 && klu.crew_y <= 720)) klu.crew_y = 36;
    if (!(klu.money_x >= 0 && klu.money_x <= 1280)) klu.money_x = 1216; if (!(klu.money_y >= 0 && klu.money_y <= 720)) klu.money_y = 100;
    klog("hud: on; Log=%d Crew=%d Money=%d HideStock=%d Shadow=%d Layer=%d Rows=%d Inset=%.3f (-1 = the game's); crew at (%.0f, %.0f), money box at (%.0f, %.0f), %.0f px a row; Arcade only, texts through the game's own ZCHAROBJ path, NOT YET RUN IN THE GAME",
         klu.log, klu.crew, klu.money, klu.hide, klu.shadow, klu.layer, klu.rows, klu.inset, klu.crew_x, klu.crew_y, klu.money_x, klu.money_y, klu.row);
}

#endif /* KLHUD_C */
