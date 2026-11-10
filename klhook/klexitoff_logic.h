/* klexitoff_logic.h - pure maths for [BotFill] OnlineExitOffset (klbotfill.c klbf_ot_slot_target). No game access, no Windows; tested by klexitoff_test.c.
 *
 * Why: online BotFill orders the AI heisters to the CENTRE of the exit box (otrExitLevel / the AllyEscapeBox). On several maps the escape van's key-framed
 * drive-in lane runs through or beside that centre (DD10 bench-proven: a seat at the centre was run over; DD01 van lines pass 131..177 cm from it, see
 * re/van_lane_audit_1110.md). The van's footprint is 110 cm half width + 40 cm capsule = 150 cm either side of its line.
 *
 * What: move the target sideways, off the lane line, to a point still inside the box with a margin. The lane line is
 *   - the line through the box centre and the van's position when that is known and at least KLXO_MINVAN cm away (every lane ends at the call/stop place
 *     near the centre; the van arrives along it), else
 *   - the box's longer horizontal axis (GUESS: lanes run along the long side of the box).
 * The target is centre +- perpendicular * off (the side with the room is taken; 100 %, 80 %, 60 % of off, never under KLXO_MINOFF), the caller says what
 * "inside with a margin" means. Nothing valid = the centre (the old behaviour). All distances in cm, horizontal plane x/z (index 0 and 2 of a position). */
#ifndef KLEXITOFF_LOGIC_H
#define KLEXITOFF_LOGIC_H
#include <math.h>

#define KLXO_MINVAN 300.0f     /* the van's position counts as a direction only when it is at least this far from the centre */
#define KLXO_MINOFF 250.0f     /* never shift by less (lane edge 150 + a lane line up to ~180 off the centre is the audit's worst case, minus slack) */

/* the unit lane direction (x, z) through the centre c: toward the van pos when usable, else the long axis (long_xz, unit, any sign). Returns 1 when from the van, 0 from the axis, -1 when neither is usable. */
static int klxo_lane(const float c[3], const float *van, const float long_xz[2], float out[2])
{
    if (van) {
        float dx = van[0] - c[0], dz = van[2] - c[2], l = (float)sqrt(dx * dx + dz * dz);
        int origin = fabs(van[0]) <= 1.0f && fabs(van[1]) <= 1.0f && fabs(van[2]) <= 1.0f;      /* a vehicle that is not placed yet sits at (0,0,0) */
        if (!origin && l >= KLXO_MINVAN) { out[0] = dx / l; out[1] = dz / l; return 1; }
    }
    if (long_xz) {
        float l = (float)sqrt(long_xz[0] * long_xz[0] + long_xz[1] * long_xz[1]);
        if (l > 0.5f) { out[0] = long_xz[0] / l; out[1] = long_xz[1] / l; return 0; }
    }
    return -1;
}

typedef int (*klxo_inside_fn)(void *ctx, const float p[3]);      /* 1 = p is inside the box WITH the caller's margin and stands on floor the caller trusts */

/* the shifted target for centre c (out = c when nothing is valid or off <= 0). Returns 1 when out moved, 0 when out = c. */
static int klxo_target(const float c[3], const float *van, const float long_xz[2], float off, klxo_inside_fn inside, void *ctx, float out[3])
{
    static const float k[3] = { 1.0f, 0.8f, 0.6f };
    float lane[2], px, pz; int i, sgn;
    out[0] = c[0]; out[1] = c[1]; out[2] = c[2];
    if (off < KLXO_MINOFF || !inside || klxo_lane(c, van, long_xz, lane) < 0) return 0;
    px = -lane[1]; pz = lane[0];      /* the perpendicular */
    for (i = 0; i < 3; i++) {
        float d = off * k[i], p[2][3];
        if (d < KLXO_MINOFF) break;
        for (sgn = 0; sgn < 2; sgn++) {
            float s = sgn ? -1.0f : 1.0f;
            p[sgn][0] = c[0] + s * px * d; p[sgn][1] = c[1]; p[sgn][2] = c[2] + s * pz * d;
        }
        { int a = inside(ctx, p[0]), b = inside(ctx, p[1]);
          if (a) sgn = 0;      /* both fit: the + side, deterministic */
          else if (b) sgn = 1; else continue;
          out[0] = p[sgn][0]; out[1] = p[sgn][1]; out[2] = p[sgn][2]; return 1; }
    }
    return 0;
}
#endif
