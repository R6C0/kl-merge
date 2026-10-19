"""
LuaJIT 2.1 bytecode (dump version 2) reader + disassembler for Payday 2's lua (scripts.crate).
The dumps are NOT stripped: chunk name, line info, upvalue names and local variable names exist.

    python -I tools/pd2_lua.py dis  <file.luac> [func-filter]   # annotated listing
    python -I tools/pd2_lua.py str  <file.luac>                  # strings + numbers per function
    python -I tools/pd2_lua.py find <dir> <regex>                # files whose constants match

Operand rendering: K"str" = string constant, N=number constant, V=local variable name (debug info),
U=upvalue name, G=global name, F=child function (index in the file).
"""
import os
import re
import struct
import sys

OPS = ("ISLT ISGE ISLE ISGT ISEQV ISNEV ISEQS ISNES ISEQN ISNEN ISEQP ISNEP ISTC ISFC IST ISF ISTYPE ISNUM "
       "MOV NOT UNM LEN ADDVN SUBVN MULVN DIVVN MODVN ADDNV SUBNV MULNV DIVNV MODNV ADDVV SUBVV MULVV DIVVV "
       "MODVV POW CAT KSTR KCDATA KSHORT KNUM KPRI KNIL UGET USETV USETS USETN USETP UCLO FNEW TNEW TDUP GGET "
       "GSET TGETV TGETS TGETB TGETR TSETV TSETS TSETB TSETM TSETR CALLM CALL CALLMT CALLT ITERC ITERN VARG "
       "ISNEXT RETM RET RET0 RET1 FORI JFORI FORL IFORL JFORL ITERL IITERL JITERL LOOP ILOOP JLOOP JMP FUNCF "
       "IFUNCF JFUNCF FUNCV IFUNCV JFUNCV FUNCC FUNCCW").split()
# operand modes: (A, B, C/D) kinds: v=var slot, d=dst, s=str const, n=num const, p=primitive, u=upvalue,
# l=lit, j=jump, f=func const, t=table const, b=base, r=rbase, -=unused
MODES = {
    'ISLT': 'v-v', 'ISGE': 'v-v', 'ISLE': 'v-v', 'ISGT': 'v-v', 'ISEQV': 'v-v', 'ISNEV': 'v-v',
    'ISEQS': 'v-s', 'ISNES': 'v-s', 'ISEQN': 'v-n', 'ISNEN': 'v-n', 'ISEQP': 'v-p', 'ISNEP': 'v-p',
    'ISTC': 'd-v', 'ISFC': 'd-v', 'IST': '--v', 'ISF': '--v', 'ISTYPE': 'v-l', 'ISNUM': 'v-l',
    'MOV': 'd-v', 'NOT': 'd-v', 'UNM': 'd-v', 'LEN': 'd-v',
    'ADDVN': 'dvn', 'SUBVN': 'dvn', 'MULVN': 'dvn', 'DIVVN': 'dvn', 'MODVN': 'dvn',
    'ADDNV': 'dvn', 'SUBNV': 'dvn', 'MULNV': 'dvn', 'DIVNV': 'dvn', 'MODNV': 'dvn',
    'ADDVV': 'dvv', 'SUBVV': 'dvv', 'MULVV': 'dvv', 'DIVVV': 'dvv', 'MODVV': 'dvv', 'POW': 'dvv', 'CAT': 'dvv',
    'KSTR': 'd-s', 'KCDATA': 'd-c', 'KSHORT': 'd-l', 'KNUM': 'd-n', 'KPRI': 'd-p', 'KNIL': 'd-l',
    'UGET': 'd-u', 'USETV': 'u-v', 'USETS': 'u-s', 'USETN': 'u-n', 'USETP': 'u-p', 'UCLO': 'r-j',
    'FNEW': 'd-f', 'TNEW': 'd-l', 'TDUP': 'd-t', 'GGET': 'd-s', 'GSET': 'v-s',
    'TGETV': 'dvv', 'TGETS': 'dvs', 'TGETB': 'dvl', 'TGETR': 'dvv',
    'TSETV': 'vvv', 'TSETS': 'vvs', 'TSETB': 'vvl', 'TSETM': 'd-n', 'TSETR': 'vvv',
    'CALLM': 'blv', 'CALL': 'blv', 'CALLMT': 'b-l', 'CALLT': 'b-l', 'ITERC': 'blv', 'ITERN': 'blv',
    'VARG': 'blv', 'ISNEXT': 'b-j', 'RETM': 'b-l', 'RET': 'r-l', 'RET0': 'r-l', 'RET1': 'r-l',
    'FORI': 'b-j', 'JFORI': 'b-j', 'FORL': 'b-j', 'IFORL': 'b-j', 'JFORL': 'b-l', 'ITERL': 'b-j',
    'IITERL': 'b-j', 'JITERL': 'b-l', 'LOOP': 'r-j', 'ILOOP': 'r-j', 'JLOOP': 'r-l', 'JMP': 'r-j',
    'FUNCF': 'r--', 'IFUNCF': 'r--', 'JFUNCF': 'r-l', 'FUNCV': 'r--', 'IFUNCV': 'r--', 'JFUNCV': 'r-l',
    'FUNCC': 'r--', 'FUNCCW': 'r--',
}
PRI = {0: 'nil', 1: 'false', 2: 'true'}


