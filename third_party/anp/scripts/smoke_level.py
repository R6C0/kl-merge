"""Unattended level look-test: autoload a level, in-game (D3D) screenshots through the opening (cutscenes), then aim
(hold right mouse) and fire (left clicks) with screenshots (muzzle flash, gun hold), then quit.
Uses kltest (GAME_LOCK, launch, log) and the loader's ANP_shot.txt back-buffer capture (works with the screen off).
usage: smoke_level.py [level=M01] [opening_s=120] [shot_every=2.0]"""
import os, re, sys, time, glob, subprocess, ctypes
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kltest
LEVEL = sys.argv[1] if len(sys.argv) > 1 else 'M01'
OPEN_S = float(sys.argv[2]) if len(sys.argv) > 2 else 120
EVERY = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
ENTERS = int(os.environ.get('SMOKE_ENTERS', '4'))     # Enter presses for 'Buffering 100%' (default 4, as before)
DD = kltest.DD
u = ctypes.windll.user32
FF = glob.glob(os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg*\*\bin\ffmpeg.exe'))[0]
r = kltest.Run('level_%s' % LEVEL)
n = [0]
def shot(tag):
    sq = os.path.join(DD, 'ANP_shot.txt')
    if os.path.exists(sq): return
    name = 'anplvl_%s_%03d_%s.bmp' % (r.id, n[0], tag); n[0] += 1
    open(sq, 'w').write(name)
def collect():
    for b in glob.glob(os.path.join(DD, 'anplvl_%s_*.bmp' % r.id)):
        try:
            if time.time() - os.path.getmtime(b) < 0.5: continue
            subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', b, '-vf', 'scale=640:-2', '-q:v', '5',
                            os.path.join(r.out, os.path.basename(b)[:-4] + '.jpg')], capture_output=True, timeout=20)
            os.remove(b)
        except OSError: pass
def mouse(down, right=False):
    u.mouse_event((0x0008 if down else 0x0010) if right else (0x0002 if down else 0x0004), 0, 0, 0, 0)
auto = os.path.join(DD, 'ANP_autoload.txt'); old_auto = open(auto).read() if os.path.exists(auto) else None
try:
    launched = False; wrote_auto = False
    if r.running(): raise SystemExit('kl2.exe already running')
    if not r.take_lock(): raise SystemExit('GAME_LOCK busy')
    if r.running(): raise SystemExit('kl2.exe started by someone else while taking the lock')
    r.clear_hooks()
    open(auto, 'w').write('%s 1 12' % LEVEL); wrote_auto = True
    launched = r.launch()
    if not launched: raise SystemExit(3)
    r.wait_log(r'autoload: load request issued', 120)
    t_load = time.time(); r.say('load requested')
    t0 = time.time(); pressed = 0
    while time.time() - t0 < OPEN_S and r.running():
        # 'Buffering 100%'. Enter is also kl2's SkipCutSeq key: extra presses after the level starts skip its intro
        # (11:32 M01 run: Enters at +3 s and +6 s of gameplay). SMOKE_ENTERS=1 for intro/cutscene tests.
        # with ANP_cutdiag.txt present the loader logs 'InGame state ... seen' the moment the level runs: stop there
        if pressed and re.search(r'cutdiag: .*InGame state', r.log()): ENTERS = pressed
        if pressed < ENTERS and time.time() - t0 > 14 + pressed * 4: r.key('enter', gap=0); pressed += 1
        shot('open'); time.sleep(EVERY); collect()
    if r.running():
        r.say('aim + fire'); r.front()
        mouse(True, right=True); time.sleep(0.8)
        for i in range(10):
            mouse(True); time.sleep(0.12); shot('fire'); mouse(False); time.sleep(0.5); collect()
        mouse(False, right=True)
        for i in range(3): shot('after'); time.sleep(1.0); collect()
finally:
    # only touch the game and the hook files if THIS run launched it (11 Oct 10:46: a refused run quit someone else's game)
    if wrote_auto and old_auto is not None: open(auto, 'w').write(old_auto)
    if launched:
        r.quit(); time.sleep(2); collect()
        r.save_log()
        sq = os.path.join(DD, 'ANP_shot.txt')
        if os.path.exists(sq): os.remove(sq)
    r.release_lock()
    print('shots in', r.out, len(glob.glob(os.path.join(r.out, '*.jpg'))))
