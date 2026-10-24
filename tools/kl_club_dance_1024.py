"""kl_club_dance_1024.py - DATA pass for Last Call (DM05A): the club civilians DANCE until something panics them.
Written 2026-10-24 (workflow, offline only). Reads a BUILT DM05A F01_Main.zip, writes a copy. Nothing imports it.

WHAT WAS FOUND (details and pictures: re/club_crowd.md Part 4)
  * Dog Days has no dance clip. Dead Men's M05_A animation file holds the club's ambient loops under /Level_Specific/M05_A/Ambient/
    (anim:Level_Specific/M05/3rd_Loungebar/{Males,Females}#...). Rendered with kl_animsheet (re/anim_dance_sheet): ONLY Female_Stripper
    (341 frames = 13.6 s at 25 fps; crouch, bent, floor, stand) is a dance; MaleGuest01/02 and FemaleGuest02 (200-217 frames) are standing
    sway / drink idles; MaleGuest03, Bartender, FemaleGuest01 are 11-frame stills; Sofa / Balcony clips are sitting poses.
  * SKELETON: every one of the 84 bones the lounge clips track exists, by NAME, in the Dog Days civilian's own clips (81 distinct bone names
    over the 'Civilian' collection of the build's .ANM; 0 bones missing). The clips ride bone NAMES, so the only conversion is kl_anm.convert
    (clip record 0x50 -> 0x68, never a raw copy) plus kl_anm.merge's renumbering of the bone / pose indices into the target's tables.
  * HOW A CIVILIAN PLAYS IT: stock Dog Days has the form. F03 'Gameplay!10_Airportpersonnel_01\\10_MiniCutScene' is a ZGROUP with a
    MiniCutsceneRout whose script is  ((Actor| NAME| ((act| ((subt| 1)| (anim| SLOT)| (idlemode| anim)| (idle| SLOT)| (blend| 1)| ...))|
    (delay| ((delay| 0)| (delayforever| 1)| ...))))| (Options| Options| ((mode| breakable))))  and is started by AIMonitor field 2 (the
    round-start list: the one that holds Timer_start_bots). 'idlemode anim' + 'idle SLOT' = the clip is the actor's idle, it loops.

WHAT IT DOES
  1. ANM: copies the chosen slots (default Female_Stripper) from Dead Men's M05_A 'Civilian' collection INTO the build's 'Civilian'
     collection (the one the club civilians' ZLNKOBJ[2] names). Only the chosen clips are carried (kl_anm.merge on a one-collection stand-in,
     then the slots are moved into 'Civilian'); the clip records' +0x2C (a .SND record offset of the SOURCE bank) is zeroed.
  2. SCENE: a new top group 'KL_Dance!' with one rout group per 10 civilians ('KLDance_NN', a clone of Dog Days' own civilian rout
     form from stock F07), each script naming the civilians by their group name; the rout list is appended to AIMonitor field 2.
     Civilian i starts DELAY = (i * 0.37) mod 6 s after the round start so the room does not move in unison.
  The panic is NOT changed: tbCivRunToGate -> 20_RunToStreet stays. Whether that rout takes the actor over from the dance (mode
  'breakable' like F03's) is the one thing that needs a live run.

Usage (from tools/):
  python kl_club_dance_1024.py build <in F01_Main.zip> <out F01_Main.zip> [--clips Female_Stripper,MaleGuest01] [--group 10] [--force]
  python kl_club_dance_1024.py stage <live zip b5e45efa> <lastcall2 zip c563e6bc> <out folder> --rehearse <scratch>
"""
import collections, hashlib, json, os, shutil, struct, subprocess, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa, kl_gms, kl_graft, kl_scene, kl_anm
import kl_fa_bots as F
import kl_fa_cover as C
import kl_fa_civs
import kl_octree as O
import kl_prpjoin as J

MD5_LIVE = 'b5e45efae901a8d3ac2c353cf37224ad'       # live DM05A zip 2026-10-24 (lastcall_1024n / club_1024d chain)
MD5_LC2 = 'c563e6bc93cf443581c35b0d5cc5f08d'        # staged lastcall2 (C:/kl_build_1024/lastcall2_1024r2)
GROUP = 'KL_Dance!'
TAG = '.before-1024dance'
AMBIENT = '/Level_Specific/M05_A/Ambient/'
DEFAULT_CLIPS = ['Female_Stripper']
COLLECTION = 'Civilian'
TMP = 'KLDanceTmp'
PER_ROUT = 10
STAGGER = 0.37
STAGGER_MOD = 6.0
HOST, FORM = kl_fa_civs.HOST, kl_fa_civs.FORM


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------ 1. the animation file
def dm_anm():
    with zipfile.ZipFile(J.level_zip('M05_A')) as z:
        n = next(x for x in z.namelist() if x.upper().endswith('.ANM'))
        return kl_anm.Anm(z.read(n), 'dm')


