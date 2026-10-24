/*
 * klcardown.c - A CAR BLAST FLOORS EVERYONE IT CATCHES, IT DOES NOT KILL THEM (track CD, 2026-10-24). Part of KLHook
 * (included by klhook.c AFTER klbotdown.c, which it borrows klbd_bot_ok / klbd_callable / KLBD_CALL from). SHIP-safe:
 * data writes and game calls only, no code byte is patched. NOT RUN IN THE GAME (the owner was playing).
 *
 * THE OWNER (Hot Coffee II, 2026-10-24): 'if someone gets close to a car and it blows up, enemy ai too, it should do a down
 * animation, not the one where they have their gun out but the one where they can get revived. should happen to cops too.'
 *
 * WHY THEY DIE (READ, kl2.exe 0490, nothing run): a car's controller is a ZVehicleEffects (vtable 0xbc0f74) on the car's
 * group. Its health model (0x412430) calls Explode (0x590480) at health 0, which calls the effects (0x877f30) and the damage
 * routine 0x8ec590 once per soldier / player in the outer radius: record kind 1, amount = falloff x damage, and PLUS 10000.0
 * for a soldier or player inside the INNER radius. Fields (GUESS: fields 15..22 of the class are laid out from +0xbdc, step 4;
 * the values fit the campaign / stock numbers): [+0xbe8] outer radius (stock 350, campaign 500), [+0xbec] inner radius (stock
 * 100, campaign 300), [+0xbf4] damage (stock 100, campaign 200). The AI asks its down only at health 0, and the down routine
 * refuses a hit worth 1,000 or more (0x70e0e0, refusal e), so a man inside the inner radius simply dies; the human's down
 * trigger (0x8da3b0) takes a blast only when the record's kind is 9 (it is 1 here) and the +10000 kills him first.
 *
 * WHAT THIS PART DOES
 *   1. TUNES each car's controller once, as soon as it is seen: inner radius -> 0 (no +10000), damage -> at most Damage (60),
 *      so a blast hurts everybody in the radius by falloff x 60 but kills nobody who is not already nearly dead.
 *   2. WATCHES the controller ([+0x5ec] health <= 0, or the blow count [+0x7d4] rises) and the car's place (read each frame
 *      while it stands: GUESS candidates [fx+4], [fx+0x5e8], [[fx+0x5e8]+4], [havokcar+4]; the first sane one wins and is
 *      logged).
 *   3. AT THE BLOW, for every AI soldier (heister bot, cop, any ZFFActor with a ZSoldier, health above 0, not down) within the
 *      outer radius (the field / 100 = metres: a GUESS, logged with the distances): the game's own down is asked, the same
 *      call klbotdown.c makes (soldier slot 51 = 0x688190 -> 0x70e0e0, no hit record, force 1: skips refusals c, d, e), every
 *      100 ms for 2.5 s because the hit animation of the blast itself can refuse once (refusal b). The game's goal does the
 *      rest: the man lies 1.5 to 3 s (the 'ZDownNotDeadNPC', the 'can be helped up' lie of the heister bots, with the
 *      KLBotDown revive helpers when that part is on), gets 25 % health on the floor and 75 % when up.
 *      COPS: the same call; a cop is not helped by anybody, he stands up by himself when the lie is over (the stock goal).
 *   4. THE HUMAN: within the radius, up, a heister (not police): the game's own trigger 0x8da3b0(D, record) is called with a
 *      zeroed record of kind 9 (a blast: it skips the health and burst tests, 0x8da409) and no attacker; D = [player+0x2948]
 *      is checked (first dword = the player, [D+4] = 0 up). It runs 0x76a450, the down start, exactly as the damage routine
 *      does (0x458e7f). GUESS: the zero record is accepted by 0x49aac0 / 0x8cf030 (no attacker = the AI's 'no clue' path).
 *
 * KEYS ([CarDown]):  Enable=1 (on only on a level that is not the stock one, Arcade, a round; [KLHook] AllMaps=1 counts the
 *   stock ones too)  Dry=0 (1 = log only, nothing written, nothing called)  Log=1 (2 = every attempt)
 *   Damage=60 (0 = leave the car's damage; else the most a blast hurts at the centre)  Inner=0 (0 = no +10000 for anybody; -1 = leave)
 *   Human=1  Bots=1  Cops=1  Seconds=2.5 (how long a down is asked)  Radius=1.0 (x the controller's outer radius)
 *
 * UNPROVEN (nothing here ran): the field offsets (GUESS above), the place of the car, the unit of the radius, that capping
 * the damage leaves the chain reaction between cars alone, that 0x70e0e0 works on a cop, and the human's synthetic record.
 */
