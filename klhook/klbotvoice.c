/*
 * klbotvoice.c - [BotFill] OnlineVoice=0|1|2: the AI heisters' event lines, online (re/bot_voice_online_spec.md, "Corrected final spec").
 * Arcade speech is a local, global (2D) line: nothing in the game's own online messages carries it, so a client never hears what the host's bots "say". The HOST sees the events
 * (klbotfill.c: a bot GRABBED a stack, a bot is aboard), sends a small hook-to-hook 'KLSYV' packet (layout in klbotvoice_logic.h; UDP 27415, the KLSYL / KLSYB socket) and EVERY seat,
 * the host through the same code, plays the plain line of that bot's voice with kltalk.c's klk_say (speaker -6, a plain flag-0 line: it needs no crew record).
 * Part of KLHook (included by klhook.c AFTER klsync.c, klbotfill.c, kltalk.c, klcrewlook.c; SHIP and TEST alike). Off unless [BotFill] OnlineVoice=1 (or 2).
 * Mode 0 = off. Mode 2 = LOG ONLY on both seats: the host logs "botvoice: DRY would send event E digit D key K" and sends NO packet, calls nothing; a client that happens to receive a
 * KLSYV logs it and does not play. Mode 1 = send + play.
 * Needs [Voice] Enable=1, Online=1, OnlineTalk=1, OnlineTalkNoScore=1 (klk_say's online gate: [rules+0x2c] must be non-null) and [BotFill] OnlineLooks=1 (the digit table the client
 * validates the digit against; with OnlineLooks off only the range 2..8 is checked). No .text patch, no game state written. Game routines are called from the game's thread only.
 *
 * v1 EVENTS: 1 = loot grab (host site: klbotfill.c, the GRABBED line), 2 = boarded / escaped (host site: the phase-3 loop before the bank book-keeping). Down / death / spotted-cops: none exist in FA.
 * KEYS (GUESS, every one): the stock per-character leaf is K_C<n> with n = digit (spec: table byte = digit - 1, leaf K_C(byte + 1)), K being the group's key. The templates below use %L (level key,
 * e.g. F06) and %D (digit). The spellings are NOT confirmed (re/bots_voice.md quotes Multiplayer/F06/ReachlootArea_01_R; the jackpot / escaped spellings were never seen): override them in the
 * ini ([BotFill] OnlineVoiceKeyLoot / OnlineVoiceKeyEscape) once the first live log shows which key the game's .LOC knows (klk_entry logs "key ... is not in this level's .LOC").
 * Dead Men bodies (KLVoice/<Name>/<event>) are not handled in v1.
 * SEND SCHEDULE: each event is sent 3 times, 100 ms apart (UDP); the client drops repeats by seq. Gaps: 15 s per bot and event, 2 s between any two lines, queue count > 8: no line.
 *
 * LOG
 *   botvoice: DRY would send event E digit D key K                    host, mode 2 (also the DRY line for the host's own play)
 *   botvoice: HOST event E digit D seq S: sent (%d bytes, sendto %d) + plays   host, mode 1
 *   botvoice: HOST event E digit D: held back (<why>)                 gap / digit / state refusals (first 10 per reason class)
 *   botvoice: CLIENT rx #N seq S event E digit D T=.. from a.b.c.d: <taken | repeat | stale>   first 10 packets, then every 20th; gaps counted
 *   botvoice: HOST|CLIENT say event E digit D key K -> klk_say %d     every klk_say result
 */
#ifndef KLBOTVOICE_C
#define KLBOTVOICE_C

#include "klbotvoice_logic.h"

static struct {
    DWORD sm; int round, rxN, toldHold;
    struct { struct klbv_pk pk; int left; DWORD at; } pend[4];
    struct klbv_seqs sq; struct klbv_gaps gaps;
    DWORD escActor[16]; int role, srcSet; unsigned long srcAddr; DWORD srcOkAt; unsigned lastT; int haveT;
} klbv_t;

/* HOST seq: kept across rounds (monotonic per session, so a client that never left the state window still takes round 2's packets); zeroed only when the session object changes */
static int klbv_seq; static DWORD klbv_seqSm;
/* log throttle per reason class (0 digit, 1 rules, 2 template, 3 gap, 4 queue, 5 host hold, 6 key read, 7 host gap, 8 pin): the first 10, then every 20th, so a flood of packets does not flood the log; not cleared by klbv_reset */
static unsigned klbv_logN[16];
static int klbv_note(int cls) { unsigned n = klbv_logN[cls & 15]++; return n < 10 || n % 20 == 0; }

