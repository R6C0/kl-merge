"""campaign_ui_1110 kit: luvsic's Dead Men UI, inside his campaign only (branch campaign-ui; in contribution with luvsic).

install.py            1) the 17 installed campaign levels (campaign_1109, tools/kl_campaign.py manifests) are swapped for the --ui builds
                         (Dead Men HUD art + typefaces baked into each level archive); the old files are hard-linked (else copied) into
                         <kit>\\backup first.
                      2) menu copies <kit>\\menu\\Patch01*_campui.zip -> beside the archives they were made from (KLExpansion\\Overlay + game root).
                      3) dll swap (pinned to the live dinput8.dll) and the [CampaignUI] ini block appended.
install.py --undo     exact reverse: levels back from <kit>\\backup (old manifests too), menu copies removed, dll + ini back.
install.py --dry      checks every pin and every refusal, writes nothing. (also valid with --undo)
Refuses (nothing written) when: kl2.exe has a thread, a pinned md5 differs, a target already exists, a campaign level is not the
1109 install or was changed since, or the drive lacks room. A kl2.exe with 0 threads (a crashed run's zombie) does not count.
Rehearsal: KLCAMP_DD=<scratch game folder> KLCAMP_IDS="M01 M14 M07F" (a subset); the code path is the same.
"""
import hashlib, json, os, shutil, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__))
DD = os.environ.get('KLCAMP_DD') or r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TOOLS = os.environ.get('KLCAMP_TOOLS') or r'C:\kl-merge\kl-merge\.claude\worktrees\campui\tools'
OUT = os.environ.get('KLCAMP_OUT') or r'C:\kl_build_1024\campaign_ui_1110\anp_out'
WORK = os.environ.get('KLCAMP_WORK') or r'C:\kl_build_1024\campaign_ui_1110\anp_work'
SHIP = os.path.join(KIT, 'dinput8.dll')
LIVE_DLL = '258daf8eb281c9d47809801e619e9a48'        # the campaign_1110 SHIP build installed 2026-11-10 (camera/voice)
LIVE_INI = 'd217832b4c76c3f771570105be722fad'   # only recorded (the ini is edited in game, so it is NOT a refusal pin)
TAG = '.before-campui1110'
BACKUP = os.path.join(KIT, 'backup')
STATE = os.path.join(KIT, 'installed.json')
MENU_DIR = os.path.join(KIT, 'menu')
MENU_PINS = os.path.join(MENU_DIR, 'menu_pins.json')    # {"<target rel to DD>": {"base": md5 of the archive it was made from, "copy": md5}}

BLOCK = r"""
; ==== Dead Men campaign UI (luvsic's menu pages, scoped to the campaign) - campaign_ui_1110 ====
[CampaignUI]
; Menu=1: Play page gets a "Dead Men Campaign" row (New game / Chapters / Difficulty). Needs [Campaign] Enable=1 (recommended on)
Menu=1
"""

sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True
import kl_campaign as K


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def ids():
    e = os.environ.get('KLCAMP_IDS')
    return e.split() if e else list(K.ALL_IDS)


def die(m): sys.exit('REFUSED: ' + m)


def menu_targets():
    pins = json.load(open(MENU_PINS, encoding='utf-8'))
    return pins


def kitname(rel): return rel.replace(chr(92), '__').replace('/', '__')


def link_or_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try: os.link(src, dst)
    except OSError: shutil.copyfile(src, dst)


def level_dirs(i):
    src, dst, _ = K.layout(i, OUT, DD)
    return src, dst


