/*
 * klchar.c - the heister the player chose: body (the eight Dog Days mercenaries and the eight Dead Men heroes),
 * mask and outfit. Part of KLHook (included by klhook.c, SHIP and TEST alike). Heap data writes, one object with
 * a private vtable, and two calls of game functions from the game's own thread; no code byte of kl2.exe changes.
 * Data side: tools\kl_chars.py wardrobe (re\wardrobe.md). SEEN IN THE GAME 2026-10-09 (runs W1 - W6): the options,
 * the body swap to a Dead Men model, a borrowed mask, the outfit variant. NOT SEEN: the value texts of the menu rows
 * (section 1, slot 10), KLWardrobe.ini Version 2 (the 24 outfits, section 3).
 *
 * 1. THREE MENU OPTIONS THE GAME DOES NOT HAVE
 *    A menu widget is bound to an option by NAME (frontend.xml Option="..."), and the names are compiled into
 *    ZMercsOptionsInterface (vtable 0xbb7dec, 15 slots, the object at [0x154d5f4]; re\menus.md 3): an unknown
 *    name reads 0 and is dropped on write. The object is on the heap, so it gets a PRIVATE VTABLE (re\antitamper.md
 *    4.4): a copy of the 15 slots with the RTTI locator in front, four of them wrapped, and its address written
 *    into the object's first dword. The stock vtable in .rdata stays as it is. Wrapped (all __thiscall, names are
 *    plain char *; read from the code 2026-10-09):
 *        slot 2  int  Get(name, player)              0x504b40  ret 8
 *        slot 5  void Set(name, value, player)       0x472450  ret 0xc
 *        slot 9  bool IsEnabled(name, player)        0x4b4560  ret 8
 *    A wrapper answers the three names below itself and passes every other name on unchanged.
 *    NOT wrapped, and it must stay so: slot 10 bool GetBounds(name, &lo, &hi) 0x611be0. Its return value is not
 *    'the bounds are valid' but 'THIS OPTION WRITES ITS OWN VALUE TEXT': the widget keeps it at +0x9b (set-up
 *    0x597a14..0x597a19), and ZToggleText's text update (slot 38, 0x6712b0) then takes the text from slot 6
 *    GetText(name, &string) (0x8b70d0 -> [iface+0x18] = 0x6994c0) instead of from its <Text> children; stock
 *    returns 1 for the eleven options whose values are made at run time only (ids 0x1f, 0x21..0x2c: resolution,
 *    refresh rate ...). The first version of this file wrapped slot 10 and returned 1: slot 6 knows no KL name,
 *    leaves the string empty, and the Heister page showed nothing between the arrows (run W2). With the stock
 *    answer 0 the widget's range is 0 .. <number of Text children> - 1 (0x694500) and child [value] is shown
 *    ('%literal' as written, 0x671375). So the XML's entry counts ARE the ranges: klc_upper below must agree
 *    with mkoverlay.py (it prints the numbers; a value above the XML's count shows no text).
 *        KLChar    0 = whoever the game gives (stock), 1..8 = J.C. Tommy Pierre Liam Jean Elwood Bud Mitchel,
 *                  9..16 = Kane, Lynch, Ashkanan, Meldal, Red, Parker, Standen, Hutchison (Dead Men's FA ranks)
 *        KLMask    0 = as the game's 'Criminal Masks' option says, 1 = no mask, 2..9 = the mask of heister 1..8
 *        KLOutfit  0..23 = armour (0..3) + 4 * shirt (0..1) + 8 * head (0..2): the 24 looks of a Dead Men Fragile
 *                  Alliance hero (= its Dead Men variant - 1); ignored on a Dog Days body, which has one outfit
 *    The values live in this DLL, so they survive the menu's option object (deleted at every scene change,
 *    klslot.c), and in KLHook.ini [Character] Char= Mask= Outfit=, so they survive the game.
 *    The object is created lazily and again for every scene: the tick re-installs the vtable whenever the
 *    object's first dword is the stock 0xbb7dec. ASSUMPTION (antitamper.md): nothing compares that dword with
 *    the stock address. klslot.c's own information line (Log=2) does, and then reads 0.
 *
 * 2. THE BODY (Arcade only)
 *    How the game does it (kl2.exe, read 2026-10-09):
 *      - a model is named by its chunk index in the level's .prm: [[entity+4]+0x68], resolved through the table at
 *        0xeac7b0 wherever it is used (0x6ad0db);
 *      - every heister object enters its model in the rules object at init: ZGameRulesHeist slot 135 (0x5684f0)
 *        stores heroes[rank] = model at rules+0x208 (callers 0x50a1c0, 0x627b50: type [player+0x273c] == 2, rank
 *        [player+0x2740]); rules = [[0x168e9e4]+0x54] while the session mode [[0x168e598]+0x5c] is 4 (0x7bb2a0);
 *      - slot 137 (0x8f5e90, argument = player index) takes the local player [gamedata+0x828+4*(char)[gamedata+
 *        0x898]] (0x660b00), reads the byte rules+0x33d (a random 0..7 from the constructor), and gives the player
 *        that model: 0x783fb0(player, heroes[byte]) = [[player+4]+0x68] = model, notify, rebuild. The AI heister
 *        that wore it gets the player's old model (0x8f5f63..).
 *    So a body swap at run time is the game's own mechanism, and a model is just a number. The hook, each tick,
 *    once rules, the local player and all eight table entries exist and have stood still for Settle ms:
 *        a. heroes[slot] = the chosen character's model   (heap dword; a Dog Days character's is already there)
 *        b. rules+0x33d = slot                            (heap byte)
 *        c. if the player does not wear that model: call slot 137 (rules, 0) - the game's own routine, with its
 *           own swap of the AI heister. Game thread only, at most Tries times a level.
 *    A Dead Men character needs its model in the level: KLWardrobe.ini beside the level archive lists the model
 *    roots of THAT build (written by kl_chars.py wardrobe). Without the file the level has only the stock eight
 *    and their own masks; a Dead Men choice is then ignored and said once.
 *    Slot of a character = whose place in the crew it takes: Kane takes J.C.'s (the AI heister J.C. keeps his own
 *    body, so in a round with Kane there are nine looks and nobody twice).
 *
 * 3. MASK AND OUTFIT
 *    A model's objects carry a variant byte; the entity's variant ([player+0x50], set by 0x88c810, which also
 *    refreshes the model) selects what is drawn. Stock: 1 = face, 2 = the heister's own mask, set by
 *    ZGameRulesHeist slot 34 (0x4b5b20) from the option UseMask. A wardrobe build adds, in every model
 *    (KLWardrobe.ini Version 2; per character Bodies and Heads, 8 and 3 on a Dead Men body, 1 and 1 on a Dog Days one):
 *        outfit  = body + Bodies * head
 *        variant = 10 * body + (1 own face | 2 own mask | 2 + m the mask of heister m, m = 1..8)
 *        variant = HeadBase + Bodies * (head - 1) + body      own face with head 1.. (a mask replaces the head, so
 *                                                             the head choice exists with the own face only)
 *    with 12 masks: step 14, 1..128 (the variant byte is compared unsigned by the renderer, re\pd2_klside.md 5; masks
 *    9..12 are Payday 2 face plates drawn over the character's own head). A Version 1 file (two outfits: Dead Men variants
 *    1 and 4) is still read: armour 3 selects its second outfit, everything else its first.
 *    Each tick the hook compares [player+0x50] with what the choice asks for and calls 0x88c810(player, variant)
 *    when it differs (game thread only). KLMask=0 leaves the game's 1 / 2 alone (and only adds the outfit).
 *    Without KLWardrobe.ini only 1 and 2 exist: 'no mask' = 1, any mask = 2.
 *    The AI heisters keep what the game gives them.
 *
 * NOT DONE: online Fragile Alliance (the body there follows a session number, 0x74ee10, and a look would have to
 * be replicated: stage 4) - the hook does nothing unless the rules object is ZGameRulesHeist (vtable 0xbd3514).
 * The player's NAME in the HUD stays that of the slot (C1..C8). Policemen (type 3) are left alone.
 * The AI heisters keep their Dog Days bodies and looks.
 *
 * KLHook.ini
 *   [Character]
 *   Enable=1        0 = this file does nothing (the three options then read 0 and are dropped, as in stock)
 *   Char=0  Mask=0  Outfit=0      the choice; rewritten when the menu changes it
 *   Settle=300      ms the rules / player / table must have stood still before the hook acts
 *   Tries=3         calls of slot 137 per level at most
 *   Log=1
 */
