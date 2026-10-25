"""kl_dm01fb_stage.py - build and stage the 2026-10-25 DM01 'owner feedback' round (kl_dm01fb_1025.py) with an md5-chained INSTALL/UNDO.

    python kl_dm01fb_stage.py <stage A zip (11c874cb...)> <out folder> [scratch folder]

Chain: stage A (doors2 + dm01squads, md5 11c874cb) -> cars (new lane) -> kick squad -> wall extinguishers -> door-kick sound; the result replaces the live
DM01 build c0e7b8ee (doors2 10359141 -> dm01squads 11c874cb -> dm01cars c0e7b8ee).  FOUR files of KLExpansion\\Maps\\DM01 change together
(F01_Main.zip, .WHD, .WAV, _LS.SND: the sound fix appends wave objects to DM01's own bank), each backed up with the suffix .before-1025dm01fb.
The installer refuses while kl2.exe runs, when ANY live file md5 is not the pinned old one, or when a backup already exists; it copies to .tmp files
first, swaps, reads every file back, and puts everything back on a failure.  UNDO only when all four live files are exactly the new ones.
The real game folder is read for the live bank files (never written); the rehearsal works on a scratch copy only."""
import hashlib, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TAG = '.before-1025dm01fb'
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
LIVE = os.path.join(DD, 'KLExpansion', 'Maps', 'DM01')
FILES = ['F01_Main.zip', 'F01_Main.WHD', 'F01_Main.WAV', 'F01_Main_LS.SND']
OLD_STAGE_A = '11c874cb'
OLD_LIVE_ZIP = 'c0e7b8ee'


def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


