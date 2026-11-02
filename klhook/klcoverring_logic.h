/* klcoverring_logic.h - pure logic of klcoverring.c ([CoverRing] poll of the engine's REAL cover count [L+0x68] and the ZHavokCar scripts' ring state).
 * No windows.h: klcoverring_test.c checks it off-game. 2026-11-01.
 *   schedule : every tick for the first KCR_FAST_MS after a level load, then once per KCR_SLOW_MS.
 *   change   : a line is logged only when the count (or the car signature) differs from the last logged one.
 *   signature: a cheap order-sensitive hash of the car records, so a done-flag flip of one car is seen as a change.
 */
#ifndef KLCOVERRING_LOGIC_H
#define KLCOVERRING_LOGIC_H

#define KCR_FAST_MS 90000UL                 /* poll every tick this long after the load */
#define KCR_SLOW_MS 5000UL                  /* then every 5 s */
#define KCR_MAX_ENUM 60                     /* cap of car enumerations per load (log budget) */

/* is a poll due? since = ms since the load, last = ms since the last poll (0xffffffff = never). Unsigned, wrap safe. */
static int kcr_due(unsigned long since, unsigned long last)
{
    if (last == 0xfffffffful) return 1;
    if (since < KCR_FAST_MS) return 1;
    return last >= KCR_SLOW_MS;
}

/* did something change? have = 0 on the first sample of a load (that always logs: the 'at load' line) */
static int kcr_changed(int have, unsigned long prev_cnt, unsigned long cnt, unsigned long prev_sig, unsigned long sig)
{
    if (!have) return 1;
    return prev_cnt != cnt || prev_sig != sig;
}

/* fold one car's observable state into a signature */
static unsigned long kcr_sig_add(unsigned long sig, unsigned long car, unsigned long script, unsigned long n, unsigned long done, unsigned long rsv)
{
    sig = sig * 31ul + car;
    sig = sig * 31ul + script;
    sig = sig * 31ul + n;
    sig = sig * 31ul + (done & 0xfful);
    sig = sig * 31ul + (rsv & 0xfful);
    return sig;
}

/* a count a running level can show: the real list holds a few hundred points; anything huge is a misread */
static int kcr_count_sane(unsigned long cnt) { return cnt < 100000ul; }

/* does a car's script look like one: [script+0x40] must be the car, and the 8 ring indices are shown only up to n (max 8) */
static int kcr_script_matches(unsigned long car, unsigned long script_back) { return car != 0 && car == script_back; }
static unsigned long kcr_idx_shown(unsigned long n) { return n > 8ul ? 8ul : n; }

/* "does the host's real count equal base + 8 * (cars whose writer ran)?" - the GUESS of the c9 note, as a number: returns the surplus (cnt - base - 8*ran), 0 = equal */
static long kcr_surplus(unsigned long cnt, unsigned long base, unsigned long ran) { return (long)cnt - (long)base - 8L * (long)ran; }

/* ---- ClientBuild (CR2, 2026-11-01): the online CLIENT runs the ring writer 0x81b6f0 itself, once per load, for every car whose script has done == 0 and rsv == 0.
   Everything below is the DECISION only (no game memory); klcoverring.c does the call. All GUESS-level: that the host's order equals the entity-table order. */
#define KCR_CB_STABLE_MS 1000UL             /* the real count must be unchanged this long (list finished) before the first call */
#define KCR_CB_GIVEUP_MS 60000UL            /* no cars / no list this long after the load: give up for this load (log once) */
#define KCR_CB_MAXSTATE  0x19UL             /* session state 0x19 = in play; a later state (round over / shop) never builds */
/* review D1 (11-01): no lower state bound, on purpose. CR3 (11-01 23:20/23:28) built at state 0x16, 1 s after the load, on both seats of DM01 and DM03: no fault,
   asserts 0, counts equal. A later gate would be too late: the DM01 host reached 0x19 at t+21.3 s and its first car activated ~0.7 s after that */

/* role/mode of the session ([sm+0x54], [sm+0x5c]): 1 for a CLIENT (role 3) of an online game-type-4 (FA) session, and also for the HOST (role 2) when host != 0
   (ClientBuildHost, CR3 11-01: CR1 showed the host rings its cars only when each one activates mid-round, in activation order 871, 737, 792, 906 on DM01, not table
   order; so BOTH seats prebuild at load in table order and the host's later activation reuses the reserved indices: VERIFIED in dasm 0x81b709 (rsv != 0 -> jne 0x81b766 skips the
   8 x 0x558350 reservation and only rewrites the points; done != 0 -> return at 0x81b703)). Offline (0/other) -> 0 */
