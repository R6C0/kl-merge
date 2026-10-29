/* klswappic.h - pure decision for [Shop] OnlineSwapPic (wk-swappic-1028). No windows.h. Used by klshoppage.c (kspg_gfx) and klswappic_test.c.
 *
 * On an UNBAKED map (stock F01-F09, DM07, DD10) the shop rows 13/16/32/35 are the carrier guns (TOQ, Buqiang 300, 800, 900); when the pool hands over HK69 / Type 81 /
 * Rem 700 / Minimi the name can follow ([Shop] OnlineSwapText=2) but the .TEX holds no card of those guns. The only thing a hook can do is show the card of another stock
 * row that looks like it. The look-alike rows below are GUESSES carried over from tools/kl_shop_sets.py ITEMS (never seen live):
 *   HK69 (item 52) -> row 14, Type 81 (33) -> row 30, Rem 700 (49) -> row 32, Minimi (47) -> row 32.
 * The result P is the stock row whose card to show in place of row R; -1 = leave the picture alone. */
#ifndef KLSWAPPIC_H
#define KLSWAPPIC_H

/* item handed over by the pool (kls_row_state == 2) -> look-alike picture row, or -1 */
static int ksp_lookalike(int item)
{
    return item == 52 ? 14 : item == 33 ? 30 : item == 49 ? 32 : item == 47 ? 32 : -1;
}

/* R = the row the element would show (shown row for the big card, carried row for the small one); state/item = kls_row_state(R, &item);
 * unbaked = the name lookup of R saw the stock text (a baked map's name already matches its card: never replace it). */
static int ksp_pic_row(int on, int online, int R, int state, int item, int unbaked)
{
    int P;
    if (!on || R < 0) return -1;
    if (!(R == 13 || R == 16 || R == 32 || R == 35)) return -1;
    if (state != 2 || !unbaked) return -1;          /* only when ours is handed over over an unbaked card */
    (void)online;                                    /* Arcade needs it as much as online: the unbaked card is the carrier's in both */
    P = ksp_lookalike(item);
    if (P < 0 || P == R) return -1;                  /* row 32 already shows its own scoped rifle: nothing to do */
    return P;
}

/* the PlayerIndex the element gets for ONE update: the element of row R shows the card of row P, the element of row P shows R's (hidden), the rest stay */
static int ksp_new_index(int idx, int R, int P)
{
    if (P < 0) return idx;
    if (idx == R) return P;
    if (idx == P) return R;
    return idx;
}

#endif