def anm_pass(dd_raw, clips, log=print):
    """-> (new .ANM bytes, report). The slots AMBIENT+name are added to the 'Civilian' collection of the Dog Days file `dd_raw`."""
    dd = kl_anm.Anm(dd_raw, 'dd')
    dm = kl_anm.convert(dm_anm())                         # header 0x50 -> 0x68 records; never the raw file
    slots = [AMBIENT + c for c in clips]
    src = dm.col(COLLECTION)
    lists = src.lists()
    pool, table, picked = [], [-1] * len(dm.slots), {}
    for s in slots:
        sid = dm.slots.index(s)
        if sid not in lists:
            raise ValueError('Dead Men %s collection has no list for %s' % (COLLECTION, s))
        table[sid] = len(pool)
        pool += lists[sid]
        picked[s] = [dm.names[c] for _f, c in lists[sid]]
    while table and table[-1] < 0:
        table.pop()
    dm.cols = [kl_anm.Collection(kl_anm.PREFIX + TMP, [], pool, table)]
    out = kl_anm.merge(dd, dm, {TMP: TMP})
    tmp = out.cols.pop()
    civ = out.col(COLLECTION)
    n0 = len(dd.clips)
    for s in slots:
        sid = out.slots.index(s)
        lst = tmp.lists()[sid]
        if sid < len(civ.table) and civ.table[sid] >= 0:
            raise ValueError('%s already has a list for %s' % (COLLECTION, s))
        civ.table += [-1] * (sid + 1 - len(civ.table))
        civ.table[sid] = len(civ.pool)
        civ.pool += lst
    kl_anm.relist(out)
    for i in range(n0, len(out.clips)):                   # +0x2C = a record offset of the SOURCE level's .SND: not valid here (kl_anm docstring)
        struct.pack_into('<I', out.clips[i], 0x2c, 0)
    bad = kl_anm.audit(out)
    if bad:
        raise ValueError('kl_anm.audit: %s' % bad[:5])
    raw = out.save()
    back = kl_anm.Anm(raw, 'dd')
    if kl_anm.audit(back) or back.save() != raw:
        raise ValueError('the new .ANM does not round-trip')
    for s in slots:                                       # the lookup the game does: name -> slot id -> Civilian collection -> clip
        ci = back.lookup(COLLECTION, s)
        if ci is None or 'Loungebar' not in back.names[ci]:
            raise ValueError('lookup of %s gives %r' % (s, ci))
    rep = collections.OrderedDict(slots=slots, clips=picked, clips_before=len(dd.clips), clips_after=len(back.clips), bytes_before=len(dd_raw),
                                  bytes_after=len(raw), bones_before=len(dd.bones), bones_after=len(back.bones), poses_before=len(dd.poses),
                                  poses_after=len(back.poses), slots_before=len(dd.slots), slots_after=len(back.slots),
                                  new_clips=[back.names[i] for i in range(n0, len(back.clips))])
    return raw, rep


# ------------------------------------------------------------------ 2. the scene
def script_for(names, slots, delays):
    parts = []
    for i, (nm, d) in enumerate(zip(names, delays)):
        s = slots[i % len(slots)]
        parts.append('(Actor| %s| ((delay| ((delay| %.2f)| (delayforever| 0)| (randdelay| 0.0)| (_dep| ())))| '
                     '(act| ((fltarget| None)| (subt| 1)| (anim| %s)| (idlemode| anim)| (dlgmode| None)| (idle| %s)| (blend| 1)| (lefthandik| 0)| (_dep| ())))| '
                     '(delay| ((delay| 0)| (delayforever| 1)| (randdelay| 0.0)| (_dep| ())))))' % (nm, d, s, s))
    return '(%s| (Options| Options| ((mode| breakable))))' % '| '.join(parts)


def dancers(B):
    """[(actor node, group node, group name)] of every ZCivilian actor of the build, in scene order."""
    sc, out = B.sc, []
    for k in range(1, len(sc.names)):
        if sc.cls(k) == 'ZFFActor' and kl_fa.has(sc, k, 'ZCivilian'):
            g = sc.parent[k]
            out.append((k, g, sc.names[g]))
    return out


