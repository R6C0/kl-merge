/*
 * klserver.c - [Server] HOST-SERVER MODE: this copy of Kane & Lynch 2 keeps hosting a Quick Match (Join Game) or Ranked
 * Fragile Alliance lobby by itself, so players can just join. Part of KLHook (included by klhook.c after klslot.c, SHIP and
 * TEST alike). Default OFF, and then nothing here runs. NOTHING OF IT HAS RUN IN THE GAME (written 2026-10-25, offline).
 *
 * Dog Days has no dedicated server: a "server" is a PC running kl2.exe (one Steam account per copy, a GPU and a window) that sits in
 * the host's seat. re\online_server.md has the reading of the exe that this file is built on.
 *
 * WHAT IT DOES (all through the game's own menu code, on the game thread, called from klh_tick; no byte of kl2.exe's code is written, so
 * it is SHIP-safe; the only writes are the lobby target byte [sm+0xb9] (data) and the menu option values (the game's own setter)):
 *  1. MENU: with no network session and a window stack that can be read, after BootSec it sets the menu options
 *       Quick: MP_RankedGame=1, MP_PrivateGame=0     Ranked: MP_RankedGame=0, MP_PrivateGame=0
 *     (what the buttons Option="MP_RankedGame" OptionValue= of frontend.xml do), opens the window the Play page would open
 *       Quick: QuickPlayerMatch     Ranked: XBoxLiveCreateRanked
 *     (0x6bee50, the call klauto's 'open' makes) and sends "FA" to its game-mode toggle (SLCreateGameModeQuickPlayerMatch /
 *     SLCreateGameModeXboxLive; what the 'Fragile Alliance' line does: kl2.exe 0x474e10..0x4752bc). That reaches the session manager's
 *     QuickJoin 0x4196e0(1,1) - CERTAIN from the disassembly for both: it SEARCHES lobbies first and CREATES a public FA lobby when none
 *     is found (random available level, MP_PrivateGame=0, create 0x6c9c10). So a server that finds a fellow server joins it as a client,
 *     which is why two servers of the same BuildKey/OnlineSet should not run at once on one lobby list (re\online_server.md).
 *  2. LOBBY: as the host (role 2, game type 4) in the lobby state 0xd it waits WaitSec for players. When MinPlayers are connected and the
 *     wait is over (or the lobby is full) it lowers the lobby target [sm+0xb9] to the number connected (kllobby.c's lever) and, with 2 or
 *     more connected, calls 0x6484d0(n) so the clients' copy follows (re\lobby_start.md 4; GUESS that this call is safe on its own).
 *     The 15 s countdown of 0x6c49a0 then moves 0xd -> 0xe -> 0xf by itself (GUESS, re\lobby_start.md 3). PressReady=1 adds a fallback:
 *     if the lobby is still in 0xd 25 s after the lowering, RETURN then SPACE are sent as scan codes (the keys the proven System Link
 *     script uses for the host's Ready; needs the window in front).
 *  3. AFTER THE ROUND (or when the session closes): when the machine is no longer a hosting session for RehostSec it starts again at 1.
 *
 * [Server] Enable=1 implies [Lobby] Solo=1 (kllobby.c: the lone host's error word is dropped, no 'all players left' window) and
 * MinPlayers=1 for kllobby. It does NOT switch on [Net] BuildKey: with BuildKey=0 any player, mod or not, can find the lobby (the owner
 * accepts that); BuildKey=1 (klmm.c, keyed by map set too) keeps it to players with the same maps and OnlineSet. A log line says which.
 *
 * THE HOST'S OWN PLAYER takes part in the round (CERTAIN: it is a normal host seat): it stands in its spawn. Nothing spectates it.
 *
 * KLHook.ini
 *   [Server]
 *   Enable=0        (recommended off) 1 = host a lobby for others, see above
 *   Mode=quick      quick = Player Match 'Join Game' (QuickJoin, public lobby)   ranked = Ranked (type 3 lobby, Ranked flag set)
 *   MinPlayers=2    humans connected (the host counts) before the wait may end early to a start; 1 = start alone after the wait (bots with [Bots] OnlineFill)
 *   WaitSec=45      seconds the lobby stays open for joiners before the target is lowered
 *   BootSec=10      seconds after the first readable menu before the first attempt
 *   SearchSec=60    seconds one 'search, else create' attempt may take before the menu is opened again
 *   RehostSec=10    seconds between the end of a session and the next attempt
 *   PressReady=0    1 = the RETURN / SPACE fallback above
 *   Log=1
 * LOG (KLHook.log)  server: ... ; pass = 'server: lobby open' then 'server: lobby target ... lowered' then the game's own load line
 */
