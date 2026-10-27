/*
 * klescprobe.c - [Online] EscProbe (default 0, debug; recommended off): READ-ONLY probe for the three guessed escape bits online.
 * Part of KLHook (klhook.c includes it after klhud_escape.c, SHIP and TEST alike). 2026-10-27, NOT RUN LIVE.
 *
 * Why: [HUD] OnlineVanIcon draws ESCAPED from score status bit 0x40 of the local seat (ABOARD unknown); [HUD] OnlineBoardTake labels a
 * living AI heister LEFT BEHIND because bot escape flags read 0; the van card uses esc_state 3..5. This logs what the game really shows.
 * Once per ~250 ms on the game thread, online and in a round (states 0x19 .. 0x1f: GO through the round-over panel), through klor_read (klor_noev=1: takes no kill-feed events) and
 * klh_rd only, nothing is written. ONE line per CHANGE, at most KLEP_CAP lines per round (round number or rules object changes reset it):
 *   escprobe: t=<ms> seat N[ LOCAL] status AAAAAAAA->BBBBBBBB alive A->B pbytes[2723 2729 273c]=xx xx xx   (status = raw [S+0x98+4*seat], alive = klor_read's
 *                                                                                                          verdict; pbytes = police/type bytes of the ZFFPlayer)
 *     full seat line now ends: ... (was xx xx xx) rec10 A->B state SS clock %.1f van N   (rec10 = crew record byte [rec+0x10], -1 = unread; a change alone logs; Arcade: 4 aboard, 6 escaped)
 *     BOTS: no rec10 probe - online bots have no crew record (klhud.c:1175, klonline_read.c:237); 0x78f470 is an Arcade game call, not a read-only reader.
 *   escprobe: t=<ms> seat N player +0x....: old->new ...      (a dword window of the ZFFPlayer, 0x2710..0x2750; GUESS: nothing there says 'in vehicle')
 *   escprobe: t=<ms> bot N actor XXXXXXXX bytes changed at +0x..: old->new ...   (actor +0x00..+0x3f, then [actor+0x54] team record +0..0x1f, the health block
 *                                                                                [[actor+0x5fc]] +0..0x1f; a dword that changes more than 6 times is called noisy and muted)
 *   escprobe: t=<ms> van state a->b vehicle XXXXXXXX timer %.1f clock %.1f          (esc_state [rules+0x1dc], vehicle [rules+0x1e4], timer [rules+0x1d8])
 *   escprobe: t=<ms> vehicle XXXXXXXX +0x..: old->new ...      (vehicle object +0x00..+0x3f, same noise rule)
 *   escprobe: t=<ms> local actor XXXXXXXX +0x..: old->new      (the local ZFFPlayer's body entity +0x00..+0x3f; a vehicle pointer would show up here; GUESS)
 * KLHook.ini [Online] EscProbe=1.
 */
#ifndef KLESCPROBE_C
#define KLESCPROBE_C

#define KLEP_CAP    400
#define KLEP_NBLK   48
#define KLEP_NOISY  6

static struct { int on; } klep;
static struct { DWORD rules; int round, lines; int van; DWORD vehicle; int vanset; int told_cap;
    struct { int kind, id; DWORD base; int have, n; BYTE prev[0x40]; BYTE chg[0x10]; BYTE noisy[0x10]; } b[KLEP_NBLK];
    DWORD st[KLOR_MAX]; BYTE al[KLOR_MAX]; BYTE pb[KLOR_MAX][3]; BYTE seen[KLOR_MAX]; short r10[KLOR_MAX]; } klep_c;   /* r10: crew record status byte (rec+0x10), -1 = not read */

static void klep_init(void)
{
    klep.on = GetPrivateProfileIntA("Online", "EscProbe", 0, klh_ini) != 0;
    if (klep.on) klog("escprobe: [Online] EscProbe=1 (read-only; one line per change, at most %d per round; needs [Online] Read=1)", KLEP_CAP);
}

static int klep_line(void) { if (klep_c.lines >= KLEP_CAP) { if (!klep_c.told_cap) { klep_c.told_cap = 1; klog("escprobe: line cap %d reached for this round", KLEP_CAP); } return 0; } klep_c.lines++; return 1; }

