#!/usr/bin/env python3
"""
grudge_1106: the 2-seat OnlineGrudge bench kit (2026-11-06). Built OFFLINE; the live run waits for c9's "game free / grudge go".

    python tools/kl_grudge_bench_1106.py gen [--test-dll PATH] [--force-live]   write/refresh the kit C:/kl_build_1024/grudge_1106 (reads the live KLHook.ini + the Q32 DD05 pair; no game contact)
    python tools/kl_grudge_bench_1106.py validate                               DRY RUN: dll md5 + TEST markers, ini keys, script ops (checked against klauto.c), live md5s. No launch.
    python tools/kl_grudge_bench_1106.py run [A|B|all] [--owner-away] [--secs N] [--allow-live-dll MD5PREFIX] [--again]
    python tools/kl_grudge_bench_1106.py summarize [A|B|all]                    PASS/FAIL per criterion from the KLHook.logs of the last runs (no game contact)

WHAT IT PROVES ([Bots] OnlineGrudge, klhook/klgrudge.c, commit a95bbc90; re/online_grudge_1106.md)
  Pass A (OnlineGrudgeDry=1): (a) the hook installs, (b) the HUMAN host's shots on an Ally AI heister reach kog_hit with attacker = a ZFFPlayer (vtable 00bb45f4)
  and health DROPS, (c) a lethal blow is attributed (killer found) and "would call slot 129" is logged, but nothing is marked.
  Pass B (OnlineGrudgeDry=0, optional, a separate run): the real mark: "made traitor (slot 129 ...)".
MAP/SEATS: Dry Dock = DD05 (slot F05, page 0, stock), 1 host + 1 joiner through tools/kl_solo_test.py. Seat inis are the Q32_DD05 pair
  (c9_1028/q32, PASS 2-seat, copied into the kit as tpl_*.ini) with the script replaced after "SOLO match started" and these host-only keys added:
  [Bots] OnlineGrudge=1 / OnlineGrudgeDry=1|0, [Down] OnlineBotDown=0 (else the bot goes down at DownPct and never has a lethal blow), [BotFill] OnlineHealthMul=1
  (bot health 350, not 1750). Base ini = a COPY of the live <DD>/KLHook.ini made at gen time (sha1 pinned in kit.json); kl_solo_test restores the live one at run end.
THE FIRING RIG: klauto op "firebot [ms] [maxm] [deg] [pulse] [aim]" (TEST build only: klauto.c is not compiled into SHIP). See klauto.c C_FIREBOT.
SAFETY: never launches kl2.exe except through kl_solo_test (only in `run`); refuses if kl2.exe runs; never writes into the game folder itself; re-checks the live
  dll + ini md5 after every pass; never touches KL_PortBackup; never kills a process. A file <kit>/STOP stops the queue.
"""
import hashlib, json, os, re, subprocess, sys, time, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import kl_n9_1106 as N                                   # md5/write/load/parse_ini/kv_last_wins/script_lines/number/live_state/kl2_running/idle_s (no side effects at import)

KIT = 'C:/kl_build_1024/grudge_1106'
DD = N.DD
SOLO = N.SOLO
Q32 = 'C:/kl_build_1024/c9_1028/q32'
TPL_HOST, TPL_JOIN = '%s/Q32_DD05_host.ini' % Q32, '%s/Q32_DD05_join.ini' % Q32
TEST_DLL_DEFAULT = os.path.join(ROOT, 'klhook', 'out_ogb1106f_test', 'dinput8.dll')      # 11-06 04:18: + klbrain traitor-cap fix 410ab59d (both checked in one slot)
LIVE_SHIP_MD5 = '727a73bb'                               # the live SHIP the bench starts from and restores (sha1 dc41cc8f...)
LIVE_SHIP_SHA1 = 'c8598902'
LIVE_INI_SHA1 = 'a64a3996'
PASSES = {'A': dict(dry=1, tag='GRUDGE_A', what='OnlineGrudgeDry=1 (log only)'),
          'B': dict(dry=0, tag='GRUDGE_B', what='OnlineGrudgeDry=0 (the real mark, slot 129)')}
SECS = 480                                               # kl_solo_test --secs budget per pass (Q32: whole 2-round run 499 s; this stops after ~40 s of round)
GAP, RELAUNCH = 45, 2
HOST_EXTRA = [('Bots', [('OnlineGrudge', '1')]),         # OnlineGrudgeDry is added per pass
              ('Down', [('OnlineBotDown', '0')]),
              ('BotFill', [('OnlineHealthMul', '1')])]
