/* klbotdown_test.c - off-game harness for klbotdown.c (track Y2b). Builds the part against a FAKE 32 MB address space
   (addresses are used as offsets) with the structures it reads laid out as re\bots_down.md says, a fake of the game's
   down routine (the call is replaced by KLBD_CALL), and replays whole situations: a bot is shot under the threshold and
   goes down, lies, gets up; the game refuses; DownsMax; Dry; the vehicle driving out; a helper; the watchdog; the
   human's attribution. NOT the game: it proves the logic and that every write goes where the notes say, not that the
   game agrees.
   Build (x86, from a VS prompt):  cl /nologo /W3 klbotdown_test.c /Fe:klbotdown_test.exe     Run: klbotdown_test.exe */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdarg.h>

#define KLH_VA(x) (x)
#define KLB_NREC 32
#define KLB_ACTOR_VT 0x00bb3bac

static BYTE mem[0x02000000 + 0x10000];
static char logbuf[1 << 17]; static int nlog;
static const char *klh_ini = "";
static int klh_exe_ok = 1;
static void klog(const char *fmt, ...)
{
    va_list ap; char t[1800]; va_start(ap, fmt); vsnprintf(t, sizeof t, fmt, ap); va_end(ap);
    nlog += snprintf(logbuf + nlog, sizeof logbuf - nlog - 1, "%s\n", t);
}
static int klh_rd(DWORD_PTR p, void *out, SIZE_T n) { if (p < 0x1000 || p + n > sizeof mem) return 0; memcpy(out, mem + p, n); return 1; }
static DWORD klh_rd32(DWORD_PTR p) { DWORD v = 0; klh_rd(p, &v, 4); return v; }
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
static float RF(DWORD a) { float f = 0; klh_rd(a, &f, 4); return f; }
static WORD R16(DWORD a) { WORD w = 0; klh_rd(a, &w, 2); return w; }

struct klb_rec { int used; DWORD at, actor, money; BYTE status, stage, flags; float hit; };
struct klb_snap { DWORD rules, score, state, vehicle; int n, level, human; BYTE veh; float timer; struct klb_rec r[KLB_NREC]; int online; };
static struct klb_snap g_snap;
static int g_code_ok = 1;
static int klb_read(struct klb_snap *s) { *s = g_snap; return 1; }
static int klr_arcade(DWORD *rules, DWORD *state, int *level) { *rules = g_snap.rules; *state = g_snap.state; *level = 1; return 1; }
static int klb_level(char why[200]) { strcpy(why, "test level"); return 1; }
static int kle_node(DWORD node, float pos[3], float dir[3]) { (void)dir; if (!node) return 0; klh_rd(node, pos, 12); return 1; }
static int g_hum; static float g_hpos[3]; static int g_use, g_kad_on = 1, g_needuse;      /* OnlineRevive: the host's human (0 = none, as before), his place, Use held, [Adrenaline] Enable, the NeedUse row */
static int kle_human(DWORD *player, float feet[3], float nodepos[3]) { if (!g_hum) return 0; *player = 0x00f00000; memcpy(feet, g_hpos, 12); memcpy(nodepos, g_hpos, 12); return 1; }      /* g_hum 0: LieFar sees "not in play" */
static int klbd_kad(float *range, float *rate, float *minhelp, int *needuse) { if (!g_kad_on) return 0; *range = 2.5f; *rate = 3.0f; *minhelp = 1.0f; *needuse = g_needuse; return 1; }      /* kladren.c's numbers (defaults) */
static int kad_use_held(DWORD pl) { (void)pl; return g_use; }
static int klb_same_code(DWORD va, const BYTE *bytes, int n) { (void)va; (void)bytes; (void)n; return g_code_ok; }

#define SCORE 0x00300000
#define CLOCK 0x00310000
#define ACT(i)  (0x00400000 + 0x1000 * (i))
#define SOL(i)  (0x00500000 + 0x1000 * (i))
#define DND(i)  (0x00600000 + 0x100 * (i))
#define NODE(i) (0x00700000 + 0x100 * (i))
#define HO(i)   (0x00800000 + 0x100 * (i))
#define NDO(i)  (0x00900000 + 0x100 * (i))
static DWORD tick;

