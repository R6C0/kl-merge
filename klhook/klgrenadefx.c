/*
 * klgrenadefx.c - [Grenade] PinSound / ThrowAnim for the Release mode (2026-11-10, owner: "i done the grenade in dm01 and its just a red
 * light no throw just explosion at the end wheres the throw n stuff and showing the grenade thrown with a pin sound or just something").
 * Part of KLHook, included by klhook.c AFTER kladren.c (it uses kladren.c's player-clip machinery) and klgrenade.c (which calls
 * klgx_press / klgx_launched / klgx_own_act through forward declarations). NOTHING HERE HAS RUN IN THE GAME.
 *
 * WHY: [Grenade] Release (luvsic's direct release) only calls the item's TryFire. Nothing plays a clip (the ZFFActionThrow chain,
 * action 0x11 / [P+0xa1c], is dead in Dog Days) and nothing plays a sound; the projectile is DD's Rocket_Flare node (red flare emitters,
 * no model: tools/kl_grenade.py 'the grenade has no model of its own').
 *
 * PinSound=1   at the G press the pin-pull cue plays (WAV below KLGrenade\), at the release the throw cue. winmm PlaySoundA, async, from the
 *              game thread (loaded by name, no import added). Files absent = silent, one log line.
 * ThrowAnim=1  at the G press the LOCAL player plays a throw clip: kladren.c's proven playback (a real ZFFActionVaultOver with a vtable copy
 *              of ours: Start/Update/End), clip slot /Weapon_Handling/Throw_Grenade/<Stand_Overhand;..> (first one his set has), turned
 *              to the aim point, in place. The release is then delayed by ThrowDelayMs (klgrenade.c's pending release) so the grenade leaves
 *              the hand while the clip plays. ThrowAnimMs caps how long the clip may hold him.
 * With either on, the release waits ThrowDelayMs after the press; both off: as before (at once).
 * NOT DONE: a model on the grenade in flight. No hook-side route to a draw was found (the projectile pool entry is a clone of a model-less
 * template; the HUD overlay has no world projection we could reuse safely). Needs the level data: a model child on the Rocket_Flare
 * template (tools/kl_grenade.py), see re/grenadefx_1110.md.
 *
 * KLHook.ini [Grenade] (read when Release=1)
 *   PinSound=0  PinFile=grenade_pin.wav  ThrowFile=grenade_throw.wav  SoundDir=<ini folder>\KLGrenade
 *   ThrowAnim=0  ThrowSlots=Stand_Overhand;Stand_Underhand;UB_Underhand  ThrowDelayMs=350  ThrowAnimMs=1200
 * Log lines: 'grenadefx: ...'.
 */
#ifndef KLGRENADEFX_C
#define KLGRENADEFX_C
#include "klgrenadefx_logic.h"

static struct {
    int pin, anim, delay, cap, logn, sndN, animN;
    char dir[MAX_PATH], pinf[MAX_PATH], thrf[MAX_PATH], slots[160];
    BOOL (WINAPI *ps)(LPCSTR, HMODULE, DWORD); int psTried, havePin, haveThr;
#ifndef KAD_TEST_NOANIM
    int ovOn; char sv[sizeof kad_ao];                         /* kad_ao as the Adrenaline anim left it, restored when our clip ended */
#endif
} klgx;

static void klgx_play(const char *path, int have, const char *what)
{
    if (!klgx.pin) return;
    if (!have) { if (klgx.sndN++ < 3) klog("grenadefx: %s sound: file missing (%s): silent (run tools\\kl_grenadefx_1110.py)", what, path); return; }
    if (!klgx.ps && !klgx.psTried) {
        HMODULE w = GetModuleHandleA("winmm.dll"); if (!w) w = LoadLibraryA("winmm.dll");
        klgx.psTried = 1; if (w) klgx.ps = (BOOL (WINAPI *)(LPCSTR, HMODULE, DWORD))GetProcAddress(w, "PlaySoundA");
        if (!klgx.ps) klog("grenadefx: winmm PlaySoundA not found: no sounds");
    }
    if (klgx.ps) { klgx.ps(path, 0, 0x20003u /* SND_ASYNC | SND_FILENAME | SND_NODEFAULT */); if (klgx.logn > 0) { klgx.logn--; klog("grenadefx: %s sound played (%s)", what, path); } }
}

