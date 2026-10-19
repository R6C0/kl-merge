/*
 * klheliprobe.c - READ-ONLY probe of the escape chopper's flight start ([Heli] Probe, default 0). Part of KLHook (included by
 * klhook.c after klescort.c: it uses klh_rd / klh_rd32 / klb_finite / kle_node / KLE_ENTS; SHIP and TEST alike).
 * It exists to settle the STILL UNKNOWN items of re\heli_call.md "Flight start, read statically" in one live run:
 * does the rout's goal exist, is the squad set, which early-out of 0x791090 / 0x7f6750 holds, does the body move.
 *
 * Probe=0 (default): klhp_init reads the key once, finds 0 and RETURNS; klhp_tick returns at its first statement
 *   (`if (!klhp.on) return;`). No patch, no write, no log line, no memory read: the behaviour equals HEAD.
 * Probe=1: at most one 'heli:' line per second per object set, plus one on each CHANGE of a non-position field (changes are
 *   themselves limited to 5 lines a second and KLHP_CAP lines in all). The objects are found in the scene's entity table
 *   (KLE_ENTS, the table klescort.c kle_veh_read walks: 128-byte slots, object at slot+0x60), by vtable.
 * Probe=2: as 1, and while no rout was found in the entity table a bounded scan of the process' committed read/write
 *   pages for the rout's vtable dword (every 10 s at most, 64 MB per pass; controllers may not be table entities).
 * NEVER writes. Every pointer goes through klh_rd (ReadProcessMemory, never faults). Hook point: klh_tick(game_thread), the
 * existing per-frame tick; NO code patch, NO import slot.
 *
 * What is read (kl2.exe build 0490; every offset not marked [EXE] is a GUESS from the static read of re\heli_call.md):
 *   rout  = object with vtable 0xbcd5cc (ZHeliFlyBehaviourRout; vtbl +0x88 = start 0x80dcd0)       [EXE: RTTI]
 *     [rout+0x74] goal (0x80dcd0 eax), [goal+8] (0 or 4 lets the start run), [rout+0x38] (0x791090 edi+0x38)   [EXE]
 *     [rout+0x40] started, [rout+0x41] blocked (0x4ebed0)                                                     [EXE]
 *   actor = [rout+0x38]: 0x791090 reads it as `mov eax,[edi+0x38]` and tests [eax+0x8c], [eax+0xbc]; the task calls the same
 *     pointer 'the squad'. GUESS that it is ONE object (the line prints it once as sq=). Its +0x8c, +0x90 (0x7f6750),
 *     +0xbc (0x791110 one-shot flag), +0x154 (0x7f680e goal store) are read as dwords (+0xbc as a byte).   [EXE read, GUESS identity]
 *   car   = rules [[0x168e9e4]+0x54]: state byte +0x1dc (0x8154f3 cmp byte), vehicle ref +0x1e4, kind byte +0x1ec  [EXE]
 *   ZHeli = [rules+0x1e4] when its vtable is 0xbcb33c, else the table entity with that vtable (ZHeli RTTI)   [EXE: RTTI]
 *     body position: kle_node([heli+4]) = world place of the scene node (+0x24 / parent +0x50, as for actors)  GUESS that a ZHeli's
 *       [obj+4] is its scene node like an actor's
 *     control state dwords +0x7d8 / +0x7dc (heli_call.md 'ZHeli control state +0x7d0..0x86c')   GUESS: meaning unknown, printed as hex
 *       NOTE (re-read 2026-10-19): 0x78a200, the ctor of ZVehicleEffects (vtable 0xbc0f74), clears ITS +0x7d8 / +0x7dc; a ZHeli (bases
 *       ZHavokLnkObj / ZLNKOBJ / ZSTDOBJ / ZGEOM) is NOT a ZVehicleEffects, so ctl7d8 / ctl7dc on the ZHeli stay a GUESS.
 *   fx    = the chopper's ZVehicleEffects controller (bases ZBaseConRout / ZEventBase), the 'this' of the ProjectileHit handler
 *     0x7a71e0 (vtable slot 26 of 0xbc0f74) and so of the health model 0x412430 (called at 0x7a739b with ecx = that same esi).   [EXE: CERTAIN]
 *     It is a CONTROLLER on the vehicle's ZGROUP, not the ZHeli and not a component inside it: its init 0x7c6f00 (vtable slot 13) takes
 *     the owner entity slot [fx+0x24], walks the slot's children ([slot+0x40], then the sibling word [slot+0x5e]) for a ZHavokCar
 *     (-> [fx+0xb94]) or a ZHeli and stores that ZHeli's object ([slot+0x60]) at [fx+0xb98] (0x7c6fd1).                       [EXE: CERTAIN]
 *     So the ZHeli does not point at it. Controllers are found through vtable +0xfc of the ZGROUP object (0x4539c0: a walk of the
 *     entity's controller ids through a global registry [0xe0ff88], by class NAME string 'ZVehicleEffects'); that walk is NOT redone
 *     here. REACH, the same way the rout is reached: an object with vtable 0xbc0f74 whose [+0xb98] equals the ZHeli pointer - first in the
 *     entity table (3 s), with Probe=2 also by the bounded heap scan (10 s, 64 MB, only while no fx is known for that ZHeli).
 *     The link [fx+0xb98] == ZHeli is CERTAIN from the code; that the controller lies in a scanned region is a GUESS (hp=? says not).
 *     hp  = float [fx+0x5ec] (health: 0x412430 tests, subtracts and stores it; 0x412674 at <= 15 % of max sends EscVehicleState 1)   [EXE]
 *     max = float [fx+0xba0] (ctor 0x78a2f5 writes it; 0x412690 and 0x412756 compare with it)                                      [EXE]
 *     blow= dword [fx+0xbfc] (ctor 0x78a323 writes 4 = Definite; 0x4127c3 'cmp dword [esi+0xbfc], 4' before the blow-up 0x877f30)   [EXE]
 *     A health change of >= 1 % of max counts as a CHANGE (the line is then written at once, under the 5 lines a second limit).
 */