/* the fake down routine (0x70e0e0 through slot 51): what it does when the game says yes, what it asks first */
static int g_accept = 1, g_ncalls, g_last_hit_arg = -1, g_last_force = -1; static DWORD g_last_soldier;
static int g_start_in[KLB_NREC];            /* frames until slot 1 (the goal's start) runs */
static int fake_call(DWORD soldier, DWORD hit, int force)
{
    DWORD actor = klh_rd32(soldier + 0x40); int i = (int)((actor - 0x00400000) / 0x1000);
    g_ncalls++; g_last_soldier = soldier; g_last_hit_arg = (int)hit; g_last_force = force;
    if (R32(actor + 0x64c) & 0xff) return 0;
    if (!g_accept) return 0;
    W8(actor + 0x64c, 1); g_start_in[i] = 3;
    return 1;
}
#define KLBD_CALL(soldier) fake_call((DWORD)(soldier), 0, 1)
static int g_btest = 1, g_nb;
#define KLBD_BTEST(dnd) (g_nb++, g_btest)

enum { KLTT_REVIVE = 4, KLTT_ADREN = 5 }; static float kltt_get(int r, int k) { (void)r; (void)k; return 1.0f; } static float kltt_bot(DWORD a, int k) { (void)a; (void)k; return 1.0f; }   /* kltrait.c: no traits in this harness */
/* ONLINE harness: the host test, the census and the clock are the part's own #ifndef hooks, replaced by fakes */
static int g_ohost = 0, g_ncen; static DWORD g_ostate = 0x19;      /* g_ohost: 1 host, 0 not, -1 settings unreadable */ static DWORD g_cen[KLB_NREC]; static DWORD g_now = 5000;
static DWORD klh_avt(DWORD a) { return klh_rd32(a); }
static DWORD klh_svt(DWORD a) { return klh_rd32(a); }      /* klhook.c: maps the private ZSoldier table of OnlineBrainTraitorArcade; none here */
static int fake_census(DWORD *out, int max) { int i; for (i = 0; i < g_ncen && i < max; i++) out[i] = g_cen[i]; return g_ncen < max ? g_ncen : max; }
static int fake_host(DWORD *rules, DWORD *state) { if (g_ohost <= 0) return g_ohost; *rules = 0x2222; *state = g_ostate; return 1; }
#define KLBD_CENSUS(out, max) fake_census(out, max)
/* [Perf] CensusSlice: the shared sliced census walks a fake entity table (g_tab, 0 = unreadable); a candidate = an actor of g_cen */
static int g_cs_on, g_ncand_calls; static DWORD g_frame, g_tab;
static int fake_cand_ok(DWORD o) { int i; g_ncand_calls++; if (o < 0x10000) return 0; for (i = 0; i < g_ncen; i++) if (g_cen[i] == o) return 1; return 0; }
#define KLBD_ENT_TAB() g_tab
#define KLBD_CAND_OK(o) fake_cand_ok(o)
#define KLBD_CS_ON() g_cs_on
#define KLBD_FRAME() g_frame
#define KLBD_ONLINE_HOST(r, s) fake_host(r, s)
#define KLBD_NOW() g_now
static int klcmp_level_active(void) { return 0; }   /* klcampaign_gate.h stand-in: the campaign skip at the head of klbd_tick is not taken */
#include "klbotdown.c"

/* the fake game's own part of a down: slot 1 raises the health to 25 % and writes a lie of 1.5 s (2 s here); the script
   ends the goal when the lie is over: byte 0, health 75 % */
static int g_goal_never;                    /* 1 = the goal's script exits at once (0x70f330 fails at its start): nothing ever follows */
static void game_frame(void)
{
    int i;
    for (i = 1; i < 4; i++) {
        DWORD a = ACT(i), d = DND(i);
        if (!(R32(a + 0x64c) & 0xff) || g_goal_never) continue;
        if (g_start_in[i] > 0 && --g_start_in[i] == 0) {
            float hp = RF(HO(i) + 4), mx = RF(HO(i) + 8);
            W32(d + 0x14, tick + 2 * 1024);
            if (hp < mx * 0.25f) WF(HO(i) + 4, mx * 0.25f);
            g_start_in[i] = -1;
        } else if (g_start_in[i] == -1 && (long)(tick - R32(d + 0x14)) >= 0) {
            W8(a + 0x64c, 0); WF(HO(i) + 4, RF(HO(i) + 8) * 0.75f); g_start_in[i] = 0;
        }
    }
}

