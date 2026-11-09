/* klcampsquad.c - [CampSquad]: crew orders (1 follow, 2 attack, 3 defend, Tab next merc) on the Dead Men CAMPAIGN levels, plus the
 * recruit and critical-flag helpers luvsic's loader runs there. OFF by default, idle unless [Campaign] Enable=1 and a campaign scene
 * (M01..M14) is loaded (klcampaign_gate.h): on Dog Days' 9 FA maps, Dead Men FA maps, Arcade and online it never runs.
 *
 * ported from luvsic's a-newer-perspective loader/squad.inc @32aa649 (in contribution with luvsic). READ = taken from his code,
 * MEASURED = checked here against kl2.exe, GUESS = neither.
 *
 * WHAT IS PORTED (all through the SAME game routines klcopsquad.c calls, so DD's own Follow/Attack/MoveTo/Recruit do the work):
 *   - tap / hold keys: a press shorter than 0.25 s is a TAP (acts on the CURRENT receiver, sc+0x10), a longer one a HOLD (all receivers). READ sq_keys.
 *     Follow = 0x4c3900(sc, hold); Attack = ZSoldier vt+0x14c (0x831850)(handle, point, T); Defend = vt+0x13c (0x760e50)(point, 0, 1, 0);
 *     Next = 0x5d3010(sc, prev) (Shift+Next = prev). READ sq_follow / sq_attack / sq_defend / sq_cycle.
 *   - the M01 refusal rule: sc+0xa0 := 1 on M01 ([CampSquad] Refuse=auto): the crew refuses orders there, as in the campaign. READ sq_refuse_rule.
 *   - recruit (Recruit=start): the level's mercs (DD's merc list 0x1548fd8) join the player's squad control. A merc held by a level squad
 *     (script+0x4f4 set, not the player squad) is left alone, or only ADOPTED (script+0x69c := P, a data write) when he has no owner and
 *     RecruitAdopt=1; a free merc is recruited after +0x4f4 was stable for RecruitSettle seconds (0x908040); a member of the player squad
 *     that is no receiver is added to the receiver list as data (the tail of 0x6213b0). Recruit=always recruits every able merc (the old
 *     behaviour of his loader). READ sq_recruit_start / sq_recruit_scan.
 *   - Critical=clear: every listed merc's script+0x513 flag is cleared when set (DD marks the crew "critical" and the orders fail); only
 *     after five code heads and two vtable slots match (MEASURED, below). READ sq_crit_*.
 * NOT PORTED (left out on purpose, listed in the commit): defend line-of-sight and ground ray, speech acks / markers / look-at, the node-table
 * "walk for mercs DD did not list", the config/command FILES (ANP_squad.txt, ANP_squad_cmd.txt: here the ini is the config), the climbing gate,
 * the HUD-state gate (0x6a88f0 busy test is replaced by the input-block gate P+0x2728 / P+0x2760), the player-squad mini-cutscene wait.
 * MEASURED heads (kl2.exe 0490): 0x5d3010 83 ec 6c 53 57 8b f9; 0x5230c0 55 8b ec 51 53 56 57; 0x4c3b10 55 8b ec 53 56 57 8b 7d 08; the rest as klcopsquad.c.
 *
 * GUESS: the keys 1/2/3 are also the campaign's weapon-select keys; the game reads them too (this module does not consume them), so an order
 * and a weapon change can happen together. Rebind in [CampSquad] if that is a problem. Nothing here is benched.
 *
 * KLHook.ini [CampSquad]  (see klhook/ini_campaign_gameplayA.txt)
 *   Enable=0  Recruit=start|always|off  RecruitAdopt=0  RecruitSettle=2  Critical=keep|clear  Refuse=auto|0|1  AttackT=5
 *   KeyFollow=0x31 KeyAttack=0x32 KeyDefend=0x33 KeyNext=0x09 KeyPrev=0   Log=1
 */