class Proto:
    pass


def uleb(d, p):
    r = 0
    s = 0
    while True:
        b = d[p]
        p += 1
        r |= (b & 0x7f) << s
        s += 7
        if b < 0x80:
            return r, p


def uleb33(d, p):
    b = d[p]
    p += 1
    v = b >> 1
    if b >= 0x80:
        v &= 0x3f
        s = 6
        while True:
            b = d[p]
            p += 1
            v |= (b & 0x7f) << s
            s += 7
            if b < 0x80:
                break
    return v, b0 if False else None, p


def uleb33b(d, p):
    b0 = d[p]
    p += 1
    v = b0 >> 1
    if b0 >= 0x80:
        v &= 0x3f
        s = 6
        while True:
            b = d[p]
            p += 1
            v |= (b & 0x7f) << s
            s += 7
            if b < 0x80:
                break
    return v, b0 & 1, p


def parse(d):
    """-> (chunkname, [Proto in file order], main Proto). Protos are numbered in the order they appear."""
    assert d[:3] == b'\x1bLJ', 'not LuaJIT bytecode'
    ver = d[3]
    flags, p = uleb(d, 4)
    name = b''
    if not flags & 2:
        n, p = uleb(d, p)
        name = d[p:p + n]
        p += n
    stack = []
    allp = []
    while True:
        ln, p = uleb(d, p)
        if ln == 0:
            break
        end = p + ln
        q = Proto()
        q.idx = len(allp)
        allp.append(q)
        q.flags, q.nparams, q.frame, nuv = d[p], d[p + 1], d[p + 2], d[p + 3]
        p += 4
        nkgc, p = uleb(d, p)
        nkn, p = uleb(d, p)
        nbc, p = uleb(d, p)
        dbglen = 0
        q.firstline = q.numline = 0
        if not flags & 2:
            dbglen, p = uleb(d, p)
            if dbglen:
                q.firstline, p = uleb(d, p)
                q.numline, p = uleb(d, p)
        q.bc = list(struct.unpack_from('<%dI' % nbc, d, p))
        p += 4 * nbc
        q.uv = list(struct.unpack_from('<%dH' % nuv, d, p))
        p += 2 * nuv
        q.kgc = []
        for _ in range(nkgc):
            tp, p = uleb(d, p)
            if tp == 0:
                q.kgc.append(('F', stack.pop()))
            elif tp == 1:
                q.kgc.append(('T', None))
                raise ValueError('table constant: handled below')
            elif tp >= 5:
                q.kgc.append(('S', d[p:p + tp - 5].decode('latin1')))
                p += tp - 5
            else:
                raise ValueError('kgc type %d' % tp)
        q.kn = []
        for _ in range(nkn):
            lo, isnum, p = uleb33b(d, p)
            if isnum:
                hi, p = uleb(d, p)
                q.kn.append(struct.unpack('<d', struct.pack('<Q', (hi << 32) | lo))[0])
            else:
                q.kn.append(lo - (1 << 32) if lo & 0x80000000 else lo)
        q.lines = []
        q.uvnames = []
        q.vars = []
        if dbglen:
            dp = p
            lsz = 1 if q.numline < 256 else 2 if q.numline < 65536 else 4
            fmt = {1: 'B', 2: 'H', 4: 'I'}[lsz]
            q.lines = list(struct.unpack_from('<%d%s' % (nbc, fmt), d, dp))
            dp += lsz * nbc
            for _ in range(nuv):
                e = d.index(b'\0', dp)
                q.uvnames.append(d[dp:e].decode('latin1'))
                dp = e + 1
            pc = 0
            while dp < end:
                b = d[dp]
                if b == 0:
                    break
                if b >= 7:
                    e = d.index(b'\0', dp)
                    nm = d[dp:e].decode('latin1')
                    dp = e + 1
                else:
                    nm = '(%s)' % ['end', 'for index', 'for limit', 'for step', 'for generic', 'for state', 'for control'][b]
                    dp += 1
                dpc, dp = uleb(d, dp)
                pc += dpc
                ln2, dp = uleb(d, dp)
                q.vars.append((nm, pc, pc + ln2))
        p = end
        stack.append(q)
    return name.decode('latin1'), allp, stack[-1] if stack else None


