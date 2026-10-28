/*
 * kltrait.c - A SMALL TRAIT PER WARDROBE CHARACTER, for the human and for the AI heisters wearing that body
 * (track traits, 2026-10-23; NOT RUN IN THE GAME). Part of KLHook (SHIP and TEST alike), included by klhook.c
 * AFTER klcrew.c and BEFORE klbalance.c. OFF unless [Traits] Enable=1. Table and reading: re\traits.md.
 *
 * WHAT IT IS: only a table and a getter. This file writes NO memory and calls NO game function. It answers
 * 'which character does crew record N wear, and what factors does that character carry', and the modules that
 * already own a proven write site multiply their own number by the factor:
 *
 *   Health      x maximum health          klgrudge.c kly_health (AI heister: CrewHealth's write) and
 *                                         klbalance.c klr_player_tick (the human: Tough / PlayerHealth's write)
 *   DamageIn    x damage taken            there is no per-victim damage write in the hook; for the same hit it is
 *                                         the same as a maximum health of 1 / DamageIn (hit counts are equal; the
 *                                         head factor and regeneration are not touched), so it is folded into
 *                                         Health: effective maximum = Health / DamageIn
 *   DamageOut   x damage dealt            AI heister ONLY: his hit share (the accuracy % klgrudge.c kly_aim writes)
 *                                         is multiplied. NOT APPLIED to the human: no per-shooter damage write
 *                                         site is proven (klbalance.c's matrix is per team pair). The line says so.
 *   AimSpread   x miss share              AI heister ONLY (klgrudge.c kly_aim): accuracy' = 100 - (100 - acc) x s;
 *                                         under 1 = tighter. The human's aim is his own hand.
 *   Regen       x regeneration speed      the HUMAN ONLY (klbalance.c: [H+0x14] delay, [H+0x18] time, both divided
 *                                         by it); an AI heister has no regeneration the hook writes.
 *   ReviveTime  x time to get up          the human: kldown.c's get-up speed divided by it; an AI heister:
 *                                         klbotdown.c's LieSeconds multiplied by it (needs [BotDown] LieSeconds > 0)
 *   Adrenaline  x potency of his shot     when HE is the helper: kladren.c's Rate (1 + (Rate - 1) x f) for a downed
 *                                         AI heister and the Meter floor for a downed human
 *
 * Every factor is held to 1 +- [Traits] MaxDelta (default 0.25), whatever the ini says: a trait is a flavour, not a
 * class. The owner's 'the AI is too OP' is the reason: the shipped table's mean effective health and mean AimSpread
 * are kept at or under 1 for the AI (re\traits.md).
 *
 * GATES (not new, inherited): the AI half rides klgrudge.c ([Bots] Enable=1, Arcade, a level that is NOT the stock
 * one of its slot); the human half rides klbalance.c ([Balance] Enable=1, same gate); the three recovery knobs ride
 * [Down] / [BotDown] / [Adrenaline] Enable. With [Traits] Enable=0 every getter answers 1.0 and nothing changes.
 *
 * WHO WEARS WHOM: klcrew.c's klw_who_now (the model each crew record wears, matched against the level's wardrobe,
 * else the eight stock heisters). Refreshed every 500 ms on the game thread; a record whose body changes is logged
 * again. A body that is not in any list (a policeman, a stranger model) has no trait.
 *
 * KEYS ([Traits]): Enable=0  Dry=0 (1 = the log lines only, every getter answers 1.0)  MaxDelta=0.25 (0 .. 0.5)  Log=1
 * KEYS ([Trait.<Name>], <Name> = the wardrobe name, e.g. [Trait.Kane]; absent key = 1.0):
 *   Health= DamageOut= DamageIn= Regen= ReviveTime= Adrenaline= AimSpread=
 *
 * ONLINE ([Voice] OnlineTraits=1, needs [Voice] Online=1 and [Online] Read=1; default 0, recommended off until benched): kltt_tick also
 * follows the LOCAL online player (klvoice_online.c's kvo_online_who: seat + character from klonline_read.c) so his trait is known and logged
 * for kltalk.c. EVERY factor answers 1.0 online (kltt_g.online): Health/DamageIn and Regen change a health or a timer the net peers also hold,
 * ReviveTime/Adrenaline change get-up and helper numbers that are replicated, DamageOut/AimSpread are AI-only (no AI heister is a wardrobe
 * record online). Nothing is written. GUESS T1: the online seat number can be used as the record index (< KLW_NREC); only the local seat is known.
 * ONLINE BOTS ([BotFill] OnlineBotTraits=1, default 0, HOST only; kltt_bot / kltt_bot_hit below, klbottrait.h): the AI heisters of an online round are not wardrobe records, but the host knows the
 * character it drew for each (klcrewlook.c, OnlineLooks=1), so Health / DamageIn scale the hits on that bot (klbalance.c klr_cb_hit) and ReviveTime scales klbotdown.c's LieSeconds. kltt_get stays 1.0 online.
 *
 * LOG: 'trait: record N = <name> (human|AI heister) Health x1.05 ...' once per record and body.
 */