/* klbv_mode and klbv_tl (the key templates) are klbotfill.c's, read in klbf_init */

static const char *klbv_ev_name(int ev) { return ev == KLBV_EV_LOOT ? "loot" : ev == KLBV_EV_ESCAPE ? "escaped" : "?"; }

static void klbv_reset(void)
{
    if (!klbv_t.sm && !klbv_t.sq.have && !klbv_t.rxN && !klbv_t.pend[0].left && !klbv_t.escActor[0]) return;
    memset(&klbv_t, 0, sizeof klbv_t);
}

/* the session: role 2 host / 3 client, mode 4, state 0x13..0x1f (a round is on; the window matches klsy_tick's, so a final event at settlement is not lost). 0 = not now. */
static int klbv_round(DWORD *smOut, DWORD *roleOut)
{
    DWORD sm, role = 0, mode = 0, state = 0;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return 0;
    if (!klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)) return 0;
    if ((role != 2 && role != 3) || mode != 4 || state < 0x13 || state > 0x1f) return 0;
    *smOut = sm; *roleOut = role;
    return 1;
}

/* the speech queue count above 8 = no new line (klk_say itself refuses above 10) */
static int klbv_queue_full(void)
{
    DWORD mgr, queue, q0 = 0;
    if (!(mgr = klh_rd32((DWORD_PTR)KLH_VA(KLK_MANAGER))) || !(queue = klh_rd32(mgr + 0x974)) || !klh_rd(queue, &q0, 4)) return 1;
    return q0 > 8;
}

/* the digit is a known bot of the OnlineLooks table (when that is on); 1 = ok */
static int klbv_digit_ok(int digit)
{
    if (digit < 2 || digit > 8) return 0;
    if (klcl_on && !klcl_t.e[digit - 1].have) return 0;      /* GUESS 4 of the spec: the client's digit equals the host's for the same bot; unknown to the look table = not a bot of this round */
    return 1;
}

/* the key of (ev, digit) for this level; 0 = not readable */
static int klbv_make_key(int ev, int digit, char *key, int cap)
{
    char scene[160], lk[64];
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, lk, sizeof lk)) return 0;
    return klbv_key(key, cap, klbv_tl[ev == KLBV_EV_LOOT ? 0 : 1], lk, digit);
}

/* build the key + play it on this seat. seat = "HOST" / "CLIENT". 1 = klk_say said it. */
static int klbv_play(const char *seat, int ev, int digit, unsigned now, int check_gap)
{
    char scene[160], lk[64], key[200]; DWORD gs, rules; int r;
    if (!klbv_digit_ok(digit)) { if (klbv_note(0)) klog("botvoice: %s event %d digit %d: not played (digit not in the OnlineLooks table / range)", seat, ev, digit); return 0; }
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLW_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || !klh_scene(scene, sizeof scene) || !klh_level_key(scene, lk, sizeof lk)) {
        if (klbv_note(1)) klog("botvoice: %s event %d digit %d: not played (rules object / scene not readable)", seat, ev, digit);
        return 0;
    }
    if (!klbv_key(key, sizeof key, klbv_tl[ev == KLBV_EV_LOOT ? 0 : 1], lk, digit)) { if (klbv_note(2)) klog("botvoice: %s event %d: key template too long", seat, ev); return 0; }
    if (check_gap && !klbv_gap_ok(&klbv_t.gaps, digit, ev, now)) { if (klbv_note(3)) klog("botvoice: %s event %d digit %d key %s: held back (gap: 15 s per bot and event, 2 s between lines)", seat, ev, digit, key); return 0; }
    if (klbv_queue_full()) { if (klbv_note(4)) klog("botvoice: %s event %d digit %d key %s: held back (speech queue > 8 or unreadable)", seat, ev, digit, key); return 0; }
    r = klk_say(key, -6, 0.0f, "bot voice (OnlineVoice)", rules, scene);      /* -6 = the crew speaker object [this+0xe0] of 0x7d0e80: GUESS, unconfirmed on a client with no record */
    klog("botvoice: %s say event %d (%s) digit %d key %s -> klk_say %d", seat, ev, klbv_ev_name(ev), digit, key, r);
    return r;
}

