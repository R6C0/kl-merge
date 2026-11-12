import os
"""round-trip test: parse each sample ANM and rebuild it; DD files must be byte-identical,
DM files must parse fully (and are also checked for identity)."""
import sys, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anm_lib
D = os.environ.get('ANP_ANM_SAMPLES', 'anm_samples') + os.sep   # folder with sample .anm files extracted from your games
ok = True
for fn in ['dd.anm', 'L01.anm', 'dm.anm', 'dm_M02A.anm']:
    t = time.time()
    raw = open(D + fn, 'rb').read()
    f = anm_lib.AnmFile.parse(raw)
    out = f.build()
    same = out == raw
    ok &= same
    a = f.anim
    # full clip-level parse
    nt = 0
    for i in range(len(a.recs)):
        a.blob_span(i); a.events(i); tb = a.track_block(i); nt += len(tb.get('tracks', []))
    print('%-12s variant=%s clips=%d tracks=%d dbs=%d names=%d  rebuild identical=%s  (%.1fs) md5 %s' % (
        fn, a.variant, len(a.recs), nt, len(f.dbs), len(f.names.names), same, time.time() - t,
        hashlib.md5(raw).hexdigest()[:8]))
print('ALL OK' if ok else 'FAIL')
sys.exit(0 if ok else 1)
