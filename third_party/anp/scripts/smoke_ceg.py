"""CEG check for ANP_Loader: does the loader leave every Valve-CEG-hashed byte of kl2.exe alone?

kl2.exe hashes ~85% of .text and 66% of .rdata (ranges: work/ext/kl-merge/klhook/klranges.h, JC's re/antitamper.md).
In a REAL session (Arcade / Fragile Alliance started from the menu) a changed hashed byte ends the game with
ExitProcess(0x8000dead) about 30 ms after the level loads. Since 11 Oct the loader's default build changes no code
byte (VEH guards / watchdog / offline data instead of the six old patches); the old patches only come back with
legacy switches in <DD>/ANP_guards.txt.

Two parts:
 1. M01 run (default): installs the loader under test for the run (default work/out_ceg/ANP_Loader.asi; the installed
    one is moved aside and put back), autoloads M01, stays --secs seconds, then
      - reads kl2's image from the running process (ReadProcessMemory, read-only) and compares every hashed range with
        the on-disk kl2.exe (part 2 below, done while the level runs),
      - checks the log: the loader's "CEG:" start-up lines, the guard lines (the VEH guards should fire where the old
        patches did: M01 = CListUser bad buckets), ExitProcess / EXCEPTION lines, the last stats line,
    quits through ANP_quit.txt and writes work/smoke/ceg_<run>/report.txt (+ log.txt).
 2. --attach: the same memory comparison against a kl2.exe that is ALREADY running (read-only; no input, no files
    written to the game folder, nothing launched or quit). Use it for a stock Arcade / FA session that W starts by
    hand: that may be a real online session on W's Steam account, so it is never started by a script.

Differences that are not ANP's (KL2Fix.asi, overlays) are reported too: any hashed difference trips the CEG check,
whoever made it.

usage:
  py scripts\\smoke_ceg.py [--asi PATH | --installed] [--level M01] [--secs 60] [--guards "cl=veh snd=veh"]
  py scripts\\smoke_ceg.py --attach
  py scripts\\smoke_ceg.py --static-only        (no game: check the build's strings / the exe and ranges files only)
"""
import argparse, ctypes, ctypes.wintypes as wt, os, re, shutil, struct, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kltest
import anp_paths

DD = kltest.DD
EXE = os.path.join(DD, 'kl2.exe')
RANGES_H = os.path.join(anp_paths.KLMERGE, 'klhook', 'klranges.h')
DEFAULT_ASI = os.path.join(anp_paths.WORK, 'out_ceg', 'ANP_Loader.asi')
IMAGE_BASE = 0x400000

# the old ANP code-patch sites (for attribution of differences)
ANP_SITES = {0x4f8a60: (8, 'CListUser guard (legacy)'), 0x71166d: (5, 'fx lookup/alias (legacy)'),
             0x51f1a5: (5, 'gfx guard (legacy)'), 0x8a40fe: (8, 'wrap guard (legacy)'),
             0x927b44: (8, 'coll guard (legacy)'), 0x446673: (6, 'snd guard (legacy)'),
             0x6d100f: (6, 'scene resolver (LegacyResolver=1)'), 0x4944f2: (5, 'xg watch (diagnostic)')}

k32 = ctypes.WinDLL('kernel32', use_last_error=True)
k32.OpenProcess.restype = wt.HANDLE
k32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
k32.ReadProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
k32.GetExitCodeProcess.argtypes = [wt.HANDLE, ctypes.POINTER(wt.DWORD)]
k32.CloseHandle.argtypes = [wt.HANDLE]
PROCESS_VM_READ, PROCESS_QUERY_LIMITED_INFORMATION, SYNCHRONIZE = 0x0010, 0x1000, 0x00100000


