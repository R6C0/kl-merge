/* klcoverring_logic.h - pure logic of klcoverring.c ([CoverRing] poll of the engine's REAL cover count [L+0x68] and the ZHavokCar scripts' ring state).
 * No windows.h: klcoverring_test.c checks it off-game. 2026-11-01.
 *   schedule : every tick for the first KCR_FAST_MS after a level load, then once per KCR_SLOW_MS.
 *   change   : a line is logged only when the count (or the car signature) differs from the last logged one.
 *   signature: a cheap order-sensitive hash of the car records, so a done-flag flip of one car is seen as a change.
 */
#ifndef KLCOVERRING_LOGIC_H
#define KLCOVERRING_LOGIC_H

#include <string.h>

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

/* ---- ClientRewrite (CR6, 2026-11-02): the online CLIENT re-runs the ring writer for a prebuilt car when that car activates, so the points get real positions like on the host.
   Why it needs the done flag: ClientBuild leaves done[+1e8]=1 rsv[+1e9]=1; the writer returns at once on done != 0 (0x81b703). The host's own activation runs it with done == 0
   (CR1: car #2's done went 1 -> 0 -> 1 with no count growth), so the client sets done to 0 itself before the call (GUESS: whatever clears it on the host is not found; the
   writer sets it to 1 again at 0x81bacb). rsv == 1 makes the writer skip the 8 index reservations (dasm 0x81b709), so the count must NOT grow and the indices must not change.
   Everything below is the DECISION only (no game memory). */
#define KCR_RW_MAXTRY   4UL                 /* attempts per car per load (state change + spare retries) */
#define KCR_RW_RETRY_MS 1500UL              /* spacing of two attempts on one car */
#define KCR_RW_SCAN_MS  200UL               /* the per-car state is looked at this often */
#define KCR_RW_SPARE_MS 15000UL             /* review 11-02: spares left after a try are retried this long after it even without a new state change
                                               (a field that moved at load would otherwise burn the only try on a parked car) */
enum { KCR_RW_NONE = 0, KCR_RW_STATE, KCR_RW_SPARE };

/* may a prebuilt ring be rewritten? exactly the shape ClientBuild leaves: done 1, rsv 1, 1..8 indices */
static int kcr_rw_pre_ok(unsigned long done, unsigned long rsv, unsigned long n) { return (done & 0xfful) == 1ul && (rsv & 0xfful) == 1ul && n >= 1ul && n <= 8ul; }

/* when is a rewrite due? state_changed = [car+0x8c0] or [car+0xa28] differs from the value seen right after the prebuild (GUESS: that is the client's view of the activation);
   spares = points of the ring that are not usable; tries/since_ms = attempts so far / ms since the last one (0xffffffff = never). */
static int kcr_rw_trigger(int state_changed, unsigned long spares, unsigned long tries, unsigned long since_ms)
{
    if (tries >= KCR_RW_MAXTRY) return KCR_RW_NONE;
    if (tries && since_ms < KCR_RW_RETRY_MS) return KCR_RW_NONE;
    if (!tries && state_changed) return KCR_RW_STATE;
    if (tries && spares && (state_changed || since_ms >= KCR_RW_SPARE_MS)) return KCR_RW_SPARE;   /* only after a first try, only while spares remain */
    return KCR_RW_NONE;
}

/* session gate: ClientRewrite on, an online client (never the host: the host does this itself), ClientBuild finished clean, state not past in-play */
static int kcr_rw_gate(int enabled, int client, int cb_done_ok, unsigned long state) { return enabled && client && cb_done_ok && state <= KCR_CB_MAXSTATE; }

/* after the call: the count must be unchanged and the indices equal; anything else = the reserve path ran (rsv semantics wrong) -> feature off */
static int kcr_rw_after_ok(unsigned long cnt_before, unsigned long cnt_after, int idx_same) { return cnt_before == cnt_after && idx_same; }

