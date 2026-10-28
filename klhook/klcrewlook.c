/*
 * klcrewlook.c - [BotFill] OnlineLooks=1: the Arcade crew look, online. The HOST draws each Ally bot's look exactly as Arcade does (klcrew.c klw_draw: a
 * character of the level's wardrobe, an outfit, a mask; never a human's body), sends it as (group digit -> look) in a 'KLSYL' packet, and EVERY seat (the host
 * too, through the same code) gives the bot with that digit the model and the variant through the game's own routines (0x783fb0, 0x88c810: klcrew.c klw_hold).
 * Part of KLHook (included by klhook.c AFTER klsync.c, klbotfill.c, klcrew.c, klcharonline.c; SHIP and TEST alike). Off unless [BotFill] OnlineLooks=1.
 * Design: re/crew_online_1028.md (a bot's model is local rendering; there is no carrier in the game's own online messages). NOTHING HERE HAS RUN IN THE GAME.
 * No .text patch. Calls of game routines only from the game's thread (klcl_tick is called from klh_tick).
 *
 * WHICH BOT IS WHICH: the group digit of the actor's group name (klbotfill.c klbf_lk_name; byte 0x12 of Glazer_Bodyguard_0N). Arcade's crew record index is digit - 1
 * (0x588980: group name[0x12] - '1'), so the online table is indexed by digit - 1 and klw_r.b[digit - 1] is that bot's klcrew.c book-keeping, as in Arcade.
 * A bot whose digit is unreadable or outside 2..8, or that shares its digit with another actor, is not touched (logged).
 *
 * KLSYL (little endian, UDP 27415 broadcast from the host, the same socket as KLSY2; an old receiver skips any magic it does not know)
 *    0   8   "KLSYL\0\0\0"
 *    8   u32 T       the host's klsy_T()
 *   12   u16 n       records, at most 16 (at most 7 are sent: digits 2..8)
 *   14   u8  ver = 1
 *   15   u8  flags = 0
 *   16   u32 epoch   FNV(session, GetTickCount() at the draw); a new value = a new draw
 *   20   u32 wsig    FNV of the wardrobe key, version, step, masks, headbase, n and every root: both seats must have the same wardrobe
 *   24   n x 12 { u8 digit (2..8), u8 ch (KLChar 1..16, 0 = keep the body), u8 outfit, u8 mask (klchar's choice number, 1 = own face), u32 root, u16 variant, u16 0 }
 * The client drops the packet when wsig differs from its own, and a record whose root is not its own wardrobe's root of ch. The variant is only compared (logged):
 * the client works it out itself from (ch, outfit, mask) with klcrew.c's klw_variant_of.
 * Send schedule: at the draw, every 1000 ms for the first 20 s of an epoch, then every 5 s (UDP); at once on a new epoch.
 *
 * HOST draw conditions (Arcade parity): [Crew] Random=1, the level gate klx_level_verdict == 2 (on a stock map Arcade's crew changes nothing, so neither does this:
 * a conflict with 'every feature on the 9 stock FA maps too' that is for the owner to decide at the Arcade level), session mode 4, state 0x13..0x19, the census
 * of the Ally bots still for [Crew] Settle ms, the local player readable (klchar.c's own swap goes first). Honoured: [Crew] Seed, DogDays, DeadMen, Include,
 * Outfits, Masks, MaskChance, PaydayMasks and the KLWardrobe.ini wardrobe. Voice, Names and the voice table are NOT touched online.
 *
 * LOG (every apply, one line per bot: seat = HOST / CLIENT)
 *   botfill: looks: HOST draw epoch=%08lx, %d bot(s), wsig %08lx (wardrobe of %s: %d characters)
 *   botfill: looks: HOST digit %d: %s (ch %d), outfit %d, mask %d, root %lu, variant %d
 *   botfill: looks: HOST send epoch=%08lx n=%d (%d bytes, sendto %d)
 *   botfill: looks: CLIENT rx epoch=%08lx n=%d T=%lu from a.b.c.d: %d record(s) taken
 *   botfill: looks: <SEAT> seat digit=%d actor=%08lx: applied | NOT taken | pending | skipped: <why>   (look ch outfit mask root variant in the text)
 */
#ifndef KLCREWLOOK_C
#define KLCREWLOOK_C

