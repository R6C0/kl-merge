/* klpagequeue_logic.h - [ShopPage] PageQueue / HintEveryShop and [HUD] ScoreboardNextHint, the PURE decisions (no game memory, no log, no windows.h).
   Included by klshoppage.c and klpagequeue_test.c. Written 2026-11-02 for the owner's ask 'a button on the after-match screen to get to the next page or the heisters
   page' (NOT RUN IN THE GAME).
   The session runs 0x1f (score) -> 0x20 (the round-over page, the shop between rounds) and only THERE the Buy Weapons list (shop mode 0x154d810 == 2) opens after a click.
   A page key pressed in 0x20 before the list is open used to be ignored ('shop mode is 0, not 2'). With PageQueue=1 the press is queued: it is held while the state stays
   0x20 (capped) and the page shows as soon as the list is open and the selector is wrapped. PageQueue=0 keeps every old rule: the early press of a wrapped-selector wait
   (3 s, mode 2 required) is exactly kpq_step with queued = 0. */
#ifndef KLPAGEQUEUE_LOGIC_H
#define KLPAGEQUEUE_LOGIC_H

#include <stddef.h>
#include <stdio.h>

#define KPQ_ST_ROUNDOVER 0x20          /* session state of the shop between rounds */
#define KPQ_ST_SCORE     0x1f          /* the scoreboard before it (review 11-02: the board's hint invites the press there, so a press is queued there too) */
#define KPQ_MODE_LIST    2             /* shop mode 0x154d810: the weapon list is open */
#define KPQ_EARLY_MS     3000u         /* the old hold: the selector is wrapped within 1.5 s of the list opening */
#define KPQ_CAP_MS       60000u        /* the queue's longest hold (GUESS: the scoreboard lasts a few seconds and the round-over page about 30 s; 60 s covers both) */
enum { KPQ_WAIT = 0, KPQ_APPLY = 1, KPQ_LAPSE = 2 };

/* ms since a stamp taken as 'now | 1' (0 = none). Bench pq2 11-03: the tick right after the press runs in the same GetTickCount ms (15.6 ms steps), so now - (now | 1) wrapped
   to 0xffffffff > the cap and every queued press lapsed 1 ms after it was queued (the old 3 s early press too). A stamp a little in the future counts as 0. */
static unsigned int kpq_age(unsigned int now, unsigned int at)
{
    unsigned int d = now - at;
    return d > 0x80000000u ? 0u : d;
}

/* the scoreboard or the round-over page: where a press is queued */
static int kpq_qstate(int st)
{
    return st == KPQ_ST_ROUNDOVER || st == KPQ_ST_SCORE;
}

/* a page key came: queue it? Only with PageQueue on, on the scoreboard or the round-over page, with the list not open and nothing pending yet */
static int kpq_should_queue(int queueOn, int st, int mode, int pending)
{
    return queueOn && kpq_qstate(st) && mode != KPQ_MODE_LIST && !pending;
}

/* a page key came while a QUEUED press is pending and the list is still not open: it cancels the queue (as a second press cancels the old early press) */
static int kpq_cancels(int queueOn, int st, int mode, int pending, int queued)
{
    return queueOn && pending && queued && kpq_qstate(st) && mode != KPQ_MODE_LIST;
}

/* one tick of the hold. queued 0 = the old early press (3 s, the list must be open all the time); queued 1 = the queued press (while st stays 0x20, up to the cap;
   the mode-2 check waits until the list opens). hpre = the shop gate is open, selok = the selector is wrapped (pages that need it; page II passes 1), age in ms */
static int kpq_step(int queued, int hpre, int st, int mode, int selok, unsigned int age)
{
    if (queued) {
        if (!kpq_qstate(st) || age > KPQ_CAP_MS) return KPQ_LAPSE;
        /* the scoreboard (no shop gate yet, it refuses 0x1f) and a closed gate WAIT: bench pq1 11-03 (DM06 host) lapsed on the 0x1f -> 0x20 edge because hpre is refreshed
           every 250 ms while kspg.st follows every gate caller, so the first 0x20 tick still saw the 0x1f gate's hpre 0 */
        if (st == KPQ_ST_SCORE || !hpre || mode != KPQ_MODE_LIST) return KPQ_WAIT;
        return selok ? KPQ_APPLY : KPQ_WAIT;
    }
    if (!hpre || age > KPQ_EARLY_MS || mode != KPQ_MODE_LIST) return KPQ_LAPSE;
    return selok ? KPQ_APPLY : KPQ_WAIT;
}

