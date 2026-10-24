/* klshoppage.c - "page II" of the between-rounds weapon shop (owner 2026-10-24: 'okay yes do a page 2'). Included by klhook.c AFTER klshop.c
 * (uses its KLS_* addresses and kls_* maker helpers' recipe; klshop.c itself is not edited).
 *
 * WHAT: a key (default F6, [ShopPage] Key=) flips the Arcade weapon shop between the stock set A and set B. In set B every row that has a
 * pair shows ANOTHER usable gun (items 33 35 38 40..59 62 63 = guns the stock FA maps carry but the shop table never lists): its own
 * name and description, the picture of the nearest stock gun, and the shop headline / category names get " II". Buying such a row hands
 * over the set-B gun at the next round (klshop.c's live-proven pool relabel: data writes only). Price, rank, lock and stars are the
 * CARRIER row's (the table is hashed and cannot change), so tools/kl_shop_sets.py picks carriers by category, price and tier.
 * The pairs, names and descriptions come from KLShopPage.ini (beside KLHook.ini; written by tools/kl_shop_sets.py).
 *
 * HOW (every address read from kl2.exe 0490 on 2026-10-24, static; nothing here ran in the game):
 *  - TEXT: MercsShowInfoFAWeapons (vtable 0xbbd0ec) and MercsSendMessageWeapons (0xbbd18c) answer a text key through vtable slot 24
 *    (0x490730, thiscall(this, char* key) -> char*, ret 4). The shop's keys are '/Menu/Online/WeaponShop/Weapon<row>' (name) and
 *    '.../Weapon<row>Desc'; the result is re-formatted with '%s' into the element's own buffer, so a static ring buffer is a safe return.
 *    Each such ELEMENT (heap object) gets a private vtable copy (DLL .data) whose slot 24 is ours, the pattern of kllocname.c / klchar.c:
 *    one data write of the object's first dword, no code byte of the exe touched. Per element (not the LOC object) so this cannot clash
 *    with kllocname.c's wrap of the LOC object.
 *  - PICTURE: MercsGraphicFA (0xbbcc84) slot 8 = update 0x58bc50: thiscall with NO stack arguments (review 2026-10-24: every path ends
 *    add esp,0xc / jmp 0x832470, which ends jmp 0x48f8e0 = plain ret; the first draft's 5-arg guess was wrong and would have eaten 20 bytes of the caller's stack). WeaponBig / PrimaryWeapon / SecondaryWeapon show themselves when their
 *    own PlayerIndex ([obj+0xc4]) equals the selected / carried row (0x58c552, 0x58c55e). The wrapper SWAPS that element-private index
 *    between row R and the picture row P for the duration of the original call, then puts it back. The global selection is not touched.
 *  - BUY: MercsFASelectorWeapons (0xbbd494) slot 20 = 0x810b20 (message handler, MSG* with a char* name first, ret 4): 'BuyWeaponDialogVoodoo'
 *    -> 0x7f73d0 refuses a row already carried; 'BuyWeapon' -> 0x6ddd10 writes the row to 0xced638/9. Our wrapper reads the name, and
 *    (a) for the Voodoo message, when the carried row of the slot being edited equals the highlighted row but was bought in the OTHER set,
 *    blanks that carried byte to 0xff for the call and restores it (OwnedTrick=1; GUESS: 0xff reads as 'no gun' in the check; the call is
 *    on the game thread, restored before it returns), (b) after 'BuyWeapon', records which set the carried gun came from.
 *  - HAND-OVER: own copy of klshop.c's recipe (park the carrier's stock objects, add 8 extra objects made with 0x710ad0 from the template
 *    0x5d2f50, labelled with the carrier's item), but per pair and ONLY for guns a slot actually carries from set B; the desired state is
 *    re-applied every tick before the round (st < 0x19) and undone when the gun is replaced. Rows klshop.c already swaps are skipped.
 *
 * k43 (2026-10-25) PRE-MAKE + LIVENESS: [ShopPage] PreMake=1 (recommended on): the page B objects of every configured pair are made ONCE while the first
 * shop is up (session state < 0x19, after the pool builder ran) and parked at once, so a page II buy in the 0x20 shop only flips byte+8 and never calls the
 * maker 0x710ad0 or reallocs the pool vector (the 10-24 21:30 exit followed such an in-0x20 buy; the log showed a clean exit(0) after focus-loss ShowCursor
 * stalls: the make is the one heavy thing a page II buy did). PreMake=0 or a failed premake keeps the old make-on-demand in kspg_enforce. Every made[][]
 * pointer is checked against the pool vector (kspg_sane) before kspg_ammo / kspg_check_pool / kspg_enforce read it, and dropped when the session enters
 * 0x23..0x25 or 0x16 (the pool is rebuilt there), so a freed object is never read.
 *
 * GUESSES (also marked in the code): the 5-arg update; the BuyWeapon message name layout; 0xff owned byte; that the shown row / carried
 * rows are bytes at 0x154d80c (dword) / 0xced638,9; that a purchase of the same row from the other set goes through the Voodoo trick.
 * KNOWN LIMITS: pad/mouse cannot toggle (key only); a gun bought in set B shows its B name in the carried slot only for that slot;
 * grenades (55..59) are only used when [ShopPage] Grenades=1 (tool side). Arcade offline only (the klshop.c gate); [ShopPage] Enable=0 default.
 */
#ifndef KLSHOPPAGE_C
#define KLSHOPPAGE_C

#define KSPG_ROWS 36
#define KSPG_PER 8
#define KSPG_MAXSLOT 96
#define KSPG_NCLS 4
#define KSPG_ROLES 192
#define KSPG_PARK 2048
#define KSPG_SHOWN_ROW 0x0154d80c
#define KSPG_MODE 0x0154d810
#define KSPG_EDIT 0x00ced63c
#define KSPG_CARRY 0x00ced638

