#!/usr/bin/env python3
"""
Property schemas of the Glacier 1 engine, read from the game executable.

A level property file (.prp) is positional: an object holds each serialized property of its
class in a fixed order, with no names. The engine knows that order from its run-time property
reflection ("RTP"). This module reads the same tables out of kl2.exe / kaneandlynch.exe, so the
exact field list of every class is known instead of being inferred from level files.

The method is HHCHunter's, from hbm-editor (packages/formats/src/rtp), which does this for
Hitman: Blood Money. Kane & Lynch differs only where noted:

  class vtable slot 11 (12 in Blood Money) is GetProperties: "mov eax, <ZPropertyInfo>; ret"
  ZPropertyInfo { +0 first record, +4 super ZPropertyInfo, +8 name }
  record        { +0 next, +4 name (0 in retail), +8 filter, +0xC type handler, ... }
                enum records carry a ZEnumInfo* (+0x14 in member records, +0x20 in accessor ones)
  type handler  { load function, save function }: 8 bytes each, all in one table
  ZEnumInfo     { +0 last entry, +4 name, +8 value size }; entry { +0 previous, +4 value, +8 name }

The engine loads the super chain first, then the class's own records in order, skipping records
whose filter lacks bit 0 (the level-file content bit).

Geometry classes are registered with a type id (kl_port_check.exe_classes) under the name of
their C++ class. Controllers are created by name: the exe exports one ZROUTCLASSINFO per
controller ("?<Owner>_<Name>_ClassInfo@@3VZROUTCLASSINFO@@A"); its static initializer stores the
controller name and the owner class, and the factory entry it is copied into is followed by the
Create function, whose constructors stamp the vtable of the implementing class.

What a type handler reads from the stream is not decoded from machine code. It is learned from
the game's own levels: every object of every stock level has to fit its class exactly, which is
also the proof that the tables were read correctly. Shapes use kl_prp.kind() notation.

    python kl_rtp.py            both games -> re/kaneandlynch.json, re/kl2.json
    python kl_rtp.py dd | dm    one game
"""
import collections, json, os, re, struct, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_exe import Exe
from kl_prp import Prp, units, kind
import kl_gms
from kl_port_check import exe_classes, level_zips, find, DM_GUESSES, DD_GUESSES, DM_EXE, DD_EXE

GET_PROPERTIES = 11          # vtable slot of RTP::cBase::GetProperties
LEVEL_FILES = 1              # a record is stored in level files when its filter has this bit
ROOT_TYPE = 0x100021         # the scene root is a ZROOM and has no .gms record
RE_DIR = os.path.join(os.path.dirname(HERE), 're')
GAMES = {'dm': (DM_GUESSES, DM_EXE), 'dd': (DD_GUESSES, DD_EXE)}
CLASSINFO = re.compile(r'^\?(.+)_ClassInfo@@3VZROUTCLASSINFO@@A$')


