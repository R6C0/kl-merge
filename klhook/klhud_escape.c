/*
 * klhud_escape.c - the expansion HUD's ESCAPE-VEHICLE ELEMENT in the new look (2026-10-11 night, track ESCAPE; owner: 'you can keep
 * it via the restyle you said'). NOT RUN IN THE GAME. Reading + live check E1: re\hud_escape.md.
 *   [HUD] Escape=1   (default = [HUD] Draft)  ZFAEscapeDisplay, the panel at the bottom centre that shows while the getaway
 *                    vehicle waits for / carries the human: the dark rounded plate is NOT drawn; in its place a white painted
 *                    chalk bar (picture 111) with the time in INK letters (names font) centred on it, the vehicle icon in
 *                    ORANGE on its left, the vehicle's health as a framed bar (117 + 111) under it; the two prompt lines
 *                    ('Q Share 50/50 with the driver.' / 'SPACE Hold escape vehicle') in the names font, chalk letters, centred.
 * Part of KLHook, an add-on of klhud.c: included by klhook.c DIRECTLY AFTER klhud_popup.c (uses klu / klu_r / klu_draw_on /
 * klu_pic / klu_pic_prep / klu_set / klu_cap_of / klu_rdata_ptr / klu_inii / klu_inif and klhook.c's klh_rd / klh_rd32 /
 * klh_data / klh_kind). Draws only while klhud.c draws (klu_draw_on). SHIP rule kept: no code byte of kl2.exe changes; heap
 * dwords only (the element's vtable pointer -> a private copy, the plate object's vtable pointer -> a private copy with ONE
 * slot wrapped, a few floats / colours of the element swapped for the length of ONE stock Render call and put back by
 * compare-and-swap), and calls of the text objects' own SetColour / SetStyle / SetFont / SetAlpha.
 *
 * 1. THE ELEMENT (EXE = kl2.exe build 0490, read statically with capstone; re\hud_escape.md has the whole reading)
 *    ZFAEscapeDisplay = [osd+0x111c], vtable 0xbbe9d0, 0x16c bytes. Slots: 2 Render 0x5d7e00 (ret 8), 4 Init 0x773d50, 5 Tick
 *    0x793ae0, 6 Update 0x548190. Fields: +0x08 the OSD, +0x0c the screen transform, +0x14 / +0x18 / +0x1c the anchor
 *    (Update: x = 1280 - 1280 x 0.05 - 765 = 451; y = 720 - 720 x [0x154daac] + [0x154dcbc]), +0x24 enabled, +0x28 'shown', +0x29 /
 *    +0x2a 'the Share / the Hold prompt is usable' (Tick: player vtable +0x258 / +0x264), +0x2c the PLATE (an object made from
 *    the level's 'BackgroundFrame' object, class tag 'ZCOB'), +0x3c the Share text, +0x4c the Hold text, +0x50 the time text,
 *    +0x54 its shadow, +0x58 -> the OSD's picture-table row of the icon (+0x7f8 = picture 170 car, +0x804 = 171 chopper),
 *    +0x5c the icon colour (Tick: state 0,7,8 white, 1,2 green 22ff22, 3,4 yellow aaaa55, 5,6 red cc0000), +0x60 the icon's
 *    DrawChunk record (colour +0x90), +0x94 its shadow record (colour +0xc4 = 80000000), +0xd4 the bar's record, +0xe0 the
 *    bar's quad (0x5ff260 writes the width x T+0x14 to +0x44), +0x144..0x150 the bar's four corner colours, +0x154 the bar colour
 *    (Tick: white while the vehicle's health ratio is > 0, else cc0000).
 * 2. WHAT THE STOCK RENDER DRAWS (0x5d7e00; all READ): only while +0x24 and +0x28 are set, the local player exists and its
 *    vtable +0x1c8 has bit 0x20 and not bit 4. In this order: SetAlpha(0xff) + SetSize(130, 45) + Draw of THE PLATE at
 *    (x + 215, y - 105); the time text at (x + 190, y - 85) (style 1 = left), its shadow at +2 / +2; the icon at (x + 170, y - 83)
 *    (layer 0xf) and its shadow +1 / +1 (layer 0xe); then - unless [0x168e59c] == 2 - the Share line (+0x3c, text 'Exit /
 *    FA_ShareWithDriverExit' or '..PilotExit', placed at +0x30 = (x + 75, y - 32)) and the Hold line (+0x4c, 'Exit /
 *    FA_HoldEscapeVehicle', at +0x30 when [0x168e59c] == 2, else at +0x40 = (x + 75, y + [0x154dcc0])), alpha 0xff when the prompt
 *    is usable, else 0x3f; and last the bar (picture 182 = the OSD's table row +0x888, layer 0xb).
 * 3. HOW THIS PART RESTYLES IT (a private vtable copy of the element, slot 2 = klesc_render, then the stock 0x5d7e00)
 *    - THE PLATE is dropped by its own Draw: the plate object's vtable pointer points at a private copy whose Draw slot (+0x1e8,
 *      4 stack arguments, thiscall) is klesc_plate_draw. While the stock Render runs for us (klesc_in_call) that slot draws OUR
 *      pictures - the bar, the icon, the health bar, all with the layers 0xb..0xd, i.e. UNDER the texts (0xe / 0xf) - and does
 *      not call the plate; otherwise it calls the original. The slot is reached only when every gate of the stock Render has
 *      passed, so our pictures show exactly when the stock panel would have shown. If the plate's Draw slot is not code, the
 *      whole part stays off (the stock look, whole).
 *    - THE ICON and THE BAR are made invisible by their colours' ALPHA for the length of the call ([+0x5c], [+0xc4], [+0x154] ->
 *      alpha 0, put back by compare-and-swap); the stock colours are read first and decide ours (the state's meaning is kept:
 *      green arriving, orange waiting, coral leaving). GUESS: a picture with alpha 0 draws nothing (the traitor box's 0xe6 fill
 *      and the ring's faded dollar show that the alpha counts).
 *    - THE TEXTS: SetColour / SetFont / SetStyle through the objects' own routines, put back (statics klesc_tx) in the same
 *      slot when we do not draw (klesc_dirty), exactly the pattern of klhud_popup.c.
 *    - THE PROMPTS' PLACE: [+0x30] and [+0x40] (x only) are exchanged for the call (Update writes them every frame) so that the
 *      centred lines stand under the bar. EscapeCentre=0 keeps the left-aligned stock place and style.
 *    The knock-down prompt (osd+0x10fc) and every other element are not touched.
 *
 * KLHook.ini, section [HUD] (needs Enable=1)
 *   Escape=0 (Draft=1 -> 1)  1 = the restyled panel
 *   EscapeIcon=30            the icon's side, virtual px (the stock one is about 26 on screen; GUESS until E1)
 *   EscapePadX=18 EscapePadY=7   chalk bar = text + 2 x PadX wide, cap + 2 x PadY high
 *   EscapeBarW=0 EscapeBarH=9    health bar (0 = as wide as the chalk bar); EscapeBarGap=5 below the chalk bar
 *   EscapeLayer=11           the bar's layer (fills + frame +1, +2; the texts are 0xe / 0xf)
 *   EscapePrompts=1          0 = leave the two prompt lines stock
 *   EscapeCentre=1           1 = the prompts centred at the time's centre (style 0x14), 0 = their stock place and style
 *   EscapeDX=0 EscapeDY=0    moves the whole picture set (not the texts) for the E1 pictures
 */
