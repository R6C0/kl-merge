/* klhook/test_shim/windows.h - a stand-in for <windows.h> so the PURE-LOGIC self-tests (the *_test.c files that include only a
   *_logic.h / *.h header, never a whole kl*.c module) build on a Linux/macOS host with gcc:
       gcc -m32 -I klhook/test_shim -o out klhook/klcs_test.c -lm
   tools/kl_tests.py does exactly this for every such test (and uses the real SDK with cl on Windows).
   -m32 is required, not a nicety: the game and the MSVC x86 build are ILP32, so `unsigned long` is 32 bits there and the tick-wrap
   checks (klcq_due, kluc_wait_left: 0xfffffff0 -> 0x10) only hold with a 32-bit long. On an LP64 build they FAIL for that reason alone.
   Only type names and calling-convention macros live here. No Win32 FUNCTION is provided on purpose: a test that needs one
   (VirtualQuery, CRITICAL_SECTION, MSG, FILETIME ...) includes a whole module and belongs to the Windows build (see the table in
   tools/kl_tests.py). The shim is never part of dinput8.dll. */
#ifndef KL_TEST_SHIM_WINDOWS_H
#define KL_TEST_SHIM_WINDOWS_H
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>

typedef uint32_t DWORD;
typedef uint16_t WORD;
typedef unsigned char BYTE;
typedef int BOOL;
typedef long LONG;
typedef unsigned long ULONG;
typedef int64_t LONGLONG;
typedef uint64_t ULONGLONG;
typedef unsigned int UINT;
typedef uintptr_t UINT_PTR;
typedef intptr_t INT_PTR;
typedef uintptr_t DWORD_PTR;
typedef size_t SIZE_T;
typedef float FLOAT;
typedef char CHAR;
typedef const char *LPCSTR;
typedef char *LPSTR;
typedef void *LPVOID;
typedef const void *LPCVOID;
typedef void *HANDLE;
typedef void *HWND;
typedef void *HMODULE;

#ifndef TRUE
#define TRUE 1
#endif
#ifndef FALSE
#define FALSE 0
#endif
#ifndef MAX_PATH
#define MAX_PATH 260
#endif
#define WINAPI
#define CALLBACK
#define __stdcall
#define __cdecl
#define __forceinline inline
#define _snprintf snprintf   /* MSVC spelling used by the hook sources */

#endif
