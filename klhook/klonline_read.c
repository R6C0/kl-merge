/*
 * klonline_read.c - THE ONLINE ROUND READER (2026-10-26, owner: "port EVERYTHING from arcade to online"; plan re/arcade_online_port_plan.md,
 * data re/online_round_data.md). Part of KLHook (klhook.c includes it after klhud_values.c, BEFORE klhud.c, SHIP and TEST alike).
 * READ ONLY: no write into the game, no call of a game routine, every pointer read through klh_rd / klh_rd32 (checked reads), every
 * object tested by its vtable. NOT RUN LIVE.
 *
 *   klor_read(&o, local)   fills a klor_snap: klbot.c's ONLINE snapshot (struct klb_snap, the one Arcade's klb_read_hud returns, with
 *                          OnlineCrew's handles forced on for the call) PLUS, per seat, the heister CHARACTER's name, the ZFFPlayer,
 *                          money, status, kills and the killer; per AI heister (no record online) the same from the Ally actors;
 *                          and the round state: round n of m, clock, length, the escape-vehicle mirrors.
 *   klor_bots(act)         the Ally ZFFActors (<= 8), cached 3 s, ONE scan. klor_bots_sorted() puts the living first (ONE order); klor_read and
 *                          klhud.c's klu_online_bots (the crew list's bot count) both read through that, so a bot row's number is the same bot.
 *   klor_loot(&rem)        the loot still lying on the map: sum of ZOnlineMoneyCtrl +0x34 over the game's object registry (as klbotfill.c); klor_read
 *                          also fills held (the seats' Sharable + Unsharable), loot_init (largest remaining this round) and the kill-feed events.
 *   klor_on                [Online] Read=1 (default 0): without it klor_read answers 0 and every port behind it stays at its old behaviour.
 *
 * HOW A SEAT GETS A HEISTER NAME (the Arcade rule of klcrew.c's klw_who_now, applied to the online bodies):
 *   record -> client struct [rec] -> ZFFPlayer [client+0x378] (re/round_end_online.md; GUESS the offset holds on a client) -> body model
 *   [[player+4]+0x68] -> the character whose root in the level's klw_source list (the wardrobe, else the eight heroes at
 *   [rules+0x208]; slot 136 of the rules = 0x452a40 is the plain getter [ecx+n*4+0x208], checked below) is that model -> its name.
 *   The model is what klcharonline.c (peer looks) or the game's own seat -> hero rule (slot 137) put on the body, so the name matches the
 *   body every peer sees. A body that is no heister now (a dead player who plays a policeman) keeps the last name read for that seat.
 *   Last fallbacks: the local seat's own choice (klchar.c klc_char), then "" (the caller shows the Steam name / Player n).
 *
 * GUESS list (a live bench must prove each; also in the commit message):
 *   G1 [[rec]+0x378] is the ZFFPlayer on a client as well as on the host.   G2 [rules+0x208] is the hero table on Sv and Cl.
 *   G3 the Arcade status bits (4 dead, 0x10 / 0x4000 waiting) are the online ones.   G4 KillerIndex S+0xe0 is the killer's SEAT (a bot kill reads -1/garbage).
 *   G5 the registry's ZOnlineMoneyCtrl entries may be stale after a level change (the loot total is the largest sum seen this round).
 *   G7 [rules+0x320] is an int (stock HUD money cache).   G8 death mark = deaths of the local seat counted from status bit 4 transitions this match (online has no lives).
 *   G9 the kill feed waits up to 700 ms for KillerIndex to settle after bit 4 sets; a bot/police kill reads -1 or the victim (shown 'DIED'); bot deaths are not read as events.
 *   G6 S = [rules+0x2c] exists on the client from the lobby state on (its creation site is not traced).
 *
 * KLHook.ini   [Online] Read=0 (recommended off until benched)   Log=1 (shared with klonline.c)
 */
#ifndef KLONLINE_READ_C
#define KLONLINE_READ_C

#include "klonline_read.h"

