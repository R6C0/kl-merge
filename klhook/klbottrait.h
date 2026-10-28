/* klbottrait.h - the pure logic of [BotFill] OnlineBotTraits (kltrait.c, 2026-10-28, wk-trait; re\traits.md ONLINE section). No game memory, no windows.h:
 * klbottrait_test.c checks it off-game.
 *
 * An online AI heister (bot) has no crew record, so kltrait.c's record table cannot name him. His identity online is the character the HOST drew for him in
 * klcrewlook.c (OnlineLooks=1: klcl_t.e[digit - 1].ch, an index 1..n into the wardrobe list); this header maps that index to a wardrobe name and turns the
 * trait factors of that name into the numbers the host-side write sites use:
 *   hit scale     a hit on the bot is multiplied by DamageIn / Health  (the same as a maximum health of Health / DamageIn for equal hit counts, as kltt_hp);
 *                 it is applied on top of the OnlineBalance scale (Tough divides too: 1 / tough x DamageIn / Health, the two are independent factors)
 *   lie seconds   LieSeconds x ReviveTime (klbotdown.c, as Arcade)
 * Every factor is held to 1 +- delta (kbt_clamp), whatever the ini says.
 */
#ifndef KLBOTTRAIT_H
#define KLBOTTRAIT_H

/* a factor held to 1 +- delta; NaN, zero and negative = 1 (kltt_clamp's rule) */
static float kbt_clamp(float v, float delta)
{
    if (!(v == v) || v <= 0) return 1.0f;
    if (v < 1.0f - delta) return 1.0f - delta;
    if (v > 1.0f + delta) return 1.0f + delta;
    return v;
}

/* the 1-based wardrobe index ch (klcrewlook.c's e.ch) -> the 0-based index into a list of n names, or -1 (0 = the draw kept his body; > n = not this wardrobe) */
static int kbt_index(int ch, int n) { return (ch >= 1 && ch <= n) ? ch - 1 : -1; }

/* the multiplier on a hit's scale for a victim with these (already clamped) factors: DamageIn / Health. Both unset (1) = 1. */
static float kbt_hit_mult(float health, float dmgin)
{
    if (!(health > 0) || !(dmgin > 0)) return 1.0f;
    return dmgin / health;
}

/* the whole scale from OnlineBalance's Tough (>0, a divisor) and the trait: 1 / tough x DamageIn / Health. tough <= 0 = no Tough. */
static float kbt_total(float tough, float health, float dmgin)
{
    return kbt_hit_mult(health, dmgin) / (tough > 0 ? tough : 1.0f);
}

/* LieSeconds x ReviveTime; a non-positive base stays (that path is off) */
static float kbt_lie(float base, float revive)
{
    if (!(base > 0)) return base;
    return base * (revive > 0 ? revive : 1.0f);
}

/* a hit scale that must be left alone by the trait: not a finite positive number, or a point-blank step (above 1 and up to the OnlinePointBlank number 'want', as
   klbalance.c's own test: those absolute steps are not scaled by Tough either) */
static int kbt_skip_hit(float f, float want)
{
    if (!(f == f) || f <= 0) return 1;
    if (f > 1.0001f && f <= want + 0.001f) return 1;
    return 0;
}

#endif