#define KLCD_C

#define KLCD_FX_VT      0x00bc0f74
#define KLCD_HUMAN_TRIG 0x008da3b0
#define KLCD_MAXCAR     24
#define KLCD_MAXACT     96

#ifndef KLCD_HUMAN_CALL                   /* the harness replaces the call; thiscall on D, one stack argument (ret 4) */
#define KLCD_HUMAN_CALL(d, rec) ((BYTE (__fastcall *)(void *, void *, void *))(DWORD_PTR)KLH_VA(KLCD_HUMAN_TRIG))((void *)(DWORD_PTR)(d), 0, (void *)(rec))
#endif

static struct {
    int on, dry, log, human, bots, cops, counttrig; float damage, inner, secs, radius;
} klcd;

struct klcd_car { DWORD fx; float hp; DWORD cnt; float pos[3]; int havepos, tuned, how; };
static struct klcd_car klcd_c[KLCD_MAXCAR];

struct klcd_ev {
    int act; DWORD t0, last; float pos[3], rad;
    int n; DWORD actor[KLCD_MAXACT], soldier[KLCD_MAXACT]; BYTE done[KLCD_MAXACT];
    int human_done; DWORD human_try;
};
static struct klcd_ev klcd_e;
static struct { DWORD rules, scan_at; int told_pos, told_unit; DWORD crew[KLB_NREC]; } klcd_g;
static int klcd_is_crew(DWORD a) { int i; for (i = 0; i < KLB_NREC; i++) if (klcd_g.crew[i] == a) return 1; return 0; }

/* ---------------------------------------------------------------- pure arithmetic */

static int klcd_fin(float f) { return f == f && f > -1e9f && f < 1e9f; }
static float klcd_dist(const float *a, const float *b)
{
    float x = a[0] - b[0], y = a[1] - b[1], z = a[2] - b[2];
    return sqrtf(x * x + y * y + z * z);
}
/* the radius in world units of the controller's outer-radius field (the field / 100: GUESS) times the key, never under 3 */
static float klcd_radius(float field, float mult)
{
    float r = field / 100.0f * mult;
    if (!klcd_fin(r) || r < 3.0f) r = 3.0f;
    if (r > 40.0f) r = 40.0f;
    return r;
}

/* ---------------------------------------------------------------- reading */

static int klcd_sane(const float p[3]) { return klcd_fin(p[0]) && klcd_fin(p[1]) && klcd_fin(p[2]) && (p[0] != 0 || p[1] != 0 || p[2] != 0) && fabsf(p[0]) < 1e5f && fabsf(p[1]) < 1e5f && fabsf(p[2]) < 1e5f; }

/* the car's place: GUESS candidates, the first that reads sane. how = 1..4, remembered. */
static int klcd_place(DWORD fx, float pos[3], int *how)
{
    DWORD a[4], so = klh_rd32(fx + 0x5e8), hc = klh_rd32(fx + 0xb94); int i;
    a[0] = klh_rd32(fx + 4); a[1] = so; a[2] = so ? klh_rd32(so + 4) : 0; a[3] = hc ? klh_rd32(hc + 4) : 0;
    for (i = 0; i < 4; i++) {
        int k = (*how > 0) ? *how - 1 : i;
        float p[3] = { 0, 0, 0 };
        if (a[k] && kle_node(a[k], p, 0) && klcd_sane(p)) { memcpy(pos, p, 12); *how = k + 1; return 1; }
        if (*how > 0) return 0;
    }
    return 0;
}