#ifndef KLHUD_ESCAPE_C
#define KLHUD_ESCAPE_C

#define KLESC_VT         0x00bbe9d0u          /* ZFAEscapeDisplay */
#define KLESC_RENDER     0x005d7e00u          /* its slot 2 */
#define KLESC_O_ESC      0x111c               /* osd: the element */
#define KLESC_NSLOT      12
#define KLESC_PLATE_SLOT 122                  /* +0x1e8 / 4: Draw(ctx, cam, &pos3, &xform) */
#define KLESC_PVT_N      256                  /* dwords copied from the plate's vtable (the text class has 150) */
#define KLESC_E_XF       0x0c
#define KLESC_E_POS      0x14
#define KLESC_E_VIS      0x24
#define KLESC_E_SHOWN    0x28
#define KLESC_E_PLATE    0x2c
#define KLESC_E_PSHARE   0x30                 /* float x, y, z: the Share line's place */
#define KLESC_E_SHARE    0x3c
#define KLESC_E_PHOLD    0x40                 /* float x, y, z: the Hold line's place (when [0x168e59c] != 2) */
#define KLESC_E_HOLD     0x4c
#define KLESC_E_TIME     0x50
#define KLESC_E_TSH      0x54
#define KLESC_E_ICONP    0x58
#define KLESC_E_ICONC    0x5c
#define KLESC_E_ICONSH   0xc4
#define KLESC_E_BARQ     0x124                /* +0xe0 + 0x44: the bar quad's width x T+0x14 (0x5ff260) */
#define KLESC_E_BARC     0x154
#define KLESC_F_DX       0x00cef1fcu          /* float 190 : the time text's offset from the anchor */
#define KLESC_F_DY       0x00cef200u          /* float -85 */
#define KLESC_F_BARMAX   0x00cef1f4u          /* float 80  : the bar's full width */
#define KLESC_T_RGB      0x14
#define KLESC_T_STYLE    0x84
#define KLESC_T_ALPHA    0x86
#define KLESC_T_FONT     0xac
#define KLESC_T_GEOM     0x04
#define KLESC_VT_ALPHA   0x218
#define KLESC_STYLE_CENTRE 0x14

