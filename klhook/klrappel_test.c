/* klrappel_test.c - off-game harness for klrappel.c (track Y3). Builds the part against a FAKE address space (addresses are
   offsets) with the player / node / channel / clip laid out as klrappel.c reads them, a FAKE of the game's placement
   (0x82cc40: writes the node's position) and of the rotation builder, and a real KLJoin.ini [Rappel] section written to a
   temp file. Replays: a normal descent; the game moving him too; the channel vanishing; a node far from Start; a dry run;
   a refused section. NOT THE GAME: it proves the logic and the order of the writes, not that the game agrees.
   Build (x86, VS prompt):  cl /nologo /W3 klrappel_test.c /Fe:klrappel_test.exe      Run: klrappel_test.exe */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdarg.h>

#define KLH_VA(x) (x)
#define KL2_SYSIF 0x6000
static BYTE mem[0x20000];
static char logbuf[1 << 18]; static int nlog;
static char klh_ini_buf[MAX_PATH]; static const char *klh_ini = klh_ini_buf;
static int klh_exe_ok = 1;
static void klog(const char *fmt, ...)
{
    va_list ap; char t[1800]; va_start(ap, fmt); vsnprintf(t, sizeof t, fmt, ap); va_end(ap);
    nlog += snprintf(logbuf + nlog, sizeof logbuf - nlog - 1, "%s\n", t);
}
static int klh_rd(DWORD_PTR p, void *out, SIZE_T n) { if (p < 0x100 || p + n > sizeof mem) return 0; memcpy(out, mem + p, n); return 1; }
static DWORD klh_rd32(DWORD_PTR p) { DWORD v = 0; klh_rd(p, &v, 4); return v; }
static int klb_finite(float f) { return f == f && f > -1e9f && f < 1e9f; }
static int klt_same_code(DWORD va, const BYTE *b, int n) { (void)va; (void)b; (void)n; return 1; }
static CRITICAL_SECTION klj_cs; static char klj_map_key[64], klj_map_file[MAX_PATH]; static FILETIME klj_map_ft;
static int klj_vec(const char *sec, const char *key, const char *file, float v[3])
{
    char t[96], *p;
    if (!GetPrivateProfileStringA(sec, key, "", t, sizeof t, file)) return 0;
    for (p = t; *p; p++) if (*p == ',' || *p == ';' || *p == '(' || *p == ')') *p = ' ';
    return sscanf(t, "%f %f %f", &v[0], &v[1], &v[2]) == 3;
}
static int klh_scene(char *out, int cap) { snprintf(out, cap, "SCENES\\Locations\\F06\\F06_Main.gms"); return 1; }
static int klh_level_key(const char *scene, char *key, int cap) { (void)scene; snprintf(key, cap, "f06\\f06_main"); return 1; }
#define PL 0x1000
#define NODE 0x2000
#define ANM 0x3000
#define CLIP 0x4000
static int kle_human(DWORD *player, float feet[3], float nodepos[3]) { *player = PL; memcpy(feet, mem + NODE + 36, 12); memcpy(nodepos, mem + NODE + 36, 12); return 1; }
static int g_placed, g_nudge; static float g_last[3];
static void fake_place(DWORD pl, const float *rot, const float *p)
{
    (void)pl; (void)rot; memcpy(mem + NODE + 36, p, 12); memcpy(g_last, p, 12); g_placed++;
    if (g_nudge) { float y; memcpy(&y, mem + NODE + 40, 4); y -= 20.0f; memcpy(mem + NODE + 40, &y, 4); }      /* the game moves him too */
}
#define KLRP_PLACE_CALL(pl, rot, p) fake_place((pl), (rot), (p))
#define KLRP_MATRIX_CALL(rot, v3) do { (rot)[0] = (v3)[0]; (rot)[1] = (v3)[1]; (rot)[2] = (v3)[2]; } while (0)

#include "klrappel.c"

static void setf(DWORD a, float v) { memcpy(mem + a, &v, 4); }
static void set32(DWORD a, DWORD v) { memcpy(mem + a, &v, 4); }
static void world(void)
{
    int i;
    memset(mem, 0, sizeof mem);
    set32(PL, KLRP_PLAYER_VT); set32(PL + 4, NODE); set32(PL + 0x70, ANM);
    setf(NODE + 0, 1); setf(NODE + 16, 1); setf(NODE + 32, 1);                      /* identity m[0], m[4], m[8]: rows of a 3x3 */
    setf(NODE + 36, 5998); setf(NODE + 40, 22767); setf(NODE + 44, -160);
    set32(ANM + 0x1c, CLIP); setf(ANM + 0x1c + 4, 0.0f); set32(ANM + 0x30, 0x8001);
    for (i = 1; i < 16; i++) set32(ANM + 0x30 + 0x38 * i, 4);
    mem[CLIP + 2] = 105; set32(0x6000, 0x7000);
}
static void ini(const char *extra, const char *prof)
{
    char f[MAX_PATH]; FILE *h;
    GetTempPathA(sizeof f, f); strcat(f, "klrappel_test.ini");
    h = fopen(f, "w");
    fprintf(h, "[Rappel]\nFrames=105\nStart=5998 22767 -160\nLand=6000 21011 0\nProfile=%s\n%s\n", prof, extra);
    fclose(h);
    strcpy(klj_map_file, f); strcpy(klj_map_key, "f06\\f06_main"); klj_map_ft.dwLowDateTime++;
}
static int fails;
#define CHECK(c, msg) do { if (!(c)) { fails++; printf("FAIL %s\n", msg); } else printf("ok   %s\n", msg); } while (0)
static const char *PROF = "0 20 80 190 330 500 670 810 920 980 1000";
static void frame(float t) { DWORD c = klh_rd32(0x7048); set32(0x7048, c + 40); setf(ANM + 0x1c + 4, t); }