static void world(void)
{
    int i;
    memset(mem, 0, sizeof mem);
    W32(KLBD_CLOCK, CLOCK);
    W32(KLBD_SOLDIER_VT + 0xcc, KLBD_SLOT51);
    memset(&g_snap, 0, sizeof g_snap);
    g_snap.rules = 0x1111; g_snap.score = SCORE; g_snap.state = KLBD_ROUND; g_snap.n = 4; g_snap.human = 0; g_snap.veh = 0;
    for (i = 0; i < 4; i++) {
        struct klb_rec *r = &g_snap.r[i]; r->used = 1; r->status = 0; r->actor = ACT(i); r->flags = (BYTE)(i ? 1 : 0); r->stage = 1;
        if (i) {
            W32(ACT(i), KLB_ACTOR_VT); W32(ACT(i) + 0x77c, SOL(i)); W32(SOL(i), KLBD_SOLDIER_VT); W32(SOL(i) + 0x40, ACT(i)); W32(SOL(i) + 0x4b8, DND(i)); W32(DND(i) + 4, SOL(i));
            W32(ACT(i) + 4, NODE(i)); WF(NODE(i), 5000 + 1000 * i); WF(NODE(i) + 4, 0); WF(NODE(i) + 8, 0);
            W32(ACT(i) + 0x5fc, HO(i)); WF(HO(i) + 4, 252); WF(HO(i) + 8, 252); W32(HO(i) + 0x24, ACT(i));
            W32(ACT(i) + 0x54, NDO(i)); W32(SOL(i) + 0xb0, 0xdead0 + i);
        }
        g_start_in[i] = 0;
    }
    tick = 100000; W32(CLOCK + 0x48, tick);
    memset(&klbd, 0, sizeof klbd);
    klbd.on = 1; klbd.arc = 1; klbd.log = 1; klbd.downs_max = 2; klbd.traitors = 1; klbd.down_pct = 20; klbd.floor_pct = 6; klbd.refuse = 3000; klbd.lie = 6; klbd.free_t = 0.75f;
    klbd.attr = 1.5f; klbd.watch = 8; klbd.preshield = 0; g_btest = 1; g_nb = 0;
    memset(klbd_r, 0, sizeof klbd_r); memset(&klbd_g, 0, sizeof klbd_g);
    g_hum = 0; g_use = 0; g_kad_on = 1; g_needuse = 0; g_ohost = 0; g_ostate = 0x19; g_ncen = 0; g_now = 5000; klbd_online_reset(); g_accept = 1; g_ncalls = 0; g_goal_never = 0; g_code_ok = 1; nlog = 0; logbuf[0] = 0; nwrites = 0;
    g_cs_on = 0; g_tab = 0; g_ncand_calls = 0; memset(&klbd_cs, 0, sizeof klbd_cs); memset(klbd_ovs, 0, sizeof klbd_ovs);
}

#define ETAB 0x01000000                     /* the fake entity table: 0x10000 slots of 0x80 bytes, the object at +0x60 */
static void ent(int slot, DWORD o) { W32(ETAB + slot * 0x80 + 0x60, o); }

static void pass(int ms) { tick += ms * 1024 / 1000; W32(CLOCK + 0x48, tick); game_frame(); g_frame++; klbd_tick(1); }
static void run(int ms) { int t; for (t = 0; t < ms; t += 16) pass(16); }
static int fails;
#define CHECK(c, msg) do { if (!(c)) { printf("FAIL: %s  (line %d)\n", msg, __LINE__); fails++; } else printf("ok:   %s\n", msg); } while (0)
static int has(const char *s) { return strstr(logbuf, s) != NULL; }

