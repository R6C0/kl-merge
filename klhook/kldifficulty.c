/* kldifficulty.c - [Difficulty] Enable=1: two keys step the damage balance in game, no ini editing (2026-11-10, owner: "make sure theres the difficulty slider for the
 * ai heisters n how much damage they take n etc", "they just absorb bullets and same as you"). NOT RUN IN THE GAME.
 *   KeyAI  (default Ctrl+Home)      steps AI HEISTERS  STOCK / TOUGH / FAIR / FRAGILE   (police -> heister and heister -> police)
 *   KeyYou (default Ctrl+PageDown)  steps YOUR DAMAGE  STOCK / EASY / NORMAL / HARD / BRUTAL  (police -> you, heister -> you)
 * Shift with the key = the previous step. The step is announced on the FA announcement line, written into klbalance.c's record (klr.f[]: klr_tick rewrites the game's
 * per-level table within ~50 ms while a round of a NON-STOCK map runs in Arcade, so the change is live at once there, GUESS for mid-round: the log line 'balance: ... now on
 * level' is the proof; at the latest the next round) and kept in KLHook.ini: [Balance] CopToCrew / CrewToCop / CopToYou / CrewToYou plus [Difficulty] Ai= / You=.
 * Stock Dog Days maps keep the game's own table (klbalance.c never writes there), online [Balance] is off ([BalOnline]): the keys then only change the ini for the next Arcade round.
 * The step table and its numbers: kldifficulty_logic.h. Not in the menu: the menu manager's table has no room (kset_tick / [Menu] TableLog; static 4938 / 5129 of 5000).
 * [Difficulty] Enable=0 (default; (recommended on)), Ai=, You= (steps read at start, win over the [Balance] numbers), KeyAI, KeyYou, Log=1.
 * Game thread only; reads and writes klr.f[] (floats, one writer per tick). Needs [Balance] Enable=1 for the live part. */
#include "kldifficulty_logic.h"
#ifdef KLHOOK_TEST
static int kla_key_held(int dik);                                   /* klauto.c (TEST only): a scripted key counts as held */
#endif
static struct { int on, log, ai, you, vkAI, vkYou, ctlAI, ctlYou; char pend[96]; DWORD pendAt, keyAt; int dAI, dYou; } kdf;

static void kdf_ini_num(const char *key, float v)
{
    char n[16]; kdf_num(n, sizeof n, v); WritePrivateProfileStringA("Balance", key, n, klh_ini);
}
static void kdf_save(void)
{
    char n[16];
    if (kdf.ai >= 0)  { kdf_ini_num("CopToCrew", kdf_ai[kdf.ai].taken); kdf_ini_num("CrewToCop", kdf_ai[kdf.ai].dealt); snprintf(n, sizeof n, "%d", kdf.ai); WritePrivateProfileStringA("Difficulty", "Ai", n, klh_ini); }
    if (kdf.you >= 0) { kdf_ini_num("CopToYou", kdf_you[kdf.you].cop); kdf_ini_num("CrewToYou", kdf_you[kdf.you].crew); snprintf(n, sizeof n, "%d", kdf.you); WritePrivateProfileStringA("Difficulty", "You", n, klh_ini); }
}
static void kdf_set(int which, int step)
{
    char t[96];
    if (which == 0) { kdf.ai = step; kdf_apply(klr.f, step, -1); kdf_say_ai(step, t, sizeof t); }
    else            { kdf.you = step; kdf_apply(klr.f, -1, step); kdf_say_you(step, t, sizeof t); }
    if (klr.on) klr.any = 1;                                  /* the dial now has something to write (klr_tick returns early without it) */
    kdf_save();
    klog("difficulty: %s (klr.f now %.2f %.2f %.2f %.2f %.2f %.2f; [Balance] keys + [Difficulty] %s written; %s)", t, klr.f[0], klr.f[1], klr.f[2], klr.f[3], klr.f[4], klr.f[5], which ? "You" : "Ai",
         klr.on ? "klbalance.c rewrites the game's table within ~50 ms on a non-stock Arcade level" : "[Balance] Enable=0: ini only, from the next start");
    snprintf(kdf.pend, sizeof kdf.pend, "%s", t); kdf.pendAt = GetTickCount() | 1;
}

