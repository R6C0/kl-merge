/*
 * kladren.c - ADRENALINE (track Y2, 2026-10-11 night). Part of KLHook (included by klhook.c AFTER kldown.c; its tick
 * runs BEFORE kld_tick). OFF unless [Adrenaline] Enable=1. NOT RUN IN THE GAME. Reading: re\adrenaline.md.
 *
 * The owner: 'an adrenaline feature so it speeds up the down player state and the ai heisters and you get a share of
 * their cut since you helped them' / 'if you get someone down like that you would be a traitor too but if you revive
 * them youd become normal again'.
 *
 * WHAT IT DOES (Arcade, a level that is not stock, session state 0x19, data writes only - no call, no patch):
 *   b. A DOWNED crew member is one of
 *        - an AI heister the GAME has put down (byte [actor+0x64c] set: the NPC's 'down not dead', which only happens
 *          with [Down] Bots=1 - re\player_down.md 11), or
 *        - the local human in the game's own knock-down ([D+4] 1 lying / 3 getting up, D = [player+0x2948]).
 *      A HELPER is another crew record in play, no traitor, not down itself, within Range (a human helper, optionally
 *      only while he holds Use: NeedUse) or BotRange (an AI heister standing by a downed human - the escort holds
 *      about 3 m from him) of the downed man.
 *        a downed AI heister: his lie tick [[soldier+0x4b8]+0x14] is pulled earlier, Rate times as fast as time runs
 *        the downed human:    kld_s.meter (kldown.c's mash meter) is held at Meter or more, so the get-up speed
 *                             FlopBase + FlopPerPress x meter (at most FlopTop) is what a hard mash would give; with
 *                             HumanFast=1 also the game's own 'fast get-up' byte [D+0x29] (speed 2.5 in 0x478270).
 *   c. THE SHARE. When the helped man is UP and the helper had helped for MinHelp seconds: x = Share x what the helped
 *      man carries. The helper gets x - the local human into his banked total [score+0x38] (as klfedkit.c's Pay does:
 *      it survives the round), anybody else into his carried money [score+0x150+4i]; Take=1 takes x out of an AI
 *      heister's carried money (a human is never debited). WHY AT THE GET-UP AND NOT AT THE PAYOUT: 0x796410 pools what
 *      the escaped non-traitors carry and gives each THE SAME share, so a transfer between two escapees is invisible
 *      in the payout, and the payout's own fields were not read far enough to add to (re\adrenaline.md 4).
 *   d. THE TRAITOR MARK BY DOWNING. A human whose bullets put a crewmate down (rules slot 131 adds to his word
 *      [score+0x1b8+2*record] when he takes an NPC's last health - re\player_down.md 11.1 - in the pass the game's down
 *      byte appears) is marked as the game marks a killer (rules slot 129 = 0x8fb0d0, read whole in re\fed_kit.md 10.2):
 *      client flag 1 at [score+0x1d4+4*record] (what slot 115 = 0x7ca230 ORs in), the local player's byte
 *      [player+0x2726] = 1 (0x70f770 writes it and then tells the sense manager - NOT done here, ASSUMED harmless but it
 *      may mean the bots do not turn on him: live check A4), and with MarkFine=1 the game's -25,000 ([score+0x24] +=
 *      [tuning+0xc10]). When the crewmate he put down gets up and HE helped (MinHelp), the mark goes again (and the fine
 *      is given back) - but ONLY a mark this part gave: a flag that was set before is never touched, and as soon as any
 *      crewmate DIES while the mark stands, the mark is the game's to keep (a real kill makes it his in the game's own
 *      books; slot 129 skips a client that already has flag 1, so it would never be marked again).
 *   e. Per crew RECORD, nothing assumes record 0 except the two places that must (banked total, [player+0x2726]: only
 *      the local player's), so an online human can be added later. Off for a police human, off on a stock level.
 *
 * NOT DONE (re\adrenaline.md 2): (a) AI heisters going down at the killing hit IN PLACE OF DYING with no [Down] Bots - the
 * game's refusal (b / d / e of 0x70e0e0) is not established and the one way to be sure (a wrapped damage routine,
 * slot 96 = 0x8473a0) needs a private ZSoldier vtable that six other parts of this hook reject by its address.
 *
 * Keys ([Adrenaline]):
 *   Enable=0   Dry=0 (1 = log only; nothing is written)   Log=1 (2 = every pass with a helper, once a second)
 *   Range=2.5 (m, a human helper)   BotRange=4.0 (m, an AI helper of a downed human)   NeedUse=0 (1 = a human helper must
 *   hold Use: bit 2 of [player+0xa54], a GUESS of re\hud_popup.md 7.12 - log it with Log=2 before turning this on)
 *   Rate=3.0 (a downed AI heister's lie runs this many times faster)   Meter=3.0 (the human's mash meter floor)
 *   HumanFast=0 (ON BREAKS THE OWNER'S RULE 'NEVER FASTER THAN NORMAL')   MinHelp=1.0 (s; review 7: a walk past is not help)   Share=0.25   Take=1   ShareBot=1 (AI helpers earn a share too)   ShareBank=1
 *   Mark=0 (1 = the traitor mark for downing a crewmate: the attribution is ASSUMED, check A4; the bots may not turn on a marked human)   MarkFine=0
 */