PS1 = r'''# dm01fb.ps1 - DM01 Hot Coffee, owner feedback round 2026-10-25 (tools/kl_dm01fb_1025.py): door-kick sound, extinguishers on the wall,
#   a cop squad that kicks a door, police cars that arrive from the road and stop by the van.
#   powershell -ExecutionPolicy Bypass -File dm01fb.ps1 [-Undo] [-DryRun] [-Game <folder>]   (-Rehearsal: scratch folders only, skips the kl2 check)
# WHAT: FOUR files of KLExpansion\Maps\DM01 are replaced by the ones next to this script: F01_Main.zip, F01_Main.WHD, F01_Main.WAV, F01_Main_LS.SND
#   (the sound fix appends the door-kick waves to DM01's own bank). Each live file is renamed <name>.before-1025dm01fb first (never overwritten).
#   CHAINED: the live zip must be the dm01cars build c0e7b8ee (doors2 -> dm01squads -> dm01cars installed before).
# SAFETY: refuses while kl2.exe runs; every live file's md5 must be exactly the one in dm01fb.json "old" (or all already the new ones);
#   copies to .tmp1025 first and checks them; read-back of all four after the swap; on a failure everything is put back;
#   UNDO only when all four live files are the new build and all four backups are the originals, then renames the backups back (byte identical).
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025dm01fb'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dm01fb.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
$real = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
if ($Rehearsal -and $Game.TrimEnd('\') -ieq $real) { '-Rehearsal is only for a scratch copy, not the real game folder.'; exit 1 }
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$dir = Join-Path $Game 'KLExpansion\Maps\DM01'
"target: $dir"
$fs = @($man.files)
foreach ($f in $fs) { if (-not (Test-Path -LiteralPath (Join-Path $dir $f.n))) { "SKIP, $dir\$($f.n) not installed"; exit 4 } }
$cur = @{}; foreach ($f in $fs) { $cur[$f.n] = md5 (Join-Path $dir $f.n) }
$allNew = $true; $allOld = $true
foreach ($f in $fs) { if ($cur[$f.n] -ne $f.new) { $allNew = $false }; if ($cur[$f.n] -ne $f.old) { $allOld = $false } }
if ($Undo) {
  $baks = @($fs | Where-Object { Test-Path -LiteralPath (Join-Path $dir ($_.n + $tag)) })
  if ($baks.Count -eq 0) { if ($allOld) { 'already undone'; exit 0 } else { 'SKIP, no backups and the live files are not the originals'; exit 4 } }
  if ($baks.Count -ne $fs.Count) { 'SKIP, some backups are missing. Nothing changed.'; exit 4 }
  if (-not $allNew) { 'SKIP, a live file is not this build (changed since?). Backups left in place.'; exit 4 }
  foreach ($f in $fs) { if ((md5 (Join-Path $dir ($f.n + $tag))) -ne $f.old) { "SKIP, backup $($f.n)$tag is not the expected original"; exit 4 } }
  if ($DryRun) { 'would restore the four originals (dry run)'; exit 0 }
  foreach ($f in $fs) {
    $p = Join-Path $dir $f.n
    Remove-Item -LiteralPath $p -Force
    Rename-Item -LiteralPath ($p + $tag) -NewName $f.n
    if ((md5 $p) -ne $f.old) { "FAILED, restored $($f.n) does not read back right!"; exit 4 }
  }
  'originals restored, read back ok'; exit 0
}
if ($allNew) { 'already installed'; exit 0 }
foreach ($f in $fs) { if ($cur[$f.n] -ne $f.old) { "SKIP, live $($f.n) md5 is $($cur[$f.n]), expected $($f.old). Another install in between? Not changed."; exit 4 } }
foreach ($f in $fs) { if (Test-Path -LiteralPath (Join-Path $dir ($f.n + $tag))) { "SKIP, $($f.n)$tag already exists. Not changed."; exit 4 } }
foreach ($f in $fs) { $s = Join-Path $PSScriptRoot $f.n; if (-not (Test-Path -LiteralPath $s) -or (md5 $s) -ne $f.new) { "SKIP, build file $s missing or changed"; exit 4 } }
if ($DryRun) { 'would install (dry run)'; exit 0 }
foreach ($f in $fs) { $t = Join-Path $dir ($f.n + '.tmp1025'); if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force } }
try {
  foreach ($f in $fs) {
    $t = Join-Path $dir ($f.n + '.tmp1025')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $f.n) -Destination $t
    if ((md5 $t) -ne $f.new) { throw "copy of $($f.n) does not read back" }
  }
} catch {
  foreach ($f in $fs) { $t = Join-Path $dir ($f.n + '.tmp1025'); if (Test-Path -LiteralPath $t) { Remove-Item -LiteralPath $t -Force } }
  "FAILED before touching the game files: $_"; exit 4
}
try {
  foreach ($f in $fs) {
    $p = Join-Path $dir $f.n
    Rename-Item -LiteralPath $p -NewName ($f.n + $tag)
    Rename-Item -LiteralPath ($p + '.tmp1025') -NewName $f.n
  }
} catch {
  foreach ($f in $fs) {
    $p = Join-Path $dir $f.n; $b = $p + $tag
    if (Test-Path -LiteralPath $b) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }; Rename-Item -LiteralPath $b -NewName $f.n }
    if (Test-Path -LiteralPath ($p + '.tmp1025')) { Remove-Item -LiteralPath ($p + '.tmp1025') -Force }
  }
  "FAILED swap, originals put back: $_"; exit 4
}
foreach ($f in $fs) { if ((md5 (Join-Path $dir $f.n)) -ne $f.new) { "FAILED read-back of $($f.n), run UNDO"; exit 4 } }
"installed (zip $((md5 (Join-Path $dir 'F01_Main.zip')).Substring(0,8))), originals kept as *$tag"
'''
BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dm01fb.ps1" {arg}\r\npause\r\n'


def run(d, game, undo=False, dry=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'dm01fb.ps1'), '-Game', game, '-Rehearsal']
    if undo:
        a.append('-Undo')
    if dry:
        a.append('-DryRun')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def build(stage_a, work, log=print):
    """stage A zip -> work/p5/{4 files}; every pass writes its own file so a failure leaves the earlier ones."""
    import kl_dm01fb_1025 as FB
    assert md5f(stage_a).startswith(OLD_STAGE_A), md5f(stage_a)
    os.makedirs(work, exist_ok=True)
    p = lambda n: os.path.join(work, n)
    rep = {}
    rep['cars'] = FB.cars(stage_a, p('p1_cars.zip'), log)
    rep['kick'] = FB.kick_squad(p('p1_cars.zip'), p('p3_kick.zip'), log)
    rep['ext'] = FB.ext_wall(p('p3_kick.zip'), p('p4_ext.zip'), log)
    os.makedirs(p('p5'), exist_ok=True)
    rep['sound'] = FB.sound(p('p4_ext.zip'), p('p5/F01_Main.zip'), LIVE, log)
    return p('p5'), rep


