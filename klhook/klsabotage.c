/*
 * klsabotage.c - [Sabotage] VanHold: THE UNDERCOVER COP HOLDS THE ESCAPE VAN (2026-10-26; owner: sabotage like Among Us, "hold the escape
 * van N seconds", nobody can tell who did it). Part of KLHook (included by klhook.c after klcopsquad.c). Default OFF.
 * NOTHING HERE HAS RUN IN THE GAME. Research, the other two sabotages and the per-map tables: re/ucc_sabotage.md.
 *
 * What it does: on the HOST, in an Undercover Cop round (game type 4, sub-mode [0x168e59c] == 1), when the LOCAL player is the UCC
 * (his ZFFPlayer byte +0x2729 == 1 and police byte +0x2723 == 0, GUESS: the UCC pick in the Sv rules' slot 4 0x40f870 writes +0x2729 = 1
 * through 0x4622b0 on [record+0x378], read as the ZFFPlayer) and he presses Key while the escape vehicle is under way or waiting
 * (state [rules+0x1dc] 1..4), the state timer [rules+0x1d8] gets HoldS more seconds, once per vehicle visit, never above 40 s.
 * In states 1/2 the van arrives later; in 3/4 it waits longer at the stop (the crew aboard sits under fire longer). That is exactly the
 * write stock 'hold the driver' (slot 152 0x8b3930: [rules+0x1d8] += 5.0) and klescort.c FollowOut / klbotfill.c OnlineVanHold make:
 * ONE data write, no game call, no announcement (stock slot 152 announces; this does not, so nothing names the UCC).
 * Facts (re/van_hold_online.md, re/bots_follow_out.md 1.6): slot 195 0x55ec70 counts the timer down and moves 1/2 -> 3 and 3/4 -> 5 at 0;
 * slot 192 0x5dff40 does not end the round while the vehicle state is 1..6, so a hold cannot lose the round by the clock.
 * GUESS (needs the live bench): the clients follow because the state machine is the host's and the escape dataset (DDL_SEscapeState
 * m_iEscapeSeqState / m_fEscapeSeqTimer) is replicated; their HUD seconds come from [score+0x58] (slot 191). Not proven online.
 * LIMIT: only a UCC who HOSTS can use it. A client UCC's key never reaches the host (no hook-to-hook request channel yet;
 * re/ucc_sabotage.md 4 has the lobby-member-data plan).
 *
 * KLHook.ini
 *   [Sabotage]
 *   VanHold=0       1 = on (host, Undercover Cop rounds only)
 *   Key=0x4a        virtual-key code of the sabotage key (J), game window in front (GetAsyncKeyState, not consumed)
 *   HoldS=8         seconds added per press, 1..20
 *   AnyMode=0       TEST: also in plain FA and C&R rounds
 *   AnyPlayer=0     TEST: the host may press without being the UCC
 *   Log=1
 */
#ifndef KLSABOTAGE_C
#define KLSABOTAGE_C
#include "klsabotage_logic.h"

#define KLSAB_SUBMODE    0x0168e59cu
#define KLSAB_GAMESTATE  0x0168e9e4u          /* [[this]+0x54] = the FA rules when [sm+0x5c] == 4 (0x7bb2a0, klbotfill.c) */
#define KLSAB_PLAYER_VT  0x00bb45f4u          /* ZFFPlayer (klcopsquad.c) */

static struct {
    int on, key, holdS, anyMode, anyPlayer, log, inwin, used, prevState, toldWho, presses, holds;
    struct klsab_key k;
    SHORT (WINAPI *aks)(int); HWND (WINAPI *fgw)(void); DWORD (WINAPI *wtp)(HWND, LPDWORD);
} klsab;

static void klsab_init(void)
{
    HMODULE u;
    klsab.on = GetPrivateProfileIntA("Sabotage", "VanHold", 0, klh_ini) != 0;
    klsab.key = GetPrivateProfileIntA("Sabotage", "Key", 0x4a, klh_ini);
    klsab.holdS = klsab_clamp_hold(GetPrivateProfileIntA("Sabotage", "HoldS", 8, klh_ini));
    klsab.anyMode = GetPrivateProfileIntA("Sabotage", "AnyMode", 0, klh_ini) != 0;
    klsab.anyPlayer = GetPrivateProfileIntA("Sabotage", "AnyPlayer", 0, klh_ini) != 0;
    klsab.log = GetPrivateProfileIntA("Sabotage", "Log", 1, klh_ini);
    if (!klsab.on) return;
    if ((u = GetModuleHandleA("user32.dll")) != 0) { klsab.aks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); klsab.fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); klsab.wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
    klog("sabotage: VanHold ON (NOT yet run live): key %#x, +%d s once per van visit, host + UCC only%s%s%s", klsab.key, klsab.holdS,
         klsab.anyMode ? ", TEST AnyMode" : "", klsab.anyPlayer ? ", TEST AnyPlayer" : "", klsab.aks ? "" : " (no GetAsyncKeyState: key off)");
}