struct klcl_e { BYTE have, ch, outfit, mask; DWORD root; WORD variant; };
struct klcl_a { DWORD epoch, actor; int last; };
static struct {
    DWORD sm, epoch, T, wsig, epochAt, sendAt, cenAt, cenGap, since, sig, badSig;
    int role, n, host, srcSet, toldSend, toldRx;
    unsigned long srcAddr;
    struct klcl_e e[8];
    struct klcl_a a[8];
} klcl_t;

#define KLCL_FNV(h, x) ((h) = ((h) ^ (DWORD)(x)) * 16777619u)

static const char *klcl_seat(void) { return klcl_t.role == 2 ? "HOST" : "CLIENT"; }

static void klcl_reset(void)
{
    if (!klcl_t.sm && !klcl_t.epoch) return;
    memset(&klcl_t, 0, sizeof klcl_t);
    memset(klw_r.b, 0, sizeof klw_r.b);
}

static void klcl_sync_sm(DWORD sm)
{
    if (klcl_t.sm != sm) { klcl_reset(); klcl_t.sm = sm; }
}

/* the wardrobe fingerprint both seats must share */
static DWORD klcl_wsig(const struct klw_src *s)
{
    DWORD h = 2166136261u; int i; const char *k;
    for (k = s->key; *k; k++) KLCL_FNV(h, (BYTE)*k);
    KLCL_FNV(h, s->wardrobe); KLCL_FNV(h, s->version); KLCL_FNV(h, s->step); KLCL_FNV(h, s->masks); KLCL_FNV(h, s->headbase); KLCL_FNV(h, s->n);
    for (i = 0; i < s->n; i++) KLCL_FNV(h, s->c[i].root);
    return h;
}

/* this seat's wardrobe (klcrew.c klw_source) and the rules object; 0 = not readable yet */
static int klcl_src(struct klw_src *src, DWORD *rules)
{
    static int told;
    DWORD gs, hero[8]; char scene[160], key[64]; int i;
    *rules = 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLW_SETTINGS))) || !(*rules = klh_rd32(gs + 0x54))) return 0;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return 0;
    memset(hero, 0, sizeof hero);
    klh_rd(*rules + 0x208, hero, sizeof hero);      /* the online rules keep the heister table here too (klcharonline.c, A1HIRE3); only the no-wardrobe fallback reads it */
    klw_source(src, hero, key);
    if (!src->wardrobe) for (i = 0; i < 8; i++) if (!hero[i]) { if (!told++) klog("botfill: looks: no wardrobe and the stock hero table is not filled yet: waiting"); return 0; }
    return 1;
}

/* the local player's body model (klcrew.c finds him the same way); 0 = not readable */
static DWORD klcl_pmodel(void)
{
    DWORD gd, player, pnode, m = 0; BYTE b = 0xff;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &b, 1) || b > 3) return 0;
    if (!(player = klh_rd32(gd + 0x828 + 4 * b)) || !(pnode = klh_rd32(player + 4)) || !klh_rd(pnode + 0x68, &m, 4)) return 0;
    return m;
}

/* Arcade's klw_level_tick returns unless player+0x273c == 2 ("a policeman after his death: leave the crew as it is"): the host draws / redraws only while it is a heister */
static int klcl_heister(void)
{
    DWORD gd, player; BYTE b = 0xff, type = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &b, 1) || b > 3) return 0;
    if (!(player = klh_rd32(gd + 0x828 + 4 * b)) || !klh_rd(player + 0x273c, &type, 1)) return 0;
    return type == 2;
}

/* the characters the OTHER humans wear / chose (klcharonline.c's peer table, effective = after its uniqueness rule); ex[c] = 1 */
static void klcl_humans(const struct klw_src *src, char ex[KLC_NCHAR + 1])
{
    int j;
    memset(ex, 0, KLC_NCHAR + 1);
    for (j = 0; j < KLCO_N; j++) {
        int c;
        if (!klco.p[j].used || j == klco.ownIdx) continue;
        c = klco_effective(j, klco.p[j].c);
        if (c >= 1 && c <= src->n && c <= KLC_NCHAR) ex[c] = 1;
    }
}

