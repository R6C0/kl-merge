/* klmenusounds_logic.h - pure logic for [MenuSounds] (2026-11-10, track T9 stage 4b, per-event menu sound picker). No windows.h.
 * Used by klslot.c (kls_menusounds, called from kls_menulook when the themed Scenes\kaneandlynch_deadmen.WHD was chosen) and
 * klmenusounds_test.c.
 *
 * WHY: stage 4a (kl_menu_sounds_1109.py) baked ONE fixed answer into the themed .WHD. The owner wants to choose per menu event
 * (navigate, confirm, back, toggle, slider ...) between the Dog Days sound, the Dead Men sound, any other Dead Men UI clip, or silence.
 * HOW: tools/kl_menu_sounds_1110.py stages ONE themed pair whose .WHD is the STOCK .WHD byte for byte and whose .WAV is the stock .WAV
 * plus every candidate clip APPENDED (nothing in place; the stock records and their shared spans are untouched) and a SIDECAR text
 * table kaneandlynch_deadmen.klms: for each event the record it stands for, and for each choice the five record fields that point
 * the record at the appended data (pcm size samples off offhi; the tool encoded each clip in the record's own codec / rate / block).
 * At bank open the hook reads the ini ([MenuSounds] <Event>=dd|dm|off|<clip>), copies the stock .WHD into memory, overwrites those five
 * dwords of each chosen record, writes the result to a temp file (name = hash of the choices, so two game copies never fight) and
 * the open goes there. "dd" = no change (the stock record stays), "dm" = the event's default Dead Men clip, "off" = a short silent
 * clip the tool appended (NEVER size 0: the engine trusts the record's size, re/gun_echo_1107.md 8).
 *
 * SIDECAR TEXT (one record per line, '#' lines and blank lines ignored, fields separated by blanks, names without blanks):
 *   KLMS 1
 *   WHD <stock .WHD length> <fnv1a-32 of it, hex>         the .WHD this table belongs to
 *   WAV <length of the themed .WAV>                        every choice's off+size must lie inside it
 *   F pcm <o> size <o> samples <o> off <o> offhi <o>      byte offsets of the five dwords from the record start (kl_whd's DD_F)
 *   E <event> <rec_off hex> <default choice> <record name> one menu event and the .WHD offset of its record's first dword
 *   C <event> <choice> <pcm> <size> <samples> <off> <offhi> a choice of that event (decimal numbers)
 * A choice name is the clip's file stem ("Up_Down", "Toggle", "OpenWindow_03"); "dd", "dm" and "off" are reserved words
 * (the tool writes "off" as a C line, "dd" and "dm" never). Case is ignored everywhere.
 *
 * DECISION TABLE (klms_resolve, per event):
 *   pick empty / "dd" / unknown event                -> keep the stock record (KLMS_STOCK)
 *   pick "dm"                                         -> the event's default choice (KLMS_CHOICE) - or STOCK if the table has none
 *   pick "off"                                        -> the choice named "off" (KLMS_CHOICE) - or KLMS_UNKNOWN (stock) if none
 *   pick <clip>                                       -> the choice of that name, else KLMS_UNKNOWN (stock, the caller logs it)
 * klms_apply never writes outside the buffer, refuses (returns -1, err text) a .WHD of another length / hash than the table says, a
 * record that does not lie inside it, a choice whose data would leave the .WAV or whose size/pcm is 0. All-or-nothing: on -1 nothing
 * was changed. Bounded tables (KLMS_MAXEV events, KLMS_MAXCH choices): a longer file is refused, not truncated. */
#ifndef KLMENUSOUNDS_LOGIC_H
#define KLMENUSOUNDS_LOGIC_H

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>

#define KLMS_MAXEV 16
#define KLMS_MAXCH 256
#define KLMS_NAME  48
#define KLMS_NF    5            /* pcm size samples off offhi */

enum { KLMS_STOCK = 0, KLMS_CHOICE, KLMS_UNKNOWN };

