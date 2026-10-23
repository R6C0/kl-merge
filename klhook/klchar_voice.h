/* klchar_voice.h - Kane's and Lynch's OWN bark set following the chosen body (re\bots_voice.md 6.5), the part of it that
   is pure arithmetic on numbers the caller read: kept apart so klcv_test.c checks it without the game. Included by
   klchar.c. Opt-in through KLWardrobe.ini [Wardrobe] VoiceKane= VoiceLynch= Material= (.SND offsets the data side wrote;
   all three absent or 0 = off). NOT RUN IN THE GAME.

   ASSUMPTION (bots_voice.md 6.5, not read in the exe): a loaded definition's address = bank base + its .SND offset,
   and bank base = [player + 0x238] (field 5 = engine/material#def in every stock level, voice.md) - Material. The
   check of a definition's head ([type u32] == 5, then 0xcdcdcdcd: characters.md) stands in for the reading. */
#ifndef KLCHAR_VOICE_H
#define KLCHAR_VOICE_H

#define KLCV_KANE   9                    /* KLChar values (the wardrobe's Dead Men bodies: re\wardrobe.md) */
#define KLCV_LYNCH  10
#define KLCV_DEFTYPE 5u                  /* a definition record's type word */
#define KLCV_DEFPAD  0xcdcdcdcdu         /* the word after it (every definition head, characters.md) */

struct klcv_cfg { DWORD kane, lynch, material; };            /* .SND offsets from KLWardrobe.ini; 0 = not given */

static int klcv_enabled(const struct klcv_cfg *c) { return c->material != 0 && (c->kane != 0 || c->lynch != 0); }

/* the .SND offset of the voice the choice asks for; 0 = none (any other body: field 0 is written back to 0) */
static DWORD klcv_want(const struct klcv_cfg *c, int klchar)
{
    if (!klcv_enabled(c)) return 0;
    if (klchar == KLCV_KANE) return c->kane;
    if (klchar == KLCV_LYNCH) return c->lynch;
    return 0;
}

/* bank base from the material definition's address; 0 when the arithmetic cannot be right */
static DWORD klcv_base(DWORD material_def, DWORD material_off)
{
    if (!material_def || !material_off || material_def <= material_off) return 0;
    return material_def - material_off;
}

/* the address of a voice definition, or 0 when the two head words read there are not a definition's */
static DWORD klcv_def(DWORD base, DWORD off, DWORD head0, DWORD head1)
{
    if (!base || !off) return 0;
    if (base + off < base) return 0;                        /* wrapped */
    return head0 == KLCV_DEFTYPE && head1 == KLCV_DEFPAD ? base + off : 0;
}

#endif /* KLCHAR_VOICE_H */
