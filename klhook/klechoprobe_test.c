/* klechoprobe_test.c - off-game checks of klechoprobe_logic.h. Build: cl /nologo /W3 klechoprobe_test.c */
#include <stdio.h>
#include <string.h>
#include "klechoprobe_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    struct kpr_stats s; struct kpr_log lg; char out[600], nm[64]; unsigned char buf[64]; int i, n;

    /* prediction: 3D voice sends unless flag bit 5; 2D / relative only with bit 6; no EFX listener = never */
    CHECK(kpr_predict(0, 1, 0, 1) == 1); CHECK(kpr_predict(0, 0, 1, 1) == 0);
    CHECK(kpr_predict(1, 1, 1, 1) == 2); CHECK(kpr_predict(1, 1, 0, 1) == 0);
    CHECK(kpr_predict(0, 1, 1, 0) == 0); CHECK(kpr_predict(1, 1, 1, 0) == 0);

    /* gun-like guess */
    CHECK(kpr_gunish("Weapons/AK47/AK47_Shot_01.wav")); CHECK(kpr_gunish("audio:weapons/ak47_shot_player#set")); CHECK(kpr_gunish("Distant_Shot_Rifle"));
    CHECK(!kpr_gunish("Dialog/Multiplayer/You_Esc/YouEsc_04_R_C8.wav")); CHECK(!kpr_gunish("Footsteps/concrete_01.wav"));
    CHECK(!kpr_gunish("weapons/ak47_reload.wav")); CHECK(!kpr_gunish("")); CHECK(!kpr_gunish(0)); CHECK(!kpr_gunish("Ambience/wind"));

    /* name from bytes */
    memset(buf, 0, sizeof buf); memcpy(buf, "Weapons/x_shot.wav", 18);
    CHECK(kpr_name_from(buf, 64, nm, sizeof nm) == 18 && !strcmp(nm, "Weapons/x_shot.wav"));
    memcpy(buf, "ab", 3); CHECK(kpr_name_from(buf, 64, nm, sizeof nm) == 0);                 /* too short */
    memcpy(buf, "1234567", 8); CHECK(kpr_name_from(buf, 64, nm, sizeof nm) == 0);           /* no letter */
    buf[0] = 'a'; buf[1] = 'b'; buf[2] = 0x01; buf[3] = 'c'; buf[4] = 'd'; buf[5] = 0; CHECK(kpr_name_from(buf, 64, nm, sizeof nm) == 0);   /* control char */
    memset(buf, 'a', 64); CHECK(kpr_name_from(buf, 64, nm, sizeof nm) == 0);                /* no NUL in the window */
    memset(buf, 0, sizeof buf); memcpy(buf, "abcdefghijklmnop", 16); CHECK(kpr_name_from(buf, 64, nm, 10) == 9 && strlen(nm) == 9);   /* cap truncates */
    CHECK(kpr_name_score("a/b.wav") > kpr_name_score("abcd"));

    /* stats and summary */
    kpr_init(&s);
    for (i = 0; i < 5; i++) kpr_add(&s, "Weapons/ak_shot.wav", 1, 0, 0);
    for (i = 0; i < 3; i++) kpr_add(&s, "Weapons/smg_shot.wav", 0, 0, 0);
    kpr_add(&s, "Dialog/x.wav", 0, 0, 0); kpr_add(&s, "Dialog/x.wav", 0, 0, 0);
    kpr_add(&s, "UI/click.wav", 1, 1, 0); kpr_add(&s, 0, 0, 0, 1);
    CHECK(s.played == 12 && s.with_send == 6 && s.late_send == 1 && s.without_send == 6 && s.unknown == 1);
    CHECK(s.gun_with == 5 && s.gun_without == 3);
    CHECK(s.nent == 5); CHECK(s.ent[0].with_send == 5 && s.ent[1].without_send == 3);
    CHECK(kpr_top_without(&s, 0) == 1);                         /* smg 3 > dialog 2 */
    CHECK(kpr_top_without(&s, 1u << 1) == 2);
    n = kpr_summary(&s, "10s", out, sizeof out, 3);
    CHECK(n == (int)strlen(out)); CHECK(strstr(out, "played 12, send 6 (late 1), no send 6, unknown 1") != 0);
    CHECK(strstr(out, "gun-like: send 5, no send 3") != 0);
    CHECK(strstr(out, "Weapons/smg_shot.wav x3 [gun-like]") != 0 && strstr(out, "Dialog/x.wav x2") != 0);
    CHECK(strstr(out, "Dialog/x.wav x2 [gun") == 0);
    /* nothing without a send */
    /* wave name before a .WHD record (descriptor d = record - 4): real layout from kaneandlynch.WHD, name 0x64d0 "SFX/OSD/Up_Down.wav" (19 chars -> 32 bytes) */
    { unsigned char w[0x100]; const char *nmA = "SFX/OSD/Up_Down.wav", *nmB = "Weapons/AK47/AK47_Shot_Player_Loud_01.wav", *nmC = "SFX/Weapons/Pistol/Pistol_Shot_Distant_A.wav";
      memset(w, 0, sizeof w); memset(w, 0xaa, 0x60);                       /* previous record body: binary */
      memcpy(w + 0xe0, nmA, strlen(nmA));                                   /* name at d-0x20 (d = w + 0x100) */
      CHECK(kpr_name_before(w, 0x100, nm, sizeof nm) == 19 && !strcmp(nm, nmA));
      memset(w, 0, sizeof w); memset(w, 0x11, 0x40); memcpy(w + 0xd0, nmB, strlen(nmB));   /* 41 chars -> 48 bytes: name at d-0x30; the tail block is printable */
      CHECK(kpr_name_before(w, 0x100, nm, sizeof nm) == (int)strlen(nmB) && !strcmp(nm, nmB));
      memset(w, 0, sizeof w); memset(w, 0x7f, 0x40); memcpy(w + 0xd0, nmC, strlen(nmC));   /* 44 chars -> 48 bytes */
      CHECK(kpr_name_before(w, 0x100, nm, sizeof nm) == (int)strlen(nmC) && !strcmp(nm, nmC));
      CHECK(kpr_gunish(nm));
      memset(w, 0, sizeof w); CHECK(kpr_name_before(w, 0x100, nm, sizeof nm) == 0);                  /* nothing but zeros */
      memset(w, 0xaa, sizeof w); CHECK(kpr_name_before(w, 0x100, nm, sizeof nm) == 0);               /* binary only */
      memset(w, 0, sizeof w); memcpy(w + 0xf0, "abcd", 4); CHECK(kpr_name_before(w, 0x100, nm, sizeof nm) == 0);   /* no extension / path: not a wave name */
      memset(w, 0, sizeof w); memcpy(w + 0xe0, nmA, strlen(nmA)); CHECK(kpr_name_before(w, 0x100, nm, 10) == 9 && strlen(nm) == 9);   /* cap truncates */
      memset(w, 0, sizeof w); memcpy(w + 0xe0, nmA, strlen(nmA)); CHECK(kpr_name_before(w + 0xc0, 0x40, nm, sizeof nm) == 19);   /* a short window still works */
    }
    kpr_init(&s); kpr_add(&s, "a_shot", 1, 0, 0); kpr_summary(&s, "all", out, sizeof out, 3); CHECK(strstr(out, "(none)") != 0);
    /* a tiny buffer never overruns and is terminated */
    kpr_summary(&s, "all", out, 20, 3); CHECK(strlen(out) < 20);
    /* a full name table still counts totals */
    kpr_init(&s);
    for (i = 0; i < KPR_NAMES + 10; i++) { char t[32]; sprintf(t, "name_%d", i); kpr_add(&s, t, i & 1, 0, 0); }
    CHECK(s.nent == KPR_NAMES && s.played == (unsigned)(KPR_NAMES + 10));
    /* long names are cut, not overrun, and still match themselves */
    { char big[200]; memset(big, 'x', 199); big[199] = 0; kpr_init(&s); kpr_add(&s, big, 0, 0, 0); kpr_add(&s, big, 0, 0, 0); CHECK(s.nent == 1 && s.ent[0].without_send == 2); }

    /* log budget: first 3 lines always, then only new (name, state) pairs, hard cap */
    memset(&lg, 0, sizeof lg); lg.always = 3; lg.cap = 5;
    CHECK(kpr_log_ok(&lg, "a", 1)); CHECK(kpr_log_ok(&lg, "a", 1)); CHECK(kpr_log_ok(&lg, "a", 1));   /* the 3 free lines, duplicates included */
    CHECK(!kpr_log_ok(&lg, "a", 1));                                                                  /* duplicate after the free lines */
    CHECK(kpr_log_ok(&lg, "a", 0));                                                                   /* same name, other state = new */
    CHECK(kpr_log_ok(&lg, "b", 1));
    CHECK(!kpr_log_ok(&lg, "c", 1));                                                                  /* cap 5 reached */
    printf("%s: %d checks, %d fails\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
