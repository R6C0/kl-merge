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

/* wk-rt2-1101 (RT1 11-01): may the exit walk follow the waypoint legs? Today only while NO van object is known (!van), no escape box (bxOn 0), the exit trigger found (vh) and the van not called.
   DM09 puts the van object in the street from the start (scan: van 58421b40 at (24235, -59842, 13883) while the bots are in the tower at y 19600): van != 0 made legsLeft 0 AND blocked the
   exit-trigger lookup (!van), so vh stayed 0 and all 7 bots walked straight at a van 60 km away. withVan (OnlineLegsWithVan): a known van does not stop the legs and the trigger is not needed
   (the van is the exit; the board test is the old 'van within 2*Near'). Returns 1 = legs run. */
static int kwy_legs_left(int withVan, int van, int bxOn, int vh, int called, int n, int leg)
{
    if (bxOn || called || n <= 0 || leg >= n) return 0;
    if (van) return withVan != 0;
    return vh != 0;
}

/* wk-rt2-1101: the exit point the legs are measured against (kwy_start): the trigger's place when known, else the van's (withVan and a van but no trigger) */
static const float *kwy_exit(int withVan, int van, int vh, const float *tpos, const float *vpos)
{
    return (withVan && van && !vh) ? vpos : tpos;
}

/* wk-rt2-1101 (RT1): 1 = klt_refuse may read the actor's class through klh_avt (a private copy of the ZFFActor vtable counts as ZFFActor). RT1L: the host's bots were moved onto klbalance.c's
   private table ('cop->bot factor: bot actor ... now on the private table'), klt_refuse read the raw vtable and refused all 17 carries with 'its actor is not a ZFFActor'. */
static int kwy_class_ok(int privOk, unsigned long raw, unsigned long viaAvt, unsigned long want)
{
    return privOk ? viaAvt == want : raw == want;
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
/* wk-rt9-1102 OnlineLateExitRoute: remaining walk length (cm, horizontal x/z) from p through legs[leg..n-1] to the exit point. leg >= n or n <= 0: straight to the exit. */
static float kwy_route_cm(const float p[3], const float (*pts)[3], int n, int leg, const float exitp[3])
{
    float len = 0, cx = p[0], cz = p[2]; int i;
    for (i = (leg < 0 ? 0 : leg); i < n; i++) { len += (float)sqrt((pts[i][0] - cx) * (pts[i][0] - cx) + (pts[i][2] - cz) * (pts[i][2] - cz)); cx = pts[i][0]; cz = pts[i][2]; }
    len += (float)sqrt((exitp[0] - cx) * (exitp[0] - cx) + (exitp[2] - cz) * (exitp[2] - cz));
    return len;
}

/* wk-rt9-1102: the OnlineLateExit threshold (s of clock left) for one bot. route 0 = base (today). route 1 = walk time of the remaining route at walkCmS plus padS, clamped to 400 (the old OnlineLateExit cap of 200 is below DM09's walk), never below base.
   DM09: about 310 m at 130 cm/s is 238 s + 20 = 258 s, so a carrier leaves at once on a 250 s clock and loots until about t=112 s on a 370 s clock (258 s clock left). base 0 (OnlineLateExit off) stays 0. */
static int kwy_late_s(int route, int base, float routeCm, float walkCmS, int padS)
{
    float s;
    if (!route || base <= 0 || !(walkCmS >= 10.0f) || !(routeCm >= 0)) return base;
    s = routeCm / walkCmS + (float)padS;
    if (s > 400.0f) s = 400.0f;
    if (s < (float)base) return base;
    return (int)(s + 0.5f);
}
#endif
