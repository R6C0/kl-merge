# pack_release.ps1 - assemble the tester download (KLMerge_package.zip) from a 'kl_release.py make' output folder.
#
#   powershell -ExecutionPolicy Bypass -File tools\launcher\pack_release.ps1 -Out <make outdir> [-Zip <path>] [-Exe <KLMergeSetup.exe>]
#
# Takes from <Out>:  manifest.json, patches\*.klp          (the package: our code/config as literal patches + binary patches
#                                                            whose SOURCE is the player's own stock DD / DM / PD2 files)
# Adds:              tools\kl_release.py                    (the installer half; needs python + zstandard on the tester's PC)
#                    tools\launcher\ (as launcher\)          KLMergeLauncher.ps1, KL Dead Men Rising.exe (exe\build.bat), README_TESTERS.md,
#                                                            KL Dead Men Rising Setup.bat
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
# TWO zips (GitHub refuses one release asset of 2 GiB or more): part 1 = everything but the second half of the patches,
# part 2 = those patches + package_part2.txt (the Setup bat checks for it). Both unpack into the same package\ folder.
$stage2 = $stage + '_2'
# every refuse below and any error remove BOTH staging folders (each holds ~1 GB of patches in %TEMP%)
$cleanup = { foreach ($d in @($stage, $stage2)) { if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force } } }
trap { & $cleanup; Write-Host ('FAILED: ' + $_); exit 1 }
New-Item -ItemType Directory -Path (Join-Path $stage2 'patches') -Force | Out-Null
# only the patches the manifest names: patches\ also keeps superseded ones (a bots zip re-made against its main zip, older makes)
New-Item -ItemType Directory -Path (Join-Path $stage 'patches') | Out-Null
$pnames = @($man.entries | ForEach-Object { $_.patch } | Sort-Object -Unique)
$psize = @{}
foreach ($pn in $pnames) {
    $pp = Join-Path (Join-Path $Out 'patches') $pn
    if (-not (Test-Path -LiteralPath $pp)) { Write-Host "REFUSED: manifest names $pn, not in $Out\patches"; & $cleanup; exit 1 }
    $psize[$pn] = (Get-Item -LiteralPath $pp).Length
}
# part 2 takes patches from the end of the sorted list until it holds half of the patch bytes
$half = (($psize.Values | Measure-Object -Sum).Sum) / 2
$two = @{}; $acc = 0
for ($i = $pnames.Count - 1; $i -ge 0 -and $acc -lt $half; $i--) { $two[$pnames[$i]] = $true; $acc += $psize[$pnames[$i]] }
foreach ($pn in $pnames) {
    $dst = if ($two.ContainsKey($pn)) { Join-Path $stage2 'patches' } else { Join-Path $stage 'patches' }
    Copy-Item -LiteralPath (Join-Path (Join-Path $Out 'patches') $pn) -Destination $dst
}
Set-Content -LiteralPath (Join-Path $stage2 'package_part2.txt') -Value ('KL: Dead Men Rising package v' + $man.version + ', part 2 of 2: ' + $two.Count + ' patches (unpack beside part 1)') -Encoding ASCII
Copy-Item -LiteralPath (Join-Path $tools 'kl_release.py') -Destination $stage
foreach ($f in @('KLMergeLauncher.ps1', 'KL Dead Men Rising.exe', 'README_TESTERS.md', 'KL Dead Men Rising Setup.bat')) {
    $p = Join-Path $here $f
    if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination (Join-Path $stage 'launcher') }
    elseif ($f -like '*.exe') { Write-Host 'note: "KL Dead Men Rising.exe" is missing (run tools\launcher\exe\build.bat) - the Setup then starts the launcher through a minimized powershell' }
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
if (Test-Path -LiteralPath (Join-Path $stage 'launcher\music')) { Write-Host 'REFUSED: launcher\music\ in the staging folder'; & $cleanup; exit 1 }
if ($Exe) {
    if (-not (Test-Path -LiteralPath $Exe)) { Write-Host "REFUSED: $Exe not found"; & $cleanup; exit 1 }
    Copy-Item -LiteralPath $Exe -Destination (Join-Path $stage 'KLMergeSetup.exe')
}