/* one line per bot and outcome, not again until the outcome or the epoch changes */
static void klcl_note(int idx, DWORD actor, int code, const char *what)
{
    struct klcl_a *a = &klcl_t.a[idx];
    if (a->last == code) return;
    a->last = code;
    klog("botfill: looks: %s seat digit=%d actor=%08lx: %s", klcl_seat(), idx + 1, (unsigned long)actor, what);
}

/* the census's Ally actors -> seen[] (rec = digit - 1) and hp[]; an actor without a usable digit, or one of two with the same digit, is left out and said once per set */
static int klcl_bots(const struct klbf_lkrec *lk, int nlk, struct klw_seen *seen, float *hp, DWORD *sig)
{
    int cnt[10], i, n = 0; DWORD h = 2166136261u, bs = 2166136261u;
    memset(cnt, 0, sizeof cnt);
    for (i = 0; i < nlk; i++) if (lk[i].digit >= '2' && lk[i].digit <= '8') cnt[lk[i].digit - '0']++;
    for (i = 0; i < nlk; i++) {
        int d = lk[i].digit - '0';
        KLCL_FNV(h, lk[i].slot); KLCL_FNV(h, lk[i].actor); KLCL_FNV(h, (BYTE)lk[i].digit);
        if (d < 2 || d > 8 || cnt[d] != 1 || !lk[i].model || n >= KLW_NREC) { KLCL_FNV(bs, lk[i].actor); KLCL_FNV(bs, (BYTE)lk[i].digit); KLCL_FNV(bs, lk[i].model != 0); continue; }
        memset(&seen[n], 0, sizeof seen[n]);
        seen[n].rec = d - 1; seen[n].actor = lk[i].actor; seen[n].node = klh_rd32(lk[i].actor + 4); seen[n].model = lk[i].model;
        klh_rd(lk[i].actor + 0x50, &seen[n].variant, 4);
        hp[n] = lk[i].hp;
        seen[n].status = (BYTE)(seen[n].node && hp[n] > 0 ? 0 : 1);      /* as Arcade's status byte: a dead bot is not in the draw (it gets ch 0); GUESS: aboard is not readable online, so only dead counts */
        n++;
    }
    if (bs != klcl_t.badSig && bs != 2166136261u) {
        klcl_t.badSig = bs;
        for (i = 0; i < nlk; i++) {
            int d = lk[i].digit - '0';
            if (d < 2 || d > 8 || cnt[d] != 1 || !lk[i].model)
                klog("botfill: looks: %s seat actor=%08lx slot=%lu group=\"%s\" digit=%c model=%08lx: skipped: %s", klcl_seat(), (unsigned long)lk[i].actor, (unsigned long)lk[i].slot, lk[i].name, lk[i].digit, (unsigned long)lk[i].model,
                     d >= 2 && d <= 8 && cnt[d] > 1 ? "another actor has the same digit" : !lk[i].model ? "no readable model" : "no usable group digit (2..8)");
        }
    }
    for (i = 1; i < n; i++) {      /* Arcade walks the crew records in order (rec = digit - 1): the same [Crew] Seed then gives the same bot -> character mapping */
        struct klw_seen t = seen[i]; float th = hp[i]; int j = i - 1;
        while (j >= 0 && seen[j].rec > t.rec) { seen[j + 1] = seen[j]; hp[j + 1] = hp[j]; j--; }
        seen[j + 1] = t; hp[j + 1] = th;
    }
    *sig = h;
    return n;
}

static void klcl_bump(DWORD now)
{
    DWORD h = 2166136261u;
    KLCL_FNV(h, klcl_t.sm); KLCL_FNV(h, now); KLCL_FNV(h, klcl_t.epoch);
    klcl_t.epoch = h ? h : 1;
    klcl_t.T = (DWORD)klsy_T(); klcl_t.epochAt = now; klcl_t.sendAt = 0; klcl_t.toldSend = 0;
    memset(klcl_t.a, 0, sizeof klcl_t.a);
}

