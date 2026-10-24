/*
 * kllocname.c - [Names]: an expansion map that sits in a stock Fragile Alliance slot ([Redirect] / [Redirect.N], klslot.c) shows ITS
 * name where the game prints the slot's title ("Subway" in the FA lobby, the Arcade lists, the filters). Part of KLHook (included by
 * klhook.c after klslot.c, SHIP and TEST alike). Off unless KLHook.ini has [Names] Enable=1. Route A of re\lobby_map_names.md; the static
 * reading (2026-10-24) is section 4 of that file.
 *
 * WHAT THE EXE DOES (read 2026-10-24, kl2.exe 0490, base 0x400000; CERTAIN = disassembly of the named addresses)
 *  - The title of slot k is the .LOC entry  AllLevels / Menu/Online/Scenarios/Title0k  (Title%02i of slot + 1, 0x436762 0x5b6a25 0x62b1a5
 *    0x631995). The GUI element resolves a key that starts with '/' in slot 24 of its vtable (0x490730 for ZMercsShowInfoFAFocus; slot 25
 *    0x4b57c0 tail-jumps to it): `push "AllLevels"; push key+1; call 0x47d8c0`. CERTAIN.
 *  - 0x47d8c0(text, folder): text NULL -> a static empty string; text starting with '%' -> text + 1 (a literal); else
 *        loc = [[[0xdd2640]+0xac]+0x94];  return loc->vtable[0](loc, folder, text, 0)      (0x47d8d5 .. 0x47d8f3)
 *    The same call, with the same three stack arguments, is made by 0x8c3790 (folder "AllLevels/Interface/FACharacters") and 0x67efb2
 *    (klhud_popup.c klpu_loc makes it too); 0x47c2a2 makes it with folder 0 and a third argument 0xb6f2c8 instead of 0.
 *    CALLING CONVENTION: thiscall, `this` in ecx, THREE stack arguments (folder, key, third), callee pops 12, result `const char *` in eax.
 *    It is vtable slot 0 (the old note's 'slot 37' is the GUI element's slot 0x25, not the LOC object's). CERTAIN as a call site; the
 *    callee itself (the class behind [..+0x94]) was not reached statically - this file therefore checks it at run time (see kllnm_pin).
 *  - The result: 0x8c3790 hands it to 0x83e2e0 (a string object made from the pointer = a COPY); 0x47d8c0's other callers return it to
 *    a GUI text which copies it as well (0x490730 returns it up, nothing frees it: the only thing freed there is the folder string).
 *    A missing key is not established. So the result is a pointer into the dictionary that nobody owns or frees.
 *
 * WHAT IT DOES
 *  The object [[[0xdd2640]+0xac]+0x94] gets a private copy of its vtable (the trick klchar.c uses on the option interface): a data write of
 *  the object's first dword, the exe's vtable in .rdata stays as it is, NO code byte of kl2.exe changes and nothing is written inside the
 *  hashed range 0x41e000 .. 0x42a000 (the private vtable is in this DLL's .data, the object is on the heap). Slot 0 of the copy is
 *  kllnm_lookup. For a key whose last part is Title01 .. Title09 under 'Scenarios' (in the key or in the folder), slot k-1 = F0k, it asks
 *  what a load would use NOW - klslot.c's page (kls_page_now(), the Arcade playlist's kpm_override) and the rule table - and, if an
 *  expansion map answers, returns that map's name from a static buffer (stable for the process, so it does not matter whether a caller
 *  copies it). Anything else calls the stock function with the arguments unchanged.
 *  The object is built per scene (the frontend and every level have their own .LOC): the tick installs the copy again whenever the
 *  object shows an exe vtable. One private copy per distinct exe vtable (4 at most).
 *
 *  Names: [Names] <map folder>=<text>   (DM01=Hot Coffee), else the entry title of the page the rule belongs to ([Page.N] F0k=Title,
 *  the one mkoverlay.py puts on the Arcade page), else no override for that rule (the stock name stays).
 *
 * KLHook.ini
 *   [Names]
 *   Enable=0        1 = wrap the LOC lookup (needs [Expansion] Enable=1 and a [Redirect] rule; otherwise nothing is wrapped)
 *   Log=0           1 = one line per distinct (folder,key)->result for keys containing Scenarios/Title (at most 64 lines)
 *   Override=0      1 = answer the expansion map's name; 0 = pass-through that only logs (the first live check)
 *   DM01=Hot Coffee         names, 47 characters at most (printable ASCII); at most 32
 *
 * GUESSES (each also marked where it is used): that vtable slot 0 of the object is that lookup for EVERY LOC object the game makes
 * (kllnm_pin checks the slot's code for a 'ret 0xc'); that the dictionary strings are plain 8-bit text (klpu_str / the HUD read them so);
 * that the lobby asks again when its map changes (menus.md 4.2, not seen); that the slot is the title number (Title0k <-> F0k, 0x464b70+1).
 */
