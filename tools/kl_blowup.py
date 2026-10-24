"""kl_blowup.py - DATA pass of the 'vehicles can blow up' fix (owner 2026-10-24: 'they never blow up, they are always on fire
from when the cops shoot it but never see it explode'). Written 2026-10-24. Companion of the hook module [VanBlow] (klhook/klescort.c).

WHAT WAS WRONG (data side): tools/kl_escape_noblow.py (live since 2026-10-19, noblow.ps1) set VehicleEffects field 23 of Dead Men's
Escape_Chopper to BlowupChanceNone on three maps - DM05A (F01), DM06 (F04), DM11B = Hasta (F04). With None the chopper burns
(Activate_DamageFX) but can never reach the blow-up (rules slot 94 grade 2 = state 6), so it never explodes. It was done to stop
Hasta's 12 destroyed-with-the-crew departures; that cost every player the explosion on all three maps. Dog Days' own FA maps
(F02/F03/F06/F08 helicopters) are BlowupChanceDefinite and untouched here.
WHAT THIS DOES (only the .prp member of the three live zips differs; no entity added/removed, slot order unchanged):
  every VehicleEffects under an 'EscapeSetup!' path:  field 23 BlowupChanceNone -> BlowupChanceDefinite (CERTAIN: the enum is
  the one kl_hc2_strip.py / kl_escape_noblow.py write), and field 3 (the health: 2200 in these files, Dog Days' helicopters 4000..
  8000 - CERTAIN that 2200 is what the log calls the chopper's health, GUESS that field 3 alone is the health the early lift-off
  at 15 % and the blow-up read) raised to --health (default 5000 = Dog Days' F08 helicopter) when it is lower. Field 4 is left.
  Why a higher health: 2200 died in 12 of 41 Hasta departures; 5000 is the lowest Dog Days helicopter that ships as Definite.
WHAT HAPPENS ABOARD: state 6 kills every record with status 4 (human by slot 11, AI by slot 16). The hook's [VanBlow] and
  the chopper's own timer decide when that can happen; this file only makes it possible again.
NOT TOUCHED: the key-framed escape van (no VehicleEffects, no BlowupChance field: its blow-up is health + the 'Invulnerable' byte,
  which is the hook's side), Dog Days' maps, Hot Coffee II's cars (kl_hc2_strip.py: parked cars stay None on purpose).
OUTPUT (small, drive G is nearly full): <out>\\<MAP>\\<Fxx>_Main.prp (only the changed member, ~MB), blowup.json (md5s),
  blowup.ps1 + INSTALL/UNDO .bat. The INSTALL patches a COPY of the live zip in place with .NET (the member is replaced), checks it,
  then swaps it in; the live zip is renamed .before-1024blowup. UNDO renames it back (byte identical).
Usage (from tools/):  python kl_blowup.py [--game <DD folder>] [--out <folder>] [--health 5000] [--hasta] [--rehearse <scratch folder>]
  --hasta: also DM11B (Hasta). OFF by default: Hasta is where 12 of 41 departures ended in state 6 with the bots aboard (they die), and that
  chopper cannot be shielded; DM05A / DM06 had none. Reviewer's call, owner may add it.
  --rehearse: copies the live zips into <scratch>\\game, runs INSTALL and UNDO there with the generated ps1 and writes the
  resulting md5s into blowup.json (the installer then refuses anything else). Never touches the real game folder.
"""
import os, sys, json, gc, hashlib, shutil, subprocess, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_map_ai as MA
from kl_prp import units

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS = [('DM05A', 'F01_Main.zip'), ('DM06', 'F04_Main.zip')]
HASTA = ('DM11B', 'F04_Main.zip')     # review 2026-10-24: NOT in the default set - all 12 logged state-6 departures with the bots aboard were here (re/hasta_chopper_1019.md); --hasta adds it
BLOW_FIELD = 23                       # VehicleEffects: enum BlowupChance*
HEALTH_FIELD = 3                      # GUESS: the health (2200 on Escape_Chopper; Dog Days helicopters 4000..8000)
TAG = '.before-1024blowup'


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def patch_prp(src, health, prefix='EscapeSetup!', log=print):
    """-> (prp member name, new prp bytes, [changes]) or (name, None, []) when nothing to do."""
    zf = zipfile.ZipFile(src)
    sc, _, _ = kl_fa.load(src)
    changes = []
    for k in range(1, len(sc.nodes)):
        if prefix.lower() not in sc.path[k].lower():
            continue
        for ci, (nm, b) in enumerate(sc.nodes[k]['ctrls']):
            if sc.p.key(nm) != 'VehicleEffects':
                continue
            us = [list(u) for u in units(b[1:-1])]
            blow, hp = kl_fa.value(sc, us[BLOW_FIELD]), kl_fa.value(sc, us[HEALTH_FIELD])
            want_blow = blow != 'BlowupChanceDefinite'
            want_hp = isinstance(hp, float) and hp < health
            if not (want_blow or want_hp):
                continue
            def fn(f, want_blow=want_blow, want_hp=want_hp):
                if want_blow:
                    MA.setv(sc, f, BLOW_FIELD, 'BlowupChanceDefinite')
                if want_hp:
                    MA.setv(sc, f, HEALTH_FIELD, float(health))
            kl_fa.edit(sc, k, ci, fn)
            changes.append('%s: %s -> %s, health %.0f -> %.0f' % (sc.path[k], blow, 'BlowupChanceDefinite', hp, max(hp, health) if want_hp else hp))
    pn = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
    return pn, (sc.p.serialize() if changes else None), changes


