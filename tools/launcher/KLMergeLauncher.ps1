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
#
# Where things are
#   package        <launcher folder>\package (manifest.json + patches\ + kl_release.py, optionally KLMergeSetup.exe),
#                  or the launcher folder itself when manifest.json lies there, or -Package <folder> / the settings file.
#   settings       KLMergeLauncher.settings.json beside this file: DD, DM, PD2, Python, Package (plain json, edit by hand if needed).
#   log            KLMergeLauncher.log beside this file (everything the log pane shows).
#   python         python_cmd.txt (written by Setup), .\python\python.exe (embedded), 'py -3', 'python' - first one that
#                  imports zstandard. Not needed when the package carries KLMergeSetup.exe.
#
# Steam launch options of the player are NEVER read or written. (Josh: your own options -o DefaultScene=... AutoExit=120
# are your test setup; with them this launcher would boot straight into F01 and quit after 120 s on YOUR PC only.)
#
# GUESS list (not run on a Windows PC when written): the WPF font fallback list, the Payday 2 folder name 'PAYDAY 2'
# (same as kl_release.py), that PyInstaller's frozen exe flushes stdout line by line (python gets -u, the exe cannot).
param([string]$Package = '')

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Windows.Forms

$script:Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:AppId = 28000                                  # Kane & Lynch 2: Dog Days on Steam (tools/kl_autotest.py APP = 28000)
$script:HookName = 'dinput8.dll'
$script:HookOffName = 'dinput8.dll.klmerge-off'
$script:Journal = 'KLMergeInstall.json'
$script:SettingsPath = Join-Path $Here 'KLMergeLauncher.settings.json'
$script:LogPath = Join-Path $Here 'KLMergeLauncher.log'
$script:Settings = @{ DD = ''; DM = ''; PD2 = ''; Python = ''; Package = '' }
$script:Proc = $null
$script:OutFile = ''; $script:ErrFile = ''; $script:OutPos = 0; $script:ErrPos = 0
$script:PackageDir = ''
$script:Manifest = $null
$script:Python = $null       # @{ Exe = 'py'; Pre = @('-3'); Version = '3.12.7' } or $null

# ------------------------------------------------------------------------------------------------ settings
function Load-Settings {
    if (Test-Path -LiteralPath $script:SettingsPath) {
        try {
            $j = Get-Content -LiteralPath $script:SettingsPath -Raw | ConvertFrom-Json
            foreach ($k in @('DD', 'DM', 'PD2', 'Python', 'Package')) {
                $v = $j.PSObject.Properties[$k]
                if ($v -and $v.Value) { $script:Settings[$k] = [string]$v.Value }
            }
        } catch { }
    }
}

function Save-Settings {
    try {
        $o = New-Object PSObject
        foreach ($k in @('DD', 'DM', 'PD2', 'Python', 'Package')) { $o | Add-Member NoteProperty $k $script:Settings[$k] }
        $o | ConvertTo-Json | Set-Content -LiteralPath $script:SettingsPath -Encoding ASCII
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
            Rename-Item -LiteralPath $offp -NewName $script:HookName
            Log 'hook ON: dinput8.dll.klmerge-off -> dinput8.dll'
            return $true
        }
        Log 'no hook file in the Dog Days folder: the mod is not installed (use INSTALL / UPDATE).'
        return $false
    }
    if ($st -eq 'off' -or $st -eq 'none') { return $true }
    if ($st -eq 'both') {
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        Rename-Item -LiteralPath $offp -NewName ($script:HookOffName + '.old-' + $stamp)
        Log ('an older dinput8.dll.klmerge-off was kept as ' + $script:HookOffName + '.old-' + $stamp + ' (nothing is deleted)')
    }
    Rename-Item -LiteralPath $dll -NewName $script:HookOffName
    Log 'hook OFF: dinput8.dll -> dinput8.dll.klmerge-off (stock game; PLAY KL MERGE or HOOK ON switches it back)'
    return $true
}

function Launch-Game {
    Log ('starting the game through Steam (steam://rungameid/' + $script:AppId + ') ...')
    Start-Process ('steam://rungameid/' + $script:AppId) | Out-Null
}

