"""kl_loot_scale_1026.py - scale the loot VALUES of a map to its place's total, 4,000,000 .. 8,000,000 (written 2026-10-26, OFFLINE).

OWNER 2026-10-26: "make loot / money higher on all maps dependent on where the map is up to 8 mil". This REPLACES the old rule "every map totals exactly
4,000,000". Each map gets a total between 4M and 8M that fits the place (table TARGETS below: a bank / vault / tower gets the most).

WHAT IT DOES (VALUES ONLY)
  Input: any map zip. Output: the same zip with ONLY the .prp member different, and in it only field 1 (the amount left) of each OnlineMoneyCtrl of type
  NORMAL / CONTAINER (the objects the rules put on their list one: kl_fa_bots.money_objects; DROP stacks - the pools a dying player sheds - are not loot
  and are not touched). Positions, models, .gms, .buf, .prm, .oct, .HVK, sounds, ini files: byte-identical (asserted on the read-back).
  Each stack is scaled proportionally to its share of the zip's CURRENT total, in multiples of UNIT (10,000), the sum is exactly the target
  (largest-remainder rounding, every stack stays >= UNIT). A stack that is <= 0 (taken from the start) is left alone.
  IDEMPOTENT: a zip already at its target with round stacks comes out byte-identical (the tool then writes nothing, md5 out = md5 in).
  Applicable to WHATEVER zip is live at install time (other agents change placement/cover/doors on the same zips): it reads the amounts from the zip
  it is given, so re-stage after any other install (command below), it never carries amounts of an older zip.

  --part (default OFF, GUESS): also scale field 4 (the size of ONE grab part, 20000 stock) by the same factor, rounded to UNIT/2, so the time to grab a
  stack stays what it is. Without it a stack twice as big takes twice as long (a part is paid every field-5 seconds: re/bots_loot.md 2). Not run live.

TOGGLE (every feature a toggle): map CONTENT; its on/off switch is the install / undo pair, backup tag .before-1026loot8m. install.py pins the live md5,
--undo puts the original back byte for byte, both refuse while kl2.exe runs.

USAGE (from tools/):
  python kl_loot_scale_1026.py targets                       the table
  python kl_loot_scale_1026.py plan [MAP ...]                what each live map would get (reads, writes nothing)
  python kl_loot_scale_1026.py apply <in.zip> <out.zip> (MAP | --target N) [--slot F06] [--part]
  python kl_loot_scale_1026.py check <zip> [MAP]             total == target, all stacks round (exit 1 otherwise)
  python kl_loot_scale_1026.py stage <root> [MAP ...] [--rehearse <scratch>] [--part]
        <root>/<MAP>/in/<zip> (a hard link / copy of the LIVE zip, md5 pinned) -> <root>/<MAP>/stage/{<zip>, install.py, build_report.json}
  RE-STAGE after another agent installed on that map:  python tools/kl_loot_scale_1026.py stage C:/kl_build_1024/loot8m_1026 DM09 --rehearse C:/kl_build_1024/loot8m_1026/_rehearse
"""
import collections, hashlib, json, os, shutil, struct, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kl_fa
import kl_fa_bots as KB
import kl_fa_author as AU
import kl_loot_1025 as LO

TAG = '.before-1026loot8m'
GAME = r'C:\Steam\steamapps\common\Kane & Lynch 2 - Dog Days'
MAPS_DIR = os.path.join(GAME, 'KLExpansion', 'Maps')
UNIT = 10000
OLD_TOTAL = 4000000                    # the rule before 2026-10-26; builders may still produce it (the scale pass runs after them)
MIN_TOTAL, MAX_TOTAL = 4000000, 8000000

