import os
"""validates the track codec description against every clip of the sample files:
every IdxT / rotation / position / morph stream is decoded, its computed size must tile the
track block exactly, quaternions must be unit length and frame indices within the clip."""
import sys, struct, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anm_lib, anm_codec as C
D = os.environ.get('ANP_ANM_SAMPLES', 'anm_samples') + os.sep   # folder with sample .anm files extracted from your games
for fn in sys.argv[1:] or ['dd.anm', 'dm.anm', 'L01.anm', 'dm_M02A.anm']:
    f = anm_lib.load(D + fn); a = f.anim; B = a.B
    st = collections.Counter(); maxdev = 0.0
    for i in range(len(a.recs)):
        tb = a.track_block(i)
        if tb['baked']:
            st['baked'] += 1; continue
        p = tb['p']; nfr = tb['frames']
        if nfr != a.frames(i): st['frames_mismatch'] += 1
        start, size = a.blob_span(i)
        segs = []
        for (oa, ob, oc, od, bone) in tb['tracks']:
            fa = C.idxt_frames(B, p + oa); fc = C.idxt_frames(B, p + oc)
            if fa and (fa[0] != 0 or fa[-1] != nfr - 1): st['rot_frame_range'] += 1
            if fc and (fc[0] != 0 or fc[-1] != nfr - 1): st['pos_frame_range'] += 1
            q = C.rot_decode_all(B, p + ob, len(fa))
            for qq in q:
                maxdev = max(maxdev, abs(math.sqrt(sum(x * x for x in qq)) - 1))
            segs += [(oa, C.idxt_size(B, p + oa), 'A'), (oc, C.idxt_size(B, p + oc), 'C'),
                     (ob, C.rot_stream_size(B, p + ob, len(fa)), 'B'), (od, 12 * len(fc), 'D')]
            hb = B[p + ob]
            st['rot_bits_%s' % ('raw' if hb >> 3 == 31 else ('const' if hb & 4 else 'delta'))] += 1
        for (oi, ov, ch) in tb['channels']:
            fi = C.idxt_frames(B, p + oi)
            segs += [(oi, C.idxt_size(B, p + oi), 'Mi'), (ov, 4 * len(fi), 'Mv')]
        segs.sort()
        hdr_end = 0x24 + 0x14 * len(tb['tracks']) + 12 * len(tb['channels']) + 36
        pos = hdr_end; gaps = 0
        for o, s, k in segs:
            if o < pos: st['overlap_' + k] += 1
            gaps += max(0, o - pos)
            pos = max(pos, o + s)
        # the streams are grouped (all A, all C, all B, all D, morph) and each group is 4-aligned;
        # count only the per-group alignment padding
        end = p - start + pos
        if a.recs[i][9] and (p + pos - start) > size or (a.recs[i][9] and size - (p + pos - start) > 3): st['tail_mismatch'] += 1
        st['pad_bytes'] += gaps
    print(fn, dict(st), 'max |q|-1 = %.2e' % maxdev)