class Reflect:
    """The reflection tables of one executable."""

    def __init__(self, path):
        self.exe = Exe(path)
        self.rtti = self.exe.rtti()
        self.geoms = exe_classes(path)[0]            # type id -> (class name, instance size)
        self._records, self._owner, self._ctrls, self._md = {}, None, None, None

    def head(self, cls):
        """The ZPropertyInfo a class's GetProperties returns, or None."""
        vt = self.rtti.by_name.get(cls)
        if vt is None or 'RTP::cBase' not in self.rtti.bases[cls]:
            return None
        fn = self.exe.u32(vt + 4 * GET_PROPERTIES)
        body = self.exe.read(fn, 6) if fn else None
        if not body or len(body) < 6 or body[0] != 0xb8 or body[5] != 0xc3:
            return None
        return struct.unpack_from('<I', body, 1)[0]

    def chain(self, head):
        """ZPropertyInfo addresses from the base class down to `head`."""
        out = []
        while head and head not in out and len(out) < 32:
            out.append(head)
            head = self.exe.u32(head + 4)
        return out[::-1]

    def records(self, head):
        """(record address, filter, type handler address) of one ZPropertyInfo, in load order."""
        if head not in self._records:
            u32, out, seen = self.exe.u32, [], set()
            node = u32(head)
            while node and node not in seen:
                seen.add(node)
                flt, handler = u32(node + 8), u32(node + 12)
                if flt is None or handler is None or u32(handler) is None:
                    raise ValueError('broken property record at %#x' % node)
                out.append((node, flt, handler))
                node = u32(node)
            self._records[head] = out
        return self._records[head]

    def fields(self, cls):
        """Level-file records of a class, base class first, or None if it has no schema."""
        head = self.head(cls)
        if head is None:
            return None
        return [r for h in self.chain(head) for r in self.records(h) if r[1] & LEVEL_FILES]

    def owner(self, head):
        """The class that registered a property list: the least derived one returning it."""
        if self._owner is None:
            self._owner = {}
            for cls, chain in self.rtti.bases.items():
                h = self.head(cls)
                cur = self._owner.get(h)
                if h and (cur is None or len(chain) < len(self.rtti.bases[cur])):
                    self._owner[h] = cls
        return self._owner.get(head)

    def enum(self, va):
        """ZEnumInfo at va -> (name, value size, [(option, value)] in declaration order), or None."""
        u32, cstr = self.exe.u32, self.exe.cstr
        if not va or u32(va) is None:
            return None
        name, size = cstr(u32(va + 4)), u32(va + 8)
        if not name or size not in (1, 2, 4):
            return None
        options, entry, seen = [], u32(va), set()
        while entry:
            value, text = u32(entry + 4), cstr(u32(entry + 8) or 0)
            if entry in seen or value is None or text is None:
                return None
            seen.add(entry)
            options.append((text, value))
            entry = u32(entry)
        return name, size, options[::-1]

    def enum_of(self, record, handler):
        """Address of the ZEnumInfo of an enum or flag-set record, or None."""
        for slot in (0x14, 0x20):                       # member record, accessor record
            va = self.exe.u32(record + slot)
            if self.enum(va):
                return va
        # flag-set loaders that are specific to one enum push its info before calling the reader
        body = self.exe.read(self.exe.u32(handler), 0x40) or b''
        for j in range(len(body) - 4):
            if body[j] == 0x68:
                va = struct.unpack_from('<I', body, j + 1)[0]
                if self.enum(va):
                    return va
        return None

    def _scan(self, fn):
        """One function, walked along its branches from the entry (Dead Men's compiler leaves no
        padding between functions, so its end cannot be found by scanning bytes).
        Returns (classes whose vtable it stores at the start of an object, called functions,
        functions it jumps to)."""
        if self._md is None:
            import capstone                         # only needed to build the schemas, not to use them
            self._md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        exe, vts = self.exe, self.rtti.by_vtable
        own, calls, tails, seen, todo = [], [], [], set(), [fn]
        while todo and len(seen) < 3000:
            va = todo.pop()
            while va not in seen:
                ins = next(self._md.disasm(exe.read(va, 16) or b'', va), None)
                if ins is None:
                    break
                seen.add(va)
                m, target = ins.mnemonic, None
                if ins.op_str.startswith('0x') and (m == 'call' or m[0] == 'j'):
                    target = int(ins.op_str, 16)
                if m == 'mov' and ins.bytes[0] == 0xc7 and ins.size == 6:       # mov dword ptr [reg], imm32
                    cls = vts.get(struct.unpack_from('<I', ins.bytes, 2)[0])
                    if cls:
                        own.append((va, cls))
                elif m == 'call' and target is not None:
                    calls.append(target)
                elif m == 'jmp':
                    if target is not None and abs(target - fn) < 0x1000:
                        todo.append(target)
                    elif target is not None:
                        tails.append(target)
                    break
                elif m[0] == 'j' and target is not None:
                    todo.append(target)                 # conditional: both ways
                elif m in ('ret', 'retf', 'int3'):      # an inline assert's int3 is jumped over
                    break
                va += ins.size
        return [c for _va, c in sorted(own)], calls, tails

    def _stamped(self, fn):
        """Classes a Create function constructs: the vtables it stores itself, or, when the
        constructor is not inlined, the ones its callees store."""
        own, calls, tails = self._scan(fn)
        for _ in range(4):                              # thunks: jmp <the real function>
            if own or calls or len(tails) != 1:
                break
            own, calls, tails = self._scan(tails[0])
        return own or [c for t in calls[:8] for c in self._scan(t)[0]]

    def controllers(self):
        """Controller name -> [(owner geometry class, implementing class, instance size)]."""
        if self._ctrls is not None:
            return self._ctrls
        exe, bases = self.exe, self.rtti.bases
        code, cva = exe.code()
        out, self.unresolved = collections.defaultdict(list), []
        for sym, info in sorted(exe.exports().items(), key=lambda kv: kv[1]):
            if not CLASSINFO.match(sym or ''):
                continue
            key = struct.pack('<I', info)
            # push 0; push <size>; push ?; push <full name>; mov ecx, <info>; call <constructor>
            # mov [info+0x20], <name>; mov [info+0x24], <owner class>; ...
            p = code.find(b'\xb9' + key + b'\xe8')
            size, stored = None, {}
            if p >= 12 and code[p - 5] == 0x68 and code[p - 7] == 0x6a:
                if code[p - 12] == 0x68:
                    size = struct.unpack_from('<I', code, p - 11)[0]
                elif code[p - 9] == 0x6a:
                    size = code[p - 8]
                for m in re.finditer(rb'\xc7\x05(....)(....)', code[p:p + 0x60], re.S):
                    addr, imm = struct.unpack('<II', m.group(1) + m.group(2))
                    stored[addr - info] = imm
            name, owner = exe.cstr(stored.get(0x20, 0)), exe.cstr(stored.get(0x24, 0))
            # mov esi, <info>; mov edi, <factory entry>: 13 dwords are copied in front of {name, Create}
            q = code.find(b'\xbe' + key + b'\xbf')
            create = exe.u32(struct.unpack_from('<I', code, q + 6)[0] + 0x38) if q >= 0 else None
            stamped = [c for c in self._stamped(create) if 'RTP::cBase' in bases[c]] if create else []
            if not (name and owner and stamped):
                self.unresolved.append(sym)
                continue
            impl = max(stamped, key=lambda c: len(bases[c]))        # the most derived class stamped
            out[name].append((owner, impl, size))
        self._ctrls = dict(out)
        return self._ctrls

    def controller(self, name, node_cls):
        """Implementing class of controller `name` on a node of class `node_cls`, or None."""
        entries = self.controllers().get(name)
        if not entries:
            return None
        chain = self.rtti.bases.get(node_cls, [node_cls])
        fits = [e for e in entries if e[0] in chain]
        if fits:
            return min(fits, key=lambda e: chain.index(e[0]))[1]    # the closest owner wins
        return entries[0][1] if len(set(e[1] for e in entries)) == 1 else None


