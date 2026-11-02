/* klshield_logic.h - [Shield] pure arithmetic and the Online gate decision (no game memory, no log, no windows.h). Included by klshield.c and klshield_test.c.
   wk-crewonline-1102: [Shield] Online=0|1|2 (1 = the ONLINE HOST's own player holding an AI soldier gets the Arcade cover; 2 = dry log). NOT run live. */
#ifndef KLSHIELD_LOGIC_H
#define KLSHIELD_LOGIC_H

/* the health handed back for a loss d of a player at hp_now whose maximum is mx: eff x d, never past the maximum; NaN / non-positive -> 0 */
static float klsh_refund(float hp_now, float d, float mx, float eff)
{
    float r = d * eff;
    if (!(r > 0)) return 0;
    if (!(hp_now == hp_now) || !(mx == mx)) return 0;
    if (hp_now + r > mx) r = mx - hp_now;
    return r > 0 ? r : 0;
}
/* the health the victim loses for a refund r of a player whose maximum is pmx: takes x (r / pmx) of HIS maximum vmx */
static float klsh_victim_loss(float r, float pmx, float vmx, float takes)
{
    if (!(pmx >= 1.0f) || !(r > 0) || !(takes > 0) || !(vmx >= 0)) return 0;
    return takes * (r / pmx) * vmx;
}
/* the hostage's health after paying loss: never below 1 (downed, not killed by his own cover duty); a man already at or under 1 is left as he is */
static float klsh_victim_after(float vhp, float loss)
{
    float nv = vhp - loss;
    if (nv < 1.0f) nv = vhp > 1.0f ? 1.0f : vhp;
    return nv;
}
/* the health at or below which the hostage is floored: DownPct of his maximum, at least 1 */
static float klsh_down_threshold(float vmx, float pct)
{
    float t = vmx * pct / 100.0f;
    return t > 1.0f ? t : 1.0f;
}

/* which world a tick runs in. arc_cfg = [Shield] Enable; arc_ok = the Arcade gate (klr_arcade && klb_level && klb_read) passed;
   online_cfg = [Shield] Online 0..2; ov = klbd_online_view result (only looked at when the Arcade part does not apply).
   -> KLSH_W_ARC / KLSH_W_ONLINE / KLSH_W_FORGET (not in a round of either: drop the round state) / KLSH_W_SKIP (transient: change nothing) */
#define KLSH_W_FORGET 0
#define KLSH_W_ARC 1
#define KLSH_W_ONLINE 2
#define KLSH_W_SKIP 3
static int klsh_world(int arc_cfg, int arc_ok, int online_cfg, int ov)
{
    if (arc_cfg && arc_ok) return KLSH_W_ARC;
    if (online_cfg < 1 || online_cfg > 2) return KLSH_W_FORGET;
    if (ov < 0) return KLSH_W_SKIP;
    if (ov > 0) return KLSH_W_ONLINE;
    return KLSH_W_FORGET;
}
#endif
