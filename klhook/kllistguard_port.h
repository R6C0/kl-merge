/* kllistguard_port.h - [Crash] ListUserGuard=2: a faithful C port of CListUser slot 0 (kl2.exe build 0490, 0x630700, thiscall(this, n, rec), ret 8)
 * with ONE change: a key of 0 is never given to the hash/range helpers. No windows.h, no game access of its own (the helpers are passed in as
 * function pointers), 32-bit only (pointers are stored as 32-bit words in the game's arrays). Tested by kllistguard_test.c.
 *
 * DISASSEMBLY of 0x630700 (capstone, 2026-11-10; "key(r)" = [r+0x54] & 0xffffff, "flag(r)" = [r+0x3c] |= 0x1000000):
 *   this+0x20 table T   hash by key: T[key] = chain head (nodes of 3 record words + next at +0xc), T[key+1..] = sorted range list of record words
 *   this+0x38 A         the new set: n record pointers, filled by the caller 0x5bfc03 (it only lists records with key != 0, test at 0x5bfb9f)
 *   this+0x3c B, this+0x40 C   scratch. No other state: NOTHING is reset or cleared after the loops (no count, no array clear); the function ends
 *                       with flag(rec) and `ret 8`. The arrays are re-filled by the caller on its next call.
 *   argrec = rec, argkey = key(rec).
 *   1. if n > 1: sort A (0x4e2b90, randomized quicksort, cdecl(arr, 0, n-1)).
 *   2. rv = 0x8176f0(this, B, argkey) decodes the old range list of argkey into B; start = rv & 0xffff, cnt = rv >> 16; sort B[start..start+cnt) (0x4e2b90).
 *   3. 0x881ef0(C, B, start, B+start, cnt) = merge of the two sorted runs into C: C = the OLD set of argkey (total = start + cnt records).
 *   4. LOOP 1 (merge-diff of C against A): for each C record c: flag(c); advance through A while A < c; A == c -> A[j] = 0 (kept: in both sets);
 *      c not in A (A exhausted or c < A[j]) -> the record left the set: pair(key(c), argrec); pair(argkey, c).
 *      pair(k, r) = if (0x4f8a60(k, r, 1) & 1) 0x6986b0(k, r, 1)  (remove r from k's chain, then from k's range list) - 5 call sites in all.
 *   5. LOOP 2: compact A (drop the zeros) -> cnt2 records = the ones NEW in the set; if cnt2: r = 0x5a4ad0(argkey, A, cnt2) (append all A to argkey's chain,
 *      returns how many fitted). r < cnt2 (alloc failure): roll back the first r (flag + pair(argkey, A[i])) and cnt2 = 0.
 *   6. LOOP 3: for each of the cnt2 new records a: r = 0x5a4ad0(key(a), &argrec, 1); flag(a); r != 1 -> pair(key(a), argrec) and pair(argkey, a).
 *   7. flag(argrec); return.
 *
 * THE BUG: loop 1's C comes from T[argkey] = pointers stored earlier. A record that was RELEASED since (a fed police respawn) has key 0; step 4 calls
 * pair(0, argrec): 0x4f8a60 takes T[0] (the table's header word, 0x4f09) as a chain node -> c0000005 at 0x4f8a8e. The same key 0 into 0x5a4ad0 (loop 3)
 * would fault at 0x5a4b06. The game's own sibling 0x5edab0 skips id 0 before both calls (0x5edabf / 0x5edaf4); this one does not.
 *
 * THIS PORT: pair() and the 0x5a4ad0 calls do nothing for key 0 (the record is dead; the sibling does the same), onskip(site, idx, key) is told, and the
 * rest of the walk goes on: later records are processed exactly as the original does (no swallowed fault leaving a half-done list). argkey == 0 (the record
 * itself is dead; the original would fault at once in step 4 or 5): steps 2..6 are skipped, flag(rec) only (GUESS: a dead record has no list to update).
 * Everything else is instruction-for-instruction (same order of helper calls, same re-reads of this+0x38/0x3c/0x40 as the original). */
#ifndef KLLISTGUARD_PORT_H
#define KLLISTGUARD_PORT_H

#ifdef _MSC_VER
#define KLLG_FC __fastcall
#else
#define KLLG_FC __attribute__((fastcall))
#endif

#define KLLG_O_TABLE 0x20u
#define KLLG_O_A     0x38u
#define KLLG_O_B     0x3cu
#define KLLG_O_C     0x40u
#define KLLG_R_FLAGS 0x3cu
#define KLLG_R_KEY   0x54u
#define KLLG_FLAG    0x01000000u
#define KLLG_KEYMASK 0x00ffffffu