def learn(reflect, game, log=print):
    """Fit every object of every stock level to its class.
    Returns (load function -> {kind: count}, counters, misfits)."""
    shapes = collections.defaultdict(collections.Counter)
    stats, misfits, cache = collections.Counter(), collections.Counter(), {}
    unregistered = collections.Counter()          # controller names levels use but the exe never registers
    u32 = reflect.exe.u32

    def fit(cls, obj, what):
        if cls not in cache:
            cache[cls] = reflect.fields(cls)
        us = units(obj[1:-1])
        if cache[cls] is None or len(us) != len(cache[cls]):
            misfits[what] += 1
            return
        for (_rec, _flt, handler), u in zip(cache[cls], us):
            shapes[u32(handler)][kind(u)] += 1

    zips = sorted(level_zips(game))
    for k, z in enumerate(zips, 1):
        print('\r  fitting stock levels %d/%d' % (k, len(zips)), end='', flush=True)
        with zipfile.ZipFile(z) as zf:
            names = set(zf.namelist())
            for n in sorted(names):
                if not n.lower().endswith('.prp'):
                    continue
                if n[:-4] + '.gms' not in names:
                    stats['property files without a scene file'] += 1
                    continue
                p = Prp(zf.read(n))
                nodes = p.nodes()
                tids = [ROOT_TYPE] + [e[1] for e in kl_gms.entities(kl_gms.unpack(zf.read(n[:-4] + '.gms')))]
                if len(tids) != len(nodes):
                    stats['property/scene files that disagree on node count'] += 1
                    continue
                stats['levels'] += 1
                for tid, node in zip(tids, nodes):
                    stats['nodes'] += 1
                    cls = reflect.geoms.get(tid, (None,))[0]
                    if cls is None:
                        misfits['node of unregistered type %#x' % tid] += 1
                        continue
                    fit(cls, node['props'], 'node ' + cls)
                    for name, obj in node['ctrls']:
                        stats['controllers'] += 1
                        nm = p.key(name)
                        impl = reflect.controller(nm, cls)
                        if impl is not None:
                            fit(impl, obj, 'controller %s (%s)' % (nm, impl))
                        elif nm not in reflect.controllers():
                            unregistered[nm] += 1     # the engine skips these (stock levels have them)
                        else:
                            misfits['controller %s on %s (no class)' % (nm, cls)] += 1
    print()
    return shapes, stats, misfits, unregistered