# the firing block that replaces everything the Q32 host did after "log SOLO match started"
FIRE_BLOCK = ['waitstate 0x19 180000',
              'log GRUDGE1106 round running (state 0x19); bots hold at their spawn for ~25 s',
              'wait 2500',
              # TEST rig: the stock gate G1 (ZFFActor slot 422, 0x868b11..0x868b49) drops a HUMAN's hit on an Ally bot while
              # rules +0x285 ('looting started', set by the first loot, 0x5cac90) is 0 - pass A run 2 fired before any loot.
              # One byte = 1, as klfedkit.c's hunt does; the game clears it at the next round. firebot hp lines log it.
              'pokeb 168e9e4+54+285 1 GRUDGE1106 looting-started byte (G1) for the bench',
              'pos g0',
              'firebot 8000 40 15 60 1',
              'pos g1',
              'tap R',
              'wait 2500',
              'firebot 8000 40 15 60 1',
              'pos g2',
              'tap R',
              'wait 2500',
              'firebot 25000 40 15 60 1',
              'pos g3',
              'log GRUDGE1106 firebot phase over; waiting for the death logs',
              'wait 5000',
              'pass 1000']
JOIN_BLOCK = ['waitstate 0x19 300000',
              'log GRUDGE1106 client in round',
              'wait 15000',
              'pos client-a',
              'wait 60000',
              'pass 1000']


def sh1(p):
    h = hashlib.sha1()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def klauto_ops():
    """The op names klauto.c's script parser knows (so `validate` checks the script against the real source, not a hand list)."""
    src = open(os.path.join(ROOT, 'klhook', 'klauto.c'), encoding='latin-1').read()
    return set(m.lower() for m in re.findall(r'_stricmp\(op, "([A-Za-z0-9]+)"\)', src))


# ---------------------------------------------------------------- ini building
def sections_text(tpl_text, extra=None, script=None):
    """Template -> ini text: every non-Script section merged (last value wins), `extra` = [(section, [(k, v)])] set in place, ONE [Script] last."""
    pre, secs = N.parse_ini(tpl_text)
    out, seen = [], set()
    extra = extra or []
    for name, lines in secs:
        if name == 'Script':
            continue
        body = N.kv_last_wins(lines)
        for sec, kvs in extra:
            if sec == name:
                for k, v in kvs:
                    body = N.set_key(body, k, v)
        seen.add(name)
        out.append('[%s]' % name); out += body
    for sec, kvs in extra:
        if sec not in seen:
            out.append('[%s]' % sec); out += ['%s=%s' % kv for kv in kvs]
    if script is not None:
        out.append('[Script]'); out += N.number(script)
    return '\n'.join(out) + '\n'


def tpl_script(tpl_text):
    for name, lines in N.parse_ini(tpl_text)[1]:
        if name == 'Script':
            return N.script_lines(lines)
    return []


def host_script(cmds):
    i = next(k for k, c in enumerate(cmds) if c.startswith('log SOLO match started'))
    t = next(k for k, c in enumerate(cmds) if c == 'label bail')
    head = [c for c in cmds[:i + 1]]
    return head + FIRE_BLOCK + cmds[t:]


def join_script(cmds):
    i = next(k for k, c in enumerate(cmds) if c.startswith('log SOLO match started'))
    t = next(k for k, c in enumerate(cmds) if c == 'label back_mm')
    return cmds[:i + 1] + JOIN_BLOCK + cmds[t:]


def build_pair(tag):
    dry = PASSES[tag]['dry']
    th, tj = N.load('%s/tpl_host.ini' % KIT), N.load('%s/tpl_join.ini' % KIT)
    extra = [(s, list(kv)) for s, kv in HOST_EXTRA]
    extra[0][1].append(('OnlineGrudgeDry', str(dry)))
    h = sections_text(th, extra, host_script(tpl_script(th)))
    j = sections_text(tj, None, join_script(tpl_script(tj)))
    h = '; grudge_1106 pass %s (%s): Q32_DD05 host + OnlineGrudge bench keys + firebot script\n' % (tag, PASSES[tag]['what']) + h
    j = '; grudge_1106 pass %s joiner: Q32_DD05 join, idles in the round, then pass\n' % tag + j
    return h, j


