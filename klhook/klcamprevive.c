/*
 * klcamprevive.c - the Dead Men CAMPAIGN wounded-merc watch, ported (OBSERVATION PART ONLY) from luvsic's a-newer-perspective
 * loader/revive.inc @32aa649 (in contribution with luvsic). Part of KLHook (included by klhook.c AFTER klfreeclimb.c),
 * ticked from klh_tick on the gameplay call of SteamAPI_RunCallbacks.
 *
 * WHAT IS PORTED: the merc census (DD's merc list 0x1548fd8 + the buddy at gameMgr+0x4cf0, each validated as a
 * ZSoldier@CPPScript vt 0xbd0954 with its body), the per-merc observation (life +0x576, down flag +0x64c, DownNotDead
 * task +0x4b8 current in script +0x74, HP block +0x5fc) and the pure state/timing rules (klcamprevive_logic.h: bleed table
 * 60/45/30/30, back-off, HP floor, prompt range). With [CampRevive] Enable=1 it logs state changes ("revive: merc=.. DOWN").
 *
 * NOT PORTED (the live part, see the slice report): TryDownNotDead (0x688190) calls, the DND hold (task +0x14), the +0x124
 * Force/Prevent writes, mask 0x4000, regen stop, the heal action (factory 0x839740 / start 0x542c00), the prompt (0x4c06c0),
 * the bleed-out Die (slot 52) and the OnDeath intercept. [CampRevive] Live=1 is accepted and refused with one log line.
 * Nothing here writes to the game: SHIP policy trivially holds.
 *
 * Mutual exclusion: kldown.c, klbotdown.c, klcdying.c, kladren.c each skip their tick when klcmp_level_active(); this module
 * acts only when it is true. Helpers are copied under the klcrv_ prefix (no dependency on any other slice).
 */
#include "klcamprevive_logic.h"

#define KLCRV_SCRIPT_VT  0x00bd0954u     /* ZSoldier@CPPScript (READ revive.inc 141) */
#define KLCRV_DND_VT     0x00bcfd24u     /* ZDownNotDeadNPC@CPPScript (142) */
#define KLCRV_MERCS      0x01548fd8u     /* merc list: count, then [16] script pointers (162, 687-694) */
#define KLCRV_MAX        20

static struct { int on, live, log, difficulty; } klcrv;
static int klcrv_dead;
struct klcrv_m { DWORD s, body; int merc, buddy, state, life, dnd, used, deadline; float hp, mx; };
static struct klcrv_m klcrv_m[KLCRV_MAX];
static int klcrv_n;
static DWORD klcrv_lastP, klcrv_lastT, klcrv_gateT, klcrv_gate, klcrv_gs;

static DWORD klcrv_d32(DWORD a) { return a ? klh_rd32(a) : 0; }
static BYTE klcrv_d8(DWORD a) { BYTE b = 0; if (a) klh_rd(a, &b, 1); return b; }

/* the soldier script's body: script+0x40 (READ failwatch.inc fw_body_of), validated back through body+0x77c */
static DWORD klcrv_body(DWORD s)
{
    DWORD b;
    if (!klfc_ok(s, 0x740) || klh_rd32(s) != KLCRV_SCRIPT_VT) return 0;
    b = klh_rd32(s + 0x40);
    return (klfc_ok(b, 0x780) && klh_rd32(b + 0x77c) == s) ? b : 0;
}
/* HP block at body+0x5fc, owner +0x24 == body (READ failwatch.inc fw_hpblk) */
static int klcrv_hp(DWORD body, float *cur, float *mx)
{
    DWORD h = klcrv_d32(body + 0x5fc);
    *cur = *mx = -1.0f;
    if (!klfc_ok(h, 0x28) || klh_rd32(h + 0x24) != body) return 0;
    *cur = klfc_f(h + 4); *mx = klfc_f(h + 8);
    return 1;
}
/* the DND task is valid and is the script's current task (READ revive.inc 413-419) */
static int klcrv_dnd_current(DWORD s, DWORD body)
{
    DWORD t = klcrv_d32(s + 0x4b8);
    return klfc_ok(t, 0x18) && klh_rd32(t) == KLCRV_DND_VT && klh_rd32(t + 4) == s && klcrv_d8(body + 0x64c) == 1 && klh_rd32(s + 0x74) == t;
}

static struct klcrv_m *klcrv_find(DWORD body) { int i; for (i = 0; i < klcrv_n; i++) if (klcrv_m[i].body == body) return &klcrv_m[i]; return 0; }