#define KLADREN_C

#define KAD_PLAYER_VT  0x00bb45f4             /* ZFFPlayer */
#define KAD_GAMEDATA   0x00dd265c
#define KAD_CLOCK      0x00dd2640             /* +0x48 the game's tick (1/1024 s) */
#define KAD_TUNING     0x0168d7c0
#define KAD_SOLDIER_VT 0x00bd0954
#define KAD_ROUND      0x19
#define KAD_M          100.0f                 /* world units a metre */

static struct {
    int on, dry, log, needuse, humanfast, share_bot, bank, mark, fine, take, bothelp, rush;
    float range, brange, rate, meter, minhelp, share, rushrange;
} kad;

static struct kad_rec {
    DWORD actor;                              /* whose record this is (a new actor in the record = a new man) */
    BYTE down;                                /* he is down now */
    DWORD t_down, tick_down, tick_last;       /* GetTickCount / the game's tick at the down; the game's tick last pass */
    int by;                                   /* the human record whose bullets put him down, -1 = not known */
    DWORD hm[KLB_NREC];                       /* ms each other record helped him this down */
    DWORD fast;                               /* the human: [D+0x29] was written by us */
    float lie0;                               /* the AI heister: seconds of lying left when he went down (log) */
    DWORD sped;                               /* ms of speed-up given (log) */
    int mkn;                                  /* the mark was put on because of him (counted in kad_m[by]) */
    int paid;                                 /* a share was paid for this man this round (review 5: once per man per round; reset with the actor / the round) */
    int rusher;                               /* Rush: record + 1 of the AI heister sent to him (0 = none) */
    DWORD rush_at, rush_soldier;              /* when the last order went; that bot's soldier (the order is checked against it) */
    float rush_back[3]; int rush_have_back;   /* where that bot's defend block was before: he is sent back there when the man is up */
} kad_r[KLB_NREC];

static struct kad_mark {
    int on;                                   /* this part's mark stands on this human record */
    int n;                                    /* crewmates he put down and has not revived */
    int keep;                                 /* the mark is the game's now (a crewmate died, or the flag was not ours) */
    int fined; int fine;                      /* the fine put on, to give back */
    BYTE byte2726;                            /* the local player's byte before */
} kad_m[KLB_NREC];

static struct { DWORD rules, state; WORD kw[KLB_NREC]; BYTE kwok[KLB_NREC]; DWORD nextlog; BYTE use_last; DWORD use_dw; } kad_g;

/* ---------------------------------------------------------------- pure arithmetic (tested off the game)  */

/* the nearest helper: -> index in dist[] of the smallest dist <= lim[i], or -1. dist < 0 = not a candidate */
static int kad_pick(const float *dist, const float *lim, int n)
{
    int i, best = -1;
    for (i = 0; i < n; i++) {
        if (dist[i] < 0 || dist[i] > lim[i]) continue;
        if (best < 0 || dist[i] < dist[best]) best = i;
    }
    return best;
}

/* a downed AI heister's lie tick pulled earlier. cur = the tick he lies until, tick = now, dt = ticks since the last
   pass. -> the new tick (never earlier than tick + 2, never later than cur); *done = ticks taken off */
static DWORD kad_lie_step(DWORD cur, DWORD tick, DWORD dt, float rate, DWORD *done)
{
    long left = (long)(cur - tick), take, nl;
    *done = 0;
    if (left <= 2 || rate <= 1.0f || dt == 0 || dt > 512) return cur;      /* a pass longer than half a second is a stall: no catch-up */
    take = (long)((rate - 1.0f) * (float)dt);
    nl = left - take; if (nl < 2) nl = 2;
    *done = (DWORD)(left - nl);
    return tick + (DWORD)nl;
}

/* the share: Share x carried, rounded down, never negative, capped at carried */
static int kad_share(int carried, float share)
{
    double x;
    if (carried <= 0 || share <= 0) return 0;
    x = (double)carried * (double)share;
    if (x > (double)carried) x = (double)carried;
    return (int)x;
}

/* ---------------------------------------------------------------- reading a man's place */

static int kad_place(const struct klb_snap *s, int i, float pos[3])
{
    if (i == s->human) { DWORD pl; float feet[3]; return kle_human(&pl, feet, pos); }
    return kle_node(klh_rd32(s->r[i].actor + 4), pos, 0);
}

static float kad_dist(const float a[3], const float b[3])
{
    float dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    return (float)sqrt(dx * dx + dy * dy + dz * dz);
}

/* ---------------------------------------------------------------- the money */

static int kad_carried(const struct klb_snap *s, int i, int *v)
{
    return klh_rd(s->score + 0x150 + 4 * i, v, 4) && *v >= 0 && *v < 100000000;
}

static int kad_put32(DWORD at, int v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 4, what); }

