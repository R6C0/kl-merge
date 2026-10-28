/* kladren_test.c - off-game harness for kladren.c (track Y2). Builds the part against a FAKE 32 MB address space
   (addresses are used as offsets) with the structures it reads laid out as re\adrenaline.md says, and replays whole
   situations: a human puts a bot down, the bot is helped up, the share and the mark come and go; the human lies
   with a bot beside him; Dry; a foreign mark; a death while marked. NOT the game: it proves the logic and that every
   write goes where the notes say, not that the game agrees.
   Build (x86, from a VS prompt):  cl /nologo /W3 /DKAD_TEST kladren_test.c /Fe:kladren_test.exe     Run: kladren_test.exe */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdarg.h>

#define KLH_VA(x) (x)
#define KLB_NREC 32
#define KLB_ACTOR_VT 0x00bb3bac
#define KLD_CLOCK 0x00dd2640
#define KLD_ONE (kld.flop == 1 || kld.flop == 3)

static BYTE mem[0x02000000 + 0x10000];
static char logbuf[1 << 16]; static int nlog;
static const char *klh_ini = "";
static int klh_exe_ok = 1;
static void klog(const char *fmt, ...)
{
    va_list ap; char t[1500]; va_start(ap, fmt); vsnprintf(t, sizeof t, fmt, ap); va_end(ap);
    nlog += snprintf(logbuf + nlog, sizeof logbuf - nlog - 1, "%s\n", t);
}
static int klh_rd(DWORD_PTR p, void *out, SIZE_T n) { if (p < 0x1000 || p + n > sizeof mem) return 0; memcpy(out, mem + p, n); return 1; }
static DWORD klh_rd32(DWORD_PTR p) { DWORD v = 0; klh_rd(p, &v, 4); return v; }
static DWORD klh_pvt(DWORD o) { return klh_rd32(o); }      /* klhook.c: maps NetSmooth's private ZFFPlayer vtable; none here */
static int nwrites; static char lastwrite[200];
static int klh_data(void *at, const void *bytes, int len, const char *what)
{
    DWORD_PTR p = (DWORD_PTR)at; if (p < 0x1000 || p + len > sizeof mem) return 0;
    memcpy(mem + p, bytes, len); nwrites++; snprintf(lastwrite, sizeof lastwrite, "%s", what); return 1;
}
#define W32(a, v) do { DWORD _v = (DWORD)(v); memcpy(mem + (a), &_v, 4); } while (0)
#define W8(a, v) (mem[(a)] = (BYTE)(v))
#define WF(a, v) do { float _v = (float)(v); memcpy(mem + (a), &_v, 4); } while (0)
#define W16(a, v) do { WORD _v = (WORD)(v); memcpy(mem + (a), &_v, 2); } while (0)
#define R32(a) klh_rd32(a)

struct klb_rec { int used; DWORD at, actor, money; BYTE status, stage, flags; float hit; };
struct klb_snap { DWORD rules, score, state, vehicle; int n, level, human; BYTE veh; float timer; struct klb_rec r[KLB_NREC]; };
static struct klb_snap g_snap;
static int klb_read(struct klb_snap *s) { *s = g_snap; return 1; }
static int klr_arcade(DWORD *rules, DWORD *state, int *level) { *rules = g_snap.rules; *state = g_snap.state; *level = 1; return 1; }
static int klb_level(char why[200]) { strcpy(why, "test level"); return 1; }
static int kle_node(DWORD node, float pos[3], float dir[3]) { (void)dir; if (!node) return 0; klh_rd(node, pos, 12); return 1; }
static float g_feet[3];
static DWORD g_pl = 0x00330000;
static int kle_human(DWORD *player, float feet[3], float nodepos[3]) { *player = g_pl; memcpy(feet, g_feet, 12); memcpy(nodepos, g_feet, 12); return 1; }

static struct { int on, flop; } kld;
static struct { int up, fnow, fdone, idu; DWORD t_land; float meter; } kld_s;
static struct { int on; } kld_bk;
static int klbd_by(int record) { (void)record; return -1; }      /* klbotdown.c export (added to kladren.c after this harness): -1 = klbotdown knows nobody, as with [BotDown] off */

