/*
 * klhud_harness_online.h - the ONLINE side of klbot.c / klonline_read.c as the OFF-GAME HUD harnesses see it
 * (klsb_test.c, klwatch_test.c). Harness only: never part of the DLL.
 *
 * klhud.c and klhud_board2.c read the online snapshot (klbot.c's struct klb_snap on_* arrays, 2026-10-18..26) and the online round
 * reader (klonline_read.c: klor_read, klor_bots_sorted, the klor_noev / klor_aikill flags). The harnesses used to carry their own copy of
 * struct klb_snap (the Arcade part only) and no klor_* at all, so they stopped compiling when the online port landed (noted 2026-10-27
 * 02:00: 'klsb_test.c was already uncompilable at HEAD (online structs not stubbed)'). This header is the one place the layout lives:
 *   - struct klb_rec / struct klb_snap: klbot.c's, every field (keep in step with klbot.c:334; the harness only zeroes them).
 *   - klonline_read.h: the REAL pure part (struct klor_snap / klor_row, klor_upper, klor_loot_share, ...).
 *   - klor_read / klor_bots_sorted: stubs that answer 'no online round' (0 rows), as klonline_read.c does with [Online] Read=0.
 * Include it where the old 'struct klb_snap { ... }' line stood, after klh_rd / klh_rd32 / klog are defined.
 */
#ifndef KLHUD_HARNESS_ONLINE_H
#define KLHUD_HARNESS_ONLINE_H

#define KLB_NREC 32
#define KLB_NLEVEL 11
struct klb_rec { int used; DWORD at, actor, money; BYTE status, stage, flags; float hit; };
struct klb_snap {                                     /* = klbot.c's struct klb_snap (2026-10-27) */
    DWORD rules, score, state, vehicle; int n, level, human; BYTE veh; float timer;
    struct klb_rec r[KLB_NREC];
    long on_money[16]; BYTE on_used[16]; int on_local;
    DWORD on_flags[16], on_rec[16]; long on_loot[16], on_rew[16]; char on_name[16][32]; int on_named;
    DWORD on_recs, on_free, on_score; int on_n;
    int online;
};
static int klb_read(struct klb_snap *s) { memset(s, 0, sizeof *s); s->human = -1; return 0; }
static int klb_hud_online, klb_hud_crew;              /* klbot.c: set by klhud.c from [HUD] Online / OnlineCrew */
static int klb_online_session(void) { return 0; }    /* klbot.c: net role host / client with game type 4 - never in the harness */
static int klb_read_hud(struct klb_snap *s)            /* klbot.c's: klb_read, else an online snapshot - the harness has no online session, so 'nothing' as klbot.c answers then */
{ if (klb_read(s)) return 1; memset(s, 0, sizeof *s); s->human = -1; return 0; }

#include "klucchide_logic.h"                           /* [UccHide]'s pure part: klucc_hud_flags (klhud.c's online crew rows), as klhook.c includes it before klhud_values.c */
#include "klonline_read.h"                            /* the pure part: structs and the small decisions, unchanged */

static int klor_on;                                   /* klonline_read.c: [Online] Read (default 0) */
static int klor_noev;                                 /* klonline_read.c: a reader that is not the kill feed leaves the event queue alone */
static int klor_aikill;                               /* klonline_read.c: [HUD] OnlineKilledAI */
static int klor_settle;                               /* klonline_read.c: [HUD] OnlineNameSettle */
static int klor_read(struct klor_snap *o, int local)  /* klonline_read.c: no online round in the harness -> 0, snapshot cleared (as with Read=0) */
{ memset(o, 0, sizeof *o); o->b.human = -1; o->local = local; return 0; }
static int klor_bots_sorted(DWORD act[KLOR_NBOT], int *alive) { (void)act; if (alive) *alive = 0; return 0; }

/* klhud_grades.c (2026-10-27, [Grades]): the REAL module, as klhook.c includes it (after klonline_read.c, before klhud.c). Off-game it reads
   its keys from the harness's nonexistent ini (every switch 0: no badge, no letter, no RANK UP), and its one code check fails harmlessly. */
static int klc_same_code(DWORD va, const BYTE *bytes, int n) { (void)va; (void)bytes; (void)n; return 0; }   /* klchar.c: no kl2.exe here */
#include "klhud_grades.c"

/* klhud_board.c (the pre-round panel): klhud_board2.c shares its place and height constants and its render slot. Only those; the panel itself is not under test. */
#define KLBRD_O_INTRO     0x10ac
#define KLBRD_H           170.0f
#define KLBRD_DY          (-20.0f)
static volatile int klbrd_told_place; static float klbrd_place[2];
static char __fastcall klbrd_render(void *el, void *edx, void *ctx, void *cam) { (void)el; (void)edx; (void)ctx; (void)cam; return 0; }
static int klbrd_code_bad, klbrd_evt_ready; static DWORD klbrd_evt[4];   /* 2026-10-27: klhud_board2.c chains onto Board=1's private table (never ready here) */
static int kllnm_killtext(char *out, int cap) { if (cap > 0) out[0] = 0; return 0; }   /* kllocname.c stub: no stock death text here */
static void kllnm_killclear(void) { }
static const char *kllnm_name_now(int n) { (void)n; return 0; }   /* kllocname.c stub: no expansion names here */
#ifndef KLSB_HARNESS_HAS_BOARD2                        /* klwatch_test.c does not include klhud_board2.c: its state-render slot ([HUD] OnlineBoardState) is a no-op there */
static void klsb_state_render(void *el, void *ctx, void *cam) { (void)el; (void)ctx; (void)cam; }
#endif

#endif /* KLHUD_HARNESS_ONLINE_H */