/* pay helper h for having helped record i up */
static void kad_pay(const struct klb_snap *s, int i, int h, DWORD ms)
{
    int have = 0, x, hv = 0, tot = 0, ok = kad_carried(s, i, &have);
    char who[24];
    snprintf(who, sizeof who, "%s", h == s->human ? "you" : (s->r[h].flags & 2) ? "TRAITOR" : "bot");
    if (!ok) { klog("adren: record %d helped record %d up (%lu ms), but his carried money cannot be read: no share", h, i, (unsigned long)ms); return; }
    x = kad_share(have, kad.share);
    if (x <= 0) { klog("adren: record %d (%s) helped record %d up (%lu ms): he carries $%d, so Share %.2f is $0", h, who, i, (unsigned long)ms, have, kad.share); return; }
    if (h != s->human && !kad.share_bot) { klog("adren: record %d (%s) helped record %d up: ShareBot=0, no share ($%d would be)", h, who, i, x); return; }
    if (kad.dry) { klog("adren: Dry - record %d (%s) WOULD get $%d (Share %.2f of the $%d record %d carries)%s", h, who, x, kad.share, have, i,
                        kad.take ? "; and record i would lose it" : ""); return; }
    if (h == s->human && kad.bank) {
        if (!klh_rd(s->score + 0x38, &tot, 4) || !kad_put32(s->score + 0x38, tot + x, "score: the banked total (the adrenaline share)")) return;
        klog("adren: SHARE - record %d (you) gets $%d (Share %.2f of the $%d record %d carries; helped %lu ms), banked: [score+0x38] %d -> %d", h, x, kad.share, have, i, (unsigned long)ms, tot, tot + x);
    } else {
        if (!kad_carried(s, h, &hv) || !kad_put32(s->score + 0x150 + 4 * h, hv + x, "score: the helper's carried money (the adrenaline share)")) return;
        klog("adren: SHARE - record %d (%s) gets $%d (Share %.2f of the $%d record %d carries; helped %lu ms), carried: $%d -> $%d", h, who, x, kad.share, have, i, (unsigned long)ms, hv, hv + x);
    }
    /* review 5: the share must not make money - with Take=1 it comes out of the helped man's carried money, a human's too */
    if (kad.take && kad_put32(s->score + 0x150 + 4 * i, have - x, "score: the helped man's carried money (the adrenaline share is his cut)"))
        klog("adren: record %d (%s) carries $%d now (was $%d: the share is out of his cut)", i, i == s->human ? "you" : "bot", have - x, have);
    else if (!kad.take) klog("adren: Take=0 - the share of $%d is NEW money (nobody is debited)", x);
}

/* ---------------------------------------------------------------- the traitor mark */

static DWORD kad_flagat(const struct klb_snap *s, int h) { return s->score + 0x1d4 + 4 * h; }

static void kad_mark_on(const struct klb_snap *s, int h, int bot)
{
    DWORD fl = 0, pl = 0; BYTE b = 0; float feet[3], np[3];
    if (!kad.mark || h < 0 || h >= s->n) return;
    if (!klh_rd(kad_flagat(s, h), &fl, 4)) return;
    if (kad_m[h].on) { kad_m[h].n++; klog("adren: MARK - record %d put record %d down too: %d crewmate(s) down by his bullets", h, bot, kad_m[h].n); return; }
    if (fl & 0xd) { klog("adren: record %d put record %d down, but his client flags are %08lx already (traitor / dead / police): no mark of ours, nothing to take off later", h, bot, (unsigned long)fl); return; }
    if (kad.dry) { klog("adren: Dry - record %d WOULD be marked a traitor for putting record %d down (client flags %08lx -> %08lx)", h, bot, (unsigned long)fl, (unsigned long)(fl | 1)); return; }
    fl |= 1;
    if (!klh_data((void *)(DWORD_PTR)kad_flagat(s, h), &fl, 4, "client flags: the traitor flag (adrenaline: he put a crewmate down)")) return;
    kad_m[h].on = 1; kad_m[h].n = 1; kad_m[h].keep = 0; kad_m[h].fined = 0;
    if (h == s->human && kle_human(&pl, feet, np) && klh_rd(pl + 0x2726, &b, 1)) {
        BYTE one = 1; kad_m[h].byte2726 = b;
        if (b != 1) klh_data((void *)(DWORD_PTR)(pl + 0x2726), &one, 1, "player: the traitor byte (adrenaline)");
    }
    if (kad.fine && h == s->human) {
        DWORD tun = klh_rd32((DWORD_PTR)KLH_VA(KAD_TUNING)); int f = tun ? (int)klh_rd32(tun + 0xc10) : 0, cur = 0;
        if (f < 0 && f > -10000000 && klh_rd(s->score + 0x24, &cur, 4) && kad_put32(s->score + 0x24, cur + f, "score: the traitor fine (adrenaline)")) { kad_m[h].fined = 1; kad_m[h].fine = f; }
    }
    klog("adren: MARK - record %d is a TRAITOR (client flags %08lx -> %08lx) because his bullets put record %d down%s; he is normal again when record %d gets up and he helped", h, (unsigned long)(fl & ~1u), (unsigned long)fl, bot,
         kad_m[h].fined ? "; the game's fine is on his round line" : "", bot);
}

