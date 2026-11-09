#!/usr/bin/env python3
"""rappel - converter side of Dead Men's rappelling in Dog Days (loader side: loader/rappel.inc).

Static RE (kl2.exe / kaneandlynch.exe, 12 Oct; see the notes at the end of this file):
  * kl2.exe still carries Dead Men's whole rappel system: ZRappellingBox (vt 0xbc23bc, the same 12 properties
    as Dead Men), ZFFPlayerMovementRappel (vt 0xbb5ebc, player movement id 0x10 at ZFFPlayer+0xdf0, built by
    0x51d240 for every player) and the rappel-point list at gameMgr+0x15b8 (max 10).  Nothing is missing in the
    exe; two things are missing in our converted levels:
  1. CLIPS.  The movement plays /Movement/Rappelling/{Start,Wait_On_Wall,Jump_Start,Jump_Loop,Jump_End}
     (name ids cached by slot 20, 0x77ac70) from the PLAYER's animation database.  The Dog Days donor (F03) has
     NO /Movement/Rappelling/ path in any database (checked 13 Oct); the merge filter (port_level.py, path_filter) keeps /Level_Specific/ and
     /Movement/Climb/ only, so Kane (the player DB) and Lynch have none.  0x59d550 then returns a NULL clip and
     Activate (slot 15, 0x6db3b0) passes it straight to PlayAnim (vt+0x204) and 0x5a5030 (inferred: crash or
     no-op the moment the player presses use at a rappel point).
     -> wrap_path_filter(): merge Dead Men's own /Movement/Rappelling/* (PlayerCharacter -> Kane,
        Lynch_Coop -> Lynch; 12 clips, the same ones Dead Men's police use).
     -> ensure_player_clips(): safety net after the merge - any of those paths Kane/Lynch still lack is pointed
        at another DB's list in the merged file. F03 itself carries none, so the clips come from Dead Men's merge
        only; the net only helps when a merged DM DB (e.g. police) has them and the player DB does not.
  2. CALLBACKS.  ZRappellingBox holds 8 message containers, 4 per player: [enter, leave, begin, end].  Dead Men
     (0x6a0600: gameMgr player slot 0 == player ? +0x38 : +0x48) gives the single player (slot 0, Kane) the
     FIRST four.  kl2 (0x495c80 enter, 0x76a240 leave, 0x7a7980 begin, 0x811c20 end) compares with player
     slot ONE (`push 1; call 0x660b00`), which is co-op player two in Dog Days (same numbering swap as the
     player filters, ANP_PFILTER_SWAP), so the single player gets the SECOND four.  Dead Men's single-player
     callbacks (M03 objective, M08 crowd + Shelly, M09 office countdown, M12 MG blocker, M13 allies catch-up)
     never fire.
     -> fix_prp_out(): ANP_RAPPEL_CB=both (default) writes Dead Men's player-one containers into BOTH halves
        (works whichever slot the player sits in; Dead Men's co-op-Lynch containers are dropped - nobody plays
        Dead Men co-op in Dog Days); 'swap' exchanges the halves; 'keep' leaves them as converted.

Hooks into tools/port_level.py (port_level.py is owned by another workflow - add these lines there):
  (1) ANM block, right after the line that defines `pf=...` (path filter, ~line 1360):
          import rappel; pf=rappel.wrap_path_filter(pf)
  (2) right after `merged,mrep=anm_merge.merge_report(...)` (~line 1361):
          merged=rappel.ensure_player_clips(merged,rep)
  (3) in convert_scene (or wherever `out` is final), right before `prp_bytes=write_prp(...)` (~line 1184):
          import rappel; rappel.fix_prp_out(out,rep)
  All three are no-ops with ANP_RAPPEL=0.  Switches:
    ANP_RAPPEL      1 (default) | 0     everything below off
    ANP_RAPPEL_ANM  dm (default) | dd | off   dm = merge Dead Men's clips (filter) + DD safety net; dd = safety net only
    ANP_RAPPEL_CB   both (default) | swap | keep

CLI (offline checks, no game needed):
    py tools/rappel.py census                       every RappellingBox / RappelCheckPoint in work/scn/dm
    py tools/rappel.py anm  DD_F03.ANM DM_LEVEL.ANM  merge with/without the rappel filter, report the player DBs
    py tools/rappel.py check CONVERTED_Main.zip     clips in Kane/Lynch + callback halves in a converted level
"""
import os, sys, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PREFIX = b'/Movement/Rappelling/'
# the five the player movement caches (kl2 0x77ac70) - the ones that must resolve in the player's DB
PLAYER_CLIPS = (b'/Movement/Rappelling/Start', b'/Movement/Rappelling/Jump_Start', b'/Movement/Rappelling/Wait_On_Wall',
                b'/Movement/Rappelling/Jump_Loop', b'/Movement/Rappelling/Jump_End')
