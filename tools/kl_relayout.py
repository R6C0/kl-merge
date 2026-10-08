"""
Exact Dead Men -> Dog Days property relayout from the two exes' own property schemas
(re/schemas_dm.json, re/schemas_dd.json, made by kl_schema_infer.py).

For an object of class C, both games list C's properties base-class first, field by field, with
the token each one reads and (for enums) the enum's name. Fields are matched level by level
(ZGEOM to ZGEOM, ZSTDOBJ to ZSTDOBJ ...) on (token, enum name); a Dog Days field with no match
takes the game's typical value for that slot, a Dead Men field with no match is dropped.
"""
import os, json, difflib, struct

HERE = os.path.dirname(os.path.abspath(__file__))
_cache = {}


def load(game):
    if game not in _cache:
        for p in (os.path.join(HERE, 'schemas_%s.json' % game),
                  os.path.join(HERE, '..', 're', 'schemas_%s.json' % game)):
            if os.path.isfile(p):
                _cache[game] = json.load(open(p)); break
        else:
            _cache[game] = None
    return _cache[game]


def fields(game, cls):
    """[(owner, letter, enum-name or None, enum-options or None)] for a class, or None."""
    s = load(game)
    if not s or cls not in s['classes']:
        return None
    out = []
    for owner, recs in s['classes'][cls]['levels']:
        for r in recs:
            letter = s['loaders'].get(r['load'])
            if letter is None:
                return None                     # a loader whose token we never saw: don't guess
            e = r.get('enum')
            out.append((owner, letter, e['name'] if e else None, e['options'] if e else None))
    return out


def controller_class(game, name):
    s = load(game)
    return s['controllers'].get(name) if s else None


def class_name(game, tid):
    s = load(game)
    if not s:
        return None
    for name, c in s['classes'].items():
        if c['tid'] == tid:
            return name
    return None


def _label(f):
    owner, letter, en, _ = f
    return (owner, letter, en)


def unit_letter(u):
    op = u[0][0]
    if op == 0x01:
        inner = u[1:-1]
        kinds = sorted(set({0x0a: 'f', 0x09: 'I', 0x04: 'i', 0x0c: 's', 0x0e: 'e'}.get(t[0], '?') for t in inner))
        return '[' + '|'.join(kinds) + '*]' if kinds else '[f*]'
    return {0x04: 'i', 0x05: 'c', 0x06: 'b', 0x07: 'B', 0x08: 'h', 0x09: 'I', 0x0a: 'f',
            0x0b: 'd', 0x0c: 's', 0x0e: 'e', 0x0d: 'r', 0x0f: 'k'}.get(op, '?')


def align(dm_fields, dd_fields, dm_units):
    """-> list of (dd_field, dm_unit or None); None where Dog Days needs a default."""
    if len(dm_units) != len(dm_fields):
        return None
    # owners differ in naming between the games only rarely; align on the whole sequence but
    # make the level boundaries part of the key so fields never cross classes.
    a = [_label(f) for f in dm_fields]
    b = [_label(f) for f in dd_fields]
    # owner names can differ (e.g. ZIngameMapGroup vs ZGROUP): if no owner matches at all, drop it
    if not set(x[0] for x in a) & set(x[0] for x in b):
        a = [(None, l, e) for _, l, e in a]
        b = [(None, l, e) for _, l, e in b]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(a1 - a0):
                out.append((dd_fields[b0 + k], dm_units[a0 + k]))
        elif tag == 'replace' and (a1 - a0) == (b1 - b0) and all(a[a0 + k][1] == b[b0 + k][1] for k in range(a1 - a0)):
            # same token, different enum/owner: keep the value, the enum fixer checks it later
            for k in range(a1 - a0):
                out.append((dd_fields[b0 + k], dm_units[a0 + k]))
        else:
            for k in range(b0, b1):
                out.append((dd_fields[k], None))
    return out


def letters(fs):
    return ''.join(f[1] for f in fs)
