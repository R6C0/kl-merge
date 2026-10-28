/*
 * kllootsync.c - [BotFill] OnlineLootSync=1: what the AI heisters (bots) looted, shown on every screen (re/bot_parity_plan_1028.md, build plan 3).
 * Online only the HOST knows it (klbotfill.c OnlineTactics: klbf_ob[].tally / phase, the OnlineBank ledger); a client sees no loot for the bots. The host sends the state in a
 * small hook-to-hook 'KLSYB' packet on the KLSY socket (UDP 27415, same path as klcrewlook.c's 'KLSYL'; layout in kllootsync_logic.h) about once a second and on every change;
 * every seat (the host through the same code) shows it as ONE LINE on the game's own announcement element (klannounce.c, its own text slot KLAN_LOOT).
 * Part of KLHook (included by klhook.c AFTER klsync.c, klcrewlook.c, klannounce.c; SHIP and TEST alike). Off unless [BotFill] OnlineLootSync=1. Never runs in Arcade (online host/client, mode 4 only).
 * No .text patch, no game state written: the game's score, scoreboard and Sharable money are NOT touched, OnlineBankCredit is not touched. Host reads klbf_ob only (host-only, as klbf_ot_run).
 *
 * HUD: klhud_board2.c / klhud_board.c / klhud.c draw the crew list and the money box with the game's own text elements that exist per crew record; the bots have no crew records online
 * (klbotfill.c), so no row of theirs can be added there. FALLBACK as the task allowed: the announcement element (the line at the top of the HUD, as klshoppage.c's hints). It is shown
 * only when no stock message is on screen, at most once per 4 s and only when the numbers changed (then it waits for a free element). GUESS: a one-line text is enough for a bench; a per-bot row needs the unproven crew-record path.
 * "total" = every bot's tally (carrying + aboard + dead bots' loot); "carried" = still carried by a living bot; "banked" = aboard the van; dead bots keep their last tally (state 'down').
 *
 * LOG
 *   botfill: lootsync: sent total=%d taken=%d carried=%d banked=%d bots=%d round=%u (%d bytes, sendto %d)   host, on change (at most every 2 s)
 *   botfill: lootsync: round summary FINAL total=%d carried=%d banked=%d taken=%d (hook tally of live slots %d) round=%u   host, at klbf_ot_summary
 *   sync: loot total=%d carried=%d banked=%d bots=%d round=%u T=%lu%s from a.b.c.d      client, on change
 *   botfill: lootsync: shown: '%s'   every seat, when the line goes to the HUD
 */
#ifndef KLLOOTSYNC_C
#define KLLOOTSYNC_C

#include "kllootsync_logic.h"

static struct {
    DWORD sm, collectAt, sendAt, logAt, shownAt, live; unsigned round, sig, sentSig, shownSig, heldSig, heldRound, heldT, srcAddr;
    int role, host, srcSet, nsent, final, toldFull;
    struct klls_pk cur, held;
    struct { DWORD actor; int digit, slot, state, amt; } e[KLLS_MAXN];
    int ne, nsum_taken;
} klls_t;

static unsigned klls_sig_of(const struct klls_pk *k)
{
    unsigned h = 2166136261u; int i;
    h = (h ^ (unsigned)k->carried) * 16777619u; h = (h ^ (unsigned)k->banked) * 16777619u; h = (h ^ (unsigned)k->n) * 16777619u;
    for (i = 0; i < k->n; i++) { h = (h ^ (unsigned)k->r[i].amt) * 16777619u; h = (h ^ (unsigned)(k->r[i].state | k->r[i].digit << 4 | k->r[i].slot << 8)) * 16777619u; }
    return h;
}

static void klls_reset(void)
{
    if (!klls_t.sm && !klls_t.round && !klls_t.heldRound) return;
    memset(&klls_t, 0, sizeof klls_t);
}

