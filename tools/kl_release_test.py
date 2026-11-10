"""Off-game self-test of kl_release.py install / uninstall / verify on fake folders (no game files, no network).
Covers: a stock source that is mmapped while built and then moved into the backup (Windows refuses a mapped move),
resume after a run stopped right after / right before the backup move, re-install over an edited keep_user ini,
verify without Payday 2, a bots zip made + installed against its main zip ('out:' ref, --only refusal).
Prints one RESULT: line; exit 1 on a FAIL."""
import os, sys, json, shutil, tempfile, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_release as R

R.low_priority = lambda: None
FAILS = []


def check(cond, what):
    print(('ok    ' if cond else 'FAIL  ') + what)
    if not cond:
        FAILS.append(what)


def sha(p):
    return hashlib.sha1(open(p, 'rb').read()).hexdigest()


def tree(root):
    out = {}
    for r, ds, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            out[R.nrm(os.path.relpath(p, root))] = sha(p)
    return out


OWNER_INI = (b'; backup in G:\\x\\Kane & Lynch 2 - Dog Days\\old\r\n[KLHook]\r\nLog=2\r\n[Ambience]\r\n'
             b'Folder=C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Ambience\r\n'
             b'[Music]\r\nEnable=0\r\nFolder = C:/Steam/steamapps/common/PAYDAY 2/assets\r\n'
             b'FolderB=C:\\Steam\\steamapps\\common\\PAYDAY 2 extra\\b\r\n[Stinger]\r\n'
             b'Folder=C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\r\nName=Kane & Lynch 2 - Dog Days\\x\r\n')


def check_localize():
    """the owner's absolute game folders become this PC's; comments, other keys and look-alike folders stay"""
    src = OWNER_INI.split(b'\r\n')
    out = R.localize_ini_bytes(OWNER_INI, dict(dd='E:\\Games\\Kane & Lynch 2 - Dog Days\\', pd2='F:\\P D\\PAYDAY 2'))
    lines = out.split(b'\r\n')
    check(out.count(b'\r\n') == OWNER_INI.count(b'\r\n') and b'\n' not in out.replace(b'\r\n', b''), 'L CRLF kept')
    check(lines[0] == src[0], 'L comment line untouched')
    check(lines[4] == b'Folder=E:\\Games\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Ambience', 'L ambience folder moved (%r)' % lines[4])
    check(lines[7] == b'Folder = F:\\P D\\PAYDAY 2/assets', 'L PD2 folder moved, key spacing kept (%r)' % lines[7])
    check(lines[8] == src[8], 'L "PAYDAY 2 extra" untouched')
    check(lines[10] == b'Folder=E:\\Games\\Kane & Lynch 2 - Dog Days', 'L bare game folder moved (%r)' % lines[10])
    check(lines[11] == src[11], 'L other keys untouched')
    nopd = R.localize_ini_bytes(OWNER_INI, dict(dd='E:\\DD\\Kane & Lynch 2 - Dog Days', pd2=None))
    check(nopd.split(b'\r\n')[7] == src[7], 'L no Payday 2: its folder left as it was')


