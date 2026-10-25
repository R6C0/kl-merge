# pd2gun.ps1 - Payday 2 AKM on Dog Days' Rifle_Type81 (shop item 33, page II): model, textures and shot sound (tools/pd2_gun.py, 2026-10-25).
#   powershell -ExecutionPolicy Bypass -File pd2gun.ps1 [-Undo] [-DryRun] [-Rehearsal] [-Game <folder>]
# WHAT: three files of Scenes\Locations\F01\ (the test slot) are replaced by the build files next to this script:
#   F01_Main.zip (.prm .MAT .TEX .oct .gms .prp .SND change), F01_Main.WHD and F01_Main.WAV (three helicopter-gun records overwritten).
#   Each live file is renamed <name>.before-1025pd2gun (never overwritten, never deleted).
# TOGGLE: -Undo puts the three originals back (byte identical, read back). Nothing else is touched.
# SAFETY: refuses while kl2.exe runs; every live file's md5 must be exactly the one this was built on (or already the new one); read-back md5
#   after each copy; if a step fails, the files already swapped are put back. -DryRun changes nothing.
# -Rehearsal: runs dry-run, install, install again, undo dry-run, undo, undo again on a COPY of the three live files in a fake game
#   folder next to this script (reh\game); the real game folder is only read.
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal, [switch]$SkipRunCheck,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025pd2gun'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'pd2gun.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }

if ($Rehearsal) {
  $real = $Game
  $Game = Join-Path $PSScriptRoot 'reh\game'
  if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'reh')) { Remove-Item -LiteralPath (Join-Path $PSScriptRoot 'reh') -Recurse -Force }
  $d = Join-Path $Game $man.dir
  New-Item -ItemType Directory -Force -Path $d | Out-Null
  New-Item -ItemType File -Force -Path (Join-Path $Game 'kl2.exe') | Out-Null
  foreach ($e in $man.files) { Copy-Item -LiteralPath (Join-Path (Join-Path $real $man.dir) $e.f) -Destination (Join-Path $d $e.f) }
  $me = $MyInvocation.MyCommand.Path
  $bad = 0
  foreach ($step in @(@('-DryRun'), @(), @(), @('-Undo','-DryRun'), @('-Undo'), @('-Undo'))) {
    "--- rehearsal step: $($step -join ' ')"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $me @step -Game $Game -SkipRunCheck
    "    exit $LASTEXITCODE"
    if ($step.Count -eq 0 -and $LASTEXITCODE -ne 0) { }
  }
  "--- final md5 of the rehearsal copies (must equal 'old'):"
  foreach ($e in $man.files) {
    $m = md5 (Join-Path $d $e.f)
    if ($m -eq $e.old) { "    $($e.f) $m = old" } else { "    $($e.f) $m DIFFERENT"; $bad = 1 }
    if (Test-Path -LiteralPath (Join-Path $d ($e.f + $tag))) { '    backup still present'; $bad = 1 }
  }
  if ($bad) { 'REHEARSAL FAILED'; exit 1 } else { 'REHEARSAL OK'; exit 0 }
}

if (-not $SkipRunCheck) {
  if (Get-Process -Name kl2 -ErrorAction SilentlyContinue) { 'REFUSED: kl2.exe is running. Close the game first.'; exit 2 }
}
if (-not (Test-Path -LiteralPath (Join-Path $Game 'kl2.exe'))) { "REFUSED: no kl2.exe in $Game"; exit 2 }
$d = Join-Path $Game $man.dir
foreach ($e in $man.files) { if (-not (Test-Path -LiteralPath (Join-Path $d $e.f))) { "REFUSED: $($e.f) missing in $d"; exit 2 } }

