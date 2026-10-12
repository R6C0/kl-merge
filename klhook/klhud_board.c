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

static struct { int on, ink, letters; } klbrd;
static struct { DWORD osd, elem; int told, told_bad; } klbrd_r;
static int klbrd_code_bad, klbrd_evt_ready;
static DWORD klbrd_evt[KLBRD_NSLOT + 1];        /* [0] RTTI locator, [1..] the slots (the element's private vtable) */
static volatile LONG klbrd_n_call, klbrd_n_done;

static int klbrd_txt_ok(DWORD obj) { return obj && klh_rd32(obj) == KLU_TEXT_VT; }

static int klbrd_is_dark(DWORD rgb) { return (int)((rgb >> 16) & 255) + (int)((rgb >> 8) & 255) + (int)(rgb & 255) < 0x180; }

/* slot 2 (Render(ctx, cam), thiscall ret 8) of the private vtable */
static char __fastcall klbrd_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el, plate = 0, plate0 = 0, tx[8], tx0[8]; int i, act = 0; char r; (void)edx;
    InterlockedIncrement(&klbrd_n_call);
    if (klbrd.on && e == klbrd_r.elem && ctx && *(const DWORD *)ctx == KLU_CTX_VT) {
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
    if (klu.log >= 2 && now - said >= 5000) {
        said = now;
        klog("hud: board: %ld intro calls, %ld restyled (plate ink %d, letters %d)", InterlockedExchange(&klbrd_n_call, 0), InterlockedExchange(&klbrd_n_done, 0), klbrd.ink, klbrd.letters);
    }
}

static void klbrd_init(void)
{   /* after klu_init (klhud.c): its ini helpers and its Enable */
    if (!klu.on) return;
    klbrd.on = klu_inii("Board", 0, 0, 1);
    if (!klbrd.on) return;
    klbrd.ink = klu_inii("BoardInk", 1, 0, 1); klbrd.letters = klu_inii("BoardLetters", 1, 0, 1);
    klog("hud: board: on; plate ink %d, letters chalk %d; the pre-round panel only (the round-over page is XML); NOT RUN IN THE GAME", klbrd.ink, klbrd.letters);
}

#endif /* KLHUD_BOARD_C */
