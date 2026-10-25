"""kl_grenade_1025.py - GRENADE STEP 1, data side only (owner 2026-10-25: "look into grenades in dead men and implementing them here ...
adding them onto your character like dead men"). Written 2026-10-25. STAGE ONLY: nothing here touches the Dog Days game folder except the
generated grenade.ps1 when the owner runs it. Research and plan: re/grenades_1025.md (and re/grenades.md sections 10, 13).

WHAT IT DOES TO THE LIVE DM01 MAP (KLExpansion\\Maps\\DM01\\F01_Main.zip, pinned on md5 4d520614...):
  1 DD ASSETS, NO DEAD MEN ASSET. The map already carries Dog Days' five grenade item templates (Weapon\\Grenade_Fragmentation ...) and Ammo
    templates, but the Ammo's projectile slot (field 24) is empty, as in all nine stock FA maps. The slot now names Dog Days' own
    Projectile\\Projectiles_01\\Rocket_Flare, which tools/kl_grenade.py patch_level turns into the frag round: fuse 3.3 s, eGRENADE_FRAG, an
    Explode (Dead Men's radius/damage numbers, Dog Days' RPG effect + sound as stand-ins) and a ShakeCamera copied from Rocket_RPG7.
    Dead Men's own Projectile\\Grenade_* groups are NOT grafted (Dog Days has no pool for their effects, re/grenades.md 2).
    Consequence: Ammo\\Launcher_HK69A1_Flare shares that node and now also explodes (no FA actor holds it).
  2 PICKUPS. Three ZFFItemWeapon nodes (Special!Pickups!Grenade_Frag_01..03, cloned from Dog Days' own L05 pickup, template = Weapon\\
    Grenade_Fragmentation, count 1, eBOTH_PLAYERS: the Dead Men M03_A shape) stand 3 m in front of three START spawn points. They are
    top-level entities like every stock pickup (not in a room tree: MEASURED L03/L04/L05). Adding entities renumbers slot ids; .gms .buf .oct
    .rmi .rmc are rewritten by the procedure of kl_grenade.add_route (room-set check before == after, .oct records unmoved).
  Members that differ from the live zip: .prp .gms .buf .oct .rmi .rmc (the .prm, sound, .ANM, .HVK ... are byte for byte the live ones).

TOGGLE: the INSTALL is the switch. UNDO grenade.bat renames the .before-1025grenade backup back (byte identical). A KLExpansion option
"Grenades (recommended on)" needs the hook (proposal in re/grenades_1025.md section 5, e8's area); until then the bat pair is the toggle.
Only DM01 is touched; the nine stock FA maps, KL_PortBackup, KLHook.ini, dinput8.dll are never touched.

Usage (from tools/):  python kl_grenade_1025.py --out <stage folder> [--game <DD>] [--rehearse <scratch folder>]
"""
import os, sys, json, gc, hashlib, shutil, subprocess, zipfile, struct, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_scene, kl_graft, kl_prpjoin as J, kl_octree as O
import kl_fa_bots as F
import kl_grenade as G
from kl_prp import Prp

DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAP, ZIPNAME = 'DM01', 'F01_Main.zip'
PIN = '4d52061482bbf3f107ad0c97157969d7'      # the live DM01 zip with the vans pass (2026-10-25)
TAG = '.before-1025grenade'
EXTS = ('.prp', '.gms', '.buf', '.oct', '.rmi', '.rmc')
DONOR = ('L05', 'ROOT\\Extras!WeaponPickups!B5!TEMP_GUN_DESERT')     # Dog Days' own pickup node (ZFFItemWeapon + Action)
START = 'eSPAWN_TYPE_FRAGILE_ALLIANCE_START'
SPOTS = (2, 4, 6)             # START_02 / 04 / 06 (three of the eight), sorted by name
AHEAD = 300.0                 # GUESS: 3 m (1 unit = 1 cm, as the spawn rows 1.6-1.9 m apart suggest) in front of the spawn's facing
LIFT = 10.0                   # GUESS: the item origin sits a little above the spawn point's floor level
COUNT = 1                     # Dead Men's pickup count (M03_A FragGrenade); GUESS that it is the field ZItemWeapon[0]


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def spots(B):
    """-> [(name, place, forward)] of the chosen START spawn points (sorted by path)."""
    sc, st = B.sc, []
    for k in range(1, len(sc.nodes)):
        if sc.cls(k) == 'ZSpawnPoint' and START in [x for x in kl_fa.node_values(sc, k) if isinstance(x, str)]:
            Rm = B.fr[B.ents[k - 1]][0]
            fx, fz = Rm[0][2], Rm[2][2]
            n = math.hypot(fx, fz) or 1.0
            st.append((sc.path[k], B.at(k), (fx / n, fz / n)))
    st.sort()
    return [st[i - 1] for i in SPOTS] if len(st) >= max(SPOTS) else st[:3]