def build(src, dst, clips=None, per=PER_ROUT, force=False, log=print, group=None, only=None):
    """group / only (lastcall3, 2026-10-25): a SECOND dance group for civilians added after the first pass: `group` = the new top's name
    (default GROUP), `only` = a set of civilian group names to dance (default all); a second group does not merge the .ANM again."""
    clips = clips or DEFAULT_CLIPS
    gname = group or GROUP
    have = md5(src)
    if have not in (MD5_LIVE, MD5_LC2) and not force:
        raise ValueError('%s: md5 %s is neither the live DM05A (%s) nor lastcall2 (%s); use --force' % (src, have, MD5_LIVE, MD5_LC2))
    B = F.Built(src)
    sc = B.sc
    if any(sc.names[t] == gname for t in sc.tops()):
        log('kl_club_dance_1024: %s already holds %s: nothing to do' % (src, gname))
        return None
    dl = dancers(B)
    if only is not None:
        dl = [x for x in dl if x[2] in only]
    if not dl:
        raise ValueError('no civilians in the build')
    names = [n for _k, _g, n in dl]
    if len(set(names)) != len(names):
        raise ValueError('civilian group names are not unique (a script names the actor by group name)')
    for _k, _g, n in dl:
        if B.values(_k).get('ZLNKOBJ[2]') != kl_anm.PREFIX + COLLECTION:
            raise ValueError('%s does not play the %s animation set' % (n, COLLECTION))
    if group:
        a0 = kl_anm.Anm(B['.ANM'], 'dd')
        for c in clips:
            if a0.lookup(COLLECTION, AMBIENT + c) is None:
                raise ValueError('the .ANM has no %s clip for %s (a second group needs the first pass)' % (COLLECTION, c))
        raw, arep = B['.ANM'], dict(bytes_before=len(B['.ANM']), bytes_after=len(B['.ANM']), note='clips already merged')
    else:
        raw, arep = anm_pass(B['.ANM'], clips, log)
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    F._roundtrip(B)
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    pre = F.room_sets_check(B.scene, octx, rmi, rmc)
    prm = B['.prm']

    M = F.Maker()
    gk = C.group_form(B)
    grp = C._node(M, B, gk, gname)
    M.place(grp, (0.0, 0.0, 0.0))
    base = F.R_ + gname + '\\'
    slots = [AMBIENT + c for c in clips]
    routs = []
    for r in range(0, len(dl), per):
        chunk = dl[r:r + per]
        nm = ('KLDance2_%02d' if group else 'KLDance_%02d') % (r // per)
        rn = M.clone(HOST, FORM + '\\20_RunToStreet', nm)
        M.place(rn, (0.0, 0.0, 0.0))
        delays = [round(((r + i) * STAGGER) % STAGGER_MOD, 2) for i in range(len(chunk))]
        # field 0 = the script, field 1 = the rout's NEXT list (stock's points at the civilian's Deactivate modifier: here nothing)
        M.set(rn, 'MiniCutsceneRout', {0: script_for([n for _k, _g, n in chunk], slots, delays), 1: []})
        grp.add(rn)
        routs.append((nm, [n for _k, _g, n in chunk], delays))
    q, order = M.scene([grp])
    Jn = J.join(sc, [(sc, t) for t in sc.tops()] + [(q, t) for t in q.tops()], 'dance')
    hit = Jn.resolve(F.R_ + 'Gameplay!AIMonitor')
    mk = [(k, i, v) for k, i, v in kl_fa.controllers(Jn, 'AIMonitor') if k in hit]
    if len(mk) != 1:
        raise ValueError('AIMonitor: %d controllers' % len(mk))
    k, i, v = mk[0]
    lst0 = list(v[2])
    lst = lst0 + [base + nm for nm, _a, _d in routs if base + nm not in lst0]

    def setl(us, lst=lst):
        us[2] = kl_fa._refs(Jn, lst)
    kl_fa.edit(Jn, k, i, setl)
    data = Jn.p.serialize()
    back = F.Prp(data)
    if back.serialize() != data or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')

    A = B.scene
    slot0 = A.slots()
    nxt = max([A.ref_slots] + [e.ref + 1 for e in B.ents])
    ref0, made_e = nxt, {}

    def ent(n, parent):
        nonlocal nxt
        e = kl_scene.Entity()
        e.name, e.tid, e.flags, e.group, e.model = n.name.encode('latin1'), n.tid, n.flags, n.group, n.model
        e.rot, e.trans, e.raw, e.aux, e.ref, e.links, e.lkey, e.kids, e.parent = n.rot, n.trans, getattr(n, 'raw', None), n.aux, nxt, n.links, 0, [], parent
        nxt += 1
        (parent.kids if parent else A.roots).append(e)
        made_e[id(n)] = e
        for kd in n.kids:
            ent(kd, e)
    ent(grp, None)
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
    # listing (GUESS, as kl_dm02_shops_1024 / kl_fa_civs.add): the new top-level group goes into the root's group tree 3 with the box of the
    # civilians it drives; the rout groups themselves have no geometry
    pts = [B.at(g) for _k, g, _n in dl]
    root3 = octn.rooms[0][3]
    if root3 is None:
        raise ValueError('the root has no tree 3')
    lo = tuple(min(p[a] for p in pts) - 10.0 for a in range(3))
    hi = tuple(max(p[a] for p in pts) + (10.0 if a != 1 else 190.0) for a in range(3))
    octn.rooms[0][3] = O.join_trees(root3, C._tree([(slot1[made_e[id(grp)]] + 2, lo, hi)]))
    octn.rooms[0][3].check()
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move:
        pm = bytearray(prm)
        t, n = struct.unpack_from('<II', pm, 0)
        old = set(octx.record_refs())
        for i_ in range(1, n):
            o_, size = struct.unpack_from('<II', pm, t + 16 * i_)
            if size == 64 and pm[o_:o_ + 4] == b'\0\1\7\0':
                v_ = struct.unpack_from('<I', pm, o_ + 0x1c)[0]
                if v_ in move:
                    struct.pack_into('<I', pm, o_ + 0x1c, move[v_]); repointed += 1
                elif v_ and v_ not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i_, v_))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(pm)
    post = F.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))

    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = data, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    new[B.ext['.ANM']] = raw
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    changed = sorted(e for e, n in B.ext.items() if new[n] != B.files[n])
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    kl_graft.write_zip(dst, [(n, new[n]) for n in B.order])
    rep = collections.OrderedDict(
        source=src, source_md5=have, out=dst, out_md5=md5(dst), members_changed=changed, civilians=len(dl), routs=[[n, a, d] for n, a, d in routs],
        entities_before=len(B.ents), entities=len(ents), entities_added=len(order), ref_ids='%d..%d' % (ref0, nxt - 1), slot_ids_moved=moved,
        prm_model_roots_repointed=repointed, slot_id_faults_before=pre, slot_id_faults_after=post, aimonitor_list2_before=len(lst0),
        aimonitor_list2_after=len(lst), anm=arep)
    log('kl_club_dance_1024: %d civilians in %d routs, %d entities added, REF ids %s, members changed %s, %d slot ids renumbered, ANM %d -> %d bytes -> %s (%s)'
        % (len(dl), len(routs), len(order), rep['ref_ids'], ' '.join(changed), moved, arep['bytes_before'], arep['bytes_after'], dst, rep['out_md5']))
    return rep


