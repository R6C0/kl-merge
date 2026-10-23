#!/usr/bin/env python3
r"""
kl_voice_fields.py - the speech LINE FIELDS of ZOnlineFragileAllianceSettings, read off kl2.exe:
field -> (flag, who, speech-manager group / single slot), and what the flag-0 ('plain') fields
hold on a level. Companion of kl_voice.LINES (same source, 302 call sites of the Init at kl2
0x88d780); this module adds the GROUP each line lands in and checks LINES against the exe.
Spec and findings: re/voiceplain_fields.md (2026-10-23).

    python kl_voice_fields.py table [--exe <kl2.exe>] [--out re/voice_fields.json]
                                   the 302 rows from the exe; checks kl_voice.LINES; writes the JSON
    python kl_voice_fields.py plain <level|zip> [--exe ..]
                                   every flag-0 field of that level's settings: key, present in the
                                   English .LOC?, sound id, text (who speaks it is read off the text)
    python kl_voice_fields.py test                 = table (0 mismatches) on the owner's PC

HOW THE EXE BUILDS THE LINES (kl2.exe build 0490, static reading; the live layout is klvoice.c's)
  ZOnlineFragileAllianceSettings vtable slot 16 = kl2 0x88d780 (the controller's activation).
  For each of 302 string fields of the object (member offsets 0x70 .. 0x538; settings field =
  (offset - 0x2c) / 4 as kl_voice has it - PROVEN by the .LOC lookup test below, 228 keys found the
  way their flag looks them up and 0 the other way on F02 / F07; NOTE the RTP record list of the
  class (kl_rtp, record +0x10) puts 0x70 one field LATER - that numbering is wrong by one here,
  42 keys land on the wrong flag with it) it calls
    0x877a30(group, key, who, flag)   -> a line appended to a GROUP (manager + g*0x18, g < 94; a
                                         group takes at most 3 lines, the 4th on is DROPPED), or
    0x6b8710(&single, key, who, flag) -> one of 27 SINGLE line slots manager+0x8d0 .. +0x93c (0x8f8 unused)
  (klvoice.c walks only the 19 singles 0x8d0..0x918; the 9 others, 0x91c..0x93c, are flag 0, so the
  per-character swap loses nothing, but [Voice] Plain never sees them.) 93 groups g0..g92 get 275 lines.
  0x6b8710: flag 1 -> ten entries K_C1..K_C9 and K_R_C9 (a missing key = empty slot), line+0x20 = 1;
            flag 0 -> ONE entry for key K exactly; no such key -> the line is freed (NULL).
  The flag and `who` are IMMEDIATES at each call site: code, not data. The KEY is data (the field).
  So a flag-0 field can never be made per-character from the level files; a flag-0 line is ONE
  recording for every speaker, in Dog Days' own levels too (PersonalRevenge, DirtyMoney).
"""
import json, os, struct, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kl_exe import Exe
from kl_port_check import find, DD_GUESSES, DD_EXE

INIT, INIT_END = 0x88d780, 0x890850          # ZOnlineFragileAllianceSettings slot 16
APPEND, SINGLE = 0x877a30, 0x6b8710           # line into a group / into a single slot
FIRST_FIELD, FIELD0 = 0x70, 0x2c              # member offset of the first line; field = (off - 0x2c) / 4
NLINES, NGROUPS = 302, 93                     # 275 lines in 93 groups (g0..g92) + 27 singles
SINGLES = [o for o in range(0x8d0, 0x940, 4) if o != 0x8f8]   # 0x8f8 is never filled by the Init
RE_JSON = os.path.join(os.path.dirname(HERE), 're', 'voice_fields.json')


def exe_path(args):
    if '--exe' in args:
        return args[args.index('--exe') + 1]
    dd = find(DD_GUESSES, DD_EXE)
    if not dd:
        sys.exit('kl2.exe not found: pass --exe <path>')
    return os.path.join(dd, DD_EXE)