/* klescort.c exports used by the Rush (2026-10-14) */
struct kle_e { int rec, mode; DWORD actor, soldier, order_at, log_at; int orders, direct, told_soft, have_target, have_route; float target[3], route[3], d_order; };
static struct { char used[KLB_NREC]; } kle_r;
static int g_orders; static float g_order_at[3];
static int kle_bot(const struct klb_snap *s, int i, DWORD *actor, DWORD *soldier, float pos[3], char why[100])
{ *actor = s->r[i].actor; *soldier = 0x00500000 + 0x1000 * i; why[0] = 0; return kle_node(0x00700000 + 0x100 * i, pos, 0); }
static int kle_block(DWORD soldier, float pos[3]) { (void)soldier; pos[0] = 111; pos[1] = 0; pos[2] = 222; return 1; }
static void kltr_set(const char *who, const char *why, int rec) { (void)who; (void)why; (void)rec; }   /* klescort.c order tracer: names the issuer of the next order; nothing traces here */
static volatile int kle_gap_exempt;                          /* klescort.c (2026-10-18): set around orders OrderGap must never refuse; the stub order below takes every order anyway */
static int kle_order2(struct kle_e *e, const float want[3], float got[3], char why[100], int dry) { (void)e; (void)why; (void)dry; g_orders++; memcpy(g_order_at, want, 12); memcpy(got, want, 12); return 1; }

/* klhud.c / klhud_names.c / klhud_popup.c exports used by the Prompt (2026-10-14): the HUD is off here, so no prompt is said */
#define KLW_NREC 32
#define KLU_OSD_VT 0x00bbd7acu
struct klnm_rec { int used, ch, human; char stock[48], chr[32]; };
static struct { struct klnm_rec r[KLW_NREC]; } klnm_r;
static struct { int on; } klu;
static struct { DWORD osd; int fault; } klu_r;
static DWORD klpu_evt[40];
static volatile LONG kset_v[4] = { 0, 1, 1, 0 };           /* klset.c: Look, Textures, Prompt, NeedUse - the harness helps without E (its human helper scenarios predate the E key) */
static int klu_same_code(DWORD va, const BYTE *bytes, int n) { (void)va; (void)bytes; (void)n; return 0; }
enum { KLAN_UCC, KLAN_ADREN, KLAN_HINT };
static int klan_ready(int slot) { (void)slot; return 0; }                          /* klannounce.c: no announcement routine in this harness: no prompt is said */
static int klan_say_el(DWORD el, const char *t, float s, int slot) { (void)el; (void)t; (void)s; (void)slot; return 0; }

#define KAD_TEST_NOANIM                 /* the Anim part (klfreeclimb.c's engine calls) is not in this harness */
enum { KLTT_REVIVE = 4, KLTT_ADREN = 5 }; static float kltt_get(int r, int k) { (void)r; (void)k; return 1.0f; }   /* kltrait.c: no traits in this harness */
#include "kladren.c"

/* ---------------------------------------------------------------- the fake world */
#define SCORE 0x00300000
#define CLOCK 0x00310000
#define GD    0x00320000
#define PL    0x00330000
#define DD    0x00340000
#define ACT(i)  (0x00400000 + 0x1000 * (i))
#define SOL(i)  (0x00500000 + 0x1000 * (i))
#define DND(i)  (0x00600000 + 0x100 * (i))
#define NODE(i) (0x00700000 + 0x100 * (i))
static DWORD tick;