static const DWORD kspg_cvt[KSPG_NCLS] = { 0x00bbd0ec, 0x00bbd18c, 0x00bbcc84, 0x00bbd494 };    /* ShowInfoFAWeapons, SendMessageWeapons, GraphicFA, SelectorWeapons */
static const int   kspg_cslot[KSPG_NCLS] = { 24, 24, 8, 20 };

typedef char *(__fastcall *kspg_txt_t)(void *self, void *edx, const char *key);
typedef void  (__fastcall *kspg_gfx_t)(void *self, void *edx);
typedef void  (__fastcall *kspg_msg_t)(void *self, void *edx, DWORD *msg);

static struct {
    int on, grenades, trick, key, log, clips, hint, keyDown, txtSeen, togglePend, premake, preDone, preTry, sane, st;
    volatile int active, pre, shownB;                 /* active: gate open and wrappers may act; shownB: set B on screen */
    int own[2];                                  /* 0/1: the gun carried in the primary / secondary slot came from set B */
    int carried[2];                              /* last seen carried rows */
    int have;                                    /* pairs loaded */
    struct { int ok, cfg, row, item, pic; DWORD retry; int fails; char name[48]; char desc[480]; } p[KSPG_ROWS];
    DWORD made[KSPG_ROWS][KSPG_PER]; int applied[KSPG_ROWS];
    DWORD parked[KSPG_PARK]; int nparked;
    int told, wait, trickOn, trickRow, trickSlot;
    DWORD lastScan, lastN, lastKey, toggleAt, listAt;
    char ring[8][520]; volatile LONG ri;
} kspg;

static struct { DWORD stock, orig; int n; DWORD vt[KSPG_MAXSLOT + 1]; } kspg_tab[KSPG_NCLS];       /* vt[0] = RTTI locator, vt[1+i] = slot i */
static struct { DWORD obj; int role; } kspg_role[KSPG_ROLES]; static int kspg_nrole;
enum { KR_NONE = 0, KR_OLDPRI = 1, KR_OLDSEC = 2, KR_BIG = 11, KR_PRI = 12, KR_SEC = 13 };

static int kspg_role_of(void *self)
{
    int i; for (i = 0; i < kspg_nrole; i++) if (kspg_role[i].obj == (DWORD)(DWORD_PTR)self) return kspg_role[i].role;
    return KR_NONE;
}

static int kspg_useB(int role) { return role == KR_OLDPRI ? kspg.own[0] : role == KR_OLDSEC ? kspg.own[1] : kspg.shownB; }

static char *kspg_ring(void) { return kspg.ring[(InterlockedIncrement(&kspg.ri) - 1) & 7]; }

static char *kspg_text(int c, void *self, const char *key)
{
    char *res = ((kspg_txt_t)(DWORD_PTR)kspg_tab[c].orig)(self, 0, key), *o; const char *p; int row, role;
    if (!kspg.active || !key || !res) return res;
    if ((p = strstr(key, "WeaponShop/Weapon")) != 0) {
        p += 17; row = 0;
        if (*p < '0' || *p > '9') return res;
        while (*p >= '0' && *p <= '9') row = row * 10 + (*p++ - '0');
        if (row < 0 || row >= KSPG_ROWS || !kspg.p[row].ok) return res;
        role = kspg_role_of(self);
        if (kspg.togglePend && !kspg.txtSeen) { kspg.txtSeen = 1; if (kspg.log) klog("shopPage: first text request after the toggle: key '%s', row %d, role %d, served from set %c", key, row, role, kspg_useB(role) ? 'B' : 'A'); }
        if (!kspg_useB(role)) return res;
        if (!*p) { o = kspg_ring(); strncpy(o, kspg.p[row].name, 519); o[519] = 0; return o; }
        if (!strcmp(p, "Desc")) { o = kspg_ring(); strncpy(o, kspg.p[row].desc, 519); o[519] = 0; return o; }
        return res;
    }
    if (kspg.hint && strstr(key, "BuyWeapons_Title")) {   /* GUESS: BuyWeapons_Title is the shop's caption; if it is never requested the hint just does not show */
        size_t n = strlen(res); char kn[16], add[48]; o = kspg_ring();
        if (n > 440) return res;
        if (kspg.key >= 0x70 && kspg.key <= 0x87) snprintf(kn, sizeof kn, "F%d", kspg.key - 0x6f);
        else if ((kspg.key >= '0' && kspg.key <= '9') || (kspg.key >= 'A' && kspg.key <= 'Z')) snprintf(kn, sizeof kn, "%c", kspg.key);
        else snprintf(kn, sizeof kn, "key %02X", kspg.key);
        snprintf(add, sizeof add, kspg.shownB ? "  II  [%s] stock page" : "  [%s] page II", kn);
        memcpy(o, res, n); strcpy(o + n, add);
        return o;
    }
    if (kspg.shownB && (strstr(key, "HeadlinePistol") || strstr(key, "HeadlineShot") ||
                       strstr(key, "HeadlineSub") || strstr(key, "HeadlineAssaultRifle"))) {
        size_t n = strlen(res); o = kspg_ring();
        if (n > 500) return res;
        memcpy(o, res, n); memcpy(o + n, " II", 4);
        return o;
    }
    return res;
}
static char *__fastcall kspg_text0(void *self, void *edx, const char *key) { (void)edx; return kspg_text(0, self, key); }
static char *__fastcall kspg_text1(void *self, void *edx, const char *key) { (void)edx; return kspg_text(1, self, key); }

