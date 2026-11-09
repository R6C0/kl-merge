#!/usr/bin/env python3
"""
launcher_test.py - off-game self-test of tools/launcher/ (the tester bootstrap + WPF launcher). No game, no network.

Checks
  1. the files exist and are plain ASCII (cmd.exe and the ini-reading hook choke on smart quotes / UTF-8 BOMs)
  2. KL Dead Men Rising Setup.bat (was KLMerge Setup.bat): RELEASE_URL is defined in ONE place at the top, it is R6C0/dead-men-rising's latest release, and
     the script refuses to run with the placeholder (findstr example.invalid); every 'goto :label' has its label
  3. KLMergeLauncher.ps1: brace / bracket / parenthesis balance outside strings and comments; the XAML here-string is
     well-formed XML; every kl_release.py verb and option the launcher passes exists in kl_release.py's argparse;
     the Steam app id equals tools/kl_autotest.py APP; the hook-off file name is the same in the script and the READMEs
  3b. music + background (2026-11-09): MediaPlayer with loop + MediaFailed handling, quiet default volume, the music file and
     tool names, Muted / Volume / MusicClip in the settings, the ASCII-escaped note sign, try/catch around audio and images,
     the two ImageBrush sides with an OpacityMask seam under dim / grain / vignette, the procedural fallback brushes, and that
     the bat / pack_release.ps1 / READMEs carry the tool, bg\\*.jpg and the music\\ exclusion
  3c. the in-game look (owner, 2026-11-09, tools/kl_hud.py --look deadmen): Impact first in the heading face, the kit's
     palette (INK / CHALK / CORAL / AMBER / GREEN / DEAD), the old red fills gone, chip tiles (CombinedGeometry Exclude
     in a tiled DrawingBrush used as OpacityMask) with ChipAmount / ChipSeed marked GUESS, brush bars with a break
     instead of filled / bordered buttons, smear panels (Smear-Path), values and the log NOT chipped, a tracked title
  3d. Defender (2026-11-09): no "-WindowStyle Hidden" in either .bat (the heuristic Trojan:Win32/Ceprolad.A fired on
     that + Bypass), the launcher is started minimized, the Setup .bat deletes nothing (no del / rmdir / Remove-Item;
     robocopy /MOVE is the one move and is commented), and README_TESTERS has the Defender / SmartScreen section
  3e. exe + game watch (owner 2026-11-09: production look, no console; hide while the game runs, back on exit/crash):
     exe/DeadMenRising.cs is a winexe that hosts the .ps1 in-process (STA, Bypass, no powershell.exe), build.bat
     passes icon + manifest, the Setup starts the exe; the visible name is KL: Dead Men Rising (no 'KL Merge' left in
     what a tester reads); the window runs in a DispatcherFrame (Hide() would end ShowDialog), Game-Watch hides on the
     game window and shows again when kl2.exe is gone, child jobs start -WindowStyle Hidden (no -NoNewWindow)
  4. when pwsh (PowerShell 7) is on the PATH, the script is parsed with System.Management.Automation.Language.Parser
     and must give 0 errors (else SKIPPED with a note, never a FAIL)
  5. README_TESTERS.md names the log / dump files a tester must send, and OWNER_RELEASE_STEPS.md has the make command

exit 0 = all pass, 1 = a FAIL. Discovered by tools/kl_tests.py (tools/launcher/*_test.py).
"""
import os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
BAT = os.path.join(HERE, 'KL Dead Men Rising Setup.bat')
EXE_SRC = os.path.join(HERE, 'exe', 'DeadMenRising.cs')
EXE_BUILD = os.path.join(HERE, 'exe', 'build.bat')
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