def parse_safe(d):
    # handle table constants (kgc type 1) -- PD2 uses them rarely; re-implement with table decode
    return parse2(d)


def parse2(d):
    """Like parse() but also decodes table constants (tp == 1)."""
    assert d[:3] == b'\x1bLJ'
    flags, p = uleb(d, 4)
    name = b''
    if not flags & 2:
        n, p = uleb(d, p)
        name = d[p:p + n]
        p += n
    stack, allp = [], []

    def ktab_val(p):
        t, p = uleb(d, p)
        if t == 0:
            return None, p
        if t == 1:
            return False, p
        if t == 2:
            return True, p
        if t == 3:
            v, p = uleb(d, p)
            return v - (1 << 32) if v & 0x80000000 else v, p
        if t == 4:
            lo, p = uleb(d, p)
            hi, p = uleb(d, p)
            return struct.unpack('<d', struct.pack('<Q', (hi << 32) | lo))[0], p
        n = t - 5
        return d[p:p + n].decode('latin1'), p + n

    while True:
        ln, p = uleb(d, p)
        if ln == 0:
            break
        end = p + ln
        q = Proto()
        q.idx = len(allp)
        allp.append(q)
        q.flags, q.nparams, q.frame, nuv = d[p], d[p + 1], d[p + 2], d[p + 3]
        p += 4
        nkgc, p = uleb(d, p)
        nkn, p = uleb(d, p)
        nbc, p = uleb(d, p)
        dbglen = 0
        q.firstline = q.numline = 0
        if not flags & 2:
            dbglen, p = uleb(d, p)
            if dbglen:
                q.firstline, p = uleb(d, p)
                q.numline, p = uleb(d, p)
        q.bc = list(struct.unpack_from('<%dI' % nbc, d, p))
        p += 4 * nbc
        q.uv = list(struct.unpack_from('<%dH' % nuv, d, p))
        p += 2 * nuv
        q.kgc = []
        for _ in range(nkgc):
            tp, p = uleb(d, p)
            if tp == 0:
                q.kgc.append(('F', stack.pop()))
            elif tp == 1:
                narr, p = uleb(d, p)
                nhash, p = uleb(d, p)
                arr = []
                for _ in range(narr):
                    v, p = ktab_val(p)
                    arr.append(v)
                hs = []
                for _ in range(nhash):
                    k, p = ktab_val(p)
                    v, p = ktab_val(p)
                    hs.append((k, v))
                q.kgc.append(('T', (arr, hs)))
            elif tp == 2 or tp == 3:
                lo, p = uleb(d, p)
                hi, p = uleb(d, p)
                q.kgc.append(('I', (hi << 32) | lo))
            elif tp == 4:
                for _ in range(4):
                    _, p = uleb(d, p)
                q.kgc.append(('C', None))
            else:
                q.kgc.append(('S', d[p:p + tp - 5].decode('latin1')))
                p += tp - 5
        q.kn = []
        for _ in range(nkn):
            lo, isnum, p = uleb33b(d, p)
            if isnum:
                hi, p = uleb(d, p)
                q.kn.append(struct.unpack('<d', struct.pack('<Q', (hi << 32) | lo))[0])
            else:
                q.kn.append(lo - (1 << 32) if lo & 0x80000000 else lo)
        q.lines, q.uvnames, q.vars = [], [], []
        if dbglen:
            dp = p
            lsz = 1 if q.numline < 256 else 2 if q.numline < 65536 else 4
            q.lines = list(struct.unpack_from('<%d%s' % (nbc, {1: 'B', 2: 'H', 4: 'I'}[lsz]), d, dp))
            dp += lsz * nbc
            for _ in range(nuv):
                e = d.index(b'\0', dp)
                q.uvnames.append(d[dp:e].decode('latin1'))
                dp = e + 1
            pc = 0
            while dp < p + dbglen - (dp - p) + (dp - p) and dp < end:
                b = d[dp]
                if b == 0:
                    break
                if b >= 7:
                    e = d.index(b'\0', dp)
                    nm = d[dp:e].decode('latin1')
                    dp = e + 1
                else:
                    nm = '(%s)' % ['end', 'for index', 'for limit', 'for step', 'for generic', 'for state', 'for control'][b]
                    dp += 1
                dpc, dp = uleb(d, dp)
                pc += dpc
                ln2, dp = uleb(d, dp)
                q.vars.append((nm, pc, pc + ln2))
        p = end
        stack.append(q)
    return name.decode('latin1'), allp, stack[-1]


def varname(q, slot, pc):
    best = None
    for nm, s, e in q.vars:
        # the n-th active variable at pc occupies slot n; compute by order
        pass
    act = [nm for nm, s, e in q.vars if s <= pc < e]
    return act[slot] if slot < len(act) else None


