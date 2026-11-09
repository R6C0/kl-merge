# pack_release.ps1 - assemble the tester download (KLMerge_package.zip) from a 'kl_release.py make' output folder.
#
#   powershell -ExecutionPolicy Bypass -File tools\launcher\pack_release.ps1 -Out <make outdir> [-Zip <path>] [-Exe <KLMergeSetup.exe>]
#
# Takes from <Out>:  manifest.json, patches\*.klp          (the package: our code/config as literal patches + binary patches
#                                                            whose SOURCE is the player's own stock DD / DM / PD2 files)
# Adds:              tools\kl_release.py                    (the installer half; needs python + zstandard on the tester's PC)
#                    tools\launcher\ (as launcher\)          KLMergeLauncher.ps1, KLMerge.bat, README_TESTERS.md, KLMerge Setup.bat
#                    tools\kl_launcher_music.py (as launcher\)  reads the launcher's music clip from the TESTER'S OWN Dead Men file
#                    tools\launcher\bin\kl_oggdec.exe (as launcher\bin\)  decodes the Ogg Vorbis menu loop (stb_vorbis, public domain)
#                    tools\launcher\bg\*.jpg (as launcher\bg\)  Josh's two background screenshots (dead_men.jpg, dog_days.jpg)
#                    -Exe <KLMergeSetup.exe>  (optional)     the frozen installer; with it the tester needs no Python at all
# Leaves out (maker only): parts\, _snap\, sha1cache.json, *.tmp*.   Never any game file: the make output holds none,
# and this script copies only the names above - it refuses to zip anything with a game extension as a belt and braces.
# NEVER packed: tools\launcher\music\ (the decoded Dead Men clip of THIS PC: a game asset; every tester makes their own).
#
# UNTESTED on Windows when written (cloud, Linux): syntax by inspection + launcher_test.py's parser pass only.
param(
    [Parameter(Mandatory = $true)][string]$Out,
    [string]$Zip = '',
    [string]$Exe = ''
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path          # tools\launcher
$tools = Split-Path -Parent $here                                 # tools
if (-not (Test-Path -LiteralPath (Join-Path $Out 'manifest.json'))) { Write-Host "REFUSED: no manifest.json in $Out (run kl_release.py make first)"; exit 1 }
if (-not (Test-Path -LiteralPath (Join-Path $Out 'patches'))) { Write-Host "REFUSED: no patches\ folder in $Out"; exit 1 }
$man = Get-Content -LiteralPath (Join-Path $Out 'manifest.json') -Raw | ConvertFrom-Json
if (-not $Zip) { $Zip = Join-Path (Split-Path -Parent $Out) ('KLMerge_package_v' + $man.version + '.zip') }

$stage = Join-Path $env:TEMP ('klmerge_pack_' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $stage | Out-Null
New-Item -ItemType Directory -Path (Join-Path $stage 'launcher') | Out-Null
Copy-Item -LiteralPath (Join-Path $Out 'manifest.json') -Destination $stage
Copy-Item -LiteralPath (Join-Path $Out 'patches') -Destination (Join-Path $stage 'patches') -Recurse
Copy-Item -LiteralPath (Join-Path $tools 'kl_release.py') -Destination $stage
foreach ($f in @('KLMergeLauncher.ps1', 'KLMerge.bat', 'README_TESTERS.md', 'KLMerge Setup.bat')) {
    $p = Join-Path $here $f
    if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination (Join-Path $stage 'launcher') }
}
# the launcher's music tool (reads the clip from the tester's own Dead Men PC_Def.str at run time; no audio travels)
Copy-Item -LiteralPath (Join-Path $tools 'kl_launcher_music.py') -Destination (Join-Path $stage 'launcher')
# its pure-Python Vorbis fallback (slow, ~7 s, but no exe): used when kl_oggdec.exe and ffmpeg are both missing or fail
Copy-Item -LiteralPath (Join-Path $tools 'kl_pyvorbis.py') -Destination (Join-Path $stage 'launcher')
# its pure-Python Bink Audio decoder (the default music = the riff of the tester's own Movies\Trailer.bik; testers have no ffmpeg)
$pybink = Join-Path $tools 'kl_pybink.py'
if (Test-Path -LiteralPath $pybink) { Copy-Item -LiteralPath $pybink -Destination (Join-Path $stage 'launcher') }
else { Write-Host 'note: tools\kl_pybink.py is missing - without ffmpeg the launcher music is MenuLoop_01 alone (no trailer riff)' }
# the Ogg Vorbis decoder the music tool uses (public-domain stb_vorbis; built by tools\launcher\oggdec\build.bat; no game data)
$oggdec = Join-Path $here 'bin\kl_oggdec.exe'
if (Test-Path -LiteralPath $oggdec) {
    New-Item -ItemType Directory -Path (Join-Path $stage 'launcher\bin') | Out-Null
    Copy-Item -LiteralPath $oggdec -Destination (Join-Path $stage 'launcher\bin')
} else { Write-Host 'note: tools\launcher\bin\kl_oggdec.exe is missing (run tools\launcher\oggdec\build.bat) - the launcher music then falls back to ffmpeg or the slow kl_pyvorbis.py' }
# the background pictures: only launcher\bg\*.jpg, nothing else of bg\
$bg = Join-Path $here 'bg'
$jpgs = @()
if (Test-Path -LiteralPath $bg) { $jpgs = @(Get-ChildItem -LiteralPath $bg -Filter '*.jpg' -File -ErrorAction SilentlyContinue) }
if ($jpgs.Count -gt 0) {
    New-Item -ItemType Directory -Path (Join-Path $stage 'launcher\bg') | Out-Null
    foreach ($j in $jpgs) { Copy-Item -LiteralPath $j.FullName -Destination (Join-Path $stage 'launcher\bg') }
    foreach ($want in @('dead_men.jpg', 'dog_days.jpg')) {
        if (-not (Test-Path -LiteralPath (Join-Path $bg $want))) { Write-Host ('note: launcher\bg\' + $want + ' is missing - the launcher draws its fallback for that side') }
    }
} else {
    Write-Host 'note: no tools\launcher\bg\*.jpg - the launcher draws its procedural background (OWNER_RELEASE_STEPS.md section 2b)'
}
# launcher\music\ is NEVER staged (a decoded game clip); the extension check below would refuse a .wav anyway
if (Test-Path -LiteralPath (Join-Path $stage 'launcher\music')) { Write-Host 'REFUSED: launcher\music\ in the staging folder'; exit 1 }
if ($Exe) {
    if (-not (Test-Path -LiteralPath $Exe)) { Write-Host "REFUSED: $Exe not found"; exit 1 }
    Copy-Item -LiteralPath $Exe -Destination (Join-Path $stage 'KLMergeSetup.exe')
}

# belt and braces: nothing with a game extension may be in the zip (the patches are .klp, our code .py/.ps1/.bat/.md/.json/.exe)
$bad = @(Get-ChildItem -LiteralPath $stage -Recurse -File | Where-Object { $_.Extension -match '^\.(zip|prp|gms|tex|prm|mat|fxc|str|wav|whd|snd|loc|anm|buf|oct|hvk|sgd|rmi|rmc|sgp|hrd|zgf|sup|mdmp|dmp|dll|ini)$' })
if ($bad.Count -gt 0) { Write-Host 'REFUSED: game-like files in the staging folder:'; $bad | ForEach-Object { Write-Host ('  ' + $_.FullName) }; exit 1 }

$count = @(Get-ChildItem -LiteralPath $stage -Recurse -File).Count
$bytes = (Get-ChildItem -LiteralPath $stage -Recurse -File | Measure-Object -Property Length -Sum).Sum
Write-Host ('staging: {0} files, {1:N1} MB -> {2}' -f $count, ($bytes / 1MB), $Zip)
if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $Zip -CompressionLevel Optimal
$sha = (Get-FileHash -LiteralPath $Zip -Algorithm SHA1).Hash.ToLower()
Set-Content -LiteralPath ($Zip + '.sha1') -Value ($sha + '  ' + (Split-Path -Leaf $Zip)) -Encoding ASCII
Write-Host ('zip: {0:N1} MB, sha1 {1}' -f ((Get-Item -LiteralPath $Zip).Length / 1MB), $sha)
Remove-Item -LiteralPath $stage -Recurse -Force
Write-Host 'Upload the zip, set RELEASE_URL in "KLMerge Setup.bat" to its download link, and hand out that .bat only.'
