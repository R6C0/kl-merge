/* klstinger_test.c - off-game harness for klstinger.c's worker. Build: cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS klstinger_test.c
   (VS x86 prompt); run: klstinger_test.exe short.mp3 [long.mp3]. Volume is 0 (silent).
   Expect: 3 shots on 2 slots (the third cuts the oldest), all open slots closed once they end, a stop command closes a long cue, 0 MCI errors, exit 0. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#define KLSTINGER_TEST
static void klog(const char *fmt, ...) { va_list a; SYSTEMTIME t; GetLocalTime(&t); printf("%02d:%02d:%02d.%03d ", t.wHour, t.wMinute, t.wSecond, t.wMilliseconds); va_start(a, fmt); vprintf(fmt, a); va_end(a); printf("\n"); fflush(stdout); }
#include "klstinger.c"

static void shot(const char *f)
{
    EnterCriticalSection(&klst_cs);
    klst_wmaster = 0;
    snprintf(klst_q[klst_qt].f, KLST_PATH, "%s", f); klst_q[klst_qt].vol = 50; klst_qt = (klst_qt + 1) % KLST_QN;
    LeaveCriticalSection(&klst_cs); SetEvent(klst_ev);
}
static int nopen(void) { int k, n = 0; for (k = 0; k < KLST_NSLOT; k++) n += klst_sh[k].open; return n; }
int main(int argc, char **argv)
{
    int i;
    if (argc < 2) { printf("usage: klstinger_test short.mp3 [long.mp3]\n"); return 2; }
    InitializeCriticalSection(&klst_cs); klst_ev = CreateEventA(0, FALSE, FALSE, 0);
    CloseHandle(CreateThread(0, 0, klst_thread, 0, 0, 0));
    printf("--- 3 shots on 2 slots\n");
    for (i = 0; i < 3; i++) { shot(argv[1]); Sleep(150); }
    /* the worker opens one mp3 at a time and an MCI open can take 1 s or more on a loaded machine: wait up to 6 s for the second slot */
    for (i = 0; i < 150 && nopen() != 2; i++) Sleep(100);
    printf("  second slot after %d ms\n", i * 100);
    printf("open=%d (must be 2)\n", nopen());
    if (nopen() != 2) return 1;
    Sleep(15000);
    printf("after the clips ended: open=%d errors=%d\n", nopen(), klst_nerr);
    if (nopen() || klst_nerr) return 1;
    printf("--- stop command\n");
    shot(argc > 2 ? argv[2] : argv[1]); Sleep(600);
    EnterCriticalSection(&klst_cs); klst_qh = klst_qt; klst_stopseq++; LeaveCriticalSection(&klst_cs); SetEvent(klst_ev); Sleep(800);
    printf("after stop: open=%d errors=%d\n", nopen(), klst_nerr);
    return (!nopen() && !klst_nerr) ? 0 : 1;
}
