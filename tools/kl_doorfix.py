#!/usr/bin/env python3
r"""
Escape-lift doors (Retomoto Tower, 2026-10-23): name the four KEYFRAMED door leaves in the two MatPosAnimProxy
lists, not the two groups that hold them.

WHY (kl2.exe, read): the ZMatPosAnimProxy handler (0x7ed520) animates an array of MatPosAnim controllers that it
fills at init by sending 'GetMatPosAnim' to every node of its list (loop 0x409430, callback 0x7477c0). A plain
group node answers only through a RelayMessageList with delay 0 (0x6e3cb0) - unproven in the built map, and live the
doors never opened. Stock Dog Days proxies name the animated leaves directly (F01 AnimProxy_RearDoors_Open =
[0,0,27,[leaves],0,[],'AITrigger',0]). So the list becomes the leaves: DrExt_A, DrExt_B, DrInt_A, DrInt_B.

ON DISK a reference list is a count token (0x04) followed by that many string tokens (0x0c), each a key index into
the .prp's key table; the string is the node's full scene path ('ROOT\...\Name'), so a changed list may append new
keys to the table (Prp.key_index). Field 3 of the MatPosAnimProxy controller is that list; the other fields
([0, 0, 75, <list>, 0, [], 'AITrigger', 0]: frames 0..75, message 'AITrigger') are not touched.

    python kl_doorfix.py check <F06_Main.zip>                  -> what the two proxies hold (exit 1 if not expected)
    python kl_doorfix.py apply <in F06_Main.zip> <out F06_Main.zip>
        Only the *_Main.prp member is rewritten; every other member is copied RAW (same bytes, order, compression,
        timestamps). Refuses a proxy that is neither the group form nor the fixed form; a fixed zip is copied as is.
kl_fa_author.wire() calls fix_scene() so that FUTURE builds write the leaves.
"""
import hashlib, os, shutil, struct, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kl_fa
from kl_prp import units

R = 'ROOT\\'
PROXY_A = 'AI_Players!Enemies!070_Elevators!AnimProxy_OpenEscapeElevator'    # tower car, part A (M09_A)
PROXY_B = 'Mercenaries!VideoProxy!MatPosAnimProxy'                           # lobby car, part B (M09_B)
PROXIES = (PROXY_A, PROXY_B)
FRAMES = (0, 75)                # fields 1 / 2: first and last frame, kept
MESSAGE = 'AITrigger'           # field 6, kept


def _proxy(sc, name):
    """(node, controller index) of the MatPosAnimProxy at scene path ROOT\\name."""
    hit = sc.resolve(R + name)
    if len(hit) != 1:
        raise ValueError('%s: %d nodes (expected 1)' % (name, len(hit)))
    k = hit[0]
    ix = [i for i, (nm, _b) in enumerate(sc.nodes[k]['ctrls']) if sc.p.key(nm) == 'MatPosAnimProxy']
    if len(ix) != 1:
        raise ValueError('%s: %d MatPosAnimProxy controllers (expected 1)' % (name, len(ix)))
    return k, ix[0]


def _fields(sc, k, i):
    return [kl_fa.value(sc, u) for u in units(sc.nodes[k]['ctrls'][i][1][1:-1])]


def _animated(sc, j):
    return any(sc.p.key(nm) == 'MatPosAnim' for nm, _b in sc.nodes[j]['ctrls'])


def leaves(sc, groups):
    """Scene paths of the children that carry a MatPosAnim, group by group, in child order."""
    out = []
    for g in groups:
        hit = sc.resolve(g)
        if len(hit) != 1:
            raise ValueError('group %s resolves to %d nodes' % (g, len(hit)))
        node = sc.nodes[hit[0]]
        if _animated(sc, hit[0]):
            raise ValueError('%s carries a MatPosAnim itself: not the group form' % g)
        for c in node['children']:
            j = next(x for x in range(hit[0] + 1, sc.end[hit[0]]) if sc.nodes[x] is c)
            if _animated(sc, j):
                out.append(sc.path[j])
    for p in out:
        if len(sc.resolve(p)) != 1:
            raise ValueError('leaf path %s is not unique' % p)
    return out