/* the exe's helpers (build 0490); thiscall(this, a, b, c) ret 0xc is called as __fastcall(this, dummy edx, a, b, c) */
typedef struct {
    void     (*sort)(unsigned *arr, unsigned lo, unsigned hi);                                              /* 0x4e2b90 cdecl */
    unsigned (KLLG_FC *range)(void *self, void *edx, unsigned *out, unsigned key);                          /* 0x8176f0 ret 8 */
    void     (*merge)(unsigned *dst, unsigned *a, unsigned na, unsigned *b, unsigned nb);                   /* 0x881ef0 cdecl */
    unsigned (KLLG_FC *add)(void *self, void *edx, unsigned key, unsigned *recs, unsigned count);           /* 0x5a4ad0 ret 0xc */
    unsigned (KLLG_FC *rem)(void *self, void *edx, unsigned key, void *rec, unsigned one);                  /* 0x4f8a60 ret 0xc */
    unsigned (KLLG_FC *rem2)(void *self, void *edx, unsigned key, void *rec, unsigned one);                 /* 0x6986b0 ret 0xc */
    void     (*onskip)(unsigned site, unsigned idx, unsigned key);                                          /* may be 0 */
} KLLG_HELPERS;

#define KLLG_SITE_LOOP1 1u   /* a C record with key 0 (the crash) */
#define KLLG_SITE_LOOP3 3u   /* a new record with key 0 (never listed by the caller) */
#define KLLG_SITE_SELF  9u   /* argrec itself has key 0 */

#define KLLG_W(p, off) (*(unsigned *)((unsigned char *)(p) + (off)))
#define KLLG_KEY(r) (KLLG_W((r), KLLG_R_KEY) & KLLG_KEYMASK)
#define KLLG_FLAGIT(r) (KLLG_W((r), KLLG_R_FLAGS) |= KLLG_FLAG)

static void kllg_pair(const KLLG_HELPERS *h, void *self, unsigned key, void *rec, unsigned site, unsigned idx)
{
    if (key == 0) { if (h->onskip) h->onskip(site, idx, key); return; }
    if (h->rem(self, 0, key, rec, 1) & 1) h->rem2(self, 0, key, rec, 1);
}

static void kllg_port(const KLLG_HELPERS *h, void *self, unsigned n, void *rec)
{
    unsigned argkey = KLLG_KEY(rec), rv, start, cnt, total, *ci, *cend, *ap, i, cnt2, r;
#define KA() (*(unsigned **)((unsigned char *)self + KLLG_O_A))
#define KB() (*(unsigned **)((unsigned char *)self + KLLG_O_B))
#define KC() (*(unsigned **)((unsigned char *)self + KLLG_O_C))
    if (n > 1) h->sort(KA(), 0, n - 1);
    if (argkey == 0) { if (h->onskip) h->onskip(KLLG_SITE_SELF, 0, 0); KLLG_FLAGIT(rec); return; }
    rv = h->range(self, 0, KB(), argkey);
    start = rv & 0xffffu; cnt = rv >> 16;
    if (cnt > 1) h->sort(KB(), start, start + cnt - 1);
    h->merge(KC(), KB(), start, KB() + start, cnt);
    total = start + cnt;
    /* loop 1 */
    ap = KA(); ci = KC(); cend = KC() + total;
    while (ci < cend) {
        unsigned c = *ci;
        void *cr = (void *)(size_t)c;
        KLLG_FLAGIT(cr);
        if (KA() + n != ap) {
            if (c > *ap) { ap++; cend = KC() + total; continue; }
            if (c == *ap) { *ap = 0; ci++; ap++; cend = KC() + total; continue; }
        }
        /* A exhausted, or c < *ap: c left the set */
        kllg_pair(h, self, KLLG_KEY(cr), rec, KLLG_SITE_LOOP1, (unsigned)(ci - KC()));
        kllg_pair(h, self, argkey, cr, KLLG_SITE_LOOP1, (unsigned)(ci - KC()));
        ci++; cend = KC() + total;
    }
    /* loop 2: compact A */
    cnt2 = 0;
    for (i = 0; i < n; i++) {
        unsigned *a = KA();
        if (a[i] != 0) { if (i != cnt2) a[cnt2] = a[i]; cnt2++; }
    }
    if (cnt2 > 0) {
        r = h->add(self, 0, argkey, KA(), cnt2);
        if (r < cnt2) {
            for (i = 0; i < r; i++) { void *ar = (void *)(size_t)KA()[i]; KLLG_FLAGIT(ar); kllg_pair(h, self, argkey, ar, KLLG_SITE_LOOP3, i); }
            cnt2 = 0;
        }
    }
    /* loop 3 */
    for (i = 0; i < cnt2; i++) {
        void *ar = (void *)(size_t)KA()[i]; unsigned k = KLLG_KEY(ar); unsigned tmp = (unsigned)(size_t)rec;
        if (k == 0) { if (h->onskip) h->onskip(KLLG_SITE_LOOP3, i, 0); KLLG_FLAGIT(ar); continue; }
        r = h->add(self, 0, k, &tmp, 1);
        KLLG_FLAGIT(ar);
        if (r != 1) { kllg_pair(h, self, k, rec, KLLG_SITE_LOOP3, i); kllg_pair(h, self, argkey, ar, KLLG_SITE_LOOP3, i); }
    }
    KLLG_FLAGIT(rec);
#undef KA
#undef KB
#undef KC
}
#endif