def verify(dst, clips):
    """Reads the output back: the rout scripts name existing civilians + slots the .ANM knows, AIMonitor names the routs."""
    B = F.Built(dst)
    sc = B.sc
    a = kl_anm.Anm(B['.ANM'], 'dd')
    civ = {n for _k, _g, n in dancers(B)}
    seen, fails = set(), []
    routs = {sc.path[k]: x for k, _i, x in kl_fa.controllers(sc, 'MiniCutsceneRout') if sc.path[k] and ('\\KL_Dance') in sc.path[k]}
    for p, x in routs.items():
        import re
        for nm in re.findall(r'\(Actor\| ([^|]*)\|', x[0]):
            if nm not in civ:
                fails.append('%s names %s: not a civilian' % (p, nm))
            seen.add(nm)
        for s in re.findall(r'\((?:anim|idle)\| ([^)]*)\)', x[0]):
            if s not in a.slots or a.lookup(COLLECTION, s) is None:
                fails.append('%s plays %s: the Civilian collection has no clip for it' % (p, s))
        if x[1]:
            fails.append('%s has a NEXT list %s' % (p, x[1]))
    if seen != civ:
        fails.append('civilians not dancing: %s' % sorted(civ - seen)[:5])
    mon = [v for k, _i, v in kl_fa.controllers(sc, 'AIMonitor')]
    named = [r for v in mon for r in v[2] if 'KL_Dance' in r]
    if sorted(named) != sorted(routs):
        fails.append('AIMonitor names %s, routs are %s' % (sorted(named), sorted(routs)))
    return fails, len(routs), len(civ)