static int klcd_fx_ok(DWORD fx) { return fx >= 0x10000 && klh_rd32(fx) == KLCD_FX_VT; }

/* every ZVehicleEffects in the entity table (heap scan is not used here: the controller of a map car is an entity) */
static int klcd_scan_fx(DWORD *out, int max)
{
    DWORD p, tab, i; int n = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return 0;
    for (i = 0; i < 0x10000 && n < max; i += 64) {
        DWORD blk[64 * 32], k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < max; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o >= 0x10000 && klh_rd32(o) == KLCD_FX_VT) out[n++] = o;
        }
    }
    return n;
}

/* every soldier actor in the entity table (cops and heister bots alike) */
static int klcd_scan_actors(DWORD *act, DWORD *sol, int max)
{
    DWORD p, tab, i; int n = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return 0;
    for (i = 0; i < 0x10000 && n < max; i += 64) {
        DWORD blk[64 * 32], k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64 && n < max; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], s = 0;
            if (o >= 0x10000 && klh_rd32(o) == KLB_ACTOR_VT && klbd_bot_ok(o, &s)) { act[n] = o; sol[n] = s; n++; }
        }
    }
    return n;
}

static int klcd_alive(DWORD actor, float *hp)
{
    DWORD h = klh_rd32(actor + 0x5fc); float v = 0;
    if (!h || klh_rd32(h + 0x24) != actor || !klh_rd(h + 4, &v, 4) || !klcd_fin(v)) return 0;
    if (hp) *hp = v;
    return v > 0.01f;
}

/* ---------------------------------------------------------------- the cars */

static void klcd_tune(struct klcd_car *c, int idx)
{
    float inner = 0, dmg = 0, outer = 0, ni = 0, nd = 0; int ok = 1;
    inner = klbd_rdf(c->fx + 0xbec, &ok); outer = klbd_rdf(c->fx + 0xbe8, &ok); dmg = klbd_rdf(c->fx + 0xbf4, &ok);
    c->tuned = 1;
    if (!ok || outer < 1 || outer > 100000 || inner < 0 || inner > outer || dmg <= 0 || dmg > 100000) {   /* REVIEW 1024: the offsets are GUESSes, so a write only on a plausible triple (inner <= outer, damage > 0) */ if (klcd.log) klog("cardown: car %d (fx %08lx): the blast fields do not read as expected (outer %.1f inner %.1f damage %.1f): left alone", idx, (unsigned long)c->fx, outer, inner, dmg); return; }
    ni = klcd.inner >= 0 ? klcd.inner : inner; nd = (klcd.damage > 0 && dmg > klcd.damage) ? klcd.damage : dmg;
    if (klcd.log) klog("cardown: car %d (fx %08lx): blast outer %.0f inner %.0f damage %.0f (health %.0f) -> inner %.0f damage %.0f%s", idx, (unsigned long)c->fx, outer, inner, dmg, c->hp, ni, nd, klcd.dry ? " - Dry: nothing written" : "");
    if (klcd.dry) return;
    if (ni != inner) klh_data((void *)(DWORD_PTR)(c->fx + 0xbec), &ni, 4, "a car's blast inner radius: no +10000 on the dead-centre victims (cardown)");
    if (nd != dmg) klh_data((void *)(DWORD_PTR)(c->fx + 0xbf4), &nd, 4, "a car's blast damage capped so a blast floors, not kills (cardown Damage)");
}