def state(sc, name):
    """('groups' | 'leaves', current list, wanted leaf list) for the proxy `name`; ValueError if neither form."""
    k, i = _proxy(sc, name)
    v = _fields(sc, k, i)
    if len(v) != 8 or (v[1], v[2]) != FRAMES or v[6] != MESSAGE or not isinstance(v[3], list):
        raise ValueError('%s: not the expected [0,0,75,list,0,[],%r,0] form: %s' % (name, MESSAGE, v))
    cur = v[3]
    if cur and all(len(sc.resolve(s)) == 1 and _animated(sc, sc.resolve(s)[0]) for s in cur):
        want = cur                      # leaves already
        if len(cur) != 4:
            raise ValueError('%s: %d animated entries (expected 4)' % (name, len(cur)))
        return 'leaves', cur, cur
    want = leaves(sc, cur)
    if len(cur) != 2 or len(want) != 4:
        raise ValueError('%s: %d groups giving %d leaves (expected 2 giving 4)' % (name, len(cur), len(want)))
    return 'groups', cur, want


def fix_scene(sc, log=print):
    """Rewrite both proxies' lists to the four leaves. Returns the number of proxies changed (0 = already fixed)."""
    import kl_fa_author as A                     # setv: lazy, kl_fa_author imports this module
    changed = 0
    plan = [(n,) + state(sc, n) for n in PROXIES]           # check both BEFORE touching either
    for name, form, cur, want in plan:
        if form == 'leaves':
            log('  kl_doorfix: %s already names its 4 leaves' % name)
            continue
        k, i = _proxy(sc, name)
        kl_fa.edit(sc, k, i, lambda us, w=want: A.setv(sc, us, 3, w))
        log('  kl_doorfix: %s: %d groups -> %d leaves' % (name, len(cur), len(want)))
        changed += 1
    return changed


# ------------------------------------------------------------------ the archive
def _raw_copy(src_fp, zi, dst_zf):
    """Copy member zi byte for byte (local header, data, data descriptor) to dst_zf's end."""
    src_fp.seek(zi.header_offset)
    lh = src_fp.read(30)
    if lh[:4] != b'PK\x03\x04':
        raise ValueError('bad local header for %s' % zi.filename)
    n, m = struct.unpack('<HH', lh[26:30])
    body = lh + src_fp.read(n + m + zi.compress_size)
    if zi.flag_bits & 0x08:
        tail = src_fp.read(16)
        if tail[:4] != b'PK\x07\x08':
            raise ValueError('%s: data descriptor without signature, not handled' % zi.filename)
        body += tail
    new = zipfile.ZipInfo(zi.filename, zi.date_time)
    for a in ('compress_type', 'comment', 'extra', 'create_system', 'create_version', 'extract_version',
              'reserved', 'flag_bits', 'volume', 'internal_attr', 'external_attr', 'CRC', 'compress_size', 'file_size'):
        setattr(new, a, getattr(zi, a))
    new.header_offset = dst_zf.fp.tell()
    dst_zf.fp.write(body)
    dst_zf.start_dir = dst_zf.fp.tell()        # close() seeks here to write the central directory
    dst_zf.filelist.append(new)
    dst_zf.NameToInfo[new.filename] = new


def apply(src, dst, log=print):
    """src archive -> dst archive with the fixed .prp. Returns True if the .prp changed."""
    sc, _snd, _loc = kl_fa.load(src)
    with zipfile.ZipFile(src) as zf:
        prp_name = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
        old = zf.read(prp_name)
    if sc.p.serialize() != old:
        raise ValueError('%s: the .prp does not re-serialize byte for byte; refusing' % src)
    if not fix_scene(sc, log):
        shutil.copyfile(src, dst)
        return False
    data = sc.p.serialize()
    if os.path.exists(dst):
        os.remove(dst)
    with zipfile.ZipFile(src) as zin, open(src, 'rb') as sfp, zipfile.ZipFile(dst, 'w') as zout:
        for zi in zin.infolist():
            if zi.filename == prp_name:
                ni = zipfile.ZipInfo(zi.filename, zi.date_time)
                ni.compress_type, ni.external_attr, ni.create_system = zi.compress_type, zi.external_attr, zi.create_system
                ni.comment, ni.extra = zi.comment, zi.extra
                zout.writestr(ni, data)
            else:
                _raw_copy(sfp, zi, zout)
    return True


def sha1_members(path):
    with zipfile.ZipFile(path) as zf:
        return [(zi.filename, zi.compress_type, hashlib.sha1(zf.read(zi)).hexdigest()) for zi in zf.infolist()]


def main(a):
    if len(a) == 2 and a[0] == 'check':
        sc, _s, _l = kl_fa.load(a[1])
        for n in PROXIES:
            form, cur, want = state(sc, n)
            print('%s: %s, %d entries' % (n, form, len(cur)))
        return 0
    if len(a) == 3 and a[0] == 'apply':
        print('changed' if apply(a[1], a[2]) else 'already fixed (copied)')
        return 0
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
