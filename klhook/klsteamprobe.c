/* klsteamprobe.c: [Net] SteamProbe=1 - a LOG-ONLY probe for a future real two-PC internet session (re/side_channel_steam.md). Sends NOTHING,
   calls no method on any returned interface. Once per online session, on the game thread, in a round (the klsy_tick gate: session manager
   with a good vtable, state 0x13..0x1f) and with the peer table singleton [0x168f960] non-null and a non-empty table:
     1. steam_api.dll exports SteamClient / SteamAPI_GetHSteamUser / SteamAPI_GetHSteamPipe (logged)
     2. ISteamClient vtable +0x44 (index 17, READ in SteamAPI_Init: args user, pipe, version string) for "SteamNetworking005", then "004"
     3. the peer table: count, per entry (max 16) the u64 id at +1 and byte +9 (klh_rd, never faults)
     4. own SteamID: SKIPPED (ISteamUser +8 returns a CSteamID, a non-POD by value: the hidden-pointer ABI is a GUESS, not worth a crash)
   Any fault in the calls -> logged, probe disabled. AFTER klhook.c's klh_rd, klog. Line prefix "steamprobe:". */

static int klsp_on, klsp_done, klsp_dead;

static int klsp_calls(void)
{   /* the only code that calls into steam; the caller wraps it in __try */
    HMODULE h = GetModuleHandleA("steam_api.dll");
    typedef void *(__cdecl *getc_t)(void);
    typedef int (__cdecl *geth_t)(void);
    getc_t pc; geth_t pu, pp; void *cli; int hu, hp, k;
    static const char *const ver[2] = { "SteamNetworking005", "SteamNetworking004" };
    if (!h) { klog("steamprobe: steam_api.dll not loaded"); return 1; }
    pc = (getc_t)GetProcAddress(h, "SteamClient"); pu = (geth_t)GetProcAddress(h, "SteamAPI_GetHSteamUser"); pp = (geth_t)GetProcAddress(h, "SteamAPI_GetHSteamPipe");
    klog("steamprobe: exports SteamClient %p SteamAPI_GetHSteamUser %p SteamAPI_GetHSteamPipe %p", (void *)pc, (void *)pu, (void *)pp);
    if (!pc || !pu || !pp) return 1;
    cli = pc(); hu = pu(); hp = pp();
    klog("steamprobe: SteamClient() %p hUser %d hPipe %d", cli, hu, hp);
    if (!cli) return 1;
    {   DWORD vt = 0, fn = 0;
        if (!klh_rd((DWORD_PTR)cli, &vt, 4) || !klh_rd(vt + 0x44, &fn, 4) || !fn) { klog("steamprobe: ISteamClient vtable unreadable"); return 1; }
        klog("steamprobe: ISteamClient vtable 0x%08lx [+0x44] 0x%08lx", (unsigned long)vt, (unsigned long)fn);
        for (k = 0; k < 2; k++) {
            /* GUESS (review of side_channel_steam.md, READ in SteamAPI_Init): thiscall, args hUser, hPipe, const char *version; done as __fastcall(this, edx dummy, ...) like klsteam.c */
            void *ni = ((void *(__fastcall *)(void *, void *, int, int, const char *))fn)(cli, 0, hu, hp, ver[k]);
            DWORD nvt = 0, m0 = 0, m1 = 0, m2 = 0;
            if (ni) { klh_rd((DWORD_PTR)ni, &nvt, 4); if (nvt) { klh_rd(nvt, &m0, 4); klh_rd(nvt + 4, &m1, 4); klh_rd(nvt + 8, &m2, 4); } }
            klog("steamprobe: GetISteamNetworking(\"%s\") -> %p vtable 0x%08lx slots 0..2 0x%08lx 0x%08lx 0x%08lx", ver[k], ni, (unsigned long)nvt, (unsigned long)m0, (unsigned long)m1, (unsigned long)m2);
        }
    }
    return 0;
}

static void klsp_init(void)
{
    klsp_on = GetPrivateProfileIntA("Net", "SteamProbe", 0, klh_ini) != 0;               /* (recommended off) log only, sends nothing */
}

static void klsp_tick(int game_thread)
{
    DWORD sm, state = 0, s, tab = 0, cnt = 0, k;
    if (!klsp_on || klsp_done || klsp_dead || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm))) return;
    if (!klh_rd(sm + 0x70, &state, 4) || state < 0x13 || state > 0x1f) return;           /* the klsy_tick round window */
    if (!(s = klh_rd32((DWORD_PTR)KLH_VA(0x0168f960)))) return;                           /* the peer table singleton (not on System Link) */
    if (!klh_rd(s + 0x28, &tab, 4) || !klh_rd(s + 0x2c, &cnt, 4) || !tab || !cnt || cnt > 4096) return;
    klsp_done = 1;
    klog("steamprobe: round state 0x%lx, peer table %08lx count %lu", (unsigned long)state, (unsigned long)tab, (unsigned long)cnt);
    for (k = 0; k < cnt && k < 16; k++) {
        unsigned char e[16]; unsigned __int64 id = 0; int ok = klh_rd(tab + 16 * k, e, 16);
        if (ok) memcpy(&id, e + 1, 8);
        klog("steamprobe: peer %lu id %016I64x flag9 %u%s", (unsigned long)k, id, ok ? e[9] : 0, ok ? "" : " (unreadable)");
    }
    klog("steamprobe: own SteamID skipped (ISteamUser+8 by-value CSteamID ABI is a GUESS)");
    __try { klsp_calls(); }
    __except (EXCEPTION_EXECUTE_HANDLER) { klsp_dead = 1; klog("steamprobe: FAULT 0x%08lx in the steam calls, probe disabled", (unsigned long)GetExceptionCode()); }
    klog("steamprobe: done (nothing was sent)");
}
