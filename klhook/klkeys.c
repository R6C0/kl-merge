/*
 * klkeys.c - ONE PLACE FOR THE MOD'S KEYS (2026-10-28, track T1 "not a secret feature"; NOT RUN IN THE GAME).
 *
 * Every mod feature that reads a key used to carry its own default: F7 was Unstick AND the host's map set AND ReShade's previous preset, F8 the Inv shelf AND the host's
 * AI toggle AND ReShade's next preset, F10 ReShade's Uplift switch, and the CopSquad keys F / G were Dog Days' own melee / grenade keys. This file holds the table of those keys
 * (defaults old and new), resolves them ONCE, checks them for clashes at boot, names them for the shop's MOD CONTROLS page (klshoppage.c) and for the hint line.
 *
 * RESOLUTION (klkeys_vk / klkeys_ctl), first hit wins:
 *   1. the module's own key line in KLHook.ini, if it is there and not empty (e.g. [Unstick] Key=0x76, [HostOpts] KeyMap=F3)   - old ini files keep working
 *   2. [Keys] <Name>=...                                                                                                      - the one place to rebind
 *   3. the default: the OLD one (what v82 shipped), or with [Keys] Map=1 the NEW clash-free one (recommended on once benched)
 * A key is written as a hex / decimal virtual-key code (0x76, 118), a name (F7, End, PageUp, Delete, Num1, A) and may start with "Ctrl+" (Ctrl+F3). 0 / "none" = no key.
 * (The module lines used GetPrivateProfileIntA, which reads "0x46" as 0: with this file a hex line works.)
 *
 * THE NEW MAP ([Keys] Map=1), every key checked against the ones in this table, ReShade.ini and Dog Days' own binds:
 *   Unstick End | Inv shelf PageUp | CopSquad follow / hold / attack Num1 / Num2 / Num3 | HostOpts map Ctrl+F3, AI Ctrl+F4, pool Ctrl+Delete | MOD CONTROLS page F2
 *   unchanged: F5 UCC ping, F6 shop page II, F9 heister, F11 mask, F12 hire page (Steam's screenshot key is F12 too: a screenshot is taken with it, [Hire] PageKey= moves it), Insert reveal,
 *   J sabotage, G grenade (the Dead Men grenade key IS the stock grenade key: Dog Days leaves the button dead, klgrenade.c wakes it).
 *   Host keys with Ctrl: there is no reliable 'lobby / before the round' read for the three host keys (klhostopt.c polls them in a round too), so they need Ctrl held: a key pressed
 *   while playing never changes the match by accident. (GUESS: Dog Days binds no F-key; the game's stock binds are only the ones in klkeys_stock below.)
 * Map=1 puts CopSquad on the NUMPAD keys: NumLock must be ON (with it off the keys send End / Down / PageDown and the squad commands do nothing; End is Unstick's key then).
 * Only the three host keys take Ctrl (klhostopt.c); a "Ctrl+" on any other key is ignored with a log line. A module line in KLHook.ini beats [Keys]: the sample ini has them commented.
 * [Keys] ControlsPage=1 turns the shop's MOD CONTROLS page + the page-cycle key on, Hints=1 the on-screen hints, ClashLog=1 the boot check. All default 0 (recommended on once benched).
 *
 * WIRING: klhook.c #include "klkeys.c" right after klmem.c (before every module that reads a key); klkeys_check() in the init block after the module inits.
 */
#ifndef KLKEYS_C
#define KLKEYS_C

enum { KK_UNSTICK, KK_INV, KK_COPF, KK_COPH, KK_COPA, KK_SAB, KK_REVEAL, KK_GREN,          /* ids 0..15 = the MOD CONTROLS page's rows 0..15 (IN ROUND, then HOST + ONLINE) */
       KK_HMAP, KK_HAI, KK_HPOOL, KK_CHAR, KK_MASK, KK_HIRE, KK_PAGE2, KK_UPING,
       KK_CYCLE,                                                                           /* the page-cycle key: no row of its own (the caption names it) */
       KK_N, KK_ROWS = KK_CYCLE };