int main(void)
{
    int t; float y, prev; char tmp[MAX_PATH];
    InitializeCriticalSection(&klj_cs);
    GetTempPathA(sizeof tmp, tmp); snprintf(klh_ini_buf, sizeof klh_ini_buf, "%sklrappel_test_hook.ini", tmp);
    { FILE *h = fopen(klh_ini_buf, "w"); fprintf(h, "[Rappel]\nEnable=1\nLog=1\n"); fclose(h); }

    /* 1: a normal descent */
    world(); klrp_init(); ini("", PROF); nlog = 0; g_placed = 0; g_nudge = 0;
    CHECK(klrp.on, "Enable=1 is read");
    klrp_tick(1); CHECK(klrp_r.player == PL, "begun: the 105-frame full-body channel and the node at Start");
    prev = 22767.0f;
    for (t = 0; t <= 104; t++) {
        frame((float)t); klrp_tick(1);
        memcpy(&y, mem + NODE + 40, 4);
        if (y > prev + 0.01f) { CHECK(0, "monotone descent"); break; }
        prev = y;
    }
    memcpy(&y, mem + NODE + 40, 4);
    CHECK(!klrp_r.player, "ended at the last frames");
    CHECK(fabs(y - 21011.0f) < 0.01f && fabs(g_last[0] - 6000.0f) < 0.01f && fabs(g_last[2] - 0.0f) < 0.01f, "the last placement is Land exactly");
    CHECK(g_placed >= 100, "about a placement a frame");
    CHECK(strstr(logbuf, "LANDED") != 0, "LANDED said");
    /* the profile: at frame 52 (s = 0.5) the share is the middle value 500 */
    world(); klrp_init(); ini("", PROF); g_placed = 0; Sleep(60); klrp_tick(1); frame(52.0f); klrp_tick(1);
    memcpy(&y, mem + NODE + 40, 4);
    CHECK(fabs(y - (22767.0f + (21011.0f - 22767.0f) * 0.5f)) < 2.0f, "frame 52 of 104 is half the drop (profile 500)");

    /* 2: the game moves him as well */
    world(); klrp_init(); ini("", PROF); nlog = 0; g_placed = 0; g_nudge = 1; Sleep(60);
    klrp_tick(1); for (t = 0; t <= 30; t++) { frame((float)t); klrp_tick(1); }
    CHECK(strstr(logbuf, "THE GAME MOVES HIM TOO") != 0, "a node moved by someone else is detected");
    CHECK(g_placed <= 4, "...and nothing is placed on after it");
    g_nudge = 0;

    /* 3: the channel disappears at frame 40 */
    world(); klrp_init(); ini("", PROF); nlog = 0; g_placed = 0; Sleep(60);
    klrp_tick(1); for (t = 0; t <= 40; t++) { frame((float)t); klrp_tick(1); }
    set32(ANM + 0x30, 4);
    klrp_tick(1);
    CHECK(strstr(logbuf, "STOPPED") != 0 && !klrp_r.player, "a vanished channel stops it without a landing");

    /* 4: his node is far from Start */
    world(); klrp_init(); ini("", PROF); nlog = 0; setf(NODE + 36, 3000); Sleep(60); klrp_tick(1);
    CHECK(!klrp_r.player && strstr(logbuf, "not the descent") != 0, "a node far from Start does not begin it");

    /* 5: dry run */
    world(); GetTempPathA(sizeof tmp, tmp); { FILE *h = fopen(klh_ini_buf, "w"); fprintf(h, "[Rappel]\nEnable=1\nDry=1\n"); fclose(h); }
    klrp_init(); ini("", PROF); g_placed = 0; Sleep(60); klrp_tick(1); for (t = 0; t <= 104; t++) { frame((float)t); klrp_tick(1); }
    CHECK(g_placed == 0 && strstr(logbuf, "DRY RUN") != 0, "Dry=1 places nothing");
    { FILE *h = fopen(klh_ini_buf, "w"); fprintf(h, "[Rappel]\nEnable=1\nLog=1\n"); fclose(h); }

    /* 6: a bad profile is refused */
    world(); klrp_init(); ini("", "0 300 200 1000"); nlog = 0; klrp_tick(1);
    CHECK(!klrp_lv.ok && !klrp_r.player, "a profile that goes back is refused");

    /* 7: armed again only after the channel has been gone for 2 s */
    world(); klrp_init(); ini("", PROF); Sleep(60); klrp_tick(1); for (t = 0; t <= 104; t++) { frame((float)t); klrp_tick(1); }
    frame(104.0f); setf(NODE + 36, 5998); setf(NODE + 40, 22767); setf(NODE + 44, -160); Sleep(60); klrp_tick(1);
    CHECK(!klrp_r.player, "the held last frame of the same cut does not begin a second descent");
    printf("%s (%d failed)\n", fails ? "FAIL" : "ALL PASS", fails);
    if (fails) printf("%s\n", logbuf);
    return fails != 0;
}