def stage(p5, out, scratch=None, live=LIVE, log=print):
    os.makedirs(out, exist_ok=True)
    files = []
    for n in FILES:
        shutil.copyfile(os.path.join(p5, n), os.path.join(out, n))
        files.append(dict(n=n, old=md5f(os.path.join(live, n)), new=md5f(os.path.join(out, n))))
    assert files[0]['old'].startswith(OLD_LIVE_ZIP), 'the live zip is %s, not the dm01cars build %s' % (files[0]['old'], OLD_LIVE_ZIP)
    man = dict(m='DM01', tag=TAG, files=files, chain='doors2 10359141 -> dm01squads 11c874cb -> dm01cars c0e7b8ee -> dm01fb')
    json.dump(man, open(os.path.join(out, 'dm01fb.json'), 'w'), indent=1)
    with open(os.path.join(out, 'dm01fb.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL dm01fb.bat', ''), ('UNDO dm01fb.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    for f in files:
        log('  %-16s %s -> %s' % (f['n'], f['old'][:8], f['new'][:8]))
    rehearse(out, man, live, scratch or os.path.join(out, 'scratch'), log)
    return man


def rehearse(d, man, live_src, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'game_DM01')
    mp = os.path.join(g, 'KLExpansion', 'Maps', 'DM01')
    assert os.path.abspath(mp).lower().startswith(scratch.lower() + os.sep)
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(mp)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    fs = man['files']
    for f in fs:
        shutil.copyfile(os.path.join(live_src, f['n']), os.path.join(mp, f['n']))
    L = lambda n: os.path.join(mp, n)
    state = lambda key: all(md5f(L(f['n'])) == f[key] for f in fs)
    t = run(d, g, dry=True); assert 'would install' in t and state('old'), t
    t = run(d, g); log(t.strip()); assert 'installed' in t and state('new'), t
    assert all(md5f(L(f['n']) + TAG) == f['old'] for f in fs)
    assert 'already installed' in run(d, g)
    t = run(d, g, undo=True, dry=True); assert 'would restore' in t and state('new'), t
    t = run(d, g, undo=True); log(t.strip())
    assert state('old') and not any(os.path.exists(L(f['n']) + TAG) for f in fs), 'undo not byte identical'
    assert 'already undone' in run(d, g, undo=True)
    run(d, g); assert state('new')
    run(d, g, undo=True); assert state('old')
    with open(L('F01_Main.zip'), 'ab') as fh:                                  # a changed live zip: refused, nothing moved
        fh.write(b'x')
    t = run(d, g); assert 'SKIP, live F01_Main.zip md5' in t and not any(os.path.exists(L(f['n']) + TAG) for f in fs), t
    shutil.copyfile(os.path.join(live_src, 'F01_Main.zip'), L('F01_Main.zip'))
    with open(L('F01_Main.WHD'), 'ab') as fh:                                  # a changed bank file: refused too
        fh.write(b'x')
    t = run(d, g); assert 'SKIP, live F01_Main.WHD md5' in t and not any(os.path.exists(L(f['n']) + TAG) for f in fs), t
    shutil.copyfile(os.path.join(live_src, 'F01_Main.WHD'), L('F01_Main.WHD'))
    run(d, g); assert state('new')                                              # install; then a half-undone state is refused
    os.remove(L('F01_Main.WAV' + TAG))
    t = run(d, g, undo=True); assert 'SKIP, some backups are missing' in t and state('new'), t
    shutil.rmtree(g, ignore_errors=True)
    log('  rehearsal ok (dry run, install, idempotent, undo dry run, undo byte-identical, undo twice, reinstall, wrong zip md5 refused, wrong bank md5 refused, missing backup refused)')


if __name__ == '__main__':
    if len(sys.argv) in (3, 4):
        w = os.path.join(sys.argv[2], 'work')
        p5, rep = build(sys.argv[1], w)
        json.dump(rep, open(os.path.join(sys.argv[2], 'build_report.json'), 'w'), indent=1, default=str)
        stage(p5, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print(__doc__)