/* the picture: swap the element's PlayerIndex R <-> P around the original update */
static void __fastcall kspg_gfx(void *self, void *edx)
{
    int role = kspg.active ? kspg_role_of(self) : 0, R = -99, swapped = 0; DWORD idx = 0, nidx = 0;
    (void)edx;
    if (role == KR_BIG && kspg.shownB && klh_rd32((DWORD_PTR)KLH_VA(KSPG_MODE)) == 2) R = (int)klh_rd32((DWORD_PTR)KLH_VA(KSPG_SHOWN_ROW));
    else if (role == KR_PRI && kspg.own[0]) R = kspg.carried[0];
    else if (role == KR_SEC && kspg.own[1]) R = kspg.carried[1];
    if (R >= 0 && R < KSPG_ROWS && kspg.p[R].ok && kspg.p[R].pic != R && kspg.p[R].pic >= 0 && kspg.p[R].pic < KSPG_ROWS) {
        idx = klh_rd32((DWORD_PTR)self + 0xc4);
        if ((int)idx == R) nidx = (DWORD)kspg.p[R].pic; else if ((int)idx == kspg.p[R].pic) nidx = (DWORD)R; else nidx = idx;
        if (nidx != idx && klh_data((void *)((DWORD_PTR)self + 0xc4), &nidx, 4, "KLShopPage: picture index (swapped for one update)")) swapped = 1;
    }
    ((kspg_gfx_t)(DWORD_PTR)kspg_tab[2].orig)(self, 0);
    if (swapped) klh_data((void *)((DWORD_PTR)self + 0xc4), &idx, 4, "KLShopPage: picture index restored");
}

/* the selector's messages */
static void kspg_note_buy(int before0, int before1)
{
    int now[2], s; now[0] = (int)(signed char)(BYTE)klh_rd32((DWORD_PTR)KLH_VA(KSPG_CARRY)); now[1] = (int)(signed char)(BYTE)(klh_rd32((DWORD_PTR)KLH_VA(KSPG_CARRY)) >> 8);
    for (s = 0; s < 2; s++) {
        int before = s ? before1 : before0;
        if (now[s] != before || (kspg.trickOn && kspg.trickSlot == s && kspg.trickRow == now[s])) {
            kspg.own[s] = kspg.shownB && now[s] >= 0 && now[s] < KSPG_ROWS && kspg.p[now[s]].ok;
            if (kspg.log) klog("shopPage: slot %d now carries row %d from set %c", s, now[s], kspg.own[s] ? 'B' : 'A');
        }
        kspg.carried[s] = now[s];
    }
    kspg.trickOn = 0;
}

static void __fastcall kspg_sel(void *self, void *edx, DWORD *msg)
{
    char nm[40]; DWORD w = 0; int edit, slot, other, hi; BYTE keep = 0, ff = 0xff; int b0, b1;
    (void)edx;
    if (!kspg.active || !msg || !klh_rdstr(klh_rd32((DWORD_PTR)msg), nm, sizeof nm)) { ((kspg_msg_t)(DWORD_PTR)kspg_tab[3].orig)(self, 0, msg); return; }
    w = klh_rd32((DWORD_PTR)KLH_VA(KSPG_CARRY));
    b0 = (int)(signed char)(BYTE)w; b1 = (int)(signed char)(BYTE)(w >> 8);
    if (!strcmp(nm, "BuyWeaponDialogVoodoo")) {
        /* 0x6ddd10 (disassembled): if [0xced63c] == -6 the row goes to byte 0xced639 (slot 1), otherwise to 0xced638 (slot 0). 0x7f73d0 refuses the row when
         * it equals EITHER byte, and reads the row from [selector+0x90] (not the global 0x154d80c). */
        edit = (int)klh_rd32((DWORD_PTR)KLH_VA(KSPG_EDIT)); slot = (edit == -6) ? 1 : 0; other = 1 - slot;
        hi = (int)klh_rd32((DWORD_PTR)self + 0x90);
        kspg.trickOn = 0;
        if (kspg.trick && hi >= 0 && hi < KSPG_ROWS && kspg.p[hi].ok && (slot ? b1 : b0) == hi && (kspg.own[slot] != 0) != (kspg.shownB != 0)) {
            if ((other ? b1 : b0) == hi) {      /* same row already in the OTHER slot: the stock refusal stands, and we say so */
                if (kspg.log) klog("shopPage: row %d is carried in both slots: the other set's gun of it is not offered (refused as stock)", hi);
            } else {
                keep = (BYTE)hi;
                if (klh_data((void *)((DWORD_PTR)KLH_VA(KSPG_CARRY) + slot), &ff, 1, "KLShopPage: owned check blanked for the dialog")) {
                    ((kspg_msg_t)(DWORD_PTR)kspg_tab[3].orig)(self, 0, msg);
                    klh_data((void *)((DWORD_PTR)KLH_VA(KSPG_CARRY) + slot), &keep, 1, "KLShopPage: owned byte restored");
                    kspg.trickOn = 1; kspg.trickRow = hi; kspg.trickSlot = slot;
                    if (kspg.log) klog("shopPage: row %d carried from the other set: owned check blanked for the dialog (slot %d, edit %d)", hi, slot, edit);
                    return;
                }
            }
        }
    }
    ((kspg_msg_t)(DWORD_PTR)kspg_tab[3].orig)(self, 0, msg);
    if (!strcmp(nm, "BuyWeapon")) kspg_note_buy(b0, b1);
}

