# voiceheard 1023: put the DM01 voice data with the radio twins (2418 KLVoice leaves instead of 1162) into <DD>\KLExpansion\Maps\DM01.
# The zip in out\DM01 is the voiceheard build with Menu/online.xml, F01_Main.TEX and the Russian .LOC taken from the zip installed
# on 2026-10-23 (md5 82b33bf8aa4a...), so it differs from that zip only in 7 .LOC files and F01_Main.SND.
# Install: moves the five live files to *.before-voiceheard, copies the new ones. Undo (-Undo): puts the *.before-voiceheard files back.
param([string]$Root = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Undo)
$ErrorActionPreference = 'Stop'
$M = Join-Path $Root 'KLExpansion\Maps\DM01'
$SRC = Join-Path $PSScriptRoot 'out\DM01'
$files = 'F01_Main.zip', 'F01_Main.WAV', 'F01_Main.WHD', 'F01_Main_LS.SND', 'KLTalk.ini'
function Fail($m) { Write-Host "FAILED: $m"; exit 1 }
if (Get-Process kl2 -ErrorAction SilentlyContinue) { Fail 'close the game first (kl2.exe is running). Nothing was changed.' }
if (-not (Test-Path -LiteralPath $M)) { Fail "no map folder $M" }
if ($Undo) {
    foreach ($f in $files) { if (-not (Test-Path -LiteralPath (Join-Path $M ($f + '.before-voiceheard')))) { Fail "no backup $f.before-voiceheard. Nothing was changed." } }
    foreach ($f in $files) {
        Remove-Item -LiteralPath (Join-Path $M $f) -Force
        Move-Item -LiteralPath (Join-Path $M ($f + '.before-voiceheard')) -Destination (Join-Path $M $f)
    }
    Write-Host 'voiceheard undone: DM01 has its earlier voice data again.'; exit 0
}
$expect = '82B33BF8AA4A'
foreach ($f in $files) { if (Test-Path -LiteralPath (Join-Path $M ($f + '.before-voiceheard'))) { Fail "already installed ($f.before-voiceheard exists). Nothing was changed." } }
$live = (Get-FileHash -LiteralPath (Join-Path $M 'F01_Main.zip') -Algorithm MD5).Hash
if (-not $live.StartsWith($expect)) { Fail "the installed DM01 F01_Main.zip (md5 $live) is not the one this package was made against ($expect...). Nothing was changed." }
foreach ($f in $files) { if (-not (Test-Path -LiteralPath (Join-Path $SRC $f))) { Fail "package file missing: $f" } }
foreach ($f in $files) { Move-Item -LiteralPath (Join-Path $M $f) -Destination (Join-Path $M ($f + '.before-voiceheard')) }
foreach ($f in $files) { Copy-Item -LiteralPath (Join-Path $SRC $f) -Destination (Join-Path $M $f) }
Write-Host 'voiceheard installed: DM01 now has the Dead Men radio lines too. Undo: "UNDO voiceheard 1023.bat".'