PLAYER_DBS = (b'Kane', b'Lynch')                 # player (PlayerCharacter) and buddy (Lynch_Coop) after the merge
DONOR_DBS = (b'Police', b'Thug', b'Swat_02')     # Dog Days DBs that carry the rappel set in F03

ENABLED = os.environ.get('ANP_RAPPEL', '1') == '1'
ANM_MODE = os.environ.get('ANP_RAPPEL_ANM', 'dm')
CB_MODE = os.environ.get('ANP_RAPPEL_CB', 'both')


def _rep_add(rep, key, n=1):
    if rep is not None:
        rep[key] += n


# ------------------------------------------------------------------------------------------------ ANM
def wrap_path_filter(pf):
    """port_level's merge filter + Dead Men's /Movement/Rappelling/* clips (None = no filter = keep None)."""
    if pf is None or not ENABLED or ANM_MODE != 'dm':
        return pf
    return lambda p_: pf(p_) or p_.startswith(PREFIX)


def ensure_player_clips(anm_bytes, rep=None):
    """Point every /Movement/Rappelling/* path the player/buddy DBs lack at the donor's Police/Thug list.
    Returns the (possibly rebuilt) ANM bytes; unchanged bytes when nothing was missing."""
    if not ENABLED or ANM_MODE == 'off':
        return anm_bytes
    import anm_lib as L
    f = L.AnmFile.parse(anm_bytes)
    names = f.names
    rids = [i for i, n in enumerate(names.names) if n.startswith(PREFIX)]
    if not rids:
        _rep_add(rep, 'rappel: no /Movement/Rappelling/ names in the ANM (player rappel cannot play)')
        return anm_bytes
    donors = [d for d in (f.db_by_short(x) for x in DONOR_DBS) if d is not None]
    changed = 0
    for short in PLAYER_DBS:
        db = f.db_by_short(short)
        if db is None:
            _rep_add(rep, 'rappel: DB %s missing in the ANM' % short.decode())
            continue
        have = sum(1 for i in rids if db.get(i) is not None)
        added = 0
        for i in rids:
            if db.get(i) is not None:
                continue
            src = next((d.get(i) for d in donors if d.get(i) is not None), None)
            if src is None:
                continue
            db.set(i, list(src)); added += 1
        changed += added
        miss = [n for n in PLAYER_CLIPS if names.id_of(n) is None or db.get(names.id_of(n)) is None]
        _rep_add(rep, 'rappel: %s DB rappel paths %d own + %d from Dog Days police%s' % (
            short.decode(), have, added, (' - STILL MISSING %s' % b','.join(m[len(PREFIX):] for m in miss).decode()) if miss else ''))
    if not changed:
        return anm_bytes
    return f.build()


def player_clip_report(anm_bytes):
    import anm_lib as L
    f = L.AnmFile.parse(anm_bytes)
    out = {}
    for short in PLAYER_DBS + DONOR_DBS:
        db = f.db_by_short(short)
        if db is None:
            out[short.decode()] = None; continue
        r = {}
        for i, n in enumerate(f.names.names):
            if n.startswith(PREFIX):
                lst = db.get(i)
                r[n[len(PREFIX):].decode()] = [c for _, c in lst] if lst else None
        out[short.decode()] = r
    return out, len(f.anim.recs), len(anm_bytes)


# ------------------------------------------------------------------------------------------------ PRP
def _box_fields(out, i):
    """out[i] = (_,12,'RappellingBox'), out[i+1] = BeginObject.  Returns (start, end, items) where items is the
    parsed field list [bool, ref, cont*8, bool, bool] with containers as (pos, [strings]) or None if the layout
    is not the expected one.  start/end delimit the event body (exclusive of BeginObject/EndObject)."""
    if i + 1 >= len(out) or out[i + 1][1] & 0x7f != 2:
        return None
    j = i + 2; items = []
    while j < len(out) and out[j][1] & 0x7f != 0x7e:
        b = out[j][1] & 0x7f
        if b == 4:
            n = out[j][2]
            strs = [out[j + 1 + k][2] for k in range(n)]
            if any(out[j + 1 + k][1] & 0x7f != 12 for k in range(n)):
                return None
            items.append(('C', j, strs)); j += 1 + n
        else:
            items.append((b, j, out[j][2])); j += 1
    kinds = [k for k, _, _ in items]
    if kinds != [6, 12] + ['C'] * 8 + [6, 6]:
        return None
    return i + 2, j, items