static void kdf_init(void)
{
    char k[32]; int vk, ctl, a, y;
    kdf.on = GetPrivateProfileIntA("Difficulty", "Enable", 0, klh_ini) != 0;
    kdf.log = GetPrivateProfileIntA("Difficulty", "Log", 1, klh_ini) != 0;
    kdf.vkAI = 0x24; kdf.ctlAI = 1; kdf.vkYou = 0x22; kdf.ctlYou = 1;                       /* Ctrl+Home, Ctrl+PageDown */
    if (klkeys_ini_key("Difficulty", "KeyAI", &vk, &ctl)) { kdf.vkAI = vk; kdf.ctlAI = ctl; }
    if (klkeys_ini_key("Difficulty", "KeyYou", &vk, &ctl)) { kdf.vkYou = vk; kdf.ctlYou = ctl; }
    kdf.ai = kdf.you = -1;
    if (!kdf.on) return;
    a = kdf_read_step((int)GetPrivateProfileIntA("Difficulty", "Ai", -1, klh_ini), KDF_AI_N);
    y = kdf_read_step((int)GetPrivateProfileIntA("Difficulty", "You", -1, klh_ini), KDF_YOU_N);
    if (a == -2) klog("difficulty: Ai= is IGNORED: 0 .. %d wanted (the [Balance] numbers stand)", KDF_AI_N - 1);
    if (y == -2) klog("difficulty: You= is IGNORED: 0 .. %d wanted (the [Balance] numbers stand)", KDF_YOU_N - 1);
    if (klr.on) {
        if (a >= 0 || y >= 0) { kdf_apply(klr.f, a, y); klr.any = 1; }
        kdf.ai = a >= 0 ? a : kdf_ai_of(klr.f[0], klr.f[1]);
        kdf.you = y >= 0 ? y : kdf_you_of(klr.f[2], klr.f[4]);
    } else { kdf.ai = a; kdf.you = y; }
    snprintf(k, sizeof k, "%s", "custom");
    klog("difficulty: on; AI HEISTERS %s (taken x%.2f, dealt x%.2f), YOUR DAMAGE %s (police x%.2f, crew x%.2f); keys %#x%s / %#x%s (Shift = previous); the balance dial %s",
         kdf.ai >= 0 ? kdf_ai[kdf.ai].name : k, klr.f[0], klr.f[1], kdf.you >= 0 ? kdf_you[kdf.you].name : k, klr.f[2], klr.f[4], kdf.vkAI, kdf.ctlAI ? "+Ctrl" : "", kdf.vkYou, kdf.ctlYou ? "+Ctrl" : "",
         klr.on ? "is on" : "is OFF ([Balance] Enable=0): the keys write the ini only");
}

static void kdf_tick(int game_thread)
{
    DWORD now = GetTickCount();
    if (!kdf.on || !game_thread || !klh_exe_ok) return;
    if (kdf.pendAt) {                                                                       /* the announcement waits for the element, up to 5 s */
        if (now - kdf.pendAt > 5000 || klan_show(kdf.pend, 3.0f, 0)) kdf.pendAt = 0;
    }
    if (now - kdf.keyAt < 30) return;
    kdf.keyAt = now;
    {
        static SHORT (WINAPI *gaks)(int); static HWND (WINAPI *fgw)(void); static DWORD (WINAPI *wtp)(HWND, LPDWORD); static int looked;
        if (!looked) {
            HMODULE u = GetModuleHandleA("user32.dll"); looked = 1;
            if (u) { gaks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
        }
        if (gaks && fgw && wtp) {
            DWORD pid = 0; HWND f = fgw(); int ctl = (gaks(0x11) & 0x8000) != 0, sh = (gaks(0x10) & 0x8000) != 0, ka = (gaks(kdf.vkAI) & 0x8000) != 0, ky = (gaks(kdf.vkYou) & 0x8000) != 0, scripted = 0, a, y;
#ifdef KLHOOK_TEST
            {   /* bench: keys klauto.c's script holds count too (as klhostopt.c) */
                static UINT (WINAPI *mvk)(UINT, UINT); static int lk;
                if (!lk) { HMODULE u = GetModuleHandleA("user32.dll"); lk = 1; if (u) mvk = (UINT (WINAPI *)(UINT, UINT))GetProcAddress(u, "MapVirtualKeyA"); }
                if (mvk) {
                    if (kla_key_held(0x1d)) ctl = scripted = 1;
                    if (kla_key_held((int)mvk((UINT)kdf.vkAI, 0))) ka = scripted = 1;
                    if (kla_key_held((int)mvk((UINT)kdf.vkYou, 0))) ky = scripted = 1;
                }
            }
#endif
            a = ka && (!kdf.ctlAI || ctl); y = ky && (!kdf.ctlYou || ctl);
            if (f) wtp(f, &pid);
            if (scripted || pid == GetCurrentProcessId()) {
                if (a && !kdf.dAI) kdf_set(0, kdf_next(kdf.ai, KDF_AI_N, sh ? -1 : 1));
                if (y && !kdf.dYou) kdf_set(1, kdf_next(kdf.you, KDF_YOU_N, sh ? -1 : 1));
            }
            kdf.dAI = a; kdf.dYou = y;
        }
    }
}
