#!/usr/bin/env python3
r"""kl_ini_shipcheck.py - is this KLHook.ini fit to ship to a tester? (2026-11-10, scheduled check-in, offline)

    python tools/kl_ini_shipcheck.py [LIVE.ini] [--sample klhook/KLHook.ini] [--dd "<DD>"] [--pd2 "<PD2>"] [--json OUT] [--notes]

kl_release `make` ships the owner's LIVE KLHook.ini as-is (install only re-points [Ambience]/[Stinger]/[Music] Folder=,
see kl_release.localize_ini_bytes). The T0 "Owner: shipped-ini review" item asked for three things by eye: probe /
diagnostic / TEST-only keys left on, comment lines and values naming the owner's own drives (G:\, C:\kl_build_1024, D:\),
and sections the repo sample does not know ([Campaign]...). This reader does that review from the repo's own sample ini,
klhook/KLHook.ini, whose comments say per key "(recommended on)", "(recommended off ...)", "TEST build only",
"diagnostic". Pure reader: writes nothing, exit 1 when it finds an ERROR or a WARN, 0 otherwise.

Findings (one line each, worst first):
  ERROR  a value with an absolute path that kl_release does not localize (breaks on every tester's PC), or a path under a
         folder that is not a game folder at all (C:\kl_build_1024, D:\...) even where it would be localized.
  WARN   an active key the sample marks "diagnostic", "TEST build(s) only", "TEST-only", "bench only", "log only" or whose
         name says Probe / Trace / Dump / Diag, when the sample does not recommend it on; a test-driver section ([Auto]
         [Bench] [Script] [Solo] [Probe]) with active keys beyond the sample.
  FEAT   an active feature key the sample marks "(recommended off ...)" (until benched / not run live): the owner's
         choice, listed so the stale sample comments get a second look; never fails the check.
  LOG    (summary line always; the lines with --notes) the hook's per-module Log= levels and the probes the sample itself
         recommends on (OnlineTagProbe, ReplicaProbe): what a tester's KLHook.log will carry.
  NOTE   (--notes) a comment line naming an owner drive path (leaks nothing that breaks, reads odd to a tester); a section
         or key the sample does not document (a tester gets a key nobody wrote up: [Campaign] and friends); a WARN/FEAT
         whose value equals the repo sample's own.
A key the sample marks "(recommended on)" is never a WARN, whatever its name (OnlineTagProbe=1 is a cull probe, not a log).
Semantics follow GetPrivateProfileString: ';' starts a comment anywhere, the first of duplicate keys wins, keys are
case-insensitive, a section repeated later merges.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = os.path.join(os.path.dirname(HERE), 'klhook', 'KLHook.ini')
DD = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TEST_SECTIONS = ('auto', 'bench', 'script', 'solo', 'probe')
NAME_RE = re.compile(r'probe|trace|diag|(?<!max)dump', re.I)      # MaxDumps = crash dump count, not a log
# a drive path: 'X:\seg' whose first segment holds no ':' ("fire:/hit:/round:" in a log-format comment is not one)
PATH_RE = re.compile(r'(?<![A-Za-z0-9_])(?:[A-Za-z]:[\\/](?=[^\s;:/\\]+(?:[\\/\s;]|$))|\\\\[^\\/\s]+[\\/])[^;\r\n]*')
GAME_FOLDERS = ('kane & lynch 2 - dog days', 'payday 2', 'kane and lynch dead men')
LOCALIZED_KEYS = ('folder', 'folderb')              # kl_release.INI_LOCAL_RE: the keys install re-points
LOCALIZED_GAMES = ('kane & lynch 2 - dog days', 'payday 2')   # kl_release.INI_GAMES
OFF_VALUES = ('', '0', 'off', 'no', 'false')
DIAG_RE = re.compile(r'diagnos|test[- ]?builds?(?: only)?|test[- ]?only|bench only|log only', re.I)
LEVELS = {'ERROR': 0, 'WARN': 1, 'FEAT': 2, 'LOG': 3, 'NOTE': 4}


def split_line(line):
    """-> (text before the first ';', comment after it or '')"""
    i = line.find(';')
    return (line, '') if i < 0 else (line[:i], line[i + 1:])


def parse_ini(text):
    """-> {section_lower: {key_lower: (key, value, lineno)}} (first duplicate wins), section order + raw names kept aside"""
    secs, names, cur = {}, {}, None
    for n, raw in enumerate(text.split('\n'), 1):
        body, _ = split_line(raw.rstrip('\r'))
        s = body.strip()
        if not s:
            continue
        if s.startswith('[') and s.endswith(']'):
            cur = s[1:-1].strip().lower()
            names.setdefault(cur, s[1:-1].strip())
            secs.setdefault(cur, {})
            continue
        if '=' not in s or cur is None:
            continue
        k, v = s.split('=', 1)
        k, v = k.strip(), v.strip()
        if k and k.lower() not in secs[cur]:
            secs[cur][k.lower()] = (k, v, n)
    return secs, names


def parse_sample(text):
    """-> {section_lower: {key_lower: doc}}: doc = the comment text that documents the key (its own inline comment, a
    commented-out ';Key=' line's comment, and every comment line of the block right above it that names the key)"""
    docs, cur, real, block = {}, None, None, []
    for raw in text.split('\n'):
        line = raw.rstrip('\r')
        s = line.strip()
        m = re.match(r'^(;?)\s*\[([^\]]+)\]\s*(?:;.*)?$', s)
        if m:
            # ';[Probe]' documents a whole off section, but the ACTIVE keys after it still belong to the last real
            # header (the hook's parser reads ';[X]' as a comment): commented-out keys go to cur, active ones to real
            cur = m.group(2).strip().lower()
            if not m.group(1):
                real = cur
            docs.setdefault(cur, {})
            continue                # the comment block above a header documents its first key ('[Auto]' PollLossMs)
        if not s:
            block = []
            continue
        if s.startswith(';'):
            km = re.match(r'^;\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*[^;\s]*\s*(?:;(.*))?$', s)
            if km and cur is not None:
                # a commented-out key line: ';Key=0   ; (recommended off ...)'
                _add(docs, cur, km.group(1), (km.group(2) or '') + ' ' + _lines_for(km.group(1), block))
                block.append(s[1:])
                continue
            block.append(s[1:])
            continue
        body, inline = split_line(line)
        if '=' in body and real is not None:
            cur = real
            k = body.split('=', 1)[0].strip()
            _add(docs, real, k, inline + ' ' + _lines_for(k, block))
            block = []
    return docs


def _lines_for(key, block):
    """the comment lines of the block that document KEY: the ones that start with it ('; Key=1 (recommended ...)',
    '; Key (recommended ...)'), else every line naming it as a word (a block of 20 keys documents each on its own line)"""
    own = [b for b in block if re.match(r'\s*%s\b' % re.escape(key), b, re.I)]
    if own:
        return ' '.join(own)
    return ' '.join(b for b in block if re.search(r'\b%s\b' % re.escape(key), b, re.I))


def _add(docs, sec, key, doc):
    d = docs.setdefault(sec, {})
    d[key.lower()] = (d.get(key.lower(), '') + ' ' + doc).strip()


def classify(doc):
    """-> 'on' | 'off' | None: what the sample recommends for a key"""
    low = doc.lower()
    if re.search(r'\(recommended on\b', low) or re.search(r'recommended on\b', low):
        return 'on'
    if re.search(r'recommended off', low) or re.search(r'\btest[- ]?(?:build(?:s)? only|only|diagnostics?)\b', low) \
            or re.search(r'\bdiagnos', low):
        return 'off'
    return None


def is_off(value):
    v, _ = split_line(value)
    return v.strip().lower() in OFF_VALUES


def path_findings(sec_name, key, value, lineno, dd, pd2):
    out = []
    for m in PATH_RE.finditer(value):
        p = m.group(0).strip().rstrip('\\/')
        low = p.lower().replace('/', '\\')
        game = next((g for g in GAME_FOLDERS if '\\' + g in low), None)
        localized = key.lower() in LOCALIZED_KEYS and any('\\' + g in low for g in LOCALIZED_GAMES)
        if game is None:
            out.append(('ERROR', sec_name, key, value, lineno, 'absolute path outside any game folder (owner-only: %s)' % p))
        elif not localized:
            out.append(('ERROR', sec_name, key, value, lineno, 'absolute game path that install does not re-point (only Folder/FolderB are): %s' % p))
        elif dd and game == 'kane & lynch 2 - dog days' and not low.startswith(dd.lower().rstrip('\\/').replace('/', '\\')):
            out.append(('NOTE', sec_name, key, value, lineno, 'Dog Days path not under --dd (install re-points it): %s' % p))
        elif pd2 and game == 'payday 2' and not low.startswith(pd2.lower().rstrip('\\/').replace('/', '\\')):
            out.append(('NOTE', sec_name, key, value, lineno, 'Payday 2 path not under --pd2 (install re-points it): %s' % p))
    return out


def check(live_text, sample_text, dd=None, pd2=None, notes=False):
    """-> list of (level, section, key, value, lineno, why), worst first"""
    live, names = parse_ini(live_text)
    docs = parse_sample(sample_text)
    sample, _ = parse_ini(sample_text)
    out = []
    for sec, keys in live.items():
        sname = names.get(sec, sec)
        sdoc = docs.get(sec)
        if sdoc is None and notes:
            out.append(('NOTE', sname, '', '', 0, 'section not in the repo sample (%d keys nobody documented for a tester)' % len(keys)))
        extra = [k for k, (_, v, _) in keys.items()
                 if not is_off(v) and split_line(v)[0].strip() != split_line(sample.get(sec, {}).get(k, ('', '', 0))[1])[0].strip()]
        if sec in TEST_SECTIONS and extra:
            out.append(('WARN', sname, '', '', 0, 'test-driver section with active keys beyond the sample (%s): a tester build should not carry them'
                        % ', '.join(keys[k][0] for k in extra)))
        for kl, (k, v, n) in keys.items():
            out.extend(path_findings(sname, k, v, n, dd, pd2))
            doc = (sdoc or {}).get(kl)
            rec = classify(doc) if doc is not None else None
            if doc is None and sdoc is not None and notes:
                out.append(('NOTE', sname, k, v, n, 'key not in the repo sample'))
            if is_off(v):
                continue
            diag = bool(NAME_RE.search(k) or (doc and DIAG_RE.search(doc)))
            if kl == 'log' or (rec == 'on' and diag):
                # the hook's per-module Log= levels and the probes the sample itself wants on: logging, not a fault
                out.append(('LOG', sname, k, v, n, 'log level' if kl == 'log' else 'log-only probe the sample recommends on'))
                continue
            if rec == 'on':
                continue
            if rec == 'off':
                why = 'sample says: ' + _short(doc)
                # a parameter "(recommended off, only used with Master on)" is inert while its master key is off;
                # "(recommended off = leave at 250 ...)" is the code default when the value IS that number
                mm = re.search(r'only (?:used )?with ([A-Za-z][A-Za-z0-9_]*)', doc, re.I)
                if mm and is_off(keys.get(mm.group(1).lower(), ('', '0', 0))[1]):
                    continue
                lm = re.search(r'leave at ([0-9.]+)', doc, re.I)
                if lm and _num(split_line(v)[0]) == _num(lm.group(1)):
                    continue
                level = 'WARN' if diag else 'FEAT'
            elif diag:
                why = 'name says probe/trace/dump/diag and the sample does not recommend it on'
                level = 'WARN'
            else:
                continue
            sv = sample.get(sec, {}).get(kl)
            if sv is not None and split_line(sv[1])[0].strip().lower() == split_line(v)[0].strip().lower():
                if notes:
                    out.append(('NOTE', sname, k, v, n, why + ' (same value as the repo sample)'))
                continue
            out.append((level, sname, k, v, n, why))
    if notes:
        for n, raw in enumerate(live_text.split('\n'), 1):
            _, comment = split_line(raw)
            for m in PATH_RE.finditer(comment):
                p = m.group(0).strip()
                if not any('\\' + g in p.lower().replace('/', '\\') for g in GAME_FOLDERS):
                    out.append(('NOTE', '', '', '', n, 'comment names an owner path: %s' % p[:60]))
    out.sort(key=lambda f: (LEVELS[f[0]], f[4]))
    return out


def _num(s):
    try:
        return float(s.strip())
    except ValueError:
        return None


def _short(doc):
    m = re.search(r'\((?:recommended off[^)]*)\)', doc, re.I) or re.search(r'test[- ]?build[^;.,]*', doc, re.I) \
        or re.search(r'diagnos[^;.,]*', doc, re.I)
    return (m.group(0) if m else doc)[:80]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ini', nargs='?', default=os.path.join(DD, 'KLHook.ini'))
    ap.add_argument('--sample', default=SAMPLE)
    ap.add_argument('--dd', default=None, help="this PC's Dog Days folder (NOTE when a localized path points elsewhere)")
    ap.add_argument('--pd2', default=None)
    ap.add_argument('--json', default=None, help='write the findings as JSON too')
    ap.add_argument('--notes', action='store_true', help='also print the NOTE lines (owner paths in comments, undocumented keys)')
    a = ap.parse_args()
    live = open(a.ini, encoding='latin1').read()
    sample = open(a.sample, encoding='latin1').read()
    found = check(live, sample, a.dd, a.pd2, notes=a.notes)
    for lv, sec, k, v, n, why in found:
        if lv in ('LOG', 'NOTE') and not a.notes:
            continue
        where = ('[%s] ' % sec if sec else '') + (('%s=%s' % (k, v[:40])) if k else '')
        print('%-5s line %-5d %-50s %s' % (lv, n, where, why))
    counts = {lv: sum(1 for f in found if f[0] == lv) for lv in LEVELS}
    logs = [f for f in found if f[0] == 'LOG']
    if logs:
        print('logging on (%d): %s' % (len(logs), ', '.join(
            ('[%s] ' % sec if k.lower() == 'log' else '') + '%s=%s' % (k, split_line(v)[0].strip()) for _, sec, k, v, _, _ in logs)))
    print('RESULT: %s - %d ERROR, %d WARN (diagnostics / TEST-only on), %d FEAT (sample says off until benched), %d logging, %d NOTE (%s vs sample %s)' % (
        'FAIL' if counts['ERROR'] or counts['WARN'] else 'PASS', counts['ERROR'], counts['WARN'], counts['FEAT'], counts['LOG'],
        counts['NOTE'], os.path.basename(a.ini), os.path.relpath(a.sample)))
    if a.json:
        json.dump([dict(level=lv, section=sec, key=k, value=v, line=n, why=why) for lv, sec, k, v, n, why in found],
                  open(a.json, 'w'), indent=1)
    return 1 if counts['ERROR'] or counts['WARN'] else 0


if __name__ == '__main__':
    sys.exit(main())
