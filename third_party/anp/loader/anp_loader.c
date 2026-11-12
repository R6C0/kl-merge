// A New Perspective - Dead Men content loader for Kane & Lynch 2: Dog Days
// - Adds new scene IDs: any Scenes/Locations/<ID>/<ID>_Main.zip becomes loadable via LoadScene Scene="<ID>"
// - Diagnostic log: crashes/asserts (with stack scan), file opens
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>

static FILE *g_log;
static CRITICAL_SECTION g_cs;
static char g_dir[MAX_PATH];
/* heapguard.inc / resetguard.inc (13 Oct, included at the end): heap assert guard, herowatch, device-reset guard */
static void anp_note(const char *fmt, va_list ap); static int heap_guard(PEXCEPTION_POINTERS ep);
static void herowatch_tick(DWORD now); static void herowatch_event(const char *why, const char *id); static void resetguard_tick(DWORD now);

static void anp_log(const char *fmt, ...) {
    if (!g_log) return;
    EnterCriticalSection(&g_cs);
    SYSTEMTIME st; GetLocalTime(&st);
    fprintf(g_log, "[%02d:%02d:%02d.%03d] ", st.wHour, st.wMinute, st.wSecond, st.wMilliseconds);
    va_list ap; va_start(ap, fmt); vfprintf(g_log, fmt, ap); va_end(ap);
    va_start(ap, fmt); anp_note(fmt, ap); va_end(ap);   /* heapguard.inc: last loader events for herowatch */
    fputc('\n', g_log); fflush(g_log);
    LeaveCriticalSection(&g_cs);
}

static int g_logFiles = 1;

/* ---------- scene id -> zip resolver ---------- */
static char g_paths[64][128];
static int g_npaths;

const char * __cdecl anp_resolve(const char *id) {
    char path[MAX_PATH], rel[128];
    if (!id || !id[0]) return NULL;
    for (int i = 0; i < g_npaths; i++) {
        // cached
        const char *p = g_paths[i];
        if (strncmp(p + 10, id, strlen(id)) == 0 && p[10 + strlen(id)] == '/') return p;
    }
    _snprintf(rel, sizeof rel, "Locations/%s/%s_Main.zip", id, id);
    _snprintf(path, sizeof path, "%s\\Scenes\\%s", g_dir, rel);
    DWORD a = GetFileAttributesA(path);
    if (a == INVALID_FILE_ATTRIBUTES) { anp_log("resolve '%s': not found (%s)", id, path); return NULL; }
    if (g_npaths < 64) { strcpy(g_paths[g_npaths], rel); anp_log("resolve '%s' -> %s", id, rel); return g_paths[g_npaths++]; }
    return NULL;
}

__attribute__((naked)) void anp_resolve_stub(void) {
    __asm__ volatile(
        "push %esi\n\t"
        "call _anp_resolve\n\t"
        "add $4, %esp\n\t"
        "pop %edi\n\t"
        "pop %esi\n\t"
        "pop %ebx\n\t"
        "ret\n\t");
}

/* ---------- CEG: every kl2.exe code byte the loader changes goes through code_write() ----------
   kl2.exe is a Valve CEG build: ~85% of .text and 66% of .rdata are hashed (kl-merge klhook/klranges.h) and in a real
   session (Arcade / Fragile Alliance started from the menu) a changed hashed byte ends the game with
   ExitProcess(0x8000dead). Import slots, .data and the heap are not hashed. The default build changes NO code byte:
   every old code patch is replaced by a vectored-exception guard, a watchdog check or converter-side data, and is only
   installed again with an explicit legacy switch (ANP_guards.txt, see guards_config). code_write() records each write;
   ceg_report() lists them at start-up ("CEG: kl2.exe code bytes changed by ANP_Loader: none" in the default build). */
typedef struct { DWORD at; int len; char what[40]; } CodePatch;
static CodePatch g_cpatch[16]; static volatile LONG g_ncpatch; static int g_cegListed;
static int code_write(DWORD at, const void *bytes, int len, const char *what) {
    DWORD old;
    if (!VirtualProtect((void*)at, len, PAGE_EXECUTE_READWRITE, &old)) return 0;
    memcpy((void*)at, bytes, len);
    VirtualProtect((void*)at, len, old, &old);
    FlushInstructionCache(GetCurrentProcess(), (void*)at, len);
    LONG i = InterlockedIncrement(&g_ncpatch) - 1;
    if (i < 16) { g_cpatch[i].at = at; g_cpatch[i].len = len; lstrcpynA(g_cpatch[i].what, what, sizeof g_cpatch[i].what); }
    if (g_cegListed) anp_log("CEG WARNING: kl2 code patched after start-up: %08lx+%d (%s)", at, len, what);
    return 1;
}
static int patch_jmp(DWORD at, void *to, int len, const char *what) {
    unsigned char b[16];
    if (len < 5 || len > 16) return 0;
    b[0] = 0xE9; *(DWORD*)(b + 1) = (DWORD)to - (at + 5);
    for (int i = 5; i < len; i++) b[i] = 0x90;
    return code_write(at, b, len, what);
}
/* rewrite the rel32 operand of the E8 call at callAt so it calls 'to' */
static int patch_call(DWORD callAt, void *to, const char *what) {
    DWORD rel = (DWORD)to - (callAt + 5);
    return code_write(callAt + 1, &rel, 4, what);
}