static void world(void)
{
    int i;
    memset(mem, 0, sizeof mem);
    W32(KLD_CLOCK, CLOCK); W32(KAD_GAMEDATA, GD); W32(GD + 0x828, PL); W8(GD + 0x898, 0);
    W32(PL, KAD_PLAYER_VT); W8(PL + 0x2723, 0); W32(PL + 0x2948, DD); W32(DD, PL); W32(DD + 4, 0);
    W32(KAD_TUNING, 0x00350000); W32(0x00350000 + 0xc10, (DWORD)-25000);
    memset(&g_snap, 0, sizeof g_snap);
    g_snap.rules = 0x1111; g_snap.score = SCORE; g_snap.state = KAD_ROUND; g_snap.n = 4; g_snap.human = 0;
    for (i = 0; i < 4; i++) {
        struct klb_rec *r = &g_snap.r[i]; r->used = 1; r->status = 0; r->actor = ACT(i); r->flags = (BYTE)(i ? 1 : 0); r->money = 0;
        if (i) {
            W32(ACT(i), KLB_ACTOR_VT); W32(ACT(i) + 0x77c, SOL(i)); W32(SOL(i), KAD_SOLDIER_VT); W32(SOL(i) + 0x40, ACT(i)); W32(SOL(i) + 0x4b8, DND(i)); W32(DND(i) + 4, SOL(i));
            W32(ACT(i) + 4, NODE(i)); WF(NODE(i), 5000 + 1000 * i); WF(NODE(i) + 4, 0); WF(NODE(i) + 8, 0);
        }
        W32(SCORE + 0x150 + 4 * i, 100000 * i);
    }
    g_feet[0] = 0; g_feet[1] = 0; g_feet[2] = 0;
    tick = 100000; W32(CLOCK + 0x48, tick);
    memset(&kad, 0, sizeof kad);
    kad.on = 1; kad.log = 1; kad.range = 2.5f; kad.brange = 4.0f; kad.rate = 3.0f; kad.meter = 3.0f; kad.minhelp = 0.4f; kad.share = 0.25f; kad.take = 1; kad.share_bot = 1; kad.bank = 1; kad.mark = 1;
    memset(&kld, 0, sizeof kld); memset(&kld_s, 0, sizeof kld_s); kld.on = 1; kld.flop = 3;
    kad_forget("test"); nlog = 0; logbuf[0] = 0; nwrites = 0;
}

static void pass(int ms) { tick += ms * 1024 / 1000; W32(CLOCK + 0x48, tick); kad_tick(1); }
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s  (line %d)\n", msg, __LINE__); fails++; } else printf("ok:   %s\n", msg); } while (0)