#define KLESC_C_TRACK    0xd00c0c0du          /* the health bar's dark backing */
#define KLESC_C_FRAME    0xc0f3f0eau          /* its frame: chalk, a little faded */
#define KLESC_CHAR_W     12.0f                /* the time's width when the object gives none ('00:04' = 5 characters) */

static struct { int on, icon, layer, prompts, centre, barw, barh, bargap, card; float padx, pady, dx, dy; } klesc;

static struct { DWORD osd, elem, plate, plate_vt0; int refused, told, told_geo; DWORD refused_at; } klesc_r;
static int klesc_code_bad;                    /* the Render code is not this build's: for good (S1); every other refusal is retried at the next level */
static DWORD klesc_told_mask;                 /* S2: one log line per reason */
static DWORD klesc_evt[KLESC_NSLOT + 1];      /* [0] RTTI locator, [1..] the slots (the element's private vtable) */
static int klesc_evt_ready;
static DWORD klesc_pvt[1 + KLESC_PVT_N];      /* the plate's private vtable: [0] locator, [1..] slots */
static DWORD klesc_pvt_src, klesc_orig_draw;  /* the vtable it copies, the original Draw */
static volatile LONG klesc_in_call;           /* 1 = the stock Render runs for OUR wrapper (render thread only) */
static volatile LONG klesc_n_call, klesc_n_paint, klesc_n_nopic;
static LONG klesc_dirty_e;                    /* render thread only: the element whose texts may carry a style of ours */

/* the numbers one stock call is painted with (render thread only; written by klesc_prep, read by klesc_paint) */
static struct { float cx, mid, bw, bh, ix, iy, bx, by, bwid, bhgt, frac; DWORD icon_rgb, fill_rgb; int icon_slot, active; void *ctx; } klesc_p;

struct klesc_t { DWORD obj, font0; DWORD rgb0; BYTE style0, alpha0, c_set, st_set, a_set, f_set; };
static struct klesc_t klesc_tx[4];            /* 0 time, 1 its shadow, 2 the Share line, 3 the Hold line */

static float klesc_f(DWORD bits) { float f; memcpy(&f, &bits, 4); return f; }
static DWORD klesc_bits(float f) { DWORD b; memcpy(&b, &f, 4); return b; }

static void *klesc_clock(void)
{   /* the clock element klu_pic borrows its picture desc and transform from (as klhud_popup.c) */
    DWORD el = klu_r.elem;
    return el && klu_r.pic_done && klh_rd32(el) == (DWORD)(DWORD_PTR)&klu_evt[1] ? (void *)(DWORD_PTR)el : 0;
}

/* ---------------------------------------------------------------- the texts */

static void klesc_say(int bit, const char *why)
{   /* S2: the reason the panel stays stock, once per process and reason */
    if (!(klesc_told_mask & (1u << bit))) { klesc_told_mask |= 1u << bit; klog("hud: escape: stands down for this call: %s", why); }
}

static int klesc_txt_ok(DWORD obj) { return obj && klh_rd32(obj) == KLU_TEXT_VT; }

static struct klesc_t *klesc_rec(int i, DWORD obj)
{   /* the record of text i for object obj; a new object = a new record (the old one was freed with its level) */
    struct klesc_t *r = &klesc_tx[i];
    if (r->obj != obj) {
        memset(r, 0, sizeof *r);
        r->obj = obj; r->rgb0 = klh_rd32(obj + KLESC_T_RGB) & 0xffffff; r->style0 = (BYTE)klh_rd32(obj + KLESC_T_STYLE);
        r->alpha0 = (BYTE)klh_rd32(obj + KLESC_T_ALPHA); r->font0 = klh_rd32(obj + KLESC_T_FONT);
    }
    return r;
}

static void klesc_style_text(int i, DWORD obj, int setc, DWORD rgb, int style, int alpha0, int font)
{   /* setc 0: colour left (rgb is a DWORD: KLU_C_INK / KLU_C_CHALK are negative as int - review M1); style 0: leave; alpha0: 1 = the alpha goes to 0; font 1 = the names font */
    struct klesc_t *r;
    if (!klesc_txt_ok(obj)) return;
    r = klesc_rec(i, obj);
    if (setc && (klh_rd32(obj + KLESC_T_RGB) & 0xffffff) != (rgb & 0xffffff)) { klu_set(obj, KLU_VT_COLOUR, rgb); r->c_set = 1; }
    if (font && klu.fontset) {
        DWORD want = klu_r.fonts[KLU_FNT_NAME], cur = klh_rd32(obj + KLESC_T_FONT);
        if (want && cur && cur != want) { klu_set(obj, KLU_VT_FONT, want); r->f_set = 1; }
    }
    if (style && (BYTE)klh_rd32(obj + KLESC_T_STYLE) != (BYTE)style) { klu_set(obj, KLU_VT_STYLE, (DWORD)style); r->st_set = 1; }
    if (alpha0 && (BYTE)klh_rd32(obj + KLESC_T_ALPHA) != 0) { klu_set(obj, KLESC_VT_ALPHA, 0); r->a_set = 1; }
}