#define KLOR_SCORE_VT   0x00bd5184u        /* DDL_ZScoreFragileAlliance instance vtable (re/online_round_data.md, CERTAIN) */
#define KLOR_PLAYER_VT  0x00bb45f4u        /* ZFFPlayer (klcharonline.c's table test) */
#define KLOR_GETHERO    0x00452a40u        /* rules slot 136: mov eax,[ecx+eax*4+0x208] */
#define KLOR_REG        0x00e09e38u        /* the object registry (pointers) and its count, klbotfill.c's source of the money controllers */
#define KLOR_REGN       0x00e0e63cu
#define KLOR_MONEY_VT   0x00bc874cu        /* ZOnlineMoneyCtrl */

static struct { int on; } klor;
static struct { DWORD rules; int round, lobby; char name[KLOR_MAX][32]; int latch[KLOR_MAX]; struct klor_seatev sev[KLOR_MAX]; long loot_init; } klor_c;   /* caches re-keyed on rules / round / lobby (names, latch, feed steps, loot whole) */
static struct klor_ev klor_pend[8]; static int klor_npend;           /* deaths resolved but not yet handed to the feed */
static int klor_noev;                                                  /* set by a reader that is NOT the kill feed (klhud_board2.c's tick): it leaves the queue alone */
static struct { DWORD rules; int deaths[KLOR_MAX]; } klor_d;                                              /* the death marks: per rules (the match), NOT cleared by a new round */
static struct { DWORD at, rules; int ok; struct klw_src src; } klor_s;                                  /* the character list of the level, refreshed every 1 s */

static void klor_init(void)
{
    klor.on = GetPrivateProfileIntA("Online", "Read", 0, klh_ini) != 0;
    klog("online read: klonline_read.c %s ([Online] Read=%d); read only, NOT RUN LIVE", klor.on ? "ON" : "off", klor.on);
}

/* the level's character list (klw_source): the wardrobe, else the eight heroes of the rules object (G2). -> 1 when usable */
static int klor_source(DWORD rules)
{
    DWORD now = GetTickCount(), hero[8], vt, slot = 0; char scene[160], key[64]; int heroes = 0;
    if (klor_s.rules == rules && klor_s.at && (DWORD)(now - klor_s.at) < 1000) return klor_s.ok;
    klor_s.rules = rules; klor_s.at = now ? now : 1; klor_s.ok = 0;
    memset(hero, 0, sizeof hero);
    if ((vt = klh_rd32(rules)) != 0 && klh_rd(vt + 0x220, &slot, 4) && slot == KLOR_GETHERO && klh_rd(rules + 0x208, hero, sizeof hero)) heroes = 1;
    else { static int told; if (!told++) klog("online read: rules slot 136 = %08lx (not the plain hero getter 0x452a40): no stock hero list; only a wardrobe level gets names", slot); }
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return 0;
    klw_source(&klor_s.src, hero, key);                       /* klcrew.c: the wardrobe of this level, else the eight heroes (roots 0 when the table is not ours) */
    klor_s.ok = klor_s.src.wardrobe || heroes;
    return klor_s.ok;
}

static DWORD klor_model(DWORD actor)
{
    DWORD node = actor ? klh_rd32(actor + 4) : 0;
    return node ? klh_rd32(node + 0x68) : 0;
}

/* the character a model belongs to (1.., 0 = none) */
static int klor_char(DWORD model)
{
    int i;
    if (!model || !klor_s.ok) return 0;
    for (i = 0; i < klor_s.src.n; i++) if (klor_s.src.c[i].root == model) return i + 1;
    return 0;
}

/* the AI heisters online: ZFFActors of team 2 (Ally) in the entity table, as klbotfill.c's census (GUESS: no human heister is team 2). Cached 3 s. -> n <= 8 */
static int klor_bots(DWORD act[KLOR_NBOT])
{
    static DWORD last, cache[KLOR_NBOT]; static int n; DWORD now = GetTickCount(); int i;
    if (!last || now - last > 3000) {
        DWORD p, tab, ii, blk[64 * 32];
        last = now ? now : 1; n = 0;
        if ((p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) && (p = klh_rd32(p + 0xc)) && (tab = klh_rd32(p + 0xc)))
            for (ii = 0; ii < 0x10000 && n < KLOR_NBOT; ii += 64) {
                DWORD k;
                if (!klh_rd(tab + ii * 0x80, blk, sizeof blk)) break;
                for (k = 0; k < 64 && n < KLOR_NBOT; k++) {
                    DWORD o = blk[k * 32 + 0x60 / 4], pr, team = 99;
                    if (o < 0x10000 || klh_avt(o) != 0x00bb3bacu) continue;
                    if (!(pr = klh_rd32(o + 0x54)) || !klh_rd(pr + 4, &team, 4) || team != 2) continue;
                    cache[n++] = o;
                }
            }
    }
    for (i = 0; i < n; i++) act[i] = cache[i];
    return n;
}