#ifndef KLCAMPSQUAD_C
#define KLCAMPSQUAD_C
#include "klcampsquad_logic.h"

#define KLCSQ_CYCLE      0x005d3010u
#define KLCSQ_SQREMOVE   0x005230c0u
#define KLCSQ_SETOWNER   0x004c3b10u
#define KLCSQ_MERC_LIST  0x01548fd8u         /* READ SQ_MERC_LIST: +0 count, +4[i] ZSoldier script */
#define KLCSQ_GS_COUNTER 0x00e0e644u         /* READ SQ_GS_COUNTER: game-state counter */
#define KLCSQ_CRIT_OFF   0x513u

struct klcsq_rec { DWORD s; int tries, seen, announced; DWORD lastT, q, qSince, heldQ; };
static struct {
    int on, recruit, adopt, settleMs, crit, refuse, log, dead, heads, critBuild;
    float attackT; int kF, kA, kD, kN, kP;
    SHORT (WINAPI *aks)(int); HWND (WINAPI *fgw)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD);
    struct klcsq_k key[3]; int nxWas, pvWas;
    DWORD P, sc, t0, recPoll, critPoll, critGs, nCalls; int critGsSeen, refuseSet, active, told;
    char key_s[64]; struct klcsq_rec rec[16];
} klcsq;

static void klcampsquad_init(void)
{
    char v[32]; HMODULE u;
    klcsq.on = GetPrivateProfileIntA("CampSquad", "Enable", 0, klh_ini) != 0;
    if (!klcsq.on) return;
    GetPrivateProfileStringA("CampSquad", "Recruit", "start", v, sizeof v, klh_ini);
    klcsq.recruit = klcsq_recmode(v); if (klcsq.recruit < 0) klcsq.recruit = KLCSQ_REC_START;
    klcsq.adopt = GetPrivateProfileIntA("CampSquad", "RecruitAdopt", 0, klh_ini) != 0;
    { char s[16]; GetPrivateProfileStringA("CampSquad", "RecruitSettle", "2", s, sizeof s, klh_ini); klcsq.settleMs = klcsq_clamp_settle_ms((float)atof(s)); }
    GetPrivateProfileStringA("CampSquad", "Critical", "keep", v, sizeof v, klh_ini); klcsq.crit = !_stricmp(v, "clear");
    GetPrivateProfileStringA("CampSquad", "Refuse", "auto", v, sizeof v, klh_ini); klcsq.refuse = !_stricmp(v, "auto") ? -1 : atoi(v) != 0;
    { char s[16]; GetPrivateProfileStringA("CampSquad", "AttackT", "5", s, sizeof s, klh_ini); klcsq.attackT = klcsq_clamp_attack_t((float)atof(s)); }
    klcsq.kF = GetPrivateProfileIntA("CampSquad", "KeyFollow", 0x31, klh_ini) & 0xff; klcsq.kA = GetPrivateProfileIntA("CampSquad", "KeyAttack", 0x32, klh_ini) & 0xff;
    klcsq.kD = GetPrivateProfileIntA("CampSquad", "KeyDefend", 0x33, klh_ini) & 0xff; klcsq.kN = GetPrivateProfileIntA("CampSquad", "KeyNext", 0x09, klh_ini) & 0xff;
    klcsq.kP = GetPrivateProfileIntA("CampSquad", "KeyPrev", 0, klh_ini) & 0xff;
    klcsq.log = GetPrivateProfileIntA("CampSquad", "Log", 1, klh_ini);
    { int i; int *kk[5]; kk[0] = &klcsq.kF; kk[1] = &klcsq.kA; kk[2] = &klcsq.kD; kk[3] = &klcsq.kN; kk[4] = &klcsq.kP;
      for (i = 0; i < 5; i++) { int j; for (j = 0; j < KK_N; j++) if (*kk[i] && klkeys_vk(j) == *kk[i]) { klog("campsquad: key %#x is also KLHook's own key %d: that order key is OFF (rebind [CampSquad] Key*)", *kk[i], j); *kk[i] = 0; break; } } }
    if ((u = GetModuleHandleA("user32.dll")) != 0) { klcsq.aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); klcsq.fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); klcsq.wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
    klog("campsquad: ON (NOT benched; campaign levels only): recruit %d adopt %d settle %d ms critical %s refuse %d attackT %.1f keys 1/2/3/next/prev %#x/%#x/%#x/%#x/%#x%s", klcsq.recruit, klcsq.adopt, klcsq.settleMs,
         klcsq.crit ? "clear" : "keep", klcsq.refuse, (double)klcsq.attackT, klcsq.kF, klcsq.kA, klcsq.kD, klcsq.kN, klcsq.kP, klcsq.aks ? "" : " (no GetAsyncKeyState: keys off)");
}

