/* klucchide_logic.h - the PURE parts of klucchide.c ([UccHide]: the Undercover Cop stays hidden until he reveals himself, host-authoritative).
 * No game reads here: klucchide.c feeds it the numbers it read; klucchide_test.c checks it off-game (tools/run_harness_linux.sh klucchide_test).
 * (klucc.c / klucc_logic.h are the separate [Ucc] suspicion pings / accuse key module; prefixes kluc_ there, klucc_ here.)
 * Included by klhook.c BEFORE klhud_values.c (the crew rows and kllocname.c ask it), so it holds the shared state too.
 *
 * THE STATE (one per peer; the HOST's is the truth, a client mirrors what the host sends):
 *   per client index i (the crew index the score flags and the stock list use, 0 .. 15):
 *     used[i], flags[i]  the online score flag dword [[rules+0x2c]+0x98+4i] as last read (0x80 = the Undercover Cop: set by the host's
 *                        round start 0x40f870 -> 0x601fd0(score, i, 0x80), replicated with the score object)
 *     revealed bit i     the UCC pressed his reveal key and the host accepted it. ONLY the key reveals (owner 2026-10-26 decision 1).
 *   epoch                the host's round number of this state: +1 at every new round the host sees; a client takes the newest epoch.
 *   me                   this peer's own client index (-1 = not known).
 * Payloads on klnetchan.c's shared channel (re/hook_netchannel.md):
 *   type UHID, host  -> all   "S;<epoch>;<ucc mask hex>;<revealed mask hex>"   (accepted only from a sender saying role 2)
 *   type UREV, client -> host "R;<epoch>;<client index>"                       (the host checks the index really has flag 0x80) */
#ifndef KLUCCHIDE_LOGIC_H
#define KLUCCHIDE_LOGIC_H

#define KLUCC_N          16
#define KLUCC_F_POLICE   0x8u
#define KLUCC_F_UCC      0x80u
#define KLUCC_F_DIRTY    0x1000u
#define KLUCC_F_UCC2     0x40000u        /* the stock list's second UCC look (state 4); meaning not read: stripped with 0x80 */
#define KLUCC_BOUNTY_STOCK 100000        /* [tuning+0x674] from the ctor 0x524050 (re/fed_kit.md 10.1) */
#define KLUCC_MIRROR_KEEP_MS 3000        /* a client that sees a new round keeps a host state adopted this recently (it is already the new round's) */

struct klucc_state {
    int n;                               /* client indices read (<= KLUCC_N) */
    unsigned char used[KLUCC_N];
    unsigned long flags[KLUCC_N];
    unsigned long revealed;              /* bit i = client i revealed */
    unsigned long epoch;                 /* host: its round counter; client: the epoch of the mirrored state */
    unsigned long min_epoch;             /* client: the lowest epoch it accepts now */
    unsigned long adopted_at;            /* client: tick of the last adopted host state (0 = never) */
    int me;                              /* own client index, -1 unknown */
    int host;                            /* 1 = this peer keeps the truth */
    int on;                              /* 1 = an Undercover Cop round is being watched (klucc.c sets it) */
};

/* client index i is an Undercover Cop (score flag 0x80) */
static int klucc_is_ucc(const struct klucc_state *s, int i)
{
    return s && i >= 0 && i < s->n && i < KLUCC_N && s->used[i] && (s->flags[i] & KLUCC_F_UCC) != 0;
}

static unsigned long klucc_ucc_mask(const struct klucc_state *s)
{
    unsigned long m = 0; int i;
    for (i = 0; s && i < s->n && i < KLUCC_N; i++) if (klucc_is_ucc(s, i)) m |= 1ul << i;
    return m;
}

/* i is an Undercover Cop who has NOT revealed himself */
static int klucc_hidden(const struct klucc_state *s, int i)
{
    return klucc_is_ucc(s, i) && !(s->revealed & (1ul << i));
}

static int klucc_any_hidden(const struct klucc_state *s)
{
    int i;
    if (!s || !s->on) return 0;
    for (i = 0; i < s->n && i < KLUCC_N; i++) if (klucc_hidden(s, i)) return 1;
    return 0;
}

/* May VIEWER (a client index, -1 = unknown) see that TARGET is an Undercover Cop? Yes when he revealed himself, when the viewer is he,
   when the viewer is on the police side (police 0x8 / dirty cop 0x1000) or is himself an Undercover Cop (owner decision 4: two UCCs know
   each other). An unknown viewer sees nothing (the safe side: a heister must not learn it from a failed read). */
