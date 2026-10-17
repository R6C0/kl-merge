/*
 * klpm.c - PRIVATE-MATCH OPTIONS, step B1 of re\pm_options.md (2026-10-18). Part of KLHook (included by klhook.c BEFORE klchar.c, whose
 * private option-interface vtable asks kpm_which() for the names it does not know, exactly as it asks klg_which() / kset_which()).
 * OFF by default: [Match] Enable=0 makes kpm_which() answer -1 for every name, so the menu and the game behave as stock.
 *
 * WHAT IS HERE (first, most feasible step - no network, no game call, no code byte of kl2.exe):
 *   1. Three option names the game does not have, stored in this DLL and in KLHook.ini [Match] (the options object is deleted at every
 *      scene change, the values must outlive it - klchar.c section 1):
 *          KLMGun   0 = the level's own start gun, 1..KPM_GUNS = a shop item   (VALUE ONLY: nothing equips it yet, see NOT DONE)
 *          KLMVote  0 = no preference, 1..N = the Nth map of maps.ini         (value only; kpm_tally() turns votes into a map)
 *          KLMPlay  0 = off, 1 = playlist in order, 2 = random without repeats (value only; kpm_next() is the cursor)
 *      The names start with KLM, not KLGun: klgun.c answers anything that starts with 'KLGun' (KLGunStart / KLGunSet).
 *      The XML entry counts of the menu rows are these ranges (klchar.c section 1, re\wardrobe.md 5a): the page is mkoverlay.py's window
 *      KLMatch (B1, 2026-10-18; built when KLHook.ini has [Match] Enable=1; maps.ini.sample gives the map names).
 *   2. maps.ini (GUESS on the format; the file does not exist yet, kpm_maps_load() reads it if present):
 *          [Maps]            Count=3
 *          [Map.1]           Id=DM01   Name=Subway (Dead Men)   Slot=F01
 *          [Bundle.1]        Name=Dead Men classics   Maps=DM01,DM03A,DM05A
 *      Path: [Match] Maps=<file>, default KLExpansion\Maps\maps.ini beside kl2.exe (kl2.exe's folder, which is also the DLL's).
 *   3. Pure functions with an off-game test (klpm_test.c): kpm_tally() (vote count -> map index; ties and 'no preference' by a draw seeded
 *      with the lobby id, so a restart does not re-roll) and kpm_next() (playlist cursor, sequence or random without repeats).
 *
 * NOT DONE (each is a later step of the build order, re\pm_options.md 6):
 *   - equipping KLMGun: the equip call behind the shop buy (0x7558ce) is not read (B0); this file does not call anything;
 *   - applying a tally / the cursor to Heist_SelectedLevel or MP_SelectedLevel, and every Steam lobby part (B2 .. B5);
 *   - KLMVote's upper bound follows the loaded maps.ini, the XML must have as many entries (GUESS: nobody checks the mismatch).
 *
 * B2 (2026-10-18, re\pm_options.md 9): THE ARCADE PLAYLIST. When an Arcade match ends the hook picks the next map (kpm_next) and (a) writes
 * the Arcade map selector's stored position, the byte of the option Heist_SelectedLevel at 0x154d632, so the map page opens on that entry,
 * and (b) tells klslot.c which menu page that entry belongs to (kpm_override), so Accept loads the playlist map even if the player opened
 * another page. The game-facing half is klpm_arc.c (needs klslot.c's tables, so it is included AFTER klslot.c); this file holds the pure
 * parts: kpm_slot_pos, kpm_advance, kpm_override, the list / bundle parsing. All behind [Match] Enable=1 AND Arcade=1.
 *
 * KLHook.ini
 *   [Match]
 *   Enable=0        1 = answer KLMGun / KLMVote / KLMPlay
 *   Arcade=1        (with Enable=1) 1 = apply the playlist after an Arcade match; 0 = the options only
 *   Mode=           playlist mode when the menu row KLMPlay is 0: off / order / random (or 0 / 1 / 2)
 *   Playlist=       map Ids from maps.ini, comma separated ('' = Bundle=, else every map of maps.ini)
 *   Bundle=         name of a [Bundle.N] section of maps.ini
 *   Log=1
 *   Maps=           path of maps.ini ('' = KLExpansion\Maps\maps.ini beside the DLL)
 *   Gun=0 Vote=0 Play=0    the choice; rewritten when the menu changes it
 *   Cursor=0        playlist position (rewritten by kpm_next's caller)
 *   Seed=1          draw seed (the lobby id once there is a lobby)
 */
#ifndef KLPM_C
#define KLPM_C

