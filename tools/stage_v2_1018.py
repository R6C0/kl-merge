"""stage_v2_1018.py - stage one V2 map for the owner's double-click install (OFFLINE: reads the build folder and the game folder, writes ONLY
under <out>, never the game folder).

    python stage_v2_1018.py <DM01B|DM06B> <built folder (holds F01_Main.zip ...)> <out folder>

<out> gets Maps\\<id>\\ (the files, written under the map's own slot name by kl_expansion.adopt, as v2_1017/DM01B_fx did), MANIFEST.txt,
install_<id>.ps1 (-Undo puts the backups back), 'INSTALL <id> v2.bat' and 'UNDO <id> v2.bat'.
The install: refuses while a kl2 with threads runs; per file md5 of the staged copy is checked before and after the copy; an existing different
file is first copied to <file>.before-v21018 (only if no such backup exists); a failed verify restores it. The menu entry is NOT written here
(tools/kl_expansion.py, EXTRA entry <id>), as for v2_1017.
"""
import hashlib, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_expansion

DD_MAPS = 'C:\\Steam\\steamapps\\common\\Kane & Lynch 2 - Dog Days\\KLExpansion\\Maps'
TAG = 'v21018'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


PS = r'''# v2_1018 install of map @ID@ ("@TITLE@"), staged 2026-10-18 by tools\stage_v2_1018.py. Run ONLY when the owner is idle and kl2.exe is closed.
# Per file: the staged copy's md5 is checked, an existing different target is backed up -> *.before-@TAG@ (only if that backup is absent), the file is
# copied and its md5 verified (a failed verify restores the backup, or removes the new file). -Undo restores the backups / removes files that were new.
# Writes ONLY under KLExpansion\Maps\@ID@. It does NOT add the menu entry (tools\kl_expansion.py, EXTRA entry @ID@).
param([switch]$Undo)
$ErrorActionPreference = 'Stop'
$maps = '@MAPS@'
$here = $PSScriptRoot
$g = Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 }
if ($g) { Write-Host 'kl2.exe is running (it has threads): close the game first'; exit 1 }
$dir = Join-Path $maps '@ID@'
$rows = @(
@ROWS@
)
$bad = 0
if ($Undo) {
  foreach ($r in $rows) {
    $t = Join-Path $dir $r.File
    $bk = "$t.before-@TAG@"
    if (Test-Path $bk) { Copy-Item $bk $t -Force; Remove-Item $bk -Force; Write-Host "$($r.File): restored"; continue }
    if (-not (Test-Path $t)) { Write-Host "$($r.File): not there"; continue }
    if ((Get-FileHash $t -Algorithm MD5).Hash.ToLower() -ne $r.New) { Write-Host "$($r.File): changed since install - NOT removed"; continue }
    Remove-Item $t -Force; Write-Host "$($r.File): removed (it was new)"
  }
  if ((Test-Path $dir) -and -not (Get-ChildItem $dir)) { Remove-Item $dir }
  exit 0
}
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
foreach ($r in $rows) {
  $t = Join-Path $dir $r.File
  $s = Join-Path (Join-Path $here 'Maps\@ID@') $r.File
  $cur = if (Test-Path $t) { (Get-FileHash $t -Algorithm MD5).Hash.ToLower() } else { 'ABSENT' }
  if ($cur -eq $r.New) { Write-Host "$($r.File): already installed"; continue }
  if ((Get-FileHash $s -Algorithm MD5).Hash.ToLower() -ne $r.New) { Write-Host "$($r.File): SKIPPED - the staged file is not the manifest's"; $bad++; continue }
  $bk = "$t.before-@TAG@"
  if ((Test-Path $t) -and -not (Test-Path $bk)) { Copy-Item $t $bk }
  Copy-Item $s $t -Force
  if ((Get-FileHash $t -Algorithm MD5).Hash.ToLower() -ne $r.New) {
    Write-Host "$($r.File): VERIFY FAILED - undoing"
    if (Test-Path $bk) { Copy-Item $bk $t -Force } else { Remove-Item $t -Force }
    $bad++; continue }
  Write-Host "$($r.File): installed, md5 verified"
}
if ($bad) { Write-Host "$bad problem(s)"; exit 2 } else { Write-Host 'all verified' }
'''


def main():
    mid, built, out = sys.argv[1], sys.argv[2], sys.argv[3]
    m = next(x for x in kl_expansion.EXTRA if x['id'] == mid)
    scratch = os.path.join(out, '_scratch')
    shutil.rmtree(scratch, ignore_errors=True)
    kl_expansion.adopt(m, built, os.path.join(scratch, 'Maps', mid), os.path.join(scratch, 'BuildInfo', mid))
    d = os.path.join(out, 'Maps', mid)
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(os.path.join(scratch, 'Maps', mid), d)
    shutil.rmtree(scratch, ignore_errors=True)
    lines = ['V2_1018 %s MANIFEST (staged offline 2026-10-18; nothing installed)' % mid,
             'map %s = "%s": slot %s (page %s). Built from %s.' % (mid, m['title'], m['slot'], m['page'], built),
             'columns: file | staged md5 | target-before md5 (ABSENT = not installed) | size', '']
    rows = []
    for f in sorted(os.listdir(d)):
        t = DD_MAPS + '\\' + mid + '\\' + f
        before = md5(t) if os.path.isfile(t) else 'ABSENT'
        new = md5(os.path.join(d, f))
        lines.append('%s | %s | %s | %d' % (f, new, before, os.path.getsize(os.path.join(d, f))))
        rows.append("  @{File='%s'; New='%s'}" % (f, new))
    lines += ['', 'Target folder: %s\\%s. Nothing else is written (no KLHook.ini, no Patch01.zip, no stock file, no other map).' % (DD_MAPS, mid)]
    open(os.path.join(out, 'MANIFEST.txt'), 'w').write('\n'.join(lines) + '\n')
    ps = PS.replace('@ID@', mid).replace('@TITLE@', m['title']).replace('@TAG@', TAG).replace('@MAPS@', DD_MAPS).replace('@ROWS@', ',\n'.join(rows))
    open(os.path.join(out, 'install_%s.ps1' % mid), 'w').write(ps)
    bat = '@echo off\r\npowershell -ExecutionPolicy Bypass -File "%%~dp0install_%s.ps1"%s\r\npause\r\n'
    open(os.path.join(out, 'INSTALL %s v2.bat' % mid), 'w').write(bat % (mid, ''))
    open(os.path.join(out, 'UNDO %s v2.bat' % mid), 'w').write(bat % (mid, ' -Undo'))
    print('\n'.join(lines[:3]), '\n', len(rows), 'files staged in', d)


if __name__ == '__main__':
    main()
