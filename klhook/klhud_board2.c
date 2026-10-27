/*
 * klhud_board2.c - the ROUND-OVER SCOREBOARD drawn by the hook (2026-10-12, track SCOREBOARD; Design B of re\hud_board_b.md). NOT RUN IN THE GAME.
 * Reading, addresses, keys, guesses and live checks SB1 .. SB3: re\hud_scoreboard.md.
 *   [HUD] Scoreboard=1   (default 0; Draft does NOT switch it on; needs Enable=1 and the level's baked fonts: Fonts=1 / Draft=1)
 *
 * WHAT IT REPLACES: the translucent centre panel of state 0x1f ('ROUND 1 / ROUND OVER / YOU SUCCESSFULLY ESCAPED. / LIVES / SCORE / ROUND SCORE /
 * TOTAL SCORE / CONTINUE IN: n', about 8 s after a round) = ZHeistOutroDisplay, [osd+0x10b4], vtable 0xbbde28 (READ in kl2.exe 0490: Render slot 2 =
 * 0x577e70, ret 8, begins 83 ec 3c 56 8b f1 8b 0d; Tick slot 5 = 0x5528c0; the deadline float [el+0xd8] = (engine ms + 0x2800) / 1024, 0x8a5340;
 * the Render draws the plate only while [[0xdd2640]+0x48] < (int)([el+0xd8] * 1024)). The XML page after it (state 0x20: BUY WEAPONS / READY) stays
 * stock (restyled by tools\kl_hud_menu.py level). The pre-round panel is klhud_board.c's.
 *
 * HOW: a private vtable copy of the element, slot 2 wrapped (as klhud_board.c / klhud.c; one heap dword written, no code byte). In the wrapper:
 * if the board is READY (a snapshot taken by the tick in state 0x1f, the pictures usable, the canaries read, the lock TRIED and got) ours is drawn and
 * the stock Render is NOT called; in EVERY other case the stock Render runs unchanged - the owner sees the old panel, never nothing, never both.
 * The stock Tick keeps running (it keeps the deadline and the 'CONTINUE IN' text current).
 *   pictures  klsb_pic2 = klu_pic with the picture description and the transform CACHED from the clock element (klhud.c's wrapped one) in
 *             states 0x16 .. 0x19, the only element whose description is proven (re\hud_hook.md 3); refused unless the outro element's [el+0xc]
 *             (transform) and [el+8] (picture table) equal the clock's. The handles are klu_r.handle[] (type-checked by klu_pic_prep).
 *   texts     a pool of 40 ZCHAROBJs made ONCE per OSD in states 0x17 .. 0x19 through klhud.c's klu_make_obj (the proven create path), strings and
 *             colours set in the tick (main thread, under klsb_cs), drawn by klu_draw_one in the render slot (the lock only TRIED).
 *   data      the tick, state 0x1f only, klb_read + klhud_values.c readers (reads only; every one returns 'nothing' on a failed read, and then the
 *             snapshot is not valid and the stock panel shows).
 *
 * KEYS  [HUD]
 *   Scoreboard=0          1 = on
 *   ScoreboardProbe=0     1 = LOG ONLY, the board is not drawn: once a second from state 0x1f: state, the element's vtable, deadline, frame, wrapper
 *                         calls, the clock wrapper's calls, the three TOTAL candidates (live check SB0)
 *   ScoreboardTest=0      1 = the stock panel is drawn and over it an outline, three texts and three pictures at known places (SB0b)
 *   ScoreboardFault=0     1 = TEST: every reader 'fails' - the stock panel must show (SB-F)
 *   ScoreboardX=320 ScoreboardY=150   the plate's top-left corner (the whole board moves with it); 640 x 400 plate
 *   ScoreboardAlpha=230   the plate's alpha 0..255
 *   ScoreboardTotal=1     TOTAL: 1 (default) = [score+0x38] alone (0x5e0012 already did +0x38 += +0x30 before state 0x1f), 0 = +0x38 + +0x30 (DOUBLE-COUNTS), 2 = the stock 'Total score' (kluv_money.total)
 *   ScoreboardCount=0     the countdown: 0 = the element's deadline [el+0xd8], 1 = the state timer [rules+0x4c]
 *   ScoreboardTextOnly=0  1 = when no picture can be drawn the texts are drawn on their own (the default: back to the stock panel)
 * SHIP rule kept: no .text patch, private vtable copy, every game read guarded, nothing written to the game but the vtable pointer of the element.
 * Included by klhook.c after klhud_board.c.
 */
#ifndef KLHUD_BOARD2_C
#define KLHUD_BOARD2_C

#define KLSB_VT          0x00bbde28u          /* ZHeistOutroDisplay */
#define KLSB_RENDER      0x00577e70u          /* its slot 2 */
#define KLSB_TICKFN      0x005528c0u          /* its slot 5 */
#define KLSB_O_OUTRO     0x10b4               /* osd: the element */
#define KLSB_E_DEADLINE  0xd8                 /* float */
#define KLSB_NTEXT_BASE  52                   /* the pool before [Grades]: with Grades off (or Letter and RankUp off) no more text objects are made than before (inert when off) */
#define KLSB_NT()        (klgrd_pool_extra() ? KLSB_NTEXT : KLSB_NTEXT_BASE)
#define KLSB_NSLOT       16
#define KLSB_NTEXT       66                   /* was 40: 4 more rows of 3 texts (2026-10-26); 52 -> 66: [Grades] GRADE head, RANK UP line, 12 letters (2026-10-27) */
#define KLSB_NPIC        112
#define KLSB_NROW        12                   /* was 8 (online FA is up to 12). More than 8 rows: the pitch shrinks so the plate and summary stay put (klsb_compose, GUESS) */
#define KLSB_NROW_OLD    8

/* ---- the layout, virtual 1280 x 720; every number is relative to the plate's top-left (KLSB_PX, KLSB_PY); tools\kl_hud.py preview-board mirrors them ---- */
#define KLSB_PX          320.0f
#define KLSB_PY          150.0f
#define KLSB_PW          640.0f
#define KLSB_PH          372.0f
#define KLSB_COLL        16.0f                /* name / left label column: plate x + 16  (= 336) */
#define KLSB_COLR        624.0f               /* right edge of the right-aligned column: plate x + 624 (= 944) */
#define KLSB_COLF        240.0f               /* fate column: plate x + 240 (= 560) */
#define KLSB_Y_TITLE     18.0f                /* 168 */
#define KLSB_Y_ROUND     32.0f                /* 182 */
#define KLSB_Y_RESULT    54.0f                /* 204 */
#define KLSB_Y_LIVES     18.0f                /* 168: the label, right-aligned */
#define KLSB_Y_SKULL     34.0f                /* 184: the skulls' top */
#define KLSB_SKULL       14.0f
#define KLSB_SKULL_STEP  16.0f
#define KLSB_Y_RULE      82.0f                /* 232: the painted rule, 600 x 4 */
#define KLSB_Y_HEAD      92.0f                /* 242: the column heads */
#define KLSB_Y_ROW0      112.0f               /* 262: the first row's block top */
#define KLSB_ROW         24.0f
#define KLSB_ROWH        20.0f
#define KLSB_Y_SEP       308.0f               /* 458: the rule above the summary */
#define KLSB_Y_SLAB      324.0f               /* 474: the summary labels' middle (ROUND SCORE / REWARDS / TOTAL SCORE, left-aligned, as the draft) */
#define KLSB_Y_SVAL      343.0f               /* 493: the values' middle (cap 11) */
#define KLSB_Y_STOT      345.0f               /* 495: the total's middle (cap 15) */
#define KLSB_X_S1        16.0f                /* 336 */
#define KLSB_X_S2        184.0f               /* 504: the label font is wide (cap 10, tracking 3: "ROUND SCORE" is about 135 px) */
#define KLSB_X_S3        304.0f               /* 624 */
#define KLSB_X_RING      560.0f               /* 880: the continue ring's middle (2026-10-13, the owner: 'the continue is offset' - 570 crowded the right border) */
#define KLSB_Y_RING      350.0f               /* 500: under the CONTINUE label, beside the values */
#define KLSB_R_RING      17.0f
#define KLSB_Y_CONT      328.0f               /* the CONTINUE label: on the summary labels' row (324). The owner's picture (v37/v38, 2026-10-13): placed at 320 it stood at 315.6, on the rule - a centred label reads 4 px high, so 324 + 4 */
#define KLSB_X_KILLED    160.0f               /* 480: 'KILLED BY name' stands on the result's line, right of it */

/* the text pool: index -> role (font + alignment); the order is the layout above */
#define KLSB_T_TITLE     0
#define KLSB_T_ROUND     1
#define KLSB_T_RESULT    2
#define KLSB_T_KILLED    3
#define KLSB_T_LIVES     4
#define KLSB_T_HEAD(c)   (5 + (c))
#define KLSB_T_ROW(i, c) (8 + 3 * (i) + (c))   /* c 0 name, 1 fate, 2 score */
#define KLSB_T_RSL       44
#define KLSB_T_RSV       45
#define KLSB_T_RWL       46
#define KLSB_T_RWV       47
#define KLSB_T_TOTL      48
#define KLSB_T_TOTV      49
#define KLSB_T_CONTL     50
#define KLSB_T_CONTN     51
#define KLSB_T_GHEAD     52                   /* [Grades] Letter: the GRADE column head */
#define KLSB_T_RANKUP    53                   /* [Grades] RankUp: the 'RANK UP: <rank>' line */
#define KLSB_T_GRADE(i)  (54 + (i))           /* [Grades] Letter: the row's letter, 12 rows */
#define KLSB_COLG        400.0f               /* [Grades] the GRADE column: plate x + 400 (between FATE and PAYOUT; GUESS: free at every row count) */

#define KLSB_ALIGN_L 0
#define KLSB_ALIGN_R 1
#define KLSB_ALIGN_C 2
static const struct { signed char fnt, align; } klsb_role[KLSB_NTEXT] = {
    { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_BIG, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_R },
    { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L },
    { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_BIG, KLSB_ALIGN_L }, { KLU_FNT_LABEL, KLSB_ALIGN_C }, { KLU_FNT_NAME, KLSB_ALIGN_C },
    { KLU_FNT_LABEL, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_R },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L },
    { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L }, { KLU_FNT_NAME, KLSB_ALIGN_L } };

