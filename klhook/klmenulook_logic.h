/* klmenulook_logic.h - pure decision for [MenuLook] DeadMen (2026-11-09, track T9, re/menu_look_1109.md 4.2). No windows.h.
 * Used by klslot.c (kls_menulook, called from kls_map) and klmenulook_test.c.
 *
 * WHAT: the Dead Men LOOK of the in-game menu (Impact-style fonts, chalk / coral colour sets, Dead Men click sounds) is a set of
 * THEMED COPIES of the menu files, each named <stem>_deadmen.<ext> and lying BESIDE the file the game would open anyway
 * (tools/kl_menu_look_1109.py install.py --variant writes them; stem + '_deadmen' + ext, same rule as variant_name() there).
 * This header decides, for one resolved path, whether that copy is the file to open. It is the BotGate .bots.zip pattern
 * (klslot.c kls_bot_apply): a path change inside the existing file wrappers, no code byte of kl2.exe.
 *
 * THE MENU FILES (name only, case-insensitive, any directory - the overlay copy under KLExpansion\Overlay\, the MountFirst / Rows12
 * alias, or the stock file under the game folder are all answered alike; re/menu_look_1109.md 1 and 4.1):
 *   patch01*.zip            Patch01.zip and Patch01_rows12.zip (the file [Lobby] Rows12=1 makes the game open, klslot.c ~976) and
 *                           any other Patch01_<x>.zip a MountFirst= line names: menu/frontend.xml + menu/ingame.xml
 *   kaneandlynch.zip        Scenes\kaneandlynch.zip: Menu/online.xml and the menu scene's eight fonts
 *   kaneandlynch.whd        Scenes\kaneandlynch.WHD + .WAV: the SFX/OSD click records, *.wav (both must be themed as a PAIR: the
 *   kaneandlynch.wav        .WHD's record offsets point into the .WAV; the stage tool writes both or neither)
 *
 * DECISION TABLE (klml_variant; out = the candidate path whenever one could be formed, so the caller can log it):
 *   on == 0                                         -> 0, KLML_OFF        key off: the path as it is, nothing probed, nothing logged
 *   path empty / no file name / '*' or '?' in it    -> 0, KLML_NOT_MENU   (a FindFirstFile pattern is never swapped)
 *   name has no '.' or the stem is empty            -> 0, KLML_NOT_MENU
 *   name is none of the four above                  -> 0, KLML_NOT_MENU   every other open: a cheap tail compare, no file probe
 *   stem ends in "_deadmen" and the rest is a menu name -> 0, KLML_ALREADY  never a double suffix (a themed copy opened directly)
 *   dir + stem + "_deadmen" + ext would not fit cap -> 0, KLML_TOO_LONG   out untouched; the caller may log it once
 *   the sibling does not exist (exists() == 0)      -> 0, KLML_MISSING    stock look; out = the sibling tried, for the ONE log line
 *   else                                            -> 1, KLML_USED       out = <dir><stem>_deadmen<ext>: open THAT file
 * The case of dir and stem is kept as given (the log shows the path the game asked for); the suffix is lower case, the extension is
 * copied as given. Separators '\' and '/' both end the directory part. Bounded: nothing is written past cap - 1, every copy is
 * length-checked first; cap is the caller's buffer size (MAX_PATH in the hook).
 * Not decided here (klslot.c): WHEN the step runs (after the MountFirst / Rows12 alias, after the overlay rule, and on the stock
 * path) and the once-per-file log. GUESS (doc 4.2): the engine re-opens these files at every scene load, so a key change applies at
 * the next game start or next menu load, never mid-session. */
#ifndef KLMENULOOK_LOGIC_H
#define KLMENULOOK_LOGIC_H

#include <string.h>

#define KLML_SUFFIX   "_deadmen"
#define KLML_SUFFIX_N 8

enum { KLML_OFF = 0, KLML_NOT_MENU, KLML_ALREADY, KLML_TOO_LONG, KLML_MISSING, KLML_USED };