/* ---- private vtables ---- */
static int kspg_pin(int c, DWORD vt)
{   /* copy the WHOLE vtable: slots up to the first non-code dword; refuse a hole or an oversize table (kllocname.c's rule) */
    char kind[9]; DWORD v; int n;
    if (klh_kind((const void *)KLH_VA(vt - 4), 8, kind) != 'r') return 0;
    for (n = 0; n < KSPG_MAXSLOT; n++) { v = klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * n)); if (!v || klh_kind((const void *)KLH_VA(v), 4, kind) != 'x') break; }
    if (n <= kspg_cslot[c] || n >= KSPG_MAXSLOT) return 0;
    /* k42: a null at slot n is the table's end pad; the NEXT class's RTTI locator (.rdata) and slot 0 (code) follow it. k40/k41 scanned n+1..n+4
     * for code and so refused 0xbbd18c (n 38), 0xbbcc84 (n 36) and 0xbbd494 (n 36), all [0][locator][code] (static read 2026-10-25): list rows,
     * picture and buy handler were never wrapped (live log 10-25 20:40). A real hole is code right after the null. */
    if (!klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * n)) && klh_kind((const void *)KLH_VA(klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * (n + 1)))), 4, kind) == 'x') return 0;
    kspg_tab[c].stock = vt; kspg_tab[c].n = n; kspg_tab[c].orig = klh_rd32((DWORD_PTR)KLH_VA(vt + 4 * kspg_cslot[c]));
    if (!klh_rd((DWORD_PTR)KLH_VA(vt - 4), kspg_tab[c].vt, 4 * (SIZE_T)(n + 1))) return 0;
    kspg_tab[c].vt[1 + kspg_cslot[c]] = (DWORD)(DWORD_PTR)(c == 0 ? (void *)kspg_text0 : c == 1 ? (void *)kspg_text1 : c == 2 ? (void *)kspg_gfx : (void *)kspg_sel);
    return 1;
}

static void kspg_setrole(DWORD obj, int role)
{
    int i; if (role == KR_NONE) return;
    for (i = 0; i < kspg_nrole; i++) if (kspg_role[i].obj == obj) { kspg_role[i].role = role; return; }
    if (kspg_nrole < KSPG_ROLES) { kspg_role[kspg_nrole].obj = obj; kspg_role[kspg_nrole].role = role; kspg_nrole++; }
}

static void kspg_scan(void)
{
    static struct { DWORD obj, kind; } tab[0x13e8]; static int told[KSPG_NCLS], dumped; int hits[KSPG_NCLS] = { 0 };
    DWORD gd = klh_rd32((DWORD_PTR)KLH_VA(0xdd265c)), mgr = gd ? klh_rd32(gd + 0x824) : 0, n, k; int c;
    if (!mgr || klh_rd32(mgr) != (DWORD)(DWORD_PTR)KLH_VA(0x00bb7dc8)) return;
    n = klh_rd32(mgr + 0x9f48);
    if (n > 0x13e8 || !klh_rd(mgr + 8, tab, 8 * (SIZE_T)n)) return;
    kspg.lastN = n;
    kspg_nrole = 0;                                           /* rebuilt on every scan: roles of elements the game dropped do not pile up */
    for (k = 0; k < n; k++) {
        DWORD vt, nv; char tag[40]; int role = KR_NONE;
        if (tab[k].kind || tab[k].obj < 0x10000 || !(vt = klh_rd32(tab[k].obj))) continue;
        for (c = 0; c < KSPG_NCLS && vt != kspg_cvt[c] && !(kspg_tab[c].n && vt == (DWORD)(DWORD_PTR)&kspg_tab[c].vt[1]); c++) ;
        if (c == KSPG_NCLS) continue;
        hits[c]++;
        if (kspg_tab[c].stock != vt && !kspg_tab[c].stock) { if (!kspg_pin(c, vt)) { if (told[c]++ < 2) klog("shopPage: vtable %08lx of class %d does not look like the one read: left alone", vt, c); continue; } }
        if (c == 2 || c == 0) {                                   /* tags: Graphic at [obj+0xb8], ShowInfo at [obj+0xc4] (char*) */
            klh_rdstr(klh_rd32(tab[k].obj + (c == 2 ? 0xb8 : 0xc4)), tag, sizeof tag);
            if (c == 2) role = !strcmp(tag, "WeaponBig") ? KR_BIG : !strcmp(tag, "PrimaryWeapon") ? KR_PRI : !strcmp(tag, "SecondaryWeapon") ? KR_SEC : KR_NONE;
            else role = !strcmp(tag, "OldPrimaryWeapon") ? KR_OLDPRI : !strcmp(tag, "OldSecondaryWeapon") ? KR_OLDSEC : KR_NONE;
            if (c == 2 && role == KR_NONE) continue;              /* other graphics: not wrapped */
        }
        kspg_setrole(tab[k].obj, role);
        nv = (DWORD)(DWORD_PTR)&kspg_tab[c].vt[1];
        if (vt == nv) continue;                                   /* already ours: role kept, nothing to write */
        if (klh_data((void *)(DWORD_PTR)tab[k].obj, &nv, 4, "KLShopPage: element vtable (private copy)") && kspg.log) klog("shopPage: element %08lx (class %d, role %d) wrapped", tab[k].obj, c, role);
    }
    if (kspg.log && dumped < 2 && klh_rd32((DWORD_PTR)KLH_VA(KSPG_MODE)) == 2) {   /* k42: proves whether list rows (1) and the buy handler (3) are in this table at all */
        dumped++;
        klog("shopPage: weapon list up, UI table n=%lu: ShowInfo %d, list rows %d, pictures %d, selector %d%s", n, hits[0], hits[1], hits[2], hits[3],
             hits[3] ? "" : " (no selector: page II buys hand over the stock gun)");
    }
}

