/* klcampui_logic.h - pure decision for [CampaignUI] Menu (2026-11-10, branch campaign-ui). No windows.h.
 * Used by klslot.c (kls_campui, chained after kls_menulook) and klcampui_test.c.
 *
 * WHAT: luvsic's Dead Men campaign menu pages are delivered as an extra row in Dog Days' CampaignMenu (tools/kl_campui_menu.py),
 * written as a COPY of each menu archive named <stem>_campui.zip beside the file the game would open anyway. This header decides,
 * for one resolved path, whether that copy is the file to open. Same pattern as klmenulook_logic.h ([MenuLook] _deadmen copies),
 * and it runs AFTER it: Patch01.zip -> (MenuLook) Patch01_deadmen.zip -> (CampaignUI) Patch01_deadmen_campui.zip.
 *
 * GATE: on = [CampaignUI] Menu=1 AND [Campaign] Enable=1 (decided once at init by the caller; klcu_gate). Off = every path as it is.
 * Only the patch archives hold menu/frontend.xml: patch01*.zip (Patch01.zip, Patch01_rows12.zip, Patch01_deadmen.zip,
 * Patch01_rows12_deadmen.zip ...). Every other open costs one tail compare, no file probe.
 *
 * DECISION TABLE (klcu_variant):
 *   on == 0                                  -> 0, KLCU_OFF
 *   empty / no file name / '*' '?' in name   -> 0, KLCU_NOT_MENU
 *   no '.' / empty stem / name not patch01*.zip -> 0, KLCU_NOT_MENU
 *   stem ends in "_campui"                   -> 0, KLCU_ALREADY   never a double suffix
 *   dir + stem + "_campui" + ext too long    -> 0, KLCU_TOO_LONG
 *   sibling missing                          -> 0, KLCU_MISSING   stock menu (out = the sibling tried, for the one log line)
 *   else                                     -> 1, KLCU_USED      out = <dir><stem>_campui<ext>
 * Bounded: nothing is written past cap - 1. */
#ifndef KLCAMPUI_LOGIC_H
#define KLCAMPUI_LOGIC_H

#include <string.h>

#define KLCU_SUFFIX   "_campui"
#define KLCU_SUFFIX_N 7

enum { KLCU_OFF = 0, KLCU_NOT_MENU, KLCU_ALREADY, KLCU_TOO_LONG, KLCU_MISSING, KLCU_USED };

typedef int (*klcu_exists_fn)(const char *path);

static int klcu_lc(int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }

static int klcu_ieq(const char *a, const char *b, size_t n)
{   /* a[0..n) == b ignoring ASCII case; b NUL-terminated and exactly n long */
    size_t i;
    for (i = 0; i < n; i++) if (!b[i] || klcu_lc((unsigned char)a[i]) != klcu_lc((unsigned char)b[i])) return 0;
    return !b[n];
}

static int klcu_gate(int menu_key, int campaign_enable) { return menu_key != 0 && campaign_enable != 0; }

static int klcu_variant(const char *path, int on, klcu_exists_fn exists, char *out, size_t cap, int *why)
{
    size_t len, dir, dot, stem, ext, i;
    const char *name;
    if (why) *why = KLCU_OFF;
    if (!on) return 0;
    if (why) *why = KLCU_NOT_MENU;
    if (!path || !path[0] || !out || cap < 2) return 0;
    len = strlen(path);
    for (dir = len; dir > 0 && path[dir - 1] != '\\' && path[dir - 1] != '/'; dir--) ;
    name = path + dir;
    if (!name[0] || strpbrk(name, "*?")) return 0;
    for (dot = len; dot > dir && path[dot - 1] != '.'; dot--) ;
    if (dot <= dir) return 0;
    dot--;
    stem = dot - dir; ext = len - dot;
    if (!stem || ext != 4 || !klcu_ieq(path + dot, ".zip", 4)) return 0;
    if (stem < 7 || !klcu_ieq(name, "patch01", 7)) return 0;
    if (stem > KLCU_SUFFIX_N && klcu_ieq(path + dot - KLCU_SUFFIX_N, KLCU_SUFFIX, KLCU_SUFFIX_N)) { if (why) *why = KLCU_ALREADY; return 0; }
    if (dot + KLCU_SUFFIX_N + ext + 1 > cap) { if (why) *why = KLCU_TOO_LONG; return 0; }
    memcpy(out, path, dot);
    for (i = 0; i < KLCU_SUFFIX_N; i++) out[dot + i] = KLCU_SUFFIX[i];
    memcpy(out + dot + KLCU_SUFFIX_N, path + dot, ext);
    out[dot + KLCU_SUFFIX_N + ext] = 0;
    if (!exists || !exists(out)) { if (why) *why = KLCU_MISSING; return 0; }
    if (why) *why = KLCU_USED;
    return 1;
}

static const char *klcu_why_text(int why)
{
    switch (why) {
    case KLCU_OFF:      return "off";
    case KLCU_NOT_MENU: return "not a patch archive";
    case KLCU_ALREADY:  return "already the campaign copy";
    case KLCU_TOO_LONG: return "variant path too long";
    case KLCU_MISSING:  return "no campaign copy beside it";
    case KLCU_USED:     return "campaign copy used";
    }
    return "?";
}

#endif
