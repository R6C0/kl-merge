/*
 * klshop.c - MORE GUNS IN THE FRAGILE ALLIANCE WEAPON SHOP, by SWAPPING WHAT A BOUGHT ROW HANDS OVER (re\shop_more_guns.md, 2026-10-19).
 * Part of KLHook (included by klhook.c after klinv.c; Arcade only, inert online). Off unless KLHook.ini [Shop] Enable=1.
 * RUN LIVE 2026-10-20 (S7-S11: rows 2, 13, 16, 32 handed over Minimi, HK69, Type 81, Rem 700; re\shop_more_guns.md). DATA writes and ONE call of the game's own object maker on the game thread; NO code byte, no hashed byte.
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
 *   Swap=          DEFAULT comma list "row:item" - row 0..35 of re\shop_plan.md, item = eFF2Item value 1..63 (tools\kl_shop_extra.py lists the usable ones)
 *   ReserveClips=2 reserve ammo, in clips, of an extra gun whose clip swallows the row's whole ammo (Minimi on a pistol row); 0 = leave it
 * KLGuns.ini beside a map's archive (2026-10-20, tools\kl_shop_swap.py writes it):
 *   [Shop]
 *   Swap=13:52,16:40   this map's set instead of the default; "Swap=" (empty) = no swap on this map; no line = the default above.
 *   The same line tells tools\kl_shop_swap.py which names/pictures to bake, so hook and bake agree. Read by klshop_level_open (klsteam.c).
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

static struct { int on, log, n; int row[KLS_MAX], item[KLS_MAX]; DWORD made[KLS_MAX][KLS_PER]; BYTE fixed[KLS_MAX][KLS_PER]; int applied[KLS_MAX], decided[KLS_MAX], told; int wait; LONG gen; int clips; int osw, oswrep, oswlog; } kls;
static char kls_oswmap[32];                                              /* the map key of the last klshop_level_open (any thread, plain bytes; [Shop] OnlineSwapLog only) */
#define KLS_AMMO_KEY 0xbeebbeeb                                        /* ZFFItemWeapon keeps rounds [obj+0xdc] and reserve [obj+0xe0] XORed with it */
/* the swap set to use, filled by klshop_init (KLHook.ini = default) and klshop_level_open (the map's KLGuns.ini [Shop] Swap, any thread);
   the game thread copies it into kls when kls_sgen changed. kls_slock is a tiny spin lock (no init needed). */
static struct { int n; int row[KLS_MAX], item[KLS_MAX]; } kls_def, kls_stg;
static volatile LONG kls_sgen, kls_slock;

static void kls_lock(void) { while (InterlockedExchange(&kls_slock, 1)) Sleep(0); }
static void kls_unlock(void) { InterlockedExchange(&kls_slock, 0); }

/* "row:item,row:item" -> set; one replacement per row, row 0..35, item 1..63, at most KLS_MAX */
static void kls_parse(const char *text, int *n, int *row, int *item, const char *who)
{
    const char *p; *n = 0;
    for (p = text; *p && *n < KLS_MAX;) {
        int r = -1, it = -1, c = 0, q, dup = 0;
        if (sscanf(p, "%d:%d%n", &r, &it, &c) >= 2) for (q = 0; q < *n; q++) if (row[q] == r) dup = 1;
        if (dup) klog("shop: %s: row %d listed twice: second entry ignored", who, r);
        else if (r >= 0 && r < 36 && it >= 1 && it < 64 && c) { row[*n] = r; item[*n] = it; (*n)++; }
        else klog("shop: %s: Swap entry near '%s' is not row(0..35):item(1..63): ignored", who, p);
        while (*p && *p != ',') p++;
        if (*p == ',') p++;
    }
}

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
        kls.fixed[k][j] = 0;
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

