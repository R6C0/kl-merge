"""
Glacier 1 (Kane & Lynch) .prp "IOPacked v0.1" reader / writer.

The file is: header, a table of null-terminated keys (strings), an object count,
then a token stream. Each token is a 1-byte opcode plus payload:

  01 u32  array begin (count)          7c      array end
  02      object begin                 7e      object end
  04 u32  int / count                  05 u8   char
  06 u8   bool                         07 u8   int8
  08 u16  int16                        09 u32  int32 / uint32
  0a f32  float                        0b f64  double
  0c u32  string (key index)           0e u32  enum (key index)
  0d u32 n + n bytes  raw blob         0f u32 n + n*u32  key-index list
  7f      end of stream

After a short settings block, the stream is the scene tree in depth-first order:
  { node properties } 04 nControllers ( 0c name { controller props } )* 04 nChildren <children>
Classes are not stored in the .prp; they come from the matching .gms.
"""
import struct

FIXED = {0x01: 4, 0x04: 4, 0x05: 1, 0x06: 1, 0x07: 1, 0x08: 2, 0x09: 4, 0x0a: 4,
         0x0b: 8, 0x0c: 4, 0x0e: 4, 0x02: 0, 0x7c: 0, 0x7e: 0}
LETTER = {0x04: 'i', 0x05: 'c', 0x06: 'b', 0x07: 'B', 0x08: 'h', 0x09: 'I', 0x0a: 'f',
          0x0b: 'd', 0x0c: 's', 0x0e: 'e', 0x0d: 'r', 0x0f: 'k'}
MAGIC = b'IOPacked v0.1'


class Prp:
    def __init__(self, data):
        if not data.startswith(MAGIC):
            raise ValueError('not an IOPacked v0.1 file')
        self.head = data[:0x0f]                       # magic + 0 + raw flag
        self.flags, self.zero, self.nkeys, off = struct.unpack_from('<IIII', data, 0x0f)
        self.keyblob = data[0x1f:0x1f + off]
        keys = self.keyblob.split(b'\0')
        if self.keyblob.endswith(b'\0'):
            keys.pop()                                # blob ends with a terminator, not a key
        self.keys = [k.decode('latin1') for k in keys]
        self.count = struct.unpack_from('<I', data, 0x1f + off)[0]
        self.tokens = self._tokenize(data, 0x1f + off + 4)
        self._build()

    # -- low level
    @staticmethod
    def _tokenize(d, pos):
        toks = []
        ap = toks.append
        end = len(d)
        while pos < end:
            op = d[pos]; p = pos + 1
            n = FIXED.get(op)
            if n is not None:
                ap((op, d[p:p + n])); pos = p + n
            elif op == 0x0d:
                L = struct.unpack_from('<I', d, p)[0]; ap((op, d[p:p + 4 + L])); pos = p + 4 + L
            elif op == 0x0f:
                L = struct.unpack_from('<I', d, p)[0]; ap((op, d[p:p + 4 + 4 * L])); pos = p + 4 + 4 * L
            elif op == 0x7f:
                ap((op, b'')); pos = p
                if pos != end:
                    raise ValueError('data after end-of-stream at %#x' % pos)
                break
            else:
                raise ValueError('unknown opcode %#x at %#x' % (op, pos))
        return toks

    def key(self, tok):
        return self.keys[struct.unpack('<I', tok[1])[0]]

    def key_index(self, s):
        try:
            return self.keys.index(s)
        except ValueError:
            self.keys.append(s)
            self.keyblob += s.encode('latin1') + b'\0'
            self.nkeys += 1
            return len(self.keys) - 1

    # -- tree
    def _obj_end(self, i):
        """i: index of '{'. Returns index after matching '}'."""
        depth = 0
        t = self.tokens
        while True:
            op = t[i][0]
            if op == 0x02: depth += 1
            elif op == 0x7e:
                depth -= 1
                if depth == 0: return i + 1
            i += 1

    def _build(self):
        t = self.tokens
        i = 0
        while t[i][0] != 0x02:
            i += 1
        self.settings = t[:i]
        self.root, i = self._node(i)
        self.tail = t[i:]
        if [x[0] for x in self.tail] != [0x7f]:
            raise ValueError('unexpected tokens after scene tree')

    def _node(self, i):
        t = self.tokens
        root = None
        stack = []                       # (node, children remaining)
        while True:
            j = self._obj_end(i)
            node = {'props': t[i:j], 'ctrls': [], 'children': []}
            i = j
            nc = struct.unpack('<I', t[i][1])[0]; i += 1
            for _ in range(nc):
                name = t[i]; j = self._obj_end(i + 1)
                node['ctrls'].append((name, t[i + 1:j])); i = j
            nch = struct.unpack('<I', t[i][1])[0]; i += 1
            if stack:
                stack[-1][0]['children'].append(node)
            else:
                root = node
            stack.append([node, nch])
            while stack and stack[-1][1] == 0:
                stack.pop()
                if stack:
                    stack[-1][1] -= 1
            if not stack:
                return root, i

    def nodes(self):
        out, st = [], [self.root]
        while st:
            n = st.pop(); out.append(n); st.extend(reversed(n['children']))
        return out

    # -- writing
    def serialize(self):
        toks = list(self.settings)
        st = [self.root]
        while st:
            n = st.pop()
            toks += n['props']
            toks.append((0x04, struct.pack('<I', len(n['ctrls']))))
            for name, body in n['ctrls']:
                toks.append(name); toks += body
            toks.append((0x04, struct.pack('<I', len(n['children']))))
            st.extend(reversed(n['children']))
        toks += self.tail
        count = sum(1 for op, _ in toks if op == 0x02)
        out = bytearray(self.head)
        out += struct.pack('<IIII', self.flags, self.zero, self.nkeys, len(self.keyblob))
        out += self.keyblob
        out += struct.pack('<I', count)
        for op, pl in toks:
            out.append(op); out += pl
        return bytes(out)


