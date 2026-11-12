"""Unattended crew-order test (loader squad.inc): autoload a level, skip the intro (Enter), god mode on, write
ANP_squad.txt (mode) and feed ANP_squad_cmd.txt commands one step at a time, collect the 'SQUAD' log lines and in-game
(D3D) shots. Based on smoke_triggers.py: GAME_LOCK, never starts while kl2.exe runs, every file put into the Dog Days
folder is removed or restored afterwards. It does NOT install the loader: copy work\\out_squad\\ANP_Loader.asi to
<DD>\\ANP_Loader.asi yourself while the game is closed (the script warns when the installed one differs).

usage: smoke_squad.py [level=M02] [mode=on] [--keys] [--cmds "follow hold; wait 6; next; ..."] [--extra "key=value ..."]
  level   any ANP level id. M01 refuses every order by design (expect 'SQUAD refuse ...'); real orders from M02 on.
  mode    off | probe | dry | on (ANP_squad.txt)
  --keys  after the commands, also press the real keys through SendInput scan codes: 1 tap, 1 hold, 3 tap, 2 tap,
          Tab, Shift+Tab (tests the DD-device input path; the game must be in the foreground)
  --cmds  replace the default command list; ';' separates steps, 'wait S' sleeps S seconds between steps
  --extra more ANP_squad.txt tokens, e.g. "markers=1 release=moveto attack_time=8"
"""
import argparse, ctypes, glob, hashlib, os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kltest

ap = argparse.ArgumentParser()
ap.add_argument('level', nargs='?', default='M02')
ap.add_argument('mode', nargs='?', default='on', choices=['off', 'probe', 'dry', 'on'])
ap.add_argument('--keys', action='store_true')
ap.add_argument('--cmds', default=None)
ap.add_argument('--extra', default='')
A = ap.parse_args()

DEFAULT = ('state; wait 3; follow hold; wait 6; next; wait 1.5; next; wait 1.5; next; wait 1.5; '
           'defend tap aim; wait 8; follow hold; wait 6; attack hold nearest; wait 10; attack tap aim; wait 6; '
           'defend hold aim; wait 8; follow hold; wait 6; state; wait 3')
STEPS = [s.strip() for s in (A.cmds or DEFAULT).split(';') if s.strip()]

DD = kltest.DD
REPO = kltest.REPO
BUILT = os.path.join(kltest.anp_paths.WORK, 'out_squad', 'ANP_Loader.asi')
r = kltest.Run('squad_%s_%s' % (A.level, A.mode))
F = {n: os.path.join(DD, n) for n in ('ANP_autoload.txt', 'ANP_squad.txt', 'ANP_squad_cmd.txt', 'ANP_squad_cmd.done',
                                     'ANP_squad_cmd.txt.tmp', 'ANP_god.txt', 'ANP_cutdiag.txt', 'ANP_shot.txt')}
KEEP = ('ANP_autoload.txt', 'ANP_squad.txt', 'ANP_god.txt', 'ANP_cutdiag.txt')    # restored to what was there before
OLD = {n: open(F[n]).read() for n in KEEP if os.path.exists(F[n])}
u = ctypes.windll.user32
n_shot = [0]


def sha1(p):
    try:
        with open(p, 'rb') as f: return hashlib.sha1(f.read()).hexdigest().upper()
    except OSError: return None


def shot(tag):
    if os.path.exists(F['ANP_shot.txt']): time.sleep(1.0)
    name = 'anpsquad_%s_%02d_%s.bmp' % (r.id, n_shot[0], re.sub(r'[^A-Za-z0-9]+', '_', tag)[:24]); n_shot[0] += 1
    open(F['ANP_shot.txt'], 'w').write(name)