static void klcd_blow(struct klcd_car *c, int idx, DWORD tick)
{
    float outer = 0; int ok = 1;
    if (!c->havepos) { klog("cardown: car %d blew (fx %08lx) but its place could not be read (the GUESS candidates all failed): nobody is floored", idx, (unsigned long)c->fx); return; }
    outer = klbd_rdf(c->fx + 0xbe8, &ok); if (!ok) outer = 350.0f;
    memset(&klcd_e, 0, sizeof klcd_e);
    klcd_e.act = 1; klcd_e.t0 = klcd_e.last = tick; memcpy(klcd_e.pos, c->pos, 12); klcd_e.rad = klcd_radius(outer, klcd.radius);
    klcd_e.n = klcd_scan_actors(klcd_e.actor, klcd_e.soldier, KLCD_MAXACT);
    klog("cardown: car %d BLEW at (%.1f, %.1f, %.1f) place via candidate %d; radius %.1f m (field %.0f / 100 x %.2f: a GUESS of the unit); %d soldier(s) in the scene%s",
         idx, c->pos[0], c->pos[1], c->pos[2], c->how, klcd_e.rad, outer, klcd.radius, klcd_e.n, klcd.dry ? " - Dry: nothing is called" : "");
}

/* ---------------------------------------------------------------- one event */

static void klcd_event(DWORD tick)
{
    struct klcd_ev *e = &klcd_e; int i, open = 0; DWORD limit = (DWORD)(klcd.secs * 1024.0f);
    if (!e->act) return;
    if ((long)(tick - e->t0) > (long)limit) { klog("cardown: the blast at (%.0f, %.0f, %.0f) is over", e->pos[0], e->pos[1], e->pos[2]); e->act = 0; return; }
    if ((long)(tick - e->last) < 102 && tick != e->t0) return;
    e->last = tick;
    for (i = 0; i < e->n; i++) {
        float p[3], hp = 0, d; BYTE dn = 0; DWORD s;
        if (e->done[i]) continue;
        if (klcd_is_crew(e->actor[i]) ? !klcd.bots : !klcd.cops) { e->done[i] = 1; continue; }
        if (!klbd_bot_ok(e->actor[i], &s) || s != e->soldier[i]) { e->done[i] = 1; continue; }
        if (!kle_node(klh_rd32(e->actor[i] + 4), p, 0) || !klcd_sane(p)) { e->done[i] = 1; continue; }
        d = klcd_dist(p, e->pos);
        if (d > e->rad) { e->done[i] = 1; continue; }
        if (!klcd_alive(e->actor[i], &hp)) { if (klcd.log) klog("cardown: soldier %08lx at %.1f m is DEAD (health %.1f): the blast killed him before the down could be asked", (unsigned long)e->actor[i], d, hp); e->done[i] = 1; continue; }
        klh_rd(e->actor[i] + 0x64c, &dn, 1);
        if (dn) { klog("cardown: soldier %08lx at %.1f m is DOWN, NOT DEAD (health %.1f)", (unsigned long)e->actor[i], d, hp); e->done[i] = 1; continue; }
        if (klcd.dry) { klog("cardown: Dry - soldier %08lx at %.1f m (health %.1f) WOULD be put down", (unsigned long)e->actor[i], d, hp); e->done[i] = 1; continue; }
        if (!klbd_callable()) { e->done[i] = 1; continue; }
        {
            BYTE ok = (BYTE)KLBD_CALL(e->soldier[i]);
            klh_rd(e->actor[i] + 0x64c, &dn, 1);
            if (klcd.log >= 2 || (ok && dn)) klog("cardown: soldier %08lx at %.1f m (health %.1f): the game's down said %s (down byte %u)", (unsigned long)e->actor[i], d, hp, ok ? "YES" : "NO, asked again", (unsigned)dn);
            if (ok && dn) e->done[i] = 1; else open++;
        }
    }
    /* the human */
    if (klcd.human && !e->human_done) {
        DWORD pl = 0, D; float feet[3], np[3]; BYTE police = 0; DWORD ds = 0; float hp = 0;
        if (kle_human(&pl, feet, np) && pl && klh_rd(pl + 0x2723, &police, 1) && !police && (D = klh_rd32(pl + 0x2948)) != 0 && klh_rd32(D) == pl && klh_rd(D + 4, &ds, 4)) {
            float d = klcd_dist(feet, e->pos), dn2 = klcd_dist(np, e->pos); DWORD ho = klh_rd32(pl + 0xa48);
            if (dn2 < d) d = dn2;
            if (d > e->rad) e->human_done = 1;
            else if (ds != 0) { klog("cardown: you are DOWN already ([D+4] %lu) %.1f m from the car", (unsigned long)ds, d); e->human_done = 1; }
            else if (!ho || !klh_rd(ho + 4, &hp, 4) || !(hp > 0.01f)) { klog("cardown: you are dead (health %.1f) %.1f m from the car: the blast was too much (the Damage cap?)", hp, d); e->human_done = 1; }
            else if (klcd.dry) { klog("cardown: Dry - you (%.1f m, health %.1f) WOULD be floored by the game's trigger 0x8da3b0 (kind 9)", d, hp); e->human_done = 1; }
            else {
                static BYTE rec[0x200];
                memset(rec, 0, sizeof rec); *(DWORD *)(rec + 8) = 9;       /* GUESS: kind 9 = a blast; attacker (rec+0) 0 */
                {
                    BYTE ok = (BYTE)KLCD_HUMAN_CALL(D, rec); DWORD ds2 = 0;
                    klh_rd(D + 4, &ds2, 4);
                    klog("cardown: you are %.1f m from the car (health %.1f): the game's trigger 0x8da3b0 (kind 9) said %s, [D+4] %lu -> %lu", d, hp, ok ? "YES" : "NO", (unsigned long)ds, (unsigned long)ds2);
                    if (ds2 != 0) e->human_done = 1; else open++;
                }
            }
        } else { e->human_done = 1; }
    }
    if (!open) e->act = 0;
}

