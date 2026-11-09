/* klcmpcore_test.c - off-game checks of klcmpcore_logic.h (the pure part of klcampaign.c, ported from luvsic's loader).
 * Build: cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klcmpcore_test.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "klcmpcore_logic.h"
static int fails, checks;
#define CHECK(c) do { checks++; if (!(c)) { fails++; printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)

int main(void)
{
    char id[16], p[128]; int mode; unsigned char dm[0x38], dd[0x38], buf[512]; int i;
    /* ids */
    CHECK(klcmpc_id_ok("M01") && klcmpc_id_ok("M03B") && klcmpc_id_ok("m07f"));
    CHECK(!klcmpc_id_ok("") && !klcmpc_id_ok(0) && !klcmpc_id_ok("M0001") && !klcmpc_id_ok("M0\\1") && !klcmpc_id_ok("..") && !klcmpc_id_ok("M 1"));
    CHECK(klcmpc_dm_index("M01") == 0 && klcmpc_dm_index("m03b") == 3 && klcmpc_dm_index("M14") == 16 && klcmpc_dm_index("M04") == -1 && klcmpc_dm_index("F01") == -1);
    CHECK(klcmpc_dm_index("M03") == 2 && klcmpc_dm_index("M3") == -1 && klcmpc_dm_index("M031") == -1);
    CHECK(klcmpc_alias("M07F") && !klcmpc_alias("M07") && !klcmpc_alias("M01"));
    CHECK(klcmpc_rpath("M01", p, sizeof p) && !strcmp(p, "Locations/M01/M01_Main.zip"));
    CHECK(klcmpc_rpath("M07F", p, sizeof p) && !strcmp(p, "CutScenes/M07/M07_A_Funeral.zip"));
    CHECK(!klcmpc_rpath("M0/1", p, sizeof p));
    CHECK(!klcmpc_rpath("M01", p, 10));
    /* scene of an opened archive path */
    CHECK(klcmpc_scene_of_path("C:\\x\\Scenes\\Locations\\M01\\M01_Main.zip", id) && !strcmp(id, "M01"));
    CHECK(klcmpc_scene_of_path("C:/x/Scenes/Locations/m03b/m03b_Main.zip", id) && !strcmp(id, "M03B"));
    CHECK(klcmpc_scene_of_path("Scenes\\Locations\\F01\\F01_Main.zip", id) && !strcmp(id, "F01"));
    CHECK(klcmpc_scene_of_path("Scenes\\Locations\\M09\\M09_Main_ls.zip", id) && !strcmp(id, "M09"));
    CHECK(klcmpc_scene_of_path("C:\\g\\Scenes\\CutScenes\\M07\\M07_A_Funeral.zip", id) && !strcmp(id, "M07F"));
    CHECK(klcmpc_scene_of_path("C:\\g\\KaneAndLynch.zip", id) && !strcmp(id, "FE"));
    CHECK(!klcmpc_scene_of_path("C:\\g\\Scenes\\Locations\\M01\\M02_Main.zip", id));          /* folder and file disagree */
    CHECK(!klcmpc_scene_of_path("C:\\g\\Scenes\\Other\\M01\\M01_Main.zip", id));
    CHECK(!klcmpc_scene_of_path("C:\\g\\Patch01.zip", id));
    CHECK(!klcmpc_scene_of_path("C:\\g\\Scenes\\Locations\\M01\\M01_Main.gms", id));
    CHECK(!klcmpc_scene_of_path("M01_Main.zip", id));
    /* saves */
    CHECK(klcmpc_is_kls("0.kls") && klcmpc_is_kls("12.KLS") && !klcmpc_is_kls(".kls") && !klcmpc_is_kls("a.kls") && !klcmpc_is_kls("1.klsx") && !klcmpc_is_kls("1.zip"));
    CHECK(klcmpc_save_path("C:\\A", "Campaign", "0.kls", p, sizeof p) && !strcmp(p, "C:\\A\\saves\\Campaign\\0.kls"));
    CHECK(!klcmpc_save_path("C:\\A", "Campaign", "0.kls", p, 10));
    /* trigger file */
    CHECK(klcmpc_parse_load("M01 1", id, &mode) && !strcmp(id, "M01") && mode == 1);
    CHECK(klcmpc_parse_load("  m03b   2\r\n", id, &mode) && !strcmp(id, "M03B") && mode == 2);
    CHECK(klcmpc_parse_load("M02", id, &mode) && !strcmp(id, "M02") && mode == 1);
    CHECK(klcmpc_parse_load("M09B 0", id, &mode) && mode == 0);
    CHECK(!klcmpc_parse_load("", id, &mode) && !klcmpc_parse_load("   ", id, &mode) && !klcmpc_parse_load("M0123456 1", id, &mode) && !klcmpc_parse_load("..\\x", id, &mode));
    /* progress */
    CHECK(klcmpc_reached_advances("M01", "M02") && !klcmpc_reached_advances("M02", "M01") && !klcmpc_reached_advances("M02", "M02") && klcmpc_reached_advances("", "M01") && !klcmpc_reached_advances("M01", "F01"));
    /* steady pump */
    { struct klcmpc_steady s; memset(&s, 0, sizeof s);
      CHECK(klcmpc_steady_update(&s, 1000, 250) == 0);
      CHECK(klcmpc_steady_update(&s, 1100, 250) == 100);
      CHECK(klcmpc_steady_update(&s, 1900, 250) == 0);              /* a gap of 800 ms restarts it (a scene load blocks the pump) */
      CHECK(klcmpc_steady_update(&s, 2100, 250) == 200); }
    /* .str headers */
    memset(dm, 0, sizeof dm); memcpy(dm, "IOISNDSTREAM", 12);
    for (i = 12; i < 0x38; i++) dm[i] = (unsigned char)(0x40 + i);
    klcmpc_wr32(dm + 0x18, 0x12345678); klcmpc_wr32(dm + 0x1c, 321);
    CHECK(klcmpc_str_is_dm(dm));
    klcmpc_str_hdr_dd(dm, dd);
    CHECK(klcmpc_rd32(dd + 0x18) == 0x12345678 && klcmpc_rd32(dd + 0x1c) == 0);                  /* tableOffset widened to u64 */
    CHECK(klcmpc_rd32(dd + 0x20) == 321);                                                          /* count moved up by 4 */
    CHECK(memcmp(dd + 0x24, dm + 0x20, 0x10) == 0 && memcmp(dd + 0x34, dm + 0x30, 4) == 0 && memcmp(dd, dm, 0x18) == 0);
    CHECK(!klcmpc_str_is_dm(dd));                                                                  /* a Dog Days header (count word 0) is left alone */
    klcmpc_wr32(dm + 0x1c, 0); CHECK(!klcmpc_str_is_dm(dm));
    klcmpc_wr32(dm + 0x1c, 100000); CHECK(!klcmpc_str_is_dm(dm));
    memcpy(dm, "IOISNDSTREAX", 12); klcmpc_wr32(dm + 0x1c, 5); CHECK(!klcmpc_str_is_dm(dm));
    /* entries, layout, virtual search, overlay */
    { unsigned char rec[72]; unsigned long meta[9] = {3, 1000, 2, 22050, 4, 0, 0, 1024, 1017}; klcmpc_ent e[3], x; int n = 0; long long end;
      memset(rec, 0, sizeof rec);
      klcmpc_wr32(rec + 8, 5000); klcmpc_wr32(rec + 16, 9000); klcmpc_wr32(rec + 24, 300); klcmpc_wr32(rec + 32, 36);
      CHECK(klcmpc_ent_from(rec, meta, 0x200, 7, &e[n])); CHECK(e[n].idxPos == 0x200 + 7 * 72 && e[n].ch == 2 && e[n].dataOff == 5000); n++;
      klcmpc_wr32(rec + 8, 100); klcmpc_wr32(rec + 24, 400); meta[2] = 1; meta[1] = 5000; meta[7] = 1024; meta[8] = 2041;
      CHECK(klcmpc_ent_from(rec, meta, 0x200, 3, &e[n])); n++;
      klcmpc_wr32(rec + 8, 20); klcmpc_wr32(rec + 24, 500);
      CHECK(klcmpc_ent_from(rec, meta, 0x200, 1, &e[n])); n++;
      meta[0] = 2; CHECK(!klcmpc_ent_from(rec, meta, 0x200, 1, &x));       /* not codec 3 */
      meta[0] = 3; meta[2] = 3; CHECK(!klcmpc_ent_from(rec, meta, 0x200, 1, &x));    /* 3 channels */
      meta[2] = 1; klcmpc_wr32(rec + 32, 28); CHECK(!klcmpc_ent_from(rec, meta, 0x200, 1, &x));   /* short meta */
      end = klcmpc_layout(e, n);
      CHECK(e[0].dataOff == 20 && e[1].dataOff == 100 && e[2].dataOff == 5000);                  /* sorted by data offset */
      CHECK(e[0].voff == KLCMPC_VBASE && e[1].voff == KLCMPC_VBASE + 0x3000 && e[0].pcm == 10000 && e[2].pcm == 4000);   /* 10000 bytes -> a 0x3000 slot */
      CHECK(e[2].voff == KLCMPC_VBASE + 0x6000 && end == e[2].voff + 0x1000);
      CHECK(klcmpc_find_v(e, n, KLCMPC_VBASE - 1) == -1 && klcmpc_find_v(e, n, KLCMPC_VBASE) == 0 && klcmpc_find_v(e, n, e[1].voff + 5) == 1 && klcmpc_find_v(e, n, end + 100) == 2);
      /* overlay: a read of the first 0x38 bytes gets the converted header; a read over the index gets virtual offset + size; the meta gets PCM */
      memset(buf, 0xee, sizeof buf); memcpy(dm, "IOISNDSTREAM", 12); klcmpc_str_hdr_dd(dm, dd);
      klcmpc_overlay(buf, 0, 0x20, dd, e, n, 0x200, 10);
      CHECK(memcmp(buf, dd, 0x20) == 0 && buf[0x20] == 0xee);
      memset(buf, 0xee, sizeof buf);
      klcmpc_overlay(buf, 0x200, 200, dd, e, n, 0x200, 10);       /* records 0..2 (idx 1 and 3 are ours, at 0x200+72 and +216) */
      { unsigned long long v = 0; memcpy(&v, buf + (0x200 + 72 + 8 - 0x200), 8);                          /* entry with idx 1 = e[0] */
        CHECK(v == (unsigned long long)e[0].voff); memcpy(&v, buf + 72 + 16, 8); CHECK(v == (unsigned long long)e[0].pcm); }
      memset(buf, 0xee, sizeof buf);
      klcmpc_overlay(buf, e[1].metaOff - 4, 60, dd, e, n, 0x200, 10);                                     /* a window over e[1]'s meta block */
      CHECK(klcmpc_rd32(buf + 4) == 2 && klcmpc_rd32(buf + 8) == e[1].samples * e[1].ch && klcmpc_rd32(buf + 4 + 16) == 16 && klcmpc_rd32(buf + 4 + 28) == 2 * e[1].ch);
      CHECK(buf[0] == 0xee && buf[4 + 36] == 0xee);
    }
    /* virtual block mapping */
    { unsigned long blk, off;
      CHECK(klcmpc_vmap(1, 1024, 4000, 8100, &blk, &off) == 0 && blk == 2 && off == 100);
      CHECK(klcmpc_vmap(KLCMPC_LIP, 1024, 4000, 100, &blk, &off) == -1);
      CHECK(klcmpc_vmap(KLCMPC_LIP, 1024, 4000, 4096, &blk, &off) == 0 && blk == 4 && off == 0);
      CHECK(klcmpc_vmap(KLCMPC_LIP, 1024, 4000, 4096 + 4001, &blk, &off) == 0 && blk == 5 && off == 1);
    }
    printf("RESULT: %s (%d checks, %d failed)\n", fails ? "FAIL" : "PASS", checks, fails);
    return fails != 0;
}