#define KPM_GUNS   36                         /* the online shop table has 36 rows (shop_plan.md 1); GUESS that one value per row is wanted */
#define KPM_MAXMAP 32
#define KPM_NPLAY  2

/* ---------------------------------------------------------------- pure core (no game, no hook state) */

typedef struct { char id[16], name[48], slot[4]; } kpm_map_t;
static kpm_map_t kpm_map[KPM_MAXMAP];
static int kpm_nmap;

static unsigned kpm_mix(unsigned x)
{   /* small integer hash (xorshift-multiply): deterministic on every machine */
    x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16; return x;
}

/* votes[i]: 0 = no preference, 1..nmaps = the map (index+1); any other value counts as no preference.
 * Returns the winning index 0..nmaps-1, or -1 if nmaps <= 0. Most votes wins; a tie (or nobody voting) is drawn among the tied maps
 * (among all maps if nobody voted), seeded with 'seed' only, so the result is a function of its arguments. */
static int kpm_tally(const int *votes, int nvotes, int nmaps, unsigned seed)
{
    int cnt[KPM_MAXMAP], i, best = 0, nt = 0, pick, tied[KPM_MAXMAP];
    if (nmaps <= 0 || nmaps > KPM_MAXMAP) return -1;
    memset(cnt, 0, sizeof cnt);
    for (i = 0; i < nvotes; i++) if (votes[i] >= 1 && votes[i] <= nmaps) cnt[votes[i] - 1]++;
    for (i = 0; i < nmaps; i++) if (cnt[i] > best) best = cnt[i];
    for (i = 0; i < nmaps; i++) if (best == 0 || cnt[i] == best) tied[nt++] = i;
    pick = nt == 1 ? 0 : (int)(kpm_mix(seed) % (unsigned)nt);
    return tied[pick];
}

/* The playlist. list[0..n-1] are map indexes (into maps.ini). mode 1 = in order, 2 = random without repeats until all have been played.
 * 'cursor' counts matches played so far (persisted by the caller). For mode 2 the order is a seeded shuffle of the list, a new shuffle for
 * each lap (seed ^ lap), and the last map of a lap is never the first of the next. Returns a map index, or -1 for n <= 0 or another mode. */
static int kpm_next(int mode, const int *list, int n, int cursor, unsigned seed)
{
    int ord[KPM_MAXMAP], i, j, lap, pos;
    if (n <= 0 || n > KPM_MAXMAP || (mode != 1 && mode != 2) || cursor < 0) return -1;
    lap = cursor / n; pos = cursor % n;
    if (mode == 1) return list[pos];
    {
        int prev_last = -1;
        for (j = 0; j <= lap; j++) {             /* shuffle lap j; only the last lap is returned, but lap j-1 decides the seam */
            for (i = 0; i < n; i++) ord[i] = list[i];
            for (i = n - 1; i > 0; i--) { int k = (int)(kpm_mix(seed ^ (unsigned)(j * 0x9e3779b1U) ^ (unsigned)(i * 0x85ebca6bU)) % (unsigned)(i + 1)); int t = ord[i]; ord[i] = ord[k]; ord[k] = t; }
            if (n > 1 && prev_last >= 0 && ord[0] == prev_last) { int t = ord[0]; ord[0] = ord[1]; ord[1] = t; }
            prev_last = ord[n - 1];
        }
    }
    return ord[pos];
}

/* split "DM01,DM03A" into map indexes (by Id, case-insensitive); unknown ids are skipped. Returns the count. */
static int kpm_parse_list(const char *s, int *out, int cap)
{
    char tok[24]; int n = 0, i;
    while (*s && n < cap) {
        int k = 0;
        while (*s == ' ' || *s == ',') s++;
        while (*s && *s != ',' && k < (int)sizeof tok - 1) tok[k++] = *s++;
        while (k > 0 && tok[k - 1] == ' ') k--;
        tok[k] = 0;
        if (!k) continue;
        for (i = 0; i < kpm_nmap; i++) if (!_stricmp(kpm_map[i].id, tok)) { out[n++] = i; break; }
    }
    return n;
}

static void kpm_maps_load(const char *file)
{
    char sec[16]; int i, n;
    kpm_nmap = 0;
    n = (int)GetPrivateProfileIntA("Maps", "Count", 0, file);
    if (n > KPM_MAXMAP) n = KPM_MAXMAP;
    for (i = 0; i < n; i++) {
        kpm_map_t *m = &kpm_map[kpm_nmap];
        snprintf(sec, sizeof sec, "Map.%d", i + 1);
        GetPrivateProfileStringA(sec, "Id", "", m->id, sizeof m->id, file);
        GetPrivateProfileStringA(sec, "Name", "", m->name, sizeof m->name, file);
        GetPrivateProfileStringA(sec, "Slot", "", m->slot, sizeof m->slot, file);
        if (m->id[0]) kpm_nmap++;
    }
}