#ifndef KLLOCNAME_C
#define KLLOCNAME_C

#define KLLNM_MAXSLOT 64                        /* slots copied at most (GUESS: a vtable of this class is shorter; the copy stops at the first non-code dword) */
#define KLLNM_NVT     4
#define KLLNM_NAMES   32
#define KLLNM_NAME    48

static int kllnm_on, kllnm_log, kllnm_override;
static struct { DWORD stock; DWORD orig; int n; DWORD vt[KLLNM_MAXSLOT + 1]; } kllnm_tab[KLLNM_NVT];     /* vt[0] = RTTI locator, vt[1..] = slots */
static int kllnm_ntab;
static char kllnm_rname[KLS_RULES][KLLNM_NAME];   /* the display name of each klslot.c rule ("" = none) */
static volatile LONG kllnm_hits;
static DWORD kllnm_seen[96]; static LONG kllnm_nseen, kllnm_nlog;

typedef const char *(__fastcall *KLLNM_LOOKUP)(void *self, void *edx, const char *folder, const char *key, DWORD third);

static void kllnm_say(const char *folder, const char *key, const char *via, const char *res)
{   /* one line per distinct (folder, key, result), 64 lines at most; a log call is a few microseconds, only for Scenarios/Title keys */
    DWORD h = 2166136261u; const char *p; LONG i, n;
    for (p = folder; p && *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    h = (h ^ 0x2f) * 16777619u;
    for (p = key; p && *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    for (p = res; p && *p; p++) h = (h ^ (BYTE)*p) * 16777619u;
    n = kllnm_nseen > 96 ? 96 : kllnm_nseen;
    for (i = 0; i < n; i++) if (kllnm_seen[i] == h) return;
    if (kllnm_nseen >= 96 || kllnm_nlog >= 64) return;
    kllnm_seen[kllnm_nseen++] = h; kllnm_nlog++;
    klog("names: lookup %s / %s -> '%s' (%s)", folder ? folder : "(null)", key, res ? res : "(null)", via);
}

/* -> 1..9 when the folder/key pair names the title of slot F0<n>, else 0 */
static int kllnm_title_slot(const char *folder, const char *key, int klen)
{
    const char *t;
    if (klen < 7) return 0;
    t = key + klen - 7;
    if (memcmp(t, "Title0", 6) || t[6] < '1' || t[6] > '9') return 0;
    if (t > key && t[-1] != '/') return 0;               /* 'xTitle01' is not ours */
    if (t == key) return folder && strstr(folder, "Scenarios") ? t[6] - '0' : 0;
    { const char *sc = strstr(key, "Scenarios"); return sc && sc < t ? t[6] - '0' : 0; }
}

/* the name of the map slot F0<n> loads NOW, or 0 = the stock slot name stays */
static const char *kllnm_name_now(int n)
{
    int s, r, page; char slot[4];
    snprintf(slot, sizeof slot, "F%02d", n);
    for (s = 0; s < kls_nslots && _stricmp(kls_slot[s].name, slot); s++) ;
    if (s == kls_nslots) return 0;
    page = kls_page_now();
    if (!kl_online()) { int o = kpm_override(kls_slot[s].name); if (o >= 0) page = o; }   /* the Arcade playlist's choice, as kls_map does */
    r = kls_find_rule(s, page); if (r < 0 && page) r = kls_find_rule(s, 0);
    return r >= 0 && kllnm_rname[r][0] ? kllnm_rname[r] : 0;
}

static const char *__fastcall kllnm_lookup(void *self, void *edx, const char *folder, const char *key, DWORD third)
{
    KLLNM_LOOKUP orig = 0; DWORD vt; int i, n = 0, klen = 0; char k[96], f[96]; const char *res, *mine = 0; (void)edx;
    vt = klh_rd32((DWORD_PTR)self);
    for (i = 0; i < kllnm_ntab; i++) if (vt == (DWORD)(DWORD_PTR)&kllnm_tab[i].vt[1]) { orig = (KLLNM_LOOKUP)(DWORD_PTR)kllnm_tab[i].orig; break; }
    if (!orig) orig = (KLLNM_LOOKUP)(DWORD_PTR)kllnm_tab[0].orig;         /* cannot happen: only objects given a copy reach this function */
    /* cheap reject first: the key is the game's own C string (read with the same care as klchar.c's option names) */
    if (key && kllnm_on && (klen = klh_rdstr((DWORD_PTR)key, k, sizeof k)) >= 7) {
        f[0] = 0; if (folder) klh_rdstr((DWORD_PTR)folder, f, sizeof f);
        n = kllnm_title_slot(f, k, klen);
    }
    if (!n) return orig(self, 0, folder, key, third);
    if (kllnm_override && (mine = kllnm_name_now(n)) != 0) {
        InterlockedIncrement(&kllnm_hits);
        if (kllnm_log) kllnm_say(f, k, "OVERRIDDEN", mine);
        return mine;
    }
    res = orig(self, 0, folder, key, third);
    if (kllnm_log) {
        char r[96]; r[0] = 0; if (res) klh_rdstr((DWORD_PTR)res, r, sizeof r);
        kllnm_say(f, k, kllnm_override ? "stock: no expansion map in this slot now" : "pass-through, Override=0", r);
    }
    return res;
}

/* a vtable of the exe is only used after the checks that make the slot-0 guess visible in the log */
static int kllnm_pin(DWORD vt, DWORD *slot0, int *nslots)
{
    char kind[9]; DWORD v, f = 0; BYTE code[1024]; int i, n = 0;
    if (!vt || klh_kind((const void *)KLH_VA(vt - 4), 8, kind) != 'r') return 0;               /* a vtable lies in .rdata */
    for (n = 0; n < KLLNM_MAXSLOT; n++) {
        v = klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * n));
        if (!v || klh_kind((const void *)KLH_VA(v), 4, kind) != 'x') break;
        if (!n) f = v;
    }
    if (n < 1) return 0;
    /* REVIEW 2026-10-24: the private copy has exactly n slots; the game reads slots beyond n from zeros = call 0 = crash. So the copy must
       be the WHOLE vtable: refuse when the scan hit the cap, or when it stopped at a NULL slot that has code behind it (a hole, not the end).
       GUESS: the end of a vtable is the next object's RTTI locator (.rdata, not code) or padding. */
    if (n >= KLLNM_MAXSLOT) return 0;
    if (!klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * n)))
        for (i = 1; i <= 4; i++) if (klh_kind((const void *)KLH_VA(klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * (n + i)))), 4, kind) == 'x') return 0;
    /* GUESS: the function is the lookup: it ends in a 'ret 0xc' (c2 0c 00): three stack arguments popped by the callee. A scan of its first
       KB can match another function's tail, so this is a plausibility check, not a proof. */
    if (!klh_rd((DWORD_PTR)KLH_VA(f), code, sizeof code)) return 0;
    for (i = 0; i + 2 < (int)sizeof code; i++) if (code[i] == 0xc2 && code[i + 1] == 0x0c && code[i + 2] == 0x00) break;
    if (i + 2 >= (int)sizeof code) return 0;
    *slot0 = f; *nslots = n;
    return 1;
}