/* HOST: a bot of slot s (klbf_ob) did event ev. Called from klbotfill.c on the game thread. */
static void klbv_event(int slot, int ev)
{
    char nm[28], dg = 0, key[200]; DWORD sm, role, a, now = GetTickCount(); int digit, i, esc;
    if (!klbv_mode || slot < 0 || slot >= KLBF_OT_BOTS || ev < 1 || ev >= KLBV_NEV) return;
    if (!klbv_round(&sm, &role) || role != 2) return;
    if (klbv_seqSm != sm) { klbv_seq = 0; klbv_seqSm = sm; }      /* seq stays monotonic across rounds of one session */
    if (klbv_t.sm != sm || klbv_t.round != (int)klbf_ot_rounds) { klbv_reset(); klbv_t.sm = sm; klbv_t.round = (int)klbf_ot_rounds; }
    klbv_t.role = 2;
    a = klbf_ob[slot].actor;
    if (!a) return;
    klbf_lk_name(a, nm, &dg); digit = dg >= '0' && dg <= '9' ? dg - '0' : 0;
    if (!klbv_digit_ok(digit)) { if (klbv_note(5)) klog("botvoice: HOST event %d slot %d: held back (group digit %d is not 2..8, or not in the OnlineLooks table)", ev, slot, digit); return; }
    esc = -1;
    if (ev == KLBV_EV_ESCAPE) {      /* boarded: once per actor and round; the actor is recorded only once the event is sent / logged (below), so a held-back bot retries on the next tick */
        for (i = 0; i < 16 && klbv_t.escActor[i] && klbv_t.escActor[i] != a; i++) ;
        if (i >= 16 || klbv_t.escActor[i] == a) return;
        esc = i;
    }
    if (!klbv_make_key(ev, digit, key, sizeof key)) { if (klbv_note(6)) klog("botvoice: HOST event %d digit %d: held back (scene / level key not readable), retried", ev, digit); return; }
    if (!klbv_gap_ok(&klbv_t.gaps, digit, ev, now)) { if (klbv_note(7)) klog("botvoice: HOST event %d digit %d key %s: held back (gap), retried on a later tick", ev, digit, key); return; }
    if (esc >= 0) klbv_t.escActor[esc] = a;
    if (klbv_mode == 2) { klog("botvoice: DRY would send event %d (%s) digit %d key %s (no packet, nothing played)", ev, klbv_ev_name(ev), digit, key); return; }
    for (i = 0; i < 4 && klbv_t.pend[i].left; i++) ;
    if (i < 4) {
        struct klbv_pk *p = &klbv_t.pend[i].pk;
        klbv_seq = klbv_next_seq(klbv_seq);
        p->T = (DWORD)klsy_T(); p->seq = klbv_seq; p->ev = ev; p->digit = digit; p->var = 1;
        klbv_t.pend[i].left = 3; klbv_t.pend[i].at = now;
        klog("botvoice: HOST event %d (%s) digit %d seq %d: queued, key %s", ev, klbv_ev_name(ev), digit, klbv_seq, key);
    } else klog("botvoice: HOST event %d digit %d: send queue full, not sent to the clients", ev, digit);
    klbv_play("HOST", ev, digit, now, 0);
}

/* HOST: send what is due (3 times, 100 ms apart). Game thread. */
static void klbv_send_due(DWORD now)
{
    int i;
    if (!klsy.sock || klbv_t.role != 2) return;
    for (i = 0; i < 4; i++) {
        unsigned char pk[KLBV_LEN]; klsy_sin a; int len, r;
        if (!klbv_t.pend[i].left || (LONG)(now - klbv_t.pend[i].at) < 0) continue;
        len = klbv_encode(pk, sizeof pk, &klbv_t.pend[i].pk);
        if (!len) { klbv_t.pend[i].left = 0; continue; }
        memset(&a, 0, sizeof a); a.fam = 2; a.port = (unsigned short)(((KLSY_PORT & 0xff) << 8) | (KLSY_PORT >> 8)); a.addr = 0xffffffffu;
        r = klsy.sendto(klsy.sock, (const char *)pk, len, 0, &a, sizeof a);
        if (klbv_t.pend[i].left == 3) klog("botvoice: HOST event %d digit %d seq %d: sent (%d bytes, sendto %d), twice more", klbv_t.pend[i].pk.ev, klbv_t.pend[i].pk.digit, klbv_t.pend[i].pk.seq, len, r);
        klbv_t.pend[i].left--; klbv_t.pend[i].at = now + 100;
    }
}

