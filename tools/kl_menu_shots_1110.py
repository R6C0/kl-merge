#!/usr/bin/env python3
r"""kl_menu_shots_1110 - T9 menu-look screenshot kit (ML1 / ML5), OFFLINE tooling; the game only starts in `run`.

  python kl_menu_shots_1110.py gen      --kit DIR [--res auto|WxH]   write the kit (scripts, twins, pages.json)
  python kl_menu_shots_1110.py validate --kit DIR                    dry check of every generated [Script] (no game)
  python kl_menu_shots_1110.py run      --kit DIR [--variants deadmen,stock] [--runs menus,match] [--twin DLL] [--dry]
  python kl_menu_shots_1110.py post     --kit DIR [--out DIR]        shots -> <out>\<deadmen|stock>\<page>.png, ML5 proof, ML1 compare

Two runs per variant (variant = `[MenuLook] DeadMen=1` "deadmen" / `DeadMen=0` "stock"):
  menus : 1 seat, keyboard tour main menu -> Arcade pages -> Heister -> Options -> Mod settings (KLGuns)   (~4 min)
  match : 2 seats (System Link FA on DD05): lobby (Rows12), pause, round over, shop page I / II / hire / MOD CONTROLS (~15 min)
The tool uses tools/kl_solo_test.py with the TEST twin of the live SHIP dll (twins.json maps live md5 -> TEST dll; a live dll that
IS a TEST build runs as it is). Shots are the hook's back-buffer shots (--d3shots, JPG, every 2 s) matched to the `log MENULOOK <page>`
script lines by clock time. Nothing is installed; kl_solo_test swaps the dll in and restores it.
Guesses are marked GUESS (focus is assumed to stay on the parent window's row after ESC; the ML1 compare is a pixel heuristic)."""
import argparse, glob, hashlib, json, os, re, shutil, subprocess, sys, time

DD = os.environ.get('KL_DD', 'C:/Steam/steamapps/common/Kane & Lynch 2 - Dog Days')
SOLO = os.environ.get('KL_SOLO_ROOT', 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo')
SOLO_TEST = os.environ.get('KL_SOLO_TEST', 'C:/kl-merge/kl-merge/tools/kl_solo_test.py')
INV = os.environ.get('KL_MENU_INV', 'C:/kl-merge/kl-merge/re/menu_inventory_1110')
if not os.path.isdir(INV):                                           # the main checkout can lag behind: fall back to this tool's own repo copy
    _alt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 're', 'menu_inventory_1110')
    if os.path.isdir(_alt):
        INV = _alt
VARIANTS = ('deadmen', 'stock')
RUNS = ('menus', 'match')
# klauto.c script ops - validate refuses anything else
OPS = set('waitwin tapuntil tap settle wait log windows msg waitstate waitload waitpeers onwin onfail label jump pass fail '
          'sel expect waitvan tele goto face pos ents peek mouse'.split())
KEYS = set('RETURN ESCAPE UP DOWN LEFT RIGHT F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 F11 F12 TAB SPACE'.split())

# known SHIP -> TEST pairs (md5 prefix 8): (ship, test, path of the TEST dll copied into the kit, note)
TWINS = [
    ('30e3ffa8', '9d67cf1e', 'C:/kl_build_1024/merged_1110a/test/dinput8.dll', 'merged_1110a'),
    ('21e26651', '12c579ce', 'C:/kl_build_1024/merged_1110b/test/dinput8.dll', 'merged_1110b (d0 will install this SHIP)'),
    ('6e3ca2ad', 'fdaeaf10', 'C:/kl_build_1024/merged_1110c/test/dinput8.dll', 'merged_1110c'),
    ('258daf8e', '2b60f49d', 'C:/kl-merge/kl-merge/klhook/out_campaign_1110_test/dinput8.dll', 'campaign build'),
    ('a058eea8', 'bbe1118d', 'C:/kl-merge/kl-merge/klhook/out_menupick1110_test/dinput8.dll', 'menu sound picker build'),
]

# (run, page = file name, expected window, inventory windows for ML1, dwell seconds the page stays after its log line)
PAGES = [
    ('menus', 'main_menu', 'MainMenu', ['MainMenu'], 5),
    ('menus', 'heist_mode', 'HeistModeMenu', ['HeistModeMenu'], 5),
    ('menus', 'arcade_maps', 'HeistPlayMenu', ['HeistPlayMenu'], 5),
    ('menus', 'heister', 'KLHeister', ['KLHeister'], 5),
    ('menus', 'arcade_deadmen_maps', 'HeistPlayMenu2', ['HeistPlayMenu2'], 5),
    ('menus', 'arcade_campaign_maps', 'HeistPlayMenu3', ['HeistPlayMenu3'], 5),
    ('menus', 'options', 'OptionsMenu', ['OptionsMenu'], 5),
    ('menus', 'mod_settings', 'KLGuns', ['KLGuns'], 5),         # "Guns" and "Mod settings" are the same window (KLGuns)
    ('match', 'lobby', 'FALobby', ['FALobby'], 5),
    ('match', 'lobby_map', 'FALobby', ['FALobby'], 4),
    ('match', 'pause', None, ['IngamePauseFA', 'IngamePauseHeist'], 5),
    ('match', 'roundover', None, ['FARoundSummary', 'HeistStatus', 'FAStatus'], 3),
    ('match', 'shop_page1', 'FABuyWeaponsNewWeapon', ['FABuyWeaponsNewWeapon'], 3),
    ('match', 'shop_page2', 'FABuyWeaponsNewWeapon', ['FABuyWeaponsNewWeapon'], 3),
    ('match', 'shop_hire', 'FABuyWeaponsNewWeapon', ['FABuyWeaponsNewWeapon'], 3),
    ('match', 'shop_controls', 'FABuyWeaponsNewWeapon', ['FABuyWeaponsNewWeapon'], 3),
]
NOT_COVERED = [
    ('Guns (separate page)', 'KLGuns IS the Mod settings window; one page, shot as mod_settings'),
    ('shop main / category lists', 'the shop lasts 30 s; page I is the weapon list, main + category are skipped to fit page II / hire / controls'),
    ('MOD CONTROLS if the 30 s run out', 'taken as the 4th F2 of the first shop; the shot then shows a closed shop (post flags a missing log line / dwell)'),
    ('lobby with more than 2 seats', 'the lobby is the 2-seat Rows12 lobby'),
]