/* RESERVE AMMO of a handed-over extra gun (workflow wsd2cunom, 2026-10-20, read twice): the loadout 0x410710 passes the ROW's ammo
   (table +4, hashed) to 0x538ec0, which sets rounds = min(clip, ammo) and reserve = ammo - rounds (0x538f72..0x538fb4). A gun whose clip
   is >= the row's ammo (Minimi 150 on the USP row's 150) gets reserve 0 (live S7: 'MINIMI / 0'). Fix, heap data only: once one of our
   objects is TAKEN (entry byte +8 == 0) with reserve 0 and rounds >= the row's ammo, its reserve [obj+0xe0] := clips x rounds (KEY-XORed,
   as the game's setter 0x494180 writes it). Once per hand-over: the mark is cleared when the entry is free again (round reset).
   GUESS: 0x6020d0 (hashed) gets the same numbers right after and might keep its own copy - a reload in the game tells. */
static void kls_ammo(void)
{
    DWORD a, n = 0, ents, i; int k, m;
    if (kls.clips <= 0 || !kls_vec(&a) || !klh_rd(a + 4, &n, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10))) return;
    for (i = 0; i < n; i++) {
        DWORD e[3];
        if (!klh_rd(ents + 12 * i, e, 12) || !e[0]) continue;
        for (k = 0; k < kls.n; k++) for (m = 0; m < KLS_PER; m++) if (kls.applied[k] && kls.made[k][m] == e[0]) {
            DWORD rounds, res, ammo, r;
            if (e[2] & 0xff) { if (!(e[2] & 0xff00)) kls.fixed[k][m] = 0; continue; }          /* free again: a later hand-over is fixed anew */
            if (kls.fixed[k][m] || !klh_rd32(e[0] + 0xc4)) continue;
            rounds = klh_rd32(e[0] + 0xdc) ^ KLS_AMMO_KEY; res = klh_rd32(e[0] + 0xe0) ^ KLS_AMMO_KEY;
            ammo = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * kls.row[k] + 4);
            kls.fixed[k][m] = 1;
            if (res || !rounds || rounds > 999 || rounds < ammo) continue;                    /* the stock formula already gave a reserve */
            r = rounds * (DWORD)kls.clips; if (r > 600) r = 600;
            r ^= KLS_AMMO_KEY;
            klh_data((void *)(DWORD_PTR)(e[0] + 0xe0), &r, 4, "KLShop: reserve ammo of a swapped gun");
            klog("shop: row %d's extra gun %08lx handed over with %lu rounds and no reserve (row ammo %lu): reserve set to %lu", kls.row[k], e[0], rounds, ammo, r ^ KLS_AMMO_KEY);
        }
    }
}

/* what the pool hands over for shop row `row`: 0 = no pair / not on, 1 = a pair but NOT decided yet (online: before the flip in kls_osw_tick), 2 = ours (*item = the item),
 * 3 = decided STOCK (no template / carrier absent / gun+0x13c missing at state 0x18). Read by kllocname.c ([Shop] OnlineSwapText=2). Any thread, plain reads.
 * Review 10-28: one 0 for 'stock' and 'undecided' made mode 2 name the carrier over a correct baked name before the flip. */
static int kls_row_state(int row, int *item)
{
    int k;
    if (item) *item = 0;
    if (!kls.on) return 0;
    for (k = 0; k < kls.n && k < KLS_MAX; k++) if (kls.row[k] == row) {
        if (kls.applied[k] == 1) { if (item) *item = kls.item[k]; return 2; }
        return kls.decided[k] ? 3 : 1;
    }
    return 0;
}

