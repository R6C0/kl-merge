/* klcamprevive_logic.h - pure logic of klcamprevive.c (no windows.h): the wounded-merc timing and decision rules.
 * Ported from luvsic's a-newer-perspective loader/revive.inc @32aa649 (in contribution with luvsic).
 * Test: klcamprevive_test.c.  Every constant below is READ from revive.inc (line given) unless marked GUESS.
 */
#ifndef KLCAMPREVIVE_LOGIC_H
#define KLCAMPREVIVE_LOGIC_H
#include <string.h>

enum { KCV_NORMAL = 0, KCV_PENDING, KCV_DOWN, KCV_GETUP, KCV_DEAD, KCV_WSTAND, KCV_EXCL };      /* revive.inc 180 RS_NAME */
enum { KCV_G_OK = 0, KCV_G_NOTASK, KCV_G_ROOM, KCV_G_VEHICLE, KCV_G_ISDOWN, KCV_G_DYING, KCV_G_REFUSED, KCV_G_NOSTART };  /* RG_* (names READ 185) */

#define KCV_MASK        0x4000      /* revive.inc 164: bit set on the body's [+0x54]->+0x3a word while down */
#define KCV_RANGE       200.0f      /* heal prompt range (revive.inc 199 default) */
#define KCV_MAXDY       50.0f
#define KCV_HPFLOOR     0.25f       /* HP floor x max (199) */
#define KCV_BACKOFF0    10000       /* ms, first back-off after a refused down (READ summary of 724-790) */
#define KCV_BACKOFF_MAX 160000

/* bleed-out seconds by difficulty 0..3 = 60/45/30/30 (199 default {60,45,30,30}); out of range -> the hardest */
static int kcv_bleed_sec(int difficulty)
{
    static const int t[4] = { 60, 45, 30, 30 };
    if (difficulty < 0 || difficulty > 3) return 30;
    return t[difficulty];
}

/* deadline in game ms from the moment a merc goes down (T in ms) */
static int kcv_deadline(int T, int difficulty) { return T + 1000 * kcv_bleed_sec(difficulty); }

/* the back-off after the n-th refused down (n from 0): 10 s, doubling, capped at 160 s */
static int kcv_backoff(int n)
{
    int v = KCV_BACKOFF0, i;
    for (i = 0; i < n && v < KCV_BACKOFF_MAX; i++) v *= 2;
    return v > KCV_BACKOFF_MAX ? KCV_BACKOFF_MAX : v;
}

/* the HP floor test: hp <= floor * max and max > 0 */
static int kcv_hp_at_floor(float hp, float mx) { return mx > 0.0f && hp <= KCV_HPFLOOR * mx + 0.0001f; }

/* a refused down gate -> falls back to the standing wounded state (revive.inc 749): everything but ISDOWN / DYING / VEHICLE */
static int kcv_gate_wstand(int g) { return g != KCV_G_ISDOWN && g != KCV_G_DYING && g != KCV_G_VEHICLE; }

/* is the heal prompt shown: player free, in range and not above maxdy, merc in the DOWN state */
static int kcv_prompt_ok(int merc_state, float dist, float dy)
{
    if (merc_state != KCV_DOWN) return 0;
    if (dy < 0) dy = -dy;
    return dist <= KCV_RANGE && dy <= KCV_MAXDY;
}

/* has the bleed deadline run out (game clock T, ms)? 0 deadline = not set */
static int kcv_bled_out(int T, int deadline) { return deadline > 0 && T - deadline >= 0; }

/* the wounded state a merc moves to for what the observation saw:
 *   life 1 + down flag (+0x64c) 1 + DND task current -> DOWN ; life != 1 -> DEAD ; otherwise NORMAL (READ 417-419, 1336-) */
static int kcv_observe_state(int life, int down_flag, int dnd_current)
{
    if (life != 1) return KCV_DEAD;
    if (down_flag == 1 && dnd_current) return KCV_DOWN;
    return KCV_NORMAL;
}

/* campaign gate + own enable + not owned by an FA module on this level */
static int kcv_idle(int campaign_active, int enable, int fa_down_modules_on)
{
    return !campaign_active || !enable || fa_down_modules_on;
}

/* merc id (script +0x6e8) valid for a campaign merc: 1..13 (revive.inc / squad.inc sq_merc_body) */
static int kcv_merc_id_ok(int m) { return m >= 1 && m <= 13; }

#endif