def build_members(live, log):
    """-> (members {ext: bytes}, report)."""
    B = F.Built(live, 'F01')
    sc = B.sc
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    if data != B['.prp']:
        raise ValueError('the live .prp does not re-serialise byte for byte')
    base_bad = sorted(str(x) for x in bad)          # the live map's own misfits (2 on the 1025 vans build); the change must add none
    log('live misfits (not ours): %s' % base_bad)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the level\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    wpath = next(sc.path[k] for k in range(1, len(sc.nodes)) if sc.path[k].endswith('\\Weapon\\Grenade_Fragmentation') and sc.cls(k) == 'ZFFItemTemplateWeapon')
    sp = spots(B)
    if len(sp) < 3:
        raise ValueError('fewer than three START spawn points')
    # ---- 1 the projectile chain (.prp only), n_actors=0: no police get a grenade (their throw needs route steps, a later job)
    rep = G.patch_level(sc, 0, log=log)
    # ---- 2 the pickups
    M = F.Maker()
    tops, places = [], []
    for i, (nm, at, (fx, fz)) in enumerate(sp):
        n = M.clone(DONOR[0], DONOR[1], 'Special!Pickups!Grenade_Frag_%02d' % (i + 1))
        # field names: ZItem[0] = template ref (a string token), ZItemWeapon[0] = count (donor values 'Weapon\\X', 0, 90, eBOTH_PLAYERS)
        M.set(n, None, {'ZItem[0]': wpath, 'ZItemWeapon[0]': COUNT})
        pos = (at[0] + fx * AHEAD, at[1] + LIFT, at[2] + fz * AHEAD)
        M.place(n, pos)
        tops.append(n)
        places.append([round(v, 1) for v in pos])
    q, order = M.scene(tops)
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'grenade pickups')
    bad = J.misfits(Jn)
    if len(bad) != len(base_bad):
        raise ValueError('objects that do not fit their class (live had %d): %s' % (len(base_bad), [(Jn.path[k], w, y) for k, w, y in bad[:3]]))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    # ---- the .gms / .buf side, as kl_grenade.add_route
    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, None, n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        for k in n.kids:
            ent(k, e)
    for t in tops:
        ent(t, None)
    A.ref_slots = nxt
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    ents = list(A.entities())
    if [e.name.decode('latin1') for e in ents] != Jn.names[1:] or [e.tid for e in ents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids), O.remap_ids(rmi, ids), O.remap_ids(rmc, ids)
    moved = sum(1 for a, b in ids.items() if a != b)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('room sets after the renumbering: %s (before: %s)' % (post, pre))
    if octn.record_refs() != octx.record_refs():
        raise ValueError('the .oct records moved: the .prm would have to be re-pointed (not done here)')
    mem = {'.prp': prp, '.gms': kl_gms.pack(gms), '.buf': buf, '.oct': octn.pack(), '.rmi': rmin.pack(), '.rmc': rmcn.pack()}
    names = {e: B.ext[e] for e in EXTS}
    r = dict(template=wpath, places=places, entities_added=len(order), slot_ids_moved=moved, flare=rep['flare'],
             ammo_field=rep['ammo_field'], member_names=names)
    log('grenade: projectile slot filled, %d pickups at %s, %d slot ids renumbered' % (len(tops), places, moved))
    return B, mem, r


def seal_and_extract(B, mem, scratch, log):
    """Write the full new zip in <scratch>, run kl_fa_bank.seal on it (stray room-list entries; may change .buf), return final members."""
    import kl_fa_bank
    d = os.path.join(scratch, 'sealcheck')
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    new = dict(B.files)
    for e in EXTS:
        new[B.ext[e]] = mem[e]
    kl_graft.write_zip(os.path.join(d, ZIPNAME), [(n, new[n]) for n in B.order])
    moved = kl_fa_bank.seal(d, log=lambda *_: None)
    with zipfile.ZipFile(os.path.join(d, ZIPNAME)) as z:
        out = {e: z.read(B.ext[e]) for e in EXTS}
    shutil.rmtree(d)
    log('seal: %d stray room-list entries moved (members changed by it: %s)' % (moved, [e for e in EXTS if out[e] != mem[e]]))
    return out, moved


