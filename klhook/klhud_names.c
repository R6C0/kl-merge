/*
 * klhud_names.c - THE NAMES OF THE CREW: the character he was given, and initials over the head.
 * Included by klhook.c AFTER klcrew.c and BEFORE klhud.c (it uses klw_who_now / klw_source / klw / klc_same_code, klhud.c calls
 * klnm_name). Spec, the reading with addresses, the decision, the WIRING and live check N1: re\hud_names.md.
 *
 * Owner (2026-10-12): 'for how the names are i want it to be that characters one that got randomised and maybe initials for like
 * above their head?'  So:
 *   1. THE CREW LIST shows, per heister, the NAME OF THE CHARACTER he wears (klcrew.c's random draw, or the body he came with):
 *      klnm_name(record, ...) - the answer of a pure READ (klw_who_now: the model each member wears now -> the level's wardrobe
 *      name, else the eight heister-table names). The game's own name string is not the source and is not needed for the list.
 *   2. THE TAG OVER A HEISTER'S HEAD ('Tommy / $0' in the pictures) shows his INITIALS. The element that draws that tag is NOT
 *      identified in kl2.exe (re\hud_names.md 2: it is not ZPlayerNameDisplay, not the player list, not the kill feed); what is
 *      known is that its text is the name in the record's client block ([[record]+8], the string klcrew.c's Names key rewrites -
 *      the picture shows 'Tommy' on a body that klcrew.c had drawn, i.e. the stock name). So [HUD] NameTags writes THAT string, with
 *      the game's own two calls (0x83e2e0 makes the string, 0x469250 hands it to the block), exactly as klcrew.c's klw_rename.
 *      It is a data write on the game's thread through two routines the game itself calls; nothing is patched.
 *
 * Keys ([HUD]; every default is 0 unless [HUD] Draft=1, then as noted):
 *   Names=1       the list's names come from klnm_name (the character); 0 = the record's own string, as before (forced on while NameTags is on).   (Draft: 1)
 *   NameTags=1    0 = the tags keep the game's name, 1 = INITIALS, 2 = the character's full name (= klcrew's Names=1).  (Draft: 1)
 *   OwnName=0     your own row: 0 = the name of YOUR character (when he wears one of the wardrobe), 1 = your Steam name.
 *   Log           the hud's: 1 says what is on, 2 lists record -> game name -> character -> initials once per change.
 * Stands down: not Arcade, the rules object not ZGameRulesHeist, [Crew] Names=1 with NameTags=1 (two writers of one string: klcrew.c
 * wins, the list still shows the characters), the two game routines not the ones this build knows, a tick off the game's thread.
 * The human's own record is NEVER renamed (his tag is not drawn over his own head, his row has its own key).
 *
 * THE INITIALS RULE (klnm_initials_one / klnm_unique, a pure function, self-test in re\hud_names.md 4):
 *   words = runs of letters and digits; the base = the first letter of each word in capitals ('Kane' -> K, 'J.C.' -> JC, 'Red' -> R);
 *   when two of the crew would get the same text, those get the first TWO letters of the first word + the first letters of the rest
 *   ('Liam' / 'Lynch' -> LI / LY), if still equal THREE letters, and an identical rest gets a digit (TOM, TOM2).
 */
#ifndef KLHUD_NAMES_C
#define KLHUD_NAMES_C

#define KLNM_MAXINI 8

/* ---------------------------------------------------------------- the pure part (no game, no globals) */