/* the code heads this module calls through, and the vtable slots (MEASURED, see the header) */
static int klcsq_heads(void)
{
    static const BYTE cyc[7] = { 0x83, 0xec, 0x6c, 0x53, 0x57, 0x8b, 0xf9 }, rem[7] = { 0x55, 0x8b, 0xec, 0x51, 0x53, 0x56, 0x57 }, own[9] = { 0x55, 0x8b, 0xec, 0x53, 0x56, 0x57, 0x8b, 0x7d, 0x08 };
    if (klcsq.heads) return klcsq.heads > 0;
    klcsq.heads = -1;
    if (!klcq_heads()) { klog("campsquad: the Follow/Attack/MoveTo/Recruit heads or ZSoldier slots +0x13c/+0x14c are not the ones this build knows: OFF"); return 0; }
    if (!klb_same_code(KLCSQ_CYCLE, cyc, 7) || !klb_same_code(KLCSQ_SQREMOVE, rem, 7) || !klb_same_code(KLCSQ_SETOWNER, own, 9)) { klog("campsquad: 0x5d3010 / 0x5230c0 / 0x4c3b10 head differs: OFF"); return 0; }
    klcsq.heads = 1; return 1;
}

static DWORD klcsq_player(void)
{   /* READ sq_player: gd+0x828+4*[gd+0x898] */
    DWORD gd, p; BYTE sel = 0xff;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 7 || !(p = klh_rd32(gd + 0x828 + 4 * sel)) || klh_pvt(p) != 0x00bb45f4u /* ZFFPlayer (klinv.c is included later) */) return 0;
    return p;
}
static int klcsq_key(int vk)
{
    HWND fg; DWORD pid = 0;
    if (!vk || !klcsq.aks || !klcsq.fgw || !klcsq.wtp || !(fg = klcsq.fgw())) return 0;
    klcsq.wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (klcsq.aks(vk) & 0x8000) != 0;
}
static int klcsq_blocked(DWORD P) { BYTE b = 0; klh_rd(P + 0x2728, &b, 1); return b || klh_rd32(P + 0x2760); }   /* READ sq_gate: gameplay input blocked */
static int klcsq_nr(DWORD sc) { return klcsq_nrecv(klh_rd32(sc + 0x18)); }

/* a merc script that is alive and orderable now: soldier script, body points back, merc id 1..13, able byte */
static DWORD klcsq_body(DWORD s)
{
    DWORD body, node, fl = 0; DWORD m;
    if (!s || klh_svt(s) != KLE_SOLDIER_VT || !(body = klh_rd32(s + 0x40)) || klh_avt(body) != KLB_ACTOR_VT || klh_rd32(body + 0x77c) != s) return 0;
    m = klh_rd32(s + 0x6e8); if (m < 1 || m > 13) return 0;
    if (!(node = klh_rd32(body + 4)) || !klh_rd(node + 0x3c, &fl, 4)) return 0;
    return body;       /* GUESS: luvsic also proves the body sits in the node table (sq_merc_body); a stale list entry is caught here only by the vtable/back-pointer tests */
}
static int klcsq_able(DWORD body, int *nodeOff)
{
    BYTE a = 0; DWORD node = klh_rd32(body + 4), fl = 0;
    klh_rd(body + 0x576, &a, 1); klh_rd(node + 0x3c, &fl, 4); *nodeOff = (fl & 0x400) != 0;
    return a == 1;
}
static int klcsq_in_list(DWORD sc, int cnt, int arr, DWORD s)
{
    int n = klcsq_nrecv(klh_rd32(sc + cnt)), i;
    for (i = 0; i < n; i++) if (klh_rd32(sc + arr + 4 * i) == s) return 1;
    return 0;
}