static int kcr_cb_role_ok(unsigned long role, unsigned long mode, int host) { return mode == 4ul && (role == 3ul || (host && role == 2ul)); }

/* review D3 (11-01): 0x558350 is a bare [L+0x68]++ with no bound against the points vector, so before the first call check that every eligible car's 8 indices fit:
   1 = cnt + 8 * eligible <= npts (vector size, (end-begin)/0x7c). npts 0 (unreadable) = no */
static int kcr_cb_fits(unsigned long cnt, unsigned long eligible, unsigned long npts) { return npts > 0ul && eligible <= 4096ul && cnt + 8ul * eligible <= npts; }

/* review D2 (11-01): the assert check 0x656740 is `test al,2; jne ok; test eax,0x200; jne ok; int3`, so a point is valid with bit 0x2 OR bit 0x200 in [pt+0x68];
   one with only 0x400 is a SPARE that still int3s. CR5 (11-02): the real ring points read 0x100a / 0x1012 / 0x140a (bit 2, no 0x200), so the old 0x200-only test
   logged every one as spare. Returns 1 = usable cover, 0 = spare / unset */
static int kcr_pt_usable(unsigned long flags) { return (flags & 0x2ul) != 0ul || (flags & 0x200ul) != 0ul; }

/* does the slot of a level key ("f01\f01_main", either slash, any case) appear in the list "F01,F03" (comma / space / semicolon separated)? Empty list = no map */
static int kcr_cb_map_listed(const char *list, const char *key)
{
    char slot[16]; int n = 0; const char *p;
    if (!list || !key) return 0;
    while (key[n] && key[n] != 0x5c && key[n] != '/' && n < (int)sizeof slot - 1) { slot[n] = (char)(key[n] >= 'a' && key[n] <= 'z' ? key[n] - 32 : key[n]); n++; }
    if (n == 0 || (key[n] && key[n] != 0x5c && key[n] != '/')) return 0;
    slot[n] = 0;
    p = list;
    while (*p) {
        int m = 0, i, same = 1;
        while (*p == ',' || *p == ' ' || *p == ';') p++;
        while (p[m] && p[m] != ',' && p[m] != ' ' && p[m] != ';') m++;
        if (m == n) {
            for (i = 0; i < m; i++) { char c = p[i]; if (c >= 'a' && c <= 'z') c = (char)(c - 32); if (c != slot[i]) { same = 0; break; } }
            if (same) return 1;
        }
        p += m;
    }
    return 0;
}

/* should this car get the call? script readable, done == 0 and rsv == 0 (the writer itself would return at once or skip the reserve otherwise) */
static int kcr_cb_car_ok(int script_readable, unsigned long done, unsigned long rsv) { return script_readable && (done & 0xfful) == 0 && (rsv & 0xfful) == 0; }

/* result codes of the gate. 0 = go (call now) */
enum { KCR_CB_GO = 0, KCR_CB_OFF, KCR_CB_NOT_CLIENT, KCR_CB_DONE, KCR_CB_STATE, KCR_CB_WAIT_LIST, KCR_CB_WAIT_CARS, KCR_CB_WAIT_STABLE, KCR_CB_GAVE_UP };

/* since = ms since the load; stable = ms the count has been unchanged; ncars = cars found; done_load = already ran / gave up for this load */
static int kcr_cb_gate(int enabled, int client, int map_ok, int done_load, unsigned long state, int list_ok, unsigned long ncars, unsigned long since, unsigned long stable)
{
    if (!enabled || !map_ok) return KCR_CB_OFF;
    if (!client) return KCR_CB_NOT_CLIENT;
    if (done_load) return KCR_CB_DONE;
    if (state > KCR_CB_MAXSTATE) return KCR_CB_STATE;
    if (since >= KCR_CB_GIVEUP_MS && (!list_ok || ncars == 0)) return KCR_CB_GAVE_UP;
    if (!list_ok) return KCR_CB_WAIT_LIST;
    if (ncars == 0) return KCR_CB_WAIT_CARS;
    if (stable < KCR_CB_STABLE_MS) return KCR_CB_WAIT_STABLE;
    return KCR_CB_GO;
}

#endif
