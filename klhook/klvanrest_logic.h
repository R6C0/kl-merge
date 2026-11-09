/* klvanrest_logic.h - [BotFill] OnlineVanRest, the PURE part (no windows.h, no game memory). Included by klbotfill.c and klvanrest_test.c.
   Problem (DM09 terminal variant): the van group is translated, so before the van is called its vehicle node reads the translated rest place, not (0,0,0). The old
   "not here" guard (all |coord| <= 1) never fires and online bots walk to the rest place (87 m off). OnlineVanRest = "x y z": a van node within KVR_NEAR_CM of that
   point is "not here" too. Key absent / unparsable = the old guard exactly. (recommended on for a map whose van group is moved; GUESS: 100 cm is wide enough for a
   resting node, narrow enough that a driven-in van never matches) */
#ifndef KLVANREST_LOGIC_H
#define KLVANREST_LOGIC_H
#include <stdio.h>
#include <math.h>
#define KVR_NEAR_CM 100.0f

/* "x y z" (also with , ; ( ) as separators) -> out; returns 1 on success, 0 = no rest point configured (old behaviour) */
static int kvr_parse(const char *s, float out[3])
{
    char buf[120]; int i; float x, y, z;
    if (!s) return 0;
    for (i = 0; s[i] && i < (int)sizeof buf - 1; i++) buf[i] = (s[i] == ',' || s[i] == ';' || s[i] == '(' || s[i] == ')') ? ' ' : s[i];
    buf[i] = 0;
    if (sscanf(buf, "%f %f %f", &x, &y, &z) != 3) return 0;
    if (!(fabsf(x) < 1e7f && fabsf(y) < 1e7f && fabsf(z) < 1e7f)) return 0;      /* also rejects NaN / inf */
    out[0] = x; out[1] = y; out[2] = z; return 1;
}

/* 1 = this van node place means "not here / not called yet". restOn = a rest point is configured. restOn 0: only the origin test (the old guard, byte for byte). */
static int kvr_not_here(const float *p, int restOn, const float *rest)
{
    if (!(fabs(p[0]) > 1 || fabs(p[1]) > 1 || fabs(p[2]) > 1)) return 1;      /* the old guard */
    if (restOn && rest) {
        float dx = p[0] - rest[0], dy = p[1] - rest[1], dz = p[2] - rest[2];
        if (dx * dx + dy * dy + dz * dz <= KVR_NEAR_CM * KVR_NEAR_CM) return 1;
    }
    return 0;
}
#endif