/* ---- orders ---- */
static int klcsq_targets(DWORD sc, int hold, DWORD *out, int cap)
{
    int n = 0, nr = klcsq_nr(sc), i, ni;
    if (!hold) {
        DWORD cur = klh_rd32(sc + 0x10), s; int idx = klcsq_cur_idx(cur, sc + 0x1c, nr);
        if (idx < 0 || !(s = klh_rd32(cur)) || !klcsq_body(s) || !klcsq_able(klcsq_body(s), &ni) || ni) return 0;
        out[0] = s; return 1;
    }
    for (i = 0; i < nr && n < cap; i++) { DWORD s = klh_rd32(sc + 0x1c + 4 * i), b = klcsq_body(s); if (b && klcsq_able(b, &ni) && !ni) out[n++] = s; }
    return n;
}
static int klcsq_bump(DWORD sc) { DWORD v = klh_rd32(sc + 8) + 1; return klh_data((void *)(DWORD_PTR)(sc + 8), &v, 4, "campsquad order counter"); }   /* READ: order counter as DD's Follow does (heap) */

struct klcsq_job { int kind, hold, prev; DWORD P, sc; int n; };
static int klcsq_do(void *arg)
{
    struct klcsq_job *j = (struct klcsq_job *)arg; DWORD list[16]; float aim[4]; int i, n;
    if (j->kind == 4) {                                                       /* select */
        ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLCSQ_CYCLE))((void *)(DWORD_PTR)j->sc, 0, j->prev); klcsq.nCalls++;
        return 1;
    }
    if (j->kind == 1) {                                                       /* follow: DD's Follow(all=hold) refuses itself; we do not call while the refusal flag is set (voice omitted) */
        BYTE a0 = 0; klh_rd(j->sc + 0xa0, &a0, 1);
        if (a0 || !klcsq_nr(j->sc)) return 0;
        ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLCQ_FOLLOW))((void *)(DWORD_PTR)j->sc, 0, j->hold); klcsq.nCalls++;
        return 1;
    }
    { BYTE a0 = 0; klh_rd(j->sc + 0xa0, &a0, 1); if (a0) return 0; }
    if (!klh_rd(j->P + 0x27b0, aim, 12) || !klb_finite(aim[0]) || !klb_finite(aim[1]) || !klb_finite(aim[2])) return 0;     /* VERIFIED aim point (klcopsquad.c header) */
    aim[3] = 0;
    n = klcsq_targets(j->sc, j->hold, list, 16); if (!n) return 0;
    if (!klcsq_bump(j->sc)) return 0;
    for (i = 0; i < n; i++) {
        DWORD s = list[i];
        if (j->kind == 2) {
            DWORD a = klh_rd32(j->P + 0xbd4), h = a ? klh_rd32(a + 0x2ac) : 0;
            if (klh_rd32(klh_rd32(s) + 0x14c) != KLCQ_ATTACK) continue;
            ((void (__fastcall *)(void *, void *, DWORD, const float *, float))(DWORD_PTR)KLH_VA(KLCQ_ATTACK))((void *)(DWORD_PTR)s, 0, h, aim, klcsq.attackT);
        } else {
            if (klh_rd32(klh_rd32(s) + 0x13c) != KLE_ORDER) continue;
            ((void (__fastcall *)(void *, void *, const float *, int, int, int))(DWORD_PTR)KLH_VA(KLE_ORDER))((void *)(DWORD_PTR)s, 0, aim, 0, 1, 0);
        }
        klcsq.nCalls++;
    }
    j->n = n;
    return 1;
}
static void klcsq_order(DWORD P, DWORD sc, int kind, int hold, int prev)
{
    struct klcsq_job j; static const char *nm[] = { "", "follow", "attack", "defend", "select" };
    memset(&j, 0, sizeof j); j.kind = kind == 3 ? 3 : kind; j.hold = hold; j.prev = prev; j.P = P; j.sc = sc;
    if (kind == 3) j.kind = 3;
    if (klfc_guard("campsquad order", klcsq_do, &j) < 0) { klcsq.dead = 1; klog("campsquad: DISABLED (fault in an order; restart the game)"); return; }
    if (klcsq.log) klog("campsquad: %s %s -> %d receivers, order no. %lu, refusal flag %d", nm[kind], kind == 4 ? (prev ? "prev" : "next") : hold ? "hold" : "tap", klcsq_nr(sc), (unsigned long)klh_rd32(sc + 8), klh_rd32(sc + 0xa0) & 0xff);
}

