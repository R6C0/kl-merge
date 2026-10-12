/* klsb_test.c - OFF-GAME check of klhud_board2.c (the round-over scoreboard). Proves the file's own logic and guards on made-up memory; nothing about the game.
 *   cl /nologo /W4 /D_CRT_SECURE_NO_WARNINGS klsb_test.c            (32-bit: vcvarsall x86; run it from the klhook folder)
 *   klsb_test.exe [dump folder]     writes <folder>\board_<case>.txt for tools\kl_hud.py preview-board (the layout the C code composed: one line a text, one a picture)
 * It includes the REAL klhud_values.c, klhud.c (and so klhud_weapon.c) and klhud_board2.c; the game's routines are stubs that record their arguments.
 * Cases: (1) zeroed / garbage memory: compose and the render slot take the stock branch; (2) every guard of the render slot one by one; (3) three made-up rounds
 * (escaped / dead with 'killed by' / traitor) composed and drawn: counts, strings, colours and places. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

/* ---------------------------------------------------------------- the host stubs */
static int klh_rd(DWORD_PTR p, void *out, SIZE_T n)
{
    MEMORY_BASIC_INFORMATION mbi;
    if (p < 0x10000 || !VirtualQuery((void *)p, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return 0;
    memcpy(out, (void *)p, n); return 1;
}
static DWORD klh_rd32(DWORD_PTR p) { DWORD v = 0; klh_rd(p, &v, 4); return v; }
static int klh_rdstr(DWORD_PTR p, char *out, int cap) { out[0] = 0; if (!p) return 0; strncpy(out, (const char *)p, (size_t)cap - 1); out[cap - 1] = 0; return (int)strlen(out); }
static char klh_ini[MAX_PATH] = "nonexistent.ini";
static int klh_exe_ok = 1;
static LONG_PTR klh_delta;
static int kllog_on;
static void klog(const char *fmt, ...) { va_list a; va_start(a, fmt); if (kllog_on) { vprintf(fmt, a); printf("\n"); } va_end(a); }
static int klh_data(void *at, const void *bytes, int len, const char *what) { (void)what; memcpy(at, bytes, (size_t)len); return 1; }
static int klh_kind(const void *p, int n, char *sec) { (void)p; (void)n; strcpy(sec, ".rdata"); return 'r'; }
static int klh_scene(char *out, int cap) { (void)cap; out[0] = 0; return 0; }
static int klx_on;
static int klx_level_verdict(const char *scene, char *why) { (void)scene; why[0] = 0; return 2; }
#define KL2_GAMEDATA 0xdd265cu
#define KL2_SYSIF    0xdd2640u
static int klnm_name(DWORD at, char *out, int cap) { (void)at; (void)out; (void)cap; return 0; }

#define KLB_NREC 32
#define KLB_NLEVEL 11
struct klb_rec { int used; DWORD at, actor, money; BYTE status, stage, flags; float hit; };
struct klb_snap { DWORD rules, score, state, vehicle; int n, level, human; BYTE veh; float timer; struct klb_rec r[KLB_NREC]; };
static int klb_read(struct klb_snap *s) { memset(s, 0, sizeof *s); s->human = -1; return 0; }

/* the game's routines (called through KLH_VA) */
static int stock_calls, text_draws, chunk_draws, last_draw_n;
static float last_text_xy[2];
struct fobj { DWORD vt; DWORD colour; DWORD style; DWORD font; DWORD layer; char text[64]; };
static struct fobj pool_objs[400]; static int pool_n;
static void __fastcall st_text(void *o, void *edx, DWORD v) { (void)edx; strncpy(((struct fobj *)o)->text, (const char *)(DWORD_PTR)v, 63); }
static void __fastcall st_colour(void *o, void *edx, DWORD v) { (void)edx; ((struct fobj *)o)->colour = v; }
static void __fastcall st_style(void *o, void *edx, DWORD v) { (void)edx; ((struct fobj *)o)->style = v; }
static void __fastcall st_font(void *o, void *edx, DWORD v) { (void)edx; ((struct fobj *)o)->font = v; }
static void __fastcall st_layer(void *o, void *edx, DWORD v) { (void)edx; ((struct fobj *)o)->layer = v; }
static void __fastcall st_draw(void *o, void *edx, void *ctx, void *cam, const float *xf, const float *pos) { (void)o; (void)edx; (void)ctx; (void)cam; (void)xf; text_draws++; last_text_xy[0] = pos[0]; last_text_xy[1] = pos[1]; }
static DWORD __fastcall st_create(void *tmpl, void *edx, DWORD parent, DWORD tag, DWORD a, DWORD b, DWORD c, DWORD d)
{ struct fobj *o = &pool_objs[pool_n++]; (void)tmpl; (void)edx; (void)parent; (void)tag; (void)a; (void)b; (void)c; (void)d; memset(o, 0, sizeof *o); o->vt = 0x00bab45cu; return (DWORD)(DWORD_PTR)o; }
static void __fastcall st_place(void *T, void *edx, float *out, float *in) { (void)T; (void)edx; out[0] = in[0]; out[1] = in[1]; out[2] = 0; }
static struct { DWORD handle; DWORD argb; float x, y, w, h; DWORD layer; } chunk_log[512];
static DWORD __fastcall st_chunk(void *ctx, void *edx, DWORD handle, DWORD *desc, float *xform, float *out, DWORD layer, DWORD one, DWORD zero)
{
    const float *rec = (const float *)(DWORD_PTR)desc[2]; (void)ctx; (void)edx; (void)xform; (void)one; (void)zero;
    if (chunk_draws < 512) { chunk_log[chunk_draws].handle = handle; memcpy(&chunk_log[chunk_draws].argb, &rec[9], 4); chunk_log[chunk_draws].x = out[0]; chunk_log[chunk_draws].y = out[1]; chunk_log[chunk_draws].w = rec[7]; chunk_log[chunk_draws].h = rec[8]; chunk_log[chunk_draws].layer = layer; }
    chunk_draws++; return 0;
}
static char __fastcall st_stock_render(void *el, void *edx, void *ctx, void *cam) { (void)el; (void)edx; (void)ctx; (void)cam; stock_calls++; return 7; }

static DWORD fake_vt[0x300 / 4];                       /* ZCHAROBJ's vtable: the slots klu_set / klu_make_obj read */
static DWORD fake_sysptr, fake_sys[0x60 / 4];
static DWORD fake_ctxvt_slot;
static BYTE *kh_va(DWORD va)
{
    if (va >= 0x00bab45cu && va < 0x00bab45cu + 0x300) return (BYTE *)&fake_vt[(va - 0x00bab45cu) / 4];
    switch (va) {
    case 0x00dd2640u: return (BYTE *)&fake_sysptr;
    case 0x00842d00u: return (BYTE *)(DWORD_PTR)st_chunk;
    case 0x005a3e90u: return (BYTE *)(DWORD_PTR)st_place;
    case 0x00577e70u: return (BYTE *)(DWORD_PTR)st_stock_render;
    case 0x005a6d40u: return (BYTE *)(DWORD_PTR)st_draw;
    case 0x00817810u: return (BYTE *)(DWORD_PTR)st_create;
    default: return (BYTE *)(DWORD_PTR)va;
    }
}
#define KLH_VA(x) kh_va((DWORD)(x))

/* stubs of the files klhud.c expects around it */
static void klht_render(void *el, void *ctx, void *cam) { (void)el; (void)ctx; (void)cam; }
struct klb_snap;
static void klht_tick(DWORD osd, const struct klb_snap *s, int show) { (void)osd; (void)s; (void)show; }
static void klht_init(void) {}
static void klht_reset(void) {}

#include "klhud_values.c"
#include "klhud.c"
#include "klhud_board2.c"

/* ---------------------------------------------------------------- made-up game memory */
static BYTE rules_mem[0x1000], recs_mem[8 * 0x7c], score_pad[0x40];
#define SC (rules_mem + 0x36c)
static void w32(BYTE *p, DWORD v) { memcpy(p, &v, 4); }
static const char *names[8] = { "R6KXO", "TOMMY", "PIERRE", "LIAM", "JEAN", "ELWOOD", "BUD", "MITCHEL" };
static DWORD name_blk[8][4];

static void setup_round(struct klb_snap *s, int nrec)
{
    int i;
    memset(rules_mem, 0, sizeof rules_mem); memset(recs_mem, 0, sizeof recs_mem); (void)score_pad;
    memset(s, 0, sizeof *s);
    s->rules = (DWORD)(DWORD_PTR)rules_mem; s->score = (DWORD)(DWORD_PTR)SC; s->n = nrec; s->human = 0; s->state = 0x1f; s->level = 1;
    w32(SC, KLUV_SCORE_VT);
    for (i = 0; i < nrec; i++) {
        s->r[i].used = 1; s->r[i].at = (DWORD)(DWORD_PTR)(recs_mem + 0x7c * i); s->r[i].flags = (BYTE)(i ? 1 : 0);
        name_blk[i][2] = (DWORD)(DWORD_PTR)names[i]; w32(recs_mem + 0x7c * i, (DWORD)(DWORD_PTR)name_blk[i]);
    }
    SC[0x44] = 10; SC[0x45] = 1; SC[0x6c] = 2;
}
static void set_flags(int i, DWORD f) { w32(SC + 0x1d4 + 4 * i, f); }

static void reset_counters(void) { stock_calls = text_draws = chunk_draws = 0; }
static void dump_case(const char *dir, const char *name)
{
    char path[MAX_PATH]; FILE *f; int i;
    if (!dir) return;
    snprintf(path, sizeof path, "%s\\board_%s.txt", dir, name);
    if (!(f = fopen(path, "w"))) return;
    fprintf(f, "# klsb_test: the layout klhud_board2.c composed (case %s); T idx x y fnt align colour 'text' | P slot x y w h argb layer\n", name);
    for (i = 0; i < KLSB_NTEXT; i++) if (klsb_r.t[i].on) fprintf(f, "T %d %.1f %.1f %d %d %08lx '%s'\n", i, klsb_r.t[i].x, klsb_r.t[i].y, klsb_role[i].fnt, klsb_role[i].align, klsb_r.t[i].want_colour, klsb_r.t[i].want);
    for (i = 0; i < klsb_r.npic; i++) fprintf(f, "P %d %.1f %.1f %.1f %.1f %08lx %d\n", klsb_r.pic[i].n, klsb_r.pic[i].x, klsb_r.pic[i].y, klsb_r.pic[i].w, klsb_r.pic[i].h, klsb_r.pic[i].argb, klsb_r.pic[i].layer);
    fclose(f);
}
static const struct klsb_t *tx(int i) { return &klsb_r.t[i]; }

static DWORD osd_mem[0x1200 / 4], el_mem[0x100 / 4], ctx_mem[8];
static HANDLE hold_ev, hold_go;
static DWORD WINAPI holdfn(LPVOID p) { (void)p; EnterCriticalSection(&klsb_cs); SetEvent(hold_ev); WaitForSingleObject(hold_go, 5000); LeaveCriticalSection(&klsb_cs); return 0; }

int main(int argc, char **argv)
{
    struct klb_snap s; int i, ok; DWORD endb; float end = 10.24f; char *dumpdir = argc > 1 ? argv[1] : 0;
    /* the game's vtable of text objects: the slots the hook calls */
    fake_vt[0x20c / 4] = (DWORD)(DWORD_PTR)st_colour; fake_vt[0x220 / 4] = (DWORD)(DWORD_PTR)st_style; fake_vt[0x234 / 4] = (DWORD)(DWORD_PTR)st_layer;
    fake_vt[0x23c / 4] = (DWORD)(DWORD_PTR)st_font; fake_vt[0x244 / 4] = (DWORD)(DWORD_PTR)st_text; fake_vt[0x1e8 / 4] = (DWORD)(DWORD_PTR)st_draw; fake_vt[0x19c / 4] = (DWORD)(DWORD_PTR)st_create;
    fake_sysptr = (DWORD)(DWORD_PTR)fake_sys;
    klu.on = 1; klu.fontset = 1; klu.anchor = 1; klu.layer = 13; klu.log = 0; klu.left = 0x11;
    klu.cap[0] = 11; klu.cap[1] = 15; klu.cap[2] = 10; klu.cap[3] = 10;
    klsb.on = 1; klsb.alpha = 230; klsb.x = KLSB_PX; klsb.y = KLSB_PY; klsb.total = 1; klsb.count = 0;
    InitializeCriticalSection(&klsb_cs); klsb_cs_ready = 1;
    for (i = 0; i < 200; i++) klu_r.handle[i] = 0;
    { static const int have[] = { 111, 112, 113, 114, 115, 123, 124, 125, 178, 181 }; for (i = 0; i < 10; i++) klu_r.handle[have[i]] = 0x1000u + (DWORD)have[i]; }
    klu_r.tmpl = 0x1234; klu_r.parent = 0x5678; for (i = 0; i < KLU_NFONT; i++) klu_r.fonts[i] = 0x9000u + (DWORD)i;

    /* (1) the reader / compose guards on zeroed and garbage memory */
    setup_round(&s, 4);
    memset(rules_mem, 0, sizeof rules_mem);                                           /* score vtable gone: kluv_ok fails */
    endb = 0; memcpy(&endb, &end, 4);
    CHECK(klsb_compose(&s, endb, 0) == 0);
    memset(&s, 0, sizeof s);
    CHECK(klsb_compose(&s, endb, 0) == 0);
    { BYTE junk[0x1000]; for (i = 0; i < 0x1000; i++) junk[i] = (BYTE)(i * 131 + 7); s.rules = (DWORD)(DWORD_PTR)junk; s.score = (DWORD)(DWORD_PTR)(junk + 0x36c); s.n = 4; s.human = 0; s.r[0].used = 1; s.r[0].at = (DWORD)(DWORD_PTR)junk;
      CHECK(klsb_compose(&s, endb, 0) == 0); }                                         /* garbage: no score vtable */
    s.rules = s.score = 0; s.r[0].at = 0xdeadbeef; CHECK(klsb_compose(&s, endb, 0) == 0);      /* wild pointers */
    klsb.fault = 1; setup_round(&s, 4); set_flags(0, KLUV_F_ESCAPED); CHECK(klsb_compose(&s, endb, 0) == 0); klsb.fault = 0;      /* ScoreboardFault */

    /* the pool */
    CHECK(klsb_make_pool() == 1 && pool_n == KLSB_NTEXT);
    for (i = 0; i < KLSB_NTEXT; i++) CHECK(klsb_r.t[i].obj != 0);
    CHECK(klsb_r.t[KLSB_T_ROUND].obj && pool_objs[1].font == klu_r.fonts[KLU_FNT_BIG] && pool_objs[0].font == klu_r.fonts[KLU_FNT_LABEL] && pool_objs[2].font == klu_r.fonts[KLU_FNT_NAME]);
    CHECK(pool_objs[4].style == (DWORD)KLU_STYLE_RIGHT && pool_objs[39].style == (DWORD)KLU_STYLE_CENTRE && pool_objs[0].style == (DWORD)klu.left);
    klsb_r.made = 1;

    /* pictures: cache by hand (the clock element's description) */
    klsb_r.T = (DWORD)(DWORD_PTR)&osd_mem[0x100]; { float *t = (float *)(DWORD_PTR)(klsb_r.T + 0xc); t[0] = 0.78125f; t[1] = 0.78125f; }
    klsb_r.tbl = 0x4000; klsb_r.desc[0] = 1; klsb_r.pics_cached = 1;
    klsb_r.osd = (DWORD)(DWORD_PTR)osd_mem; osd_mem[0] = KLU_OSD_VT;
    klsb_r.elem = (DWORD)(DWORD_PTR)el_mem; el_mem[0] = KLSB_VT; el_mem[2] = klsb_r.tbl; el_mem[3] = klsb_r.T;
    memcpy((BYTE *)el_mem + KLSB_E_DEADLINE, &end, 4);
    ctx_mem[0] = KLU_CTX_VT;
    fake_sys[0x48 / 4] = 1000;                                                       /* engine frame; the deadline is 10.24 s = frame 10485 */

    /* (3a) a round everybody escaped from */
    setup_round(&s, 4);
    set_flags(0, KLUV_F_ESCAPED); set_flags(1, KLUV_F_ESCAPED); set_flags(2, KLUV_F_ESCAPED); set_flags(3, KLUV_F_ESCAPED);
    w32(SC + 0x30, 707778); w32(SC + 0x38, 707778); w32(recs_mem + 0x2c, 707778); w32(recs_mem + 0x7c + 0x2c, 120000); w32(SC + 0x184, 0);
    CHECK(klsb_compose(&s, endb, 1000) == 1);
    CHECK(!strcmp(tx(KLSB_T_TITLE)->want, "ROUND OVER") && !strcmp(tx(KLSB_T_ROUND)->want, "ROUND 1") && !strcmp(tx(KLSB_T_RESULT)->want, "EVERYBODY ESCAPED"));
    CHECK(tx(KLSB_T_RESULT)->want_colour == KLU_C_GREENHI && !tx(KLSB_T_KILLED)->on);
    CHECK(!strcmp(tx(KLSB_T_ROW(0, 0))->want, "R6KXO") && !strcmp(tx(KLSB_T_ROW(0, 1))->want, "ESCAPED") && !strcmp(tx(KLSB_T_ROW(0, 2))->want, "$707,778"));
    CHECK(!strcmp(tx(KLSB_T_ROW(1, 2))->want, "$120,000") && !tx(KLSB_T_ROW(4, 0))->on);
    CHECK(!strcmp(tx(KLSB_T_RSV)->want, "$707,778") && !strcmp(tx(KLSB_T_TOTV)->want, "$707,778") && !strcmp(tx(KLSB_T_CONTN)->want, "10"));
    CHECK(tx(KLSB_T_ROW(0, 0))->want_colour == KLU_C_INK);                           /* your row: ink on the chalk block */
    CHECK(klsb_r.npic >= 15 && klsb_r.npic <= KLSB_NPIC && klsb_r.pic[0].n == 181 && klsb_r.pic[0].w == 640.0f && klsb_r.pic[0].h == 372.0f && (klsb_r.pic[0].argb >> 24) == 230);
    CHECK(klu_addpic_q == 0);                                                         /* the redirect is always cleared */
    CHECK(klu_r.npic == 0);                                                           /* the HUD's own queue was not touched */
    dump_case(dumpdir, "escaped");
    klsb_apply();
    CHECK(!strcmp(pool_objs[1].text, "ROUND 1") && pool_objs[0].colour == KLU_C_CORAL);

    /* (2) the render slot: every guard in turn (the good case first) */
    klsb_r.valid = 1; klsb_r.state = 0x1f;
    reset_counters(); ok = (int)(signed char)klsb_render(el_mem, 0, ctx_mem, 0);
    CHECK(ok == 1 && stock_calls == 0 && klsb_n_ours == 1 && text_draws > 20 && chunk_draws == klsb_r.npic);
    reset_counters(); klsb_r.valid = 0; ok = klsb_render(el_mem, 0, ctx_mem, 0); CHECK(ok == 7 && stock_calls == 1 && text_draws == 0 && chunk_draws == 0); klsb_r.valid = 1;
    reset_counters(); klsb_r.state = 0x20; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); klsb_r.state = 0x1f;
    reset_counters(); fake_sys[0x48 / 4] = 10486; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); fake_sys[0x48 / 4] = 1000;      /* deadline passed */
    {   /* review B1 (re\hud_cloud_review.md): a round over after 32 min of game clock - the deadline is 1963.1 units, over the old bound of 1000. NOT BUILT, NOT RUN */
        float late = (2000000.0f + 10240.0f) / 1024.0f;
        reset_counters(); memcpy((BYTE *)el_mem + KLSB_E_DEADLINE, &late, 4); fake_sys[0x48 / 4] = 2000000;
        klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 0 && chunk_draws == klsb_r.npic);
        fake_sys[0x48 / 4] = 2010241; reset_counters(); klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0);     /* and it still passes */
        fake_sys[0x48 / 4] = 1000; memcpy((BYTE *)el_mem + KLSB_E_DEADLINE, &end, 4);
    }
    reset_counters(); { float z = -1.0f; memcpy((BYTE *)el_mem + KLSB_E_DEADLINE, &z, 4); } klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); memcpy((BYTE *)el_mem + KLSB_E_DEADLINE, &end, 4);
    reset_counters(); klsb_r.pics_cached = 0; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0 && text_draws == 0); klsb_r.pics_cached = 1;      /* no picture: stock (TextOnly=0) */
    reset_counters(); klsb.textonly = 1; klsb_r.pics_cached = 0; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 0 && chunk_draws == 0 && text_draws > 20); klsb.textonly = 0; klsb_r.pics_cached = 1;
    reset_counters(); el_mem[3] = 0x1111; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); el_mem[3] = klsb_r.T;                  /* another transform than the clock's */
    reset_counters(); el_mem[2] = 0x2222; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); el_mem[2] = klsb_r.tbl;                  /* another picture table */
    reset_counters(); { DWORD o = osd_mem[0]; osd_mem[0] = 0; klsb_render(el_mem, 0, ctx_mem, 0); osd_mem[0] = o; } CHECK(stock_calls == 1 && chunk_draws == 0);            /* the OSD canary */
    reset_counters(); { DWORD o = pool_objs[0].vt; pool_objs[0].vt = 0; klsb_render(el_mem, 0, ctx_mem, 0); pool_objs[0].vt = o; } CHECK(stock_calls == 1 && chunk_draws == 0);   /* the text canary */
    reset_counters(); ctx_mem[0] = 0; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); ctx_mem[0] = KLU_CTX_VT;                    /* not a ZDrawBufferSimple */
    reset_counters(); { DWORD_PTR e2 = klsb_r.elem; klsb_r.elem = 0; klsb_render(el_mem, 0, ctx_mem, 0); klsb_r.elem = e2; } CHECK(stock_calls == 1 && chunk_draws == 0);      /* not the wrapped element */
    reset_counters(); klsb.probe = 1; klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0); klsb.probe = 0;                                     /* ScoreboardProbe = log only */
    { /* a busy lock (another thread holds it): the stock panel that frame, never a wait */
        HANDLE th; LONG b0 = klsb_n_busy;
        hold_ev = CreateEventA(0, 1, 0, 0); hold_go = CreateEventA(0, 1, 0, 0);
        th = CreateThread(0, 0, holdfn, 0, 0, 0); WaitForSingleObject(hold_ev, 5000);
        reset_counters(); klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0 && klsb_n_busy == b0 + 1);
        SetEvent(hold_go); WaitForSingleObject(th, 5000); CloseHandle(th);
    }
    reset_counters(); ok = (int)(signed char)klsb_render(el_mem, 0, ctx_mem, 0); CHECK(ok == 1 && stock_calls == 0);                                                    /* and the good case again */

    /* (3b) a round the human died in, killed by crew index 2 (PIERRE), a traitor among the crew */
    setup_round(&s, 6);
    set_flags(0, KLUV_F_DEAD); set_flags(1, KLUV_F_ESCAPED); set_flags(2, KLUV_F_TRAITOR); set_flags(3, KLUV_F_DEAD); set_flags(4, 0); set_flags(5, KLUV_F_ESCAPED);
    SC[0x6c] = 1; SC[0x10c] = 2; SC[0x45] = 3; w32(SC + 0x30, 250000); w32(SC + 0x38, 650000); w32(SC + 0x184 + 4, (DWORD)-25000);
    w32(recs_mem + 0x7c + 0x2c, 90000); w32(recs_mem + 5 * 0x7c + 0x2c, 160000);
    CHECK(klsb_compose(&s, endb, 1000) == 1);
    CHECK(!strcmp(tx(KLSB_T_RESULT)->want, "YOU ARE DEAD") && tx(KLSB_T_RESULT)->want_colour == KLU_C_CORAL && !strcmp(tx(KLSB_T_KILLED)->want, "KILLED BY  PIERRE"));
    CHECK(!strcmp(tx(KLSB_T_ROW(0, 1))->want, "DEAD") && tx(KLSB_T_ROW(0, 0))->want_colour == KLU_C_DEAD && !strcmp(tx(KLSB_T_ROW(0, 2))->want, "$0"));
    CHECK(!strcmp(tx(KLSB_T_ROW(2, 1))->want, "TRAITOR") && tx(KLSB_T_ROW(2, 0))->want_colour == KLU_C_INK);       /* alive traitor: orange block, ink */
    CHECK(!strcmp(tx(KLSB_T_ROW(4, 1))->want, "LEFT BEHIND") && !strcmp(tx(KLSB_T_ROW(5, 2))->want, "$160,000"));
    CHECK(!strcmp(tx(KLSB_T_TOTV)->want, "$650,000") && !strcmp(tx(KLSB_T_ROUND)->want, "ROUND 3"));            /* Total=1 (default, review M1): +0x38 alone = rounds before + this one */
    klsb.total = 0; klsb_compose(&s, endb, 1000); CHECK(!strcmp(tx(KLSB_T_TOTV)->want, "$900,000")); klsb.total = 1; klsb_compose(&s, endb, 1000);
    CHECK(!strcmp(tx(KLSB_T_RWV)->want, "$0"));                                         /* rewards of the human (index 0) */
    dump_case(dumpdir, "dead");

    /* (3c) YOU are the traitor and escaped; the game over title when no life is left */
    setup_round(&s, 5);
    set_flags(0, KLUV_F_ESCAPED | KLUV_F_TRAITOR); set_flags(1, KLUV_F_DEAD); set_flags(2, KLUV_F_DEAD); set_flags(3, KLUV_F_ESCAPED); set_flags(4, KLUV_F_DEAD);
    SC[0x6c] = 0; SC[0x45] = 2; w32(SC + 0x30, 880000); w32(SC + 0x38, 1587778); w32(SC + 0x184, (DWORD)-25000); w32(recs_mem + 0x2c, 880000); w32(recs_mem + 3 * 0x7c + 0x2c, 40000);
    CHECK(klsb_compose(&s, endb, 1000) == 1);
    CHECK(!strcmp(tx(KLSB_T_TITLE)->want, "GAME OVER") && !strcmp(tx(KLSB_T_RESULT)->want, "YOU ESCAPED") && !tx(KLSB_T_KILLED)->on);
    CHECK(!strcmp(tx(KLSB_T_ROW(0, 1))->want, "TRAITOR OUT") && tx(KLSB_T_ROW(0, 1))->want_colour == KLU_C_INK && !strcmp(tx(KLSB_T_RWV)->want, "-$25,000") && tx(KLSB_T_RWV)->want_colour == KLU_C_CORAL);
    CHECK(!strcmp(tx(KLSB_T_TOTV)->want, "$1,587,778"));
    dump_case(dumpdir, "traitor");

    /* (4) a level without the skull picture: 'LIVES n' as text; without 111: 181 */
    klu_r.handle[178] = 0; klsb_compose(&s, endb, 1000); CHECK(!strcmp(tx(KLSB_T_LIVES)->want, "LIVES 0")); klu_r.handle[178] = 0x1000u + 178;
    klu_r.handle[181] = 0; klsb_compose(&s, endb, 1000); CHECK(klsb_r.pic[0].n == 111); klu_r.handle[181] = 0x1000u + 181;

    /* (5) the queue never overflows */
    CHECK(klsb_r.npic <= KLSB_NPIC);
    /* (6) a forgotten state: everything dropped, the render takes the stock branch */
    klsb_forget(); reset_counters(); klsb_render(el_mem, 0, ctx_mem, 0); CHECK(stock_calls == 1 && chunk_draws == 0 && klsb_r.elem == 0);

    printf("%d checks, %d failed\n", checks, fails);
    return fails != 0;
}
