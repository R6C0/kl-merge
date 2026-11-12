/* heapguard.inc (13 Oct) - hero/actor teardown heap assert guard + herowatch diagnostic. Included at the end of
   anp_loader.c. No kl2 code byte is changed (CEG): one VEH exact-site guard, data reads only.

   ---- GUARD 'heap' (ANP_guards.txt heap=veh|off, default veh) ----
   Crash (7 of 19 dumps 11-13 Oct, incl. W's 13 Oct 05:12): int3 at 0x4665dc. 0x466590 = ZWin32Allocator block unlink:
       mov eax,[esp+4]; add eax,-0x10; cmp [eax],0x12345678; jne 0x4665dc (int3; ret)
   Header of a large block (> 0x80 bytes, HeapAlloc'd by 0x7bb2c0): [ptr-0x10] magic 0x12345678, +4/+8 list links,
   +0xc HeapAlloc base. Sole caller: ZWin32Allocator::Free 0x882c30 (vt 0xb8ed54 slot 3):
       0x882c7f push ecx; call 0x466590 (ret 0x882c85); mov edx,[eax+0xc]; ...; HeapFree; 0x882c9b mov al,1; pop esi; ret 4
   All 7 stacks: frame loop -> ZGROUP child teardown 0x76bc6e -> ZFFActor scalar dtor 0x6d6530 (only in ZFFActor's
   vtable 0xbb3bac) -> 0x7c6060 -> ZActor 0x8dd600 -> ZLNKWHANDS 0x7fe1b0 -> ZIKLNKOBJ 0x4b36f0 -> ZLNKOBJ dtor 0x6dd6f0,
   which frees member +0x88 (render instance; its dtor 0x516d70) via 0x6ad680 -> 0x7f05f0 (takes lock 0xe059c0 at
   0x7f05fc, leaves it at 0x7f0659 right after the free returns to 0x7f0657) -> 0x882c30 -> 0x466590.
   Stack at the int3: [esp] 0x882c85, +4 ptr, +8 esi (0x882c30), +0xc ret (0x7f0657), ... +0x28 = esi saved by 0x6ad680
   = the ZLNKOBJ 'this' when +0x2c = 0x6dd751 (the +0x88 free; 0x6dd732 = +0x18, 0x6dd767 = +0x70).
   Guard: on exactly that int3 (code bytes checked) log ptr, its 16 header bytes, the owner, and resume at 0x882c9b with
   esp += 8 (= 0x882c30's normal successful return: al = 1, pop esi, ret 4). The block is not unlinked and not freed:
   one leaked block per hit (0x3bc for an instance), no crash. Callers see a normal Free, so locks stay balanced.

   ---- DIAGNOSTIC 'herowatch' (ANP_guards.txt herowatch=on|off, default on) ----
   1 Hz from the PeekMessage tick (main thread, data reads only): the player (ZFFPlayer, gameMgr[0xdd265c]+0x828[+0x898])
   the buddy body (gameMgr+0x4cf0, written by soldier init 0x615e5d = script+0x40) and every merc body (merc list
   0x1548fd8: count, 16 ZSoldier scripts, body = script+0x40). For each: ZLNKOBJ+0x88 and its header magic. Logs when
   +0x88 changes and the FIRST time a header is wrong, with the scene and the last loader events (recruit, climb, give,
   rappel, grenade, cutdiag, scene). At every scene request (campaign.inc cmp_strncpy) the same check runs at once, plus
   one walk over the node table that checks +0x88 of every ZLNKOBJ-derived object (exact RTTI base-class test).
   Note (static RTTI): ZFFPlayer derives ZPlayer -> ZLNKWHANDS -> ... -> ZLNKOBJ, NOT ZFFActor, so the crashing object
   (ZFFActor) is never the player itself; soldier/buddy bodies are checked for being ZFFActor at run time. */

#define HG_TD_ZLNKOBJ   0xcdea40   /* TypeDescriptor .?AVZLNKOBJ@@ (base class of ZFFActor/ZFFPlayer at offset 0) */
#define HG_VT_FFACTOR   0xbb3bac
#define HG_VT_FFPLAYER  0xbb45f4
#define HG_VT_SCRIPT    0xbd0954   /* ZSoldier@CPPScript */
#define HG_VT_ALLOC     0xb8ed54   /* ZWin32Allocator */
#define HG_MAGIC        0x12345678

