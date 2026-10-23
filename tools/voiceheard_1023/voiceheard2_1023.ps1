# voiceheard2 1023: per-map version of voiceheard_1023.ps1. Puts a map's Dead Men voice data WITH the radio twins
# (2418 KLVoice leaves) into <DD>\KLExpansion\Maps\<Map>. The package folder out\<Map> holds the five files; its zip differs from the
# zip installed on 2026-10-23 only in the .LOC files the rebuild changed and the .SND (other members, Russian/Japanese .LOC kept).
# Install: moves the five live files to *.before-voiceheard, copies the new ones. Undo (-Undo): puts the *.before-voiceheard files back.
# DM01 behaves exactly as voiceheard_1023.ps1 (same md5 guard, same backup suffix). Add a map: add a row to $maps.
param([string]$Map = 'DM02', [string]$Root = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Undo)
$ErrorActionPreference = 'Stop'
# map -> slot file prefix, md5 prefix of the installed <slot>.zip this package was made against
$maps = @{
    'DM01' = @{ Slot = 'F01_Main'; Md5 = '82B33BF8AA4A' }
    'DM02' = @{ Slot = 'F02_Main'; Md5 = '966A19142BA7' }
}
function Fail($m) { Write-Host "FAILED: $m"; exit 1 }
if (-not $maps.ContainsKey($Map)) { Fail "unknown map '$Map' (known: $($maps.Keys -join ', ')). Nothing was changed." }
$slot = $maps[$Map].Slot
$M = Join-Path $Root "KLExpansion\Maps\$Map"
$SRC = Join-Path $PSScriptRoot "out\$Map"
$files = "$slot.zip", "$slot.WAV", "$slot.WHD", "${slot}_LS.SND", 'KLTalk.ini'
if (Get-Process kl2 -ErrorAction SilentlyContinue) { Fail 'close the game first (kl2.exe is running). Nothing was changed.' }
if (-not (Test-Path -LiteralPath $M)) { Fail "no map folder $M" }
if ($Undo) {
    foreach ($f in $files) { if (-not (Test-Path -LiteralPath (Join-Path $M ($f + '.before-voiceheard')))) { Fail "no backup $f.before-voiceheard. Nothing was changed." } }
    foreach ($f in $files) {
        Remove-Item -LiteralPath (Join-Path $M $f) -Force
        Move-Item -LiteralPath (Join-Path $M ($f + '.before-voiceheard')) -Destination (Join-Path $M $f)
    }
    Write-Host "voiceheard undone: $Map has its earlier voice data again."; exit 0
}
$expect = $maps[$Map].Md5
foreach ($f in $files) { if (Test-Path -LiteralPath (Join-Path $M ($f + '.before-voiceheard'))) { Fail "already installed ($f.before-voiceheard exists). Nothing was changed." } }
$live = (Get-FileHash -LiteralPath (Join-Path $M "$slot.zip") -Algorithm MD5).Hash
if (-not $live.StartsWith($expect)) { Fail "the installed $Map $slot.zip (md5 $live) is not the one this package was made against ($expect...). Nothing was changed." }
foreach ($f in $files) { if (-not (Test-Path -LiteralPath (Join-Path $SRC $f))) { Fail "package file missing: $f" } }
foreach ($f in $files) { Move-Item -LiteralPath (Join-Path $M $f) -Destination (Join-Path $M ($f + '.before-voiceheard')) }
foreach ($f in $files) { Copy-Item -LiteralPath (Join-Path $SRC $f) -Destination (Join-Path $M $f) }
Write-Host "voiceheard installed: $Map now has the Dead Men radio lines too. Undo: ""UNDO voiceheard2 $Map.bat""."
