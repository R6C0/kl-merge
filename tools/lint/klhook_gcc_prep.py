#!/usr/bin/env python3
"""Prepares a scratch copy of klhook/ for a GCC type check (tools/run_harness_linux.sh --check-hook).

The real build is MSVC. GCC cannot parse MSVC's structured exception handling or inline assembly, so for the
TYPE CHECK ONLY this rewrites them into plain C that keeps every expression visible to the compiler:
  __try { X }  __except (F) { H }   ->   if (1) { X }  else if (klchk_filter(F)) { H }
  __asm <insn> [<ops>]              ->   ;              (single-line statements)
  #define XXX_FWD(n) ... naked __asm forwarders   ->   an empty function
  GetExceptionInformation()         ->   ((EXCEPTION_POINTERS *)0)
Nothing it produces is ever compiled into the DLL. Usage: klhook_gcc_prep.py <scratch dir>
"""
import re, sys, os

FWD = re.compile(r'^#define (KL[A-Z]*_FWD)\(n\) .*$', re.M)
THUNK = re.compile(r'^#define KVO_THUNK\(n\) .*$', re.M)          # klvoice.c: naked thunks kvo_t<n>
ASMBLK = re.compile(r'__asm\s*\{[^}]*\}')                      # multi-line __asm { ... } block (no braces inside)
ASM = re.compile(r'^(\s*)__asm\s+[a-z]+(?:\s+[^\n]*)?$', re.M)
TRY = re.compile(r'__try\s*\{')
EXC = re.compile(r'__except\s*\(')

def prep(path):
    s = open(path, encoding='latin-1').read()
    o = s
    s = FWD.sub(lambda m: '#define %s(n) static void %s##n(void) { }   /* GCC TYPE CHECK ONLY */'
                % (m.group(1), {'KLX_FWD': 'klx_fwd', 'KLMM_FWD': 'klmm_fwd', 'KLBLD_FWD': 'klbld_fwd'}.get(m.group(1), m.group(1).lower())), s)
    s = THUNK.sub('#define KVO_THUNK(n) static void kvo_t##n(void) { }   /* GCC TYPE CHECK ONLY */', s)
    s = ASMBLK.sub(';', s)
    s = ASM.sub(lambda m: m.group(1) + ';', s)
    s = s.replace('GetExceptionInformation()', '((EXCEPTION_POINTERS *)0)')
    s = TRY.sub('if (1) {', s)
    # __except (expr) { ... }  ->  else if (klchk_filter(expr)) { ... } : expr stays type-checked, never runs
    out, i = [], 0
    for m in EXC.finditer(s):
        start = m.end()           # just after '('
        depth, j = 1, start
        while depth and j < len(s):
            depth += {'(': 1, ')': -1}.get(s[j], 0)
            j += 1
        out.append(s[i:m.start()]); out.append('else if (klchk_filter(' + s[start:j - 1] + '))'); i = j
    out.append(s[i:]); s = ''.join(out)
    if s != o:
        if 'klchk_filter(' in s and not s.startswith('static long klchk_filter'):
            s = 'static long klchk_filter(long x);   /* GCC TYPE CHECK ONLY */\n' + s
        open(path, 'w', encoding='latin-1').write(s)
        return True
    return False

d = sys.argv[1]
n = sum(prep(os.path.join(d, f)) for f in os.listdir(d) if f.endswith('.c'))
# one definition, in the single translation unit's root (klhook.c includes the modules)
root = os.path.join(d, 'klhook.c')
r = open(root, encoding='latin-1').read()
open(root, 'w', encoding='latin-1').write(r.replace('#include <windows.h>', '#include <windows.h>\nstatic long klchk_filter(long x) { return x; }   /* GCC TYPE CHECK ONLY */', 1))
print('klhook_gcc_prep: %d file(s) rewritten for the type check' % n)
