"""Unattended Dead Men level-chain test (campaigns design 3.1, test step 1).
Needs ANP_Loader with campaign.inc (ANP_endlevel.txt / ANP_load.txt) and ANP_autoload.txt = '<first id> 1 12'.
Launches DD via Steam, waits for the first level, then for every level: Enter for 'Buffering 100%', one screenshot,
ANP_endlevel.txt = the expected next target (fires the scene's real ZSceneChanger, slot 34), and checks that
ANP_log.txt opens exactly the next scene of the chain:
  M01 M02 M03 M03B M05 M06 M07 M07F M08 M09 M09B M11 M11B M12 M13 M13B -(M14 exit)-> M14 -> front end.
M07F = the funeral (Scenes/CutScenes/M07/M07_A_Funeral.zip, built by port_level.py M07F / build_all.ps1 and installed
with M07; campaign.inc knows the id for ANP_load.txt). It is a cutscene scene that may end into M08 by itself while it
settles: a next scene that opens before ANP_endlevel.txt is written counts as a pass ('advanced by itself').
The next scene of a link is always the first different scene opened after the current scene's own open line in
ANP_log.txt (not after a mark taken later), so an advance that lands before the script's next step is still seen.
If a level end does not lead to the expected scene, the link is marked FAIL and the next level is loaded with
ANP_load.txt so the rest of the chain is still tested. Frames + log + result.json go to work/smoke/chain_<run>/.
Rules (as smoke_m01): refuses to start if kl2.exe runs; always removes ANP_quit.txt; taskkill only as a last resort.
usage: smoke_chain.py [first_id=M01] [settle_seconds=10]"""
import ctypes, ctypes.wintypes as wt, os, sys, time, subprocess, glob, re, json
DD = r'C:\Program Files (x86)\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = time.strftime('%m%d_%H%M%S'); OUT = os.path.join(REPO, 'work', 'smoke', 'chain_' + RUN); os.makedirs(OUT, exist_ok=True)
FF = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))[0]
LOG = os.path.join(DD, 'ANP_log.txt'); QUIT = os.path.join(DD, 'ANP_quit.txt')
ENDF = os.path.join(DD, 'ANP_endlevel.txt'); LOADF = os.path.join(DD, 'ANP_load.txt')
CHAIN = ['M01', 'M02', 'M03', 'M03B', 'M05', 'M06', 'M07', 'M07F', 'M08', 'M09', 'M09B', 'M11', 'M11B', 'M12', 'M13', 'M13B', 'M14', 'FRONTEND']
first = sys.argv[1] if len(sys.argv) > 1 else 'M01'
settle = float(sys.argv[2]) if len(sys.argv) > 2 else 10
u = ctypes.windll.user32; k32 = ctypes.windll.kernel32; u.SetProcessDPIAware()
t0 = time.time()
def say(s):
    line = '%7.1fs %s' % (time.time() - t0, s); print(line, flush=True)
    open(os.path.join(OUT, 'steps.txt'), 'a').write(line + '\n')
def running(exe='kl2.exe'):
    return exe in subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ' + exe, '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout.lower()
def kl2_hwnd():
    found = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
    def cb(h, _):
        pid = wt.DWORD(); u.GetWindowThreadProcessId(h, ctypes.byref(pid))
        if u.IsWindowVisible(h):
            hp = k32.OpenProcess(0x1000, False, pid.value)
            if hp:
                b = ctypes.create_unicode_buffer(260); n = wt.DWORD(260)
                k32.QueryFullProcessImageNameW(hp, 0, b, ctypes.byref(n)); k32.CloseHandle(hp)
                if os.path.basename(b.value).lower() == 'kl2.exe': found.append(h)
        return True
    u.EnumWindows(cb, 0); return found[0] if found else None
def key_enter(hold=0.08):
    u.keybd_event(0, 0x1C, 0x0008, 0); time.sleep(hold); u.keybd_event(0, 0x1C, 0x0008 | 0x0002, 0)