/* CLIENT: a KLSYV arrived (called from klsy_tick's drain, game thread) */
static void klbv_rx(const char *pk, int len, DWORD now, unsigned long from)
{
    struct klbv_pk k; DWORD sm, role; int take;
    if (!klbv_mode || !klbv_decode((const unsigned char *)pk, len, &k)) return;
    if (!klbv_round(&sm, &role) || role != 3) return;
    if (klbv_t.sm != sm) { klbv_reset(); klbv_t.sm = sm; }
    klbv_t.role = 3;
    /* the source pin: the sender of the first valid packet. The session host's address is not readable here (GUESS: no known field), so a mismatch is logged and the pin moves to the new sender after 10 s without a packet from the pinned one */
    if (klbv_t.srcSet && from != klbv_t.srcAddr) {
        if ((DWORD)(now - klbv_t.srcOkAt) < 10000) { if (klbv_note(8)) klog("botvoice: CLIENT packet from %lu.%lu.%lu.%lu ignored: the pinned source is %lu.%lu.%lu.%lu", from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24, klbv_t.srcAddr & 255, klbv_t.srcAddr >> 8 & 255, klbv_t.srcAddr >> 16 & 255, klbv_t.srcAddr >> 24); return; }
        klog("botvoice: CLIENT source re-pinned to %lu.%lu.%lu.%lu (nothing from %lu.%lu.%lu.%lu for 10 s)", from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24, klbv_t.srcAddr & 255, klbv_t.srcAddr >> 8 & 255, klbv_t.srcAddr >> 16 & 255, klbv_t.srcAddr >> 24);
        klbv_t.srcSet = 0; memset(&klbv_t.sq, 0, sizeof klbv_t.sq); klbv_t.haveT = 0;
    }
    if (!klbv_t.srcSet) { klbv_t.srcSet = 1; klbv_t.srcAddr = from; }
    klbv_t.srcOkAt = now;
    /* a digit not (yet) in the OnlineLooks table (its KLSYL record can arrive after this packet): do not spend the seq; the repeats 100 / 200 ms later retry */
    if (!klbv_digit_ok(k.digit)) { if (klbv_note(0)) klog("botvoice: CLIENT seq %d digit %d: not in the OnlineLooks table / range yet, not taken (a repeat retries)", k.seq, k.digit); return; }
    take = klbv_seq_take(&klbv_t.sq, k.seq);
    /* T far behind the last taken T on a packet the book calls repeat / stale = a restarted host (new seq run): reset the book (T is ms modulo 1e9; GUESS thresholds 30 s .. 500e6 ms) */
    if (!take && klbv_t.haveT && klbv_t.lastT - k.T > 30000u && klbv_t.lastT - k.T < 500000000u) {
        klog("botvoice: CLIENT seq %d T=%lu is far behind the last T=%u: the host restarted, seq book reset", k.seq, (unsigned long)k.T, klbv_t.lastT);
        memset(&klbv_t.sq, 0, sizeof klbv_t.sq); memset(&klbv_t.gaps, 0, sizeof klbv_t.gaps); take = klbv_seq_take(&klbv_t.sq, k.seq);
    }
    if (take) { klbv_t.lastT = k.T; klbv_t.haveT = 1; }
    if (klbv_t.rxN < 10 || klbv_t.rxN % 20 == 0)
        klog("botvoice: CLIENT rx #%d seq %d event %d digit %d T=%lu from %lu.%lu.%lu.%lu: %s (taken %u, repeats %u, stale %u, lost %u)", klbv_t.rxN, k.seq, k.ev, k.digit, (unsigned long)k.T, from & 255, from >> 8 & 255, from >> 16 & 255, from >> 24,
             take ? "taken" : "dropped", klbv_t.sq.taken, klbv_t.sq.repeats, klbv_t.sq.stale, klbv_t.sq.lost);
    klbv_t.rxN++;
    if (!take) return;
    if (klbv_mode == 2) { char key[200]; if (klbv_make_key(k.ev, k.digit, key, sizeof key)) klog("botvoice: DRY CLIENT would say event %d digit %d key %s (mode 2: nothing played)", k.ev, k.digit, key); return; }
    klbv_play("CLIENT", k.ev, k.digit, now, 1);
}

static void klbv_tick(int game_thread)
{
    DWORD sm, role;
    if (!klbv_mode || !game_thread || !klh_exe_ok) return;
    if (!klbv_round(&sm, &role)) { klbv_reset(); return; }
    if (role == 2 && klbv_t.sm == sm) klbv_send_due(GetTickCount());
}

#endif /* KLBOTVOICE_C */