static const struct klkeys_def {
    const char *name;                    /* [Keys] <name>= */
    const char *label;                   /* the page's row title */
    const char *sec, *key;               /* the module's own ini line */
    short oldVk, newVk, newCtl;          /* default before / with Map=1; newCtl: Ctrl must be held */
    short stockOk;                       /* the feature uses the stock bind on purpose (not a clash) */
    const char *scope;                   /* where it works */
    const char *desc;
} klkeys_def[KK_N] = {
    { "Unstick",   "UNSTICK",          "Unstick",   "Key",        0x76, 0x23, 0, 0, "Arcade",                   "Put me back at the last place I walked to freely when I am stuck inside an object in cover." },
    { "Inv",       "GUN SHELF",        "Inv",       "Key",        0x77, 0x21, 0, 0, "Arcade",                   "A third gun: swaps the gun in hand with the one on the shelf." },
    { "CopFollow", "COP SQUAD FOLLOW", "CopSquad",  "KeyFollow",  0x46, 0x61, 0, 0, "Cops and Robbers",         "Police AI under you: follow me." },
    { "CopHold",   "COP SQUAD HOLD",   "CopSquad",  "KeyHold",    0x47, 0x62, 0, 0, "Cops and Robbers",         "Police AI under you: hold where they stand." },
    { "CopAttack", "COP SQUAD ATTACK", "CopSquad",  "KeyAttack",  0x48, 0x63, 0, 0, "Cops and Robbers",         "Police AI under you: attack what I aim at." },
    { "Sabotage",  "HOLD THE VAN",     "Sabotage",  "Key",        0x4a, 0x4a, 0, 0, "Online, host cop",         "Undercover cop (the host): hold the escape van for a few seconds." },
    { "Reveal",    "REVEAL (UCC)",     "Ucc",       "RevealKey",  0x2d, 0x2d, 0, 0, "Arcade and online",        "Undercover cop: show yourself as police (hidden cop mode)." },
    { "Grenade",   "GRENADE THROW",    "Grenade",   "Key",        0x47, 0x47, 0, 1, "Arcade",                   "Throw a Dead Men grenade you carry (the stock grenade key)." },
    { "HostMap",   "HOST: MAP SET",    "HostOpts",  "KeyMap",     0x76, 0x72, 1, 0, "Online host",              "Cycle the map set: Dog Days, Dead Men, both." },
    { "HostAI",    "HOST: AI HEISTERS","HostOpts",  "KeyAI",      0x77, 0x73, 1, 0, "Online host",              "AI heisters fill the empty seats: on or off." },
    { "HostPool",  "HOST: MAP POOL",   "HostOpts",  "KeyPool",    0x2e, 0x2e, 1, 0, "Online host",              "Cycle the random map pool (needs the map pool on)." },
    { "Char",      "HEISTER SELECT",   "CharOnline","KeyChar",    0x78, 0x78, 0, 0, "Online",                   "Pick your heister, seen on every peer. Shift = previous." },
    { "Mask",      "MASK SELECT",      "CharOnline","KeyMask",    0x7a, 0x7a, 0, 0, "Online",                   "Pick your mask, seen on every peer. Ctrl = outfit, Shift = previous." },
    { "Hire",      "HIRE PAGE",        "Hire",      "PageKey",    0x7b, 0x7b, 0, 0, "Arcade and online",        "In the Buy Weapons shop: hire a heister for the next round. F12 is Steam's screenshot key too." },
    { "Page2",     "SHOP PAGE II",     "ShopPage",  "Key",        0x75, 0x75, 0, 0, "Arcade (view online)",     "In the Buy Weapons shop: the extra guns of page II." },
    { "UccPing",   "UCC PING / ACCUSE","Ucc",       "Key",        0x74, 0x74, 0, 0, "Online",                   "Cop: ping the heister you aim at as suspicious. Heister: accuse the one you suspect." },
    { "PageKey",   "NEXT SHOP PAGE",   "Keys",      "PageKey",    0x71, 0x71, 0, 0, "Arcade and online",        "In the Buy Weapons shop: next page (page II, hire, mod controls)." },
};

