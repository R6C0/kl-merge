#!/usr/bin/env python3
r"""klmusic_check.py - does every track a [Music] / [Music.<map>] playlist names exist? (reads klhook/klmusic.c's keys)

    python tools/klmusic_check.py KLHook.music.patch.ini [more.ini ...]

Mirrors klmusic.c klmu_parse: a name with a drive or a leading backslash is a full path, a bare name is looked up in Folder,
then FolderB. Prints the tracks per mood and exits 1 when a file is missing or a mood list is longer than 32 entries.
Pure reader; the audio files are never copied.
"""
import configparser, os, sys

MOODS = ('Calm', 'Action', 'Escape', 'Down', 'Stinger')


def lines_of(path):
    # the game reads values verbatim; configparser would choke on '%' and treat ';' inside values as text - same as Windows
    cp = configparser.RawConfigParser(strict=False, interpolation=None, comment_prefixes=(';',), inline_comment_prefixes=())
    cp.optionxform = str
    cp.read(path, encoding='latin-1')
    return cp


def check(path):
    cp = lines_of(path)
    bad = 0
    base = dict(cp['Music']) if cp.has_section('Music') else {}
    secs = ['Music'] + [s for s in cp.sections() if s.lower().startswith('music.')]
    for s in secs:
        d = dict(base); d.update(dict(cp[s]))
        folder, folderb = d.get('Folder', ''), d.get('FolderB', '')
        for m in MOODS:
            val = d.get(m, '')
            names = [x.strip() for x in val.split(';') if x.strip()]
            if len(names) > 32:
                print('%s [%s] %s: %d entries, the hook keeps 32' % (path, s, m, len(names))); bad += 1
            for n in names:
                if len(n) > 1 and (n[1] == ':' or n[0] == '\\'):
                    full = n
                else:
                    full = os.path.join(folder, n)
                    if not os.path.exists(full) and folderb:
                        full = os.path.join(folderb, n)
                if not os.path.exists(full):
                    print('MISSING [%s] %s: %s' % (s, m, full)); bad += 1
            if names and s == 'Music':
                print('[%s] %-7s %2d tracks' % (s, m, len(names)))
            elif names:
                print('[%s] %-7s %2d tracks (override)' % (s, m, len(names)))
    print('%s: %s' % (path, 'OK' if not bad else '%d problem(s)' % bad))
    return bad


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.exit(1 if sum(check(p) for p in sys.argv[1:]) else 0)