/* ---- pool hand-over ---- */
static int kspg_isparked(DWORD o) { int i; for (i = 0; i < kspg.nparked; i++) if (kspg.parked[i] == o) return i + 1; return 0; }
static void kspg_unpark(int i1) { kspg.parked[i1 - 1] = kspg.parked[--kspg.nparked]; }

static int kspg_wantB(int row) { return (kspg.own[0] && kspg.carried[0] == row) || (kspg.own[1] && kspg.carried[1] == row); }

static int kspg_make(int row)
{   /* the objects of pair `row`, once: same recipe as kls_apply (klshop.c), but they start parked */
    DWORD a, n = 0, cap = 0, grow = 0, ents; void *tmpl, *self; int j;
    if (kspg.made[row][0]) return 1;
    if (!kls_vec(&a) || !klh_rd(a + 4, &n, 4) || !klh_rd(a + 8, &cap, 4) || !klh_rd(a + 0xc, &grow, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10))) return 0;
    if (!(self = (void *)(DWORD_PTR)klh_rd32(klh_rd32((DWORD_PTR)KLH_VA(KLS_UI)) + 0x15b0))) return 0;
    tmpl = ((kls_tmpl_t)KLH_VA(KLS_TEMPLATE))(self, 0, kspg.p[row].item);
    if (!tmpl) { if (kspg.p[row].fails++ < 3) klog("shopPage: item %d has no template in this level: row %d left as it is (tried again in 20 s, a later map may have it)", kspg.p[row].item, row); kspg.p[row].ok = 0; kspg.p[row].retry = GetTickCount() + 20000; return 0; }
    if (cap < n + KSPG_PER + 1) {
        DWORD ncap = n + KSPG_PER + 8; void *p;
        if (grow > 64) return 0;
        p = ((kls_realloc_t)(DWORD_PTR)klh_rd32((DWORD_PTR)KLH_VA(KLS_REALLOC)))((void *)(DWORD_PTR)ents, ncap * 12);
        if (!p) return 0;
        ents = (DWORD)(DWORD_PTR)p; cap = ncap;
        klh_data((void *)(DWORD_PTR)(a + 8), &cap, 4, "KLShopPage: pool capacity"); klh_data((void *)(DWORD_PTR)(a + 0x10), &ents, 4, "KLShopPage: pool array");
    }
    {   DWORD carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * row);
        for (j = 0; j < KSPG_PER; j++) {
            DWORD obj = (DWORD)(DWORD_PTR)((kls_maker_t)KLH_VA(KLS_MAKER))(self, 0, 0, tmpl), ent[3];
            if (!obj) break;
            ent[0] = obj; ent[1] = carrier; ent[2] = 0;                /* label = carrier's item; byte+8 = 0 (parked until wanted) */
            klh_data((void *)(DWORD_PTR)(ents + 12 * n), ent, 12, "KLShopPage: pool entry"); n++;
            kspg.made[row][j] = obj;
            if (kspg.nparked < KSPG_PARK) kspg.parked[kspg.nparked++] = obj;
        }
    }
    if (!j) { if (kspg.p[row].fails++ < 3) klog("shopPage: object maker returned nothing for item %d: row %d left as it is (tried again in 20 s)", kspg.p[row].item, row); kspg.p[row].ok = 0; kspg.p[row].retry = GetTickCount() + 20000; return 0; }
    klh_data((void *)(DWORD_PTR)(a + 4), &n, 4, "KLShopPage: pool count");
    klog("shopPage: row %d: %d objects of item %d added to the pool (parked until bought)", row, j, kspg.p[row].item);
    return 1;
}

/* k43 liveness guard: made[row][] is dropped (with its parked marks) when ANY of its objects is no longer an entry of the pool vector at its current
 * count. One read of the entry array per pass (kspg.sane is cleared by the tick), so the three readers below call it for free. */
static int kspg_ours(int row, DWORD o);
static void kspg_sane(void)
{
    static DWORD tab[4096 * 3]; DWORD a, n = 0, ents, i; int row, m, j;
    if (kspg.sane) return;
    kspg.sane = 1;
    for (row = 0; row < KSPG_ROWS && !kspg.made[row][0]; row++) ;
    if (row == KSPG_ROWS) return;                                 /* nothing of ours made */
    if (!kls_vec(&a) || !klh_rd(a + 4, &n, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10)) || !klh_rd(ents, tab, 12 * (SIZE_T)n)) {
        memset(kspg.made, 0, sizeof kspg.made); kspg.nparked = 0; kspg.preDone = 0; kspg.preTry = 0;      /* pool unreadable: trust nothing */
        klog("shopPage: the pool vector is unreadable: every extra gun pointer dropped, made again when needed");
        return;
    }
    for (row = 0; row < KSPG_ROWS; row++) {
        int dead = 0;
        if (!kspg.made[row][0]) continue;
        for (m = 0; m < KSPG_PER && kspg.made[row][m] && !dead; m++) {
            int alive = 0; for (i = 0; i < n && !alive; i++) alive = tab[3 * i] == kspg.made[row][m];
            if (!alive) dead = 1;
        }
        if (!dead) continue;
        for (j = 0; j < kspg.nparked; ) { int isours = kspg_ours(row, kspg.parked[j]); if (isours) kspg.parked[j] = kspg.parked[--kspg.nparked]; else j++; }
        memset(kspg.made[row], 0, sizeof kspg.made[row]); kspg.preDone = 0; kspg.preTry = 0;
        klog("shopPage: row %d: an extra gun is no longer in the pool (rebuilt): pointers dropped, made again when needed", row);
    }
}

static int kspg_ours(int row, DWORD o) { int m; for (m = 0; m < KSPG_PER; m++) if (kspg.made[row][m] == o) return 1; return 0; }