static const BYTE klsb_code[8] = { 0x83, 0xec, 0x3c, 0x56, 0x8b, 0xf1, 0x8b, 0x0d };     /* 0x577e70 sub esp,0x3c; push esi; mov esi,ecx; mov ecx,[..] */

struct klsb_t { DWORD obj, colour, want_colour; float x, y; int on; char cur[KLU_TEXTLEN], want[KLU_TEXTLEN]; };

static struct {
    int on, probe, test, fault, textonly, total, count, lead, rows12;
    int ostate;                               /* 2026-10-27: [HUD] OnlineBoardState (default 0): online, compose the end card from the round-end state and draw it on the clock element's render when the outro element at osd+0x10b4 stays 0 */
    int online, intro;                        /* 2026-10-26: [HUD] OnlineBoard / OnlineIntro (default 0): the end card / the intro lines in an ONLINE round, from klonline_read.c */
    float x, y; int alpha;
} klsb;

static struct {
    DWORD osd, elem;                          /* the outro element of this OSD, wrapped */
    int refused, told_bad, made, pics_cached, valid, told_fault, told_nopic, told_first;
    DWORD T, tbl, desc[13], odesc[13]; int have_o, told_o, wrapfail;                   /* the clock element's transform, picture table and picture description, cached */
    struct klsb_t t[KLSB_NTEXT];
    struct klu_picq pic[KLSB_NPIC]; int npic;
    DWORD state;                              /* the session state of the last tick */
    float cd_max;                             /* the countdown's first value this round */
    LONG sframe; int sset, spath, told_s, told_n; DWORD s_tick0;   /* OnlineBoardState: engine frame at the first state-0x1f tick, the path is live, log latches, tick time of the first compose */
} klsb_r;
static DWORD klsb_evt[KLSB_NSLOT + 1];
static int klsb_evt_ready, klsb_code_bad;
static CRITICAL_SECTION klsb_cs; static int klsb_cs_ready;
static volatile LONG klsb_n_call, klsb_n_ours, klsb_n_stock, klsb_n_busy, klsb_n_refused, klsb_n_srender, klsb_n_sdrawn;

/* ---------------------------------------------------------------- pictures: klu_pic with a CACHED description */

#define klsb_ly(d) (klu.layer - (d) < 0 ? 0 : klu.layer - (d))     /* review NOTE: Layer can be set low; never a negative layer */
static int klsb_pic2(void *ctx, int n, float x, float y, float w, float h, DWORD argb, int layer)
{   /* klu_pic (klhud.c 3) for an element that is not the clock: the description and the transform are the clock's, cached by the tick.
       -> 1 = DrawChunk called. The handle is the one klu_pic_prep type-checked. */
    DWORD handle = n >= 0 && n < 200 ? klu_r.handle[n] : 0, desc[13]; float rec[10], in[2], out[3] = { 0, 0, 0 }; const float *t;
    float xform[9] = { 0, 0, 1.0f, 0, 1.0f, 0, 1.0f, 0, 0 };
    if (!handle || !klsb_r.T || !ctx || *(const DWORD *)ctx != KLU_CTX_VT || !(w > 0) || !(h > 0)) return 0;
    memcpy(desc, klsb_r.have_o ? klsb_r.odesc : klsb_r.desc, sizeof desc);     /* the outro element's own description (el+0xa4, review S1) when it was read, else the clock's */
    t = (const float *)(DWORD_PTR)(klsb_r.T + 0xc);
    memcpy(rec, &desc[3], 40);
    rec[7] = w * t[0]; rec[8] = h * t[1];                            /* GUESS (klhud.c 3 a): the record's size is virtual pixels x T[+0xc], T[+0x10] */
    if (klu.anchor) { x += w * 0.5f; y += h * 0.5f; }                /* GUESS (3 b): the place is the sprite's middle */
    memcpy(&rec[9], &argb, 4);
    desc[2] = (DWORD)(DWORD_PTR)rec;
    in[0] = x; in[1] = y;
    ((void (__fastcall *)(void *, void *, float *, float *))(DWORD_PTR)KLH_VA(KLU_PLACE))((void *)(DWORD_PTR)klsb_r.T, 0, out, in);
    ((DWORD (__fastcall *)(void *, void *, DWORD, DWORD *, float *, float *, DWORD, DWORD, DWORD))(DWORD_PTR)KLH_VA(KLU_DRAWCHUNK))(ctx, 0, handle, desc, xform, out, (DWORD)layer, 1, 0);
    return 1;
}

static void klsb_cache_odesc(void)
{   /* review S1: the stock Render builds its plate from the element's own description at el+0xa4 (same layout as the clock's at +0x40; tint at el+0xd4 = rec[9]).
       Read in state 0x1f (the stock panel has drawn by then); used only if it looks like a description (desc[0]==1, record pointer inside the element or non-null, size words sane); else the clock's stays. */
    DWORD el = klsb_r.elem, d[13]; int k, nz = 0;
    if (klsb_r.have_o || !el || !klsb_r.pics_cached) return;
    if (!klh_rd(el + 0xa4, d, sizeof d)) return;
    for (k = 3; k < 13; k++) if (d[k]) nz = 1;
    if (klu.log && !klsb_r.told_o) klog("hud: scoreboard: descriptions - outro element el+0xa4 head %08lx %08lx %08lx %08lx; clock el+0x40 head %08lx %08lx %08lx %08lx", d[0], d[1], d[2], d[3], klsb_r.desc[0], klsb_r.desc[1], klsb_r.desc[2], klsb_r.desc[3]);
    if (d[0] != 1 || !nz) { klsb_r.told_o = 1; return; }
    memcpy(klsb_r.odesc, d, sizeof d); klsb_r.have_o = 1; klsb_r.told_o = 1;
    if (klu.log) klog("hud: scoreboard: pictures now use the outro element's own description (el+0xa4)");
}

static void klsb_cache_pics(void)
{   /* main thread: the clock element's transform, table and description, once per OSD (the clock draws in states 0x16 .. 0x19: its description is then the proven one) */
    DWORD el = klu_r.elem, d[13];
    if (klsb_r.pics_cached || !el || !klu_r.pic_done) return;
    klsb_r.T = klh_rd32(el + 0xc); klsb_r.tbl = klh_rd32(el + 8);
    if (!klsb_r.T || !klsb_r.tbl || !klh_rd(el + 0x40, d, sizeof d) || d[0] != 1) { klsb_r.T = klsb_r.tbl = 0; return; }
    memcpy(klsb_r.desc, d, sizeof d);
    klsb_r.pics_cached = 1;
    if (klu.log) klog("hud: scoreboard: the clock element's picture description cached (transform %08lx, picture table %08lx, description head %08lx %08lx)", klsb_r.T, klsb_r.tbl, d[0], d[1]);
}

/* ---------------------------------------------------------------- the render slot */

static void klsb_text(int i, void *ctx, void *cam)
{   /* klhud.c's rule: y is the capitals' top (cen); the label font's baked tracking is added back for right / centre alignment */
    const struct klsb_t *t = &klsb_r.t[i]; float tx = t->x;
    if (!t->on || !t->obj) return;
    if (klsb_role[i].fnt == KLU_FNT_LABEL) tx += klsb_role[i].align == KLSB_ALIGN_R ? KLU_TRACK : klsb_role[i].align == KLSB_ALIGN_C ? KLU_TRACK * 0.5f : 0.0f;
    klu_draw_one(t->obj, ctx, cam, tx, t->y);
}

static int klsb_alive(void)
{   /* the canaries (one checked read each): the OSD, text 0 of the pool */
    return klsb_r.osd && klh_rd32(klsb_r.osd) == KLU_OSD_VT && klsb_r.t[0].obj && klh_rd32(klsb_r.t[0].obj) == KLU_TEXT_VT;
}

static int klsb_ours(DWORD e, void *ctx, void *cam)
{   /* -> 1 = the board was drawn (the stock Render must NOT run); 0 = draw nothing, the stock Render runs */
    int i, ok = 0; DWORD sys, end_bits; LONG frame = 0; float end;
    if (!TryEnterCriticalSection(&klsb_cs)) { InterlockedIncrement(&klsb_n_busy); return 0; }
    if (klsb_r.valid && klsb_r.made && klsb_r.state == 0x1f && klsb_alive()) {
        end_bits = *(const DWORD *)(DWORD_PTR)(e + KLSB_E_DEADLINE); memcpy(&end, &end_bits, 4);
        sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF));
        /* the deadline is the GAME clock in 1/1024 s units + 10 s ([[0xdd2640]+0x48], re\climb.md: raw clock + offset, held in a pause; whether it
           restarts at a level load is NOT established): the old bound 1000 (= 1024 s of game clock) sent every round-over after ~17 min of that clock
           back to the stock panel (re\hud_cloud_review.md B1).
           2.0e6 units = 23 days; end * 1024 stays below 2^31 so the LONG cast cannot overflow. NOT BUILT, NOT RUN. */
        if (end > 0 && end < 2.0e6f && sys && klh_rd(sys + 0x48, &frame, 4) && frame < (LONG)(end * 1024.0f)) {
            int pics = klsb_r.pics_cached && *(const DWORD *)(DWORD_PTR)(e + 0xc) == klsb_r.T && *(const DWORD *)(DWORD_PTR)(e + 8) == klsb_r.tbl && (klu_r.handle[111] || klu_r.handle[181]);
            if (pics || klsb.textonly) {
                if (pics) for (i = 0; i < klsb_r.npic; i++) {
                    const struct klu_picq *p = &klsb_r.pic[i];
                    klsb_pic2(ctx, p->n, p->x, p->y, p->w, p->h, p->argb, p->layer);
                }
                for (i = 0; i < KLSB_NT(); i++) klsb_text(i, ctx, cam);
                ok = 1;
            } else InterlockedIncrement(&klsb_n_refused);
        }
    }
    LeaveCriticalSection(&klsb_cs);
    return ok;
}