def gen(test_dll=None, force_live=False):
    ld = N.live_state()
    ini_sha = sh1('%s/KLHook.ini' % DD)
    dll_sha = sh1('%s/dinput8.dll' % DD)
    bad = []
    if not (ld['dll'] or '').startswith(LIVE_SHIP_MD5):
        bad.append('live dinput8.dll md5 %s is not the pinned SHIP %s' % ((ld['dll'] or '-')[:8], LIVE_SHIP_MD5))
    if not ini_sha.startswith(LIVE_INI_SHA1):
        bad.append('live KLHook.ini sha1 %s is not the pinned %s' % (ini_sha[:8], LIVE_INI_SHA1))
    if bad and not force_live:
        raise SystemExit('gen: %s (pass --force-live to build from what is live)' % '; '.join(bad))
    test_dll = test_dll or TEST_DLL_DEFAULT
    if not os.path.isfile(test_dll):
        raise SystemExit('gen: TEST dll %s missing (build: klhook/build_auto.bat klhook/out_ogb1106_test)' % test_dll)
    os.makedirs('%s/hook_test' % KIT, exist_ok=True)
    shutil.copy2(test_dll, '%s/hook_test/dinput8.dll' % KIT)
    shutil.copy2('%s/KLHook.ini' % DD, '%s/KLHook_base.ini' % KIT)                  # snapshot of the CURRENT live ini, taken now
    if os.path.isfile('%s/KLShopPage.ini' % DD):
        shutil.copy2('%s/KLShopPage.ini' % DD, '%s/KLShopPage.ini' % KIT)
    shutil.copy2(TPL_HOST, '%s/tpl_host.ini' % KIT)
    shutil.copy2(TPL_JOIN, '%s/tpl_join.ini' % KIT)
    for t in PASSES:
        h, j = build_pair(t)
        N.write('%s/%s_host.ini' % (KIT, t), h)
        N.write('%s/%s_join.ini' % (KIT, t), j)
    meta = {'made': time.strftime('%Y-%m-%d %H:%M:%S'), 'hook_md5': N.md5('%s/hook_test/dinput8.dll' % KIT), 'hook_src': test_dll.replace('\\', '/'),
            'base_ini_md5': N.md5('%s/KLHook_base.ini' % KIT), 'base_ini_sha1': sh1('%s/KLHook_base.ini' % KIT),
            'live_at_gen': {'dll': ld['dll'], 'dll_sha1': dll_sha, 'ini': ld['ini'], 'ini_sha1': ini_sha},
            'zips_f05': N.zip_md5s('DD05', 'F05'), 'secs': SECS}
    N.write('%s/kit.json' % KIT, json.dumps(meta, indent=1))
    N.write('%s/README.txt' % KIT, readme(meta))
    print('gen: kit %s: TEST dll %s (from %s), base ini sha1 %s (live copy), live SHIP %s' % (KIT, meta['hook_md5'][:8], test_dll, meta['base_ini_sha1'][:8], (ld['dll'] or '-')[:8]))
    return 0


def readme(meta):
    return """GRUDGE_1106: 2-seat OnlineGrudge bench (host + joiner on this PC), Dry Dock DD05 (slot F05, page 0, stock)
made %(made)s. Offline-built. NOT run live. Do not run while the owner plays (live runs block keyboard and mouse); c9 says "game free / grudge go" first.

BUILD UNDER TEST
  hook_test/dinput8.dll  md5 %(hook)s  = klhook/build_auto.bat TEST build of the working tree (klgrudge.c a95bbc90 + the klauto 'firebot' op). Source: %(src)s
  It is NOT the live SHIP (%(ship)s): kl_solo_test swaps it in and puts the live dll back. Live SHIP + live ini are pinned in kit.json
  (dll md5 %(ship)s sha1 %(shipsha)s, KLHook.ini sha1 %(inisha)s) and re-checked after every pass.

RUN (from the repo root C:\\kl-merge\\kl-merge, game closed, Steam signed in)
  python tools/kl_grudge_bench_1106.py validate                      (dry run, no launch; must say RESULT: validate OK)
  python tools/kl_grudge_bench_1106.py run A --owner-away            (pass A, OnlineGrudgeDry=1: the proof)
  python tools/kl_grudge_bench_1106.py run B --owner-away            (optional pass B, OnlineGrudgeDry=0: the real mark, slot 129)
  python tools/kl_grudge_bench_1106.py summarize all                 (PASS/FAIL per criterion from the logs; no game contact)
  Without --owner-away the run refuses when the owner touched input in the last 300 s.
  Each pass: ~7-8 min wall (host first, joiner +45 s, lobby ~2 min, load, ~50 s of round, firebot phase ~40 s, then pass), --secs 480 budget.
  Logs: %(solo)s\\GRUDGE_<A|B>\\inst1\\KLHook.log (host), inst2 (joiner); run output %(kit)s/GRUDGE_<A|B>_run.txt.

PASS CRITERIA, pass A (grep the HOST log, inst1/KLHook.log)
  A1 hook installs   : grep -E "grudge: OnlineGrudge on \\(dry log\\): HOST only|private ZSoldier table [0-9a-f]+ made|sub-mode .*= 0 \\(Fragile Alliance\\): on"   (all three; and NO "the hit hook is OFF")
  A2 humans hit      : grep -E "online grudge dry: hit #[0-9]+ on AI heister [0-9]+ .*attacker [0-9a-f]+ vtable 00bb45f4 \\(HUMAN\\).*health [0-9.]+ -> [0-9.]+"   with the second health LOWER than the first
  A3 lethal blow     : grep -E "online grudge dry: lethal blow on AI heister .*vtable 00bb45f4: HUMAN"  then  "AI heister N (actor SAME) died: lethal blow .*killer found" (same actor)  then  "would call slot 129 \\(killer [0-9]+, victim -1\\)"
  A4 nothing marked  : NO "made traitor" line, NO "faulted", no log line starting "<time> [tag: ]CRASH", no KLHook_N.dmp / kl2_*_crash_*.mdmp (plain "EndOnFatal" / "logs it first as CRASH" text is normal; do not grep -i), RESULT PASS in the run output
  rig sanity (diagnostic, not a gate): grep "firebot" shows "target rec", "fire DOWN" and "firebot over ... health now"
PASS CRITERIA, pass B (OnlineGrudgeDry=0)
  B1 "grudge: OnlineGrudge on: HOST only" (no "(dry log)"), then B2 "human [0-9]+ killed an AI heister: made traitor \\(slot 129 killer [0-9]+ victim -1, then slot 105\\)" and "traitors now:"
  Whether the CLIENT shows the traitor state is not scripted: look at the joiner window / its log by hand.
DIAGNOSTICS when a gate fails
  no hit lines at all      : grep firebot: no "fire DOWN" = the rig (fire button / aim), else "AI heister N soldier ... not the stock one" or "slot 96 reads" = hook not installed on the bot
  hit but health not taken : "(no health taken: dead already, or completion not synchronous)" = the damage is written after the handler returns (GUESS 1 wrong): only the stamp fallback works
  hit not HUMAN            : "vtable check: not a ZFFPlayer" (attacker is not [hit+0] = the player: GUESS 2 wrong) / "rules-record check: ZFFPlayer without a seat"
  bot health never drops while the firebot hp lines show a hit: the sub-mode 0 friendly-fire filter (0x6e354e..0x6e35a5) zeroes human-on-bot damage: a finding in itself.
  not host (census 0 records, 'ONLINE host: role' absent) : the seat started as client; A1 fails too.
  no bot in range          : "firebot: no living Ally AI heister within 40 m": bots are not at the spawn at 0x19+2.5 s (they walk away at once or are not Ally).
GUESSES in the rig: yaw-only aim, fire = mouse button 0 held (never seen to fire a gun in an earlier log), 'tap R' = reload, Ally team = [[actor+0x54]+4]==2,
  slot 3 of klbd_online_view shared with OnlineGrudge's tick (reads only).
UNDO: nothing to undo - kl_solo_test restores dinput8.dll and KLHook.ini; `run` then re-checks both md5s against the pin and says so. If a bench was killed: the live dll
  is the TEST one -> copy the SHIP back (build/klhook/ship, md5 %(ship)s) by hand.
""" % dict(made=meta['made'], hook=meta['hook_md5'][:8], src=meta['hook_src'], ship=LIVE_SHIP_MD5, shipsha=LIVE_SHIP_SHA1, inisha=LIVE_INI_SHA1,
           solo=SOLO.replace('/', '\\'), kit=KIT)


