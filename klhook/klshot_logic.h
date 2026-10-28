/* klshot_logic.h - pure logic of kld3.c's back-buffer shots ([Memory] D3dShotEvery / Dir / Tag / From / Max / Fmt), so klshot_test.c
 * can check it off-game. 2026-10-28: the bench's desktop grab (kl_autotest.shot, GDI BitBlt) is all-zero while the monitor is off or the
 * session locked; the D3D9 back buffer is not. Fmt 0 = JPG (as before), 1 = PNG, 2 = BMP: the D3DXIMAGE_FILEFORMAT values are
 * BMP 0, JPG 1, TGA 2, PNG 3 (d3dx9tex.h). Max default 40 as before, at most 400. */
#ifndef KLSHOT_LOGIC_H
#define KLSHOT_LOGIC_H
#include <stdio.h>
#include <string.h>

static int klshot_max(int v) { return v <= 0 ? 40 : v > 400 ? 400 : v; }
static int klshot_fmt(int v) { return v == 1 || v == 2 ? v : 0; }                      /* anything else: JPG */
static int klshot_d3dx_fmt(int f) { return f == 1 ? 3 : f == 2 ? 0 : 1; }
static const char *klshot_ext(int f) { return f == 1 ? "png" : f == 2 ? "bmp" : "jpg"; }
/* 0 = wait, 1 = arm (first call after From: remember the time, no shot), 2 = shoot now. times in ms; last == 0 = not armed yet */
static int klshot_due(unsigned long now, unsigned long last, unsigned long t0, int from_s, int every_s, int n, int max)
{
    if (every_s <= 0 || n >= max) return 0;
    if (from_s && now - t0 < (unsigned long)from_s * 1000) return 0;
    if (!last) return 1;
    return now - last < (unsigned long)every_s * 1000 ? 0 : 2;
}
static void klshot_path(char *out, size_t cap, const char *dir, const char *tag, int n, int fmt)
{
    _snprintf(out, cap, "%s%sKLShot_%s_%02d.%s", dir, dir[0] ? "\\" : "", tag, n, klshot_ext(fmt));
    out[cap - 1] = 0;
}
#endif