def units(tokens):
    """Split an object's inner tokens into field units. Arrays/sub-objects are one unit, and so is
    a reference list: an int count n followed by n strings (both games write entity-reference
    lists that way, without array markers)."""
    out, i, n = [], 0, len(tokens)
    while i < n:
        op = tokens[i][0]
        if op in (0x01, 0x02):
            close = 0x7c if op == 0x01 else 0x7e
            j, depth = i + 1, 1
            while depth:
                o = tokens[j][0]
                if o == op: depth += 1
                elif o == close: depth -= 1
                j += 1
            out.append(tokens[i:j]); i = j
        elif op == 0x04:
            c = struct.unpack('<I', tokens[i][1])[0]
            j = i + 1 + c
            if 0 < c and j <= n and all(tokens[k][0] == 0x0c for k in range(i + 1, j)):
                out.append(tokens[i:j]); i = j
            elif 0 < c and i + 1 < n and tokens[i + 1][0] == 0x0d and len(tokens[i + 1][1]) == 4 + c:
                out.append(tokens[i:i + 2]); i += 2          # byte count + raw block
            else:
                out.append(tokens[i:i + 1]); i += 1
        else:
            out.append(tokens[i:i + 1]); i += 1
    return out


def kind(unit):
    """What one field unit is on disk, in the notation the schemas use (kl_rtp.py):
    a scalar's LETTER; 'f*9' an array of 9 floats; 'refs' a count and that many strings;
    'raw' a byte count and a raw block; 'cont' a zero count (an empty 'refs' or 'raw')."""
    unit = list(unit)
    op = unit[0][0]
    if op == 0x01:
        inner = unit[1:-1]
        ops = set(o for o, _ in inner)
        n = struct.unpack('<I', unit[0][1])[0]
        if len(ops) == 1 and len(inner) == n and next(iter(ops)) in LETTER:
            return '%s*%d' % (LETTER[next(iter(ops))], n)
        return 'array'                      # empty, mixed or nested: not a property the schemas know
    if op == 0x02:
        return 'object'
    if op == 0x04:
        if len(unit) == 1:
            return 'cont' if unit[0][1] == b'\0\0\0\0' else 'count'
        return 'raw' if unit[1][0] == 0x0d else 'refs'
    return LETTER.get(op, '?')


def signature(tokens):
    """Field-layout signature of an object's tokens. Array lengths are collapsed, but every
    distinct element layout is kept, so arrays of sub-objects are compared in full."""
    def elem(toks, i):
        op = toks[i][0]
        if op in (0x01, 0x02):
            close = 0x7c if op == 0x01 else 0x7e
            j, depth = i + 1, 1
            while depth:
                o = toks[j][0]
                if o == op: depth += 1
                elif o == close: depth -= 1
                j += 1
            inner = toks[i + 1:j - 1]
            if op == 0x02:
                return '{' + seq(inner) + '}', j
            k, kinds = 0, set()
            while k < len(inner):
                e, k = elem(inner, k)
                kinds.add(e)
            return '[' + '|'.join(sorted(kinds)) + '*]', j
        if op == 0x7e:
            return '}', i + 1
        return LETTER.get(op, '?'), i + 1
    def seq(toks):
        out, i = [], 0
        while i < len(toks):
            e, i = elem(toks, i)
            out.append(e)
        return ''.join(out)
    return seq(list(tokens))