int main(void)
{
    DWORD done;
    /* ---- pure arithmetic */
    CHECK(fabsf(klbd_thresh(252, 20) - 50.4f) < 0.01f && klbd_thresh(2, 20) == 1.0f, "klbd_thresh: 20 % of 252 = 50.4, never under 1");
    CHECK(fabsf(klbd_floor(252, 6, 50.4f) - 15.12f) < 0.01f && klbd_floor(252, 30, 50.4f) == 50.4f && klbd_floor(10, 0, 5) == 1.0f, "klbd_floor: 6 %, never over the threshold, at least 1");
    CHECK(klbd_lie_step(1000 + 3072, 1000, 100, 3.0f, &done) == 1000 + 3072 - 200 && done == 200, "klbd_lie_step: x3 takes 2 x dt off");
    CHECK(klbd_lie_step(1100, 1000, 100, 3.0f, &done) == 1002 && done == 98, "klbd_lie_step: never earlier than tick+2");
    CHECK(klbd_lie_step(1000 + 3072, 1000, 900, 3.0f, &done) == 1000 + 3072 && done == 0, "klbd_lie_step: a stall takes nothing");

    /* ---- 1: a bot is shot under the threshold, the hook asks, the game says yes, he lies LieSeconds, gets up */
    printf("--- scenario 1: the down\n"); world();
    run(100);
    CHECK(g_ncalls == 0 && nwrites == 0, "a healthy bot: no call, no write");
    WF(HO(1) + 4, 80); run(64);
    CHECK(g_ncalls == 0, "80 of 252 is over the threshold 50.4: nothing asked");
    WF(HO(1) + 4, 40); pass(16);
    CHECK(g_ncalls == 1 && g_last_soldier == SOL(1) && g_last_hit_arg == 0 && g_last_force == 1, "40 of 252: the game's down is asked ONCE, for his soldier, with no hit record and force 1");
    CHECK((R32(ACT(1) + 0x64c) & 0xff) == 1, "the (fake) game said yes: the down byte is set");
    pass(16);
    CHECK(has("record 1 IS DOWN, NOT DEAD (1 of 2)") && has("the HOOK asked and the game said YES"), "the IS DOWN line says 1 of 2 and who asked");
    run(200);
    CHECK(R32(DND(1) + 0x14) == klbd_r[1].tick_down + 6 * 1024, "the lie tick is tick_down + LieSeconds (6 s) once the game's slot 1 has written its own");
    CHECK(has("he lies until tick") && has("LieSeconds=6.0"), "the lie line");
    CHECK(RF(HO(1) + 4) >= 252 * 0.25f - 0.01f, "the game raised his health to 25 % (its slot 1); the part did not touch it (LiePct 0)");
    CHECK((R16(NDO(1) + 0x3a) & 0x800) != 0, "FreeSeconds: bit 0x800 of the 'no damage' word is held in the first 0.75 s");
    run(1000);
    CHECK((R16(NDO(1) + 0x3a) & 0x800) == 0, "...and taken off after 0.75 s");
    CHECK((R32(ACT(1) + 0x64c) & 0xff) == 1, "he is still lying at 1.5 s (the game alone would have got him up at 2 s; ours is 6 s)");
    run(5200);
    CHECK((R32(ACT(1) + 0x64c) & 0xff) == 0 && has("record 1 IS UP"), "he is up after the lie");
    CHECK(fabsf(RF(HO(1) + 4) - 189.0f) < 0.1f, "up with 75 % (the game's own)");
    CHECK(!has("watchdog") && !has("the byte is cleared"), "no watchdog line");

    /* ---- 2: a second down, then the budget is spent */
    printf("--- scenario 2: DownsMax\n");
    WF(HO(1) + 4, 30); run(100);
    CHECK(g_ncalls == 2 && has("(2 of 2)"), "second down: asked and 2 of 2");
    run(7000);
    CHECK((R32(ACT(1) + 0x64c) & 0xff) == 0, "up again");
    { int before = g_ncalls; WF(HO(1) + 4, 30); run(500); CHECK(g_ncalls == before, "DownsMax 2 spent: no third call (he dies like stock)"); }

    /* ---- 3: the game refuses */
    printf("--- scenario 3: refused\n"); world(); g_accept = 0;
    W32(SOL(2) + 0xa4, 0x00a00000); W32(0x00a00000 + 8, 2);        /* his ZHitAnimTask runs */
    WF(HO(2) + 4, 10); pass(16);
    CHECK(g_ncalls == 1 && has("the game said NO at try 1") && has("(RUNS: no down while a hit animation plays)"), "refused: first try, the reason names the hit animation");
    CHECK(RF(HO(2) + 4) >= 15.1f, "held at the FloorPct 6 % = 15.1 while it is refused (he was at 10)");
    WF(HO(2) + 4, 3); pass(16);
    CHECK(RF(HO(2) + 4) >= 15.1f, "a lower health is lifted to the floor again");
    run(500);
    CHECK(g_ncalls >= 4 && g_ncalls <= 7, "tried every ~100 ms (not every frame)");
    g_accept = 1; W32(0x00a00000 + 8, 0); pass(16); pass(16); pass(120);
    CHECK((R32(ACT(2) + 0x64c) & 0xff) == 1, "once the hit animation is over the same call is accepted");
    CHECK(has("IS DOWN") && !has("refused for"), "no give-up line when it was accepted in time");
    /* give up */
    world(); g_accept = 0; WF(HO(1) + 4, 10); run(3300);
    CHECK(has("refused for 3.") && has("NO down this time"), "after RefuseMs the part gives up and says so");
    { int c = g_ncalls; run(500); CHECK(g_ncalls == c, "no more calls after giving up"); }
    WF(HO(1) + 4, 200); pass(16); WF(HO(1) + 4, 10); pass(16);
    CHECK(g_ncalls > 0 && has("record 1 is at 10.0"), "healed over the threshold: a new episode (asked again)");

    /* ---- 4: Dry */
    printf("--- scenario 4: Dry\n"); world(); klbd.adry = 1;
    WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls == 0 && nwrites == 0, "Dry: no call, not one write");
    CHECK(has("Dry - record 1 is at 20.0") && has("WOULD ask"), "Dry: the WOULD line");

    /* ---- 5: the vehicle drives out */
    printf("--- scenario 5: vehicle state 5\n"); world();
    WF(HO(1) + 4, 20); pass(16); pass(16);
    CHECK((R16(NDO(1) + 0x3a) & 0x800) != 0, "the shield is on at the start of the down");
    g_snap.veh = 5; pass(16);
    CHECK((R16(NDO(1) + 0x3a) & 0x800) == 0, "vehicle state 5: the shield is taken off the same pass");
    WF(HO(2) + 4, 20); { int c = g_ncalls; pass(16); CHECK(g_ncalls == c, "vehicle state 5: no new down is asked"); }

    /* ---- 6: a helper pulls the lie earlier; our writer yields */
    printf("--- scenario 6: klbd_speed\n"); world();
    WF(HO(1) + 4, 20); run(300);
    { DWORD t0 = R32(DND(1) + 0x14); int w;
      CHECK(t0 == klbd_r[1].tick_down + 6 * 1024, "lie at 6 s");
      klbd_speed(1, 3.0f); pass(100); w = klbd_speed(1, 3.0f);
      CHECK(w && R32(DND(1) + 0x14) < t0, "klbd_speed(1, 3.0) pulled the lie tick earlier");
      { DWORD t1 = R32(DND(1) + 0x14); run(200); CHECK(R32(DND(1) + 0x14) == t1, "the part's own LieSeconds write does not put it back"); }
      CHECK(klbd_is_down(1) == 1 && klbd_is_down(2) == 0 && klbd_is_down(0) == 0, "klbd_is_down: record 1 only"); }

    /* ---- 7: the watchdog */
    printf("--- scenario 7: the goal never runs\n"); world(); g_goal_never = 1; klbd.lie = 3;
    WF(HO(1) + 4, 20); run(11000);
    CHECK((R32(ACT(1) + 0x64c) & 0xff) == 1, "no goal: the byte still stands at 11 s (lie 3 + watch 8)");
    run(1500);
    CHECK(has("the byte is cleared") && has("record 1 IS UP"), "the watchdog cleared the byte (the part may ask again: DownsMax bounds it)");

    /* ---- 8: attribution */
    printf("--- scenario 8: who put him down\n"); world();
    g_snap.r[1].hit = 0; pass(16);
    g_snap.r[1].hit = 30.0f; WF(HO(1) + 4, 20); pass(16); pass(16);
    CHECK(klbd_by(1) == 0 && has("a human's bullet"), "his sum on bot 1 rose just before: put down by record 0, klbd_by(1) = 0");
    world(); g_snap.r[2].hit = 30.0f; pass(16); WF(HO(2) + 4, 20); run(2000);
    CHECK(klbd_by(2) == -1, "a rise a long time before (2 s > AttrMs 1.5 s): nobody known");

    /* ---- 9: LiePct, UpPct, NoFire, traitors off */
    printf("--- scenario 9: LiePct / UpPct / NoFire\n"); world(); klbd.lie_pct = 50; klbd.up_pct = 40; klbd.nofire = 1;
    WF(HO(1) + 4, 20); run(400);
    CHECK(fabsf(RF(HO(1) + 4) - 126.0f) < 0.5f, "LiePct 50: 126 of 252 on the floor");
    CHECK(R32(SOL(1) + 0xb0) == 0, "NoFire: the target pointer is cleared while he lies");
    run(7000);
    CHECK(fabsf(RF(HO(1) + 4) - 100.8f) < 0.5f, "UpPct 40: 100.8 when he is up");
    world(); klbd.traitors = 0; g_snap.r[1].flags = 3; WF(HO(1) + 4, 20); run(200);
    CHECK(g_ncalls == 0, "Traitors=0: a turned bot is left alone");

    /* ---- 10: the code check, Enable=0, not the round */
    printf("--- scenario 10: guards\n"); world(); g_code_ok = 0; WF(HO(1) + 4, 20); run(100);
    CHECK(g_ncalls == 0 && has("is not the one this build knows"), "a different build: nothing is called");
    world(); klbd.on = 0; WF(HO(1) + 4, 20); run(100);
    CHECK(g_ncalls == 0 && nwrites == 0, "Enable=0: nothing");
    world(); g_snap.state = 0x10; WF(HO(1) + 4, 20); run(100);
    CHECK(g_ncalls == 0 && nwrites == 0, "no round: nothing");
    world(); g_snap.r[1].status = 7; WF(HO(1) + 4, 20); run(100);
    CHECK(g_ncalls == 0, "a dead record: nothing");

    /* ---- 11: ONLINE host: pseudo records from the census, the Arcade down on them; client / off / dry write nothing */
    printf("--- scenario 11: online host\n");
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 1; g_ncen = 2; g_cen[0] = ACT(1); g_cen[1] = ACT(2);
    WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls >= 1 && g_last_soldier == SOL(1), "online host: the census bot under the threshold is asked down");
    CHECK(has("ONLINE round") && has("IS DOWN"), "online host: the round-start line and the IS DOWN line");
    run(7000);
    CHECK(R32(ACT(1) + 0x64c) == 0 && has("IS UP"), "online host: he gets up after his lie");
    CHECK(R32(ACT(3) + 0x64c) == 0, "online host: an actor outside the census is not touched");
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 0; g_ncen = 1; g_cen[0] = ACT(1); WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls == 0 && nwrites == 0, "online CLIENT (not host): nothing is asked, nothing written");
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 0; g_ohost = 1; g_ncen = 1; g_cen[0] = ACT(1); WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls == 0 && nwrites == 0, "OnlineBotDown=0: nothing");
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; klbd.odry = 1; g_ohost = 1; g_ncen = 1; g_cen[0] = ACT(1); WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls == 0 && nwrites == 0 && has("WOULD ask"), "OnlineBotDownDry: logs, writes nothing");
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 1; g_ncen = 1; g_cen[0] = ACT(1); WF(HO(1) + 4, 0); run(300);
    CHECK(g_ncalls == 0, "online host: a dead bot (health 0) is left alone");

    /* review fixes 1 and 2: the pass runs only in state 0x19; an unreadable settings object changes nothing. NOT covered here: the real klbd_census /
       klbd_online_host (entity-table walk, role-2 gate, team read) - KLBD_CENSUS / KLBD_ONLINE_HOST are faked above; only a live bench reads them. */
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 1; g_ostate = 0x15; g_ncen = 1; g_cen[0] = ACT(1); WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls == 0 && nwrites == 0, "online host in pre-round state 0x15: no down, no write");
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 1; g_ncen = 1; g_cen[0] = ACT(1); WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls >= 1, "online host in state 0x19: down");
    { int rounds = 0; const char *q = logbuf; while ((q = strstr(q, "ONLINE round runs")) != NULL) { rounds++; q++; }
      g_ohost = -1; run(300); g_ohost = 1; run(300);
      q = logbuf; while ((q = strstr(q, "ONLINE round runs")) != NULL) { rounds--; q++; }
      CHECK(rounds == 0, "settings unreadable for a moment: no forget, no second round-start line"); }

    /* ---- 12: OnlineRevive: the host's human by a downed online bot pulls his lie (Range 2.5 m, MinHelp 1 s, Rate 3) */
    printf("--- scenario 12: online revive\n");
