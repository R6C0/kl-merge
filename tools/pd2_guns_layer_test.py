#!/usr/bin/env python3
"""pd2_guns_layer_test.py - off-game checks of the layer parameterisation of pd2_guns_layer.py (no game files read, nothing baked):
the 1106b defaults, the 1106c layer (keys, tag, base stage, out folder), the installer text per layer and the key tables."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pd2_guns_layer as L
import pd2_guns_multi as M

fails = checks = 0


def check(c, msg):
    global fails, checks
    checks += 1
    if not c:
        fails += 1
        print('FAIL: ' + msg)


# default = 1106b, as before the parameterisation
check(L.LAYER == '1106b' and L.KEYS == ['C45', 'HRL50', 'HRL51'] and L.TAG == '.before-pd2guns1106b' and L.BASE is None, '1106b defaults')
check(L.src_root() == M.MAPROOT, '1106b is baked on the live maps')
check(os.path.basename(L.default_out()) == 'pd2guns_1106b', '1106b default out')
py_b = L.INSTALL_PY.replace('@TITLE@', L.LAYERS['1106b']['title']).replace('@TAG@', L.TAG)
check("TAG = '.before-pd2guns1106b'" in py_b and '@' not in py_b.replace('@echo', ''), '1106b installer text')

# every layer: keys exist in SPECS, a body detail is known, keys of different layers are disjoint, tags differ
spec_keys = {s['key'] for s in M.SPECS}
seen = set()
for name, lay in L.LAYERS.items():
    check(set(lay['keys']) <= spec_keys, '%s: keys are pd2_guns_multi SPECS' % name)
    check(set(lay['keys']) <= set(L.DETAIL), '%s: a body detail byte per key' % name)
    check(not (set(lay['keys']) & seen), '%s: keys disjoint from the other layers' % name)
    seen |= set(lay['keys'])
check(len({l['tag'] for l in L.LAYERS.values()}) == len(L.LAYERS), 'distinct backup tags')

# switch to 1106c and back
L.configure('1106c')
check(L.KEYS == ['R700', 'GL40', 'GL40GAS', 'GL40FLR'] and L.TAG == '.before-pd2guns1106c', '1106c keys / tag')
check(L.BASE == os.path.join(L.WORK_BUILD, 'pd2guns_1106b') and L.src_root() == L.BASE, '1106c is staged on the 1106b stage')
check(L.default_out().lower().startswith('d:'), '1106c default out is on D:')
py_c = L.INSTALL_PY.replace('@TITLE@', L.LAYERS['1106c']['title']).replace('@TAG@', L.TAG)
check("TAG = '.before-pd2guns1106c'" in py_c and '1106b' not in py_c.split('"""', 2)[2], '1106c installer text')
check(set(L.KEYS).isdisjoint(L.LAYERS['1106b']['keys']), '1106c adds keys, repeats none')
L.configure('1106b')
check(L.KEYS == ['C45', 'HRL50', 'HRL51'] and L.BASE is None, 'configure back to 1106b')

print('pd2_guns_layer_test: %d checks, %d FAIL' % (checks, fails))
sys.exit(1 if fails else 0)