#define KLHP_ROUT_VT   0x00bcd5cc             /* ZHeliFlyBehaviourRout vtable (debug/heli_call_read.py rtti) */
#define KLHP_HELI_VT   0x00bcb33c             /* ZHeli vtable */
#define KLHP_FX_VT     0x00bc0f74             /* ZVehicleEffects vtable (RTTI; stamped by its ctor 0x78a222) */
#define KLHP_MAX       8
#define KLHP_CAP       3000                   /* lines in all per process */

static struct {
    int on, scan_heap, told_none, told_on, lines;
    DWORD rout[KLHP_MAX], heli[KLHP_MAX]; int nr, nh;
    DWORD tab, scan_at, said_at, chg_at, heap_at;
    DWORD sig[KLHP_MAX * 2];                      /* the last signature per object index (the last slot: the car state alone) */
    DWORD fx[KLHP_MAX], fx_at[KLHP_MAX], fx_heap_at;   /* the ZVehicleEffects found per ZHeli index; last table scan per index; last heap scan */
    float hp[KLHP_MAX];                           /* the health last written per ZHeli index */
} klhp;

static float klhp_f(DWORD bits) { float f; memcpy(&f, &bits, 4); return f; }

/* the ZVehicleEffects of a ZHeli: vtable 0xbc0f74 and [+0xb98] == the ZHeli object. Entity table first (a table scan reads up to 640 KB:
   not more than once in 3 s per ZHeli), then with heap = Probe 2 the committed RW private pages (64 MB at most, once in 10 s). */
static DWORD klhp_find_fx(DWORD heli, int heap)
{
    DWORD now = GetTickCount(), p, tab, i;
    if (!heli) return 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) return 0;
    for (i = 0; i < 0x10000; i += 64) {
        DWORD blk[64 * 32], k;
        if (!klh_rd(tab + i * 0x80, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4];
            if (o >= 0x10000 && klh_rd32(o) == KLHP_FX_VT && klh_rd32(o + 0xb98) == heli) return o;
        }
    }
    if (heap && (!klhp.fx_heap_at || now - klhp.fx_heap_at >= 10000)) {
        SYSTEM_INFO si; BYTE *a; MEMORY_BASIC_INFORMATION mb; static BYTE buf[0x10000]; SIZE_T done = 0;
        klhp.fx_heap_at = now;
        GetSystemInfo(&si);
        for (a = (BYTE *)si.lpMinimumApplicationAddress; a < (BYTE *)si.lpMaximumApplicationAddress && done < (64u << 20); ) {
            if (!VirtualQuery(a, &mb, sizeof mb)) break;
            if (mb.State == MEM_COMMIT && mb.Type == MEM_PRIVATE && mb.Protect == PAGE_READWRITE) {
                BYTE *q = (BYTE *)mb.BaseAddress, *e = q + mb.RegionSize;
                for (; q < e; q += sizeof buf) {
                    SIZE_T n = (SIZE_T)(e - q) < sizeof buf ? (SIZE_T)(e - q) : sizeof buf, k;
                    if (!klh_rd((DWORD_PTR)q, buf, n)) continue;
                    done += n;
                    for (k = 0; k + 4 <= n; k += 4) if (*(DWORD *)(buf + k) == KLHP_FX_VT) {
                        DWORD o = (DWORD)(DWORD_PTR)(q + k);
                        if (klh_rd32(o + 0xb98) == heli) return o;
                    }
                }
            }
            a = (BYTE *)mb.BaseAddress + mb.RegionSize;
        }
    }
    return 0;
}

