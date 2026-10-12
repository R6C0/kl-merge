/* klwatch_test.c - OFF-GAME check of the WATCH LOOK in klhud.c (klu_watch_look, klu_escape_look; 2026-10-12, cloud session).
 * Dumps every picture the hook queues for a set of round times so that tools/kl_hud_watch_check.py can compare them, number for
 * number, with tools/kl_hud_watch.py (the model the previews were judged on) and render them with the baked textures; `sweep`
 * prints the worst picture count over a whole round. Host stubs: the same as klsb_test.c (copied). NOT the game.
 *   MSVC:  cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klwatch_test.c          Linux: tools/run_harness_linux.sh klwatch_test
 *   klwatch_test.exe [sweep] > watch_c.txt                                        */
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

int main(int argc, char **argv)
{
    static const float clocks[] = { 360.0f, 330.0f, 219.0f, 130.0f, 61.0f, 60.0f, 59.5f, 40.0f, 5.0f, 0.4f };
    static const float lefts[] = { 1.0f, 0.65f, 0.35f, 0.0f };
    static const int have[] = { 111, 112, 113, 114, 115, 123, 124, 125, 126, 170, 171, 181, 185, 190 };
    int c, i, k;
    klu.wstyle = 1; klu.wwear = 1; klu.wseconds = 0; klu.layer = 13;
    for (i = 0; i < (int)(sizeof have / sizeof have[0]); i++) klu_r.handle[have[i]] = 0x1000u + (DWORD)have[i];
    if (argc > 1 && !strcmp(argv[1], "sweep")) {
        int worst[2] = { 0, 0 }; float at[2] = { 0, 0 }, t;
        for (k = 0; k < 2; k++) { klu.wseconds = k; for (t = 360.0f; t > 0.05f; t -= 0.1f) { klu_r.npic = 0; klu_watch_look(1212.0f, 66.0f, t); if (klu_r.npic > worst[k]) { worst[k] = klu_r.npic; at[k] = t; } } }
        printf("watch worst: %d pictures at %.1f s (WatchSeconds=0); %d at %.1f s (WatchSeconds=1)\n", worst[0], at[0], worst[1], at[1]);
        worst[0] = 0; for (t = 1.0f; t >= 0.0f; t -= 0.001f) { klu_r.npic = 0; klu_escape_look(1150.0f, 66.0f, t, 170); if (klu_r.npic > worst[0]) { worst[0] = klu_r.npic; at[0] = t; } }
        printf("escape worst: %d pictures at left %.3f\n", worst[0], at[0]);
        return 0;
    }
    for (k = 0; k < 2; k++) {
        klu.wseconds = k;
        for (c = 0; c < (int)(sizeof clocks / sizeof clocks[0]); c++) {
            klu_r.npic = 0; klu_watch_look(1212.0f, 66.0f, clocks[c]);
            printf("CASE watch %d %.2f %d\n", k, clocks[c], klu_r.npic);
            for (i = 0; i < klu_r.npic; i++) printf("P %d %.3f %.3f %.3f %.3f %08lx %d\n", klu_r.pic[i].n, klu_r.pic[i].x, klu_r.pic[i].y, klu_r.pic[i].w, klu_r.pic[i].h, (unsigned long)klu_r.pic[i].argb, klu_r.pic[i].layer);
        }
    }
    klu.wseconds = 0;
    for (c = 0; c < 4; c++) {
        klu_r.npic = 0; klu_escape_look(1150.0f, 66.0f, lefts[c], 170);
        printf("CASE escape 0 %.2f %d\n", lefts[c], klu_r.npic);
        for (i = 0; i < klu_r.npic; i++) printf("P %d %.3f %.3f %.3f %.3f %08lx %d\n", klu_r.pic[i].n, klu_r.pic[i].x, klu_r.pic[i].y, klu_r.pic[i].w, klu_r.pic[i].h, (unsigned long)klu_r.pic[i].argb, klu_r.pic[i].layer);
    }
    return 0;
}