def front():
    h = kl2_hwnd()
    if h and u.GetForegroundWindow() != h:
        u.keybd_event(0x12, 0, 0, 0); u.SetForegroundWindow(h); u.keybd_event(0x12, 0, 2, 0); time.sleep(0.3)
    return h and u.GetForegroundWindow() == h
def shot(name):
    h = kl2_hwnd()
    if not h: return None
    r = wt.RECT(); u.GetWindowRect(h, ctypes.byref(r))
    x, y = max(r.left, 0), max(r.top, 0); w, hh = r.right - x, r.bottom - y
    if w < 320 or hh < 200: return None
    fn = os.path.join(OUT, name)
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'gdigrab', '-offset_x', str(x), '-offset_y', str(y),
                    '-video_size', '%dx%d' % (w - w % 2, hh - hh % 2), '-i', 'desktop', '-frames:v', '1', '-vf', 'scale=640:-2',
                    '-q:v', '5', fn], capture_output=True, timeout=20)
    return fn if os.path.exists(fn) else None
def newlog():
    try:
        d = open(LOG, 'rb').read()
        # the loader starts a fresh log at every launch: if the first bytes changed, the whole file is new
        fresh = len(d) < log0 or d[:len(head0)] != head0
        return d.decode('latin1', 'replace') if fresh else d[log0:].decode('latin1', 'replace')
    except OSError: return ''
SCENE_RE = re.compile(r'open SCENES[\\/](?:Locations[\\/](\w+)[\\/]\1_Main\.zip|(KaneAndLynch)\.zip'
                      r'|(CutScenes[\\/]M07[\\/]M07_A_Funeral)\.zip) ok', re.I)
def scene_id(m):
    return (m.group(1) or ('M07F' if m.group(3) else 'FRONTEND')).upper()
def scene_opens(text):
    """distinct scene opens in order (consecutive repeats of the same scene collapsed)"""
    seq = []
    for m in SCENE_RE.finditer(text):
        s = scene_id(m)
        if not seq or seq[-1] != s: seq.append(s)
    return seq
def own_open_end(text, sid, start=0):
    """log position just after the first open line of scene sid at or after start (None if there is none)"""
    for m in SCENE_RE.finditer(text, start):
        if scene_id(m) == sid: return m.end()
    return None
def first_other_open(text, cur, start):
    """(scene, start, end) of the first open of a scene other than cur at or after start (None if there is none)"""
    for m in SCENE_RE.finditer(text, start):
        s = scene_id(m)
        if s != cur: return s, m.start(), m.end()
    return None
def wait_for(pred, timeout, step=1.0):
    end = time.time() + timeout
    while time.time() < end:
        v = pred()
        if v: return v
        if not running(): return None
        time.sleep(step)
    return pred()
def target_of(nxt):
    if nxt == 'M07F': return 'CutScenes/M07/M07_A_Funeral'
    return 'KaneAndLynch' if nxt == 'FRONTEND' else 'Locations/%s/%s_Main' % (nxt, nxt)
def settle_level(lid):
    """the level file is open: wait, Enter through 'Buffering 100%', settle, screenshot"""
    time.sleep(8)
    for _ in range(3):
        if not running(): return
        front(); key_enter(); time.sleep(3)
    time.sleep(settle)
    f = shot('%02d_%s.jpg' % (CHAIN.index(lid) if lid in CHAIN else 99, lid))
    say('%s: screenshot %s' % (lid, os.path.basename(f) if f else 'FAILED'))

if running('kl2.exe'): print('kl2.exe already running - W may be playing; not touching anything'); sys.exit(2)
for f in (QUIT, ENDF, LOADF):
    if os.path.exists(f): os.remove(f)