def fix_prp_out(out, rep=None):
    """ANP_RAPPEL_CB on every RappellingBox event in port_level's op list (in place). Returns boxes changed."""
    if not ENABLED or CB_MODE == 'keep':
        return 0
    n_changed = 0
    i = 0
    while i < len(out):
        p_, op_, v_ = out[i]
        if op_ & 0x7f == 12 and v_ == 'RappellingBox' and i + 1 < len(out) and out[i + 1][1] & 0x7f == 2:
            r = _box_fields(out, i)
            if r is None:
                _rep_add(rep, 'rappel: RappellingBox with an unexpected layout left as is')
                i += 1; continue
            start, end, items = r
            conts = [s for k, _, s in items if k == 'C']
            p1, p2 = conts[0:4], conts[4:8]
            if CB_MODE == 'swap':
                new = p2 + p1
            else:   # both
                new = p1 + p1
            if new == conts:
                i = end; continue
            # rebuild the body: bool, ref, 8 containers, bool, bool (op prefixes copied from the originals)
            body = [out[items[0][1]], out[items[1][1]]]
            cont_ops = [out[j] for k, j, _ in items if k == 'C']
            for q, strs in enumerate(new):
                cp, cop, _ = cont_ops[q]
                body.append((cp, cop, len(strs)))
                body.extend((0, 12, s) for s in strs)
            body += [out[items[10][1]], out[items[11][1]]]
            out[start:end] = body
            n_changed += 1
            used = sum(1 for s in p1 if s)
            _rep_add(rep, 'rappel: RappellingBox callbacks %s (Dead Men player-one lists in use %d/4)' % (CB_MODE, used))
            i = start + len(body)
            continue
        i += 1
    return n_changed


# ------------------------------------------------------------------------------------------------ CLI
def _scenes_dm():
    import anp_paths
    return os.path.join(anp_paths.WORK, 'scn', 'dm')


def census(levels=None):
    from scene import Scene
    d = _scenes_dm()
    lv = levels or sorted(x[:-9] for x in os.listdir(d) if x.endswith('_Main.prp') and 'FA' not in x)
    tot = 0
    for L in lv:
        S = Scene(os.path.join(d, L + '_Main'))
        def path(idx):
            p = []
            while idx:
                p.append(S.gms.ents[idx - 1]['name']); idx = S.nodes[idx]['parent']
            return '\\'.join(reversed(p))
        for node in S.nodes[1:]:
            for name, ev in node['events']:
                if name not in ('RappellingBox', 'RappelCheckPoint'):
                    continue
                tot += 1
                props = [v for _, op, v in node['props'] if op & 0x7f == 10]
                pos = props[9:12] if len(props) >= 12 else []
                size = props[-3:] if len(props) >= 15 else []
                print('%-5s ent %-6d %-16s %s' % (L, node['idx'] - 1, name, path(node['idx'])))
                print('       local pos %s size %s' % (['%.1f' % x for x in pos], ['%.1f' % x for x in size]))
                if name == 'RappellingBox':
                    fake = [(0, 12, 'RappellingBox'), (0, 2, None)] + list(ev) + [(0, 0x7e, None)]
                    r = _box_fields(fake, 0)
                    if r:
                        _, _, items = r
                        conts = [s for k, _, s in items if k == 'C']
                        print('       enabled=%d facing=%s last bools=%d,%d' % (items[0][2], items[1][2].split('\\')[-1], items[10][2], items[11][2]))
                        for q, lab in enumerate(('enter', 'leave', 'begin', 'end')):
                            if conts[q] or conts[q + 4]:
                                print('       %-5s P1 %s | P2 %s' % (lab, [s.split('\\')[-1] for s in conts[q]], [s.split('\\')[-1] for s in conts[q + 4]]))
    print('total', tot)


