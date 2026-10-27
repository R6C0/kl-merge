/*
 * klmappool.c - [MapPool] RANDOM MAP POOLS for online rounds (2026-10-27, mappool_1027a; owner: 'random maps with the icons showing what maps
 * in the pool e.g. full dead men, full dog days, mix'). Part of KLHook (included by klhook.c AFTER klslot.c, BEFORE klhostopt.c); DATA only
 * (our own variables, the ini, and - only with Apply=1 - the game's own lobby setters called from the game thread). SHIP and TEST alike.
 *
 * POOL (host chooses; value 0 = off, 1 = Full Dead Men, 2 = Full Dog Days, 3 = Mix):
 *   the pool is built from the [Redirect] / [Redirect.N] rules klslot.c loaded (every (slot, page) with a map folder) plus the stock level of any
 *   slot that has only paged rules. A map is classified by its FOLDER NAME: DM* = Dead Men, DD* = Dog Days (and the stock level), anything else =
 *   Mix only. Pool 1 = the DM entries, 2 = the DD/stock entries, 3 = all.
 * DRAW: a seeded permutation (splitmix64 Fisher-Yates) of the pool; every load takes the first entry of the permutation that is not used yet AND
 *   belongs to the slot the game is loading; it is then marked used. When every entry is used the cycle number goes up (a new permutation, all
 *   free again). So: no map twice until the whole pool has been played. Peers need NO message per round: the seed (host's, sent in klx_opts as
 *   'q<hex>'; fallback = the Steam lobby id) and the load count are the same on every peer, and the slot of each load is the host's (replicated by
 *   the game itself, DDL SetLevelIndex), so the same entry is taken. A map folder is bound to ITS slot (files are named Fxx_Main.*), which is why a
 *   draw can only choose among the entries of the slot being loaded unless the host also moves the slot:
 * APPLY (host, [MapPool] Apply=1, default 0, GUESS - not run live): in the lobby the host looks at the NEXT entry of the permutation and, when its
 *   slot differs from the lobby's slot, sets the lobby slot with the sequence the stock selector uses (re/private_match_mapsync.md 6.1):
 *   store MP_SelectedLevel (0xb6d6e4) = menu index of the slot (inverse table 0x80c9f0), sm vtbl+0x28(slot), 0x7163e0(sm, slot), 0x4b5fc0(sm)
 *   (commit: DDL SetLevelIndex, replicates), 0x549e80(sm) (Steam lobby data). With Apply=0 the pool only chooses among the loaded slot's maps.
 * ICONS: the lobby picture toggler shows the host's slot picture. tools/kl_mappool.py stages one icon set per pool (a collage of every map in
 *   the pool, with the pool label as the map title) that INSTALL swaps in; the in-game picture cannot be changed live from the hook (no safe
 *   route found), so the icon set is chosen at install time and the label tells which pool it is.
 * Offline / Arcade: NEVER touched (klpm.c owns it).
 *
 * [MapPool] Enable=0 (recommended off until benched) / Pool=0 (0 off, 1 DM, 2 DD, 3 Mix; the HOST's value is what counts: klhostopt.c sends it)
 *           / Apply=0 / Seed=0 (fixed seed for tests; 0 = the host's / lobby id) / Log=1.
 */
#ifndef KLMAPPOOL_C
#define KLMAPPOOL_C

#define KMP_MAX 64
static struct {
    int on, apply, log, ini_pool, seedIni;
    int pool;                              /* the effective pool (host: own; client: the host's as heard) */
    DWORD seed;                            /* the effective seed; 0 = not known yet */
    int n, cls[KMP_MAX], slot[KMP_MAX], page[KMP_MAX]; char name[KMP_MAX][48];
    int built, order[KMP_MAX], norder, used[KMP_MAX], cycle, loads;
    DWORD builtSeed; int builtPool;
    int curSlot, curPage; DWORD curAt;     /* the pick of the load in progress (probes within 60 s repeat it) */
    DWORD lastApply; int lastWant;
} kmp;

static const int kmp_menu_idx[9] = { 0, 1, 2, 3, 6, 4, 5, 7, 8 };      /* slot (Fnn - 1) -> menu index; the exe's table at 0x80c9f0 */

static const char *kmp_pool_name(int p) { return p == 1 ? "Full Dead Men" : p == 2 ? "Full Dog Days" : p == 3 ? "Mix (Dead Men + Dog Days)" : "off"; }

static unsigned __int64 kmp_mix(unsigned __int64 x)
{
    x += 0x9E3779B97F4A7C15ULL; x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL; x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL; return x ^ (x >> 31);
}

static int kmp_class(const char *map)
{   /* 1 = Dead Men (DM*), 2 = Dog Days (DD*), 0 = other (Mix only) */
    if (!_strnicmp(map, "DM", 2)) return 1;
    if (!_strnicmp(map, "DD", 2)) return 2;
    return 0;
}

static int kmp_in_pool(int pool, int cls) { return pool == 3 || (pool == 1 && cls == 1) || (pool == 2 && cls == 2); }

