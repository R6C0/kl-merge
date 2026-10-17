r"""stage_v2_final.py - ONE installer for the final v2 maps DM01B (slot F03) and DM06B (slot F02) (OFFLINE: reads the staged folders and the
game folder, writes ONLY <root>: MANIFEST.txt, install_v2final.ps1, 'INSTALL v2 maps final.bat', 'UNDO v2 maps final.bat').

    python stage_v2_final.py <root holding DM01B\ and DM06B\>

Installed per map (to KLExpansion\Maps\<id>): the archive, .WHD/.WAV, _LS.SND, F0x_Main_LS_* language files, .hti, KLWardrobe.ini, KLTalk.ini.
NOT installed: KLTalk.newhook.ini (only for the newer hook; copy by hand over KLTalk.ini) and the notes (json/txt/png).
Install: refuses while a kl2 with threads runs; staged md5 checked before and after each copy; an existing different file is first copied to
<file>.before-v2final (only if absent); a failed verify restores it. Undo restores the backups, and removes only files that were ABSENT before
(and unchanged since). The menu entry is NOT written here (tools/kl_expansion.py, EXTRA entries).
"""
import hashlib, os, re, sys

DD_MAPS = 'C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Maps'
TAG = 'v2final'
MAPS = ['DM01B', 'DM06B']
KEEP = re.compile(r'^F\d\d_Main(\.zip|\.WAV|\.WHD|\.hti|_LS\.SND|_LS_\w+\.(WAV|WHD))$|^(KLWardrobe|KLTalk)\.ini$')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


PS = r'''# v2 maps FINAL install (DM01B Hot Coffee II + DM06B Park II), staged 2026-10-18 by tools\stage_v2_final.py. Run ONLY when the owner is idle and kl2.exe is closed.
# Per file: staged md5 checked, a different existing target is backed up -> *.before-@TAG@ (only if absent), copied, md5 verified (failure restores).
# -Undo restores the backups and removes only files that were new (ABSENT) and are unchanged. Writes ONLY under KLExpansion\Maps\<id>.
param([switch]$Undo)
$ErrorActionPreference = 'Stop'
$maps = '@MAPS@'
$here = $PSScriptRoot
$g = Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 }
if ($g) { Write-Host 'kl2.exe is running (it has threads): close the game first'; exit 1 }
$rows = @(
@ROWS@
)
$bad = 0
foreach ($r in $rows) {
  $dir = Join-Path $maps $r.Id
  $t = Join-Path $dir $r.File
  $bk = "$t.before-@TAG@"
  $lbl = "$($r.Id)\$($r.File)"
  if ($Undo) {
    if (Test-Path $bk) { Copy-Item $bk $t -Force; Remove-Item $bk -Force; Write-Host "${lbl}: restored"; continue }
    if (-not (Test-Path $t)) { Write-Host "${lbl}: not there"; continue }
    if ($r.Was -ne 'ABSENT') { Write-Host "${lbl}: was there before this install, no backup needed - kept"; continue }
    if ((Get-FileHash $t -Algorithm MD5).Hash.ToLower() -ne $r.New) { Write-Host "${lbl}: changed since install - NOT removed"; continue }
    Remove-Item $t -Force; Write-Host "${lbl}: removed (it was new)"
    continue
  }
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
  $s = Join-Path (Join-Path $here $r.Id) $r.File
  $cur = if (Test-Path $t) { (Get-FileHash $t -Algorithm MD5).Hash.ToLower() } else { 'ABSENT' }
  if ($cur -eq $r.New) { Write-Host "${lbl}: already installed"; continue }
  if ((Get-FileHash $s -Algorithm MD5).Hash.ToLower() -ne $r.New) { Write-Host "${lbl}: SKIPPED - the staged file is not the manifest's"; $bad++; continue }
  if ((Test-Path $t) -and -not (Test-Path $bk)) { Copy-Item $t $bk }
  Copy-Item $s $t -Force
  if ((Get-FileHash $t -Algorithm MD5).Hash.ToLower() -ne $r.New) {
    Write-Host "${lbl}: VERIFY FAILED - undoing"
    if (Test-Path $bk) { Copy-Item $bk $t -Force } else { Remove-Item $t -Force }
    $bad++; continue }
  Write-Host "${lbl}: installed, md5 verified"
}
if ($Undo) {
  foreach ($id in @('@IDS@')) { $d = Join-Path $maps $id; if ((Test-Path $d) -and -not (Get-ChildItem $d)) { Remove-Item $d } }
  exit 0
}
if ($bad) { Write-Host "$bad problem(s)"; exit 2 } else { Write-Host 'all verified' }
'''


def main():
    root = os.path.abspath(sys.argv[1])
    lines = ['V2 MAPS FINAL MANIFEST (staged offline 2026-10-18; nothing installed)',
             'columns: map\\file | staged md5 | target-before md5 (ABSENT = not installed) | size', '']
    rows = []
    for mid in MAPS:
        d = os.path.join(root, mid)
        for f in sorted(os.listdir(d)):
            if not KEEP.match(f):
                continue
            t = DD_MAPS + '\\' + mid + '\\' + f
            before = md5(t) if os.path.isfile(t) else 'ABSENT'
            new = md5(os.path.join(d, f))
            lines.append('%s\\%s | %s | %s | %d' % (mid, f, new, before, os.path.getsize(os.path.join(d, f))))
            rows.append("  @{Id='%s'; File='%s'; New='%s'; Was='%s'}" % (mid, f, new, before))
    lines += ['', 'Target: %s\\<id>. Nothing else is written (no KLHook.ini, no PC_Def.str, no Patch01.zip, no stock file).' % DD_MAPS]
    open(os.path.join(root, 'MANIFEST.txt'), 'w').write('\n'.join(lines) + '\n')
    ps = PS.replace('@TAG@', TAG).replace('@MAPS@', DD_MAPS).replace('@IDS@', "','".join(MAPS)).replace('@ROWS@', ',\n'.join(rows))
    open(os.path.join(root, 'install_v2final.ps1'), 'w').write(ps)
    bat = '@echo off\r\npowershell -ExecutionPolicy Bypass -File "%%~dp0install_v2final.ps1"%s\r\npause\r\n'
    open(os.path.join(root, 'INSTALL v2 maps final.bat'), 'w').write(bat % '')
    open(os.path.join(root, 'UNDO v2 maps final.bat'), 'w').write(bat % ' -Undo')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