static void kad_mark_off(const struct klb_snap *s, int h, int bot, const char *why)
{
    DWORD fl = 0, pl = 0; float feet[3], np[3];
    if (h < 0 || h >= KLB_NREC || !kad_m[h].on) return;
    if (kad_m[h].n > 0) kad_m[h].n--;
    if (kad_m[h].n > 0) { klog("adren: record %d is still marked: %d crewmate(s) he put down are not up yet (%s)", h, kad_m[h].n, why); return; }
    if (kad_m[h].keep) { klog("adren: record %d keeps the mark: it is the game's now (%s)", h, why); kad_m[h].on = 0; return; }
    if (kad.dry || !klh_rd(kad_flagat(s, h), &fl, 4)) { kad_m[h].on = 0; return; }
    if (fl & 1) {
        fl &= ~1u; klh_data((void *)(DWORD_PTR)kad_flagat(s, h), &fl, 4, "client flags: the traitor flag off (adrenaline: he revived the crewmate)");
    }
    if (h == s->human && kle_human(&pl, feet, np)) { BYTE z = kad_m[h].byte2726; klh_data((void *)(DWORD_PTR)(pl + 0x2726), &z, 1, "player: the traitor byte back (adrenaline)"); }
    if (kad_m[h].fined) { int cur = 0; if (klh_rd(s->score + 0x24, &cur, 4)) kad_put32(s->score + 0x24, cur - kad_m[h].fine, "score: the traitor fine given back (adrenaline)"); }
    klog("adren: UNMARK - record %d is a normal heister again (client flags %08lx)%s - record %d is up (%s)", h, (unsigned long)fl, kad_m[h].fined ? "; the fine is given back" : "", bot, why);
    kad_m[h].on = 0; kad_m[h].fined = 0;
}

/* ---------------------------------------------------------------- Rush: an AI heister runs to a downed crewmate */

static int kad_rushing(int h)                 /* is record h already sent to somebody? */
{
    int i;
    for (i = 0; i < KLB_NREC; i++) if (kad_r[i].down && kad_r[i].rusher == h + 1) return 1;
    return 0;
}

/* a place 0.8 m from the downed man, on the bot's side */
static void kad_beside(const float man[3], const float bot[3], float out[3])
{
    float dx = bot[0] - man[0], dz = bot[2] - man[2], l = (float)sqrt(dx * dx + dz * dz);
    memcpy(out, man, 12);
    if (l > 1.0f) { out[0] = man[0] + dx / l * 0.8f * KAD_M; out[2] = man[2] + dz / l * 0.8f * KAD_M; }
}

static void kad_rush(const struct klb_snap *s, int i, float pos[][3], const int *havepos, const BYTE *dn, DWORD now)
{
    struct kad_rec *k = &kad_r[i]; struct kle_e e; float bp[3], want[3], got[3], d; char why[100]; DWORD actor, soldier; int h, best = -1, r; float bd = 0;
    if (!kad.rush || !havepos[i] || now - k->t_down < 600) return;
    if (k->rusher) {                                                       /* already sent: again every 2.5 s while he is not there yet */
        h = k->rusher - 1;
        if (now - k->rush_at < 2500 || !havepos[h] || dn[h]) return;
        if (!kle_bot(s, h, &actor, &soldier, bp, why) || soldier != k->rush_soldier) { klog("adren: RUSH - record %d no longer runs to record %d (%s)", h, i, why[0] ? why : "another soldier"); k->rusher = 0; k->rush_have_back = 0; return; }
        if ((d = kad_dist(bp, pos[i])) <= kad.brange * KAD_M * 0.9f) { k->rush_at = now; return; }
        memset(&e, 0, sizeof e); e.rec = h; e.actor = actor; e.soldier = soldier;
        kad_beside(pos[i], bp, want);
        r = kle_order2(&e, want, got, why, kad.dry); k->rush_at = now;
        if (kad.log >= 2) klog("adren: RUSH - record %d is %.1f m from record %d: ordered again (%s)", h, d / KAD_M, i, r == 1 ? "called" : r == 2 ? "dry" : why);
        return;
    }
    for (h = 0; h < s->n; h++) {
        const struct klb_rec *q = &s->r[h];
        if (h == i || !q->used || !(q->flags & 1) || (q->flags & 2) || q->status != 0 || dn[h] || !havepos[h]) continue;
        if (kle_r.used[h] && i != s->human) continue;                      /* an escort stays with the human unless the human is the one down */
        if (kad_rushing(h)) continue;
        if (fabs(pos[h][1] - pos[i][1]) > 3.0f * KAD_M) continue;          /* another floor: the path may be long */
        d = kad_dist(pos[h], pos[i]);
        if (d > kad.rushrange * KAD_M) continue;
        if (best < 0 || d < bd) { best = h; bd = d; }
    }
    if (best < 0) return;
    if (bd <= kad.brange * KAD_M * 0.9f) return;                          /* somebody is by him already */
    if (!kle_bot(s, best, &actor, &soldier, bp, why)) { if (kad.log >= 2) klog("adren: RUSH - record %d cannot be sent to record %d: %s", best, i, why); return; }
    memset(&e, 0, sizeof e); e.rec = best; e.actor = actor; e.soldier = soldier;
    k->rush_have_back = kle_block(soldier, k->rush_back) && (k->rush_back[0] || k->rush_back[1] || k->rush_back[2]);
    kad_beside(pos[i], bp, want);
    r = kle_order2(&e, want, got, why, kad.dry);
    if (!r) { klog("adren: RUSH - record %d not sent to record %d: %s", best, i, why); k->rush_have_back = 0; return; }
    k->rusher = best + 1; k->rush_at = now; k->rush_soldier = soldier;
    klog("adren: RUSH - record %d (%s) runs to record %d (%s), %.1f m away, to (%.0f, %.0f, %.0f)%s", best, kle_r.used[best] ? "your escort" : "bot", i, i == s->human ? "you" : "bot", bd / KAD_M,
         want[0], want[1], want[2], r == 2 ? " - DRY: not called" : "");
}

