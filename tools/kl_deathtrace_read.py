#!/usr/bin/env python3
"""
Print the [DeathTrace] result of a bench run (tools/kl_bench_1106.py kits dd10trace3a/b/c/d) from KLHook.log, with a one-line verdict per round.

    python tools/kl_deathtrace_read.py dd10trace3a          # <work>/build/klhook/solo/<kit>_solo/inst1/KLHook.log
    python tools/kl_deathtrace_read.py <path to KLHook.log>
    python tools/kl_deathtrace_read.py dd10trace3a --all     # also every 'deathtrace: s' sample line

Read only; never writes. Verdict rules are the README's (C:/kl_build_1024/dd10trace_1110/README.txt): a GUESS list lives in klhook/kldeathtrace.c.
"""
import os, re, sys

SOLO = 'G:/SteamLibrary/steamapps/common/Kane and Lynch Dead Men/KL_PortTools/build/klhook/solo'


def find(arg):
    if os.path.isfile(arg):
        return arg
    p = '%s/%s_solo/inst1/KLHook.log' % (SOLO, arg)
    return p if os.path.isfile(p) else None


def verdict(chunk):
    """Judge one round. 'Ground' attackers are the engine's floor / impact damage (kind 3, seen in dd10trace1110on while running): reported, not named as the killer."""
    dmg = [l for l in chunk if 'deathtrace: dmg(router)' in l]
    txt = [l for l in chunk if 'deathtrace: text' in l]
    died = any('deathtrace: DEATH' in l for l in chunk)
    names = {}
    for l in dmg:
        m = re.search(r"attacker=([0-9a-f]+) class=(\S+) name='([^']*)'", l)
        if m:
            k = ('null' if int(m.group(1), 16) == 0 else m.group(3) or m.group(2))
            names[k] = names.get(k, 0) + 1
    summ = 'dmg attackers: ' + (', '.join('%s x%d' % kv for kv in sorted(names.items(), key=lambda kv: -kv[1])) or 'none')
    if not died and not txt:
        return 'NO DEATH this round. ' + summ
    tail = [l for l in chunk if re.search(r'deathtrace: tail', l)]
    last = tail[-1] if tail else ''
    named = [l for l in txt if 'entity=null' not in l]
    if named:
        m = re.search(r"class=(\S+) name='([^']*)'", named[-1])
        return 'KILLER NAMED by the kill-text builder: %s. %s' % (m.group(0) if m else '?', summ)
    last_dmg = [m for l in dmg[-3:] for m in [re.search(r"attacker=([0-9a-f]+) class=(\S+) name='([^']*)'", l)] if m and int(m.group(1), 16) and m.group(3) != 'Ground']
    if last_dmg:
        return 'killer candidate = last non-Ground attacker %s (%s). %s' % (last_dmg[-1].group(3), last_dmg[-1].group(2), summ)
    if re.search(r'box=OUT|ahead-OUT', last):
        return 'entity=null, box OUT in the last samples -> engine level-box (out-of-bounds) kill. ' + summ
    vy = re.search(r' v=\([-\d.]+ ([-\d.]+) ', last)
    if vy and float(vy.group(1)) < -300:
        return 'entity=null, big negative vy -> a fall kill. ' + summ
    return 'entity=null (FA_DieFromSelf / script-environment kill): read the dmg stack addresses. ' + summ


def main():
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    if not a:
        print(__doc__); return 2
    p = find(a[0])
    if not p:
        print('no log for %r (looked under %s)' % (a[0], SOLO)); return 1
    L = open(p, encoding='latin-1', errors='replace').read().splitlines()
    print('log: %s (%d lines)' % (p, len(L)))
    for l in L:
        if re.search(r'deathtrace: (on|detour|no memory)|FallRescue', l):
            print(l[:220])
    chunks, cur = [], None
    for l in L:
        if 'deathtrace: round start' in l:
            cur = [l]; chunks.append(cur)
        elif cur is not None:
            cur.append(l)
    print('rounds seen: %d' % len(chunks))
    for i, ch in enumerate(chunks, 1):
        print('==== ROUND %d ====' % i)
        for j, l in enumerate(ch):
            if re.search(r'deathtrace: (round|dmg|text|DEATH|tail)', l) or 'BENCH1106 ROUND' in l or (j and 'deathtrace: tail' in ch[j - 1]):
                print(l[:300])
            elif '--all' in sys.argv and 'deathtrace: ' in l:
                print(l[:300])
        print('VERDICT round %d: %s' % (i, verdict(ch)))
    if not chunks:
        print('no "deathtrace: round start" line: dll not TEST/[DeathTrace] off/SessionSafe=1? check the first lines above')
    return 0


if __name__ == '__main__':
    sys.exit(main())
