/* klshoppage_online.c - [ShopPage] OnlineSend=0|1 (default 0, "(recommended off until benched)"). Included by klshoppage.c after klshoppage_probe.c (uses kspp_*, kspg).
 * PAGE II ONLINE, STEP 2 = TRANSPORT ONLY (NOT RUN IN THE GAME, written 2026-10-27). NO game-state write: no money change, no pool relabel (that is step 4).
 *
 * A CLIENT pressing a page II row online (the place kspg_sel logs 'page2buy SWALLOWED') sends one request to the host through klnetchan.c, the way klhire_online.c
 * does it (knc_send, host = role 2 / client = role 3 checked on receipt, 6 s ack timeout, 'host not ready' when the rules / seat / table cannot be read).
 * The HOST judges and answers; the HOST pressing its own row judges locally and only logs.
 *
 * MESSAGE: channel type 'SHOPG' (5 bytes, KLNC_TYPE_MAX 9; the handler table has 16 slots). Payload (printable ASCII, <= 40 bytes):
 *   client -> host  'Q' s<seat> r<row> i<carrier item> n<round>             e.g. Qs2r5i41n1
 *   host -> all     'A' s<seat> r<row> i<carrier item> n<round> o<ok 0|1> m<reason code>     e.g. As2r5i41n1o1m0
 *   Every number is parsed with sscanf and range-checked: seat 0..15, row 0..KSPG_ROWS-1, item 0..63, round 0..99.
 *
 * HOST JUDGEMENT (each one a reason; first hit wins):
 *   m8 host not ready   the online rules / score object / the host's own page II pairs are unreadable ([ShopPage] Enable=1 needed on the host)
 *   m1 not shop phase   session state 0 or 0x19 (GUESS G1: the same 'not 0x19' idea as klhire_online.c; online state numbers unproven)
 *   m2 bad seat         seat is not a human seat in use, or the host's own seat in a REMOTE request
 *   m3 bad row          row outside the loaded pairs (kspg.p[row].ok == 0)
 *   m4 item differs     the client's carrier item is not the host's carrier item of that row (the tables differ)
 *   m5 one per round    this seat already had a page II gun accepted in this round (bookkeeping only; kept per round number)
 *   m6 money            the seat's money (klor_read on_money, needs [Online] Read=1) is below the row's price (kspg_price; 0 = unknown = not checked)
 *   (m7 reserved: money unreadable shows as m8 host not ready, klor_read needs [Online] Read=1)
 *   m0 ok
 *
 * LOG LINES (klog; 'shopg:'):
 *   shopg: on (OnlineSend=1, ...)                                          at start
 *   shopg: asked the host: seat S row R item I round N                    client, after the send
 *   shopg: seat S asked row R item I: ok | refused <why>                  host, for a remote request AND for its own press ("(host's own press, log only)" appended)
 *   shopg: host judged seat S row R item I: ok | refused <why>            client, on the answer
 *   shopg: no answer from the host about row R (6000 ms)                  client timeout
 *   shopg: refused: <why>                                                 client could not send (channel closed, no seat, still waiting, not online)
 * GUESS list: G1 shop-phase test (above); G2 the seat number in Q is trusted (friends / private match, like HIRE); G3 'round' = klor snapshot S+0x34c (0 = unread, the one-per-round
 * book then keys on 0).
 */
#ifndef KLSHOPPAGE_ONLINE_C
#define KLSHOPPAGE_ONLINE_C

#include "klnetchan_logic.h"                                     /* struct knc_msg (klnetchan.c, included later, includes the same guarded header) */
static unsigned knc_send(const char *type, const char *payload, int ent);
static int knc_want(const char *who);
static int knc_on(const char *type, void (*fn)(const struct knc_msg *m, int src));

static int kspg_price(int row);                                /* klshoppage.c, defined after this include */

#define KSPO_ASKMS 6000
#define KSPO_SEATS 16

enum { KSPO_OK = 0, KSPO_PHASE = 1, KSPO_SEAT = 2, KSPO_ROW = 3, KSPO_ITEM = 4, KSPO_ONCE = 5, KSPO_MONEY = 6, KSPO_MONEYX = 7, KSPO_NOTREADY = 8 };

static struct {
    int on, pend, pendRow, pendItem; DWORD pendAt, lastPress; int lastRow;
    int got[KSPO_SEATS];                          /* host: round number + 1 in which the seat's page II request was accepted (0 none); bookkeeping only */
    int told;
} kspo;