/* ---------- crash / assert logging ---------- */
/* readable() never faults (IsBadReadPtr raises exceptions internally, which re-entered this VEH) */
static int readable(const void *p, size_t n) {
    MEMORY_BASIC_INFORMATION mi;
    const BYTE *a = (const BYTE*)p, *e = a + n;
    if ((DWORD)a < 0x10000 || e < a) return 0;
    while (a < e) {
        if (!VirtualQuery(a, &mi, sizeof mi)) return 0;
        if (mi.State != MEM_COMMIT || (mi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return 0;
        a = (const BYTE*)mi.BaseAddress + mi.RegionSize;
    }
    return 1;
}
static volatile LONG g_inVeh = 0;
static const char *rtti_name(const void *obj);
static void dump_nodes(void);
static void dump_gui(void);
static int node_table(DWORD *stride, DWORD *cap, BYTE **base);
static long node_of(const void *obj) {
    DWORD stride, cap; BYTE *base;
    if (!obj || !node_table(&stride, &cap, &base)) return -1;
    for (DWORD i = 0; i < cap && i < 400000; i++) { BYTE *nd = base + i * stride; if (!readable(nd + 0x60, 4)) break; if (*(const void**)(nd + 0x60) == obj) return (long)i; }
    return -1;
}
static void log_obj_strings(const char *tag, const BYTE *o, int n);
static int climb_veh(PEXCEPTION_POINTERS ep);   /* climb.inc: fault inside a climb guard -> resume after it */
static int ceg_guard_veh(PEXCEPTION_POINTERS ep);   /* exact-site guards that replace the old code patches (CEG) */
static void wrap_watch(DWORD busyMs);               /* watchdog: text word-wrap stall check (replaces 0x8a40fe patch) */
/* sound counters (stats line, snd_stats_thread) */
static volatile LONG g_divGuard, g_nullList;
/* ---- v4BonesLights guard (M09 crash 0x577e08, 11 Oct). Default on; <DD>\ANP_no_boneslights_guard.txt turns it off.
   The shader-constant setter ZRenderBinderContextD3DFX slot 1 (0x7d3dd0), case 0x46 = v4BonesLights (0x7d57c2), loads
   edi = [renderCtx+0x3d0] (bone-space light block, 0x70 bytes), treats only 0x20 as "no lights" (= a null light object
   + 0x20, the engine's own fallback) and calls the vec3*mat3 helper 0x577df0 with edx = edi: a 0 there faults at
   0x577e08. Only ZRenderEntryBones/BonesRigid/Deformer write +0x3d0, so a skinned/rigid material drawn before any of
   them (or a bone-instancing record with lights 0) leaves it 0. The guard needs no code patch (CEG-hashed .text is not
   touched): on that exact fault it hands the in-flight call a zeroed light block (edx/edi, the cache 0xf1b244), sets
   ctx+0x3d0 = 0x20 so later draws take the engine's no-lights path, and logs once which draw item / render entry /
   node it was (0x856a60 frame: ret slot R = 0x856ae8, [R+0xc] = draw item, [R+0x10] = ctx, [R+0x40] = render entry). */
static int g_guardBonesLights = 1;
static volatile LONG g_bonesLightsHits;
static __attribute__((aligned(16))) BYTE g_noLights[0x80];
static void boneslights_diag(CONTEXT *cx, BYTE *ctx) {
    DWORD *sp = (DWORD*)cx->Esp, *R = NULL;
    for (int i = 0; i < 0x400; i++) {
        if (!readable(sp + i, 0x48)) break;
        if (sp[i] == 0x856ae8 && sp[i + 4] == (DWORD)ctx) { R = sp + i; break; }
    }
    anp_log("  boneslights: ctx %p +3d4(k)=%08lx  0x856a60 frame %s (esp+%lx)", ctx, readable(ctx + 0x3d4, 4) ? *(DWORD*)(ctx + 0x3d4) : 0,
            R ? "found" : "NOT found", R ? (DWORD)((BYTE*)R - (BYTE*)sp) : 0);
    if (R) {
        BYTE *inst = (BYTE*)R[3], *entry = (BYTE*)R[0x10], *a1 = (BYTE*)R[1];
        anp_log("  boneslights: draw item %p %s | arg1 %p %s | entry %p %s node %ld", inst, rtti_name(inst), a1, rtti_name(a1),
                entry, rtti_name(entry), node_of(entry));
        if (readable(entry, 0x260)) {
            BYTE *geom = *(BYTE**)(entry + 0x198);
            DWORD frame = readable((void*)0xef4d80, 4) ? *(DWORD*)0xef4d80 : 0;
            DWORD inset = (frame < 64 && readable(entry + 0x15c + frame * 4, 4)) ? *(DWORD*)(entry + 0x15c + frame * 4) : 0;
            anp_log("  boneslights: entry+198 %p %s node %ld | +258 %08lx +25c %08lx | instset[%lu] %08lx", geom, rtti_name(geom),
                    node_of(geom), *(DWORD*)(entry + 0x258), *(DWORD*)(entry + 0x25c), frame, inset);
            if (inset && readable((void*)inset, 8)) {
                DWORD n = *(DWORD*)inset;
                anp_log("  boneslights: instset count %lu rec0+34 %08lx", n, readable((void*)(inset + 4 + 0x34), 4) ? *(DWORD*)(inset + 4 + 0x34) : 0);
            }
            log_obj_strings("entry", entry, 0x260);
            if (readable(geom, 0x80)) log_obj_strings("geom", geom, 0x80);
        }
    }
    /* every RTTI object on the stack up to the frame (draw item, material instance, entry...) */
    int lim = R ? (int)(R - sp) + 0x20 : 0x200;
    for (int i = 0, shown = 0; i < lim && shown < 24; i++) {
        if (!readable(sp + i, 4)) break;
        const char *nm = rtti_name((void*)sp[i]);
        if (nm[0] == '.') { anp_log("  boneslights: esp+%03x %08lx %s", i * 4, sp[i], nm); shown++; }
    }
}
static int boneslights_guard(PEXCEPTION_POINTERS ep) {
    CONTEXT *cx = ep->ContextRecord;
    if (!g_guardBonesLights || ep->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION || cx->Eip != 0x577e08 ||
        cx->Edx != 0 || cx->Edi != 0 || !readable((void*)cx->Esp, 0x14) || *(DWORD*)(cx->Esp + 0xc) != 0x7d57ec) return 0;
    static const BYTE expect[3] = {0xd9, 0x02, 0xd8};      /* fld [edx]; fmul ... */
    BYTE *ctx = (BYTE*)(cx->Esi - 0x9c);                   /* 0x7d57c8: add esi,0x9c; 0x577df0 keeps esi/edi */
    if (memcmp((void*)0x577e08, expect, 3) || !readable(ctx + 0x3d0, 8) || *(DWORD*)(ctx + 0x3d0) != 0) return 0;
    LONG n = InterlockedIncrement(&g_bonesLightsHits);
    if (n <= 3) {
        anp_log("boneslights guard: v4BonesLights with ctx+3d0 = 0 (hit %ld) -> zero light block, ctx+3d0 = 0x20", n);
        if (n == 1) boneslights_diag(cx, ctx);
    } else if ((n & (n - 1)) == 0) anp_log("boneslights guard: hits %ld", n);
    cx->Edx = cx->Edi = (DWORD)g_noLights;
    *(DWORD*)0xf1b244 = (DWORD)g_noLights;
    *(DWORD*)(ctx + 0x3d0) = 0x20;
    return 1;
}
static LONG CALLBACK veh(PEXCEPTION_POINTERS ep) {
    DWORD code = ep->ExceptionRecord->ExceptionCode;
    if (code == EXCEPTION_ACCESS_VIOLATION && boneslights_guard(ep)) return EXCEPTION_CONTINUE_EXECUTION;
    /* before the generic divide guard: the snd exact-site guard must see 0x44668b first */
    if ((code == EXCEPTION_ACCESS_VIOLATION || code == EXCEPTION_BREAKPOINT || code == EXCEPTION_INT_DIVIDE_BY_ZERO) &&
        ceg_guard_veh(ep)) return EXCEPTION_CONTINUE_EXECUTION;
    if (code == EXCEPTION_INT_DIVIDE_BY_ZERO) {   /* sound streaming setup with unconverted DM records: divisor -> 1 */
        CONTEXT *cx = ep->ContextRecord; unsigned char *ip = (unsigned char*)cx->Eip;
        if (cx->Eip >= 0x446600 && cx->Eip < 0x4b3000 && readable(ip, 4) && ip[0] == 0xf7) {
            static int dz; int ok = 0;
            if (ip[1] == 0x74 && ip[2] == 0x24) { DWORD *p = (DWORD*)(cx->Esp + ip[3]); if (readable(p, 4)) { *p = 1; ok = 1; } }
            else if ((ip[1] & 0xf8) == 0xf0) {            /* div reg */
                DWORD *regs[8] = {&cx->Eax, &cx->Ecx, &cx->Edx, &cx->Ebx, &cx->Esp, &cx->Ebp, &cx->Esi, &cx->Edi};
                *regs[ip[1] & 7] = 1; ok = 1;
            }
            if (ok) { InterlockedIncrement(&g_divGuard); if (dz++ < 20) anp_log("div-by-zero guard at %08lx (sound record) -> divisor 1", cx->Eip); return EXCEPTION_CONTINUE_EXECUTION; }
        }
    }
    if (code == EXCEPTION_ACCESS_VIOLATION && (DWORD)ep->ExceptionRecord->ExceptionAddress == 0x900ff8 &&
        ep->ContextRecord->Eip == 0x900ff8 && ep->ContextRecord->Ecx == 0) {
        /* sound-list GetEntry(rec=ecx, idx) (0x900ff0, ret 4) called with rec NULL: an audio definition whose .SND
           offset is not a sound list in this level's bank (ZDllSoundWintel vt+0x58 returned 0; M01 v3 pause menu).
           Nothing is pushed before 0x900ff8, so [esp] is the return address: return 0 ("no such entry"), which every
           caller already handles. */
        CONTEXT *cx = ep->ContextRecord; const BYTE *ip = (const BYTE*)0x900ff8;
        static const BYTE expect[4] = {0x66, 0x3b, 0x41, 0x18};          /* cmp ax, [ecx+0x18] */
        if (readable(ip, 4) && memcmp(ip, expect, 4) == 0 && readable((void*)cx->Esp, 8)) {
            static DWORD last, n;
            DWORD ret = *(DWORD*)cx->Esp, now = GetTickCount();
            n++; InterlockedIncrement(&g_nullList);
            if (n == 1 || now - last >= 1000) {
                last = now;
                anp_log("null sound-list guard: 0x900ff0(NULL, idx %lu) from %08lx returned 0 (id ~%08lx, hits %lu)",
                        *(DWORD*)(cx->Esp + 4) & 0xff, ret, cx->Edx & ~0xffu, n);
            }
            cx->Eax = 0; cx->Eip = ret; cx->Esp += 8;
            return EXCEPTION_CONTINUE_EXECUTION;
        }
    }
    if (code == 0xE0A0B001 && ep->ExceptionRecord->NumberParameters >= 1) {   /* arm hardware write watch (DR0) */
        CONTEXT *cx = ep->ContextRecord;
        cx->Dr0 = (DWORD)ep->ExceptionRecord->ExceptionInformation[0];
        cx->Dr7 = (cx->Dr7 & ~0xF0003u) | 0x1 | (1u << 16) | (3u << 18);
        cx->ContextFlags |= CONTEXT_DEBUG_REGISTERS;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (code == EXCEPTION_SINGLE_STEP && (ep->ContextRecord->Dr6 & 1)) {
        static int hits; CONTEXT *cx = ep->ContextRecord;
        if (hits++ < 40) {
            DWORD a = cx->Dr0, v = readable((void*)a, 4) ? *(DWORD*)a : 0;
            char sb[600]; int k = 0; DWORD *sp = (DWORD*)cx->Esp;
            for (int i = 0; i < 256 && k < 560; i++) { if (!readable(sp + i, 4)) break; if (sp[i] >= 0x401000 && sp[i] < 0xb10000) k += sprintf(sb + k, " %08lx", sp[i]); }
            sb[k] = 0;
            anp_log("WATCH write [%08lx] = %08lx (%s node %ld) at eip %08lx stack:%s", a, v, rtti_name((void*)v), node_of((void*)v), cx->Eip, sb);
        }
        cx->Dr6 = 0;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (climb_veh(ep)) return EXCEPTION_CONTINUE_EXECUTION;
    if (code != EXCEPTION_ACCESS_VIOLATION && code != EXCEPTION_BREAKPOINT && code != EXCEPTION_ILLEGAL_INSTRUCTION &&
        code != EXCEPTION_STACK_OVERFLOW && code != EXCEPTION_INT_DIVIDE_BY_ZERO && code != EXCEPTION_PRIV_INSTRUCTION)
        return EXCEPTION_CONTINUE_SEARCH;
    static int count = 0;
    if (InterlockedExchange(&g_inVeh, 1)) return EXCEPTION_CONTINUE_SEARCH;
    if (count++ > 20) { g_inVeh = 0; return EXCEPTION_CONTINUE_SEARCH; }
    CONTEXT *c = ep->ContextRecord;
    anp_log("EXCEPTION %08lx at %08lx (info %08lx %08lx)", code, (DWORD)ep->ExceptionRecord->ExceptionAddress,
         ep->ExceptionRecord->NumberParameters > 0 ? (DWORD)ep->ExceptionRecord->ExceptionInformation[0] : 0,
         ep->ExceptionRecord->NumberParameters > 1 ? (DWORD)ep->ExceptionRecord->ExceptionInformation[1] : 0);
    {   /* which module faulted, and on which thread (11 Oct: a crash at 0x695e199b off the main thread had no name) */
        HMODULE fm = NULL; char mn[MAX_PATH] = "?";
        if (GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                               (LPCSTR)ep->ExceptionRecord->ExceptionAddress, &fm) && fm) {
            if (!GetModuleFileNameA(fm, mn, sizeof mn)) strcpy(mn, "?");
        }
        const char *bn = strrchr(mn, '\\');
        anp_log("  module %s+%lx thread %lu", bn ? bn + 1 : mn,
                fm ? (DWORD)ep->ExceptionRecord->ExceptionAddress - (DWORD)fm : 0, GetCurrentThreadId());
    }
    anp_log("  eax=%08lx ebx=%08lx ecx=%08lx edx=%08lx esi=%08lx edi=%08lx ebp=%08lx esp=%08lx",
         c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    char buf[2048]; int n = 0; DWORD *sp = (DWORD*)c->Esp;
    for (int i = 0; i < 1024 && n < 2000; i++) {
        DWORD v;
        if (((DWORD)(sp + i) & 0xfff) == 0 || i == 0) { if (!readable(sp + i, 4)) break; }
        v = sp[i];
        if (v >= 0x401000 && v < 0xb10000) n += sprintf(buf + n, " %08lx", v);
    }
    buf[n] = 0;
    anp_log("  stack:%s", buf);
    // dump a few strings pointed to by registers (often asserts carry messages)
    DWORD regs[] = {c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi};
    for (int i = 0; i < 6; i++) {
        const char *s = (const char*)regs[i];
        if (readable(s, 96) && s[0] >= 32 && s[0] < 127) {
            char t[96]; int k = 0;
            while (k < 95 && s[k] >= 32 && s[k] < 127) { t[k] = s[k]; k++; }
            t[k] = 0; if (k >= 4) anp_log("  reg%d str: %s", i, t);
        }
    }
    {   /* RTTI of objects in registers */
        DWORD rr[] = {c->Eax, c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi};
        const char *rn[] = {"eax", "ebx", "ecx", "edx", "esi", "edi"};
        for (int i = 0; i < 6; i++) {
            const char *nm = rtti_name((void*)rr[i]);
            if (nm[0] == '.') anp_log("  %s -> %s node %ld", rn[i], nm, node_of((void*)rr[i]));
        }
    }
    if ((DWORD)ep->ExceptionRecord->ExceptionAddress == 0x458819) {   /* streamer ReadFile failed */
        BYTE *st = (BYTE*)c->Esi;
        if (readable(st, 0x20)) {
            HANDLE h = *(HANDLE*)(st + 0x18);
            DWORD sz = *(DWORD*)(st + 0xc);
            DWORD lo = 0, hi = 0;
            if (readable(*(void**)(st + 0x10), 8)) { lo = ((DWORD*)*(void**)(st + 0x10))[0]; hi = ((DWORD*)*(void**)(st + 0x10))[1]; }
            char path[MAX_PATH] = "?";
            typedef DWORD (WINAPI *GFPN)(HANDLE, LPSTR, DWORD, DWORD);
            GFPN f = (GFPN)GetProcAddress(GetModuleHandleA("kernel32.dll"), "GetFinalPathNameByHandleA");
            if (f) f(h, path, MAX_PATH, 0);
            const char *msg = (const char*)(c->Esp + 0x20);
            if (readable(msg, 64)) anp_log("  stream error text: %.120s", msg);
            anp_log("  stream read failed: handle %p file %s size %lu off(ptr %p) %08lx:%08lx buf %08lx lasterr %lu",
                    h, path, sz, *(void**)(st + 0x10), hi, lo, *(DWORD*)(st + 0x1c), GetLastError());
        }
    }
    if ((DWORD)ep->ExceptionRecord->ExceptionAddress == 0x6a1ff7) {   /* GUI lookup by name failed */
        BYTE *world = *(BYTE**)(*(DWORD*)0xdd2640 + 0xac);
        if (readable(world + 0x116c, 4)) {
            BYTE *dir = world + 0x116c;
            anp_log("  world=%p dir obj %s vt=%08lx", world, rtti_name(dir), *(DWORD*)dir);
            const DWORD *w = (const DWORD*)dir;
            if (readable(dir, 64)) anp_log("  dir words: %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx", w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7]);
        }
    }
    if ((DWORD)ep->ExceptionRecord->ExceptionAddress == 0x493d95) {   /* actor cover-anim setup: anim lookup returned 0 */
        BYTE *o = (BYTE*)c->Esi;
        if (readable(o, 0x110)) {
            BYTE *ac = *(BYTE**)(o + 0x100);
            anp_log("  cover-setup obj %p ids: 54=%04x 62=%04x a2=%04x 82=%04x c2=%04x  animcomp=%p", o,
                    *(WORD*)(o + 0x54), *(WORD*)(o + 0x62), *(WORD*)(o + 0xa2), *(WORD*)(o + 0x82), *(WORD*)(o + 0xc2), ac);
            if (readable(ac, 0x100)) {
                const DWORD *w = (const DWORD*)ac;
                anp_log("  animcomp %s +84=%08lx words: %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx", rtti_name(ac), w[0x21],
                        w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7]);
                anp_log("  animcomp +60..+9c: %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx | %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx",
                        w[0x18], w[0x19], w[0x1a], w[0x1b], w[0x1c], w[0x1d], w[0x1e], w[0x1f],
                        w[0x20], w[0x21], w[0x22], w[0x23], w[0x24], w[0x25], w[0x26], w[0x27]);
                log_obj_strings("animcomp", ac, 0x100);
            }
            log_obj_strings("cover", o, 0x110);
        }
    }
    g_inVeh = 0;
    return EXCEPTION_CONTINUE_SEARCH;
}

/* ---------- CreateFileA logging via IAT ---------- */
typedef HANDLE (WINAPI *CreateFileA_t)(LPCSTR, DWORD, DWORD, LPSECURITY_ATTRIBUTES, DWORD, DWORD, HANDLE);
static CreateFileA_t real_CreateFileA;
/* ---------- Dead Men .str (IOISNDSTREAM) header virtualisation ----------
   DM header: ... +0x18 u32 tableOffset, +0x1c count, +0x20.. ; DD widened tableOffset to u64,
   shifting the rest by 4.  We serve a converted 0x38-byte header for handles opened on DM .str files. */
typedef BOOL (WINAPI *ReadFile_t)(HANDLE, LPVOID, DWORD, LPDWORD, LPOVERLAPPED);
typedef BOOL (WINAPI *CloseHandle_t)(HANDLE);
static ReadFile_t real_ReadFile;
static CloseHandle_t real_CloseHandle;
static CRITICAL_SECTION g_strCs;
static HANDLE g_strH[32]; static BYTE g_strHdr[32][0x38]; static int g_strUsed[32]; static int g_strFile[32];
/* per DM .str file: IMA-ADPCM (codec 3) entries, which Dog Days cannot read from a stream -> served as silent PCM */
/* Dead Men IMA-ADPCM stream entries are served to Dog Days as 16-bit PCM at virtual offsets >= STR_VBASE
   (same deterministic mapping as tools/strvirt.py, which rewrites the level WHD records). */
#define STR_VBASE 0x60000000LL
/* LIP block.  1483 of Dead Men's 1928 ADPCM stream entries start with a 4 KB LIP block: a 'LIP ' lip-sync chunk
   padded with zeros to 4096 bytes (= ADPCM blocks 0-3 at 1024 bytes; the audio starts at block 4; the meta sample
   count includes those 4 blocks).  Their WHD records say LIP word 4 (= 4 KB LIP block), and Dog Days reads the first
   4 KB of the stream as that block (the first virtual read is 4096 bytes) and the audio after it.  The old loader
   decoded the LIP block as ADPCM, so Dog Days parsed decoded noise as the LIP chunk.
   Virtual layout with lip=1: [0,4096) = the Dead Men LIP block verbatim, [4096,...) = PCM of ADPCM blocks 4...
   tools/sndconv.whd_postfix sets the WHD size/sample fields to match (4096 + (samples - 4*spb)*ch*2); the slot
   (voff spacing) stays the strvirt one, so old and new levels share the mapping.
   lip: 0 = not probed yet, 1 = no LIP block, else the LIP block size in bytes (4096). */
#define LIP_BLOCK 4096
typedef struct { DWORD dataOff, dataSize, metaOff, metaSize, ch, rate, samples, balign, spb, idxPos, pcm, idx; LONGLONG voff; DWORD lip; } StrEnt;
typedef struct { char path[MAX_PATH]; StrEnt *e; int n; StrEnt **byV; HANDLE src; CRITICAL_SECTION cs;
                 int lastEnt, lastBlk; short *blk; BYTE *srcbuf; DWORD tbl, cnt; } StrFile;
static StrFile g_strFiles[8]; static int g_nStrFiles;
static int g_adpcmSilence = 0;   /* WHD records are converted now -> let DM ADPCM streams play */
static int ent_cmp(const void *a, const void *b) {
    const StrEnt *x = (const StrEnt*)a, *y = (const StrEnt*)b;
    if (x->dataOff != y->dataOff) return x->dataOff < y->dataOff ? -1 : 1;
    return x->idx < y->idx ? -1 : x->idx > y->idx;
}
static int str_find(HANDLE h) { for (int i = 0; i < 32; i++) if (g_strUsed[i] && g_strH[i] == h) return i; return -1; }
static int is_dm_str(const char *n) {
    size_t L = strlen(n);
    return L > 4 && _stricmp(n + L - 4, ".str") == 0 && (strstr(n, "Kane and Lynch Dead Men") || strstr(n, "kane and lynch dead men"));
}
static void str_register(HANDLE h, const char *n);
static volatile LONG g_ioQuitTick;
static void io_quit_check(void) {
    DWORD now = GetTickCount();
    if (now - (DWORD)g_ioQuitTick < 2000) return;
    g_ioQuitTick = now;
    char q[MAX_PATH]; _snprintf(q, sizeof q, "%s\\ANP_quit.txt", g_dir);
    if (GetFileAttributesA(q) != INVALID_FILE_ATTRIBUTES) { DeleteFileA(q); TerminateProcess(GetCurrentProcess(), 0); }
}
#include "adpcm.h"
static volatile LONG g_vReads, g_vBytes;
/* sound switches (ANP_sound.txt in the game folder, "key=value" tokens; read once at start):
   lip=1       serve the 4 KB LIP block of Dead Men ADPCM entries verbatim, audio from ADPCM block 4 (see LIP_BLOCK)
               (0 = old behaviour: everything decoded as ADPCM)
   zerofill=1  real reads on Dead Men .str handles that return fewer bytes than asked get the rest zeroed
               (kl2's streamer 0x458750 ignores the byte count, so a read past EOF - e.g. Dead Men's empty
               PC_Eng.str - left stale buffer bytes that the stream then parsed as LIP/audio)
   stats=5     sound stats line every N seconds when something changed (0 = off)
   sndpatch=1  rate-0 guard for the streamed-sound setup (0x446673..0x44668b), 11 Oct: 1 = exact-site VEH (no code
               byte changed; same result as the old stub), 0 = off (the generic VEH divide guard still covers the div
               at 0x44668b, divisor 1), legacy = the old code patch at 0x446673 (CEG-hashed page).
               ANP_guards.txt snd=... overrides this.
   cpu=1       stats line also names threads that were busy >= 90% of the interval (a spinning sound thread)
   Bisect switches (sound round 2, 11 Oct):
   vpcm=1      Dead Men ADPCM stream entries served as decoded PCM (default)
   vpcm=silence  same reads, but every virtual byte is zero (is anything audible without the DM streams?)
   vpcm=off    no virtual serving: reads at the virtual offsets go to the real file (past its end -> zero-filled);
               header/index/meta overlays stay so Dog Days still parses the file
   strhook=0   do not register Dead Men .str handles at all (raw DM headers; may not play / may misparse)
   al=1        hook OpenAL32 imports (IAT; not CEG-hashed) and count sources played, AL_GAIN 0 / > 0, NaN floats,
               buffers, on the stats line ("al:")
   gainfloor=F (needs al=1) every source AL_GAIN below F is raised to F (e.g. 0.2): proof run for "gain 0" levels
   nanfix=1    (needs al=1) NaN/Inf in alSourcef/alSourcefv/alListenerfv values -> 0 (gain -> 1) */
static int g_sndLip = 1, g_sndZeroFill = 1, g_sndStats = 5, g_sndPatch = 1, g_sndCpu = 1;
static int g_vpcm = 1, g_strHook = 1, g_alHook = 1, g_nanFix = 0; static float g_gainFloor = 0.0f;
static volatile LONG g_lipBlocks, g_strReads, g_shortReads, g_zeroBytes, g_vOutside, g_lastVRead;
static void snd_config(void) {
    char p[MAX_PATH]; _snprintf(p, sizeof p, "%s\\ANP_sound.txt", g_dir);
    FILE *f = fopen(p, "r"); char t[64];
    if (!f) return;
    while (fscanf(f, "%63s", t) == 1) {
        char *e = strchr(t, '='); if (!e) continue; *e++ = 0; int v = atoi(e);
        if (!_stricmp(t, "lip")) g_sndLip = v; else if (!_stricmp(t, "zerofill")) g_sndZeroFill = v;
        else if (!_stricmp(t, "stats")) g_sndStats = v;
        else if (!_stricmp(t, "sndpatch")) g_sndPatch = (!_stricmp(e, "legacy") || v == 2) ? 2 : (v ? 1 : 0);
        else if (!_stricmp(t, "cpu")) g_sndCpu = v;
        else if (!_stricmp(t, "vpcm")) g_vpcm = !_stricmp(e, "silence") ? 2 : !_stricmp(e, "off") ? 0 : (v ? 1 : 0);
        else if (!_stricmp(t, "strhook")) g_strHook = v;
        else if (!_stricmp(t, "al")) g_alHook = v;
        else if (!_stricmp(t, "nanfix")) g_nanFix = v;
        else if (!_stricmp(t, "gainfloor")) g_gainFloor = (float)atof(e);
    }
    fclose(f);
}
/* raw Dead Men bytes [at, at+len) of the source file (caller holds sf->cs) */
static DWORD str_raw(StrFile *sf, DWORD at, BYTE *dst, DWORD len) {
    DWORD got = 0;
    if (sf->src == INVALID_HANDLE_VALUE) return 0;
    SetFilePointer(sf->src, (LONG)at, NULL, FILE_BEGIN);
    if (!real_ReadFile(sf->src, dst, len, &got, NULL)) got = 0;
    return got;
}
/* copy virtual bytes [b, b+len) of entry e into dst (caller holds sf->cs) */
static void str_pcm_bytes(StrFile *sf, int ei, DWORD b, BYTE *dst, DWORD len) {
    StrEnt *e = &sf->e[ei];
    DWORD fsz = 2 * e->ch, bbytes = e->spb * fsz, blk0 = 0;
    BYTE *src = sf->srcbuf;
    if (bbytes > 16384 || e->balign > 8192 || !src || !sf->blk) { memset(dst, 0, len); return; }
    if (g_sndLip) {
        if (!e->lip) {                                   /* probe once: data starts with 'LIP ' (same rule as sndconv) */
            BYTE h[8]; e->lip = 1;
            if (LIP_BLOCK % e->balign == 0 && str_raw(sf, e->dataOff, h, 8) == 8 && memcmp(h, "LIP ", 4) == 0) e->lip = LIP_BLOCK;
        }
        if (e->lip == LIP_BLOCK) {
            if (b < LIP_BLOCK) {                         /* the LIP block itself, verbatim */
                DWORD t = LIP_BLOCK - b < len ? LIP_BLOCK - b : len, g = str_raw(sf, e->dataOff + b, dst, t);
                if (g < t) memset(dst + g, 0, t - g);
                /* 2 Dead Men chunks are longer than the 4 KB block (max 5123 bytes): clamp the length kl2 parses */
                if (b <= 4 && b + t >= 8) { DWORD *pl = (DWORD*)(dst + 4 - b); if (*pl > LIP_BLOCK - 8) *pl = LIP_BLOCK - 8; }
                if (b == 0) InterlockedIncrement(&g_lipBlocks);
                dst += t; b += t; len -= t;
                if (!len) return;
            }
            b -= LIP_BLOCK; blk0 = LIP_BLOCK / e->balign;  /* audio = ADPCM blocks 4.. */
        }
    }
    while (len) {
        DWORD blk = blk0 + b / bbytes, off = b % bbytes, take = bbytes - off;
        if (take > len) take = len;
        if (sf->lastEnt != ei || sf->lastBlk != (int)blk) {
            DWORD at = e->dataOff + blk * e->balign, want = e->balign, got = 0;
            if (want > 8192) want = 8192;
            if (blk * e->balign >= e->dataSize) want = 0;
            else if (blk * e->balign + want > e->dataSize) want = e->dataSize - blk * e->balign;
            if (want && sf->src != INVALID_HANDLE_VALUE) {
                SetFilePointer(sf->src, (LONG)at, NULL, FILE_BEGIN);
                real_ReadFile(sf->src, src, want, &got, NULL);
            }
            memset(sf->blk, 0, bbytes);
            if (got >= 4 * e->ch) ima_decode_block(src, (int)got, (int)e->ch, sf->blk, (int)e->spb);
            sf->lastEnt = ei; sf->lastBlk = (int)blk;
        }
        memcpy(dst, (BYTE*)sf->blk + off, take);
        dst += take; b += take; len -= take;
    }
}
static BOOL str_serve_virtual(StrFile *sf, HANDLE h, BYTE *buf, DWORD n, LPDWORD rd, LPOVERLAPPED ov, LONGLONG pos) {
    memset(buf, 0, n);
    EnterCriticalSection(&sf->cs);
    /* binary search: last entry with voff <= pos */
    int lo = 0, hi = sf->n - 1, ei = -1;
    while (lo <= hi) { int m = (lo + hi) / 2; if (sf->e[m].voff <= pos) { ei = m; lo = m + 1; } else hi = m - 1; }
    LONGLONG a = pos, b = pos + n, inside = 0;
    for (int i = ei < 0 ? 0 : ei; i < sf->n && sf->e[i].voff < b; i++) {
        StrEnt *e = &sf->e[i];
        LONGLONG s0 = e->voff, s1 = e->voff + e->pcm;
        LONGLONG p0 = a > s0 ? a : s0, p1 = b < s1 ? b : s1;
        if (p1 > p0) {
            if (g_vpcm != 2) str_pcm_bytes(sf, i, (DWORD)(p0 - s0), buf + (p0 - a), (DWORD)(p1 - p0));   /* 2 = silence */
            inside += p1 - p0;
        }
    }
    LeaveCriticalSection(&sf->cs);
    InterlockedIncrement(&g_vReads); InterlockedExchangeAdd(&g_vBytes, (LONG)n);
    InterlockedExchangeAdd(&g_vOutside, (LONG)(n - inside)); InterlockedExchange(&g_lastVRead, (LONG)GetTickCount());
    if (g_vReads <= 5) anp_log("virtual PCM read pos %llx len %lu (entry %d)", (unsigned long long)pos, n, ei);
    if (rd) *rd = n;
    if (ov) {
        ov->Internal = 0; ov->InternalHigh = n;
        if (ov->hEvent) SetEvent((HANDLE)((ULONG_PTR)ov->hEvent & ~(ULONG_PTR)1));
    } else {
        LARGE_INTEGER np; np.QuadPart = pos + n; SetFilePointerEx(h, np, NULL, FILE_BEGIN);
    }
    return TRUE;
}
static void put_bytes(BYTE *buf, LONGLONG a, LONGLONG b, LONGLONG at, const void *src, DWORD len) {
    LONGLONG p0 = at > a ? at : a, p1 = at + len < b ? at + len : b;
    for (LONGLONG p = p0; p < p1; p++) buf[p - a] = ((const BYTE*)src)[p - at];
}
static void str_overlay(int k, StrFile *sf, BYTE *buf, LONGLONG pos, DWORD got) {
    LONGLONG a = pos, b = pos + got;
    if (a < 0x38) put_bytes(buf, a, b, 0, g_strHdr[k], 0x38);
    if (!sf || !sf->n) return;
    int touchIdx = (a < (LONGLONG)sf->tbl + (LONGLONG)sf->cnt * 72) && (b > sf->tbl);
    static int lg;
    for (int i = 0; i < sf->n; i++) {
        StrEnt *e = &sf->e[i];
        if (touchIdx && e->idxPos + 24 > a && e->idxPos + 8 < b) {
            unsigned long long v[2] = {(unsigned long long)e->voff, (unsigned long long)e->pcm};
            put_bytes(buf, a, b, e->idxPos + 8, v, 16);
        }
        if (e->metaOff < b && e->metaOff + 36 > a) {
            DWORD m[9] = {2, e->samples * e->ch, e->ch, e->rate, 16, 0, 0, 2 * e->ch, 0};
            put_bytes(buf, a, b, e->metaOff, m, 36);
            if (lg++ < 5) anp_log("str meta -> PCM (entry at %08lx, %lu samples)", e->dataOff, e->samples);
        }
    }
    if (touchIdx) { static int li; if (li++ < 4) anp_log("str index read pos %llx len %lu: ADPCM entries -> virtual PCM", (unsigned long long)pos, got); }
}
static BOOL WINAPI my_ReadFile(HANDLE h, LPVOID buf, DWORD n, LPDWORD rd, LPOVERLAPPED ov) {
    io_quit_check();
    int k = -1; LONGLONG pos = -1; StrFile *sf = NULL;
    if (h != INVALID_HANDLE_VALUE) {
        EnterCriticalSection(&g_strCs); k = str_find(h); LeaveCriticalSection(&g_strCs);
    }
    if (k >= 0) {
        sf = &g_strFiles[g_strFile[k]];
        if (ov) pos = (LONGLONG)ov->Offset | ((LONGLONG)ov->OffsetHigh << 32);
        else { LONG hi = 0; DWORD lo = SetFilePointer(h, 0, &hi, FILE_CURRENT); pos = (LONGLONG)lo | ((LONGLONG)hi << 32); }
        if (pos >= STR_VBASE && sf->n && g_vpcm) return str_serve_virtual(sf, h, (BYTE*)buf, n, rd, ov, pos);
    }
    BOOL r = real_ReadFile(h, buf, n, rd, ov);
    if (k >= 0) {
        DWORD got = 0;
        if (!r && ov && GetLastError() == ERROR_IO_PENDING) {
            r = GetOverlappedResult(h, ov, &got, TRUE);
            if (rd) *rd = got;
            static int lp; if (lp++ < 3) anp_log("str read went async (pos %llx) -> waited", (unsigned long long)pos);
        } else got = rd ? *rd : (ov ? (DWORD)ov->InternalHigh : n);
        if (r && got && pos >= 0) str_overlay(k, sf, (BYTE*)buf, pos, got);
        InterlockedIncrement(&g_strReads);
        if (!r && GetLastError() == ERROR_HANDLE_EOF) {   /* overlapped read wholly past the end (vpcm=off) */
            InterlockedIncrement(&g_shortReads);
            if (g_sndZeroFill) { memset(buf, 0, n); InterlockedExchangeAdd(&g_zeroBytes, (LONG)n); }
            SetLastError(ERROR_HANDLE_EOF);
        } else if (r && got < n) {
            InterlockedIncrement(&g_shortReads);
            if (g_sndZeroFill) { memset((BYTE*)buf + got, 0, n - got); InterlockedExchangeAdd(&g_zeroBytes, (LONG)(n - got)); }
            static int ls; if (ls++ < 5) anp_log("str short read: %s pos %llx asked %lu got %lu%s", sf ? sf->path : "?",
                                                 (unsigned long long)pos, n, got, g_sndZeroFill ? " -> rest zeroed" : "");
        }
    }
    return r;
}
static BOOL WINAPI my_CloseHandle(HANDLE h) {
    EnterCriticalSection(&g_strCs);
    int k = str_find(h); if (k >= 0) g_strUsed[k] = 0;
    LeaveCriticalSection(&g_strCs);
    return real_CloseHandle(h);
}
static LPCSTR campaign_file(LPCSTR n, DWORD acc, DWORD disp);   /* campaign.inc: menu archive, save slots, scene tracking */
static HANDLE WINAPI my_CreateFileA(LPCSTR n, DWORD a, DWORD s, LPSECURITY_ATTRIBUTES sa, DWORD c, DWORD f, HANDLE t) {
    n = campaign_file(n, a, c);
    HANDLE h = real_CreateFileA(n, a, s, sa, c, f, t);
    if (h != INVALID_HANDLE_VALUE && n && g_strHook && is_dm_str(n)) str_register(h, n);
    if (g_logFiles && n) {
        static char last[MAX_PATH]; static int rep = 0;
        if (_stricmp(n, last) == 0) { rep++; }
        else {
            if (rep) anp_log("  (previous open repeated %d more times)", rep);
            rep = 0; strncpy(last, n, MAX_PATH - 1);
            anp_log("open %s %s", n, h == INVALID_HANDLE_VALUE ? "FAILED" : "ok");
        }
    }
    return h;
}
static void str_register(HANDLE h, const char *n) {
    BYTE dm[0x38];
    HANDLE r = real_CreateFileA(n, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
    DWORD got = 0;
    if (r == INVALID_HANDLE_VALUE) return;
    BOOL ok = real_ReadFile ? real_ReadFile(r, dm, 0x38, &got, NULL) : ReadFile(r, dm, 0x38, &got, NULL);
    real_CloseHandle ? real_CloseHandle(r) : CloseHandle(r);
    if (!ok || got < 0x38 || memcmp(dm, "IOISNDSTREAM", 12) != 0) return;
    BYTE dd[0x38];
    memcpy(dd, dm, 0x18);
    DWORD tbl = *(DWORD*)(dm + 0x18);
    *(DWORD*)(dd + 0x18) = tbl; *(DWORD*)(dd + 0x1c) = 0;
    memcpy(dd + 0x20, dm + 0x1c, 0x14);      /* count, 0x100, flags... */
    memcpy(dd + 0x34, dm + 0x30, 4);
    /* find / build the ADPCM entry list for this file */
    int fi = -1;
    for (int i = 0; i < g_nStrFiles; i++) if (_stricmp(g_strFiles[i].path, n) == 0) fi = i;
    if (fi < 0 && g_nStrFiles < 8) {
        fi = g_nStrFiles++;
        strncpy(g_strFiles[fi].path, n, MAX_PATH - 1);
        DWORD cnt = *(DWORD*)(dm + 0x1c);
        HANDLE r2 = real_CreateFileA(n, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
        if (r2 != INVALID_HANDLE_VALUE && cnt > 0 && cnt < 100000) {
            BYTE *t = (BYTE*)malloc(cnt * 72); DWORD g2 = 0;
            SetFilePointer(r2, (LONG)tbl, NULL, FILE_BEGIN);
            real_ReadFile(r2, t, cnt * 72, &g2, NULL);
            StrEnt *ents = (StrEnt*)malloc(sizeof(StrEnt) * cnt); int ne = 0;
            if (g2 == cnt * 72) for (DWORD i = 0; i < cnt; i++) {
                BYTE *e = t + i * 72;
                DWORD dOff = *(DWORD*)(e + 8), dSz = *(DWORD*)(e + 16), mOff = *(DWORD*)(e + 24), mSz = *(DWORD*)(e + 32);
                DWORD meta[9] = {0};
                if (mSz >= 20 && mSz <= 36) {
                    SetFilePointer(r2, (LONG)mOff, NULL, FILE_BEGIN); DWORD g3 = 0;
                    real_ReadFile(r2, meta, mSz, &g3, NULL);
                    if (meta[0] == 3 && mSz >= 36 && meta[2] >= 1 && meta[2] <= 2 && meta[7] >= 4 * meta[2] && meta[8] > 1) {
                        StrEnt x; memset(&x, 0, sizeof x);
                        x.dataOff = dOff; x.dataSize = dSz; x.metaOff = mOff; x.metaSize = mSz; x.ch = meta[2]; x.rate = meta[3];
                        x.samples = meta[1]; x.balign = meta[7]; x.spb = meta[8]; x.idxPos = tbl + i * 72; x.idx = i;
                        ents[ne++] = x;
                    }
                }
            }
            qsort(ents, ne, sizeof(StrEnt), ent_cmp);
            LONGLONG v = STR_VBASE;
            for (int i = 0; i < ne; i++) { ents[i].pcm = ents[i].samples * ents[i].ch * 2; ents[i].voff = v; v += (ents[i].pcm + 0xFFF) & ~0xFFF; }
            StrFile *sf = &g_strFiles[fi];
            sf->e = ents; sf->n = ne; sf->tbl = tbl; sf->cnt = cnt; sf->lastEnt = -1; sf->lastBlk = -1;
            sf->blk = (short*)malloc(sizeof(short) * 2 * 4096); sf->srcbuf = (BYTE*)malloc(8192);
            InitializeCriticalSection(&sf->cs);
            sf->src = real_CreateFileA(n, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, OPEN_EXISTING, 0, NULL);
            free(t);
            anp_log("DM stream %s: %d ADPCM entries -> virtual PCM %llx..%llx (LIP chunk in block 0: %s)", n, ne,
                    (unsigned long long)STR_VBASE, (unsigned long long)v, g_sndLip ? "served as LIP + silence" : "decoded as ADPCM (lip=0)");
        }
        if (r2 != INVALID_HANDLE_VALUE) real_CloseHandle(r2);
    }
    EnterCriticalSection(&g_strCs);
    int k = str_find(h);
    if (k < 0) for (int i = 0; i < 32; i++) if (!g_strUsed[i]) { k = i; break; }
    if (k >= 0) { g_strH[k] = h; memcpy(g_strHdr[k], dd, 0x38); g_strUsed[k] = 1; g_strFile[k] = fi < 0 ? 0 : fi; }
    LeaveCriticalSection(&g_strCs);
    anp_log("DM stream %s: table %08lx count %lu -> DD header", n, tbl, *(DWORD*)(dm + 0x1c));
}
static void hook_iat(HMODULE mod, const char *dll, const char *fn, void *nf, void **orig) {
    BYTE *base = (BYTE*)mod;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS*)(base + ((IMAGE_DOS_HEADER*)base)->e_lfanew);
    IMAGE_IMPORT_DESCRIPTOR *imp = (IMAGE_IMPORT_DESCRIPTOR*)(base + nt->OptionalHeader.DataDirectory[1].VirtualAddress);
    for (; imp->Name; imp++) {
        if (_stricmp((char*)(base + imp->Name), dll)) continue;
        IMAGE_THUNK_DATA *ot = (IMAGE_THUNK_DATA*)(base + imp->OriginalFirstThunk), *t = (IMAGE_THUNK_DATA*)(base + imp->FirstThunk);
        for (; ot->u1.AddressOfData; ot++, t++) {
            if (ot->u1.Ordinal & IMAGE_ORDINAL_FLAG) continue;
            IMAGE_IMPORT_BY_NAME *ibn = (IMAGE_IMPORT_BY_NAME*)(base + ot->u1.AddressOfData);
            if (strcmp((char*)ibn->Name, fn)) continue;
            DWORD old; VirtualProtect(&t->u1.Function, 4, PAGE_READWRITE, &old);
            *orig = (void*)t->u1.Function; t->u1.Function = (DWORD)nf;
            VirtualProtect(&t->u1.Function, 4, old, &old);
            return;
        }
    }
}

/* ---------- autoload: ANP_autoload.txt = "<SceneID> [mode] [delaySeconds]" ---------- */
typedef BOOL (WINAPI *PeekMessageA_t)(LPMSG, HWND, UINT, UINT, UINT);
static PeekMessageA_t real_PeekMessageA;
static DWORD g_t0; static int g_autoDone; static char g_autoId[8]; static int g_autoMode = 1, g_autoDelay = 12;
typedef void (__thiscall *SetId_t)(void *self, const char *id);
typedef void (__thiscall *Start_t)(void *self);
static void do_load(const char *id, int mode) {
    anp_log("autoload: starting scene '%s' mode %d", id, mode);
    DWORD app = *(DWORD*)0xdd2640;
    if (app) {
        DWORD sub = *(DWORD*)(app + 0xac);
        if (sub) *(DWORD*)(sub + 0xb8) = 1;
    }
    *(DWORD*)0x156b3bc = mode;
    ((SetId_t)0x869d00)((void*)0x156b3b0, id);
    ((Start_t)0x6c8040)((void*)0x156b3b0);
    anp_log("autoload: load request issued");
}
static DWORD g_lastQuitCheck;
static volatile DWORD g_lastPeek;
static HANDLE g_mainThread;
/* ANP_shot.txt -> ANP_shot.bmp: GDI capture of the primary screen at half size.
   (lets the build/test loop see the game without an external screenshot tool) */
#include "d3dshot.inc"
static void write_bmp(const char *name, HDC m, HBITMAP b, int w, int h) {
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\%s", g_dir, name);
    BITMAPINFOHEADER bi; memset(&bi, 0, sizeof bi);
    bi.biSize = sizeof bi; bi.biWidth = w; bi.biHeight = h; bi.biPlanes = 1; bi.biBitCount = 24; bi.biCompression = BI_RGB;
    int stride = (w * 3 + 3) & ~3; DWORD sz = stride * h;
    unsigned char *px = (unsigned char*)malloc(sz);
    int got = px ? GetDIBits(m, b, 0, h, px, (BITMAPINFO*)&bi, DIB_RGB_COLORS) : 0;
    if (got) {
        BITMAPFILEHEADER fh; memset(&fh, 0, sizeof fh);
        fh.bfType = 0x4d42; fh.bfOffBits = sizeof fh + sizeof bi; fh.bfSize = fh.bfOffBits + sz;
        FILE *f = fopen(fn, "wb");
        if (f) { fwrite(&fh, sizeof fh, 1, f); fwrite(&bi, sizeof bi, 1, f); fwrite(px, 1, sz, f); fclose(f); }
        anp_log("shot: %dx%d -> %s", w, h, name);
    } else anp_log("shot: GetDIBits failed (%lu)", GetLastError());
    free(px);
}
static HWND g_bestWnd; static int g_bestArea;
static BOOL CALLBACK enum_wnd(HWND hw, LPARAM lp) {
    DWORD pid = 0; GetWindowThreadProcessId(hw, &pid);
    if (pid != GetCurrentProcessId()) return TRUE;
    char t[128] = "", c[128] = ""; WCHAR wt[128] = L""; InternalGetWindowText(hw, wt, 127); WideCharToMultiByte(CP_ACP, 0, wt, -1, t, sizeof t, NULL, NULL); GetClassNameA(hw, c, sizeof c);
    RECT r; GetWindowRect(hw, &r);
    LONG st = GetWindowLongA(hw, GWL_STYLE), ex = GetWindowLongA(hw, GWL_EXSTYLE);
    anp_log("  wnd %p '%s' class '%s' rect %ld,%ld-%ld,%ld vis %d iconic %d style %08lx ex %08lx fg %d",
            hw, t, c, r.left, r.top, r.right, r.bottom, IsWindowVisible(hw), IsIconic(hw), st, ex, GetForegroundWindow() == hw);
    int a = (r.right - r.left) * (r.bottom - r.top);
    if (IsWindowVisible(hw) && !(ex & WS_EX_LAYERED) && a > g_bestArea) { g_bestArea = a; g_bestWnd = hw; }
    return TRUE;
}
static void take_shot(void) {
    /* window enumeration + PrintWindow removed: both can block forever on a hung main thread */
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_shot.bmp", g_dir);
    int W = GetSystemMetrics(SM_CXSCREEN), H = GetSystemMetrics(SM_CYSCREEN);
    int w = W / 2, h = H / 2;
    HDC s = GetDC(NULL); HDC m = CreateCompatibleDC(s);
    HBITMAP b = CreateCompatibleBitmap(s, w, h); HGDIOBJ old = SelectObject(m, b);
    SetStretchBltMode(m, HALFTONE); SetBrushOrgEx(m, 0, 0, NULL);
    StretchBlt(m, 0, 0, w, h, s, 0, 0, W, H, SRCCOPY | CAPTUREBLT);
    SelectObject(m, old);
    BITMAPINFOHEADER bi; memset(&bi, 0, sizeof bi);
    bi.biSize = sizeof bi; bi.biWidth = w; bi.biHeight = h; bi.biPlanes = 1; bi.biBitCount = 24; bi.biCompression = BI_RGB;
    int stride = (w * 3 + 3) & ~3; DWORD sz = stride * h;
    unsigned char *px = (unsigned char*)malloc(sz);
    int got = px ? GetDIBits(m, b, 0, h, px, (BITMAPINFO*)&bi, DIB_RGB_COLORS) : 0;
    if (got) {
        BITMAPFILEHEADER fh; memset(&fh, 0, sizeof fh);
        fh.bfType = 0x4d42; fh.bfOffBits = sizeof fh + sizeof bi; fh.bfSize = fh.bfOffBits + sz;
        FILE *f = fopen(fn, "wb");
        if (f) { fwrite(&fh, sizeof fh, 1, f); fwrite(&bi, sizeof bi, 1, f); fwrite(px, 1, sz, f); fclose(f); }
        anp_log("shot: %dx%d -> ANP_shot.bmp", w, h);
    } else anp_log("shot: GetDIBits failed (%lu)", GetLastError());
    free(px); DeleteObject(b); DeleteDC(m); ReleaseDC(NULL, s);
}

/* ---- ANP_where.txt: positions for level-placement work. File holds node indices (whitespace separated);
   every node whose class contains "Player" is added.  Logs the node record and the object's plausible floats. */
static void dump_floats(const char *tag, const BYTE *p, DWORD n) {
    char b[4096]; int k = 0;
    for (DWORD o = 0; o + 4 <= n && k < (int)sizeof b - 40; o += 4) {
        float v = *(const float*)(p + o); DWORD w = *(const DWORD*)(p + o);
        if (w == 0) continue;
        if (v != v || v > 1e6f || v < -1e6f || (v > -1e-3f && v < 1e-3f)) continue;
        k += sprintf(b + k, " %lx:%.2f", o, v);
    }
    anp_log("%s%s", tag, b);
}
static void dump_where(void) {
    DWORD stride, cap; BYTE *base;
    if (!node_table(&stride, &cap, &base)) { anp_log("where: node table not ready"); return; }
    long want[64]; int nw = 0;
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_where.txt", g_dir);
    FILE *f = fopen(fn, "r");
    if (f) { long v; while (nw < 48 && fscanf(f, "%ld", &v) == 1) want[nw++] = v; fclose(f); }
    for (DWORD i = 0; i < cap && i < 400000 && nw < 64; i++) {
        BYTE *nd = base + i * stride; if (!readable(nd, stride)) break;
        void *o = *(void**)(nd + 0x60); if (!o) continue;
        const char *nm = rtti_name(o);
        if (strstr(nm, "Player") && !strstr(nm, "Action")) want[nw++] = (long)i;
    }
    /* ZPlayerAction registry: init (vt slot 13, 0x4c4de0) runs only if gameMgr+0x828 != 0 and appends the
       action to gameMgr+0xa20 {count, ptr[32]}; +0x54 enabled, +0x7c initialised, +0x88 use geom, +0x98 hud slot */
    {
        DWORD gm = readable((void*)0xdd265c, 4) ? *(DWORD*)0xdd265c : 0;
        if (gm && readable((void*)(gm + 0xa20), 0x84)) {
            DWORD n = *(DWORD*)(gm + 0xa20);
            anp_log("where: gameMgr %08lx +828=%08lx playeractions %lu", gm, *(DWORD*)(gm + 0x828), n);
            for (DWORD k = 0; k < n && k < 32; k++) {
                BYTE *pa = *(BYTE**)(gm + 0xa24 + 4 * k);
                if (!readable(pa, 0xa0)) continue;
                const char *txt = "";
                DWORD sp = *(DWORD*)(pa + 0x50); if (sp && readable((void*)(sp + 0xc), 4)) txt = (const char*)(sp + 0xc);
                void *ug = *(void**)(pa + 0x88);
                anp_log("where:   pa[%lu] %p %s text='%.60s' en=%d init=%d geom=%p (%s node %ld) hud=%ld owner=%p node %ld",
                        k, pa, rtti_name(pa), txt, pa[0x54], pa[0x7c], ug, ug ? rtti_name(ug) : "-", node_of(ug),
                        (long)*(DWORD*)(pa + 0x98), *(void**)(pa + 0x24), node_of(*(void**)(pa + 0x24)));
            }
        }
    }
    for (int j = 0; j < nw; j++) {
        DWORD i = (DWORD)want[j]; if (i >= cap) continue;
        BYTE *nd = base + i * stride; if (!readable(nd, stride)) continue;
        void *o = *(void**)(nd + 0x60);
        anp_log("where: node %lu %s obj %p", i, o ? rtti_name(o) : "-", o);
        dump_floats("where:   node:", nd, stride);
        if (o && readable(o, 0x400)) dump_floats("where:   obj:", (const BYTE*)o, 0x400);
    }
}
static DWORD WINAPI watchdog(LPVOID p) {
    char q[MAX_PATH]; _snprintf(q, sizeof q, "%s\\ANP_quit.txt", g_dir);
    char sq[MAX_PATH]; _snprintf(sq, sizeof sq, "%s\\ANP_shot.txt", g_dir);
    int samples = 0, ticks = 0; LONG pendingShot = 0;
    SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
    for (;;) {
        Sleep(500); ticks++;
        if (ticks == 6) install_d3d_hooks();
        if (GetFileAttributesA(sq) != INVALID_FILE_ATTRIBUTES) {
            /* optional content = output file name */
            FILE *f = fopen(sq, "r"); char nm[64] = "";
            if (f) { if (fgets(nm, sizeof nm, f)) { char *e = nm + strlen(nm); while (e > nm && (e[-1]=='\n'||e[-1]=='\r'||e[-1]==' ')) *--e = 0; } fclose(f); }
            DeleteFileA(sq);
            _snprintf(g_shotName, sizeof g_shotName, "%s", (nm[0] && strstr(nm, ".bmp")) ? nm : "ANP_shot.bmp");
            if (g_origDevPresent || g_origScPresent) { InterlockedExchange(&g_shotReq, 1); pendingShot = ticks; }
            else take_shot();
        }
        { char nq[MAX_PATH]; _snprintf(nq, sizeof nq, "%s\\ANP_nodes.txt", g_dir);
          if (GetFileAttributesA(nq) != INVALID_FILE_ATTRIBUTES) { DeleteFileA(nq); dump_nodes(); } }
        { char gq[MAX_PATH]; _snprintf(gq, sizeof gq, "%s\\ANP_gui.txt", g_dir);
          if (GetFileAttributesA(gq) != INVALID_FILE_ATTRIBUTES) { DeleteFileA(gq); dump_gui(); } }
        { char wq[MAX_PATH]; _snprintf(wq, sizeof wq, "%s\\ANP_where.txt", g_dir);
          if (GetFileAttributesA(wq) != INVALID_FILE_ATTRIBUTES) { dump_where(); DeleteFileA(wq); } }
        if (pendingShot && ticks - pendingShot == 6) {
            if (g_shotReq) anp_log("d3dshot: not served in 3s (presents dev %ld sc %ld) -> GDI", g_devPresents, g_scPresents), g_shotReq = 0, take_shot();
            pendingShot = 0;
        }
        if (GetFileAttributesA(q) != INVALID_FILE_ATTRIBUTES) {
            DeleteFileA(q);
            anp_log("watchdog: ANP_quit.txt found: terminating process");
            if (g_log) fflush(g_log);
            TerminateProcess(GetCurrentProcess(), 0);
        }
        DWORD lp = g_lastPeek;
        if (g_mainThread && lp) wrap_watch(GetTickCount() - lp);
        if (g_mainThread && lp && GetTickCount() - lp > 90000) {
            anp_log("watchdog: main thread hung for %lus -> terminating (unattended test safety)", (GetTickCount() - lp) / 1000);
            if (g_log) fflush(g_log);
            TerminateProcess(GetCurrentProcess(), 3);
        }
        if (g_mainThread && lp && GetTickCount() - lp > 4000 && samples < 400) {
            static CONTEXT c; static DWORD stk[256]; int n = 0;
            if (SuspendThread(g_mainThread) != (DWORD)-1) {
                c.ContextFlags = CONTEXT_FULL;
                if (GetThreadContext(g_mainThread, &c)) {
                    DWORD *sp = (DWORD*)c.Esp;
                    for (int i = 0; i < 2048 && n < 256; i++) {
                        if (!readable(sp + i, 4)) break;
                        DWORD v = sp[i];
                        if (v >= 0x401000 && v < 0xb10000) stk[n++] = v;
                    }
                }
                ResumeThread(g_mainThread);
                char buf[3000]; int k = 0;
                for (int i = 0; i < n && k < 2900; i++) k += sprintf(buf + k, " %08lx", stk[i]);
                buf[k] = 0;
                anp_log("watchdog: main thread busy %lums eip=%08lx esp=%08lx ebp=%08lx eax=%08lx ecx=%08lx stack:%s",
                        GetTickCount() - lp, c.Eip, c.Esp, c.Ebp, c.Eax, c.Ecx, buf);
                samples++;
            }
        }
    }
    return 0;
}
/* ---- campaigns: ANP_load.txt / ANP_endlevel.txt test hooks (main thread). See campaign.inc ---- */
#include "campaign.inc"
/* ---- level-start cutscene diagnostics (read-only, opt-in with ANP_cutdiag.txt). See cutdiag.inc ---- */
#include "cutdiag.inc"
/* ---- TEST-ONLY player god mode (opt-in with ANP_god.txt). See godmode.inc ---- */
#include "godmode.inc"
static BOOL WINAPI my_PeekMessageA(LPMSG m, HWND h, UINT a, UINT b, UINT r) {
    DWORD now = GetTickCount();
    g_lastPeek = now;
    if (!g_mainThread) {
        DuplicateHandle(GetCurrentProcess(), GetCurrentThread(), GetCurrentProcess(), &g_mainThread,
                        THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, 0);
        CreateThread(NULL, 0, watchdog, NULL, 0, NULL);
        anp_log("watchdog started");
    }
    if (now - g_lastQuitCheck > 1000) {
        g_lastQuitCheck = now;
        char q[MAX_PATH]; _snprintf(q, sizeof q, "%s\\ANP_quit.txt", g_dir);
        if (GetFileAttributesA(q) != INVALID_FILE_ATTRIBUTES) {
            DeleteFileA(q);
            anp_log("ANP_quit.txt found: terminating process");
            if (g_log) fflush(g_log);
            TerminateProcess(GetCurrentProcess(), 0);
        }
    }
    campaign_tick(now);
    cutdiag_tick(now);
    godmode_tick(now);
    herowatch_tick(now); resetguard_tick(now);   /* heapguard.inc / resetguard.inc: data reads only */
    if (!g_autoDone) {
        if (!g_t0) {
            g_t0 = GetTickCount();
            char p[MAX_PATH]; _snprintf(p, sizeof p, "%s\\ANP_autoload.txt", g_dir);
            FILE *f = fopen(p, "r");
            if (f) {
                if (fscanf(f, "%7s %d %d", g_autoId, &g_autoMode, &g_autoDelay) < 1) g_autoId[0] = 0;
                fclose(f);
                anp_log("autoload configured: '%s' mode %d after %ds", g_autoId, g_autoMode, g_autoDelay);
            }
            if (!g_autoId[0]) g_autoDone = 1;
        } else if (GetTickCount() - g_t0 > (DWORD)g_autoDelay * 1000) {
            g_autoDone = 1;
            do_load(g_autoId, g_autoMode);
        }
    }
    return real_PeekMessageA(m, h, a, b, r);
}


/* ---------- CListUser (dynamic overlap graph) guard ----------
   FUN_004f8a60(this, id, geom, flag) walks bucket list *(this+0x20)+id*4.  A bad id (geom+0x54)
   crashed M01; log who carries it and skip instead of crashing. */
static const char *rtti_name(const void *obj) {
    if (!obj || !readable(obj, 4)) return "?";
    const DWORD *vt = *(const DWORD* const*)obj;
    if (!readable(vt - 1, 4)) return "?";
    DWORD col = vt[-1]; if (!readable((void*)col, 16)) return "?";
    DWORD td = *(DWORD*)(col + 12); if (!readable((void*)(td + 8), 64)) return "?";
    return (const char*)(td + 8);
}
static void log_obj_strings(const char *tag, const BYTE *o, int n) {
    for (int i = 0; i < n; i += 4) {
        if (!readable(o + i, 4)) break;
        const char *s = *(const char* const*)(o + i);
        if ((DWORD)s < 0x10000 || !readable(s, 48)) continue;
        int k = 0; while (k < 47 && s[k] >= 32 && s[k] < 127) k++;
        if (k >= 4 && s[k] == 0) anp_log("    %s+%02x -> \"%s\"", tag, i, s);
    }
}
typedef DWORD (__fastcall *ClFind_t)(void *self, void *edx, DWORD id, void *geom, int flag);
static ClFind_t g_clFindOrig;
static int g_clBad;
static DWORD __fastcall my_cl_find(void *self, void *edx, DWORD id, void *geom, int flag) {
    DWORD base = *(DWORD*)((BYTE*)self + 0x20);
    DWORD *bucket = (DWORD*)(base + id * 4);
    DWORD head = readable(bucket, 4) ? *bucket : 0xdeadbeef;
    if (head != 0 && (head < 0x10000 || !readable((void*)head, 16))) {
        if (g_clBad++ < 40) {
            anp_log("CListUser guard: bad bucket id=%06lx head=%08lx (base %08lx) geom=%p %s +54=%08lx +3c=%08lx",
                    id, head, base, geom, rtti_name(geom),
                    geom ? *(DWORD*)((BYTE*)geom + 0x54) : 0, geom ? *(DWORD*)((BYTE*)geom + 0x3c) : 0);
            if (geom && readable(geom, 0x80)) {
                const DWORD *w = (const DWORD*)geom;
                anp_log("    geom words: %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx | %08lx %08lx %08lx %08lx",
                        w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[0x14], w[0x15], w[0x16], w[0x17]);
                log_obj_strings("geom", (const BYTE*)geom, 0x80);
            }
        }
        return 0;
    }
    return g_clFindOrig(self, edx, id, geom, flag);
}
/* ---- effect permutation lookup logger: FUN_008b8fd0(lib, effectName, defines[2n], n, kind) ---- */
typedef void* (__attribute__((thiscall)) *FxLookup_t)(void *lib, const char *name, char **defs, unsigned n, unsigned kind);
static unsigned g_fxMissHash[512]; static int g_fxMissN, g_fxMissTotal, g_fxHitTotal;
static void* __attribute__((thiscall)) my_fxlookup(void *lib, const char *name, char **defs, unsigned n, unsigned kind) {
    void *r = ((FxLookup_t)0x8b8fd0)(lib, name, defs, n, kind);
    if (r) { g_fxHitTotal++; return r; }
    g_fxMissTotal++;
    char buf[1024]; int k = _snprintf(buf, sizeof buf, "%u %s :", kind, readable(name, 1) ? name : "?");
    for (unsigned i = 0; i < n && i < 32 && k < 1000; i++)
        k += _snprintf(buf + k, sizeof buf - k, " %s", readable(defs[2*i], 1) ? defs[2*i] : "?");
    unsigned h = 2166136261u; for (char *c = buf; *c; c++) h = (h ^ (unsigned char)*c) * 16777619u;
    int seen = 0; for (int i = 0; i < g_fxMissN; i++) if (g_fxMissHash[i] == h) seen = 1;
    if (!seen && g_fxMissN < 512) g_fxMissHash[g_fxMissN++] = h;
    if (!seen) anp_log("FXMISS %s", buf);
    /* runtime alias: closest permutation in the library (same kind/effect/mesh type/blend state) */
    void *best = NULL; int bestScore = 1 << 30;
    if (readable((char*)lib + 0x1c28, 4) && n >= 1 && readable(defs, 8 * n)) {
        unsigned cnt = *(unsigned*)((char*)lib + 0x1c28);
        int wantBlend = 0;
        for (unsigned i = 0; i < n; i++) if (readable(defs[2*i], 1) && !strcmp(defs[2*i], "BLENDENABLED")) wantBlend = 1;
        for (unsigned i = 0; i < cnt && i < 4096; i++) {
            unsigned *e = *(unsigned**)((char*)lib + 0x1c2c + 4*i);
            if (!readable(e, 20) || e[0] != kind || !readable((char*)e[1], 1) || strcmp((char*)e[1], name)) continue;
            char **dl = (char**)e[3]; unsigned m = e[4];
            if (!m || !readable(dl, 8 * m) || !readable(dl[0], 1) || strcmp(dl[0], defs[0])) continue;   /* mesh type */
            int hasBlend = 0, score = 0;
            for (unsigned j = 0; j < m; j++) if (readable(dl[2*j], 1) && !strcmp(dl[2*j], "BLENDENABLED")) hasBlend = 1;
            if (hasBlend != wantBlend) continue;
            for (unsigned a = 1; a < n; a++) {             /* wanted defines missing from candidate */
                int f = 0; for (unsigned j = 1; j < m; j++) if (readable(dl[2*j],1) && !strcmp(dl[2*j], defs[2*a])) { f = 1; break; }
                if (!f) score += 10;
            }
            for (unsigned j = 1; j < m; j++) {             /* extra defines in candidate */
                if (!readable(dl[2*j],1)) continue;
                int f = 0; for (unsigned a = 1; a < n; a++) if (!strcmp(dl[2*j], defs[2*a])) { f = 1; break; }
                if (!f && strcmp(dl[2*j], "STDSAMPLERSTATE") && strcmp(dl[2*j], "USEDEFAULTREFLECTIONMAP")) score += 4;
            }
            if (score < bestScore) { bestScore = score; best = e; }
        }
        if (best && !seen) anp_log("FXALIAS -> score %d", bestScore);
    }
    static int dumped;
    if (!dumped && readable((char*)lib + 0x1c28, 4)) {
        dumped = 1;
        unsigned cnt = *(unsigned*)((char*)lib + 0x1c28);
        anp_log("FX lib %p count %u", lib, cnt);
        for (unsigned i = 0; i < cnt && i < 400; i++) {
            unsigned *e = *(unsigned**)((char*)lib + 0x1c2c + 4*i);
            if (!readable(e, 20)) continue;
            char lb[600]; int q = _snprintf(lb, sizeof lb, "  fx[%u] kind %u %s n%u :", i, e[0], readable((char*)e[1],1) ? (char*)e[1] : "?", e[4]);
            char **dl = (char**)e[3];
            for (unsigned j = 0; j < e[4] && j < 16 && q < 560 && readable(dl, 8*(j+1)); j++)
                q += _snprintf(lb + q, sizeof lb - q, " %s", readable(dl[2*j],1) ? dl[2*j] : "?");
            anp_log("%s", lb);
        }
    }
    return best ? best : r;
}
static void install_fx_logger(void) {
    unsigned char *p = (unsigned char*)0x71166d;
    if (p[0] != 0xE8 || (DWORD)(p + 5 + *(LONG*)(p + 1)) != 0x8b8fd0) { anp_log("fx logger: unexpected call site"); return; }
    patch_call(0x71166d, my_fxlookup, "fx lookup/alias (legacy)");
    anp_log("fx logger installed (LEGACY code patch at 0x71166d, CEG-hashed)");
}
/* ---- ZGraphic template guard: FUN_0051f180 int3s when its template (this+0x8c) can't be instantiated ---- */
static int g_gfxFail;
void log_graphic_fail(BYTE *g) {
    if (g_gfxFail++ >= 20) return;
    anp_log("ZGraphic template missing: obj %p %s", g, rtti_name(g));
    if (readable(g + 0x80, 0x30)) {
        const DWORD *w = (const DWORD*)(g + 0x80);
        anp_log("    +80: %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx %08lx", w[0],w[1],w[2],w[3],w[4],w[5],w[6],w[7],w[8],w[9]);
    }
    log_obj_strings("gfx", g, 0x100);
    if (readable(g + 0x94, 4)) { BYTE *t = *(BYTE**)(g + 0x94); if (readable(t, 0x40)) log_obj_strings("gfx+94", t, 0x40); }
}
/* retry the template lookup with a graphic that exists in Dead Men's menu resources, so menus that
   reference Dog Days-only graphics (Icon_Fail, BlackBackground...) still get a valid object */
typedef DWORD (__attribute__((thiscall)) *F502300_t)(void *container, void *ref, DWORD a3);
DWORD retry_graphic(BYTE *self, void *container, DWORD a3) {
    static const char *fb[] = {"Background", "Line_Long_01#01", "Line_Short_01#01", NULL};
    if (!readable(self + 0x8c, 0x1c)) return 0;
    char **pname = (char**)(self + 0x9c); char *old = *pname; DWORD r = 0;
    for (int i = 0; fb[i] && !r; i++) { *pname = (char*)fb[i]; r = ((F502300_t)0x502300)(container, self + 0x8c, a3); }
    *pname = old;
    if (g_gfxFail < 40) anp_log("  graphic '%s' -> fallback %s", readable(old, 1) ? old : "?", r ? "ok" : "FAILED");
    return r;
}
__attribute__((naked)) void graphic_fail_stub(void) {
    __asm__ __volatile__(
        "test %eax,%eax\n\t"
        "jz 1f\n\t"
        "push $0x51f1aa\n\t"
        "ret\n"
        "1:\n\t"
        "mov 0x24(%esp),%ecx\n\t"
        "mov 0x28(%esp),%edx\n\t"
        "pushal\n\t"
        "push %esi\n\t"
        "call _log_graphic_fail\n\t"
        "add $4,%esp\n\t"
        "mov 24(%esp),%ecx\n\t"   /* saved ecx/edx in pushal frame: EDI ESI EBP ESP EBX EDX ECX EAX */
        "mov 20(%esp),%edx\n\t"
        "push %edx\n\t"
        "push %ecx\n\t"
        "push %esi\n\t"
        "call _retry_graphic\n\t"
        "add $12,%esp\n\t"
        "mov %eax,28(%esp)\n\t"
        "popal\n\t"
        "test %eax,%eax\n\t"
        "jz 2f\n\t"
        "mov %eax,0x88(%esi)\n\t"
        "push $0x51f1aa\n\t"
        "ret\n"
        "2:\n\t"
        "mov 0x20(%esp),%eax\n\t"
        "movl $0,(%eax)\n\t movl $0,4(%eax)\n\t movl $0,8(%eax)\n\t movl $0,12(%eax)\n\t"
        "movl $0,16(%eax)\n\t movl $0,20(%eax)\n\t movb $0,24(%eax)\n\t"
        "pop %edi\n\t pop %esi\n\t pop %ebx\n\t"
        "add $0x10,%esp\n\t"
        "ret $0x10\n\t");
}
static void install_gfx_guard(void) {
    static const unsigned char expect[] = {0x3b, 0xc3, 0x75, 0x01, 0xcc};
    if (memcmp((void*)0x51f1a5, expect, 5) != 0) { anp_log("gfx guard: unexpected bytes"); return; }
    patch_jmp(0x51f1a5, graphic_fail_stub, 5, "gfx guard (legacy)");
    anp_log("gfx guard installed (LEGACY code patch at 0x51f1a5, CEG-hashed)");
}
/* ---- text word-wrap stall guard: FUN_008a3e60 loops forever when a word can't fit and no char is consumed ---- */
volatile DWORD g_wrapLast, g_wrapStall, g_wrapHits;
__attribute__((naked)) void wrap_stall_stub(void) {
    __asm__ __volatile__(
        "test %ebp,%ebp\n\t"
        "jz 3f\n\t"
        "cmp _g_wrapLast,%ebp\n\t"
        "jne 1f\n\t"
        "incl _g_wrapStall\n\t"
        "cmpl $3,_g_wrapStall\n\t"
        "jb 2f\n\t"
        "movl $0,_g_wrapStall\n\t"
        "incl _g_wrapHits\n\t"
        "jmp 3f\n"
        "1:\n\t"
        "mov %ebp,_g_wrapLast\n\t"
        "movl $0,_g_wrapStall\n"
        "2:\n\t"
        "push $0x8a3f00\n\t"
        "ret\n"
        "3:\n\t"
        "push $0x8a4106\n\t"
        "ret\n\t");
}
static void install_wrap_guard(void) {
    static const unsigned char expect[] = {0x85, 0xed, 0x0f, 0x85, 0xfa, 0xfd, 0xff, 0xff};
    if (memcmp((void*)0x8a40fe, expect, 8) != 0) { anp_log("wrap guard: unexpected bytes"); return; }
    patch_jmp(0x8a40fe, wrap_stall_stub, 8, "wrap guard (legacy)");
    anp_log("wrap guard installed (LEGACY code patch at 0x8a40fe, CEG-hashed)");
}
static void install_cl_guard(void) {
    static const unsigned char expect[] = {0x51, 0x8b, 0x54, 0x24, 0x08, 0x89, 0x0c, 0x24};
    unsigned char *p = (unsigned char*)0x4f8a60;
    if (memcmp(p, expect, 8) != 0) { anp_log("CListUser guard: unexpected bytes, not installed"); return; }
    unsigned char *t = VirtualAlloc(NULL, 32, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(t, p, 8); t[8] = 0xE9; *(DWORD*)(t + 9) = 0x4f8a68 - ((DWORD)t + 13);
    g_clFindOrig = (ClFind_t)t;
    patch_jmp(0x4f8a60, my_cl_find, 8, "CListUser guard (legacy)");
    anp_log("CListUser guard installed (LEGACY code patch at 0x4f8a60, CEG-hashed)");
}


/* ---------- static handle table (FUN_0040a880 on *(0xe0ff90)) diagnostics ---------- */
static int node_table(DWORD *stride, DWORD *cap, BYTE **base) {
    DWORD mgr = readable((void*)0xe0ff90, 4) ? *(DWORD*)0xe0ff90 : 0;
    if (!mgr || !readable((void*)(mgr + 0xc), 4)) return 0;
    DWORD T = *(DWORD*)(mgr + 0xc);
    if (!readable((void*)T, 0x14)) return 0;
    *stride = *(DWORD*)(T + 4); *cap = *(DWORD*)(T + 8); *base = *(BYTE**)(T + 0xc);
    return *stride && *base;
}
static void dump_nodes(void) {
    DWORD stride, cap; BYTE *base;
    if (!node_table(&stride, &cap, &base)) { anp_log("nodes: table not ready"); return; }
    char fn[MAX_PATH]; _snprintf(fn, sizeof fn, "%s\\ANP_nodes.log", g_dir);
    FILE *f = fopen(fn, "w"); if (!f) return;
    fprintf(f, "stride %lu cap %lu base %p\n", stride, cap, base);
    int n = 0;
    for (DWORD i = 0; i < cap && i < 400000; i++) {
        BYTE *nd = base + i * stride;
        if (!readable(nd, stride)) { fprintf(f, "%lu unreadable\n", i); break; }
        void *o = *(void**)(nd + 0x60);
        if (!o) continue;
        { DWORD par = *(DWORD*)(nd + 0x50); long pi = (par >= (DWORD)base && par < (DWORD)base + cap * stride) ? (long)((par - (DWORD)base) / stride) : -1;
          fprintf(f, "%lu %s p%ld", i, rtti_name(o), pi); }
        if (i < 64) { const DWORD *w = (const DWORD*)nd; for (DWORD k = 0; k < stride / 4 && k < 32; k++) fprintf(f, " %08lx", w[k]); }
        fprintf(f, "\n"); n++;
    }
    fclose(f);
    anp_log("nodes: dumped %d live nodes (stride %lu cap %lu) -> ANP_nodes.log", n, stride, cap);
}
/* ---- collision octree callback guard: FUN_00927b30 resolves record+0x4c (static handle) and calls vt+0x2e8.
   A handle that lands on a non-spatial object (e.g. ZGROUP) crashed; log it and hand back a dummy that says "skip". */
__attribute__((naked)) static void dummy_ret1(void) { __asm__ __volatile__("mov $1,%eax\n\tret\n\t"); }
static DWORD g_dummyVt[0x400 / 4]; static DWORD g_dummyObj[16] = { (DWORD)g_dummyVt };
static volatile LONG g_collBad;
static void coll_report(DWORD h, void *o, DWORD fn, const char *how) {
    if (InterlockedIncrement(&g_collBad) <= 30) {
        DWORD stride, cap; BYTE *base; char nb[256] = "";
        DWORD idx = (h >> 7) & 0x7fffff;
        if ((h & 0x40000000) && node_table(&stride, &cap, &base)) {
            int k = 0;
            for (int d = -3; d <= 3; d++) {
                BYTE *nd = base + (idx + d) * stride;
                k += _snprintf(nb + k, sizeof nb - k, " [%d]%s", d, readable(nd + 0x60, 4) ? rtti_name(*(void**)(nd + 0x60)) : "?");
                if (k > 220) break;
            }
        }
        anp_log("coll guard%s: handle %08lx idx %lu low %lu -> %p %s (vt+2e8=%08lx) neighbours:%s", how, h, idx, h & 0x7f, o,
                rtti_name(o), fn, nb);
    }
}
/* legacy (code patch at 0x927b44): resolve, check vt+0x2e8, hand back a dummy that says "skip" */
static void* __cdecl my_coll_resolve(DWORD h) {
    void *o = ((void* (__cdecl*)(DWORD))0x8ccde0)(h);
    DWORD fn = 0;
    if (o && readable(o, 4)) { DWORD *vt = *(DWORD**)o; if (readable(vt + 0x2e8 / 4, 4)) fn = vt[0x2e8 / 4]; }
    if (fn >= 0x401000 && fn < 0xb10000) return o;
    coll_report(h, o, fn, "");
    return g_dummyObj;
}
static void install_coll_guard(void) {
    static const unsigned char expect[] = {0x50, 0xe8, 0x96, 0x52, 0xfa, 0xff, 0x8b, 0xd8};
    unsigned char *p = (unsigned char*)0x927b44;
    if (memcmp(p, expect, 8) != 0) { anp_log("coll guard: unexpected bytes"); return; }
    for (int i = 0; i < 0x400 / 4; i++) g_dummyVt[i] = (DWORD)dummy_ret1;
    patch_call(0x927b45, my_coll_resolve, "coll guard (legacy)");
    anp_log("coll guard installed (LEGACY code patch at 0x927b45, CEG-hashed)");
}


/* ---- ZXMLGUISystem ctor hook: watch writes to its +0x24 (menu window) ---- */
static void* __fastcall my_xg_ctor(void *self) {
    void *r = ((void* (__fastcall*)(void*))0x8a4330)(self);
    anp_log("ZXMLGUISystem created %p -> watching +0x24", r);
    ULONG_PTR a = (ULONG_PTR)r + 0x24;
    RaiseException(0xE0A0B001, 0, 1, &a);
    return r;
}
static void install_xg_watch(void) {
    unsigned char *p = (unsigned char*)0x4944f2;
    static const unsigned char expect[] = {0xe8, 0x39, 0xfe, 0x40, 0x00};
    if (memcmp(p, expect, 5) != 0) { anp_log("xg watch: unexpected bytes"); return; }
    patch_call(0x4944f2, my_xg_ctor, "xg watch (diagnostic)");
    anp_log("xg watch installed (DIAGNOSTIC code patch at 0x4944f2, CEG-hashed; arms DR0 - never in a release)");
}


typedef void (WINAPI *ODS_t)(LPCSTR);
static ODS_t real_ODS;
static volatile LONG g_odsN;
static void WINAPI my_ODS(LPCSTR m) {
    if (m && InterlockedIncrement(&g_odsN) < 3000) {
        char t[400]; int k = 0;
        while (k < 398 && m[k]) { t[k] = (m[k] == '\n' || m[k] == '\r') ? ' ' : m[k]; k++; }
        t[k] = 0; anp_log("ODS: %s", t);
    }
    if (real_ODS) real_ODS(m);
}


/* GUI diagnostics: ANP_gui.txt -> dump current ZXMLGUISystem (DAT_01539f0c) window stack */
static const char *safe_name_vt0c(void *w) {
    if (!w || !readable(w, 4)) return "?";
    DWORD *vt = *(DWORD**)w; if (!readable(vt + 3, 4)) return "?";
    DWORD fn = vt[3]; if (fn < 0x401000 || fn >= 0xb10000) return "?";
    const char *r = ((const char* (__attribute__((thiscall)) *)(void*))fn)(w);
    return (r && readable(r, 4)) ? r : "?";
}
static void dump_gui(void) {
    DWORD gs = readable((void*)0x1539f0c, 4) ? *(DWORD*)0x1539f0c : 0;
    anp_log("gui: system %08lx %s", gs, rtti_name((void*)gs));
    if (!gs || !readable((void*)gs, 0x6c4)) return;
    DWORD *p = (DWORD*)gs;
    anp_log("gui: +24 menu %08lx %s node %ld | +34 %08lx %s | +38 %08lx %s", p[9], rtti_name((void*)p[9]), node_of((void*)p[9]),
            p[0xd], rtti_name((void*)p[0xd]), p[0xe], rtti_name((void*)p[0xe]));
    int n = (int)p[0xca]; anp_log("gui: open windows %d (199=%ld 200=%ld)", n, (long)p[199], (long)p[200]);
    for (int i = 0; i < n && i < 16; i++) { void *w = (void*)p[0xcb + i]; anp_log("gui:   [%d] %p %s", i, w, rtti_name(w)); }
    { char b[600]; int k = 0; for (int i = 0xc4; i < 0xd8; i++) k += sprintf(b + k, " %08lx", p[i]); anp_log("gui: raw c4..d7:%s", b); }
    for (int i = 0xc4; i < 0xd8; i++) { const char *nm = rtti_name((void*)p[i]); if (nm[0] == '.') anp_log("gui:   p[%x] -> %s node %ld", i, nm, node_of((void*)p[i])); }
    for (int i = 0x12c; i < 0x140; i++) { const char *nm = rtti_name((void*)p[i]); if (nm[0] == '.') anp_log("gui:   p[%x] -> %s node %ld", i, nm, node_of((void*)p[i])); }
}


/* ---- streamed sound buffer setup: min variant rate 0 (unconverted DM SND type-1 records) divides by zero ---- */
volatile DWORD g_sndZero;
__attribute__((naked)) void snd_rate_stub(void) {
    __asm__ __volatile__(
        "mov 0x1c(%esp),%ebp\n\t"
        "test %ebp,%ebp\n\t"
        "jnz 1f\n\t"
        "incl _g_sndZero\n\t"
        "mov $22050,%ebp\n\t"
        "mov %ebp,0x1c(%esp)\n"
        "1:\n\t"
        "mul %ebp\n\t"
        "push $0x446679\n\t"
        "ret\n\t");
}
static void install_snd_guard(void) {
    static const unsigned char expect[] = {0x8b, 0x6c, 0x24, 0x1c, 0xf7, 0xe5};
    if (memcmp((void*)0x446673, expect, 6) != 0) { anp_log("snd guard: unexpected bytes"); return; }
    patch_jmp(0x446673, snd_rate_stub, 6, "snd guard (legacy)");
    anp_log("snd guard installed (LEGACY code patch at 0x446673, CEG-hashed)");
}

/* =====================================================================================================================
   CEG-safe guards (11 Oct). They replace the six old code patches without changing a kl2.exe code byte.
   Switches: <DD>\ANP_guards.txt, "key=value" tokens (whitespace separated, read once at start):
     cl=veh     CListUser bucket guard (0x4f8a60, overlap table h[6]). veh: on an access violation at one of the four
                bucket-walk reads 0x4f8a8e/92/97/9e (fault address inside [edx, edx+0x10), before any write) resume at
                0x4f8b40 (xor eax,eax; pop ebx/esi/ebp/ecx; ret 0xc) = the old hook's "return 0". Catches what the
                hook caught in practice (M01: id 0 reads the h[6] header word 0x56cf); a bucket head that happens to
                be MAPPED garbage is not caught - the real fix is the converter (M01's id-0 overlap object).
     fx=off     runtime FX permutation alias (call at 0x71166d). No VEH is possible (nothing faults): the aliases are
                built offline from fxc\miss_<ID>.txt (scripts\fxmiss_harvest.py). legacy = old call patch (logs
                FXMISS lines and aliases at run time).
     gfx=veh    ZGraphic template guard: int3 at 0x51f1a9 (template not found) -> graphic_fail_stub (fallback graphic),
                registers and stack are the same as at the old patch site 0x51f1a5.
     wrap=watch text word-wrap stall (0x8a3e60 loop never advances). Nothing faults, so: watch = the watchdog logs a
                suspected stall (main thread busy >= 1.5 s inside 0x8a3e60 on consecutive samples); rescue = also
                ends the loop (main thread suspended at a stack-balanced point of the loop body with the same ebp on
                3 samples, return address 0x5aa4b1 -> Eip 0x8a4106 = the old stub's exit; CONTEXT_CONTROL only, never
                debug registers). The cause (DM 20-byte glyph records) is gone: fonts are converted (dmfont.py).
     coll=veh   collision octree callback 0x927b30: a handle that resolves to NULL / an object without a readable
                vtable / a vt+0x2e8 that faults when called -> "skip" (al=0), as the old dummy object did.
                Faults at 0x927b4c (ebx), 0x927b4e (vtable) and the call target itself ([esp] = 0x927b5b).
                A wrong-class object with a callable slot is not caught (offline validator: node order).
     snd=veh    rate 0 in the streamed-sound setup: divide fault at 0x44668b with ebp = [esp+0x1c] = 0 ->
                [esp+0x1c] = 22050, eax = 0xcccccccd, Eip = 0x446673 (re-runs mul/shr/div exactly like the old stub).
                (ANP_sound.txt sndpatch=0/1/legacy sets this too; ANP_guards.txt wins.)
     Each also takes off (no guard) and legacy (the old code patch, CEG-hashed: never for a release / a real
     Arcade or Fragile Alliance session). legacy=all = every guard legacy (the pre-11-Oct loader).
   Counters are on the stats line: "guards snd S div D null N cl C gfx G coll K wrap W sus U".
   ===================================================================================================================== */
enum { G_OFF = 0, G_ON = 1, G_LEGACY = 2, G_RESCUE = 3 };
static int g_gCl = G_ON, g_gFx = G_OFF, g_gGfx = G_ON, g_gWrap = G_ON, g_gColl = G_ON, g_gSnd = G_ON;
static int g_gHeap = G_ON, g_gHeroWatch = 1, g_gReset = 1;   /* heap=veh|off, herowatch=on|off, reset=on|all(2)|off */
static volatile LONG g_clHits, g_gfxHits, g_wrapSuspect, g_wrapRescue;
static const char *g_modeName[] = {"off", "veh", "LEGACY", "rescue"};
static int guard_mode(const char *v, int allowRescue) {
    if (!_stricmp(v, "legacy") || !_stricmp(v, "patch") || !strcmp(v, "2")) return G_LEGACY;
    if (allowRescue && !_stricmp(v, "rescue")) return G_RESCUE;
    if (!_stricmp(v, "off") || !strcmp(v, "0")) return G_OFF;
    return G_ON;                                          /* veh / on / watch / 1 */
}
static void guards_config(void) {
    g_gSnd = g_sndPatch;                                  /* ANP_sound.txt sndpatch (default 1 = veh) */
    char p[MAX_PATH]; _snprintf(p, sizeof p, "%s\\ANP_guards.txt", g_dir);
    FILE *f = fopen(p, "r"); char t[64];
    if (f) {
        while (fscanf(f, "%63s", t) == 1) {
            if (t[0] == '#' || t[0] == ';') { int c; while ((c = fgetc(f)) != EOF && c != '\n'); continue; }
            char *e = strchr(t, '='); if (!e) continue; *e++ = 0;
            if (!_stricmp(t, "legacy") && !_stricmp(e, "all")) { g_gCl = g_gFx = g_gGfx = g_gWrap = g_gColl = g_gSnd = G_LEGACY; }
            else if (!_stricmp(t, "cl")) g_gCl = guard_mode(e, 0);
            else if (!_stricmp(t, "fx")) g_gFx = guard_mode(e, 0) == G_LEGACY ? G_LEGACY : G_OFF;
            else if (!_stricmp(t, "gfx")) g_gGfx = guard_mode(e, 0);
            else if (!_stricmp(t, "wrap")) g_gWrap = guard_mode(e, 1);
            else if (!_stricmp(t, "coll")) g_gColl = guard_mode(e, 0);
            else if (!_stricmp(t, "snd")) g_gSnd = guard_mode(e, 0);
            else if (!_stricmp(t, "heap") || !_stricmp(t, "heapguard")) g_gHeap = guard_mode(e, 0) == G_OFF ? G_OFF : G_ON;
            else if (!_stricmp(t, "herowatch")) g_gHeroWatch = guard_mode(e, 0) != G_OFF;
            else if (!_stricmp(t, "reset") || !_stricmp(t, "resetguard")) g_gReset = !_stricmp(e, "all") ? 2 : guard_mode(e, 0) != G_OFF;
            else anp_log("guards: unknown key '%s' in ANP_guards.txt", t);
        }
        fclose(f);
    }
    anp_log("guards (%s): cl=%s fx=%s gfx=%s wrap=%s coll=%s snd=%s heap=%s herowatch=%s reset=%s", f ? "ANP_guards.txt" : "defaults",
            g_modeName[g_gCl], g_gFx == G_LEGACY ? "LEGACY" : "off (offline aliases)", g_modeName[g_gGfx],
            g_gWrap == G_ON ? "watch" : g_modeName[g_gWrap], g_modeName[g_gColl], g_modeName[g_gSnd],
            g_modeName[g_gHeap], g_gHeroWatch ? "on" : "off", g_gReset == 2 ? "all" : g_gReset ? "on" : "off");
}
static int code_byte_ok(DWORD at, const BYTE *b, int n) { return readable((void*)at, n) && memcmp((void*)at, b, n) == 0; }

/* -- CListUser: 0x4f8a60 bucket walk. Stack at the four reads: [esp] ebx, +4 esi, +8 ebp, +0xc this, +0x10 ret,
      +0x14 id, +0x18 geom (= esi), +0x1c flag. Caller's own frame starts at esp+0x20. */
static const DWORD g_clRets[] = {0x5a9b89, 0x5edad2, 0x5edb07, 0x61ee1a, 0x6307ed, 0x630811, 0x6308a8, 0x63090f, 0x630931};
static int cl_guard(PEXCEPTION_POINTERS ep) {
    CONTEXT *cx = ep->ContextRecord; DWORD eip = cx->Eip;
    if (eip == 0x4f8a6e) {
        /* bucket SLOT read (mov edx,[ecx], ecx = base + id*4) unreadable - the legacy hook's "bucket not readable"
           case. Only ecx (this) is pushed here: [esp] this, +4 ret. Resume at 0x4f8b45 (pop ecx; ret 0xc), eax = 0. */
        static const BYTE slot[] = {0x8b, 0x11}, tail[] = {0x59, 0xc2, 0x0c, 0x00};
        if ((DWORD)ep->ExceptionRecord->ExceptionAddress != eip || ep->ExceptionRecord->NumberParameters < 2 ||
            ep->ExceptionRecord->ExceptionInformation[0] != 0 || (DWORD)ep->ExceptionRecord->ExceptionInformation[1] != cx->Ecx ||
            !readable((void*)cx->Esp, 0x10) || !code_byte_ok(0x4f8a6e, slot, 2) || !code_byte_ok(0x4f8b45, tail, 4)) return 0;
        DWORD ret = ((const DWORD*)cx->Esp)[1]; int known = 0;
        for (unsigned i = 0; i < sizeof g_clRets / sizeof g_clRets[0]; i++) if (g_clRets[i] == ret) known = 1;
        if (!known) return 0;
        LONG n = InterlockedIncrement(&g_clHits);
        if (n <= 40) anp_log("CListUser guard (veh): bucket slot unreadable id=%06lx slot=%08lx from %08lx (hit %ld)",
                             ((const DWORD*)cx->Esp)[2], cx->Ecx, ret, n);
        cx->Eax = 0; cx->Eip = 0x4f8b45;
        return 1;
    }
    if (eip != 0x4f8a8e && eip != 0x4f8a92 && eip != 0x4f8a97 && eip != 0x4f8a9e) return 0;
    if ((DWORD)ep->ExceptionRecord->ExceptionAddress != eip || ep->ExceptionRecord->NumberParameters < 2 ||
        ep->ExceptionRecord->ExceptionInformation[0] != 0) return 0;
    DWORD fa = (DWORD)ep->ExceptionRecord->ExceptionInformation[1];
    if (fa < cx->Edx || fa >= cx->Edx + 0x10 || !readable((void*)cx->Esp, 0x20)) return 0;
    static const BYTE resume[] = {0x33, 0xc0, 0x5b, 0x5e, 0x5d, 0x59, 0xc2, 0x0c, 0x00};    /* 0x4f8b40 */
    if (!code_byte_ok(0x4f8b40, resume, sizeof resume)) return 0;
    const DWORD *sp = (const DWORD*)cx->Esp; DWORD ret = sp[4], id = sp[5];
    int known = 0; for (unsigned i = 0; i < sizeof g_clRets / sizeof g_clRets[0]; i++) if (g_clRets[i] == ret) known = 1;
    if (!known) return 0;
    LONG n = InterlockedIncrement(&g_clHits);
    if (n <= 40) {
        BYTE *geom = (BYTE*)cx->Esi; DWORD base = readable((void*)(sp[3] + 0x20), 4) ? *(DWORD*)(sp[3] + 0x20) : 0;
        anp_log("CListUser guard (veh): bad bucket id=%06lx head=%08lx (base %08lx) geom=%p %s +54=%08lx from %08lx (hit %ld)",
                id, cx->Edx, base, geom, rtti_name(geom), readable(geom + 0x54, 4) ? *(DWORD*)(geom + 0x54) : 0, ret, n);
        if (n == 1) {   /* node_of scans the node table: first hit only */
            /* who carries overlap id <id>: the mover is in the caller's frame (0x630800 path: [caller esp+0x20];
               0x6307d3 path: *edi) - list every RTTI object near the caller frame whose +0x54 low 24 bits == id */
            anp_log("    geom node %ld", node_of(geom));
            int shown = 0;
            for (int i = 8; i < 8 + 24 && shown < 4; i++) {
                if (!readable(sp + i, 4)) break;
                BYTE *o = (BYTE*)sp[i]; const char *nm = rtti_name(o);
                if (nm[0] == '.' && readable(o + 0x54, 4) && (*(DWORD*)(o + 0x54) & 0xffffff) == id)
                    anp_log("    id carrier? esp+%02x %p %s +54=%08lx node %ld", i * 4, o, nm, *(DWORD*)(o + 0x54), node_of(o)), shown++;
            }
            if (ret == 0x6307ed && readable((void*)cx->Edi, 4)) {
                BYTE *o = *(BYTE**)cx->Edi;
                anp_log("    caller [edi] %p %s +54=%08lx node %ld", o, rtti_name(o), readable(o + 0x54, 4) ? *(DWORD*)(o + 0x54) : 0, node_of(o));
            }
        }
    } else if ((n & (n - 1)) == 0) anp_log("CListUser guard (veh): hits %ld", n);
    cx->Eip = 0x4f8b40;
    return 1;
}
/* -- gfx: int3 at 0x51f1a9 (0x502300 found no template; eax = 0) */
static int gfx_guard(PEXCEPTION_POINTERS ep) {
    CONTEXT *cx = ep->ContextRecord;
    if ((DWORD)ep->ExceptionRecord->ExceptionAddress != 0x51f1a9 || (cx->Eip != 0x51f1a9 && cx->Eip != 0x51f1aa) || cx->Eax != 0) return 0;
    static const BYTE site[] = {0x3b, 0xc3, 0x75, 0x01, 0xcc};
    if (!code_byte_ok(0x51f1a5, site, sizeof site)) return 0;
    InterlockedIncrement(&g_gfxHits);
    cx->Eip = (DWORD)graphic_fail_stub;                  /* logs "ZGraphic template missing" itself */
    return 1;
}
/* -- coll: 0x927b30 callback. record = esi, handle = [esi+0x4c] */
static int coll_guard(PEXCEPTION_POINTERS ep) {
    CONTEXT *cx = ep->ContextRecord; DWORD eip = cx->Eip;
    if (ep->ExceptionRecord->NumberParameters < 2) return 0;
    DWORD fa = (DWORD)ep->ExceptionRecord->ExceptionInformation[1];
#define COLL_HANDLE() (readable((void*)(cx->Esi + 0x4c), 4) ? *(DWORD*)(cx->Esi + 0x4c) : 0)
    static const BYTE site[] = {0x8b, 0x13, 0x8b, 0x82, 0xe8, 0x02, 0x00, 0x00, 0x83, 0xc4, 0x04};   /* 0x927b4c */
    if ((eip == 0x927b4c && fa == cx->Ebx) || (eip == 0x927b4e && fa == cx->Edx + 0x2e8)) {
        if (!code_byte_ok(0x927b4c, site, sizeof site) || !readable((void*)cx->Esp, 4)) return 0;
        coll_report(COLL_HANDLE(), (void*)cx->Ebx, 0, " (veh)");
        cx->Esp += 4;                                     /* the pushed handle (add esp,4 at 0x927b54 not run yet) */
        cx->Eip = 0x927b5f;                               /* pop edi; pop esi; xor al,al; pop ebx; add esp,0x18; ret */
        return 1;
    }
    if (fa == eip && (DWORD)ep->ExceptionRecord->ExceptionAddress == eip && readable((void*)cx->Esp, 4) &&
        *(DWORD*)cx->Esp == 0x927b5b && cx->Ecx == cx->Ebx) {   /* call eax at 0x927b59 into a non-executable target */
        if (!code_byte_ok(0x927b4c, site, sizeof site)) return 0;
        coll_report(COLL_HANDLE(), (void*)cx->Ebx, eip, " (veh, call)");
        cx->Esp += 4; cx->Eax = (cx->Eax & ~0xffu) | 1; cx->Eip = 0x927b5b;   /* al = 1 -> skip */
        return 1;
    }
#undef COLL_HANDLE
    return 0;
}
/* -- snd: div ebp at 0x44668b with ebp = 0 */
static int snd_guard(PEXCEPTION_POINTERS ep) {
    CONTEXT *cx = ep->ContextRecord;
    if (cx->Eip != 0x44668b || cx->Ebp != 0 || !readable((void*)(cx->Esp + 0x1c), 4) || *(DWORD*)(cx->Esp + 0x1c) != 0) return 0;
    static const BYTE site[] = {0x8b, 0x6c, 0x24, 0x1c, 0xf7, 0xe5};
    if (!code_byte_ok(0x446673, site, sizeof site)) return 0;
    LONG n = InterlockedIncrement((volatile LONG*)&g_sndZero);
    if (n <= 5) anp_log("snd guard (veh): stream rate 0 at 0x44668b -> 22050 (hit %ld)", n);
    *(DWORD*)(cx->Esp + 0x1c) = 22050;
    cx->Eax = 0xcccccccd;                                 /* as set at 0x44666b; no stack op between 0x446673 and here */
    cx->Eip = 0x446673;
    return 1;
}
static int ceg_guard_veh(PEXCEPTION_POINTERS ep) {
    DWORD code = ep->ExceptionRecord->ExceptionCode;
    if (code == EXCEPTION_ACCESS_VIOLATION) {
        if (g_gCl == G_ON && cl_guard(ep)) return 1;
        if (g_gColl == G_ON && coll_guard(ep)) return 1;
    } else if (code == EXCEPTION_BREAKPOINT) {
        if (g_gGfx == G_ON && gfx_guard(ep)) return 1;
        if (g_gHeap == G_ON && heap_guard(ep)) return 1;   /* heapguard.inc: 0x4665dc heap-header assert */
    } else if (code == EXCEPTION_INT_DIVIDE_BY_ZERO) {
        if (g_gSnd == G_ON && snd_guard(ep)) return 1;
    }
    return 0;
}
/* -- wrap: watchdog thread. Stack-balanced windows of the 0x8a3e60 loop body (esp = frame base, [esp+0x24] = return
      address 0x5aa4b1, the only caller 0x5aa4ac), where Eip can move to the epilogue 0x8a4106 (pop edi/esi/ebp,
      al = 1, pop ebx, add esp,0x14, ret). Nothing is logged or allocated while the main thread is suspended. */
static const DWORD g_wrapWin[][2] = {
    {0x8a3f00, 0x8a3f45}, {0x8a3f4f, 0x8a3f5f}, {0x8a3f68, 0x8a3f8b}, {0x8a3f98, 0x8a3fae}, {0x8a3fbf, 0x8a3fd0},
    {0x8a3fdd, 0x8a3fea}, {0x8a4006, 0x8a4037}, {0x8a404c, 0x8a4064}, {0x8a4070, 0x8a4071}, {0x8a407d, 0x8a40ab},
    {0x8a40b7, 0x8a40db}, {0x8a40ed, 0x8a4106}};
static int wrap_window(DWORD eip) {
    for (unsigned i = 0; i < sizeof g_wrapWin / sizeof g_wrapWin[0]; i++) if (eip >= g_wrapWin[i][0] && eip < g_wrapWin[i][1]) return 1;
    return 0;
}
static void wrap_watch(DWORD busyMs) {
    static int streak, reported; static DWORD sameEbp, sameN, sameT0;
    if (g_gWrap != G_ON && g_gWrap != G_RESCUE) return;
    if (busyMs < 1500) { streak = 0; reported = 0; sameN = 0; return; }
    int tries = (g_gWrap == G_RESCUE && streak >= 1) ? 300 : 1, inside = 0, rescued = 0;
    DWORD seenEip = 0, seenEbp = 0;
    for (int t = 0; t < tries && !rescued; t++) {
        CONTEXT c; memset(&c, 0, sizeof c); c.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        if (SuspendThread(g_mainThread) == (DWORD)-1) return;
        int in = 0, win = 0;
        if (GetThreadContext(g_mainThread, &c)) {
            if (c.Eip >= 0x8a3e60 && c.Eip < 0x8a4130) in = 1;
            else {
                const DWORD *sp = (const DWORD*)c.Esp;
                int nsp = readable(sp, 96 * 4) ? 96 : readable(sp, 16 * 4) ? 16 : 0;
                for (int i = 0; i < nsp && !in; i++) if (sp[i] > 0x8a3e60 && sp[i] < 0x8a4130) in = 1;
            }
            if (in && wrap_window(c.Eip) && c.Ebp && readable((void*)(c.Esp + 0x24), 4) && *(DWORD*)(c.Esp + 0x24) == 0x5aa4b1) {
                win = 1;
                if (c.Ebp == sameEbp) sameN++; else { sameEbp = c.Ebp; sameN = 1; sameT0 = GetTickCount(); }
                if (g_gWrap == G_RESCUE && sameN >= 3 && GetTickCount() - sameT0 >= 20) {
                    c.ContextFlags = CONTEXT_CONTROL; c.Eip = 0x8a4106;
                    rescued = SetThreadContext(g_mainThread, &c) ? 1 : 0;
                }
            }
        }
        ResumeThread(g_mainThread);
        if (in) { inside = 1; seenEip = c.Eip; seenEbp = c.Ebp; }
        if (!in) break;
        if (!win && tries > 1) Sleep(1);
        else if (tries > 1) Sleep(2);
    }
    if (rescued) {
        InterlockedIncrement(&g_wrapRescue);
        anp_log("wrap rescue: text word-wrap loop 0x8a3e60 stalled (ebp %08lx, %lu same samples) -> Eip 0x8a4106", sameEbp, sameN);
        streak = 0; reported = 0; sameN = 0; return;
    }
    if (!inside) { streak = 0; return; }
    if (++streak == 2 && !reported) {
        reported = 1; InterlockedIncrement(&g_wrapSuspect);
        anp_log("wrap watch: main thread busy %lums inside the text word-wrap 0x8a3e60 (eip %08lx ebp %08lx) - suspected stall%s",
                busyMs, seenEip, seenEbp, g_gWrap == G_RESCUE ? "" : " (wrap=rescue in ANP_guards.txt ends it)");
    }
}
/* -- start-up: install what the switches ask for, then list every kl2 code byte changed */
static const struct { DWORD at; int n; BYTE b[8]; const char *what; } g_cegSites[] = {
    {0x4f8a60, 8, {0x51, 0x8b, 0x54, 0x24, 0x08, 0x89, 0x0c, 0x24}, "CListUser"},
    {0x71166d, 5, {0xe8, 0x5e, 0x79, 0x1a, 0x00}, "fx call"},
    {0x51f1a5, 5, {0x3b, 0xc3, 0x75, 0x01, 0xcc}, "gfx"},
    {0x8a40fe, 8, {0x85, 0xed, 0x0f, 0x85, 0xfa, 0xfd, 0xff, 0xff}, "wrap"},
    {0x927b44, 8, {0x50, 0xe8, 0x96, 0x52, 0xfa, 0xff, 0x8b, 0xd8}, "coll"},
    {0x446673, 6, {0x8b, 0x6c, 0x24, 0x1c, 0xf7, 0xe5}, "snd"},
    {0x6d100f, 6, {0x5f, 0x5e, 0x33, 0xc0, 0x5b, 0xc3}, "resolver"},
    {0x4944f2, 5, {0xe8, 0x39, 0xfe, 0x40, 0x00}, "xg watch"}};
static void install_guards(void) {
    for (int i = 0; i < 0x400 / 4; i++) g_dummyVt[i] = (DWORD)dummy_ret1;
    if (g_gCl == G_LEGACY) install_cl_guard();
    if (g_gFx == G_LEGACY) install_fx_logger();
    if (g_gGfx == G_LEGACY) install_gfx_guard();
    if (g_gWrap == G_LEGACY) install_wrap_guard();
    if (g_gColl == G_LEGACY) install_coll_guard();
    if (g_gSnd == G_LEGACY) install_snd_guard();
}
static void ceg_report(void) {
    char b[700]; int k = 0; LONG n = g_ncpatch;
    for (LONG i = 0; i < n && i < 16 && k < 600; i++)
        k += _snprintf(b + k, sizeof b - k, " %08lx+%d [%s]", g_cpatch[i].at, g_cpatch[i].len, g_cpatch[i].what);
    b[k] = 0;
    if (!n) anp_log("CEG: kl2.exe code bytes changed by ANP_Loader: none (import slots, .data and heap only)");
    else anp_log("CEG: kl2.exe code bytes changed by ANP_Loader: %ld patch(es):%s  <<< CEG-hashed pages: a real Arcade / Fragile "
                 "Alliance session will end with ExitProcess(0x8000dead)", n, b);
    int pristine = 0; char bad[300]; int kb = 0; bad[0] = 0;
    for (unsigned i = 0; i < sizeof g_cegSites / sizeof g_cegSites[0]; i++) {
        if (code_byte_ok(g_cegSites[i].at, g_cegSites[i].b, g_cegSites[i].n)) pristine++;
        else if (kb < 260) kb += _snprintf(bad + kb, sizeof bad - kb, " %08lx(%s)", g_cegSites[i].at, g_cegSites[i].what);
    }
    anp_log("CEG: old patch sites with stock bytes %d/%u%s%s", pristine, (unsigned)(sizeof g_cegSites / sizeof g_cegSites[0]),
            kb ? ", changed:" : "", bad);
    g_cegListed = 1;
}

/* ---- sound stats line (ANP_sound.txt stats=N): one line every N s when a counter moved ----
   snd: vreads/vKB = virtual PCM reads served (Dead Men ADPCM), vout = bytes asked outside every entry,
   lip = LIP blocks served, last = seconds since the last virtual read, str = real reads on Dead Men .str handles,
   short/zKB = reads that returned fewer bytes than asked (zero-filled), guards: snd = rate-0 guard hits (VEH or
   legacy stub), div = VEH divide guard hits, null = null sound-list guard hits, cl = CListUser bad buckets, gfx =
   missing ZGraphic templates, coll = collision callback skips, wrap = word-wrap stalls ended (legacy stub / rescue),
   sus = suspected word-wrap stalls (watch); mem: committed MB above 2 GB, largest free block.
   cpu (cpu=1): threads busy >= 90% of the interval, as tid:percent (m = main thread). */
#include <tlhelp32.h>
typedef struct { DWORD tid; ULONGLONG t; } ThrT;
static ThrT g_thr[256]; static int g_nthr;
static int snd_cpu(char *out, int cap, DWORD dtMs) {   /* returns the number of busy threads other than the main one */
    out[0] = 0; int k = 0, others = 0;
    HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (s == INVALID_HANDLE_VALUE) return 0;
    THREADENTRY32 te; te.dwSize = sizeof te;
    DWORD pid = GetCurrentProcessId(), mainTid = g_mainThread ? GetThreadId(g_mainThread) : 0;
    ThrT nt[256]; int nn = 0;
    for (BOOL ok = Thread32First(s, &te); ok && nn < 256; ok = Thread32Next(s, &te)) {
        if (te.th32OwnerProcessID != pid) continue;
        HANDLE h = OpenThread(THREAD_QUERY_LIMITED_INFORMATION, FALSE, te.th32ThreadID);
        if (!h) continue;
        FILETIME c, e, kt, ut;
        if (GetThreadTimes(h, &c, &e, &kt, &ut)) {
            ULONGLONG t = ((ULONGLONG)kt.dwHighDateTime << 32 | kt.dwLowDateTime) + ((ULONGLONG)ut.dwHighDateTime << 32 | ut.dwLowDateTime);
            nt[nn].tid = te.th32ThreadID; nt[nn].t = t; nn++;
            for (int i = 0; i < g_nthr; i++) if (g_thr[i].tid == te.th32ThreadID) {
                ULONGLONG d = (t - g_thr[i].t) / 10000;     /* ms */
                if (dtMs && d * 100 >= (ULONGLONG)dtMs * 90 && k < cap - 24) {
                    k += sprintf(out + k, " %lu%s:%u%%", te.th32ThreadID, te.th32ThreadID == mainTid ? "m" : "", (unsigned)(d * 100 / dtMs));
                    if (te.th32ThreadID != mainTid) others++;
                }
                break;
            }
        }
        CloseHandle(h);
    }
    CloseHandle(s);
    memcpy(g_thr, nt, sizeof(ThrT) * nn); g_nthr = nn;
    return others;
}
static void snd_mem(DWORD *hiMB, DWORD *freeMB) {
    MEMORY_BASIC_INFORMATION mi; ULONGLONG hi = 0, big = 0;
    for (BYTE *a = (BYTE*)0x10000; ; ) {
        if (!VirtualQuery(a, &mi, sizeof mi)) break;
        if (mi.State == MEM_COMMIT && (DWORD)mi.BaseAddress >= 0x80000000u) hi += mi.RegionSize;
        if (mi.State == MEM_FREE && mi.RegionSize > big) big = mi.RegionSize;
        BYTE *n = (BYTE*)mi.BaseAddress + mi.RegionSize;
        if (n <= a) break;
        a = n;
    }
    *hiMB = (DWORD)(hi >> 20); *freeMB = (DWORD)(big >> 20);
}
/* ---- OpenAL instrumentation (ANP_sound.txt al=1, default on): IAT hooks on kl2's OpenAL32 imports ----
   Import slots are not CEG-hashed.  kl2 never reads alGetError (0x6000a9 stores it in a global), so AL errors are
   counted here.  Counters go on the stats line as "al:". */
#define ANP_AL_GAIN 0x100A
#define ANP_AL_POSITION 0x1004
#define ANP_AL_DIRECTION 0x1005
#define ANP_AL_VELOCITY 0x1006
#define ANP_AL_ORIENTATION 0x100F
static volatile LONG g_alPlay, g_alGain0, g_alGainPos, g_alNaN, g_alFloored, g_alBuf, g_alBufOdd, g_alErr, g_alGainMaxK;
typedef void (__cdecl *alSourcef_t)(unsigned, int, float);
typedef void (__cdecl *alSourcefv_t)(unsigned, int, const float *);
typedef void (__cdecl *alListenerfv_t)(int, const float *);
typedef void (__cdecl *alSourcePlay_t)(unsigned);
typedef void (__cdecl *alBufferData_t)(unsigned, int, const void *, int, int);
typedef int (__cdecl *alGetError_t)(void);
static alSourcef_t real_alSourcef; static alSourcefv_t real_alSourcefv; static alListenerfv_t real_alListenerfv;
static alSourcePlay_t real_alSourcePlay; static alBufferData_t real_alBufferData; static alGetError_t real_alGetError;
static int al_bad(float f) { DWORD b; memcpy(&b, &f, 4); return (b & 0x7f800000) == 0x7f800000; }   /* NaN or Inf */
static int al_count(int param, int listener) {
    if (param == ANP_AL_ORIENTATION) return listener ? 6 : 3;
    if (param == ANP_AL_POSITION || param == ANP_AL_VELOCITY || param == ANP_AL_DIRECTION) return 3;
    return 1;
}
static void __cdecl my_alSourcef(unsigned s, int p, float v) {
    if (al_bad(v)) { InterlockedIncrement(&g_alNaN); if (g_nanFix) v = p == ANP_AL_GAIN ? 1.0f : 0.0f; }
    if (p == ANP_AL_GAIN) {
        if (v > 0.0f) {
            InterlockedIncrement(&g_alGainPos);
            LONG k = (LONG)(v * 1000.0f); if (k > g_alGainMaxK) g_alGainMaxK = k;
        } else InterlockedIncrement(&g_alGain0);
        if (g_gainFloor > 0.0f && !(v >= g_gainFloor)) { v = g_gainFloor; InterlockedIncrement(&g_alFloored); }
    }
    real_alSourcef(s, p, v);
}
static void __cdecl my_alSourcefv(unsigned s, int p, const float *v) {
    float t[6]; int n = al_count(p, 0), bad = 0;
    if (v) for (int i = 0; i < n; i++) { t[i] = v[i]; if (al_bad(t[i])) { bad++; t[i] = 0.0f; } }
    if (bad) { InterlockedIncrement(&g_alNaN); if (g_nanFix) { real_alSourcefv(s, p, t); return; } }
    real_alSourcefv(s, p, v);
}
static void __cdecl my_alListenerfv(int p, const float *v) {
    float t[6]; int n = al_count(p, 1), bad = 0;
    if (v) for (int i = 0; i < n; i++) { t[i] = v[i]; if (al_bad(t[i])) { bad++; t[i] = p == ANP_AL_GAIN ? 1.0f : 0.0f; } }
    if (bad) { InterlockedIncrement(&g_alNaN); if (g_nanFix) { real_alListenerfv(p, t); return; } }
    real_alListenerfv(p, v);
}
static void __cdecl my_alSourcePlay(unsigned s) { InterlockedIncrement(&g_alPlay); real_alSourcePlay(s); }
static void __cdecl my_alBufferData(unsigned b, int fmt, const void *d, int size, int freq) {
    LONG n = InterlockedIncrement(&g_alBuf);
    int odd = size <= 0 || freq < 4000 || freq > 192000 || fmt < 0x1100 || fmt > 0x1103;
    if (odd) InterlockedIncrement(&g_alBufOdd);
    if (n <= 4 || (odd && g_alBufOdd <= 5)) anp_log("al: alBufferData #%ld fmt %#x size %d freq %d%s", n, fmt, size, freq, odd ? " ODD" : "");
    real_alBufferData(b, fmt, d, size, freq);
}
static int __cdecl my_alGetError(void) {
    int e = real_alGetError();
    if (e) { LONG n = InterlockedIncrement(&g_alErr); if (n <= 10) anp_log("al: alGetError -> %#x (#%ld)", e, n); }
    return e;
}
static void install_al_hooks(void) {
    HMODULE m = GetModuleHandleA(NULL);
    hook_iat(m, "OpenAL32.dll", "alSourcef", my_alSourcef, (void**)&real_alSourcef);
    hook_iat(m, "OpenAL32.dll", "alSourcefv", my_alSourcefv, (void**)&real_alSourcefv);
    hook_iat(m, "OpenAL32.dll", "alListenerfv", my_alListenerfv, (void**)&real_alListenerfv);
    hook_iat(m, "OpenAL32.dll", "alSourcePlay", my_alSourcePlay, (void**)&real_alSourcePlay);
    hook_iat(m, "OpenAL32.dll", "alBufferData", my_alBufferData, (void**)&real_alBufferData);
    hook_iat(m, "OpenAL32.dll", "alGetError", my_alGetError, (void**)&real_alGetError);
    anp_log("ANP loader: OpenAL hooks Sourcef %s Sourcefv %s Listenerfv %s SourcePlay %s BufferData %s GetError %s (gainfloor %.3f nanfix %d)",
            real_alSourcef ? "ok" : "MISSING", real_alSourcefv ? "ok" : "MISSING", real_alListenerfv ? "ok" : "MISSING",
            real_alSourcePlay ? "ok" : "MISSING", real_alBufferData ? "ok" : "MISSING", real_alGetError ? "ok" : "MISSING",
            (double)g_gainFloor, g_nanFix);
}
static DWORD WINAPI snd_stats_thread(LPVOID p) {
    LONG last[24] = {0}; DWORD lastT = GetTickCount(), lastLog = 0;
    for (;;) {
        Sleep(g_sndStats * 1000);
        DWORD now = GetTickCount(), dt = now - lastT; lastT = now;
        LONG cur[24] = {g_vReads, g_vBytes, g_vOutside, g_lipBlocks, g_strReads, g_shortReads, g_zeroBytes, (LONG)g_sndZero, g_divGuard, g_nullList,
                        g_alPlay, g_alGain0, g_alGainPos, g_alNaN, g_alFloored, g_alBuf, g_alBufOdd, g_alErr, 0,
                        g_clHits + (LONG)g_clBad, (LONG)g_gfxFail,g_collBad, (LONG)g_wrapHits + g_wrapRescue, g_wrapSuspect};
        LONG gmax = InterlockedExchange(&g_alGainMaxK, 0);
        char cpu[200] = ""; int busy = g_sndCpu ? snd_cpu(cpu, sizeof cpu, dt) : 0;
        int moved = memcmp(cur, last, sizeof cur) != 0;
        if (!moved && !busy && now - lastLog < 60000) continue;
        DWORD hiMB, freeMB; snd_mem(&hiMB, &freeMB);
        LONG lv = g_lastVRead;
        anp_log("snd: vreads %ld (+%ld) vKB %lu vout %ld lip %ld last %lds | str %ld short %ld zKB %lu | guards snd %ld div %ld null %ld cl %ld gfx %ld coll %ld wrap %ld sus %ld | mem >2GB %luMB freemax %luMB | cpu>=90%%:%s",
                cur[0], cur[0] - last[0], (unsigned long)cur[1] >> 10, cur[2], cur[3], lv ? (long)((now - (DWORD)lv) / 1000) : -1L,
                cur[4], cur[5], (unsigned long)cur[6] >> 10, cur[7], cur[8], cur[9], cur[19], cur[20], cur[21], cur[22], cur[23],
                hiMB, freeMB, cpu[0] ? cpu : " -");
        if (g_alHook)
            anp_log("al: play %ld (+%ld) gain0 %ld (+%ld) gain>0 %ld (+%ld) gainmax %.3f floored %ld nan %ld (+%ld) buf %ld odd %ld err %ld",
                    cur[10], cur[10] - last[10], cur[11], cur[11] - last[11], cur[12], cur[12] - last[12], gmax / 1000.0,
                    cur[14], cur[13], cur[13] - last[13], cur[15], cur[16], cur[17]);
        memcpy(last, cur, sizeof cur); lastLog = now;
    }
    return 0;
}


/* ---- foreground-window nudge throttle (tip from JC's K&L project) ----
   kl2 0x6f4220 runs about once a millisecond: GetForegroundWindow, walk to the root window, and if it is the
   game's window, re-set the cursor and inject a mouse_event.  During loads that dominates (minutes instead of
   seconds).  Answer the real window at most every 250 ms; in between report "no foreground" so the nudge is
   skipped.  Only call site in the exe is 0x6f4229. */
typedef HWND (WINAPI *GetForegroundWindow_t)(void);
static GetForegroundWindow_t real_GetForegroundWindow;
static DWORD g_fgLast; static unsigned g_fgSkipped;
static HWND WINAPI my_GetForegroundWindow(void) {
    DWORD now = GetTickCount();
    if (now - g_fgLast < 250) { g_fgSkipped++; return NULL; }
    g_fgLast = now;
    return real_GetForegroundWindow();
}

/* ---- Dead Men climb (W + E into a ledge): frame hook, probe, live action. See climb.inc ---- */
static void squad_frame(void);   /* squad.inc, ticked from climb.inc's frame hook */
static void give_frame(void);    /* give.inc, ticked from climb.inc's frame hook */
static void grenade_frame(void); /* grenade.inc, ticked from climb.inc's frame hook */
static void rappel_frame(void);  /* rappel.inc, ticked from climb.inc's frame hook */
static void equipassist_frame(void); /* equipassist.inc, ticked from climb.inc's frame hook */
static void revive_frame(void);  /* revive.inc, ticked from climb.inc's frame hook; the two below are read by climb/squad/give */
static int revive_is_down(const BYTE *body);
static int revive_prompt_up(void);
#include "failwatch.inc"   /* mission-fail / merc-state diagnostic (data reads only; opt-in ANP_failwatch.txt) */
#include "climb.inc"
/* ---- Dead Men crew orders (Follow / Fire at / Defend): ANP_squad.txt, ANP_squad_cmd.txt. See squad.inc ---- */
#include "squad.inc"
/* ---- Dead Men weapon giving / swapping with squad mates: ANP_give.txt, ANP_give_cmd.txt. See give.inc ---- */
#include "give.inc"
/* ---- Dead Men player grenade throw (G): ANP_grenade.txt, ANP_grenade_cmd.txt. See grenade.inc ---- */
#include "grenade.inc"
/* ---- Dead Men rappelling (RappellingBox points): ANP_rappel.txt. See rappel.inc ---- */
#include "rappel.inc"
/* ---- Dead Men mini-cutscene equip for the player (same-type gun replaced): ANP_equip.txt. See equipassist.inc ---- */
#include "equipassist.inc"
/* ---- Dead Men wounded mercs + revive (DND hold, bleed-out, heal prompt): ANP_revive.txt, ANP_revive_cmd.txt. See revive.inc ---- */
#include "revive.inc"
/* ---- heap assert guard 0x4665dc + herowatch (ZLNKOBJ+0x88); D3D device-reset render-list guard. ANP_guards.txt ---- */
#include "heapguard.inc"
#include "resetguard.inc"

BOOL WINAPI DllMain(HINSTANCE hi, DWORD reason, LPVOID r) {
    if (reason != DLL_PROCESS_ATTACH) return TRUE;
    DisableThreadLibraryCalls(hi);
    InitializeCriticalSection(&g_cs);
    GetModuleFileNameA(NULL, g_dir, MAX_PATH);
    char *s = strrchr(g_dir, '\\'); if (s) *s = 0;
    char lp[MAX_PATH]; _snprintf(lp, sizeof lp, "%s\\ANP_log.txt", g_dir);
    g_log = fopen(lp, "w");
    campaign_init();   /* campaign.inc: ANP_campaign.txt, strncpy scene routing (replaces the 0x6d100f patch), ExitProcess tripwire */
    // old resolver patch (CEG-hashed code): only with LegacyResolver=1 or when the strncpy import can't be hooked
    unsigned char *p = (unsigned char*)0x6d100f;
    static const unsigned char expect[] = {0x5f, 0x5e, 0x33, 0xc0, 0x5b, 0xc3};
    if (!campaign_legacy_resolver()) anp_log("ANP loader: scene resolver patch at 0x6d100f not installed (strncpy routing)");
    else if (memcmp(p, expect, 6) == 0) {
        patch_jmp(0x6d100f, anp_resolve_stub, 6, "scene resolver (LegacyResolver=1)");
        anp_log("ANP loader: scene resolver hooked (LEGACY code patch at 0x6d100f, CEG-hashed)");
    } else anp_log("ANP loader: unexpected bytes at 0x6d100f, resolver NOT hooked");
    { char gp[MAX_PATH]; _snprintf(gp, sizeof gp, "%s\\ANP_no_boneslights_guard.txt", g_dir);
      g_guardBonesLights = GetFileAttributesA(gp) == INVALID_FILE_ATTRIBUTES;
      anp_log("ANP loader: v4BonesLights guard (0x577e08) %s", g_guardBonesLights ? "on" : "OFF (ANP_no_boneslights_guard.txt)"); }
    snd_config();
    anp_log("ANP loader: sound lip=%d zerofill=%d stats=%d sndpatch=%s cpu=%d vpcm=%s strhook=%d al=%d gainfloor=%.3f nanfix=%d (ANP_sound.txt)",
            g_sndLip, g_sndZeroFill, g_sndStats, g_sndPatch == 2 ? "legacy" : g_sndPatch ? "1" : "0", g_sndCpu,
            g_vpcm == 2 ? "silence" : g_vpcm ? "1" : "off", g_strHook, g_alHook, (double)g_gainFloor, g_nanFix);
    guards_config();   /* ANP_guards.txt: CEG-safe guards (default) or the old code patches (legacy) */
    AddVectoredExceptionHandler(1, veh);
    install_guards();
    if (g_alHook) install_al_hooks();
    if (g_sndStats > 0) CreateThread(NULL, 0, snd_stats_thread, NULL, 0, NULL);
    { char wp[MAX_PATH]; _snprintf(wp, sizeof wp, "%s\\ANP_watch_xg.txt", g_dir); if (GetFileAttributesA(wp) != INVALID_FILE_ATTRIBUTES) install_xg_watch(); }
    InitializeCriticalSection(&g_strCs);
    hook_iat(GetModuleHandleA(NULL), "kernel32.dll", "ReadFile", my_ReadFile, (void**)&real_ReadFile);
    hook_iat(GetModuleHandleA(NULL), "kernel32.dll", "CloseHandle", my_CloseHandle, (void**)&real_CloseHandle);
    anp_log("ANP loader: ReadFile hook %s, CloseHandle hook %s", real_ReadFile ? "ok" : "MISSING", real_CloseHandle ? "ok" : "MISSING");
    hook_iat(GetModuleHandleA(NULL), "kernel32.dll", "CreateFileA", my_CreateFileA, (void**)&real_CreateFileA);
    hook_iat(GetModuleHandleA(NULL), "kernel32.dll", "OutputDebugStringA", my_ODS, (void**)&real_ODS);
    anp_log("ANP loader: OutputDebugStringA hook %s", real_ODS ? "ok" : "MISSING");
    hook_iat(GetModuleHandleA(NULL), "user32.dll", "PeekMessageA", my_PeekMessageA, (void**)&real_PeekMessageA);
    anp_log("ANP loader: PeekMessageA hook %s", real_PeekMessageA ? "ok" : "MISSING");
    if (GetFileAttributesA("ANP_no_fg_throttle.txt") == INVALID_FILE_ATTRIBUTES) {
        hook_iat(GetModuleHandleA(NULL), "user32.dll", "GetForegroundWindow", my_GetForegroundWindow, (void**)&real_GetForegroundWindow);
        anp_log("ANP loader: GetForegroundWindow throttle %s", real_GetForegroundWindow ? "ok" : "MISSING");
    }
    install_climb();
    herowatch_init(); resetguard_install();   /* heapguard.inc / resetguard.inc (SetEvent import slot) */
    ceg_report();      /* every kl2 code byte changed above (default build: none) */
    anp_log("ANP loader: init done (dir %s)", g_dir);
    return TRUE;
}
