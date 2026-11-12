/* klgrenade_logic.h - the PURE parts of klgrenade.c's [Grenade] Release mode: the throw plan (release point, flight time, launch
 * velocity), the ammo bookkeeping after a shot, the config clamps. No game reads here: klgrenade.c feeds it numbers it read;
 * klgrenade_test.c checks it off-game.
 *
 * Ported from luvsic's a-newer-perspective loader/grenade.inc @32aa649 (gr_try, lines 503-577; in contribution with luvsic):
 * the NPC throw formula the item's own SetThrowVelocity (vt+0x2cc = 0x536dc0) is fed with. READ there, not measured here.
 * Units: game units (100 = 1 m), y is UP (feet at P+0x460, aim point P+0x27b0). */
#ifndef KLGRENADE_LOGIC_H
#define KLGRENADE_LOGIC_H
#include <math.h>

#define KLGR_AMMO_XOR 0xbeebbeebul            /* clip [item+0xdc] and reserve [item+0xe0] are stored XORed (READ grenade.inc gr_clip) */
#define KLGR_GRAVITY  982.0f                  /* cm/s^2, luvsic's constant */

struct klgr_cfg { float range, speed, vmax, up, fwd; };    /* luvsic's defaults: 2000 1000 1500 150 70 */
struct klgr_plan { float rel[3], tgt[3], v[3], t, dist; int fwd_only; };

static float klgr_clampf(float v, float lo, float hi) { return !(v == v) ? lo : v < lo ? lo : v > hi ? hi : v; }
static void klgr_cfg_clamp(struct klgr_cfg *c)
{
    c->range = klgr_clampf(c->range, 300.0f, 5000.0f);
    c->speed = klgr_clampf(c->speed, 200.0f, 3000.0f);
    c->vmax  = klgr_clampf(c->vmax, 300.0f, 3000.0f);
    c->up    = klgr_clampf(c->up, 0.0f, 300.0f);
    c->fwd   = klgr_clampf(c->fwd, 0.0f, 200.0f);
}

/* clip / reserve as the game stores them */
static int klgr_unxor(unsigned long raw) { return (int)(raw ^ KLGR_AMMO_XOR); }

/* The throw: from the feet and the aim point. 0 = refused (a non-finite number, or no usable aim: the aim point must be 50 cm ..
   1 km away horizontally; luvsic falls back to the facing there, this port refuses and logs). 1 = plan filled. */
static int klgr_plan_throw(const float feet[3], const float aim[3], const struct klgr_cfg *c, struct klgr_plan *o)
{
    float dx, dz, h, fx, fz, d[3], L, t, vl, s; int i;
    for (i = 0; i < 3; i++) if (!(feet[i] == feet[i]) || !(aim[i] == aim[i]) || fabsf(feet[i]) > 1e7f || fabsf(aim[i]) > 1e7f) return 0;
    dx = aim[0] - feet[0]; dz = aim[2] - feet[2]; h = sqrtf(dx * dx + dz * dz);
    if (!(h > 50.0f && h < 100000.0f)) return 0;
    fx = dx / h; fz = dz / h;
    o->rel[0] = feet[0] + fx * c->fwd; o->rel[1] = feet[1] + c->up; o->rel[2] = feet[2] + fz * c->fwd;    /* clear of the capsule */
    for (i = 0; i < 3; i++) { o->tgt[i] = aim[i]; d[i] = aim[i] - o->rel[i]; }
    L = sqrtf(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
    if (L > c->range) { s = c->range / L; d[0] *= s; d[1] *= s; d[2] *= s; L = c->range; }
    if (L < 100.0f) { d[0] = fx * 300.0f; d[1] = 0.0f; d[2] = fz * 300.0f; L = 300.0f; }               /* too close: lob it 3 m ahead */
    t = L / c->speed; if (t < 0.25f) t = 0.25f;
    o->v[0] = d[0] / t; o->v[1] = d[1] / t + 0.5f * KLGR_GRAVITY * t; o->v[2] = d[2] / t;
    vl = sqrtf(o->v[0] * o->v[0] + o->v[1] * o->v[1] + o->v[2] * o->v[2]);
    if (vl > c->vmax) { s = c->vmax / vl; o->v[0] *= s; o->v[1] *= s; o->v[2] *= s; }
    o->t = t; o->dist = L; o->fwd_only = 0;
    return 1;
}

/* One grenade used: clip first, else reserve; a clip emptied with reserve left is refilled by one (DM 0x5e8030).
   -> 1 when the item is now empty (clip + reserve == 0). */
static int klgr_consume(int clip, int res, int refill, int *nclip, int *nres)
{
    int c = clip, r = res > 0 ? res : 0;
    if (c > 0) c--; else if (r > 0) r--;
    if (refill && c == 0 && r > 0) { c = 1; r--; }
    *nclip = c; *nres = r;
    return c + r == 0;
}

/* Did the shot launch? luvsic's proof (review 13 Oct): item+0x138 (shots) changed AND the release point was consumed (zeroed) AND the
   pool cursor moved off the entry that was next. */
static int klgr_launched(int shots0, int shots1, int rel_zeroed, int idx_next, int idx1, int pool_count)
{
    return shots1 != shots0 && rel_zeroed && pool_count > 0 && idx1 != idx_next;
}

/* Cooldown in ms (luvsic default 1 s), wrap safe. */
static int klgr_cool_over(unsigned long last, unsigned long now, unsigned long ms) { return !last || now - last >= ms; }

#endif