def meta_of():
    p = '%s/kit.json' % KIT
    return json.load(open(p)) if os.path.isfile(p) else None


# ---------------------------------------------------------------- validate
def parsed(text):
    """-> {section: {key: value}} (last wins) and the script command list."""
    pre, secs = N.parse_ini(text)
    d, scr = {}, []
    for name, lines in secs:
        if name == 'Script':
            scr += N.script_lines(lines)
        else:
            for ln in N.kv_last_wins(lines):
                k, _, v = ln.partition('=')
                d.setdefault(name, {})[k] = v
    return d, scr, len(re.findall(r'^\[Script\]', text, re.M)), len(re.findall(r'^\[Auto\]', text, re.M))


def validate():
    v = N.V()
    print('validate (dry run: no game launch, no write into the game folder)')
    v.ok(os.path.isdir(DD), 'Dog Days folder')
    v.ok(os.path.isfile('%s/kl2.exe' % DD), 'kl2.exe present')
    n = N.kl2_running()
    v.ok(n == 0, 'no kl2.exe running (%d now; `run` refuses while one runs)' % n, warn=True)
    v.ok(os.path.isfile(os.path.join(ROOT, 'tools/kl_solo_test.py')), 'tools/kl_solo_test.py')
    v.ok(os.path.isdir(SOLO), 'solo work folder')
    meta = meta_of()
    if not v.ok(meta is not None, 'kit.json (run `gen` first)'):
        print('RESULT: validate FAILED - %d FAIL' % v.fail); return 1
    # --- the TEST dll
    dll = '%s/hook_test/dinput8.dll' % KIT
    if v.ok(os.path.isfile(dll), 'bench dll'):
        data = open(dll, 'rb').read()
        v.ok(hashlib.md5(data).hexdigest() == meta['hook_md5'], 'dll md5 %s = kit.json %s' % (hashlib.md5(data).hexdigest()[:8], meta['hook_md5'][:8]))
        v.ok(data.count(b'(TEST)') >= 3 and b"klauto's scripted keys" in data, 'dll carries the TEST markers ((TEST) x%d + klauto strings): it is build_auto.bat, not build.bat' % data.count(b'(TEST)'))
        v.ok(b'firebot' in data, 'dll has the klauto op "firebot" (%d strings)' % data.count(b'firebot'))
        v.ok(data.count(b'OnlineGrudge') >= 3 and b'online grudge%s: hit #' in data and b'would call slot 129' in data, 'dll has the OnlineGrudge keys and the log strings the greps need')
        pe = int.from_bytes(data[0x3c:0x40], 'little')
        v.ok(data[:2] == b'MZ' and data[pe:pe + 4] == b'PE\0\0' and int.from_bytes(data[pe + 4:pe + 6], 'little') == 0x14c, 'dll is a 32-bit PE (kl2.exe is 32-bit)')
        v.ok(2_500_000 < len(data) < 2_800_000, 'dll size %.2f MB (TEST builds are about 2.6 MB)' % (len(data) / 1e6))
        src = meta.get('hook_src')
        if src and os.path.isfile(src):
            v.ok(N.md5(src) == meta['hook_md5'], 'kit dll still equals the build output it was copied from (%s)' % src, warn=True)
    # --- the live state vs the pin
    live = N.live_state(); ld = live['dll'] or ''
    v.ok(ld.startswith(LIVE_SHIP_MD5), 'live dinput8.dll md5 %s %s' % (ld[:8], '= pinned SHIP %s' % LIVE_SHIP_MD5 if ld.startswith(LIVE_SHIP_MD5) else '(NOT the pinned SHIP: `run` refuses; a bench or TEST leftover may be live)'), warn=True)
    if os.path.isfile('%s/dinput8.dll' % DD):
        v.ok(sh1('%s/dinput8.dll' % DD).startswith(LIVE_SHIP_SHA1), 'live dinput8.dll sha1 %s = pinned %s' % (sh1('%s/dinput8.dll' % DD)[:8], LIVE_SHIP_SHA1), warn=True)
    base = '%s/KLHook_base.ini' % KIT
    if v.ok(os.path.isfile(base), 'base ini snapshot'):
        v.ok(sh1(base) == meta['live_at_gen']['ini_sha1'] and N.md5(base) == meta['base_ini_md5'], 'base ini = the live ini at gen (sha1 %s, md5 %s; LIVE_INI_SHA1 %s is only gen\'s default pin)' % (sh1(base)[:8], N.md5(base)[:8], LIVE_INI_SHA1))
        v.ok(live['ini'] == meta['live_at_gen']['ini'], 'live KLHook.ini unchanged since gen (md5 %s vs %s; peers restore other inis: rerun gen --force-live right before the slot)' % ((live['ini'] or '-')[:8], (meta['live_at_gen']['ini'] or '-')[:8]))
        bt = N.load(base)
        for sec in ('Expansion', 'Lobby', 'Bots', 'Down', 'BotFill', 'Redirect'):
            v.ok('[%s]' % sec in bt, 'base ini has [%s]' % sec)
        v.ok(re.search(r'^\[Script\]', bt, re.M) is None, 'base ini has no [Script] (an appended one would wipe the bench script)')
    v.ok(os.path.isfile(TPL_HOST) and os.path.isfile(TPL_JOIN), 'Q32_DD05 templates present')
    z = N.zip_md5s('DD05', 'F05')
    v.ok(all(z.values()) and z == meta['zips_f05'], 'live F05 map zips unchanged since gen (%s)' % '/'.join((x or '-')[:6] for x in z.values()))
    # --- seat inis and scripts
    ops = klauto_ops()
    v.ok('firebot' in ops and len(ops) > 30, 'klauto.c parser knows %d ops incl. firebot' % len(ops))
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import kl_solo_test as S
    for t in PASSES:
        for who in ('host', 'join'):
            p = '%s/%s_%s.ini' % (KIT, t, who); nm = os.path.basename(p)
            if not v.ok(os.path.isfile(p), '%s file' % nm):
                continue
            txt = N.load(p); d, scr, nscr, nauto = parsed(txt)
            v.ok(nscr == 1 and nauto == 1, '%s: one [Script], one [Auto]' % nm)
            bad = sorted({c.split()[0] for c in scr if c.split() and c.split()[0].lower() not in ops})
            v.ok(not bad and len(scr) > 30 and len(scr) < 600, '%s: %d script lines, every op known to klauto.c%s' % (nm, len(scr), (' UNKNOWN %s' % bad) if bad else ''))
            nums = re.findall(r'^(\d+)=', txt.split('[Script]')[1], re.M)
            v.ok(nums == [str(i + 1) for i in range(len(nums))], '%s: script lines numbered 1..%d without a gap (the parser stops at the first gap)' % (nm, len(nums)))
            labs = {c.split(None, 1)[1] for c in scr if c.startswith('label ')}
            jumps = [c.split()[2] if c.startswith('onwin') else c.split()[1] for c in scr if c.startswith(('onwin ', 'jump '))]
            v.ok(all(j in labs for j in jumps), '%s: every onwin/jump label exists' % nm)
            keys_ok = all(re.match(r'^(tap|down|up)\s+(\S+)', c) is None or S is not None for c in scr)
            v.ok(keys_ok and any(c.startswith('pass') for c in scr), '%s: has pass' % nm)
            v.ok(d.get('Expansion', {}).get('Page') == '0', '%s: Page=0' % nm)
            if who == 'host':
                v.ok(d.get('Lobby', {}).get('MinPlayers') == '2', '%s: MinPlayers=2' % nm)
            if who == 'host':
                v.ok(d.get('Bots', {}).get('OnlineGrudge') == '1' and d['Bots'].get('OnlineGrudgeDry') == str(PASSES[t]['dry']), '%s: [Bots] OnlineGrudge=1, OnlineGrudgeDry=%d' % (nm, PASSES[t]['dry']))
                v.ok(d.get('Down', {}).get('OnlineBotDown') == '0', '%s: [Down] OnlineBotDown=0 (bench only; live 1)' % nm)
                v.ok(d.get('BotFill', {}).get('OnlineHealthMul') == '1', '%s: [BotFill] OnlineHealthMul=1 (bench only; live 5)' % nm)
                v.ok(sum(1 for c in scr if c == 'tap RIGHT') == 6, '%s: 6 x tap RIGHT = slot F05' % nm)
                fb = [c for c in scr if c.startswith('firebot')]
                v.ok(len(fb) == 3 and all(re.match(r'^firebot \d+ \d+(\.\d+)? \d+(\.\d+)?( \d+( [01])?)?$', c) for c in fb), '%s: %d firebot lines, args ms maxm deg parse' % (nm, len(fb)))
                i0 = next((i for i, c in enumerate(scr) if c.startswith('waitstate 0x19')), 99999); i1 = next((i for i, c in enumerate(scr) if c.startswith('firebot')), -1)
                v.ok(0 <= i0 < i1, '%s: firebot comes after waitstate 0x19' % nm)
                ip = next((i for i, c in enumerate(scr) if c.startswith('pokeb 168e9e4+54+285 1')), -1)
                v.ok(i0 < ip < i1, '%s: pokeb rules +0x285 = 1 sits between waitstate 0x19 and the first firebot' % nm)
                v.ok(any(c.startswith('waitpeers 2') for c in scr), '%s: waitpeers 2' % nm)
                v.ok(any(c.startswith('tap R') and c.split()[1] == 'R' for c in scr), '%s: tap R (reload; key name R is in klauto.c kla_key row QWERTYUIOP)' % nm)
            else:
                v.ok('OnlineGrudge' not in d.get('Bots', {}), '%s: joiner has no OnlineGrudge key' % nm)
            # the merged ini the instance really gets (base + seat ini; [Script] replaces)
            mg = S.merge(S.read_ini(base), S.read_ini(p))
            md = {s.lower(): dict((k.lower(), val) for k, val in items if k) for s, items in mg}
            if who == 'host':
                v.ok(md.get('bots', {}).get('onlinegrudge') == '1' and md.get('down', {}).get('onlinebotdown') == '0' and md.get('botfill', {}).get('onlinehealthmul') == '1',
                     '%s: merged with the base ini the keys hold (OnlineGrudge=1, OnlineBotDown=0, OnlineHealthMul=1)' % nm)
                v.ok(md.get('bots', {}).get('onlinefill', '').startswith('1') and md.get('lobby', {}).get('keepround', '').startswith('1'), '%s: merged ini keeps the live OnlineFill=1 and KeepRound=1' % nm)
    v.ok(os.path.isfile('%s/README.txt' % KIT), 'README.txt')
    print('  info command: python tools/kl_grudge_bench_1106.py run A --owner-away   (then: run B --owner-away, summarize all)')
    print('RESULT: validate %s - %d FAIL' % ('OK' if not v.fail else 'FAILED', v.fail))
    return 1 if v.fail else 0