# ---- plan (all checks before any change) ----
$plan = @()
foreach ($e in $man.files) {
  $live = Join-Path $d $e.f; $bak = $live + $tag; $src = Join-Path $PSScriptRoot $e.f
  $cur = md5 $live
  if ($Undo) {
    if ($cur -eq $e.old -and -not (Test-Path -LiteralPath $bak)) { "$($e.f): already the original, nothing to undo"; continue }
    if ($cur -ne $e.new) { "REFUSED: $($e.f) live md5 $cur is neither the installed build nor the original"; exit 3 }
    if (-not (Test-Path -LiteralPath $bak)) { "REFUSED: backup $bak missing"; exit 3 }
    if ((md5 $bak) -ne $e.old) { "REFUSED: backup $bak is not the original (md5 $(md5 $bak))"; exit 3 }
    $plan += ,@($e, $live, $bak, $src)
  } else {
    if ($cur -eq $e.new) { "$($e.f): already installed"; continue }
    if ($cur -ne $e.old) { "REFUSED: $($e.f) live md5 $cur is not the one this build was made on ($($e.old))"; exit 3 }
    if (Test-Path -LiteralPath $bak) { "REFUSED: backup $bak already exists"; exit 3 }
    if (-not (Test-Path -LiteralPath $src)) { "REFUSED: build file $src missing"; exit 3 }
    if ((md5 $src) -ne $e.new) { "REFUSED: build file $src md5 $(md5 $src) is not $($e.new)"; exit 3 }
    $plan += ,@($e, $live, $bak, $src)
  }
}
if ($plan.Count -eq 0) { 'nothing to do'; exit 0 }
if ($DryRun) { foreach ($p in $plan) { "DRYRUN would $(if ($Undo) {'restore'} else {'install'}) $($p[0].f)" }; 'DRYRUN ok, nothing changed'; exit 0 }

# ---- act, all or nothing ----
$done = @()
try {
  foreach ($p in $plan) {
    $e = $p[0]; $live = $p[1]; $bak = $p[2]; $src = $p[3]
    if ($Undo) {
      $keep = $live + '.undo-tmp'
      Rename-Item -LiteralPath $live -NewName (Split-Path $keep -Leaf)
      try { Rename-Item -LiteralPath $bak -NewName (Split-Path $live -Leaf) }
      catch { Rename-Item -LiteralPath $keep -NewName (Split-Path $live -Leaf); throw }
      if ((md5 $live) -ne $e.old) { throw "read-back of restored $($e.f) differs" }
      Remove-Item -LiteralPath $keep -Force
      $done += ,@('undo', $e, $live, $bak)
      "restored $($e.f)"
    } else {
      $tmp = $live + '.tmp'
      Copy-Item -LiteralPath $src -Destination $tmp -Force
      if ((md5 $tmp) -ne $e.new) { Remove-Item -LiteralPath $tmp -Force; throw "copy of $($e.f) failed md5" }
      Rename-Item -LiteralPath $live -NewName (Split-Path $bak -Leaf)
      Rename-Item -LiteralPath $tmp -NewName (Split-Path $live -Leaf)
      $done += ,@('inst', $e, $live, $bak)
      if ((md5 $live) -ne $e.new) { throw "read-back of $($e.f) differs" }
      "installed $($e.f)"
    }
  }
} catch {
  "FAILED: $_ - rolling back"
  if (-not $Undo) {
    foreach ($x in $done) {
      $live = $x[2]; $bak = $x[3]
      if (Test-Path -LiteralPath $bak) { Remove-Item -LiteralPath $live -Force -ErrorAction SilentlyContinue; Rename-Item -LiteralPath $bak -NewName (Split-Path $live -Leaf) }
    }
    foreach ($p in $plan) {   # the file that was mid-swap
      $live = $p[1]; $bak = $p[2]
      if ((Test-Path -LiteralPath $bak) -and -not (Test-Path -LiteralPath $live)) { Rename-Item -LiteralPath $bak -NewName (Split-Path $live -Leaf) }
      if (Test-Path -LiteralPath ($live + '.tmp')) { Remove-Item -LiteralPath ($live + '.tmp') -Force }
    }
  }
  exit 4
}
'OK'
exit 0