/* ==== [Shop] OnlineSwap=0|1|2 (2026-10-28, NOT RUN IN THE GAME; 0 = off, default; 1 = on; 2 = log only: nothing made, nothing parked) ====
 * What it is for: on a baked map the shop rows 13/16/32/35 are NAMED and PICTURED as HK69 / TYPE 81 / REM 700 / MINIMI. Arcade's [Shop] Swap hands those guns over;
 * online the swap is off (the gate in klshop_tick), so the stock carrier gun came out. This makes the same swap online, with the same pool recipe as offline.
 * THE ID QUESTION: no item id travels in the buy. It sends ROWS (RMCBuyWeaponPack(primaryRow, secondaryRow), see the header, read in kl2.exe); every peer resolves
 *   row -> carrier item through the SAME hashed table at 0xbd1f68 and then picks a free pool entry LABELLED with that carrier (0x55bee0). Our objects carry the
 *   carrier's label, so host and client both take "the extra gun of row R" from their own pool: the same id is computed from the same row on both sides, and
 *   no network message is changed. What a row cannot carry is the OBJECT identity: each gun has a Quazal DO (gun+0x13c) whose id comes from the entity order
 *   (0x6ece90), so every peer must make the same objects in the same order. In code that is: rows ascending (not list order), KLS_PER objects per row, made at the
 *   hook point of [ShopPage] OnlineEarlyMake (between the pool build 0x5230a0 and the DO pass), the same swap set on every peer (the map's KLGuns.ini [Shop] Swap,
 *   else KLHook.ini; the log line 'osw: set' prints a hash to compare across peers).
 *   GUESS: the DO pass links objects made here exactly as it does for page II's early make (that path is itself unbenched), and the net spawn bookkeeping after
 *   each item in the builder (0x753150, see the header) is not needed for them.
 * Safety: stock entries of the carrier are parked ONLY when every object of ours of that row has gun+0x13c != 0 (the CE27_P2P4H crash 0x9425a4 came from a gun with
 *   +0x13c = 0 handed over online); otherwise ours are parked and the stock gun is handed over, as before this key existed. Needs [ShopPage] Enable=1 (the hook
 *   point, kllobby.c's slot-26 wrapper, is armed from klshoppage.c).
 */
static DWORD kls_osw_hash(void)
{
    DWORD h = 2166136261u; int k, row;
    for (row = 0; row < 36; row++) for (k = 0; k < kls.n; k++) if (kls.row[k] == row) { h = (h ^ (DWORD)row) * 16777619u; h = (h ^ (DWORD)kls.item[k]) * 16777619u; }
    return h;
}

static int kls_in_pool(DWORD ents, DWORD n, DWORD obj)
{
    DWORD i;
    for (i = 0; i < n; i++) if (klh_rd32(ents + 12 * i) == obj) return 1;
    return 0;
}

static void kls_adopt(void)
{
    if (kls.gen == kls_sgen) return;
    kls_lock(); kls.gen = kls_sgen; kls.n = kls_stg.n; memcpy(kls.row, kls_stg.row, sizeof kls.row); memcpy(kls.item, kls_stg.item, sizeof kls.item); kls_unlock();
    memset(kls.made, 0, sizeof kls.made); memset(kls.fixed, 0, sizeof kls.fixed); memset(kls.applied, 0, sizeof kls.applied); memset(kls.decided, 0, sizeof kls.decided); kls.told = 0; kls.wait = 0;
}

