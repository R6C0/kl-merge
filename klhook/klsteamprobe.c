/* klsteamprobe.c: [Net] SteamProbe=1 - a LOG-ONLY probe for a future real two-PC internet session (re/side_channel_steam.md). Sends NOTHING,
   calls no method on any returned interface (the GetISteamNetworking call itself is real work on Steam's side, from the game thread; a null result is the expected "not served" answer). Once per online session, on the game thread, in a round (the klsy_tick gate: session manager
   with a good vtable, state 0x13..0x1f) and with the peer table singleton [0x168f960] non-null and a non-empty table:
     1. steam_api.dll exports SteamClient / SteamAPI_GetHSteamUser / SteamAPI_GetHSteamPipe (logged)
     2. ISteamClient vtable +0x44 (index 17, READ in SteamAPI_Init: args user, pipe, version string) for "SteamNetworking005", then "004"
     3. the peer table: count, per entry (max 16) the u64 id at +1 and byte +9 (klh_rd, never faults)
     4. own SteamID: SKIPPED (ISteamUser +8 returns a CSteamID, a non-POD by value: the hidden-pointer ABI is a GUESS, not worth a crash)
   Any fault in the calls -> logged, probe disabled. AFTER klhook.c's klh_rd, klog. Line prefix "steamprobe:". */

/* [Net] SideChannelSteam=1 (2026-10-29, step 1 of re/side_channel_steam.md) turns the SAME log-only probe on and adds a peer-table dump once a minute (at most 20 lines
   a session, guarded reads). [Net] SteamProbe=1 is the older switch for the one-shot part only. Pure part (version order, vtable offset, entry parse, log budget): klsteamside.h,
   checked by klsteamside_test.c. Nothing is sent or read from any packet queue by either switch. */
#include "klsteamside.h"

static int klsp_on, klsp_done, klsp_dead, klsp_side, klsp_used, klsp_have_last;
static DWORD klsp_last;

static int klsp_calls(void)
{   /* the only code that calls into steam; the caller wraps it in __try */
    HMODULE h = GetModuleHandleA("steam_api.dll");
    typedef void *(__cdecl *getc_t)(void);
    typedef int (__cdecl *geth_t)(void);
    getc_t pc; geth_t pu, pp; void *cli; int hu, hp, k;
    if (!h) { klog("steamprobe: steam_api.dll not loaded"); return 1; }
    pc = (getc_t)GetProcAddress(h, "SteamClient"); pu = (geth_t)GetProcAddress(h, "SteamAPI_GetHSteamUser"); pp = (geth_t)GetProcAddress(h, "SteamAPI_GetHSteamPipe");
    klog("steamprobe: exports SteamClient %p SteamAPI_GetHSteamUser %p SteamAPI_GetHSteamPipe %p", (void *)pc, (void *)pu, (void *)pp);
    if (!pc || !pu || !pp) return 1;
    cli = pc(); hu = pu(); hp = pp();
    klog("steamprobe: SteamClient() %p hUser %d hPipe %d", cli, hu, hp);
    if (!cli) return 1;
    {   DWORD vt = 0, fn = 0;
        if (!klh_rd((DWORD_PTR)cli, &vt, 4) || !klh_rd(vt + KLSS_GETNET_VOFF, &fn, 4) || !fn) { klog("steamprobe: ISteamClient vtable unreadable"); return 1; }
        klog("steamprobe: ISteamClient vtable 0x%08lx [+0x44] 0x%08lx", (unsigned long)vt, (unsigned long)fn);
        for (k = 0; k < KLSS_NVER; k++) {
            /* READ in steam_api.dll (the Dog Days copy), SteamAPI_Init 0x3b403570..0x3b40366d and a second copy at 0x3b404715..0x3b40473e:
                 mov ecx,[client]; mov eax,[ecx]; mov edx,[eax+0x44]; push "SteamNetworking003"; push esi; push edi; call edx
               with esi = [0x3b417e8c] = the value SteamAPI_GetHSteamPipe returns and edi = [0x3b417e90] = SteamAPI_GetHSteamUser's. So: vtable byte offset 0x44 (index 17),
               THISCALL (ecx = client, callee pops 12), args pushed right to left = (hUser, hPipe, const char *version). Only the version string differs for 004/005.
               That 004/005 are served by steamclient.dll, and that their SendP2PPacket slots are unchanged, is NOT readable offline: the null/non-null log line is the answer.
               Done as __fastcall(this, edx dummy, ...) like klsteam.c. */
            void *ni = ((void *(__fastcall *)(void *, void *, int, int, const char *))fn)(cli, 0, hu, hp, klss_ver(k));
            DWORD nvt = 0, m0 = 0, m1 = 0, m2 = 0;
            if (ni) { klh_rd((DWORD_PTR)ni, &nvt, 4); if (nvt) { klh_rd(nvt, &m0, 4); klh_rd(nvt + 4, &m1, 4); klh_rd(nvt + 8, &m2, 4); } }
            klog("steamprobe: GetISteamNetworking(\"%s\") -> %p vtable 0x%08lx slots 0..2 0x%08lx 0x%08lx 0x%08lx", klss_ver(k), ni, (unsigned long)nvt, (unsigned long)m0, (unsigned long)m1, (unsigned long)m2);
        }
    }
    return 0;
}