/* OnlineBoardState (2026-10-27, [HUD] OnlineBoardState=1, needs OnlineBoard=1; NOT run live): online the outro element at osd+0x10b4 can stay 0 for minutes (G10), so there is
   nothing to wrap. The tick then composes the card from the round-end state (GUESS G14: session state 0x1f, as the element path) and this draws it on the CLOCK element's render
   (klhud.c klu_render_elem calls it after the stock render; GUESS G15: that element still renders in state 0x1f; the tick logs when it does not). The countdown runs
   10 s from the tick that first saw 0x1f (GUESS G13/G16, no deadline to read). Read-only toward the replicated state. Not used once the element is wrapped. */
static void klsb_state_render(void *el, void *ctx, void *cam)
{
    int i; DWORD sys; LONG frame = 0, end;
    if (!klsb.on || !klsb.ostate || klsb.probe || klsb.test || !klsb_r.spath || klsb_r.elem || !ctx || (DWORD)(DWORD_PTR)el != klu_r.elem || *(const DWORD *)ctx != KLU_CTX_VT) return;
    InterlockedIncrement(&klsb_n_srender);
    if (!TryEnterCriticalSection(&klsb_cs)) { InterlockedIncrement(&klsb_n_busy); return; }
    end = klsb_r.sframe + 10 * 1024;
    sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF));
    if (klsb_r.valid && klsb_r.made && klsb_r.state == 0x1f && klsb_alive() && klsb_r.pics_cached && sys && klh_rd(sys + 0x48, &frame, 4) && frame < end &&
        *(const DWORD *)(DWORD_PTR)((DWORD)(DWORD_PTR)el + 0xc) == klsb_r.T && *(const DWORD *)(DWORD_PTR)((DWORD)(DWORD_PTR)el + 8) == klsb_r.tbl && (klu_r.handle[111] || klu_r.handle[181])) {
        for (i = 0; i < klsb_r.npic; i++) {
            const struct klu_picq *p = &klsb_r.pic[i];
            klsb_pic2(ctx, p->n, p->x, p->y, p->w, p->h, p->argb, p->layer);
        }
        for (i = 0; i < KLSB_NT(); i++) klsb_text(i, ctx, cam);
        InterlockedIncrement(&klsb_n_sdrawn);
    }
    LeaveCriticalSection(&klsb_cs);
}

static void klsb_testdraw(DWORD e, void *ctx, void *cam)
{   /* ScoreboardTest: over the stock panel (drawn first): an outline, three texts, three pictures - do they appear, where, how large, which tint */
    float x = klsb.x, y = klsb.y; DWORD sys; LONG frame = 0;
    if (klsb_r.state < 0x1f || !klsb_r.made) return;
    (void)e; sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)); if (!sys || !klh_rd(sys + 0x48, &frame, 4)) return;
    if (!TryEnterCriticalSection(&klsb_cs)) return;
    if (klsb_alive() && klsb_r.pics_cached && *(const DWORD *)(DWORD_PTR)(e + 0xc) == klsb_r.T && *(const DWORD *)(DWORD_PTR)(e + 8) == klsb_r.tbl) {      /* review B2: the same transform / table test as klsb_ours (e is the element the game renders now) */
        klsb_pic2(ctx, 181, x, y, KLSB_PW, 1.0f, KLU_C_CORAL, klu.layer); klsb_pic2(ctx, 181, x, y + KLSB_PH - 1.0f, KLSB_PW, 1.0f, KLU_C_CORAL, klu.layer);
        klsb_pic2(ctx, 181, x, y, 1.0f, KLSB_PH, KLU_C_CORAL, klu.layer); klsb_pic2(ctx, 181, x + KLSB_PW - 1.0f, y, 1.0f, KLSB_PH, KLU_C_CORAL, klu.layer);
        klsb_pic2(ctx, klu_r.handle[111] ? 111 : 181, x + 40.0f, y + 300.0f, 160.0f, 24.0f, 0xff0c0c0du, klsb_ly(1));
        klsb_pic2(ctx, klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, x + 240.0f, y + 300.0f, 160.0f, 6.0f, KLU_C_CHALK, klu.layer);
        klsb_pic2(ctx, klu_r.handle[178] ? 178 : 181, x + 440.0f, y + 300.0f, 14.0f, 14.0f, KLU_C_CORAL, klu.layer);
        klsb_text(KLSB_T_TITLE, ctx, cam); klsb_text(KLSB_T_LIVES, ctx, cam); klsb_text(KLSB_T_CONTN, ctx, cam);
    }
    LeaveCriticalSection(&klsb_cs);
}

static char __fastcall klsb_render(void *el, void *edx, void *ctx, void *cam)
{
    DWORD e = (DWORD)(DWORD_PTR)el; char r; (void)edx;
    InterlockedIncrement(&klsb_n_call);
    if (klsb.on && !klsb.probe && !klsb.test && e == klsb_r.elem && ctx && *(const DWORD *)ctx == KLU_CTX_VT && klsb_ours(e, ctx, cam)) {
        InterlockedIncrement(&klsb_n_ours);
        return 1;
    }
    InterlockedIncrement(&klsb_n_stock);
    r = ((klu_render_t)(DWORD_PTR)KLH_VA(KLSB_RENDER))(el, 0, ctx, cam);
    if (klsb.on && klsb.test && e == klsb_r.elem && ctx && *(const DWORD *)ctx == KLU_CTX_VT) klsb_testdraw(e, ctx, cam);
    return r;
}

/* ---------------------------------------------------------------- the private vtable (main thread) */