# ---------------------------------------------------------------- run
def solo_cmd(t, owner_away, secs):
    c = [sys.executable, 'tools/kl_solo_test.py', '--hook', '%s/hook_test' % KIT, '--tag', PASSES[t]['tag'], '--base', '%s/KLHook_base.ini' % KIT, '--n', '2',
         '--secs', str(secs), '--ini1', '%s/%s_host.ini' % (KIT, t), '--ini2', '%s/%s_join.ini' % (KIT, t), '--gap', str(GAP), '--relaunch', str(RELAUNCH), '--park', '1']
    if owner_away:
        c.append('--owner-away')
    return c


def run(args):
    owner_away, again = '--owner-away' in args, '--again' in args
    secs, allow, names, i = SECS, None, [], 0
    while i < len(args):
        a = args[i]
        if a == '--secs':
            secs = int(args[i + 1]); i += 1
        elif a == '--allow-live-dll':
            allow = args[i + 1]; i += 1
        elif not a.startswith('--'):
            names.append(a.upper() if a.upper() in PASSES else a)
        i += 1
    sel = list(PASSES) if names == ['ALL'] or names == ['all'] else (names or ['A'])
    if any(t not in PASSES for t in sel):
        print('RESULT: not started - pass must be A, B or all'); return 1
    if validate():
        print('RESULT: not started - validate failed'); return 1
    ld = N.live_state()['dll'] or ''
    if not ld.startswith(LIVE_SHIP_MD5) and not (allow and ld.startswith(allow)):
        print('RESULT: not started - live dinput8.dll md5 %s is not the pinned SHIP %s (a bench or TEST leftover is live). Pass --allow-live-dll <md5 prefix> to accept it.' % (ld[:8], LIVE_SHIP_MD5)); return 1
    if N.kl2_running():
        print('RESULT: not started - kl2.exe is running'); return 1
    if not owner_away and N.idle_s() < 300:
        print('RESULT: not started - owner input %d s ago (use --owner-away if the owner said they are away)' % N.idle_s()); return 1
    before = N.live_state()
    done_p = '%s/done.json' % KIT
    done = json.load(open(done_p)) if os.path.isfile(done_p) else {}
    rc_all = 0
    for t in sel:
        tag = PASSES[t]['tag']
        if tag in done and not again:
            print('skip %s (done at %s; --again reruns it)' % (t, done[tag])); continue
        if os.path.isfile('%s/STOP' % KIT):
            print('STOP file found: stopped before pass %s' % t); break
        for q in (1, 2):
            d = '%s/%s/inst%d' % (SOLO, tag, q)
            os.makedirs(d, exist_ok=True)
            if os.path.isfile('%s/KLShopPage.ini' % KIT):
                shutil.copy2('%s/KLShopPage.ini' % KIT, '%s/KLShopPage.ini' % d)
        cmd = solo_cmd(t, owner_away, secs)
        print('[pass %s] %s' % (t, PASSES[t]['what']), flush=True)
        print('  $ ' + ' '.join('"%s"' % c if ' ' in c else c for c in cmd), flush=True)
        with open('%s/%s_run.txt' % (KIT, tag), 'w') as out:
            rc = subprocess.run(cmd, cwd=ROOT, stdout=out, stderr=subprocess.STDOUT).returncode
        txt = N.load('%s/%s_run.txt' % (KIT, tag))
        res = [l for l in txt.splitlines() if l.startswith('RESULT')]
        print('  bench exit %d | %s' % (rc, (res[-1] if res else 'no RESULT line')[:200]), flush=True)
        after = N.live_state()
        if after != before:
            print('STOP: live game files changed by the bench: dll %s -> %s, ini %s -> %s. Restore by hand (the bench puts the original back; a kill leaves the TEST dll).' % (
                (before['dll'] or '-')[:8], (after['dll'] or '-')[:8], (before['ini'] or '-')[:8], (after['ini'] or '-')[:8]))
            rc_all = 1; break
        if 'RESULT: not started' in txt:
            print('STOP: kl_solo_test did not start (%s)' % (res[-1][:160] if res else '?')); rc_all = 1; break
        if 'ABORTED' in txt:
            print('STOP: owner input aborted pass %s; rerun with --again' % t); rc_all = 1; break
        done[tag] = time.strftime('%Y-%m-%d %H:%M')
        N.write(done_p, json.dumps(done, indent=1))
        time.sleep(30)
    print('live dll/ini after the run: %s' % ('byte-identical to before (dll %s, ini %s)' % ((before['dll'] or '-')[:8], (before['ini'] or '-')[:8]) if N.live_state() == before else 'DIFFERENT - see above'))
    summarize(sel)
    return rc_all


