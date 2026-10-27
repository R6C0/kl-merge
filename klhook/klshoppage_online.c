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
 *   m6 money            the seat's SHOP money (the stock getters 0x622e10 TotalLootMoney + 0x639c10 TotalRewardMoney on S = [rules+0x2c], re/shop_hire.md 8.2; NOT klor's
 *                       on_money, which is the in-round carried money) is below the row's price (kspg_price; 0 = unknown = not checked)
 *   m7 money unreadable the getters cannot be read (rules / score object not as known, or the code bytes of the getters differ: kspo_shopmoney)
 *                       (the seat list above still comes from klor_read, so [Online] Read=1 stays needed on the host for the judge as a whole, not for the money)
 *   m0 ok
 *
 * LOG LINES (klog; 'shopg:'):
 *   shopg: on (OnlineSend=1, ...)                                          at start
 *   shopg: asked the host: seat S row R item I round N                    client, after the send
 *   shopg: seat S asked row R item I: ok | refused <why>                  host, for a remote request AND for its own press ("(host's own press, log only)" appended)
 *   shopg: host judged seat S row R item I: ok | refused <why>            client, on the answer
 *   shopg: no answer from the host about row R (6000 ms)                  client timeout
 *   shopg: refused: <why>                                                 client could not send (channel closed, no seat, still waiting, not online)
 *
 * STEP 4 = APPLY ([ShopPage] OnlineApply=1, default 0, "(recommended off until benched)", needs OnlineSend=1 + Enable=1; written 2026-10-27, NOT RUN IN THE GAME).
 * The money and the carried row are the STOCK path's, so Arcade and online behave alike: an approved page II buy is the stock BuyWeapon of the row's CARRIER
 * (same price, same rank; Cl commit 0x682b60 forwards to the host, Sv commit 0x55d3e0 charges the score and stores the rows; the host judged the price first), and the
 * page II gun reaches the player by the Arcade POOL RELABEL (klshoppage.c kspg_enforce / kspg_repark: carrier's stock entries parked, ours free) on every peer.
 *   host press   kspg_sel -> kspo_gate: judge (the same m-codes, no per-round limit, m9 = carried already / a buy in flight), ok -> book + 'A' o1 broadcast, the
 *                stock handler runs (BuyWeaponDialogVoodoo, then BuyWeapon via okRow). Refused -> swallowed, nothing changes.
 *   client press kspg_sel -> kspo_gate -> kspo_press (ask, swallow). The host's 'A' o1 -> every peer books (seat,row); the buyer's tick fires the stock BuyWeapon on the
 *                live selector (kspg_applybuy). 'A' o0 -> nothing changes.
 *   book         counts (kspo_wantB) only once the seat's carried row (rules getters +0x104/+0x108) equals the page II row = the stock buy really landed; dropped when
 *                replaced, when the session ends, or after 30 s unseen.
 * LIMITS: wantB is per carrier row, not per seat: while any seat holds a page II gun for a carrier, every hand-out of that carrier item (other humans, bots) gets the
 * page II gun (up to 8 made objects). A refusal is only in the log (the shop shows nothing), the confirm dialog is skipped on a client (the buy is fired as BuyWeapon).
 * GUESS list: G1 shop-phase test (above); G2 the seat number in Q is trusted (friends / private match, like HIRE); G3 'round' = klor snapshot S+0x34c (0 = unread, the one-per-round
 * book then keys on 0).
 * STEP 4 GUESSES: G4 the client's stock commit 0x682b60 -> 0x8e3a40 reaches the host's Sv commit 0x55d3e0 (charge + rows), as a stock page I buy does (P2P3C pressed one,
 * money not yet seen to move: round 1, $0); G5 the klor seat number is the record index of the rules getters +0x104/+0x108 (and of the Q/A messages); G6 the hand-out takes
 * a free pool entry by label (carrier item) so parking the carrier's stock entries and freeing ours gives the page II gun (Arcade's proven recipe, unproven online);
 * G7 a CLIENT's own pool is what its local hand-out reads (probe: clients build their own pool, 0x78a8d0 gated on [session+0x5c]==4), so every peer relabels its own copy.
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
#define KSPO_MONEYSEATS 12                          /* the shop money getters cover seats 0..11 only */

