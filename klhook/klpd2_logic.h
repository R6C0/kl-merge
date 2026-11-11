/* klpd2_logic.h - pure decisions of the master switch [Payday2] Enable (2026-11-11, owner: "most people wont have payday 2 installed ... a setting somewhere
 * that enables that on or off in game"). No windows.h; tested by klpd2_test.c.
 * The switch hides the PAYDAY 2 CHOICES of the hook; it removes no file (the release ships the PD2-derived bytes to everyone):
 *   - wardrobe masks: KLMask 10..13 are the four PD2 face plates (klchar.c KLC_MASKS 12 = 8 Dog Days masks + 4 PD2). Off: skipped when cycling, a saved one acts as 0.
 *   - shop page II (klshoppage.c, [ShopPage] Enable + KLShopPage.ini [Pairs]): its 13 rows are PD2 guns. Off: the page is not offered.
 *   - the jukebox ([Music] Enable) plays Payday 2's own music files.
 * Missing key = ON (the behaviour before the switch existed). */
#ifndef KLPD2_LOGIC_H
#define KLPD2_LOGIC_H

#define KP2_MASK_FIRST 10      /* first Payday 2 plate in the KLMask value space (0 game, 1 none, 2..9 heister masks, 10..13 PD2) */
#define KP2_MASK_LAST  13

/* raw = GetPrivateProfileInt("Payday2","Enable",-1,...): -1 = key missing = on */
static int kp2_enabled(int raw) { return raw < 0 ? 1 : raw != 0; }
static int kp2_is_mask(int v) { return v >= KP2_MASK_FIRST && v <= KP2_MASK_LAST; }
/* a saved / announced mask value as it acts */
static int kp2_mask_eff(int v, int on) { return (on || !kp2_is_mask(v)) ? v : 0; }
/* the Heister page's spinner passed `v` (a mask value) while the choice was `cur`: with PD2 off a plate value is replaced so the spinner never rests on one.
   cur 0 = it came round from below (step back from 0 to the last non-PD2 mask 9), else it stepped past 9 (round to 0) */
static int kp2_mask_menu(int cur, int v, int on)
{
    if (on || !kp2_is_mask(v)) return v;
    return cur == 0 ? KP2_MASK_FIRST - 1 : 0;
}
/* the F11 key: keep stepping (step +1 / -1) over the span (values 0..span-1) until a non-PD2 value */
static int kp2_mask_key(int v, int step, int span, int on)
{
    int n = 0;
    if (on || span <= 0) return v;
    while (kp2_is_mask(v) && n++ < span) v = ((v + step) % span + span) % span;
    return v;
}
/* shop page II: the PD2 set is the default (no [Set] Name or "pd2"); a differently named set (e.g. a Dead Men fallback set) is not PD2 content */
static int kp2_set_is_pd2(const char *name)
{
    const char *p = "pd2"; int i;
    if (!name || !name[0]) return 1;
    for (i = 0; i < 3; i++) { char c = name[i]; if (c >= 'A' && c <= 'Z') c = (char)(c + 32); if (c != p[i]) return 0; }
    return name[3] == 0 || name[3] == ' ' || name[3] == '_' || name[3] == '-';
}
static int kp2_page2_on(int shopEnable, int on, const char *setName) { return shopEnable && (on || !kp2_set_is_pd2(setName)); }
static int kp2_music_on(int musicEnable, int on) { return musicEnable && on; }

#endif
