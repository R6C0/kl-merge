# KLMergeLauncher.ps1 - the KL Merge launcher window (WPF, Windows PowerShell 5.1 or newer, no third-party parts).
#
# Start it through KLMerge.bat (which passes -ExecutionPolicy Bypass -STA). "KLMerge Setup.bat" fetches the release
# package first; this window never downloads anything.
#
# What it does
#   PLAY DOG DAYS     the stock game: the hook DLL is set aside (dinput8.dll -> dinput8.dll.klmerge-off, a RENAME, never a
#                     delete), then the game is started through Steam (steam://rungameid/28000) so the overlay and online
#                     play work as usual. The mod's other files stay on disk but nothing loads them without the hook
#                     (exception: the few replaced stock sound files and PC_Def.str of the package groups 'stockwav' /
#                     'pcdef', if the package has them - UNINSTALL puts those back byte for byte).
#   PLAY KL MERGE     the modded game: the hook DLL gets its name back (dinput8.dll.klmerge-off -> dinput8.dll), Steam starts
#                     the game. WHY A RENAME: klhook/klhook.c DllMain reads [KLHook] ContinueAsserts / MaxDumps / MaxAsserts /
#                     AssertSoft / EndOnFatal / FastExit / Stall* / ExitLog / Tick and nothing like a global Enable key, so the
#                     only clean 'off' is for kl2.exe not to find a dinput8.dll beside it (Windows then loads the system one).
#   INSTALL / UPDATE  python kl_release.py install <DD> --pkg <package> --yes [--dm <DM>] [--pd2 <PD2>]   (or KLMergeSetup.exe)
#   VERIFY            python kl_release.py verify  <DD> --pkg <package>
#   UNINSTALL         python kl_release.py uninstall <DD> --yes     (restores the stock files from <DD>\KL_PortBackup,
#                     journal <DD>\KLMergeInstall.json; the launcher asks first)
#   The hook is switched ON before each of the three so kl_release.py sees the real dinput8.dll (otherwise an install
#   would write a second copy and leave the .klmerge-off one behind).
#   COLLECT LOGS      zips <DD>\KLHook.log, KLHook_*.dmp, kl2_490_crash_*.mdmp, KLMergeInstall.json and this launcher's
#                     log into KLMerge_logs_<stamp>.zip beside the launcher - the file to send to Josh after a crash.
#   MUSIC             a Dead Men music clip plays quietly (System.Windows.Media.MediaPlayer, volume 0.22, looped) from
#                     <launcher folder>\music\deadmen_riff.wav. THAT FILE IS NEVER SHIPPED: the launcher makes it on the
#                     tester's PC from the tester's OWN Dead Men PC_Def.str ("python kl_launcher_music.py extract", run once
#                     when the Dead Men folder is known - at start, after INSTALL, or on UNMUTE). No Dead Men, no python, or
#                     a clip that cannot be decoded (exit 2) = silence, never an error. MUTE / UNMUTE in the header; the
#                     mute state and the volume are remembered in the settings file (Muted, Volume, MusicClip).
#                     The clip is Dead Men's MAIN MENU loop (SFX/UserInterface/MenuLoop_01, an Ogg Vorbis stream inside PC_Def.str, 77 s),
#                     decoded by <launcher folder>\bin\kl_oggdec.exe (public-domain stb_vorbis), else ffmpeg on the PATH.
#   BACKGROUND        <launcher folder>\bg\dead_men.jpg (left) and bg\dog_days.jpg (right), Josh's own screenshots (not in
#                     the repo), each ImageBrush UniformToFill, blended at a soft diagonal seam (OpacityMask), dimmed, under
#                     the grain and the vignette. Missing images = a procedural fallback: left a desaturated grey film-grain
#                     gradient (Dead Men's 2007 documentary grime), right a cooler dark teal with blocky 'compressed video'
#                     noise and scan lines (Dog Days' camcorder look). No art, logos or characters are drawn by this script.
#   LOOK (2026-11-09) the in-game Dead Men theme (tools/kl_hud.py --look deadmen; mock tools/launcher/design_mock_1109.html):
#                     Impact capitals with light chipping (a tiled OpacityMask of white minus a few 1-2 px holes, Chip-Nicks),
#                     buttons = a chalk brush bar with one break + the word (no fills, no borders), panels = a torn dark
#                     smear (a jittered polygon as the panel's Background brush, Smear-Path) with a broken chalk stroke on
#                     top, the kit's palette (INK / CHALK / CORAL / AMBER / GREEN / DEAD red). Values and the log stay plain.
#                     ChipAmount / ChipSeed at the top of the window section; letter tracking = hair spaces (Track).
#
# Where things are
#   package        <launcher folder>\package (manifest.json + patches\ + kl_release.py, optionally KLMergeSetup.exe),
#                  or the launcher folder itself when manifest.json lies there, or -Package <folder> / the settings file.
#   settings       KLMergeLauncher.settings.json beside this file: DD, DM, PD2, Python, Package, MusicClip, Muted, Volume
#                  (plain json, edit by hand if needed; MusicClip = a clip name for kl_launcher_music.py --clip, empty = its default list).
#   log            KLMergeLauncher.log beside this file (everything the log pane shows).
#   python         python_cmd.txt (written by Setup), .\python\python.exe (embedded), 'py -3', 'python' - first one that
#                  imports zstandard. Not needed when the package carries KLMergeSetup.exe (except for the music clip).
#   music tool     kl_launcher_music.py beside this file (Setup copies it up), or <package>\launcher\, or ..\ (the repo's tools\).
#   bg images      bg\ beside this file (Setup copies it up), or <package>\launcher\bg\.
#
# Steam launch options of the player are NEVER read or written. (Josh: your own options -o DefaultScene=... AutoExit=120
# are your test setup; with them this launcher would boot straight into F01 and quit after 120 s on YOUR PC only.)
#
# GUESS list (not run on a Windows PC when written): the WPF font fallback list, the hair-space tracking (width of U+200A in
# the fallback face, see $script:Hair), the chip amount 4 % (ChipAmount), the Payday 2 folder name 'PAYDAY 2'
# (same as kl_release.py), that PyInstaller's frozen exe flushes stdout line by line (python gets -u, the exe cannot);
# music: volume 0.22 as 'slightly', that MediaPlayer.MediaEnded + Position = 0 loops a .wav without a gap, that the WPF
# JPEG decoder takes the owner's screenshots as they are; the seam's gradient points (relative to the window, so the seam
# angle changes with the window's shape).
param([string]$Package = '')

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms

# Setup starts this script with -WindowStyle Hidden: an error that escapes would end it without a word. Last net: say it.
trap {
    $msg = 'The KL Merge launcher stopped: ' + $_.Exception.Message + ' (KLMergeLauncher.ps1 line ' + $_.InvocationInfo.ScriptLineNumber + ')'
    try { Add-Content -LiteralPath (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'KLMergeLauncher.log') -Value $msg -Encoding UTF8 } catch { }
    try { [void][System.Windows.MessageBox]::Show($msg + "`r`n`r`nPlease send KLMergeLauncher.log (beside the launcher) to Josh.", 'KL MERGE', 'OK', 'Error') } catch { }
    exit 1
}