log0 = os.path.getsize(LOG) if os.path.exists(LOG) else 0
head0 = open(LOG, 'rb').read(256) if log0 else b''
results = []
try:
    say('launching steam://rungameid/28000'); os.startfile('steam://rungameid/28000')
    for _ in range(90):
        if running(): break
        time.sleep(1)
    else:
        say('kl2.exe did not start within 90 s (Steam sign-in window?)'); sys.exit(3)
    say('kl2.exe running')
    if not wait_for(lambda: first in scene_opens(newlog()), 150):
        say('first level %s never opened' % first); raise SystemExit(4)
    say('%s opened' % first)
    cur = first
    # cur_pos = log position just after the current scene's own open line. The next scene is the first different scene
    # opened after it, wherever that open lands relative to the script's own steps (a scene that runs into the next
    # one by itself, e.g. the funeral into M08, can open it before this loop takes any later mark)
    cur_pos = own_open_end(newlog(), first, 0) or 0
    i = CHAIN.index(first)
    while i + 1 < len(CHAIN) and running():
        nxt = CHAIN[i + 1]
        settle_level(cur)
        if not running(): say('kl2.exe gone in %s' % cur); break
        nxt_end = None
        early = first_other_open(newlog(), cur, cur_pos)
        if early:
            got, _, nxt_end = early; tail = newlog()[cur_pos:]; fired = ['(advanced by itself, no ANP_endlevel.txt)']
            say('%s: next scene opened by itself while settling: %s' % (cur, got))
        else:
            mark = len(newlog())
            open(ENDF, 'w').write(target_of(nxt)); say('%s: ANP_endlevel.txt = %s' % (cur, target_of(nxt)))
            def after():
                t = newlog()
                hit = first_other_open(t, cur, cur_pos)
                if hit: return hit
                if 'not firing' in t[mark:]: return 'notfired'
                return None
            res = wait_for(after, 90)
            tail = newlog()[mark:]
            fired = [l for l in tail.splitlines() if 'endlevel:' in l]
            if isinstance(res, tuple):
                got, at, nxt_end = res
                if at < mark:
                    fired.insert(0, '(advanced by itself before ANP_endlevel.txt was written)')
                    tail = newlog()[cur_pos:]
            else:
                got = res
        rec = dict(level=cur, expected=nxt, opened=got, ok=(got == nxt), endlevel_log=fired[:12],
                   exceptions=[l for l in tail.splitlines() if 'EXCEPTION' in l][:5])
        results.append(rec)
        say('%s -> %s: %s (opened %s)' % (cur, nxt, 'PASS' if rec['ok'] else 'FAIL', got))
        if not running(): break
        if not rec['ok']:
            if nxt == 'FRONTEND': break
            mark = len(newlog())
            open(LOADF, 'w').write('%s 1' % nxt); say('fallback: ANP_load.txt = %s' % nxt)
            nxt_end = wait_for(lambda: own_open_end(newlog(), nxt, mark), 90)
            if not nxt_end: say('fallback load of %s failed' % nxt); break
        cur = nxt; cur_pos = nxt_end; i += 1
    if running() and results and results[-1]['expected'] == 'FRONTEND' and results[-1]['ok']:
        time.sleep(12); front(); f = shot('99_frontend.jpg'); say('front end screenshot %s' % (os.path.basename(f) if f else 'FAILED'))
finally:
    if running():
        open(QUIT, 'w').write('quit'); say('ANP_quit.txt written')
        for _ in range(30):
            if not running(): break
            time.sleep(1)
        if running(): say('still running after 30 s: taskkill'); subprocess.run(['taskkill', '/IM', 'kl2.exe', '/F'], capture_output=True)
    time.sleep(2)
    for f in (QUIT, ENDF, LOADF):
        if os.path.exists(f): os.remove(f); say('%s removed' % os.path.basename(f))
    lg = newlog(); open(os.path.join(OUT, 'log.txt'), 'w', encoding='utf-8').write(lg)
    seq = scene_opens(lg)
    npass = sum(1 for r in results if r['ok'])
    summary = dict(run=RUN, scene_order=seq, links=len(results), passed=npass,
                   chain_ok=(npass == len(CHAIN) - 1 - CHAIN.index(first)), results=results)
    json.dump(summary, open(os.path.join(OUT, 'result.json'), 'w'), indent=1)
    say('scene order: %s' % ' -> '.join(seq))
    say('links passed %d / %d (expected %d) -> %s' % (npass, len(results), len(CHAIN) - 1 - CHAIN.index(first),
                                                     'CHAIN OK' if summary['chain_ok'] else 'CHAIN INCOMPLETE'))
    say('done -> %s' % OUT)
