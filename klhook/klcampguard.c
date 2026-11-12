/* klcampguard.c - [CampGuard]: luvsic's crash guards for the converted Dead Men CAMPAIGN levels, as byte-checked exact-site branches
 * inside KLHook's one vectored handler (veh() in klhook.c calls klcg_veh() first thing for a fault inside kl2.exe).
 * Ported from luvsic's a-newer-perspective loader/anp_loader.c @32aa649 (cl_guard, gfx_guard, coll_guard, snd_guard, divide guard, null
 * sound-list guard, boneslights_guard; ~160-290 and ~1287-1465) and loader/heapguard.inc (in contribution with luvsic). His legacy CODE
 * patches (0x6d100f, 0x71166d, ...) are NOT ported: this module changes no kl2.exe code byte (SHIP / CEG safe), it edits the faulting
 * thread's context, the stack, heap blocks and one .data pointer. Decision logic, site table and byte signatures: klcampguard_logic.h.
 *
 * Keys, all default 0 ("(recommended off)" until benched), section [CampGuard]:
 *   ListUser   CListUser bucket-walk guard (0x4f8a8e/92/97/9e and the slot read 0x4f8a6e), campaign levels only
 *   ListUserFA the SAME guard on EVERY map (Dog Days' 9 FA maps, Dead Men FA maps, Arcade, private, online)
 *   Gfx        ZGraphic template int3 0x51f1a9 (fail branch only, no fallback-graphic retry)
 *   Coll       collision octree callback 0x927b4c / 0x927b4e / the call 0x927b59
 *   Snd        stream rate 0 at 0x44668b -> 22050
 *   SndDiv     any other divide by zero in 0x446600..0x4b3000 (divisor -> 1)
 *   NullList   null sound list 0x900ff8
 *   BonesLights  v4BonesLights null light block 0x577e08
 *   Heap       heap block unlink int3 0x4665dc (leaks that block)
 * Every guard except ListUserFA needs the campaign gate (klcampaign_gate.h: [Campaign] Enable=1 AND a converted story level m01..m14 loaded), so on
 * the FA maps / Arcade / private / online they never resume anything. A fault that is not an exact match is not touched: it reaches
 * KLHook's normal ASSERT / CRASH logging and dump. A resumed fault is NOT counted as an assert or crash and writes no dump; it is counted here
 * and logged at the 1st-3rd hit and every power of two ("campguard: ...").
 *
 * ListUserFA is the owner's open DM03 crash (2026-11-09 16:46, debug/notes/2026-11-09-dm03-fedrespawn-crash.md): c0000005 at 0x4f8a8e reading
 * 0x4f09, callers 0x6307ed (CListUser walk 0x630700) < 0x5bfc05, a record with id 0 (released while still in the per-frame list) after the police
 * respawn. That crash is owned by another session (d0); this key only makes the guard available. WHAT RESUMING THERE SKIPS: 0x4f8a60 is "remove value
 * from the hash chain [this+0x20][key]"; the walk only READ before it faulted (no write), so the table is not half-edited. The resume is the
 * function's own "not found" return (eax = 0): the value (id 0x741 in that dump) is NOT unlinked from its bucket. GUESS: harmless unless that
 * value is freed later while still linked (then a later walk of its bucket reads freed memory), and the id-0 record stays in the per-frame list
 * for the walk to meet again (each meeting is another guarded miss, not a crash). It hides the symptom, not the writer of [rec+0x54] = 0. NOT BENCHED.
 *
 * NOT PORTED (slice notes): the text word-wrap watchdog (0x8a3e60, needs a thread that suspends the game thread; diagnostic-grade, the cause was DM
 * 20-byte glyph records which the converter fixes), herowatch (DR0 diagnostics), the D3D reset guard (resetguard.inc: Dog Days' klfps.c
 * [Graphics] ResetDrain already empties both render command lists after every successful Reset, lost path and the 3 mode-change callers), and the
 * ZGraphic fallback-graphic retry. */
#include "klcampaign_gate.h"
#include "klcampguard_logic.h"

static unsigned klcg_mask;                         /* groups switched on */
static int klcg_fa;                                /* ListUserFA: the CListUser guard on every map */
static volatile LONG klcg_hits[KLCG_NSITE], klcg_refused;
static __declspec(align(16)) unsigned char klcg_nolights[0x80];     /* the zero light block of the BonesLights guard (heap/.data of this DLL) */

static int klcg_mem_rdn(void *u, unsigned addr, void *out, int n) { (void)u; return klh_rd((DWORD_PTR)addr, out, (SIZE_T)n); }

