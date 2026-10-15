/*
 * klbotdown.c - THE AI HEISTERS GO 'DOWN, NOT DEAD' (track Y2b, 2026-10-12). Part of KLHook (included by klhook.c
 * BEFORE kladren.c; its tick runs BEFORE kad_tick). OFF unless [BotDown] Enable=1. NOT RUN IN THE GAME.
 * Reading and the live checks: re\bots_down.md.
 *
 * THE OWNER: 'so the ai heisters are 1:1 with you' (the human is knocked down by police fire, lies, gets up slowly, can be
 * helped up; re\player_down.md, re\adrenaline.md).
 *
 * WHY THE GAME NEVER DID IT (READ, kl2.exe 0490): a soldier's damage routine (ZSoldier slot 96 = 0x8473a0) writes the new
 * health with the actor's set-health slot (0x84789d -> 0x792bc0 -> 0x61efd0, which clamps to [0, maximum]) and ONLY AT
 * HEALTH 0 asks for a down: soldier slot 51 (0x847968 = 0x688190, a dog says no, else a plain jump to 0x70e0e0) with the
 * hit record and 0. 0x70e0e0 then runs a list of refusals (re\player_down.md 11.1): a. already down, b. 0x70f330 (a hit
 * animation plays, somebody holds him, he sits, the 16 mesh probes of 1 m), c. was down once, d. a head hit within 15 m,
 * e. damage over 1,000, f/g. the modifier / the level-wide pause. In 267 of 267 logged cases it said no and nobody
 * established which test. The killing hit is the WORST moment to ask: its own hit animation runs, and c / d / e / g are
 * all about THAT hit.
 *
 * WHAT THIS PART DOES INSTEAD (data reads, ONE game call, no patch, no private vtable):
 *   1. It never lets him reach 0 by the many small hits that kill the crew (3 a second, 1 .. 21 each): the tick runs once
 *      a frame (klhook.c: SteamAPI_RunCallbacks in the main loop), so a bot is seen between two hits.
 *   2. When his health is at or under DownPct of his maximum (default 30 %), the hook ASKS THE DOWN ITSELF, outside the hit:
 *      the same call the damage routine makes (soldier vtable +0xcc = 0x688190 -> 0x70e0e0), with NO HIT RECORD (the game
 *      handles a missing record: 0x70e29e .. 0x70e2ab, attacker 0) and the SECOND ARGUMENT 1 (the 'force' flag the routine
 *      has: [ebp+0xc] <> 0 jumps over c, d, e at 0x70e12d and over f / g at 0x70e1fc to 0x70e29e). What can still refuse is
 *      a and b only - and b is a property of the bot's situation NOW, not of a hit: the call is repeated every 100 ms for
 *      RefuseMs (3 s), so it is asked again once his hit animation is over or he has moved.
 *   3. While it is refused, his health is held at FloorPct (6 %) at least: the next bullet cannot take the last of it. After
 *      RefuseMs he is let go (he dies like a stock heister at the next hits) and the line says why.
 *   4. The game's own down does the rest: the goal is pushed (0x6cabf0), byte [actor+0x64c] = 1, 0.1 s without damage,
 *      the goal's start (slot 1 = 0x7ea990) raises his health to 25 % if he has less and writes the tick he lies until
 *      ([dnd+0x14], 1.5 .. 3.0 s), the script (0x5f4ac0) lays him down, takes hits in FULL while he lies (a second health
 *      0 kills him: refusal a - so police CAN finish him), gives him 75 % at the get-up and ends the goal. This part adds
 *      only DATA to that: LieSeconds (the tick written once the game has written its own), FreeSeconds (bit 0x800 of the
 *      'no damage' word, never while the vehicle drives out), LiePct / UpPct (health on the floor / when up), NoFire
 *      (the soldier's target [soldier+0xb0] cleared each pass: the script fires only at a target - ASSUMED).
 *   5. DownsMax (2) downs a life: his 'was down once' byte [actor+0x5cb] is not looked at (flag 1 skips refusal c).
 *
 * KEYS ([BotDown]):
 *   Enable=0   Dry=0 (1 = log only: nothing is written, nothing is called)   Log=1 (2 = every pass of a down)
 *   DownPct=30  FloorPct=6  PreShield=1  DownsMax=2  RefuseMs=4000  LieSeconds=6 (0 = the game's 1.5 .. 3.0; a GUESS)  FreeSeconds=0.75
 *   LiePct=0 (0 = the game's 25)  UpPct=0 (0 = the game's 75)  NoFire=0 (ASSUMED safe: live check B3)  Traitors=1
 *   AttrMs=1500 (a human's hit counts as the cause if his sum on the victim rose this long before the down)
 *   WatchSeconds=8 (the down byte standing this long after the lie is over = the goal never ran: the byte is cleared)
 *
 * EXPORTS for kladren.c (re\bots_down.md 8):  klbd_is_down(record)   klbd_speed(record, rate)   klbd_by(record)
 *
 * WHILE THE LOCAL HUMAN IS POLICE (klfed.c's fed; 2026-10-14, the owner on Retomoto: 'issues with being able to kill them as a
 * fed - they take so much damage, but if they're a traitor I can headshot one bullet'). KLHook.log 20:29:47 .. 20:31:37: every
 * loyal heister the fed fought went down at 30 % (the hook asked), was out of reach of damage while the game refused (PreShield,
 * up to RefuseMs = 8 s in the owner's ini) and for FreeSeconds (5 s) on the floor, and GOT UP WITH FULL HEALTH (378 of 378)
 * - twice a life: about three health bars of 378 (Tough 1.5) against a stock 252. The 'traitor' kills (the TRAITOR pay =
 * the heister who had killed you, records 4 / 3 at 20:37:21 / 20:44:03) went from above 30 % to 0 in ONE frame (no
 * 'is at' line): a head shot is x 10 on an NPC, so it skips everything this part does - one shot. Not a traitor rule of
 * this part (Traitors=1: traitors are handled as the loyal are). So while [player+0x2723] is set (klbalance.c's
 * klr_local_police; 0 in the off-game harness):
 *   FedDowns=0      downs the HOOK asks in a life while you are police (0 = none: no PreShield, no floor - he dies at 0 like
 *                   any NPC; the game's own down at health 0 of a body hit can still happen once, as stock)
 *   FedFree=0       FreeSeconds while you are police (0 = a downed heister takes your hits at once)
 *   FedUpPct=25     the health a heister gets up with while you are police, per cent of his maximum (0 = the game's full)
 *   FedHealth=0     per cent of the round's maximum an AI heister has while you are police (0 = 100 / [Balance] Tough, the
 *                   stock 252 at Tough 1.5; 100 = leave). Written once per bot at the same share (never heals or hurts);
 *                   put back when you are no longer police or the round ends, if the game has not written another.
 * As a heister nothing of this acts: every key above is read only while the police byte is set.
 *
 * NOT DONE: the belly-flop dive clip (the game's down plays Down_Not_Dead_Get_Down, onto the side: the state graph 0x730be0
 * is shared with the police); an attacker for the down (the hit record is not at hand: attacker 0 - the human's share is
 * read from the rules' sum A[0][victim], klgrudge.c's float, instead); a point-blank step or a left-behind kill from above
 * the threshold in ONE frame still kills (as stock): [Balance] PointBlankToCrew shrinks the first.
 */
