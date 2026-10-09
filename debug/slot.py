#!/usr/bin/env python3
"""
Put a kept build into Dog Days' F01 TEST SLOT, with the hook's side files, and say what is there.

    python debug/slot.py status [slot]                 sha1 of the slot's archive, its side files, the hook pair
    python debug/slot.py put <build folder> [slot] [--join <KLJoin.ini>]
    python debug/slot.py same <build folder> [slot]    exit 0 when the slot holds exactly that build

Like kl_graft.install (which is being edited by others and does not know KLWardrobe.ini), but:
- copies <slot>_Main* AND the hook's side files of the build: KLJoin.ini (kljoin.c) and
  KLWardrobe.ini (klchar.c reads it beside the archive that is opened). A side file the build does
  not have is REMOVED from the slot (a wardrobe list of another build names model numbers that are
  not models there). --join gives the KLJoin.ini when the build folder has none (play2 has none:
  the owner's Retomoto build takes klhook/KLJoin.retomoto.ini).
- never touches KL_PortBackup and refuses to overwrite a file whose stock original is not already
  in KL_PortBackup (so no stock file can be lost through this tool);
- refuses while a kl2.exe with a thread exists.
"""
import hashlib, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
from kl_port_check import find, DD_GUESSES, DD_EXE
import kl_autotest

SIDE = ('KLJoin.ini', 'KLWardrobe.ini')


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def files(folder, slot):
    return sorted(f for f in os.listdir(folder) if f.startswith(slot + '_Main') or f in SIDE)


def status(dd, slot):
    d = os.path.join(dd, 'Scenes', 'Locations', slot)
    for f in files(d, slot):
        if f.endswith('.zip') or f in SIDE:
            print('%s  %12d  %s' % (sha1(os.path.join(d, f)), os.path.getsize(os.path.join(d, f)), os.path.join('Scenes', 'Locations', slot, f)))
    for f in ('dinput8.dll', 'KLHook.ini', os.path.join('KLExpansion', 'Overlay', 'Patch01.zip')):
        p = os.path.join(dd, f)
        print('%s  %12d  %s' % (sha1(p), os.path.getsize(p), f) if os.path.isfile(p) else '%-40s  %12s  %s' % ('-', '-', f))


def same(dd, src, slot, join=None):
    d = os.path.join(dd, 'Scenes', 'Locations', slot)
    want = {f: os.path.join(src, f) for f in files(src, slot)}
    if join:
        want['KLJoin.ini'] = join
    have = files(d, slot)
    bad = [f for f in have if f not in want] + [f for f in want if f not in have]
    bad += [f for f in want if f in have and (os.path.getsize(want[f]) != os.path.getsize(os.path.join(d, f)) or sha1(want[f]) != sha1(os.path.join(d, f)))]
    return sorted(set(bad))


def put(dd, src, slot, join=None):
    if kl_autotest.running():
        raise SystemExit('kl2.exe is running: nothing changed')
    d = os.path.join(dd, 'Scenes', 'Locations', slot)
    back = os.path.join(dd, 'KL_PortBackup', 'Scenes', 'Locations', slot)
    want = {f: os.path.join(src, f) for f in files(src, slot)}
    if join:
        want['KLJoin.ini'] = join
    if slot + '_Main.zip' not in want:
        raise SystemExit('%s has no %s_Main.zip' % (src, slot))
    for f in want:
        if f not in SIDE and os.path.isfile(os.path.join(d, f)) and not os.path.isfile(os.path.join(back, f)):
            raise SystemExit('%s is in the slot but not in KL_PortBackup: it may be a stock file - nothing changed' % f)
    for f in files(d, slot):
        if f not in want:
            if f in SIDE:
                os.remove(os.path.join(d, f))
                print('removed %s (this build has none)' % f)
            else:
                raise SystemExit('the slot has %s, the build has not - nothing changed' % f)
    for f, p in sorted(want.items()):
        t = os.path.join(d, f)
        if os.path.isfile(t) and os.path.getsize(t) == os.path.getsize(p) and sha1(t) == sha1(p):
            continue
        shutil.copyfile(p, t)
    bad = same(dd, src, slot, join)
    print('slot %s = %s%s: %s' % (slot, src, ' + ' + join if join else '', 'ok, %d files' % len(want) if not bad else 'DIFFERENT: ' + ', '.join(bad)))
    return not bad


def main():
    a = sys.argv[1:]
    join = None
    if '--join' in a:
        i = a.index('--join'); join = a[i + 1]; del a[i:i + 2]
    dd = find(DD_GUESSES, DD_EXE)
    if not dd or not a:
        raise SystemExit(__doc__)
    if a[0] == 'status':
        status(dd, a[1] if len(a) > 1 else 'F01')
    elif a[0] == 'same':
        bad = same(dd, a[1], a[2] if len(a) > 2 else 'F01', join)
        print('same' if not bad else 'DIFFERENT: ' + ', '.join(bad))
        return 1 if bad else 0
    elif a[0] == 'put':
        return 0 if put(dd, a[1], a[2] if len(a) > 2 else 'F01', join) else 1
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    sys.exit(main())
