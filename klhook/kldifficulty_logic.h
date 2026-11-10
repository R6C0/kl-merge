/*
 * kldifficulty_logic.h - PURE part of [Difficulty] (2026-11-10, owner: "make sure theres the difficulty slider for the ai heisters n how much damage
 * they take n etc" and "they just absorb bullets and same as you"). No windows.h; tested off game by kldifficulty_test.c.
 *
 * Two steppers over klbalance.c's per-level damage record (klr.f[]): the factor of a bullet is stored per direction, so the "slider" is a table of steps.
 *   AI HEISTERS (what the police do to an AI heister, and what an AI heister does to the police)
 *       step 0 STOCK    CopToCrew 0.01  CrewToCop 3.0   (the stock Arcade level-1 row: a police bullet costs 1 percent: the bullet sponge)
 *       step 1 TOUGH    0.25  2.0
 *       step 2 FAIR     0.70  1.0   (recommended on: a police bullet hurts an AI heister as much as it hurts YOU at CopToYou 0.7; CrewToCop 1.0 = what the live ini had)
 *       step 3 FRAGILE  1.20  0.8
 *   YOUR DAMAGE TAKEN (police -> you, AI heister -> you)
 *       step 0 STOCK    CopToYou 0.10 CrewToYou 0.10
 *       step 1 EASY     0.40  0.35
 *       step 2 NORMAL   0.70  0.60  (= the live ini of 2026-11-10: unchanged)
 *       step 3 HARD     1.00  0.85
 *       step 4 BRUTAL   1.40  1.20
 * The numbers are written as [Balance] keys (CopToCrew, CrewToCop, CopToYou, CrewToYou), so the file stays readable without the hook. The step itself is
 * also kept in [Difficulty] Ai= / You= (the Mod Options tool and the next start read them).
 */
#ifndef KLDIFFICULTY_LOGIC_H
#define KLDIFFICULTY_LOGIC_H
#include <stdio.h>
#include <string.h>

#define KDF_AI_N  4
#define KDF_YOU_N 5
#define KDF_AI_DEF  2
#define KDF_YOU_DEF 2

static const struct kdf_ai_def { const char *name; float taken, dealt; } kdf_ai[KDF_AI_N] = {
    { "STOCK", 0.01f, 3.0f }, { "TOUGH", 0.25f, 2.0f }, { "FAIR", 0.70f, 1.0f }, { "FRAGILE", 1.20f, 0.8f },
};
static const struct kdf_you_def { const char *name; float cop, crew; } kdf_you[KDF_YOU_N] = {
    { "STOCK", 0.10f, 0.10f }, { "EASY", 0.40f, 0.35f }, { "NORMAL", 0.70f, 0.60f }, { "HARD", 1.00f, 0.85f }, { "BRUTAL", 1.40f, 1.20f },
};

/* klr.f[] order: 0 CopToCrew, 1 CrewToCop, 2 CopToYou, 3 YouToCop, 4 CrewToYou, 5 YouToCrew (klbalance.c klr_key) */
#define KDF_NF 6

static int kdf_clamp(int v, int n) { return v < 0 ? 0 : v >= n ? n - 1 : v; }
static int kdf_close(float a, float b) { float d = a - b; return d < 0.0005f && d > -0.0005f; }

/* write the step's factors into f[6]; only the four it owns, the rest (YouToCop, YouToCrew) stay. step < 0 = leave that half alone. */
static void kdf_apply(float f[KDF_NF], int ai, int you)
{
    if (ai >= 0)  { ai = kdf_clamp(ai, KDF_AI_N);    f[0] = kdf_ai[ai].taken; f[1] = kdf_ai[ai].dealt; }
    if (you >= 0) { you = kdf_clamp(you, KDF_YOU_N); f[2] = kdf_you[you].cop; f[4] = kdf_you[you].crew; }
}
/* which step the numbers are, -1 = a custom set (hand-edited ini) */
static int kdf_ai_of(float taken, float dealt)
{
    int i; for (i = 0; i < KDF_AI_N; i++) if (kdf_close(taken, kdf_ai[i].taken) && kdf_close(dealt, kdf_ai[i].dealt)) return i;
    return -1;
}
static int kdf_you_of(float cop, float crew)
{
    int i; for (i = 0; i < KDF_YOU_N; i++) if (kdf_close(cop, kdf_you[i].cop) && kdf_close(crew, kdf_you[i].crew)) return i;
    return -1;
}
/* the next step: dir +1 / -1, wraps; from a custom set (-1) the first press goes to the first step (+1) or the last (-1) */
static int kdf_next(int cur, int n, int dir)
{
    if (cur < 0) return dir < 0 ? n - 1 : 0;
    return (cur + (dir < 0 ? n - 1 : 1)) % n;
}
/* the ini text of one number: always '%.2f' (klr_inif reads it with atof) */
static void kdf_num(char *o, size_t cap, float v) { snprintf(o, cap, "%.2f", v); }

/* the announcement line (the FA announcement element takes ~40 characters comfortably; GUESS: the width, as klmodestab's 60) */
static void kdf_say_ai(int step, char *o, size_t cap)
{
    step = kdf_clamp(step, KDF_AI_N);
    snprintf(o, cap, "AI HEISTERS %s: hit x%.2f, deal x%.1f", kdf_ai[step].name, kdf_ai[step].taken, kdf_ai[step].dealt);
}
static void kdf_say_you(int step, char *o, size_t cap)
{
    step = kdf_clamp(step, KDF_YOU_N);
    snprintf(o, cap, "YOUR DAMAGE %s: police x%.2f, crew x%.2f", kdf_you[step].name, kdf_you[step].cop, kdf_you[step].crew);
}
/* [Difficulty] Ai= / You= as read (default -1 when absent): -1 stays absent, anything else out of range is refused (-2) */
static int kdf_read_step(int v, int n) { return v == -1 ? -1 : (v < 0 || v >= n) ? -2 : v; }

#endif
