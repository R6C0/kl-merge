/* klcampaign_outfits_logic.h - [Wardrobe] CampaignOutfits: the campaign outfits (KLChar 17 ..) of tools\kl_outfits_1110.py.
 * Pure logic (no windows.h): klchar.c includes it, klcampaign_outfits_test.c tests it.
 *
 * The wardrobe table grew from 16 to 32 characters (KLC_NCHAR). Characters 17.. are Dead Men campaign models dressed like a
 * Dog Days heister (one body, face / own mask / 8 stock masks / Payday 2 plates) that take a crew slot 0..7, so klchar.c's
 * look code needs nothing new: a character is a name, a root and a slot.
 * Toggle (KLHook.ini [Wardrobe] CampaignOutfits, default 1, "(recommended on)"): off = the table is cut to the first 16
 * characters, so a KLWardrobe.ini written with campaign outfits behaves exactly like the old one (no random crew pick, no
 * KLChar above 16). */
#ifndef KLCAMPAIGN_OUTFITS_LOGIC_H
#define KLCAMPAIGN_OUTFITS_LOGIC_H

#define KCO_BASE 16                 /* the Dog Days heisters + the eight Dead Men Fragile Alliance heroes */

/* characters the table keeps: -1 = the ini names more than `nmax` (refuse the wardrobe, as before), else n, or KCO_BASE when off */
static int kco_chars(int n, int campaign, int nmax)
{
    if (n < 1 || n > nmax) return -1;
    return (!campaign && n > KCO_BASE) ? KCO_BASE : n;
}

/* the KLChar that is used: 0 (the game's own) for a value out of range or above the base while the toggle is off */
static int kco_clamp(int ch, int campaign, int nmax)
{
    if (ch < 0 || ch > nmax) return 0;
    if (!campaign && ch > KCO_BASE) return 0;
    return ch;
}

/* the highest KLChar the Heister page may set: nmax with the toggle on, KCO_BASE (16) off */
static int kco_upper(int campaign, int nmax) { return campaign ? nmax : KCO_BASE; }

/* a pick above what the loaded map's KLWardrobe.ini holds (`have` characters, kco_chars) is the game's own body (0), never an index past the table:
   the Heister page is one list for all maps, the characters per map are 1..16 (kl_outfits_1110 fits what the .prm can hold) */
static int kco_pick(int ch, int campaign, int nmax, int have)
{
    ch = kco_clamp(ch, campaign, nmax);
    return (ch > have || ch > nmax) ? 0 : ch;
}

/* the first campaign character: KLChar 17 is table entry 16 */
static int kco_is_campaign(int ch) { return ch > KCO_BASE; }

#endif
