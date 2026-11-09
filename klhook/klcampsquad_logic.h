/* klcampsquad_logic.h - the PURE parts of klcampsquad.c ([CampSquad]: crew orders on the Dead Men campaign levels).
 * Ported from luvsic's a-newer-perspective loader/squad.inc @32aa649 (in contribution with luvsic): the tap/hold key machine
 * (his sq_keys, DM 0x638ea0), the M01 refusal rule (sq_refuse_rule), the recruit=start classifier (sq_recruit_start),
 * the config clamps (sq_cfg_poll) and the critical=clear decision (sq_crit_pass). No game reads here; klcampsquad.c feeds it
 * numbers it read. Off-game test: klcampsquad_test.c. Times in ms (GetTickCount). */
#ifndef KLCAMPSQUAD_LOGIC_H
#define KLCAMPSQUAD_LOGIC_H

#define KLCSQ_TAP_MS   250      /* READ squad.inc:145 SQ_TAP_T 256 engine units (1024/s) = 0.25 s: a press shorter than this is a TAP, longer a HOLD */
enum { KLCSQ_REC_OFF = 0, KLCSQ_REC_START = 1, KLCSQ_REC_ALWAYS = 2 };

/* ---- config clamps (READ sq_cfg_poll) ---- */
static float klcsq_clamp_attack_t(float t) { return (t > 0.0f && t < 120.0f) ? t : 5.0f; }                 /* NaN fails both tests: 5 s */
static int klcsq_clamp_settle_ms(float s) { return (s >= 0.0f && s <= 30.0f) ? (int)(s * 1000.0f) : 2000; }
/* recruit= word or number: off | start | always; 0 = off, 1 = always (the old behaviour), 2+ = start (READ). -1 = unknown word (keep the old value) */
static int klcsq_recmode(const char *v)
{
    if (!v) return -1;
    if (!strcmp(v, "off")) return KLCSQ_REC_OFF;
    if (!strcmp(v, "start")) return KLCSQ_REC_START;
    if (!strcmp(v, "always")) return KLCSQ_REC_ALWAYS;
    if (v[0] >= '0' && v[0] <= '9') { int r = atoi(v); return r <= 0 ? KLCSQ_REC_OFF : r == 1 ? KLCSQ_REC_ALWAYS : KLCSQ_REC_START; }
    return -1;
}

/* ---- the M01 refusal rule (READ sq_refuse_rule): refuse -1 = auto (only on M01), 0 never, 1 always. key = "m01\m01_main" form. ---- */
static int klcsq_is_m01(const char *key) { return key && key[0] == 'm' && key[1] == '0' && key[2] == '1' && (key[3] == 0x5c || (key[3] >= 'a' && key[3] <= 'z')); }
static int klcsq_refuse_rule(int refuse, const char *key) { return refuse == 1 || (refuse < 0 && klcsq_is_m01(key)); }

/* ---- tap / hold machine (READ sq_keys): result 0 nothing, 1 HOLD just fired (key still down), 2 TAP (released before the hold time) ---- */
struct klcsq_k { int down, fired; unsigned long t0; };
static int klcsq_key_step(struct klcsq_k *k, int d, unsigned long now)
{
    if (d && !k->down) { k->down = 1; k->t0 = now; k->fired = 0; return 0; }
    if (d && k->down && !k->fired && now - k->t0 >= KLCSQ_TAP_MS) { k->fired = 1; return 1; }
    if (!d && k->down) { int tap = !k->fired; k->down = 0; return tap ? 2 : 0; }
    return 0;
}
/* an edge key (next / prev): fires once per press */
static int klcsq_edge(int *was, int d) { int f = d && !*was; *was = d ? 1 : 0; return f; }

/* ---- recruit classifier (READ sq_recruit_start / sq_recruit_scan) ----
   what to do with ONE merc that is not yet a receiver. */
