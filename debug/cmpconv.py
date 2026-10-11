"""Our kl_convert against luvsic's converter on one Dead Men level: per class, how many nodes come out with other tokens."""
import sys, zipfile, struct, collections, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'c:\kl-merge\kl-merge\tools')
import kl_snd, kl_gms, kl_rtp
import kl_prpjoin as J
import kl_convert as K
from kl_prp import Prp

LEVEL, HIS = sys.argv[1], sys.argv[2]
src = J.Scene.load(LEVEL, 'dm')
data, _st = K.convert_level(kl_snd.member(LEVEL, '_Main.prp', 'dm'), K.converter(kl_snd.game_dir('dd'), kl_snd.workdir()), src.tids)
ours = J.Scene(Prp(data), src.names, src.tids, 'dd', LEVEL)

with zipfile.ZipFile(HIS) as zf:
    prp = [n for n in zf.namelist() if n.lower().endswith('_main.prp')][0]
    hp = Prp(zf.read(prp)); raw = kl_gms.unpack(zf.read(prp[:-4] + '.gms')); buf = zf.read(prp[:-4] + '.buf')
names, tids = ['ROOT'], [kl_rtp.ROOT_TYPE]
for decl, tid, _p in kl_gms.entities(raw):
    o = struct.unpack_from('<I', raw, 4 * (decl & 0xffffff))[0]
    names.append(buf[o:buf.index(b'\0', o)].decode('latin1')); tids.append(tid)
his = J.Scene(hp, names, tids, 'dd', 'his')
print('ours: %d nodes; his: %d nodes (he grafts %d more)' % (len(ours.nodes), len(his.nodes), len(his.nodes) - len(ours.nodes)))
n = min(len(ours.nodes), len(src.names))
same_names = sum(ours.names[k] == his.names[k] for k in range(1, n))
print('names equal on the first %d nodes: %d' % (n - 1, same_names))


def key(sc, toks):
    """tokens with string / reference keys resolved to text, so that two files with other key tables compare"""
    out = []
    for op, pl in toks:
        if op == 0x0c:
            out.append((op, sc.p.keys[struct.unpack('<I', pl)[0]]))
        elif op == 0x0f:
            out.append((op, tuple(sc.p.keys[i] for i in struct.unpack_from('<%dI' % (len(pl) // 4 - 1), pl, 4))))
        else:
            out.append((op, bytes(pl)))
    return out


cls_tot, cls_diff, type_diff, ctrl_diff = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
ex = {}
for k in range(1, n):
    if ours.names[k] != his.names[k]:
        continue
    c = ours.cls(k) or hex(ours.tids[k])
    cls_tot[c] += 1
    if ours.tids[k] != his.tids[k]:
        type_diff[(c, his.cls(k) or hex(his.tids[k]))] += 1
        continue
    a, b = key(ours, ours.nodes[k]['props']), key(his, his.nodes[k]['props'])
    if a != b:
        cls_diff[c] += 1
        if c not in ex:
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            ex[c] = (ours.names[k][-60:], i, len(a), len(b), str(a[i:i + 2])[:110], str(b[i:i + 2])[:110])
    ca = {nm: key(ours, body) for nm, body in ours.nodes[k]['ctrls']}
    cb = {nm: key(his, body) for nm, body in his.nodes[k]['ctrls']}
    for nm in set(ca) | set(cb):
        if ca.get(nm) != cb.get(nm):
            ctrl_diff[(nm, 'only ours' if nm not in cb else 'only his' if nm not in ca else 'differs')] += 1
print('\nnodes whose own object differs, by class (differ / total):')
for c, d in cls_diff.most_common(40):
    e = ex[c]
    print('  %-34s %6d / %-6d  e.g. ...%s token %d (len %d / %d)\n        ours %s\n        his  %s' % (c, d, cls_tot[c], e[0], e[1], e[2], e[3], e[4], e[5]))
print('\nclasses that come out the same on every node: %d of %d' % (sum(1 for c in cls_tot if not cls_diff[c]), len(cls_tot)))
print('\ntype id differs (ours -> his):', dict(type_diff.most_common(20)))
print('\ncontrollers that differ:')
for (nm, how), d in ctrl_diff.most_common(40):
    print('  %-40s %-10s %d' % (nm, how, d))