#ifndef KLSERVER_C
#define KLSERVER_C

static int klsv_on, klsv_ranked, klsv_min = 2, klsv_wait = 45, klsv_boot = 10, klsv_search = 60, klsv_rehost = 10, klsv_ready, klsv_log = 1;

static void klsv_init(void)
{
    char m[16];
    klsv_on = GetPrivateProfileIntA("Server", "Enable", 0, klh_ini) != 0;
    if (!klsv_on) return;
    GetPrivateProfileStringA("Server", "Mode", "quick", m, sizeof m, klh_ini);
    klsv_ranked = !_stricmp(m, "ranked");
    if (_stricmp(m, "ranked") && _stricmp(m, "quick")) klog("server: Mode=%s is not quick or ranked: quick", m);
    klsv_min = (int)GetPrivateProfileIntA("Server", "MinPlayers", 2, klh_ini); if (klsv_min < 1 || klsv_min > 8) klsv_min = 2;
    klsv_wait = (int)GetPrivateProfileIntA("Server", "WaitSec", 45, klh_ini); if (klsv_wait < 0 || klsv_wait > 3600) klsv_wait = 45;
    klsv_boot = (int)GetPrivateProfileIntA("Server", "BootSec", 10, klh_ini); if (klsv_boot < 0 || klsv_boot > 600) klsv_boot = 10;
    klsv_search = (int)GetPrivateProfileIntA("Server", "SearchSec", 60, klh_ini); if (klsv_search < 10 || klsv_search > 600) klsv_search = 60;
    klsv_rehost = (int)GetPrivateProfileIntA("Server", "RehostSec", 10, klh_ini); if (klsv_rehost < 1 || klsv_rehost > 600) klsv_rehost = 10;
    klsv_ready = GetPrivateProfileIntA("Server", "PressReady", 0, klh_ini) != 0;
    klsv_log = GetPrivateProfileIntA("Server", "Log", 1, klh_ini) != 0;
    klog("server: ON - mode %s, MinPlayers %d, WaitSec %d, BootSec %d, SearchSec %d, RehostSec %d, PressReady %d (implies [Lobby] Solo=1; NOT run live)",
         klsv_ranked ? "RANKED" : "quick", klsv_min, klsv_wait, klsv_boot, klsv_search, klsv_rehost, klsv_ready);
    if (!GetPrivateProfileIntA("Net", "BuildKey", 0, klh_ini))
        klog("server: [Net] BuildKey=0: players WITHOUT the mod's maps can find this lobby%s", GetPrivateProfileIntA("Expansion", "OnlineSet", 0, klh_ini) ? " and will fail to load the OnlineSet map" : "");
}

/* the open windows of the menu: names bottom to top; -> count (0 = no readable stack) */
static int klsv_stack(char *top, int cap, char *all, int allcap)
{
    DWORD gd, mgr, w, n, i, win[24]; char nm[64]; int len = 0;
    top[0] = 0; all[0] = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT || !(w = klh_rd32(mgr + 4)) || klh_rd32(w) != KLS_WSYS_VT) return 0;
    n = klh_rd32(w + 0x328);
    if (!n || n > 24 || !klh_rd(w + 0x330, win, 4 * n)) return 0;
    for (i = 0; i < n; i++) {
        kls_win_name(win[i], nm, sizeof nm);
        if (len < allcap - 70) len += snprintf(all + len, allcap - len, "%s%s", i ? " > " : "", nm[0] ? nm : "?");
        if (i == n - 1) { strncpy(top, nm, cap - 1); top[cap - 1] = 0; }
    }
    return (int)n;
}

static void klsv_option(const char *name, int value)
{   /* the menu option object's set (vtable slot 5, 0x472450 or klchar.c's wrapper), then a read back (slot 2) for the log */
    DWORD obj = klh_rd32((DWORD_PTR)KLH_VA(KLC_OPTIONS)), vt, set, get;
    if (!obj || klh_rd32(obj) == 0 || !(vt = klh_rd32(obj)) || !(set = klh_rd32(vt + 4 * 5)) || !(get = klh_rd32(vt + 4 * 2))) { klog("server: option object not ready, %s not set", name); return; }
    ((void (__fastcall *)(void *, void *, const char *, int, int))(DWORD_PTR)set)((void *)(DWORD_PTR)obj, 0, name, value, 0);
    if (klsv_log) klog("server: option %s = %d (read back %d)", name, value, ((int (__fastcall *)(void *, void *, const char *, int))(DWORD_PTR)get)((void *)(DWORD_PTR)obj, 0, name, 0));
}