/* ---------------------------------------------------------------- one pass */

static void klcd_forget(void) { memset(klcd_c, 0, sizeof klcd_c); memset(&klcd_e, 0, sizeof klcd_e); memset(&klcd_g, 0, sizeof klcd_g); }

static void klcd_tick(int game_thread)
{
    struct klb_snap sn; DWORD rules, state, clock, tick = 0, now; int level, i; char why[200];
    if (!klcd.on || !game_thread || !klh_exe_ok) return;
    if (!(klr_arcade(&rules, &state, &level) && klb_level(why) && state == KLB_ROUND && klb_read(&sn) && sn.state == KLB_ROUND)) { if (klcd_g.rules) klcd_forget(); return; }
    if (sn.rules != klcd_g.rules) {
        klcd_forget(); klcd_g.rules = sn.rules;
        klog("cardown: a round runs (Arcade, not the stock level: %s); a car blast floors the AI and you (Damage cap %.0f, Inner %.0f, Bots %d Cops %d Human %d)%s",
             why, klcd.damage, klcd.inner, klcd.bots, klcd.cops, klcd.human, klcd.dry ? " - Dry: nothing is called, nothing is written" : "");
    }
    if (!(clock = klh_rd32((DWORD_PTR)KLH_VA(KLBD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    now = GetTickCount();
    { DWORD cr[KLB_NREC]; memset(cr, 0, sizeof cr); for (i = 0; i < sn.n && i < KLB_NREC; i++) if (sn.r[i].used && sn.r[i].actor) cr[i] = sn.r[i].actor; memcpy(klcd_g.crew, cr, sizeof cr); }
    /* find new controllers (every 2 s) */
    if (!klcd_g.scan_at || now - klcd_g.scan_at >= 2000) {
        DWORD fx[KLCD_MAXCAR * 2]; int n = klcd_scan_fx(fx, KLCD_MAXCAR * 2), k;
        klcd_g.scan_at = now;
        for (k = 0; k < n; k++) {
            int have = 0, free_ = -1;
            for (i = 0; i < KLCD_MAXCAR; i++) { if (klcd_c[i].fx == fx[k]) have = 1; else if (!klcd_c[i].fx && free_ < 0) free_ = i; }
            if (!have && free_ >= 0) { memset(&klcd_c[free_], 0, sizeof klcd_c[free_]); klcd_c[free_].fx = fx[k]; klcd_c[free_].hp = -1; }
        }
    }
    for (i = 0; i < KLCD_MAXCAR; i++) {
        struct klcd_car *c = &klcd_c[i]; float hp; int ok = 1; DWORD cnt, dead = 0;
        if (!c->fx) continue;
        if (!klcd_fx_ok(c->fx)) { memset(c, 0, sizeof *c); continue; }       /* gone */
        hp = klbd_rdf(c->fx + 0x5ec, &ok); cnt = klh_rd32(c->fx + 0x7d4);
        if (!ok) continue;
        if (c->hp < 0) { c->hp = hp; c->cnt = cnt; }
        if (!c->tuned) klcd_tune(c, i);
        if (hp > 0) { float p[3]; if (klcd_place(c->fx, p, &c->how)) { memcpy(c->pos, p, 12); c->havepos = 1; } }
        if (c->hp > 0 && hp <= 0) dead = 1;
        if (cnt != c->cnt && cnt > c->cnt && cnt < 1000) {              /* REVIEW 1024: +0x7d4 is a GUESS; a count that is not a blow count would floor men beside a harmless car, so it only triggers with CountTrigger=1 */
            if (klcd.log) klog("cardown: car %d: [+0x7d4] %lu -> %lu (hp %.0f)%s", i, (unsigned long)c->cnt, (unsigned long)cnt, hp, klcd.counttrig ? "" : " - not a trigger (CountTrigger=0)");
            if (klcd.counttrig) dead = 1;
        }
        c->hp = hp; c->cnt = cnt;
        if (dead) klcd_blow(c, i, tick);
    }
    klcd_event(tick);
}

/* ---------------------------------------------------------------- init */

static float klcd_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("CarDown", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

static void klcd_init(void)
{
    memset(&klcd, 0, sizeof klcd); memset(klcd_c, 0, sizeof klcd_c); memset(&klcd_e, 0, sizeof klcd_e); memset(&klcd_g, 0, sizeof klcd_g);
    klcd.on = GetPrivateProfileIntA("CarDown", "Enable", 1, klh_ini) != 0;
    if (!klcd.on) return;
    klcd.dry = GetPrivateProfileIntA("CarDown", "Dry", 0, klh_ini) != 0;
    klcd.log = GetPrivateProfileIntA("CarDown", "Log", 1, klh_ini);
    klcd.human = GetPrivateProfileIntA("CarDown", "Human", 1, klh_ini) != 0;
    klcd.counttrig = GetPrivateProfileIntA("CarDown", "CountTrigger", 0, klh_ini) != 0;
    klcd.bots = GetPrivateProfileIntA("CarDown", "Bots", 1, klh_ini) != 0;
    klcd.cops = GetPrivateProfileIntA("CarDown", "Cops", 1, klh_ini) != 0;
    klcd.damage = klcd_inif("Damage", "60", 0.0f, 100000.0f);
    klcd.inner = klcd_inif("Inner", "0", -1.0f, 100000.0f);
    klcd.secs = klcd_inif("Seconds", "2.5", 0.3f, 10.0f);
    klcd.radius = klcd_inif("Radius", "1.0", 0.2f, 5.0f);
    klog("cardown: on%s (Arcade, a level that is not the stock one): a car blast floors everyone in its radius into the game's revivable down instead of killing - Damage cap %.0f, inner radius %.0f, %.1f s of asking, Human %d Bots %d Cops %d",
         klcd.dry ? " (Dry=1: nothing is called, nothing is written)" : "", klcd.damage, klcd.inner, klcd.secs, klcd.human, klcd.bots, klcd.cops);
}