AUTO = """[Auto]
Enable=1
Hooks=0
Nodes=0
EndHooks=1
CmdDrop=DefaultScene,AutoExit
CmdAdd=-o DisableSplashScreens -o AutoExit=1950
StallMs=300000
MaxRunMs=1940000
LoadedMs=0
Unfocused=1
BlockReal=1
FirstChance=1
"""


class S:
    """tiny [Script] builder: numbered lines, comment lines kept out of the numbering"""
    def __init__(self):
        self.l = []

    def __call__(self, line):
        self.l.append(line)

    def tap(self, key, n=1, gap=700):
        for _ in range(n):
            self('tap ' + key); self('wait %d' % gap)

    def page(self, page, dwell):
        self('log MENULOOK ' + page)
        self('wait %d' % int(dwell * 1000))

    def text(self):
        out, k = ['[Script]'], 0
        for x in self.l:
            if x.startswith(';'):
                out.append(x); continue
            k += 1; out.append('%d=%s' % (k, x))
        return '\n'.join(out) + '\n'


def head(s):
    s('onwin ShowAchievements bail')              # a wrong DOWN count must never press RETURN on Achievements (A1 crash page)
    s('onfail bail 12')                           # a page not reached: stop the tour, keep the shots taken so far
    s('waitwin CampaignMenu 180000')
    s('wait 1500')
    s('tap ESCAPE')
    s('waitwin MainMenu 15000')
    s('wait 3500')


def menus_script():
    s = S()
    head(s)
    s.page('main_menu', 5)
    s.tap('DOWN', 1, 1200)                                            # Play -> Heist (Arcade)
    s('tapuntil RETURN HeistModeMenu 15000 2'); s('wait 1500')
    s.page('heist_mode', 5)
    s('tapuntil RETURN HeistPlayMenu 8000 2'); s('wait 1500')         # row 0 Start Heist = stock Arcade maps
    s.page('arcade_maps', 5)
    s('tap ESCAPE'); s('waitwin HeistModeMenu 8000'); s('wait 1500')
    s.tap('DOWN', 5, 500); s('wait 800')                              # GUESS: the parent keeps its focus row after ESC; 5 DOWN = Heister
    s('tapuntil RETURN KLHeister 8000 2'); s('wait 1500')
    s.page('heister', 5)
    s('tap ESCAPE'); s('waitwin HeistModeMenu 8000'); s('wait 1500')
    s.tap('DOWN', 1, 800)                                             # -> Dead Men maps
    s('tapuntil RETURN HeistPlayMenu2 8000 2'); s('wait 1500')
    s.page('arcade_deadmen_maps', 5)
    s('tap ESCAPE'); s('waitwin HeistModeMenu 8000'); s('wait 1500')
    s.tap('DOWN', 1, 800)                                             # -> Dead Men campaign
    s('tapuntil RETURN HeistPlayMenu3 8000 2'); s('wait 1500')
    s.page('arcade_campaign_maps', 5)
    # two ESC steps, each waited for: 'tapuntil ESCAPE MainMenu' from page 3 stops with 'off route' (klauto.c C_TAPUNTIL: top = HeistModeMenu is
    # neither the source nor the target page) and would drop the tour at 'bail' before Options / Mod settings
    s('tap ESCAPE'); s('waitwin HeistModeMenu 8000'); s('wait 1500')
    s('tap ESCAPE'); s('waitwin MainMenu 8000'); s('wait 2000')
    s.tap('DOWN', 3, 800)                                             # GUESS: MainMenu keeps Heist (row 1); +3 = Options (row 4), Achievements passed without RETURN
    s('tapuntil RETURN OptionsMenu 15000 2'); s('wait 1500')
    s.page('options', 5)
    s.tap('DOWN', 8, 500); s('wait 800')                              # OptionsMenu rows: Game Video Audio Mouse Keys Controls Tips Credits [Mod settings]
    s('tapuntil RETURN KLGuns 8000 2'); s('wait 1500')
    s.page('mod_settings', 5)
    s('pass 3000')
    s('label bail')
    s('log MENULOOK tour stopped: a page was not reached')
    s('tap ESCAPE')
    s('wait 1500')
    s('fail MENULOOK a page was not reached')
    return s.text()


