#!/usr/bin/env python3
"""
n9_1106: the 9-player SMOOTHNESS bench kit (2026-11-06). One command per step; the live run waits for c9's "game free / n9 go".

    python tools/kl_n9_1106.py gen [--ship PREFIX]      (TEST twin of the live SHIP, see TWINS) write/refresh the kit C:/kl_build_1024/n9_1106 (reads the live KLHook.ini + zips, no game contact)
    python tools/kl_n9_1106.py validate                 DRY RUN: files, dll md5 + TEST markers, ini sections, script ops, live zip md5s vs gen. No launch.
    python tools/kl_n9_1106.py plan                     the map order (never-at-9 first) and the wall-time estimate
    python tools/kl_n9_1106.py run [MAP ...|all|arc] [--owner-away] [--again] [--secs N] [--allow-live-dll MD5PREFIX]
    python tools/kl_n9_1106.py summarize [MAP ...|all]  smoothness table from the logs of the last runs (no game contact)

WHAT IT IS
  For each Fragile Alliance map (all except DM05A = Last Call, and everything in slot F07: DD07, DM03A, DD10): 1 host + 8 joiners on this
  PC through tools/kl_solo_test.py (--n 9 --gap 45 --gap2 60 --hang-secs 150 --relaunch 3 --park 1), one map at a time, then
  tools/kl_n9_smooth.py reads the nine KLHook.logs and gives SMOOTH / HITCHY / FAIL per seat and per map. A final Arcade (offline, 1 seat,
  DD01) reference run gives the floor for the same numbers (--ref).

THE BUILD UNDER TEST (said plainly)
  hook_test/dinput8.dll = C:/kl_build_1024/week_1028/sm1105e/hook_test/dinput8.dll, md5 5f52009d, the build_auto TEST twin of the live SHIP
  288fb016 (c9_1105e_install). How sure: the twin is named for it in kl_bench_1106.py (c9's own note) and carries the TEST markers, but I did
  not rebuild it from source; the SHIP<->TEST pairing is c9's statement, not something this tool can prove from the bytes (the two differ by klauto).
  `run` refuses unless the LIVE dinput8.dll is a SHIP in ACCEPT_LIVE (288fb016 only) or you pass --allow-live-dll <md5 prefix>: the benches swap
  the TEST dll in and put back "whatever was there", so a TEST leftover live (a bench was killed) would be restored as if it were the player's.

BASE INI: the kit's KLHook_base.ini is a COPY of the live <DD>/KLHook.ini made at gen time (md5 recorded in kit.json). Per-map host/joiner inis
  are the proven 9-seat templates of maps9_1026e (N9_DM01e = first 9/9 PASS) retargeted: [Expansion] Page=, the lobby RIGHT taps for the
  slot (SLOT_POS), the MAPS9 log line, one [Auto] with a budget, FrameLimit 30 fps, StallMs 120000, waitpeers 9 540000 30000.

SAFETY (all enforced in code)
  never launches kl2.exe except through kl_solo_test (only in `run`); refuses if kl2.exe is running; never writes into the game folder itself
  (kl_solo_test swaps the TEST dll in and restores it; this tool re-checks the live dll + ini md5 after every map and stops on a difference);
  never touches KL_PortBackup; never kills a process. A file <kit>/STOP stops the queue after the current map.
"""
import ctypes, hashlib, json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
KIT = 'C:/kl_build_1024/n9_1106'
DD = 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days'
SOLO = 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo'
TPL = 'C:/kl_build_1024/maps9_1026e'                       # M_DM01_host.ini / M_DM01_join.ini = the proven 9-seat pair
# live SHIP md5 prefix -> (its build_auto TEST twin, twin md5, label). gen picks the twin of the SHIP that is live (or --ship PREFIX).
TWINS = {'288fb016': ('C:/kl_build_1024/week_1028/sm1105e/hook_test/dinput8.dll', '5f52009dd89f0e4d732a2addbed3d652', 'SHIP c9_1105e_install (TEST twin 5f52009d)'),
         '727a73bb': ('C:/kl_build_1024/n9_twins/727a73bb/dinput8.dll', 'b6a697726b66ca7270921d6d4543005f',   # 6b's pf1106 hook_test (copied 11-06; 6b: 2-seat DD05+DM01 PASS)
                      'SHIP cda03a57 pics/perf (6b, 11-06; TEST twin b6a69772)')}