#define KLBD_C

#define KLBD_SOLDIER_VT 0x00bd0954
#define KLBD_SLOT51     0x00688190            /* soldier vtable +0xcc: a dog says no, else a jump to 0x70e0e0 */
#define KLBD_DOWNFN     0x0070e0e0
#define KLBD_CLOCK      0x00dd2640            /* +0x48 the game's tick (1/1024 s) */
#define KLBD_ROUND      0x19
#define KLBD_NHIT       12                    /* rows of the rules' hit-sum matrix (klgrudge.c KLY_NROW) */

#define KLBD_BTEST_FN   0x0070f330            /* the b test of 0x70e0e0, thiscall on the ZDownNotDeadNPC; read whole (reots_down.md 9) */
#ifndef KLBD_BTEST
#define KLBD_BTEST(dnd) ((BYTE (__fastcall *)(void *, void *))(DWORD_PTR)KLH_VA(KLBD_BTEST_FN))((void *)(DWORD_PTR)(dnd), 0)
#endif
#ifndef KLBD_CALL                             /* the harness replaces the call */
#define KLBD_CALL(soldier) ((BYTE (__fastcall *)(void *, void *, void *, int))(DWORD_PTR)KLH_VA(KLBD_SLOT51))((void *)(DWORD_PTR)(soldier), 0, 0, 1)
#endif

static struct {
    int on, dry, log, downs_max, nofire, traitors;
    float down_pct, floor_pct, lie, free_t, lie_pct, up_pct, refuse, attr, watch; int preshield;
    float lie_far, lie_far_at;      /* LieFar / LieFarAt (2026-10-15): the lie when the human is not near (nobody can help) */
    int fed_downs; float fed_free, fed_up, fed_health;      /* while the local human is police (klfed.c's fed) */
} klbd;

static struct klbd_rec {
    DWORD actor, soldier;
    BYTE down, gaveup, shield, lie_done, pct_done, said, dryseen, mine;
    int downs, tries, by;
    DWORD tick_down, l0, lie_tick, first_try, last_try, spd_last, a_tick, watch_log;
    float prevA, hp, hmax;
    BYTE fed_done; DWORD fed_h; float fed_from, fed_to;     /* FedHealth: the health object written and the maximum before / after */
} klbd_r[KLB_NREC];
static struct { DWORD rules; int told_code, fed; } klbd_g;

/* the local human is police (klfed.c's fed): klbalance.c reads the byte; the off-game harness has no klbalance.c */
#ifndef KLBD_FED
#ifdef KLBALANCE_C
#define KLBD_FED() klr_local_police()
#define KLBD_TOUGH() ((klr.on && klr.tough > 0) ? klr.tough : 1.0f)
#else
#define KLBD_FED() 0
#define KLBD_TOUGH() 1.0f
#endif
#endif

/* ---------------------------------------------------------------- pure arithmetic (tested off the game) */

/* the threshold in health points: DownPct of the maximum, never under 1 */
static float klbd_thresh(float hmax, float pct) { float t = hmax * pct / 100.0f; return t < 1.0f ? 1.0f : t; }

/* the floor a pending bot is held at: FloorPct of the maximum, but under the threshold and at least 1 */
static float klbd_floor(float hmax, float fpct, float thresh)
{
    float f = hmax * fpct / 100.0f;
    if (f > thresh) f = thresh;
    return f < 1.0f ? 1.0f : f;
}

/* a downed bot's lie tick pulled earlier (the same arithmetic as kladren.c's kad_lie_step; never earlier than tick + 2,
   never later than cur; a pass longer than half a second is a stall and gives nothing) */