static int klsv_open(const char *win)
{   /* what klauto 'open' does: window system->0x6bee50(name, 1, 0, 1) */
    DWORD gd, mgr, w;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT || !(w = klh_rd32(mgr + 4)) || klh_rd32(w) != KLS_WSYS_VT) return 0;
    ((void (__fastcall *)(void *, void *, const char *, int, int, int))(DWORD_PTR)KLH_VA(0x6bee50))((void *)(DWORD_PTR)w, 0, win, 1, 0, 1);
    return 1;
}

static int klsv_msg(const char *elem, const char *msg)
{   /* what ZSendMessage does: find the element by name (0x83faf0), call its slot 20 (vtable + 0x50) with a pointer to the text pointer */
    DWORD gd, mgr, vt, fn; void *e;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824))) return 0;
    e = ((void *(__fastcall *)(void *, void *, const char *))(DWORD_PTR)KLH_VA(0x83faf0))((void *)(DWORD_PTR)mgr, 0, elem);
    if (!e) { klog("server: no GUI element '%s' in the open pages", elem); return 0; }
    vt = klh_rd32((DWORD_PTR)e); fn = vt ? klh_rd32(vt + 0x50) : 0;
    if (!kls_in_image(fn)) { klog("server: element '%s' at %p has no kl2.exe slot 20 (%08lx)", elem, e, (unsigned long)fn); return 0; }
    ((void (__fastcall *)(void *, void *, const char **))(DWORD_PTR)fn)(e, 0, &msg);
    return 1;
}

static void klsv_key(WORD scan)
{   /* user32 is looked up at run time (the DLL is not linked against it, as klqol2.c) */
    INPUT in[2]; static BOOL (WINAPI *si)(UINT, LPINPUT, int); static HWND (WINAPI *fg)(void); static DWORD (WINAPI *tid)(HWND, LPDWORD); HWND f; DWORD pid = 0;
    if (!si) {
        HMODULE u = GetModuleHandleA("user32.dll");
        if (u) { si = (BOOL (WINAPI *)(UINT, LPINPUT, int))GetProcAddress(u, "SendInput"); fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); tid = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
    }
    if (!si || !fg || !tid || !(f = fg())) return;
    tid(f, &pid);
    if (pid != GetCurrentProcessId()) { klog("server: PressReady: the game window is not in front, key 0x%02x not sent", scan); return; }
    memset(in, 0, sizeof in);
    in[0].type = INPUT_KEYBOARD; in[0].ki.wScan = scan; in[0].ki.dwFlags = KEYEVENTF_SCANCODE;
    in[1].type = INPUT_KEYBOARD; in[1].ki.wScan = scan; in[1].ki.dwFlags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP;
    si(2, in, sizeof(INPUT));
}

