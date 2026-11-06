#!/usr/bin/env python3
"""
Bench kits for the two staged-but-never-run builds (2026-11-06). One command each once the owner says "test".

    python tools/kl_bench_1106.py gen                 write/refresh the kit folders under C:/kl_build_1024/bench_1106 (no game contact)
    python tools/kl_bench_1106.py validate [kit|all]  DRY RUN: paths, md5s, TEST dll marker, ini sections, script ops, install.py --dry.
                                                      Never launches the game, never writes into the game folder.
    python tools/kl_bench_1106.py run lc1106 [solo|online|all]
    python tools/kl_bench_1106.py run dd10s1106 [solo|long|all]
    python tools/kl_bench_1106.py run lcglass1106 online       glass pass on the live chain: round-2 reset 0x25 time per seat
    python tools/kl_bench_1106.py verify lc1106|dd10s1106 [part]    re-read the logs of the last run (no game contact)

Kits
  lc1106     Last Call chain stage (C:/kl_build_1024/lastcall_chain_1105/stage: plain zip c8dd18ee, bots 42ed37ba, F01_Main_LS.SND)
             solo Arcade round on DM05A (slot F01, page 3) with [Heli] Probe=2, [Camera] Log=1, d3 shots; then an online 2-seat round
             (the hook swaps in the bots zip) = Q32 host/join pair, round 1 -> shop -> round 2.
  dd10s1106  DD10 Flat Raid slim stage (C:/kl_build_1024/dd10_slim_1105/stage, slot F07, page 3 entry 5): solo round + a long online match
             (4 rounds) with the memory log; compares the largest free block with the ~14.4 MB baseline.

IMPORTANT, said plainly: kl_solo_test.py runs kl2.exe against the LIVE Dog Days folder (it reads <DD>/KLExpansion/Maps/<MAP>), so the staged
files can only be tested by installing them there. `run` therefore (1) records the md5 of every file in the map folder, (2) runs the stage's
own install.py (originals renamed *.before-1105chain / *.before-1105slim, never overwritten), (3) runs the bench (which itself swaps the TEST
dinput8.dll in and the live one back), (4) ALWAYS runs install.py --undo in a finally block and compares the md5s with step 1. If the undo
fails the tool prints UNDO FAILED and the exact command to run by hand. It touches nothing but KLExpansion/Maps/<MAP> and dinput8.dll
(swapped by kl_solo_test). KL_PortBackup is never touched. The launch options are never changed (the bench starts kl2.exe directly).
"""
import hashlib, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = 'C:/kl_build_1024/bench_1106'
DD = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
SOLO = 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo'
HOOK_SRC = 'C:/kl_build_1024/n9_twins/727a73bb/dinput8.dll'    # TEST twin b6a69772 of SHIP 727a73bb (6b pics_1105_hook, live since 11-06)
HOOK_MD5 = 'b6a697726b66ca7270921d6d4543005f'
Q32 = 'C:/kl_build_1024/c9_1028/q32'
COVER = ('AssertSoft', 'ClientBuild', 'ClientBuildHost', 'ClientRewrite', 'ClientRingSync')
OPS = set('waitwin settle tapuntil tap wait windows sel expect msg waitload waitstate waitvan waitpeers tele goto pos ents peek log pass fail label jump onwin mouse'.split())

