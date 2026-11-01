/* klassoft_logic.h - the PURE part of [KLHook] AssertSoft (klhook.c veh()): parse the list and test an address. No windows.h.
 * AssertSoft=0x6567e8,0x845a8b,...  = kl2.exe OFFSETS, exactly as the log prints them ("ASSERT at kl2.exe+6567e8 (00a567e8)": the
 * number after the +). Hex only; "0x" optional; separators , ; space; a token that is not hex or is over 0x2000000 is skipped and
 * counted in *bad. Checked off-game by klassoft_test.c. */
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
        if (ok && digits && v <= 0x2000000ul && n < max) { int dup = 0, i; for (i = 0; i < n; i++) if (out[i] == v) dup = 1; if (!dup) out[n++] = v; }
        else if (bad) (*bad)++;
    }
    return n;
}
/* -> index of off in the list or -1 */
static int kas_find(const unsigned long *l, int n, unsigned long off)
{
    int i; for (i = 0; i < n; i++) if (l[i] == off) return i;
    return -1;
}
#endif