#ifndef KLCHAR_C
#define KLCHAR_C

#define KLC_OPTIONS     0x0154d5f4            /* ZMercsOptionsInterface * */
#define KLC_OPTIONS_VT  0x00bb7dec
#define KLC_NSLOT       15
#define KLC_SESSION     0x0168e598            /* +0x5c = mode, 4 = Arcade (Heist) */
#define KLC_SETTINGS    0x0168e9e4            /* +0x54 = the rules object */
#define KLC_RULES_VT    0x00bd3514            /* ZGameRulesHeist */
#define KLC_ATTACH      0x008f5e90            /* its slot 137 */
#define KLC_SETVARIANT  0x0088c810
#define KLC_NCHAR       16
#define KLC_MASKS       12                    /* 8 Dog Days heisters' masks + 4 Payday 2 plates (tools\kl_pd2mask.py); a build may have fewer (Masks=) */
#define KLC_OUTFITS     24                    /* KLOutfit 0..23; mkoverlay.py's Outfit row has as many entries */

static int klc_on = 1, klc_log = 1, klc_settle = 300, klc_tries = 3;
static volatile LONG klc_char, klc_mask, klc_outfit;
static DWORD klc_vt[KLC_NSLOT + 1];           /* [0] RTTI locator, [1..] the slots */
static int klc_vt_ready;
static CRITICAL_SECTION klc_cs;
static struct { int on, version, step, masks, headbase, n; struct { DWORD root; int slot, outfits, bodies, heads, stock; char name[32]; } c[KLC_NCHAR]; char key[64], file[MAX_PATH]; } klc_w;