/* ---------------------------------------------------------------- the host: send */
static void klcl_send(DWORD sm, DWORD now)
{
    char pk[24 + 16 * 12]; klsy_sin a; DWORD T; WORD n = 0; int i, len, r;
    if (!klcl_t.host || !klcl_t.epoch || klcl_t.sm != sm) return;
    if (klcl_t.sendAt && (LONG)(now - klcl_t.sendAt) < 0) return;
    klcl_t.sendAt = now + ((DWORD)(now - klcl_t.epochAt) < 20000u ? 1000u : 5000u);
    if (!klcl_t.sendAt) klcl_t.sendAt = 1;
    memset(pk, 0, sizeof pk);
    for (i = 1; i < 8; i++) {      /* index = digit - 1; digits 2..8 */
        const struct klcl_e *e = &klcl_t.e[i]; char *q = pk + 24 + n * 12;
        if (!e->have) continue;
        q[0] = (char)(i + 1); q[1] = (char)e->ch; q[2] = (char)e->outfit; q[3] = (char)e->mask;
        memcpy(q + 4, &e->root, 4); memcpy(q + 8, &e->variant, 2);
        n++;
    }
    T = (DWORD)klsy_T();
    memcpy(pk, "KLSYL\0\0\0", 8); memcpy(pk + 8, &T, 4); memcpy(pk + 12, &n, 2); pk[14] = 1; pk[15] = 0;
    memcpy(pk + 16, &klcl_t.epoch, 4); memcpy(pk + 20, &klcl_t.wsig, 4);
    len = 24 + n * 12;
    memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
    r = klsy.sendto(klsy.sock, pk, len, 0, &a, sizeof a);
    if (!klcl_t.toldSend) { klcl_t.toldSend = 1; klog("botfill: looks: HOST send epoch=%08lx n=%d (%d bytes, sendto %d)", (unsigned long)klcl_t.epoch, (int)n, len, r); }
}

/* ---------------------------------------------------------------- the client: receive (called from klsy_tick's drain, game thread) */
static void klcl_rx(const char *pk, int len, DWORD now, unsigned long from)
{
    struct klw_src src; DWORD sm, state = 0, rules, epoch, wsig, T; WORD n; int i, taken = 0;
    (void)now;
    if (len < 24 || memcmp(pk, "KLSYL", 5)) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !klh_rd(sm + 0x70, &state, 4) || state < 0x13 || state > 0x19) return;
    memcpy(&n, pk + 12, 2); memcpy(&T, pk + 8, 4); memcpy(&epoch, pk + 16, 4); memcpy(&wsig, pk + 20, 4);
    if (pk[14] != 1 || n > 16 || 24 + n * 12 > len || !epoch || T >= 1000000000u) return;      /* klsy_T() never reaches 1e9: a bigger T is garbage */
    if (klsy.srcSet && from != klsy.srcAddr) return;      /* the host that sent the round's first valid list */
    klcl_sync_sm(sm);
    if (klcl_t.host) return;      /* this seat drew the table itself */
    if (klcl_t.srcSet && from != klcl_t.srcAddr) return;
    if (klcl_t.epoch) {
        if (epoch == klcl_t.epoch) return;      /* a repeat: nothing changes */
        /* klsy_T() is the clock in ms modulo 1e9, not 2^32: the forward distance (mod 1e9) of 1 .. 5e8-1 is newer, anything else (0 or more than half the modulus) is an older epoch that came late */
        { DWORD fwd = (T + 1000000000u - klcl_t.T % 1000000000u) % 1000000000u; if (fwd == 0 || fwd >= 500000000u) return; }
    }
    if (!klcl_src(&src, &rules)) return;      /* not readable yet: the host resends */
    if (klcl_wsig(&src) != wsig) {
        static DWORD told; if (told != epoch) { told = epoch; klog("botfill: looks: CLIENT rx epoch=%08lx dropped: wardrobe fingerprint %08lx here, %08lx at the host (another KLWardrobe.ini / level?)", (unsigned long)epoch, (unsigned long)klcl_wsig(&src), (unsigned long)wsig); }
        return;
    }
    if (!klcl_t.srcSet) { klcl_t.srcSet = 1; klcl_t.srcAddr = from; }
    memset(klcl_t.e, 0, sizeof klcl_t.e); memset(klcl_t.a, 0, sizeof klcl_t.a);
    for (i = 0; i < n; i++) {
        const BYTE *q = (const BYTE *)pk + 24 + i * 12; DWORD root; WORD var; int d = q[0];
        memcpy(&root, q + 4, 4); memcpy(&var, q + 8, 2);
        if (d < 2 || d > 8 || q[1] > src.n || q[1] > KLC_NCHAR || q[3] < 1) { klog("botfill: looks: CLIENT rx record %d refused: digit %d ch %d mask %d", i, d, q[1], q[3]); continue; }
        if (q[3] > KLC_MASKS + 1 || q[3] > 1 + (src.wardrobe ? src.masks : 1) || (q[1] && (q[2] >= KLC_OUTFITS || q[2] >= src.c[q[1] - 1].bodies * src.c[q[1] - 1].heads) && q[2] != 0)) {
            klog("botfill: looks: CLIENT rx record %d refused: outfit %d / mask %d out of this wardrobe's range (ch %d, %d masks)", i, q[2], q[3], q[1], src.wardrobe ? src.masks : 1); continue;
        }
        if (q[1] && root != src.c[q[1] - 1].root) { klog("botfill: looks: CLIENT digit %d: skipped: root %lu sent, %lu here for ch %d", d, (unsigned long)root, (unsigned long)src.c[q[1] - 1].root, q[1]); continue; }
        klcl_t.e[d - 1].have = 1; klcl_t.e[d - 1].ch = q[1]; klcl_t.e[d - 1].outfit = q[2]; klcl_t.e[d - 1].mask = q[3]; klcl_t.e[d - 1].root = root; klcl_t.e[d - 1].variant = var;
        taken++;
    }
    klcl_t.epoch = epoch; klcl_t.T = T; klcl_t.wsig = wsig; klcl_t.n = taken; klcl_t.epochAt = now; klcl_t.role = 3;
    klog("botfill: looks: CLIENT rx epoch=%08lx n=%d T=%lu from %lu.%lu.%lu.%lu: %d record(s) taken", (unsigned long)epoch, (int)n, (unsigned long)T, from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24, taken);
}