/* the Ally actors, the LIVING first (health [[a+0x5fc]+4] > 0), the rest after, each group in table order. *alive = how many live. -> n <= 8 */
static int klor_bots_sorted(DWORD act[KLOR_NBOT], int *alive)
{
    DWORD raw[KLOR_NBOT]; int n = klor_bots(raw), i, a = 0, k = 0, pass;
    for (pass = 0; pass < 2; pass++)
        for (i = 0; i < n; i++) {
            DWORD hp; float hv[2] = { 0, 0 }; int live;
            if (klh_avt(raw[i]) != 0x00bb3bacu) continue;
            hp = klh_rd32(raw[i] + 0x5fc);
            live = hp && klh_rd(hp + 4, hv, 8) && hv[0] > 0;
            if (live != (pass == 0)) continue;
            act[k++] = raw[i]; if (live) a++;
        }
    if (alive) *alive = a;
    return k;
}

/* the loot still on the map: the registry of the money controllers (klbotfill.c; type +0x38 == 1 is the players' drop pool: skipped). -> 1 and *rem, 0 = nothing readable */
static int klor_loot(long *rem)
{
    DWORD rn = klh_rd32((DWORD_PTR)KLH_VA(KLOR_REGN)), reg[0x400], q, j; long sum = 0; int any = 0;
    if (rn > 0x1000) rn = 0x1000;
    for (q = 0; q < rn; q += 0x400) {
        DWORD m = rn - q < 0x400 ? rn - q : 0x400;
        if (!klh_rd((DWORD_PTR)KLH_VA(KLOR_REG) + 4 * q, reg, 4 * m)) break;
        for (j = 0; j < m; j++) {
            DWORD o = reg[j], type = 0; int amt = 0;
            if (o < 0x10000 || klh_rd32(o) != KLOR_MONEY_VT) continue;
            if (!klh_rd(o + 0x38, &type, 4) || type == 1 || !klh_rd(o + 0x34, &amt, 4) || amt <= 0) continue;
            sum += amt; any = 1;
        }
    }
    *rem = sum;
    return any;
}