static void klcrv_collect(DWORD gd)
{
    int i, nl = (int)klh_rd32((DWORD_PTR)KLH_VA(KLCRV_MERCS));
    DWORD bb = klh_rd32(gd + 0x4cf0);
    if (nl < 0) nl = 0;
    if (nl > 16) nl = 16;
    for (i = 0; i < klcrv_n; i++) klcrv_m[i].used = 0;
    for (i = 0; i < nl; i++) {
        DWORD s = klh_rd32((DWORD_PTR)KLH_VA(KLCRV_MERCS) + 4 + 4 * i), b = s ? klcrv_body(s) : 0;
        int id = s ? (int)klh_rd32(s + 0x6e8) : 0;
        struct klcrv_m *m;
        if (!b || !kcv_merc_id_ok(id)) continue;
        m = klcrv_find(b);
        if (!m && klcrv_n < KLCRV_MAX) {
            m = &klcrv_m[klcrv_n++]; memset(m, 0, sizeof *m);
            m->s = s; m->body = b; m->merc = id; m->buddy = b == bb; m->state = KCV_NORMAL; m->life = 1;
            klog("camprevive: merc %d (%s) listed, body %08lx", id, m->buddy ? "buddy" : "ai", b);
        }
        if (m) { m->used = 1; m->s = s; }
    }
    for (i = 0; i < klcrv_n; ) {                                   /* gone from the list: forget (no write ever happened) */
        if (!klcrv_m[i].used) klcrv_m[i] = klcrv_m[--klcrv_n]; else i++;
    }
}

static void klcrv_watch(struct klcrv_m *m, int T)
{
    int life = klcrv_d8(m->body + 0x576), dnd = klcrv_dnd_current(m->s, m->body), ns = kcv_observe_state(life, klcrv_d8(m->body + 0x64c), dnd);
    float hp, mx;
    klcrv_hp(m->body, &hp, &mx);
    if (ns != m->state) {
        if (ns == KCV_DOWN) m->deadline = kcv_deadline(T, klcrv.difficulty);
        if (klcrv.log) klog("camprevive: merc %d state %d -> %d (life %d, dnd %d, hp %.0f/%.0f%s%s)", m->merc, m->state, ns, life, dnd, hp, mx,
                            kcv_hp_at_floor(hp, mx) ? ", at the floor" : "", ns == KCV_DOWN ? ", would bleed out in the DM time" : "");
        m->state = ns;
    }
    if (m->state == KCV_DOWN && kcv_bled_out(T, m->deadline) && m->deadline > 0) {
        if (klcrv.log) klog("camprevive: merc %d bleed-out time (%d s) passed while down - observation only, the game decides", m->merc, kcv_bleed_sec(klcrv.difficulty));
        m->deadline = 0;
    }
    m->life = life; m->dnd = dnd; m->hp = hp; m->mx = mx;
}

static int klcrv_tick_body(void *unused)
{
    DWORD gd, P, now, gs; signed char pi = -1; int T, i;
    (void)unused;
    now = GetTickCount();
    if (!klcrv_gateT || now - klcrv_gateT > 1000) { klcrv_gate = klcmp_level_active() != 0; klcrv_gateT = now ? now : 1; }
    if (kcv_idle(klcrv_gate, klcrv.on, 0)) { klcrv_n = 0; return 0; }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA)))) return 0;
    if (!klh_rd(gd + 0x898, &pi, 1) || pi < 0 || pi > 7) return 0;
    if (!(P = klh_rd32(gd + 0x828 + 4 * pi)) || klh_pvt(P) != KLFC_PLAYER_VT || !klfc_ok(P, 0x2e00)) return 0;
    T = klfc_T();
    if (T == (int)klcrv_lastT) return 0;                              /* paused */
    klcrv_lastT = (DWORD)T;
    gs = klh_rd32((DWORD_PTR)KLH_VA(0xe0e644));                       /* game-state counter (READ revive.inc 163 RV_GS) */
    if (P != klcrv_lastP || gs != klcrv_gs) { klcrv_lastP = P; klcrv_gs = gs; klcrv_n = 0; }   /* new player / reload: forget (nothing was written) */
    if (klh_rd32((DWORD_PTR)KLH_VA(KLCRV_MERCS)) == 0) { klcrv_n = 0; return 0; }              /* merc list emptied: objects may be freed */
    klcrv_collect(gd);
    for (i = 0; i < klcrv_n; i++) klcrv_watch(&klcrv_m[i], T);
    return 0;
}

static void klcrv_tick(int game_thread)
{
    if (!klcrv.on || klcrv_dead || !game_thread || !klh_exe_ok) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA)) return;
    if (kl_online()) return;
    if (klfc_guard("camprevive tick", klcrv_tick_body, 0) < 0) { klcrv_dead = 1; klog("camprevive: DISABLED for this session (fault in tick)"); }
}

static void klcrv_init(void)
{
    memset(&klcrv, 0, sizeof klcrv);
    klcrv.on = GetPrivateProfileIntA("CampRevive", "Enable", 0, klh_ini) != 0;
    klcrv.live = GetPrivateProfileIntA("CampRevive", "Live", 0, klh_ini) != 0;
    klcrv.log = (int)GetPrivateProfileIntA("CampRevive", "Log", 1, klh_ini);
    klcrv.difficulty = (int)GetPrivateProfileIntA("CampRevive", "Difficulty", 1, klh_ini);   /* GUESS: the game's difficulty (0x156b5f0) is not read yet; this key stands in */
    if (klcrv.on) klog("camprevive: Enable=1 - observation only on a campaign level ([Campaign] Enable=1)%s", klcrv.live ? "; Live=1 REFUSED: the revive writes are not ported" : "");
}
