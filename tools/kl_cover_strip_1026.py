#!/usr/bin/env python3
"""
TAKE THE KL_CoverSix! GROUP OUT OF A FINISHED MAP (2026-10-26). OFFLINE: reads a zip, writes a zip. Installs nothing.

    python kl_cover_strip_1026.py strip <zip> <out zip>

The inverse of kl_fa_cover.apply for the player-cover pass (kl_cover_1026): the top-level group 'KL_CoverSix!' and its boxes (CoverBoxH/M_K6_nn)
leave the .prp, .gms/.buf (kl_scene.remove, slot ids renumbered), the .oct / .rmi / .rmc (kl_octree.remap_ids with the group's slot ids dropped: the
root's group tree 3 entry and, for tier a boxes, their tree 0 items) and the .prm (model roots re-pointed at the .oct records that moved, as apply does).
Used by kl_cover_stage_1026 `--replace`: the live zip is stripped, a new group is planned on the result (with the floor + nav filter), and the
changed members are patched into the LIVE zip bytes. Same member-level patch as the other stage tools: nothing else in the zip changes.
Proved on the result: .prp re-serialises, .prp and .gms list the same entities, no dangling reference added, room sets unchanged
(kl_fa_bots.room_sets_check), the large blocks keep their size, no entity of the group is left.
"""
import json, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_gms
import kl_fa_bots as KB
import kl_octree as O
import kl_prpjoin as J
from kl_prp import Prp
import kl_cover_add as A_
import kl_cover_1026 as K

SEP = A_.SEP