ACCEPT_LIVE = {k: v[2] for k, v in TWINS.items()}
HOOK_SRC, HOOK_MD5 = TWINS['288fb016'][:2]               # default when the live dll is no known SHIP (a bench is live): gen --ship picks another
SLOT_POS = {'F01': 0, 'F02': 1, 'F03': 2, 'F04': 3, 'F06': 4, 'F07': 5, 'F05': 6, 'F08': 7, 'F09': 8}
# (map, slot, page): same table as tools/kl_maps9_1026.py
MAPS = [('DD%02d' % i, 'F%02d' % i, 0) for i in range(1, 10)]
MAPS += [('DM01', 'F01', 2), ('DM02', 'F02', 2), ('DM03', 'F03', 2), ('DM06', 'F04', 2), ('DM09', 'F06', 2), ('DM03A', 'F07', 2)]
MAPS += [('DM05A', 'F01', 3), ('DM06B', 'F02', 3), ('DM01B', 'F03', 3), ('DM11B', 'F04', 3), ('DM07', 'F06', 3), ('DD10', 'F07', 3)]
EXCLUDE = {'DM05A'}                                        # Last Call (staged chain, c9's)
EXCLUDE_SLOT = {'F07'}                                     # DD07, DM03A, DD10 (slot F07: c9's slim stage / DD07 own work)
RAN_AT_9 = {'DM01', 'DD01'}                                # fallback when the solo/ folder cannot be scanned
OPS = set('waitwin settle tapuntil tap wait windows sel expect msg waitload waitstate waitvan waitpeers tele pos ents peek log pass fail label jump onwin onfail mouse'.split())
GAP, GAP2, HANG, RELAUNCH = 45, 60, 150, 3
OBS_MS = 300000                                            # host observation of the running round (template: 300000)
SECS = 1800                                                # kl_solo_test --secs budget per map (N9_DM01e queue used 30 min)
AUTO_EXIT = SECS - 60
TYPICAL_S = 17 * 60                                        # N9_DM01e 08:12 -> 08:28, N9_DD01f 10:14 -> 10:30 (lobby fill ~9 min, load, 300 s round)
BETWEEN_S = 60                                             # settle + checks between maps
ARC_SECS = 700


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='latin-1', newline='\n') as f:
        f.write(text)


def load(path):
    return open(path, encoding='latin-1').read()


# ---------------------------------------------------------------- map list and order
def maps_at_9():
    """Map folders that have a 9-seat run in the solo/ work folder (a tag with inst9 whose name carries the map; a LOWERCASE letter after the digits is a run letter: N9_DM01b = DM01, N9_DM01B = DM01B). Fallback RAN_AT_9."""
    found = set()
    try:
        for t in os.listdir(SOLO):
            if os.path.isdir(os.path.join(SOLO, t, 'inst9')):
                for m in re.findall(r'(D[DM]\d\d[A-Z]?)', t):
                    found.add(m)
    except OSError:
        pass
    return found or set(RAN_AT_9)


def map_list(ran=None):
    """-> [(map, slot, page, ran_at_9)] never-at-9 first, then the rest; table order inside each group."""
    ran = maps_at_9() if ran is None else ran
    ms = [(m, s, p) for m, s, p in MAPS if m not in EXCLUDE and s not in EXCLUDE_SLOT]
    first = [(m, s, p, False) for m, s, p in ms if m not in ran]
    last = [(m, s, p, True) for m, s, p in ms if m in ran]
    return first + last


def estimate(n_maps, with_arc=True):
    typ = n_maps * (TYPICAL_S + BETWEEN_S) + (ARC_SECS + BETWEEN_S if with_arc else 0)
    worst = n_maps * (SECS + BETWEEN_S) + (ARC_SECS + BETWEEN_S if with_arc else 0)
    return typ, worst


