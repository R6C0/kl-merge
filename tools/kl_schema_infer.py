"""
Work out what each RTP load function reads (the .prp token letter) by lining the exe's exact
property schemas up against objects in the game's own levels. Writes schemas_<game>.json:
  { "loaders": {load_va: letter}, "classes": {name: [field...]}, "controllers": {name: class} }
Run from KL_PortTools on the PC:  python kl_schema_infer.py dd|dm
"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import kl_convert as K
from kl_schema import Schema
from kl_port_check import exe_classes, find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

game = sys.argv[1]
root = sys.argv[2] if len(sys.argv) > 2 else (find(DM_GUESSES, DM_EXE) if game == 'dm' else find(DD_GUESSES, DD_EXE))
exe = os.path.join(root, DM_EXE if game == 'dm' else DD_EXE)
S = Schema(exe)
classes, _ = exe_classes(exe)                     # tid -> (registered name, size)
ref = K.DDReference(root)
votes = collections.defaultdict(collections.Counter)
samples = {}

def learn(cls, sigs, what):
    fields = S.fields(cls)
    if fields is None:
        return 'noschema'
    ok = False
    for sg in sigs:
        # csig is '{' + letters + '}' with arrays as [..] -> collapse each unit to one symbol
        us, i, inner = [], 0, sg[1:-1]
        while i < len(inner):
            if inner[i] == '[':
                j = inner.index(']', i); us.append(inner[i:j + 1]); i = j + 1
            else:
                us.append(inner[i]); i += 1
        if len(us) != len(fields):
            continue
        ok = True
        for u, f in zip(us, fields):
            votes[f['load']][u] += 1
    return 'ok' if ok else 'len-mismatch'

stats = collections.Counter()
for tid, sigs in ref.cls.items():
    name = classes.get(tid, (None,))[0]
    if not name:
        stats['class-unregistered'] += 1; continue
    cls = name if name in S.by_name else None
    if cls is None:
        stats['class-no-rtti:' + name] += 1; continue
    stats['class-' + learn(cls, sigs, name)] += 1
ctrl = S.controllers()
for name, sigs in ref.ctrl.items():
    cls = ctrl.get(name)
    if not cls:
        stats['ctrl-unknown'] += 1; continue
    stats['ctrl-' + learn(cls, sigs, name)] += 1
print(dict(stats))
loaders, conflicts = {}, {}
for load, c in votes.items():
    best, n = c.most_common(1)[0]
    loaders['%#x' % load] = best
    if len(c) > 1:
        conflicts['%#x' % load] = dict(c)
print('loaders', loaders)
print('conflicts', conflicts)
out = {'exe': os.path.basename(exe), 'loaders': loaders, 'conflicts': conflicts, 'controllers': ctrl, 'classes': {}}
for tid, (name, size) in classes.items():
    ch = S.chain(name)
    if ch is None:
        continue
    out['classes'][name] = {'tid': tid, 'levels': [(o, [{'load': '%#x' % r['load'], 'enum': r['enum']} for r in recs]) for o, recs in ch]}
for name, cls in ctrl.items():
    ch = S.chain(cls)
    if ch is not None and cls not in out['classes']:
        out['classes'][cls] = {'tid': None, 'levels': [(o, [{'load': '%#x' % r['load'], 'enum': r['enum']} for r in recs]) for o, recs in ch]}
json.dump(out, open(os.path.join(HERE, 'schemas_%s.json' % game), 'w'), indent=0)
print('wrote schemas_%s.json: %d classes' % (game, len(out['classes'])))