static int klsb_wrap(DWORD osd)
{   /* -> 1 while the element's first dword is our private vtable. Refuses (and says why) unless the vtable, slots 2 and 5 and the first code bytes are what 0490 has */
    DWORD el, cur = 0, vt;
    if (!(el = klh_rd32(osd + KLSB_O_OUTRO)) || !klh_rd(el, &cur, 4)) return 0;
    if (!klsb_evt_ready) {
        if (!klu_same_code(KLSB_RENDER, klsb_code, sizeof klsb_code) || !klh_rd((DWORD_PTR)KLH_VA(KLSB_VT - 4), klsb_evt, sizeof klsb_evt) ||
            klsb_evt[1 + 2] != KLSB_RENDER || klsb_evt[1 + 5] != KLSB_TICKFN) {
            klog("hud: scoreboard: the outro element's vtable / Render is not what this build knows (slot 2 = %08lx, slot 5 = %08lx; code 0x577e70): the stock panel stays", klsb_evt[1 + 2], klsb_evt[1 + 5]);
            klsb_code_bad = 1;
            return 0;
        }
        klsb_evt[1 + 2] = (DWORD)(DWORD_PTR)klsb_render;
        klsb_evt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klsb_evt[1];
    if (cur == vt) { klsb_r.elem = el; return 1; }
    if (cur != KLSB_VT) {
        if (!klsb_r.told_bad) { klsb_r.told_bad = 1; klog("hud: scoreboard: the element at osd+0x10b4 = %08lx has vtable %08lx, not ZHeistOutroDisplay's (%08lx): the stock panel stays", el, cur, KLSB_VT); }
        return 0;
    }
    if (!klh_data((void *)(DWORD_PTR)el, &vt, 4, "the outro element's vtable (private copy, slot 2 wrapped)")) return 0;
    klsb_r.elem = el;
    if (klu.log) klog("hud: scoreboard: element %08lx (ZHeistOutroDisplay, the round-over panel) now renders through the private vtable (slot 2 -> klsb_render, else the stock 0x577e70)", el);
    return 1;
}

/* ---------------------------------------------------------------- the pool of texts (main thread) */

static void klsb_forget(void)
{   /* the OSD / the round is over: what we hold belongs to a scene that is gone (the objects are the scene's: never freed by the hook) */
    if (klsb_cs_ready) EnterCriticalSection(&klsb_cs);
    memset(&klsb_r, 0, sizeof klsb_r);
    if (klsb_cs_ready) LeaveCriticalSection(&klsb_cs);
}

static int klsb_make_pool(void)
{
    int i; char why[160];
    if (!klu_r.tmpl || !klu_r.parent) return 0;
    for (i = 0; i < KLSB_NT(); i++) {
        int f = klsb_role[i].fnt, st = klsb_role[i].align == KLSB_ALIGN_R ? KLU_STYLE_RIGHT : klsb_role[i].align == KLSB_ALIGN_C ? KLU_STYLE_CENTRE : KLU_STYLE_LEFT;
        DWORD o = klu_make_obj(klu_r.tmpl, klu_r.fonts[f], st, KLU_C_CHALK, klu.layer, why);
        if (!o) { klog("hud: scoreboard: text %d: %s; no board this level", i, why); return 0; }
        klsb_r.t[i].obj = o; klsb_r.t[i].colour = klsb_r.t[i].want_colour = KLU_C_CHALK;
    }
    if (klu.log) klog("hud: scoreboard: %d texts made (template %08lx, parent %08lx; fonts names %08lx big %08lx labels %08lx small %08lx)", KLSB_NT(), klu_r.tmpl, klu_r.parent, klu_r.fonts[0], klu_r.fonts[1], klu_r.fonts[2], klu_r.fonts[3]);
    return 1;
}

/* ---------------------------------------------------------------- the snapshot (main thread, state 0x1f, under klsb_cs) */

static void klsb_put(int i, float x, float y, const char *s, DWORD colour)
{
    struct klsb_t *t = &klsb_r.t[i];
    t->x = x; t->y = y; t->on = s && s[0]; snprintf(t->want, sizeof t->want, "%s", s ? s : ""); t->want_colour = colour;
}

static const char *klsb_fate(const struct klb_snap *s, int i, int traitor, DWORD *colour, int *dead)
{
    *dead = 0; *colour = KLU_C_CHALK;
    switch (kluv_state(s, i)) {
    case KLUV_ST_DEAD: case KLUV_ST_WAITING:                                     *dead = 1; *colour = KLU_C_DEAD; return "DEAD";
    case KLUV_ST_ESCAPED:                                                        *colour = traitor ? KLU_C_ORANGE : KLU_C_GREENHI; return traitor ? "TRAITOR OUT" : "ESCAPED";
    case KLUV_ST_DIRTYCOP: case KLUV_ST_POLICE: case KLUV_ST_UNDERCOP: case KLUV_ST_UNDERCOP2: *colour = KLU_C_BLUE; return "FED";
    case KLUV_ST_ABOARD:                                                         *colour = KLU_C_GREEN; return traitor ? "TRAITOR" : "ABOARD";
    case KLUV_ST_TRAITOR:                                                        *colour = KLU_C_ORANGE; return "TRAITOR";
    default:                                                                     *colour = KLU_C_OUT; return "LEFT BEHIND";
    }
}

/* [Grades] the letter's colour, and the RANK UP line (right-aligned on the title row, left of the LIVES label's skulls) */
static DWORD klsb_grade_colour(char L) { return L == 'S' ? KLU_C_GREENHI : L == 'A' ? KLU_C_GREEN : L == 'B' ? KLU_C_CHALK : L == 'C' ? KLU_C_ORANGE : KLU_C_CORAL; }
static void klsb_grade_put(int row, float px, float rowc, const struct klgrd_in *in)
{
    char L = klgrd_letter(in, 0), t[2];
    if (!L || row < 0 || row >= KLSB_NROW) return;
    t[0] = L; t[1] = 0;
    klsb_put(KLSB_T_GRADE(row), px + KLSB_COLG, klu_cen(rowc, KLU_FNT_NAME), t, klsb_grade_colour(L));
}
static void klsb_rankup_put(float px, float py, int idx)
{
    int b = -1, a = -1; char t[64];
    if (!klgrd_up(idx, &b, &a)) return;
    snprintf(t, sizeof t, "RANK UP  %s", klgrd_name_of(klgrd_nameset(), a));
    for (b = 0; t[b]; b++) if (t[b] >= 'a' && t[b] <= 'z') t[b] = (char)(t[b] - 32);
    klsb_put(KLSB_T_RANKUP, px + KLSB_X_KILLED + 200.0f, klu_cen(py + KLSB_Y_TITLE + 5.0f, KLU_FNT_NAME), t, KLU_C_GREENHI);
}

static int klsb_compose(const struct klb_snap *s, DWORD end_bits, LONG frame)
{   /* -> 1 = a snapshot is ready in klsb_r.t[] / klsb_r.pic[] */
    float px = klsb.x, py = klsb.y, cdv = 0, cdt; char name[KLSB_NROW][48], buf[64], num[40]; int i, human = s->human >= 0 ? s->human : 0, rn = 0, rm = 0;
    int lives, res, lost = 0, over = 0, row = 0, nrow_max = klsb.rows12 ? KLSB_NROW : KLSB_NROW_OLD, nused = 0; float pitch = KLSB_ROW, rowh = KLSB_ROWH; struct kluv_money m; DWORD flags; float rowc; float end;
    (void)rm; (void)lost;
    if (klsb.fault) { if (!klsb_r.told_fault++) klog("hud: scoreboard: ScoreboardFault=1: every reader fails, the stock panel shows"); return 0; }
    if (!kluv_ok(s) || !kluv_idx(s, human)) return 0;
    if (!kluv_money(s, human, &m)) return 0;
    res = kluv_result(s, human, &lost, &over);
    if (res == KLUV_RES_NONE) return 0;
    if (!kluv_round(s, &rn, &rm)) rn = s->level;
    lives = kluv_lives(s);
    memcpy(&end, &end_bits, 4);
    for (i = 0; i < KLSB_NTEXT; i++) klsb_r.t[i].on = 0;
    klsb_r.npic = 0;
    klu_addpic_q = klsb_r.pic; klu_addpic_n = &klsb_r.npic; klu_addpic_cap = KLSB_NPIC;      /* every klu_addpic / klu_outline / klu_arc below goes to OUR queue (cleared again before this returns) */
    klu_addpic(klu_r.handle[181] ? 181 : 111, px, py, KLSB_PW, KLSB_PH, ((DWORD)klsb.alpha << 24) | 0x000c0c0du, klsb_ly(4));      /* the plate: first in the queue. UI_White (181) in ink: picture 111 is a RAGGED brush stroke - stretched over 640 x 372 it shows vertical holes (tools\kl_hud.py preview-board) */
    klu_outline(px, py, KLSB_PW, KLSB_PH, KLU_C_CORAL, klsb_ly(3));
    /* names (the crew list's own way) */
    memset(name, 0, sizeof name);
    for (i = 0; i < s->n && i < nrow_max; i++) nused += s->r[i].used != 0;
    if (nused > KLSB_NROW_OLD) { pitch = 8.0f * KLSB_ROW / (float)nused; rowh = pitch - (KLSB_ROW - KLSB_ROWH); }      /* GUESS: 9..12 rows share the height of 8 (192 px): 12 rows = 16 px pitch, 12 px blocks (cap 11 text); not seen live */
    for (i = 0; i < s->n && i < nrow_max; i++) {
        const struct klb_rec *r = &s->r[i]; DWORD blk, str = 0;
        if (!r->used) continue;
        if ((blk = klh_rd32(r->at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, name[i], sizeof name[i]);
        klnm_name(r->at, name[i], sizeof name[i]);
        if (!name[i][0]) snprintf(name[i], sizeof name[i], r->flags & 1 ? "Heister %d" : "You", i);
        if (i == human) klgrd_decorate(name[i], sizeof name[i], 0, i, 1); else klgrd_decorate_rank(name[i], sizeof name[i], klgrd_bot_rank());     /* [Grades] Badge */
    }
    /* the countdown */
    if (klsb.count == 1) { float tm = 0; if (klh_rd(s->rules + KLUV_R_LEFT, &tm, 4) && tm == tm && tm >= 0 && tm < 100.0f) cdv = tm; }
    else cdv = (end * 1024.0f - (float)frame) / 1024.0f;
    /* 2026-10-25 owner: 'instead of the 10 second countdown to buy shop its 7 then it does it'. The element's deadline is engine ms + 0x2800 = 10 s, but the
       buy-weapons page takes over after 7 s of it, so the count we show starts at 7: subtract the lead (3 s). [HUD] ScoreboardShopLead=<tenths of s>, default 30;
       0 = the raw 10 s. Only the deadline route (ScoreboardCount=0); the state-timer route reads the game's own value. The 3 s is the owner's report, not measured. */
    if (klsb.count == 0 && klsb.lead > 0) { cdv -= klsb.lead / 10.0f; if (cdv < 0) cdv = 0; }
    if (!(cdv >= 0)) cdv = 0;
    if (cdv > 99.0f) cdv = 99.0f;
    if (klsb_r.cd_max <= 0 || cdv > klsb_r.cd_max) klsb_r.cd_max = cdv > 0.5f ? cdv : klsb_r.cd_max;
    cdt = klsb_r.cd_max > 0 ? cdv / klsb_r.cd_max : 0.0f;
    if (cdt > 1.0f) cdt = 1.0f;

    /* ---- top: title, round, result, killed by, lives ---- */
    klsb_put(KLSB_T_TITLE, px + KLSB_COLL, klu_cen(py + KLSB_Y_TITLE + 5.0f, KLU_FNT_LABEL), over ? "GAME OVER" : "ROUND OVER", KLU_C_CORAL);
    snprintf(buf, sizeof buf, "ROUND %d", rn);
    klsb_put(KLSB_T_ROUND, px + KLSB_COLL, klu_cen(py + KLSB_Y_ROUND + 7.5f, KLU_FNT_BIG), buf, KLU_C_CHALK);
    {
        const char *rt; DWORD rc; int killed = 0;
        switch (res) {
        case KLUV_RES_ALL_ESC:  rt = "EVERYBODY ESCAPED"; rc = KLU_C_GREENHI; break;
        case KLUV_RES_YOU_ESC:  rt = "YOU ESCAPED";        rc = KLU_C_GREENHI; break;
        case KLUV_RES_ALL_DEAD: rt = "EVERYBODY IS DEAD";  rc = KLU_C_CORAL;   break;
        case KLUV_RES_LAST_ESC: {   /* every record escaped or police: a human who turned fed or died is not "left behind" (review S6) */
            int hs = kluv_state(s, human);
            if (hs == KLUV_ST_DEAD || hs == KLUV_ST_WAITING) { rt = "YOU ARE DEAD"; rc = KLU_C_CORAL; killed = 1; }
            else if (hs == KLUV_ST_DIRTYCOP || hs == KLUV_ST_POLICE || hs == KLUV_ST_UNDERCOP || hs == KLUV_ST_UNDERCOP2) { rt = "YOU ARE A FED"; rc = KLU_C_BLUE; killed = 1; }
            else { rt = "LEFT BEHIND"; rc = KLU_C_ORANGE; }
            break; }
        case KLUV_RES_YOU_DEAD: rt = "YOU ARE DEAD";       rc = KLU_C_CORAL;   break;
        default:                rt = "TIME IS UP";         rc = KLU_C_ORANGE;  break;
        }
        klsb_put(KLSB_T_RESULT, px + KLSB_COLL, klu_cen(py + KLSB_Y_RESULT + 5.5f, KLU_FNT_NAME), rt, rc);
        if (res == KLUV_RES_YOU_DEAD || res == KLUV_RES_ALL_DEAD || killed) {
            int k = kluv_killer(s, human);
            snprintf(buf, sizeof buf, "KILLED BY  %s", k >= 0 && k < nrow_max && name[k][0] ? name[k] : "THE POLICE");
            klsb_put(KLSB_T_KILLED, px + KLSB_X_KILLED, klu_cen(py + KLSB_Y_RESULT + 5.5f, KLU_FNT_LABEL), buf, KLU_C_CORAL);
        }
    }
    if (klu_r.handle[KLUV_SKULL_PIC]) {
        int k;
        klsb_put(KLSB_T_LIVES, px + KLSB_COLR, klu_cen(py + KLSB_Y_LIVES + 5.0f, KLU_FNT_LABEL), "LIVES", KLU_C_CORAL);
        for (k = 0; k < KLUV_LIVES_MAX; k++)
            klu_addpic(KLUV_SKULL_PIC, px + KLSB_COLR - KLSB_SKULL_STEP * (KLUV_LIVES_MAX - k) + (KLSB_SKULL_STEP - KLSB_SKULL), py + KLSB_Y_SKULL, KLSB_SKULL, KLSB_SKULL, k < lives ? KLU_C_CHALK : 0x4cf3f0eau, klu.layer);
    } else {
        snprintf(buf, sizeof buf, "LIVES %d", lives);
        klsb_put(KLSB_T_LIVES, px + KLSB_COLR, klu_cen(py + KLSB_Y_LIVES + 5.0f, KLU_FNT_LABEL), buf, KLU_C_CORAL);
    }

    /* ---- the crew rows ---- */
    klsb_put(KLSB_T_HEAD(0), px + KLSB_COLL, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "DEAD MEN", KLU_C_CORAL);
    klsb_put(KLSB_T_HEAD(1), px + KLSB_COLF, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "FATE", KLU_C_CORAL);
    klsb_put(KLSB_T_HEAD(2), px + KLSB_COLR, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "PAYOUT", KLU_C_CORAL);      /* record+0x2c, not score+0x30 (review S4) */
    if (klgrd_letter_on()) klsb_put(KLSB_T_GHEAD, px + KLSB_COLG, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "GRADE", KLU_C_CORAL);
    klsb_rankup_put(px, py, human);
    klu_addpic(klu_r.handle[111] ? 111 : 181, px + 20.0f, py + KLSB_Y_RULE, 600.0f, 4.0f, KLU_C_CHALK, klsb_ly(1));            /* the painted rule under the top rows */
    for (i = 0; i < s->n && i < nrow_max; i++) {
        const struct klb_rec *r = &s->r[i]; struct kluv_money mi; const char *fate; DWORD fc, nc, sc, bc = 0; int dead, traitor, you, rr;
        if (!r->used) continue;
        rr = row++;
        flags = kluv_flags(s, i);
        traitor = ((flags & KLUV_F_TRAITOR) || (kluv_early && (r->flags & 2))) != 0;      /* the bot's own mark only with [HUD] TraitorEarly=1 (klhud_values.c) */
        you = i == human;
        fate = klsb_fate(s, i, traitor, &fc, &dead);
        rowc = py + KLSB_Y_ROW0 + pitch * rr + rowh * 0.5f;
        if (!kluv_money(s, i, &mi)) memset(&mi, 0, sizeof mi);
        { long v = mi.payout; if (!v && kluv_state(s, i) == KLUV_ST_ESCAPED) v = mi.carried; if (dead) v = 0; klu_dollars(num, sizeof num, v); }
        if (!dead && (you || traitor)) bc = traitor ? KLU_C_ORANGE : KLU_C_CHALK;
        nc = dead ? KLU_C_DEAD : bc ? KLU_C_INK : KLU_C_CHALK;
        sc = dead ? KLU_C_DEADCASH : bc ? (traitor ? KLU_C_INK : KLU_C_INKCASH) : KLU_C_GREENHI;
        if (bc) { fc = KLU_C_INK; klu_addpic(klu_r.handle[181] ? 181 : 111, px + 8.0f, rowc - rowh * 0.5f, KLSB_PW - 16.0f, rowh, bc, klsb_ly(2));     /* flat 181: the ragged 111 broke the traitor block (review S5) */ }
        klsb_put(KLSB_T_ROW(rr, 0), px + KLSB_COLL, klu_cen(rowc, KLU_FNT_NAME), name[i], nc);
        klsb_put(KLSB_T_ROW(rr, 1), px + KLSB_COLF, klu_cen(rowc, KLU_FNT_LABEL), fate, fc);
        klsb_put(KLSB_T_ROW(rr, 2), px + KLSB_COLR - 8.0f, klu_cen(rowc, KLU_FNT_NAME), num, sc);
        if (klgrd_letter_on()) {   /* [Grades] Letter: Arcade has no per-record kills, so the grade rests on the payout, the rewards (yours) and the fate */
            struct klgrd_in gi; memset(&gi, 0, sizeof gi);
            gi.loot = mi.payout ? mi.payout : mi.carried; gi.rewards = you ? m.rewards : 0; gi.escaped = kluv_state(s, i) == KLUV_ST_ESCAPED; gi.dead = dead; gi.traitor = traitor;
            gi.fed = !strcmp(fate, "FED");
            klsb_grade_put(rr, px, rowc, &gi);
        }
        if (dead) {
            const unsigned char *c; float w = 0;
            for (c = (const unsigned char *)name[i]; *c; c++) if ((*c & 0xc0) != 0x80) w += KLUV_NAME_CHARW;
            klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, px + KLSB_COLL - 4.0f, rowc - 1.0f, w + 8.0f, 2.0f, KLU_C_DEAD, klu.layer);
        }
    }

    /* ---- the summary ---- */
    klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, px + 20.0f, py + KLSB_Y_SEP, 600.0f, 3.0f, KLU_C_CHALK, klsb_ly(1));
    {
        long rs = m.round_score ? m.round_score : m.round_now, tot;
        tot = klsb.total == 0 ? m.banked + rs : klsb.total == 2 ? m.total : m.banked;     /* default 1: +0x38 already holds the rounds before PLUS this one (0x5e0012: +0x38 += +0x30, review M1) */
        klsb_put(KLSB_T_RSL, px + KLSB_X_S1, klu_cen(py + KLSB_Y_SLAB, KLU_FNT_LABEL), "ROUND SCORE", KLU_C_CORAL);
        klu_dollars(num, sizeof num, rs);
        klsb_put(KLSB_T_RSV, px + KLSB_X_S1, klu_cen(py + KLSB_Y_SVAL, KLU_FNT_NAME), num, KLU_C_GREEN);
        klsb_put(KLSB_T_RWL, px + KLSB_X_S2, klu_cen(py + KLSB_Y_SLAB, KLU_FNT_LABEL), "REWARDS", KLU_C_CORAL);
        klu_dollars(num, sizeof num, m.rewards);
        klsb_put(KLSB_T_RWV, px + KLSB_X_S2, klu_cen(py + KLSB_Y_SVAL, KLU_FNT_NAME), num, m.rewards < 0 ? KLU_C_CORAL : KLU_C_GREEN);
        klsb_put(KLSB_T_TOTL, px + KLSB_X_S3, klu_cen(py + KLSB_Y_SLAB, KLU_FNT_LABEL), "TOTAL SCORE", KLU_C_CORAL);
        klu_dollars(num, sizeof num, tot);
        klsb_put(KLSB_T_TOTV, px + KLSB_X_S3, klu_cen(py + KLSB_Y_STOT, KLU_FNT_BIG), num, KLU_C_GREENHI);
    }

    /* ---- the continue ring ---- */
    {
        float cx = px + KLSB_X_RING, cy = py + KLSB_Y_RING;
        snprintf(num, sizeof num, "%d", (int)ceil(cdv - 0.001f));
        klsb_put(KLSB_T_CONTN, cx, klu_cen(cy + 5.5f, KLU_FNT_NAME), num, KLU_C_CHALK);      /* the owner's picture: the count stood 5.5 px above the ring's middle ("the number is still off") */
        klsb_put(KLSB_T_CONTL, cx, klu_cen(py + KLSB_Y_CONT, KLU_FNT_LABEL), "CONTINUE", KLU_C_CORAL);
        /* 2026-10-13, the owner (a picture of this ring): 'countdown bottom right needs to be fixed' - 114 of the watch bake is the watch FACE
           (batons), so the watch look takes a plain dark disc of round brush dabs (113) here, as the gun dial */
        if (klu.wstyle && klu_r.handle[KLU_DAB_PIC]) klu_dab_at(cx, cy, 48.0f, 0x9c080809u, klsb_ly(2));
        else klu_addpic(114, cx - 24.0f, cy - 24.0f, 48.0f, 48.0f, 0x9c080809u, klsb_ly(2));
        klu_track(NULL, NULL, cx, cy, KLSB_R_RING, KLU_TRACK_C, klsb_ly(1));
        klu_arc(NULL, NULL, cx, cy, KLSB_R_RING, 0, 0.0f, cdt, KLU_C_CHALK, klu.layer);
    }
    klu_addpic_q = 0;
    return 1;
}

/* ---------------------------------------------------------------- ONLINE end card (2026-10-26, [HUD] OnlineBoard=1; needs [Online] Read=1, [HUD] Scoreboard=1)
 * Included by klhud_board2.c, after klsb_put. The same plate, rows, summary and ring as klsb_compose, fed by the online reader (klonline_read.c)
 * instead of the Heist records. Read-only toward the replicated state.
 * GUESS G10: the online round-over element at osd+0x10b4 is ZHeistOutroDisplay too (state 0x1f); klsb_wrap refuses it when not, the stock panel stays.
 * GUESS G11: the PAYOUT column is the seat's Sharable + Unsharable (klor_row.money), REWARDS = Sharable (S+0x188), as klhud.c's online TOTAL / REWARDS.
 * GUESS G12: the fate bits are the Arcade flag bits (klu_online_kind).
 * GUESS G13: no shop lead on the countdown (the deadline route, raw 10 s): the online between-rounds page timing is not measured.
 * Rows: humans first, then the AI heisters (no payout: '-'), at most KLSB_NROW. */
static int klsb_compose_online(const struct klor_snap *o, DWORD end_bits, LONG frame)
{
    float px = klsb.x, py = klsb.y, cdv, cdt, pitch = KLSB_ROW, rowh = KLSB_ROWH, rowc, end; char name[KLSB_NROW][48], buf[64], num[40];
    int i, row = 0, nused, loc = o->local, lk = KLUV_K_CREW, over, lives; const struct klor_row *me; DWORD fl = 0;
    if (klsb.fault || !o->ok || o->n < 1) return 0;
    me = klu_onrow(o, loc);
    if (me->used) { fl = klucc_hud_flags(me->flags, loc, loc); lk = klu_online_kind(fl, 1); }
    over = o->rounds > 0 && o->round >= o->rounds;
    lives = KLUV_LIVES_MAX - o->deaths < 0 ? 0 : KLUV_LIVES_MAX - o->deaths;
    memcpy(&end, &end_bits, 4);
    for (i = 0; i < KLSB_NTEXT; i++) klsb_r.t[i].on = 0;
    klsb_r.npic = 0;
    klu_addpic_q = klsb_r.pic; klu_addpic_n = &klsb_r.npic; klu_addpic_cap = KLSB_NPIC;
    klu_addpic(klu_r.handle[181] ? 181 : 111, px, py, KLSB_PW, KLSB_PH, ((DWORD)klsb.alpha << 24) | 0x000c0c0du, klsb_ly(4));
    klu_outline(px, py, KLSB_PW, KLSB_PH, KLU_C_CORAL, klsb_ly(3));
    memset(name, 0, sizeof name);
    nused = o->n + o->nbots; if (nused > KLSB_NROW) nused = KLSB_NROW;
    if (nused > KLSB_NROW_OLD) { pitch = 8.0f * KLSB_ROW / (float)nused; rowh = pitch - (KLSB_ROW - KLSB_ROWH); }
    for (i = 0; i < nused; i++) {
        if (i < o->n) {
            const struct klor_row *r = &o->r[i];
            if (r->name[0]) snprintf(name[i], sizeof name[i], "%s", r->name);
            else if (r->seat == loc) snprintf(name[i], sizeof name[i], "You");
            else snprintf(name[i], sizeof name[i], "Player %d", r->seat + 1);
        } else {
            const struct klor_row *r = &o->bot[i - o->n];
            snprintf(name[i], sizeof name[i], "%s", r->name[0] ? r->name : "Heister");
            klgrd_decorate_rank(name[i], sizeof name[i], klgrd_bot_rank());
        }
        if (i < o->n) klgrd_decorate(name[i], sizeof name[i], 1, o->r[i].seat, o->r[i].seat == loc);     /* [Grades] Badge */
    }
    cdv = (end * 1024.0f - (float)frame) / 1024.0f;
    if (!(cdv >= 0)) cdv = 0;
    if (cdv > 99.0f) cdv = 99.0f;
    if (klsb_r.cd_max <= 0 || cdv > klsb_r.cd_max) klsb_r.cd_max = cdv > 0.5f ? cdv : klsb_r.cd_max;
    cdt = klsb_r.cd_max > 0 ? cdv / klsb_r.cd_max : 0.0f;
    if (cdt > 1.0f) cdt = 1.0f;
    klsb_put(KLSB_T_TITLE, px + KLSB_COLL, klu_cen(py + KLSB_Y_TITLE + 5.0f, KLU_FNT_LABEL), over ? "GAME OVER" : "ROUND OVER", KLU_C_CORAL);
    if (o->round > 0) snprintf(buf, sizeof buf, "ROUND %d OF %d", o->round, o->rounds); else snprintf(buf, sizeof buf, "ROUND OVER");
    klsb_put(KLSB_T_ROUND, px + KLSB_COLL, klu_cen(py + KLSB_Y_ROUND + 7.5f, KLU_FNT_BIG), buf, KLU_C_CHALK);
    {
        const char *rt = ""; DWORD rc = KLU_C_ORANGE;
        if (me->used) {
            if (lk == KLUV_K_ESCAPED) { rt = "YOU ESCAPED"; rc = KLU_C_GREENHI; }
            else if (lk == KLUV_K_DEAD) { rt = "YOU ARE DEAD"; rc = KLU_C_CORAL; }
            else if (lk == KLUV_K_FED) { rt = "YOU ARE A FED"; rc = KLU_C_BLUE; }
            else { rt = "LEFT BEHIND"; rc = KLU_C_ORANGE; }
        }
        klsb_put(KLSB_T_RESULT, px + KLSB_COLL, klu_cen(py + KLSB_Y_RESULT + 5.5f, KLU_FNT_NAME), rt, rc);
        if (lk == KLUV_K_DEAD && me->used) {      /* the upgraded KILLED BY line (owner 2026-10-26): the killer's heister name, YOURSELF, or THE POLICE when no seat did it */
            int k = me->killer; const struct klor_row *kr = k >= 0 ? klu_onrow(o, k) : 0; char kn[40];
            if (k == loc) snprintf(kn, sizeof kn, "YOURSELF");
            else if (kr && kr->used) { snprintf(kn, sizeof kn, "%s", kr->name[0] ? kr->name : "Player"); klor_upper(kn); }
            else if (klu_onkillai && me->ai_killer[0]) { snprintf(kn, sizeof kn, "%s", me->ai_killer); klor_upper(kn); }   /* [HUD] OnlineKilledAI */
            else snprintf(kn, sizeof kn, "THE POLICE");
            snprintf(buf, sizeof buf, "KILLED BY  %s", kn);
            klsb_put(KLSB_T_KILLED, px + KLSB_X_KILLED, klu_cen(py + KLSB_Y_RESULT + 5.5f, KLU_FNT_LABEL), buf, KLU_C_CORAL);
        }
    }
    if (klu_r.handle[KLUV_SKULL_PIC]) {
        int k;
        klsb_put(KLSB_T_LIVES, px + KLSB_COLR, klu_cen(py + KLSB_Y_LIVES + 5.0f, KLU_FNT_LABEL), "LIVES", KLU_C_CORAL);
        for (k = 0; k < KLUV_LIVES_MAX; k++)
            klu_addpic(KLUV_SKULL_PIC, px + KLSB_COLR - KLSB_SKULL_STEP * (KLUV_LIVES_MAX - k) + (KLSB_SKULL_STEP - KLSB_SKULL), py + KLSB_Y_SKULL, KLSB_SKULL, KLSB_SKULL, k < lives ? KLU_C_CHALK : 0x4cf3f0eau, klu.layer);
    }
    klsb_put(KLSB_T_HEAD(0), px + KLSB_COLL, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "DEAD MEN", KLU_C_CORAL);
    klsb_put(KLSB_T_HEAD(1), px + KLSB_COLF, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "FATE", KLU_C_CORAL);
    klsb_put(KLSB_T_HEAD(2), px + KLSB_COLR, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "PAYOUT", KLU_C_CORAL);
    if (klgrd_letter_on()) klsb_put(KLSB_T_GHEAD, px + KLSB_COLG, klu_cen(py + KLSB_Y_HEAD + 5.0f, KLU_FNT_LABEL), "GRADE", KLU_C_CORAL);
    klsb_rankup_put(px, py, loc);
    klu_addpic(klu_r.handle[111] ? 111 : 181, px + 20.0f, py + KLSB_Y_RULE, 600.0f, 4.0f, KLU_C_CHALK, klsb_ly(1));
    for (i = 0; i < nused; i++) {
        const char *fate; DWORD fc, nc, sc, f2; int dead = 0, you = 0, kind; long v = 0;
        if (i < o->n) {
            const struct klor_row *r = &o->r[i];
            f2 = klucc_hud_flags(r->flags, loc, r->seat);
            kind = klu_online_kind(f2, r->seat == loc); you = r->seat == loc; v = r->money;
            if (kind == KLUV_K_DEAD) { dead = 1; fate = "DEAD"; fc = KLU_C_DEAD; }
            else if (kind == KLUV_K_ESCAPED) { fate = "ESCAPED"; fc = KLU_C_GREENHI; }
            else if (kind == KLUV_K_FED) { fate = "FED"; fc = KLU_C_BLUE; }
            else if (kind == KLUV_K_TRAITOR) { fate = "TRAITOR"; fc = KLU_C_ORANGE; }
            else if (f2 & KLUV_F_ABOARD) { fate = "ABOARD"; fc = KLU_C_GREEN; }
            else { fate = "LEFT BEHIND"; fc = KLU_C_OUT; }
            if (dead) v = 0;
            klu_dollars(num, sizeof num, v);
        } else {
            const struct klor_row *r = &o->bot[i - o->n];
            if (!r->alive) { dead = 1; fate = "DEAD"; fc = KLU_C_DEAD; } else { fate = "AI"; fc = KLU_C_CHALK; }
            strcpy(num, "-");
        }
        rowc = py + KLSB_Y_ROW0 + pitch * row + rowh * 0.5f;
        nc = dead ? KLU_C_DEAD : you ? KLU_C_INK : KLU_C_CHALK;
        sc = dead ? KLU_C_DEADCASH : you ? KLU_C_INKCASH : KLU_C_GREENHI;
        if (you && !dead) { fc = KLU_C_INK; klu_addpic(klu_r.handle[181] ? 181 : 111, px + 8.0f, rowc - rowh * 0.5f, KLSB_PW - 16.0f, rowh, KLU_C_CHALK, klsb_ly(2)); }
        klsb_put(KLSB_T_ROW(row, 0), px + KLSB_COLL, klu_cen(rowc, KLU_FNT_NAME), name[i], nc);
        klsb_put(KLSB_T_ROW(row, 1), px + KLSB_COLF, klu_cen(rowc, KLU_FNT_LABEL), fate, fc);
        klsb_put(KLSB_T_ROW(row, 2), px + KLSB_COLR - 8.0f, klu_cen(rowc, KLU_FNT_NAME), num, sc);
        if (klgrd_letter_on() && i < o->n) {   /* [Grades] Letter: humans only (bots have no record) */
            const struct klor_row *r = &o->r[i]; struct klgrd_in gi; memset(&gi, 0, sizeof gi);
            gi.kills = r->kills; gi.police = r->police_kills; gi.loot = r->loot; gi.rewards = r->reward;
            gi.escaped = kind == KLUV_K_ESCAPED; gi.dead = dead; gi.traitor = kind == KLUV_K_TRAITOR; gi.fed = kind == KLUV_K_FED;
            klsb_grade_put(row, px, rowc, &gi);
        }
        if (dead) {
            const unsigned char *c; float w = 0;
            for (c = (const unsigned char *)name[i]; *c; c++) if ((*c & 0xc0) != 0x80) w += KLUV_NAME_CHARW;
            klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, px + KLSB_COLL - 4.0f, rowc - 1.0f, w + 8.0f, 2.0f, KLU_C_DEAD, klu.layer);
        }
        row++;
    }
    klu_addpic(klu_r.handle[KLU_DRY()] ? KLU_DRY() : 181, px + 20.0f, py + KLSB_Y_SEP, 600.0f, 3.0f, KLU_C_CHALK, klsb_ly(1));
    snprintf(num, sizeof num, "%d", me->used ? me->kills : 0);      /* the Arcade slot labelled ROUND SCORE shows KILLS online (round score is not an online value; GUESS G16) */
    klsb_put(KLSB_T_RSL, px + KLSB_X_S1, klu_cen(py + KLSB_Y_SLAB, KLU_FNT_LABEL), "KILLS", KLU_C_CORAL);
    klsb_put(KLSB_T_RSV, px + KLSB_X_S1, klu_cen(py + KLSB_Y_SVAL, KLU_FNT_NAME), num, KLU_C_GREEN);
    klsb_put(KLSB_T_RWL, px + KLSB_X_S2, klu_cen(py + KLSB_Y_SLAB, KLU_FNT_LABEL), "REWARDS", KLU_C_CORAL);
    klu_dollars(num, sizeof num, me->used ? me->reward : 0);
    klsb_put(KLSB_T_RWV, px + KLSB_X_S2, klu_cen(py + KLSB_Y_SVAL, KLU_FNT_NAME), num, KLU_C_GREEN);
    klsb_put(KLSB_T_TOTL, px + KLSB_X_S3, klu_cen(py + KLSB_Y_SLAB, KLU_FNT_LABEL), "TOTAL SCORE", KLU_C_CORAL);
    klu_dollars(num, sizeof num, me->used ? me->money : 0);
    klsb_put(KLSB_T_TOTV, px + KLSB_X_S3, klu_cen(py + KLSB_Y_STOT, KLU_FNT_BIG), num, KLU_C_GREENHI);
    {
        float cx = px + KLSB_X_RING, cy = py + KLSB_Y_RING;
        snprintf(num, sizeof num, "%d", (int)ceil(cdv - 0.001f));
        klsb_put(KLSB_T_CONTN, cx, klu_cen(cy + 5.5f, KLU_FNT_NAME), num, KLU_C_CHALK);
        klsb_put(KLSB_T_CONTL, cx, klu_cen(py + KLSB_Y_CONT, KLU_FNT_LABEL), "CONTINUE", KLU_C_CORAL);
        if (klu.wstyle && klu_r.handle[KLU_DAB_PIC]) klu_dab_at(cx, cy, 48.0f, 0x9c080809u, klsb_ly(2));
        else klu_addpic(114, cx - 24.0f, cy - 24.0f, 48.0f, 48.0f, 0x9c080809u, klsb_ly(2));
        klu_track(NULL, NULL, cx, cy, KLSB_R_RING, KLU_TRACK_C, klsb_ly(1));
        klu_arc(NULL, NULL, cx, cy, KLSB_R_RING, 0, 0.0f, cdt, KLU_C_CHALK, klu.layer);
    }
    klu_addpic_q = 0;
    return 1;
}

