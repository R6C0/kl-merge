/*
 * klshop.c - MORE GUNS IN THE FRAGILE ALLIANCE WEAPON SHOP, by SWAPPING WHAT A BOUGHT ROW HANDS OVER (re\shop_more_guns.md, 2026-10-19).
 * Part of KLHook (included by klhook.c after klinv.c; Arcade only, inert online). Off unless KLHook.ini [Shop] Enable=1 and Swap= is set.
 * NOTHING HERE HAS RUN IN THE GAME. DATA writes and ONE call of the game's own object maker on the game thread; NO code byte, no hashed byte.
 *
 * WHY NOT NEW ROWS (CERTAIN, read in kl2.exe): the shop is 36 rows x 24 bytes at 0xbd1f68 (hashed .rdata, klranges.h); the builder 0x78a8d0 loops
 *   exactly that table, the buy is RMCBuyWeaponPack(primaryRow, secondaryRow) and the server and the loadout (0x6a5260, 0x410710) index the
 *   same hashed table by a ROW BYTE. A 37th row would be read from the armour table behind it. A private vtable does not help: the readers are
 *   plain code on the table. So the number of ROWS cannot grow; what a row HANDS OVER can change.
 * WHAT THIS DOES (static reading): the loadout gives table[row].item through 0x538ec0 -> 0x55bee0, which searches the WEAPON POOL ([0x168e96c] ->
 *   [w] -> vector {+4 count, +8 cap, +0xc grow, +0x10 array of 12-byte {object, item, byte+8 free, byte+9 dropped}}) for a free object LABELLED
 *   with that item, and takes ammo / handling from the OBJECT. The label is used only for that search. So for a pair "row:item":
 *     1. the stock entries of the carrier row's item are PARKED (free byte +8 := 0; the game rebuilds the pool every round, so nothing is put back);
 *     2. the game's own maker 0x710ad0 (this = [[0xdd265c]+0x15b0], args 0, template of <item> from 0x5d2f50) makes 8 objects of the extra gun;
 *     3. they are appended to the pool with the carrier's label, exactly as the builder does (count, cap, realloc through IAT 0xb10328).
 *   Buying the carrier row then gives the extra gun at the carrier row's price; the owner SEES the carrier row's name and picture (text and
 *   pictures are baked: tools\kl_shop_extra.py prints what to rename). It is a REPLACEMENT per row, never an extra row. Several pairs: Swap=28:40,29:41.
 *   Gate: Arcade (session +0x5c == 4), rules ZGameRulesHeist, kl_online() == 0, state < 0x19 (before the round), template of the item exists,
 *   the carrier's stock objects are in the pool (builder has run). Re-done when none of our objects is in the pool any more (new round).
 *
 * KLHook.ini
 *   [Shop]
 *   Enable=0       1 = on (Arcade only)
 *   Swap=          comma list "row:item" - row 0..35 of re\shop_plan.md, item = eFF2Item value 1..63 (tools\kl_shop_extra.py lists the usable ones)
 *   (no Log key: the module always logs)
 *
 * CERTAIN: the pool layout, the builder's append recipe (0x78aa14..0x78aa86), the maker's call shape (ret 8, this in ecx), template lookup 0x5d2f50.
 * GUESS: (1) the extra gun's HANDLING CLIPS must exist in the criminal animation sets (else broken / T-pose arms); (2) the inventory needs
 *   a binding for the item (a missing one may stop the pick-up, the log will show nothing); (3) the 0x753150 call after each item in the builder
 *   (probably net spawn bookkeeping) is NOT repeated here; (4) DLC / rank gating of the carrier row still applies; (5) the shop text and
 *   picture show the carrier gun unless baked; (6) the pool's cap / grow fields are as read; (7) objects made here are freed by the game's
 *   pool reset (0x42d9a0 / 0x5cae10) like the builder's.
 *
 * WIRING (klhook.c; not done):
 *   #include "klshop.c"          below  #include "klinv.c"
 *   klshop_init();               below  klinv_init();
 *   klshop_tick(game_thread);    below  klinv_tick(game_thread);
 */
#ifndef KLSHOP_C
#define KLSHOP_C