/* ---------------------------------------------------------------- B2: Arcade playlist, pure parts */

/* "F07" -> 6 (0-based slot index), anything else -> -1 */
static int kpm_slot_idx(const char *s)
{
    if (!s || (s[0] != 'F' && s[0] != 'f') || s[1] != '0' || s[2] < '1' || s[2] > '9' || s[3]) return -1;
    return s[2] - '1';
}

/* slot index 0..8 -> the Arcade page's menu POSITION (kl2 0x80c9f0's table, read 2026-10-18: 0,1,2,3,6,4,5,7,8; the inverse of 0x746570's
 * 0,1,2,3,5,6,4,7,8). -1 for another value. */
static int kpm_slot_pos(int slot)
{
    static const signed char t[9] = { 0, 1, 2, 3, 6, 4, 5, 7, 8 };
    return slot >= 0 && slot < 9 ? t[slot] : -1;
}

/* After a match: which map is next? list[0..n-1] = map indexes; played = the map index just played (-1 unknown). *cursor = matches played.
 * Order (mode 1): when 'played' is on the list the next one is the entry after it (so a first map picked by hand joins the sequence);
 * otherwise the cursor just moves on. Random (mode 2): the cursor moves on. Returns the next map index or -1. */
static int kpm_advance(int mode, const int *list, int n, int *cursor, unsigned seed, int played)
{
    int k;
    if (n <= 0 || n > KPM_MAXMAP || (mode != 1 && mode != 2) || !cursor) return -1;
    if (mode == 1 && played >= 0) {
        for (k = 0; k < n; k++) if (list[k] == played) break;
        if (k < n) *cursor = k + 1; else (*cursor)++;
    } else (*cursor)++;
    if (*cursor < 0 || *cursor > 100000) *cursor = 0;
    return kpm_next(mode, list, n, *cursor, seed);
}

/* the playlist override klslot.c asks (kls_map): for the slot with this name (e.g. "F07") which menu page must the load use? -1 = none. */
static char kpm_ovr_slot[8];
static volatile LONG kpm_ovr_page = -1;
static int kpm_override(const char *slotname)
{
    LONG p = kpm_ovr_page;
    if (p < 0 || !slotname || !kpm_ovr_slot[0] || _stricmp(slotname, kpm_ovr_slot)) return -1;
    return (int)p;
}
static void kpm_ovr_set(const char *slotname, int page)
{
    if (!slotname || page < 0) { InterlockedExchange(&kpm_ovr_page, -1); return; }
    strncpy(kpm_ovr_slot, slotname, sizeof kpm_ovr_slot - 1); kpm_ovr_slot[sizeof kpm_ovr_slot - 1] = 0;
    InterlockedExchange(&kpm_ovr_page, page);
}

/* [Match] Mode text -> 0 off, 1 order, 2 random */
static int kpm_mode_text(const char *s)
{
    if (!s || !s[0]) return 0;
    if (!_stricmp(s, "order") || !_stricmp(s, "sequence") || !strcmp(s, "1")) return 1;
    if (!_stricmp(s, "random") || !strcmp(s, "2")) return 2;
    return 0;
}

/* The Maps= text of [Bundle.N] whose Name= is 'name' (case-insensitive); 0 when there is none. */
static int kpm_bundle_maps(const char *file, const char *name, char *out, int cap)
{
    char sec[16], nm[48]; int i;
    for (i = 1; i <= 16; i++) {
        snprintf(sec, sizeof sec, "Bundle.%d", i);
        GetPrivateProfileStringA(sec, "Name", "", nm, sizeof nm, file);
        if (nm[0] && !_stricmp(nm, name)) { GetPrivateProfileStringA(sec, "Maps", "", out, cap, file); return out[0] != 0; }
    }
    return 0;
}

static int kpm_arc_on, kpm_ini_mode, kpm_list[KPM_MAXMAP], kpm_nlist;

/* ---------------------------------------------------------------- the options (hook side) */

#define KPM_N 3
static const char *const kpm_names[KPM_N] = { "KLMGun", "KLMVote", "KLMPlay" };
static const char *const kpm_keys[KPM_N] = { "Gun", "Vote", "Play" };
static int kpm_on, kpm_log = 1;
static volatile LONG kpm_v[KPM_N];
static int kpm_cursor; static unsigned kpm_seed = 1;

static int kpm_upper(int i)
{
    if (i == 0) return KPM_GUNS;
    if (i == 1) return kpm_nmap;             /* 0 when no maps.ini: only 'no preference' */
    return KPM_NPLAY;
}