/* ---------------------------------------------------------------- the three options */

static const char *const klc_names[3] = { "KLChar", "KLMask", "KLOutfit" };
static const int klc_upper[3] = { KLC_NCHAR, KLC_MASKS + 1, KLC_OUTFITS - 1 };
static volatile LONG *const klc_value[3] = { &klc_char, &klc_mask, &klc_outfit };
static const char *const klc_keys[3] = { "Char", "Mask", "Outfit" };

static int klc_which(const char *name)
{   /* the game hands a plain C string; anything unreadable is not ours */
    char n[12]; int i;
    if (!name || !klh_rd((DWORD_PTR)name, n, 3) || n[0] != 'K' || n[1] != 'L') return -1;
    if (!klh_rdstr((DWORD_PTR)name, n, sizeof n)) return -1;
    for (i = 0; i < 3; i++) if (!strcmp(n, klc_names[i])) return i;
    return -1;
}

static int __fastcall klc_get(void *self, void *edx, const char *name, int player)
{
    int i = klc_which(name); (void)edx;
    if (i >= 0) return (int)*klc_value[i];
    if ((i = klg_which(name)) >= 0) return klg_get(i);      /* klgun.c: KLGunStart, KLGunSet */
    if ((i = kset_which(name)) >= 0) return kset_get(i);      /* klset.c: the Mod settings rows */
    return ((int (__fastcall *)(void *, void *, const char *, int))(DWORD_PTR)KLH_VA(0x504b40))(self, 0, name, player);
}

static void __fastcall klc_set(void *self, void *edx, const char *name, int value, int player)
{
    int i = klc_which(name); (void)edx;
    if (i >= 0) {
        char v[16];
        if (value < 0) value = 0;
        if (value > klc_upper[i]) value = klc_upper[i];
        if (InterlockedExchange(klc_value[i], value) != value) {
            snprintf(v, sizeof v, "%d", value); WritePrivateProfileStringA("Character", klc_keys[i], v, klh_ini);
            if (klc_log) klog("character: menu set %s = %d", klc_names[i], value);
        }
        return;
    }
    if ((i = klg_which(name)) >= 0) { klg_put(i, value); return; }
    if ((i = kset_which(name)) >= 0) { kset_put(i, value); return; }
    ((void (__fastcall *)(void *, void *, const char *, int, int))(DWORD_PTR)KLH_VA(0x472450))(self, 0, name, value, player);
}

