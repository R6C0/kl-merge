/*
 * klhud_board.c - the PRE-ROUND PANEL in the new look (2026-10-12, track BOARD). NOT RUN IN THE GAME. Reading + live check B3: re\hud_board.md.
 *   [HUD] Board=1   (default 0 until B3 has run; Draft does NOT switch it on)   ZFAIntroDisplay, the translucent grey panel that shows
 *                   'FRAGILE ALLIANCE ARCADE - ROUND 1 / LIVES LEFT [skulls] / HEIST STARTS IN n SEC' before state 0x19.
 *   BoardInk=1      the panel's plate is drawn INK (0c0c0d) in place of grey, with its own alpha: the chalk letters read on a bright wall
 *   BoardLetters=1  every text of the element that is not dark (the shadows are) is set to CHALK for the call
 *
 * WHAT IS KNOWN (READ in kl2.exe 0x768c40 with capstone, re\hud_board.md 2): ZFAIntroDisplay = [osd+0x10ac], vtable 0xbbdd98, 0xf8 bytes,
 * slot 2 = Render 0x768c40 (ret 8). It draws, in this order: [esi+0x28] = THE PLATE (an object of the text class: SetAlpha 0xff through
 * vtable +0x218, SetSize / alpha through +0x23c with 0x320 and a fade value, Draw through +0x1e8), then the texts [esi+0xac] / [esi+0xb0]
 * (a text and its shadow 2 px apart: 0xbbe4ec / 0xbbe4f0), +0xb4 .. +0xc0, +0xcc / +0xd0 (the second set is the branch of 0x7f6850), and
 * the two rules between the lines by 0x8a6ca0 (colour 0xbbe490 with alpha 0x7f written to +0x9c..+0xa8). This part does not touch the rules
 * or the skulls (they are drawn by the stock code and are picture work: klu_pic cannot draw before state 0x19).
 * WHAT IS GUESSED: that colouring the plate object changes what its Draw paints (it does for the escape panel's plate, which has the same class,
 * run E1 of re\hud_escape.md); that the colour dword keeps its alpha byte in the top byte (we keep it as read); which of the texts are shadows
 * (told by their colour: a dark one is left alone).
 * THREAD NOTE (review 4): klbrd_render runs where the stock Render runs, takes no klu_cs and SetColours objects the main thread may update (same pattern as klhud);
 * if B3 faults, look here first.
 * SHIP rule kept: no code byte changes; the element's vtable pointer -> a private copy with slot 2 wrapped; the plate / the texts get their colour
 * through their own SetColour for the length of ONE stock Render call and are put back in the same call. Included by klhook.c after klhud_tags.c.
 */
#ifndef KLHUD_BOARD_C
#define KLHUD_BOARD_C

#define KLBRD_VT          0x00bbdd98u          /* ZFAIntroDisplay */
#define KLBRD_RENDER      0x00768c40u          /* its slot 2 */
#define KLBRD_O_INTRO     0x10ac               /* osd: the element */
#define KLBRD_NSLOT       12
#define KLBRD_E_PLATE     0x28
#define KLBRD_T_RGB       0x14

static const BYTE klbrd_code[8] = { 0x83, 0xec, 0x58, 0x56, 0x8b, 0xf1, 0x8b, 0x0d };     /* 0x768c40 sub esp,0x58; push esi; mov esi,ecx; mov ecx,[..] */
static const int klbrd_text_off[] = { 0xac, 0xb0, 0xb4, 0xb8, 0xbc, 0xc0, 0xcc, 0xd0 };

static struct { int on, ink, letters, card; } klbrd;
static struct { DWORD osd, elem; int told, told_bad; } klbrd_r;
static int klbrd_code_bad, klbrd_evt_ready;
static DWORD klbrd_evt[KLBRD_NSLOT + 1];        /* [0] RTTI locator, [1..] the slots (the element's private vtable) */
static volatile LONG klbrd_n_call, klbrd_n_done, klbrd_n_card;
static void klsb_intro_draw(void *ctx, void *cam);      /* klhud_board2.c (included after this file) */
static volatile int klbrd_told_place; static float klbrd_place[2];
#define KLBRD_DX     0.0f                       /* the card's backing against the plate's place: GUESSES until the first picture (the stock panel: 800 wide, about 170 high) */
#define KLBRD_DY     (-20.0f)
#define KLBRD_H      170.0f
#define KLBRD_RULE1  52.0f
#define KLBRD_RULE2  104.0f

static int klbrd_txt_ok(DWORD obj) { return obj && klh_rd32(obj) == KLU_TEXT_VT; }

static int klbrd_is_dark(DWORD rgb) { return (int)((rgb >> 16) & 255) + (int)((rgb >> 8) & 255) + (int)(rgb & 255) < 0x180; }

