/*
 * klinv.c - MORE GUNS IN FRAGILE ALLIANCE (Arcade, offline): a SHELF. re\weapon_slots.md is the note.
 *
 * THE RULE (READ, kl2.exe build 0490): the pickup routine 0x6cc1d0 (ZFFPlayer vtable slot 417) counts the guns in the
 * inventory with 0x73c470(inv, 2) + 0x73c470(inv, 1) (kind 2 one-handed, kind 1 two-handed; 0x6cc2d7 .. 0x6cc2ef) and
 * with `cmp bl, 2 ; jb` (0x6cc2ef) lets a gun through only when fewer than two are held; otherwise the gun in the hand
 * is dropped. The world pickup trigger 0x7cd310 refuses earlier by the same count (<= 1). Kinds 0 (grenade) and 3 (special
 * equipment) are not counted. The limit is a constant in CODE, and that code is inside the hashed ranges (klranges.h):
 * it cannot be patched. The HUD (ZWeaponDisplay tick 0x88bac0) shows two slots (the held one and 'the other').
 *
 * WHAT THIS DOES: the count 0x73c470 walks the inventory's entries ([player+0xcec]: +8 array of 16-byte entries, +0xc
 * count; an entry counts when [entry+8] (the gun object) is non-zero and [[entry+0xc]+8] (its binding's kind) is the
 * kind asked - all READ at 0x73c470..0x73c4a2). A gun whose object pointer in its entry is 0 is NOT COUNTED, and the HUD's
 * 'other weapon' lookup (0x49b2f0) skips it too (GUESS: it tests the same field). So the hook SHELVES a gun by writing
 * ZERO to [entry+8] (heap data; no code, no vtable, no IAT, no call into the game) and keeps the object pointer. Two guns
 * in hand + one on the shelf = three guns. A key rotates: it shelves the gun that is not selected and brings the shelved
 * one back. Pick-ups work as stock when fewer than two guns are held.
 *
 * ONLY OFFLINE ARCADE (rules object ZGameRulesHeist 0xbd3514, session game type 4, no network role) and OFF unless
 * [Inv] Enable=1. kl_online() = inert: online the inventory replicates (DDL_SInventoryItems: item + ref), a shelved gun
 * would be a gun the peers still see you carry or one they never see again (GUESS, not seen).
 *
 * GUESSES (nothing of this has run in the game): (1) a shelved gun's object keeps living (not freed, not returned to
 * the weapon pool by anything but the round reset) and is simply not reachable from the inventory; (2) its model stays
 * wherever the game parked it (the back model) - it may still be drawn; (3) the game never rewrites [entry+8] of an
 * entry that has none, except when you pick up the SAME item again (then the restore finds the slot taken, logs it and
 * gives the object up); (4) the rest of the game (ammo boxes, the switch key, the drop key) treats the entry as empty;
 * (5) 0x49b2f0 tests [entry+8] like 0x73c470 (READ 0x49b311 cmp [eax+8],0; was GUESS 1); the add path 0x8aacc0 -> 0x6a00e0 -> mov [esi+8],ebx (0x8aad03) fills the entry found by item id (0x5aa000 compares [entry+0], READ), so a third DIFFERENT item fills its own pre-registered entry; at death / round end / a new player object the shelf is dropped (the object belongs to the pool again after the
 * round reset) - the hook cannot give it back; (6) binding+4 is the item id.
 *
 * WIRING (the lead; mirrors klnet.c):
 *   klhook.c ~651  #include "klinv.c"        (after klnet.c)
 *   klhook.c ~782  klinv_tick(game_thread);  in klh_tick
 *   klhook.c ~1129 klinv_init();             in klh_w_runcallbacks, after klnet_init();
 * KEYS: [Inv] Enable=0 Key=0x77 (VK_F8; the rotate key; the key is polled, NOT consumed, so the game also sees it: pick one it does not bind. Menus/pause are NOT excluded, GUESS: harmless, the swap only edits the inventory) Log=1 (0 quiet, 1 events, 2 + every refusal).
 */
