/* kldown_hold.h - the decision of [Down] MashHold (kldown.c), PURE: no game memory, no log, no clock of its own. Included by kldown.c and by
   kldown_hold_test.c (the off-game harness; same file, so what the harness proves is the code that ships).
   What it decides. ONLINE the part does not speed up the get-up clip (that is a local write the other machines never see). It HOLDS the
   get-up instead: while he lies, the GET UP button is kept from reaching the game (kldown.c: bit 0x80 of the input mask), a meter fills by
   the presses of the Cover key counted from the keyboard / pad, and when it is full the hold is let go - the stock one-press get-up then
   runs at stock speed and the game's own GettingUp message goes to the others (re\down_online_built.md).
   Unit of the meter: one press = 1.0 (a press is a key EDGE, up -> down; a held key counts once). need = presses worth the meter must reach,
   decay = what the meter loses a second. dt is the game's frame seconds (the caller clamps it).
   States of the down, [D+4]: 0 up, 2 falling, 1 lying, 3 getting up. Presses count only while he LIES (1): the fall is held, nothing is
   stored in it, so a man cannot charge the meter before he has landed.
   GUESS: need 8 and decay 1.5 a second are numbers for the owner's hands, not measured (6 presses a second fill it in about 1.8 s, 3 a second
   in about 5 s, under 1.5 a second never). */
#ifndef KLDOWN_HOLD_H
#define KLDOWN_HOLD_H

struct kldh {
    float meter;           /* presses' worth in the meter now */
    int latched;           /* 1 = the meter was full (or the time bound ran out): the hold is let go until the down is over */
    int timeout;           /* 1 = latched by the time bound, not by the meter */
    int prev;              /* the key as the last pass saw it */
    int presses;           /* edges counted while he lay, in this down */
    DWORD t_lie;           /* GetTickCount of the first pass that saw him lying (0 = not yet) */
    DWORD t_full;          /* the tick the hold was let go (0 = not yet) */
};

/* One pass. ds = [D+4]; key = the Cover key / pad button is down now; dt = seconds since the last pass; per = meter a press adds
   (1.0 unless a key says other); decay = per second; need = meter that lets go; maxlie_ms = time bound on the lying (0 = none);
   alive = he lives and the round runs (else: no hold, everything reset). -> 1 = keep the hold (the GET UP button must not reach the
   game), 0 = let it through. *edge = 1 when this pass counted a press. */
static int kldh_step(struct kldh *h, DWORD ds, int key, float dt, float per, float decay, float need, DWORD now, DWORD maxlie_ms, int alive, int *edge)
{
    int e = 0;
    if (edge) *edge = 0;
    if (!alive || (ds != 1 && ds != 2)) {            /* up, getting up, dead, out of play: the next down starts afresh; nothing is held */
        h->meter = 0; h->latched = 0; h->timeout = 0; h->presses = 0; h->t_lie = 0; h->t_full = 0; h->prev = key != 0;
        return 0;
    }
    if (ds == 2) {                                   /* falling: held, no press counts, nothing is stored */
        h->meter = 0; h->latched = 0; h->timeout = 0; h->presses = 0; h->t_lie = 0; h->t_full = 0; h->prev = key != 0;
        return 1;
    }
    /* lying */
    if (!h->t_lie) h->t_lie = now ? now : 1;
    if (dt < 0 || dt != dt) dt = 0;
    if (dt > 0.25f) dt = 0.25f;                      /* a hitch must not empty (or fill) the meter by itself */
    if (!h->latched) {
        h->meter -= decay * dt; if (h->meter < 0) h->meter = 0;
        if (key && !h->prev) { h->meter += per; h->presses++; e = 1; }
        if (h->meter >= need) { h->latched = 1; h->t_full = now ? now : 1; }
        else if (maxlie_ms && (DWORD)(now - h->t_lie) >= maxlie_ms) { h->latched = 1; h->timeout = 1; h->t_full = now ? now : 1; }
    }
    h->prev = key != 0;
    if (edge) *edge = e;
    return h->latched ? 0 : 1;
}

/* ---- the Cover-key filter (MashHoldHow=2), PURE: what the keyboard proxy in klrigid.c does to a GetDeviceData buffer / a GetDeviceState array.
   A buffered DirectInput keyboard event is a DIDEVICEOBJECTDATA of 20 bytes on x86: dwOfs = the DIK scan code, dwData = 0x80 down / 0 up.
   Rule: while the filter is on, the Cover key's PRESS events are dropped (the game never sees the key go down); the RELEASE of a press that was
   dropped is dropped too (a release without a press is harmless, but dropping it keeps the pair together); the release of a press that was
   NOT dropped (the key was already down when the hold began) is kept, so the game is never left believing a key is down. Order of the other
   events is kept. Returns the new count. scan = 0 never matches. GetAsyncKeyState (the meter's source) is a different path (user32's
   async key table, not DirectInput's buffer): it still sees every press this drops. */