enum { KLCSQ_R_SKIP = 0,       /* unable / disabled / nothing to do */
       KLCSQ_R_LEAVE,          /* held by a level squad: the level's merc, never recruited (recruit=start) */
       KLCSQ_R_ADOPT,          /* held by a level squad and no owner: only +0x69c := P (data write), adopt=1 */
       KLCSQ_R_SETTLE,         /* +0x4f4 changed less than settle ms ago: wait */
       KLCSQ_R_WAIT,           /* gate closed (cutscene / blocked input) or the player squad runs a mini-cutscene */
       KLCSQ_R_ADDRECV,        /* in the player squad but no receiver: add to the receiver list (data, as 0x6213b0's tail) */
       KLCSQ_R_RECRUIT,        /* call 0x908040 */
       KLCSQ_R_GIVEUP };       /* 8 tries this level */
struct klcsq_rec_in {
    int mode;                  /* KLCSQ_REC_* */
    int able, nodeOff;         /* body+0x576 == 1; node+0x3c bit 0x400 */
    unsigned long q, sq, own, P;   /* script+0x4f4, the player squad, script+0x69c, the player */
    long sinceQ;               /* ms since +0x4f4 last changed */
    int settleMs, adopt, gateClosed, squadBusy; /* squadBusy: the player squad's behaviour is a mini-cutscene */
    int tries, sinceTry;       /* recruits tried this level, ms since the last try (<0 = never) */
};
static int klcsq_recruit_class(const struct klcsq_rec_in *r)
{
    if (r->mode == KLCSQ_REC_OFF) return KLCSQ_R_SKIP;
    if (!r->able || r->nodeOff) return KLCSQ_R_SKIP;
    if (r->mode == KLCSQ_REC_ALWAYS) {
        if (r->q == r->sq && r->own == r->P && r->sq) return KLCSQ_R_SKIP;             /* already his: nothing to do (READ) */
        if (r->gateClosed) return KLCSQ_R_WAIT;
        if (r->tries >= 8) return KLCSQ_R_GIVEUP;
        if (r->sinceTry >= 0 && r->sinceTry < 3000) return KLCSQ_R_SKIP;
        return KLCSQ_R_RECRUIT;
    }
    if (r->q && r->q != r->sq) return (!r->own && r->adopt) ? KLCSQ_R_ADOPT : KLCSQ_R_LEAVE;
    if (r->sinceQ < r->settleMs) return KLCSQ_R_SETTLE;
    if (r->gateClosed) return KLCSQ_R_WAIT;
    if (r->q == r->sq && r->sq && r->squadBusy) return KLCSQ_R_WAIT;
    if (r->tries >= 8) return KLCSQ_R_GIVEUP;
    if (r->sinceTry >= 0 && r->sinceTry < 3000) return KLCSQ_R_SKIP;
    if (r->q == r->sq && r->sq) return KLCSQ_R_ADDRECV;
    return KLCSQ_R_RECRUIT;                                                              /* +0x4f4 == 0: in no squad */
}

/* ---- critical=clear (READ sq_crit_pass): which flag byte to touch. The flag at script+0x513 is cleared when set; +0x512 stays. ---- */
static int klcsq_crit_needs_clear(unsigned flag513) { return flag513 != 0; }
/* a pass is due when the game-state counter changed, or once a second when any listed merc still has the flag */
static int klcsq_crit_due(int gsSeen, unsigned long gsOld, unsigned long gsNew, int anySet, unsigned long sinceLast)
{ return (gsSeen && gsOld != gsNew) || (anySet && sinceLast >= 1000); }

/* ---- the legal receiver count / list (sc+0x18 <= 16): a count outside 0..16 is a bad read ---- */
static int klcsq_nrecv(unsigned long n) { return n > 16 ? 16 : (int)n; }
/* the receiver the tap acts on: sc+0x10 points into the list (sc+0x1c..); -1 when outside it */
static int klcsq_cur_idx(unsigned long cur, unsigned long listBase, int nrecv)
{ if (cur < listBase || ((cur - listBase) & 3)) return -1; return (int)((cur - listBase) / 4) < nrecv ? (int)((cur - listBase) / 4) : -1; }

#endif
