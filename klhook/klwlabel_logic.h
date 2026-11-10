/*
 * klwlabel_logic.h - PURE part of the wardrobe labels (patch "wardrobe", owner 11-07: 'label the outfit categories more clearly bc if they want to find
 * dead men its not too obvious on how to get there'; NOT RUN IN THE GAME; no windows.h, tested off game by klwlabel_test.c).
 *
 * The three wardrobe lists (klchar.c KLChar 0..16, KLMask 0..13, KLOutfit 0..23) turned into GROUPS (DOG DAYS / DEAD MEN / PAYDAY 2) and the text
 * "n/N  GROUP: Name" that klcharonline.c shows on the F9 / F11 announce line and that mkoverlay.py --labels bakes into the Heister page. kwl_next_group()
 * gives the Ctrl+F9 / Ctrl+F11 jump (first entry of the next / previous group, wrapping). The name tables repeat klchar.c / mkoverlay.py / kl_chars.py
 * (klco_names, MASK_LOOKS, DM_ARMOUR...): klwlabel_test.c pins the counts, and mkoverlay.py --labels prints the same strings (compared once by hand, see
 * re/wardrobe.md 'labels').
 */
#ifndef KLWLABEL_LOGIC_H
#define KLWLABEL_LOGIC_H
#include <stdio.h>
#include <string.h>

enum { KWL_CHAR = 0, KWL_MASK = 1, KWL_OUTFIT = 2 };           /* the same numbers as klchar.c klc_value[] / klc_keys[] */
enum { KWL_G_DEFAULT = 0, KWL_G_DOGDAYS, KWL_G_DEADMEN, KWL_G_PD2, KWL_G_CAMPAIGN };
#define KWL_NCHAR   33     /* klchar.c KLC_NCHAR + 1 (1110: 16 -> 32 with the 16 campaign outfits, tools\kl_outfits_1110.py SPECS) */
#define KWL_NMASK   14     /* KLC_MASKS + 2 */
#define KWL_NOUTFIT 24     /* KLC_OUTFITS */

static const char *const kwl_gname[5] = { "DEFAULT", "DOG DAYS", "DEAD MEN", "PAYDAY 2", "CAMPAIGN" };

static const char *const kwl_chars[KWL_NCHAR] = { "Game default", "J.C.", "Tommy", "Pierre", "Liam", "Jean", "Elwood", "Bud", "Mitchel",
                                                  "Kane", "Lynch", "Ashkanan", "Meldal", "Red", "Parker", "Standen", "Hutchison",
                                                  /* 17..32: tools\kl_outfits_1110.py SPECS menu names, in order (mkoverlay.py CAMPAIGN_CHARS is the twin) */
                                                  "Kane - window cleaner (Retomoto)", "Lynch - window cleaner (Retomoto)", "Vaultbreaker",
                                                  "Shelly - window cleaner", "Rific - window cleaner", "Thapa - window cleaner",
                                                  "Carlos", "Lion (Elder Brother)", "Flame (Little Brother)",
                                                  "Mute (the Doctor)", "Fuentes", "Kane - bust-out",
                                                  "Lynch - bust-out", "Kane - bank", "Lynch - bank",
                                                  "Retomoto boss" };
static const char *const kwl_mask_look[8] = { "Moustache", "Black beard", "Red opera", "Orange face", "Skull", "Porcelain doll", "Red and white opera", "Blue opera" };
static const char *const kwl_pd2_mask[4] = { "Wolf", "Dallas", "Chains", "Hoxton" };
static const char *const kwl_armour[4] = { "Plain clothes", "Light vest", "Tactical vest", "Heavy armour" };
static const char *const kwl_shirt[2] = { "", "black shirt" };
static const char *const kwl_head[3] = { "", "dark balaclava", "black balaclava" };

static int kwl_span(int which) { return which == KWL_CHAR ? KWL_NCHAR : which == KWL_MASK ? KWL_NMASK : which == KWL_OUTFIT ? KWL_NOUTFIT : 0; }

/* v + step wrapped into 0..span-1 (Shift = step -1: 0 -> span-1) */
static int kwl_wrap(int v, int step, int span)
{
    if (span <= 0) return 0;
    return ((v + step) % span + span) % span;
}