static const char *kspo_why(int c)
{
    switch (c) {
    case KSPO_OK: return "ok"; case KSPO_PHASE: return "not the shop phase"; case KSPO_SEAT: return "no such seat (or the host's own in a remote request)";
    case KSPO_ROW: return "no such page II row"; case KSPO_ITEM: return "carrier item differs (tables differ)"; case KSPO_ONCE: return "one page II gun per seat per round";
    case KSPO_MONEY: return "not enough money"; case KSPO_MONEYX: return "money unreadable ([Online] Read=1 needed on the host)"; case KSPO_NOTREADY: return "host not ready"; }
    return "?";
}

static int kspo_role(void)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598u)), role = 0;
    return sm && klh_rd(sm + 0x54, &role, 4) ? (int)role : 0;
}

static int kspo_state(void)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598u)), st = 0;
    return sm && klh_rd(sm + 0x70, &st, 4) ? (int)st : 0;
}

static int kspo_item_of(int row)
{
    if (row < 0 || row >= KSPG_ROWS) return -1;
    return (int)klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * (DWORD)row);
}

/* the host's verdict on (seat, row, item, round). remote = the request came over the wire. Returns a KSPO_ reason. NO game write. */
static int kspo_judge(int seat, int row, int item, int round, int remote, int record)
{
    int c = KSPO_NOTREADY;
    static struct klor_snap sn;
    __try {
        int i, found = 0; DWORD price;
        klor_noev = 1; i = klor_read(&sn, kspp_loc()); klor_noev = 0;
        if (!i || !sn.ok || !kspg.have) { c = KSPO_NOTREADY; goto done; }
        { int st = kspo_state(); if (st == 0 || st == 0x19) { c = KSPO_PHASE; goto done; } }          /* G1 */
        if (seat < 0 || seat >= KSPO_SEATS) { c = KSPO_SEAT; goto done; }
        for (i = 0; i < sn.n && i < KLOR_MAX; i++) if (sn.r[i].used && !sn.r[i].bot && sn.r[i].seat == seat) found = 1;
        if (!found || (remote && seat == sn.local)) { c = KSPO_SEAT; goto done; }
        if (row < 0 || row >= KSPG_ROWS || !kspg.p[row].ok) { c = KSPO_ROW; goto done; }
        if (item != kspo_item_of(row)) { c = KSPO_ITEM; goto done; }
        if (kspo.got[seat] == round + 1) { c = KSPO_ONCE; goto done; }
        price = (DWORD)kspg_price(row);
        if (price) {
            if ((unsigned long)sn.b.on_money[seat] < (unsigned long)price) { c = KSPO_MONEY; goto done; }
        }
        c = KSPO_OK;
        if (record) kspo.got[seat] = round + 1;
    done: ;
    } __except (1) { klor_noev = 0; c = KSPO_NOTREADY; }
    return c;
}

static int kspo_round(void)
{
    static struct klor_snap sn; int r = 0;
    __try { klor_noev = 1; if (klor_read(&sn, kspp_loc()) && sn.ok && klor_round_ok(sn.round, sn.rounds)) r = sn.round; klor_noev = 0; } __except (1) { klor_noev = 0; }
    return r < 0 || r > 99 ? 0 : r;
}

static int kspo_myseat(void)
{
    static struct klor_snap sn; int s = -1;
    __try { klor_noev = 1; if (klor_read(&sn, kspp_loc()) && sn.ok && sn.local >= 0 && sn.local < KSPO_SEATS) s = sn.local; klor_noev = 0; } __except (1) { klor_noev = 0; }
    return s;
}

/* HOST: 'Q' from a client */
static void kspo_on_ask(const struct knc_msg *m)
{
    int seat = -1, row = -1, item = -1, round = -1, why; char pay[64];
    if (kspo_role() != 2 || m->role != 3) return;
    if (sscanf(m->payload + 1, "s%dr%di%dn%d", &seat, &row, &item, &round) < 4) return;
    if (seat < 0 || seat >= KSPO_SEATS || row < 0 || row >= KSPG_ROWS || item < 0 || item > 63 || round < 0 || round > 99) return;
    why = kspo_judge(seat, row, item, kspo_round(), 1, 1);          /* the host's own round: the client's n is only echoed back */
    klog("shopg: seat %d asked row %d item %d: %s%s", seat, row, item, why ? "refused " : "ok", why ? kspo_why(why) : "");
    snprintf(pay, sizeof pay, "As%dr%di%dn%do%dm%d", seat, row, item, round, why == KSPO_OK, why);
    knc_send("SHOPG", pay, -1);
}