def setup(base):
    dd, dm, pkg = (os.path.join(base, x) for x in ('dd', 'dm', 'pkg'))
    for d in (dd, dm, os.path.join(pkg, 'patches')):
        os.makedirs(d)
    rnd = __import__('random').Random(7)
    open(os.path.join(dd, 'kl2.exe'), 'wb').write(b'MZ' + bytes(rnd.getrandbits(8) for _ in range(4000)))
    stock = bytes(rnd.getrandbits(8) for _ in range(300000))
    open(os.path.join(dd, 'Big.str'), 'wb').write(stock)
    os.utime(os.path.join(dd, 'Big.str'), (1e9, 1e9))
    open(os.path.join(dd, 'KLHook.ini'), 'wb').write(b'[KLHook]\nLog=1\n')     # the user's own ini (keep_user)
    live = os.path.join(base, 'live'); os.makedirs(live)
    mod = stock[:100000] + b'MOD' * 1000 + stock[150000:]
    open(os.path.join(live, 'Big.str'), 'wb').write(mod)
    open(os.path.join(live, 'New.txt'), 'wb').write(b'new file\n')
    open(os.path.join(live, 'KLHook.ini'), 'wb').write(OWNER_INI)
    mk = R.Maker(dd, dm, None, pkg, level=3, log=lambda *a: None)
    ents = []
    for rel, refs, extra in (('Big.str', ['dd:Big.str'], dict(stock=True)), ('New.txt', [], {}), ('KLHook.ini', [], dict(keep_user=True))):
        p = os.path.join(live, rel)
        s = sha(p)
        pf = os.path.join(pkg, 'patches', s[:20] + '.klp')
        mk.make_file(p, refs, pf)
        ents.append(dict(group='core', rel=rel, size=os.path.getsize(p), sha1=s, patch=os.path.basename(pf),
                         refs={r: [os.path.getsize(mk.resolve(r)), sha(mk.resolve(r))] for r in refs}, **extra))
    mk.sources.close()
    json.dump(dict(name='KL Merge', version=R.VERSION, kl2_sha1=sha(os.path.join(dd, 'kl2.exe')), entries=ents),
              open(os.path.join(pkg, 'manifest.json'), 'w'))
    return dd, dm, pkg, live


def run(*argv):
    return R.main(list(argv))


def write_zip(path, members):
    import zipfile
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, d in members:
            z.writestr(n, d)


