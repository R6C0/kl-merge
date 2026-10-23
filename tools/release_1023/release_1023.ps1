# release_1023.ps1 - installs / undoes the 1023 owner release for Kane & Lynch 2: Dog Days (KLHook dinput8.dll + KLHook.ini patch).
#   powershell -ExecutionPolicy Bypass -File release_1023.ps1 -Root "<DD folder>" [-BackupDir <dir>] [-SkipRunCheck]
#   powershell -ExecutionPolicy Bypass -File release_1023.ps1 -Root "<DD folder>" -Undo [-Stamp <yyyyMMdd-HHmmss>] [-BackupDir <dir>]
# The package folder (next to this script) holds: dinput8.dll (SHIP hook), KLHook.release1023.patch.ini, kl_ini_patch.py.
# INSTALL: (1) refuses while kl2.exe runs (-SkipRunCheck: tests on a copy only); (2) checks every package file and that python works and the ini
#   patch applies, BEFORE anything is written; (3) copies <Root>\dinput8.dll and <Root>\KLHook.ini to <BackupDir> as dinput8.dll.<stamp> /
#   KLHook.ini.<stamp> (md5-checked) and writes manifest_<stamp>.txt; (4) copies the package dll in (md5-checked, rolled back on a mismatch);
#   (5) applies the ini patch with kl_ini_patch.py (comments, order and line endings of the rest stay); (6) writes "UNDO release 1023.bat"
#   (and a stamped copy) into <BackupDir>, with a copy of this script beside it, so the undo does not depend on the package folder.
#   Running it twice is harmless: nothing that is already in place is backed up again, and with nothing to change no undo is written.
# UNDO: puts dinput8.dll and KLHook.ini back from the stamped backups, byte for byte (md5-checked). What is live right now is first saved as
#   <name>.undo-<time> in <BackupDir>, so an ini edit made after the install is not lost. A file that did not exist before the install is removed.
# Never touches anything else under <Root> (no KL_PortBackup, no map zip).
param(
    [Parameter(Mandatory = $true)][Alias('Dd')][string]$Root,
    [string]$BackupDir,
    [switch]$Undo,
    [string]$Stamp,
    [switch]$SkipRunCheck,
    [switch]$BalanceOn   # also write [Balance] Enable=1 (default: Enable stays as it is in the live ini)
)
$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $BackupDir) { $BackupDir = Join-Path (Split-Path -Parent $src) 'release_1023_backup' }
$dllLive = Join-Path $Root 'dinput8.dll'
$iniLive = Join-Path $Root 'KLHook.ini'
function Md5([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash }
function Fail([string]$m, [int]$code) { Write-Host $m; exit $code }

if (-not $SkipRunCheck -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Fail 'kl2.exe is running - close the game first.' 2 }
if (-not (Test-Path -LiteralPath (Join-Path $Root 'kl2.exe'))) { Fail ('kl2.exe not found in "' + $Root + '" - wrong folder?') 2 }

# ---------------------------------------------------------------- UNDO
if ($Undo) {
    if (-not $Stamp) {
        $last = Get-ChildItem -LiteralPath $BackupDir -Filter 'manifest_*.txt' -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
        if (-not $last) { Fail ('no manifest_*.txt in ' + $BackupDir + ' - nothing to undo.') 2 }
        $Stamp = $last.BaseName.Substring('manifest_'.Length)
    }
    $mf = Join-Path $BackupDir ('manifest_' + $Stamp + '.txt')
    if (-not (Test-Path -LiteralPath $mf)) { Fail ('manifest not found: ' + $mf) 2 }
    $m = @{}
    foreach ($l in [System.IO.File]::ReadAllLines($mf)) { $i = $l.IndexOf('='); if ($i -gt 0) { $m[$l.Substring(0, $i)] = $l.Substring($i + 1) } }
    $now = Get-Date -Format 'yyyyMMdd-HHmmss'
    # verify both backups first, so a half undo cannot happen
    foreach ($k in 'dll', 'ini') {
        if ($m[$k + '_backup'] -ne 'NONE' -and $m[$k + '_backup'] -ne 'SAME') {
            $b = Join-Path $BackupDir $m[$k + '_backup']
            if (-not (Test-Path -LiteralPath $b)) { Fail ('backup missing: ' + $b + ' - nothing was changed.') 3 }
            if ((Md5 $b) -ne $m[$k + '_backup_md5']) { Fail ('backup md5 differs from the manifest: ' + $b + ' - nothing was changed.') 3 }
        }
    }
    foreach ($k in 'dll', 'ini') {
        $live = if ($k -eq 'dll') { $dllLive } else { $iniLive }
        $nm = Split-Path -Leaf $live
        if ($m[$k + '_backup'] -eq 'SAME') { Write-Host ($nm + ' was not changed by the install: left as it is.'); continue }
        if (Test-Path -LiteralPath $live) {
            if ((Md5 $live) -ne $m[$k + '_new_md5']) { Write-Host ($nm + ' has changed since the install (or another pass replaced it).') }
            Copy-Item -LiteralPath $live -Destination (Join-Path $BackupDir ($nm + '.undo-' + $now))
            Write-Host ('current ' + $nm + ' saved as ' + $nm + '.undo-' + $now)
        }
        if ($m[$k + '_backup'] -eq 'NONE') {
            if (Test-Path -LiteralPath $live) { Remove-Item -LiteralPath $live -Force; Write-Host ($nm + ' did not exist before the install: removed.') }
        } else {
            $b = Join-Path $BackupDir $m[$k + '_backup']
            Copy-Item -LiteralPath $b -Destination $live -Force
            if ((Md5 $live) -ne (Md5 $b)) { Fail ($nm + ' restore md5 mismatch!') 3 }
            Write-Host ($nm + ' restored from ' + $m[$k + '_backup'] + ' (md5 ok)')
        }
    }
    Write-Host 'undo done.'; exit 0
}

# ---------------------------------------------------------------- INSTALL
$pkgDll = Join-Path $src 'dinput8.dll'
$pkgPatch = Join-Path $src 'KLHook.release1023.patch.ini'
$pkgPy = Join-Path $src 'kl_ini_patch.py'
foreach ($p in $pkgDll, $pkgPatch, $pkgPy) { if (-not (Test-Path -LiteralPath $p)) { Fail ('missing in the package: ' + $p) 2 } }
if (-not (Test-Path -LiteralPath $iniLive)) { Fail ('no KLHook.ini in ' + $Root + ' - nothing to patch.') 2 }
# the package dll must match dinput8.dll.sha1 (first token of that file), else nothing is installed
$pkgSha = Join-Path $src 'dinput8.dll.sha1'
if (-not (Test-Path -LiteralPath $pkgSha)) { Fail ('missing in the package: ' + $pkgSha + ' - cannot verify the dll.') 2 }
$wantSha = ([System.IO.File]::ReadAllText($pkgSha).Trim() -split '\s+')[0].ToUpper()
$gotSha = (Get-FileHash -LiteralPath $pkgDll -Algorithm SHA1).Hash.ToUpper()
if ($gotSha -ne $wantSha) { Fail ('package dinput8.dll sha1 ' + $gotSha + ' differs from dinput8.dll.sha1 (' + $wantSha + ') - nothing was changed.') 3 }
Write-Host ('package dll sha1 ok: ' + $gotSha)
if (Test-Path -LiteralPath $dllLive) { Write-Host ('live dll sha1 before the install: ' + (Get-FileHash -LiteralPath $dllLive -Algorithm SHA1).Hash) }
$py = $null
foreach ($c in 'python', 'py') { if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break } }
if (-not $py) { Fail 'python not found on the PATH (needed for kl_ini_patch.py). Nothing was changed.' 2 }

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ('klrelease1023_' + [guid]::NewGuid().ToString('N') + '.ini')
function IniVal([string]$f, [string]$sec, [string]$key) {
    $in = $false
    foreach ($l in [System.IO.File]::ReadAllLines($f)) {
        $t = $l.Trim()
        if ($t.StartsWith('[')) { $in = ($t -ieq ('[' + $sec + ']')); continue }
        if ($in -and $t -match ('^' + $key + '\s*=\s*([^;\s]*)')) { return $Matches[1] }
    }
    return '(not set)'
}
$usePatch = $pkgPatch
if ($BalanceOn) {
    $usePatch = Join-Path ([System.IO.Path]::GetTempPath()) ('klrelease1023_patch_' + [guid]::NewGuid().ToString('N') + '.ini')
    [System.IO.File]::WriteAllText($usePatch, ([System.IO.File]::ReadAllText($pkgPatch) -replace '(?m)^\[Balance\]',"[Balance]`r`nEnable=1"))
}
$out = & $py $pkgPy $iniLive $usePatch -o $tmp
if ($BalanceOn -and (Test-Path -LiteralPath $usePatch)) { Remove-Item -LiteralPath $usePatch -Force }
if ($LASTEXITCODE -ne 0) { Fail ("ini patch failed (exit $LASTEXITCODE):`n" + ($out -join "`n") + "`nNothing was changed.") 3 }
$iniChanges = (Test-Path -LiteralPath $tmp) -and ((Md5 $tmp) -ne (Md5 $iniLive))
$dllChanges = (-not (Test-Path -LiteralPath $dllLive)) -or ((Md5 $dllLive) -ne (Md5 $pkgDll))
Write-Host ($out -join "`n")
$chk = if (Test-Path -LiteralPath $tmp) { $tmp } else { $iniLive }
Write-Host ('[Balance] after the patch: Enable=' + (IniVal $chk 'Balance' 'Enable') + ' Risk=' + (IniVal $chk 'Balance' 'Risk') + ' Tough=' + (IniVal $chk 'Balance' 'Tough') + ' CopToCrew=' + (IniVal $chk 'Balance' 'CopToCrew') + ' YouToCop=' + (IniVal $chk 'Balance' 'YouToCop') + ' RegenDelay=' + (IniVal $chk 'Balance' 'RegenDelay') + ' RegenTime=' + (IniVal $chk 'Balance' 'RegenTime'))
if ((IniVal $chk 'Balance' 'Enable') -ne '1') { Write-Host 'NOTE: [Balance] Enable is not 1, so the whole balance module (pass 2 included) does nothing. Re-run with -BalanceOn to switch it on.' }
if (-not $iniChanges -and -not $dllChanges) {
    if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
    Write-Host 'already installed: dinput8.dll and KLHook.ini are as the release wants them. Nothing was changed.'; exit 0
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$dllBk = 'NONE'; $dllBkMd5 = ''; $iniBk = 'NONE'; $iniBkMd5 = ''
if ($dllChanges -and (Test-Path -LiteralPath $dllLive)) {
    $dllBk = 'dinput8.dll.' + $stamp
    Copy-Item -LiteralPath $dllLive -Destination (Join-Path $BackupDir $dllBk)
    $dllBkMd5 = Md5 (Join-Path $BackupDir $dllBk)
    if ($dllBkMd5 -ne (Md5 $dllLive)) { Fail 'dll backup md5 mismatch - nothing installed.' 3 }
}
if ($iniChanges) {
    $iniBk = 'KLHook.ini.' + $stamp
    Copy-Item -LiteralPath $iniLive -Destination (Join-Path $BackupDir $iniBk)
    $iniBkMd5 = Md5 (Join-Path $BackupDir $iniBk)
    if ($iniBkMd5 -ne (Md5 $iniLive)) { Fail 'ini backup md5 mismatch - nothing installed.' 3 }
}
# unchanged files: undo has nothing to put back, so the manifest names the live file's own md5 and a backup is not needed
if (-not $dllChanges) { $dllBk = 'SAME'; $dllBkMd5 = '' }   # SAME = not changed by this install: not backed up, undo skips it
if (-not $iniChanges) { $iniBk = 'SAME'; $iniBkMd5 = '' }
try {
    if ($dllChanges) {
        Copy-Item -LiteralPath $pkgDll -Destination $dllLive -Force
        if ((Md5 $pkgDll) -ne (Md5 $dllLive)) { throw 'dinput8.dll md5 mismatch after the copy' }
        Write-Host 'dinput8.dll installed (md5 ok)'
    } else { Write-Host 'dinput8.dll is already the release hook.' }
    if ($iniChanges) {
        Copy-Item -LiteralPath $tmp -Destination $iniLive -Force
        if ((Md5 $tmp) -ne (Md5 $iniLive)) { throw 'KLHook.ini md5 mismatch after the copy' }
        Write-Host 'KLHook.ini patched (md5 ok)'
    } else { Write-Host 'KLHook.ini already has every release key.' }
} catch {
    Write-Host ('FAILED: ' + $_.Exception.Message + ' - putting the backups back.')
    if ($dllChanges) {
        if ($dllBk -eq 'NONE') { if (Test-Path -LiteralPath $dllLive) { Remove-Item -LiteralPath $dllLive -Force } }   # there was no dll before: remove the new one
        else { Copy-Item -LiteralPath (Join-Path $BackupDir $dllBk) -Destination $dllLive -Force }
    }
    if ($iniChanges -and $iniBk -ne 'NONE') { Copy-Item -LiteralPath (Join-Path $BackupDir $iniBk) -Destination $iniLive -Force }
    exit 3
} finally { if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force } }

