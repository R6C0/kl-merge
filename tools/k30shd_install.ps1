# k30shd_install.ps1 - install (or -Undo) hook k30shd = k29d (frame limiter, k29b) + klshield.c ([Shield] human shield rework).
# NOT RUN by the agent that wrote it (the owner was playing). Source of truth is the repo (tools\); the staged copy is in <work>\build\shield_1024b\.
# Install: refuses while kl2.exe runs; refuses unless the live dinput8.dll is exactly k29d (md5 E02300DF...) and the staged dll matches
#   k30shd.md5; backs up dinput8.dll and KLHook.ini as <name>.before-1024k30shd (never overwritten: a second install is refused until UNDO);
#   copies the dll; appends a [Shield] block to KLHook.ini ONLY if there is none. Not one other line of the ini changes.
# Undo: puts the k29d dll back from the backup; takes out the [Shield] block this installer added (found by its marker line) and nothing
#   else of the ini (later edits, e.g. by KL Mod Options, are kept).
param([switch]$Undo, [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Force)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-1024k30shd'
$marker = '; --- added by the k30shd installer (human shield rework); remove this block or run UNDO to take it out ---'
$K29D = 'E02300DFBF7DAC28E355C97847281843'
function Md5($p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash.ToUpper() }
function Die($m) { Write-Host "REFUSED: $m"; exit 1 }
if (-not $Force -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Die 'kl2.exe is running' }
$dll = Join-Path $Game 'dinput8.dll'; $ini = Join-Path $Game 'KLHook.ini'
if (-not (Test-Path -LiteralPath $dll)) { Die "no dinput8.dll in $Game" }
if (-not (Test-Path -LiteralPath $ini)) { Die "no KLHook.ini in $Game" }

if ($Undo) {
    $bd = $dll + $tag
    if (-not (Test-Path -LiteralPath $bd)) { Die "no backup dinput8.dll$tag" }
    Copy-Item -LiteralPath $bd -Destination $dll -Force
    if ((Md5 $dll) -ne (Md5 $bd)) { Die 'restore of dinput8.dll failed the md5 check' }
    Remove-Item -LiteralPath $bd
    $raw = [IO.File]::ReadAllText($ini, [Text.Encoding]::GetEncoding(28591))
    $i = $raw.IndexOf($marker)
    if ($i -ge 0) {
        # the block runs from the marker to the next section header that is not [Shield] (or the end of the file)
        $rest = $raw.Substring($i + $marker.Length)
        $m = [regex]::Match($rest, '\r?\n(?=\[(?!Shield\]))')
        $tail = if ($m.Success) { $rest.Substring($m.Index + $m.Length) } else { '' }
        $head = $raw.Substring(0, $i).TrimEnd("`r", "`n")
        $nl = if ($raw.EndsWith("`n") -and -not $raw.EndsWith("`r`n")) { "`n" } else { "`r`n" }
        $new = if ($tail) { $head + $nl + $nl + $tail } else { $head + $nl }
        [IO.File]::WriteAllText($ini, $new, [Text.Encoding]::GetEncoding(28591))
        Write-Host 'removed the [Shield] block from KLHook.ini'
    } else { Write-Host ("no installer marker in KLHook.ini: ini left as it is (backup KLHook.ini$tag kept)") }
    if ((Test-Path -LiteralPath ($ini + $tag)) -and ((Md5 $ini) -eq (Md5 ($ini + $tag)))) { Remove-Item -LiteralPath ($ini + $tag) }
    Write-Host ("k30shd undone:dinput8.dll is k29d again (md5 " + (Md5 $dll) + ")")
    exit 0
}

# ---- install
$src = Join-Path $here 'dinput8.dll.k30shd'
$want = $null
Get-Content -LiteralPath (Join-Path $here 'k30shd.md5') | ForEach-Object { if ($_ -match '^([0-9A-Fa-f]{32})\s+\*?dinput8\.dll\.k30shd\s*$') { $want = $Matches[1].ToUpper() } }
if (-not $want) { Die 'no md5 line for dinput8.dll.k30shd in k30shd.md5' }
if ((Md5 $src) -ne $want) { Die 'staged dinput8.dll.k30shd does not match k30shd.md5: rebuild the staging folder' }
if ((Md5 $dll) -ne $K29D) { Die ("live dinput8.dll is " + (Md5 $dll) + ", not k29d ($K29D): something else changed it; look before installing") }
foreach ($f in @($dll, $ini)) { if (Test-Path -LiteralPath ($f + $tag)) { Die ((Split-Path -Leaf $f) + "$tag already exists: run UNDO first (backups are never overwritten)") } }
Copy-Item -LiteralPath $dll -Destination ($dll + $tag)
Copy-Item -LiteralPath $ini -Destination ($ini + $tag)
foreach ($f in @($dll, $ini)) { if ((Md5 $f) -ne (Md5 ($f + $tag))) { Die ("backup of $f failed the md5 check") } }
Copy-Item -LiteralPath $src -Destination $dll -Force
if ((Md5 $dll) -ne $want) { Write-Host 'copy failed the md5 check: restoring k29d'; Copy-Item -LiteralPath ($dll + $tag) -Destination $dll -Force; exit 1 }
$raw = [IO.File]::ReadAllText($ini, [Text.Encoding]::GetEncoding(28591))
if ($raw -match '(?im)^\s*\[Shield\]') {
    Write-Host 'KLHook.ini already has a [Shield] section: left alone'
} else {
    $nl = if ($raw.EndsWith("`n") -and -not $raw.EndsWith("`r`n")) { "`n" } else { "`r`n" }
    $add = (@($marker, '[Shield]', 'Enable=1', 'Dry=0', 'Log=1', 'Absorb=0.65', 'AbsorbDown=0.30', 'HostageTakes=2.0', 'DownPct=35', 'ReleaseDown=1', 'Down=1') -join $nl) + $nl
    if ($raw.Length -gt 0 -and -not $raw.EndsWith("`n")) { $raw += $nl }
    [IO.File]::WriteAllText($ini, $raw + $nl + $add, [Text.Encoding]::GetEncoding(28591))
    Write-Host 'added [Shield] Enable=1 Dry=0 (set Dry=1 for log-only) Absorb=0.65 HostageTakes=2.0 DownPct=35 ReleaseDown=1'
}
Write-Host ("Installed k30shd (md5 $want). Undo: UNDO k30shd.bat. Look in KLHook.log for the 'shield:' lines (YOU HOLD ... gives the raw hold fields).")
exit 0