/* the man is up (or gone): the bot that ran to him goes back to where his own orders had him */
static void kad_rush_end(const struct klb_snap *s, int i, const char *why_)
{
    struct kad_rec *k = &kad_r[i]; struct kle_e e; float bp[3], got[3]; char why[100]; DWORD actor, soldier; int h = k->rusher - 1, r;
    if (!k->rusher) return;
    k->rusher = 0;
    if (!k->rush_have_back) { klog("adren: RUSH - record %d is done with record %d (%s); his own orders take him on", h, i, why_); return; }
    k->rush_have_back = 0;
    if (kle_r.used[h]) { klog("adren: RUSH - record %d (your escort) is done with record %d (%s): the escort takes him back", h, i, why_); return; }
    if (!kle_bot(s, h, &actor, &soldier, bp, why) || soldier != k->rush_soldier) { klog("adren: RUSH - record %d is done with record %d (%s); not sent back (%s)", h, i, why_, why); return; }
    memset(&e, 0, sizeof e); e.rec = h; e.actor = actor; e.soldier = soldier;
    r = kle_order2(&e, k->rush_back, got, why, kad.dry);
    klog("adren: RUSH - record %d is done with record %d (%s): sent back to (%.0f, %.0f, %.0f) (%s)", h, i, why_, k->rush_back[0], k->rush_back[1], k->rush_back[2], r == 1 ? "called" : r == 2 ? "dry" : why);
}

/* ---------------------------------------------------------------- one pass */

static void kad_forget(const char *why)
{
    int i; (void)why;
    for (i = 0; i < KLB_NREC; i++) if (kad_r[i].fast) kad_r[i].fast = 0;      /* [D+0x29] is the game's own to reset with D */
    memset(kad_r, 0, sizeof kad_r);
    memset(kad_m, 0, sizeof kad_m);
    memset(&kad_g, 0, sizeof kad_g);
    for (i = 0; i < KLB_NREC; i++) kad_g.kw[i] = 0xffff;      /* no 'before' yet: the first pass of a round is no rise */
}