#ifndef KLINV_C
#define KLINV_C

#define KLINV_RULES_VT   0x00bd3514u             /* ZGameRulesHeist (READ klhook.c kl_online) */
#define KLINV_SESSION    0x0168e598u
#define KLINV_SETTINGS   0x0168e9e4u
#define KLINV_PLAYER_VT  0x00bb45f4u             /* ZFFPlayer */
#define KLINV_COUNT      0x0073c470u             /* count(inv, kind): the walk this file relies on */
#define KLINV_O_INV      0xcec                   /* [player+0xcec] inventory (READ re/hud_weapon.md, 0x6cc2d1) */
#define KLINV_O_SEL      0x924                   /* [player+0x924] item id selected (READ re/hud_weapon.md 0x88bac0) */
#define KLINV_MAXSHELF   3

static struct {
    int on, key, log;
} klinv;

static struct {
    int n;
    DWORD player, inv;
    struct { DWORD idx, obj, bind, item, key, objvt; } e[KLINV_MAXSHELF + 1];   /* +1: a swap on a full shelf shelves first, then restores */
    int fgwarned, told_code;
} klinv_r;

static SHORT (WINAPI *klinv_key)(int);
static HWND (WINAPI *klinv_fg)(void);
static DWORD (WINAPI *klinv_wtp)(HWND, LPDWORD);

/* the arcade, offline, in a round: the local player's object, or 0 */
static DWORD klinv_player(void)
{
    DWORD sm, gs, rules, gd, p, role = 0; BYTE sel = 0xff;
    if (kl_online()) return 0;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLINV_SESSION))) || klh_rd32(sm + 0x5c) != 4) return 0;
    if (!klh_rd(sm + 0x54, &role, 4) || role == 2 || role == 3) return 0;
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLINV_SETTINGS))) || !(rules = klh_rd32(gs + 0x54)) || klh_rd32(rules) != KLINV_RULES_VT) return 0;
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &sel, 1) || sel >= 28) return 0;
    if (!(p = klh_rd32(gd + 0x828 + 4 * sel)) || klh_pvt(p) != KLINV_PLAYER_VT) return 0;
    return p;
}

/* the inventory's array and count, bounds-checked */
static int klinv_inv(DWORD player, DWORD *inv, DWORD *arr, DWORD *cnt)
{
    DWORD n = 0;
    if (!(*inv = klh_rd32(player + KLINV_O_INV)) || !(*arr = klh_rd32(*inv + 8)) || !klh_rd(*inv + 0xc, &n, 4) || n == 0 || n > 64) return 0;
    *cnt = n; return 1;
}

/* entry i -> object, binding, item, kind (kind 0xff when the entry has no binding). Layout READ at 0x73c470 (+8 object,
   +0xc binding, binding+8 kind); binding+4 = item id is a GUESS from the earlier reading of 0x5aa000 (only used for
   the log and for 'not the selected one'). */
static int klinv_entry(DWORD arr, DWORD i, DWORD *obj, DWORD *bind, DWORD *item, DWORD *kind)
{
    DWORD e = arr + 16 * i;
    *obj = *bind = *item = 0; *kind = 0xff;
    if (!klh_rd(e + 8, obj, 4) || !klh_rd(e + 0xc, bind, 4)) return 0;
    if (*bind > 0x10000 && (!klh_rd(*bind + 4, item, 4) || !klh_rd(*bind + 8, kind, 4))) return 0;
    return 1;
}

static int klinv_guns(DWORD arr, DWORD cnt, DWORD *idx, int max)
{
    DWORD i, obj, bind, item, kind; int g = 0;
    for (i = 0; i < cnt; i++)
        if (klinv_entry(arr, i, &obj, &bind, &item, &kind) && obj && (kind == 1 || kind == 2) && g < max) idx[g++] = i;
    return g;
}