# ------------------------------------------------------------------------------------------------ the window
$grainSeed = New-Object System.Random 1313
function Grain-Rects([int]$n, [int]$size) {
    $sb = New-Object System.Text.StringBuilder
    for ($i = 0; $i -lt $n; $i++) {
        $x = $grainSeed.Next(0, $size); $y = $grainSeed.Next(0, $size)
        [void]$sb.Append('<RectangleGeometry Rect="' + $x + ',' + $y + ',1,1"/>')
    }
    return $sb.ToString()
}
$grainLight = Grain-Rects 90 96
$grainDark = Grain-Rects 70 96

$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="KL MERGE" Width="960" Height="680" MinWidth="820" MinHeight="560"
        Background="#0A0A0A" Foreground="#CFCFCF" WindowStartupLocation="CenterScreen"
        FontFamily="Segoe UI" FontSize="13" UseLayoutRounding="True" SnapsToDevicePixels="True">
  <Window.Resources>
    <!-- GUESS: WPF resolves the first family it finds in this list; Bahnschrift Condensed may show as plain Bahnschrift -->
    <FontFamily x:Key="Head">Bahnschrift Condensed, Bahnschrift, Impact, Segoe UI</FontFamily>
    <SolidColorBrush x:Key="Red" Color="#A3121A"/>
    <SolidColorBrush x:Key="RedDim" Color="#6E0C11"/>
    <SolidColorBrush x:Key="Ink" Color="#D9D9D9"/>
    <SolidColorBrush x:Key="Grey" Color="#8A8A8A"/>
    <SolidColorBrush x:Key="Rule" Color="#2C2C2C"/>
    <SolidColorBrush x:Key="Panel" Color="#121212"/>
    <DrawingBrush x:Key="Grain" TileMode="Tile" Viewport="0,0,96,96" ViewportUnits="Absolute" Opacity="0.6">
      <DrawingBrush.Drawing>
        <DrawingGroup>
          <GeometryDrawing Brush="#16FFFFFF">
            <GeometryDrawing.Geometry><GeometryGroup><!--GRAIN_LIGHT--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
          <GeometryDrawing Brush="#30000000">
            <GeometryDrawing.Geometry><GeometryGroup><!--GRAIN_DARK--></GeometryGroup></GeometryDrawing.Geometry>
          </GeometryDrawing>
        </DrawingGroup>
      </DrawingBrush.Drawing>
    </DrawingBrush>
    <Style x:Key="KLButton" TargetType="Button">
      <Setter Property="FontFamily" Value="{StaticResource Head}"/>
      <Setter Property="FontSize" Value="17"/>
      <Setter Property="Foreground" Value="{StaticResource Ink}"/>
      <Setter Property="Background" Value="#151515"/>
      <Setter Property="BorderBrush" Value="#3A3A3A"/>
      <Setter Property="Padding" Value="18,9"/>
      <Setter Property="Margin" Value="0,0,0,10"/>
      <Setter Property="HorizontalContentAlignment" Value="Left"/>
      <Setter Property="Cursor" Value="Hand"/>
      <Setter Property="Template">
        <Setter.Value>
          <ControlTemplate TargetType="Button">
            <Border x:Name="B" Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="1" Padding="{TemplateBinding Padding}">
              <Grid>
                <Rectangle x:Name="Bar" Width="3" HorizontalAlignment="Left" Margin="-18,-9,0,-9" Fill="{StaticResource Red}" Visibility="Collapsed"/>
                <ContentPresenter HorizontalAlignment="{TemplateBinding HorizontalContentAlignment}" VerticalAlignment="Center"/>
              </Grid>
            </Border>
            <ControlTemplate.Triggers>
              <Trigger Property="IsMouseOver" Value="True">
                <Setter TargetName="B" Property="BorderBrush" Value="{StaticResource Red}"/>
                <Setter TargetName="Bar" Property="Visibility" Value="Visible"/>
                <Setter TargetName="B" Property="Background" Value="#1C1C1C"/>
              </Trigger>
              <Trigger Property="IsPressed" Value="True">
                <Setter TargetName="B" Property="Background" Value="#0E0E0E"/>
              </Trigger>
              <Trigger Property="IsEnabled" Value="False">
                <Setter Property="Opacity" Value="0.35"/>
              </Trigger>
            </ControlTemplate.Triggers>
          </ControlTemplate>
        </Setter.Value>
      </Setter>
    </Style>
    <Style x:Key="KLPrimary" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="Background" Value="#7E0E14"/>
      <Setter Property="BorderBrush" Value="#A3121A"/>
      <Setter Property="Foreground" Value="#F2F2F2"/>
      <Setter Property="FontSize" Value="20"/>
      <Setter Property="Padding" Value="18,12"/>
    </Style>
    <Style x:Key="KLSmall" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="FontSize" Value="13"/>
      <Setter Property="Padding" Value="10,4"/>
      <Setter Property="Margin" Value="0,0,8,0"/>
    </Style>
    <Style x:Key="Pick" TargetType="Button" BasedOn="{StaticResource KLButton}">
      <Setter Property="FontSize" Value="12"/>
      <Setter Property="Padding" Value="7,1"/>
      <Setter Property="Margin" Value="8,0,0,0"/>
      <Setter Property="FontFamily" Value="Segoe UI"/>
    </Style>
    <Style x:Key="Key" TargetType="TextBlock">
      <Setter Property="FontFamily" Value="{StaticResource Head}"/>
      <Setter Property="FontSize" Value="13"/>
      <Setter Property="Foreground" Value="{StaticResource Grey}"/>
      <Setter Property="Margin" Value="0,0,12,4"/>
      <Setter Property="VerticalAlignment" Value="Top"/>
    </Style>
    <Style x:Key="Val" TargetType="TextBlock">
      <Setter Property="FontSize" Value="12.5"/>
      <Setter Property="Foreground" Value="{StaticResource Ink}"/>
      <Setter Property="Margin" Value="0,0,0,4"/>
      <Setter Property="TextWrapping" Value="Wrap"/>
      <Setter Property="VerticalAlignment" Value="Top"/>
    </Style>
  </Window.Resources>
  <Grid>
    <Rectangle Fill="{StaticResource Grain}" IsHitTestVisible="False"/>
    <Rectangle IsHitTestVisible="False">
      <Rectangle.Fill>
        <RadialGradientBrush Center="0.5,0.42" GradientOrigin="0.5,0.42" RadiusX="0.78" RadiusY="0.80">
          <GradientStop Color="#00000000" Offset="0.0"/>
          <GradientStop Color="#2A000000" Offset="0.55"/>
          <GradientStop Color="#D8000000" Offset="1.0"/>
        </RadialGradientBrush>
      </Rectangle.Fill>
    </Rectangle>
    <Grid Margin="30,22,30,22">
      <Grid.RowDefinitions>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="Auto"/>
        <RowDefinition Height="*"/>
      </Grid.RowDefinitions>
      <!-- header -->
      <Grid Grid.Row="0">
        <StackPanel Orientation="Horizontal" VerticalAlignment="Bottom">
          <Rectangle Width="10" Height="42" Fill="{StaticResource Red}" Margin="0,0,14,4"/>
          <TextBlock Text="KL MERGE" FontFamily="{StaticResource Head}" FontSize="46" Foreground="#E8E8E8" VerticalAlignment="Bottom"/>
          <TextBlock Text="DEAD MEN INSIDE DOG DAYS" FontFamily="{StaticResource Head}" FontSize="15" Foreground="{StaticResource Grey}" Margin="18,0,0,11" VerticalAlignment="Bottom"/>
        </StackPanel>
        <TextBlock x:Name="LblVersion" Text="TESTER BUILD" FontFamily="{StaticResource Head}" FontSize="14" Foreground="{StaticResource Grey}" HorizontalAlignment="Right" VerticalAlignment="Bottom" Margin="0,0,0,10"/>
      </Grid>
      <Rectangle Grid.Row="1" Height="1" Fill="{StaticResource Rule}" Margin="0,10,0,14"/>
      <!-- body -->
      <Grid Grid.Row="2">
        <Grid.ColumnDefinitions>
          <ColumnDefinition Width="300"/>
          <ColumnDefinition Width="24"/>
          <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>
        <!-- buttons -->
        <StackPanel Grid.Column="0">
          <Button x:Name="BtnPlayMod" Style="{StaticResource KLPrimary}" Content="PLAY KL MERGE"/>
          <Button x:Name="BtnPlayStock" Style="{StaticResource KLButton}" Content="PLAY DOG DAYS  (STOCK)"/>
          <TextBlock x:Name="LblHookNote" Text="" Foreground="{StaticResource Grey}" FontSize="11.5" Margin="0,-4,0,12" TextWrapping="Wrap"/>
          <Rectangle Height="1" Fill="{StaticResource Rule}" Margin="0,0,0,12"/>
          <Button x:Name="BtnInstall" Style="{StaticResource KLButton}" Content="INSTALL / UPDATE"/>
          <Button x:Name="BtnVerify" Style="{StaticResource KLButton}" Content="VERIFY"/>
          <Button x:Name="BtnUninstall" Style="{StaticResource KLButton}" Content="UNINSTALL  (RESTORE STOCK)"/>
          <Rectangle Height="1" Fill="{StaticResource Rule}" Margin="0,2,0,12"/>
          <WrapPanel>
            <Button x:Name="BtnHook" Style="{StaticResource KLSmall}" Content="HOOK ON / OFF"/>
            <Button x:Name="BtnLogs" Style="{StaticResource KLSmall}" Content="COLLECT LOGS"/>
            <Button x:Name="BtnOpen" Style="{StaticResource KLSmall}" Content="GAME FOLDER"/>
            <Button x:Name="BtnRefresh" Style="{StaticResource KLSmall}" Content="REFRESH"/>
          </WrapPanel>
        </StackPanel>
        <!-- status -->
        <Border Grid.Column="2" Background="{StaticResource Panel}" BorderBrush="{StaticResource Rule}" BorderThickness="1" Padding="16,12">
          <Grid>
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
            <TextBlock Grid.Row="0" Grid.ColumnSpan="3" Text="STATUS" FontFamily="{StaticResource Head}" FontSize="15" Foreground="{StaticResource Red}" Margin="0,0,0,8"/>
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
        </Border>
      </Grid>
      <Rectangle Grid.Row="3" Height="1" Fill="{StaticResource Rule}" Margin="0,16,0,10"/>
      <!-- log -->
      <Grid Grid.Row="4">
        <Grid.RowDefinitions><RowDefinition Height="Auto"/><RowDefinition Height="*"/></Grid.RowDefinitions>
        <TextBlock Grid.Row="0" Text="LOG" FontFamily="{StaticResource Head}" FontSize="13" Foreground="{StaticResource Grey}" Margin="0,0,0,4"/>
        <TextBox Grid.Row="1" x:Name="TxtLog" IsReadOnly="True" Background="#0D0D0D" Foreground="#BDBDBD" BorderBrush="{StaticResource Rule}" BorderThickness="1"
                 FontFamily="Consolas" FontSize="12" Padding="8" TextWrapping="NoWrap" VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Auto" AcceptsReturn="True"/>
      </Grid>
    </Grid>
  </Grid>
