"""Unattended trigger-box test: autoload a level, skip intro cutscenes (Enter), teleport the player into given boxes
(ANP_tp.txt, loader climb.inc test hook) and watch cutdiag lines (cutscenes starting) + D3D shots.
usage: smoke_triggers.py <level> "<name> x y z yaw" ["<name> x y z yaw" ...]"""
import os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kltest
LEVEL = sys.argv[1]; SPOTS = [a.split() for a in sys.argv[2:]]
DD = kltest.DD
r = kltest.Run('trig_%s' % LEVEL)
auto = os.path.join(DD, 'ANP_autoload.txt'); old_auto = open(auto).read() if os.path.exists(auto) else None
cd = os.path.join(DD, 'ANP_cutdiag.txt'); cl = os.path.join(DD, 'ANP_climb.txt'); old_cl = open(cl).read() if os.path.exists(cl) else None
launched = False; wrote = False
def shot(tag):
    r.hook('ANP_shot.txt', 'anptrig_%s_%s.bmp' % (r.id, tag)); time.sleep(1.5)
try:
    if r.running(): raise SystemExit('kl2.exe already running')
    if not r.take_lock(): raise SystemExit('GAME_LOCK busy')
    if r.running(): raise SystemExit('kl2.exe started by someone else')
    r.clear_hooks(); wrote = True
    open(auto, 'w').write('%s 1 12' % LEVEL); open(cd, 'w').write(''); open(cl, 'w').write('live trace=1')
    open(os.path.join(DD, 'ANP_god.txt'), 'w').write('1')    # test-only god mode (loader godmode.inc): survive firefights
    launched = r.launch()
    if not launched: raise SystemExit(3)
    r.wait_log(r'autoload: load request issued', 120); time.sleep(14)
    r.key('enter', gap=2)                                  # Buffering 100%
    r.wait_log(r'cutdiag: .*InGame state', 60)
    t0 = time.time()
    while time.time() - t0 < 45 and r.running():          # skip the intro cutscenes
        r.key('enter', gap=0); time.sleep(3); r.touch_lock()
    for s in SPOTS:
        name, x, y, z, yaw = s[0], s[1], s[2], s[3], s[4]
        mark = len(r.log())
        r.hook('ANP_tp.txt', '%s %s %s %s' % (x, y, z, yaw)); time.sleep(6); shot(name)
        lines = [l for l in r.log()[mark:].splitlines() if re.search(r'cutdiag: .*C n|climb: tp:', l)]
        r.say('%s: %d lines' % (name, len(lines)))
        for l in lines[:20]: r.say('   ' + l[:200])
        time.sleep(4)
finally:
    if wrote:
        if old_auto is not None: open(auto, 'w').write(old_auto)
        if old_cl is not None: open(cl, 'w').write(old_cl)
    if launched: r.quit(); r.save_log()
    if wrote and os.path.exists(cd): os.remove(cd)
    if wrote and os.path.exists(os.path.join(DD, 'ANP_god.txt')): os.remove(os.path.join(DD, 'ANP_god.txt'))
    r.release_lock()
    for b in [f for f in os.listdir(DD) if f.startswith('anptrig_%s' % r.id)]:
        try: os.replace(os.path.join(DD, b), os.path.join(r.out, b))
        except OSError: pass
    print('done ->', r.out)
