# Private-match options page (re\pm_options.md B1), staged 2026-10-18. Copy of the script in build\pm_1018 (this one is the source).
#  1 overlay : KLExpansion\Overlay\Patch01.zip  <- Patch01.zip of this folder (mkoverlay.py with [Match] Enable=1: frontend.xml gains the window KLMatch
#              and an Options-menu button 'Match options'; everything else as the installed ini says, see READ ME in re\pm_options.md 8.5)
#  2 maps    : KLExpansion\Maps\maps.ini <- maps.ini of this folder (names on the 'Map vote' row; GUESS format of klpm.c)
#  3 ini     : KLHook.ini [Match] Enable=1 (the rows are answered only then; default stays 0 everywhere else)
#  4 hook    : NOT shipped here. The installed dinput8.dll must already contain klpm.c (the string KLMVote), or pass -Dll <path of a SHIP
#              dinput8.dll built from this commit>. Without klpm the new rows name options nobody answers: the script REFUSES then.
# Backups: <file>.before-pm1018 (first run only). -Undo puts every one back (maps.ini and the ini included; maps.ini is removed if it was new).
# Refuses while kl2.exe runs (0-thread zombies ignored).
param([switch]$Undo, [string]$Dll = '')
$ErrorActionPreference = 'Stop'
$g = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$tag = '.before-pm1018'
if (Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 }) { 'kl2.exe is running: close the game first'; exit 1 }
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
$ini = "$g\KLHook.ini"
$ovl = "$g\KLExpansion\Overlay\Patch01.zip"
$maps = "$g\KLExpansion\Maps\maps.ini"
$dll = "$g\dinput8.dll"
$plan = [ordered]@{}
$plan[$ovl] = "$here\Patch01.zip"
$plan[$maps] = "$here\maps.ini"
if ($Dll) { $plan[$dll] = $Dll }

if ($Undo) {
  foreach ($t in @($plan.Keys) + $ini + $dll) {
    if (Test-Path -LiteralPath "$t$tag") { Copy-Item -LiteralPath "$t$tag" $t -Force; "restored $t" }
    elseif ($t -eq $maps -and (Test-Path -LiteralPath "$t.new-pm1018")) { Remove-Item -LiteralPath $t -Force; Remove-Item -LiteralPath "$t.new-pm1018" -Force; "removed $t (it was new)" }
    else { "no backup for $t (left alone)" }
  }
  exit 0
}
$want = @{ $ovl = '7419c574c5bc4ee7171e350ebb8e628a'; $maps = '' }
foreach ($t in $plan.Keys) {
  $s = $plan[$t]
  if (-not (Test-Path -LiteralPath $s)) { "ABORT: missing $s"; exit 4 }
  if ($t -ne $maps -and -not (Test-Path -LiteralPath $t)) { "ABORT: missing installed $t"; exit 4 }
}
if ((md5 "$here\Patch01.zip") -ne $want[$ovl]) { "ABORT: Patch01.zip of this folder is not $($want[$ovl])"; exit 4 }
# the hook must answer KLMVote (the name is a plain ASCII string in klpm.c's table)
$hook = if ($Dll) { $Dll } else { $dll }
$hb = [IO.File]::ReadAllBytes($hook)
$hs = [Text.Encoding]::GetEncoding(28591).GetString($hb)
if (-not $hs.Contains('KLMVote')) { "ABORT: $hook has no klpm.c (no 'KLMVote'): the Match rows would be dead. Build a SHIP dll from this commit and pass -Dll <path>."; exit 6 }
foreach ($t in @($plan.Keys) + $ini) {
  if (Test-Path -LiteralPath "$t$tag") { continue }
  if (Test-Path -LiteralPath $t) { Copy-Item -LiteralPath $t "$t$tag" }
  elseif ($t -eq $maps) { Set-Content -LiteralPath "$t.new-pm1018" -Value 'maps.ini did not exist before pm1018' }
}
foreach ($t in $plan.Keys) {
  $s = $plan[$t]
  if ($t -eq $dll) { Copy-Item -LiteralPath $dll "$dll$tag" -ErrorAction SilentlyContinue }
  Copy-Item -LiteralPath $s $t -Force
  if ((md5 $t) -ne (md5 $s)) { "copy FAILED md5 check: $t (run with -Undo)"; exit 5 }
}
"files copied and md5-checked: $($plan.Count)"
$enc = [Text.Encoding]::GetEncoding(28591)
$raw = $enc.GetString([IO.File]::ReadAllBytes($ini))
$nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
function SetKey([string]$text, [string]$sec, [string]$key, [string]$val) {
  $m = [regex]::Match($text, "(?m)^\[$sec\][^\r\n]*\r?\n")
  if (-not $m.Success) {
    if (-not $text.EndsWith("`n")) { $text += $nl }
    return $text + "[$sec]$nl$key=$val$nl"
  }
  $start = $m.Index + $m.Length
  $next = [regex]::Match($text.Substring($start), "(?m)^\[")
  $end = if ($next.Success) { $start + $next.Index } else { $text.Length }
  $body = $text.Substring($start, $end - $start)
  $k = [regex]::Match($body, "(?m)^$key\s*=[^\r\n]*")
  if ($k.Success) { $body = $body.Substring(0, $k.Index) + "$key=$val" + $body.Substring($k.Index + $k.Length) }
  else { $body = "$key=$val$nl" + $body }
  return $text.Substring(0, $start) + $body + $text.Substring($end)
}
$raw = SetKey $raw 'Match' 'Enable' '1'
[IO.File]::WriteAllBytes($ini, $enc.GetBytes($raw))
'KLHook.ini: [Match] Enable=1'
'installed. Undo: UNDO match options.bat'