#ifndef KLTRAIT_C
#define KLTRAIT_C

enum { KLTT_HEALTH, KLTT_DMGOUT, KLTT_DMGIN, KLTT_REGEN, KLTT_REVIVE, KLTT_ADREN, KLTT_AIM, KLTT_N };
static const char *const kltt_key[KLTT_N] = { "Health", "DamageOut", "DamageIn", "Regen", "ReviveTime", "Adrenaline", "AimSpread" };

#define KLTT_NSET 40

static struct { int on, dry, log; float delta; int nset; struct { char name[32]; int has; float v[KLTT_N]; } set[KLTT_NSET]; } ktrait;
static struct {
    DWORD rules, last; int human, n, online;
    struct { int ch; DWORD actor; int told; char name[32]; int set; } r[KLW_NREC];     /* set = index in ktrait.set, -1 = no trait */
} kltt_g;

static float kltt_clamp(float v)
{
    if (!(v == v) || v <= 0) return 1.0f;
    if (v < 1.0f - ktrait.delta) return 1.0f - ktrait.delta;
    if (v > 1.0f + ktrait.delta) return 1.0f + ktrait.delta;
    return v;
}

/* the set of a wardrobe name, read from the ini on first sight; -1 = the ini has no [Trait.<name>] key at all */
static int kltt_set_of(const char *name)
{
    int i, k, any = 0; char sec[64], t[32], *e;
    for (i = 0; i < ktrait.nset; i++) if (!_stricmp(ktrait.set[i].name, name)) return ktrait.set[i].has ? i : -1;
    if (ktrait.nset >= KLTT_NSET) return -1;
    i = ktrait.nset++;
    snprintf(ktrait.set[i].name, sizeof ktrait.set[i].name, "%s", name);
    snprintf(sec, sizeof sec, "Trait.%s", name);
    for (k = 0; k < KLTT_N; k++) {
        double d; ktrait.set[i].v[k] = 1.0f;
        GetPrivateProfileStringA(sec, kltt_key[k], "", t, sizeof t, klh_ini);
        if (!t[0]) continue;
        d = strtod(t, &e);
        while (*e == ' ' || *e == '\t') e++;
        if (e == t || (*e && *e != ';')) { klog("trait: [%s] %s=%s is IGNORED: one number with a decimal point (1 = nothing)", sec, kltt_key[k], t); continue; }
        ktrait.set[i].v[k] = kltt_clamp((float)d); any = 1;
        if (ktrait.set[i].v[k] != (float)d) klog("trait: [%s] %s=%s is held to %.2f ([Traits] MaxDelta=%.2f)", sec, kltt_key[k], t, ktrait.set[i].v[k], ktrait.delta);
    }
    ktrait.set[i].has = any;
    return any ? i : -1;
}

/* the factor of a crew record (rec) for one knob; 1.0 = nothing. rec < 0 = the local human. */
static float kltt_get(int rec, int knob)
{
    int s;
    if (!ktrait.on || ktrait.dry || knob < 0 || knob >= KLTT_N) return 1.0f;
    if (rec < 0) rec = kltt_g.human;
    if (rec < 0 || rec >= KLW_NREC || kltt_g.online) return 1.0f;           /* online: log only, no gameplay factor (see ONLINE above) */
    s = kltt_g.r[rec].set;
    if (!kltt_g.r[rec].ch || s < 0 || s >= ktrait.nset) return 1.0f;
    return ktrait.set[s].v[knob];
}

/* effective maximum health: Health / DamageIn */
static float kltt_hp(int rec) { return kltt_get(rec, KLTT_HEALTH) / kltt_get(rec, KLTT_DMGIN); }

