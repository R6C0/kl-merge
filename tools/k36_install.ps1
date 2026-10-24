# k36_install.ps1 - install (or -Undo) hook k36 = k34 + klfps.c self-limiting wrappers (k34 with [FrameLimit] Enable=1 died at the first Present with c00000fd, a stack overflow).
# Install: refuses while kl2.exe runs; refuses unless the live dinput8.dll is k34 (A22B642B...) and the staged dll matches k36.md5; backs up dinput8.dll
#   and KLHook.ini as <name>.before-1024k36 (never overwritten); copies the dll. KLHook.ini is NOT changed (no block).
# Undo: puts the k34 dll back from the backup (md5 checked) and removes the ini backup when the ini is unchanged.
param([switch]$Undo, [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Force)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-1024k36'
$begin = '; --- k36 installer block BEGIN (run UNDO k36.bat to take it out) ---'
$end = '; --- k36 installer block END ---'
$OK = @{ 'A22B642B88B13A522155755F34CA6C91' = 'k34' }
function Md5($p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash.ToUpper() }
function Die($m) { Write-Host "REFUSED: $m"; exit 1 }
if (-not $Force -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Die 'kl2.exe is running' }
$dll = Join-Path $Game 'dinput8.dll'; $ini = Join-Path $Game 'KLHook.ini'
if (-not (Test-Path -LiteralPath $dll)) { Die "no dinput8.dll in $Game" }
if (-not (Test-Path -LiteralPath $ini)) { Die "no KLHook.ini in $Game" }
$enc = [Text.Encoding]::GetEncoding(28591)

if ($Undo) {
    $bd = $dll + $tag
    if (-not (Test-Path -LiteralPath $bd)) { Die "no backup dinput8.dll$tag" }
    Copy-Item -LiteralPath $bd -Destination $dll -Force
    if ((Md5 $dll) -ne (Md5 $bd)) { Die 'restore of dinput8.dll failed the md5 check' }
    Remove-Item -LiteralPath $bd
    $raw = [IO.File]::ReadAllText($ini, $enc)
    $i = $raw.IndexOf($begin); $j = $raw.IndexOf($end)
    if ($i -ge 0 -and $j -gt $i) {
        $after = $raw.Substring($j + $end.Length).TrimStart("`r", "`n")
        $head = $raw.Substring(0, $i).TrimEnd("`r", "`n")
        $nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
        $new = if ($after) { $head + $nl + $nl + $after } else { $head + $nl }
        [IO.File]::WriteAllText($ini, $new, $enc)
        Write-Host 'removed the k36 block from KLHook.ini'
    } else { Write-Host "no k36 block in KLHook.ini: ini left as it is" }
    if ((Test-Path -LiteralPath ($ini + $tag)) -and ((Md5 $ini) -eq (Md5 ($ini + $tag)))) { Remove-Item -LiteralPath ($ini + $tag) }
    $now = Md5 $dll; $name = if ($OK.ContainsKey($now)) { $OK[$now] } else { 'unknown' }
    Write-Host "k36 undone: dinput8.dll is $name again (md5 $now)"
    exit 0
}

# ---- install
$src = Join-Path $here 'dinput8.dll.k36'
$want = $null
Get-Content -LiteralPath (Join-Path $here 'k36.md5') | ForEach-Object { if ($_ -match '^([0-9A-Fa-f]{32})\s+\*?dinput8\.dll\.k36\s*$') { $want = $Matches[1].ToUpper() } }
if (-not $want) { Die 'no md5 line for dinput8.dll.k36 in k36.md5' }
if ((Md5 $src) -ne $want) { Die 'staged dinput8.dll.k36 does not match k36.md5' }
$live = Md5 $dll
if (-not $OK.ContainsKey($live)) { Die "live dinput8.dll is $live, not k34: something else changed it; look before installing" }
foreach ($f in @($dll, $ini)) { if (Test-Path -LiteralPath ($f + $tag)) { Die ((Split-Path -Leaf $f) + "$tag already exists: run UNDO first") } }
Copy-Item -LiteralPath $dll -Destination ($dll + $tag)
Copy-Item -LiteralPath $ini -Destination ($ini + $tag)
foreach ($f in @($dll, $ini)) { if ((Md5 $f) -ne (Md5 ($f + $tag))) { Die "backup of $f failed the md5 check" } }
Copy-Item -LiteralPath $src -Destination $dll -Force
if ((Md5 $dll) -ne $want) { Write-Host 'copy failed the md5 check: restoring'; Copy-Item -LiteralPath ($dll + $tag) -Destination $dll -Force; exit 1 }

Write-Host "Installed k36 (md5 $want) over $($OK[$live]). KLHook.ini is NOT touched (check [FrameLimit] yourself: Enable=0 is the stopgap; to try the limiter set Enable=1, and SwapChain=0 first if you want the safe half). Undo: UNDO k36.bat. KLHook.log lines: fps:"
exit 0