def fmt_op(q, pc, w):
    op = OPS[w & 0xff] if (w & 0xff) < len(OPS) else '?%d' % (w & 0xff)
    a = (w >> 8) & 0xff
    b = (w >> 24) & 0xff
    c = (w >> 16) & 0xff
    dd = (w >> 16) & 0xffff
    m = MODES.get(op, 'r-l')
    two = m[1] == '-' and m[2] != '-' or op in ('KSHORT',)
    out = []

    def one(kind, val, signed=False):
        if kind == 'v' or kind == 'd' or kind == 'b' or kind == 'r':
            nm = varname(q, val, pc + 1)
            return 'r%d%s' % (val, ('(%s)' % nm) if nm else '')
        if kind == 's':
            return 'K"%s"' % q.kgc[len(q.kgc) - 1 - val][1] if q.kgc[len(q.kgc) - 1 - val][0] == 'S' else 'K?%d' % val
        if kind == 'n':
            return 'N%r' % (q.kn[val],) if val < len(q.kn) else 'N?'
        if kind == 'p':
            return PRI.get(val, '?')
        if kind == 'u':
            return 'U%d(%s)' % (val, q.uvnames[val] if val < len(q.uvnames) else '?')
        if kind == 'l':
            return str(val - 65536 if signed and val >= 32768 else val)
        if kind == 'j':
            return '->%d' % (pc + 1 + val - 0x8000)
        if kind == 'f':
            k = q.kgc[len(q.kgc) - 1 - val]
            return 'F#%d' % k[1].idx if k[0] == 'F' else 'F?'
        if kind == 't':
            k = q.kgc[len(q.kgc) - 1 - val]
            return 'TAB%r' % (k[1],)
        return ''
    if m[1] == '-' and m[2] != '-' and op not in ('IST', 'ISF'):
        # A, D form
        out.append(one(m[0], a))
        out.append(one(m[2], dd, signed=(op == 'KSHORT')))
    elif op in ('IST', 'ISF'):
        out.append(one('v', dd))
    elif m == 'r--' or m == '---':
        out.append('')
    else:
        out.append(one(m[0], a))
        out.append(one(m[1], b))
        out.append(one(m[2], c))
    return '%-6s %s' % (op, ' '.join(x for x in out if x))


def dis(q, out):
    out.append('--- function #%d lines %d..%d params %d uv=%s' % (q.idx, q.firstline, q.firstline + q.numline,
                                                                  q.nparams, ','.join(q.uvnames)))
    for pc, w in enumerate(q.bc):
        ln = q.firstline + q.lines[pc] if q.lines else 0
        out.append('%4d  L%-5d %s' % (pc, ln, fmt_op(q, pc, w)))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == 'find':
        rx = re.compile(argv[2])
        for root, _, fs in os.walk(argv[1]):
            for f in fs:
                p = os.path.join(root, f)
                try:
                    nm, allp, main_ = parse2(open(p, 'rb').read())
                except Exception as e:
                    print('ERR', p, e)
                    continue
                hit = set()
                for q in allp:
                    for k, v in q.kgc:
                        if k == 'S' and rx.search(v):
                            hit.add(v)
                if hit:
                    print(p[len(argv[1]):], sorted(hit)[:8])
        return 0
    d = open(argv[1], 'rb').read()
    nm, allp, main_ = parse2(d)
    if cmd == 'dis':
        out = []
        flt = argv[2] if len(argv) > 2 else None
        for q in allp:
            if flt and str(q.idx) != flt:
                continue
            dis(q, out)
        print('\n'.join(out))
    elif cmd == 'names':
        for q in allp:
            kstr = {}
            fn = {}
            for pc, w in enumerate(q.bc):
                op = OPS[w & 0xff]
                a = (w >> 8) & 0xff
                if op == 'KSTR':
                    kstr[a] = q.kgc[len(q.kgc) - 1 - ((w >> 16) & 0xffff)][1]
                elif op == 'FNEW':
                    fn[a] = q.kgc[len(q.kgc) - 1 - ((w >> 16) & 0xffff)][1]
                elif op in ('TSETS', 'TSETV') and a in fn:
                    if op == 'TSETS':
                        nm = q.kgc[len(q.kgc) - 1 - ((w >> 16) & 0xff)][1]
                    else:
                        nm = kstr.get((w >> 16) & 0xff, '?')
                    f = fn.pop(a)
                    print('#%d L%d-%d  %s' % (f.idx, f.firstline, f.firstline + f.numline, nm))
    elif cmd == 'str':
        for q in allp:
            print('#%d L%d params=%d: %s | %s' % (q.idx, q.firstline, q.nparams,
                  ' '.join(repr(v) for k, v in q.kgc if k == 'S'), ' '.join(repr(x) for x in q.kn)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
