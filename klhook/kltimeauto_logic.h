/* kltimeauto_logic.h - [Lobby] TimeAuto, the PURE decision (no game memory, no log). Included by kllobbyopt.c and kltimeauto_test.c. No windows.h.
   TimeAuto=N (1..20 minutes, 0 = stock): once per lobby the host's Heist time is set to N without a key press. The value is CLAMPED to the range the
   lobby row offers with the current [Lobby] TimeMin / TimeMax (stock 3..5), so the auto value is always one LEFT/RIGHT can reach and the stock clamps
   never see a number outside their range (safest choice; a bench wanting 6 min sets TimeMax=6 or more too). Returns the minutes to set, or 0 = do nothing
   (off, invalid, or the lobby already holds that value). */
#ifndef KLTIMEAUTO_LOGIC_H
#define KLTIMEAUTO_LOGIC_H

static int kta_clamp(int want, int tmin, int tmax)
{
    int lo = (tmin >= 1 && tmin <= 2) ? tmin : 3, hi = (tmax >= 6 && tmax <= 20) ? tmax : 5;
    if (want < lo) want = lo;
    if (want > hi) want = hi;
    return want;
}
static int kta_target(int want, int tmin, int tmax, int cur)
{
    int n;
    if (want < 1 || want > 20) return 0;
    n = kta_clamp(want, tmin, tmax);
    return n == cur ? 0 : n;
}
#endif
