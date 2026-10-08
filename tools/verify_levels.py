#!/usr/bin/env python3
"""
Convert the Fragile Alliance maps and check every converted object against Dog Days.

    python verify_levels.py [M01_FA_A ...]

For each level this writes <work folder>/converted/<level>/<base>_Main.prp and then checks, with
the class schemas read from kl2.exe (re/kl2.json):
  * every node and controller has exactly the fields Dog Days reads for its class (the class a
    node gets is the one kl_gms.convert gives its .gms record)
  * every enum value and flag exists in Dog Days' enum for that field
  * every controller is one Dog Days registers
  * no item is bound twice (the engine asserts on a second InventoryBinding of an item)
The last line per level must say "problems: 0" before a build is installed.
"""
import collections, os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_convert as K
from kl_prp import Prp, units
from kl_port_check import find, workdir, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE


def problems(conv, data, tids):
    """Counter of what is wrong with a converted .prp, given the Dead Men class ids of its nodes."""
    dd, prob = conv.dd, collections.Counter()
    p = Prp(data)
    def check(cls, obj, who):
        why = dd.misfit(cls, obj)
        if why:
            prob['%s: %s' % (who, why)] += 1
            return
        for f, u in zip(dd.fields(cls), units(K.body(obj))):
            if f.kind in ('e', 'k'):
                names = [p.key(u[0])] if f.kind == 'e' else K._resolve(p, u)[0][1][1:]
                for n in names:
                    if n not in conv.options[f.enum]:
                        prob['%s: %s is not in enum %s' % (who, n, dd.enums[f.enum]['name'])] += 1
    items = collections.Counter()
    for k, (tid, node) in enumerate(zip(tids, p.nodes())):
        cls = dd.geoms.get(tid if k == 0 else K.RETYPE.get(tid, tid))
        if cls is None:
            prob['node type %#x is not a Dog Days class' % tid] += 1
            continue
        check(cls, node['props'], 'node ' + cls)
        for name, obj in node['ctrls']:
            nm = p.key(name)
            impl = dd.controller(nm, cls)
            if impl is None:
                prob['controller %s is not registered by Dog Days' % nm] += 1
                continue
            check(impl, obj, 'controller ' + nm)
            if nm == 'InventoryBinding':
                item = [p.key(t) for t in obj if t[0] == 0x0e][0]
                items[item] += item != 'eFF2ItemNoItem'
    dup = {k: v for k, v in items.items() if v > 1}
    if dup:
        prob['items bound more than once: %s' % dup] += 1
    return prob


def main():
    dm, dd = find(DM_GUESSES, DM_EXE), find(DD_GUESSES, DD_EXE)
    if not dm or not dd:
        raise SystemExit('Could not find both games; edit DM_GUESSES / DD_GUESSES in kl_port_check.py')
    work = workdir()
    conv = K.converter(dd, work)
    total = 0
    for lv in sys.argv[1:] or K.FA_LEVELS:
        base = lv.replace('_', '')
        n = 'Scenes/Locations/%s/%s_Main.prp' % (lv, base)
        with zipfile.ZipFile(os.path.join(dm, 'Scenes', 'Locations', lv, base + '_Main.zip')) as zf:
            tids = K.node_types(zf, n)
            out, st = K.convert_level(zf.read(n), conv, tids)
        od = os.path.join(work, 'converted', lv)
        os.makedirs(od, exist_ok=True)
        open(os.path.join(od, base + '_Main.prp'), 'wb').write(out)
        prob = problems(conv, out, tids)
        total += sum(prob.values())
        print(lv, dict(st))
        print('  problems:', sum(prob.values()), prob.most_common(12))
    for what, c in sorted(conv.report.items()):
        print('%s: %s' % (what, c.most_common(60)))
    print('assumed pairings (a new field next to same-typed ones): %s' % sorted(conv.assumed))
    return total


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