static void klinv_drop_shelf(const char *why)
{
    if (klinv_r.n) klog("inv: shelf of %d gun(s) dropped (%s): the object(s) are not reachable any more until the round reset", klinv_r.n, why);
    klinv_r.n = 0; klinv_r.player = klinv_r.inv = 0;
}

static int klinv_put(DWORD at, DWORD v, const char *what) { return klh_data((void *)(DWORD_PTR)at, &v, 4, what); }

static void klinv_press(void)
{
    static const BYTE count_code[7] = { 0x53, 0x8b, 0x59, 0x0c, 0x56, 0x32, 0xc0 };      /* 0x73c470 push ebx ; mov ebx,[ecx+0xc] ; push esi ; xor al,al */
    DWORD player, inv, arr, cnt, idx[8], sel = 0, obj, bind, item, kind; int g, i, shelve = -1;
    if (!(player = klinv_player())) { if (klinv.log > 1) klog("inv: key: no Arcade round of your own offline"); return; }
    if (!klc_same_code(KLINV_COUNT, count_code, sizeof count_code)) { if (!klinv_r.told_code++) klog("inv: 0x73c470 is not the counting routine this build knows: nothing is written"); return; }
    if (klinv_r.n && klinv_r.player != player) klinv_drop_shelf("another player object");
    if (!klinv_inv(player, &inv, &arr, &cnt)) { klog("inv: key: the inventory cannot be read"); return; }
    if (klinv_r.n && klinv_r.inv != inv) klinv_drop_shelf("another inventory object");
    klh_rd(player + KLINV_O_SEL, &sel, 4);
    g = klinv_guns(arr, cnt, idx, 8);
    /* 1. when two guns are held, shelve the one that is not selected (a slot is then free for a pick-up) */
    if (g >= 2) {
        for (i = 0; i < g; i++)
            if (klinv_entry(arr, idx[i], &obj, &bind, &item, &kind) && item != sel && klh_rd32(arr + 16 * idx[i]) != sel) { shelve = i; break; }   /* both candidate ids (binding+4 GUESS, entry+0 READ 0x5aa020) must differ from the selected one */
        if (shelve < 0) shelve = g - 1;
    } else if (!klinv_r.n) { if (klinv.log > 1) klog("inv: key: %d gun(s) held and nothing on the shelf: nothing to do", g); return; }
    if (shelve >= 0) {
        DWORD e = idx[shelve], o, b, it, k, key = klh_rd32(arr + 16 * idx[shelve]), ovt;
        e = idx[shelve];
        klinv_entry(arr, e, &o, &b, &it, &k);
        ovt = klh_rd32(o);
        if (!ovt) { klog("inv: key: the gun object has no readable vtable: not shelved"); return; }
        key = klh_rd32(arr + 16 * e);
        if (!klinv_put(arr + 16 * e + 8, 0, "inventory entry: gun object pointer, shelved")) { klog("inv: key: write refused"); return; }
        klinv_r.player = player; klinv_r.inv = inv;
        klinv_r.e[klinv_r.n].idx = e; klinv_r.e[klinv_r.n].obj = o; klinv_r.e[klinv_r.n].bind = b; klinv_r.e[klinv_r.n].item = it; klinv_r.e[klinv_r.n].key = key; klinv_r.e[klinv_r.n].objvt = ovt; klinv_r.n++;
        klog("inv: shelved item %lu (entry %lu, object %08lx, kind %lu); %d on the shelf", it, e, o, k, klinv_r.n);
        g--;
    }
    /* 2. bring back the OLDEST shelved gun when a slot is free (fewer than two held), but never the one just shelved */
    if (klinv_r.n > 0 && g < 2 && !(shelve >= 0 && klinv_r.n < 2)) {   /* the gun just shelved is e[n-1]; with n >= 2 e[0] is an older one */
        DWORD e = klinv_r.e[0].idx, curobj = 1, curbind = 0;
        /* never write a pointer that may have been freed: the entry must still hold the recorded item id (entry+0), the
           recorded binding and no object, and the gun object must still carry the vtable it had when it was shelved */
        if (e < cnt && klh_rd(arr + 16 * e + 8, &curobj, 4) && klh_rd(arr + 16 * e + 0xc, &curbind, 4) && curobj == 0 && curbind == klinv_r.e[0].bind &&
            klh_rd32(arr + 16 * e) == klinv_r.e[0].key && klh_rd32(klinv_r.e[0].obj) == klinv_r.e[0].objvt &&
            klinv_put(arr + 16 * e + 8, klinv_r.e[0].obj, "inventory entry: gun object pointer, restored")) {
            klog("inv: restored item %lu (entry %lu, object %08lx)", klinv_r.e[0].item, e, klinv_r.e[0].obj);
        } else klog("inv: could not restore item %lu: entry %lu is taken or changed (same item picked up again?); that gun is given up", klinv_r.e[0].item, e);
        for (i = 1; i < klinv_r.n; i++) klinv_r.e[i - 1] = klinv_r.e[i];
        klinv_r.n--;
    }
}