$script:Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:AppId = 28000                                  # Kane & Lynch 2: Dog Days on Steam (tools/kl_autotest.py APP = 28000)
$script:HookName = 'dinput8.dll'
$script:HookOffName = 'dinput8.dll.klmerge-off'
$script:Journal = 'KLMergeInstall.json'
$script:SettingsPath = Join-Path $Here 'KLMergeLauncher.settings.json'
$script:LogPath = Join-Path $Here 'KLMergeLauncher.log'
$script:Settings = @{ DD = ''; DM = ''; PD2 = ''; Python = ''; Package = ''; MusicClip = ''; Muted = $false; Volume = 0.22 }
$script:StringKeys = @('DD', 'DM', 'PD2', 'Python', 'Package', 'MusicClip')
$script:DefaultVolume = 0.22                           # GUESS: 'slightly' (0 .. 1, MediaPlayer.Volume)
$script:Proc = $null
$script:OutFile = ''; $script:ErrFile = ''; $script:OutPos = 0; $script:ErrPos = 0
$script:PackageDir = ''
$script:Manifest = $null
$script:Python = $null       # @{ Exe = 'py'; Pre = @('-3'); Version = '3.12.7' } or $null
$script:MusicName = 'deadmen_riff.wav'          # was deadmen_menu.wav (menu loop alone), deadmen_launcher.wav (FA theme): a new name so an old file is not reused
$script:MusicPath = Join-Path $Here ('music\' + $script:MusicName)
$script:MusicToolName = 'kl_launcher_music.py'
$script:Player = $null       # System.Windows.Media.MediaPlayer, or $null when audio is unavailable
$script:MusicLoaded = $false
$script:MusicProc = $null; $script:MusicOut = ''; $script:MusicErr = ''
$script:MusicTried = $false  # one extract attempt per start (a second one on UNMUTE / after INSTALL)
$script:Note = [string][char]0x266A   # the music note shown in the header state text

# ------------------------------------------------------------------------------------------------ settings
function Load-Settings {
    if (Test-Path -LiteralPath $script:SettingsPath) {
        try {
            $j = Get-Content -LiteralPath $script:SettingsPath -Raw | ConvertFrom-Json
            foreach ($k in $script:StringKeys) {
                $v = $j.PSObject.Properties[$k]
                if ($v -and $v.Value) { $script:Settings[$k] = [string]$v.Value }
            }
            $v = $j.PSObject.Properties['Muted']
            if ($v) { $script:Settings.Muted = [bool]$v.Value }
            $v = $j.PSObject.Properties['Volume']
            if ($v -and $v.Value -ne $null) {
                $vol = [double]$v.Value
                if ($vol -ge 0 -and $vol -le 1) { $script:Settings.Volume = $vol }
            }
        } catch { }
    }
}

function Save-Settings {
    try {
        $o = New-Object PSObject
        foreach ($k in $script:StringKeys) { $o | Add-Member NoteProperty $k $script:Settings[$k] }
        $o | Add-Member NoteProperty Muted ([bool]$script:Settings.Muted)
        $o | Add-Member NoteProperty Volume ([double]$script:Settings.Volume)
        $o | ConvertTo-Json | Set-Content -LiteralPath $script:SettingsPath -Encoding UTF8     # UTF8: a folder name with accents survives (ASCII wrote '?')
    } catch { }
}

# ------------------------------------------------------------------------------------------------ Steam / games
function Get-SteamLibraries {
    $roots = @()
    foreach ($k in @('HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam')) {
        try {
            $v = Get-ItemProperty -Path $k -ErrorAction Stop
            $p = $v.SteamPath
            if (-not $p) { $p = $v.InstallPath }
            if ($p) { $roots += ($p -replace '/', '\') }
        } catch { }
    }
    $roots += 'C:\Program Files (x86)\Steam'
    $roots += 'C:\Steam'
    $libs = @()
    foreach ($r in $roots) {
        if (-not (Test-Path -LiteralPath $r)) { continue }
        if ($libs -notcontains $r) { $libs += $r }
        $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            try {
                $txt = Get-Content -LiteralPath $vdf -Raw
                foreach ($m in [regex]::Matches($txt, '"path"\s+"([^"]+)"')) {
                    $p = $m.Groups[1].Value -replace '\\\\', '\'
                    if ((Test-Path -LiteralPath $p) -and ($libs -notcontains $p)) { $libs += $p }
                }
            } catch { }
        }
    }
    return $libs
}

function Find-Game([string]$folder, [string]$exe) {
    foreach ($l in Get-SteamLibraries) {
        $p = Join-Path $l ('steamapps\common\' + $folder)
        if ($exe) { if (Test-Path -LiteralPath (Join-Path $p $exe)) { return $p } }
        elseif (Test-Path -LiteralPath $p) { return $p }
    }
    return ''
}

function Game-Running {
    try {
        $live = @(Get-Process -Name kl2 -ErrorAction SilentlyContinue | Where-Object { try { $_.Threads.Count -gt 0 } catch { $false } })
        return $live.Count -gt 0
    } catch { return $false }
}

# ------------------------------------------------------------------------------------------------ package / python
function Find-Package {
    $cands = @()
    if ($Package) { $cands += $Package }
    if ($script:Settings.Package) { $cands += $script:Settings.Package }
    $cands += (Join-Path $script:Here 'package')
    $cands += $script:Here
    foreach ($c in $cands) {
        if ($c -and (Test-Path -LiteralPath (Join-Path $c 'manifest.json'))) { return $c }
    }
    return ''
}

function Load-Manifest {
    $script:Manifest = $null
    if (-not $script:PackageDir) { return }
    try { $script:Manifest = Get-Content -LiteralPath (Join-Path $script:PackageDir 'manifest.json') -Raw | ConvertFrom-Json } catch { $script:Manifest = $null }
}

function Test-Python([string]$exe, [string[]]$pre) {
    $ErrorActionPreference = 'Continue'          # PS 5.1: a native command's stderr would otherwise throw under 'Stop'
    try {
        $out = & $exe @pre -c "import sys, zstandard; print(sys.version.split()[0])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return [string]$out }
    } catch { }
    return ''
}

function Find-Python {
    $tries = @()
    if ($script:Settings.Python) { $tries += ,@($script:Settings.Python) }
    $cmdfile = Join-Path $script:Here 'python_cmd.txt'
    if (Test-Path -LiteralPath $cmdfile) {
        $line = (Get-Content -LiteralPath $cmdfile -Raw).Trim()
        if ($line) { $tries += ,@($line) }
    }
    $tries += ,@((Join-Path $script:Here 'python\python.exe'))
    $tries += ,@('py -3')
    $tries += ,@('python')
    foreach ($t in $tries) {
        $cmd = [string]$t[0]
        if (-not $cmd) { continue }
        if ($cmd -like '* -3') { $exe = $cmd.Substring(0, $cmd.Length - 3).Trim(); $pre = @('-3') }
        else { $exe = $cmd.Trim('"'); $pre = @() }
        if ($exe -match '[\\/]' -and -not (Test-Path -LiteralPath $exe)) { continue }
        $v = Test-Python $exe $pre
        if ($v) { return @{ Exe = $exe; Pre = $pre; Version = $v; Cmd = $cmd } }
    }
    return $null
}

function Get-Sha1([string]$path) {
    try { return (Get-FileHash -LiteralPath $path -Algorithm SHA1).Hash.ToLower() } catch { return '' }
}

function Short([string]$sha) { if ($sha -and $sha.Length -ge 8) { return $sha.Substring(0, 8) } else { return '????????' } }

# ------------------------------------------------------------------------------------------------ hook on / off
function Hook-State {
    $dd = $script:Settings.DD
    if (-not $dd) { return 'none' }
    $on = Test-Path -LiteralPath (Join-Path $dd $script:HookName)
    $off = Test-Path -LiteralPath (Join-Path $dd $script:HookOffName)
    if ($on -and $off) { return 'both' }
    if ($on) { return 'on' }
    if ($off) { return 'off' }
    return 'none'
}

function Hook-Set([bool]$want) {
    # returns $true when the wanted state holds afterwards. Renames only; nothing is ever deleted.
    $dd = $script:Settings.DD
    if (-not $dd) { Log 'no Dog Days folder set'; return $false }
    if (Game-Running) { Log 'REFUSED: kl2.exe is running - close the game first.'; return $false }
    $dll = Join-Path $dd $script:HookName
    $offp = Join-Path $dd $script:HookOffName
    $st = Hook-State
    if ($want) {
        if ($st -eq 'on') { return $true }
        if ($st -eq 'both') { Log 'both dinput8.dll and dinput8.dll.klmerge-off exist: dinput8.dll stays (the mod loads); the other file is left alone.'; return $true }
        if ($st -eq 'off') {
            try { Rename-Item -LiteralPath $offp -NewName $script:HookName }
            catch { Log ('could not switch the hook ON: ' + $_.Exception.Message + ' (antivirus or another program holding the file? close it and try again)'); return $false }
            Log 'hook ON: dinput8.dll.klmerge-off -> dinput8.dll'
            return $true
        }
        Log 'no hook file in the Dog Days folder: the mod is not installed (use INSTALL / UPDATE).'
        return $false
    }
    if ($st -eq 'off' -or $st -eq 'none') { return $true }
    try {
        if ($st -eq 'both') {
            $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
            Rename-Item -LiteralPath $offp -NewName ($script:HookOffName + '.old-' + $stamp)
            Log ('an older dinput8.dll.klmerge-off was kept as ' + $script:HookOffName + '.old-' + $stamp + ' (nothing is deleted)')
        }
        Rename-Item -LiteralPath $dll -NewName $script:HookOffName
    } catch { Log ('could not switch the hook OFF: ' + $_.Exception.Message + ' (antivirus or another program holding the file? close it and try again)'); return $false }
    Log 'hook OFF: dinput8.dll -> dinput8.dll.klmerge-off (stock game; PLAY KL MERGE or HOOK ON switches it back)'
    return $true
}

function Launch-Game {
    Log ('starting the game through Steam (steam://rungameid/' + $script:AppId + ') ...')
    Start-Process ('steam://rungameid/' + $script:AppId) | Out-Null
}

# ------------------------------------------------------------------------------------------------ the window
# LOOK (owner, 2026-11-09): the in-game Dead Men theme of tools/kl_hud.py --look deadmen, not a 'launcher'. Impact
# capitals with LIGHT chipping, brush-kit bars instead of boxes, a torn dark smear behind each panel, the kit's palette:
# INK #0C0C0D, CHALK #F3F0EA, CORAL #F0475A, AMBER #E0962E, GREEN #63A05B, DEAD red #8C3138, muted keys #B8B3AA.
# Mock the owner judged: tools/launcher/design_mock_1109.html (Anton stood in for Impact there).
$script:ChipAmount = 0.04      # GUESS: share of the lettering eaten by nicks (kl_hud _chip keeps all nicks under 3 % of a glyph;
                               #        here the holes also fall on the gaps between letters, so 4 % of the tile is about that;
                               #        0 = no chipping at all)
$script:ChipSeed = 1109        # the seed of every chip, bar break and smear edge: the same wear on every start
$script:Hair = [string][char]0x200A   # GUESS: a hair space between letters stands in for letter tracking (WPF TextBlock has
                                      #        no letter-spacing); Impact has no U+200A, the fallback face draws it ~1/10 em

$wearSeed = New-Object System.Random $script:ChipSeed
$inv = [System.Globalization.CultureInfo]::InvariantCulture
function Num([double]$v) { return $v.ToString('0.##', $inv) }     # Path / Rect numbers always with a dot, whatever the locale

function Grain-Rects([int]$n, [int]$size, [int]$dot = 1, [int]$snap = 1) {
    # $n random $dot x $dot squares in a $size x $size tile; $snap > 1 puts them on a grid (the 'macroblock' look)
    $sb = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $n; $i++) {
        $x = $wearSeed.Next(0, $size); $y = $wearSeed.Next(0, $size)
        if ($snap -gt 1) { $x = $x - ($x % $snap); $y = $y - ($y % $snap) }
        [void]$sb.Append('<RectangleGeometry Rect="' + $x + ',' + $y + ',' + $dot + ',' + $dot + '"/>')
    }
    return $sb.ToString()
}

function Chip-Nicks([double]$amount, [int]$size, [bool]$big) {
    # The nicks of one $size x $size chip tile: 1 x 1, 2 x 1 and 1 x 2 holes at fixed pseudo-random spots until about
    # 70 % of $amount * area is taken, plus (when $big) two slightly larger elliptical bites. The tile is a WHITE square
    # minus these holes (CombinedGeometry Exclude) and is used as an OpacityMask: where a hole lies the ink is gone,
    # like kl_hud's _chip nicks bitten out of the glyph outline. Below ~16 px text gets the 'Light' tile (half amount,
    # 1 px holes only), after kl_hud (no chips under 16 px: a nick eats a thin stem).
    $sb = New-Object System.Text.StringBuilder
    $area = $size * $size * $amount
    $used = 0.0
    $guard = 0
    while ($used -lt $area * 0.7 -and $guard -lt 200) {
        $guard++
        $w = 1; $h = 1
        if ($big) {
            $r = $wearSeed.Next(0, 4)
            if ($r -eq 0) { $w = 2 } elseif ($r -eq 1) { $h = 2 }
        }
        $x = $wearSeed.Next(0, $size - $w + 1); $y = $wearSeed.Next(0, $size - $h + 1)
        [void]$sb.Append('<RectangleGeometry Rect="' + $x + ',' + $y + ',' + $w + ',' + $h + '"/>')
        $used += $w * $h
    }
    if ($big) {
        for ($i = 0; $i -lt 2; $i++) {
            $cx = $wearSeed.Next(2, $size - 2); $cy = $wearSeed.Next(2, $size - 2)
            $rx = 1.0 + $wearSeed.NextDouble() * 0.6; $ry = 0.7 + $wearSeed.NextDouble() * 0.4
            [void]$sb.Append('<EllipseGeometry Center="' + (Num $cx) + ',' + (Num $cy) + '" RadiusX="' + (Num $rx) + '" RadiusY="' + (Num $ry) + '"/>')
        }
    }
    return $sb.ToString()
}

function Smear-Path([int]$n, [double]$jx, [double]$jy) {
    # A torn dark smear: a closed polygon on a 1000 x 1000 box with $n points per edge, each pulled in or out by up to
    # $jx (sides) / $jy (top, bottom) units, used as the Geometry of the panel's Background DrawingBrush (Stretch=Fill, so
    # it takes the panel's size and has no layout of its own). No two edges are straight, the corners are soft (not a
    # box), like kl_hud _plate_pixels 'plate' (rows that wander by 0..4 px).
    $pts = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -le $n; $i++) { $pts.Add((Num (1000.0 * $i / $n)) + ',' + (Num (($wearSeed.NextDouble() * 2 - 1) * $jy))) }
    for ($i = 1; $i -le $n; $i++) { $pts.Add((Num (1000 + ($wearSeed.NextDouble() * 2 - 1) * $jx)) + ',' + (Num (1000.0 * $i / $n))) }
    for ($i = $n - 1; $i -ge 0; $i--) { $pts.Add((Num (1000.0 * $i / $n)) + ',' + (Num (1000 + ($wearSeed.NextDouble() * 2 - 1) * $jy))) }
    for ($i = $n - 1; $i -ge 1; $i--) { $pts.Add((Num (($wearSeed.NextDouble() * 2 - 1) * $jx)) + ',' + (Num (1000.0 * $i / $n))) }
    return 'M ' + $pts[0] + ' L ' + (($pts | Select-Object -Skip 1) -join ' ') + ' Z'
}

$chipNicks = Chip-Nicks $script:ChipAmount 24 $true
$chipLight = Chip-Nicks ($script:ChipAmount * 0.5) 24 $false
$grainLight = Grain-Rects 170 96
$grainDark = Grain-Rects 130 96
$filmLight = Grain-Rects 60 64 2            # left fallback: coarse film grain (Dead Men's grime)
$filmDark = Grain-Rects 80 64 2
$blocksLight = Grain-Rects 22 128 8 8       # right fallback: 8 px macroblocks (Dog Days' compressed video)
$blocksTint = Grain-Rects 14 128 8 8
$blocksDark = Grain-Rects 26 128 8 8
$smearStatus = Smear-Path 10 9 14           # status plate: 10 points per edge
$smearLog = Smear-Path 12 6 22              # log plate: flatter, so its top and bottom wander more in box units

$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="KL MERGE" Width="1040" Height="720" MinWidth="860" MinHeight="580"
        Background="#0C0C0D" Foreground="#F3F0EA" WindowStartupLocation="CenterScreen"
        FontFamily="Bahnschrift SemiCondensed, Segoe UI" FontSize="13" UseLayoutRounding="True" SnapsToDevicePixels="True">
  <Window.Resources>
    <!-- the chip tiles: white 24 x 24 minus a handful of holes, tiled over the Impact lettering as an OpacityMask (see Chip-Nicks) -->
    <DrawingBrush x:Key="Chip" TileMode="Tile" Viewport="0,0,24,24" ViewportUnits="Absolute">
      <DrawingBrush.Drawing>
        <GeometryDrawing Brush="White">
          <GeometryDrawing.Geometry>
            <CombinedGeometry GeometryCombineMode="Exclude">
              <CombinedGeometry.Geometry1><RectangleGeometry Rect="0,0,24,24"/></CombinedGeometry.Geometry1>
              <CombinedGeometry.Geometry2><GeometryGroup>@CHIP_NICKS@</GeometryGroup></CombinedGeometry.Geometry2>
            </CombinedGeometry>
          </GeometryDrawing.Geometry>
        </GeometryDrawing>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <DrawingBrush x:Key="ChipLight" TileMode="Tile" Viewport="0,0,24,24" ViewportUnits="Absolute">
      <DrawingBrush.Drawing>
        <GeometryDrawing Brush="White">
          <GeometryDrawing.Geometry>
            <CombinedGeometry GeometryCombineMode="Exclude">
              <CombinedGeometry.Geometry1><RectangleGeometry Rect="0,0,24,24"/></CombinedGeometry.Geometry1>
              <CombinedGeometry.Geometry2><GeometryGroup>@CHIP_LIGHT@</GeometryGroup></CombinedGeometry.Geometry2>
            </CombinedGeometry>
          </GeometryDrawing.Geometry>
        </GeometryDrawing>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <!-- the bar break: an alpha gradient with hard stops, a 1-2 px gap just under the middle of every brush bar (kl_hud stroke() gaps) -->
    <LinearGradientBrush x:Key="BarBreak" StartPoint="0,0" EndPoint="0,1">
      <GradientStop Color="#FF000000" Offset="0.0"/>
      <GradientStop Color="#FF000000" Offset="0.46"/>
      <GradientStop Color="#00000000" Offset="0.46"/>
      <GradientStop Color="#00000000" Offset="0.51"/>
      <GradientStop Color="#FF000000" Offset="0.51"/>
      <GradientStop Color="#FF000000" Offset="1.0"/>
    </LinearGradientBrush>
    <!-- GUESS: WPF takes the first installed family of the list; Impact ships with Windows since 98 -->
    <FontFamily x:Key="Head">Impact, Haettenschweiler, Arial Narrow</FontFamily>
    <FontFamily x:Key="Body">Bahnschrift SemiCondensed, Segoe UI</FontFamily>
    <SolidColorBrush x:Key="Chalk" Color="#F3F0EA"/>
    <SolidColorBrush x:Key="ChalkDim" Color="#CFCAC2"/>
    <SolidColorBrush x:Key="Coral" Color="#F0475A"/>
    <SolidColorBrush x:Key="CoralHi" Color="#FF7384"/>
    <SolidColorBrush x:Key="Key" Color="#B8B3AA"/>
    <SolidColorBrush x:Key="Grey" Color="#9A968F"/>
    <SolidColorBrush x:Key="Off" Color="#6E6A64"/>
    <SolidColorBrush x:Key="Amber" Color="#E0962E"/>
    <SolidColorBrush x:Key="Green" Color="#63A05B"/>
    <SolidColorBrush x:Key="Dead" Color="#8C3138"/>
    <DrawingBrush x:Key="Grain" TileMode="Tile" Viewport="0,0,96,96" ViewportUnits="Absolute" Opacity="0.8">
      <DrawingBrush.Drawing>
        <DrawingGroup>
          <GeometryDrawing Brush="#2CFFFFFF">
            <GeometryDrawing.Geometry><GeometryGroup><!--GRAIN_LIGHT--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
          <GeometryDrawing Brush="#4A000000">
            <GeometryDrawing.Geometry><GeometryGroup><!--GRAIN_DARK--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
        </DrawingGroup>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <!-- background fallbacks (used when bg\dead_men.jpg / bg\dog_days.jpg are missing): no art, only gradients and noise -->
    <LinearGradientBrush x:Key="FilmGrad" StartPoint="0,0" EndPoint="1,1">
      <GradientStop Color="#FF3B3936" Offset="0.0"/>
      <GradientStop Color="#FF2A2927" Offset="0.45"/>
      <GradientStop Color="#FF171615" Offset="1.0"/>
    </LinearGradientBrush>
    <DrawingBrush x:Key="FilmGrain" TileMode="Tile" Viewport="0,0,64,64" ViewportUnits="Absolute" Opacity="0.9">
      <DrawingBrush.Drawing>
        <DrawingGroup>
          <GeometryDrawing Brush="#1EFFFFFF">
            <GeometryDrawing.Geometry><GeometryGroup><!--FILM_LIGHT--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
          <GeometryDrawing Brush="#3C000000">
            <GeometryDrawing.Geometry><GeometryGroup><!--FILM_DARK--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
        </DrawingGroup>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <LinearGradientBrush x:Key="VideoGrad" StartPoint="1,0" EndPoint="0,1">
      <GradientStop Color="#FF14262C" Offset="0.0"/>
      <GradientStop Color="#FF0B161B" Offset="0.55"/>
      <GradientStop Color="#FF07090C" Offset="1.0"/>
    </LinearGradientBrush>
    <DrawingBrush x:Key="VideoBlocks" TileMode="Tile" Viewport="0,0,128,128" ViewportUnits="Absolute" Opacity="0.8">
      <DrawingBrush.Drawing>
        <DrawingGroup>
          <GeometryDrawing Brush="#12FFFFFF">
            <GeometryDrawing.Geometry><GeometryGroup><!--BLOCKS_LIGHT--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
          <GeometryDrawing Brush="#1A3FA8B8">
            <GeometryDrawing.Geometry><GeometryGroup><!--BLOCKS_TINT--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
          <GeometryDrawing Brush="#26000000">
            <GeometryDrawing.Geometry><GeometryGroup><!--BLOCKS_DARK--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
        </DrawingGroup>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <DrawingBrush x:Key="ScanLines" TileMode="Tile" Viewport="0,0,4,3" ViewportUnits="Absolute" Opacity="0.5">
      <DrawingBrush.Drawing>
        <GeometryDrawing Brush="#14000000">
          <GeometryDrawing.Geometry><RectangleGeometry Rect="0,0,4,1"/></GeometryDrawing.Geometry>
        </GeometryDrawing>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <!-- BUTTONS: no filled rectangle, no 1 px border. A brush BAR on the left (a Border whose left edge is the bar, its
         OpacityMask the break) + the Impact word. Foreground / BorderBrush = the resting colour of word / bar;
         Background is NEVER painted: it is the HOVER colour (word and bar take it on mouse-over). Pressed dims, disabled greys. -->
    <Style x:Key="KLButton" TargetType="Button">
      <Setter Property="FontFamily" Value="{StaticResource Head}"/>
      <Setter Property="FontSize" Value="27"/>
      <Setter Property="Foreground" Value="{StaticResource Chalk}"/>
      <Setter Property="BorderBrush" Value="{StaticResource Chalk}"/>
      <Setter Property="Background" Value="{StaticResource Coral}"/>
      <Setter Property="BorderThickness" Value="7,0,0,0"/>
      <Setter Property="Padding" Value="15,8,0,7"/>
      <Setter Property="Margin" Value="0,0,0,6"/>
      <Setter Property="HorizontalContentAlignment" Value="Left"/>
      <Setter Property="HorizontalAlignment" Value="Left"/>
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Tag" Value="track"/>
      <Setter Property="OpacityMask" Value="{StaticResource Chip}"/>
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Button">
            <Grid x:Name="Root" Background="Transparent">
              <Grid.ColumnDefinitions><ColumnDefinition Width="Auto"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
              <Border x:Name="Bar" Grid.Column="0" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}"
                      OpacityMask="{StaticResource BarBreak}" Margin="0,3,0,2"/>
              <ContentPresenter x:Name="Txt" Grid.Column="1" Margin="{TemplateBinding Padding}" TextElement.Foreground="{TemplateBinding Foreground}"
                                HorizontalAlignment="{TemplateBinding HorizontalContentAlignment}" VerticalAlignment="Center"/>
            </Grid>
            <ControlTemplate.Triggers>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="Txt" Property="TextElement.Foreground" Value="{Binding Background, RelativeSource={RelativeSource TemplatedParent}}"/>
                <Setter TargetName="Bar" Property="BorderBrush" Value="{Binding Background, RelativeSource={RelativeSource TemplatedParent}}"/>
              </Trigger>
              <Trigger Property="IsPressed" Value="True">
                <Setter TargetName="Root" Property="Opacity" Value="0.72"/>
              </Trigger>
              <Trigger Property="IsEnabled" Value="False">
                <Setter TargetName="Txt" Property="TextElement.Foreground" Value="{StaticResource Off}"/>
                <Setter TargetName="Bar" Property="BorderBrush" Value="{StaticResource Off}"/>
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style x:Key="KLPrimary" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="Foreground" Value="{StaticResource Coral}"/>
      <Setter Property="BorderBrush" Value="{StaticResource Coral}"/>
      <Setter Property="Background" Value="{StaticResource CoralHi}"/>
      <Setter Property="BorderThickness" Value="9,0,0,0"/>
      <Setter Property="FontSize" Value="34"/>
      <Setter Property="Padding" Value="16,8,0,7"/>
    </Style>
    <Style x:Key="KLDim" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="Foreground" Value="{StaticResource ChalkDim}"/>
      <Setter Property="FontSize" Value="23"/>
      <Setter Property="Padding" Value="15,7,0,6"/>
    </Style>
    <Style x:Key="KLSmall" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="Foreground" Value="{StaticResource ChalkDim}"/>
      <Setter Property="FontSize" Value="16"/>
      <Setter Property="BorderThickness" Value="4,0,0,0"/>
      <Setter Property="Padding" Value="10,5,0,4"/>
      <Setter Property="Margin" Value="0,0,14,2"/>
      <Setter Property="OpacityMask" Value="{StaticResource ChipLight}"/>
    </Style>
    <Style x:Key="KLMute" TargetType="Button" BasedOn="{StaticResource KLSmall}">
      <Setter Property="Foreground" Value="{StaticResource Chalk}"/>
      <Setter Property="BorderThickness" Value="0"/>
      <Setter Property="Padding" Value="6,2,6,1"/>
      <Setter Property="Margin" Value="0"/>
    </Style>
    <Style x:Key="Pick" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="FontSize" Value="14"/>
      <Setter Property="Foreground" Value="{StaticResource Grey}"/>
      <Setter Property="BorderThickness" Value="0"/>
      <Setter Property="Padding" Value="8,0,0,0"/>
      <Setter Property="Margin" Value="8,0,0,0"/>
      <Setter Property="Tag" Value="notrack"/>
      <Setter Property="OpacityMask" Value="{x:Null}"/>
    </Style>
    <Style x:Key="Key" TargetType="TextBlock">
      <Setter Property="FontFamily" Value="{StaticResource Head}"/>
      <Setter Property="FontSize" Value="15"/>
      <Setter Property="Foreground" Value="{StaticResource Key}"/>
      <Setter Property="Margin" Value="0,0,14,6"/>
      <Setter Property="VerticalAlignment" Value="Top"/>
      <Setter Property="Tag" Value="track"/>
      <Setter Property="OpacityMask" Value="{StaticResource ChipLight}"/>
    </Style>
    <Style x:Key="Val" TargetType="TextBlock">
      <Setter Property="FontFamily" Value="{StaticResource Body}"/>
      <Setter Property="FontSize" Value="12.5"/>
      <Setter Property="Foreground" Value="{StaticResource Chalk}"/>
      <Setter Property="Margin" Value="0,1,0,6"/>
      <Setter Property="TextWrapping" Value="Wrap"/>
      <Setter Property="VerticalAlignment" Value="Top"/>
    </Style>
  </Window.Resources>
  <Grid>
    <!-- background: right = Dog Days (whole window), left = Dead Men on top of it, faded out along a diagonal seam -->
    <Grid x:Name="BgRight" IsHitTestVisible="False">
      <Rectangle Fill="{StaticResource VideoGrad}"/>
      <Rectangle Fill="{StaticResource VideoBlocks}"/>
      <Rectangle Fill="{StaticResource ScanLines}"/>
      <Rectangle x:Name="BgRightImg" Fill="Transparent"/>
    </Grid>
    <Grid x:Name="BgLeft" IsHitTestVisible="False">
      <Grid.OpacityMask>
        <!-- GUESS: the gradient runs from (0, 0.325) to (1, 0.675) of the window, so the seam leans about 20 degrees
             and sits at the middle; opaque up to 0.44, gone from 0.56: a soft band, not a hard cut -->
        <LinearGradientBrush StartPoint="0,0.325" EndPoint="1,0.675">
          <GradientStop Color="#FF000000" Offset="0.0"/>
          <GradientStop Color="#FF000000" Offset="0.44"/>
          <GradientStop Color="#00000000" Offset="0.56"/>
          <GradientStop Color="#00000000" Offset="1.0"/>
        </LinearGradientBrush>
      </Grid.OpacityMask>
      <Rectangle Fill="{StaticResource FilmGrad}"/>
      <Rectangle Fill="{StaticResource FilmGrain}"/>
      <Rectangle x:Name="BgLeftImg" Fill="Transparent"/>
    </Grid>
    <!-- dim 0.28 over the drawn fallback (#47), 0.6 over photos (#99, set by Bg-Init) -->
    <Rectangle x:Name="BgDim" Fill="#47000000" IsHitTestVisible="False"/>
    <Rectangle Fill="{StaticResource Grain}" IsHitTestVisible="False"/>
    <!-- four faint diagonal scratches on the film, scaled with the window (Stretch=Fill), the stroke stays thin -->
    <Path Stretch="Fill" Stroke="#14FFFFFF" StrokeThickness="0.9" IsHitTestVisible="False"
          Data="M 30,950 L 320,100 M 660,20 L 712,980 M 930,150 L 866,830 M 130,300 L 200,296"/>
    <Rectangle IsHitTestVisible="False">
      <Rectangle.Fill>
        <RadialGradientBrush Center="0.5,0.40" GradientOrigin="0.5,0.40" RadiusX="0.80" RadiusY="0.82">
          <GradientStop Color="#00000000" Offset="0.0"/>
          <GradientStop Color="#40000000" Offset="0.55"/>
          <GradientStop Color="#E6000000" Offset="1.0"/>
        </RadialGradientBrush>
      </Rectangle.Fill>
    </Rectangle>
    <Grid Margin="30,22,30,22">
      <Grid.RowDefinitions>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="*"/>
      </Grid.RowDefinitions>
      <!-- header: the title block alone leans -0.6 degrees -->
      <Grid Grid.Row="0">
        <StackPanel Orientation="Horizontal" VerticalAlignment="Bottom" RenderTransformOrigin="0,1">
          <StackPanel.RenderTransform><RotateTransform Angle="-0.6"/></StackPanel.RenderTransform>
          <TextBlock FontFamily="{StaticResource Head}" FontSize="54" Foreground="{StaticResource Chalk}" VerticalAlignment="Bottom" Tag="notrack" OpacityMask="{StaticResource Chip}"><Run Text="KL "/><Run Text="MERGE" Foreground="{StaticResource Coral}"/></TextBlock>
          <TextBlock Text="DEAD MEN INSIDE DOG DAYS" FontFamily="{StaticResource Head}" FontSize="17" Foreground="{StaticResource Grey}" Margin="18,0,0,8" VerticalAlignment="Bottom" Tag="track" OpacityMask="{StaticResource ChipLight}"/>
        </StackPanel>
        <StackPanel Orientation="Horizontal" HorizontalAlignment="Right" VerticalAlignment="Bottom" Margin="0,0,0,8">
          <TextBlock x:Name="LblMusic" Text="&#9834; MUSIC" FontFamily="{StaticResource Head}" FontSize="14" Foreground="{StaticResource Grey}" VerticalAlignment="Center" Margin="0,0,12,0" Tag="track" OpacityMask="{StaticResource ChipLight}"/>
          <StackPanel Margin="0,0,22,0" VerticalAlignment="Center">
            <Button x:Name="BtnMute" Style="{StaticResource KLMute}" Content="MUTE" ToolTip="Mute / unmute the launcher music (a Dead Men clip read from your own Dead Men files)"/>
            <!-- the chalk underline with one break (a dashed Line in units of its 3 px thickness) -->
            <Line X2="1" Stretch="Fill" Stroke="{StaticResource Chalk}" StrokeThickness="3" StrokeDashArray="9 2.5 40 2" Margin="0,1,0,0" IsHitTestVisible="False"/>
          </StackPanel>
          <TextBlock x:Name="LblVersion" Text="TESTER BUILD" FontFamily="{StaticResource Head}" FontSize="14" Foreground="{StaticResource Grey}" VerticalAlignment="Center" Margin="0,0,0,1" Tag="track" OpacityMask="{StaticResource ChipLight}"/>
        </StackPanel>
      </Grid>
      <!-- the rule under the header: a 4 px chalk stroke with two breaks and a faint 1 px dashed line under it -->
      <Grid Grid.Row="1" Margin="0,8,0,14" Height="9">
        <Line X2="1" Stretch="Fill" Stroke="{StaticResource Chalk}" StrokeThickness="4" StrokeDashArray="70 4.5 95 2.5 400 4" Opacity="0.95" VerticalAlignment="Top"/>
        <Line X2="1" Stretch="Fill" Stroke="{StaticResource Chalk}" StrokeThickness="1" StrokeDashArray="40 9 3 12" Opacity="0.35" VerticalAlignment="Top" Margin="0,8,0,0"/>
      </Grid>
      <!-- body -->
      <Grid Grid.Row="2">
        <Grid.ColumnDefinitions>
          <ColumnDefinition Width="380"/>
          <ColumnDefinition Width="30"/>
          <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        <!-- buttons -->
        <StackPanel Grid.Column="0">
          <Button x:Name="BtnPlayMod" Style="{StaticResource KLPrimary}" Content="PLAY KL MERGE"/>
          <Button x:Name="BtnPlayStock" Style="{StaticResource KLButton}"><TextBlock Tag="track"><Run Text="PLAY DOG DAYS"/><Run Text="  (STOCK)" FontSize="14" Foreground="{StaticResource Grey}"/></TextBlock></Button>
          <TextBlock x:Name="LblHookNote" Text="" Foreground="{StaticResource Grey}" FontSize="11.5" Margin="22,-2,0,10" TextWrapping="Wrap"/>
          <Button x:Name="BtnInstall" Style="{StaticResource KLDim}" Content="INSTALL / UPDATE"/>
          <Button x:Name="BtnVerify" Style="{StaticResource KLDim}" Content="VERIFY"/>
          <Button x:Name="BtnUninstall" Style="{StaticResource KLDim}"><TextBlock Tag="track"><Run Text="UNINSTALL"/><Run Text="  (RESTORE STOCK)" FontSize="13" Foreground="{StaticResource Grey}"/></TextBlock></Button>
          <UniformGrid Columns="2" Margin="22,10,0,0" HorizontalAlignment="Left">
            <Button x:Name="BtnHook" Style="{StaticResource KLSmall}" Content="HOOK ON / OFF"/>
            <Button x:Name="BtnLogs" Style="{StaticResource KLSmall}" Content="COLLECT LOGS"/>
            <Button x:Name="BtnOpen" Style="{StaticResource KLSmall}" Content="GAME FOLDER"/>
            <Button x:Name="BtnRefresh" Style="{StaticResource KLSmall}" Content="REFRESH"/>
          </UniformGrid>
        </StackPanel>
        <!-- status: a torn dark smear (Smear-Path as the panel's Background brush, Stretch=Fill: no layout of its own, so an
             Auto row cannot blow up) at 86 %, a chalk stroke along the top with two breaks, no sides, no bottom -->
        <Grid Grid.Column="2" VerticalAlignment="Top">
          <Grid.Background>
            <DrawingBrush Stretch="Fill"><DrawingBrush.Drawing><GeometryDrawing Brush="#DB0A0A0B" Geometry="@SMEAR_STATUS@"/></DrawingBrush.Drawing></DrawingBrush>
          </Grid.Background>
          <Line X2="1" Stretch="Fill" Stroke="{StaticResource Chalk}" StrokeThickness="2" StrokeDashArray="110 7 45 15 150 4" Opacity="0.55" VerticalAlignment="Top" Margin="8,3,10,0" IsHitTestVisible="False"/>
          <Grid Margin="22,18,22,18">
            <Grid.ColumnDefinitions>
              <ColumnDefinition Width="Auto"/>
              <ColumnDefinition Width="*"/>
              <ColumnDefinition Width="Auto"/>
            </Grid.ColumnDefinitions>
            <Grid.RowDefinitions>
              <RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/>
              <RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/>
              <RowDefinition Height="Auto"/><RowDefinition Height="Auto"/><RowDefinition Height="Auto"/>
            </Grid.RowDefinitions>
            <TextBlock Grid.Row="0" Grid.ColumnSpan="3" Text="STATUS" FontFamily="{StaticResource Head}" FontSize="21" Foreground="{StaticResource Coral}" Margin="0,0,0,10" Tag="track" OpacityMask="{StaticResource Chip}"/>
            <TextBlock Grid.Row="1" Grid.Column="0" Style="{StaticResource Key}" Text="DOG DAYS"/>
            <TextBlock Grid.Row="1" Grid.Column="1" Style="{StaticResource Val}" x:Name="LblDD" Text="-"/>
            <Button    Grid.Row="1" Grid.Column="2" Style="{StaticResource Pick}" x:Name="BtnPickDD" Content="..."/>
            <TextBlock Grid.Row="2" Grid.Column="0" Style="{StaticResource Key}" Text="DEAD MEN"/>
            <TextBlock Grid.Row="2" Grid.Column="1" Style="{StaticResource Val}" x:Name="LblDM" Text="-"/>
            <Button    Grid.Row="2" Grid.Column="2" Style="{StaticResource Pick}" x:Name="BtnPickDM" Content="..."/>
            <TextBlock Grid.Row="3" Grid.Column="0" Style="{StaticResource Key}" Text="PAYDAY 2"/>
            <TextBlock Grid.Row="3" Grid.Column="1" Style="{StaticResource Val}" x:Name="LblPD2" Text="-"/>
            <Button    Grid.Row="3" Grid.Column="2" Style="{StaticResource Pick}" x:Name="BtnPickPD2" Content="..."/>
            <TextBlock Grid.Row="4" Grid.Column="0" Style="{StaticResource Key}" Text="MOD"/>
            <TextBlock Grid.Row="4" Grid.Column="1" Grid.ColumnSpan="2" Style="{StaticResource Val}" x:Name="LblMod" Text="-"/>
            <TextBlock Grid.Row="5" Grid.Column="0" Style="{StaticResource Key}" Text="HOOK"/>
            <TextBlock Grid.Row="5" Grid.Column="1" Grid.ColumnSpan="2" Style="{StaticResource Val}" x:Name="LblHook" Text="-"/>
            <TextBlock Grid.Row="6" Grid.Column="0" Style="{StaticResource Key}" Text="PACKAGE"/>
            <TextBlock Grid.Row="6" Grid.Column="1" Grid.ColumnSpan="2" Style="{StaticResource Val}" x:Name="LblPkg" Text="-"/>
            <TextBlock Grid.Row="7" Grid.Column="0" Style="{StaticResource Key}" Text="PYTHON"/>
            <TextBlock Grid.Row="7" Grid.Column="1" Grid.ColumnSpan="2" Style="{StaticResource Val}" x:Name="LblPy" Text="-"/>
            <TextBlock Grid.Row="8" Grid.Column="0" Style="{StaticResource Key}" Text="GAME"/>
            <TextBlock Grid.Row="8" Grid.Column="1" Grid.ColumnSpan="2" Style="{StaticResource Val}" x:Name="LblGame" Text="-"/>
          </Grid>
        </Grid>
      </Grid>
      <!-- log: the same smear, flatter, at 82 %, no stroke; the TextBox has no box of its own -->
      <Grid Grid.Row="3" Margin="0,22,0,0">
        <Grid.Background>
          <DrawingBrush Stretch="Fill"><DrawingBrush.Drawing><GeometryDrawing Brush="#D10A0A0B" Geometry="@SMEAR_LOG@"/></DrawingBrush.Drawing></DrawingBrush>
        </Grid.Background>
        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions>
        <TextBlock Grid.Row="0" Text="LOG" FontFamily="{StaticResource Head}" FontSize="16" Foreground="{StaticResource Grey}" Margin="14,8,0,4" Tag="track" OpacityMask="{StaticResource ChipLight}"/>
        <TextBox Grid.Row="1" x:Name="TxtLog" IsReadOnly="True" Background="Transparent" Foreground="#CFCAC2" BorderThickness="0" CaretBrush="#F3F0EA" SelectionBrush="#F0475A"
                 FontFamily="Consolas" FontSize="12" Padding="12,2,12,8" TextWrapping="NoWrap" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Auto" AcceptsReturn="True"/>
      </Grid>
    </Grid>
  </Grid>
</Window>
'@
$xaml = $xaml.Replace('@CHIP_NICKS@', $chipNicks).Replace('@CHIP_LIGHT@', $chipLight)
$xaml = $xaml.Replace('@SMEAR_STATUS@', $smearStatus).Replace('@SMEAR_LOG@', $smearLog)
$xaml = $xaml.Replace('<!--GRAIN_LIGHT-->', $grainLight).Replace('<!--GRAIN_DARK-->', $grainDark)
$xaml = $xaml.Replace('<!--FILM_LIGHT-->', $filmLight).Replace('<!--FILM_DARK-->', $filmDark)
$xaml = $xaml.Replace('<!--BLOCKS_LIGHT-->', $blocksLight).Replace('<!--BLOCKS_TINT-->', $blocksTint).Replace('<!--BLOCKS_DARK-->', $blocksDark)

$script:Win = [Windows.Markup.XamlReader]::Parse($xaml)
$ui = @{}
foreach ($n in @('LblVersion', 'BtnPlayMod', 'BtnPlayStock', 'LblHookNote', 'BtnInstall', 'BtnVerify', 'BtnUninstall', 'BtnHook', 'BtnLogs', 'BtnOpen', 'BtnRefresh',
                 'LblDD', 'BtnPickDD', 'LblDM', 'BtnPickDM', 'LblPD2', 'BtnPickPD2', 'LblMod', 'LblHook', 'LblPkg', 'LblPy', 'LblGame', 'TxtLog',
                 'LblMusic', 'BtnMute', 'BgLeft', 'BgRight', 'BgLeftImg', 'BgRightImg', 'BgDim')) {
    $ui[$n] = $script:Win.FindName($n)
}

# ------------------------------------------------------------------------------------------------ lettering helpers
function Track([string]$s) {
    # letter tracking for the Impact capitals: a hair space after every letter that is followed by a letter (see $script:Hair)
    if (-not $s -or $s.Contains($script:Hair)) { return $s }
    $sb = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $s.Length; $i++) {
        [void]$sb.Append($s[$i])
        if ($i -lt $s.Length - 1 -and $s[$i] -ne ' ' -and $s[$i + 1] -ne ' ') { [void]$sb.Append($script:Hair) }
    }
    return $sb.ToString()
}