static void klcsq_keys(DWORD P, DWORD sc, DWORD now)
{
    const int vk[3] = { klcsq.kF, klcsq.kA, klcsq.kD }; int i, nx, pv;
    if (klcsq_blocked(P)) { memset(klcsq.key, 0, sizeof klcsq.key); return; }
    for (i = 0; i < 3; i++) {
        int r = klcsq_key_step(&klcsq.key[i], klcsq_key(vk[i]), now);
        if (r == 1) klcsq_order(P, sc, i == 0 ? 1 : i == 1 ? 2 : 3, 1, 0);
        else if (r == 2) klcsq_order(P, sc, i == 0 ? 1 : i == 1 ? 2 : 3, 0, 0);
        if (klcsq.dead) return;
    }
    nx = klcsq_key(klcsq.kN); pv = klcsq.kP && klcsq_key(klcsq.kP);
    { int shift = klcsq_key(0x10); if (klcsq_edge(&klcsq.nxWas, nx)) klcsq_order(P, sc, 4, 0, shift && !klcsq.kP); }
    if (klcsq_edge(&klcsq.pvWas, pv)) klcsq_order(P, sc, 4, 0, 1);
}

/* ---- recruit ---- */
static struct klcsq_rec *klcsq_rec(DWORD s)
{
    int i;
    for (i = 0; i < 16; i++) if (klcsq.rec[i].s == s) return &klcsq.rec[i];
    for (i = 0; i < 16; i++) if (!klcsq.rec[i].s) { memset(&klcsq.rec[i], 0, sizeof klcsq.rec[i]); klcsq.rec[i].s = s; return &klcsq.rec[i]; }
    return 0;
}
static int klcsq_unsafe(DWORD s, DWORD body)         /* READ sq_recruit_unsafe: 0x908040 -> 0x4c3b10 dereferences these unchecked */
{
    BYTE t[0x78];
    if (!klh_rd(klh_rd32(s + 0x63c), t, 0x78) || !klh_rd(klh_rd32(s + 0x738), t, 0x10) || !klh_rd(klh_rd32(s + 0x6d8), t, 4) || !klh_rd(klh_rd32(body + 4), t, 0x60)) return 1;
    return klh_rd32(klh_rd32(s) + 0x1b0) != KLCSQ_SETOWNER;
}
struct klcsq_rj { DWORD sc, sq, s, body, P; int kind; };
static int klcsq_rec_do(void *arg)
{
    struct klcsq_rj *r = (struct klcsq_rj *)arg;
    if (r->kind == KLCSQ_R_RECRUIT) {
        if (r->sq && klh_rd32(r->sq + 0xc0) >= 12) return 0;                                   /* 0x48c480 stops at 12 members */
        if (klcsq_nr(r->sc) >= 16) return 0;
        if (klh_rd32(r->s + 0x4f4) == 0 || klh_rd32(r->s + 0x4f4) == r->sq) { /* free, or already ours: no squad to leave */ }
        ((void (__fastcall *)(void *, void *, void *))(DWORD_PTR)KLH_VA(KLCQ_RECRUIT))((void *)(DWORD_PTR)r->sc, 0, (void *)(DWORD_PTR)r->body); klcsq.nCalls++;
        return 1;
    }
    return 0;
}
static int klcsq_add_receiver(DWORD sc, DWORD s)      /* READ sq_add_receiver: the tail of 0x6213b0 as data */
{
    int n = klcsq_nrecv(klh_rd32(sc + 0x18)); DWORD cnt; BYTE one = 1;
    if (klcsq_in_list(sc, 0x18, 0x1c, s)) return 1;
    if (n >= 16) return 0;
    if (!klh_data((void *)(DWORD_PTR)(sc + 0x1c + 4 * n), &s, 4, "campsquad receiver")) return 0;
    cnt = (DWORD)(n + 1);
    if (!klh_data((void *)(DWORD_PTR)(sc + 0x18), &cnt, 4, "campsquad receiver count")) return 0;
    klh_data((void *)(DWORD_PTR)(sc + 0xcc), &one, 1, "campsquad sc+0xcc");
    return 1;
}
static void klcsq_scan(DWORD P, DWORD sc, DWORD now)
{
    DWORD sq = klh_rd32(sc + 0xa4), cand[16]; int nc = 0, nl, i, j;
    if (klcsq.recruit == KLCSQ_REC_OFF || now - klcsq.t0 < 1000 || (klcsq.recPoll && now - klcsq.recPoll < 500)) return;
    klcsq.recPoll = now;
    if (!sq || !klh_rd32(sq)) return;
    nl = (int)klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST)); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (i = 0; i < nl; i++) { DWORD s = klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST) + 4 + 4 * i), dup = 0; for (j = 0; j < nc; j++) dup |= cand[j] == s; if (s && !dup) cand[nc++] = s; }
    for (i = 0; i < nc && !klcsq.dead; i++) {
        DWORD s = cand[i], body = klcsq_body(s); struct klcsq_rec *r; struct klcsq_rec_in in; int cls, nodeOff = 0; struct klcsq_rj job;
        if (!body || klcsq_in_list(sc, 0x18, 0x1c, s) || klcsq_in_list(sc, 0x5c, 0x60, s)) continue;       /* a receiver, or parked by 0x523d10 */
        if (!(r = klcsq_rec(s))) continue;
        memset(&in, 0, sizeof in);
        in.mode = klcsq.recruit; in.able = klcsq_able(body, &nodeOff); in.nodeOff = nodeOff; in.q = klh_rd32(s + 0x4f4); in.sq = sq; in.own = klh_rd32(s + 0x69c); in.P = P;
        if (!r->seen || r->q != in.q) { r->seen = 1; r->q = in.q; r->qSince = now; }
        in.sinceQ = (long)(now - r->qSince); in.settleMs = klcsq.settleMs; in.adopt = klcsq.adopt; in.gateClosed = klcsq_blocked(P); in.squadBusy = 0;   /* squadBusy omitted: NOT ported */
        in.tries = r->tries; in.sinceTry = r->lastT ? (int)(now - r->lastT) : -1;
        cls = klcsq_recruit_class(&in);
        if (cls == KLCSQ_R_SKIP || cls == KLCSQ_R_SETTLE || cls == KLCSQ_R_WAIT) continue;
        if (cls == KLCSQ_R_LEAVE) { if (klcsq.log && r->heldQ != in.q) { r->heldQ = in.q; klog("campsquad: recruit hold merc %lu s=%08lx held by level squad %08lx: left to the level", (unsigned long)klh_rd32(s + 0x6e8), (unsigned long)s, (unsigned long)in.q); } continue; }
        if (cls == KLCSQ_R_GIVEUP) { if (r->tries++ == 8 && klcsq.log) klog("campsquad: recruit merc %lu s=%08lx: gave up after 8 tries this level", (unsigned long)klh_rd32(s + 0x6e8), (unsigned long)s); continue; }
        if (cls == KLCSQ_R_ADOPT) {
            if (klcsq_unsafe(s, body)) continue;
            if (klh_data((void *)(DWORD_PTR)(s + 0x69c), &P, 4, "campsquad adopt owner") && klcsq.log && r->heldQ != in.q) { r->heldQ = in.q; klog("campsquad: recruit adopt merc %lu s=%08lx held by level squad %08lx: owner 0 -> P (data only)", (unsigned long)klh_rd32(s + 0x6e8), (unsigned long)s, (unsigned long)in.q); }
            continue;
        }
        if (klcsq_unsafe(s, body)) { if (!r->announced++ && klcsq.log) klog("campsquad: recruit merc %lu s=%08lx skipped: unsafe pointers (+0x63c/+0x738/+0x6d8/vtable)", (unsigned long)klh_rd32(s + 0x6e8), (unsigned long)s); continue; }
        r->lastT = now ? now : 1; r->tries++;
        if (cls == KLCSQ_R_ADDRECV) {
            int ok = klcsq_add_receiver(sc, s);
            if (klcsq.log) klog("campsquad: recruit merc %lu s=%08lx in the player squad, no receiver -> %s (data; no Follow)", (unsigned long)klh_rd32(s + 0x6e8), (unsigned long)s, ok ? "added" : "NOT added (full / not writable)");
            continue;
        }
        job.sc = sc; job.sq = sq; job.s = s; job.body = body; job.P = P; job.kind = KLCSQ_R_RECRUIT;
        if (klfc_guard("campsquad recruit", klcsq_rec_do, &job) < 0) { klcsq.dead = 1; klog("campsquad: DISABLED (fault in the recruit)"); return; }
        if (klcsq.log) klog("campsquad: recruit merc %lu s=%08lx -> receivers %d, in list %d, squad ptr %08lx (player squad %08lx), try %d", (unsigned long)klh_rd32(s + 0x6e8), (unsigned long)s, klcsq_nr(sc), klcsq_in_list(sc, 0x18, 0x1c, s), (unsigned long)klh_rd32(s + 0x4f4), (unsigned long)sq, r->tries);
    }
}