static int __fastcall klc_enabled(void *self, void *edx, const char *name, int player)
{   /* the stock function returns a bool in al; the caller tests al only */
    (void)edx;
    if (klc_which(name) >= 0 || klg_which(name) >= 0 || kset_which(name) >= 0) return 1;
    return ((int (__fastcall *)(void *, void *, const char *, int))(DWORD_PTR)KLH_VA(0x4b4560))(self, 0, name, player);
}

static void klc_options_tick(void)
{   /* give the menu's option object the private vtable whenever it shows the stock one */
    static LONG told; DWORD obj, vt;
    obj = klh_rd32((DWORD_PTR)KLH_VA(KLC_OPTIONS));
    if (!obj || klh_rd32(obj) != KLC_OPTIONS_VT) return;
    if (!klc_vt_ready) {
        static const DWORD stock[4][2] = { { 2, 0x504b40 }, { 5, 0x472450 }, { 9, 0x4b4560 }, { 10, 0x611be0 } };      /* 10: checked, not wrapped */
        int i;
        if (!klh_rd((DWORD_PTR)KLH_VA(KLC_OPTIONS_VT - 4), klc_vt, sizeof klc_vt)) return;
        for (i = 0; i < 4; i++) if (klc_vt[1 + stock[i][0]] != stock[i][1]) {
            if (!InterlockedExchange(&told, 1)) klog("character: slot %lu of the option interface is %08lx, not %08lx: the menu options are off", stock[i][0], klc_vt[1 + stock[i][0]], stock[i][1]);
            return;
        }
        klc_vt[1 + 2] = (DWORD)(DWORD_PTR)klc_get; klc_vt[1 + 5] = (DWORD)(DWORD_PTR)klc_set;
        klc_vt[1 + 9] = (DWORD)(DWORD_PTR)klc_enabled;
        klc_vt_ready = 1;
    }
    vt = (DWORD)(DWORD_PTR)&klc_vt[1];
    if (klh_data((void *)(DWORD_PTR)obj, &vt, 4, "option interface vtable") && klc_log)
        klog("character: option object %08lx now answers KLChar / KLMask / KLOutfit (private vtable)", obj);
}

/* ---------------------------------------------------------------- KLWardrobe.ini of the level */

