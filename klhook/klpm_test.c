/* klpm_test.c - OFF-GAME check of klpm.c's pure core (tally, playlist cursor, maps.ini, option names). Nothing about the game.
 *   cl /nologo /W4 /D_CRT_SECURE_NO_WARNINGS klpm_test.c     (run from the klhook folder; any x86/x64 vcvars) */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
static int klh_rd(DWORD_PTR p, void *out, SIZE_T n) { if (p < 0x10000) return 0; memcpy(out, (void *)p, n); return 1; }
static int klh_rdstr(DWORD_PTR p, char *out, int cap) { out[0] = 0; if (!p) return 0; strncpy(out, (const char *)p, (size_t)cap - 1); out[cap - 1] = 0; return (int)strlen(out); }
static char klh_ini[MAX_PATH] = "klpm_test.ini";
static void klog(const char *fmt, ...) { va_list a; va_start(a, fmt); vprintf(fmt, a); printf("\n"); va_end(a); }
#include "klpm.c"

int main(void)
{
    int v1[] = { 2, 2, 1, 0 }, v0[] = { 0, 0, 0 }, vbad[] = { 9, -1 }, list[5] = { 0, 1, 2, 3, 4 }, seen[5], i, lap, d;
    FILE *f;
    /* tally */
    CHECK(kpm_tally(v1, 4, 3, 7) == 1);                       /* two votes for map 2 */
    CHECK(kpm_tally(v1, 4, 3, 99) == 1);                      /* the seed is irrelevant without a tie */
    CHECK(kpm_tally(v0, 3, 3, 5) == kpm_tally(v0, 3, 3, 5));  /* deterministic */
    CHECK(kpm_tally(v0, 3, 4, 5) >= 0 && kpm_tally(v0, 3, 4, 5) < 4);
    CHECK(kpm_tally(vbad, 2, 3, 1) >= 0 && kpm_tally(vbad, 2, 3, 1) < 3);
    CHECK(kpm_tally(v1, 0, 0, 1) == -1);
    { int t[] = { 1, 3 }, k, hit[3] = { 0, 0, 0 };            /* a tie 1 vs 3 is drawn among those two only, both reachable */
      for (k = 0; k < 64; k++) { int w = kpm_tally(t, 2, 3, (unsigned)k); CHECK(w == 0 || w == 2); hit[w]++; }
      CHECK(hit[0] > 0 && hit[2] > 0 && hit[1] == 0); }
    /* playlist */
    for (i = 0; i < 12; i++) CHECK(kpm_next(1, list, 5, i, 3) == i % 5);
    CHECK(kpm_next(0, list, 5, 0, 3) == -1 && kpm_next(2, list, 0, 0, 3) == -1 && kpm_next(1, list, 5, -1, 3) == -1);
    for (lap = 0; lap < 20; lap++) {                          /* random: every lap is a permutation, and no map twice in a row across a lap */
        memset(seen, 0, sizeof seen);
        for (i = 0; i < 5; i++) { int m = kpm_next(2, list, 5, lap * 5 + i, 11); CHECK(m >= 0 && m < 5); seen[m]++; }
        for (i = 0; i < 5; i++) CHECK(seen[i] == 1);
        if (lap > 0) CHECK(kpm_next(2, list, 5, lap * 5, 11) != kpm_next(2, list, 5, lap * 5 - 1, 11));
    }
    CHECK(kpm_next(2, list, 5, 7, 11) == kpm_next(2, list, 5, 7, 11));
    d = 0; for (i = 0; i < 5; i++) if (kpm_next(2, list, 5, i, 1) != kpm_next(2, list, 5, i, 2)) d = 1;
    CHECK(d);                                                 /* another seed, another order (for these two seeds) */
    CHECK(kpm_next(2, list, 1, 4, 1) == 0);                   /* one map: fine, repeats are unavoidable */
    /* maps.ini */
    f = fopen("klpm_test_maps.ini", "w");
    fputs("[Maps]\nCount=3\n[Map.1]\nId=DM01\nName=Subway\nSlot=F01\n[Map.2]\nId=DM03A\nName=Bank\nSlot=F03\n[Map.3]\nId=DM05A\nName=Last Call\nSlot=F01\n", f); fclose(f);
    { char full[MAX_PATH]; int l[8], n; GetFullPathNameA("klpm_test_maps.ini", MAX_PATH, full, 0);
      kpm_maps_load(full);
      CHECK(kpm_nmap == 3 && !strcmp(kpm_map[1].id, "DM03A") && !strcmp(kpm_map[2].slot, "F01") && !strcmp(kpm_map[2].name, "Last Call"));
      n = kpm_parse_list("dm05a, DM01 ,nope,DM03A", l, 8);
      CHECK(n == 3 && l[0] == 2 && l[1] == 0 && l[2] == 1); }
    /* option names: off -> nothing; on -> ours only; KLMask and the others stay out */
    kpm_on = 0; CHECK(kpm_which("KLMGun") == -1);
    kpm_on = 1; CHECK(kpm_which("KLMGun") == 0 && kpm_which("KLMVote") == 1 && kpm_which("KLMPlay") == 2);
    CHECK(kpm_which("KLMask") == -1 && kpm_which("KLGunStart") == -1 && kpm_which("KLChar") == -1 && kpm_which("Difficulty") == -1 && kpm_which(0) == -1);
    kpm_put(1, 99); CHECK(kpm_get(1) == 3);                   /* clamped to the maps.ini count */
    kpm_put(2, -4); CHECK(kpm_get(2) == 0);
    kpm_put(0, 40); CHECK(kpm_get(0) == KPM_GUNS);
    /* B2: Arcade playlist, pure parts */
    CHECK(kpm_slot_idx("F01") == 0 && kpm_slot_idx("f09") == 8 && kpm_slot_idx("F10") == -1 && kpm_slot_idx("F00") == -1 && kpm_slot_idx("X01") == -1 && kpm_slot_idx(0) == -1);
    { int sl, pos, inv[9]; for (sl = 0; sl < 9; sl++) { pos = kpm_slot_pos(sl); CHECK(pos >= 0 && pos < 9); inv[pos] = sl; }
      /* the inverse must be kl2 0x746570's position -> slot table 0,1,2,3,5,6,4,7,8 */
      { static const int t[9] = { 0, 1, 2, 3, 5, 6, 4, 7, 8 }; for (pos = 0; pos < 9; pos++) CHECK(inv[pos] == t[pos]); }
      CHECK(kpm_slot_pos(-1) == -1 && kpm_slot_pos(9) == -1); }
    { int cur = 0, l3[3] = { 4, 2, 7 };
      CHECK(kpm_advance(1, l3, 3, &cur, 1, 2) == 7 && cur == 2);          /* played map 2 is list[1]: next is list[2] */
      CHECK(kpm_advance(1, l3, 3, &cur, 1, 7) == 4 && cur == 3);          /* wraps (cursor 3 -> position 0) */
      cur = 5; CHECK(kpm_advance(1, l3, 3, &cur, 1, 99) == l3[6 % 3] && cur == 6);   /* played map not on the list: the cursor moves on */
      cur = 0; CHECK(kpm_advance(1, l3, 3, &cur, 1, -1) == 2 && cur == 1);
      cur = 0; CHECK(kpm_advance(2, l3, 3, &cur, 5, 4) == kpm_next(2, l3, 3, 1, 5) && cur == 1);
      cur = 0; CHECK(kpm_advance(0, l3, 3, &cur, 1, 4) == -1 && kpm_advance(1, l3, 0, &cur, 1, 4) == -1 && kpm_advance(1, l3, 3, 0, 1, 4) == -1);
      cur = 100000; kpm_advance(2, l3, 3, &cur, 1, -1); CHECK(cur == 0); }   /* bounded: kpm_next replays every lap */
    CHECK(kpm_override("F07") == -1);                                   /* nothing set */
    kpm_ovr_set("F07", 2); CHECK(kpm_override("F07") == 2 && kpm_override("f07") == 2 && kpm_override("F01") == -1 && kpm_override(0) == -1);
    kpm_ovr_set(0, -1); CHECK(kpm_override("F07") == -1);
    CHECK(kpm_mode_text("order") == 1 && kpm_mode_text("RANDOM") == 2 && kpm_mode_text("2") == 2 && kpm_mode_text("") == 0 && kpm_mode_text("x") == 0 && kpm_mode_text(0) == 0);
    f = fopen("klpm_test_maps.ini", "w");
    fputs("[Bundle.1]\nName=Classics\nMaps=DM01,DM03A\n[Bundle.2]\nName=Other\nMaps=DM05A\n", f); fclose(f);
    { char full[MAX_PATH], m[64]; GetFullPathNameA("klpm_test_maps.ini", MAX_PATH, full, 0);
      CHECK(kpm_bundle_maps(full, "other", m, sizeof m) && !strcmp(m, "DM05A"));
      CHECK(kpm_bundle_maps(full, "Classics", m, sizeof m) && !strcmp(m, "DM01,DM03A"));
      CHECK(!kpm_bundle_maps(full, "none", m, sizeof m)); }
    DeleteFileA("klpm_test_maps.ini"); DeleteFileA("klpm_test.ini");
    printf("%d checks, %d failed\n", checks, fails);
    return fails != 0;
}