/* HOST: read klbf_ob (reads only) into klls_t.cur. A bot whose slot was freed (dead / gone) keeps its last tally as 'down' unless it was aboard. */
static void klls_collect(DWORD sm)
{
    int i, j, grabs = 0, live = 0; struct klls_pk *k = &klls_t.cur;
    if (klls_t.sm != sm || klls_t.round != (unsigned)klbf_ot_rounds) { memset(klls_t.e, 0, sizeof klls_t.e); klls_t.ne = 0; klls_t.sm = sm; klls_t.round = (unsigned)klbf_ot_rounds; klls_t.sentSig = 0; klls_t.final = 0; klls_t.toldFull = 0; }
    for (j = 0; j < klls_t.ne; j++) if (klls_t.e[j].state != KLLS_ST_BOARD) klls_t.e[j].state = KLLS_ST_DEAD;      /* until the walk below finds it again */
    for (i = 0; i < KLBF_OT_BOTS; i++) {
        DWORD a = klbf_ob[i].actor; char nm[28], dg;
        if (!a) continue;
        grabs += klbf_ob[i].grabs; live += klbf_ob[i].tally;
        for (j = 0; j < klls_t.ne && klls_t.e[j].actor != a; j++) ;
        if (j == klls_t.ne) {
            if (klls_t.ne >= KLLS_MAXN) { if (!klls_t.toldFull++) klog("botfill: lootsync: more than %d bots: the others are not sent (their loot is in no list)", KLLS_MAXN); continue; }
            memset(&klls_t.e[j], 0, sizeof klls_t.e[j]); klls_t.e[j].actor = a; klls_t.ne++;
        }
        if (!klls_t.e[j].digit) { klbf_lk_name(a, nm, &dg); if (dg >= '1' && dg <= '9') klls_t.e[j].digit = dg - '0'; }      /* group digit of Glazer_Bodyguard_0N; 0 = unreadable (the slot number shows) */
        klls_t.e[j].slot = i; klls_t.e[j].amt = klbf_ob[i].tally > 0 ? klbf_ob[i].tally : 0; klls_t.e[j].state = klbf_ob[i].phase == 3 ? KLLS_ST_BOARD : KLLS_ST_CARRY;
    }
    memset(k, 0, sizeof *k);
    k->round = klls_t.round; k->n = klls_t.ne;
    for (j = 0; j < klls_t.ne; j++) {
        k->r[j].digit = klls_t.e[j].digit; k->r[j].slot = klls_t.e[j].slot; k->r[j].state = klls_t.e[j].state; k->r[j].amt = klls_t.e[j].amt;
        if (klls_t.e[j].state == KLLS_ST_CARRY) k->carried += klls_t.e[j].amt; else if (klls_t.e[j].state == KLLS_ST_BOARD) k->banked += klls_t.e[j].amt;
    }
    klls_t.nsum_taken = grabs; klls_t.live = (DWORD)live;
    klls_t.sig = klls_sig_of(k); klls_t.host = 1;
}

static int klls_total(const struct klls_pk *k) { int j, t = 0; for (j = 0; j < k->n; j++) t += k->r[j].amt; return t; }

static void klls_send(DWORD now, int force)
{
    unsigned char pk[KLLS_HDR + KLLS_MAXN * KLLS_REC]; klsy_sin a; int len, r, changed;
    if (!klls_t.host || !klls_t.round || !klsy.sock) return;
    changed = klls_t.sig != klls_t.sentSig;
    if (!force && !(changed && (LONG)(now - klls_t.sendAt) >= 250) && (LONG)(now - klls_t.sendAt) < 1000) return;
    klls_t.cur.T = (unsigned)klsy_T(); klls_t.cur.flags = klls_t.final ? 1 : 0;
    if (!(len = klls_encode(pk, sizeof pk, &klls_t.cur))) return;
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
    r = klsy.sendto(klsy.sock, (char *)pk, len, 0, &a, sizeof a);
    klls_t.sendAt = now ? now : 1; klls_t.nsent++;
    if (changed || !klls_t.logAt) {
        klls_t.sentSig = klls_t.sig;
        if (!klls_t.logAt || (LONG)(now - klls_t.logAt) >= 2000) { klls_t.logAt = now ? now : 1; klog("botfill: lootsync: sent total=%d taken=%d carried=%d banked=%d bots=%d round=%u (%d bytes, sendto %d)", klls_total(&klls_t.cur), klls_t.nsum_taken, klls_t.cur.carried, klls_t.cur.banked, klls_t.cur.n, klls_t.cur.round, len, r); }
    }
}