# belt and braces: nothing with a game extension may be in the zip (the patches are .klp, our code .py/.ps1/.bat/.md/.json/.exe)
$bad = @(Get-ChildItem -LiteralPath $stage, $stage2 -Recurse -File | Where-Object { $_.Extension -match '^\.(zip|prp|gms|tex|prm|mat|fxc|str|wav|whd|snd|loc|anm|buf|oct|hvk|sgd|rmi|rmc|sgp|hrd|zgf|sup|mdmp|dmp|dll|ini)$' })
if ($bad.Count -gt 0) { Write-Host 'REFUSED: game-like files in the staging folder:'; $bad | ForEach-Object { Write-Host ('  ' + $_.FullName) }; & $cleanup; exit 1 }

# part n: <Zip> and <Zip minus .zip>_2.zip; upload names KLMerge_package.zip and KLMerge_package_2.zip (the Setup bat's
# RELEASE_URL is .../releases/latest/download/KLMerge_package.zip, part 2 the same link with _2.zip)
$Zip2 = $Zip -replace '\.zip$', '_2.zip'
$uploads = @()
# no file of an earlier pack may survive a refused one: a stale part beside a new part would be a mixed release
foreach ($old in @($Zip, $Zip2, (Join-Path (Split-Path -Parent $Zip) 'KLMerge_package.zip'), (Join-Path (Split-Path -Parent $Zip) 'KLMerge_package_2.zip'))) {
    foreach ($o in @($old, ($old + '.sha1'))) { if (Test-Path -LiteralPath $o) { Remove-Item -LiteralPath $o } }
}
foreach ($p in @(@{ S = $stage; Z = $Zip; U = 'KLMerge_package.zip' }, @{ S = $stage2; Z = $Zip2; U = 'KLMerge_package_2.zip' })) {
    $count = @(Get-ChildItem -LiteralPath $p.S -Recurse -File).Count
    $bytes = (Get-ChildItem -LiteralPath $p.S -Recurse -File | Measure-Object -Property Length -Sum).Sum
    Write-Host ('staging: {0} files, {1:N1} MB -> {2}' -f $count, ($bytes / 1MB), $p.Z)
    if (Test-Path -LiteralPath $p.Z) { Remove-Item -LiteralPath $p.Z }
    Compress-Archive -Path (Join-Path $p.S '*') -DestinationPath $p.Z -CompressionLevel Optimal
    $sha = (Get-FileHash -LiteralPath $p.Z -Algorithm SHA1).Hash.ToLower()
    Set-Content -LiteralPath ($p.Z + '.sha1') -Value ($sha + '  ' + (Split-Path -Leaf $p.Z)) -Encoding ASCII
    $len = (Get-Item -LiteralPath $p.Z).Length
    Write-Host ('zip: {0:N1} MB, sha1 {1}' -f ($len / 1MB), $sha)
    # GitHub refuses a release asset of 2 GiB or more
    if ($len -ge 2147483648) { Write-Host ('REFUSED: ' + $p.Z + ' is 2 GiB or more - GitHub would refuse this release asset'); & $cleanup; exit 1 }
    # the upload name: hard link beside the versioned zip (same bytes, no extra disk), a copy when linking fails
    $upload = Join-Path (Split-Path -Parent $p.Z) $p.U
    if ($upload -ne $p.Z) {
        if (Test-Path -LiteralPath $upload) { Remove-Item -LiteralPath $upload }
        try { New-Item -ItemType HardLink -Path $upload -Target $p.Z -ErrorAction Stop | Out-Null }
        catch { Copy-Item -LiteralPath $p.Z -Destination $upload }
        Set-Content -LiteralPath ($upload + '.sha1') -Value ($sha + '  ' + $p.U) -Encoding ASCII
    }
    $uploads += $upload
}
& $cleanup
foreach ($u in $uploads) { Write-Host ('upload: ' + $u + ' (+ .sha1)') }
Write-Host 'Upload BOTH files (+ their .sha1) to the same release (OWNER_RELEASE_STEPS.md section 4).'
Write-Host 'Hand out "KL Dead Men Rising Setup.bat" only; its RELEASE_URL never changes.'