/* From klsteam.c's klh_level_open: the game opens the level archive <key> ("f01\f01_main.zip") from <opened>. */
static void klc_level_open(const char *key, const char *opened)
{
    char file[MAX_PATH], sec[24], *s; int i, n, ver, ok = 0;
    DWORD len;
    if (!klc_on) return;
    len = GetFullPathNameA(opened, MAX_PATH, file, 0);
    if (!len || len >= MAX_PATH || !(s = strrchr(file, 0x5c)) || (size_t)(s - file) + 16 >= sizeof file) return;
    strcpy(s + 1, "KLWardrobe.ini");
    EnterCriticalSection(&klc_cs);
    memset(&klc_w, 0, sizeof klc_w);
    snprintf(klc_w.key, sizeof klc_w.key, "%s", key); if ((s = strrchr(klc_w.key, '.')) != 0) *s = 0;
    n = (int)GetPrivateProfileIntA("Wardrobe", "Characters", 0, file);
    ver = (int)GetPrivateProfileIntA("Wardrobe", "Version", 0, file);
    if ((ver == 1 || ver == 2) && n > 0 && n <= KLC_NCHAR) {
        klc_w.version = ver;
        klc_w.step = (int)GetPrivateProfileIntA("Wardrobe", "OutfitStep", 10, file);
        klc_w.masks = (int)GetPrivateProfileIntA("Wardrobe", "Masks", KLC_MASKS, file);
        klc_w.headbase = (int)GetPrivateProfileIntA("Wardrobe", "HeadBase", 0, file);
        ok = klc_w.masks >= 1 && klc_w.masks <= KLC_MASKS && klc_w.step >= klc_w.masks + 2;    /* an 8-mask build still works: its last four choices fall back */
        for (i = 0; i < n; i++) {
            int top;
            snprintf(sec, sizeof sec, "Character.%d", i + 1);
            klc_w.c[i].root = GetPrivateProfileIntA(sec, "Root", 0, file);
            klc_w.c[i].slot = (int)GetPrivateProfileIntA(sec, "Slot", -1, file);
            klc_w.c[i].outfits = (int)GetPrivateProfileIntA(sec, "Outfits", 1, file);
            klc_w.c[i].bodies = ver == 1 ? klc_w.c[i].outfits : (int)GetPrivateProfileIntA(sec, "Bodies", 1, file);
            klc_w.c[i].heads = ver == 1 ? 1 : (int)GetPrivateProfileIntA(sec, "Heads", 1, file);
            klc_w.c[i].stock = (int)GetPrivateProfileIntA(sec, "Stock", 0, file);
            GetPrivateProfileStringA(sec, "Name", "?", klc_w.c[i].name, sizeof klc_w.c[i].name, file);
            if (!klc_w.c[i].root || klc_w.c[i].slot < 0 || klc_w.c[i].slot > 7 || klc_w.c[i].bodies < 1 || klc_w.c[i].heads < 1) break;
            /* every variant the formula can give must be a byte, and the head block must lie above the mask blocks */
            top = klc_w.c[i].heads > 1 ? klc_w.headbase + klc_w.c[i].bodies * (klc_w.c[i].heads - 1) - 1 : klc_w.step * (klc_w.c[i].bodies - 1) + 2 + klc_w.masks;
            if (top > 255 || (klc_w.c[i].heads > 1 && klc_w.headbase <= klc_w.step * (klc_w.c[i].bodies - 1) + 2 + klc_w.masks)) break;
        }
        if (i == n && ok) { klc_w.on = 1; klc_w.n = n; strcpy(klc_w.file, file); }
        else klog("character: %s is not usable (entry %d, Masks=%d, OutfitStep=%d, HeadBase=%d): this level has the stock looks only", file, i + 1, klc_w.masks, klc_w.step, klc_w.headbase);
    } else if (ver) klog("character: %s has Version=%d, this hook reads 1 and 2: this level has the stock looks only", file, ver);
    LeaveCriticalSection(&klc_cs);
    if (klc_log) {
        if (klc_w.on) klog("character: level %s has a wardrobe (version %d): %d characters, %d masks (%s)", klc_w.key, klc_w.version, klc_w.n, klc_w.masks, file);
        else klog("character: level %s has no KLWardrobe.ini beside its archive: stock heisters and their own masks only", klc_w.key);
    }
}

/* ---------------------------------------------------------------- the level side */

/* The variant a look has on a wardrobe model (the formula of tools\kl_chars.py variant_of; checked against it for
 * every outfit and mask by the off-game test, re\wardrobe.md 5b). bodies / heads: of the model the player wears;
 * mask: KLMask (0 = keep the game's own 1 / 2, which `cur`, the variant now set, shows). */
static int klc_variant(int version, int step, int headbase, int bodies, int heads, int outfit, int mask, DWORD cur)
{
    int body, head, code;
    /* outfit = body + Bodies * head; a choice the model does not have falls back to its first body / head */
    if (version == 1) { body = (bodies > 1 && outfit % 4 == 3) ? 1 : 0; head = 0; }       /* the old file: its outfit 1 = armour 3 */
    else if (bodies <= 1) { body = 0; head = 0; }                                         /* a Dog Days body */
    else { body = outfit % bodies; head = outfit / bodies; if (head >= heads) head = 0; }
    /* 1 own face, 2 own mask, 2 + m the mask of heister m */
    if (!mask) code = ((!headbase || cur < (DWORD)headbase) && cur % (DWORD)step == 2) ? 2 : 1;
    else code = mask == 1 ? 1 : 1 + mask;
    return (code == 1 && head) ? headbase + bodies * (head - 1) + body : step * body + code;
}

static int klc_same_code(DWORD va, const BYTE *bytes, int n)
{
    BYTE c[16];
    return n <= (int)sizeof c && klh_rd((DWORD_PTR)KLH_VA(va), c, n) && !memcmp(c, bytes, n);
}