# ------------------------------------------------------------------------------------------------ static inputs
def load_ranges(path=RANGES_H):
    txt = open(path, encoding='utf-8', errors='replace').read()
    rng = [(int(a, 16), int(b, 16)) for a, b in re.findall(r'\{\s*0x([0-9a-fA-F]+),\s*0x([0-9a-fA-F]+)\s*\}', txt)]
    m = re.search(r'#define\s+KLH_NHASHED\s+(\d+)', txt)
    if m and int(m.group(1)) != len(rng): raise SystemExit('klranges.h: %d ranges parsed, header says %s' % (len(rng), m.group(1)))
    return rng


class DiskImage:
    """kl2.exe as the Windows loader maps it (fixed base 0x400000, no relocations)"""
    def __init__(self, path=EXE):
        self.d = open(path, 'rb').read()
        d = self.d; pe = struct.unpack_from('<I', d, 0x3c)[0]
        if d[:2] != b'MZ' or d[pe:pe + 4] != b'PE\0\0': raise SystemExit('%s: not a PE file' % path)
        nsec, = struct.unpack_from('<H', d, pe + 6); optsz, = struct.unpack_from('<H', d, pe + 20)
        self.timestamp, = struct.unpack_from('<I', d, pe + 8)
        self.base, = struct.unpack_from('<I', d, pe + 24 + 28)
        nrel = struct.unpack_from('<II', d, pe + 24 + 96 + 5 * 8)[1]
        if self.base != IMAGE_BASE or nrel: raise SystemExit('kl2.exe: base %#x relocs %d - this script assumes 0x400000 / none' % (self.base, nrel))
        self.secs = []
        s = pe + 24 + optsz
        for i in range(nsec):
            name = d[s:s + 8].rstrip(b'\0').decode('latin1')
            vsize, va, rawsz, rawptr = struct.unpack_from('<IIII', d, s + 8)
            chars, = struct.unpack_from('<I', d, s + 36)
            self.secs.append((name, self.base + va, vsize, rawptr, rawsz, chars)); s += 40

    def section(self, va):
        for sec in self.secs:
            if sec[1] <= va < sec[1] + max(sec[2], sec[4]): return sec
        return None

    def read(self, va, n):
        out = bytearray(n)
        if va < self.secs[0][1]:                                # PE headers (mapped from file offset 0)
            off = va - self.base; take = max(0, min(n, self.secs[0][1] - va, len(self.d) - off))
            out[:take] = self.d[off:off + take]
            return bytes(out)
        sec = self.section(va)
        if not sec: return bytes(out)
        name, sva, vsize, rawptr, rawsz, chars = sec
        off = va - sva; take = max(0, min(n, rawsz - off))
        out[:take] = self.d[rawptr + off: rawptr + off + take]
        return bytes(out)


class Proc:
    def __init__(self, pid):
        self.pid = pid
        self.h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid)
        if not self.h: raise SystemExit('OpenProcess(%d) failed: %d' % (pid, ctypes.get_last_error()))

    def read(self, va, n):
        """bytes, or None for pages that can't be read"""
        buf = ctypes.create_string_buffer(n); got = ctypes.c_size_t(0)
        if k32.ReadProcessMemory(self.h, ctypes.c_void_p(va), buf, n, ctypes.byref(got)) and got.value == n:
            return buf.raw
        return None

    def exit_code(self):
        c = wt.DWORD(0)
        return c.value if k32.GetExitCodeProcess(self.h, ctypes.byref(c)) else None

    def close(self):
        if self.h: k32.CloseHandle(self.h); self.h = None


def kl2_pid():
    import subprocess
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    for line in out.splitlines():
        f = [x.strip('"') for x in line.split('","')]
        if len(f) > 1 and f[0].strip('"').lower() == 'kl2.exe': return int(f[1])
    return None


# ------------------------------------------------------------------------------------------------ the comparison
def diff_runs(va, a, b, gap=8):
    runs = []; i = 0; n = len(a)
    while i < n:
        if a[i] == b[i]: i += 1; continue
        j = i; last = i
        while j < n and j - last <= gap:
            if a[j] != b[j]: last = j
            j += 1
        runs.append((va + i, last - i + 1)); i = last + 1
    return runs


