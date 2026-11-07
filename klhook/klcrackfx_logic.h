/* klcrackfx_logic.h - the cracked lens' immersion numbers (klreshade.c 6, owner 11-07: "just need it to feel a bit more immersive").
 * Pure logic, no windows.h, so klcrackfx_test.c checks it off-game.
 *   klcf_heal: a crack fades as health recovers after it was made: share rec = (now - at birth) / (1 - at birth), 0..1; the intensity
 *              is scaled by 1 - fade * rec. fade (LensCrackHealFade, 0..1) 0 = the old fixed crack; 0.5 (recommended) = half strength at full
 *              health, so a crack never goes away by itself (it still clears on death / respawn / new round, as before).
 *   klcf_age:  KL_CrackFX.x = 1 + the newest crack's age in seconds (capped at 60), 0 = no crack. The +1 keeps 0 for 'no data', which is
 *              what an older dll leaves in the uniform: the shader then draws no flash. GUESS: fade 0.5 and the 60 s cap are by eye. */
#ifndef KLCRACKFX_LOGIC_H
#define KLCRACKFX_LOGIC_H

static float klcf_heal(float inten, float h_birth, float h_now, float fade)
{
    float rec;
    if (!(fade > 0.0f) || !(h_birth == h_birth) || !(h_now == h_now)) return inten;
    if (fade > 1.0f) fade = 1.0f;
    if (h_birth >= 0.999f) return inten;                  /* made at full health: nothing to heal back to */
    rec = (h_now - h_birth) / (1.0f - h_birth);
    if (rec < 0.0f) rec = 0.0f;
    if (rec > 1.0f) rec = 1.0f;
    return inten * (1.0f - fade * rec);
}

static float klcf_age(unsigned int now, unsigned int birth, int n)   /* 32-bit like GetTickCount, also on LP64 */
{
    unsigned int ms;
    if (n <= 0) return 0.0f;
    ms = now - birth;                                     /* wraps like GetTickCount */
    if (ms > 60000u) ms = 60000u;
    return 1.0f + (float)ms / 1000.0f;
}

#endif /* KLCRACKFX_LOGIC_H */
