/* klshopset.h - the PURE parts of the shop page II "set check" ([ShopPage] SetCheck / SetCheckStrict, 2026-11-08): which page II set a peer runs
 * (pd2 / dm / stock), told over klnetchan as type SHPH, compared by a 32-bit hash. No game reads, no windows.h, no sockets: klshoppage_online.c feeds it.
 * Checked off-game by klshopset_test.c; the Python twin is tools/kl_fallback_guns.py set_hash(), same golden vectors (tools/kl_fallback_guns_test.py).
 *
 * WHY: a page II gun is a look on a fixed (row, carrier item, picture row) pair. Two peers with a different KLShopPage.ini (other set, other pairs) buy the same carrier,
 * each relabels its own pool, and the card and the gun in hand silently differ per peer. The check makes that visible, and (strict) refuses the page II press.
 * NO GAMEPLAY STATE DEPENDS ON THE HASH: the carrier-row buy path is the stock one.
 *
 * HASH: FNV-1a 32 over the canonical string
 *     "KLSET1\n" + for every page II row ascending: "<row>|<item>|<picrow>\n" + "S=<set name>\n"
 * Display names, descriptions, [Tabs] and the zip chunk count are NOT in it (they differ legitimately between builds and maps).
 * Row set = what kspg_load keeps: pairs Pn (n < Count, Count 0..KSS_ROWS) that parse as row|item|pic| with row 0..35 and item 1..63; a later Pn of the same row replaces the
 * earlier one. Set name = [Set] Name of KLShopPage.ini, normalised by kss_name (leading token of A-Z a-z 0-9 _ -, lower case, 15 chars; empty / absent = "pd2").
 *
 * MESSAGE (type SHPH, ASCII, <= KSS_PAY_MAX bytes):  v1s<seat 0..15>h<8 hex>n<pairs 0..36>t<set type 0 pd2, 1 dm, 2 stock, 3 other>     e.g. v1s1h1a2b3c4dn13t0
 * Anything that does not fit this exactly is dropped by kss_parse (a receiver never indexes with an unchecked number). An old build has no SHPH handler: its peer stays UNKNOWN.
 *
 * DECISION TABLE (kss_decide; check = [ShopPage] SetCheck, strict = SetCheckStrict):
 *   check 0                      ALLOW        (today's behaviour exactly)
 *   MATCH                        ALLOW
 *   MISMATCH / UNKNOWN, strict 0 ALLOW_WARN   (log + caption, never refuse)
 *   MISMATCH / UNKNOWN, strict 1 REFUSE       (page II press only; page I is untouched)
 */
#ifndef KLSHOPSET_H
#define KLSHOPSET_H

#include <stdio.h>
#include <string.h>

#define KSS_ROWS     36
#define KSS_SEATS    16
#define KSS_NAME_MAX 16
#define KSS_PAY_MAX  40
#define KSS_PIC_MAX  99999                                   /* a picture row is clamped to -KSS_PIC_MAX..KSS_PIC_MAX (tools/kl_fallback_guns.py SET_PIC_MAX, same clamp) */
#define KSS_ROW_LEN  16                                      /* worst case "35|63|-99999\n" = 13 chars; 16 leaves slack */
#define KSS_CANON_MAX (8 + KSS_ROWS * KSS_ROW_LEN + 4 + KSS_NAME_MAX + 4)

enum { KSS_UNKNOWN = 0, KSS_MATCH = 1, KSS_MISMATCH = 2 };
enum { KSS_ALLOW = 0, KSS_ALLOW_WARN = 1, KSS_REFUSE = 2 };

struct kss_row { int ok, item, pic; };                       /* indexed by page II row */

static unsigned kss_fnv(const char *s, int len)
{
    unsigned h = 2166136261u; int i;
    for (i = 0; i < len; i++) { h ^= (unsigned char)s[i]; h *= 16777619u; }
    return h;
}

/* the set name: leading whitespace skipped, then the leading run of [A-Za-z0-9_-] lower-cased (<= 15 chars); anything else ends it (a trailing "; comment" included) */
static void kss_name(const char *raw, char *out)
{
    int n = 0;
    if (raw) {
        while (*raw == ' ' || *raw == '\t') raw++;
        for (; *raw && n < KSS_NAME_MAX - 1; raw++) {
            char c = *raw;
            if (c >= 'A' && c <= 'Z') c = (char)(c + 32);
            if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_' || c == '-')) break;
            out[n++] = c;
        }
    }
    if (!n) { strcpy(out, "pd2"); return; }
    out[n] = 0;
}