# ---------------------------------------------------------------- summarize
def logtext(tag, inst):
    p = '%s/%s/inst%d/KLHook.log' % (SOLO, tag, inst)
    return N.load(p) if os.path.isfile(p) else None


CRASH = re.compile(r'(?m)^\S+ (?:\S+: )?CRASH\b(?![^\n]*GUARDED)|KLHook_\d+\.dmp|kl2_\d+_crash_[^\s]*\.mdmp|unhandled exception')


def criteria(t, host, join):
    """-> [(id, ok, text)] for one pass from the host (and joiner) log texts."""
    dry = PASSES[t]['dry']
    R = lambda pat: re.findall(pat, host)
    out = []
    on = R(r'grudge: OnlineGrudge on (\(dry log\))?: HOST only')
    tab = R(r'private ZSoldier table [0-9a-f]+ made')
    sub = R(r'online grudge: sub-mode \[0x168e59c\] = 0 \(Fragile Alliance\): on')
    off = R(r'the hit hook is OFF')
    out.append(('a1', bool(on) and bool(tab) and bool(sub) and not off and bool(on[0]) == bool(dry),
                'hook installs: OnlineGrudge on%s=%d, private ZSoldier table=%d, FA sub-mode on=%d, "hook is OFF"=%d' % (' (dry)' if dry else '', len(on), len(tab), len(sub), len(off))))
    hits = re.findall(r'online grudge%s: hit #\d+ on AI heister \d+ \(actor [0-9a-f]+\): attacker [0-9a-f]+ vtable 00bb45f4 \(HUMAN\), hit type \d+, health ([\d.]+) -> ([\d.]+)' % (' dry' if dry else ''), host)
    drops = [(a, b) for a, b in hits if float(b) < float(a)]
    out.append(('a2', bool(drops), 'human hits reach kog_hit, attacker vtable 00bb45f4 (HUMAN), health drops: %d human hit(s), %d with a drop%s' % (len(hits), len(drops), (' e.g. %s -> %s' % drops[0]) if drops else '')))
    lk = r'online grudge%s: ' % (' dry' if dry else '')
    leth = R(lk + r'lethal blow on AI heister \d+ \(actor ([0-9a-f]+), health [\d.]+ -> [\d.]+\): attacker [0-9a-f]+ vtable 00bb45f4: HUMAN')
    died = R(lk + r'AI heister \d+ \(actor ([0-9a-f]+)\) died: lethal blow human .*-> killer found')
    would = R(r'online grudge dry: would call slot 129 \(killer \d+, victim -1\)')
    # same bot: a died line for an actor that also had a HUMAN lethal blow; the "would call" line must come after that died line
    same = [a for a in died if a in leth]
    wpos = [m.start() for m in re.finditer(r'online grudge dry: would call slot 129 \(killer \d+, victim -1\)', host)]
    dpos = [m.start() for a in same for m in re.finditer(lk + r'AI heister \d+ \(actor ' + a + r'\) died', host)]
    would_after = bool(dpos and wpos and max(wpos) > min(dpos))
    real = R(r'human \d+ killed an AI heister: made traitor \(slot 129 killer \d+ victim -1, then slot 105\)')
    if dry:
        out.append(('a3', bool(same) and would_after, 'lethal blow attributed (same actor): lethal-blow lines %d, "died ... killer found" %d, same actor %d, "would call slot 129" %d (after died: %s). If this fails with firebot fire DOWN present and large held ms: weapon too weak / semi-auto, not an OnlineGrudge defect' % (len(leth), len(died), len(same), len(would), would_after)))
        out.append(('a4', not R(r'made traitor') and not R(r'faulted'), 'nothing marked in the dry pass: "made traitor" %d, "faulted" %d' % (len(R(r'made traitor')), len(R(r'faulted')))))
    else:
        out.append(('b2', bool(set(leth) & set(died)) and bool(real), 'lethal blow + real mark: lethal %d, died/killer found %d, "made traitor (slot 129 ... victim -1, then slot 105)" %d; "traitors now:" %d' % (len(leth), len(died), len(real), len(R(r'traitors now:')))))
        out.append(('b3', not R(r'faulted'), '"slot 129 / 105 faulted": %d' % len(R(r'faulted'))))
    cr = [m for m in CRASH.findall(host)] + ([m for m in CRASH.findall(join)] if join else [])
    out.append(('crash', not cr, 'no CRASH|FATAL|.dmp in the host/joiner logs (%d)' % len(cr)))
    rs = N.load('%s/%s_run.txt' % (KIT, PASSES[t]['tag'])) if os.path.isfile('%s/%s_run.txt' % (KIT, PASSES[t]['tag'])) else ''
    out.append(('result', 'RESULT: inst1 IN ROUND' in rs or re.search(r'inst1 \| .*PASS', rs) is not None or 'RESULT PASS' in rs, 'bench output has RESULT PASS / IN ROUND (script reached pass)'))
    fb = R(r'firebot target rec'); fd = R(r'firebot fire DOWN'); fo = R(r'firebot over')
    out.append(('rig', bool(fb) and bool(fd) and bool(fo), 'rig sanity (diagnostic): firebot target %d, fire DOWN %d, firebot over %d' % (len(fb), len(fd), len(fo))))
    return out