def check_zip(path):
    import zipfile
    from prp import PRP
    z = zipfile.ZipFile(path)
    anm = next((n for n in z.namelist() if n.lower().endswith('_main.anm')), None)
    prp = next((n for n in z.namelist() if n.lower().endswith('_main.prp')), None)
    if anm:
        rep_, nclips, size = player_clip_report(z.read(anm))
        print('ANM %s: %d clips, %d bytes' % (anm, nclips, size))
        for db, r in rep_.items():
            if r is None:
                print('  %-8s (no DB)' % db); continue
            miss = [n.decode()[len(PREFIX):] for n in PLAYER_CLIPS if r.get(n.decode()[len(PREFIX):]) is None]
            print('  %-8s %2d rappel paths%s' % (db, sum(1 for v in r.values() if v), ('  MISSING ' + ','.join(miss)) if miss else '  (player set complete)'))
    if prp:
        pr = PRP(z.read(prp))
        ops = list(pr.instrs())
        for i, (p_, op_, v_) in enumerate(ops):
            if op_ & 0x7f == 12 and v_ == 'RappellingBox':
                r = _box_fields(ops, i)
                if not r:
                    print('  RappellingBox @%d: unexpected layout' % i); continue
                conts = [s for k, _, s in r[2] if k == 'C']
                print('  RappellingBox facing=%s first-half=%s second-half=%s' % (
                    r[2][1][2].split('\\')[-1], [len(c) for c in conts[:4]], [len(c) for c in conts[4:]]))


def anm_cli(dd_path, dm_path):
    import anm_merge
    dd = open(dd_path, 'rb').read(); dm = open(dm_path, 'rb').read()
    base_pf = lambda p_: p_.startswith(b'/Level_Specific/') or p_.startswith(b'/Movement/Climb/')
    res = {}
    for lab, pf in (('without', base_pf), ('with', wrap_path_filter(base_pf))):
        merged, mrep = anm_merge.merge_report(dd, dm, None, None, 'start', path_filter=pf)
        rep = collections.Counter()
        fixed = ensure_player_clips(merged, rep)
        r0, n0, s0 = player_clip_report(merged)
        r1, n1, s1 = player_clip_report(fixed)
        res[lab] = (s0, n0, s1)
        print('== %s rappel filter: merged %d bytes, %d clips; after safety net %d bytes' % (lab, s0, n0, s1))
        for db in ('Kane', 'Lynch'):
            print('   %-6s merged: %s' % (db, {k: v for k, v in (r0[db] or {}).items() if v}))
            print('   %-6s final : %s' % (db, {k: v for k, v in (r1[db] or {}).items() if v}))
        for k, v in rep.items():
            print('   rep:', k, v)
    if 'with' in res and 'without' in res:
        print('ANM growth from the Dead Men rappel clips: %+d bytes (%+d clips)' % (res['with'][0] - res['without'][0], res['with'][1] - res['without'][1]))


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__)
    elif a[0] == 'census':
        census(a[1:] or None)
    elif a[0] == 'anm' and len(a) == 3:
        anm_cli(a[1], a[2])
    elif a[0] == 'check' and len(a) == 2:
        check_zip(a[1])
    else:
        print(__doc__)

# ---------------------------------------------------------------------------------------------- RE notes
# ZRappellingBox (both exes): +0x24 owner geom, +0x30 enabled (property 0; message 'AITrigger' sets it,
#   DD handler 0x87da50), +0x34 facing PosObject handle, +0x38..+0x44 player-slot-1 [enter, leave, begin, end],
#   +0x48..+0x54 everyone else, +0x58/+0x59 the two trailing bools (+0x59: Update 0x82552a branch).
#   Init (slot 14, DD 0x69aca0): list gameMgr+0x15b8 <- {geom handle, facing 3x3, box} (0x6bc690, 10 max);
#   enabled -> HUD use action 0x18 (0x452a60).
# ZFFPlayerMovementRappel (DD vt 0xbb5ebc, movement 0x10): TryActivate slot 14 0x673a20 (point lookup 0x4c47b0:
#   geom visible, box enabled, geom vt+0x170 contains the player; prompt 2 via 0x4c06c0; use -> 0x50a8f0(2)),
#   Activate slot 15 0x6db3b0 (Begin callback, Start clip, warp onto the facing), Update slot 17 0x825290
#   (state player+0x25c0: 0 start, 1 wait on wall, 2 jump loop, 3 jump, 4 jump end, 5 done -> End callback),
#   Deactivate slot 13 0x6165f0, clip ids slot 20 0x77ac70 (+0x1fe4 Start, +0x1fe6 Jump_Start,
#   +0x1fe8 Wait_On_Wall, +0x1fea Jump_Loop, +0x1fec Jump_End), state +0x1f64 active, +0x1f68 point entry,
#   +0x1f6c prompt shown, +0x1f6d started.