/* ---- critical=clear (READ sq_crit_*) ---- */
static int klcsq_crit_build(void)
{
    static const struct { DWORD a; BYTE n, b[7]; } t[] = {
        { 0x8f44a0, 7, { 0x8a, 0x81, 0x13, 0x05, 0x00, 0x00, 0xc3 } }, { 0x725b32, 6, { 0x88, 0x81, 0x13, 0x05, 0x00, 0x00 } }, { 0x615e42, 5, { 0xb9, 0xd8, 0x8f, 0x54, 0x01 } },
        { 0x65a4fd, 6, { 0xff, 0x05, 0x44, 0xe6, 0xe0, 0x00 } }, { 0x5d5de7, 6, { 0xff, 0x05, 0x44, 0xe6, 0xe0, 0x00 } } };
    unsigned i;
    for (i = 0; i < sizeof t / sizeof t[0]; i++) if (!klb_same_code(t[i].a, t[i].b, t[i].n)) { klog("campsquad: critical: kl2 build mismatch at %08lx: critical=clear OFF", (unsigned long)t[i].a); return 0; }
    if (klh_rd32((DWORD_PTR)KLH_VA(KLE_SOLDIER_VT + 0xe4)) != 0x725b20 || klh_rd32((DWORD_PTR)KLH_VA(KLE_SOLDIER_VT + 0xe8)) != 0x8f44a0) { klog("campsquad: critical: ZSoldier vtable slots 57/58 differ: critical=clear OFF"); return 0; }
    return 1;
}
static void klcsq_crit(DWORD now)
{
    DWORD list[16], gs; int nl, n = 0, i, set = 0, cleared = 0;
    if (!klcsq.crit) return;
    if (klcsq.critBuild == 0) klcsq.critBuild = klcsq_crit_build() ? 1 : -1;
    if (klcsq.critBuild != 1) return;
    nl = (int)klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST)); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (i = 0; i < nl; i++) { DWORD s = klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_MERC_LIST) + 4 + 4 * i); BYTE f; if (s && klcsq_body(s) && klh_rd(s + KLCSQ_CRIT_OFF, &f, 1)) { list[n++] = s; set += klcsq_crit_needs_clear(f); } }
    gs = klh_rd32((DWORD_PTR)KLH_VA(KLCSQ_GS_COUNTER));
    { int due = klcsq_crit_due(klcsq.critGsSeen, klcsq.critGs, gs, set > 0, now - klcsq.critPoll); if (!klcsq.critGsSeen) klcsq.critGsSeen = 1; klcsq.critGs = gs; if (!due) return; }
    klcsq.critPoll = now;
    for (i = 0; i < n; i++) { BYTE f = 0, z = 0; if (klh_rd(list[i] + KLCSQ_CRIT_OFF, &f, 1) && klcsq_crit_needs_clear(f) && klh_data((void *)(DWORD_PTR)(list[i] + KLCSQ_CRIT_OFF), &z, 1, "campsquad critical flag")) cleared++; }   /* +0x512 stays as DD set it */
    if (cleared && klcsq.log) klog("campsquad: critical cleared on %d of %d listed mercs (gs %lu)", cleared, n, (unsigned long)gs);
}