def attribute(addr, n, anp_writes):
    for at, (ln, what) in list(anp_writes.items()) + list(ANP_SITES.items()):
        if addr < at + ln and at < addr + n: return 'ANP: ' + what
    return 'NOT ANP (KL2Fix.asi? overlay? another mod?)'


def compare(proc, disk, ranges, anp_writes=None, say=print):
    """every hashed range + the rest of .text (informational). Returns (report lines, hashed diff count, unread)"""
    anp_writes = anp_writes or {}
    lines = []; hashed_diffs = []; other_diffs = []; unread = 0; total = 0
    hdr_mem = proc.read(IMAGE_BASE, 0x400); hdr_disk = disk.d[:0x400]
    if not hdr_mem: raise SystemExit('cannot read kl2 image header at 0x400000')
    pe = struct.unpack_from('<I', hdr_mem, 0x3c)[0]
    ts_mem = struct.unpack_from('<I', hdr_mem, pe + 8)[0]
    lines.append('image: header TimeDateStamp mem %#x disk %#x %s' % (ts_mem, disk.timestamp, 'ok' if ts_mem == disk.timestamp else 'MISMATCH (other exe?)'))

    def scan(s, e, into):
        nonlocal unread, total
        va = s
        while va < e:
            n = min(0x10000, e - va)
            m = proc.read(va, n)
            if m is None:                                      # page by page
                for p in range(va, va + n, 0x1000):
                    q = min(0x1000 - (p & 0xfff), va + n - p)
                    mm = proc.read(p, q)
                    if mm is None: unread += q; continue
                    total += q; into += diff_runs(p, disk.read(p, q), mm)
            else:
                total += n; into += diff_runs(va, disk.read(va, n), m)
            va += n

    for s, e in ranges: scan(s, e, hashed_diffs)
    hashed_total = total; hashed_unread = unread
    text = [x for x in disk.secs if x[0] == '.text'][0]
    t0, t1 = text[1], text[1] + text[2]
    cur = t0
    for s, e in ranges + [(t1, t1)]:                            # .text pages outside the hashed ranges
        s2, e2 = max(cur, t0), min(s, t1)
        if s2 < e2: scan(s2, e2, other_diffs)
        cur = max(cur, e)
    lines.append('compared %d hashed bytes in %d ranges (%d unreadable), %d unhashed .text bytes' %
                 (hashed_total, len(ranges), hashed_unread, total - hashed_total))

    def show(tag, runs):
        for addr, n in runs[:60]:
            sec = disk.section(addr); secname = sec[0] if sec else '?'
            note = ''
            if sec and addr >= sec[1] + sec[2]: note = ' (beyond VirtualSize: loader mapping, ignore)'
            dm = disk.read(addr, min(n, 16)); mm = proc.read(addr, min(n, 16)) or b''
            lines.append('  %s %08x+%-4d %-7s disk %-32s mem %-32s %s%s' % (tag, addr, n, secname, dm.hex(), mm.hex(),
                                                                       attribute(addr, n, anp_writes), note))
        if len(runs) > 60: lines.append('  ... %d more' % (len(runs) - 60))

    real = [r for r in hashed_diffs if not (disk.section(r[0]) and r[0] >= disk.section(r[0])[1] + disk.section(r[0])[2])]
    lines.append('HASHED differences: %d run(s), %d byte(s)%s' % (len(real), sum(n for _, n in real),
                 '  <<< a REAL Arcade/FA session would end with ExitProcess(0x8000dead)' if real else '  (CEG-safe)'))
    show('HASHED', hashed_diffs)
    lines.append('unhashed .text differences (not checked by CEG, informational): %d run(s)' % len(other_diffs))
    show('other ', other_diffs)
    return lines, len(real), hashed_unread


