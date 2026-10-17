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
 *      The XML entry counts of the menu rows are these ranges (klchar.c section 1, re\wardrobe.md 5a): the overlay page is NOT written yet.
 *   2. maps.ini (GUESS on the format; the file does not exist yet, kpm_maps_load() reads it if present):
 *          [Maps]            Count=3
 *          [Map.1]           Id=DM01   Name=Subway (Dead Men)   Slot=F01
 *          [Bundle.1]        Name=Dead Men classics   Maps=DM01,DM03A,DM05A
 *      Path: [Match] Maps=<file>, default KLExpansion\Maps\maps.ini beside kl2.exe (kl2.exe's folder, which is also the DLL's).
 *   3. Pure functions with an off-game test (klpm_test.c): kpm_tally() (vote count -> map index; ties and 'no preference' by a draw seeded
 *      with the lobby id, so a restart does not re-roll) and kpm_next() (playlist cursor, sequence or random without repeats).
 *
 * NOT DONE (each is a later step of the build order, re\pm_options.md 6):
 *   - the overlay page (mkoverlay.py; the entry 'Match options' in the main menu) - without it the three names are never asked;
 *   - equipping KLMGun: the equip call behind the shop buy (0x7558ce) is not read (B0); this file does not call anything;
 *   - applying a tally / the cursor to Heist_SelectedLevel or MP_SelectedLevel, and every Steam lobby part (B2 .. B5);
 *   - KLMVote's upper bound follows the loaded maps.ini, the XML must have as many entries (GUESS: nobody checks the mismatch).
 *
 * KLHook.ini
 *   [Match]
 *   Enable=0        1 = answer KLMGun / KLMVote / KLMPlay
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
    for (i = 0; i < KPM_N; i++) {
        int v = (int)GetPrivateProfileIntA("Match", kpm_keys[i], 0, klh_ini);
        kpm_v[i] = (v < 0 || v > kpm_upper(i)) ? 0 : v;
    }
    klog("match: on; %d maps in maps.ini (%s); Gun=%ld Vote=%ld Play=%ld Cursor=%d Seed=%u; options only, nothing is applied yet", kpm_nmap, file, kpm_v[0], kpm_v[1], kpm_v[2], kpm_cursor, kpm_seed);
}

#endif /* KLPM_C */