static void klcsq_reset(DWORD P, DWORD sc, DWORD now)
{
    memset(klcsq.key, 0, sizeof klcsq.key); memset(klcsq.rec, 0, sizeof klcsq.rec);
    klcsq.nxWas = klcsq.pvWas = 1; klcsq.P = P; klcsq.sc = sc; klcsq.t0 = now; klcsq.recPoll = klcsq.critPoll = 0; klcsq.critGsSeen = 0; klcsq.refuseSet = 0;
}

static void klcampsquad_tick(int game_thread)
{
    DWORD now = GetTickCount(), P, sc; char scene[260], key[200];
    if (!klcsq.on || !game_thread || !klh_exe_ok || klcsq.dead) return;
    if (klh_rcb_ra != (DWORD_PTR)KLH_VA(KLFC_RCB_RA) || kl_online() || !klcmp_level_active()) { klcsq.active = 0; return; }
    if (!(P = klcsq_player()) || !(sc = klh_rd32(P + 0xcd0)) || klh_rd32(sc) != KLCQ_SC_VT || klh_rd32(sc + 4) != P) { klcsq.active = 0; return; }
    if (!klcsq_heads()) { klcsq.dead = 1; return; }
    if (!klcsq.active || klcsq.P != P || klcsq.sc != sc) { klcsq_reset(P, sc, now); klcsq.active = 1; if (klcsq.log) klog("campsquad: campaign level, player %08lx squad control %08lx: orders armed", (unsigned long)P, (unsigned long)sc); }
    if (!klcsq.refuseSet) {                          /* READ: the refusal flag is written once per level (a data write) */
        key[0] = 0; if (klh_scene(scene, sizeof scene)) klh_level_key(scene, key, sizeof key);
        klcsq.refuseSet = 1;
        if (klcsq_refuse_rule(klcsq.refuse, key)) { BYTE one = 1; if (klh_data((void *)(DWORD_PTR)(sc + 0xa0), &one, 1, "campsquad refusal flag") && klcsq.log) klog("campsquad: refusal rule (%s): sc+0xa0 := 1, the crew refuses orders here", key); }
    }
    klcsq_keys(P, sc, now);
    if (klcsq.dead) return;
    klcsq_scan(P, sc, now);
    if (!klcsq.dead) klcsq_crit(now);
}
#endif /* KLCAMPSQUAD_C */
