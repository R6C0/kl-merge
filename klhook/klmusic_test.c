/* klmusic_test.c - off-game harness for klmusic.c's worker (the MCI side): plays short files at VOLUME 0 (silent) and prints what the
   worker does. Build: cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klmusic_test.c  (from a VS x86 prompt); run: klmusic_test.exe a.mp3 b.mp3 s.mp3
   Checks: crossfade between two tracks at the end of the first (follow), a mood change, a stinger lead, END (stinger once, then none). */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#define KLMUSIC_TEST
static void klog(const char *fmt, ...) { va_list a; SYSTEMTIME t; GetLocalTime(&t); printf("%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds); va_start(a, fmt); vprintf(fmt, a); va_end(a); printf("\n"); fflush(stdout); }
#include "klmusic.c"

static void post(int mood, int n, char **f, int ns, char **sf, int fade)
{
    int i;
    EnterCriticalSection(&klmu_cs);
    klmu_cmd.seq++; klmu_cmd.mood = mood; klmu_cmd.vol = 0; klmu_cmd.fade = fade; klmu_cmd.rnd = 0;
    klmu_cmd.pl.n = n; for (i = 0; i < n; i++) snprintf(klmu_cmd.pl.f[i], KLMU_PATH, "%s", f[i]);
    klmu_cmd.lead.n = ns; for (i = 0; i < ns; i++) snprintf(klmu_cmd.lead.f[i], KLMU_PATH, "%s", sf[i]);
    LeaveCriticalSection(&klmu_cs);
    SetEvent(klmu_ev);
}

int main(int argc, char **argv)
{
    char *two[2], *st[1];
    if (argc < 4) { printf("usage: klmusic_test a.mp3 b.mp3 stinger.mp3\n"); return 2; }
    two[0] = argv[1]; two[1] = argv[2]; st[0] = argv[3];
    InitializeCriticalSection(&klmu_cs); klmu_ev = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, klmu_thread, 0, 0, 0));
    printf("--- CALM, two 6 s tracks, fade 1000: expect a, then b about 4.7 s later (crossfade), then a again\n");
    post(KLMU_CALM, 2, two, 0, 0, 1000); Sleep(11000);
    printf("--- ACTION with a stinger lead (4 s), list = b: expect stinger, then b\n");
    post(KLMU_ACTION, 1, &two[1], 1, st, 1000); Sleep(8000);
    printf("--- END: stinger once, nothing after\n");
    post(KLMU_END, 0, 0, 1, st, 1000); Sleep(7000);
    printf("--- NONE\n");
    post(KLMU_NONE, 0, 0, 0, 0, 1000); Sleep(2500);
    printf("cur=%d open0=%d open1=%d errors=%d\n", klmu_cur, klmu_sl[0].open, klmu_sl[1].open, klmu_nerr);
    return (klmu_cur == -1 && !klmu_sl[0].open && !klmu_sl[1].open && !klmu_nerr) ? 0 : 1;
}
