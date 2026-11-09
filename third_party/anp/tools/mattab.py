"""Impact-material table (GMS h[12] -> offset into .buf).
Layout (offsets relative to table start T):
  hdr  [rows, cols, lists, stride, strings, data]
  rows : n, (strIdx, id)*n        ids are 1-based row numbers
  cols : n, (strIdx, type, off, arrFlag)*n
  lists: n, (strIdx, off)*n  -> each list: n, (strIdx, idx)*n
  data : rows*stride
  strings: n, off*n, text      (offsets relative to T)
Dog Days code looks rows up by name ("Flesh Hero", "Metal Perforated") and
crashes when they are missing, so we append alias rows cloned from DM rows."""
import struct

DD_ALIASES = {'Flesh Hero': 'Flesh', 'Metal Perforated': 'Perforated Metal',
              'Stone Perforated': 'Perforated Stone'}

def _cstr(d, o): return d[o:d.index(b'\0', o)].decode('latin1')

def parse(buf, T):
    rows_o, cols_o, lists_o, stride, str_o, data_o = struct.unpack_from('<6I', buf, T)
    n = struct.unpack_from('<I', buf, T + str_o)[0]
    S = [_cstr(buf, T + struct.unpack_from('<I', buf, T + str_o + 4 + 4 * i)[0]) for i in range(n)]
    nr = struct.unpack_from('<I', buf, T + rows_o)[0]
    rows = [struct.unpack_from('<II', buf, T + rows_o + 4 + 8 * i) for i in range(nr)]
    nc = struct.unpack_from('<I', buf, T + cols_o)[0]
    cols = [struct.unpack_from('<4I', buf, T + cols_o + 4 + 16 * i) for i in range(nc)]
    nl = struct.unpack_from('<I', buf, T + lists_o)[0]
    lists = []
    for i in range(nl):
        si, lo = struct.unpack_from('<II', buf, T + lists_o + 4 + 8 * i)
        m = struct.unpack_from('<I', buf, T + lo)[0]
        lists.append((si, [struct.unpack_from('<II', buf, T + lo + 4 + 8 * k) for k in range(m)]))
    data = [bytes(buf[T + data_o + stride * i: T + data_o + stride * (i + 1)]) for i in range(nr)]
    return dict(S=S, rows=rows, cols=cols, lists=lists, stride=stride, data=data)

def build(t):
    S, rows, cols, lists, stride, data = t['S'], t['rows'], t['cols'], t['lists'], t['stride'], t['data']
    out = bytearray(24)
    rows_o = len(out); out += struct.pack('<I', len(rows)) + b''.join(struct.pack('<II', *r) for r in rows)
    cols_o = len(out); out += struct.pack('<I', len(cols)) + b''.join(struct.pack('<4I', *c) for c in cols)
    lists_o = len(out); out += struct.pack('<I', len(lists)) + bytes(8 * len(lists))
    data_o = len(out)
    for r in data: out += r
    for i, (si, ent) in enumerate(lists):
        lo = len(out)
        out += struct.pack('<I', len(ent)) + b''.join(struct.pack('<II', *e) for e in ent)
        struct.pack_into('<II', out, lists_o + 4 + 8 * i, si, lo)
    str_o = len(out)
    out += struct.pack('<I', len(S)) + bytes(4 * len(S))
    for i, s in enumerate(S):
        struct.pack_into('<I', out, str_o + 4 + 4 * i, len(out)); out += s.encode('latin1') + b'\0'
    while len(out) % 16: out.append(0)
    struct.pack_into('<6I', out, 0, rows_o, cols_o, lists_o, stride, str_o, data_o)
    return bytes(out)

def add_dd_rows(buf, T, aliases=DD_ALIASES, rep=None):
    """returns (new_table_bytes, added_names)"""
    t = parse(buf, T)
    names = {t['S'][si]: rid for si, rid in t['rows']}
    added = []
    for new, src in aliases.items():
        if new in names or src not in names: continue
        rid = len(t['rows']) + 1
        t['S'].append(new)
        t['rows'].append((len(t['S']) - 1, rid))
        t['data'].append(t['data'][names[src] - 1])
        names[new] = rid; added.append(new)
    return build(t), added

if __name__ == '__main__':
    import sys
    buf = open(sys.argv[1], 'rb').read(); T = int(sys.argv[2], 16)
    t = parse(buf, T)
    nb, added = add_dd_rows(buf, T)
    t2 = parse(nb, 0)
    print(added, len(t['rows']), '->', len(t2['rows']))
    # round-trip check without additions
    rb = build(t); t3 = parse(rb, 0)
    assert t3 == t, 'roundtrip mismatch'
    print('roundtrip ok', [ (t2['S'][s], i) for s, i in t2['rows'][-4:]])