def collect():
    for b in glob.glob(os.path.join(DD, 'anpsquad_%s_*.bmp' % r.id)):
        try:
            if time.time() - os.path.getmtime(b) < 0.5: continue
            if kltest.FF:
                subprocess.run([kltest.FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', b, '-vf', 'scale=640:-2', '-q:v', '5',
                                os.path.join(r.out, os.path.basename(b)[:-4] + '.jpg')], capture_output=True, timeout=20)
                os.remove(b)
            else: os.replace(b, os.path.join(r.out, os.path.basename(b)))
        except (OSError, subprocess.SubprocessError): pass


def squad_lines(text):
    return [l for l in text.splitlines() if re.search(r'SQUAD |climb: FAULT .*squad|EXCEPTION', l)]


def send_cmd(cmd):
    """write one command; wait until the loader consumed it (renamed to ANP_squad_cmd.done)"""
    if os.path.exists(F['ANP_squad_cmd.done']): os.remove(F['ANP_squad_cmd.done'])
    with open(F['ANP_squad_cmd.txt'] + '.tmp', 'w') as f: f.write(cmd + '\n')
    os.replace(F['ANP_squad_cmd.txt'] + '.tmp', F['ANP_squad_cmd.txt'])
    r.say('cmd: %s' % cmd)
    ok = r.wait_for(lambda: not os.path.exists(F['ANP_squad_cmd.txt']), 10, 0.25)
    if not ok: r.say('   (not consumed within 10 s: level not ready, paused or module off)')
    return ok


def key_sc(sc, hold=0.08, ext=False):
    flags = 0x0008 | (0x0001 if ext else 0)
    u.keybd_event(0, sc, flags, 0); time.sleep(hold); u.keybd_event(0, sc, flags | 0x0002, 0)


def keys_phase():
    r.front(); time.sleep(0.5)
    plan = [('1 tap', 0x02, 0.08), ('1 hold', 0x02, 0.6), ('3 tap', 0x04, 0.08), ('2 tap', 0x03, 0.08), ('Tab', 0x0F, 0.08)]
    for name, sc, hold in plan:
        r.say('key %s' % name); key_sc(sc, hold); time.sleep(3); shot('key_' + name); collect()
    r.say('key Shift+Tab'); u.keybd_event(0, 0x2A, 0x0008, 0, ); time.sleep(0.05); key_sc(0x0F); u.keybd_event(0, 0x2A, 0x000A, 0)
    time.sleep(3); shot('key_shift_tab'); collect()


launched = False; wrote = False
try:
    if r.running(): raise SystemExit('kl2.exe already running')
    inst, built = sha1(os.path.join(DD, 'ANP_Loader.asi')), sha1(BUILT)
    if not inst: raise SystemExit('no ANP_Loader.asi in the Dog Days folder')
    if built and inst != built:
        r.say('WARNING: the installed ANP_Loader.asi (%s) is not %s (%s): copy it in first (game closed)' % (inst[:10], BUILT, built[:10]))
    if not r.take_lock(): raise SystemExit('GAME_LOCK busy')
    if r.running(): raise SystemExit('kl2.exe started by someone else')
    r.clear_hooks(); wrote = True
    for n in ('ANP_squad_cmd.txt', 'ANP_squad_cmd.done'):
        if os.path.exists(F[n]): os.remove(F[n])
    open(F['ANP_autoload.txt'], 'w').write('%s 1 12' % A.level)
    open(F['ANP_cutdiag.txt'], 'w').write('')              # logs 'InGame state' (intro skip loop stops there)
    open(F['ANP_god.txt'], 'w').write('1')                 # test-only god mode (loader godmode.inc)
    open(F['ANP_squad.txt'], 'w').write('mode=%s stat=5 %s\n' % (A.mode, A.extra))
    r.say('ANP_squad.txt = mode=%s stat=5 %s' % (A.mode, A.extra))
    launched = r.launch()
    if not launched: raise SystemExit(3)
    if not r.wait_log(r'SQUAD config', 60):
        r.say('FAIL: no "SQUAD config" line - the installed loader has no squad module (copy %s)' % BUILT)
    r.wait_log(r'autoload: load request issued', 120); time.sleep(14)
    r.key('enter', gap=2)                                  # Buffering 100%
    r.wait_log(r'cutdiag: .*InGame state', 60)
    t0 = time.time()
    while time.time() - t0 < 45 and r.running():          # skip the intro cutscenes
        r.key('enter', gap=0); time.sleep(3); r.touch_lock()
    if not r.wait_log(r'SQUAD probe scene=', 60): r.say('no "SQUAD probe" line within 60 s (not an ANP level, or no player)')
    shot('start'); time.sleep(1.5); collect()
    for step in STEPS:
        if not r.running(): r.say('kl2.exe is gone'); break
        m = re.match(r'wait\s+([\d.]+)$', step, re.I)
        if m:
            end = time.time() + float(m.group(1))
            while time.time() < end: r.touch_lock(); time.sleep(0.5); collect()
            continue
        mark = len(r.log())
        send_cmd(step); time.sleep(1.5)
        for l in squad_lines(r.log()[mark:])[:12]: r.say('   ' + l[l.find('SQUAD'):][:230] if 'SQUAD' in l else '   ' + l[:230])
        shot(step); collect()
    if A.keys and r.running(): keys_phase()
    time.sleep(6); collect()