static void kllnm_tick(int game_thread)
{
    static DWORD last; static LONG told_bad, told_ok;
    DWORD now = GetTickCount(), sys, db, loc, vt, s0 = 0, nv; int i, n = 0, t;
    if (!kllnm_on || !game_thread || !klh_exe_ok || now - last < 100) return;       /* the object's first dword is written from the game's own thread only */
    last = now;
    if (!(sys = klh_rd32((DWORD_PTR)KLH_VA(KL2_SYSIF))) || !(db = klh_rd32(sys + 0xac)) || !(loc = klh_rd32(db + 0x94)) || !(vt = klh_rd32(loc))) return;
    for (i = 0; i < kllnm_ntab; i++) if (vt == (DWORD)(DWORD_PTR)&kllnm_tab[i].vt[1]) return;       /* already ours */
    for (t = 0; t < kllnm_ntab && kllnm_tab[t].stock != vt; t++) ;
    if (t == kllnm_ntab) {                                  /* a vtable not seen yet: build the copy */
        if (kllnm_ntab >= KLLNM_NVT) { if (!InterlockedExchange(&told_bad, 1)) klog("names: more than %d different LOC vtables: the lookup is left alone", KLLNM_NVT); return; }
        if (!kllnm_pin(vt, &s0, &n)) {
            if (InterlockedIncrement(&told_bad) <= 3) klog("names: LOC object %08lx has vtable %08lx which does not look like the lookup (not in .rdata, no code in slot 0, or no 'ret 0xc'): left alone", loc, vt);
            return;
        }
        kllnm_tab[t].stock = vt; kllnm_tab[t].orig = s0; kllnm_tab[t].n = n;
        if (!klh_rd((DWORD_PTR)KLH_VA(vt - 4), &kllnm_tab[t].vt[0], 4 * (SIZE_T)(n + 1))) return;
        kllnm_tab[t].vt[1] = (DWORD)(DWORD_PTR)kllnm_lookup;            /* slot 0 */
        kllnm_ntab++;
    }
    nv = (DWORD)(DWORD_PTR)&kllnm_tab[t].vt[1];
    if (klh_data((void *)(DWORD_PTR)loc, &nv, 4, "LOC object vtable (private copy, slot 0 wrapped)") && InterlockedIncrement(&told_ok) <= 6)
        klog("names: LOC object %08lx (stock vtable %08lx, %d slots, slot 0 = %08lx) now answers through the private vtable; Override=%d Log=%d", loc, vt, kllnm_tab[t].n, kllnm_tab[t].orig, kllnm_override, kllnm_log);
}