</Window>
'@
$xaml = $xaml.Replace('<!--GRAIN_LIGHT-->', $grainLight).Replace('<!--GRAIN_DARK-->', $grainDark)

$script:Win = [Windows.Markup.XamlReader]::Parse($xaml)
$ui = @{}
foreach ($n in @('LblVersion', 'BtnPlayMod', 'BtnPlayStock', 'LblHookNote', 'BtnInstall', 'BtnVerify', 'BtnUninstall', 'BtnHook', 'BtnLogs', 'BtnOpen', 'BtnRefresh',
                 'LblDD', 'BtnPickDD', 'LblDM', 'BtnPickDM', 'LblPD2', 'BtnPickPD2', 'LblMod', 'LblHook', 'LblPkg', 'LblPy', 'LblGame', 'TxtLog')) {
    $ui[$n] = $script:Win.FindName($n)
}

# ------------------------------------------------------------------------------------------------ log pane
function Log([string]$line) {
    $t = (Get-Date -Format 'HH:mm:ss') + '  ' + $line
    try { Add-Content -LiteralPath $script:LogPath -Value $t -Encoding ASCII } catch { }
    $ui.TxtLog.AppendText($t + "`r`n")
    $ui.TxtLog.ScrollToEnd()
}

function Log-Raw([string]$text) {
    if (-not $text) { return }
    try { Add-Content -LiteralPath $script:LogPath -Value $text.TrimEnd("`r", "`n") -Encoding ASCII } catch { }
    $ui.TxtLog.AppendText($text.Replace("`r`n", "`n").Replace("`n", "`r`n"))
    $ui.TxtLog.ScrollToEnd()
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
    $ui.LblDD.Text = $(if ($s.DD) { $s.DD } else { 'NOT FOUND - pick the folder that holds kl2.exe' })
    $ui.LblDM.Text = $(if ($s.DM) { $s.DM } else { 'NOT FOUND - needed for INSTALL (the Dead Men maps are rebuilt from it)' })
    $ui.LblPD2.Text = $(if ($s.PD2) { $s.PD2 } else { 'not found (optional: the Payday 2 masks / guns are skipped)' })

    $script:PackageDir = Find-Package
    Load-Manifest
    if ($script:Manifest) {
        $n = @($script:Manifest.entries).Count
        $ui.LblPkg.Text = 'v' + $script:Manifest.version + ', ' + $n + ' files  -  ' + $script:PackageDir
        $ui.LblVersion.Text = 'TESTER BUILD  v' + $script:Manifest.version
    } else {
        $ui.LblPkg.Text = 'NO PACKAGE: run "KLMerge Setup.bat" first (it downloads and unpacks it)'
        $ui.LblVersion.Text = 'TESTER BUILD'
    }

    if ($script:PackageDir -and (Test-Path -LiteralPath (Join-Path $script:PackageDir 'KLMergeSetup.exe'))) {
        $ui.LblPy.Text = 'not needed (package has KLMergeSetup.exe)'
    } else {
        if (-not $script:Python) { $script:Python = Find-Python }
        $ui.LblPy.Text = $(if ($script:Python) { $script:Python.Version + '  (' + $script:Python.Cmd + ', zstandard ok)' } else { 'NOT FOUND - run "KLMerge Setup.bat" (it fetches an embedded Python 3 + zstandard)' })
    }

    if ($s.DD) {
        $jp = Join-Path $s.DD $script:Journal
        if (Test-Path -LiteralPath $jp) {
            try { $j = Get-Content -LiteralPath $jp -Raw | ConvertFrom-Json; $ui.LblMod.Text = 'INSTALLED: ' + @($j.entries).Count + ' files (journal ' + $script:Journal + ', backups in KL_PortBackup)' } catch { $ui.LblMod.Text = 'installed (journal unreadable)' }
        } else { $ui.LblMod.Text = 'not installed' }
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
        switch ($st) {
            'on'   { $ui.LblHook.Text = 'ON  (dinput8.dll, sha1 ' + (Short $sha) + $cmp + ')'; $ui.LblHookNote.Text = '' }
            'off'  { $ui.LblHook.Text = 'OFF  (set aside as ' + $script:HookOffName + ', sha1 ' + (Short $sha) + $cmp + ')'; $ui.LblHookNote.Text = 'The hook is OFF: the game runs stock. PLAY KL MERGE or HOOK ON / OFF switches it back.' }
            'both' { $ui.LblHook.Text = 'ON, plus a stray ' + $script:HookOffName + ' (left alone)'; $ui.LblHookNote.Text = '' }
            default { $ui.LblHook.Text = 'no hook file (mod not installed)'; $ui.LblHookNote.Text = '' }
        }
    } else {
        $ui.LblMod.Text = '-'; $ui.LblHook.Text = '-'; $ui.LblHookNote.Text = ''
    }
    $ui.LblGame.Text = $(if (Game-Running) { 'kl2.exe is RUNNING (close it before install / uninstall / hook switch)' } else { 'not running' })
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

function Quote([string]$s) { return '"' + $s + '"' }

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
    Log ('> ' + $file + ' ' + ($argv -join ' '))
    try {
        $script:Proc = Start-Process -FilePath $file -ArgumentList $argv -WorkingDirectory $script:PackageDir -RedirectStandardOutput $script:OutFile -RedirectStandardError $script:ErrFile -NoNewWindow -PassThru
    } catch {
        Log ('could not start: ' + $_.Exception.Message); $script:Proc = $null; return
    }
    Set-Buttons $false
    $ui.BtnRefresh.IsEnabled = $false
}