/* ---------- last loader events (filled from anp_log, see anp_note) ---------- */
enum { HN_RECRUIT, HN_SQUAD, HN_CLIMB, HN_GIVE, HN_RAPPEL, HN_GRENADE, HN_CUTDIAG, HN_SCENE, HN_N };
static const char *g_hnName[HN_N] = {"squad recruit", "squad", "climb", "give", "rappel", "grenade", "cutdiag", "scene"};
static char g_hnText[HN_N][168]; static DWORD g_hnTick[HN_N];
/* called by anp_log with g_cs held: keeps the last line of each interesting kind (cheap prefix test on the format) */
static void anp_note(const char *fmt, va_list ap) {
    int k;
    if (!fmt) return;
    if (!strncmp(fmt, "SQUAD ", 6)) k = HN_SQUAD;
    else if (!strncmp(fmt, "climb:", 6)) k = HN_CLIMB;
    else if (!strncmp(fmt, "give:", 5)) k = HN_GIVE;
    else if (!strncmp(fmt, "rappel:", 7)) k = HN_RAPPEL;
    else if (!strncmp(fmt, "grenade:", 8)) k = HN_GRENADE;
    else if (!strncmp(fmt, "cutdiag:", 8)) k = HN_CUTDIAG;
    else if (!strncmp(fmt, "scene request", 13) || !strncmp(fmt, "campaign: scene", 15) || !strncmp(fmt, "campaign: front end", 19)) k = HN_SCENE;
    else return;
    char b[168]; _vsnprintf(b, sizeof b - 1, fmt, ap); b[sizeof b - 1] = 0;
    if (k == HN_SQUAD && strstr(b, "recruit")) k = HN_RECRUIT;
    memcpy(g_hnText[k], b, sizeof b); g_hnTick[k] = GetTickCount();
}
static void hw_log_events(const char *tag) {
    char t[HN_N][168]; DWORD tk[HN_N], now = GetTickCount();
    EnterCriticalSection(&g_cs); memcpy(t, g_hnText, sizeof t); memcpy(tk, g_hnTick, sizeof tk); LeaveCriticalSection(&g_cs);
    int any = 0;
    for (int k = 0; k < HN_N; k++) {
        if (!tk[k]) continue;
        any = 1;
        anp_log("%s   last %s (%.1f s ago): %s", tag, g_hnName[k], (now - tk[k]) / 1000.0, t[k]);
    }
    if (!any) anp_log("%s   no recruit/climb/give/rappel/grenade/cutdiag/scene event logged yet", tag);
}