def summarize(names):
    sel = list(PASSES) if not names or names in (['all'], ['ALL']) else [n.upper() for n in names]
    rc = 0
    for t in sel:
        tag = PASSES[t]['tag']
        host, join = logtext(tag, 1), logtext(tag, 2)
        print('== pass %s (%s)' % (t, PASSES[t]['what']))
        if host is None:
            print('   no host log yet (%s/%s/inst1/KLHook.log)' % (SOLO, tag)); continue
        bad = 0
        for cid, ok, text in criteria(t, host, join):
            gate = cid != 'rig'
            print('   %-6s %-4s %s' % (cid, 'PASS' if ok else ('FAIL' if gate else 'warn'), text))
            bad += (not ok) and gate
        print('   PASS %s: %s' % (t, 'ALL GATES' if not bad else '%d gate(s) FAILED' % bad))
        for l in host.splitlines():
            if re.search(r'online grudge|OnlineGrudge|firebot|GRUDGE1106', l):
                print('     | ' + l[:230])
        rc |= 1 if bad else 0
    return rc


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    cmd, rest = a[0], a[1:]
    if cmd == 'gen':
        dll = rest[rest.index('--test-dll') + 1] if '--test-dll' in rest else None
        return gen(dll, '--force-live' in rest)
    if cmd == 'validate':
        return validate()
    if cmd == 'run':
        return run(rest)
    if cmd == 'summarize':
        return summarize(rest)
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