function Track-Tree($o) {
    # applies Track to every TextBlock / Button with Tag 'track' (the styles set it on the Impact faces, 'notrack' on the title)
    if ($o -is [System.Windows.Controls.TextBlock]) {
        if ([string]$o.Tag -eq 'track') { foreach ($r in @($o.Inlines)) { if ($r -is [System.Windows.Documents.Run]) { $r.Text = Track $r.Text } } }
        return
    }
    if ($o -is [System.Windows.Controls.Button] -and ($o.Content -is [string])) {
        if ([string]$o.Tag -eq 'track') { $o.Content = Track ([string]$o.Content) }
        return
    }
    if ($o -is [System.Windows.DependencyObject]) {
        foreach ($c in [System.Windows.LogicalTreeHelper]::GetChildren($o)) { Track-Tree $c }
    }
}
try { Track-Tree $script:Win } catch { }

# value tones: green = fine, amber = a warning, dead red = an error, key grey = unknown / optional, chalk = plain
$script:Tones = @{}
foreach ($kv in @(@('ok', '#63A05B'), @('warn', '#E0962E'), @('bad', '#8C3138'), @('dim', '#B8B3AA'), @('plain', '#F3F0EA'))) {
    try {
        $b = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color][System.Windows.Media.ColorConverter]::ConvertFromString($kv[1]))
        $b.Freeze(); $script:Tones[$kv[0]] = $b
    } catch { }
}
function Set-Val($tb, [string]$text, [string]$tone = 'plain') {
    $tb.Text = $text
    try { if ($script:Tones.ContainsKey($tone)) { $tb.Foreground = $script:Tones[$tone] } } catch { }
}