static void kspg_enforce(void)
{   /* only before the round: every entry of a pair's carrier is parked or free as the desired set says (see the header) */
    DWORD a, n = 0, ents, i; int row;
    kspg_sane();
    if (!kls_vec(&a) || !klh_rd(a + 4, &n, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10))) return;
    for (row = 0; row < KSPG_ROWS; row++) {
        DWORD carrier; int wantB;
        if (!kspg.p[row].ok) continue;
        wantB = kspg_wantB(row);
        if (!wantB && !kspg.made[row][0]) continue;
        if (wantB && !kspg.made[row][0]) {                                           /* fallback: PreMake=0, or the premake did not get this pair */
            static BYTE told[KSPG_ROWS];                                          /* once per row: a failing make retries every pass */
            if (kspg.log && !told[row]) { told[row] = 1; klog("shopPage: row %d was not premade: the extra guns are made now (fallback)", row); }
            if (!kspg_make(row)) continue;
        }
        if (!klh_rd(a + 4, &n, 4) || !(ents = klh_rd32(a + 0x10))) return;     /* the make may have grown it */
        carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * row);
        for (i = 0; i < n; i++) {
            DWORD e[3]; int ours, park, pi; BYTE v;
            if (!klh_rd(ents + 12 * i, e, 12) || e[1] != carrier || !e[0]) continue;
            ours = kspg_ours(row, e[0]);
            park = ours ? !wantB : wantB;                                  /* ours are parked while A is wanted, stock ones while B is */
            pi = kspg_isparked(e[0]);
            if (park && (e[2] & 0xff)) {                                   /* free but should be parked */
                v = 0; if (klh_data((void *)(DWORD_PTR)(ents + 12 * i + 8), &v, 1, "KLShopPage: park gun") && !pi && kspg.nparked < KSPG_PARK) kspg.parked[kspg.nparked++] = e[0];
            } else if (!park && pi && !(e[2] & 0xff)) {                    /* parked by us, wanted again */
                v = 1; if (klh_data((void *)(DWORD_PTR)(ents + 12 * i + 8), &v, 1, "KLShopPage: unpark gun")) kspg_unpark(pi);
            } else if (!park && pi && (e[2] & 0xff)) kspg_unpark(pi);
        }
    }
}

static int kspg_gate(void)
{
    DWORD sm, st = 0, gs, rules;
    if (!(sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION))) || klh_rd32(sm + 0x5c) != 4 || !klh_rd(sm + 0x70, &st, 4)) return 0;
    if (kl_online()) return 0;
    /* k43 review: no drop on the 0x23..0x25 -> 0x16 edge. The pool SURVIVES the round (klshop.c re-park, shop_more_guns.md S6): the round end only
       frees every gun again, and kspg_enforce re-parks ours in the next shop. Dropping made[] here leaked a fresh set per pair per round and left the
       old set unrecognised and free. A real rebuild (new map) is caught by kspg_sane, which checks every pointer against the pool. */
    if ((int)st != kspg.st) kspg.st = (int)st;
    gs = klh_rd32((DWORD_PTR)KLH_VA(KLS_SETTINGS)); rules = gs ? klh_rd32(gs + 0x54) : 0;
    if (!rules || klh_rd32(rules) != (DWORD)(DWORD_PTR)KLH_VA(KLS_RULES_VT)) return 0;
    /* 1 = a shop can be open, 2 = otherwise. The session runs 0x16 (first shop) -> 0x18 -> 0x19 (play) -> 0x1f (score) -> 0x20 (the shop
       between rounds) -> 0x23..0x25 -> 0x16; k40 took only st < 0x19, so the page key did nothing in the 0x20 shop (live log 10-25 20:32) */
    return (st < 0x19 || st == 0x20) ? 1 : 2;
}

/* pool rebuilt (new map)? then forget our objects (k43: kspg_sane checks every pointer, not just the first) */
static void kspg_check_pool(void) { kspg_sane(); }

/* k43 PreMake: the first shop (state < 0x19, the builder has run = the carrier has free stock entries, kls_apply's test) gets every pair's page B objects
 * made once, parked by kspg_make itself (byte+8 = 0, label = carrier). Retries per tick for ~20 s, then gives up (the make on demand stays the fallback). */
static void kspg_premake(void)
{
    DWORD a, n = 0, ents, i; int row, made = 0, wait = 0;
    if (!kspg.premake || kspg.preDone) return;
    if (!kls_vec(&a) || !klh_rd(a + 4, &n, 4) || n > 4096 || n < 8 || !(ents = klh_rd32(a + 0x10))) return;
    for (row = 0; row < KSPG_ROWS; row++) {
        DWORD carrier; int built = 0;
        if (!kspg.p[row].ok || kspg.made[row][0]) continue;
        carrier = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * row);
        if (!carrier) continue;
        for (i = 0; i < n && !built; i++) { DWORD e[3]; built = klh_rd(ents + 12 * i, e, 12) && e[1] == carrier && e[0] && (e[2] & 0xff); }
        if (!built) { wait++; continue; }
        if (kspg_make(row)) { made++; if (!klh_rd(a + 4, &n, 4) || !(ents = klh_rd32(a + 0x10))) return; } else wait++;
    }
    if (made && kspg.log) klog("shopPage: premade %d pair(s) in the first shop (parked): a page II buy only flips the pool entries", made);
    if (!wait || ++kspg.preTry > 80) {
        kspg.preDone = 1;
        if (wait) klog("shopPage: premake gave up on %d pair(s): they are made on demand in the shop (fallback)", wait);
    }
}