static void klsp_init(void)
{
    klsp_side = GetPrivateProfileIntA("Net", "SideChannelSteam", 0, klh_ini) != 0;       /* (recommended off) log only, sends nothing */
    klsp_on = klsp_side || GetPrivateProfileIntA("Net", "SteamProbe", 0, klh_ini) != 0;  /* (recommended off) log only, sends nothing */
}

/* One peer-table dump through the log budget (<= 1 line per minute-dump header + one per peer, 20 lines a session). Guarded reads only (klh_rd never faults). */
static void klsp_peers(DWORD state, DWORD tab, DWORD cnt, const char *why)
{
    DWORD now = GetTickCount(), k; int allowed, want = 1 + (int)(cnt < 16 ? cnt : 16);
    allowed = klss_dump_budget(now, klsp_last, klsp_have_last, klsp_used, want);
    if (!allowed) return;
    klsp_used += allowed; klsp_last = now; klsp_have_last = 1;
    klog("steamprobe: %s: round state 0x%lx, peer table %08lx count %lu", why, (unsigned long)state, (unsigned long)tab, (unsigned long)cnt);
    for (k = 0; k < cnt && k < 16 && (int)k + 1 < allowed; k++) {
        unsigned char e[16]; klss_peer p; int ok = klh_rd(tab + 16 * k, e, 16), good = ok && klss_peer_parse(e, &p);
        if (!ok) klog("steamprobe: peer %lu (unreadable)", (unsigned long)k);
        else klog("steamprobe: peer %lu id %08lx%08lx flag9 %u%s", (unsigned long)k, good ? p.id_hi : 0, good ? p.id_lo : 0, (unsigned)e[9], good ? "" : " (empty)");
    }
    if (klsp_used >= KLSS_MAX_LINES) klog("steamprobe: peer-table log budget spent (%d lines), silent from now on", KLSS_MAX_LINES);
}

static void klsp_tick(int game_thread)
{
    DWORD sm, state = 0, s, tab = 0, cnt = 0;
    if (!klsp_on || klsp_dead || !game_thread || !klh_exe_ok) return;
    if (klsp_done && (!klsp_side || klsp_used >= KLSS_MAX_LINES)) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x70, &state, 4) || state < 0x13 || state > 0x1f) return;           /* the klsy_tick round window */
    if (!(s = klh_rd32((DWORD_PTR)KLH_VA(0x0168f960)))) return;                           /* GUESS: [0x168f960] holds a POINTER to the singleton (re/netcode.md only says "global"); if it is the object itself the probe stays silent. Not on System Link */
    if (!klh_rd(s + 0x28, &tab, 4) || !klh_rd(s + 0x2c, &cnt, 4) || !klss_table_ok(tab, cnt)) return;
    if (klsp_done) { klsp_peers(state, tab, cnt, "peers"); return; }                      /* SideChannelSteam: the once-a-minute table dump */
    klsp_done = 1;
    klsp_peers(state, tab, cnt, "first look");
    klog("steamprobe: own SteamID skipped (ISteamUser+8 by-value CSteamID ABI is a GUESS)");
    __try { klsp_calls(); }
    __except (EXCEPTION_EXECUTE_HANDLER) { klsp_dead = 1; klog("steamprobe: FAULT 0x%08lx in the steam calls, probe disabled", (unsigned long)GetExceptionCode()); }
    klog("steamprobe: done (nothing was sent)");
}