/* ---------------------------------------------------------------- the host: draw */
static void klcl_host_draw(const struct klw_src *src, const struct klw_seen *seen, int n, DWORD pmodel, DWORD state, DWORD rules, DWORD now)
{
    char ex[KLC_NCHAR + 1]; int i;
    klcl_humans(src, ex);
    if (!klco.on) { static int told; if (!told++) klog("botfill: looks: HOST: [CharOnline] is off, so the other players' bodies are not known: only the host's own body is kept out of the bots' draw"); }
    klw_draw(src, seen, n, klw_char_of(src, pmodel), state, rules, ex);
    memset(klcl_t.e, 0, sizeof klcl_t.e); klcl_t.n = 0;
    for (i = 0; i < n; i++) {
        int rec = seen[i].rec; const struct klw_bot *b = &klw_r.b[rec]; struct klcl_e *e = &klcl_t.e[rec];
        e->have = 1; e->ch = (BYTE)b->ch;
        if (b->ch) { e->outfit = (BYTE)b->outfit; e->mask = (BYTE)b->mask; e->root = src->c[b->ch - 1].root; e->variant = (WORD)klw_variant_of(src, b, 1); }
        else e->mask = 1;
        klcl_t.n++;
    }
    klcl_t.wsig = klcl_wsig(src); klcl_t.host = 1;
    klcl_bump(now);
    klog("botfill: looks: HOST draw epoch=%08lx, %d bot(s), wsig %08lx (wardrobe of %s: %d characters)", (unsigned long)klcl_t.epoch, n, (unsigned long)klcl_t.wsig, src->key, src->n);
    for (i = 0; i < n; i++) {
        const struct klcl_e *e = &klcl_t.e[seen[i].rec];
        if (e->ch) klog("botfill: looks: HOST digit %d: %s (ch %d), outfit %d, mask %d, root %lu, variant %d", seen[i].rec + 1, src->c[e->ch - 1].name, e->ch, e->outfit, e->mask - 1, (unsigned long)e->root, e->variant);
        else klog("botfill: looks: HOST digit %d: keeps his body (no character left)", seen[i].rec + 1);
    }
}