# ------------------------------------------------------------------ install / undo, md5-chained
PS1 = r'''# dance.ps1 - Last Call (DM05A): the club civilians dance until the panic (tools/kl_club_dance_1024.py, 2026-10-24).
#   powershell -ExecutionPolicy Bypass -File dance.ps1 [-Undo] [-DryRun] [-Game <folder>]
# WHAT: KLExpansion\Maps\DM05A\F01_Main.zip is replaced by the build file next to this script (.ANM .prp .gms .buf .oct .rmi .rmc .prm
#   change). The live zip is renamed F01_Main.zip.before-1024dance (never overwritten).
# SAFETY: refuses while kl2.exe runs; the live zip md5 must be exactly the one this was built on (or already the new one); read-back md5
#   after the copy; on failure the original is put back; UNDO only when live == the new build, and renames the backup back (byte identical).
param([switch]$Undo, [switch]$DryRun,
      [string]$Game = 'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days')
$ErrorActionPreference = 'Stop'
$tag = '.before-1024dance'
$man = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dance.json') -Raw | ConvertFrom-Json
function md5($f) { (Get-FileHash -LiteralPath $f -Algorithm MD5).Hash.ToLower() }
if (Get-Process kl2 -ErrorAction SilentlyContinue) { 'kl2.exe is running: close the game first. Nothing was changed.'; exit 1 }
if (-not (Test-Path (Join-Path $Game 'kl2.exe'))) { "no kl2.exe in $Game"; exit 1 }
$dst = Join-Path $Game ('KLExpansion\Maps\' + $man.m + '\' + $man.f)
$bak = "$dst$tag"; $tmp = "$dst.tmp1024"
$src = Join-Path $PSScriptRoot $man.f
"target: $dst  (built on $($man.old.Substring(0,8)))"
if (-not (Test-Path -LiteralPath $dst)) { "SKIP, $dst not installed"; exit 4 }
$cur = md5 $dst
if ($Undo) {
  if (-not (Test-Path -LiteralPath $bak)) { if ($cur -eq $man.old) { 'already undone'; exit 0 } else { "SKIP, no backup and live is $cur"; exit 4 } }
  if ($cur -ne $man.new) { "SKIP, live is $cur, not this build (changed since). Backup left in place."; exit 4 }
  if ((md5 $bak) -ne $man.old) { 'SKIP, backup is not the expected original'; exit 4 }
  if ($DryRun) { 'would restore the original (dry run)'; exit 0 }
  Remove-Item -LiteralPath $dst -Force
  Rename-Item -LiteralPath $bak -NewName $man.f
  if ((md5 $dst) -ne $man.old) { 'FAILED, restored file does not read back right!'; exit 4 }
  'original restored, read back ok'; exit 0
}
if ($cur -eq $man.new) { 'already installed'; exit 0 }
if ($cur -ne $man.old) { "SKIP, live md5 is $cur, expected $($man.old). Another install in between? Not changed."; exit 4 }
if (Test-Path -LiteralPath $bak) { "SKIP, $bak already exists. Not changed."; exit 4 }
if (-not (Test-Path -LiteralPath $src) -or (md5 $src) -ne $man.new) { "SKIP, build file $src missing or changed"; exit 4 }
if ($DryRun) { 'would install (dry run)'; exit 0 }
if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Force }
Copy-Item -LiteralPath $src -Destination $tmp
if ((md5 $tmp) -ne $man.new) { 'FAILED copying, live untouched'; Remove-Item -LiteralPath $tmp -Force; exit 4 }
Rename-Item -LiteralPath $dst -NewName ($man.f + $tag)
$ok = $false
try { Rename-Item -LiteralPath $tmp -NewName $man.f; $ok = (Test-Path -LiteralPath $dst) } catch { $ok = $false }
if (-not $ok) {
  if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Force }
  Rename-Item -LiteralPath $bak -NewName $man.f
  'FAILED swap, original put back'; exit 4
}
if ((md5 $dst) -ne $man.new) { 'FAILED read-back, run UNDO'; exit 4 }
"installed (md5 $((md5 $dst).Substring(0,8))), original kept as $($man.f)$tag"
'''
BAT = '@echo off\r\ncd /d "%~dp0"\r\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dance.ps1" {arg}\r\npause\r\n'