def shape_of(kinds):
    """One on-disk shape from the kinds seen at a type handler's positions, or None if they clash.
    An empty reference list and an empty raw block are both a lone zero count ('cont')."""
    ks = set(kinds)
    if len(ks) == 1:
        return next(iter(ks))
    for full in ('refs', 'raw'):
        if ks == {'cont', full}:
            return full
    return None


def build(game, exe_name, log=print):
    """Everything the converter needs from one game, as plain data for re/<exe>.json."""
    path = os.path.join(game, exe_name)
    r = Reflect(path)
    log('%s: %d classes with RTTI, %d registered geometry classes' % (exe_name, len(r.rtti.by_name), len(r.geoms)))
    ctrls = r.controllers()
    log('  controllers: %d names, %d not resolved %s' % (len(ctrls), len(r.unresolved), r.unresolved[:6]))
    shapes, stats, misfits, unregistered = learn(r, game, log)
    log('  %s' % dict(stats))
    log('  objects that do not fit their class: %d %s' % (sum(misfits.values()), misfits.most_common(12)))
    log('  controllers used by stock levels but not registered by the exe: %s' % dict(unregistered))

    classes = sorted(c for c in r.rtti.by_name if r.head(c) is not None)
    heads = sorted(set(h for c in classes for h in r.chain(r.head(c))))
    # a list registered by an abstract class has no vtable to name it: use the name the
    # ZPropertyInfo carries, else the least derived class that inherits it
    heir = {}
    for c in classes:
        rank = (len(r.rtti.bases[c]), c)
        for h in r.chain(r.head(c)):
            if r.owner(h) is None and (h not in heir or rank < heir[h]):
                heir[h] = rank
    owner = lambda h: r.owner(h) or r.exe.cstr(r.exe.u32(h + 8)) or '(base of %s)' % heir[h][1]
    handlers = [rec[2] for h in heads for rec in r.records(h)]
    lo, hi = min(handlers), max(handlers)
    types, clash = [], []
    for handler in range(lo, hi + 8, 8):
        load = r.exe.u32(handler)
        seen = shapes.get(load, {})
        shape = shape_of(seen) if seen else None
        if seen and shape is None:
            clash.append((hex(load), dict(seen)))
        types.append({'load': '%#x' % load, 'kind': shape, 'seen': sum(seen.values())})
    if clash:
        log('  !! type handlers seen with more than one shape: %s' % clash)

    enums, levels, missing_enum = {}, {}, 0
    for h in heads:
        props = []
        for rec, flt, handler in r.records(h):
            t = (handler - lo) // 8
            e = None
            if types[t]['kind'] in ('e', 'k'):
                e = r.enum_of(rec, handler)
                if e is None:
                    missing_enum += 1
                else:
                    name, size, options = r.enum(e)
                    enums['%#x' % e] = {'name': name, 'size': size, 'options': options}
            props.append([flt, t, '%#x' % e if e else None])
        sup = r.exe.u32(h + 4)
        levels['%#x' % h] = {'owner': owner(h), 'super': '%#x' % sup if sup else None, 'props': props}
    if missing_enum:
        log('  !! enum records without a readable ZEnumInfo: %d' % missing_enum)

    return {
        'exe': {'file': exe_name, 'timestamp': '%#x' % r.exe.timestamp, 'bytes': len(r.exe.d)},
        'proof': {'stats': dict(stats), 'misfits': dict(misfits), 'controllers_unresolved': r.unresolved,
                  'handler_shape_clashes': len(clash), 'enum_records_without_info': missing_enum},
        'unregistered': dict(unregistered),
        'get_properties_slot': GET_PROPERTIES,
        'types': types,
        'enums': dict(sorted(enums.items())),
        'levels': levels,
        'classes': {c: {'info': '%#x' % r.head(c), 'bases': r.rtti.bases[c][1:]} for c in classes},
        'geoms': {'%#x' % t: [n, s] for t, (n, s) in sorted(r.geoms.items())},
        'controllers': {n: [list(e) for e in es] for n, es in sorted(ctrls.items())},
    }


