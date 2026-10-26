/* kldown_mirror_test.c - off-game checks of kldown_mirror_logic.h. Build: cl /nologo /W3 kldown_mirror_test.c  (or tools/run_harness_linux.sh kldown_mirror_test) */
#include "kldown_mirror_logic.h"

static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    char b[128]; struct kdm_fl f; struct kdm_sy y; int i, j;
    /* announce round trip + strictness */
    CHECK(kdm_fmt_fl(b, sizeof b, 3, 41, 7, 2, 0x1ff) > 0); CHECK(!strcmp(b, "1;3;41;7;2;1ff"));
    CHECK(kdm_parse_fl(b, &f) && f.mode == 3 && f.sheet == 41 && f.n == 7 && f.group == 2 && f.mask == 0x1ff);
    CHECK(kdm_parse_fl("1;1;0;3;0;0", &f) && f.mode == 1);
    CHECK(kdm_parse_fl("1;0;0;3;0;0", &f) && f.mode == 0);
    CHECK(!kdm_parse_fl("1;3;0;3;0;0", &f));                 /* mode 3 needs a sheet */
    CHECK(!kdm_parse_fl("1;2;41;3;0;0", &f));                /* mode 2 does not exist */
    CHECK(!kdm_parse_fl("2;3;41;3;0;0", &f));                /* version */
    CHECK(!kdm_parse_fl("1;3;41;3;0", &f));                  /* short */
    CHECK(!kdm_parse_fl("1;3;41;3;0;0;9", &f));              /* long */
    CHECK(!kdm_parse_fl("1;3;41;99999;0;0", &f));            /* n out of range */
    CHECK(!kdm_parse_fl("1;3;41;3;0;fff", &f));              /* mask beyond 9 bits */
    CHECK(!kdm_parse_fl("1;3;41;3;0;0 junk", &f)); CHECK(!kdm_parse_fl("", &f)); CHECK(!kdm_parse_fl(0, &f));
    /* sync round trip */
    CHECK(kdm_fmt_sy(b, sizeof b, 4, 37.46f, 2.5f, 120) > 0); CHECK(!strcmp(b, "1;4;375;250;120"));
    CHECK(kdm_parse_sy(b, &y) && y.n == 4 && y.frame > 37.4f && y.frame < 37.6f && y.rate > 2.49f && y.rate < 2.51f && y.to == 120);
    CHECK(!kdm_parse_sy("1;4;375;0;120", &y));               /* rate 0 */
    CHECK(!kdm_parse_sy("1;4;-5;100;120", &y)); CHECK(!kdm_parse_sy("1;4;5;100;1", &y)); CHECK(!kdm_parse_sy("1;4;5;100", &y));
    /* hash: deterministic, spreads */
    CHECK(kdm_hash(3, 5, KDM_SALT) == kdm_hash(3, 5, KDM_SALT));
    CHECK(kdm_hash(3, 5, KDM_SALT) != kdm_hash(3, 6, KDM_SALT)); CHECK(kdm_hash(3, 5, KDM_SALT) != kdm_hash(4, 5, KDM_SALT));
    {   /* the draw is spread: 9 entries (kld_md weights 2 0 0 2 0 1 1 1 1, groups 1 1 1 2 2 3 4 5 6), 3000 falls of 6 bodies, nobody starves */
        float w[9] = { 2, 0, 0, 2, 0, 1, 1, 1, 1 }; int g[9] = { 1, 1, 1, 2, 2, 3, 4, 5, 6 }; int cnt[9] = { 0 }, last[6] = { 0 }, back = 0;
        for (j = 0; j < 6; j++) for (i = 1; i <= 500; i++) {
            int p = kdm_det_pick(w, g, 9, last[j], kdm_hash(j, i, KDM_SALT));
            CHECK(p >= 0 && w[p] > 0); cnt[p]++;
            if (last[j] && g[p] == last[j]) back++;
            last[j] = g[p];
        }
        CHECK(back == 0);                                    /* never the group played last, other groups exist */
        CHECK(cnt[1] == 0 && cnt[2] == 0 && cnt[4] == 0);    /* weight 0 is never drawn */
        for (i = 0; i < 9; i++) if (w[i] > 0) CHECK(cnt[i] > 150);
    }
    /* the same r gives the same entry as kld_mix_next's walk (re-implemented here the long way) */
    {   float w[3] = { 1, 2, 1 }; int g[3] = { 1, 2, 3 };
        CHECK(kdm_pick_r(w, g, 3, 0, 0.5f, 0) == 0); CHECK(kdm_pick_r(w, g, 3, 0, 1.5f, 0) == 1); CHECK(kdm_pick_r(w, g, 3, 0, 3.5f, 0) == 2);
        CHECK(kdm_pick_r(w, g, 3, 2, 0.5f, 0) == 0); CHECK(kdm_pick_r(w, g, 3, 2, 1.5f, 0) == 2);   /* group 2 is skipped: 1 then 1 */
        CHECK(kdm_pick_r(w, g, 3, 9, 99.0f, 0) == 2);                                                /* r past the end: the last entry */
        { int g1[2] = { 1, 1 }; float w1[2] = { 1, 1 }; CHECK(kdm_pick_r(w1, g1, 2, 1, 0.1f, 0) == 0); }   /* only one group: it may repeat */
        CHECK(kdm_pick_r(w, g, 0, 0, 0, 0) == -1);
    }
    /* follow speed: on target = the master's pace; behind = faster; ahead = slower; clamped */
    CHECK(kdm_fps(2.0f, 10, 10, 2.0f) == 50.0f);
    CHECK(kdm_fps(2.0f, 10, 15, 2.0f) > 50.0f); CHECK(kdm_fps(2.0f, 15, 10, 2.0f) < 50.0f);
    CHECK(kdm_fps(2.0f, 0, 1000, 2.0f) == 100.0f); CHECK(kdm_fps(2.0f, 1000, 0, 2.0f) == 25.0f);
    CHECK(kdm_fps(0.02f, 0, 0, 2.0f) == 0.5f); CHECK(kdm_fps(20.0f, 0, 1000, 2.0f) == 250.0f);
    /* pool sharing */
    {   unsigned p[4] = { 0x1000, 0x2000, 0x1000, 0x3000 };
        CHECK(kdm_pool_users(p, 4, 0) == 1);                 /* shares with body 2 */
        CHECK(kdm_pool_users(p, 4, 1) == 0); CHECK(kdm_pool_users(p, 4, 3) == 0);
        CHECK(kdm_pool_users(p, 4, 4) == -1); p[1] = 0; CHECK(kdm_pool_users(p, 4, 1) == -1);
    }
    printf("kldown_mirror_test: %d checks, %d failed\n", checks, fails);
    return fails ? 1 : 0;
}