/* the host's round summary (klbotfill.c klbf_ot_summary, before the tally is cleared): the final list goes out three times (UDP) and its total is logged for the bench */
static void klls_summary(void)
{
    int i;
    if (!klls_on || !klbf_ot_in || !klbf_ot_sm) return;
    klls_collect((DWORD)klbf_ot_sm); klls_t.final = 1;
    for (i = 0; i < 3; i++) klls_send(GetTickCount(), 1);
    klog("botfill: lootsync: round summary FINAL total=%d carried=%d banked=%d taken=%d (hook tally of live slots %d) round=%u", klls_total(&klls_t.cur), klls_t.cur.carried, klls_t.cur.banked, klls_t.nsum_taken, (int)klls_t.live, klls_t.cur.round);
    klls_t.host = 0;      /* nothing more is sent until the next round's collect */
}

/* CLIENT: a 'KLSYB' packet (klsync.c's drain, game thread) */
static void klls_rx(const char *pk, int len, DWORD now, unsigned long from)
{
    struct klls_pk k; DWORD sm, state = 0;
    if (len < KLLS_HDR || memcmp(pk, "KLSYB", 5)) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x70, &state, 4) || state < 0x13 || state > 0x1f) return;      /* not in a round: a late packet of the last one */
    if (klls_t.host) return;      /* this seat is the sender */
    if (!klls_decode((const unsigned char *)pk, len, &k)) { static int told; if (told++ < 3) klog("sync: loot: a KLSYB packet of %d bytes was refused (out of range)", len); return; }
    if (klsy.srcSet && from != klsy.srcAddr) return;      /* the host that sent the round's first valid list */
    if (klls_t.sm != sm) { memset(&klls_t, 0, sizeof klls_t); klls_t.sm = sm; }
    if (klls_t.srcSet && from != klls_t.srcAddr) return;
    if (!klls_newer(k.round, k.T, klls_t.heldRound, klls_t.heldT)) return;
    if (!klls_t.srcSet) { klls_t.srcSet = 1; klls_t.srcAddr = (unsigned)from; }
    klls_t.held = k; klls_t.heldRound = k.round; klls_t.heldT = k.T; klls_t.role = 3;
    klls_t.heldSig = klls_sig_of(&k);
    if (klls_t.heldSig != klls_t.sentSig || (k.flags & 1)) {      /* sentSig = the last signature logged on a client */
        klls_t.sentSig = klls_t.heldSig;
        klog("sync: loot total=%d carried=%d banked=%d bots=%d round=%u T=%lu%s from %lu.%lu.%lu.%lu", klls_total(&k), k.carried, k.banked, k.n, k.round, (unsigned long)k.T, (k.flags & 1) ? " FINAL" : "", from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24);
    }
    (void)now;
}

/* every seat: put the held / own list on the HUD line */
static void klls_show(DWORD now, const struct klls_pk *k, unsigned sig)
{
    char t[240]; DWORD el; int any = 0, j;
    for (j = 0; j < k->n; j++) if (k->r[j].amt) any = 1;
    if (!any || sig == klls_t.shownSig) return;
    if (klls_t.shownAt && (LONG)(now - klls_t.shownAt) < 4000) return;
    if (!(el = klan_element()) || klan_busy(el)) return;      /* waits for a free element; the newest numbers go out then */
    klls_text(t, sizeof t, k);
    if (klan_say_el(el, t, 6.0f, KLAN_LOOT)) { klls_t.shownSig = sig; klls_t.shownAt = now ? now : 1; klog("botfill: lootsync: shown: '%s'", t); }
}

static void klls_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0;
    if (!klls_on || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klls_reset(); return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if ((role != 2 && role != 3) || mode != 4 || state < 0x13 || state > 0x1f) { klls_reset(); return; }      /* Arcade (offline) never gets here; the next round starts clean */
    if (role == 2) {
        if (!klbf_ot || !klbf_ot_in || (DWORD)klbf_ot_sm != sm || state != KLB_ROUND) return;      /* the gates of klbf_ot_run */
        if ((LONG)(now - klls_t.collectAt) >= 500) { klls_t.collectAt = now ? now : 1; klls_collect(sm); }
        klls_show(now, &klls_t.cur, klls_t.sig);
    } else if (klls_t.heldRound) klls_show(now, &klls_t.held, klls_t.heldSig);
}

#endif /* KLLOOTSYNC_C */
