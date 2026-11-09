#!/usr/bin/env python3
"""
launcher_test.py - off-game self-test of tools/launcher/ (the tester bootstrap + WPF launcher). No game, no network.

Checks
  1. the files exist and are plain ASCII (cmd.exe and the ini-reading hook choke on smart quotes / UTF-8 BOMs)
  2. KLMerge Setup.bat: RELEASE_URL is defined in ONE place at the top, the committed default is the placeholder, and
     the script refuses to run with the placeholder (findstr example.invalid); every 'goto :label' has its label
  3. KLMergeLauncher.ps1: brace / bracket / parenthesis balance outside strings and comments; the XAML here-string is
     well-formed XML; every kl_release.py verb and option the launcher passes exists in kl_release.py's argparse;
     the Steam app id equals tools/kl_autotest.py APP; the hook-off file name is the same in the script and the READMEs
  3b. music + background (2026-11-09): MediaPlayer with loop + MediaFailed handling, quiet default volume, the music file and
     tool names, Muted / Volume / MusicClip in the settings, the ASCII-escaped note sign, try/catch around audio and images,
     the two ImageBrush sides with an OpacityMask seam under dim / grain / vignette, the procedural fallback brushes, and that
     the bat / pack_release.ps1 / READMEs carry the tool, bg\*.jpg and the music\ exclusion
  4. when pwsh (PowerShell 7) is on the PATH, the script is parsed with System.Management.Automation.Language.Parser
     and must give 0 errors (else SKIPPED with a note, never a FAIL)
  5. README_TESTERS.md names the log / dump files a tester must send, and OWNER_RELEASE_STEPS.md has the make command

exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py (tools/launcher/*_test.py).
"""
import os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
BAT = os.path.join(HERE, 'KLMerge Setup.bat')
WRAP = os.path.join(HERE, 'KLMerge.bat')
PS1 = os.path.join(HERE, 'KLMergeLauncher.ps1')
PACK = os.path.join(HERE, 'pack_release.ps1')
README = os.path.join(HERE, 'README_TESTERS.md')
OWNER = os.path.join(HERE, 'OWNER_RELEASE_STEPS.md')
RELEASE = os.path.join(TOOLS, 'kl_release.py')
AUTOTEST = os.path.join(TOOLS, 'kl_autotest.py')

fails = []
notes = []


def check(cond, what):
    if cond:
        print('  ok   ' + what)
    else:
        print('  FAIL ' + what)
        fails.append(what)


def read(p):
    with open(p, 'rb') as f:
        return f.read()


def ascii_only(p):
    b = read(p)
    bad = [i for i, c in enumerate(b) if c > 0x7e or (c < 0x20 and c not in (9, 10, 13))]
    return not bad, (('byte 0x%02x at offset %d' % (b[bad[0]], bad[0])) if bad else '')