/* watch n bytes (<= 0x40, multiple of 4) at base: log the dwords that changed since the last look; prefix e.g. "bot 2 actor 00ab1234 bytes changed at" */
static void klep_block(int kind, int id, DWORD base, int n, const char *what)
{
    int i, k = -1, any = 0, noisy_new = 0; BYTE cur[0x40]; char buf[600]; size_t len = 0;
    if (!base || n > 0x40) return;
    for (i = 0; i < KLEP_NBLK; i++) if (klep_c.b[i].have && klep_c.b[i].kind == kind && klep_c.b[i].id == id) { k = i; break; }
    if (k < 0) for (i = 0; i < KLEP_NBLK; i++) if (!klep_c.b[i].have) { k = i; memset(&klep_c.b[i], 0, sizeof klep_c.b[i]); break; }
    if (k < 0) return;
    if (!klh_rd(base, cur, (SIZE_T)n)) return;
    if (!klep_c.b[k].have || klep_c.b[k].base != base) {          /* first look (or the object moved): remember, log nothing */
        klep_c.b[k].have = 1; klep_c.b[k].kind = kind; klep_c.b[k].id = id; klep_c.b[k].base = base; memset(klep_c.b[k].chg, 0, 0x10); memset(klep_c.b[k].noisy, 0, 0x10);
        memcpy(klep_c.b[k].prev, cur, (size_t)n); return;
    }
    buf[0] = 0;
    for (i = 0; i < n; i += 4) {
        DWORD a, b; memcpy(&a, klep_c.b[k].prev + i, 4); memcpy(&b, cur + i, 4);
        if (a == b) continue;
        memcpy(klep_c.b[k].prev + i, &b, 4);
        if (klep_c.b[k].noisy[i / 4]) continue;
        if (++klep_c.b[k].chg[i / 4] > KLEP_NOISY) { klep_c.b[k].noisy[i / 4] = 1; noisy_new++; continue; }
        if (len < sizeof buf - 40) { len += (size_t)snprintf(buf + len, sizeof buf - len, " +0x%02x: %08lx->%08lx", i, (unsigned long)a, (unsigned long)b); any = 1; }
    }
    if (any && klep_line()) klog("escprobe: t=%lu %s%s", (unsigned long)GetTickCount(), what, buf);
    if (noisy_new && klep_line()) klog("escprobe: t=%lu %s %d dword(s) changed more than %d times: muted (noisy)", (unsigned long)GetTickCount(), what, noisy_new, KLEP_NOISY);
}

