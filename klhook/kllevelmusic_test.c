/* kllevelmusic_test.c - off-game checks of kllevelmusic_logic.h. Build: cl /nologo /W3 kllevelmusic_test.c */
#include <stdio.h>
#include "kllevelmusic_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
int main(void)
{
    struct kllm_st s = { 0, 0, 0, 0, 0 }; unsigned t;
    CHECK(!kllm_step(&s, 0, 5, 1000, 2000));                       /* no round */
    for (t = 1000; t < 90000; t += 250) CHECK(!kllm_step(&s, 1, 5, t, 2000));   /* round 1 never fires */
    CHECK(!kllm_step(&s, 0, 5, 90000, 2000));                      /* intermission */
    CHECK(!kllm_step(&s, 1, 6, 100000, 2000));                     /* round 2 begins: wait */
    CHECK(!kllm_step(&s, 1, 6, 101750, 2000));
    CHECK(kllm_step(&s, 1, 6, 102000, 2000));                      /* fires once after the delay */
    CHECK(!kllm_step(&s, 1, 6, 102250, 2000)); CHECK(!kllm_step(&s, 1, 6, 150000, 2000));
    CHECK(kllm_step(&s, 1, 7, 200000, 0));                         /* round 3, delay 0: at once */
    CHECK(!kllm_step(&s, 1, 7, 200250, 0));
    { struct kllm_st m = { 0, 0, 0, 0, 0 };                        /* leaving the round before the delay cancels it */
      kllm_step(&m, 1, 1, 0, 2000); kllm_step(&m, 1, 2, 10000, 2000);
      CHECK(!kllm_step(&m, 0, 2, 10500, 2000)); CHECK(!kllm_step(&m, 0, 2, 13000, 2000)); }
    printf("kllevelmusic_test: %d checks, %d fail\n", checks, fails); return fails != 0;
}