def preflight(undo):
    errs = []
    if K.game_running(): errs.append('kl2.exe is running (a thread count above 0): close the game first')
    dll, ini = os.path.join(DD, 'dinput8.dll'), os.path.join(DD, 'KLHook.ini')
    if not undo:
        if md5(dll) != LIVE_DLL: errs.append('live dinput8.dll %s is not the pinned %s' % (md5(dll), LIVE_DLL))
        if '[campaign]' not in open(ini, 'rb').read().decode('ascii', 'replace').lower(): errs.append('KLHook.ini has no [Campaign] block: the campaign_1110 install is not there')
        for p in (dll + TAG, ini + TAG):
            if os.path.exists(p): errs.append('%s exists: already installed? (run --undo first)' % p)
        if os.path.exists(STATE): errs.append('%s exists: already installed' % STATE)
        if os.path.exists(BACKUP) and os.listdir(BACKUP): errs.append('%s is not empty' % BACKUP)
        if md5(SHIP) != open(os.path.join(KIT, 'dinput8.dll.md5')).read().split()[0]: errs.append('kit dinput8.dll is not the staged build')
        need = 0
        for i in ids():
            src, dst = level_dirs(i)
            mp = os.path.join(dst, K.MANIFEST)
            if not os.path.isfile(mp): errs.append('%s: not installed by tools/kl_campaign.py (no manifest)' % i); continue
            old = json.load(open(mp, encoding='utf-8'))
            if old.get('tool') != 'kl_campaign': errs.append('%s: foreign manifest' % i); continue
            for f, h in old['files'].items():
                p = os.path.join(dst, f)
                if not os.path.isfile(p) or md5(p) != h: errs.append('%s: %s changed since the 1109 install' % (i, f)); break
            if not os.path.isfile(os.path.join(src, K.layout(i, OUT, DD)[2])): errs.append('%s: --ui build missing in %s' % (i, OUT))
            else: need += sum(os.path.getsize(os.path.join(src, f)) for f in K._files(src))
        probe = DD
        free = shutil.disk_usage(probe).free
        if free < need * 1.05 + (256 << 20): errs.append('needs %d MB free for the new levels, %d MB free' % (need >> 20, free >> 20))
        for rel, p in menu_targets().items():
            t = os.path.join(DD, rel)
            if os.path.exists(t): errs.append('%s exists' % t)
            b = os.path.join(DD, rel.replace('_campui', ''))
            if not os.path.isfile(b): errs.append('menu base %s missing' % b)
            elif md5(b) != p['base']: errs.append('menu base %s changed since the copy was built (%s != %s): rebuild with tools/kl_campui_menu.py' % (b, md5(b), p['base']))
    else:
        if not os.path.exists(STATE): errs.append('not installed (no %s)' % STATE)
        else:
            st = json.load(open(STATE, encoding='utf-8'))
            if md5(dll) != st['dll']: errs.append('live dll is no longer the kit build: restore %s by hand' % (dll + TAG))
            for i in st['levels']:
                src, dst = level_dirs(i)
                mp = os.path.join(dst, K.MANIFEST)
                if not os.path.isfile(mp): errs.append('%s: manifest gone' % i); continue
                cur = json.load(open(mp, encoding='utf-8'))
                for f, h in cur['files'].items():
                    p = os.path.join(dst, f)
                    if not os.path.isfile(p) or md5(p) != h: errs.append('%s: %s changed since this install' % (i, f)); break
                if not os.path.isdir(os.path.join(BACKUP, i)): errs.append('%s: no backup in %s' % (i, BACKUP))
            for rel, h in st['menu'].items():
                t = os.path.join(DD, rel)
                if os.path.exists(t) and md5(t) != h: errs.append('%s changed since this install' % t)
    return errs


def install(dry):
    errs = preflight(False)
    if errs: die('\n  '.join(errs))
    if dry: print('install: all pins and refusals OK (dry run, nothing written): levels %s, %d menu copies' % (' '.join(ids()), len(menu_targets()))); return
    dll, ini = os.path.join(DD, 'dinput8.dll'), os.path.join(DD, 'KLHook.ini')
    lv = ids()
    st = dict(levels=[], menu={}, dll=md5(SHIP), old_dll=LIVE_DLL, old_ini=LIVE_INI)
    json.dump(dict(st, partial=True), open(STATE, 'w'))                      # written first: a half install can still be undone
    try:
        for i in lv:                                                          # 1. backup (hard link: install replaces files, never rewrites in place)
            src, dst = level_dirs(i)
            old = json.load(open(os.path.join(dst, K.MANIFEST), encoding='utf-8'))
            for f in list(old['files']) + [K.MANIFEST]:
                if f == K.MANIFEST:                                           # the manifest is rewritten in place by install_level: copy, never link
                    os.makedirs(os.path.join(BACKUP, i), exist_ok=True); shutil.copyfile(os.path.join(dst, f), os.path.join(BACKUP, i, f))
                else: link_or_copy(os.path.join(dst, f), os.path.join(BACKUP, i, f))
        for i in lv:                                                          # 2. levels (kl_campaign.install_level: .klpart + replace, manifest last)
            K.install_level(i, OUT, DD, WORK, running=lambda: False, force=False)
            st['levels'].append(i)
        for rel in menu_targets():                                           # 3. menu copies
            t = os.path.join(DD, rel); shutil.copyfile(os.path.join(MENU_DIR, kitname(rel)), t + '.klpart'); os.replace(t + '.klpart', t)
            st['menu'][rel] = md5(t)
        shutil.copy2(dll, dll + TAG); shutil.copy2(ini, ini + TAG)           # 4. dll + ini
        shutil.copy2(SHIP, dll)
        text = open(ini, 'rb').read().decode('ascii')
        if '[campaignui]' in text.lower(): raise SystemExit('ini already has [CampaignUI]')
        open(ini, 'wb').write((text + ('' if text.endswith('\n') else '\n') + BLOCK.lstrip('\n')).encode('ascii'))
        st['ini'] = md5(ini)
        json.dump(st, open(STATE, 'w'), indent=1)
    except BaseException:
        print('install failed: reverting what was done')
        try: revert(lv, list(st['menu']) + [r for r in menu_targets() if r not in st['menu']])
        except BaseException as e: print('REVERT FAILED (%s): restore by hand from %s and the *%s files' % (e, BACKUP, TAG)); json.dump(dict(st, partial=True), open(STATE, 'w'))
        else:
            if os.path.exists(STATE): os.remove(STATE)
        raise
    print('installed: %d levels, %d menu copies, dll %s -> %s, ini %s -> %s' % (len(lv), len(st['menu']), LIVE_DLL[:8], st['dll'][:8], LIVE_INI[:8], st['ini'][:8]))


