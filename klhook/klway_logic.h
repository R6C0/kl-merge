/* klway_logic.h - [BotFill] OnlineWayPerMap / OnlineLegHopDy, the PURE decisions (no game memory, no log, no clock). Included by klbotfill.c and klway_test.c.
   Research wk-rtroute-1101 (DM09): the tower and the street are separate nav parts joined only by a hook jump (klhop.c [CrewHop]); a leg across the join can never be walked,
   and DM09 (slot F06) loaded DD06's [BotFillWay_F06] route. PerMap picks the section; LegHopDy keeps a bot off legs on another floor and holds it at the last leg of its floor.
   Both default 0 = today. NOT run live. */
#ifndef KLWAY_LOGIC_H
#define KLWAY_LOGIC_H
#include <math.h>

#define KWY_HOLD_MS 60000      /* GUESS: a bot waits at most 60 s for klhop to carry it before the old timer advances it (the 90 s cap stays the backstop) */

/* OnlineWayPerMap: 0 = slot section only (today). 1 = [BotFillWay_<MAP>] first, slot section when the per-map one is empty. 2 = per-map first; the slot section only when no
   redirected map folder is known (a stock slot map), so DD06's route never loads on DM09. Returns 1 = read the slot section too. */
static int kwy_use_slot(int mode, int folderKnown, int permapN)
{
    if (mode != 1 && mode != 2) return 1;
    if (permapN > 0) return 0;
    if (mode == 2 && folderKnown) return 0;
    return 1;
}

/* first leg still AHEAD of a bot at p (as klbf_way_start before): nearer the exit (horizontally) by more than `near`. hopdy > 0: legs whose height differs from the bot's by more than
   hopdy are skipped (another floor / the other side of the join). pts is n x {x, y(height), z}. Returns n when none is left. */
static int kwy_start(const float p[3], const float exitp[3], const float (*pts)[3], int n, float hopdy, float near_)
{
    float bd = (p[0] - exitp[0]) * (p[0] - exitp[0]) + (p[2] - exitp[2]) * (p[2] - exitp[2]), wd; int i;
    bd = (float)sqrt(bd) - near_;
    for (i = 0; i < n; i++) {
        if (hopdy > 0 && fabs(pts[i][1] - p[1]) > hopdy) continue;
        if (hopdy > 0 && i + 1 < n && fabs(pts[i + 1][1] - pts[i][1]) > hopdy) return i;      /* the last leg of this floor (the lift floor) lies no nearer the exit than the hall (DM09: 11.3 km vs 11.2 km), but it is where the carry happens: always ahead */
        wd = (float)sqrt((pts[i][0] - exitp[0]) * (pts[i][0] - exitp[0]) + (pts[i][2] - exitp[2]) * (pts[i][2] - exitp[2]));
        if (wd < bd) return i;
    }
    return n;
}

/* 1 = hold on the current leg: hopdy > 0, the NEXT leg is more than hopdy above/below the bot (it still has to be carried across), and holdCap ms have not passed on this leg */
static int kwy_hold(float botY, float nextY, float hopdy, unsigned long onLegMs, unsigned long holdCap)
{
    if (!(hopdy > 0)) return 0;
    if (onLegMs >= holdCap) return 0;
    return fabs(nextY - botY) > hopdy;
}

/* 1 = the carry happened: the bot was held on this leg (heldFlag), is now on the NEXT leg's floor (within hopdy) and off the current leg's floor, so the current leg counts as reached (no idle 15 s timer) */
static int kwy_carried(int heldFlag, float botY, float curY, float nextY, float hopdy)
{
    if (!heldFlag || !(hopdy > 0)) return 0;
    return fabs(nextY - botY) <= hopdy && fabs(curY - botY) > hopdy;
}
/* wk-dropfix-1101 (SP2 11-01). OnlineStackProbe=3 POLL: one log line per change of the watched stack's amount (+0x34), state (+0x64) or armed byte (+0x6c); -1 = unreadable (a change to or from
   unreadable counts, so a freed object is said once). prev* < -2 = nothing read yet (the first read is always a line). */
static int ksp_changed(int pAmt, int pSt, int pArm, int amt, int st, int arm)
{
    if (pAmt < -2) return 1;
    return amt != pAmt || st != pSt || arm != pArm;
}

/* OnlineDropFollow: may a bot be sent to this type-1 object? Not a HIDDEN one (the pool objects armed at round start sit hidden at one pool point: DD09 and DD05 (5224, 1020, -11056)),
   and only one that appeared within the window after a REAL stack drain (drained = a type-0/2 stack was seen to empty within +-3 s of the drop's first sighting). hidden -1 = unreadable = no. */
static int kdf_drop_ok(int hidden, int drained)
{
    return hidden == 0 && drained != 0;
}
#endif