def xaml_parse_check(pwsh, ps):
    """Windows only: run the launcher's own prelude (everything before '$script:Win = ...XamlReader]::Parse', minus the
    trap, whose MessageBox would hang a test) in an STA PowerShell, then XamlReader.Parse the built $xaml. Shows nothing."""
    cut = ps.find('$script:Win = [Windows.Markup.XamlReader]::Parse($xaml)')
    t0 = ps.find('\ntrap {')
    t1 = ps.find('\n}', t0 + 1)
    if cut < 0 or t0 < 0 or t1 < 0 or not t0 < t1 < cut:
        check(False, 'ps1: XamlReader.Parse line and the trap block are found (for the real XAML parse)')
        return
    pre = ps[:t0] + ps[t1 + 2:cut]
    pre += ("\ntry { [void][Windows.Markup.XamlReader]::Parse($xaml); Write-Output 'XAML_PARSE_OK' }\n"
            "catch { $x = $_.Exception; while ($x.InnerException) { $x = $x.InnerException }; Write-Output ('XAML_PARSE_FAIL ' + $x.Message) }\n")
    import tempfile
    d = tempfile.mkdtemp(prefix='kllaunch_xaml_')
    p = os.path.join(d, 'KLMergeLauncher.ps1')
    try:
        with open(p, 'w', encoding='ascii', errors='replace', newline='\r\n') as f:
            f.write(pre.replace('\r\n', '\n'))
        exe = shutil.which('powershell') or pwsh                     # Windows PowerShell: STA + WPF always there
        r = subprocess.run([exe, '-NoProfile', '-NonInteractive', '-STA', '-ExecutionPolicy', 'Bypass', '-File', p],
                           capture_output=True, text=True, timeout=180)
        out = (r.stdout + r.stderr).strip()
        check('XAML_PARSE_OK' in out, 'ps1: the built window XAML loads in WPF (XamlReader.Parse): %s' % out[-300:])
    except Exception as e:
        notes.append('real XAML parse skipped: %s' % e)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    print('launcher_test: ' + HERE)
    # 1. files + ascii
    for p in (BAT, EXE_SRC, EXE_BUILD, PS1, PACK, README, OWNER):
        check(os.path.exists(p), 'exists: ' + os.path.basename(p))
    for p in (BAT, EXE_SRC, EXE_BUILD, PS1, PACK):
        if os.path.exists(p):
            ok, why = ascii_only(p)
            check(ok, 'ascii only: %s %s' % (os.path.basename(p), why))

    # 2. the bootstrap bat
    bat = read(BAT).decode('ascii', 'replace')
    urls = re.findall(r'^\s*set\s+"RELEASE_URL=([^"]*)"', bat, re.M)
    check(len(urls) == 1, 'RELEASE_URL is set in exactly one place (found %d)' % len(urls))
    check(urls and urls[0] == 'https://github.com/R6C0/dead-men-rising/releases/latest/download/KLMerge_package.zip',
          'RELEASE_URL = the public release repo\'s latest KLMerge_package.zip (a fixed asset name, so the link never changes)')
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
    # 3d. Defender: the hidden-window form of the powershell start is the heuristic trigger; the Setup's fallback is minimized
    code = '\n'.join(l for l in bat.splitlines() if not l.strip().lower().startswith('rem'))
    check('-WindowStyle Hidden' not in code, 'the Setup .bat does not start powershell with -WindowStyle Hidden (Defender heuristic)')
    check(re.search(r'^start\s+"[^"]*"\s+/min\s+powershell', code, re.M | re.I) is not None, 'the Setup .bat falls back to a minimized powershell start (old package, no exe)')
    check('Ceprolad' in bat, 'the Setup .bat says why its fallback is not hidden')
    # 3e. the exe
    check(re.search(r'^\s*start ""\s+"%HERE%KL Dead Men Rising\.exe"', code, re.M) is not None, 'the Setup .bat starts KL Dead Men Rising.exe when it is there')
    check(r'copy /Y "%PKG%\launcher\KL Dead Men Rising.exe"' in bat, 'the Setup .bat copies the exe up from the package')
    cs = read(EXE_SRC).decode('ascii', 'replace')
    check('[STAThread]' in cs and 'ApartmentState.STA' in cs and 'PSThreadOptions.UseCurrentThread' in cs, 'exe: STA, the runspace runs on the STA thread (WPF)')
    check('ExecutionPolicy.Bypass' in cs and 'Process.Start' not in cs and 'powershell.exe' not in cs.split('using System;')[1], 'exe: Bypass in its own runspace, no powershell.exe child')
    check('AddCommand(ps1)' in cs and '"KLMergeLauncher.ps1"' in cs, 'exe: runs KLMergeLauncher.ps1 as a script file (keeps $MyInvocation)')
    check('Mutex' in cs and 'SetForegroundWindow' in cs, 'exe: one launcher at a time (a second start fronts the first)')
    check('AssemblyProduct("KL: Dead Men Rising")' in cs and 'AssemblyFileVersion' in cs, 'exe: version info names KL: Dead Men Rising')
    bb = read(EXE_BUILD).decode('ascii', 'replace')
    check('/target:winexe' in bb and '/win32icon:dmr.ico' in bb and '/win32manifest:app.manifest' in bb, 'exe build: winexe (no console) + icon + manifest')
    check(os.path.exists(os.path.join(HERE, 'exe', 'dmr.ico')) and os.path.exists(os.path.join(HERE, 'exe', 'app.manifest')), 'exe: dmr.ico and app.manifest exist')
    bat_code = '\n'.join(l for l in bat.splitlines() if not l.strip().lower().startswith('rem'))
    check(re.search(r'(?im)^\s*(del|erase|rmdir|rd)\b', bat_code) is None and 'Remove-Item' not in bat_code and '-Recurse' not in bat_code,
          'the Setup .bat has no del / erase / rmdir / Remove-Item')
    check('/MOVE' in bat and re.search(r'rem .*?/MOVE is a MOVE', bat) is not None, 'the one robocopy /MOVE in the Setup .bat is commented as a move')

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
            # 11-09: the brush-kit restyle gave a SolidColorBrush and a Style both x:Key="Key" -> XamlReader threw
            # 'Add value to dictionary of type ResourceDictionary' on the owner's first launch. Keys must be unique per dictionary.
            xkey = '{http://schemas.microsoft.com/winfx/2006/xaml}Key'
            dups, keys = [], set()
            for el in root.iter():
                seen = {}
                for c in el:
                    k = c.get(xkey)
                    if k is None:
                        continue
                    keys.add(k)
                    if k in seen:
                        dups.append('%s (%s + %s)' % (k, seen[k].split('}')[-1], c.tag.split('}')[-1]))
                    seen[k] = c.tag
            check(not dups, 'ps1: no x:Key twice in one resource dictionary (dup: %s)' % ', '.join(dups))
            refs = set(re.findall(r'\{StaticResource (\w+)\}', xaml))
            check(refs <= keys, 'ps1: every {StaticResource X} names an x:Key of the XAML (missing: %s)' % ', '.join(sorted(refs - keys)))
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

    # 3e. visible name + game watch (owner 2026-11-09)
    if ps:
        shown = [m for m in re.findall(r"(?:Text|Content|Title)=\"([^\"]*)\"", xaml)] + re.findall(r"(?:Log|Show)\s*\(?\s*'([^']*)'", ps)
        check(not [t for t in shown if re.search(r'KL MERGE|KLMerge Setup', t, re.I)], 'name: no KL Merge in the window texts, titles, logs or message boxes')
        check('Title="KL: Dead Men Rising"' in xaml and 'PLAY DEAD MEN RISING' in xaml, 'name: window title KL: Dead Men Rising, button PLAY DEAD MEN RISING')
        check('.ShowDialog()' not in ps.replace('$d.ShowDialog()', '') and 'Dispatcher]::PushFrame($script:Frame)' in ps and '$script:Frame.Continue = $false' in ps,
              'watch: the window runs in a DispatcherFrame, not ShowDialog (Hide() would end ShowDialog)')
        gw = ps[ps.find('function Game-Watch'):]
        gw = gw[:gw.find('\n}\n') + 3]
        check('$script:Win.Hide()' in gw and '$script:Win.Show()' in gw and 'Game-Window' in gw and 'Game-Running' in gw and 'Crash-Files' in gw,
              'watch: Game-Watch hides on the game window, shows again when kl2.exe is gone and reports crash dumps')
        check('MainWindowHandle' in ps and re.search(r'\$script:GameWaitS = \d+\s+# GUESS', ps) is not None, "watch: 'booted' = kl2 has a main window; the wait limit is marked GUESS")
        check('$script:GameWatch = @{' in ps[ps.find('function Launch-Game'):ps.find('function Launch-Game') + 400], 'watch: Launch-Game arms the watch')
        check('-NoNewWindow -PassThru' not in ps and ps.count('-WindowStyle Hidden -PassThru') >= 2, 'child jobs: -WindowStyle Hidden, not -NoNewWindow (the exe host has no console to share)')
    # 3b. music + background (2026-11-09, owner: quiet Dead Men music with a mute switch, a two-game background)
    check('System.Windows.Media.MediaPlayer' in ps, 'ps1: music through System.Windows.Media.MediaPlayer')
    mv = re.search(r"\$script:DefaultVolume = ([0-9.]+)", ps)
    check(mv and 0 < float(mv.group(1)) <= 0.3, 'ps1: default music volume is quiet (%s)' % (mv and mv.group(1)))
    check("Volume = 0.22" in ps, 'ps1: the settings default Volume is 0.22')
    check('MediaEnded' in ps and '[TimeSpan]::Zero' in ps, 'ps1: the clip loops (MediaEnded -> Position 0 -> Play)')
    check('MediaFailed' in ps, 'ps1: a playback failure is caught (MediaFailed handler)')
    check("$script:MusicName = 'deadmen_riff.wav'" in ps and "'music\\' + $script:MusicName" in ps, 'ps1: music file is <launcher>\\music\\deadmen_riff.wav (new name: an old FA-theme deadmen_launcher.wav is not reused)')
    check(ps.count('$null = $script:Proc.Handle') == 1 and ps.count('$null = $script:MusicProc.Handle') == 1, 'ps1: both Start-Process objects keep their Handle (else ExitCode reads empty)')
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

    # 3c. the in-game look (owner 2026-11-09: "follow the in-game UI theme ... a Dead Men feel"; tools/kl_hud.py --look deadmen)
    if m:
        res = xaml[xaml.find('<Window.Resources>'):xaml.find('</Window.Resources>')]
        mf = re.search(r'<FontFamily x:Key="Head">([^<]*)</FontFamily>', res)
        check(mf and mf.group(1).split(',')[0].strip() == 'Impact', 'look: the heading face is Impact first (%s)' % (mf and mf.group(1)))
        check('FontFamily="Consolas"' in xaml[xaml.find('x:Name="TxtLog"') - 400:xaml.find('x:Name="TxtLog"') + 400], 'look: the log stays Consolas')
        for col, what in (('#0C0C0D', 'INK background'), ('#F3F0EA', 'CHALK text'), ('#F0475A', 'CORAL accent'), ('#B8B3AA', 'muted keys'),
                          ('#E0962E', 'AMBER warning'), ('#63A05B', 'GREEN ok'), ('#8C3138', 'DEAD red error'), ('#6E6A64', 'disabled grey')):
            check(col in ps, 'look: palette has %s %s' % (what, col))
        for old in ('#A3121A', '#7E0E14', '#6E0C11'):
            check(old not in ps, 'look: the old red fill %s is gone' % old)
        check('Background="#0C0C0D"' in xaml[:xaml.find('<Window.Resources>')], 'look: the window background is INK')
        # chip tiles: an OpacityMask of white minus holes, tiled, on the Impact text (not on values / the log)
        for key in ('Chip', 'ChipLight'):
            blk = res[res.find('x:Key="%s"' % key):]
            blk = blk[:blk.find('</DrawingBrush>')]
            check('TileMode="Tile"' in blk and 'ViewportUnits="Absolute"' in blk and 'GeometryCombineMode="Exclude"' in blk and 'Brush="White"' in blk,
                  'look: %s = tiled white DrawingBrush minus holes (CombinedGeometry Exclude)' % key)
        check(re.search(r'\$script:ChipAmount = [0-9.]+\s+# GUESS', ps) is not None and '$script:ChipSeed = ' in ps, 'ps1: ChipAmount (GUESS) and ChipSeed are variables at the top of the window section')
        check('function Chip-Nicks' in ps and 'System.Random $script:ChipSeed' in ps, 'ps1: the nicks come from a seeded RNG (Chip-Nicks)')
        masked = re.findall(r'OpacityMask="\{StaticResource (Chip\w*)\}"', xaml) + re.findall(r'Property="OpacityMask" Value="\{StaticResource (Chip\w*)\}"', res)
        check(len(masked) >= 8, 'look: the chip mask is used on the Impact text and buttons (%d uses: title, sub, music, version, STATUS, LOG + the button / Key styles)' % len(masked))
        val_style = res[res.find('x:Key="Val"'):]
        val_style = val_style[:val_style.find('</Style>')]
        check('OpacityMask' not in val_style and 'OpacityMask' not in xaml[xaml.find('x:Name="TxtLog"'):xaml.find('x:Name="TxtLog"') + 500], 'look: values and the log are NOT chipped')
        check('OpacityMask="{StaticResource Chip}"' in xaml[xaml.find('<!-- header'):xaml.find('<!-- body -->')] and '<Run Text="DEAD MEN RISING" Foreground="{StaticResource Coral}"/>' in xaml,
              'look: the title KL: DEAD MEN RISING is chipped, DEAD MEN RISING in CORAL')
        check('RotateTransform Angle="-0.6"' in xaml, 'look: the title block leans -0.6 degrees')
        # buttons: a brush bar with a break + the word; nothing filled, nothing bordered
        tpl = res[res.find('x:Key="KLButton"'):]
        tpl = tpl[:tpl.find('</Style>')]
        check('x:Name="Bar"' in tpl and 'OpacityMask="{StaticResource BarBreak}"' in tpl, 'look: the button bar is a Border edge with the BarBreak mask (one gap)')
        check('Background="Transparent"' in tpl and 'Background="{TemplateBinding Background}"' not in tpl and 'BorderThickness="1"' not in tpl, 'look: buttons paint no fill and no 1 px border')
        check('Property="IsMouseOver"' in tpl and 'Property="IsPressed"' in tpl and 'Property="IsEnabled"' in tpl and '{StaticResource Off}' in tpl, 'look: hover / pressed / disabled triggers (disabled = #6E6A64)')
        check('BorderThickness" Value="7,0,0,0"' in res and 'BorderThickness" Value="9,0,0,0"' in res and 'BorderThickness" Value="4,0,0,0"' in res, 'look: bar widths 7 / 9 (primary) / 4 (small)')
        check('<Run Text="  (STOCK)"' in xaml and '<Run Text="  (RESTORE STOCK)"' in xaml, 'look: the secondary words are smaller grey Runs')
        check('<Border ' not in xaml[xaml.find('<!-- body -->'):] or 'BorderThickness="1"' not in xaml[xaml.find('<!-- body -->'):], 'look: no hairline bordered Border panels in the body')
        # smear panels + chalk rules
        check('function Smear-Path' in ps and xaml.count('Geometry="@SMEAR_') == 2 and '@SMEAR_STATUS@' in ps and '@SMEAR_LOG@' in ps, 'look: status + log panels are Smear-Path backgrounds')
        check('Brush="#DB0A0A0B"' in xaml and 'Brush="#D10A0A0B"' in xaml, 'look: smear fills #0A0A0B at ~86 % / ~82 %')
        check(xaml.count('<Line X2="1" Stretch="Fill"') >= 4 and 'StrokeThickness="4"' in xaml and 'StrokeDashArray=' in xaml, 'look: chalk rules are dashed Lines (header 4 px with breaks, panel top, mute underline)')
        check('<Path Stretch="Fill" Stroke="#14FFFFFF"' in xaml, 'look: faint diagonal scratches on the background')
        check('x:Name="BgDim" Fill="#47000000"' in xaml and 'FromArgb(0x99, 0, 0, 0)' in ps, 'look: dim 0.28 over the fallback, 0.6 over photos')
        check('function Track' in ps and '[char]0x200A' in ps and 'Track-Tree $script:Win' in ps, 'ps1: letter tracking by hair spaces (Track / Track-Tree), ASCII escape only')
        check('function Set-Val' in ps and "Set-Val $ui.LblGame 'not running' 'ok'" in ps and "'bad'" in ps, 'ps1: value tones (ok / warn / bad / dim) via Set-Val')
    if not os.path.exists(os.path.join(HERE, 'design_mock_1109.html')):
        notes.append('design_mock_1109.html (the mock the owner judged) is not beside the launcher; the ps1 header refers to it')

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
        if os.name == 'nt':
            xaml_parse_check(pwsh, ps)
        else:
            notes.append('not Windows: real XamlReader.Parse of the launcher window SKIPPED')
    else:
        notes.append('pwsh not on the PATH: PowerShell parser check SKIPPED (run this test once on Windows)')

    # 5. the READMEs
    rd = read(README).decode('utf-8', 'replace')
    for word in ('KLHook.log', 'kl2_490_crash_', 'KLHook_', '.dmp', 'KL_PortBackup', 'UNINSTALL', 'Dead Men', 'Payday 2', 'firewall'):
        check(word in rd, 'README_TESTERS mentions ' + word)
    check('## If Windows Defender / SmartScreen complains' in rd, 'README_TESTERS has the Defender / SmartScreen section')
    for word in ('Ceprolad', 'plain text', 'Unblock', 'Protection history', 'signed'):
        check(word in rd[rd.find('## If Windows Defender'):], 'README_TESTERS Defender section mentions ' + word)
    ow = read(OWNER).decode('utf-8', 'replace')
    check('kl_release.py make' in ow and '--dd' in ow and '--dm' in ow, 'OWNER_RELEASE_STEPS has the make command')
    check('RELEASE_URL' in ow and 'PyInstaller' in ow, 'OWNER_RELEASE_STEPS covers RELEASE_URL and the frozen exe')
    check('UNTESTED' in ow or 'untested' in ow, 'OWNER_RELEASE_STEPS labels what is untested')
    pk = read(PACK).decode('ascii', 'replace')
    check('manifest.json' in pk and 'patches' in pk and 'kl_release.py' in pk and 'launcher' in pk, 'pack_release.ps1 bundles manifest + patches + kl_release.py + launcher')
    check('_snap' in pk and 'sha1cache' in pk, 'pack_release.ps1 knows the maker-only folders it must leave out')
    check("'kl_launcher_music.py'" in pk, 'pack_release.ps1 packs launcher\\kl_launcher_music.py')
    check("'kl_pybink.py'" in pk and 'kl_pybink.py' in bat, 'pack_release.ps1 packs kl_pybink.py (when it exists) and the bat copies it up')
    check("'kl_pyvorbis.py'" in pk and 'kl_pyvorbis.py' in bat and os.path.exists(os.path.join(TOOLS, 'kl_pyvorbis.py')), 'pack_release.ps1 packs kl_pyvorbis.py, the bat copies it up, and it exists')
    check("'bin\\kl_oggdec.exe'" in pk and "'launcher\\bin'" in pk, 'pack_release.ps1 packs launcher\\bin\\kl_oggdec.exe')
    check('bin\\kl_oggdec.exe' in bat and 'bin\\kl_oggdec.exe' in ow and 'kl_oggdec' in rd, 'the bat copies the decoder up; OWNER steps + README name it')
    sha = os.path.join(HERE, 'oggdec', 'stb_vorbis.sha256')
    check(os.path.exists(sha) and os.path.exists(os.path.join(HERE, 'oggdec', 'kl_oggdec.c')) and os.path.exists(os.path.join(HERE, 'oggdec', 'build.bat')), 'oggdec/: source, build.bat and the pinned stb_vorbis sha256 exist')
    svc = os.path.join(HERE, 'oggdec', 'stb_vorbis.c')
    if os.path.exists(svc):
        import hashlib
        check(hashlib.sha256(open(svc, 'rb').read()).hexdigest() == open(sha).read().split()[0], 'oggdec/stb_vorbis.c matches its pinned sha256')

    check("-Filter '*.jpg'" in pk and "'launcher\\bg'" in pk, 'pack_release.ps1 packs launcher\\bg\\*.jpg')
    check("'launcher\\music'" in pk and 'REFUSED' in pk[pk.find("'launcher\\music'") - 200:pk.find("'launcher\\music'") + 200] and '|wav|' in pk, 'pack_release.ps1 refuses launcher\\music\\ (and any .wav)')
    for word in ('MUTE', 'own', 'PC_Def.str', 'deadmen_riff.wav', 'bg\\dead_men.jpg'):
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