/* ---- ClientRingSync (CR8, 2026-11-02): the HOST sends the cover points of each prebuilt car ('KLSYR', UDP 27415 broadcast, the KLSYV socket); the CLIENT copies a point
   into its own list only where the host's point is usable and the client's is a spare. Reason (CR7): the ring is a function of the car's world pose at call time and the car is
   NOT replicated (GUESS: no ZHavokCar net sync in the RTTI), so the rings differ per seat (yaw 11 vs 0 deg on DM03 car #0); only a copy makes "usable on the host" imply
   "usable on the client". Pure encode / decode / decision here; no game memory.
   KLSYR (little endian), header 24 bytes then n x 60 bytes:
      0 8 "KLSYR\0\0\0" | 8 u32 T (host klsy_T) | 12 u16 seq | 14 u8 ver=1 | 15 u8 n (1..8) | 16 u16 car ordinal (entity-table order, informational) | 18 u16 0 | 20 u32 0
      per point: u32 idx | u32 flags [pt+0x68] | f32 x3 [pt+0x28] | 9 x u32 [pt+0x40..0x63] | u32 [pt+0x24]
   The format is a GUESS of this build. */
#define KCR_RS_HDR   24
#define KCR_RS_REC   60
#define KCR_RS_MAXN  8
#define KCR_RS_MAXIDX 100000ul
#define KCR_RS_MS    1000UL                 /* host: every car is re-sent this often (a lost datagram is repaired by the next) */
#define KCR_RS_MAXCARS 16                   /* host: cars per sweep (1 packet each, ~504 bytes, far under the 1472 MTU) */
#define KCR_RS_MOVED 20.0f                  /* a client point farther than this from the host's one is only LOGGED (stage 1 never overwrites a usable point) */

struct kcr_rpt { unsigned long idx, flags, blk[9], f24; float pos[3]; };
struct kcr_rhdr { unsigned long T; unsigned seq, ord, n; };

static void kcr_rs_p32(unsigned char *p, unsigned long v) { p[0] = (unsigned char)v; p[1] = (unsigned char)(v >> 8); p[2] = (unsigned char)(v >> 16); p[3] = (unsigned char)(v >> 24); }
static unsigned long kcr_rs_g32(const unsigned char *p) { return (unsigned long)p[0] | (unsigned long)p[1] << 8 | (unsigned long)p[2] << 16 | (unsigned long)p[3] << 24; }
static void kcr_rs_pf(unsigned char *p, float f) { unsigned long v; memcpy(&v, &f, 4); kcr_rs_p32(p, v); }
static float kcr_rs_gf(const unsigned char *p) { unsigned long v = kcr_rs_g32(p); float f; unsigned int u = (unsigned int)v; memcpy(&f, &u, 4); return f; }

/* bytes written, 0 = refused (cap, n, an index out of range, seq 0) */
static int kcr_ring_pack(unsigned char *out, int cap, const struct kcr_rhdr *h, const struct kcr_rpt *pts)
{
    unsigned i; int k, len;
    if (!out || !h || !pts || h->n < 1u || h->n > KCR_RS_MAXN || h->seq < 1u || h->seq > 65535u || h->ord > 65535u) return 0;
    len = KCR_RS_HDR + (int)h->n * KCR_RS_REC;
    if (cap < len) return 0;
    for (i = 0; i < h->n; i++) if (pts[i].idx >= KCR_RS_MAXIDX) return 0;
    memset(out, 0, (size_t)len);
    memcpy(out, "KLSYR", 5);
    kcr_rs_p32(out + 8, h->T); out[12] = (unsigned char)h->seq; out[13] = (unsigned char)(h->seq >> 8); out[14] = 1; out[15] = (unsigned char)h->n;
    out[16] = (unsigned char)h->ord; out[17] = (unsigned char)(h->ord >> 8);
    for (i = 0; i < h->n; i++) {
        unsigned char *r = out + KCR_RS_HDR + i * KCR_RS_REC;
        kcr_rs_p32(r, pts[i].idx); kcr_rs_p32(r + 4, pts[i].flags);
        for (k = 0; k < 3; k++) kcr_rs_pf(r + 8 + k * 4, pts[i].pos[k]);
        for (k = 0; k < 9; k++) kcr_rs_p32(r + 20 + k * 4, pts[i].blk[k]);
        kcr_rs_p32(r + 56, pts[i].f24);
    }
    return len;
}