static int kpm_which(const char *name)
{   /* -> 0 .. KPM_N-1 for our names, -1 for anything else (or unreadable, or the feature off) */
    char n[12]; int i;
    if (!kpm_on || !name || !klh_rd((DWORD_PTR)name, n, 4) || memcmp(n, "KLM", 3) || n[3] == 'a') return -1;   /* 'KLMask' is klchar.c's */
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n)) return -1;
    for (i = 0; i < KPM_N; i++) if (!strcmp(n, kpm_names[i])) return i;
    return -1;
}

static int kpm_get(int i) { return (int)kpm_v[i]; }

static void kpm_put(int i, int value)
{
    char v[16];
    if (value < 0) value = 0;
    if (value > kpm_upper(i)) value = kpm_upper(i);
    if (InterlockedExchange(&kpm_v[i], value) != value) {
        snprintf(v, sizeof v, "%d", value); WritePrivateProfileStringA("Match", kpm_keys[i], v, klh_ini);
        if (kpm_log) klog("match: menu set %s = %d", kpm_names[i], value);
    }
}

static void kpm_init(void)
{
    char file[MAX_PATH], *s; int i;
    kpm_on = GetPrivateProfileIntA("Match", "Enable", 0, klh_ini) != 0;
    if (!kpm_on) return;
    kpm_log = GetPrivateProfileIntA("Match", "Log", 1, klh_ini);
    GetPrivateProfileStringA("Match", "Maps", "", file, sizeof file, klh_ini);
    if (!file[0] && GetModuleFileNameA(0, file, sizeof file) && (s = strrchr(file, 0x5c)) != 0 && (size_t)(s - file) + 28 < sizeof file)
        strcpy(s + 1, "KLExpansion\\Maps\\maps.ini");
    else if (file[0] && file[1] != ':' && file[0] != 0x5c) {   /* a RELATIVE [Match] Maps: GetPrivateProfile*A would look in the Windows folder, so anchor it at kl2.exe's folder */
        char rel[MAX_PATH]; strcpy(rel, file); file[0] = 0;
        if (GetModuleFileNameA(0, file, sizeof file) && (s = strrchr(file, 0x5c)) != 0 && (size_t)(s - file) + 1 + strlen(rel) < sizeof file) strcpy(s + 1, rel);
        else file[0] = 0;
    }
    if (GetFileAttributesA(file) != INVALID_FILE_ATTRIBUTES) kpm_maps_load(file);
    kpm_cursor = (int)GetPrivateProfileIntA("Match", "Cursor", 0, klh_ini); if (kpm_cursor < 0 || kpm_cursor > 100000) kpm_cursor = 0;   /* kpm_next replays every lap up to the cursor: bound the work */
    kpm_seed = (unsigned)GetPrivateProfileIntA("Match", "Seed", 1, klh_ini);
    if (!kpm_seed) kpm_seed = GetTickCount() | 1;          /* Seed=0: another order each session */
    for (i = 0; i < KPM_N; i++) {
        int v = (int)GetPrivateProfileIntA("Match", kpm_keys[i], 0, klh_ini);
        kpm_v[i] = (v < 0 || v > kpm_upper(i)) ? 0 : v;
    }
    kpm_arc_on = GetPrivateProfileIntA("Match", "Arcade", 1, klh_ini) != 0;
    {   char t[200], b[200];
        GetPrivateProfileStringA("Match", "Mode", "", t, sizeof t, klh_ini); kpm_ini_mode = kpm_mode_text(t);
        GetPrivateProfileStringA("Match", "Playlist", "", t, sizeof t, klh_ini);
        if (!t[0]) { GetPrivateProfileStringA("Match", "Bundle", "", b, sizeof b, klh_ini); if (b[0] && !kpm_bundle_maps(file, b, t, sizeof t)) klog("match: Bundle=%s is not in maps.ini; the playlist is every map", b); }
        kpm_nlist = t[0] ? kpm_parse_list(t, kpm_list, KPM_MAXMAP) : 0;
        if (!kpm_nlist) for (i = 0; i < kpm_nmap; i++) kpm_list[kpm_nlist++] = i;
    }
    klog("match: on; %d maps in maps.ini (%s); Gun=%ld Vote=%ld Play=%ld Cursor=%d Seed=%u; Arcade playlist %s: %d map(s), ini mode %d; the gun and the vote are values only", kpm_nmap, file, kpm_v[0], kpm_v[1], kpm_v[2], kpm_cursor, kpm_seed, kpm_arc_on ? "on" : "off", kpm_nlist, kpm_ini_mode);
}

#endif /* KLPM_C */
