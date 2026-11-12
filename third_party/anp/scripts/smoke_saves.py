"""Unattended save-separation test for the ANP campaigns (design tests 4a and 4b).

Needs (installed by the lead, game closed): the campaign build of ANP_Loader.asi, the chain builds of M03 and M03B in
<DD>\\Scenes\\Locations (work/out_chain), and <DD>\\ANP\\ANP_Patch01.zip (the menu; the Dog Days row is row 2).
No autoload: ANP_autoload.txt is moved aside for the run and put back.

Safety: before anything, Dog Days' save folder (Documents\\Square Enix\\Kane & Lynch 2 - Dog Days) and ANP's Dead Men
slot (%LOCALAPPDATA%\\A Newer Perspective\\saves\\DeadMen) are copied to work/backup/saves_<run>/. The Dead Men slot
is moved aside so the seeding is tested from scratch (--keep-slot keeps it). At the end 0.kls is put back from the
backup if it changed (--no-restore leaves it), and the Dead Men slot of the run is kept in the run folder.

  4a  Press Start -> main menu (SHA-1 h1 of 0.kls) -> ANP_load.txt "M03 1" -> Enter through 'Buffering' ->
      ANP_endlevel.txt "Locations/M03B/M03B_Main" (the real level end: level-complete bookkeeping + save) -> M03B.
      PASS: 0.kls SHA-1 still h1; the log shows "save redirect (DeadMen, write" and saves\\DeadMen\\0.kls exists.
  4b  ANP_load.txt "MM01 0" (what QuitGame does) -> front end. PASS: "profile reload" logged, 0.kls still h1.
      Then Dog Days 'Resume game' from the menu (keys: Down, Enter, Enter): the scene it loads is reported (with
      --baseline it must equal the scene a first, untouched session resumes). 0.kls may change after this point:
      that is Dog Days' own play.

usage: py -I scripts\\smoke_saves.py [--baseline] [--keep-slot] [--no-restore] [--resume-keys=down,enter,enter]
                                    [--wait-min=30]"""
import json, os, shutil, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kltest
from kltest import DD, DOCS_SAVE, APPDATA, lines, sha1

flags = dict((a[2:].split('=', 1) + [''])[:2] for a in sys.argv[1:] if a.startswith('--'))
if any(not a.startswith('--') for a in sys.argv[1:]) or 'help' in flags: print(__doc__); sys.exit(1)
RESUME_KEYS = (flags.get('resume-keys') or 'down,enter,enter').split(',')
SAVE = os.path.join(DOCS_SAVE, '0.kls')
SLOT = os.path.join(APPDATA, 'saves', 'DeadMen')

r = kltest.Run('saves')
bad = kltest.preflight(r)
for lid in ('M03', 'M03B'):
    if not os.path.exists(os.path.join(DD, 'Scenes', 'Locations', lid, '%s_Main.zip' % lid)): bad.append('%s is not installed' % lid)
if not os.path.exists(SAVE): bad.append('no Dog Days save at %s (play to the main menu once first)' % SAVE)
if bad: print('\n'.join(bad)); sys.exit(2)
if not r.take_lock(float(flags.get('wait-min') or 30)): r.say('GAME_LOCK still held - giving up'); sys.exit(2)

BK = os.path.join(kltest.anp_paths.WORK, 'backup', 'saves_' + r.id)
res = dict(run=r.id, backup=BK, hashes={}, checks={}, notes=[])
chk, H = res['checks'], res['hashes']


def h(tag):
    H[tag] = sha1(SAVE); r.say('0.kls SHA-1 %-14s %s' % (tag, H[tag])); return H[tag]


def press_start_to_menu():
    if not r.wait_log(r'campaign: front end loading', 120): r.say('front end never loaded'); return False
    time.sleep(12); r.park_mouse(); r.shot('%s_press_start' % phase)
    r.key('enter'); time.sleep(16); r.park_mouse(); r.shot('%s_main_menu' % phase)
    return r.running()


def resume_dd(tag):
    """Dog Days row -> CampaignMenu -> Resume game; returns the scene id the game opened"""
    mark = len(r.log())
    for k in RESUME_KEYS: r.key(k, gap=1.5)
    req = r.wait_log(r"scene request '(\w+)'.*", 40, since=mark)
    r.say('%s resume request: %s' % (tag, req))
    got = r.wait_log(r'campaign: scene \'(\w+)\' loading', 90, since=mark)
    sid = got.split("'")[1] if got else None
    r.say('%s resume loaded: %s' % (tag, sid))
    if sid:
        time.sleep(10)
        for _ in range(3):
            if not r.running(): break
            r.key('enter', gap=3)
        time.sleep(6); r.shot('%s_resumed_%s' % (tag, sid))
    return sid, req


def level_ready(lid, since):
    if not r.wait_log(r'open SCENES\\Locations\\%s\\%s_Main\.zip ok' % (lid, lid), 90, since=since): return False
    time.sleep(10)
    for _ in range(3):
        if not r.running(): return False
        r.key('enter', gap=3)
    time.sleep(8); r.shot('%s_%s' % (phase, lid))
    return r.running()


