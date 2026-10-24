# modopts_install.ps1 - installs / removes the KL Mod Options tool (2026-10-24). Source of the staged copy under <work>\build\modopts_1024.
#   -Mode install : copies kl_mod_options.py and "KL Mod Options.bat" into <Dog Days>\KLModOptions\ (a NEW folder; no game file and not
#                   KLHook.ini is touched). A file already there is first kept as <name>.before-1024modopts (once). md5 of every copied
#                   file is checked against modopts.md5 beside this script and again after the copy.
#   -Mode undo    : puts the .before-1024modopts files back, or removes what install added; removes the folder if it is empty.
#   Both refuse while kl2.exe runs. -GameDir overrides the Dog Days folder (rehearsal on a fake folder).
param(
    [ValidateSet('install','undo')][string]$Mode = 'install',
    [string]$GameDir = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
# a kl2.exe of THIS folder (or one whose path cannot be read) blocks; a kl2.exe elsewhere does not (rehearsal on a fake folder)
$gd = [System.IO.Path]::GetFullPath($GameDir).TrimEnd('\')
foreach ($p in @(Get-Process -Name kl2 -ErrorAction SilentlyContinue)) {
    $pp = $null; try { $pp = $p.MainModule.FileName } catch {}
    if (-not $pp -or $pp.StartsWith($gd, [System.StringComparison]::OrdinalIgnoreCase)) { Write-Host 'kl2.exe is running: close the game first.'; exit 1 }
}
if (-not (Test-Path -LiteralPath (Join-Path $GameDir 'kl2.exe')) -and -not (Test-Path -LiteralPath (Join-Path $GameDir 'KLHook.ini'))) { Write-Host "not a Dog Days folder: $GameDir"; exit 1 }
$dst = Join-Path $GameDir 'KLModOptions'
$files = @('kl_mod_options.py', 'KL Mod Options.bat')
function Md5($p) { (Get-FileHash -LiteralPath $p -Algorithm MD5).Hash }
$want = @{}
Get-Content -LiteralPath (Join-Path $here 'modopts.md5') | ForEach-Object { if ($_ -match '^([0-9A-Fa-f]{32})\s+\*?(.+)$') { $want[$Matches[2].Trim()] = $Matches[1].ToUpper() } }
if ($Mode -eq 'install') {
    foreach ($f in $files) {
        $s = Join-Path $here $f
        if (-not $want.ContainsKey($f)) { Write-Host "no md5 line for $f"; exit 1 }
        if ((Md5 $s) -ne $want[$f]) { Write-Host "staged $f does not match modopts.md5: rebuild the staging folder"; exit 1 }
    }
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    foreach ($f in $files) {
        $t = Join-Path $dst $f
        $bak = $t + '.before-1024modopts'
        if ((Test-Path -LiteralPath $t) -and -not (Test-Path -LiteralPath $bak) -and ((Md5 $t) -ne $want[$f])) { Copy-Item -LiteralPath $t -Destination $bak }
        Copy-Item -LiteralPath (Join-Path $here $f) -Destination $t -Force
        if ((Md5 $t) -ne $want[$f]) { Write-Host "copy of $f failed the md5 check"; exit 1 }
        Write-Host "installed $t  $($want[$f])"
    }
    Write-Host "Done. Start: $dst\KL Mod Options.bat (close the game first; saved changes apply at the next start)."
} else {
    foreach ($f in $files) {
        $t = Join-Path $dst $f
        $bak = $t + '.before-1024modopts'
        if (Test-Path -LiteralPath $bak) { Move-Item -LiteralPath $bak -Destination $t -Force; Write-Host "restored $f from its backup" }
        elseif (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force; Write-Host "removed $f" }
    }
    if ((Test-Path -LiteralPath $dst) -and -not (Get-ChildItem -LiteralPath $dst -Force)) { Remove-Item -LiteralPath $dst -Force; Write-Host 'removed the empty KLModOptions folder' }
    Write-Host 'KLHook.ini was not touched by this undo (its own backup is KLHook.ini.before-modoptions; the tool has a Restore button).'
}