/* -> 1 and *o when the online rules are up and [Online] Read=1; local = the local seat or -1 */
static int klor_read(struct klor_snap *o, int local)
{
    int save_o, save_c, r, i, k; DWORD S, vt;
    memset(o, 0, sizeof *o); o->local = local; o->b.human = -1;
    if (!klor.on || !klh_exe_ok) return 0;
    save_o = klb_hud_online; save_c = klb_hud_crew; klb_hud_online = 1; klb_hud_crew = 1;
    r = klb_read_hud(&o->b);
    klb_hud_online = save_o; klb_hud_crew = save_c;
    if (!r || !o->b.online || !o->b.rules) return 0;
    vt = klh_rd32(o->b.rules); o->host = vt == KLB_RULES_SV;
    if (klor_d.rules != o->b.rules) { klor_d.rules = o->b.rules; memset(klor_d.deaths, 0, sizeof klor_d.deaths); }
    klor_source(o->b.rules);
    /* the mirrors the base tick keeps in the rules object on Sv and Cl alike (round_online_data.md: [rules+0x4c] clock, +0x1d8 / +0x1dc / +0x1e4 the escape) */
    { float c = 0, t = 0; BYTE v = 0;
      if (klh_rd(o->b.rules + 0x4c, &c, 4) && klb_finite(c) && c >= 0 && c < 100000.0f) o->clock = c;
      if (klh_rd(o->b.rules + 0x1d8, &t, 4) && klb_finite(t) && t >= 0 && t < 100000.0f) o->esc_timer = t;
      if (klh_rd(o->b.rules + 0x1dc, &v, 1)) o->esc_state = v;
      o->vehicle = klh_rd32(o->b.rules + 0x1e4); }
    S = klh_rd32(o->b.rules + 0x2c);
    o->score = S;
    o->ok = S && klh_rd32(S) == KLOR_SCORE_VT;
    if (!o->ok) { static DWORD told; if (told != S) { told = S; klog("online read: score object [rules+0x2c] = %08lx has vtable %08lx (not 0xbd5184, G6): no kills / round / killer", (unsigned long)S, (unsigned long)(S ? klh_rd32(S) : 0)); } }
    if (o->ok) {
        signed char cur = 0, num = 0; float len = 0;
        if (klh_rd(S + 0x34c, &cur, 1) && klh_rd(S + 0x3d0, &num, 1) && klor_round_ok(cur, num)) { o->round = cur; o->rounds = num; }
        if (klh_rd(S + 0x324, &len, 4) && klb_finite(len) && len > 0 && len < 100000.0f) o->length = len;
    }
    /* re-key the caches (review #5): a new rules object, a new round number, or the lobby (state < 0x17) <-> the round: names, killer latches, feed steps and the loot whole start over
       (a seat can hold another heister next round; a stale name or a latched killer from the last round must not carry over). The death marks (klor_d) stay: they are the match's. */
    { int lobby = o->b.state < 0x17;
      if (klor_c.rules != o->b.rules || (o->round && o->round != klor_c.round) || lobby != klor_c.lobby) {
          klor_c.rules = o->b.rules; klor_c.round = o->round; klor_c.lobby = lobby; klor_c.loot_init = 0;
          memset(klor_c.name, 0, sizeof klor_c.name);
          for (i = 0; i < KLOR_MAX; i++) { klor_c.latch[i] = -1; klor_c.sev[i].prev = -1; klor_c.sev[i].at = 0; }
      } }
    /* the humans: one row per record in use (b.on_used), in seat order */
    for (k = 0; k < o->b.on_n && k < KLOR_MAX; k++) {
        struct klor_row *w; DWORD client, P, type = 0; signed char kills = 0, pk = 0, kb = -1; int dead, ch;
        if (!o->b.on_used[k] || o->n >= KLOR_MAX) continue;
        w = &o->r[o->n++];
        w->used = 1; w->seat = k; w->rec = o->b.on_rec[k]; w->flags = o->b.on_flags[k];
        w->money = o->b.on_money[k]; w->loot = o->b.on_loot[k]; w->reward = o->b.on_rew[k];
        w->killer = -1;
        client = w->rec ? klh_rd32(w->rec) : 0;
        P = client >= 0x10000 ? klh_rd32(client + 0x378) : 0;
        if (P >= 0x10000 && klh_rd32(P) == KLOR_PLAYER_VT) {
            w->player = P;
            if (klh_rd(P + 0x273c, &type, 1) && (type & 0xff) == 2) { w->actor = P; w->model = klor_model(P); }
        }
        ch = klor_char(w->model);
        if (ch >= 1) { w->ch = ch; snprintf(w->name, sizeof w->name, "%s", klor_s.src.c[ch - 1].name); snprintf(klor_c.name[k], sizeof klor_c.name[k], "%s", w->name); o->names_ok++; }
        else if (klor_c.name[k][0]) snprintf(w->name, sizeof w->name, "%s", klor_c.name[k]);
        else if (k == local && klor_s.ok && klc_char >= 1 && klc_char <= klor_s.src.n) snprintf(w->name, sizeof w->name, "%s", klor_s.src.c[klc_char - 1].name);
        dead = klor_flags_dead(w->flags);
        w->alive = !(dead || (w->flags & 0x40));
        if (o->ok && k < KLOR_SEATS) {                           /* review #4: the S arrays hold 12 seats; a seat >= 12 would read the next array */
            if (klh_rd(S + 0xec + k, &kills, 1)) w->kills = kills;
            if (klh_rd(S + 0x170 + k, &pk, 1)) w->police_kills = pk;
            if (klh_rd(S + 0xe0 + k, &kb, 1)) w->killer = kb;
        }
        w->killer = klor_killer_latch(&klor_c.latch[k], dead, w->killer, KLOR_SEATS);
        o->held += w->money > 0 ? w->money : 0;
        if (o->ok && k < KLOR_SEATS && o->b.state == 0x19) {      /* the kill feed + death marks: status bit 4 (dead) going 0 -> 1 while the round runs */
            int ek = -1, st = klor_ev_step(&klor_c.sev[k], (w->flags & 0x4u) != 0, w->killer, GetTickCount(), &ek);
            if (st & 1) klor_d.deaths[k]++;
            if ((st & 2) && klor_npend < 8) { klor_pend[klor_npend].victim = k; klor_pend[klor_npend].killer = ek; klor_npend++; }      /* queued: a reader that is not the feed (klor_noev) must not eat the event */
        } else if (o->ok && k < KLOR_SEATS) { int dummy = -1; klor_ev_step(&klor_c.sev[k], (w->flags & 0x4u) != 0, -1, GetTickCount(), &dummy); klor_c.sev[k].at = 0; }   /* not in a round: track, never emit */
        if (k == local && k < KLOR_SEATS) o->deaths = klor_d.deaths[k];
    }
    if (!klor_noev) { int q; for (q = 0; q < klor_npend && o->nev < 4; q++) o->ev[o->nev++] = klor_pend[q]; klor_npend = 0; }
    /* the loot bar's numbers: what is left on the map (cached 0.5 s, the registry scan is 0x1000 pointers) and the largest remaining seen this round */
    if (o->b.state == 0x19) {
        static DWORD at, rules; static long rem; static int ok; DWORD now = GetTickCount();
        if (rules != o->b.rules || !at || now - at >= 500) { rules = o->b.rules; at = now ? now : 1; rem = 0; ok = klor_loot(&rem); }
        if (ok) { o->loot_ok = 1; o->loot_rem = rem; o->loot_init = klor_loot_latch(&klor_c.loot_init, rem); }
        klh_rd(o->b.rules + 0x320, &o->stock_money, 4);           /* GUESS: [rules+0x320] is an int (the stock HUD's money cache, re/online_round_data.md) */
        { static DWORD ll; static int told; if (told < 40 && now - ll >= 10000) { ll = now ? now : 1; told++;
            klog("online read: loot: on the map %ld (%s), largest this round %ld, crew holds %ld (S+0x188 + S+0x224 summed), stock HUD money [rules+0x320] = %ld (local seat %d)",
                 o->loot_rem, o->loot_ok ? "read" : "NO controller read", o->loot_init, o->held, o->stock_money, o->local); } }
    }
    /* the AI heisters (no record): from the Ally actors, living first (the SAME scan and order as klhud.c's klu_online_bots: klor_bots_sorted) */
    { DWORD act[KLOR_NBOT]; int na = 0, nb = klor_bots_sorted(act, &na), a;
      for (a = 0; a < nb && o->nbots < KLOR_NBOT; a++) {
          struct klor_row *w = &o->bot[o->nbots++]; int ch;
          w->used = 1; w->seat = -1; w->bot = 1; w->actor = act[a]; w->alive = a < na; w->killer = -1;
          w->model = klor_model(act[a]); ch = klor_char(w->model);
          if (ch >= 1) { w->ch = ch; snprintf(w->name, sizeof w->name, "%s", klor_s.src.c[ch - 1].name); o->names_ok++; }
      } }
    { static DWORD last_state = 0xffffffffu; static int last_n = -1, last_nb = -1, told;
      if ((o->b.state != last_state || o->n != last_n || o->nbots != last_nb) && told < 30) {
          told++; last_state = o->b.state; last_n = o->n; last_nb = o->nbots;
          klog("online read: %s rules %08lx state 0x%lx: %d seat(s), %d bot(s), %d name(s) from bodies, round %d of %d, clock %.0f / %.0f s, vehicle state %d, score %s",
               o->host ? "HOST" : "CLIENT", (unsigned long)o->b.rules, (unsigned long)o->b.state, o->n, o->nbots, o->names_ok, o->round, o->rounds, o->clock, o->length, (int)o->esc_state, o->ok ? "ok" : "NOT readable");
      } }
    return 1;
}

#endif /* KLONLINE_READ_C */
