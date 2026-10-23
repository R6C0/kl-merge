# sound3_1023.ps1 - installs / removes sound pass 3 (Local + Panic one-shots, Payday 2 music by phase) for Dog Days.
#   powershell -ExecutionPolicy Bypass -File sound3_1023.ps1 -Dd "<DD folder>" [-Undo] [-SkipRunCheck]
# INSTALL: refuses while kl2.exe runs; copies local\ and panic\ (next to this script) to <DD>\KLExpansion\Ambience\ and md5-checks them;
#   saves KLHook.ini as KLHook.ini.before-sound3 (once; the undo's source of the old sections); then REPLACES, in KLHook.ini, every
#   [section] named in KLHook.sound3.patch.ini by the patch's version, except [Ambience] and [Music], which are merged key by key
#   (only the patch's keys change; Calm is unioned) (sections that do not exist yet are appended).
#   The hook dinput8.dll is NOT touched: this pass needs the sound3 hook (klhook\out_sound3_1023) for the Local / Panic / Assault keys;
#   an older hook ignores the new keys and plays as before.
# UNDO: puts back, section by section, the text those sections had in KLHook.ini.before-sound3 (sections that did not exist then are
#   removed), so any other edit made to KLHook.ini since stays; deletes <DD>\KLExpansion\Ambience\local and \panic.
param([Parameter(Mandatory = $true)][string]$Dd, [switch]$Undo, [switch]$SkipRunCheck)
$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
$ini = Join-Path $Dd 'KLHook.ini'; $bak = $ini + '.before-sound3'; $lib = Join-Path $Dd 'KLExpansion\Ambience'
$patch = Join-Path $src 'KLHook.sound3.patch.ini'
if (-not $SkipRunCheck -and (Get-Process -Name kl2 -ErrorAction SilentlyContinue)) { Write-Host 'kl2.exe is running - close the game first.'; exit 2 }
if (-not (Test-Path -LiteralPath $ini)) { Write-Host ('no KLHook.ini in "' + $Dd + '"'); exit 2 }
$enc = [System.Text.Encoding]::Default

# an ini as an ordered list of blocks: @{ name = 'Ambience.DM01' or $null (text before the first section); lines = [list] }
function Read-Blocks([string]$path) {
    $blocks = New-Object System.Collections.ArrayList; $cur = @{ name = $null; lines = (New-Object System.Collections.ArrayList) }
    foreach ($l in ([System.IO.File]::ReadAllText($path, $enc) -split "`r?`n")) {
        if ($l -match '^\[([^\]]+)\]\s*$') { [void]$blocks.Add($cur); $cur = @{ name = $Matches[1]; lines = (New-Object System.Collections.ArrayList) } }
        [void]$cur.lines.Add($l)          # the header line itself stays the first line of its block
    }
    [void]$blocks.Add($cur); return ,$blocks
}
function Write-Blocks($blocks, [string]$path) {
    $all = New-Object System.Collections.ArrayList
    foreach ($b in $blocks) { foreach ($l in $b.lines) { [void]$all.Add($l) } }
    [System.IO.File]::WriteAllText($path, (($all -join "`r`n").TrimEnd() + "`r`n"), $enc)
}
function Trim-Block($b) { while ($b.lines.Count -gt 1 -and $b.lines[$b.lines.Count - 1].Trim() -eq '') { $b.lines.RemoveAt($b.lines.Count - 1) }; [void]$b.lines.Add('') }
function Replace-Sections($live, $new) {      # $new: blocks whose names replace same-named blocks of $live (appended when absent)
    foreach ($nb in $new) {
        if ($null -eq $nb.name) { continue }
        $hit = $false
        for ($i = 0; $i -lt $live.Count; $i++) { if ($live[$i].name -eq $nb.name) { $live[$i] = $nb; $hit = $true; break } }
        if (-not $hit) { [void]$live.Add($nb) }
        Trim-Block $nb
    }
}