/* ---------------------------------------------------------------- ONLINE intro lines ([HUD] OnlineIntro=1, needs Board=1 BoardCard=1 Scoreboard=1)
 * Two centred lines under the pre-round card (klhud_board.c), in the CONTN (name font) and CONTL (label font) slots:
 *   ROUND n OF m     and     <players> PLAYERS   <minutes> MIN   YOUR HEISTER <name>
 * GUESS G14: the card's place (klbrd_place) is its centre as in Arcade; the lines sit at y0 + KLBRD_H + 34 / + 62 (not seen live).
 * GUESS G15: the intro shows in states 0x16..0x18. LIMIT: the text pool is made in states 0x17..0x19 only, so the first intro of a match may lack the lines. */
static void klsb_intro_compose(const struct klor_snap *o)
{
    float cx, y0; char a[64], b[112], nm[40]; const struct klor_row *me; int mins;
    if (!klbrd_told_place || !o->ok) return;
    cx = klbrd_place[0]; y0 = klbrd_place[1] + KLBRD_DY; nm[0] = 0;
    me = klu_onrow(o, o->local);
    if (me->used && me->name[0]) { snprintf(nm, sizeof nm, "%s", me->name); klor_upper(nm); }
    if (o->round > 0) snprintf(a, sizeof a, "ROUND %d OF %d", o->round, o->rounds); else a[0] = 0;
    mins = (int)(o->length / 60.0f + 0.5f);
    if (mins > 0 && mins < 100) snprintf(b, sizeof b, "%d PLAYERS   %d MIN%s%s", o->n + o->nbots, mins, nm[0] ? "   YOUR HEISTER " : "", nm);
    else snprintf(b, sizeof b, "%d PLAYERS%s%s", o->n + o->nbots, nm[0] ? "   YOUR HEISTER " : "", nm);
    klsb_put(KLSB_T_CONTN, cx, klu_cen(y0 + KLBRD_H + 34.0f, KLU_FNT_NAME), a, KLU_C_CHALK);
    klsb_put(KLSB_T_CONTL, cx, klu_cen(y0 + KLBRD_H + 62.0f, KLU_FNT_LABEL), b, KLU_C_CORAL);
}

