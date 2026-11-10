#!/usr/bin/env python3
"""
kl_tests.py - run EVERY off-game self-test of the repo in one go and say PASS / FAIL / SKIP per test (2026-10-28, scheduled check-in).

usage: python tools/kl_tests.py [--list] [--py | --c] [--only NAME ...] [--keep DIR] [-v]
  exit 0 = nothing failed (skips are fine), 1 = at least one FAIL, 2 = bad usage.

What it runs
  1. tools/*_test.py (+ tools/launcher/*_test.py)  each with the repo's python, no arguments (their fixtures are hand-made unless the table
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

# python tests that need a third-party module: (module name) -> else SKIP with the pip line (2026-11-09: kl_release_test died with
# AttributeError 'NoneType'.ZstdCompressionParameters on a host without zstandard)
PY_NEEDS_MODULE = {
    'kl_release_test.py': 'zstandard',
}

# *_test.py files that are NOT self-tests (they drive the game): never run here
PY_NOT_TESTS = {
    'kl_solo_test.py': 'live two-seat bench driver (needs --hook and Dog Days)',
}

# python tests whose checks only hold as a non-root user: a read-only file (chmod) must make the write fail. root writes through it
# (cloud sandboxes run as root), so the rollback checks fail there for no fault of the tool -> SKIP, with the reason.
PY_NOT_ROOT = {
    'kl_gunpunch_test.py': 'write-error rollback checks use a read-only file; root writes through chmod',
}

# C tests: 'logic' builds with the shim on any host, 'win' needs the real SDK (includes a whole module).
C_TESTS = {
    'klcs_test.c': 'logic',            # klcopsquad_logic.h
    'klshield_test.c': 'logic',        # klshield_logic.h ([Shield] arithmetic + Online world gate, no windows.h)
    'klmodestab_test.c': 'logic',      # klmodestab_logic.h ([Keys] ModesTab rows + RoundHints text, no windows.h)
    'klcv_test.c': 'logic',            # klchar_voice.h
    'kldown_hold_test.c': 'logic',     # kldown_hold.h
    'klguard_test.c': 'logic',         # klguard_logic.h (OnlineGuardMode pure part)
    'klogrudge_test.c': 'logic',       # klogrudge_logic.h ([Bots] OnlineGrudge pure part)
    'klgetup_test.c': 'logic',         # klgetup_logic.h (+ kldown_hold.h)
    'klgetupbeacon_test.c': 'logic',   # klgetupbeacon.h (OnlineGetUpBeacon pure part)
    'klway_test.c': 'logic',           # klway_logic.h (OnlineWayPerMap / OnlineLegHopDy pure part)
    'klwaitvan_test.c': 'logic',       # klwaitvan_logic.h (OnlineLegWaitVan pure decision, no windows.h)
    'klshot2d_test.c': 'logic',        # klshot2d_logic.h (RemoteShot2DGate gate + slot-74 counter, no windows.h)
    'klboardpar_test.c': 'logic',      # klboardpar_logic.h (OnlineBoardAllNear pure decision, no windows.h)
    'klslot_rand_test.c': 'logic',     # klslot_rand_logic.h (random online map pick: mix, index, round advance, no windows.h)
    'klbrain_test.c': 'logic',         # klbrain_logic.h ([Brain] vector insertion order, growth, switches, PuppetOff window, no windows.h)
    'kldroptake_test.c': 'logic',      # kldroptake_logic.h (OnlineDropTake pure decision, no windows.h)
    'klcensus_test.c': 'logic',        # klcensus_logic.h (OnlineTriggersCensus new-cop pointer set, no windows.h)
    'klhpmax_test.c': 'logic',         # klhpmax_logic.h (one registry of every writer of an AI heister's maximum health: grudge + botfill + FedHealth compose, RV1A_DD05 350 -> 350000)
    'kldroptable_test.c': 'logic',     # kldroptable_logic.h (type-1 drop table eviction, no windows.h)
    'kldoorhold_test.c': 'logic',    # kldoorhold_logic.h (OnlineDoorHold pure decision, no windows.h)
    'kltimeauto_test.c': 'logic',     # kltimeauto_logic.h ([Lobby] TimeAuto clamp / when to apply, no windows.h)
    'klpagequeue_test.c': 'logic',    # klpagequeue_logic.h ([ShopPage] PageQueue hold, HintEveryShop re-arm, [HUD] ScoreboardNextHint text, no windows.h)
    'klstackdiag_test.c': 'logic',     # klstackdiag_logic.h (stack state log text + OnlineStackRecheck scan decision, no windows.h)
    'klstackhid_test.c': 'logic',      # klstackhid_logic.h ([BotFill] OnlineStackRecheckHid grace for state 0 + hidden 1 stacks, no windows.h)
    'klvantime_test.c': 'logic',      # klvantime_logic.h (OnlineVanAfterLegs / OnlineVanBoPos / OnlineVanFarHold pure part, no windows.h)
    'klassoft_test.c': 'logic',        # klassoft_logic.h (AssertSoft list parse, no windows.h)
    'klhud_boardbots_test.c': 'logic', # klhud_boardbots_logic.h ([HUD] OnlineBoardBots: AI heister rows of the online round-over card)
    'klperf_test.c': 'logic',          # klperf_logic.h ([Perf] OsdBackoff / OnlineCache / FastRead pure parts)
    'klhud_codeguard_test.c': 'logic', # klhud_codeguard_logic.h ([HUD] ProbeJmp: the code-bytes guard accepts a forwarding jmp)
    'klwlabel_test.c': 'logic',        # klwlabel_logic.h (wardrobe group tags, "n/N  GROUP > Name" labels, group jumps, no windows.h)
    'klfit_test.c': 'logic',          # klfit_logic.h ([Keys] CaptionTidy / CaptionMax / RowFit: caption + row fitting, no windows.h)
    'klshopui_test.c': 'logic',        # klshopui_logic.h ([ShopPage] TidyPage2 / [Hire] TidyPage: page II + hire page wording, widths, stars/lock rules)
    'klshopset_test.c': 'win',         # klshopset.h is pure, but the test reads a KLShopPage.ini with GetPrivateProfileInt/StringA (not in the shim)
    'klecho_test.c': 'logic',         # klecho_logic.h ([Echo] per room kind AL reverb parameter changes, no windows.h)
    'klechoprobe_test.c': 'logic',     # klechoprobe_logic.h ([Echo] Probe: which voices carry the aux send, names, summary, log budget)
    'klreverbbox_test.c': 'logic',     # klreverbbox_logic.h ([Echo] RoomBoxes table parse, oriented box, hysteresis, winner)
    'klcoverring_test.c': 'logic',     # klcoverring_logic.h ([CoverRing] schedule / change detection, no windows.h)
    'kldown_mirror_test.c': 'logic',   # kldown_mirror_logic.h (no windows.h at all)
    'klgrades_test.c': 'logic',        # klgrades.h (uses _snprintf: -D_snprintf=snprintf)
    'kllootsync_test.c': 'logic',      # kllootsync_logic.h
    'klbalonline_test.c': 'logic',     # klbalonline.h
    'klswappic_test.c': 'logic',       # klswappic.h ([Shop] OnlineSwapPic decision)
    'klpicown_test.c': 'logic',        # klpicown_logic.h ([Hire] BakedPics / [ShopPage] OwnPics decision)
    'klbottrait_test.c': 'logic',      # klbottrait.h
    'klshot_test.c': 'logic',          # klshot_logic.h (uses _snprintf: shim may need -D_snprintf=snprintf)
    'klleaf_test.c': 'logic',          # klleaf_logic.h (leaf probe schedule + CarStall door gate)
    'kldoorclose_test.c': 'logic',     # kldoorclose_logic.h (DoorCloseMs open detection, timer, busy postpone, stale give-up, slots)
    'klbotvoice_test.c': 'logic',      # klbotvoice_logic.h
    'klnamesprobe_test.c': 'logic',    # klnamesprobe_logic.h ([BotFill] OnlineNamesProbe digest / list / cadence)
    'klht_test.c': 'logic',            # klhud_tags_dist.h
    'klland_test.c': 'logic',          # klland_logic.h ([Join] Land= move timing + Land= range check)
    'klmenulook_test.c': 'logic',      # klmenulook_logic.h ([MenuLook] DeadMen: which menu files get their _deadmen sibling, no windows.h)
    'klcampui_test.c': 'logic',      # klcampui_logic.h ([CampaignUI] Menu: which patch archives get their _campui sibling, no windows.h)
    'klmappool_ov_test.c': 'logic',    # no windows.h
    'klhirepic_test.c': 'logic',       # no windows.h
    'klhirepick_test.c': 'logic',      # klhire_pick.h ([Hire] PickDefault)
    'klvanshield_test.c': 'logic',     # klvanshield_logic.h ([VanBlow] ShieldUntilBoarded / HealFloor / ShieldWhileWaiting)
    'klcrackfx_test.c': 'logic',       # klcrackfx_logic.h (lens crack heal fade + KL_CrackFX age)
    'klnc_test.c': 'logic',            # klnetchan_logic.h + klucc_logic.h
    'klonline_read_test.c': 'logic',   # klonline_read.h
    'klsteamside_test.c': 'logic',     # klsteamside.h ([Net] SideChannelSteam probe: version order, peer parse, log budget)
    'klsabot_test.c': 'logic',         # klsabotage_logic.h
    'klua_test.c': 'logic',            # no windows.h
    'klucchide_test.c': 'logic',       # klucchide_logic.h
    'klud_test.c': 'logic',            # klucc_down_logic.h
    # 2026-11-09 (scheduled check-in): the luvsic campaign merge + music / grenade / van-rest tests, all run here with gcc -m32 + ASan/UBSan clean
    'kladpcm_test.c': 'logic',         # kladpcm.h (Dead Men ADPCM .str decode vs a spec reference decoder; 615 checks)
    'klcampaign_test.c': 'logic',      # klcampaign_logic.h ([Campaign] Enable gate: scene key m<NN>[ab]\, idle on FA / Arcade / online)
    'klcamppick_test.c': 'logic',      # klcamppick_logic.h ([CampaignPick] in-menu campaign level list: page split, go window, one-shot start)
    'klcampgive_test.c': 'logic',      # klcampgive_logic.h ([CampGive] give / swap; includes windows.h via the shim)
    'klcampguard_test.c': 'logic',     # klcampguard_logic.h ([CampGuard] exact-site byte checks against kl2.exe 0490's measured bytes)
    'klcamprappel_test.c': 'logic',    # klcamprappel_logic.h (campaign rappel guards, missing-clip refusal)
    'klcamprevive_test.c': 'logic',    # klcamprevive_logic.h (wounded-merc watch, observation only)
    'klcampsquad_test.c': 'logic',     # klcampsquad_logic.h ([CampSquad] crew orders, pure numbers; includes windows.h via the shim)
    'klcmpcore_test.c': 'logic',       # klcmpcore_logic.h (campaign core: scene-id routing, save redirect, progress ini)
    'klgrenade_test.c': 'logic',       # klgrenade_logic.h ([Grenade] Release decision)
    'kllevelmusic_test.c': 'logic',    # kllevelmusic_logic.h ([LevelMusic] Restart: round 2+ music replay decision)
    'klvanrest_test.c': 'logic',       # klvanrest_logic.h ([BotFill] OnlineVanRest rest-position guard)
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

# C tests that are not self-tests: they need audio files (mp3 args) the runner does not have. Always SKIP, with the reason.
C_MANUAL = {
    'klambience_test.c': 'manual: needs bed.mp3 shot.mp3 arguments (real audio files)',
    'klmciwrap_test.c': 'manual: needs a long.mp3 argument (real audio file)',
    'klmusic_test.c': 'manual: needs a.mp3 b.mp3 stinger.mp3 arguments (real audio files)',
    'klstinger_test.c': 'manual: needs short.mp3 [long.mp3] arguments (real audio files)',
}

# extra link options per test (the test's own header says how it is meant to be built)
C_LINK = {
    'klhigh_test.c': '/link /LARGEADDRESSAWARE',      # header: cl ... klhigh_test.c /Fe:klhigh_test.exe /link /LARGEADDRESSAWARE
}

# tests that include a file generated from a module (header: sed -n '/bit maps/,/who called/p' klhigh.c | sed '$d' > bits.inc)
C_GENERATED = {
    'klhigh_bits_test.c': ('bits.inc', 'klhigh.c', r'^/\* -+ bit maps \*/', r'^/\* -+ who called \*/'),
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
    # tools/*_test.py plus the launcher's own test (tools/launcher/*_test.py, 2026-11-09: tester distribution scripts)
    for path in sorted(glob.glob(os.path.join(HERE, '*_test.py')) + glob.glob(os.path.join(HERE, 'launcher', '*_test.py'))):
        name = os.path.basename(path)
        if name == os.path.basename(__file__) or (only and name not in only and name[:-3] not in only):
            continue
        if name in PY_NOT_TESTS:
            yield Result(name, 'SKIP', 'not a self-test: ' + PY_NOT_TESTS[name])
            continue
        if name in PY_NOT_ROOT and hasattr(os, 'geteuid') and os.geteuid() == 0:
            yield Result(name, 'SKIP', 'running as root: ' + PY_NOT_ROOT[name])
            continue
        missing = [f for f in PY_NEEDS.get(name, []) if not os.path.exists(f)]
        if missing:
            yield Result(name, 'SKIP', 'needs ' + os.path.basename(missing[0]) + ' (game file, not here)')
            continue
        mod = PY_NEEDS_MODULE.get(name)
        if mod and run([sys.executable, '-c', 'import ' + mod], HERE)[0] != 0:
            yield Result(name, 'SKIP', 'needs the python module %s (pip install %s)' % (mod, mod))
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
                f.write('#include <stdio.h>'+chr(10)+'int main(void){return sizeof(long)==4?0:1;}'+chr(10))
            rc, _ = run(['gcc', '-m32', '-o', os.path.join(d, 'a'), src], d)
            _gcc32 = rc == 0 and run([os.path.join(d, 'a')], d)[0] == 0
            shutil.rmtree(d, ignore_errors=True)
    return _gcc32


def gen_include(name, outdir):
    """write the generated include of a C_GENERATED test into outdir: the module's lines from the start marker up to (not
    including) the end marker, like the sed in the test header. Returns an error text, '' when fine."""
    import re
    inc, mod, start, end = C_GENERATED[name]
    lines = open(os.path.join(KLHOOK, mod), encoding='utf-8', errors='replace').read().splitlines()
    a = next((i for i, l in enumerate(lines) if re.match(start, l)), None)
    b = next((i for i, l in enumerate(lines) if a is not None and i > a and re.match(end, l)), None)
    if a is None or b is None:
        return 'markers not found in ' + mod
    with open(os.path.join(outdir, inc), 'w') as f:
        f.write(chr(10).join(lines[a:b]) + chr(10))
    return ''


def build_c(name, outdir):
    """returns (rc, output, exe)"""
    src = os.path.join(KLHOOK, name)
    exe = os.path.join(outdir, name[:-2] + ('.exe' if WIN else ''))
    inc = ''
    if name in C_GENERATED:
        err = gen_include(name, outdir)
        if err:
            return 1, err, exe
        inc = ' /I"%s"' % outdir if WIN else ''
    if WIN:
        cl = 'cl /nologo /W3 /D_CRT_SECURE_NO_WARNINGS%s "%s" /Fe:"%s" %s' % (inc, src, exe, C_LINK.get(name, ''))
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
        if name in C_MANUAL:
            yield Result(name, 'SKIP', C_MANUAL[name])
            continue
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