# [Ambience] and [Music] are MERGED key by key (only the patch's keys are touched), so edits made to those global sections since
# the patch was staged survive. Calm is unioned with the live list. Every other section is replaced whole.
$mergeNames = @('Ambience', 'Music')
function Key-Of([string]$l) { if ($l -match '^\s*;' -or $l -notmatch '=') { return $null }; return $l.Split('=')[0].Trim().ToLower() }
function Set-Key($blk, [string]$key, [string]$line) {       # replace the first line with that key, else append before trailing blanks
    for ($i = 1; $i -lt $blk.lines.Count; $i++) { if ((Key-Of $blk.lines[$i]) -eq $key) { $blk.lines[$i] = $line; return } }
    $j = $blk.lines.Count; while ($j -gt 1 -and $blk.lines[$j - 1].Trim() -eq '') { $j-- }
    $blk.lines.Insert($j, $line)
}
function Merge-Global($live, $pb) {
    $lb = $live | Where-Object { $_.name -eq $pb.name } | Select-Object -First 1
    if (-not $lb) { [void]$live.Add($pb); Trim-Block $pb; return }
    foreach ($l in $pb.lines) {
        $k = Key-Of $l; if (-not $k) { continue }
        if ($k -eq 'calm') {
            $cur = @(); foreach ($x in $lb.lines) { if ((Key-Of $x) -eq 'calm') { $cur = @($x.Substring($x.IndexOf('=') + 1).Split(';') | Where-Object { $_ }) } }
            $add = @($l.Substring($l.IndexOf('=') + 1).Split(';') | Where-Object { $_ -and ($cur -notcontains $_) })
            Set-Key $lb 'calm' ('Calm=' + ((@($cur) + $add) -join ';'))
        } else { Set-Key $lb $k $l }
    }
    Trim-Block $lb
}
function Unmerge-Global($live, $old, $pb) {       # put back, for the patch's keys only, the value the backup had (or remove the key)
    $lb = $live | Where-Object { $_.name -eq $pb.name } | Select-Object -First 1
    if (-not $lb) { return $false }
    $ob = $old | Where-Object { $_.name -eq $pb.name } | Select-Object -First 1
    foreach ($l in $pb.lines) {
        $k = Key-Of $l; if (-not $k) { continue }
        $oldLine = $null
        if ($ob) { foreach ($x in $ob.lines) { if ((Key-Of $x) -eq $k) { $oldLine = $x; break } } }
        if ($oldLine) { Set-Key $lb $k $oldLine }
        else { for ($i = 1; $i -lt $lb.lines.Count; $i++) { if ((Key-Of $lb.lines[$i]) -eq $k) { $lb.lines.RemoveAt($i); break } } }
    }
    return $true
}

if ($Undo) {
    if (-not (Test-Path -LiteralPath $bak)) { Write-Host 'no KLHook.ini.before-sound3 - the ini is left alone.' }
    elseif (-not (Test-Path -LiteralPath $patch)) { Write-Host 'KLHook.sound3.patch.ini is missing next to this script - the ini is left alone.' }
    else {
        $live = Read-Blocks $ini; $old = Read-Blocks $bak; $pat = Read-Blocks $patch; $n = 0
        foreach ($pb in $pat) {
            if ($null -eq $pb.name) { continue }
            if ($mergeNames -contains $pb.name) { if (Unmerge-Global $live $old $pb) { $n++ }; continue }
            $o = $old | Where-Object { $_.name -eq $pb.name } | Select-Object -First 1
            for ($i = 0; $i -lt $live.Count; $i++) {
                if ($live[$i].name -eq $pb.name) { if ($o) { $live[$i] = $o } else { $live.RemoveAt($i) }; $n++; break }
            }
        }
        Write-Blocks $live $ini; Write-Host ("KLHook.ini: $n section(s) put back; everything else left as it was.")
    }
    foreach ($g in 'local', 'panic') { $d = Join-Path $lib $g; if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force -Confirm:$false; Write-Host ('removed ' + $d) } }
    Write-Host 'undo done.'; exit 0
}

if (-not (Test-Path -LiteralPath $patch)) { Write-Host 'KLHook.sound3.patch.ini is missing next to this script.'; exit 2 }
# 1. the clips
$bad = 0; $cnt = 0
foreach ($g in 'local', 'panic') {
    $sd = Join-Path $src $g; if (-not (Test-Path -LiteralPath $sd)) { Write-Host ('missing in the package: ' + $g); exit 2 }
    $dd2 = Join-Path $lib $g; New-Item -ItemType Directory -Force -Path $dd2 | Out-Null
    foreach ($f in Get-ChildItem -LiteralPath $sd -Filter *.mp3) {
        $t = Join-Path $dd2 $f.Name; Copy-Item -LiteralPath $f.FullName -Destination $t -Force; $cnt++
        if ((Get-FileHash -LiteralPath $t -Algorithm MD5).Hash -ne (Get-FileHash -LiteralPath $f.FullName -Algorithm MD5).Hash) { Write-Host ('COPY MISMATCH ' + $t); $bad++ }
    }
}
if ($bad) { Write-Host "$bad file(s) did not copy right - KLHook.ini NOT changed."; exit 3 }
Write-Host "$cnt clip(s) copied to $lib"
# 2. the ini
if (-not (Test-Path -LiteralPath $bak)) { Copy-Item -LiteralPath $ini -Destination $bak; Write-Host ('saved ' + $bak) }
$live = Read-Blocks $ini; $pat = Read-Blocks $patch
$whole = New-Object System.Collections.ArrayList
foreach ($pb in $pat) { if ($null -eq $pb.name) { continue }; if ($mergeNames -contains $pb.name) { Merge-Global $live $pb } else { [void]$whole.Add($pb) } }
Replace-Sections $live $whole
Write-Blocks $live $ini
$names = ($pat | Where-Object { $_.name } | ForEach-Object { $_.name }).Count
Write-Host "KLHook.ini: $names section(s) replaced / added. Install done. Use the sound3 hook (klhook\out_sound3_1023) to hear the new groups."
exit 0