struct kldh_ev { DWORD ofs, data, ts, seq, app; };
struct kldh_kf { int dropped_down; };

static DWORD kldh_filter_events(struct kldh_kf *k, struct kldh_ev *ev, DWORD n, DWORD scan, int on)
{
    DWORD i, o = 0;
    for (i = 0; i < n; i++) {
        int drop = 0;
        if (scan && ev[i].ofs == scan) {
            if (ev[i].data & 0x80) { if (on) { drop = 1; k->dropped_down = 1; } else k->dropped_down = 0; }   /* a press that passes ends any owed release: a stale one (the device lost its buffer on a focus change) must not eat the release of THIS press and leave the key stuck down */
            else if (k->dropped_down) { drop = 1; k->dropped_down = 0; }
        }
        if (!drop) { if (o != i) ev[o] = ev[i]; o++; }
    }
    return o;
}

/* GetDeviceState (256 bytes, 0x80 = down): the Cover key shows up while the filter is on. */
static void kldh_filter_state(BYTE *st, DWORD cb, DWORD scan, int on)
{
    if (on && scan && scan < cb) st[scan] = 0;
}

/* ---- the victim-side GIVE-BACK (OnlineFreeFall / OnlineFactors), PURE: he lost (before - now) in one frame to a hit the game priced in full; the price
   he should have paid is factor x that. Returns the health to write: now + (1 - factor) x loss, never above what he had before the hit and never above
   max. *lethal = 1 when he is already dead (now <= 0.01): nothing is given back - a hit bigger than his health kills him before it can be priced.
   A factor of 1 or more, below 0 or not a number gives nothing back (the hit stays at the game's price). */
static float kldh_giveback(float now, float before, float max, float factor, int *lethal)
{
    float give, nh;
    if (lethal) *lethal = 0;
    if (now <= 0.01f) { if (lethal) *lethal = 1; return now; }
    if (!(factor >= 0.0f) || factor >= 0.999f || !(before > now)) return now;
    give = (before - now) * (1.0f - factor);
    nh = now + give;
    if (nh > before) nh = before;
    if (max > 0 && nh > max) nh = max;
    return nh > now ? nh : now;
}

/* ---- the PRE-APPLY price (OnlinePreScale), PURE: the rules' damage hook (slot 15 of the FA rules, kl2 0x425320(victim, float *delta, attacker), called by
   0x6e3400 BEFORE the subtraction) hands over the delta by pointer; for this machine's own knocked-down body the delta is multiplied by Arcade's factor.
   kldh_pick = which factor applies (SHARED with the give-back fallback, so both paths price a hit the same way); kldh_prescale = the delta to apply. */
enum { KLDH_R_NONE = 0, KLDH_R_FREE, KLDH_R_COP, KLDH_R_CREW, KLDH_R_COP_FALL, KLDH_R_CREW_FALL };
/* ds = [D+4] (1 lying, 2 falling, 3 getting up); cls = attacker class (0 = none / a human heister: unscaled as in Arcade, 1 = police / guard / human cop, 2 = AI heister);
   hurt = the ini's Vulnerable; ofree / ofac = OnlineFreeFall / OnlineFactors. -> the factor (1 = the hit stays at the game's price); *rule = KLDH_R_* */
static float kldh_pick(int ds, int cls, int hurt, int ofree, int ofac, float cop, float crew, int *rule)
{
    *rule = KLDH_R_NONE;
    if (ds == 2 && ofree && !hurt) { *rule = KLDH_R_FREE; return 0.0f; }
    if (ofac && cls == 1) { *rule = ds == 2 ? KLDH_R_COP_FALL : KLDH_R_COP; return cop; }
    if (ofac && cls == 2) { *rule = ds == 2 ? KLDH_R_CREW_FALL : KLDH_R_CREW; return crew; }
    return 1.0f;
}

/* delta = the health change the game is about to apply (negative = damage). A heal (>= 0), NaN, a factor of 1 or more, below 0 or not a number: unchanged.
   Otherwise delta x factor (never more damage than the game priced, never a heal). */
static float kldh_prescale(float delta, float factor)
{
    if (!(delta < 0.0f) || delta < -1e9f) return delta;
    if (!(factor >= 0.0f) || factor >= 0.999f) return delta;
    return delta * factor;
}

/* Does the after-the-hit give-back stay out of THIS health drop? Only when slot 15 priced / considered a hit of this machine's OWN downed body a moment ago
   (t_hit = GetTickCount of that hit, 0 = none seen in this round). A slot-15 call for anybody else's body, or a round with no own-body hit yet, must NOT keep it out:
   a hit applied by a path slot 15 never sees on this machine would then go unpriced. window_ms covers the tick lagging the hit by a frame or two. */
static int kldh_giveback_stays_out(int pre, DWORD t_hit, DWORD now, DWORD window_ms)
{
    return pre && t_hit != 0 && (DWORD)(now - t_hit) <= window_ms;
}

#endif /* KLDOWN_HOLD_H */