static void klhp_scan_table(void)
{
    DWORD p, tab, slot, i, blk[64 * 32]; int nr = 0, nh = 0;
    klhp.nr = klhp.nh = 0;
    if (!(p = klh_rd32((DWORD_PTR)KLH_VA(KLE_ENTS))) || !(p = klh_rd32(p + 0xc)) || !(tab = klh_rd32(p + 0xc))) { klhp.tab = 0; return; }
    klhp.tab = tab;
    for (i = 0; i < 0x10000; i += 64) {               /* 64 slots (8 KB) a read; a failed read ends the table */
        DWORD k;
        slot = tab + i * 0x80;
        if (!klh_rd(slot, blk, sizeof blk)) break;
        for (k = 0; k < 64; k++) {
            DWORD o = blk[k * 32 + 0x60 / 4], vt;
            if (o < 0x10000 || !klh_rd(o, &vt, 4)) continue;
            if (vt == KLHP_ROUT_VT && nr < KLHP_MAX) klhp.rout[nr++] = o;
            else if (vt == KLHP_HELI_VT && nh < KLHP_MAX) klhp.heli[nh++] = o;
        }
    }
    klhp.nr = nr; klhp.nh = nh;
}

static void klhp_scan_heap(void)
{   /* Probe=2: dwords equal to the rout vtable at 4-byte alignment in committed RW private pages, 64 MB at most */
    SYSTEM_INFO si; BYTE *a; MEMORY_BASIC_INFORMATION mb; static BYTE buf[0x10000]; SIZE_T done = 0; int nr = klhp.nr;
    GetSystemInfo(&si);
    for (a = (BYTE *)si.lpMinimumApplicationAddress; a < (BYTE *)si.lpMaximumApplicationAddress && done < (64u << 20) && nr < KLHP_MAX; ) {
        if (!VirtualQuery(a, &mb, sizeof mb)) break;
        if (mb.State == MEM_COMMIT && mb.Type == MEM_PRIVATE && mb.Protect == PAGE_READWRITE) {
            BYTE *q = (BYTE *)mb.BaseAddress, *e = q + mb.RegionSize;
            for (; q < e && nr < KLHP_MAX; q += sizeof buf) {
                SIZE_T n = (SIZE_T)(e - q) < sizeof buf ? (SIZE_T)(e - q) : sizeof buf, k;
                if (!klh_rd((DWORD_PTR)q, buf, n)) continue;
                done += n;
                for (k = 0; k + 4 <= n; k += 4) if (*(DWORD *)(buf + k) == KLHP_ROUT_VT) {
                    DWORD o = (DWORD)(DWORD_PTR)(q + k), g = klh_rd32(o + 0x74);
                    int dup = 0, j;
                    if (g && g < 0x10000) continue;               /* a goal pointer is a heap address or 0 */
                    for (j = 0; j < nr; j++) if (klhp.rout[j] == o) dup = 1;
                    if (!dup && nr < KLHP_MAX) klhp.rout[nr++] = o;
                }
            }
        }
        a = (BYTE *)mb.BaseAddress + mb.RegionSize;
    }
    klhp.nr = nr;
}