def write(path, data):
    """JSON with one line per class / record list / enum, so diffs between builds stay readable."""
    one = lambda v: json.dumps(v, separators=(',', ':'))
    with open(path, 'w', newline='\n') as f:
        f.write('{\n')
        keys = list(data)
        for i, k in enumerate(keys):
            v, comma = data[k], ',' if i < len(keys) - 1 else ''
            if isinstance(v, dict) and v and all(isinstance(x, (dict, list)) for x in v.values()):
                f.write(' %s: {\n%s\n }%s\n' % (json.dumps(k), ',\n'.join('  %s: %s' % (json.dumps(a), one(b)) for a, b in v.items()), comma))
            elif isinstance(v, list) and v and isinstance(v[0], (dict, list)):
                f.write(' %s: [\n%s\n ]%s\n' % (json.dumps(k), ',\n'.join('  ' + one(b) for b in v), comma))
            else:
                f.write(' %s: %s%s\n' % (json.dumps(k), one(v), comma))
        f.write('}\n')


# owner: the class that registered the field; kind: its shape on disk (kl_prp.kind);
# enum: key into Schema.enums for enums and flag sets; type: type handler index;
# key: "<ZPropertyInfo>:<record index>", the same for every class that inherits the field
Field = collections.namedtuple('Field', 'owner kind enum type key')


class Schema:
    """Schemas of one game, as saved by this script in re/<exe>.json."""

    def __init__(self, data):
        self.data = data
        self.types, self.enums = data['types'], data['enums']
        self.geoms = {int(t, 16): n for t, (n, _s) in data['geoms'].items()}
        self.controllers = data['controllers']
        self.unregistered = data['unregistered']    # controller names stock levels carry anyway
        self._fields = {}

    @classmethod
    def load(cls, game):
        """game: 'dd' or 'dm'."""
        name = os.path.splitext(GAMES[game][1])[0] + '.json'
        with open(os.path.join(RE_DIR, name)) as f:
            return cls(json.load(f))

    def bases(self, cls):
        return [cls] + self.data['classes'][cls]['bases'] if cls in self.data['classes'] else [cls]

    def fields(self, cls):
        """Level-file fields of a class, base class first, or None if the game has no such class."""
        if cls not in self._fields:
            info = self.data['classes'].get(cls)
            out = None
            if info:
                chain, h = [], info['info']
                while h:
                    chain.append(h)
                    h = self.data['levels'][h]['super']
                out = [Field(self.data['levels'][h]['owner'], self.types[t]['kind'], e, t, '%s:%d' % (h, i))
                       for h in reversed(chain)
                       for i, (flt, t, e) in enumerate(self.data['levels'][h]['props']) if flt & LEVEL_FILES]
            self._fields[cls] = out
        return self._fields[cls]

    def controller(self, name, node_cls):
        """Implementing class of controller `name` on a node of class `node_cls`, or None."""
        entries = self.controllers.get(name)
        if not entries:
            return None
        chain = self.bases(node_cls)
        fits = [e for e in entries if e[0] in chain]
        if fits:
            return min(fits, key=lambda e: chain.index(e[0]))[1]
        return entries[0][1] if len(set(e[1] for e in entries)) == 1 else None

    def misfit(self, cls, obj):
        """Why an object's tokens (braces included) do not fit class `cls`, or None if they do.
        A stock level never returns anything but None here; a converted one must not either,
        because the engine reads exactly these fields in this order."""
        fields = self.fields(cls)
        if fields is None:
            return 'the game has no class %s' % cls
        us = units(obj[1:-1])
        for i, (f, u) in enumerate(zip(fields, us)):
            k = kind(u)
            if k != f.kind and not (k == 'cont' and f.kind in ('refs', 'raw')):
                return 'field %d (%s): expected %s, found %s' % (i, f.owner, f.kind, k)
        if len(us) != len(fields):
            return '%d fields, class has %d' % (len(us), len(fields))
        return None


def main():
    which = [a for a in sys.argv[1:] if a in GAMES] or ['dm', 'dd']
    os.makedirs(RE_DIR, exist_ok=True)
    for g in which:
        guesses, exe_name = GAMES[g]
        game = find(guesses, exe_name)
        if not game:
            raise SystemExit('Could not find %s; edit the folder guesses in kl_port_check.py' % exe_name)
        data = build(game, exe_name)
        out = os.path.join(RE_DIR, os.path.splitext(exe_name)[0] + '.json')
        write(out, data)
        print('  -> %s (%d classes, %d type handlers, %d enums)' % (out, len(data['classes']), len(data['types']), len(data['enums'])))


if __name__ == '__main__':
    main()