KITS = {
    'lc1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lastcall_chain_1105/stage', tag='.before-1105chain',
                   files={'F01_Main.zip': 'c8dd18ee28b511db2ee46a10f9e86e11', 'F01_Main.bots.zip': '42ed37ba', 'F01_Main_LS.SND': 'b6fdd4c0'},
                   solo_secs=1500, parts=('solo', 'online')),
    'dd10s1106': dict(map='DD10', slot='F07', entry=5, stage='C:/kl_build_1024/dd10_slim_1105/stage', tag='.before-1105slim',
                      files={'F07_Main.zip': '66ec246da361ace049fc65e2762b4a9c', 'F07_Main.bots.zip': '3ccb580fc527638af2eb099394fc5369',
                             'F07_Main.WAV': '9fd304579b3dd40c577265a79f7c4e90', 'F07_Main.WHD': '3a260f8b542f4308f77e0a62840075a0'},
                      solo_secs=1500, parts=('solo', 'long')),
    # glass pass on top of the LIVE chain (install.py pins c8dd18ee): the round-2 reset (0x25) must drop from 21-29 s per seat to seconds
    'lcglass1106': dict(map='DM05A', slot='F01', entry=0, stage='C:/kl_build_1024/lastcall_glass_1106/stage', tag='.before-1106glass',
                        files={'F01_Main.zip': '3f0018b38593d708ac830e53150fb814', 'F01_Main.bots.zip': 'cb962a65', 'F01_Main.bots.base.md5': '00cfe35a'},
                        solo_secs=1500, parts=('online', 'solo')),
    # the LIVE DM05A as it is (chain + glass + pd2guns + buttons + pics, 11-06): stage None = nothing installed, the live zip is pinned and
    # the map folder must be byte-identical after the run (escape boarding with E, re/lastcall_escape_screen_1106.md)
    'lclive1106': dict(map='DM05A', slot='F01', entry=0, stage=None, tag=None, live={'F01_Main.zip': 'e6d2f73e'},
                       solo_secs=1500, parts=('solo',)),
}
LC = ('lc1106', 'lcglass1106', 'lclive1106')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def mapdir(k):
    return '%s/KLExpansion/Maps/%s' % (DD, KITS[k]['map'])


def snap(d):
    return {n: md5(os.path.join(d, n)) for n in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, n))}


def read_secs(path):
    secs, cur = [], None
    for ln in open(path, encoding='latin-1').read().splitlines():
        m = re.match(r'\s*\[([^\]]+)\]\s*$', ln)
        if m:
            cur = (m.group(1), []); secs.append(cur)
        elif cur is not None and '=' in ln and not ln.lstrip().startswith(';'):
            k, _, v = ln.partition('=')
            cur[1].append((k.strip(), v))
    return secs


def script_of(path):
    return [v for s, kv in read_secs(path) if s == 'Script' for k, v in kv]


# ---------------------------------------------------------------- generation
def solo_script(k, secs_total):
    c = KITS[k]
    s = ['waitwin CampaignMenu 180000', 'settle 15 150 60000', 'tapuntil ESCAPE MainMenu 10000 3', 'settle 8 150 30000', 'wait 1500', 'tap DOWN', 'wait 1200',
         'tapuntil RETURN HeistModeMenu 15000 2', 'settle 8 150 30000', 'wait 3000', 'windows']
    for _ in range(7):
        s += ['tap DOWN', 'wait 500']
    s += ['wait 2500', 'windows', 'tap RETURN', 'waitwin HeistPlayMenu3 8000', 'wait 3000', 'windows',
          'sel HeistLevel_P3 0xceceec %d' % c['entry'], 'wait 2500', 'expect 0xceceec %d' % c['entry'],
          'log BENCH1106 %s entry %d page 3 slot %s' % (c['map'], c['entry'], c['slot']), 'msg HeistLevel_P3 StartGame', 'waitload 300000',
          'log BENCH1106 level loaded: %s' % c['map'], 'wait 23000', 'peek 0x168e598+0x70 session-state-must-be-0x19', 'pos spawn']
    if k in LC:
        # Escape: the vehicle state machine is open-loop timers (re/lastcall_heli_1105.md). Wait for state 3 (van/chopper at the pad),
        # board by teleporting into the box (GUESS: the coordinates are the box from the doc, 7361/2014/3201; 'tele' is TEST-rig only),
        # then wait for the round-over panel (0x1f) and the shop (0x20). Every wait goes on at its timeout so a dead chain still ends.
        s += ['wait 30000', 'pos at-60s', 'log BENCH1106 waiting for vehicle state 3', 'waitvan 3 600000', 'pos van3', 'wait 5000',
              'tele 7361 2014 3201', 'log BENCH1106 teleported into the escape box', 'wait 3000', 'pos teleported',
              # run lc1106 (11-06 02:43): the player stood in BoardingTrigger_Heli (centre 7361/2014/3201, half extents 400x200x300, so y 1814..2214;
              # floor 1881) but never went aboard: a human boards only through PlayerAction 'EnterVehicle', i.e. HOLDING E there
              # (re/human_escape_online_1028.md, live hold 2-5 s); the bench never pressed it. Walk from +x first: facing is a GUESS (eIntDir_CtrlDir)
              'goto 7561 3201 60 8000', 'goto 7361 3201 60 8000', 'wait 1000', 'pos in-box',
              'tap E 3000', 'wait 1000', 'pos try1', 'tap E 3000', 'wait 1000', 'pos try2', 'tap E 4000', 'wait 1000', 'pos boarded',
              'waitvan 5 120000', 'pos van5',
              'wait 8000', 'pos after5', 'waitstate 0x1f 240000', 'pos s1f', 'wait 12000', 'waitstate 0x20 120000', 'log BENCH1106 LC solo done', 'wait 3000', 'pass 1000']
    else:
        for i in range(1, 11):
            s += ['wait 30000', 'pos at-%ds' % (60 + 30 * i)]
            if i % 3 == 0:
                s.append('windows')
        s += ['log BENCH1106 DD10 solo done', 'pass 1000']
    return s


