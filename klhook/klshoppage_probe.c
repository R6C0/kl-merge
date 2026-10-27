/* klshoppage_probe.c - [ShopPage] OnlineProbe=0|1 (default 0, "(recommended off until benched)"). Included by klshoppage.c after struct kspg and before kspg_sel.
 * PROBE ONLY: LOG ONLY, writes nothing, no detour of its own (it is polled from klshoppage_tick and called from kspg_sel's existing wrapper).
 *
 * QUESTION (plan step 1, online page II): does the weapon pool [0x168e96c] exist and hold the carrier guns on a CLIENT, and does the stock hand-over
 * (byte+8 1 -> 0, owner at [obj+0x5c]) happen there for every seat, or is it host-only? Pass = HANDOUT lines on the client for every seat.
 *
 * LAYOUT (read from klshop.c's kls_vec / kls_apply and re/shop_cap.md:222, NOT re-verified in the game here): [0x168e96c] = pool object; [pool] = vector V;
 * [V+4] count, [V+8] cap, [V+0xc] grow, [V+0x10] -> array of 12-byte records {object, item label, byte+8 free, byte+9 dropped}. Owner of a handed-out gun =
 * [obj+0x5c] (the task's reading; GUESS: a player / actor pointer; matched against klor_read's rows to get a seat, else logged raw with seat ?).
 *
 * LINES (all through klog, 150 per session):
 *   shopProbe: role=host|client|sp phase=%x pool=%p count=%d carriers: item%d x%d free=%d ...   once per phase change in 0x16..0x19 (and again once when
 *                                                                          the pool first becomes readable inside the same phase)
 *   shopProbe: HANDOUT obj=%p item=%d owner=%p(seat %d|seat?) role=%s phase=%x tick=%u         byte+8 1 -> 0 seen between two polls, any item
 *   shopProbe: page2buy ...      a page II row buy: swallowed (OnlineLook) or passed on (OnlinePage2), row, carrier item, the message name
 *   shopProbe: stockbuy row=%d crew[seat]=+3:%d->%d +4:%d->%d zc+1dc=%d +29c=%d money=%lu->%lu    1.5 s after a stock BuyWeapon (replication time);
 *                                                                          crew[seat] = [rules+8] + 0x74 * seat, zc+1dc / +29c = rules+0x1dc (byte) / rules+0x29c (dword) (read as asked, meaning unknown);
 *                                                                          money = the SHOP money of the seat, stock getters 0x622e10 + 0x639c10 (seat from klor_read, needs [Online] Read=1, else 'n/a')
 * The stock buy line is only reached when klshoppage's wrappers are live online ([ShopPage] Enable=1 + OnlineLook=1, the gate of kspg_gate).
 */
#ifndef KLSHOPPAGE_PROBE_C
#define KLSHOPPAGE_PROBE_C

#define KSPP_MAXN 4096
#define KSPP_MAXLOG 150

static struct {
    int n_log, capSaid, lastSt, poolSaid, inRange;
    DWORD pobj[KSPP_MAXN]; BYTE pfree[KSPP_MAXN]; DWORD pn, parr;
    int pbPend, pbRow, pbSeat, pbB3, pbB4; DWORD pbDue, pbMoney; int pbMoneyOk;
} kspp;

static struct klor_snap kspp_snap;
static int kspo_shopmoney(int seat, DWORD *first, DWORD *second);   /* klshoppage_online.c, defined after this include */

/* the local seat as klescprobe.c reads it (osd player list element +0xefc); -1 unknown */
static int kspp_loc(void)
{
    DWORD pl, li = 0;
    if (klu_r.osd && (pl = klh_rd32(klu_r.osd + KLU_O_PLIST)) && klh_rd(pl + 0xefc, &li, 1) && li < 16) return (int)li;
    return -1;
}

static int kspp_item_ok(DWORD it) { return it == 33 || it == 35 || it == 38 || (it >= 40 && it <= 59); }

static void kspp_log(const char *fmt, ...)
{
    char b[900]; va_list ap;
    if (kspp.n_log >= KSPP_MAXLOG) { if (!kspp.capSaid) { kspp.capSaid = 1; klog("shopProbe: line cap (%d) reached, silent from here", KSPP_MAXLOG); } return; }
    kspp.n_log++;
    va_start(ap, fmt); vsnprintf(b, sizeof b, fmt, ap); va_end(ap);
    b[sizeof b - 1] = 0;
    klog("%s", b);
}

static const char *kspp_role(void)
{
    DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598u)), role = 0;
    if (!sm || !klh_rd(sm + 0x54, &role, 4)) return "?";
    return role == 2 ? "host" : role == 3 ? "client" : "sp";
}