/* canonical string -> length (0 = does not fit) */
static int kss_canon(const struct kss_row *rows, const char *rawname, char *out, int cap)
{
    int r, n, w; char nm[KSS_NAME_MAX];
    if (!rows || !out || cap < KSS_CANON_MAX) return 0;
    kss_name(rawname, nm);
    n = snprintf(out, (size_t)cap, "KLSET1\n");
    for (r = 0; r < KSS_ROWS; r++) {
        int item, pic;
        if (n < 0 || n >= cap) return 0;                       /* never hand snprintf a negative / wrapped size */
        if (!rows[r].ok) continue;
        item = rows[r].item; pic = rows[r].pic;
        if (item < 1 || item > 63) continue;                   /* the loader never keeps these (kspg_load / set_rows); a hand-built row is skipped the same way */
        if (pic < -KSS_PIC_MAX) pic = -KSS_PIC_MAX; else if (pic > KSS_PIC_MAX) pic = KSS_PIC_MAX;
        w = snprintf(out + n, (size_t)(cap - n), "%d|%d|%d\n", r, item, pic);
        if (w < 0 || w >= cap - n) return 0;
        n += w;
    }
    if (n < 0 || n >= cap) return 0;
    w = snprintf(out + n, (size_t)(cap - n), "S=%s\n", nm);
    if (w < 0 || w >= cap - n) return 0;
    n += w;
    return n > 0 && n < cap ? n : 0;
}

static unsigned kss_hash(const struct kss_row *rows, const char *rawname)
{
    char b[KSS_CANON_MAX + 8]; int n = kss_canon(rows, rawname, b, (int)sizeof b);
    return n ? kss_fnv(b, n) : 0;
}

static int kss_count(const struct kss_row *rows)
{
    int r, n = 0;
    for (r = 0; r < KSS_ROWS; r++) if (rows[r].ok) n++;
    return n;
}

/* 0 pd2, 1 dm, 2 stock, 3 other (informational only: the hash already holds the name) */
static int kss_type(const char *rawname)
{
    char nm[KSS_NAME_MAX]; kss_name(rawname, nm);
    return !strcmp(nm, "pd2") ? 0 : !strcmp(nm, "dm") ? 1 : !strcmp(nm, "stock") ? 2 : 3;
}

/* ---- the SHPH payload */
struct kss_msg { int seat, pairs, type; unsigned hash; };

static int kss_encode(char *out, int cap, int seat, unsigned hash, int pairs, int type)
{
    int n;
    if (!out || cap < KSS_PAY_MAX || seat < 0 || seat >= KSS_SEATS || pairs < 0 || pairs > KSS_ROWS || type < 0 || type > 3) return 0;
    n = snprintf(out, (size_t)cap, "v1s%dh%08xn%dt%d", seat, hash, pairs, type);
    return n > 0 && n < KSS_PAY_MAX ? n : 0;
}

static int kss_num(const char **p, int maxdig, int lo, int hi, int *v)
{
    int n = 0, x = 0;
    while (n < maxdig && **p >= '0' && **p <= '9') { x = x * 10 + (**p - '0'); (*p)++; n++; }
    if (!n || x < lo || x > hi) return 0;
    *v = x; return 1;
}

/* -> 1 and *m filled; 0 for anything malformed (length, version, field order, range, hex) */
static int kss_parse(const char *pay, struct kss_msg *m)
{
    const char *p = pay; int i, len = 0; unsigned h = 0;
    if (!pay || !m) return 0;
    while (len <= KSS_PAY_MAX && pay[len]) len++;
    if (len > KSS_PAY_MAX || len < 12) return 0;
    if (*p++ != 'v' || *p++ != '1' || *p++ != 's') return 0;
    if (!kss_num(&p, 2, 0, KSS_SEATS - 1, &m->seat)) return 0;
    if (*p++ != 'h') return 0;
    for (i = 0; i < 8; i++, p++) {
        char c = *p; unsigned d;
        if (c >= '0' && c <= '9') d = (unsigned)(c - '0'); else if (c >= 'a' && c <= 'f') d = (unsigned)(c - 'a' + 10); else if (c >= 'A' && c <= 'F') d = (unsigned)(c - 'A' + 10); else return 0;
        h = h << 4 | d;
    }
    m->hash = h;
    if (*p++ != 'n') return 0;
    if (!kss_num(&p, 2, 0, KSS_ROWS, &m->pairs)) return 0;
    if (*p++ != 't') return 0;
    if (!kss_num(&p, 1, 0, 3, &m->type)) return 0;
    return *p == 0;
}