static void klesc_restore_texts(void)
{   /* nothing of ours is left on the stock objects when we do not draw */
    int i;
    for (i = 0; i < 4; i++) {
        struct klesc_t *r = &klesc_tx[i];
        if (r->obj && klesc_txt_ok(r->obj)) {
            if (r->c_set) klu_set(r->obj, KLU_VT_COLOUR, r->rgb0);
            if (r->f_set && r->font0) klu_set(r->obj, KLU_VT_FONT, r->font0);
            if (r->st_set) klu_set(r->obj, KLU_VT_STYLE, r->style0);
            if (r->a_set) klu_set(r->obj, KLESC_VT_ALPHA, r->alpha0);
        }
        memset(r, 0, sizeof *r);
    }
    klesc_dirty_e = 0;
}

/* ---------------------------------------------------------------- the plate: its Draw slot */

static void klesc_paint(void *ctx);
/* Draw(ctx, cam, &pos3, &xform), thiscall, four stack arguments (the stock Render pushes four) = a __fastcall with four */
static void __fastcall klesc_plate_draw(void *obj, void *edx, void *ctx, void *cam, void *pos, void *xf)
{
    (void)edx;
    if (klesc_in_call) { klesc_paint(ctx); return; }          /* the stock plate is not drawn: OUR pictures are, in its place in the draw order */
    ((void (__fastcall *)(void *, void *, void *, void *, void *, void *))(DWORD_PTR)klesc_orig_draw)(obj, 0, ctx, cam, pos, xf);
}

static int klesc_plate_wrap(DWORD plate)
{   /* -> 1 = the plate object's vtable pointer is our private copy */
    DWORD vt = klh_rd32(plate), nv; char sec[9];
    if (vt == (DWORD)(DWORD_PTR)&klesc_pvt[1]) return 1;
    if (!klu_rdata_ptr(vt)) { if (!klesc_r.told) { klesc_r.told = 1; klog("hud: escape: the plate object %08lx has a vtable %08lx outside the image's read-only data: the panel stays stock", plate, vt); } return 0; }
    if (klesc_pvt_src != vt) {
        DWORD slot;
        if (!klh_rd((DWORD_PTR)(vt - 4), klesc_pvt, sizeof klesc_pvt) && !klh_rd((DWORD_PTR)(vt - 4), klesc_pvt, 4 * 161)) return 0;
        slot = klesc_pvt[1 + KLESC_PLATE_SLOT];
        if (klh_kind((const void *)(DWORD_PTR)KLH_VA(slot), 4, sec) != 'x') {
            if (!klesc_r.told) { klesc_r.told = 1; klog("hud: escape: the plate's Draw slot (+0x1e8 of vtable %08lx) = %08lx is not code: the panel stays stock", vt, slot); }
            return 0;
        }
        klesc_orig_draw = slot; klesc_pvt[1 + KLESC_PLATE_SLOT] = (DWORD)(DWORD_PTR)klesc_plate_draw; klesc_pvt_src = vt;
        klog("hud: escape: the plate object %08lx (vtable %08lx, Draw = %08lx %s) now draws through the private vtable (Draw slot wrapped)", plate, vt, slot, slot == 0x5a6d40 ? "= ZCHAROBJ's 0x5a6d40" : "NOT ZCHAROBJ's 0x5a6d40");
    }
    nv = (DWORD)(DWORD_PTR)&klesc_pvt[1];
    if (!klh_data((void *)(DWORD_PTR)plate, &nv, 4, "the plate's vtable (private copy, Draw slot wrapped)")) return 0;
    klesc_r.plate = plate; klesc_r.plate_vt0 = klesc_pvt_src;
    return 1;
}

static void klesc_plate_back(void)
{   /* the plate object gets its own vtable pointer back while we do not draw (render thread) */
    DWORD p = klesc_r.plate;
    if (p && klh_rd32(p) == (DWORD)(DWORD_PTR)&klesc_pvt[1] && klesc_r.plate_vt0) klh_data((void *)(DWORD_PTR)p, &klesc_r.plate_vt0, 4, "the plate's vtable put back");
    klesc_r.plate = 0;
}

/* ---------------------------------------------------------------- the pictures (called from the plate's Draw slot) */

