/*
 * klhud_shopnames.c - [HUD] OnlineShopNames=0|1|2 (default 0, recommended off until benched; needs [Online] Read=1): heister names in the ONLINE round-over / shop roster.
 * Part of KLHook (klhook.c includes it after klhud_board2.c, SHIP and TEST alike). 2026-10-27, NOT RUN LIVE.
 *
 * Why: the stock online roster (Menu/online.xml MercsShowInfoFA rows, StatusPlayerName handler 0x5bb7df) shows STEAM names. The name comes from
 * 0x67f300(sessionmgr, idx): slot = [[sm+4]->vtbl+0x38](idx) (what 0x8fdf90 does), client = [slot], name char* = [client+0x35c] (0x833cc0: add ecx,0x358; jmp 0x962850).
 * The owner wants Kane, Parker, ... there, as Arcade.
 *
 * WHAT IS AT client+0x358 (disassembled 2026-10-27, debug/dasm.py): vtable 0xbda3ec = a Quazal "PseudoGlobalVariable"-style holder (RTTI at 0xbda3e8 says
 *   PseudoGlobalVariable<MulticastInterface*>: GUESS that the name is shared by folded code, the layout is what counts). Slots: 0 0x962860 = dtor (frees [+8] ONLY, the
 *   array 0x9627d0 made), 3 0x94c310 (array[i] = [+0x10]), 4 0x962850 = GETTER (return [+4]), 5 0x950580 = SETTER (mov [ecx+4],arg: a PLAIN POINTER STORE, no copy, no free).
 *   So [client+0x35c] is a bare pointer: the holder neither owns nor frees the text it points at (GUESS: the Steam name string belongs to the session player), and a
 *   pointer swap cannot double-free. NOT a small-string / pointer+size+capacity layout, so nothing is copied in place.
 * Design (no .text detour, data only):
 *   2 = LOG ONLY, writes nothing.
 *   1 = while online and the session state [sm+0x70] is 0x1f..0x20 (KLSN_ST_SWAP: the score / roster page), for each session slot k whose client has the 0xbda3ec holder
 *       and whose seat k has a klor row with a heister name: save [client+0x35c], point it at OUR static buffer holding the name. Restored (only when the pointer is still ours
 *       AND slot k still answers the same client) when the state leaves 0x1f..0x20, the round / rules change, the roster read fails, and in klx_exit_line before ExitProcess.
 *       Other readers of the name (announcements 0x69d511 / 0x6d9f5f / 0x5e272f, KilledBy 0x500781, 0x43e4e6, FollowCam 0x8246d5) see it too while swapped: the window is short.
 *       The text chat uses a different source (GUESS: the sender's name is sent in the message), the lobby is never in the window. [[record]+8] is never touched online.
 *   Row mapping (GUESS G1, bench value 2 shows it): session slot k <-> klor row with seat == k. No row = the stock name stays.
 * Calls game code ONLY the slot getter (the vtable slot 0x38 of [sm+4]): its address must be in .text, called under __try, idx 0..KLSN_NSLOT-1; reads otherwise.
 *
 * Log lines to look for (max KLSN_CAP per session, ONE per (state, slot)):
 *   shopnames: on (mode=N ...)                                              init
 *   shopnames: getter fn XXXXXXXX code xx xx ... (sm XXXXXXXX list XXXXXXXX)  first tick in the window
 *   shopnames: state 1f slot 0 -> client XXXXXXXX holder-vt XXXXXXXX ptr XXXXXXXX stock 'R6KK0' | klor seat 0 'Kane' (row) | swapped|no row|would swap|stood down: ...
 *   shopnames: swapped N slot(s) / restored N slot(s) (why)
 */
#ifndef KLHUD_SHOPNAMES_C
#define KLHUD_SHOPNAMES_C

#define KLSN_NSLOT    12                /* session slots tried (0..11): the online FA cap is 12 players */
#define KLSN_CAP      200               /* log lines per session */
#define KLSN_VT       0xbda3ec          /* the holder at client+0x358 */
#define KLSN_O_HOLD   0x358
#define KLSN_O_PTR    0x35c
#define KLSN_ST_LO    0x1f              /* log window: the round-over score page .. the shop (0x1f..0x28) */
#define KLSN_ST_HI    0x28
#define KLSN_ST_SWAP_HI 0x20            /* the swap window 0x1f..0x20 only (the score page); GUESS: the roster shown there is the one with Steam names */
#define KLSN_TEXT_LO  0x401000          /* .text of kl2.exe: the getter must live here (no ASLR, base 0x400000) */
#define KLSN_TEXT_HI  0xb00000

