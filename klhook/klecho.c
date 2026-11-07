/*
 * klecho.c - [Echo]: room reverb that follows the place (2026-11-07, owner: "make gun shots more echoy or just adaptive to the
 * environment"). Part of KLHook (included by klhook.c after klambience.c, SHIP and TEST alike). OFF unless [Echo] Enable=1.
 *
 * WHAT: Dog Days has ONE global OpenAL EFX reverb slot. ZSynthOpenAL::SetReverb (0x5fff30) pushes the current room's roomeffect into it
 * with 12 alEffectf calls through the function pointer at 0x14f356c (a .data global, filled at init by alGetProcAddress("alEffectf")
 * at 0x521416). This file swaps that DATA pointer for a wrapper that lengthens the decay and lifts the reflections / late tail per
 * kind of room (indoor / street / roof / hall, klecho_logic.h) and calls the real function. Nothing else changes: no code byte is
 * written (a SHIP build may write data), nothing in the game's files. Every sound with an aux send follows (guns, footsteps, voices,
 * explosions); that is the "adaptive" part. Works the same on the 9 stock FA maps, the Dead Men maps (once they carry reverb boxes,
 * re/gun_echo_1107.md) and online (the same exe plays an online round).
 *
 * GUESS / NOT VERIFIED IN THE GAME (2026-11-07, offline, nothing was launched): whether a gun voice carries the aux send. The voice
 * creation sites pass the slot with the default send gain (static reading) but no run has listened. [Echo] Log=1 writes one line per
 * distinct room effect ("echo: roof decay 1.49->2.38 refl 0.052->0.104 late ...") so one owner-present run can show the rooms.
 *
 * KLHook.ini
 *   [Echo]
 *   ; Room reverb follows the place: longer decay + stronger tail per room kind (recommended on once the owner has listened)
 *   Enable=0
 *   ; global strength in percent, 100 = the curve in klecho_logic.h, 0 = the engine's own values, up to 300
 *   Strength=100
 *   ; per kind percent of that curve (indoor = small tight rooms, street = between buildings, roof = open area, hall = big covered)
 *   IndoorPct=100  StreetPct=100  RoofPct=100  HallPct=100
 *   Log=1
 */
#ifndef KLECHO_C
#define KLECHO_C

#include "klecho_logic.h"

#define KLECHO_SLOT 0x14f356cu                               /* alEffectf pointer (kl2.exe .data) */

static struct klecho_cfg klecho_c = { 100, { 100, 100, 100, 100, 100 } };
static struct klecho_st klecho_s;
static int klecho_on, klecho_log = 1, klecho_logn, klecho_installed;
static LONG klecho_calls;
static float klecho_o[3], klecho_n[3];                       /* decay, reflections, late: engine value / ours (for the log line) */
static float klecho_seen[24][2]; static int klecho_nseen;    /* dedupe of the log: (kind, decay) */
typedef void (__cdecl *klecho_al_fn)(unsigned, int, float);
static klecho_al_fn klecho_real;

static void __cdecl klecho_wrap(unsigned eff, int param, float v)
{
    float nv = v;
    if (klecho_on && param >= 1 && param <= 12) {
        nv = klecho_value(&klecho_c, &klecho_s, param, v);
        if (param == 5) { klecho_o[0] = v; klecho_n[0] = nv; }
        if (param == 7) { klecho_o[1] = v; klecho_n[1] = nv; }
        if (param == 9) { klecho_o[2] = v; klecho_n[2] = nv; }
        if (param == 10 && klecho_log && klecho_logn < 60) {
            int i, dup = 0; float key = klecho_o[0] * 1000.0f + klecho_o[1];
            for (i = 0; i < klecho_nseen; i++) if (klecho_seen[i][0] == (float)klecho_s.kind && klecho_seen[i][1] == key) dup = 1;
            if (!dup && klecho_nseen < 24) {
                static const char *nm[5] = { "none", "indoor", "street", "roof", "hall" };
                klecho_seen[klecho_nseen][0] = (float)klecho_s.kind; klecho_seen[klecho_nseen][1] = key; klecho_nseen++; klecho_logn++;
                klog("echo: %s decay %.2f->%.2f refl %.3f->%.3f late %.3f->%.3f (late delay %.3f->%.3f)", nm[klecho_s.kind], klecho_o[0], klecho_n[0],
                     klecho_o[1], klecho_n[1], klecho_o[2], klecho_n[2], v, nv);
            }
        }
        InterlockedIncrement(&klecho_calls);
    }
    if (klecho_real) klecho_real(eff, param, nv);
}

static void klecho_tick(int game_thread)
{
    BYTE *slot; DWORD cur, mine = (DWORD)(DWORD_PTR)klecho_wrap;
    if (!klecho_on || !game_thread || !klh_exe_ok) return;
    slot = KLH_VA(KLECHO_SLOT);
    cur = klh_rd32((DWORD_PTR)slot);
    if (!cur || cur == mine) return;                         /* alEffectf not resolved yet, or already ours */
    klecho_real = (klecho_al_fn)(DWORD_PTR)cur;              /* (re)wrap: the engine may re-resolve it after an audio device reset */
    if (klh_data(slot, &mine, 4, "echo alEffectf")) {
        if (!klecho_installed++) klog("echo: wrapping alEffectf slot %08lx (was %08lx): strength %d, indoor/street/roof/hall %d/%d/%d/%d%%",
                                      (unsigned long)KLECHO_SLOT, (unsigned long)cur, klecho_c.strength, klecho_c.pct[KLE_INDOOR], klecho_c.pct[KLE_STREET], klecho_c.pct[KLE_ROOF], klecho_c.pct[KLE_HALL]);
    } else klecho_real = 0;
}

static void klecho_init(void)
{
    klecho_on = GetPrivateProfileIntA("Echo", "Enable", 0, klh_ini) != 0;
    if (!klecho_on) return;
    klecho_log = GetPrivateProfileIntA("Echo", "Log", 1, klh_ini) != 0;
    klecho_c.strength = GetPrivateProfileIntA("Echo", "Strength", 100, klh_ini);
    klecho_c.pct[KLE_INDOOR] = GetPrivateProfileIntA("Echo", "IndoorPct", 100, klh_ini);
    klecho_c.pct[KLE_STREET] = GetPrivateProfileIntA("Echo", "StreetPct", 100, klh_ini);
    klecho_c.pct[KLE_ROOF] = GetPrivateProfileIntA("Echo", "RoofPct", 100, klh_ini);
    klecho_c.pct[KLE_HALL] = GetPrivateProfileIntA("Echo", "HallPct", 100, klh_ini);
    if (klecho_c.strength < 0) klecho_c.strength = 0;
    if (klecho_c.strength > 300) klecho_c.strength = 300;
    klog("echo: on ([Echo] Enable=1): the engine's reverb slot is wrapped once the audio system is up");
}

#endif /* KLECHO_C */
