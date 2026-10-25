/*
 * klnetload.c - ONLINE FA WITH MORE PEOPLE: a read-only LOAD PROBE and one opt-in send-rate fix. Part of KLHook (included by
 * klhook.c right after klnetfix.c; SHIP and TEST alike; every key is OFF by default). re\max_players.md section 6 is the note.
 *
 * NOTHING HERE HAS RUN IN THE GAME. Everything is off unless KLHook.ini has one of the keys below.
 *
 *   [NetLoad]
 *   Probe=0          1 = (recommended off, a diagnosis) one line a second in a network session: how many peers, how the game's frames
 *                    ran (fps, the longest gap between two frames, gaps over 50 / 100 ms), what the sender numbers are now. Reads only.
 *   ProbeLines=600   at most this many lines per process
 *   ScaleSend=0      1 = (recommended off) the SENDER'S minimum update interval grows with the number of peers, so a full lobby does not
 *                    send eleven streams at the rate that was tuned for three. min = stock * (1 + ScalePct/100 * (peers - ScaleFrom)),
 *                    at most MaxFactor times the stock number. Player position / angle / camera / aim (and the AI datasets of the host
 *                    with ScaleActors=1). Only the SENDER'S numbers count (klnet.c), so it helps when the HOST and the clients both run it.
 *   ScaleFrom=4      peers up to this number get the stock numbers
 *   ScalePct=12      percent per extra peer
 *   MaxFactor=2.0    never more than 2.0 x stock (1.0 .. 4.0)
 *   ScaleActors=0    1 = also the host's AI position / angle intervals
 *
 * WHY (re\max_players.md 6, GUESS where said): Net-Z sends a station's position at most every 'min' ms per peer (stock 100 ms = 10 a
 * second, klnet.c section 2), so the bandwidth a machine uploads grows with the peers it feeds: three peers 30 updates a second, eleven
 * 110. Steam P2P here is UNRELIABLE sends with Net-Z's PRUDP on top, so a saturated upstream shows as late and lost packets, which the
 * receiver extrapolates (the spin of re\netcode_receiver.md). GUESS: that the game's own throttling does not already do this - it was
 * not read. Slowing the sender trades fidelity for fewer lost packets; that is why it is a switch and why Probe exists first.
 *
 * WHAT IT WRITES: the same four dwords per dataset as klnet.c (min intervals at 0xd35424 / 0xd3545c / 0xd3547c / 0xd3549c and, with
 * ScaleActors, 0xd34668 / 0xd34688), .data, not in a hashed range, through klh_data. Skipped altogether when klnet.c's own Tune is
 * writing the same numbers (Tune=1 with a number). Gate: this machine is SERVER or CLIENT, game type 4, session state 0x13..0x1f, the
 * service's ranked byte is 0 (a RANKED lobby is never touched). The numbers are put back when the gate closes. A number that no longer
 * holds what we wrote (the game rewrote it at a Net-Z start) is re-read as the new stock one.
 *
 * PEERS: connected = hi - lo of the handler's list, [[[sm+4]+8]+8] and [+0xc] (kllobby.c reads the same; GUESS that it counts bytes
 * the same way for a client as for a server: on a CLIENT the count is only trusted when it is 1..12).
 */
#ifndef KLNETLOAD_C
#define KLNETLOAD_C

static struct {
    int probe, scale, actors, from, pct, nlines;
    float maxf;
    LONG frames, over50, over100, maxgap;     /* since the last line */
    DWORD lastframe, lastline;
    int have, wrote[KLNET_NDS];               /* scale state */
    DWORD stock[KLNET_NDS], ours[KLNET_NDS];
    DWORD last_peers, told_gate;
} knl;

/* connected peers of a network session, 0 = not known */
static DWORD knl_peers(DWORD sm)
{
    DWORD h, v, lo, hi;
    if (!(h = klh_rd32(sm + 4)) || !(v = klh_rd32(h + 8))) return 0;
    lo = klh_rd32(v + 8); hi = klh_rd32(v + 0xc);
    if (!lo || hi < lo || hi - lo > 16) return 0;
    return hi - lo;
}

/* the gate shared by the probe's 'acting' word and the scaler: a network FA session past its load, not ranked */
static int knl_gate(DWORD sm, DWORD *role_out, DWORD *state_out)
{
    DWORD role = 0, mode = 0, state = 0, svc; BYTE ranked = 1, ranked_bit = 0, props[0x20];
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return 0;
    if (role_out) *role_out = role;
    if (state_out) *state_out = state;
    if ((role != 2 && role != 3) || mode != 4 || state < 0x13 || state > 0x1f) return 0;
    if (!(svc = klh_rd32(sm + 0x17c)) || klh_rd32(svc) != KLNET_SVC_VT || !klh_rd(svc + 0x36f, &ranked, 1)) return 0;     /* the service must be the one this build knows */
    if (klh_rd(svc + 0x370, props, sizeof props)) ranked_bit = (props[8] >> 5) & 1;
    if (ranked || (role == 2 && ranked_bit)) return 0;       /* a client's property bits are stale: its ranked BYTE alone (klnet.c) */
    return 1;
}

static void knl_restore(void)
{
    int i, n = 0; struct klnet_num cur[KLNET_NDS];
    if (!knl.have) return;
    klnet_read_nums(cur);
    for (i = 0; i < KLNET_NDS; i++)
        if (knl.wrote[i] && cur[i].min == knl.ours[i] && cur[i].min != knl.stock[i]) n += klh_data((void *)KLH_VA(klnet_ds[i].min), &knl.stock[i], 4, "Net-Z min update interval (stock, NetLoad)");
    memset(knl.wrote, 0, sizeof knl.wrote); knl.have = 0;
    klog("netload: ScaleSend: the session is over or no longer eligible: %d interval(s) put back to the game's own", n);
}