$script:Timer = New-Object System.Windows.Threading.DispatcherTimer
$script:Timer.Interval = [TimeSpan]::FromMilliseconds(300)
$script:Timer.Add_Tick({
    if (-not $script:Proc) { return }
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
    $zip = Join-Path $script:Here ('KLMerge_logs_' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.zip')
    try {
        Compress-Archive -LiteralPath $files -DestinationPath $zip -CompressionLevel Optimal
        Log ('logs collected: ' + $zip + '  (' + $files.Count + ' files) - send this file to Josh')
        Start-Process explorer.exe ('/select,"' + $zip + '"') | Out-Null
    } catch { Log ('could not zip the logs: ' + $_.Exception.Message) }
}

# ------------------------------------------------------------------------------------------------ wiring
$ui.BtnPlayMod.Add_Click({
    if ($script:Proc) { Log 'a job is still running'; return }
    if (Hook-Set $true) { Launch-Game }
    Refresh-Status
})
$ui.BtnPlayStock.Add_Click({
    if ($script:Proc) { Log 'a job is still running'; return }
    if (Hook-Set $false) {
        Launch-Game
        Log 'stock game started. The mod stays installed; PLAY KL MERGE puts the hook back.'
    }
    Refresh-Status
})
$ui.BtnInstall.Add_Click({
    $st = Hook-State
    if ($st -eq 'off') { if (-not (Hook-Set $true)) { return } }
    Start-Tool 'install' @('--yes')
})
$ui.BtnVerify.Add_Click({
    $st = Hook-State
    if ($st -eq 'off') { if (-not (Hook-Set $true)) { return } }
    Start-Tool 'verify' @()
})
$ui.BtnUninstall.Add_Click({
    $r = [System.Windows.MessageBox]::Show('Remove the KL Merge files and put the stock Dog Days files back from KL_PortBackup?', 'KL MERGE - UNINSTALL', 'YesNo', 'Warning')
    if ($r -ne 'Yes') { Log 'uninstall cancelled'; return }
    $st = Hook-State
    if ($st -eq 'off') { if (-not (Hook-Set $true)) { return } }
    Start-Tool 'uninstall' @('--yes')
})
$ui.BtnHook.Add_Click({
    if ($script:Proc) { Log 'a job is still running'; return }
    $st = Hook-State
    if ($st -eq 'off') { [void](Hook-Set $true) } elseif ($st -eq 'none') { Log 'no hook file (mod not installed)' } else { [void](Hook-Set $false) }
    Refresh-Status
})
$ui.BtnLogs.Add_Click({ Collect-Logs })
$ui.BtnOpen.Add_Click({ if ($script:Settings.DD) { Start-Process explorer.exe (Quote $script:Settings.DD) | Out-Null } })
$ui.BtnRefresh.Add_Click({ $script:Python = $null; Refresh-Status; Log 'status refreshed' })
$ui.BtnPickDD.Add_Click({
    $p = Pick-Folder 'Pick the Kane & Lynch 2 - Dog Days folder (the one with kl2.exe)' $script:Settings.DD
    if ($p) {
        if (Test-Path -LiteralPath (Join-Path $p 'kl2.exe')) { $script:Settings.DD = $p; Log ('Dog Days folder: ' + $p) } else { Log ('REFUSED: no kl2.exe in ' + $p) }
        Refresh-Status
    }
})
$ui.BtnPickDM.Add_Click({
    $p = Pick-Folder 'Pick the Kane & Lynch: Dead Men folder (the one with kaneandlynch.exe)' $script:Settings.DM
    if ($p) {
        if (Test-Path -LiteralPath (Join-Path $p 'kaneandlynch.exe')) { $script:Settings.DM = $p; Log ('Dead Men folder: ' + $p) } else { Log ('REFUSED: no kaneandlynch.exe in ' + $p) }
        Refresh-Status
    }
})
$ui.BtnPickPD2.Add_Click({
    $p = Pick-Folder 'Pick the PAYDAY 2 folder (optional)' $script:Settings.PD2
    if ($p) { $script:Settings.PD2 = $p; Log ('Payday 2 folder: ' + $p); Refresh-Status }
})
$script:Win.Add_Closing({
    param($sender, $e)
    if ($script:Proc) { Log 'a job is still running: the window stays open until it ends'; $e.Cancel = $true }
})

# ------------------------------------------------------------------------------------------------ go
Load-Settings
Log ('KL Merge launcher started in ' + $script:Here)
Refresh-Status
if (-not $script:Settings.DD) { Log 'Dog Days was not found in any Steam library: use the ... button next to DOG DAYS.' }
[void]$script:Win.ShowDialog()