def revert(levels, menu_rels):
    """the shared reverse of install(): tolerant of a half install (each step only when its backup / file is there)"""
    dll, ini = os.path.join(DD, 'dinput8.dll'), os.path.join(DD, 'KLHook.ini')
    for i in levels:
        src, dst = level_dirs(i)
        bk = os.path.join(BACKUP, i)
        if not os.path.isdir(bk): continue
        mp = os.path.join(dst, K.MANIFEST)
        cur = json.load(open(mp, encoding='utf-8')) if os.path.isfile(mp) else {'files': {}}
        oldfiles = [os.path.relpath(os.path.join(d, f), bk).replace(os.sep, '/') for d, _, fs in os.walk(bk) for f in fs]
        for f in oldfiles:                                                   # old files back (manifest last)
            if f == K.MANIFEST: continue
            t = os.path.join(dst, f); os.makedirs(os.path.dirname(t), exist_ok=True)
            shutil.copyfile(os.path.join(bk, f), t + '.klpart'); os.replace(t + '.klpart', t)
        for f in cur['files']:                                               # files only the --ui build had
            if f not in oldfiles and os.path.isfile(os.path.join(dst, f)): os.remove(os.path.join(dst, f))
        shutil.copyfile(os.path.join(bk, K.MANIFEST), mp + '.klpart'); os.replace(mp + '.klpart', mp)
    for rel in menu_rels:
        t = os.path.join(DD, rel)
        if os.path.exists(t): os.remove(t)
    if os.path.exists(dll + TAG): shutil.copy2(dll + TAG, dll); os.remove(dll + TAG)
    if os.path.exists(ini + TAG):
        text = open(ini, 'rb').read().decode('ascii')
        blk = BLOCK.lstrip(chr(10))
        if blk in text: text = text.replace(blk, '', 1)                      # exactly our lines; later edits elsewhere stay
        else: print('ini: [CampaignUI] block was edited; left as is (delete the section by hand)')
        open(ini, 'wb').write(text.encode('ascii'))
        if md5(ini) == md5(ini + TAG): os.remove(ini + TAG); print('ini restored byte-exact')
        else: print('ini: campaign UI lines removed, other edits kept; backup left at %s' % (ini + TAG))
    shutil.rmtree(BACKUP, ignore_errors=True)


def undo(dry):
    errs = preflight(True)
    if errs: die('\n  '.join(errs))
    st = json.load(open(STATE, encoding='utf-8'))
    if st.get('partial'): die('%s is partial (an install failed half way): restore by hand from %s and the *%s files' % (STATE, BACKUP, TAG))
    if dry: print('undo: all pins OK (dry run, nothing written)'); return
    revert(st['levels'], list(st['menu']))
    dll = os.path.join(DD, 'dinput8.dll')
    os.remove(STATE)
    print('undone: %d levels back to the 1109 files, menu copies removed, dll %s' % (len(st['levels']), md5(dll)[:8]))


if __name__ == '__main__':
    dry = '--dry' in sys.argv
    undo(dry) if '--undo' in sys.argv else install(dry)