static struct {
    int done, map, page, hints, clash;                   /* [Keys] Map / ControlsPage / Hints / ClashLog */
    int vk[KK_N], ctl[KK_N], src[KK_N];                  /* resolved; src 0 = default, 1 = module line, 2 = [Keys] line */
    DWORD onAt; int on[KK_N];                            /* the live ON/OFF of each feature (klkeys_on), cached 2 s */
} klkeys;

/* ---- key names ---- */
static const struct { const char *n; int vk; } klkeys_nm[] = {
    { "Backspace", 8 }, { "Tab", 9 }, { "Enter", 13 }, { "Pause", 0x13 }, { "Esc", 27 }, { "Space", 32 }, { "PageUp", 33 }, { "PageDown", 34 }, { "End", 35 }, { "Home", 36 },
    { "Left", 37 }, { "Up", 38 }, { "Right", 39 }, { "Down", 40 }, { "PrintScreen", 44 }, { "Insert", 45 }, { "Delete", 46 }, { "CapsLock", 0x14 }, { "NumLock", 0x90 }, { "ScrollLock", 0x91 },
    { "Num*", 0x6a }, { "Num+", 0x6b }, { "Num-", 0x6d }, { "Num.", 0x6e }, { "Num/", 0x6f }, { ";", 0xba }, { "=", 0xbb }, { ",", 0xbc }, { "-", 0xbd }, { ".", 0xbe }, { "/", 0xbf },
    { "`", 0xc0 }, { "[", 0xdb }, { "\\", 0xdc }, { "]", 0xdd }, { "'", 0xde }, { "Mouse4", 5 }, { "Mouse5", 6 }, { "MouseMiddle", 4 },
};

static void klkeys_name(int vk, int ctl, char *o, size_t cap)
{
    const char *pre = ctl ? "Ctrl+" : ""; int i;
    if (vk <= 0) snprintf(o, cap, "none");
    else if (vk >= 0x70 && vk <= 0x87) snprintf(o, cap, "%sF%d", pre, vk - 0x6f);
    else if (vk >= 0x60 && vk <= 0x69) snprintf(o, cap, "%sNum%d", pre, vk - 0x60);
    else if ((vk >= '0' && vk <= '9') || (vk >= 'A' && vk <= 'Z')) snprintf(o, cap, "%s%c", pre, vk);
    else {
        for (i = 0; i < (int)(sizeof klkeys_nm / sizeof klkeys_nm[0]); i++) if (klkeys_nm[i].vk == vk) { snprintf(o, cap, "%s%s", pre, klkeys_nm[i].n); return; }
        snprintf(o, cap, "%skey %02X", pre, vk);
    }
}

/* "Ctrl+F3" / "0x76" / "118" / "End" / "A" / "0" / "none" -> 1 = parsed (vk 0 = no key). Trailing "; comment" ignored. */
static int klkeys_parse(const char *s, int *vk, int *ctl)
{
    char b[40]; size_t n = 0; char *e; int i; long v;
    *ctl = 0; *vk = 0;
    while (*s == ' ' || *s == '\t') s++;
    while (*s && *s != ';' && n < sizeof b - 1) b[n++] = *s++;
    while (n && (b[n - 1] == ' ' || b[n - 1] == '\t' || b[n - 1] == '\r')) n--;
    b[n] = 0;
    if (!n) return 0;
    if (!_strnicmp(b, "ctrl+", 5)) { *ctl = 1; memmove(b, b + 5, n - 4); }
    if (!_stricmp(b, "none")) return 1;
    if ((b[0] == 'F' || b[0] == 'f') && b[1] >= '1' && b[1] <= '9') { v = strtol(b + 1, &e, 10); if (!*e && v >= 1 && v <= 24) { *vk = (int)v + 0x6f; return 1; } }
    if (!_strnicmp(b, "num", 3) && b[3] >= '0' && b[3] <= '9' && !b[4]) { *vk = 0x60 + (b[3] - '0'); return 1; }
    if (b[0] && !b[1] && ((b[0] >= 'a' && b[0] <= 'z') || (b[0] >= 'A' && b[0] <= 'Z'))) { *vk = b[0] & ~0x20; return 1; }
    for (i = 0; i < (int)(sizeof klkeys_nm / sizeof klkeys_nm[0]); i++) if (!_stricmp(b, klkeys_nm[i].n)) { *vk = klkeys_nm[i].vk; return 1; }
    v = strtol(b, &e, 0);
    if (e != b && !*e && v >= 0 && v <= 0xfe) { *vk = (int)v; return 1; }
    return 0;
}

