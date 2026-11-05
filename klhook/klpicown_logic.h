/* klpicown_logic.h - pure decision for [Hire] BakedPics / [ShopPage] OwnPics (2026-11-05). No windows.h. Used by klshoppage.c (kspg_gfx, kspg_scan) and klpicown_test.c.
 *
 * tools/kl_shop_pics.py bakes 36 EXTRA big-picture elements into the level's Menu/online.xml (template FAWeaponGraphicBig, same tag "WeaponBig" as the stock
 * ones) with their own pictures: PlayerIndex 100..115 = the 16 heister cards (KLChar 1..16), 120..139 = the Page II cards (KLShopPage.ini slot P0..P19).
 * A picture element draws when its PlayerIndex equals the shown row. So the hook shows the one wanted card by giving its element the shown row for one
 * update (element-private swap and restore, the same data-only trick as every other picture here) and hides the stock card (index 99 = no row).
 * Fails open: a card whose element the scan did not find (map not baked) is never wanted, the stock behaviour stays. Constants are the same as
 * kl_shop_pics.py (HIRE_BASE, PAIR_BASE, ...): kl_shop_pics_test.py compares them. */
#ifndef KLPICOWN_LOGIC_H
#define KLPICOWN_LOGIC_H

#define KPO_HIRE_BASE 100
#define KPO_N_HIRE    16
#define KPO_PAIR_BASE 120
#define KPO_N_PAIR    20
#define KPO_HIDE      99          /* the PlayerIndex that matches no row (as the hire page's hidden card) */

static int kpo_is_own(int idx) { return idx >= KPO_HIRE_BASE && idx < KPO_PAIR_BASE + KPO_N_PAIR && !(idx >= KPO_HIRE_BASE + KPO_N_HIRE && idx < KPO_PAIR_BASE); }

/* bit of own index idx in the scan mask (two DWORDs: idx - 100 = 0..39) */
static void kpo_mask_set(unsigned long m[2], int idx) { if (kpo_is_own(idx)) m[(idx - KPO_HIRE_BASE) >> 5] |= 1ul << ((idx - KPO_HIRE_BASE) & 31); }
static int  kpo_mask_has(const unsigned long m[2], int idx) { return kpo_is_own(idx) && ((m[(idx - KPO_HIRE_BASE) >> 5] >> ((idx - KPO_HIRE_BASE) & 31)) & 1); }

/* the own index to show now, or -1 (stock look).
 * hire_up: the hire page is on screen and [Hire] BakedPics=1; ch: the highlighted heister 1..16 (0 = a row that is not a heister);
 * pg2_up: a Page II gun is shown and [ShopPage] OwnPics=1; slot: its KLShopPage.ini slot 0..19 (-1 = none). mask: the own elements the scan found. */
static int kpo_want(int hire_up, int ch, int pg2_up, int slot, const unsigned long mask[2])
{
    int w = -1;
    if (hire_up && ch >= 1 && ch <= KPO_N_HIRE) w = KPO_HIRE_BASE + ch - 1;
    else if (!hire_up && pg2_up && slot >= 0 && slot < KPO_N_PAIR) w = KPO_PAIR_BASE + slot;
    return (w >= 0 && kpo_mask_has(mask, w)) ? w : -1;
}

/* the PlayerIndex a WeaponBig element should have for one update; -1 = leave it. idx = its own index now, shown = the shown row, want = kpo_want().
 * The wanted own element gets the shown row (it draws); the stock elements get 99 while a card is wanted (they would draw the carrier's picture). */
static int kpo_big_index(int idx, int shown, int want)
{
    if (want < 0) return -1;
    if (kpo_is_own(idx)) return idx == want ? shown : -1;
    return idx == KPO_HIDE ? -1 : KPO_HIDE;
}

#endif