# ------------------------------------------------------------------ the tiers (target, one-line reason)
# GUESS (all of them): the owner gave the rule ("bank, vault, tower, casino most; streets, flats, digs less", DM09 Retomoto = 8M) and nothing else; WHICH
# map is in which tier is my reading of what the map is, judged from its title and from what the loot objects are called in the level. Edit a number here
# and re-stage; nothing else depends on it. Steps of 500,000 so a tier is easy to read.
TARGETS = collections.OrderedDict([
    # --- 8.0M: the owner's examples
    ('DM09', (8000000, 'Retomoto Tower: the owner named it; the tower is the biggest heist (statues + boardroom, two parts)')),
    ('DM03A', (8000000, 'The Vault: the bank vault itself, nothing richer exists')),
    # --- 7.0M
    ('DM03', (7000000, 'Withdrawal: the bank (drawers + the garage cash), but its vault is the separate 8M map')),
    ('DD08', (7000000, 'stock F08: server room of a corporate tower (47 locked cases), an office tower like Retomoto but a smaller take')),
    # --- 6.0 .. 6.5M
    ('DD01', (6500000, 'stock F01: control room with 58 locked vault cases (the vault-door map)')),
    ('DM02', (6000000, 'Late Night Opening: shopping mall, jewellery + watch stores, 49 cases')),
    ('DD03', (6000000, 'stock F03: airport hangar + cargo plane, 12 freight cases')),
    ('DD09', (6000000, 'stock F09: large hall, two 2M stacks (an exchange hall), few big stacks')),
    # --- 5.0 .. 5.5M
    ('DD02', (5500000, 'stock F02: train bridge, cargo of a train (24 stacks)')),
    ('DD06', (5500000, 'stock F06: money transporter (armoured cash convoy), cash by definition but in the open')),
    ('DM11B', (5000000, 'Hasta: villa compound, escape by chopper, 16 stacks incl. a 1.95M one carried by the team-mode drop')),
    ('DD04', (5000000, 'stock F04: loot hall (one warehouse of goods)')),
    # --- 4.5M
    ('DD05', (4500000, 'stock F05: a deal, buyer and seller with cash (6 stacks, small place)')),
    ('DD07', (4500000, 'stock F07: street fight between rival mercs, 5 stacks')),
    ('DM01', (4500000, 'Hot Coffee: street cafe + the senator, carried money; open street, not a safe')),
    ('DM05A', (4500000, 'Last Call: a club; tills and the office safe (was only 2.2M)')),
    # --- 4.0M: the floor - streets, flats, digs
    ('DM01B', (4000000, 'Hot Coffee II: diner + back lot, street scale')),
    ('DM06', (4000000, 'A Walk in the Park: park and street, the money is carried by four bosses (3.35M now)')),
    ('DM06B', (4000000, 'A Walk in the Park II: park, street scale')),
    ('DM07', (4000000, 'The Dig: an excavation site, equipment cases, nothing of a bank')),
    ('DD10', (4000000, 'The Flat Raid (campaign flat + street): a flat, the smallest take')),
])


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def live_zip(name):
    """The map's Fxx_Main.zip in the live game folder -> (path, slot)."""
    d = os.path.join(MAPS_DIR, name)
    zs = [f for f in os.listdir(d) if len(f) == 12 and f[0] == 'F' and f.endswith('_Main.zip')]
    if len(zs) != 1:
        raise SystemExit('%s: expected one Fxx_Main.zip, found %s' % (d, zs))
    return os.path.join(d, zs[0]), zs[0][:3]


def low_priority():
    """Below-normal CPU priority (the game may be running)."""
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)
    except Exception:
        pass