# ------------------------------------------------------------------------------------------------ log pane
function Log([string]$line) {
    $t = (Get-Date -Format 'HH:mm:ss') + '  ' + $line
    try { Add-Content -LiteralPath $script:LogPath -Value $t -Encoding UTF8 } catch { }
    $ui.TxtLog.AppendText($t + "`r`n")
    $ui.TxtLog.ScrollToEnd()
}

function Log-Raw([string]$text) {
    if (-not $text) { return }
    try { Add-Content -LiteralPath $script:LogPath -Value $text.TrimEnd("`r", "`n") -Encoding UTF8 } catch { }
    $ui.TxtLog.AppendText($text.Replace("`r`n", "`n").Replace("`n", "`r`n"))
    $ui.TxtLog.ScrollToEnd()
}

# every button runs through Guard: an error is logged and shown, the window stays (an unhandled one would close it)
function Guard([scriptblock]$body) {
    try { & $body } catch {
        $m = $_.Exception.Message + ' (line ' + $_.InvocationInfo.ScriptLineNumber + ')'
        try { Log ('ERROR: ' + $m) } catch { }
        try { [void][System.Windows.MessageBox]::Show($m + "`r`n`r`nThe launcher keeps running. COLLECT LOGS and send the zip to Josh if this repeats.", 'KL MERGE', 'OK', 'Warning') } catch { }
    }
}