static void klinv_tick(int game_thread)
{
    static DWORD last; static int was; DWORD now, pid = 0; int down;
    if (!klinv.on || !klh_exe_ok) return;
    if (klinv_r.n) {                                           /* EVERY call, not throttled: the shelf is kept only while the same player lives in the same inventory */
        DWORD p = klinv_player(), inv = 0, arr = 0, cnt = 0;
        if (!p) klinv_drop_shelf("no offline Arcade round");
        else if (p != klinv_r.player) klinv_drop_shelf("another player object");
        else if (!klinv_inv(p, &inv, &arr, &cnt) || inv != klinv_r.inv) klinv_drop_shelf("another inventory object");
    }
    now = GetTickCount();
    if (now - last < 30) return;
    last = now;
    down = (klinv_key(klinv.key) & 0x8000) != 0;
    if (down && !was) {
        klinv_wtp(klinv_fg(), &pid);
        if (pid == GetCurrentProcessId() && !game_thread) return;                 /* not our thread: leave `was` alone, the press is seen on the next game-thread tick */
        if (pid == GetCurrentProcessId() && game_thread) {
            __try { klinv_press(); } __except (EXCEPTION_EXECUTE_HANDLER) { klog("inv: fault in the key handler: shelf dropped"); klinv_r.n = 0; }
        } else if (!klinv_r.fgwarned++) klog("inv: key seen but the game window is not in front or the tick is not on the game thread: ignored");
    }
    was = down;
}

static void klinv_init(void)
{
    HMODULE u; int v;
    if (!GetPrivateProfileIntA("Inv", "Enable", 0, klh_ini)) return;
    v = (int)GetPrivateProfileIntA("Inv", "Key", 0x77, klh_ini); klinv.key = v < 1 || v > 0xfe ? 0x77 : v;
    v = (int)GetPrivateProfileIntA("Inv", "Log", 1, klh_ini); klinv.log = v < 0 ? 0 : v > 2 ? 2 : v;
    u = GetModuleHandleA("user32.dll"); if (!u) u = LoadLibraryA("user32.dll");
    if (u) {
        klinv_key = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState");
        klinv_fg = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow");
        klinv_wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId");
    }
    if (!klinv_key || !klinv_fg || !klinv_wtp) { klog("inv: user32 functions not found: OFF"); return; }
    klinv.on = 1;
    klog("inv: on; Key=0x%02x Log=%d; offline Arcade only. Hold two guns, press the key: the one not selected goes on the shelf (its entry's object pointer is zeroed: not counted, GUESS not shown), pick up a third; press again to swap / bring one back. re\\weapon_slots.md", klinv.key, klinv.log);
}

#endif /* KLINV_C */