AUTO = ['[Auto]', 'Enable=1', 'Hooks=0', 'Nodes=0', 'EndHooks=1', 'CmdDrop=DefaultScene,AutoExit', 'CmdAdd=-o DisableSplashScreens -o AutoExit={x}',
        'StallMs=300000', 'MaxRunMs={m}', 'LoadedMs=0', 'Unfocused=1', 'BlockReal=1', 'FirstChance=1', 'PosLogMs=5000']


def probes(k):
    t = ['[Memory]', 'Log=1']
    if k in LC:
        t = ['[Heli]', 'Probe=2', '[Camera]', 'Log=1', '[Memory]', 'Log=1']
    return t


def long_match(lines, extra_rounds):
    """Insert extra 'shop -> next round' blocks before the pass line of a Q32 script (rounds 3, 4 ...)."""
    i = max(j for j, l in enumerate(lines) if l.startswith('pass '))
    add = []
    for r in range(3, 3 + extra_rounds):
        add += ['log BENCH1106 shop before round %d' % r, 'waitstate 0x20 600000', 'waitstate 0x19 240000', 'log BENCH1106 ROUND %d running' % r, 'wait 30000', 'pos host-r%d' % r]
    return lines[:i] + add + lines[i:]


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='latin-1', newline='\n') as f:
        f.write(text)


def renumber(lines):
    out, n = [], 0
    for l in lines:
        if l.startswith(';'):
            out.append(l)
        else:
            n += 1; out.append('%d=%s' % (n, l))
    return out


def pair(k, who, long_rounds):
    """Q32 host/join file with the kit's probes added and, for the long match, extra rounds in the script (both seats)."""
    q = '%s/Q32_%s_%s.ini' % (Q32, KITS[k]['map'], who)
    secs = read_secs(q)
    scr = script_of(q)
    if long_rounds:
        scr = long_match(scr, long_rounds)
    # keep every non-Script section, drop [Auto] (rewritten for the longer run), keep order
    secs_t = ['; bench_1106 %s %s: Q32 pair (round 1 -> shop -> round 2%s) + probes' % (k, who, (' -> %d more' % long_rounds) if long_rounds else '')]
    total = 2400 if long_rounds else 1950
    for name, kv in secs:
        if name == 'Script':
            continue
        if name == 'Auto':
            kv = [(a, b) for a, b in kv if a not in ('CmdAdd', 'MaxRunMs')] + [('CmdAdd', '-o DisableSplashScreens -o AutoExit=%d' % total), ('MaxRunMs', str((total - 10) * 1000))]
        secs_t.append('[%s]' % name); secs_t += ['%s=%s' % kv_ for kv_ in kv]
    secs_t += probes(k)
    secs_t += ['[Script]'] + renumber(scr)
    return '\n'.join(secs_t) + '\n'