static void klhp_line(DWORD now, int idx, DWORD rout, DWORD heli, DWORD rules, int due, DWORD fx)
{
    DWORD goal = 0, g8 = 0, sq = 0, a8c = 0, a90 = 0, a154 = 0, c7d8 = 0, c7dc = 0, blow = 0, sig; int changed, hpchg = 0;
    float hp = 0, hpmax = 0; int havehp = 0;
    BYTE st = 0, kind = 0, a_bc = 0, started = 0, blocked = 0; DWORD veh = 0; float pos[3] = { 0, 0, 0 }; int havepos = 0;
    if (rout) {
        goal = klh_rd32(rout + 0x74); sq = klh_rd32(rout + 0x38);
        if (goal) g8 = klh_rd32(goal + 8);
        klh_rd(rout + 0x40, &started, 1); klh_rd(rout + 0x41, &blocked, 1);
        if (sq) { a8c = klh_rd32(sq + 0x8c); a90 = klh_rd32(sq + 0x90); a154 = klh_rd32(sq + 0x154); klh_rd(sq + 0xbc, &a_bc, 1); }
    }
    if (rules) { klh_rd(rules + 0x1dc, &st, 1); klh_rd(rules + 0x1ec, &kind, 1); veh = klh_rd32(rules + 0x1e4); }
    if (heli) {
        c7d8 = klh_rd32(heli + 0x7d8); c7dc = klh_rd32(heli + 0x7dc);
        havepos = kle_node(klh_rd32(heli + 4), pos, 0);
    }
    if (fx) {                                          /* health model of the ZVehicleEffects: read-only, klh_rd32 never faults */
        hp = klhp_f(klh_rd32(fx + 0x5ec)); hpmax = klhp_f(klh_rd32(fx + 0xba0)); blow = klh_rd32(fx + 0xbfc);
        havehp = klb_finite(hp) && klb_finite(hpmax) && hpmax > 0;
        if (havehp && idx < KLHP_MAX) hpchg = (hp > klhp.hp[idx] ? hp - klhp.hp[idx] : klhp.hp[idx] - hp) >= 0.01f * hpmax;   /* >= 1 % of max */
    }
    sig = goal * 31u + g8 * 17u + sq * 13u + a8c * 7u + a90 * 5u + a154 * 3u + a_bc + st * 101u + c7d8 * 19u + c7dc * 23u + started * 29u + blocked * 37u + kind * 41u + fx * 43u + blow * 47u;
    changed = hpchg || sig != klhp.sig[idx];                    /* the signature holds every non-position field */
    if (changed) { if (now - klhp.chg_at < 200) return; klhp.chg_at = now; }   /* 5 change lines a second at most; an unwritten change comes next tick */
    else if (!due) return;                             /* otherwise one line a second */
    klhp.sig[idx] = sig; if (havehp && idx < KLHP_MAX) klhp.hp[idx] = hp;
    if (klhp.lines >= KLHP_CAP) return;
    klhp.lines++;
    /* the called vehicle's vtable and place next to the ZHeli's (run N1018_L3: the ZHeli stood still while the call went 1 -> 5):
       equal vtables and places = ref1e4 IS the heli; a different vtable = the rules called another vehicle */
    {
        DWORD vvt = veh ? klh_rd32(veh) : 0, hvt = heli ? klh_rd32(heli) : 0; float vp[3] = { 0, 0, 0 };
        char hps[64] = "hp=?";                        /* '?' = no ZVehicleEffects reached for this ZHeli (see the header 'fx') */
        if (havehp) sprintf(hps, "hp=%.0f/%.0f blow=%lu", hp, hpmax, blow);
        int hv = veh && kle_node(klh_rd32(veh + 4), vp, 0);
        klog("heli: t=%lu %s rout=%08lx goal=%08lx goal8=%lu started=%u blocked=%u sq=%08lx a8c=%08lx a90=%08lx a_bc=%u a154=%08lx | rules=%08lx veh1dc=%u kind=%u ref1e4=%08lx vt=%08lx at %s(%.0f, %.0f, %.0f) | zheli=%08lx vt=%08lx pos=%s(%.0f, %.0f, %.0f) ctl7d8=%08lx ctl7dc=%08lx | fx=%08lx %s",
             now, changed ? "CHANGE" : "tick", rout, goal, g8, started, blocked, sq, a8c, a90, a_bc, a154, rules, st, kind, veh, vvt,
             hv ? "" : "unreadable ", vp[0], vp[1], vp[2], heli, hvt,
             havepos ? "" : "unreadable ", pos[0], pos[1], pos[2], c7d8, c7dc, fx, hps);
    }
}