typedef struct { char name[KLMS_NAME]; unsigned rec; char dflt[KLMS_NAME]; char recname[KLMS_NAME * 2]; } klms_ev;
typedef struct { int ev; char name[KLMS_NAME]; unsigned long v[KLMS_NF]; } klms_ch;       /* v = pcm size samples off offhi */
typedef struct {
    unsigned fo[KLMS_NF];      /* byte offset of each of the five fields from rec_off */
    int have_f;
    unsigned long whdlen, whdhash, wavlen;
    int have_whd, have_wav;
    int nev, nch;
    klms_ev e[KLMS_MAXEV];
    klms_ch c[KLMS_MAXCH];
} klms_tab;

static const char *const klms_fname[KLMS_NF] = { "pcm", "size", "samples", "off", "offhi" };

static int klms_lc(int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }
static int klms_ieq(const char *a, const char *b)
{
    for (; *a && *b; a++, b++) if (klms_lc((unsigned char)*a) != klms_lc((unsigned char)*b)) return 0;
    return !*a && !*b;
}

static unsigned long klms_fnv(const unsigned char *p, size_t n, unsigned long h)
{   /* FNV-1a 32; pass 2166136261 to start. (unsigned long may be wider than 32 bits on a test host: mask) */
    size_t i;
    h &= 0xffffffffUL;
    for (i = 0; i < n; i++) h = ((h ^ p[i]) * 16777619UL) & 0xffffffffUL;
    return h;
}
#define KLMS_FNV0 2166136261UL

/* split one line into at most max blank-separated tokens (in place); -> count */
static int klms_split(char *line, char **tok, int max)
{
    int n = 0;
    while (*line) {
        while (*line == ' ' || *line == '\t' || *line == '\r') line++;
        if (!*line) break;
        if (n == max) return max + 1;
        tok[n++] = line;
        while (*line && *line != ' ' && *line != '\t' && *line != '\r') line++;
        if (*line) *line++ = 0;
    }
    return n;
}

static int klms_num(const char *s, int base, unsigned long *out)
{
    char *e; unsigned long v;
    if (!s || !*s) return 0;
    v = strtoul(s, &e, base);
    if (*e) return 0;
    *out = v & 0xffffffffUL;
    return 1;
}

static int klms_copyname(char *d, size_t cap, const char *s)
{   /* -> 0 when it does not fit */
    size_t n = strlen(s);
    if (n == 0 || n >= cap) return 0;
    memcpy(d, s, n + 1);
    return 1;
}

static int klms_find_ev(const klms_tab *t, const char *name)
{
    int i;
    for (i = 0; i < t->nev; i++) if (klms_ieq(t->e[i].name, name)) return i;
    return -1;
}

static int klms_find_ch(const klms_tab *t, int ev, const char *name)
{
    int i;
    for (i = 0; i < t->nch; i++) if (t->c[i].ev == ev && klms_ieq(t->c[i].name, name)) return i;
    return -1;
}

static void klms_msg(char *err, size_t cap, int ln, const char *fmt, ...)
{
    va_list ap; int k = 0;
    if (!err || cap < 2) return;
    if (ln > 0) k = snprintf(err, cap, "line %d: ", ln);
    if (k < 0 || (size_t)k >= cap) { err[0] = 0; return; }
    va_start(ap, fmt); vsnprintf(err + k, cap - (size_t)k, fmt, ap); va_end(ap);
    err[cap - 1] = 0;
}

