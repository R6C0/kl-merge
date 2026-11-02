/* klstackdiag_logic.h - wk-scorefix-1102 (re/bots_online_scorecard_1101.md G4): the short "[+0x34] state hidden" text added to the
   "stack .. is gone before it got there" and "left stack" log lines (always on, log only), and [BotFill] OnlineStackRecheck, the pure
   scan-side decision. No game memory, no windows.h. Included by klbotfill.c and klstackdiag_test.c. NOT run live. */
#ifndef KLSTACKDIAG_LOGIC_H
#define KLSTACKDIAG_LOGIC_H
#include <stdio.h>

/* amt = [stack+0x34] (-1 unreadable), st = [+0x64] state byte (-1 unreadable), armed = [+0x6c] (-1 unreadable), hid = node-hidden bit [[[o+0x24]+4]+0x3c]&0x400 (-1 unreadable, 0/1);
   vtOk = the object still has the money vtable (a freed object reads as another vtable, GUESS). */
static void ksd_fmt(char *out, int cap, int vtOk, int amt, int st, int armed, int hid)
{
    if (cap <= 0) return;
    /* count = cap, then terminate at cap-1: the klgrades.h / klshot_logic.h pattern. It yields cap-1 characters under both MSVC
       _snprintf (no terminator when it fills the buffer) and C99 snprintf (the shim maps _snprintf to it); `cap - 1` gave cap-2 on
       the C99 side, which failed klstackdiag_test's truncation check on Linux (11-02 cloud run, first with gcc -m32). */
    if (!vtOk) _snprintf(out, cap, "[+0x34]=%d state %d armed %d hidden %d (NOT the money vtable)", amt, st, armed, hid);
    else _snprintf(out, cap, "[+0x34]=%d state %d armed %d hidden %d", amt, st, armed, hid);
    out[cap - 1] = 0;
}

/* OnlineStackRecheck (default 0 = today): the stack list drops a stack whose state byte is 2 or 3 (the same refusal the timed-parts loop already has: "stack changed state")
   or whose node is hidden. GUESS: a stack the stock script hides / puts in state 2-3 at the round start is not takeable; unreadable (-1) never drops. */
static int ksd_scan_drop(int on, int st, int hid)
{
    if (!on) return 0;
    return (st >= 2 && st <= 3) || hid == 1;
}

#endif