static int klsab_keydown(void)
{
    HWND fg; DWORD pid = 0;
    if (!klsab.key || !klsab.aks || !klsab.fgw || !klsab.wtp || !(fg = klsab.fgw())) return 0;
    klsab.wtp(fg, &pid);
    return pid == GetCurrentProcessId() && (klsab.aks(klsab.key) & 0x8000) != 0;
}

/* the local player's ZFFPlayer (gd+0x828+4*[gd+0x898], klcopsquad.c klcq_local / klescort.c kle_human): ucc / police bytes, 0 = unreadable */
static int klsab_local(int *ucc, int *police)
{
    DWORD gd, pl; BYTE sel = 0xff, a = 0, b = 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel > 3 || !(pl = klh_rd32(gd + 0x828 + 4 * sel))) return 0;
    if (klh_rd32(pl) != KLSAB_PLAYER_VT || !klh_rd(pl + 0x2729, &a, 1) || !klh_rd(pl + 0x2723, &b, 1)) return 0;
    *ucc = a; *police = b;
    return 1;
}

static void klsab_tick(int game_thread)
{
    DWORD now = GetTickCount(), sm, role = 0, mode = 0, state = 0, sub = 0, gs, rules; BYTE v = 0; float tm = 0, want; int vstate, ucc = 0, police = 0;
    if (!klsab.on || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLNET_SESSION))) || !KLH_SM_VT_OK(klh_rd32(sm)) || !klh_rd(sm + 0x54, &role, 4) || !klh_rd(sm + 0x5c, &mode, 4) || !klh_rd(sm + 0x70, &state, 4)
        || !klh_rd((DWORD_PTR)KLH_VA(KLSAB_SUBMODE), &sub, 4) || !klsab_gate(role, mode, state, sub, klsab.anyMode)) { klsab.inwin = 0; return; }
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLSAB_GAMESTATE))) || !(rules = klh_rd32(gs + 0x54)) || !KLH_RULES_SV_OK(klh_rd32(rules)) || !klh_rd(rules + 0x1dc, &v, 1)) return;
    vstate = v;
    if (!klsab.inwin) { klsab.inwin = 1; klsab.used = 0; klsab.prevState = vstate; memset(&klsab.k, 0, sizeof klsab.k); if (klsab.log) klog("sabotage: round on the host (sub-mode %lu, state 0x%lx): VanHold armed", (unsigned long)sub, (unsigned long)state); }
    if (klsab_new_visit(klsab.prevState, vstate)) klsab.used = 0;
    klsab.prevState = vstate;
    if (!klsab_edge(&klsab.k, klsab_keydown(), now)) return;
    klsab.presses++;
    if (!klsab_local(&ucc, &police) && !klsab.anyPlayer) { if (klsab.log) klog("sabotage: key: the local player could not be read: nothing done"); return; }
    if (!klsab_may_press(ucc, police, klsab.anyPlayer)) { if (klsab.log >= 2 || !klsab.toldWho++) klog("sabotage: key: the local player is not the hidden UCC (+0x2729 %d, police %d): nothing done", ucc, police); return; }
    if (!klh_rd(rules + 0x1d8, &tm, 4)) return;
    want = klsab_hold(vstate, tm, klsab.used, klsab.holdS);
    if (want < 0) { if (klsab.log) klog("sabotage: key: van state %d, timer %.1f s, %s: nothing done", vstate, tm, klsab.used ? "already held this visit" : "not under way / waiting, or at the cap"); return; }
    if (!klh_data((void *)(DWORD_PTR)(rules + 0x1d8), &want, 4, "rules: escape vehicle state timer ([Sabotage] VanHold)")) { klog("sabotage: [rules+0x1d8] could NOT be written"); return; }
    klsab.used = 1; klsab.holds++;
    if (klsab.log) klog("sabotage: VAN HELD: state %d, timer [rules+0x1d8] %.1f -> %.1f s (press %d, hold %d this session)", vstate, tm, want, klsab.presses, klsab.holds);
}
#endif /* KLSABOTAGE_C */