static int klucc_sees(const struct klucc_state *s, int viewer, int target)
{
    unsigned long vf;
    if (!klucc_is_ucc(s, target)) return 1;                     /* nothing to hide */
    if (s->revealed & (1ul << target)) return 1;
    if (viewer < 0 || viewer >= s->n || viewer >= KLUCC_N || !s->used[viewer]) return 0;
    if (viewer == target) return 1;
    vf = s->flags[viewer];
    return (vf & (KLUCC_F_POLICE | KLUCC_F_DIRTY | KLUCC_F_UCC)) != 0;
}

/* the flag dword of TARGET as VIEWER's crew list may show it: 0x80 (and 0x40000) taken out while the viewer may not see it.
   0xffffffff (slot 114's 'no such client') and dwords without 0x80 pass unchanged. */
static unsigned long klucc_view(const struct klucc_state *s, int viewer, int target, unsigned long f)
{
    if (f == 0xfffffffful || !(f & KLUCC_F_UCC) || !s || !s->on) return f;
    if (klucc_sees(s, viewer, target)) return f;
    return f & ~(KLUCC_F_UCC | KLUCC_F_UCC2);
}

/* the reward a criminal gets for killing an Undercover Cop ([tuning+0x674]). It is ONE int for the whole round, not per UCC:
   'hidden' while any UCC of the round is still hidden, 'revealed' once every UCC has revealed himself (owner decision 3: 200,000 / 400,000).
   GUESS (two UCCs, one revealed): the lower number until both have revealed. */
static long klucc_bounty(const struct klucc_state *s, long hidden, long revealed)
{
    return klucc_any_hidden(s) ? hidden : revealed;
}

/* HOST: client i asks to reveal. -> 1 when the state changed (i is a UCC and was hidden), 0 otherwise (not a UCC, already revealed,
   a stale epoch, out of range). */
static int klucc_host_reveal(struct klucc_state *s, unsigned long epoch, int i)
{
    if (!s || !s->host || epoch != s->epoch || !klucc_hidden(s, i)) return 0;
    s->revealed |= 1ul << i;
    return 1;
}

/* HOST: a new round. Every UCC is hidden again, the epoch moves on. */
static void klucc_host_new_round(struct klucc_state *s)
{
    s->revealed = 0; s->epoch++;
}

/* CLIENT: a new round seen locally. The mirror is cleared unless a host state was adopted in the last KLUCC_MIRROR_KEEP_MS (the host
   saw the round first and its packet is already the new round's); a cleared mirror then accepts only a NEWER epoch than it held. */
static void klucc_client_new_round(struct klucc_state *s, unsigned long now)
{
    if (s->adopted_at && now - s->adopted_at < KLUCC_MIRROR_KEEP_MS) return;
    s->revealed = 0;
    s->min_epoch = s->epoch + 1;
}

/* CLIENT: the host's state arrived. -> 1 when adopted. An epoch below min_epoch or below the one held is refused; a revealed bit only
   counts for an index this peer itself reads as a UCC (a stale bit cannot out a heister). */
static int klucc_client_apply(struct klucc_state *s, unsigned long epoch, unsigned long ucc, unsigned long rev, unsigned long now)
{
    if (!s || s->host || epoch < s->min_epoch || epoch < s->epoch) return 0;
    (void)ucc;                                                   /* the host's view of who is UCC: logged by klucc.c, the local flags decide */
    s->epoch = epoch;
    s->revealed = rev & klucc_ucc_mask(s);
    s->adopted_at = now ? now : 1;
    return 1;
}

/* ---- packets ---- */
static int klucc_fmt_state(char *o, int cap, unsigned long epoch, unsigned long ucc, unsigned long rev)
{
    return snprintf(o, (size_t)cap, "S;%lu;%lx;%lx", epoch, ucc, rev);
}

static int klucc_fmt_req(char *o, int cap, unsigned long epoch, int i)
{
    return snprintf(o, (size_t)cap, "R;%lu;%d", epoch, i);
}