static void kad_tick(int game_thread)
{
    struct klb_snap sn; DWORD rules, state, now, tick = 0, clock, gd, pl = 0, D = 0, ds = 0; int level, act, i, j, hs = -1; char why[200];
    BYTE police = 0, idx = 0xff;
    float pos[KLB_NREC][3]; int havepos[KLB_NREC]; BYTE dn[KLB_NREC]; DWORD dnd[KLB_NREC];
    if (!kad.on || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    act = klr_arcade(&rules, &state, &level) && klb_level(why) && state == KAD_ROUND && klb_read(&sn) && sn.state == KAD_ROUND;
    if (!act) { if (kad_g.rules) kad_forget("round over"); return; }
    if (sn.rules != kad_g.rules) {            /* a new round / rules object: a mark left over from the last round is taken off, nothing else is carried */
        for (i = 0; i < KLB_NREC; i++) if (kad_m[i].on && !kad_m[i].keep && !kad.dry) { DWORD fl = 0; if (klh_rd(sn.score + 0x1d4 + 4 * i, &fl, 4) && (fl & 1)) { fl &= ~1u; klh_data((void *)(DWORD_PTR)(sn.score + 0x1d4 + 4 * i), &fl, 4, "client flags: a mark of last round (adrenaline)"); } }
        kad_forget("new rules object"); kad_g.rules = sn.rules;
        klog("adren: a round runs (Arcade, not the stock level: %s); %d crew record(s); Range %.1f m, BotRange %.1f m, Rate %.1f, Meter %.1f, Share %.2f, Mark %d%s", why, sn.n, kad.range, kad.brange, kad.rate, kad.meter, kad.share, kad.mark, kad.dry ? " - Dry: nothing is written" : "");
    }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KAD_GAMEDATA))) || !(clock = klh_rd32((DWORD_PTR)KLH_VA(KLD_CLOCK))) || !klh_rd(clock + 0x48, &tick, 4)) return;
    /* the local human's knock-down state (D), if he is a criminal in play */
    if (klh_rd(gd + 0x898, &idx, 1) && idx < 4 && (pl = klh_rd32(gd + 0x828 + 4 * idx)) != 0 && klh_rd32(pl) == KAD_PLAYER_VT && klh_rd(pl + 0x2723, &police, 1) && !police &&
        (D = klh_rd32(pl + 0x2948)) != 0 && klh_rd32(D) == pl && klh_rd(D + 4, &ds, 4)) hs = sn.human; else { pl = 0; D = 0; ds = 0; }
    /* each record: down? place? */
    for (i = 0; i < sn.n; i++) {
        const struct klb_rec *r = &sn.r[i]; struct kad_rec *k = &kad_r[i]; BYTE d = 0; DWORD s = 0, dn_ = 0;
        dn[i] = 0; dnd[i] = 0; havepos[i] = 0;
        if (!r->used) { if (k->actor) memset(k, 0, sizeof *k); continue; }
        if (k->actor != r->actor) { memset(k, 0, sizeof *k); k->actor = r->actor; k->by = -1; }
        if (r->status != 0) continue;           /* aboard / escaped / dead: out of play */
        if (i == sn.human) { if (i == hs && (ds == 1 || ds == 3)) d = 1; }
        else if ((r->flags & 1) && r->actor && klh_rd32(r->actor) == KLB_ACTOR_VT && (s = klh_rd32(r->actor + 0x77c)) != 0 && klh_rd32(s) == KAD_SOLDIER_VT && klh_rd32(s + 0x40) == r->actor) {
            klh_rd(r->actor + 0x64c, &d, 1);
            if (d) { dn_ = klh_rd32(s + 0x4b8); if (dn_ && klh_rd32(dn_ + 4) != s) dn_ = 0; dnd[i] = dn_; }
        }
        dn[i] = d ? 1 : 0;
        havepos[i] = kad_place(&sn, i, pos[i]);
    }
    /* the humans' bullets: whose word [score+0x1b8+2i] rose since the last pass */
    for (i = 0; i < sn.n; i++) {
        WORD w = 0; kad_g.kwok[i] = 0;
        if (sn.r[i].used && !(sn.r[i].flags & 1) && klh_rd(sn.score + 0x1b8 + 2 * i, &w, 2)) { kad_g.kwok[i] = 1; }
        (void)w;
    }
    for (i = 0; i < sn.n; i++) {
        const struct klb_rec *r = &sn.r[i]; struct kad_rec *k = &kad_r[i]; DWORD dt;
        if (!r->used) continue;
        if (r->status != 0 && k->down) {        /* he left play while down (died, was left behind) */
            kad_rush_end(&sn, i, "he left play");
            k->down = 0;
            if (k->mkn) { kad_m[k->by].keep = 1; }
            klog("adren: record %d left play while down (%s)", i, r->status == 7 ? "he DIED" : "status other than in-play"); continue;
        }
        if (r->status != 0) continue;
        dt = k->tick_last ? tick - k->tick_last : 0; k->tick_last = tick;
        if (dt > 512) dt = 0;                  /* a stall or a load: no catch-up, no credit */
        if (dn[i] && !k->down) {
            /* ---- he goes down */
            int by = -1, h;
            k->down = 1; k->t_down = now; k->tick_down = tick; k->by = -1; memset(k->hm, 0, sizeof k->hm); k->sped = 0; k->mkn = 0;
            if (i != sn.human) for (h = 0; h < sn.n; h++) {       /* a human whose word rose in this pass put him down (ASSUMED reading of re\player_down.md 11.1) */
                WORD w = 0;
                if (!sn.r[h].used || (sn.r[h].flags & 1) || !kad_g.kwok[h] || !klh_rd(sn.score + 0x1b8 + 2 * h, &w, 2)) continue;
                if (w != kad_g.kw[h] && kad_g.kw[h] != 0xffff && (WORD)(w - kad_g.kw[h]) < 1000) { by = h; break; }
            }
            if (by < 0 && klbd_by(i) >= 0) by = klbd_by(i);          /* klbotdown.c: the threshold down never raises the score word */
            k->by = by;
            if (i == sn.human) {
                klog("adren: YOU ARE DOWN (state %lu) at (%.0f, %.0f, %.0f)%s", ds, havepos[i] ? pos[i][0] : 0, havepos[i] ? pos[i][1] : 0, havepos[i] ? pos[i][2] : 0, kld.on ? "" : " ([Down] is off: the meter cannot be driven)");
            } else {
                long lt = dnd[i] ? (long)(klh_rd32(dnd[i] + 0x14) - tick) : 0; k->lie0 = lt / 1024.0f;
                klog("adren: record %d (%s) IS DOWN at (%.0f, %.0f, %.0f); he lies %.2f s; put down by %s", i, sn.r[i].flags & 2 ? "TRAITOR" : "bot", havepos[i] ? pos[i][0] : 0, havepos[i] ? pos[i][1] : 0, havepos[i] ? pos[i][2] : 0, k->lie0,
                     by >= 0 ? "a human's bullet (his word rose)" : "nobody known (police, or the word did not rise)");
                if (by >= 0 && !(sn.r[i].flags & 2)) { kad_mark_on(&sn, by, i); if (kad_m[by].on) k->mkn = 1; }
            }
        } else if (!dn[i] && k->down) {
            /* ---- he is up */
            int best = -1, h; DWORD bm = 0;
            kad_rush_end(&sn, i, "he is up");
            k->down = 0;
            for (h = 0; h < sn.n; h++) if (k->hm[h] > bm) { bm = k->hm[h]; best = h; }
            klog("adren: record %d IS UP after %.2f s on the floor (he lay %.2f s at go-down; unhelped the game gives 1.5 .. 3.0); helped %lu ms by %s", i, (now - k->t_down) / 1000.0f, k->lie0, (unsigned long)bm, best >= 0 ? (best == sn.human ? "you" : "a bot") : "nobody");
            if (i != sn.human) { DWORD ho = klh_rd32(sn.r[i].actor + 0x5fc), v4 = 0, v8 = 0; float f4, f8; if (ho) { v4 = klh_rd32(ho + 4); v8 = klh_rd32(ho + 8); memcpy(&f4, &v4, 4); memcpy(&f8, &v8, 4); klog("adren: record %d health object %08lx at the get-up: [+4] %.1f [+8] %.1f (RAW, layout not read: A0/A1 expect about 75 %% of the maximum if the game ended the lie itself, 0 or less if our pull ended it too soon)", i, (unsigned long)ho, f4, f8); } }
            if (k->fast && pl) { BYTE z = 0; klh_data((void *)(DWORD_PTR)(D + 0x29), &z, 1, "player: the fast get-up byte back (adrenaline)"); }
            k->fast = 0;
            if (best >= 0 && bm >= (DWORD)(kad.minhelp * 1000.0f)) {
                if (kad.share > 0) { if (k->paid) klog("adren: record %d was helped up before this round: no second share (once per man per round)", i); else { k->paid = 1; kad_pay(&sn, i, best, bm); } }
                if (k->by >= 0 && k->by == best) kad_mark_off(&sn, k->by, i, "he helped him up");
                else if (k->by >= 0 && k->mkn) klog("adren: record %d (who put record %d down) did not help him up: his mark stays", k->by, i);
            } else if (k->by >= 0 && k->mkn) klog("adren: record %d got up without enough help (%lu ms of %.0f): the mark of record %d stays", i, (unsigned long)bm, kad.minhelp * 1000.0f, k->by);
            k->by = -1; k->mkn = 0;
            continue;
        }
        if (!dn[i] || !k->down) continue;
        /* ---- he lies: who is by him? */
        {
            float dist[KLB_NREC], lim[KLB_NREC]; int h, hp; BYTE use = 0; DWORD usedw = 0;
            for (h = 0; h < sn.n; h++) {
                const struct klb_rec *q = &sn.r[h];
                dist[h] = -1; lim[h] = 0;
                if (h == i || !q->used || q->status != 0 || dn[h] || (q->flags & 2) || !havepos[h] || !havepos[i]) continue;
                if (!(q->flags & 1) && h != sn.human) continue;             /* a human that is not the local one: his place is not read here (online later) */
                if (h == sn.human && police) continue;
                if (!(q->flags & 1)) {                                       /* a human helper: Range, and Use if asked */
                    if (kad.needuse && !(h == sn.human && pl && klh_rd(pl + 0xa54, &usedw, 4) && (usedw & 2))) continue;
                    lim[h] = kad.range * KAD_M;
                } else if (i == sn.human) lim[h] = kad.brange * KAD_M;       /* an AI heister by a downed human */
                else if (kad.bothelp) lim[h] = kad.brange * KAD_M;          /* BotHelp: an AI heister by a downed AI heister */
                else continue;
                if (fabs(pos[h][1] - pos[i][1]) > 2.0f * KAD_M) continue;    /* another floor */
                dist[h] = kad_dist(pos[h], pos[i]);
            }
            hp = kad_pick(dist, lim, sn.n);
            kad_rush(&sn, i, pos, havepos, dn, now);
            if (pl && klh_rd(pl + 0xa54, &usedw, 4)) { use = (BYTE)((usedw & 2) != 0); if (kad.log >= 2 && (usedw != kad_g.use_dw)) { klog("adren: [player+0xa54] %08lx -> %08lx (bit 2, the GUESSED 'use key held': %d)", (unsigned long)kad_g.use_dw, (unsigned long)usedw, use); kad_g.use_dw = usedw; } }
            if (hp < 0) { if (k->fast && pl && i == sn.human) { BYTE z = 0; klh_data((void *)(DWORD_PTR)(D + 0x29), &z, 1, "player: the fast get-up byte back (adrenaline)"); k->fast = 0; } continue; }
            k->hm[hp] += dt * 1000u / 1024u;
            if (kad.log >= 2 && now >= kad_g.nextlog) { kad_g.nextlog = now + 1000; klog("adren: record %d is helped by record %d (%s), %.1f m away, %lu ms so far", i, hp, hp == sn.human ? "you" : "a bot", dist[hp] / KAD_M, (unsigned long)k->hm[hp]); }
            if (kad.dry) continue;
            if (i == sn.human) {
                /* the mash meter: the same condition as kldown.c's press count (a get-up it drives, or a landed Flop fall) */
                if (kld.on && (kld_s.up || (KLD_ONE && kld_s.fnow && kld_s.t_land && !kld_s.fdone))) {
                    if (kld_s.meter < kad.meter) kld_s.meter = kad.meter;
                }
                if (kad.humanfast && ds == 1 && !k->fast) {
                    BYTE one = 1, cur = 0;
                    if (klh_rd(D + 0x29, &cur, 1) && !cur && klh_data((void *)(DWORD_PTR)(D + 0x29), &one, 1, "player: the fast get-up byte (adrenaline)")) { k->fast = 1; klog("adren: HumanFast - [D+0x29] = 1: the game's own fast get-up (speed 2.5) is asked while record %d stands by him", hp); }
                }
            } else if (dnd[i]) {
                DWORD cur = klh_rd32(dnd[i] + 0x14), done = 0, nw = kad_lie_step(cur, tick, dt, kad.rate, &done);
                if (nw != cur && klh_data((void *)(DWORD_PTR)(dnd[i] + 0x14), &nw, 4, "an AI heister's down-not-dead: the tick he lies until (adrenaline)")) k->sped += done;
            }
            (void)use; (void)j;
        }
    }
    /* a crewmate that DIED (status 7) while a mark of ours stands: the mark is the game's from now on */
    for (i = 0; i < sn.n; i++) if (sn.r[i].used && sn.r[i].status == 7 && !kad_r[i].down)
        for (j = 0; j < KLB_NREC; j++) if (kad_m[j].on && !kad_m[j].keep) { kad_m[j].keep = 1; klog("adren: record %d died while the mark of record %d stands: the mark is the game's to keep now", i, j); }
    /* the words for the next pass */
    for (i = 0; i < sn.n; i++) { WORD w = 0; if (kad_g.kwok[i] && klh_rd(sn.score + 0x1b8 + 2 * i, &w, 2)) kad_g.kw[i] = w; else kad_g.kw[i] = 0xffff; }
    kad_g.state = state;
}