# ------------------------------------------------------------------ the arithmetic
def scale(values, target, unit=UNIT):
    """{key: amount} -> {key: new amount}: proportional, multiples of unit, the sum exactly target, every positive stack >= unit.
    Integer arithmetic only (largest remainder; ties go to the larger old value, then the lower key). Idempotent: round stacks that already
    sum to the target come back unchanged."""
    if target % unit:
        raise ValueError('target %d is not a multiple of %d' % (target, unit))
    pos = {k: v for k, v in values.items() if v > 0}
    if not pos:
        raise ValueError('no positive stack to scale')
    S, U = sum(pos.values()), target // unit
    if U < len(pos):
        raise ValueError('target %d cannot give %d stacks %d each' % (target, len(pos), unit))
    q, rem = {}, {}
    for k, v in pos.items():
        q[k], rem[k] = divmod(v * U, S)                  # exact share = v * U / S units
    for k in q:
        if q[k] < 1:
            q[k], rem[k] = 1, -1                         # a stack never vanishes; it is paid for out of the largest below
    left = U - sum(q.values())
    order = sorted(pos, key=lambda k: (-rem[k], -pos[k], k))
    i = 0
    while left > 0:                                      # hand out the missing units
        q[order[i % len(order)]] += 1
        left -= 1
        i += 1
    while left < 0:                                      # only after the min-1 rule: take from the largest stacks
        k = max(q, key=lambda x: (q[x], -x))
        q[k] -= 1
        left += 1
    out = dict(values)
    out.update({k: q[k] * unit for k in q})
    return out


# ------------------------------------------------------------------ the pass
def loot(B):
    return {o['node']: o for o in KB.money_objects(B)}


def set_part(B, k, v):
    i = AU.ctrl_of(B.sc, k, 'OnlineMoneyCtrl')
    kl_fa.edit(B.sc, k, i, lambda us: AU.setv(B.sc, us, 4, int(v)))


def part_of(B, k):
    for nm, body in B.sc.nodes[k]['ctrls']:
        if B.sc.p.key(nm) == 'OnlineMoneyCtrl':
            v = [kl_fa.value(B.sc, u) for u in KB.units(body[1:-1])]
            return v[4], v[5]
    return None, None