/* parse the sidecar text (not NUL-terminated needed: n bytes). -> 1 ok; 0 + err (cap bytes) when anything is wrong. */
static int klms_parse(const char *buf, size_t n, klms_tab *t, char *err, size_t cap)
{
    char line[512]; char *tok[12]; size_t i = 0; int nt, ln = 0, magic = 0, f;
#define KLMS_BAD(...) do { klms_msg(err, cap, ln, __VA_ARGS__); return 0; } while (0)
    memset(t, 0, sizeof *t);
    while (i < n) {
        size_t l = 0;
        while (i < n && buf[i] != '\n') { if (l + 1 < sizeof line) line[l++] = buf[i]; else { ln++; KLMS_BAD("line too long"); } i++; }
        if (i < n) i++;
        line[l] = 0; ln++;
        { char *h = strchr(line, '#'); if (h) *h = 0; }
        nt = klms_split(line, tok, 12);
        if (nt == 0) continue;
        if (nt > 11) KLMS_BAD("too many fields");
        if (!strcmp(tok[0], "KLMS")) {
            unsigned long v;
            if (nt != 2 || !klms_num(tok[1], 10, &v) || v != 1) KLMS_BAD("not KLMS 1");
            magic = 1; continue;
        }
        if (!magic) KLMS_BAD("no KLMS 1 header first");
        if (!strcmp(tok[0], "WHD")) {
            if (nt != 3 || !klms_num(tok[1], 10, &t->whdlen) || !klms_num(tok[2], 16, &t->whdhash)) KLMS_BAD("bad WHD line");
            t->have_whd = 1; continue;
        }
        if (!strcmp(tok[0], "WAV")) {
            if (nt != 2 || !klms_num(tok[1], 10, &t->wavlen)) KLMS_BAD("bad WAV line");
            t->have_wav = 1; continue;
        }
        if (!strcmp(tok[0], "F")) {
            if (nt != 1 + 2 * KLMS_NF) KLMS_BAD("bad F line");
            for (f = 0; f < KLMS_NF; f++) {
                unsigned long o;
                if (strcmp(tok[1 + 2 * f], klms_fname[f]) || !klms_num(tok[2 + 2 * f], 10, &o) || o > 256 || (o & 3)) KLMS_BAD("bad F field %s", klms_fname[f]);
                t->fo[f] = (unsigned)o;
            }
            t->have_f = 1; continue;
        }
        if (!strcmp(tok[0], "E")) {
            unsigned long r; klms_ev *e;
            if (nt < 4 || nt > 5 || !klms_num(tok[2], 16, &r)) KLMS_BAD("bad E line");
            if (t->nev >= KLMS_MAXEV) KLMS_BAD("more than %d events", KLMS_MAXEV);
            if (klms_find_ev(t, tok[1]) >= 0) KLMS_BAD("event %s twice", tok[1]);
            e = &t->e[t->nev];
            if (!klms_copyname(e->name, sizeof e->name, tok[1]) || !klms_copyname(e->dflt, sizeof e->dflt, tok[3])) KLMS_BAD("name too long");
            if (nt == 5 && !klms_copyname(e->recname, sizeof e->recname, tok[4])) KLMS_BAD("record name too long");
            e->rec = (unsigned)r; t->nev++; continue;
        }
        if (!strcmp(tok[0], "C")) {
            unsigned long v[KLMS_NF]; int ev; klms_ch *c;
            if (nt != 3 + KLMS_NF) KLMS_BAD("bad C line");
            for (f = 0; f < KLMS_NF; f++) if (!klms_num(tok[3 + f], 10, &v[f])) KLMS_BAD("bad number in C line");
            ev = klms_find_ev(t, tok[1]);
            if (ev < 0) KLMS_BAD("C line for unknown event %s (E lines first)", tok[1]);
            if (klms_ieq(tok[2], "dd") || klms_ieq(tok[2], "dm")) KLMS_BAD("choice name %s is reserved", tok[2]);
            if (klms_find_ch(t, ev, tok[2]) >= 0) KLMS_BAD("choice %s of %s twice", tok[2], tok[1]);
            if (t->nch >= KLMS_MAXCH) KLMS_BAD("more than %d choices", KLMS_MAXCH);
            c = &t->c[t->nch];
            if (!klms_copyname(c->name, sizeof c->name, tok[2])) KLMS_BAD("choice name too long");
            c->ev = ev; for (f = 0; f < KLMS_NF; f++) c->v[f] = v[f];
            t->nch++; continue;
        }
        KLMS_BAD("unknown line type %s", tok[0]);
    }
    if (!magic) { ln = 0; KLMS_BAD("empty / no KLMS header"); }
    if (!t->have_f || !t->have_whd || !t->have_wav) { ln = 0; KLMS_BAD("missing F / WHD / WAV line"); }
    if (!t->nev) { ln = 0; KLMS_BAD("no events"); }
    for (f = 0; f < t->nev; f++) {
        if (!klms_ieq(t->e[f].dflt, "dd") && klms_find_ch(t, f, t->e[f].dflt) < 0) { ln = 0; KLMS_BAD("event %s: default choice %s has no C line", t->e[f].name, t->e[f].dflt); }
    }
#undef KLMS_BAD
    return 1;
}