static void klesc_paint(void *ctx)
{
    void *clock = klesc_clock(); float x0; int bar, drew = 0; DWORD fillpic;
    if (!klesc_p.active || !clock || klesc.card) return;          /* EscapeCard: klhud.c draws the van card; nothing here */
    bar = klu_r.handle[111] ? 111 : 181; fillpic = (DWORD)bar;
    x0 = klesc_p.cx - klesc_p.bw * 0.5f;
    /* the chalk bar the time sits on */
    drew |= klu_pic(clock, ctx, KLU_NPIC, bar, x0, klesc_p.mid - klesc_p.bh * 0.5f, klesc_p.bw, klesc_p.bh, KLU_C_CHALK, klesc.layer);
    /* the vehicle icon, orange (the state's meaning kept) */
    if (klesc_p.icon_slot > 0 && klu_r.handle[klesc_p.icon_slot])
        drew |= klu_pic(clock, ctx, KLU_NPIC, klesc_p.icon_slot, klesc_p.ix, klesc_p.iy, (float)klesc.icon, (float)klesc.icon, klesc_p.icon_rgb, klesc.layer + 2);
    /* the health bar: dark track, painted fill, frame */
    drew |= klu_pic(clock, ctx, KLU_NPIC, 181 > 0 && klu_r.handle[181] ? 181 : bar, klesc_p.bx, klesc_p.by, klesc_p.bwid, klesc_p.bhgt, KLESC_C_TRACK, klesc.layer);
    if (klesc_p.frac > 0.005f)
        drew |= klu_pic(clock, ctx, KLU_NPIC, (int)fillpic, klesc_p.bx + 2.0f, klesc_p.by + 2.0f, (klesc_p.bwid - 4.0f) * klesc_p.frac, klesc_p.bhgt - 4.0f, klesc_p.fill_rgb, klesc.layer + 1);
    if (klu_r.handle[117]) klu_pic(clock, ctx, KLU_NPIC, 117, klesc_p.bx, klesc_p.by, klesc_p.bwid, klesc_p.bhgt, KLESC_C_FRAME, klesc.layer + 2);
    if (drew) InterlockedIncrement(&klesc_n_paint); else InterlockedIncrement(&klesc_n_nopic);
}

/* ---------------------------------------------------------------- the render slot (whichever thread renders) */

static DWORD klesc_class_rgb(DWORD rgb)
{   /* the stock icon colour -> ours: green arriving, coral leaving, orange else (waiting / white) */
    int r = (rgb >> 16) & 255, g = (rgb >> 8) & 255, b = rgb & 255;
    (void)r; (void)g; (void)b;
    return KLU_C_ORANGE;                         /* 2026-10-12: the draft's escape colour whatever the state (was green arriving / coral leaving) */
}
#define KLESC_ICON_INK   0.47f               /* the stock icon pictures' ink is about this part of their square (run S1: a 30 px picture showed a 14 px car) */
/* -> 1 = our look is prepared for this call (the writes of section 3 are made; klesc_after puts them back) */
static struct { DWORD e; DWORD iconc, iconc_new, shc, shc_new, barc, barc_new; DWORD px, py, qx, qy; int pos_set; } klesc_w;

