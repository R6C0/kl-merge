/* klstackhid_logic.h - wk-lootmetric-1102 (re/stack_state3_1102.md): [BotFill] OnlineStackRecheckHid / OnlineStackRecheckHidS, the pure scan-side
   decision. OnlineStackRecheck drops a stack that is state 0 + hidden 1 at the round start (not yet appeared; SR1D 3 -> 6 armed 3 s later).
   With the Hid key on, such a stack is kept until S seconds into the round; state 2/3 and every other hidden stack are decided as before.
   No game memory, no windows.h. Included by klbotfill.c and klstackhid_test.c. NOT run live. */
#ifndef KLSTACKHID_LOGIC_H
#define KLSTACKHID_LOGIC_H

#define KSH_DEF_S 8
#define KSH_MAX_S 60

/* [BotFill] OnlineStackRecheckHidS clamp: 0..60 s */
static int ksh_clamp_s(int s) { return s < 0 ? 0 : s > KSH_MAX_S ? KSH_MAX_S : s; }

/* 1 = drop the stack from the scan list. recheck = OnlineStackRecheck, hidOn = OnlineStackRecheckHid, st / hid as in klstackdiag_logic.h (-1 unreadable),
   elapsedMs = ms since the round started (the host's tactics round). Needs klstackdiag_logic.h included first. */
static int ksh_scan_drop(int recheck, int hidOn, int hidS, int st, int hid, unsigned long elapsedMs)
{
    if (!recheck) return 0;
    if (hidOn && st == 0 && hid == 1 && elapsedMs < (unsigned long)ksh_clamp_s(hidS) * 1000ul) return 0;
    return ksd_scan_drop(1, st, hid);
}

#endif
