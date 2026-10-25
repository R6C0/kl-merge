# kl_fedoutfit_all.ps1 - every map's fed-outfit stage in one go (2026-10-25; written by tools/kl_fedoutfit_stage.py).
#   powershell -ExecutionPolicy Bypass -File fedoutfit_all.ps1 [-Undo] [-DryRun] [-Game <folder>]   (-Rehearsal: scratch folder only)
# Each map is independent (its own manifest, md5 chain and backups); a map that is not at the md5 it was built for is SKIPPED with a line
# saying so, the others still go. Install order = the order in maps.txt; UNDO runs it backwards. Exit 0 only when every map is done / undone.
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$real = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
if ($Rehearsal -and $Game.TrimEnd('\') -ieq $real) { '-Rehearsal is only for a scratch copy, not the real game folder.'; exit 1 }
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
$maps = @(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'maps.txt') | Where-Object { $_.Trim() -ne '' })
if ($Undo) { [array]::Reverse($maps) }
$bad = 0
foreach ($m in $maps) {
  "=== $m"
  $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot "$m\fedoutfit.ps1"), '-Game', $Game)
  if ($Undo) { $a += '-Undo' }
  if ($DryRun) { $a += '-DryRun' }
  if ($Rehearsal) { $a += '-Rehearsal' }
  & powershell @a
  if ($LASTEXITCODE -ne 0) { $bad++; "  -> $m exit $LASTEXITCODE" }
}
''
if ($bad -eq 0) { 'all maps done' } else { "$bad map(s) not done (see the lines above); the rest went through" }
if (-not $Undo -and -not $DryRun) {
  $ini = Join-Path $Game 'KLHook.ini'
  $body = if (Test-Path -LiteralPath $ini) { [regex]::Match((Get-Content -LiteralPath $ini -Raw), '(?ims)^\[Fed\]\s*$(.*?)(?=^\[|\z)').Groups[1].Value } else { '' }
  if ($body -notmatch '(?im)^\s*Body\s*=\s*1') {
    'NOTE: KLHook.ini [Fed] has no Body=1: the [FedBody] sections are inert until it does (HOOK_PROPOSAL.md). Last Call needs no hook line.'
  }
}
exit $(if ($bad -eq 0) { 0 } else { 4 })
