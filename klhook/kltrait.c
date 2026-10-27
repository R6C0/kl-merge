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
    klog("trait: on; MaxDelta %.2f%s; a trait scales a number another module already writes (klgrudge.c health + accuracy, klbalance.c your health + regeneration, kldown.c / klbotdown.c get-up, kladren.c adrenaline), each behind its own Enable", ktrait.delta, ktrait.dry ? ", Dry=1 (log only)" : "");
}

#endif /* KLTRAIT_C */