/* n points decoded (1..8), 0 = refused: short / long / foreign magic / wrong version / reserved bytes / n out of range / index out of range / T or seq out of range */
static int kcr_ring_unpack(const unsigned char *pk, int len, struct kcr_rhdr *h, struct kcr_rpt *pts)
{
    unsigned i; int k;
    if (!pk || !h || !pts || len < KCR_RS_HDR || memcmp(pk, "KLSYR\0\0\0", 8)) return 0;
    if (pk[14] != 1 || pk[18] || pk[19] || kcr_rs_g32(pk + 20)) return 0;
    h->T = kcr_rs_g32(pk + 8); h->seq = (unsigned)pk[12] | (unsigned)pk[13] << 8; h->n = pk[15]; h->ord = (unsigned)pk[16] | (unsigned)pk[17] << 8;
    if (h->T >= 1000000000ul || h->seq < 1u || h->n < 1u || h->n > KCR_RS_MAXN || len != KCR_RS_HDR + (int)h->n * KCR_RS_REC) return 0;
    for (i = 0; i < h->n; i++) {
        const unsigned char *r = pk + KCR_RS_HDR + i * KCR_RS_REC;
        memset(&pts[i], 0, sizeof pts[i]);
        pts[i].idx = kcr_rs_g32(r); pts[i].flags = kcr_rs_g32(r + 4);
        if (pts[i].idx >= KCR_RS_MAXIDX) return 0;
        for (k = 0; k < 3; k++) pts[i].pos[k] = kcr_rs_gf(r + 8 + k * 4);
        for (k = 0; k < 9; k++) pts[i].blk[k] = kcr_rs_g32(r + 20 + k * 4);
        pts[i].f24 = kcr_rs_g32(r + 56);
    }
    return (int)h->n;
}

/* the next seq (1..65535) */
static unsigned kcr_rs_next_seq(unsigned s) { return s >= 65535u || s < 1u ? 1u : s + 1u; }

/* what to do with one received point. 1 = write it into the client's slot (host usable, client spare). 0 = leave: the host's point is a spare (nothing to give), or the client's is
   already usable (stage 1 never overwrites a usable point: no position / nav churn). */
static int kcr_ring_apply_decision(unsigned long client_flags, unsigned long host_flags) { return kcr_pt_usable(host_flags) && !kcr_pt_usable(client_flags); }

/* 1 when the points are farther apart than KCR_RS_MOVED on any axis pair (squared distance); used for the log only */
static int kcr_rs_moved(const float *a, const float *b)
{
    float dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
    return dx * dx + dy * dy + dz * dz > KCR_RS_MOVED * KCR_RS_MOVED;
}

/* a received position is written only when every axis is finite and inside +-1e7 (a NaN fails both compares) */
static int kcr_rs_pos_ok(const float *p)
{
    int k;
    for (k = 0; k < 3; k++) if (!(p[k] > -1e7f && p[k] < 1e7f)) return 0;
    return 1;
}

/* may this index be written? it must be one of the client's own car's ring indices (idx list of n entries) and inside the points vector; anything else = the car sets differ */
static int kcr_rs_idx_owned(const unsigned long *own, unsigned long nown, unsigned long idx, unsigned long npts)
{
    unsigned long k;
    if (!own || idx >= npts) return 0;
    for (k = 0; k < nown && k < 8ul; k++) if (own[k] == idx) return 1;
    return 0;
}

/* host side: may a car be sent? built ring (done 1), 1..8 indices, every index inside the points vector */
static int kcr_rs_car_sendable(unsigned long done, unsigned long n, const unsigned long *idx, unsigned long npts)
{
    unsigned long k;
    if ((done & 0xfful) != 1ul || n < 1ul || n > 8ul) return 0;
    for (k = 0; k < n; k++) if (idx[k] >= npts) return 0;
    return 1;
}

#endif
