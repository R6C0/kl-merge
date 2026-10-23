# Payday 2 music switch for the owner's live KLHook.ini (2026-10-23).
# Owner: "all the payday 2 music makes it stutter, should be an option to switch it on if u have payday 2".
#   -Off (default): [Music] Enable=0 (the klmusic.c jukebox plays only Payday 2 soundtrack mp3s, in place from the PAYDAY 2 folder)
#                   and the three *_pd2_* clips leave the [Stinger] lists (the Dog Days stinger clips stay).
#   -On:            [Music] Enable=1 and the three clips come back. Needs Payday 2 installed (Folder/FolderB point into it).
# Retomoto Tower, Park II, The Vault and Last Call are in [Music] EngineMaps: they keep their own Dead Men music either way.
# Refuses while kl2.exe runs (the game's Mod settings page can rewrite the ini). Backup: KLHook.ini.before-pd2music-<stamp>.
param([switch]$On, [switch]$Off, [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days', [switch]$Rehearsal)
$ErrorActionPreference = 'Stop'
$ini = Join-Path $Game 'KLHook.ini'
if (-not (Test-Path $ini)) { Write-Host "no KLHook.ini in $Game"; exit 1 }
# -Rehearsal skips the running-game check: only for tests on a fake game folder
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { Write-Host 'Dog Days is running: close it first, then run this again.'; exit 1 }
$want = if ($On) { 1 } else { 0 }
# clip -> stinger list it belongs to (as staged by tools/kl_stinger.py)
$pd2 = [ordered]@{ 'Loud' = 'loud\loud_pd2_razormind.mp3'; 'Betray' = 'betray\betray_pd2_deathwish.mp3'; 'Reached' = 'reached\reached_pd2_music.mp3' }

$enc = [Text.Encoding]::Default
$text = [IO.File]::ReadAllText($ini, $enc)
$nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
$lines = $text -split "`r?`n"
$sec = ''; $setMusic = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    $l = $lines[$i]
    if ($l -match '^\[(.+)\]\s*$') { $sec = $Matches[1]; continue }
    if ($sec -eq 'Music' -and $l -match '^Enable\s*=') { $lines[$i] = "Enable=$want"; $setMusic = $true; continue }
    if ($sec -eq 'Stinger' -and $l -match '^(\w+)=(.*)$' -and $pd2.Contains($Matches[1])) {
        $key = $Matches[1]; $clip = $pd2[$key]
        $items = @($Matches[2] -split ';' | Where-Object { $_ -and $_ -ne $clip })
        if ($want -eq 1) { $items += $clip }
        $lines[$i] = "$key=" + ($items -join ';')
    }
}
if (-not $setMusic) { Write-Host 'no [Music] Enable line found: nothing changed'; exit 1 }
$new = $lines -join $nl
if ($new -eq $text) { Write-Host ("Payday 2 music is already " + $(if ($want) { 'ON' } else { 'OFF' })); exit 0 }
Copy-Item $ini ($ini + '.before-pd2music-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
[IO.File]::WriteAllText($ini, $new, $enc)
Write-Host ("Payday 2 music is now " + $(if ($want) { 'ON (needs Payday 2 installed)' } else { 'OFF' }) + '. Retomoto Tower keeps its own music either way.')