#define KLS_SESSION 0x0168e598
#define KLS_SETTINGS 0x0168e9e4
#define KLS_WEAPONS 0x0168e96c
#define KLS_SHOP    0x00bd1f68
#define KLS_RULES_VT 0x00bd3514
#define KLS_UI      0x00dd265c
#define KLS_MAKER   0x00710ad0
#define KLS_TEMPLATE 0x005d2f50
#define KLS_REALLOC 0x00b10328
#define KLS_MAX 8
#define KLS_PER 8

typedef void *(__fastcall *kls_maker_t)(void *self, void *edx, int zero, void *tmpl);
typedef void *(__fastcall *kls_tmpl_t)(void *self, void *edx, int item);
typedef void *(__cdecl *kls_realloc_t)(void *, size_t);

static struct { int on, log, n; int row[KLS_MAX], item[KLS_MAX]; DWORD made[KLS_MAX][KLS_PER]; int applied[KLS_MAX], told; int wait; } kls;

static int kls_code_ok(void)
{   /* the first bytes of the maker and the template lookup in THIS build */
    static const BYTE mk[8] = { 0x8b, 0x44, 0x24, 0x08, 0x85, 0xc0, 0x75, 0x03 };       /* 0x710ad0 mov eax,[esp+8]; test eax,eax; jne */
    static const BYTE tp[8] = { 0x8b, 0x44, 0x24, 0x04, 0x8b, 0x04, 0x81, 0xc2 };       /* 0x5d2f50 mov eax,[esp+4]; mov eax,[ecx+eax*4]; ret 4 */
    BYTE a[8], b[8];
    return klh_rd((DWORD_PTR)KLH_VA(KLS_MAKER), a, 8) && !memcmp(a, mk, 8) && klh_rd((DWORD_PTR)KLH_VA(KLS_TEMPLATE), b, 8) && !memcmp(b, tp, 8);
}

/* pool vector: -> array pointer, count; 0 when unreadable */
static DWORD kls_vec(DWORD *vec)
{
    DWORD w, a;
    if (!(w = klh_rd32((DWORD_PTR)KLH_VA(KLS_WEAPONS))) || !(a = klh_rd32(w)) || a < 0x10000) return 0;
    *vec = a; return a;
}

static int kls_apply(int k)
{
    DWORD a, n = 0, cap = 0, grow = 0, ents, i, carrier; int j, parked = 0; void *tmpl, *self;
    if (!kls_vec(&a) || !klh_rd(a + 4, &n, 4) || !klh_rd(a + 8, &cap, 4) || !klh_rd(a + 0xc, &grow, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10))) return 0;
    if (!(carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * kls.row[k]))) return 0;
    for (i = 0; i < n; i++) { DWORD e[3]; if (klh_rd(ents + 12 * i, e, 12) && e[1] == carrier && e[0] && (e[2] & 0xff) && !(e[2] & 0xff00)) parked++; }
    if (!parked) return 0;                                               /* builder has not run yet */
    if (!(self = (void *)(DWORD_PTR)klh_rd32(klh_rd32((DWORD_PTR)KLH_VA(KLS_UI)) + 0x15b0))) return 0;
    tmpl = ((kls_tmpl_t)KLH_VA(KLS_TEMPLATE))(self, 0, kls.item[k]);
    if (!tmpl) { klog("shop: item %d has no template in this level: pair %d:%d skipped", kls.item[k], kls.row[k], kls.item[k]); return -1; }
    if (cap < n + KLS_PER + 1) {                                        /* the builder's growth: cap += grow, realloc(array, cap*12) */
        DWORD ncap = n + KLS_PER + 8; void *p;
        if (grow > 64) return 0;
        p = ((kls_realloc_t)(DWORD_PTR)klh_rd32((DWORD_PTR)KLH_VA(KLS_REALLOC)))((void *)(DWORD_PTR)ents, ncap * 12);
        if (!p) return 0;
        ents = (DWORD)(DWORD_PTR)p; cap = ncap;
        klh_data((void *)(DWORD_PTR)(a + 8), &cap, 4, "KLShop: pool capacity"); klh_data((void *)(DWORD_PTR)(a + 0x10), &ents, 4, "KLShop: pool array");
    }
    for (j = 0; j < KLS_PER; j++) {
        DWORD obj = (DWORD)(DWORD_PTR)((kls_maker_t)KLH_VA(KLS_MAKER))(self, 0, 0, tmpl), ent[3];
        if (!obj) break;
        ent[0] = obj; ent[1] = carrier; ent[2] = 1;                      /* object, label, byte+8 = 1 free, byte+9 = 0 */
        klh_data((void *)(DWORD_PTR)(ents + 12 * n), ent, 12, "KLShop: pool entry"); n++;
        kls.made[k][j] = obj;
    }
    if (!j) { klog("shop: object maker returned nothing for item %d: pair %d:%d dropped, stock left alone", kls.item[k], kls.row[k], kls.item[k]); return -1; }   /* never park without a replacement */
    klh_data((void *)(DWORD_PTR)(a + 4), &n, 4, "KLShop: pool count");
    for (i = 0; i < n - j; i++) {                                        /* park the stock objects of the carrier */
        DWORD e[3]; BYTE zero = 0;
        if (klh_rd(ents + 12 * i, e, 12) && e[1] == carrier && (e[2] & 0xff)) klh_data((void *)(DWORD_PTR)(ents + 12 * i + 8), &zero, 1, "KLShop: park stock gun");
    }
    kls.applied[k] = 1;
    klog("shop: row %d (item %lu) now hands over item %d: %d objects added, %d stock parked (static reading, GUESS until run)", kls.row[k], carrier, kls.item[k], j, parked);
    return 1;
}