static int klkeys_ini_key(const char *sec, const char *key, int *vk, int *ctl)
{
    char b[48]; GetPrivateProfileStringA(sec, key, "", b, sizeof b, klh_ini);
    return b[0] && klkeys_parse(b, vk, ctl);
}

/* [Keys] <name>= as a plain virtual-key code with a default (the call the task names): a module that wants its own key line in [Keys] asks this */
static int klkeys_get(const char *name, int def_vk)
{
    int vk, ctl; return klkeys_ini_key("Keys", name, &vk, &ctl) ? vk : def_vk;
}

static void klkeys_init(void)
{
    int i;
    if (klkeys.done) return;
    klkeys.done = 1;
    klkeys.map = GetPrivateProfileIntA("Keys", "Map", 0, klh_ini) != 0;                 /* (recommended on once benched) the clash-free map above */
    klkeys.page = GetPrivateProfileIntA("Keys", "ControlsPage", 0, klh_ini) != 0;       /* (recommended on once benched) MOD CONTROLS shop page + page-cycle key */
    klkeys.hints = GetPrivateProfileIntA("Keys", "Hints", 0, klh_ini) != 0;             /* (recommended on once benched) on-screen hint when the shop opens */
    klkeys.clash = GetPrivateProfileIntA("Keys", "ClashLog", 0, klh_ini) != 0;          /* (recommended on once benched) boot clash check, one WARN per clash */
    for (i = 0; i < KK_N; i++) {
        const struct klkeys_def *d = &klkeys_def[i]; int vk, ctl;
        klkeys.src[i] = 0;
        if (i != KK_CYCLE && klkeys_ini_key(d->sec, d->key, &vk, &ctl)) klkeys.src[i] = 1;
        else if (klkeys_ini_key("Keys", d->name, &vk, &ctl)) klkeys.src[i] = 2;
        else if (klkeys.map) { vk = d->newVk; ctl = d->newCtl; }
        else { vk = d->oldVk; ctl = 0; }
        if (ctl && i != KK_HMAP && i != KK_HAI && i != KK_HPOOL) {     /* review 10-28: only klhostopt.c tests Ctrl; the other modules read the bare key, so a Ctrl+ here would be shown and not honoured */
            klog("keys: Ctrl+ ignored for %s (only the three host keys take Ctrl): the bare key is used", d->label); ctl = 0;
        }
        klkeys.vk[i] = vk; klkeys.ctl[i] = ctl;
    }
}
static int klkeys_vk(int id) { klkeys_init(); return id >= 0 && id < KK_N ? klkeys.vk[id] : 0; }
static int klkeys_ctl(int id) { klkeys_init(); return id >= 0 && id < KK_N ? klkeys.ctl[id] : 0; }
static int klkeys_page_on(void) { klkeys_init(); return klkeys.page; }
static int klkeys_hints_on(void) { klkeys_init(); return klkeys.hints; }