static int klnm_isword(unsigned char c) { return (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || c >= 0x80; }
static char klnm_up(char c) { return c >= 'a' && c <= 'z' ? (char)(c - 32) : c; }

/* one UTF-8 character (its lead byte and continuation bytes) from s to out; -> bytes copied */
static int klnm_ch(const char *s, char *out)
{
    int n = 1;
    out[0] = klnm_up(s[0]);
    while (((unsigned char)s[n] & 0xc0) == 0x80 && n < 4) { out[n] = s[n]; n++; }
    return n;
}

/* level 0: the first letter of every word; level k >= 1: the first k + 1 letters of the first word, then the first letters of the others.
   -> the text in out (at most cap - 1 bytes), '?' for a name without a letter */
static void klnm_initials_one(const char *name, int level, char *out, int cap)
{
    int o = 0, firstword = 1; const char *p = name ? name : "";
    if (cap < 2) { if (cap > 0) out[0] = 0; return; }
    while (*p) {
        while (*p && !klnm_isword((unsigned char)*p)) p++;
        if (!*p) break;
        {
            int want = firstword ? (level < 1 ? 1 : level + 1) : 1, k;
            for (k = 0; k < want && klnm_isword((unsigned char)*p); k++) {
                char tmp[4]; int n = klnm_ch(p, tmp), j;
                if (o + n > cap - 1) break;
                for (j = 0; j < n; j++) out[o++] = tmp[j];
                p += n;
            }
        }
        while (klnm_isword((unsigned char)*p)) p++;                /* the rest of the word */
        firstword = 0;
        if (o >= cap - 1 || o >= KLNM_MAXINI - 1) break;
    }
    if (!o) out[o++] = '?';
    out[o] = 0;
}

/* the initials of n names that must all differ: out[i] gets a text of at most KLNM_MAXINI bytes. names[i] == NULL or "" -> out "" */
static void klnm_unique(const char *const *names, int n, char out[][KLNM_MAXINI])
{
    int i, j, level, dup[64]; 
    if (n > 64) n = 64;
    for (i = 0; i < n; i++) { if (names[i] && names[i][0]) klnm_initials_one(names[i], 0, out[i], KLNM_MAXINI); else out[i][0] = 0; }
    for (level = 1; level <= 2; level++) {
        int any = 0;
        for (i = 0; i < n; i++) { dup[i] = 0; if (out[i][0]) for (j = 0; j < n; j++) if (j != i && !_stricmp(out[i], out[j])) { dup[i] = 1; any = 1; break; } }
        if (!any) return;
        for (i = 0; i < n; i++) if (dup[i]) klnm_initials_one(names[i], level, out[i], KLNM_MAXINI);
    }
    for (i = 0; i < n; i++)                                       /* still equal (the same name twice): a digit from the second on */
        for (j = 0; j < i; j++) if (out[i][0] && !_stricmp(out[i], out[j])) {
            int k = 2, tries = 0; char t[KLNM_MAXINI + 4];
            do {
                size_t l = strlen(out[i]); if (l > KLNM_MAXINI - 3) l = KLNM_MAXINI - 3;
                memcpy(t, out[i], l); snprintf(t + l, sizeof t - l, "%d", k++);
                for (int m = 0; m < n; m++) if (m != i && !_stricmp(t, out[m])) { t[0] = 0; break; }
            } while (!t[0] && ++tries < 8);
            if (t[0]) { strncpy(out[i], t, KLNM_MAXINI - 1); out[i][KLNM_MAXINI - 1] = 0; }
            break;
        }
}

#ifndef KLNM_PURE_ONLY

/* ---------------------------------------------------------------- the game side */

/* stock = the name the GAME gave him (never our own text, S2); tagged = the last text WE wrote into his string */
struct klnm_rec { int used, ch, human, tries, told; DWORD actor, at; char stock[48], chr[32], ini[KLNM_MAXINI], tagged[48]; };

static struct { int on, tags, own, log, names_conflict; } klnm;
static struct { DWORD rules, last, state, since; int n, left; struct klnm_rec r[KLW_NREC]; } klnm_r;

static void klnm_read_name(DWORD at, char *out, int cap)
{   /* [[record]+8], as klhud.c reads it (0x841e50's record, the client block, the string's first pointer) */
    DWORD blk, str = 0; out[0] = 0;
    if ((blk = klh_rd32(at)) != 0 && klh_rd(blk + 8, &str, 4) && str) klh_rdstr(str, out, cap);
}

/* S1 / S2: take the record's current string as the game's name - unless it is empty (not set yet) or is what we wrote ourselves */
static void klnm_learn(struct klnm_rec *q)
{
    char cur[48]; klnm_read_name(q->at, cur, sizeof cur);
    if (!cur[0]) return;
    if (q->stock[0] && q->tagged[0] && !strcmp(cur, q->tagged)) return;
    snprintf(q->stock, sizeof q->stock, "%s", cur);
}

/* what the list and the tags show for each record now. Rate-limited to one read of the crew per 250 ms; off the game's thread too
   (reads only). -> 1 when the table is current */
static int klnm_refresh(void)
{
    struct klw_who w; struct klw_src src; DWORD hero[8]; int k, i, na = 0, changed = 0; const char *nm[KLW_NREC]; int idx[KLW_NREC]; char ini[KLW_NREC][KLNM_MAXINI]; char seen[KLW_NREC];
    DWORD now = GetTickCount();
    if (klnm_r.rules && (LONG)(now - klnm_r.last) < 250) return 1;
    klnm_r.last = now;
    if (!klh_exe_ok || !klw_who_now(&w)) { klnm_r.rules = 0; return 0; }
    if (w.rules != klnm_r.rules) { memset(klnm_r.r, 0, sizeof klnm_r.r); klnm_r.rules = w.rules; klnm_r.left = 0; klnm_r.since = now; }
    klnm_r.state = w.state;
    if (!klh_rd(w.rules + 0x208, hero, sizeof hero)) return 0;
    klw_source(&src, hero, w.key);
    memset(seen, 0, sizeof seen);
    for (k = 0; k < w.n; k++) {
        struct klnm_rec *q; int rec = w.m[k].rec, ch = w.m[k].ch;
        if (rec < 0 || rec >= KLW_NREC) continue;
        q = &klnm_r.r[rec]; seen[rec] = 1;
        if (!q->used || q->at != w.m[k].at || q->actor != w.m[k].actor) {       /* a new member in this slot: the name the game gave him is the fallback */
            struct klnm_rec old = *q;                                           /* S2: the slot's old stock / tagged texts decide whether the string now is OURS */
            memset(q, 0, sizeof *q); q->used = 1; q->at = w.m[k].at; q->actor = w.m[k].actor; changed = 1;
            if (old.at == q->at) { memcpy(q->stock, old.stock, sizeof q->stock); memcpy(q->tagged, old.tagged, sizeof q->tagged); }
            klnm_learn(q);
        }
        q->used = 1;
        q->human = (k == w.human);
        if (q->human) { q->tagged[0] = 0; klnm_learn(q); }                       /* his is never rewritten: keep it current */
        else if (!q->stock[0]) klnm_learn(q);                                    /* S1: the string was empty at first sight */
        if (ch != q->ch) { q->ch = ch; q->tries = 0; q->told = 0; changed = 1; }
        if (ch >= 1 && ch <= src.n) snprintf(q->chr, sizeof q->chr, "%s", src.c[ch - 1].name); else q->chr[0] = 0;
    }
    for (i = 0; i < KLW_NREC; i++)                                                /* S5: a record that left the crew is not 'used' any more (its texts are kept for S2) */
        if (!seen[i] && klnm_r.r[i].used) { klnm_r.r[i].used = 0; changed = 1; }
    for (i = 0; i < KLW_NREC; i++) {                                              /* initials among the AI heisters of this round only */
        struct klnm_rec *q = &klnm_r.r[i];
        if (!q->used || q->human) continue;
        nm[na] = q->chr[0] ? q->chr : q->stock; idx[na++] = i;
    }
    if (na) klnm_unique(nm, na, ini);
    for (i = 0; i < na; i++) { if (strcmp(klnm_r.r[idx[i]].ini, ini[i])) changed = 1; snprintf(klnm_r.r[idx[i]].ini, KLNM_MAXINI, "%s", ini[i]); }
    klnm_r.n = w.n;
    if (changed) klnm_r.since = now;                                              /* S1: the crew moved: the tick waits until it has stood still */
    if (changed && klnm.log > 1) {
        for (i = 0; i < KLW_NREC; i++) {
            struct klnm_rec *q = &klnm_r.r[i];
            if (q->used) klog("names: record %d%s: game name '%s' -> character '%s' -> %s '%s'", i, q->human ? " (you)" : "", q->stock, q->chr[0] ? q->chr : "(none: his own name)",
                              q->human ? "list" : "tag", q->human ? (klnm.own ? q->stock : q->chr[0] ? q->chr : q->stock) : q->ini);
        }
    }
    return 1;
}

/* THE LIST'S NAME for the record at 'at' (the address klb_read gives: recs + 0x7c * i). -> 1 and the name in out; 0 = leave the game's own */
static int klnm_name(DWORD at, char *out, int cap)
{
    int i;
    if (!klnm.on || cap < 2 || !klnm_refresh()) return 0;
    for (i = 0; i < KLW_NREC; i++) {
        const struct klnm_rec *q = &klnm_r.r[i];
        if (!q->used || q->at != at) continue;
        if (q->human && klnm.own) return 0;                                        /* his Steam name: the record's own string */
        snprintf(out, (size_t)cap, "%s", q->chr[0] ? q->chr : q->stock);
        return out[0] != 0;
    }
    return 0;
}

/* THE TAG'S INITIALS for the record at 'at' without writing anything (klhud_tags.c: the hook draws the tag itself, the record keeps its full
   name for the kill feed and the score page). -> 1 and the initials in out; 0 = unknown (the caller falls back to the record's own string) */
static int klnm_tag_ini(DWORD at, char *out, int cap)
{
    int i;
    if (cap < 2 || !klnm_refresh()) return 0;
    for (i = 0; i < KLW_NREC; i++) {
        const struct klnm_rec *q = &klnm_r.r[i];
        if (!q->used || q->at != at || q->human || !q->ini[0]) continue;
        snprintf(out, (size_t)cap, "%s", q->ini);
        return 1;
    }
    return 0;
}

/* the game's two steps (kl2 0x588980 / 0x8f5f99 as klcrew.c's klw_rename): a string of its heap from the text, handed (and given up)
   to the record's client block. Game thread only. -> 1 when the record now holds the text */
static int klnm_write(struct klnm_rec *q, const char *want)
{
    DWORD blk = klh_rd32(q->at), s[3] = { 0, 0, 0 }; char cur[48]; DWORD len;
    struct { char *b, *e, *c; } t = { 0, 0, 0 };
    if (!blk || !klh_rd(blk + 8, s, sizeof s)) return 0;
    len = s[1] - s[0]; cur[0] = '?'; cur[1] = 0;
    if (s[0] && s[1] >= s[0] && len < sizeof cur - 1 && klh_rd(s[0], cur, len)) cur[len] = 0;
    if (!strcmp(cur, want)) { snprintf(q->tagged, sizeof q->tagged, "%s", want); return 2; }      /* already there: no call, no try used */
    ((void *(__fastcall *)(void *, void *, const char *))(DWORD_PTR)KLH_VA(KLW_STRING))(&t, 0, want);
    if (!t.b) { klog("names: record: the game made no string for '%s': not renamed", want); return 0; }
    ((void (__fastcall *)(void *, void *, char *, char *, char *))(DWORD_PTR)KLH_VA(KLW_RENAME))((void *)(DWORD_PTR)blk, 0, t.b, t.e, t.c);
    snprintf(q->tagged, sizeof q->tagged, "%s", want);                             /* S2: remembered, so a later look at the string knows it is ours */
    if (klnm.log > 1) klog("names: the tag text of the record at %08lx is now '%s' (was '%s')", q->at, want, cur);
    return 1;
}

static void klnm_tick(int game_thread)
{
    static const BYTE string_code[15] = { 0x56, 0x8b, 0xf1, 0x8b, 0x4c, 0x24, 0x08, 0x8d, 0x44, 0x24, 0x08, 0x50, 0x51, 0x8b, 0xce };          /* 0x83e2e0 (klcrew.c) */
    static const BYTE rename_code[12] = { 0x6a, 0xff, 0x68, 0x98, 0xbe, 0xad, 0x00, 0x64, 0xa1, 0x00, 0x00, 0x00 };                          /* 0x469250 (klcrew.c) */
    static int toldconf, toldcode, toldthread, codeok = -1; int i, calls = 0, v; char why[200]; DWORD now = GetTickCount();
    if (!klnm.tags || !klh_exe_ok) return;
    if (!game_thread) { if (!toldthread++) klog("names: the tick is not on the game's thread: the tag texts cannot be written"); return; }       /* S6: before any touch of the table */
    if (!klb_level(why)) return;                                                   /* M2: only a level that is NOT the stock one of its slot (klcrew.c's gate) */
    if (klw.names && klnm.tags == 1) { if (!toldconf++) klog("names: [Crew] Names=1 writes the full character name into the tags and [HUD] NameTags=1 wants initials: [Crew] Names=0 is needed; the tags are left to klcrew.c"); return; }
    if (klw.names) return;                                                         /* NameTags=2: klcrew.c does it */
    if (!klnm_refresh() || !klnm_r.rules) return;
    if (klnm_r.state >= 0x1f) { klnm_r.left = 1; return; }                         /* S3: the score page: the next round starts the tries afresh */
    if (klnm_r.state < 0x12 || klnm_r.state > 0x19) return;                        /* S1: only between the load and the end of a round (klcrew.c) */
    if (klnm_r.left) {
        klnm_r.left = 0;
        for (i = 0; i < KLW_NREC; i++) { klnm_r.r[i].tries = 0; klnm_r.r[i].told = 0; }
        klnm_r.since = now;
    }
    if ((LONG)(now - klnm_r.since) < 1500) return;                                 /* S1: the crew has stood still for 1.5 s (a new member, a new body) */
    if (codeok < 0) codeok = klc_same_code(KLW_STRING, string_code, sizeof string_code) && klc_same_code(KLW_RENAME, rename_code, sizeof rename_code);
    if (!codeok) { if (!toldcode++) klog("names: the two name routines are not the ones this build knows: the tags keep the game's names"); return; }
    for (i = 0; i < KLW_NREC && calls < 2; i++) {
        struct klnm_rec *q = &klnm_r.r[i]; const char *want; BYTE st = 0xff;
        if (!q->used || q->human || !q->stock[0]) continue;                        /* S1: the game's string must exist */
        if (q->tries >= 3) { if (!q->told++) klog("names: the record at %08lx took its tag text three times and the game set it back: left alone for this round", q->at); continue; }
        if (!klh_rd(q->at + 0x10, &st, 1) || st) continue;                         /* aboard / dead: left as it is */
        want = klnm.tags == 2 ? (q->chr[0] ? q->chr : q->stock) : q->ini;
        if (!want[0]) continue;
        v = klnm_write(q, want);
        if (v == 1) { q->tries++; calls++; }
    }
}

static void klnm_init(void)
{
    int draft = (int)GetPrivateProfileIntA("HUD", "Draft", 0, klh_ini), v;
    memset(&klnm, 0, sizeof klnm); memset(&klnm_r, 0, sizeof klnm_r);
    v = (int)GetPrivateProfileIntA("HUD", "Names", draft, klh_ini); klnm.on = v < 0 ? 0 : v > 1 ? 1 : v;
    /* 2026-10-12: with [HUD] HeadTags (klhud_tags.c) the hook draws the initials itself and the record keeps its full name (kill feed, score
       page): NameTags then defaults to 0. Without HeadTags under Draft it stays 1 (the rename). A key that is set still wins. */
    v = (int)GetPrivateProfileIntA("HUD", "HeadTags", draft, klh_ini);
    v = (int)GetPrivateProfileIntA("HUD", "NameTags", draft && v == 0, klh_ini); klnm.tags = v < 0 ? 0 : v > 2 ? 2 : v;       /* M1: not 'Tags' (klhud.c's TRAITOR text key) */
    v = (int)GetPrivateProfileIntA("HUD", "OwnName", 0, klh_ini); klnm.own = v != 0;
    klnm.log = (int)GetPrivateProfileIntA("HUD", "Log", 1, klh_ini);
    if (klnm.tags && !klnm.on) { klnm.on = 1; klog("names: [HUD] NameTags is on, so the list shows the character's name too (Names=0 cannot be kept: the list would show the initials)"); }      /* S4 */
    if (klnm.on || klnm.tags) klog("names: on; list = %s, tags = %s, own row = %s", klnm.on ? "the character's name" : "the game's name",
                                    klnm.tags == 0 ? "the game's" : klnm.tags == 1 ? "initials" : "the character's full name", klnm.own ? "your Steam name" : "your character's name");
}

#endif /* KLNM_PURE_ONLY */
#endif /* KLHUD_NAMES_C */