static void kmp_build(void)
{   /* the entry list from klslot.c's rules (identical on every peer with the same ini and map folders) */
    int s, r, p;
    kmp.n = 0;
    for (s = 0; s < kls_nslots && s < KLS_SLOTS; s++) {
        int has0 = kls_find_rule(s, 0) >= 0;
        if (kls_slot[s].name[0] != 'F' && kls_slot[s].name[0] != 'f') continue;
        if (!has0 && kmp.n < KMP_MAX) {            /* the stock level of the slot (a Dog Days map) */
            kmp.slot[kmp.n] = s; kmp.page[kmp.n] = 0; kmp.cls[kmp.n] = 2; snprintf(kmp.name[kmp.n], 48, "stock %s", kls_slot[s].name); kmp.n++;
        }
        for (p = 0; p < KLS_RANDOM; p++) {
            if (p == 1 || (r = kls_find_rule(s, p)) < 0 || kmp.n >= KMP_MAX) continue;
            kmp.slot[kmp.n] = s; kmp.page[kmp.n] = p; kmp.cls[kmp.n] = kmp_class(kls_rule[r].map);
            snprintf(kmp.name[kmp.n], 48, "%s", kls_rule[r].map); kmp.n++;
        }
    }
    kmp.built = 1;
}

static void kmp_perm(void)
{   /* the permutation of the current pool for (seed, cycle) */
    int i, j, t; unsigned __int64 x;
    kmp.norder = 0;
    for (i = 0; i < kmp.n; i++) if (kmp_in_pool(kmp.pool, kmp.cls[i])) kmp.order[kmp.norder++] = i;
    x = ((unsigned __int64)kmp.seed << 8) ^ ((unsigned __int64)(kmp.cycle + 1) * 0xD6E8FEB86659FD93ULL) ^ (unsigned __int64)kmp.pool;
    for (i = kmp.norder - 1; i > 0; i--) { x = kmp_mix(x); j = (int)((x >> 8) % (unsigned)(i + 1)); t = kmp.order[i]; kmp.order[i] = kmp.order[j]; kmp.order[j] = t; }
    kmp.builtSeed = kmp.seed; kmp.builtPool = kmp.pool;
}

static void kmp_ready(void)
{   /* (re)build when the pool or seed changed: a new pool starts a fresh no-repeat cycle */
    if (!kmp.built) kmp_build();
    if (kmp.builtPool != kmp.pool || kmp.builtSeed != kmp.seed) {
        if (kmp.builtPool != kmp.pool || kmp.builtSeed != kmp.seed) { memset(kmp.used, 0, sizeof kmp.used); kmp.cycle = 0; kmp.loads = 0; kmp.curAt = 0; }
        kmp_perm();
        if (kmp.log) {
            int i; char b[600]; int l = snprintf(b, sizeof b, "mappool: pool %d (%s) seed %08lx: %d maps, order:", kmp.pool, kmp_pool_name(kmp.pool), (unsigned long)kmp.seed, kmp.norder);
            for (i = 0; i < kmp.norder && l < (int)sizeof b - 60; i++) l += snprintf(b + l, sizeof b - l, " %s(F%02d)", kmp.name[kmp.order[i]], atoi(kls_slot[kmp.slot[kmp.order[i]]].name + 1));
            klog("%s", b);
        }
    }
}

static int kmp_next_entry(int slotFilter)
{   /* the first unused entry of the permutation (of the slot, when slotFilter >= 0); starts a new cycle when all are used; -1 = none */
    int i, tries;
    for (tries = 0; tries < 2; tries++) {
        int all = 1;
        for (i = 0; i < kmp.norder; i++) if (!kmp.used[kmp.order[i]]) { all = 0; if (slotFilter < 0 || kmp.slot[kmp.order[i]] == slotFilter) return kmp.order[i]; }
        if (!all || !kmp.norder) return -1;        /* unused entries exist, just not for this slot (or the pool is empty) */
        memset(kmp.used, 0, sizeof kmp.used); kmp.cycle++; kmp_perm();
        if (kmp.log) klog("mappool: every map of the pool was played: new cycle %d (new order)", kmp.cycle);
    }
    return -1;
}

/* from klslot.c kls_map, online only: -> the page for slot index s, or -1 = the pool does not decide (stock rules apply). */
static int kmp_pick(int s)
{
    DWORD now = GetTickCount(); int e;
    if (!kmp.on || !kmp.pool || !kmp.seed) return -1;
    kmp_ready();
    if (kmp.curAt && kmp.curSlot == s && now - kmp.curAt < 60000) { kmp.curAt = now ? now : 1; return kmp.curPage; }   /* the probes of one load */
    e = kmp_next_entry(s);
    if (e < 0) { if (kmp.log) klog("mappool: slot %s has no map in pool %s: the stock rules decide", kls_slot[s].name, kmp_pool_name(kmp.pool)); return -1; }
    kmp.used[e] = 1; kmp.loads++; kmp.curSlot = s; kmp.curPage = kmp.page[e]; kmp.curAt = now ? now : 1;
    if (kmp.log) klog("mappool: LOAD %d (cycle %d): pool %s -> %s on slot %s (page %d)", kmp.loads, kmp.cycle, kmp_pool_name(kmp.pool), kmp.name[e], kls_slot[s].name, kmp.page[e]);
    return kmp.page[e];
}