/* called from klshoppage.c's kspg_early_make (game thread, online, session state still 0x14 / 0x15, right after the pool build) */
static void kls_osw_early(int host)
{
    DWORD sm, st, a, n = 0, cap = 0, grow = 0, ents, i, carrier; int k, row, rows = 0, made = 0, had = 0; void *self;
    if (!kls.on || !kls.osw || !klh_exe_ok || !kl_online()) return;
    kls_adopt();
    if (!kls.n) return;
    if (!kls_code_ok()) { static BYTE t0; if (!t0) { t0 = 1; klog("osw: code of the object maker / template lookup is not as read: nothing done"); } return; }
    sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION)); st = sm ? klh_rd32(sm + 0x70) : 0xffff;
    if (!sm || klh_rd32(sm + 0x5c) != 4 || (st != 0x14 && st != 0x15)) { static BYTE t1; if (!t1) { t1 = 1; klog("osw: early make skipped: mode %d state 0x%lx", sm ? (int)klh_rd32(sm + 0x5c) : -1, (unsigned long)st); } return; }
    if (!kls_vec(&a) || !klh_rd(a + 4, &n, 4) || !klh_rd(a + 8, &cap, 4) || !klh_rd(a + 0xc, &grow, 4) || !n || n > 4096 || !(ents = klh_rd32(a + 0x10))) { klog("osw: early make skipped: pool empty or unreadable"); return; }
    if (!(self = (void *)(DWORD_PTR)klh_rd32(klh_rd32((DWORD_PTR)KLH_VA(KLS_UI)) + 0x15b0))) { klog("osw: early make skipped: UI object (template lookup) not ready"); return; }
    kls.oswrep = 1;
    klog("osw: set %d pair(s), hash %08lx (compare on every peer), mode %d (%s site, state 0x%lx)", kls.n, (unsigned long)kls_osw_hash(), kls.osw, host ? "host" : "client", (unsigned long)st);
    for (row = 0; row < 36; row++) for (k = 0; k < kls.n; k++) {
        void *tmpl; int j, parked = 0;
        if (kls.row[k] != row) continue;
        rows++;
        if (kls.made[k][0] && kls_in_pool(ents, n, kls.made[k][0])) { had++; continue; }   /* survived from the last round: no second set */
        memset(kls.made[k], 0, sizeof kls.made[k]); memset(kls.fixed[k], 0, sizeof kls.fixed[k]); kls.applied[k] = 0; kls.decided[k] = 0;
        if (!(carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * row))) continue;
        for (i = 0; i < n; i++) { DWORD e[3]; if (klh_rd(ents + 12 * i, e, 12) && e[1] == carrier && e[0]) parked++; }
        tmpl = ((kls_tmpl_t)KLH_VA(KLS_TEMPLATE))(self, 0, kls.item[k]);
        if (!tmpl) { kls.decided[k] = 1; klog("osw: row %d item %d has no template: row stays stock", row, kls.item[k]); if (kls.oswlog) klog("oswlog: map %s row %d item %d: STOCK handed over (no template)", kls_oswmap[0] ? kls_oswmap : "?", row, kls.item[k]); continue; }
        if (!parked) { kls.decided[k] = 1; klog("osw: row %d carrier %lu has no stock object in the pool: row stays stock", row, (unsigned long)carrier); if (kls.oswlog) klog("oswlog: map %s row %d item %d: STOCK handed over (carrier absent from the pool)", kls_oswmap[0] ? kls_oswmap : "?", row, kls.item[k]); continue; }
        if (kls.osw == 2) { klog("osw: LOG ONLY row %d (carrier item %lu, %d stock object(s)) would get %d object(s) of item %d", row, (unsigned long)carrier, parked, KLS_PER, kls.item[k]); if (kls.oswlog) klog("oswlog: map %s row %d carrier %lu item %d: OURS would be handed over (OnlineSwap=2, log only)", kls_oswmap[0] ? kls_oswmap : "?", row, (unsigned long)carrier, kls.item[k]); continue; }
        if (cap < n + KLS_PER + 1) {                                    /* same growth as kls_apply */
            DWORD ncap = n + KLS_PER + 8; void *p;
            if (grow > 64) continue;
            p = ((kls_realloc_t)(DWORD_PTR)klh_rd32((DWORD_PTR)KLH_VA(KLS_REALLOC)))((void *)(DWORD_PTR)ents, ncap * 12);
            if (!p) continue;
            ents = (DWORD)(DWORD_PTR)p; cap = ncap;
            klh_data((void *)(DWORD_PTR)(a + 8), &cap, 4, "KLShop: online pool capacity"); klh_data((void *)(DWORD_PTR)(a + 0x10), &ents, 4, "KLShop: online pool array");
        }
        for (j = 0; j < KLS_PER; j++) {
            DWORD obj = (DWORD)(DWORD_PTR)((kls_maker_t)KLH_VA(KLS_MAKER))(self, 0, 0, tmpl), ent[3];
            if (!obj) break;
            ent[0] = obj; ent[1] = carrier; ent[2] = 0;                  /* PARKED, carrier's label: the stock gun is the default until kls_osw_tick sees gun+0x13c on all of ours (a missed tick or a fault leaves stock) */
            klh_data((void *)(DWORD_PTR)(ents + 12 * n), ent, 12, "KLShop: online pool entry"); n++;
            kls.made[k][j] = obj; kls.fixed[k][j] = 0;
        }
        klh_data((void *)(DWORD_PTR)(a + 4), &n, 4, "KLShop: online pool count");
        if (j) made++;
        klog("osw: row %d (carrier item %lu): %d object(s) of item %d made (%s)", row, (unsigned long)carrier, j, kls.item[k], host ? "host" : "client");
    }
    klog("osw: early make done: %d pair(s) in the set, %d made now, %d already there, pool %lu", rows, made, had, (unsigned long)n);
}

