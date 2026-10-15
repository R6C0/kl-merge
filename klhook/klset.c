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
 * 2026-10-15 (mkoverlay.py v27, the menu with the ReShade rows): THE MENU MANAGER'S TABLE HAS NO ROOM (re\hud_menu.md 1.1: 5,096 slots,
 * budget 5000; CLAUDE.md 2026-10-12: margin about 4), so the window's rows were made to cost nothing new - among other things the two
 * adrenaline rows became ONE row, option KLSAdren (kset_which -> KLS_ADREN): value = Prompt | NeedUse << 1, entries
 *   0 'Stand by him'   1 'Stand by him + messages'   2 'Hold E'   3 'Hold E + messages'
 * read from and written into the same two keys through rows 2 and 3 (kladren.c still reads kset_v[2] / [3]). KLSPrompt / KLSUseE are
 * still answered (an older overlay's rows keep working). No Neural row in the menu (next start only; [Graphics] Neural in the ini).
 * [Menu] TableLog=1 (default 0, reads only): one line 'menu: table N of 5096 entries ...' whenever the menu manager's count has
 * changed and stood for 2 s (= after each XML load: the main menu, a level) - the LIVE count that every new menu element needs
 * (re\hud_menu.md 7 check K0 / 8, the wiring drafted there and never built; here behind a key). Game thread only, klh_rd only.
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
#define KLS_ADREN KLS_N                                  /* the one row 'Adrenaline' = rows 2 (Prompt, bit 0) and 3 (NeedUse, bit 1) */
static int kset_table_log;                              /* [Menu] TableLog */
static const char *klrs_setting(int i);                  /* klreshade.c: what a change of row i does now (and it tells the bridge) */

static int kset_which(const char *name)
{   /* -> 0 .. KLS_N-1 for our names, -1 for anything else (or unreadable) */
    char n[16]; int i;
    if (!name || !klh_rd((DWORD_PTR)name, n, 3) || memcmp(n, "KLS", 3)) return -1;
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n)) return -1;
    for (i = 0; i < KLS_N; i++) if (!strcmp(n, kset_names[i])) return i;
    if (!strcmp(n, "KLSAdren")) return KLS_ADREN;
    return -1;
}

static int kset_get(int i)
{
    if (i == KLS_ADREN) return (kset_v[2] ? 1 : 0) | (kset_v[3] ? 2 : 0);
    return (int)kset_v[i];
}

static void kset_put(int i, int value)
{
    char v[16];
    if (i == KLS_ADREN) {                               /* the combined row: each half through its own row (its own ini key and log line) */
        if (value < 0) value = 0;
        if (value > 3) value = 3;
        kset_put(2, value & 1);
        kset_put(3, (value >> 1) & 1);
        return;
    }
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
    kset_table_log = (int)GetPrivateProfileIntA("Menu", "TableLog", 0, klh_ini);
    klog("settings: the menu's Mod settings rows read Look=%ld Textures=%ld Prompt=%ld NeedUse(E)=%ld CameraFX=%ld Glare=%ld AA=%ld Neural=%ld", kset_v[0], kset_v[1], kset_v[2], kset_v[3], kset_v[4], kset_v[5], kset_v[6], kset_v[7]);
}

/* ---- [Menu] TableLog: the menu manager's table, a LOG LINE, reads only (re\hud_menu.md 8; live check K0) ----
 * READ in kl2.exe: the manager [[0xdd265c]+0x824] (ZMercsMenuElements, vtable 0xbb7dc8; the window system keeps the same pointer at
 * +0x4b4, 0x8a43d8) holds a count at +0x9f48 and {object, kind} pairs from +8: kind 0 element (0x7fad67), 1 window (0x667e5e), 2 colour
 * set (0x47d641), 3 button graphic (0x53c781); int3 past 0x13e8 (0x7fad8d, 0x667e6e, 0x47d629, 0x53c769). 0x861720 (the mouse over the
 * menu) calls vtable +0x84 on entry (id & 0xffff) of the object under the cursor with no kind test; the menu scene's button
 * ZWINDOWS\Menu\DefaultFocus carries id 5000: an entry 5000 that is not an element is the crash of 2026-10-10 14:24. One line whenever
 * the count has changed and stood for 2 s. An element's name is [element+4] (klauto.c). */
#define KSET_MENU_MGR_VT 0x00bb7dc8
#define KSET_MENU_CAP    0x13e8
#define KSET_MENU_HOT    5000
static void kset_tick(int game_thread)
{
    static DWORD polled, seen_n = (DWORD)-1, since, said_n = (DWORD)-1, bad_vt;
    static struct { DWORD obj, kind; } tab[KSET_MENU_CAP];
    static const char *const kind_name[5] = { "an element", "a WINDOW", "a COLOUR SET", "a BUTTON GRAPHIC", "of an unknown kind" };
    DWORD now = GetTickCount(), gd, mgr, vt, n, k, c[5] = { 0, 0, 0, 0, 0 };
    char scene[160], nm[48];
    if (!kset_table_log || !game_thread || !klh_exe_ok || now - polled < 500) return;
    polled = now;
    gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)); mgr = gd ? klh_rd32(gd + 0x824) : 0;
    if (!mgr) return;
    vt = klh_rd32(mgr);
    if (vt != (DWORD)(DWORD_PTR)KLH_VA(KSET_MENU_MGR_VT)) {
        if (vt != bad_vt) { bad_vt = vt; klog("menu: the manager %08lx has vtable %08lx, not ZMercsMenuElements (00bb7dc8): its table is not read", mgr, vt); }
        return;
    }
    n = klh_rd32(mgr + 0x9f48);
    if (n != seen_n) { seen_n = n; since = now; return; }
    if (n == said_n || now - since < 2000) return;
    said_n = n;
    klh_scene(scene, sizeof scene);
    if (n > KSET_MENU_CAP || !klh_rd(mgr + 8, tab, 8 * (SIZE_T)n)) { klog("menu: table count %lu, not readable - OVER THE CAP 5096 if it is above it (scene '%s')", n, scene); return; }
    for (k = 0; k < n; k++) c[tab[k].kind < 4 ? tab[k].kind : 4]++;
    if (n > KSET_MENU_HOT) {
        k = tab[KSET_MENU_HOT].kind < 4 ? tab[KSET_MENU_HOT].kind : 4;
        nm[0] = 0;
        if (k == 0) klh_rdstr(klh_rd32(tab[KSET_MENU_HOT].obj + 4), nm, sizeof nm);
        klog("menu: table %lu of 5096 entries (%lu elements, %lu windows, %lu colour sets, %lu button graphics, %lu other); %lu free below the cap; OVER 5000: entry 5000 is %s%s%s%s; scene '%s'",
             n, c[0], c[1], c[2], c[3], c[4], KSET_MENU_CAP - n, kind_name[k], nm[0] ? " '" : "", nm, nm[0] ? "'" : "",
             scene);
        if (k) klog("menu: entry 5000 is NOT an element - THE MOUSE OVER THE MENU BACKGROUND WILL FAULT (0x861720, the 14:24 crash class)");
    } else
        klog("menu: table %lu of 5096 entries (%lu elements, %lu windows, %lu colour sets, %lu button graphics, %lu other); %lu free below entry 5000; scene '%s'",
             n, c[0], c[1], c[2], c[3], c[4], KSET_MENU_HOT - n, scene);
}

#endif
