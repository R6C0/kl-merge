/* klkillcash_test.c - OFF-GAME checks of klkillcash_logic.h ([HUD] KillCash). Exit 0 only when every check passes. */
#include "klkillcash_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static int fmt_is(const char *stock, long d, const char *want)
{
    char o[64]; klkc_format(stock, d, o, sizeof o);
    if (strcmp(o, want)) printf("  '%s' %ld -> '%s' (want '%s')\n", stock, d, o, want);
    return !strcmp(o, want);
}

int main(void)
{
    char b[16];
    CHECK(fmt_is("POLICE +$0", 0, "KILLED POLICE"));                 /* the owner's '$0': gone */
    CHECK(fmt_is("POLICE +$0", 1500, "KILLED POLICE  +$1,500"));     /* the money that really moved */
    CHECK(fmt_is("POLICE +$5000", 5000, "KILLED POLICE  +$5,000"));
    CHECK(fmt_is("JEAN -$20000", -20000, "KILLED JEAN  -$20,000"));
    CHECK(fmt_is("+$50000", 50000, "+$50,000"));                     /* a bonus: no name, no KILLED */
    CHECK(fmt_is("+$0", 0, ""));                                    /* nothing to say */
    CHECK(fmt_is("  SWAT  +$0", 0, "KILLED SWAT"));
    CHECK(fmt_is("POLICE", 250, "KILLED POLICE  +$250"));            /* no '$' at all */
    CHECK(fmt_is("POLICE +$0", 1234567, "KILLED POLICE  +$1,234,567"));
    klkc_num(999, b, sizeof b); CHECK(!strcmp(b, "999"));
    klkc_num(1000, b, sizeof b); CHECK(!strcmp(b, "1,000"));
    klkc_num(-1000, b, sizeof b); CHECK(!strcmp(b, "1,000"));
    { char t[8]; klkc_format("POLICE +$0", 123456, t, sizeof t); CHECK(strlen(t) == 7); }   /* truncates, never overruns */
    { char t[64];
      klkc_revive("Jean", 1, 3000, t, sizeof t); CHECK(!strcmp(t, "YOU GOT JEAN UP  +$3,000"));
      klkc_revive("Jean", 0, 3000, t, sizeof t); CHECK(!strcmp(t, "JEAN GOT YOU UP  -$3,000"));
      klkc_revive("your crewmate", 1, 0, t, sizeof t); CHECK(!strcmp(t, "YOU GOT YOUR CREWMATE UP"));
      klkc_revive("", 0, 12500, t, sizeof t); CHECK(!strcmp(t, "CREWMATE GOT YOU UP  -$12,500"));
      klkc_revive_tag(3000, t, sizeof t); CHECK(!strcmp(t, "REVIVE +$3,000"));
      klkc_revive_tag(-1250, t, sizeof t); CHECK(!strcmp(t, "REVIVE -$1,250"));
      klkc_revive_tag(0, t, sizeof t); CHECK(t[0] == 0); }
    { char t[10]; klkc_revive("Jean", 1, 3000, t, sizeof t); CHECK(strlen(t) == 9); }   /* truncates, never overruns */
    printf("klkillcash_test: %d checks, %d failed\n", checks, fails);
    return fails != 0;
}