static DWORD klbd_lie_step(DWORD cur, DWORD tick, DWORD dt, float rate, DWORD *done)
{
    long left = (long)(cur - tick), take, nl;
    *done = 0;
    if (left <= 2 || rate <= 1.0f || dt == 0 || dt > 512) return cur;
    take = (long)((rate - 1.0f) * (float)dt);
    nl = left - take; if (nl < 2) nl = 2;
    *done = (DWORD)(left - nl);
    return tick + (DWORD)nl;
}

static int klbd_fin(float f) { return f == f && f > -1e9f && f < 1e9f; }
static float klbd_rdf(DWORD at, int *ok) { float f = 0; if (!klh_rd(at, &f, 4) || !klbd_fin(f)) { *ok = 0; return 0; } return f; }

/* ---------------------------------------------------------------- reading a bot */

static int klbd_bot_ok(DWORD actor, DWORD *soldier)
{
    DWORD s;
    if (!actor || klh_rd32(actor) != KLB_ACTOR_VT) return 0;
    if (!(s = klh_rd32(actor + 0x77c)) || klh_rd32(s) != KLBD_SOLDIER_VT || klh_rd32(s + 0x40) != actor) return 0;
    *soldier = s;
    return 1;
}

/* is the call this build knows the one the soldier's slot 51 holds? (once per round, said once) */
static int klbd_callable(void)
{
    static const BYTE cb[16] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x34, 0x56, 0x8b, 0xf1, 0xe8, 0xd2, 0xa9, 0xf0, 0xff, 0x84, 0xc0 };      /* 0x70f330 */
    static const BYTE c51[16] = { 0x55, 0x8b, 0xec, 0x8b, 0x81, 0xd8, 0x06, 0x00, 0x00, 0x83, 0x38, 0x06, 0x75, 0x06, 0x32, 0xc0 };
    static const BYTE cdn[16] = { 0x55, 0x8b, 0xec, 0x83, 0xec, 0x10, 0x56, 0x8b, 0xf1, 0x8b, 0x4e, 0x40, 0x8b, 0x01, 0x8b, 0x90 };
    int ok = klh_rd32((DWORD_PTR)KLH_VA(KLBD_SOLDIER_VT + 0xcc)) == KLBD_SLOT51 && klb_same_code(KLBD_SLOT51, c51, sizeof c51) && klb_same_code(KLBD_DOWNFN, cdn, sizeof cdn) && klb_same_code(KLBD_BTEST_FN, cb, sizeof cb);
    if (!ok && !klbd_g.told_code++) klog("botdown: the soldier's down routine (slot 51 = 0x688190 -> 0x70e0e0) is not the one this build knows: nothing is called, nothing is written");
    return ok;
}

/* why the game said NO: what can be read (a, the hit animation, holder, seat, attachment) and, when asked, the game's own b test
   (0x70f330 called on his dnd: bt = 1 yes, 0 no, -1 not asked). The 16 mesh probes are not readable; they are the verdict when b
   says NO and none of the readable parts does. Offline (reots_down.md 9): a probe fails when the 100-unit segment from his place
   leaves the navigation mesh, i.e. he stands within 1 m of a mesh edge (a wall, a cover box) or off the mesh. */
static void klbd_why(DWORD actor, DWORD soldier, int bt, char *out, int n)
{
    DWORD wo, ao, ws = 0, as = 0, holder = 0, seat = 0, s18 = 0, s40 = 0, att = 0; BYTE dn = 0; int hitanim, seated;
    if ((wo = klh_rd32(soldier + 0x4b4)) != 0) klh_rd(wo + 8, &ws, 4);
    if ((ao = klh_rd32(soldier + 0xa4)) != 0) klh_rd(ao + 8, &as, 4);
    klh_rd(actor + 0x774, &holder, 4); klh_rd(actor + 0x88c, &seat, 4); klh_rd(actor + 0x5b4, &att, 4); klh_rd(actor + 0x64c, &dn, 1);
    if (seat) { klh_rd(seat + 0x18, &s18, 4); klh_rd(seat + 0x40, &s40, 4); }
    hitanim = as != 0 && as != 4; seated = seat && s18 && !s40;
    snprintf(out, n, "ZHitAnimTask state %lu%s; b test %s; %s", (unsigned long)as, hitanim ? " (RUNS: no down while a hit animation plays)" : "",
        bt < 0 ? "not asked" : bt ? "YES" : "NO",
        dn ? "a: he is down already" :
        ws != 0 && ws != 4 ? "a: his ZWounded state runs" :
        holder ? "b: somebody holds him" :
        seated ? "b: he sits in a seat" :
        hitanim ? "b: the hit animation (asked again)" :
        bt == 1 ? "b passes, so the refusal is a (ZWounded / down) or the dog rule" :
        att ? "b: attached to an object (refused if a ZHavokLnkObj), bone 2 low, or the mesh probes" :
        "b: the 16 mesh probes of 1 m / bone 2: he stands within 1 m of the edge of the navigation mesh (a wall, a cover box) or off it");
}