static void klep_tick(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(); struct klor_snap o; int i, loc = -1;
    if (!klep.on || !game_thread || !klh_exe_ok || now - last < 250) return;
    last = now ? now : 1;
    if (klu_r.osd) { DWORD pl = klh_rd32(klu_r.osd + KLU_O_PLIST), li = 0; if (pl && klh_rd(pl + 0xefc, &li, 4) && li < 16) loc = (int)li; }
    klor_noev = 1; i = klor_read(&o, loc); klor_noev = 0;
    /* gate: 0x19 (GO) .. 0x1f (round over / outro panel, klhud_board2.c:227,279,909; 0x1d+ also read at klhud_board2.c:863). Boarding / escape may land after 0x19. 0x20 (buy page) and the lobby are out. GUESS: 0x1a..0x1e are real states of the same round (no code names them) */
    if (!i || o.b.state < 0x19 || o.b.state > 0x1f) return;
    if (klep_c.rules != o.b.rules || (o.round && klep_c.round != o.round)) { memset(&klep_c, 0, sizeof klep_c); klep_c.rules = o.b.rules; klep_c.round = o.round; klep_c.van = -1; klog("escprobe: new round %d (rules %08lx), local seat %d", o.round, (unsigned long)o.b.rules, loc); }
    /* the van */
    if (!klep_c.vanset || (int)o.esc_state != klep_c.van || o.vehicle != klep_c.vehicle) {
        if (klep_c.vanset && klep_line()) klog("escprobe: t=%lu van state %d->%d vehicle %08lx->%08lx timer %.1f clock %.1f", (unsigned long)now, klep_c.van, (int)o.esc_state, (unsigned long)klep_c.vehicle, (unsigned long)o.vehicle, o.esc_timer, o.clock);
        else if (!klep_c.vanset) klog("escprobe: t=%lu van initial state %d vehicle %08lx timer %.1f clock %.1f", (unsigned long)now, (int)o.esc_state, (unsigned long)o.vehicle, o.esc_timer, o.clock);
        klep_c.vanset = 1; klep_c.van = (int)o.esc_state; klep_c.vehicle = o.vehicle;
    }
    if (o.vehicle >= 0x10000) { char w[48]; snprintf(w, sizeof w, "vehicle %08lx", (unsigned long)o.vehicle); klep_block(3, 0, o.vehicle, 0x40, w); }
    /* the human seats */
    for (i = 0; i < o.n; i++) {
        const struct klor_row *w = &o.r[i]; int s = w->seat; BYTE pb[3] = { 0, 0, 0 }, r10b = 0; short r10 = -1; char tag[48];
        if (s < 0 || s >= KLOR_MAX) continue;
        if (w->player) { klh_rd(w->player + 0x2723, &pb[0], 1); klh_rd(w->player + 0x2729, &pb[1], 1); klh_rd(w->player + 0x273c, &pb[2], 1); }
        if (w->rec >= 0x10000 && klh_rd(w->rec + 0x10, &r10b, 1)) r10 = r10b;      /* crew record status byte: Arcade 4 = aboard, 6 = escaped (klhud_values.c:528-536); online record layout is a GUESS */
        if (!klep_c.seen[s] || klep_c.st[s] != w->flags || klep_c.al[s] != (BYTE)w->alive || memcmp(klep_c.pb[s], pb, 3) || klep_c.r10[s] != r10) {
            if (klep_line()) klog("escprobe: t=%lu seat %d%s status %08lx->%08lx alive %d->%d pbytes[2723 2729 273c]=%02x %02x %02x (was %02x %02x %02x) rec10 %d->%d state %02lx clock %.1f van %d",
                (unsigned long)now, s, s == loc ? " LOCAL" : "", klep_c.seen[s] ? (unsigned long)klep_c.st[s] : 0ul, (unsigned long)w->flags, klep_c.seen[s] ? (int)klep_c.al[s] : -1, w->alive,
                pb[0], pb[1], pb[2], klep_c.pb[s][0], klep_c.pb[s][1], klep_c.pb[s][2], klep_c.seen[s] ? (int)klep_c.r10[s] : -1, (int)r10, (unsigned long)o.b.state, o.clock, (int)o.esc_state);
            klep_c.seen[s] = 1; klep_c.st[s] = w->flags; klep_c.al[s] = (BYTE)w->alive; memcpy(klep_c.pb[s], pb, 3); klep_c.r10[s] = r10;
        }
        if (w->player) { snprintf(tag, sizeof tag, "seat %d player%s", s, s == loc ? " LOCAL" : ""); klep_block(1, s, w->player + 0x2710, 0x40, tag); }
        if (s == loc && w->actor) { snprintf(tag, sizeof tag, "local actor %08lx", (unsigned long)w->actor); klep_block(4, s, w->actor, 0x40, tag); }
    }
    /* the AI heisters: actor +0..0x3f, the team record [actor+0x54], the health block [actor+0x5fc] */
    for (i = 0; i < o.nbots; i++) {
        const struct klor_row *w = &o.bot[i]; char tag[64]; DWORD id = (DWORD)i;
        if (!w->actor) continue;
        id = (w->actor >> 4) & 0xff;                          /* key by the actor (the sorted order moves when one dies): hashed into the id space, collisions only merge two watches */
        snprintf(tag, sizeof tag, "bot %d actor %08lx bytes changed at", i, (unsigned long)w->actor);
        klep_block(10, (int)id, w->actor, 0x40, tag);
        { DWORD t = klh_rd32(w->actor + 0x54); if (t >= 0x10000) { snprintf(tag, sizeof tag, "bot %d team-rec %08lx bytes changed at", i, (unsigned long)t); klep_block(11, (int)id, t, 0x20, tag); } }
        { DWORD h = klh_rd32(w->actor + 0x5fc); if (h >= 0x10000) { snprintf(tag, sizeof tag, "bot %d health-blk %08lx bytes changed at", i, (unsigned long)h); klep_block(12, (int)id, h, 0x20, tag); } }
    }
}

#endif /* KLESCPROBE_C */