static struct { int mode; } klsn;
static struct {
    DWORD rules; int round, lines, told_fn, standdown_told;
    WORD told[KLSN_ST_HI - KLSN_ST_LO + 1];                   /* per state: bit k = slot k logged */
    DWORD client[KLSN_NSLOT], saved[KLSN_NSLOT], sm;          /* the swap: client 0 = none; saved = the stock char* */
    char buf[KLSN_NSLOT][40];                                 /* OUR texts the swapped pointers point at (static: never freed) */
    int nsw;
    volatile LONG down;                                       /* set by the exit restore: the tick stands down for good (any-thread ExitProcess vs the game-thread tick) */
} klsn_c;

typedef DWORD (__fastcall *klsn_get_t)(void *, void *, int);

static int klsn_line(void) { if (klsn_c.lines >= KLSN_CAP) return 0; klsn_c.lines++; return 1; }

/* the slot object of session slot k and its client ([slot]); 0 = none. Reads h = [sm+4], fn = [[h]+0x38]; the call is the getter 0x8fdf90 jumps to. */
static DWORD klsn_client(DWORD sm, int k, DWORD *fn_out, DWORD *slot_out)
{
    DWORD h = klh_rd32(sm + 4), vt = h > 0xffff ? klh_rd32(h) : 0, fn = vt > 0xffff ? klh_rd32(vt + 0x38) : 0, slot = 0;
    if (fn_out) *fn_out = fn;
    if (slot_out) *slot_out = 0;
    if (fn < KLSN_TEXT_LO || fn >= KLSN_TEXT_HI) return 0;
    __try { slot = ((klsn_get_t)(DWORD_PTR)fn)((void *)(DWORD_PTR)h, 0, k); } __except (EXCEPTION_EXECUTE_HANDLER) { slot = 0; }
    if (slot_out) *slot_out = slot;
    return slot > 0xffff ? klh_rd32(slot) : 0;
}

/* is p inside one of OUR text buffers (never to be saved as a "stock" pointer) */
static int klsn_ours(DWORD p) { DWORD b = (DWORD)(DWORD_PTR)klsn_c.buf; return p >= b && p < b + (DWORD)sizeof klsn_c.buf; }

/* undo slot k: write the stock char* back when the client is readable, still holds the holder vtable and its pointer is still OURS. NO game call (no getter): works even when the slot no longer answers
 * this client, the session is gone, or on the exit thread. A refused write KEEPS client/saved so the next tick retries. returns 1 restored, 0 nothing of ours left, -1 refused (kept). */
static int klsn_undo(int k)
{
    DWORD c = klsn_c.client[k], cur = 0, vt = 0; int r = 0;
    if (!c) return 0;
    if (klh_rd(c + KLSN_O_HOLD, &vt, 4) && vt == KLSN_VT && klh_rd(c + KLSN_O_PTR, &cur, 4) && klsn_ours(cur)) {
        DWORD sv = klsn_c.saved[k];
        if (klsn_ours(sv)) sv = 0;     /* never write our own buffer back as "stock" (cannot happen after the save guard; belt and braces) */
        if (sv < 0x10000 || !klh_data((void *)(DWORD_PTR)(c + KLSN_O_PTR), &sv, 4, "shopnames restore")) return -1;
        r = 1;
    }       /* else the client is gone / the game stored a new pointer: nothing of ours to undo */
    klsn_c.client[k] = 0; klsn_c.saved[k] = 0; if (klsn_c.nsw > 0) klsn_c.nsw--;
    return r;
}

/* put every swapped pointer back. direct=1 = the exit path (any thread): also sets the stand-down flag. No game call either way (see klsn_undo). */
static void klsn_restore(const char *why, int direct)
{
    int k, n = 0, dropped = 0, kept = 0, had = klsn_c.nsw;
    if (direct) klsn_c.down = 1;
    for (k = 0; k < KLSN_NSLOT; k++) { int r = klsn_undo(k); if (r > 0) n++; else if (r < 0) kept++; else if (klsn_c.client[k] == 0 && had) dropped++; }
    if (had && klsn_line()) klog("shopnames: restored %d slot(s), %d dropped (pointer no longer ours), %d refused and kept for retry (%s)", n, dropped, kept, why);
}