static void klshop_tick(int game_thread)
{
    DWORD sm, st = 0; int k, any = 0;
    if (!kls.on || !game_thread || !klh_exe_ok) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x70, &st, 4)) return;
    if (kl_online()) return;
    { DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(KLS_SETTINGS)), rules = gs ? klh_rd32(gs + 0x54) : 0;
      if (!rules || klh_rd32(rules) != (DWORD)(DWORD_PTR)KLH_VA(KLS_RULES_VT)) return; }
    if (st >= 0x19) return;                                              /* the round runs: leave the pool alone */
    if (kls.wait > 3000) return;
    if (!kls_code_ok()) { if (!kls.told++) klog("shop: code of the object maker / template lookup is not as read: nothing done"); return; }
    for (k = 0; k < kls.n; k++) {
        if (kls.row[k] < 0) continue;
        if (kls.applied[k]) {                                            /* still ours? else the pool was rebuilt: forget and redo */
            DWORD a, n = 0, ents, i; int alive = 0;
            if (kls_vec(&a) && klh_rd(a + 4, &n, 4) && n <= 4096 && (ents = klh_rd32(a + 0x10)))
                for (i = 0; i < n && !alive; i++) { DWORD e[3]; if (klh_rd(ents + 12 * i, e, 12) && e[0] == kls.made[k][0]) alive = 1; }
            if (alive) { any = 1; continue; }
            memset(kls.made[k], 0, sizeof kls.made[k]); kls.applied[k] = 0;
        }
        if (kls_apply(k) == -1) kls.row[k] = -1;
        else any = 1;
    }
    if (!any) kls.wait++;
}

static void klshop_init(void)
{
    char buf[200], *p;
    kls.on = GetPrivateProfileIntA("Shop", "Enable", 0, klh_ini) != 0;
    if (!kls.on) return;
    GetPrivateProfileStringA("Shop", "Swap", "", buf, sizeof buf, klh_ini);
    for (p = buf; *p && kls.n < KLS_MAX;) {
        int r = -1, it = -1, c = 0;
        int q, dup = 0;
        if (sscanf(p, "%d:%d%n", &r, &it, &c) >= 2) for (q = 0; q < kls.n; q++) if (kls.row[q] == r) dup = 1;   /* one replacement per row */
        if (dup) klog("shop: row %d listed twice: second entry ignored", r);
        else if (r >= 0 && r < 36 && it >= 1 && it < 64) { kls.row[kls.n] = r; kls.item[kls.n] = it; kls.n++; }
        else klog("shop: Swap entry near '%s' is not row(0..35):item(1..63): ignored", p);
        while (*p && *p != ',') p++;
        if (*p == ',') p++;
        (void)c;
    }
    if (!kls.n) kls.on = 0;
    klog("shop: on; %d swap(s); Arcade only, before the round; replaces what a bought row hands over (never adds a row); EXPERIMENT, nothing has run", kls.n);
}

#endif /* KLSHOP_C */