/* [ShopPage] AutoOpen (2026-11-03, NOT RUN IN THE GAME): with a QUEUED page press pending on the round-over page the hook itself presses Buy Weapons (ZW_SELECT3 to the page's
   MercsFAStatusReady element), so one press on the scoreboard = Buy Weapons + the page. The values below are GUESSES to be graded by the bench ('pagequeue: autoopen send N'). */
#define KPQ_AO_SETTLE_MS 800u          /* GUESS: the 0x20 page must have been up this long (its GUI pages are built and the Ready element answers) before the first send */
#define KPQ_AO_GAP_MS    1500u         /* GUESS: a retry waits this long (the list opens within about 1.5 s of a click in the log of the old early-press work) */
#define KPQ_AO_MAXSEND   3             /* at most this many sends per queued press while the list stays closed */

/* send ZW_SELECT3 now? autoOn = [ShopPage] AutoOpen, queueOn = PageQueue (AutoOpen alone does nothing), queued = a QUEUED press is pending (not lapsed / cancelled; the old early
   press of PageQueue=0 never counts), st / mode = session state / shop mode, upMs = ms the 0x20 page has been up, sends = sends so far for this press, sinceMs = ms since the last send */
static int kpq_autoopen_due(int autoOn, int queueOn, int queued, int st, int mode, unsigned int upMs, int sends, unsigned int sinceMs)
{
    if (!autoOn || !queueOn || !queued) return 0;
    if (st != KPQ_ST_ROUNDOVER) return 0;                       /* never on the scoreboard (the page does not exist yet) or in any other state */
    if (mode == KPQ_MODE_LIST) return 0;                        /* the list is open: the existing apply path takes over */
    if (upMs < KPQ_AO_SETTLE_MS) return 0;
    if (sends >= KPQ_AO_MAXSEND) return 0;
    if (sends > 0 && sinceMs < KPQ_AO_GAP_MS) return 0;
    return 1;
}

/* the Ready elements whose name may be sent to: Arcade (HeistStatus = no leaderboard, HeistLBStatus = leaderboard) and online (FAStatus, FAStatusTeam), read from the level XML
   (hire_1027/F01/online.xml). The _EndGame / _Endgame variants (game over) are NOT in the list and are refused by name: game over must never open the shop. */
static const char *const kpq_ready_names[] = { "MercsFAStatusReadyHeistLBStatus", "MercsFAStatusReadyHeistStatus", "MercsFAStatusReadyFAStatusTeam", "MercsFAStatusReadyFAStatus", 0 };

static int kpq_ready_name_ok(const char *n)
{
    int i;
    if (!n) return 0;
    for (i = 0; kpq_ready_names[i]; i++) { const char *a = kpq_ready_names[i], *b = n; while (*a && *a == *b) { a++; b++; } if (!*a && !*b) return 1; }
    return 0;
}

/* [ShopPage] AutoOpenSteps (2026-11-03, NOT RUN IN THE GAME): after AutoOpen's send opened FABuyWeaponsNew (shop mode 0), the hook opens FABuyWeaponsNewCategory and then
   FABuyWeaponsNewWeapon itself (window system 0x6bee50(name, 1, 0, 1), the call the XML's OpenWindow rows make), so the page lands on the weapon list (mode 2) with no
   RETURN. Read in kl2.exe 11-03 (research agent): each window's selector init 0x534530 sets mode = the XML SelectionState; in mode 0 it sets slot 0xced63c = -6 (Primary)
   and category 0xced640 = -4 (pistols); mode 1 keeps the slot and sets the category -4; mode 2 keeps both. The window system queues ONE request while busy (+0x4bc), so
   a step is made only when it is idle. Selector messages are never sent (ZW_SELECT3 to a selector in mode 2 BUYS). The times below are GUESSES. */
#define KPQ_AS_SETTLE_MS 300u          /* GUESS: a new top window has been on top this long before the next step (its selector init has run) */
#define KPQ_AS_FIRST_MS  5000u         /* step 0: FABuyWeaponsNew must come up within this long of the AutoOpen send (pq3: about 1.2 s) */
#define KPQ_AS_STEP_MS   2500u         /* steps 1 and 2: the asked window must answer within this long */
#define KPQ_SLOT_PRIMARY (-6)
#define KPQ_CAT_PISTOLS  (-4)
enum { KPQ_AS_WAIT = 0, KPQ_AS_OPENCAT = 1, KPQ_AS_OPENWPN = 2, KPQ_AS_DONE = 3, KPQ_AS_ABORT = 4 };
enum { KPQ_TOP_OTHER = 0, KPQ_TOP_NEW = 1, KPQ_TOP_CAT = 2, KPQ_TOP_WPN = 3 };