/* game thread, online, state 0x16..0x18 (before the round runs): per pair decide stock-or-ours from gun+0x13c, logged once per round.
 * kls.applied[k]: 0 = undecided (ours parked from kls_osw_early, stock free), 1 = ours (flipped ONCE when every one of ours has +0x13c: unpark ours, then keep
 * the free stock entries of the carrier parked). Never flips back: ours were parked until then, so no player can hold one and an unpark cannot free a taken gun.
 * Review 10-28: the first version parked whichever side was unwanted on every tick and never unparked, so a not-linked -> linked flip parked BOTH sides. */
static void kls_osw_tick(DWORD st)
{
    DWORD a, n = 0, ents, i; int k, m;
    if (!kls.osw || kls.osw == 2 || st < 0x16 || st >= 0x19 || !kls_vec(&a) || !klh_rd(a + 4, &n, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10))) return;
    for (k = 0; k < kls.n; k++) {
        DWORD carrier; int linked = 0, cnt = 0, want;
        if (kls.row[k] < 0 || !kls.made[k][0]) continue;
        if (!kls_in_pool(ents, n, kls.made[k][0])) { memset(kls.made[k], 0, sizeof kls.made[k]); kls.applied[k] = 0; kls.decided[k] = 0; continue; }
        if (!(carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * kls.row[k]))) continue;
        for (m = 0; m < KLS_PER && kls.made[k][m]; m++) { cnt++; if (klh_rd32((DWORD_PTR)kls.made[k][m] + 0x13c)) linked++; }
        want = cnt && linked == cnt;
        if (kls.oswrep) {
            DWORD id = 0;
            __try { id = ((DWORD (__fastcall *)(DWORD))(DWORD_PTR)KLH_VA(0x6ece90))(kls.made[k][0]); } __except (1) { id = 0xdead; }
            klog("osw: row %d: %d object(s), %d with gun+0x13c set, id 0x6ece90 of the first = %lu (state 0x%lx): %s", kls.row[k], cnt, linked, (unsigned long)id, (unsigned long)st, want ? "ours are handed over" : "STOCK gun stays (net sub-object missing)");
            if (kls.oswlog) klog("oswlog: map %s row %d carrier %lu item %d: %s", kls_oswmap[0] ? kls_oswmap : "?", kls.row[k], (unsigned long)carrier, kls.item[k], want ? "OURS handed over" : "STOCK handed over");
        }
        if (!kls.applied[k] && !want) { if (st >= 0x18) kls.decided[k] = 1; continue; }   /* undecided: ours stay parked, stock stays free */
        for (i = 0; i < n; i++) {
            DWORD e[3]; BYTE zero = 0, one = 1; int ours = 0;
            if (!klh_rd(ents + 12 * i, e, 12) || e[1] != carrier || !e[0]) continue;
            for (m = 0; m < KLS_PER; m++) if (e[0] == kls.made[k][m]) ours = 1;
            if (ours) { if (!kls.applied[k] && !(e[2] & 0xff)) klh_data((void *)(DWORD_PTR)(ents + 12 * i + 8), &one, 1, "KLShop: online unpark ours (net sub-object linked)"); }
            else if (e[2] & 0xff) klh_data((void *)(DWORD_PTR)(ents + 12 * i + 8), &zero, 1, "KLShop: online park stock gun");
        }
        if (!kls.applied[k] && kls.oswlog && !kls.oswrep) klog("oswlog: map %s row %d carrier %lu item %d: OURS (flipped after the first report, state 0x%lx)", kls_oswmap[0] ? kls_oswmap : "?", kls.row[k], (unsigned long)carrier, kls.item[k], (unsigned long)st);
        kls.applied[k] = 1; kls.decided[k] = 0;
    }
    kls.oswrep = 0;
}

