/* klmciwrap_test.c - off-game regression for the MCI worker clock wrap (mciwrap 1023; see re/mciwrap_1023.md). Silent (volume 0).
   AMBIENCE: cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klmciwrap_test.c /Feamb.exe   (VS x86 prompt)   run: amb.exe long.mp3
   MUSIC:    cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS /DTEST_MUSIC klmciwrap_test.c /Femus.exe   run: mus.exe long.mp3
   long.mp3 = any mp3 of 20 s or more. The wrap needs a slow MCI 'open' to land in the same worker pass as a 250 ms poll, so each round is
   chance (about open_ms / 250); the test repeats 40 times (about 60 s). Old code: AMBIENCE reports 'closed early', MUSIC reports 'skipped'.
   A fixed worker: exit 0. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
static volatile LONG nlog;
static void klog(const char *fmt, ...) { va_list a; va_start(a, fmt); vprintf(fmt, a); va_end(a); printf("\n"); fflush(stdout); nlog++; }
#ifndef TEST_MUSIC
#define KLAMBIENCE_TEST
#include "klambience.c"
int main(int argc, char **argv)
{
    int i, bad = 0;
    if (argc < 2) { printf("usage: klmciwrap_test long.mp3\n"); return 2; }
    InitializeCriticalSection(&klam_cs); klam_ev = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, klam_thread, 0, 0, 0));
    for (i = 0; i < 40; i++) {
        int k, open;
        Sleep(37 * (i % 7));                                   /* vary the phase against the 250 ms poll */
        EnterCriticalSection(&klam_cs);
        snprintf(klam_q[klam_qt].f, KLAM_PATH, "%s", argv[1]); klam_q[klam_qt].vol = 0; klam_qt = (klam_qt + 1) % KLAM_QN;
        LeaveCriticalSection(&klam_cs); SetEvent(klam_ev);
        Sleep(900);                                            /* a 20 s clip is still playing: the slot must be open */
        open = 0; for (k = 0; k < KLAM_NSHOT; k++) open += klam_sh[k].open;
        if (!open) { bad++; printf("round %d: the one-shot was closed early (clock wrap)\n", i); }
        EnterCriticalSection(&klam_cs); klam_cmd.seq++; klam_cmd.stop = 1; klam_cmd.bed[0] = 0; LeaveCriticalSection(&klam_cs); SetEvent(klam_ev);
        Sleep(300);
    }
    printf("ambience: %d of 40 closed early, MCI errors %d\n", bad, klam_nerr);
    return bad || klam_nerr ? 1 : 0;
}
#else
#define KLMUSIC_TEST
#include "klmusic.c"
int main(int argc, char **argv)
{
    int i, bad = 0;
    if (argc < 2) { printf("usage: klmciwrap_test long.mp3\n"); return 2; }
    InitializeCriticalSection(&klmu_cs); klmu_ev = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, klmu_thread, 0, 0, 0));
    for (i = 0; i < 40; i++) {
        LONG before; int cur0;
        Sleep(37 * (i % 7));
        before = nlog;
        EnterCriticalSection(&klmu_cs);
        klmu_cmd.seq++; klmu_cmd.mood = KLMU_CALM; klmu_cmd.vol = 0; klmu_cmd.fade = 0; klmu_cmd.rnd = 0; klmu_cmd.lead.n = 0;
        klmu_cmd.pl.n = 2; snprintf(klmu_cmd.pl.f[0], KLMU_PATH, "%s", argv[1]); snprintf(klmu_cmd.pl.f[1], KLMU_PATH, "%s", argv[1]);
        LeaveCriticalSection(&klmu_cs); SetEvent(klmu_ev);
        Sleep(1200);                                           /* exactly ONE 'music: ...' start line: a second one = the follow logic skipped the fresh track */
        cur0 = klmu_cur;
        if (nlog - before != 1 || cur0 < 0) { bad++; printf("round %d: %ld start lines, cur=%d (skipped)\n", i, (long)(nlog - before), cur0); }
        EnterCriticalSection(&klmu_cs); klmu_cmd.seq++; klmu_cmd.mood = KLMU_NONE; klmu_cmd.fade = 0; klmu_cmd.pl.n = 0; klmu_cmd.lead.n = 0; LeaveCriticalSection(&klmu_cs); SetEvent(klmu_ev);
        Sleep(300);
    }
    printf("music: %d of 40 skipped, MCI errors %d\n", bad, klmu_nerr);
    return bad || klmu_nerr ? 1 : 0;
}
#endif
