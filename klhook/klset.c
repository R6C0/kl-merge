/*
 * klset.c - THE 'MOD SETTINGS' ROWS OF THE MENU (2026-10-14, the owner: 'i want it to be an option within the game's settings like
 * when u click options'). Part of KLHook (included by klhook.c BEFORE klchar.c, whose private option-interface vtable answers these
 * names as it answers KLChar / KLGunStart: klc_get / klc_set / klc_enabled ask kset_which first).
 *
 * The rows are ToggleText widgets of the window mkoverlay.py writes (KLGuns, now headed 'Mod settings', reached from the Options
 * menu and from the Arcade page); a row's value is an option name kl2.exe does not know, answered here. The value lives in this
 * DLL and in KLHook.ini, so a change in the menu is kept for the next start:
 *   KLSLook    0 Off / 1 KL look / 2 LiveLeak look   -> [Graphics] Look       (ReShade is loaded at start: takes effect at the next start)
 *   KLSTex     0 off / 1 on                           -> [Graphics] Textures   (anisotropic x16: next start)
 *   KLSPrompt  0 off / 1 on                           -> [Adrenaline] Prompt   (the centre messages: at once, kladren.c reads kset_v[2])
 *   KLSUseE    0 off / 1 on                           -> [Adrenaline] NeedUse  (hold E by a downed crewmate: at once, kset_v[3])
 * 2026-10-15 (the ReShade bridge, klreshade.c; the four new rows are LIVE only with [ReShade] Bridge=1 and ReShade loaded - then Look
 * is live too; klreshade.c klrs_setting says per row what a change does now):
 *   KLSCam     0 off / 1 subtle / 2 raw               -> [Graphics] CameraFX   (uniform KL_CamFX, [ReShade] TechCamFX)
 *   KLSGlare   0 off / 1 on                           -> [Graphics] Glare      (uniform KL_Glare, [ReShade] TechGlare)
 *   KLSAA      0 off / 1 SMAA / 2 FXAA                -> [Graphics] AA         (techniques SMAA@SMAA.fx / KL_FXAA@KL_FXAA.fx)
 *   KLSNeural  0 off / 1 on                           -> [Graphics] Neural     (the Uplift add-on: klhook.c at start, next start)
 * The new rows are APPENDED (index 4..7): kladren.c reads kset_v[2] / [3] by number. Look's default is 1 as klhook.c's (it loads
 * ReShade with the KL look when the key is absent; the row said Off until 2026-10-15).
 * The entry counts of the XML rows ARE these ranges (re\wardrobe.md 5a): mkoverlay.py SET_ROWS must agree with kset_upper.
 */
#ifndef KLSET_C
#define KLSET_C

#define KLS_N 8
static const char *const kset_names[KLS_N] = { "KLSLook", "KLSTex", "KLSPrompt", "KLSUseE", "KLSCam", "KLSGlare", "KLSAA", "KLSNeural" };
static const int kset_upper[KLS_N] = { 2, 1, 1, 1, 2, 1, 2, 1 };
static const char *const kset_sec[KLS_N] = { "Graphics", "Graphics", "Adrenaline", "Adrenaline", "Graphics", "Graphics", "Graphics", "Graphics" };
static const char *const kset_key[KLS_N] = { "Look", "Textures", "Prompt", "NeedUse", "CameraFX", "Glare", "AA", "Neural" };
static const int kset_def[KLS_N] = { 1, 1, 1, 1, 1, 1, 1, 0 };
static volatile LONG kset_v[KLS_N] = { 1, 1, 1, 1, 1, 1, 1, 0 };
static const char *klrs_setting(int i);                  /* klreshade.c: what a change of row i does now (and it tells the bridge) */

static int kset_which(const char *name)
{   /* -> 0 .. KLS_N-1 for our names, -1 for anything else (or unreadable) */
    char n[16]; int i;
    if (!name || !klh_rd((DWORD_PTR)name, n, 3) || memcmp(n, "KLS", 3)) return -1;
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n)) return -1;
    for (i = 0; i < KLS_N; i++) if (!strcmp(n, kset_names[i])) return i;
    return -1;
}

static int kset_get(int i) { return (int)kset_v[i]; }

static void kset_put(int i, int value)
{
    char v[16];
    if (value < 0) value = 0;
    if (value > kset_upper[i]) value = kset_upper[i];
    if (InterlockedExchange(&kset_v[i], value) != value) {
        snprintf(v, sizeof v, "%d", value); WritePrivateProfileStringA(kset_sec[i], kset_key[i], v, klh_ini);
        klog("settings: menu set %s = %d ([%s] %s=%d in KLHook.ini%s)", kset_names[i], value, kset_sec[i], kset_key[i], value, klrs_setting(i));
    }
}

static void kset_init(void)
{
    int i;
    for (i = 0; i < KLS_N; i++) {
        int v = (int)GetPrivateProfileIntA(kset_sec[i], kset_key[i], kset_def[i], klh_ini);
        kset_v[i] = v < 0 ? 0 : v > kset_upper[i] ? kset_upper[i] : v;
    }
    klog("settings: the menu's Mod settings rows read Look=%ld Textures=%ld Prompt=%ld NeedUse(E)=%ld CameraFX=%ld Glare=%ld AA=%ld Neural=%ld", kset_v[0], kset_v[1], kset_v[2], kset_v[3], kset_v[4], kset_v[5], kset_v[6], kset_v[7]);
}

#endif