# ------------------------------------------------------------------------------------------------ status
function Set-Buttons([bool]$on) {
    foreach ($n in @('BtnPlayMod', 'BtnPlayStock', 'BtnInstall', 'BtnVerify', 'BtnUninstall', 'BtnHook', 'BtnLogs', 'BtnPickDD', 'BtnPickDM', 'BtnPickPD2')) { $ui[$n].IsEnabled = $on }
}

function Refresh-Status {
    $s = $script:Settings
    if (-not $s.DD -or -not (Test-Path -LiteralPath (Join-Path $s.DD 'kl2.exe'))) { $s.DD = Find-Game 'Kane & Lynch 2 - Dog Days' 'kl2.exe' }
    if (-not $s.DM -or -not (Test-Path -LiteralPath $s.DM)) { $s.DM = Find-Game 'Kane and Lynch Dead Men' 'kaneandlynch.exe' }
    if (-not $s.PD2 -or -not (Test-Path -LiteralPath $s.PD2)) { $s.PD2 = Find-Game 'PAYDAY 2' '' }     # GUESS: Steam folder name, as in kl_release.py
    # value tones (Set-Val): green = fine, amber = a warning, dead red = an error that stops INSTALL, grey = unknown / optional
    if ($s.DD) { Set-Val $ui.LblDD $s.DD 'ok' } else { Set-Val $ui.LblDD 'NOT FOUND - pick the folder that holds kl2.exe' 'bad' }
    if ($s.DM) { Set-Val $ui.LblDM $s.DM 'ok' } else { Set-Val $ui.LblDM 'NOT FOUND - needed for INSTALL (the Dead Men maps are rebuilt from it)' 'bad' }
    if ($s.PD2) { Set-Val $ui.LblPD2 $s.PD2 'ok' } else { Set-Val $ui.LblPD2 'not found (optional: the Payday 2 masks / guns are skipped)' 'warn' }

    $script:PackageDir = Find-Package
    Load-Manifest
    if ($script:Manifest) {
        $n = @($script:Manifest.entries).Count
        Set-Val $ui.LblPkg ('v' + $script:Manifest.version + ', ' + $n + ' files  -  ' + $script:PackageDir) 'plain'
        $ui.LblVersion.Text = Track ('TESTER BUILD  v' + $script:Manifest.version)
    } else {
        Set-Val $ui.LblPkg 'NO PACKAGE: run "KLMerge Setup.bat" first (it downloads and unpacks it)' 'bad'
        $ui.LblVersion.Text = Track 'TESTER BUILD'
    }

    if ($script:PackageDir -and (Test-Path -LiteralPath (Join-Path $script:PackageDir 'KLMergeSetup.exe'))) {
        Set-Val $ui.LblPy 'not needed (package has KLMergeSetup.exe)' 'plain'
    } else {
        if (-not $script:Python) { $script:Python = Find-Python }
        if ($script:Python) { Set-Val $ui.LblPy ($script:Python.Version + '  (' + $script:Python.Cmd + ', zstandard ok)') 'plain' }
        else { Set-Val $ui.LblPy 'NOT FOUND - run "KLMerge Setup.bat" (it fetches an embedded Python 3 + zstandard)' 'bad' }
    }

    if ($s.DD) {
        $jp = Join-Path $s.DD $script:Journal
        if (Test-Path -LiteralPath $jp) {
            try { $j = Get-Content -LiteralPath $jp -Raw | ConvertFrom-Json; Set-Val $ui.LblMod ('INSTALLED: ' + @($j.entries).Count + ' files (journal ' + $script:Journal + ', backups in KL_PortBackup)') 'ok' } catch { Set-Val $ui.LblMod 'installed (journal unreadable)' 'warn' }
        } else { Set-Val $ui.LblMod 'not installed' 'dim' }
        $st = Hook-State
        $dll = Join-Path $s.DD $(if ($st -eq 'off') { $script:HookOffName } else { $script:HookName })
        $sha = ''
        if ($st -ne 'none') { $sha = Get-Sha1 $dll }
        $pk = ''
        if ($script:Manifest) {
            $e = @($script:Manifest.entries | Where-Object { $_.rel -eq 'dinput8.dll' })
            if ($e.Count -gt 0) { $pk = [string]$e[0].sha1 }
        }
        $cmp = ''
        if ($sha -and $pk) { $cmp = $(if ($sha -eq $pk) { ', = package hook' } else { ', DIFFERS from the package hook (run INSTALL / UPDATE)' }) }
        $onTone = $(if ($sha -and $pk -and $sha -ne $pk) { 'warn' } else { 'ok' })
        switch ($st) {
            'on'   { Set-Val $ui.LblHook ('ON  (dinput8.dll, sha1 ' + (Short $sha) + $cmp + ')') $onTone; $ui.LblHookNote.Text = '' }
            'off'  { Set-Val $ui.LblHook ('OFF  (set aside as ' + $script:HookOffName + ', sha1 ' + (Short $sha) + $cmp + ')') 'warn'; $ui.LblHookNote.Text = 'The hook is OFF: the game runs stock. PLAY KL MERGE or HOOK ON / OFF switches it back.' }
            'both' { Set-Val $ui.LblHook ('ON, plus a stray ' + $script:HookOffName + ' (left alone)') 'warn'; $ui.LblHookNote.Text = '' }
            default { Set-Val $ui.LblHook 'no hook file (mod not installed)' 'dim'; $ui.LblHookNote.Text = '' }
        }
    } else {
        Set-Val $ui.LblMod '-' 'dim'; Set-Val $ui.LblHook '-' 'dim'; $ui.LblHookNote.Text = ''
    }
    if (Game-Running) { Set-Val $ui.LblGame 'kl2.exe is RUNNING (close it before install / uninstall / hook switch)' 'warn' } else { Set-Val $ui.LblGame 'not running' 'ok' }
    Save-Settings
}