finally:
    if launched: r.quit(); time.sleep(1); collect()
    text = r.save_log() if launched else ''
    if wrote:
        for n in KEEP:
            try:
                if n in OLD: open(F[n], 'w').write(OLD[n])
                elif os.path.exists(F[n]): os.remove(F[n])
            except OSError as e: r.say('could not restore %s: %s' % (n, e))
        for n in ('ANP_squad_cmd.txt', 'ANP_squad_cmd.done', 'ANP_squad_cmd.txt.tmp', 'ANP_shot.txt'):
            if os.path.exists(F[n]):
                try: os.remove(F[n])
                except OSError: pass
    r.release_lock()
    collect()
    for b in glob.glob(os.path.join(DD, 'anpsquad_%s_*.bmp' % r.id)):
        try: os.replace(b, os.path.join(r.out, os.path.basename(b)))
        except OSError: pass
    if text:
        sl = squad_lines(text)
        with open(os.path.join(r.out, 'squad_lines.txt'), 'w', encoding='utf-8') as f: f.write('\n'.join(sl) + '\n')
        has = lambda p: any(re.search(p, l) for l in sl)
        checks = [('module loaded (SQUAD config)', has(r'SQUAD config')),
                  ('probe line', has(r'SQUAD probe scene=')),
                  ('stat lines', sum(1 for l in sl if 'SQUAD stat ' in l) >= 2),
                  ('no SQUAD DISABLED', not has(r'SQUAD DISABLED')),
                  ('no EXCEPTION', not has(r'EXCEPTION c\w+ at (?!00a8e3cb)'))]   # 0xa8e3cb = benign Steam probe
        if A.mode == 'on' and A.level.upper() == 'M01':
            checks.append(('M01 refusal', has(r'SQUAD (refuse (follow|attack|defend) |order follow .*REFUSED)')))
        elif A.mode == 'on':
            checks += [('follow issued', has(r'SQUAD order follow \w+ -> 0x4c3900')),
                       ('defend or nolos', has(r'SQUAD (order defend merc=|defend fail nolos)')),
                       ('attack issued', has(r'SQUAD order attack merc='))]
        elif A.mode == 'dry':
            checks.append(('dry orders', has(r'SQUAD (order \w+ .*dry|(order|refuse) \w+ \w+: .*\(dry\)|sel .*\(dry: unchanged\))')))
        for name, ok in checks: r.say('%s %s' % ('PASS' if ok else 'FAIL', name))
        r.say('%d SQUAD lines -> %s' % (len(sl), os.path.join(r.out, 'squad_lines.txt')))
    print('done ->', r.out)