int main(void)
{
    DWORD cur, done; int i;
    /* ---- pure arithmetic */
    { float d[4] = { 300, -1, 120, 90 }, l[4] = { 250, 250, 250, 80 };
      CHECK(kad_pick(d, l, 4) == 2, "kad_pick: nearest within its own limit (3 is nearer but over its limit)");
      d[2] = 400; CHECK(kad_pick(d, l, 4) == -1, "kad_pick: nobody in range = -1"); }
    CHECK(kad_lie_step(1000 + 3072, 1000, 100, 3.0f, &done) == 1000 + 3072 - 200 && done == 200, "kad_lie_step: x3 takes 2 x dt off");
    CHECK(kad_lie_step(1100, 1000, 100, 3.0f, &done) == 1002 && done == 98, "kad_lie_step: never earlier than tick+2");
    CHECK(kad_lie_step(1000 + 3072, 1000, 900, 3.0f, &done) == 1000 + 3072 && done == 0, "kad_lie_step: a 900-tick pass (a stall) takes nothing");
    CHECK(kad_lie_step(1000 + 3072, 1000, 100, 1.0f, &done) == 1000 + 3072, "kad_lie_step: Rate 1 = nothing");
    CHECK(kad_share(400000, 0.25f) == 100000 && kad_share(0, 0.25f) == 0 && kad_share(-5, 0.25f) == 0 && kad_share(100, 2.0f) == 100, "kad_share");

    /* ---- 1: the human puts bot 1 down, stands by him, he gets up: share banked, mark on and off */
    printf("--- scenario 1\n"); world();
    W32(SCORE + 0x1d4, 0); W32(SCORE + 0x38, 1000); W16(SCORE + 0x1b8, 5);
    pass(100);                                              /* a quiet pass */
    W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 3072); W16(SCORE + 0x1b8, 6);   /* the game floors bot 1 and counts it for the human */
    pass(100);
    CHECK(R32(SCORE + 0x1d4) & 1, "the human is marked: client flag 1 set");
    CHECK(kad_m[0].on && kad_m[0].n == 1, "mark bookkeeping: on, 1 down");
    g_feet[0] = 6000 + 150; g_feet[1] = 0; g_feet[2] = 0;   /* he walks up: 1.5 m away */
    cur = R32(DND(1) + 0x14);
    for (i = 0; i < 10; i++) pass(100);
    CHECK((long)(R32(DND(1) + 0x14) - tick) < (long)(cur - tick) - 1500 || 1, "(info) lie tick moved");
    CHECK((long)(cur - R32(DND(1) + 0x14)) > 1500, "his lie tick was pulled earlier (a second of help took ~2 s off)");
    CHECK(kad_r[1].hm[0] >= 900, "help time ~1 s accumulated for record 0");
    W8(ACT(1) + 0x64c, 0);                                  /* he is up */
    pass(100);
    CHECK(R32(SCORE + 0x38) == 1000 + 25000, "share banked: 1000 -> 26000 (25 % of the $100000 bot 1 carried)");
    CHECK(R32(SCORE + 0x150 + 4) == 75000, "Take: the bot lost the share out of his cut");
    CHECK(!(R32(SCORE + 0x1d4) & 1) && !kad_m[0].on, "the mark is taken off again: he revived him");

    /* ---- 2: he is NOT helped: the mark stays */
    printf("--- scenario 2\n"); world();
    W16(SCORE + 0x1b8, 1); pass(100);
    W8(ACT(2) + 0x64c, 1); W32(DND(2) + 0x14, tick + 3072); W16(SCORE + 0x1b8, 2); pass(100);
    CHECK(R32(SCORE + 0x1d4) & 1, "marked");
    g_feet[0] = 90000;                                       /* far away */
    for (i = 0; i < 10; i++) pass(100);
    W8(ACT(2) + 0x64c, 0); pass(100);
    CHECK(R32(SCORE + 0x1d4) & 1, "he got up alone: the mark stays");
    CHECK(R32(SCORE + 0x38) == 0, "no share without help");

    /* ---- 3: a foreign mark (flag already set) is never touched */
    printf("--- scenario 3\n"); world();
    W32(SCORE + 0x1d4, 1); W16(SCORE + 0x1b8, 1); pass(100);
    W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 3072); W16(SCORE + 0x1b8, 2); pass(100);
    g_feet[0] = 6100; for (i = 0; i < 6; i++) pass(100);
    W8(ACT(1) + 0x64c, 0); pass(100);
    CHECK((R32(SCORE + 0x1d4) & 1) && !kad_m[0].on, "the game's own mark stays; nothing of ours was put on");

    /* ---- 4: a crewmate dies while the mark stands: it becomes the game's */
    printf("--- scenario 4\n"); world();
    W16(SCORE + 0x1b8, 1); pass(100);
    W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 3072); W16(SCORE + 0x1b8, 2); pass(100);
    g_snap.r[3].status = 7; pass(100);
    g_feet[0] = 6100; for (i = 0; i < 6; i++) pass(100);
    W8(ACT(1) + 0x64c, 0); pass(100);
    CHECK(R32(SCORE + 0x1d4) & 1, "a death while marked: the mark is kept after the revive");

    /* ---- 5: Dry */
    printf("--- scenario 5\n"); world(); kad.dry = 1;
    W16(SCORE + 0x1b8, 1); pass(100);
    W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 3072); W16(SCORE + 0x1b8, 2); pass(100);
    g_feet[0] = 6100; for (i = 0; i < 6; i++) pass(100);
    W8(ACT(1) + 0x64c, 0); pass(100);
    CHECK(nwrites == 0, "Dry: not one write");

    /* ---- 6: the human lies, a bot stands 3 m away: the meter is raised; 6 m: not */
    printf("--- scenario 6\n"); world();
    W32(DD + 4, 3); kld_s.up = 1; kld_s.meter = 0.5f; g_feet[0] = 6000 - 300; pass(100); pass(100);
    CHECK(kld_s.meter >= 3.0f, "a bot 3 m from the downed human: the mash meter is held at Meter");
    world(); W32(DD + 4, 3); kld_s.up = 1; kld_s.meter = 0.5f; g_feet[0] = 6000 - 900; pass(100); pass(100);
    CHECK(kld_s.meter < 3.0f, "a bot 9 m away: no boost");
    world(); W32(DD + 4, 3); kld_s.up = 1; kld_s.meter = 0.5f; g_feet[0] = 6000 - 300; g_snap.r[1].flags |= 2; g_snap.r[2].flags |= 2; g_snap.r[3].flags |= 2; pass(100); pass(100);
    CHECK(kld_s.meter < 3.0f, "traitors do not help");
    /* he gets up helped: a bot is paid out of... the HUMAN is never debited, the bot gets Share of what the human carries */
    world(); W32(DD + 4, 3); W32(SCORE + 0x150, 400000); kld_s.up = 1; g_feet[0] = 6000 - 300; pass(100); for (i = 0; i < 8; i++) pass(100);
    W32(DD + 4, 0); pass(100);
    CHECK(R32(SCORE + 0x150) == 300000, "review 5: the helped human is debited the share (Take=1): the share makes no money");
    CHECK(R32(SCORE + 0x150 + 4) == 100000 + 100000, "the bot beside him got 25 % of $400000 carried");
    /* review 5: a second down + help of the same man in the same round pays nothing more */
    W32(DD + 4, 3); kld_s.up = 1; pass(100); for (i = 0; i < 8; i++) pass(100); W32(DD + 4, 0); pass(100);
    CHECK(R32(SCORE + 0x150) == 300000 && R32(SCORE + 0x150 + 4) == 200000, "once per man per round: the second get-up pays nothing");

    /* ---- 7: a new rules object takes a leftover mark off */
    printf("--- scenario 7\n"); world();
    W16(SCORE + 0x1b8, 1); pass(100);
    W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 3072); W16(SCORE + 0x1b8, 2); pass(100);
    g_snap.rules = 0x2222; pass(100);
    CHECK(!(R32(SCORE + 0x1d4) & 1), "a new round: the old mark of ours is taken off");


    /* ---- 8 (2026-10-14): BotHelp + Rush: bot 1 goes down, bot 2 (10 m off) is sent to him, helps him up, earns the share, goes back */
    printf("--- scenario 8\n"); world(); kad.bothelp = 1; kad.rush = 1; kad.rushrange = 25.0f; g_orders = 0;
    g_feet[0] = -9000;                                      /* the human is 150 m off: no human help */
    pass(100);
    W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 6144);
    pass(100);
    CHECK(g_orders == 0, "no rush in the first 0.6 s");
    Sleep(700); pass(100);
    CHECK(g_orders == 1 && kad_r[1].rusher == 2 + 1, "Rush: the nearest bot (record 2, 10 m) is sent");
    CHECK(fabs(g_order_at[0] - (6000 + 80)) < 1 && fabs(g_order_at[2]) < 1, "Rush: to 0.8 m beside the downed bot, on the sender's side");
    WF(NODE(2), 6000 + 120);                                /* bot 2 arrives: 1.2 m away */
    for (i = 0; i < 10; i++) pass(100);
    CHECK(kad_r[1].hm[2] >= 900, "BotHelp: bot 2 helps bot 1 (~1 s)");
    W8(ACT(1) + 0x64c, 0); pass(100);
    CHECK(R32(SCORE + 0x150 + 8) == 200000 + 25000 && R32(SCORE + 0x150 + 4) == 75000, "BotHelp: bot 2 gets 25 % of bot 1's cut, out of it");
    CHECK(g_orders == 2 && g_order_at[0] == 111 && g_order_at[2] == 222 && kad_r[1].rusher == 0, "Rush: bot 2 is sent back to its own place when bot 1 is up");
    world(); kad.rush = 1; kad.rushrange = 25.0f; g_orders = 0; kle_r.used[2] = 1; kle_r.used[3] = 1; g_feet[0] = -9000;   /* both other bots are escorts */
    pass(100); W8(ACT(1) + 0x64c, 1); W32(DND(1) + 0x14, tick + 6144); pass(100); Sleep(700); pass(100);
    CHECK(g_orders == 0, "Rush: an escort is not taken from the human for a downed bot");
    memset(&kle_r, 0, sizeof kle_r);

    /* ---- 9 (2026-10-14): the human in kldown.c's fall reads 'down state 2' - he is down, and a bot is sent to him (his escort may go) */
    printf("--- scenario 9\n"); world(); kad.rush = 1; kad.rushrange = 25.0f; g_orders = 0; kle_r.used[1] = 1;
    g_feet[0] = 5000; pass(100);                            /* bot 1 (his escort) 10 m off, bot 2 20 m */
    W32(DD + 4, 2); pass(100);
    CHECK(kad_r[0].down, "down state 2 = the human is down");
    Sleep(700); pass(100);
    CHECK(g_orders == 1 && kad_r[0].rusher == 1 + 1, "Rush: his escort (record 1, nearest) runs to the downed human");
    W32(DD + 4, 0); pass(100);
    CHECK(!kad_r[0].down && kad_r[0].rusher == 0, "he is up: the rush ends (the escort takes his own man back)");
    memset(&kle_r, 0, sizeof kle_r);
    printf("\n%s (%d failure(s))\n", fails ? "FAILED" : "ALL PASS", fails);
    return fails != 0;
}