phase = 'setup'
try:
    os.makedirs(BK, exist_ok=True)
    shutil.copytree(DOCS_SAVE, os.path.join(BK, 'DogDays'), dirs_exist_ok=True)
    if os.path.isdir(SLOT): shutil.copytree(SLOT, os.path.join(BK, 'DeadMen_slot_before'), dirs_exist_ok=True)
    r.say('backup -> %s' % BK)
    h('h0_start')
    if os.path.isdir(SLOT) and 'keep-slot' not in flags:
        shutil.rmtree(SLOT); r.say('Dead Men slot cleared (a copy is in the backup): seeding is tested')
    r.clear_hooks(); r.move_aside('ANP_autoload.txt')

    if 'baseline' in flags:                   # a first session: what does an untouched Dog Days resume load?
        phase = 'base'
        if r.launch() and press_start_to_menu():
            res['baseline_resume'] = resume_dd('base')[0]
        r.quit()
        with open(os.path.join(r.out, 'log_baseline.txt'), 'w', encoding='utf-8') as f: f.write(r.log())
        if sha1(SAVE) != H['h0_start']:
            shutil.copy2(os.path.join(BK, 'DogDays', '0.kls'), SAVE); r.say('baseline session changed 0.kls: restored from the backup')
        h('h0_after_baseline')

    phase = 'a'
    if not r.launch(): raise SystemExit(3)
    if not r.wait_log(r'campaign: config .*', 60): res['notes'].append('no campaign config line: old ANP_Loader.asi?')
    if not press_start_to_menu(): raise SystemExit(4)
    h1 = h('h1_menu')
    if h1 != H.get('h0_after_baseline', H['h0_start']): res['notes'].append('Press Start itself rewrote 0.kls (stock behaviour; the checks compare against h1)')
    # ---- 4a
    mark = len(r.log()); r.hook('ANP_load.txt', 'M03 1')
    req = r.wait_log(r"scene request 'M03'.*", 30, since=mark); r.say('request: %s' % req)
    chk['4a_mode_DeadMen'] = bool(req and 'mode DeadMen' in req)
    if not level_ready('M03', mark): raise SystemExit(5)
    h('h2_in_M03')
    mark = len(r.log()); r.hook('ANP_endlevel.txt', 'Locations/M03B/M03B_Main')
    chk['4a_level_end_fired'] = bool(r.wait_log(r'endlevel: level end issued', 60, since=mark))
    chk['4a_M03B_loaded'] = level_ready('M03B', mark)
    h2 = h('h2_after_end')
    lg = r.log()
    res['save_redirects'] = lines(lg, r'save redirect')[:20]
    chk['4a_dd_save_unchanged'] = h2 == h1
    chk['4a_redirected_write'] = any('save redirect (DeadMen, write' in l for l in res['save_redirects'])
    chk['4a_slot_file'] = os.path.exists(os.path.join(SLOT, '0.kls'))
    res['slot_sha1'] = sha1(os.path.join(SLOT, '0.kls'))
    r.hook('ANP_cstate.txt'); time.sleep(2)
    # ---- 4b
    phase = 'b'
    mark = len(r.log()); r.hook('ANP_load.txt', 'MM01 0')
    chk['4b_front_end'] = bool(r.wait_log(r'campaign: front end loading.*', 90, since=mark))
    rel = r.wait_log(r'campaign: profile reload.*', 30, since=mark); r.say('reload: %s' % rel)
    chk['4b_profile_reload'] = bool(rel and 'skipped' not in rel)
    done = r.wait_log(r'campaign: profile reload (done|did NOT).*', 20, since=mark); r.say('reload result: %s' % done)
    chk['4b_profile_read_from_disk'] = bool(done and 'read from disk' in done)
    time.sleep(8); r.park_mouse(); r.shot('b_main_menu')
    h3 = h('h3_after_reload')
    chk['4b_dd_save_unchanged'] = h3 == h1
    r.hook('ANP_cstate.txt'); time.sleep(2)
    sid, rq = resume_dd('b')
    res['resume'] = dict(scene=sid, request=rq)
    chk['4b_resume_mode_DogDays'] = bool(rq and 'mode DogDays' in rq)
    chk['4b_resume_is_DD_level'] = bool(sid and sid.startswith('L'))
    if 'baseline_resume' in res: chk['4b_resume_matches_baseline'] = sid == res['baseline_resume']
    res['dd_save_written_by_resume'] = any('save redirect' not in l and '0.kls' in l for l in lines(r.log()[mark:], r'open .*\.kls'))
    h('h4_after_resume')
finally:
    r.quit()
    r.restore_moved()
    lg = r.save_log()
    res['log'] = dict(campaign=lines(lg, r'campaign:|scene request|save redirect|ExitProcess|cstate:|achievement')[:120],
                      exceptions=[l for l in lines(lg, 'EXCEPTION') if '00a8e3cb' not in l][:10],
                      ceg_tripwire=lines(lg, 'CEG TRIPWIRE'))
    chk['no_ceg_exit'] = not res['log']['ceg_tripwire']
    if os.path.isdir(SLOT): shutil.copytree(SLOT, os.path.join(r.out, 'DeadMen_slot'), dirs_exist_ok=True)
    h('h5_end')
    if H.get('h5_end') != H.get('h0_start') and 'no-restore' not in flags and os.path.exists(os.path.join(BK, 'DogDays', '0.kls')):
        shutil.copy2(os.path.join(BK, 'DogDays', '0.kls'), SAVE); r.say('0.kls restored from the backup'); h('h6_restored')
    r.release_lock()
    res['pass'] = all(chk.values()) and bool(chk)
    with open(os.path.join(r.out, 'result.json'), 'w') as f: json.dump(res, f, indent=1)
    for k, v in chk.items(): r.say('%-30s %s' % (k, 'ok' if v else 'FAIL'))
    r.say('%s -> %s' % ('SAVE TEST PASSED' if res['pass'] else 'SAVE TEST FAILED', r.out))