def match_host_script():
    s = S()
    head(s)
    s('log SOLO host at MainMenu')
    s.tap('DOWN', 2, 1500)                                            # proven route: Online
    s('tapuntil RETURN OnlineMenu 15000 2'); s('wait 3000')
    s.tap('DOWN', 1, 1500)
    s('tapuntil RETURN SystemLink 15000 2'); s('wait 3000')
    s.tap('DOWN', 2, 1500)                                            # Create Game
    s('tapuntil RETURN SystemLinkCreate 15000 2'); s('wait 1500')
    s('tap RETURN')                                                   # FA
    s('waitwin FALobby 60000'); s('wait 2500')
    s.page('lobby', 5)
    s.tap('RIGHT', 6, 900)                                            # map row 6 x RIGHT -> slot F05 (DD05), as the proven MAPS9 script
    s.page('lobby_map', 4)
    s('waitpeers 2 600000 10000'); s('wait 1500')
    s('tap RETURN'); s('wait 3000')                                   # Ready (host)
    s('waitload 300000')
    s('log SOLO match started')
    s('waitstate 0x19 120000')
    s('wait 14000')
    s('tap ESCAPE'); s('wait 2500')                                   # GUESS: Esc opens IngamePauseFA in an online round (it does not pause the round)
    s.page('pause', 5)
    s('tap ESCAPE'); s('wait 2000')
    s('waitstate 0x1f 900000')
    s('wait 2500')
    s.page('roundover', 3)
    s('waitstate 0x20 120000')
    s('wait 2000')
    s('onfail shopskip 6')
    s('msg MercsFAStatusReadyHeistLBStatus ZW_SELECT3')
    s('waitwin FABuyWeaponsNew 15000')
    s('settle 5 150 10000')
    s('tapuntil RETURN FABuyWeaponsNewCategory 2500 8')
    s('settle 5 150 3000')
    s('tapuntil RETURN FABuyWeaponsNewWeapon 2500 8')
    s('settle 5 150 3000')
    s.page('shop_page1', 3)
    s('tap F2'); s('wait 1800')
    s.page('shop_page2', 3)
    s('tap F2'); s('wait 1800')
    s.page('shop_hire', 3)
    s('tap F2'); s('wait 1800')
    s.page('shop_controls', 3)
    s('tap ESCAPE'); s('wait 1000')
    s('tap ESCAPE'); s('wait 1000')
    s('label shopskip')
    s('waitstate 0x19 120000')
    s('wait 5000')
    s('pass 3000')
    s('label bail')
    s('tap ESCAPE')
    s('wait 1500')
    s('fail MENULOOK a page was not reached')
    return s.text()


# the proven client of the shoplook / PD2R benches (shoplook_1109\src\PD2R_DD05_join.ini), shortened to the shop-1 / round-2 path
JOIN = """[Script]
1=waitwin CampaignMenu 180000
2=log SOLO client at CampaignMenu
3=wait 1500
4=tap ESCAPE
5=label mm
6=onwin ShowAchievements back_mm
7=waitwin MainMenu 30000
8=wait 4000
9=windows
10=tap DOWN
11=wait 2000
12=tap DOWN
13=wait 2000
14=tap RETURN
15=waitwin OnlineMenu 15000
16=label om
17=onwin FAShowRules back_om
18=wait 4000
19=windows
20=tap DOWN
21=wait 2000
22=tap RETURN
23=waitwin SystemLink 15000
24=log SOLO client at SystemLink
25=windows
26=wait 3000
27=tap DOWN
28=wait 1500
29=tap RETURN
30=waitwin SystemLinkFindGame 20000
31=wait 1500
32=windows
33=tap RETURN
34=waitwin SystemLinkServerBrowser 30000
35=wait 15000
36=windows
37=tap RETURN
38=waitwin FALobby 90000
39=wait 3000
40=log SOLO client joined
41=windows
42=tap RETURN
43=wait 3000
44=windows
45=waitload 1400000
46=log SOLO match started
47=windows
48=wait 15000
49=windows
50=log client round 1 running, waiting for the shop (0x20)
51=waitstate 0x1f 600000
52=waitstate 0x20 120000
53=wait 2000
54=onfail pqafter 6
55=msg MercsFAStatusReadyHeistLBStatus ZW_SELECT3
56=waitwin FABuyWeaponsNew 15000
57=settle 5 150 10000
58=tapuntil RETURN FABuyWeaponsNewCategory 2500 8
59=settle 5 150 3000
60=wait 1000
61=tap F2
62=waitwin FABuyWeaponsNewWeapon 15000
63=wait 3000
64=windows
65=tap ESCAPE
66=wait 1500
67=tap ESCAPE
68=wait 1500
69=label pqafter
70=waitstate 0x19 120000
71=wait 20000
72=pos client-r2
73=windows
74=pass 3000
75=label back_mm
76=tap ESCAPE
77=wait 3000
78=jump mm 4
79=label back_om
80=tap ESCAPE
81=wait 3000
82=jump om 4
"""