# ------------------------------------------------------------------------------------------------ running kl_release.py
function Read-New([string]$path, [ref]$pos) {
    if (-not $path -or -not (Test-Path -LiteralPath $path)) { return '' }
    try {
        $fs = [IO.File]::Open($path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            if ($fs.Length -le $pos.Value) { return '' }
            [void]$fs.Seek($pos.Value, [IO.SeekOrigin]::Begin)
            $buf = New-Object byte[] ($fs.Length - $pos.Value)
            $n = $fs.Read($buf, 0, $buf.Length)
            $pos.Value = $pos.Value + $n
            return [Text.Encoding]::UTF8.GetString($buf, 0, $n)
        } finally { $fs.Close() }
    } catch { return '' }
}

# trailing backslashes are doubled: the C runtime's argv parser reads 'C:\Games\"' as an escaped quote
function Quote([string]$s) { return '"' + ($s -replace '(\\+)$', '$1$1') + '"' }

function Start-Tool([string]$verb, [string[]]$extra) {
    if ($script:Proc) { Log 'a job is still running - wait for it to finish.'; return }
    if (-not $script:PackageDir) { Log 'no package: run "KLMerge Setup.bat" first.'; return }
    $s = $script:Settings
    if (-not $s.DD) { Log 'no Dog Days folder: pick it with the ... button.'; return }
    if (Game-Running) { Log 'REFUSED: kl2.exe is running - close the game first.'; return }
    $argv = @($verb, (Quote $s.DD))
    if ($verb -ne 'uninstall') { $argv += '--pkg'; $argv += (Quote $script:PackageDir) }
    if ($verb -eq 'install') {
        if ($s.DM) { $argv += '--dm'; $argv += (Quote $s.DM) }
        if ($s.PD2) { $argv += '--pd2'; $argv += (Quote $s.PD2) }
    }
    if ($extra) { $argv += $extra }
    $exe = Join-Path $script:PackageDir 'KLMergeSetup.exe'
    if (Test-Path -LiteralPath $exe) {
        $file = $exe
    } else {
        if (-not $script:Python) { $script:Python = Find-Python }
        if (-not $script:Python) { Log 'no Python 3 with zstandard: run "KLMerge Setup.bat" again.'; return }
        $file = $script:Python.Exe
        $argv = @($script:Python.Pre) + @('-u', (Quote (Join-Path $script:PackageDir 'kl_release.py'))) + $argv
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $script:OutFile = Join-Path $env:TEMP ('klmerge_' + $verb + '_' + $stamp + '.out.txt')
    $script:ErrFile = Join-Path $env:TEMP ('klmerge_' + $verb + '_' + $stamp + '.err.txt')
    $script:OutPos = 0; $script:ErrPos = 0
    # the hook is switched ON only now, after every refusal above: a refused job leaves it as it was
    $flipped = $false
    if ((Hook-State) -eq 'off') {
        if (-not (Hook-Set $true)) { return }
        $flipped = $true
    }
    Log ('> ' + $file + ' ' + ($argv -join ' '))
    try {
        $script:Proc = Start-Process -FilePath $file -ArgumentList $argv -WorkingDirectory $script:PackageDir -RedirectStandardOutput $script:OutFile -RedirectStandardError $script:ErrFile -NoNewWindow -PassThru
        $null = $script:Proc.Handle   # keeps the process handle open, else .ExitCode reads empty after exit (Start-Process -PassThru quirk)
    } catch {
        Log ('could not start: ' + $_.Exception.Message); $script:Proc = $null
        if ($flipped) { [void](Hook-Set $false) }
        return
    }
    Set-Buttons $false
    $ui.BtnRefresh.IsEnabled = $false
}

$script:Timer = New-Object System.Windows.Threading.DispatcherTimer
$script:Timer.Interval = [TimeSpan]::FromMilliseconds(300)
$script:Timer.Add_Tick({
    try { Music-Poll } catch { }
    if (-not $script:Proc) { return }
    try {
        $o = Read-New $script:OutFile ([ref]$script:OutPos); if ($o) { Log-Raw $o }
        $e = Read-New $script:ErrFile ([ref]$script:ErrPos); if ($e) { Log-Raw $e }
        if ($script:Proc.HasExited) {
            Start-Sleep -Milliseconds 150
            $o = Read-New $script:OutFile ([ref]$script:OutPos); if ($o) { Log-Raw $o }
            $e = Read-New $script:ErrFile ([ref]$script:ErrPos); if ($e) { Log-Raw $e }
            $code = $script:Proc.ExitCode
            $script:Proc = $null
            Log ('finished, exit code ' + $code + $(if ($code -eq 0) { ' (OK)' } else { ' (see the lines above; 2 = refused before anything was written)' }))
            Set-Buttons $true
            $ui.BtnRefresh.IsEnabled = $true
            Refresh-Status
            if ($code -eq 0 -and -not $script:MusicLoaded) { try { Music-Extract $true } catch { } }   # INSTALL done: the Dead Men folder is known now
        }
    } catch {
        # logged once per distinct message (the timer ticks every 300 ms)
        $m = 'timer: ' + $_.Exception.Message
        if ($m -ne $script:TickErr) { $script:TickErr = $m; try { Log $m } catch { } }
        if (-not $script:Proc) { Set-Buttons $true; $ui.BtnRefresh.IsEnabled = $true }
    }
})
$script:Timer.Start()

# ------------------------------------------------------------------------------------------------ pickers / misc
function Pick-Folder([string]$what, [string]$start) {
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = $what
    $d.ShowNewFolderButton = $false
    if ($start -and (Test-Path -LiteralPath $start)) { $d.SelectedPath = $start }
    if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { return $d.SelectedPath }
    return ''
}

function Collect-Logs {
    $dd = $script:Settings.DD
    if (-not $dd) { Log 'no Dog Days folder'; return }
    $files = @()
    foreach ($pat in @('KLHook.log', 'KLHook.old.log', 'KLHook_*.dmp', 'kl2_490_crash_*.mdmp', 'KLMergeInstall.json', 'KLHook.ini', 'KLHook.result')) {
        $files += @(Get-ChildItem -LiteralPath $dd -Filter $pat -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
    }
    if (Test-Path -LiteralPath $script:LogPath) { $files += $script:LogPath }
    $files = @($files | Select-Object -Unique)
    if ($files.Count -eq 0) { Log 'nothing to collect (no KLHook.log or dumps in the game folder)'; return }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $zip = Join-Path $script:Here ('KLMerge_logs_' + $stamp + '.zip')
    # copied first with FileShare ReadWrite: the running game keeps KLHook.log open and Compress-Archive refuses such a file
    $tmp = Join-Path $env:TEMP ('klmerge_logs_' + $stamp)
    try {
        [void](New-Item -ItemType Directory -Path $tmp -Force)
        $copies = @()
        foreach ($f in $files) {
            try {
                $dstp = Join-Path $tmp ([IO.Path]::GetFileName($f))
                $src = [IO.File]::Open($f, [IO.FileMode]::Open, [IO.FileAccess]::Read, ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
                try {
                    $dst = [IO.File]::Create($dstp)
                    try { $src.CopyTo($dst) } finally { $dst.Close() }
                } finally { $src.Close() }
                $copies += $dstp
            } catch { Log ('skipped ' + $f + ': ' + $_.Exception.Message) }
        }
        if ($copies.Count -eq 0) { Log 'could not read any of the log files'; return }
        Compress-Archive -LiteralPath $copies -DestinationPath $zip -CompressionLevel Optimal
        Log ('logs collected: ' + $zip + '  (' + $copies.Count + ' files) - send this file to Josh')
        Start-Process explorer.exe ('/select,"' + $zip + '"') | Out-Null
    } catch { Log ('could not zip the logs: ' + $_.Exception.Message) }
    finally { try { [IO.Directory]::Delete($tmp, $true) } catch { } }    # the launcher's own temp copies only, never the game folder
}

# ------------------------------------------------------------------------------------------------ music
# Everything here is best effort: an exception anywhere leaves the window working and writes one log line.
function Music-Label {
    $n = $script:Note
    if ($script:Settings.Muted) {
        $ui.LblMusic.Text = Track ($n + ' MUTED'); $ui.BtnMute.Content = Track 'UNMUTE'
    } elseif ($script:MusicLoaded) {
        $ui.LblMusic.Text = Track ($n + ' DEAD MEN  ' + [int]([double]$script:Settings.Volume * 100) + '%'); $ui.BtnMute.Content = Track 'MUTE'
    } elseif ($script:MusicProc) {
        $ui.LblMusic.Text = Track ($n + ' READING YOUR DEAD MEN MUSIC ...'); $ui.BtnMute.Content = Track 'MUTE'
    } else {
        $ui.LblMusic.Text = Track ($n + ' NO MUSIC'); $ui.BtnMute.Content = Track 'MUTE'
    }
}

function Music-Init {
    try {
        $script:Player = New-Object System.Windows.Media.MediaPlayer
        $script:Player.add_MediaEnded({ try { $script:Player.Position = [TimeSpan]::Zero; $script:Player.Play() } catch { } })
        $script:Player.add_MediaFailed({ param($s, $e)
            try { $script:MusicLoaded = $false; Log ('music: playback failed (' + $e.ErrorException.Message + ') - silent'); Music-Label } catch { } })
    } catch {
        $script:Player = $null
        Log ('music: no MediaPlayer on this PC (' + $_.Exception.Message + ') - silent')
    }
}

function Music-Apply {
    # pushes Muted / Volume to the player
    if (-not $script:Player) { Music-Label; return }
    try {
        $script:Player.Volume = [double]$script:Settings.Volume
        $script:Player.IsMuted = [bool]$script:Settings.Muted
        if ($script:MusicLoaded) {
            if ($script:Settings.Muted) { $script:Player.Pause() } else { $script:Player.Play() }
        }
    } catch { Log ('music: ' + $_.Exception.Message) }
    Music-Label
}

function Music-Load {
    # opens music\deadmen_riff.wav when it exists; starts muted when it does not (nothing to play)
    $script:MusicLoaded = $false
    if (-not $script:Player) { Music-Label; return }
    if (-not (Test-Path -LiteralPath $script:MusicPath)) { Music-Label; return }
    try {
        $script:Player.Open((New-Object System.Uri($script:MusicPath)))
        $script:MusicLoaded = $true
        Music-Apply
        if (-not $script:Settings.Muted) { Log ('music: playing ' + $script:MusicPath + ' at ' + [int]([double]$script:Settings.Volume * 100) + '% (MUTE in the header turns it off)') }
    } catch {
        $script:MusicLoaded = $false
        Log ('music: could not open ' + $script:MusicPath + ' (' + $_.Exception.Message + ') - silent')
        Music-Label
    }
}

function Find-MusicTool {
    foreach ($c in @((Join-Path $script:Here $script:MusicToolName),
                     $(if ($script:PackageDir) { Join-Path $script:PackageDir ('launcher\' + $script:MusicToolName) } else { '' }),
                     (Join-Path (Split-Path -Parent $script:Here) $script:MusicToolName))) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return ''
}

function Music-Extract([bool]$again = $false) {
    # makes music\deadmen_riff.wav from the tester's OWN Dead Men PC_Def.str in the background (python kl_launcher_music.py
    # extract). Nothing of it ships. Silent when Dead Men / python / the tool are missing; exit 2 = no decodable clip.
    if ($script:MusicProc) { return }
    if ($script:MusicTried -and -not $again) { return }
    if (Test-Path -LiteralPath $script:MusicPath) { Music-Load; return }
    $dm = $script:Settings.DM
    if (-not $dm -or -not (Test-Path -LiteralPath (Join-Path $dm 'PC_Def.str'))) { Music-Label; return }
    $script:MusicTried = $true
    $tool = Find-MusicTool
    if (-not $tool) { Log ('music: ' + $script:MusicToolName + ' not found beside the launcher - no launcher music (the package needs launcher\' + $script:MusicToolName + ')'); Music-Label; return }
    if (-not $script:Python) { $script:Python = Find-Python }
    if (-not $script:Python) { Log 'music: no Python 3 found - no launcher music (run "KLMerge Setup.bat" once)'; Music-Label; return }
    $argv = @($script:Python.Pre) + @('-u', (Quote $tool), 'extract', '--dm', (Quote $dm), '--out', (Quote $script:MusicPath))
    if ($script:Settings.MusicClip) { $argv += '--clip'; $argv += (Quote $script:Settings.MusicClip) }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $script:MusicOut = Join-Path $env:TEMP ('klmerge_music_' + $stamp + '.out.txt')
    $script:MusicErr = Join-Path $env:TEMP ('klmerge_music_' + $stamp + '.err.txt')
    try {
        $dir = Split-Path -Parent $script:MusicPath
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        Log ('music: reading a Dead Men clip from your own ' + (Join-Path $dm 'PC_Def.str') + ' (a few seconds, in the background) ...')
        $script:MusicProc = Start-Process -FilePath $script:Python.Exe -ArgumentList $argv -WorkingDirectory $script:Here -RedirectStandardOutput $script:MusicOut -RedirectStandardError $script:MusicErr -NoNewWindow -PassThru
        $null = $script:MusicProc.Handle   # as for $script:Proc: without it .ExitCode is empty and exit 2 (silence) can't be told apart
    } catch {
        $script:MusicProc = $null
        Log ('music: could not start ' + $script:MusicToolName + ' (' + $_.Exception.Message + ') - silent')
    }
    Music-Label
}

function Music-Poll {
    # called from the timer: picks up the finished extract
    if (-not $script:MusicProc) { return }
    if (-not $script:MusicProc.HasExited) { return }
    $code = $script:MusicProc.ExitCode
    $script:MusicProc = $null
    $pos = 0
    $txt = (Read-New $script:MusicOut ([ref]$pos)); $pos = 0; $txt += (Read-New $script:MusicErr ([ref]$pos))
    if ($code -eq 0 -and (Test-Path -LiteralPath $script:MusicPath)) {
        $line = @($txt -split "`n" | Where-Object { $_ -like 'wrote *' }) | Select-Object -Last 1
        Log ('music: ' + $(if ($line) { $line.Trim() } else { 'clip written' }))
        Music-Load
    } else {
        $why = @($txt -split "`n" | Where-Object { $_ -like 'NO MUSIC*' -or $_ -like '*Error*' -or $_ -like '*Traceback*' }) | Select-Object -Last 1
        Log ('music: none (exit ' + $code + $(if ($why) { ': ' + $why.Trim() } else { '' }) + ') - the launcher stays silent; the mod is not affected')
        Music-Label
    }
}

# ------------------------------------------------------------------------------------------------ background images
function Bg-Brush([string]$path) {
    $bi = New-Object System.Windows.Media.Imaging.BitmapImage
    $bi.BeginInit()
    $bi.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad      # read once; the file is not kept open
    $bi.UriSource = New-Object System.Uri($path)
    $bi.EndInit()
    $bi.Freeze()
    $b = New-Object System.Windows.Media.ImageBrush($bi)
    $b.Stretch = [System.Windows.Media.Stretch]::UniformToFill
    $b.AlignmentX = [System.Windows.Media.AlignmentX]::Center
    $b.AlignmentY = [System.Windows.Media.AlignmentY]::Center
    $b.Freeze()
    return $b
}

function Bg-Init {
    # bg\dead_men.jpg (left) + bg\dog_days.jpg (right) beside the launcher or in <package>\launcher\bg; else the procedural fallback
    $dirs = @((Join-Path $script:Here 'bg'))
    if ($script:PackageDir) { $dirs += (Join-Path $script:PackageDir 'launcher\bg') }
    $got = 0
    foreach ($pair in @(@('dead_men.jpg', 'BgLeftImg'), @('dog_days.jpg', 'BgRightImg'))) {
        foreach ($d in $dirs) {
            $p = Join-Path $d $pair[0]
            if (-not (Test-Path -LiteralPath $p)) { continue }
            try { $ui[$pair[1]].Fill = Bg-Brush $p; $got++ } catch { Log ('background: ' + $pair[0] + ' not usable (' + $_.Exception.Message + ')') }
            break
        }
    }
    try {
        # with photos behind the text a stronger dim keeps it readable (0.6 = 0x99); the fallback is dark already (0.28 = 0x47 in the XAML)
        if ($got -gt 0) { $ui.BgDim.Fill = New-Object System.Windows.Media.SolidColorBrush([System.Windows.Media.Color]::FromArgb(0x99, 0, 0, 0)) }
    } catch { }
    if ($got -eq 0) { Log 'background: no bg\dead_men.jpg / bg\dog_days.jpg beside the launcher - using the drawn fallback' }
}

# ------------------------------------------------------------------------------------------------ wiring
$ui.BtnMute.Add_Click({ Guard {
    $script:Settings.Muted = -not [bool]$script:Settings.Muted
    Save-Settings
    Music-Apply
    if (-not $script:Settings.Muted -and -not $script:MusicLoaded) { Music-Extract $true }
} })
$ui.BtnPlayMod.Add_Click({ Guard {
    if ($script:Proc) { Log 'a job is still running'; return }
    if (Hook-Set $true) { Launch-Game }
    Refresh-Status
} })
$ui.BtnPlayStock.Add_Click({ Guard {
    if ($script:Proc) { Log 'a job is still running'; return }
    if (Hook-Set $false) {
        Launch-Game
        Log 'stock game started. The mod stays installed; PLAY KL MERGE puts the hook back.'
    }
    Refresh-Status
} })
# INSTALL / VERIFY / UNINSTALL: Start-Tool switches the hook ON itself, after its checks
$ui.BtnInstall.Add_Click({ Guard { Start-Tool 'install' @('--yes') } })
$ui.BtnVerify.Add_Click({ Guard { Start-Tool 'verify' @() } })
$ui.BtnUninstall.Add_Click({ Guard {
    $r = [System.Windows.MessageBox]::Show('Remove the KL Merge files and put the stock Dog Days files back from KL_PortBackup?', 'KL MERGE - UNINSTALL', 'YesNo', 'Warning')
    if ($r -ne 'Yes') { Log 'uninstall cancelled'; return }
    Start-Tool 'uninstall' @('--yes')
} })
$ui.BtnHook.Add_Click({ Guard {
    if ($script:Proc) { Log 'a job is still running'; return }
    $st = Hook-State
    if ($st -eq 'off') { [void](Hook-Set $true) } elseif ($st -eq 'none') { Log 'no hook file (mod not installed)' } else { [void](Hook-Set $false) }
    Refresh-Status
} })
$ui.BtnLogs.Add_Click({ Guard { Collect-Logs } })
$ui.BtnOpen.Add_Click({ Guard { if ($script:Settings.DD) { Start-Process explorer.exe (Quote $script:Settings.DD) | Out-Null } } })
$ui.BtnRefresh.Add_Click({ Guard { $script:Python = $null; Refresh-Status; Log 'status refreshed' } })
$ui.BtnPickDD.Add_Click({ Guard {
    $p = Pick-Folder 'Pick the Kane & Lynch 2 - Dog Days folder (the one with kl2.exe)' $script:Settings.DD
    if ($p) {
        if (Test-Path -LiteralPath (Join-Path $p 'kl2.exe')) { $script:Settings.DD = $p; Log ('Dog Days folder: ' + $p) } else { Log ('REFUSED: no kl2.exe in ' + $p) }
        Refresh-Status
    }
} })
$ui.BtnPickDM.Add_Click({ Guard {
    $p = Pick-Folder 'Pick the Kane & Lynch: Dead Men folder (the one with kaneandlynch.exe)' $script:Settings.DM
    if ($p) {
        if (Test-Path -LiteralPath (Join-Path $p 'kaneandlynch.exe')) { $script:Settings.DM = $p; Log ('Dead Men folder: ' + $p) } else { Log ('REFUSED: no kaneandlynch.exe in ' + $p) }
        Refresh-Status
    }
} })
$ui.BtnPickPD2.Add_Click({ Guard {
    $p = Pick-Folder 'Pick the PAYDAY 2 folder (optional)' $script:Settings.PD2
    if ($p) { $script:Settings.PD2 = $p; Log ('Payday 2 folder: ' + $p); Refresh-Status }
} })
$script:Win.Add_Closing({
    param($sender, $e)
    if ($script:Proc) { Log 'a job is still running: the window stays open until it ends'; $e.Cancel = $true }
})

# ------------------------------------------------------------------------------------------------ go
Load-Settings
Log ('KL Merge launcher started in ' + $script:Here)
Refresh-Status
if (-not $script:Settings.DD) { Log 'Dog Days was not found in any Steam library: use the ... button next to DOG DAYS.' }
try { Bg-Init } catch { Log ('background: ' + $_.Exception.Message + ' - using the drawn fallback') }
try {
    Music-Init
    Music-Load                      # plays when music\deadmen_riff.wav exists and Muted is off
    if (-not $script:MusicLoaded) {
        # no file yet: silent (as good as muted) until the clip has been read from the tester's own Dead Men files
        Music-Label
        if (-not $script:Settings.Muted) { Music-Extract }
    }
} catch { Log ('music: ' + $_.Exception.Message + ' - silent') }
[void]$script:Win.ShowDialog()
try { if ($script:Player) { $script:Player.Stop(); $script:Player.Close() } } catch { }