#ifndef KAD_TEST_NOANIM
/* start the clip; 1 = the action is running. Any slot / clip refusal tries the next candidate, a precondition refusal stops. */
static int klgx_anim(DWORD P, const float to[3], const char **why)
{
    struct kad_an_go g; float M[9], Pf[3], dx, dz, l; char cand[64], slot[128]; int i, r = 0;
    *why = 0;
    if (kad_an.dead) { *why = "adrenaline anim disabled after a fault"; return 0; }
    if (kad_an.active || klgx.ovOn) { *why = "a clip is already running"; return 0; }
    if (!klfc_pose(P, M, Pf)) { *why = "his pose cannot be read"; return 0; }
    dx = Pf[0] - to[0]; dz = Pf[2] - to[2]; l = (float)sqrt(dx * dx + dz * dz);
    memcpy(klgx.sv, &kad_ao, sizeof kad_ao);
    kad_ao.face = 1; kad_ao.alignf = 6; kad_ao.inject = 0; kad_ao.log = 1; kad_ao.userslot = 1; kad_ao.dist = l;        /* dist = his own distance: AlignTo turns him, he stays */
    for (i = 0; klgx_nth(klgx.slots, i, cand, sizeof cand); i++) {
        if (!klgx_slot_path(cand, slot, sizeof slot)) continue;
        strcpy(kad_ao.slot, slot);
        memset(&g, 0, sizeof g); g.P = P; g.rec = -1; memcpy(g.to, to, 12);
        r = kad_an_guard("go", kad_an_go_body, &g);
        if (r < 0) { kad_an_disable("go"); *why = "fault"; r = 0; break; }
        if (r == 1) break;
        *why = g.why ? g.why : "refused";
        if (!g.why || (!strstr(g.why, "slot") && !strstr(g.why, "clip"))) break;          /* a precondition (moving, action running ...): the next clip would fail alike */
    }
    if (r == 1) { klgx.ovOn = 1; kad_gx_cap = klgx.cap; *why = 0; }
    else memcpy(&kad_ao, klgx.sv, sizeof kad_ao);
    return r == 1;
}
/* every tick: give kad_ao back once our clip is over */
static void klgx_poll(void)
{
    if (klgx.ovOn && !kad_an.active) { memcpy(&kad_ao, klgx.sv, sizeof kad_ao); klgx.ovOn = 0; kad_gx_cap = 0; }
}
static int klgx_own_act(DWORD act) { return klgx.ovOn && kad_an.active && kad_an.act == act; }
#else
static int klgx_anim(DWORD P, const float to[3], const char **why) { (void)P; (void)to; *why = "built without the clip machinery"; return 0; }
static void klgx_poll(void) {}
static int klgx_own_act(DWORD act) { (void)act; return 0; }
#endif

/* klgrenade.c: the G press passed every check and a grenade is in hand. Returns the tick the release is due at (0 = release now). */
static DWORD klgx_press(DWORD P, DWORD now)
{
    float aim[3]; int animOk = 0; const char *why = 0;
    if (!klgx.pin && !klgx.anim) return 0;
    klgx_play(klgx.pinf, klgx.havePin, "pin");
    if (klgx.anim && klh_rd(P + 0x27b0, aim, 12)) {
        animOk = klgx_anim(P, aim, &why);
        if (!animOk && klgx.animN++ < 5) klog("grenadefx: throw clip not started: %s (the grenade is thrown without it)", why ? why : "?");
    }
    return klgx_due(now, klgx.delay, klgx.pin, animOk);
}
/* klgrenade.c: the shot launched */
static void klgx_launched(void) { klgx_play(klgx.thrf, klgx.haveThr, "throw"); }

static void klgx_init(void)
{
    char buf[MAX_PATH];
    memset(&klgx, 0, sizeof klgx);
    klgx.pin = GetPrivateProfileIntA("Grenade", "PinSound", 0, klh_ini) != 0;
    klgx.anim = GetPrivateProfileIntA("Grenade", "ThrowAnim", 0, klh_ini) != 0;
    klgx.delay = klgx_delay_clamp((int)GetPrivateProfileIntA("Grenade", "ThrowDelayMs", 350, klh_ini));
    klgx.cap = klgx_cap_clamp((int)GetPrivateProfileIntA("Grenade", "ThrowAnimMs", 1200, klh_ini));
    klgx.logn = 6;
    GetPrivateProfileStringA("Grenade", "ThrowSlots", KLGX_SLOTS_DEF, klgx.slots, sizeof klgx.slots, klh_ini);
    if (!klgx.pin && !klgx.anim) return;
    GetPrivateProfileStringA("Grenade", "SoundDir", "", buf, sizeof buf, klh_ini);
    if (buf[0]) { size_t n = strlen(buf); strcpy(klgx.dir, buf); if (klgx.dir[n - 1] != 0x5c && n + 2 < sizeof klgx.dir) strcat(klgx.dir, "\\"); }
    else if (!klgx_dir_of(klh_ini, "KLGrenade", klgx.dir, sizeof klgx.dir)) klgx.dir[0] = 0;
    GetPrivateProfileStringA("Grenade", "PinFile", "grenade_pin.wav", buf, sizeof buf, klh_ini);
    _snprintf(klgx.pinf, sizeof klgx.pinf, "%s%s", klgx.dir, buf); klgx.pinf[sizeof klgx.pinf - 1] = 0;
    GetPrivateProfileStringA("Grenade", "ThrowFile", "grenade_throw.wav", buf, sizeof buf, klh_ini);
    _snprintf(klgx.thrf, sizeof klgx.thrf, "%s%s", klgx.dir, buf); klgx.thrf[sizeof klgx.thrf - 1] = 0;
    klgx.havePin = GetFileAttributesA(klgx.pinf) != INVALID_FILE_ATTRIBUTES; klgx.haveThr = GetFileAttributesA(klgx.thrf) != INVALID_FILE_ATTRIBUTES;
    klog("grenadefx: ON (NOT benched): PinSound=%d (pin %s, throw %s) ThrowAnim=%d slots '%s' delay %d ms cap %d ms; no model on the flight (needs level data)",
         klgx.pin, klgx.havePin ? "found" : "MISSING", klgx.haveThr ? "found" : "MISSING", klgx.anim, klgx.slots, klgx.delay, klgx.cap);
}
#endif /* KLGRENADEFX_C */