/* slot 2 (Render(ctx, cam), thiscall ret 8) of the private vtable */
static char __fastcall klbrd_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el, plate = 0, plate0 = 0, tx[8], tx0[8]; int i, act = 0; char r; (void)edx;
    InterlockedIncrement(&klbrd_n_call);
    /* 2026-10-13 CARD (BoardCard=1, default; the owner: 'needs new ui / revamp'). Run v37_MENU: the plate's colour did nothing (the grey
       stayed). Run v38_MENU: klhud.c's HUD is made only when the stock FA set shows (18:29:18), i.e. AFTER this panel (18:29:08 .. :20), so
       the panel is restyled HERE, in its own Render: the stock plate is left out (its end [el+0xf4] reads 0 for this one call: the stock
       Render draws the plate only while the clock [[0xdd2640]+0x48] < [el+0xf4] x 1024, 0x768c88 .. 0x768caa), and in its place a dark
       brush backing and two chalk brush rules, through the clock element's pictures (klu_pic; klbrd_tick makes klu_pic_prep run early);
       the title text (+0xac) in coral for the call. The texts, the lives' skulls and the stock's thin rules are the stock Render's.
       Only while the panel stands (that same clock test); the backing's place is the plate's (+0x14 / +0x18, the stock SetSize 800). */
    if (klbrd.on && klbrd.card && e == klbrd_r.elem && ctx && *(const DWORD *)ctx == KLU_CTX_VT) {
        LONG endb = *(const LONG *)(DWORD_PTR)(e + 0xf4), clk = 0; float end; DWORD sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)), title = klh_rd32(e + 0xac), t0 = 0; void *clock = klpu_clock();
        memcpy(&end, &endb, 4);
        if (end > 0 && sys && klh_rd(sys + 0x48, &clk, 4) && (float)clk < end * 1024.0f) {
            float px = *(const float *)(DWORD_PTR)(e + 0x14), py = *(const float *)(DWORD_PTR)(e + 0x18);
            if (!klbrd_told_place) { klbrd_place[0] = px; klbrd_place[1] = py; klbrd_told_place = 1; }
            if (clock) {
                float x0 = px - 400.0f + KLBRD_DX, y0 = py + KLBRD_DY;
                {   /* run v39_MENU: a round dab (113) stretched to 880 x 230 drew nothing; the painted stroke (111, proven on the HUD's rows) in ink */
                    int bk = klu_r.handle[111] ? 111 : klu_r.handle[181] ? 181 : -1;
                    if (bk > 0) klu_pic(clock, ctx, KLU_NPIC, bk, x0 - 20.0f, y0 - 22.0f, 840.0f, KLBRD_H + 34.0f, 0xc80c0c0du, 6);
                }
                if (klu_r.handle[111]) {
                    klu_pic(clock, ctx, KLU_NPIC, 111, x0 + 60.0f, y0 + KLBRD_RULE1, 680.0f, 4.0f, KLU_C_CHALK, 7);
                    klu_pic(clock, ctx, KLU_NPIC, 111, x0 + 60.0f, y0 + KLBRD_RULE2, 680.0f, 4.0f, KLU_C_CHALK, 7);
                }
                InterlockedIncrement(&klbrd_n_card);
            }
            if (klbrd_txt_ok(title)) { t0 = klh_rd32(title + KLBRD_T_RGB); klu_set(title, KLU_VT_COLOUR, (t0 & 0xff000000u) | (KLU_C_CORAL & 0x00ffffffu)); }
            *(volatile LONG *)(DWORD_PTR)(e + 0xf4) = 0;
            r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLBRD_RENDER))(el, 0, ctx, cam);
            klsb_intro_draw(ctx, cam);                 /* [HUD] OnlineIntro (klhud_board2.c): round n of m / players / minutes / your heister, under the card */
            InterlockedCompareExchange((volatile LONG *)(DWORD_PTR)(e + 0xf4), endb, 0);       /* back, unless the game wrote a new end meanwhile */
            if (t0 && klbrd_txt_ok(title)) klu_set(title, KLU_VT_COLOUR, (klh_rd32(title + KLBRD_T_RGB) & 0xff000000u) | (t0 & 0x00ffffffu));
            return r;
        }
    }
    if (klbrd.on && !klbrd.card && e == klbrd_r.elem && ctx && *(const DWORD *)ctx == KLU_CTX_VT) {
        memset(tx, 0, sizeof tx); memset(tx0, 0, sizeof tx0);
        if (klbrd.ink) {
            plate = klh_rd32(e + KLBRD_E_PLATE);
            if (klbrd_txt_ok(plate)) {
                plate0 = klh_rd32(plate + KLBRD_T_RGB);
                klu_set(plate, KLU_VT_COLOUR, (plate0 & 0xff000000u) | (KLU_C_INK & 0x00ffffffu));
                act = 1;
            } else plate = 0;
        }
        if (klbrd.letters)
            for (i = 0; i < 8; i++) {
                DWORD t = klh_rd32(e + klbrd_text_off[i]), c;
                if (!klbrd_txt_ok(t)) continue;
                c = klh_rd32(t + KLBRD_T_RGB);
                if (klbrd_is_dark(c & 0xffffff) || (c & 0xffffff) == (KLU_C_CHALK & 0xffffff)) continue;
                tx[i] = t; tx0[i] = c;
                klu_set(t, KLU_VT_COLOUR, (c & 0xff000000u) | (KLU_C_CHALK & 0x00ffffffu));
                act = 1;
            }
    }
    r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLBRD_RENDER))(el, 0, ctx, cam);
    if (act) {
        /* review SHOULD 3: put back the RGB bytes only; the alpha byte is whatever the stock Render left (it writes SetAlpha / fades inside the call) */
        if (plate && klbrd_txt_ok(plate)) klu_set(plate, KLU_VT_COLOUR, (klh_rd32(plate + KLBRD_T_RGB) & 0xff000000u) | (plate0 & 0x00ffffffu));
        for (i = 0; i < 8; i++) if (tx[i] && klbrd_txt_ok(tx[i])) klu_set(tx[i], KLU_VT_COLOUR, (klh_rd32(tx[i] + KLBRD_T_RGB) & 0xff000000u) | (tx0[i] & 0x00ffffffu));
        InterlockedIncrement(&klbrd_n_done);
    }
    return r;
}