/* reserve ammo of a handed-over extra gun: the recipe of kls_ammo (klshop.c), for our objects */
static void kspg_ammo(void)
{
    DWORD a, n = 0, ents, i; int row, m;
    kspg_sane();
    for (row = 0; row < KSPG_ROWS && !kspg.made[row][0]; row++) ;
    if (row == KSPG_ROWS) return;                                 /* nothing of ours made: nothing to scan */
    if (kspg.clips <= 0 || !kls_vec(&a) || !klh_rd(a + 4, &n, 4) || n > 4096 || !(ents = klh_rd32(a + 0x10))) return;
    for (i = 0; i < n; i++) {
        DWORD e[3];
        if (!klh_rd(ents + 12 * i, e, 12) || !e[0] || (e[2] & 0xff)) continue;           /* only TAKEN objects */
        for (row = 0; row < KSPG_ROWS; row++) for (m = 0; m < KSPG_PER; m++) if (kspg.made[row][m] == e[0] && !kspg_isparked(e[0])) {
            DWORD rounds, res, ammo, r;
            static DWORD done[KSPG_ROWS * KSPG_PER]; int d = row * KSPG_PER + m;
            if (done[d] == e[0] || !klh_rd32(e[0] + 0xc4)) continue;
            done[d] = e[0];
            rounds = klh_rd32(e[0] + 0xdc) ^ KLS_AMMO_KEY; res = klh_rd32(e[0] + 0xe0) ^ KLS_AMMO_KEY;
            ammo = klh_rd32((DWORD_PTR)KLH_VA(KLS_SHOP) + 24 * row + 4);
            if (res || !rounds || rounds > 999 || rounds < ammo) continue;
            r = rounds * (DWORD)kspg.clips; if (r > 600) r = 600;
            r ^= KLS_AMMO_KEY;
            klh_data((void *)(DWORD_PTR)(e[0] + 0xe0), &r, 4, "KLShopPage: reserve ammo");
        }
    }
}

/* ---- ini ---- */
static int kspg_load(void)
{
    char file[MAX_PATH], *s, buf[520], key[16]; int i, n, ok = 0;
    strncpy(file, klh_ini, MAX_PATH - 20); file[MAX_PATH - 21] = 0;
    s = strrchr(file, 0x5c); if (!s) s = strrchr(file, '/');
    if (!s) return 0;
    strcpy(s + 1, "KLShopPage.ini");
    n = (int)GetPrivateProfileIntA("Pairs", "Count", 0, file);
    if (n < 0 || n > KSPG_ROWS) n = 0;
    for (i = 0; i < n; i++) {
        int row = -1, item = 0, pic = -1, c = 0; char *q, *d;
        snprintf(key, sizeof key, "P%d", i);
        GetPrivateProfileStringA("Pairs", key, "", buf, sizeof buf, file);
        if (sscanf(buf, "%d|%d|%d|%n", &row, &item, &pic, &c) < 3 || !c || row < 0 || row >= KSPG_ROWS || item < 1 || item > 63) { klog("shopPage: %s %s not row|item|pic|name: skipped", file, key); continue; }
        q = buf + c; strncpy(kspg.p[row].name, q, 47); kspg.p[row].name[47] = 0;
        snprintf(key, sizeof key, "D%d", i);
        GetPrivateProfileStringA("Desc", key, "", buf, sizeof buf, file);
        for (q = d = buf; *q; q++) { if (q[0] == '\\' && q[1] == 'n') { *d++ = '\n'; q++; } else *d++ = *q; } *d = 0;
        strncpy(kspg.p[row].desc, buf, 479); kspg.p[row].desc[479] = 0;
        kspg.p[row].row = row; kspg.p[row].item = item; kspg.p[row].pic = pic; kspg.p[row].ok = kspg.p[row].cfg = 1; ok++;
    }
    return ok;
}

static void kspg_init(void)
{
    kspg.on = GetPrivateProfileIntA("ShopPage", "Enable", 0, klh_ini) != 0;
    if (!kspg.on) return;
    kspg.key = (int)GetPrivateProfileIntA("ShopPage", "Key", 0x75, klh_ini);
    if (kspg.key < 1 || kspg.key > 0xfe) kspg.key = 0x75;
    kspg.trick = GetPrivateProfileIntA("ShopPage", "OwnedTrick", 1, klh_ini) != 0;
    kspg.log = GetPrivateProfileIntA("ShopPage", "Log", 1, klh_ini) != 0;
    kspg.hint = GetPrivateProfileIntA("ShopPage", "Hint", 1, klh_ini) != 0;
    kspg.clips = GetPrivateProfileIntA("ShopPage", "ReserveClips", 2, klh_ini);
    kspg.premake = GetPrivateProfileIntA("ShopPage", "PreMake", 1, klh_ini) != 0;       /* k43 (recommended on): make the page B guns in the first shop */
    kspg.have = kspg_load();
    if (!kspg.have) { klog("shopPage: on, but KLShopPage.ini has no pairs: nothing is done"); kspg.on = 0; return; }
    kspg.carried[0] = kspg.carried[1] = -1;
    klog("shopPage: on; %d pairs from KLShopPage.ini; key 0x%02x flips the shop between set A and set B (Arcade offline only)", kspg.have, kspg.key);
}

