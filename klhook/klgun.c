/*
 * klgun.c - switchable looks of guns: a Dead Men gun's model on a Dog Days gun. Part of KLHook (included by klhook.c
 * before klchar.c, SHIP and TEST alike). Heap data writes only; no code byte, no game call.
 * Data side and the reasons: tools\kl_guns.py (its docstring). NOT RUN IN THE GAME YET (2026-10-09).
 *
 * THE DATA. A level built by kl_guns.py has, for some guns, a model whose object table is
 *     [the stock parts][the parts of look 1][the parts of look 2] ...
 * A part (a mesh object of the .prm, 64 bytes) carries a variant byte at +0x0f; the gun entity's variant is 0, so a
 * part is drawn when its byte is 0. As built: stock parts 0, look n parts Hidden + n (100 + n) - the stock gun.
 * KLGuns.ini beside the level archive lists per gun: Item (eFF2Item number), Root (the model's chunk index in THIS
 * build's .prm), Stock (number of stock parts), Looks, Look<n>Parts.
 *
 * WHAT THE HOOK DOES. About once a second, on a level that has the file: for every gun, the wanted group (0 = stock,
 * n = look n) gets variant 0 in the loaded .prm and every other group its Hidden + group. The chunk is found the way
 * the game finds it: the pointer table at 0xeac7b0 (one pointer per chunk index, count at 0xeac7a4; 0x6ad0db), then
 * root +0x14 object count, +0x18 object table chunk, each entry an object chunk. Everything is checked before a
 * byte is written (root type 7, object type 8, the count equal to the file's groups); a mismatch switches that gun
 * off for the level and says so once. The bytes are heap data of the loaded file: outside every hashed range.
 * It is a change of the MODEL, so everyone who carries that gun in the level shows the look - the player, the AI
 * heisters, the police. And it is local: another machine shows what its own setting says.
 * ASSUMPTIONS, not run: that a part is drawn by comparing its variant byte with the entity's each time (if the game
 * caches which parts a gun instance draws, a switch shows only on guns created after it - the hook writes as soon
 * as the level's file is in, which is before the round's guns are handed out); that 100.. matches no gun entity.
 *
 * WHICH LOOK
 *   KLGunStart  0..2   the starting rifle (item 29, Zastava): 0 stock, 1 = its look 1 (MP5), 2 = its look 2 (AK-74)
 *   KLGunSet    0..1   every other gun of the file: 0 stock, 1 = its look 1 (the Dead Men look)
 * Two menu options (window KLGuns of the overlay, mkoverlay.py) answered through klchar.c's private vtable on the
 * option object: klchar.c asks klg_which() for the names it does not know itself. Kept in KLHook.ini:
 *   [Guns]
 *   Enable=1
 *   Start=0
 *   Set=0
 *   Log=1
 */
#ifndef KLGUN_C
#define KLGUN_C

#define KLG_TABLE     0x00eac7b0              /* chunk index -> pointer */
#define KLG_COUNT     0x00eac7a4
#define KLG_NGUN      16
#define KLG_NLOOK     4
#define KLG_START_ITEM 29                     /* eFF2ItemRifle_Zastavam85 */

static int klg_on = 1, klg_log = 1;
static volatile LONG klg_start, klg_set;
static CRITICAL_SECTION klg_cs;
static struct { int on, n, hidden; struct { DWORD root; int item, stock, looks, parts[KLG_NLOOK], off, shown; char tpl[40], label[KLG_NLOOK][24]; } g[KLG_NGUN]; char key[64]; } klg_f;

static const char *const klg_names[2] = { "KLGunStart", "KLGunSet" };
static const int klg_upper[2] = { 2, 1 };     /* mkoverlay.py GUN_ROWS has as many entries + 1 */
static volatile LONG *const klg_value[2] = { &klg_start, &klg_set };
static const char *const klg_keys[2] = { "Start", "Set" };

static int klg_which(const char *name)
{   /* -> 0 / 1 for our two option names, -1 for anything else (or unreadable) */
    char n[12]; int i;
    if (!klg_on || !name || !klh_rd((DWORD_PTR)name, n, 5) || memcmp(n, "KLGun", 5)) return -1;
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n)) return -1;
    for (i = 0; i < 2; i++) if (!strcmp(n, klg_names[i])) return i;
    return -1;
}

