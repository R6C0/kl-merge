/* klgrenadefx_logic.h - the PURE parts of klgrenadefx.c ([Grenade] PinSound / ThrowAnim for the Release mode): the delay clock between the
 * G press and the release, the clamps of the new keys, the clip-slot candidate list, the path join. No game reads here;
 * klgrenadefx_test.c checks it off-game. */
#ifndef KLGRENADEFX_LOGIC_H
#define KLGRENADEFX_LOGIC_H
#include <string.h>
#include <stdio.h>

#define KLGX_SLOT_PREFIX "/Weapon_Handling/Throw_Grenade/"      /* MEASURED in DD's F07 / L05 and DM01's own .ANM (366..381), see re/grenadefx_1110.md */
#define KLGX_SLOTS_DEF   "Stand_Overhand;Stand_Underhand;UB_Underhand"   /* GUESS: Stand_Overhand fits a standing G throw; the others are fallbacks when a set lacks it */

static int klgx_clampi(int v, int lo, int hi) { return v < lo ? lo : v > hi ? hi : v; }

/* [Grenade] ThrowDelayMs: press -> release. 0 = release at once (no anim wait) */
static int klgx_delay_clamp(int ms) { return klgx_clampi(ms, 0, 3000); }
/* [Grenade] ThrowAnimMs: the longest the throw clip may hold the player (cap, the clip may end sooner) */
static int klgx_cap_clamp(int ms) { return klgx_clampi(ms, 300, 4000); }

/* The press arms a pending release when there is anything to wait for (the pin sound or the clip) and a delay: due = now + delay (never 0). */
static unsigned long klgx_due(unsigned long now, int delayMs, int pin, int animStarted)
{
    unsigned long d;
    if (delayMs <= 0 || (!pin && !animStarted)) return 0;
    d = now + (unsigned long)delayMs;
    return d ? d : 1;
}
/* wrap-safe 'is it time' */
static int klgx_is_due(unsigned long now, unsigned long due) { return due != 0 && (long)(now - due) >= 0; }
/* a pending release that could not run (wrong thread context) is given up after this long past due */
static int klgx_expired(unsigned long now, unsigned long due, int graceMs) { return due != 0 && (long)(now - due) > graceMs; }

/* the n-th candidate of a ';' list into out (without the prefix); 0 when there is none */
static int klgx_nth(const char *list, int n, char *out, int cap)
{
    const char *p = list; int i = 0;
    if (!list || cap < 2) return 0;
    for (;;) {
        const char *e = strchr(p, ';'); int len = e ? (int)(e - p) : (int)strlen(p);
        while (len > 0 && (p[0] == ' ')) { p++; len--; }
        while (len > 0 && p[len - 1] == ' ') len--;
        if (len > 0) { if (i == n) { if (len >= cap) len = cap - 1; memcpy(out, p, (size_t)len); out[len] = 0; return 1; } i++; }
        if (!e) return 0;
        p = e + 1;
    }
}
/* a candidate is a bare name (Stand_Overhand) -> prefix + name; a leading '/' is a full slot path and is kept */
static int klgx_slot_path(const char *cand, char *out, int cap)
{
    if (!cand || !cand[0]) return 0;
    return snprintf(out, (size_t)cap, "%s%s", cand[0] == '/' ? "" : KLGX_SLOT_PREFIX, cand) < cap;
}
/* directory of the ini path + sub (ini 'C:\x\KLHook.ini', sub 'KLGrenade' -> 'C:\x\KLGrenade\') */
static int klgx_dir_of(const char *ini, const char *sub, char *out, int cap)
{
    const char *s = ini ? strrchr(ini, 0x5c) : 0; int n = s ? (int)(s - ini) + 1 : 0;
    if (!ini || n + (int)strlen(sub) + 2 > cap) return 0;
    memcpy(out, ini, (size_t)n); out[n] = 0; strcat(out, sub); strcat(out, "\\");
    return 1;
}
#endif