/* the bit of FreeSeconds: on = hold 0x800 of the 'takes no damage' word, off = take it off (never another bit) */
static void klbd_shield(struct klbd_rec *b, int on)
{
    DWORD o = klh_rd32(b->actor + 0x54); WORD w = 0, nw;
    if (!o || !klh_rd(o + 0x3a, &w, 2)) return;
    nw = on ? (WORD)(w | 0x800) : (WORD)(w & ~0x800);
    if (nw != w && !klh_data((void *)(DWORD_PTR)(o + 0x3a), &nw, 2, "an AI heister's 'takes no damage' word: the down-not-dead bit 0x800 (botdown)")) return;
    b->shield = (BYTE)on;
}

/* FedHealth put back: his maximum as it was, his health at the same share - only when the object is still his and still
   holds our maximum (another value = the game wrote one: left alone) */
static void klbd_fed_undo(struct klbd_rec *b, int i, const char *why)
{
    DWORD h; int ok = 1; float hp, hmax, nh;
    if (!b->fed_done) return;
    b->fed_done = 0;
    if (!b->actor || klh_rd32(b->actor) != KLB_ACTOR_VT || !(h = klh_rd32(b->actor + 0x5fc)) || h != b->fed_h || klh_rd32(h + 0x24) != b->actor) return;
    hp = klbd_rdf(h + 4, &ok); hmax = klbd_rdf(h + 8, &ok);
    if (!ok || fabsf(hmax - b->fed_to) > 0.5f || b->fed_to < 1.0f) { if (klbd.log) klog("botdown: record %d: FedHealth not put back (%s): his maximum is %.1f, not the %.1f written", i, why, hmax, b->fed_to); return; }
    nh = hp > 0.01f ? hp * b->fed_from / b->fed_to : hp;
    if (klh_data((void *)(DWORD_PTR)(h + 8), &b->fed_from, 4, "an AI heister's maximum health put back (botdown FedHealth)")) {
        if (hp > 0.01f) klh_data((void *)(DWORD_PTR)(h + 4), &nh, 4, "an AI heister's health at the same share (botdown FedHealth put back)");
        if (klbd.log) klog("botdown: record %d: FedHealth put back (%s): maximum %.1f -> %.1f, health %.1f -> %.1f", i, why, b->fed_to, b->fed_from, hp, hp > 0.01f ? nh : hp);
    }
}

/* everything of ours off one bot */
static void klbd_back(struct klbd_rec *b)
{
    DWORD s = 0;
    if (b->actor && b->shield && klbd_bot_ok(b->actor, &s) && s == b->soldier) klbd_shield(b, 0);
    if (b->fed_done) klbd_fed_undo(b, (int)(b - klbd_r), "the hook lets go of him");
    memset(b, 0, sizeof *b);
}

/* ---------------------------------------------------------------- exports */

static int klbd_is_down(int record)
{
    BYTE d = 0;
    if (!klbd.on || record < 0 || record >= KLB_NREC || !klbd_r[record].actor) return 0;
    return klh_rd(klbd_r[record].actor + 0x64c, &d, 1) && d;
}

/* the human record whose bullets took his health shortly before the down, or -1 */
static int klbd_by(int record) { return (record >= 0 && record < KLB_NREC && klbd.on) ? klbd_r[record].by : -1; }

/* pull a downed bot's lie earlier (a helper stands by): -> 1 when the tick was written. The part's own LieSeconds write yields
   to it for good. rate 3.0 = three times as fast as time runs. */