def override_ini(variant, run, res):
    w, h = res
    s = '; kl_menu_shots_1110: variant %s, run %s (generated; the live KLHook.ini is the base)\n' % (variant, run)
    s += '[MenuLook]\nDeadMen=%d\n' % (1 if variant == 'deadmen' else 0)
    s += '[Expansion]\nLog=%d\n' % (2 if run == 'menus' else 1)      # 2 = every file open (ML5 proof)
    if run == 'match':
        s += 'Page=0\n'
    s += '[Echo]\nProbe=1\n[Menu]\nTableLog=1\n'
    s += '[Solo]\nW=%d\nH=%d\n' % (w, h)
    if run == 'match':
        s += '[Lobby]\nRows12=1\nMinPlayers=2\nPlayersMax=12\nPlayersAuto=1\nExtraSeats=1\nMaxPlayers=12\n'
    return s


def desktop_res():
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command',
                              '(Get-CimInstance Win32_VideoController | Select -First 1 | % { "$($_.CurrentHorizontalResolution)x$($_.CurrentVerticalResolution)" })'],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        m = re.match(r'(\d+)x(\d+)$', out)
        if m and int(m.group(1)) >= 640:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return 1920, 1080                                                 # GUESS when the desktop cannot be read


def parse_res(v):
    if v in (None, '', 'auto'):
        return desktop_res()
    m = re.match(r'(\d+)x(\d+)$', v)
    if not m:
        raise SystemExit('--res must be auto or WxH')
    return int(m.group(1)), int(m.group(2))


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def is_test_dll(p):
    return b'(TEST)' in open(p, 'rb').read()


# ------------------------------------------------------------------------------------------------------------------ gen
def cmd_gen(a):
    kit = a.kit
    os.makedirs(kit, exist_ok=True)
    res = parse_res(a.res)
    for v in VARIANTS:
        for run in RUNS:
            tag = 'MENULOOK_%s_%s' % (v.upper(), run.upper())
            body = menus_script() if run == 'menus' else match_host_script()
            open(os.path.join(kit, tag + '_host.ini'), 'w', encoding='utf-8').write(override_ini(v, run, res) + AUTO + body)
            if run == 'match':
                open(os.path.join(kit, tag + '_join.ini'), 'w', encoding='utf-8').write(override_ini(v, run, res) + AUTO + JOIN)
    tw = {}
    for ship, test, src, note in TWINS:
        ent = {'test': test, 'note': note, 'file': None}
        if os.path.isfile(src) and md5(src).startswith(test):
            d = os.path.join(kit, 'twins', test)
            os.makedirs(d, exist_ok=True)
            shutil.copy(src, os.path.join(d, 'dinput8.dll'))
            ent['file'] = 'twins/%s/dinput8.dll' % test
        tw[ship] = ent
    json.dump({'ship_to_test': tw, 'note': 'live dll md5 prefix -> TEST twin; a live dll whose md5 prefix is a "test" value (or has (TEST) in it) runs as it is'},
              open(os.path.join(kit, 'twins.json'), 'w', encoding='utf-8'), indent=1)
    json.dump({'res': list(res), 'pages': [dict(run=p[0], page=p[1], expect=p[2], windows=p[3], dwell=p[4]) for p in PAGES],
               'not_covered': NOT_COVERED}, open(os.path.join(kit, 'pages.json'), 'w', encoding='utf-8'), indent=1)
    shutil.copy(os.path.abspath(__file__), os.path.join(kit, 'kl_menu_shots_1110.py'))
    for name, doc, sub in (('run.py', 'python run.py [--variants deadmen,stock] [--runs menus,match] [--twin DLL] [--dry]', 'run'),
                           ('post.py', 'python post.py   (shots -> ..\\shots\\<variant>\\<page>.png, ml5.txt, ml1.txt; no game)', 'post'),
                           ('validate.py', 'python validate.py   (dry check of the generated scripts; no game)', 'validate')):
        open(os.path.join(kit, name), 'w', encoding='utf-8').write(
            '#!/usr/bin/env python3\n"""kit entry: %s"""\nimport os, subprocess, sys\nK = os.path.dirname(os.path.abspath(__file__))\n'
            'sys.exit(subprocess.call([sys.executable, os.path.join(K, "kl_menu_shots_1110.py"), "%s", "--kit", K] + sys.argv[1:]))\n' % (doc, sub))
    print('kit written:', kit, '| res %dx%d' % res, '|', len(os.listdir(kit)), 'entries')
    return 0


# ------------------------------------------------------------------------------------------------------------------ validate
def check_script(text, name):
    """problems in an ini's [Script]: ops, numbering, labels, keys, ending"""
    bad, ops, labels, uses, sec, expect = [], [], set(), [], None, 1
    for ln in text.splitlines():
        m = re.match(r'\[(\w+)\]\s*$', ln)
        if m:
            sec = m.group(1).lower(); continue
        if sec != 'script' or not ln.strip() or ln.startswith(';'):
            continue
        m = re.match(r'(\d+)=(\w+)\s*(.*)$', ln)
        if not m:
            bad.append('%s: unparsable script line %r' % (name, ln[:60])); continue
        n, op, rest = int(m.group(1)), m.group(2).lower(), m.group(3)
        if n != expect:
            bad.append('%s: script numbering jumps %d -> %d' % (name, expect - 1, n)); expect = n
        expect += 1
        if op not in OPS:
            bad.append('%s: line %d op %r is not a klauto op' % (name, n, op))
        ops.append(op)
        w = rest.split()
        if op == 'label' and w:
            labels.add(w[0])
        if op in ('jump', 'onfail') and w:
            uses.append((n, w[0]))
        if op == 'onwin' and len(w) > 1:
            uses.append((n, w[1]))
        if op in ('tap', 'tapuntil') and (not w or w[0] not in KEYS):
            bad.append('%s: line %d taps unknown key %r' % (name, n, w[0] if w else ''))
        if op == 'wait' and not re.match(r'\d+$', rest.strip()):
            bad.append('%s: line %d wait needs ms' % (name, n))
        if op == 'tapuntil' and len(w) < 2:
            bad.append('%s: line %d tapuntil needs a window' % (name, n))
    for n, lab in uses:
        if lab not in labels:
            bad.append('%s: line %d goes to undefined label %r' % (name, n, lab))
    if not ops:
        bad.append('%s: no [Script]' % name)
    elif 'fail' not in ops[-3:] and ops[-1] not in ('pass', 'jump'):
        bad.append('%s: script does not end in pass / fail / jump' % name)
    return bad, ops