static void klshoppage_tick(int game_thread)
{
    DWORD now, w; int g, s, i;
    static SHORT (WINAPI *gaks)(int); static HWND (WINAPI *fgw)(void); static DWORD (WINAPI *wtp)(HWND, LPDWORD); static int looked;
    static DWORD lastfull;
    if (!kspg.on || !game_thread || !klh_exe_ok) return;
    now = GetTickCount();
    if (!looked) {
        HMODULE u = GetModuleHandleA("user32.dll"); looked = 1;
        if (u) { gaks = (SHORT (WINAPI *)(int))GetProcAddress(u, "GetAsyncKeyState"); fgw = (HWND (WINAPI *)(void))GetProcAddress(u, "GetForegroundWindow"); wtp = (DWORD (WINAPI *)(HWND, LPDWORD))GetProcAddress(u, "GetWindowThreadProcessId"); }
        if (!gaks || !fgw || !wtp) klog("shopPage: user32's key functions not found: the page key is not read");
    }
    /* the key is read on every tick (a short press is missed at 4 Hz); edge detection (up -> down); only in the weapon list (mode 2) before the round */
    if (gaks && fgw && wtp) {
        int down = (gaks(kspg.key) & 0x8000) != 0;
        if (down && !kspg.keyDown && !kspg.pre && kspg.log && now - kspg.lastKey > 150 && klh_rd32((DWORD_PTR)KLH_VA(KSPG_MODE)) == 2) {
            DWORD sm = klh_rd32((DWORD_PTR)KLH_VA(KLS_SESSION));   /* the weapon list is up but the gate says no shop: say so (k40 was silent here) */
            kspg.lastKey = now;
            klog("shopPage: key pressed in the weapon list, but session state 0x%lx is not a shop state: ignored", sm ? klh_rd32(sm + 0x70) : 0);
        }
        if (down && !kspg.keyDown && kspg.pre && now - kspg.lastKey > 150) {
            DWORD pid = 0; HWND f = fgw(); if (f) wtp(f, &pid);
            if (pid == GetCurrentProcessId()) {
                DWORD mode = klh_rd32((DWORD_PTR)KLH_VA(KSPG_MODE));
                kspg.lastKey = now;
                if (mode == 2) {
                    kspg.shownB = !kspg.shownB; kspg.togglePend = 1; kspg.txtSeen = 0; kspg.toggleAt = now;
                    if (kspg.log) klog("shopPage: shop now shows set %c (mode %lu, highlighted row %d, category %d, slot %d)", kspg.shownB ? 'B' : 'A', mode,
                                       (int)klh_rd32((DWORD_PTR)KLH_VA(KSPG_SHOWN_ROW)), (int)klh_rd32((DWORD_PTR)KLH_VA(0x00ced640)), (int)klh_rd32((DWORD_PTR)KLH_VA(KSPG_EDIT)));
                } else if (kspg.log) klog("shopPage: key pressed but the shop mode is %lu, not 2 (weapon list): ignored", mode);
            }
        }
        kspg.keyDown = down;
    }
    if (kspg.togglePend && now - kspg.toggleAt > 1500) {
        kspg.togglePend = 0;
        if (!kspg.txtSeen && kspg.log) klog("shopPage: WARNING no shop text was requested in 1.5 s after the toggle: the names may stay as they were until the cursor moves (the game may cache them)");
    }
    if (now - kspg.lastScan < 250) return;
    kspg.lastScan = now; kspg.sane = 0;
    g = kspg_gate();
    kspg.pre = (g == 1);
    if (!g) { kspg.active = 0; kspg.shownB = 0; return; }
    if (g == 2 && kspg.shownB) { kspg.shownB = 0; if (kspg.log) klog("shopPage: the round runs: page back to set A"); }
    for (i = 0; i < KSPG_ROWS; i++) if (kspg.p[i].cfg && !kspg.p[i].ok && kspg.p[i].retry && now > kspg.p[i].retry) { kspg.p[i].retry = 0; kspg.p[i].ok = 1; }
    if (!kls_code_ok()) { if (!kspg.told++) klog("shopPage: code of the object maker / template lookup is not as read: nothing done"); kspg.active = 0; return; }
    if (kls.on) for (i = 0; i < KSPG_ROWS; i++) if (kspg.p[i].ok) for (s = 0; s < kls.n; s++) if (kls.row[s] == i) { kspg.p[i].ok = 0; kspg.p[i].retry = 0; klog("shopPage: row %d is swapped by [Shop] Swap: no page II for it", i); }
    /* carried rows: a change nobody bought (round reset, other mod) resets that slot to set A. k42 fallback: a change while the weapon list was up
     * in the shop (mode 2 now or < 2 s ago) counts as a purchase from the page on screen, for when the selector is not wrapped (kspg_sel already
     * moved carried[] when it is, so this cannot count a buy twice). GUESS: only 0x6ddd10 (BuyWeapon) changes 0xced638/9 while the list is up. */
    w = klh_rd32((DWORD_PTR)KLH_VA(KSPG_CARRY));
    if (g == 1 && klh_rd32((DWORD_PTR)KLH_VA(KSPG_MODE)) == 2) kspg.listAt = now;
    for (s = 0; s < 2; s++) {
        int cur = (int)(signed char)(BYTE)(w >> (8 * s));
        if (cur == kspg.carried[s]) continue;
        if (g == 1 && kspg.listAt && now - kspg.listAt < 2000) {
            kspg.own[s] = kspg.shownB && cur >= 0 && cur < KSPG_ROWS && kspg.p[cur].ok;
            if (kspg.log) klog("shopPage: slot %d now carries row %d from set %c (seen by polling: the buy handler is not wrapped)", s, cur, kspg.own[s] ? 'B' : 'A');
        } else { if (kspg.own[s] && kspg.log) klog("shopPage: slot %d carried row changed %d -> %d without a purchase seen: set A assumed", s, kspg.carried[s], cur); kspg.own[s] = 0; }
        kspg.carried[s] = cur;
    }
    kspg.active = 1;
    if (now - lastfull > 1500) { lastfull = now; kspg_scan(); }
    if (g == 1) { kspg_check_pool(); if (kspg.st < 0x19) kspg_premake(); kspg_enforce(); }
    kspg_ammo();
}

#endif /* KLSHOPPAGE_C */