/* called by klbrd_render (klhud_board.c) after the stock intro Render, inside the card branch */
static void klsb_intro_draw(void *ctx, void *cam)
{
    if (!klsb.intro || !klsb_cs_ready || !TryEnterCriticalSection(&klsb_cs)) return;
    if (klsb_r.made && klsb_r.state >= 0x16 && klsb_r.state <= 0x18 && klsb_alive()) { klsb_text(KLSB_T_CONTN, ctx, cam); klsb_text(KLSB_T_CONTL, ctx, cam); }
    LeaveCriticalSection(&klsb_cs);
}

static void klsb_apply(void)
{   /* SetText / SetColour of every text whose string or colour changed (the same discipline as klu_apply; under klsb_cs) */
    int i;
    for (i = 0; i < KLSB_NT(); i++) {
        struct klsb_t *t = &klsb_r.t[i]; DWORD vt;
        if (!t->obj) continue;
        if (!klh_rd(t->obj, &vt, 4) || vt != KLU_TEXT_VT) { klsb_r.valid = 0; klsb_r.made = 0; klog("hud: scoreboard: text %d (%08lx) no longer has ZCHAROBJ's vtable: no board this level", i, t->obj); return; }
        if (!t->on) continue;
        if (strcmp(t->want, t->cur)) {
            klu_set(t->obj, KLU_VT_TEXT, (DWORD)(DWORD_PTR)t->want);
            if (klu.log >= 2) klog("hud: scoreboard: text %d: '%s' -> '%s'", i, t->cur, t->want);
            strcpy(t->cur, t->want);
        }
        if (t->want_colour != t->colour) { klu_set(t->obj, KLU_VT_COLOUR, t->want_colour); t->colour = t->want_colour; }
    }
}