def cmd_validate(a):
    kit, bad, seen = a.kit, [], 0
    pages = json.load(open(os.path.join(kit, 'pages.json')))['pages']
    for v in VARIANTS:
        for run in RUNS:
            tag = 'MENULOOK_%s_%s' % (v.upper(), run.upper())
            for role in ('host', 'join'):
                if role == 'join' and run == 'menus':
                    continue
                p = os.path.join(kit, '%s_%s.ini' % (tag, role))
                name = os.path.basename(p)
                if not os.path.isfile(p):
                    bad.append('missing ' + p); continue
                t = open(p, encoding='utf-8').read()
                b, _ = check_script(t, name)
                bad += b
                seen += 1
                if len(re.findall(r'^\[Script\]\s*$', t, re.M)) != 1:
                    bad.append('%s: [Script] must appear exactly once' % name)
                dm = re.search(r'\[MenuLook\]\s*\nDeadMen=(\d)', t)
                if not dm or int(dm.group(1)) != (1 if v == 'deadmen' else 0):
                    bad.append('%s: [MenuLook] DeadMen is not %d' % (name, 1 if v == 'deadmen' else 0))
                if role == 'host':
                    want = [q['page'] for q in pages if q['run'] == run]
                    got = re.findall(r'^\d+=log MENULOOK (\w+)\s*$', t, re.M)
                    if got != want:
                        bad.append('%s: page labels %s != pages.json %s' % (name, got, want))
    for ship, e in json.load(open(os.path.join(kit, 'twins.json')))['ship_to_test'].items():
        if e['file'] and not md5(os.path.join(kit, e['file'])).startswith(e['test']):
            bad.append('twin %s: file md5 != %s' % (ship, e['test']))
    for b in bad:
        print('PROBLEM', b)
    print('validate: %d scripts checked, %d problems' % (seen, len(bad)))
    return 1 if bad else 0


# ------------------------------------------------------------------------------------------------------------------ run
def kl2_processes():
    """(real, zombie) pids of kl2.exe from tasklist: a thread-less zombie shows well under 4000 K of memory"""
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq kl2.exe', '/FO', 'CSV', '/NH'], capture_output=True, text=True).stdout
    real, zomb = [], []
    for ln in out.splitlines():
        c = [x.strip('"') for x in ln.split('","')]
        if len(c) >= 5 and c[0].lower().startswith('kl2.exe'):
            kb = int(re.sub(r'\D', '', c[4]) or 0)
            (real if kb >= 4000 else zomb).append(int(c[1]))
    return real, zomb


def pick_twin(kit, live_dll, override):
    """(path of the TEST dll, its md5 prefix, why); SystemExit with REFUSED when none is known"""
    if override:
        if not os.path.isfile(override):
            raise SystemExit('REFUSED: --twin %s is not a file' % override)
        if not is_test_dll(override):
            raise SystemExit('REFUSED: --twin has no "(TEST)" marker - not a build_auto.bat dll (the bench would hang with NO LOG)')
        return override, md5(override)[:8], 'override'
    m = md5(live_dll)[:8]
    tj = json.load(open(os.path.join(kit, 'twins.json')))['ship_to_test']
    if m in tj:
        e = tj[m]
        if not e['file']:
            raise SystemExit('REFUSED: live dll %s has the twin %s but its file was missing when the kit was written (%s); pass --twin' % (m, e['test'], e['note']))
        return os.path.join(kit, e['file']), e['test'], 'TEST twin of the live SHIP %s (%s)' % (m, e['note'])
    for ship, e in tj.items():
        if e['test'] == m and e['file']:
            return os.path.join(kit, e['file']), e['test'], 'the live dll IS the TEST twin of SHIP %s' % ship
    if is_test_dll(live_dll):
        return live_dll, m, 'the live dll is a TEST build (pair unknown)'
    raise SystemExit('REFUSED: live dll %s has no known TEST twin (twins.json). Pass --twin <TEST dinput8.dll> or add the pair.' % m)