/* CLIENT: 'A' from the host */
static void kspo_on_answer(const struct knc_msg *m)
{
    int seat = -1, row = -1, item = -1, round = -1, ok = 0, why = 0;
    if (kspo_role() != 3 || m->role != 2) return;
    if (sscanf(m->payload + 1, "s%dr%di%dn%do%dm%d", &seat, &row, &item, &round, &ok, &why) < 6) return;
    if (seat < 0 || seat >= KSPO_SEATS || row < 0 || row >= KSPG_ROWS || item < 0 || item > 63 || why < 0 || why > 9) return;
    if (seat != kspo_myseat()) return;
    if (!kspo.pend || kspo.pendRow != row) return;                     /* late or not asked: a judgement with nothing waiting is ignored */
    kspo.pend = 0;
    klog("shopg: host judged seat %d row %d item %d: %s%s", seat, row, item, ok ? "ok" : "refused ", ok ? "" : kspo_why(why));
}

static void kspo_on_msg(const struct knc_msg *m, int src)
{
    (void)src;
    if (!kspo.on || !m) return;
    if (m->payload[0] == 'Q') kspo_on_ask(m); else if (m->payload[0] == 'A') kspo_on_answer(m);
}

/* from kspg_sel's swallowed page II buy (online, row = the page II row) */
static void kspo_press(int row)
{
    int seat, item, role, round, why; char pay[64]; DWORD now = GetTickCount();
    if (!kspo.on || !kl_online()) return;
    if (row == kspo.lastRow && now - kspo.lastPress < 800) return;     /* BuyWeapon + BuyWeaponDialogVoodoo for one click */
    kspo.lastRow = row; kspo.lastPress = now;
    role = kspo_role(); item = kspo_item_of(row); round = kspo_round();
    if (row < 0 || row >= KSPG_ROWS || item < 0 || item > 63) { klog("shopg: refused: row %d / carrier item %d out of range", row, item); return; }
    seat = kspo_myseat();
    if (seat < 0) { klog("shopg: refused: own seat unknown (not in an online FA round)"); return; }
    if (role == 2) {                                                     /* the host's own press: judge here, log only (step 4 will act) */
        why = kspo_judge(seat, row, item, round, 0, 0);
        klog("shopg: seat %d asked row %d item %d: %s%s (host's own press, log only)", seat, row, item, why ? "refused " : "ok", why ? kspo_why(why) : "");
        return;
    }
    if (role != 3) { klog("shopg: refused: no client / host role (%d)", role); return; }
    if (kspo.pend && now - kspo.pendAt < KSPO_ASKMS) { klog("shopg: refused: still waiting for the host's answer about row %d", kspo.pendRow); return; }
    snprintf(pay, sizeof pay, "Qs%dr%di%dn%d", seat, row, item, round);
    if (!knc_send("SHOPG", pay, -1)) { klog("shopg: refused: the message channel is not open (no session / [NetChan] off), nothing sent"); return; }
    kspo.pend = 1; kspo.pendRow = row; kspo.pendItem = item; kspo.pendAt = now;
    klog("shopg: asked the host: seat %d row %d item %d round %d", seat, row, item, round);
}

static void kspo_tick(void)
{
    if (!kspo.on || !kspo.pend) return;
    if (GetTickCount() - kspo.pendAt >= KSPO_ASKMS) { klog("shopg: no answer from the host about row %d (%d ms)", kspo.pendRow, KSPO_ASKMS); kspo.pend = 0; }
}

static void kspo_init(void)
{
    kspo.on = GetPrivateProfileIntA("ShopPage", "OnlineSend", 0, klh_ini) != 0;
    if (!kspo.on) return;
    knc_want("shopg");
    knc_on("SHOPG", kspo_on_msg);
    klog("shopg: on ([ShopPage] OnlineSend=1, recommended off until benched): a client's page II press is sent to the host, the host judges and logs; NO game-state write (step 2). Needs [NetChan], [ShopPage] Enable=1 + OnlineLook=1 on both, [Online] Read=1 on the host");
}

#endif /* KLSHOPPAGE_ONLINE_C */