static int kpq_top_kind(const char *n)
{
    const char *p = "FABuyWeaponsNew"; const char *q = n;
    if (!n) return KPQ_TOP_OTHER;
    while (*p && *p == *q) { p++; q++; }
    if (*p) return KPQ_TOP_OTHER;
    if (!*q) return KPQ_TOP_NEW;
    p = "Category"; { const char *r = q; while (*p && *p == *r) { p++; r++; } if (!*p && !*r) return KPQ_TOP_CAT; }
    p = "Weapon";   { const char *r = q; while (*p && *p == *r) { p++; r++; } if (!*p && !*r) return KPQ_TOP_WPN; }
    return KPQ_TOP_OTHER;
}

/* one tick of the steps. step 0 = waiting for FABuyWeaponsNew (age = ms since the AutoOpen send), 1 = Category asked, 2 = Weapon asked (age = ms since that call).
   top = kpq_top_kind of the top window, topMs = ms it has been on top, slot / cat = 0xced63c / 0xced640, busy = the window system's +0x4bc byte */
static int kpq_aostep(int step, int top, int mode, int slot, int cat, int busy, unsigned int age, unsigned int topMs)
{
    if (mode == KPQ_MODE_LIST) return KPQ_AS_DONE;                   /* the list is open (by us or the player): the queued press applies */
    if (step == 0) {
        if (age > KPQ_AS_FIRST_MS) return KPQ_AS_ABORT;
        if (top == KPQ_TOP_CAT || top == KPQ_TOP_WPN) return KPQ_AS_ABORT;   /* the player already walks the shop: never race their own RETURN */
        if (top != KPQ_TOP_NEW || mode != 0 || slot != KPQ_SLOT_PRIMARY || busy || topMs < KPQ_AS_SETTLE_MS) return KPQ_AS_WAIT;
        return KPQ_AS_OPENCAT;
    }
    if (age > KPQ_AS_STEP_MS) return KPQ_AS_ABORT;
    if (step == 1) {
        if (top == KPQ_TOP_NEW) return KPQ_AS_WAIT;                   /* the request is still queued */
        if (top != KPQ_TOP_CAT) return KPQ_AS_ABORT;
        if (mode != 1 || busy || topMs < KPQ_AS_SETTLE_MS) return KPQ_AS_WAIT;
        return cat == KPQ_CAT_PISTOLS ? KPQ_AS_OPENWPN : KPQ_AS_ABORT;   /* research: a lower selector's update could rewrite the category; abort rather than open a bad list */
    }
    if (step == 2) return (top == KPQ_TOP_CAT || top == KPQ_TOP_WPN) ? KPQ_AS_WAIT : KPQ_AS_ABORT;
    return KPQ_AS_ABORT;
}

/* [ShopPage] HintEveryShop: what 'hint shown' becomes when the shop closes (0 = the hint may show again in the next shop) */
static int kpq_hint_done_after_close(int everyShop, int done)
{
    return everyShop ? 0 : done;
}

/* [HUD] ScoreboardNextHint: 'NEXT: BUY WEAPONS, THEN [F2] MORE PAGES  [F3] HEISTERS'; with PageQueue on (queueOn) the press works right on the board:
   'PRESS NOW: [F2] MORE PAGES ...' (the page opens with Buy Weapons). An empty / NULL key name = that feature is off. page2Key is offered only when the
   cycle key is off (the cycle key already reaches page II). Upper case (the label font is capitals). -> 1 = a line was built, 0 = no page feature on (out is empty) */
static int kpq_board_hint(char *out, size_t cap, int queueOn, const char *cycleKey, const char *hireKey, const char *page2Key)
{
    size_t l; int n = 0, i;
    const char *k[3], *w[3];
    k[0] = cycleKey; w[0] = "more pages";
    k[1] = hireKey;  w[1] = "heisters";
    k[2] = (cycleKey && cycleKey[0]) ? 0 : page2Key; w[2] = "page II";
    if (!out || cap < 16) return 0;
    out[0] = 0;
    l = (size_t)snprintf(out, cap, "%s", queueOn ? "PRESS NOW:" : "NEXT: BUY WEAPONS, THEN");
    if (l >= cap) { out[0] = 0; return 0; }
    for (i = 0; i < 3; i++) {
        size_t m; char *p;
        if (!k[i] || !k[i][0]) continue;
        m = (size_t)snprintf(out + l, cap - l, "%s[%s] %s", n ? "  " : " ", k[i], w[i]);
        if (l + m >= cap) { out[l] = 0; break; }           /* cut at a whole entry */
        for (p = out + l; *p; p++) if (*p >= 'a' && *p <= 'z') *p = (char)(*p - 'a' + 'A');
        l += m; n++;
    }
    if (!n) { out[0] = 0; return 0; }
    return 1;
}

#endif /* KLPAGEQUEUE_LOGIC_H */
