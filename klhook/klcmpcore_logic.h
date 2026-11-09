/* klcmpcore_logic.h - pure helpers of klcampaign.c (the campaign runtime core), no windows.h, tested by klcmpcore_test.c.
 *
 * Ported from luvsic's a-newer-perspective loader/campaign.inc + loader/anp_loader.c @32aa649 (in contribution with luvsic).
 * READ = taken from his code (file:line in the comment), MEASURED = checked here, GUESS = not verified.
 * Included by klcampaign.c AFTER <string.h>; the test includes <stdio.h> <string.h> <stdlib.h> first.
 */
#ifndef KLCMPCORE_LOGIC_H
#define KLCMPCORE_LOGIC_H
#include "kladpcm.h"

/* ---------------------------------------------------------------- scene ids */

/* a scene id the loader may route: 1..4 characters, letters and digits only (SetId copies 4 chars into 0x156b6f5,
   campaign.inc:199 cmp_anp_id). The existence of Scenes\Locations\<id>\<id>_Main.zip is checked by the caller. */
static int klcmpc_id_ok(const char *id)
{
    int i;
    if (!id || !id[0]) return 0;
    for (i = 0; id[i]; i++) {
        char c = id[i];
        if (i >= 4) return 0;
        if (!((c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'))) return 0;
    }
    return 1;
}

/* the ids of the 17 converted story levels, in play order (READ campaign.inc:75 CMP_DM_ORDER); -1 = not one of them */
static const char *const klcmpc_order[] = {"M01", "M02", "M03", "M03B", "M05", "M06", "M07", "M07F", "M08", "M09", "M09B",
                                           "M11", "M11B", "M12", "M13", "M13B", "M14", 0};
static int klcmpc_dm_index(const char *id)
{
    int i;
    for (i = 0; klcmpc_order[i]; i++) {
        const char *a = klcmpc_order[i], *b = id; int k = 0;
        while (a[k] && b[k] && ((a[k] | 32) == (b[k] | 32))) k++;
        if (!a[k] && !b[k]) return i;
    }
    return -1;
}

/* the one id whose scene is not Scenes\Locations\<id>\<id>_Main.zip: the funeral keeps Dead Men's path because kl2's scene
   bookkeeping (0x881350 / 0x696c40) skips chapter index and profile save for any scene path containing "Funeral"
   (READ campaign.inc:81 CMP_ALIAS). NULL = the normal path. */
static const char *klcmpc_alias(const char *id)
{
    if (id && id[0] == 'M' && id[1] == '0' && id[2] == '7' && id[3] == 'F' && !id[4]) return "CutScenes/M07/M07_A_Funeral.zip";
    if (id && id[0] == 'm' && id[1] == '0' && id[2] == '7' && id[3] == 'f' && !id[4]) return "CutScenes/M07/M07_A_Funeral.zip";
    return 0;
}

/* the path the scene table's entry gets for an id (under Scenes, forward slashes; READ campaign.inc:217) */
static int klcmpc_rpath(const char *id, char *out, int cap)
{
    int n;
    const char *al = klcmpc_alias(id);
    if (!klcmpc_id_ok(id)) return 0;
    n = al ? (int)strlen(al) : (int)(2 * strlen(id) + 18);
    if (n >= cap) return 0;
    if (al) strcpy(out, al); else { sprintf(out, "Locations/%s/%s_Main.zip", id, id); }
    return 1;
}

/* a path of an opened archive -> the scene it is. "...Locations\<id>\<id>_Main*.zip" -> id (upper case); the funeral by its
   alias path; "KaneAndLynch.zip" -> "FE" (the front end). READ campaign.inc:326-370 (cmp_scene_of); rewritten for clarity,
   same rules. */
static const char *klcmpc_base(const char *n)
{
    const char *b = n + strlen(n);
    while (b > n && b[-1] != '\\' && b[-1] != '/') b--;
    return b;
}
static int klcmpc_ieq(const char *a, const char *b, int n)
{
    int i;
    for (i = 0; i < n; i++) {
        char x = a[i], y = b[i];
        if (x == '\\') x = '/'; if (y == '\\') y = '/';
        if (x >= 'A' && x <= 'Z') x = (char)(x + 32);
        if (y >= 'A' && y <= 'Z') y = (char)(y + 32);
        if (x != y) return 0;
    }
    return 1;
}
static int klcmpc_scene_of_path(const char *n, char *id)
{
    const char *b = klcmpc_base(n), *us; size_t bl = strlen(b), nl = strlen(n); int il, i;
    const char *al = "CutScenes/M07/M07_A_Funeral.zip"; size_t all = strlen(al);
    if (bl < 9 || !klcmpc_ieq(b + bl - 4, ".zip", 4)) return 0;
    if (bl == 16 && klcmpc_ieq(b, "KaneAndLynch.zip", 16)) { strcpy(id, "FE"); return 1; }
    if (nl > all && (n[nl - all - 1] == '\\' || n[nl - all - 1] == '/') && klcmpc_ieq(n + nl - all, al, (int)all)) { strcpy(id, "M07F"); return 1; }
    us = strchr(b, '_');
    if (!us || us - b > 4 || us == b || !klcmpc_ieq(us, "_Main", 5)) return 0;
    il = (int)(us - b);
    if (b - n < il + 1 || !klcmpc_ieq(b - il - 1, b, il)) return 0;                            /* "<id>\<id>_Main" */
    if (b - il - 2 >= n && b[-il - 2] != '\\' && b[-il - 2] != '/') return 0;
    if (b - n < il + 11 || !klcmpc_ieq(b - il - 11, "Locations", 9)) return 0;                  /* "Locations\<id>\" */
    for (i = 0; i < il; i++) { char c = b[i]; id[i] = (char)(c >= 'a' && c <= 'z' ? c - 32 : c); }
    id[il] = 0;
    return 1;
}

/* a save file name: digits then ".kls" (READ campaign.inc:331) */
static int klcmpc_is_kls(const char *b)
{
    int k = 0;
    while (b[k] >= '0' && b[k] <= '9') k++;
    return k > 0 && klcmpc_ieq(b + k, ".kls", 5);       /* 5 = with the NUL */
}

/* "M01 1" / "M03B" / "  M02   1  " -> id and mode (mode default 1: the value luvsic's ANP_load.txt gives do_load).
   0 = nothing usable. id is upper-cased. READ anp_loader.c:/campaign.inc:896 (sscanf "%7s %d"). */
static int klcmpc_parse_load(const char *line, char *id, int *mode)
{
    int i = 0, n = 0, m = 0, have = 0, neg = 0;
    while (line[i] == ' ' || line[i] == '\t') i++;
    while (line[i] && line[i] != ' ' && line[i] != '\t' && line[i] != '\r' && line[i] != '\n') { if (n < 7) id[n++] = line[i]; i++; }
    id[n] = 0;
    if (!klcmpc_id_ok(id)) return 0;
    for (n = 0; id[n]; n++) if (id[n] >= 'a' && id[n] <= 'z') id[n] = (char)(id[n] - 32);
    while (line[i] == ' ' || line[i] == '\t') i++;
    if (line[i] == '-') { neg = 1; i++; }
    while (line[i] >= '0' && line[i] <= '9') { m = m * 10 + (line[i] - '0'); have = 1; i++; if (m > 100000) break; }
    *mode = have ? (neg ? -m : m) : 1;
    return 1;
}

/* ---------------------------------------------------------------- Dead Men .str (IOISNDSTREAM) -> Dog Days header + virtual PCM */

/* Dead Men's header: "IOISNDSTREAM", +0x18 u32 tableOffset, +0x1c u32 count. Dog Days widened tableOffset to u64, shifting
   the rest by 4, so in a Dog Days header +0x1c (the high half) is 0. A header is Dead Men's when the magic matches and
   +0x1c is a plausible count. MEASURED against luvsic's tools only through his str_register (anp_loader.c:/str_register);
   the content test (rather than his "path contains Kane and Lynch Dead Men") is MINE: the converted campaign levels load
   their .str from the Dog Days folder. */
static int klcmpc_str_is_dm(const unsigned char *h38)
{
    unsigned long cnt = (unsigned long)h38[0x1c] | ((unsigned long)h38[0x1d] << 8) | ((unsigned long)h38[0x1e] << 16) | ((unsigned long)h38[0x1f] << 24);
    return memcmp(h38, "IOISNDSTREAM", 12) == 0 && cnt > 0 && cnt < 100000;
}
static unsigned long klcmpc_rd32(const unsigned char *p) { return (unsigned long)p[0] | ((unsigned long)p[1] << 8) | ((unsigned long)p[2] << 16) | ((unsigned long)p[3] << 24); }
static void klcmpc_wr32(unsigned char *p, unsigned long v) { p[0] = (unsigned char)v; p[1] = (unsigned char)(v >> 8); p[2] = (unsigned char)(v >> 16); p[3] = (unsigned char)(v >> 24); }

/* the converted header (READ anp_loader.c:/str_register): dm[0..0x18) kept, tableOffset widened to u64, the rest shifted by 4 */
static void klcmpc_str_hdr_dd(const unsigned char *dm, unsigned char *dd)
{
    memcpy(dd, dm, 0x18);
    klcmpc_wr32(dd + 0x18, klcmpc_rd32(dm + 0x18)); klcmpc_wr32(dd + 0x1c, 0);
    memcpy(dd + 0x20, dm + 0x1c, 0x14);
    memcpy(dd + 0x34, dm + 0x30, 4);
}

#define KLCMPC_VBASE 0x60000000LL                 /* virtual PCM starts here (READ anp_loader.c:/STR_VBASE; same mapping as tools/strvirt.py) */
#define KLCMPC_LIP   4096                          /* the 'LIP ' lip-sync block served verbatim (READ anp_loader.c:/LIP_BLOCK) */
typedef struct { unsigned long dataOff, dataSize, metaOff, metaSize, ch, rate, samples, balign, spb, idxPos, pcm, idx; long long voff; unsigned long lip; } klcmpc_ent;

/* one index record (72 bytes) + its meta block -> an IMA-ADPCM entry? meta = 9 dwords; codec 3, 1 or 2 channels (READ
   anp_loader.c:/str_register). 1 = e filled. */
static int klcmpc_ent_from(const unsigned char *rec, const unsigned long *meta, unsigned long tbl, unsigned long i, klcmpc_ent *e)
{
    unsigned long mSz = klcmpc_rd32(rec + 32);
    memset(e, 0, sizeof *e);
    if (mSz < 36 || mSz > 36) return 0;
    if (!(meta[0] == 3 && meta[2] >= 1 && meta[2] <= 2 && meta[7] >= 4 * meta[2] && meta[8] > 1)) return 0;
    e->dataOff = klcmpc_rd32(rec + 8); e->dataSize = klcmpc_rd32(rec + 16); e->metaOff = klcmpc_rd32(rec + 24); e->metaSize = mSz;
    e->ch = meta[2]; e->rate = meta[3]; e->samples = meta[1]; e->balign = meta[7]; e->spb = meta[8];
    e->idxPos = tbl + i * 72; e->idx = i;
    return 1;
}
static int klcmpc_ent_cmp(const void *a, const void *b)
{
    const klcmpc_ent *x = (const klcmpc_ent *)a, *y = (const klcmpc_ent *)b;
    if (x->dataOff != y->dataOff) return x->dataOff < y->dataOff ? -1 : 1;
    return x->idx < y->idx ? -1 : x->idx > y->idx;
}
/* sort by data offset and give each entry its virtual offset: 4 KB-aligned slots from KLCMPC_VBASE; returns the end */
static long long klcmpc_layout(klcmpc_ent *e, int n)
{
    long long v = KLCMPC_VBASE; int i;
    qsort(e, n, sizeof *e, klcmpc_ent_cmp);
    for (i = 0; i < n; i++) { e[i].pcm = e[i].samples * e[i].ch * 2; e[i].voff = v; v += (e[i].pcm + 0xFFF) & ~0xFFFLL; }
    return v;
}
/* last entry whose voff <= pos; -1 = none (binary search, READ anp_loader.c:/str_serve_virtual) */
static int klcmpc_find_v(const klcmpc_ent *e, int n, long long pos)
{
    int lo = 0, hi = n - 1, ei = -1;
    while (lo <= hi) { int m = (lo + hi) / 2; if (e[m].voff <= pos) { ei = m; lo = m + 1; } else hi = m - 1; }
    return ei;
}

/* copy the part of src[at, at+len) that falls inside buf's window [a, b) */
static void klcmpc_put(unsigned char *buf, long long a, long long b, long long at, const void *src, unsigned long len)
{
    long long p0 = at > a ? at : a, p1 = at + (long long)len < b ? at + (long long)len : b, p;
    for (p = p0; p < p1; p++) buf[p - a] = ((const unsigned char *)src)[p - at];
}
/* what a real read of file bytes [pos, pos+got) returns, rewritten: the converted header, the index records' offset/size
   (-> virtual offset / PCM size) and the meta blocks (-> PCM descriptors). READ anp_loader.c:/str_overlay. */
static void klcmpc_overlay(unsigned char *buf, long long pos, unsigned long got, const unsigned char *hdr38, const klcmpc_ent *e, int n,
                           unsigned long tbl, unsigned long cnt)
{
    long long a = pos, b = pos + got; int i, touch;
    if (a < 0x38) klcmpc_put(buf, a, b, 0, hdr38, 0x38);
    if (!n) return;
    touch = (a < (long long)tbl + (long long)cnt * 72) && (b > (long long)tbl);
    for (i = 0; i < n; i++) {
        const klcmpc_ent *x = &e[i];
        if (touch && (long long)x->idxPos + 24 > a && (long long)x->idxPos + 8 < b) {
            unsigned long long v[2]; v[0] = (unsigned long long)x->voff; v[1] = (unsigned long long)x->pcm;
            klcmpc_put(buf, a, b, (long long)x->idxPos + 8, v, 16);
        }
        if ((long long)x->metaOff < b && (long long)x->metaOff + 36 > a) {
            unsigned long m[9]; m[0] = 2; m[1] = x->samples * x->ch; m[2] = x->ch; m[3] = x->rate; m[4] = 16; m[5] = 0; m[6] = 0; m[7] = 2 * x->ch; m[8] = 0;
            klcmpc_put(buf, a, b, x->metaOff, m, 36);
        }
    }
}

/* virtual byte b of an entry -> (ADPCM block, byte offset inside the decoded block). lip = 0/1: audio from block 0; lip =
   KLCMPC_LIP: the first 4 KB are the LIP block and audio starts at block KLCMPC_LIP / balign. -1 = inside the LIP block. */
static int klcmpc_vmap(unsigned long lip, unsigned long balign, unsigned long bbytes, unsigned long b, unsigned long *blk, unsigned long *off)
{
    unsigned long blk0 = 0;
    if (lip == KLCMPC_LIP) { if (b < KLCMPC_LIP) return -1; b -= KLCMPC_LIP; blk0 = KLCMPC_LIP / balign; }
    *blk = blk0 + b / bbytes; *off = b % bbytes;
    return 0;
}

/* ---------------------------------------------------------------- the IAT hook layer's pure part */

/* the name an opened .kls goes to: <appdir>\saves\<slot>\<base> (READ campaign.inc:440; slot = "Campaign" here, see GUESS in
   klcampaign.c). 0 = does not fit. */
static int klcmpc_save_path(const char *appdir, const char *slot, const char *base, char *out, int cap)
{
    int n = (int)(strlen(appdir) + strlen(slot) + strlen(base) + 9);
    if (n >= cap) return 0;
    sprintf(out, "%s\\saves\\%s\\%s", appdir, slot, base);
    return 1;
}

/* the progress rule (READ campaign.inc:393): "reached" only moves forward in play order */
static int klcmpc_reached_advances(const char *reached, const char *id)
{
    int i = klcmpc_dm_index(id);
    return i >= 0 && i > klcmpc_dm_index(reached);
}

/* "stable pump": the tick has come at least every gap ms for the last hold ms (READ campaign.inc:906 steadySince) */
struct klcmpc_steady { unsigned long prev, since; };
static unsigned long klcmpc_steady_update(struct klcmpc_steady *s, unsigned long now, unsigned long gap)
{   /* -> how long the pump has been steady */
    if (!s->prev || now - s->prev > gap) s->since = now;
    s->prev = now;
    return now - s->since;
}

#endif