static int klcg_veh(EXCEPTION_POINTERS *ep)
{   /* 1 = the fault was an exact known site, the context is edited, resume */
    EXCEPTION_RECORD *r = ep->ExceptionRecord; CONTEXT *c = ep->ContextRecord;
    klcg_in in; klcg_act a; klcg_mem m; int site; unsigned g; LONG n; unsigned i;
    if (!klcg_mask || !klh_exe_ok || klh_delta) return 0;
    in.code = r->ExceptionCode; in.at = (unsigned)(DWORD_PTR)r->ExceptionAddress; in.nparam = r->NumberParameters;
    in.info0 = r->NumberParameters > 0 ? (unsigned)r->ExceptionInformation[0] : 0;
    in.info1 = r->NumberParameters > 1 ? (unsigned)r->ExceptionInformation[1] : 0;
    in.eip = c->Eip;
    in.reg[KLCG_EAX] = c->Eax; in.reg[KLCG_ECX] = c->Ecx; in.reg[KLCG_EDX] = c->Edx; in.reg[KLCG_EBX] = c->Ebx;
    in.reg[KLCG_ESP] = c->Esp; in.reg[KLCG_EBP] = c->Ebp; in.reg[KLCG_ESI] = c->Esi; in.reg[KLCG_EDI] = c->Edi;
    m.u = 0; m.rdn = klcg_mem_rdn;
    site = klcg_decide(&m, &in, klcg_mask, (unsigned)(DWORD_PTR)klcg_nolights, &a);
    if (!site) return 0;
    g = klcg_group(site);
    /* the gate, last (it reads the scene name): the CListUser guard may also run on any map when ListUserFA=1 */
    if (!(g == KLCG_G_LISTUSER && klcg_fa) && !klcmp_level_active()) {
        if (InterlockedIncrement(&klcg_refused) <= 3)
            klog("campguard: %s matched at %08x but no campaign level is loaded ([Campaign] Enable / scene): left to the normal crash path", klcg_name(site), in.at);
        return 0;
    }
    for (i = 0; i < a.npoke; i++) *(DWORD *)(DWORD_PTR)a.poke[i].a = a.poke[i].v;           /* stack / heap / .data of the game, addresses proven readable by the logic */
    if (a.zeroN) memset((void *)(DWORD_PTR)a.zeroAt, 0, a.zeroN);
    for (i = 0; i < 8; i++) if (a.regset & (1u << i)) switch (i) {
        case KLCG_EAX: c->Eax = a.reg[i]; break; case KLCG_ECX: c->Ecx = a.reg[i]; break; case KLCG_EDX: c->Edx = a.reg[i]; break; case KLCG_EBX: c->Ebx = a.reg[i]; break;
        case KLCG_ESP: c->Esp = a.reg[i]; break; case KLCG_EBP: c->Ebp = a.reg[i]; break; case KLCG_ESI: c->Esi = a.reg[i]; break; case KLCG_EDI: c->Edi = a.reg[i]; break; }
    c->Eip = a.eip;
    n = InterlockedIncrement(&klcg_hits[site]);
    if (klcg_log_now(n))
        klog("campguard: %s at %08x resumed at %08x (hit %ld; %08x %08x)%s", klcg_name(site), in.at, a.eip, n, a.i0, a.i1,
             g == KLCG_G_LISTUSER && klcg_fa && !klcmp_level_active() ? " [ListUserFA, not a campaign level]" : "");
    return 1;
}

static void klcg_init(void)
{
    static const struct { const char *key; unsigned bit; } k[] = { { "ListUser", KLCG_G_LISTUSER }, { "Gfx", KLCG_G_GFX }, { "Coll", KLCG_G_COLL }, { "Snd", KLCG_G_SND },
        { "SndDiv", KLCG_G_SNDDIV }, { "NullList", KLCG_G_NULLLIST }, { "BonesLights", KLCG_G_BONES }, { "Heap", KLCG_G_HEAP } };
    unsigned i;
    klcg_mask = 0; klcg_fa = GetPrivateProfileIntA("CampGuard", "ListUserFA", 0, klh_ini) != 0;
    for (i = 0; i < sizeof k / sizeof k[0]; i++) if (GetPrivateProfileIntA("CampGuard", k[i].key, 0, klh_ini)) klcg_mask |= k[i].bit;
    if (klcg_fa) klcg_mask |= KLCG_G_LISTUSER;
    klcg_any = klcg_mask != 0;
    if (klcg_mask) klog("campguard: groups %02x (ListUserFA %d); campaign gate [Campaign] Enable=%d; exact-site VEH branches, no code bytes changed", klcg_mask, klcg_fa, klcmp_enabled());
}
