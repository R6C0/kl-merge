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

#endif /* KLDOWN_HOLD_H */
