/*
 * klgrenade.c - DEAD MEN GRENADES, STEP 0: a LOG-ONLY PROBE. re\grenades_1025.md section 5 is the plan.
 *
 * WHAT IT ANSWERS: does a stock Fragile Alliance player hold a grenade item (inventory kind 0), and does the grenade bit
 * appear in the player's words when the throw key is held. kl2.exe's setter 0x4aa410 can only CLEAR bit 0x40 of
 * [player+0xb90] (READ); 0x544780 copies that bit into bit 0x800 of the action word [player+0x818] every frame (READ,
 * 0x5447f9 / 0x544805). So with stock code both bits are expected to stay 0; this probe shows it in the log.
 *
 * WHAT IT DOES: nothing but reads. On a key press (and every 200 ms while it is held, at most 10 samples, then once on
 * release) it logs [P+0xb90], [P+0x818], [P+0x924] (selected item id) and every inventory entry ([P+0xcec]: +8 array of
 * 16-byte entries, +0xc count; entry +0 key, +8 object, +0xc binding; binding +4 item id (GUESS, see klinv.c), +8 kind
 * 0 grenade, 1 two-handed, 2 one-handed, 3 special). For 3 s after a press it also logs any change of bit 0x40 / 0x800.
 * No write, no call into the game. Local player only, offline Arcade only (klinv_player).
 *
 * WIRING: klhook.c  #include "klgrenade.c" below #include "klinv.c"; klgrenade_tick(game_thread) below klinv_tick;
 *   klgrenade_init() below klinv_init().
 * KEYS: [Grenade] Probe=0 (1 = on; recommended off: it only writes log lines) Key=0x47 (VK 'G'; polled, not consumed).
 */
#ifndef KLGRENADE_C
#define KLGRENADE_C

#define KLGR_O_BTN   0xb90                   /* replicated button state; bit 0x40 = grenade (READ 0x4aa410) */
#define KLGR_O_ACT   0x818                   /* action word; bit 0x800 = grenade (READ 0x5447f9) */

static struct {
    int on, key;
    DWORD press_at, last_sample, watch_until, last_btn, last_act;
    int samples, was, fgwarned;
} klgr;

static void klgr_dump(DWORD p, const char *why)
{
    DWORD btn = 0, act = 0, sel = 0, inv, arr, cnt, i, obj, bind, item, kind;
    klh_rd(p + KLGR_O_BTN, &btn, 4); klh_rd(p + KLGR_O_ACT, &act, 4); klh_rd(p + KLINV_O_SEL, &sel, 4);
    klog("grenade probe (%s): player %08lx b90=%08lx (0x40 %s) 818=%08lx (0x800 %s) selected item %lu",
         why, p, btn, btn & 0x40 ? "SET" : "clear", act, act & 0x800 ? "SET" : "clear", sel);
    klgr.last_btn = btn; klgr.last_act = act;
    if (!klinv_inv(p, &inv, &arr, &cnt)) { klog("grenade probe: inventory not readable"); return; }
    for (i = 0; i < cnt; i++)
        if (klinv_entry(arr, i, &obj, &bind, &item, &kind))
            klog("grenade probe:   entry %lu key %lu object %08lx binding %08lx item %lu kind %lu%s", i, klh_rd32(arr + 16 * i), obj, bind, item, kind,
                 kind == 0 ? " (GRENADE)" : kind == 3 ? " (special)" : "");
}

static void klgrenade_tick(int game_thread)
{
    DWORD now, p, pid = 0; int down;
    if (!klgr.on || !klh_exe_ok || !game_thread) return;
    now = GetTickCount();
    down = (klinv_key(klgr.key) & 0x8000) != 0;
    if (!down && !klgr.was && !(klgr.watch_until && (int)(klgr.watch_until - now) > 0)) return;   /* idle: no player reads */
    if (!(p = klinv_player())) { klgr.was = 0; return; }
    if (klgr.watch_until && (int)(klgr.watch_until - now) > 0) {             /* bit changes after a press, every game tick */
        DWORD btn = 0, act = 0;
        if (klh_rd(p + KLGR_O_BTN, &btn, 4) && klh_rd(p + KLGR_O_ACT, &act, 4)) {   /* a failed read is skipped, not logged as a change */
            if ((btn ^ klgr.last_btn) & 0x40) klog("grenade probe: b90 bit 0x40 now %s (+%lu ms)", btn & 0x40 ? "SET" : "clear", now - klgr.press_at);
            if ((act ^ klgr.last_act) & 0x800) klog("grenade probe: 818 bit 0x800 now %s (+%lu ms)", act & 0x800 ? "SET" : "clear", now - klgr.press_at);
            klgr.last_btn = btn; klgr.last_act = act;
        }
    }
    if (down) {
        klinv_wtp(klinv_fg(), &pid);
        if (pid != GetCurrentProcessId()) { if (!klgr.fgwarned++) klog("grenade probe: key seen but the game window is not in front: ignored"); return; }
    }
    __try {
        if (down && !klgr.was) { klgr.press_at = klgr.last_sample = now; klgr.watch_until = now + 3000; klgr.samples = 0; klgr_dump(p, "press"); }
        else if (down && now - klgr.last_sample >= 200 && klgr.samples < 10) { klgr.last_sample = now; klgr.samples++; klgr_dump(p, "held"); }
        else if (!down && klgr.was) klgr_dump(p, "release");
    } __except (EXCEPTION_EXECUTE_HANDLER) { klog("grenade probe: fault while reading: probe off"); klgr.on = 0; }
    klgr.was = down;
}

static void klgrenade_init(void)
{
    int v;
    if (!GetPrivateProfileIntA("Grenade", "Probe", 0, klh_ini)) return;
    v = (int)GetPrivateProfileIntA("Grenade", "Key", 0x47, klh_ini); klgr.key = v < 1 || v > 0xfe ? 0x47 : v;
    if (!klinv_key) {                                                        /* klinv_init fills these only when [Inv] is on */
        HMODULE u = GetModuleHandleA("user32.dll"); if (!u) u = LoadLibraryA("user32.dll");
        if (u) {
            klinv_key = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
            klinv_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
            klinv_wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
        }
    }
    if (!klinv_key || !klinv_fg || !klinv_wtp) { klog("grenade probe: user32 functions not found: OFF"); return; }
    klgr.on = 1;
    klog("grenade probe: on (log only, no writes); Key=0x%02x; offline Arcade, local player. re\\grenades_1025.md step 0", klgr.key);
}

#endif /* KLGRENADE_C */