static void klhp_tick(int game_thread)
{
    DWORD now, rules = 0, gs, rv = 0; int i, due, anyalive = 0;
    if (!klhp.on) return;                               /* Probe=0: nothing below ever runs */
    if (!game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    gs = klh_rd32((DWORD_PTR)KLH_VA(0x0168e9e4));
    if (gs) rules = klh_rd32(gs + 0x54);
    if (rules) rv = klh_rd32(rules + 0x1e4);
    /* re-validate the known objects each tick (cheap: one dword each); rescan when none is alive, at most every 3 s, 10 s for the heap */
    for (i = 0; i < klhp.nr; i++) if (klh_rd32(klhp.rout[i]) == KLHP_ROUT_VT) anyalive = 1;
    for (i = 0; i < klhp.nh; i++) if (klh_rd32(klhp.heli[i]) == KLHP_HELI_VT) anyalive = 1;
    if (!anyalive && (!klhp.scan_at || now - klhp.scan_at >= 3000)) {
        int hadr = klhp.nr + klhp.nh;
        klhp.scan_at = now;
        klhp_scan_table();
        if (klhp.scan_heap && !klhp.nr && (!klhp.heap_at || now - klhp.heap_at >= 10000)) { klhp.heap_at = now; klhp_scan_heap(); }
        if (klhp.nr + klhp.nh != hadr || (!klhp.told_none && !klhp.nr && !klhp.nh)) {
            klog("heli: probe scan: %d ZHeliFlyBehaviourRout, %d ZHeli in the entity table (table %08lx)%s", klhp.nr, klhp.nh, klhp.tab,
                 !klhp.nr ? (klhp.scan_heap ? "; no rout (heap scan on)" : "; no rout: GUESS the routs are controllers, not table entities - Probe=2 scans the heap") : "");
            if (!klhp.nr && !klhp.nh) klhp.told_none = 1;
        }
    }
    if (rv && klh_rd32(rv) == KLHP_HELI_VT) {            /* the rules' own vehicle first: it is the one the call acts on */
        int have = 0; for (i = 0; i < klhp.nh; i++) if (klhp.heli[i] == rv) have = 1;
        if (!have && klhp.nh < KLHP_MAX) klhp.heli[klhp.nh++] = rv;
    }
    due = !klhp.said_at || now - klhp.said_at >= 1000;
    {
        int n = klhp.nr > klhp.nh ? klhp.nr : klhp.nh, k;
        if (!klhp.nr && !klhp.nh) { klhp_line(now, KLHP_MAX * 2 - 1, 0, 0, rules, due, 0); }          /* the car state alone */
        for (k = 0; k < n && k < KLHP_MAX; k++) {
            DWORD r = k < klhp.nr ? klhp.rout[k] : 0, h = k < klhp.nh ? klhp.heli[k] : 0, fx = 0;
            if (r && klh_rd32(r) != KLHP_ROUT_VT) r = 0;
            if (h && klh_rd32(h) != KLHP_HELI_VT) h = 0;
            if (h) {                                      /* the chopper's ZVehicleEffects: kept while it still points at this ZHeli, else looked for (3 s apart) */
                fx = klhp.fx[k];
                if (fx && (klh_rd32(fx) != KLHP_FX_VT || klh_rd32(fx + 0xb98) != h)) fx = 0;
                if (!fx && (!klhp.fx_at[k] || now - klhp.fx_at[k] >= 3000)) { klhp.fx_at[k] = now; fx = klhp_find_fx(h, klhp.scan_heap); }
                klhp.fx[k] = fx;
            }
            if (r || h) klhp_line(now, k, r, h, rules, due, fx);
        }
        if (due) klhp.said_at = now;
    }
}

static void klhp_init(void)
{
    klhp.on = GetPrivateProfileIntA("Heli", "Probe", 0, klh_ini);       /* the only read of this key; 0 = this file does nothing at all */
    klhp.scan_heap = klhp.on >= 2;
    klhp.on = klhp.on != 0;
    if (klhp.on) klog("heli: probe ON ([Heli] Probe=%d): READ-ONLY 'heli:' lines, 1 a second per object plus changes; re\\heli_call.md 'Handover: HELI4 grep recipe'", klhp.scan_heap ? 2 : 1);
}