/* the pool vector's array and count; 0 = pool null / unreadable. Bounded: count <= KSPP_MAXN */
static int kspp_pool(DWORD *pool, DWORD *arr, DWORD *n)
{
    DWORD w = klh_rd32((DWORD_PTR)KLH_VA(0x0168e96cu)), v, c = 0, a;
    *pool = w; *arr = 0; *n = 0;
    if (!w || !(v = klh_rd32(w)) || v < 0x10000 || !klh_rd(v + 4, &c, 4) || c > KSPP_MAXN || !(a = klh_rd32(v + 0x10)) || a < 0x10000) return 0;
    *arr = a; *n = c;
    return 1;
}

/* owner seat of a handed-out gun: klor_read's rows (humans) matched on player / actor; -1 = not resolvable */
static int kspp_seat_of(DWORD owner)
{
    int i;
    if (!owner) return -1;
    klor_noev = 1; i = klor_read(&kspp_snap, kspp_loc()); klor_noev = 0;
    if (!i) return -1;
    for (i = 0; i < kspp_snap.n && i < KLOR_MAX; i++)
        if (kspp_snap.r[i].used && (kspp_snap.r[i].player == owner || kspp_snap.r[i].actor == owner)) return kspp_snap.r[i].seat;
    return -1;
}

static void kspp_snapshot(DWORD st, DWORD pool, DWORD arr, DWORD n)
{
    static DWORD tab[KSPP_MAXN * 3]; int cnt[64], fr[64], it, len; char b[800]; DWORD i;
    memset(cnt, 0, sizeof cnt); memset(fr, 0, sizeof fr);
    if (arr && n && klh_rd(arr, tab, 12 * (SIZE_T)n))
        for (i = 0; i < n; i++) if (tab[3 * i + 1] < 64) { cnt[tab[3 * i + 1]]++; if (tab[3 * i + 2] & 0xff) fr[tab[3 * i + 1]]++; }
    len = snprintf(b, sizeof b, "shopProbe: role=%s phase=%lx pool=%p count=%lu carriers:", kspp_role(), (unsigned long)st, (void *)(DWORD_PTR)pool, (unsigned long)n);
    for (it = 0; it < 64 && len > 0 && len < (int)sizeof b - 40; it++)
        if (kspp_item_ok((DWORD)it) && cnt[it]) len += snprintf(b + len, sizeof b - len, " item%d x%d free=%d", it, cnt[it], fr[it]);
    kspp_log("%s%s", b, !pool ? " (pool pointer null)" : !arr ? " (vector unreadable)" : "");
}