PS1 = r'''# grenade.ps1 - DM01 frag grenade chain + 3 pickups (tools/kl_grenade_1025.py, 2026-10-25).
#   powershell -ExecutionPolicy Bypass -File grenade.ps1 [-Undo] [-DryRun] [-Rehearsal] [-Game <folder>]
# WHAT: six members (.prp .gms .buf .oct .rmi .rmc) inside KLExpansion\Maps\DM01\F01_Main.zip are replaced (same names). The live zip is COPIED,
#   the copy is patched and checked (member md5s, entry count), then swapped in; the live zip is renamed F01_Main.zip.before-1025grenade.
# SAFETY: refuses while kl2.exe runs; skipped unless the live zip md5 is exactly the pinned one (or already the new one);
#   read-back after the swap, on failure the original is put back; UNDO renames the backup back (md5 == the original).
#   -Rehearsal: does not need kl2.exe to be absent and refuses the real game folder.
# Not touched: the nine stock FA maps, KL_PortBackup, KLHook.ini, dinput8.dll.
param([switch]$Undo, [switch]$DryRun, [switch]$Rehearsal,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1025grenade'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'grenade.json') -Raw | ConvertFrom-Json
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
function Bytes-Md5($b) { $h = [System.Security.Cryptography.MD5]::Create().ComputeHash($b); ([BitConverter]::ToString($h) -replace '-', '').ToLower() }
function Patch-Zip($zip, $items) {
  $z = [System.IO.Compression.ZipFile]::Open($zip, 'Update')
  try {
    foreach ($it in $items) {
      $old = $z.Entries | Where-Object { $_.FullName -eq $it.member } | Select-Object -First 1
      if (-not $old) { throw "member $($it.member) not found" }
      $old.Delete()
      $e = $z.CreateEntry($it.member, [System.IO.Compression.CompressionLevel]::Optimal)
      $e.LastWriteTime = [DateTimeOffset]::new(2026, 10, 25, 0, 0, 0, [TimeSpan]::Zero)
      $s = $e.Open(); $b = [System.IO.File]::ReadAllBytes((Join-Path $PSScriptRoot $it.file)); $s.Write($b, 0, $b.Length); $s.Dispose()
    }
  } finally { $z.Dispose() }
}
function Member-Md5($zip, $member) {
  $z = [System.IO.Compression.ZipFile]::OpenRead($zip)
  try {
    $e = $z.Entries | Where-Object { $_.FullName -eq $member } | Select-Object -First 1
    if (-not $e) { return '' }
    $s = $e.Open(); $m = New-Object System.IO.MemoryStream; $s.CopyTo($m); $s.Dispose()
    return (Bytes-Md5 $m.ToArray())
  } finally { $z.Dispose() }
}
function Count-Entries($zip) { $z = [System.IO.Compression.ZipFile]::OpenRead($zip); try { $z.Entries.Count } finally { $z.Dispose() } }
$real = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
if ($Rehearsal -and ([IO.Path]::GetFullPath($Game).TrimEnd('\') -ieq $real)) { 'Rehearsal refuses the real game folder.'; exit 1 }
if (-not $Rehearsal -and (Get-Process kl2 -ErrorAction SilentlyContinue)) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$x = $man
$dst = Join-Path $Game ('KLExpansion\Maps\' + $x.m + '\' + $x.f)
$bak = "$dst$tag"; $tmp = "$dst.tmp1025g"
$name = $x.m + '\' + $x.f
if (-not (Test-Path -LiteralPath $dst)) { "$name : SKIP, not installed"; exit 4 }
$cur = md5 $dst
if ($Undo) {
  if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $x.old) { "$name : already undone"; exit 0 } else { "$name : SKIP, no backup and live is $cur"; exit 4 } }
  if ($x.new -and $cur -ne $x.new) { "$name : SKIP, live is $cur, not the grenade build (changed since?). Backup left in place."; exit 4 }
  if ((md5 $bak) -ne $x.old) { "$name : SKIP, backup is not the expected original"; exit 4 }
  if ($DryRun) { "$name : would restore the original (dry run)"; exit 0 }
  Remove-Item -LiteralPath $dst -Force
  Rename-Item -LiteralPath $bak -NewName $x.f
  if ((md5 $dst) -ne $x.old) { "$name : FAILED, restored file does not read back right!"; exit 4 }
  "$name : original restored, read back ok"; exit 0
}
if ($x.new -and $cur -eq $x.new) { "$name : already installed"; exit 0 }
if ($cur -ne $x.old) { "$name : SKIP, live md5 is $cur, expected $($x.old). Another install in between? Not changed (rebuild with tools/kl_grenade_1025.py on the new live file)."; exit 4 }
if (Test-Path -LiteralPath $bak) { "$name : SKIP, $bak already exists. Not changed."; exit 4 }
foreach ($it in $x.items) {
  $p = Join-Path $PSScriptRoot $it.file
  if (-not (Test-Path -LiteralPath $p) -or (md5 $p) -ne $it.md5) { "$name : SKIP, build file $p missing or changed"; exit 4 }
}
if ($DryRun) { "$name : would patch $($x.items.Count) members (dry run)"; exit 0 }
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
Copy-Item -LiteralPath $dst -Destination $tmp
try {
  $n0 = Count-Entries $tmp
  Patch-Zip $tmp $x.items
  if ((Count-Entries $tmp) -ne $n0) { throw 'entry count changed' }
  foreach ($it in $x.items) { if ((Member-Md5 $tmp $it.member) -ne $it.md5) { throw "member $($it.member) does not read back" } }
  if ($x.new -and (md5 $tmp) -ne $x.new) { throw "patched zip md5 $(md5 $tmp) is not the rehearsed $($x.new)" }
} catch { "$name : FAILED while patching the copy ($_). Live file untouched."; Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; exit 4 }
Rename-Item -LiteralPath $dst -NewName ($x.f + $tag)
$ok = $false
try { Rename-Item -LiteralPath $tmp -NewName $x.f; $ok = (Test-Path -LiteralPath $dst) } catch { $ok = $false }
if (-not $ok) {
  if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
  Rename-Item -LiteralPath $bak -NewName $x.f
  "$name : FAILED swap, original put back"; exit 4
}
"$name : installed (md5 $((md5 $dst).Substring(0,8))), original kept as $($x.f)$tag"
'done.'
'''

BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0grenade.ps1" {arg}\r\npause\r\n'


def write_files(out, man):
    with open(os.path.join(out, 'grenade.json'), 'w') as fh:
        json.dump(man, fh, indent=1)
    with open(os.path.join(out, 'grenade.ps1'), 'w', newline='\r\n') as fh:
        fh.write(PS1)
    for nm, arg in (('INSTALL DM01 grenade.bat', ''), ('UNDO DM01 grenade.bat', '-Undo')):
        with open(os.path.join(out, nm), 'w', newline='') as fh:
            fh.write(BAT.format(arg=arg))


def verify(zp, log):
    """Offline checks of the patched zip (loads it again from disk)."""
    B = F.Built(zp, 'F01')
    sc = B.sc
    data, bad, _p, _n = J.check(sc, log=lambda *_a: None)
    assert data == B['.prp'] and len(bad) == 2, 'patched .prp does not re-serialise / misfits %d (live had 2)' % len(bad)
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    rs = F.room_sets_check(B.scene, octx, rmi, rmc)
    ch = G.chain(sc)
    assert ch['ammo_projectile'].endswith('Rocket_Flare'), ch['ammo_projectile']
    names = [n for n, _v in ch['flare_ctrls']]
    assert names == ['FFHavokProjectileBallistic', 'Explode', 'ShakeCamera'], names
    pk = [k for k in range(1, len(sc.nodes)) if sc.cls(k) == 'ZFFItemWeapon']
    assert len(pk) == 3
    for k in pk:
        v = kl_fa.node_values(sc, k)
        assert v[9].endswith('Weapon\\Grenade_Fragmentation') and v[12] == 'eBOTH_PLAYERS', v
        assert len(sc.resolve(v[9])) == 1, 'template ref does not resolve'
    log('verify: %d nodes, room sets %s, flare ctrls %s, pickups %d at %s' % (len(sc.nodes), rs or 'clean', names, len(pk), [[round(c) for c in B.at(k)] for k in pk]))
    del B
    gc.collect()


