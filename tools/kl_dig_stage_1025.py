"""kl_dig_stage_1025.py - md5-chained INSTALL / UNDO for the Dig (DM07, M07_A on host F07 -> slot F06, page 3).

  python tools/kl_dig_stage_1025.py stage <stage dir containing KLExpansion\\> <out dir> [--str <PC_Def.str>] [--rehearse <scratch>]

Writes into <out dir>: dig.json (md5 and size of every file), dig.ps1, INSTALL DM07 dig.bat, UNDO DM07 dig.bat,
INSTALL DM07 music (PC_Def.str).bat, UNDO DM07 music (PC_Def.str).bat.

Maps step: copies KLExpansion\\Maps\\DM07\\* and KLExpansion\\BuildInfo\\DM07\\* into the game. Every file is NEW (absent before); a file that
is present with another md5 is SKIPPED (never overwritten). -Undo removes only the files whose md5 is the manifest's.
Music step (-Str): PC_Def.str is replaced only when its md5 is the pinned base; the original is MOVED to PC_Def.str.before-1025dig.
Both refuse while kl2.exe runs (not with -Rehearsal). -Rehearsal -Game <scratch> works on a scratch game folder, -DryRun writes nothing.
The menu entry ([Redirect.3] F06=DM07, [Page.3], overlay, picture) is NOT written here: kl_expansion.py build/install owns KLHook.ini.
"""
import hashlib, json, os, shutil, subprocess, sys

TAG = '.before-1025dig'
SUB = ('KLExpansion\\Maps\\DM07', 'KLExpansion\\BuildInfo\\DM07')