def table(exe):
    """-> [{field, offset, flag, who, group, site}] in call order. group = 'g<n>' (manager +
    n*0x18) or 's<offset>' (a single slot). Pattern per call site (every one of the 302):
      mov eax,[esi+OFF]; test; je; add eax,0xc; jmp; xor eax,eax; mov ecx,[0x168e958];
      push FLAG; push WHO; push eax; (lea REG,[ecx+G]; push REG | push ecx); call APPEND|SINGLE"""
    import capstone
    E = Exe(exe) if isinstance(exe, str) else exe
    code = E.read(INIT, INIT_END - INIT)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    rows, off, pushes, lea = [], None, [], None
    for i in md.disasm(code, INIT):
        s = i.op_str
        if i.mnemonic == 'mov' and s.startswith('eax, dword ptr [esi + 0x'):
            off, pushes, lea = int(s[len('eax, dword ptr [esi + '):-1], 16), [], None
        elif i.mnemonic == 'push':
            pushes.append(s)
        elif i.mnemonic == 'lea' and ', [ecx + 0x' in s:
            lea = int(s.split('[ecx + ')[1][:-1], 16)
        elif i.mnemonic == 'call' and s in ('0x877a30', '0x6b8710'):
            if off is None or len(pushes) < 4:
                raise ValueError('unexpected call shape at %#x' % i.address)
            flag, who = int(pushes[-4], 0), int(pushes[-3], 0)
            if who > 0x7fffffff:
                who -= 1 << 32
            if s == '0x6b8710':
                group = 's%#x' % lea
            else:
                group = 'g%d' % ((lea or 0) // 0x18)
            rows.append(dict(field=(off - FIELD0) // 4, offset=off, flag=flag, who=who, group=group, site=i.address))
            off, pushes, lea = None, [], None
    return rows


def check(rows, log=print):
    """The exe's rows against kl_voice.LINES (flag, who per field). -> number of mismatches"""
    import kl_voice
    want = kl_voice.line_fields()
    bad = 0
    if len(rows) != NLINES:
        log('  !! %d line call sites, expected %d' % (len(rows), NLINES)); bad += 1
    fields = {r['field'] for r in rows}
    for f in sorted(set(want) ^ fields):
        log('  !! field %d is in %s only' % (f, 'kl_voice.LINES' if f in want else 'the exe'))
        bad += 1
    for r in rows:
        w = want.get(r['field'])
        if w and (w[0], w[1]) != (r['flag'], r['who']):
            log('  !! field %d: exe flag %d who %d, kl_voice.LINES %s' % (r['field'], r['flag'], r['who'], w)); bad += 1
    per = {}
    for r in rows:
        per.setdefault(r['group'], []).append(r['field'])
    over = {g: fs for g, fs in per.items() if g[0] == 'g' and len(fs) > 3}
    if over:
        log('  !! groups with more than 3 lines (the engine drops the 4th on): %s' % over); bad += 1
    singles = sorted(int(g[1:], 16) for g in per if g[0] == 's')
    if singles != SINGLES or sum(1 for g in per if g[0] == 'g') != NGROUPS:
        log('  !! %d groups, single slots %s' % (sum(1 for g in per if g[0] == 'g'), [hex(x) for x in singles])); bad += 1
    log('  %d lines: %d in %d groups, %d singles; flag 1: %d, flag 0: %d; kl_voice.LINES mismatches: %d'
        % (len(rows), sum(len(f) for g, f in per.items() if g[0] == 'g'), sum(1 for g in per if g[0] == 'g'),
           sum(1 for g in per if g[0] == 's'), sum(r['flag'] for r in rows), sum(1 - r['flag'] for r in rows), bad))
    return bad


def groups(rows=None):
    """{field: group} from the JSON (or rows)."""
    if rows is None:
        with open(RE_JSON) as f:
            rows = json.load(f)['lines']
    return {r['field']: r['group'] for r in rows}


def plain(src, rows, log=print):
    """Every flag-0 field of the settings on a level: key, English .LOC presence, sound id, text."""
    import kl_fa, kl_loc, kl_voice
    sc, snd, loc = kl_fa.load(src)
    st = kl_voice.settings(sc)
    if len(st) != 1:
        log('  %d settings controllers on %s' % (len(st), src)); return
    vals = st[0][2]
    leaves = {p: n for p, n in kl_loc.leaves(kl_loc.parse(loc))}
    present = missing = empty = 0
    for r in rows:
        if r['flag']:
            continue
        key = vals[r['field']]
        if not key:
            empty += 1; continue
        n = leaves.get(key.strip('/'))
        if n is None:
            missing += 1
            log('  %-4s who %2d MISSING %s' % (r['group'], r['who'], key)); continue
        present += 1
        text, _x, sid, _q = kl_loc.fields(n)
        log('  %-4s who %2d snd %-8s %-58s %s' % (r['group'], r['who'], sid, key, (text or b'').decode('latin1')[:90]))
    log('  flag-0 fields: %d with a key the .LOC has, %d whose key is missing (silent), %d empty' % (present, missing, empty))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'test'
    rows = table(exe_path(argv))
    if cmd in ('table', 'test'):
        bad = check(rows)
        if cmd == 'table':
            out = argv[argv.index('--out') + 1] if '--out' in argv else RE_JSON
            with open(out, 'w') as f:
                json.dump({'exe': 'kl2.exe 0490', 'init': INIT, 'fields_from': FIRST_FIELD, 'note': __doc__.split('\n')[1].strip(),
                           'lines': rows}, f, indent=0)
            print('  wrote %s' % out)
        sys.exit(1 if bad else 0)
    if cmd == 'plain':
        plain(argv[2], rows)
        return
    print(__doc__)


if __name__ == '__main__':
    main(sys.argv)