/* ---------------------------------------------------------------- [BotFill] OnlineBotTraits (2026-10-28, wk-trait; NOT RUN IN THE GAME; re\traits.md ONLINE)
   The traits of the AI heisters of an online round, on the HOST only (a bot is the host's actor; his health and timers are written there, the clients follow through the
   game's own replication - the same assumption OnlineBalance / OnlineBotDown make). A bot has no crew record online, so kltt_get() cannot name him; his identity is the
   character the host DREW for him (klcrewlook.c, OnlineLooks=1: klcl_bot_look) once that look is applied. WHAT IS APPLIED:
     Health, DamageIn   a hit on him is multiplied by DamageIn / Health (klbalance.c klr_cb_hit -> klr_tr_orig, on top of OnlineBalance's Tough); the same as kltt_hp's maximum health
     ReviveTime         klbotdown.c LieSeconds x it (needs [Down] OnlineBotDown=1 and [BotDown] LieSeconds > 0)
   NOT APPLIED online (logged as such): DamageOut, AimSpread (no online accuracy write for bots exists; kly_aim is Arcade's crew records), Regen (no regeneration is written for
   a bot), Adrenaline (online has no helper path for bots: kladren.c needs the crew records). Human seats keep 1.0 (their health / timers are per peer).
   Pure logic: klbottrait.h (klbottrait_test.c). Dry=1 resolves and logs, applies nothing. */
#include "klbottrait.h"
static int klcl_bot_look(DWORD actor, int *ch, DWORD *epoch);       /* klcrewlook.c, defined later: the host's applied look of that actor */
static DWORD klcl_bot_actor(int idx);                               /* klcrewlook.c: the actor of bot slot idx (digit - 1), 0 = none */
static int klcl_bot_name(int ch, char *name, int size);
static int klcl_bot_known(DWORD actor, DWORD *epoch);              /* klcrewlook.c: the actor still has its slot this epoch (latch) */            /* klcrewlook.c: the wardrobe name of a 1-based index */
static struct {
    int on, nres; DWORD last30;
    struct { DWORD actor, epoch; int ch, set; } c[16];
    volatile LONG hits, hit_scaled, hit_refused, lie, wardrobe_miss;
    double mult_sum;
} kltb;

/* the trait set of an online bot, -1 = none (not the host, no OnlineLooks look applied yet, a kept body, no [Trait.<name>] block). Logs once per bot and body. Game thread. */
static int kltt_bot_set(DWORD actor)
{
    int ch = 0, i, s, slot = -1; DWORD ep = 0; char name[32];
    if (!ktrait.on || !kltb.on || !actor) return -1;
    for (i = 0; i < 16; i++) { if (kltb.c[i].actor == actor) { slot = i; break; } }
    /* LATCH (review): once resolved, the set stays while the actor keeps its slot this epoch - a dead / downed / re-read / pending look (klcl_note code 13, 3, 16) must not blink the trait off */
    if (slot >= 0 && klcl_bot_known(actor, &ep) && kltb.c[slot].epoch == ep) return kltb.c[slot].set;
    if (!klcl_bot_look(actor, &ch, &ep) || ch < 1) return -1;
    if (slot >= 0 && kltb.c[slot].epoch == ep && kltb.c[slot].ch == ch) return kltb.c[slot].set;
    if (!klcl_bot_name(ch, name, sizeof name)) { InterlockedIncrement(&kltb.wardrobe_miss); return -1; }      /* wardrobe not readable this instant: asked again */
    if (slot < 0) { for (i = 0; i < 16 && kltb.c[i].actor; i++) ; slot = i < 16 ? i : (int)(kltb.nres % 16); }
    s = kltt_set_of(name);
    kltb.c[slot].actor = actor; kltb.c[slot].epoch = ep; kltb.c[slot].ch = ch; kltb.c[slot].set = s; kltb.nres++;
    if (ktrait.log) {
        if (s < 0) klog("trait: online bot %08lx wears %s: no [Trait.%s] block, no trait", (unsigned long)actor, name, name);
        else {
            const float *v = ktrait.set[s].v;
            klog("trait: online bot %08lx wears %s: Health x%.2f DamageIn x%.2f ReviveTime x%.2f APPLIED (hit scale x%.3f, LieSeconds x%.2f); DamageOut x%.2f AimSpread x%.2f Regen x%.2f Adrenaline x%.2f NOT applied online%s",
                 (unsigned long)actor, name, v[KLTT_HEALTH], v[KLTT_DMGIN], v[KLTT_REVIVE], kbt_hit_mult(v[KLTT_HEALTH], v[KLTT_DMGIN]), v[KLTT_REVIVE], v[KLTT_DMGOUT], v[KLTT_AIM], v[KLTT_REGEN], v[KLTT_ADREN],
                 ktrait.dry ? " - Dry=1: nothing is applied" : "");
        }
    }
    return s;
}

