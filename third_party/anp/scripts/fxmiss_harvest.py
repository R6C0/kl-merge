"""Harvest the loader's FXMISS lines into fxc/miss_<ID>.txt (the offline replacement for the runtime FX alias).

Until 11 Oct the loader's code patch at 0x71166d (CEG-hashed) aliased every effect permutation the library lacked to
the closest one at run time and logged it as "FXMISS <kind> <effect> : <defines>". The default loader no longer does
that (fx=off); port_level.py builds the aliases into the level's .fxc instead (fxcalias.build) whenever
fxc/miss_<ID>.txt exists. This script collects the keys from the smoke logs.

A log line belongs to the Dead Men level whose scene zip was opened last ("open .../Locations/<ID>/<ID>_Main.zip").
The loader de-duplicates FXMISS per process, so in a chain run a key that an earlier level missed is not logged again
for a later one: the union over all logs covers that as long as each level also has a run of its own (the table shows
single-level runs per level).

usage: py scripts\\fxmiss_harvest.py [--apply] [logs...]
  default logs: work/smoke/*/log.txt and <DD>/ANP_log.txt
  default output: work/out_ceg/fxc/miss_<ID>.txt (merged with the existing fxc/miss_<ID>.txt)
  --apply: write fxc/miss_<ID>.txt in the repo (then rebuild the levels with tools/port_level.py)
"""
import glob, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import anp_paths

LEVELS = ['M01', 'M02', 'M03', 'M03B', 'M05', 'M06', 'M07', 'M07F', 'M08', 'M09', 'M09B', 'M11', 'M11B', 'M12', 'M13', 'M13B',
          'M14']
OPEN = re.compile(r'open .*?Locations[/\\](\w+)[/\\]\1_Main\.zip ok', re.I)
# scenes outside Locations (tools/port_level.py SPECIAL_SCENES): the funeral = M07F
OPEN_SPECIAL = [(re.compile(r'open .*?CutScenes[/\\]M07[/\\]M07_A_Funeral\.zip ok', re.I), 'M07F')]
MISS = re.compile(r'FXMISS (\d+ \S+ :.*)$')


def harvest(paths):
    keys = {l: set() for l in LEVELS}; runs = {l: [0, 0] for l in LEVELS}   # [single-level logs, all logs]
    for p in paths:
        try: text = open(p, 'rb').read().decode('latin1', 'replace')
        except OSError: continue
        cur = None; seen = set()
        for line in text.splitlines():
            m = OPEN.search(line)
            if m:
                cur = m.group(1).upper(); seen.add(cur); continue
            sp = next((sid for rx, sid in OPEN_SPECIAL if rx.search(line)), None)
            if sp:
                cur = sp; seen.add(cur); continue
            m = MISS.search(line)
            if m and cur in keys: keys[cur].add(' '.join(m.group(1).split()))
        lv = [l for l in seen if l in keys]
        for l in lv:
            runs[l][1] += 1
            if len(lv) == 1: runs[l][0] += 1
    return keys, runs


def main():
    apply = '--apply' in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not paths:
        paths = sorted(glob.glob(os.path.join(anp_paths.WORK, 'smoke', '*', 'log.txt')))
        try: paths.append(os.path.join(anp_paths.game_dir('ANP_DD_GAME', anp_paths.DD_FOLDER), 'ANP_log.txt'))
        except SystemExit: pass
    keys, runs = harvest(paths)
    src = os.path.join(anp_paths.REPO, 'fxc')
    dst = src if apply else os.path.join(anp_paths.WORK, 'out_ceg', 'fxc')
    os.makedirs(dst, exist_ok=True)
    print('%d logs. level  runs(single/all)  harvested  existing  written' % len(paths))
    for l in LEVELS:
        old = os.path.join(src, 'miss_%s.txt' % l); have = []
        if os.path.exists(old): have = [x.strip() for x in open(old, encoding='utf-8') if x.strip()]
        allk = sorted(set(have) | keys[l], key=lambda s: (int(s.split()[0]), s))
        if allk and (keys[l] - set(have) or not apply):
            with open(os.path.join(dst, 'miss_%s.txt' % l), 'w', encoding='utf-8', newline='\n') as f: f.write('\n'.join(allk) + '\n')
        print('  %-5s %4d/%-4d %20d %9d %8d%s' % (l, runs[l][0], runs[l][1], len(keys[l]), len(have), len(allk),
              '' if runs[l][0] else '   <- no single-level run: keys shared with an earlier level may be missing'))
    print('written to', dst, '' if apply else '(not the repo; --apply writes fxc/)')


if __name__ == '__main__':
    main()