static void klsv_tick(int game_thread)
{
    static DWORD last, sm_last, lobby_t, lowered_t, online_t, phase_t, next_t, boot_t, said_t; static int phase, tries, armed = 1, lowered, keys;
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, st = 0; char top[64], all[240]; int n;
    if (!klsv_on || !game_thread || !klh_exe_ok || now - last < 250) return;
    last = now;
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION));
    if (sm) { klh_rd(sm + 0x54, &role, 4); klh_rd(sm + 0x5c, &mode, 4); klh_rd(sm + 0x70, &st, 4); }

    if (sm && role == 2 && mode == 4 && KLH_SM_VT_OK(klh_rd32(sm))) {               /* ---- hosting a FA session */
        BYTE cur = 0; int conn = kllb_connected(sm);
        online_t = now; phase = 2; tries = 0;
        klh_rd(sm + 0xb9, &cur, 1);
        if (st != 0xd && st != 0xe && st != 0xf) { armed = 1; return; }               /* between lobbies / in a round */
        if (armed && st == 0xd) {
            armed = 0; lowered = 0; keys = 0; lobby_t = now; said_t = now;
            klog("server: lobby open (state 0x%lx, target %u, %d connected): waiting %d s for %d player(s) - the lobby is %s", (unsigned long)st, cur, conn, klsv_wait, klsv_min, klsv_ranked ? "ranked" : "public (Quick Match)");
        }
        if (armed || lowered) {
            if (lowered && klsv_ready && st == 0xd && keys < 8 && now - lowered_t > 25000 + 20000 * (DWORD)keys) {
                klog("server: PressReady: still in 0xd %lu s after the lowering: RETURN then SPACE (try %d)", (unsigned long)((now - lowered_t) / 1000), keys + 1);
                klsv_key(0x1c); Sleep(120); klsv_key(0x39); keys++;
            }
            return;
        }
        if (now - said_t >= 60000) { said_t = now; klog("server: lobby still open, state 0x%lx, %d of target %u connected", (unsigned long)st, conn, cur); }
        if (conn < 1 || conn > 12) return;
        if ((conn >= klsv_min && now - lobby_t >= (DWORD)klsv_wait * 1000) || (conn >= (int)cur && conn >= 2)) {
            BYTE want = (BYTE)conn;
            if (cur > want) {
                if (!kllb_orig) kllb_orig = cur;                                    /* klbotfill.c: bots fill target - connected */
                if (klh_data((void *)(DWORD_PTR)(sm + 0xb9), &want, 1, "lobby target players"))
                    klog("server: lobby target %u -> %d (%d connected after %lu s): the round starts when the game's countdown runs out", cur, conn, conn, (unsigned long)((now - lobby_t) / 1000));
                if (conn >= 2) {                                                    /* GUESS (re\lobby_start.md 4): carries the number to the clients' replicated variable */
                    __try { ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(0x6484d0))((void *)(DWORD_PTR)sm, 0, conn); klog("server: 0x6484d0(%d) called (client copy of the target)", conn); }
                    __except (EXCEPTION_EXECUTE_HANDLER) { klog("server: 0x6484d0(%d) faulted: not repeated", conn); }
                }
            }
            lowered = 1; lowered_t = now;
        }
        return;
    }

    /* ---- no hosting session */
    if (sm && role == 3) {                                                          /* QuickJoin found a lobby and joined it as a client: stay until it is over */
        if (sm_last != sm) { sm_last = sm; klog("server: joined another host's lobby as a client (state 0x%lx): staying until that session ends", (unsigned long)st); }
        online_t = now; return;
    }
    if (online_t && now - online_t < (DWORD)klsv_rehost * 1000) return;
    if (online_t) { klog("server: the hosted session is over (role %lu, state 0x%lx): hosting again", (unsigned long)role, (unsigned long)st); online_t = 0; phase = 0; tries = 0; armed = 1; }
    n = klsv_stack(top, sizeof top, all, sizeof all);
    if (!n) return;                                                                 /* a load or no menu: wait */
    if (!boot_t) { boot_t = now; if (klsv_log) klog("server: menu readable [%s], first attempt in %d s", all, klsv_boot); }
    if (now - boot_t < (DWORD)klsv_boot * 1000 || now < next_t) return;
    {   const char *win = klsv_ranked ? "XBoxLiveCreateRanked" : "QuickPlayerMatch", *el = klsv_ranked ? "SLCreateGameModeXboxLive" : "SLCreateGameModeQuickPlayerMatch";
        if (phase == 0) {
            if (tries >= 20) { klog("server: 20 attempts without a session: waiting 5 min"); tries = 0; next_t = now + 300000; return; }
            klsv_option("MP_RankedGame", klsv_ranked ? 0 : 1);
            klsv_option("MP_PrivateGame", 0);
            if (!_stricmp(top, win)) { phase = 1; phase_t = now - 2000; return; }
            klog("server: attempt %d: menu [%s] -> open %s", tries + 1, all, win);
            if (klsv_open(win)) { phase = 1; phase_t = now; }
            else next_t = now + 3000;
        } else if (phase == 1) {
            if (_stricmp(top, win)) { if (now - phase_t > 15000) { klog("server: %s did not come to the top (top is %s): again", win, top); phase = 0; tries++; } return; }
            if (now - phase_t < 1500) return;
            klog("server: %s open: sending FA to %s (QuickJoin: search, else create)", win, el);
            if (klsv_msg(el, "FA")) { phase = 2; phase_t = now; tries++; } else { phase = 0; tries++; next_t = now + 4000; }
        } else if (phase == 2 && now - phase_t > (DWORD)klsv_search * 1000) {
            klog("server: no hosting session %d s after the message (menu [%s]): again", klsv_search, all);
            phase = 0;
        }
    }
}

#endif /* KLSERVER_C */