/* the factor of an online bot for one knob; 1.0 = nothing (also Dry, a human, any unresolved bot) */
static float kltt_bot(DWORD actor, int knob)
{
    int s;
    if (!ktrait.on || !kltb.on || ktrait.dry || knob < 0 || knob >= KLTT_N || !actor) return 1.0f;
    s = kltt_bot_set(actor);
    if (s >= 0 && knob == KLTT_REVIVE && ktrait.set[s].v[knob] != 1.0f) InterlockedIncrement(&kltb.lie);      /* asked once per down by klbotdown.c */
    return s < 0 ? 1.0f : ktrait.set[s].v[knob];
}

/* the multiplier on a hit on that online bot (DamageIn / Health); 1.0 = nothing */
static float kltt_bot_hit(DWORD actor) { return kltb.on ? kbt_hit_mult(kltt_bot(actor, KLTT_HEALTH), kltt_bot(actor, KLTT_DMGIN)) : 1.0f; }

/* 1 when the online-bot half is wanted at all: klbalance.c arms its slot-423 wrapper for it (not in Dry, which only logs) */
static int kltt_bot_on(void) { return ktrait.on && kltb.on && !ktrait.dry; }

/* the accuracy % an AI heister of that record is wanted at, from what he has (base); base itself when there is no trait */
static float kltt_aim(int rec, float base)
{
    float a = base, sp = kltt_get(rec, KLTT_AIM), dm = kltt_get(rec, KLTT_DMGOUT);
    if (sp == 1.0f && dm == 1.0f) return base;
    a = 100.0f - (100.0f - a) * sp;
    a *= dm;
    return a < 0 ? 0 : a > 100.0f ? 100.0f : a;
}

static int kvo_online_src(struct klw_src *s);                       /* klvoice_online.c, defined later */

