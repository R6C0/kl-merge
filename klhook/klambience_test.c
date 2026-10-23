/* klambience_test.c - off-game harness for klambience.c's worker: a bed (volume 0 = silent) that must restart when it ends, plus
   one-shots. Build: cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klambience_test.c (VS x86 prompt); run: klambience_test.exe bed.mp3 shot.mp3
   Expect: bed opens, restarts (log shows MCI ok), 6 shots overflow the 4 slots (2 dropped or queued), all closed at the end. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#define KLAMBIENCE_TEST
static void klog(const char *fmt, ...) { va_list a; SYSTEMTIME t; GetLocalTime(&t); printf("%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds); va_start(a, fmt); vprintf(fmt, a); va_end(a); printf("\n"); fflush(stdout); }
#include "klambience.c"

static void bed(const char *f, int fade)
{
    EnterCriticalSection(&klam_cs);
    klam_cmd.seq++; klam_cmd.vol = 0; klam_cmd.fade = fade; klam_cmd.bedvol = 45; snprintf(klam_cmd.bed, sizeof klam_cmd.bed, "%s", f);
    LeaveCriticalSection(&klam_cs); SetEvent(klam_ev);
}
static void shot(const char *f)
{
    EnterCriticalSection(&klam_cs);
    snprintf(klam_q[klam_qt].f, KLAM_PATH, "%s", f); klam_q[klam_qt].vol = 50; klam_qt = (klam_qt + 1) % KLAM_QN;
    LeaveCriticalSection(&klam_cs); SetEvent(klam_ev);
}
int main(int argc, char **argv)
{
    int i, open;
    if (argc < 3) { printf("usage: klambience_test bed.mp3 shot.mp3\n"); return 2; }
    InitializeCriticalSection(&klam_cs); klam_ev = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, klam_thread, 0, 0, 0));
    printf("--- bed (volume 0), 6 s of it, with 3 shots\n");
    bed(argv[1], 500); Sleep(800); for (i = 0; i < 3; i++) shot(argv[2]); Sleep(6000);
    printf("--- bed off\n"); bed("", 500); Sleep(1500);
    open = klam_bed.open; for (i = 0; i < KLAM_NSHOT; i++) open += klam_sh[i].open;
    printf("open=%d errors=%d\n", open, klam_nerr);
    return (!open && !klam_nerr) ? 0 : 1;
}