static int klesc_prep(DWORD e)
{
    DWORD osd, T, plate, time, tsh, share, hold, iconp, iconc, barc; float ax, ay, dx, dy, cap, tw, ext[2] = { 0, 0 }, bar_a, barmax, quad, mid, top;
    BYTE vis = 0, shown = 0; int bar;
    if (!klh_rd(e + KLESC_E_VIS, &vis, 1) || !klh_rd(e + KLESC_E_SHOWN, &shown, 1) || !vis || !shown) return 0;
    plate = klh_rd32(e + KLESC_E_PLATE); time = klh_rd32(e + KLESC_E_TIME); tsh = klh_rd32(e + KLESC_E_TSH);
    share = klh_rd32(e + KLESC_E_SHARE); hold = klh_rd32(e + KLESC_E_HOLD);
    if (!plate) { klesc_say(0, "the element has no plate object (+0x2c = 0)"); return 0; }
    if (!klesc_txt_ok(time) || !klesc_txt_ok(tsh) || !klesc_txt_ok(share) || !klesc_txt_ok(hold)) { klesc_say(1, "a text object of the element (+0x3c / +0x4c / +0x50 / +0x54) has not the text class's vtable"); return 0; }
    bar = klu_r.handle[111] ? 111 : klu_r.handle[181] ? 181 : -1;
    if (bar < 0) { InterlockedIncrement(&klesc_n_nopic); klesc_say(2, "this level has neither the chalk picture 111 nor the plain 181 (not baked with the extras)"); return 0; }
    if (!klesc_plate_wrap(plate)) return 0;
    osd = klh_rd32(e + 8); T = klh_rd32(e + KLESC_E_XF);
    if (!osd || !T || !klh_rd(e + KLESC_E_POS, &ax, 4) || !klh_rd(e + KLESC_E_POS + 4, &ay, 4) || !(ax > 0 && ax < 1280.0f && ay > 0 && ay < 720.0f)) { klesc_say(3, "the element's osd / transform / anchor is not valid yet"); return 0; }
    dx = klesc_f(klh_rd32((DWORD_PTR)KLH_VA(KLESC_F_DX))); dy = klesc_f(klh_rd32((DWORD_PTR)KLH_VA(KLESC_F_DY)));
    if (!(dx > 100.0f && dx < 400.0f)) dx = 190.0f; if (!(dy < -20.0f && dy > -200.0f)) dy = -85.0f;
    barmax = klesc_f(klh_rd32((DWORD_PTR)KLH_VA(KLESC_F_BARMAX))); if (!(barmax > 10.0f && barmax < 400.0f)) barmax = 80.0f;
    /* the texts: ink on the chalk bar, centred; the shadow gone; the prompts chalk, centred */
    cap = klu.fontset ? klu_cap_of(KLU_FNT_NAME) : 15.0f;
    klesc_dirty_e = (LONG)e;
    if (klesc.card) { klesc_style_text(0, time, 0, 0, 0, 1, 0); klesc_style_text(1, tsh, 0, 0, 0, 1, 0); }     /* EscapeCard: the time is klhud.c's card's */
    else {
    klesc_style_text(0, time, 1, KLU_C_INK, KLESC_STYLE_CENTRE, 0, 1);
    klesc_style_text(1, tsh, 0, 0, KLESC_STYLE_CENTRE, 1, 1);
    }
    if (klesc.prompts) {
        klesc_style_text(2, share, 1, KLU_C_CHALK, klesc.centre ? KLESC_STYLE_CENTRE : 0, 0, 1);
        klesc_style_text(3, hold, 1, KLU_C_CHALK, klesc.centre ? KLESC_STYLE_CENTRE : 0, 0, 1);
        /* review M1: the stock Render sets the prompts' alpha itself on every call (0xff usable, 0x3f dimmed); a write here was overwritten at once, so the dimmed look is the game's own and stays */
    }
    /* the numbers of the pictures */
    if (klh_rd(klh_rd32(time + KLESC_T_GEOM) + 0x40, ext, 8) && ext[0] > 2.0f && ext[0] < 300.0f) tw = 2.0f * ext[0]; else tw = 5.0f * KLESC_CHAR_W;
    top = ay + dy; mid = top + cap * 0.5f + klesc.dy;
    klesc_p.cx = ax + dx + klesc.dx; klesc_p.mid = mid;
    klesc_p.bw = tw + 2.0f * klesc.padx; if (klesc_p.bw < 64.0f) klesc_p.bw = 64.0f;
    klesc_p.bh = cap + 2.0f * klesc.pady;
    klesc_p.ix = klesc_p.cx - klesc_p.bw * 0.5f - 6.0f - (float)klesc.icon * (0.5f + 0.5f * KLESC_ICON_INK); klesc_p.iy = mid - (float)klesc.icon * 0.5f;      /* the INK's right edge 6 px from the bar */
    klesc_p.bwid = klesc.barw > 0 ? (float)klesc.barw : klesc_p.bw; klesc_p.bhgt = (float)klesc.barh;
    klesc_p.bx = klesc_p.cx - klesc_p.bwid * 0.5f; klesc_p.by = mid + klesc_p.bh * 0.5f + (float)klesc.bargap;
    iconp = klh_rd32(e + KLESC_E_ICONP); iconc = klh_rd32(e + KLESC_E_ICONC); barc = klh_rd32(e + KLESC_E_BARC);
    klesc_p.icon_slot = iconp > osd && (iconp - osd) % 12 == 0 && (iconp - osd) / 12 < 200 ? (int)((iconp - osd) / 12) : 170;
    klesc_p.icon_rgb = klesc_class_rgb(iconc);
    quad = klesc_f(klh_rd32(e + KLESC_E_BARQ)); { float a = klesc_f(klh_rd32(T + 0x14)); bar_a = a > 0 ? quad / (a * barmax) : 0; }
    if (!(bar_a >= 0)) bar_a = 0; if (bar_a > 1.0f) bar_a = 1.0f;
    klesc_p.frac = bar_a; klesc_p.fill_rgb = (barc & 0xffffff) == 0xcc0000 ? KLU_C_CORAL : KLU_C_ORANGE;
    klesc_p.active = 1;
    if (klesc.card) {                                            /* the van card (klhud.c compose): this frame, the health share, the icon, the time object */
        InterlockedExchange(&klu_esc_frac, (LONG)klesc_bits(klesc_p.frac)); InterlockedExchange(&klu_esc_slot, (LONG)klesc_p.icon_slot);
        InterlockedExchange(&klu_esc_time, (LONG)time); InterlockedExchange(&klu_esc_at, (LONG)(GetTickCount() | 1));
    }
    /* the stock call's own data: the icon and its shadow and the bar become transparent; the prompts' x moves to the centre */
    klesc_w.e = e; klesc_w.iconc = iconc; klesc_w.iconc_new = iconc & 0x00ffffffu;
    klesc_w.shc = klh_rd32(e + KLESC_E_ICONSH); klesc_w.shc_new = 0;
    klesc_w.barc = barc; klesc_w.barc_new = barc & 0x00ffffffu;
    InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_ICONC), (LONG)klesc_w.iconc_new);
    InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_ICONSH), (LONG)klesc_w.shc_new);
    InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_BARC), (LONG)klesc_w.barc_new);
    klesc_w.pos_set = 0;
    if (klesc.prompts && klesc.centre) {
        klesc_w.px = klh_rd32(e + KLESC_E_PSHARE); klesc_w.qx = klh_rd32(e + KLESC_E_PHOLD); klesc_w.pos_set = 1;
        InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_PSHARE), (LONG)klesc_bits(klesc_p.cx));
        InterlockedExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_PHOLD), (LONG)klesc_bits(klesc_p.cx));
    }
    if (!klesc_r.told_geo) {
        klesc_r.told_geo = 1;
        klog("hud: escape: anchor (%.0f, %.0f), time text at (%.0f, %.0f) width %.0f (%s), cap %.0f -> chalk bar %.0f x %.0f at x %.0f, mid %.0f; icon slot %d at (%.0f, %.0f) %dpx; health bar %.0f x %.0f at (%.0f, %.0f), fraction %.2f (quad %.2f, T+0x14 %.5f); stock icon colour %08lx bar colour %08lx",
             ax, ay, ax + dx, top, tw, ext[0] > 2.0f ? "from the text object" : "a guess", cap, klesc_p.bw, klesc_p.bh, klesc_p.cx - klesc_p.bw * 0.5f, mid, klesc_p.icon_slot, klesc_p.ix, klesc_p.iy, klesc.icon,
             klesc_p.bwid, klesc_p.bhgt, klesc_p.bx, klesc_p.by, klesc_p.frac, quad, klesc_f(klh_rd32(T + 0x14)), iconc, barc);
    }
    return 1;
}