/* ---------- reads ---------- */
static DWORD hg32(DWORD a) { return readable((void*)a, 4) ? *(DWORD*)a : 0; }
static int hg_vt_ok(DWORD vt) { return vt >= 0xb10000 && vt < 0xd40000; }    /* kl2 .rdata */
static void hg_name(const BYTE *o, char *out, int n) {                       /* node name: [o+4] node, +0x6c string */
    out[0] = 0;
    DWORD node = hg32((DWORD)o + 4), s = node ? hg32(node + 0x6c) : 0;
    if (!s || !readable((void*)s, 1)) return;
    int k = 0; const char *p = (const char*)s;
    while (k < n - 1 && readable(p + k, 1) && p[k] >= 32 && p[k] < 127) { out[k] = p[k]; k++; }
    out[k] = 0;
}
static long hg_node_idx(const BYTE *o) {
    DWORD stride, cap; BYTE *base; DWORD node = hg32((DWORD)o + 4);
    if (!node || !node_table(&stride, &cap, &base) || node < (DWORD)base || node >= (DWORD)base + cap * stride) return -1;
    return (long)((node - (DWORD)base) / stride);
}
/* live node object: kl2 vtable, node back-pointer node+0x60 == o (rejects stale pointers to freed/reused memory) */
static int hg_live(const BYTE *o) {
    if (!o || !readable(o, 0x90) || !hg_vt_ok(*(const DWORD*)o)) return 0;
    DWORD node = *(const DWORD*)(o + 4);
    return node && readable((void*)(node + 0x60), 4) && *(DWORD*)(node + 0x60) == (DWORD)o;
}
/* 1 = small-block pool (no header), 0 = heap block (has a header), -1 = allocator not found */
static int hg_pool(DWORD p) {
    DWORD m = hg32(0xdda7a0), A = m ? hg32(m + 4) : 0;
    if (!A || !readable((void*)A, 0x1100) || *(DWORD*)A != HG_VT_ALLOC) return -1;
    if (!*(BYTE*)(A + 0x10f4)) return 0;
    DWORD lo = *(DWORD*)(A + 0x10f0), hi = lo + (*(DWORD*)(A + 0x10ec) << 20);
    return p >= lo && p < hi;
}
enum { HS_NULL, HS_OK, HS_POOL, HS_BAD, HS_UNREAD };
static const char *g_hsName[] = {"null", "ok", "pool", "BAD", "UNREADABLE"};
static int hg_hdr(DWORD p, DWORD *h) {
    h[0] = h[1] = h[2] = h[3] = 0;
    if (!p) return HS_NULL;
    if (hg_pool(p) == 1) return HS_POOL;
    if (!readable((void*)(p - 0x10), 0x10)) return HS_UNREAD;
    memcpy(h, (void*)(p - 0x10), 16);
    return h[0] == HG_MAGIC ? HS_OK : HS_BAD;
}
/* exact RTTI test: does the class of vtable vt have ZLNKOBJ as a base at offset 0 (cached per vtable) */
static DWORD g_hgVt[512]; static BYTE g_hgVtLnk[512]; static int g_hgVtN, g_hgRttiOk = -1;
static int hg_is_lnk(DWORD vt) {
    if (!hg_vt_ok(vt) || g_hgRttiOk != 1) return 0;
    for (int i = 0; i < g_hgVtN; i++) if (g_hgVt[i] == vt) return g_hgVtLnk[i];
    int r = 0;
    DWORD col = hg32(vt - 4), chd = col ? hg32(col + 16) : 0, n = chd ? hg32(chd + 8) : 0, bca = chd ? hg32(chd + 12) : 0;
    for (DWORD i = 0; bca && i < n && i < 64; i++) {
        DWORD bcd = hg32(bca + 4 * i);
        if (bcd && hg32(bcd) == HG_TD_ZLNKOBJ && hg32(bcd + 8) == 0) { r = 1; break; }
    }
    if (g_hgVtN < 512) { g_hgVt[g_hgVtN] = vt; g_hgVtLnk[g_hgVtN] = (BYTE)r; g_hgVtN++; }
    return r;
}