/* which group entry idx of list `which` belongs to (KWL_G_*); out-of-range idx -> KWL_G_DEFAULT */
static int kwl_group(int which, int idx)
{
    if (idx < 0 || idx >= kwl_span(which)) return KWL_G_DEFAULT;
    if (which == KWL_CHAR) return idx == 0 ? KWL_G_DEFAULT : idx <= 8 ? KWL_G_DOGDAYS : idx <= 16 ? KWL_G_DEADMEN : KWL_G_CAMPAIGN;     /* 9 Kane and 10 Lynch are Dead Men bodies too */
    if (which == KWL_MASK) return idx <= 1 ? KWL_G_DEFAULT : idx <= 9 ? KWL_G_DOGDAYS : KWL_G_PD2;         /* 0 Game option, 1 No mask | 2..9 the 8 stock looks | 10..13 Payday 2 */
    return KWL_G_DEADMEN;                                                                                   /* outfits: Dead Men bodies only */
}

static const char *kwl_group_name(int which, int idx) { return kwl_gname[kwl_group(which, idx)]; }

/* the bare name of an entry (no counter, no group); "?" when out of range */
static void kwl_name(int which, int idx, char *out, int cap)
{
    if (cap <= 0) return;
    out[0] = 0;
    if (idx < 0 || idx >= kwl_span(which)) { snprintf(out, cap, "?"); return; }
    if (which == KWL_CHAR) snprintf(out, cap, "%s", kwl_chars[idx]);
    else if (which == KWL_MASK) {
        if (idx == 0) snprintf(out, cap, "Game option");
        else if (idx == 1) snprintf(out, cap, "No mask");
        else if (idx <= 9) snprintf(out, cap, "%s (%s)", kwl_mask_look[idx - 2], kwl_chars[idx - 1]);       /* the heister who wears it in the stock game: J.C. .. Mitchel */
        else snprintf(out, cap, "%s", kwl_pd2_mask[idx - 10]);
    } else {                                                                                                  /* tools\kl_chars.py outfit_name: armour (0..3) + 4 * shirt + 8 * head */
        int a = idx % 4, sh = idx / 4 % 2, hd = idx / 8;
        snprintf(out, cap, "%s%s%s%s%s", kwl_armour[a], kwl_shirt[sh][0] ? ", " : "", kwl_shirt[sh], kwl_head[hd][0] ? ", " : "", kwl_head[hd]);
    }
}

/* "n/N  GROUP: Name" (n is 1-based); the DEFAULT group has no tag: "1/17  Game default". Out of range: "?/N  ?" */
static void kwl_label(int which, int idx, char *out, int cap)
{
    char nm[64]; int span = kwl_span(which);
    if (cap <= 0) return;
    kwl_name(which, idx, nm, sizeof nm);
    if (idx < 0 || idx >= span) { snprintf(out, cap, "?/%d  ?", span); return; }
    if (kwl_group(which, idx) == KWL_G_DEFAULT) snprintf(out, cap, "%d/%d  %s", idx + 1, span, nm);
    else snprintf(out, cap, "%d/%d  %s: %s", idx + 1, span, kwl_group_name(which, idx), nm);
}

/* the announce line: "HEISTER 10/17  DEAD MEN: Kane", "MASK 11/14  PAYDAY 2: Wolf  (Ctrl+key: outfit)", "OUTFIT 5/24  DEAD MEN: ...  (key: mask)";
   the two trailing hints are the ones of the old bare-number text */
static void kwl_hud(int which, int idx, char *out, int cap)
{
    char l[100];
    if (cap <= 0) return;
    kwl_label(which, idx, l, sizeof l);
    snprintf(out, cap, "%s %s%s", which == KWL_CHAR ? "HEISTER" : which == KWL_MASK ? "MASK" : "OUTFIT", l,
             which == KWL_MASK ? "  (Ctrl+key: outfit)" : which == KWL_OUTFIT ? "  (key: mask)" : "");
}

/* the entry that starts the group after (dir > 0) or before (dir < 0) idx's group, wrapping; the same idx when the list has one group (outfits) */
static int kwl_next_group(int which, int idx, int dir)
{
    int span = kwl_span(which), g, i, j;
    if (span <= 0) return 0;
    if (idx < 0 || idx >= span) idx = 0;
    g = kwl_group(which, idx);
    if (dir >= 0) {                                                  /* forward: the first entry after the current group's run (the groups are contiguous) */
        for (i = 1; i <= span; i++) { j = (idx + i) % span; if (kwl_group(which, j) != g) return j; }
        return idx;
    }
    /* backward: the first entry of the group before the current one */
    for (i = 1; i <= span; i++) {
        j = ((idx - i) % span + span) % span;
        if (kwl_group(which, j) != g) {                              /* j is the last entry of the previous group: walk to its start */
            int pg = kwl_group(which, j);
            while (j > 0 && kwl_group(which, j - 1) == pg) j--;
            return j;
        }
    }
    return idx;
}

#endif /* KLWLABEL_LOGIC_H */