def cmd_run(a):
    kit = a.kit
    variants = [x for x in a.variants.split(',') if x]
    runs = [x for x in a.runs.split(',') if x]
    for x in variants:
        if x not in VARIANTS:
            raise SystemExit('unknown variant ' + x)
    for x in runs:
        if x not in RUNS:
            raise SystemExit('unknown run ' + x)
    real, zomb = kl2_processes()
    if real and not a.dry:
        raise SystemExit('REFUSED: kl2.exe is running (pids %s) - the owner or another bench holds the game; zombies %s are ignored. '
                         'Announce BENCH START only after this check passes.' % (real, zomb))
    hook, test8, why = pick_twin(kit, DD + '/dinput8.dll', a.twin)
    print('TEST dll %s (%s) | %s | live dll %s | zombies %s | real kl2 %s' % (hook, test8, why, md5(DD + '/dinput8.dll')[:8], zomb, real), flush=True)
    if os.path.basename(hook).lower() != 'dinput8.dll':
        raise SystemExit('REFUSED: --twin must be named dinput8.dll')
    if 'deadmen' in variants:                                          # without the themed copies the deadmen variant is a stock run
        for rel in ('Scenes/kaneandlynch_deadmen.WHD', 'Scenes/kaneandlynch_deadmen.WAV', 'KLExpansion/Overlay/Patch01_deadmen.zip'):
            if not os.path.isfile(DD + '/' + rel) and not a.dry:
                raise SystemExit('REFUSED: %s is missing in the game folder - the deadmen variant would run the stock look (install the menu look first)' % rel)
    out_root = os.path.join(os.path.dirname(os.path.abspath(kit.rstrip('/\\'))), 'shots')
    if os.path.isdir(out_root) and os.listdir(out_root) and not a.dry:       # never overwrite an earlier result set: move it aside
        keep = '%s_before_%s' % (out_root, time.strftime('%m%d_%H%M%S'))
        os.rename(out_root, keep)
        print('earlier shots moved to', keep, flush=True)
    rc_all = 0
    for v in variants:
        for run in runs:
            tag = 'MENULOOK_%s_%s' % (v.upper(), run.upper())
            base = os.path.join(kit, 'KLHook_base_%s.ini' % tag)
            n = 1 if run == 'menus' else 2
            secs, last = (380, 380) if run == 'menus' else (1100, 800)
            cmd = [sys.executable, SOLO_TEST, '--hook', os.path.dirname(hook), '--n', str(n), '--secs', str(secs), '--tag', tag, '--owner-away',
                   '--d3shots', '--shots', '2-%d:2' % last, '--base', base, '--ini1', os.path.join(kit, tag + '_host.ini')]
            if n == 2:
                cmd += ['--gap', '45', '--relaunch', '2', '--ini2', os.path.join(kit, tag + '_join.ini')]
            print(' '.join('"%s"' % c if ' ' in c else c for c in cmd), flush=True)
            if a.dry:
                continue
            real, _ = kl2_processes()
            if real:
                raise SystemExit('REFUSED: kl2.exe started meanwhile (pids %s)' % real)
            for old_shot in glob.glob('%s/%s/KLShot_inst*_*.jpg' % (SOLO, tag)):   # stale shots of an earlier run of this tag would match by clock time
                try:
                    os.remove(old_shot)
                except OSError:
                    pass
            shutil.copy(DD + '/KLHook.ini', base)
            for i in range(1, n + 1):
                d = '%s/%s/inst%d' % (SOLO, tag, i)
                os.makedirs(d, exist_ok=True)
                if os.path.isfile(DD + '/KLShopPage.ini'):
                    shutil.copy(DD + '/KLShopPage.ini', d + '/KLShopPage.ini')     # kl_solo_test does not stage it; [ShopPage] would be off
            t0 = time.time()
            with open(os.path.join(kit, tag + '_run.txt'), 'w', encoding='utf-8') as f:
                rc = subprocess.call(cmd, cwd=os.path.dirname(os.path.dirname(SOLO_TEST)), stdout=f, stderr=subprocess.STDOUT)
            print('%s exit %d after %.0f s' % (tag, rc, time.time() - t0), flush=True)
            rc_all |= (rc != 0)
    if not a.dry:
        rc_all |= cmd_post(argparse.Namespace(kit=kit, out=None))
    return rc_all


# ------------------------------------------------------------------------------------------------------------------ post
STEP = re.compile(r'^(\d\d):(\d\d):(\d\d)\.(\d+)\s+script \d+: MENULOOK (\w+)\s*$')


def read_steps(logp):
    """[(clock seconds of day, page)] from the `log MENULOOK <page>` script lines"""
    steps = []
    for ln in open(logp, encoding='latin-1', errors='replace').read().splitlines():
        m = STEP.match(ln)
        if m:
            steps.append((int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) + float('0.' + m.group(4)), m.group(5)))
    return steps


def shot_secs(p):
    mt = os.path.getmtime(p)
    t = time.localtime(mt)
    return t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec + mt % 1


def pick_shot(shots, t0, dwell):
    """last shot between 1.0 s after the page's log line and the end of its dwell (page settled, next key not yet sent)"""
    best = None
    for p, s in shots:
        if 1.0 <= (s - t0) % 86400 <= dwell + 0.3:
            best = p
    if best:
        return best, 'settled'
    for p, s in shots:
        if 0.0 <= (s - t0) % 86400 <= dwell + 1.5:
            best = p
    return best, ('late-or-early' if best else 'missing')