static void kltt_tick(int game_thread)
{
    struct klw_who w; struct klw_src src; DWORD hero[8]; int i, onl = 0;
    DWORD now = GetTickCount();
    if (!ktrait.on || !game_thread || now - kltt_g.last < 500) return;
    kltt_g.last = now;
    if (kltb.on) {      /* [BotFill] OnlineBotTraits: resolve every applied bot (the per-bot line) and say the counters every 30 s while any bot is known */
        DWORD a[8]; int k, nb = 0, ch; DWORD ep;
        for (k = 0; k < 8; k++) { DWORD act = klcl_bot_actor(k); if (act && klcl_bot_look(act, &ch, &ep)) a[nb++] = act; }
        for (k = 0; k < nb; k++) kltt_bot_set(a[k]);
        if (nb && now - kltb.last30 >= 30000u) {
            LONG n = kltb.hit_scaled; kltb.last30 = now;
            klog("trait: online bots 30 s: %d bot(s) with a look, %d resolved in all | hits seen on bots %ld, scaled by DamageIn / Health %ld (mean x%.3f), write refused %ld | LieSeconds x ReviveTime applied %ld | DamageOut / AimSpread / Regen / Adrenaline: not applied online%s",
                 nb, kltb.nres, (long)kltb.hits, (long)n, n ? kltb.mult_sum / n : 1.0, (long)kltb.hit_refused, (long)kltb.lie, ktrait.dry ? " | Dry=1" : "");
        }
        else if (!nb) kltb.last30 = now;
    }
    if (!klk_who_any(&w, &onl) || w.n <= 0) {
        if (kltt_g.n || kltt_g.rules) { memset(&kltt_g, 0, sizeof kltt_g); kltt_g.human = -1; kltt_g.last = now; }
        return;
    }
    if (w.rules != kltt_g.rules || kltt_g.online != onl) { memset(&kltt_g, 0, sizeof kltt_g); kltt_g.rules = w.rules; kltt_g.online = onl; kltt_g.last = now; }
    if (onl) { if (!kvo_online_src(&src)) return; }                    /* the online round's own character list (klonline_read.c) */
    else {
        if (!klh_rd(w.rules + 0x208, hero, sizeof hero)) return;
        klw_source(&src, hero, w.key);
    }
    kltt_g.human = w.human >= 0 && w.human < w.n ? w.m[w.human].rec : -1;
    kltt_g.n = w.n;
    for (i = 0; i < w.n; i++) {
        int rec = w.m[i].rec, ch = w.m[i].ch; DWORD actor = w.m[i].actor;
        if (rec < 0 || rec >= KLW_NREC) continue;
        if (kltt_g.r[rec].ch == ch && kltt_g.r[rec].actor == actor && kltt_g.r[rec].told) continue;
        kltt_g.r[rec].ch = ch; kltt_g.r[rec].actor = actor; kltt_g.r[rec].told = 1; kltt_g.r[rec].set = -1; kltt_g.r[rec].name[0] = 0;
        if (ch < 1 || ch > src.n) { if (ktrait.log) klog("trait: record %d wears no body of the list: no trait", rec); continue; }
        snprintf(kltt_g.r[rec].name, sizeof kltt_g.r[rec].name, "%s", src.c[ch - 1].name);
        kltt_g.r[rec].set = kltt_set_of(kltt_g.r[rec].name);
        if (kltt_g.r[rec].set < 0) { if (ktrait.log) klog("trait: record %d = %s: no [Trait.%s] block, no trait", rec, kltt_g.r[rec].name, kltt_g.r[rec].name); continue; }
        if (ktrait.log) {
            const float *v = ktrait.set[kltt_g.r[rec].set].v; int human = rec == kltt_g.human;
            klog("trait: record %d = %s (%s) Health x%.2f DamageOut x%.2f DamageIn x%.2f Regen x%.2f ReviveTime x%.2f Adrenaline x%.2f AimSpread x%.2f%s%s",
                 rec, kltt_g.r[rec].name, human ? "human" : "AI heister", v[0], v[1], v[2], v[3], v[4], v[5], v[6],
                 onl ? " - ONLINE (OnlineTraits=1): the local player; NO factor is applied online, the line is for kltalk.c" : human ? " - DamageOut and AimSpread are NOT applied to the human" : " - Regen is NOT applied to an AI heister",
                 ktrait.dry ? " - Dry=1: nothing is applied" : "");
        }
    }
}

static void kltt_init(void)
{
    char t[32];
    memset(&kltt_g, 0, sizeof kltt_g); kltt_g.human = -1;
    if (!GetPrivateProfileIntA("Traits", "Enable", 0, klh_ini)) return;
    ktrait.on = 1;
    ktrait.dry = GetPrivateProfileIntA("Traits", "Dry", 0, klh_ini) != 0;
    ktrait.log = GetPrivateProfileIntA("Traits", "Log", 1, klh_ini);
    GetPrivateProfileStringA("Traits", "MaxDelta", "0.25", t, sizeof t, klh_ini);
    ktrait.delta = (float)atof(t);
    if (!(ktrait.delta >= 0) || ktrait.delta > 0.5f) ktrait.delta = 0.25f;
    kltb.on = GetPrivateProfileIntA("BotFill", "OnlineBotTraits", 0, klh_ini) != 0;      /* (recommended off) */
    if (kltb.on) klog("trait: OnlineBotTraits=1 (recommended off; HOST of an online FA round with bots, needs [BotFill] OnlineHost=1 + OnlineLooks=1; a bot wears the character the host drew): Health / DamageIn scale the hits on him (x DamageIn / Health, with OnlineBalance's Tough), ReviveTime scales [BotDown] LieSeconds; DamageOut, AimSpread, Regen, Adrenaline are NOT applied online%s", ktrait.dry ? " - Dry=1: only the log lines" : "");
    klog("trait: on; MaxDelta %.2f%s; a trait scales a number another module already writes (klgrudge.c health + accuracy, klbalance.c your health + regeneration, kldown.c / klbotdown.c get-up, kladren.c adrenaline), each behind its own Enable", ktrait.delta, ktrait.dry ? ", Dry=1 (log only)" : "");
}

#endif /* KLTRAIT_C */