def hm(s):
    return '%d h %02d min' % (s // 3600, (s % 3600) // 60)


# ---------------------------------------------------------------- ini building
def parse_ini(text):
    """-> ordered [(section, [lines])]; a repeated section is merged into its first occurrence. Comment/blank lines kept in place."""
    secs, idx = [], {}
    cur = None
    pre = []
    for ln in text.splitlines():
        m = re.match(r'\s*\[([^\]]+)\]\s*$', ln)
        if m:
            name = m.group(1)
            if name not in idx:
                idx[name] = len(secs); secs.append((name, []))
            cur = secs[idx[name]][1]
        elif cur is None:
            pre.append(ln)
        else:
            cur.append(ln)
    return pre, secs


def set_key(lines, key, val):
    """Replace every 'key=...' line (last one wins in the game's reader, so keep ONE) or append."""
    out, done = [], False
    for ln in lines:
        if re.match(r'\s*%s\s*=' % re.escape(key), ln):
            if not done:
                out.append('%s=%s' % (key, val)); done = True
            continue
        out.append(ln)
    if not done:
        out.append('%s=%s' % (key, val))
    return out


def kv_last_wins(lines):
    """A merged section (the template repeated [Auto]) -> one line per key, the LAST value, first-seen position; comments dropped."""
    order, val = [], {}
    for ln in lines:
        m = re.match(r'\s*([A-Za-z0-9_.]+)\s*=(.*)$', ln)
        if m and not ln.lstrip().startswith(';'):
            if m.group(1) not in val:
                order.append(m.group(1))
            val[m.group(1)] = m.group(2)
    return ['%s=%s' % (k, val[k]) for k in order]


def script_lines(lines):
    """[Script] body -> list of commands (numbering dropped; comments dropped; blank dropped)."""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(';'):
            continue
        m = re.match(r'^\d+=(.*)$', s)
        out.append(m.group(1) if m else s)
    return out


def number(cmds):
    return ['%d=%s' % (i + 1, c) for i, c in enumerate(cmds)]


def retarget_host(cmds, name, slot, page):
    """Drop any earlier RIGHT/wait/MAPS9 block after 'log SOLO host lobby', insert the slot's taps, set the waitpeers/observation numbers."""
    out, i = [], 0
    while i < len(cmds):
        c = cmds[i]
        if c.startswith('tap RIGHT') or c.startswith('log MAPS9'):
            i += 1
            # the wait 900 that follows a RIGHT, and the 'windows' after the MAPS9 log
            if c.startswith('tap RIGHT') and i < len(cmds) and cmds[i] == 'wait 900':
                i += 1
            elif c.startswith('log MAPS9') and i < len(cmds) and cmds[i] == 'windows':
                i += 1
            continue
        if c.startswith('waitpeers'):
            c = 'waitpeers 9 540000 30000'
        elif re.match(r'wait 300000$', c):
            c = 'wait %d' % OBS_MS
        out.append(c)
        if c.startswith('log SOLO host lobby'):
            for _ in range(SLOT_POS[slot]):
                out += ['tap RIGHT', 'wait 900']
            out += ['log MAPS9 map row stepped %d x RIGHT -> slot %s, expect LOAD %s page %d rule %s' % (SLOT_POS[slot], slot, slot, page, name), 'windows']
        i += 1
    return out


def auto_section(secs_total):
    return ['Enable=1', 'Hooks=0', 'Nodes=0', 'EndHooks=1', 'CmdDrop=DefaultScene,AutoExit',
            'CmdAdd=-o DisableSplashScreens -o AutoExit=%d' % (secs_total - 60), 'StallMs=120000', 'MaxRunMs=%d' % ((secs_total - 70) * 1000),
            'LoadedMs=0', 'Unfocused=1', 'BlockReal=1', 'FirstChance=1', 'PosLogMs=5000']


PROBES_OFF = ('BotDeathProbe', 'CoverDump', 'CoverRing', 'MFProbe')


def build(tpl_text, who, name, slot, page, secs_total=SECS):
    """Per-map overlay: merged template sections, one [Auto], Page=, retargeted host script. A joiner gets [Script] unchanged."""
    pre, secs = parse_ini(tpl_text)
    out = ['; n9_1106 %s %s: slot %s page %d, 9 seats, built on the proven maps9_1026e %s template' % (name, who, slot, page, who)]
    have = {n for n, _ in secs}
    for sec, lines in secs:
        if sec == 'Script':
            continue
        if sec == 'Expansion':
            lines = set_key(set_key(lines, 'Page', str(page)), 'Log', '1')
        if sec == 'Auto':
            lines = auto_section(secs_total)
        else:
            lines = kv_last_wins(lines) if sec in ('Lobby', 'HUD', 'Sync', 'FrameLimit', 'Auto') else [l for l in lines if l.strip() and not l.lstrip().startswith(';')]
        out.append('[%s]' % sec); out += lines
    if 'Expansion' not in have:
        out += ['[Expansion]', 'Page=%d' % page, 'Log=1']
    if 'FrameLimit' not in have:                            # 9 uncapped instances starve each other (N9_DM01d)
        out += ['[FrameLimit]', 'Enable=1', 'SwapChain=1', 'Fps=30']
    if 'Auto' not in have:
        out += ['[Auto]'] + auto_section(secs_total)
    for sec in PROBES_OFF:                                  # TEST-only probes default on; SHIP has them off (re/mp_smooth_audit_1106.md: CoverDump's
        if sec not in have:                                 # round-start burst = the 300 ms spikes), so 9-seat numbers match what players get
            out += ['[%s]' % sec, 'Enable=0']
    scr =[l for sec, ls in secs if sec == 'Script' for l in script_lines(ls)]
    if who == 'host':
        scr = retarget_host(scr, name, slot, page)
    out += ['[Script]'] + number(scr)
    return '\n'.join(out) + '\n'


def arc_ini():
    """Offline Arcade reference: 1 seat on stock DD01 (the ARC1_DD01 script), stands still, cops barely hurt it (round runs to its end)."""
    s = ['waitwin CampaignMenu 180000', 'settle 15 150 60000', 'tapuntil ESCAPE MainMenu 10000 3', 'settle 8 150 30000', 'wait 1500', 'tap DOWN', 'wait 1200',
         'tapuntil RETURN HeistModeMenu 15000 2', 'settle 8 150 30000', 'wait 3000', 'windows', 'tap RETURN', 'waitwin HeistPlayMenu 8000', 'wait 3000', 'windows',
         'sel HeistLevel 0xceceec 0', 'wait 2500', 'expect 0xceceec 0', 'log N9ARC starting entry 0 = DD01 (F01) page 0', 'msg HeistLevel StartGame',
         'waitload 300000', 'log N9ARC level loaded: DD01', 'wait 23000', 'peek 0x168e598+0x70 session-state-must-be-0x19', 'pos spawn']
    for i in range(1, 11):
        s += ['wait 30000', 'pos t%d' % (30 * i)]
    s += ['log N9ARC DD01 observed 300 s', 'pass 1000']
    t = ['; n9_1106 Arcade reference: OFFLINE, 1 seat, DD01 page 0, stands still (ARC1_DD01 script)', '[Expansion]', 'Page=0', 'Log=1',
         '[Balance]', 'CopToYou=0.001', 'PointBlankToYou=0.0', '[Auto]'] + auto_section(ARC_SECS) + ['[Script]'] + number(s)
    return '\n'.join(t) + '\n'


# ---------------------------------------------------------------- live state
def zip_files(slot):
    return ['%s_Main.zip' % slot, '%s_Main.bots.zip' % slot]


def map_dir(name):
    return '%s/KLExpansion/Maps/%s' % (DD, name)


def zip_md5s(name, slot):
    d, out = map_dir(name), {}
    for f in zip_files(slot):
        p = '%s/%s' % (d, f)
        out[f] = md5(p) if os.path.isfile(p) else None
    return out


def live_state():
    return {'dll': md5('%s/dinput8.dll' % DD) if os.path.isfile('%s/dinput8.dll' % DD) else None,
            'ini': md5('%s/KLHook.ini' % DD) if os.path.isfile('%s/KLHook.ini' % DD) else None}


def kl2_running():
    """kl2.exe that really run: thread-less lingering entries (killed benches, cleared by a reboot) do not count (kl_autotest.running)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kl_autotest
    return len(kl_autotest.running())


def idle_s():
    class L(ctypes.Structure):
        _fields_ = [('s', ctypes.c_uint), ('t', ctypes.c_uint)]
    l = L(8, 0)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(l))
    return ((ctypes.windll.kernel32.GetTickCount() - l.t) & 0xffffffff) // 1000


# ---------------------------------------------------------------- gen
def gen(ship=None):
    import shutil
    ld = live_state()['dll'] or ''
    ship = ship or next((k for k in TWINS if ld.startswith(k)), None)
    if ship not in TWINS:
        raise SystemExit('gen: live dll %s is no known SHIP (%s): pass --ship PREFIX' % (ld[:8], ', '.join(TWINS)))
    src, _, label = TWINS[ship]
    os.makedirs('%s/hook_test' % KIT, exist_ok=True)
    shutil.copy2(src, '%s/hook_test/dinput8.dll' % KIT)
    print('gen: SHIP %s -> %s' % (ship, label))
    shutil.copy2('%s/KLHook.ini' % DD, '%s/KLHook_base.ini' % KIT)          # snapshot of the CURRENT live ini, taken now
    shutil.copy2('%s/KLShopPage.ini' % DD, '%s/KLShopPage.ini' % KIT)
    th, tj = load('%s/M_DM01_host.ini' % TPL), load('%s/M_DM01_join.ini' % TPL)
    shutil.copy2('%s/M_DM01_host.ini' % TPL, '%s/tpl_host.ini' % KIT)
    shutil.copy2('%s/M_DM01_join.ini' % TPL, '%s/tpl_join.ini' % KIT)
    ml = map_list()
    zips = {}
    for m, s, p, _ in ml:
        write('%s/%s_host.ini' % (KIT, m), build(th, 'host', m, s, p))
        write('%s/%s_join.ini' % (KIT, m), build(tj, 'join', m, s, p))
        zips[m] = zip_md5s(m, s)
    write('%s/arc_ref.ini' % KIT, arc_ini())
    meta = {'made': time.strftime('%Y-%m-%d %H:%M:%S'), 'ship': ship, 'hook_md5': md5('%s/hook_test/dinput8.dll' % KIT), 'base_ini_md5': md5('%s/KLHook_base.ini' % KIT),
            'live_at_gen': live_state(), 'order': [dict(map=m, slot=s, page=p, ran_at_9=r) for m, s, p, r in ml], 'zips': zips,
            'ran_at_9': sorted(maps_at_9())}
    write('%s/kit.json' % KIT, json.dumps(meta, indent=1))
    typ, worst = estimate(len(ml))
    print('gen: kit %s: %d maps (%s), TEST dll %s, base ini %s (live ini copy)' % (KIT, len(ml), ' '.join(m for m, *_ in ml), meta['hook_md5'][:8], meta['base_ini_md5'][:8]))
    print('gen: live dll now %s (accepted SHIP for run: %s)' % ((meta['live_at_gen']['dll'] or '-')[:8], ', '.join(ACCEPT_LIVE)))
    print('gen: estimate %s typical, %s worst (%d maps + Arcade reference)' % (hm(typ), hm(worst), len(ml)))
    return 0


def meta_of():
    p = '%s/kit.json' % KIT
    return json.load(open(p)) if os.path.isfile(p) else None


# ---------------------------------------------------------------- validate
class V:
    def __init__(s):
        s.fail = 0

    def ok(s, cond, text, warn=False):
        if not cond and not warn:
            s.fail += 1
        print('  %-4s %s' % ('PASS' if cond else ('WARN' if warn else 'FAIL'), text))
        return cond


def validate(quiet_run=False):
    v = V()
    print('validate (dry run: no game launch, no write into the game folder)')
    v.ok(os.path.isdir(DD), 'Dog Days folder')
    v.ok(os.path.isfile('%s/kl2.exe' % DD), 'kl2.exe present')
    n = kl2_running()
    v.ok(n == 0, 'no kl2.exe running (%d now; `run` refuses while one runs)' % n, warn=True)
    v.ok(os.path.isfile(os.path.join(ROOT, 'tools/kl_solo_test.py')), 'tools/kl_solo_test.py')
    v.ok(os.path.isfile(os.path.join(ROOT, 'tools/kl_n9_smooth.py')), 'tools/kl_n9_smooth.py')
    v.ok(os.path.isdir(SOLO), 'solo work folder')
    meta = meta_of()
    if not v.ok(meta is not None, 'kit.json (run `gen` first)'):
        print('RESULT: validate FAILED - %d FAIL' % v.fail); return 1
    dll = '%s/hook_test/dinput8.dll' % KIT
    if v.ok(os.path.isfile(dll), 'bench dll'):
        data = open(dll, 'rb').read()
        ship = meta.get('ship', '288fb016'); want = TWINS.get(ship, TWINS['288fb016'])[1]
        v.ok(hashlib.md5(data).hexdigest() == want, 'dll md5 %s = TEST twin %s of SHIP %s' % (hashlib.md5(data).hexdigest()[:8], want[:8], ship))
        v.ok(data.count(b'(TEST)') >= 3 and b"klauto's scripted keys" in data, 'dll carries the TEST markers ((TEST) x%d + klauto strings)' % data.count(b'(TEST)'))
        v.ok(2_500_000 < len(data) < 2_700_000, 'dll size %.2f MB (about 2.59 MB)' % (len(data) / 1e6))
    live = live_state()
    ld = live['dll'] or ''
    acc = [k for k in ACCEPT_LIVE if ld.startswith(k)]
    v.ok(bool(acc), 'live dinput8.dll md5 %s %s' % (ld[:8], ('= ' + ACCEPT_LIVE[acc[0]]) if acc else '(not an accepted SHIP: `run` refuses; a bench or a TEST leftover may be live)'), warn=True)
    base = '%s/KLHook_base.ini' % KIT
    if v.ok(os.path.isfile(base), 'base ini snapshot (md5 %s)' % (md5(base)[:8] if os.path.isfile(base) else '-')):
        txt = load(base)
        v.ok(md5(base) == meta['base_ini_md5'], 'base ini unchanged since gen')
        v.ok(live['ini'] == meta['live_at_gen']['ini'], 'live KLHook.ini unchanged since gen (md5 %s vs gen %s; a newer live ini is NOT in the kit: rerun gen)' % ((live['ini'] or '-')[:8], (meta['live_at_gen']['ini'] or '-')[:8]), warn=True)
        for sec in ('Expansion', 'Lobby', 'Bots', 'Redirect.2', 'Redirect.3', 'Redirect'):
            v.ok('[%s]' % sec in txt, 'base ini has [%s]' % sec)
        for key in ('AssertSoft', 'ClientBuild', 'ClientRewrite', 'ClientRingSync'):
            v.ok(re.search(r'^%s' % key, txt, re.M) is not None, 'base ini has cover line %s*' % key, warn=True)
    v.ok(os.path.isfile('%s/KLShopPage.ini' % KIT), 'KLShopPage.ini copy (staged into solo/<TAG>/inst1..9 by run)')
    for e in meta['order']:
        m, s = e['map'], e['slot']
        cur = zip_md5s(m, s)
        v.ok(cur == meta['zips'][m] and all(cur.values()), '%s: live %s md5 %s (gen %s)' % (m, ' '.join(zip_files(s)), '/'.join((x or '-')[:6] for x in cur.values()), '/'.join((x or '-')[:6] for x in meta['zips'][m].values())))
        for who in ('host', 'join'):
            p = '%s/%s_%s.ini' % (KIT, m, who)
            if not v.ok(os.path.isfile(p), '%s file' % os.path.basename(p)):
                continue
            t = load(p)
            scr = [l for sec, ls in parse_ini(t)[1] if sec == 'Script' for l in script_lines(ls)]
            bad = sorted({c.split()[0] for c in scr if c.split() and c.split()[0] not in OPS})
            v.ok(not bad and len(scr) > 20, '%s: %d script lines, ops known%s' % (os.path.basename(p), len(scr), (' UNKNOWN %s' % bad) if bad else ''))
            v.ok(len(re.findall(r'^\[Script\]', t, re.M)) == 1 and len(re.findall(r'^\[Auto\]', t, re.M)) == 1, '%s: one [Script], one [Auto]' % os.path.basename(p))
            v.ok(any(c.startswith('pass') for c in scr), '%s: has pass' % os.path.basename(p))
            v.ok(re.search(r'^Page=%d$' % e['page'], t, re.M) is not None, '%s: Page=%d' % (os.path.basename(p), e['page']))
            if who == 'host':
                v.ok(sum(1 for c in scr if c == 'tap RIGHT') == SLOT_POS[s], '%s: %d x tap RIGHT for slot %s' % (os.path.basename(p), SLOT_POS[s], s))
                v.ok(any(c.startswith('waitpeers 9 540000') for c in scr), '%s: waitpeers 9 540000 30000' % os.path.basename(p))
            v.ok('Fps=30' in t and 'StallMs=120000' in t, '%s: FrameLimit Fps=30, StallMs=120000' % os.path.basename(p))
    ap = '%s/arc_ref.ini' % KIT
    v.ok(os.path.isfile(ap) and 'pass 1000' in load(ap), 'arc_ref.ini (Arcade reference, DD01)')
    typ, worst = estimate(len(meta['order']))
    print('  info %d maps, never-at-9 first: %s | at 9 before: %s' % (len(meta['order']), ' '.join(e['map'] for e in meta['order'] if not e['ran_at_9']), ' '.join(e['map'] for e in meta['order'] if e['ran_at_9'])))
    print('  info estimate %s typical (%d min a map), %s worst (%d min budget a map), incl. the Arcade reference' % (hm(typ), TYPICAL_S // 60, hm(worst), SECS // 60))
    print('  command: python tools/kl_n9_1106.py run all --owner-away')
    print('RESULT: validate %s - %d FAIL' % ('OK' if not v.fail else 'FAILED', v.fail))
    return 1 if v.fail else 0


# ---------------------------------------------------------------- run / summarize
def tag_of(m):
    return 'N9S_%s' % m


def summarize(names, refs=('N9S_ARC_DD01',)):
    import kl_n9_smooth as sm
    meta = meta_of()
    order = [e['map'] for e in meta['order']] if meta else [m for m, *_ in map_list()]
    sel = order if not names or names == ['all'] else names
    rows, lines = [], []
    ref_list = [r for r in refs if os.path.isdir(os.path.join(SOLO, r))]
    worst = 0
    for m in sel + (['ARC_DD01'] if os.path.isdir(os.path.join(SOLO, 'N9S_ARC_DD01')) and names in ([], ['all']) else []):
        tag = tag_of(m)
        if not os.path.isdir(os.path.join(SOLO, tag)):
            rows.append((m, 'NOT RUN', '')); continue
        r = sm.analyse(tag, expect=1 if m == 'ARC_DD01' else 9)
        lines.append(sm.fmt_run(r, ref_list if m != 'ARC_DD01' else ()))
        rows.append((m, r['verdict'], r))
        worst = max(worst, {'SMOOTH': 0, 'HITCHY': 1, 'FAIL': 2}.get(r['verdict'], 0))
    print('\n'.join(lines))
    print('--- n9_1106 per map')
    for m, v, _ in rows:
        print('  %-7s %s' % (m, v))
    cnt = {k: sum(1 for _, v, _ in rows if v == k) for k in ('SMOOTH', 'HITCHY', 'FAIL', 'NOT RUN')}
    print('RESULT: n9_1106 %s' % ', '.join('%d %s' % (n, k) for k, n in cnt.items()))
    return 1 if cnt['FAIL'] else 0


def solo_cmd(m, host, join, hook, secs, owner_away, n=9):
    c = [sys.executable, 'tools/kl_solo_test.py', '--hook', hook, '--tag', tag_of(m), '--base', '%s/KLHook_base.ini' % KIT, '--n', str(n), '--secs', str(secs),
         '--ini1', host]
    if n > 1:
        c += ['--gap', str(GAP), '--gap2', str(GAP2), '--hang-secs', str(HANG), '--relaunch', str(RELAUNCH), '--park', '1', '--ini2', join]
    if owner_away:
        c.append('--owner-away')
    return c


def run(args):
    import shutil
    owner_away, again = '--owner-away' in args, '--again' in args
    secs = SECS
    allow = None
    names = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--secs':
            secs = int(args[i + 1]); i += 1
        elif a == '--allow-live-dll':
            allow = args[i + 1]; i += 1
        elif not a.startswith('--'):
            names.append(a)
        i += 1
    if validate():
        print('RESULT: not started - validate failed'); return 1
    meta = meta_of()
    order = [e for e in meta['order']]
    arc = 'arc' in names
    if names in ([], ['all']):
        names, arc = [e['map'] for e in order], True
    sel = [e for e in order if e['map'] in names]
    ld = live_state()['dll'] or ''
    if not any(ld.startswith(k) for k in ACCEPT_LIVE) and not (allow and ld.startswith(allow)):
        print('RESULT: not started - live dinput8.dll md5 %s is not an accepted SHIP (%s); a bench or TEST leftover is live. Pass --allow-live-dll <md5 prefix> to accept it.' % (ld[:8], ', '.join(ACCEPT_LIVE)))
        return 1
    if kl2_running():
        print('RESULT: not started - kl2.exe is running'); return 1
    if not owner_away and idle_s() < 300:
        print('RESULT: not started - owner input %d s ago (use --owner-away if the owner said they are away)' % idle_s()); return 1
    before = live_state()
    done_p = '%s/done.json' % KIT
    done = json.load(open(done_p)) if os.path.isfile(done_p) else {}
    jobs = [(e['map'], e['slot']) for e in sel] + ([('ARC_DD01', 'F01')] if arc else [])
    # the Arcade reference goes FIRST when it is asked for alone, otherwise last (the 9-seat maps are the point)
    t0 = time.time()
    rc_all = 0
    for k, (m, slot) in enumerate(jobs):
        tag = tag_of(m)
        if tag in done and not again:
            print('skip %s (done at %s; --again reruns it)' % (m, done[tag])); continue
        if os.path.isfile('%s/STOP' % KIT):
            print('STOP file found: queue stopped before %s' % m); break
        if kl2_running():
            print('STOP: kl2.exe is running before %s (someone else started the game); nothing launched' % m); rc_all = 1; break
        if not owner_away and idle_s() < 300:
            print('STOP: owner input %d s ago before %s' % (idle_s(), m)); rc_all = 1; break
        if m != 'ARC_DD01':
            now = zip_md5s(m, slot)
            if now != meta['zips'][m]:
                print('STOP: live map zips of %s changed since gen (%s -> %s); rerun gen' % (m, meta['zips'][m], now)); rc_all = 1; break
        n = 1 if m == 'ARC_DD01' else 9
        for q in range(1, n + 1):
            d = '%s/%s/inst%d' % (SOLO, tag, q)
            os.makedirs(d, exist_ok=True)
            shutil.copy2('%s/KLShopPage.ini' % KIT, '%s/KLShopPage.ini' % d)
        host = '%s/arc_ref.ini' % KIT if m == 'ARC_DD01' else '%s/%s_host.ini' % (KIT, m)
        join = '%s/%s_join.ini' % (KIT, m)
        cmd = solo_cmd(m, host, join, '%s/hook_test' % KIT, ARC_SECS if n == 1 else secs, owner_away, n)
        print('[%d/%d] %s  (elapsed %s)' % (k + 1, len(jobs), m, hm(int(time.time() - t0))), flush=True)
        print('  $ ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd), flush=True)
        with open('%s/%s_run.txt' % (KIT, m), 'w') as out:
            rc = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
        txt = load('%s/%s_run.txt' % (KIT, m)) if os.path.isfile('%s/%s_run.txt' % (KIT, m)) else ''
        res = [l for l in txt.splitlines() if l.startswith('RESULT')]
        print('  bench exit %d | %s' % (rc, (res[-1] if res else 'no RESULT line')[:200]), flush=True)
        after = live_state()
        if after != before:
            print('STOP: live game files changed by the bench: dll %s -> %s, ini %s -> %s. Restore by hand (the bench puts the original back; a kill leaves the TEST dll).' % (
                (before['dll'] or '-')[:8], (after['dll'] or '-')[:8], (before['ini'] or '-')[:8], (after['ini'] or '-')[:8]))
            rc_all = 1; break
        done[tag] = time.strftime('%Y-%m-%d %H:%M')
        write(done_p, json.dumps(done, indent=1))
        if 'not started' in txt.lower() and 'RESULT: not started' in txt:
            print('STOP: kl_solo_test did not start (%s)' % res[-1][:160] if res else 'STOP: not started'); rc_all = 1; break
        if 'ABORTED' in txt:
            print('STOP: owner input aborted %s; rerun it with --again' % m); done.pop(tag, None); write(done_p, json.dumps(done, indent=1)); rc_all = 1; break
        time.sleep(BETWEEN_S)
    print('live dll/ini after the queue: %s' % ('byte-identical to before (dll %s, ini %s)' % ((before['dll'] or '-')[:8], (before['ini'] or '-')[:8]) if live_state() == before else 'DIFFERENT - see above'))
    summarize([e['map'] for e in sel] + (['ARC_DD01'] if arc else []))
    return rc_all


def plan():
    ml = map_list()
    typ, worst = estimate(len(ml))
    print('n9_1106 plan: %d maps, never run at 9 first' % len(ml))
    for i, (m, s, p, r) in enumerate(ml, 1):
        print('  %2d %-6s slot %s page %d  %s' % (i, m, s, p, 'ran at 9 before' if r else 'NEVER at 9'))
    print('  +  Arcade reference (ARC_DD01, 1 seat, %d s)' % ARC_SECS)
    print('wall time: %s typical (%d min a map: N9_DM01e/N9_DD01f took 16 min start to end, +1 min between), %s worst (budget %d min a map)' % (hm(typ), TYPICAL_S // 60, hm(worst), SECS // 60))
    print('excluded: %s (Last Call) and slot F07: DD07, DM03A, DD10' % ', '.join(sorted(EXCLUDE)))
    return 0


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    c, rest = a[0], a[1:]
    if c == 'gen':
        return gen(sys.argv[sys.argv.index('--ship') + 1] if '--ship' in sys.argv else None)
    if c == 'validate':
        return validate()
    if c == 'plan':
        return plan()
    if c == 'run':
        return run(rest)
    if c == 'summarize':
        return summarize(rest)
    print('unknown command %s' % c); return 2


if __name__ == '__main__':
    sys.exit(main())