/* is the feature switched on in the ini RIGHT NOW (read again every 2 s: the host options and Mod Options write the file while the game runs) */
static int klkeys_on_ini(int id)
{
#define KKE(s, k, d) (GetPrivateProfileIntA(s, k, d, klh_ini) != 0)
    switch (id) {
    case KK_UNSTICK: return KKE("Unstick", "Enable", 1);
    case KK_INV:     return KKE("Inv", "Enable", 0);
    case KK_COPF: case KK_COPH: case KK_COPA: return KKE("CopSquad", "Enable", 0);
    case KK_SAB:     return KKE("Sabotage", "VanHold", 0);
    case KK_REVEAL:  return KKE("Ucc", "Hide", 0);
    case KK_GREN:    return KKE("Grenade", "Throw", 0);
    case KK_HMAP: case KK_HAI: return KKE("HostOpts", "Enable", 0) && KKE("HostOpts", "Keys", 1);
    case KK_HPOOL:   return KKE("HostOpts", "Enable", 0) && KKE("HostOpts", "Keys", 1) && KKE("MapPool", "Enable", 0);
    case KK_CHAR: case KK_MASK: return KKE("CharOnline", "Enable", 0);
    case KK_HIRE:    return KKE("Hire", "Enable", 0) && KKE("Hire", "Page", 0);
    case KK_PAGE2:   return KKE("ShopPage", "Enable", 0);
    case KK_UPING:   return KKE("Ucc", "Pings", 0) || KKE("Ucc", "Accuse", 0);
    case KK_CYCLE:   return KKE("Keys", "ControlsPage", 0);
    }
#undef KKE
    return 0;
}
static int klkeys_on(int id)
{
    DWORD now = GetTickCount(); int i;
    if (!klkeys.onAt || now - klkeys.onAt > 2000) { klkeys.onAt = now | 1; for (i = 0; i < KK_N; i++) klkeys.on[i] = klkeys_on_ini(i); }
    return id >= 0 && id < KK_N ? klkeys.on[id] : 0;
}

/* ---- boot clash check ---- */
/* Dog Days' own keyboard binds: GUESS beyond F / G (melee / grenade, VERIFIED by the owner's 10-27 note) - the usual third-person set; a mod key on one of them (without Ctrl) is warned */
static const struct { int vk; const char *what; } klkeys_stock[] = {
    { 'F', "melee" }, { 'G', "grenade" }, { 'E', "use / climb" }, { 'R', "reload" }, { 'Q', "cover swap" }, { 'C', "crouch / cover" }, { 'V', "voice" }, { 0x09, "scoreboard" }, { 0x20, "jump / vault" },
};

