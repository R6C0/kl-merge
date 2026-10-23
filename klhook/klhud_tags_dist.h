/* klhud_tags_dist.h - the HeadMaxDist arithmetic of klhud_tags.c (option D of re\hud_tags_sight.md), kept apart so that
   klht_test.c checks it without the HUD stack. Pure functions, no game read. Included by klhud_tags.c. */
#ifndef KLHUD_TAGS_DIST_H
#define KLHUD_TAGS_DIST_H

/* HeadMaxDist: the alpha (0..255) a tag gets at `dist` centimetres from the human: 255 up to maxdist - fade, a straight fade
   to 0 at maxdist, 0 beyond; maxdist 0 = always 255 (off). Pure arithmetic (harness klht_test.c). */
static int klht_alpha_at(float dist, float maxdist_m, float fade_m)
{
    float maxd = maxdist_m * 100.0f, fade = fade_m * 100.0f, a;
    if (maxdist_m <= 0.0f) return 255;
    if (!(dist >= 0.0f)) return 255;                               /* NaN or a failed read: drawn (the stock's behaviour) */
    if (dist >= maxd) return 0;
    if (fade <= 0.0f || dist <= maxd - fade) return 255;
    a = (maxd - dist) / fade * 255.0f;
    return a < 1.0f ? 1 : a > 255.0f ? 255 : (int)a;              /* 1: still drawn, all but gone (0 = not drawn at all) */
}
/* a colour with its alpha byte replaced (the hook's text colours are 0xAARRGGBB) */
static DWORD klht_with_alpha(DWORD col, int alpha) { return (col & 0x00ffffffu) | ((DWORD)(alpha & 0xff) << 24); }

#endif /* KLHUD_TAGS_DIST_H */