static int klg_get(int i) { return (int)*klg_value[i]; }

static void klg_put(int i, int value)
{
    char v[16];
    if (value < 0) value = 0;
    if (value > klg_upper[i]) value = klg_upper[i];
    if (InterlockedExchange(klg_value[i], value) != value) {
        snprintf(v, sizeof v, "%d", value); WritePrivateProfileStringA("Guns", klg_keys[i], v, klh_ini);
        if (klg_log) klog("guns: menu set %s = %d", klg_names[i], value);
    }
}

/* From klsteam.c's klh_level_open: the game opens the level archive <key> ("f01\f01_main.zip") from <opened>. */
static void klg_level_open(const char *key, const char *opened)
{
    char file[MAX_PATH], sec[16], k[24], *s; int i, j, n; DWORD len;
    if (!klg_on) return;
    len = GetFullPathNameA(opened, MAX_PATH, file, 0);
    if (!len || len >= MAX_PATH || !(s = strrchr(file, 0x5c)) || (size_t)(s - file) + 12 >= sizeof file) return;
    strcpy(s + 1, "KLGuns.ini");
    EnterCriticalSection(&klg_cs);
    memset(&klg_f, 0, sizeof klg_f);
    snprintf(klg_f.key, sizeof klg_f.key, "%s", key); if ((s = strrchr(klg_f.key, '.')) != 0) *s = 0;
    n = (int)GetPrivateProfileIntA("Guns", "Count", 0, file);
    if (GetPrivateProfileIntA("Guns", "Version", 0, file) == 1 && n > 0 && n <= KLG_NGUN) {
        klg_f.hidden = (int)GetPrivateProfileIntA("Guns", "Hidden", 100, file);
        for (i = 0; i < n; i++) {
            snprintf(sec, sizeof sec, "Gun.%d", i + 1);
            klg_f.g[i].root = GetPrivateProfileIntA(sec, "Root", 0, file);
            klg_f.g[i].item = (int)GetPrivateProfileIntA(sec, "Item", 0, file);
            klg_f.g[i].stock = (int)GetPrivateProfileIntA(sec, "Stock", 0, file);
            klg_f.g[i].looks = (int)GetPrivateProfileIntA(sec, "Looks", 0, file);
            klg_f.g[i].shown = -1;
            GetPrivateProfileStringA(sec, "Template", "?", klg_f.g[i].tpl, sizeof klg_f.g[i].tpl, file);
            if (!klg_f.g[i].root || klg_f.g[i].stock < 1 || klg_f.g[i].looks < 1 || klg_f.g[i].looks > KLG_NLOOK) break;
            for (j = 0; j < klg_f.g[i].looks; j++) {
                snprintf(k, sizeof k, "Look%dParts", j + 1); klg_f.g[i].parts[j] = (int)GetPrivateProfileIntA(sec, k, 0, file);
                snprintf(k, sizeof k, "Look%d", j + 1); GetPrivateProfileStringA(sec, k, "?", klg_f.g[i].label[j], sizeof klg_f.g[i].label[j], file);
                if (klg_f.g[i].parts[j] < 1) break;
            }
            if (j < klg_f.g[i].looks) break;
        }
        if (i == n && klg_f.hidden >= 64 && klg_f.hidden + KLG_NLOOK <= 255) { klg_f.on = 1; klg_f.n = n; }
        else klog("guns: %s is not usable (entry %d, Hidden=%d): this level has the stock guns only", file, i + 1, klg_f.hidden);
    }
    LeaveCriticalSection(&klg_cs);
    if (klg_log && klg_f.on) klog("guns: level %s has %d gun(s) with looks (%s)", klg_f.key, klg_f.n, file);
}