def gen():
    import shutil
    os.makedirs(KIT, exist_ok=True)
    live = '%s/KLHook.ini' % DD
    for k, c in KITS.items():
        d = '%s/%s' % (KIT, k)
        os.makedirs('%s/hook_test' % d, exist_ok=True)
        shutil.copy2(HOOK_SRC, '%s/hook_test/dinput8.dll' % d)
        shutil.copy2(live, '%s/KLHook_base.ini' % d)       # snapshot of the live ini (cover lines etc.); a later live edit does not change a kit
        shutil.copy2('%s/KLShopPage.ini' % DD, '%s/KLShopPage.ini' % d)
        t = ['; bench_1106 %s solo: OFFLINE Arcade, 1 seat, %s slot %s page 3 entry %d' % (k, c['map'], c['slot'], c['entry']),
             '; the seat stands still; cops hurt it 0.001 x so its death does not end the round (as ARC1)',
             '[Balance]', 'CopToYou=0.001', 'PointBlankToYou=0.0'] + probes(k)
        n = c['solo_secs']
        t += [l.replace('{x}', str(n - 60)).replace('{m}', str((n - 70) * 1000)) for l in AUTO]
        t += ['[Script]'] + renumber(solo_script(k, n))
        write('%s/solo.ini' % d, '\n'.join(t) + '\n')
        lr = 2 if k == 'dd10s1106' else 0
        write('%s/online_host.ini' % d, pair(k, 'host', lr))
        write('%s/online_join.ini' % d, pair(k, 'join', lr))
    print('gen: kits written under', KIT)


# ---------------------------------------------------------------- validate
class V:
    def __init__(s):
        s.fail = 0

    def ok(s, cond, text, warn=False):
        tag = 'PASS' if cond else ('WARN' if warn else 'FAIL')
        if not cond and not warn:
            s.fail += 1
        print('  %-4s %s' % (tag, text))
        return cond


def validate(which):
    v = V()
    print('validate (dry run: no game launch, no write into the game folder)')
    v.ok(os.path.isdir(DD), 'Dog Days folder %s' % DD)
    v.ok(os.path.isfile('%s/kl2.exe' % DD), 'kl2.exe present')
    tl = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe'], capture_output=True, text=True).stdout
    v.ok('kl2.exe' not in tl, 'no kl2.exe is running (a run would refuse otherwise)', warn=True)
    v.ok(os.path.isfile(os.path.join(ROOT, 'tools/kl_solo_test.py')), 'tools/kl_solo_test.py')
    v.ok(os.path.isdir(SOLO), 'solo work folder %s' % SOLO)
    for k in (list(KITS) if which == 'all' else [which]):
        c, d = KITS[k], '%s/%s' % (KIT, k)
        print('[%s]' % k)
        dll = '%s/hook_test/dinput8.dll' % d
        if v.ok(os.path.isfile(dll), 'bench dll %s' % dll):
            data = open(dll, 'rb').read()
            v.ok(hashlib.md5(data).hexdigest() == HOOK_MD5, 'dll md5 %s = TEST twin b6a69772' % hashlib.md5(data).hexdigest()[:8])
            v.ok(data.count(b'(TEST)') >= 3 and b"klauto's scripted keys" in data, 'dll carries the TEST markers ((TEST) x%d, klauto strings = build_auto.bat build; SHIP has 1)' % data.count(b'(TEST)'))
            v.ok(2_500_000 < len(data) < 2_700_000, 'dll size %.2f MB (about 2.59 MB expected)' % (len(data) / 1e6))
        live_dll = '%s/dinput8.dll' % DD
        if os.path.isfile(live_dll):
            v.ok(b"klauto's scripted keys" not in open(live_dll, 'rb').read(), 'live dll is the SHIP build, no klauto (md5 %s; kl_solo_test swaps the TEST dll in and back)' % md5(live_dll)[:8], warn=True)
        base = '%s/KLHook_base.ini' % d
        if v.ok(os.path.isfile(base), 'base ini snapshot'):
            txt = open(base, encoding='latin-1').read()
            for key in COVER:
                v.ok(re.search(r'^%s=' % key, txt, re.M) is not None, 'base ini has cover line %s' % key)
            for sec in ('Expansion', 'Memory', 'Heli', 'Camera', 'Lobby'):
                v.ok('[%s]' % sec in txt, 'base ini has [%s]' % sec, warn=sec in ('Heli', 'Camera'))
            if c['slot'] not in (re.search(r'^ClientBuildMaps=([^\s;]*)', txt, re.M) or [0, ''])[1].split(','):
                v.ok(False, 'ClientBuildMaps does not list %s (kits copy the live cover lines; ONLINE client build for that slot is whatever the live ini says)' % c['slot'], warn=True)
        v.ok(os.path.isfile('%s/KLShopPage.ini' % d), 'KLShopPage.ini copy (staged into solo/<TAG>/inst1+2 by run)')
        for f in ('solo.ini', 'online_host.ini', 'online_join.ini'):
            p = '%s/%s' % (d, f)
            if v.ok(os.path.isfile(p), 'kit file %s' % f):
                scr = script_of(p)
                bad = sorted({l.split()[0] for l in scr if l.split() and l.split()[0] not in OPS})
                v.ok(not bad and len(scr) > 20, '%s: %d script lines, ops known%s' % (f, len(scr), (' (UNKNOWN: %s)' % bad) if bad else ''))
                v.ok(sum(1 for l in re.findall(r'^\[Script\]', open(p, encoding='latin-1').read(), re.M)) == 1, '%s: exactly one [Script] section' % f)
                v.ok(any(l.startswith('pass') for l in scr), '%s: ends with pass' % f)
        st = c['stage']
        if st is None:
            for n, want in c['live'].items():
                p = '%s/%s' % (mapdir(k), n)
                v.ok(os.path.isfile(p) and md5(p).startswith(want), 'live %s md5 %s = pin %s (nothing is installed)' % (n, md5(p)[:8] if os.path.isfile(p) else '-', want))
            for part in c['parts']:
                print('  command: python tools/kl_bench_1106.py run %s %s' % (k, part))
            continue
        inst = '%s/install.py' % st
        v.ok(os.path.isfile(inst), 'stage install.py (md5 %s)' % (md5(inst)[:8] if os.path.isfile(inst) else '-'))
        for n, want in c['files'].items():
            p = '%s/%s' % (st, n)
            if v.ok(os.path.isfile(p), 'staged %s' % n):
                v.ok(md5(p).startswith(want[:8]), 'staged %s md5 %s = %s' % (n, md5(p)[:8], want[:8]))
        md = mapdir(k)
        if v.ok(os.path.isdir(md), 'live map folder %s' % md):
            haveb = [n for n in os.listdir(md) if n.endswith(c['tag'])]
            v.ok(not haveb, 'no %s backups present (install refuses otherwise)%s' % (c['tag'], (': ' + ', '.join(haveb)) if haveb else ''))
            v.ok(True, 'live md5s now: ' + ', '.join('%s=%s' % (n, m[:8]) for n, m in snap(md).items() if '.before-' not in n and n.startswith(c['slot'] + '_Main.') and n.split('.')[-1] in ('zip', 'WAV', 'WHD', 'SND', 'md5')))
        if os.path.isfile(inst):
            r = subprocess.run([sys.executable, inst, '--dry', '--game', DD] if k == 'dd10s1106' else [sys.executable, inst, '--dry'], capture_output=True, text=True)
            v.ok(r.returncode == 0, 'install.py --dry exit %d: %s' % (r.returncode, (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or [''])[-1][:140]))
        for part in c['parts']:
            print('  command: python tools/kl_bench_1106.py run %s %s' % (k, part))
    print('RESULT: validate %s - %d FAIL' % ('OK' if not v.fail else 'FAILED', v.fail))
    return 1 if v.fail else 0