/* -> 'S' (state: *epoch *a = ucc mask, *b = revealed mask), 'R' (request: *epoch, *a = client index), 0 = not ours / malformed */
static int klucc_parse(const char *p, unsigned long *epoch, unsigned long *a, unsigned long *b)
{
    int used = 0, idx = -1;
    if (!p) return 0;
    if (p[0] == 'S' && p[1] == ';') {
        if (sscanf(p + 2, "%lu;%lx;%lx%n", epoch, a, b, &used) != 3 || p[2 + used]) return 0;
        if (*a >> KLUCC_N || *b >> KLUCC_N) return 0;
        return 'S';
    }
    if (p[0] == 'R' && p[1] == ';') {
        if (sscanf(p + 2, "%lu;%d%n", epoch, &idx, &used) != 2 || p[2 + used] || idx < 0 || idx >= KLUCC_N) return 0;
        *a = (unsigned long)idx; *b = 0;
        return 'R';
    }
    return 0;
}

/* ---- the kill-feed route (kllocname.c's LOC lookup): -> the key to look up instead, or 0 = keep the game's key.
   FA_Killed_UCC (the full path 'AllLevels/Interface/Online/Announcements/FA_Killed_UCC', 0x463cd9) -> the same path with FA_Killed_Merc
   (both lines take only {Reward1}: 0x463cc9 / 0x463eaa); FA_NoFriendlyFireUCC (folder 'AllLevels/Interface/Online', 0x6ffecf) ->
   FA_NoFriendlyFire. out needs room for the key + 1. */
static const char *klucc_route_key(const char *key, char *out, int cap)
{
    static const char ucc[] = "FA_Killed_UCC", merc[] = "FA_Killed_Merc", ff[] = "FA_NoFriendlyFireUCC";
    int n, lu = (int)sizeof ucc - 1, lf = (int)sizeof ff - 1;
    if (!key) return 0;
    n = (int)strlen(key);
    if (n >= lf && !strcmp(key + n - lf, ff) && (n == lf || key[n - lf - 1] == '/')) {
        if (n + 1 > cap) return 0;
        memcpy(out, key, (size_t)(n - 3)); out[n - 3] = 0;       /* drop 'UCC' */
        return out;
    }
    if (n >= lu && !strcmp(key + n - lu, ucc) && (n == lu || key[n - lu - 1] == '/')) {
        if (n - lu + (int)sizeof merc > cap) return 0;
        memcpy(out, key, (size_t)(n - lu)); memcpy(out + n - lu, merc, sizeof merc);
        return out;
    }
    return 0;
}

/* the stock crew list's row-state routine 0x572050 .. 0x5721c1 (re/hud_values.md g): a slot-114 call returning inside it is the only
   one whose answer is stripped (every other caller - rewards, rules, the HUD's own readers - gets the true flags) */
static int klucc_ra_is_list(unsigned long ra, unsigned long lo, unsigned long hi) { return ra > lo && ra < hi; }

/* key edge: -> 1 on the first poll that sees the key down after it was up (and at least debounce ms after the last edge) */
struct klucc_key { int down; unsigned long at; };
static int klucc_edge(struct klucc_key *k, int down, unsigned long now, unsigned long debounce)
{
    int e = down && !k->down && (!k->at || now - k->at >= debounce);
    if (e) k->at = now ? now : 1;
    k->down = down;
    return e;
}

/* a new round, seen locally: the round clock ([rules+0x4c], seconds left) jumped UP by more than 5 s, or an index that was no UCC is
   one now (a new pick at the round start 0x40f870; a UCC LOSING the flag - dead, back as police - is no new round), or the state left
   the round window and came back */
static int klucc_round_changed(float left_was, float left_now, unsigned long ucc_was, unsigned long ucc_now, int window_was, int window_now)
{
    if (window_now && !window_was) return 1;
    if (ucc_now & ~ucc_was) return 1;
    return left_now == left_now && left_was == left_was && left_now > left_was + 5.0f;
}

/* ---- this peer's state: klucchide.c fills it, the crew rows (klhud.c) and the LOC lookup (kllocname.c) read it ---- */
static struct klucc_state klucc_st = { 0, { 0 }, { 0 }, 0, 0, 0, 0, -1, 0, 0 };
static int klucc_hud_on, klucc_feed_on;          /* [UCC] Rows / Feed, set by klucc_init only when [UccHide] Enable=1 */

/* our online crew rows: the flag dword of client TARGET as this peer may show it (VIEWER = the row list's own index when klucchide.c does
   not know this peer's client index) */
static unsigned long klucc_hud_flags(unsigned long f, int viewer, int target)
{
    if (!klucc_hud_on || !klucc_st.on) return f;
    return klucc_view(&klucc_st, klucc_st.me >= 0 ? klucc_st.me : viewer, target, f);
}

#endif /* KLUCCHIDE_LOGIC_H */
