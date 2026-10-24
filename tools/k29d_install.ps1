# k29d_install.ps1 - install (or -Undo) the combined hook k29d: k29b ([CarDown], Announcer key) + [FrameLimit] frame limiter (klfps.c) with the 240/120/60/30 presets.
# NOT RUN by the agent that wrote it. Source of truth is the repo (tools\); the staged copy is in <work>\build\k29d_1024\.
# Install: refuses while kl2.exe runs; refuses unless the live dinput8.dll is exactly k29b (md5 aa912e09...) and the staged dll matches
#   k29d.md5; backs up dinput8.dll, KLHook.ini and Patch01.zip as <name>.before-1024k29d (never overwritten: a second install is refused
#   until UNDO); copies the dll; appends a [FrameLimit] section to KLHook.ini ONLY if there is none. Not one other line of the ini changes
#   (live [Voice] Announcer=0 and [CarDown] Dry=1 stay). Patch01.zip is only backed up: k29d changes nothing in it.
# Undo: puts the k29b dll back from the backup; takes out the [FrameLimit] block this installer added (found by its marker line) and nothing
#   else of the ini (later edits, e.g. by KL Mod Options, are kept); leaves Patch01.zip alone and removes its backup when identical.
param([switch]$Undo, [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Force)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-1024k29d'
$marker = '; --- added by the k29d installer (frame limiter); remove this block or run UNDO to take it out ---'
$K29B = 'AA912E09D2D5D6CA010899D505D70341'
function Md5($p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash.ToUpper() }
function Die($m) { Write-Host "REFUSED: $m"; exit 1 }
if (-not $Force -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Die 'kl2.exe is running' }
$dll = Join-Path $Game 'dinput8.dll'; $ini = Join-Path $Game 'KLHook.ini'; $p01 = Join-Path $Game 'Patch01.zip'
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
        # the block runs from the marker to the next section header that is not [FrameLimit] (or the end of the file)
        $rest = $raw.Substring($i + $marker.Length)
        $m = [regex]::Match($rest, '\r?\n(?=\[(?!FrameLimit\]))')
        $tail = if ($m.Success) { $rest.Substring($m.Index + $m.Length) } else { '' }
        $head = $raw.Substring(0, $i).TrimEnd("`r", "`n")
        $nl = if ($raw.EndsWith("`n") -and -not $raw.EndsWith("`r`n")) { "`n" } else { "`r`n" }   # the file's own last line ending
        $new = if ($tail) { $head + $nl + $nl + $tail } else { $head + $nl }
        [IO.File]::WriteAllText($ini, $new, [Text.Encoding]::GetEncoding(28591))
        Write-Host 'removed the [FrameLimit] block from KLHook.ini'
    } else { Write-Host ("no installer marker in KLHook.ini: ini left as it is (backup KLHook.ini$tag kept)") }
    if ((Test-Path -LiteralPath ($p01 + $tag)) -and ((Md5 $p01) -eq (Md5 ($p01 + $tag)))) { Remove-Item -LiteralPath ($p01 + $tag) }
    Write-Host ("k29d undone: dinput8.dll is k29b again (md5 " + (Md5 $dll) + ")")
    exit 0
}

# ---- install
$src = Join-Path $here 'dinput8.dll.k29d'
$want = $null
Get-Content -LiteralPath (Join-Path $here 'k29d.md5') | ForEach-Object { if ($_ -match '^([0-9A-Fa-f]{32})\s+\*?dinput8\.dll\.k29d\s*$') { $want = $Matches[1].ToUpper() } }
if (-not $want) { Die 'no md5 line for dinput8.dll.k29d in k29d.md5' }
if ((Md5 $src) -ne $want) { Die 'staged dinput8.dll.k29d does not match k29d.md5: rebuild the staging folder' }
if ((Md5 $dll) -ne $K29B) { Die ("live dinput8.dll is " + (Md5 $dll) + ", not k29b ($K29B): something else changed it; look before installing") }
foreach ($f in @($dll, $ini, $p01)) { if (Test-Path -LiteralPath ($f + $tag)) { Die ((Split-Path -Leaf $f) + "$tag already exists: run UNDO first (backups are never overwritten)") } }
Copy-Item -LiteralPath $dll -Destination ($dll + $tag)
Copy-Item -LiteralPath $ini -Destination ($ini + $tag)
if (Test-Path -LiteralPath $p01) { Copy-Item -LiteralPath $p01 -Destination ($p01 + $tag) }
foreach ($f in @($dll, $ini)) { if ((Md5 $f) -ne (Md5 ($f + $tag))) { Die ("backup of $f failed the md5 check") } }
Copy-Item -LiteralPath $src -Destination $dll -Force
if ((Md5 $dll) -ne $want) { Write-Host 'copy failed the md5 check: restoring k29b'; Copy-Item -LiteralPath ($dll + $tag) -Destination $dll -Force; exit 1 }
$raw = [IO.File]::ReadAllText($ini, [Text.Encoding]::GetEncoding(28591))
if ($raw -match '(?im)^\s*\[FrameLimit\]') {
    Write-Host 'KLHook.ini already has a [FrameLimit] section: left alone'
} else {
    $nl = if ($raw.EndsWith("`n") -and -not $raw.EndsWith("`r`n")) { "`n" } else { "`r`n" }   # the file's own last line ending
    $add = (@($marker, '[FrameLimit]', 'Enable=1', 'Fps=0', 'FrontEdge=1', 'PassiveWait=0', 'Log=1') -join $nl) + $nl
    if ($raw.Length -gt 0 -and -not $raw.EndsWith("`n")) { $raw += $nl }
    [IO.File]::WriteAllText($ini, $raw + $nl + $add, [Text.Encoding]::GetEncoding(28591))
    Write-Host 'added [FrameLimit] Enable=1 Fps=0 (auto = the highest of 240/120/60/30 fps the screen shows; skipped while the game vsync is on) FrontEdge=1 PassiveWait=0 Log=1'
}
Write-Host ("Installed k29d (md5 $want). Undo: UNDO k29d.bat. Look in KLHook.log for the 'fps:' lines.")
exit 0