/* ---------- herowatch: watched objects ---------- */
typedef struct { BYTE *obj; DWORD vt, inst, prev[4]; int np, state, badLogged, seen; char role[12], name[40]; long node; } HwEnt;
static HwEnt g_hw[24]; static int g_hwN;
static DWORD g_hwLast; static int g_hwLines, g_hwMainTid;
static volatile LONG g_heapHits;
static void hw_log(const char *fmt, ...) {
    if (g_hwLines > 3000) return;
    if (++g_hwLines == 3000) { anp_log("herowatch: line cap reached, herowatch logging stops"); return; }
    char b[1400]; va_list ap; va_start(ap, fmt); _vsnprintf(b, sizeof b - 1, fmt, ap); va_end(ap); b[sizeof b - 1] = 0;
    anp_log("herowatch: %s", b);
}
static const char *hw_scene(void) { return g_cscene[0] ? g_cscene : "-"; }
static BYTE *hw_player(void) {
    DWORD gm = hg32(0xdd265c);
    if (!gm || !readable((void*)(gm + 0x828), 0x74)) return 0;
    signed char pi = *(signed char*)(gm + 0x898);
    if (pi < 0 || pi > 7) return 0;
    BYTE *P = *(BYTE**)(gm + 0x828 + 4 * pi);
    return (hg_live(P) && *(DWORD*)P == HG_VT_FFPLAYER) ? P : 0;
}
/* the objects to watch now: player, buddy body, merc bodies */
static int hw_current(BYTE **obj, const char **role, int max) {
    int n = 0;
    BYTE *P = hw_player(); if (P && n < max) { obj[n] = P; role[n++] = "player"; }
    DWORD gm = hg32(0xdd265c); BYTE *B = gm ? (BYTE*)hg32(gm + 0x4cf0) : 0;
    if (B && hg_live(B) && n < max) { obj[n] = B; role[n++] = "buddy"; }
    int nl = (int)hg32(0x1548fd8); if (nl < 0) nl = 0; if (nl > 16) nl = 16;
    for (int i = 0; i < nl && n < max; i++) {
        DWORD s = hg32(0x1548fdc + 4 * i);
        if (!s || !readable((void*)s, 0x6f0) || *(DWORD*)s != HG_VT_SCRIPT) continue;
        BYTE *b = (BYTE*)*(DWORD*)(s + 0x40);
        if (!hg_live(b) || hg32((DWORD)b + 0x77c) != s) continue;
        int dup = 0; for (int j = 0; j < n; j++) if (obj[j] == b) dup = 1;
        if (!dup) { obj[n] = b; role[n++] = "merc"; }
    }
    return n;
}
static void hw_bad(HwEnt *e, const DWORD *h, const char *why) {
    hw_log("*** %s '%s' node %ld obj %p (%s) +88 %08lx header %s: %08lx %08lx %08lx %08lx (magic should be 12345678) "
           "scene %s [%s] - the ZLNKOBJ dtor 0x6dd6f0 will hit the heap assert 0x4665dc on this block",
           e->role, e->name, e->node, e->obj, rtti_name(e->obj), e->inst, g_hsName[e->state], h[0], h[1], h[2], h[3], hw_scene(), why);
    hw_log_events("herowatch:");
}
static void hw_check(const char *why, int verbose) {
    BYTE *obj[24]; const char *role[24]; int n = hw_current(obj, role, 24);
    for (int i = 0; i < g_hwN; i++) g_hw[i].seen = 0;
    for (int i = 0; i < n; i++) {
        HwEnt *e = NULL;
        for (int j = 0; j < g_hwN; j++) if (g_hw[j].obj == obj[i]) { e = &g_hw[j]; break; }
        DWORD inst = *(DWORD*)(obj[i] + 0x88), h[4]; int st = hg_hdr(inst, h);
        if (!e) {
            if (g_hwN >= 24) continue;
            e = &g_hw[g_hwN++]; memset(e, 0, sizeof *e);
            e->obj = obj[i]; e->vt = *(DWORD*)obj[i]; e->inst = inst; e->state = st;
            lstrcpynA(e->role, role[i], sizeof e->role); hg_name(obj[i], e->name, sizeof e->name); e->node = hg_node_idx(obj[i]);
            hw_log("watching %s '%s' node %ld obj %p %s +88 %08lx (%s) scene %s", e->role, e->name, e->node, e->obj,
                   rtti_name(e->obj), inst, g_hsName[st], hw_scene());
        } else if (inst != e->inst) {
            hw_log("%s '%s' node %ld obj %p: +88 %08lx -> %08lx (%s) scene %s [%s]", e->role, e->name, e->node, e->obj,
                   e->inst, inst, g_hsName[st], hw_scene(), why);
            if (e->np < 4) e->prev[e->np++] = e->inst; else { memmove(e->prev, e->prev + 1, 12); e->prev[3] = e->inst; }
            e->inst = inst; e->badLogged = 0;
        }
        e->seen = 1; e->state = st;
        if ((st == HS_BAD || st == HS_UNREAD) && !e->badLogged) { e->badLogged = 1; hw_bad(e, h, why); }
        if (verbose) hw_log("  [%s] %s '%s' node %ld obj %p +88 %08lx %s", why, e->role, e->name, e->node, e->obj, inst, g_hsName[st]);
    }
    /* entries no longer present: log once (that is the teardown order), then forget them */
    for (int i = 0; i < g_hwN; ) {
        if (g_hw[i].seen) { i++; continue; }
        hw_log("%s '%s' node %ld obj %p gone (last +88 %08lx %s) scene %s [%s]", g_hw[i].role, g_hw[i].name, g_hw[i].node,
               g_hw[i].obj, g_hw[i].inst, g_hsName[g_hw[i].state], hw_scene(), why);
        g_hw[i] = g_hw[--g_hwN];
    }
}
/* every ZLNKOBJ-derived object in the node table: +0x88 header (one-off, at a scene request) */
static void hw_walk(const char *why) {
    DWORD stride, cap; BYTE *base;
    if (g_hgRttiOk != 1 || !node_table(&stride, &cap, &base) || stride < 0x64) return;
    DWORD t = GetTickCount();
    if (cap > 400000) cap = 400000;
    int whole = readable(base, cap * stride), nl = 0, na = 0, cnt[5] = {0}, shown = 0;
    for (DWORD i = 0; i < cap; i++) {
        BYTE *nd = base + i * stride;
        if (!whole && !readable(nd + 0x60, 4)) break;
        BYTE *o = *(BYTE**)(nd + 0x60);
        if (!o || !readable(o, 0x8c) || !hg_is_lnk(*(DWORD*)o)) continue;
        nl++; if (*(DWORD*)o == HG_VT_FFACTOR) na++;
        DWORD inst = *(DWORD*)(o + 0x88), h[4]; int st = hg_hdr(inst, h); cnt[st]++;
        if ((st == HS_BAD || st == HS_UNREAD) && shown++ < 12) {
            char nm[40]; hg_name(o, nm, sizeof nm);
            hw_log("*** [%s] node %lu obj %p %s '%s' +88 %08lx header %s: %08lx %08lx %08lx %08lx", why, i, o, rtti_name(o), nm,
                   inst, g_hsName[st], h[0], h[1], h[2], h[3]);
        }
    }
    hw_log("[%s] node walk: %d ZLNKOBJ objects (%d ZFFActor) +88: ok %d pool %d null %d BAD %d unreadable %d (%lu ms) scene %s",
           why, nl, na, cnt[HS_OK], cnt[HS_POOL], cnt[HS_NULL], cnt[HS_BAD], cnt[HS_UNREAD], GetTickCount() - t, hw_scene());
}
static void herowatch_init(void) {
    static const DWORD fakeActor = HG_VT_FFACTOR;        /* rtti_name reads the vtable from *obj */
    const char *nm = (const char*)(HG_TD_ZLNKOBJ + 8);
    g_hgRttiOk = readable(nm, 14) && !memcmp(nm, ".?AVZLNKOBJ@@", 14) && !strcmp(rtti_name(&fakeActor), ".?AVZFFActor@@");
    anp_log("herowatch: %s (ZLNKOBJ+0x88 header magic of player / buddy / mercs at 1 Hz and at scene requests; RTTI check %s)",
            g_gHeroWatch ? "on" : "off (ANP_guards.txt herowatch=off)", g_hgRttiOk ? "ok" : "FAILED - node walk off");
}
static void herowatch_tick(DWORD now) {
    if (!g_gHeroWatch) return;
    if (!g_hwMainTid) g_hwMainTid = (int)GetCurrentThreadId();
    if ((int)GetCurrentThreadId() != g_hwMainTid || now - g_hwLast < 1000) return;
    g_hwLast = now;
    hw_check("tick", 0);
}
/* campaign.inc cmp_strncpy: a scene request (QuitGame = MM01, next level, restart); the old scene is torn down after it */
static void herowatch_event(const char *why, const char *id) {
    if (!g_gHeroWatch) return;
    if (g_hwMainTid && (int)GetCurrentThreadId() != g_hwMainTid) return;   /* g_hw is main-thread state */
    char w[48]; _snprintf(w, sizeof w, "%s '%s'", why, id ? id : "?"); w[sizeof w - 1] = 0;
    hw_log("%s: checking watched objects (scene %s, heap guard hits so far %ld)", w, hw_scene(), g_heapHits);
    hw_check(w, 1);
    hw_walk(w);
}