/* ---------------------------------------------------------------- init */

static float kad_inif(const char *key, const char *def, float lo, float hi)
{
    char t[40]; float v;
    GetPrivateProfileStringA("Adrenaline", key, def, t, sizeof t, klh_ini);
    v = (float)atof(t);
    if (!(v == v) || v < lo || v > hi) v = (float)atof(def);
    return v;
}

static void kad_init(void)
{
    memset(&kad, 0, sizeof kad); memset(kad_r, 0, sizeof kad_r); memset(kad_m, 0, sizeof kad_m); memset(&kad_g, 0, sizeof kad_g);
    kad.on = GetPrivateProfileIntA("Adrenaline", "Enable", 0, klh_ini) != 0;
    if (!kad.on) return;
    kad.dry = GetPrivateProfileIntA("Adrenaline", "Dry", 0, klh_ini) != 0;
    kad.log = GetPrivateProfileIntA("Adrenaline", "Log", 1, klh_ini);
    kad.needuse = GetPrivateProfileIntA("Adrenaline", "NeedUse", 0, klh_ini) != 0;
    kad.humanfast = GetPrivateProfileIntA("Adrenaline", "HumanFast", 0, klh_ini) != 0;
    kad.share_bot = GetPrivateProfileIntA("Adrenaline", "ShareBot", 1, klh_ini) != 0;
    kad.bank = GetPrivateProfileIntA("Adrenaline", "ShareBank", 1, klh_ini) != 0;
    kad.mark = GetPrivateProfileIntA("Adrenaline", "Mark", 0, klh_ini) != 0;   /* review 3: OFF until check A4 shows the word rises only for crew victims */
    kad.fine = GetPrivateProfileIntA("Adrenaline", "MarkFine", 0, klh_ini) != 0;
    kad.take = GetPrivateProfileIntA("Adrenaline", "Take", 1, klh_ini) != 0;
    kad.range = kad_inif("Range", "2.5", 0.5f, 10.0f);
    kad.brange = kad_inif("BotRange", "4.0", 0.5f, 15.0f);
    kad.rate = kad_inif("Rate", "3.0", 1.0f, 10.0f);
    kad.meter = kad_inif("Meter", "3.0", 0.0f, 20.0f);
    kad.minhelp = kad_inif("MinHelp", "1.0", 0.0f, 10.0f);
    kad.share = kad_inif("Share", "0.25", 0.0f, 1.0f);
    kad.bothelp = GetPrivateProfileIntA("Adrenaline", "BotHelp", 1, klh_ini) != 0;
    kad.rush = GetPrivateProfileIntA("Adrenaline", "Rush", 1, klh_ini) != 0;
    kad.rushrange = kad_inif("RushRange", "25", 2.0f, 80.0f);
    klog("adren: on%s; a downed crewmate gets up faster with a helper within %.1f m (a bot by a downed human: %.1f m; NeedUse=%d); AI lie x%.1f, your mash meter at least %.1f (HumanFast=%d); the helper gets %.0f %% of what the helped man carries (%s, Take=%d, ShareBot=%d); Mark=%d MarkFine=%d. Arcade on a level that is not stock, not for a police human; data writes only (re\\adrenaline.md)",
         kad.dry ? " (Dry=1: nothing is written)" : "", kad.range, kad.brange, kad.needuse, kad.rate, kad.meter, kad.humanfast, kad.share * 100.0f, kad.bank ? "banked for a human" : "carried", kad.take, kad.share_bot, kad.mark, kad.fine);
    klog("adren: BotHelp=%d (an AI heister by a downed AI heister helps and earns as a human would), Rush=%d (the nearest free AI heister within %.0f m on the same floor RUNS to a downed crewmate, and goes back to his own place when the man is up)", kad.bothelp, kad.rush, kad.rushrange);
    if (!kld.on) klog("adren: [Down] Enable=0 - the human's knock-down is the game's own plain one: the meter cannot be driven (HumanFast=1 can still ask the fast get-up); an AI heister only lies when [Down] Bots=1 (or the game puts him down)");
    else if (!kld_bk.on) klog("adren: [Down] Bots=0 - no AI heister goes down, so only the human side acts (a bot by a downed human); set [Down] Bots=1 (BotsLie=6 gives the adrenaline something to speed)");
}
