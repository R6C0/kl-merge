# k34_install.ps1 - install (or -Undo) hook k34 = k32 + [VanBlow] (empty escape van can be shot to pieces and explode) + [CamSmooth] StanceMs (crouch/stand/run camera height eased) + [HUD] HideIdleEscape (van card hidden with no vehicle) + k29d + e8's v30 voice fix (KeepStock) + the 10-24 evening tracks:
#   [Unstick] cover safety net (klunstick.c), [Shield] human shield rework (klshield.c), [FrameLimit] swap-chain Present fix (klfps.c),
#   [Censor] Late/Player late head blow (klcensor.c), [Dying] almost-dead down for you / heisters hold fire (klcdying.c),
#   [CamSmooth] camera smoothing in animations and on aim out (klcamsmooth.c), [ClubCalm] read-only probe (off).
# Install: refuses while kl2.exe runs; refuses unless the live dinput8.dll is k29d (E02300DF...) or e8's v30 (E90D42C0...) and the staged
#   dll matches k34.md5; backs up dinput8.dll and KLHook.ini as <name>.before-1024k34 (never overwritten); copies the dll; appends ONE
#   marked block holding only the sections the ini does not have yet. Not one other line of the ini changes.
# Undo: puts the old dll back from the backup and cuts out the marked block (from the start marker to the end marker), nothing else.
param([switch]$Undo, [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Force)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-1024k34'
$begin = '; --- k34 installer block BEGIN (run UNDO k34.bat to take it out) ---'
$end = '; --- k34 installer block END ---'
$OK = @{ 'E02300DFBF7DAC28E355C97847281843' = 'k29d'; 'E90D42C085B471D614B22FEBDF87E7D3' = 'v30' }
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
        Write-Host 'removed the k34 block from KLHook.ini'
    } else { Write-Host "no k34 block in KLHook.ini: ini left as it is" }
    if ((Test-Path -LiteralPath ($ini + $tag)) -and ((Md5 $ini) -eq (Md5 ($ini + $tag)))) { Remove-Item -LiteralPath ($ini + $tag) }
    $now = Md5 $dll; $name = if ($OK.ContainsKey($now)) { $OK[$now] } else { 'unknown' }
    Write-Host "k34 undone: dinput8.dll is $name again (md5 $now)"
    exit 0
}

# ---- install
$src = Join-Path $here 'dinput8.dll.k34'
$want = $null
Get-Content -LiteralPath (Join-Path $here 'k34.md5') | ForEach-Object { if ($_ -match '^([0-9A-Fa-f]{32})\s+\*?dinput8\.dll\.k34\s*$') { $want = $Matches[1].ToUpper() } }
if (-not $want) { Die 'no md5 line for dinput8.dll.k34 in k34.md5' }
if ((Md5 $src) -ne $want) { Die 'staged dinput8.dll.k34 does not match k34.md5' }
$live = Md5 $dll
if (-not $OK.ContainsKey($live)) { Die "live dinput8.dll is $live, not k29d or v30: something else changed it; look before installing" }
foreach ($f in @($dll, $ini)) { if (Test-Path -LiteralPath ($f + $tag)) { Die ((Split-Path -Leaf $f) + "$tag already exists: run UNDO first") } }
Copy-Item -LiteralPath $dll -Destination ($dll + $tag)
Copy-Item -LiteralPath $ini -Destination ($ini + $tag)
foreach ($f in @($dll, $ini)) { if ((Md5 $f) -ne (Md5 ($f + $tag))) { Die "backup of $f failed the md5 check" } }
Copy-Item -LiteralPath $src -Destination $dll -Force
if ((Md5 $dll) -ne $want) { Write-Host 'copy failed the md5 check: restoring'; Copy-Item -LiteralPath ($dll + $tag) -Destination $dll -Force; exit 1 }

$sections = [ordered]@{
    'Unstick'   = @('Enable=1', 'Auto=1', 'Log=1', 'Dry=0')
    'Shield'    = @('Enable=1', 'Dry=0', 'Log=1', 'Absorb=0.65', 'AbsorbDown=0.30', 'HostageTakes=2.0', 'DownPct=35', 'ReleaseDown=1', 'Down=1')
    'Dying'     = @('Enable=1', 'Dry=1   ; 1 = log only for YOUR down; set 0 once the dying: lines look right. Heisters hold fire either way (Bots=1)', 'Log=1', 'Bots=1')
    'CamSmooth' = @('Enable=1', 'Dry=0', 'Log=1', 'DtFix=1', 'PivotMs=60', 'BlendMs=250', 'AimOutMs=320', 'AimInMs=90', 'JumpCm=12', 'JumpFov=0.05', 'StanceMs=280', 'StanceCm=6')
    'VanBlow'   = @('Enable=1', 'Dry=0', 'Log=1', 'EmptyDelay=1500')
}
$raw = [IO.File]::ReadAllText($ini, $enc)
$nl = if ($raw.Contains("`r`n") -or -not $raw.Contains("`n")) { "`r`n" } else { "`n" }
$lines = @($begin)
foreach ($s in $sections.Keys) {
    if ($raw -match ('(?im)^\s*\[' + $s + '\]')) { Write-Host "KLHook.ini already has [$s]: left alone"; continue }
    $lines += "[$s]"; $lines += $sections[$s]
    Write-Host "added [$s]"
}
$lines += $end
if ($raw.Length -gt 0 -and -not $raw.EndsWith("`n")) { $raw += $nl }
[IO.File]::WriteAllText($ini, $raw + $nl + ($lines -join $nl) + $nl, $enc)
Write-Host "Installed k34 (md5 $want) over $($OK[$live]). Undo: UNDO k34.bat. KLHook.log lines: fps:, camsm:, shield:, unstick:, dying:, censor:, vanblow:"
exit 0