# ---------------------------------------------------------------- verify
def logs(tag):
    out = {}
    for n in (1, 2):
        p = '%s/%s/inst%d/KLHook.log' % (SOLO, tag, n)
        if os.path.isfile(p):
            out[n] = open(p, encoding='latin-1', errors='replace').read().splitlines()
    return out


def faults(lines):
    """Case-sensitive on purpose: 'EndOnFatal=1' / 'ContinueAsserts' lines are settings, not faults."""
    pat = re.compile(r'(EXCEPTION|FATAL|CRASH|ACCESS_VIOLATION)|access violation|memory fault|c0000005', re.I if False else 0)
    return [l for l in lines if pat.search(l)]


def dumps(tag, n):
    d = '%s/%s/inst%d' % (SOLO, tag, n)
    return [f for f in os.listdir(d) if f.lower().endswith(('.dmp', '.mdmp'))] if os.path.isdir(d) else []


def nums(l):
    return [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', l)]


def near(p, q, r):
    return sum((a - b) ** 2 for a, b in zip(p, q)) ** 0.5 <= r


def verify(k, part, tagbase=None):
    tag = '%s_%s' % (k, part)
    L = logs(tag)
    res = []
    if not L:
        print('RESULT: %s no logs under %s/%s' % (tag, SOLO, tag)); return 1

    def chk(name, cond, detail=''):
        res.append(cond); print('  %s %s %s' % ('PASS' if cond else 'FAIL', name, detail))
    print('verify %s' % tag)
    for n, lines in L.items():
        f = faults(lines)
        dm = dumps(tag, n)
        chk('inst%d no fault lines / dump files' % n, not f and not dm, ('first: ' + (f[0][:160] if f else dm[0])) if (f or dm) else '(%d log lines, 0 dumps)' % len(lines))
    if part == 'solo':
        a = L[1]
        # the census line ("botfill: round census") is logged only in an online FA round (klbotfill.c klbf_tick gate):
        # the 130 check lives in the online branch
        hel = []
        for l in a:
            m = re.search(r'heli: t=.*zheli=(\w+) vt=\w+ pos=\S*\((-?\d+), (-?\d+), (-?\d+)\)', l)
            if m and m.group(1) != '00000000':
                hel.append((l[:12], tuple(float(m.group(i)) for i in (2, 3, 4))))
        pad = (7300, 2249, 3500)
        if k in LC:
            if hel:
                d0 = sum((x - y) ** 2 for x, y in zip(hel[0][1], pad)) ** .5
                d1 = min(sum((x - y) ** 2 for x, y in zip(h[1], pad)) ** .5 for h in hel)
                chk('ZHeli moves toward (7300,2249,3500)', d1 < d0 * 0.5, 'first %s %.0f m away, closest %.0f m (%d samples; stock hang was 15394,6942,18351)' % (hel[0][0], d0, d1, len(hel)))
            else:
                chk('ZHeli moves toward (7300,2249,3500)', False, 'no "heli: t=" line with a ZHeli (is [Heli] Probe=2 in the run ini?)')
            eye = (7093, 2181, 2727)
            # klcam.c logs the render camera as "cam: ... eye X Y Z"; only the outro (after 0x19 -> 0x1f) counts
            i0 = next((i for i, l in enumerate(a) if re.search(r'session: state \S+ -> 0x1f', l)), len(a))
            eyes = [tuple(float(m.group(j)) for j in (1, 2, 3)) for l in a[i0:] if ' cam:' in l for m in [re.search(r'\beye (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)', l)] if m]
            hit = [e for e in eyes if near(e, eye, 150)]
            chk('escape camera eye about (7093,2181,2727) in the outro', bool(hit), '%d outro cam eyes, %s' % (len(eyes), ('e.g. (%.0f,%.0f,%.0f)' % hit[0]) if hit else ('last (%.0f,%.0f,%.0f)' % eyes[-1]) if eyes else 'none'))
        st = [m.group(1) for l in a for m in [re.search(r'session: state \S+ -> (0x[0-9a-f]+)', l)] if m]
        chk('session reaches 0x1f then 0x20', '0x1f' in st and '0x20' in st[st.index('0x1f'):] if '0x1f' in st else False, 'states seen: %s' % ' '.join(st[-8:]))
        van = [l[:140] for l in a if 'van card' in l or 'vehicle state' in l]
        print('  info vehicle lines: %d, last: %s' % (len(van), van[-1] if van else '-'))
        if k in LC:
            print('  info grey screen: LOOK at the shots (KLShot_inst1_NN.jpg in %s/%s); event times below' % (SOLO, tag))
            ev = [l[:12] + ' ' + l[13:100] for l in a if re.search(r'session: state \S+ -> 0x(1f|20)|BENCH1106|hud: van card.*state (3|5)', l)]
            for e in ev[:40]:
                print('       ', e)
            import glob
            for s in sorted(glob.glob('%s/%s/KLShot_inst1_*.jpg' % (SOLO, tag)))[:90]:
                print('        shot %s %s' % (time.strftime('%H:%M:%S', time.localtime(os.path.getmtime(s))), os.path.basename(s)))
            # civilian speech is the engine's own sound-bank playback: the hook logs none, so no log check is possible
            print('  info women / civilian voices: not logged by the hook; LOOK at the shots and listen')
            sq = [l for l in a if re.search(r'squad|spawn', l, re.I)]
            print('  info squad/spawn lines: %d (first: %s)' % (len(sq), sq[0][:140] if sq else '-'))
    if k == 'dd10s1106':
        a = L[1]
        mem = [(m.group(1), float(m.group(2))) for l in a for m in [re.search(r'(\S+) memory: every 10 s: .*largest piece ([\d.]+) MB', l)] if m]
        if mem:
            lo = min(x[1] for x in mem)
            chk('largest free block stays above the ~14.4 MB baseline', lo > 14.4, 'min %.1f MB, last %.1f MB, %d samples' % (lo, mem[-1][1], len(mem)))
        else:
            chk('largest free block logged', False, 'no "memory: every 10 s" lines ([Memory] Log=1)')
        sn = [l[:150] for l in a if re.search(r'wav|whd|sound bank|SND', l, re.I) and re.search(r'fail|bad|error|missing|refus', l, re.I)]
        chk('no sound/WAV load error lines', not sn, sn[0] if sn else '(audio itself: owner ear check, the bench is silent by design)')
    if part in ('online', 'long'):
        for n, lines in L.items():
            st = [m.group(1) for l in lines for m in [re.search(r'session: state \S+ -> (0x[0-9a-f]+)', l)] if m]
            # a round ends 0x19 -> 0x1f; after the match's last round 0x1f goes to 0x28 (match over), not to the shop 0x20
            want = 3 if part == 'long' else 2
            ends = sum(1 for i in range(1, len(st)) if st[i] == '0x1f' and st[i - 1] == '0x19')
            # the online script ends ~30 s into the last round (lcglass1106 11-06: round 2 entered, never ended), so the gate is
            # "round N entered" (N entries into 0x19) plus N-1 completed round ends; a full last round is the long part's job
            ins = st.count('0x19')
            chk('inst%d reaches round %d (%d+ entries into 0x19, %d+ round ends)' % (n, want, want, want - 1), ins >= want and ends >= want - 1,
                'entries %d, round ends %d, shops %d, match over %s' % (ins, ends, st.count('0x20'), '0x28' in st))
        for n, lines in L.items():
            # round reset dwell: the stripped HavokShatterGlassConnectivity made 0x25 last 21-29 s per seat on DM05A (DD maps ~0.01 s)
            ts = [(l[:12], m.group(1), m.group(2)) for l in lines for m in [re.search(r'session: state (0x[0-9a-f]+) -> (0x[0-9a-f]+)', l)] if m]
            sec = lambda t: int(t[0:2]) * 3600 + int(t[3:5]) * 60 + float(t[6:12])
            dw = [sec(ts[i + 1][0]) - sec(ts[i][0]) for i in range(len(ts) - 1) if ts[i][2] == '0x25' and ts[i + 1][1] == '0x25']
            chk('inst%d round reset 0x25 under 8 s' % n, bool(dw) and max(dw) < 8, '0x25 dwell s: %s' % (', '.join('%.1f' % x for x in dw) or 'never reached'))
        if k in LC:
            rx = re.compile(r'botfill: round census: (\d+) ZFFActor')
            for n, lines in L.items():
                c = sorted({int(m.group(1)) for l in lines for m in [rx.search(l)] if m})
                chk('inst%d loads with census 130 (previously 116)' % n, 130 in c, 'census lines: %s' % (c or 'none'))
        a = L[1]
        bg = [l[:150] for l in a if 'botgate' in l and ('bots' in l)]
        chk('botgate decided for the slot', bool(bg), bg[-1] if bg else 'no botgate line')
        if k == 'dd10s1106':
            mem = [float(m.group(1)) for n_ in L.values() for l in n_ for m in [re.search(r'memory: every 10 s: .*largest piece ([\d.]+) MB', l)] if m]
            if mem:
                chk('largest free block stays above 14.4 MB over the long match', min(mem) > 14.4, 'min %.1f MB over %d samples (both seats)' % (min(mem), len(mem)))
    bad = res.count(False)
    print('RESULT: %s %s (%d checks, %d FAIL)' % (tag, 'PASS' if not bad else 'FAIL', len(res), bad))
    return 1 if bad else 0


# ---------------------------------------------------------------- run
def sh(cmd, **kw):
    print('  $ ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd), flush=True)
    return subprocess.run(cmd, **kw).returncode


def kl2_procs():
    """[(pid, working set KB)] for every kl2.exe, from tasklist's CSV."""
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    r = []
    for l in out.splitlines():
        f = [x.strip('"') for x in l.split('","')]
        if len(f) >= 5 and f[0].lower() == 'kl2.exe':
            r.append((int(f[1]), int(re.sub(r'\D', '', f[4]) or 0)))
    return r


def run(k, part):
    c = KITS[k]
    if validate(k):
        print('RESULT: not started - validate failed'); return 1
    parts = c['parts'] if part == 'all' else (part,)
    for p in parts:
        if p not in c['parts']:
            print('RESULT: not started - %s has parts %s' % (k, c['parts'])); return 1
    d, md, before = '%s/%s' % (KIT, k), mapdir(k), None
    before = snap(md)
    inst = [sys.executable, '%s/install.py' % c['stage']] + (['--game', DD] if k == 'dd10s1106' else []) if c['stage'] else None
    z = kl2_procs()
    if any(kb >= 1024 for _, kb in z):
        print('RESULT: not started - a live kl2.exe is running: %s' % z); return 1
    if z:
        # unkillable kl2.exe left at ~44 K (Access denied to Stop-Process) hold no game: install.py's own tasklist check
        # would refuse forever, so skip it only when every kl2.exe is such a zombie
        print('  ignoring zombie kl2.exe (working set < 1 MB): %s' % z, flush=True)
        if k in LC and inst:
            inst.append('--skip-run-check')
    rc_total = 0
    if inst:
        print('INSTALLING the stage into the LIVE game folder (undone at the end): %s' % md, flush=True)
        if sh(inst):
            print('RESULT: not started - install.py refused (nothing changed)'); return 1
    else:
        print('nothing installed: the bench runs on the live %s as it is' % md, flush=True)
    try:
        for p in parts:
            tag = '%s_%s' % (k, p)
            for i in (1, 2):
                os.makedirs('%s/%s/inst%d' % (SOLO, tag, i), exist_ok=True)
                import shutil
                shutil.copy2('%s/KLShopPage.ini' % d, '%s/%s/inst%d/KLShopPage.ini' % (SOLO, tag, i))
            if p == 'solo':
                args = ['--n', '1', '--secs', str(c['solo_secs']), '--ini1', '%s/solo.ini' % d, '--shots', '30-%d:20' % (c['solo_secs'] - 60), '--d3shots']
            else:
                secs = 2500 if p == 'long' else 1900
                args = ['--n', '2', '--secs', str(secs), '--gap', '45', '--relaunch', '2', '--ini1', '%s/online_host.ini' % d, '--ini2', '%s/online_join.ini' % d]
                if k in LC:
                    args += ['--shots', '60-%d:60' % (secs - 60), '--d3shots']
            cmd = [sys.executable, 'tools/kl_solo_test.py', '--hook', '%s/hook_test' % d, '--tag', tag, '--base', '%s/KLHook_base.ini' % d, '--owner-away'] + args
            with open('%s/%s_run.txt' % (d, p), 'w') as out:
                print('  run %s (log %s/%s_run.txt)' % (tag, d, p), flush=True)
                rc = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
            print('  bench exit %d' % rc, flush=True)
            rc_total |= verify(k, p)
    finally:
        if inst:
            print('UNDOING the stage (install.py --undo)', flush=True)
            r = sh(inst + ['--undo'])
        else:
            r = 0
        after = snap(md)
        same = {n: m for n, m in after.items() if not (c['tag'] and n.endswith(c['tag']))} == {n: m for n, m in before.items()}
        if not inst and not same:
            print('MAP FOLDER CHANGED during the run (nothing was installed): compare with the md5s above'); rc_total = 1
        elif r or not same:
            print('UNDO FAILED - run by hand: python "%s/install.py" --undo%s ; then compare with the md5s above' % (c['stage'], (' --game "%s"' % DD) if k == 'dd10s1106' else ''))
            rc_total = 1
        else:
            print('undo OK: every file in %s has its pre-run md5 again' % md)
    print('RESULT: %s run done, %s' % (k, 'ALL PASS' if not rc_total else 'see FAIL lines'))
    return rc_total


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return 2
    cmd = a[0]
    if cmd == 'gen':
        gen(); return 0
    if cmd == 'validate':
        return validate(a[1] if len(a) > 1 else 'all')
    if cmd == 'run' and len(a) > 1 and a[1] in KITS:
        return run(a[1], a[2] if len(a) > 2 else 'all')
    if cmd == 'verify' and len(a) > 1 and a[1] in KITS:
        parts = [a[2]] if len(a) > 2 else KITS[a[1]]['parts']
        return max(verify(a[1], p) for p in parts)
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