def check_out_refs(base):
    """O: a bots zip is patched against its main zip as built by the same install ('out:' ref)"""
    rnd = __import__('random').Random(11)
    blob = lambda n: bytes(rnd.getrandbits(8) for _ in range(n // 2)) * 2
    dd, dm, pkg = (os.path.join(base, x) for x in ('odd', 'odm', 'opkg'))
    os.makedirs(dm)
    open(os.path.join(os.makedirs(dd) or dd, 'kl2.exe'), 'wb').write(b'MZ' + blob(2000))
    prp, tex, buf = blob(60000), blob(150000), blob(90000)
    maps = os.path.join(dd, 'KLExpansion', 'Maps')
    main_rel, bots_rel = 'KLExpansion/Maps/DMX/F99/F99_Main.zip', 'KLExpansion/Maps/DMX/F99/F99_Main.bots.zip'
    write_zip(os.path.join(dd, main_rel), [('F99_Main.prp', prp), ('F99_Main.TEX', tex), ('F99_Main.buf', buf)])
    write_zip(os.path.join(dd, bots_rel), [('F99_Main.prp', prp[:30000] + b'BOTS' + prp[30004:]), ('F99_Main.TEX', tex), ('F99_Main.buf', buf)])
    write_zip(os.path.join(maps, 'DMZ', 'F98', 'F98_Main.zip'), [('F98_Main.prp', blob(40000))])        # nothing in common
    write_zip(os.path.join(maps, 'DMZ', 'F98', 'F98_Main.bots.zip'), [('F98_Main.prp', blob(40000))])
    check(R.main(['make', pkg, '--dd', dd, '--dm', dm, '--only', 'map:DMX,map:DMZ', '--level', '3']) == 0, 'O make')
    man = json.load(open(os.path.join(pkg, 'manifest.json')))
    man['kl2_sha1'] = sha(os.path.join(dd, 'kl2.exe'))
    E = {e['rel']: e for e in man['entries']}
    b = E[bots_rel]
    check(list(b['refs']) == ['out:' + main_rel] and b['refs']['out:' + main_rel] == [E[main_rel]['size'], E[main_rel]['sha1']],
          'O bots refs = out:<main> with its size + sha1 (got %s)' % b['refs'])
    check(b['patch'].endswith('.out.klp') and b['patch_size'] < b['size'] // 8, 'O bots patch small (%d of %d)' % (b['patch_size'], b['size']))
    zb = E['KLExpansion/Maps/DMZ/F98/F98_Main.bots.zip']
    alt = [os.path.getsize(os.path.join(pkg, 'patches', zb['sha1'][:20] + x)) for x in ('.klp', '.out.klp')]
    check(zb['patch_size'] == min(alt), 'O unrelated bots: the smaller of out: and old patch kept (%d of %s)' % (zb['patch_size'], alt))
    lives = {rel: open(os.path.join(dd, rel), 'rb').read() for rel in E}
    for rel in E:                                       # the player's Dog Days: no mod files yet
        os.remove(os.path.join(dd, rel))
    shutil.rmtree(maps)
    man['entries'] = man['entries'][::-1]               # bots listed first: install must still build the main zip first
    json.dump(man, open(os.path.join(pkg, 'manifest.json'), 'w'))
    pristine = tree(dd)
    args = ('--dm', dm, '--pkg', pkg, '--yes')
    check(run('install', dd, *args) == 0, 'O install')
    check(all(open(os.path.join(dd, rel), 'rb').read() == d for rel, d in lives.items()), 'O every zip byte-exact')
    check(not os.path.exists(os.path.join(dd, R.TMPDIR)), 'O temp folder gone')
    check(run('verify', dd, '--pkg', pkg) == 0, 'O verify clean')
    check(run('uninstall', dd, '--yes') == 0 and tree(dd) == pristine, 'O uninstall byte-exact')
    # --only: the main zip in another group, not installed -> refused before anything is written
    for e in man['entries']:
        if e['rel'] == main_rel:
            e['group'] = 'map:DMY'
    json.dump(man, open(os.path.join(pkg, 'manifest.json'), 'w'))
    check(run('install', dd, *args, '--only', 'DMX') == 2 and tree(dd) == pristine, 'O --only without its source refused, nothing written')
    check(run('install', dd, *args, '--only', 'DMY') == 0, 'O --only DMY (main zip alone)')
    check(run('install', dd, *args, '--only', 'DMX') == 0, 'O --only DMX built from the installed main zip')
    check(open(os.path.join(dd, bots_rel), 'rb').read() == lives[bots_rel], 'O bots zip byte-exact from the installed source')
    open(os.path.join(dd, bots_rel), 'ab').write(b'x')               # something to do; the installed main is edited -> refused
    open(os.path.join(dd, main_rel), 'ab').write(b'x')
    check(run('install', dd, *args, '--only', 'DMX') == 2, 'O --only DMX refused when the installed main zip differs')
    check(run('uninstall', dd, '--yes') == 0, 'O uninstall after --only')


def main():
    base = tempfile.mkdtemp(prefix='klrel_')
    try:
        dd, dm, pkg, live = setup(base)
        args = ('--dm', dm, '--pkg', pkg, '--yes')
        pristine = tree(dd)

        # A: plain install + uninstall (the mapped stock Big.str must move into the backup)
        check(run('install', dd, *args) == 0, 'A install')
        check(sha(os.path.join(dd, 'Big.str')) == sha(os.path.join(live, 'Big.str')), 'A Big.str is the mod file')
        check(os.path.exists(os.path.join(dd, R.BACKUP, 'Big.str')), 'A stock Big.str moved to the backup')
        check(os.path.exists(os.path.join(dd, 'KLHook.ini.new-' + R.VERSION)), 'A user ini kept, default saved beside it')
        check(not os.path.exists(os.path.join(dd, R.TMPDIR)), 'A temp folder gone')
        check(run('verify', dd, '--pkg', pkg) == 0, 'A verify clean')
        check(run('uninstall', dd, '--yes') == 0, 'A uninstall')
        back = {k: v for k, v in tree(dd).items() if not k.startswith(R.BACKUP)}
        check(back == pristine, 'A uninstall byte-exact')

        # B: stopped right after the backup move (journal 'replaced', backup there, dest missing): resume must keep 'replaced'
        bk = os.path.join(dd, R.BACKUP, 'Big.str')
        os.replace(os.path.join(dd, 'Big.str'), bk)
        json.dump(dict(entries=[dict(rel='Big.str', sha1='x', group='core', size=0, action='replaced', backup=R.BACKUP + '/Big.str')], dirs=[]),
                  open(R.journal_path(dd), 'w'))
        os.makedirs(os.path.join(dd, R.TMPDIR)); open(os.path.join(dd, R.TMPDIR, 'junk.part'), 'wb').write(b'x')
        check(run('install', dd, *args) == 0, 'B resumed install')
        j = json.load(open(R.journal_path(dd)))
        rec = [x for x in j['entries'] if x['rel'] == 'Big.str'][0]
        check(rec['action'] == 'replaced' and rec['backup'] == R.BACKUP + '/Big.str', 'B record stays replaced (got %s)' % rec['action'])
        check(run('uninstall', dd, '--yes') == 0, 'B uninstall')
        back = {k: v for k, v in tree(dd).items() if not k.startswith(R.BACKUP)}
        check(back == pristine, 'B stock Big.str back after uninstall')
        check(not os.path.exists(os.path.join(dd, R.TMPDIR)), 'B uninstall removed the temp folder')

        # C: stopped right before the move (journal 'replaced', backup missing, dest still stock): uninstall leaves it
        json.dump(dict(entries=[dict(rel='Big.str', sha1='x', group='core', size=0, action='replaced', backup=R.BACKUP + '/_klmerge_replaced/t/Big.str')], dirs=[]),
                  open(R.journal_path(dd), 'w'))
        run('uninstall', dd, '--yes')
        check(sha(os.path.join(dd, 'Big.str')) == pristine['Big.str'], 'C stock Big.str untouched')
        check(not [f for f in os.listdir(dd) if '.edited-' in f], 'C no .edited copy made')
        os.remove(R.journal_path(dd))

        # D: re-install over the mod's ini after the user edited it: the record stays ours, uninstall cleans the .new file
        os.remove(os.path.join(dd, 'KLHook.ini'))
        check(run('install', dd, *args) == 0, 'D install without a user ini')
        open(os.path.join(dd, 'KLHook.ini'), 'ab').write(b'Edited=1\n')
        os.remove(os.path.join(dd, 'New.txt'))                       # something to do so the install runs again
        check(run('install', dd, *args) == 0, 'D re-install')
        j = json.load(open(R.journal_path(dd)))
        rec = [x for x in j['entries'] if x['rel'] == 'KLHook.ini'][0]
        check(rec['action'] == 'new', 'D ini record stays new (got %s)' % rec['action'])
        check(run('uninstall', dd, '--yes') == 0, 'D uninstall')
        check(not os.path.exists(os.path.join(dd, 'KLHook.ini.new-' + R.VERSION)), 'D .new ini removed')
        check(not os.path.exists(os.path.join(dd, 'KLHook.ini')), 'D mod ini not left as live ini')

        # G: make picks up the hook's own files beside KLHook.ini (KLReverbBoxes.ini, KLGrenade\*.wav)
        gdd = os.path.join(base, 'gdd')
        for d in ('KLGrenade', 'Scenes', os.path.join('KLExpansion', 'Maps')):
            os.makedirs(os.path.join(gdd, d))
        for rel in ('KLReverbBoxes.ini', 'KLGrenade/grenade_pin.wav', 'KLGrenade/grenade_throw.wav', 'KLGrenade/x.wav.before-1110',
                    'Scenes/kaneandlynch.WAV', 'Scenes/kaneandlynch_deadmen.WAV', 'Scenes/kaneandlynch_deadmen.WAV.before-menusounds_1110',
                    'Scenes/kaneandlynch_deadmen.klms', 'Scenes/other_deadmen.WHD'):
            open(os.path.join(gdd, rel), 'wb').write(b'x')
        fake = type('M', (), dict(dd=gdd, pd2_skipped=[], stock_dd=lambda self, rel: os.path.join(gdd, rel)))()
        T = {t['rel']: t for t in R.enumerate_targets(fake, ['core'])}
        check(sorted(T) == ['KLGrenade/grenade_pin.wav', 'KLGrenade/grenade_throw.wav', 'KLReverbBoxes.ini', 'Scenes/kaneandlynch_deadmen.WAV',
                            'Scenes/kaneandlynch_deadmen.klms', 'Scenes/other_deadmen.WHD'], 'G make lists the hook files (got %s)' % sorted(T))
        check(T['Scenes/kaneandlynch_deadmen.WAV'].get('refs') == ['dd:Scenes/kaneandlynch.WAV'], 'G themed bank patched against its stock bank')
        check(T['Scenes/other_deadmen.WHD']['kind'] == 'lit' and T['Scenes/kaneandlynch_deadmen.klms']['kind'] == 'lit', 'G no stock sibling -> literal')

        # F: a fresh install points the ini's game folders at this PC; verify, re-install and uninstall accept it as ours
        check_localize()
        pd2 = os.path.join(base, 'p1', 'PAYDAY 2'); os.makedirs(pd2)
        fargs = ('--dm', dm, '--pd2', pd2, '--pkg', pkg, '--yes')
        edited = [f for f in os.listdir(dd) if '.edited-' in f]
        check(run('install', dd, *fargs) == 0, 'F install without a user ini')
        ini = open(os.path.join(dd, 'KLHook.ini'), 'rb').read()
        check(('Folder=%s\\KLExpansion\\Ambience' % os.path.abspath(dd)).encode() in ini, 'F ambience folder is this PC\'s')
        check(('Folder = %s/assets' % os.path.abspath(pd2)).encode() in ini, 'F PD2 folder is this PC\'s')
        j = json.load(open(R.journal_path(dd)))
        rec = [x for x in j['entries'] if x['rel'] == 'KLHook.ini'][0]
        check(rec.get('local_sha1') == sha(os.path.join(dd, 'KLHook.ini')), 'F journal holds the localized sha1')
        check(run('verify', dd, '--pkg', pkg, '--pd2', pd2) == 0, 'F verify clean on the localized ini')
        before = tree(dd)
        check(run('install', dd, *fargs) == 0 and tree(dd) == before, 'F second install changes nothing')
        pd2b = os.path.join(base, 'p2', 'PAYDAY 2'); os.makedirs(pd2b)
        check(run('install', dd, '--dm', dm, '--pd2', pd2b, '--pkg', pkg, '--yes') == 0, 'F install after Payday 2 moved')
        ini = open(os.path.join(dd, 'KLHook.ini'), 'rb').read()
        check(('Folder = %s/assets' % os.path.abspath(pd2b)).encode() in ini, 'F unedited ini re-pointed at the new Payday 2 folder')
        j = json.load(open(R.journal_path(dd)))
        rec = [x for x in j['entries'] if x['rel'] == 'KLHook.ini'][0]
        check(rec.get('local_sha1') == sha(os.path.join(dd, 'KLHook.ini')), 'F journal follows the re-pointed ini')
        check(run('uninstall', dd, '--yes') == 0, 'F uninstall')
        check(not os.path.exists(os.path.join(dd, 'KLHook.ini')), 'F localized ini removed, not kept as edited')
        check([f for f in os.listdir(dd) if '.edited-' in f] == edited, 'F no new .edited copy')

        # E: verify skips Payday 2 entries when Payday 2 is absent
        man = json.load(open(os.path.join(pkg, 'manifest.json')))
        man['entries'].append(dict(group='core', rel='Pd.bin', size=1, sha1='y', patch='none', refs={'pd:x.bin': [1, 'z']}))
        json.dump(man, open(os.path.join(pkg, 'manifest.json'), 'w'))
        R.find_game = lambda folder: None
        check(run('install', dd, *args) == 0, 'E install without Payday 2')
        check(run('verify', dd, '--pkg', pkg) == 0, 'E verify without Payday 2 skips pd: entries')

        check_out_refs(base)
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print('RESULT: %s (%d fails)' % ('FAIL' if FAILS else 'PASS', len(FAILS)))
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