def build(game, out, scratch, log=print):
    live = os.path.join(game, 'KLExpansion', 'Maps', MAP, ZIPNAME)
    cur = md5(live)
    if cur != PIN:
        raise SystemExit('live %s is %s, not the pinned %s: another install came in between; re-check and update PIN' % (live, cur, PIN))
    os.makedirs(out, exist_ok=True)
    B, mem, r = build_members(live, log)
    fin, sealed = seal_and_extract(B, mem, scratch, log)
    names = r.pop('member_names')
    items = []
    for e in EXTS:
        fn = 'DM01_Main' + e
        with open(os.path.join(out, fn), 'wb') as fh:
            fh.write(fin[e])
        items.append({'member': names[e], 'file': fn, 'md5': hashlib.md5(fin[e]).hexdigest(),
                      'old_md5': hashlib.md5(B.files[names[e]]).hexdigest(), 'changed': fin[e] != B.files[names[e]]})
    man = {'m': MAP, 'f': ZIPNAME, 'old': cur, 'new': '', 'items': items, 'sealed': sealed, 'report': r}
    write_files(out, man)
    del B
    gc.collect()
    return man


def ps(out, game, *extra):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(out, 'grenade.ps1'), '-Rehearsal', '-Game', game] + list(extra)
    r = subprocess.run(a, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rehearse(out, game, scratch, log=print):
    """INSTALL / UNDO on a COPY in <scratch>\\game (an empty kl2.exe stand-in, never run). Fills 'new' in grenade.json."""
    g = os.path.join(scratch, 'game')
    if os.path.isdir(g):
        shutil.rmtree(g)
    man = json.load(open(os.path.join(out, 'grenade.json')))
    d = os.path.join(g, 'KLExpansion', 'Maps', MAP)
    os.makedirs(d)
    shutil.copy2(os.path.join(game, 'KLExpansion', 'Maps', MAP, ZIPNAME), d)
    open(os.path.join(g, 'kl2.exe'), 'wb').close()
    zp = os.path.join(d, ZIPNAME)
    rc, txt = ps(out, g, '-DryRun'); log(txt); assert rc == 0
    rc, txt = ps(out, g); log(txt); assert rc == 0, 'install rc %d' % rc
    new = md5(zp)
    with zipfile.ZipFile(zp) as z:
        assert z.testzip() is None
        for it in man['items']:
            assert hashlib.md5(z.read(it['member'])).hexdigest() == it['md5'], it['member']
    log('patched md5 %s' % new)
    verify(zp, log)
    rc, txt = ps(out, g, '-Undo'); log(txt); assert rc == 0
    assert md5(zp) == man['old'] and not os.path.exists(zp + TAG), 'undo is not byte identical'
    log('UNDO byte identical: ok')
    rc, txt = ps(out, g); assert rc == 0
    assert md5(zp) == new, 'second install differs (not deterministic)'
    log('second install gives the same md5: ok')
    man['new'] = new
    json.dump(man, open(os.path.join(out, 'grenade.json'), 'w'), indent=1)
    rc, txt = ps(out, g); log(txt); assert 'already installed' in txt     # manifest now has the md5
    rc, txt = ps(out, g, '-Undo'); log(txt); assert md5(zp) == man['old']
    rc, txt = ps(out, g, '-Undo'); log(txt); assert 'already undone' in txt, 'undo twice'
    with open(zp, 'ab') as fh:
        fh.write(b'x')
    rc, txt = ps(out, g); log(txt)
    assert rc == 4 and 'SKIP, live md5' in txt, 'a changed live file must be refused'
    log('pin check: a changed live file is refused: ok')
    shutil.rmtree(g)
    return new


def main():
    a = sys.argv[1:]

    def opt(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    game, out = opt('--game', DD), opt('--out')
    if not out:
        print(__doc__)
        return 2
    scratch = opt('--rehearse') or os.path.join(out, '_scratch')
    os.makedirs(scratch, exist_ok=True)
    man = build(game, out, scratch)
    print('kl_grenade_1025: %d members -> %s' % (len(man['items']), out))
    if '--rehearse' in a:
        print('rehearsal ok, new zip md5', rehearse(out, game, scratch))
    return 0


if __name__ == '__main__':
    sys.exit(main())