enum { KSPO_OK = 0, KSPO_PHASE = 1, KSPO_SEAT = 2, KSPO_ROW = 3, KSPO_ITEM = 4, KSPO_ONCE = 5, KSPO_MONEY = 6, KSPO_MONEYX = 7, KSPO_NOTREADY = 8, KSPO_CARRIED = 9 };

#define KSPO_BOOKMS 30000                         /* STEP 4: a booked buy that never shows in the rules is dropped after this */

static struct {
    int on, pend, pendRow, pendItem; DWORD pendAt, lastPress; int lastRow;
    int got[KSPO_SEATS];                          /* host: round number + 1 in which the seat's page II request was accepted (0 none); bookkeeping only (step 2) / seen buys (step 4) */
    int told;
    /* STEP 4 (OnlineApply): the book of approved page II buys, one per seat, the same on every peer (the host's 'A' answer is broadcast).
       bk[seat] = page II row + 1 (0 none). bkSeen: the stock buy of the carrier showed in the rules' carried rows (the getters the stock commit 0x55d3e0 uses). */
    int bk[KSPO_SEATS], bkSeen[KSPO_SEATS]; DWORD bkAt[KSPO_SEATS], bkTick;
    int okRow; DWORD okAt;                        /* row + 1 whose stock buy may pass kspg_sel's gate (approved; consumed by the BuyWeapon) */
    DWORD bmN, bmAt; int bmDone;                  /* [Bench] ShopMoney: target, stay entry, done this stay */
    int doRow; DWORD doAt;                        /* client: row + 1 approved by the host, the stock buy is fired from the tick */
} kspo;

static int kspg_applybuy(int row);                             /* klshoppage.c, after this include: fires the stock buy of the carrier row */

static const char *kspo_why(int c)
{
    switch (c) {
    case KSPO_OK: return "ok"; case KSPO_PHASE: return "not the shop phase"; case KSPO_SEAT: return "no such seat (or the host's own in a remote request)";
    case KSPO_ROW: return "no such page II row"; case KSPO_ITEM: return "carrier item differs (tables differ)"; case KSPO_ONCE: return "one page II gun per seat per round";
    case KSPO_MONEY: return "not enough money"; case KSPO_MONEYX: return "money unreadable (shop money getters / score object not as known)"; case KSPO_NOTREADY: return "host not ready";
    case KSPO_CARRIED: return "the seat already carries that row (or has a page II buy still pending)"; }
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

/* STEP 4: the rows a seat carries, read with the rules' own getters (vtable +0x104 primary, +0x108 secondary: the ones the stock commit 0x55d3e0 compares the
   new rows with; Sv and Cl share 0x5f1730 / 0x691340, thiscall(rules, byte seat) ret 4 -> signed byte row, -1 = none / no such record).
   GUESS: the seat number of klor is the record index of these getters ('slot k = seat k', re/open_work_log.md 07:45). Returns 0 when unreadable (rows -2). Reads only. */
typedef signed char (__fastcall *kspo_get_t)(void *rules, void *edx, int seat);
static int kspo_carried(int seat, int *r0, int *r1)
{
    DWORD gs, rules, vt, f0, f1; char kind[9]; int ok = 0;
    *r0 = *r1 = -2;
    if (seat < 0 || seat >= KSPO_SEATS) return 0;
    gs = klh_rd32((DWORD_PTR)KLH_VA(KLS_SETTINGS)); rules = gs ? klh_rd32(gs + 0x54) : 0;
    if (!rules || !(vt = klh_rd32(rules)) || (!KLH_RULES_SV_OK(vt) && !KLH_RULES_CL_OK(vt))) return 0;
    f0 = klh_rd32(vt + 0x104); f1 = klh_rd32(vt + 0x108);
    if (!f0 || !f1 || klh_kind((const void *)KLH_VA(f0), 4, kind) != 'x' || klh_kind((const void *)KLH_VA(f1), 4, kind) != 'x') return 0;
    __try {
        *r0 = (int)((kspo_get_t)(DWORD_PTR)f0)((void *)(DWORD_PTR)rules, 0, seat);
        *r1 = (int)((kspo_get_t)(DWORD_PTR)f1)((void *)(DWORD_PTR)rules, 0, seat);
        ok = 1;
    } __except (1) { *r0 = *r1 = -2; ok = 0; }
    return ok;
}

/* SHOP MONEY (re/shop_hire.md 8.2 + 8.5, read from kl2.exe 2026-10-27). S = [rules+0x2c] (vtable 0xbd5184), 12 seats. Money of a seat = first store (S+0x1b8 + 4*seat, TotalLootMoney,
   getter 0x622e10 -> 0x5f3b70) + second store (S+0x1e8 + 4*seat, TotalRewardMoney, getter 0x639c10 -> 0x411fe0), both thiscall(S, seat) ret 4. Same getters and guard idea as klhire_online.c
   (klhro_money; that file is included AFTER this one, so this is a small local copy). Returns 0 = unreadable / code differs. Reads only. */
static int kspo_score(DWORD *rules, DWORD *score)
{
    DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(KLS_SETTINGS)), r, sc, vt;
    if (!gs || !(r = klh_rd32(gs + 0x54)) || !(vt = klh_rd32(r)) || !(KLH_RULES_SV_OK(vt) || KLH_RULES_CL_OK(vt))) return 0;
    if (!(sc = klh_rd32(r + 0x2c)) || klh_rd32(sc) != 0xbd5184) return 0;
    if (rules) *rules = r;
    if (score) *score = sc;
    return 1;
}