static void klc_level_tick(int game_thread)
{
    static DWORD rules0, player0, since, sig0; static int tries, toldmode, toldnodm, toldthread, toldcode; static LONG lastv = -1, lastbody = -1;
    static const BYTE attach_code[9] = { 0x80, 0x7c, 0x24, 0x04, 0xff, 0x53, 0x55, 0x56, 0x57 };        /* 0x8f5e90 cmp byte [esp+4],0xff ; push ebx.. */
    static const BYTE variant_code[10] = { 0x8b, 0x44, 0x24, 0x04, 0x56, 0x8b, 0xf1, 0x89, 0x46, 0x50 };  /* 0x88c810 .. mov [esi+0x50],eax */
    DWORD sm, gs, rules, gd, player, node, model, hero[8], sig, now = GetTickCount(), cur = 0, want_root = 0; BYTE b = 0xff, idx = 0, type = 0, busy = 0;
    int ch = (int)klc_char, mask = (int)klc_mask, outfit = (int)klc_outfit, i, slot = -1, wardrobe, v;
    char key[64], scene[160];
    if (!ch && !mask && !outfit) return;
    if (kl_online()) {                                                      /* local-only look: peers see the stock model; harmless, so it is NOT stopped here (re/netcode_plan.md 2.1), only said once */
        static int toldnet;
        if (!toldnet++) klog("character: a network session: the choice shows on this machine only, peers see the stock model");
    }
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLC_SESSION))) || klh_rd32(sm + 0x5c) != 4) return;                    /* Arcade only */
    if (!(gs = klh_rd32((DWORD_PTR)KLH_VA(KLC_SETTINGS))) || !(rules = klh_rd32(gs + 0x54))) return;
    if (klh_rd32(rules) != KLC_RULES_VT) {
        if (!toldmode++) klog("character: the rules object %08lx has vtable %08lx, not ZGameRulesHeist: nothing is changed", rules, klh_rd32(rules));
        return;
    }
    if (!(gd = klh_rd32((DWORD_PTR)KLH_VA(KL2_GAMEDATA))) || !klh_rd(gd + 0x898, &b, 1) || b == 0xff || (signed char)b < 0 || b > 3) return;
    if (!(player = klh_rd32(gd + 0x828 + 4 * b)) || !(node = klh_rd32(player + 4))) return;
    if (!klh_rd(player + 0x273c, &type, 1) || type != 2 || !klh_rd(player + 0x2723, &busy, 1) || busy) return;     /* a heister, and slot 137 would act on him */
    if (!klh_rd(rules + 0x208, hero, sizeof hero) || !klh_rd(node + 0x68, &model, 4) || !model) return;
    for (i = 0; i < 8; i++) if (!hero[i]) return;                                                           /* the eight are not all registered yet */
    for (sig = rules ^ player, i = 0; i < 8; i++) sig = sig * 31 + hero[i];
    if (rules != rules0 || player != player0) { rules0 = rules; player0 = player; tries = 0; lastv = lastbody = -1; since = now; sig0 = sig; return; }
    if (sig != sig0) { sig0 = sig; since = now; }
    if ((LONG)(now - since) < klc_settle) return;
    if (!klh_scene(scene, sizeof scene) || !klh_level_key(scene, key, sizeof key)) return;
    wardrobe = klc_w.on && !_stricmp(key, klc_w.key);
    if (!klc_same_code(KLC_ATTACH, attach_code, sizeof attach_code) || !klc_same_code(KLC_SETVARIANT, variant_code, sizeof variant_code)) {
        if (!toldcode++) klog("character: the two game routines are not the ones this build knows: nothing is changed");
        return;
    }
    /* ---- the body */
    if (ch >= 1 && ch <= 8) { slot = ch - 1; want_root = wardrobe ? klc_w.c[slot].root : hero[slot]; }
    else if (ch > 8 && ch <= KLC_NCHAR) {
        if (wardrobe && ch <= klc_w.n && !klc_w.c[ch - 1].stock) { slot = klc_w.c[ch - 1].slot; want_root = klc_w.c[ch - 1].root; }
        else if (!toldnodm++) klog("character: KLChar=%d is a Dead Men body and level %s has no wardrobe: the game's own choice stays", ch, key);
    }
    if (slot >= 0) {
        if (hero[slot] != want_root && klh_data((void *)(DWORD_PTR)(rules + 0x208 + 4 * slot), &want_root, 4, "heister model table")) {
            if (klc_log) klog("character: heister table entry %d: model %lu -> %lu (%s)", slot, hero[slot], want_root, wardrobe ? klc_w.c[ch - 1].name : "stock");
            hero[slot] = want_root;                           /* our own change does not restart the wait */
            for (sig0 = rules ^ player, i = 0; i < 8; i++) sig0 = sig0 * 31 + hero[i];
        }
        idx = (BYTE)slot;
        if (klh_rd(rules + 0x33d, &b, 1) && b != idx) klh_data((void *)(DWORD_PTR)(rules + 0x33d), &idx, 1, "Arcade heister index");
        if (model != want_root) {
            if (!game_thread) { if (!toldthread++) klog("character: the tick is not on the game's thread ([KLHook] Tick=0?): the body cannot be changed"); }
            else if (tries < klc_tries) {
                tries++;
                ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLC_ATTACH))((void *)(DWORD_PTR)rules, 0, 0);
                klh_rd(node + 0x68, &cur, 4);
                klog("character: body: slot %d, model %lu -> %lu asked through the game's own routine (try %d): the player now has %lu%s", slot, model, want_root, tries, cur, cur == want_root ? "" : " - NOT taken");
                model = cur;
            }
        } else if (InterlockedExchange(&lastbody, (LONG)want_root) != (LONG)want_root && klc_log) klog("character: the player wears model %lu (slot %d)", want_root, slot);
    }
    /* ---- mask and outfit: the variant of the model the player wears now */
    if (!wardrobe) { if (!mask) return; v = mask == 1 ? 1 : 2; }
    else {
        for (i = 0; i < klc_w.n && klc_w.c[i].root != model; i++) ;       /* whose model does the player wear now? */
        if (i == klc_w.n) return;                             /* not a wardrobe model (a policeman's, another build's): leave it */
        if (!klh_rd(player + 0x50, &cur, 4)) return;
        if (mask >= 2 && mask - 1 > klc_w.masks) {               /* a mask this build does not have (an 8-mask build, KLMask 10..13): no mask */
            static int toldmask; if (!toldmask++) klog("character: KLMask=%d asks for mask %d and level %s has %d: no mask instead", mask, mask - 1, key, klc_w.masks);
            mask = 1;
        }
        v = klc_variant(klc_w.version, klc_w.step, klc_w.headbase, klc_w.c[i].bodies, klc_w.c[i].heads, outfit, mask, cur);
    }
    if (!klh_rd(player + 0x50, &cur, 4) || cur == (DWORD)v) return;
    if (!game_thread) { if (!toldthread++) klog("character: the tick is not on the game's thread ([KLHook] Tick=0?): the look cannot be changed"); return; }
    ((void (__fastcall *)(void *, void *, int))(DWORD_PTR)KLH_VA(KLC_SETVARIANT))((void *)(DWORD_PTR)player, 0, v);
    if (InterlockedExchange(&lastv, v) != v && klc_log) klog("character: look: variant %lu -> %d (mask choice %d, outfit %d) on model %lu", cur, v, mask, outfit, model);
}

