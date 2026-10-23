#!/usr/bin/env python3
"""
Apply a PATCH ini to a KLHook.ini (or any ini) and keep everything else: comments, blank lines, key order, line
endings. Nothing in tools/ did this before (klini_audit.py only reads); written 2026-10-23 for the balance patch.

    python kl_ini_patch.py <target.ini> <patch.ini> [--dry-run] [-o <out.ini>] [--backup=<suffix>]

  --dry-run      print a unified diff of what would change; write nothing
  -o <out.ini>   write the result there instead of over the target (the target is then never touched)
  --backup=SUF   before overwriting the target in place, copy it to <target>.SUF (refuses if that file exists)

Rules (the same lookup Windows' GetPrivateProfileString does, which is what the hook uses):
  - sections and keys match case-insensitively; a key is replaced on its FIRST occurrence in its section (the one the
    game reads); a second occurrence in the same section is reported (it is dead text) and left alone
  - a replaced line keeps its own indentation and line ending; a trailing '; comment' on the old line is dropped
    (the old value is printed in the report instead); comment lines above it stay
  - a key the section lacks is appended after the section's last key/comment-with-content line, before blank lines
    that precede the next section; a missing section is appended at the end of the file
  - the patch ini may hold comment lines ('; ...'): they are written above a NEW key only (not above a replaced one)
Exit status 0 = ok (also when nothing changes), 2 = bad input.
"""
import difflib, os, re, shutil, sys

SEC = re.compile(r'^\s*\[([^\]]+)\]\s*$')
KEY = re.compile(r'^(\s*)([^;=\[\s][^=]*?)\s*=(.*)$')


def read_lines(p):
    with open(p, 'rb') as fh:
        raw = fh.read()
    text = raw.decode('utf-8-sig', 'surrogateescape') if raw[:3] == b'\xef\xbb\xbf' else raw.decode('latin-1')
    bom = raw[:3] == b'\xef\xbb\xbf'
    return text.splitlines(True), bom


def parse_patch(p):
    """-> [(section, [(key, value, [comment lines above])])] in file order."""
    lines, _bom = read_lines(p)
    out, cur, pend = [], None, []
    for ln in lines:
        s = ln.strip()
        m = SEC.match(ln)
        if m:
            cur = (m.group(1).strip(), [])
            out.append(cur)
            pend = []
        elif s.startswith(';'):
            pend.append(s)
        elif not s:
            continue
        else:
            k = KEY.match(ln)
            if not k or cur is None:
                raise ValueError('%s: cannot read the line %r' % (p, ln.rstrip()))
            cur[1].append((k.group(2).strip(), k.group(3).strip(), pend))
            pend = []
    return out


def eol_of(lines):
    for ln in lines:
        if ln.endswith('\r\n'):
            return '\r\n'
        if ln.endswith('\n'):
            return '\n'
    return '\r\n'


def apply_patch(lines, patch):
    """-> (new lines, report lines)"""
    lines, rep, eol = list(lines), [], eol_of(lines)
    if lines and not lines[-1].endswith(('\n', '\r')):
        lines[-1] += eol
    for sec, keys in patch:
        # find the section (first one with that name, as GetPrivateProfile does)
        start = next((i for i, ln in enumerate(lines) if SEC.match(ln) and SEC.match(ln).group(1).strip().lower() == sec.lower()), None)
        if start is None:
            if lines and lines[-1].strip():
                lines.append(eol)
            lines.append('[%s]%s' % (sec, eol))
            start = len(lines) - 1
            rep.append('[%s] NEW SECTION' % sec)
        end = next((i for i in range(start + 1, len(lines)) if SEC.match(lines[i])), len(lines))
        for key, val, comments in keys:
            hits = [i for i in range(start + 1, end) if KEY.match(lines[i]) and KEY.match(lines[i]).group(2).strip().lower() == key.lower()]
            if hits:
                i = hits[0]
                m = KEY.match(lines[i])
                old = m.group(3).split(';')[0].strip()
                ending = lines[i][len(lines[i].rstrip('\r\n')):] or eol
                lines[i] = '%s%s=%s%s' % (m.group(1), m.group(2).strip(), val, ending)
                rep.append('[%s] %s: %s -> %s%s' % (sec, key, old or '(empty)', val, '   (line %d)' % (i + 1)))
                if len(hits) > 1:
                    rep.append('[%s] %s: also set on line(s) %s - dead text, left alone' % (sec, key, ', '.join(str(h + 1) for h in hits[1:])))
            else:
                at = end
                while at - 1 > start and (not lines[at - 1].strip() or lines[at - 1].lstrip().startswith(';')):
                    at -= 1       # before the blank / comment lines that precede the next section (they describe IT)
                new = [c + eol for c in comments] + ['%s=%s%s' % (key, val, eol)]
                lines[at:at] = new
                end += len(new)
                rep.append('[%s] %s: (absent) -> %s   (appended at line %d)' % (sec, key, val, at + len(comments) + 1))
    return lines, rep


def main(argv):
    if len(argv) < 2 or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 2
    pos = [a for a in argv if not a.startswith('-')]
    dry = '--dry-run' in argv
    out = argv[argv.index('-o') + 1] if '-o' in argv else None
    if out in pos:
        pos.remove(out)
    suf = next((a.split('=', 1)[1] for a in argv if a.startswith('--backup=')), None)
    if len(pos) != 2:
        print(__doc__)
        return 2
    target, patch = pos
    lines, bom = read_lines(target)
    new, rep = apply_patch(lines, parse_patch(patch))
    for r in rep:
        print('  ' + r)
    diff = list(difflib.unified_diff([l.rstrip('\r\n') for l in lines], [l.rstrip('\r\n') for l in new], target, (out or target) + ' (patched)', lineterm='', n=1))
    if dry:
        print('\n'.join(diff) if diff else '(no change)')
        return 0
    if not diff:
        print('(no change)')
        return 0
    dst = out or target
    if not out and suf:
        b = target + '.' + suf
        if os.path.exists(b):
            print('backup %s exists: refusing' % b)
            return 2
        shutil.copyfile(target, b)
    with open(dst, 'wb') as fh:
        fh.write((b'\xef\xbb\xbf' if bom else b'') + ''.join(new).encode('utf-8' if bom else 'latin-1', 'surrogateescape'))
    print('written %s (%d lines changed)' % (dst, sum(1 for l in diff if l[:1] in '+-' and l[:3] not in ('+++', '---')) // 2))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