static void kllnm_init(void)
{
    char val[KLLNM_NAME + 8]; int r, nn = 0;
    if (!GetPrivateProfileIntA("Names", "Enable", 0, klh_ini)) return;
    kllnm_log = GetPrivateProfileIntA("Names", "Log", 0, klh_ini) != 0;
    kllnm_override = GetPrivateProfileIntA("Names", "Override", 0, klh_ini) != 0;
    if (!kls_on) { klog("names: Enable=1 but [Expansion] is off: there is no slot to rename, nothing is wrapped"); return; }
    for (r = 0; r < kls_nrules; r++) {
        char sec[16], key[8];
        kllnm_rname[r][0] = 0;
        GetPrivateProfileStringA("Names", kls_rule[r].map, "", val, sizeof val, klh_ini);
        if (!val[0] && kls_rule[r].page >= 2) {           /* the Arcade page's entry title (mkoverlay.py) for that slot */
            snprintf(sec, sizeof sec, "Page.%d", kls_rule[r].page); snprintf(key, sizeof key, "%s", kls_slot[kls_rule[r].slot].name);
            GetPrivateProfileStringA(sec, key, "", val, sizeof val, klh_ini);
        }
        if (val[0]) {
            char *p; int ok = 1;
            for (p = val; *p; p++) if ((BYTE)*p < 0x20 || (BYTE)*p > 0x7e || *p == '%') ok = 0;      /* GUESS: 8-bit text; plain ASCII only, so no code page question. '%' refused (REVIEW: a GUI text may be a printf format) */
            if (val[0] == '/') ok = 0;                         /* REVIEW GUESS: a leading '/' is a LOC key to the GUI element (0x490730), not a literal */
            if (!ok || strlen(val) >= KLLNM_NAME) { klog("names: the name of %s (%s) is refused: printable ASCII, under %d characters", kls_rule[r].map, val, KLLNM_NAME); continue; }
            memcpy(kllnm_rname[r], val, strlen(val) + 1); nn++;
        }
        if (kllnm_rname[r][0]) klog("names: slot %s page %d -> %s is called '%s'", kls_slot[kls_rule[r].slot].name, kls_rule[r].page, kls_rule[r].map, kllnm_rname[r]);
    }
    kllnm_on = 1;
    klog("names: enabled; %d name(s) for %d rule(s); Override=%d Log=%d (the LOC object is wrapped by the tick; no code of kl2.exe is changed)", nn, kls_nrules, kllnm_override, kllnm_log);
}

#endif /* KLLOCNAME_C */