/* ---- what this peer has heard */
/* ident = what identified the seat's player last time (0 = seat empty); sid = the netchan session id that last announced for the seat (0 = none / not known);
 * fresh/freshAt = a DIFFERENT sid announced for the seat at freshAt and the watch has not yet seen the occupant change.
 * The seat number in SHPH is what the sender wrote: netchan has no authenticated sender, so a modded peer can claim any seat. The check is a consistency aid, not anti-cheat. */
struct kss_peers { int have[KSS_SEATS]; unsigned h[KSS_SEATS]; int hostHave; unsigned hostH; unsigned ident[KSS_SEATS]; unsigned sid[KSS_SEATS]; int fresh[KSS_SEATS]; unsigned freshAt[KSS_SEATS]; };

#define KSS_FRESH_MS 3000u   /* GUESS: a new occupant's announce that arrives before the 0.5 s seat watch sees the change is kept when the change shows up within 3 s */

static void kss_reset(struct kss_peers *p) { memset(p, 0, sizeof *p); }

/* a parsed SHPH from a sender of role 2 (host) or 3 (client) with netchan session id sid (0 = unknown) at time now (ms);
 * -> 1 when it is new or changed what we knew, 0 when nothing changed / role not usable */
static int kss_note_from(struct kss_peers *p, int sender_role, const struct kss_msg *m, unsigned sid, unsigned now)
{
    int s, ch;
    if (!p || !m) return 0;
    if (sender_role == 2) { ch = !p->hostHave || p->hostH != m->hash; p->hostHave = 1; p->hostH = m->hash; return ch; }
    if (sender_role != 3 || m->seat < 0 || m->seat >= KSS_SEATS) return 0;
    s = m->seat;
    ch = !p->have[s] || p->h[s] != m->hash;
    if (sid && p->sid[s] && p->sid[s] != sid) { p->fresh[s] = 1; p->freshAt[s] = now; ch = 1; }   /* another sender for this seat: most likely the next occupant */
    if (sid) p->sid[s] = sid;
    p->have[s] = 1; p->h[s] = m->hash;
    return ch;
}

static int kss_note(struct kss_peers *p, int sender_role, const struct kss_msg *m) { return kss_note_from(p, sender_role, m, 0, 0); }

/* the seat's occupant as the reader sees it (ident 0 = seat empty / not in use) at time now (ms). A changed ident drops what we knew of that seat, so a different build that takes
 * the seat is UNKNOWN until it announces - except when a new sender announced for the seat within KSS_FRESH_MS before the change was seen (its entry is the new occupant's).
 * -> 1 when an entry was dropped. */
static int kss_seat_ident(struct kss_peers *p, int seat, unsigned ident, unsigned now)
{
    int cleared = 0;
    if (!p || seat < 0 || seat >= KSS_SEATS) return 0;
    if (p->ident[seat] != ident) {
        int keep = ident && p->fresh[seat] && now - p->freshAt[seat] <= KSS_FRESH_MS;
        if (p->ident[seat] && p->have[seat] && !keep) {   /* first sight of a seat (old ident 0) keeps an entry that arrived before the watch saw it */
            p->have[seat] = 0; p->h[seat] = 0; p->sid[seat] = 0; cleared = 1;
        }
        p->fresh[seat] = 0; p->ident[seat] = ident;
    }
    return cleared;
}

static int kss_state(int have, unsigned theirs, int mine_have, unsigned mine)
{
    if (!have || !mine_have) return KSS_UNKNOWN;
    return theirs == mine ? KSS_MATCH : KSS_MISMATCH;
}

static int kss_state_host(const struct kss_peers *p, int mine_have, unsigned mine) { return kss_state(p->hostHave, p->hostH, mine_have, mine); }
static int kss_state_seat(const struct kss_peers *p, int seat, int mine_have, unsigned mine)
{
    if (seat < 0 || seat >= KSS_SEATS) return KSS_UNKNOWN;
    return kss_state(p->have[seat], p->h[seat], mine_have, mine);
}

static int kss_decide(int check, int strict, int state)
{
    if (!check || state == KSS_MATCH) return KSS_ALLOW;
    return strict ? KSS_REFUSE : KSS_ALLOW_WARN;
}

#endif /* KLSHOPSET_H */