static int klsn_name_ok(const char *s)
{
    int i; if (!s[0]) return 0;
    for (i = 0; s[i]; i++) if ((BYTE)s[i] < 0x20 || (BYTE)s[i] > 0x7e) return 0;
    return i < 32;
}

static void klsn_init(void)
{
    klsn.mode = (int)GetPrivateProfileIntA("HUD", "OnlineShopNames", 0, klh_ini);
    if (klsn.mode < 0 || klsn.mode > 2) klsn.mode = 0;
    if (klsn.mode && !klor.on) { klog("shopnames: [HUD] OnlineShopNames=%d needs [Online] Read=1: off", klsn.mode); klsn.mode = 0; }
    if (klsn.mode) klog("shopnames: on (mode=%d: %s; states %02x..%02x%s; client+0x35c char*, holder vtable %08x; NOT RUN IN THE GAME)", klsn.mode,
                        klsn.mode == 1 ? "swaps the name pointer in the roster states" : "LOG ONLY, writes nothing", KLSN_ST_LO, KLSN_ST_HI, klsn.mode == 1 ? " (swap 1f..20)" : "", KLSN_VT);
}

static void klsn_tick(int game_thread)
{
    static DWORD last; DWORD now = GetTickCount(), sm, st = 0xffffffff, osd; struct klor_snap o; int k, i, loc = -1, swap_win, ok, kmax = 0; DWORD seen[KLSN_NSLOT];
    if (!klsn.mode || klsn_c.down || !game_thread || !klh_exe_ok || (DWORD)(now - last) < 100) return;
    last = now ? now : 1;
    sm = klh_rd32((DWORD_PTR)KLH_VA(0x0168e598));
    if (sm && klh_rd(sm + 0x70, &st, 4) == 0) st = 0xffffffff;
    ok = sm && KLH_SM_VT_OK(klh_rd32(sm)) && st >= KLSN_ST_LO && st <= KLSN_ST_HI && kl_online();
    swap_win = ok && klsn.mode == 1 && st <= KLSN_ST_SWAP_HI;
    if (!swap_win && klsn_c.nsw) klsn_restore(ok ? "left the swap states" : "left the roster states / offline", 0);
    if (!ok) return;
    osd = klu_r.osd;
    if (osd) { DWORD pl = klh_rd32(osd + KLU_O_PLIST), li = 0; if (pl && klh_rd(pl + 0xefc, &li, 1) && li < 16) loc = (int)li; }
    klor_noev = 1; i = klor_read(&o, loc) && o.ok; klor_noev = 0;
    if (!i) { if (klsn_c.nsw) klsn_restore("the roster read failed", 0); return; }
    if (klsn_c.rules != o.b.rules || (o.round && klsn_c.round != o.round)) {
        if (klsn_c.nsw) klsn_restore("round or rules changed", 0);
        klsn_c.rules = o.b.rules; klsn_c.round = o.round; memset(klsn_c.told, 0, sizeof klsn_c.told);
    }
    klsn_c.sm = sm;
    for (i = 0; i < o.n; i++) if (o.r[i].seat >= kmax && o.r[i].seat < KLSN_NSLOT) kmax = o.r[i].seat + 1;     /* only ask the getter for seats that have a klor row */
    memset(seen, 0, sizeof seen);
    for (k = 0; k < kmax; k++) {
        DWORD fn = 0, slot = 0, c = klsn_client(sm, k, &fn, &slot), ptr = 0, vt = 0; const struct klor_row *row = 0; const char *nm = ""; char stock[40], why[64]; int dup, stock_ok;
        if (!klsn_c.told_fn && fn && klsn_line()) {
            BYTE code[16]; char hx[64]; int j; klsn_c.told_fn = 1; memset(code, 0, sizeof code); klh_rd(fn, code, 16);
            for (j = 0; j < 16; j++) snprintf(hx + 3 * j, 4, "%02x ", code[j]);
            klog("shopnames: getter fn %08lx code %s(sm %08lx list %08lx)", (unsigned long)fn, hx, (unsigned long)sm, (unsigned long)klh_rd32(sm + 4));
        }
        if (!c) continue;
        for (i = 0; i < k; i++) if (seen[i] == c) break;
        dup = i < k; seen[k] = c;
        klh_rd(c + KLSN_O_HOLD, &vt, 4); klh_rd(c + KLSN_O_PTR, &ptr, 4);
        for (i = 0; i < o.n; i++) if (o.r[i].seat == k) { row = &o.r[i]; break; }
        if (row) nm = row->name[0] ? row->name : (k < KLOR_MAX ? klor_c.name[k] : "");      /* klor_c.name: the cache for a seat whose body is gone */
        stock_ok = 1;
        if (klsn_ours(ptr)) { snprintf(stock, sizeof stock, "(ours) %s", (const char *)(DWORD_PTR)ptr); stock_ok = klsn_c.client[k] == c && ptr == (DWORD)(DWORD_PTR)klsn_c.buf[k]; }
        else if (!klh_rdstr(ptr, stock, sizeof stock) || !stock[0]) { snprintf(stock, sizeof stock, "?"); stock_ok = 0; }
        why[0] = 0;
        if (klsn.mode == 1) {
            if (!row) snprintf(why, sizeof why, "no row for seat %d: stock", k);
            else if (!klsn_name_ok(nm)) snprintf(why, sizeof why, "row has no usable name: stock");
            else if (vt != KLSN_VT) snprintf(why, sizeof why, "STOOD DOWN: holder vtable %08lx is not %08x", (unsigned long)vt, KLSN_VT);
            else if (dup) snprintf(why, sizeof why, "STOOD DOWN: client already seen under another slot");
            else if (ptr < 0x10000 && !klsn_ours(ptr)) snprintf(why, sizeof why, "STOOD DOWN: name pointer %08lx unusable", (unsigned long)ptr);
            else if (!stock_ok) snprintf(why, sizeof why, "STOOD DOWN: stock text unreadable or pointer is still ours from an earlier swap");     /* evidence gate: a readable stock Steam name must be there; GUESS G1 (seat==slot) has no name to compare against in klor */
            else if (!swap_win) snprintf(why, sizeof why, "state %02lx is outside the swap states: stock", (unsigned long)st);
        } else snprintf(why, sizeof why, "%s", !row ? "no row" : "would swap");
        if (klsn.mode == 1 && why[0] && klsn_c.client[k] && klsn_undo(k) > 0 && klsn_line()) klog("shopnames: slot %d swap undone at once (%s)", k, why);
        if (klsn.mode == 1 && !why[0]) {
            if (klsn_c.client[k] && klsn_c.client[k] != c) { DWORD oc = klsn_c.client[k]; int r = klsn_undo(k); if (klsn_line()) klog("shopnames: slot %d client changed %08lx -> %08lx: the old swap is undone (%d)", k, (unsigned long)oc, (unsigned long)c, r); if (r < 0) { snprintf(why, sizeof why, "STOOD DOWN: old swap not yet undone"); } }
            if (why[0]) { /* old swap kept for retry */ }
            else if (!klsn_c.client[k]) {
                DWORD nb = (DWORD)(DWORD_PTR)klsn_c.buf[k];
                snprintf(klsn_c.buf[k], sizeof klsn_c.buf[k], "%s", nm);
                if (klh_data((void *)(DWORD_PTR)(c + KLSN_O_PTR), &nb, 4, "shopnames swap")) { klsn_c.client[k] = c; klsn_c.saved[k] = ptr; klsn_c.nsw++; snprintf(why, sizeof why, "SWAPPED"); }
                else snprintf(why, sizeof why, "STOOD DOWN: write refused");
            } else if (strcmp(klsn_c.buf[k], nm)) { snprintf(klsn_c.buf[k], sizeof klsn_c.buf[k], "%s", nm); snprintf(why, sizeof why, "SWAPPED (text updated)"); }
            else snprintf(why, sizeof why, "SWAPPED");
        }
        if (st - KLSN_ST_LO < (DWORD)(sizeof klsn_c.told / sizeof klsn_c.told[0]) && !(klsn_c.told[st - KLSN_ST_LO] & (1u << k))) {
            klsn_c.told[st - KLSN_ST_LO] |= (WORD)(1u << k);
            if (klsn_line()) klog("shopnames: state %02lx slot %d -> client %08lx (slot obj %08lx) holder-vt %08lx ptr %08lx stock '%s' | klor seat %s name '%s' cache '%s' | %s | local seat %d round %d",
                                  (unsigned long)st, k, (unsigned long)c, (unsigned long)slot, (unsigned long)vt, (unsigned long)ptr, stock, row ? "yes" : "NONE", nm, k < KLOR_MAX ? klor_c.name[k] : "", why, loc, o.round);
        }
    }
}

#endif /* KLHUD_SHOPNAMES_C */