$mfLines = @(
    ('stamp=' + $stamp),
    ('root=' + $Root),
    ('dll_backup=' + $dllBk), ('dll_backup_md5=' + $dllBkMd5), ('dll_new_md5=' + (Md5 $dllLive)),
    ('ini_backup=' + $iniBk), ('ini_backup_md5=' + $iniBkMd5), ('ini_new_md5=' + (Md5 $iniLive))
)
[System.IO.File]::WriteAllLines((Join-Path $BackupDir ('manifest_' + $stamp + '.txt')), $mfLines)
# the undo kit: a copy of this script and a bat that names this install's stamp
Copy-Item -LiteralPath $MyInvocation.MyCommand.Path -Destination (Join-Path $BackupDir 'release_1023.ps1') -Force
$bat = @(
    '@echo off',
    ('rem UNDO release 1023: puts dinput8.dll and KLHook.ini back exactly as they were before the install of ' + $stamp + '. Close the game first.'),
    ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release_1023.ps1" -Root "' + $Root + '" -Undo -Stamp ' + $stamp + ' -BackupDir "%~dp0."'),
    'pause'
)
[System.IO.File]::WriteAllLines((Join-Path $BackupDir 'UNDO release 1023.bat'), $bat, [System.Text.Encoding]::Default)
[System.IO.File]::WriteAllLines((Join-Path $BackupDir ('UNDO release 1023 ' + $stamp + '.bat')), $bat, [System.Text.Encoding]::Default)
Write-Host ('done. Backups: ' + $BackupDir)
Write-Host ('Undo: "' + (Join-Path $BackupDir 'UNDO release 1023.bat') + '"')
