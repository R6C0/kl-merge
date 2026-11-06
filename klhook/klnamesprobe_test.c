/* klnamesprobe_test.c - off-game checks of klnamesprobe_logic.h. Build: cl /nologo /W3 klnamesprobe_test.c */
#include "klnamesprobe_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

static void put(struct klnp_e *e, int d, unsigned long m, const char *n) { e->digit = d; e->model = m; memset(e->name, 0, sizeof e->name); strcpy(e->name, n); }

int main(void)
{
    struct klnp_e a[4], b[4], c[4]; char t[160]; unsigned long ls = 0, la = 0; int first = 1;
    put(&a[0], 2, 0x10, "Kane"); put(&a[1], 5, 0x20, "Liam"); put(&a[2], 3, 0x30, ""); put(&a[3], 8, 0x40, "Pierre");
    put(&b[0], 8, 0x40, "Pierre"); put(&b[1], 3, 0x30, ""); put(&b[2], 5, 0x20, "Liam"); put(&b[3], 2, 0x10, "Kane");      /* same bots, another census order */
    CHECK(klnp_digest(a, 4) == klnp_digest(b, 4));
    CHECK(klnp_digest(a, 4) != 0 && klnp_digest(a, 0) == 0 && klnp_digest(0, 4) == 0 && klnp_digest(a, -1) == 0);
    memcpy(c, a, sizeof a); c[1].model = 0x21; CHECK(klnp_digest(c, 4) != klnp_digest(a, 4));      /* another model for digit 5 */
    memcpy(c, a, sizeof a); strcpy(c[0].name, "Kana"); CHECK(klnp_digest(c, 4) != klnp_digest(a, 4));
    memcpy(c, a, sizeof a); c[2].digit = 0; CHECK(klnp_digest(c, 4) != klnp_digest(a, 4));      /* unreadable group name is visible in the digest */
    memcpy(c, a, sizeof a); c[2].digit = 4; CHECK(klnp_digest(c, 4) != klnp_digest(a, 4));
    CHECK(klnp_digest(a, 3) != klnp_digest(a, 4));      /* a missing bot shows */
    put(&c[0], 2, 1, "ab"); put(&c[1], 3, 1, "c"); put(&c[2], 2, 1, "a"); put(&c[3], 3, 1, "bc");
    CHECK(klnp_digest(c, 2) != klnp_digest(c + 2, 2));      /* name terminator */
    /* list text */
    CHECK(klnp_list(t, sizeof t, a, 4) > 0); CHECK(!strcmp(t, "2=Kane 3=- 5=Liam 8=Pierre"));
    CHECK(klnp_list(t, sizeof t, b, 4) > 0); CHECK(!strcmp(t, "2=Kane 3=- 5=Liam 8=Pierre"));
    memcpy(c, a, sizeof a); c[0].digit = 0; klnp_list(t, sizeof t, c, 4); CHECK(!strcmp(t, "?=Kane 3=- 5=Liam 8=Pierre"));
    CHECK(klnp_list(t, sizeof t, a, 0) == 0 && t[0] == 0);
    CHECK(klnp_list(t, 0, a, 4) == 0);
    { char s[12]; int n = klnp_list(s, sizeof s, a, 4); CHECK(n == (int)strlen(s) && n <= 11); }      /* truncation is safe and terminated */
    { char s[1]; klnp_list(s, 1, a, 4); CHECK(s[0] == 0); }
    { struct klnp_e big[KLNP_MAXE + 4]; int i; for (i = 0; i < KLNP_MAXE + 4; i++) put(&big[i], 2 + i % 7, (unsigned long)i, "X"); CHECK(klnp_digest(big, KLNP_MAXE + 4) == klnp_digest(big, KLNP_MAXE)); klnp_list(t, sizeof t, big, KLNP_MAXE + 4); CHECK(strlen(t) < sizeof t); }
    /* due: first line; a change inside minms waits; heartbeat; wrapping clock */
    CHECK(klnp_due(1000, 7, &ls, &la, &first, 2000, 10000) == 1 && !first && ls == 7 && la == 1000);
    CHECK(klnp_due(1500, 7, &ls, &la, &first, 2000, 10000) == 0);      /* same digest, early */
    CHECK(klnp_due(1600, 8, &ls, &la, &first, 2000, 10000) == 0 && ls == 7 && la == 1000);      /* changed but inside minms: deferred, state kept */
    CHECK(klnp_due(3100, 8, &ls, &la, &first, 2000, 10000) == 1 && ls == 8 && la == 3100);      /* now it fires */
    CHECK(klnp_due(12000, 8, &ls, &la, &first, 2000, 10000) == 0);
    CHECK(klnp_due(13100, 8, &ls, &la, &first, 2000, 10000) == 1);      /* heartbeat */
    ls = 1; la = 0xfffffff0ul; first = 0; CHECK(klnp_due(0x10, 1, &ls, &la, &first, 2000, 10000) == 0 && klnp_due(0x10 + 2500, 2, &ls, &la, &first, 2000, 10000) == 1);      /* 32-bit wrap */
    CHECK(klnp_due(1, 1, 0, &la, &first, 1, 1) == 0 && klnp_due(1, 1, &ls, 0, &first, 1, 1) == 0 && klnp_due(1, 1, &ls, &la, 0, 1, 1) == 0);
    printf("klnamesprobe_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