/* a human now wears (or chose) the character a bot was given: that bot is drawn again from the characters nobody has; the new epoch goes out at once */
static int klcl_host_redraw(const struct klw_src *src, DWORD pmodel, DWORD now)
{
    char ex[KLC_NCHAR + 1], taken[KLC_NCHAR + 1]; int i, j, changed = 0, pch = klw_char_of(src, pmodel), choice = klc_on ? (int)klc_char : 0;
    klcl_humans(src, ex);
    if (pch) ex[pch] = 1;
    if (choice >= 1 && choice <= src->n) ex[choice] = 1;
    for (i = 1; i < 8; i++) {
        struct klcl_e *e = &klcl_t.e[i]; struct klw_bot *b = &klw_r.b[i]; int c;
        if (!e->have || !e->ch || !ex[e->ch]) continue;
        memcpy(taken, ex, sizeof taken);
        for (j = 1; j < 8; j++) if (klcl_t.e[j].have && klcl_t.e[j].ch) taken[klcl_t.e[j].ch] = 1;
        c = klw_pick(src, taken);
        klog("botfill: looks: HOST digit %d wore a body a human has now (ch %d): drawn again -> %s", i + 1, e->ch, c ? src->c[c - 1].name : "keeps his body");
        b->used = 1; b->ch = c;
        if (c) { klw_dress(src, b); e->ch = (BYTE)c; e->outfit = (BYTE)b->outfit; e->mask = (BYTE)b->mask; e->root = src->c[c - 1].root; e->variant = (WORD)klw_variant_of(src, b, 1); }
        else { e->ch = 0; e->mask = 1; e->root = 0; e->variant = 0; }
        changed = 1;
    }
    if (changed) { klcl_t.wsig = klcl_wsig(src); klcl_bump(now); }
    return changed;
}

/* ---------------------------------------------------------------- every seat: apply the table to the bots */
static int klcl_apply(const struct klw_src *src, struct klw_seen *seen, const float *hp, int n, DWORD pmodel)
{
    struct klw_seen list[KLW_NREC]; int na = 0, i, done = 1; char what[200];
    if (!klw_code_ok()) return 0;
    for (i = 0; i < n; i++) {
        struct klw_seen *q = &seen[i]; int idx = q->rec; struct klcl_e *e = &klcl_t.e[idx]; struct klcl_a *a = &klcl_t.a[idx]; const struct klw_chr *c; DWORD vt;
        if (idx < 0 || idx > 7 || !e->have) continue;
        if (a->epoch != klcl_t.epoch || a->actor != q->actor) { a->epoch = klcl_t.epoch; a->actor = q->actor; a->last = 0; memset(&klw_r.b[idx], 0, sizeof klw_r.b[idx]); }
        if (!e->ch) { klcl_note(idx, q->actor, 10, "skipped: the draw keeps his body"); continue; }
        if (e->ch > src->n) { klcl_note(idx, q->actor, 11, "skipped: character outside this wardrobe"); continue; }
        c = &src->c[e->ch - 1];
        if (e->root != c->root) { klcl_note(idx, q->actor, 12, "skipped: root differs from this wardrobe's"); continue; }
        if (!q->node || hp[i] <= 0) { klcl_note(idx, q->actor, 13, "skipped: dead or downed (no scene node / health <= 0)"); continue; }      /* dead counts as done (Arcade skips a dead bot by its status); the 2 s cadence still re-reads every bot */
        if (c->root == pmodel) { klcl_note(idx, q->actor, 14, "skipped: the local player wears this body"); continue; }
        vt = klh_rd32(q->actor);      /* the REAL vtable (a puppet's private copy too): slot 119 must be the rebuild routine the model call ends in */
        if (!vt || klh_rd32(vt + 4 * 119) != KLW_REBUILD) { snprintf(what, sizeof what, "skipped: vtable %08lx slot 119 is not the rebuild routine", (unsigned long)vt); klcl_note(idx, q->actor, 15, what); continue; }
        klw_r.b[idx].used = 1; klw_r.b[idx].actor = q->actor; klw_r.b[idx].ch = e->ch; klw_r.b[idx].outfit = e->outfit; klw_r.b[idx].mask = e->mask;
        list[na++] = *q;
    }
    if (!na) return 1;
    klw_hold(src, list, na, pmodel, 1, 0, 0);
    for (i = 0; i < na; i++) {
        const struct klw_seen *q = &list[i]; int idx = q->rec; const struct klcl_e *e = &klcl_t.e[idx]; const struct klw_bot *b = &klw_r.b[idx];
        DWORD m = 0, v = 0; int want, code; const char *res;
        if (!klh_rd32(q->actor + 4) || !klh_rd(klh_rd32(q->actor + 4) + 0x68, &m, 4) || !klh_rd(q->actor + 0x50, &v, 4)) { klcl_note(idx, q->actor, 16, "skipped: model / variant unreadable after the call"); done = 0; continue; }
        want = klw_variant_of(src, b, v);
        if (m == e->root && (int)v == want) { code = 1; res = "applied"; }
        else if (m != e->root && b->tries >= klw.tries) { code = 2; res = "NOT taken (the model call did not change the model)"; }
        else if (m == e->root && b->looks >= KLW_LOOKCALLS) { code = 4; res = "variant set back by the game 64 times: left alone"; }
        else { code = 3; res = "pending"; }
        if (code != 1 && code != 2 && code != 4) done = 0;
        snprintf(what, sizeof what, "%s (look ch %d, outfit %d, mask %d, root %lu, variant %d; wears model %lu variant %lu, tries %d)", res, e->ch, e->outfit, e->mask - 1, (unsigned long)e->root, want, (unsigned long)m, (unsigned long)v, b->tries);
        klcl_note(idx, q->actor, code, what);
    }
    return done;
}