def anp_writes_from_log(text):
    """the loader's own list: 'CEG: kl2.exe code bytes changed by ANP_Loader: N patch(es): 004f8a60+8 [..] ...'"""
    w = {}
    for m in re.finditer(r'CEG: kl2\.exe code bytes changed by ANP_Loader: \d+ patch\(es\):(.*)', text):
        for a, n, what in re.findall(r'([0-9a-f]{8})\+(\d+) \[([^\]]*)\]', m.group(1)):
            w[int(a, 16)] = (int(n), what)
    return w


# ------------------------------------------------------------------------------------------------ log checks
GUARD_PATS = [
    ('CEG start-up line', r'CEG: kl2\.exe code bytes changed by ANP_Loader: .*'),
    ('CEG stock-bytes line', r'CEG: old patch sites with stock bytes .*'),
    ('guards config', r'guards \((?:ANP_guards\.txt|defaults)\): .*'),
    ('legacy patch installed', r'.*LEGACY code patch at .*'),
    ('CListUser (veh)', r'CListUser guard \(veh\).*'),
    ('CListUser (legacy)', r'CListUser guard: bad bucket.*'),
    ('snd (veh)', r'snd guard \(veh\).*'),
    ('gfx (template missing)', r'ZGraphic template missing.*'),
    ('coll', r'coll guard.*: handle.*'),
    ('wrap watch / rescue', r'wrap (?:watch|rescue):.*'),
    ('FXMISS (legacy fx only)', r'FXMISS .*'),
    ('div guard (generic)', r'div-by-zero guard at.*'),
    ('ExitProcess', r'ExitProcess\(0x.*'),
    ('EXCEPTION', r'EXCEPTION [0-9a-f]{8} at .*'),
]


