"""kl_rt_joinini.py SRC_DM09_FOLDER OUT_FOLDER [--margins] [--set SECTION.KEY=VALUE ...] [--dry]

Opt-in post-pass on a built Retomoto (DM09) folder: copies every file of SRC to OUT and rewrites ONLY
KLJoin.ini values that the caller asks for. With no flag the output is byte-identical to the source
(proved by md5 in the run's summary). Nothing in the Dog Days folder is touched; nothing is installed.

Why (re/retomoto_fa.md 13.1): the crew hop / join margins read from the owner's real rounds were thin:
  [CrewHop.2] Radius 700: the 11 first sightings lie 653..697 from From (3 to spare for one bot in eleven);
  [CrewHop.3] Height 150: sightings sit at dy +130..+146 (4 to spare), the +0x460 place disagrees (dy +217..225).
--margins applies exactly those two GUESSes:  CrewHop.2.Radius 700 -> 800,  CrewHop.3.Height 150 -> 250.
--set edits any other single key (the section header must be exact, e.g. CrewHop.2; the key must exist ONCE
in that section, else the tool stops - it never adds a key).

GUESS (not tested in the game): 800 catches a bot earlier on its way in (it is carried the moment it stands
Wait=1 s inside the circle), so bots may be carried from a little further away; whether walls lie within 800
of the lift lobby is unchecked. 250 only widens the height window of hop 3; hop 3 already worked on the node
alone. Revert = use the source folder.

Exit code 0 = written and verified (only the named lines differ), 1 = refused."""
import sys, os, re, shutil, hashlib, argparse

MARGINS = ['CrewHop.2.Radius=800', 'CrewHop.3.Height=250']


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def edit(data, sets):
    """data: bytes of KLJoin.ini. sets: list of (section, key, value). Returns (new bytes, [(section,key,old,new)])."""
    lines = data.split(b'\n')          # keeps any \r at the end of a line
    done = []
    for sec, key, val in sets:
        cur = None
        hits = []
        for i, ln in enumerate(lines):
            s = ln.strip()
            if s.startswith(b'[') and s.endswith(b']'):
                cur = s[1:-1].decode('latin1')
            elif cur == sec and not s.startswith(b';'):
                m = re.match(rb'^(\s*)' + re.escape(key.encode()) + rb'(\s*=\s*)([^\r]*?)(\s*)$', ln.rstrip(b'\r'))
                if m:
                    hits.append((i, m))
        if len(hits) != 1:
            raise SystemExit('refused: [%s] %s found %d times (need exactly 1)' % (sec, key, len(hits)))
        i, m = hits[0]
        cr = b'\r' if lines[i].endswith(b'\r') else b''
        old = m.group(3).decode('latin1')
        lines[i] = m.group(1) + key.encode() + m.group(2) + val.encode() + m.group(4) + cr
        done.append((sec, key, old, val))
    return b'\n'.join(lines), done


def parse_set(s):
    if '=' not in s or '.' not in s.split('=')[0]:
        raise SystemExit('refused: --set wants SECTION.KEY=VALUE, got ' + s)
    lhs, val = s.split('=', 1)
    sec, key = lhs.rsplit('.', 1)
    return sec, key, val


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('out')
    ap.add_argument('--margins', action='store_true')
    ap.add_argument('--set', action='append', default=[])
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args(argv)
    sets = [parse_set(s) for s in (MARGINS if a.margins else []) + a.set]
    ini = os.path.join(a.src, 'KLJoin.ini')
    if not os.path.isfile(ini):
        raise SystemExit('refused: no KLJoin.ini in ' + a.src)
    src_abs, out_abs = os.path.abspath(a.src), os.path.abspath(a.out)
    if src_abs == out_abs:
        raise SystemExit('refused: OUT must differ from SRC')
    if 'KL_PortBackup' in out_abs or 'steamapps' in out_abs.lower():
        raise SystemExit('refused: OUT must not be a game folder')
    data = open(ini, 'rb').read()
    new, done = edit(data, sets)
    for d in done:
        print('KLJoin.ini [%s] %s: %s -> %s' % d)
    if a.dry:
        print('dry run: nothing written')
        return 0
    os.makedirs(a.out, exist_ok=True)
    for n in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, n)
        if not os.path.isfile(p):
            continue
        q = os.path.join(a.out, n)
        if n == 'KLJoin.ini':
            open(q, 'wb').write(new)
        else:
            shutil.copy2(p, q)
    diff = []
    for n in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, n)
        if os.path.isfile(p) and md5(p) != md5(os.path.join(a.out, n)):
            diff.append(n)
    if diff != (['KLJoin.ini'] if new != data else []):
        raise SystemExit('refused: unexpected differing members %s' % diff)
    # only the named lines differ
    a_l, b_l = data.split(b'\n'), new.split(b'\n')
    nd = sum(1 for x, y in zip(a_l, b_l) if x != y)
    if len(a_l) != len(b_l) or nd != len(done):
        raise SystemExit('refused: %d lines differ, expected %d' % (nd, len(done)))
    print('differs from source: %s; lines changed: %d' % (diff or 'nothing (byte-identical)', nd))
    for n in sorted(os.listdir(a.out)):
        print('%s %s' % (md5(os.path.join(a.out, n)), n))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
