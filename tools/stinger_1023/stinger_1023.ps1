# stinger_1023.ps1 - installs / removes the 1023 event-stinger pass for Kane & Lynch 2: Dog Days.
#   powershell -ExecutionPolicy Bypass -File stinger_1023.ps1 -Dd "<DD folder>" [-Undo] [-Dll]
# INSTALL: (1) refuses while kl2.exe runs; (2) copies the clip folders (loud loot down dead betray last30 open reached) to
#   <DD>\KLExpansion\Stinger and md5-checks every file; (3) writes a timestamped copy of KLHook.ini (FOR MANUAL RECOVERY ONLY, undo never
#   uses it); (4) appends the [Stinger] block (KLHook.stinger.patch.ini, Folder= rewritten to the installed library) between a start and an
#   end marker (skipped when the start marker is already there).
#   The hook dinput8.dll is NOT touched unless -Dll is given (then refused unless the live dll equals the backup or the package's dll).
#   The stinger code is inert until the hook that contains klstinger.c is installed AND [Stinger] Enable=1.
# UNDO (surgical): removes only the marker block this script appended and deletes <DD>\KLExpansion\Stinger. With -Undo -Dll the dll is
#   put back from its backup, only if the live dll is still the package's.
param([Parameter(Mandatory = $true)][string]$Dd, [switch]$Undo, [switch]$Dll, [switch]$SkipRunCheck)  # SkipRunCheck: tests on a copy only
$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-1023stg'
$marker = '; stinger-1023 block (tools/kl_stinger.py)'
$markerEnd = '; stinger-1023 block end'
if (-not $SkipRunCheck -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Write-Host 'kl2.exe is running - close the game first.'; exit 2 }
if (-not (Test-Path -LiteralPath (Join-Path $Dd 'kl2.exe'))) { Write-Host ('kl2.exe not found in "' + $Dd + '"'); exit 2 }
$ini = Join-Path $Dd 'KLHook.ini'; $dllPath = Join-Path $Dd 'dinput8.dll'; $lib = Join-Path $Dd 'KLExpansion\Stinger'
$pkgDll = Join-Path $src 'dll\dinput8.dll'
function Md5([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash }
function Split-Lines([string]$t) { $t -split "`r?`n" }

if ($Undo) {
    if (Test-Path -LiteralPath $ini) {
        $lines = Split-Lines ([System.IO.File]::ReadAllText($ini, [System.Text.Encoding]::Default))
        $out = New-Object System.Collections.ArrayList; $inBlock = $false; $removed = 0
        foreach ($line in $lines) {
            if ($inBlock) { if ($line.TrimEnd() -eq $markerEnd) { $inBlock = $false }; continue }
            if ($line.TrimEnd() -eq $marker) {
                $inBlock = $true; $removed++
                if ($out.Count -gt 0 -and $out[$out.Count - 1].Trim() -eq '') { $out.RemoveAt($out.Count - 1) }
                continue
            }
            [void]$out.Add($line)
        }
        if ($inBlock) { Write-Host 'KLHook.ini has the stinger start marker but no end marker - ini NOT changed; remove the block by hand.'; exit 4 }
        if ($removed) { [System.IO.File]::WriteAllText($ini, (($out -join "`r`n").TrimEnd() + "`r`n"), [System.Text.Encoding]::Default) }
        Write-Host ("KLHook.ini: $removed marker block(s) removed; everything else left as it was.")
    } else { Write-Host 'no KLHook.ini - nothing to do there.' }
    if ($Dll) {
        $b = $dllPath + $tag
        if (-not (Test-Path -LiteralPath $b)) { Write-Host 'no dll backup - dinput8.dll left alone.' }
        elseif ((Test-Path -LiteralPath $pkgDll) -and (Md5 $dllPath) -ne (Md5 $pkgDll)) { Write-Host 'live dinput8.dll is not this package''s - left alone.' }
        else { Copy-Item -LiteralPath $b -Destination $dllPath -Force; Write-Host 'dinput8.dll restored from its backup.' }
    }
    if (Test-Path -LiteralPath $lib) { Remove-Item -LiteralPath $lib -Recurse -Force; Write-Host ('removed ' + $lib) }
    Write-Host 'undo done.'; exit 0
}

$need = @('KLHook.stinger.patch.ini'); if ($Dll) { $need += 'dll\dinput8.dll' }
foreach ($n1 in $need) { if (-not (Test-Path -LiteralPath (Join-Path $src $n1))) { Write-Host ('missing in the package: ' + $n1); exit 2 } }
if ($Dll) {
    $b = $dllPath + $tag
    if (Test-Path -LiteralPath $dllPath) {
        $live = Md5 $dllPath; $pk = Md5 $pkgDll
        $okBackup = (Test-Path -LiteralPath $b) -and ($live -eq (Md5 $b))
        if (-not ($okBackup -or $live -eq $pk)) { Write-Host 'refused: the live dinput8.dll is neither the backup nor this package''s dll (another pass or hook is installed). Nothing was changed.'; exit 3 }
    }
}
# 1. the clip library
New-Item -ItemType Directory -Force -Path $lib | Out-Null
$bad = 0; $n = 0
foreach ($gd in Get-ChildItem -LiteralPath $src -Directory | Where-Object { $_.Name -ne 'dll' }) {
    $sd = $gd.FullName
    $dd2 = Join-Path $lib $gd.Name; New-Item -ItemType Directory -Force -Path $dd2 | Out-Null
    foreach ($f in Get-ChildItem -LiteralPath $sd -Filter *.mp3) {
        $t = Join-Path $dd2 $f.Name
        Copy-Item -LiteralPath $f.FullName -Destination $t -Force
        if ((Md5 $f.FullName) -ne (Md5 $t)) { Write-Host ('MD5 MISMATCH ' + $t); $bad++ }
        $n++
    }
}
Write-Host ("$n clip files copied, $bad md5 problems")
if ($bad) { Write-Host 'stopping before the hook and the ini are touched.'; exit 3 }
# 2. the hook DLL (only with -Dll)
if ($Dll) {
    $b = $dllPath + $tag
    if ((Test-Path -LiteralPath $dllPath) -and -not (Test-Path -LiteralPath $b) -and (Md5 $dllPath) -ne (Md5 $pkgDll)) { Copy-Item -LiteralPath $dllPath -Destination $b; Write-Host ('backup ' + $b) }
    Copy-Item -LiteralPath $pkgDll -Destination $dllPath -Force
    if ((Md5 $pkgDll) -ne (Md5 $dllPath)) { Write-Host 'dinput8.dll md5 mismatch'; exit 3 }
    Write-Host 'dinput8.dll installed (md5 ok)'
} else { Write-Host 'dinput8.dll not touched (use -Dll to copy the package hook).' }
# 3. KLHook.ini
$text = [System.IO.File]::ReadAllText($ini, [System.Text.Encoding]::Default)
if ($text.Contains($marker)) { Write-Host 'KLHook.ini already has the stinger block - ini left as it is.' }
else {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $bk = $ini + $tag + '-' + $stamp
    Copy-Item -LiteralPath $ini -Destination $bk; Write-Host ('ini copy for manual recovery only: ' + $bk)
    $stg = [System.IO.File]::ReadAllText((Join-Path $src 'KLHook.stinger.patch.ini'), [System.Text.Encoding]::Default)
    $stg = $stg -replace '(?m)^Folder=[^\r\n]*', ('Folder=' + $lib)
    $new = $text.TrimEnd() + "`r`n`r`n" + $marker + "`r`n" + $stg.TrimEnd() + "`r`n" + $markerEnd + "`r`n"
    [System.IO.File]::WriteAllText($ini, $new, [System.Text.Encoding]::Default)
    Write-Host 'KLHook.ini updated: [Stinger] block appended.'
}
Write-Host 'done. Undo: UNDO stinger 1023.bat'