/* ---------- the guard ---------- */
static void heap_guard_report(LONG n, const DWORD *sp, DWORD ptr) {
    DWORD h[4]; int st = hg_hdr(ptr, h);
    DWORD ret2 = sp[3], retF = sp[11]; BYTE *self = (BYTE*)sp[10];
    const char *member = retF == 0x6dd751 ? "+0x88 (render instance)" : retF == 0x6dd732 ? "+0x18" : retF == 0x6dd767 ? "+0x70" : NULL;
    anp_log("heapguard: bad heap header at free (hit %ld) ptr %08lx header %s: %08lx %08lx %08lx %08lx scene %s thread %lu "
            "-> block leaked, Free returns 1 (0x882c9b)", n, ptr, g_hsName[st], h[0], h[1], h[2], h[3], hw_scene(), GetCurrentThreadId());
    if (member) {
        char nm[40]; hg_name(self, nm, sizeof nm);
        anp_log("heapguard:   owner ZLNKOBJ dtor 0x6dd6f0 member %s: this %p (vt now %08lx %s) node %ld '%s' +88 %08lx",
                member, self, hg32((DWORD)self), rtti_name(self), hg_node_idx(self), nm, hg32((DWORD)self + 0x88));
    } else anp_log("heapguard:   caller of 0x882c30 %08lx, frame +0x28 %08lx +0x2c %08lx (not the ZLNKOBJ dtor)", ret2, sp[10], retF);
    /* herowatch cross-reference: was this block or this object watched? */
    for (int i = 0; i < g_hwN; i++) {
        HwEnt *e = &g_hw[i]; int prev = 0;
        for (int k = 0; k < e->np; k++) if (e->prev[k] == ptr) prev = 1;
        if (e->obj == self) anp_log("heapguard:   this = watched %s '%s' (+88 %08lx when last checked, %s)", e->role, e->name, e->inst, g_hsName[e->state]);
        else if (e->inst == ptr) anp_log("heapguard:   ptr is ALSO the current +88 of watched %s '%s' obj %p -> shared instance / double free", e->role, e->name, e->obj);
        if (prev) anp_log("heapguard:   ptr was an EARLIER +88 of watched %s '%s' obj %p (replaced since) -> stale copy freed twice", e->role, e->name, e->obj);
    }
    if (n == 1) {
        char b[700]; int k = 0;
        for (int i = 0; i < 160 && k < 640; i++) {
            if (!readable(sp + i, 4)) break;
            if (sp[i] >= 0x401000 && sp[i] < 0xb10000) k += sprintf(b + k, " %08lx", sp[i]);
        }
        b[k] = 0;
        anp_log("heapguard:   stack:%s", b);
        hw_log_events("heapguard:");
    }
}
static int heap_guard(PEXCEPTION_POINTERS ep) {
    CONTEXT *cx = ep->ContextRecord;
    if ((DWORD)ep->ExceptionRecord->ExceptionAddress != 0x4665dc || (cx->Eip != 0x4665dc && cx->Eip != 0x4665dd)) return 0;
    if (!readable((void*)cx->Esp, 0x34)) return 0;
    const DWORD *sp = (const DWORD*)cx->Esp;
    if (sp[0] != 0x882c85 || cx->Eax != sp[1] - 0x10) return 0;
    static const BYTE unlink[] = {0x8b, 0x44, 0x24, 0x04, 0x83, 0xc0, 0xf0, 0x81, 0x38, 0x78, 0x56, 0x34, 0x12, 0x75, 0x3d};  /* 0x466590 */
    static const BYTE site[] = {0xcc, 0xc3};                                    /* 0x4665dc int3; ret */
    static const BYTE call[] = {0x51, 0xe8, 0x0b, 0x39, 0xbe, 0xff};            /* 0x882c7f push ecx; call 0x466590 */
    static const BYTE tail[] = {0xb0, 0x01, 0x5e, 0xc2, 0x04, 0x00};            /* 0x882c9b mov al,1; pop esi; ret 4 */
    if (!code_byte_ok(0x466590, unlink, sizeof unlink) || !code_byte_ok(0x4665dc, site, sizeof site) ||
        !code_byte_ok(0x882c7f, call, sizeof call) || !code_byte_ok(0x882c9b, tail, sizeof tail)) return 0;
    LONG n = InterlockedIncrement(&g_heapHits);
    if (n <= 10) heap_guard_report(n, sp, sp[1]);
    else if ((n & (n - 1)) == 0) anp_log("heapguard: hits %ld (ptr %08lx)", n, sp[1]);
    cx->Esp += 8;                                        /* drop 0x466590's return address and the pushed ptr */
    cx->Eip = 0x882c9b;                                  /* al = 1; pop esi; ret 4 -> back to 0x882c30's caller */
    return 1;
}