def to_png(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        from PIL import Image
        Image.open(src).convert('RGB').save(dst)
        return True
    except Exception:
        shutil.copy(src, os.path.splitext(dst)[0] + os.path.splitext(src)[1])
        return False


def ml5_proof(logp, variant):
    """audio-free ML5 proof for one log: menulook / menusounds lines, themed file opens, probe waves -> (ok, lines)"""
    t = open(logp, encoding='latin-1', errors='replace').read().splitlines() if os.path.isfile(logp) else []
    ml = [l for l in t if re.search(r'\bmenulook:', l)]
    ms = [l for l in t if re.search(r'\bmenusounds:', l)]
    opens = [l for l in t if re.search(r'expansion: .*(kaneandlynch|Patch01)', l, re.I)]
    probe = [l for l in t if 'echo-probe play' in l]
    redir = [l for l in ml if '_deadmen' in l and '->' in l]
    whd = [l for l in redir if re.search(r'kaneandlynch\.WHD', l, re.I)]
    wav = [l for l in redir if re.search(r'kaneandlynch\.WAV', l, re.I)]
    themed_opens = [l for l in opens if '_deadmen' in l]
    off = [l for l in ml if 'menulook: off' in l]
    miss = [l for l in ml if ' ON but no ' in l]
    if variant == 'deadmen':
        ok = bool(whd) and bool(wav) and not miss and not off
        why = 'WHD redirect %d, WAV redirect %d, missing-sibling lines %d, off lines %d' % (len(whd), len(wav), len(miss), len(off))
    else:
        ok = bool(off) and not redir and not themed_opens
        why = 'off lines %d, themed redirects %d (want 0), themed opens %d (want 0)' % (len(off), len(redir), len(themed_opens))
    out = ['ML5 %s: %s - %s' % (variant, 'PASS' if ok else 'FAIL', why),
           '  menulook lines %d, menusounds lines %d, Patch01/kaneandlynch opens %d, echo-probe play lines %d' % (len(ml), len(ms), len(opens), len(probe))]
    out += ['    ' + l[:200] for l in ml[:10]] + ['    ' + l[:200] for l in ms[:12]] + ['    open: ' + l[:200] for l in opens[:10]]
    names = {}
    for l in probe:
        for w in re.findall(r'[A-Za-z0-9_/]+\.wav', l):
            names[w] = names.get(w, 0) + 1
    out.append('  waves named by the probe (%d distinct): %s' % (len(names), ', '.join('%s x%d' % kv for kv in sorted(names.items())[:12])))
    return ok, out


# ML1 heuristics (GUESS) ---------------------------------------------------------------------------------------------
def inv_elements(window, inv=None):
    """elements of `## Window `X`` in the menu inventory md tables: dicts i, name, type, x, y, w, h (ints, '~' stripped), font, text"""
    def num(x):
        x = x.strip().rstrip('~')
        return int(x) if re.match(r'-?\d+$', x) else None
    for f in sorted(glob.glob((inv or INV) + '/*.md')):
        cur, out = None, []
        for ln in open(f, encoding='utf-8', errors='replace').read().splitlines() + ['## Window `END`']:
            m = re.match(r'## Window `([^`]+)`', ln)
            if m:
                if cur == window and out:
                    return out
                cur, out = m.group(1), []
                continue
            if cur == window and re.match(r'^\|\s*\d+\s*\|', ln):
                c = [x.strip() for x in ln.strip().strip('|').split('|')]
                if len(c) >= 16:
                    out.append(dict(i=int(c[0]), name=c[3], type=c[4], x=num(c[6]), y=num(c[7]), w=num(c[8]), h=num(c[9]), font=c[13], text=c[15]))
    return []


def box(iw, ih, e, band=30, wdef=240):
    """pixel box of an element: 1280x720 virtual screen, the 768x576 ScreenBaseSize block centred (GUESS), x/y relative to the block"""
    sx, sy = iw / 1280.0, ih / 720.0
    x0, y0 = (1280 - 768) / 2.0 + e['x'], (720 - 576) / 2.0 + e['y']
    return (int(x0 * sx), int(y0 * sy), int((x0 + (e['w'] or wdef)) * sx), int((y0 + (e['h'] or band)) * sy))


def ink_extent(img, bx, thr=150):
    """(left, right) pixel columns holding bright pixels inside the box, or None"""
    from PIL import ImageOps
    bx = (max(0, bx[0]), max(0, bx[1]), min(img.size[0], bx[2]), min(img.size[1], bx[3]))
    if bx[2] <= bx[0] or bx[3] <= bx[1]:
        return None
    g = ImageOps.grayscale(img.crop(bx))
    w, h = g.size
    px = g.load()
    cols = [x for x in range(w) if any(px[x, y] >= thr for y in range(h))]
    return (cols[0] + bx[0], cols[-1] + bx[0]) if cols else None


def compare_page(dm_path, st_path, windows, inv=None):
    """ML1 on one page: declared overlaps of text rows (inventory only), then per text row the ink extent in the deadmen shot against the
    stock shot and the declared width. GUESS: a pixel heuristic; positions assume the centred 768x576 block."""
    from PIL import Image
    dm, st = Image.open(dm_path).convert('RGB'), Image.open(st_path).convert('RGB')
    if dm.size != st.size:
        st = st.resize(dm.size)
    W, H = dm.size
    rows = []
    for win in windows:
        els = [e for e in inv_elements(win, inv) if e['x'] is not None and e['y'] is not None and e['text']
               and e['type'].rstrip('~') not in ('Graphic', 'GUIGroup', 'MercsGraphic')]
        for i, e in enumerate(els):
            lab = e['name'] or e['text'][:24]
            b = box(W, H, e)
            for f in els[i + 1:]:
                c = box(W, H, f)
                if b[0] < c[2] and c[0] < b[2] and abs(b[1] - c[1]) < (b[3] - b[1]) * 0.6:
                    rows.append('declared-overlap %s: %s (el %d) x %s (el %d) [GUESS boxes]' % (win, lab, e['i'], f['name'] or f['text'][:24], f['i']))
            a, s = ink_extent(dm, b), ink_extent(st, b)
            if a and s:
                grow = (a[1] - a[0]) - (s[1] - s[0])
                if grow > max(6, 0.12 * (s[1] - s[0])):
                    rows.append('wider-than-stock %s: %s (el %d, Font %s): +%d px ink vs stock [GUESS ink threshold]' % (win, lab, e['i'], e['font'], grow))
                if e['w'] and a[1] > b[2] + 4:
                    rows.append('overruns-width %s: %s (el %d): ink ends %d px past the declared width' % (win, lab, e['i'], a[1] - b[2]))
            elif a and not s:
                rows.append('ink-only-in-deadmen %s: %s (el %d)' % (win, lab, e['i']))
    return rows


def cmd_post(a):
    kit = a.kit
    out_root = a.out or os.path.join(os.path.dirname(os.path.abspath(kit.rstrip('/\\'))), 'shots')
    pages = json.load(open(os.path.join(kit, 'pages.json')))['pages']
    rc, ml5, ml1, got = 0, [], [], {}
    if not glob.glob(INV + '/*.md'):
        ml1.append('ML1 WARNING: no menu inventory under %s (set KL_MENU_INV) - every page below would read "no findings" for lack of data' % INV)
        rc = 1
    for v in VARIANTS:
        for run in RUNS:
            tag = 'MENULOOK_%s_%s' % (v.upper(), run.upper())
            logp = '%s/%s/inst1/KLHook.log' % (SOLO, tag)
            if not os.path.isfile(logp):
                print('%s: no log (not run yet)' % tag); continue
            steps = read_steps(logp)
            files = glob.glob('%s/%s/KLShot_inst1_*.jpg' % (SOLO, tag)) + glob.glob('%s/%s/inst1/KLShot_inst1_*.jpg' % (SOLO, tag))
            shots = [(p, shot_secs(p)) for p in sorted(files, key=os.path.getmtime)]
            print('%s: %d MENULOOK lines, %d shots' % (tag, len(steps), len(shots)))
            for q in [p for p in pages if p['run'] == run]:
                st = [s for s in steps if s[1] == q['page']]
                if not st:
                    print('  %-22s NOT REACHED (no log line)' % q['page']); rc = 1; continue
                p, how = pick_shot(shots, st[0][0], q['dwell'])
                if not p:
                    print('  %-22s log line but NO SHOT in its dwell' % q['page']); rc = 1; continue
                dst = os.path.join(out_root, v, q['page'] + '.png')
                png = to_png(p, dst)
                got[(v, q['page'])] = dst if png else os.path.splitext(dst)[0] + '.jpg'
                print('  %-22s %-13s %s%s' % (q['page'], how, os.path.basename(p), '' if png else '  (PIL missing: copied as JPG)'))
            if run == 'menus':
                ok, lines = ml5_proof(logp, v)
                ml5 += lines
                rc |= (not ok)
    for q in pages:
        d, s = got.get(('deadmen', q['page'])), got.get(('stock', q['page']))
        if not d or not s:
            continue
        try:
            rows = compare_page(d, s, q['windows'])
        except Exception as ex:
            rows = ['compare failed: %s' % ex]
        ml1.append('%s (%s): %s' % (q['page'], ','.join(q['windows']), 'no clipped / overlapping rows found [GUESS heuristic]' if not rows else '%d finding(s) [GUESS]' % len(rows)))
        ml1 += ['    ' + r for r in rows]
    os.makedirs(out_root, exist_ok=True)
    open(os.path.join(out_root, 'ml5.txt'), 'w', encoding='utf-8').write('\n'.join(ml5) + '\n')
    open(os.path.join(out_root, 'ml1.txt'), 'w', encoding='utf-8').write('\n'.join(ml1) + '\n')
    print('\n'.join(ml5)); print('\n'.join(ml1))
    print('shots under', out_root)
    print('RESULT: %s' % ('PASS' if not rc else 'CHECK (pages missing or ML5 failed)'))
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('gen'); g.add_argument('--kit', required=True); g.add_argument('--res', default='auto')
    v = sub.add_parser('validate'); v.add_argument('--kit', required=True)
    r = sub.add_parser('run'); r.add_argument('--kit', required=True); r.add_argument('--variants', default='deadmen,stock')
    r.add_argument('--runs', default='menus,match'); r.add_argument('--twin'); r.add_argument('--dry', action='store_true')
    p = sub.add_parser('post'); p.add_argument('--kit', required=True); p.add_argument('--out')
    a = ap.parse_args()
    return {'gen': cmd_gen, 'validate': cmd_validate, 'run': cmd_run, 'post': cmd_post}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