def _ps(d, game, undo=False):
    a = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', os.path.join(d, 'dance.ps1'), '-Game', game]
    if undo:
        a.append('-Undo')
    r = subprocess.run(a, capture_output=True, text=True)
    return r.stdout + r.stderr


def stage(live, lc2, out, scratch=None, clips=None, log=print):
    """out/live (built on the live zip) and out/lastcall2 (built on the staged lastcall2 zip), each with an md5-chained INSTALL/UNDO."""
    if md5(live) != MD5_LIVE or md5(lc2) != MD5_LC2:
        raise SystemExit('inputs are not the pinned live %s / lastcall2 %s' % (MD5_LIVE, MD5_LC2))
    vd = {}
    for v, src in (('live', live), ('lastcall2', lc2)):
        d = os.path.join(out, v)
        os.makedirs(d, exist_ok=True)
        z = os.path.join(d, 'F01_Main.zip')
        rep = build(src, z, clips)
        fails, nr, nc = verify(z, clips or DEFAULT_CLIPS)
        if fails:
            raise SystemExit('verify FAIL: %s' % fails)
        log('verify %s: PASS (%d routs, %d civilians)' % (v, nr, nc))
        man = dict(m='DM05A', f='F01_Main.zip', variant=v, old=md5(src), new=md5(z), tag=TAG)
        with open(os.path.join(d, 'dance.json'), 'w') as fh:
            json.dump(man, fh, indent=1)
        with open(os.path.join(d, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        with open(os.path.join(d, 'dance.ps1'), 'w', newline='\r\n') as fh:
            fh.write(PS1)
        for nm, arg in (('INSTALL dance %s.bat' % v, ''), ('UNDO dance %s.bat' % v, '-Undo')):
            with open(os.path.join(d, nm), 'w', newline='') as fh:
                fh.write(BAT.format(arg=arg))
        vd[v] = (d, man, src)
        log('%s: %s -> %s' % (v, man['old'], man['new']))
    if scratch:
        rehearse(vd, scratch, log)
    return 0


def rehearse(vd, scratch, log=print):
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game')
    live = os.path.join(g, 'KLExpansion', 'Maps', 'DM05A', 'F01_Main.zip')
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    log('rehearsal target (inside scratch): ' + live)
    for v, (d, man, src) in vd.items():
        shutil.rmtree(g, ignore_errors=True)
        os.makedirs(os.path.dirname(live))
        open(os.path.join(g, 'kl2.exe'), 'wb').close()
        shutil.copy2(src, live)
        log('--- %s' % v)
        t = _ps(d, g); log(t); assert 'installed' in t and md5(live) == man['new'], t
        assert os.path.isfile(live + TAG) and md5(live + TAG) == man['old']
        t = _ps(d, g, True); log(t)
        assert md5(live) == man['old'] and not os.path.exists(live + TAG), 'undo not byte identical'
        t = _ps(d, g); assert md5(live) == man['new']
        t = _ps(d, g); assert 'already installed' in t, t
        o = 'lastcall2' if v == 'live' else 'live'
        t = _ps(vd[o][0], g); log(t); assert 'SKIP' in t and md5(live) == man['new'], t
        t = _ps(vd[o][0], g, True); assert 'SKIP' in t and md5(live) == man['new'], t
        t = _ps(d, g, True); assert md5(live) == man['old'] and not os.path.exists(live + TAG)
        with open(live, 'ab') as fh:
            fh.write(b'x')
        t = _ps(d, g); log(t); assert 'SKIP, live md5' in t and not os.path.exists(live + TAG), t
        log('%s rehearsal ok (install, undo byte-identical, reinstall same md5, other base refused, wrong md5 refused)' % v)
    shutil.rmtree(g, ignore_errors=True)


def main():
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    clips = opt('--clips')
    clips = clips.split(',') if clips else None
    if len(a) < 3 or a[0] not in ('build', 'stage'):
        print(__doc__)
        return 2
    if a[0] == 'build':
        rep = build(a[1], a[2], clips, int(opt('--group', PER_ROUT)), '--force' in a)
        if rep:
            fails, nr, nc = verify(a[2], clips or DEFAULT_CLIPS)
            print('verify:', 'PASS' if not fails else fails)
            return 1 if fails else 0
        return 0
    return stage(a[1], a[2], a[3], opt('--rehearse'), clips)


if __name__ == '__main__':
    sys.exit(main())