static void klcl_tick(int game_thread)
{
    static struct klbf_lkrec lk[64]; static char toldRand, toldScene[160]; static int toldVerdict;
    struct klw_seen seen[KLW_NREC]; float hp[KLW_NREC]; struct klw_src src;
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, rules, pmodel, sig; int nlk, n, i, done;
    if (!klcl_on || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) { klcl_reset(); return; }
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return;
    if (state < 0xd || state >= 0x1f || (role != 2 && role != 3) || mode != 4) { klcl_reset(); return; }      /* the next round draws again, under a new epoch */
    if (state < 0x13 || state > 0x19) return;
    klcl_sync_sm(sm); klcl_t.role = (int)role;
    if (role == 3 && !klcl_t.epoch) return;      /* an old host, or nothing received yet: today's behaviour */
    if ((LONG)(now - klcl_t.cenAt) < (LONG)klcl_t.cenGap) return;
    klcl_t.cenAt = now; klcl_t.cenGap = 500;
    if (role == 2) {
        char scene[160], why[200]; int v;
        if (!klw.random) { if (!toldRand++) klog("botfill: looks: HOST: [Crew] Random=0: Arcade changes no bot look with it off, so online changes none either"); return; }
        if (!klx_on || !klh_scene(scene, sizeof scene)) return;
        if ((v = klx_level_verdict(scene, why)) != 2) {
            if (v && (strcmp(scene, toldScene) || v != toldVerdict)) { snprintf(toldScene, sizeof toldScene, "%s", scene); toldVerdict = v; klog("botfill: looks: HOST: level '%s' %s (%.150s): no bot look is drawn (as in Arcade)", scene, v == 1 ? "is the STOCK one of its slot" : "is not known", why); }
            return;
        }
    }
    if (!klcl_src(&src, &rules) || !(pmodel = klcl_pmodel())) return;
    nlk = klbf_ally_census(lk, 64, NULL);
    n = klcl_bots(lk, nlk, seen, hp, &sig);
    if (sig != klcl_t.sig) { klcl_t.sig = sig; klcl_t.since = now; return; }      /* everything must stand still: klchar.c's swap of the player goes first */
    if ((LONG)(now - klcl_t.since) < klw.settle) return;
    if (role == 2) {
        int need = !klcl_t.host, heister = klcl_heister();      /* a cop / dead / spectating host: no new draw, no redraw; the looks already sent keep being sent and applied */
        for (i = 0; i < n && !need; i++) if (!klcl_t.e[seen[i].rec].have) need = 1;      /* a bot the draw does not know */
        if (need) { if (n && heister) klcl_host_draw(&src, seen, n, pmodel, state, rules, now); }
        else if (heister) klcl_host_redraw(&src, pmodel, now);
    }
    if (!klcl_t.epoch || !n) { if (!n || (role == 2 && !klcl_heister())) klcl_t.cenGap = 2000; return; }      /* no bot, or a host that cannot draw now: the slow cadence; 500 ms only while a draw can still come */
    done = klcl_apply(&src, seen, hp, n, pmodel);
    if (done) klcl_t.cenGap = 2000;
}

#endif /* KLCREWLOOK_C */