static void klshop_tick(int game_thread)
{
    DWORD sm, st = 0; int k, any = 0;
    if (!kls.on || !game_thread || !klh_exe_ok) return;
    if (kls.gen != kls_sgen) {                                           /* a map announced its set (or the default came back): adopt it, forget the old state */
        kls_lock(); kls.gen = kls_sgen; kls.n = kls_stg.n; memcpy(kls.row, kls_stg.row, sizeof kls.row); memcpy(kls.item, kls_stg.item, sizeof kls.item); kls_unlock();
        memset(kls.made, 0, sizeof kls.made); memset(kls.fixed, 0, sizeof kls.fixed); memset(kls.applied, 0, sizeof kls.applied); memset(kls.decided, 0, sizeof kls.decided); kls.told = 0; kls.wait = 0;
    }
    if (!kls.n) return;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x70, &st, 4)) return;
    if (kl_online()) {                                                   /* online: only [Shop] OnlineSwap (1; 2 logs in kls_osw_early), the rules vtable differs online so it is not tested */
        if (kls.osw == 1) { kls_ammo(); kls_osw_tick(st); }
        return;
    }
    { DWORD gs = klh_rd32((DWORD_PTR)KLH_VA(KLS_SETTINGS)), rules = gs ? klh_rd32(gs + 0x54) : 0;
      if (!rules || klh_rd32(rules) != (DWORD)(DWORD_PTR)KLH_VA(KLS_RULES_VT)) return; }
    kls_ammo();                                                          /* also while the round runs: the loadout hands over as it starts */
    if (st >= 0x19) return;                                              /* the round runs: leave the pool alone */
    if (kls.wait > 3000) return;
    if (!kls_code_ok()) { if (!kls.told++) klog("shop: code of the object maker / template lookup is not as read: nothing done"); return; }
    for (k = 0; k < kls.n; k++) {
        if (kls.row[k] < 0) continue;
        if (kls.applied[k]) {                                            /* still ours? else the pool was rebuilt: forget and redo */
            DWORD a, n = 0, ents, i; int alive = 0;
            if (kls_vec(&a) && klh_rd(a + 4, &n, 4) && n <= 4096 && (ents = klh_rd32(a + 0x10)))
                for (i = 0; i < n && !alive; i++) { DWORD e[3]; if (klh_rd(ents + 12 * i, e, 12) && e[0] == kls.made[k][0]) alive = 1; }
            if (alive) {                                                 /* LIVE 2026-10-20 (S6): the pool survives the round, but the round's end frees
                                                                            every gun again, the parked stock ones too, and they come first: re-park them */
                DWORD carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * kls.row[k]); int re = 0;
                for (i = 0; i < n; i++) {
                    DWORD e[3]; BYTE zero = 0; int m, ours = 0;
                    if (!klh_rd(ents + 12 * i, e, 12) || e[1] != carrier || !(e[2] & 0xff)) continue;
                    for (m = 0; m < KLS_PER; m++) if (e[0] == kls.made[k][m]) ours = 1;
                    if (!ours) { klh_data((void *)(DWORD_PTR)(ents + 12 * i + 8), &zero, 1, "KLShop: re-park stock gun"); re++; }
                }
                if (re) klog("shop: row %d: %d stock object(s) were free again (round reset): parked again", kls.row[k], re);
                any = 1; continue;
            }
            memset(kls.made[k], 0, sizeof kls.made[k]); memset(kls.fixed[k], 0, sizeof kls.fixed[k]); kls.applied[k] = 0; kls.decided[k] = 0;
        }
        if (kls_apply(k) == -1) kls.row[k] = -1;
        else any = 1;
    }
    if (!any) kls.wait++;
}

