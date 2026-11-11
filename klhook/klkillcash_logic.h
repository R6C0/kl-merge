/* klkillcash_logic.h - [HUD] KillCash (owner 2026-11-11: 'when you kill someone it doesnt accurately tell you how much money they give you ... it just
 * says $0 - remove that and on the right say who you killed and give the accurate amount of cash you earned'). Pure text logic, no Windows.
 * The stock points pop-up line ('POLICE +$0', '+$50000', klhud_kill.c) keeps only its name part; the amount is what the local player's money
 * really moved since the line came in (klhud.c: REWARDS delta, else TOTAL delta). 0 -> no amount at all (never '$0').
 * GUESS: the text before the first '$' (and its '+' / '-') is the victim's name ('POLICE', a heister); a line with no name is a bonus. */
#ifndef KLKILLCASH_LOGIC_H
#define KLKILLCASH_LOGIC_H
#include <stdio.h>
#include <string.h>

/* the name part of a stock line: the text before the '$' with a trailing '+' / '-' / spaces cut; "" when none */
static void klkc_name(const char *stock, char *out, size_t n)
{
    const char *d = strchr(stock, '$'); size_t k = d ? (size_t)(d - stock) : strlen(stock);
    while (k && (stock[k - 1] == '+' || stock[k - 1] == '-' || stock[k - 1] == ' ')) k--;
    while (k && *stock == ' ') { stock++; k--; }
    if (k >= n) k = n - 1;
    memcpy(out, stock, k); out[k] = 0;
}

/* thousands with commas, sign kept: 12500 -> "12,500" */
static void klkc_num(long v, char *out, size_t n)
{
    char t[24]; int i, l, o = 0; unsigned long u = v < 0 ? 0UL - (unsigned long)v : (unsigned long)v;
    l = snprintf(t, sizeof t, "%lu", u);
    if (n < 2) { if (n) out[0] = 0; return; }
    for (i = 0; i < l && o < (int)n - 1; i++) {
        if (i && (l - i) % 3 == 0 && o < (int)n - 2) out[o++] = ',';
        out[o++] = t[i];
    }
    out[o] = 0;
}

/* the line to draw: 'KILLED POLICE  +$1,500', 'KILLED POLICE' (no money moved), '+$50,000' (no name), '' (no name, no money: draw nothing) */
static void klkc_format(const char *stock, long delta, char *out, size_t n)
{
    char nm[48], num[24]; int o = 0;
    klkc_name(stock, nm, sizeof nm);
    klkc_num(delta, num, sizeof num);
    if (!n) return;
    out[0] = 0;
    if (nm[0]) o = snprintf(out, n, "KILLED %s", nm);
    if (o < 0 || (size_t)o >= n) return;
    if (delta) snprintf(out + o, n - (size_t)o, "%s%s$%s", nm[0] ? "  " : "", delta < 0 ? "-" : "+", num);
}

#endif
