/* klboardpar_logic.h - [BotFill] OnlineBoardAllNear (cm), the PURE decision (no game memory, no log, no clock). Included by klbotfill.c and klboardpar_test.c.
   wk-boardpar-1102. Static reading of kl2.exe (re/boardall_review_exe.md, re/bots_follow_out.md; NOT run live): stock Arcade sets "aboard" (status 4) only through the boarding rule 0x6840a0,
   reached from the escape/boarding box, so only a bot AT the van counts; any other AI record is shot when the van leaves. Every Arcade log line "taken aboard" says 0.0 m from the box. OnlineBoardAll
   counts bots up to OnlineBoardAllM (default 6000 cm = 60 m) as aboard and so banks their whole tally (RT4A/RT4B: $3.5M for bots left behind). OnlineBoardAllNear > 0 narrows that radius
   to min(OnlineBoardAllM, Near); a typical Arcade-like value is about 300 cm (GUESS: box half extents are 0.8 to 4 m). 0 = today's behaviour. */
#ifndef KLBOARDPAR_LOGIC_H
#define KLBOARDPAR_LOGIC_H

/* normalise the ini value: <= 0 = off (0), otherwise at least 100 cm, at most 30000 */
static float kbp_near_clamp(int v)
{
    if (v <= 0) return 0.0f;
    if (v < 100) v = 100;
    if (v > 30000) v = 30000;
    return (float)v;
}

/* effective boardall radius in cm: OnlineBoardAllM, narrowed by Near when Near > 0 */
static float kbp_limit(float all_m, float near_m)
{
    return (near_m > 0 && near_m < all_m) ? near_m : all_m;
}

/* decision for a bot at distance d cm: 1 = count aboard, 0 = too far for boardall anyway, 2 = within OnlineBoardAllM but left out by Near (log it) */
static int kbp_decide(float d, float all_m, float near_m)
{
    if (d > all_m) return 0;
    if (near_m > 0 && d > near_m) return 2;
    return 1;
}
#endif