/* one event: pick -> the choice index (>= 0) or -1 = keep the stock record; *why = KLMS_STOCK / KLMS_CHOICE / KLMS_UNKNOWN */
static int klms_resolve(const klms_tab *t, int ev, const char *pick, int *why)
{
    int c;
    if (why) *why = KLMS_STOCK;
    if (ev < 0 || ev >= t->nev || !pick) return -1;
    while (*pick == ' ' || *pick == '\t') pick++;
    if (!*pick || klms_ieq(pick, "dd")) return -1;
    if (klms_ieq(pick, "dm")) {
        if (klms_ieq(t->e[ev].dflt, "dd")) return -1;
        c = klms_find_ch(t, ev, t->e[ev].dflt);
    } else c = klms_find_ch(t, ev, pick);
    if (c < 0) { if (why) *why = KLMS_UNKNOWN; return -1; }
    if (why) *why = KLMS_CHOICE;
    return c;
}

static void klms_put32(unsigned char *p, unsigned long v)
{
    p[0] = (unsigned char)v; p[1] = (unsigned char)(v >> 8); p[2] = (unsigned char)(v >> 16); p[3] = (unsigned char)(v >> 24);
}

/* hash of the CHOICES (not the picks' spelling): same choices -> same temp file name. pick[ev] = the chosen choice index or -1. */
static unsigned long klms_choice_hash(const klms_tab *t, const int *pick)
{
    unsigned long h = KLMS_FNV0; int i;
    for (i = 0; i < t->nev; i++) {
        unsigned char b[4]; int c = pick[i];
        klms_put32(b, t->whdhash); h = klms_fnv(b, 4, h);
        klms_put32(b, (unsigned long)(i * 1000 + (c + 1))); h = klms_fnv(b, 4, h);
        if (c >= 0) { int f; for (f = 0; f < KLMS_NF; f++) { klms_put32(b, t->c[c].v[f]); h = klms_fnv(b, 4, h); } }
    }
    return h;
}

/* picks[ev] = the ini text of each event (may be NULL entries). Patches whd (len bytes) in place for the chosen events.
 * -> number of records changed (>= 0), or -1 with err (nothing changed). choice[] (KLMS_MAXEV ints) receives the choice index per event
 * (-1 = stock), a pick naming no choice stays stock (the caller logs it: klms_resolve says KLMS_UNKNOWN). */
static int klms_apply(unsigned char *whd, size_t len, const klms_tab *t, const char *const *picks, int *choice, char *err, size_t cap)
{
    int ev, f, changed = 0; int why;
    if (len != t->whdlen) { klms_msg(err, cap, 0, ".WHD is %lu bytes, the table says %lu", (unsigned long)len, t->whdlen); return -1; }
    if (klms_fnv(whd, len, KLMS_FNV0) != t->whdhash) { klms_msg(err, cap, 0, ".WHD hash is not the table's %08lx (another stock bank)", t->whdhash); return -1; }
    for (ev = 0; ev < t->nev; ev++) {
        int c = klms_resolve(t, ev, picks ? picks[ev] : 0, &why);
        if (choice) choice[ev] = c;
        if (c < 0) continue;
        for (f = 0; f < KLMS_NF; f++)
            if ((unsigned long)t->e[ev].rec + t->fo[f] + 4 > len) { klms_msg(err, cap, 0, "event %s: record %x lies outside the .WHD", t->e[ev].name, t->e[ev].rec); return -1; }
        if (!t->c[c].v[0] || !t->c[c].v[1] || !t->c[c].v[2]) { klms_msg(err, cap, 0, "choice %s of %s has pcm/size/samples 0", t->c[c].name, t->e[ev].name); return -1; }
        if (t->c[c].v[4] || t->c[c].v[3] + t->c[c].v[1] > t->wavlen || t->c[c].v[3] < 16) { klms_msg(err, cap, 0, "choice %s of %s: data %lx+%lx leaves the .WAV (%lu bytes)", t->c[c].name, t->e[ev].name, t->c[c].v[3], t->c[c].v[1], t->wavlen); return -1; }
    }
    for (ev = 0; ev < t->nev; ev++) {
        int c = choice ? choice[ev] : -1;
        if (!choice) { c = klms_resolve(t, ev, picks ? picks[ev] : 0, &why); }
        if (c < 0) continue;
        for (f = 0; f < KLMS_NF; f++) klms_put32(whd + t->e[ev].rec + t->fo[f], t->c[c].v[f]);
        changed++;
    }
    return changed;
}

#endif