static void knl_scale(DWORD peers)
{
    struct klnet_num cur[KLNET_NDS]; int i, n = 0; float f;
    if (peers > (DWORD)knl.from) f = 1.0f + (float)knl.pct / 100.0f * (float)(peers - (DWORD)knl.from); else f = 1.0f;
    if (f > knl.maxf) f = knl.maxf;
    klnet_read_nums(cur);
    for (i = 0; i < KLNET_NDS; i++) {
        DWORD want;
        if (!cur[i].ok || (klnet_ds[i].actor && !knl.actors)) continue;
        if (!knl.have || !knl.wrote[i]) knl.stock[i] = cur[i].min;
        else if (cur[i].min != knl.ours[i]) knl.stock[i] = cur[i].min;       /* the game set it again (a new Net-Z start): that is the stock one now */
        want = (DWORD)((float)knl.stock[i] * f + 0.5f);
        if (want < 1) want = 1;
        if (want > 1000) want = 1000;                          /* klnet_read_nums' own sanity bound for a min */
        if (want == cur[i].min) { knl.ours[i] = want; continue; }
        if (klh_data((void *)KLH_VA(klnet_ds[i].min), &want, 4, "Net-Z min update interval (NetLoad)")) { knl.ours[i] = want; knl.wrote[i] = 1; n++; }
    }
    knl.have = 1;
    if (n) klog("netload: ScaleSend: %lu peers -> sender intervals x%.2f (%d number(s) written; stock player position %lu ms)", peers, f, n, knl.stock[2]);
}

static void knl_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, state = 0, peers; int ok;
    if (!knl.probe && !knl.scale) return;
    if (!klh_exe_ok) return;
    if (game_thread && knl.probe) {                             /* one call a frame: the gaps are the stutter the other peers see as late packets */
        if (knl.lastframe) {
            DWORD gap = now - knl.lastframe;
            knl.frames++;
            if (gap > 50) knl.over50++;
            if (gap > 100) knl.over100++;
            if ((LONG)gap > knl.maxgap) knl.maxgap = (LONG)gap;
        }
        knl.lastframe = now;
    }
    if (now - knl.lastline < 1000) return;
    knl.lastline = now;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION)))) { if (knl.have) knl_restore(); return; }
    ok = knl_gate(sm, &role, &state);
    peers = (role == 2 || role == 3) ? knl_peers(sm) : 0;
    if (knl.scale) {
        if (ok && peers >= 1 && peers <= 12 && !(klnet.tune && klnet.any)) knl_scale(peers);
        else if (knl.have) knl_restore();
    }
    if (knl.probe && (role == 2 || role == 3) && knl.nlines < 600) {
        struct klnet_num nm[KLNET_NDS]; BYTE target = 0, maxp = 0;
        klnet_read_nums(nm);
        klh_rd(sm + 0xb9, &target, 1); klh_rd(sm + 0xb8, &maxp, 1);
        knl.nlines++;
        klog("netload: %s state 0x%lx peers %lu (target %u, max %u) %s | frames %ld (%.0f fps) gap max %ld ms, over 50 ms %ld, over 100 ms %ld | sender min ms: player pos %lu ang %lu cam %lu aim %lu, AI pos %lu ang %lu%s",
             role == 2 ? "SERVER" : "CLIENT", state, peers, target, maxp, ok ? "eligible" : "not eligible (state/ranked/service)",
             knl.frames, (double)knl.frames, knl.maxgap, knl.over50, knl.over100,
             nm[2].min, nm[3].min, nm[4].min, nm[5].min, nm[0].min, nm[1].min, knl.have ? " [ScaleSend active]" : "");
        knl.frames = 0; knl.over50 = 0; knl.over100 = 0; knl.maxgap = 0;
    } else if (knl.probe) { knl.frames = 0; knl.over50 = 0; knl.over100 = 0; knl.maxgap = 0; }
}

static void knl_init(void)
{
    char b[32];
    knl.probe = GetPrivateProfileIntA("NetLoad", "Probe", 0, klh_ini) != 0;
    knl.scale = GetPrivateProfileIntA("NetLoad", "ScaleSend", 0, klh_ini) != 0;
    knl.actors = GetPrivateProfileIntA("NetLoad", "ScaleActors", 0, klh_ini) != 0;
    knl.from = (int)GetPrivateProfileIntA("NetLoad", "ScaleFrom", 4, klh_ini); if (knl.from < 1) knl.from = 1; if (knl.from > 12) knl.from = 12;
    knl.pct = (int)GetPrivateProfileIntA("NetLoad", "ScalePct", 12, klh_ini); if (knl.pct < 1) knl.pct = 1; if (knl.pct > 100) knl.pct = 100;
    GetPrivateProfileStringA("NetLoad", "MaxFactor", "2.0", b, sizeof b, klh_ini); knl.maxf = (float)atof(b);
    if (!(knl.maxf >= 1.0f)) knl.maxf = 1.0f;
    if (knl.maxf > 4.0f) knl.maxf = 4.0f;
    if (!knl.probe && !knl.scale) return;
    klog("netload: on; Probe=%d ScaleSend=%d (from %d peers, +%d%% each, at most x%.1f, AI %d); reads only, plus the min-interval dwords of klnet.c when ScaleSend=1 (default off)",
         knl.probe, knl.scale, knl.from, knl.pct, knl.maxf, knl.actors);
}

#endif /* KLNETLOAD_C */
