/*
 * klhirepic.h - the PURE part of the hire-page pictures (klhirepic.c, [Hire] PagePics): which heister the highlighted row is, where the big picture box sits on
 * the screen, the image file name and header check, the gate. No Windows, no game: tested off-game by klhirepic_test.c.
 */
#ifndef KLHIREPIC_H
#define KLHIREPIC_H

#include <string.h>

/* shop row -> KLChar 1..16, 0 = no heister. The SAME table as klshoppage.c kspg_h_ch (re/shop_hire.md section 9): Pistols tab rows 0..7 = Dog Days crew
 * (KLChar 1..8), SMGs tab rows 17..24 = Dead Men crew (KLChar 9..16). */
static int khp_char_of_row(int row)
{
    if (row >= 0 && row <= 7) return row + 1;
    if (row >= 17 && row <= 24) return row - 17 + 9;
    return 0;
}

/* KLChar -> image file name 'char_01.kmi' (tools/kl_portraits.py gray writes the same names); cap >= 12 */
static void khp_file(int ch, char *out, int cap)
{
    if (cap < 12) { if (cap > 0) out[0] = 0; return; }
    if (ch < 1) ch = 1;
    if (ch > 16) ch = 16;
    out[0] = 'c'; out[1] = 'h'; out[2] = 'a'; out[3] = 'r'; out[4] = '_'; out[5] = (char)('0' + ch / 10); out[6] = (char)('0' + ch % 10);
    out[7] = '.'; out[8] = 'k'; out[9] = 'm'; out[10] = 'i'; out[11] = 0;
}

/* The picture box of the weapon / hire page in back-buffer pixels. online.xml (Window FABuyWeaponsNew): the ScreenBaseSize group is 768 x 576 centred; the
 * picture group inside it is X=432 Y=60 W=445 H=210. The menu's virtual screen is 1280 x 720 stretched over the whole back buffer (as the HUD, re/hud.md):
 * the group's origin is ((1280-768)/2, (720-576)/2) = (256, 72), the box (688, 132, 445, 210) virtual.
 * MEASURED on the 640 x 480 shot research/shots/SHOP1_386s.png: card x 344..567, y 88..228 = 688 * 0.5, 132 * 0.667 ... (688+445) * 0.5, (132+210) * 0.667: exact.
 * GUESS: the same rule at 16:9 and larger (the stretch is aspect independent in the HUD; no shop shot at 1280 x 720 or 2560 x 1440 was found to check). */
#define KHP_VW 1280.0f
#define KHP_VH 720.0f
#define KHP_BX 688.0f
#define KHP_BY 132.0f
#define KHP_BW 445.0f
#define KHP_BH 210.0f
static void khp_box(float sw, float sh, float *x, float *y, float *w, float *h)
{
    float sx = sw / KHP_VW, sy = sh / KHP_VH;
    *x = KHP_BX * sx; *y = KHP_BY * sy; *w = KHP_BW * sx; *h = KHP_BH * sy;
}

/* the gate (game thread): the hire page is up (not the controls page), the shop gate is open, the list is the weapon list (mode 2); -> the KLChar to draw or 0 */
static int khp_want(int hire, int ctl, int hact, unsigned mode, int row)
{
    if (!hire || ctl || !hact || mode != 2) return 0;
    return khp_char_of_row(row);
}

/* a snapshot is fresh when the game thread wrote it within maxms (wrap-safe unsigned tick arithmetic) */
static int khp_fresh(unsigned now, unsigned at, unsigned maxms) { return at != 0 && (unsigned)(now - at) <= maxms; }

/* 'KMI1', u32 w, u32 h, w * h * 4 bytes (B, G, R, A), w and h 1..512 (the same file as the map pool's thumbnails, klmappool_ov.c) -> 1 when the n bytes are a valid image */
static int khp_kmi_ok(const unsigned char *b, unsigned n, unsigned *w, unsigned *h)
{
    unsigned iw, ih;
    if (n < 12 || memcmp(b, "KMI1", 4)) return 0;
    iw = (unsigned)b[4] | (unsigned)b[5] << 8 | (unsigned)b[6] << 16 | (unsigned)b[7] << 24;
    ih = (unsigned)b[8] | (unsigned)b[9] << 8 | (unsigned)b[10] << 16 | (unsigned)b[11] << 24;
    if (iw < 1 || ih < 1 || iw > 512 || ih > 512 || n != 12 + iw * ih * 4) return 0;
    if (w) *w = iw;
    if (h) *h = ih;
    return 1;
}

#endif