static int klbd_speed(int record, float rate)
{
    struct klbd_rec *b; DWORD clock, tick = 0, dnd, cur, nw, done = 0, dt;
    if (!klbd.on || klbd.dry || record < 0 || record >= KLB_NREC) return 0;
    b = &klbd_r[record];
    if (!b->actor || !b->down || !(clock = klh_rd32((DWORD_PTR)KLH_VA(KLBD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return 0;
    dt = b->spd_last ? tick - b->spd_last : 0; b->spd_last = tick;
    if (!(dnd = klh_rd32(b->soldier + 0x4b8)) || klh_rd32(dnd + 4) != b->soldier) return 0;
    cur = klh_rd32(dnd + 0x14); nw = klbd_lie_step(cur, tick, dt, rate, &done);
    b->lie_done = 1;
    return nw != cur && klh_data((void *)(DWORD_PTR)(dnd + 0x14), &nw, 4, "an AI heister's down-not-dead: the tick he lies until (botdown, a helper)");
}

/* ---------------------------------------------------------------- one pass */

static void klbd_forget(void)
{
    int i;
    for (i = 0; i < KLB_NREC; i++) if (klbd_r[i].actor) klbd_back(&klbd_r[i]);
    memset(&klbd_g, 0, sizeof klbd_g);
}

static void klbd_tick(int game_thread)
{
    struct klb_snap sn; DWORD rules, state, clock, tick = 0; int level, i, fed, downs_max; float free_t, fed_k; char why[200];
    if (!klbd.on || !game_thread || !klh_exe_ok) return;
    if (!(klr_arcade(&rules, &state, &level) && klb_level(why) && state == KLBD_ROUND && klb_read(&sn) && sn.state == KLBD_ROUND)) { if (klbd_g.rules) klbd_forget(); return; }
    if (sn.rules != klbd_g.rules) {
        klbd_forget(); klbd_g.rules = sn.rules;
        klog("botdown: a round runs (Arcade, not the stock level: %s); %d crew record(s); DownPct %.0f %% FloorPct %.0f %% DownsMax %d LieSeconds %.1f FreeSeconds %.2f NoFire %d%s",
             why, sn.n, klbd.down_pct, klbd.floor_pct, klbd.downs_max, klbd.lie, klbd.free_t, klbd.nofire, klbd.dry ? " - Dry: nothing is called, nothing is written" : "");
    }
    if (!(clock = klh_rd32((DWORD_PTR)KLH_VA(KLBD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    /* the local human is police: the fed's own rules (header) */
    fed = KLBD_FED() ? 1 : 0;
    fed_k = klbd.fed_health > 0 ? klbd.fed_health / 100.0f : 1.0f / KLBD_TOUGH();
    if (fed_k < 0.05f) fed_k = 0.05f; if (fed_k > 10.0f) fed_k = 10.0f;
    if (fed != klbd_g.fed) {
        klbd_g.fed = fed;
        if (fed) klog("botdown: you are POLICE: the AI heisters get %d down(s) asked by the hook a life (FedDowns; PreShield / floor only for those), FreeSeconds %.2f (FedFree), get up with %s, maximum health x %.3f (FedHealth%s)%s",
                      klbd.fed_downs, klbd.fed_free, klbd.fed_up > 0 ? "FedUpPct of the maximum" : "the game's (full)", fed_k, klbd.fed_health > 0 ? "" : " = 1 / [Balance] Tough",
                      klbd.dry ? " - Dry: nothing is written" : "");
        else klog("botdown: you are no longer police: DownsMax %d, FreeSeconds %.2f, UpPct %.0f again; FedHealth is put back", klbd.downs_max, klbd.free_t, klbd.up_pct);
    }
    downs_max = fed ? klbd.fed_downs : klbd.downs_max;
    free_t = fed ? klbd.fed_free : klbd.free_t;
    for (i = 0; i < sn.n && i < KLB_NREC; i++) {
        const struct klb_rec *r = &sn.r[i]; struct klbd_rec *b = &klbd_r[i];
        DWORD s = 0, h, dnd; BYTE dn = 0; float hp, hmax, thr, pos[3] = { 0, 0, 0 }; int hok = 1, have, pend_now = 0;
        if (!r->used || !(r->flags & 1) || !klbd_bot_ok(r->actor, &s)) { if (b->actor) klbd_back(b); continue; }
        if (!klbd.traitors && (r->flags & 2)) continue;
        if (b->actor != r->actor || b->soldier != s) { if (b->actor) klbd_back(b); b->actor = r->actor; b->soldier = s; b->by = -1; b->prevA = r->hit; }
        if (!(h = klh_rd32(r->actor + 0x5fc)) || klh_rd32(h + 0x24) != r->actor) continue;
        hp = klbd_rdf(h + 4, &hok); hmax = klbd_rdf(h + 8, &hok);
        if (!hok || hmax < 1.0f || hmax > 100000.0f || !klh_rd(r->actor + 0x64c, &dn, 1)) continue;
        thr = klbd_thresh(hmax, klbd.down_pct);
        /* the human's share of his health taken (klgrudge.c's float, per cent of the maximum): a rise = his bullet */
        if (i < KLBD_NHIT && klbd_fin(r->hit) && r->hit > b->prevA + 0.001f) b->a_tick = tick;
        if (i < KLBD_NHIT) b->prevA = r->hit;
        dnd = klh_rd32(s + 0x4b8); if (dnd && klh_rd32(dnd + 4) != s) dnd = 0;
        if (!b->said) { b->said = 1; if (klbd.log >= 2) klog("botdown: record %d (actor %08lx): health %.1f of %.1f; a down is asked at %.1f or less, held at %.1f", i, (unsigned long)r->actor, hp, hmax, thr, klbd_floor(hmax, klbd.floor_pct, thr)); }
        have = kle_node(klh_rd32(r->actor + 4), pos, 0);
        /* FedHealth: once per bot while you are police, at the same share; put back when you are not */
        if (!fed && b->fed_done) { klbd_fed_undo(b, i, "you are no longer police"); hok = 1; hp = klbd_rdf(h + 4, &hok); hmax = klbd_rdf(h + 8, &hok); if (!hok || hmax < 1.0f) continue; thr = klbd_thresh(hmax, klbd.down_pct); }
        if (fed && !b->fed_done && !klbd.dry && r->status == 0 && hp > 0.01f && fabsf(fed_k - 1.0f) > 0.001f) {
            float nmax = hmax * fed_k, nh = hp * fed_k;
            b->fed_done = 1; b->fed_h = h; b->fed_from = hmax; b->fed_to = nmax;
            if (klh_data((void *)(DWORD_PTR)(h + 8), &nmax, 4, "an AI heister's maximum health while you are police (botdown FedHealth)") &&
                klh_data((void *)(DWORD_PTR)(h + 4), &nh, 4, "an AI heister's health at the same share (botdown FedHealth)")) {
                if (klbd.log) klog("botdown: record %d%s: maximum %.1f -> %.1f, health %.1f -> %.1f (FedHealth x %.3f: you are police)", i, (r->flags & 2) ? " (TRAITOR)" : "", hmax, nmax, hp, nh, fed_k);
                hp = nh; hmax = nmax; thr = klbd_thresh(hmax, klbd.down_pct);
            } else { b->fed_done = 0; }
        }

        if (r->status != 0) {                                            /* aboard / escaped / dead */
            if (b->down) { klog("botdown: record %d left play while down (%s) after %.2f s", i, r->status == 7 ? "he DIED" : "status other than in-play", (float)(long)(tick - b->tick_down) / 1024.0f); b->down = 0; }
            if (b->first_try && !b->down && r->status == 7) klog("botdown: record %d DIED while a down was pending (%d try(s), %s)", i, b->tries, b->gaveup ? "the part had given up" : "one frame took more than the floor held");
            b->first_try = b->last_try = 0; b->tries = 0;
            if (b->shield) klbd_shield(b, 0);
            continue;
        }
        /* the vehicle drives out: the game kills the crew left behind (1,000,000 damage) - no new down, no shield */
        if (b->shield && sn.veh >= 5) { klbd_shield(b, 0); if (klbd.log >= 2) klog("botdown: record %d: the 'no damage' bit is taken off (the vehicle drives out)", i); }

        if (!b->down && dn) {
            /* ---- he is down (ours or the game's own) */
            b->down = 1; b->tick_down = tick; b->lie_done = 0; b->pct_done = 0; b->spd_last = 0; b->watch_log = 0;
            if (!b->mine) b->downs++;
            b->by = (b->a_tick && (long)(tick - b->a_tick) <= (long)(klbd.attr * 1024.0f) && sn.human >= 0) ? sn.human : -1;
            klog("botdown: record %d IS DOWN, NOT DEAD (%d of %d) at (%.0f, %.0f, %.0f) - %s; health %.1f of %.1f; %s; put down by %s",
                 i, b->downs, klbd.downs_max, have ? pos[0] : 0, have ? pos[1] : 0, have ? pos[2] : 0, b->mine ? "the HOOK asked and the game said YES" : "the game did it by itself",
                 hp, hmax, "the tick he lies until is written by the game's goal a frame later (the next 'he lies until' line)",
                 b->by >= 0 ? "a human's bullet (his sum on this bot rose just before)" : "nobody known (police, or no rise of the human's sum)");
            b->l0 = dnd ? klh_rd32(dnd + 0x14) : 0;
        } else if (b->down && !dn) {
            /* ---- he is up */
            b->down = 0; b->mine = 0; b->first_try = b->last_try = 0; b->tries = 0; b->gaveup = 0;
            if (b->shield) klbd_shield(b, 0);
            klog("botdown: record %d IS UP after %.2f s at (%.0f, %.0f, %.0f): health %.1f of %.1f (READ in B2: the game's get-up gave FULL health, 252 of 252, twice - not the 75 %% the script's constant suggests), heist stage %u", i, (float)(long)(tick - b->tick_down) / 1024.0f,
                 have ? pos[0] : 0, have ? pos[1] : 0, have ? pos[2] : 0, hp, hmax, (unsigned)r->stage);
            {
                float up = fed ? klbd.fed_up : klbd.up_pct;
                if (!klbd.dry && up > 0 && hp > 0.01f && fabsf(hp - hmax * up / 100.0f) > 0.5f) {
                    float nh = hmax * up / 100.0f;
                    if (klh_data((void *)(DWORD_PTR)(h + 4), &nh, 4, "an AI heister's health: what he has when he is up from his down (botdown UpPct / FedUpPct)")) { klog("botdown: record %d: up with %.1f of %.1f (%s=%.0f; the game gave %.1f)", i, nh, hmax, fed ? "FedUpPct" : "UpPct", up, hp); hp = nh; }
                }
            }
            b->by = -1;
        }
        if (b->down) {
            /* ---- he lies */
            if (klbd.dry) { b->hp = hp; b->hmax = hmax; continue; }
            if (dnd && !b->lie_done) {
                DWORD cur = klh_rd32(dnd + 0x14);
                if (cur != b->l0 || (long)(tick - b->tick_down) > 1024) {      /* slot 1 (0x7ea990) wrote its own tick: ours goes in, once */
                    if (klbd.lie > 0 && (long)(cur - b->tick_down) >= 1400) {      /* under 1.4 s = a helper (kladren.c) pulled it already: not put back */
                        float lie = klbd.lie, far_m = -1.0f; const char *lkey = "LieSeconds"; DWORD want;
                        if (klbd.lie_far > 0 && klbd.lie_far < lie) {      /* LieFar: the human is not near him - nobody will come to help, the long lie only costs the crew time */
                            DWORD hpl = 0; float hf[3], hn[3];
                            if (have && kle_human(&hpl, hf, hn)) far_m = sqrtf((hf[0] - pos[0]) * (hf[0] - pos[0]) + (hf[1] - pos[1]) * (hf[1] - pos[1]) + (hf[2] - pos[2]) * (hf[2] - pos[2])) / 100.0f;
                            if (far_m < 0 || far_m > klbd.lie_far_at) { lie = klbd.lie_far; lkey = "LieFar"; }
                        }
                        want = b->tick_down + (DWORD)(lie * 1024.0f);
                        if ((long)(want - tick) > 0 && cur != want && klh_data((void *)(DWORD_PTR)(dnd + 0x14), &want, 4, "an AI heister's down-not-dead: the tick he lies until (botdown LieSeconds)")) {
                            b->lie_tick = want; klog("botdown: record %d: he lies until tick %ld (%s=%.1f, you %.1f m away (-1 = not in play); the game had %ld = %.2f s)", i, (long)want, lkey, lie, far_m, (long)cur, (float)(long)(cur - b->tick_down) / 1024.0f);
                        }
                    }
                    b->lie_done = 1;
                }
            }
            if (!b->pct_done && (b->lie_done || (long)(tick - b->tick_down) > 1024)) {      /* the game has given him its 25 % by now */
                b->pct_done = 1;
                if (klbd.lie_pct > 0 && hp > 0.01f && fabsf(hp - hmax * klbd.lie_pct / 100.0f) > 0.5f) {
                    float nh = hmax * klbd.lie_pct / 100.0f;
                    if (klh_data((void *)(DWORD_PTR)(h + 4), &nh, 4, "an AI heister's health on the floor (botdown LiePct)")) { klog("botdown: record %d: %.1f of %.1f on the floor (LiePct=%.0f; the game gave %.1f)", i, nh, hmax, klbd.lie_pct, hp); hp = nh; }
                }
            }
            if (free_t > 0 && sn.veh < 5 && (long)(tick - b->tick_down) < (long)(free_t * 1024.0f)) klbd_shield(b, 1);
            else if (b->shield) klbd_shield(b, 0);
            if (klbd.nofire) {
                DWORD tgt = 0, zero = 0;
                if (klh_rd(s + 0xb0, &tgt, 4) && tgt && klh_data((void *)(DWORD_PTR)(s + 0xb0), &zero, 4, "an AI heister's target, cleared while he lies (botdown NoFire)") && klbd.log >= 2)
                    klog("botdown: record %d: his target [soldier+0xb0] %08lx cleared (NoFire)", i, (unsigned long)tgt);
            }
            /* the watchdog: the goal's script ends at once when 0x70f330 fails at its start - the byte then stays set for good */
            {
                float lie = klbd.lie > 0 ? klbd.lie : 3.0f;
                if ((long)(tick - b->tick_down) > (long)((lie + klbd.watch) * 1024.0f) && (long)(tick - b->tick_down) > 0) {
                    BYTE zero = 0;
                    if (klh_data((void *)(DWORD_PTR)(r->actor + 0x64c), &zero, 1, "an AI heister's down byte (botdown watchdog: the goal never ran)"))
                        klog("botdown: record %d: the down byte stood %.1f s (lie %.1f + WatchSeconds %.1f): the goal's script never ended it - the byte is cleared, he is a plain heister again", i, (float)(long)(tick - b->tick_down) / 1024.0f, lie, klbd.watch);
                }
            }
        } else if (hp <= 0.01f) {
            /* dead (or about to be) without a down: said once by the klbot line; here only the verdict on this part */
            if (b->tries || b->first_try) { klog("botdown: record %d DIED at health 0 while a down was pending (%d try(s), %s)", i, b->tries, b->gaveup ? "the part had given up" : "the floor did not hold: one frame took more than the floor"); }
            b->first_try = b->last_try = 0; b->tries = 0;
        } else if (hp > thr) {
            /* healthy again: a new episode */
            b->first_try = b->last_try = 0; b->tries = 0; b->gaveup = 0; b->dryseen = 0;
        } else if (!b->gaveup && b->downs < downs_max && sn.veh < 5 && r->status == 0) {
            /* ---- at or under the threshold, standing: ask for the down */
            float fl = klbd_floor(hmax, klbd.floor_pct, thr);
            if (klbd.dry) {
                if (!b->dryseen++) klog("botdown: Dry - record %d is at %.1f of %.1f (<= %.1f): the hook WOULD ask the game's down now (soldier %08lx, slot 51, no hit, force 1) and hold his health at %.1f; down %d of %d", i, hp, hmax, thr, (unsigned long)s, fl, b->downs + 1, klbd.downs_max);
                continue;
            }
            if (!b->first_try) { b->first_try = tick; klog("botdown: record %d is at %.1f of %.1f (<= %.1f = DownPct %.0f %%): the game's down is asked (0x70e0e0 through slot 51, no hit record, force 1)", i, hp, hmax, thr, klbd.down_pct); }
            pend_now = 1;
            if (klbd.preshield) klbd_shield(b, 1);       /* no hit can take his health while the game is asked (the same 0x800 bit as FreeSeconds; at most RefuseMs) */
            if (hp < fl) { klh_data((void *)(DWORD_PTR)(h + 4), &fl, 4, "an AI heister's health: held at the floor while his down is asked (botdown FloorPct)"); hp = fl; }
            if (!b->last_try || (long)(tick - b->last_try) >= 102) {          /* every 100 ms */
                BYTE ok;
                if (!klbd_callable()) { b->gaveup = 1; continue; }
                b->last_try = tick; b->tries++;
                b->mine = 1;
                ok = (BYTE)KLBD_CALL(s);
                klh_rd(r->actor + 0x64c, &dn, 1);
                if (ok && dn) {
                    /* the next pass sees the byte and logs the down; the lie tick is read there */
                    b->downs++;
                    if (klbd.log >= 2) klog("botdown: record %d: the game said YES at try %d (%.2f s after the first)", i, b->tries, (float)(long)(tick - b->first_try) / 1024.0f);
                } else {
                    char w[420]; int bt = -1; b->mine = 0;
                    if (dnd && (b->tries == 1 || klbd.log >= 2 || (long)(tick - b->first_try) > (long)(klbd.refuse / 1000.0f * 1024.0f))) bt = KLBD_BTEST(dnd) ? 1 : 0;
                    klbd_why(r->actor, s, bt, w, sizeof w);
                    if (b->tries == 1 || klbd.log >= 2) klog("botdown: record %d: the game said NO at try %d (returned %u, down byte %u) - %s", i, b->tries, (unsigned)ok, (unsigned)dn, w);
                    if ((long)(tick - b->first_try) > (long)(klbd.refuse / 1000.0f * 1024.0f)) {
                        b->gaveup = 1;
                        klog("botdown: record %d: refused for %.1f s (%d tries): he gets NO down this time and dies like a stock heister at the next hits (last reason: %s)", i, (float)(long)(tick - b->first_try) / 1024.0f, b->tries, w);
                    }
                }
            }
        }
        if (b->shield && !b->down && !pend_now) klbd_shield(b, 0);      /* the pre-YES shield ends with the asking */
        b->hp = hp; b->hmax = hmax;
    }
}

/* ---------------------------------------------------------------- init */

static float klbd_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("BotDown", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

static void klbd_init(void)
{
    memset(&klbd, 0, sizeof klbd); memset(klbd_r, 0, sizeof klbd_r); memset(&klbd_g, 0, sizeof klbd_g);
    klbd.on = GetPrivateProfileIntA("BotDown", "Enable", 0, klh_ini) != 0;
    if (!klbd.on) return;
    klbd.dry = GetPrivateProfileIntA("BotDown", "Dry", 0, klh_ini) != 0;
    klbd.log = GetPrivateProfileIntA("BotDown", "Log", 1, klh_ini);
    klbd.downs_max = GetPrivateProfileIntA("BotDown", "DownsMax", 2, klh_ini);
    if (klbd.downs_max < 1) klbd.downs_max = 1; if (klbd.downs_max > 9) klbd.downs_max = 9;
    klbd.nofire = GetPrivateProfileIntA("BotDown", "NoFire", 0, klh_ini) != 0;
    klbd.traitors = GetPrivateProfileIntA("BotDown", "Traitors", 1, klh_ini) != 0;
    klbd.down_pct = klbd_inif("DownPct", "30", 1.0f, 60.0f);
    klbd.floor_pct = klbd_inif("FloorPct", "6", 0.0f, 30.0f);
    klbd.refuse = klbd_inif("RefuseMs", "4000", 0.0f, 20000.0f);
    klbd.preshield = GetPrivateProfileIntA("BotDown", "PreShield", 1, klh_ini) != 0;
    klbd.lie = klbd_inif("LieSeconds", "6", 0.0f, 15.0f);
    if (klbd.lie > 0 && klbd.lie < 0.5f) klbd.lie = 0.5f;
    klbd.lie_far = klbd_inif("LieFar", "0", 0.0f, 15.0f); if (klbd.lie_far > 0 && klbd.lie_far < 0.5f) klbd.lie_far = 0.5f;      /* 0 = off */
    klbd.lie_far_at = klbd_inif("LieFarAt", "25", 2.0f, 500.0f);
    klbd.free_t = klbd_inif("FreeSeconds", "0.75", 0.0f, 15.0f);      /* 15 (was 5) = the whole LieSeconds (2026-10-15, run v70_T1E: four downed bots were shot dead 7 .. 12 s into a 15 s lie) */
    klbd.lie_pct = klbd_inif("LiePct", "0", 0.0f, 100.0f);
    klbd.up_pct = klbd_inif("UpPct", "0", 0.0f, 100.0f);
    klbd.attr = klbd_inif("AttrMs", "1500", 0.0f, 20000.0f) / 1000.0f;
    klbd.watch = klbd_inif("WatchSeconds", "8", 3.0f, 60.0f);
    klbd.fed_downs = GetPrivateProfileIntA("BotDown", "FedDowns", 0, klh_ini);
    if (klbd.fed_downs < 0) klbd.fed_downs = 0; if (klbd.fed_downs > klbd.downs_max) klbd.fed_downs = klbd.downs_max;
    klbd.fed_free = klbd_inif("FedFree", "0", 0.0f, 5.0f);
    klbd.fed_up = klbd_inif("FedUpPct", "25", 0.0f, 100.0f);
    klbd.fed_health = klbd_inif("FedHealth", "0", 0.0f, 1000.0f);
    if (klbd.fed_health > 0 && klbd.fed_health < 5.0f) klbd.fed_health = 5.0f;
    klog("botdown: on%s; an AI heister at %.0f %% of his health or less is put DOWN, NOT DEAD by the game's own routine (asked from the hook without a hit, force 1; floor %.0f %% while refused for up to %.0f ms), up to %d times a life; lies %s, FreeSeconds %.2f, LiePct %.0f, UpPct %.0f, NoFire %d, Traitors %d. Arcade, a level that is not stock; data writes and ONE game call (re\\bots_down.md)",
         klbd.dry ? " (Dry=1: nothing is called, nothing is written)" : "", klbd.down_pct, klbd.floor_pct, klbd.refuse, klbd.downs_max,
         klbd.lie > 0 ? "LieSeconds" : "as long as the game says", klbd.free_t, klbd.lie_pct, klbd.up_pct, klbd.nofire, klbd.traitors);
    if (klbd.lie > 0) klog("botdown: LieSeconds=%.1f (a GUESS; the game's own is 1.5 .. 3.0)", klbd.lie);
    if (klbd.lie_far > 0) klog("botdown: LieFar=%.1f: a bot that goes down more than LieFarAt=%.0f m from you (or while you are not in play) lies only that long - nobody will come to help him (run v71_T3: downed crew lay 15 s each in the street and missed the van)", klbd.lie_far, klbd.lie_far_at);
    klog("botdown: while you are police (a fed): FedDowns %d, FedFree %.2f, FedUpPct %.0f, FedHealth %s", klbd.fed_downs, klbd.fed_free, klbd.fed_up, klbd.fed_health > 0 ? "set" : "0 = 100 / [Balance] Tough");
}