/* polled from klshoppage_tick on the game thread, whatever [ShopPage] Enable says; reads only */
static void kspp_tick(void)
{
    static DWORD tab[KSPP_MAXN * 3]; DWORD sm, st = 0, pool, arr, n, i, now = GetTickCount(); int ok, inr;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598u))) || !klh_rd(sm + 0x70, &st, 4)) { kspp.lastSt = -1; kspp.inRange = 0; return; }
    /* follow-up of a stock buy: the replicated money / crew bytes are read 1.5 s after the click */
    if (kspp.pbPend && now - kspp.pbDue < 0x80000000u) {
        DWORD rules = 0, gs = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4u)), rec = 0, vz = 0; BYTE v1dc = 0, b3 = 0xff, b4 = 0xff; unsigned long m1 = 0; int mok = 0;
        kspp.pbPend = 0;
        rules = gs ? klh_rd32(gs + 0x54) : 0;
        if (rules && (KLH_RULES_SV_OK(klh_rd32(rules)) || KLH_RULES_CL_OK(klh_rd32(rules)))) {
            klh_rd(rules + 0x1dc, &v1dc, 1); klh_rd(rules + 0x29c, &vz, 4);
            if (kspp.pbSeat >= 0 && kspp.pbSeat < 16 && (rec = klh_rd32(rules + 8))) { klh_rd(rec + 0x74 * (DWORD)kspp.pbSeat + 3, &b3, 1); klh_rd(rec + 0x74 * (DWORD)kspp.pbSeat + 4, &b4, 1); }
            { DWORD q1 = 0, q2 = 0; if (kspp.pbSeat >= 0 && kspp.pbSeat < 16 && kspo_shopmoney(kspp.pbSeat, &q1, &q2)) { m1 = (unsigned long)(q1 + q2); mok = 1; } }   /* shop money = the stock getters' sum (re/shop_hire.md 8.2), not klor's in-round on_money */
        }
        if (mok && kspp.pbMoneyOk) kspp_log("shopProbe: stockbuy row=%d crew[%d]=+3:%d->%d +4:%d->%d zc+1dc=%d +29c=%lu money=%lu->%lu", kspp.pbRow, kspp.pbSeat, kspp.pbB3, (int)b3, kspp.pbB4, (int)b4, (int)v1dc, (unsigned long)vz, (unsigned long)kspp.pbMoney, m1);
        else kspp_log("shopProbe: stockbuy row=%d crew[%d]=+3:%d->%d +4:%d->%d zc+1dc=%d +29c=%lu money=n/a (seat unknown or the money getters unreadable)", kspp.pbRow, kspp.pbSeat, kspp.pbB3, (int)b3, kspp.pbB4, (int)b4, (int)v1dc, (unsigned long)vz);
    }
    inr = st >= 0x16 && st <= 0x19;
    if (!inr) { kspp.lastSt = (int)st; kspp.inRange = 0; kspp.pn = 0; kspp.poolSaid = 0; return; }
    ok = kspp_pool(&pool, &arr, &n);
    if ((int)st != kspp.lastSt || !kspp.inRange) {
        kspp.poolSaid = ok; kspp.lastSt = (int)st;
        kspp_snapshot(st, pool, arr, n);                                  /* once per phase change (round start = 0x19) */
    } else if (ok && !kspp.poolSaid) { kspp.poolSaid = 1; kspp_snapshot(st, pool, arr, n); }   /* the pool became readable inside the phase */
    if (!kspp.inRange) kspp.pn = 0;                                        /* new stay in the range: fresh baseline */
    kspp.inRange = 1;
    if (!ok) { kspp.pn = 0; return; }
    if (!klh_rd(arr, tab, 12 * (SIZE_T)n)) return;
    if (kspp.pn && arr == kspp.parr) {
        for (i = 0; i < n && i < kspp.pn; i++) {
            DWORD *e = tab + 3 * i;
            if (kspp.pobj[i] == e[0] && kspp.pfree[i] && !(e[2] & 0xff) && e[0]) {          /* free 1 -> 0 */
                DWORD owner = klh_rd32(e[0] + 0x5c); int seat = kspp_seat_of(owner);
                if (seat >= 0) kspp_log("shopProbe: HANDOUT obj=%p item=%lu owner=%p(seat %d) role=%s phase=%lx tick=%lu", (void *)(DWORD_PTR)e[0], (unsigned long)e[1], (void *)(DWORD_PTR)owner, seat, kspp_role(), (unsigned long)st, (unsigned long)now);
                else kspp_log("shopProbe: HANDOUT obj=%p item=%lu owner=%p(seat?) role=%s phase=%lx tick=%lu", (void *)(DWORD_PTR)e[0], (unsigned long)e[1], (void *)(DWORD_PTR)owner, kspp_role(), (unsigned long)st, (unsigned long)now);
            }
        }
    }
    for (i = 0; i < n; i++) { kspp.pobj[i] = tab[3 * i]; kspp.pfree[i] = (BYTE)(tab[3 * i + 2] & 0xff); }
    kspp.pn = n; kspp.parr = arr;
}

/* called from kspg_sel's BuyWeapon path, before the stock handler: remember the pre-state of the buy (reads only) */
static void kspp_buy_before(int row)
{
    DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4u)), rules = gs ? klh_rd32(gs + 0x54) : 0, rec; BYTE b3 = 0xff, b4 = 0xff; int seat = -1;
    kspp.pbPend = 0;
    kspp.pbMoneyOk = 0;
    if (!rules || !(KLH_RULES_SV_OK(klh_rd32(rules)) || KLH_RULES_CL_OK(klh_rd32(rules)))) return;
    klor_noev = 1;
    if (klor_read(&kspp_snap, kspp_loc())) { seat = kspp_snap.local; if (seat >= 0 && seat < 16) { DWORD q1 = 0, q2 = 0; if (kspo_shopmoney(seat, &q1, &q2)) { kspp.pbMoney = q1 + q2; kspp.pbMoneyOk = 1; } }   /* shop money = getter sum (8.2) */ }
    klor_noev = 0;
    if (seat >= 0 && seat < 16 && (rec = klh_rd32(rules + 8))) { klh_rd(rec + 0x74 * (DWORD)seat + 3, &b3, 1); klh_rd(rec + 0x74 * (DWORD)seat + 4, &b4, 1); }
    kspp.pbRow = row; kspp.pbSeat = seat; kspp.pbB3 = (int)b3; kspp.pbB4 = (int)b4;
}
static void kspp_buy_after(void) { kspp.pbDue = GetTickCount() + 1500; kspp.pbPend = 1; }

#endif /* KLSHOPPAGE_PROBE_C */
