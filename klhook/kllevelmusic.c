/* kllevelmusic.c - [LevelMusic] Restart=1: the level music of a converted Dead Men FA map comes back in round 2+ (owner 2026-11-09:
 * "music not coming in for the round after"). CAUSE (exe disassembly, re/open_work_log.md): the music is settings field 157; the settings
 * Init (0x88d780 -> 0x8736d0) stores it at [[0x168e958]+0x944] and 0x8ce720 plays it ONCE; later rounds reuse the loaded level and nothing
 * calls it again (only Backstab, 0x67f0a9, plays field 158). Affects DM01 DM02 DM03 DM06 (field 157 non-zero); PlayMusic-node maps are
 * re-armed by their round-start triggers; DM05A / DD01-DD09 have no level music.
 * FIX: ~Delay ms after a new round (not the first on the map) call the game's own thiscall 0x8ce720(mgr, [mgr+0x944]); it stops the old
 * instance itself (0x7d9560) and stores the new handle at [mgr+0x950]. GUESS: the Init-time call context is still valid in round 2.
 * [LevelMusic] Restart=0 ((recommended on) once benched), Delay=2000, Log=1. Game thread only, Arcade and (Online=1) network rounds. */
#include "kllevelmusic_logic.h"
static struct { int on, online, log; DWORD delay, t_last; char map[40]; struct kllm_st st; } kllm;

static void kllm_init(void)
{
    kllm.on = GetPrivateProfileIntA("LevelMusic", "Restart", 0, klh_ini) != 0;
    kllm.online = GetPrivateProfileIntA("LevelMusic", "Online", 0, klh_ini) != 0;
    kllm.delay = (DWORD)GetPrivateProfileIntA("LevelMusic", "Delay", 2000, klh_ini);
    kllm.log = GetPrivateProfileIntA("LevelMusic", "Log", 1, klh_ini) != 0;
    if (kllm.on) klog("levelmusic: Restart=1 (delay %lu ms, online %d)", (unsigned long)kllm.delay, kllm.online);
}

static void kllm_tick(int game_thread)
{
    DWORD now = GetTickCount(), mgr, snd, inst0, inst1; struct klb_snap s; char key[40];
    if (!kllm.on || !game_thread || !klh_exe_ok || now - kllm.t_last < 250) return;
    kllm.t_last = now;
    if (kl_online() && !kllm.online) return;
    klmu_mapkey(key, sizeof key);
    if (strcmp(key, kllm.map)) { snprintf(kllm.map, sizeof kllm.map, "%s", key); memset(&kllm.st, 0, sizeof kllm.st); }
    if (!kllm.map[0] || !klon_read(&s, kllm.online)) return;
    if (!kllm_step(&kllm.st, s.state == KLB_ROUND, s.rules, now, kllm.delay)) return;
    mgr = klh_rd32((DWORD_PTR)KLH_VA(0x0168e958)); snd = mgr ? klh_rd32(mgr + 0x944) : 0; inst0 = mgr ? klh_rd32(mgr + 0x950) : 0;
    if (!mgr || !snd || !klh_rd32((DWORD_PTR)KLH_VA(0x00dd2640)) ) { if (kllm.log) klog("levelmusic: round %d on %s: no level music (mgr %08lx snd %08lx)", kllm.st.rounds, kllm.map, (unsigned long)mgr, (unsigned long)snd); return; }
    { typedef void (__fastcall *play_t)(void *thisp, void *edx, DWORD snd);      /* 0x8ce720: thiscall, one stack arg, ret 4 */
      KLFC_CALL(play_t, 0x8ce720)((void *)mgr, 0, snd); }
    inst1 = klh_rd32(mgr + 0x950);
    if (kllm.log) klog("levelmusic: round %d on %s: restarted sound %08lx (handle %08lx -> %08lx)", kllm.st.rounds, kllm.map, (unsigned long)snd, (unsigned long)inst0, (unsigned long)inst1);
}