/* ---- HOST: put the lobby on the slot of the NEXT map of the permutation (Apply=1, GUESS) ---- */
typedef DWORD (__fastcall *kmp_f0)(void *self, void *edx);
typedef DWORD (__fastcall *kmp_f1)(void *self, void *edx, DWORD a);
typedef DWORD (__fastcall *kmp_f3)(void *self, void *edx, DWORD a, DWORD b, DWORD c);

static void kmp_tick(int game_thread, int host)
{
    DWORD now = GetTickCount(), sm, st = 0, vt, fn, state = 0, cur = 0xff; int e, want, slot;
    if (!kmp.on || !kmp.apply || !game_thread || !host || !kmp.pool || !kmp.seed || !klh_exe_ok) return;
    if (now - kmp.lastApply < 3000) return;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));
    if (!sm || !klh_rd(sm + 0x70, &state, 4) || state != 0xd) return;              /* only while the lobby screen is up */
    kmp_ready();
    if (kmp.curAt && now - kmp.curAt < 60000) return;                             /* a load is in progress */
    e = kmp_next_entry(-1);
    if (e < 0) return;
    slot = atoi(kls_slot[kmp.slot[e]].name + 1) - 1;
    if (slot < 0 || slot > 8) return;
    klh_rd(sm + 0xbf, &cur, 1);
    if ((int)(cur & 0xff) == slot) { kmp.lastWant = slot; return; }
    if (kmp.lastWant == slot && now - kmp.lastApply < 15000) return;               /* tried just now: do not loop on a setter that does not stick */
    vt = klh_rd32(sm); fn = vt ? klh_rd32(vt + 0x28) : 0;
    if (fn < (DWORD)(DWORD_PTR)KLH_VA(0x401000) || fn >= (DWORD)(DWORD_PTR)KLH_VA(0xa00000)) return;     /* not kl2.exe code: a foreign vtable, do not call */
    want = slot; kmp.lastApply = now; kmp.lastWant = want;
    ((kmp_f1)(DWORD_PTR)fn)((void *)(DWORD_PTR)sm, 0, (DWORD)slot);                /* GUESS (menu order, see header): sm vtbl+0x28 = SetLevel(slot) */
    ((kmp_f1)KLH_VA(0x7163e0))((void *)(DWORD_PTR)sm, 0, (DWORD)slot);
    ((kmp_f0)KLH_VA(0x4b5fc0))((void *)(DWORD_PTR)sm, 0);                          /* commit: DDL SetLevelIndex, replicates to the peers */
    st = kllo_store();
    if (st) ((kmp_f3)(DWORD_PTR)klh_rd32(klh_rd32(st) + 0x14))((void *)(DWORD_PTR)st, 0, 0xb6d6e4, (DWORD)kmp_menu_idx[slot], 0);
    ((kmp_f0)KLH_VA(0x549e80))((void *)(DWORD_PTR)sm, 0);                          /* Steam lobby data */
    klog("mappool: HOST set the lobby slot %lu -> F%02d for the next map %s (pool %s, GUESS sequence, store %s)", (unsigned long)(cur & 0xff), slot + 1, kmp.name[e], kmp_pool_name(kmp.pool), st ? "set" : "NOT found");
}

static void kmpo_init(void);                  /* klmappool_ov.c: [MapPool] Overlay (the live pool drawn over the lobby) */

static void kmp_init(void)
{
    kmp.on = GetPrivateProfileIntA("MapPool", "Enable", 0, klh_ini) != 0;
    kmp.log = GetPrivateProfileIntA("MapPool", "Log", 1, klh_ini) != 0;
    kmp.lastWant = -1;
    if (!kmp.on) return;
    kmp.apply = GetPrivateProfileIntA("MapPool", "Apply", 0, klh_ini) != 0;
    kmp.ini_pool = GetPrivateProfileIntA("MapPool", "Pool", 0, klh_ini);
    if (kmp.ini_pool < 0 || kmp.ini_pool > 3) kmp.ini_pool = 0;
    kmp.seedIni = (int)GetPrivateProfileIntA("MapPool", "Seed", 0, klh_ini);
    kmp.pool = 0; kmp.seed = 0;                 /* the effective values are set by klhostopt.c while a session runs: nothing outside one */
    klog("mappool: on; Pool=%d (%s) Apply=%d Seed=%08lx Log=%d; NOT run live. The pool and seed come from the host (klhostopt.c 'p<pool>q<seed>')", kmp.pool, kmp_pool_name(kmp.pool), kmp.apply, (unsigned long)kmp.seed, kmp.log);
    kmpo_init();
}

#endif