static void klsb_probe_line(DWORD osd, const struct klb_snap *s, int have)
{
    static DWORD said; static LONG lc, lu, ls, lclk; DWORD now = GetTickCount(), el, vt = 0, endb = 0, dsys; float end = 0; LONG frame = 0, c = klsb_n_call, u = klsb_n_ours, st = klsb_n_stock, clk = klu_n_call;
    if (now - said < 1000) return;
    said = now;
    el = klh_rd32(osd + KLSB_O_OUTRO); if (el) { klh_rd(el, &vt, 4); endb = klh_rd32(el + KLSB_E_DEADLINE); memcpy(&end, &endb, 4); }
    dsys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF)); if (dsys) klh_rd(dsys + 0x48, &frame, 4);
    klog("hud: scoreboard: probe: state %02lx, outro element %08lx vtable %08lx (%s), deadline %.3f s = frame %ld, engine frame %ld (%.2f s left), wrapper calls +%ld (stock +%ld, ours +%ld), the clock wrapper +%ld (draw_on %ld)",
         have ? s->state : 0, el, vt, vt == KLSB_VT ? "ZHeistOutroDisplay" : vt == (DWORD)(DWORD_PTR)&klsb_evt[1] ? "OUR private copy" : "UNKNOWN", end, (LONG)(end * 1024.0f), frame, ((double)(LONG)(end * 1024.0f) - frame) / 1024.0, c - lc, st - ls, u - lu, clk - lclk, klu_draw_on);
    if (have && kluv_ok(s) && s->human >= 0) {
        struct kluv_money m;
        if (kluv_money(s, s->human, &m))
            klog("hud: scoreboard: probe: round %d, lives %d; score+0x30 = %ld, +0x34 = %ld, +0x38 = %ld; kluv total %ld, round_now %ld, carried %ld, rewards %ld, record 0 payout %ld split %ld; state timer [rules+0x4c] = %.2f",
                 s->level, kluv_lives(s), m.round_score, m.best, m.banked, m.total, m.round_now, m.carried, m.rewards, m.payout, m.split, kluv_round_left(s));
    }
    lc = c; lu = u; ls = st; lclk = clk;
}