static void klesc_after(DWORD e)
{   /* compare-and-swap: only what is still ours goes back (the Tick writes +0x5c / +0x154 from the game thread) */
    InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_ICONC), (LONG)klesc_w.iconc, (LONG)klesc_w.iconc_new);
    InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_ICONSH), (LONG)klesc_w.shc, (LONG)klesc_w.shc_new);
    InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_BARC), (LONG)klesc_w.barc, (LONG)klesc_w.barc_new);
    if (klesc_w.pos_set) {
        InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_PSHARE), (LONG)klesc_w.px, (LONG)klesc_bits(klesc_p.cx));
        InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + KLESC_E_PHOLD), (LONG)klesc_w.qx, (LONG)klesc_bits(klesc_p.cx));
    }
    klesc_p.active = 0;
}

/* slot 2 (Render(ctx, cam), thiscall ret 8) of the private vtable of the escape element */
static char __fastcall klesc_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el; int act = 0; char r; (void)edx;
    InterlockedIncrement(&klesc_n_call);
    if (klesc.on && e == klesc_r.elem && ctx && *(const DWORD *)ctx == KLU_CTX_VT && klu_draw_on && klesc_clock()) act = klesc_prep(e);
    if (!act && (klesc_dirty_e == (LONG)e || klesc_r.plate)) { klesc_restore_texts(); klesc_plate_back(); }       /* the put-back does not depend on this part's level state */
    if (act) InterlockedExchange(&klesc_in_call, 1);
    r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLESC_RENDER))(el, 0, ctx, cam);
    if (act) { InterlockedExchange(&klesc_in_call, 0); klesc_after(e); }
    return r;
}

/* ---------------------------------------------------------------- main thread */

static int klesc_wrap(DWORD osd)
{   /* -> 1 while the element's first dword is our private vtable */
    static const BYTE render_code[10] = { 0x6a, 0xff, 0x68, 0x2b, 0x23, 0xad, 0x00, 0x64, 0xa1, 0x00 };        /* 0x5d7e00 push -1; push 0xad232b; mov eax, fs:[0] */
    DWORD el, cur = 0, vt;
    if (!(el = klh_rd32(osd + KLESC_O_ESC)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klesc_evt_ready) {
        if (!klu_same_code(KLESC_RENDER, render_code, sizeof render_code) || !klh_rd((DWORD_PTR)KLH_VA(KLESC_VT - 4), klesc_evt, sizeof klesc_evt) || klesc_evt[1 + 2] != KLESC_RENDER ||
            klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + 0x218)) == 0 || klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + KLU_VT_STYLE)) == 0) {
            klog("hud: escape: the element's Render is not the routine this build knows (0x5d7e00; slot 2 = %08lx): the panel stays stock", klesc_evt[1 + 2]);
            klesc_code_bad = 1;
            return 0;
        }
        klesc_evt[1 + 2] = (DWORD)(DWORD_PTR)klesc_render;
        klesc_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klesc_evt[1];
    if (cur == vt) { klesc_r.elem = el; return 1; }
    if (cur != KLESC_VT) { klog("hud: escape: the element at osd+0x111c = %08lx has vtable %08lx, not ZFAEscapeDisplay's: the panel stays stock", el, cur); return 0; }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the escape element's vtable (private copy, slot 2 wrapped)")) return 0;
    klesc_r.elem = el;
    if (klu.log) klog("hud: escape: element %08lx (the escape-vehicle panel) now renders through the private vtable (slot 2 -> klesc_render, then the stock 0x5d7e00)", el);
    return 1;
}