static int klbrd_wrap(DWORD osd)
{   /* -> 1 while the element's first dword is our private vtable */
    DWORD el, cur = 0, vt;
    if (!(el = klh_rd32(osd + KLBRD_O_INTRO)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klbrd_evt_ready) {
        if (!klu_same_code(KLBRD_RENDER, klbrd_code, sizeof klbrd_code) || !klh_rd((DWORD_PTR)KLH_VA(KLBRD_VT - 4), klbrd_evt, sizeof klbrd_evt) || klbrd_evt[1 + 2] != KLBRD_RENDER ||
            klh_rd32((DWORD_PTR)KLH_VA(KLU_TEXT_VT + KLU_VT_COLOUR)) == 0) {
            klog("hud: board: the intro element's Render is not the routine this build knows (0x768c40; slot 2 = %08lx): the panel stays stock", klbrd_evt[1 + 2]);
            klbrd_code_bad = 1;
            return 0;
        }
        klbrd_evt[1 + 2] = (DWORD)(DWORD_PTR)klbrd_render;
        klbrd_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klbrd_evt[1];
    if (cur == vt) { klbrd_r.elem = el; return 1; }
    if (cur != KLBRD_VT) {
        if (!klbrd_r.told_bad) { klbrd_r.told_bad = 1; klog("hud: board: the element at osd+0x10ac = %08lx has vtable %08lx, not ZFAIntroDisplay's: the panel stays stock", el, cur); }
        return 0;
    }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the intro element's vtable (private copy, slot 2 wrapped)")) return 0;
    klbrd_r.elem = el;
    if (klu.log) klog("hud: board: element %08lx (ZFAIntroDisplay, the pre-round panel) now renders through the private vtable (slot 2 -> klbrd_render, then the stock 0x768c40)", el);
    return 1;
}

static void klbrd_tick(int game_thread)
{
    static DWORD last, said; DWORD now = GetTickCount(), osd;
    if (!klbrd.on || !klu.on || !klh_exe_ok || !game_thread || now - last < 250) return;
    last = now;
    osd = klu_r.osd;
    if (!osd || klh_rd32(osd) != KLU_OSD_VT) { klbrd_r.osd = 0; klbrd_r.elem = 0; return; }
    if (osd != klbrd_r.osd) { klbrd_r.osd = osd; klbrd_r.elem = 0; klbrd_r.told_bad = 0; }
    if (klbrd_code_bad) return;
    klbrd_wrap(osd);
    if (klbrd.card && klu_r.elem && !klu_r.pic_done) klu_pic_prep(klu_r.elem);      /* the card draws BEFORE klhud.c is made (it reads the handles only then) */
    if (klbrd_told_place == 1 && klu.log) { klbrd_told_place = 2; klog("hud: board: card: the panel's place (+0x14, +0x18) = (%.1f, %.1f); the backing is drawn from it", klbrd_place[0], klbrd_place[1]); }
    if (klu.log >= 2 && now - said >= 5000) {
        said = now;
        klog("hud: board: %ld intro calls, %ld restyled (plate ink %d, letters %d), %ld as the card", InterlockedExchange(&klbrd_n_call, 0), InterlockedExchange(&klbrd_n_done, 0), klbrd.ink, klbrd.letters, InterlockedExchange(&klbrd_n_card, 0));
    }
}

static void klbrd_init(void)
{   /* after klu_init (klhud.c): its ini helpers and its Enable */
    if (!klu.on) return;
    klbrd.on = klu_inii("Board", 0, 0, 1);
    if (!klbrd.on) return;
    klbrd.card = klu_inii("BoardCard", 1, 0, 1);      /* 2026-10-13: 1 = the draft's card in place of the stock panel; 0 = the old recolour (it did nothing live) */
    klbrd.ink = klu_inii("BoardInk", 1, 0, 1); klbrd.letters = klu_inii("BoardLetters", 1, 0, 1);
    klog("hud: board: on; plate ink %d, letters chalk %d; the pre-round panel only (the round-over page is XML); NOT RUN IN THE GAME", klbrd.ink, klbrd.letters);
}

#endif /* KLHUD_BOARD_C */