def log_report(text):
    out = []
    for tag, pat in GUARD_PATS:
        hits = re.findall(pat, text)
        out.append('  %-26s %4d%s' % (tag, len(hits), ('   e.g. ' + hits[0][:150]) if hits else ''))
    stats = re.findall(r'snd: .*\| guards (.*?) \| mem.*', text)
    out.append('  last stats guards: %s' % (stats[-1] if stats else '(no stats line)'))
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--asi', default=DEFAULT_ASI, help='loader build to test (installed for the run, then put back)')
    ap.add_argument('--installed', action='store_true', help='test the ANP_Loader.asi that is installed now')
    ap.add_argument('--level', default='M01'); ap.add_argument('--secs', type=float, default=60)
    ap.add_argument('--guards', default=None, help='ANP_guards.txt text for the run (default: none = loader defaults)')
    ap.add_argument('--attach', action='store_true', help='read-only memory check of an already running kl2.exe')
    ap.add_argument('--static-only', action='store_true')
    a = ap.parse_args()

    ranges = load_ranges(); disk = DiskImage()
    print('kl2.exe %s TimeDateStamp %#x, %d hashed ranges (%d bytes) from %s' % (EXE, disk.timestamp, len(ranges),
          sum(e - s for s, e in ranges), RANGES_H))
    if disk.timestamp != 0x4c80f728: print('WARNING: klranges.h was generated for TimeDateStamp 0x4c80f728')
    for at, (n, what) in sorted(ANP_SITES.items()):
        h = any(s < at + n and at < e for s, e in ranges)
        print('  old ANP site %08x+%d %-36s %s' % (at, n, what, 'HASHED' if h else 'not hashed'))
    if a.static_only: return 0

    if a.attach:
        pid = kl2_pid()
        if not pid: raise SystemExit('kl2.exe is not running')
        p = Proc(pid)
        text = ''
        try: text = open(kltest.LOG, 'rb').read().decode('latin1', 'replace')
        except OSError: pass
        lines, nh, unread = compare(p, disk, ranges, anp_writes_from_log(text))
        p.close()
        out = ['attach: kl2.exe pid %d (read-only)' % pid] + lines + ['log (%s):' % kltest.LOG] + log_report(text)
        print('\n'.join(out))
        return 1 if nh or unread else 0

    r = kltest.Run('ceg')
    report = []
    guards_path = os.path.join(DD, 'ANP_guards.txt'); auto = os.path.join(DD, 'ANP_autoload.txt')
    old_auto = open(auto).read() if os.path.exists(auto) else None
    launched = wrote_auto = installed = False; proc = None; nh = -1; unread = -1
    try:
        bad = kltest.preflight(r, need_menu=False)
        if bad: raise SystemExit('; '.join(bad))
        if not r.take_lock(): raise SystemExit('GAME_LOCK busy')
        if r.running(): raise SystemExit('kl2.exe started by someone else while taking the lock')
        r.clear_hooks()
        if not a.installed:
            if not os.path.exists(a.asi): raise SystemExit('no loader build at %s (run loader\\build.bat ..\\work\\out_ceg)' % a.asi)
            r.move_aside('ANP_Loader.asi'); shutil.copy2(a.asi, os.path.join(DD, 'ANP_Loader.asi')); installed = True
            r.say('installed %s (sha1 %s)' % (a.asi, kltest.sha1(a.asi)))
        r.move_aside('ANP_guards.txt')
        if a.guards: r.hook('ANP_guards.txt', a.guards)
        open(auto, 'w').write('%s 1 12' % a.level); wrote_auto = True
        launched = r.launch()
        if not launched: raise SystemExit(3)
        pid = kl2_pid(); proc = Proc(pid) if pid else None
        if not r.wait_log(r'autoload: load request issued', 120): raise SystemExit('no autoload (see log)')
        t0 = time.time(); r.say('load requested')
        pressed = 0
        while time.time() - t0 < a.secs and r.running():
            if pressed < 3 and time.time() - t0 > 14 + pressed * 4: r.key('enter', gap=0); pressed += 1
            r.touch_lock(); time.sleep(1)
        if r.running() and proc:
            r.say('comparing kl2 image in memory with kl2.exe on disk (read-only)')
            lines, nh, unread = compare(proc, disk, ranges, anp_writes_from_log(r.log()), r.say)
            report += ['memory check after %.0f s in %s:' % (time.time() - t0, a.level)] + lines
        else:
            report.append('kl2.exe is gone before the memory check')
    finally:
        if launched: r.quit()
        code = proc.exit_code() if proc else None
        if proc: proc.close()
        if wrote_auto:
            if old_auto is not None: open(auto, 'w').write(old_auto)
            else:
                try: os.remove(auto)
                except OSError: pass
        gp = os.path.join(DD, 'ANP_guards.txt')
        if a.guards and os.path.exists(gp): os.remove(gp)
        r.restore_moved()                                       # ANP_Loader.asi + ANP_guards.txt back
        text = r.save_log() if launched else ''
        r.release_lock()
    report.append('process exit code: %s%s' % ('%#x' % code if code is not None else '?',
                  '  <<< 0x8000dead = CEG kill' if code == 0x8000dead else ''))
    report.append('log checks (%s):' % os.path.join(r.out, 'log.txt'))
    report += log_report(text)
    ok_start = re.search(r'CEG: kl2\.exe code bytes changed by ANP_Loader: none', text)
    cl_fired = re.search(r'CListUser guard \(veh\)', text) or re.search(r'CListUser guard: bad bucket', text)
    report.append('VERDICT: loader start-up line %s | hashed diffs %s (unreadable hashed bytes %s) | CListUser guard %s (old patch fired in every M01 run)' % (
        'none (ok)' if ok_start else 'NOT "none"', nh if nh >= 0 else '?', unread if unread >= 0 else '?', 'fired' if cl_fired else 'did not fire'))
    open(os.path.join(r.out, 'report.txt'), 'w', encoding='utf-8').write('\n'.join(report) + '\n')
    print('\n'.join(report)); print('report:', os.path.join(r.out, 'report.txt'))
    return 0 if ok_start and nh == 0 and unread == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