def strip(src, log=print):
    """-> (members {name: bytes} that change, report dict), or (None, None) when the zip has no KL_CoverSix! group."""
    A_.use_slot(src)
    K.C.GROUP, K.C.TAG = K.GROUP, K.TAG
    B = KB.Built(src)
    sc = B.sc
    tops = [t for t in sc.tops() if sc.names[t] == K.NAME_GROUP]
    if not tops:
        return None, None
    if len([k for k in range(1, len(sc.nodes)) if sc.names[k] == K.NAME_GROUP]) != len(tops) or len(tops) != 1:
        raise ValueError('%s: expected exactly one top-level %s, found %d' % (src, K.NAME_GROUP, len(tops)))
    top = tops[0]
    gone_nodes = set(range(top, sc.end[top]))
    if any(sc.cls(k) not in ('ZGROUP', 'ZSTDOBJ') for k in gone_nodes):
        raise ValueError('the group holds something else than boxes: %s' % sorted({sc.cls(k) for k in gone_nodes}))
    same = J.join(sc, [(sc, t) for t in sc.tops()], 'same')
    if J.fingerprints(same)[0] != J.fingerprints(sc)[0] or J.text(same, same.p.settings) != J.text(sc, sc.p.settings):
        raise ValueError('kl_prpjoin.join does not reproduce the build\'s .prp')
    A = B.scene
    g0, b0 = A.write()
    if kl_gms.pack(g0) != B['.gms'] or b0 != B['.buf']:
        raise ValueError('kl_scene does not reproduce the build\'s .gms / .buf')
    octx, rmi, rmc = O.Oct.parse(B['.oct']), O.RoomIndex.parse(B['.rmi']), O.RoomIndex.parse(B['.rmc'])
    if octx.pack() != B['.oct'] or rmi.pack() != B['.rmi'] or rmc.pack() != B['.rmc']:
        raise ValueError('kl_octree does not reproduce the build\'s .oct / .rmi / .rmc')
    pre = KB.room_sets_check(A, octx, rmi, rmc)
    big0 = {e: len(B[e]) for e in KB.BIG}
    # ---- .prp
    Jn = J.join(sc, [(sc, t) for t in sc.tops()], 'uncover', skip={top})
    dang0, dang1 = J.dangling(sc), J.dangling(Jn)
    if len(dang1[0]) > len(dang0[0]) or len(dang1[1]) > len(dang0[1]):
        raise ValueError('new dangling references: %s' % (sorted(set(dang1[0]) - set(dang0[0]))[:5],))
    prp = Jn.p.serialize()
    back = Prp(prp)
    if back.serialize() != prp or len(back.nodes()) != len(Jn.nodes):
        raise ValueError('the new .prp does not round-trip')
    # ---- .gms / .buf
    slot0 = A.slots()
    gone_ents = set(B.ents[top - 1].walk())
    if len(gone_ents) != len(gone_nodes):
        raise ValueError('the .prp group has %d nodes, the .gms group %d entities' % (len(gone_nodes), len(gone_ents)))
    A.remove(B.ents[top - 1])
    faults = A.check()
    if faults:
        raise ValueError('kl_scene.check: %s' % faults[:3])
    allents = list(A.entities())
    if [e.name.decode('latin1') for e in allents] != Jn.names[1:] or [e.tid for e in allents] != Jn.tids[1:]:
        raise ValueError('the new .gms and .prp disagree on the entities')
    gms, buf = A.write()
    slot1 = A.slots()
    gids = {slot0[e] + 2 for e in gone_ents}
    ids = {slot0[e] + 2: slot1[e] + 2 for e in slot0 if e in slot1}
    ids[1] = 1
    octn, rmin, rmcn = O.remap_ids(octx, ids, gids), O.remap_ids(rmi, ids, gids), O.remap_ids(rmc, ids, gids)
    left = sum(1 for room in octn.rooms for t in room if t is not None for it in t.items if it[0] in gids)
    if left:
        raise ValueError('%d room-tree items still name a removed entity' % left)
    moved = sum(1 for a, b in ids.items() if a != b)
    move = {a: b for a, b in zip(octx.record_refs(), octn.record_refs()) if a != b}
    repointed, new_prm = 0, None
    if move:
        prm = bytearray(B['.prm'])
        tt, nn = struct.unpack_from('<II', prm, 0)
        old = set(octx.record_refs())
        for i in range(1, nn):
            off, size = struct.unpack_from('<II', prm, tt + 16 * i)
            if size == 64 and prm[off:off + 4] == b'\0\1\7\0':
                v = struct.unpack_from('<I', prm, off + 0x1c)[0]
                if v in move:
                    struct.pack_into('<I', prm, off + 0x1c, move[v])
                    repointed += 1
                elif v and v not in old:
                    raise ValueError('.prm chunk %d names an .oct record that is not there (%#x)' % (i, v))
        if not repointed:
            raise ValueError('%d .oct records moved and no model root names one' % len(move))
        new_prm = bytes(prm)
    post = KB.room_sets_check(A, octn, rmin, rmcn)
    if post != pre:
        raise ValueError('slot ids after the renumbering: %s (before: %s)' % (post, pre))
    new = dict(B.files)
    new[B.ext['.prp']], new[B.ext['.gms']], new[B.ext['.buf']] = prp, kl_gms.pack(gms), buf
    new[B.ext['.oct']], new[B.ext['.rmi']], new[B.ext['.rmc']] = octn.pack(), rmin.pack(), rmcn.pack()
    if new_prm is not None:
        new[B.ext['.prm']] = new_prm
    if big0 != {e: len(new[B.ext[e]]) for e in KB.BIG}:
        raise ValueError('a large block changed its size')
    repl = {n: new[n] for e, n in B.ext.items() if new[n] != B.files[n]}
    rep = {'entities_before': len(B.ents), 'entities': len(allents), 'removed': len(gone_ents), 'slot_ids_moved': moved, 'prm_roots_repointed': repointed,
           'members_changed': sorted(e for e, n in B.ext.items() if n in repl)}
    log('  stripped %s: %d entities removed (%d -> %d), %d slot ids renumbered, %d model roots re-pointed; members %s'
        % (K.NAME_GROUP, len(gone_ents), len(B.ents), len(allents), moved, repointed, rep['members_changed']))
    return repl, rep


def main():
    a = sys.argv[1:]
    if len(a) != 3 or a[0] != 'strip':
        sys.exit(__doc__)
    import kl_loot_1025 as LO
    repl, rep = strip(a[1])
    if repl is None:
        sys.exit('no %s group in %s' % (K.NAME_GROUP, a[1]))
    LO.patch_zip(a[1], a[2], repl)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