static void klg_apply(int gi, int want)
{   /* group `want` of gun gi shown, the others hidden; reads and checks everything first */
    DWORD count = 0, root, tab, n, objs[96], idx[96]; BYTE head[0x20], oh[0x10]; int total, i, j, g, changed = 0, okay = 1; const char *why = 0;
    total = klg_f.g[gi].stock; for (j = 0; j < klg_f.g[gi].looks; j++) total += klg_f.g[gi].parts[j];
    if (total > 96) why = "more than 96 parts";
    else if (!klh_rd((DWORD_PTR)KLH_VA(KLG_COUNT), &count, 4) || klg_f.g[gi].root >= count) return;                 /* the level's file is not in (yet) */
    else if (!(root = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * klg_f.g[gi].root))) || !klh_rd(root, head, sizeof head)) return;
    else if (head[2] != 7 || head[3] != 0) why = "the chunk is not a model root";
    else if ((n = *(DWORD *)(head + 0x14)) != (DWORD)total) why = "the model does not have the parts the file lists";
    else if (*(DWORD *)(head + 0x18) >= count || !(tab = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * *(DWORD *)(head + 0x18)))) || !klh_rd(tab, idx, 4 * n)) why = "no object table";
    if (!why) for (i = 0; i < total; i++) {
        if (idx[i] >= count || !(objs[i] = klh_rd32((DWORD_PTR)KLH_VA(KLG_TABLE + 4 * idx[i]))) || !klh_rd(objs[i], oh, sizeof oh) || oh[2] != 8 || oh[3] != 0) { why = "a part is not a mesh object"; break; }
    }
    if (why) {
        if (!klg_f.g[gi].off) klog("guns: %s (model %lu) left alone on this level: %s", klg_f.g[gi].tpl, klg_f.g[gi].root, why);
        klg_f.g[gi].off = 1; return;
    }
    for (i = 0, g = 0, j = klg_f.g[gi].stock; i < total; i++) {
        BYTE cur = 0, v;
        while (i >= j) j += klg_f.g[gi].parts[g++];           /* g = the group object i belongs to: 0 stock, n look n */
        v = (BYTE)(g == want ? 0 : klg_f.hidden + g);
        if (!klh_rd(objs[i] + 0x0f, &cur, 1)) { okay = 0; continue; }
        if (cur != v) { if (klh_data((void *)(DWORD_PTR)(objs[i] + 0x0f), &v, 1, "gun part variant")) changed++; else okay = 0; }
    }
    if ((changed || klg_f.g[gi].shown != want) && klg_log)
        klog("guns: %s now shows %s (%d part byte(s) written%s)", klg_f.g[gi].tpl, want ? klg_f.g[gi].label[want - 1] : "its own model", changed, okay ? "" : "; SOME COULD NOT BE WRITTEN");
    klg_f.g[gi].shown = want;
}

static void klg_tick(void)
{
    static DWORD calls; char scene[160], key[64]; int i, want;
    if (!klg_on || !klh_exe_ok || !klg_f.on || (calls++ & 31)) return;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key) || _stricmp(key, klg_f.key)) return;
    EnterCriticalSection(&klg_cs);
    for (i = 0; i < klg_f.n; i++) {
        if (klg_f.g[i].off) continue;
        want = klg_f.g[i].item == KLG_START_ITEM ? (int)klg_start : (klg_set ? 1 : 0);
        if (want > klg_f.g[i].looks) want = 0;
        klg_apply(i, want);
    }
    LeaveCriticalSection(&klg_cs);
}

static void klg_init(void)
{
    InitializeCriticalSection(&klg_cs);
    klg_on = GetPrivateProfileIntA("Guns", "Enable", 1, klh_ini);
    klg_log = GetPrivateProfileIntA("Guns", "Log", 1, klh_ini);
    klg_start = (LONG)GetPrivateProfileIntA("Guns", "Start", 0, klh_ini); if (klg_start < 0 || klg_start > klg_upper[0]) klg_start = 0;
    klg_set = (LONG)GetPrivateProfileIntA("Guns", "Set", 0, klh_ini); if (klg_set < 0 || klg_set > klg_upper[1]) klg_set = 0;
    if (klg_on) klog("guns: on; starting rifle look %ld, shop guns %s", klg_start, klg_set ? "Dead Men looks" : "Dog Days");
}

#endif /* KLGUN_C */
