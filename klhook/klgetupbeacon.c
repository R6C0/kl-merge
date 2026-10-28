/*
 * klgetupbeacon.c - [BotFill] OnlineGetUpBeacon=0|1 (default 0, "(recommended off)"; only meaningful with OnlineGetUp 1 / 2 on BOTH machines). wk-getup2-1028, re/bot_getup_online.md section 7.
 * Why: bench GU3 (10-28, DD04 online, 2 seats): the joiner was knocked down ("down: YOU ARE DOWN ... down state 2") but the host never logged "botfill: getup: seat N IS DOWN". The host reads a
 * JOINER's REPLICA body D = [P+0x2948], [D+4]; kldown.c's down mirror refuses the replica (the "pool SHARED with other bodies" refusal), so on the host that state never leaves 0.
 * What: the DOWNED machine knows its own state (kldown.c's pass). It sends the host a 32-byte UDP packet 'KLSYD' (layout and schedule in klgetupbeacon.h; the KLSYB / KLSYV channel:
 * UDP 27415, broadcast, klsy.sock) once a second while down and 3x (one seq, 100 ms apart) on getting up. The HOST drains them (klgb_host_rx, from klsy_tick), keeps one record per table index
 * (klgb_seats, klbotfill.c) and klbf_gu_pass counts a seat as down when EITHER its replica says so OR a fresh (< 3 s) down beacon does; the place is the replica's when readable, else the beacon's.
 * Identity: the sender's index in the session player table (klco_table; the same convention klcharonline.c announces looks with, down_mirror.md item 3). The host CHECKS it against the replica of
 * that index (beacon place within 1500 cm of the replica's feet) and falls back to the nearest replica within 600 cm (GUESS thresholds, logged once per seat).
 * The downed-machine half (a bot by the body adds to the mash meter) is unchanged (klbotfill.c klbf_gu_rate_now); the host's rush (kle_order2) now gets its trigger online.
 * No game memory is written; one UDP send per second per downed machine. Game thread only (kldown.c's pass; klsy_tick).
 *
 * LOG
 *   getup: beacon SENT down|up seq N seat S at (x, y, z)                  client, each down beacon and the first up send
 *   getup: beacon rx seat N down|up seq S (gap G ms, from a.b.c.d)         host, when the state changes (first beacon and each flip)
 *   getup: beacon from a.b.c.d ignored: wrong level tag ...                host, once
 *   botfill: getup: seat N IS DOWN (D ... state ...) at (...) (beacon)    host, klbotfill.c, when the beacon made the call
 *   botfill: getup: beacon says seat N but that replica is far ...        host, klbotfill.c, once per seat: the index does not name that body
 */
#ifndef KLGETUPBEACON_C
#define KLGETUPBEACON_C

/* CLIENT: kldown.c's pass calls this every frame it acts online (klgb_on checked there). pl = this machine's own body, ds = [D+4], alive = he lives. */
static void klgb_own(DWORD pl, DWORD ds, int alive, DWORD now)
{
    static struct klgb_tx tx; static DWORD lastPl, loggedSeq; static unsigned toldNoIdx;
    DWORD sm = 0, role = 0, ents = 0; int n = 0, idx = -1, i, d = 0, down; unsigned seq = 0; struct klgb_tx keep; struct klgb_pk k; unsigned char b[KLGB_LEN]; klsy_sin a; char scene[160]; float pos[3];
    if (!klgb_on || !pl || !klsy.sock || !klh_exe_ok) return;
    if (!klbv_round(&sm, &role) || role != 3) return;      /* a client in a round only (the host reads its own body directly) */
    if (pl != lastPl) { lastPl = pl; tx.down = 0; tx.burst = 0; }      /* another body: the seq keeps counting (the host's book drops only an older seq) */
    down = alive && kgu_downed(ds);
    keep = tx;
    if (!klgb_tx_step(&tx, down, now, &d, &seq)) return;
    if (klco_table(sm, &ents, &n)) for (i = 0; i < n; i++) if (klco_ent(ents, n, i) == pl) idx = i;
    if (idx < 0 && n) { DWORD e2 = 0; int how = 0; idx = klco_find_own(ents, n, now, &e2, &how); }
    if (idx < 0 || idx >= KLGB_MAX_SEATS || !klh_rd(pl + 0x460, pos, 12) || !kle_ok3(pos)) {
        tx = keep;      /* nothing was sent: try again next pass */
        if (!(toldNoIdx++ % 50)) klog("getup: beacon not sent: own table index %d / place not readable (%u pass(es))", idx, toldNoIdx);
        return;
    }
    memset(&k, 0, sizeof k); k.ver = KLGB_VER; k.seat = (unsigned char)idx; k.flags = (unsigned char)(d ? 1 : 0); k.seq = seq; k.T = (unsigned)klsy_T();
    k.tag = klh_scene(scene, sizeof scene) ? klgb_tag(scene) : 0; memcpy(k.pos, pos, 12);
    if (!klgb_encode(b, sizeof b, &k)) return;
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
    i = klsy.sendto(klsy.sock, (const char *)b, KLGB_LEN, 0, &a, sizeof a);
    if (d || loggedSeq != seq) { loggedSeq = seq; klog("getup: beacon SENT %s seq %u seat %d at (%.0f, %.0f, %.0f) (sendto %d)", d ? "down" : "up", seq, idx, pos[0], pos[1], pos[2], i); }
}

/* HOST: drain the beacons (called from klsy_tick for role 2 in a round). The host's socket also receives its own list broadcasts: everything not 'KLSYD' is skipped. */
static void klgb_host_rx(DWORD now)
{
    static char pk[1500]; static int toldTag; static int lastDown[KLGB_MAX_SEATS]; static DWORD lastSm;
    klsy_sin from; int fl, len, k; struct klgb_pk p; char scene[160]; unsigned tag, gap = 0; DWORD sm = 0, role = 0;
    if (!klgb_on || !klsy.sock || !klsy.recvfrom) return;
    if (!klbv_round(&sm, &role) || role != 2) return;
    if (sm != lastSm) { lastSm = sm; memset(lastDown, 0xff, sizeof lastDown); }      /* -1 = nothing logged for the seat yet */
    tag = klh_scene(scene, sizeof scene) ? klgb_tag(scene) : 0;
    for (k = 0; k < 128; k++) {
        fl = sizeof from; len = klsy.recvfrom(klsy.sock, pk, sizeof pk, 0, &from, &fl);
        if (len < 0) break;
        if (len < 5 || memcmp(pk, "KLSYD", 5) || !klgb_decode((const unsigned char *)pk, len, &p)) continue;
        if (tag && p.tag && p.tag != tag) { if (!toldTag++) klog("getup: beacon from %lu.%lu.%lu.%lu ignored: wrong level tag %08x (mine %08x)", from.addr & 255, from.addr >> 8 & 255, from.addr >> 16 & 255, from.addr >> 24, p.tag, tag); continue; }
        if (!klgb_take(&klgb_seats[p.seat], &p, now, &gap)) continue;
        if (lastDown[p.seat] != (p.flags & 1))
            klog("getup: beacon rx seat %d %s seq %u (gap %u ms, from %lu.%lu.%lu.%lu) at (%.0f, %.0f, %.0f)", p.seat, (p.flags & 1) ? "down" : "up", p.seq, gap, from.addr & 255, from.addr >> 8 & 255, from.addr >> 16 & 255, from.addr >> 24, p.pos[0], p.pos[1], p.pos[2]);
        lastDown[p.seat] = p.flags & 1;
    }
}

#endif /* KLGETUPBEACON_C */
