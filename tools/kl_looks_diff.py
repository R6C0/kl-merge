"""Diff the OnlineLooks=2 probe lines of a 2-seat bench (host inst1 vs client inst2).

usage: python -I tools/kl_looks_diff.py <TAG>     (logs under <work>/build/klhook/solo/<TAG>/inst1|2/KLHook.log)

Takes the LAST full block ('botfill: looks: <SEAT> seat, N Ally bot(s)' + its N bot lines) of each seat and
compares, bot index by bot index, the fields that can match across machines: group name, digit, class.
Actor / model addresses differ per process and are only printed. Slot (entity-table index) is compared too:
an equal slot order on both seats is what a host->client looks message keyed by bot index would need.
"""
import os, re, sys

SOLO = r"G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\build\klhook\solo"
HDR = re.compile(r'botfill: looks: (HOST|CLIENT) seat, (\d+) Ally bot')
BOT = re.compile(r'botfill: looks: (HOST|CLIENT) bot (\d+) slot=(\d+) actor=(\w+) cls=(\w+) team=(\d+) group="([^"]*)" digit=(.) model=(\w+)')


def last_block(path):
    blocks, cur = [], None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = HDR.search(line)
            if m:
                cur = {'seat': m.group(1), 'n': int(m.group(2)), 'bots': []}
                blocks.append(cur)
                continue
            m = BOT.search(line)
            if m and cur is not None:
                cur['bots'].append(dict(i=int(m.group(2)), slot=int(m.group(3)), actor=m.group(4), cls=m.group(5),
                                        group=m.group(7), digit=m.group(8), model=m.group(9)))
    full = [b for b in blocks if len(b['bots']) == b['n']]
    return full[-1] if full else None, len(blocks)


def main():
    if len(sys.argv) != 2:
        print(__doc__); return 2
    tag = sys.argv[1]
    seats = {}
    for inst in ('inst1', 'inst2'):
        p = os.path.join(SOLO, tag, inst, 'KLHook.log')
        if not os.path.exists(p):
            print(f'{inst}: no log at {p}'); return 1
        blk, nb = last_block(p)
        print(f'{inst}: {nb} looks block(s)' + (f', last full: {blk["seat"]} {blk["n"]} bot(s)' if blk else ', none full'))
        seats[inst] = blk
    h, c = seats['inst1'], seats['inst2']
    if not h or not c:
        print('RESULT: NO DATA (a seat logged no full looks block: OnlineLooks=2 missing or no round census)'); return 1
    same_order = same_set = True
    for i in range(max(len(h['bots']), len(c['bots']))):
        hb = h['bots'][i] if i < len(h['bots']) else None
        cb = c['bots'][i] if i < len(c['bots']) else None
        fmt = lambda b: f"slot {b['slot']:>5} {b['group']:<22} d{b['digit']} cls {b['cls']}" if b else '-'
        ok = hb and cb and (hb['slot'], hb['group'], hb['digit']) == (cb['slot'], cb['group'], cb['digit'])
        same_order &= bool(ok)
        print(f"  bot {i}: host {fmt(hb):<52} | client {fmt(cb):<52} {'same' if ok else 'DIFF'}")
    key = lambda b: (b['group'], b['digit'])
    same_set = sorted(map(key, h['bots'])) == sorted(map(key, c['bots']))
    print(f"RESULT: {'SAME ORDER' if same_order else ('SAME SET, OTHER ORDER' if same_set else 'DIFFERENT')} "
          f"(host {len(h['bots'])} bot(s), client {len(c['bots'])}; groups with '?' mean the name read failed)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