/* From klsteam.c's klh_level_open (any thread, several times per load): the map's own swap set, "[Shop] Swap=row:item,..." in the
   KLGuns.ini beside the opened archive. No such line = KLHook.ini's [Shop] Swap (the default); "Swap=" empty = no swap on this map.
   Reads a file, touches no game memory. Inert unless [Shop] Enable=1. */
static void klshop_level_open(const char *key, const char *opened)
{
    char file[MAX_PATH], buf[200], *s; DWORD len; int n, row[KLS_MAX], item[KLS_MAX], same;
    if (!kls.on) return;
    if (key) { strncpy(kls_oswmap, key, sizeof kls_oswmap - 1); kls_oswmap[sizeof kls_oswmap - 1] = 0; }
    len = GetFullPathNameA(opened, MAX_PATH, file, 0);
    if (!len || len >= MAX_PATH || !(s = strrchr(file, 0x5c)) || (size_t)(s - file) + 12 >= sizeof file) return;
    strcpy(s + 1, "KLGuns.ini");
    GetPrivateProfileStringA("Shop", "Swap", "<none>", buf, sizeof buf, file);
    if (!strcmp(buf, "<none>")) { n = kls_def.n; memcpy(row, kls_def.row, sizeof row); memcpy(item, kls_def.item, sizeof item); }
    else kls_parse(buf, &n, row, item, key);
    kls_lock();
    same = n == kls_stg.n && !memcmp(row, kls_stg.row, sizeof(int) * n) && !memcmp(item, kls_stg.item, sizeof(int) * n);
    if (!same) { kls_stg.n = n; memcpy(kls_stg.row, row, sizeof row); memcpy(kls_stg.item, item, sizeof item); InterlockedIncrement(&kls_sgen); }
    kls_unlock();
    if (!same) klog("shop: map %s: %d swap(s) from %s (%s)", key, n, strcmp(buf, "<none>") ? "its KLGuns.ini [Shop] Swap" : "KLHook.ini [Shop] Swap", buf);
}

static void klshop_init(void)
{
    char buf[200];
    kls.on = GetPrivateProfileIntA("Shop", "Enable", 0, klh_ini) != 0;
    if (!kls.on) return;
    GetPrivateProfileStringA("Shop", "Swap", "", buf, sizeof buf, klh_ini);
    kls_parse(buf, &kls_def.n, kls_def.row, kls_def.item, "KLHook.ini");
    kls_stg = kls_def; kls_sgen = 1; kls.gen = 0;                        /* the tick adopts it */
    kls.osw = GetPrivateProfileIntA("Shop", "OnlineSwap", 0, klh_ini); if (kls.osw < 0 || kls.osw > 2) kls.osw = 0;   /* 0 off, 1 on, 2 log only; online the swap rides the early-make hook of klshoppage.c (needs [ShopPage] Enable=1) */
    if (kls.osw) klog("shop: OnlineSwap=%d (NOT run in the game): online the baked rows hand over the swapped gun like Arcade; no network message changes; see klshop.c OnlineSwap", kls.osw);
    kls.oswlog = kls.osw && GetPrivateProfileIntA("Shop", "OnlineSwapLog", 0, klh_ini) != 0;   /* (recommended off) bench only: one 'oswlog:' line per row and round, with the map */
    if (kls.oswlog) klog("shop: OnlineSwapLog=1 (bench only): 'oswlog: map .. row .. item ..: OURS|STOCK handed over' per row and round");
    kls.clips = GetPrivateProfileIntA("Shop", "ReserveClips", 2, klh_ini); /* reserve of an extra gun the row's ammo leaves empty, in clips (0 = leave it) */
    klog("shop: on; %d default swap(s); a map's KLGuns.ini [Shop] Swap overrides; Arcade only, before the round; replaces what a bought row hands over (never adds a row); proven live S7-S11", kls_def.n);
}

#endif /* KLSHOP_C */
