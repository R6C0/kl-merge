/* kldown_mirror_logic.h - the PURE parts of kldown_mirror.c (online flop mirror, re/down_mirror.md): the two message payloads,
 * the hash the message-less fallback draws with, the weighted pick (the same walk as kld_mix_next in kldown.c), the follow-speed
 * law of the get-up sync and the pool-sharing verdict. No game reads: kldown_mirror.c feeds it numbers. Checked off-game by
 * kldown_mirror_test.c (cl /nologo /W3 kldown_mirror_test.c).
 *
 * KDFL (announce, the victim -> everybody, while he is UP):  "1;<mode>;<sheet>;<n>;<lastgroup>;<mask hex>"
 *   mode 0 = nothing armed (disarm), 1 = Flop=1 belly, 3 = Flop=3 list entry `sheet` (sheet number of kld_md: 41 7 13 12 9 10 25 42 43)
 *   n    = the number of the knock-down the clip is for (his kld_s.downs + 1)
 *   group = the group (1..6) of the announced clip (the replica keeps it as 'played last' for its own hash pick), mask = bit k set when kld_md[k] is in his list (log only)
 * KDSY (sync, the victim -> everybody, while he LIES after the landing): "1;<n>;<frame x10>;<rate x100>;<to>"
 *   rate = the channel's fps / 25 (his mash speed), to = the clip's last frame. */
#ifndef KLDOWN_MIRROR_LOGIC_H
#define KLDOWN_MIRROR_LOGIC_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KDM_MAXN    9999
#define KDM_SALT    0x4b4cu                /* 'KL': the hash's constant - every machine must use the same one */

struct kdm_fl { int mode, sheet, n, group; unsigned mask; };
struct kdm_sy { int n; float frame, rate; int to; };

static int kdm_fmt_fl(char *out, int cap, int mode, int sheet, int n, int group, unsigned mask)
{
    int k = snprintf(out, cap, "1;%d;%d;%d;%d;%x", mode, sheet, n, group, mask);
    return k > 0 && k < cap ? k : 0;
}

/* strict: six fields, version 1, every number in range; anything else -> 0 */
static int kdm_parse_fl(const char *s, struct kdm_fl *f)
{
    int v = 0, mode = 0, sheet = 0, n = 0, group = 0; unsigned mask = 0; int used = 0;
    if (!s || sscanf(s, "%d;%d;%d;%d;%d;%x%n", &v, &mode, &sheet, &n, &group, &mask, &used) != 6 || s[used] != 0 || v != 1) return 0;
    if (mode != 0 && mode != 1 && mode != 3) return 0;
    if (sheet < 0 || sheet > 99 || n < 0 || n > KDM_MAXN || group < 0 || group > 9 || mask > 0x1ffu) return 0;
    if (mode == 3 && sheet == 0) return 0;
    f->mode = mode; f->sheet = sheet; f->n = n; f->group = group; f->mask = mask;
    return 1;
}

static int kdm_fmt_sy(char *out, int cap, int n, float frame, float rate, int to)
{
    int k = snprintf(out, cap, "1;%d;%d;%d;%d", n, (int)(frame * 10.0f + 0.5f), (int)(rate * 100.0f + 0.5f), to);
    return k > 0 && k < cap ? k : 0;
}

static int kdm_parse_sy(const char *s, struct kdm_sy *y)
{
    int v = 0, n = 0, f10 = 0, r100 = 0, to = 0, used = 0;
    if (!s || sscanf(s, "%d;%d;%d;%d;%d%n", &v, &n, &f10, &r100, &to, &used) != 5 || s[used] != 0 || v != 1) return 0;
    if (n < 0 || n > KDM_MAXN || f10 < 0 || f10 > 60000 || r100 < 5 || r100 > 1000 || to < 2 || to > 5000) return 0;
    y->n = n; y->frame = f10 / 10.0f; y->rate = r100 / 100.0f; y->to = to;
    return 1;
}

/* the same hash on every machine: (the table index of the one who falls, the number of the fall, the salt) */
static unsigned kdm_hash(int idx, int n, unsigned salt)
{
    unsigned h = (unsigned)idx * 0x9E3779B1u ^ (unsigned)n * 0x85EBCA6Bu ^ salt * 0xC2B2AE35u;
    h ^= h >> 15; h *= 0x2C1B3C6Du; h ^= h >> 12; h *= 0x297A2D39u; h ^= h >> 15;
    return h;
}

/* r in [0, sum) from a hash - the same 24-bit scaling kld_mix_next uses on its xorshift */
static float kdm_hash_r(unsigned h, float sum) { return (float)(h >> 8) / 16777216.0f * sum; }

/* kld_mix_next's walk: `others` = some entry is not of the last group; the entries of the last group are skipped then; r is walked down
   by the weights. w / grp are per list entry. -> the index picked, -1 = none; *sumOut = the sum r was scaled by (so a caller can draw r itself) */
static int kdm_pick_r(const float *w, const int *grp, int cnt, int lastgroup, float r, float *sumOut)
{
    int i, others = 0, pick = -1; float sum = 0;
    for (i = 0; i < cnt; i++) if (grp[i] != lastgroup) others++;
    for (i = 0; i < cnt; i++) if (!others || grp[i] != lastgroup) sum += w[i];
    if (sumOut) *sumOut = sum;
    for (i = 0; i < cnt; i++) {
        if (others && grp[i] == lastgroup) continue;
        pick = i;
        if ((r -= w[i]) < 0) break;
    }
    return pick;
}

static int kdm_det_pick(const float *w, const int *grp, int cnt, int lastgroup, unsigned h)
{
    float sum = 0;
    kdm_pick_r(w, grp, cnt, lastgroup, 0.0f, &sum);
    return kdm_pick_r(w, grp, cnt, lastgroup, kdm_hash_r(h, sum), 0);
}

/* the speed the replica's channel is set to: the master's rate x 25 frames a second plus a pull of `k` per frame of error (target - frame), clamped
   to [0.5 x, 2 x] of the master's speed and the channel's own 0.5 .. 250 bound */
static float kdm_fps(float rate, float frame, float target, float k)
{
    float base = rate * 25.0f, f = base + k * (target - frame), lo = base * 0.5f, hi = base * 2.0f;
    if (f < lo) f = lo; if (f > hi) f = hi;
    if (f < 0.5f) f = 0.5f; if (f > 250.0f) f = 250.0f;
    return f;
}

/* pool sharing: how many of the other bodies wear this animation pool. pools[] = every body's [+0x78] (the session table's and the game data's
   places, a body once), self = the index to leave out. 0 = exclusive (the replica's pool may be written), > 0 = shared (REFUSE). */
static int kdm_pool_users(const unsigned *pools, int n, int self)
{
    int i, c = 0;
    if (self < 0 || self >= n || !pools[self]) return -1;
    for (i = 0; i < n; i++) if (i != self && pools[i] == pools[self]) c++;
    return c;
}

#endif