static void klesc_forget(void)
{   /* the level went, or klhud.c dropped its state: the element stays wrapped; its render slot puts the texts back by itself */
    klesc_r.osd = 0; klesc_r.elem = 0; klesc_r.told_geo = 0;
    klesc_r.refused = 0;                                /* S1: a refusal lasts until the level changes */
    memset(klesc_tx, 0, sizeof klesc_tx); klesc_dirty_e = 0; klesc_r.plate = 0; klesc_r.plate_vt0 = 0;       /* S3: forget WITHOUT writing: a freed level's addresses may be a new level's objects */
}

static void klesc_tick(int game_thread)
{
    static DWORD last, said; DWORD now = GetTickCount(), osd;
    if (!klesc.on || !klu.on || !klh_exe_ok || !game_thread || now - last < 50) return;
    last = now;
    osd = klu_r.osd;
    if (!osd || !klu_r.made || klu_r.fault || !klu_r.elem || klh_rd32(osd) != KLU_OSD_VT) { if (klesc_r.osd) klesc_forget(); return; }
    if (osd != klesc_r.osd) { klesc_forget(); klesc_r.osd = osd; }
    if (klesc_code_bad) return;
    if (klesc_r.refused && now - klesc_r.refused_at < 3000) return;             /* S1: a refusal is retried after 3 s (was: for good) */
    if (!klu_r.pic_done) klu_pic_prep(klu_r.elem);
    if (!klesc_wrap(osd)) { klesc_r.refused = 1; klesc_r.refused_at = now; return; }
    klesc_r.refused = 0;
    if (klu.log >= 2 && now - said >= 5000) {
        said = now;
        klog("hud: escape: %ld element calls, %ld painted frames, %ld frames without a picture; chalk bar %s, icon %d %s, frame 117 %s",
             InterlockedExchange(&klesc_n_call, 0), InterlockedExchange(&klesc_n_paint, 0), InterlockedExchange(&klesc_n_nopic, 0),
             klu_r.handle[111] ? "111" : klu_r.handle[181] ? "181 (plain)" : "NONE", klesc_p.icon_slot, klu_r.handle[klesc_p.icon_slot > 0 ? klesc_p.icon_slot : 170] ? "ok" : "NOT DRAWN", klu_r.handle[117] ? "ok" : "none");
    }
}

static void klesc_init(void)
{   /* after klu_init (klhud.c): its ini helpers and its Enable */
    if (!klu.on) return;
    klesc.on = klu_inii("Escape", klu.draft, 0, 1);
    if (!klesc.on) return;
    klesc.card = klu_inii("EscapeCard", 1, 0, 1);      /* 2026-10-13: 1 = the van card in the money box column (the owner: the restyled panel 'looks broken'); 0 = the 2026-10-11 restyle */
    klesc.icon = klu_inii("EscapeIcon", 62, 8, 120); klesc.layer = klu_inii("EscapeLayer", 11, 2, 13);
    klesc.prompts = klu_inii("EscapePrompts", 1, 0, 1); klesc.centre = klu_inii("EscapeCentre", 1, 0, 1);
    klesc.barw = klu_inii("EscapeBarW", 0, 0, 400); klesc.barh = klu_inii("EscapeBarH", 9, 4, 30); klesc.bargap = klu_inii("EscapeBarGap", 5, 0, 60);
    klesc.padx = klu_inif("EscapePadX", "18"); klesc.pady = klu_inif("EscapePadY", "7"); klesc.dx = klu_inif("EscapeDX", "0"); klesc.dy = klu_inif("EscapeDY", "0");
    if (!(klesc.padx >= 0 && klesc.padx <= 200)) klesc.padx = 18; if (!(klesc.pady >= 0 && klesc.pady <= 100)) klesc.pady = 7;
    if (!(klesc.dx > -300 && klesc.dx < 300)) klesc.dx = 0; if (!(klesc.dy > -300 && klesc.dy < 300)) klesc.dy = 0;
    klog("hud: escape: on; icon %d px, layer %d, prompts %d (centred %d), pad %.0f / %.0f, health bar %d x %d (gap %d); only while the HUD of klhud.c draws; NOT RUN IN THE GAME",
         klesc.icon, klesc.layer, klesc.prompts, klesc.centre, klesc.padx, klesc.pady, klesc.barw, klesc.barh, klesc.bargap);
}

#endif /* KLHUD_ESCAPE_C */
