#!/usr/bin/env python3
"""
kl_tests.py - run EVERY off-game self-test of the repo in one go and say PASS / FAIL / SKIP per test (2026-10-28, scheduled check-in).

usage: python tools/kl_tests.py [--list] [--py | --c] [--only NAME ...] [--keep DIR] [-v]
  exit 0 = nothing failed (skips are fine), 1 = at least one FAIL, 2 = bad usage.

What it runs
  1. tools/*_test.py                 each with the repo's python, no arguments (their fixtures are hand-made unless the table
                                     PY_NEEDS names a game file; absent file -> SKIP, never FAIL). PY_NOT_TESTS names the
                                     *_test.py that drive the game (kl_solo_test.py): always SKIP.
  2. klhook/*_test.c  (logic)        the tests that include only a *_logic.h / *.h header: built with
                                        Windows:  cl /nologo /W3 test.c   (from a VS x86 prompt, or build.bat's vcvarsall)
                                        else:     gcc -m32 -I klhook/test_shim test.c -lm   (klhook/test_shim/windows.h)
                                     -m32 matters: the game is ILP32, `unsigned long` is 32 bits, the tick-wrap checks need it.
                                     No gcc -m32 (no gcc-multilib) -> SKIP with the reason, not FAIL.
  3. klhook/*_test.c  (win)          the tests that include a whole kl*.c module (VirtualQuery, CRITICAL_SECTION, MSG ...): cl only;
                                     on any other host -> SKIP.
A *_test.c not in C_TESTS is tagged UNLISTED and still tried (cl on Windows; the shim elsewhere, where a build failure is a
SKIP, not a verdict), so a new test is never silently dropped: add it to the table with its kind.
A test passes when its process exits 0 (every *_test.c and *_test.py here does that only on all-pass); the last line of its
output is shown beside the verdict. -v prints the whole output of every FAIL.

Written in the cloud on Linux (gcc -m32 path RUN, every listed test PASS or SKIP); the Windows cl path follows the build lines
in the tests' own headers and build.bat but was NOT RUN here (no cl in the cloud) - first Windows run: `python tools\\kl_tests.py --c`.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KLHOOK = os.path.join(ROOT, 'klhook')
SHIM = os.path.join(KLHOOK, 'test_shim')
WIN = sys.platform.startswith('win')
VCVARS = r'C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat'   # same as build.bat

# python tests that read a game file by default: (file that must exist) -> else SKIP
PY_NEEDS = {
    'kl_map_shift_test.py': [r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days\KLExpansion\Maps\DM11B\F04_Main.zip'],
}

# *_test.py files that are NOT self-tests (they drive the game): never run here
PY_NOT_TESTS = {
    'kl_solo_test.py': 'live two-seat bench driver (needs --hook and Dog Days)',
}

# C tests: 'logic' builds with the shim on any host, 'win' needs the real SDK (includes a whole module).
C_TESTS = {
    'klcs_test.c': 'logic',            # klcopsquad_logic.h
    'klcv_test.c': 'logic',            # klchar_voice.h
    'kldown_hold_test.c': 'logic',     # kldown_hold.h
    'klgetup_test.c': 'logic',         # klgetup_logic.h (+ kldown_hold.h)
    'kldown_mirror_test.c': 'logic',   # kldown_mirror_logic.h (no windows.h at all)
    'klgrades_test.c': 'logic',        # klgrades.h (uses _snprintf: -D_snprintf=snprintf)
    'kllootsync_test.c': 'logic',      # kllootsync_logic.h
    'klbalonline_test.c': 'logic',     # klbalonline.h
    'klshot_test.c': 'logic',          # klshot_logic.h (uses _snprintf: shim may need -D_snprintf=snprintf)
    'klbotvoice_test.c': 'logic',      # klbotvoice_logic.h
    'klht_test.c': 'logic',            # klhud_tags_dist.h
    'klmappool_ov_test.c': 'logic',    # no windows.h
    'klnc_test.c': 'logic',            # klnetchan_logic.h + klucc_logic.h
    'klonline_read_test.c': 'logic',   # klonline_read.h
    'klsabot_test.c': 'logic',         # klsabotage_logic.h
    'klua_test.c': 'logic',            # no windows.h
    'klucchide_test.c': 'logic',       # klucchide_logic.h
    'klud_test.c': 'logic',            # klucc_down_logic.h
    'kladren_test.c': 'win',           # includes kladren.c
    'klambience_test.c': 'win',        # klambience.c
    'klbotdown_test.c': 'win',         # klbotdown.c
    'klhigh_test.c': 'win',            # klhigh.c
    'klhigh_bits_test.c': 'win',       # bits.inc (generated beside the test on the PC)
    'klmciwrap_test.c': 'win',         # klambience.c + klmusic.c
    'klmem_test.c': 'win',             # klmem.c
    'klmusic_test.c': 'win',           # klmusic.c
    'klpm_test.c': 'win',              # klpm.c
    'klrappel_test.c': 'win',          # klrappel.c
    'klsb_test.c': 'win',              # klhud.c + klhud_board2.c
    'klstinger_test.c': 'win',         # klstinger.c
    'klwatch_test.c': 'win',           # klhud.c
}

TIMEOUT = 600


class Result:
    def __init__(self, name, verdict, note='', out=''):
        self.name, self.verdict, self.note, self.out = name, verdict, note, out


def last_line(text):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return lines[-1].strip()[:110] if lines else ''


def run(cmd, cwd, shell=False):
    try:
        p = subprocess.run(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT)
        return p.returncode, p.stdout.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired as e:
        return 124, (e.stdout or b'').decode('utf-8', 'replace') + '\n[timeout %d s]' % TIMEOUT
    except OSError as e:
        return 127, str(e)


def py_tests(only):
    for path in sorted(glob.glob(os.path.join(HERE, '*_test.py'))):
        name = os.path.basename(path)
        if name == os.path.basename(__file__) or (only and name not in only and name[:-3] not in only):
            continue
        if name in PY_NOT_TESTS:
            yield Result(name, 'SKIP', 'not a self-test: ' + PY_NOT_TESTS[name])
            continue
        missing = [f for f in PY_NEEDS.get(name, []) if not os.path.exists(f)]
        if missing:
            yield Result(name, 'SKIP', 'needs ' + os.path.basename(missing[0]) + ' (game file, not here)')
            continue
        rc, out = run([sys.executable, path], HERE)
        yield Result(name, 'PASS' if rc == 0 else 'FAIL', ('exit %d: ' % rc if rc else '') + last_line(out), out)


_gcc32 = None


def gcc_m32_ok():
    """gcc that can build 32-bit (gcc-multilib); cached."""
    global _gcc32
    if _gcc32 is None:
        _gcc32 = False
        if shutil.which('gcc'):
            d = tempfile.mkdtemp(prefix='kl_m32_')
            src = os.path.join(d, 'a.c')
            with open(src, 'w') as f:
                f.write('#include <stdio.h>\nint main(void){return sizeof(long)==4?0:1;}\n')
            rc, _ = run(['gcc', '-m32', '-o', os.path.join(d, 'a'), src], d)
            _gcc32 = rc == 0 and run([os.path.join(d, 'a')], d)[0] == 0
            shutil.rmtree(d, ignore_errors=True)
    return _gcc32


def build_c(name, outdir):
    """returns (rc, output, exe)"""
    src = os.path.join(KLHOOK, name)
    exe = os.path.join(outdir, name[:-2] + ('.exe' if WIN else ''))
    if WIN:
        cl = 'cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS "%s" /Fe:"%s"' % (src, exe)
        if shutil.which('cl'):
            rc, out = run(cl, outdir, shell=True)
        elif os.path.exists(VCVARS):
            rc, out = run('call "%s" x86 >nul 2>nul && %s' % (VCVARS, cl), outdir, shell=True)
        else:
            return 127, 'no cl on the PATH and no ' + VCVARS, exe
        return rc, out, exe
    cmd = ['gcc', '-m32', '-w', '-I', SHIM, '-D_snprintf=snprintf', '-o', exe, src, '-lm']
    rc, out = run(cmd, outdir)
    return rc, out, exe


def c_tests(only, outdir):
    listed = set(C_TESTS)
    names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(KLHOOK, '*_test.c')))
    for name in names:
        if only and name not in only and name[:-2] not in only:
            continue
        kind = C_TESTS.get(name)
        tag = '' if kind else ' UNLISTED (add it to C_TESTS)'
        if not WIN:
            if kind == 'win':
                yield Result(name, 'SKIP', 'needs the Windows SDK (includes a whole module)')
                continue
            if not gcc_m32_ok():
                yield Result(name, 'SKIP', 'needs gcc -m32 (install gcc-multilib); 64-bit long breaks the tick-wrap checks' + tag)
                continue
        rc, out, exe = build_c(name, outdir)
        if rc != 0:
            if kind is None and not WIN:   # an unlisted test is tried with the shim; not building there is no verdict
                yield Result(name, 'SKIP', 'did not build with the shim (needs the SDK?): ' + last_line(out) + tag)
            else:
                yield Result(name, 'FAIL', 'build failed: ' + last_line(out) + tag, out)
            continue
        rc, out = run([exe], outdir)
        yield Result(name, 'PASS' if rc == 0 else 'FAIL', ('exit %d: ' % rc if rc else '') + last_line(out) + tag, out)
    for name in sorted(listed - set(names)):
        yield Result(name, 'SKIP', 'listed in C_TESTS but the file is gone (drop the row)')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='print the tests and their kind, run nothing')
    ap.add_argument('--py', action='store_true', help='python tests only')
    ap.add_argument('--c', action='store_true', help='C tests only')
    ap.add_argument('--only', nargs='*', default=[], help='test file names (with or without extension)')
    ap.add_argument('--keep', help='build directory for the C tests (default: a temp dir, removed)')
    ap.add_argument('-v', action='store_true', help='print the full output of every FAIL')
    a = ap.parse_args()
    if a.py and a.c:
        print('--py and --c exclude each other')
        return 2
    if a.list:
        for p in sorted(glob.glob(os.path.join(HERE, '*_test.py'))):
            n = os.path.basename(p)
            if n != os.path.basename(__file__):
                print('%-28s py     %s' % (n, 'needs ' + ', '.join(PY_NEEDS[n]) if n in PY_NEEDS else
                                           'NOT A TEST: ' + PY_NOT_TESTS[n] if n in PY_NOT_TESTS else ''))
        for p in sorted(glob.glob(os.path.join(KLHOOK, '*_test.c'))):
            n = os.path.basename(p)
            print('%-28s c/%s' % (n, C_TESTS.get(n, 'UNLISTED')))
        return 0
    outdir = a.keep or tempfile.mkdtemp(prefix='kl_tests_')
    os.makedirs(outdir, exist_ok=True)
    only = set(a.only)
    results = []
    t0 = time.time()
    try:
        if not a.c:
            results += list(py_tests(only))
        if not a.py:
            results += list(c_tests(only, outdir))
    finally:
        if not a.keep:
            shutil.rmtree(outdir, ignore_errors=True)
    for r in results:
        print('%-5s %-28s %s' % (r.verdict, r.name, r.note))
        if a.v and r.verdict == 'FAIL':
            print('      ' + r.out.replace('\n', '\n      ').rstrip())
    n = {k: sum(1 for r in results if r.verdict == k) for k in ('PASS', 'FAIL', 'SKIP')}
    print('RESULT: %s - %d pass, %d fail, %d skip (%d tests, %.0f s, host %s%s)' % (
        'FAIL' if n['FAIL'] else 'PASS', n['PASS'], n['FAIL'], n['SKIP'], len(results), time.time() - t0,
        sys.platform, '' if WIN else (', gcc -m32 ' + ('ok' if gcc_m32_ok() else 'MISSING'))))
    return 1 if n['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
