# kl_fedoutfit.ps1 - one map's fed-outfit stage, 2026-10-25 (written by tools/kl_fedoutfit_stage.py; this file is copied next to fedoutfit.json).
#   powershell -ExecutionPolicy Bypass -File fedoutfit.ps1 [-Undo] [-DryRun] [-Game <folder>]   (-Rehearsal: scratch folder only, skips the kl2 check)
# WHAT: replaces the files listed in fedoutfit.json "files" of <Game>\KLExpansion\Maps\<map>\ (a KLJoin.ini whose [FedBody] names the body the
#   player's fed wears, or for Last Call the whole F01_Main.zip with a grafted police body). Nothing else is touched.
# SAFETY: refuses while kl2.exe runs; every file named in "pins" (the map's zip, whose .prm chunk count the [FedBody] Entries= was written for)
#   must have exactly the md5 in the manifest, and every file in "files" exactly its "old" md5 (or be absent when old is null), else SKIP and nothing
#   is changed; the old file is RENAMED to <name>.before-1025fedoutfit (never overwritten; absent -> a .absent marker); read-back md5 after the
#   copy, on failure the originals are put back. UNDO only when live == the new file; it renames the backup back (byte identical).
# Exit: 0 done / already done, 1 refused (game running, bad folder), 4 SKIP (md5 differs: another install in between, rebuild with
#   python tools/kl_fedoutfit_stage.py).
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025fedoutfit'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fedoutfit.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
$real = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
if ($Rehearsal -and $Game.TrimEnd('\') -ieq $real) { '-Rehearsal is only for a scratch copy, not the real game folder.'; exit 1 }
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$dir = Join-Path $Game ('KLExpansion\Maps\' + $man.m)
if (-not (Test-Path -LiteralPath $dir)) { "SKIP, $dir not installed"; exit 4 }
"map $($man.m): $dir"
# pins: the files this stage depends on but does not change
foreach ($p in @($man.pins)) {
  if ($null -eq $p) { continue }
  $pf = Join-Path $dir $p.n
  if (-not (Test-Path -LiteralPath $pf)) { "SKIP, pinned file $($p.n) is missing"; exit 4 }
  $h = md5 $pf
  if ($h -ne $p.md5) { "SKIP, $($p.n) is $h, this stage was built for $($p.md5) (the [FedBody] Entries= would be stale). Rebuild: python tools/kl_fedoutfit_stage.py"; exit 4 }
}
$files = @($man.files)
if ($Undo) {
  $todo = @()
  foreach ($f in $files) {
    $live = Join-Path $dir $f.n; $bak = "$live$tag"; $mark = "$bak.absent"
    $has = Test-Path -LiteralPath $live
    $cur = if ($has) { md5 $live } else { $null }
    if ($cur -eq $f.old -and -not (Test-Path -LiteralPath $bak) -and -not (Test-Path -LiteralPath $mark)) { "$($f.n): already undone"; continue }
    if ($cur -ne $f.new) { "SKIP, $($f.n) is $cur, not this stage's file (changed since?). Nothing changed."; exit 4 }
    if ($null -eq $f.old) { if (-not (Test-Path -LiteralPath $mark)) { "SKIP, no $($f.n)$tag.absent marker"; exit 4 } }
    else {
      if (-not (Test-Path -LiteralPath $bak)) { "SKIP, no backup $($f.n)$tag"; exit 4 }
      if ((md5 $bak) -ne $f.old) { "SKIP, backup $($f.n)$tag is not the expected original"; exit 4 }
    }
    $todo += $f
  }
  if ($DryRun) { "would restore $($todo.Count) file(s) (dry run)"; exit 0 }
  foreach ($f in $todo) {
    $live = Join-Path $dir $f.n; $bak = "$live$tag"; $mark = "$bak.absent"
    Remove-Item -LiteralPath $live -Force
    if ($null -eq $f.old) { Remove-Item -LiteralPath $mark -Force; "$($f.n): removed (there was none before)" }
    else {
      Rename-Item -LiteralPath $bak -NewName $f.n
      if ((md5 $live) -ne $f.old) { "FAILED, restored $($f.n) does not read back right!"; exit 4 }
      "$($f.n): original restored, read back ok"
    }
  }
  exit 0
}
$todo = @()
foreach ($f in $files) {
  $live = Join-Path $dir $f.n; $bak = "$live$tag"; $mark = "$bak.absent"
  $src = Join-Path $PSScriptRoot $f.n
  $has = Test-Path -LiteralPath $live
  $cur = if ($has) { md5 $live } else { $null }
  if ($cur -eq $f.new) { "$($f.n): already installed"; continue }
  if ($cur -ne $f.old) { "SKIP, $($f.n) is $cur, expected $($f.old). Another install in between? Nothing changed."; exit 4 }
  if ((Test-Path -LiteralPath $bak) -or (Test-Path -LiteralPath $mark)) { "SKIP, $($f.n)$tag already exists. Nothing changed."; exit 4 }
  if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $f.new) { "SKIP, build file $src missing or changed"; exit 4 }
  $todo += $f
}
if ($DryRun) { "would install $($todo.Count) file(s) (dry run)"; exit 0 }
foreach ($f in $todo) {
  $live = Join-Path $dir $f.n; $bak = "$live$tag"; $mark = "$bak.absent"; $tmp = "$live.tmp1025fo"
  $src = Join-Path $PSScriptRoot $f.n
  if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
  Copy-Item -LiteralPath $src -Destination $tmp
  if ((md5 $tmp) -ne $f.new) { "FAILED copying $($f.n), live untouched"; Remove-Item -LiteralPath $tmp -Force; exit 4 }
  if ($null -eq $f.old) { Set-Content -LiteralPath $mark -Value 'no file before 1025fedoutfit' -Encoding ASCII }
  else { Rename-Item -LiteralPath $live -NewName ($f.n + $tag) }
  $ok = $false
  try { Rename-Item -LiteralPath $tmp -NewName $f.n; $ok = (Test-Path -LiteralPath $live) } catch { $ok = $false }
  if (-not $ok) {
    if (Test-Path -LiteralPath $live) { Remove-Item -LiteralPath $live -Force }
    if ($null -eq $f.old) { Remove-Item -LiteralPath $mark -Force } else { Rename-Item -LiteralPath $bak -NewName $f.n }
    "FAILED swap of $($f.n), original put back"; exit 4
  }
  if ((md5 $live) -ne $f.new) { "FAILED read-back of $($f.n), run UNDO"; exit 4 }
  "$($f.n): installed (md5 $((md5 $live).Substring(0,8))), original kept as $($f.n)$tag"
}
