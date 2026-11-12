/* klcamppick.c - [CampaignPick]: the in-menu list of luvsic's 16 Dead Men campaign levels (see klcamppick_logic.h for the design).
 * Included by klhook.c AFTER klslot.c and klcampaign.c (uses kls_win_name, KLS_*, klcmpr_do_load, klcmpr_anp_id).
 * Game thread only (called from the tick). Reads the menu window stack; when the topmost window is the wait window "KLCampGo<NN>" it
 * starts the level via klcmpr_do_load(id, 1), exactly like KLCampaign_load.txt "Mxx 1" does.
 * Needs [Campaign] Enable=1 (Routing=1 for the scene ids); without it the picker stays idle. [CampaignPick] Enable=1, Log=1.
 * The window stack is read the way klslot.c's kls_menu_watch reads it (PROVEN there: count at +0x328, pointers from +0x330, the last is the top).
 * GUESS (not run in the game): an OpenWindow button to a near-empty window keeps it on top for >= 1 tick (50 ms poll). */
#include "klcamppick_logic.h"

static struct { int on, log; klcp_state st; DWORD t; } klcpk;

static void klcpk_init(void)
{
    memset(&klcpk, 0, sizeof klcpk);
    if (!GetPrivateProfileIntA("CampaignPick", "Enable", 0, klh_ini)) return;
    klcpk.log = GetPrivateProfileIntA("CampaignPick", "Log", 1, klh_ini) != 0;
    if (!klcmp_enabled()) { klog("campaignpick: [CampaignPick] Enable=1 but [Campaign] Enable=0: the picker stays idle"); return; }
    klcpk.on = 1;
    klog("campaignpick: on (%d levels; a list button opens window KLCampGo<NN>, the level starts like KLCampaign_load.txt)", KLCP_N);
}

static void klcpk_tick(int game_thread)
{
    DWORD gd, mgr, w, n, win[24], now; char nm[64]; const char *id;
    if (!klcpk.on || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    if (now - klcpk.t < 50) return;
    klcpk.t = now;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !(mgr = klh_rd32(gd + 0x824)) || klh_rd32(mgr) != KLS_MENUMGR_VT || !(w = klh_rd32(mgr + 4)) ||
        klh_rd32(w) != KLS_WSYS_VT) { klcpk.st.armed = 0; return; }
    n = klh_rd32(w + 0x328);
    if (!n || n > 24 || !klh_rd(w + 0x330, win, 4 * n)) { klcpk.st.armed = 0; return; }
    kls_win_name(win[n - 1], nm, sizeof nm);                                  /* the topmost window */
    if (!(id = klcp_step(&klcpk.st, nm))) return;
    if (!(klcmpr_anp_id(id) || klcmpr_stock_id(id))) { klog("campaignpick: %s: no Scenes\\Locations\\%s\\%s_Main.zip, nothing started", id, id, id); return; }
    if (klcpk.log) klog("campaignpick: window %s -> level %s", nm, id);
    klcmpr_do_load(id, 1);
}