typedef int (*klml_exists_fn)(const char *path);     /* 1 = a plain file is there (klslot.c: kls_isfile, this dll's own import) */

static int klml_lc(int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }

static int klml_ieq(const char *a, const char *b, size_t n)
{   /* a[0..n) == b[0..n) ignoring ASCII case; b is the NUL-terminated pattern and must be exactly n long */
    size_t i;
    for (i = 0; i < n; i++) if (!b[i] || klml_lc((unsigned char)a[i]) != klml_lc((unsigned char)b[i])) return 0;
    return !b[n];
}

/* stem = the file name without directory and extension (stemlen chars), ext = its extension with the '.' (extlen chars);
   -> 1 when stem.ext is one of the menu files above */
static int klml_is_menu_name(const char *stem, size_t stemlen, const char *ext, size_t extlen)
{
    if (extlen != 4) return 0;
    if (stemlen >= 7 && klml_ieq(stem, "patch01", 7) && klml_ieq(ext, ".zip", 4)) return 1;     /* patch01*.zip */
    if (stemlen == 12 && klml_ieq(stem, "kaneandlynch", 12) &&
        (klml_ieq(ext, ".zip", 4) || klml_ieq(ext, ".whd", 4) || klml_ieq(ext, ".wav", 4))) return 1;
    return 0;
}

/* -> 1 and out = the _deadmen sibling to open; 0 = keep path (why says which row of the table). out has room for cap bytes. */
static int klml_variant(const char *path, int on, klml_exists_fn exists, char *out, size_t cap, int *why)
{
    size_t len, dir, dot, stem, ext, i;
    const char *name;
    if (why) *why = KLML_OFF;
    if (!on) return 0;
    if (why) *why = KLML_NOT_MENU;
    if (!path || !path[0] || !out || cap < 2) return 0;
    len = strlen(path);
    for (dir = len; dir > 0 && path[dir - 1] != '\\' && path[dir - 1] != '/'; dir--) ;
    name = path + dir;
    if (!name[0] || strpbrk(name, "*?")) return 0;
    for (dot = len; dot > dir && path[dot - 1] != '.'; dot--) ;
    if (dot <= dir) return 0;                           /* no extension */
    dot--;                                              /* index of the last '.' */
    stem = dot - dir; ext = len - dot;
    if (!stem) return 0;                                /* ".zip" alone */
    if (stem > KLML_SUFFIX_N && klml_ieq(path + dot - KLML_SUFFIX_N, KLML_SUFFIX, KLML_SUFFIX_N)) {   /* a themed copy opened directly: never a double suffix */
        if (!klml_is_menu_name(name, stem - KLML_SUFFIX_N, path + dot, ext)) return 0;
        if (why) *why = KLML_ALREADY;
        return 0;
    }
    if (!klml_is_menu_name(name, stem, path + dot, ext)) return 0;
    if (dot + KLML_SUFFIX_N + ext + 1 > cap) { if (why) *why = KLML_TOO_LONG; return 0; }
    memcpy(out, path, dot);
    for (i = 0; i < KLML_SUFFIX_N; i++) out[dot + i] = KLML_SUFFIX[i];
    memcpy(out + dot + KLML_SUFFIX_N, path + dot, ext);
    out[dot + KLML_SUFFIX_N + ext] = 0;
    if (!exists || !exists(out)) { if (why) *why = KLML_MISSING; return 0; }
    if (why) *why = KLML_USED;
    return 1;
}

static const char *klml_why_text(int why)
{   /* for the log lines */
    switch (why) {
    case KLML_OFF:      return "off";
    case KLML_NOT_MENU: return "not a menu file";
    case KLML_ALREADY:  return "already the themed copy";
    case KLML_TOO_LONG: return "variant path too long";
    case KLML_MISSING:  return "no themed copy beside it";
    case KLML_USED:     return "themed copy used";
    }
    return "?";
}

#endif