static void klc_tick(int game_thread)
{
    if (!klc_on || !klh_exe_ok) return;
    klc_options_tick();
    klc_level_tick(game_thread);
}

static void klc_init(void)
{
    InitializeCriticalSection(&klc_cs);
    klc_on = GetPrivateProfileIntA("Character", "Enable", 1, klh_ini);
    klc_log = GetPrivateProfileIntA("Character", "Log", 1, klh_ini);
    klc_settle = GetPrivateProfileIntA("Character", "Settle", 300, klh_ini);
    klc_tries = GetPrivateProfileIntA("Character", "Tries", 3, klh_ini);
    klc_char = (LONG)GetPrivateProfileIntA("Character", "Char", 0, klh_ini); if (klc_char < 0 || klc_char > KLC_NCHAR) klc_char = 0;
    klc_mask = (LONG)GetPrivateProfileIntA("Character", "Mask", 0, klh_ini); if (klc_mask < 0 || klc_mask > KLC_MASKS + 1) klc_mask = 0;
    klc_outfit = (LONG)GetPrivateProfileIntA("Character", "Outfit", 0, klh_ini); if (klc_outfit < 0 || klc_outfit >= KLC_OUTFITS) klc_outfit = 0;
    if (klc_on) klog("character: on; choice Char=%ld Mask=%ld Outfit=%ld (0 = the game's own); Settle=%d Tries=%d", klc_char, klc_mask, klc_outfit, klc_settle, klc_tries);
}

#endif /* KLCHAR_C */
