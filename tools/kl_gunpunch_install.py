#!/usr/bin/env python3
"""gunpunch_1108 installer (owner double-click: INSTALL punchy gun sounds all maps.bat does the same through PowerShell).
python install.py [--undo] [--check] [--root <game folder>] [--groups maps,stock,story]
Pins: every bank's live .WAV md5 must be the gunraw_1107 output (manifest input_md5) or already this kit's output; any other = REFUSED, nothing written.
Refuses while kl2.exe has threads. Backups: <bank>.WAV.before-1108gunpunch (never overwritten). --undo writes the old spans back (md5-checked)
and refuses unless every bank is this kit's output or already restored (so UNDO of a LATER layer must be run first).
ALL-OR-NOTHING: a failure part-way (write error, md5 mismatch) rolls every bank touched in that run back from the kit's own span files
(exit 5 = rolled back, 8 = roll back incomplete, backups named). NOTE: writes over the stock Dog Days sound banks IN PLACE (like gunraw_1107); needs the owner's OK."""
import hashlib, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
TAG = 'before-1108gunpunch'
md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()


def running():
    try:
        o = subprocess.run(['powershell', '-NoProfile', '-Command', "(Get-Process kl2 -ErrorAction SilentlyContinue | Where-Object { $_.Threads.Count -gt 0 } | Measure-Object).Count"],
                           capture_output=True, text=True).stdout.strip()
        return int(o or 0) > 0
    except Exception:
        return False


def write_spans(t, sp, src):
    p = 0
    with open(t, 'r+b') as f:
        for i in range(0, len(sp), 2):
            f.seek(sp[i]); f.write(src[p:p + sp[i + 1]]); p += sp[i + 1]
        f.flush(); os.fsync(f.fileno())


def main(a):
    undo = '--undo' in a; check = '--check' in a
    root = a[a.index('--root') + 1] if '--root' in a else ROOT
    groups = (a[a.index('--groups') + 1] if '--groups' in a else 'maps,stock,story').split(',')
    man = json.load(open(os.path.join(HERE, 'manifest.json')))['banks']
    if '--root' not in a and not check and running(): print('kl2.exe is running: close the game first'); return 1
    todo, bad = [], []
    for k, e in man.items():
        if e['group'] not in groups: continue
        t = os.path.join(root, e['file'])
        if not os.path.exists(t): print('skip', k, 'not installed'); continue
        cur = md5(t)
        if undo:
            if cur == e['input_md5']: print('ok  ', k, 'already the gunraw_1107 state'); continue
            if cur != e['output_md5']: bad.append('%s: .WAV is neither the gunraw_1107 bank nor this kit\'s output (a later layer? undo it first)' % k); continue
        else:
            if cur == e['output_md5']: print('ok  ', k, 'already punchy'); continue
            if cur != e['input_md5']: bad.append('%s: .WAV is not the gunraw_1107 bank this kit was built on (changed since)' % k); continue
        todo.append((k, e, t))
    if bad: print('REFUSED, nothing written:'); [print(' ', b) for b in bad]; return 3
    if check: print('check OK: %d banks would change' % len(todo)); return 0
    if not undo:
        need = sum(os.path.getsize(t) for _k, _e, t in todo if not os.path.exists(t + '.' + TAG))
        free = shutil.disk_usage(root).free
        if free < need + 200 * 2 ** 20: print('ABORT: free space %d MB < backups %d MB + 200 MB' % (free >> 20, need >> 20)); return 6
        for k, e, t in todo:
            b = t + '.' + TAG
            if not os.path.exists(b):
                shutil.copyfile(t, b)
                if md5(b) != e['input_md5']: print('FAILED backup of', k); return 7
    done = []                                           # banks touched in this run (the failing one included), for the roll back
    try:
        for k, e, t in todo:
            done.append((k, e, t))
            src = open(os.path.join(HERE, 'Banks', e['group'], e['id'] + ('.old' if undo else '.new')), 'rb').read()
            write_spans(t, e['spans'], src)
            want = e['input_md5'] if undo else e['output_md5']
            if md5(t) != want: raise RuntimeError('md5 check failed after writing ' + k)
            print('done', k)
    except Exception as ex:                             # ALL-OR-NOTHING: put every bank touched in this run back to its state before the run
        print('FAILED (%s: %s): rolling back %d bank(s)' % (type(ex).__name__, ex, len(done)))
        bad = []
        for k, e, t in reversed(done):
            try:
                if md5(t) == (e['output_md5'] if undo else e['input_md5']): continue      # never written (the write itself failed)
                src = open(os.path.join(HERE, 'Banks', e['group'], e['id'] + ('.new' if undo else '.old')), 'rb').read()
                write_spans(t, e['spans'], src)
                if md5(t) != (e['output_md5'] if undo else e['input_md5']): bad.append(k)
            except Exception as ex2:
                bad.append('%s (%s)' % (k, ex2))
        if bad: print('ROLL BACK INCOMPLETE for:', ', '.join(bad), '- backups are *.' + TAG + ' (copy back over the .WAV)'); return 8
        print('rolled back: nothing changed'); return 5
    print(('restored' if undo else 'updated'), len(todo), 'banks. Backups: *.WAV.' + TAG)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