static void klkeys_check_now(void)
{
    int i, j, nc = 0, nr = 0, nfeat = 0; char a[24], b[24], nm[64];
    struct { int vk, ctl; char what[48]; } rs[48]; int nrs = 0;
    klkeys_init();
    if (!klkeys.clash) return;
    {   /* ReShade.ini (read only): every line whose name holds 'Key' is a shortcut: vk[,ctrl,shift,alt] (PresetShortcutKeys: groups of four) */
        static char secs[16384]; char path[MAX_PATH], *s;
        snprintf(path, sizeof path, "%s\\ReShade.ini", dir);
        if (GetFileAttributesA(path) != INVALID_FILE_ATTRIBUTES) {
            GetPrivateProfileSectionNamesA(secs, sizeof secs, path);
            for (s = secs; *s && nrs < 44; s += strlen(s) + 1) {
                static char sec[16384]; char *l; DWORD n = GetPrivateProfileSectionA(s, sec, sizeof sec, path);
                (void)n;
                for (l = sec; *l && nrs < 44; ) {
                    char *eq = strchr(l, '='), *line = l; int v[16], nv = 0, step; char *p;
                    l += strlen(l) + 1;                                           /* the next line first: the name is cut at '=' below */
                    if (!eq || !strstr(line, "Key") || strstr(line, "Keyboard")) continue;
                    *eq = 0; p = eq + 1;
                    while (*p && nv < 16) { v[nv++] = atoi(p); while (*p && *p != ',') p++; if (*p == ',') p++; }
                    step = strstr(line, "ShortcutKeys") ? 4 : nv >= 4 ? 4 : 1;
                    for (i = 0; i < nv && nrs < 44; i += step) {
                        if (step == 4 && i + 3 < nv && (v[i + 2] || v[i + 3])) continue;      /* a Shift / Alt shortcut is another key from ours (the mod keys use neither) */
                        if (v[i] > 0 && v[i] < 0xff) { rs[nrs].vk = v[i]; rs[nrs].ctl = step == 4 && i + 1 < nv ? v[i + 1] != 0 : 0; snprintf(rs[nrs].what, sizeof rs[nrs].what, "ReShade.ini [%s] %s", s, line); nrs++; }
                    }
                }
            }
        } else klog("keys: no ReShade.ini beside the game: its shortcuts are not checked");
    }
    for (i = 0; i < KK_N; i++) {
        if (!klkeys_on(i) || klkeys.vk[i] <= 0) continue;
        nfeat++;
        klkeys_name(klkeys.vk[i], klkeys.ctl[i], a, sizeof a);
        for (j = i + 1; j < KK_N; j++) {                                           /* two enabled features on one key */
            if (!klkeys_on(j) || klkeys.vk[j] != klkeys.vk[i] || klkeys.ctl[j] != klkeys.ctl[i]) continue;
            if (klkeys_def[i].stockOk && klkeys_def[j].stockOk) continue;
            klog("keys: WARN CLASH %s and %s both use %s: set [Keys] %s= or %s= (or Map=1)", klkeys_def[i].label, klkeys_def[j].label, a, klkeys_def[i].name, klkeys_def[j].name); nc++;
        }
        if (!klkeys.ctl[i] && !klkeys_def[i].stockOk)                              /* a stock bind */
            for (j = 0; j < (int)(sizeof klkeys_stock / sizeof klkeys_stock[0]); j++)
                if (klkeys_stock[j].vk == klkeys.vk[i]) { klog("keys: WARN CLASH %s uses %s, the game's own '%s' key: [Keys] %s= moves it (CopSquad F/G = melee / grenade, 10-27)", klkeys_def[i].label, a, klkeys_stock[j].what, klkeys_def[i].name); nc++; }
        for (j = 0; j < nrs; j++)                                                  /* ReShade.ini shortcuts */
            if (rs[j].vk == klkeys.vk[i] && rs[j].ctl == klkeys.ctl[i]) { klkeys_name(rs[j].vk, rs[j].ctl, b, sizeof b); klog("keys: WARN CLASH %s uses %s, %s (ReShade.ini is read only: move the mod key, [Keys] %s=)", klkeys_def[i].label, a, rs[j].what, klkeys_def[i].name); nc++; nr++; }
        if (klkeys.vk[i] == 0x7b && !klkeys.ctl[i]) klog("keys: note: %s is on F12, Steam's screenshot key (a screenshot is taken too; [Hire] PageKey= or [Keys] Hire= moves it)", klkeys_def[i].label);
    }
    snprintf(nm, sizeof nm, "%s", klkeys.map ? "Map=1 (clash-free keys)" : "Map=0 (old keys)");
    klog("keys: %s, %d enabled keyed feature(s), %d clash(es) (%d with ReShade.ini)%s", nm, nfeat, nc, nr, klkeys.page ? ", MOD CONTROLS page on" : "");
}

/* the check reads ReShade.ini (file I/O): never under DllMain's loader lock. A thread started there waits for the lock, then sleeps until the modules have read their keys. */
static DWORD WINAPI klkeys_check_thread(LPVOID p) { (void)p; Sleep(8000); klkeys_check_now(); return 0; }
static void klkeys_check(void)
{
    klkeys_init();
    if (klkeys.clash) { HANDLE h = CreateThread(0, 0, klkeys_check_thread, 0, 0, 0); if (h) CloseHandle(h); }
}

#endif /* KLKEYS_C */