static int kspo_money_code_ok(void)
{
    static const BYTE g1[] = { 0x83, 0xc1, 0x58, 0xe9 };
    static int ok = -1;
    if (ok < 0) {
        ok = klc_same_code(0x622e10, g1, sizeof g1) && klc_same_code(0x639c10, g1, sizeof g1);
        if (!ok) klog("shopg: the money getters 0x622e10 / 0x639c10 are not the ones this build knows (other kl2.exe?): the page II judge reports 'money unreadable'");
    }
    return ok;
}

static int kspo_shopmoney(int seat, DWORD *first, DWORD *second)
{
    DWORD sc = 0;
    if (seat < 0 || seat >= 12 || !kspo_score(0, &sc) || !kspo_money_code_ok()) return 0;
    __try {
        *first = ((DWORD (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(0x622e10))((void *)(DWORD_PTR)sc, 0, seat);
        *second = ((DWORD (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(0x639c10))((void *)(DWORD_PTR)sc, 0, seat);
    } __except (1) { return 0; }
    return 1;
}

/* [Bench] ShopMoney=<n> (BENCH ONLY, default 0 = off, "(bench only, recommended off)"; written 2026-10-27, NOT RUN IN THE GAME). HOST only (Sv rules), once per shop stay
   (kspo_benchmoney, called from klshoppage_tick while the shop gate is 1): every seat in use whose shop money (getter sum) is below n is raised to n.
   HOW TO ADD, from the disassembly of kl2.exe (re/shop_hire.md 8.5): the SPENDERS cannot add. 0x6b1910 (first store) and 0x7f6950 (second) call 0x8bb7b0 / 0x6406f0, which do
   'cmp esi,eax ; jbe sub ; mov [edx],0' = an UNSIGNED compare, an amount above the store (a negative one included) CLAMPS the store to 0. So the add is the game's own pair
   0x6cfdb0 (AddLootMoney, first store) / 0x497ce0 (AddRewardMoney, second): same wrapper as the spenders (sub esp,8 / set seat byte via 0x7dea30 / the array op / 0x942b20 notify
   with the dirty mask / 0x57aca0), whose array op is 0x688160 'add [ecx+eax*4+0x160],edx ; or word [ecx+0x1fe],0x80' (0x453cd0 adds to +0x190 with mask 1). thiscall(S, seat, amount) ret 8,
   so the new money replicates exactly like a spend. Only 0x6cfdb0 is used (the first store is the one the getters sum first). The guard compares the wrapper's first 8 bytes and the
   'call 0x688160' at 0x6cfdcf. n is capped at 99,999,999. */
static int kspo_addcode_ok(void)
{
    static const BYTE a1[] = { 0x83, 0xec, 0x08, 0x53, 0x8b, 0x5c, 0x24, 0x10 }, a2[] = { 0xe8, 0x8c, 0x83, 0xfb, 0xff };
    static int ok = -1;
    if (ok < 0) {
        ok = klc_same_code(0x6cfdb0, a1, sizeof a1) && klc_same_code(0x6cfdcf, a2, sizeof a2);
        if (!ok) klog("bench: ShopMoney refused: 0x6cfdb0 (AddLootMoney) is not the routine this build knows (other kl2.exe?); nothing written");
    }
    return ok;
}

static void kspo_benchmoney(void)
{
    DWORD rules = 0, sc = 0, n = 0, fr; int seat, wrote = 0, st = kspo_state();
    if (!kspo.bmN || kspo.bmDone || st == 0 || st == 0x19 || !kspo_score(&rules, &sc) || !KLH_RULES_SV_OK(klh_rd32(rules))) return;    /* host only, shop phase */
    if (!kspo.bmAt) kspo.bmAt = GetTickCount() ? GetTickCount() : 1;
    if (GetTickCount() - kspo.bmAt < 3000) return;                      /* let the shop come up first (as OnlineTestBuy's 3 s) */
    if (!klh_rd(rules + 0x14, &n, 4) || n == 0 || n > 16 || !kspo_money_code_ok() || !kspo_addcode_ok()) { kspo.bmDone = 1; return; }
    fr = klh_rd32(rules + 0xc);
    for (seat = 0; seat < KSPO_MONEYSEATS && (DWORD)seat < n; seat++) {
        DWORD m1 = 0, m2 = 0, m3 = 0, m4 = 0; BYTE b = 1;
        if (!fr || !klh_rd(fr + seat, &b, 1) || b) continue;            /* seat not in use */
        if (!kspo_shopmoney(seat, &m1, &m2)) continue;
        if ((unsigned __int64)m1 + m2 >= (unsigned __int64)kspo.bmN) continue;
        __try { ((void (__fastcall *)(void *, void *, int, DWORD))(DWORD_PTR)KLH_VA(0x6cfdb0))((void *)(DWORD_PTR)sc, 0, seat, kspo.bmN - (m1 + m2)); } __except (1) { klog("bench: ShopMoney seat %d: the add faulted", seat); continue; }
        kspo_shopmoney(seat, &m3, &m4);
        klog("bench: ShopMoney seat %d %lu -> %lu", seat, (unsigned long)(m1 + m2), (unsigned long)(m3 + m4));
        wrote++;
    }
    if (wrote) kspo.bmDone = 1;                                          /* once per stay, but retry until at least one seat was written */
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
        if (kspg.apply) {   /* STEP 4: Arcade lets the player buy again, so no per-round limit; but one buy in flight per seat, and nothing to buy when the row is carried */
            int c0, c1;
            if (kspo.bk[seat] && !kspo.bkSeen[seat] && GetTickCount() - kspo.bkAt[seat] < KSPO_BOOKMS) { c = KSPO_CARRIED; goto done; }
            if (kspo_carried(seat, &c0, &c1) && (c0 == row || c1 == row)) { c = KSPO_CARRIED; goto done; }
        } else if (kspo.got[seat] == round + 1) { c = KSPO_ONCE; goto done; }
        price = (DWORD)kspg_price(row);
        {
            DWORD m1 = 0, m2 = 0;                                   /* the shop money: stock getters' sum, like the stock handler 0x55d3e0 compares (8.2) */
            if (!price) { c = KSPO_MONEYX; goto done; }             /* unknown price: the stock handler may refuse silently, so do not approve */
            if (!kspo_shopmoney(seat, &m1, &m2)) { c = KSPO_MONEYX; goto done; }
            if ((unsigned __int64)m1 + (unsigned __int64)m2 < (unsigned __int64)price) { c = KSPO_MONEY; goto done; }
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

/* STEP 4 book. An approved buy is booked on EVERY peer (host: when it approves, clients: on the broadcast 'A' o1). It only counts (kspo_wantB) once the stock buy of
   the carrier row shows in that seat's carried rows, so a cancelled dialog / a buy the stock path refused hands nothing over. */
static void kspo_book_add(int seat, int row)
{
    if (!kspg.apply || seat < 0 || seat >= KSPO_SEATS || row < 0 || row >= KSPG_ROWS) return;
    kspo.bk[seat] = row + 1; kspo.bkSeen[seat] = 0; kspo.bkAt[seat] = GetTickCount();
    klog("shopg: apply: seat %d row %d booked (counts once the stock buy of its carrier shows in the rules)", seat, row);
}

/* the seats that will get page II row `row` at the next hand-out (the pool relabel asks) */
static int kspo_wantB(int row)
{
    int s, n = 0;
    for (s = 0; s < KSPO_SEATS; s++) if (kspo.bk[s] == row + 1 && kspo.bkSeen[s]) n++;
    return n;
}

/* game thread, <= 4 Hz: book -> seen (the carrier row is carried), seen -> gone (replaced / session over), pending -> dropped (never showed) */
static void kspo_book_tick(void)
{
    DWORD now = GetTickCount(); int s;
    if (!kspg.apply || now - kspo.bkTick < 250) return;
    kspo.bkTick = now;
    for (s = 0; s < KSPO_SEATS; s++) {
        int row = kspo.bk[s] - 1, c0, c1, has;
        if (row < 0) continue;
        if (!kl_online()) { kspo.bk[s] = 0; kspo.bkSeen[s] = 0; continue; }
        if (!kspo_carried(s, &c0, &c1)) { if (!kspo.bkSeen[s] && now - kspo.bkAt[s] > KSPO_BOOKMS) { klog("shopg: apply: seat %d row %d: the carried rows are unreadable for %d ms: dropped", s, row, KSPO_BOOKMS); kspo.bk[s] = 0; } continue; }
        has = (c0 == row || c1 == row);
        if (has && !kspo.bkSeen[s]) {
            kspo.bkSeen[s] = 1; kspo.got[s] = kspo_round() + 1;
            klog("shopg: apply: seat %d now carries row %d (rows %d,%d): page II gun item %d is lined up for the next hand-over", s, row, c0, c1, kspg.p[row].item);
        } else if (!has && kspo.bkSeen[s]) {
            klog("shopg: apply: seat %d no longer carries row %d (rows %d,%d): the page II gun is let go", s, row, c0, c1);
            kspo.bk[s] = 0; kspo.bkSeen[s] = 0;
        } else if (!has && !kspo.bkSeen[s] && now - kspo.bkAt[s] > KSPO_BOOKMS) {
            klog("shopg: apply: seat %d row %d: the stock buy never showed in the carried rows (%d,%d) within %d ms: nothing handed over", s, row, c0, c1, KSPO_BOOKMS);
            kspo.bk[s] = 0;
        }
    }
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
    if (why == KSPO_OK) kspo_book_add(seat, row);                  /* STEP 4: the client's stock buy follows its answer; money and the carried row are the stock path's (host-side) */
}

/* CLIENT: 'A' from the host */
static void kspo_on_answer(const struct knc_msg *m)
{
    int seat = -1, row = -1, item = -1, round = -1, ok = 0, why = 0;
    if (kspo_role() != 3 || m->role != 2) return;
    if (sscanf(m->payload + 1, "s%dr%di%dn%do%dm%d", &seat, &row, &item, &round, &ok, &why) < 6) return;
    if (seat < 0 || seat >= KSPO_SEATS || row < 0 || row >= KSPG_ROWS || item < 0 || item > 63 || why < 0 || why > 9) return;
    if (ok && why == 0) kspo_book_add(seat, row);                      /* STEP 4: every peer books an approved buy (seats other than mine too) */
    if (seat != kspo_myseat()) return;
    if (!kspo.pend || kspo.pendRow != row) return;                     /* late or not asked: a judgement with nothing waiting is ignored */
    kspo.pend = 0;
    klog("shopg: host judged seat %d row %d item %d: %s%s", seat, row, item, ok ? "ok" : "refused ", ok ? "" : kspo_why(why));
    if (ok && why == 0 && kspg.apply) { kspo.doRow = row + 1; kspo.doAt = GetTickCount(); }   /* the stock buy of the carrier is fired from the tick (game thread) */
}

/* STEP 4, the gate in kspg_sel for a page II row (online, OnlineApply=1): 1 = let the stock handler buy the CARRIER row now, 0 = swallow.
   Host: judge here, approve -> book + broadcast 'A' o1, the stock buy goes on (money and rows are the stock host path's, authoritative).
   Client: ask the host (kspo_press), swallow; the host's 'A' fires the stock buy later through kspg_applybuy (okRow set there). */
static void kspo_press(int row);
static int kspo_gate(int row, const char *nm)
{
    DWORD now = GetTickCount(); int role = kspo_role(), seat, item, round, why, isbuy = !strcmp(nm, "BuyWeapon"), pre = 0; char pay[64];
    if (row < 0 || row >= KSPG_ROWS) return 0;
    if (isbuy && kspo.okRow == row + 1 && now - kspo.okAt < 20000) {     /* the dialog was judged (host), or our own fired buy (client): the confirm / the fired BuyWeapon passes once */
        kspo.okRow = 0;
        if (role == 3) return 1;                                         /* client: booked on the host's answer already */
        pre = 1;                                                         /* host: judged at the dialog; booked + broadcast below, only now that the buy is confirmed */
    }
    if (role == 3) { kspo_press(row); return 0; }
    if (role != 2) { klog("shopg: refused: no client / host role (%d)", role); return 0; }
    seat = kspo_myseat(); item = kspo_item_of(row); round = kspo_round();
    if (seat < 0) { klog("shopg: refused: own seat unknown (not in an online FA round)"); return 0; }
    if (item < 0 || item > 63) { klog("shopg: refused: row %d / carrier item %d out of range", row, item); return 0; }
    if (!pre) {
        if (row == kspo.lastRow && now - kspo.lastPress < 800) return 0;   /* the second message of one refused click */
        kspo.lastRow = row; kspo.lastPress = now;
        why = kspo_judge(seat, row, item, round, 0, 0);
        klog("shopg: seat %d asked row %d item %d: %s%s (host's own press, applied)", seat, row, item, why ? "refused " : "ok", why ? kspo_why(why) : "");
        if (why) return 0;
        if (!isbuy) { kspo.okRow = row + 1; kspo.okAt = now; return 1; }  /* dialog message: judged, NOT booked: a cancelled dialog books nothing and may be pressed again */
    }
    kspo_book_add(seat, row);
    snprintf(pay, sizeof pay, "As%dr%di%dn%do1m0", seat, row, item, round);
    knc_send("SHOPG", pay, -1);                                       /* the clients book it too */
    return 1;
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
    if (!kspo.on) return;
    if (kspo.pend && GetTickCount() - kspo.pendAt >= KSPO_ASKMS) { klog("shopg: no answer from the host about row %d (%d ms)", kspo.pendRow, KSPO_ASKMS); kspo.pend = 0; }
    if (!kspg.apply) return;
    kspo_book_tick();
    if (kspo.doRow) {   /* the host approved: press the stock buy of the carrier on the live selector; retried per tick for 3 s (list up, selector wrapped) */
        if (!kl_online()) kspo.doRow = 0;
        else if (kspg_applybuy(kspo.doRow - 1)) kspo.doRow = 0;
        else if (GetTickCount() - kspo.doAt > 3000) { klog("shopg: apply: row %d approved but the weapon list / selector was not there within 3000 ms: the stock buy was NOT made (nothing charged)", kspo.doRow - 1); kspo.doRow = 0; }
    }
}

static void kspo_init(void)
{
    kspo.on = GetPrivateProfileIntA("ShopPage", "OnlineSend", 0, klh_ini) != 0;
    { int v = (int)GetPrivateProfileIntA("Bench", "ShopMoney", 0, klh_ini); kspo.bmN = v < 0 ? 0 : v > 99999999 ? 99999999 : (DWORD)v;
      if (kspo.bmN) klog("bench: [Bench] ShopMoney=%lu (bench only, recommended off): once per shop stay the HOST raises every seat's shop money to that, through the game's AddLootMoney 0x6cfdb0", (unsigned long)kspo.bmN); }
    if (!kspo.on) return;
    knc_want("shopg");
    knc_on("SHOPG", kspo_on_msg);
    klog("shopg: on ([ShopPage] OnlineSend=1, recommended off until benched): a client's page II press is sent to the host, the host judges and logs; NO game-state write (step 2). Needs [NetChan], [ShopPage] Enable=1 + OnlineLook=1 on both, [Online] Read=1 on the host");
}

#endif /* KLSHOPPAGE_ONLINE_C */