def apply(src, dst, target, slot, part=False, log=print):
    """src zip -> dst zip with the stack values scaled to `target`. -> report dict. src is read only. Writes nothing if nothing changes (dst = copy)."""
    if not MIN_TOTAL <= target <= MAX_TOTAL or target % UNIT:
        raise ValueError('target %d is outside %d..%d or not a multiple of %d' % (target, MIN_TOTAL, MAX_TOTAL, UNIT))
    B = KB.Built(src, slot)
    before = loot(B)
    old = {k: o['amount'] for k, o in before.items()}
    new = scale(old, target)
    parts0 = {k: part_of(B, k) for k in before}
    parts1 = {}
    for k in before:
        if new[k] != old[k]:
            LO.amount(B, k, new[k])
        if part and old[k] > 0:
            f = new[k] / float(old[k])
            p0 = parts0[k][0]
            parts1[k] = max(UNIT // 2, int(round(p0 * f / (UNIT // 2))) * (UNIT // 2)) if p0 else p0
            if parts1[k] != p0:
                set_part(B, k, parts1[k])
    prp = B.sc.p.serialize()
    prpname = B.ext['.prp']
    repl = {prpname: prp} if prp != B.files[prpname] else {}
    os.makedirs(os.path.dirname(os.path.abspath(dst)) or '.', exist_ok=True)
    if repl:
        LO.patch_zip(src, dst, repl)
    else:
        shutil.copyfile(src, dst)
    # ---- read back: every other member identical, the prm in particular; amounts as planned; total on target; only the amount (and part) fields differ
    A = KB.Built(dst, slot)
    after = loot(A)
    bad = []
    if set(after) != set(before):
        bad.append('the set of loot objects changed')
    for k in before:
        if after[k]['amount'] != new[k]:
            bad.append('node %d amount %s != %s' % (k, after[k]['amount'], new[k]))
        if after[k]['at'] != before[k]['at'] or after[k]['type'] != before[k]['type']:
            bad.append('node %d moved or retyped' % k)
        if part and old[k] > 0 and part_of(A, k)[0] != parts1[k]:
            bad.append('node %d part %s != %s' % (k, part_of(A, k)[0], parts1[k]))
        if not part and part_of(A, k) != parts0[k]:
            bad.append('node %d grab fields changed' % k)
    if sum(a['amount'] for a in after.values()) != target:
        bad.append('total %d != %d' % (sum(a['amount'] for a in after.values()), target))
    if len(A.sc.names) != len(B.sc.names):
        bad.append('node count changed')
    for n in A.files:
        if n != prpname and A.files[n] != B.files[n]:
            bad.append('member %s changed' % n)
    if list(A.files) != list(B.files):
        bad.append('member list/order changed')
    if A.files[B.ext['.prm']] != B.files[B.ext['.prm']]:
        bad.append('.prm changed')
    if bad:
        raise ValueError('verify: ' + '; '.join(bad))
    rep = collections.OrderedDict(
        md5_in=md5(src), md5_out=md5(dst), members_changed=sorted(repl), total_before=sum(old.values()), total_after=target, objects=len(after),
        prm_identical=True, part_scaled=bool(part), stacks=[collections.OrderedDict(
            node=k, name=B.sc.names[k], kind=before[k]['kind'], old=old[k], new=new[k],
            grab_s_old=_grab(parts0[k], old[k]), grab_s_new=_grab(parts1.get(k, parts0[k]), new[k])) for k in sorted(before)])
    log('  %d stacks, total %d -> %d, members changed: %s, md5 %s -> %s' % (len(after), rep['total_before'], target, ' '.join(repl) or 'none (already on target)',
                                                                       rep['md5_in'][:8], rep['md5_out'][:8]))
    return rep


def _grab(part_sec, amount):
    """Seconds to grab a whole stack at the stored part size and rate (tuning factor +0x624 not applied: GUESS 1)."""
    p, s = part_sec
    if not p or not isinstance(s, (int, float)) or amount <= 0:
        return None
    return round(-(-amount // p) * s, 1)


def check(path, target=None, slot=None, log=print):
    """The zip's loot against its target -> [problems]. Without a target: only 'round and inside 4M..8M'."""
    slot = slot or os.path.basename(path)[:3]
    B = KB.Built(path, slot)
    vals = {k: o['amount'] for k, o in loot(B).items()}
    tot = sum(vals.values())
    bad = []
    if target is not None and tot != target:
        bad.append('total %d, target %d' % (tot, target))
    if not MIN_TOTAL <= tot <= MAX_TOTAL:
        bad.append('total %d is outside %d..%d' % (tot, MIN_TOTAL, MAX_TOTAL))
    odd = [k for k, v in vals.items() if v % UNIT and v > 0]
    if odd:
        bad.append('%d stack(s) not a multiple of %d: %s' % (len(odd), UNIT, odd[:6]))
    log('%s: %d stacks, total %d, target %s: %s' % (os.path.basename(path), len(vals), tot, target, 'PASS' if not bad else 'FAIL ' + '; '.join(bad)))
    return bad


# ------------------------------------------------------------------ staging
INSTALL_PY = LO.INSTALL_PY.replace('loot-placement', 'loot-value scale (4M..8M)').replace('tools/kl_loot_1025.py', 'tools/kl_loot_scale_1026.py').replace(
    '2026-10-25', '2026-10-26').replace(
    "(the map was changed since this was staged)", "(the map was changed since this was staged: re-stage, python tools/kl_loot_scale_1026.py stage C:/kl_build_1024/loot8m_1026 %(map)s)")


def rehearse(d, name, src, new_md5, old_md5, scratch, zn, log=print):
    """install, undo (byte-identical), reinstall, again = no-op, undo, wrong live md5 refused - on a COPY tree under scratch, never the game folder."""
    scratch = os.path.abspath(scratch)
    g = os.path.join(scratch, 'rehearse_game_' + name)
    live = os.path.join(g, 'KLExpansion', 'Maps', name, zn)
    assert os.path.abspath(live).lower().startswith(scratch.lower() + os.sep), live
    LO.rmtree(g)
    os.makedirs(os.path.dirname(live))
    shutil.copy2(src, live)
    run = lambda *x: subprocess.run([sys.executable, os.path.join(d, 'install.py'), '--game', g, '--skip-run-check'] + list(x), capture_output=True, text=True).stdout
    try:
        t = run(); log('  ' + t.strip()); assert 'installed' in t and md5(live) == new_md5, t
        assert os.path.isfile(live + TAG) and md5(live + TAG) == old_md5
        t = run('--undo'); log('  ' + t.strip())
        assert md5(live) == old_md5 and not os.path.exists(live + TAG), 'undo not byte identical'
        with open(src, 'rb') as a, open(live, 'rb') as b:
            while True:
                x, y = a.read(1 << 22), b.read(1 << 22)
                assert x == y, 'undone zip differs from the original'
                if not x:
                    break
        t = run(); assert md5(live) == new_md5, t
        t = run(); assert 'already installed' in t, t
        t = run('--undo'); assert md5(live) == old_md5 and not os.path.exists(live + TAG)
        os.chmod(live, 0o666)
        with open(live, 'ab') as fh:
            fh.write(b'x')
        t = run(); log('  ' + t.strip()); assert 'REFUSED' in t and not os.path.exists(live + TAG), t
    finally:
        LO.rmtree(g)
    log('  rehearsal ok (install, undo byte-identical, reinstall, again = no-op, wrong live md5 refused)')


def stage(root, names=None, scratch=None, part=False, log=print):
    free = shutil.disk_usage(root).free
    if free < 3 << 30:
        raise SystemExit('only %d MB free under %s (need 3 GB)' % (free >> 20, root))
    for name in names or TARGETS:
        target, why = TARGETS[name]
        lz, slot = live_zip(name)
        h_live = md5(lz)
        d = os.path.join(root, name)
        src = os.path.join(d, 'in', os.path.basename(lz))
        os.makedirs(os.path.dirname(src), exist_ok=True)
        if os.path.exists(src):
            os.remove(src)
        try:
            os.link(lz, src)                               # same volume: no second copy; installers replace the live file, never write into it
        except OSError:
            shutil.copyfile(lz, src)
        h = md5(src)
        if h != h_live:
            raise SystemExit('%s changed while it was read (%s -> %s); run again' % (lz, h_live, h))
        log('== %s (%s) -> %d: %s ==' % (name, os.path.basename(lz), target, why))
        out = os.path.join(d, 'stage')
        LO.rmtree(out)
        os.makedirs(out)
        dst = os.path.join(out, os.path.basename(lz))
        rep = apply(src, dst, target, slot, part, log)
        rep['map'], rep['target'], rep['reason'] = name, target, why
        if rep['md5_out'] == h:
            log('  already on target: install.py would change nothing; staging nothing')
            LO.rmtree(out)
            continue
        with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
            fh.write(INSTALL_PY % dict(map=name, zip=os.path.basename(lz), tag=TAG, game=GAME, old=h, new=rep['md5_out']))
        with open(os.path.join(out, 'build_report.json'), 'w') as fh:
            json.dump(rep, fh, indent=1, default=str)
        if scratch:
            os.makedirs(scratch, exist_ok=True)
            rehearse(out, name, src, rep['md5_out'], h, scratch, os.path.basename(lz), log)
    return 0


INSTALL_ANY = '''"""Runs the install.py (stage/ or stage_*/) whose pinned input md5 fits the live zip of this map; --undo: the one whose output md5 is live.
Other arguments are passed on (--game, --skip-run-check). Exit 2 when none fits (stage again)."""
import glob, hashlib, os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
a = sys.argv[1:]
undo = '--undo' in a
for ip in sorted(glob.glob(os.path.join(here, 'stage*', 'install.py'))):
    src = open(ip).read()
    old, new = re.search(r"^OLD, NEW = '(\\w+)', '(\\w+)'", src, re.M).groups()
    mp, zp = re.search(r"^MAP, ZIP, TAG = '(\\w+)', '([\\w.]+)'", src, re.M).groups()[:2]
    game = a[a.index('--game') + 1] if '--game' in a else eval(re.search(r"^GAME = (.+)$", src, re.M).group(1))
    live = os.path.join(game, 'KLExpansion', 'Maps', mp, zp)
    if not os.path.isfile(live):
        continue
    h = hashlib.md5(open(live, 'rb').read()).hexdigest()
    if h == (new if undo else old):
        sys.exit(subprocess.call([sys.executable, ip] + a))
print('REFUSED: no staged install.py fits the live md5 (stage again)')
sys.exit(2)
'''


def stage_alt(root, name, alt, scratch=None, part=False, log=print):
    """stage() for ONE map from the zip `alt` (another agent's staged zip that is about to be installed) instead of the live one.
    -> <root>/<name>/stage_<md5 of alt, 8>/ ; its install.py pins THAT md5. <root>/<name>/install_any.py picks whichever install.py fits the live md5."""
    target, why = TARGETS[name]
    lz, slot = live_zip(name)
    zn = os.path.basename(lz)
    h = md5(alt)
    d = os.path.join(root, name)
    out = os.path.join(d, 'stage_' + h[:8])
    LO.rmtree(out)
    os.makedirs(out)
    log('== %s from %s (md5 %s) -> %d ==' % (name, alt, h[:8], target))
    rep = apply(alt, os.path.join(out, zn), target, slot, part, log)
    rep['map'], rep['target'], rep['reason'], rep['input'] = name, target, why, alt
    with open(os.path.join(out, 'install.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_PY % dict(map=name, zip=zn, tag=TAG, game=GAME, old=h, new=rep['md5_out']))
    with open(os.path.join(out, 'build_report.json'), 'w') as fh:
        json.dump(rep, fh, indent=1, default=str)
    with open(os.path.join(d, 'install_any.py'), 'w', newline='\n') as fh:
        fh.write(INSTALL_ANY)
    if scratch:
        os.makedirs(scratch, exist_ok=True)
        rehearse(out, name, alt, rep['md5_out'], h, scratch, zn, log)
    return rep


def main():
    low_priority()
    a = sys.argv[1:]
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if not a:
        print(__doc__)
        return 2
    if a[0] == 'targets':
        for m, (t, why) in TARGETS.items():
            print('%-6s %9d  %s' % (m, t, why))
        return 0
    if a[0] == 'plan':
        for m in [x for x in a[1:] if x in TARGETS] or TARGETS:
            lz, slot = live_zip(m)
            B = KB.Built(lz, slot)
            old = {k: o['amount'] for k, o in loot(B).items()}
            new = scale(old, TARGETS[m][0])
            print('%-6s %d stacks %9d -> %9d  %s' % (m, len(old), sum(old.values()), sum(new.values()), [(old[k], new[k]) for k in sorted(old)][:6]))
        return 0
    if a[0] == 'apply' and len(a) >= 4:
        tgt = int(opt('--target')) if '--target' in a else TARGETS[a[3]][0]
        slot = opt('--slot') or os.path.basename(a[1])[:3]
        apply(a[1], a[2], tgt, slot, '--part' in a)
        return 0
    if a[0] == 'check' and len(a) >= 2:
        return 1 if check(a[1], TARGETS[a[2]][0] if len(a) > 2 and a[2] in TARGETS else None) else 0
    if a[0] == 'stage-alt' and len(a) >= 4:        # stage-alt <root> MAP <zip> [--rehearse scratch] [--part]
        stage_alt(a[1], a[2], a[3], opt('--rehearse'), '--part' in a)
        return 0
    if a[0] == 'stage' and len(a) >= 2:
        return stage(a[1], [x for x in a[2:] if x in TARGETS] or None, opt('--rehearse'), '--part' in a)
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main())