static void klsb_tick(int game_thread)
{
    static DWORD last, said; DWORD now = GetTickCount(), osd, el, endb = 0, sys; struct klb_snap s; int have, hon = 0, st, nowrap = 0; struct klor_snap on; LONG frame = 0;
    if (!klsb.on || !klu.on || !klh_exe_ok || !game_thread || now - last < 100) return;
    last = now;
    osd = klu_r.osd;
    if (!osd || !klu_r.made || klu_r.fault || !klu_r.elem || klh_rd32(osd) != KLU_OSD_VT) { if (klsb_r.osd) klsb_forget(); return; }
    if (osd != klsb_r.osd) { klsb_forget(); klsb_r.osd = osd; }
    if (klsb_r.refused || klsb_code_bad) return;
    if (!klu_r.pic_done) klu_pic_prep(klu_r.elem);
    /* 2026-10-27: online the outro element at osd+0x10b4 is still 0 for minutes (Q27_DM03 refused after 3 s and never drew the online card): an absent element is waited for, only a present one that will not wrap counts */
    if (!klsb_wrap(osd)) { if (klsb.ostate && klsb.online && !klsb_code_bad && !klh_rd32(osd + KLSB_O_OUTRO)) nowrap = 1; else { if (!klsb_code_bad && (!klh_rd32(osd + KLSB_O_OUTRO) || ++klsb_r.wrapfail < 30)) return; klsb_r.refused = 1; if (klu.log) klog("hud: scoreboard: the wrap failed %d tick(s) (%s): the stock panel stays for this OSD", klsb_r.wrapfail, klsb_code_bad ? "code / vtable mismatch" : "element not readable or not ZHeistOutroDisplay"); return; } }
    if (!nowrap) { klsb_r.wrapfail = 0; klsb_r.spath = 0; }
    klsb_cache_pics();
    if (klsb_r.state == 0x1f && !nowrap) klsb_cache_odesc();
    have = klb_read(&s);
    if (!have) {   /* 2026-10-26 HUD parity: ONLINE the Arcade readers refuse (no Heist score object). Not composed here (the online outro element and its data are undecoded, re\hud_online.md): log what the online round-over looks like, once per state, so the next bench decodes it. */
        static int told_state = -1; struct klb_snap o;
        if (klb_read_hud(&o) && o.online && o.state != told_state && o.state >= 0x1d) {
            DWORD el2 = klsb_r.elem ? klsb_r.elem : 0, vt2 = el2 ? klh_rd32(el2) : 0; int i;
            told_state = o.state;
            klog("hud: scoreboard: ONLINE state %02lx (the stock round-over panel stays; the Arcade board is not drawn online yet): outro element %08lx vtable %08lx (%s), %d crew rows, named %d", (DWORD)o.state, el2, vt2, vt2 == KLSB_VT ? "ZHeistOutroDisplay, same class as Arcade" : "other / not wrapped", o.on_n, o.on_named);
            for (i = 0; i < o.on_n && i < 16; i++) klog("hud: scoreboard: ONLINE row %d rec %08lx '%s' flags %08lx loot %ld rewards %ld", i, o.on_rec[i], o.on_name[i], o.on_flags[i], o.on_loot[i], o.on_rew[i]);
        }
    }
    if (!have && (klsb.online || klsb.intro)) {      /* 2026-10-26: online, from the reader; the local seat as klhud.c finds it (the player list's +0xefc) */
        DWORD pl = klh_rd32(osd + KLU_O_PLIST), li = 0; int loc = -1;
        if (pl && klh_rd(pl + 0xefc, &li, 4) && li < 16) loc = (int)li;
        klor_noev = 1; hon = klor_read(&on, loc) && on.ok; klor_noev = 0;      /* this reader never takes the kill-feed events */
    }
    st = have ? (int)s.state : hon ? (int)on.b.state : 0;
    klsb_r.state = st;
    if (klsb.probe || (klu.log >= 2 && have && s.state >= 0x1f)) klsb_probe_line(osd, &s, have);
    if (!have && !hon) { klsb_r.valid = 0; return; }
    klgrd_round_reset(st);      /* [Grades] RankUp: latch the ranks in the round (states 0x16..0x19), compare in 0x1f */
    if (have) klgrd_track(0, s.human >= 0 ? s.human : 0, 1, st);
    else { int q; klgrd_note_online(&on); for (q = 0; q < on.n; q++) klgrd_track(1, on.r[q].seat, on.r[q].seat == on.local, st); }
    if (klsb.on && !klsb_r.made && ((st >= 0x17 && st <= 0x19) || (nowrap && st == 0x1f)) && klu_r.fonts[0]) {
        EnterCriticalSection(&klsb_cs);
        klsb_r.made = klsb_make_pool();
        if (!klsb_r.made) klsb_r.refused = 1;
        LeaveCriticalSection(&klsb_cs);
        if (klsb_r.refused) return;
    }
    if (!klsb_r.made) { klsb_r.valid = 0; return; }
    if (klsb.probe) return;                                   /* log only: nothing is composed, the stock panel shows */
    if (hon && klsb.intro && st >= 0x16 && st <= 0x18) { EnterCriticalSection(&klsb_cs); klsb_intro_compose(&on); klsb_apply(); LeaveCriticalSection(&klsb_cs); }
    if (st != 0x1f) {
        if (klsb_r.valid) { EnterCriticalSection(&klsb_cs); klsb_r.valid = 0; LeaveCriticalSection(&klsb_cs); }
        if (st < 0x1f) { klsb_r.cd_max = 0; klsb_r.sset = 0; klsb_r.told_s = 0; }
        klsb_r.spath = 0;
        return;
    }
    if (!have && !klsb.online) { klsb_r.valid = 0; return; }
    el = klsb_r.elem; sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF));
    if (nowrap) {      /* OnlineBoardState: no outro element: the countdown starts at the first state-0x1f tick (GUESS G16), drawn by klsb_state_render on the clock element */
        float endf;
        if (have || !hon || !sys || !klh_rd(sys + 0x48, &frame, 4)) { klsb_r.valid = 0; klsb_r.spath = 0; return; }
        if (!klsb_r.sset) { klsb_r.sset = 1; klsb_r.sframe = frame; klsb_r.s_tick0 = now; InterlockedExchange(&klsb_n_srender, 0); InterlockedExchange(&klsb_n_sdrawn, 0); klsb_r.told_n = 0; }
        endf = (float)(klsb_r.sframe + 10 * 1024) / 1024.0f; memcpy(&endb, &endf, 4);
        klsb_r.spath = 1;
        if (!klsb_r.told_s) { klsb_r.told_s = 1; klog("hud: scoreboard: OnlineBoardState: round-end state 1f at engine frame %ld with NO outro element at osd+0x10b4: the online card is composed from the state (10 s countdown from here, GUESS) and drawn on the clock element's render (%d seats); NOT RUN IN THE GAME", (long)frame, on.n); }
        else if (!klsb_r.told_n && now - klsb_r.s_tick0 >= 3000) {
            klsb_r.told_n = 1;
            klog("hud: scoreboard: OnlineBoardState: 3 s in state 1f: clock element renders +%ld, card drawn +%ld%s", klsb_n_srender, klsb_n_sdrawn, klsb_n_srender ? (klsb_n_sdrawn ? " (shown)" : " (composed but not drawn: pictures / lock / canary)") : " (the clock element does not render in this state: G15 is wrong, the stock panel is all there is)");
        }
        EnterCriticalSection(&klsb_cs);
        klsb_r.valid = klsb_compose_online(&on, endb, frame);
        if (klsb_r.valid) klsb_apply();
        LeaveCriticalSection(&klsb_cs);
        return;
    }
    if (!el || !klh_rd(el + KLSB_E_DEADLINE, &endb, 4) || !sys || !klh_rd(sys + 0x48, &frame, 4)) { klsb_r.valid = 0; return; }
    if (klsb.test) {
        EnterCriticalSection(&klsb_cs);
        klsb_put(KLSB_T_TITLE, klsb.x + 10.0f, klsb.y + 6.0f, "LEFT AT X+10 Y+6", KLU_C_CORAL);
        klsb_put(KLSB_T_LIVES, klsb.x + KLSB_PW - 10.0f, klsb.y + 6.0f, "RIGHT AT X+630 Y+6", KLU_C_CORAL);
        klsb_put(KLSB_T_CONTN, klsb.x + KLSB_PW * 0.5f, klsb.y + 6.0f, "CENTRE AT X+320 Y+6", KLU_C_CORAL);
        klsb_apply();
        LeaveCriticalSection(&klsb_cs);
        return;
    }
    EnterCriticalSection(&klsb_cs);
    klsb_r.valid = have ? klsb_compose(&s, endb, frame) : klsb_compose_online(&on, endb, frame);
    if (klsb_r.valid) klsb_apply();
    LeaveCriticalSection(&klsb_cs);
    if (klsb_r.valid && !klsb_r.told_first) { klsb_r.told_first = 1; if (klu.log) klog("hud: scoreboard: the first snapshot of this round is ready (%d pictures); the next frames draw the board in place of the stock panel", klsb_r.npic); }
    if (klu.log >= 2 && now - said >= 5000) { said = now; klog("hud: scoreboard: %ld wrapper calls, %ld ours, %ld stock, %ld lock busy, %ld refused (no picture)", InterlockedExchange(&klsb_n_call, 0), InterlockedExchange(&klsb_n_ours, 0), InterlockedExchange(&klsb_n_stock, 0), InterlockedExchange(&klsb_n_busy, 0), InterlockedExchange(&klsb_n_refused, 0)); }
}

static void klsb_init(void)
{   /* after klu_init (klhud.c): its ini helpers and its Enable */
    if (!klu.on) return;
    klsb.on = klu_inii("Scoreboard", 0, 0, 1);
    if (!klsb.on) return;
    klsb.online = klu_inii("OnlineBoard", 0, 0, 1); klsb.ostate = klsb.online && klu_inii("OnlineBoardState", 0, 0, 1); klsb.intro = klu_inii("OnlineIntro", 0, 0, 1);
    klsb.probe = klu_inii("ScoreboardProbe", 0, 0, 1); klsb.test = klu_inii("ScoreboardTest", 0, 0, 1); klsb.fault = klu_inii("ScoreboardFault", 0, 0, 1);
    klsb.rows12 = klu_inii("Rows12", 1, 0, 1); klsb.textonly = klu_inii("ScoreboardTextOnly", 0, 0, 1); klsb.total = klu_inii("ScoreboardTotal", 1, 0, 2); klsb.count = klu_inii("ScoreboardCount", 0, 0, 1); klsb.lead = klu_inii("ScoreboardShopLead", 30, 0, 100);   /* tenths of a second cut off the 10 s countdown: the shop opens at 7 (owner 2026-10-25) */
    klsb.alpha = klu_inii("ScoreboardAlpha", 230, 0, 255);
    klsb.x = klu_inif("ScoreboardX", "320"); klsb.y = klu_inif("ScoreboardY", "150");
    if (!(klsb.x >= 0 && klsb.x <= 640)) klsb.x = KLSB_PX;
    if (!(klsb.y >= 0 && klsb.y <= 320)) klsb.y = KLSB_PY;
    if (!klu.fontset) { klog("hud: scoreboard: needs the level's baked fonts ([HUD] Fonts=1 or Draft=1): off"); klsb.on = 0; return; }
    InitializeCriticalSection(&klsb_cs); klsb_cs_ready = 1;
    klog("hud: scoreboard: on (Scoreboard=1 Probe=%d Test=%d Fault=%d TextOnly=%d Total=%d Count=%d Alpha=%d at %.0f,%.0f); ZHeistOutroDisplay [osd+0x10b4] (OnlineBoardState=%d: without it, from the state), state 0x1f only, every failure = the stock panel; NOT RUN IN THE GAME",
         klsb.probe, klsb.test, klsb.fault, klsb.textonly, klsb.total, klsb.count, klsb.alpha, klsb.x, klsb.y, klsb.ostate);
}

#endif /* KLHUD_BOARD2_C */
