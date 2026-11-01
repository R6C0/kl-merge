/* klassoft_logic.h - the PURE part of [KLHook] AssertSoft (klhook.c veh()): parse the list and test an address. No windows.h.
 * AssertSoft=0x6567e8,0x845a8b,...  = kl2.exe ADDRESSES (VAs, base 0x400000, no ASLR): the number in brackets of an ASSERT line
 * ("ASSERT at kl2.exe+2567e8 (006567e8)" -> 0x6567e8), as every note writes them. AS1 (11-01): the first cut took OFFSETS while the ini
 * held VAs, so nothing matched (42 asserts, soft 0); an offset and a VA cannot be told apart (offsets reach 0x134e000), so VAs only.
 * Hex only; "0x" optional; separators , ; space; a token that is not hex or is outside 0x400000..0x2000000 (an offset, say) is skipped
 * and counted in *bad. Checked off-game by klassoft_test.c. */
#ifndef KLASSOFT_LOGIC_H
#define KLASSOFT_LOGIC_H
#include <string.h>
#define KAS_MAX 32
static int kas_parse(const char *s, unsigned long *out, int max, int *bad)
{
    int n = 0; if (bad) *bad = 0;
    while (s && *s) {
        unsigned long v = 0; int digits = 0, ok = 1;
        while (*s == ',' || *s == ';' || *s == ' ' || *s == '\t') s++;
        if (!*s) break;
        if (s[0] == '0' && (s[1] == 'x' || s[1] == 'X')) s += 2;
        for (; *s && *s != ',' && *s != ';' && *s != ' ' && *s != '\t'; s++) {
            int d = *s >= '0' && *s <= '9' ? *s - '0' : *s >= 'a' && *s <= 'f' ? *s - 'a' + 10 : *s >= 'A' && *s <= 'F' ? *s - 'A' + 10 : -1;
            if (d < 0 || digits >= 8) { ok = 0; continue; }
            v = v * 16 + (unsigned long)d; digits++;
        }
        if (ok && digits && v >= 0x400000ul && v <= 0x2000000ul && n < max) { int dup = 0, i; for (i = 0; i < n; i++) if (out[i] == v) dup = 1; if (!dup) out[n++] = v; }
        else if (bad) (*bad)++;
    }
    return n;
}
/* -> index of the address va in the list or -1 */
static int kas_find(const unsigned long *l, int n, unsigned long va)
{
    int i; for (i = 0; i < n; i++) if (l[i] == va) return i;
    return -1;
}

/* ---- AssertSoftGuard (11-01, re/assertsoft_safety_1101.md): per-site table + the pure pool test ----
 * All five sites read the cover point's flags at [rec+0x68] (rec = [L+0x44] + idx*0x7c, L = [[0xdd265c]+0x15a0], idx < 0x1788 = the game's own
 * bound at 0x656776) and, when neither bit 2 nor 0x200 is set, hit an int3 whose fall-through is the SAME code the "bit 2 set" case runs (kind 0,
 * read-only on rec). So stepping over never writes out of bounds; the only hazard is a rec that is NOT inside the pool (an index without a bound:
 * 0x845a8b with state 0, and the 0x491eb0 helper behind 0x51d049 / 0x555900 never check the upper bound). With AssertSoftGuard=1 veh() steps over
 * a listed site only when the record is provably inside the pool; otherwise the hit takes the ordinary visible assert path (log + one dump).
 * Where the record sits at the int3: KAS_REC_EDI / KAS_REC_ESI = a register holds rec; KAS_IDX_ESI4 = rec is not kept, but [esi+4] is the index. */
#define KAS_POOL_CAP 0x1788ul
#define KAS_REC_SIZE 0x7cul
enum { KAS_REC_NONE = 0, KAS_REC_EDI = 1, KAS_REC_ESI = 2, KAS_IDX_ESI4 = 3 };
typedef struct { unsigned long va; int where; const char *name; } kas_site;
static const kas_site kas_sites[] = {
    { 0x6567e8, KAS_REC_EDI,  "0x656740 set-state, rec in edi (idx range-checked at 0x656776)" },
    { 0x845a8b, KAS_REC_ESI,  "0x845980 set-state(ebx), rec in esi (upper bound checked only when ebx != 0)" },
    { 0x51d049, KAS_IDX_ESI4, "0x51d020 kind query, rec via 0x491eb0 (no bound), idx = [esi+4]" },
    { 0x555900, KAS_REC_EDI,  "0x5558d0 cover-point fire/aim, rec = 0x491eb0 result in edi (no bound)" },
    { 0x4ede1b, KAS_REC_ESI,  "0x4ede00 kind test, this = rec in esi (called from 0x845b53 with an unchecked idx)" },
};
#define KAS_NSITES ((int)(sizeof kas_sites / sizeof kas_sites[0]))
static int kas_site_where(unsigned long va)
{
    int i; for (i = 0; i < KAS_NSITES; i++) if (kas_sites[i].va == va) return kas_sites[i].where;
    return KAS_REC_NONE;                 /* not in the table: the guard cannot judge it, so it passes (the list alone decides) */
}
/* 1 = step over is safe. pool = [L+0x44] (0 if unreadable), reg = the register named by 'where' (edi / esi), idx = [esi+4] for KAS_IDX_ESI4 (ignored else) */
static int kas_guard_ok(int where, unsigned long pool, unsigned long reg, unsigned long idx)
{
    if (where == KAS_REC_NONE) return 1;
    if (!pool) return 0;
    if (where == KAS_IDX_ESI4) return idx < KAS_POOL_CAP;
    if (reg < pool || reg >= pool + KAS_POOL_CAP * KAS_REC_SIZE) return 0;
    return (reg - pool) % KAS_REC_SIZE == 0;
}
#endif