#define OREV(mode, hx, hy, nu, use, kon) do { world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 1; g_ncen = 1; g_cen[0] = ACT(1); klbd.orev = (mode); klbd.orevlog = 1; \
        g_hum = 1; g_hpos[0] = (hx); g_hpos[1] = (hy); g_hpos[2] = 0; g_needuse = (nu); g_use = (use); g_kad_on = (kon); WF(HO(1) + 4, 20); run(300); } while (0)
    OREV(1, 6100, 0, 0, 0, 1); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 0 && has("you help him up") && has("is up after") && has("the pull ran"), "by him (1 m), NeedUse off: up by 3.5 s (lie 6 s alone)");
    OREV(1, 6100, 0, 1, 0, 1); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && has("not holding Use") && !has("you help him up"), "NeedUse on, Use not held: no help, still down at 3.5 s");
    OREV(1, 6100, 0, 1, 1, 1); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 0 && has("you help him up"), "NeedUse on, Use held: up by 3.5 s");
    OREV(1, 6100, 0, 1, 1, 1); { int t; for (t = 0; t < 3200; t += 250) { g_use = (t / 250) & 1 ? 0 : 1; run(250); } }
    CHECK(R32(ACT(1) + 0x64c) == 1 && has("you help him up"), "NeedUse on, Use tapped (250 ms on / off): the pauses are not credited - still down at 3.5 s");
    OREV(1, 6600, 0, 0, 0, 1); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && !has("you help him up"), "6 m away (Range 2.5): no help");
    OREV(1, 6100, 300, 0, 0, 1); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && !has("you help him up"), "3 m above (another floor): no help");
    OREV(1, 6100, 0, 0, 0, 0); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && !has("you help him up"), "[Adrenaline] Enable=0: no help");
    OREV(0, 6100, 0, 0, 0, 1); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && !has("adren-online"), "OnlineRevive=0: nothing");
    OREV(2, 6100, 0, 0, 0, 1); { DWORD t0 = R32(DND(1) + 0x14); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && has("log only") && R32(DND(1) + 0x14) == t0, "OnlineRevive=2: the line, the lie tick untouched"); }
    world(); klbd.orev = 1; g_hum = 1; g_hpos[0] = 6100; WF(HO(1) + 4, 20); run(300); run(3200);
    CHECK(R32(ACT(1) + 0x64c) == 1 && !has("adren-online"), "Arcade (not online): OnlineRevive does nothing (kladren.c's own adrenaline is the Arcade one)");

    /* ---- 13: [Perf] CensusSlice: one census for every slot table, 128 blocks a frame, published only when the sweep is done */
    printf("--- scenario 13: CensusSlice\n");
    { struct klb_snap sa, sb; int k, steps = 0; DWORD i0;
      world(); g_cs_on = 1; g_tab = ETAB; g_ncen = 2; g_cen[0] = ACT(1); g_cen[1] = ACT(2); ent(5000, ACT(1)); ent(60000, ACT(2)); ent(7000, ACT(3));
      memset(&sa, 0, sizeof sa); sa.rules = 0x2222; sb = sa;
      for (k = 0; k < 7; k++) { g_frame++; klbd_ov_fill(&klbd_ovs[1], &sa, g_now); steps++; }
      CHECK(klbd_cs.at == 0 && klbd_ovs[1].ncand == 0 && sa.n == 0, "7 slices of 128 blocks: the sweep is not done, nothing published, no record yet");
      i0 = klbd_cs.i; klbd_ov_fill(&klbd_ovs[2], &sb, g_now);
      CHECK(klbd_cs.i == i0, "a second table in the same frame does not walk a second slice");
      g_frame++; klbd_ov_fill(&klbd_ovs[1], &sa, g_now);
      CHECK(klbd_cs.at == g_now && klbd_cs.n == 2 && sa.n == 2 && klbd_ovs[1].ncand == 2, "8th slice: the sweep is done, both Ally actors (slot 60000 too), ACT(3) not a candidate");
      CHECK(g_ncand_calls == 0x10000, "one sweep = each of the 0x10000 slots tested once");
      g_frame++; klbd_ov_fill(&klbd_ovs[2], &sb, g_now); klbd_ov_fill(&klbd_o, &sb, g_now);
      CHECK(sb.n == 2 && klbd_ovs[2].ncand == 2 && klbd_o.ncand == 2 && g_ncand_calls == 0x10000, "the other tables take the same result: no second walk");
      g_frame++; g_now += 500; klbd_ov_fill(&klbd_ovs[1], &sa, g_now);
      CHECK(klbd_cs.run == 0 && g_ncand_calls == 0x10000, "0.5 s later: no new sweep (once a second)");
      g_frame++; g_now += 600; klbd_ov_fill(&klbd_ovs[1], &sa, g_now);
      CHECK(klbd_cs.run == 1 && klbd_cs.n == 2 && klbd_ovs[1].ncand == 2, "1.1 s: a new sweep runs; the last result stays published meanwhile");
      memset(&klbd_ovs[3], 0, sizeof klbd_ovs[3]); sb.rules = 0x3333; g_frame++; klbd_ov_fill(&klbd_ovs[3], &sb, g_now);
      CHECK(klbd_ovs[3].ncand == 0 && sb.n == 0, "another session key: the result of 0x2222 is not handed over");
      world(); g_cs_on = 1; g_tab = ETAB; g_ncen = 1; g_cen[0] = ACT(1); ent(10, ACT(1)); memset(&sa, 0, sizeof sa); sa.rules = 0x2222;
      for (k = 0; k < 8; k++) { g_frame++; klbd_ov_fill(&klbd_ovs[1], &sa, g_now); }
      CHECK(sa.n == 1 && klbd_ovs[1].slot[0] == ACT(1), "one bot: in slot 0 after the 8th slice");
      g_tab = 0; for (k = 0; k < 10; k++) { g_frame++; g_now += 300; memset(&sa, 0, sizeof sa); sa.rules = 0x2222; klbd_ov_fill(&klbd_ovs[1], &sa, g_now); }
      CHECK(sa.n == 0 && klbd_ovs[1].slot[0] == 0, "table unreadable 3 s (a level load): the stale result is not used, the slot goes");
      g_tab = ETAB; ent(10, 0); ent(20, ACT(1)); for (k = 0; k < 8; k++) { g_frame++; memset(&sa, 0, sizeof sa); sa.rules = 0x2222; klbd_ov_fill(&klbd_ovs[1], &sa, g_now); }
      CHECK(sa.n == 1 && klbd_ovs[1].slot[0] == ACT(1), "the table is back: a fresh sweep finds him again");
      world(); g_cs_on = 1; g_tab = ETAB; g_ncen = 1; g_cen[0] = ACT(1); ent(10, ACT(1)); memset(&sa, 0, sizeof sa); sa.rules = 0x2222;
      for (k = 0; k < 4; k++) { g_frame++; klbd_ov_fill(&klbd_ovs[1], &sa, g_now); }
      g_tab = ETAB + 0x80; for (k = 0; k < 4; k++) { g_frame++; klbd_ov_fill(&klbd_ovs[1], &sa, g_now); }
      CHECK(klbd_cs.at == 0 && klbd_cs.run == 1, "the table moved mid-sweep: it starts over (4 slices are not a sweep)");
      world(); g_cs_on = 1; g_tab = ETAB; g_ncen = 1; g_cen[0] = ACT(1); ent(10, ACT(1));
      { int lost = 0; for (k = 0; k < 60; k++) { g_frame++; g_now += 250; memset(&sa, 0, sizeof sa); sa.rules = 0x2222; klbd_ov_fill(&klbd_ovs[1], &sa, g_now);
          if (k >= 8 && klbd_ovs[1].slot[0] != ACT(1)) lost++; }
        CHECK(lost == 0 && klbd_cs.at > 5000 + 8 * 250, "a lone caller every 250 ms (sweep 2 s, cycle 3 s > FRESH): the bot keeps slot 0 through 15 s of sweeps"); }
      (void)steps; }
    world(); g_snap.state = 0x10; klbd.arc = 0; klbd.oon = 1; g_ohost = 1; g_cs_on = 1; g_tab = ETAB; g_ncen = 2; g_cen[0] = ACT(1); g_cen[1] = ACT(2); ent(3, ACT(1)); ent(4, ACT(2));
    WF(HO(1) + 4, 20); run(300);
    CHECK(g_ncalls >= 1 && g_last_soldier == SOL(1) && has("IS DOWN"), "CensusSlice on: the online host's down works as with the one-call census");

    printf("\n%s (%d failure(s))\n", fails ? "FAILED" : "ALL PASS", fails);
    return fails ? 1 : 0;
}