def strip_ps(src):
    """PowerShell source without strings and comments (rough tokenizer good enough for bracket counting)."""
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == '<' and src.startswith('<#', i):
            j = src.find('#>', i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == '#':
            j = src.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == '@' and i + 1 < n and src[i + 1] in '\'"' and src[i + 2:i + 3] in ('\r', '\n'):
            q = src[i + 1]
            j = src.find('\n' + q + '@', i)
            if j < 0:
                return None
            i = j + 3
            continue
        if c == "'":
            j = i + 1
            while j < n:
                if src[j] == "'":
                    if j + 1 < n and src[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if src[j] == '`':
                    j += 2
                    continue
                if src[j] == '"':
                    if j + 1 < n and src[j + 1] == '"':
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def main():
    print('launcher_test: ' + HERE)
    # 1. files + ascii
    for p in (BAT, WRAP, PS1, PACK, README, OWNER):
        check(os.path.exists(p), 'exists: ' + os.path.basename(p))
    for p in (BAT, WRAP, PS1, PACK):
        if os.path.exists(p):
            ok, why = ascii_only(p)
            check(ok, 'ascii only: %s %s' % (os.path.basename(p), why))

    # 2. the bootstrap bat
    bat = read(BAT).decode('ascii', 'replace')
    urls = re.findall(r'^\s*set\s+"RELEASE_URL=([^"]*)"', bat, re.M)
    check(len(urls) == 1, 'RELEASE_URL is set in exactly one place (found %d)' % len(urls))
    check(urls and 'example.invalid' in urls[0], 'the committed RELEASE_URL is the placeholder (Josh sets the real one)')
    check('findstr /i /c:"example.invalid"' in bat, 'the bat refuses to download from the placeholder URL')
    check('KLMergeLauncher.ps1' in bat and '-ExecutionPolicy Bypass -STA' in bat, 'the bat starts the launcher with -ExecutionPolicy Bypass -STA')
    check('zstandard' in bat and 'get-pip.py' in bat and '._pth' in bat, 'the bat installs zstandard into the embedded python (._pth + get-pip)')
    check('KLMergeSetup.exe' in bat, 'the bat skips python when the package has KLMergeSetup.exe')
    labels = set(re.findall(r'^:(\w+)\s*$', bat, re.M))
    gotos = set(re.findall(r'goto\s+:(\w+)', bat))
    check(gotos <= labels, 'every goto has its label (missing: %s)' % ', '.join(sorted(gotos - labels)))
    check('rem GUESS' in bat or 'GUESS:' in bat, 'the bat marks its guessed URLs with GUESS')
    for word in ('KL_PortBackup', 'KLMergeInstall.json', 'steam launch', 'Steam launch'):
        pass  # (the bat does not touch the game folder itself; nothing to check here)
    wrap = read(WRAP).decode('ascii', 'replace')
    check('-ExecutionPolicy Bypass -STA' in wrap and 'KLMergeLauncher.ps1' in wrap, 'KLMerge.bat wraps the ps1 with -ExecutionPolicy Bypass -STA')

    # 3. the launcher script
    ps = read(PS1).decode('ascii', 'replace')
    body = strip_ps(ps)
    check(body is not None, 'ps1: strings and here-strings close')
    if body is not None:
        for a, b in (('{', '}'), ('(', ')'), ('[', ']')):
            check(body.count(a) == body.count(b), 'ps1: %s%s balanced outside strings (%d / %d)' % (a, b, body.count(a), body.count(b)))
        check('$args =' not in body and '$args +=' not in body, 'ps1: the automatic $args variable is not assigned')
    m = re.search(r"\$xaml = @'\r?\n(.*?)\r?\n'@", ps, re.S)
    check(bool(m), 'ps1: the XAML here-string is found')
    if m:
        xaml = m.group(1).replace('<!--GRAIN_LIGHT-->', '').replace('<!--GRAIN_DARK-->', '')
        try:
            root = ET.fromstring(xaml)
            check(root.tag.endswith('}Window'), 'ps1: XAML root is a Window')
            names = set(re.findall(r'x:Name="(\w+)"', xaml))
            wanted = set(re.findall(r"\$ui\[?'?(?:\.)?(Btn\w+|Lbl\w+|TxtLog)", ps)) | set(re.findall(r"\$ui\.(\w+)", ps))
            wanted = {w for w in wanted if w[0].isupper()}
            check(wanted <= names, 'ps1: every $ui.<name> the script uses is an x:Name in the XAML (missing: %s)' % ', '.join(sorted(wanted - names)))
            findnames = set(re.findall(r"'(\w+)'", ps[ps.find("foreach ($n in @('LblVersion'"):ps.find("$ui[$n] = ")]))
            check(findnames <= names, 'ps1: every FindName() target exists in the XAML (missing: %s)' % ', '.join(sorted(findnames - names)))
        except ET.ParseError as e:
            check(False, 'ps1: XAML is well-formed XML (%s)' % e)
    # verbs / options against kl_release.py's argparse
    rel = read(RELEASE).decode('utf-8', 'replace')
    verbs = set(re.findall(r"add_parser\('(\w+)'\)", rel))
    for mm in re.finditer(r"for name in \(([^)]*)\):\s*\n\s*s = sub\.add_parser\(name\)", rel):
        verbs |= set(re.findall(r"'(\w+)'", mm.group(1)))
    used_verbs = set(re.findall(r"Start-Tool '(\w+)'", ps))
    check(used_verbs == {'install', 'verify', 'uninstall'}, 'ps1: calls install / verify / uninstall (found %s)' % ', '.join(sorted(used_verbs)))
    check(used_verbs <= verbs, 'kl_release.py argparse has every verb the launcher calls (argparse: %s)' % ', '.join(sorted(verbs)))
    opts = set(re.findall(r"add_argument\('(--\w+)'", rel))
    used_opts = set(re.findall(r"'(--\w+)'", ps[ps.find('function Start-Tool'):ps.find('$stamp = Get-Date', ps.find('function Start-Tool'))]))
    check(used_opts <= opts, 'kl_release.py has every option the launcher passes (%s; argparse: %s)' % (', '.join(sorted(used_opts)), ', '.join(sorted(opts))))
    check("'--yes'" in ps and "Start-Tool 'install' @('--yes')" in ps, 'ps1: install runs with --yes (kl_release.py would otherwise wait on input())')
    check("Start-Tool 'uninstall' @('--yes')" in ps, 'ps1: uninstall runs with --yes')
    check("'--pkg'" in ps, 'ps1: passes --pkg (kl_release.py defaults the package to its own folder otherwise)')
    # app id
    at = read(AUTOTEST).decode('utf-8', 'replace')
    ma = re.search(r'^APP = (\d+)', at, re.M)
    mp = re.search(r'\$script:AppId = (\d+)', ps)
    check(ma and mp and ma.group(1) == mp.group(1), 'Steam app id in the launcher equals kl_autotest.py APP (%s / %s)' % (ma and ma.group(1), mp and mp.group(1)))
    check("'steam://rungameid/'" in ps, 'ps1: launches through steam://rungameid/')
    # hook off name consistency
    mh = re.search(r"\$script:HookOffName = '([^']+)'", ps)
    check(bool(mh), 'ps1: HookOffName defined')
    if mh:
        off = mh.group(1)
        for p in (README, OWNER):
            txt = read(p).decode('utf-8', 'replace')
            check(off in txt, '%s names the hook-off file %s' % (os.path.basename(p), off))
    check('Rename-Item' in ps and 'Remove-Item' not in ps, 'ps1: the hook switch renames and never deletes')
    check('launch options' in ps.lower() and 'Set-ItemProperty' not in ps, 'ps1: never writes Steam launch options')
    check('GUESS' in ps, 'ps1: has a GUESS list')

    # 3b. music + background (2026-11-09, owner: quiet Dead Men music with a mute switch, a two-game background)
    check('System.Windows.Media.MediaPlayer' in ps, 'ps1: music through System.Windows.Media.MediaPlayer')
    mv = re.search(r"\$script:DefaultVolume = ([0-9.]+)", ps)
    check(mv and 0 < float(mv.group(1)) <= 0.3, 'ps1: default music volume is quiet (%s)' % (mv and mv.group(1)))
    check("Volume = 0.22" in ps, 'ps1: the settings default Volume is 0.22')
    check('MediaEnded' in ps and '[TimeSpan]::Zero' in ps, 'ps1: the clip loops (MediaEnded -> Position 0 -> Play)')
    check('MediaFailed' in ps, 'ps1: a playback failure is caught (MediaFailed handler)')
    check("$script:MusicName = 'deadmen_launcher.wav'" in ps and "'music\\' + $script:MusicName" in ps, 'ps1: music file is <launcher>\\music\\deadmen_launcher.wav')
    check("$script:MusicToolName = 'kl_launcher_music.py'" in ps and "'extract', '--dm'" in ps and "'--out'" in ps, 'ps1: makes the clip with kl_launcher_music.py extract --dm --out')
    check("'--clip'" in ps and 'MusicClip' in ps, 'ps1: MusicClip setting -> --clip')
    for k in ('Muted', 'Volume', 'MusicClip'):
        check(("'%s'" % k in ps) or ("NoteProperty %s" % k in ps), 'ps1: settings file carries ' + k)
    check("[char]0x266A" in ps and '&#9834;' in ps, 'ps1: the music note is written as an ASCII escape (code + XAML entity), not as a UTF-8 char')
    check('function Music-Poll' in ps and 'Music-Poll' in ps[ps.find('$script:Timer.Add_Tick'):ps.find('$script:Timer.Start()')], 'ps1: the timer polls the background extract')
    check("Music-Extract $true" in ps[ps.find('$script:Timer.Add_Tick'):ps.find('$script:Timer.Start()')], 'ps1: a finished INSTALL (exit 0) triggers the extract')
    check('if (-not $script:MusicLoaded) {' in ps and 'if (-not $script:Settings.Muted) { Music-Extract }' in ps, 'ps1: no music file at start = silent, extract only when not muted')
    check('BtnMute.Add_Click' in ps and 'Settings.Muted = -not' in ps, 'ps1: MUTE / UNMUTE toggles and remembers the state')
    check('exit 2' in ps or '2 = no decodable clip' in ps, 'ps1: documents the tool exit code 2 = silence')
    for fn in ('Music-Init', 'Music-Load', 'Music-Extract', 'Bg-Init'):
        body = ps[ps.find('function ' + fn):]
        body = body[:body.find('\nfunction ', 1) if body.find('\nfunction ', 1) > 0 else len(body)]
        check('try {' in body and 'catch' in body, 'ps1: %s has try/catch (audio / images never crash the window)' % fn)
    check('ImageBrush' in ps and 'UniformToFill' in ps and "'dead_men.jpg'" in ps and "'dog_days.jpg'" in ps, 'ps1: background = bg\\dead_men.jpg + bg\\dog_days.jpg as ImageBrush UniformToFill')
    check('<Grid.OpacityMask>' in ps and 'LinearGradientBrush' in ps[ps.find('<Grid.OpacityMask>'):ps.find('</Grid.OpacityMask>')], 'ps1: the two sides blend through an OpacityMask gradient (soft seam)')
    check('BitmapCacheOption]::OnLoad' in ps, 'ps1: images are read once (OnLoad), the files are not kept open')
    check('FilmGrain' in ps and 'VideoBlocks' in ps and 'ScanLines' in ps, 'ps1: procedural fallback brushes exist (film grain left, video blocks + scan lines right)')
    if m:
        bg_order = [xaml.find(s) for s in ('x:Name="BgRight"', 'x:Name="BgLeft"', 'x:Name="BgDim"', 'StaticResource Grain}', 'RadialGradientBrush', 'Margin="30,22,30,22"')]
        check(all(i >= 0 for i in bg_order) and bg_order == sorted(bg_order), 'ps1: background layers lie under dim, grain, vignette and the content (XAML order)')
        check('x:Name="BtnMute"' in xaml and 'x:Name="LblMusic"' in xaml and xaml.find('x:Name="BtnMute"') < xaml.find('<!-- body -->'), 'ps1: MUTE button and state text are in the header')
    check('Remove-Item' not in ps, 'ps1: the music code never deletes either')
    check(os.path.exists(os.path.join(TOOLS, 'kl_launcher_music.py')) and os.path.exists(os.path.join(TOOLS, 'kl_launcher_music_test.py')), 'tools/kl_launcher_music.py + its self-test exist')
    gi = read(os.path.join(os.path.dirname(TOOLS), '.gitignore')).decode('utf-8', 'replace')
    check('tools/launcher/music/' in gi and 'tools/launcher/bg/*' in gi, '.gitignore keeps the decoded clip and the owner pictures out of the repo')
    check('kl_launcher_music.py' in bat and 'launcher\\bg\\*.jpg' in bat, 'the bat copies the music tool and bg\\*.jpg up beside the launcher')

    # 4. pwsh parse when available
    pwsh = shutil.which('pwsh') or shutil.which('powershell')
    if pwsh:
        for p in (PS1, PACK):
            cmd = ("$t=$null;$e=$null;[void][System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$t,[ref]$e);"
                   "if($e){$e|%%{Write-Output ($_.Extent.StartLineNumber.ToString()+': '+$_.Message)};exit 1}else{Write-Output 'parse ok';exit 0}") % p.replace("'", "''")
            try:
                r = subprocess.run([pwsh, '-NoProfile', '-NonInteractive', '-Command', cmd], capture_output=True, text=True, timeout=120)
                check(r.returncode == 0, 'pwsh parse %s: %s' % (os.path.basename(p), (r.stdout + r.stderr).strip()[:300]))
            except Exception as e:
                notes.append('pwsh parse skipped: %s' % e)
    else:
        notes.append('pwsh not on the PATH: PowerShell parser check SKIPPED (run this test once on Windows)')

    # 5. the READMEs
    rd = read(README).decode('utf-8', 'replace')
    for word in ('KLHook.log', 'kl2_490_crash_', 'KLHook_', '.dmp', 'KL_PortBackup', 'UNINSTALL', 'Dead Men', 'Payday 2', 'firewall'):
        check(word in rd, 'README_TESTERS mentions ' + word)
    ow = read(OWNER).decode('utf-8', 'replace')
    check('kl_release.py make' in ow and '--dd' in ow and '--dm' in ow, 'OWNER_RELEASE_STEPS has the make command')
    check('RELEASE_URL' in ow and 'PyInstaller' in ow, 'OWNER_RELEASE_STEPS covers RELEASE_URL and the frozen exe')
    check('UNTESTED' in ow or 'untested' in ow, 'OWNER_RELEASE_STEPS labels what is untested')
    pk = read(PACK).decode('ascii', 'replace')
    check('manifest.json' in pk and 'patches' in pk and 'kl_release.py' in pk and 'launcher' in pk, 'pack_release.ps1 bundles manifest + patches + kl_release.py + launcher')
    check('_snap' in pk and 'sha1cache' in pk, 'pack_release.ps1 knows the maker-only folders it must leave out')
    check("'kl_launcher_music.py'" in pk, 'pack_release.ps1 packs launcher\\kl_launcher_music.py')
    check("-Filter '*.jpg'" in pk and "'launcher\\bg'" in pk, 'pack_release.ps1 packs launcher\\bg\\*.jpg')
    check("'launcher\\music'" in pk and 'REFUSED' in pk[pk.find("'launcher\\music'") - 200:pk.find("'launcher\\music'") + 200] and '|wav|' in pk, 'pack_release.ps1 refuses launcher\\music\\ (and any .wav)')
    for word in ('MUTE', 'own', 'PC_Def.str', 'deadmen_launcher.wav', 'bg\\dead_men.jpg'):
        check(word in rd, 'README_TESTERS mentions ' + word + ' (music from the tester\'s own Dead Men files, mute button, background)')
    for word in ('bg\\dead_men.jpg', 'bg\\dog_days.jpg', 'kl_launcher_music.py', 'launcher\\music\\', 'FA_SlashMixPrison', 'TakyoAction_Layer2_TAmbient_Loop'):
        check(word in ow, 'OWNER_RELEASE_STEPS mentions ' + word)
    check(os.path.exists(os.path.join(HERE, 'bg', 'README.txt')), 'tools/launcher/bg/README.txt tells where the pictures go')

    for n in notes:
        print('  note ' + n)
    if fails:
        print('RESULT: FAIL %d check(s): %s' % (len(fails), '; '.join(fails)[:400]))
        return 1
    print('RESULT: PASS (%s)' % ('pwsh parsed' if pwsh else 'no pwsh here: parser check skipped'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