def md5f(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


PS1 = r'''# dig.ps1 - The Dig (DM07, M07_A on F07 -> slot F06, menu page 3), 2026-10-25 (tools/kl_dig_stage_1025.py).
#   Maps step: copies NEW files only (never overwrites). -Undo removes only files whose md5 is dig.json's.
#   -Str: the music stream PC_Def.str, replaced only when its md5 is the pinned base; the original is moved to PC_Def.str.before-1025dig.
param([string]$Game = "C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days", [switch]$Undo, [switch]$DryRun, [switch]$Rehearsal, [switch]$Str)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$man = Get-Content -Raw (Join-Path $here "dig.json") | ConvertFrom-Json
$tag = $man.tag
function Md5($p) { (Get-FileHash -Algorithm MD5 -LiteralPath $p).Hash.ToLower() }
if (-not $Rehearsal) {
    if (Get-Process -Name kl2 -ErrorAction SilentlyContinue) { Write-Host "kl2.exe is running: close the game first."; exit 1 }
}
if (-not (Test-Path (Join-Path $Game "kl2.exe"))) { Write-Host "no kl2.exe in $Game"; exit 1 }
if ($Str) {
    $live = Join-Path $Game "PC_Def.str"; $bak = $live + $tag; $s = $man.str
    if (-not $s) { Write-Host "this stage has no PC_Def.str"; exit 1 }
    if (-not $Undo) {
        if (-not (Test-Path $live)) { Write-Host "SKIP, no PC_Def.str in the game folder"; exit 0 }
        $m = Md5 $live
        if ($m -eq $s.new) { Write-Host "already installed (PC_Def.str $($s.new))"; exit 0 }
        if ($m -ne $s.old) { Write-Host "SKIP, live md5 $m is not the pinned $($s.old)"; exit 0 }
        if (Test-Path $bak) { Write-Host "SKIP, $bak already exists"; exit 0 }
        if ($DryRun) { Write-Host "would install PC_Def.str $($s.old) -> $($s.new)"; exit 0 }
        Move-Item -LiteralPath $live -Destination $bak
        Copy-Item -LiteralPath (Join-Path $here "PC_Def.str") -Destination $live
        if ((Md5 $live) -ne $s.new) { Remove-Item -LiteralPath $live -Force; Move-Item -LiteralPath $bak -Destination $live; Write-Host "copy failed, original put back"; exit 1 }
        Write-Host "installed PC_Def.str $($s.new) (original: $bak)"
    } else {
        if (-not (Test-Path $bak)) { Write-Host "already undone (no $bak)"; exit 0 }
        if ($DryRun) { Write-Host "would undo PC_Def.str"; exit 0 }
        if (Test-Path $live) { Remove-Item -LiteralPath $live -Force }
        Move-Item -LiteralPath $bak -Destination $live
        Write-Host "undone, PC_Def.str is $(Md5 $live)"
    }
    exit 0
}
$did = 0; $skip = 0; $gone = 0
foreach ($f in $man.files) {
    $dst = Join-Path $Game $f.p
    if (-not $Undo) {
        if (Test-Path -LiteralPath $dst) {
            if ((Get-Item -LiteralPath $dst).Length -eq $f.n -and (Md5 $dst) -eq $f.m) { continue }
            Write-Host "SKIP, $($f.p) exists with another md5 (not overwritten)"; $skip++; continue
        }
        if ($DryRun) { $did++; continue }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
        Copy-Item -LiteralPath (Join-Path $here $f.p) -Destination $dst
        if ((Md5 $dst) -ne $f.m) { Remove-Item -LiteralPath $dst -Force; Write-Host "copy of $($f.p) failed"; exit 1 }
        $did++
    } else {
        if (-not (Test-Path -LiteralPath $dst)) { continue }
        if ((Md5 $dst) -ne $f.m) { Write-Host "KEEP, $($f.p) changed since the install"; $skip++; continue }
        if ($DryRun) { $did++; continue }
        Remove-Item -LiteralPath $dst -Force; $did++
    }
}
if (-not $Undo) {
    if ($DryRun) { Write-Host "would install $did files ($skip skipped)" }
    elseif ($did -eq 0 -and $skip -eq 0) { Write-Host "already installed" }
    else { Write-Host "installed $did files ($skip skipped). Menu entry: python tools/kl_expansion.py install" }
} else {
    if ($DryRun) { Write-Host "would remove $did files ($skip kept)" }
    elseif ($did -eq 0 -and $skip -eq 0) { Write-Host "already undone" }
    else {
        foreach ($d in ($man.dirs | Sort-Object -Descending)) { $p = Join-Path $Game $d; if ((Test-Path $p) -and -not (Get-ChildItem -Force $p)) { Remove-Item $p -Force } }
        Write-Host "undone, $did files removed ($skip kept)"
    }
}
'''

BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dig.ps1" {arg}\r\npause\r\n'


def run_ps(d, game, *flags):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'dig.ps1'), '-Game', game, '-Rehearsal'] + list(flags)
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(src, out, strp=None, game_live=None, scratch=None, log=print):
    os.makedirs(out, exist_ok=True)
    files, dirs = [], set()
    for sub in SUB:
        base = os.path.join(src, sub)
        for root, _d, fs in os.walk(base):
            for f in fs:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, src)
                dst = os.path.join(out, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst):
                    try:
                        os.link(full, dst)
                    except OSError:
                        shutil.copy2(full, dst)
                files.append(dict(p=rel, n=os.path.getsize(full), m=md5f(full)))
        dirs.add(sub)
    man = dict(tag=TAG, files=sorted(files, key=lambda x: x['p']), dirs=sorted(dirs))
    if strp:
        if not game_live:
            raise SystemExit('--str needs --live <installed PC_Def.str> for the pinned base md5')
        dst = os.path.join(out, 'PC_Def.str')
        if not os.path.exists(dst):
            try:
                os.link(strp, dst)
            except OSError:
                shutil.copy2(strp, dst)
        man['str'] = dict(old=md5f(game_live), new=md5f(strp), size=os.path.getsize(strp))
    with open(os.path.join(out, 'dig.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'dig.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL DM07 dig.bat', ''), ('UNDO DM07 dig.bat', '-Undo'),
                    ('INSTALL DM07 music (PC_Def.str).bat', '-Str'), ('UNDO DM07 music (PC_Def.str).bat', '-Str -Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    log('staged %s: %d files, %.1f MB%s' % (out, len(files), sum(f['n'] for f in files) / 1e6, ', str ' + man['str']['new'][:8] if strp else ''))
    if scratch:
        rehearse(out, man, scratch, log)
    return man


def rehearse(d, man, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game_dm07')
    shutil.rmtree(g, ignore_errors=True)
    os.makedirs(g)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    tree = lambda: sorted(os.path.relpath(os.path.join(r, f), g) for r, _d, fs in os.walk(g) for f in fs)
    t = run_ps(d, g, '-DryRun'); log(t.strip()); assert 'would install' in t and tree() == ['kl2.exe'], t
    t = run_ps(d, g); log(t.strip()); assert 'installed %d files' % len(man['files']) in t, t
    for f in man['files']:
        assert md5f(os.path.join(g, f['p'])) == f['m'], f['p']
    assert 'already installed' in run_ps(d, g)
    t = run_ps(d, g, '-Undo'); log(t.strip())
    assert tree() == ['kl2.exe'] and not os.path.exists(os.path.join(g, 'KLExpansion', 'Maps', 'DM07')), tree()[:5]
    assert 'already undone' in run_ps(d, g, '-Undo')
    run_ps(d, g)
    victim = os.path.join(g, man['files'][0]['p'])
    with open(victim, 'ab') as fh:
        fh.write(b'x')
    t = run_ps(d, g); log(t.strip()); assert 'SKIP' in t and 'another md5' in t, t
    t = run_ps(d, g, '-Undo'); log(t.strip()); assert 'KEEP' in t and os.path.exists(victim), t
    shutil.rmtree(g, ignore_errors=True)
    if 'str' in man:
        os.makedirs(g)
        open(os.path.join(g, 'kl2.exe'), 'wb').close()
        live = os.path.join(g, 'PC_Def.str')
        t = run_ps(d, g, '-Str', '-DryRun'); assert 'SKIP, no PC_Def' in t, t
        # a stand-in base cannot match the pinned md5, so the wrong-base refusal is what is rehearsed here; the happy path is run by the caller with the real base
        with open(live, 'wb') as fh:
            fh.write(b'not the pinned file')
        t = run_ps(d, g, '-Str'); log(t.strip()); assert 'SKIP, live md5' in t and open(live, 'rb').read() == b'not the pinned file', t
        shutil.rmtree(g, ignore_errors=True)
    log('rehearsal ok (dry run, install, md5 per file, idempotent, undo leaves only kl2.exe, undo twice, changed file skipped / kept)')


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if len(a) >= 3 and a[0] == 'stage':
        stage(a[1], a[2], opt('--str'), opt('--live'), opt('--rehearse'))
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