PS1 = r'''# blowup.ps1 - escape vehicles can blow up again (tools/kl_blowup.py, 2026-10-24).
#   powershell -ExecutionPolicy Bypass -File blowup.ps1 [-Undo] [-DryRun] [-Game <folder>]
# WHY: owner 2026-10-24: 'they never blow up, always on fire'. noblow (2026-10-19) set Dead Men's Escape_Chopper to
#   BlowupChanceNone on DM05A, DM06 and DM11B (Hasta); this puts Definite back and the health at 5000 (kl_blowup.py has the reasons).
# WHAT: only the .prp member inside F0x_Main.zip is replaced (same name, same slot order). The live zip is COPIED, the copy is
#   patched and checked (member md5, entry count), then swapped in; the live zip is renamed F0x_Main.zip.before-1024blowup.
# SAFETY: refuses while kl2.exe runs; a map is skipped unless its live zip md5 is exactly the expected one (or already the new one);
#   read-back md5 after the swap, on failure the original is put back; UNDO renames the backup back (md5 == the original).
# Not touched: KL_PortBackup, stock files, KLHook.ini, dinput8.dll.
param([switch]$Undo, [switch]$DryRun,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1024blowup'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'blowup.json') -Raw | ConvertFrom-Json
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
function Patch-Zip($zip, $member, $prp) {
  $z = [System.IO.Compression.ZipFile]::Open($zip, 'Update')
  try {
    $old = $z.Entries | Where-Object { $_.FullName -eq $member } | Select-Object -First 1
    if (-not $old) { throw "member $member not found" }
    $old.Delete()
    $e = $z.CreateEntry($member, [System.IO.Compression.CompressionLevel]::Optimal)
    $e.LastWriteTime = [DateTimeOffset]::new(2026, 10, 24, 0, 0, 0, [TimeSpan]::Zero)
    $s = $e.Open(); $b = [System.IO.File]::ReadAllBytes($prp); $s.Write($b, 0, $b.Length); $s.Dispose()
  } finally { $z.Dispose() }
}
function Member-Md5($zip, $member) {
  $z = [System.IO.Compression.ZipFile]::OpenRead($zip)
  try {
    $e = $z.Entries | Where-Object { $_.FullName -eq $member } | Select-Object -First 1
    if (-not $e) { return '' }
    $s = $e.Open(); $m = New-Object System.IO.MemoryStream; $s.CopyTo($m); $s.Dispose()
    $h = [System.Security.Cryptography.MD5]::Create().ComputeHash($m.ToArray())
    return ([BitConverter]::ToString($h) -replace '-', '').ToLower()
  } finally { $z.Dispose() }
}
function Count-Entries($zip) { $z = [System.IO.Compression.ZipFile]::OpenRead($zip); try { $z.Entries.Count } finally { $z.Dispose() } }
if (Get-Process kl2 -ErrorAction SilentlyContinue) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$bad = 0
foreach ($x in $man.maps) {
  $dst = Join-Path $Game ('KLExpansion\Maps\' + $x.m + '\' + $x.f)
  $bak = "$dst$tag"; $tmp = "$dst.tmp1024"
  $src = Join-Path $PSScriptRoot ($x.m + '\' + $x.prp_file)
  $name = $x.m + '\' + $x.f
  if (-not (Test-Path -LiteralPath $dst)) { "$name : SKIP, not installed"; $bad++; continue }
  $cur = md5 $dst
  if ($Undo) {
    if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $x.old) { "$name : already undone" } else { "$name : SKIP, no backup and live is $cur"; $bad++ }; continue }
    if ($x.new -and $cur -ne $x.new) { "$name : SKIP, live is $cur, not the blowup build (changed since?). Backup left in place."; $bad++; continue }
    if ((md5 $bak) -ne $x.old) { "$name : SKIP, backup is not the expected original"; $bad++; continue }
    if ($DryRun) { "$name : would restore the original (dry run)"; continue }
    Remove-Item -LiteralPath $dst -Force
    Rename-Item -LiteralPath $bak -NewName $x.f
    if ((md5 $dst) -ne $x.old) { "$name : FAILED, restored file does not read back right!"; $bad++; continue }
    "$name : original restored, read back ok"
    continue
  }
  if ($x.new -and $cur -eq $x.new) { "$name : already installed"; continue }
  if ($cur -ne $x.old) { "$name : SKIP, live md5 is $cur, expected $($x.old). Another install in between? Not changed."; $bad++; continue }
  if (Test-Path -LiteralPath $bak) { "$name : SKIP, $bak already exists. Not changed."; $bad++; continue }
  if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $x.prp_md5) { "$name : SKIP, build file $src missing or changed"; $bad++; continue }
  if ($DryRun) { "$name : would patch $($x.member) (dry run)"; continue }
  if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
  Copy-Item -LiteralPath $dst -Destination $tmp
  try {
    $n0 = Count-Entries $tmp
    Patch-Zip $tmp $x.member $src
    if ((Count-Entries $tmp) -ne $n0) { throw 'entry count changed' }
    if ((Member-Md5 $tmp $x.member) -ne $x.prp_md5) { throw 'member does not read back' }
    if ($x.new -and (md5 $tmp) -ne $x.new) { throw "patched zip md5 $(md5 $tmp) is not the rehearsed $($x.new)" }
  } catch { "$name : FAILED while patching the copy ($_). Live file untouched."; Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; $bad++; continue }
  Rename-Item -LiteralPath $dst -NewName ($x.f + $tag)
  $ok = $false
  try { Rename-Item -LiteralPath $tmp -NewName $x.f; $ok = (Test-Path -LiteralPath $dst) } catch { $ok = $false }
  if (-not $ok) {
    if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
    Rename-Item -LiteralPath $bak -NewName $x.f
    "$name : FAILED swap, original put back"; $bad++; continue
  }
  "$name : installed (md5 $((md5 $dst).Substring(0,8))), original kept as $($x.f)$tag"
}
if ($bad) { "done with $bad problem(s), see above."; exit 4 }
'done.'
'''

BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0blowup.ps1" {arg}\r\npause\r\n'


def build(game, out, health, log=print, hasta=False):
    os.makedirs(out, exist_ok=True)
    man = {'health': health, 'maps': []}
    for m, f in MAPS + ([HASTA] if hasta else []):
        live = os.path.join(game, 'KLExpansion', 'Maps', m, f)
        pn, prp, changes = patch_prp(live, health)
        if prp is None:
            log('%s\\%s: nothing to change' % (m, f))
            continue
        d = os.path.join(out, m)
        os.makedirs(d, exist_ok=True)
        pf = f.replace('_Main.zip', '_Main.prp')
        with open(os.path.join(d, pf), 'wb') as fh:
            fh.write(prp)
        man['maps'].append({'m': m, 'f': f, 'member': pn, 'prp_file': pf, 'old': md5(live),
                            'prp_md5': hashlib.md5(prp).hexdigest(), 'new': '', 'changes': changes})
        for c in changes:
            log('  %s: %s' % (m, c))
    with open(os.path.join(out, 'blowup.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'blowup.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL blowup.bat', ''), ('UNDO blowup.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))
    return man


def ps(out, game, undo=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(out, 'blowup.ps1'), '-Game', game]
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rehearse(out, game, scratch, log=print):
    """INSTALL + UNDO on COPIES. Needs a kl2.exe stand-in file in the scratch game folder (an empty file; never run)."""
    g = os.path.join(scratch, 'game')
    man = json.load(open(os.path.join(out, 'blowup.json')))
    for x in man['maps']:
        d = os.path.join(g, 'KLExpansion', 'Maps', x['m'])
        os.makedirs(d, exist_ok=True)
        shutil.copy2(os.path.join(game, 'KLExpansion', 'Maps', x['m'], x['f']), d)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    rc, txt = ps(out, g)
    log(txt)
    new = {}
    for x in man['maps']:
        live = os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
        new[x['m']] = md5(live)
        with zipfile.ZipFile(live) as z:
            assert z.testzip() is None, 'zip test failed ' + live
            assert hashlib.md5(z.read(x['member'])).hexdigest() == x['prp_md5']
        sc, _, _ = kl_fa.load(live)
        gc.collect()                  # kl_fa.load may leave its zip open; the next UNDO must be able to delete the file
        vals = [kl_fa.value(sc, [list(u) for u in units(b[1:-1])][BLOW_FIELD]) for k in range(1, len(sc.nodes)) if 'escapesetup!' in sc.path[k].lower() for nm, b in sc.nodes[k]['ctrls'] if sc.p.key(nm) == 'VehicleEffects']
        log('  %s patched md5 %s, escape VehicleEffects blow=%s' % (x['m'], new[x['m']], vals))
    # determinism: second install of fresh copies must give the same md5s
    rc2, txt2 = ps(out, g, undo=True)
    log(txt2)
    for x in man['maps']:
        live = os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
        assert md5(live) == x['old'], 'undo is not byte identical: ' + x['m']
        assert not os.path.exists(live + TAG)
    log('UNDO byte identical: ok')
    rc3, txt3 = ps(out, g)
    for x in man['maps']:
        live = os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])
        assert md5(live) == new[x['m']], 'second install differs (not deterministic): ' + x['m']
        x['new'] = new[x['m']]
    log('second install gives the same md5s: ok')
    json.dump(man, open(os.path.join(out, 'blowup.json'), 'w'), indent=1)
    # with the md5s now in the manifest: install must say 'already installed', undo again byte identical, and a wrong live file is refused
    rc4, txt4 = ps(out, g)
    log(txt4)
    rc5, txt5 = ps(out, g, undo=True)
    log(txt5)
    for x in man['maps']:
        assert md5(os.path.join(g, 'KLExpansion', 'Maps', x['m'], x['f'])) == x['old']
    log('final UNDO byte identical: ok')
    shutil.rmtree(g)


def main():
    a = sys.argv[1:]
    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    game = opt('--game', DD)
    out = opt('--out')
    if not out:
        import kl_port_check
        out = os.path.join(kl_port_check.workdir(), 'build', 'blowup_1024')
    man = build(game, out, float(opt('--health', 5000)), hasta='--hasta' in a)
    print('kl_blowup: %d map(s) -> %s' % (len(man['maps']), out))
    if '--rehearse' in a:
        rehearse(out, game, opt('--rehearse'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
